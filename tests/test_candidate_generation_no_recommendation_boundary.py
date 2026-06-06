from __future__ import annotations

import pytest

from src.candidate_generation import (
    CandidateGenerationError,
    build_candidate_generation_document,
)
from src.portfolio_alternatives_builder import (
    builder_prefill_to_candidate_setup,
    launchpad_card_to_builder_prefill,
)


DECISION_BOUNDARY = (
    "This is not a rebalance recommendation. Actual rebalance decision is made "
    "only after Current vs Candidate Comparison and Decision Verdict."
)


def _reference_candidate_setup() -> dict[str, object]:
    prefill = launchpad_card_to_builder_prefill(
        {
            "card_id": "launchpad_01_compare_against_simple_benchmark",
            "goal": "Compare against simple benchmark",
            "source_problem_id": "mixed_evidence_no_action",
            "source_diagnosis_id": "mixed_evidence_no_action",
            "hypothesis_to_test": "Test whether simple references clarify materiality.",
            "default_method": "equal_weight",
            "suggested_methods": [
                {"candidate_method_id": "equal_weight", "method_role": "reference_benchmark"},
                {"candidate_method_id": "risk_parity", "method_role": "reference_benchmark"},
            ],
            "success_criteria": ["Create a transparent reference point."],
            "tradeoff_to_watch": "Simplicity versus risk concentration.",
            "when_to_skip": "Skip if the reference test is not relevant.",
            "card_type": "reference_benchmark_test",
            "launch_status": "reference_test",
            "is_rebalance_recommendation": False,
            "decision_boundary": DECISION_BOUNDARY,
        }
    )
    setup = builder_prefill_to_candidate_setup(prefill)
    assert setup is not None
    return setup


def test_candidate_generation_never_turns_reference_candidate_into_recommendation() -> None:
    document = build_candidate_generation_document(
        _reference_candidate_setup(),
        weights={"VOO": 0.5, "TLT": 0.5},
    )

    candidate = document["candidate"]
    assert candidate["source_launchpad_card_type"] == "reference_benchmark_test"
    assert candidate["method"] == "equal_weight"
    assert candidate["is_rebalance_recommendation"] is False
    assert candidate["decision_boundary"] == DECISION_BOUNDARY
    assert "verdict" not in candidate
    assert "recommended_action" not in candidate
    assert document["guardrails"]["does_not_create_decision_verdict"] is True
    assert document["handoff_to_comparison"]["does_not_create_verdict"] is True
    assert document["handoff_to_comparison"]["can_compare"] is True


def test_candidate_generation_rejects_builder_setup_that_cannot_generate() -> None:
    setup = _reference_candidate_setup()
    setup["can_generate_candidate"] = False

    with pytest.raises(CandidateGenerationError, match="candidate_setup_cannot_generate_candidate"):
        build_candidate_generation_document(setup, weights={"VOO": 1.0})


def test_candidate_generation_attempt_without_weights_cannot_compare_yet() -> None:
    document = build_candidate_generation_document(_reference_candidate_setup())

    assert document["generation_status"] == "attempt_created"
    assert document["candidate"]["weights"] is None
    assert document["handoff_to_comparison"]["can_compare"] is False
    assert document["handoff_to_comparison"]["blocked_reason"] == "candidate_weights_not_available"
