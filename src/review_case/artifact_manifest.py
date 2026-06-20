"""Artifact manifest helpers for Portfolio MRI Review Cases.

The manifest is an internal architecture seam around the existing
``review_state_v1`` ``artifacts`` map. It centralizes safe artifact keys and
run-local artifact references without changing public FastAPI response shapes,
stage ``artifact_refs`` lists, CLI commands, or generated artifact schemas.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_ARTIFACT_KEY_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]*$")
_WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:[\\/]")


class ReviewCaseArtifactManifestError(ValueError):
    """Raised when a Review Case artifact manifest is not safe to store."""


@dataclass(frozen=True)
class ReviewCaseArtifactManifest:
    """Safe key-to-reference map for one Review Case.

    The serialized shape is intentionally just ``dict[str, str]`` so the
    existing public ``review_state_v1`` ``artifacts`` field remains unchanged.
    """

    artifacts: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        normalized: dict[str, str] = {}
        for key, ref in self.artifacts.items():
            normalized[review_case_artifact_key(key)] = review_case_artifact_ref(ref)
        object.__setattr__(self, "artifacts", normalized)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any] | None) -> "ReviewCaseArtifactManifest":
        """Build a manifest from an existing staged-state ``artifacts`` map."""

        if value is None:
            return cls()
        if not isinstance(value, Mapping):
            raise ReviewCaseArtifactManifestError("Review Case artifacts must be a mapping.")
        return cls({key: ref for key, ref in value.items()})  # type: ignore[dict-item]

    @classmethod
    def from_existing_run_local_refs(
        cls,
        run_dir: Path,
        refs: Mapping[str, str],
    ) -> "ReviewCaseArtifactManifest":
        """Build a manifest from known refs that exist under ``run_dir``."""

        root = Path(run_dir)
        existing: dict[str, str] = {}
        for key, ref in refs.items():
            safe_key = review_case_artifact_key(key)
            safe_ref = review_case_artifact_ref(ref)
            if (root / safe_ref).exists():
                existing[safe_key] = safe_ref
        return cls(existing)

    def to_public_artifacts_map(self) -> dict[str, str]:
        """Return the unchanged public ``review_state_v1`` artifacts map."""

        return dict(self.artifacts)


def review_case_artifact_key(value: Any) -> str:
    """Return a safe artifact manifest key or raise."""

    if not isinstance(value, str) or not value.strip():
        raise ReviewCaseArtifactManifestError("Artifact manifest keys must be non-empty strings.")
    key = value.strip()
    if not _ARTIFACT_KEY_RE.fullmatch(key):
        raise ReviewCaseArtifactManifestError("Artifact manifest keys must be stable identifiers.")
    return key


def review_case_artifact_ref(value: Any) -> str:
    """Return a safe run-local or logical artifact reference or raise."""

    if not isinstance(value, str) or not value.strip():
        raise ReviewCaseArtifactManifestError("Artifact refs must be non-empty strings.")
    ref = value.strip().replace("\\", "/")
    if ref.startswith("logical://"):
        return ref
    if _WINDOWS_DRIVE_RE.search(value) or ref.startswith("/"):
        raise ReviewCaseArtifactManifestError("Artifact refs must not expose absolute local paths.")
    if any(part == ".." for part in ref.split("/")):
        raise ReviewCaseArtifactManifestError("Artifact refs must stay within the run-local review folder.")
    return ref
