"""
View After Optimization — tilt protocol (simplified, no risk-budget blocks).

PM chooses view_type (HEDGE | TACTICAL), asset X, delta. Funding sells from other
positions in descending RC order. Gates: weight bounds, target vol, max DD, per-asset RC caps.
Stress suite is diagnostic-only (run_stress). Auto-shrink: 5% → 2% → 1%.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.optimization import portfolio_vol_annual, rc_by_asset_from_weights
from src.risk_contrib import build_rc_cap_per_ticker, cov_matrix_monthly, resolve_rc_asset_cap

DELTA_MENU_PCT = [5.0, 2.0, 1.0]
HEDGE_BENEFIT_NAV_MIN = 0.005


def _get_donors_ordered(
    asset: str,
    weights: dict[str, float],
    rc_by_asset: dict[str, float],
    min_weight: float,
) -> list[str]:
    """Donors: other tickers with weight > min_weight, highest RC first."""
    candidates = [
        t for t in weights
        if weights.get(t, 0) > min_weight and t != asset and rc_by_asset.get(t, 0) >= 0
    ]
    return sorted(candidates, key=lambda t: -rc_by_asset.get(t, 0))


def _compute_funding(
    asset: str,
    delta: float,
    weights: dict[str, float],
    rc_by_asset: dict[str, float],
    min_weight: float,
) -> tuple[dict[str, float], list[tuple[str, float]]]:
    donors_ordered = _get_donors_ordered(asset, weights, rc_by_asset, min_weight)
    need = delta
    new_weights = copy.deepcopy(weights)
    donors_sold: list[tuple[str, float]] = []

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

    new_weights[asset] = new_weights.get(asset, 0) + (delta - need)
    s = sum(new_weights.values())
    if s > 0:
        new_weights = {t: v / s for t, v in new_weights.items()}
    return new_weights, donors_sold


def run_view_after_optimization(
    baseline_weights: dict[str, float],
    view_type: str,
    asset: str,
    delta_choice_pct: float,
    monthly_returns: pd.DataFrame,
    *,
    cash_proxy_ticker: str | None = None,
    baseline_stress: dict[str, Any] | None = None,
    target_vol_annual: float | None = None,
    target_max_drawdown_pct: float | None = None,
    rc_asset_cap_pct: float | None = None,
    stress_top3_rc_sum_cap_pct: float = 0.70,
    min_single_security_weight_pct: float = 1.0,
    max_single_security_weight_pct: float = 100.0,
    run_stress_fn=None,
    portfolio_vol_fn=None,
    max_drawdown_fn=None,
    **_: Any,
) -> dict[str, Any]:
    if run_stress_fn is None:
        from src.stress import run_stress

        run_stress_fn = run_stress
    if portfolio_vol_fn is None:
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

    def _portfolio_betas(w: dict[str, float], betas_df: pd.DataFrame):
        if betas_df is None or betas_df.empty:
            return {}
        from src.stress_factors import portfolio_factor_betas

        return portfolio_factor_betas(w, betas_df)

    min_weight = (min_single_security_weight_pct or 1.0) / 100.0
    cash = (cash_proxy_ticker or "BIL").strip().upper()
    risk_tickers = [t for t in baseline_weights if str(t).strip().upper() != cash]
    cols = [t for t in risk_tickers if t in monthly_returns.columns]
    if not cols:
        return _report_rejected(
            baseline_weights,
            baseline_stress,
            view_type,
            asset,
            delta_choice_pct,
            broken_gate="mandate",
            reason="No return data for risk portfolio",
        )
    cov_df = cov_matrix_monthly(monthly_returns[cols].dropna(how="all"), ddof=1)
    if baseline_stress is None:
        baseline_stress = {}

    asset_betas_df = pd.DataFrame()
    try:
        from src.stress_factors import FACTOR_WEEKS_5Y, compute_asset_factor_betas_weekly, portfolio_factor_betas

        end_str = str(monthly_returns.index.max())[:10]
        beta_tickers = [t for t in cols if baseline_weights.get(t, 0) > 0] or list(cols)
        asset_betas_df = compute_asset_factor_betas_weekly(beta_tickers, end_str, FACTOR_WEEKS_5Y)
        _ = portfolio_factor_betas(baseline_weights, asset_betas_df)
    except Exception:
        pass

    deltas_to_try = [delta_choice_pct / 100.0]
    for d in DELTA_MENU_PCT:
        x = d / 100.0
        if x < deltas_to_try[0] and x not in deltas_to_try:
            deltas_to_try.append(x)
    deltas_to_try.sort(reverse=True)

    n_assets = len([t for t in baseline_weights if baseline_weights.get(t, 0) > 0])
    rc_cap_map = build_rc_cap_per_ticker(cols, rc_asset_cap_pct, max(n_assets, 1))

    execution_delta = 0.0
    tilted_weights: dict[str, float] = {}
    funding_donors_sold: list[tuple[str, float]] = []
    outcome_status = "TILT_REJECTED"
    rb_status = "N_A"
    stress_failure_code: str | None = None
    broken_gate: str | None = "mandate"
    key_metric_values: dict[str, Any] = {}
    tilted_stress: dict[str, Any] = {}

    for delta in deltas_to_try:
        broken_gate = None
        if delta > baseline_weights.get(asset, 0) + sum(baseline_weights.get(t, 0) for t in baseline_weights if t != asset):
            continue
        rc_by_asset_baseline = rc_by_asset_from_weights(baseline_weights, cov_df)
        tilted_weights, donors_sold = _compute_funding(asset, delta, baseline_weights, rc_by_asset_baseline, min_weight)
        funding_donors_sold = donors_sold
        execution_delta = delta

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

        ret_slice = monthly_returns[
            [t for t in tilted_weights if t in monthly_returns.columns and tilted_weights[t] > 0]
        ].dropna(how="all")
        mdd = max_drawdown_fn(tilted_weights, ret_slice, list(tilted_weights.keys()))
        if target_max_drawdown_pct is not None and mdd is not None and mdd < -abs(target_max_drawdown_pct):
            broken_gate = "mandate"
            key_metric_values["max_dd"] = mdd
            key_metric_values["max_dd_limit"] = target_max_drawdown_pct
            continue

        tilted_stress = run_stress_fn(
            tickers=list(baseline_weights.keys()),
            weights=tilted_weights,
            monthly_returns=monthly_returns,
            asset_betas=asset_betas_df,
            portfolio_betas=_portfolio_betas(tilted_weights, asset_betas_df),
            target_max_drawdown_pct=target_max_drawdown_pct,
            rc_asset_cap_pct=rc_asset_cap_pct,
            stress_top3_rc_sum_cap_pct=stress_top3_rc_sum_cap_pct,
            cash_proxy_ticker=cash_proxy_ticker or "BIL",
        )
        key_metric_values["stress_diagnostic_status"] = tilted_stress.get("status")
        key_metric_values["stress_diagnostic_codes"] = tilted_stress.get("diagnostic_codes", [])

        rc_tilted = rc_by_asset_from_weights(tilted_weights, cov_df)
        cap_ref = resolve_rc_asset_cap(rc_asset_cap_pct, max(n_assets, 1))
        for t, rc in rc_tilted.items():
            cap_t = float(rc_cap_map.get(t, cap_ref))
            if rc > cap_t + 1e-9:
                broken_gate = "RC"
                key_metric_values["rc_breach"] = {t: rc, "cap": cap_t}
                break
        else:
            pass
        if broken_gate == "RC":
            continue

        broken_gate = None

        if view_type == "HEDGE":
            base_worst = baseline_stress.get("worst_scenario_loss_pct")
            tilt_worst = tilted_stress.get("worst_scenario_loss_pct")
            if base_worst is not None and tilt_worst is not None:
                if tilt_worst >= base_worst + HEDGE_BENEFIT_NAV_MIN:
                    outcome_status = "TILT_ACCEPTED"
                    key_metric_values["hedge_benefit_nav"] = tilt_worst - base_worst
                else:
                    outcome_status = "TILT_NO_BENEFIT"
                    broken_gate = "benefit"
                    key_metric_values["hedge_benefit_nav"] = tilt_worst - base_worst
                    key_metric_values["hedge_benefit_required"] = HEDGE_BENEFIT_NAV_MIN
            else:
                base_pass = sum(1 for s in (baseline_stress.get("scenario_results") or []) if s.get("pass"))
                tilt_pass = sum(1 for s in (tilted_stress.get("scenario_results") or []) if s.get("pass"))
                if tilt_pass >= base_pass + 1:
                    outcome_status = "TILT_ACCEPTED"
                    key_metric_values["hedge_benefit_pass_count"] = tilt_pass - base_pass
                else:
                    outcome_status = "TILT_NO_BENEFIT"
                    broken_gate = "benefit"
                    key_metric_values["hedge_benefit_pass_count"] = tilt_pass - base_pass
        else:
            outcome_status = "TILT_ACCEPTED"

        break
    else:
        if not tilted_weights:
            tilted_weights = copy.deepcopy(baseline_weights)
        if outcome_status == "TILT_REJECTED" and not broken_gate:
            broken_gate = "mandate"

    return {
        "baseline_weights": {k: round(v, 6) for k, v in baseline_weights.items() if v > 0},
        "baseline_stress": {
            "status": baseline_stress.get("status"),
            "worst_scenario_loss_pct": baseline_stress.get("worst_scenario_loss_pct"),
            "scenario_results": baseline_stress.get("scenario_results"),
        } if baseline_stress else {},
        "request": {"view_type": view_type, "asset": asset, "delta_choice": delta_choice_pct},
        "execution_delta": round(execution_delta, 4),
        "funding_contributions": 0.0,
        "funding_donors_sold": [{"ticker": t, "amount": a} for t, a in funding_donors_sold],
        "donor_blocks": [],
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
    baseline_stress: dict[str, Any] | None,
    view_type: str,
    asset: str,
    delta_choice_pct: float,
    broken_gate: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "baseline_weights": {k: round(v, 6) for k, v in baseline_weights.items() if v > 0},
        "baseline_stress": (baseline_stress or {}) if baseline_stress else {},
        "request": {"view_type": view_type, "asset": asset, "delta_choice": delta_choice_pct},
        "execution_delta": 0.0,
        "funding_contributions": 0.0,
        "funding_donors_sold": [],
        "donor_blocks": [],
        "outcome_status": "TILT_REJECTED",
        "rb_status": "N_A",
        "stress_failure_code": None,
        "broken_gate": broken_gate,
        "key_metric_values": {"reason": reason},
        "tilted_weights": {},
        "tilted_stress_summary": {},
    }


def write_view_execution_report(report: dict[str, Any], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
