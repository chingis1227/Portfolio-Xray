"""
Current-vs-policy workflow status artifact.

See docs/specs/current_vs_policy_workflow_spec.md.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.candidate_comparison import (
    CURRENT_SIDECAR_SUBDIR,
    positive_current_weights,
    sidecar_meets_minimum,
)
from src.config_schema import PortfolioConfig

SCHEMA_VERSION = "current_vs_policy_status_v1"
ELIGIBLE_ROW_STATUSES = frozenset({"available", "degraded"})
MATERIALIZE_COMMAND = "python run_report.py --materialize-current"

_SKIP_MESSAGES: dict[str, str] = {
    "current_not_configured": (
        "Current weights were not supplied; No-Trade versus current was not evaluated."
    ),
    "current_not_materialized": (
        "Current weights are configured but not materialized; run current materialization "
        "before comparing to policy."
    ),
    "current_only_diagnostic_mode": (
        "This run diagnoses current holdings only; compare to policy after a combined workflow."
    ),
    "policy_target_unavailable": (
        "Policy target is unavailable; No-Trade versus current was not evaluated."
    ),
    "weights_not_loadable": (
        "Weight vectors could not be loaded; No-Trade and trades were skipped."
    ),
    "mandate_or_data_block": (
        "Resolve mandate or data issues before interpreting versus-current results."
    ),
}


def _candidate_by_id(comparison: dict[str, Any], candidate_id: str) -> dict[str, Any] | None:
    for row in comparison.get("candidates") or []:
        if row.get("candidate_id") == candidate_id:
            return row
    return None


def _row_status(comparison: dict[str, Any], candidate_id: str) -> str:
    row = _candidate_by_id(comparison, candidate_id)
    if not row:
        return "unavailable"
    return str(row.get("status") or "unavailable")


def _resolve_skip_reason(
    *,
    analysis_mode: str,
    cfg: PortfolioConfig,
    policy_status: str,
    current_status: str,
    current_reason: str | None,
    output_dir_final: Path,
    selection: dict[str, Any] | None,
) -> str | None:
    if analysis_mode == "analyze_current_weights":
        return "current_only_diagnostic_mode"

    decision_status = (selection or {}).get("decision_status")
    if decision_status in ("mandate_risk_reduction", "data_review_required"):
        return "mandate_or_data_block"

    if policy_status not in ELIGIBLE_ROW_STATUSES:
        return "policy_target_unavailable"

    if not positive_current_weights(cfg):
        return "current_not_configured"

    if current_status not in ELIGIBLE_ROW_STATUSES:
        if current_reason == "missing_current_report":
            return "current_not_materialized"
        return "current_not_configured"

    sidecar = output_dir_final / CURRENT_SIDECAR_SUBDIR
    if positive_current_weights(cfg) and not sidecar_meets_minimum(sidecar):
        return "current_not_materialized"

    warnings = list((selection or {}).get("warnings") or [])
    if "no_trade_skipped_missing_weights" in warnings:
        return "weights_not_loadable"

    return None


def build_current_vs_policy_status(
    comparison: dict[str, Any],
    cfg: PortfolioConfig,
    *,
    project_root: Path | None = None,
    selection: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build current_vs_policy_status_v1 from comparison (and optional selection)."""
    project_root = project_root or Path.cwd()
    analysis_mode = str(getattr(cfg, "analysis_mode", "optimize_from_universe"))
    out_rel = str(getattr(cfg, "output_dir_final", "Main portfolio")).replace("\\", "/")
    output_dir_final = project_root / out_rel

    policy_status = _row_status(comparison, "policy")
    current_status = _row_status(comparison, "current")
    current_row = _candidate_by_id(comparison, "current") or {}
    current_reason = current_row.get("unavailable_reason")

    combined_complete = (
        policy_status in ELIGIBLE_ROW_STATUSES and current_status in ELIGIBLE_ROW_STATUSES
    )

    if analysis_mode == "analyze_current_weights":
        workflow_profile = "current_only_diagnostic"
    elif combined_complete and analysis_mode == "optimize_from_universe":
        workflow_profile = "combined_current_vs_policy"
    else:
        workflow_profile = "policy_only"

    skip_reason = _resolve_skip_reason(
        analysis_mode=analysis_mode,
        cfg=cfg,
        policy_status=policy_status,
        current_status=current_status,
        current_reason=current_reason,
        output_dir_final=output_dir_final,
        selection=selection,
    )

    no_trade_actionable = (
        workflow_profile == "combined_current_vs_policy"
        and skip_reason is None
        and (selection or {}).get("decision_status") != "mandate_risk_reduction"
    )

    sidecar = output_dir_final / CURRENT_SIDECAR_SUBDIR
    materialization_required = (
        analysis_mode == "optimize_from_universe" and positive_current_weights(cfg)
    )
    materialization_completed = sidecar_meets_minimum(sidecar)

    current_artifact_root: str | None = None
    if current_row.get("artifact_root"):
        current_artifact_root = str(current_row["artifact_root"]).replace("\\", "/")
    elif materialization_completed:
        current_artifact_root = f"{out_rel}/{CURRENT_SIDECAR_SUBDIR}"

    if no_trade_actionable:
        user_message_en = (
            "Current and policy profiles are both in this comparison; "
            "No-Trade versus current was evaluated when selection ran."
        )
    elif skip_reason:
        user_message_en = _SKIP_MESSAGES.get(
            skip_reason,
            "No-Trade versus current was not evaluated for this workflow profile.",
        )
    else:
        user_message_en = (
            "Policy comparison completed; current-vs-policy No-Trade was not actionable."
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analysis_end": comparison.get("analysis_end"),
        "workflow_profile": workflow_profile,
        "combined_context_complete": combined_complete,
        "no_trade_actionable": no_trade_actionable,
        "policy_row_status": policy_status,
        "current_row_status": current_status,
        "current_artifact_root": current_artifact_root,
        "skip_reason": skip_reason,
        "user_message_en": user_message_en,
        "materialization": {
            "required": materialization_required,
            "completed": materialization_completed,
            "command_hint": MATERIALIZE_COMMAND
            if materialization_required and not materialization_completed
            else None,
        },
    }


def write_current_vs_policy_status_txt(status: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(status.get("user_message_en", "") + "\n")


def write_current_vs_policy_status_outputs(
    cfg: PortfolioConfig,
    comparison: dict[str, Any],
    *,
    project_root: Path | None = None,
    selection: dict[str, Any] | None = None,
    write_txt: bool = True,
) -> dict[str, Path]:
    project_root = project_root or Path.cwd()
    out_dir = project_root / str(getattr(cfg, "output_dir_final", "Main portfolio"))
    out_dir.mkdir(parents=True, exist_ok=True)

    status = build_current_vs_policy_status(
        comparison,
        cfg,
        project_root=project_root,
        selection=selection,
    )
    paths: dict[str, Path] = {}
    json_path = out_dir / "current_vs_policy_status.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2, ensure_ascii=False)
    paths["current_vs_policy_status_json"] = json_path

    if write_txt:
        txt_path = out_dir / "current_vs_policy_status.txt"
        write_current_vs_policy_status_txt(status, txt_path)
        paths["current_vs_policy_status_txt"] = txt_path

    return paths


__all__ = [
    "SCHEMA_VERSION",
    "MATERIALIZE_COMMAND",
    "build_current_vs_policy_status",
    "write_current_vs_policy_status_outputs",
    "write_current_vs_policy_status_txt",
]
