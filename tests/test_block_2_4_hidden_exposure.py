from __future__ import annotations

import copy

from src.block_2_4_hidden_exposure import (
    ALERT_IDS,
    BLOCK_2_4_ID,
    EVIDENCE_DIRECTIONS,
    EVIDENCE_SOURCES,
    build_block_2_4_hidden_exposure,
)
from src.portfolio_xray import build_portfolio_xray_v2


def _block_2_1() -> dict:
    return {
        "block": "2.1_asset_allocation",
        "capital_allocation_breakdown": {
            "by_asset_class": [
                {"name": "equity", "weight_pct": 45.0},
                {"name": "fixed_income", "weight_pct": 40.0},
            ],
            "by_main_risk_factor": [
                {"name": "equity", "weight_pct": 45.0},
                {"name": "real_rates", "weight_pct": 40.0},
            ],
            "by_risk_role": [
                {"name": "risk_on", "weight_pct": 45.0},
                {"name": "defensive", "weight_pct": 40.0},
            ],
        },
        "duplicate_exposure_flags": [{"observed": 0.12}],
    }


def _block_2_2() -> dict:
    return {
        "block": "2.2_portfolio_metrics",
        "return_risk_metrics": {"skewness": -0.7, "kurtosis": 5.0},
        "drawdown_diagnostics": {
            "count_drawdowns_gt_10": 2,
            "count_drawdowns_gt_20": 1,
            "pct_time_underwater": 0.35,
        },
        "tail_risk_diagnostics": {"es_95": -0.02, "es_99": -0.03, "eee_10": -0.035},
        "benchmark_dependence": {
            "beta_portfolio": 0.8,
            "downside_beta": 1.0,
            "corr_base": 0.78,
        },
        "rolling_diagnostics": {
            "core_view": {
                "rolling_beta_or_correlation": {
                    "available": True,
                    "latest_correlation": 0.78,
                }
            }
        },
        "correlation_breakdown": {
            "top3_highest_correlation_pairs": [
                {"ticker_a": "SPY", "ticker_b": "SCHD", "correlation": 0.82}
            ]
        },
    }


def _block_2_3() -> dict:
    return {
        "block": "2.3_factor_exposure",
        "factor_beta_snapshot": {
            "beta_eq": 0.5,
            "beta_rr": 0.4,
            "beta_credit": 0.35,
        },
        "factor_significance_confidence": {
            "beta_eq": {"status": "significant"},
            "beta_rr": {"status": "weak_evidence"},
            "beta_credit": {"status": "weak_evidence"},
        },
    }


def _assert_evidence_schema(item: dict) -> None:
    assert set(item) == {"metric", "value", "threshold", "direction", "source", "interpretation"}
    assert item["direction"] in EVIDENCE_DIRECTIONS
    assert item["source"] in EVIDENCE_SOURCES
    assert isinstance(item["metric"], str) and item["metric"]
    assert isinstance(item["interpretation"], str) and item["interpretation"]


def test_block_2_4_contract_and_structured_evidence() -> None:
    block = build_block_2_4_hidden_exposure(_block_2_1(), _block_2_2(), _block_2_3())

    assert block["block"] == BLOCK_2_4_ID
    assert block["status"] in {"ok", "partial", "unavailable"}
    assert tuple(block["alerts"]) == ALERT_IDS
    assert block["diagnostics_meta"]["threshold_policy"] == "heuristic_v1"
    assert block["diagnostics_meta"]["does_not_optimize"] is True
    assert block["diagnostics_meta"]["does_not_generate_candidates"] is True
    assert block["diagnostics_meta"]["does_not_run_stress_lab"] is True

    for alert in block["alerts"].values():
        assert {
            "status",
            "score",
            "evidence",
            "explanation",
            "why_it_matters",
            "next_tests",
            "confidence",
            "data_quality_warnings",
            "insufficient_evidence_reasons",
            "calculation_notes",
        } <= set(alert)
        assert alert["status"] in {"Low", "Medium", "High", "Unavailable"}
        for item in alert["evidence"]:
            _assert_evidence_schema(item)


def test_block_2_4_missing_data_returns_unavailable_or_low_confidence() -> None:
    block = build_block_2_4_hidden_exposure(None, None, None)

    assert block["status"] == "unavailable"
    for alert in block["alerts"].values():
        assert alert["status"] == "Unavailable"
        assert alert["score"] is None
        assert alert["confidence"] == "unavailable"
        assert alert["insufficient_evidence_reasons"]


def test_block_2_4_status_boundaries() -> None:
    low = build_block_2_4_hidden_exposure(
        _block_2_1(),
        {
            **_block_2_2(),
            "benchmark_dependence": {"beta_portfolio": 0.0, "downside_beta": 0.0},
            "rolling_diagnostics": {"core_view": {"rolling_beta_or_correlation": {"latest_correlation": 0.0}}},
        },
        {"factor_beta_snapshot": {"beta_eq": 0.0}, "factor_significance_confidence": {}},
    )["alerts"]["hidden_equity_beta"]
    assert low["status"] == "Low"
    assert 0 <= low["score"] <= 39

    medium = build_block_2_4_hidden_exposure(
        _block_2_1(),
        {
            **_block_2_2(),
            "benchmark_dependence": {"beta_portfolio": 0.70, "downside_beta": 0.90},
            "rolling_diagnostics": {"core_view": {"rolling_beta_or_correlation": {"latest_correlation": 0.70}}},
        },
        {"factor_beta_snapshot": {"beta_eq": 0.35}, "factor_significance_confidence": {}},
    )["alerts"]["hidden_equity_beta"]
    assert medium["status"] == "Medium"
    assert 40 <= medium["score"] <= 69

    high = build_block_2_4_hidden_exposure(
        _block_2_1(),
        {
            **_block_2_2(),
            "benchmark_dependence": {"beta_portfolio": 1.0, "downside_beta": 1.2},
            "rolling_diagnostics": {"core_view": {"rolling_beta_or_correlation": {"latest_correlation": 0.85}}},
        },
        {"factor_beta_snapshot": {"beta_eq": 0.65}, "factor_significance_confidence": {}},
    )["alerts"]["hidden_equity_beta"]
    assert high["status"] == "High"
    assert 70 <= high["score"] <= 100


def test_block_2_4_weak_hedge_is_preliminary_without_stress_lab() -> None:
    alert = build_block_2_4_hidden_exposure(_block_2_1(), _block_2_2(), _block_2_3())["alerts"][
        "weak_hedge_behavior"
    ]

    assert "preliminary_without_stress_lab" in alert["data_quality_warnings"]
    assert any("does not claim actual hedge failure" in note for note in alert["calculation_notes"])
    assert "equity_shock" in alert["next_tests"]


def test_block_2_4_does_not_mutate_input_blocks() -> None:
    block_21 = _block_2_1()
    block_22 = _block_2_2()
    block_23 = _block_2_3()
    before = (copy.deepcopy(block_21), copy.deepcopy(block_22), copy.deepcopy(block_23))

    build_block_2_4_hidden_exposure(block_21, block_22, block_23)

    assert (block_21, block_22, block_23) == before


def test_portfolio_xray_v2_includes_block_2_4_without_removing_legacy_section() -> None:
    xray = build_portfolio_xray_v2(
        analysis_setup={"analysis_portfolio": {"portfolio_role": "test"}},
        weights={"SPY": 0.6, "BND": 0.4},
        rc_asset=[],
        stress_report={"factor_betas_5y": {"beta_eq": 0.4, "beta_rr": 0.3}},
        portfolio_valid=True,
        portfolio_metrics={"beta_portfolio": 0.8, "downside_beta": 1.0},
        taxonomy_rows={
            "SPY": {"asset_class": "equity", "main_risk_factor": "equity", "risk_role": ["risk_on"]},
            "BND": {
                "asset_class": "fixed_income",
                "main_risk_factor": "real_rates",
                "risk_role": ["defensive"],
            },
        },
    )

    assert xray["block_2_4_hidden_exposure"]["block"] == BLOCK_2_4_ID
    assert tuple(xray["block_2_4_hidden_exposure"]["alerts"]) == ALERT_IDS
    assert "hidden_risk_detector" in xray["sections"]
    assert xray["block_2_1_asset_allocation"]["block"] == "2.1_asset_allocation"
    assert xray["block_2_2_portfolio_metrics"]["block"] == "2.2_portfolio_metrics"
    assert xray["block_2_3_factor_exposure"]["block"] == "2.3_factor_exposure"
