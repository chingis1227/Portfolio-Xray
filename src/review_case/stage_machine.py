"""Stage transition rules for Portfolio MRI Review Cases.

The state machine is an internal architecture seam for the existing
``review_state_v1`` shape. It centralizes how a staged review row moves between
``pending``, ``running``, terminal, and compatibility statuses without changing
public FastAPI envelopes, generated artifact schemas, or the raw-dict
compatibility paths that still sanitize older run-local state.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, MutableMapping, Sequence
from dataclasses import dataclass
from typing import Any

from .domain import REVIEW_CASE_STAGE_NAMES, ReviewStageStatus

_STARTED_STAGE_STATUSES = frozenset({"running", "completed", "partial", "blocked", "failed"})
_COMPLETED_STAGE_STATUSES = frozenset({"completed", "partial", "blocked", "failed", "skipped"})
_VALID_STAGE_STATUSES = _STARTED_STAGE_STATUSES | _COMPLETED_STAGE_STATUSES | {"pending"}


class ReviewCaseStageTransitionError(ValueError):
    """Raised when a Review Case stage transition request is not valid."""


@dataclass(frozen=True)
class StageTransition:
    """Requested status update for one canonical Review Case stage."""

    stage: str
    status: ReviewStageStatus
    artifact_refs: Sequence[Any] | None = None


class ReviewCaseStageMachine:
    """Apply narrow stage/status transitions to the current staged-state shape."""

    def __init__(
        self,
        *,
        clock: Callable[[], str],
        artifact_ref_sanitizer: Callable[[Any, str], str] | None = None,
    ) -> None:
        self._clock = clock
        self._artifact_ref_sanitizer = artifact_ref_sanitizer or self._default_artifact_ref_sanitizer

    def apply_to_staged_state(
        self,
        state: MutableMapping[str, Any],
        transition: StageTransition,
    ) -> None:
        """Apply ``transition`` in-place to an existing ``review_state_v1`` dict.

        The method intentionally validates only the requested stage/status and
        the row it updates. It does not parse the entire Review Case domain
        object, so old run-local raw dictionaries can still flow through public
        sanitization paths before later migration sessions tighten them.
        """

        stage = _canonical_stage(transition.stage)
        status = _stage_status(transition.status)
        now = self._clock()

        stages = self._stages_mapping(state)
        row = self._stage_row(stages.get(stage))

        if not row.get("started_at") and status in _STARTED_STAGE_STATUSES:
            row["started_at"] = now
        if status in _COMPLETED_STAGE_STATUSES:
            row["completed_at"] = now
        row["status"] = status
        if transition.artifact_refs is not None:
            row["artifact_refs"] = [
                self._artifact_ref_sanitizer(ref, stage) for ref in transition.artifact_refs
            ]

        stages[stage] = row
        state["stages"] = stages
        state["current_stage"] = stage

    @staticmethod
    def _stages_mapping(state: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
        raw_stages = state.get("stages")
        if isinstance(raw_stages, MutableMapping):
            return raw_stages
        return {}

    @staticmethod
    def _stage_row(value: Any) -> dict[str, Any]:
        if isinstance(value, Mapping):
            return dict(value)
        return {}

    @staticmethod
    def _default_artifact_ref_sanitizer(value: Any, stage: str) -> str:
        if isinstance(value, str) and value.strip():
            return value.strip()
        return f"logical://{stage}"


def _canonical_stage(value: Any) -> str:
    if not isinstance(value, str) or value not in REVIEW_CASE_STAGE_NAMES:
        raise ReviewCaseStageTransitionError(f"Unknown Review Case stage: {value!r}")
    return value


def _stage_status(value: Any) -> ReviewStageStatus:
    if not isinstance(value, str) or value not in _VALID_STAGE_STATUSES:
        raise ReviewCaseStageTransitionError(f"Unknown Review Case stage status: {value!r}")
    return value  # type: ignore[return-value]
