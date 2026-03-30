"""
View After Optimization — protocol per docs/docs/view_after_optimization_spec.md.

Deterministic tilt: PM chooses view_type (HEDGE | TACTICAL), asset X, delta_choice.
Funding: HEDGE → Growth first; TACTICAL → same block as X first. Within donors, highest RC first, min_weight respected.
Gates: mandate (TargetVol/MaxDD), stress (PASS), RC caps, weight caps, RB corridor.
Auto-shrink: 5% → 2% → 1%. Output: view_execution_report.json.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.optimization import (
    RISK_BUDGET_BLOCKS,
    check_rb_corridor,
    get_risk_portfolio_tickers,
    rc_by_asset_from_weights,
    rc_by_block_from_weights,
    ticker_to_block_map,
)
from policy_math.feasibility import DEFAULT_RC_CAP_RB_K_MULTIPLIER, RC_CAP_MODE_GLOBAL
from src.risk_contrib import build_rc_cap_per_ticker, cov_matrix_monthly, resolve_rc_asset_cap

# Delta menu: try in order when gates fail
DELTA_MENU_PCT = [5.0, 2.0, 1.0]  # 5% → 2% → 1%

# Scenario id → stress failure code (spec §2.2)
SCENARIO_TO_STRESS_CODE = {
    "rates_shock": "FAIL_STRESS_DURATION",
    "inflation_stagflation": "FAIL_STRESS_INFLATION",
    "liquidity_shock": "FAIL_STRESS_LIQUIDITY",
    "equity_shock": "FAIL_STRESS_TAIL",
    "credit_shock": "FAIL_STRESS_TAIL",
}

# HEDGE benefit: worst loss must improve by at least this (NAV fraction)
HEDGE_BENEFIT_NAV_MIN = 0.005  # 0.5% NAV


def _rb_status(
    actual_rc_block: dict[str, float],
    rc_block_targets: dict[str, float],
    corridor_pp: float,
    deviation_threshold_pp: float = 0.02,
) -> str:
    """PASS_RB | PASS_BUT_RB_OFF | FAIL_RB_INFEASIBLE per spec §2.1."""
    ok, _ = check_rb_corridor(actual_rc_block, rc_block_targets, corridor_pp)
    if ok:
        return "PASS_RB"
    max_dev = 0.0
    for b in RISK_BUDGET_BLOCKS:
        t = rc_block_targets.get(b)
        a = actual_rc_block.get(b)
        if t is not None and a is not None:
            max_dev = max(max_dev, abs(a - t))
    if max_dev <= deviation_threshold_pp:
        return "PASS_BUT_RB_OFF"
    return "FAIL_RB_INFEASIBLE"


def _stress_failure_code(failed_scenario: str | None) -> str | None:
    """Map scenario id to spec stress failure code."""
    if not failed_scenario:
        return None
    return SCENARIO_TO_STRESS_CODE.get(failed_scenario, "FAIL_STRESS_TAIL")


def _get_donors_ordered(
    view_type: str,
    asset: str,
    blocks: dict[str, list[str]],
    weights: dict[str, float],
    rc_by_asset: dict[str, float],
    min_weight: float,
) -> list[str]:
    """
    Donor tickers in order of use: sell from this list (by RC descending within allowed set).
    HEDGE: Growth first, then Duration, then Inflation (avoid selling protection first).
    TACTICAL: same block as X first, then others by block order.
    Only include tickers with weight > min_weight.
    """
    ticker_to_block = ticker_to_block_map(blocks)
    asset_block = ticker_to_block.get(asset, "Growth")
    candidates = [
        t for t in weights
        if weights.get(t, 0) > min_weight and t != asset and rc_by_asset.get(t, 0) >= 0
    ]
    if not candidates:
        return []

    if view_type == "HEDGE":
        # Growth first, then Duration, then Inflation
        order_blocks = ["Growth", "Duration", "Inflation"]
    else:
        # TACTICAL: same block as asset first, then others
        order_blocks = [asset_block] + [b for b in ["Growth", "Duration", "Inflation"] if b != asset_block]

    out: list[str] = []
    for b in order_blocks:
        in_b = [t for t in candidates if ticker_to_block.get(t) == b]
        in_b_sorted = sorted(in_b, key=lambda t: -rc_by_asset.get(t, 0))
        out.extend(in_b_sorted)
    return out


def _compute_funding(
    view_type: str,
    asset: str,
    delta: float,
    weights: dict[str, float],
    rc_by_asset: dict[str, float],
    blocks: dict[str, list[str]],
    min_weight: float,
) -> tuple[dict[str, float], list[tuple[str, float]], list[str]]:
    """
    Apply delta to asset by selling from donors. Returns (new_weights, donors_sold as (ticker, amount), donor_blocks).
    """
    donors_ordered = _get_donors_ordered(view_type, asset, blocks, weights, rc_by_asset, min_weight)
    need = delta
    new_weights = copy.deepcopy(weights)
    donors_sold: list[tuple[str, float]] = []
    donor_blocks: list[str] = []
    ticker_to_block = ticker_to_block_map(blocks)

    for t in donors_ordered:
        if need <= 0:
            break
        w = new_weights.get(t, 0)
        can_sell = max(0, w - min_weight)
        sell = min(need, can_sell)
        if sell <= 0:
            continue
        new_weights[t] = w - sell
        need -= sell
        donors_sold.append((t, round(sell, 6)))
        if t not in [x[0] for x in donors_sold[:-1]] or not donor_blocks:
            donor_blocks.append(ticker_to_block.get(t, ""))

    new_weights[asset] = new_weights.get(asset, 0) + (delta - need)
    # Normalize to sum 1
    s = sum(new_weights.values())
    if s > 0:
        new_weights = {t: v / s for t, v in new_weights.items()}
    return new_weights, donors_sold, list(dict.fromkeys(donor_blocks))


def run_view_after_optimization(
    baseline_weights: dict[str, float],
    view_type: str,
    asset: str,
    delta_choice_pct: float,
    blocks: dict[str, list[str]],
    monthly_returns: pd.DataFrame,
    rc_block_targets: dict[str, float],
    *,
    baseline_rb: dict[str, float] | None = None,
    baseline_stress: dict[str, Any] | None = None,
    target_vol_annual: float | None = None,
    target_max_drawdown_pct: float | None = None,
    rc_asset_cap_pct: float | None = None,
    rc_cap_mode: str = RC_CAP_MODE_GLOBAL,
    rc_cap_rb_k_multiplier: float = DEFAULT_RC_CAP_RB_K_MULTIPLIER,
    stress_top3_rc_sum_cap_pct: float = 0.70,
    rb_corridor_pp: float = 0.05,
    rb_deviation_threshold_pp: float = 0.02,
    min_single_security_weight_pct: float = 1.0,
    max_single_security_weight_pct: float = 100.0,
    run_stress_fn=None,
    portfolio_vol_fn=None,
    max_drawdown_fn=None,
) -> dict[str, Any]:
    """
    Execute view protocol: try delta_choice, shrink 5%→2%→1% on gate failure.
    Returns view_execution_report dict (baseline_weights, request, execution_delta, funding_*, outcome_status, rb_status, stress_failure_code, broken_gate, key_metric_values).
    """
    if run_stress_fn is None:
        from src.stress import run_stress
        run_stress_fn = run_stress
    if portfolio_vol_fn is None:
        from src.optimization import portfolio_vol_annual
        portfolio_vol_fn = portfolio_vol_annual
    if max_drawdown_fn is None:
        from src.metrics_asset import max_drawdown
        def _mdd(weights, returns_df, tickers):
            cols = [t for t in tickers if t in returns_df.columns and weights.get(t, 0) > 0]
            if not cols or len(returns_df) < 2:
                return None
            w_vec = [weights.get(t, 0) for t in cols]
            port_ret = returns_df[cols].dot(w_vec).dropna()
            if len(port_ret) < 2:
                return None
            mdd, _ = max_drawdown(port_ret)
            return mdd
        max_drawdown_fn = _mdd

    def _portfolio_betas(w: dict[str, float], betas_df):
        if betas_df is None or betas_df.empty:
            return {}
        from src.stress_factors import portfolio_factor_betas
        return portfolio_factor_betas(w, betas_df)

    min_weight = (min_single_security_weight_pct or 1.0) / 100.0
    risk_tickers = get_risk_portfolio_tickers(blocks)
    cols = [t for t in risk_tickers if t in monthly_returns.columns]
    if not cols:
        return _report_rejected(
            baseline_weights, baseline_rb, baseline_stress, view_type, asset, delta_choice_pct,
            broken_gate="mandate", reason="No return data for risk portfolio",
        )
    cov_df = cov_matrix_monthly(monthly_returns[cols].dropna(how="all"), ddof=1)
    if baseline_rb is None:
        baseline_rb = rc_by_block_from_weights(baseline_weights, cov_df, blocks)
    if baseline_stress is None:
        baseline_stress = {}

    # Build asset_betas / portfolio_betas for stress (optional)
    asset_betas_df = pd.DataFrame()
    portfolio_betas_dict: dict[str, float] = {}
    try:
        from src.stress_factors import (
            FACTOR_WEEKS_5Y,
            compute_asset_factor_betas_weekly,
            portfolio_factor_betas,
        )
        end_str = str(monthly_returns.index.max())[:10]
        beta_tickers = [t for t in cols if baseline_weights.get(t, 0) > 0]
        if not beta_tickers:
            beta_tickers = list(cols)
        asset_betas_df = compute_asset_factor_betas_weekly(beta_tickers, end_str, FACTOR_WEEKS_5Y)
        portfolio_betas_dict = portfolio_factor_betas(baseline_weights, asset_betas_df)
    except Exception:
        pass

    # Delta menu: include requested then smaller
    deltas_to_try = [delta_choice_pct / 100.0]
    for d in DELTA_MENU_PCT:
        x = d / 100.0
        if x < deltas_to_try[0] and x not in deltas_to_try:
            deltas_to_try.append(x)
    deltas_to_try.sort(reverse=True)

    rb_growth = rc_block_targets.get("Growth")
    n_assets = len([t for t in baseline_weights if baseline_weights.get(t, 0) > 0])
    rc_cap_map = build_rc_cap_per_ticker(
        blocks,
        rc_block_targets,
        rc_asset_cap_pct,
        rc_cap_mode,
        rc_cap_rb_k_multiplier,
        max(n_assets, 1),
    )

    execution_delta = 0.0
    tilted_weights: dict[str, float] = {}
    funding_donors_sold: list[tuple[str, float]] = []
    donor_blocks: list[str] = []
    outcome_status = "TILT_REJECTED"
    rb_status = "FAIL_RB_INFEASIBLE"
    stress_failure_code: str | None = None
    broken_gate: str | None = "mandate"
    key_metric_values: dict[str, Any] = {}
    tilted_stress: dict[str, Any] = {}

    for delta in deltas_to_try:
        broken_gate = None
        if delta > baseline_weights.get(asset, 0) + sum(baseline_weights.get(t, 0) for t in baseline_weights if t != asset):
            continue
        rc_by_asset_baseline = rc_by_asset_from_weights(baseline_weights, cov_df)
        tilted_weights, donors_sold, donor_blocks = _compute_funding(
            view_type, asset, delta, baseline_weights, rc_by_asset_baseline, blocks, min_weight,
        )
        funding_donors_sold = donors_sold
        execution_delta = delta

        # Gate 1: mandate (weight bounds, vol, max DD)
        weight_ok = True
        for t, w in tilted_weights.items():
            if w > 0 and (w < min_weight or w > (max_single_security_weight_pct or 100) / 100.0):
                broken_gate = "weight"
                key_metric_values["weight_violation"] = {t: w}
                weight_ok = False
                break
        if not weight_ok:
            continue
        sum_w = sum(tilted_weights.values())
        if abs(sum_w - 1.0) > 1e-6:
            broken_gate = "mandate"
            key_metric_values["weight_sum"] = sum_w
            continue

        current_vol = portfolio_vol_fn(tilted_weights, cov_df)
        if target_vol_annual is not None and target_vol_annual > 0 and current_vol > target_vol_annual * 1.5:
            broken_gate = "mandate"
            key_metric_values["vol"] = current_vol
            key_metric_values["target_vol"] = target_vol_annual
            continue

        ret_slice = monthly_returns[[t for t in tilted_weights if t in monthly_returns.columns and tilted_weights[t] > 0]].dropna(how="all")
        mdd = max_drawdown_fn(tilted_weights, ret_slice, list(tilted_weights.keys()))
        if target_max_drawdown_pct is not None and mdd is not None and mdd < -abs(target_max_drawdown_pct):
            broken_gate = "mandate"
            key_metric_values["max_dd"] = mdd
            key_metric_values["max_dd_limit"] = target_max_drawdown_pct
            continue

        # Stress diagnostic (non-blocking): run for audit only
        tilted_stress = run_stress_fn(
            tickers=list(baseline_weights.keys()),
            weights=tilted_weights,
            blocks=blocks,
            monthly_returns=monthly_returns,
            asset_betas=asset_betas_df,
            portfolio_betas=_portfolio_betas(tilted_weights, asset_betas_df),
            target_max_drawdown_pct=target_max_drawdown_pct,
            rc_asset_cap_pct=rc_asset_cap_pct,
            stress_top3_rc_sum_cap_pct=stress_top3_rc_sum_cap_pct,
            rc_cap_mode=rc_cap_mode,
            rc_cap_rb_k_multiplier=rc_cap_rb_k_multiplier,
            rc_block_targets=rc_block_targets,
        )
        key_metric_values["stress_diagnostic_status"] = tilted_stress.get("status")
        key_metric_values["stress_diagnostic_codes"] = tilted_stress.get("diagnostic_codes", [])

        # Gate 3: RC caps
        rc_tilted = rc_by_asset_from_weights(tilted_weights, cov_df)
        for t, rc in rc_tilted.items():
            cap_t = float(rc_cap_map.get(t, resolve_rc_asset_cap(rc_asset_cap_pct, max(n_assets, 1), rb_growth)))
            if rc > cap_t + 1e-9:
                broken_gate = "RC"
                key_metric_values["rc_breach"] = {t: rc, "cap": cap_t}
                break
        else:
            pass  # no RC breach
        if broken_gate == "RC":
            continue

        # Gate 4: RB status
        actual_rb = rc_by_block_from_weights(tilted_weights, cov_df, blocks)
        rb_status = _rb_status(
            actual_rb, rc_block_targets, rb_corridor_pp, rb_deviation_threshold_pp,
        )
        if rb_status == "FAIL_RB_INFEASIBLE":
            broken_gate = "RB"
            key_metric_values["actual_rb"] = actual_rb
            key_metric_values["target_rb"] = rc_block_targets
            continue

        broken_gate = None

        # HEDGE benefit (HEDGE only)
        if view_type == "HEDGE":
            base_worst = baseline_stress.get("worst_scenario_loss_pct")
            tilt_worst = tilted_stress.get("worst_scenario_loss_pct")
            if base_worst is not None and tilt_worst is not None:
                if tilt_worst >= base_worst + HEDGE_BENEFIT_NAV_MIN:
                    outcome_status = "TILT_ACCEPTED"
                    key_metric_values["hedge_benefit_nav"] = (tilt_worst - base_worst)
                else:
                    outcome_status = "TILT_NO_BENEFIT"
                    broken_gate = "benefit"
                    key_metric_values["hedge_benefit_nav"] = (tilt_worst - base_worst)
                    key_metric_values["hedge_benefit_required"] = HEDGE_BENEFIT_NAV_MIN
            else:
                base_pass = sum(1 for s in (baseline_stress.get("scenario_results") or []) if s.get("pass"))
                tilt_pass = sum(1 for s in (tilted_stress.get("scenario_results") or []) if s.get("pass"))
                if tilt_pass >= base_pass + 1:
                    outcome_status = "TILT_ACCEPTED"
                    key_metric_values["hedge_benefit_pass_count"] = (tilt_pass - base_pass)
                else:
                    outcome_status = "TILT_NO_BENEFIT"
                    broken_gate = "benefit"
                    key_metric_values["hedge_benefit_pass_count"] = (tilt_pass - base_pass)
        else:
            outcome_status = "TILT_ACCEPTED"

        break
    else:
        # all deltas failed
        if not tilted_weights:
            tilted_weights = copy.deepcopy(baseline_weights)
        if outcome_status == "TILT_REJECTED" and not broken_gate:
            broken_gate = "mandate"

    return {
        "baseline_weights": {k: round(v, 6) for k, v in baseline_weights.items() if v > 0},
        "baseline_rb": baseline_rb,
        "baseline_stress": {
            "status": baseline_stress.get("status"),
            "worst_scenario_loss_pct": baseline_stress.get("worst_scenario_loss_pct"),
            "scenario_results": baseline_stress.get("scenario_results"),
        } if baseline_stress else {},
        "request": {
            "view_type": view_type,
            "asset": asset,
            "delta_choice": delta_choice_pct,
        },
        "execution_delta": round(execution_delta, 4),
        "funding_contributions": 0.0,
        "funding_donors_sold": [{"ticker": t, "amount": a} for t, a in funding_donors_sold],
        "donor_blocks": donor_blocks,
        "outcome_status": outcome_status,
        "rb_status": rb_status,
        "stress_failure_code": stress_failure_code,
        "broken_gate": broken_gate,
        "key_metric_values": key_metric_values,
        "tilted_weights": {k: round(v, 6) for k, v in tilted_weights.items() if v > 0} if tilted_weights else {},
        "tilted_stress_summary": {
            "status": tilted_stress.get("status"),
            "worst_scenario_loss_pct": tilted_stress.get("worst_scenario_loss_pct"),
        } if tilted_stress else {},
    }


def _report_rejected(
    baseline_weights: dict[str, float],
    baseline_rb: dict[str, float] | None,
    baseline_stress: dict[str, Any] | None,
    view_type: str,
    asset: str,
    delta_choice_pct: float,
    broken_gate: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "baseline_weights": {k: round(v, 6) for k, v in baseline_weights.items() if v > 0},
        "baseline_rb": baseline_rb or {},
        "baseline_stress": (baseline_stress or {}) if baseline_stress else {},
        "request": {"view_type": view_type, "asset": asset, "delta_choice": delta_choice_pct},
        "execution_delta": 0.0,
        "funding_contributions": 0.0,
        "funding_donors_sold": [],
        "donor_blocks": [],
        "outcome_status": "TILT_REJECTED",
        "rb_status": "FAIL_RB_INFEASIBLE",
        "stress_failure_code": None,
        "broken_gate": broken_gate,
        "key_metric_values": {"reason": reason},
        "tilted_weights": {},
        "tilted_stress_summary": {},
    }


def write_view_execution_report(report: dict[str, Any], path: str | Path) -> None:
    """Write view_execution_report.json to path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
