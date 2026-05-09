"""
Risk budgeting baselines: class-aggregated targets (SLSQP) and per-asset budgets (Spinu + SLSQP fallback).

Taxonomy: merged ``config/etf_universe.yml`` then ``config/stock_universe.yml`` (same rule as
``load_ticker_asset_class_map``). Sub-buckets use only fields present on those YAML rows.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import yaml
from scipy.optimize import minimize

from src.risk_budgeting_presets import (
    RISK_BUDGET_BUCKET_KEYS,
    get_preset,
)
from src.risk_parity_spinu import repair_covariance_psd, spinu_ccd_equal_budget

TAXONOMY_ETF_REL = "config/etf_universe.yml"
TAXONOMY_STOCK_REL = "config/stock_universe.yml"

_SUM_TOL = 1e-6


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_yaml_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def load_merged_universe_rows(
    *,
    etf_universe_path: Path | None = None,
    stock_universe_path: Path | None = None,
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    """
    ticker -> full YAML row; ticker -> ``etf_universe`` | ``stock_universe`` for provenance.
    ETFs win on duplicate tickers; stocks fill only missing tickers.
    """
    root = project_root()
    etf_p = etf_universe_path or (root / TAXONOMY_ETF_REL)
    stock_p = stock_universe_path or (root / TAXONOMY_STOCK_REL)
    merged: dict[str, dict[str, Any]] = {}
    source: dict[str, str] = {}
    for row in _load_yaml_list(etf_p):
        if not isinstance(row, dict):
            continue
        t = row.get("ticker")
        if not isinstance(t, str) or not t.strip():
            continue
        tik = t.strip()
        merged[tik] = row
        source[tik] = "etf_universe"
    for row in _load_yaml_list(stock_p):
        if not isinstance(row, dict):
            continue
        t = row.get("ticker")
        if not isinstance(t, str) or not t.strip():
            continue
        tik = t.strip()
        if tik in merged:
            continue
        merged[tik] = row
        source[tik] = "stock_universe"
    return merged, source


def risk_budget_bucket_from_row(row: dict[str, Any] | None) -> str:
    """Map a single universe row to a canonical risk-budget bucket name."""
    if not row:
        return "unknown"
    ac = str(row.get("asset_class") or "").strip().lower()
    subtype = str(row.get("subtype") or "").strip().lower()

    if ac == "crypto":
        return "crypto"
    if ac == "cash":
        return "cash"
    if ac == "equity":
        return "equity"
    if ac == "commodity":
        if subtype in ("gold", "silver"):
            return "real_assets"
        return "commodity"
    if ac == "alternative":
        if subtype in ("reit", "infrastructure"):
            return "real_assets"
        return "alternatives"
    if ac == "fixed_income":
        if subtype == "tips":
            return "inflation_linked"
        if subtype in ("t_bill", "ultra_short_bond"):
            return "cash"
        if subtype in (
            "high_yield",
            "corporate_ig",
            "em_debt",
            "bank_loan",
            "preferred",
            "floating_rate",
        ):
            return "credit"
        return "fixed_income"
    return "unknown"


def normalize_budget_map(
    raw: dict[str, Any],
    *,
    allowed_keys: set[str] | None = None,
) -> tuple[dict[str, float], list[str]]:
    """
    Returns (normalized map, warnings). Values must be non-negative and sum to 1.
    """
    warnings: list[str] = []
    out: dict[str, float] = {}
    for k, v in raw.items():
        key = str(k).strip()
        if allowed_keys is not None and key not in allowed_keys:
            warnings.append(f"Ignored unknown key {key!r}")
            continue
        try:
            fv = float(v)
        except (TypeError, ValueError):
            raise ValueError(f"Risk budget value for {key!r} must be numeric, got {v!r}") from None
        if fv < 0:
            raise ValueError(f"Risk budget for {key!r} must be non-negative, got {fv}")
        out[key] = fv
    s = float(sum(out.values()))
    if s <= 0:
        raise ValueError("Risk budget targets are empty or sum to zero")
    if abs(s - 1.0) > _SUM_TOL:
        raise ValueError(f"Risk budget targets must sum to 1.0, got {s:.12f}")
    return out, warnings


def resolve_class_risk_targets(
    risk_cfg: dict[str, Any],
) -> tuple[dict[str, float], str, bool, list[str]]:
    """
    Effective bucket targets, preset name, manual_override flag, warnings.

    Manual ``targets`` overrides preset when non-empty.
    """
    warnings: list[str] = []
    preset_name = str(risk_cfg.get("preset") or "balanced").strip().lower()
    manual = risk_cfg.get("targets") or {}
    if isinstance(manual, dict) and len(manual) > 0:
        allowed = set(RISK_BUDGET_BUCKET_KEYS)
        targets, w = normalize_budget_map({str(k): v for k, v in manual.items()}, allowed_keys=allowed)
        warnings.extend(w)
        return targets, preset_name, True, warnings
    targets = get_preset(preset_name)
    return targets, preset_name, False, warnings


def pc_from_w(w: np.ndarray, cov: np.ndarray) -> np.ndarray:
    w = np.asarray(w, dtype=float)
    n = len(w)
    v = float(w @ cov @ w)
    if v <= 1e-16:
        return np.ones(n, dtype=float) / float(n)
    m = cov @ w
    return (w * m) / v


def class_risk_contributions(
    w: np.ndarray,
    cov: np.ndarray,
    bucket_indices: np.ndarray,
    n_buckets: int,
) -> np.ndarray:
    """Vector R of length n_buckets: sum of PC_i for assets in each bucket."""
    pc = pc_from_w(w, cov)
    r = np.zeros(n_buckets, dtype=float)
    for i, bi in enumerate(bucket_indices):
        r[int(bi)] += float(pc[i])
    return r


def solve_class_risk_budget_slsqp(
    cov: np.ndarray,
    bucket_indices: np.ndarray,
    b_target: np.ndarray,
    *,
    tol: float = 1e-9,
    maxiter: int = 5000,
) -> tuple[np.ndarray, dict[str, Any]]:
    """
    Minimize sum_k (R_k(w) - b_k)^2 subject to sum w = 1, w >= 0.
    ``b_target`` length K, nonnegative, sums to 1; ``bucket_indices`` maps asset -> 0..K-1.
    """
    cov = np.asarray(cov, dtype=float)
    n = int(cov.shape[0])
    bi = np.asarray(bucket_indices, dtype=int).reshape(-1)
    if len(bi) != n:
        raise ValueError("bucket_indices length must match covariance size")
    k = int(b_target.shape[0])
    b = np.asarray(b_target, dtype=float).reshape(-1)
    if len(b) != k:
        raise ValueError("b_target length mismatch")

    def objective(x: np.ndarray) -> float:
        x = np.maximum(x, 0.0)
        s = float(np.sum(x))
        if s <= 1e-15:
            return 1e12
        w = x / s
        r = class_risk_contributions(w, cov, bi, k)
        d = r - b
        return float(d @ d)

    diag = np.maximum(np.diag(cov), 1e-12)
    inv_vol = 1.0 / np.sqrt(diag)
    x0 = inv_vol / float(np.sum(inv_vol))
    bounds = [(0.0, 1.0)] * n
    cons = {"type": "eq", "fun": lambda x: float(np.sum(x) - 1.0)}
    res = minimize(
        objective,
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=cons,
        options={"maxiter": int(maxiter), "ftol": float(tol)},
    )
    if res.x is None or not np.all(np.isfinite(res.x)):
        return np.ones(n) / float(n), {
            "solver_status": "FAIL_NUMERICAL",
            "solver_success": False,
            "solver_message": "invalid SLSQP solution",
            "objective_value": None,
        }
    w_raw = np.clip(res.x, 0.0, None)
    s = float(np.sum(w_raw))
    w = (w_raw / s) if s > 1e-15 else np.ones(n) / float(n)
    r = class_risk_contributions(w, cov, bi, k)
    diff = r - b
    tracking = float(diff @ diff)
    max_dev = float(np.max(np.abs(diff))) if k else 0.0
    return w, {
        "solver_status": "OK" if res.success else "APPROXIMATE",
        "solver_success": bool(res.success),
        "solver_message": str(res.message) if hasattr(res, "message") else "",
        "objective_value": float(res.fun) if res.fun is not None else tracking,
        "risk_budget_tracking_error": tracking,
        "max_budget_deviation": max_dev,
        "realized_class_risk": r.tolist(),
        "nit": int(getattr(res, "nit", 0) or 0),
    }


def solve_asset_risk_budget_spinu(
    cov: np.ndarray,
    budget: np.ndarray,
    *,
    spinu_max_iter: int = 50_000,
    spinu_tol: float = 1e-10,
    slsqp_tol: float = 1e-9,
) -> tuple[np.ndarray, dict[str, Any]]:
    """
    Primary: Spinu CCD with vector ``budget`` (sums to 1, all positive).
    Fallback: SLSQP minimize sum_i (PC_i - b_i)^2 subject to sum w = 1, w >= 0.
    """
    cov = np.asarray(cov, dtype=float)
    n = cov.shape[0]
    b = np.asarray(budget, dtype=float).reshape(-1)
    if len(b) != n:
        raise ValueError("budget length must match n")
    if np.any(b <= 0) or abs(float(np.sum(b)) - 1.0) > _SUM_TOL:
        raise ValueError("budget must be positive and sum to 1")

    cov_rep, psd_modified = repair_covariance_psd(cov)

    w_spinu, spinu_diag = spinu_ccd_equal_budget(
        cov_rep,
        budget=b,
        max_iter=int(spinu_max_iter),
        tol=float(spinu_tol),
        init="inv_vol",
    )
    pc_spinu = pc_from_w(w_spinu, cov_rep)
    max_err_spinu = float(np.max(np.abs(pc_spinu - b)))
    spinu_ok = (
        bool(spinu_diag.get("converged"))
        and np.all(np.isfinite(w_spinu))
        and abs(float(np.sum(w_spinu)) - 1.0) < 1e-8
        and np.all(w_spinu > 0)
        and max_err_spinu <= 1e-2
    )

    if spinu_ok:
        return w_spinu, {
            "solver": "spinu_ccd",
            "fallback_used": False,
            "spinu_converged": bool(spinu_diag.get("converged")),
            "spinu_iterations": int(spinu_diag.get("iterations") or 0),
            "max_budget_deviation": max_err_spinu,
            "cov_psd_repaired": psd_modified,
            "risk_budget_tracking_error": float(np.sum((pc_spinu - b) ** 2)),
        }

    def objective(x: np.ndarray) -> float:
        x = np.maximum(x, 0.0)
        s = float(np.sum(x))
        if s <= 1e-15:
            return 1e12
        w = x / s
        pc = pc_from_w(w, cov_rep)
        d = pc - b
        return float(d @ d)

    x0 = np.ones(n) / float(n)
    bounds = [(0.0, 1.0)] * n
    cons = {"type": "eq", "fun": lambda x: float(np.sum(x) - 1.0)}
    res = minimize(
        objective,
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=cons,
        options={"maxiter": 5000, "ftol": float(slsqp_tol)},
    )
    if res.x is None or not np.all(np.isfinite(res.x)):
        w_fb = np.ones(n) / float(n)
        pc = pc_from_w(w_fb, cov_rep)
        return w_fb, {
            "solver": "slsqp_fallback",
            "fallback_used": True,
            "spinu_converged": bool(spinu_diag.get("converged")),
            "solver_success": False,
            "solver_message": "SLSQP fallback failed",
            "max_budget_deviation": float(np.max(np.abs(pc - b))),
            "cov_psd_repaired": psd_modified,
            "risk_budget_tracking_error": float(np.sum((pc - b) ** 2)),
        }

    w_raw = np.clip(res.x, 0.0, None)
    s = float(np.sum(w_raw))
    w = w_raw / s if s > 1e-15 else np.ones(n) / float(n)
    pc = pc_from_w(w, cov_rep)
    return w, {
        "solver": "slsqp_fallback",
        "fallback_used": True,
        "spinu_converged": bool(spinu_diag.get("converged")),
        "solver_success": bool(res.success),
        "solver_message": str(res.message) if hasattr(res, "message") else "",
        "max_budget_deviation": float(np.max(np.abs(pc - b))),
        "cov_psd_repaired": psd_modified,
        "risk_budget_tracking_error": float(np.sum((pc - b) ** 2)),
        "nit": int(getattr(res, "nit", 0) or 0),
    }
