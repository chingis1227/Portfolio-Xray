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

from src.config_schema import GROWTH_EM_DEBT_KEY, GROWTH_HY_KEY
from src.risk_contrib import (
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


def get_risk_portfolio_tickers(blocks: dict[str, list[str]]) -> list[str]:
    """Return tickers in RiskPortfolio: Growth + Duration + Inflation + Growth_HY + Growth_EM_debt. Exclude Liquidity, Tail."""
    out = []
    for b in RISK_BUDGET_BLOCKS:
        out.extend(blocks.get(b, []))
    for b in GROWTH_SUB_BLOCKS:
        out.extend(blocks.get(b, []))
    return out


def ticker_to_block_map(blocks: dict[str, list[str]]) -> dict[str, str]:
    """Return ticker -> block name for RiskPortfolio. Growth_HY and Growth_EM_debt map to 'Growth' for RC block."""
    m = {}
    for b in RISK_BUDGET_BLOCKS:
        for t in blocks.get(b, []):
            m[t] = b
    for b in GROWTH_SUB_BLOCKS:
        for t in blocks.get(b, []):
            m[t] = "Growth"
    return m


def growth_weight_caps(
    n: int,
    n_core: int,
    n_sat: int,
    rb_growth: float | None = None,
) -> tuple[float, float]:
    """Core/Satellite max weights for Growth. feasibility_constraints_spec §3.1; §6 Equity-Only when rb_growth >= 0.90."""
    if rb_growth is not None and rb_growth >= 0.90:
        # Equity-Only: max_weight_core <= 0.50, max_weight_sat in [0.10, 0.15]
        return 0.50, 0.15
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
    min_weight: float,
    max_single_security_weight_pct: float | None = None,
    rb_growth: float | None = None,
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

    bounds = []
    for t in tickers:
        block = ticker_to_block.get(t, "Growth")
        if block == "Growth":
            cap = max_core if t in growth_core_candidates else max_sat
        else:
            cap = 0.40
        if global_cap is not None:
            cap = min(cap, global_cap)
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
    max_core: float,
    max_sat: float,
    rb_growth: float,
) -> tuple[bool, str]:
    """
    Feasibility spec §2, §5, §6: check that risk budget is achievable with current block composition.
    Returns (ok, error_message). If not ok, error_message describes the first failed check.
    """
    rb = rc_block_targets or {}
    rb_g = float(rb.get("Growth", 1.0 / 3))
    rb_d = float(rb.get("Duration", 1.0 / 3))
    rb_i = float(rb.get("Inflation", 1.0 / 3))
    total = rb_g + rb_d + rb_i
    if total <= 0:
        return False, "rc_block_targets sum must be positive"
    rb_g /= total
    rb_d /= total
    rb_i /= total

    growth_tickers = (
        list(blocks.get("Growth", []))
        + list(blocks.get(GROWTH_HY_KEY, []))
        + list(blocks.get(GROWTH_EM_DEBT_KEY, []))
    )
    duration_tickers = list(blocks.get("Duration", []))
    inflation_tickers = list(blocks.get("Inflation", []))

    k_growth = len(growth_tickers)
    k_duration = len(duration_tickers)
    k_inflation = len(inflation_tickers)

    # Single-asset block: k_required = 1 (that asset's RC = block RC; feasibility_constraints_spec §3.2).
    k_required_g = 1 if k_growth == 1 else (math.ceil(rb_g / rc_asset_cap) if rc_asset_cap > 0 else 0)
    k_required_d = 1 if k_duration == 1 else (math.ceil(rb_d / rc_asset_cap) if rc_asset_cap > 0 else 0)
    k_required_i = 1 if k_inflation == 1 else (math.ceil(rb_i / rc_asset_cap) if rc_asset_cap > 0 else 0)

    if k_growth < k_required_g:
        return False, (
            f"Risk budget not achievable: Growth has {k_growth} assets, need at least "
            f"{k_required_g} (ceil(RB_growth/rc_asset_cap)). Add assets to Growth or lower RB_growth."
        )
    if k_duration < k_required_d:
        return False, (
            f"Risk budget not achievable: Duration has {k_duration} assets, need at least "
            f"{k_required_d}. Add assets to Duration or lower RB_duration."
        )
    if k_inflation < k_required_i:
        return False, (
            f"Risk budget not achievable: Inflation has {k_inflation} assets, need at least "
            f"{k_required_i}. Add assets to Inflation or lower RB_inflation."
        )

    n_core = sum(1 for t in growth_tickers if t in growth_core_candidates)
    n_sat = k_growth - n_core
    # Weight feasibility: Nc·max_core + Ns·max_sat >= W_growth (use rb_growth as required growth weight share)
    growth_capacity = n_core * max_core + n_sat * max_sat
    if growth_capacity < rb_g:
        return False, (
            f"Growth weight capacity {growth_capacity:.3f} < RB_growth {rb_g:.3f}. "
            "Increase Core/Satellite caps or add Growth assets (feasibility_constraints_spec §3.1)."
        )
    if rb_growth >= 0.90:
        # Equity-Only: Nc·max_core + Ns·max_sat >= 1.0
        if growth_capacity < 1.0:
            return False, (
                f"Equity-Only: Growth capacity {growth_capacity:.3f} < 1.0. "
                "Need Nc·0.5 + Ns·0.15 >= 1.0 (feasibility_constraints_spec §6)."
            )
    return True, ""


def run_risk_budget_optimization(
    returns_df: pd.DataFrame,
    blocks: dict[str, list[str]],
    rc_block_targets: dict[str, float],
    growth_core_candidates: list[str],
    rc_asset_cap_pct: float | None = None,
    min_single_security_weight_pct: float | None = None,
    max_single_security_weight_pct: float | None = None,
    window_months: int = 60,
) -> tuple[dict[str, float], str]:
    """
    Find RiskPortfolio weights satisfying risk budget (RC block shares) and feasibility.
    Objective: maximize expected return (Growth spec). Returns (weights_dict, status_message).
    RC_vol cap has priority over weight caps; if fallback solution violates RC cap, returns FAIL.
    """
    risk_tickers = get_risk_portfolio_tickers(blocks)
    if not risk_tickers:
        return {}, "FAIL: no RiskPortfolio tickers (Growth+Duration+Inflation+Growth_HY+Growth_EM_debt)"

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

    # Count assets per block in cols (feasibility: per-asset RC cap applies to every asset; single-asset block cannot exceed cap).
    duration_in_cols = [i for i, t in enumerate(cols) if ticker_to_block.get(t) == "Duration"]
    inflation_in_cols = [i for i, t in enumerate(cols) if ticker_to_block.get(t) == "Inflation"]
    growth_in_cols = [i for i, t in enumerate(cols) if ticker_to_block.get(t) == "Growth"]
    n_dur, n_infl, n_growth = len(duration_in_cols), len(inflation_in_cols), len(growth_in_cols)

    # Effective RB: if a block has one asset, its max RC = rc_asset_cap (per-asset cap); redistribute shortfall to other blocks.
    achievable_d = min(rb_duration, rc_asset_cap) if n_dur == 1 else rb_duration
    achievable_i = min(rb_inflation, rc_asset_cap) if n_infl == 1 else rb_inflation
    achievable_g = min(rb_growth, rc_asset_cap) if n_growth == 1 else rb_growth
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
    )

    effective_rb = {"Growth": rb_growth, "Duration": rb_duration, "Inflation": rb_inflation}
    ok, err = check_rb_achievement(
        blocks, effective_rb, rc_asset_cap, growth_core_candidates,
        n, max_core, max_sat, rb_growth,
    )
    if not ok:
        return {}, f"FAIL_FEASIBILITY: {err}"

    growth_hy_set = set(blocks.get(GROWTH_HY_KEY, []))
    growth_em_debt_set = set(blocks.get(GROWTH_EM_DEBT_KEY, []))
    hy_indices = [i for i, t in enumerate(cols) if t in growth_hy_set]
    em_debt_indices = [i for i, t in enumerate(cols) if t in growth_em_debt_set]

    # Per-asset RC cap: strict global cap for every asset (feasibility spec §1); no exception for single-asset blocks.
    rc_cap_per_asset = [rc_asset_cap] * n

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
        cap_i = rc_cap_per_asset[idx]

        def rc_cap(w: np.ndarray) -> float:
            pc = _pc_from_w(w, cov)
            return float(pc[idx] - cap_i)
        return rc_cap

    # RC_vol(HY) <= 10% * RC_vol(Growth); RC_vol(EM_debt) <= 10% * RC_vol(Growth)
    def constraint_rc_hy(w: np.ndarray) -> float:
        pc = _pc_from_w(w, cov)
        rc_g = sum(pc[i] for i, t in enumerate(cols) if ticker_to_block.get(t) == "Growth")
        rc_hy = sum(pc[i] for i in hy_indices) if hy_indices else 0.0
        return float(HY_EM_RC_CAP_FRACTION * rc_g - rc_hy)  # ineq: 0.1*rc_g - rc_hy >= 0

    def constraint_rc_em_debt(w: np.ndarray) -> float:
        pc = _pc_from_w(w, cov)
        rc_g = sum(pc[i] for i, t in enumerate(cols) if ticker_to_block.get(t) == "Growth")
        rc_em = sum(pc[i] for i in em_debt_indices) if em_debt_indices else 0.0
        return float(HY_EM_RC_CAP_FRACTION * rc_g - rc_em)

    constraints_core = [
        {"type": "eq", "fun": constraint_sum},
        {"type": "eq", "fun": constraint_rc_growth},
        {"type": "eq", "fun": constraint_rc_duration},
        {"type": "eq", "fun": constraint_rc_inflation},
    ]
    # Add HY/EM_debt ineq if any such assets in cols
    if hy_indices:
        constraints_core.append({"type": "ineq", "fun": constraint_rc_hy})
    if em_debt_indices:
        constraints_core.append({"type": "ineq", "fun": constraint_rc_em_debt})

    constraints_full = constraints_core + [
        {"type": "ineq", "fun": make_rc_cap(i)} for i in range(n)
    ]

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

    res = minimize(
        objective,
        x0.copy(),
        method="SLSQP",
        bounds=bounds,
        constraints=constraints_full,
        options={"maxiter": 1000, "ftol": 1e-9},
    )
    used_fallback = False
    if not res.success:
        res = minimize(
            objective,
            x0.copy(),
            method="SLSQP",
            bounds=bounds,
            constraints=constraints_core,
            options={"maxiter": 1000, "ftol": 1e-9},
        )
        if not res.success:
            w_fallback = np.clip(feas.x, min_weight, np.array([b[1] for b in bounds]) - 1e-8)
            w_fallback = w_fallback / w_fallback.sum()
            res = type("Res", (), {"success": True, "x": w_fallback})()
        used_fallback = True

    w = res.x
    pc = _pc_from_w(w, cov)

    # Post-solution validation: RC_vol cap has priority (policy). Use per-asset caps (single-asset block = RB_block).
    viol_idx = [i for i in range(n) if pc[i] > rc_cap_per_asset[i]]
    if viol_idx:
        viol_tickers = [cols[i] for i in viol_idx]
        if used_fallback:
            return {}, (
                f"FAIL_RC_CAP: After fallback, per-asset RC cap still violated by {viol_tickers}. "
                "RC_vol cap has priority over weight caps; cannot return this portfolio."
            )
        return {}, f"FAIL_RC_CAP: Per-asset RC cap violated: {viol_tickers}"

    rc_g = sum(pc[i] for i, t in enumerate(cols) if ticker_to_block.get(t) == "Growth")
    rc_hy = sum(pc[i] for i in hy_indices) if hy_indices else 0.0
    rc_em = sum(pc[i] for i in em_debt_indices) if em_debt_indices else 0.0
    if rc_g > 1e-12:
        if rc_hy > HY_EM_RC_CAP_FRACTION * rc_g + 1e-9:
            return {}, (
                f"FAIL_RC_CAP: RC_vol(HY)={rc_hy:.3f} > 10%*RC_vol(Growth)={HY_EM_RC_CAP_FRACTION*rc_g:.3f}. "
                "Growth_HY sub-limit violated."
            )
        if rc_em > HY_EM_RC_CAP_FRACTION * rc_g + 1e-9:
            return {}, (
                f"FAIL_RC_CAP: RC_vol(EM_debt)={rc_em:.3f} > 10%*RC_vol(Growth)={HY_EM_RC_CAP_FRACTION*rc_g:.3f}. "
                "Growth_EM_debt sub-limit violated."
            )

    rc_d = sum(pc[i] for i, t in enumerate(cols) if ticker_to_block.get(t) == "Duration")
    rc_i = sum(pc[i] for i, t in enumerate(cols) if ticker_to_block.get(t) == "Inflation")
    w_dict = {t: float(w[i]) for i, t in enumerate(cols)}
    for t in risk_tickers:
        if t not in w_dict:
            w_dict[t] = 0.0
    status_msg = ("OK (fallback) " if used_fallback else "OK ") + f"(RC G/D/I: {rc_g:.3f}/{rc_d:.3f}/{rc_i:.3f})"
    return w_dict, status_msg


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
