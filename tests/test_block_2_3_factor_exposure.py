from __future__ import annotations

import pytest

from src.block_2_3_factor_exposure import (
    BLOCK_2_3_ID,
    PRODUCTION_BETA_KEYS,
    PRODUCTION_FACTOR_UNIVERSE,
    build_block_2_3_factor_exposure,
)
from src.portfolio_xray import build_portfolio_xray_v2


def _analysis_setup() -> dict:
    return {
        "version": "analysis_setup_v1",
        "portfolio_input": {
            "analysis_subject_type": "current_portfolio",
            "source_analysis_mode": "analyze_current_weights",
            "investor_currency": "USD",
        },
        "analysis_subject": {"type": "current_portfolio"},
        "analysis_portfolio": {
            "weights": {"VOO": 0.5, "BND": 0.4, "Cash USD": 0.1},
            "cash_handling": {
                "cash_proxy_ticker": "BIL",
                "real_cash_holdings": [{"ticker": "Cash USD", "weight": 0.1}],
            },
        },
    }


def _full_beta_map(seed: float = 0.1) -> dict[str, float]:
    return {key: round(seed + idx * 0.01, 4) for idx, key in enumerate(PRODUCTION_BETA_KEYS)}


def _regression_block(*, n_obs: int = 250, p_value: float = 0.04) -> dict:
    betas = _full_beta_map(0.2)
    return {
        "window_weeks": 260,
        "n_obs": n_obs,
        "r2": 0.42,
        "adj_r2": 0.39,
        "betas": betas,
        "t": {key: 2.2 for key in PRODUCTION_BETA_KEYS},
        "p": {key: p_value for key in PRODUCTION_BETA_KEYS},
        "hac_inference": {
            "se_type": "hac_newey_west",
            "kernel": "bartlett",
            "max_lags": 4,
            "t": [0.0] + [2.5 for _ in PRODUCTION_BETA_KEYS],
            "p": [0.9] + [p_value for _ in PRODUCTION_BETA_KEYS],
            "ci_low": [0.0] + [0.1 for _ in PRODUCTION_BETA_KEYS],
            "ci_high": [0.0] + [0.3 for _ in PRODUCTION_BETA_KEYS],
        },
    }


def _decomp() -> dict:
    rows = []
    for idx, beta in enumerate(PRODUCTION_BETA_KEYS, start=1):
        rows.append(
            {
                "factor": "vix" if beta == "beta_vix" else PRODUCTION_FACTOR_UNIVERSE[idx - 1],
                "beta_key": beta,
                "gross_total_variance_share": 0.10 / idx,
                "net_total_variance_share": 0.08 / idx,
                "direction": "risk_adder",
            }
        )
    return {
        "status": "available",
        "method": "r2_scaled_factor_rc_plus_residual",
        "r2": 0.5,
        "rows": rows,
    }


def _stress_report() -> dict:
    return {
        "factor_betas_5y": _full_beta_map(0.2),
        "factor_betas_10y": _full_beta_map(0.15),
        "factor_regression_5y": _regression_block(n_obs=250, p_value=0.04),
        "factor_regression_10y": _regression_block(n_obs=480, p_value=0.08),
        "factor_betas_kalman": {
            "status": "available",
            "method": "kalman_random_walk_weekly_factor_betas",
            "latest": _full_beta_map(0.22),
            "latest_date": "2026-05-22",
        },
        "factor_variance_decomposition": _decomp(),
        "factor_diagnostics_meta": {
            "status": "available",
            "source": "cached_daily_returns_weekly_ols",
            "factor_beta_keys": list(PRODUCTION_BETA_KEYS),
            "missing_factors": [],
            "aligned_weekly_observations": 250,
        },
    }


def assert_block_2_3_product_contract(block: dict) -> None:
    assert block["block"] == BLOCK_2_3_ID
    assert block["block_id"] == "2.3"
    assert block["block_name"] == "Factor Exposure / Factor Sensitivity"
    assert block["status"] in {"available", "partial", "unavailable"}
    assert block["factor_universe"] == list(PRODUCTION_FACTOR_UNIVERSE)
    for key in (
        "factor_beta_snapshot",
        "factor_betas_5y",
        "factor_betas_10y",
        "kalman_current_beta",
        "factor_significance_confidence",
        "factor_variance_contribution",
        "factor_risk_ranking",
        "factor_exposure_summary",
        "data_quality_warnings",
        "factor_diagnostics_meta",
        "naming_validation",
        "stress_lab_separation",
    ):
        assert key in block
    assert set(block["factor_beta_snapshot"]) == set(PRODUCTION_BETA_KEYS)
    assert set(block["factor_betas_5y"]["betas"]) == set(PRODUCTION_BETA_KEYS)
    assert set(block["factor_betas_10y"]["betas"]) == set(PRODUCTION_BETA_KEYS)
    assert set(block["kalman_current_beta"]["betas"]) == set(PRODUCTION_BETA_KEYS)
    assert set(block["factor_significance_confidence"]) == set(PRODUCTION_BETA_KEYS)
    assert len(block["factor_risk_ranking"]) <= 3
    assert block["stress_lab_separation"]["no_scenario_shocks_in_this_block"] is True
    assert block["stress_lab_separation"]["no_rebalance_recommendations"] is True


def test_block_2_3_available_contract_from_stress_report() -> None:
    block = build_block_2_3_factor_exposure(
        stress_report=_stress_report(),
        analysis_setup=_analysis_setup(),
        weights={"VOO": 0.5, "BND": 0.4, "Cash USD": 0.1},
    )

    assert_block_2_3_product_contract(block)
    assert block["status"] == "available"
    assert block["factor_betas_5y"]["status"] == "available"
    assert block["factor_betas_10y"]["status"] == "available"
    assert block["kalman_current_beta"]["available"] is True
    assert block["factor_significance_confidence"]["beta_eq"]["status"] == "significant"
    assert block["factor_variance_contribution"]["status"] == "available"
    assert block["factor_risk_ranking"][0]["rank"] == 1
    assert "Stress Lab" in block["factor_exposure_summary"]["diagnostic_interpretation"]


def test_block_2_3_missing_factor_betas_5y_degrades_without_recompute(monkeypatch: pytest.MonkeyPatch) -> None:
    import src.stress_factors as stress_factors

    def _forbidden(*args, **kwargs):  # pragma: no cover - should never be called
        raise AssertionError("Block 2.3 must not trigger factor calculations")

    monkeypatch.setattr(stress_factors, "portfolio_factor_regression_weekly", _forbidden)
    monkeypatch.setattr(stress_factors, "factor_variance_decomposition_weekly", _forbidden)
    monkeypatch.setattr(stress_factors, "compute_portfolio_kalman_factor_betas_weekly", _forbidden)

    stress = _stress_report()
    del stress["factor_betas_5y"]
    block = build_block_2_3_factor_exposure(stress_report=stress, analysis_setup=_analysis_setup())

    assert_block_2_3_product_contract(block)
    assert block["status"] == "partial"
    assert block["factor_betas_5y"]["status"] == "unavailable"
    assert any("factor_betas_5y missing" in warning for warning in block["data_quality_warnings"])


def test_block_2_3_kalman_error_maps_to_precise_unavailable_reason() -> None:
    stress = _stress_report()
    stress.pop("factor_betas_kalman", None)
    stress["factor_betas_kalman_error"] = "Length mismatch: Expected axis has 2 elements, new values have 1 elements"
    block = build_block_2_3_factor_exposure(stress_report=stress, analysis_setup=_analysis_setup())

    kalman = block["kalman_current_beta"]
    assert kalman["available"] is False
    assert kalman["reason"] == "kalman_computation_failed"
    assert any("Length mismatch" in note for note in kalman["notes"])
    assert not any("Kalman current beta unavailable" in w for w in block["data_quality_warnings"])
    assert any("Kalman current beta unavailable" in d for d in block["informational_disclosures"])


def test_block_2_3_unavailable_when_stress_report_missing() -> None:
    block = build_block_2_3_factor_exposure(stress_report=None, analysis_setup=None, weights={})

    assert_block_2_3_product_contract(block)
    assert block["status"] == "unavailable"
    assert block["factor_variance_contribution"]["status"] == "unavailable"
    assert block["kalman_current_beta"]["available"] is False
    assert block["factor_exposure_summary"]["dominant_factor"] is None


def test_block_2_3_naming_validation_warns_on_extra_and_internal_factor_names() -> None:
    stress = _stress_report()
    stress["factor_betas_5y"]["beta_oil"] = 0.99
    block = build_block_2_3_factor_exposure(stress_report=stress, analysis_setup=_analysis_setup())

    warnings = block["naming_validation"]["warnings"]
    assert block["naming_validation"]["status"] == "warnings"
    assert any("beta_oil" in warning for warning in warnings)
    assert any("vix->VIX_volatility" in warning for warning in warnings)


def test_block_2_3_real_cash_warning_and_no_cash_proxy_substitution() -> None:
    block = build_block_2_3_factor_exposure(
        stress_report=_stress_report(),
        analysis_setup=_analysis_setup(),
        weights={"VOO": 0.9, "Cash USD": 0.1},
    )

    assert any("real cash" in note.lower() for note in block["informational_disclosures"])
    assert block["factor_diagnostics_meta"]["cash_handling"] == "real_cash_has_zero_return_and_no_price_series"
    assert "BIL" not in block["factor_beta_snapshot"]


def test_portfolio_xray_contains_block_2_3_alongside_2_1_and_2_2() -> None:
    xray = build_portfolio_xray_v2(
        analysis_setup=_analysis_setup(),
        weights={"VOO": 0.5, "BND": 0.4, "Cash USD": 0.1},
        rc_asset=[],
        stress_report=_stress_report(),
        portfolio_valid=True,
        portfolio_metrics={"window_months": 120, "cagr": 0.08, "vol_annual": 0.1},
    )

    assert "block_2_1_asset_allocation" in xray
    assert "block_2_2_portfolio_metrics" in xray
    assert "block_2_3_factor_exposure" in xray
    assert_block_2_3_product_contract(xray["block_2_3_factor_exposure"])
    assert "factor_exposure" in xray["sections"]
