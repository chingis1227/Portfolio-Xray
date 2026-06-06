"""Current-vs-candidate product comparison adapter.

This module projects the canonical multi-candidate comparison into a smaller
MVP view centered on the diagnosed baseline versus one selected candidate or a
shortlist. It does not alter ``candidate_comparison.json`` or selection logic.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

CURRENT_VS_CANDIDATE_VERSION = "current_vs_candidate_v1"
CURRENT_VS_CANDIDATE_FILENAME = "current_vs_candidate.json"
DEFAULT_TRANSACTION_COST_BPS = 10
DEFAULT_TRANSACTION_COST_MODEL = "bps_on_turnover_half_sum"

_MATERIALITY_THRESHOLDS: dict[str, float] = {
    "cagr": 0.005,
    "vol_annual": 0.005,
    "max_drawdown": 0.01,
    "sharpe": 0.05,
    "worst_stress_loss": 0.01,
    "weight_top1_weight_pct": 0.05,
    "weight_top3_weight_sum_pct": 0.05,
    "weight_hhi": 0.02,
    "rc_top1_rc_pct": 0.05,
    "rc_top3_rc_sum_pct": 0.05,
    "rc_hhi": 0.02,
    "beta_portfolio": 0.05,
}

_RISK_IMPACT_AREAS = frozenset(
    {
        "risk",
        "stress_risk",
        "concentration_risk",
        "risk_contribution",
        "factor_risk",
    }
)
_FACTOR_BETA_KEYS = (
    "beta_eq",
    "beta_rr",
    "beta_inf",
    "beta_credit",
    "beta_usd",
    "beta_cmd",
    "beta_vix",
    "beta_us_growth",
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _as_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _candidate_by_id(comparison: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("candidate_id")): row
        for row in comparison.get("candidates", [])
        if isinstance(row, dict) and row.get("candidate_id")
    }


def _baseline_id(comparison: dict[str, Any], by_id: dict[str, dict[str, Any]]) -> str | None:
    preferred = comparison.get("comparison_baseline_candidate_id")
    if preferred in by_id:
        return str(preferred)
    if "analysis_subject" in by_id:
        return "analysis_subject"
    if "current" in by_id:
        return "current"
    return None


def _selected_ids(
    comparison: dict[str, Any],
    selection: dict[str, Any] | None,
    candidate_ids: Iterable[str] | None,
    baseline_id: str | None,
) -> tuple[str, ...]:
    explicit = tuple(str(cid).strip() for cid in (candidate_ids or []) if str(cid).strip())
    if explicit:
        return explicit
    favored = (selection or {}).get("favored_candidate_id")
    if favored:
        return (str(favored),)
    rows = [
        row
        for row in comparison.get("candidates", [])
        if isinstance(row, dict)
        and row.get("candidate_id")
        and row.get("candidate_id") != baseline_id
        and row.get("status") == "available"
        and row.get("role") not in {"analysis_subject", "user_current", "policy"}
    ]
    return tuple(str(row["candidate_id"]) for row in rows[:1])


def _metric_value(row: dict[str, Any], field: str, primary_window: str) -> float | None:
    metrics = row.get("metrics")
    if isinstance(metrics, dict):
        window = metrics.get(primary_window)
        if isinstance(window, dict) and field in window:
            return _as_float(window.get(field))
        if field in metrics:
            return _as_float(metrics.get(field))
    if field == "max_drawdown":
        drawdown = row.get("drawdown")
        if isinstance(drawdown, dict):
            return _as_float(drawdown.get("max_drawdown"))
    return None


def _nested_float(row: dict[str, Any], section: str, field: str) -> float | None:
    block = row.get(section)
    if isinstance(block, dict):
        return _as_float(block.get(field))
    return None


def _factor_beta_value(row: dict[str, Any], beta_key: str) -> float | None:
    factor = row.get("factor_regime")
    if not isinstance(factor, dict):
        return None
    for block_key in ("factor_regression_10y", "factor_regression_5y"):
        block = factor.get(block_key)
        if not isinstance(block, dict):
            continue
        betas = block.get("betas")
        if isinstance(betas, dict):
            value = _as_float(betas.get(beta_key))
            if value is not None:
                return value
        value = _as_float(block.get(beta_key))
        if value is not None:
            return value
    return None


def _worst_stress_loss(row: dict[str, Any]) -> float | None:
    stress = row.get("stress")
    if not isinstance(stress, dict):
        return None
    values: list[float] = []
    for scenario in stress.get("scenarios") or []:
        if isinstance(scenario, dict):
            value = _as_float(scenario.get("portfolio_pnl_pct"))
            if value is not None:
                values.append(value)
    return min(values) if values else None


def _delta(candidate: float | None, baseline: float | None) -> float | None:
    if candidate is None or baseline is None:
        return None
    return candidate - baseline


def _direction_from_values(
    *,
    candidate_value: float | None,
    baseline_value: float | None,
    lower_is_better: bool,
) -> tuple[float | None, str]:
    d = _delta(candidate_value, baseline_value)
    if d is None:
        return None, "unknown"
    if abs(d) < 1e-12:
        return d, "flat"
    if lower_is_better:
        return d, "improved" if candidate_value < baseline_value else "worse"
    return d, "improved" if candidate_value > baseline_value else "worse"


def _materiality(field: str, delta: float | None) -> dict[str, Any]:
    threshold = _MATERIALITY_THRESHOLDS.get(field)
    if delta is None or threshold is None:
        return {
            "is_material": False,
            "threshold": threshold,
            "status": "unavailable" if delta is None else "not_assessed",
        }
    return {
        "is_material": abs(delta) >= threshold,
        "threshold": threshold,
        "status": "assessed",
    }


def _dimension_from_values(
    *,
    field: str,
    label: str,
    category: str,
    impact_area: str,
    baseline_value: float | None,
    candidate_value: float | None,
    lower_is_better: bool = False,
    comparison_basis: str = "candidate_minus_baseline",
) -> dict[str, Any]:
    delta, direction = _direction_from_values(
        candidate_value=candidate_value,
        baseline_value=baseline_value,
        lower_is_better=lower_is_better,
    )
    status = "available" if delta is not None else "unavailable"
    row = {
        "field": field,
        "label": label,
        "category": category,
        "impact_area": impact_area,
        "baseline_value": baseline_value,
        "candidate_value": candidate_value,
        "delta": delta,
        "lower_is_better": lower_is_better,
        "direction": direction,
        "status": status,
        "comparison_basis": comparison_basis,
        "materiality": _materiality(field, delta),
    }
    if status == "unavailable":
        row["unavailable_reason"] = "baseline_or_candidate_metric_missing"
    return row


def _dimension_row(
    *,
    field: str,
    label: str,
    candidate: dict[str, Any],
    baseline: dict[str, Any],
    primary_window: str,
    lower_is_better: bool = False,
    category: str = "risk_return",
    impact_area: str = "return",
) -> dict[str, Any]:
    b = _metric_value(baseline, field, primary_window)
    c = _metric_value(candidate, field, primary_window)
    return _dimension_from_values(
        field=field,
        label=label,
        category=category,
        impact_area=impact_area,
        baseline_value=b,
        candidate_value=c,
        lower_is_better=lower_is_better,
    )


def _weight_maps_from_row(row: dict[str, Any]) -> dict[str, float]:
    for key in ("weights", "final_weights_total"):
        raw = row.get(key)
        weights = _normalize_weights(raw)
        if weights:
            return weights
    concentration = row.get("weight_concentration")
    if isinstance(concentration, dict):
        for key in ("weights", "final_weights_total"):
            weights = _normalize_weights(concentration.get(key))
            if weights:
                return weights
    return {}


def _normalize_weights(raw: Any) -> dict[str, float]:
    if not isinstance(raw, Mapping):
        return {}
    weights: dict[str, float] = {}
    for ticker, value in raw.items():
        weight = _as_float(value)
        if ticker is None or weight is None:
            continue
        weights[str(ticker)] = weight
    return weights


def _turnover_half_sum(
    baseline_weights: Mapping[str, float],
    candidate_weights: Mapping[str, float],
) -> float | None:
    if not baseline_weights or not candidate_weights:
        return None
    keys = set(baseline_weights) | set(candidate_weights)
    return round(sum(abs(candidate_weights.get(k, 0.0) - baseline_weights.get(k, 0.0)) for k in keys) / 2.0, 6)


def _candidate_generation_candidate(
    candidate_generation: dict[str, Any] | None,
    candidate_id: str | None,
) -> dict[str, Any] | None:
    if not isinstance(candidate_generation, dict):
        return None
    candidate = candidate_generation.get("candidate")
    if not isinstance(candidate, dict):
        return None
    if candidate_id and str(candidate.get("candidate_id") or "") != str(candidate_id):
        return None
    return candidate


def candidate_generation_blocks_comparison(
    candidate_generation: dict[str, Any] | None,
    selected_candidate_ids: Iterable[str] | None = None,
) -> str | None:
    """Return a blocking reason when Block 7 evidence is not comparable."""

    if not isinstance(candidate_generation, dict):
        return "candidate_generation_missing"
    status = str(candidate_generation.get("generation_status") or "").strip()
    candidate = candidate_generation.get("candidate")
    if not isinstance(candidate, dict):
        return "candidate_generation_candidate_missing"
    candidate_id = str(candidate.get("candidate_id") or "").strip()
    weights = _normalize_weights(candidate.get("weights"))
    handoff = candidate_generation.get("handoff_to_comparison")
    can_compare = handoff.get("can_compare") if isinstance(handoff, Mapping) else None
    if status in {"failed", "infeasible"}:
        return f"candidate_generation_{status}"
    if status != "generated":
        return f"candidate_generation_not_generated:{status or 'missing'}"
    if not candidate_id:
        return "candidate_generation_candidate_id_missing"
    if not weights:
        return "candidate_generation_weights_missing"
    if can_compare is not True:
        return "candidate_generation_handoff_not_comparable"
    explicit = tuple(str(cid).strip() for cid in (selected_candidate_ids or ()) if str(cid).strip())
    if explicit and candidate_id not in explicit:
        return f"candidate_generation_candidate_id_mismatch:{candidate_id}!={','.join(explicit)}"
    return None


def _blocked_current_vs_candidate(
    *,
    comparison: dict[str, Any],
    candidate_generation: dict[str, Any] | None,
    requested_candidate_ids: Iterable[str] | None,
    reason: str,
) -> dict[str, Any]:
    candidate = (
        candidate_generation.get("candidate")
        if isinstance(candidate_generation, dict)
        else None
    )
    candidate_id = candidate.get("candidate_id") if isinstance(candidate, dict) else None
    return {
        "schema_version": CURRENT_VS_CANDIDATE_VERSION,
        "diagnostic_only": True,
        "generated_at": _utc_now_iso(),
        "analysis_end": comparison.get("analysis_end") if isinstance(comparison, dict) else None,
        "primary_window": str(comparison.get("primary_window") or "10y") if isinstance(comparison, dict) else "10y",
        "view_mode": "blocked",
        "comparison_status": "blocked_by_candidate_generation",
        "reason": reason,
        "baseline": {"candidate_id": None, "display_name": None, "status": None, "role": None},
        "requested_candidate_ids": list(requested_candidate_ids or ([candidate_id] if candidate_id else [])),
        "selected_candidate_ids": [],
        "comparisons": [],
        "candidate_lineage": {
            "candidate_id": candidate_id,
            "generation_status": candidate_generation.get("generation_status") if isinstance(candidate_generation, dict) else None,
            "can_compare": (
                (candidate_generation.get("handoff_to_comparison") or {}).get("can_compare")
                if isinstance(candidate_generation, dict)
                else None
            ),
        },
        "source_artifacts": {
            "candidate_comparison": "candidate_comparison.json" if isinstance(comparison, dict) else None,
            "selection_decision": None,
            "candidate_generation": "candidate_generation.json" if isinstance(candidate_generation, dict) else None,
        },
        "comparison_questions_answered": [],
        "warnings": [reason],
    }


def _transaction_cost_bps(generation_candidate: dict[str, Any] | None) -> tuple[float, str]:
    for container_name in ("parameters", "constraints"):
        container = (generation_candidate or {}).get(container_name)
        if isinstance(container, dict):
            value = _as_float(container.get("transaction_cost_bps"))
            if value is not None:
                return value, f"candidate_generation.candidate.{container_name}.transaction_cost_bps"
    return float(DEFAULT_TRANSACTION_COST_BPS), "action_engine_default"


def _practicality(
    *,
    candidate: dict[str, Any],
    baseline: dict[str, Any],
    generation_candidate: dict[str, Any] | None,
) -> dict[str, Any]:
    baseline_weights = _weight_maps_from_row(baseline)
    candidate_weights = _weight_maps_from_row(candidate)
    if not candidate_weights and isinstance(generation_candidate, dict):
        candidate_weights = _normalize_weights(generation_candidate.get("weights"))
    turnover = _turnover_half_sum(baseline_weights, candidate_weights)
    turnover_status = "available" if turnover is not None else "unavailable"
    bps, bps_source = _transaction_cost_bps(generation_candidate)
    estimated_cost = round(turnover * bps / 10000.0, 6) if turnover is not None else None
    return {
        "turnover_required": {
            "status": turnover_status,
            "turnover_half_sum_pct": turnover,
            "unavailable_reason": None
            if turnover is not None
            else "baseline_or_candidate_weights_missing",
            "source": "comparison_row_weights"
            if baseline_weights and candidate_weights
            else None,
        },
        "transaction_cost_assumption": {
            "status": "available",
            "transaction_cost_bps": bps,
            "transaction_cost_model": DEFAULT_TRANSACTION_COST_MODEL,
            "source": bps_source,
        },
        "estimated_transaction_cost_pct": estimated_cost,
    }


def _compact_dimension(dim: dict[str, Any]) -> dict[str, Any]:
    return {
        "field": dim.get("field"),
        "label": dim.get("label"),
        "category": dim.get("category"),
        "impact_area": dim.get("impact_area"),
        "delta": dim.get("delta"),
        "direction": dim.get("direction"),
        "is_material": (dim.get("materiality") or {}).get("is_material"),
    }


def _tradeoff_summary(dimensions: list[dict[str, Any]]) -> dict[str, Any]:
    available = [d for d in dimensions if d.get("status") == "available"]
    improved = [d for d in available if d.get("direction") == "improved"]
    worsened = [d for d in available if d.get("direction") == "worse"]
    similar = [d for d in available if d.get("direction") == "flat"]
    risk_reduced = [
        d
        for d in improved
        if str(d.get("impact_area") or "") in _RISK_IMPACT_AREAS
    ]
    risk_added = [
        d
        for d in worsened
        if str(d.get("impact_area") or "") in _RISK_IMPACT_AREAS
    ]
    unavailable = [d for d in dimensions if d.get("status") == "unavailable"]
    return {
        "what_improved": [_compact_dimension(d) for d in improved],
        "what_worsened": [_compact_dimension(d) for d in worsened],
        "what_stayed_similar": [_compact_dimension(d) for d in similar],
        "risk_reduced": [_compact_dimension(d) for d in risk_reduced],
        "risk_added": [_compact_dimension(d) for d in risk_added],
        "unavailable_metrics": [
            {
                "field": d.get("field"),
                "label": d.get("label"),
                "category": d.get("category"),
                "unavailable_reason": d.get("unavailable_reason"),
            }
            for d in unavailable
        ],
    }


def _criteria_target_field(text: str, dimensions_by_field: Mapping[str, dict[str, Any]]) -> str | None:
    t = text.lower()
    if any(word in t for word in ("stress", "tail", "crisis", "severe")):
        return "worst_stress_loss"
    if "drawdown" in t:
        return "max_drawdown"
    if "volatility" in t or " vol" in f" {t}":
        return "vol_annual"
    if "sharpe" in t:
        return "sharpe"
    if "return" in t or "cagr" in t:
        return "cagr"
    if "risk contribution" in t:
        for field in ("rc_top1_rc_pct", "rc_top3_rc_sum_pct", "rc_hhi"):
            if field in dimensions_by_field:
                return field
    if any(word in t for word in ("concentration", "largest holding", "top-3", "top3", "holding")):
        for field in ("weight_top1_weight_pct", "weight_top3_weight_sum_pct", "weight_hhi"):
            if field in dimensions_by_field:
                return field
    if "beta_eq" in t or "equity beta" in t:
        return "beta_eq" if "beta_eq" in dimensions_by_field else "beta_portfolio"
    if "credit" in t and "beta_credit" in dimensions_by_field:
        return "beta_credit"
    if ("rates" in t or "duration" in t) and "beta_rr" in dimensions_by_field:
        return "beta_rr"
    if ("vix" in t or "volatility spike" in t) and "beta_vix" in dimensions_by_field:
        return "beta_vix"
    if "beta" in t or "factor" in t:
        return "beta_portfolio"
    return None


def _success_criteria_result(
    *,
    criteria: Iterable[Any],
    dimensions: list[dict[str, Any]],
) -> dict[str, Any]:
    criteria_text = [str(item).strip() for item in criteria if str(item).strip()]
    if not criteria_text:
        return {"overall_status": "not_provided", "criteria": []}
    dimensions_by_field = {
        str(d.get("field")): d for d in dimensions if isinstance(d, dict) and d.get("field")
    }
    rows: list[dict[str, Any]] = []
    for criterion in criteria_text:
        field = _criteria_target_field(criterion, dimensions_by_field)
        if field is None:
            rows.append(
                {
                    "criterion": criterion,
                    "status": "not_evaluated",
                    "reason": "criterion_not_mapped_to_available_metric",
                    "metric_field": None,
                }
            )
            continue
        dim = dimensions_by_field.get(field)
        if not dim or dim.get("status") == "unavailable":
            rows.append(
                {
                    "criterion": criterion,
                    "status": "unavailable",
                    "reason": "mapped_metric_unavailable",
                    "metric_field": field,
                }
            )
            continue
        direction = dim.get("direction")
        status = (
            "met"
            if direction == "improved"
            else "not_met"
            if direction == "worse"
            else "similar"
            if direction == "flat"
            else "unavailable"
        )
        rows.append(
            {
                "criterion": criterion,
                "status": status,
                "reason": f"mapped_metric_direction:{direction}",
                "metric_field": field,
                "metric_delta": dim.get("delta"),
            }
        )
    statuses = {str(row.get("status")) for row in rows}
    if "not_met" in statuses and "met" in statuses:
        overall = "mixed"
    elif "not_met" in statuses:
        overall = "not_met"
    elif statuses == {"met"}:
        overall = "met"
    elif "met" in statuses:
        overall = "partially_met"
    elif statuses == {"similar"}:
        overall = "similar"
    elif statuses <= {"not_evaluated"}:
        overall = "not_evaluated"
    else:
        overall = "unavailable"
    return {"overall_status": overall, "criteria": rows}


def _materiality_for_decision_review(
    *,
    dimensions: list[dict[str, Any]],
    success_criteria_result: dict[str, Any],
) -> dict[str, Any]:
    available = [d for d in dimensions if d.get("status") == "available"]
    if not available:
        return {
            "status": "insufficient_evidence",
            "is_material_enough": False,
            "reason": "no_available_comparison_metrics",
            "supporting_improvements": [],
            "limiting_tradeoffs": [],
        }
    material_improvements = [
        d
        for d in available
        if d.get("direction") == "improved" and (d.get("materiality") or {}).get("is_material")
    ]
    material_worse = [
        d
        for d in available
        if d.get("direction") == "worse" and (d.get("materiality") or {}).get("is_material")
    ]
    success_status = str(success_criteria_result.get("overall_status") or "")
    if material_improvements and success_status != "not_met":
        status = "review_candidate"
        is_material_enough = True
        reason = "at_least_one_material_improvement_available"
    else:
        status = "not_material"
        is_material_enough = False
        reason = (
            "success_criteria_not_met"
            if success_status == "not_met"
            else "no_material_improvement_detected"
        )
    return {
        "status": status,
        "is_material_enough": is_material_enough,
        "reason": reason,
        "supporting_improvements": [_compact_dimension(d) for d in material_improvements],
        "limiting_tradeoffs": [_compact_dimension(d) for d in material_worse],
    }


def _comparison_row(
    *,
    candidate: dict[str, Any],
    baseline: dict[str, Any],
    primary_window: str,
    candidate_generation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    generation_candidate = _candidate_generation_candidate(
        candidate_generation,
        str(candidate.get("candidate_id") or ""),
    )
    dimensions = [
        _dimension_row(
            field="cagr",
            label="Return",
            candidate=candidate,
            baseline=baseline,
            primary_window=primary_window,
            category="risk_return",
            impact_area="return",
        ),
        _dimension_row(
            field="vol_annual",
            label="Volatility",
            candidate=candidate,
            baseline=baseline,
            primary_window=primary_window,
            lower_is_better=True,
            category="risk_return",
            impact_area="risk",
        ),
        _dimension_row(
            field="max_drawdown",
            label="Max drawdown",
            candidate=candidate,
            baseline=baseline,
            primary_window=primary_window,
            lower_is_better=False,
            category="risk_return",
            impact_area="risk",
        ),
        _dimension_row(
            field="sharpe",
            label="Sharpe",
            candidate=candidate,
            baseline=baseline,
            primary_window=primary_window,
            category="risk_return",
            impact_area="risk_adjusted_return",
        ),
    ]
    b_stress = _worst_stress_loss(baseline)
    c_stress = _worst_stress_loss(candidate)
    dimensions.append(
        _dimension_from_values(
            field="worst_stress_loss",
            label="Worst stress loss",
            category="stress",
            impact_area="stress_risk",
            baseline_value=b_stress,
            candidate_value=c_stress,
            lower_is_better=False,
        )
    )
    dimensions.extend(
        [
            _dimension_from_values(
                field="weight_top1_weight_pct",
                label="Largest holding weight",
                category="concentration",
                impact_area="concentration_risk",
                baseline_value=_nested_float(
                    baseline, "weight_concentration", "top1_weight_pct"
                ),
                candidate_value=_nested_float(
                    candidate, "weight_concentration", "top1_weight_pct"
                ),
                lower_is_better=True,
            ),
            _dimension_from_values(
                field="weight_top3_weight_sum_pct",
                label="Top-3 holding weight",
                category="concentration",
                impact_area="concentration_risk",
                baseline_value=_nested_float(
                    baseline, "weight_concentration", "top3_weight_sum_pct"
                ),
                candidate_value=_nested_float(
                    candidate, "weight_concentration", "top3_weight_sum_pct"
                ),
                lower_is_better=True,
            ),
            _dimension_from_values(
                field="weight_hhi",
                label="Weight concentration HHI",
                category="concentration",
                impact_area="concentration_risk",
                baseline_value=_nested_float(baseline, "weight_concentration", "weight_hhi"),
                candidate_value=_nested_float(candidate, "weight_concentration", "weight_hhi"),
                lower_is_better=True,
            ),
            _dimension_from_values(
                field="rc_top1_rc_pct",
                label="Largest risk contribution",
                category="concentration",
                impact_area="risk_contribution",
                baseline_value=_nested_float(baseline, "diversification", "top1_rc_pct"),
                candidate_value=_nested_float(candidate, "diversification", "top1_rc_pct"),
                lower_is_better=True,
            ),
            _dimension_from_values(
                field="rc_top3_rc_sum_pct",
                label="Top-3 risk contribution",
                category="concentration",
                impact_area="risk_contribution",
                baseline_value=_nested_float(baseline, "diversification", "top3_rc_sum_pct"),
                candidate_value=_nested_float(candidate, "diversification", "top3_rc_sum_pct"),
                lower_is_better=True,
            ),
            _dimension_from_values(
                field="rc_hhi",
                label="Risk contribution HHI",
                category="concentration",
                impact_area="risk_contribution",
                baseline_value=_nested_float(baseline, "diversification", "rc_hhi"),
                candidate_value=_nested_float(candidate, "diversification", "rc_hhi"),
                lower_is_better=True,
            ),
        ]
    )
    beta_baseline = _metric_value(baseline, "beta_portfolio", primary_window)
    beta_candidate = _metric_value(candidate, "beta_portfolio", primary_window)
    dimensions.append(
        _dimension_from_values(
            field="beta_portfolio",
            label="Portfolio beta exposure",
            category="factor_behavior",
            impact_area="factor_risk",
            baseline_value=abs(beta_baseline) if beta_baseline is not None else None,
            candidate_value=abs(beta_candidate) if beta_candidate is not None else None,
            lower_is_better=True,
            comparison_basis="absolute_exposure_change",
        )
    )
    for beta_key in _FACTOR_BETA_KEYS:
        b_beta = _factor_beta_value(baseline, beta_key)
        c_beta = _factor_beta_value(candidate, beta_key)
        if b_beta is None and c_beta is None:
            continue
        dimensions.append(
            _dimension_from_values(
                field=beta_key,
                label=f"{beta_key} absolute exposure",
                category="factor_behavior",
                impact_area="factor_risk",
                baseline_value=abs(b_beta) if b_beta is not None else None,
                candidate_value=abs(c_beta) if c_beta is not None else None,
                lower_is_better=True,
                comparison_basis="absolute_exposure_change",
            )
        )
    tradeoff_summary = _tradeoff_summary(dimensions)
    success_result = _success_criteria_result(
        criteria=(generation_candidate or {}).get("success_criteria") or [],
        dimensions=dimensions,
    )
    return {
        "candidate_id": candidate.get("candidate_id"),
        "display_name": candidate.get("display_name"),
        "status": candidate.get("status"),
        "role": candidate.get("role"),
        "artifact_root": candidate.get("artifact_root"),
        "dimensions": dimensions,
        "what_improved": tradeoff_summary["what_improved"],
        "what_worsened": tradeoff_summary["what_worsened"],
        "what_stayed_similar": tradeoff_summary["what_stayed_similar"],
        "risk_reduced": tradeoff_summary["risk_reduced"],
        "risk_added": tradeoff_summary["risk_added"],
        "practicality": _practicality(
            candidate=candidate,
            baseline=baseline,
            generation_candidate=generation_candidate,
        ),
        "success_criteria_result": success_result,
        "materiality_for_decision_review": _materiality_for_decision_review(
            dimensions=dimensions,
            success_criteria_result=success_result,
        ),
        "tradeoff_summary": tradeoff_summary,
        "data_quality": {
            "missing_fields": candidate.get("missing_fields") or [],
            "warnings": candidate.get("warnings") or [],
            "construction_disclosure_status": (
                (candidate.get("construction_disclosure") or {}).get("disclosure_status")
                if isinstance(candidate.get("construction_disclosure"), dict)
                else None
            ),
        },
        "source_files": candidate.get("source_files") or [],
    }


def build_current_vs_candidate(
    comparison: dict[str, Any],
    *,
    selection: dict[str, Any] | None = None,
    candidate_ids: Iterable[str] | None = None,
    candidate_generation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Project canonical comparison into current-vs-candidate view."""

    selected_for_guard = tuple(str(cid).strip() for cid in (candidate_ids or ()) if str(cid).strip())
    if candidate_generation is not None:
        blocked_reason = candidate_generation_blocks_comparison(
            candidate_generation,
            selected_for_guard,
        )
        if blocked_reason is not None:
            return _blocked_current_vs_candidate(
                comparison=comparison,
                candidate_generation=candidate_generation,
                requested_candidate_ids=selected_for_guard,
                reason=blocked_reason,
            )

    by_id = _candidate_by_id(comparison)
    baseline_id = _baseline_id(comparison, by_id)
    baseline = by_id.get(baseline_id or "")
    selected = _selected_ids(comparison, selection, candidate_ids, baseline_id)
    primary_window = str(comparison.get("primary_window") or "10y")
    warnings: list[str] = []
    rows: list[dict[str, Any]] = []
    if baseline is None:
        warnings.append("baseline_unavailable")
    for cid in selected:
        candidate = by_id.get(cid)
        if candidate is None:
            warnings.append(f"candidate_unavailable:{cid}")
            continue
        if baseline is not None:
            rows.append(
                _comparison_row(
                    candidate=candidate,
                    baseline=baseline,
                    primary_window=primary_window,
                    candidate_generation=candidate_generation,
                )
            )
    comparable_selected = tuple(
        str(row.get("candidate_id"))
        for row in rows
        if isinstance(row, dict) and row.get("candidate_id")
    )
    view_mode = (
        "diagnosis_only"
        if not rows
        else "one_candidate"
        if len(rows) == 1
        else "shortlist"
    )
    return {
        "schema_version": CURRENT_VS_CANDIDATE_VERSION,
        "diagnostic_only": True,
        "generated_at": _utc_now_iso(),
        "comparison_status": "available" if rows else "blocked_by_missing_comparison",
        "reason": None if rows else "no_comparable_candidate_rows",
        "analysis_end": comparison.get("analysis_end"),
        "primary_window": primary_window,
        "view_mode": view_mode,
        "baseline": {
            "candidate_id": baseline.get("candidate_id") if baseline else baseline_id,
            "display_name": baseline.get("display_name") if baseline else None,
            "status": baseline.get("status") if baseline else None,
            "role": baseline.get("role") if baseline else None,
        },
        "requested_candidate_ids": list(selected),
        "selected_candidate_ids": list(comparable_selected),
        "comparisons": rows,
        "candidate_lineage": {
            "candidate_id": comparable_selected[0] if comparable_selected else None,
            "generation_status": candidate_generation.get("generation_status") if isinstance(candidate_generation, dict) else None,
            "can_compare": (
                (candidate_generation.get("handoff_to_comparison") or {}).get("can_compare")
                if isinstance(candidate_generation, dict)
                else None
            ),
        },
        "source_artifacts": {
            "candidate_comparison": "candidate_comparison.json",
            "selection_decision": "selection_decision.json" if selection else None,
            "candidate_generation": "candidate_generation.json"
            if isinstance(candidate_generation, dict)
            else None,
        },
        "comparison_questions_answered": [
            "what_improved",
            "what_worsened",
            "what_stayed_similar",
            "risk_reduced",
            "risk_added",
            "turnover_required",
            "transaction_cost_assumption",
            "success_criteria_result",
            "materiality_for_decision_review",
        ],
        "warnings": warnings,
    }


def write_current_vs_candidate_outputs(
    *,
    output_dir: str | Path,
    comparison: dict[str, Any],
    selection: dict[str, Any] | None = None,
    candidate_ids: Iterable[str] | None = None,
    candidate_generation: dict[str, Any] | None = None,
) -> dict[str, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    doc = build_current_vs_candidate(
        comparison,
        selection=selection,
        candidate_ids=candidate_ids,
        candidate_generation=candidate_generation,
    )
    path = out / CURRENT_VS_CANDIDATE_FILENAME
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False, default=str)
    return {"current_vs_candidate_json": path}
