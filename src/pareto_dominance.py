"""
Pareto / Dominance Check — multi-criteria dominance among comparison candidates.

See docs/specs/pareto_dominance_spec.md.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config_schema import PortfolioConfig
from src.selection_engine import (
    ELIGIBLE_STATUSES,
    _finite,
    _load_json,
    _resolve_weights,
    _turnover_half_sum_pct,
)

SCHEMA_VERSION = "pareto_dominance_v1"

_OBJECTIVE_META: dict[str, dict[str, str]] = {
    "cagr": {"direction": "higher_better"},
    "vol_annual": {"direction": "lower_better"},
    "max_drawdown": {"direction": "higher_better"},
    "stress_worst_loss": {"direction": "higher_better"},
    "es_95": {"direction": "higher_better"},
    "turnover_vs_current": {"direction": "lower_better"},
}

_BASE_REQUIRED = ("cagr", "vol_annual", "max_drawdown")
_OPTIONAL_OBJECTIVES = ("es_95", "turnover_vs_current")


def _candidates_by_id(comparison: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {c["candidate_id"]: c for c in comparison.get("candidates", []) if c.get("candidate_id")}


def _round3(value: float) -> float:
    return round(float(value), 3)


def _stress_worst_loss(cand: dict[str, Any]) -> float | None:
    stress = cand.get("stress") or {}
    scenarios = stress.get("scenarios") or []
    losses: list[float] = []
    for row in scenarios:
        if not isinstance(row, dict):
            continue
        pnl = _finite(row.get("portfolio_pnl_pct"))
        if pnl is not None:
            losses.append(pnl)
    if not losses:
        abbreviated = _finite(stress.get("worst_portfolio_pnl_pct"))
        if abbreviated is not None:
            return abbreviated
        return None
    return max(losses)


def _max_drawdown_value(cand: dict[str, Any], window: str) -> float | None:
    metrics = (cand.get("metrics") or {}).get(window) or {}
    v = _finite(metrics.get("max_drawdown"))
    if v is not None:
        return v
    dd = cand.get("drawdown") or {}
    return _finite(dd.get("max_drawdown"))


def _extract_objectives(
    cand: dict[str, Any],
    *,
    window: str,
    turnover_vs_current: float | None,
) -> dict[str, float]:
    metrics = (cand.get("metrics") or {}).get(window) or {}
    out: dict[str, float] = {}
    cagr = _finite(metrics.get("cagr"))
    vol = _finite(metrics.get("vol_annual"))
    mdd = _max_drawdown_value(cand, window)
    if cagr is not None:
        out["cagr"] = _round3(cagr)
    if vol is not None:
        out["vol_annual"] = _round3(vol)
    if mdd is not None:
        out["max_drawdown"] = _round3(mdd)
    stress_loss = _stress_worst_loss(cand)
    if stress_loss is not None:
        out["stress_worst_loss"] = _round3(stress_loss)
    es = _finite(metrics.get("es_95"))
    if es is not None:
        out["es_95"] = _round3(es)
    if turnover_vs_current is not None:
        out["turnover_vs_current"] = _round3(turnover_vs_current)
    return out


def _missing_required(
    objectives: dict[str, float],
    required: tuple[str, ...],
) -> list[str]:
    return [oid for oid in required if oid not in objectives]


def _a_dominates_b(
    obj_a: dict[str, float],
    obj_b: dict[str, float],
    active: tuple[str, ...],
) -> tuple[bool, list[str], list[str]]:
    """Return (dominates, strict_objectives, objectives_skipped)."""
    strict: list[str] = []
    skipped: list[str] = []
    for oid in active:
        if oid not in obj_a or oid not in obj_b:
            skipped.append(oid)
            continue
        direction = _OBJECTIVE_META[oid]["direction"]
        va, vb = obj_a[oid], obj_b[oid]
        if direction == "higher_better":
            if va < vb:
                return False, [], skipped
            if va > vb:
                strict.append(oid)
        else:
            if va > vb:
                return False, [], skipped
            if va < vb:
                strict.append(oid)
    if not strict:
        return False, [], skipped
    return True, strict, skipped


def _pair_objectives(
    obj_a: dict[str, float],
    obj_b: dict[str, float],
    *,
    required: tuple[str, ...],
    optional: tuple[str, ...],
) -> tuple[tuple[str, ...] | None, list[str]]:
    """Active objectives for pair, or None if not comparable."""
    missing = _missing_required(obj_a, required) + _missing_required(obj_b, required)
    if missing:
        return None, sorted(set(missing))
    active = list(required)
    skipped: list[str] = []
    for oid in optional:
        if oid in obj_a and oid in obj_b:
            active.append(oid)
        else:
            skipped.append(f"{oid}_missing")
    return tuple(active), skipped


def _turnover_map(
    by_id: dict[str, dict[str, Any]],
    *,
    project_root: Path,
) -> dict[str, float]:
    current = by_id.get("current")
    if not current or current.get("status") not in ELIGIBLE_STATUSES:
        return {}
    w_current = _resolve_weights(current, project_root=project_root)
    if not w_current:
        return {}
    out: dict[str, float] = {}
    for cid, cand in by_id.items():
        if cid == "current" or cand.get("status") not in ELIGIBLE_STATUSES:
            continue
        w_cand = _resolve_weights(cand, project_root=project_root)
        if not w_cand:
            continue
        out[cid] = _turnover_half_sum_pct(w_cand, w_current)
    return out


def _any_evaluable_has_stress(by_id: dict[str, dict[str, Any]]) -> bool:
    for cand in by_id.values():
        if cand.get("status") not in ELIGIBLE_STATUSES:
            continue
        if _stress_worst_loss(cand) is not None:
            return True
    return False


def _evaluation_status(
    cand: dict[str, Any],
    objectives: dict[str, float],
    required: tuple[str, ...],
) -> str:
    if cand.get("status") not in ELIGIBLE_STATUSES:
        return "unavailable"
    if _missing_required(objectives, required):
        return "partial_objectives"
    return "complete"


def _summary_plain_en(
    *,
    non_dominated_count: int,
    dominated_count: int,
    favored_name: str | None,
    favored_is_dominated: bool,
    dominance_status: str,
) -> str:
    if dominance_status == "insufficient_candidates":
        return "Pareto dominance was not evaluated because fewer than two candidates had complete metrics."
    parts = [
        f"{non_dominated_count} candidate(s) are on the Pareto-efficient set; "
        f"{dominated_count} are dominated on return, risk, drawdown, and stress when applicable."
    ]
    if favored_name and favored_is_dominated:
        parts.append(
            f"The selection favorite ({favored_name}) is dominated by at least one alternative "
            "on the evaluated metrics; this does not change the selection record."
        )
    elif favored_name:
        parts.append(f"The selection favorite ({favored_name}) is not dominated on the evaluated metrics.")
    return " ".join(parts)


def build_pareto_dominance(
    comparison: dict[str, Any],
    *,
    selection: dict[str, Any] | None = None,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Build pareto_dominance_v1 from candidate comparison."""
    project_root = project_root or Path.cwd()
    window = str(comparison.get("primary_window") or "10y")
    by_id = _candidates_by_id(comparison)
    turnover_by_id = _turnover_map(by_id, project_root=project_root)

    required: list[str] = list(_BASE_REQUIRED)
    if _any_evaluable_has_stress(by_id):
        required.append("stress_worst_loss")
    required_tuple = tuple(required)

    objectives_by_id: dict[str, dict[str, float]] = {}
    eval_status_by_id: dict[str, str] = {}
    for cid, cand in by_id.items():
        objs = _extract_objectives(
            cand,
            window=window,
            turnover_vs_current=turnover_by_id.get(cid),
        )
        objectives_by_id[cid] = objs
        eval_status_by_id[cid] = _evaluation_status(cand, objs, required_tuple)

    evaluable_ids = [
        cid
        for cid, cand in by_id.items()
        if cand.get("status") in ELIGIBLE_STATUSES
        and eval_status_by_id[cid] == "complete"
    ]

    pairwise: list[dict[str, Any]] = []
    dominators_of: dict[str, list[dict[str, Any]]] = {cid: [] for cid in by_id}
    dominates_map: dict[str, list[dict[str, Any]]] = {cid: [] for cid in by_id}

    for dominator_id in evaluable_ids:
        for dominated_id in evaluable_ids:
            if dominator_id == dominated_id:
                continue
            active, skipped = _pair_objectives(
                objectives_by_id[dominator_id],
                objectives_by_id[dominated_id],
                required=required_tuple,
                optional=_OPTIONAL_OBJECTIVES,
            )
            if active is None:
                continue
            dominates, strict, pair_skipped = _a_dominates_b(
                objectives_by_id[dominator_id],
                objectives_by_id[dominated_id],
                active,
            )
            if not dominates:
                continue
            objectives_skipped = list(skipped) + list(pair_skipped)
            pairwise.append(
                {
                    "dominator_id": dominator_id,
                    "dominated_id": dominated_id,
                    "strict_objectives": strict,
                    "objectives_skipped": objectives_skipped,
                }
            )
            dom_cand = by_id[dominator_id]
            dom_row = {
                "candidate_id": dominator_id,
                "display_name": dom_cand.get("display_name", dominator_id),
                "strict_objectives": strict,
            }
            dominators_of[dominated_id].append(dom_row)
            dominated_cand = by_id[dominated_id]
            dominates_map[dominator_id].append(
                {
                    "candidate_id": dominated_id,
                    "display_name": dominated_cand.get("display_name", dominated_id),
                    "strict_objectives": strict,
                }
            )

    candidate_rows: list[dict[str, Any]] = []
    non_dominated_count = 0
    dominated_count = 0
    not_evaluated_count = 0

    for cid, cand in by_id.items():
        eval_status = eval_status_by_id[cid]
        if eval_status != "complete" or cid not in evaluable_ids:
            pareto_status = "not_evaluated"
            not_evaluated_count += 1
            dominance_note = None
        elif dominators_of[cid]:
            pareto_status = "dominated"
            dominated_count += 1
            top = dominators_of[cid][0]
            dominance_note = (
                f"Dominated by {top.get('display_name', top.get('candidate_id'))} "
                f"on {', '.join(top.get('strict_objectives') or [])}."
            )
        else:
            pareto_status = "non_dominated"
            non_dominated_count += 1
            dominance_note = None

        other_non_dom = sum(
            1
            for other_id in evaluable_ids
            if other_id != cid and not dominators_of[other_id]
        )

        candidate_rows.append(
            {
                "candidate_id": cid,
                "display_name": cand.get("display_name", cid),
                "status": cand.get("status"),
                "pareto_status": pareto_status,
                "evaluation_status": eval_status,
                "objectives": objectives_by_id.get(cid, {}),
                "dominated_by": dominators_of.get(cid, []),
                "dominates": dominates_map.get(cid, []),
                "non_dominated_alternatives_count": other_non_dom,
                "dominance_note": dominance_note,
            }
        )

    favored_id = (selection or {}).get("favored_candidate_id")
    favored_is_dominated = bool(
        favored_id and favored_id in dominators_of and dominators_of[favored_id]
    )
    favored_name = None
    if favored_id and favored_id in by_id:
        favored_name = str(by_id[favored_id].get("display_name", favored_id))

    if len(evaluable_ids) < 2:
        dominance_status = "insufficient_candidates"
    elif any(eval_status_by_id[cid] == "partial_objectives" for cid in by_id):
        dominance_status = "partial"
    else:
        dominance_status = "complete"

    warnings: list[str] = []
    if len(evaluable_ids) < 2:
        warnings.append("pareto_insufficient_evaluable_candidates")

    objectives_evaluated = list(required_tuple)
    objectives_optional = [oid for oid in _OPTIONAL_OBJECTIVES if oid != "turnover_vs_current"]
    if turnover_by_id:
        objectives_optional.append("turnover_vs_current")

    doc: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "diagnostic_only": True,
        "non_executing": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analysis_end": comparison.get("analysis_end"),
        "primary_window": window,
        "dominance_status": dominance_status,
        "objectives_evaluated": objectives_evaluated,
        "objectives_optional": objectives_optional,
        "evaluable_candidate_count": len(evaluable_ids),
        "non_dominated_count": non_dominated_count,
        "dominated_count": dominated_count,
        "not_evaluated_count": not_evaluated_count,
        "favored_candidate_id": favored_id,
        "favored_is_dominated": favored_is_dominated,
        "favored_dominance_note": (
            f"{favored_name} is dominated on evaluated metrics."
            if favored_is_dominated and favored_name
            else None
        ),
        "candidates": candidate_rows,
        "pairwise_dominance": pairwise,
        "summary_plain_en": _summary_plain_en(
            non_dominated_count=non_dominated_count,
            dominated_count=dominated_count,
            favored_name=favored_name,
            favored_is_dominated=favored_is_dominated,
            dominance_status=dominance_status,
        ),
        "warnings": warnings,
        "input_artifacts": {
            "candidate_comparison.json": "candidate_comparison.json",
            "selection_decision.json": (
                "selection_decision.json" if selection is not None else None
            ),
        },
    }
    return doc


def write_pareto_dominance_txt(doc: dict[str, Any], path: Path) -> None:
    window = doc.get("primary_window", "10y")
    objs = ", ".join(doc.get("objectives_evaluated") or [])
    optional = doc.get("objectives_optional") or []
    if optional:
        objs = f"{objs}; optional: {', '.join(optional)}"

    lines = [
        "Pareto / Dominance Check (non-executing)",
        "=" * 72,
        f"Analysis end: {doc.get('analysis_end', '—')}   Primary window: {window}",
        "",
        "Scope",
        "-" * 40,
        f"  Objectives: {objs}.",
        f"  Dominance status: {doc.get('dominance_status', '—')}.",
        "",
        "Efficient set",
        "-" * 40,
    ]
    non_dom = [
        c for c in doc.get("candidates", []) if c.get("pareto_status") == "non_dominated"
    ]
    if non_dom:
        for row in non_dom:
            lines.append(f"  - {row.get('display_name', row.get('candidate_id'))}")
    else:
        lines.append("  None with complete metrics.")
    lines.extend(["", "Dominated profiles", "-" * 40])
    dominated = [c for c in doc.get("candidates", []) if c.get("pareto_status") == "dominated"]
    if dominated:
        for row in dominated:
            note = row.get("dominance_note") or "Dominated on evaluated metrics."
            lines.append(f"  - {row.get('display_name', row.get('candidate_id'))}: {note}")
    else:
        lines.append("  None.")
    lines.extend(["", "Favored profile check", "-" * 40])
    favored = doc.get("favored_candidate_id")
    if favored:
        if doc.get("favored_is_dominated"):
            lines.append(
                f"  Selection favorite ({favored}) is dominated on evaluated metrics "
                "(informational only)."
            )
        else:
            lines.append(f"  Selection favorite ({favored}) is not dominated on evaluated metrics.")
    else:
        lines.append("  No selection favorite recorded.")
    lines.extend(
        [
            "",
            "Interpretation",
            "-" * 40,
            f"  {doc.get('summary_plain_en') or ''}",
            "",
            "See pareto_dominance.json for pairwise dominance detail.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def write_pareto_dominance_outputs(
    cfg: PortfolioConfig,
    *,
    project_root: Path | None = None,
    comparison: dict[str, Any] | None = None,
    selection: dict[str, Any] | None = None,
    write_txt: bool = True,
) -> dict[str, Path]:
    """Write Pareto dominance artifacts when comparison exists."""
    project_root = project_root or Path.cwd()
    out_dir = project_root / str(getattr(cfg, "output_dir_final", "Main portfolio"))

    if comparison is None:
        comparison = _load_json(out_dir / "candidate_comparison.json")
    if not comparison:
        return {}

    if selection is None:
        selection = _load_json(out_dir / "selection_decision.json")

    doc = build_pareto_dominance(
        comparison,
        selection=selection,
        project_root=project_root,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    json_path = out_dir / "pareto_dominance.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
    paths["pareto_dominance_json"] = json_path

    if write_txt:
        txt_path = out_dir / "pareto_dominance.txt"
        write_pareto_dominance_txt(doc, txt_path)
        paths["pareto_dominance_txt"] = txt_path

    return paths


__all__ = [
    "SCHEMA_VERSION",
    "build_pareto_dominance",
    "write_pareto_dominance_outputs",
    "write_pareto_dominance_txt",
]
