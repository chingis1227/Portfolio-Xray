"""Product-facing Light Monitoring / What Changed projection.

This module projects the existing ``monitoring_diff.json`` contract into a
small diagnosis-first product summary. It does not change monitoring history
storage, monitoring_diff schema, selection logic, formulas, or thresholds.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WHAT_CHANGED_SUMMARY_VERSION = "what_changed_summary_v1"
WHAT_CHANGED_SUMMARY_FILENAME = "what_changed_summary.json"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _decision_verdict_id(decision_verdict: dict[str, Any] | None) -> str | None:
    if not isinstance(decision_verdict, dict):
        return None
    value = decision_verdict.get("verdict_id")
    return str(value) if value is not None else None


def _problem_ids(problem_classification: dict[str, Any] | None) -> list[str]:
    if not isinstance(problem_classification, dict):
        return []
    out: list[str] = []
    for row in problem_classification.get("problems") or []:
        if isinstance(row, dict) and row.get("problem_id"):
            out.append(str(row["problem_id"]))
    return out[:5]


def _append_line(
    lines: list[dict[str, Any]],
    *,
    category: str,
    message: str,
    evidence_refs: list[dict[str, str]],
    retest_trigger: bool = False,
) -> None:
    lines.append(
        {
            "category": category,
            "message": message,
            "evidence_refs": evidence_refs,
            "retest_trigger": retest_trigger,
        }
    )


def _profile_change_lines(
    monitoring_diff: dict[str, Any],
    primary_profile_id: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    lines: list[dict[str, Any]] = []
    triggers: list[str] = []
    profile_changes = monitoring_diff.get("profile_changes")
    primary = {}
    if isinstance(profile_changes, dict):
        primary = profile_changes.get(primary_profile_id) or {}
    if not isinstance(primary, dict) or not primary.get("available"):
        if monitoring_diff.get("diff_status") == "diff_degraded":
            _append_line(
                lines,
                category="evidence_gap",
                message="Primary profile change evidence is degraded; review monitoring_diff.json before interpreting changes.",
                evidence_refs=[
                    {"artifact": "monitoring_diff.json", "field_path": "diff_status"},
                    {"artifact": "monitoring_diff.json", "field_path": f"profile_changes.{primary_profile_id}"},
                ],
                retest_trigger=True,
            )
            triggers.append("monitoring_evidence_degraded")
        return lines, triggers

    if primary.get("top_risk_contributor_changed"):
        _append_line(
            lines,
            category="risk_contributor",
            message="The top risk contributor changed for the monitored portfolio profile.",
            evidence_refs=[
                {
                    "artifact": "monitoring_diff.json",
                    "field_path": f"profile_changes.{primary_profile_id}.top_risk_contributor_changed",
                }
            ],
            retest_trigger=True,
        )
        triggers.append("top_risk_contributor_changed")
    if primary.get("worst_scenario_changed"):
        _append_line(
            lines,
            category="stress_behavior",
            message="The worst stress scenario changed for the monitored portfolio profile.",
            evidence_refs=[
                {
                    "artifact": "monitoring_diff.json",
                    "field_path": f"profile_changes.{primary_profile_id}.worst_scenario_changed",
                }
            ],
            retest_trigger=True,
        )
        triggers.append("worst_scenario_changed")
    if primary.get("macro_regime_changed"):
        _append_line(
            lines,
            category="market_context",
            message="The macro regime label changed versus the prior snapshot.",
            evidence_refs=[
                {
                    "artifact": "monitoring_diff.json",
                    "field_path": f"profile_changes.{primary_profile_id}.macro_regime_changed",
                }
            ],
            retest_trigger=True,
        )
        triggers.append("macro_regime_changed")
    if primary.get("mandate_status_changed"):
        _append_line(
            lines,
            category="mandate",
            message="The mandate-valid status changed versus the prior snapshot.",
            evidence_refs=[
                {
                    "artifact": "monitoring_diff.json",
                    "field_path": f"profile_changes.{primary_profile_id}.mandate_status_changed",
                }
            ],
            retest_trigger=True,
        )
        triggers.append("mandate_status_changed")
    return lines, triggers


def _decision_lines(
    monitoring_diff: dict[str, Any],
    decision_verdict: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], list[str]]:
    lines: list[dict[str, Any]] = []
    triggers: list[str] = []
    decision_changes = monitoring_diff.get("decision_changes")
    action_changes = monitoring_diff.get("action_changes")
    if isinstance(decision_changes, dict) and decision_changes.get("decision_status_changed"):
        _append_line(
            lines,
            category="decision",
            message="The formal selection decision status changed since the prior snapshot.",
            evidence_refs=[
                {"artifact": "monitoring_diff.json", "field_path": "decision_changes.decision_status_changed"},
                {"artifact": "selection_decision.json", "field_path": "decision_status"},
            ],
            retest_trigger=True,
        )
        triggers.append("decision_status_changed")
    if isinstance(action_changes, dict) and action_changes.get("action_status_changed"):
        _append_line(
            lines,
            category="action",
            message="The non-executing action status changed since the prior snapshot.",
            evidence_refs=[
                {"artifact": "monitoring_diff.json", "field_path": "action_changes.action_status_changed"},
                {"artifact": "action_plan.json", "field_path": "action_status"},
            ],
            retest_trigger=True,
        )
        triggers.append("action_status_changed")
    if monitoring_diff.get("rebalance_trigger"):
        _append_line(
            lines,
            category="review_trigger",
            message="Current monitoring indicates the decision package should be reviewed; this does not execute trades.",
            evidence_refs=[
                {"artifact": "monitoring_diff.json", "field_path": "rebalance_trigger"},
                {"artifact": "decision_verdict.json", "field_path": "verdict_id"},
            ],
            retest_trigger=True,
        )
        triggers.append("rebalance_trigger")
    verdict_id = _decision_verdict_id(decision_verdict)
    if verdict_id:
        _append_line(
            lines,
            category="decision_verdict",
            message=f"Current product-facing verdict is '{verdict_id}'.",
            evidence_refs=[{"artifact": "decision_verdict.json", "field_path": "verdict_id"}],
        )
    return lines, triggers


def build_what_changed_summary(
    *,
    monitoring_diff: dict[str, Any] | None,
    decision_verdict: dict[str, Any] | None = None,
    problem_classification: dict[str, Any] | None = None,
    current_vs_candidate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a product-level summary from existing monitoring evidence."""

    warnings: list[str] = []
    if not isinstance(monitoring_diff, dict):
        warnings.append("missing_required_source:monitoring_diff.json")
        return {
            "schema_version": WHAT_CHANGED_SUMMARY_VERSION,
            "diagnostic_only": True,
            "generated_at": _utc_now_iso(),
            "summary_status": "missing_monitoring",
            "headline": "Monitoring evidence is not available.",
            "primary_profile_id": None,
            "current_analysis_end": None,
            "prior_analysis_end": None,
            "problem_ids": _problem_ids(problem_classification),
            "decision_verdict_id": _decision_verdict_id(decision_verdict),
            "current_vs_candidate_mode": (
                current_vs_candidate.get("view_mode") if isinstance(current_vs_candidate, dict) else None
            ),
            "what_changed_lines": [],
            "retest_triggers": [],
            "source_artifacts": {
                "monitoring_diff": None,
                "decision_verdict": "decision_verdict.json" if isinstance(decision_verdict, dict) else None,
                "problem_classification": "problem_classification.json"
                if isinstance(problem_classification, dict)
                else None,
                "current_vs_candidate": "current_vs_candidate.json"
                if isinstance(current_vs_candidate, dict)
                else None,
            },
            "guardrails": {
                "does_not_change_monitoring_schema": True,
                "does_not_write_monitoring_history": True,
                "does_not_calculate_metrics": True,
                "does_not_execute_trades": True,
            },
            "warnings": warnings,
        }

    diff_status = str(monitoring_diff.get("diff_status") or "unknown")
    primary_profile_id = str(monitoring_diff.get("primary_profile_id") or "unknown")
    lines: list[dict[str, Any]] = []
    triggers: list[str] = []

    if diff_status == "no_prior_snapshot":
        _append_line(
            lines,
            category="baseline",
            message="This is the first comparable monitoring snapshot, or the prior snapshot has the same analysis date.",
            evidence_refs=[
                {"artifact": "monitoring_diff.json", "field_path": "diff_status"},
                {"artifact": "monitoring_diff.json", "field_path": "summary_plain_en"},
            ],
        )
    else:
        profile_lines, profile_triggers = _profile_change_lines(monitoring_diff, primary_profile_id)
        lines.extend(profile_lines)
        triggers.extend(profile_triggers)

    decision_lines, decision_triggers = _decision_lines(monitoring_diff, decision_verdict)
    lines.extend(decision_lines)
    triggers.extend(decision_triggers)

    source_warnings = monitoring_diff.get("warnings")
    if isinstance(source_warnings, list):
        for warning in source_warnings:
            warnings.append(f"monitoring_diff:{warning}")
        if source_warnings:
            _append_line(
                lines,
                category="warning",
                message="Monitoring emitted warnings; review source monitoring evidence before acting.",
                evidence_refs=[{"artifact": "monitoring_diff.json", "field_path": "warnings"}],
                retest_trigger=True,
            )
            triggers.append("monitoring_warning")

    if not lines:
        _append_line(
            lines,
            category="no_material_change",
            message="No product-level monitoring change line was triggered from current evidence.",
            evidence_refs=[{"artifact": "monitoring_diff.json", "field_path": "summary_plain_en"}],
        )

    unique_triggers = list(dict.fromkeys(triggers))
    if diff_status == "no_prior_snapshot":
        headline = "Monitoring baseline stored; future runs can show What Changed."
    elif unique_triggers:
        headline = "Monitoring changes detected; review affected evidence before the next decision."
    else:
        headline = "No product-level monitoring trigger detected."

    return {
        "schema_version": WHAT_CHANGED_SUMMARY_VERSION,
        "diagnostic_only": True,
        "generated_at": _utc_now_iso(),
        "summary_status": "available",
        "headline": headline,
        "primary_profile_id": primary_profile_id,
        "current_analysis_end": monitoring_diff.get("current_analysis_end"),
        "prior_analysis_end": monitoring_diff.get("prior_analysis_end"),
        "problem_ids": _problem_ids(problem_classification),
        "decision_verdict_id": _decision_verdict_id(decision_verdict),
        "current_vs_candidate_mode": (
            current_vs_candidate.get("view_mode") if isinstance(current_vs_candidate, dict) else None
        ),
        "what_changed_lines": lines,
        "retest_triggers": unique_triggers,
        "source_artifacts": {
            "monitoring_diff": "monitoring_diff.json",
            "decision_verdict": "decision_verdict.json" if isinstance(decision_verdict, dict) else None,
            "problem_classification": "problem_classification.json"
            if isinstance(problem_classification, dict)
            else None,
            "current_vs_candidate": "current_vs_candidate.json"
            if isinstance(current_vs_candidate, dict)
            else None,
        },
        "guardrails": {
            "does_not_change_monitoring_schema": True,
            "does_not_write_monitoring_history": True,
            "does_not_calculate_metrics": True,
            "does_not_execute_trades": True,
        },
        "warnings": warnings,
    }


def write_what_changed_summary_outputs(
    *,
    output_dir: str | Path,
    monitoring_diff: dict[str, Any] | None,
    decision_verdict: dict[str, Any] | None = None,
    problem_classification: dict[str, Any] | None = None,
    current_vs_candidate: dict[str, Any] | None = None,
) -> dict[str, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    doc = build_what_changed_summary(
        monitoring_diff=monitoring_diff,
        decision_verdict=decision_verdict,
        problem_classification=problem_classification,
        current_vs_candidate=current_vs_candidate,
    )
    path = out / WHAT_CHANGED_SUMMARY_FILENAME
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False, default=str)
    return {"what_changed_summary_json": path}
