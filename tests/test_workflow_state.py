from __future__ import annotations

from pathlib import Path

from src.config_schema import validate_config
from src.portfolio_review_workflow import build_portfolio_review_plan
from src.workflow_state import (
    WORKFLOW_STATE_DIAGNOSIS_ONLY,
    WORKFLOW_STATE_MULTIPLE_CANDIDATES,
    WORKFLOW_STATE_ONE_CANDIDATE,
    classify_review_plan,
    parse_candidate_ids,
    resolve_workflow_state,
)


def _cfg():
    return validate_config(
        {
            "tickers": ["VOO", "BND"],
            "investor_currency": "USD",
            "analysis_subject": {
                "type": "current_portfolio",
                "weights": {"VOO": 0.6, "BND": 0.4},
            },
        }
    )


def test_parse_candidate_ids_handles_string_and_iterable() -> None:
    assert parse_candidate_ids(" equal_weight, risk_parity ,, ") == (
        "equal_weight",
        "risk_parity",
    )
    assert parse_candidate_ids([" equal_weight ", "", "risk_parity"]) == (
        "equal_weight",
        "risk_parity",
    )
    assert parse_candidate_ids(None) == ()


def test_resolve_workflow_state_diagnosis_only_when_candidates_skipped() -> None:
    assessment = resolve_workflow_state(skip_candidates=True)

    assert assessment.state == WORKFLOW_STATE_DIAGNOSIS_ONLY
    assert assessment.candidate_count == 0
    assert assessment.source == "skip_candidates"
    assert assessment.comparison_expected is True


def test_resolve_workflow_state_one_candidate_from_explicit_id() -> None:
    assessment = resolve_workflow_state(candidate_ids="equal_weight")

    assert assessment.state == WORKFLOW_STATE_ONE_CANDIDATE
    assert assessment.candidate_count == 1
    assert assessment.candidate_ids == ("equal_weight",)
    assert assessment.source == "candidate_ids"


def test_resolve_workflow_state_multiple_candidates_from_explicit_ids() -> None:
    assessment = resolve_workflow_state(candidate_ids="equal_weight,risk_parity")

    assert assessment.state == WORKFLOW_STATE_MULTIPLE_CANDIDATES
    assert assessment.candidate_count == 2
    assert assessment.candidate_ids == ("equal_weight", "risk_parity")


def test_resolve_workflow_state_multiple_candidates_from_known_factory_profile() -> None:
    assessment = resolve_workflow_state(factory_profile="core_fast")

    assert assessment.state == WORKFLOW_STATE_MULTIPLE_CANDIDATES
    assert assessment.candidate_count == 6
    assert assessment.source == "factory_profile"
    assert assessment.warnings == ()


def test_resolve_workflow_state_unknown_factory_profile_is_diagnosis_only_warning() -> None:
    assessment = resolve_workflow_state(factory_profile="future_profile")

    assert assessment.state == WORKFLOW_STATE_DIAGNOSIS_ONLY
    assert assessment.candidate_count == 0
    assert assessment.warnings == ("unknown_factory_profile:future_profile",)


def test_resolve_workflow_state_artifact_ids_support_compare_existing_flow() -> None:
    assessment = resolve_workflow_state(
        skip_candidates=True,
        artifact_candidate_ids=["equal_weight", "risk_parity"],
    )

    assert assessment.state == WORKFLOW_STATE_MULTIPLE_CANDIDATES
    assert assessment.candidate_count == 2
    assert assessment.candidate_ids == ("equal_weight", "risk_parity")
    assert assessment.source == "artifact_candidate_ids"


def test_resolve_workflow_state_comparison_expected_tracks_skip_compare() -> None:
    assessment = resolve_workflow_state(candidate_ids="equal_weight", skip_compare=True)

    assert assessment.state == WORKFLOW_STATE_ONE_CANDIDATE
    assert assessment.comparison_expected is False


def test_classify_default_review_plan_as_multiple_candidates(tmp_path: Path) -> None:
    plan = build_portfolio_review_plan(_cfg(), project_root=tmp_path, skip_pdf=True)
    assessment = classify_review_plan(plan)

    assert assessment.state == WORKFLOW_STATE_MULTIPLE_CANDIDATES
    assert assessment.candidate_count == 6
    assert assessment.source == "factory_profile"


def test_classify_explicit_single_candidate_review_plan(tmp_path: Path) -> None:
    plan = build_portfolio_review_plan(
        _cfg(),
        project_root=tmp_path,
        candidate_ids="equal_weight",
        skip_pdf=True,
    )
    assessment = classify_review_plan(plan)

    assert assessment.state == WORKFLOW_STATE_ONE_CANDIDATE
    assert assessment.candidate_count == 1
    assert assessment.candidate_ids == ("equal_weight",)


def test_classify_skip_candidates_plan_as_diagnosis_only_unknown_scope(tmp_path: Path) -> None:
    plan = build_portfolio_review_plan(
        _cfg(),
        project_root=tmp_path,
        skip_candidates=True,
        skip_pdf=True,
    )
    assessment = classify_review_plan(plan)

    assert assessment.state == WORKFLOW_STATE_DIAGNOSIS_ONLY
    assert assessment.source == "comparison_existing_artifacts_unknown"
    assert "comparison_candidate_scope_unknown" in assessment.warnings
