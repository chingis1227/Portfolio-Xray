from __future__ import annotations

from src.decision_verdict import build_decision_verdict_from_block7_8


def _generation() -> dict:
    return {
        "generation_status": "generated",
        "candidate": {"candidate_id": "equal_weight", "status": "generated"},
        "method_availability": {"available": True, "availability_status": "available"},
        "warnings": [],
        "handoff_to_comparison": {"can_compare": True},
    }


def test_missing_current_vs_candidate_evidence_is_insufficient() -> None:
    doc = build_decision_verdict_from_block7_8(
        candidate_generation=_generation(),
        current_vs_candidate=None,
    )

    assert doc["verdict_id"] == "evidence_insufficient"
    assert doc["selection_decision_status"] == "data_review_required"
    assert doc["verdict_reason_id"] == "current_vs_candidate_missing"
    assert doc["no_trade"]["evaluated"] is False
    assert "missing or degraded evidence" in doc["recommended_action"]


def test_data_quality_gaps_make_verdict_evidence_insufficient() -> None:
    doc = build_decision_verdict_from_block7_8(
        candidate_generation=_generation(),
        current_vs_candidate={
            "baseline": {"candidate_id": "analysis_subject"},
            "selected_candidate_ids": ["equal_weight"],
            "comparisons": [
                {
                    "candidate_id": "equal_weight",
                    "status": "available",
                    "dimensions": [{"field": "worst_stress_loss", "status": "available"}],
                    "risk_reduced": [],
                    "risk_added": [],
                    "what_improved": [],
                    "what_worsened": [],
                    "practicality": {},
                    "success_criteria_result": {"overall_status": "unavailable"},
                    "materiality_for_decision_review": {
                        "status": "insufficient_evidence",
                        "is_material_enough": False,
                        "reason": "no_available_comparison_metrics",
                    },
                    "data_quality": {
                        "missing_fields": ["stress.scenarios"],
                        "warnings": [],
                        "construction_disclosure_status": "available",
                    },
                }
            ],
            "warnings": [],
        },
    )

    assert doc["verdict_id"] == "evidence_insufficient"
    assert doc["verdict_reason_id"] == "insufficient_data_quality"
    assert "comparison_row_missing_fields" in doc["confidence_limitations"]
