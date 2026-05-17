"""
Robustness Scorecard builder (diagnostic-only resilience scoring).

See docs/specs/robustness_scorecard_spec.md.
Distinct from src/robustness.py (optimizer weight stability).
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config_schema import PortfolioConfig

SCHEMA_VERSION = "robustness_scorecard_v1"
WEIGHTS_PROFILE = "default_weights_reviewable"
PRIMARY_WINDOW = "10y"

DEFAULT_WEIGHTS: dict[str, float] = {
    "downside_protection": 0.25,
    "stress_resilience": 0.20,
    "diversification_rc": 0.20,
    "return_efficiency": 0.15,
    "factor_stability": 0.10,
    "mandate_fit": 0.10,
}

COMPONENT_DISPLAY: dict[str, str] = {
    "downside_protection": "Downside protection",
    "stress_resilience": "Stress resilience",
    "diversification_rc": "Diversification / risk contribution",
    "return_efficiency": "Return efficiency",
    "factor_stability": "Factor stability",
    "mandate_fit": "Mandate fit",
}

STRESS_OVERALL_RANK: dict[str, float] = {
    "DIAG_PASS": 4.0,
    "PASS": 4.0,
    "DIAG_PASS_WITH_WARNING": 3.0,
    "PASS_WITH_WARNING": 3.0,
    "DIAG_ATTENTION": 2.0,
    "ATTENTION": 2.0,
}

SCORABLE_STATUSES = frozenset({"available", "degraded"})


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


def _rank_subscores(
    raw: dict[str, float | None],
    *,
    higher_is_better: bool,
) -> dict[str, float | None]:
    """Map raw values to 0–100 percentile sub-scores among finite values."""
    out: dict[str, float | None] = {k: None for k in raw}
    valid = {k: v for k, v in raw.items() if _finite(v) is not None}
    for k, v in list(valid.items()):
        valid[k] = float(v)  # type: ignore[arg-type]

    if not valid:
        return out
    if len(valid) == 1:
        cid = next(iter(valid))
        out[cid] = 50.0
        return out

    items = sorted(valid.items(), key=lambda x: (x[1], x[0]), reverse=higher_is_better)
    n = len(items)
    i = 0
    while i < n:
        j = i
        while j < n and items[j][1] == items[i][1]:
            j += 1
        avg_pos = (i + j - 1) / 2.0
        score = 100.0 * (1.0 - avg_pos / (n - 1)) if n > 1 else 50.0
        for k in range(i, j):
            out[items[k][0]] = score
        i = j
    return out


def _mean_subscores(sub: dict[str, float | None]) -> tuple[float | None, str, list[str]]:
    values = [v for v in sub.values() if v is not None]
    if not values:
        return None, "not_computed", ["no_sub_scores"]
    if len(values) < len([k for k, v in sub.items() if k]):
        status = "partial"
    else:
        status = "complete"
    return sum(values) / len(values), status, []


def _stress_overall_numeric(overall: Any) -> float | None:
    if overall is None:
        return None
    key = str(overall).strip()
    if key in STRESS_OVERALL_RANK:
        return STRESS_OVERALL_RANK[key]
    if key.startswith("DIAG_") or key.startswith("FAIL"):
        return 1.0
    return 2.0


def _resolve_stress_scenarios(
    cand: dict[str, Any],
    *,
    project_root: Path,
) -> tuple[list[dict[str, Any]], str]:
    """Return scenario rows and stress_inputs_source label."""
    stress = cand.get("stress") or {}
    scenarios = stress.get("scenarios")
    if isinstance(scenarios, list) and scenarios:
        comp_ids = {
            str(s.get("scenario_id"))
            for s in scenarios
            if isinstance(s, dict) and s.get("scenario_id")
        }
        if len(comp_ids) >= 6:
            return scenarios, "comparison"
        source = "partial"
    else:
        scenarios = []
        source = "comparison"

    artifact_root = cand.get("artifact_root")
    if not artifact_root:
        return scenarios, source if scenarios else "comparison"

    folder = Path(str(artifact_root))
    if not folder.is_absolute():
        folder = project_root / folder

    report = _load_json(folder / "stress_report.json")
    if not report:
        return scenarios, source if scenarios else "comparison"

    fallback_rows: list[dict[str, Any]] = []
    for row in report.get("scenario_results") or []:
        if not isinstance(row, dict):
            continue
        sid = row.get("scenario_id")
        if sid is None:
            continue
        fallback_rows.append(
            {
                "scenario_id": sid,
                "portfolio_pnl_pct": row.get("portfolio_pnl_pct"),
                "pass": row.get("pass"),
            }
        )

    if not fallback_rows:
        return scenarios, source if scenarios else "comparison"

    if not scenarios:
        return fallback_rows, "stress_report_fallback"

    by_id = {str(s.get("scenario_id")): s for s in scenarios if isinstance(s, dict)}
    for row in fallback_rows:
        sid = str(row["scenario_id"])
        if sid not in by_id:
            by_id[sid] = row
    merged = list(by_id.values())
    label = "stress_report_fallback" if len(merged) > len(scenarios) else source
    return merged, label


def _regression_adj_r2(block: dict[str, Any] | None) -> float | None:
    if not block:
        return None
    for key in ("adj_r_squared", "adj_r2", "r_squared_adj"):
        val = _finite(block.get(key))
        if val is not None:
            return val
    return None


def _beta_dispersion(block: dict[str, Any] | None) -> float | None:
    if not block:
        return None
    betas = block.get("betas") or block.get("factor_betas")
    if not isinstance(betas, dict):
        return None
    abs_vals = [_finite(v) for v in betas.values()]
    finite = [abs(abs(v)) for v in abs_vals if v is not None]
    if len(finite) < 2:
        return None
    return max(finite) - min(finite)


def _mandate_absolute_score(mandate: dict[str, Any]) -> tuple[float, list[str]]:
    warnings: list[str] = []
    if mandate.get("portfolio_valid") is False:
        warnings.append("mandate_portfolio_invalid")
        return 25.0, warnings

    cf = mandate.get("client_fit")
    if cf is True:
        score = 100.0
    elif cf is False:
        score = 0.0
    else:
        score = 50.0

    constraints = mandate.get("constraints_status")
    if isinstance(constraints, dict) and constraints:
        statuses = [str(v).upper() for v in constraints.values()]
        pass_rate = sum(1 for s in statuses if s == "PASS") / len(statuses)
        score = 0.5 * score + 0.5 * (pass_rate * 100.0)

    return score, warnings


def _scorable_candidates(comparison: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        c
        for c in comparison.get("candidates", [])
        if c.get("status") in SCORABLE_STATUSES
    ]


def _component_downside(
    scored: list[dict[str, Any]],
    primary: str,
) -> dict[str, dict[str, Any]]:
    raw_md: dict[str, float | None] = {}
    raw_vol: dict[str, float | None] = {}
    raw_sortino: dict[str, float | None] = {}
    raw_recovery: dict[str, float | None] = {}

    for cand in scored:
        cid = cand["candidate_id"]
        m = (cand.get("metrics") or {}).get(primary) or {}
        dd = cand.get("drawdown") or {}
        raw_md[cid] = _finite(m.get("max_drawdown"))
        raw_vol[cid] = _finite(m.get("vol_annual"))
        raw_sortino[cid] = _finite(m.get("sortino"))
        recovered = dd.get("recovered")
        ttr = _finite(dd.get("time_to_recovery_months"))
        if recovered is True:
            raw_recovery[cid] = 100.0 - (ttr if ttr is not None else 0.0)
        elif recovered is False:
            raw_recovery[cid] = 0.0
        else:
            raw_recovery[cid] = None

    sub_md = _rank_subscores(raw_md, higher_is_better=True)
    sub_vol = _rank_subscores(raw_vol, higher_is_better=False)
    sub_sortino = _rank_subscores(raw_sortino, higher_is_better=True)
    sub_recovery = _rank_subscores(raw_recovery, higher_is_better=True)

    out: dict[str, dict[str, Any]] = {}
    for cand in scored:
        cid = cand["candidate_id"]
        subs = {
            "max_drawdown": sub_md.get(cid),
            "vol_annual": sub_vol.get(cid),
            "sortino": sub_sortino.get(cid),
            "recovery": sub_recovery.get(cid),
        }
        score, status, missing = _mean_subscores(subs)
        out[cid] = {
            "score": round(score) if score is not None else None,
            "weight": DEFAULT_WEIGHTS["downside_protection"],
            "status": status,
            "sub_scores": {k: round(v, 1) if v is not None else None for k, v in subs.items()},
            "inputs_used": [k for k, v in subs.items() if v is not None],
            "missing_inputs": missing,
        }
    return out


def _component_stress(
    scored: list[dict[str, Any]],
    *,
    project_root: Path,
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    raw_overall: dict[str, float | None] = {}
    raw_mean_pnl: dict[str, float | None] = {}
    raw_worst_pnl: dict[str, float | None] = {}
    raw_pass_rate: dict[str, float | None] = {}
    stress_sources: dict[str, str] = {}

    for cand in scored:
        cid = cand["candidate_id"]
        stress = cand.get("stress") or {}
        raw_overall[cid] = _stress_overall_numeric(stress.get("overall"))
        scenarios, source = _resolve_stress_scenarios(cand, project_root=project_root)
        stress_sources[cid] = source

        pnls: list[float] = []
        passes = 0
        total_pass = 0
        for row in scenarios:
            if not isinstance(row, dict):
                continue
            pnl = _finite(row.get("portfolio_pnl_pct"))
            if pnl is not None:
                pnls.append(pnl)
            if row.get("pass") is True:
                passes += 1
            if row.get("pass") is not None:
                total_pass += 1

        raw_mean_pnl[cid] = sum(pnls) / len(pnls) if pnls else None
        raw_worst_pnl[cid] = max(pnls) if pnls else None
        raw_pass_rate[cid] = (passes / total_pass) if total_pass else None

    sub_overall = _rank_subscores(raw_overall, higher_is_better=True)
    sub_mean = _rank_subscores(raw_mean_pnl, higher_is_better=True)
    sub_worst = _rank_subscores(raw_worst_pnl, higher_is_better=True)
    sub_pass = _rank_subscores(raw_pass_rate, higher_is_better=True)

    out: dict[str, dict[str, Any]] = {}
    for cand in scored:
        cid = cand["candidate_id"]
        subs = {
            "stress_overall": sub_overall.get(cid),
            "mean_scenario_pnl": sub_mean.get(cid),
            "worst_scenario_pnl": sub_worst.get(cid),
            "scenario_pass_rate": sub_pass.get(cid),
        }
        score, status, missing = _mean_subscores(subs)
        out[cid] = {
            "score": round(score) if score is not None else None,
            "weight": DEFAULT_WEIGHTS["stress_resilience"],
            "status": status,
            "sub_scores": {k: round(v, 1) if v is not None else None for k, v in subs.items()},
            "inputs_used": [k for k, v in subs.items() if v is not None],
            "missing_inputs": missing,
            "stress_inputs_source": stress_sources.get(cid, "comparison"),
        }
    return out, stress_sources


def _component_diversification(scored: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    raw_top1: dict[str, float | None] = {}
    raw_top3: dict[str, float | None] = {}
    raw_hhi: dict[str, float | None] = {}

    for cand in scored:
        cid = cand["candidate_id"]
        div = cand.get("diversification") or {}
        raw_top1[cid] = _finite(div.get("top1_rc_pct"))
        raw_top3[cid] = _finite(div.get("top3_rc_sum_pct"))
        raw_hhi[cid] = _finite(div.get("rc_hhi"))

    sub_top1 = _rank_subscores(raw_top1, higher_is_better=False)
    sub_top3 = _rank_subscores(raw_top3, higher_is_better=False)
    sub_hhi = _rank_subscores(raw_hhi, higher_is_better=False)

    out: dict[str, dict[str, Any]] = {}
    for cand in scored:
        cid = cand["candidate_id"]
        div = cand.get("diversification") or {}
        if not div:
            out[cid] = {
                "score": None,
                "weight": DEFAULT_WEIGHTS["diversification_rc"],
                "status": "not_computed",
                "sub_scores": {},
                "inputs_used": [],
                "missing_inputs": ["diversification"],
            }
            continue

        subs: dict[str, float | None] = {
            "top1_rc_pct": sub_top1.get(cid),
            "top3_rc_sum_pct": sub_top3.get(cid),
        }
        if raw_hhi.get(cid) is not None:
            subs["rc_hhi"] = sub_hhi.get(cid)

        score, status, missing = _mean_subscores(subs)
        out[cid] = {
            "score": round(score) if score is not None else None,
            "weight": DEFAULT_WEIGHTS["diversification_rc"],
            "status": status,
            "sub_scores": {k: round(v, 1) if v is not None else None for k, v in subs.items()},
            "inputs_used": list(subs.keys()),
            "missing_inputs": missing,
        }
    return out


def _component_return_efficiency(
    scored: list[dict[str, Any]],
    primary: str,
) -> dict[str, dict[str, Any]]:
    raw_cagr: dict[str, float | None] = {}
    raw_sharpe: dict[str, float | None] = {}
    raw_sortino: dict[str, float | None] = {}
    raw_rpv: dict[str, float | None] = {}

    for cand in scored:
        cid = cand["candidate_id"]
        m = (cand.get("metrics") or {}).get(primary) or {}
        cagr = _finite(m.get("cagr"))
        vol = _finite(m.get("vol_annual"))
        raw_cagr[cid] = cagr
        raw_sharpe[cid] = _finite(m.get("sharpe"))
        raw_sortino[cid] = _finite(m.get("sortino"))
        if cagr is not None and vol is not None and vol > 0:
            raw_rpv[cid] = cagr / vol
        else:
            raw_rpv[cid] = None

    sub_cagr = _rank_subscores(raw_cagr, higher_is_better=True)
    sub_sharpe = _rank_subscores(raw_sharpe, higher_is_better=True)
    sub_sortino = _rank_subscores(raw_sortino, higher_is_better=True)
    sub_rpv = _rank_subscores(raw_rpv, higher_is_better=True)

    out: dict[str, dict[str, Any]] = {}
    for cand in scored:
        cid = cand["candidate_id"]
        subs = {
            "cagr": sub_cagr.get(cid),
            "sharpe": sub_sharpe.get(cid),
            "sortino": sub_sortino.get(cid),
            "return_per_vol": sub_rpv.get(cid),
        }
        score, status, missing = _mean_subscores(subs)
        out[cid] = {
            "score": round(score) if score is not None else None,
            "weight": DEFAULT_WEIGHTS["return_efficiency"],
            "status": status,
            "sub_scores": {k: round(v, 1) if v is not None else None for k, v in subs.items()},
            "inputs_used": [k for k, v in subs.items() if v is not None],
            "missing_inputs": missing,
        }
    return out


def _component_factor_stability(scored: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    raw_r2: dict[str, float | None] = {}
    raw_disp: dict[str, float | None] = {}

    for cand in scored:
        cid = cand["candidate_id"]
        fr = cand.get("factor_regime") or {}
        reg10 = fr.get("factor_regression_10y")
        if isinstance(reg10, dict):
            raw_r2[cid] = _regression_adj_r2(reg10)
            raw_disp[cid] = _beta_dispersion(reg10)
        else:
            raw_r2[cid] = None
            raw_disp[cid] = None

    sub_r2 = _rank_subscores(raw_r2, higher_is_better=True)
    sub_disp = _rank_subscores(raw_disp, higher_is_better=False)

    out: dict[str, dict[str, Any]] = {}
    for cand in scored:
        cid = cand["candidate_id"]
        subs: dict[str, float | None] = {"adj_r2_10y": sub_r2.get(cid)}
        if raw_disp.get(cid) is not None:
            subs["beta_dispersion"] = sub_disp.get(cid)
        score, status, missing = _mean_subscores(subs)
        out[cid] = {
            "score": round(score) if score is not None else None,
            "weight": DEFAULT_WEIGHTS["factor_stability"],
            "status": status,
            "sub_scores": {k: round(v, 1) if v is not None else None for k, v in subs.items()},
            "inputs_used": list(subs.keys()),
            "missing_inputs": missing,
        }
    return out


def _component_mandate_fit(scored: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    abs_scores: dict[str, float] = {}
    abs_warnings: dict[str, list[str]] = {}
    for cand in scored:
        cid = cand["candidate_id"]
        score, warns = _mandate_absolute_score(cand.get("mandate") or {})
        abs_scores[cid] = score
        abs_warnings[cid] = warns

    rel = _rank_subscores({k: v for k, v in abs_scores.items()}, higher_is_better=True)

    out: dict[str, dict[str, Any]] = {}
    for cand in scored:
        cid = cand["candidate_id"]
        blended = 0.5 * abs_scores[cid] + 0.5 * (rel.get(cid) or 50.0)
        if (cand.get("mandate") or {}).get("portfolio_valid") is False:
            blended = min(blended, 25.0)
        subs = {
            "absolute_mandate": round(abs_scores[cid], 1),
            "relative_mandate": round(rel.get(cid) or 50.0, 1),
        }
        out[cid] = {
            "score": round(blended),
            "weight": DEFAULT_WEIGHTS["mandate_fit"],
            "status": "complete",
            "sub_scores": subs,
            "inputs_used": list(subs.keys()),
            "missing_inputs": [],
            "warnings": abs_warnings.get(cid, []),
        }
    return out


def _total_score(
    components: dict[str, dict[str, Any]],
    *,
    skip_components: set[str],
) -> int | None:
    active: list[tuple[float, float]] = []
    for comp_id, weight in DEFAULT_WEIGHTS.items():
        if comp_id in skip_components:
            continue
        block = components.get(comp_id) or {}
        score = block.get("score")
        status = block.get("status")
        if status == "not_computed" or score is None:
            continue
        active.append((float(score), weight))

    if not active:
        return None
    w_sum = sum(w for _, w in active)
    total = sum(s * w / w_sum for s, w in active)
    return int(round(total))


def _weighted_contribution(
    components: dict[str, dict[str, Any]],
    *,
    skip_components: set[str],
) -> dict[str, float]:
    active_weights = {
        cid: w
        for cid, w in DEFAULT_WEIGHTS.items()
        if cid not in skip_components and (components.get(cid) or {}).get("score") is not None
    }
    w_sum = sum(active_weights.values()) or 1.0
    contrib: dict[str, float] = {}
    for cid, w in active_weights.items():
        score = float((components.get(cid) or {}).get("score") or 0)
        contrib[cid] = score * (w / w_sum)
    return contrib


def _explanation_bullets(
    *,
    display_name: str,
    total_score: int | None,
    rank: int | None,
    components: dict[str, dict[str, Any]],
    skip_components: set[str],
) -> list[str]:
    if total_score is None or rank is None:
        return ["Insufficient inputs for a robustness score in this comparison run."]

    bullets = [
        f"Ranks #{rank} in this comparison with a robustness score of {total_score}/100.",
    ]
    contrib = _weighted_contribution(components, skip_components=skip_components)
    ranked = sorted(
        ((cid, v) for cid, v in contrib.items() if cid not in skip_components),
        key=lambda x: (-x[1], x[0]),
    )
    for cid, _ in ranked[:2]:
        label = COMPONENT_DISPLAY.get(cid, cid)
        bullets.append(f"{label} is among the strongest contributors to the total score.")
    if ranked:
        weakest = ranked[-1][0]
        bullets.append(
            f"{COMPONENT_DISPLAY.get(weakest, weakest)} is the weakest component relative to peers."
        )
    return bullets[:4]


def build_robustness_scorecard(
    comparison: dict[str, Any],
    *,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Build scorecard document from canonical candidate_comparison.json content."""
    project_root = project_root or Path.cwd()
    primary = comparison.get("primary_window") or PRIMARY_WINDOW
    scored = _scorable_candidates(comparison)
    run_warnings: list[str] = []

    if len(scored) == 1:
        run_warnings.append("single_candidate_comparison")
    if not scored:
        run_warnings.append("no_scored_candidates")

    downside = _component_downside(scored, primary)
    stress, _stress_src = _component_stress(scored, project_root=project_root)
    diversification = _component_diversification(scored)
    return_eff = _component_return_efficiency(scored, primary)
    factor = _component_factor_stability(scored)
    mandate = _component_mandate_fit(scored)

    if any(
        (diversification.get(c["candidate_id"]) or {}).get("status") == "not_computed"
        for c in scored
    ):
        run_warnings.append("diversification_inputs_missing")

    candidate_scores: list[dict[str, Any]] = []

    for cand in comparison.get("candidates", []):
        cid = cand["candidate_id"]
        if cand.get("status") not in SCORABLE_STATUSES:
            candidate_scores.append(
                {
                    "candidate_id": cid,
                    "display_name": cand.get("display_name", cid),
                    "score_status": "not_scored",
                    "total_score": None,
                    "robustness_rank": None,
                    "components": {},
                    "explanation_bullets": [],
                    "warnings": [],
                }
            )
            continue

        components = {
            "downside_protection": downside.get(cid, {}),
            "stress_resilience": stress.get(cid, {}),
            "diversification_rc": diversification.get(cid, {}),
            "return_efficiency": return_eff.get(cid, {}),
            "factor_stability": factor.get(cid, {}),
            "mandate_fit": mandate.get(cid, {}),
        }
        skip_components: set[str] = set()
        if (diversification.get(cid) or {}).get("status") == "not_computed":
            skip_components.add("diversification_rc")
        total = _total_score(components, skip_components=skip_components)
        partial = any(
            (components[k] or {}).get("status") in ("partial", "not_computed")
            for k in components
        )
        score_status = "partial" if partial else "scored"
        if total is None:
            score_status = "partial"

        cand_warnings = list(cand.get("warnings") or [])
        for comp in components.values():
            cand_warnings.extend(comp.get("warnings") or [])

        candidate_scores.append(
            {
                "candidate_id": cid,
                "display_name": cand.get("display_name", cid),
                "score_status": score_status,
                "total_score": total,
                "robustness_rank": None,
                "components": components,
                "explanation_bullets": [],
                "warnings": sorted(set(cand_warnings)),
            }
        )

    rankable = [
        c
        for c in candidate_scores
        if c.get("score_status") in ("scored", "partial") and c.get("total_score") is not None
    ]
    rankable.sort(key=lambda x: (-int(x["total_score"]), x["candidate_id"]))
    for i, row in enumerate(rankable, start=1):
        row["robustness_rank"] = i
        row["explanation_bullets"] = _explanation_bullets(
            display_name=str(row["display_name"]),
            total_score=int(row["total_score"]),
            rank=i,
            components=row["components"],
            skip_components=skip_components,
        )

    scored_count = len(rankable)
    highest = rankable[0] if rankable else None
    scores = [int(c["total_score"]) for c in rankable]
    spread = (max(scores) - min(scores)) if len(scores) >= 2 else 0

    ranking_table = [
        {
            "candidate_id": c["candidate_id"],
            "display_name": c["display_name"],
            "total_score": c["total_score"],
            "robustness_rank": c["robustness_rank"],
        }
        for c in rankable
    ]

    doc: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "diagnostic_only": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "weights_profile": WEIGHTS_PROFILE,
        "weights": dict(DEFAULT_WEIGHTS),
        "primary_window": primary,
        "input_artifact": "candidate_comparison.json",
        "comparison_schema_version": comparison.get("schema_version"),
        "candidates": candidate_scores,
        "comparison_summary": {
            "scored_count": scored_count,
            "highest_robustness_candidate_id": highest["candidate_id"] if highest else None,
            "highest_robustness_display_name": highest["display_name"] if highest else None,
            "highest_total_score": highest["total_score"] if highest else None,
            "score_spread": spread,
            "ranking_table": ranking_table,
        },
        "warnings": run_warnings,
    }
    return doc


def write_robustness_scorecard_txt(scorecard: dict[str, Any], path: Path) -> None:
    primary = scorecard.get("primary_window") or PRIMARY_WINDOW
    lines = [
        f"Robustness Scorecard (diagnostic only) — primary window {primary}",
        f"Weights profile: {scorecard.get('weights_profile', WEIGHTS_PROFILE)}",
        "",
        f"{'Rank':>4}  {'Candidate':<40}  {'Score':>5}",
    ]
    for row in scorecard.get("comparison_summary", {}).get("ranking_table", []):
        lines.append(
            f"{row.get('robustness_rank', ''):>4}  "
            f"{row.get('display_name', ''):<40}  "
            f"{row.get('total_score', ''):>5}"
        )
    summary = scorecard.get("comparison_summary") or {}
    if summary.get("highest_robustness_display_name"):
        lines.extend(
            [
                "",
                (
                    f"Highest: {summary['highest_robustness_display_name']} — "
                    "see robustness_scorecard.json for component detail."
                ),
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def write_robustness_scorecard_outputs(
    cfg: PortfolioConfig,
    *,
    project_root: Path | None = None,
    comparison: dict[str, Any] | None = None,
    write_txt: bool = True,
) -> dict[str, Path]:
    project_root = project_root or Path.cwd()
    out_dir = project_root / str(getattr(cfg, "output_dir_final", "Main portfolio"))

    if comparison is None:
        json_path = out_dir / "candidate_comparison.json"
        if not json_path.is_file():
            raise FileNotFoundError(f"candidate_comparison.json not found: {json_path}")
        with open(json_path, encoding="utf-8") as f:
            comparison = json.load(f)

    scorecard = build_robustness_scorecard(comparison, project_root=project_root)
    out_dir.mkdir(parents=True, exist_ok=True)

    paths: dict[str, Path] = {}
    json_out = out_dir / "robustness_scorecard.json"
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(scorecard, f, indent=2, ensure_ascii=False)
    paths["robustness_scorecard_json"] = json_out

    if write_txt:
        txt_out = out_dir / "robustness_scorecard.txt"
        write_robustness_scorecard_txt(scorecard, txt_out)
        paths["robustness_scorecard_txt"] = txt_out

    return paths


__all__ = [
    "SCHEMA_VERSION",
    "DEFAULT_WEIGHTS",
    "build_robustness_scorecard",
    "write_robustness_scorecard_outputs",
    "write_robustness_scorecard_txt",
]
