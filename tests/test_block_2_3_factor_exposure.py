from __future__ import annotations

from typing import Any

import pytest

from src.block_2_3_factor_exposure import (
    BLOCK_2_3_ID,
    FACTOR_BETAS_3Y_UNAVAILABLE_REASON,
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
        "factor_betas_3y": _full_beta_map(0.18),
        "factor_betas_5y": _full_beta_map(0.2),
        "factor_betas_10y": _full_beta_map(0.15),
        "factor_regression_3y": _regression_block(n_obs=150, p_value=0.05),
        "factor_regression_5y": _regression_block(n_obs=250, p_value=0.04),
        "factor_regression_10y": _regression_block(n_obs=480, p_value=0.08),
        "factor_betas_kalman": {
            "status": "available",
            "method": "kalman_random_walk_weekly_factor_betas",
            "latest": _full_beta_map(0.22),
            "latest_date": "2026-05-22",
            "uncertainty_by_beta": {
                key: ("low" if key == "beta_eq" else "moderate" if key == "beta_credit" else "high")
                for key in PRODUCTION_BETA_KEYS
            },
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


BLOCK_2_3_CORE_MVP_TOP_LEVEL_KEYS = (
    "factor_betas_3y",
    "factor_betas_5y",
    "factor_betas_10y",
    "kalman_current_beta",
    "factor_kalman_uncertainty",
    "factor_beta_stability",
    "factor_signal_confidence",
    "factor_significance_confidence",
    "factor_variance_contribution",
    "factor_risk_ranking",
    "factor_exposure_summary",
)

_BANNED_REGRESSION_STAT_KEYS = frozenset(
    {
        "t_stat",
        "p_value",
        "hac_inference",
        "factor_multicollinearity",
        "serial_correlation_diagnostics",
        "breusch_godfrey",
        "breusch_pagan",
        "durbin_watson",
        "vif",
        "cond",
        "ci_low",
        "ci_high",
        "adj_r2",
        "r2",
    }
)


def _collect_dict_keys(obj: Any, *, prefix: str = "") -> set[str]:
    found: set[str] = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            found.add(path)
            found.update(_collect_dict_keys(value, prefix=path))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            found.update(_collect_dict_keys(item, prefix=f"{prefix}[{idx}]"))
    return found


def assert_block_2_3_no_raw_regression_statistics(block: dict) -> None:
    keys = _collect_dict_keys(block)
    leaks = sorted(
        path
        for path in keys
        if any(
            banned in path.split(".") or path.endswith(f".{banned}") or path == banned
            for banned in _BANNED_REGRESSION_STAT_KEYS
        )
    )
    assert not leaks, f"raw regression statistics leaked into Block 2.3 product output: {leaks}"


def assert_block_2_3_product_contract(block: dict) -> None:
    assert block["block"] == BLOCK_2_3_ID
    assert block["block_id"] == "2.3"
    assert block["block_name"] == "Factor Exposure / Factor Sensitivity"
    assert block["status"] in {"available", "partial", "unavailable"}
    assert block["factor_universe"] == list(PRODUCTION_FACTOR_UNIVERSE)
    for key in (
        "factor_beta_snapshot",
        *BLOCK_2_3_CORE_MVP_TOP_LEVEL_KEYS,
        "data_quality_warnings",
        "informational_disclosures",
        "factor_diagnostics_meta",
        "naming_validation",
        "stress_lab_separation",
    ):
        assert key in block
    assert set(block["factor_beta_snapshot"]) == set(PRODUCTION_BETA_KEYS)
    assert set(block["factor_betas_3y"]["betas"]) == set(PRODUCTION_BETA_KEYS)
    assert set(block["factor_betas_5y"]["betas"]) == set(PRODUCTION_BETA_KEYS)
    assert set(block["factor_betas_10y"]["betas"]) == set(PRODUCTION_BETA_KEYS)
    assert set(block["kalman_current_beta"]["betas"]) == set(PRODUCTION_BETA_KEYS)
    assert set(block["factor_kalman_uncertainty"]) == set(PRODUCTION_BETA_KEYS)
    assert set(block["factor_beta_stability"]) == set(PRODUCTION_BETA_KEYS)
    assert set(block["factor_signal_confidence"]) == set(PRODUCTION_BETA_KEYS)
    assert set(block["factor_significance_confidence"]) == set(PRODUCTION_BETA_KEYS)
    for beta_key in PRODUCTION_BETA_KEYS:
        kalman_row = block["factor_kalman_uncertainty"][beta_key]
        assert set(kalman_row) == {"kalman_uncertainty_label", "kalman_note", "unavailable_reason"}
        assert "signal_confidence" not in kalman_row
        stability_row = block["factor_beta_stability"][beta_key]
        assert set(stability_row) == {"beta_stability_label", "unavailable_reason", "windows_available"}
        assert stability_row["beta_stability_label"] in {
            "stable",
            "moderately_changed",
            "unstable",
            "unavailable",
        }
        row = block["factor_signal_confidence"][beta_key]
        assert set(row) == {"signal_confidence", "confidence_reason", "inference_source", "regression_window"}
        assert "kalman_uncertainty_label" not in row
        assert "t_stat" not in row
        assert "p_value" not in row
        legacy = block["factor_significance_confidence"][beta_key]
        assert legacy.get("status") == row.get("signal_confidence")
        assert legacy.get("confidence_reason") == row.get("confidence_reason")
        assert "t_stat" not in legacy
        assert "p_value" not in legacy
    assert len(block["factor_risk_ranking"]) <= 3
    summary = block["factor_exposure_summary"]
    assert "factor_highlights" in summary
    assert "main_caveat" in summary
    assert isinstance(summary["factor_highlights"], list)
    assert block["stress_lab_separation"]["no_scenario_shocks_in_this_block"] is True
    assert block["stress_lab_separation"]["no_rebalance_recommendations"] is True
    meta_notes = block["factor_diagnostics_meta"].get("method_notes") or []
    assert any("adapt" in str(note).lower() for note in meta_notes)
    assert any("stress_report" in str(note) for note in meta_notes)
    assert_block_2_3_no_raw_regression_statistics(block)


def test_block_2_3_available_contract_from_stress_report() -> None:
    block = build_block_2_3_factor_exposure(
        stress_report=_stress_report(),
        analysis_setup=_analysis_setup(),
        weights={"VOO": 0.5, "BND": 0.4, "Cash USD": 0.1},
    )

    assert_block_2_3_product_contract(block)
    assert block["status"] == "available"
    assert block["factor_betas_3y"]["status"] == "available"
    assert block["factor_betas_5y"]["status"] == "available"
    assert block["factor_betas_10y"]["status"] == "available"
    assert block["factor_betas_3y"]["window_months"] == 36
    assert block["factor_betas_3y"]["observations_used"] == 150
    assert block["kalman_current_beta"]["available"] is True
    eq_kalman = block["factor_kalman_uncertainty"]["beta_eq"]
    assert eq_kalman["kalman_uncertainty_label"] == "low"
    assert "relatively stable" in eq_kalman["kalman_note"]
    assert eq_kalman["unavailable_reason"] is None
    credit_kalman = block["factor_kalman_uncertainty"]["beta_credit"]
    assert credit_kalman["kalman_uncertainty_label"] == "moderate"
    assert "5Y/10Y" in credit_kalman["kalman_note"]
    eq_signal = block["factor_signal_confidence"]["beta_eq"]
    assert eq_signal["signal_confidence"] == "significant"
    assert eq_signal["inference_source"] == "hac_newey_west"
    assert "HAC p-value below 0.05" in eq_signal["confidence_reason"]
    assert block["factor_significance_confidence"]["beta_eq"]["status"] == "significant"
    assert block["factor_variance_contribution"]["status"] == "available"
    assert block["factor_risk_ranking"][0]["rank"] == 1
    assert block["factor_beta_stability"]["beta_eq"]["beta_stability_label"] == "stable"
    summary = block["factor_exposure_summary"]
    assert "equity" in summary["client_summary"].lower()
    assert summary["factor_highlights"]
    assert summary["factor_highlights"][0]["signal_confidence"] == "significant"
    assert "statistically significant" in summary["client_summary"]
    assert "Stress Lab" in summary["diagnostic_interpretation"]


def test_block_2_3_signal_confidence_prefers_hac_over_ols() -> None:
    stress = _stress_report()
    reg = stress["factor_regression_5y"]
    reg["p"]["beta_eq"] = 0.20
    reg["hac_inference"]["p"][1] = 0.03
    block = build_block_2_3_factor_exposure(stress_report=stress, analysis_setup=_analysis_setup())
    eq = block["factor_signal_confidence"]["beta_eq"]
    assert eq["signal_confidence"] == "significant"
    assert eq["inference_source"] == "hac_newey_west"


def test_block_2_3_signal_confidence_ols_fallback_when_hac_missing() -> None:
    stress = _stress_report()
    reg = stress["factor_regression_5y"]
    reg.pop("hac_inference", None)
    reg["p"]["beta_eq"] = 0.04
    reg["t"]["beta_eq"] = 2.1
    block = build_block_2_3_factor_exposure(stress_report=stress, analysis_setup=_analysis_setup())
    eq = block["factor_signal_confidence"]["beta_eq"]
    assert eq["signal_confidence"] == "significant"
    assert eq["inference_source"] == "ols_classic"
    assert "OLS p-value below 0.05" in eq["confidence_reason"]


def test_block_2_3_signal_confidence_weak_when_p_between_thresholds() -> None:
    stress = _stress_report()
    reg = stress["factor_regression_5y"]
    reg["hac_inference"]["p"][1] = 0.10
    block = build_block_2_3_factor_exposure(stress_report=stress, analysis_setup=_analysis_setup())
    eq = block["factor_signal_confidence"]["beta_eq"]
    assert eq["signal_confidence"] == "weak_evidence"
    assert "above the strong-significance threshold" in eq["confidence_reason"]


def test_block_2_3_signal_confidence_unavailable_when_beta_missing() -> None:
    stress = _stress_report()
    stress["factor_betas_5y"]["beta_eq"] = None
    del stress["factor_betas_5y"]["beta_eq"]
    stress["factor_betas_5y"].pop("beta_eq", None)
    block = build_block_2_3_factor_exposure(stress_report=stress, analysis_setup=_analysis_setup())
    row = block["factor_signal_confidence"]["beta_eq"]
    assert row["signal_confidence"] == "unavailable"
    assert "missing" in row["confidence_reason"].lower()


def test_block_2_3_missing_factor_betas_3y_marks_window_unavailable_with_reason() -> None:
    stress = _stress_report()
    del stress["factor_betas_3y"]
    block = build_block_2_3_factor_exposure(stress_report=stress, analysis_setup=_analysis_setup())

    assert_block_2_3_product_contract(block)
    assert block["factor_betas_3y"]["status"] == "unavailable"
    assert block["factor_betas_3y"]["unavailable_reason"] == FACTOR_BETAS_3Y_UNAVAILABLE_REASON
    assert any(FACTOR_BETAS_3Y_UNAVAILABLE_REASON in warning for warning in block["data_quality_warnings"])
    assert block["factor_betas_5y"]["status"] == "available"
    assert block["factor_betas_10y"]["status"] == "available"


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


def test_block_2_3_product_summary_notes_kalman_divergence_and_caveat() -> None:
    stress = _stress_report()
    stress["factor_betas_kalman"]["latest"]["beta_eq"] = -0.35
    stress["factor_betas_kalman"]["uncertainty_by_beta"]["beta_eq"] = "high"
    block = build_block_2_3_factor_exposure(stress_report=stress, analysis_setup=_analysis_setup())
    summary = block["factor_exposure_summary"]
    eq_highlight = next(row for row in summary["factor_highlights"] if row["factor"] == "equity")
    assert eq_highlight["kalman_alignment"] == "differs_from_5y_10y"
    assert "differs from the 5Y/10Y" in summary["client_summary"]
    assert summary["main_caveat"] is not None
    assert "Kalman uncertainty is high" in summary["main_caveat"]


def test_block_2_3_product_summary_mentions_weak_signal_for_top_factor() -> None:
    stress = _stress_report()
    reg = stress["factor_regression_5y"]
    reg["hac_inference"]["p"][1] = 0.12
    block = build_block_2_3_factor_exposure(stress_report=stress, analysis_setup=_analysis_setup())
    summary = block["factor_exposure_summary"]
    eq_highlight = next(row for row in summary["factor_highlights"] if row["factor"] == "equity")
    assert eq_highlight["signal_confidence"] == "weak_evidence"
    assert "statistically weak" in summary["client_summary"]


def test_block_2_3_beta_stability_sign_flip_is_unstable() -> None:
    stress = _stress_report()
    stress["factor_betas_3y"]["beta_eq"] = 0.45
    stress["factor_betas_5y"]["beta_eq"] = 0.40
    stress["factor_betas_10y"]["beta_eq"] = -0.35
    block = build_block_2_3_factor_exposure(stress_report=stress, analysis_setup=_analysis_setup())
    eq = block["factor_beta_stability"]["beta_eq"]
    assert eq["beta_stability_label"] == "unstable"
    assert eq["unavailable_reason"] is None


def test_block_2_3_beta_stability_moderate_gap() -> None:
    stress = _stress_report()
    stress["factor_betas_3y"]["beta_credit"] = 0.20
    stress["factor_betas_5y"]["beta_credit"] = 0.38
    stress["factor_betas_10y"]["beta_credit"] = 0.22
    block = build_block_2_3_factor_exposure(stress_report=stress, analysis_setup=_analysis_setup())
    credit = block["factor_beta_stability"]["beta_credit"]
    assert credit["beta_stability_label"] == "moderately_changed"


def test_block_2_3_beta_stability_unavailable_with_one_window() -> None:
    stress = _stress_report()
    for key in ("factor_betas_3y", "factor_betas_10y"):
        stress[key]["beta_rr"] = None
        stress[key].pop("beta_rr", None)
    block = build_block_2_3_factor_exposure(stress_report=stress, analysis_setup=_analysis_setup())
    rr = block["factor_beta_stability"]["beta_rr"]
    assert rr["beta_stability_label"] == "unavailable"
    assert rr["unavailable_reason"] == "insufficient_beta_windows"
    assert rr["windows_available"] == 1


def test_block_2_3_kalman_uncertainty_unknown_maps_to_unavailable_per_factor() -> None:
    stress = _stress_report()
    stress["factor_betas_kalman"]["uncertainty_by_beta"]["beta_rr"] = "unknown"
    block = build_block_2_3_factor_exposure(stress_report=stress, analysis_setup=_analysis_setup())
    rr = block["factor_kalman_uncertainty"]["beta_rr"]
    assert rr["kalman_uncertainty_label"] == "unavailable"
    assert rr["unavailable_reason"] == "kalman_uncertainty_unknown"
    assert block["factor_kalman_uncertainty"]["beta_eq"]["kalman_uncertainty_label"] == "low"


def test_block_2_3_kalman_uncertainty_does_not_change_signal_confidence() -> None:
    stress = _stress_report()
    stress["factor_betas_kalman"]["uncertainty_by_beta"] = {key: "high" for key in PRODUCTION_BETA_KEYS}
    block = build_block_2_3_factor_exposure(stress_report=stress, analysis_setup=_analysis_setup())
    assert block["factor_kalman_uncertainty"]["beta_eq"]["kalman_uncertainty_label"] == "high"
    assert "noisy" in block["factor_kalman_uncertainty"]["beta_eq"]["kalman_note"]
    assert block["factor_signal_confidence"]["beta_eq"]["signal_confidence"] == "significant"


def test_block_2_3_kalman_error_maps_to_precise_unavailable_reason() -> None:
    stress = _stress_report()
    stress.pop("factor_betas_kalman", None)
    stress["factor_betas_kalman_error"] = "Length mismatch: Expected axis has 2 elements, new values have 1 elements"
    block = build_block_2_3_factor_exposure(stress_report=stress, analysis_setup=_analysis_setup())

    kalman = block["kalman_current_beta"]
    assert kalman["available"] is False
    assert kalman["reason"] == "kalman_computation_failed"
    assert any("Length mismatch" in note for note in kalman["notes"])
    eq_unc = block["factor_kalman_uncertainty"]["beta_eq"]
    assert eq_unc["kalman_uncertainty_label"] == "unavailable"
    assert eq_unc["unavailable_reason"] == "kalman_computation_failed"
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


def test_block_2_3_core_mvp_upgrade_fields_present() -> None:
    block = build_block_2_3_factor_exposure(
        stress_report=_stress_report(),
        analysis_setup=_analysis_setup(),
    )
    for key in BLOCK_2_3_CORE_MVP_TOP_LEVEL_KEYS:
        assert key in block
    summary = block["factor_exposure_summary"]
    assert summary.get("client_summary")
    assert isinstance(summary.get("factor_highlights"), list)
    assert "main_caveat" in summary
    for beta_key in PRODUCTION_BETA_KEYS:
        kalman_row = block["factor_kalman_uncertainty"][beta_key]
        signal_row = block["factor_signal_confidence"][beta_key]
        assert "kalman_uncertainty_label" in kalman_row
        assert "signal_confidence" in signal_row
        assert "kalman_uncertainty_label" not in signal_row


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
