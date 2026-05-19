"""
Trade-off Explanation and Model Risk Diagnostics (diagnostic-only).

See docs/specs/tradeoff_and_model_risk_spec.md.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config_schema import PortfolioConfig
from src.selection_engine import (
    _finite,
    _resolve_weights,
    _turnover_half_sum_pct,
)

TRADEOFF_SCHEMA = "tradeoff_explanation_v1"
MODEL_RISK_SCHEMA = "model_risk_diagnostics_v1"
PRIMARY_WINDOW = "10y"
ELIGIBLE_BASELINE_STATUSES = frozenset({"available", "degraded"})
BASELINE_CANDIDATE_IDS = ("analysis_subject", "current")
SEVERITY_ORDER = ("info", "low", "medium", "high")

DIMENSION_SPECS: tuple[tuple[str, str, str, str], ...] = (
    ("return_cagr", "cagr", "pct", "higher"),
    ("risk_vol", "vol_annual", "pct", "lower"),
    ("drawdown", "max_drawdown", "pct", "higher"),
    ("risk_adjusted_sharpe", "sharpe", "ratio", "higher"),
)


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _round3(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 3)


def _candidates_by_id(comparison: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {c["candidate_id"]: c for c in comparison.get("candidates", []) if c.get("candidate_id")}


def _candidate_available(cand: dict[str, Any] | None) -> bool:
    return bool(cand and cand.get("status") in ELIGIBLE_BASELINE_STATUSES)


def _preferred_baseline_id(
    comparison: dict[str, Any],
    selection: dict[str, Any] | None,
    by_id: dict[str, dict[str, Any]],
) -> str | None:
    explicit = (selection or {}).get("baseline_candidate_id")
    if explicit and _candidate_available(by_id.get(str(explicit))):
        return str(explicit)
    comp_baseline = comparison.get("comparison_baseline_candidate_id")
    if comp_baseline and _candidate_available(by_id.get(str(comp_baseline))):
        return str(comp_baseline)
    for candidate_id in BASELINE_CANDIDATE_IDS:
        if _candidate_available(by_id.get(candidate_id)):
            return candidate_id
    return None


def _metrics_10y(cand: dict[str, Any]) -> dict[str, Any]:
    return (cand.get("metrics") or {}).get(PRIMARY_WINDOW) or {}


def _max_drawdown_value(cand: dict[str, Any]) -> float | None:
    dd = cand.get("drawdown") or {}
    v = _finite(dd.get("max_drawdown"))
    if v is not None:
        return v
    return _finite(_metrics_10y(cand).get("max_drawdown"))


def _worst_scenario_loss(stress: dict[str, Any]) -> float | None:
    scenarios = stress.get("scenarios") or []
    losses: list[float] = []
    for row in scenarios:
        if not isinstance(row, dict):
            continue
        pnl = _finite(row.get("portfolio_pnl_pct"))
        if pnl is not None:
            losses.append(pnl)
    if not losses:
        return None
    return min(losses)


def _stress_rank(overall: Any) -> int | None:
    if overall is None:
        return None
    text = str(overall).strip().upper()
    if not text:
        return None
    if text.startswith("FAIL"):
        return 0
    if "FAIL" in text:
        return 0
    if text.startswith("DIAG_PASS") or text.endswith("PASS"):
        return 2
    if text.startswith("DIAG"):
        return 1
    return 1


def _stress_is_fail(overall: Any) -> bool:
    rank = _stress_rank(overall)
    return rank == 0


def _direction(
    baseline: float | None,
    target: float | None,
    *,
    better: str,
) -> str:
    if baseline is None or target is None:
        return "unknown"
    if baseline == target:
        return "unchanged"
    if better == "higher":
        if target > baseline:
            return "improves"
        return "worsens"
    if target < baseline:
        return "improves"
    return "worsens"


def _plain_dimension(
    dimension_id: str,
    *,
    baseline: float | None,
    target: float | None,
    delta: float | None,
    direction: str,
    baseline_name: str,
    target_name: str,
) -> str:
    labels = {
        "return_cagr": "10y CAGR",
        "risk_vol": "10y annualized volatility",
        "drawdown": "10y maximum drawdown",
        "risk_adjusted_sharpe": "10y Sharpe ratio",
        "stress_worst_loss": "worst stress scenario loss",
        "stress_overall": "stress overall status",
        "health_score": "portfolio health score",
        "robustness_score": "robustness score",
    }
    label = labels.get(dimension_id, dimension_id)
    if direction == "unknown":
        return f"{label} could not be compared between {baseline_name} and {target_name}."
    if direction == "unchanged":
        return f"{label} is unchanged between {baseline_name} and {target_name}."
    verb = "higher" if direction == "improves" and dimension_id in (
        "return_cagr",
        "drawdown",
        "risk_adjusted_sharpe",
        "health_score",
        "robustness_score",
        "stress_worst_loss",
        "stress_overall",
    ) else "lower"
    if dimension_id in ("risk_vol",):
        verb = "lower" if direction == "improves" else "higher"
    if delta is not None and dimension_id not in ("stress_overall",):
        return (
            f"{label} is {verb} on {target_name} versus {baseline_name} "
            f"(delta {_round3(delta)})."
        )
    return f"{label} {direction.replace('_', ' ')}s on {target_name} versus {baseline_name}."


def _score_total(
    doc: dict[str, Any] | None,
    candidate_id: str,
) -> float | None:
    if not doc:
        return None
    for row in doc.get("candidates", []):
        if row.get("candidate_id") == candidate_id:
            if row.get("score_status") not in ("scored", "partial"):
                return None
            return _finite(row.get("total_score"))
    return None


def _build_dimension(
    dimension_id: str,
    *,
    baseline: dict[str, Any],
    target: dict[str, Any],
    baseline_name: str,
    target_name: str,
    health: dict[str, Any] | None,
    robustness: dict[str, Any] | None,
    warnings: list[str],
) -> dict[str, Any]:
    b_id = baseline["candidate_id"]
    t_id = target["candidate_id"]
    b_m = _metrics_10y(baseline)
    t_m = _metrics_10y(target)
    b_stress = baseline.get("stress") or {}
    t_stress = target.get("stress") or {}

    baseline_value: float | None = None
    target_value: float | None = None
    delta: float | None = None
    delta_unit = "pct"
    better = "higher"
    delta_note: str | None = None

    if dimension_id == "return_cagr":
        baseline_value = _finite(b_m.get("cagr"))
        target_value = _finite(t_m.get("cagr"))
        better = "higher"
    elif dimension_id == "risk_vol":
        baseline_value = _finite(b_m.get("vol_annual"))
        target_value = _finite(t_m.get("vol_annual"))
        better = "lower"
    elif dimension_id == "drawdown":
        baseline_value = _max_drawdown_value(baseline)
        target_value = _max_drawdown_value(target)
        better = "higher"
        delta_note = "Positive delta means less negative drawdown on the target."
    elif dimension_id == "risk_adjusted_sharpe":
        baseline_value = _finite(b_m.get("sharpe"))
        target_value = _finite(t_m.get("sharpe"))
        delta_unit = "ratio"
        better = "higher"
    elif dimension_id == "stress_worst_loss":
        baseline_value = _worst_scenario_loss(b_stress)
        target_value = _worst_scenario_loss(t_stress)
        better = "higher"
        delta_note = "Positive delta means a smaller loss on the target."
    elif dimension_id == "stress_overall":
        baseline_value = _stress_rank(b_stress.get("overall"))
        target_value = _stress_rank(t_stress.get("overall"))
        delta_unit = "rank"
        better = "higher"
    elif dimension_id == "health_score":
        baseline_value = _score_total(health, b_id)
        target_value = _score_total(health, t_id)
        delta_unit = "score_points"
        better = "higher"
    elif dimension_id == "robustness_score":
        baseline_value = _score_total(robustness, b_id)
        target_value = _score_total(robustness, t_id)
        delta_unit = "score_points"
        better = "higher"
    else:
        warnings.append(f"tradeoff_dimension_missing_{dimension_id}")
        return {
            "dimension_id": dimension_id,
            "baseline_value": None,
            "target_value": None,
            "delta": None,
            "delta_unit": "pct",
            "direction": "unknown",
            "plain_english": _plain_dimension(
                dimension_id,
                baseline=None,
                target=None,
                delta=None,
                direction="unknown",
                baseline_name=baseline_name,
                target_name=target_name,
            ),
        }

    if baseline_value is None or target_value is None:
        warnings.append(f"tradeoff_dimension_missing_{dimension_id}")
        direction = "unknown"
        delta = None
    else:
        delta = _round3(target_value - baseline_value)
        direction = _direction(baseline_value, target_value, better=better)

    dim: dict[str, Any] = {
        "dimension_id": dimension_id,
        "baseline_value": _round3(baseline_value) if baseline_value is not None else None,
        "target_value": _round3(target_value) if target_value is not None else None,
        "delta": delta,
        "delta_unit": delta_unit,
        "direction": direction,
        "plain_english": _plain_dimension(
            dimension_id,
            baseline=baseline_value,
            target=target_value,
            delta=delta,
            direction=direction,
            baseline_name=baseline_name,
            target_name=target_name,
        ),
    }
    if delta_note:
        dim["delta_note"] = delta_note
    return dim


def _pair_dimensions(
    baseline: dict[str, Any],
    target: dict[str, Any],
    *,
    health: dict[str, Any] | None,
    robustness: dict[str, Any] | None,
    warnings: list[str],
) -> list[dict[str, Any]]:
    b_name = baseline.get("display_name") or baseline.get("candidate_id", "baseline")
    t_name = target.get("display_name") or target.get("candidate_id", "target")
    dims: list[dict[str, Any]] = []
    for dim_id, _, _, _ in DIMENSION_SPECS:
        dims.append(
            _build_dimension(
                dim_id,
                baseline=baseline,
                target=target,
                baseline_name=b_name,
                target_name=t_name,
                health=health,
                robustness=robustness,
                warnings=warnings,
            )
        )
    for extra in ("stress_worst_loss", "stress_overall", "health_score", "robustness_score"):
        dims.append(
            _build_dimension(
                extra,
                baseline=baseline,
                target=target,
                baseline_name=b_name,
                target_name=t_name,
                health=health,
                robustness=robustness,
                warnings=warnings,
            )
        )
    return dims


def _aggregate_improves_worsens(dimensions: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    improves: list[str] = []
    worsens: list[str] = []
    for dim in dimensions:
        did = dim.get("dimension_id")
        if not did:
            continue
        direction = dim.get("direction")
        if direction == "improves":
            improves.append(str(did))
        elif direction == "worsens":
            worsens.append(str(did))
    return improves, worsens


def _top_weight_shifts(
    w_baseline: dict[str, float],
    w_target: dict[str, float],
    *,
    limit: int = 5,
) -> list[dict[str, Any]]:
    keys = sorted(set(w_baseline) | set(w_target))
    rows: list[dict[str, Any]] = []
    for ticker in keys:
        delta = w_target.get(ticker, 0.0) - w_baseline.get(ticker, 0.0)
        rows.append(
            {
                "ticker": ticker,
                "delta_pct": _round3(delta * 100.0),
            }
        )
    rows.sort(key=lambda r: abs(r.get("delta_pct") or 0.0), reverse=True)
    return rows[:limit]


def _build_pair(
    pair_id: str,
    baseline: dict[str, Any],
    target: dict[str, Any],
    *,
    health: dict[str, Any] | None,
    robustness: dict[str, Any] | None,
    project_root: Path,
    warnings: list[str],
) -> dict[str, Any]:
    pair_warnings: list[str] = []
    dimensions = _pair_dimensions(
        baseline,
        target,
        health=health,
        robustness=robustness,
        warnings=pair_warnings,
    )
    warnings.extend(pair_warnings)
    w_b = _resolve_weights(baseline, project_root=project_root)
    w_t = _resolve_weights(target, project_root=project_root)
    turnover = None
    weight_shifts: list[dict[str, Any]] = []
    if w_b and w_t:
        turnover = _turnover_half_sum_pct(w_t, w_b)
        weight_shifts = _top_weight_shifts(w_b, w_t)
    return {
        "pair_id": pair_id,
        "baseline_candidate_id": baseline.get("candidate_id"),
        "target_candidate_id": target.get("candidate_id"),
        "baseline_display_name": baseline.get("display_name"),
        "target_display_name": target.get("display_name"),
        "dimensions": dimensions,
        "turnover_half_sum_pct": turnover,
        "weight_shifts_top": weight_shifts,
    }


def build_tradeoff_explanation(
    comparison: dict[str, Any],
    selection: dict[str, Any] | None,
    *,
    project_root: Path,
    health: dict[str, Any] | None = None,
    robustness: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build tradeoff_explanation_v1 from comparison and selection."""
    warnings: list[str] = []
    by_id = _candidates_by_id(comparison)
    favored_id = (selection or {}).get("favored_candidate_id")
    decision_status = (selection or {}).get("decision_status")
    baseline_id = _preferred_baseline_id(comparison, selection, by_id)

    if selection is None:
        tradeoff_status = "selection_unavailable"
    elif not favored_id:
        tradeoff_status = "no_favored_target"
    else:
        baseline = by_id.get(baseline_id or "")
        if not baseline:
            tradeoff_status = "baseline_unavailable"
        elif favored_id not in by_id:
            tradeoff_status = "insufficient_metrics"
        else:
            target = by_id[favored_id]
            if not _metrics_10y(target) or not _metrics_10y(baseline):
                tradeoff_status = "insufficient_metrics"
            else:
                tradeoff_status = "complete"

    pairs: list[dict[str, Any]] = []
    improves: list[str] = []
    worsens: list[str] = []
    cost_of_change: dict[str, Any] = {}
    target_id = favored_id

    if favored_id and favored_id in by_id and tradeoff_status in ("complete", "baseline_unavailable"):
        target_cand = by_id[favored_id]
        if tradeoff_status == "complete":
            baseline_cand = by_id[str(baseline_id)]
            primary = _build_pair(
                "baseline_to_favored",
                baseline_cand,
                target_cand,
                health=health,
                robustness=robustness,
                project_root=project_root,
                warnings=warnings,
            )
            pairs.append(primary)
            improves, worsens = _aggregate_improves_worsens(primary.get("dimensions") or [])
            cost_of_change = {
                "turnover_half_sum_pct": primary.get("turnover_half_sum_pct"),
                "weight_shifts_top": primary.get("weight_shifts_top") or [],
            }
            if selection and selection.get("no_trade"):
                cost_of_change["no_trade_context"] = dict(selection["no_trade"])

        policy = by_id.get("policy")
        if policy and policy.get("status") in ELIGIBLE_BASELINE_STATUSES:
            if favored_id != "policy":
                pairs.append(
                    _build_pair(
                        "policy_to_favored",
                        policy,
                        target_cand,
                        health=health,
                        robustness=robustness,
                        project_root=project_root,
                        warnings=warnings,
                    )
                )
            current_cand = by_id.get("current")
            if (
                current_cand
                and current_cand.get("status") in ELIGIBLE_BASELINE_STATUSES
            ):
                pairs.append(
                    _build_pair(
                        "current_to_policy",
                        current_cand,
                        policy,
                        health=health,
                        robustness=robustness,
                        project_root=project_root,
                        warnings=warnings,
                    )
                )

        ranking = (selection or {}).get("composite_ranking") or []
        runner_up = None
        for row in ranking:
            cid = row.get("candidate_id")
            if cid and cid != favored_id and cid in by_id:
                if by_id[cid].get("status") in ELIGIBLE_BASELINE_STATUSES:
                    runner_up = cid
                    break
        if runner_up:
            pairs.append(
                _build_pair(
                    "favored_to_runner_up",
                    target_cand,
                    by_id[runner_up],
                    health=health,
                    robustness=robustness,
                    project_root=project_root,
                    warnings=warnings,
                )
            )

    if tradeoff_status == "complete" and not (improves or worsens):
        tradeoff_status = "insufficient_metrics"

    baseline_name = (by_id.get(baseline_id or "") or {}).get("display_name") or baseline_id or "baseline"
    target_name = (
        (by_id.get(target_id) or {}).get("display_name") if target_id else None
    ) or (selection or {}).get("favored_display_name") or target_id or "—"

    headline = (
        f"Comparing {baseline_name} to {target_name}: "
        f"{len(improves)} improving dimension(s), {len(worsens)} worsening dimension(s)."
    )
    paragraph_parts = [headline]
    if improves:
        paragraph_parts.append(
            "Improvements include: " + ", ".join(improves[:4]) + "."
        )
    if worsens:
        paragraph_parts.append(
            "Trade-offs include: " + ", ".join(worsens[:4]) + "."
        )
    if cost_of_change.get("turnover_half_sum_pct") is not None:
        paragraph_parts.append(
            f"Estimated weight turnover (half-sum) is "
            f"{cost_of_change['turnover_half_sum_pct']}%."
        )
    paragraph_parts.append(
        "This summary is diagnostic only and does not instruct trading."
    )

    return {
        "schema_version": TRADEOFF_SCHEMA,
        "diagnostic_only": True,
        "non_executing": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analysis_end": comparison.get("analysis_end"),
        "primary_window": comparison.get("primary_window") or PRIMARY_WINDOW,
        "tradeoff_status": tradeoff_status,
        "baseline_candidate_id": baseline_id if tradeoff_status != "baseline_unavailable" else None,
        "target_candidate_id": target_id,
        "selection_decision_status": decision_status,
        "pairs": pairs,
        "summary": {
            "headline": headline,
            "tradeoff_paragraph": " ".join(paragraph_parts),
        },
        "improves": improves,
        "worsens": worsens,
        "cost_of_change": cost_of_change,
        "warnings": sorted(set(warnings)),
        "input_artifacts": {
            "candidate_comparison": "candidate_comparison.json",
            "selection_decision": "selection_decision.json" if selection else None,
            "portfolio_health_score": "portfolio_health_score.json" if health else None,
            "robustness_scorecard": "robustness_scorecard.json" if robustness else None,
        },
    }


def _warning_row(
    warning_id: str,
    *,
    category: str,
    severity: str,
    candidate_id: str | None,
    source_artifact: str,
    plain_english: str,
    source_field: str | None = None,
    code: str | None = None,
    review_hint: str | None = None,
) -> dict[str, Any]:
    return {
        "warning_id": warning_id,
        "category": category,
        "severity": severity,
        "candidate_id": candidate_id,
        "source_artifact": source_artifact,
        "source_field": source_field,
        "code": code,
        "plain_english": plain_english,
        "review_hint": review_hint,
    }


def _adj_r2_from_regression(block: dict[str, Any] | None) -> float | None:
    if not block:
        return None
    for key in ("adj_r2", "adj_r_squared", "adjusted_r_squared"):
        v = _finite(block.get(key))
        if v is not None:
            return v
    return None


def _load_stress_report(cand: dict[str, Any], project_root: Path) -> dict[str, Any] | None:
    root = cand.get("artifact_root")
    if not root:
        return None
    folder = project_root / str(root).replace("\\", "/")
    return _load_json(folder / "stress_report.json")


def _load_run_result(cand: dict[str, Any], project_root: Path) -> dict[str, Any] | None:
    root = cand.get("artifact_root")
    if not root:
        return None
    folder = project_root / str(root).replace("\\", "/")
    return _load_json(folder / "run_result.json")


def _concentration_severity(value_pct: float, *, weight: bool) -> str | None:
    """weight: True for weight top1; False for RC top1 (values as fraction 0-1)."""
    pct = value_pct * 100.0 if value_pct <= 1.0 else value_pct
    if weight:
        if pct > 40:
            return "high"
        if pct > 25:
            return "medium"
    else:
        if pct > 45:
            return "high"
        if pct > 35:
            return "medium"
    return None


def _dedupe_warnings(warnings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best: dict[tuple[str, str | None], dict[str, Any]] = {}
    for row in warnings:
        key = (str(row.get("warning_id")), row.get("candidate_id"))
        existing = best.get(key)
        if not existing:
            best[key] = row
            continue
        sev_new = row.get("severity", "low")
        sev_old = existing.get("severity", "low")
        if SEVERITY_ORDER.index(sev_new) > SEVERITY_ORDER.index(sev_old):
            best[key] = row
    return list(best.values())


def _overall_severity(counts: dict[str, int]) -> str:
    if counts.get("high", 0) > 0:
        return "high"
    if counts.get("medium", 0) > 0:
        return "moderate"
    if counts.get("low", 0) > 0:
        return "low"
    if counts.get("info", 0) > 0:
        return "low"
    return "none"


def build_model_risk_diagnostics(
    comparison: dict[str, Any],
    selection: dict[str, Any] | None,
    *,
    project_root: Path,
    health: dict[str, Any] | None = None,
    robustness: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build model_risk_diagnostics_v1 from comparison and linked artifacts."""
    warnings: list[dict[str, Any]] = []
    by_id = _candidates_by_id(comparison)
    favored_id = (selection or {}).get("favored_candidate_id")
    baseline_id = _preferred_baseline_id(comparison, selection, by_id)
    focus_ids = {cid for cid in ("policy", baseline_id, favored_id) if cid}

    for run_w in comparison.get("warnings") or []:
        text = str(run_w)
        if "mixed_analysis" in text.lower():
            warnings.append(
                _warning_row(
                    "mixed_analysis_dates",
                    category="window_sensitivity",
                    severity="medium",
                    candidate_id=None,
                    source_artifact="candidate_comparison.json",
                    source_field="warnings",
                    code=text,
                    plain_english=(
                        "Candidates may use different analysis end dates; "
                        "compare metrics with caution."
                    ),
                )
            )

    for cid, cand in by_id.items():
        status = cand.get("status")
        if status == "degraded" and cid in focus_ids:
            warnings.append(
                _warning_row(
                    "candidate_degraded",
                    category="data_quality",
                    severity="medium",
                    candidate_id=cid,
                    source_artifact="candidate_comparison.json",
                    source_field="status",
                    plain_english=(
                        f"{cand.get('display_name', cid)} is marked degraded; "
                        "some inputs may be incomplete."
                    ),
                )
            )

        missing = cand.get("missing_fields") or []
        if "stress.overall" in missing or "stress" in str(missing):
            if cid in focus_ids:
                warnings.append(
                    _warning_row(
                        "stress_partial_coverage",
                        category="stress_coverage",
                        severity="medium",
                        candidate_id=cid,
                        source_artifact="candidate_comparison.json",
                        source_field="missing_fields",
                        plain_english=(
                            f"Stress summary is partial or missing for "
                            f"{cand.get('display_name', cid)}."
                        ),
                    )
                )

        mandate = cand.get("mandate") or {}
        if mandate.get("portfolio_valid") is False and cid in ("policy", favored_id):
            warnings.append(
                _warning_row(
                    "mandate_portfolio_invalid",
                    category="mandate",
                    severity="high",
                    candidate_id=cid,
                    source_artifact="candidate_comparison.json",
                    source_field="mandate.portfolio_valid",
                    plain_english=(
                        f"{cand.get('display_name', cid)} does not pass mandate validity checks."
                    ),
                )
            )

        wc = cand.get("weight_concentration") or {}
        top1_w = _finite(wc.get("top1_weight_pct"))
        if top1_w is not None:
            sev = _concentration_severity(top1_w, weight=True)
            if sev and cid in focus_ids:
                warnings.append(
                    _warning_row(
                        "concentration_weight_top1_high",
                        category="concentration",
                        severity=sev,
                        candidate_id=cid,
                        source_artifact="candidate_comparison.json",
                        source_field="weight_concentration.top1_weight_pct",
                        plain_english=(
                            f"Largest weight position is {_round3(top1_w * 100 if top1_w <= 1 else top1_w)}% "
                            f"on {cand.get('display_name', cid)}."
                        ),
                    )
                )

        div = cand.get("diversification") or {}
        top1_rc = _finite(div.get("top1_rc_pct"))
        if top1_rc is not None:
            sev = _concentration_severity(top1_rc, weight=False)
            if sev and cid in focus_ids:
                warnings.append(
                    _warning_row(
                        "concentration_rc_top1_high",
                        category="concentration",
                        severity=sev,
                        candidate_id=cid,
                        source_artifact="candidate_comparison.json",
                        source_field="diversification.top1_rc_pct",
                        plain_english=(
                            f"Top risk contributor accounts for a large share of "
                            f"variance on {cand.get('display_name', cid)}."
                        ),
                    )
                )

        stress = cand.get("stress") or {}
        if _stress_is_fail(stress.get("overall")) and cid in ("policy", favored_id):
            warnings.append(
                _warning_row(
                    "stress_fail_on_favored",
                    category="stress_coverage",
                    severity="high",
                    candidate_id=cid,
                    source_artifact="candidate_comparison.json",
                    source_field="stress.overall",
                    code=str(stress.get("overall")),
                    plain_english=(
                        f"Stress testing flags a fail status on {cand.get('display_name', cid)}."
                    ),
                )
            )

        for cand_warn in cand.get("warnings") or []:
            text = str(cand_warn)
            wid = f"upstream_{text[:48].lower().replace(' ', '_')}"
            warnings.append(
                _warning_row(
                    wid,
                    category="data_quality",
                    severity="low",
                    candidate_id=cid,
                    source_artifact="candidate_comparison.json",
                    source_field="warnings",
                    code=text,
                    plain_english=f"Comparison noted: {text}.",
                )
            )

        stress_report = _load_stress_report(cand, project_root)
        if stress_report:
            reg10 = stress_report.get("factor_regression_10y")
            if isinstance(reg10, dict):
                adj = _adj_r2_from_regression(reg10)
                if adj is not None and adj < 0.35 and cid in focus_ids:
                    warnings.append(
                        _warning_row(
                            "factor_adj_r2_low_10y",
                            category="factor_model",
                            severity="medium",
                            candidate_id=cid,
                            source_artifact="stress_report.json",
                            source_field="factor_regression_10y",
                            plain_english=(
                                f"10y factor model explains a limited share of returns "
                                f"(adjusted R² {_round3(adj)}) on {cand.get('display_name', cid)}."
                            ),
                        )
                    )
                mc = reg10.get("factor_multicollinearity") or {}
                sev_raw = str(mc.get("severity") or "").lower()
                if sev_raw in ("elevated", "severe") and cid in focus_ids:
                    warnings.append(
                        _warning_row(
                            "factor_multicollinearity_elevated",
                            category="factor_model",
                            severity="high" if sev_raw == "severe" else "medium",
                            candidate_id=cid,
                            source_artifact="stress_report.json",
                            source_field="factor_multicollinearity.severity",
                            plain_english=(
                                f"Factor exposures may be hard to separate "
                                f"({sev_raw} multicollinearity) on {cand.get('display_name', cid)}."
                            ),
                        )
                    )
            if stress_report.get("factor_betas_rolling_error") and cid in focus_ids:
                warnings.append(
                    _warning_row(
                        "factor_rolling_betas_error",
                        category="factor_model",
                        severity="medium",
                        candidate_id=cid,
                        source_artifact="stress_report.json",
                        source_field="factor_betas_rolling_error",
                        plain_english=(
                            f"Rolling factor betas could not be fully computed for "
                            f"{cand.get('display_name', cid)}."
                        ),
                    )
                )

        run_result = _load_run_result(cand, project_root)
        if run_result:
            for msg in run_result.get("warnings") or []:
                text = str(msg)
                if "WARN_MODEL_RISK_YOUNG_WEIGHT" in text and cid in focus_ids:
                    warnings.append(
                        _warning_row(
                            "young_etf_weight_warn",
                            category="data_quality",
                            severity="medium",
                            candidate_id=cid,
                            source_artifact="run_result.json",
                            code=text,
                            plain_english=(
                                "Young ETF history may limit reliability of risk estimates "
                                "for one or more holdings."
                            ),
                        )
                    )

    baseline = by_id.get(baseline_id or "")
    if not baseline:
        warning_id = (
            "analysis_subject_unavailable"
            if (selection or {}).get("baseline_candidate_id") == "analysis_subject"
            or comparison.get("comparison_baseline_candidate_id") == "analysis_subject"
            else "current_unavailable"
        )
        warnings.append(
            _warning_row(
                warning_id,
                category="selection_confidence",
                severity="low",
                candidate_id=None,
                source_artifact="candidate_comparison.json",
                plain_english=(
                    "Starting portfolio inputs are unavailable; baseline trade-off "
                    "and No-Trade context may be less grounded."
                ),
            )
        )

    if selection:
        for sw in selection.get("warnings") or []:
            text = str(sw)
            if "partial_score" in text.lower():
                warnings.append(
                    _warning_row(
                        "selection_partial_scores",
                        category="selection_confidence",
                        severity="medium",
                        candidate_id=None,
                        source_artifact="selection_decision.json",
                        code=text,
                        plain_english="Selection used partial score inputs for some candidates.",
                    )
                )
        if selection.get("decision_status") == "data_review_required":
            warnings.append(
                _warning_row(
                    "selection_data_review",
                    category="selection_confidence",
                    severity="high",
                    candidate_id=None,
                    source_artifact="selection_decision.json",
                    source_field="decision_status",
                    plain_english="Formal selection requires data review before acting on results.",
                )
            )

    if health and favored_id:
        for row in health.get("candidates", []):
            if row.get("candidate_id") == favored_id and row.get("score_status") == "not_scored":
                warnings.append(
                    _warning_row(
                        "health_not_scored_favored",
                        category="score_degradation",
                        severity="medium",
                        candidate_id=favored_id,
                        source_artifact="portfolio_health_score.json",
                        plain_english="Favored profile was not scored in the health scorecard.",
                    )
                )
    if robustness and favored_id:
        for row in robustness.get("candidates", []):
            if row.get("candidate_id") == favored_id and row.get("score_status") == "not_scored":
                warnings.append(
                    _warning_row(
                        "robustness_not_scored_favored",
                        category="score_degradation",
                        severity="medium",
                        candidate_id=favored_id,
                        source_artifact="robustness_scorecard.json",
                        plain_english="Favored profile was not scored in the robustness scorecard.",
                    )
                )

    warnings = _dedupe_warnings(warnings)
    counts = {s: 0 for s in ("high", "medium", "low", "info")}
    by_category: dict[str, dict[str, int]] = {}
    by_candidate: dict[str, list[str]] = {}

    for row in warnings:
        sev = str(row.get("severity") or "low")
        if sev in counts:
            counts[sev] += 1
        cat = str(row.get("category") or "data_quality")
        by_category.setdefault(cat, {s: 0 for s in ("high", "medium", "low", "info")})
        if sev in by_category[cat]:
            by_category[cat][sev] += 1
        cid = row.get("candidate_id")
        if cid:
            by_candidate.setdefault(str(cid), []).append(str(row.get("warning_id")))

    overall = _overall_severity(counts)
    high_med = [w for w in warnings if w.get("severity") in ("high", "medium")]
    if high_med:
        summary = (
            f"{counts.get('high', 0)} high-severity and {counts.get('medium', 0)} "
            f"medium-severity model-risk item(s) require review."
        )
    elif warnings:
        summary = "Model-risk flags are present but none are high severity."
    else:
        summary = "No material model-risk warnings were aggregated for this run."

    return {
        "schema_version": MODEL_RISK_SCHEMA,
        "diagnostic_only": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analysis_end": comparison.get("analysis_end"),
        "overall_severity": overall,
        "summary_plain_en": summary,
        "warning_count": counts,
        "warnings": warnings,
        "by_category": by_category,
        "by_candidate": by_candidate,
        "run_level_notes": [],
        "input_artifacts": {
            "candidate_comparison": "candidate_comparison.json",
            "selection_decision": "selection_decision.json" if selection else None,
            "portfolio_health_score": "portfolio_health_score.json" if health else None,
            "robustness_scorecard": "robustness_scorecard.json" if robustness else None,
        },
    }


def write_tradeoff_explanation_txt(doc: dict[str, Any], path: Path) -> None:
    lines = [
        "Trade-off explanation (non-executing, diagnostic only)",
        "=" * 60,
        f"Analysis end: {doc.get('analysis_end', '—')}",
        f"Status: {doc.get('tradeoff_status', '—')}",
        "",
    ]
    primary = next(
        (
            p
            for p in doc.get("pairs") or []
            if p.get("pair_id") in ("baseline_to_favored", "current_to_favored")
        ),
        None,
    )
    if primary:
        lines.append(
            f"Primary pair: {primary.get('baseline_display_name')} → "
            f"{primary.get('target_display_name')}"
        )
        lines.append("")
        lines.append("What improves")
        for dim_id in doc.get("improves") or []:
            dim = next(
                (d for d in primary.get("dimensions") or [] if d.get("dimension_id") == dim_id),
                None,
            )
            if dim:
                lines.append(f"  - {dim.get('plain_english')}")
        lines.append("")
        lines.append("What worsens")
        for dim_id in doc.get("worsens") or []:
            dim = next(
                (d for d in primary.get("dimensions") or [] if d.get("dimension_id") == dim_id),
                None,
            )
            if dim:
                lines.append(f"  - {dim.get('plain_english')}")
    else:
        lines.append("Primary baseline-to-favored pair not available.")
    lines.append("")
    lines.append("Cost of change")
    cost = doc.get("cost_of_change") or {}
    if cost.get("turnover_half_sum_pct") is not None:
        lines.append(f"  Turnover (half-sum): {cost['turnover_half_sum_pct']}%")
    for shift in cost.get("weight_shifts_top") or []:
        lines.append(f"  {shift.get('ticker')}: Δ {shift.get('delta_pct')}%")
    lines.append("")
    lines.append(f"Selection context: {doc.get('selection_decision_status', '—')}")
    lines.append("")
    lines.append("See tradeoff_explanation.json for secondary comparison pairs.")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def write_model_risk_diagnostics_txt(doc: dict[str, Any], path: Path) -> None:
    lines = [
        "Model risk diagnostics (diagnostic only)",
        "=" * 60,
        f"Analysis end: {doc.get('analysis_end', '—')}",
        f"Overall severity: {doc.get('overall_severity', '—')}",
        "",
        "Summary",
        doc.get("summary_plain_en", ""),
        "",
    ]
    for sev in ("high", "medium"):
        rows = [w for w in doc.get("warnings") or [] if w.get("severity") == sev]
        if not rows:
            continue
        lines.append(sev.capitalize())
        for row in rows:
            cid = row.get("candidate_id")
            prefix = f"[{cid}] " if cid else ""
            lines.append(f"  - {prefix}{row.get('plain_english')}")
        lines.append("")
    low_rows = [w for w in doc.get("warnings") or [] if w.get("severity") in ("low", "info")]
    if len(low_rows) <= 3:
        for row in low_rows:
            lines.append(f"  - {row.get('plain_english')}")
    elif low_rows:
        lines.append(f"({len(low_rows)} additional low/info items in JSON.)")
    lines.append("")
    lines.append("See model_risk_diagnostics.json for the full catalog.")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def write_tradeoff_and_model_risk_outputs(
    cfg: PortfolioConfig,
    *,
    project_root: Path | None = None,
    comparison: dict[str, Any] | None = None,
    selection: dict[str, Any] | None = None,
    health: dict[str, Any] | None = None,
    robustness: dict[str, Any] | None = None,
    write_txt: bool = True,
) -> dict[str, Path]:
    """Write trade-off and model-risk artifacts when comparison exists."""
    project_root = project_root or Path.cwd()
    out_dir = project_root / str(getattr(cfg, "output_dir_final", "Main portfolio"))

    if comparison is None:
        comparison = _load_json(out_dir / "candidate_comparison.json")
    if not comparison:
        return {}

    if selection is None:
        selection = _load_json(out_dir / "selection_decision.json")
    if health is None:
        health = _load_json(out_dir / "portfolio_health_score.json")
    if robustness is None:
        robustness = _load_json(out_dir / "robustness_scorecard.json")

    tradeoff = build_tradeoff_explanation(
        comparison,
        selection,
        project_root=project_root,
        health=health,
        robustness=robustness,
    )
    model_risk = build_model_risk_diagnostics(
        comparison,
        selection,
        project_root=project_root,
        health=health,
        robustness=robustness,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    tradeoff_json = out_dir / "tradeoff_explanation.json"
    with open(tradeoff_json, "w", encoding="utf-8") as f:
        json.dump(tradeoff, f, indent=2, ensure_ascii=False)
    paths["tradeoff_explanation_json"] = tradeoff_json

    model_json = out_dir / "model_risk_diagnostics.json"
    with open(model_json, "w", encoding="utf-8") as f:
        json.dump(model_risk, f, indent=2, ensure_ascii=False)
    paths["model_risk_diagnostics_json"] = model_json

    if write_txt:
        tradeoff_txt = out_dir / "tradeoff_explanation.txt"
        write_tradeoff_explanation_txt(tradeoff, tradeoff_txt)
        paths["tradeoff_explanation_txt"] = tradeoff_txt
        model_txt = out_dir / "model_risk_diagnostics.txt"
        write_model_risk_diagnostics_txt(model_risk, model_txt)
        paths["model_risk_diagnostics_txt"] = model_txt

    return paths


__all__ = [
    "TRADEOFF_SCHEMA",
    "MODEL_RISK_SCHEMA",
    "build_tradeoff_explanation",
    "build_model_risk_diagnostics",
    "write_tradeoff_and_model_risk_outputs",
    "write_tradeoff_explanation_txt",
    "write_model_risk_diagnostics_txt",
]
