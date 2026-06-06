from __future__ import annotations

import json

from scripts.core_mvp_validation_contract import decision_verdict_v1_product_contract_violations
from src.decision_verdict import build_decision_verdict_from_block7_8


def _candidate_generation(
    *,
    status: str = "generated",
    method_available: bool = True,
) -> dict:
    return {
        "schema_version": "candidate_generation_v1",
        "generation_status": status,
        "candidate": {
            "candidate_id": "equal_weight",
            "candidate_name": "Equal Weight",
            "status": status,
            "failure_reason": None,
            "infeasibility_reason": None,
            "is_rebalance_recommendation": False,
        },
        "method_availability": {
            "method": "equal_weight",
            "method_variant": "equal_weight",
            "available": method_available,
            "availability_status": "available" if method_available else "unavailable",
        },
        "warnings": [],
        "handoff_to_comparison": {
            "can_compare": status == "generated",
            "blocked_reason": None if status == "generated" else f"candidate_generation_{status}",
        },
    }


def _current_vs_candidate(*, material: bool = True, success: str = "met") -> dict:
    return {
        "schema_version": "current_vs_candidate_v1",
        "diagnostic_only": True,
        "baseline": {"candidate_id": "analysis_subject", "status": "available"},
        "selected_candidate_ids": ["equal_weight"],
        "comparisons": [
            {
                "candidate_id": "equal_weight",
                "status": "available",
                "dimensions": [{"field": "worst_stress_loss", "status": "available"}],
                "risk_reduced": [{"field": "worst_stress_loss", "is_material": material}],
                "risk_added": [{"field": "cagr", "is_material": True}],
                "what_improved": [{"field": "worst_stress_loss", "is_material": material}],
                "what_worsened": [{"field": "cagr", "is_material": True}],
                "practicality": {
                    "turnover_required": {"status": "available", "turnover_half_sum_pct": 0.10},
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


def test_direct_block9_verdict_contract_is_valid_and_tradeoff_visible() -> None:
    doc = build_decision_verdict_from_block7_8(
        candidate_generation=_candidate_generation(),
        current_vs_candidate=_current_vs_candidate(),
    )

    assert not decision_verdict_v1_product_contract_violations(doc)
    assert doc["verdict_id"] == "rebalance_to_selected_candidate"
    assert doc["selection_decision_status"] == "selected_candidate"
    assert doc["source_artifacts"]["candidate_generation"] == "candidate_generation.json"
    assert doc["source_artifacts"]["current_vs_candidate"] == "current_vs_candidate.json"
    assert doc["source_artifacts"]["selection_decision"] is None
    assert doc["guardrails"]["does_not_claim_best_portfolio"] is True
    assert doc["guardrails"]["does_not_hide_tradeoffs"] is True
    assert "best portfolio" not in json.dumps(doc).lower()
    assert doc["evidence_summary"]["what_worsened"]


def test_direct_block9_insufficient_method_quality_is_evidence_insufficient() -> None:
    doc = build_decision_verdict_from_block7_8(
        candidate_generation=_candidate_generation(method_available=False),
        current_vs_candidate=_current_vs_candidate(),
    )

    assert doc["verdict_id"] == "evidence_insufficient"
    assert doc["selection_decision_status"] == "data_review_required"
    assert doc["verdict_reason_id"] == "insufficient_optimizer_or_method_quality"
    assert "method_unavailable" in doc["confidence_limitations"]


def test_direct_block9_mixed_evidence_can_test_another_candidate() -> None:
    doc = build_decision_verdict_from_block7_8(
        candidate_generation=_candidate_generation(),
        current_vs_candidate=_current_vs_candidate(material=False, success="mixed"),
    )

    assert doc["verdict_id"] == "test_another_candidate_or_review_evidence"
    assert doc["selection_decision_status"] == "inconclusive"
    assert doc["verdict_reason_id"] == "test_another_candidate"
    assert "test another candidate" in doc["recommended_action"].lower()
