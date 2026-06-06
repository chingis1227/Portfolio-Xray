from __future__ import annotations

from src.decision_verdict import build_decision_verdict_from_block7_8


def test_failed_candidate_generation_cannot_become_rebalance_verdict() -> None:
    doc = build_decision_verdict_from_block7_8(
        candidate_generation={
            "generation_status": "failed",
            "candidate": {
                "candidate_id": "minimum_variance_constrained",
                "status": "failed",
                "failure_reason": "optimizer_solver_failed",
                "infeasibility_reason": None,
                "is_rebalance_recommendation": False,
            },
            "method_availability": {
                "available": True,
                "availability_status": "available",
            },
            "warnings": ["factory_step_failed"],
            "handoff_to_comparison": {
                "can_compare": False,
                "blocked_reason": "candidate_generation_failed",
            },
        },
        current_vs_candidate={
            "baseline": {"candidate_id": "analysis_subject"},
            "selected_candidate_ids": [],
            "comparisons": [],
            "warnings": ["candidate_unavailable:minimum_variance_constrained"],
        },
    )

    assert doc["verdict_id"] == "candidate_failed_or_infeasible"
    assert doc["selection_decision_status"] == "candidate_failed_or_infeasible"
    assert doc["selected_candidate_id"] is None
    assert doc["reviewed_candidate_id"] == "minimum_variance_constrained"
    assert doc["verdict_reason_id"] == "candidate_failed_or_infeasible"
    assert doc["no_trade"]["evaluated"] is False
    assert "optimizer_solver_failed" in doc["confidence_limitations"]


def test_infeasible_candidate_generation_blocks_comparison_verdict() -> None:
    doc = build_decision_verdict_from_block7_8(
        candidate_generation={
            "generation_status": "infeasible",
            "candidate": {
                "candidate_id": "minimum_cvar_constrained",
                "status": "infeasible",
                "failure_reason": None,
                "infeasibility_reason": "constraints_infeasible",
                "is_rebalance_recommendation": False,
            },
            "method_availability": {
                "available": True,
                "availability_status": "available",
            },
            "warnings": [],
            "handoff_to_comparison": {
                "can_compare": False,
                "blocked_reason": "candidate_generation_infeasible",
            },
        },
        current_vs_candidate=None,
    )

    assert doc["verdict_id"] == "candidate_failed_or_infeasible"
    assert doc["verdict_reason_id"] == "candidate_failed_or_infeasible"
    assert "constraints_infeasible" in doc["confidence_limitations"]
