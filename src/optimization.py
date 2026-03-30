"""
Portfolio optimization: risk budget (RC block targets), RC caps, weight caps, Growth max return.
Per docs/portfolio_construction_policy.md, docs/docs/optimization_growth_spec.md,
docs/docs/feasibility_constraints_spec.md, docs/docs/optimization_proliquidity_spec.md.
"""
from __future__ import annotations

import math
import numpy as np
import pandas as pd
from scipy.optimize import minimize

from policy_math.feasibility import (
    DEFAULT_RC_CAP_RB_K_MULTIPLIER,
    FeasibilityContext,
    RC_CAP_MODE_GLOBAL,
    RC_CAP_MODE_PER_BLOCK_RB_K,
    check_feasible,
    compute_rc_caps_by_block_from_targets,
    resolve_weight_caps,
)
from src.blocks import get_ticker_to_block_for_rb
from src.config_schema import GROWTH_EM_DEBT_KEY, GROWTH_HY_KEY
from src.risk_contrib import (
    build_rc_cap_per_ticker,
    cov_matrix_monthly,
    percentage_contributions_variance,
    resolve_rc_asset_cap,
    variance_p,
)

RISK_BUDGET_BLOCKS = ("Growth", "Duration", "Inflation")
# Sub-blocks of Growth: tickers participate in RiskPortfolio and count as Growth for RC; separate 10% RC caps apply
GROWTH_SUB_BLOCKS = (GROWTH_HY_KEY, GROWTH_EM_DEBT_KEY)
MIN_WEIGHT_DEFAULT = 0.01
HY_EM_RC_CAP_FRACTION = 0.10  # RC_vol(HY) and RC_vol(EM_debt) <= 10% of RC_vol(Growth)
# RB corridor: realized block RC must be within target ± this (hard constraint)
RB_CORRIDOR_PP = 0.05
RB_RANGE_EXPANSION_PP = 0.05
RB_GRID_STEP_PP = 0.01
RC_CAP_PENALTY_LAMBDA_DEFAULT = 25.0
# Default weight for Herfindahl(sum RC_i^2) in risk_skeleton stage — spreads RC_vol when feasible
DEFAULT_RISK_SKELETON_CONCENTRATION_LAMBDA = 10.0
# Optimization objective modes (production Main default: two-stage risk_skeleton → max_return; see docs/two_stage_optimization.md)
OBJECTIVE_MODE_MAX_RETURN = "max_return"
# Equal RC_vol per asset: minimize sum_i (RC_i - 1/n)^2 (+ RC-cap penalty)
OBJECTIVE_MODE_RISK_PARITY = "risk_parity"
# Feasible skeleton: RC-cap penalty + minimize risk concentration (HHI on RC_vol shares)
OBJECTIVE_MODE_RISK_SKELETON = "risk_skeleton"
OBJECTIVE_MODES = (OBJECTIVE_MODE_MAX_RETURN, OBJECTIVE_MODE_RISK_PARITY, OBJECTIVE_MODE_RISK_SKELETON)


def get_risk_portfolio_tickers(blocks: dict[str, list[str]]) -> list[str]:
    """Return tickers in RiskPortfolio: Growth + Duration + Inflation + Growth_HY + Growth_EM_debt. Exclude Liquidity, Tail."""
    out = []
    for b in RISK_BUDGET_BLOCKS:
        out.extend(blocks.get(b, []))
    for b in GROWTH_SUB_BLOCKS:
        out.extend(blocks.get(b, []))
    return out


def ticker_to_block_map(blocks: dict[str, list[str]]) -> dict[str, str]:
    """Return ticker -> block name for RiskPortfolio. Alias for get_ticker_to_block_for_rb (blocks module)."""
    return get_ticker_to_block_for_rb(blocks)


def growth_weight_caps(
    n: int,
    n_core: int,
    n_sat: int,
    rb_growth: float | None = None,
) -> tuple[float, float]:
    """
    Core/Satellite max weights for Growth.
    Delegates to policy_math.feasibility.resolve_weight_caps (single source of truth).
    """
    equity_only = bool(rb_growth is not None and rb_growth >= 0.90)
    caps = resolve_weight_caps(n_total=n, n_core=n_core, n_sat=n_sat, equity_only=equity_only)
    max_core = caps["max_weight_core"] or 0.0
    max_sat = caps["max_weight_sat"] or 0.0
    return max_core, max_sat


def build_bounds(
    tickers: list[str],
    ticker_to_block: dict[str, str],
    growth_core_candidates: list[str],
    n_total: int,
    min_weight: float,
    max_single_security_weight_pct: float | None = None,
    rb_growth: float | None = None,
    per_ticker_max_weight: dict[str, float] | None = None,
) -> list[tuple[float, float]]:
    """Per-asset (low, high) weight bounds. Growth: Core/Satellite (or Equity-Only if rb_growth>=0.9); others: 0.40.
    If max_single_security_weight_pct is set, it caps all assets (override)."""
    growth_tickers = [t for t in tickers if ticker_to_block.get(t) == "Growth"]
    n_growth = len(growth_tickers)
    n_core = sum(1 for t in growth_tickers if t in growth_core_candidates)
    n_sat = n_growth - n_core
    max_core, max_sat = growth_weight_caps(n_total, n_core, n_sat, rb_growth)

    global_cap: float | None = None
    if max_single_security_weight_pct is not None and max_single_security_weight_pct > 0:
        global_cap = float(max_single_security_weight_pct)

    ptm = per_ticker_max_weight or {}
    bounds = []
    for t in tickers:
        block = ticker_to_block.get(t, "Growth")
        if block == "Growth":
            cap = max_core if t in growth_core_candidates else max_sat
        else:
            cap = 0.40
        if global_cap is not None:
            cap = min(cap, global_cap)
        if t in ptm:
            cap = min(cap, float(ptm[t]))
        bounds.append((min_weight, min(cap, 1.0)))
    return bounds


def _pc_from_w(w: np.ndarray, cov: np.ndarray) -> np.ndarray:
    """Percentage contributions to variance; sum = 1."""
    var_p = variance_p(w, cov)
    if var_p <= 1e-16:
        return np.full_like(w, 1.0 / len(w))
    m = cov @ w
    return (w * m) / var_p


def check_rb_achievement(
    blocks: dict[str, list[str]],
    rc_block_targets: dict[str, float],
    rc_asset_cap: float,
    growth_core_candidates: list[str],
    n_total: int,
    rb_growth: float,
    *,
    rc_cap_mode: str = RC_CAP_MODE_GLOBAL,
    rc_cap_rb_k_multiplier: float = DEFAULT_RC_CAP_RB_K_MULTIPLIER,
    rc_asset_cap_pct: float | None = None,
) -> tuple[bool, str]:
    """
    Delegate structural feasibility checks to policy_math.feasibility.check_feasible.

    Returns (ok, error_message). If not ok, error_message is a joined string of reasons.
    """
    equity_only = bool(rb_growth >= 0.90)
    ctx = FeasibilityContext(
        blocks=blocks,
        rc_block_targets=rc_block_targets,
        n_total=n_total,
        growth_core_candidates=growth_core_candidates,
        equity_only=equity_only,
        rc_asset_cap=rc_asset_cap,
        rc_cap_mode=rc_cap_mode,
        rc_cap_rb_k_multiplier=rc_cap_rb_k_multiplier,
        rc_asset_cap_pct=rc_asset_cap_pct,
    )
    ok, reasons = check_feasible(ctx)
    if ok:
        return True, ""
    msg = "; ".join(reasons.values()) if reasons else "Feasibility check failed."
    return False, msg


def _normalize_rb_target(target: dict[str, float]) -> dict[str, float]:
    """Normalize Growth/Duration/Inflation target to sum=1."""
    g = float(target.get("Growth", 0.0))
    d = float(target.get("Duration", 0.0))
    i = float(target.get("Inflation", 0.0))
    s = g + d + i
    if s <= 1e-12:
        return {"Growth": 1.0 / 3, "Duration": 1.0 / 3, "Inflation": 1.0 / 3}
    return {"Growth": g / s, "Duration": d / s, "Inflation": i / s}


def _expanded_rb_ranges(
    base_ranges: dict[str, dict[str, float]] | None,
    expansion_pp: float = RB_RANGE_EXPANSION_PP,
) -> dict[str, dict[str, float]] | None:
    """Expand per-block min/max by +/- expansion_pp and clip to [0,1]."""
    if not base_ranges:
        return None
    out: dict[str, dict[str, float]] = {}
    for b in RISK_BUDGET_BLOCKS:
        spec = base_ranges.get(b)
        if not isinstance(spec, dict):
            continue
        lo = max(0.0, float(spec.get("min", 0.0)) - expansion_pp)
        hi = min(1.0, float(spec.get("max", 1.0)) + expansion_pp)
        if hi < lo:
            lo, hi = hi, lo
        out[b] = {"min": lo, "max": hi}
    return out or None


def _build_rb_candidates_from_ranges(
    target_mid: dict[str, float],
    target_ranges: dict[str, dict[str, float]] | None,
    step_pp: float = RB_GRID_STEP_PP,
) -> list[dict[str, float]]:
    """
    Build candidate RB targets inside min/max ranges with G+D+I=1.
    Candidates are ordered by distance to midpoint target.
    """
    if not target_ranges:
        return []
    g_spec = target_ranges.get("Growth") or {}
    d_spec = target_ranges.get("Duration") or {}
    i_spec = target_ranges.get("Inflation") or {}
    g_min, g_max = float(g_spec.get("min", 0.0)), float(g_spec.get("max", 1.0))
    d_min, d_max = float(d_spec.get("min", 0.0)), float(d_spec.get("max", 1.0))
    i_min, i_max = float(i_spec.get("min", 0.0)), float(i_spec.get("max", 1.0))
    if g_max < g_min or d_max < d_min or i_max < i_min:
        return []

    vals_g = np.arange(g_min, g_max + step_pp / 2, step_pp)
    vals_d = np.arange(d_min, d_max + step_pp / 2, step_pp)
    out: list[dict[str, float]] = []
    seen: set[tuple[float, float, float]] = set()
    for g in vals_g:
        for d in vals_d:
            i = 1.0 - float(g) - float(d)
            if i < i_min - 1e-9 or i > i_max + 1e-9:
                continue
            cand = _normalize_rb_target({"Growth": float(g), "Duration": float(d), "Inflation": float(i)})
            key = (round(cand["Growth"], 6), round(cand["Duration"], 6), round(cand["Inflation"], 6))
            if key in seen:
                continue
            seen.add(key)
            out.append(cand)
    if not out:
        return []

    def _distance(c: dict[str, float]) -> float:
        return (
            abs(c["Growth"] - target_mid["Growth"])
            + abs(c["Duration"] - target_mid["Duration"])
            + abs(c["Inflation"] - target_mid["Inflation"])
        )

    out.sort(key=_distance)
    return out


def run_risk_budget_optimization(
    returns_df: pd.DataFrame,
    blocks: dict[str, list[str]],
    rc_block_targets: dict[str, float],
    growth_core_candidates: list[str],
    rc_asset_cap_pct: float | None = None,
    min_single_security_weight_pct: float | None = None,
    max_single_security_weight_pct: float | None = None,
    window_months: int = 60,
    duration_internal_weights: dict[str, float] | None = None,
    inflation_internal_weights: dict[str, float] | None = None,
    returns_window: pd.DataFrame | None = None,
    use_shrinkage: bool = False,
    rb_target_ranges: dict[str, dict[str, float]] | None = None,
    rb_search_enabled: bool = True,
    cov_precomputed: pd.DataFrame | None = None,
    mu_precomputed: pd.Series | None = None,
    per_ticker_max_weight: dict[str, float] | None = None,
    rc_cap_mode: str = RC_CAP_MODE_GLOBAL,
    rc_cap_rb_k_multiplier: float = DEFAULT_RC_CAP_RB_K_MULTIPLIER,
    rc_cap_penalty_lambda: float = RC_CAP_PENALTY_LAMBDA_DEFAULT,
    objective_mode: str = OBJECTIVE_MODE_MAX_RETURN,
    warm_start_weights: dict[str, float] | None = None,
    skeleton_tracking_lambda: float = 0.0,
    soft_target_vol_annual: float | None = None,
    soft_vol_penalty_lambda: float = 0.0,
    soft_target_return_annual: float | None = None,
    soft_return_penalty_lambda: float = 0.0,
    risk_skeleton_concentration_lambda: float = DEFAULT_RISK_SKELETON_CONCENTRATION_LAMBDA,
) -> tuple[dict[str, float], str]:
    """
    Find RiskPortfolio weights satisfying risk budget (RC block shares) and feasibility.
    Objective: maximize expected return (Growth spec) with RC-cap penalty term,
    risk_parity: minimize sum_i (RC_i - 1/n)^2 + RC penalty;
    risk_skeleton: RC penalty + lambda * sum_i RC_vol_i^2 (Herfindahl) to prefer least concentrated risk among feasible points.
    RC_vol cap control is penalty-first (soft objective), while structural constraints remain hard.
    Optional warm_start_weights + skeleton_tracking_lambda tie a max_return stage to a prior skeleton.
    Optional soft_* : when objective_mode=max_return and lambdas>0, add penalties
    (sigma_annual - target_vol)^2 and (12*mu_monthly - target_return)^2 vs IPS/profile decimals.
    Returns (weights_dict, status_message).
    If returns_window is provided, it is used as the primary window (already sliced); otherwise
    the window is taken from returns_df and window_months.
    If cov_precomputed and mu_precomputed are set, covariance and expected returns come from there
    (dual-matrix / young-ETF path); inner join on returns_window is skipped.
    """
    if rb_search_enabled:
        base_target = _normalize_rb_target(rc_block_targets or {})
        candidates: list[tuple[str, dict[str, float]]] = [("midpoint", base_target)]
        in_range = _build_rb_candidates_from_ranges(base_target, rb_target_ranges)
        candidates.extend([("range", c) for c in in_range if c != base_target])
        expanded_ranges = _expanded_rb_ranges(rb_target_ranges)
        expanded = _build_rb_candidates_from_ranges(base_target, expanded_ranges)
        existing = {(round(c["Growth"], 6), round(c["Duration"], 6), round(c["Inflation"], 6)) for _, c in candidates}
        for c in expanded:
            key = (round(c["Growth"], 6), round(c["Duration"], 6), round(c["Inflation"], 6))
            if key not in existing:
                candidates.append(("expanded", c))
                existing.add(key)

        best_weights: dict[str, float] = {}
        best_status = "FAIL_DATA: no candidate succeeded"
        for stage, candidate_target in candidates:
            w_try, st_try = run_risk_budget_optimization(
                returns_df,
                blocks,
                candidate_target,
                growth_core_candidates,
                rc_asset_cap_pct=rc_asset_cap_pct,
                min_single_security_weight_pct=min_single_security_weight_pct,
                max_single_security_weight_pct=max_single_security_weight_pct,
                window_months=window_months,
                duration_internal_weights=duration_internal_weights,
                inflation_internal_weights=inflation_internal_weights,
                returns_window=returns_window,
                use_shrinkage=use_shrinkage,
                rb_target_ranges=rb_target_ranges,
                rb_search_enabled=False,
                cov_precomputed=cov_precomputed,
                mu_precomputed=mu_precomputed,
                per_ticker_max_weight=per_ticker_max_weight,
                rc_cap_mode=rc_cap_mode,
                rc_cap_rb_k_multiplier=rc_cap_rb_k_multiplier,
                rc_cap_penalty_lambda=rc_cap_penalty_lambda,
                objective_mode=objective_mode,
                warm_start_weights=warm_start_weights,
                skeleton_tracking_lambda=skeleton_tracking_lambda,
                soft_target_vol_annual=soft_target_vol_annual,
                soft_vol_penalty_lambda=soft_vol_penalty_lambda,
                soft_target_return_annual=soft_target_return_annual,
                soft_return_penalty_lambda=soft_return_penalty_lambda,
                risk_skeleton_concentration_lambda=risk_skeleton_concentration_lambda,
            )
            if not w_try:
                if "FAIL_DATA" in st_try and not best_weights:
                    best_status = st_try
                continue
            if cov_precomputed is not None and mu_precomputed is not None and not cov_precomputed.empty:
                cols_eval = [
                    t for t in get_risk_portfolio_tickers(blocks)
                    if t in cov_precomputed.index and t in cov_precomputed.columns
                ]
                cov_eval = cov_precomputed.reindex(index=cols_eval, columns=cols_eval)
            elif returns_window is not None and not returns_window.empty:
                ret_eval = returns_window
                if ret_eval.empty:
                    return w_try, st_try + f" | RB_TARGET_SOURCE: {stage}"
                cov_eval = cov_matrix_monthly(ret_eval, ddof=1, use_shrinkage=use_shrinkage)
            else:
                cols_eval = [t for t in get_risk_portfolio_tickers(blocks) if t in returns_df.columns]
                ret_eval = returns_df[cols_eval].iloc[-window_months:].dropna(axis=1, how="all").dropna(how="any")
                if ret_eval.empty:
                    return w_try, st_try + f" | RB_TARGET_SOURCE: {stage}"
                cov_eval = cov_matrix_monthly(ret_eval, ddof=1, use_shrinkage=use_shrinkage)
            actual = rc_by_block_from_weights(w_try, cov_eval, blocks)
            rb_ok, _ = check_rb_corridor(actual, candidate_target, corridor_pp=RB_CORRIDOR_PP)
            st_final = (
                st_try
                + f" | RB_TARGET_SOURCE: {stage}"
                + f" | RB_TARGET_USED: {candidate_target['Growth']:.3f}/{candidate_target['Duration']:.3f}/{candidate_target['Inflation']:.3f}"
            )
            if rb_ok:
                return w_try, st_final
            if not best_weights:
                best_weights, best_status = w_try, st_final
        return best_weights, best_status

    risk_tickers = get_risk_portfolio_tickers(blocks)
    if not risk_tickers:
        return {}, "FAIL: no RiskPortfolio tickers (Growth+Duration+Inflation+Growth_HY+Growth_EM_debt)"

    ticker_to_block = ticker_to_block_map(blocks)
    MIN_FULL_JOIN_MONTHS = 11  # minimum months where all risk tickers have data (Full NaN-safe; young tickers)

    use_precomputed_cov = (
        cov_precomputed is not None
        and mu_precomputed is not None
        and not cov_precomputed.empty
    )

    if use_precomputed_cov:
        cols = [
            t for t in risk_tickers
            if t in cov_precomputed.index and t in cov_precomputed.columns
        ]
        if not cols:
            return {}, "FAIL_DATA: cov_precomputed missing overlap with RiskPortfolio tickers"
        cols = [t for t in risk_tickers if t in cols]
        n = len(cols)
        cov = cov_precomputed.reindex(index=cols, columns=cols).fillna(0.0).values
        mu = mu_precomputed.reindex(cols).fillna(0.0).values
    elif returns_window is not None and not returns_window.empty:
        ret = returns_window
        cols = list(ret.columns)
        if len(ret) < MIN_FULL_JOIN_MONTHS:
            return {}, (
                f"FAIL_DATA: returns_window has only {len(ret)} months. "
                f"Need at least {MIN_FULL_JOIN_MONTHS} months."
            )
    else:
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

        # Full mode: inner join — only months where all (available) risk tickers have data; drop columns with no data
        ret = returns_df[cols].iloc[-window_months:]
        ret = ret.dropna(axis=1, how="all")
        ret = ret.dropna(how="any")
        if len(ret) < MIN_FULL_JOIN_MONTHS:
            # Try longer lookback (young ticker may have shorter history)
            lookback = min(returns_df.shape[0], max(window_months * 2, 120))
            ret = returns_df[cols].iloc[-lookback:]
            ret = ret.dropna(axis=1, how="all")
            ret = ret.dropna(how="any")
            if len(ret) >= MIN_FULL_JOIN_MONTHS:
                ret = ret.iloc[-min(window_months, len(ret)):]
            else:
                return {}, (
                    f"FAIL_DATA: insufficient history after inner join ({len(ret)} months). "
                    f"Need at least {MIN_FULL_JOIN_MONTHS} months where every risk ticker has data."
                )
        else:
            ret = ret.iloc[-min(window_months, len(ret)):]  # use up to window_months of full overlap
        cols = list(ret.columns)
    if not cols:
        return {}, "FAIL_DATA: no assets with returns in window"

    if not use_precomputed_cov:
        n = len(cols)
        mu = ret.mean().values
        cov = cov_matrix_monthly(ret, ddof=1, use_shrinkage=use_shrinkage).values
    # else: n, mu, cov already set from cov_precomputed / mu_precomputed

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

    equity_only_rb = rb_growth >= 0.90
    if rc_asset_cap_pct is not None and rc_asset_cap_pct > 0:
        rc_scalar = float(rc_asset_cap_pct)
        rc_caps_by_block = {"Growth": rc_scalar, "Duration": rc_scalar, "Inflation": rc_scalar}
    elif rc_cap_mode == RC_CAP_MODE_PER_BLOCK_RB_K:
        rc_caps_by_block = compute_rc_caps_by_block_from_targets(
            blocks,
            rb_growth,
            rb_duration,
            rb_inflation,
            rc_cap_rb_k_multiplier,
            equity_only_rb,
        )
    else:
        rc_scalar = resolve_rc_asset_cap(rc_asset_cap_pct, n, rb_growth)
        rc_caps_by_block = {"Growth": rc_scalar, "Duration": rc_scalar, "Inflation": rc_scalar}

    rc_cap_map = build_rc_cap_per_ticker(
        blocks,
        {"Growth": rb_growth, "Duration": rb_duration, "Inflation": rb_inflation},
        rc_asset_cap_pct,
        rc_cap_mode,
        rc_cap_rb_k_multiplier,
        n,
    )
    rc_cap_per_asset = [float(rc_cap_map.get(t, rc_caps_by_block[ticker_to_block.get(t, "Growth")])) for t in cols]

    min_weight = float(min_single_security_weight_pct) if min_single_security_weight_pct is not None and min_single_security_weight_pct > 0 else MIN_WEIGHT_DEFAULT

    # Count assets per block in cols (feasibility: per-asset RC cap applies to every asset; single-asset block cannot exceed cap).
    duration_in_cols = [i for i, t in enumerate(cols) if ticker_to_block.get(t) == "Duration"]
    inflation_in_cols = [i for i, t in enumerate(cols) if ticker_to_block.get(t) == "Inflation"]
    growth_in_cols = [i for i, t in enumerate(cols) if ticker_to_block.get(t) == "Growth"]
    n_dur, n_infl, n_growth = len(duration_in_cols), len(inflation_in_cols), len(growth_in_cols)

    cap_d_block, cap_i_block, cap_g_block = (
        rc_caps_by_block["Duration"],
        rc_caps_by_block["Inflation"],
        rc_caps_by_block["Growth"],
    )
    # Effective RB: if a block has one asset, its max RC = that block's per-asset cap; redistribute shortfall to other blocks.
    achievable_d = min(rb_duration, cap_d_block) if n_dur == 1 else rb_duration
    achievable_i = min(rb_inflation, cap_i_block) if n_infl == 1 else rb_inflation
    achievable_g = min(rb_growth, cap_g_block) if n_growth == 1 else rb_growth
    shortfall_d = rb_duration - achievable_d
    shortfall_i = rb_inflation - achievable_i
    shortfall_g = rb_growth - achievable_g

    rb_growth_eff = achievable_g
    rb_duration_eff = achievable_d
    rb_inflation_eff = achievable_i
    if shortfall_d > 1e-12 and (rb_growth + rb_inflation) > 1e-12:
        rb_growth_eff += shortfall_d * rb_growth / (rb_growth + rb_inflation)
        rb_inflation_eff += shortfall_d * rb_inflation / (rb_growth + rb_inflation)
    if shortfall_i > 1e-12 and (rb_growth + rb_duration) > 1e-12:
        rb_growth_eff += shortfall_i * rb_growth / (rb_growth + rb_duration)
        rb_duration_eff += shortfall_i * rb_duration / (rb_growth + rb_duration)
    if shortfall_g > 1e-12 and (rb_duration + rb_inflation) > 1e-12:
        rb_duration_eff += shortfall_g * rb_duration / (rb_duration + rb_inflation)
        rb_inflation_eff += shortfall_g * rb_inflation / (rb_duration + rb_inflation)
    total_eff = rb_growth_eff + rb_duration_eff + rb_inflation_eff
    if total_eff > 1e-12:
        rb_growth_eff /= total_eff
        rb_duration_eff /= total_eff
        rb_inflation_eff /= total_eff
    rb_growth, rb_duration, rb_inflation = rb_growth_eff, rb_duration_eff, rb_inflation_eff

    growth_tickers = [t for t in cols if ticker_to_block.get(t) == "Growth"]
    n_core = sum(1 for t in growth_tickers if t in growth_core_candidates)
    n_sat = len(growth_tickers) - n_core
    max_core, max_sat = growth_weight_caps(n, n_core, n_sat, rb_growth)
    bounds = build_bounds(
        cols, ticker_to_block, growth_core_candidates, n, min_weight,
        max_single_security_weight_pct=max_single_security_weight_pct,
        rb_growth=rb_growth,
        per_ticker_max_weight=per_ticker_max_weight,
    )

    effective_rb = {"Growth": rb_growth, "Duration": rb_duration, "Inflation": rb_inflation}
    rc_ctx_scalar = resolve_rc_asset_cap(rc_asset_cap_pct, n, rb_growth)
    ok, err = check_rb_achievement(
        blocks,
        effective_rb,
        rc_ctx_scalar,
        growth_core_candidates,
        n,
        rb_growth,
        rc_cap_mode=rc_cap_mode,
        rc_cap_rb_k_multiplier=rc_cap_rb_k_multiplier,
        rc_asset_cap_pct=rc_asset_cap_pct,
    )
    if not ok:
        feasibility_warning = f"FAIL_FEASIBILITY: {err}"
    else:
        feasibility_warning = ""

    growth_hy_set = set(blocks.get(GROWTH_HY_KEY, []))
    growth_em_debt_set = set(blocks.get(GROWTH_EM_DEBT_KEY, []))
    hy_indices = [i for i, t in enumerate(cols) if t in growth_hy_set]
    em_debt_indices = [i for i, t in enumerate(cols) if t in growth_em_debt_set]

    penalty_lambda = float(rc_cap_penalty_lambda) if rc_cap_penalty_lambda > 0 else RC_CAP_PENALTY_LAMBDA_DEFAULT
    obj_mode = objective_mode if objective_mode in OBJECTIVE_MODES else OBJECTIVE_MODE_MAX_RETURN
    obj_mode_invalid = objective_mode not in OBJECTIVE_MODES
    track_lam = float(skeleton_tracking_lambda) if skeleton_tracking_lambda > 0 else 0.0
    w_ref_vec: np.ndarray | None = None
    if track_lam > 0 and obj_mode == OBJECTIVE_MODE_MAX_RETURN and warm_start_weights:
        w_ref_vec = np.array([float(warm_start_weights.get(t, 0.0)) for t in cols], dtype=float)
        sr = float(w_ref_vec.sum())
        if sr > 1e-12:
            w_ref_vec = w_ref_vec / sr
        else:
            w_ref_vec = None

    rc_cap_arr = np.array(rc_cap_per_asset, dtype=float)

    stv = float(soft_target_vol_annual) if soft_target_vol_annual is not None else None
    lam_sv = float(soft_vol_penalty_lambda) if soft_vol_penalty_lambda and soft_vol_penalty_lambda > 0 else 0.0
    st_ret = float(soft_target_return_annual) if soft_target_return_annual is not None else None
    lam_sr = float(soft_return_penalty_lambda) if soft_return_penalty_lambda and soft_return_penalty_lambda > 0 else 0.0
    skel_conc_lam = (
        float(risk_skeleton_concentration_lambda)
        if risk_skeleton_concentration_lambda and risk_skeleton_concentration_lambda > 0
        else 0.0
    )

    def objective(w: np.ndarray) -> float:
        # RC cap as soft penalty (not hard inequality): encourages concentration control while preserving feasibility.
        pc = _pc_from_w(w, cov)
        rc_viol = np.maximum(0.0, pc - rc_cap_arr)
        rc_pen = float(np.sum(rc_viol * rc_viol))
        base = penalty_lambda * rc_pen
        if obj_mode == OBJECTIVE_MODE_RISK_PARITY:
            target = 1.0 / float(n)
            rp_dev = float(np.sum((pc - target) ** 2))
            return rp_dev + base
        if obj_mode == OBJECTIVE_MODE_RISK_SKELETON:
            # Herfindahl on RC_vol: lower => less concentrated risk; min 1/n when equal RC
            hhi_rc = float(np.sum(pc * pc))
            return base + skel_conc_lam * hhi_rc
        track = 0.0
        if w_ref_vec is not None:
            d = w - w_ref_vec
            track = track_lam * float(np.dot(d, d))
        soft_ips = 0.0
        if lam_sv > 0 and stv is not None:
            var_p = float(w @ cov @ w)
            sigma_m = math.sqrt(max(var_p, 0.0))
            sigma_ann = sigma_m * math.sqrt(12.0)
            dv = sigma_ann - stv
            soft_ips += lam_sv * (dv * dv)
        if lam_sr > 0 and st_ret is not None:
            mu_m = float(np.dot(mu, w))
            ret_ann_lin = 12.0 * mu_m
            dr = ret_ann_lin - st_ret
            soft_ips += lam_sr * (dr * dr)
        return -float(np.dot(mu, w)) + base + track + soft_ips

    def constraint_sum(w: np.ndarray) -> float:
        return float(np.sum(w) - 1.0)

    # RB corridor constraints (inequalities) instead of strict equalities:
    #   rb_block - RB_CORRIDOR_PP <= RC_block <= rb_block + RB_CORRIDOR_PP

    def constraint_rb_growth_lower(w: np.ndarray) -> float:
        pc = _pc_from_w(w, cov)
        rc_g = sum(pc[i] for i, t in enumerate(cols) if ticker_to_block.get(t) == "Growth")
        return float(rc_g - (rb_growth - RB_CORRIDOR_PP))

    def constraint_rb_growth_upper(w: np.ndarray) -> float:
        pc = _pc_from_w(w, cov)
        rc_g = sum(pc[i] for i, t in enumerate(cols) if ticker_to_block.get(t) == "Growth")
        return float((rb_growth + RB_CORRIDOR_PP) - rc_g)

    def constraint_rb_duration_lower(w: np.ndarray) -> float:
        pc = _pc_from_w(w, cov)
        rc_d = sum(pc[i] for i, t in enumerate(cols) if ticker_to_block.get(t) == "Duration")
        return float(rc_d - (rb_duration - RB_CORRIDOR_PP))

    def constraint_rb_duration_upper(w: np.ndarray) -> float:
        pc = _pc_from_w(w, cov)
        rc_d = sum(pc[i] for i, t in enumerate(cols) if ticker_to_block.get(t) == "Duration")
        return float((rb_duration + RB_CORRIDOR_PP) - rc_d)

    def constraint_rb_inflation_lower(w: np.ndarray) -> float:
        pc = _pc_from_w(w, cov)
        rc_i = sum(pc[i] for i, t in enumerate(cols) if ticker_to_block.get(t) == "Inflation")
        return float(rc_i - (rb_inflation - RB_CORRIDOR_PP))

    def constraint_rb_inflation_upper(w: np.ndarray) -> float:
        pc = _pc_from_w(w, cov)
        rc_i = sum(pc[i] for i, t in enumerate(cols) if ticker_to_block.get(t) == "Inflation")
        return float((rb_inflation + RB_CORRIDOR_PP) - rc_i)

    # Growth HY sub-limit: RC_vol(HY) <= 10% × RC_vol(Growth) — feasibility_constraints_spec §2b
    def constraint_hy_sub(w: np.ndarray) -> float:
        pc = _pc_from_w(w, cov)
        rc_g = sum(pc[i] for i, t in enumerate(cols) if ticker_to_block.get(t) == "Growth")
        rc_hy = sum(pc[i] for i in hy_indices) if hy_indices else 0.0
        return float(0.10 * rc_g - rc_hy)

    # Growth EM Debt sub-limit: RC_vol(EM Debt) <= 10% × RC_vol(Growth) — feasibility_constraints_spec §2c
    def constraint_em_debt_sub(w: np.ndarray) -> float:
        pc = _pc_from_w(w, cov)
        rc_g = sum(pc[i] for i, t in enumerate(cols) if ticker_to_block.get(t) == "Growth")
        rc_em = sum(pc[i] for i in em_debt_indices) if em_debt_indices else 0.0
        return float(0.10 * rc_g - rc_em)

    # Block-internal mix constraints (Duration/Inflation selection): w_t = internal[t] * W_block
    def make_duration_internal_constraint(idx_t: int, internal_t: float, duration_indices: list[int]):
        def fn(w: np.ndarray) -> float:
            w_d = sum(w[i] for i in duration_indices)
            return float(w[idx_t] - internal_t * w_d)
        return fn

    def make_inflation_internal_constraint(idx_t: int, internal_t: float, inflation_indices: list[int]):
        def fn(w: np.ndarray) -> float:
            w_i = sum(w[i] for i in inflation_indices)
            return float(w[idx_t] - internal_t * w_i)
        return fn

    constraints_core = [
        {"type": "eq", "fun": constraint_sum},
        {"type": "ineq", "fun": constraint_rb_growth_lower},
        {"type": "ineq", "fun": constraint_rb_growth_upper},
        {"type": "ineq", "fun": constraint_rb_duration_lower},
        {"type": "ineq", "fun": constraint_rb_duration_upper},
        {"type": "ineq", "fun": constraint_rb_inflation_lower},
        {"type": "ineq", "fun": constraint_rb_inflation_upper},
    ]
    if hy_indices:
        constraints_core.append({"type": "ineq", "fun": constraint_hy_sub})
    if em_debt_indices:
        constraints_core.append({"type": "ineq", "fun": constraint_em_debt_sub})

    if duration_internal_weights and duration_in_cols:
        # One equality per Duration ticker except last: w_t = internal[t] * W_d
        dur_tickers = [cols[i] for i in duration_in_cols]
        for k, idx in enumerate(duration_in_cols[:-1]):
            t = cols[idx]
            internal_t = duration_internal_weights.get(t)
            if internal_t is not None:
                constraints_core.append({
                    "type": "eq",
                    "fun": make_duration_internal_constraint(idx, internal_t, duration_in_cols),
                })
    if inflation_internal_weights and inflation_in_cols:
        inf_tickers = [cols[i] for i in inflation_in_cols]
        for k, idx in enumerate(inflation_in_cols[:-1]):
            t = cols[idx]
            internal_t = inflation_internal_weights.get(t)
            if internal_t is not None:
                constraints_core.append({
                    "type": "eq",
                    "fun": make_inflation_internal_constraint(idx, internal_t, inflation_in_cols),
                })

    # RC cap is handled via objective penalty (soft); keep structural constraints hard.
    constraints_full = constraints_core

    def penalty_rc(w: np.ndarray) -> float:
        s = float(np.sum(w) - 1.0)
        pc = _pc_from_w(w, cov)
        rg = sum(pc[i] for i, t in enumerate(cols) if ticker_to_block.get(t) == "Growth") - rb_growth
        rd = sum(pc[i] for i, t in enumerate(cols) if ticker_to_block.get(t) == "Duration") - rb_duration
        ri = sum(pc[i] for i, t in enumerate(cols) if ticker_to_block.get(t) == "Inflation") - rb_inflation
        return s * s + rg * rg + rd * rd + ri * ri

    bounds_hi = np.array([b[1] for b in bounds])
    x0_from_warm: np.ndarray | None = None
    if warm_start_weights:
        xw = np.array([float(warm_start_weights.get(t, 0.0)) for t in cols], dtype=float)
        xw = np.clip(xw, min_weight, bounds_hi - 1e-6)
        sw = float(xw.sum())
        if sw > 1e-12:
            x0_from_warm = xw / sw

    x0 = np.zeros(n)
    for b, target in (("Growth", rb_growth), ("Duration", rb_duration), ("Inflation", rb_inflation)):
        idx = [i for i, t in enumerate(cols) if ticker_to_block.get(t) == b]
        if idx:
            if b == "Duration" and duration_internal_weights:
                for i in idx:
                    x0[i] = target * duration_internal_weights.get(cols[i], 1.0 / len(idx))
            elif b == "Inflation" and inflation_internal_weights:
                for i in idx:
                    x0[i] = target * inflation_internal_weights.get(cols[i], 1.0 / len(idx))
            else:
                x0[idx] = target / len(idx)
    if np.abs(x0.sum() - 1.0) > 1e-6:
        x0 = np.ones(n) / n
    x0 = np.clip(x0, min_weight, bounds_hi - 1e-6)
    x0 = x0 / x0.sum()

    feas = minimize(penalty_rc, x0, method="L-BFGS-B", bounds=bounds, options={"maxiter": 300})
    if x0_from_warm is not None:
        x0_slsqp = x0_from_warm.copy()
    elif feas.fun < 1e-6:
        x0_slsqp = feas.x
    else:
        x0_slsqp = feas.x / feas.x.sum()

    res = minimize(
        objective,
        x0_slsqp.copy(),
        method="SLSQP",
        bounds=bounds,
        constraints=constraints_full,
        options={"maxiter": 1000, "ftol": 1e-9},
    )
    used_fallback = False
    if not res.success:
        res = minimize(
            objective,
            x0_slsqp.copy(),
            method="SLSQP",
            bounds=bounds,
            constraints=constraints_core,
            options={"maxiter": 1000, "ftol": 1e-9},
        )
        if not res.success:
            # Deterministic fallback: use feasibility solution (penalty_rc) and normalize
            w_fallback = np.clip(feas.x, min_weight, np.array([b[1] for b in bounds]) - 1e-8)
            w_fallback = w_fallback / w_fallback.sum()
            res = type("Res", (), {"success": True, "x": w_fallback})()
        used_fallback = True

    w = res.x
    pc = _pc_from_w(w, cov)

    # Post-solution RC diagnostics: RC_vol cap has priority in policy,
    # but in this refactored version violations are reported via status string
    # instead of causing a hard FAIL (fallback mode).
    viol_idx = [i for i in range(n) if pc[i] > rc_cap_per_asset[i]]
    rc_cap_viol_tickers = [cols[i] for i in viol_idx] if viol_idx else []

    rc_g = sum(pc[i] for i, t in enumerate(cols) if ticker_to_block.get(t) == "Growth")
    rc_d = sum(pc[i] for i, t in enumerate(cols) if ticker_to_block.get(t) == "Duration")
    rc_i = sum(pc[i] for i, t in enumerate(cols) if ticker_to_block.get(t) == "Inflation")

    w_dict = {t: float(w[i]) for i, t in enumerate(cols)}
    for t in risk_tickers:
        if t not in w_dict:
            w_dict[t] = 0.0

    status_parts = []
    status_parts.append("OK_FALLBACK" if used_fallback else "OK")
    if feasibility_warning:
        status_parts.append(feasibility_warning)
    if rc_cap_viol_tickers:
        status_parts.append(f"VIOL_RC_ASSET_CAP: {rc_cap_viol_tickers}")
    status_parts.append(f"RC_CAP_PENALTY_LAMBDA={penalty_lambda:.2f}")
    status_parts.append(f"OBJECTIVE_MODE={obj_mode}")
    if obj_mode_invalid:
        status_parts.append(f"OBJECTIVE_MODE_INVALID: {objective_mode!r} -> max_return")
    if warm_start_weights:
        status_parts.append("WARM_START=on")
    if track_lam > 0 and w_ref_vec is not None:
        status_parts.append(f"SKEL_TRACK_LAMBDA={track_lam:.4g}")
    if lam_sv > 0 and stv is not None:
        status_parts.append(f"SOFT_VOL_TARGET={stv:.4f} LAMBDA={lam_sv:.4g}")
    if lam_sr > 0 and st_ret is not None:
        status_parts.append(f"SOFT_RET_TARGET={st_ret:.4f} LAMBDA={lam_sr:.4g}")
    if obj_mode == OBJECTIVE_MODE_RISK_SKELETON:
        status_parts.append(f"SKEL_HHI_LAMBDA={skel_conc_lam:.4g}")
    status_parts.append(f"RC G/D/I: {rc_g:.3f}/{rc_d:.3f}/{rc_i:.3f}")
    status_msg = " | ".join(status_parts)
    return w_dict, status_msg


RC_POSTPROCESS_MAX_ITER = 200
RC_POSTPROCESS_STEP_PCT = 0.005


def enforce_rc_caps_postprocess(
    weights_risk: dict[str, float],
    cov_df: pd.DataFrame,
    blocks: dict[str, list[str]],
    growth_core_candidates: list[str],
    rc_asset_cap: float | list[float],
    min_weight: float,
    max_single_security_weight_pct: float | None,
    rb_growth: float,
    risk_tickers: list[str],
    max_iterations: int = RC_POSTPROCESS_MAX_ITER,
    step_pct: float = RC_POSTPROCESS_STEP_PCT,
    per_ticker_max_weight: dict[str, float] | None = None,
    rc_cap_by_ticker: dict[str, float] | None = None,
) -> tuple[dict[str, float], bool, dict]:
    """
    RC post-processing fallback: iteratively reduce weight from assets above RC cap
    and reallocate to recipient bucket (core equity then lowest-vol Duration/Inflation).
    Respects min_weight, weight caps, no leverage/short.
    rc_asset_cap: scalar (same cap for all) or list aligned with internal cols order.
    If rc_cap_by_ticker is set, per-ticker caps override (lookup by cols[i]).
    Returns (adjusted_weights, success, diagnostics).
    """
    cols = [
        t for t in risk_tickers
        if t in weights_risk and t in cov_df.columns and t in cov_df.index and weights_risk.get(t, 0) > 0
    ]
    if not cols:
        return dict(weights_risk), True, {}
    n = len(cols)
    ticker_to_block = ticker_to_block_map(blocks)
    bounds = build_bounds(
        cols, ticker_to_block, growth_core_candidates, n, min_weight,
        max_single_security_weight_pct=max_single_security_weight_pct,
        rb_growth=rb_growth,
        per_ticker_max_weight=per_ticker_max_weight,
    )
    cov = cov_df.reindex(index=cols, columns=cols).fillna(0).values
    w = np.array([weights_risk[t] for t in cols], dtype=float)

    if rc_cap_by_ticker is not None:
        cap_row = [float(rc_cap_by_ticker.get(t, 1.0)) for t in cols]
    elif isinstance(rc_asset_cap, (int, float)):
        cap_row = [float(rc_asset_cap)] * n
    else:
        cap_row = [float(x) for x in rc_asset_cap]
        if len(cap_row) != n:
            return dict(weights_risk), False, {"reason": "rc_cap_len_mismatch", "n": n, "caps": len(cap_row)}

    vol_per = np.sqrt(np.maximum(np.diag(cov), 1e-20))
    hedge = [t for t in cols if ticker_to_block.get(t) in ("Duration", "Inflation")]
    hedge_vol = [(t, vol_per[cols.index(t)]) for t in hedge]
    hedge_vol.sort(key=lambda x: (x[1], x[0]))
    recipient_order = [t for t in ("VOO", "VT", "VTI") if t in cols]
    recipient_order += [t for t, _ in hedge_vol]
    if not recipient_order:
        return dict(weights_risk), False, {"reason": "no_recipient"}

    for it in range(max_iterations):
        var_p = variance_p(w, cov)
        if var_p <= 1e-16:
            break
        pc = (w * (cov @ w)) / var_p
        violators = [i for i in range(n) if pc[i] > cap_row[i] + 1e-9]
        if not violators:
            s = float(w.sum())
            if s > 1e-12:
                w = w / s
            out = {t: float(w[j]) for j, t in enumerate(cols)}
            for t in risk_tickers:
                if t not in out:
                    out[t] = 0.0
            return out, True, {"iterations": it, "rc_cap": cap_row}

        violators.sort(key=lambda i: (-pc[i], cols[i]))
        donor_idx = violators[0]
        lo, hi = bounds[donor_idx]
        delta_max = float(w[donor_idx] - lo)
        if delta_max <= 1e-9:
            out = {t: float(w[j]) for j, t in enumerate(cols)}
            for t in risk_tickers:
                if t not in out:
                    out[t] = 0.0
            return out, False, {
                "iterations": it,
                "remaining_violators": [cols[i] for i in violators],
                "reason": "donor_at_min",
            }
        delta = min(step_pct, delta_max)

        total_recipient_space = 0.0
        for rec_ticker in recipient_order:
            j = cols.index(rec_ticker)
            rec_hi = bounds[j][1]
            total_recipient_space += max(0.0, rec_hi - w[j])
        transfer = min(delta, total_recipient_space)
        if transfer <= 1e-12:
            out = {t: float(w[j]) for j, t in enumerate(cols)}
            for t in risk_tickers:
                if t not in out:
                    out[t] = 0.0
            return out, False, {"iterations": it, "reason": "recipient_caps_full"}

        w[donor_idx] -= transfer
        remaining = transfer
        for rec_ticker in recipient_order:
            if remaining <= 1e-12:
                break
            j = cols.index(rec_ticker)
            rec_hi = bounds[j][1]
            space = max(0.0, rec_hi - w[j])
            if space <= 1e-12:
                continue
            add = min(remaining, space)
            w[j] += add
            remaining -= add
        w = np.clip(w, [b[0] for b in bounds], [b[1] for b in bounds])
        # Keep sum=1 (no renormalize so we do not push weights over caps)

    var_p = variance_p(w, cov)
    pc = (w * (cov @ w)) / var_p if var_p > 1e-16 else np.ones(n) / n
    violators = [i for i in range(n) if pc[i] > cap_row[i] + 1e-9]
    out = {t: float(w[j]) for j, t in enumerate(cols)}
    for t in risk_tickers:
        if t not in out:
            out[t] = 0.0
    return out, False, {
        "iterations": max_iterations,
        "remaining_violators": [cols[i] for i in violators],
        "reason": "max_iterations",
    }


def _alpha_shift_to_target_vol(
    weights_risk: dict[str, float],
    cov_df: pd.DataFrame,
    target_vol_annual: float,
    n_rc: int,
    donor_shift_mode: str,
    blocks: dict[str, list[str]],
    growth_core_candidates: list[str],
) -> tuple[dict[str, float], str | None]:
    """
    ProLiquidity §1.7: When cash prohibited and vol > target, shift weight from top-N_rc donors to recipient
    until vol <= target_vol_annual. Returns (adjusted_weights_risk, error_message). error_message non-None on failure.
    """
    tickers = [t for t in weights_risk if t in cov_df.columns and t in cov_df.index]
    if not tickers:
        return dict(weights_risk), "No risk assets in covariance for alpha shift."
    cov = cov_df.reindex(index=tickers, columns=tickers).fillna(0).values
    w = np.array([weights_risk[t] for t in tickers])
    current_vol = float(np.sqrt(variance_p(w, cov) * 12)) if variance_p(w, cov) > 0 else 0.0
    if current_vol <= target_vol_annual:
        return dict(weights_risk), None

    pc = percentage_contributions_variance(w, cov)
    rc_by_ticker = [(tickers[i], float(pc[i])) for i in range(len(tickers)) if w[i] > 0]
    rc_by_ticker.sort(key=lambda x: (-x[1], x[0]))
    donors = [x[0] for x in rc_by_ticker[: min(n_rc, len(rc_by_ticker))]]
    donors = [t for t in donors if weights_risk.get(t, 0) > 0]
    if not donors:
        return dict(weights_risk), "Donor set empty for alpha shift."

    # Recipient: VOO > VT > VTI > lowest-vol in Duration/Inflation
    ticker_to_block = ticker_to_block_map(blocks)
    for candidate in ("VOO", "VT", "VTI"):
        if candidate in weights_risk and weights_risk.get(candidate, 0) >= 0 and candidate in tickers:
            recipient = candidate
            break
    else:
        hedge = [t for t in tickers if ticker_to_block.get(t) in ("Duration", "Inflation")]
        if not hedge:
            return dict(weights_risk), "No recipient (VOO/VT/VTI or Duration/Inflation) in portfolio for alpha shift."
        vol_by_ticker = []
        for t in hedge:
            idx = tickers.index(t)
            vol_t = float(np.sqrt(cov[idx, idx] * 12)) if cov[idx, idx] > 0 else 0.0
            vol_by_ticker.append((t, vol_t))
        vol_by_ticker.sort(key=lambda x: (x[1], x[0]))
        recipient = vol_by_ticker[0][0]

    donor_weights = np.array([weights_risk[t] for t in donors])
    alpha_max = float(donor_weights.sum())
    if alpha_max <= 0:
        return dict(weights_risk), "Total donor weight is zero."

    tol_vol = 1e-6
    alpha_lo, alpha_hi = 0.0, alpha_max
    for _ in range(80):
        alpha = (alpha_lo + alpha_hi) / 2.0
        if donor_shift_mode == "equal":
            take_per_donor = alpha / len(donors) if donors else 0.0
            new_weights = dict(weights_risk)
            for t in donors:
                new_weights[t] = max(0.0, weights_risk[t] - take_per_donor)
            add_to_recipient = min(alpha, sum(weights_risk[t] for t in donors) - sum(new_weights[t] for t in donors))
        else:
            # proportional: reduce each donor by (alpha / alpha_max) * donor_weight
            new_weights = dict(weights_risk)
            for t in donors:
                frac = weights_risk[t] / alpha_max if alpha_max > 0 else 0.0
                new_weights[t] = max(0.0, weights_risk[t] - alpha * frac)
            add_to_recipient = sum(weights_risk[t] for t in donors) - sum(new_weights[t] for t in donors)
        new_weights[recipient] = weights_risk.get(recipient, 0.0) + add_to_recipient
        w_new = np.array([new_weights.get(t, 0.0) for t in tickers])
        var_p = variance_p(w_new, cov)
        vol_new = float(np.sqrt(var_p * 12)) if var_p > 0 else 0.0
        if vol_new <= target_vol_annual + tol_vol:
            alpha_hi = alpha
        else:
            alpha_lo = alpha
        if alpha_hi - alpha_lo < 1e-8:
            break

    alpha_final = alpha_hi
    if donor_shift_mode == "equal":
        take_per_donor = alpha_final / len(donors) if donors else 0.0
        out = dict(weights_risk)
        for t in donors:
            out[t] = max(0.0, weights_risk[t] - take_per_donor)
        add_to_recipient = sum(weights_risk[t] for t in donors) - sum(out[t] for t in donors)
    else:
        out = dict(weights_risk)
        for t in donors:
            frac = weights_risk[t] / alpha_max if alpha_max > 0 else 0.0
            out[t] = max(0.0, weights_risk[t] - alpha_final * frac)
        add_to_recipient = sum(weights_risk[t] for t in donors) - sum(out[t] for t in donors)
    out[recipient] = out.get(recipient, 0.0) + add_to_recipient
    w_final = np.array([out.get(t, 0.0) for t in tickers])
    vol_final = float(np.sqrt(variance_p(w_final, cov) * 12)) if variance_p(w_final, cov) > 0 else 0.0
    if vol_final > target_vol_annual + 1e-4:
        return dict(weights_risk), (
            "TargetVol cannot be achieved with cash_policy='prohibited' "
            "given the current universe and constraints."
        )
    return out, None


def proliquidity(
    weights_risk: dict[str, float],
    cash_proxy_ticker: str,
    current_vol_annual: float,
    target_vol_annual: float,
    liquidity_floor_pct: float,
    cash_policy: str,
    cov_df: pd.DataFrame | None = None,
    n_rc: int = 3,
    donor_shift_mode: str = "proportional",
    blocks: dict[str, list[str]] | None = None,
    growth_core_candidates: list[str] | None = None,
) -> tuple[dict[str, float], str | None]:
    """
    Apply ProLiquidity: cash_weight = max(liquidity_floor, vol_scaling); scale RiskPortfolio by (1 - cash_weight), add cash.
    When cash_policy == "prohibited" and current_vol > target_vol, applies Deterministic Alpha Shift (§1.7).
    Returns (final_weights_dict, error_message). error_message is non-None on failure (e.g. FAIL_CONSTRAINT).
    """
    if cash_policy == "prohibited":
        if current_vol_annual > target_vol_annual and cov_df is not None and blocks is not None and growth_core_candidates is not None:
            shifted, err = _alpha_shift_to_target_vol(
                weights_risk, cov_df, target_vol_annual, n_rc, donor_shift_mode, blocks, growth_core_candidates
            )
            if err:
                return shifted, err
            return shifted, None
        return dict(weights_risk), None

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
    return out, None


def portfolio_vol_annual(weights: dict[str, float], cov_df: pd.DataFrame) -> float:
    """Annualized vol from monthly covariance; weights and cov must share same tickers."""
    tickers = [t for t in weights if t in cov_df.columns and t in cov_df.index]
    if not tickers:
        return 0.0
    w = np.array([weights[t] for t in tickers])
    cov = cov_df.reindex(index=tickers, columns=tickers).fillna(0).values
    var = variance_p(w, cov)
    return float(np.sqrt(var * 12)) if var > 0 else 0.0


def rc_by_block_from_weights(
    weights_risk: dict[str, float],
    cov_df: pd.DataFrame,
    blocks: dict[str, list[str]],
) -> dict[str, float]:
    """
    Compute actual RC share by block (Growth, Duration, Inflation) from RiskPortfolio weights.
    Returns dict with keys Growth, Duration, Inflation; values sum to 1.
    """
    ticker_to_block = ticker_to_block_map(blocks)
    cols = [t for t in weights_risk if t in cov_df.columns and t in cov_df.index and weights_risk.get(t, 0) > 0]
    if not cols:
        return {}
    w = np.array([weights_risk[t] for t in cols])
    cov = cov_df.reindex(index=cols, columns=cols).fillna(0).values
    pc = _pc_from_w(w, cov)
    out: dict[str, float] = {}
    for b in RISK_BUDGET_BLOCKS:
        out[b] = sum(pc[i] for i, t in enumerate(cols) if ticker_to_block.get(t) == b)
    total = sum(out.values())
    if total <= 0:
        return {b: 0.0 for b in RISK_BUDGET_BLOCKS}
    return {b: float(out[b] / total) for b in RISK_BUDGET_BLOCKS}


def rc_by_asset_from_weights(
    weights_risk: dict[str, float],
    cov_df: pd.DataFrame,
) -> dict[str, float]:
    """
    Compute percentage risk contribution (RC) per asset from RiskPortfolio weights and covariance.
    Returns dict ticker -> RC share (sum = 1 over present assets).
    """
    cols = [t for t in weights_risk if t in cov_df.columns and t in cov_df.index and weights_risk.get(t, 0) > 0]
    if not cols:
        return {}
    w = np.array([weights_risk[t] for t in cols])
    cov = cov_df.reindex(index=cols, columns=cols).fillna(0).values
    pc = _pc_from_w(w, cov)
    return {t: float(pc[i]) for i, t in enumerate(cols)}


def check_rb_corridor(
    actual_rc_block: dict[str, float],
    rc_block_targets: dict[str, float],
    corridor_pp: float = RB_CORRIDOR_PP,
) -> tuple[bool, list[str]]:
    """
    Check if realized block RC is within target ± corridor_pp (hard constraint).
    Returns (ok, list of violation messages).
    Used by run_optimization (production RB quality gate) and view_after_optimization (RB status).
    """
    violations: list[str] = []
    for b in RISK_BUDGET_BLOCKS:
        target = rc_block_targets.get(b)
        actual = actual_rc_block.get(b)
        if target is None or actual is None:
            continue
        lo = target - corridor_pp
        hi = target + corridor_pp
        if actual < lo - 1e-9 or actual > hi + 1e-9:
            violations.append(
                f"RB corridor: {b} actual={actual:.3f} outside [{lo:.3f}, {hi:.3f}] (target={target:.3f} ± {corridor_pp})"
            )
    return len(violations) == 0, violations
