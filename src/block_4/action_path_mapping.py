"""Block 4 v3 suggested action path mapping.

Builds per-problem action-path fields and the deduped top-level
``suggested_actions[]`` list from prioritization output.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.block_4.problem_prioritization import ProblemPrioritizationResult
from src.block_4.problem_scoring import ProblemScoreRow, ProblemScoringResult
from src.block_4.problem_taxonomy import (
    PROBLEM_REGISTRY,
    get_action_path,
    get_problem_definition,
    method_suggestions_for_problem,
    reasonable_paths_for_problem,
)

ACTION_PATH_MAPPING_RULESET_VERSION = "block_4_v3_action_path_mapping_v1"


@dataclass(frozen=True)
class SuggestedActionRow:
    action_path_id: str
    label_en: str
    source_problem_ids: tuple[str, ...]
    priority: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_path_id": self.action_path_id,
            "label_en": self.label_en,
            "source_problem_ids": list(self.source_problem_ids),
            "priority": self.priority,
        }


@dataclass
class ActionPathMappingResult:
    primary_problem: dict[str, Any]
    secondary_problems: tuple[dict[str, Any], ...] = ()
    suggested_actions: tuple[SuggestedActionRow, ...] = ()
    problem_rows: tuple[dict[str, Any], ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "primary_problem": self.primary_problem,
            "secondary_problems": list(self.secondary_problems),
            "suggested_actions": [row.to_dict() for row in self.suggested_actions],
            "problems": list(self.problem_rows),
        }


def map_action_paths(
    prioritization: ProblemPrioritizationResult,
    scoring: ProblemScoringResult,
) -> ActionPathMappingResult:
    """Map prioritized problems to ProblemRow action fields and suggested_actions."""
    demoted_symptoms = _demoted_symptom_ids(prioritization)
    primary_score = prioritization.primary_row or scoring.get_row(prioritization.primary_problem_id)
    if primary_score is None:
        raise ValueError(f"Missing score row for primary problem {prioritization.primary_problem_id!r}")

    primary_problem = build_problem_row(
        prioritization.primary_problem_id,
        primary_score,
        role="primary",
        demoted_symptom_ids=demoted_symptoms,
    )

    secondary_problems: list[dict[str, Any]] = []
    for problem_id, score_row in zip(
        prioritization.secondary_problem_ids,
        prioritization.secondary_rows,
    ):
        secondary_problems.append(
            build_problem_row(problem_id, score_row, role="secondary")
        )

    suggested_actions = build_suggested_actions(primary_problem, secondary_problems)
    problem_rows = (primary_problem,) + tuple(secondary_problems)

    return ActionPathMappingResult(
        primary_problem=primary_problem,
        secondary_problems=tuple(secondary_problems),
        suggested_actions=suggested_actions,
        problem_rows=problem_rows,
    )


def build_problem_row(
    problem_id: str,
    score_row: ProblemScoreRow,
    *,
    role: str = "primary",
    demoted_symptom_ids: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Build a v2 ``ProblemRow`` dict with action-path and narrative fields."""
    defn = get_problem_definition(problem_id)
    if defn is None:
        raise ValueError(f"Unknown problem_id {problem_id!r}")

    secondary_action_path_ids = [
        action_id
        for action_id in defn.secondary_action_path_ids
        if action_id != defn.primary_action_path_id
    ]

    row: dict[str, Any] = {
        "problem_id": problem_id,
        "label_en": defn.label_en,
        "diagnosis_role": defn.diagnosis_role,
        "diagnosis_subtypes": list(defn.diagnosis_subtypes),
        "severity": score_row.severity,
        "confidence": score_row.confidence,
        "short_diagnosis_en": _short_diagnosis_en(defn, score_row),
        "why_it_matters_en": _why_it_matters_en(defn),
        "evidence_refs": list(score_row.evidence_refs),
        "negative_evidence_refs": list(score_row.negative_evidence_refs),
        "suggested_action_path_id": defn.primary_action_path_id,
        "secondary_action_path_ids": secondary_action_path_ids,
        "candidate_method_suggestions": [
            dict(item) for item in method_suggestions_for_problem(problem_id)
        ],
        "reasonable_paths_to_test": list(reasonable_paths_for_problem(problem_id)),
        "scoring": score_row.scoring.to_dict(),
    }

    if defn.problem_id_legacy:
        row["problem_id_legacy"] = defn.problem_id_legacy

    overreact = _do_not_overreact_reason_en(
        defn,
        role=role,
        demoted_symptom_ids=demoted_symptom_ids,
    )
    if overreact:
        row["do_not_overreact_reason_en"] = overreact

    if defn.common_false_positive_en:
        row["risk_of_misinterpretation_en"] = defn.common_false_positive_en

    return row


def build_suggested_actions(
    primary_problem: dict[str, Any],
    secondary_problems: list[dict[str, Any]],
) -> tuple[SuggestedActionRow, ...]:
    """Dedupe action paths across primary and secondary problems with stable priority."""
    collected: list[tuple[str, str, list[str]]] = []

    def _append(action_path_id: str, source_problem_id: str) -> None:
        action_path = get_action_path(action_path_id)
        if action_path is None:
            return
        for idx, (existing_id, label_en, sources) in enumerate(collected):
            if existing_id == action_path_id:
                if source_problem_id not in sources:
                    sources.append(source_problem_id)
                return
        collected.append((action_path_id, action_path.label_en, [source_problem_id]))

    _append(
        str(primary_problem["suggested_action_path_id"]),
        str(primary_problem["problem_id"]),
    )
    for secondary in secondary_problems:
        _append(
            str(secondary["suggested_action_path_id"]),
            str(secondary["problem_id"]),
        )

    for problem_row in [primary_problem, *secondary_problems]:
        problem_id = str(problem_row["problem_id"])
        for action_path_id in problem_row.get("secondary_action_path_ids") or []:
            _append(str(action_path_id), problem_id)

    return tuple(
        SuggestedActionRow(
            action_path_id=action_path_id,
            label_en=label_en,
            source_problem_ids=tuple(source_problem_ids),
            priority=index,
        )
        for index, (action_path_id, label_en, source_problem_ids) in enumerate(collected, start=1)
    )


def _demoted_symptom_ids(prioritization: ProblemPrioritizationResult) -> tuple[str, ...]:
    return tuple(
        rejected.problem_id
        for rejected in prioritization.rejected_problems
        if rejected.reject_reason_code == "superseded_by_root_cause_diagnosis"
    )


def _short_diagnosis_en(defn, score_row: ProblemScoreRow) -> str:
    if score_row.evidence_refs:
        top_ref = max(
            score_row.evidence_refs,
            key=lambda ref: float(ref.get("normalized_score") or 0.0),
        )
        interpretation = str(top_ref.get("interpretation_en") or "").strip()
        if interpretation:
            return interpretation
    first_sentence = defn.technical_definition_en.split(".")[0].strip()
    if first_sentence:
        return first_sentence + "."
    return defn.label_en + "."


def _why_it_matters_en(defn) -> str:
    text = str(defn.portfolio_manager_interpretation_en or "").strip()
    if not text:
        return defn.label_en + " requires attention in the current diagnostic context."
    parts = [part.strip() for part in text.replace("\n", " ").split(". ") if part.strip()]
    if len(parts) >= 2:
        return ". ".join(parts[:2]).rstrip(".") + "."
    return parts[0].rstrip(".") + "."


def _do_not_overreact_reason_en(
    defn,
    *,
    role: str,
    demoted_symptom_ids: tuple[str, ...],
) -> str | None:
    if role != "primary":
        return None
    if demoted_symptom_ids:
        labels = [
            PROBLEM_REGISTRY[pid].label_en
            for pid in demoted_symptom_ids
            if pid in PROBLEM_REGISTRY
        ]
        if labels:
            if len(labels) == 1:
                return (
                    f"{labels[0]} is secondary; "
                    f"{defn.label_en.lower()} drives the primary diagnosis."
                )
            joined = ", ".join(labels[:-1]) + f", and {labels[-1]}"
            return (
                f"{joined} are secondary; "
                f"{defn.label_en.lower()} drives the primary diagnosis."
            )
    reason = str(defn.do_not_overreact_reason_en or "").strip()
    return reason or None
