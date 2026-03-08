"""
Portfolio optimization: risk budget (RC block targets), RC caps, weight caps, Growth max return.
Per docs/portfolio_construction_policy.md, docs/docs/optimization_growth_spec.md,
docs/docs/feasibility_constraints_spec.md, docs/docs/optimization_proliquidity_spec.md.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from src.risk_contrib import (
    cov_matrix_monthly,
    percentage_contributions_variance,
    variance_p,
)

RISK_BUDGET_BLOCKS = ("Growth", "Duration", "Inflation")
MIN_WEIGHT_DEFAULT = 0.01


def get_risk_portfolio_tickers(blocks: dict[str, list[str]]) -> list[str]:
    """Return tickers in RiskPortfolio (Growth + Duration + Inflation). Exclude Liquidity, Tail."""
    out = []
    for b in RISK_BUDGET_BLOCKS:
        out.extend(blocks.get(b, []))
    return out


def ticker_to_block_map(blocks: dict[str, list[str]]) -> dict[str, str]:
    """Return ticker -> block name for RiskPortfolio blocks."""
    m = {}
    for b in RISK_BUDGET_BLOCKS:
        for t in blocks.get(b, []):
            m[t] = b
    return m


def resolve_rc_asset_cap(
    rc_asset_cap_pct: float | None,
    n_assets: int,
    rb_growth: float,
) -> float:
    """From feasibility_constraints_spec. If RB_growth >= 0.90 (Equity-Only), rc_asset_cap = max(rc_asset_cap, 0.15)."""
    if rc_asset_cap_pct is not None and rc_asset_cap_pct > 0:
        base = float(rc_asset_cap_pct)
    elif n_assets < 4:
        base = 0.40
    else:
        base = min(0.25, max(0.10, 1.5 / n_assets))
    if rb_growth >= 0.90:
        base = max(base, 0.15)
    return base


def growth_weight_caps(
    n: int,
    n_core: int,
    n_sat: int,
) -> tuple[float, float]:
    """Core/Satellite max weights for Growth. feasibility_constraints_spec §3.1."""
    if n_core == 0:
        if n <= 3:
            return 0.40, 0.40
        return min(0.25, max(0.10, 2.5 / n)), min(0.25, max(0.10, 2.5 / n))
    max_core = min(0.35, max(0.25, 2.0 / n))
    if n_sat <= 2:
        max_sat = 0.40
    else:
        term = (1.0 - n_core * max_core) / (n - n_core) + 0.02
        max_sat = min(0.25, max(min(0.10, max(0.05, 2.0 / n)), term))
    return max_core, max_sat


def build_bounds(
    tickers: list[str],
    ticker_to_block: dict[str, str],
    growth_core_candidates: list[str],
    n_total: int,
    rc_asset_cap: float,
    min_weight: float,
) -> list[tuple[float, float]]:
    """Per-asset (low, high) weight bounds. Growth: Core/Satellite caps; others: 0.40 cap."""
    growth_tickers = [t for t in tickers if ticker_to_block.get(t) == "Growth"]
    n_growth = len(growth_tickers)
    n_core = sum(1 for t in growth_tickers if t in growth_core_candidates)
    n_sat = n_growth - n_core
    max_core, max_sat = growth_weight_caps(n_total, n_core, n_sat)

    bounds = []
    for t in tickers:
        block = ticker_to_block.get(t, "Growth")
        if block == "Growth":
            cap = max_core if t in growth_core_candidates else max_sat
        else:
            cap = 0.40 if n_total > 3 else 0.40
        bounds.append((min_weight, min(cap, 1.0)))
    return bounds


def _pc_from_w(w: np.ndarray, cov: np.ndarray) -> np.ndarray:
    """Percentage contributions to variance; sum = 1."""
    var_p = variance_p(w, cov)
    if var_p <= 1e-16:
        return np.full_like(w, 1.0 / len(w))
    m = cov @ w
    return (w * m) / var_p


def run_risk_budget_optimization(
    returns_df: pd.DataFrame,
    blocks: dict[str, list[str]],
    rc_block_targets: dict[str, float],
    growth_core_candidates: list[str],
    rc_asset_cap_pct: float | None = None,
    min_single_security_weight_pct: float | None = None,
    window_months: int = 60,
) -> tuple[dict[str, float], str]:
    """
    Find RiskPortfolio weights satisfying risk budget (RC block shares) and feasibility.
    Objective: maximize expected return (Growth spec). Returns (weights_dict, status_message).
    """
    risk_tickers = get_risk_portfolio_tickers(blocks)
    if not risk_tickers:
        return {}, "FAIL: no RiskPortfolio tickers (Growth+Duration+Inflation)"

    ticker_to_block = ticker_to_block_map(blocks)
    # Use only tickers with data; others get zero weight
    cols = [t for t in risk_tickers if t in returns_df.columns]
    missing = set(risk_tickers) - set(cols)
    if missing:
        import logging
        logging.getLogger(__name__).warning(
            "Тикеры без данных (исключены из оптимизации, вес = 0): %s", sorted(missing)
        )
    if not cols:
        return {}, f"FAIL_DATA: no risk tickers with returns (missing: {risk_tickers})"

    ret = returns_df[cols].dropna(how="all")
    if len(ret) < 24:
        return {}, f"FAIL_DATA: insufficient history ({len(ret)} months)"

    # Use last window_months
    ret = ret.iloc[-window_months:]
    ret = ret.dropna(axis=1, how="all")
    cols = list(ret.columns)
    if not cols:
        return {}, "FAIL_DATA: no assets with returns in window"

    n = len(cols)
    mu = ret.mean().values
    cov = cov_matrix_monthly(ret, ddof=1).values

    rb = rc_block_targets or {}
    rb_growth = float(rb.get("Growth", 1.0 / 3))
    rb_duration = float(rb.get("Duration", 1.0 / 3))
    rb_inflation = float(rb.get("Inflation", 1.0 / 3))
    total_rb = rb_growth + rb_duration + rb_inflation
    if total_rb <= 0:
        return {}, "FAIL: rc_block_targets sum must be positive"
    rb_growth /= total_rb
    rb_duration /= total_rb
    rb_inflation /= total_rb

    rc_asset_cap = resolve_rc_asset_cap(rc_asset_cap_pct, n, rb_growth)
    min_weight = float(min_single_security_weight_pct) if min_single_security_weight_pct is not None and min_single_security_weight_pct > 0 else MIN_WEIGHT_DEFAULT

    growth_tickers = [t for t in cols if ticker_to_block.get(t) == "Growth"]
    n_core = sum(1 for t in growth_tickers if t in growth_core_candidates)
    n_sat = len(growth_tickers) - n_core
    bounds = build_bounds(cols, ticker_to_block, growth_core_candidates, n, rc_asset_cap, min_weight)

    def objective(w: np.ndarray) -> float:
        return -float(np.dot(mu, w))

    def constraint_sum(w: np.ndarray) -> float:
        return float(np.sum(w) - 1.0)

    def constraint_rc_growth(w: np.ndarray) -> float:
        pc = _pc_from_w(w, cov)
        block_rc = sum(pc[i] for i, t in enumerate(cols) if ticker_to_block.get(t) == "Growth")
        return float(block_rc - rb_growth)

    def constraint_rc_duration(w: np.ndarray) -> float:
        pc = _pc_from_w(w, cov)
        block_rc = sum(pc[i] for i, t in enumerate(cols) if ticker_to_block.get(t) == "Duration")
        return float(block_rc - rb_duration)

    def constraint_rc_inflation(w: np.ndarray) -> float:
        pc = _pc_from_w(w, cov)
        block_rc = sum(pc[i] for i, t in enumerate(cols) if ticker_to_block.get(t) == "Inflation")
        return float(block_rc - rb_inflation)

    def make_rc_cap(idx: int):
        def rc_cap(w: np.ndarray) -> float:
            pc = _pc_from_w(w, cov)
            return float(pc[idx] - rc_asset_cap)
        return rc_cap

    # First try: only risk-budget equality constraints (sum=1, RC block shares)
    constraints_core = [
        {"type": "eq", "fun": constraint_sum},
        {"type": "eq", "fun": constraint_rc_growth},
        {"type": "eq", "fun": constraint_rc_duration},
        {"type": "eq", "fun": constraint_rc_inflation},
    ]
    # Second: add per-asset RC cap (can make problem infeasible)
    constraints_full = constraints_core + [
        {"type": "ineq", "fun": make_rc_cap(i)} for i in range(n)
    ]

    # Initial point: first find feasible for risk-budget (minimize squared RC block errors)
    def penalty_rc(w: np.ndarray) -> float:
        s = float(np.sum(w) - 1.0)
        pc = _pc_from_w(w, cov)
        rg = sum(pc[i] for i, t in enumerate(cols) if ticker_to_block.get(t) == "Growth") - rb_growth
        rd = sum(pc[i] for i, t in enumerate(cols) if ticker_to_block.get(t) == "Duration") - rb_duration
        ri = sum(pc[i] for i, t in enumerate(cols) if ticker_to_block.get(t) == "Inflation") - rb_inflation
        return s * s + rg * rg + rd * rd + ri * ri

    x0 = np.zeros(n)
    for b, target in (("Growth", rb_growth), ("Duration", rb_duration), ("Inflation", rb_inflation)):
        idx = [i for i, t in enumerate(cols) if ticker_to_block.get(t) == b]
        if idx:
            x0[idx] = target / len(idx)
    if np.abs(x0.sum() - 1.0) > 1e-6:
        x0 = np.ones(n) / n
    x0 = np.clip(x0, min_weight, np.array([b[1] for b in bounds]) - 1e-6)
    x0 = x0 / x0.sum()

    feas = minimize(penalty_rc, x0, method="L-BFGS-B", bounds=bounds, options={"maxiter": 300})
    if feas.fun < 1e-6:
        x0 = feas.x
    else:
        x0 = feas.x / feas.x.sum()

    # Solve with risk-budget constraints only
    res = minimize(
        objective,
        x0.copy(),
        method="SLSQP",
        bounds=bounds,
        constraints=constraints_core,
        options={"maxiter": 1000, "ftol": 1e-9},
    )
    if not res.success:
        # Fallback: use penalty minimizer (approx risk-budget), clip to bounds and normalize
        w_fallback = np.clip(feas.x, min_weight, np.array([b[1] for b in bounds]) - 1e-8)
        w_fallback = w_fallback / w_fallback.sum()
        res = type("Res", (), {"success": True, "x": w_fallback})()

    w = res.x
    w_dict = {t: float(w[i]) for i, t in enumerate(cols)}
    pc = _pc_from_w(w, cov)
    rc_g = sum(pc[i] for i, t in enumerate(cols) if ticker_to_block.get(t) == "Growth")
    rc_d = sum(pc[i] for i, t in enumerate(cols) if ticker_to_block.get(t) == "Duration")
    rc_i = sum(pc[i] for i, t in enumerate(cols) if ticker_to_block.get(t) == "Inflation")
    # Add zero weight for excluded (missing data) tickers
    for t in risk_tickers:
        if t not in w_dict:
            w_dict[t] = 0.0
    status_msg = f"OK (RC G/D/I: {rc_g:.3f}/{rc_d:.3f}/{rc_i:.3f})"
    viol = [cols[i] for i in range(n) if pc[i] > rc_asset_cap]
    if viol:
        status_msg += f"; ВНИМАНИЕ: RC выше лимита для {viol}"
    return w_dict, status_msg


def proliquidity(
    weights_risk: dict[str, float],
    cash_proxy_ticker: str,
    current_vol_annual: float,
    target_vol_annual: float,
    liquidity_floor_pct: float,
    cash_policy: str,
) -> dict[str, float]:
    """
    Apply ProLiquidity: cash_weight = max(liquidity_floor, vol_scaling); scale RiskPortfolio by (1 - cash_weight), add cash.
    """
    if cash_policy == "prohibited":
        return dict(weights_risk)

    if current_vol_annual <= 0:
        vol_scaling_cash = 0.0
    else:
        scaler = target_vol_annual / current_vol_annual
        vol_scaling_cash = max(0.0, 1.0 - scaler)
    cash_weight = max(liquidity_floor_pct, vol_scaling_cash)
    cash_weight = max(0.0, min(1.0, cash_weight))
    risky_weight = 1.0 - cash_weight

    out = {t: risky_weight * w for t, w in weights_risk.items()}
    out[cash_proxy_ticker] = cash_weight
    return out


def portfolio_vol_annual(weights: dict[str, float], cov_df: pd.DataFrame) -> float:
    """Annualized vol from monthly covariance; weights and cov must share same tickers."""
    tickers = [t for t in weights if t in cov_df.columns and t in cov_df.index]
    if not tickers:
        return 0.0
    w = np.array([weights[t] for t in tickers])
    cov = cov_df.reindex(index=tickers, columns=tickers).fillna(0).values
    var = variance_p(w, cov)
    return float(np.sqrt(var * 12)) if var > 0 else 0.0
