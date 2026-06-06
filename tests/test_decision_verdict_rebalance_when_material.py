from __future__ import annotations

from src.decision_verdict import build_decision_verdict_from_block7_8


def test_material_candidate_can_receive_rebalance_review_verdict() -> None:
    doc = build_decision_verdict_from_block7_8(
        candidate_generation={
            "generation_status": "generated",
            "candidate": {
                "candidate_id": "minimum_cvar_constrained",
                "status": "generated",
                "is_rebalance_recommendation": False,
            },
            "method_availability": {"available": True, "availability_status": "available"},
            "warnings": [],
            "handoff_to_comparison": {"can_compare": True},
        },
        current_vs_candidate={
            "baseline": {"candidate_id": "analysis_subject"},
            "selected_candidate_ids": ["minimum_cvar_constrained"],
            "comparisons": [
                {
                    "candidate_id": "minimum_cvar_constrained",
                    "status": "available",
                    "dimensions": [{"field": "worst_stress_loss", "status": "available"}],
                    "risk_reduced": [
                        {"field": "worst_stress_loss", "is_material": True}
                    ],
                    "risk_added": [
                        {"field": "cagr", "is_material": True}
                    ],
                    "what_improved": [
                        {"field": "worst_stress_loss", "is_material": True}
                    ],
                    "what_worsened": [
                        {"field": "cagr", "is_material": True}
                    ],
                    "practicality": {
                        "turnover_required": {
                            "status": "available",
                            "turnover_half_sum_pct": 0.20,
                        },
                        "estimated_transaction_cost_pct": 0.0002,
                    },
                    "success_criteria_result": {"overall_status": "met", "criteria": []},
                    "materiality_for_decision_review": {
                        "status": "review_candidate",
                        "is_material_enough": True,
                        "reason": "at_least_one_material_improvement_available",
                    },
                    "data_quality": {
                        "missing_fields": [],
                        "warnings": [],
                        "construction_disclosure_status": "available",
                    },
                }
            ],
            "warnings": [],
        },
    )

    assert doc["verdict_id"] == "rebalance_to_selected_candidate"
    assert doc["selected_candidate_id"] == "minimum_cvar_constrained"
    assert doc["reviewed_candidate_id"] == "minimum_cvar_constrained"
    assert doc["verdict_reason_id"] == "rebalance_when_material"
    assert doc["no_trade"]["applies"] is False
    assert doc["evidence_summary"]["risk_added"]
    assert "trade-offs" in doc["recommended_action"]
