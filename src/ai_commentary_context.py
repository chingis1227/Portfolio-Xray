"""Grounding context for product-facing AI Commentary.

This module builds a deterministic evidence bundle that an AI commentary layer
may consume later. It does not call an LLM, calculate metrics, set decisions,
or change any existing decision/selection contract.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AI_COMMENTARY_CONTEXT_VERSION = "ai_commentary_context_v1"
AI_COMMENTARY_CONTEXT_FILENAME = "ai_commentary_context.json"
PURPOSE_GROUNDED_DECISION_CONTEXT = "grounded_ai_commentary_context"
PURPOSE_DIAGNOSIS_GROUNDING_ONLY = "diagnosis_grounding_only"

ALLOWED_SOURCE_ARTIFACTS: tuple[str, ...] = (
    "portfolio_xray.json",
    "stress_report.json",
    "problem_classification.json",
    "candidate_launchpad.json",
    "candidate_comparison.json",
    "current_vs_candidate.json",
    "selection_decision.json",
    "decision_verdict.json",
    "action_plan.json",
    "monitoring_diff.json",
)

FORBIDDEN_CLAIM_CATEGORIES: tuple[str, ...] = (
    "new_metric_calculation",
    "unsupported_verdict",
    "trade_execution_instruction",
    "schema_rename",
    "data_quality_status_creation",
    "performance_guarantee",
    "optimizer_formula_change",
    "unstated_tax_advice",
)

REQUIRED_GROUNDING_RULES: tuple[str, ...] = (
    "Use only values and statuses present in allowed source artifacts.",
    "Every material claim must cite an artifact and field path.",
    "Do not compute new metrics, thresholds, rankings, or optimizer results.",
    "Do not rename or reinterpret Selection Engine statuses.",
    "Do not issue trade execution instructions or binding investment advice.",
    "State evidence gaps and confidence limitations when source artifacts warn or are missing.",
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _source_name(name: str, doc: dict[str, Any] | None) -> str | None:
    return name if isinstance(doc, dict) else None


def _append_reference(
    refs: list[dict[str, Any]],
    *,
    artifact: str,
    field_path: str,
    value: Any = None,
    summary: str | None = None,
) -> None:
    ref: dict[str, Any] = {"artifact": artifact, "field_path": field_path}
    if value is not None:
        ref["value"] = value
    if summary:
        ref["summary"] = summary
    refs.append(ref)


def _problem_refs(problem_classification: dict[str, Any] | None) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    if not isinstance(problem_classification, dict):
        return refs
    problems = problem_classification.get("problems")
    if isinstance(problems, list):
        for idx, problem in enumerate(problems[:5]):
            if not isinstance(problem, dict):
                continue
            _append_reference(
                refs,
                artifact="problem_classification.json",
                field_path=f"problems[{idx}]",
                value={
                    "problem_id": problem.get("problem_id"),
                    "severity": problem.get("severity"),
                    "status": problem.get("status"),
                },
            )
    return refs


def _launchpad_refs(candidate_launchpad: dict[str, Any] | None) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    if not isinstance(candidate_launchpad, dict):
        return refs
    cards = candidate_launchpad.get("cards")
    if isinstance(cards, list):
        for idx, card in enumerate(cards[:5]):
            if not isinstance(card, dict):
                continue
            _append_reference(
                refs,
                artifact="candidate_launchpad.json",
                field_path=f"cards[{idx}]",
                value={
                    "card_id": card.get("card_id"),
                    "goal": card.get("goal"),
                    "method_id": card.get("method_id"),
                },
            )
    return refs


def _comparison_refs(
    comparison: dict[str, Any] | None,
    current_vs_candidate: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    if isinstance(comparison, dict):
        _append_reference(
            refs,
            artifact="candidate_comparison.json",
            field_path="comparison_baseline_candidate_id",
            value=comparison.get("comparison_baseline_candidate_id"),
        )
        _append_reference(
            refs,
            artifact="candidate_comparison.json",
            field_path="candidate_menu.factory_evidence_status",
            value=(comparison.get("candidate_menu") or {}).get("factory_evidence_status")
            if isinstance(comparison.get("candidate_menu"), dict)
            else None,
        )
    if isinstance(current_vs_candidate, dict):
        _append_reference(
            refs,
            artifact="current_vs_candidate.json",
            field_path="view_mode",
            value=current_vs_candidate.get("view_mode"),
        )
        for idx, row in enumerate(current_vs_candidate.get("comparisons") or []):
            if not isinstance(row, dict):
                continue
            _append_reference(
                refs,
                artifact="current_vs_candidate.json",
                field_path=f"comparisons[{idx}]",
                value={
                    "candidate_id": row.get("candidate_id"),
                    "status": row.get("status"),
                    "dimension_count": len(row.get("dimensions") or []),
                },
            )
    return refs


def _decision_refs(
    selection: dict[str, Any] | None,
    decision_verdict: dict[str, Any] | None,
    action: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    if isinstance(selection, dict):
        _append_reference(
            refs,
            artifact="selection_decision.json",
            field_path="decision_status",
            value=selection.get("decision_status"),
        )
        _append_reference(
            refs,
            artifact="selection_decision.json",
            field_path="favored_candidate_id",
            value=selection.get("favored_candidate_id"),
        )
        no_trade = selection.get("no_trade")
        if isinstance(no_trade, dict):
            _append_reference(
                refs,
                artifact="selection_decision.json",
                field_path="no_trade",
                value={
                    "evaluated": no_trade.get("evaluated"),
                    "baseline_candidate_id": no_trade.get("baseline_candidate_id"),
                    "target_candidate_id": no_trade.get("target_candidate_id"),
                },
            )
    if isinstance(decision_verdict, dict):
        _append_reference(
            refs,
            artifact="decision_verdict.json",
            field_path="verdict_id",
            value=decision_verdict.get("verdict_id"),
        )
        _append_reference(
            refs,
            artifact="decision_verdict.json",
            field_path="confidence",
            value=decision_verdict.get("confidence"),
        )
    if isinstance(action, dict):
        _append_reference(
            refs,
            artifact="action_plan.json",
            field_path="action_status",
            value=action.get("action_status"),
        )
    return refs


def _xray_refs(portfolio_xray: dict[str, Any] | None) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    if not isinstance(portfolio_xray, dict):
        return refs
    _append_reference(
        refs,
        artifact="portfolio_xray.json",
        field_path="version",
        value=portfolio_xray.get("version"),
    )
    _append_reference(
        refs,
        artifact="portfolio_xray.json",
        field_path="diagnostic_only",
        value=portfolio_xray.get("diagnostic_only"),
    )
    block_2_6 = portfolio_xray.get("block_2_6_portfolio_weakness_map")
    if isinstance(block_2_6, dict):
        _append_reference(
            refs,
            artifact="portfolio_xray.json",
            field_path="block_2_6_portfolio_weakness_map.status",
            value=block_2_6.get("status"),
            summary=str(block_2_6.get("summary") or "")[:240] or None,
        )
    legacy = portfolio_xray.get("legacy_summary")
    if isinstance(legacy, dict):
        scope = legacy.get("_scope")
        if isinstance(scope, dict) and scope.get("product_surface") is not None:
            _append_reference(
                refs,
                artifact="portfolio_xray.json",
                field_path="legacy_summary._scope.product_surface",
                value=scope.get("product_surface"),
            )
    return refs


def _stress_refs(stress_report: dict[str, Any] | None) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    if not isinstance(stress_report, dict):
        return refs
    _append_reference(
        refs,
        artifact="stress_report.json",
        field_path="status",
        value=stress_report.get("status"),
    )
    _append_reference(
        refs,
        artifact="stress_report.json",
        field_path="loss_gate_mode",
        value=stress_report.get("loss_gate_mode"),
    )
    primary = (
        stress_report.get("primary_diagnostic_code")
        or stress_report.get("fail_reason_code")
        or stress_report.get("skip_reason")
    )
    if primary is not None:
        _append_reference(
            refs,
            artifact="stress_report.json",
            field_path="primary_diagnostic_code",
            value=primary,
        )
    worst = stress_report.get("worst_scenario_loss_pct")
    if worst is not None:
        _append_reference(
            refs,
            artifact="stress_report.json",
            field_path="worst_scenario_loss_pct",
            value=worst,
        )
    scorecard = stress_report.get("stress_scorecard_v1")
    if isinstance(scorecard, dict):
        _append_reference(
            refs,
            artifact="stress_report.json",
            field_path="stress_scorecard_v1.overall_status",
            value=scorecard.get("overall_status"),
        )
    return refs


def _is_post_compare_context(
    *,
    comparison: dict[str, Any] | None,
    current_vs_candidate: dict[str, Any] | None,
    selection: dict[str, Any] | None,
    decision_verdict: dict[str, Any] | None,
) -> bool:
    return all(
        isinstance(doc, dict)
        for doc in (comparison, current_vs_candidate, selection, decision_verdict)
    )


def _monitoring_refs(monitoring_diff: dict[str, Any] | None) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    if not isinstance(monitoring_diff, dict):
        return refs
    _append_reference(
        refs,
        artifact="monitoring_diff.json",
        field_path="change_status",
        value=monitoring_diff.get("change_status"),
    )
    return refs


def _warnings(
    *,
    comparison: dict[str, Any] | None,
    current_vs_candidate: dict[str, Any] | None,
    selection: dict[str, Any] | None,
    decision_verdict: dict[str, Any] | None,
    portfolio_xray: dict[str, Any] | None = None,
    stress_report: dict[str, Any] | None = None,
    diagnosis_only: bool = False,
) -> list[str]:
    warnings: list[str] = []
    if diagnosis_only:
        if not isinstance(portfolio_xray, dict):
            warnings.append("missing_diagnosis_source:portfolio_xray.json")
        if not isinstance(stress_report, dict):
            warnings.append("missing_diagnosis_source:stress_report.json")
        return warnings
    required = {
        "candidate_comparison.json": comparison,
        "current_vs_candidate.json": current_vs_candidate,
        "selection_decision.json": selection,
        "decision_verdict.json": decision_verdict,
    }
    for name, doc in required.items():
        if not isinstance(doc, dict):
            warnings.append(f"missing_required_source:{name}")
    for source_name, doc in (
        ("current_vs_candidate.json", current_vs_candidate),
        ("selection_decision.json", selection),
        ("decision_verdict.json", decision_verdict),
    ):
        source_warnings = doc.get("warnings") if isinstance(doc, dict) else None
        if isinstance(source_warnings, list):
            warnings.extend(f"{source_name}:{warning}" for warning in source_warnings)
        limits = doc.get("confidence_limitations") if isinstance(doc, dict) else None
        if isinstance(limits, list):
            warnings.extend(f"{source_name}:confidence_limit:{limit}" for limit in limits)
    return warnings


def build_ai_commentary_context(
    *,
    comparison: dict[str, Any] | None,
    current_vs_candidate: dict[str, Any] | None,
    selection: dict[str, Any] | None,
    decision_verdict: dict[str, Any] | None,
    action: dict[str, Any] | None = None,
    problem_classification: dict[str, Any] | None = None,
    candidate_launchpad: dict[str, Any] | None = None,
    monitoring_diff: dict[str, Any] | None = None,
    portfolio_xray: dict[str, Any] | None = None,
    stress_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the deterministic evidence contract for future AI Commentary."""

    post_compare = _is_post_compare_context(
        comparison=comparison,
        current_vs_candidate=current_vs_candidate,
        selection=selection,
        decision_verdict=decision_verdict,
    )
    diagnosis_only = not post_compare

    evidence_references: list[dict[str, Any]] = []
    evidence_references.extend(_xray_refs(portfolio_xray))
    evidence_references.extend(_stress_refs(stress_report))
    evidence_references.extend(_problem_refs(problem_classification))
    evidence_references.extend(_launchpad_refs(candidate_launchpad))
    if post_compare:
        evidence_references.extend(_comparison_refs(comparison, current_vs_candidate))
        evidence_references.extend(_decision_refs(selection, decision_verdict, action))
    evidence_references.extend(_monitoring_refs(monitoring_diff))

    purpose = (
        PURPOSE_DIAGNOSIS_GROUNDING_ONLY
        if diagnosis_only
        else PURPOSE_GROUNDED_DECISION_CONTEXT
    )

    return {
        "schema_version": AI_COMMENTARY_CONTEXT_VERSION,
        "diagnostic_only": True,
        "generated_at": _utc_now_iso(),
        "purpose": purpose,
        "grounding_phase": "diagnosis_only" if diagnosis_only else "post_compare",
        "allowed_source_artifacts": list(ALLOWED_SOURCE_ARTIFACTS),
        "forbidden_claim_categories": list(FORBIDDEN_CLAIM_CATEGORIES),
        "required_grounding_rules": list(REQUIRED_GROUNDING_RULES),
        "commentary_topics": {
            "portfolio_diagnosis": "Use Portfolio X-Ray, Stress Test Lab, and Problem Classification when available.",
            "candidate_logic": "Use Candidate Launchpad and current-vs-candidate evidence; do not invent weights.",
            "current_vs_candidate": "Explain only projected dimensions present in current_vs_candidate.json.",
            "decision_verdict": "Use decision_verdict.json as product language and selection_decision.json as technical source.",
            "no_trade": "If no-trade applies, cite selection_decision.json.no_trade and decision_verdict.json.",
            "monitoring_next": "Use monitoring_diff.json only when available; otherwise state that monitoring context is absent.",
        },
        "evidence_references": evidence_references,
        "source_artifacts": {
            "portfolio_xray": _source_name("portfolio_xray.json", portfolio_xray),
            "stress_report": _source_name("stress_report.json", stress_report),
            "problem_classification": _source_name("problem_classification.json", problem_classification),
            "candidate_launchpad": _source_name("candidate_launchpad.json", candidate_launchpad),
            "candidate_comparison": _source_name("candidate_comparison.json", comparison),
            "current_vs_candidate": _source_name("current_vs_candidate.json", current_vs_candidate),
            "selection_decision": _source_name("selection_decision.json", selection),
            "decision_verdict": _source_name("decision_verdict.json", decision_verdict),
            "action_plan": _source_name("action_plan.json", action),
            "monitoring_diff": _source_name("monitoring_diff.json", monitoring_diff),
        },
        "guardrails": {
            "does_not_call_llm": True,
            "does_not_calculate_metrics": True,
            "does_not_change_selection_or_verdict": True,
            "does_not_execute_trades": True,
        },
        "warnings": _warnings(
            comparison=comparison,
            current_vs_candidate=current_vs_candidate,
            selection=selection,
            decision_verdict=decision_verdict,
            portfolio_xray=portfolio_xray,
            stress_report=stress_report,
            diagnosis_only=diagnosis_only,
        ),
    }


def write_ai_commentary_context_outputs(
    *,
    output_dir: str | Path,
    comparison: dict[str, Any] | None,
    current_vs_candidate: dict[str, Any] | None,
    selection: dict[str, Any] | None,
    decision_verdict: dict[str, Any] | None,
    action: dict[str, Any] | None = None,
    problem_classification: dict[str, Any] | None = None,
    candidate_launchpad: dict[str, Any] | None = None,
    monitoring_diff: dict[str, Any] | None = None,
    portfolio_xray: dict[str, Any] | None = None,
    stress_report: dict[str, Any] | None = None,
) -> dict[str, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    doc = build_ai_commentary_context(
        comparison=comparison,
        current_vs_candidate=current_vs_candidate,
        selection=selection,
        decision_verdict=decision_verdict,
        action=action,
        problem_classification=problem_classification,
        candidate_launchpad=candidate_launchpad,
        monitoring_diff=monitoring_diff,
        portfolio_xray=portfolio_xray,
        stress_report=stress_report,
    )
    path = out / AI_COMMENTARY_CONTEXT_FILENAME
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False, default=str)
    return {"ai_commentary_context_json": path}
