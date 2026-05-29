"""Block 4 v2 problem prioritization (Session 06).

Selects one primary problem, up to two secondary problems, and explicit
rejected hypotheses from scored rows using decision_score, severity,
confidence, and ``ROOT_CAUSE_ELEVATION_RULES``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.block_4.evidence_extraction import EvidenceExtractionResult
from src.block_4.problem_scoring import ProblemScoreRow, ProblemScoringResult
from src.block_4.problem_taxonomy import (
    PROBLEM_REGISTRY,
    ROOT_CAUSE_ELEVATION_RULES,
    get_problem_definition,
)

PRIORITIZATION_RULESET_VERSION = "block_4_v2_prioritization_heuristic_v1"
MAX_SECONDARY_PROBLEMS = 2

_SEVERITY_RANK = {"high": 3, "medium": 2, "low": 1, "unavailable": 0}
_CONFIDENCE_RANK = {"high": 3, "medium": 2, "low": 1}
_MATERIALITY_RANK = {"high": 3, "medium": 2, "low": 1, "none": 0}

_SPECIAL_PRIMARY_ORDER = (
    "evidence_insufficient_data_quality",
    "evidence_insufficient_conflicting_signals",
    "current_portfolio_acceptable",
)

_ELEVATION_BOOST = 0.08


@dataclass(frozen=True)
class RejectedProblemRow:
    problem_id: str
    reject_reason_code: str
    reject_reason_en: str
    top_evidence_refs: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "problem_id": self.problem_id,
            "reject_reason_code": self.reject_reason_code,
            "reject_reason_en": self.reject_reason_en,
            "top_evidence_refs": list(self.top_evidence_refs),
        }


@dataclass
class ProblemPrioritizationResult:
    primary_problem_id: str
    secondary_problem_ids: tuple[str, ...] = ()
    rejected_problems: tuple[RejectedProblemRow, ...] = ()
    problems_activated: int = 0
    elevation_rules_applied: tuple[str, ...] = ()
    primary_row: ProblemScoreRow | None = None
    secondary_rows: tuple[ProblemScoreRow, ...] = field(default_factory=tuple)

    def selected_problem_ids(self) -> tuple[str, ...]:
        return (self.primary_problem_id,) + self.secondary_problem_ids

    def to_summary_dict(self) -> dict[str, Any]:
        return {
            "primary_problem_id": self.primary_problem_id,
            "n_secondary": len(self.secondary_problem_ids),
            "n_rejected": len(self.rejected_problems),
            "n_problems": 1 + len(self.secondary_problem_ids),
            "problems_activated": self.problems_activated,
            "elevation_rules_applied": list(self.elevation_rules_applied),
        }


def prioritize_problems(
    scoring: ProblemScoringResult,
    evidence: EvidenceExtractionResult | None = None,
) -> ProblemPrioritizationResult:
    """Rank activated problems into primary, secondary (max 2), and rejected lists."""
    problems_activated = len(scoring.activated_problem_ids)

    special_primary = _resolve_special_primary(scoring)
    if special_primary is not None:
        primary_row = scoring.get_row(special_primary)
        rejected = _build_rejected_problems(
            scoring,
            selected_ids=(special_primary,),
            demoted_ids=set(),
            elevation_rules_applied=(),
        )
        return ProblemPrioritizationResult(
            primary_problem_id=special_primary,
            secondary_problem_ids=(),
            rejected_problems=rejected,
            problems_activated=problems_activated,
            elevation_rules_applied=(),
            primary_row=primary_row,
            secondary_rows=(),
        )

    candidates = list(scoring.actionable_activated_ids)
    if not candidates:
        acceptable_id = "current_portfolio_acceptable"
        primary_row = scoring.get_row(acceptable_id)
        rejected = _build_rejected_problems(
            scoring,
            selected_ids=(acceptable_id,),
            demoted_ids=set(),
            elevation_rules_applied=(),
        )
        return ProblemPrioritizationResult(
            primary_problem_id=acceptable_id,
            secondary_problem_ids=(),
            rejected_problems=rejected,
            problems_activated=problems_activated,
            elevation_rules_applied=(),
            primary_row=primary_row,
            secondary_rows=(),
        )

    demoted_ids, score_boosts, applied_rules = _apply_elevation_rules(
        candidates,
        scoring,
        evidence,
    )
    ranked = sorted(
        candidates,
        key=lambda pid: _rank_sort_key(pid, scoring.rows[pid], score_boosts),
        reverse=True,
    )

    primary_id = _select_primary_id(ranked, scoring, demoted_ids)
    primary_row = scoring.get_row(primary_id)

    demoted_for_rejection = _demoted_after_primary(primary_id, demoted_ids, applied_rules)
    remaining = [pid for pid in ranked if pid != primary_id and pid not in demoted_for_rejection]
    secondary_ids = tuple(remaining[:MAX_SECONDARY_PROBLEMS])
    secondary_rows = tuple(scoring.rows[pid] for pid in secondary_ids if pid in scoring.rows)

    selected_ids = (primary_id,) + secondary_ids
    rejected = _build_rejected_problems(
        scoring,
        selected_ids=selected_ids,
        demoted_ids=demoted_for_rejection,
        elevation_rules_applied=applied_rules,
    )

    return ProblemPrioritizationResult(
        primary_problem_id=primary_id,
        secondary_problem_ids=secondary_ids,
        rejected_problems=rejected,
        problems_activated=problems_activated,
        elevation_rules_applied=applied_rules,
        primary_row=primary_row,
        secondary_rows=secondary_rows,
    )


def _resolve_special_primary(scoring: ProblemScoringResult) -> str | None:
    for problem_id in _SPECIAL_PRIMARY_ORDER:
        row = scoring.get_row(problem_id)
        if row is not None and row.activated:
            if problem_id == "current_portfolio_acceptable":
                if scoring.actionable_activated_ids:
                    continue
            return problem_id
    return None


def _apply_elevation_rules(
    candidates: list[str],
    scoring: ProblemScoringResult,
    evidence: EvidenceExtractionResult | None,
) -> tuple[set[str], dict[str, float], tuple[str, ...]]:
    candidate_set = set(candidates)
    demoted_ids: set[str] = set()
    score_boosts: dict[str, float] = {}
    applied: list[str] = []

    for rule in ROOT_CAUSE_ELEVATION_RULES:
        prefer = str(rule["prefer_primary"])
        demotes = tuple(str(pid) for pid in rule.get("demote_when_present", ()))
        if prefer not in candidate_set:
            continue
        if not any(pid in candidate_set for pid in demotes):
            continue

        prefer_row = scoring.get_row(prefer)
        if prefer_row is None:
            continue

        if rule.get("requires_stress_confirmation"):
            if prefer_row.scoring.stress_confirmation != "confirmed":
                continue

        requires_signal = rule.get("requires_signal")
        if requires_signal:
            if evidence is None or not evidence.has_signal(str(requires_signal)):
                continue

        applied.append(str(rule["rule_id"]))
        score_boosts[prefer] = score_boosts.get(prefer, 0.0) + _ELEVATION_BOOST
        demoted_ids.update(pid for pid in demotes if pid in candidate_set)

    return demoted_ids, score_boosts, tuple(applied)


def _rank_sort_key(
    problem_id: str,
    row: ProblemScoreRow,
    score_boosts: dict[str, float],
) -> tuple[float, int, int, int, str]:
    scoring = row.scoring
    decision = scoring.decision_score + score_boosts.get(problem_id, 0.0)
    return (
        decision,
        _SEVERITY_RANK.get(row.severity, 0),
        _CONFIDENCE_RANK.get(row.confidence, 0),
        _MATERIALITY_RANK.get(scoring.materiality, 0),
        problem_id,
    )


def _select_primary_id(
    ranked: list[str],
    scoring: ProblemScoringResult,
    demoted_ids: set[str],
) -> str:
    eligible = [
        pid
        for pid in ranked
        if pid not in demoted_ids and not _blocked_as_primary(scoring.rows[pid])
    ]
    if eligible:
        return eligible[0]
    fallback = [pid for pid in ranked if not _blocked_as_primary(scoring.rows[pid])]
    if fallback:
        return fallback[0]
    return ranked[0]


def _blocked_as_primary(row: ProblemScoreRow) -> bool:
    if row.problem_id == "weak_crisis_resilience":
        return (
            row.scoring.stress_confirmation == "pre_stress_only"
            and row.confidence == "low"
        )
    return False


def _demoted_after_primary(
    primary_id: str,
    demoted_ids: set[str],
    applied_rules: tuple[str, ...],
) -> set[str]:
    if not applied_rules:
        return set()
    relevant_demotes: set[str] = set()
    for rule in ROOT_CAUSE_ELEVATION_RULES:
        if str(rule["rule_id"]) not in applied_rules:
            continue
        if str(rule["prefer_primary"]) != primary_id:
            continue
        relevant_demotes.update(str(pid) for pid in rule.get("demote_when_present", ()))
    return demoted_ids & relevant_demotes


def _build_rejected_problems(
    scoring: ProblemScoringResult,
    *,
    selected_ids: tuple[str, ...],
    demoted_ids: set[str],
    elevation_rules_applied: tuple[str, ...],
) -> tuple[RejectedProblemRow, ...]:
    selected_set = set(selected_ids)
    rejected: list[RejectedProblemRow] = []

    for problem_id, row in sorted(scoring.rows.items()):
        if problem_id in selected_set:
            continue

        reason_code, reason_en = _resolve_reject_reason(
            row,
            demoted_ids=demoted_ids,
            elevation_rules_applied=elevation_rules_applied,
            selected_ids=selected_set,
        )
        if reason_code is None:
            continue

        rejected.append(
            RejectedProblemRow(
                problem_id=problem_id,
                reject_reason_code=reason_code,
                reject_reason_en=reason_en,
                top_evidence_refs=_top_evidence_refs(row),
            )
        )

    return tuple(rejected)


def _resolve_reject_reason(
    row: ProblemScoreRow,
    *,
    demoted_ids: set[str],
    elevation_rules_applied: tuple[str, ...],
    selected_ids: set[str],
) -> tuple[str, str] | tuple[None, None]:
    defn = get_problem_definition(row.problem_id)
    label = defn.label_en if defn is not None else row.problem_id

    if row.problem_id in demoted_ids and elevation_rules_applied:
        prefer_labels = _prefer_primary_labels(elevation_rules_applied, demoted_ids, row.problem_id)
        prefer_text = prefer_labels[0] if prefer_labels else "a stress-confirmed root cause"
        return (
            "superseded_by_root_cause_diagnosis",
            f"{label} is secondary to {prefer_text}; stress-confirmed root cause drives the diagnosis.",
        )

    if row.activated and row.problem_id not in selected_ids:
        return (
            "lower_priority_than_selected_problems",
            f"{label} activated but ranked below the selected primary and secondary problems.",
        )

    if row.reject_reason_code and row.reject_reason_en:
        return row.reject_reason_code, row.reject_reason_en

    if not row.activated and row.required_met:
        stress = row.scoring.stress_confirmation
        materiality = row.scoring.materiality
        if stress in {"pre_stress_only", "contradicted", "unavailable"} and materiality in {"low", "none"}:
            return (
                "stress_not_confirmed_below_materiality",
                f"{label} is elevated but stress losses are not material and confirmation is weak.",
            )

    if not row.activated and row.evidence_refs and not row.required_met:
        return (
            "required_evidence_incomplete",
            f"Required evidence for {label} is incomplete.",
        )

    return None, None


def _prefer_primary_labels(
    applied_rules: tuple[str, ...],
    demoted_ids: set[str],
    demoted_id: str,
) -> list[str]:
    labels: list[str] = []
    for rule in ROOT_CAUSE_ELEVATION_RULES:
        if str(rule["rule_id"]) not in applied_rules:
            continue
        demotes = {str(pid) for pid in rule.get("demote_when_present", ())}
        if demoted_id not in demotes:
            continue
        prefer = str(rule["prefer_primary"])
        defn = PROBLEM_REGISTRY.get(prefer)
        if defn is not None:
            labels.append(defn.label_en)
    return labels


def _top_evidence_refs(row: ProblemScoreRow, limit: int = 3) -> tuple[dict[str, Any], ...]:
    refs = list(row.evidence_refs)
    refs.sort(key=lambda ref: float(ref.get("normalized_score") or 0.0), reverse=True)
    trimmed: list[dict[str, Any]] = []
    for ref in refs[:limit]:
        compact = {key: ref[key] for key in ref if key != "normalized_score"}
        if "normalized_score" in ref:
            compact["normalized_score"] = ref["normalized_score"]
        trimmed.append(compact)
    return tuple(trimmed)
