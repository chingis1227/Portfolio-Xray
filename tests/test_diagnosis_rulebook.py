"""Parity tests for the read-only Block 4 diagnosis rulebook."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.block_4.diagnosis_rulebook import (
    REQUIRED_GOVERNANCE_CHECKS,
    assert_valid_diagnosis_rulebook,
    load_diagnosis_rulebook,
    validate_diagnosis_rulebook,
)
from src.block_4.problem_taxonomy import (
    ACTION_PATH_REGISTRY,
    PROBLEM_REGISTRY,
    ROOT_CAUSE_ELEVATION_RULES,
)


def test_rulebook_yaml_parses_as_mapping() -> None:
    rulebook = load_diagnosis_rulebook()

    assert isinstance(rulebook, dict)
    assert rulebook["schema_version"] == "diagnosis_rulebook_schema_v1"
    assert rulebook["status"] == "parity"
    assert rulebook["threshold_source"] == "config/block_4_thresholds.yml"


def test_rulebook_validator_passes_current_yaml() -> None:
    result = assert_valid_diagnosis_rulebook()

    assert result.valid
    assert not result.errors
    assert "problem_ids_match_python_registry" in result.checks_passed
    assert "action_paths_match_python_registry" in result.checks_passed
    assert "threshold_refs_exist_in_threshold_source" in result.checks_passed


def test_rulebook_action_paths_match_python_registry() -> None:
    rulebook = load_diagnosis_rulebook()
    yaml_paths = rulebook["action_paths"]

    assert set(yaml_paths) == set(ACTION_PATH_REGISTRY)
    for action_path_id, defn in ACTION_PATH_REGISTRY.items():
        row = yaml_paths[action_path_id]
        assert row["label_en"] == defn.label_en
        assert row["goal_label"] == defn.goal_label
        assert tuple(row["candidate_method_ids"]) == defn.candidate_method_ids
        assert row["launchpad_description_en"] == defn.launchpad_description_en


def test_rulebook_problems_match_python_registry() -> None:
    rulebook = load_diagnosis_rulebook()
    yaml_problems = rulebook["problems"]

    assert set(yaml_problems) == set(PROBLEM_REGISTRY)
    for problem_id, defn in PROBLEM_REGISTRY.items():
        row = yaml_problems[problem_id]
        evidence = row["evidence"]
        launchpad = row["launchpad"]
        action_paths = row["action_paths"]

        assert row["label_en"] == defn.label_en
        assert row["role"] == defn.diagnosis_role
        assert row["eligible_as_primary"] is defn.eligible_as_primary
        assert row["suppress_launchpad_methods"] is defn.suppress_launchpad_methods
        assert tuple(evidence["required_signals"]) == defn.required_evidence_signals
        assert tuple(evidence["supporting_signals"]) == defn.supporting_evidence_signals
        assert tuple(evidence["contrary_signals"]) == defn.negative_evidence_signals
        assert action_paths["primary_action_path_id"] == defn.primary_action_path_id
        assert tuple(action_paths["secondary_action_path_ids"]) == defn.secondary_action_path_ids
        assert launchpad["card_title_en"] == defn.launchpad_card_title_en
        assert launchpad["what_this_tests_en"] == defn.launchpad_what_this_tests_en
        assert launchpad["tradeoff_en"] == defn.launchpad_tradeoff_en
        assert launchpad["skip_when_en"] == defn.launchpad_skip_when_en
        assert tuple(launchpad["default_candidate_method_ids"]) == defn.default_candidate_method_ids
        assert row["do_not_overreact_en"] == defn.do_not_overreact_reason_en
        assert row["when_not_primary_en"] == defn.when_not_to_select_as_primary_en
        assert row["false_positive_notes_en"] == [defn.common_false_positive_en]
        assert row["false_negative_notes_en"] == [defn.common_false_negative_en]
        assert row["downstream_comparison_focus_en"] == defn.downstream_comparison_focus_en


def test_rulebook_prioritization_rules_match_root_cause_elevation_rules() -> None:
    rulebook = load_diagnosis_rulebook()
    yaml_rules = {row["rule_id"]: row for row in rulebook["prioritization_rules"]}
    python_rules = {row["rule_id"]: row for row in ROOT_CAUSE_ELEVATION_RULES}

    assert set(yaml_rules) == set(python_rules)
    for rule_id, current in python_rules.items():
        row = yaml_rules[rule_id]
        assert row["prefer_primary"] == current["prefer_primary"]
        assert tuple(row["demote_when_present"]) == tuple(current["demote_when_present"])
        assert row["requires_stress_confirmation"] is bool(current.get("requires_stress_confirmation", False))
        expected_signals = (current["requires_signal"],) if current.get("requires_signal") else ()
        assert tuple(row["requires_signals"]) == expected_signals


def test_rulebook_governance_lists_required_validation_checks() -> None:
    rulebook = load_diagnosis_rulebook()

    assert REQUIRED_GOVERNANCE_CHECKS <= set(rulebook["governance"]["required_validation_checks"])


def test_rulebook_validation_detects_problem_registry_drift(tmp_path: Path) -> None:
    rulebook = load_diagnosis_rulebook()
    rulebook["problems"] = dict(rulebook["problems"])
    rulebook["problems"].pop(next(iter(PROBLEM_REGISTRY)))
    path = tmp_path / "diagnosis_rulebook.yml"

    import yaml

    path.write_text(yaml.safe_dump(rulebook, allow_unicode=True, sort_keys=False), encoding="utf-8")

    result = validate_diagnosis_rulebook(path)

    assert not result.valid
    assert any("problem ids do not match Python registry" in error for error in result.errors)


def test_rulebook_validation_does_not_mutate_python_registries() -> None:
    before_problems = tuple(PROBLEM_REGISTRY.items())
    before_action_paths = tuple(ACTION_PATH_REGISTRY.items())

    result = assert_valid_diagnosis_rulebook()

    assert result.valid
    assert tuple(PROBLEM_REGISTRY.items()) == before_problems
    assert tuple(ACTION_PATH_REGISTRY.items()) == before_action_paths


@pytest.mark.parametrize(
    "problem_id",
    ["weak_crisis_resilience", "high_concentration", "evidence_insufficient_data_quality"],
)
def test_rulebook_problem_entries_have_hypothesis_and_success_criteria(problem_id: str) -> None:
    rulebook = load_diagnosis_rulebook()
    row = rulebook["problems"][problem_id]

    assert row["hypothesis_tests"], problem_id
    assert row["success_criteria"], problem_id
    criterion_ids = {item["criterion_id"] for item in row["success_criteria"]}
    for test in row["hypothesis_tests"]:
        assert set(test["success_criteria_refs"]) <= criterion_ids
        assert test["decision_boundary_en"].startswith("Candidate comparison and Decision Verdict")
