"""Block 4 v3 diagnosis facade and JSON writers.

Orchestrates evidence extraction through launchpad card generation and writes
``problem_classification.json`` + ``candidate_launchpad.json`` (v3 schema).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.block_4.action_path_mapping import ActionPathMappingResult, map_action_paths
from src.block_4.evidence_extraction import (
    EvidenceExtractionResult,
    build_diagnosis_evidence_bundle,
    extract_evidence_signals,
)
from src.block_4.launchpad_cards import (
    DECISION_BOUNDARY_EN,
    build_candidate_launchpad_v3_document,
    success_criteria_for_action_path,
)
from src.block_4.no_trade_gate import (
    NoTradeGateResult,
    build_diagnosis_summary,
    evaluate_no_trade_gate,
)
from src.block_4.problem_prioritization import ProblemPrioritizationResult, prioritize_problems
from src.block_4.problem_scoring import ProblemScoringResult, score_problems
from src.block_4.problem_taxonomy import get_problem_definition, is_symptom_problem
from src.block_4.thresholds import get_block_4_thresholds
from src.candidate_launchpad import CANDIDATE_LAUNCHPAD_FILENAME
from src.portfolio_alternatives_builder import write_portfolio_alternatives_builder_outputs
from src.problem_classification import PROBLEM_CLASSIFICATION_FILENAME

PROBLEM_CLASSIFICATION_V3_VERSION = "problem_classification_v3"
BLOCK_4_DIAGNOSIS_FACADE_VERSION = "build_block_4_diagnosis_v3"
DIAGNOSIS_INTERPRETATION_CHAIN_VERSION = "diagnosis_interpretation_chain_v1"

HEDGE_GAP_SOURCE_V1 = "hedge_gap_analysis_v1"
HEDGE_GAP_SOURCE_LEGACY = "stress_conclusions.hedge_gap_status"
STRESS_SCORECARD_SOURCE_V1 = "current_portfolio_stress_scorecard_v1"
STRESS_SCORECARD_SOURCE_LEGACY = "stress_scorecard_v1"
WEAKNESS_MAP_SOURCE_BLOCK = "block_2_6_portfolio_weakness_map"


@dataclass
class Block4DiagnosisResult:
    problem_classification: dict[str, Any]
    candidate_launchpad: dict[str, Any]
    evidence: EvidenceExtractionResult
    scoring: ProblemScoringResult
    prioritization: ProblemPrioritizationResult
    mapping: ActionPathMappingResult
    gate: NoTradeGateResult
    status: str

    @property
    def primary_problem_id(self) -> str:
        return str(self.problem_classification["primary_problem"]["problem_id"])


@dataclass(frozen=True)
class Block4DiagnosisWriteResult:
    problem_classification_path: Path
    candidate_launchpad_path: Path
    diagnosis: Block4DiagnosisResult


def build_block_4_diagnosis(
    *,
    portfolio_xray: dict[str, Any] | None,
    stress_report: dict[str, Any] | None,
    client_fit_check: dict[str, Any] | None = None,
    analysis_end: str | None = None,
    generated_at: str | None = None,
) -> Block4DiagnosisResult:
    """Run the Block 4 v3 evidence-to-diagnosis pipeline and return both JSON documents."""
    xray = portfolio_xray if isinstance(portfolio_xray, dict) else {}
    stress = stress_report if isinstance(stress_report, dict) else {}
    client_fit = client_fit_check if isinstance(client_fit_check, dict) else {}

    evidence = extract_evidence_signals(xray, stress, client_fit)
    scoring = score_problems(evidence)
    evidence_bundle = build_diagnosis_evidence_bundle(evidence, scoring)
    prioritization = prioritize_problems(scoring, evidence)
    mapping = map_action_paths(prioritization, scoring)
    gate = evaluate_no_trade_gate(mapping, scoring, evidence, prioritization=prioritization)

    status = _builder_status(evidence, xray, stress)
    warnings = _builder_warnings(evidence, xray, stress)
    hedge_gap_source, stress_scorecard_source = _provenance_sources(xray, stress)

    rejected_rows = [row.to_dict() for row in prioritization.rejected_problems]
    problems_shim = [_mirror_problem_row_for_v1_shim(row) for row in mapping.problem_rows]
    primary_diagnosis = _build_primary_diagnosis(
        mapping=mapping,
        scoring=scoring,
        prioritization=prioritization,
        gate=gate,
    )
    next_diagnostic_step = _next_diagnostic_step(mapping.primary_problem, gate)
    interpretation_chain = _build_interpretation_chain(
        primary_diagnosis=primary_diagnosis,
        mapping=mapping,
        scoring=scoring,
        prioritization=prioritization,
        next_diagnostic_step=next_diagnostic_step,
        evidence=evidence,
        client_fit_check=client_fit,
        diagnostic_quality_status=_diagnostic_quality_status(scoring, prioritization, evidence),
    )
    diagnostic_quality_status = interpretation_chain["diagnostic_quality_status"]
    client_fit_context = interpretation_chain["client_fit_context"]

    cfg = get_block_4_thresholds()
    problem_classification: dict[str, Any] = {
        "schema_version": PROBLEM_CLASSIFICATION_V3_VERSION,
        "diagnostic_only": True,
        "diagnosis_mode": "current_portfolio_problem_classification",
        "ruleset_version": cfg.ruleset_version,
        "status": status,
        "generated_at": generated_at or _utc_now_iso(),
        "analysis_end": analysis_end,
        "source_artifacts": {
            "portfolio_xray": "portfolio_xray.json" if xray else None,
            "stress_report": "stress_report.json" if stress else None,
            "client_fit_check": "client_fit_check.json" if client_fit else None,
        },
        "client_fit_status": client_fit_context["client_fit_status"],
        "diagnostic_quality_status": diagnostic_quality_status,
        "client_fit_context": client_fit_context,
        "primary_diagnosis": primary_diagnosis,
        "root_cause": primary_diagnosis.get("root_cause"),
        "supporting_symptoms": primary_diagnosis.get("supporting_symptoms", []),
        "key_evidence": primary_diagnosis.get("key_evidence", []),
        "why_this_matters": primary_diagnosis.get("why_this_matters"),
        "why_not_other_problems": primary_diagnosis.get("why_not_other_problems", []),
        "confidence": primary_diagnosis.get("confidence"),
        "confidence_explanation": primary_diagnosis.get("confidence_explanation"),
        "materiality": primary_diagnosis.get("materiality"),
        "actionability": primary_diagnosis.get("actionability"),
        "suggested_hypothesis": primary_diagnosis.get("suggested_hypothesis"),
        "next_diagnostic_step": next_diagnostic_step,
        "success_criteria": primary_diagnosis.get("success_criteria", []),
        "interpretation_chain": interpretation_chain,
        "diagnosis_evidence_items": interpretation_chain["diagnosis_evidence_items"],
        "root_cause_narrative": interpretation_chain["root_cause_narrative"],
        "metric_to_diagnosis_trace": interpretation_chain["metric_to_diagnosis_trace"],
        "professional_rationale_refs": interpretation_chain["professional_rationale_refs"],
        "backend_audit": {
            "primary_problem": mapping.primary_problem,
            "secondary_problems": list(mapping.secondary_problems),
            "suggested_actions": [row.to_dict() for row in mapping.suggested_actions],
            "evidence_bundle": evidence_bundle.to_dict(),
            "scoring_is_backend_audit_metadata": True,
        },
        "primary_problem": mapping.primary_problem,
        "secondary_problems": list(mapping.secondary_problems),
        "rejected_problems": rejected_rows,
        "suggested_actions": [row.to_dict() for row in mapping.suggested_actions],
        "no_trade_or_monitoring_view": gate.to_dict(),
        "data_quality_warnings": list(evidence.data_quality_warnings),
        "diagnostics_meta": {
            "evidence_signal_count": evidence.signal_count,
            "problems_evaluated": scoring.problems_evaluated,
            "problems_activated": prioritization.problems_activated,
            "block_4_facade_version": BLOCK_4_DIAGNOSIS_FACADE_VERSION,
            "legacy_sections_fallback_used": evidence.legacy_sections_fallback_used,
        },
        "problems": problems_shim,
        "summary": build_diagnosis_summary(
            mapping,
            gate,
            n_rejected=len(rejected_rows),
        ),
        "warnings": warnings,
    }

    if hedge_gap_source is not None:
        problem_classification["hedge_gap_source"] = hedge_gap_source
    if stress_scorecard_source is not None:
        problem_classification["stress_scorecard_source"] = stress_scorecard_source
    if isinstance(xray.get(WEAKNESS_MAP_SOURCE_BLOCK), dict):
        problem_classification["weakness_map_source"] = WEAKNESS_MAP_SOURCE_BLOCK

    candidate_launchpad = build_candidate_launchpad_v3_document(
        mapping,
        analysis_end=analysis_end,
        generated_at=problem_classification["generated_at"],
        scoring=scoring,
        evidence=evidence,
        no_trade_gate=gate,
        ruleset_version=cfg.ruleset_version,
    )

    return Block4DiagnosisResult(
        problem_classification=problem_classification,
        candidate_launchpad=candidate_launchpad,
        evidence=evidence,
        scoring=scoring,
        prioritization=prioritization,
        mapping=mapping,
        gate=gate,
        status=status,
    )


def write_block_4_diagnosis_outputs(
    *,
    output_dir: str | Path,
    portfolio_xray: dict[str, Any] | None,
    stress_report: dict[str, Any] | None,
    client_fit_check: dict[str, Any] | None = None,
    analysis_end: str | None = None,
) -> Block4DiagnosisWriteResult:
    """Write v3 ``problem_classification.json`` and ``candidate_launchpad.json``."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    diagnosis = build_block_4_diagnosis(
        portfolio_xray=portfolio_xray,
        stress_report=stress_report,
        client_fit_check=client_fit_check,
        analysis_end=analysis_end,
    )

    pc_path = out / PROBLEM_CLASSIFICATION_FILENAME
    lp_path = out / CANDIDATE_LAUNCHPAD_FILENAME

    with pc_path.open("w", encoding="utf-8") as handle:
        json.dump(diagnosis.problem_classification, handle, indent=2, ensure_ascii=False, default=str)
    with lp_path.open("w", encoding="utf-8") as handle:
        json.dump(diagnosis.candidate_launchpad, handle, indent=2, ensure_ascii=False, default=str)
    write_portfolio_alternatives_builder_outputs(
        out,
        candidate_launchpad=diagnosis.candidate_launchpad,
        problem_classification=diagnosis.problem_classification,
        client_fit_check=client_fit_check,
    )

    return Block4DiagnosisWriteResult(
        problem_classification_path=pc_path,
        candidate_launchpad_path=lp_path,
        diagnosis=diagnosis,
    )


def block_4_manifest_extra(
    problem_classification: dict[str, Any] | None,
    candidate_launchpad: dict[str, Any] | None,
) -> dict[str, Any]:
    """Manifest ``extra`` block for Block 4 v3 wiring."""
    if not isinstance(problem_classification, dict):
        return {}
    if problem_classification.get("schema_version") != PROBLEM_CLASSIFICATION_V3_VERSION:
        return {}
    summary = problem_classification.get("summary") if isinstance(problem_classification.get("summary"), dict) else {}
    return {
        "block_4_diagnosis": {
            "schema_version": PROBLEM_CLASSIFICATION_V3_VERSION,
            "launchpad_schema_version": (
                candidate_launchpad.get("schema_version")
                if isinstance(candidate_launchpad, dict)
                else None
            ),
            "ruleset_version": problem_classification.get("ruleset_version"),
            "status": problem_classification.get("status"),
            "primary_problem_id": summary.get("primary_problem_id"),
            "no_trade_outcome": summary.get("no_trade_outcome"),
            "facade_version": BLOCK_4_DIAGNOSIS_FACADE_VERSION,
        }
    }


def _build_primary_diagnosis(
    *,
    mapping: ActionPathMappingResult,
    scoring: ProblemScoringResult,
    prioritization: ProblemPrioritizationResult,
    gate: NoTradeGateResult,
) -> dict[str, Any]:
    primary = mapping.primary_problem
    primary_id = str(primary.get("problem_id") or prioritization.primary_problem_id)
    defn = get_problem_definition(primary_id)
    scoring_block = primary.get("scoring") if isinstance(primary.get("scoring"), dict) else {}
    action_path_id = str(primary.get("suggested_action_path_id") or "")
    key_evidence = _collect_key_evidence(primary, scoring, limit=5)
    supporting_symptoms = _supporting_symptoms(scoring, exclude_id=primary_id, limit=5)
    why_not = _why_not_other_problems(prioritization, limit=5)

    root_cause = {
        "problem_id": primary_id,
        "label_en": primary.get("label_en") or (defn.label_en if defn else primary_id),
        "diagnosis_role": primary.get("diagnosis_role") or (defn.diagnosis_role if defn else "unknown"),
    }
    if defn is not None and defn.diagnosis_subtypes:
        root_cause["diagnosis_subtypes"] = list(defn.diagnosis_subtypes)

    return {
        "diagnosis_id": primary_id,
        "label_en": primary.get("label_en") or root_cause["label_en"],
        "thesis_en": _diagnosis_thesis(primary, gate),
        "root_cause": root_cause,
        "supporting_symptoms": supporting_symptoms,
        "key_evidence": key_evidence,
        "why_this_matters": primary.get("why_it_matters_en"),
        "why_not_other_problems": why_not,
        "confidence": primary.get("confidence"),
        "confidence_explanation": _confidence_explanation(primary, scoring, gate),
        "materiality": scoring_block.get("materiality"),
        "actionability": _actionability(gate),
        "suggested_hypothesis": _suggested_hypothesis(primary, gate),
        "success_criteria": list(success_criteria_for_action_path(action_path_id)),
        "secondary_diagnoses": list(mapping.secondary_problems)[:2],
        "mixed_evidence_note": _mixed_evidence_note(scoring, primary_id),
        "audit_scoring": scoring_block,
    }


def _diagnosis_thesis(primary: dict[str, Any], gate: NoTradeGateResult) -> str:
    primary_id = str(primary.get("problem_id") or "")
    label = str(primary.get("label_en") or primary_id.replace("_", " ")).strip()
    short = str(primary.get("short_diagnosis_en") or "").strip()
    if primary_id == "current_portfolio_acceptable":
        return (
            "Current portfolio is acceptable under current evidence. "
            "No material rebalance is justified; monitor the key risks."
        )
    if primary_id == "mixed_evidence_no_action":
        return (
            "No dominant actionable problem is confirmed. "
            "The evidence is usable but mixed, so a rebalance is not justified yet."
        )
    if primary_id == "evidence_insufficient_data_quality":
        return (
            "Evidence quality is not reliable enough for an investment diagnosis. "
            "Resolve data gaps before testing candidates."
        )
    if short:
        return f"{label}: {short}"
    return f"{label} is the primary diagnosis under current evidence."


def _collect_key_evidence(
    primary: dict[str, Any],
    scoring: ProblemScoringResult,
    *,
    limit: int,
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = [
        ref for ref in primary.get("evidence_refs") or [] if isinstance(ref, dict)
    ]
    if len(refs) < limit:
        for row in sorted(
            scoring.rows.values(),
            key=lambda r: r.scoring.decision_score,
            reverse=True,
        ):
            for ref in row.evidence_refs:
                if len(refs) >= limit:
                    break
                if ref not in refs:
                    refs.append(ref)
            if len(refs) >= limit:
                break

    compact: list[dict[str, Any]] = []
    for ref in refs[:limit]:
        compact.append(_compact_evidence_ref(ref))
    return compact


def _supporting_symptoms(
    scoring: ProblemScoringResult,
    *,
    exclude_id: str,
    limit: int,
) -> list[dict[str, Any]]:
    rows = [
        row
        for row in scoring.rows.values()
        if row.problem_id != exclude_id and row.activated and is_symptom_problem(row.problem_id)
    ]
    rows.sort(key=lambda row: row.scoring.decision_score, reverse=True)
    symptoms: list[dict[str, Any]] = []
    for row in rows[:limit]:
        defn = get_problem_definition(row.problem_id)
        symptoms.append(
            {
                "problem_id": row.problem_id,
                "label_en": defn.label_en if defn else row.problem_id,
                "severity": row.severity,
                "confidence": row.confidence,
                "why_it_supports_primary_en": (
                    f"{defn.label_en if defn else row.problem_id} is treated as supporting evidence, "
                    "not as the primary diagnosis, because root-cause triage takes priority."
                ),
                "top_evidence": [
                    _compact_evidence_ref(ref)
                    for ref in row.evidence_refs[:2]
                    if isinstance(ref, dict)
                ],
            }
        )
    return symptoms


def _why_not_other_problems(
    prioritization: ProblemPrioritizationResult,
    *,
    limit: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rejected in prioritization.rejected_problems[:limit]:
        defn = get_problem_definition(rejected.problem_id)
        rows.append(
            {
                "problem_id": rejected.problem_id,
                "label_en": defn.label_en if defn else rejected.problem_id,
                "reason_code": rejected.reject_reason_code,
                "reason_en": rejected.reject_reason_en,
            }
        )
    return rows


def _confidence_explanation(
    primary: dict[str, Any],
    scoring: ProblemScoringResult,
    gate: NoTradeGateResult,
) -> str:
    confidence = str(primary.get("confidence") or "low")
    scoring_block = primary.get("scoring") if isinstance(primary.get("scoring"), dict) else {}
    stress_confirmation = str(scoring_block.get("stress_confirmation") or "unavailable")
    if primary.get("problem_id") == "evidence_insufficient_data_quality":
        return "Confidence is capped because upstream data quality is not reliable enough."
    if primary.get("problem_id") == "mixed_evidence_no_action":
        return "Confidence is cautious: evidence is usable, but no root-cause diagnosis dominates."
    if stress_confirmation == "confirmed":
        return f"Confidence is {confidence} because stress evidence supports the diagnosis."
    if scoring.conflicting_signal_bundle:
        return f"Confidence is {confidence} because some evidence is mixed and should be monitored."
    return f"Confidence is {confidence}; stress confirmation is {stress_confirmation}."


def _build_interpretation_chain(
    *,
    primary_diagnosis: dict[str, Any],
    mapping: ActionPathMappingResult,
    scoring: ProblemScoringResult,
    prioritization: ProblemPrioritizationResult,
    next_diagnostic_step: dict[str, Any],
    evidence: EvidenceExtractionResult,
    client_fit_check: dict[str, Any],
    diagnostic_quality_status: str,
) -> dict[str, Any]:
    """Build additive source-backed interpretation fields for ``problem_classification_v3``.

    The chain is intentionally read-only over current Block 4 runtime results. It does not rescore,
    reprioritize, or read the Session 03 YAML as an active runtime registry.
    """

    primary = mapping.primary_problem
    primary_id = str(primary_diagnosis.get("diagnosis_id") or primary.get("problem_id") or "")
    evidence_items = _diagnosis_evidence_items(primary, scoring, limit=10)
    metric_trace = _metric_to_diagnosis_trace(evidence_items, primary_id)
    root_cause_narrative = _root_cause_narrative(
        primary=primary,
        primary_diagnosis=primary_diagnosis,
        scoring=scoring,
        prioritization=prioritization,
        evidence_items=evidence_items,
    )
    rationale_refs = _professional_rationale_refs(primary_id)
    rejected_alternatives = _rejected_alternative_items(prioritization, limit=5)
    client_fit_context = _client_fit_context(
        evidence=evidence,
        client_fit_check=client_fit_check,
        diagnostic_quality_status=diagnostic_quality_status,
        selected_diagnosis_id=primary_id,
    )
    source_artifacts = {
        str(item.get("source_artifact"))
        for item in evidence_items
        if item.get("source_artifact")
    }
    if client_fit_context.get("source_artifact"):
        source_artifacts.add(str(client_fit_context["source_artifact"]))

    return {
        "schema_version": DIAGNOSIS_INTERPRETATION_CHAIN_VERSION,
        "diagnostic_only": True,
        "selected_diagnosis_id": primary_id,
        "selected_diagnosis_role": primary.get("diagnosis_role"),
        "source_artifacts": sorted(source_artifacts),
        "client_fit_status": client_fit_context["client_fit_status"],
        "diagnostic_quality_status": diagnostic_quality_status,
        "client_fit_context": client_fit_context,
        "diagnosis_evidence_items": evidence_items,
        "root_cause_narrative": root_cause_narrative,
        "metric_to_diagnosis_trace": metric_trace,
        "rejected_alternatives": rejected_alternatives,
        "professional_rationale_refs": rationale_refs,
        "next_step_link": {
            "step_type": next_diagnostic_step.get("type"),
            "label": next_diagnostic_step.get("label"),
            "decision_boundary": next_diagnostic_step.get("decision_boundary"),
        },
        "recommendation_boundary_en": DECISION_BOUNDARY_EN,
    }


def _diagnosis_evidence_items(
    primary: dict[str, Any],
    scoring: ProblemScoringResult,
    *,
    limit: int,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    def _append(ref: dict[str, Any], *, evidence_role: str, linked_problem_id: str) -> None:
        if not isinstance(ref, dict) or len(items) >= limit:
            return
        signal = str(ref.get("signal") or "")
        evidence_id = str(ref.get("evidence_id") or f"ev_{linked_problem_id}_{signal}_{len(items) + 1}")
        key = (evidence_id, signal, linked_problem_id)
        if key in seen:
            return
        seen.add(key)

        item: dict[str, Any] = {
            "evidence_item_id": evidence_id,
            "linked_problem_id": linked_problem_id,
            "evidence_role": evidence_role,
            "signal": signal,
            "source_artifact": ref.get("source_artifact"),
            "source_block": ref.get("source_block"),
            "source_field_path": ref.get("raw_field_path") or ref.get("evidence_path"),
            "observed_value": ref.get("value"),
            "interpretation_en": ref.get("interpretation_en"),
            "why_relevant_to_diagnosis_en": ref.get("why_relevant_to_problem_en"),
            "evidence_path": ref.get("evidence_path"),
        }
        if ref.get("normalized_score") is not None:
            item["normalized_score"] = ref.get("normalized_score")
        if ref.get("severity") is not None:
            item["severity"] = ref.get("severity")
        if ref.get("confidence") is not None:
            item["confidence"] = ref.get("confidence")
        if ref.get("linked_assets"):
            item["linked_assets"] = ref.get("linked_assets")
        if ref.get("limitation_en"):
            item["limitation_en"] = ref.get("limitation_en")
        items.append(item)

    primary_id = str(primary.get("problem_id") or "")
    for ref in primary.get("evidence_refs") or []:
        _append(ref, evidence_role="supports_selected_diagnosis", linked_problem_id=primary_id)
    for ref in primary.get("negative_evidence_refs") or []:
        _append(ref, evidence_role="contrary_to_selected_diagnosis", linked_problem_id=primary_id)

    symptom_rows = [
        row
        for row in scoring.rows.values()
        if row.problem_id != primary_id and row.activated and is_symptom_problem(row.problem_id)
    ]
    symptom_rows.sort(key=lambda row: row.scoring.decision_score, reverse=True)
    for row in symptom_rows:
        for ref in row.evidence_refs[:2]:
            _append(ref, evidence_role="supporting_symptom", linked_problem_id=row.problem_id)
            if len(items) >= limit:
                break
        if len(items) >= limit:
            break

    return items


def _client_fit_context(
    *,
    evidence: EvidenceExtractionResult,
    client_fit_check: dict[str, Any],
    diagnostic_quality_status: str,
    selected_diagnosis_id: str,
) -> dict[str, Any]:
    status_signal = next(iter(evidence.get_signals("client_fit_status")), None)
    conflict_signal = next(iter(evidence.get_signals("goal_risk_conflict")), None)
    status = str(
        (status_signal.value if status_signal is not None else None)
        or client_fit_check.get("client_fit_status")
        or "not_provided"
    )
    conflict = client_fit_check.get("goal_risk_conflict") if isinstance(client_fit_check, dict) else {}
    conflict_status = str(
        (conflict.get("status") if isinstance(conflict, dict) else None)
        or ("conflict" if conflict_signal is not None else "not_evaluated")
    )
    fit_signals = sorted(
        name
        for name in evidence.signals
        if name == "goal_risk_conflict" or name == "client_fit_status" or name.startswith("client_fit_")
    )
    return {
        "schema_version": "client_fit_interpretation_context_v1",
        "source_artifact": "client_fit_check.json" if client_fit_check else None,
        "client_fit_status": status,
        "goal_risk_conflict_status": conflict_status,
        "diagnostic_quality_status": diagnostic_quality_status,
        "selected_diagnosis_id": selected_diagnosis_id,
        "diagnosis_selection_boundary_en": (
            "Client Fit status is interpreted separately from diagnostic quality; only an explicit "
            "goal-risk conflict can become the selected Problem Classification outcome."
        ),
        "client_fit_signal_names": fit_signals,
    }


def _diagnostic_quality_status(
    scoring: ProblemScoringResult,
    prioritization: ProblemPrioritizationResult,
    evidence: EvidenceExtractionResult,
) -> str:
    if evidence.has_signal("data_trust_failure") or prioritization.primary_problem_id == "evidence_insufficient_data_quality":
        return "evidence_insufficient"

    actionable_rows = [
        scoring.rows[pid]
        for pid in scoring.actionable_activated_ids
        if pid in scoring.rows and scoring.rows[pid].activated
    ]
    if not actionable_rows:
        if scoring.conflicting_signal_bundle:
            return "watch"
        return "clean"

    def _rank(row: Any) -> int:
        severity = {"high": 3, "medium": 2, "low": 1}.get(str(row.severity), 0)
        materiality = {"high": 3, "medium": 2, "low": 1}.get(str(row.scoring.materiality), 0)
        return max(severity, materiality)

    max_rank = max(_rank(row) for row in actionable_rows)
    if max_rank >= 3:
        return "material_issue"
    if max_rank == 2:
        return "issue"
    return "watch"


def _metric_to_diagnosis_trace(
    evidence_items: list[dict[str, Any]],
    primary_id: str,
) -> list[dict[str, Any]]:
    trace: list[dict[str, Any]] = []
    for idx, item in enumerate(evidence_items, start=1):
        trace.append(
            {
                "trace_id": f"trace_{idx:02d}_{item.get('signal') or 'signal'}",
                "source_artifact": item.get("source_artifact"),
                "source_block": item.get("source_block"),
                "source_field_path": item.get("source_field_path"),
                "metric_or_signal": item.get("signal"),
                "evidence_item_id": item.get("evidence_item_id"),
                "linked_problem_id": item.get("linked_problem_id"),
                "contributes_to_selected_diagnosis_id": primary_id,
                "contribution": item.get("evidence_role"),
                "interpretation_en": item.get("interpretation_en"),
            }
        )
    return trace


def _root_cause_narrative(
    *,
    primary: dict[str, Any],
    primary_diagnosis: dict[str, Any],
    scoring: ProblemScoringResult,
    prioritization: ProblemPrioritizationResult,
    evidence_items: list[dict[str, Any]],
) -> dict[str, Any]:
    primary_id = str(primary_diagnosis.get("diagnosis_id") or primary.get("problem_id") or "")
    label = str(primary_diagnosis.get("label_en") or primary.get("label_en") or primary_id)
    role = str(primary.get("diagnosis_role") or "")
    thesis = str(primary_diagnosis.get("thesis_en") or "").strip()
    defn = get_problem_definition(primary_id)
    top_signal = next(
        (str(item.get("interpretation_en") or "").strip() for item in evidence_items if item.get("interpretation_en")),
        "",
    )

    if primary_id == "evidence_insufficient_data_quality":
        statement = (
            "Data quality is the selected outcome because the available source artifacts do not "
            "support a reliable investment diagnosis yet."
        )
    elif primary_id in {"mixed_evidence_no_action", "current_portfolio_acceptable"}:
        statement = thesis or f"{label} is selected as the current portfolio outcome."
    elif role == "root_cause":
        evidence_phrase = f" The leading source-backed signal is: {top_signal}" if top_signal else ""
        statement = (
            f"{label} is selected as the primary root-cause diagnosis because the strongest "
            f"evidence points to a portfolio structure, not just an outcome metric.{evidence_phrase}"
        )
    else:
        statement = (
            f"{label} is selected as the primary diagnosis because no stronger governed root-cause "
            "diagnosis was confirmed with the available evidence."
        )

    return {
        "diagnosis_id": primary_id,
        "label_en": label,
        "diagnosis_role": role,
        "n_supporting_evidence_items": len(
            [item for item in evidence_items if item.get("evidence_role") != "contrary_to_selected_diagnosis"]
        ),
        "n_rejected_alternatives": len(prioritization.rejected_problems),
        "elevation_rules_applied": list(prioritization.elevation_rules_applied),
        "statement_en": statement,
        "root_cause_over_symptom_en": (
            "Root-cause diagnoses outrank symptom diagnoses when they explain the same evidence "
            "with sufficient confidence and materiality."
        ),
        "portfolio_manager_interpretation_en": (
            defn.portfolio_manager_interpretation_en if defn is not None else None
        ),
        "confidence_context_en": primary_diagnosis.get("confidence_explanation"),
        "source_refs": [
            "docs/specs/diagnosis_interpretation_methodology_spec.md#layer-4-root-cause-over-symptom",
            "docs/specs/block_4_diagnosis_v3_spec.md#primary-selection-order",
            "src/block_4/problem_taxonomy.py::PROBLEM_REGISTRY",
        ],
    }


def _professional_rationale_refs(primary_id: str) -> list[dict[str, Any]]:
    defn = get_problem_definition(primary_id)
    refs: list[dict[str, Any]] = [
        {
            "ref_id": "diagnosis_interpretation_methodology",
            "source": "docs/specs/diagnosis_interpretation_methodology_spec.md",
            "reason_en": "Defines the evidence-to-diagnosis chain and root-cause-over-symptom boundary.",
        },
        {
            "ref_id": "block_4_diagnosis_contract",
            "source": "docs/specs/block_4_diagnosis_v3_spec.md",
            "reason_en": "Defines the current Problem Classification v3 product contract and primary selection order.",
        },
        {
            "ref_id": "block_4_threshold_source",
            "source": "config/block_4_thresholds.yml",
            "reason_en": "Governs numeric activation, materiality, severity, and confidence settings.",
        },
    ]
    if defn is not None:
        refs.append(
            {
                "ref_id": f"problem_taxonomy.{primary_id}",
                "source": "src/block_4/problem_taxonomy.py::PROBLEM_REGISTRY",
                "problem_id": primary_id,
                "reason_en": "Provides controlled diagnosis metadata used by the runtime taxonomy.",
                "rationale_en": defn.portfolio_manager_interpretation_en,
            }
        )
    return refs


def _rejected_alternative_items(
    prioritization: ProblemPrioritizationResult,
    *,
    limit: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rejected in prioritization.rejected_problems[:limit]:
        defn = get_problem_definition(rejected.problem_id)
        rows.append(
            {
                "problem_id": rejected.problem_id,
                "label_en": defn.label_en if defn else rejected.problem_id,
                "reason_code": rejected.reject_reason_code,
                "reason_en": rejected.reject_reason_en,
                "top_evidence_item_ids": [
                    str(ref.get("evidence_id"))
                    for ref in rejected.top_evidence_refs
                    if isinstance(ref, dict) and ref.get("evidence_id")
                ],
            }
        )
    return rows


def _actionability(gate: NoTradeGateResult) -> dict[str, Any]:
    return {
        "outcome": gate.outcome,
        "headline_en": gate.headline_en,
        "recommended_next_step": gate.recommended_next_step,
        "launchpad_suppressed": gate.launchpad_suppressed,
        "reasons": list(gate.reasons),
    }


def _suggested_hypothesis(primary: dict[str, Any], gate: NoTradeGateResult) -> str:
    label = str(primary.get("label_en") or primary.get("problem_id") or "the diagnosis").lower()
    action = str(primary.get("suggested_action_path_id") or "").replace("_", " ")
    if gate.launchpad_suppressed:
        return (
            "Do not launch a portfolio-changing candidate yet. "
            "Monitor the evidence or use a simple benchmark only as a reference point."
        )
    return f"Test whether {action} improves {label} versus the current portfolio."


def _next_diagnostic_step(primary: dict[str, Any], gate: NoTradeGateResult) -> dict[str, Any]:
    primary_id = str(primary.get("problem_id") or "")
    if primary_id == "evidence_insufficient_data_quality":
        return {
            "type": "data_quality_improvement",
            "label": "Resolve data quality before candidate comparison",
            "reason": (
                "Diagnostic evidence is not reliable enough to compare Equal Weight, Risk Parity, "
                "or any other candidate."
            ),
            "decision_boundary": DECISION_BOUNDARY_EN,
        }
    if primary_id == "goal_risk_conflict":
        return {
            "type": "client_objective_review",
            "label": "Review objectives and risk limits before candidate testing",
            "reason": (
                "Client Fit found an internal goal-risk conflict; clarify return, volatility, "
                "drawdown, and horizon trade-offs before interpreting candidate tests."
            ),
            "candidate_method_ids": [],
            "decision_boundary": DECISION_BOUNDARY_EN,
        }
    if primary_id in {"mixed_evidence_no_action", "current_portfolio_acceptable"}:
        return {
            "type": "reference_comparison",
            "label": "Compare against Equal Weight and Risk Parity",
            "reason": (
                "Immediate rebalance is not justified, but the current allocation should be tested "
                "against simple reference portfolios."
            ),
            "candidate_method_ids": ["equal_weight", "risk_parity"],
            "decision_boundary": DECISION_BOUNDARY_EN,
        }

    action = str(primary.get("suggested_action_path_id") or "").replace("_", " ")
    label = str(primary.get("label_en") or primary_id.replace("_", " "))
    return {
        "type": "targeted_hypothesis_test",
        "label": f"Test {action}",
        "reason": f"The primary diagnosis is {label}; test the targeted hypothesis before references.",
        "decision_boundary": DECISION_BOUNDARY_EN,
    }


def _mixed_evidence_note(scoring: ProblemScoringResult, primary_id: str) -> dict[str, Any] | None:
    if not scoring.conflicting_signal_bundle:
        return None
    if primary_id == "mixed_evidence_no_action":
        return {
            "status": "primary_outcome",
            "message_en": "Mixed evidence is the reason action is not justified yet.",
        }
    return {
        "status": "warning_only",
        "message_en": (
            "Some diagnostic signals are mixed, but a stronger root-cause diagnosis dominates."
        ),
    }


def _mirror_problem_row_for_v1_shim(row: dict[str, Any]) -> dict[str, Any]:
    mirrored = dict(row)
    mirrored["label"] = row.get("label_en")
    severity = str(row.get("severity") or "")
    if severity == "medium":
        mirrored["severity"] = "moderate"
    evidence_refs = row.get("evidence_refs") if isinstance(row.get("evidence_refs"), list) else []
    mirrored["evidence"] = [_compact_evidence_ref(ref) for ref in evidence_refs if isinstance(ref, dict)]
    return mirrored


def _compact_evidence_ref(ref: dict[str, Any]) -> dict[str, Any]:
    compact = {
        "source_artifact": ref.get("source_artifact"),
        "source_block": ref.get("source_block"),
        "signal": ref.get("signal"),
        "interpretation_en": ref.get("interpretation_en"),
        "value": ref.get("value"),
        "evidence_path": ref.get("evidence_path"),
    }
    if ref.get("linked_assets"):
        compact["linked_assets"] = ref.get("linked_assets")
    if ref.get("limitation_en"):
        compact["limitation_en"] = ref.get("limitation_en")
    if ref.get("raw_field_path"):
        compact["raw_field_path"] = ref.get("raw_field_path")
    return compact


def _builder_status(
    evidence: EvidenceExtractionResult,
    portfolio_xray: dict[str, Any],
    stress_report: dict[str, Any],
) -> str:
    if not portfolio_xray or not stress_report:
        return "unavailable"
    if evidence.data_quality_warnings or evidence.has_signal("partial_sections"):
        return "partial"
    if evidence.has_signal("stress_block_unavailable"):
        return "partial"
    return "ok"


def _builder_warnings(
    evidence: EvidenceExtractionResult,
    portfolio_xray: dict[str, Any],
    stress_report: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []
    if not portfolio_xray:
        warnings.append("missing_portfolio_xray")
    if not stress_report:
        warnings.append("missing_stress_report")
    if evidence.legacy_sections_fallback_used:
        warnings.append("legacy_sections_fallback_used")
    return warnings


def _provenance_sources(
    portfolio_xray: dict[str, Any],
    stress_report: dict[str, Any],
) -> tuple[str | None, str | None]:
    hedge_gap_source: str | None = None
    stress_scorecard_source: str | None = None

    if stress_report.get("hedge_gap_analysis_v1"):
        hedge_gap_source = HEDGE_GAP_SOURCE_V1
    elif stress_report.get("stress_conclusions"):
        hedge_gap_source = HEDGE_GAP_SOURCE_LEGACY

    if stress_report.get("current_portfolio_stress_scorecard_v1"):
        stress_scorecard_source = STRESS_SCORECARD_SOURCE_V1
    elif stress_report.get("stress_scorecard_v1") or stress_report.get("stress_conclusions"):
        stress_scorecard_source = STRESS_SCORECARD_SOURCE_LEGACY

    return hedge_gap_source, stress_scorecard_source


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
