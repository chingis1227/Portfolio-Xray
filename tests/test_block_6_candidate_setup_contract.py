from __future__ import annotations

from src.portfolio_alternatives_builder import (
    CANDIDATE_SETUP_PROHIBITED_FIELDS,
    candidate_setup_contract_violations,
    builder_prefill_to_candidate_setup,
    launchpad_card_to_builder_prefill,
)


DECISION_BOUNDARY = (
    "This is not a rebalance recommendation. Actual rebalance decision is made "
    "only after Current vs Candidate Comparison and Decision Verdict."
)


def _launchpad_card(**overrides: object) -> dict[str, object]:
    card: dict[str, object] = {
        "card_id": "launchpad_01_improve_crisis_resilience",
        "goal": "Improve crisis resilience",
        "source_problem_id": "weak_crisis_resilience",
        "source_diagnosis_id": "weak_crisis_resilience",
        "hypothesis_to_test": "Test whether stress loss improves without hiding tradeoffs.",
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
        "success_criteria": ["Lower severe-stress loss."],
        "tradeoff_to_watch": "Stress protection versus expected return and turnover.",
        "when_to_skip": "Skip if the crisis-resilience diagnosis no longer applies.",
        "card_type": "targeted_hypothesis_test",
        "launch_status": "hypothesis_test",
        "is_rebalance_recommendation": False,
        "decision_boundary": DECISION_BOUNDARY,
    }
    card.update(overrides)
    return card


def test_candidate_setup_contains_only_validated_block_6_handoff_fields() -> None:
    prefill = launchpad_card_to_builder_prefill(_launchpad_card())

    setup = builder_prefill_to_candidate_setup(prefill)

    assert setup is not None
    assert setup["candidate_setup_id"].startswith("candidate_setup_builder_prefill_")
    assert setup["builder_prefill_id"] == prefill["builder_prefill_id"]
    assert setup["source_card_id"] == "launchpad_01_improve_crisis_resilience"
    assert setup["source_diagnosis_id"] == "weak_crisis_resilience"
    assert setup["goal"] == "Improve crisis resilience"
    assert setup["selected_method"] == "minimum_cvar"
    assert setup["original_suggested_method"] == "minimum_cvar"
    assert setup["method_changed_by_user"] is False
    assert setup["parameters"]["method"] == "minimum_cvar"
    assert setup["constraints"]["constraint_preset"] == "balanced"
    assert setup["success_criteria"] == ["Lower severe-stress loss."]
    assert setup["tradeoff_to_watch"] == "Stress protection versus expected return and turnover."
    assert setup["decision_boundary"] == DECISION_BOUNDARY
    assert setup["is_rebalance_recommendation"] is False
    assert setup["can_generate_candidate"] is True
    assert setup["validation_status"] == "valid"
    assert setup["validation_warnings"] == []
    assert setup["created_at"]
    assert CANDIDATE_SETUP_PROHIBITED_FIELDS.isdisjoint(setup)
    assert not candidate_setup_contract_violations(setup)


def test_candidate_setup_preserves_user_method_change_without_candidate_id() -> None:
    prefill = launchpad_card_to_builder_prefill(_launchpad_card())

    setup = builder_prefill_to_candidate_setup(
        prefill,
        edits={"selected_method": "maximum_diversification"},
    )

    assert setup is not None
    assert setup["selected_method"] == "maximum_diversification"
    assert setup["original_suggested_method"] == "minimum_cvar"
    assert setup["method_changed_by_user"] is True
    assert "candidate_id" not in setup
    assert "weights" not in setup


def test_candidate_setup_is_not_exposed_for_data_quality_blocker() -> None:
    prefill = launchpad_card_to_builder_prefill(
        _launchpad_card(
            card_id="launchpad_01_evidence_insufficient_do_not_act_yet",
            goal="Review data quality",
            source_problem_id="evidence_insufficient_data_quality",
            source_diagnosis_id="evidence_insufficient_data_quality",
            default_method=None,
            suggested_methods=[],
            card_type="monitor_or_data_step",
            launch_status="monitor_or_resolve_data",
        )
    )

    setup = builder_prefill_to_candidate_setup(prefill)

    assert setup is None
