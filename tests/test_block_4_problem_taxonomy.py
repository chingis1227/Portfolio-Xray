"""Tests for Block 4 v2 problem taxonomy registry (Session 02)."""

from __future__ import annotations

from scripts.core_mvp_validation_contract import (
    BLOCK_4_V2_ACTION_PATH_IDS,
    PROBLEM_CLASSIFICATION_V2_IDS,
)
from src.block_2_6_portfolio_weakness_map import RISK_TYPES
from src.block_4.problem_taxonomy import (
    ACTION_PATH_REGISTRY,
    BLOCK_2_6_RISK_TYPE_TO_PROBLEM_IDS_V2,
    PROBLEM_ID_V1_TO_V2,
    PROBLEM_REGISTRY,
    ROOT_CAUSE_ELEVATION_RULES,
    all_action_path_ids,
    all_problem_ids,
    get_action_path,
    get_problem_definition,
    method_suggestions_for_problem,
    reasonable_paths_for_problem,
    resolve_problem_id_v2,
)


def test_registry_has_fifteen_problems() -> None:
    assert len(PROBLEM_REGISTRY) == 15
    assert set(all_problem_ids()) == PROBLEM_CLASSIFICATION_V2_IDS


def test_action_paths_match_contract() -> None:
    assert set(all_action_path_ids()) == BLOCK_4_V2_ACTION_PATH_IDS


def test_every_problem_has_primary_action_path() -> None:
    for pid, defn in PROBLEM_REGISTRY.items():
        assert defn.primary_action_path_id in ACTION_PATH_REGISTRY, pid
        for sid in defn.secondary_action_path_ids:
            assert sid in ACTION_PATH_REGISTRY, f"{pid} secondary {sid}"


def test_every_problem_has_required_metadata_fields() -> None:
    for pid, defn in PROBLEM_REGISTRY.items():
        assert defn.label_en.strip(), pid
        assert defn.technical_definition_en.strip(), pid
        assert defn.portfolio_manager_interpretation_en.strip(), pid
        assert defn.required_evidence_signals, pid
        assert defn.launchpad_card_title_en.strip(), pid
        assert defn.when_not_to_select_as_primary_en.strip(), pid


def test_reasonable_paths_non_empty_for_actionable_problems() -> None:
    for pid in (
        "high_volatility",
        "weak_crisis_resilience",
        "current_portfolio_acceptable",
        "evidence_insufficient_data_quality",
    ):
        paths = reasonable_paths_for_problem(pid)
        assert paths, pid
        for goal in paths:
            found = any(ap.goal_label == goal for ap in ACTION_PATH_REGISTRY.values())
            assert found, f"{pid} goal {goal!r} not in action paths"


def test_method_suggestions_suppressed_for_monitor_and_evidence_problems() -> None:
    assert method_suggestions_for_problem("current_portfolio_acceptable") == ()
    assert method_suggestions_for_problem("evidence_insufficient_data_quality") == ()
    assert method_suggestions_for_problem("weak_crisis_resilience")


def test_v1_legacy_mapping() -> None:
    assert resolve_problem_id_v2("high_drawdown_risk") == "high_drawdown"
    assert resolve_problem_id_v2("data_review_required") == "evidence_insufficient_data_quality"
    assert resolve_problem_id_v2("high_volatility") == "high_volatility"
    assert PROBLEM_ID_V1_TO_V2["high_drawdown_risk"] == "high_drawdown"


def test_block_2_6_mapping_covers_all_risk_types() -> None:
    assert set(BLOCK_2_6_RISK_TYPE_TO_PROBLEM_IDS_V2) == set(RISK_TYPES)
    for risk_type, problem_ids in BLOCK_2_6_RISK_TYPE_TO_PROBLEM_IDS_V2.items():
        for pid in problem_ids:
            assert pid in PROBLEM_REGISTRY, f"{risk_type} -> {pid}"


def test_root_cause_rules_reference_valid_problem_ids() -> None:
    assert ROOT_CAUSE_ELEVATION_RULES
    for rule in ROOT_CAUSE_ELEVATION_RULES:
        assert rule["prefer_primary"] in PROBLEM_REGISTRY
        for pid in rule.get("demote_when_present", ()):
            assert pid in PROBLEM_REGISTRY


def test_get_helpers() -> None:
    assert get_problem_definition("missing") is None
    assert get_action_path("reduce_volatility") is not None
    assert get_problem_definition("high_drawdown").problem_id_legacy == "high_drawdown_risk"
