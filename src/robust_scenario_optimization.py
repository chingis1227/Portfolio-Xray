"""
Scenario-Based Robust Optimization v1 — lower-half mean default objective.

Additive module: does not alter mandate gates or main policy optimizer.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from src.optimization import _build_bounds, get_risk_portfolio_tickers
from src.optimization_status import APPROXIMATE_SOLVER, CLEAN_SOLVE
from src.risk_parity_spinu import repair_covariance_psd
from src.historical_stress_fallback import asset_betas_from_stress_report
from src.stress import PRODUCTION_FACTOR_BETA_KEYS, _scenario_return_per_asset

ROBUST_SCENARIO_OPTIMIZATION_VERSION = "robust_scenario_optimization_v1"

OBJECTIVE_LOWER_HALF_MEAN = "lower_half_mean"
OBJECTIVE_MAXIMIN = "maximin"
OBJECTIVE_HYBRID_LEGACY = "hybrid_legacy"


def lower_half_mean(returns: np.ndarray) -> tuple[float, int, np.ndarray]:
    """Mean of the ceil(N/2) smallest scenario returns (worst-first tail)."""
    r = np.asarray(returns, dtype=float).ravel()
    n = len(r)
    k = max(1, int(np.ceil(n / 2)))
    order = np.argsort(r)
    idx = order[:k]
    return float(np.mean(r[idx])), k, idx


def discrete_percentiles(sorted_returns: np.ndarray, qs: tuple[float, ...]) -> dict[str, float | None]:
    """Empirical percentiles on discrete scenario returns (diagnostic only)."""
    r = np.sort(np.asarray(sorted_returns, dtype=float).ravel())
    n = len(r)
    out: dict[str, float | None] = {}
    if n == 0:
        for q in qs:
            out[f"p{int(q * 100)}"] = None
        return out
    for q in qs:
        pos = q * (n - 1)
        lo = int(np.floor(pos))
        hi = int(np.ceil(pos))
        if lo == hi:
            val = float(r[lo])
        else:
            val = float(r[lo] * (hi - pos) + r[hi] * (pos - lo))
        out[f"p{int(q * 100)}"] = val
    return out


def _nested_cov_to_sigma(keys: list[str], nested: dict[str, dict[str, float]] | None) -> np.ndarray:
    if not nested:
        return np.eye(len(keys)) * 1e-8
    mat = np.zeros((len(keys), len(keys)), dtype=float)
    for i, ti in enumerate(keys):
        row = nested.get(ti) or {}
        for j, tj in enumerate(keys):
            mat[i, j] = float(row.get(tj, 0.0))
    mat, _ = repair_covariance_psd(mat)
    return mat


def _asset_betas_df_from_stress(
    stress_report: dict[str, Any] | None,
    tickers: list[str],
) -> tuple[pd.DataFrame, list[str]]:
    """
    Load per-asset factor betas for synthetic shocks (same naming as ``_scenario_return_per_asset``).

    Prefers ``stress_report[\"asset_factor_betas\"]`` (written by ``run_report`` / ``run_optimization``).
    If absent, falls back to replicating ``factor_betas_5y`` across all tickers (explicit warning).
    """
    warnings: list[str] = []
    canon_cols = list(PRODUCTION_FACTOR_BETA_KEYS)

    raw_block: dict[str, Any] | None = None
    if stress_report and isinstance(stress_report.get("asset_factor_betas"), dict):
        raw_block = stress_report.get("asset_factor_betas")  # type: ignore[assignment]
    elif stress_report and isinstance(stress_report.get("asset_factor_betas_weekly"), dict):
        raw_block = stress_report.get("asset_factor_betas_weekly")  # type: ignore[assignment]

    df = asset_betas_from_stress_report(stress_report, tickers)
    df = df.reindex(list(tickers)).fillna(0.0)

    used_fallback = False
    need_fallback = raw_block is None or df.empty or not any(str(c).startswith("beta_") for c in df.columns)
    if need_fallback:
        if raw_block is None:
            warnings.append("robust_scenario_opt_no_asset_factor_betas_in_stress_report")
        else:
            warnings.append("robust_scenario_opt_asset_factor_betas_unparsed_or_missing_columns")
        fb = (stress_report or {}).get("factor_betas_5y") or (stress_report or {}).get("factor_betas") or {}
        if isinstance(fb, dict) and fb:
            warnings.append(
                "robust_scenario_opt_fallback_portfolio_factor_betas_5y_replicated_to_all_assets"
            )
            row = {k: float(fb.get(k, 0.0) or 0.0) for k in canon_cols}
            df = pd.DataFrame([row.copy() for _ in tickers], index=list(tickers), dtype=float)
            used_fallback = True
        else:
            warnings.append("robust_scenario_opt_no_usable_betas_synthetic_shocks_may_be_zero")
            df = pd.DataFrame(0.0, index=list(tickers), columns=canon_cols, dtype=float)

    for col in canon_cols:
        if col not in df.columns:
            df[col] = 0.0
            warnings.append(f"robust_scenario_opt_missing_beta_column_zero_fill:{col}")

    if raw_block is not None and not used_fallback:
        for t in tickers:
            keys_try = [t, str(t).upper()]
            if not any(k in raw_block for k in keys_try):
                warnings.append(f"robust_scenario_opt_ticker_missing_from_asset_factor_betas:{t}")

    return df.loc[:, canon_cols], warnings


@dataclass
class RobustOptInputs:
    ticker_order: list[str]
    C: np.ndarray
    scenario_ids: list[str]
    scenario_roles: list[str]
    confidence_weights: np.ndarray
    Sigma_base: np.ndarray
    mu_base: np.ndarray
    objective_mode: str = OBJECTIVE_LOWER_HALF_MEAN
    lambdas: dict[str, float] = field(default_factory=dict)
    stress_indices: list[int] = field(default_factory=list)
    beta_load_warnings: list[str] = field(default_factory=list)


def build_robust_optimization_inputs(
    *,
    scenario_library_normalized: dict[str, Any],
    stress_report: dict[str, Any] | None,
    risk_tickers: list[str],
    objective_mode: str = OBJECTIVE_LOWER_HALF_MEAN,
    lambdas: dict[str, float] | None = None,
) -> RobustOptInputs:
    scenarios = scenario_library_normalized.get("scenarios") or []
    lam = dict(lambdas or {})
    lam.setdefault("vol", 0.05)
    lam.setdefault("stress_penalty", 0.02)
    lam.setdefault("hhi", 0.01)

    tickers = [str(t).strip() for t in risk_tickers]
    n = len(tickers)
    base_row = next((x for x in scenarios if str(x.get("scenario_id")) == "base_historical"), None)
    if base_row is None:
        raise ValueError("robust optimization requires base_historical in scenario_library_normalized")

    mu_map = base_row.get("expected_returns_by_asset") or {}
    if not isinstance(mu_map, dict) or len(mu_map) == 0:
        raise ValueError("base_historical.expected_returns_by_asset missing")
    mu_base = np.array([float(mu_map.get(t, 0.0)) for t in tickers], dtype=float)

    a_cov = base_row.get("asset_covariance_monthly_equivalent")
    if not isinstance(a_cov, dict):
        a_cov = (base_row.get("asset_covariance") or {}).get("matrix") if isinstance(base_row.get("asset_covariance"), dict) else {}
    Sigma_base = _nested_cov_to_sigma(tickers, a_cov if isinstance(a_cov, dict) else None)

    rows_pool: list[dict[str, Any]] = []
    for s in scenarios:
        if not isinstance(s, dict):
            continue
        sid = str(s.get("scenario_id") or "")
        role = str(s.get("optimization_role") or "")
        st = str(s.get("scenario_type") or "")
        if sid == "base_historical":
            rows_pool.append(s)
            continue
        if role in {"hard_stress_constraint", "soft_constraint"} and st in {"historical_stress", "synthetic_stress"}:
            rows_pool.append(s)

    scenario_ids: list[str] = []
    coeffs: list[np.ndarray] = []
    roles: list[str] = []
    confs: list[float] = []
    stress_idx: list[int] = []

    asset_betas_df, beta_warnings = _asset_betas_df_from_stress(stress_report, tickers)

    for i_scen, s in enumerate(rows_pool):
        sid = str(s.get("scenario_id"))
        st = str(s.get("scenario_type"))
        role = str(s.get("optimization_role"))
        cw = float(s.get("confidence_weight") or 0.0)
        c = np.zeros(n, dtype=float)
        if sid == "base_historical":
            c = mu_base.copy()
        elif st == "historical_stress":
            sar = s.get("scenario_asset_return")
            if isinstance(sar, dict):
                c = np.array([float(sar.get(t, sar.get(str(t).upper(), 0.0)) or 0.0) for t in tickers], dtype=float)
            else:
                continue
        elif st == "synthetic_stress":
            shock = s.get("scenario_factor_move")
            if isinstance(shock, dict) and shock:
                shock_f = {str(k): float(v) for k, v in shock.items() if isinstance(v, (int, float))}
                r_asset = _scenario_return_per_asset(shock_f, asset_betas_df, tickers)
                c = np.array([float(r_asset.reindex([t]).fillna(0.0).iloc[0]) for t in tickers], dtype=float)
            else:
                sr = s.get("scenario_shock_return")
                if sr is not None and np.isfinite(float(sr)):
                    c = np.full(n, float(sr) / max(n, 1))
                else:
                    continue
        else:
            continue
        scenario_ids.append(sid)
        coeffs.append(c)
        roles.append(role)
        confs.append(cw)
        if sid != "base_historical":
            stress_idx.append(len(scenario_ids) - 1)

    if not coeffs:
        raise ValueError("no scenarios built for robust optimization pool")

    C = np.vstack(coeffs)
    return RobustOptInputs(
        ticker_order=tickers,
        C=C,
        scenario_ids=scenario_ids,
        scenario_roles=roles,
        confidence_weights=np.array(confs, dtype=float),
        Sigma_base=Sigma_base,
        mu_base=mu_base,
        objective_mode=objective_mode,
        lambdas=lam,
        stress_indices=stress_idx,
        beta_load_warnings=beta_warnings,
    )


def compute_scenario_returns_vector(w: np.ndarray, inputs: RobustOptInputs) -> np.ndarray:
    return inputs.C @ np.asarray(w, dtype=float)


def robust_objective_loss(
    w: np.ndarray,
    inputs: RobustOptInputs,
) -> float:
    """Scalar loss to minimize (negative primary + regularizers)."""
    w = np.asarray(w, dtype=float)
    r = compute_scenario_returns_vector(w, inputs)
    mode = inputs.objective_mode
    lam = inputs.lambdas

    if mode == OBJECTIVE_MAXIMIN:
        primary = -float(np.min(r))
    elif mode == OBJECTIVE_HYBRID_LEGACY:
        mu_p = float(inputs.mu_base @ w)
        sig = float(np.sqrt(max(w @ inputs.Sigma_base @ w, 0.0)))
        primary = -mu_p + float(lam.get("vol", 0.05)) * sig
        for j in inputs.stress_indices:
            if j < len(r):
                primary += float(lam.get("stress_penalty", 0.02)) * float(inputs.confidence_weights[j]) * max(
                    0.0, -float(r[j])
                )
        hhi = float(np.sum(w**2))
        primary += float(lam.get("hhi", 0.01)) * hhi
        return primary
    else:
        lh, _, _ = lower_half_mean(r)
        primary = -lh
        sig = float(np.sqrt(max(w @ inputs.Sigma_base @ w, 0.0)))
        primary += float(lam.get("vol", 0.05)) * sig
        for j in inputs.stress_indices:
            if j < len(r):
                primary += float(lam.get("stress_penalty", 0.02)) * float(inputs.confidence_weights[j]) * max(
                    0.0, -float(r[j])
                )
        hhi = float(np.sum(w**2))
        primary += float(lam.get("hhi", 0.01)) * hhi
        return primary


def run_robust_scenario_optimization(
    inputs: RobustOptInputs,
    *,
    bounds: list[tuple[float, float]],
    warm_starts: list[np.ndarray] | None = None,
) -> dict[str, Any]:
    n = len(inputs.ticker_order)
    cons = {"type": "eq", "fun": lambda x: float(np.sum(x) - 1.0)}
    best_x: np.ndarray | None = None
    best_loss = float("inf")
    msg = ""
    best_success = False
    best_status: int | None = None
    best_nit: int | None = None

    starts: list[np.ndarray] = []
    if warm_starts:
        for ws in warm_starts:
            v = np.asarray(ws, dtype=float).ravel()
            if len(v) == n:
                v = np.maximum(v, 1e-8)
                v = v / v.sum()
                starts.append(v)
    if not starts:
        starts.append(np.ones(n) / n)

    for x0 in starts:
        res = minimize(
            robust_objective_loss,
            x0,
            args=(inputs,),
            method="SLSQP",
            bounds=bounds,
            constraints=cons,
            options={"maxiter": 800, "ftol": 1e-10},
        )
        if res.fun < best_loss:
            best_loss = float(res.fun)
            best_x = np.asarray(res.x, dtype=float)
            msg = str(res.message)
            best_success = bool(res.success)
            best_status = int(res.status) if getattr(res, "status", None) is not None else None
            best_nit = int(res.nit) if getattr(res, "nit", None) is not None else None

    assert best_x is not None
    w_opt = best_x / max(best_x.sum(), 1e-12)
    r_opt = compute_scenario_returns_vector(w_opt, inputs)
    lh, k_lh, idx_lh = lower_half_mean(r_opt)
    pct = discrete_percentiles(r_opt, (0.05, 0.10, 0.25))
    quality_status = CLEAN_SOLVE if best_success else APPROXIMATE_SOLVER

    return {
        "weights_vec": w_opt,
        "scenario_returns": r_opt,
        "lower_half_mean": lh,
        "lower_half_k": k_lh,
        "lower_half_indices": idx_lh.tolist(),
        "objective_loss_at_optimum": best_loss,
        "optimizer_message": msg,
        "solver": {
            "name": "SLSQP",
            "success": bool(best_success),
            "status": "OK" if best_success else "APPROXIMATE",
            "raw_status": best_status,
            "message": msg,
            "iterations": best_nit,
            "multi_start_count": len(starts),
            "fallback_used": False,
            "fallback_reason": None,
            "optimization_quality_status": quality_status,
        },
        "percentile_diagnostics_only": True,
        "percentiles_discrete": pct,
        "scenario_ids_order": list(inputs.scenario_ids),
    }


def export_robust_optimization_outputs(
    result: dict[str, Any],
    inputs: RobustOptInputs,
    *,
    output_dir: Path,
    comparisons: dict[str, dict[str, float]] | None = None,
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    weights_dict = {inputs.ticker_order[i]: round(float(result["weights_vec"][i]), 6) for i in range(len(inputs.ticker_order))}

    summary = {
        "version": ROBUST_SCENARIO_OPTIMIZATION_VERSION,
        "objective_mode": inputs.objective_mode,
        "lambdas": inputs.lambdas,
        "lower_half_mean": round(float(result["lower_half_mean"]), 6),
        "lower_half_k": int(result["lower_half_k"]),
        "base_expected_return_monthly": round(float(inputs.mu_base @ result["weights_vec"]), 6),
        "base_vol_monthly": round(float(np.sqrt(max(result["weights_vec"] @ inputs.Sigma_base @ result["weights_vec"], 0.0))), 6),
        "percentile_diagnostics_only": bool(result.get("percentile_diagnostics_only")),
        "percentiles_discrete": {k: (round(float(v), 6) if v is not None else None) for k, v in (result.get("percentiles_discrete") or {}).items()},
        "sorted_scenario_returns_at_optimum": [
            {"scenario_id": inputs.scenario_ids[i], "return": round(float(result["scenario_returns"][i]), 6)}
            for i in np.argsort(result["scenario_returns"])
        ],
        "comparisons": comparisons or {},
        "optimizer_message": result.get("optimizer_message"),
        "solver": dict(result.get("solver") or {}),
        "solver_success": (result.get("solver") or {}).get("success"),
        "solver_status": (result.get("solver") or {}).get("status"),
        "fallback_used": (result.get("solver") or {}).get("fallback_used", False),
        "fallback_reason": (result.get("solver") or {}).get("fallback_reason"),
        "optimization_quality_status": (result.get("solver") or {}).get("optimization_quality_status"),
        "beta_load_warnings": list(inputs.beta_load_warnings or []),
    }

    paths: dict[str, str] = {}
    p_json = output_dir / "robust_optimization_v1_summary.json"
    p_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    paths["robust_optimization_v1_summary.json"] = str(p_json)

    p_wj = output_dir / "robust_optimization_weights.json"
    p_wj.write_text(json.dumps(weights_dict, indent=2), encoding="utf-8")
    paths["robust_optimization_weights.json"] = str(p_wj)

    lines = [f"{t}: {weights_dict[t]}" for t in inputs.ticker_order]
    p_wt = output_dir / "robust_optimization_weights.txt"
    p_wt.write_text("\n".join(lines), encoding="utf-8")
    paths["robust_optimization_weights.txt"] = str(p_wt)

    scen_df = pd.DataFrame(
        {
            "scenario_id": inputs.scenario_ids,
            "optimization_role": inputs.scenario_roles,
            "confidence_weight": inputs.confidence_weights,
            "return_at_optimum": result["scenario_returns"],
        }
    )
    p_so = output_dir / "robust_optimization_scenario_outcomes.csv"
    scen_df.to_csv(p_so, index=False)
    paths["robust_optimization_scenario_outcomes.csv"] = str(p_so)

    cand_df = pd.DataFrame({"scenario_id": inputs.scenario_ids, "role": inputs.scenario_roles})
    p_cand = output_dir / "robust_optimization_candidate_scenarios.csv"
    cand_df.to_csv(p_cand, index=False)
    paths["robust_optimization_candidate_scenarios.csv"] = str(p_cand)

    diag_df = pd.DataFrame([{"metric": "lower_half_mean", "value": result["lower_half_mean"]}])
    p_diag = output_dir / "robust_optimization_diagnostics.csv"
    diag_df.to_csv(p_diag, index=False)
    paths["robust_optimization_diagnostics.csv"] = str(p_diag)

    return paths


__all__ = [
    "ROBUST_SCENARIO_OPTIMIZATION_VERSION",
    "OBJECTIVE_HYBRID_LEGACY",
    "OBJECTIVE_LOWER_HALF_MEAN",
    "OBJECTIVE_MAXIMIN",
    "RobustOptInputs",
    "_asset_betas_df_from_stress",
    "build_robust_optimization_inputs",
    "compute_scenario_returns_vector",
    "discrete_percentiles",
    "export_robust_optimization_outputs",
    "lower_half_mean",
    "robust_objective_loss",
    "run_robust_scenario_optimization",
]
