"""Product-facing Decision Verdict mapping.

This module maps the existing technical Selection Engine / No-Trade contract
into product-facing verdict language. It does not change Selection Engine
schemas, formulas, statuses, or action planning behavior.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DECISION_VERDICT_VERSION = "decision_verdict_v1"
DECISION_VERDICT_FILENAME = "decision_verdict.json"

STATUS_TO_VERDICT: dict[str, tuple[str, str]] = {
    "candidate_failed_or_infeasible": (
        "candidate_failed_or_infeasible",
        "Candidate failed or infeasible",
    ),
    "selected_candidate": (
        "rebalance_to_selected_candidate",
        "Rebalance to selected candidate for review",
    ),
    "no_material_rebalance": (
        "no_material_rebalance_recommended",
        "No material rebalance recommended",
    ),
    "inconclusive": (
        "test_another_candidate_or_review_evidence",
        "Test another candidate or review evidence",
    ),
    "data_review_required": (
        "evidence_insufficient",
        "Evidence insufficient",
    ),
    "mandate_risk_reduction": (
        "risk_reduction_required",
        "Risk reduction required before allocation change",
    ),
}

# UI filtering: Core MVP compare outcomes vs legacy policy mandate semantics.
STATUS_TO_VERDICT_FAMILY: dict[str, str] = {
    "selected_candidate": "core_compare",
    "no_material_rebalance": "core_compare",
    "inconclusive": "core_compare",
    "data_review_required": "core_compare",
    "mandate_risk_reduction": "policy_mandate",
}

HIGH_TURNOVER_HALF_SUM_THRESHOLD = 0.50
HIGH_TRANSACTION_COST_PCT_THRESHOLD = 0.005


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _selection_status(selection: dict[str, Any] | None) -> str:
    if not isinstance(selection, dict):
        return "data_review_required"
    return str(selection.get("decision_status") or "inconclusive")


def _confidence(status: str, selection: dict[str, Any] | None) -> str:
    warnings = (selection or {}).get("warnings") if isinstance(selection, dict) else None
    n_warnings = len(warnings) if isinstance(warnings, list) else 0
    if status == "selected_candidate" and n_warnings == 0:
        return "medium"
    if status == "no_material_rebalance" and n_warnings == 0:
        return "medium"
    if status in {"data_review_required", "inconclusive"}:
        return "low"
    if n_warnings:
        return "low"
    return "medium"


def _confidence_limits(
    *,
    status: str,
    selection: dict[str, Any] | None,
    current_vs_candidate: dict[str, Any] | None,
) -> list[str]:
    limits: list[str] = []
    warnings = (selection or {}).get("warnings") if isinstance(selection, dict) else None
    if isinstance(warnings, list):
        limits.extend(str(w) for w in warnings)
    if status in {"data_review_required", "inconclusive"}:
        limits.append(f"selection_status:{status}")
    if isinstance(current_vs_candidate, dict) and current_vs_candidate.get("warnings"):
        limits.extend(f"current_vs_candidate:{w}" for w in current_vs_candidate.get("warnings") or [])
    return limits


def _recommended_action(
    *,
    verdict_id: str,
    selection: dict[str, Any] | None,
    action: dict[str, Any] | None,
) -> str:
    if verdict_id == "no_material_rebalance_recommended":
        return "Keep current portfolio and monitor; no material rebalance is indicated by current thresholds."
    if verdict_id == "evidence_insufficient":
        return "Review missing or degraded evidence before acting."
    if verdict_id == "risk_reduction_required":
        return "Review mandate/risk reduction needs before considering candidate allocation changes."
    if verdict_id == "test_another_candidate_or_review_evidence":
        return "Review comparison evidence or test another candidate."
    target = (selection or {}).get("favored_display_name") or (selection or {}).get("favored_candidate_id")
    action_status = (action or {}).get("action_status") if isinstance(action, dict) else None
    if action_status:
        return f"Review implementation plan for {target or 'selected candidate'}; action status: {action_status}."
    return f"Review selected candidate {target or ''} and implementation evidence.".strip()


def _direct_candidate(candidate_generation: dict[str, Any] | None) -> dict[str, Any] | None:
    candidate = candidate_generation.get("candidate") if isinstance(candidate_generation, dict) else None
    return candidate if isinstance(candidate, dict) else None


def _first_comparison_row(current_vs_candidate: dict[str, Any] | None) -> dict[str, Any] | None:
    rows = (
        current_vs_candidate.get("comparisons")
        if isinstance(current_vs_candidate, dict)
        else None
    )
    if isinstance(rows, list) and rows and isinstance(rows[0], dict):
        return rows[0]
    return None


def _selected_candidate_id_from_current_vs(
    current_vs_candidate: dict[str, Any] | None,
) -> str | None:
    selected = (
        current_vs_candidate.get("selected_candidate_ids")
        if isinstance(current_vs_candidate, dict)
        else None
    )
    if isinstance(selected, list) and selected:
        return str(selected[0])
    return None


def _comparison_warnings(current_vs_candidate: dict[str, Any] | None) -> list[str]:
    warnings = (
        current_vs_candidate.get("warnings")
        if isinstance(current_vs_candidate, dict)
        else None
    )
    return [str(item) for item in warnings] if isinstance(warnings, list) else []


def _available_dimensions(row: dict[str, Any] | None) -> list[dict[str, Any]]:
    dimensions = row.get("dimensions") if isinstance(row, dict) else None
    if not isinstance(dimensions, list):
        return []
    return [
        item
        for item in dimensions
        if isinstance(item, dict) and item.get("status") == "available"
    ]


def _method_quality_problem(
    candidate_generation: dict[str, Any] | None,
    row: dict[str, Any] | None,
) -> str | None:
    availability = (
        candidate_generation.get("method_availability")
        if isinstance(candidate_generation, dict)
        else None
    )
    if isinstance(availability, dict):
        if availability.get("available") is False:
            return "method_unavailable"
        status = str(availability.get("availability_status") or "available")
        if status not in {"available", "not_applicable"}:
            return f"method_availability:{status}"
    if isinstance(row, dict) and str(row.get("status") or "") == "degraded":
        return "comparison_row_degraded"
    data_quality = row.get("data_quality") if isinstance(row, dict) else None
    if isinstance(data_quality, dict):
        disclosure_status = str(data_quality.get("construction_disclosure_status") or "")
        if disclosure_status in {"missing", "unavailable", "unknown", "degraded", "failed"}:
            return f"construction_disclosure:{disclosure_status}"
    return None


def _data_quality_problem(
    current_vs_candidate: dict[str, Any] | None,
    row: dict[str, Any] | None,
) -> str | None:
    blocking_warnings = [
        warning
        for warning in _comparison_warnings(current_vs_candidate)
        if warning.startswith("baseline_unavailable")
        or warning.startswith("candidate_unavailable:")
    ]
    if blocking_warnings:
        return blocking_warnings[0]
    data_quality = row.get("data_quality") if isinstance(row, dict) else None
    if isinstance(data_quality, dict) and data_quality.get("missing_fields"):
        return "comparison_row_missing_fields"
    if row is not None and not _available_dimensions(row):
        return "no_available_comparison_metrics"
    return None


def _turnover_block(row: dict[str, Any] | None) -> dict[str, Any]:
    practicality = row.get("practicality") if isinstance(row, dict) else None
    if not isinstance(practicality, dict):
        return {"applies": False, "reason": "practicality_missing"}
    turnover = practicality.get("turnover_required")
    turnover_value = None
    if isinstance(turnover, dict):
        try:
            turnover_value = float(turnover.get("turnover_half_sum_pct"))
        except (TypeError, ValueError):
            turnover_value = None
    cost_value = None
    try:
        cost_value = float(practicality.get("estimated_transaction_cost_pct"))
    except (TypeError, ValueError):
        cost_value = None
    applies = (
        turnover_value is not None
        and turnover_value >= HIGH_TURNOVER_HALF_SUM_THRESHOLD
    ) or (
        cost_value is not None
        and cost_value >= HIGH_TRANSACTION_COST_PCT_THRESHOLD
    )
    return {
        "applies": applies,
        "turnover_half_sum_pct": turnover_value,
        "high_turnover_threshold": HIGH_TURNOVER_HALF_SUM_THRESHOLD,
        "estimated_transaction_cost_pct": cost_value,
        "high_transaction_cost_threshold": HIGH_TRANSACTION_COST_PCT_THRESHOLD,
    }


def _direct_recommended_action(
    *,
    verdict_id: str,
    reason_id: str,
    selected_candidate_id: str | None,
) -> str:
    candidate = selected_candidate_id or "selected candidate"
    if verdict_id == "rebalance_to_selected_candidate":
        return (
            f"Candidate {candidate} is material enough for rebalance review; "
            "confirm the documented trade-offs before any implementation."
        )
    if reason_id == "risk_improved_but_turnover_too_high":
        return (
            "Keep current portfolio for now: risk evidence improved, but the "
            "required turnover or estimated cost is too high for an automatic rebalance."
        )
    if reason_id == "keep_current_portfolio":
        return "Keep current portfolio; this candidate did not satisfy the stated hypothesis."
    if verdict_id == "no_material_rebalance_recommended":
        return "Keep current portfolio and monitor; the candidate does not show material enough improvement."
    if verdict_id == "test_another_candidate_or_review_evidence":
        return "Do not rebalance on this candidate; test another candidate or refine the hypothesis."
    return "Review missing or degraded evidence before acting."


def _direct_rationale(
    *,
    reason_id: str,
    row: dict[str, Any] | None,
    materiality: dict[str, Any],
    success: dict[str, Any],
    turnover: dict[str, Any],
) -> str:
    if reason_id in {"candidate_generation_failed", "candidate_generation_infeasible"}:
        return "Candidate generation did not produce comparable weights, so no action verdict can be supported."
    if reason_id == "candidate_failed_or_infeasible":
        return "Candidate generation failed or was infeasible, so Block 8 comparison must remain blocked."
    if reason_id in {"insufficient_data_quality", "insufficient_optimizer_or_method_quality"}:
        return "The comparison or method evidence is degraded or incomplete, so the verdict is evidence insufficient."
    if reason_id == "risk_improved_but_turnover_too_high":
        return "Risk evidence improved, but practicality evidence blocks a rebalance verdict."
    if reason_id == "rebalance_when_material":
        return "The selected candidate shows material improvement against the available comparison evidence."
    if reason_id == "keep_current_portfolio":
        return "The candidate does not meet the stated success criteria, so the current portfolio should be kept."
    if reason_id == "test_another_candidate":
        return "The evidence is mixed or the hypothesis is not clearly evaluated, so another candidate should be tested."
    if reason_id == "no_material_rebalance":
        return str(materiality.get("reason") or "No material improvement detected.")
    return (
        f"materiality={materiality.get('status')}; "
        f"success_criteria={success.get('overall_status')}; "
        f"turnover_block={turnover.get('applies')}; "
        f"candidate={row.get('candidate_id') if isinstance(row, dict) else None}"
    )


def build_decision_verdict_from_block7_8(
    *,
    candidate_generation: dict[str, Any] | None,
    current_vs_candidate: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build Block 9 directly from Block 7 and Block 8 evidence.

    This is the vertical product-loop builder.  It does not use the advanced
    Selection Engine ranking and it does not claim that a candidate is the
    "best portfolio"; it evaluates one generated hypothesis against the
    current-vs-candidate evidence.
    """

    candidate = _direct_candidate(candidate_generation)
    generation_status = (
        str(candidate_generation.get("generation_status") or "")
        if isinstance(candidate_generation, dict)
        else ""
    )
    handoff = (
        candidate_generation.get("handoff_to_comparison")
        if isinstance(candidate_generation, dict)
        else None
    )
    selected_candidate_id = (
        str(candidate.get("candidate_id"))
        if isinstance(candidate, dict) and candidate.get("candidate_id")
        else _selected_candidate_id_from_current_vs(current_vs_candidate)
    )
    baseline = (
        current_vs_candidate.get("baseline")
        if isinstance(current_vs_candidate, dict)
        else None
    )
    baseline_id = (
        str(baseline.get("candidate_id"))
        if isinstance(baseline, dict) and baseline.get("candidate_id")
        else None
    )
    row = _first_comparison_row(current_vs_candidate)
    materiality = (
        row.get("materiality_for_decision_review")
        if isinstance(row, dict) and isinstance(row.get("materiality_for_decision_review"), dict)
        else {}
    )
    success = (
        row.get("success_criteria_result")
        if isinstance(row, dict) and isinstance(row.get("success_criteria_result"), dict)
        else {}
    )
    turnover = _turnover_block(row)
    confidence_limitations: list[str] = []
    confidence_limitations.extend(
        f"candidate_generation:{warning}"
        for warning in (
            candidate_generation.get("warnings")
            if isinstance(candidate_generation, dict)
            else []
        )
        or []
    )
    confidence_limitations.extend(
        f"current_vs_candidate:{warning}" for warning in _comparison_warnings(current_vs_candidate)
    )

    if not isinstance(candidate_generation, dict) or not isinstance(candidate, dict):
        status = "data_review_required"
        reason_id = "candidate_generation_missing"
    elif generation_status in {"failed", "infeasible"}:
        status = "candidate_failed_or_infeasible"
        reason_id = "candidate_failed_or_infeasible"
        reason = candidate.get("failure_reason") or candidate.get("infeasibility_reason")
        if reason:
            confidence_limitations.append(str(reason))
    elif isinstance(handoff, dict) and handoff.get("can_compare") is False:
        status = "data_review_required"
        reason_id = "candidate_not_comparable"
        if handoff.get("blocked_reason"):
            confidence_limitations.append(str(handoff.get("blocked_reason")))
    elif not isinstance(current_vs_candidate, dict) or row is None:
        status = "data_review_required"
        reason_id = "current_vs_candidate_missing"
    elif (quality_problem := _data_quality_problem(current_vs_candidate, row)) is not None:
        status = "data_review_required"
        reason_id = "insufficient_data_quality"
        confidence_limitations.append(quality_problem)
    elif (method_problem := _method_quality_problem(candidate_generation, row)) is not None:
        status = "data_review_required"
        reason_id = "insufficient_optimizer_or_method_quality"
        confidence_limitations.append(method_problem)
    elif str(materiality.get("status") or "") == "insufficient_evidence":
        status = "data_review_required"
        reason_id = "insufficient_data_quality"
        confidence_limitations.append(str(materiality.get("reason") or "insufficient_evidence"))
    elif turnover.get("applies") and row.get("risk_reduced"):
        status = "no_material_rebalance"
        reason_id = "risk_improved_but_turnover_too_high"
    elif success.get("overall_status") in {"not_met", "unavailable"}:
        status = "no_material_rebalance"
        reason_id = "keep_current_portfolio"
    elif materiality.get("is_material_enough") is True:
        status = "selected_candidate"
        reason_id = "rebalance_when_material"
    elif success.get("overall_status") in {"mixed", "not_evaluated"}:
        status = "inconclusive"
        reason_id = "test_another_candidate"
    else:
        status = "no_material_rebalance"
        reason_id = "no_material_rebalance"

    verdict_id, verdict_label = STATUS_TO_VERDICT.get(
        status,
        ("evidence_insufficient", "Evidence insufficient"),
    )
    verdict_family = STATUS_TO_VERDICT_FAMILY.get(status, "core_compare")
    confidence = "low" if status in {"data_review_required", "inconclusive", "candidate_failed_or_infeasible"} else "medium"
    no_trade_applies = status == "no_material_rebalance"
    no_trade_evaluated = status not in {"data_review_required", "candidate_failed_or_infeasible"}
    no_trade_source = {
        "source": "block_7_8_direct_evidence",
        "reason_id": reason_id,
        "turnover_block": turnover,
        "materiality_for_decision_review": materiality,
        "success_criteria_result": success,
    }

    return {
        "schema_version": DECISION_VERDICT_VERSION,
        "diagnostic_only": False,
        "generated_at": _utc_now_iso(),
        "verdict_id": verdict_id,
        "verdict_label": verdict_label,
        "verdict_family": verdict_family,
        "selection_decision_status": status,
        "baseline_candidate_id": baseline_id,
        "selected_candidate_id": selected_candidate_id if status == "selected_candidate" else None,
        "reviewed_candidate_id": selected_candidate_id,
        "verdict_reason_id": reason_id,
        "no_trade": {
            "evaluated": no_trade_evaluated,
            "applies": no_trade_applies,
            "source": no_trade_source,
        },
        "recommended_action": _direct_recommended_action(
            verdict_id=verdict_id,
            reason_id=reason_id,
            selected_candidate_id=selected_candidate_id,
        ),
        "confidence": confidence,
        "confidence_limitations": confidence_limitations,
        "rationale_summary": _direct_rationale(
            reason_id=reason_id,
            row=row,
            materiality=materiality,
            success=success,
            turnover=turnover,
        ),
        "evidence_summary": {
            "generation_status": generation_status or None,
            "method_availability": (
                candidate_generation.get("method_availability")
                if isinstance(candidate_generation, dict)
                else None
            ),
            "materiality_for_decision_review": materiality or None,
            "success_criteria_result": success or None,
            "risk_reduced": row.get("risk_reduced") if isinstance(row, dict) else [],
            "risk_added": row.get("risk_added") if isinstance(row, dict) else [],
            "what_improved": row.get("what_improved") if isinstance(row, dict) else [],
            "what_worsened": row.get("what_worsened") if isinstance(row, dict) else [],
            "practicality": row.get("practicality") if isinstance(row, dict) else None,
        },
        "source_artifacts": {
            "selection_decision": None,
            "candidate_generation": "candidate_generation.json"
            if isinstance(candidate_generation, dict)
            else None,
            "current_vs_candidate": "current_vs_candidate.json"
            if isinstance(current_vs_candidate, dict)
            else None,
            "action_plan": None,
        },
        "guardrails": {
            "does_not_rename_selection_engine_contract": True,
            "does_not_change_selection_formulas": True,
            "does_not_execute_trades": True,
            "does_not_claim_best_portfolio": True,
            "does_not_hide_tradeoffs": True,
        },
    }


def build_decision_verdict(
    *,
    selection: dict[str, Any] | None,
    current_vs_candidate: dict[str, Any] | None = None,
    action: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build product-facing verdict from existing technical artifacts."""

    status = _selection_status(selection)
    verdict_id, verdict_label = STATUS_TO_VERDICT.get(
        status,
        ("evidence_insufficient", "Evidence insufficient"),
    )
    no_trade = (selection or {}).get("no_trade") if isinstance(selection, dict) else None
    confidence = _confidence(status, selection)
    favored_id = (selection or {}).get("favored_candidate_id") if isinstance(selection, dict) else None
    baseline_id = (selection or {}).get("baseline_candidate_id") if isinstance(selection, dict) else None
    if not baseline_id and isinstance(no_trade, dict):
        baseline_id = no_trade.get("baseline_candidate_id")
    rationale = (selection or {}).get("rationale") if isinstance(selection, dict) else None
    rationale_summary = rationale.get("summary") if isinstance(rationale, dict) else None

    verdict_family = STATUS_TO_VERDICT_FAMILY.get(status, "core_compare")

    return {
        "schema_version": DECISION_VERDICT_VERSION,
        "diagnostic_only": False,
        "generated_at": _utc_now_iso(),
        "verdict_id": verdict_id,
        "verdict_label": verdict_label,
        "verdict_family": verdict_family,
        "selection_decision_status": status,
        "baseline_candidate_id": baseline_id,
        "selected_candidate_id": favored_id,
        "no_trade": {
            "evaluated": bool(isinstance(no_trade, dict) and no_trade.get("evaluated")),
            "applies": status == "no_material_rebalance",
            "source": no_trade if isinstance(no_trade, dict) else None,
        },
        "recommended_action": _recommended_action(
            verdict_id=verdict_id,
            selection=selection,
            action=action,
        ),
        "confidence": confidence,
        "confidence_limitations": _confidence_limits(
            status=status,
            selection=selection,
            current_vs_candidate=current_vs_candidate,
        ),
        "rationale_summary": rationale_summary,
        "source_artifacts": {
            "selection_decision": (
                selection.get("source_artifact", "selection_decision.json")
                if isinstance(selection, dict) and not selection.get("support_only")
                else None
            ),
            "current_vs_candidate": "current_vs_candidate.json"
            if isinstance(current_vs_candidate, dict)
            else None,
            "action_plan": "action_plan.json" if isinstance(action, dict) else None,
        },
        "guardrails": {
            "does_not_rename_selection_engine_contract": True,
            "does_not_change_selection_formulas": True,
            "does_not_execute_trades": True,
        },
    }


def write_decision_verdict_outputs(
    *,
    output_dir: str | Path,
    selection: dict[str, Any] | None = None,
    current_vs_candidate: dict[str, Any] | None = None,
    action: dict[str, Any] | None = None,
    candidate_generation: dict[str, Any] | None = None,
) -> dict[str, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    if selection is None and (
        candidate_generation is not None or current_vs_candidate is not None
    ):
        doc = build_decision_verdict_from_block7_8(
            candidate_generation=candidate_generation,
            current_vs_candidate=current_vs_candidate,
        )
    else:
        doc = build_decision_verdict(
            selection=selection,
            current_vs_candidate=current_vs_candidate,
            action=action,
        )
    path = out / DECISION_VERDICT_FILENAME
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False, default=str)
    return {"decision_verdict_json": path}
