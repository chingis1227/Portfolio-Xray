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
    selection: dict[str, Any] | None,
    current_vs_candidate: dict[str, Any] | None = None,
    action: dict[str, Any] | None = None,
) -> dict[str, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    doc = build_decision_verdict(
        selection=selection,
        current_vs_candidate=current_vs_candidate,
        action=action,
    )
    path = out / DECISION_VERDICT_FILENAME
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False, default=str)
    return {"decision_verdict_json": path}
