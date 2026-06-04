"""Block 4 v3 no-trade / monitor gate.

Evaluates whether the diagnosis supports proceeding to Launchpad,
monitoring only, or deferring action until evidence improves.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.block_4.action_path_mapping import ActionPathMappingResult
from src.block_4.evidence_extraction import EvidenceExtractionResult
from src.block_4.problem_prioritization import ProblemPrioritizationResult
from src.block_4.problem_scoring import ProblemScoringResult
from src.block_4.problem_taxonomy import get_problem_definition

NO_TRADE_GATE_RULESET_VERSION = "block_4_v3_no_trade_gate_v1"

OUTCOME_PROCEED = "proceed_to_launchpad"
OUTCOME_MONITOR = "monitor"
OUTCOME_DO_NOT_ACT = "do_not_act_yet"

STEP_SELECT_LAUNCHPAD = "select_launchpad_card"
STEP_MONITOR = "monitor_quarterly"
STEP_RERUN = "rerun_diagnostics"
STEP_RESOLVE_DATA = "resolve_data"
STEP_COMPARE_REFERENCE = "compare_reference_benchmarks"

_EVIDENCE_INSUFFICIENT_IDS = frozenset(
    {
        "evidence_insufficient_data_quality",
        "mixed_evidence_no_action",
    }
)


@dataclass(frozen=True)
class NoTradeGateResult:
    outcome: str
    headline_en: str
    reasons: tuple[str, ...]
    recommended_next_step: str
    launchpad_suppressed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "headline_en": self.headline_en,
            "reasons": list(self.reasons),
            "recommended_next_step": self.recommended_next_step,
            "launchpad_suppressed": self.launchpad_suppressed,
        }


def evaluate_no_trade_gate(
    mapping: ActionPathMappingResult,
    scoring: ProblemScoringResult,
    evidence: EvidenceExtractionResult,
    *,
    prioritization: ProblemPrioritizationResult | None = None,
) -> NoTradeGateResult:
    """Decide proceed / monitor / do-not-act from mapped diagnosis and evidence quality."""
    primary = mapping.primary_problem
    primary_id = str(primary["problem_id"])
    defn = get_problem_definition(primary_id)

    if primary_id == "evidence_insufficient_data_quality":
        return _gate_data_quality(evidence)
    if primary_id == "mixed_evidence_no_action":
        return _gate_mixed_evidence(scoring, prioritization)
    if primary_id == "current_portfolio_acceptable":
        return _gate_acceptable(primary)

    confidence = str(primary.get("confidence") or "low")
    severity = str(primary.get("severity") or "unavailable")
    scoring_block = primary.get("scoring") if isinstance(primary.get("scoring"), dict) else {}
    stress_confirmation = str(scoring_block.get("stress_confirmation") or "unavailable")
    materiality = str(scoring_block.get("materiality") or "none")
    label = defn.label_en if defn is not None else primary_id.replace("_", " ")

    if stress_confirmation == "contradicted":
        return NoTradeGateResult(
            outcome=OUTCOME_DO_NOT_ACT,
            headline_en=f"Contradicting evidence blocks a confident {label.lower()} action.",
            reasons=_actionable_reasons(
                primary,
                evidence,
                extra=["Stress and pre-stress evidence contradict the primary hypothesis"],
            ),
            recommended_next_step=STEP_RERUN,
            launchpad_suppressed=True,
        )

    if confidence == "low" and stress_confirmation != "confirmed":
        return NoTradeGateResult(
            outcome=OUTCOME_DO_NOT_ACT,
            headline_en=f"{label} is flagged but confidence is too low to act without stress confirmation.",
            reasons=_actionable_reasons(
                primary,
                evidence,
                extra=["Primary confidence is low", "Stress confirmation is not available or is weak"],
            ),
            recommended_next_step=STEP_RERUN,
            launchpad_suppressed=True,
        )

    if materiality in {"none", "low"} and severity in {"low", "unavailable"}:
        return NoTradeGateResult(
            outcome=OUTCOME_MONITOR,
            headline_en=f"{label} is present but not material enough to prioritize candidate testing now.",
            reasons=_actionable_reasons(
                primary,
                evidence,
                extra=["Primary materiality is below the action threshold"],
            ),
            recommended_next_step=STEP_MONITOR,
            launchpad_suppressed=True,
        )

    if (
        stress_confirmation == "confirmed"
        and materiality in {"high", "medium"}
        and confidence in {"high", "medium"}
    ):
        return NoTradeGateResult(
            outcome=OUTCOME_PROCEED,
            headline_en=_proceed_headline(label, primary),
            reasons=_actionable_reasons(primary, evidence),
            recommended_next_step=STEP_SELECT_LAUNCHPAD,
            launchpad_suppressed=False,
        )

    if stress_confirmation == "pre_stress_only" or confidence == "low":
        return NoTradeGateResult(
            outcome=OUTCOME_MONITOR,
            headline_en=f"Monitor {label.lower()} until stress evidence confirms the diagnosis.",
            reasons=_actionable_reasons(
                primary,
                evidence,
                extra=["Diagnosis relies on pre-stress evidence only"],
            ),
            recommended_next_step=STEP_MONITOR,
            launchpad_suppressed=True,
        )

    return NoTradeGateResult(
        outcome=OUTCOME_PROCEED,
        headline_en=_proceed_headline(label, primary),
        reasons=_actionable_reasons(primary, evidence),
        recommended_next_step=STEP_SELECT_LAUNCHPAD,
        launchpad_suppressed=False,
    )


def build_diagnosis_summary(
    mapping: ActionPathMappingResult,
    gate: NoTradeGateResult,
    *,
    n_rejected: int = 0,
) -> dict[str, Any]:
    """Build ``summary`` block for problem_classification_v3."""
    primary_id = str(mapping.primary_problem["problem_id"])
    return {
        "primary_problem_id": primary_id,
        "n_secondary": len(mapping.secondary_problems),
        "n_rejected": n_rejected,
        "n_problems": len(mapping.problem_rows),
        "current_portfolio_acceptable": primary_id == "current_portfolio_acceptable",
        "no_trade_outcome": gate.outcome,
    }


def gate_from_primary_problem_id(primary_problem_id: str) -> NoTradeGateResult:
    """Minimal gate fallback when only the primary id is known (legacy shim)."""
    if primary_problem_id == "evidence_insufficient_data_quality":
        return NoTradeGateResult(
            outcome=OUTCOME_DO_NOT_ACT,
            headline_en="Evidence quality must be reviewed before portfolio action.",
            reasons=("Diagnostic inputs are incomplete or untrusted.",),
            recommended_next_step=STEP_RESOLVE_DATA,
            launchpad_suppressed=True,
        )
    if primary_problem_id == "mixed_evidence_no_action":
        return NoTradeGateResult(
            outcome=OUTCOME_DO_NOT_ACT,
            headline_en=(
                "No immediate rebalance is justified; compare against simple reference benchmarks."
            ),
            reasons=("Usable evidence is mixed, but no root-cause diagnosis is strong enough to act on.",),
            recommended_next_step=STEP_COMPARE_REFERENCE,
            launchpad_suppressed=True,
        )
    if primary_problem_id == "current_portfolio_acceptable":
        return NoTradeGateResult(
            outcome=OUTCOME_MONITOR,
            headline_en=(
                "No immediate rebalance is justified; monitor and compare against simple references."
            ),
            reasons=("No actionable problem crossed materiality gates.",),
            recommended_next_step=STEP_COMPARE_REFERENCE,
            launchpad_suppressed=True,
        )
    return NoTradeGateResult(
        outcome=OUTCOME_PROCEED,
        headline_en="The primary diagnosis supports testing a Launchpad hypothesis.",
        reasons=(),
        recommended_next_step=STEP_SELECT_LAUNCHPAD,
        launchpad_suppressed=False,
    )


def _gate_data_quality(evidence: EvidenceExtractionResult) -> NoTradeGateResult:
    reasons: list[str] = []
    if evidence.data_quality_warnings:
        reasons.extend(evidence.data_quality_warnings[:3])
    if evidence.has_signal("data_trust_failure"):
        reasons.append("Data trust checks failed on one or more diagnostic blocks")
    if evidence.has_signal("partial_sections"):
        reasons.append("Multiple Block 2 sections are partial or unavailable")
    if not reasons:
        reasons.append("Evidence quality requires review before candidate testing")
    return NoTradeGateResult(
        outcome=OUTCOME_DO_NOT_ACT,
        headline_en="Evidence quality must be reviewed before portfolio action.",
        reasons=tuple(dict.fromkeys(reasons)),
        recommended_next_step=STEP_RESOLVE_DATA,
        launchpad_suppressed=True,
    )


def _gate_mixed_evidence(
    scoring: ProblemScoringResult,
    prioritization: ProblemPrioritizationResult | None,
) -> NoTradeGateResult:
    reasons = [
        "Usable evidence is mixed, but no dominant root-cause diagnosis is confirmed strongly enough to act on"
    ]
    if scoring.conflicting_signal_bundle:
        reasons.append("Mixed-evidence note activated during problem scoring")
    if prioritization is not None and prioritization.rejected_problems:
        reasons.append("Several hypotheses were not selected because the evidence did not dominate")
    return NoTradeGateResult(
        outcome=OUTCOME_DO_NOT_ACT,
        headline_en="No immediate rebalance is justified; compare against simple reference benchmarks.",
        reasons=tuple(reasons),
        recommended_next_step=STEP_COMPARE_REFERENCE,
        launchpad_suppressed=True,
    )


def _gate_acceptable(primary: dict[str, Any]) -> NoTradeGateResult:
    reasons: list[str] = ["No actionable problem crossed materiality gates"]
    if primary.get("severity") == "low":
        reasons.append("Primary severity is in the monitor band")
    return NoTradeGateResult(
        outcome=OUTCOME_MONITOR,
        headline_en="No immediate rebalance is justified; monitor and compare against simple references.",
        reasons=tuple(reasons),
        recommended_next_step=STEP_COMPARE_REFERENCE,
        launchpad_suppressed=True,
    )


def _proceed_headline(label: str, primary: dict[str, Any]) -> str:
    short = str(primary.get("short_diagnosis_en") or "").strip()
    if short:
        return f"Stress-confirmed {label.lower()} warrants testing a defensive hypothesis."
    return f"Stress-confirmed {label.lower()} warrants testing a Launchpad hypothesis."


def _actionable_reasons(
    primary: dict[str, Any],
    evidence: EvidenceExtractionResult,
    *,
    extra: list[str] | None = None,
) -> tuple[str, ...]:
    reasons: list[str] = []
    confidence = str(primary.get("confidence") or "")
    scoring_block = primary.get("scoring") if isinstance(primary.get("scoring"), dict) else {}
    materiality = str(scoring_block.get("materiality") or "")
    stress_confirmation = str(scoring_block.get("stress_confirmation") or "")

    if confidence == "high":
        reasons.append("Primary confidence is high")
    elif confidence == "medium":
        reasons.append("Primary confidence is medium")

    if materiality == "high":
        reasons.append("Primary problem materiality is high")
    elif materiality == "medium":
        reasons.append("Primary problem materiality is medium")

    if stress_confirmation == "confirmed":
        reasons.append("Stress evidence confirms the primary diagnosis")
    elif stress_confirmation == "pre_stress_only":
        reasons.append("Diagnosis is based on pre-stress evidence only")

    if evidence.has_signal("worst_synthetic_scenario") and materiality in {"high", "medium"}:
        reasons.append("Worst synthetic loss exceeds materiality floor")

    if extra:
        reasons.extend(extra)

    return tuple(dict.fromkeys(reason for reason in reasons if reason))
