from __future__ import annotations

"""
Portfolio variants (baseline constructions) outside the policy framework.

This module intentionally does NOT apply RC caps, discretionary overlays, or hidden policy filters to Equal-Weight, Risk-Parity, or Minimum-Variance baselines:

- no RC caps as optimization targets (RC_vol stays a report diagnostic)
- no ProLiquidity / mandate-specific layers on these baselines
- Minimum-Variance uses the same **feasibility/config box bounds** as ``run_optimization.py`` (:func:`src.optimization._build_bounds`), not extra custom mandate constraints

These variants are pure asset-level baselines built on the same eligible universe
and then evaluated by the existing metrics / stress-test / client-fit pipeline.

Minimum Variance baseline minimizes ``0.5 * w' Σ w`` subject to the same long-only
box constraints as the policy optimizer (:func:`src.optimization._build_bounds`), with
monthly **Σ** built like ``run_optimization.py`` (optional Young-ETF dual covariance +
per-ticker caps when enabled). **SLSQP** uses the analytical gradient ``Σ w``. Vol
targeting, extra quadratic inequalities, turnover penalties, and L1 regularization
are not implemented in v1.
"""

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Iterable, Tuple

import numpy as np
import pandas as pd
import yaml
from scipy.optimize import minimize

from src.config_schema import PortfolioConfig
from src.optimization import MIN_WEIGHT_DEFAULT, _build_bounds
from src.risk_contrib import cov_matrix_monthly, rc_vol_window
from src.risk_parity_spinu import repair_covariance_psd, spinu_ccd_equal_budget
from src.windows import slice_window
from src.young_etfs_dual_cov import build_dual_covariance_and_mu, per_ticker_young_weight_caps


BASELINE_EQ_LABEL = "Equal-Weight Portfolio"
BASELINE_EQ_BY_CLASS_LABEL = "Equal-Weight by Asset-Class Portfolio"
BASELINE_RP_LABEL = "Risk Parity Portfolio"
BASELINE_MV_LABEL = "Minimum Variance Portfolio"

OPTIMIZER_NAME_MINIMUM_VARIANCE = "minimum_variance"
MINIMUM_VARIANCE_SOLVER = "SLSQP"
MINIMUM_VARIANCE_OBJECTIVE = "0.5 * w.T @ covariance @ w"

MINIMUM_VARIANCE_METADATA_EXPORT_KEYS = (
    "optimizer_name",
    "solver",
    "objective",
    "covariance_method",
    "shrinkage_used",
    "psd_repair_used",
    "young_etf_dual_mode",
    "eligible_universe",
    "final_weights",
    "portfolio_variance",
    "annualized_volatility",
    "solver_status",
    "solver_success",
    "solver_message",
    "max_weight",
    "min_weight",
    "active_constraints",
    "fallback_used",
)


def minimum_variance_baseline_metadata_export(diagnostics: Dict[str, object]) -> Dict[str, Any]:
    """Structured fields for ``baseline_weights_metadata.json`` / summary blobs."""
    out: Dict[str, Any] = {}
    for k in MINIMUM_VARIANCE_METADATA_EXPORT_KEYS:
        if k in diagnostics:
            out[k] = diagnostics[k]
    return out

EQUAL_WEIGHT_METHOD_BY_ASSETS = "equal_weight_by_assets"
EQUAL_WEIGHT_METHOD_BY_ASSET_CLASS = "equal_weight_by_asset_class_then_assets"

EQUAL_WEIGHT_METADATA_EXPORT_KEYS = (
    "equal_weight_method",
    "asset_classes_used",
    "class_weights",
    "tickers_per_class",
    "excluded_missing_asset_class",
    "warnings",
    "reason",
    "baseline_weights_note",
    "universe_eligible",
)


def equal_weight_baseline_metadata_export(diagnostics: Dict[str, object]) -> Dict[str, Any]:
    """Structured fields for ``baseline_weights_metadata.json`` / summary blobs."""
    out: Dict[str, Any] = {}
    for k in EQUAL_WEIGHT_METADATA_EXPORT_KEYS:
        if k in diagnostics:
            out[k] = diagnostics[k]
    return out


@dataclass
class BaselineWeightsResult:
    weights: Dict[str, float]
    status: str
    diagnostics: Dict[str, object]


def _eligible_universe_from_returns(
    cfg: PortfolioConfig,
    monthly_returns: pd.DataFrame,
    analysis_end: str,
    window_months: int,
) -> Tuple[list[str], Dict[str, float]]:
    """
    Derive the eligible investable universe for baselines.

    Rules:
    - Use the same tickers universe as config.tickers.
    - Exclude assets only if they fail the same minimum data / coverage checks
      as used elsewhere for portfolio analytics (simple window coverage filter).
    - No hidden filters.
    """
    tickers = [t for t in cfg.tickers if t in monthly_returns.columns]
    coverage_threshold = getattr(cfg, "coverage_threshold", 0.90) or 0.90
    end_ts = pd.Timestamp(analysis_end)
    eligible: list[str] = []
    coverage: Dict[str, float] = {}

    # Simple coverage: share of non-NaN points in the window.
    for t in tickers:
        series = monthly_returns[t]
        window = slice_window(series, analysis_end, window_months).dropna()
        if window.empty:
            coverage[t] = 0.0
            continue
        total = (end_ts.to_period("M") - window.index.min().to_period("M")).n + 1
        cov_ratio = len(window) / float(total) if total > 0 else 0.0
        coverage[t] = cov_ratio
        if cov_ratio >= coverage_threshold:
            eligible.append(t)

    return eligible, coverage


def _project_root_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def load_ticker_asset_class_map(
    *,
    etf_universe_path: Path | None = None,
    stock_universe_path: Path | None = None,
) -> dict[str, str]:
    """
    Merge ETF and stock taxonomy YAML maps (ticker -> asset_class).
    ETFs are loaded first; stock entries fill tickers missing from ETFs.
    """

    root = _project_root_dir()
    etf_p = etf_universe_path or (root / "config" / "etf_universe.yml")
    stock_p = stock_universe_path or (root / "config" / "stock_universe.yml")
    merged: dict[str, str] = {}
    secondary: dict[str, str] = {}

    for path, is_primary in ((etf_p, True), (stock_p, False)):
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        if not isinstance(data, list):
            continue
        for row in data:
            if not isinstance(row, dict):
                continue
            ticker = row.get("ticker")
            ac = row.get("asset_class")
            if not isinstance(ticker, str) or not isinstance(ac, str):
                continue
            tik = ticker.strip()
            acl = ac.strip()
            if not tik or not acl:
                continue
            if is_primary:
                merged[tik] = acl
            else:
                secondary[tik] = acl

    for tik, acl in secondary.items():
        merged.setdefault(tik, acl)

    return merged


def build_equal_weight_baseline(
    cfg: PortfolioConfig,
    monthly_returns: pd.DataFrame,
    analysis_end: str,
    window_months: int,
) -> BaselineWeightsResult:
    """
    Equal-Weight Portfolio:
    - Universe: same eligible tickers as main engine, but without policy logic.
    - If N eligible assets, each weight = 1/N.
    - Long-only, fully invested; no caps, no RC constraints, no overlays.
    """
    eligible, coverage = _eligible_universe_from_returns(
        cfg, monthly_returns, analysis_end, window_months
    )
    diagnostics: Dict[str, object] = {
        "universe_eligible": eligible,
        "universe_coverage": coverage,
        "equal_weight_method": EQUAL_WEIGHT_METHOD_BY_ASSETS,
    }

    if len(eligible) < 2:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_INFEASIBLE_UNIVERSE",
            diagnostics={
                **diagnostics,
                "asset_classes_used": [],
                "class_weights": {},
                "tickers_per_class": {},
                "excluded_missing_asset_class": [],
                "reason": "Fewer than 2 eligible assets for Equal-Weight baseline",
            },
        )

    n = len(eligible)
    w_eq = 1.0 / float(n)
    weights: Dict[str, float] = {t: 0.0 for t in cfg.tickers}
    for t in eligible:
        weights[t] = w_eq

    diagnostics["asset_classes_used"] = []
    diagnostics["class_weights"] = {}
    diagnostics["tickers_per_class"] = {}
    diagnostics["excluded_missing_asset_class"] = []
    diagnostics["baseline_weights_note"] = (
        "Per-asset Equal-Weight baseline; taxonomy fields intentionally empty "
        "(use equal_weight_by_asset_class_then_assets for class-balanced weights metadata)."
    )

    return BaselineWeightsResult(
        weights=weights,
        status="OK",
        diagnostics=diagnostics,
    )


def build_equal_weight_by_asset_class_baseline(
    cfg: PortfolioConfig,
    monthly_returns: pd.DataFrame,
    analysis_end: str,
    window_months: int,
    *,
    asset_class_lookup: dict[str, str] | None = None,
    etf_universe_path: Path | None = None,
    stock_universe_path: Path | None = None,
) -> BaselineWeightsResult:
    """
    Equal-weight over asset classes (each class receives 1 / n_classes),
    then equal-weight within each class among classified eligible assets.

    Eligible-universe filtering matches :func:`build_equal_weight_baseline`.
    Tickers without ``asset_class`` in the merged taxonomy lookup are excluded
    from the portfolio weights and listed in diagnostics.
    """

    eligible, coverage = _eligible_universe_from_returns(
        cfg, monthly_returns, analysis_end, window_months
    )
    taxonomy = (
        asset_class_lookup
        if asset_class_lookup is not None
        else load_ticker_asset_class_map(
            etf_universe_path=etf_universe_path,
            stock_universe_path=stock_universe_path,
        )
    )

    excluded_missing: list[str] = []
    tickers_kept: list[str] = []
    for t in eligible:
        ac = taxonomy.get(t)
        if not ac:
            excluded_missing.append(t)
        else:
            tickers_kept.append(t)

    by_class: Dict[str, list[str]] = {}
    for t in tickers_kept:
        acl = taxonomy[t]
        by_class.setdefault(acl, []).append(t)

    for k in list(by_class.keys()):
        by_class[k] = sorted(by_class[k])

    nonempty_classes = sorted(by_class.keys())
    diagnostics: Dict[str, object] = {
        "universe_eligible": eligible,
        "universe_coverage": coverage,
        "equal_weight_method": EQUAL_WEIGHT_METHOD_BY_ASSET_CLASS,
        "asset_classes_used": list(nonempty_classes),
        "excluded_missing_asset_class": sorted(set(excluded_missing)),
        "tickers_per_class": {cl: list(tks) for cl, tks in sorted(by_class.items())},
        "baseline_weights_note": (
            "Class-balanced Equal-Weight: equal budget per asset class "
            "(non-empty classes only), equal split inside each class."
        ),
    }

    warns: list[str] = []
    if excluded_missing:
        warns.append(
            "Excluded eligible tickers with no asset_class in taxonomy: "
            + ", ".join(sorted(set(excluded_missing)))
        )

    if not nonempty_classes:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_INFEASIBLE_UNIVERSE",
            diagnostics={
                **diagnostics,
                "class_weights": {},
                "reason": (
                    "No eligible tickers with asset_class taxonomy after exclusions"
                ),
                "warnings": warns,
            },
        )

    if len(tickers_kept) < 2:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_INFEASIBLE_UNIVERSE",
            diagnostics={
                **diagnostics,
                "class_weights": {
                    cl: round(1.0 / len(nonempty_classes), 14)
                    for cl in nonempty_classes
                },
                "reason": (
                    "Fewer than 2 taxonomy-classified eligible assets for "
                    "Equal-Weight by Asset-Class baseline"
                ),
                "warnings": warns,
            },
        )

    n_classes = len(nonempty_classes)
    class_budget = 1.0 / float(n_classes)
    cw = {cl: class_budget for cl in nonempty_classes}
    diagnostics["class_weights"] = {cl: float(cw[cl]) for cl in nonempty_classes}

    if warns:
        diagnostics["warnings"] = warns

    weights: Dict[str, float] = {t: 0.0 for t in cfg.tickers}

    for cl in nonempty_classes:
        members = by_class[cl]
        if not members:
            continue
        w_each = float(class_budget) / float(len(members))
        for tik in members:
            weights[tik] = w_each

    return BaselineWeightsResult(
        weights=weights,
        status="OK",
        diagnostics=diagnostics,
    )


def _pc_from_w_static(w_vec: np.ndarray, cov: np.ndarray) -> np.ndarray:
    var_p = float(w_vec @ cov @ w_vec)
    if var_p <= 1e-16:
        return np.ones_like(w_vec) / float(len(w_vec))
    m = cov @ w_vec
    return (w_vec * m) / var_p


def _risk_parity_slsqp_fallback(
    cov: np.ndarray,
    cols: list[str],
    *,
    tol: float = 1e-8,
) -> Tuple[np.ndarray, Any, str]:
    """Emergency fallback: SLSQP minimizing squared RC deviation from 1/n."""
    n = len(cols)
    target_rc = 1.0 / float(n)

    def objective(w_vec: np.ndarray) -> float:
        pc = _pc_from_w_static(w_vec, cov)
        diff = pc - target_rc
        return float(np.dot(diff, diff))

    x0 = np.ones(n) / float(n)
    bounds = [(0.0, 1.0)] * n
    constraints = [{"type": "eq", "fun": lambda w_vec: float(np.sum(w_vec) - 1.0)}]

    res = minimize(
        objective,
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 5000, "ftol": tol},
    )

    if res.x is None or not np.all(np.isfinite(res.x)):
        return np.array([]), res, "FAIL_NUMERICAL"
    w = np.clip(res.x, 0.0, None)
    s = float(w.sum())
    if s <= 1e-12:
        return np.array([]), res, "FAIL_NUMERICAL"
    w = w / s
    status = "OK" if res.success else "APPROXIMATE"
    return w, res, status


def _risk_parity_solver(
    cov_df: pd.DataFrame,
    tickers: Iterable[str],
    *,
    tol: float = 1e-8,
    spinu_max_iter: int = 50_000,
    spinu_tol: float = 1e-10,
    spinu_eps_floor: float = 1e-12,
    max_rc_error_spinu_abort: float = 1e-2,
) -> Tuple[Dict[str, float], Dict[str, object]]:
    """
    Pure asset-level risk parity (equal RC_vol share). Primary: Spinu CCD on::

        0.5 x'Σx - sum_i (1/N) log(x_i)

    Fallback: SLSQP on squared RC deviation (legacy emergency path).
    Σ is PSD-repaired from the input covariance (Ledoit-Wolf upstream).
    """
    cols = [t for t in tickers if t in cov_df.columns and t in cov_df.index]
    n = len(cols)
    if n == 0:
        return {}, {"status": "FAIL_NO_ASSETS"}

    cov_raw = cov_df.reindex(index=cols, columns=cols).fillna(0.0).values
    cov, cov_psd_repaired = repair_covariance_psd(cov_raw)
    target_rc = 1.0 / float(n)

    w, spinu_diag = spinu_ccd_equal_budget(
        cov,
        eps_floor=spinu_eps_floor,
        max_iter=spinu_max_iter,
        tol=spinu_tol,
        init="inv_vol",
    )

    spinu_ok = (
        bool(spinu_diag.get("converged"))
        and np.all(np.isfinite(w))
        and abs(float(np.sum(w)) - 1.0) < 1e-8
        and float(spinu_diag.get("max_rc_error", 1.0)) <= max_rc_error_spinu_abort
        and np.all(w > 0)
    )

    fallback_used = False
    slsqp_res = None
    iterations_spinu = int(spinu_diag.get("iterations") or 0)

    if spinu_ok:
        status = "OK"
        rp_solver = "spinu_ccd"
        pc_final = _pc_from_w_static(w, cov)
        diagnostics: Dict[str, object] = {
            "status": status,
            "risk_parity_solver": rp_solver,
            "spinu_converged": bool(spinu_diag.get("converged")),
            "fallback_used": False,
            "cov_psd_repaired": cov_psd_repaired,
            "spinu_iterations": iterations_spinu,
            "spinu_max_coord_delta": spinu_diag.get("max_coord_delta"),
            "spinu_objective": spinu_diag.get("objective"),
            "iterations": iterations_spinu,
            "max_rc_error": float(np.max(np.abs(pc_final - target_rc))),
            "rc_target": target_rc,
            "rc_by_asset": {cols[i]: float(pc_final[i]) for i in range(n)},
        }
        weights = {t: float(w[i]) for i, t in enumerate(cols)}
        return weights, diagnostics

    # Emergency fallback: SLSQP
    fallback_used = True
    w_fb, slsqp_res, fb_status = _risk_parity_slsqp_fallback(cov, cols, tol=tol)
    if w_fb.size == 0:
        return {}, {
            "status": "FAIL_NUMERICAL",
            "risk_parity_solver": "slsqp_fallback_failed",
            "spinu_converged": bool(spinu_diag.get("converged")),
            "fallback_used": True,
            "cov_psd_repaired": cov_psd_repaired,
            "spinu_iterations": iterations_spinu,
            "spinu_max_rc_error": spinu_diag.get("max_rc_error"),
        }

    w = w_fb
    pc_final = _pc_from_w_static(w, cov)
    diagnostics = {
        "status": fb_status,
        "risk_parity_solver": "slsqp_fallback",
        "spinu_converged": bool(spinu_diag.get("converged")),
        "fallback_used": True,
        "cov_psd_repaired": cov_psd_repaired,
        "spinu_iterations": iterations_spinu,
        "spinu_max_coord_delta": spinu_diag.get("max_coord_delta"),
        "spinu_max_rc_error": spinu_diag.get("max_rc_error"),
        "iterations": int(slsqp_res.nit) if slsqp_res is not None and hasattr(slsqp_res, "nit") else None,
        "max_rc_error": float(np.max(np.abs(pc_final - target_rc))),
        "rc_target": target_rc,
        "rc_by_asset": {cols[i]: float(pc_final[i]) for i in range(n)},
    }
    weights = {t: float(w[i]) for i, t in enumerate(cols)}
    return weights, diagnostics


def build_risk_parity_baseline(
    cfg: PortfolioConfig,
    monthly_returns: pd.DataFrame,
    analysis_end: str,
    window_months: int,
) -> BaselineWeightsResult:
    """
    Risk-Parity Portfolio:
    - Universe: same eligible tickers as main engine.
    - Objective: equalized asset-level RC_vol as defined in metrics_specification.md.
    - Solver: Spinu cyclical coordinate descent on 0.5 x'Σx - (1/N)Σ log(x_i) with b_i=1/N,
      Σ = PSD-repaired Ledoit-Wolf monthly covariance; emergency fallback SLSQP on squared RC dispersion.
    - Constraints: long-only, fully invested. No caps.
    - If solver is unstable/infeasible, returns best feasible approximation and marks status.
    """
    eligible, coverage = _eligible_universe_from_returns(
        cfg, monthly_returns, analysis_end, window_months
    )
    diagnostics = {
        "universe_eligible": eligible,
        "universe_coverage": coverage,
    }

    if len(eligible) < 2:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_INFEASIBLE_UNIVERSE",
            diagnostics={
                **diagnostics,
                "reason": "Fewer than 2 eligible assets for Risk-Parity baseline",
            },
        )

    # Covariance on monthly simple returns, ddof=1, inner join on eligible assets.
    returns_slice = slice_window(
        monthly_returns[eligible], analysis_end, window_months
    ).dropna(how="any")
    if returns_slice.shape[0] < 2:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_DATA",
            diagnostics={
                **diagnostics,
                "reason": f"Insufficient history for covariance (rows={returns_slice.shape[0]})",
            },
        )

    # User-requested RP setting: covariance via Ledoit-Wolf shrinkage for stability.
    cov_df = cov_matrix_monthly(returns_slice, ddof=1, use_shrinkage=True)
    w_rp, diag = _risk_parity_solver(cov_df, eligible)

    # Normalize to full universe, long-only, fully invested.
    total = float(sum(max(0.0, w) for w in w_rp.values()))
    if total <= 0:
        weights = {t: 0.0 for t in cfg.tickers}
        status = "FAIL_NUMERICAL"
    else:
        weights = {t: 0.0 for t in cfg.tickers}
        for t, w in w_rp.items():
            weights[t] = max(0.0, float(w) / total)
        status = "OK" if diag.get("status") == "OK" else "APPROXIMATE"

    diagnostics.update(diag)
    return BaselineWeightsResult(
        weights=weights,
        status=status,
        diagnostics=diagnostics,
    )


def _budget_simplex_intersects_box(bounds: list[tuple[float, float]]) -> bool:
    s_lo = float(sum(b[0] for b in bounds))
    s_hi = float(sum(b[1] for b in bounds))
    return s_lo <= 1.0 + 1e-9 and s_hi >= 1.0 - 1e-9


def _minimum_variance_slsqp(
    cov: np.ndarray,
    bounds: list[tuple[float, float]],
    *,
    maxiter: int = 2000,
) -> tuple[np.ndarray, Any, bool]:
    """
    Constrained minimum-variance via SLSQP on 0.5 w'Σw with jac Σw, sum(w)=1, box bounds.

    Returns
    -------
    weights :
        Length-N dense weight vector aligned to ``bounds``.
    result :
        ``scipy.optimize.OptimizeResult`` or a minimal namespace for clip fallback.
    fallback_used :
        True if a normalized boundary clip fallback replaced a failed SLSQP run.
    """
    n = len(bounds)
    lo = np.array([float(b[0]) for b in bounds], dtype=float)
    hi = np.array([float(b[1]) for b in bounds], dtype=float)
    diag = np.diag(np.asarray(cov, dtype=float))
    inv_vol = np.zeros(n, dtype=float)
    for i in range(n):
        v = float(diag[i])
        if v > 1e-18:
            inv_vol[i] = 1.0 / float(np.sqrt(v))
    if float(np.sum(inv_vol)) < 1e-12:
        x0 = np.ones(n, dtype=float) / float(n)
    else:
        x0 = inv_vol / float(np.sum(inv_vol))
    x0 = np.clip(x0, lo, hi)
    sw = float(x0.sum())
    if sw > 1e-12:
        x0 = x0 / sw
    else:
        mid = 0.5 * (lo + hi)
        s_mid = float(np.sum(mid))
        x0 = mid / s_mid if s_mid > 1e-12 else np.ones(n, dtype=float) / float(n)

    def penalty_feas(w_vec: np.ndarray) -> float:
        s = float(np.sum(w_vec) - 1.0)
        return s * s

    feas = minimize(
        penalty_feas,
        x0,
        method="L-BFGS-B",
        bounds=list(zip(lo, hi)),
        options={"maxiter": 400},
    )
    x_start = np.asarray(feas.x, dtype=float).copy()
    if not np.all(np.isfinite(x_start)):
        x_start = np.clip(x0, lo, hi)

    def objective(w_vec: np.ndarray) -> float:
        return 0.5 * float(w_vec @ cov @ w_vec)

    def grad_obj(w_vec: np.ndarray) -> np.ndarray:
        return cov @ w_vec

    cons = [{"type": "eq", "fun": lambda w_vec: float(np.sum(w_vec) - 1.0)}]
    scipy_bounds = list(zip(lo, hi))

    res = minimize(
        objective,
        x_start,
        method="SLSQP",
        jac=grad_obj,
        bounds=scipy_bounds,
        constraints=cons,
        options={"maxiter": maxiter, "ftol": 1e-9},
    )
    fallback_used = False
    if not getattr(res, "success", False) or not np.all(np.isfinite(res.x)):
        res = minimize(
            objective,
            x_start,
            method="SLSQP",
            jac=grad_obj,
            bounds=scipy_bounds,
            constraints=cons,
            options={"maxiter": maxiter, "ftol": 1e-12},
        )

    x_out = np.asarray(res.x, dtype=float) if getattr(res, "x", None) is not None else None
    if (
        not getattr(res, "success", False)
        or x_out is None
        or not np.all(np.isfinite(x_out))
    ):
        fx = getattr(feas, "x", None)
        if fx is not None and np.all(np.isfinite(fx)):
            w_fb = np.clip(np.asarray(fx, dtype=float), lo, hi)
        elif getattr(res, "x", None) is not None:
            w_fb = np.clip(np.asarray(res.x, dtype=float), lo, hi)
        else:
            w_fb = None

        if w_fb is None:
            res = SimpleNamespace(
                success=False,
                x=np.full(n, np.nan),
                status=getattr(res, "status", None),
                message="SLSQP failed and no feasible fallback available",
                nit=getattr(res, "nit", None),
            )
        else:
            s = float(w_fb.sum())
            if s > 1e-12:
                w_fb = w_fb / s
                res = SimpleNamespace(
                    success=True,
                    x=w_fb,
                    status=getattr(res, "status", None),
                    message="Normalized feasible point after SLSQP non-convergence",
                    nit=getattr(res, "nit", None),
                )
                fallback_used = True
            else:
                res = SimpleNamespace(
                    success=False,
                    x=np.full(n, np.nan),
                    status=getattr(res, "status", None),
                    message="Fallback normalization failed",
                    nit=getattr(res, "nit", None),
                )

    w_final = np.asarray(res.x, dtype=float)
    return w_final, res, fallback_used


def build_minimum_variance_baseline(
    cfg: PortfolioConfig,
    monthly_returns: pd.DataFrame,
    analysis_end: str,
    window_months: int,
) -> BaselineWeightsResult:
    """
    Minimum-Variance Portfolio (baseline):

    - Universe: same eligible tickers as other baselines (coverage filter on ``cfg.tickers``).
    - **Σ**: monthly covariance on the inner-joined window; when ``young_etf_optimization_policy.enabled``
      (default True), uses :func:`build_dual_covariance_and_mu` like ``run_optimization.py``; otherwise
      sample or Ledoit--Wolf per ``cfg.covariance_shrinkage``. PSD-repaired for the solver.
    - Bounds: :func:`src.optimization._build_bounds` (feasibility cap + optional global / Young caps).
    - Solver: **SLSQP** minimizing ``0.5 w' Σ w`` with Jacobian ``Σ w`` and ``sum(w) = 1``.

    RC caps, mandate gates, turnover, vol targeting, and extra quadratic constraints are **not**
    applied here (v1).
    """
    eligible, coverage = _eligible_universe_from_returns(
        cfg, monthly_returns, analysis_end, window_months
    )
    diagnostics: Dict[str, object] = {
        "universe_eligible": eligible,
        "universe_coverage": coverage,
        "optimizer_name": OPTIMIZER_NAME_MINIMUM_VARIANCE,
        "solver": MINIMUM_VARIANCE_SOLVER,
        "objective": MINIMUM_VARIANCE_OBJECTIVE,
        "active_constraints": [
            "equality: sum(weights) = 1",
            "box: per-asset bounds from feasibility cap and config (min_single / max_single / young caps)",
        ],
    }

    if len(eligible) < 2:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_INFEASIBLE_UNIVERSE",
            diagnostics={
                **diagnostics,
                "reason": "Fewer than 2 eligible assets for Minimum-Variance baseline",
            },
        )

    returns_slice = slice_window(
        monthly_returns[eligible], analysis_end, window_months
    ).dropna(how="any")
    if returns_slice.shape[0] < 2:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_DATA",
            diagnostics={
                **diagnostics,
                "reason": f"Insufficient history for covariance (rows={returns_slice.shape[0]})",
            },
        )

    cols = [str(c) for c in returns_slice.columns]
    young_pol = getattr(cfg, "young_etf_optimization_policy", None) or {}
    dual_enabled = bool(young_pol.get("enabled", True))
    use_shrinkage = bool(getattr(cfg, "covariance_shrinkage", False))
    per_ticker_caps: dict[str, float] | None = None
    young_diag: dict[str, Any] | None = None

    if dual_enabled:
        cov_df, _mu, ydiag = build_dual_covariance_and_mu(
            monthly_returns,
            cols,
            window_months,
            young_pol,
            use_shrinkage_on_core=use_shrinkage,
        )
        young_diag = ydiag
        cols = [str(c) for c in cov_df.columns]
        per_ticker_caps = per_ticker_young_weight_caps(
            young_diag["tickers"],
            float(young_pol.get("max_weight_candidate_or_new_pct", 0.02)),
        )
        if not per_ticker_caps:
            per_ticker_caps = None
        covariance_method = f"young_etf_dual:{young_diag.get('mode', '')}"
        diagnostics["young_etf_dual_mode"] = young_diag.get("mode")
        diagnostics["shrinkage_used"] = bool(use_shrinkage)
    else:
        cov_df = cov_matrix_monthly(returns_slice[cols], ddof=1, use_shrinkage=use_shrinkage)
        covariance_method = "ledoit_wolf_monthly" if use_shrinkage else "sample_monthly_ddof1"
        diagnostics["young_etf_dual_mode"] = None
        diagnostics["shrinkage_used"] = bool(use_shrinkage)

    cov_np_raw = cov_df.reindex(index=cols, columns=cols).fillna(0.0).values
    cov_np, psd_repaired = repair_covariance_psd(cov_np_raw)
    diagnostics["covariance_method"] = covariance_method
    diagnostics["psd_repair_used"] = bool(psd_repaired)

    min_w = (
        float(cfg.min_single_security_weight_pct)
        if cfg.min_single_security_weight_pct is not None
        and float(cfg.min_single_security_weight_pct) > 0
        else float(MIN_WEIGHT_DEFAULT)
    )
    bounds = _build_bounds(
        cols,
        len(cols),
        min_w,
        cfg.max_single_security_weight_pct,
        per_ticker_caps,
    )

    if not _budget_simplex_intersects_box(bounds):
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_INFEASIBLE_BOUNDS",
            diagnostics={
                **diagnostics,
                "reason": (
                    "Weight bounds infeasible for a fully invested portfolio "
                    "(sum of lower bounds > 1 or sum of upper bounds < 1)"
                ),
                "bounds_detail": {
                    cols[i]: {"min": float(bounds[i][0]), "max": float(bounds[i][1])}
                    for i in range(len(cols))
                },
            },
        )

    w_vec, res, fallback_used = _minimum_variance_slsqp(cov_np, bounds)

    if (not np.all(np.isfinite(w_vec))) or w_vec.shape[0] != len(cols):
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_NUMERICAL",
            diagnostics={
                **diagnostics,
                "reason": "Minimum-variance solver returned non-finite weights",
                "fallback_used": bool(fallback_used),
                "solver_success": bool(getattr(res, "success", False)),
                "solver_message": str(getattr(res, "message", "")),
            },
        )

    lo_arr = np.array([b[0] for b in bounds], dtype=float)
    hi_arr = np.array([b[1] for b in bounds], dtype=float)
    w_vec = np.clip(w_vec, lo_arr, hi_arr)
    ssum = float(w_vec.sum())
    if ssum > 1e-12:
        w_vec = w_vec / ssum
    else:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_NUMERICAL",
            diagnostics={**diagnostics, "reason": "Normalized weights sum to ~0"},
        )

    var_p = float(w_vec @ cov_np @ w_vec)
    ann_vol = float(np.sqrt(max(var_p, 0.0) * 12.0))

    weights: Dict[str, float] = {t: 0.0 for t in cfg.tickers}
    for i, t in enumerate(cols):
        weights[t] = float(w_vec[i])

    w_nonzero = {t: float(weights[t]) for t in cols if weights[t] > 1e-14}
    diagnostics.update(
        {
            "eligible_universe": list(cols),
            "final_weights": dict(sorted(w_nonzero.items(), key=lambda x: (-x[1], x[0]))),
            "portfolio_variance": var_p,
            "annualized_volatility": ann_vol,
            "solver_status": getattr(res, "status", None),
            "solver_success": bool(getattr(res, "success", False)),
            "solver_message": str(getattr(res, "message", "")),
            "max_weight": float(np.max(w_vec)) if len(w_vec) else 0.0,
            "min_weight": float(np.min(w_vec)) if len(w_vec) else 0.0,
            "fallback_used": bool(fallback_used),
        }
    )

    tol_sum = 1e-5
    tol_b = 1e-5
    sum_ok = abs(float(np.sum(w_vec)) - 1.0) < tol_sum
    in_bounds = bool(np.all(w_vec >= lo_arr - tol_b) and np.all(w_vec <= hi_arr + tol_b))
    solver_ok = bool(getattr(res, "success", False)) and not fallback_used

    if solver_ok and sum_ok and in_bounds:
        status = "OK"
    elif sum_ok and in_bounds and var_p == var_p:
        status = "APPROXIMATE"
    else:
        status = "FAIL_NUMERICAL"

    return BaselineWeightsResult(weights=weights, status=status, diagnostics=diagnostics)


def export_baseline_weights_txt(
    weights: Dict[str, float],
    rc_series: pd.Series | None,
    label: str,
    output_dir: Path,
) -> None:
    """
    Human-readable weights.txt for baseline variants.
    For Risk-Parity, include realized RC_vol if available.
    """
    lines = [
        f"{label} — final weights",
        "=" * 50,
        "",
    ]
    rc_map = {}
    if rc_series is not None and not rc_series.empty:
        rc_map = {str(t): float(v) for t, v in rc_series.dropna().items()}

    non_zero = {t: w for t, w in weights.items() if w and abs(w) > 1e-12}
    for t in sorted(non_zero.keys(), key=lambda x: (-non_zero[x], x)):
        w = non_zero[t]
        if rc_map:
            rc = rc_map.get(t)
            if rc is not None:
                lines.append(f"  {t}: weight={w:.1%}, RC_vol={rc:.1%}")
            else:
                lines.append(f"  {t}: weight={w:.1%}")
        else:
            lines.append(f"  {t}: weight={w:.1%}")
    lines.append("")
    lines.append(f"Sum of weights: {sum(weights.values()):.1%}")

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "weights.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

