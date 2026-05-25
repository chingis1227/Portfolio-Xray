"""Current-vs-candidate product comparison adapter.

This module projects the canonical multi-candidate comparison into a smaller
MVP view centered on the diagnosed baseline versus one selected candidate or a
shortlist. It does not alter ``candidate_comparison.json`` or selection logic.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

CURRENT_VS_CANDIDATE_VERSION = "current_vs_candidate_v1"
CURRENT_VS_CANDIDATE_FILENAME = "current_vs_candidate.json"


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


def _dimension_row(
    *,
    field: str,
    label: str,
    candidate: dict[str, Any],
    baseline: dict[str, Any],
    primary_window: str,
    lower_is_better: bool = False,
) -> dict[str, Any]:
    b = _metric_value(baseline, field, primary_window)
    c = _metric_value(candidate, field, primary_window)
    d = _delta(c, b)
    if d is None:
        direction = "unknown"
    elif abs(d) < 1e-12:
        direction = "flat"
    elif lower_is_better:
        direction = "improved" if c < b else "worse"
    else:
        direction = "improved" if c > b else "worse"
    return {
        "field": field,
        "label": label,
        "baseline_value": b,
        "candidate_value": c,
        "delta": d,
        "lower_is_better": lower_is_better,
        "direction": direction,
    }


def _comparison_row(
    *,
    candidate: dict[str, Any],
    baseline: dict[str, Any],
    primary_window: str,
) -> dict[str, Any]:
    dimensions = [
        _dimension_row(
            field="cagr",
            label="Return",
            candidate=candidate,
            baseline=baseline,
            primary_window=primary_window,
        ),
        _dimension_row(
            field="vol_annual",
            label="Volatility",
            candidate=candidate,
            baseline=baseline,
            primary_window=primary_window,
            lower_is_better=True,
        ),
        _dimension_row(
            field="max_drawdown",
            label="Max drawdown",
            candidate=candidate,
            baseline=baseline,
            primary_window=primary_window,
            lower_is_better=False,
        ),
        _dimension_row(
            field="sharpe",
            label="Sharpe",
            candidate=candidate,
            baseline=baseline,
            primary_window=primary_window,
        ),
    ]
    b_stress = _worst_stress_loss(baseline)
    c_stress = _worst_stress_loss(candidate)
    stress_delta = _delta(c_stress, b_stress)
    dimensions.append(
        {
            "field": "worst_stress_loss",
            "label": "Worst stress loss",
            "baseline_value": b_stress,
            "candidate_value": c_stress,
            "delta": stress_delta,
            "lower_is_better": False,
            "direction": "unknown"
            if stress_delta is None
            else "improved"
            if c_stress > b_stress
            else "worse"
            if c_stress < b_stress
            else "flat",
        }
    )
    return {
        "candidate_id": candidate.get("candidate_id"),
        "display_name": candidate.get("display_name"),
        "status": candidate.get("status"),
        "role": candidate.get("role"),
        "artifact_root": candidate.get("artifact_root"),
        "dimensions": dimensions,
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
) -> dict[str, Any]:
    """Project canonical comparison into current-vs-candidate view."""

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
                )
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
        "analysis_end": comparison.get("analysis_end"),
        "primary_window": primary_window,
        "view_mode": view_mode,
        "baseline": {
            "candidate_id": baseline.get("candidate_id") if baseline else baseline_id,
            "display_name": baseline.get("display_name") if baseline else None,
            "status": baseline.get("status") if baseline else None,
            "role": baseline.get("role") if baseline else None,
        },
        "selected_candidate_ids": list(selected),
        "comparisons": rows,
        "source_artifacts": {
            "candidate_comparison": "candidate_comparison.json",
            "selection_decision": "selection_decision.json" if selection else None,
        },
        "warnings": warnings,
    }


def write_current_vs_candidate_outputs(
    *,
    output_dir: str | Path,
    comparison: dict[str, Any],
    selection: dict[str, Any] | None = None,
    candidate_ids: Iterable[str] | None = None,
) -> dict[str, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    doc = build_current_vs_candidate(
        comparison,
        selection=selection,
        candidate_ids=candidate_ids,
    )
    path = out / CURRENT_VS_CANDIDATE_FILENAME
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False, default=str)
    return {"current_vs_candidate_json": path}
