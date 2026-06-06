from __future__ import annotations

import json
from pathlib import Path

from src.candidate_generation import (
    CANDIDATE_GENERATION_SCHEMA_VERSION,
    build_candidate_generation_document,
    candidate_generation_contract_violations,
    write_candidate_generation_outputs,
)
from src.portfolio_alternatives_builder import (
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
        "hypothesis_to_test": "Test whether severe-stress loss improves.",
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


def _candidate_setup(edits: dict[str, object] | None = None) -> dict[str, object]:
    prefill = launchpad_card_to_builder_prefill(_launchpad_card())
    setup = builder_prefill_to_candidate_setup(prefill, edits=edits)
    assert setup is not None
    return setup


def test_candidate_generation_contract_preserves_builder_setup_fields() -> None:
    setup = _candidate_setup()

    document = build_candidate_generation_document(
        setup,
        weights={"VOO": 0.5, "TLT": 0.5},
    )

    assert document["schema_version"] == CANDIDATE_GENERATION_SCHEMA_VERSION
    assert {
        "candidate",
        "generation_status",
        "source_builder_setup",
        "method_availability",
        "warnings",
        "handoff_to_comparison",
    }.issubset(document)
    assert document["generation_status"] == "generated"
    candidate = document["candidate"]
    assert candidate["candidate_id"] == "minimum_cvar_constrained"
    assert candidate["source_card_id"] == "launchpad_01_improve_crisis_resilience"
    assert candidate["source_diagnosis_id"] == "weak_crisis_resilience"
    assert candidate["source_launchpad_card_type"] == "targeted_hypothesis_test"
    assert candidate["source_builder_setup_id"] == setup["builder_prefill_id"]
    assert candidate["candidate_setup_id"] == setup["candidate_setup_id"]
    assert candidate["goal"] == "Improve crisis resilience"
    assert candidate["hypothesis_to_test"] == "Test whether severe-stress loss improves."
    assert candidate["method"] == "minimum_cvar"
    assert candidate["method_variant"] == "minimum_cvar_constrained"
    assert candidate["capped"] is True
    assert candidate["uncapped"] is False
    assert candidate["min_asset_weight"] == 0.0
    assert candidate["max_asset_weight"] == 0.2
    assert candidate["constraint_preset"] == "balanced"
    assert candidate["parameters"]["method"] == "minimum_cvar"
    assert candidate["constraints"]["constraint_preset"] == "balanced"
    assert candidate["weights"] == {"VOO": 0.5, "TLT": 0.5}
    assert candidate["status"] == "generated"
    assert candidate["failure_reason"] is None
    assert candidate["infeasibility_reason"] is None
    assert candidate["success_criteria"] == ["Lower severe-stress loss."]
    assert candidate["tradeoff_to_watch"] == "Stress protection versus expected return and turnover."
    assert candidate["decision_boundary"] == DECISION_BOUNDARY
    assert candidate["is_rebalance_recommendation"] is False
    assert candidate["generation_source"] == "block_6_builder_setup"
    assert document["handoff_to_comparison"]["can_compare"] is True
    assert not candidate_generation_contract_violations(document)


def test_write_candidate_generation_outputs_materializes_json(tmp_path: Path) -> None:
    setup = _candidate_setup(edits={"selected_method": "maximum_diversification"})

    paths = write_candidate_generation_outputs(
        tmp_path,
        candidate_setup=setup,
        weights={"VOO": 0.4, "TLT": 0.6},
    )

    path = paths["candidate_generation_json"]
    assert path == tmp_path / "candidate_generation.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["candidate"]["candidate_id"] == "maximum_diversification"
    assert payload["candidate"]["method"] == "maximum_diversification"
    assert payload["candidate"]["weights"] == {"VOO": 0.4, "TLT": 0.6}
    assert payload["guardrails"]["creates_exactly_one_candidate_attempt"] is True


def test_generated_status_requires_non_empty_weights() -> None:
    setup = _candidate_setup()

    try:
        build_candidate_generation_document(setup, status="generated")
    except Exception as exc:
        assert "weights must be non-empty" in str(exc)
    else:
        raise AssertionError("generated candidate without weights must violate the contract")
