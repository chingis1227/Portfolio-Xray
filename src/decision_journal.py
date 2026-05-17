"""
Decision Journal — generated, non-executing decision record (projection only).

See docs/specs/decision_journal_spec.md.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config_schema import PortfolioConfig
from src.selection_engine import rationale_text_is_client_safe

SCHEMA_VERSION = "decision_journal_v1"
PRIMARY_WINDOW = "10y"
LATEST_JOURNAL_REL = Path("journal/latest/decision_journal.json")
HISTORY_DIR_REL = Path("journal/history")

ELIGIBLE_CURRENT_STATUSES = frozenset({"available", "degraded"})


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _rel_path(path: Path, project_root: Path) -> str:
    try:
        return str(path.relative_to(project_root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _finite(value: Any) -> float | None:
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return f


def _candidates_by_id(comparison: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {c["candidate_id"]: c for c in comparison.get("candidates", []) if c.get("candidate_id")}


def _score_by_id(doc: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not doc:
        return {}
    out: dict[str, dict[str, Any]] = {}
    for row in doc.get("candidates", []):
        cid = row.get("candidate_id")
        if cid:
            out[str(cid)] = row
    return out


def _worst_scenario(stress: dict[str, Any]) -> tuple[str | None, float | None]:
    scenarios = stress.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        failed = stress.get("failed_scenario")
        if failed:
            return str(failed), None
        return None, None
    best_id: str | None = None
    best_loss: float | None = None
    for s in scenarios:
        if not isinstance(s, dict):
            continue
        sid = s.get("scenario_id")
        pnl = _finite(s.get("portfolio_pnl_pct"))
        if pnl is None:
            continue
        if best_loss is None or pnl < best_loss:
            best_loss = pnl
            best_id = str(sid) if sid is not None else None
    return best_id, best_loss


def _macro_regime_label(factor_regime: dict[str, Any]) -> str | None:
    macro = factor_regime.get("macro_regime")
    if not isinstance(macro, dict):
        return None
    for key in ("label", "regime", "regime_label", "name"):
        val = macro.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return None


def _composite_rank_top3(composite: list[dict[str, Any]]) -> list[dict[str, Any]]:
    top: list[dict[str, Any]] = []
    for row in composite[:3]:
        top.append(
            {
                "candidate_id": row.get("candidate_id"),
                "selection_score": row.get("selection_score"),
                "rank": row.get("rank"),
            }
        )
    return top


def _mandate_notes(mandate: dict[str, Any]) -> str | None:
    notes: list[str] = []
    for key in ("warnings", "notes", "fail_reasons"):
        val = mandate.get(key)
        if isinstance(val, list):
            for item in val:
                if item is not None and str(item).strip():
                    notes.append(str(item).strip())
        elif val is not None and str(val).strip():
            notes.append(str(val).strip())
    if not notes and mandate.get("portfolio_valid") is False:
        return "Mandate checks did not pass for this profile."
    if not notes:
        return None
    return "; ".join(notes[:3])


def _weight_sources(comparison: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for cand in comparison.get("candidates", []):
        cid = cand.get("candidate_id")
        if not cid:
            continue
        method = cand.get("construction_method")
        role = cand.get("role")
        if method:
            out[str(cid)] = str(method)
        elif role:
            out[str(cid)] = str(role)
        else:
            out[str(cid)] = "unknown"
    return out


def _current_available(by_id: dict[str, dict[str, Any]]) -> bool:
    current = by_id.get("current")
    return bool(current and current.get("status") in ELIGIBLE_CURRENT_STATUSES)


def _score_deltas(
    *,
    favored_id: str | None,
    health_by_id: dict[str, dict[str, Any]],
    robust_by_id: dict[str, dict[str, Any]],
) -> tuple[float | None, float | None]:
    if not favored_id:
        return None, None
    cur_h = health_by_id.get("current", {}).get("total_score")
    fav_h = health_by_id.get(favored_id, {}).get("total_score")
    cur_r = robust_by_id.get("current", {}).get("total_score")
    fav_r = robust_by_id.get(favored_id, {}).get("total_score")
    h_delta = None
    r_delta = None
    if cur_h is not None and fav_h is not None:
        h_delta = round(float(fav_h) - float(cur_h), 3)
    if cur_r is not None and fav_r is not None:
        r_delta = round(float(fav_r) - float(cur_r), 3)
    return h_delta, r_delta


def _build_expected_improvement(
    *,
    decision_status: str,
    favored_id: str | None,
    by_id: dict[str, dict[str, Any]],
    selection: dict[str, Any],
    action: dict[str, Any] | None,
    health: dict[str, Any] | None,
    robustness: dict[str, Any] | None,
) -> dict[str, Any]:
    if not _current_available(by_id):
        return {
            "status": "not_applicable",
            "health_score_delta": None,
            "robustness_score_delta": None,
            "drawdown_improvement_pp": None,
            "turnover_half_sum_pct": None,
            "materiality_met": None,
            "summary": "Current portfolio not in comparison; improvement versus current not assessed.",
        }

    no_trade = selection.get("no_trade") or {}
    rc = (action or {}).get("risk_context") or {}
    health_delta = no_trade.get("health_score_delta")
    robust_delta = no_trade.get("robustness_score_delta")
    dd_improvement = no_trade.get("drawdown_improvement_pp")
    turnover = no_trade.get("turnover_half_sum_abs_delta_pct")

    if health_delta is None:
        health_delta = rc.get("health_score_delta")
    if robust_delta is None:
        robust_delta = rc.get("robustness_score_delta")
    if dd_improvement is None:
        dd_improvement = rc.get("drawdown_improvement_pp")
    if turnover is None:
        turnover = (action or {}).get("turnover_half_sum_pct")

    degraded = False
    if health_delta is None and robust_delta is None:
        h_delta, r_delta = _score_deltas(
            favored_id=favored_id,
            health_by_id=_score_by_id(health),
            robust_by_id=_score_by_id(robustness),
        )
        health_delta = h_delta
        robust_delta = r_delta
        if health_delta is None and robust_delta is None:
            degraded = True

    if decision_status == "selected_candidate":
        materiality_met: bool | None = True
        summary = (
            "Material rebalance criteria met relative to current for the favored profile."
        )
    elif decision_status == "no_material_rebalance":
        materiality_met = False
        summary = (
            "Score and turnover deltas versus current do not support a material rebalance."
        )
    else:
        materiality_met = None
        summary = "Improvement versus current is informational only for this decision status."

    status = "degraded" if degraded else "available"
    return {
        "status": status,
        "health_score_delta": health_delta,
        "robustness_score_delta": robust_delta,
        "drawdown_improvement_pp": dd_improvement,
        "turnover_half_sum_pct": turnover,
        "materiality_met": materiality_met,
        "summary": summary,
    }


def _build_accepted_risks(cand: dict[str, Any] | None) -> dict[str, Any]:
    if not cand:
        return {
            "worst_scenario_id": None,
            "worst_scenario_loss_pct": None,
            "stress_overall": None,
            "top_risk_contributor": None,
            "top_risk_contributor_pct": None,
            "mandate_portfolio_valid": None,
            "mandate_notes": None,
        }
    stress = cand.get("stress") or {}
    div = cand.get("diversification") or {}
    mandate = cand.get("mandate") or {}
    worst_id, worst_loss = _worst_scenario(stress)
    return {
        "worst_scenario_id": worst_id,
        "worst_scenario_loss_pct": worst_loss,
        "stress_overall": stress.get("overall"),
        "top_risk_contributor": div.get("top1_rc_asset"),
        "top_risk_contributor_pct": div.get("top1_rc_pct"),
        "mandate_portfolio_valid": mandate.get("portfolio_valid"),
        "mandate_notes": _mandate_notes(mandate),
    }


def _build_rationale(selection: dict[str, Any], decision_status: str) -> dict[str, Any]:
    sel_rat = selection.get("rationale") or {}
    summary = sel_rat.get("summary") or ""
    if not summary:
        favored = selection.get("favored_display_name") or selection.get("favored_candidate_id")
        summary = f"Decision status: {decision_status}."
        if favored:
            summary += f" Favored profile for review: {favored}."
    return {
        "summary": summary,
        "selection_bullets": list(sel_rat.get("selection_bullets") or []),
        "no_trade_bullets": list(sel_rat.get("no_trade_bullets") or []),
        "tradeoff_bullets": list(sel_rat.get("tradeoff_bullets") or []),
        "data_quality_notes": list(sel_rat.get("data_quality_notes") or []),
    }


def _build_implementation_plan(action: dict[str, Any] | None) -> dict[str, Any] | None:
    if not action:
        return None
    trades = action.get("trades") or []
    priority: list[str] = []
    for row in action.get("priority_trades") or []:
        if not isinstance(row, dict):
            continue
        ticker = row.get("ticker") or row.get("asset")
        if ticker:
            priority.append(str(ticker))
        if len(priority) >= 5:
            break
    return {
        "action_status": action.get("action_status"),
        "target_candidate_id": action.get("target_candidate_id"),
        "turnover_half_sum_pct": action.get("turnover_half_sum_pct"),
        "estimated_transaction_cost_pct": action.get("estimated_transaction_cost_pct"),
        "trade_count": len(trades) if isinstance(trades, list) else 0,
        "priority_tickers": priority,
        "no_trades_reason": action.get("no_trades_reason"),
    }


def _build_what_changed(monitoring_diff: dict[str, Any] | None) -> dict[str, Any] | None:
    if not monitoring_diff:
        return None
    return {
        "diff_status": monitoring_diff.get("diff_status"),
        "summary_plain_en": monitoring_diff.get("summary_plain_en"),
        "rebalance_trigger": monitoring_diff.get("rebalance_trigger"),
        "prior_analysis_end": monitoring_diff.get("prior_analysis_end"),
    }


def _assumptions_data_quality_notes(
    comparison: dict[str, Any],
    selection: dict[str, Any],
) -> list[str]:
    notes: list[str] = []
    for w in comparison.get("warnings") or []:
        if w and str(w) not in notes:
            notes.append(str(w))
    for w in selection.get("warnings") or []:
        if w and str(w) not in notes:
            notes.append(str(w))
    for w in selection.get("missing_inputs") or []:
        msg = f"Missing input: {w}"
        if msg not in notes:
            notes.append(msg)
    return notes


def build_decision_journal(
    comparison: dict[str, Any],
    selection: dict[str, Any],
    *,
    action: dict[str, Any] | None = None,
    monitoring_diff: dict[str, Any] | None = None,
    health: dict[str, Any] | None = None,
    robustness: dict[str, Any] | None = None,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Project decision journal from pipeline artifacts (no recomputation)."""
    project_root = project_root or Path.cwd()
    by_id = _candidates_by_id(comparison)
    decision_status = str(selection.get("decision_status") or "")
    favored_id = selection.get("favored_candidate_id")
    favored_display = selection.get("favored_display_name")
    favored_row = by_id.get(favored_id) if favored_id else None

    risk_row = favored_row
    if decision_status == "no_material_rebalance" and by_id.get("current"):
        risk_row = by_id.get("current") or favored_row

    setup = comparison.get("analysis_setup_summary") or {}
    analysis_mode = (
        setup.get("source_analysis_mode")
        or setup.get("analysis_mode")
        or "unknown"
    )

    macro_profile_id = favored_id or "policy"
    macro_row = by_id.get(macro_profile_id) or by_id.get("policy")
    macro_label = None
    if macro_row:
        macro_label = _macro_regime_label(macro_row.get("factor_regime") or {})

    warnings: list[str] = []
    if not action:
        warnings.append("journal_partial_missing_action")
    if not monitoring_diff:
        warnings.append("journal_no_monitoring_diff")

    out_dir_name = comparison.get("output_dir_final") or "Main portfolio"
    out_dir = project_root / str(out_dir_name)

    artifact_refs: dict[str, str | None] = {
        "candidate_comparison": _rel_path(out_dir / "candidate_comparison.json", project_root),
        "selection_decision": _rel_path(out_dir / "selection_decision.json", project_root),
        "action_plan": (
            _rel_path(out_dir / "action_plan.json", project_root) if action else None
        ),
        "monitoring_diff": (
            _rel_path(out_dir / "monitoring_diff.json", project_root)
            if monitoring_diff
            else None
        ),
        "portfolio_health_score": (
            _rel_path(out_dir / "portfolio_health_score.json", project_root)
            if health
            else None
        ),
        "robustness_scorecard": (
            _rel_path(out_dir / "robustness_scorecard.json", project_root)
            if robustness
            else None
        ),
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_only": True,
        "non_executing": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analysis_end": comparison.get("analysis_end"),
        "investor_currency": comparison.get("investor_currency"),
        "output_dir_final": out_dir_name,
        "decision_record": {
            "decision_status": decision_status,
            "favored_candidate_id": favored_id,
            "favored_display_name": favored_display,
            "formal_decision": selection.get("formal_decision"),
            "selection_weights_profile": selection.get("selection_weights_profile"),
            "no_trade_thresholds_profile": selection.get("no_trade_thresholds_profile"),
            "composite_rank_top3": _composite_rank_top3(
                list(selection.get("composite_ranking") or [])
            ),
        },
        "selected_portfolio": {
            "candidate_id": favored_id,
            "display_name": favored_display,
            "role": (favored_row or {}).get("role"),
            "status": (favored_row or {}).get("status"),
            "construction_method": (favored_row or {}).get("construction_method"),
            "mandate_portfolio_valid": ((favored_row or {}).get("mandate") or {}).get(
                "portfolio_valid"
            ),
        },
        "rejected_alternatives": list(selection.get("rejected_candidates") or []),
        "assumptions": {
            "analysis_mode": analysis_mode,
            "primary_window": PRIMARY_WINDOW,
            "investor_currency": comparison.get("investor_currency"),
            "weight_sources": _weight_sources(comparison),
            "data_quality_notes": _assumptions_data_quality_notes(comparison, selection),
        },
        "expected_improvement": _build_expected_improvement(
            decision_status=decision_status,
            favored_id=favored_id,
            by_id=by_id,
            selection=selection,
            action=action,
            health=health,
            robustness=robustness,
        ),
        "accepted_risks": _build_accepted_risks(risk_row),
        "macro_context": {
            "macro_regime_label": macro_label,
            "profile_id": macro_profile_id if macro_row else None,
        },
        "rationale": _build_rationale(selection, decision_status),
        "no_trade_status": {
            "is_no_trade": decision_status == "no_material_rebalance",
            "no_trade": selection.get("no_trade"),
            "no_trades_reason": (action or {}).get("no_trades_reason"),
        },
        "implementation_plan": _build_implementation_plan(action),
        "what_changed": _build_what_changed(monitoring_diff),
        "follow_up_review_date": None,
        "process_review": {"status": "not_implemented"},
        "artifact_refs": artifact_refs,
        "warnings": sorted(set(warnings)),
    }


def _history_path(out_dir: Path, analysis_end: str | None) -> Path:
    safe_end = (analysis_end or "unknown").replace("/", "-").replace("\\", "-")
    return out_dir / HISTORY_DIR_REL / f"decision_journal_{safe_end}.json"


def persist_decision_journal(out_dir: Path, journal: dict[str, Any]) -> dict[str, Path]:
    """Write root, latest, and history journal copies."""
    paths: dict[str, Path] = {}
    root = out_dir / "decision_journal.json"
    with open(root, "w", encoding="utf-8") as f:
        json.dump(journal, f, indent=2, ensure_ascii=False)
    paths["decision_journal_json"] = root

    latest_dir = out_dir / LATEST_JOURNAL_REL.parent
    latest_dir.mkdir(parents=True, exist_ok=True)
    latest = out_dir / LATEST_JOURNAL_REL
    with open(latest, "w", encoding="utf-8") as f:
        json.dump(journal, f, indent=2, ensure_ascii=False)
    paths["decision_journal_latest"] = latest

    hist = _history_path(out_dir, journal.get("analysis_end"))
    hist.parent.mkdir(parents=True, exist_ok=True)
    with open(hist, "w", encoding="utf-8") as f:
        json.dump(journal, f, indent=2, ensure_ascii=False)
    paths["decision_journal_history"] = hist
    return paths


def write_decision_journal_txt(journal: dict[str, Any], path: Path) -> None:
    """Compact English summary."""
    record = journal.get("decision_record") or {}
    selected = journal.get("selected_portfolio") or {}
    rationale = (journal.get("rationale") or {}).get("summary") or ""
    rejected = journal.get("rejected_alternatives") or []
    analysis_end = journal.get("analysis_end") or "—"
    status = record.get("decision_status") or "—"
    display = selected.get("display_name") or selected.get("candidate_id") or "—"

    lines = [
        f"Decision journal (generated, non-executing) — analysis end {analysis_end}",
        f"Status: {status}",
        f"Selected profile for review: {display}",
        "",
    ]
    if rationale:
        lines.append(f"Rationale: {rationale}")
        lines.append("")
    lines.append(f"Rejected alternatives: {len(rejected)} candidates (see decision_journal.json).")
    lines.append("Follow-up review: not scheduled in V1.")
    lines.append("")
    lines.append(
        "See artifact_refs in decision_journal.json for selection, action, and monitoring files."
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def write_decision_journal_outputs(
    cfg: PortfolioConfig,
    *,
    project_root: Path | None = None,
    comparison: dict[str, Any] | None = None,
    selection: dict[str, Any] | None = None,
    action: dict[str, Any] | None = None,
    monitoring_diff: dict[str, Any] | None = None,
    health: dict[str, Any] | None = None,
    robustness: dict[str, Any] | None = None,
    write_txt: bool = True,
) -> dict[str, Path]:
    """Write decision journal after monitoring when selection and comparison exist."""
    project_root = project_root or Path.cwd()
    out_dir = project_root / str(getattr(cfg, "output_dir_final", "Main portfolio"))

    if comparison is None:
        comparison = _load_json(out_dir / "candidate_comparison.json")
    if not comparison:
        return {}

    if selection is None:
        selection = _load_json(out_dir / "selection_decision.json")
    if not selection:
        return {}

    if action is None:
        action = _load_json(out_dir / "action_plan.json")
    if monitoring_diff is None:
        monitoring_diff = _load_json(out_dir / "monitoring_diff.json")
    if health is None:
        health = _load_json(out_dir / "portfolio_health_score.json")
    if robustness is None:
        robustness = _load_json(out_dir / "robustness_scorecard.json")

    journal = build_decision_journal(
        comparison,
        selection,
        action=action,
        monitoring_diff=monitoring_diff,
        health=health,
        robustness=robustness,
        project_root=project_root,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    paths = persist_decision_journal(out_dir, journal)

    if write_txt:
        txt_path = out_dir / "decision_journal.txt"
        write_decision_journal_txt(journal, txt_path)
        paths["decision_journal_txt"] = txt_path

    return paths


__all__ = [
    "SCHEMA_VERSION",
    "build_decision_journal",
    "persist_decision_journal",
    "rationale_text_is_client_safe",
    "write_decision_journal_outputs",
    "write_decision_journal_txt",
]
