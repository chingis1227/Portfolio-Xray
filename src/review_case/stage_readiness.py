"""Downstream stage readiness rules for staged Review Cases.

This helper keeps behavior-preserving readiness checks close to the Review Case
architecture while the public FastAPI routes continue to own response envelopes.
It intentionally reads the existing raw ``review_state_v1`` dictionary shape so
older run-local state can still pass through compatibility and sanitization
paths.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ReviewCaseStageReadinessIssue:
    """Public-safe reason a downstream Review Case stage is not ready."""

    code: str
    message: str


class ReviewCaseStageReadinessError(ValueError):
    """Raised when a downstream Review Case stage is not ready."""

    def __init__(self, issue: ReviewCaseStageReadinessIssue) -> None:
        super().__init__(issue.message)
        self.issue = issue


@dataclass(frozen=True)
class ReviewCaseStageReadiness:
    """Read downstream stage readiness from an existing staged-state mapping."""

    state: Mapping[str, Any]

    def is_stage_completed(self, stage: str) -> bool:
        """Return whether ``stage`` is marked completed in raw staged state."""

        return _text(_record(_record(self.state.get("stages")).get(stage)).get("status")) == "completed"

    def assert_downstream_stage_ready(
        self,
        stage: str,
        *,
        required_previous: str | None = None,
    ) -> None:
        """Raise a public-safe issue when ``stage`` cannot run yet."""

        if required_previous and not self.is_stage_completed(required_previous):
            raise ReviewCaseStageReadinessError(
                ReviewCaseStageReadinessIssue(
                    code="stage_not_ready",
                    message=f"{stage} is not ready because {required_previous} has not completed for this review.",
                )
            )
        if stage == "candidate" and not self.is_stage_completed("launchpad_builder"):
            raise ReviewCaseStageReadinessError(
                ReviewCaseStageReadinessIssue(
                    code="stage_not_ready",
                    message="Candidate generation is not ready until diagnosis and Builder setup are complete.",
                )
            )


def review_case_stage_readiness_from_state(state: Mapping[str, Any]) -> ReviewCaseStageReadiness:
    """Create a readiness helper for the existing raw staged-state shape."""

    return ReviewCaseStageReadiness(state=state)


def _record(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None
