"""Downstream artifact lineage rules for staged Review Cases.

This helper keeps candidate, comparison, and verdict lineage checks close to
the Review Case architecture while FastAPI route adapters continue to own
public response envelopes and safe-error mapping. It intentionally consumes the
existing generated artifact dictionaries so run-local schemas and public API
contracts stay unchanged during the migration.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


class ReviewCaseDownstreamLineageError(ValueError):
    """Raised when downstream generated artifacts do not share one lineage."""


@dataclass(frozen=True)
class ReviewCaseCandidateLineage:
    """Lineage for the active generated candidate."""

    selected_card_id: str
    candidate_id: str


@dataclass(frozen=True)
class ReviewCaseComparisonLineage:
    """Lineage for the active current-vs-candidate comparison."""

    selected_card_id: str
    candidate_id: str
    comparison_id: str


@dataclass(frozen=True)
class ReviewCaseVerdictLineage:
    """Lineage for the active non-binding Decision Verdict."""

    selected_card_id: str
    candidate_id: str
    comparison_id: str
    verdict_id: str


def review_case_comparison_id_for_candidate(candidate_id: str | None) -> str | None:
    """Return the stable comparison id used by current public FastAPI envelopes."""

    return f"current_vs_candidate:{candidate_id}" if candidate_id else None


def review_case_candidate_lineage(
    candidate_generation: Mapping[str, Any],
    requested_candidate_id: str,
) -> ReviewCaseCandidateLineage:
    """Validate that ``requested_candidate_id`` is the active generated candidate."""

    candidate = _record(candidate_generation.get("candidate"))
    actual_candidate_id = _text(candidate.get("candidate_id"))
    if not actual_candidate_id:
        raise ReviewCaseDownstreamLineageError("candidate_generation.candidate.candidate_id is required.")
    if actual_candidate_id != requested_candidate_id:
        raise ReviewCaseDownstreamLineageError(
            "Requested candidate_id does not match the active run-local candidate."
        )
    selected_card_id = _text(candidate.get("source_card_id"), candidate_generation.get("selected_card_id"))
    if not selected_card_id:
        raise ReviewCaseDownstreamLineageError(
            "Active candidate does not contain a selected Launchpad card id."
        )
    return ReviewCaseCandidateLineage(
        selected_card_id=selected_card_id,
        candidate_id=actual_candidate_id,
    )


def review_case_comparison_lineage(
    *,
    candidate_generation: Mapping[str, Any],
    current_vs_candidate: Mapping[str, Any],
    requested_comparison_id: str,
) -> ReviewCaseComparisonLineage:
    """Validate that the active comparison belongs to the active candidate."""

    candidate_id = _active_comparison_candidate_id(current_vs_candidate)
    valid_comparison_ids = {
        candidate_id,
        review_case_comparison_id_for_candidate(candidate_id),
        f"comparison:{candidate_id}",
        f"comparison_{candidate_id}",
    }
    if requested_comparison_id not in valid_comparison_ids:
        raise ReviewCaseDownstreamLineageError(
            "Requested comparison_id does not match the active run-local comparison."
        )
    candidate_lineage = review_case_candidate_lineage(candidate_generation, candidate_id)
    if not review_case_comparison_has_displayable_evidence(
        current_vs_candidate,
        candidate_lineage.candidate_id,
    ):
        raise ReviewCaseDownstreamLineageError(
            "Active current-vs-candidate comparison does not contain displayable evidence for the selected candidate."
        )
    return ReviewCaseComparisonLineage(
        selected_card_id=candidate_lineage.selected_card_id,
        candidate_id=candidate_lineage.candidate_id,
        comparison_id=review_case_comparison_id_for_candidate(candidate_lineage.candidate_id)
        or requested_comparison_id,
    )


def review_case_verdict_lineage(
    *,
    candidate_generation: Mapping[str, Any],
    current_vs_candidate: Mapping[str, Any],
    verdict: Mapping[str, Any],
    requested_verdict_id: str,
) -> ReviewCaseVerdictLineage:
    """Validate that the active verdict belongs to the active comparison."""

    actual_verdict_id = _text(verdict.get("verdict_id"))
    if not actual_verdict_id:
        raise ReviewCaseDownstreamLineageError("decision_verdict.json does not contain a verdict_id.")
    if actual_verdict_id != requested_verdict_id:
        raise ReviewCaseDownstreamLineageError(
            "Requested verdict_id does not match the active run-local Decision Verdict."
        )
    candidate_id = _text(verdict.get("reviewed_candidate_id"), verdict.get("selected_candidate_id"))
    if not candidate_id:
        raise ReviewCaseDownstreamLineageError(
            "decision_verdict.json does not contain a reviewed candidate id."
        )
    candidate_lineage = review_case_candidate_lineage(candidate_generation, candidate_id)
    comparison_id = (
        review_case_comparison_id_for_candidate(candidate_lineage.candidate_id)
        or candidate_lineage.candidate_id
    )
    comparison_lineage = review_case_comparison_lineage(
        candidate_generation=candidate_generation,
        current_vs_candidate=current_vs_candidate,
        requested_comparison_id=comparison_id,
    )
    if comparison_lineage.candidate_id != candidate_lineage.candidate_id:
        raise ReviewCaseDownstreamLineageError(
            "Active current-vs-candidate comparison does not match the active Decision Verdict candidate."
        )
    return ReviewCaseVerdictLineage(
        selected_card_id=candidate_lineage.selected_card_id,
        candidate_id=candidate_lineage.candidate_id,
        comparison_id=comparison_lineage.comparison_id,
        verdict_id=actual_verdict_id,
    )


def review_case_comparison_has_displayable_evidence(
    current_vs_candidate: Mapping[str, Any],
    candidate_id: str | None,
) -> bool:
    """Return whether the comparison has at least one displayable metric row."""

    row = _first_comparison_row(current_vs_candidate, candidate_id)
    if not row:
        return False
    dimensions = [_record(item) for item in _list(row.get("dimensions"))]
    for dimension in dimensions:
        status = str(dimension.get("status") or "").strip().lower()
        if status in {"unavailable", "not_available", "missing", "unknown"}:
            continue
        direction = str(dimension.get("direction") or "").strip().lower()
        if (
            dimension.get("baseline_value") is not None
            or dimension.get("candidate_value") is not None
            or dimension.get("delta") is not None
            or (bool(direction) and direction != "unknown")
        ):
            return True
    return False


def _active_comparison_candidate_id(current_vs_candidate: Mapping[str, Any]) -> str:
    selected_ids = [
        str(item).strip()
        for item in _list(current_vs_candidate.get("selected_candidate_ids"))
        if str(item).strip()
    ]
    rows = [_record(item) for item in _list(current_vs_candidate.get("comparisons"))]
    row_ids = [
        str(row.get("candidate_id") or "").strip()
        for row in rows
        if str(row.get("candidate_id") or "").strip()
    ]
    candidate_id = (selected_ids or row_ids or [""])[0]
    if not candidate_id:
        raise ReviewCaseDownstreamLineageError(
            "current_vs_candidate.json does not contain an active selected candidate."
        )
    return candidate_id


def _first_comparison_row(
    current_vs_candidate: Mapping[str, Any],
    candidate_id: str | None,
) -> Mapping[str, Any]:
    rows = [_record(item) for item in _list(current_vs_candidate.get("comparisons"))]
    if candidate_id:
        for row in rows:
            if _text(row.get("candidate_id")) == candidate_id:
                return row
        return {}
    return rows[0] if rows else {}


def _record(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _text(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None
