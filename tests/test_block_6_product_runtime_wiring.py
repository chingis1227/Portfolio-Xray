from __future__ import annotations

import json
from pathlib import Path

from src.portfolio_alternatives_builder import (
    PORTFOLIO_ALTERNATIVES_BUILDER_FILENAME,
    write_portfolio_alternatives_builder_outputs,
)
from src.product_bundle_paths import (
    manifest_key_category,
    product_bundle_generated_paths_for_manifest,
    resolve_portfolio_alternatives_builder_path,
)


DECISION_BOUNDARY = (
    "This is not a rebalance recommendation. Actual rebalance decision is made "
    "only after Current vs Candidate Comparison and Decision Verdict."
)


def _launchpad_doc(card: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": "candidate_launchpad_v3",
        "cards": [card],
        "summary": {"primary_card_id": card.get("card_id")},
    }


def _targeted_card(**overrides: object) -> dict[str, object]:
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
            }
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


def test_builder_writer_materializes_ready_setup_without_candidate_outputs(tmp_path: Path) -> None:
    paths = write_portfolio_alternatives_builder_outputs(
        tmp_path,
        candidate_launchpad=_launchpad_doc(_targeted_card()),
        problem_classification={
            "next_diagnostic_step": {
                "type": "targeted_hypothesis_test",
                "decision_boundary": DECISION_BOUNDARY,
            }
        },
    )

    path = paths["portfolio_alternatives_builder_json"]
    assert path == tmp_path / PORTFOLIO_ALTERNATIVES_BUILDER_FILENAME
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["schema_version"] == "portfolio_alternatives_builder_v1"
    assert doc["status"] == "ok"
    assert doc["can_generate_candidate"] is True
    assert doc["reason"] is None
    assert doc["builder_prefill"]["source_card_id"] == "launchpad_01_improve_crisis_resilience"
    assert doc["candidate_setup"]["selected_method"] == "minimum_cvar"
    assert doc["validation"]["validation_status"] == "valid"
    assert doc["guardrails"]["does_not_generate_candidate"] is True
    assert "candidate_id" not in doc["candidate_setup"]
    assert not (tmp_path / "current_vs_candidate.json").exists()
    assert not (tmp_path / "decision_verdict.json").exists()


def test_builder_writer_blocks_data_quality_card(tmp_path: Path) -> None:
    write_portfolio_alternatives_builder_outputs(
        tmp_path,
        candidate_launchpad=_launchpad_doc(
            _targeted_card(
                card_id="launchpad_01_evidence_insufficient_do_not_act_yet",
                goal="Review data quality",
                source_problem_id="evidence_insufficient_data_quality",
                source_diagnosis_id="evidence_insufficient_data_quality",
                default_method=None,
                suggested_methods=[],
                card_type="monitor_or_data_step",
                launch_status="monitor_or_resolve_data",
            )
        ),
        problem_classification=None,
    )

    doc = json.loads(
        (tmp_path / PORTFOLIO_ALTERNATIVES_BUILDER_FILENAME).read_text(encoding="utf-8")
    )
    assert doc["status"] == "blocked"
    assert doc["can_generate_candidate"] is False
    assert doc["reason"] == "data_quality_blocker"
    assert doc["candidate_setup"] is None
    assert doc["validation"]["validation_status"] == "blocked_by_data_quality"


def test_builder_artifact_is_discoverable_as_product_bundle_key(tmp_path: Path) -> None:
    subject = tmp_path / "Main portfolio" / "analysis_subject"
    subject.mkdir(parents=True)
    (subject / "problem_classification.json").write_text("{}", encoding="utf-8")
    (subject / "candidate_launchpad.json").write_text("{}", encoding="utf-8")
    (subject / PORTFOLIO_ALTERNATIVES_BUILDER_FILENAME).write_text("{}", encoding="utf-8")

    generated = product_bundle_generated_paths_for_manifest(tmp_path / "Main portfolio")

    assert resolve_portfolio_alternatives_builder_path(tmp_path / "Main portfolio") == (
        subject / PORTFOLIO_ALTERNATIVES_BUILDER_FILENAME
    )
    assert "portfolio_alternatives_builder_json" in generated
    assert manifest_key_category("portfolio_alternatives_builder_json") == "product_bundle"
