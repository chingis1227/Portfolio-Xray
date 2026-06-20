"""Downstream evidence-chain context projection for staged Review Cases.

This helper keeps the bounded comparison, verdict, and report context parsing
close to the Review Case architecture while FastAPI route adapters continue to
own public Pydantic response models. It intentionally consumes the existing
generated artifact dictionaries and serializes to the same public field names
without changing generated artifact schemas or API envelopes.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from typing import Any


DEFAULT_RECOMMENDATION_BOUNDARY = (
    "Decision Verdict is non-binding decision support and does not execute trades."
)


@dataclass(frozen=True)
class ReviewCaseDownstreamEvidenceChainContext:
    """Bounded display context linking downstream stages to diagnosis evidence."""

    selected_diagnosis_id: str | None = None
    selected_diagnosis_label: str | None = None
    selected_diagnosis_role: str | None = None
    diagnosis_statement: str | None = None
    tested_hypothesis: str | None = None
    success_criteria: list[str] = field(default_factory=list)
    tradeoff_to_watch: str | None = None
    candidate_boundary: str | None = None
    recommendation_boundary: str | None = None
    source_artifacts: list[str] = field(default_factory=list)

    def to_public_dict(self) -> dict[str, Any]:
        """Return the existing public FastAPI evidence-chain field shape."""

        return asdict(self)


def review_case_downstream_evidence_chain_context(
    candidate_generation: Mapping[str, Any],
    *,
    comparison_row: Mapping[str, Any] | None = None,
    verdict: Mapping[str, Any] | None = None,
    ai_context: Mapping[str, Any] | None = None,
) -> ReviewCaseDownstreamEvidenceChainContext:
    """Build bounded downstream evidence context from existing artifact dictionaries."""

    candidate = _record(candidate_generation.get("candidate"))
    row = _record(comparison_row)
    verdict_row = _record(verdict)
    ai_row = _record(ai_context)
    source_artifacts = _dedupe_text(
        _string_list(candidate_generation.get("source_artifacts"))
        + _string_list(row.get("source_artifacts"))
        + list(_record(ai_row.get("source_artifacts")).keys())
    )
    if not source_artifacts:
        source_artifacts = [
            "problem_classification.json",
            "candidate_generation.json",
            "current_vs_candidate.json",
        ]
        if verdict_row:
            source_artifacts.append("decision_verdict.json")
        if ai_row:
            source_artifacts.append("ai_commentary_context.json")

    return ReviewCaseDownstreamEvidenceChainContext(
        selected_diagnosis_id=_text(
            candidate.get("source_diagnosis_id"),
            row.get("source_diagnosis_id"),
            row.get("diagnosis_id"),
            verdict_row.get("source_diagnosis_id"),
        ),
        selected_diagnosis_label=_text(
            candidate.get("source_diagnosis_label"),
            row.get("source_diagnosis_label"),
            row.get("diagnosis_label"),
        ),
        selected_diagnosis_role=_text(
            candidate.get("source_diagnosis_role"),
            row.get("source_diagnosis_role"),
        ),
        diagnosis_statement=_text(
            candidate.get("source_diagnosis_statement"),
            row.get("diagnosis_statement"),
            verdict_row.get("diagnosis_statement"),
        ),
        tested_hypothesis=_text(
            candidate.get("hypothesis_to_test"),
            row.get("hypothesis_to_test"),
            verdict_row.get("hypothesis_tested"),
        ),
        success_criteria=_dedupe_text(
            _string_list(candidate.get("success_criteria"))
            + _as_text_list(row.get("success_criteria"), fallback_field="criterion")
            + _as_text_list(row.get("success_criteria_result"), fallback_field="criterion")
        )[:8],
        tradeoff_to_watch=_text(candidate.get("tradeoff_to_watch"), row.get("tradeoff_to_watch")),
        candidate_boundary=_text(
            candidate.get("decision_boundary"),
            candidate.get("candidate_boundary"),
            row.get("candidate_boundary"),
        ),
        recommendation_boundary=_text(
            candidate.get("decision_boundary"),
            verdict_row.get("recommendation_boundary"),
            verdict_row.get("decision_boundary"),
        )
        or DEFAULT_RECOMMENDATION_BOUNDARY,
        source_artifacts=source_artifacts[:10],
    )


def _record(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _text(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _string_list(value: Any) -> list[str]:
    return [str(item).strip() for item in _list(value) if item is not None and str(item).strip()]


def _as_text_list(items: Any, *, fallback_field: str = "label") -> list[str]:
    result: list[str] = []
    for item in _list(items):
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
        elif isinstance(item, Mapping):
            text = _text(
                item.get(fallback_field),
                item.get("summary"),
                item.get("field"),
                item.get("criterion"),
                item.get("reason"),
            )
            if text:
                result.append(text)
    return result


def _dedupe_text(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = str(item or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result
