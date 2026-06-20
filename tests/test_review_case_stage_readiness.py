from __future__ import annotations

import pytest

from src.review_case import (
    ReviewCaseStageReadinessError,
    review_case_stage_readiness_from_state,
)


def test_stage_readiness_reads_completed_stage_from_raw_state() -> None:
    readiness = review_case_stage_readiness_from_state(
        {
            "stages": {
                "launchpad_builder": {"status": "completed"},
                "candidate": {"status": "pending"},
            }
        }
    )

    assert readiness.is_stage_completed("launchpad_builder") is True
    assert readiness.is_stage_completed("candidate") is False


def test_stage_readiness_handles_missing_raw_state_for_compatibility() -> None:
    readiness = review_case_stage_readiness_from_state({"stages": None})

    assert readiness.is_stage_completed("launchpad_builder") is False


def test_stage_readiness_blocks_candidate_until_builder_is_complete() -> None:
    readiness = review_case_stage_readiness_from_state(
        {"stages": {"launchpad_builder": {"status": "running"}}}
    )

    with pytest.raises(ReviewCaseStageReadinessError) as exc:
        readiness.assert_downstream_stage_ready("candidate")

    assert exc.value.issue.code == "stage_not_ready"
    assert (
        exc.value.issue.message
        == "Candidate generation is not ready until diagnosis and Builder setup are complete."
    )


def test_stage_readiness_blocks_required_previous_stage() -> None:
    readiness = review_case_stage_readiness_from_state(
        {"stages": {"candidate": {"status": "completed"}, "comparison": {"status": "pending"}}}
    )

    with pytest.raises(ReviewCaseStageReadinessError) as exc:
        readiness.assert_downstream_stage_ready("verdict", required_previous="comparison")

    assert exc.value.issue.code == "stage_not_ready"
    assert exc.value.issue.message == (
        "verdict is not ready because comparison has not completed for this review."
    )


def test_stage_readiness_allows_ready_downstream_stage() -> None:
    readiness = review_case_stage_readiness_from_state(
        {"stages": {"candidate": {"status": "completed"}, "comparison": {"status": "completed"}}}
    )

    readiness.assert_downstream_stage_ready("verdict", required_previous="comparison")
