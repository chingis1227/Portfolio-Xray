"""Inactive-by-default artifact storage seam for Review Case artifacts.

The current source of truth for generated artifacts remains the run-local
filesystem under ``runs/frontend_review_*``. This module adds the smallest
safe adapter boundary needed for later S3-compatible or Cloudflare R2 storage
work without uploading files, requiring cloud credentials, changing public API
envelopes, or changing generated artifact schemas.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .artifact_manifest import (
    ReviewCaseArtifactManifest,
    ReviewCaseArtifactManifestError,
    review_case_artifact_key,
    review_case_artifact_ref,
)

_RUN_LOCAL_BACKENDS = {"", "run_local", "run-local", "local", "filesystem", "fs"}
_REMOTE_BACKENDS = {"s3", "s3_compatible", "s3-compatible", "r2", "cloudflare_r2"}
_DEFAULT_KEY_PREFIX = "review-cases"
_REVIEW_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]{1,160}$")
_OBJECT_KEY_SEGMENT_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]+$")


class ReviewCaseArtifactStorageError(ValueError):
    """Raised when Review Case artifact storage input is unsafe."""


@dataclass(frozen=True)
class ReviewCaseArtifactStorageConfig:
    """Validated internal artifact-storage configuration.

    The active backend is intentionally ``run_local`` in this session. Remote
    backend names are recognized only as future intent and produce safe
    warnings plus local fallback metadata.
    """

    backend: str
    requested_backend: str
    key_prefix: str
    bucket_name: str | None = None
    endpoint_url_configured: bool = False
    warnings: tuple[str, ...] = ()

    def operational_metadata(self) -> dict[str, Any]:
        """Return metadata safe for internal logs.

        Bucket names and endpoint URL values are intentionally not included.
        The metadata only records whether those settings were present.
        """

        return {
            "backend": self.backend,
            "requested_backend": self.requested_backend,
            "key_prefix": self.key_prefix,
            "bucket_configured": bool(self.bucket_name),
            "endpoint_url_configured": self.endpoint_url_configured,
            "warnings": list(self.warnings),
        }


class RunLocalReviewCaseArtifactStorage:
    """Default artifact storage adapter backed by existing run-local files."""

    backend = "run_local"

    def artifact_exists(self, run_dir: Path, artifact_ref: str) -> bool:
        """Return whether ``artifact_ref`` exists under ``run_dir``."""

        safe_ref = _storage_artifact_ref(artifact_ref)
        if safe_ref.startswith("logical://"):
            return False
        return (Path(run_dir) / safe_ref).is_file()

    def manifest_from_existing_refs(
        self,
        run_dir: Path,
        refs: Mapping[str, str],
    ) -> ReviewCaseArtifactManifest:
        """Build the current public artifacts map from existing local files."""

        return ReviewCaseArtifactManifest.from_existing_run_local_refs(run_dir, refs)

    def reference_for_artifact(self, run_dir: Path, artifact_key: str, artifact_ref: str) -> str:
        """Return the unchanged safe run-local ref for an existing artifact."""

        review_case_artifact_key(artifact_key)
        safe_ref = _storage_artifact_ref(artifact_ref)
        if safe_ref.startswith("logical://"):
            raise ReviewCaseArtifactStorageError("Logical artifact refs are not run-local files.")
        if not self.artifact_exists(run_dir, safe_ref):
            raise FileNotFoundError(safe_ref)
        return safe_ref


def review_case_artifact_storage_config(
    env: Mapping[str, str] | None = None,
) -> ReviewCaseArtifactStorageConfig:
    """Return validated internal artifact-storage configuration.

    Remote storage is deliberately inactive in this groundwork session. If an
    operator sets an S3-compatible or R2 backend name, the config records that
    intent and falls back to ``run_local`` until a later session implements
    upload/read behavior.
    """

    source = env if env is not None else os.environ
    requested_backend = _clean_env_value(
        source.get("PMRI_REVIEW_CASE_ARTIFACT_STORAGE_BACKEND")
    ).lower()
    warnings: list[str] = []

    if requested_backend in _RUN_LOCAL_BACKENDS:
        backend = "run_local"
    elif requested_backend in _REMOTE_BACKENDS:
        backend = "run_local"
        warnings.append("remote_artifact_storage_inactive")
    else:
        backend = "run_local"
        warnings.append("unsupported_artifact_storage_backend")

    raw_key_prefix = _clean_env_value(
        source.get("PMRI_REVIEW_CASE_ARTIFACT_KEY_PREFIX")
    ) or _DEFAULT_KEY_PREFIX
    try:
        key_prefix = review_case_artifact_key_prefix(raw_key_prefix)
    except ReviewCaseArtifactStorageError:
        key_prefix = _DEFAULT_KEY_PREFIX
        warnings.append("invalid_artifact_key_prefix")

    bucket_name = _clean_env_value(
        source.get("PMRI_REVIEW_CASE_ARTIFACT_BUCKET")
        or source.get("PMRI_REVIEW_CASE_R2_BUCKET")
        or source.get("PMRI_REVIEW_CASE_S3_BUCKET")
    ) or None
    if bucket_name is not None and not _safe_bucket_name(bucket_name):
        bucket_name = None
        warnings.append("invalid_artifact_bucket_name")

    endpoint_url_configured = bool(
        _clean_env_value(
            source.get("PMRI_REVIEW_CASE_ARTIFACT_ENDPOINT_URL")
            or source.get("PMRI_REVIEW_CASE_R2_ENDPOINT_URL")
            or source.get("PMRI_REVIEW_CASE_S3_ENDPOINT_URL")
        )
    )

    return ReviewCaseArtifactStorageConfig(
        backend=backend,
        requested_backend=requested_backend or "run_local",
        key_prefix=key_prefix,
        bucket_name=bucket_name,
        endpoint_url_configured=endpoint_url_configured,
        warnings=tuple(warnings),
    )


def review_case_artifact_storage_backend(env: Mapping[str, str] | None = None) -> str:
    """Return the active Review Case artifact-storage backend."""

    return review_case_artifact_storage_config(env).backend


def review_case_artifact_key_prefix(value: Any) -> str:
    """Return a safe object-key prefix for future remote storage."""

    if not isinstance(value, str) or not value.strip():
        raise ReviewCaseArtifactStorageError("Artifact key prefix must be a non-empty string.")
    prefix = value.strip().replace("\\", "/").strip("/")
    if not prefix:
        raise ReviewCaseArtifactStorageError("Artifact key prefix must be a non-empty string.")
    _validate_object_key_parts(prefix.split("/"), label="Artifact key prefix")
    return prefix


def review_case_artifact_object_key(
    review_id: str,
    artifact_ref: str,
    *,
    key_prefix: str = _DEFAULT_KEY_PREFIX,
) -> str:
    """Build a safe future S3/R2 object key for a run-local artifact ref."""

    safe_review_id = _review_case_storage_review_id(review_id)
    safe_prefix = review_case_artifact_key_prefix(key_prefix)
    safe_ref = _storage_artifact_ref(artifact_ref)
    if safe_ref.startswith("logical://"):
        raise ReviewCaseArtifactStorageError("Logical artifact refs cannot become object keys.")
    _validate_object_key_parts(safe_ref.split("/"), label="Artifact ref")
    return f"{safe_prefix}/{safe_review_id}/{safe_ref}"


def run_local_review_case_artifact_storage(
    env: Mapping[str, str] | None = None,
) -> RunLocalReviewCaseArtifactStorage:
    """Return the active artifact-storage adapter.

    The adapter is always run-local in this session, including when future
    remote backend names are present in the environment.
    """

    review_case_artifact_storage_config(env)
    return RunLocalReviewCaseArtifactStorage()


def _clean_env_value(value: str | None) -> str:
    return (value or "").strip()


def _storage_artifact_ref(value: Any) -> str:
    try:
        return review_case_artifact_ref(value)
    except ReviewCaseArtifactManifestError as exc:
        raise ReviewCaseArtifactStorageError(str(exc)) from exc


def _review_case_storage_review_id(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReviewCaseArtifactStorageError("Review id must be a non-empty string.")
    review_id = value.strip()
    if not _REVIEW_ID_PATTERN.fullmatch(review_id):
        raise ReviewCaseArtifactStorageError("Review id is not safe for artifact storage.")
    return review_id


def _validate_object_key_parts(parts: list[str], *, label: str) -> None:
    if not parts:
        raise ReviewCaseArtifactStorageError(f"{label} must not be empty.")
    for part in parts:
        if part in {"", ".", ".."} or not _OBJECT_KEY_SEGMENT_PATTERN.fullmatch(part):
            raise ReviewCaseArtifactStorageError(f"{label} contains an unsafe object-key segment.")


def _safe_bucket_name(value: str) -> bool:
    try:
        review_case_artifact_key(value)
    except ReviewCaseArtifactManifestError:
        return False
    return True
