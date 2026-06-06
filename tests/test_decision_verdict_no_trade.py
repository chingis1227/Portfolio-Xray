from __future__ import annotations

from src.decision_verdict import build_decision_verdict_from_block7_8


def _generation() -> dict:
    return {
        "generation_status": "generated",
        "candidate": {"candidate_id": "risk_parity", "status": "generated"},
        "method_availability": {"available": True, "availability_status": "available"},
        "warnings": [],
        "handoff_to_comparison": {"can_compare": True},
    }


def _comparison(
    *,
    material: bool,
    success: str = "similar",
    turnover: float = 0.10,
) -> dict:
    return {
        "baseline": {"candidate_id": "analysis_subject"},
        "selected_candidate_ids": ["risk_parity"],
        "comparisons": [
            {
                "candidate_id": "risk_parity",
                "status": "available",
                "dimensions": [{"field": "vol_annual", "status": "available"}],
                "risk_reduced": [{"field": "vol_annual", "is_material": material}],
                "risk_added": [],
                "what_improved": [{"field": "vol_annual", "is_material": material}],
                "what_worsened": [],
                "practicality": {
                    "turnover_required": {
                        "status": "available",
                        "turnover_half_sum_pct": turnover,
                    },
                    "estimated_transaction_cost_pct": 0.0001,
                },
                "success_criteria_result": {"overall_status": success, "criteria": []},
                "materiality_for_decision_review": {
                    "status": "review_candidate" if material else "not_material",
                    "is_material_enough": material,
                    "reason": "at_least_one_material_improvement_available"
                    if material
                    else "no_material_improvement_detected",
                },
                "data_quality": {
                    "missing_fields": [],
                    "warnings": [],
                    "construction_disclosure_status": "available",
                },
            }
        ],
        "warnings": [],
    }


def test_no_material_rebalance_is_valid_no_trade_outcome() -> None:
    doc = build_decision_verdict_from_block7_8(
        candidate_generation=_generation(),
        current_vs_candidate=_comparison(material=False),
    )

    assert doc["verdict_id"] == "no_material_rebalance_recommended"
    assert doc["selection_decision_status"] == "no_material_rebalance"
    assert doc["verdict_reason_id"] == "no_material_rebalance"
    assert doc["no_trade"]["evaluated"] is True
    assert doc["no_trade"]["applies"] is True
    assert "Keep current portfolio" in doc["recommended_action"]


def test_risk_improved_but_turnover_too_high_keeps_current_portfolio() -> None:
    doc = build_decision_verdict_from_block7_8(
        candidate_generation=_generation(),
        current_vs_candidate=_comparison(material=True, success="met", turnover=0.65),
    )

    assert doc["verdict_id"] == "no_material_rebalance_recommended"
    assert doc["verdict_reason_id"] == "risk_improved_but_turnover_too_high"
    assert doc["no_trade"]["applies"] is True
    assert doc["no_trade"]["source"]["turnover_block"]["applies"] is True
    assert "turnover" in doc["recommended_action"].lower()


def test_candidate_that_misses_success_criteria_keeps_current_portfolio() -> None:
    doc = build_decision_verdict_from_block7_8(
        candidate_generation=_generation(),
        current_vs_candidate=_comparison(material=True, success="not_met"),
    )

    assert doc["verdict_id"] == "no_material_rebalance_recommended"
    assert doc["verdict_reason_id"] == "keep_current_portfolio"
    assert "Keep current portfolio" in doc["recommended_action"]
