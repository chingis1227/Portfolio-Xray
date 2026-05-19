"""
Compact report/PDF-facing projection of the V1 decision package artifacts.

See docs/specs/decision_package_reporting_spec.md.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config_schema import PortfolioConfig

SCHEMA_VERSION = "decision_package_report_v1"
REPORT_TXT_MARKER = "## Decision package (non-executing)"
PRIMARY_WINDOW = "10y"
TOP_CANDIDATE_ROWS = 3
TOP_TRADE_ROWS = 5
BASELINE_CANDIDATE_IDS = ("analysis_subject", "current")

_DECISION_STATUS_LINES: dict[str, str] = {
    "selected_candidate": "Favored profile selected for further review.",
    "no_material_rebalance": "No material rebalance suggested versus starting portfolio weights.",
    "inconclusive": "Selection inconclusive; review comparison and score drivers.",
    "data_review_required": "Decision requires data review before acting on results.",
    "mandate_risk_reduction": (
        "Mandate constraints require risk reduction before allocation change."
    ),
}


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _candidates_by_id(comparison: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not comparison:
        return {}
    return {
        c["candidate_id"]: c
        for c in comparison.get("candidates", [])
        if c.get("candidate_id")
    }


def _candidate_available(cand: dict[str, Any] | None) -> bool:
    return bool(cand and cand.get("status") in ("available", "degraded"))


def _preferred_baseline_id(
    comparison: dict[str, Any] | None,
    selection: dict[str, Any] | None,
) -> str | None:
    by_id = _candidates_by_id(comparison)
    explicit = (selection or {}).get("baseline_candidate_id")
    if explicit and _candidate_available(by_id.get(str(explicit))):
        return str(explicit)
    comp_baseline = (comparison or {}).get("comparison_baseline_candidate_id")
    if comp_baseline and _candidate_available(by_id.get(str(comp_baseline))):
        return str(comp_baseline)
    for candidate_id in BASELINE_CANDIDATE_IDS:
        if _candidate_available(by_id.get(candidate_id)):
            return candidate_id
    return None


def _format_candidate_highlight(cand: dict[str, Any], *, label: str | None = None) -> str:
    m = (cand.get("metrics") or {}).get(PRIMARY_WINDOW) or {}
    name = cand.get("display_name") or cand.get("candidate_id") or "Profile"
    prefix = f"{label}: " if label else ""
    return (
        f"  {prefix}{name}: "
        f"CAGR {_fmt_pct(m.get('cagr'))}, vol {_fmt_pct(m.get('vol_annual'))}, "
        f"max DD {_fmt_pct(m.get('max_drawdown'))}, "
        f"stress {_fmt_stress_label((cand.get('stress') or {}).get('overall'))}"
    )


def _selection_explanation_notes(selection: dict[str, Any]) -> list[str]:
    rationale = selection.get("rationale") or {}
    notes: list[str] = []
    for key in ("risk_reduction_notes", "selection_bullets", "data_quality_notes"):
        for raw in rationale.get(key) or []:
            text = str(raw).strip()
            if text and text not in notes:
                notes.append(text)
    return notes


def _selection_warning_line(raw: Any) -> str:
    text = str(raw)
    labels = {
        "mandate_risk_reduction": "Mandate risk-reduction status recorded.",
        "no_trade_skipped_missing_weights": "No-Trade materiality could not be evaluated because weights were missing.",
        "no_trade_not_actionable": "No-Trade materiality was not actionable for this run.",
        "partial_score_inputs": "Selection used partial score inputs.",
    }
    return labels.get(text, text)


def _score_row(
    doc: dict[str, Any] | None,
    candidate_id: str,
    *,
    rank_key: str,
) -> dict[str, Any] | None:
    if not doc:
        return None
    for row in doc.get("candidates", []):
        if row.get("candidate_id") == candidate_id:
            return row
    return None


def _fmt_pct(v: Any) -> str:
    if v is None:
        return "—"
    try:
        return f"{float(v):.1%}"
    except (TypeError, ValueError):
        return str(v)


def _fmt_num(v: Any, *, digits: int = 1) -> str:
    if v is None:
        return "—"
    try:
        return f"{float(v):.{digits}f}"
    except (TypeError, ValueError):
        return str(v)


def _fmt_stress_label(raw: Any) -> str:
    if raw is None:
        return "—"
    text = str(raw).strip()
    if text.startswith("DIAG_"):
        return "Diagnostic pass" if "PASS" in text.upper() else "Diagnostic review"
    if text.startswith("FAIL_"):
        return "Stress review required"
    return text


def _section_status(available: bool, *, reason: str | None = None) -> dict[str, str]:
    if available:
        return {"availability": "available"}
    return {"availability": "not_available", "reason": reason or "artifact_missing"}


def build_decision_package_summary_lines(
    *,
    comparison: dict[str, Any] | None,
    health: dict[str, Any] | None,
    robustness: dict[str, Any] | None,
    selection: dict[str, Any] | None,
    action: dict[str, Any] | None,
    monitoring_diff: dict[str, Any] | None,
    decision_journal: dict[str, Any] | None,
    workflow_status: dict[str, Any] | None = None,
    tradeoff: dict[str, Any] | None = None,
    model_risk: dict[str, Any] | None = None,
    assumption_sensitivity: dict[str, Any] | None = None,
    pareto_dominance: dict[str, Any] | None = None,
    regret_analysis: dict[str, Any] | None = None,
) -> list[str]:
    """Build plain-English summary lines (UTF-8)."""
    analysis_end = (comparison or selection or action or {}).get("analysis_end") or "—"
    currency = (comparison or selection or {}).get("investor_currency") or "—"
    lines: list[str] = [
        "Decision package summary (non-executing)",
        "=" * 72,
        f"Analysis end: {analysis_end}   Investor currency: {currency}",
        "",
        "This summary projects existing decision JSON artifacts. "
        "It is not trade advice and does not execute orders.",
        "",
    ]
    show_legacy_workflow_status = (
        workflow_status
        and workflow_status.get("user_message_en")
        and workflow_status.get("workflow_profile") != "portfolio_first_review"
    )
    if show_legacy_workflow_status:
        lines.append("Legacy current-vs-policy workflow")
        lines.append("-" * 40)
        lines.append(f"  {workflow_status['user_message_en']}")
        lines.append("")

    # Comparison
    lines.append("Comparison highlights")
    lines.append("-" * 40)
    if not comparison:
        lines.append("Not available (candidate_comparison.json missing).")
    else:
        by_id = _candidates_by_id(comparison)
        baseline_id = _preferred_baseline_id(comparison, selection)
        baseline = by_id.get(baseline_id or "")
        if baseline:
            lines.append(_format_candidate_highlight(baseline, label="Starting portfolio"))
        else:
            lines.append("  Starting portfolio: not available (analysis_subject diagnostics missing).")
        if health:
            scored = [
                r
                for r in health.get("candidates", [])
                if r.get("score_status") == "scored"
                and r.get("candidate_id") not in BASELINE_CANDIDATE_IDS
            ]
            scored.sort(key=lambda r: r.get("health_rank") or 999)
            if scored:
                lines.append("  Candidate alternatives by health rank:")
                for row in scored[:TOP_CANDIDATE_ROWS]:
                    cid = row.get("candidate_id", "")
                    disp = (by_id.get(cid) or {}).get("display_name") or cid
                    lines.append(
                        f"    {disp}: health {_fmt_num(row.get('total_score'))} "
                        f"(rank {row.get('health_rank')})"
                    )
    lines.append("")

    favored_id = (selection or {}).get("favored_candidate_id")

    # Robustness
    lines.append("Robustness scorecard")
    lines.append("-" * 40)
    if not robustness:
        lines.append("Not available (robustness_scorecard.json missing).")
    elif favored_id:
        row = _score_row(robustness, favored_id, rank_key="robustness_rank")
        if row and row.get("score_status") == "scored":
            lines.append(
                f"  Favored profile: total {_fmt_num(row.get('total_score'))}, "
                f"rank {row.get('robustness_rank')}"
            )
        else:
            lines.append("  Favored profile not scored in robustness scorecard.")
    else:
        lines.append("  No favored profile from selection.")
    lines.append("")

    # Health
    lines.append("Portfolio health score")
    lines.append("-" * 40)
    if not health:
        lines.append("Not available (portfolio_health_score.json missing).")
    elif favored_id:
        row = _score_row(health, favored_id, rank_key="health_rank")
        if row and row.get("score_status") == "scored":
            lines.append(
                f"  Favored profile: total {_fmt_num(row.get('total_score'))}, "
                f"rank {row.get('health_rank')}"
            )
        else:
            lines.append("  Favored profile not scored in health score.")
    else:
        lines.append("  No favored profile from selection.")
    lines.append("")

    # Selection
    lines.append("Selection")
    lines.append("-" * 40)
    if not selection:
        lines.append("Not available (selection_decision.json missing).")
    else:
        status = selection.get("decision_status", "")
        favored = selection.get("favored_display_name") or favored_id or "—"
        nt = selection.get("no_trade")
        workflow_profile = (workflow_status or {}).get("workflow_profile")
        if workflow_profile == "portfolio_first_review":
            no_trade_ok = bool(nt and nt.get("evaluated"))
        else:
            no_trade_ok = bool(
                workflow_status.get("no_trade_actionable")
                if workflow_status
                else (nt and nt.get("evaluated"))
            )
        if status == "no_material_rebalance" and not no_trade_ok:
            lines.append(
                "  Status: Selection recorded; No-Trade versus the starting portfolio was not evaluated."
            )
        else:
            lines.append(f"  Status: {_DECISION_STATUS_LINES.get(status, status)}")
        lines.append(f"  Favored profile: {favored}")
        rationale = selection.get("rationale") or {}
        if rationale.get("summary"):
            lines.append(f"  {rationale['summary']}")
        if status == "mandate_risk_reduction" and not favored_id:
            lines.append(
                "  No favored profile is shown because mandate risk-reduction gates blocked selection."
            )
            for note in _selection_explanation_notes(selection)[:3]:
                lines.append(f"  Mandate note: {note}")
        if nt and nt.get("evaluated") and no_trade_ok:
            lines.append(f"  Versus starting portfolio: {nt.get('summary', '')}")
        elif (
            workflow_status
            and workflow_profile != "portfolio_first_review"
            and not workflow_status.get("no_trade_actionable")
        ):
            skip = workflow_status.get("user_message_en")
            if skip:
                lines.append(f"  {skip}")
        for w in selection.get("warnings") or []:
            lines.append(f"  Warning: {_selection_warning_line(w)}")
    lines.append("")

    lines.append("Trade-offs")
    lines.append("-" * 40)
    if not tradeoff:
        lines.append("Not available (tradeoff_explanation.json missing).")
    else:
        summary = tradeoff.get("summary") or {}
        if summary.get("headline"):
            lines.append(f"  {summary['headline']}")
        if summary.get("tradeoff_paragraph"):
            lines.append(f"  {summary['tradeoff_paragraph']}")
        cost = tradeoff.get("cost_of_change") or {}
        if cost.get("turnover_half_sum_pct") is not None:
            lines.append(f"  Turnover (half-sum): {cost['turnover_half_sum_pct']}%")
    lines.append("")

    lines.append("Model risk")
    lines.append("-" * 40)
    if not model_risk:
        lines.append("Not available (model_risk_diagnostics.json missing).")
    else:
        lines.append(f"  Overall severity: {model_risk.get('overall_severity', '—')}")
        if model_risk.get("summary_plain_en"):
            lines.append(f"  {model_risk['summary_plain_en']}")
        for row in model_risk.get("warnings") or []:
            if row.get("severity") in ("high", "medium"):
                lines.append(f"  - {row.get('plain_english')}")
    lines.append("")

    lines.append("Assumption sensitivity")
    lines.append("-" * 40)
    if not assumption_sensitivity:
        lines.append("Not available (assumption_sensitivity.json missing).")
    else:
        stability = assumption_sensitivity.get("stability_status", "—")
        client_stability = (
            "assumption-sensitive"
            if stability == "fragile"
            else stability.replace("_", " ")
        )
        lines.append(f"  Stability: {client_stability}")
        rate = assumption_sensitivity.get("favored_stable_rate")
        if rate is not None:
            lines.append(f"  Favored stable rate (Tier A): {rate:.1%}")
        if assumption_sensitivity.get("policy_default_sensitive"):
            lines.append(
                "  Policy-default check: composite-only ranking would favor a different profile."
            )
        summary = assumption_sensitivity.get("summary_plain_en")
        if summary:
            lines.append(f"  {summary}")
    lines.append("")

    lines.append("Pareto / dominance")
    lines.append("-" * 40)
    if not pareto_dominance:
        lines.append("Not available (pareto_dominance.json missing).")
    else:
        lines.append(
            f"  Efficient set: {pareto_dominance.get('non_dominated_count', '—')} profile(s); "
            f"dominated: {pareto_dominance.get('dominated_count', '—')}."
        )
        if pareto_dominance.get("favored_is_dominated"):
            lines.append(
                "  Selection favorite is dominated on evaluated metrics (informational only)."
            )
        summary = pareto_dominance.get("summary_plain_en")
        if summary:
            lines.append(f"  {summary}")
    lines.append("")

    lines.append("Regret analysis")
    lines.append("-" * 40)
    if not regret_analysis:
        lines.append("Not available (regret_analysis.json missing).")
    else:
        status = regret_analysis.get("regret_status", "—")
        lines.append(f"  Status: {status}")
        favored_ref = next(
            (
                r
                for r in regret_analysis.get("reference_profiles") or []
                if r.get("reference_id") == "favored"
            ),
            None,
        )
        if favored_ref and favored_ref.get("worst_regret") is not None:
            lines.append(
                f"  Favored worst regret: {favored_ref.get('worst_regret')} "
                f"({favored_ref.get('worst_scenario_id', '—')})."
            )
        summary = regret_analysis.get("summary_plain_en")
        if summary:
            lines.append(f"  {summary}")
    lines.append("")

    # Action
    lines.append("Action plan")
    lines.append("-" * 40)
    if not action:
        lines.append("Not available (action_plan.json missing).")
    else:
        lines.append(f"  Status: {action.get('action_status', '—')}")
        if action.get("turnover_half_sum_pct") is not None:
            lines.append(f"  Turnover (half-sum): {action.get('turnover_half_sum_pct')}%")
        reason = action.get("no_trades_reason")
        if reason:
            lines.append(f"  {reason}")
        trades = action.get("trades") or []
        if trades:
            lines.append("  For review (not execution instructions):")
            for t in trades[:TOP_TRADE_ROWS]:
                lines.append(
                    f"    {t.get('ticker')} {t.get('direction')} "
                    f"Δw={t.get('delta_weight')} ({t.get('delta_pct')}%)"
                )
            if len(trades) > TOP_TRADE_ROWS:
                lines.append(f"    ... and {len(trades) - TOP_TRADE_ROWS} more in action_plan.json")
    lines.append("")

    # Monitoring
    lines.append("Monitoring — What Changed")
    lines.append("-" * 40)
    if not monitoring_diff:
        lines.append("Not available (monitoring_diff.json missing).")
    else:
        diff_status = monitoring_diff.get("diff_status", "—")
        lines.append(f"  Diff status: {diff_status}")
        if monitoring_diff.get("prior_analysis_end"):
            lines.append(
                f"  Prior analysis end: {monitoring_diff.get('prior_analysis_end')}"
            )
        summary = monitoring_diff.get("summary_plain_en")
        if summary:
            lines.append(f"  {summary}")
        elif diff_status == "no_prior_snapshot":
            lines.append("  No prior snapshot; first run stored for future comparison.")
    lines.append("")

    # Journal
    lines.append("Decision journal")
    lines.append("-" * 40)
    if not decision_journal:
        lines.append("Not available (decision_journal.json missing).")
    else:
        lines.append(
            "  Generated decision record: see decision_journal.json, "
            "journal/latest/, and journal/history/."
        )
    lines.append("")

    lines.append("Artifact index")
    lines.append("-" * 40)
    for name in (
        "candidate_comparison.json",
        "robustness_scorecard.json",
        "portfolio_health_score.json",
        "selection_decision.json",
        "tradeoff_explanation.json",
        "model_risk_diagnostics.json",
        "assumption_sensitivity.json",
        "pareto_dominance.json",
        "regret_analysis.json",
        "action_plan.json",
        "monitoring_diff.json",
        "decision_journal.json",
    ):
        lines.append(f"  {name}")
    lines.append("")
    return lines


def build_decision_package_report(
    *,
    comparison: dict[str, Any] | None,
    health: dict[str, Any] | None,
    robustness: dict[str, Any] | None,
    selection: dict[str, Any] | None,
    action: dict[str, Any] | None,
    monitoring_diff: dict[str, Any] | None,
    decision_journal: dict[str, Any] | None,
    workflow_status: dict[str, Any] | None = None,
    tradeoff: dict[str, Any] | None = None,
    model_risk: dict[str, Any] | None = None,
    assumption_sensitivity: dict[str, Any] | None = None,
    pareto_dominance: dict[str, Any] | None = None,
    regret_analysis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Machine-readable index plus embedded plain summary."""
    lines = build_decision_package_summary_lines(
        comparison=comparison,
        health=health,
        robustness=robustness,
        selection=selection,
        action=action,
        monitoring_diff=monitoring_diff,
        decision_journal=decision_journal,
        workflow_status=workflow_status,
        tradeoff=tradeoff,
        model_risk=model_risk,
        assumption_sensitivity=assumption_sensitivity,
        pareto_dominance=pareto_dominance,
        regret_analysis=regret_analysis,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "diagnostic_only": False,
        "non_executing": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analysis_end": (comparison or selection or {}).get("analysis_end"),
        "investor_currency": (comparison or selection or {}).get("investor_currency"),
        "output_dir_final": (comparison or selection or {}).get("output_dir_final"),
        "summary_plain_en": "\n".join(lines),
        "sections": {
            "comparison": _section_status(comparison is not None),
            "robustness": _section_status(robustness is not None),
            "health": _section_status(health is not None),
            "selection": _section_status(selection is not None),
            "tradeoffs": _section_status(tradeoff is not None),
            "model_risk": _section_status(model_risk is not None),
            "assumption_sensitivity": _section_status(assumption_sensitivity is not None),
            "pareto_dominance": _section_status(pareto_dominance is not None),
            "regret_analysis": _section_status(regret_analysis is not None),
            "action": _section_status(action is not None),
            "monitoring": _section_status(monitoring_diff is not None),
            "journal": _section_status(decision_journal is not None),
        },
        "input_artifacts": {
            "candidate_comparison": "candidate_comparison.json" if comparison else None,
            "robustness_scorecard": "robustness_scorecard.json" if robustness else None,
            "portfolio_health_score": "portfolio_health_score.json" if health else None,
            "selection_decision": "selection_decision.json" if selection else None,
            "tradeoff_explanation": "tradeoff_explanation.json" if tradeoff else None,
            "model_risk_diagnostics": "model_risk_diagnostics.json" if model_risk else None,
            "assumption_sensitivity": (
                "assumption_sensitivity.json" if assumption_sensitivity else None
            ),
            "pareto_dominance": "pareto_dominance.json" if pareto_dominance else None,
            "regret_analysis": "regret_analysis.json" if regret_analysis else None,
            "action_plan": "action_plan.json" if action else None,
            "monitoring_diff": "monitoring_diff.json" if monitoring_diff else None,
            "decision_journal": "decision_journal.json" if decision_journal else None,
        },
    }


def build_decision_package_report_md(
    summary_plain_en: str,
    *,
    report_title: str = "Decision Package Summary",
    analysis_end: str | None = None,
) -> str:
    """
    PDF-facing Markdown from the plain summary body.

    Delegates to ``pdf_reports.build_decision_package_pdf_md`` so Pandoc uses YAML front matter
    instead of a long H1 that can break XeLaTeX on analysis-end dates.
    """
    from src.pdf_reports import build_decision_package_pdf_md

    _ = report_title  # kept for backward-compatible call signature
    return build_decision_package_pdf_md(summary_plain_en, analysis_end=analysis_end)


def _append_summary_to_report_txt(report_path: Path, summary_plain_en: str) -> bool:
    if not report_path.is_file():
        return False
    existing = report_path.read_text(encoding="utf-8")
    if REPORT_TXT_MARKER in existing:
        return False
    block = (
        "\n\n"
        + REPORT_TXT_MARKER
        + "\n"
        + "-" * 72
        + "\n"
        + summary_plain_en
        + "\n"
    )
    with open(report_path, "a", encoding="utf-8") as f:
        f.write(block)
    return True


def write_decision_package_reporting_outputs(
    cfg: PortfolioConfig,
    *,
    project_root: Path | None = None,
    comparison: dict[str, Any] | None = None,
    health: dict[str, Any] | None = None,
    robustness: dict[str, Any] | None = None,
    selection: dict[str, Any] | None = None,
    action: dict[str, Any] | None = None,
    monitoring_diff: dict[str, Any] | None = None,
    decision_journal: dict[str, Any] | None = None,
    workflow_status: dict[str, Any] | None = None,
    tradeoff: dict[str, Any] | None = None,
    model_risk: dict[str, Any] | None = None,
    assumption_sensitivity: dict[str, Any] | None = None,
    pareto_dominance: dict[str, Any] | None = None,
    regret_analysis: dict[str, Any] | None = None,
    append_report_txt: bool = True,
) -> dict[str, Path]:
    project_root = project_root or Path.cwd()
    out_dir = project_root / str(getattr(cfg, "output_dir_final", "Main portfolio"))
    out_dir.mkdir(parents=True, exist_ok=True)

    if comparison is None:
        comparison = _load_json(out_dir / "candidate_comparison.json")
    if health is None:
        health = _load_json(out_dir / "portfolio_health_score.json")
    if robustness is None:
        robustness = _load_json(out_dir / "robustness_scorecard.json")
    if selection is None:
        selection = _load_json(out_dir / "selection_decision.json")
    if action is None:
        action = _load_json(out_dir / "action_plan.json")
    if monitoring_diff is None:
        monitoring_diff = _load_json(out_dir / "monitoring_diff.json")
    if decision_journal is None:
        decision_journal = _load_json(out_dir / "decision_journal.json")
    if workflow_status is None:
        workflow_status = _load_json(out_dir / "current_vs_policy_status.json")
    if tradeoff is None:
        tradeoff = _load_json(out_dir / "tradeoff_explanation.json")
    if model_risk is None:
        model_risk = _load_json(out_dir / "model_risk_diagnostics.json")
    if assumption_sensitivity is None:
        assumption_sensitivity = _load_json(out_dir / "assumption_sensitivity.json")
    if pareto_dominance is None:
        pareto_dominance = _load_json(out_dir / "pareto_dominance.json")
    if regret_analysis is None:
        regret_analysis = _load_json(out_dir / "regret_analysis.json")

    doc = build_decision_package_report(
        comparison=comparison,
        health=health,
        robustness=robustness,
        selection=selection,
        action=action,
        monitoring_diff=monitoring_diff,
        decision_journal=decision_journal,
        workflow_status=workflow_status,
        tradeoff=tradeoff,
        model_risk=model_risk,
        assumption_sensitivity=assumption_sensitivity,
        pareto_dominance=pareto_dominance,
        regret_analysis=regret_analysis,
    )
    paths: dict[str, Path] = {}
    json_path = out_dir / "decision_package_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
    paths["decision_package_summary_json"] = json_path

    txt_path = out_dir / "decision_package_summary.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(doc["summary_plain_en"])
    paths["decision_package_summary_txt"] = txt_path

    if append_report_txt:
        report_path = out_dir / "report.txt"
        if _append_summary_to_report_txt(report_path, doc["summary_plain_en"]):
            paths["report_txt_appended"] = report_path

    return paths


__all__ = [
    "SCHEMA_VERSION",
    "REPORT_TXT_MARKER",
    "build_decision_package_report",
    "build_decision_package_report_md",
    "build_decision_package_summary_lines",
    "write_decision_package_reporting_outputs",
]
