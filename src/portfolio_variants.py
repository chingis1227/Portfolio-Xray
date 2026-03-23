from __future__ import annotations

"""
Portfolio variants (baseline constructions) outside the policy/block framework.

This module intentionally does NOT apply any policy logic to Equal-Weight and Risk-Parity:

- no block logic
- no risk budgets
- no RC caps
- no weight caps
- no max weight limits
- no discretionary overlays
- no hidden policy filters

These variants are pure asset-level baselines built on the same eligible universe
and then evaluated by the existing metrics / stress-test / client-fit pipeline.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from src.config_schema import PortfolioConfig
from src.risk_contrib import cov_matrix_monthly, rc_vol_window
from src.windows import slice_window


BASELINE_EQ_LABEL = "Equal-Weight Portfolio"
BASELINE_RP_LABEL = "Risk Parity Portfolio"


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
    - No block logic, no hidden filters.
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


def build_equal_weight_baseline(
    cfg: PortfolioConfig,
    monthly_returns: pd.DataFrame,
    analysis_end: str,
    window_months: int,
) -> BaselineWeightsResult:
    """
    Equal-Weight Portfolio:
    - Universe: same eligible tickers as main engine, but without any block/policy logic.
    - If N eligible assets, each weight = 1/N.
    - Long-only, fully invested; no caps, no RC constraints, no overlays.
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
                "reason": "Fewer than 2 eligible assets for Equal-Weight baseline",
            },
        )

    n = len(eligible)
    w_eq = 1.0 / float(n)
    weights: Dict[str, float] = {t: 0.0 for t in cfg.tickers}
    for t in eligible:
        weights[t] = w_eq

    return BaselineWeightsResult(
        weights=weights,
        status="OK",
        diagnostics=diagnostics,
    )


def _risk_parity_solver(
    cov_df: pd.DataFrame,
    tickers: Iterable[str],
    *,
    tol: float = 1e-8,
) -> Tuple[Dict[str, float], Dict[str, object]]:
    """
    Pure asset-level risk parity solver (equal percentage contribution to variance).

    Long-only, fully invested; no block structure, no policy caps.
    Solved via SLSQP by minimizing dispersion of variance risk contributions.
    """
    cols = [t for t in tickers if t in cov_df.columns and t in cov_df.index]
    n = len(cols)
    if n == 0:
        return {}, {"status": "FAIL_NO_ASSETS"}

    cov = cov_df.reindex(index=cols, columns=cols).fillna(0.0).values
    target_rc = 1.0 / float(n)

    def _pc_from_w(w_vec: np.ndarray) -> np.ndarray:
        var_p = float(w_vec @ cov @ w_vec)
        if var_p <= 1e-16:
            return np.ones_like(w_vec) / float(len(w_vec))
        m = cov @ w_vec
        return (w_vec * m) / var_p

    def objective(w_vec: np.ndarray) -> float:
        pc = _pc_from_w(w_vec)
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

    if res.success and np.all(np.isfinite(res.x)):
        w = np.clip(res.x, 0.0, None)
        s = float(w.sum())
        if s <= 1e-12:
            return {}, {"status": "FAIL_NUMERICAL"}
        w = w / s
        status = "OK"
    else:
        # Return best feasible approximation from solver output when available.
        if res.x is None or not np.all(np.isfinite(res.x)):
            return {}, {"status": "FAIL_NUMERICAL"}
        w = np.clip(res.x, 0.0, None)
        s = float(w.sum())
        if s <= 1e-12:
            return {}, {"status": "FAIL_NUMERICAL"}
        w = w / s
        status = "APPROXIMATE"

    # Final RC for diagnostics
    pc_final = _pc_from_w(w)
    weights = {t: float(w[i]) for i, t in enumerate(cols)}
    diagnostics = {
        "status": status,
        "iterations": int(res.nit) if hasattr(res, "nit") else None,
        "max_rc_error": float(np.max(np.abs(pc_final - target_rc))),
        "rc_target": target_rc,
        "rc_by_asset": {cols[i]: float(pc_final[i]) for i in range(n)},
    }
    return weights, diagnostics


def build_risk_parity_baseline(
    cfg: PortfolioConfig,
    monthly_returns: pd.DataFrame,
    analysis_end: str,
    window_months: int,
) -> BaselineWeightsResult:
    """
    Risk-Parity Portfolio:
    - Universe: same eligible tickers as main engine (no block logic).
    - Objective: equalized asset-level RC_vol as defined in metrics_specification.md.
    - Constraints: long-only, fully invested. No block budgets, no caps.
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
                lines.append(f"  {t}: weight={w:.3f}, RC_vol={rc:.3f}")
            else:
                lines.append(f"  {t}: weight={w:.3f}")
        else:
            lines.append(f"  {t}: weight={w:.3f}")
    lines.append("")
    lines.append(f"Sum of weights: {sum(weights.values()):.3f}")

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "weights.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

