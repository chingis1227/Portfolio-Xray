"""
Selection Engine and No-Trade Recommendation (formal, non-executing decision record).

See docs/specs/selection_engine_spec.md.
"""

from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config_schema import PortfolioConfig
from src.optimization_status import optimization_quality_family

SCHEMA_VERSION = "selection_decision_v1"
WEIGHTS_PROFILE = "default_weights_reviewable"
THRESHOLDS_PROFILE = "default_no_trade_thresholds_reviewable"
PRIMARY_WINDOW = "10y"
SNAPSHOT_10Y = "snapshot_10y.json"

DEFAULT_SELECTION_WEIGHTS: dict[str, float] = {
    "w_health": 0.45,
    "w_robust": 0.45,
    "w_mandate": 0.10,
}

DEFAULT_NO_TRADE_THRESHOLDS: dict[str, float] = {
    "min_health_score_delta": 3.0,
    "min_robustness_score_delta": 3.0,
    "max_turnover_half_sum_pct": 15.0,
    "min_max_drawdown_improvement_pp": 1.0,
}

ELIGIBLE_STATUSES = frozenset({"available", "degraded"})
SCORABLE_SCORE_STATUSES = frozenset({"scored", "partial"})
BASELINE_CANDIDATE_IDS = ("analysis_subject", "current")

FORBIDDEN_RATIONALE_PATTERNS = (
    re.compile(r"\bbuy\b", re.IGNORECASE),
    re.compile(r"\bsell\b", re.IGNORECASE),
    re.compile(r"\brecommended\s+buy\b", re.IGNORECASE),
    re.compile(r"\brecommended\s+sell\b", re.IGNORECASE),
    re.compile(r"\bFAIL_[A-Z0-9_]+\b"),
    re.compile(r"\bDIAG_[A-Z0-9_]+\b"),
)


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


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _candidates_by_id(comparison: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {c["candidate_id"]: c for c in comparison.get("candidates", []) if c.get("candidate_id")}


def _baseline_candidate_id(by_id: dict[str, dict[str, Any]]) -> str | None:
    for candidate_id in BASELINE_CANDIDATE_IDS:
        cand = by_id.get(candidate_id)
        if cand and cand.get("status") in ELIGIBLE_STATUSES:
            return candidate_id
    return None


def _score_maps(
    health: dict[str, Any] | None,
    robustness: dict[str, Any] | None,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    health_by_id: dict[str, dict[str, Any]] = {}
    robust_by_id: dict[str, dict[str, Any]] = {}
    if health:
        for row in health.get("candidates", []):
            cid = row.get("candidate_id")
            if cid:
                health_by_id[str(cid)] = row
    if robustness:
        for row in robustness.get("candidates", []):
            cid = row.get("candidate_id")
            if cid:
                robust_by_id[str(cid)] = row
    return health_by_id, robust_by_id


def _mandate_component(cand: dict[str, Any]) -> tuple[float, list[str]]:
    """Absolute 0–100 mandate component and row-level flags."""
    flags: list[str] = []
    mandate = cand.get("mandate") or {}
    pv = mandate.get("portfolio_valid")
    status = cand.get("status")

    if pv is False:
        return 0.0, flags

    if pv is True:
        if status == "degraded" or cand.get("warnings"):
            return 70.0, flags
        return 100.0, flags

    flags.append("mandate_unknown")
    return 50.0, flags


def _health_total(row: dict[str, Any] | None) -> float | None:
    if not row or row.get("score_status") not in SCORABLE_SCORE_STATUSES:
        return None
    return _finite(row.get("total_score"))


def _robustness_total(row: dict[str, Any] | None) -> float | None:
    if not row or row.get("score_status") not in SCORABLE_SCORE_STATUSES:
        return None
    return _finite(row.get("total_score"))


def _resolve_weights(
    cand: dict[str, Any],
    *,
    project_root: Path,
) -> dict[str, float] | None:
    """Load final_weights_total from candidate artifact folder."""
    root = cand.get("artifact_root")
    if not root:
        return None
    folder = project_root / str(root).replace("\\", "/")
    snap = _load_json(folder / SNAPSHOT_10Y)
    if not snap:
        return None
    weights_raw = snap.get("final_weights_total")
    if not isinstance(weights_raw, dict) or not weights_raw:
        return None
    out: dict[str, float] = {}
    for ticker, pct in weights_raw.items():
        v = _finite(pct)
        if v is None or v < 0:
            continue
        out[str(ticker)] = float(v)
    return out or None


def _turnover_half_sum_pct(
    w_target: dict[str, float],
    w_current: dict[str, float],
) -> float:
    keys = set(w_target) | set(w_current)
    total = sum(abs(w_target.get(k, 0.0) - w_current.get(k, 0.0)) for k in keys)
    return round(0.5 * total * 100.0, 3)


def _max_drawdown_value(cand: dict[str, Any]) -> float | None:
    dd = cand.get("drawdown") or {}
    v = _finite(dd.get("max_drawdown"))
    if v is not None:
        return v
    metrics = (cand.get("metrics") or {}).get(PRIMARY_WINDOW) or {}
    return _finite(metrics.get("max_drawdown"))


def _drawdown_improvement_pp(target: dict[str, Any], current: dict[str, Any]) -> float | None:
    t_dd = _max_drawdown_value(target)
    c_dd = _max_drawdown_value(current)
    if t_dd is None or c_dd is None:
        return None
    return round((t_dd - c_dd) * 100.0, 3)


def _mandate_breach_indicators(cand: dict[str, Any]) -> bool:
    mandate = cand.get("mandate") or {}
    if mandate.get("portfolio_valid") is False:
        return True
    stress = cand.get("stress") or {}
    fail = str(stress.get("fail_reason_code") or stress.get("primary_diagnostic_code") or "")
    if fail:
        upper = fail.upper()
        if "MANDATE" in upper or "MAXDD" in upper or "FAIL_" in upper:
            return True
    warnings = cand.get("warnings") or []
    return any("mandate" in str(w).lower() for w in warnings)


def _candidate_optimization_quality(cand: dict[str, Any]) -> dict[str, Any]:
    disclosure = cand.get("construction_disclosure") or {}
    quality = disclosure.get("optimizer_quality")
    if isinstance(quality, dict):
        return quality
    methodology = disclosure.get("optimizer_methodology")
    if isinstance(methodology, dict):
        solver = methodology.get("solver")
        if isinstance(solver, dict):
            q_status = solver.get("optimization_quality_status")
            fallback_used = bool(solver.get("fallback_used", False))
            if q_status or fallback_used:
                return {
                    "optimization_quality_status": q_status,
                    "optimization_quality_family": optimization_quality_family(
                        q_status,
                        fallback_used=fallback_used,
                    ),
                    "fallback_used": fallback_used,
                    "fallback_reason": solver.get("fallback_reason"),
                }
    return {}


def _check_mandate_risk_reduction(
    by_id: dict[str, dict[str, Any]],
    *,
    baseline_id: str | None = None,
) -> tuple[bool, list[str]]:
    notes: list[str] = []
    baseline_id = baseline_id or _baseline_candidate_id(by_id)
    current = by_id.get(baseline_id or "current")
    policy = by_id.get("policy")

    if current and current.get("status") in ELIGIBLE_STATUSES:
        if _mandate_breach_indicators(current):
            label = current.get("display_name") or current.get("candidate_id") or "Starting portfolio"
            notes.append(
                f"{label} does not meet mandate fit; risk reduction is required before allocation changes."
            )
            return True, notes

    if baseline_id == "analysis_subject":
        return False, notes

    if policy and policy.get("status") in ELIGIBLE_STATUSES:
        if _mandate_breach_indicators(policy):
            if current and current.get("status") in ELIGIBLE_STATUSES and _mandate_breach_indicators(current):
                notes.append(
                    "Both policy and current profiles show mandate stress; address risk limits before rebalancing."
                )
            else:
                notes.append(
                    "Policy profile fails mandate validation; allocation change is not advised until constraints are resolved."
                )
            return True, notes

    return False, notes


def _selection_weights(
    health: dict[str, Any] | None,
    robustness: dict[str, Any] | None,
    warnings: list[str],
) -> tuple[dict[str, float], bool]:
    has_health = bool(health and health.get("candidates"))
    has_robust = bool(robustness and robustness.get("candidates"))
    if not has_health and not has_robust:
        return dict(DEFAULT_SELECTION_WEIGHTS), False
    if has_health and has_robust:
        return dict(DEFAULT_SELECTION_WEIGHTS), False
    warnings.append("partial_score_inputs")
    return {"w_health": 0.45, "w_robust": 0.45, "w_mandate": 0.10}, True


def _composite_row(
    cand: dict[str, Any],
    *,
    health_row: dict[str, Any] | None,
    robust_row: dict[str, Any] | None,
    weights: dict[str, float],
) -> dict[str, Any] | None:
    cid = cand["candidate_id"]
    if cand.get("status") not in ELIGIBLE_STATUSES:
        return None
    if cid in BASELINE_CANDIDATE_IDS or cand.get("role") in ("analysis_subject", "user_current"):
        return None

    mandate_pts, _ = _mandate_component(cand)
    if mandate_pts <= 0:
        return None

    h = _health_total(health_row)
    r = _robustness_total(robust_row)
    if h is None and r is None:
        return None

    h_eff = h if h is not None else 0.0
    r_eff = r if r is not None else 0.0
    if h is None or r is None:
        # Single-score path: renormalize health+robust portion only when one missing
        if h is None and r is not None:
            w_h, w_r = 0.0, weights["w_robust"] / (weights["w_health"] + weights["w_robust"])
        elif r is None and h is not None:
            w_h, w_r = weights["w_health"] / (weights["w_health"] + weights["w_robust"]), 0.0
        else:
            w_h, w_r = weights["w_health"], weights["w_robust"]
    else:
        w_h, w_r = weights["w_health"], weights["w_robust"]

    selection_score = w_h * h_eff + w_r * r_eff + weights["w_mandate"] * mandate_pts
    return {
        "candidate_id": cid,
        "display_name": cand.get("display_name", cid),
        "selection_score": round(selection_score, 3),
        "health_total": h,
        "robustness_total": r,
        "mandate_component": round(mandate_pts, 3),
        "health_rank": (health_row or {}).get("health_rank"),
        "robustness_rank": (robust_row or {}).get("robustness_rank"),
    }


def _composite_sort_key(row: dict[str, Any]) -> tuple:
    rr = row.get("robustness_rank")
    hr = row.get("health_rank")
    return (
        -float(row.get("selection_score") or 0),
        rr if rr is not None else 10_000,
        hr if hr is not None else 10_000,
        row.get("candidate_id") or "",
    )


def _evaluate_no_trade(
    *,
    target: dict[str, Any],
    baseline: dict[str, Any],
    health_by_id: dict[str, dict[str, Any]],
    robust_by_id: dict[str, dict[str, Any]],
    project_root: Path,
    thresholds: dict[str, float],
    warnings: list[str],
) -> tuple[bool, dict[str, Any]]:
    """Returns (is_no_trade, no_trade_block)."""
    target_id = target["candidate_id"]
    baseline_id = str(baseline.get("candidate_id") or "current")
    h_tgt = _health_total(health_by_id.get(target_id))
    h_cur = _health_total(health_by_id.get(baseline_id))
    r_tgt = _robustness_total(robust_by_id.get(target_id))
    r_cur = _robustness_total(robust_by_id.get(baseline_id))

    health_delta: float | None = None
    robust_delta: float | None = None
    if h_tgt is not None and h_cur is not None:
        health_delta = round(h_tgt - h_cur, 3)
    if r_tgt is not None and r_cur is not None:
        robust_delta = round(r_tgt - r_cur, 3)

    w_target = _resolve_weights(target, project_root=project_root)
    w_current = _resolve_weights(baseline, project_root=project_root)
    turnover: float | None = None
    if w_target and w_current:
        turnover = _turnover_half_sum_pct(w_target, w_current)

    dd_improvement = _drawdown_improvement_pp(target, baseline)
    if dd_improvement is None:
        warnings.append("no_trade_drawdown_unknown")

    min_h = thresholds["min_health_score_delta"]
    min_r = thresholds["min_robustness_score_delta"]
    max_turn = thresholds["max_turnover_half_sum_pct"]
    min_dd = thresholds["min_max_drawdown_improvement_pp"]

    small_scores = (
        health_delta is not None
        and robust_delta is not None
        and health_delta < min_h
        and robust_delta < min_r
    )

    high_turnover = turnover is not None and turnover > max_turn
    weak_drawdown = dd_improvement is not None and dd_improvement < min_dd

    if not small_scores:
        is_no_trade = False
    elif dd_improvement is None:
        is_no_trade = bool(high_turnover)
    else:
        is_no_trade = bool(high_turnover or weak_drawdown)

    block: dict[str, Any] = {
        "evaluated": True,
        "baseline_candidate_id": baseline_id,
        "target_candidate_id": target_id,
        "health_score_delta": health_delta,
        "robustness_score_delta": robust_delta,
        "turnover_half_sum_abs_delta_pct": turnover,
        "drawdown_improvement_pp": dd_improvement,
        "thresholds_profile": THRESHOLDS_PROFILE,
        "materiality_pass": not is_no_trade,
        "summary": (
            f"No material rebalance suggested versus {baseline.get('display_name') or baseline_id}."
            if is_no_trade
            else f"Material benefit versus {baseline.get('display_name') or baseline_id} may warrant review."
        ),
    }
    return is_no_trade, block


def _build_rejected(
    composite: list[dict[str, Any]],
    favored_id: str | None,
    by_id: dict[str, dict[str, Any]],
    *,
    baseline_id: str | None = None,
) -> list[dict[str, Any]]:
    rejected: list[dict[str, Any]] = []
    ranked_ids = {r["candidate_id"] for r in composite}
    for cid, cand in sorted(by_id.items()):
        if cid == favored_id:
            continue
        if cid == baseline_id or cid in BASELINE_CANDIDATE_IDS:
            continue
        if cand.get("status") == "unavailable":
            rejected.append(
                {
                    "candidate_id": cid,
                    "display_name": cand.get("display_name", cid),
                    "reason_code": "unavailable",
                    "short_note": cand.get("unavailable_reason") or "Artifacts not available for comparison.",
                }
            )
        elif cid not in ranked_ids and cand.get("status") in ELIGIBLE_STATUSES:
            rejected.append(
                {
                    "candidate_id": cid,
                    "display_name": cand.get("display_name", cid),
                    "reason_code": "not_favored",
                    "short_note": "Not selected in this comparison run.",
                }
            )
        elif cid in ranked_ids and cid != favored_id:
            rejected.append(
                {
                    "candidate_id": cid,
                    "display_name": cand.get("display_name", cid),
                    "reason_code": "lower_composite_score",
                    "short_note": "Lower composite selection score than the favored profile.",
                }
            )
    return rejected


def _rationale_strings_forbidden(text: str) -> bool:
    return any(p.search(text) for p in FORBIDDEN_RATIONALE_PATTERNS)


def build_selection_decision(
    comparison: dict[str, Any],
    *,
    health: dict[str, Any] | None = None,
    robustness: dict[str, Any] | None = None,
    project_root: Path | None = None,
) -> dict[str, Any] | None:
    """Build selection decision document; None if comparison is unusable."""
    if not comparison or not comparison.get("candidates"):
        return None

    project_root = project_root or Path.cwd()
    warnings: list[str] = []
    missing_inputs: list[str] = []
    by_id = _candidates_by_id(comparison)
    baseline_id = _baseline_candidate_id(by_id)
    baseline = by_id.get(baseline_id) if baseline_id else None

    health_by_id, robust_by_id = _score_maps(health, robustness)
    has_health = bool(health_by_id)
    has_robust = bool(robust_by_id)

    if not has_health and not has_robust:
        return {
            "schema_version": SCHEMA_VERSION,
            "formal_decision": True,
            "non_executing": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "analysis_end": comparison.get("analysis_end"),
            "investor_currency": comparison.get("investor_currency"),
            "output_dir_final": comparison.get("output_dir_final"),
            "decision_status": "data_review_required",
            "baseline_candidate_id": baseline_id,
            "baseline_display_name": (baseline or {}).get("display_name"),
            "favored_candidate_id": None,
            "favored_display_name": None,
            "selection_weights_profile": WEIGHTS_PROFILE,
            "no_trade_thresholds_profile": THRESHOLDS_PROFILE,
            "composite_ranking": [],
            "rationale": {
                "summary": "Decision requires data review before acting on results.",
                "selection_bullets": [],
                "no_trade_bullets": [],
                "tradeoff_bullets": [],
                "data_quality_notes": ["Missing both portfolio health and robustness score artifacts."],
            },
            "no_trade": None,
            "rejected_candidates": [],
            "warnings": ["missing_score_artifacts"],
            "input_artifacts": {
                "candidate_comparison": "candidate_comparison.json",
                "portfolio_health_score": None,
                "robustness_scorecard": None,
            },
            "missing_inputs": ["portfolio_health_score.json", "robustness_scorecard.json"],
        }

    sel_weights, _ = _selection_weights(health, robustness, warnings)
    thresholds = dict(DEFAULT_NO_TRADE_THRESHOLDS)

    if not has_health:
        missing_inputs.append("portfolio_health_score.json")
    if not has_robust:
        missing_inputs.append("robustness_scorecard.json")

    mandate_reduction, risk_notes = _check_mandate_risk_reduction(
        by_id,
        baseline_id=baseline_id,
    )

    composite: list[dict[str, Any]] = []
    for cid, cand in by_id.items():
        row = _composite_row(
            cand,
            health_row=health_by_id.get(cid),
            robust_row=robust_by_id.get(cid),
            weights=sel_weights,
        )
        if row:
            composite.append(row)

    composite.sort(key=_composite_sort_key)
    for i, row in enumerate(composite, start=1):
        row["rank"] = i

    policy = by_id.get("policy")
    favored_id: str | None = None
    favored_display: str | None = None

    if baseline_id != "analysis_subject" and policy and policy.get("status") in ELIGIBLE_STATUSES:
        m_pts, _ = _mandate_component(policy)
        if m_pts > 0:
            favored_id = "policy"
            favored_display = policy.get("display_name", "Policy Portfolio")

    if favored_id is None and composite:
        winner = composite[0]
        favored_id = winner["candidate_id"]
        favored_display = winner["display_name"]

    rejected = _build_rejected(composite, favored_id, by_id, baseline_id=baseline_id)

    rationale: dict[str, Any] = {
        "summary": "",
        "selection_bullets": [],
        "no_trade_bullets": [],
        "tradeoff_bullets": [],
        "data_quality_notes": [],
    }
    no_trade_block: dict[str, Any] | None = None
    decision_status: str

    if mandate_reduction:
        decision_status = "mandate_risk_reduction"
        favored_id = None
        favored_display = None
        rationale["summary"] = (
            "Mandate constraints require risk reduction; allocation change is not advised until resolved."
        )
        rationale["selection_bullets"] = risk_notes[:5]
        rationale["risk_reduction_notes"] = risk_notes[:5]
        rationale["data_quality_notes"] = risk_notes
        warnings.append("mandate_risk_reduction")
    elif favored_id is None:
        decision_status = "inconclusive"
        rationale["summary"] = "Selection inconclusive; review comparison and score drivers."
        if not composite:
            rationale["data_quality_notes"].append("No eligible scored candidates for composite ranking.")
            warnings.append("no_scored_candidates")
    else:
        current = baseline
        current_ok = current and current.get("status") in ELIGIBLE_STATUSES
        target = by_id.get(favored_id) or {}
        target_quality = _candidate_optimization_quality(target)

        if favored_id == "policy" and policy and policy.get("status") in ELIGIBLE_STATUSES:
            rationale["selection_bullets"].append(
                "Policy (optimized) profile is the default favored target when mandate fit allows."
            )
        elif composite and composite[0]["candidate_id"] == favored_id:
            rationale["selection_bullets"].append(
                f"Highest composite selection score among eligible alternatives ({composite[0]['selection_score']:.1f})."
            )

        if current_ok and favored_id != baseline_id:
            w_tgt = _resolve_weights(target, project_root=project_root)
            w_cur = _resolve_weights(current, project_root=project_root)
            if w_tgt and w_cur:
                is_no_trade, no_trade_block = _evaluate_no_trade(
                    target=target,
                    baseline=current,
                    health_by_id=health_by_id,
                    robust_by_id=robust_by_id,
                    project_root=project_root,
                    thresholds=thresholds,
                    warnings=warnings,
                )
                if is_no_trade:
                    decision_status = "no_material_rebalance"
                    rationale["summary"] = no_trade_block.get(
                        "summary",
                        "No material rebalance suggested versus the starting portfolio.",
                    )
                    rationale["no_trade_bullets"] = [
                        f"Health score delta versus baseline: {no_trade_block.get('health_score_delta')}.",
                        f"Robustness score delta versus baseline: {no_trade_block.get('robustness_score_delta')}.",
                        f"Estimated turnover (half-sum): {no_trade_block.get('turnover_half_sum_abs_delta_pct')}%.",
                    ]
                else:
                    decision_status = "selected_candidate"
                    rationale["summary"] = (
                        f"Favored profile: {favored_display} for this comparison."
                    )
            else:
                decision_status = "selected_candidate"
                rationale["summary"] = (
                    f"Favored profile: {favored_display} for this comparison."
                )
                warnings.append("no_trade_skipped_missing_weights")
                rationale["data_quality_notes"].append(
                    "No-Trade materiality not evaluated: baseline or target weight vectors could not be loaded."
                )
        else:
            decision_status = "selected_candidate"
            rationale["summary"] = f"Favored profile: {favored_display} for this comparison."
            if not current_ok:
                warnings.append("no_trade_not_actionable")
                rationale["data_quality_notes"].append(
                    "Starting portfolio baseline not available; No-Trade versus baseline was not evaluated."
                )
                cur = by_id.get("current") or {}
                if cur.get("unavailable_reason") == "missing_current_report":
                    rationale["data_quality_notes"].append(
                        "Run: python run_report.py --materialize-current"
                    )

        if target_quality:
            family = target_quality.get("optimization_quality_family")
            q_status = target_quality.get("optimization_quality_status") or "unknown"
            if family == "approximate":
                warnings.append(f"favored_optimizer_quality_not_clean:{favored_id}:{q_status}")
                rationale["data_quality_notes"].append(
                    "Favored target used an approximate optimizer solve or fallback; review construction disclosure before acting."
                )
            elif family == "failed":
                warnings.append(f"favored_optimizer_quality_failed:{favored_id}:{q_status}")
                rationale["data_quality_notes"].append(
                    "Favored target reports failed optimizer quality; review comparison artifacts before acting."
                )

    if missing_inputs:
        rationale["data_quality_notes"].append(
            f"Partial score inputs: {', '.join(missing_inputs)}."
        )

    doc: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "formal_decision": True,
        "non_executing": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analysis_end": comparison.get("analysis_end"),
        "investor_currency": comparison.get("investor_currency"),
        "output_dir_final": comparison.get("output_dir_final"),
        "baseline_candidate_id": baseline_id,
        "baseline_display_name": (baseline or {}).get("display_name"),
        "decision_status": decision_status,
        "favored_candidate_id": favored_id,
        "favored_display_name": favored_display,
        "selection_weights_profile": WEIGHTS_PROFILE,
        "no_trade_thresholds_profile": THRESHOLDS_PROFILE,
        "selection_weights": sel_weights,
        "no_trade_thresholds": thresholds,
        "composite_ranking": composite,
        "rationale": rationale,
        "no_trade": no_trade_block,
        "rejected_candidates": rejected,
        "warnings": sorted(set(warnings)),
        "input_artifacts": {
            "candidate_comparison": "candidate_comparison.json",
            "portfolio_health_score": (
                "portfolio_health_score.json" if has_health else None
            ),
            "robustness_scorecard": (
                "robustness_scorecard.json" if has_robust else None
            ),
        },
        "missing_inputs": missing_inputs,
    }
    return doc


def write_selection_decision_txt(decision: dict[str, Any], path: Path) -> None:
    status = decision.get("decision_status", "")
    favored = decision.get("favored_display_name") or decision.get("favored_candidate_id") or "—"
    lines = [
        f"Selection decision (formal, non-executing) — primary window {PRIMARY_WINDOW}",
        f"Status: {status}",
        f"Favored profile: {favored}",
        "",
    ]
    nt = decision.get("no_trade")
    if nt and nt.get("evaluated"):
        baseline = nt.get("baseline_candidate_id") or decision.get("baseline_candidate_id") or "current"
        lines.extend(
            [
                (
                    f"Versus {baseline}: health {nt.get('health_score_delta')}, "
                    f"robustness {nt.get('robustness_score_delta')}, "
                    f"turnover (half-sum) {nt.get('turnover_half_sum_abs_delta_pct')}%"
                ),
                f"Conclusion: {nt.get('summary', '')}",
                "",
            ]
        )
    elif decision.get("rationale", {}).get("summary"):
        lines.append(decision["rationale"]["summary"])
        lines.append("")

    lines.append("See selection_decision.json for composite ranking and rejected candidates.")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def write_selection_decision_outputs(
    cfg: PortfolioConfig,
    *,
    project_root: Path | None = None,
    comparison: dict[str, Any] | None = None,
    health: dict[str, Any] | None = None,
    robustness: dict[str, Any] | None = None,
    write_txt: bool = True,
) -> dict[str, Path]:
    """Write selection_decision.json when comparison exists."""
    project_root = project_root or Path.cwd()
    out_dir = project_root / str(getattr(cfg, "output_dir_final", "Main portfolio"))

    if comparison is None:
        json_path = out_dir / "candidate_comparison.json"
        if not json_path.is_file():
            return {}
        with open(json_path, encoding="utf-8") as f:
            comparison = json.load(f)

    if health is None:
        health = _load_json(out_dir / "portfolio_health_score.json")
    if robustness is None:
        robustness = _load_json(out_dir / "robustness_scorecard.json")

    decision = build_selection_decision(
        comparison,
        health=health,
        robustness=robustness,
        project_root=project_root,
    )
    if decision is None:
        return {}

    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    json_out = out_dir / "selection_decision.json"
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(decision, f, indent=2, ensure_ascii=False)
    paths["selection_decision_json"] = json_out

    if write_txt:
        txt_out = out_dir / "selection_decision.txt"
        write_selection_decision_txt(decision, txt_out)
        paths["selection_decision_txt"] = txt_out

    return paths


def rationale_text_is_client_safe(text: str) -> bool:
    """True when text passes V1 forbidden-pattern lint."""
    return not _rationale_strings_forbidden(text)


__all__ = [
    "SCHEMA_VERSION",
    "DEFAULT_NO_TRADE_THRESHOLDS",
    "DEFAULT_SELECTION_WEIGHTS",
    "build_selection_decision",
    "rationale_text_is_client_safe",
    "write_selection_decision_outputs",
    "write_selection_decision_txt",
]
