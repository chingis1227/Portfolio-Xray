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


def _comparison(*, material: bool = False, success: str = "not_met") -> dict:
    return {
        "baseline": {"candidate_id": "analysis_subject"},
        "selected_candidate_ids": ["equal_weight"],
        "comparisons": [
            {
                "candidate_id": "equal_weight",
                "status": "available",
                "dimensions": [{"field": "vol_annual", "status": "available"}],
                "risk_reduced": [{"field": "vol_annual", "is_material": material}],
                "risk_added": [],
                "what_improved": [{"field": "vol_annual", "is_material": material}],
                "what_worsened": [],
                "practicality": {
                    "turnover_required": {
                        "status": "available",
                        "turnover_half_sum_pct": 0.10,
                    },
                    "estimated_transaction_cost_pct": 0.0001,
                },
                "success_criteria_result": {"overall_status": success, "criteria": []},
                "materiality_for_decision_review": {
                    "status": "review_candidate" if material else "not_material",
                    "is_material_enough": material,
                    "reason": "review_candidate" if material else "no_material_improvement_detected",
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


def _client_fit(status: str = "fit") -> dict:
    return {
        "schema_version": "client_fit_check_v1",
        "client_fit_status": status,
        "profile": {
            "preset_id": "balanced",
            "source_quality": "medium",
            "horizon_years": 7,
            "target_return_range": {"min": 0.05, "max": 0.07},
            "target_vol_range": {"min": 0.07, "max": 0.10},
            "target_max_drawdown_pct": -0.20,
        },
        "goal_risk_conflict": {
            "status": "conflict" if status == "conflict" else "clear",
            "reasons": ["aggressive_return_with_balanced_or_lower_volatility_limit"]
            if status == "conflict"
            else [],
        },
    }


def _problem(status: str = "material_issue", problem_id: str = "high_concentration") -> dict:
    return {
        "schema_version": "problem_classification_v3",
        "diagnostic_quality_status": status,
        "primary_problem": {"problem_id": problem_id},
    }


def test_client_fit_pass_alone_cannot_create_keep_current_when_diagnosis_has_issue() -> None:
    doc = build_decision_verdict_from_block7_8(
        candidate_generation=_generation(),
        current_vs_candidate=_comparison(material=False, success="not_met"),
        client_fit_check=_client_fit("fit"),
        problem_classification=_problem("material_issue"),
    )

    assert doc["verdict_id"] == "test_another_candidate_or_review_evidence"
    assert doc["decision_action"] == "test_another_candidate"
    assert doc["no_trade"]["applies"] is False
    assert doc["verdict_reason_id"] == "client_fit_pass_does_not_clear_material_diagnosis"
    assert doc["evidence_summary"]["client_fit_decision_context"]["client_fit_status"] == "fit"
    assert doc["evidence_summary"]["client_fit_decision_context"]["diagnostic_quality_status"] == "material_issue"
    assert "fit result as enough" in doc["recommended_action"]


def test_goal_risk_conflict_routes_to_revise_objectives_language() -> None:
    doc = build_decision_verdict_from_block7_8(
        candidate_generation=_generation(),
        current_vs_candidate=_comparison(material=True, success="met"),
        client_fit_check=_client_fit("conflict"),
        problem_classification=_problem("clean", "goal_risk_conflict"),
    )

    assert doc["verdict_id"] == "revise_objectives"
    assert doc["selection_decision_status"] == "revise_objectives"
    assert doc["decision_action"] == "revise_objectives"
    assert doc["no_trade"]["evaluated"] is False
    assert "Review the stated return, risk, drawdown, and horizon objectives" in doc["recommended_action"]
    assert "optimizer can satisfy inconsistent goals" in doc["recommended_action"]
    assert doc["guardrails"]["goal_risk_conflict_routes_to_objective_review"] is True
