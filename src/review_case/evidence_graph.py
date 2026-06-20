"""Evidence graph helpers for Portfolio MRI Review Cases.

The evidence graph is an internal architecture seam for relating canonical
Review Case stages, the existing artifact manifest entries, and source
evidence references. It does not change public FastAPI envelopes,
``review_state_v1``, CLI commands, generated artifact schemas, or calculation
logic.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal

from .artifact_manifest import (
    ReviewCaseArtifactManifest,
    ReviewCaseArtifactManifestError,
    review_case_artifact_key,
    review_case_artifact_ref,
)
from .domain import REVIEW_CASE_STAGE_NAMES, ReviewCase

EvidenceNodeKind = Literal["stage", "artifact", "source"]
EvidenceRelationship = Literal[
    "stage_outputs_artifact",
    "stage_uses_source",
    "artifact_uses_source",
    "source_supports_stage",
    "source_supports_artifact",
]

EVIDENCE_GRAPH_SCHEMA_VERSION = "review_case_evidence_graph_v1"

_NODE_KINDS = {"stage", "artifact", "source"}
_RELATIONSHIPS = {
    "stage_outputs_artifact",
    "stage_uses_source",
    "artifact_uses_source",
    "source_supports_stage",
    "source_supports_artifact",
}


class ReviewCaseEvidenceGraphError(ValueError):
    """Raised when a Review Case evidence graph is unsafe or inconsistent."""


@dataclass(frozen=True)
class ReviewCaseEvidenceLink:
    """Directed relation between two Review Case evidence graph nodes."""

    from_node: str
    to_node: str
    relationship: EvidenceRelationship

    def __post_init__(self) -> None:
        _parse_node_ref(self.from_node)
        _parse_node_ref(self.to_node)
        if self.relationship not in _RELATIONSHIPS:
            raise ReviewCaseEvidenceGraphError(
                f"Unknown Review Case evidence relationship: {self.relationship!r}"
            )

    @classmethod
    def stage_outputs_artifact(cls, stage: str, artifact_key: str) -> "ReviewCaseEvidenceLink":
        return cls(
            from_node=review_case_evidence_node_ref("stage", stage),
            to_node=review_case_evidence_node_ref("artifact", artifact_key),
            relationship="stage_outputs_artifact",
        )

    @classmethod
    def stage_uses_source(cls, stage: str, source_id: str) -> "ReviewCaseEvidenceLink":
        return cls(
            from_node=review_case_evidence_node_ref("stage", stage),
            to_node=review_case_evidence_node_ref("source", source_id),
            relationship="stage_uses_source",
        )

    @classmethod
    def artifact_uses_source(cls, artifact_key: str, source_id: str) -> "ReviewCaseEvidenceLink":
        return cls(
            from_node=review_case_evidence_node_ref("artifact", artifact_key),
            to_node=review_case_evidence_node_ref("source", source_id),
            relationship="artifact_uses_source",
        )

    @classmethod
    def source_supports_stage(cls, source_id: str, stage: str) -> "ReviewCaseEvidenceLink":
        return cls(
            from_node=review_case_evidence_node_ref("source", source_id),
            to_node=review_case_evidence_node_ref("stage", stage),
            relationship="source_supports_stage",
        )

    @classmethod
    def source_supports_artifact(cls, source_id: str, artifact_key: str) -> "ReviewCaseEvidenceLink":
        return cls(
            from_node=review_case_evidence_node_ref("source", source_id),
            to_node=review_case_evidence_node_ref("artifact", artifact_key),
            relationship="source_supports_artifact",
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "from": self.from_node,
            "to": self.to_node,
            "relationship": self.relationship,
        }


@dataclass(frozen=True)
class ReviewCaseEvidenceGraph:
    """Internal graph of stages, artifacts, source evidence, and their links."""

    artifact_manifest: ReviewCaseArtifactManifest = field(default_factory=ReviewCaseArtifactManifest)
    sources: Mapping[str, str] = field(default_factory=dict)
    links: Sequence[ReviewCaseEvidenceLink] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        artifact_manifest = _artifact_manifest(self.artifact_manifest)
        try:
            sources = {
                review_case_artifact_key(source_id): review_case_artifact_ref(ref)
                for source_id, ref in self.sources.items()
            }
        except ReviewCaseArtifactManifestError as exc:
            raise ReviewCaseEvidenceGraphError(str(exc)) from exc
        links = tuple(self.links)
        valid_nodes = _valid_nodes(artifact_manifest, sources)
        for link in links:
            if link.from_node not in valid_nodes or link.to_node not in valid_nodes:
                raise ReviewCaseEvidenceGraphError(
                    "Evidence graph links must reference declared stages, artifacts, or sources."
                )
        object.__setattr__(self, "artifact_manifest", artifact_manifest)
        object.__setattr__(self, "sources", sources)
        object.__setattr__(self, "links", links)

    @classmethod
    def from_review_case(
        cls,
        review_case: ReviewCase,
        *,
        sources: Mapping[str, str] | None = None,
        links: Sequence[ReviewCaseEvidenceLink] = (),
    ) -> "ReviewCaseEvidenceGraph":
        """Build a graph from one Review Case's existing artifact manifest."""

        return cls(
            artifact_manifest=ReviewCaseArtifactManifest.from_mapping(review_case.artifacts),
            sources=dict(sources or {}),
            links=links,
        )

    def to_dict(self, *, schema_version: str = EVIDENCE_GRAPH_SCHEMA_VERSION) -> dict[str, Any]:
        """Serialize the internal evidence graph in a stable, testable shape."""

        artifacts = self.artifact_manifest.to_public_artifacts_map()
        nodes: list[dict[str, str]] = [
            {"id": review_case_evidence_node_ref("stage", stage), "kind": "stage", "key": stage}
            for stage in REVIEW_CASE_STAGE_NAMES
        ]
        nodes.extend(
            {
                "id": review_case_evidence_node_ref("artifact", key),
                "kind": "artifact",
                "key": key,
                "ref": artifacts[key],
            }
            for key in sorted(artifacts)
        )
        nodes.extend(
            {
                "id": review_case_evidence_node_ref("source", key),
                "kind": "source",
                "key": key,
                "ref": self.sources[key],
            }
            for key in sorted(self.sources)
        )
        return {
            "schema_version": schema_version,
            "nodes": nodes,
            "links": [link.to_dict() for link in self.links],
        }


def review_case_evidence_node_ref(kind: EvidenceNodeKind, key: Any) -> str:
    """Return a stable evidence graph node reference or raise."""

    if kind not in _NODE_KINDS:
        raise ReviewCaseEvidenceGraphError(f"Unknown evidence node kind: {kind!r}")
    if kind == "stage":
        if not isinstance(key, str) or key not in REVIEW_CASE_STAGE_NAMES:
            raise ReviewCaseEvidenceGraphError(f"Unknown Review Case stage: {key!r}")
        return f"stage:{key}"
    safe_key = review_case_artifact_key(key)
    return f"{kind}:{safe_key}"


def _artifact_manifest(value: Any) -> ReviewCaseArtifactManifest:
    try:
        if isinstance(value, ReviewCaseArtifactManifest):
            return ReviewCaseArtifactManifest.from_mapping(value.to_public_artifacts_map())
        if isinstance(value, Mapping):
            return ReviewCaseArtifactManifest.from_mapping(value)
    except ReviewCaseArtifactManifestError as exc:
        raise ReviewCaseEvidenceGraphError(str(exc)) from exc
    raise ReviewCaseEvidenceGraphError("Evidence graph requires a Review Case artifact manifest.")


def _valid_nodes(
    artifact_manifest: ReviewCaseArtifactManifest,
    sources: Mapping[str, str],
) -> set[str]:
    artifacts = artifact_manifest.to_public_artifacts_map()
    return {
        *(review_case_evidence_node_ref("stage", stage) for stage in REVIEW_CASE_STAGE_NAMES),
        *(review_case_evidence_node_ref("artifact", key) for key in artifacts),
        *(review_case_evidence_node_ref("source", key) for key in sources),
    }


def _parse_node_ref(value: Any) -> tuple[EvidenceNodeKind, str]:
    if not isinstance(value, str) or ":" not in value:
        raise ReviewCaseEvidenceGraphError("Evidence graph node refs must use '<kind>:<key>'.")
    kind, key = value.split(":", 1)
    if kind not in _NODE_KINDS:
        raise ReviewCaseEvidenceGraphError(f"Unknown evidence node kind: {kind!r}")
    if kind == "stage":
        if key not in REVIEW_CASE_STAGE_NAMES:
            raise ReviewCaseEvidenceGraphError(f"Unknown Review Case stage: {key!r}")
        return "stage", key
    try:
        safe_key = review_case_artifact_key(key)
    except ReviewCaseArtifactManifestError as exc:
        raise ReviewCaseEvidenceGraphError(str(exc)) from exc
    return kind, safe_key  # type: ignore[return-value]
