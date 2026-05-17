"""
Monitoring snapshots and What Changed diff (non-binding, generated-only).

See docs/specs/monitoring_spec.md.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config_schema import PortfolioConfig

SNAPSHOT_SCHEMA_VERSION = "analysis_snapshot_v1"
DIFF_SCHEMA_VERSION = "monitoring_diff_v1"
MONITORED_PROFILE_IDS = ("current", "policy")
LATEST_SNAPSHOT_REL = Path("monitoring/latest/analysis_snapshot.json")
HISTORY_DIR_REL = Path("monitoring/history")


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


def _score_by_id(doc: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not doc:
        return {}
    out: dict[str, dict[str, Any]] = {}
    for row in doc.get("candidates", []):
        cid = row.get("candidate_id")
        if cid:
            out[str(cid)] = row
    return out


def _candidates_by_id(comparison: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {c["candidate_id"]: c for c in comparison.get("candidates", []) if c.get("candidate_id")}


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


def _profile_from_sources(
    cand: dict[str, Any],
    *,
    health_row: dict[str, Any] | None,
    robust_row: dict[str, Any] | None,
) -> dict[str, Any]:
    metrics = (cand.get("metrics") or {}).get("10y") or {}
    stress = cand.get("stress") or {}
    div = cand.get("diversification") or {}
    mandate = cand.get("mandate") or {}
    worst_id, worst_loss = _worst_scenario(stress)

    health_score = None
    if health_row:
        ts = health_row.get("total_score")
        if ts is not None:
            health_score = int(ts)

    robust_score = None
    if robust_row:
        ts = robust_row.get("total_score")
        if ts is not None:
            robust_score = int(ts)

    return {
        "candidate_id": cand.get("candidate_id"),
        "display_name": cand.get("display_name"),
        "status": cand.get("status"),
        "health_score": health_score,
        "robustness_score": robust_score,
        "metrics_10y": {
            k: metrics[k]
            for k in ("cagr", "vol_annual", "max_drawdown", "sharpe", "beta_portfolio")
            if k in metrics and metrics[k] is not None
        },
        "stress_overall": stress.get("overall"),
        "worst_scenario_id": worst_id,
        "worst_scenario_loss_pct": worst_loss,
        "top_risk_contributor": div.get("top1_rc_asset"),
        "top_risk_contributor_pct": div.get("top1_rc_pct"),
        "macro_regime_label": _macro_regime_label(cand.get("factor_regime") or {}),
        "mandate_portfolio_valid": mandate.get("portfolio_valid"),
    }


def _decision_projection(selection: dict[str, Any] | None) -> dict[str, Any]:
    if not selection:
        return {}
    return {
        "decision_status": selection.get("decision_status"),
        "favored_candidate_id": selection.get("favored_candidate_id"),
        "favored_display_name": selection.get("favored_display_name"),
        "no_trade": selection.get("no_trade"),
    }


def _action_projection(action: dict[str, Any] | None) -> dict[str, Any]:
    if not action:
        return {}
    return {
        "action_status": action.get("action_status"),
        "selection_decision_status": action.get("selection_decision_status"),
        "turnover_half_sum_pct": action.get("turnover_half_sum_pct"),
        "target_candidate_id": action.get("target_candidate_id"),
    }


def build_analysis_snapshot(
    comparison: dict[str, Any],
    *,
    health: dict[str, Any] | None = None,
    robustness: dict[str, Any] | None = None,
    selection: dict[str, Any] | None = None,
    action: dict[str, Any] | None = None,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Build analysis_snapshot_v1 from decision-pipeline artifacts."""
    project_root = project_root or Path.cwd()
    by_id = _candidates_by_id(comparison)
    health_by = _score_by_id(health)
    robust_by = _score_by_id(robustness)

    profiles: dict[str, Any] = {}
    warnings: list[str] = []
    for pid in MONITORED_PROFILE_IDS:
        cand = by_id.get(pid)
        if not cand:
            continue
        if cand.get("status") not in ("available", "degraded"):
            warnings.append(f"profile_{pid}_not_available")
            continue
        profiles[pid] = _profile_from_sources(
            cand,
            health_row=health_by.get(pid),
            robust_row=robust_by.get(pid),
        )

    out_dir = comparison.get("output_dir_final") or "Main portfolio"
    out_path = project_root / str(out_dir)

    artifact_refs = {
        "candidate_comparison": _rel_path(out_path / "candidate_comparison.json", project_root),
    }
    if health:
        artifact_refs["portfolio_health_score"] = _rel_path(
            out_path / "portfolio_health_score.json", project_root
        )
    if robustness:
        artifact_refs["robustness_scorecard"] = _rel_path(
            out_path / "robustness_scorecard.json", project_root
        )
    if selection:
        artifact_refs["selection_decision"] = _rel_path(
            out_path / "selection_decision.json", project_root
        )
    if action:
        artifact_refs["action_plan"] = _rel_path(out_path / "action_plan.json", project_root)

    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analysis_end": comparison.get("analysis_end"),
        "investor_currency": comparison.get("investor_currency"),
        "output_dir_final": str(out_dir).replace("\\", "/"),
        "profiles": profiles,
        "decision": _decision_projection(selection),
        "action": _action_projection(action),
        "artifact_refs": artifact_refs,
        "warnings": warnings,
    }


def _delta(current: float | None, prior: float | None) -> float | None:
    if current is None or prior is None:
        return None
    return round(current - prior, 4)


def _profile_diff(
    current_prof: dict[str, Any] | None,
    prior_prof: dict[str, Any] | None,
) -> dict[str, Any]:
    if not current_prof or not prior_prof:
        return {"available": False}

    cur_m = current_prof.get("metrics_10y") or {}
    pri_m = prior_prof.get("metrics_10y") or {}

    cur_worst_id = current_prof.get("worst_scenario_id")
    pri_worst_id = prior_prof.get("worst_scenario_id")
    cur_macro = current_prof.get("macro_regime_label")
    pri_macro = prior_prof.get("macro_regime_label")
    cur_mandate = current_prof.get("mandate_portfolio_valid")
    pri_mandate = prior_prof.get("mandate_portfolio_valid")
    cur_rc = current_prof.get("top_risk_contributor")
    pri_rc = prior_prof.get("top_risk_contributor")

    return {
        "available": True,
        "health_score_delta": _delta(
            _finite(current_prof.get("health_score")),
            _finite(prior_prof.get("health_score")),
        ),
        "robustness_score_delta": _delta(
            _finite(current_prof.get("robustness_score")),
            _finite(prior_prof.get("robustness_score")),
        ),
        "vol_annual_delta": _delta(_finite(cur_m.get("vol_annual")), _finite(pri_m.get("vol_annual"))),
        "beta_delta": _delta(
            _finite(cur_m.get("beta_portfolio")),
            _finite(pri_m.get("beta_portfolio")),
        ),
        "max_drawdown_delta": _delta(
            _finite(cur_m.get("max_drawdown")),
            _finite(pri_m.get("max_drawdown")),
        ),
        "worst_scenario_changed": (cur_worst_id != pri_worst_id)
        if cur_worst_id is not None or pri_worst_id is not None
        else None,
        "worst_scenario_loss_delta": _delta(
            _finite(current_prof.get("worst_scenario_loss_pct")),
            _finite(prior_prof.get("worst_scenario_loss_pct")),
        ),
        "top_risk_contributor_changed": (cur_rc != pri_rc)
        if cur_rc is not None or pri_rc is not None
        else None,
        "macro_regime_changed": (cur_macro != pri_macro)
        if cur_macro is not None or pri_macro is not None
        else None,
        "mandate_status_changed": (cur_mandate != pri_mandate)
        if cur_mandate is not None or pri_mandate is not None
        else None,
    }


def _rebalance_trigger(selection: dict[str, Any] | None, action: dict[str, Any] | None) -> bool:
    if selection and selection.get("decision_status") == "selected_candidate":
        return True
    if action and action.get("action_status") == "trades_for_review":
        return True
    return False


def _summary_plain_en(
    *,
    diff_status: str,
    primary_id: str,
    profile_change: dict[str, Any],
    decision_changes: dict[str, Any],
    current_end: str | None,
    prior_end: str | None,
) -> str:
    if diff_status == "no_prior_snapshot":
        end = current_end or "this run"
        return (
            f"This is the first stored monitoring snapshot for analysis ending {end}. "
            "No prior snapshot is available for comparison. Future runs will show What Changed "
            "when a previous snapshot exists under monitoring/latest/."
        )

    parts: list[str] = []
    if prior_end and current_end:
        parts.append(
            f"Compared to the prior analysis ending {prior_end}, the run ending {current_end} "
            f"shows the following for profile '{primary_id}'."
        )

    if profile_change.get("available"):
        hd = profile_change.get("health_score_delta")
        if hd is not None:
            direction = "higher" if hd > 0 else "lower" if hd < 0 else "unchanged"
            parts.append(f"Health score is {direction} by {abs(hd):.0f} points.")
        if profile_change.get("worst_scenario_changed"):
            parts.append("The worst stress scenario identifier changed.")
        if profile_change.get("macro_regime_changed"):
            parts.append("The macro regime label changed.")
        if profile_change.get("mandate_status_changed"):
            parts.append("Mandate portfolio-valid status changed versus the prior snapshot.")
    else:
        parts.append("Profile-level risk deltas are partial because prior or current profile data was missing.")

    if decision_changes.get("decision_status_changed"):
        parts.append("The formal selection decision status changed since the prior run.")

    if not parts:
        return "Monitoring diff completed with no material field changes detected."
    return " ".join(parts)


def build_monitoring_diff(
    current_snapshot: dict[str, Any],
    prior_snapshot: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build monitoring_diff_v1 comparing current snapshot to prior."""
    warnings: list[str] = []
    current_end = current_snapshot.get("analysis_end")
    prior_end = prior_snapshot.get("analysis_end") if prior_snapshot else None

    if not prior_snapshot:
        diff_status = "no_prior_snapshot"
    elif prior_end == current_end:
        diff_status = "no_prior_snapshot"
        warnings.append("prior_same_analysis_end_ignored")
    else:
        diff_status = "diff_available"

    profiles_current = current_snapshot.get("profiles") or {}
    profiles_prior = (prior_snapshot or {}).get("profiles") or {}

    primary_id = "current"
    if primary_id not in profiles_current and "policy" in profiles_current:
        primary_id = "policy"

    profile_changes: dict[str, Any] = {}
    for pid in MONITORED_PROFILE_IDS:
        if pid in profiles_current or pid in profiles_prior:
            profile_changes[pid] = _profile_diff(
                profiles_current.get(pid),
                profiles_prior.get(pid),
            )

    primary_change = profile_changes.get(primary_id) or {"available": False}
    if diff_status == "diff_available" and not primary_change.get("available"):
        diff_status = "diff_degraded"
        warnings.append("primary_profile_diff_degraded")

    cur_dec = current_snapshot.get("decision") or {}
    pri_dec = (prior_snapshot or {}).get("decision") or {}
    decision_changes = {
        "decision_status_changed": bool(
            cur_dec.get("decision_status") != pri_dec.get("decision_status")
            and (cur_dec.get("decision_status") or pri_dec.get("decision_status"))
        ),
        "prior_decision_status": pri_dec.get("decision_status"),
        "current_decision_status": cur_dec.get("decision_status"),
        "prior_favored_candidate_id": pri_dec.get("favored_candidate_id"),
        "current_favored_candidate_id": cur_dec.get("favored_candidate_id"),
    }

    cur_act = current_snapshot.get("action") or {}
    pri_act = (prior_snapshot or {}).get("action") or {}
    action_changes = {
        "action_status_changed": bool(
            cur_act.get("action_status") != pri_act.get("action_status")
            and (cur_act.get("action_status") or pri_act.get("action_status"))
        ),
        "prior_action_status": pri_act.get("action_status"),
        "current_action_status": cur_act.get("action_status"),
    }

    return {
        "schema_version": DIFF_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "diff_status": diff_status,
        "primary_profile_id": primary_id,
        "prior_analysis_end": prior_end,
        "current_analysis_end": current_end,
        "profile_changes": profile_changes,
        "decision_changes": decision_changes,
        "action_changes": action_changes,
        "rebalance_trigger": _rebalance_trigger(
            current_snapshot.get("decision"),
            current_snapshot.get("action"),
        ),
        "summary_plain_en": _summary_plain_en(
            diff_status=diff_status,
            primary_id=primary_id,
            profile_change=primary_change,
            decision_changes=decision_changes,
            current_end=current_end,
            prior_end=prior_end,
        ),
        "warnings": warnings,
        "input_artifacts": {
            "current_snapshot": "monitoring/latest/analysis_snapshot.json",
            "prior_snapshot": "monitoring/latest/analysis_snapshot.json"
            if prior_snapshot
            else None,
        },
    }


def _history_path(out_dir: Path, analysis_end: str | None) -> Path:
    safe_end = (analysis_end or "unknown").replace("/", "-").replace("\\", "-")
    return out_dir / HISTORY_DIR_REL / f"analysis_snapshot_{safe_end}.json"


def persist_analysis_snapshot(out_dir: Path, snapshot: dict[str, Any]) -> dict[str, Path]:
    """Write latest and history copies; return written paths."""
    paths: dict[str, Path] = {}
    latest_dir = out_dir / "monitoring" / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    latest = latest_dir / "analysis_snapshot.json"
    with open(latest, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    paths["analysis_snapshot_latest"] = latest

    hist = _history_path(out_dir, snapshot.get("analysis_end"))
    hist.parent.mkdir(parents=True, exist_ok=True)
    with open(hist, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    paths["analysis_snapshot_history"] = hist
    return paths


def write_monitoring_diff_txt(diff: dict[str, Any], path: Path) -> None:
    lines = [
        "Monitoring — What Changed",
        "=" * 50,
        "",
        f"Status: {diff.get('diff_status')}",
        f"Primary profile: {diff.get('primary_profile_id')}",
    ]
    if diff.get("prior_analysis_end"):
        lines.append(f"Prior analysis end: {diff['prior_analysis_end']}")
    if diff.get("current_analysis_end"):
        lines.append(f"Current analysis end: {diff['current_analysis_end']}")
    lines.append("")
    lines.append(diff.get("summary_plain_en") or "")
    lines.append("")
    if diff.get("rebalance_trigger"):
        lines.append("Rebalance trigger: review suggested (non-executing).")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def write_monitoring_outputs(
    cfg: PortfolioConfig,
    *,
    project_root: Path | None = None,
    comparison: dict[str, Any] | None = None,
    health: dict[str, Any] | None = None,
    robustness: dict[str, Any] | None = None,
    selection: dict[str, Any] | None = None,
    action: dict[str, Any] | None = None,
    write_txt: bool = True,
) -> dict[str, Path]:
    """Write monitoring snapshot (latest+history) and monitoring_diff after decision pipeline."""
    project_root = project_root or Path.cwd()
    out_dir = project_root / str(getattr(cfg, "output_dir_final", "Main portfolio"))

    if comparison is None:
        comparison = _load_json(out_dir / "candidate_comparison.json")
    if not comparison:
        return {}

    if health is None:
        health = _load_json(out_dir / "portfolio_health_score.json")
    if robustness is None:
        robustness = _load_json(out_dir / "robustness_scorecard.json")
    if selection is None:
        selection = _load_json(out_dir / "selection_decision.json")
    if action is None:
        action = _load_json(out_dir / "action_plan.json")

    prior_path = out_dir / LATEST_SNAPSHOT_REL
    prior_snapshot = _load_json(prior_path)

    snapshot = build_analysis_snapshot(
        comparison,
        health=health,
        robustness=robustness,
        selection=selection,
        action=action,
        project_root=project_root,
    )
    diff = build_monitoring_diff(snapshot, prior_snapshot)

    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    diff_json = out_dir / "monitoring_diff.json"
    with open(diff_json, "w", encoding="utf-8") as f:
        json.dump(diff, f, indent=2, ensure_ascii=False)
    paths["monitoring_diff_json"] = diff_json

    if write_txt:
        diff_txt = out_dir / "monitoring_diff.txt"
        write_monitoring_diff_txt(diff, diff_txt)
        paths["monitoring_diff_txt"] = diff_txt

    paths.update(persist_analysis_snapshot(out_dir, snapshot))
    return paths


__all__ = [
    "SNAPSHOT_SCHEMA_VERSION",
    "DIFF_SCHEMA_VERSION",
    "build_analysis_snapshot",
    "build_monitoring_diff",
    "persist_analysis_snapshot",
    "write_monitoring_outputs",
    "write_monitoring_diff_txt",
]
