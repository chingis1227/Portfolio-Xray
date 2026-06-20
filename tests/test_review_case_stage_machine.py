from __future__ import annotations

import pytest

from src.review_case import (
    ReviewCaseStageMachine,
    ReviewCaseStageTransitionError,
    StageTransition,
)


def _machine(now: str = "2026-06-19T14:00:00Z") -> ReviewCaseStageMachine:
    return ReviewCaseStageMachine(
        clock=lambda: now,
        artifact_ref_sanitizer=lambda ref, stage: (
            str(ref).replace("\\", "/")
            if isinstance(ref, str) and not str(ref).startswith("C:")
            else f"logical://{stage}"
        ),
    )


def test_stage_machine_starts_stage_and_records_current_stage() -> None:
    state: dict[str, object] = {"stages": {"input": {"status": "pending"}}}

    _machine().apply_to_staged_state(state, StageTransition(stage="input", status="running"))

    assert state["current_stage"] == "input"
    assert state["stages"]["input"] == {
        "status": "running",
        "started_at": "2026-06-19T14:00:00Z",
    }


def test_stage_machine_completes_stage_without_overwriting_started_at() -> None:
    state: dict[str, object] = {
        "stages": {
            "xray": {
                "status": "running",
                "started_at": "2026-06-19T13:59:00Z",
                "artifact_refs": [],
            }
        }
    }

    _machine().apply_to_staged_state(
        state,
        StageTransition(
            stage="xray",
            status="completed",
            artifact_refs=["analysis_subject\\portfolio_xray.json"],
        ),
    )

    assert state["current_stage"] == "xray"
    assert state["stages"]["xray"] == {
        "status": "completed",
        "started_at": "2026-06-19T13:59:00Z",
        "completed_at": "2026-06-19T14:00:00Z",
        "artifact_refs": ["analysis_subject/portfolio_xray.json"],
    }


def test_stage_machine_handles_missing_stages_mapping_for_raw_compatibility() -> None:
    state: dict[str, object] = {}

    _machine().apply_to_staged_state(
        state,
        StageTransition(stage="candidate", status="blocked", artifact_refs=["C:/secret.json"]),
    )

    assert state["current_stage"] == "candidate"
    assert state["stages"]["candidate"] == {
        "status": "blocked",
        "started_at": "2026-06-19T14:00:00Z",
        "completed_at": "2026-06-19T14:00:00Z",
        "artifact_refs": ["logical://candidate"],
    }


@pytest.mark.parametrize(
    ("stage", "status"),
    [
        ("unknown", "running"),
        ("input", "unknown"),
    ],
)
def test_stage_machine_rejects_unknown_stage_or_status(stage: str, status: str) -> None:
    with pytest.raises(ReviewCaseStageTransitionError):
        _machine().apply_to_staged_state(
            {"stages": {}},
            StageTransition(stage=stage, status=status),  # type: ignore[arg-type]
        )
