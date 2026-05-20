"""
Regret Analysis — scenario opportunity loss vs best available candidate.

See docs/specs/regret_analysis_spec.md.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config_schema import PortfolioConfig
from src.selection_engine import ELIGIBLE_STATUSES, _finite, _load_json
from src.stress_artifacts import resolve_analysis_subject_stress_report_path

SCHEMA_VERSION = "regret_analysis_v1"


def _candidates_by_id(comparison: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {c["candidate_id"]: c for c in comparison.get("candidates", []) if c.get("candidate_id")}


def _round3(value: float) -> float:
    return round(float(value), 3)


def _is_evaluable(cand: dict[str, Any]) -> bool:
    return cand.get("status") in ELIGIBLE_STATUSES


def _scenario_pnls(cand: dict[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    stress = cand.get("stress") or {}
    for row in stress.get("scenarios") or []:
        if not isinstance(row, dict):
            continue
        sid = row.get("scenario_id")
        pnl = _finite(row.get("portfolio_pnl_pct"))
        if sid and pnl is not None:
            out[str(sid)] = _round3(pnl)
    return out


def _collect_scenario_ids(by_id: dict[str, dict[str, Any]], opportunity_ids: list[str]) -> list[str]:
    ids: set[str] = set()
    for cid in opportunity_ids:
        ids.update(_scenario_pnls(by_id[cid]).keys())
    return sorted(ids)


def _best_for_scenario(
    by_id: dict[str, dict[str, Any]],
    opportunity_ids: list[str],
    scenario_id: str,
) -> tuple[str | None, float | None, dict[str, float]]:
    pnls: dict[str, float] = {}
    for cid in opportunity_ids:
        pnl = _scenario_pnls(by_id[cid]).get(scenario_id)
        if pnl is not None:
            pnls[cid] = pnl
    if not pnls:
        return None, None, pnls
    best_pnl = max(pnls.values())
    best_id = min(cid for cid, v in pnls.items() if v == best_pnl)
    return best_id, best_pnl, pnls


def _rank_by_pnl(pnl: float, pnls: dict[str, float]) -> int:
    ordered = sorted(pnls.items(), key=lambda kv: (-kv[1], kv[0]))
    for i, (_, v) in enumerate(ordered, start=1):
        if v == pnl:
            return i
    return len(ordered) + 1


def _resolve_reference(
    reference_id: str,
    *,
    by_id: dict[str, dict[str, Any]],
    selection: dict[str, Any] | None,
) -> tuple[str | None, dict[str, Any] | None, str]:
    if reference_id == "favored":
        favored = (selection or {}).get("favored_candidate_id")
        if not favored:
            return None, None, "not_available"
        cand = by_id.get(favored)
        if not cand or not _is_evaluable(cand):
            return favored, cand, "not_available"
        return favored, cand, "complete"

    if reference_id == "current":
        for cand in by_id.values():
            if cand.get("role") == "user_current" and _is_evaluable(cand):
                return cand["candidate_id"], cand, "complete"
        return None, None, "not_available"

    if reference_id == "benchmark":
        for cand in by_id.values():
            if cand.get("role") == "benchmark" and _is_evaluable(cand):
                return cand["candidate_id"], cand, "complete"
        return None, None, "not_available"

    return None, None, "not_available"


def _reference_profile_row(
    reference_id: str,
    *,
    candidate_id: str | None,
    cand: dict[str, Any] | None,
    reference_status: str,
    scenario_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    regrets = [r["regret"] for r in scenario_rows if r.get("regret") is not None]
    worst_regret = max(regrets) if regrets else None
    worst_scenario_id = None
    if worst_regret is not None:
        for row in scenario_rows:
            if row.get("regret") == worst_regret:
                worst_scenario_id = row.get("scenario_id")
                break
    zero_count = sum(1 for r in scenario_rows if r.get("regret") == 0)
    partial = any(r.get("regret") is None for r in scenario_rows) and regrets
    status = reference_status
    if status == "complete" and partial:
        status = "partial_scenarios"
    return {
        "reference_id": reference_id,
        "candidate_id": candidate_id,
        "display_name": (cand or {}).get("display_name") if cand else None,
        "reference_status": status,
        "mean_regret": _round3(sum(regrets) / len(regrets)) if regrets else None,
        "worst_regret": _round3(worst_regret) if worst_regret is not None else None,
        "worst_scenario_id": worst_scenario_id,
        "scenarios_evaluated": len(regrets),
        "scenarios_with_zero_regret": zero_count,
        "scenario_rows": scenario_rows,
    }


def _metric_regret_slice(
    by_id: dict[str, Any],
    opportunity_ids: list[str],
    *,
    window: str,
    references: list[tuple[str, str | None, dict[str, Any] | None, str]],
) -> dict[str, Any]:
    cagrs: dict[str, float] = {}
    for cid in opportunity_ids:
        metrics = (by_id[cid].get("metrics") or {}).get(window) or {}
        cagr = _finite(metrics.get("cagr"))
        if cagr is not None:
            cagrs[cid] = _round3(cagr)
    if len(cagrs) < 2:
        return {"status": "insufficient_data"}
    best_cagr = max(cagrs.values())
    best_id = min(cid for cid, v in cagrs.items() if v == best_cagr)
    by_reference: dict[str, Any] = {}
    for ref_id, cid, _cand, ref_status in references:
        if ref_status != "complete" or not cid or cid not in cagrs:
            by_reference[ref_id] = {
                "cagr": None,
                "cagr_regret": None,
                "status": "not_available",
            }
            continue
        cagr_r = _round3(best_cagr - cagrs[cid])
        by_reference[ref_id] = {
            "cagr": cagrs[cid],
            "cagr_regret": cagr_r,
            "status": "complete",
        }
    return {
        "status": "complete",
        "informational_only": True,
        "primary_window": window,
        "cagr_best_candidate_id": best_id,
        "cagr_best": best_cagr,
        "by_reference": by_reference,
    }


def _try_regime_slices(
    *,
    project_root: Path,
    cfg: PortfolioConfig,
    by_id: dict[str, dict[str, Any]],
    opportunity_ids: list[str],
    references: list[tuple[str, str | None, dict[str, Any] | None, str]],
) -> tuple[str, list[dict[str, Any]], str | None]:
    output_dir_final = str(getattr(cfg, "output_dir_final", "Main portfolio"))
    subject_stress = resolve_analysis_subject_stress_report_path(
        project_root=project_root,
        output_dir_final=output_dir_final,
    )
    policy_folder = project_root / output_dir_final
    stress = _load_json(subject_stress) if subject_stress else _load_json(policy_folder / "stress_report.json")
    macro_diag = (stress or {}).get("macro_regime_diagnostics") or {}
    primary = macro_diag.get("current_regime") or macro_diag.get("primary_regime")
    if not primary:
        return (
            "not_available",
            [],
            "Macro regime regret requires projected regime PnL on comparison rows.",
        )

    regime_fields: list[tuple[str, str, dict[str, float]]] = []
    for cid in opportunity_ids:
        fr = by_id[cid].get("factor_regime") or {}
        macro = fr.get("macro_regime") if isinstance(fr.get("macro_regime"), dict) else {}
        slices = macro.get("regime_slices") or macro.get("portfolio_pnl_by_regime")
        if not isinstance(slices, list):
            continue
        pnls: dict[str, float] = {}
        for row in slices:
            if not isinstance(row, dict):
                continue
            rid = row.get("regime_id") or row.get("regime")
            pnl = _finite(row.get("portfolio_pnl_pct") or row.get("pnl_pct"))
            if rid and pnl is not None:
                pnls[str(rid)] = _round3(pnl)
        if pnls:
            regime_fields.append((cid, str(by_id[cid].get("display_name", cid)), pnls))

    if len(regime_fields) < 1:
        return (
            "not_available",
            [],
            "Macro regime regret requires projected regime PnL on comparison rows.",
        )

    regime_ids = sorted({rid for _, _, pnls in regime_fields for rid in pnls})
    slices_out: list[dict[str, Any]] = []
    for regime_id in regime_ids:
        pnls = {cid: m[regime_id] for cid, _, m in regime_fields if regime_id in m}
        if not pnls:
            continue
        best_pnl = max(pnls.values())
        best_id = min(cid for cid, v in pnls.items() if v == best_pnl)
        by_reference: dict[str, Any] = {}
        for ref_id, cid, _cand, ref_status in references:
            if ref_status != "complete" or not cid:
                by_reference[ref_id] = {"pnl": None, "regret": None}
                continue
            pnl = pnls.get(cid)
            regret = _round3(best_pnl - pnl) if pnl is not None else None
            by_reference[ref_id] = {
                "pnl": pnl,
                "regret": regret,
                "rank_by_pnl": _rank_by_pnl(pnl, pnls) if pnl is not None else None,
            }
        slices_out.append(
            {
                "regime_id": regime_id,
                "primary_regime_label": primary,
                "best_candidate_id": best_id,
                "best_pnl": best_pnl,
                "by_reference": by_reference,
            }
        )

    if not slices_out:
        return (
            "not_available",
            [],
            "Macro regime regret requires projected regime PnL on comparison rows.",
        )
    return "complete", slices_out, None


def _summary_plain_en(
    *,
    regret_status: str,
    reference_profiles: list[dict[str, Any]],
    scenario_count: int,
) -> str:
    if regret_status == "insufficient_candidates":
        return (
            "Regret analysis was not completed because fewer than one evaluable "
            "candidate was available in the comparison run."
        )
    if regret_status == "no_scenario_pnl":
        return (
            "Stress scenario regret was not computed because no scenario PnL "
            "was available on evaluable candidates."
        )
    favored = next((r for r in reference_profiles if r.get("reference_id") == "favored"), None)
    if favored and favored.get("worst_regret") is not None:
        name = favored.get("display_name") or favored.get("candidate_id") or "favored profile"
        worst = favored.get("worst_regret")
        sid = favored.get("worst_scenario_id") or "a stress scenario"
        return (
            f"Under the favored profile ({name}), worst stress regret versus the best "
            f"available candidate is {worst:.1%} in scenario {sid}."
        )
    current = next((r for r in reference_profiles if r.get("reference_id") == "current"), None)
    if current and current.get("worst_regret") is not None:
        worst = current.get("worst_regret")
        sid = current.get("worst_scenario_id") or "a stress scenario"
        return (
            f"Current portfolio stress regret versus the best available candidate peaks "
            f"at {worst:.1%} in scenario {sid} (informational)."
        )
    return (
        f"Stress regret was evaluated across {scenario_count} scenario(s) for available "
        "reference profiles; see regret_analysis.json for detail."
    )


def build_regret_analysis(
    comparison: dict[str, Any],
    *,
    selection: dict[str, Any] | None = None,
    pareto: dict[str, Any] | None = None,
    project_root: Path | None = None,
    cfg: PortfolioConfig | None = None,
) -> dict[str, Any]:
    """Build regret_analysis_v1 from candidate comparison."""
    project_root = project_root or Path.cwd()
    window = str(comparison.get("primary_window") or "10y")
    by_id = _candidates_by_id(comparison)
    opportunity_ids = sorted(cid for cid, cand in by_id.items() if _is_evaluable(cand))
    warnings: list[str] = []

    if not opportunity_ids:
        return {
            "schema_version": SCHEMA_VERSION,
            "diagnostic_only": True,
            "non_executing": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "analysis_end": comparison.get("analysis_end"),
            "primary_window": window,
            "regret_status": "insufficient_candidates",
            "opportunity_set_candidate_ids": [],
            "scenario_count": 0,
            "reference_profiles": [],
            "scenario_regret": [],
            "regime_regret_status": "not_available",
            "regime_slices": [],
            "regime_regret_note": (
                "Macro regime regret requires projected regime PnL on comparison rows."
            ),
            "metric_regret": {"status": "insufficient_data"},
            "summary_plain_en": _summary_plain_en(
                regret_status="insufficient_candidates",
                reference_profiles=[],
                scenario_count=0,
            ),
            "warnings": ["regret_insufficient_candidates"],
            "input_artifacts": {
                "candidate_comparison.json": "candidate_comparison.json",
                "selection_decision.json": (
                    "selection_decision.json" if selection is not None else None
                ),
                "pareto_dominance.json": (
                    "pareto_dominance.json" if pareto is not None else None
                ),
            },
        }

    scenario_ids = _collect_scenario_ids(by_id, opportunity_ids)
    has_any_pnl = False
    for sid in scenario_ids:
        _, best_pnl, _ = _best_for_scenario(by_id, opportunity_ids, sid)
        if best_pnl is not None:
            has_any_pnl = True
            break

    if not has_any_pnl:
        metric_regret = _metric_regret_slice(
            by_id,
            opportunity_ids,
            window=window,
            references=[],
        )
        return {
            "schema_version": SCHEMA_VERSION,
            "diagnostic_only": True,
            "non_executing": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "analysis_end": comparison.get("analysis_end"),
            "primary_window": window,
            "regret_status": "no_scenario_pnl",
            "opportunity_set_candidate_ids": opportunity_ids,
            "scenario_count": 0,
            "reference_profiles": [],
            "scenario_regret": [],
            "regime_regret_status": "not_available",
            "regime_slices": [],
            "regime_regret_note": (
                "Macro regime regret requires projected regime PnL on comparison rows."
            ),
            "metric_regret": metric_regret,
            "summary_plain_en": _summary_plain_en(
                regret_status="no_scenario_pnl",
                reference_profiles=[],
                scenario_count=0,
            ),
            "warnings": ["regret_no_scenario_pnl"],
            "input_artifacts": {
                "candidate_comparison.json": "candidate_comparison.json",
                "selection_decision.json": (
                    "selection_decision.json" if selection is not None else None
                ),
                "pareto_dominance.json": (
                    "pareto_dominance.json" if pareto is not None else None
                ),
            },
        }

    ref_specs = [
        _resolve_reference("favored", by_id=by_id, selection=selection),
        _resolve_reference("current", by_id=by_id, selection=selection),
        _resolve_reference("benchmark", by_id=by_id, selection=selection),
    ]

    scenario_regret: list[dict[str, Any]] = []
    ref_scenario_rows: dict[str, list[dict[str, Any]]] = {
        "favored": [],
        "current": [],
        "benchmark": [],
    }

    for sid in scenario_ids:
        best_id, best_pnl, pnls = _best_for_scenario(by_id, opportunity_ids, sid)
        if best_pnl is None:
            scenario_regret.append(
                {
                    "scenario_id": sid,
                    "status": "insufficient_data",
                    "best_candidate_id": None,
                    "best_pnl": None,
                    "by_reference": {},
                }
            )
            continue

        by_reference: dict[str, Any] = {}
        for ref_id, cid, _cand, ref_status in [
            ("favored", *ref_specs[0]),
            ("current", *ref_specs[1]),
            ("benchmark", *ref_specs[2]),
        ]:
            if ref_status == "not_available":
                by_reference[ref_id] = {"pnl": None, "regret": None, "rank_by_pnl": None}
                ref_scenario_rows[ref_id].append(
                    {"scenario_id": sid, "pnl": None, "regret": None}
                )
                continue
            pnl = pnls.get(cid) if cid else None
            regret = None
            rank = None
            if pnl is not None:
                regret = _round3(best_pnl - pnl)
                rank = _rank_by_pnl(pnl, pnls)
                if regret < 0:
                    warnings.append(
                        f"regret_negative_data_bug:{ref_id}:{sid}:{regret}"
                    )
            by_reference[ref_id] = {
                "pnl": pnl,
                "regret": regret,
                "rank_by_pnl": rank,
            }
            ref_scenario_rows[ref_id].append(
                {"scenario_id": sid, "pnl": pnl, "regret": regret}
            )

        scenario_regret.append(
            {
                "scenario_id": sid,
                "status": "complete",
                "best_candidate_id": best_id,
                "best_pnl": best_pnl,
                "by_reference": by_reference,
            }
        )

    reference_profiles: list[dict[str, Any]] = []
    for ref_id, cid, cand, ref_status in [
        ("favored", *ref_specs[0]),
        ("current", *ref_specs[1]),
        ("benchmark", *ref_specs[2]),
    ]:
        if ref_status == "not_available":
            reason = "no_favored_profile"
            if ref_id == "favored" and not (selection or {}).get("favored_candidate_id"):
                reason = "no_favored_profile"
            elif ref_id == "favored" and cid:
                reason = "favored_not_evaluable"
            else:
                reason = "not_available"
            reference_profiles.append(
                {
                    "reference_id": ref_id,
                    "candidate_id": cid,
                    "display_name": None,
                    "reference_status": "not_available",
                    "not_available_reason": reason,
                    "mean_regret": None,
                    "worst_regret": None,
                    "worst_scenario_id": None,
                    "scenarios_evaluated": 0,
                    "scenarios_with_zero_regret": 0,
                }
            )
            continue
        row = _reference_profile_row(
            ref_id,
            candidate_id=cid,
            cand=cand,
            reference_status=ref_status,
            scenario_rows=ref_scenario_rows[ref_id],
        )
        row.pop("scenario_rows", None)
        reference_profiles.append(row)

    regret_status = "complete"
    if any(r.get("reference_status") == "partial_scenarios" for r in reference_profiles):
        regret_status = "partial"

    regime_status = "not_available"
    regime_slices: list[dict[str, Any]] = []
    regime_note = (
        "Macro regime regret requires projected regime PnL on comparison rows."
    )
    if cfg is not None:
        regime_status, regime_slices, regime_note = _try_regime_slices(
            project_root=project_root,
            cfg=cfg,
            by_id=by_id,
            opportunity_ids=opportunity_ids,
            references=[
                ("favored", *ref_specs[0]),
                ("current", *ref_specs[1]),
                ("benchmark", *ref_specs[2]),
            ],
        )

    metric_regret = _metric_regret_slice(
        by_id,
        opportunity_ids,
        window=window,
        references=[
            ("favored", *ref_specs[0]),
            ("current", *ref_specs[1]),
            ("benchmark", *ref_specs[2]),
        ],
    )

    if pareto and pareto.get("non_dominated"):
        warnings.append("pareto_cross_reference_available")

    return {
        "schema_version": SCHEMA_VERSION,
        "diagnostic_only": True,
        "non_executing": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analysis_end": comparison.get("analysis_end"),
        "primary_window": window,
        "regret_status": regret_status,
        "opportunity_set_candidate_ids": opportunity_ids,
        "scenario_count": len([s for s in scenario_regret if s.get("status") == "complete"]),
        "reference_profiles": reference_profiles,
        "scenario_regret": scenario_regret,
        "regime_regret_status": regime_status,
        "regime_slices": regime_slices,
        "regime_regret_note": regime_note,
        "metric_regret": metric_regret,
        "summary_plain_en": _summary_plain_en(
            regret_status=regret_status,
            reference_profiles=reference_profiles,
            scenario_count=len(scenario_ids),
        ),
        "warnings": warnings,
        "input_artifacts": {
            "candidate_comparison.json": "candidate_comparison.json",
            "selection_decision.json": (
                "selection_decision.json" if selection is not None else None
            ),
            "pareto_dominance.json": (
                "pareto_dominance.json" if pareto is not None else None
            ),
        },
    }


def write_regret_analysis_txt(doc: dict[str, Any], path: Path) -> None:
    window = doc.get("primary_window", "10y")
    opp = doc.get("opportunity_set_candidate_ids") or []
    scenario_count = doc.get("scenario_count", 0)
    refs = doc.get("reference_profiles") or []

    lines = [
        "Regret Analysis (non-executing)",
        "=" * 72,
        f"Analysis end: {doc.get('analysis_end', '—')}   Primary window: {window}",
        "",
        "Scope",
        "-" * 40,
        f"  Opportunity set: {len(opp)} candidate(s); stress scenarios: {scenario_count}.",
        f"  Regret status: {doc.get('regret_status', '—')}.",
        f"  Reference profiles evaluated: "
        f"{sum(1 for r in refs if r.get('reference_status') == 'complete')}.",
        "",
        "Favored profile regret",
        "-" * 40,
    ]
    favored = next((r for r in refs if r.get("reference_id") == "favored"), None)
    if favored and favored.get("reference_status") == "complete":
        lines.append(
            f"  {favored.get('display_name', favored.get('candidate_id'))}: "
            f"mean regret {favored.get('mean_regret')}, worst {favored.get('worst_regret')} "
            f"({favored.get('worst_scenario_id', '—')})."
        )
    else:
        lines.append("  Favored reference not available.")

    lines.extend(["", "Current vs best", "-" * 40])
    current = next((r for r in refs if r.get("reference_id") == "current"), None)
    if current and current.get("reference_status") == "complete":
        lines.append(
            f"  {current.get('display_name', current.get('candidate_id'))}: "
            f"worst regret {current.get('worst_regret')} "
            f"({current.get('worst_scenario_id', '—')})."
        )
    else:
        lines.append("  Current reference not evaluable.")

    lines.extend(["", "Benchmark check", "-" * 40])
    bench = next((r for r in refs if r.get("reference_id") == "benchmark"), None)
    if bench and bench.get("reference_status") == "complete":
        lines.append(
            f"  {bench.get('display_name', bench.get('candidate_id'))}: "
            f"worst regret {bench.get('worst_regret')}."
        )
    else:
        lines.append("  Benchmark reference not available.")

    metric = doc.get("metric_regret") or {}
    if metric.get("status") == "complete":
        lines.extend(
            [
                "",
                "Primary-window CAGR regret (informational)",
                "-" * 40,
                f"  Best CAGR: {metric.get('cagr_best')} "
                f"({metric.get('cagr_best_candidate_id')}).",
            ]
        )

    lines.extend(
        [
            "",
            "Interpretation",
            "-" * 40,
            f"  {doc.get('summary_plain_en') or ''}",
            "  Stress regret uses historical scenario PnL from the comparison run; "
            "it is not a forecast and does not change selection.",
            "",
            "See regret_analysis.json for per-scenario detail.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def write_regret_analysis_outputs(
    cfg: PortfolioConfig,
    *,
    project_root: Path | None = None,
    comparison: dict[str, Any] | None = None,
    selection: dict[str, Any] | None = None,
    pareto: dict[str, Any] | None = None,
    write_txt: bool = True,
) -> dict[str, Path]:
    """Write regret analysis artifacts when comparison exists."""
    project_root = project_root or Path.cwd()
    out_dir = project_root / str(getattr(cfg, "output_dir_final", "Main portfolio"))

    if comparison is None:
        comparison = _load_json(out_dir / "candidate_comparison.json")
    if not comparison:
        return {}

    if selection is None:
        selection = _load_json(out_dir / "selection_decision.json")
    if pareto is None:
        pareto = _load_json(out_dir / "pareto_dominance.json")

    doc = build_regret_analysis(
        comparison,
        selection=selection,
        pareto=pareto,
        project_root=project_root,
        cfg=cfg,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    json_path = out_dir / "regret_analysis.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
    paths["regret_analysis_json"] = json_path

    if write_txt:
        txt_path = out_dir / "regret_analysis.txt"
        write_regret_analysis_txt(doc, txt_path)
        paths["regret_analysis_txt"] = txt_path

    return paths


__all__ = [
    "SCHEMA_VERSION",
    "build_regret_analysis",
    "write_regret_analysis_outputs",
    "write_regret_analysis_txt",
]
