"""Screen read models for Portfolio MRI Review Cases.

The screen read model is an internal architecture seam for future API and
frontend migration work. It projects a typed ``ReviewCase`` plus an optional
Evidence Graph into stage progress, artifact availability, and evidence links
without changing public FastAPI envelopes, ``review_state_v1``, CLI commands,
or generated artifact schemas.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .domain import REVIEW_CASE_STAGE_NAMES, ReviewCase
from .evidence_graph import (
    EVIDENCE_GRAPH_SCHEMA_VERSION,
    ReviewCaseEvidenceGraph,
)

SCREEN_READ_MODEL_SCHEMA_VERSION = "review_case_screen_read_model_v1"

_TERMINAL_STAGE_STATUSES = frozenset({"completed", "partial", "blocked", "failed", "skipped"})
_AVAILABLE_ARTIFACT_RELATIONSHIPS = frozenset(
    {"stage_outputs_artifact", "source_supports_artifact", "artifact_uses_source"}
)


class ReviewCaseScreenReadModelError(ValueError):
    """Raised when a Review Case cannot be projected safely for screens."""


@dataclass(frozen=True)
class ReviewCaseStageProgress:
    """Screen-facing progress summary for one canonical Review Case stage."""

    stage: str
    status: str
    started_at: str | None
    completed_at: str | None
    artifact_refs: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_started(self) -> bool:
        return self.started_at is not None or self.status in _TERMINAL_STAGE_STATUSES

    @property
    def is_terminal(self) -> bool:
        return self.status in _TERMINAL_STAGE_STATUSES

    @property
    def has_artifacts(self) -> bool:
        return bool(self.artifact_refs)

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "is_started": self.is_started,
            "is_terminal": self.is_terminal,
            "has_artifacts": self.has_artifacts,
            "artifact_refs": list(self.artifact_refs),
        }


@dataclass(frozen=True)
class ReviewCaseArtifactAvailability:
    """Screen-facing availability summary for one manifest artifact."""

    key: str
    ref: str
    producing_stages: tuple[str, ...] = field(default_factory=tuple)
    evidence_source_ids: tuple[str, ...] = field(default_factory=tuple)

    @property
    def available(self) -> bool:
        return bool(self.ref)

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "ref": self.ref,
            "available": self.available,
            "producing_stages": list(self.producing_stages),
            "evidence_source_ids": list(self.evidence_source_ids),
        }


@dataclass(frozen=True)
class ReviewCaseEvidenceLinkReadModel:
    """Screen-facing evidence link between stage, artifact, or source nodes."""

    from_node: str
    to_node: str
    relationship: str

    def to_dict(self) -> dict[str, str]:
        return {
            "from": self.from_node,
            "to": self.to_node,
            "relationship": self.relationship,
        }


@dataclass(frozen=True)
class ReviewCaseScreenReadModel:
    """Internal read model for future Review Case screen projections."""

    review_id: str
    status: str
    current_stage: str
    mode: str
    stages: tuple[ReviewCaseStageProgress, ...]
    artifacts: tuple[ReviewCaseArtifactAvailability, ...]
    evidence_links: tuple[ReviewCaseEvidenceLinkReadModel, ...] = field(default_factory=tuple)
    evidence_sources: Mapping[str, str] = field(default_factory=dict)

    @classmethod
    def from_review_case(
        cls,
        review_case: ReviewCase,
        *,
        evidence_graph: ReviewCaseEvidenceGraph | None = None,
    ) -> "ReviewCaseScreenReadModel":
        """Project one Review Case into a stable, internal screen read model."""

        graph_dict = _evidence_graph_dict(evidence_graph)
        _validate_graph_artifacts_match_case(review_case, graph_dict)

        stage_rows = tuple(
            ReviewCaseStageProgress(
                stage=stage,
                status=review_case.stages[stage].status,
                started_at=review_case.stages[stage].started_at,
                completed_at=review_case.stages[stage].completed_at,
                artifact_refs=tuple(review_case.stages[stage].artifact_refs),
            )
            for stage in REVIEW_CASE_STAGE_NAMES
        )

        graph_links = tuple(
            ReviewCaseEvidenceLinkReadModel(
                from_node=link["from"],
                to_node=link["to"],
                relationship=link["relationship"],
            )
            for link in graph_dict["links"]
        )
        source_refs = _graph_source_refs(graph_dict)
        artifacts = tuple(
            ReviewCaseArtifactAvailability(
                key=key,
                ref=ref,
                producing_stages=tuple(_producing_stages_for_artifact(key, graph_links)),
                evidence_source_ids=tuple(_source_ids_for_artifact(key, graph_links)),
            )
            for key, ref in sorted(review_case.artifacts.items())
        )

        return cls(
            review_id=review_case.review_id,
            status=review_case.status,
            current_stage=review_case.current_stage,
            mode=review_case.mode,
            stages=stage_rows,
            artifacts=artifacts,
            evidence_links=graph_links,
            evidence_sources=source_refs,
        )

    def to_dict(
        self,
        *,
        schema_version: str = SCREEN_READ_MODEL_SCHEMA_VERSION,
    ) -> dict[str, Any]:
        """Serialize the internal read model in a stable, testable shape."""

        terminal_stage_count = sum(1 for stage in self.stages if stage.is_terminal)
        available_artifact_count = sum(1 for artifact in self.artifacts if artifact.available)
        return {
            "schema_version": schema_version,
            "review_id": self.review_id,
            "status": self.status,
            "current_stage": self.current_stage,
            "mode": self.mode,
            "progress": {
                "total_stage_count": len(self.stages),
                "terminal_stage_count": terminal_stage_count,
                "active_stage": self.current_stage,
            },
            "stages": [stage.to_dict() for stage in self.stages],
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "artifact_availability": {
                "available_artifact_count": available_artifact_count,
                "artifact_count": len(self.artifacts),
            },
            "evidence": {
                "sources": dict(self.evidence_sources),
                "links": [link.to_dict() for link in self.evidence_links],
            },
        }


def _evidence_graph_dict(evidence_graph: ReviewCaseEvidenceGraph | None) -> dict[str, Any]:
    if evidence_graph is None:
        return {"schema_version": EVIDENCE_GRAPH_SCHEMA_VERSION, "nodes": [], "links": []}
    graph_dict = evidence_graph.to_dict()
    if graph_dict.get("schema_version") != EVIDENCE_GRAPH_SCHEMA_VERSION:
        raise ReviewCaseScreenReadModelError("Unexpected Review Case evidence graph schema.")
    return graph_dict


def _validate_graph_artifacts_match_case(
    review_case: ReviewCase,
    graph_dict: Mapping[str, Any],
) -> None:
    graph_artifacts = {
        node["key"]: node["ref"]
        for node in graph_dict.get("nodes", [])
        if isinstance(node, Mapping) and node.get("kind") == "artifact"
    }
    if graph_artifacts and graph_artifacts != dict(review_case.artifacts):
        raise ReviewCaseScreenReadModelError(
            "Evidence graph artifacts must match the Review Case artifact manifest."
        )


def _graph_source_refs(graph_dict: Mapping[str, Any]) -> dict[str, str]:
    return {
        node["key"]: node["ref"]
        for node in graph_dict.get("nodes", [])
        if isinstance(node, Mapping) and node.get("kind") == "source"
    }


def _producing_stages_for_artifact(
    artifact_key: str,
    links: tuple[ReviewCaseEvidenceLinkReadModel, ...],
) -> list[str]:
    artifact_node = f"artifact:{artifact_key}"
    stages: list[str] = []
    for link in links:
        if link.relationship != "stage_outputs_artifact" or link.to_node != artifact_node:
            continue
        kind, key = _split_node_ref(link.from_node)
        if kind == "stage" and key not in stages:
            stages.append(key)
    return stages


def _source_ids_for_artifact(
    artifact_key: str,
    links: tuple[ReviewCaseEvidenceLinkReadModel, ...],
) -> list[str]:
    artifact_node = f"artifact:{artifact_key}"
    source_ids: list[str] = []
    for link in links:
        if link.relationship not in _AVAILABLE_ARTIFACT_RELATIONSHIPS:
            continue
        if link.from_node == artifact_node:
            kind, key = _split_node_ref(link.to_node)
        elif link.to_node == artifact_node:
            kind, key = _split_node_ref(link.from_node)
        else:
            continue
        if kind == "source" and key not in source_ids:
            source_ids.append(key)
    return source_ids


def _split_node_ref(value: str) -> tuple[str, str]:
    kind, _, key = value.partition(":")
    return kind, key
