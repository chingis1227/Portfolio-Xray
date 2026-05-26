from __future__ import annotations

import copy

from src.block_2_6_portfolio_weakness_map import (
    EVIDENCE_DIRECTIONS,
    EVIDENCE_SOURCES,
    RISK_TYPES,
    RISK_RULE_TABLES,
    build_block_2_6_portfolio_weakness_map,
)


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
            "hidden_equity_beta": {"score": 70},
            "duration_concentration": {"score": 55},
            "credit_liquidity_risk": {"score": 60},
            "correlation_concentration": {"score": 45},
            "tail_risk": {"score": 65},
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


def test_block_2_6_contract_shape_and_nine_risks() -> None:
    block = build_block_2_6_portfolio_weakness_map(
        _block_2_1(),
        _block_2_2(),
        _block_2_3(),
        _block_2_4(),
        _block_2_5(),
        thresholds={"top1_rc_moderate": 0.25, "top1_rc_high": 0.35},
    )

    assert block["block"] == "2.6_portfolio_weakness_map"
    assert block["block_id"] == "2.6"
    assert block["status"] in {"ok", "partial", "unavailable"}
    assert tuple(r["risk_type"] for r in block["risk_types"]) == RISK_TYPES
    assert isinstance(block["next_tests_global"], list) and block["next_tests_global"]

    for risk in block["risk_types"]:
        assert {
            "risk_type",
            "risk_title",
            "score_0_100",
            "severity",
            "confidence",
            "evidence",
            "explanation",
            "why_it_matters",
            "next_tests",
            "limitations",
        } <= set(risk)
        assert risk["risk_type"] in RISK_TYPES
        assert risk["severity"] in {"Low", "Medium", "High", "Unavailable"}
        assert risk["confidence"] in {"high", "medium", "low", "unavailable"}
        for item in risk["evidence"]:
            _assert_evidence_schema(item)


def test_block_2_6_missing_data_is_unavailable() -> None:
    block = build_block_2_6_portfolio_weakness_map(None, None, None, None, None)
    assert block["status"] == "unavailable"
    assert len(block["risk_types"]) == 9
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

