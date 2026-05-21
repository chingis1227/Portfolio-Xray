from __future__ import annotations

from types import SimpleNamespace

import pandas as pd

from run_optimization import _build_legacy_policy_optimizer_run_metadata


def _cfg() -> SimpleNamespace:
    return SimpleNamespace(
        tickers=["VOO", "BND", "GLD", "BIL"],
        min_single_security_weight_pct=0.01,
        max_single_security_weight_pct=0.6,
    )


def test_legacy_policy_optimizer_metadata_discloses_method_inputs_and_bounds() -> None:
    returns_window = pd.DataFrame(
        {"VOO": [0.01, 0.02], "BND": [0.003, 0.004], "GLD": [0.0, 0.01]},
        index=pd.to_datetime(["2026-03-31", "2026-04-30"]),
    )
    meta = _build_legacy_policy_optimizer_run_metadata(
        _cfg(),
        optimization_status="OK | OBJECTIVE_MODE=max_return | SOFT_VOL_TARGET=0.1200 LAMBDA=12",
        production_status="APPROVED",
        analysis_end="2026-04-30",
        returns_frequency="monthly",
        periods_per_year=12,
        window_months=120,
        secondary_window_months=60,
        risk_tickers_all=["VOO", "BND", "GLD"],
        eligible_universe=["VOO", "BND", "GLD"],
        cash_proxy_ticker="BIL",
        covariance_shrinkage=True,
        dual_covariance_enabled=False,
        young_diagnostics=None,
        per_ticker_young_caps=None,
        soft_target_vol_annual=0.12,
        soft_vol_penalty_lambda=12.0,
        soft_target_return_annual=0.06,
        soft_return_penalty_lambda=8.0,
        liquidity_floor_pct=0.05,
        current_vol_annual=0.11,
        target_vol_annual=0.12,
        cash_policy="allowed",
        mandate_gate_passed=True,
        weights_written=True,
        estimator_returns_window=returns_window,
    )

    assert meta["schema_version"] == "legacy_policy_optimizer_run_metadata_v1"
    assert meta["optimizer_role"] == "legacy_policy"
    assert meta["objective"]["objective_mode"] == "max_return"
    assert meta["expected_returns"]["source"] == "sample_mean_monthly_simple_returns"
    assert meta["covariance"]["method"] == "ledoit_wolf_shrinkage"
    assert meta["input_window"]["analysis_end"] == "2026-04-30"
    assert meta["input_window"]["returns_panel_end"] == "2026-04-30"
    assert meta["input_window"]["returns_panel_rows"] == 2
    assert len(meta["input_fingerprints"]["returns_panel_fingerprint"]) == 64
    assert len(meta["input_fingerprints"]["config_fingerprint"]) == 64
    assert len(meta["input_fingerprints"]["universe_fingerprint"]) == 64
    assert meta["expected_returns"]["analysis_end"] == "2026-04-30"
    assert meta["covariance"]["analysis_end"] == "2026-04-30"
    assert meta["covariance"]["methodology"]["schema_version"] == "optimizer_covariance_methodology_v1"
    assert meta["covariance"]["methodology"]["join_policy"] == "inner_join_complete_cases"
    assert meta["covariance"]["methodology"]["young_etf"]["enabled"] is False
    assert "Covariance method=ledoit_wolf_shrinkage" in meta["covariance"]["methodology_summary"]
    assert meta["universe"]["eligible_universe"] == ["VOO", "BND", "GLD"]
    assert meta["universe"]["universe_fingerprint"] == meta["input_fingerprints"]["universe_fingerprint"]
    assert meta["constraints"]["resolved_bounds_by_ticker"]["VOO"]["min_weight"] == 0.01
    assert meta["cash_policy"]["post_optimization_overlay"] == "ProLiquidity"
    assert meta["solver"]["fallback_used"] is False
    assert meta["release"]["weights_written"] is True


def test_legacy_policy_optimizer_metadata_marks_fallback_quality() -> None:
    meta = _build_legacy_policy_optimizer_run_metadata(
        _cfg(),
        optimization_status="OK_FALLBACK | OBJECTIVE_MODE=max_return",
        production_status="OK_FALLBACK",
        analysis_end="2026-04-30",
        returns_frequency="monthly",
        periods_per_year=12,
        window_months=120,
        secondary_window_months=60,
        risk_tickers_all=["VOO", "BND"],
        eligible_universe=["VOO", "BND"],
        cash_proxy_ticker="BIL",
        covariance_shrinkage=False,
        dual_covariance_enabled=True,
        young_diagnostics={"mode": "fallback_full_inner_join"},
        per_ticker_young_caps={"BND": 0.02},
        soft_target_vol_annual=None,
        soft_vol_penalty_lambda=12.0,
        soft_target_return_annual=None,
        soft_return_penalty_lambda=8.0,
        liquidity_floor_pct=0.0,
        current_vol_annual=0.1,
        target_vol_annual=0.12,
        cash_policy="prohibited",
        mandate_gate_passed=True,
        weights_written=True,
    )

    assert meta["covariance"]["source"] == "young_etf_dual_covariance"
    assert meta["covariance"]["method"] == "fallback_full_inner_join"
    assert meta["covariance"]["methodology"]["young_etf"]["enabled"] is True
    assert meta["covariance"]["methodology"]["young_etf"]["mode"] == "fallback_full_inner_join"
    assert meta["young_etf_methodology"]["per_ticker_caps"] == {"BND": 0.02}
    assert meta["constraints"]["per_ticker_young_caps"] == {"BND": 0.02}
    assert meta["solver"]["solver_success"] is True
    assert meta["solver"]["fallback_used"] is True
    assert meta["solver"]["fallback_reason"] == "primary_slsqp_retry_or_feasibility_projection"
    assert meta["solver"]["optimization_quality_status"] == "approximate_fallback"
