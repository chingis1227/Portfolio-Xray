from __future__ import annotations

from scripts.core_mvp_validation_contract import (
    builder_prefill_product_contract_violations,
)
from src.portfolio_alternatives_builder import (
    BUILDER_PREFILL_PROHIBITED_FIELDS,
    BUILDER_PREFILL_REQUIRED_FIELDS,
    builder_prefill_contract_violations,
    build_builder_prefill_from_launchpad_card,
)


def _launchpad_card(**overrides: object) -> dict[str, object]:
    card: dict[str, object] = {
        "card_id": "launchpad_01_improve_crisis_resilience",
        "goal": "Improve crisis resilience",
        "source_problem_id": "weak_crisis_resilience",
        "source_diagnosis_id": "weak_crisis_resilience",
        "hypothesis_to_test": "Test whether stress loss improves.",
        "default_method": "minimum_cvar",
        "suggested_methods": [
            {
                "candidate_method_id": "minimum_cvar",
                "method_role": "targeted_hypothesis",
            },
            {
                "candidate_method_id": "maximum_diversification",
                "method_role": "targeted_hypothesis",
            },
        ],
        "success_criteria": ["Lower stress loss."],
        "tradeoff_to_watch": "Stress protection versus expected return.",
        "when_to_skip": "Skip if the diagnosis no longer applies.",
        "card_type": "targeted_hypothesis_test",
        "launch_status": "hypothesis_test",
        "is_rebalance_recommendation": False,
        "decision_boundary": "This is not a rebalance recommendation.",
    }
    card.update(overrides)
    return card


def test_block_6_builder_prefill_contains_session_01_contract_fields() -> None:
    prefill = build_builder_prefill_from_launchpad_card(_launchpad_card())

    missing = set(BUILDER_PREFILL_REQUIRED_FIELDS) - set(prefill)

    assert not missing
    assert prefill["builder_prefill_id"] == "builder_prefill_launchpad_01_improve_crisis_resilience"
    assert prefill["source_problem_id"] == "weak_crisis_resilience"
    assert prefill["rebalancing_frequency"] is None
    assert prefill["transaction_cost_bps"] is None
    assert prefill["created_from"] == "candidate_launchpad_v3"
    assert prefill["status"] == "ready_for_user_confirmation"
    assert prefill["warnings"] == []
    assert BUILDER_PREFILL_PROHIBITED_FIELDS.isdisjoint(prefill)
    assert not builder_prefill_contract_violations(prefill)
    assert not builder_prefill_product_contract_violations(prefill)


def test_block_6_builder_prefill_contract_rejects_candidate_output_fields() -> None:
    prefill = build_builder_prefill_from_launchpad_card(_launchpad_card())
    prefill["candidate_id"] = "minimum_cvar"
    prefill["weights"] = {"VOO": 1.0}

    local_violations = builder_prefill_contract_violations(prefill)
    product_violations = builder_prefill_product_contract_violations(prefill)

    assert any("prohibited fields present" in row for row in local_violations)
    assert any("candidate_id" in row and "weights" in row for row in local_violations)
    assert any("prohibited fields present" in row for row in product_violations)


def test_block_6_data_quality_prefill_is_blocked_contract_object() -> None:
    prefill = build_builder_prefill_from_launchpad_card(
        _launchpad_card(
            card_id="launchpad_01_evidence_insufficient_do_not_act_yet",
            goal="Review data quality",
            source_problem_id="evidence_insufficient_data_quality",
            source_diagnosis_id="evidence_insufficient_data_quality",
            hypothesis_to_test="Resolve data quality before testing candidates.",
            default_method=None,
            suggested_methods=[],
            card_type="monitor_or_data_step",
            launch_status="monitor_or_resolve_data",
        )
    )

    assert prefill["status"] == "blocked"
    assert prefill["suggested_method"] is None
    assert prefill["candidate_generation_allowed"] is False
    assert prefill["warnings"] == []
    assert BUILDER_PREFILL_PROHIBITED_FIELDS.isdisjoint(prefill)
    assert not builder_prefill_contract_violations(prefill)
    assert not builder_prefill_product_contract_violations(prefill)
