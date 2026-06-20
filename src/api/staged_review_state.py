"""Run-local staged-review state helpers for FastAPI review routes.

The public staged-review routes still live in ``src.api.reviews``. This module
keeps the behavior-preserving state concerns in one place: reading and writing
``review_state.json``, enforcing owner checks, sanitizing raw artifact refs for
public responses, and building the safe staged status envelopes.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from scripts.run_review_from_payload import safe_review_run_dir, scrub_failure_text, write_json
from src.api.models import (
    API_VERSION,
    StagedProviderStatus,
    StagedReviewMode,
    StagedReviewStatusResponse,
    StagedSafeError,
    StagedStageName,
    StagedStageState,
)
from src.review_case import (
    REVIEW_CASE_STAGE_NAMES,
    ReviewCase,
    ReviewCaseScreenReadModel,
)
from src.review_case.repository import staged_state_path

SAFE_REF_RE = re.compile(r"^[A-Za-z]:[\\/]|^/(...:Users|home|var|tmp|mnt)/")


@dataclass(frozen=True)
class ReviewAccessError(Exception):
    """Public-safe authorization or lineage failure for a run-local review."""

    status_code: int
    code: str
    message: str


def utc_now_iso() -> str:
    """Return the current UTC timestamp in the existing staged-state format."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def record(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def list_value(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def text(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def string_list(value: Any) -> list[str]:
    return [str(item).strip() for item in list_value(value) if item is not None and str(item).strip()]


def safe_ref(value: Any, *, fallback: str) -> str:
    """Sanitize refs using the legacy FastAPI public-ref compatibility rule."""

    if not isinstance(value, str) or not value.strip():
        return fallback
    ref = value.strip().replace("\\", "/")
    if SAFE_REF_RE.search(ref):
        return fallback
    return ref


def safe_staged_ref(value: Any, *, fallback: str) -> str:
    """Return a public-safe staged artifact ref without changing legacy relative refs."""

    ref = safe_ref(value, fallback=fallback)
    normalized = ref.replace("\\", "/")
    if Path(normalized).is_absolute() or normalized.startswith("/") or SAFE_REF_RE.search(normalized):
        return fallback
    return normalized


def read_json_file(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} is not a JSON object.")
    return data


@dataclass(frozen=True)
class StagedReviewStateStore:
    """Behavior-preserving run-local ``review_state.json`` adapter."""

    schema_version: str

    def path(self, run_dir: Path) -> Path:
        return staged_state_path(run_dir)

    def write(self, run_dir: Path, state: dict[str, Any]) -> None:
        state["updated_at"] = utc_now_iso()
        temp_path = run_dir / "review_state.json.tmp"
        write_json(temp_path, state)
        temp_path.replace(self.path(run_dir))

    def read(self, run_dir: Path) -> dict[str, Any]:
        state = read_json_file(self.path(run_dir))
        if state.get("schema_version") != self.schema_version:
            raise ValueError(f"Run-local review_state.json is not {self.schema_version}.")
        return state

    def read_optional(self, run_dir: Path) -> dict[str, Any] | None:
        try:
            if not self.path(run_dir).is_file():
                return None
            return self.read(run_dir)
        except (FileNotFoundError, ValueError):
            return None

    def assert_owner(self, state: dict[str, Any] | None, owner_id: str | None) -> None:
        stored_owner = text(record(state or {}).get("owner_id"))
        if not stored_owner:
            raise ReviewAccessError(
                403,
                "review_forbidden",
                "Review owner is missing; restart the review.",
            )
        if not owner_id or stored_owner != owner_id:
            raise ReviewAccessError(
                403,
                "review_forbidden",
                "Review belongs to a different authenticated user.",
            )

    def read_authorized(self, review_id: str, owner_id: str | None) -> tuple[Path, dict[str, Any]]:
        run_dir = safe_review_run_dir(review_id)
        state = self.read(run_dir)
        self.assert_owner(state, owner_id)
        return run_dir, state

    def authorize_owner(self, review_id: str, owner_id: str | None) -> None:
        run_dir = safe_review_run_dir(review_id)
        state = self.read_optional(run_dir)
        self.assert_owner(state, owner_id)

    def exists(self, run_dir: Path) -> bool:
        return self.path(run_dir).is_file()


def staged_safe_error(
    *,
    code: str,
    message: str,
    user_action: str,
    retryable: bool,
    stage: StagedStageName | None,
) -> StagedSafeError:
    return StagedSafeError(
        code=code,  # type: ignore[arg-type]
        message=scrub_failure_text(message),
        user_action=user_action,  # type: ignore[arg-type]
        retryable=retryable,
        stage=stage,
    )


@dataclass(frozen=True)
class ReviewCaseStatusProjection:
    """Internal staged-status projection bundle for Review Case migration work.

    ``public_status`` is the existing FastAPI response envelope. ``screen_read_model``
    is the additive internal read model built from that sanitized public response.
    Callers must keep returning ``public_status`` until a separate public contract
    migration explicitly changes the staged status API.
    """

    public_status: StagedReviewStatusResponse
    screen_read_model: ReviewCaseScreenReadModel


def review_case_screen_read_model_from_public_status(
    status: StagedReviewStatusResponse,
    *,
    owner_id: str = "public-status-projection",
) -> ReviewCaseScreenReadModel:
    """Project a public-safe staged status response into the internal screen read model.

    This is a behavior-preserving migration adapter: callers keep returning the
    existing ``StagedReviewStatusResponse`` envelope, while tests and later API
    adapters can prove the sanitized public status is also compatible with the
    typed Review Case screen read-model seam.
    """

    raw_status = status.model_dump(mode="json")
    source_stages = record(raw_status.get("stages"))
    canonical_stages = {
        stage: {
            "status": text(record(source_stages.get(stage)).get("status"), "pending") or "pending",
            "started_at": text(record(source_stages.get(stage)).get("started_at")),
            "completed_at": text(record(source_stages.get(stage)).get("completed_at")),
            "artifact_refs": string_list(record(source_stages.get(stage)).get("artifact_refs")),
        }
        for stage in REVIEW_CASE_STAGE_NAMES
    }
    case_state = {
        "schema_version": status.schema_version,
        "review_id": status.review_id,
        "status": status.status,
        "current_stage": status.current_stage,
        "mode": status.mode,
        "owner_id": owner_id,
        "created_at": status.created_at,
        "updated_at": status.updated_at,
        "stages": canonical_stages,
        "artifacts": dict(status.artifacts),
        "provider_status": status.provider_status.model_dump(mode="json"),
        "warnings": list(status.warnings),
        "safe_error": status.safe_error.model_dump(mode="json") if status.safe_error is not None else None,
    }
    review_case = ReviewCase.from_staged_state_dict(
        case_state,
        expected_schema_version=status.schema_version,
    )
    return ReviewCaseScreenReadModel.from_review_case(review_case)


def review_case_screen_read_model_from_state(
    state: dict[str, Any],
    *,
    schema_version: str,
    initial_provider_status: Mapping[StagedReviewMode, StagedProviderStatus],
    owner_id: str = "public-status-projection",
) -> ReviewCaseScreenReadModel:
    """Project raw staged state through public sanitization into the screen read model."""

    return review_case_status_projection_from_state(
        state,
        schema_version=schema_version,
        initial_provider_status=initial_provider_status,
        owner_id=owner_id,
    ).screen_read_model


def review_case_status_projection_from_state(
    state: dict[str, Any],
    *,
    schema_version: str,
    initial_provider_status: Mapping[StagedReviewMode, StagedProviderStatus],
    owner_id: str = "public-status-projection",
) -> ReviewCaseStatusProjection:
    """Build the public staged status and internal screen read model together.

    This is the behavior-preserving API-side migration seam after Session 25:
    raw run-local state is sanitized once into the existing public status
    response, then the internal Review Case read model is derived from that
    public-safe envelope. The returned ``public_status`` remains the only value
    exposed by current FastAPI routes.
    """

    public_status = public_staged_status_from_state(
        state,
        schema_version=schema_version,
        initial_provider_status=initial_provider_status,
    )
    return ReviewCaseStatusProjection(
        public_status=public_status,
        screen_read_model=review_case_screen_read_model_from_public_status(
            public_status,
            owner_id=owner_id,
        ),
    )


def public_staged_status_from_state(
    state: dict[str, Any],
    *,
    schema_version: str,
    initial_provider_status: Mapping[StagedReviewMode, StagedProviderStatus],
) -> StagedReviewStatusResponse:
    raw_mode = text(state.get("mode"), "live") or "live"
    mode: StagedReviewMode = "demo_qa" if raw_mode == "demo_qa" else "live"
    stages: dict[str, StagedStageState] = {}
    for stage, raw_row in record(state.get("stages")).items():
        row = record(raw_row)
        refs = [
            safe_staged_ref(ref, fallback=f"logical://{stage}")
            for ref in list_value(row.get("artifact_refs"))
        ]
        stages[str(stage)] = StagedStageState(
            status=text(row.get("status"), "pending") or "pending",  # type: ignore[arg-type]
            started_at=text(row.get("started_at")),
            completed_at=text(row.get("completed_at")),
            artifact_refs=refs,
        )
    artifacts = {
        str(key): safe_staged_ref(value, fallback=f"logical://{key}")
        for key, value in record(state.get("artifacts")).items()
    }
    provider_status = StagedProviderStatus(
        **record(state.get("provider_status") or initial_provider_status[mode].model_dump(mode="json"))
    )
    safe_error = None
    if isinstance(state.get("safe_error"), dict):
        raw_error = record(state.get("safe_error"))
        safe_error = staged_safe_error(
            code=text(raw_error.get("code"), "PYTHON_STAGE_FAILED") or "PYTHON_STAGE_FAILED",
            message=text(raw_error.get("message"), "Staged review failed.") or "Staged review failed.",
            user_action=text(raw_error.get("user_action"), "retry") or "retry",
            retryable=bool(raw_error.get("retryable")),
            stage=text(raw_error.get("stage")) or None,  # type: ignore[arg-type]
        )
    current_stage = text(state.get("current_stage"), "input") or "input"
    return StagedReviewStatusResponse(
        api_version=API_VERSION,
        schema_version=schema_version,
        review_id=text(state.get("review_id"), "unknown") or "unknown",
        stage="diagnosis",
        status=text(state.get("status"), "running") or "running",  # type: ignore[arg-type]
        current_stage=current_stage,  # type: ignore[arg-type]
        mode=mode,
        created_at=text(state.get("created_at")),
        updated_at=text(state.get("updated_at")),
        stages=stages,
        artifacts=artifacts,
        provider_status=provider_status,
        warnings=string_list(state.get("warnings")),
        safe_error=safe_error,
    )


def staged_status_not_found(
    review_id: str,
    message: str,
    *,
    schema_version: str,
    initial_provider_status: StagedProviderStatus,
) -> StagedReviewStatusResponse:
    now = utc_now_iso()
    return StagedReviewStatusResponse(
        api_version=API_VERSION,
        schema_version=schema_version,
        review_id=review_id,
        stage="diagnosis",
        status="failed",
        current_stage="input",
        mode="live",
        created_at=None,
        updated_at=now,
        stages={},
        artifacts={},
        provider_status=initial_provider_status,
        warnings=[],
        safe_error=staged_safe_error(
            code="ARTIFACT_MISSING",
            message=message,
            user_action="none",
            retryable=False,
            stage="input",
        ),
    )
