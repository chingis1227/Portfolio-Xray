from __future__ import annotations

import copy
from typing import Any

import pytest

from src.block_2_6_portfolio_weakness_map import (
    BLOCK_2_6_ID,
    BLOCK_2_6_NAME,
    EVIDENCE_DIRECTIONS,
    EVIDENCE_SOURCES,
    LEGACY_RISK_ALIASES,
    RISK_TYPES,
    RISK_RULE_TABLES,
    RULE_VERSION,
    build_block_2_6_portfolio_weakness_map,
)
from src.scenario_library import SYNTHETIC_SCENARIO_IDS

BLOCK_2_6_TOP_LEVEL_KEYS = frozenset(
    {
        "block",
        "block_id",
        "block_name",
        "status",
        "summary",
        "data_quality_warnings",
        "metadata",
        "risk_types",
        "next_tests_global",
    }
)

BLOCK_2_6_STATUS_VALUES = frozenset({"ok", "partial", "unavailable"})

RISK_ROW_REQUIRED_KEYS = frozenset(
    {
        "risk_type",
        "risk_title",
        "score_0_100",
        "severity",
        "confidence",
        "evidence",
        "short_diagnosis",
        "why_status",
        "key_evidence",
        "linked_assets",
        "data_quality_warnings",
        "confidence_reason",
        "why_it_matters",
        "next_tests",
        "limitations",
        "explanation",
    }
)

GENERIC_NARRATIVE_BOILERPLATE = (
    "This score is a pre-stress heuristic based on already-computed portfolio diagnostics."
)

# Minimum evidence metric ids per canonical risk (Session 08 matrix).
RISK_EVIDENCE_METRICS: dict[str, tuple[str, ...]] = {
    "equity_shock": (
        "equity_weight",
        "risk_on_weight",
        "downside_beta",
        "beta_portfolio",
        "beta_eq",
    ),
    "credit_shock": (
        "credit_liquidity_weight",
        "credit_rc_pct",
        "beta_credit",
        "credit_liquidity_risk_score",
    ),
    "rates_shock": (
        "rates_duration_weight",
        "beta_rr",
        "duration_concentration_score",
    ),
    "inflation_stagflation": (
        "inflation_linked_rc_pct",
        "commodity_weight",
        "beta_inf",
    ),
    "liquidity_shock": (
        "credit_rc_pct",
        "correlation_concentration_score",
        "credit_liquidity_risk_score",
        "tail_risk_score",
    ),
    "usd_shock": (
        "dominant_currency_weight",
        "beta_usd",
        "usd_factor_variance_share",
    ),
    "commodity_shock": (
        "commodity_weight",
        "commodity_rc_pct",
        "real_assets_rc_pct",
    ),
    "recession_severe": (
        "equity_rc_pct",
        "credit_rc_pct",
        "downside_beta",
        "tail_risk_score",
    ),
}


def assert_block_2_6_product_contract(block: dict[str, Any]) -> None:
    """§2.6.1 product block shape for golden and live portfolio_xray.json."""
    assert isinstance(block, dict)
    assert set(block) == BLOCK_2_6_TOP_LEVEL_KEYS
    assert block["block"] == BLOCK_2_6_ID
    assert block["block_id"] == "2.6"
    assert block["block_name"] == BLOCK_2_6_NAME
    assert block["status"] in BLOCK_2_6_STATUS_VALUES
    assert isinstance(block["summary"], str) and block["summary"]
    assert isinstance(block["data_quality_warnings"], list)
    assert isinstance(block["next_tests_global"], list)

    metadata = block["metadata"]
    assert isinstance(metadata, dict)
    assert metadata["rule_version"] == RULE_VERSION
    assert metadata["stress_lab_separation"] == "no_stress_pnl_or_attribution"
    assert metadata.get("legacy_risk_aliases") == LEGACY_RISK_ALIASES
    diagnostics_meta = metadata.get("diagnostics_meta") or {}
    assert diagnostics_meta.get("ruleset") == RULE_VERSION
    assert isinstance(diagnostics_meta.get("blocked_upstream_fields"), list)

    assert len(block["risk_types"]) == len(RISK_TYPES)
    assert tuple(r["risk_type"] for r in block["risk_types"]) == RISK_TYPES

    for risk in block["risk_types"]:
        assert RISK_ROW_REQUIRED_KEYS <= set(risk)
        assert risk["risk_type"] in SYNTHETIC_SCENARIO_IDS
        assert risk["severity"] in {"Low", "Medium", "High", "Unavailable"}
        assert risk["confidence"] in {"high", "medium", "low", "unavailable"}
        assert risk["explanation"] == risk["short_diagnosis"]
        assert isinstance(risk["short_diagnosis"], str) and risk["short_diagnosis"]
        assert isinstance(risk["why_status"], str) and risk["why_status"]
        assert isinstance(risk["key_evidence"], list) and 3 <= len(risk["key_evidence"]) <= 5
        assert all(isinstance(x, str) and x for x in risk["key_evidence"])
        assert isinstance(risk["linked_assets"], list)
        assert isinstance(risk["next_tests"], list) and risk["next_tests"]
        assert risk["risk_type"] in risk["next_tests"]
        assert GENERIC_NARRATIVE_BOILERPLATE not in risk["short_diagnosis"]
        assert GENERIC_NARRATIVE_BOILERPLATE not in risk["why_status"]
        for item in risk["evidence"]:
            _assert_evidence_schema(item)


def _block_2_1() -> dict:
    return {
        "block": "2.1_asset_allocation",
        "capital_allocation_breakdown": {
            "by_asset_class": [
                {"name": "equity", "weight_pct": 55.0},
                {"name": "fixed_income", "weight_pct": 35.0},
                {"name": "commodity", "weight_pct": 5.0},
                {"name": "real_assets", "weight_pct": 5.0},
            ],
            "by_main_risk_factor": [
                {"name": "equity", "weight_pct": 55.0},
                {"name": "real_rates", "weight_pct": 25.0},
                {"name": "credit", "weight_pct": 10.0},
                {"name": "liquidity", "weight_pct": 5.0},
            ],
        },
    }


def _block_2_2() -> dict:
    return {"block": "2.2_portfolio_metrics", "benchmark_dependence": {"downside_beta": 1.05}}


def _block_2_3() -> dict:
    return {"block": "2.3_factor_exposure", "factor_beta_snapshot": {"beta_rr": 0.35}}


def _block_2_4() -> dict:
    return {
        "block": "2.4_hidden_exposure",
        "alerts": {
            "hidden_equity_beta": {
                "status": "High",
                "score": 70,
                "confidence": "high",
                "confidence_reason": "test",
                "limitations": ["test limitation"],
                "contributing_assets": [{"ticker": "SPY", "weight_pct": 55.0}],
                "next_tests": ["equity_shock"],
            },
            "duration_concentration": {"status": "Medium", "score": 55, "confidence": "medium", "limitations": []},
            "credit_liquidity_risk": {"status": "Medium", "score": 60, "confidence": "medium", "limitations": []},
            "correlation_concentration": {"status": "Low", "score": 45, "confidence": "low", "limitations": []},
            "tail_risk": {"status": "Medium", "score": 65, "confidence": "medium", "limitations": []},
        },
    }


def _block_2_5() -> dict:
    return {
        "block": "2.5_risk_budget_view",
        "top1_rc_asset": {"risk_contribution_pct": 0.30},
        "risk_budget_bucket_contribution": [
            {"bucket": "equity", "risk_contribution_pct": 0.55},
            {"bucket": "credit", "risk_contribution_pct": 0.20},
            {"bucket": "commodity", "risk_contribution_pct": 0.05},
            {"bucket": "real_assets", "risk_contribution_pct": 0.05},
            {"bucket": "inflation_linked", "risk_contribution_pct": 0.05},
        ],
    }


def _assert_evidence_schema(item: dict) -> None:
    assert set(item) == {"metric", "value", "threshold_key", "direction", "source", "interpretation"}
    assert item["direction"] in EVIDENCE_DIRECTIONS
    assert item["source"] in EVIDENCE_SOURCES
    assert isinstance(item["metric"], str) and item["metric"]
    assert isinstance(item["interpretation"], str) and item["interpretation"]


def test_block_2_6_contract_shape_and_risk_narrative_v2() -> None:
    block = build_block_2_6_portfolio_weakness_map(
        _block_2_1(),
        _block_2_2(),
        _block_2_3(),
        _block_2_4(),
        _block_2_5(),
        thresholds={"top1_rc_moderate": 0.25, "top1_rc_high": 0.35},
    )

    assert_block_2_6_product_contract(block)

    equity = next(r for r in block["risk_types"] if r["risk_type"] == "equity_shock")
    assert equity["linked_assets"] and equity["linked_assets"][0].get("ticker") == "SPY"


@pytest.mark.parametrize("risk_type", RISK_TYPES)
def test_block_2_6_per_risk_evidence_surface(risk_type: str) -> None:
    block = build_block_2_6_portfolio_weakness_map(
        _block_2_1(),
        _block_2_2(),
        _block_2_3(),
        _block_2_4(),
        _block_2_5(),
    )
    risk = next(r for r in block["risk_types"] if r["risk_type"] == risk_type)
    metrics = {row["metric"] for row in risk["evidence"]}
    for expected in RISK_EVIDENCE_METRICS[risk_type]:
        assert expected in metrics


def test_block_2_6_high_equity_fixture_scores_high() -> None:
    b21 = _block_2_1()
    b21["capital_allocation_breakdown"]["by_asset_class"] = [{"name": "equity", "weight_pct": 85.0}]
    b22 = _block_2_2()
    b22["benchmark_dependence"] = {"downside_beta": 1.35, "beta_portfolio": 1.25}
    block = build_block_2_6_portfolio_weakness_map(b21, b22, _block_2_3(), _block_2_4(), _block_2_5())
    equity = next(r for r in block["risk_types"] if r["risk_type"] == "equity_shock")
    assert equity["severity"] == "High"
    assert equity["score_0_100"] is not None and equity["score_0_100"] >= 70


def _block_2_1_usd_rich() -> dict:
    block = _block_2_1()
    block["capital_allocation_breakdown"]["by_currency"] = [
        {"name": "usd", "weight_pct": 72.0},
        {"name": "eur", "weight_pct": 28.0},
    ]
    block["investor_currency"] = "EUR"
    return block


def _block_2_3_usd_rich() -> dict:
    return {
        "block": "2.3_factor_exposure",
        "factor_beta_snapshot": {"beta_usd": 0.42, "beta_rr": 0.35},
        "factor_variance_contribution": {
            "contributions": {"USD": 0.18, "equity": 0.55},
        },
    }


def test_usd_shock_scores_when_upstream_fx_fields_present() -> None:
    block = build_block_2_6_portfolio_weakness_map(
        _block_2_1_usd_rich(),
        {**_block_2_2(), "investor_currency": "EUR"},
        _block_2_3_usd_rich(),
        _block_2_4(),
        _block_2_5(),
    )
    usd_risk = next(r for r in block["risk_types"] if r["risk_type"] == "usd_shock")
    assert usd_risk["severity"] in {"Low", "Medium", "High"}
    assert usd_risk["score_0_100"] is not None
    blocked = block["metadata"]["diagnostics_meta"]["blocked_upstream_fields"]
    blocked_fields = {row["field"] for row in blocked if isinstance(row, dict)}
    assert "block_2_3.factor_beta_snapshot.beta_usd" not in blocked_fields


def test_block_2_6_missing_data_is_unavailable() -> None:
    block = build_block_2_6_portfolio_weakness_map(None, None, None, None, None)
    assert block["status"] == "unavailable"
    assert len(block["risk_types"]) == 8
    for risk in block["risk_types"]:
        assert risk["severity"] == "Unavailable"
        assert risk["score_0_100"] is None
        assert risk["confidence"] == "unavailable"
        assert risk["limitations"]


def test_block_2_6_does_not_mutate_inputs() -> None:
    b21, b22, b23, b24, b25 = _block_2_1(), _block_2_2(), _block_2_3(), _block_2_4(), _block_2_5()
    before = (copy.deepcopy(b21), copy.deepcopy(b22), copy.deepcopy(b23), copy.deepcopy(b24), copy.deepcopy(b25))

    build_block_2_6_portfolio_weakness_map(b21, b22, b23, b24, b25)

    assert (b21, b22, b23, b24, b25) == before


def test_block_2_6_warns_on_forbidden_stress_keys_in_inputs() -> None:
    b24 = _block_2_4()
    b24["stress_report"] = {"scenario_results": [{"scenario": "equity_shock"}]}

    block = build_block_2_6_portfolio_weakness_map(_block_2_1(), _block_2_2(), _block_2_3(), b24, _block_2_5())

    warnings = " ".join(block.get("data_quality_warnings") or [])
    assert "stress boundary warning" in warnings
    assert set(block["metadata"]["forbidden_stress_keys_detected"]) >= {"stress_report", "scenario_results"}


def test_block_2_6_rule_tables_cover_all_risks_and_sum_weights() -> None:
    assert set(RISK_RULE_TABLES) >= set(RISK_TYPES)
    for risk_type in RISK_TYPES:
        table = RISK_RULE_TABLES[risk_type]
        signals = table.get("signals") or []
        total = sum(float(s["weight"]) for s in signals) if signals else 0.0
        if signals:
            assert abs(total - 1.0) < 1e-9


def test_usd_shock_unavailable_exposes_blocked_upstream_fields() -> None:
    block = build_block_2_6_portfolio_weakness_map(
        _block_2_1(),
        _block_2_2(),
        _block_2_3(),
        _block_2_4(),
        _block_2_5(),
    )

    usd_risk = next(r for r in block["risk_types"] if r["risk_type"] == "usd_shock")
    assert usd_risk["severity"] == "Unavailable"
    assert usd_risk["score_0_100"] is None
    assert usd_risk["limitations"]

    blocked = block["metadata"]["diagnostics_meta"]["blocked_upstream_fields"]
    assert isinstance(blocked, list) and blocked
    blocked_fields = {row["field"] for row in blocked if isinstance(row, dict)}
    assert "block_2_3.factor_beta_snapshot.beta_usd" in blocked_fields
    assert "block_2_3.factor_variance_contribution.contributions.USD" in blocked_fields

