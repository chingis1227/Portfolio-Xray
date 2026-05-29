"""Regression tests: snapshot analytics.tail_risk → Block 2.2 → Block 2.4 wiring."""

from __future__ import annotations

from typing import Any

from src.block_2_4_hidden_exposure import build_block_2_4_hidden_exposure
from src.portfolio_xray import build_portfolio_xray_v2
from src.snapshot import resolve_xray_snapshot_inputs


def _tail_analytics(
    *,
    metric_available: bool = True,
    var_95: float = -0.009,
    es_95: float = -0.014,
) -> dict[str, Any]:
    return {
        "tail_risk": {
            "method": "historical",
            "frequency": "daily",
            "window_months": 120,
            "window_label": "10y",
            "analysis_end": "2026-04-30",
            "n_obs": 2514,
            "metric_available": metric_available,
            "unavailable_reason": None if metric_available else "insufficient_daily_obs_lt_60",
            "var_95": var_95 if metric_available else None,
            "var_99": -0.016 if metric_available else None,
            "es_95": es_95 if metric_available else None,
            "es_99": -0.025 if metric_available else None,
        },
        "var_95": var_95 if metric_available else None,
        "var_99": -0.016 if metric_available else None,
        "es_95": es_95 if metric_available else None,
        "es_99": -0.025 if metric_available else None,
        "drawdown_structure": {
            "summary": {
                "pct_time_underwater": 0.567,
                "longest_underwater_months": 26,
            }
        },
        "rolling_sharpe_36m": {"last": 1.144},
        "rolling_vol_12m": {"last": 0.091},
        "rolling_beta_36m": {"last": 0.512},
    }


def _window_snapshot(label: str, *, analytics: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "window_label": label,
        "window_months": 120 if label == "10y" else 60 if label == "5y" else 36,
        "RC_asset": [{"ticker": "SPY", "rc_pct": 0.2}],
        "metrics": {
            "cagr": 0.099,
            "vol_annual": 0.096,
            "max_drawdown": -0.198,
            "sharpe": 0.799,
            "beta_portfolio": 0.513,
            "downside_beta": 0.536,
            "metric_quality": {"benchmark_ticker": "SPY", "n_obs": 120},
        },
        "analytics": analytics,
    }


def _aggregate_snapshot_without_analytics() -> dict[str, Any]:
    return {
        "RC_asset": [{"ticker": "SPY", "rc_pct": 0.2}],
        "metrics": {"cagr": 0.099, "beta_portfolio": 0.513},
    }


def test_resolve_xray_snapshot_inputs_prefers_10y_analytics() -> None:
    snapshots = {
        "10y": _window_snapshot("10y", analytics=_tail_analytics()),
        "5y": _window_snapshot("5y", analytics=_tail_analytics(var_95=-0.011, es_95=-0.015)),
    }
    inputs = resolve_xray_snapshot_inputs(
        snapshots,
        fallback_snapshot=_aggregate_snapshot_without_analytics(),
    )
    analytics = inputs["portfolio_analytics"]
    assert isinstance(analytics, dict)
    assert analytics["tail_risk"]["metric_available"] is True
    assert inputs["portfolio_metrics"]["cagr"] == 0.099
    assert inputs["drawdown_structure"] is not None


def test_portfolio_xray_block_2_2_tail_risk_from_snapshot_10y_analytics() -> None:
    snapshots = {"10y": _window_snapshot("10y", analytics=_tail_analytics())}
    inputs = resolve_xray_snapshot_inputs(
        snapshots,
        fallback_snapshot=_aggregate_snapshot_without_analytics(),
    )
    xray = build_portfolio_xray_v2(
        analysis_setup={"analysis_portfolio": {"portfolio_role": "user_current_portfolio"}},
        weights={"SPY": 0.5, "BND": 0.5},
        rc_asset=inputs["rc_asset"],
        stress_report={"factor_betas_5y": {"beta_eq": 0.4}},
        portfolio_valid=True,
        portfolio_metrics=inputs["portfolio_metrics"],
        portfolio_analytics=inputs["portfolio_analytics"],
        drawdown_structure=inputs["drawdown_structure"],
    )
    tail = xray["block_2_2_portfolio_metrics"]["tail_risk_diagnostics"]
    assert tail["metric_available"] is True
    assert tail["var_95"] == -0.009
    assert tail["es_95"] == -0.014
    assert tail["var_99"] == -0.016
    assert tail["es_99"] == -0.025
    assert tail["method"] == "historical"
    assert tail["frequency"] == "daily"
    assert tail["window"] == "10y"
    assert tail["n_obs"] == 2514
    warnings = xray["block_2_2_portfolio_metrics"]["data_quality_warnings"]
    assert not any("tail risk" in w.lower() for w in warnings)


def test_block_2_4_tail_risk_alert_uses_es_var_from_block_2_2() -> None:
    snapshots = {"10y": _window_snapshot("10y", analytics=_tail_analytics())}
    inputs = resolve_xray_snapshot_inputs(snapshots)
    xray = build_portfolio_xray_v2(
        analysis_setup={"analysis_portfolio": {"portfolio_role": "user_current_portfolio"}},
        weights={"SPY": 0.5, "BND": 0.5},
        rc_asset=inputs["rc_asset"],
        stress_report={"factor_betas_5y": {"beta_eq": 0.4}},
        portfolio_valid=True,
        portfolio_metrics=inputs["portfolio_metrics"],
        portfolio_analytics=inputs["portfolio_analytics"],
        drawdown_structure=inputs["drawdown_structure"],
    )
    block_22 = xray["block_2_2_portfolio_metrics"]
    block_21 = xray["block_2_1_asset_allocation"]
    block_23 = xray["block_2_3_factor_exposure"]
    alert = build_block_2_4_hidden_exposure(block_21, block_22, block_23)["alerts"]["tail_risk"]
    evidence_metrics = {row["metric"] for row in alert["evidence"]}
    assert "es_95" in evidence_metrics
    assert "var_95" in evidence_metrics
    assert "var_99" in evidence_metrics
    es_row = next(row for row in alert["evidence"] if row["metric"] == "es_95")
    assert es_row["value"] == -0.014
    assert alert["status"] in {"Low", "Medium", "High"}


def test_tail_risk_unavailable_when_all_windows_missing_tail_metrics() -> None:
    empty_analytics = {"rolling_sharpe_36m": {"last": 0.5}}
    snapshots = {
        "10y": _window_snapshot("10y", analytics=empty_analytics),
        "5y": _window_snapshot("5y", analytics=dict(empty_analytics)),
    }
    inputs = resolve_xray_snapshot_inputs(
        snapshots,
        fallback_snapshot=_aggregate_snapshot_without_analytics(),
    )
    xray = build_portfolio_xray_v2(
        analysis_setup={"analysis_portfolio": {"portfolio_role": "user_current_portfolio"}},
        weights={"SPY": 1.0},
        rc_asset=inputs["rc_asset"],
        stress_report={},
        portfolio_valid=True,
        portfolio_metrics=inputs["portfolio_metrics"],
        portfolio_analytics=inputs["portfolio_analytics"],
    )
    tail = xray["block_2_2_portfolio_metrics"]["tail_risk_diagnostics"]
    assert tail["metric_available"] is False
    assert tail["var_95"] is None
    assert tail["es_95"] is None
    warnings = xray["block_2_2_portfolio_metrics"]["data_quality_warnings"]
    assert any("tail risk" in w.lower() for w in warnings)


def test_resolve_xray_snapshot_inputs_fallback_5y_when_10y_tail_unavailable() -> None:
    snapshots = {
        "10y": _window_snapshot("10y", analytics={"tail_risk": {"metric_available": False}}),
        "5y": _window_snapshot("5y", analytics=_tail_analytics(var_95=-0.012, es_95=-0.017)),
    }
    inputs = resolve_xray_snapshot_inputs(snapshots)
    tail = inputs["portfolio_analytics"]["tail_risk"]
    assert tail["metric_available"] is True
    assert tail["var_95"] == -0.012
