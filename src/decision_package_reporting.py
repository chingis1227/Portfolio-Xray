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

_DECISION_STATUS_LINES: dict[str, str] = {
    "selected_candidate": "Favored profile selected for further review.",
    "no_material_rebalance": "No material rebalance suggested versus current weights.",
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

    # Comparison
    lines.append("Comparison highlights")
    lines.append("-" * 40)
    if not comparison:
        lines.append("Not available (candidate_comparison.json missing).")
    else:
        by_id = _candidates_by_id(comparison)
        for key in ("policy", "current"):
            cand = by_id.get(key)
            if not cand:
                continue
            status = cand.get("status", "")
            if status == "unavailable":
                lines.append(
                    f"  {cand.get('display_name', key)}: unavailable "
                    f"({cand.get('unavailable_reason', 'no artifacts')})"
                )
                continue
            m = (cand.get("metrics") or {}).get(PRIMARY_WINDOW) or {}
            lines.append(
                f"  {cand.get('display_name', key)}: "
                f"CAGR {_fmt_pct(m.get('cagr'))}, vol {_fmt_pct(m.get('vol_annual'))}, "
                f"max DD {_fmt_pct(m.get('max_drawdown'))}, "
                f"stress {_fmt_stress_label((cand.get('stress') or {}).get('overall'))}"
            )
        if health:
            scored = [
                r
                for r in health.get("candidates", [])
                if r.get("score_status") == "scored" and r.get("candidate_id") != "current"
            ]
            scored.sort(key=lambda r: r.get("health_rank") or 999)
            if scored:
                lines.append("  Top candidates by health rank:")
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
        lines.append(f"  Status: {_DECISION_STATUS_LINES.get(status, status)}")
        lines.append(f"  Favored profile: {favored}")
        rationale = selection.get("rationale") or {}
        if rationale.get("summary"):
            lines.append(f"  {rationale['summary']}")
        nt = selection.get("no_trade")
        if nt and nt.get("evaluated"):
            lines.append(f"  Versus current: {nt.get('summary', '')}")
        for w in selection.get("warnings") or []:
            lines.append(f"  Warning: {w}")
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
            "action": _section_status(action is not None),
            "monitoring": _section_status(monitoring_diff is not None),
            "journal": _section_status(decision_journal is not None),
        },
        "input_artifacts": {
            "candidate_comparison": "candidate_comparison.json" if comparison else None,
            "robustness_scorecard": "robustness_scorecard.json" if robustness else None,
            "portfolio_health_score": "portfolio_health_score.json" if health else None,
            "selection_decision": "selection_decision.json" if selection else None,
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
    """PDF-facing Markdown from the plain summary body."""
    title = report_title
    if analysis_end:
        title = f"{report_title} — analysis end {analysis_end}"
    body = summary_plain_en.replace("\n", "\n\n")
    return f"# {title}\n\n{body}\n"


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

    doc = build_decision_package_report(
        comparison=comparison,
        health=health,
        robustness=robustness,
        selection=selection,
        action=action,
        monitoring_diff=monitoring_diff,
        decision_journal=decision_journal,
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
