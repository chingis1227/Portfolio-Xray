"""
Portfolio Health Score builder (diagnostic-only holistic quality scoring).

See docs/specs/portfolio_health_score_spec.md.
Distinct from src/robustness.py (optimizer weight stability).
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config_schema import PortfolioConfig

SCHEMA_VERSION = "portfolio_health_score_v1"
WEIGHTS_PROFILE = "default_weights_reviewable"
PRIMARY_WINDOW = "10y"
LEGACY_DISPLAY_PRIORITY = ("current", "policy")

DEFAULT_WEIGHTS: dict[str, float] = {
    "structural_diversification": 0.15,
    "weight_concentration": 0.10,
    "drawdown_resilience": 0.15,
    "stress_behavior": 0.10,
    "risk_adjusted_return": 0.14,
    "factor_balance": 0.09,
    "macro_regime_fit": 0.06,
    "liquidity_implementation": 0.05,
    "mandate_and_model_risk": 0.06,
    "resilience_reference": 0.10,
}

COMPONENT_DISPLAY: dict[str, str] = {
    "structural_diversification": "Structural diversification (RC)",
    "weight_concentration": "Weight concentration",
    "drawdown_resilience": "Drawdown resilience",
    "stress_behavior": "Stress behavior",
    "risk_adjusted_return": "Risk-adjusted return",
    "factor_balance": "Factor balance",
    "macro_regime_fit": "Macro regime fit",
    "liquidity_implementation": "Liquidity / implementation",
    "mandate_and_model_risk": "Mandate and model risk",
    "resilience_reference": "Resilience reference",
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
HIGH_SEVERITY_WARNING_MARKERS = (
    "data_quality",
    "missing_data",
    "stale_",
    "stress_summary_missing",
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


def _rank_subscores(
    raw: dict[str, float | None],
    *,
    higher_is_better: bool,
) -> dict[str, float | None]:
    out: dict[str, float | None] = {k: None for k in raw}
    valid = {k: float(v) for k, v in raw.items() if _finite(v) is not None}
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
    status = "partial" if len(values) < len(sub) else "complete"
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
) -> list[dict[str, Any]]:
    stress = cand.get("stress") or {}
    scenarios = stress.get("scenarios")
    if isinstance(scenarios, list) and scenarios:
        return [s for s in scenarios if isinstance(s, dict)]

    artifact_root = cand.get("artifact_root")
    if not artifact_root:
        return []

    folder = Path(str(artifact_root))
    if not folder.is_absolute():
        folder = project_root / folder

    report = _load_json(folder / "stress_report.json")
    if not report:
        return []

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
    return fallback_rows


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
    finite = [abs(v) for v in (_finite(x) for x in betas.values()) if v is not None]
    if len(finite) < 2:
        return None
    return max(finite) - min(finite)


def _mandate_absolute_score(mandate: dict[str, Any], warnings: list[str]) -> tuple[float, list[str]]:
    out_warnings: list[str] = []
    if mandate.get("portfolio_valid") is False:
        out_warnings.append("mandate_portfolio_invalid")
        base = 20.0
    else:
        cf = mandate.get("client_fit")
        if cf is True:
            base = 100.0
        elif cf is False:
            base = 0.0
        else:
            base = 50.0

        constraints = mandate.get("constraints_status")
        if isinstance(constraints, dict) and constraints:
            statuses = [str(v).upper() for v in constraints.values()]
            pass_rate = sum(1 for s in statuses if s == "PASS") / len(statuses)
            base = 0.5 * base + 0.5 * (pass_rate * 100.0)

    penalty = 0.0
    for w in warnings:
        wlow = str(w).lower()
        if any(m in wlow for m in HIGH_SEVERITY_WARNING_MARKERS):
            penalty += 10.0
    penalty = min(penalty, 30.0)
    return max(0.0, base - penalty), out_warnings


def _liquidity_absolute_from_folder(folder: Path) -> tuple[float | None, list[str]]:
    for name in ("run_metadata.json", "run_result.json"):
        doc = _load_json(folder / name)
        if not doc:
            continue
        for key in ("pro_liquidity_status", "proliquidity_status", "liquidity_status"):
            status = doc.get(key)
            if status is None and isinstance(doc.get("proliquidity"), dict):
                status = doc["proliquidity"].get("status")
            if status is None:
                continue
            norm = str(status).strip().lower()
            if norm in ("pass", "ok", "success"):
                return 100.0, []
            if norm in ("warn", "warning", "caution"):
                return 50.0, []
            if norm in ("fail", "failed", "error"):
                return 0.0, []
    return None, []


def _macro_fit_fields(macro: dict[str, Any] | None) -> tuple[float | None, float | None]:
    if not macro or not isinstance(macro, dict):
        return None, None
    fit = _finite(macro.get("portfolio_fit") or macro.get("regime_fit_score") or macro.get("fit_score"))
    conf = _finite(macro.get("regime_confidence") or macro.get("confidence"))
    return fit, conf


def _scorable_candidates(comparison: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        c
        for c in comparison.get("candidates", [])
        if c.get("status") in SCORABLE_STATUSES
    ]


def _robustness_totals_by_id(
    robustness: dict[str, Any] | None,
) -> dict[str, int | None]:
    if not robustness:
        return {}
    out: dict[str, int | None] = {}
    for row in robustness.get("candidates") or []:
        if not isinstance(row, dict):
            continue
        cid = row.get("candidate_id")
        if cid is None:
            continue
        ts = row.get("total_score")
        out[str(cid)] = int(ts) if ts is not None else None
    return out


def _component_structural_diversification(scored: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
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
        if not cand.get("diversification"):
            out[cid] = {
                "score": None,
                "weight": DEFAULT_WEIGHTS["structural_diversification"],
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
            "weight": DEFAULT_WEIGHTS["structural_diversification"],
            "status": status,
            "sub_scores": {k: round(v, 1) if v is not None else None for k, v in subs.items()},
            "inputs_used": list(subs.keys()),
            "missing_inputs": missing,
        }
    return out


def _component_weight_concentration(scored: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    raw_top1: dict[str, float | None] = {}
    raw_top3: dict[str, float | None] = {}
    raw_hhi: dict[str, float | None] = {}

    for cand in scored:
        cid = cand["candidate_id"]
        wc = cand.get("weight_concentration") or {}
        raw_top1[cid] = _finite(wc.get("top1_weight_pct"))
        raw_top3[cid] = _finite(wc.get("top3_weight_sum_pct"))
        raw_hhi[cid] = _finite(wc.get("weight_hhi"))

    sub_top1 = _rank_subscores(raw_top1, higher_is_better=False)
    sub_top3 = _rank_subscores(raw_top3, higher_is_better=False)
    sub_hhi = _rank_subscores(raw_hhi, higher_is_better=False)

    out: dict[str, dict[str, Any]] = {}
    for cand in scored:
        cid = cand["candidate_id"]
        if not cand.get("weight_concentration"):
            out[cid] = {
                "score": None,
                "weight": DEFAULT_WEIGHTS["weight_concentration"],
                "status": "not_computed",
                "sub_scores": {},
                "inputs_used": [],
                "missing_inputs": ["weight_concentration"],
            }
            continue
        subs: dict[str, float | None] = {
            "top1_weight_pct": sub_top1.get(cid),
            "top3_weight_sum_pct": sub_top3.get(cid),
        }
        if raw_hhi.get(cid) is not None:
            subs["weight_hhi"] = sub_hhi.get(cid)
        score, status, missing = _mean_subscores(subs)
        out[cid] = {
            "score": round(score) if score is not None else None,
            "weight": DEFAULT_WEIGHTS["weight_concentration"],
            "status": status,
            "sub_scores": {k: round(v, 1) if v is not None else None for k, v in subs.items()},
            "inputs_used": list(subs.keys()),
            "missing_inputs": missing,
        }
    return out


def _component_drawdown_resilience(
    scored: list[dict[str, Any]],
    primary: str,
) -> dict[str, dict[str, Any]]:
    raw_md: dict[str, float | None] = {}
    raw_recovery: dict[str, float | None] = {}

    for cand in scored:
        cid = cand["candidate_id"]
        m = (cand.get("metrics") or {}).get(primary) or {}
        dd = cand.get("drawdown") or {}
        raw_md[cid] = _finite(m.get("max_drawdown") if m.get("max_drawdown") is not None else dd.get("max_drawdown"))
        recovered = dd.get("recovered")
        ttr = _finite(dd.get("time_to_recovery_months"))
        if recovered is True:
            raw_recovery[cid] = 100.0 - (ttr if ttr is not None else 0.0)
        elif recovered is False:
            raw_recovery[cid] = 0.0
        else:
            raw_recovery[cid] = None

    sub_md = _rank_subscores(raw_md, higher_is_better=True)
    sub_recovery = _rank_subscores(raw_recovery, higher_is_better=True)

    out: dict[str, dict[str, Any]] = {}
    for cand in scored:
        cid = cand["candidate_id"]
        subs = {
            "max_drawdown": sub_md.get(cid),
            "recovery": sub_recovery.get(cid),
        }
        score, status, missing = _mean_subscores(subs)
        out[cid] = {
            "score": round(score) if score is not None else None,
            "weight": DEFAULT_WEIGHTS["drawdown_resilience"],
            "status": status,
            "sub_scores": {k: round(v, 1) if v is not None else None for k, v in subs.items()},
            "inputs_used": [k for k, v in subs.items() if v is not None],
            "missing_inputs": missing,
        }
    return out


def _component_stress_behavior(
    scored: list[dict[str, Any]],
    *,
    project_root: Path,
) -> dict[str, dict[str, Any]]:
    raw_overall: dict[str, float | None] = {}
    raw_worst_pnl: dict[str, float | None] = {}
    raw_pass_rate: dict[str, float | None] = {}

    for cand in scored:
        cid = cand["candidate_id"]
        stress = cand.get("stress") or {}
        raw_overall[cid] = _stress_overall_numeric(stress.get("overall"))
        scenarios = _resolve_stress_scenarios(cand, project_root=project_root)
        pnls: list[float] = []
        passes = 0
        total_pass = 0
        for row in scenarios:
            pnl = _finite(row.get("portfolio_pnl_pct"))
            if pnl is not None:
                pnls.append(pnl)
            if row.get("pass") is True:
                passes += 1
            if row.get("pass") is not None:
                total_pass += 1
        raw_worst_pnl[cid] = max(pnls) if pnls else None
        raw_pass_rate[cid] = (passes / total_pass) if total_pass else None

    sub_overall = _rank_subscores(raw_overall, higher_is_better=True)
    sub_worst = _rank_subscores(raw_worst_pnl, higher_is_better=True)
    sub_pass = _rank_subscores(raw_pass_rate, higher_is_better=True)

    out: dict[str, dict[str, Any]] = {}
    for cand in scored:
        cid = cand["candidate_id"]
        subs = {
            "stress_overall": sub_overall.get(cid),
            "worst_scenario_pnl": sub_worst.get(cid),
            "scenario_pass_rate": sub_pass.get(cid),
        }
        score, status, missing = _mean_subscores(subs)
        out[cid] = {
            "score": round(score) if score is not None else None,
            "weight": DEFAULT_WEIGHTS["stress_behavior"],
            "status": status,
            "sub_scores": {k: round(v, 1) if v is not None else None for k, v in subs.items()},
            "inputs_used": [k for k, v in subs.items() if v is not None],
            "missing_inputs": missing,
        }
    return out


def _component_risk_adjusted_return(
    scored: list[dict[str, Any]],
    primary: str,
) -> dict[str, dict[str, Any]]:
    raw_cagr: dict[str, float | None] = {}
    raw_sharpe: dict[str, float | None] = {}
    raw_sortino: dict[str, float | None] = {}

    for cand in scored:
        cid = cand["candidate_id"]
        m = (cand.get("metrics") or {}).get(primary) or {}
        raw_cagr[cid] = _finite(m.get("cagr"))
        raw_sharpe[cid] = _finite(m.get("sharpe"))
        raw_sortino[cid] = _finite(m.get("sortino"))

    sub_cagr = _rank_subscores(raw_cagr, higher_is_better=True)
    sub_sharpe = _rank_subscores(raw_sharpe, higher_is_better=True)
    sub_sortino = _rank_subscores(raw_sortino, higher_is_better=True)

    out: dict[str, dict[str, Any]] = {}
    for cand in scored:
        cid = cand["candidate_id"]
        subs = {
            "cagr": sub_cagr.get(cid),
            "sharpe": sub_sharpe.get(cid),
            "sortino": sub_sortino.get(cid),
        }
        score, status, missing = _mean_subscores(subs)
        out[cid] = {
            "score": round(score) if score is not None else None,
            "weight": DEFAULT_WEIGHTS["risk_adjusted_return"],
            "status": status,
            "sub_scores": {k: round(v, 1) if v is not None else None for k, v in subs.items()},
            "inputs_used": [k for k, v in subs.items() if v is not None],
            "missing_inputs": missing,
        }
    return out


def _component_factor_balance(scored: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
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
        subs: dict[str, float | None] = {}
        if raw_disp.get(cid) is not None:
            subs["beta_dispersion"] = sub_disp.get(cid)
        if raw_r2.get(cid) is not None:
            subs["adj_r2_10y"] = sub_r2.get(cid)
        if not subs:
            out[cid] = {
                "score": None,
                "weight": DEFAULT_WEIGHTS["factor_balance"],
                "status": "partial",
                "sub_scores": {},
                "inputs_used": [],
                "missing_inputs": ["factor_regression_10y"],
            }
            continue
        score, status, missing = _mean_subscores(subs)
        out[cid] = {
            "score": round(score) if score is not None else None,
            "weight": DEFAULT_WEIGHTS["factor_balance"],
            "status": status,
            "sub_scores": {k: round(v, 1) if v is not None else None for k, v in subs.items()},
            "inputs_used": list(subs.keys()),
            "missing_inputs": missing,
        }
    return out


def _component_macro_regime_fit(scored: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    raw_fit: dict[str, float | None] = {}
    raw_conf: dict[str, float | None] = {}

    for cand in scored:
        cid = cand["candidate_id"]
        fr = cand.get("factor_regime") or {}
        macro = fr.get("macro_regime") if isinstance(fr.get("macro_regime"), dict) else None
        fit, conf = _macro_fit_fields(macro)
        raw_fit[cid] = fit
        raw_conf[cid] = conf

    if not any(v is not None for v in raw_fit.values()) and not any(v is not None for v in raw_conf.values()):
        return {
            cand["candidate_id"]: {
                "score": None,
                "weight": DEFAULT_WEIGHTS["macro_regime_fit"],
                "status": "not_computed",
                "sub_scores": {},
                "inputs_used": [],
                "missing_inputs": ["macro_regime"],
            }
            for cand in scored
        }

    sub_fit = _rank_subscores(raw_fit, higher_is_better=True)
    sub_conf = _rank_subscores(raw_conf, higher_is_better=True)

    out: dict[str, dict[str, Any]] = {}
    for cand in scored:
        cid = cand["candidate_id"]
        subs: dict[str, float | None] = {}
        if raw_fit.get(cid) is not None:
            subs["regime_fit_score"] = sub_fit.get(cid)
        if raw_conf.get(cid) is not None:
            subs["regime_confidence"] = sub_conf.get(cid)
        if not subs:
            out[cid] = {
                "score": None,
                "weight": DEFAULT_WEIGHTS["macro_regime_fit"],
                "status": "not_computed",
                "sub_scores": {},
                "inputs_used": [],
                "missing_inputs": ["macro_regime"],
            }
            continue
        score, status, missing = _mean_subscores(subs)
        out[cid] = {
            "score": round(score) if score is not None else None,
            "weight": DEFAULT_WEIGHTS["macro_regime_fit"],
            "status": status,
            "sub_scores": {k: round(v, 1) if v is not None else None for k, v in subs.items()},
            "inputs_used": list(subs.keys()),
            "missing_inputs": missing,
        }
    return out


def _component_liquidity_implementation(
    scored: list[dict[str, Any]],
    *,
    project_root: Path,
) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    rel_raw: dict[str, float | None] = {}

    for cand in scored:
        cid = cand["candidate_id"]
        artifact_root = cand.get("artifact_root")
        abs_score: float | None = None
        if artifact_root:
            folder = Path(str(artifact_root))
            if not folder.is_absolute():
                folder = project_root / folder
            abs_score, _ = _liquidity_absolute_from_folder(folder)
        rel_raw[cid] = abs_score

    has_any = any(v is not None for v in rel_raw.values())
    rel_rank = _rank_subscores(rel_raw, higher_is_better=True) if has_any else {}

    for cand in scored:
        cid = cand["candidate_id"]
        abs_score = rel_raw.get(cid)
        if abs_score is None:
            out[cid] = {
                "score": None,
                "weight": DEFAULT_WEIGHTS["liquidity_implementation"],
                "status": "not_computed",
                "sub_scores": {},
                "inputs_used": [],
                "missing_inputs": ["liquidity_inputs"],
            }
            continue
        rel_part = rel_rank.get(cid) or 50.0
        blended = 0.6 * abs_score + 0.4 * rel_part
        out[cid] = {
            "score": round(blended),
            "weight": DEFAULT_WEIGHTS["liquidity_implementation"],
            "status": "complete",
            "sub_scores": {
                "absolute_liquidity": round(abs_score, 1),
                "relative_liquidity": round(rel_part, 1),
            },
            "inputs_used": ["pro_liquidity_status"],
            "missing_inputs": [],
        }
    return out


def _component_mandate_and_model_risk(scored: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    abs_scores: dict[str, float] = {}
    abs_warnings: dict[str, list[str]] = {}
    for cand in scored:
        cid = cand["candidate_id"]
        score, warns = _mandate_absolute_score(
            cand.get("mandate") or {},
            list(cand.get("warnings") or []),
        )
        abs_scores[cid] = score
        abs_warnings[cid] = warns

    rel = _rank_subscores({k: v for k, v in abs_scores.items()}, higher_is_better=True)

    out: dict[str, dict[str, Any]] = {}
    for cand in scored:
        cid = cand["candidate_id"]
        blended = 0.6 * abs_scores[cid] + 0.4 * (rel.get(cid) or 50.0)
        if (cand.get("mandate") or {}).get("portfolio_valid") is False:
            blended = min(blended, 20.0)
        subs = {
            "absolute_mandate": round(abs_scores[cid], 1),
            "relative_mandate": round(rel.get(cid) or 50.0, 1),
        }
        out[cid] = {
            "score": round(blended),
            "weight": DEFAULT_WEIGHTS["mandate_and_model_risk"],
            "status": "complete",
            "sub_scores": subs,
            "inputs_used": list(subs.keys()),
            "missing_inputs": [],
            "warnings": abs_warnings.get(cid, []),
        }
    return out


def _component_resilience_reference(
    scored: list[dict[str, Any]],
    robustness_totals: dict[str, int | None],
) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for cand in scored:
        cid = cand["candidate_id"]
        total = robustness_totals.get(cid)
        if total is None:
            out[cid] = {
                "score": None,
                "weight": DEFAULT_WEIGHTS["resilience_reference"],
                "status": "not_computed",
                "sub_scores": {},
                "inputs_used": [],
                "missing_inputs": ["robustness_total"],
            }
            continue
        out[cid] = {
            "score": int(total),
            "weight": DEFAULT_WEIGHTS["resilience_reference"],
            "status": "complete",
            "sub_scores": {"robustness_total": float(total)},
            "inputs_used": ["robustness_scorecard.total_score"],
            "missing_inputs": [],
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


def _top_drivers_drags(
    components: dict[str, dict[str, Any]],
    *,
    skip_components: set[str],
    peer_contribs: list[dict[str, float]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    contrib = _weighted_contribution(components, skip_components=skip_components)
    medians: dict[str, float] = {}
    for comp_id in DEFAULT_WEIGHTS:
        if comp_id in skip_components:
            continue
        vals = [c.get(comp_id, 0.0) for c in peer_contribs if comp_id in c]
        if vals:
            medians[comp_id] = sum(vals) / len(vals)

    deltas = []
    for comp_id, value in contrib.items():
        delta = value - medians.get(comp_id, value)
        deltas.append((comp_id, delta, value))

    deltas.sort(key=lambda x: (-x[1], x[0]))
    drivers = []
    for comp_id, delta, _ in deltas:
        if delta <= 0 or len(drivers) >= 2:
            continue
        drivers.append(
            {
                "component_id": comp_id,
                "direction": "positive",
                "label": (
                    f"{COMPONENT_DISPLAY.get(comp_id, comp_id)} ranks above peers in this comparison."
                ),
            }
        )

    drags_sorted = sorted(deltas, key=lambda x: (x[1], x[0]))
    drags = []
    for comp_id, delta, _ in drags_sorted:
        if delta >= 0 or len(drags) >= 2:
            continue
        drags.append(
            {
                "component_id": comp_id,
                "direction": "negative",
                "label": (
                    f"{COMPONENT_DISPLAY.get(comp_id, comp_id)} is a relative drag versus peers."
                ),
            }
        )
    return drivers, drags


def _explanation_bullets(
    *,
    display_name: str,
    total_score: int | None,
    rank: int | None,
    top_drivers: list[dict[str, Any]],
    top_drags: list[dict[str, Any]],
) -> list[str]:
    if total_score is None or rank is None:
        return ["Insufficient inputs for a portfolio health score in this comparison run."]

    bullets = [
        f"{display_name} ranks #{rank} in this comparison with a health score of {total_score}/100.",
    ]
    for item in top_drivers[:2]:
        bullets.append(item["label"])
    for item in top_drags[:2]:
        bullets.append(item["label"])
    return bullets[:5]


def build_portfolio_health_score(
    comparison: dict[str, Any],
    *,
    project_root: Path | None = None,
    robustness_scorecard: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build health score document from canonical candidate_comparison.json content."""
    project_root = project_root or Path.cwd()
    primary = comparison.get("primary_window") or PRIMARY_WINDOW
    scored = _scorable_candidates(comparison)
    run_warnings: list[str] = []

    if len(scored) == 1:
        run_warnings.append("single_candidate_comparison")
    if not scored:
        run_warnings.append("no_scored_candidates")

    if robustness_scorecard is None:
        run_warnings.append("robustness_scorecard_missing")

    robustness_totals = _robustness_totals_by_id(robustness_scorecard)

    structural = _component_structural_diversification(scored)
    weight_conc = _component_weight_concentration(scored)
    drawdown = _component_drawdown_resilience(scored, primary)
    stress = _component_stress_behavior(scored, project_root=project_root)
    risk_ret = _component_risk_adjusted_return(scored, primary)
    factor_bal = _component_factor_balance(scored)
    macro_fit = _component_macro_regime_fit(scored)
    liquidity = _component_liquidity_implementation(scored, project_root=project_root)
    mandate = _component_mandate_and_model_risk(scored)
    resilience = _component_resilience_reference(scored, robustness_totals)

    if any((structural.get(c["candidate_id"]) or {}).get("status") == "not_computed" for c in scored):
        run_warnings.append("diversification_inputs_missing")
    if any((weight_conc.get(c["candidate_id"]) or {}).get("status") == "not_computed" for c in scored):
        run_warnings.append("weight_concentration_inputs_missing")
    if not robustness_scorecard:
        if "robustness_scorecard_missing" not in run_warnings:
            run_warnings.append("robustness_scorecard_missing")
    if any((macro_fit.get(c["candidate_id"]) or {}).get("status") == "not_computed" for c in scored):
        run_warnings.append("macro_regime_missing")
    if any((liquidity.get(c["candidate_id"]) or {}).get("status") == "not_computed" for c in scored):
        run_warnings.append("liquidity_inputs_missing")

    skip_global: set[str] = set()
    if not robustness_scorecard or not any(v is not None for v in robustness_totals.values()):
        skip_global.add("resilience_reference")

    candidate_scores: list[dict[str, Any]] = []
    peer_contribs_by_id: dict[str, dict[str, float]] = {}

    for cand in comparison.get("candidates", []):
        cid = cand["candidate_id"]
        if cand.get("status") not in SCORABLE_STATUSES:
            candidate_scores.append(
                {
                    "candidate_id": cid,
                    "display_name": cand.get("display_name", cid),
                    "score_status": "not_scored",
                    "total_score": None,
                    "health_rank": None,
                    "components": {},
                    "top_drivers": [],
                    "top_drags": [],
                    "explanation_bullets": [],
                    "warnings": [],
                }
            )
            continue

        skip = set(skip_global)
        if (structural.get(cid) or {}).get("status") == "not_computed":
            skip.add("structural_diversification")
        if (weight_conc.get(cid) or {}).get("status") == "not_computed":
            skip.add("weight_concentration")
        if (macro_fit.get(cid) or {}).get("status") == "not_computed":
            skip.add("macro_regime_fit")
        if (liquidity.get(cid) or {}).get("status") == "not_computed":
            skip.add("liquidity_implementation")
        if (resilience.get(cid) or {}).get("status") == "not_computed":
            skip.add("resilience_reference")

        components = {
            "structural_diversification": structural.get(cid, {}),
            "weight_concentration": weight_conc.get(cid, {}),
            "drawdown_resilience": drawdown.get(cid, {}),
            "stress_behavior": stress.get(cid, {}),
            "risk_adjusted_return": risk_ret.get(cid, {}),
            "factor_balance": factor_bal.get(cid, {}),
            "macro_regime_fit": macro_fit.get(cid, {}),
            "liquidity_implementation": liquidity.get(cid, {}),
            "mandate_and_model_risk": mandate.get(cid, {}),
            "resilience_reference": resilience.get(cid, {}),
        }
        total = _total_score(components, skip_components=skip)
        partial = any(
            (components[k] or {}).get("status") in ("partial", "not_computed") for k in components
        )
        score_status = "partial" if partial else "scored"
        if total is None:
            score_status = "partial"

        cand_warnings = list(cand.get("warnings") or [])
        for comp in components.values():
            cand_warnings.extend(comp.get("warnings") or [])

        peer_contribs_by_id[cid] = _weighted_contribution(components, skip_components=skip)

        candidate_scores.append(
            {
                "candidate_id": cid,
                "display_name": cand.get("display_name", cid),
                "score_status": score_status,
                "total_score": total,
                "health_rank": None,
                "components": components,
                "top_drivers": [],
                "top_drags": [],
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

    peer_for_rank = [peer_contribs_by_id[c["candidate_id"]] for c in rankable if c["candidate_id"] in peer_contribs_by_id]

    for i, row in enumerate(rankable, start=1):
        row["health_rank"] = i
        skip = skip_global.copy()
        comps = row["components"]
        if (comps.get("structural_diversification") or {}).get("status") == "not_computed":
            skip.add("structural_diversification")
        if (comps.get("weight_concentration") or {}).get("status") == "not_computed":
            skip.add("weight_concentration")
        if (comps.get("macro_regime_fit") or {}).get("status") == "not_computed":
            skip.add("macro_regime_fit")
        if (comps.get("liquidity_implementation") or {}).get("status") == "not_computed":
            skip.add("liquidity_implementation")
        if (comps.get("resilience_reference") or {}).get("status") == "not_computed":
            skip.add("resilience_reference")
        drivers, drags = _top_drivers_drags(comps, skip_components=skip, peer_contribs=peer_for_rank)
        row["top_drivers"] = drivers
        row["top_drags"] = drags
        row["explanation_bullets"] = _explanation_bullets(
            display_name=str(row["display_name"]),
            total_score=int(row["total_score"]),
            rank=i,
            top_drivers=drivers,
            top_drags=drags,
        )

    scored_count = len(rankable)
    highest = rankable[0] if rankable else None
    scores = [int(c["total_score"]) for c in rankable]
    spread = (max(scores) - min(scores)) if len(scores) >= 2 else 0

    by_id = {c["candidate_id"]: c for c in rankable}
    policy_score = (by_id.get("policy") or {}).get("total_score")
    current_score = (by_id.get("current") or {}).get("total_score")
    if (by_id.get("analysis_subject") or {}).get("total_score") is not None:
        display_priority = ["analysis_subject"]
    else:
        display_priority = list(LEGACY_DISPLAY_PRIORITY)

    ranking_table = [
        {
            "candidate_id": c["candidate_id"],
            "display_name": c["display_name"],
            "total_score": c["total_score"],
            "health_rank": c["health_rank"],
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
        "input_artifacts": {
            "candidate_comparison": "candidate_comparison.json",
            "robustness_scorecard": "robustness_scorecard.json",
        },
        "comparison_schema_version": comparison.get("schema_version"),
        "robustness_schema_version": (
            robustness_scorecard.get("schema_version") if robustness_scorecard else None
        ),
        "display_priority": display_priority,
        "candidates": candidate_scores,
        "comparison_summary": {
            "scored_count": scored_count,
            "highest_health_candidate_id": highest["candidate_id"] if highest else None,
            "highest_health_display_name": highest["display_name"] if highest else None,
            "highest_total_score": highest["total_score"] if highest else None,
            "score_spread": spread,
            "policy_total_score": policy_score,
            "current_total_score": current_score,
            "ranking_table": ranking_table,
        },
        "warnings": sorted(set(run_warnings)),
    }
    return doc


def write_portfolio_health_score_txt(scorecard: dict[str, Any], path: Path) -> None:
    primary = scorecard.get("primary_window") or PRIMARY_WINDOW
    lines = [
        f"Portfolio Health Score (diagnostic only) — primary window {primary}",
        f"Weights profile: {scorecard.get('weights_profile', WEIGHTS_PROFILE)}",
        "",
        "Priority rows:",
    ]
    by_id = {c["candidate_id"]: c for c in scorecard.get("candidates", [])}
    for cid in scorecard.get("display_priority") or LEGACY_DISPLAY_PRIORITY:
        row = by_id.get(cid)
        if row and row.get("total_score") is not None:
            lines.append(f"  {row.get('display_name', cid):<38}  {row.get('total_score'):>3}")
    lines.extend(["", f"{'Rank':>4}  {'Candidate':<40}  {'Score':>5}"])
    for row in scorecard.get("comparison_summary", {}).get("ranking_table", []):
        lines.append(
            f"{row.get('health_rank', ''):>4}  "
            f"{row.get('display_name', ''):<40}  "
            f"{row.get('total_score', ''):>5}"
        )
    lines.extend(
        [
            "",
            "See portfolio_health_score.json for component drivers (top_drivers / top_drags).",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def write_portfolio_health_score_outputs(
    cfg: PortfolioConfig,
    *,
    project_root: Path | None = None,
    comparison: dict[str, Any] | None = None,
    robustness_scorecard: dict[str, Any] | None = None,
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

    if robustness_scorecard is None:
        rob_path = out_dir / "robustness_scorecard.json"
        if rob_path.is_file():
            robustness_scorecard = _load_json(rob_path)

    health = build_portfolio_health_score(
        comparison,
        project_root=project_root,
        robustness_scorecard=robustness_scorecard,
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    paths: dict[str, Path] = {}
    json_out = out_dir / "portfolio_health_score.json"
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(health, f, indent=2, ensure_ascii=False)
    paths["portfolio_health_score_json"] = json_out

    if write_txt:
        txt_out = out_dir / "portfolio_health_score.txt"
        write_portfolio_health_score_txt(health, txt_out)
        paths["portfolio_health_score_txt"] = txt_out

    return paths


__all__ = [
    "SCHEMA_VERSION",
    "DEFAULT_WEIGHTS",
    "build_portfolio_health_score",
    "write_portfolio_health_score_outputs",
    "write_portfolio_health_score_txt",
]
