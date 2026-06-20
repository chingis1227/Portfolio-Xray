"""Domain objects for one Portfolio MRI Review Case.

The Review Case model is an internal architecture boundary. It represents the
same staged review that the web API already exposes as ``review_state_v1``, but
keeps the domain rules in a small typed module instead of spreading raw dict
construction across runtime adapters. This module must not change formulas,
public API envelopes, run-local artifact schemas, or frontend routes.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal

from .artifact_manifest import (
    ReviewCaseArtifactManifest,
    ReviewCaseArtifactManifestError,
    review_case_artifact_ref,
)

ReviewCaseMode = Literal["demo_qa", "live"]
ReviewCaseStatus = Literal["pending", "running", "completed", "partial", "blocked", "failed"]
ReviewStageStatus = Literal["pending", "running", "completed", "partial", "blocked", "failed", "skipped"]

REVIEW_CASE_STAGE_NAMES: tuple[str, ...] = (
    "input",
    "data_load",
    "xray",
    "stress",
    "client_fit",
    "problem_classification",
    "launchpad_builder",
    "candidate",
    "comparison",
    "verdict",
    "report",
)

_REVIEW_CASE_STATUSES = {"pending", "running", "completed", "partial", "blocked", "failed"}
_REVIEW_STAGE_STATUSES = _REVIEW_CASE_STATUSES | {"skipped"}
_REVIEW_CASE_MODES = {"demo_qa", "live"}


class ReviewCaseValidationError(ValueError):
    """Raised when a Review Case would violate the safe staged-review contract."""


@dataclass(frozen=True)
class ReviewStage:
    """State for one step in the staged Portfolio MRI review journey."""

    status: ReviewStageStatus = "pending"
    started_at: str | None = None
    completed_at: str | None = None
    artifact_refs: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.status not in _REVIEW_STAGE_STATUSES:
            raise ReviewCaseValidationError(f"Unknown review stage status: {self.status!r}")
        for ref in self.artifact_refs:
            _validate_safe_artifact_ref(ref)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ReviewStage":
        raw_refs = value.get("artifact_refs", [])
        if not isinstance(raw_refs, Sequence) or isinstance(raw_refs, (str, bytes)):
            raise ReviewCaseValidationError("Review stage artifact_refs must be a list of strings.")
        return cls(
            status=_stage_status(value.get("status")),
            started_at=_optional_text(value.get("started_at")),
            completed_at=_optional_text(value.get("completed_at")),
            artifact_refs=tuple(_safe_text_ref(ref) for ref in raw_refs),
        )

    def to_staged_state_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "artifact_refs": list(self.artifact_refs),
        }


@dataclass(frozen=True)
class ReviewCase:
    """Internal domain representation of one run-local staged web review."""

    review_id: str
    status: ReviewCaseStatus
    current_stage: str
    mode: ReviewCaseMode
    owner_id: str
    created_at: str | None
    updated_at: str | None
    stages: Mapping[str, ReviewStage]
    artifacts: Mapping[str, str] = field(default_factory=dict)
    provider_status: Mapping[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    safe_error: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.review_id.strip():
            raise ReviewCaseValidationError("Review Case requires a review_id.")
        if self.status not in _REVIEW_CASE_STATUSES:
            raise ReviewCaseValidationError(f"Unknown review status: {self.status!r}")
        if self.current_stage not in REVIEW_CASE_STAGE_NAMES:
            raise ReviewCaseValidationError(f"Unknown current review stage: {self.current_stage!r}")
        if self.mode not in _REVIEW_CASE_MODES:
            raise ReviewCaseValidationError(f"Unknown review mode: {self.mode!r}")
        if not self.owner_id.strip():
            raise ReviewCaseValidationError("Review Case requires an owner_id.")
        if tuple(self.stages.keys()) != REVIEW_CASE_STAGE_NAMES:
            raise ReviewCaseValidationError("Review Case stages must match the canonical staged-review order.")
        try:
            artifacts = ReviewCaseArtifactManifest.from_mapping(self.artifacts).to_public_artifacts_map()
        except ReviewCaseArtifactManifestError as exc:
            raise ReviewCaseValidationError(str(exc)) from exc
        object.__setattr__(self, "artifacts", artifacts)
        for warning in self.warnings:
            if not isinstance(warning, str):
                raise ReviewCaseValidationError("Review Case warnings must be strings.")

    @classmethod
    def initial(
        cls,
        review_id: str,
        *,
        mode: ReviewCaseMode,
        owner_id: str | None = None,
        now: str,
        provider_status: Mapping[str, Any],
        artifacts: Mapping[str, str] | None = None,
    ) -> "ReviewCase":
        """Create the initial Review Case state for ``POST /reviews/staged``."""

        stages = {
            stage: ReviewStage(status="pending", started_at=None, completed_at=None, artifact_refs=())
            for stage in REVIEW_CASE_STAGE_NAMES
        }
        stages["input"] = ReviewStage(
            status="running",
            started_at=now,
            completed_at=None,
            artifact_refs=("payload.json",),
        )
        return cls(
            review_id=review_id,
            status="running",
            current_stage="input",
            mode=mode,
            owner_id=owner_id or "local-dev-user",
            created_at=now,
            updated_at=now,
            stages=stages,
            artifacts=dict(artifacts or {}),
            provider_status=dict(provider_status),
            warnings=(),
            safe_error=None,
        )

    @classmethod
    def from_staged_state_dict(
        cls,
        value: Mapping[str, Any],
        *,
        expected_schema_version: str,
    ) -> "ReviewCase":
        """Load a Review Case from the existing public ``review_state_v1`` shape."""

        if value.get("schema_version") != expected_schema_version:
            raise ReviewCaseValidationError("Run-local review state has an unexpected schema version.")
        raw_stages = value.get("stages")
        if not isinstance(raw_stages, Mapping):
            raise ReviewCaseValidationError("Run-local review state is missing stages.")
        stages = {
            stage: ReviewStage.from_mapping(_mapping(raw_stages.get(stage), f"stage {stage!r}"))
            for stage in REVIEW_CASE_STAGE_NAMES
        }
        return cls(
            review_id=_required_text(value.get("review_id"), "review_id"),
            status=_case_status(value.get("status")),
            current_stage=_required_text(value.get("current_stage"), "current_stage"),
            mode=_mode(value.get("mode")),
            owner_id=_required_text(value.get("owner_id"), "owner_id"),
            created_at=_optional_text(value.get("created_at")),
            updated_at=_optional_text(value.get("updated_at")),
            stages=stages,
            artifacts=_artifact_manifest(value.get("artifacts")),
            provider_status=dict(_mapping(value.get("provider_status"), "provider_status")),
            warnings=tuple(_warnings(value.get("warnings"))),
            safe_error=dict(value["safe_error"]) if isinstance(value.get("safe_error"), Mapping) else None,
        )

    def to_staged_state_dict(self, *, schema_version: str) -> dict[str, Any]:
        """Serialize to the public run-local staged-review state shape."""

        return {
            "schema_version": schema_version,
            "review_id": self.review_id,
            "status": self.status,
            "current_stage": self.current_stage,
            "mode": self.mode,
            "owner_id": self.owner_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "stages": {
                stage: self.stages[stage].to_staged_state_dict()
                for stage in REVIEW_CASE_STAGE_NAMES
            },
            "artifacts": dict(self.artifacts),
            "provider_status": dict(self.provider_status),
            "warnings": list(self.warnings),
            "safe_error": dict(self.safe_error) if self.safe_error is not None else None,
        }


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ReviewCaseValidationError("Expected a string or null value.")
    return value


def _required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReviewCaseValidationError(f"Review Case requires {field_name}.")
    return value


def _safe_text_ref(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReviewCaseValidationError("Artifact refs must be non-empty strings.")
    _validate_safe_artifact_ref(value)
    return value


def _case_status(value: Any) -> ReviewCaseStatus:
    text = _required_text(value, "status")
    if text not in _REVIEW_CASE_STATUSES:
        raise ReviewCaseValidationError(f"Unknown review status: {text!r}")
    return text  # type: ignore[return-value]


def _stage_status(value: Any) -> ReviewStageStatus:
    text = _required_text(value, "stage status")
    if text not in _REVIEW_STAGE_STATUSES:
        raise ReviewCaseValidationError(f"Unknown review stage status: {text!r}")
    return text  # type: ignore[return-value]


def _mode(value: Any) -> ReviewCaseMode:
    text = _required_text(value, "mode")
    if text not in _REVIEW_CASE_MODES:
        raise ReviewCaseValidationError(f"Unknown review mode: {text!r}")
    return text  # type: ignore[return-value]


def _mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ReviewCaseValidationError(f"Review Case requires mapping field {field_name}.")
    return value


def _artifact_manifest(value: Any) -> dict[str, str]:
    if value is None:
        return {}
    raw = _mapping(value, "artifacts")
    try:
        return ReviewCaseArtifactManifest.from_mapping(raw).to_public_artifacts_map()
    except ReviewCaseArtifactManifestError as exc:
        raise ReviewCaseValidationError(str(exc)) from exc


def _warnings(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ReviewCaseValidationError("Review Case warnings must be a list of strings.")
    return [_required_text(item, "warning") for item in value]


def _validate_safe_artifact_ref(ref: str) -> None:
    try:
        review_case_artifact_ref(ref)
    except ReviewCaseArtifactManifestError as exc:
        raise ReviewCaseValidationError(str(exc)) from exc
