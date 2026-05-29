"""Block 2.6 Portfolio Weakness Map — pre-stress hypothesis scoring.

This module is a read-only adapter over already-built product blocks 2.1–2.5.
It must not read Stress Lab artifacts (stress_report scenario PnL, attribution),
and it must not re-fit factor models or recompute RC_vol.
"""

from __future__ import annotations

import math
from typing import Any

BLOCK_2_6_ID = "2.6_portfolio_weakness_map"
BLOCK_2_6_NAME = "Portfolio Weakness Map"
RULE_VERSION = "heuristic_v2"

# Product-facing risk ids must align with Stress Lab synthetic scenario ids.
RISK_TYPES: tuple[str, ...] = (
    "equity_shock",
    "credit_shock",
    "rates_shock",
    "inflation_stagflation",
    "liquidity_shock",
    "usd_shock",
    "commodity_shock",
    "recession_severe",
)

# Transitional map for backward compatibility (legacy weakness ids).
# These aliases must not introduce a parallel product namespace; they are diagnostic-only metadata.
LEGACY_RISK_ALIASES: dict[str, str | None] = {
    "equity_crash": "equity_shock",
    "rates_up": "rates_shock",
    "inflation_shock": "inflation_stagflation",
    "credit_spreads": "credit_shock",
    "liquidity_shock": "liquidity_shock",
    "usd_shock": "usd_shock",
    "commodity_shock": "commodity_shock",
    "volatility_spike": None,
    "recession": "recession_severe",
}

STATUS_BANDS: dict[str, list[int]] = {
    "Low": [0, 39],
    "Medium": [40, 69],
    "High": [70, 100],
}

EVIDENCE_DIRECTIONS = {
    "above_threshold",
    "below_threshold",
    "present",
    "missing",
    "conflicting",
}

EVIDENCE_SOURCES = {
    "block_2_1",
    "block_2_2",
    "block_2_3",
    "block_2_4",
    "block_2_5",
}

FORBIDDEN_STRESS_KEYS: tuple[str, ...] = (
    "stress_report",
    "scenario_results",
    "pnl_by_asset_pct",
    "loss_attribution",
    "failed_scenario",
    "failed_test",
)


# Rule tables (Session 04): declarative scoring specs per risk type.
# These tables must stay Stress-Lab-agnostic: only Blocks 2.1–2.5 derived metrics.
RISK_RULE_TABLES: dict[str, dict[str, Any]] = {
    "equity_shock": {
        "minimum_evaluable_weight": 0.55,
        "signals": [
            {"metric": "equity_weight", "weight": 0.18, "moderate": 0.35, "high": 0.55},
            {"metric": "risk_on_weight", "weight": 0.08, "moderate": 0.20, "high": 0.35},
            {"metric": "downside_beta", "weight": 0.15, "moderate": 0.90, "high": 1.20},
            {"metric": "beta_portfolio_abs", "weight": 0.10, "moderate": 0.90, "high": 1.20},
            {"metric": "rolling_corr_latest", "weight": 0.10, "moderate": 0.70, "high": 0.85},
            {"metric": "beta_eq_abs", "weight": 0.12, "moderate": 0.35, "high": 0.65},
            {"metric": "equity_factor_variance_share", "weight": 0.10, "moderate": 0.20, "high": 0.35},
            {"metric": "equity_rc_pct", "weight": 0.07, "moderate": 0.35, "high": 0.55},
            {"metric": "hidden_equity_beta_score_frac", "weight": 0.10, "moderate": 0.40, "high": 0.70},
        ],
    },
    "rates_shock": {
        "minimum_evaluable_weight": 0.55,
        "signals": [
            {"metric": "rates_duration_weight", "weight": 0.42, "moderate": 0.25, "high": 0.45},
            {"metric": "beta_rr_abs", "weight": 0.18, "moderate": 0.25, "high": 0.50},
            {"metric": "duration_concentration_score_frac", "weight": 0.20, "moderate": 0.40, "high": 0.70},
            {"metric": "real_rates_factor_variance_share", "weight": 0.10, "moderate": 0.10, "high": 0.20},
            {"metric": "top1_rc_share", "weight": 0.10, "moderate": "thr_top1_mod", "high": "thr_top1_high"},
        ],
    },
    "inflation_stagflation": {
        "minimum_evaluable_weight": 0.55,
        "signals": [
            {"metric": "inflation_linked_rc_pct", "weight": 0.28, "moderate": 0.05, "high": 0.15},
            {"metric": "commodity_weight", "weight": 0.22, "moderate": 0.05, "high": 0.15},
            {"metric": "real_assets_weight", "weight": 0.18, "moderate": 0.05, "high": 0.15},
            {"metric": "beta_inf_abs", "weight": 0.12, "moderate": 0.20, "high": 0.40},
            {"metric": "inflation_factor_variance_share", "weight": 0.10, "moderate": 0.10, "high": 0.20},
            {"metric": "commodity_rc_pct", "weight": 0.10, "moderate": 0.05, "high": 0.15},
        ],
    },
    "credit_shock": {
        "minimum_evaluable_weight": 0.55,
        "signals": [
            {"metric": "credit_liquidity_weight", "weight": 0.32, "moderate": 0.20, "high": 0.35},
            {"metric": "credit_rc_pct", "weight": 0.28, "moderate": 0.20, "high": 0.35},
            {"metric": "beta_credit_abs", "weight": 0.15, "moderate": 0.20, "high": 0.40},
            {"metric": "credit_factor_variance_share", "weight": 0.10, "moderate": 0.10, "high": 0.20},
            {"metric": "credit_liquidity_risk_score_frac", "weight": 0.15, "moderate": 0.40, "high": 0.70},
        ],
    },
    "liquidity_shock": {
        "minimum_evaluable_weight": 0.55,
        "signals": [
            {"metric": "risk_on_or_carry_weight", "weight": 0.20, "moderate": 0.20, "high": 0.35},
            {"metric": "credit_rc_pct", "weight": 0.25, "moderate": 0.15, "high": 0.30},
            {"metric": "correlation_concentration_score_frac", "weight": 0.25, "moderate": 0.40, "high": 0.70},
            {"metric": "credit_liquidity_risk_score_frac", "weight": 0.20, "moderate": 0.40, "high": 0.70},
            {"metric": "tail_risk_score_frac", "weight": 0.10, "moderate": 0.40, "high": 0.70},
        ],
    },
    "usd_shock": {
        "minimum_evaluable_weight": 0.55,
        "signals": [
            {"metric": "dominant_currency_weight", "weight": 0.25, "moderate": 0.60, "high": 0.80},
            {"metric": "usd_currency_weight", "weight": 0.15, "moderate": 0.40, "high": 0.70},
            {"metric": "investor_currency_mismatch_flag", "weight": 0.15, "moderate": 0.50, "high": 0.90},
            {"metric": "beta_usd_abs", "weight": 0.25, "moderate": 0.20, "high": 0.40},
            {"metric": "usd_factor_variance_share", "weight": 0.20, "moderate": 0.10, "high": 0.20},
        ],
    },
    "commodity_shock": {
        "minimum_evaluable_weight": 0.55,
        "signals": [
            {"metric": "commodity_weight", "weight": 0.30, "moderate": 0.05, "high": 0.15},
            {"metric": "real_assets_weight", "weight": 0.25, "moderate": 0.05, "high": 0.15},
            {"metric": "commodity_rc_pct", "weight": 0.25, "moderate": 0.05, "high": 0.15},
            {"metric": "real_assets_rc_pct", "weight": 0.20, "moderate": 0.05, "high": 0.15},
        ],
    },
    "recession_severe": {
        "minimum_evaluable_weight": 0.55,
        "signals": [
            {"metric": "equity_rc_pct", "weight": 0.30, "moderate": 0.35, "high": 0.55},
            {"metric": "credit_rc_pct", "weight": 0.22, "moderate": 0.20, "high": 0.35},
            {"metric": "downside_beta", "weight": 0.18, "moderate": 0.90, "high": 1.20},
            {"metric": "beta_eq_abs", "weight": 0.10, "moderate": 0.35, "high": 0.65},
            {"metric": "tail_risk_score_frac", "weight": 0.20, "moderate": 0.40, "high": 0.70},
        ],
    },
}


def _validate_rule_tables(rule_tables: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for risk_type in RISK_TYPES:
        table = rule_tables.get(risk_type)
        if not isinstance(table, dict):
            errors.append(f"missing rule table for risk_type={risk_type}")
            continue
        min_w = _as_float(table.get("minimum_evaluable_weight"))
        if min_w is None or not (0.0 <= min_w <= 1.0):
            errors.append(f"invalid minimum_evaluable_weight for risk_type={risk_type}")
        signals = table.get("signals")
        if not isinstance(signals, list):
            errors.append(f"invalid signals list for risk_type={risk_type}")
            continue
        total_w = 0.0
        for sig in signals:
            if not isinstance(sig, dict):
                errors.append(f"invalid signal row (not dict) for risk_type={risk_type}")
                continue
            if not isinstance(sig.get("metric"), str) or not sig["metric"]:
                errors.append(f"signal missing metric for risk_type={risk_type}")
            w = _as_float(sig.get("weight"))
            if w is None or w < 0.0:
                errors.append(f"signal invalid weight for risk_type={risk_type}, metric={sig.get('metric')}")
            else:
                total_w += w
            mod = sig.get("moderate")
            high = sig.get("high")
            if isinstance(mod, (int, float)) and isinstance(high, (int, float)) and float(mod) > float(high):
                errors.append(f"signal moderate>high for risk_type={risk_type}, metric={sig.get('metric')}")
        if signals and abs(total_w - 1.0) > 1e-6:
            errors.append(f"signal weights must sum to 1.0 for risk_type={risk_type} (got {total_w})")
    return errors

_RISK_COPY: dict[str, dict[str, Any]] = {
    "equity_shock": {
        "title": "Equity shock risk",
        "why_it_matters": (
            "Equity crashes can dominate multi-asset portfolios when equity exposure is high or when "
            "diversifiers behave like equity in risk-off markets."
        ),
        "next_tests": ["equity_shock", "recession_severe", "liquidity_shock"],
    },
    "rates_shock": {
        "title": "Rates shock / duration risk",
        "why_it_matters": (
            "Rate shocks can hurt duration-sensitive sleeves even when the headline allocation looks balanced."
        ),
        "next_tests": ["rates_shock", "inflation_stagflation"],
    },
    "inflation_stagflation": {
        "title": "Inflation / stagflation risk",
        "why_it_matters": (
            "Inflation shocks can pressure both bonds and equities while changing the role of real assets and "
            "inflation-linked exposure."
        ),
        "next_tests": ["inflation_stagflation", "commodity_shock"],
    },
    "credit_shock": {
        "title": "Credit shock risk",
        "why_it_matters": (
            "Credit spreads can widen quickly when growth slows or liquidity tightens, harming credit and "
            "carry-like exposures."
        ),
        "next_tests": ["credit_shock", "liquidity_shock", "recession_severe"],
    },
    "liquidity_shock": {
        "title": "Liquidity shock risk",
        "why_it_matters": (
            "Liquidity shocks can force correlated drawdowns across risk assets, especially when credit and "
            "carry exposures are material."
        ),
        "next_tests": ["liquidity_shock", "credit_shock", "recession_severe"],
    },
    "usd_shock": {
        "title": "USD shock risk",
        "why_it_matters": (
            "Large USD moves can reprice non-USD assets and change the effective risk balance of a global portfolio."
        ),
        "next_tests": ["usd_shock"],
    },
    "commodity_shock": {
        "title": "Commodity shock risk",
        "why_it_matters": (
            "Commodity shocks can impact inflation expectations, real asset hedges, and sector exposures."
        ),
        "next_tests": ["commodity_shock", "inflation_stagflation"],
    },
    "recession_severe": {
        "title": "Severe recession risk",
        "why_it_matters": (
            "Recessions can combine equity drawdowns, credit deterioration, and weaker diversification across "
            "risk sleeves."
        ),
        "next_tests": ["recession_severe", "credit_shock", "equity_shock"],
    },
}


def _as_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            return None
        return number
    except (TypeError, ValueError):
        return None


def _path(doc: dict[str, Any] | None, *keys: str) -> Any:
    cur: Any = doc if isinstance(doc, dict) else {}
    for key in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _detect_forbidden_keys(doc: Any, forbidden: set[str]) -> set[str]:
    """Best-effort scan to guard the Stress Lab separation contract."""
    found: set[str] = set()
    if isinstance(doc, dict):
        for k, v in doc.items():
            key = str(k)
            if key in forbidden:
                found.add(key)
            if isinstance(v, (dict, list, tuple)):
                found |= _detect_forbidden_keys(v, forbidden)
    elif isinstance(doc, (list, tuple)):
        for item in doc:
            if isinstance(item, (dict, list, tuple)):
                found |= _detect_forbidden_keys(item, forbidden)
    return found


def _pct_to_fraction(value: Any) -> float | None:
    number = _as_float(value)
    if number is None:
        return None
    if abs(number) > 1.0:
        return number / 100.0
    return number


def _breakdown_weight(block_2_1: dict[str, Any] | None, dimension: str, labels: set[str]) -> float | None:
    rows = _path(block_2_1, "capital_allocation_breakdown", dimension)
    if not isinstance(rows, list):
        return None
    total = 0.0
    found = False
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "").strip().lower()
        if name in labels:
            weight = _pct_to_fraction(row.get("weight_pct"))
            if weight is not None:
                total += weight
                found = True
    return total if found else 0.0


def _dominant_breakdown_entry(block_2_1: dict[str, Any] | None, dimension: str) -> tuple[str | None, float | None]:
    rows = _path(block_2_1, "capital_allocation_breakdown", dimension)
    if not isinstance(rows, list) or not rows:
        return None, None
    best_label: str | None = None
    best_w: float | None = None
    for row in rows:
        if not isinstance(row, dict):
            continue
        label = str(row.get("name") or "").strip()
        w = _pct_to_fraction(row.get("weight_pct"))
        if label and w is not None and (best_w is None or w > best_w):
            best_label, best_w = label, w
    return best_label, best_w


def _bucket_share(block_2_5: dict[str, Any] | None, bucket: str, field: str) -> float | None:
    rows = _path(block_2_5, "risk_budget_bucket_contribution")
    if not isinstance(rows, list):
        return None
    for row in rows:
        if not isinstance(row, dict):
            continue
        if str(row.get("bucket") or "").strip().lower() == bucket.strip().lower():
            return _pct_to_fraction(row.get(field))
    return 0.0


def _top1_rc_share(block_2_5: dict[str, Any] | None) -> float | None:
    return _pct_to_fraction(_path(block_2_5, "top1_rc_asset", "risk_contribution_pct"))


def _hidden_alert_score(block_2_4: dict[str, Any] | None, alert_id: str) -> int | None:
    score = _path(block_2_4, "alerts", alert_id, "score")
    if isinstance(score, (int, float)) and not math.isnan(float(score)):
        return int(round(float(score)))
    return None


def _hidden_alert_v2(block_2_4: dict[str, Any] | None, alert_id: str) -> dict[str, Any]:
    """Extract Block 2.4 alert fields, preferring heuristic_v2 contract when present.

    This is a read-only adapter: it does not rescore or reinterpret the alert.
    """
    raw = _path(block_2_4, "alerts", alert_id)
    if not isinstance(raw, dict):
        return {
            "status": "Unavailable",
            "score": None,
            "confidence": "unavailable",
            "confidence_reason": None,
            "limitations": ["Hidden exposure alert is missing from Block 2.4."],
            "contributing_assets": [],
            "next_tests": [],
        }
    score = raw.get("score")
    score_i: int | None = None
    if isinstance(score, (int, float)) and not math.isnan(float(score)):
        score_i = int(round(float(score)))
    status = str(raw.get("status") or ("Unavailable" if score_i is None else "")).strip() or "Unavailable"
    confidence = str(raw.get("confidence") or ("unavailable" if score_i is None else "low")).strip() or "low"
    confidence_reason = raw.get("confidence_reason")
    if confidence_reason is not None and not isinstance(confidence_reason, str):
        confidence_reason = None
    limitations = raw.get("limitations")
    limitations_list = [str(x) for x in limitations] if isinstance(limitations, list) else []
    contributing = raw.get("contributing_assets")
    contributing_list = contributing if isinstance(contributing, list) else []
    next_tests = raw.get("next_tests")
    next_tests_list = [str(x) for x in next_tests] if isinstance(next_tests, list) else []
    return {
        "status": status,
        "score": score_i,
        "confidence": confidence,
        "confidence_reason": confidence_reason,
        "limitations": limitations_list,
        "contributing_assets": contributing_list,
        "next_tests": next_tests_list,
    }


def _factor_beta(block_2_3: dict[str, Any] | None, beta_key: str) -> float | None:
    return _as_float(_path(block_2_3, "factor_beta_snapshot", beta_key))


def _factor_variance_share(block_2_3: dict[str, Any] | None, factor_name: str) -> float | None:
    return _as_float(_path(block_2_3, "factor_variance_contribution", "contributions", factor_name))


def _rolling_correlation_latest(block_2_2: dict[str, Any] | None) -> float | None:
    return _as_float(
        _path(
            block_2_2,
            "rolling_diagnostics",
            "core_view",
            "rolling_beta_or_correlation",
            "latest_correlation",
        )
    )


def _threshold(thresholds: dict[str, Any] | None, key: str) -> float | None:
    if not isinstance(thresholds, dict):
        return None
    return _as_float(thresholds.get(key))


def _evidence(
    *,
    metric: str,
    value: Any,
    threshold_key: str | None,
    direction: str,
    source: str,
    interpretation: str,
) -> dict[str, Any]:
    if direction not in EVIDENCE_DIRECTIONS:
        raise ValueError(f"unknown evidence direction: {direction}")
    if source not in EVIDENCE_SOURCES:
        raise ValueError(f"unknown evidence source: {source}")
    return {
        "metric": metric,
        "value": value,
        "threshold_key": threshold_key,
        "direction": direction,
        "source": source,
        "interpretation": interpretation,
    }


def _score_signal(value: float | None, *, moderate: float, high: float) -> float | None:
    if value is None:
        return None
    x = float(value)
    if x < moderate:
        return max(0.0, min(39.0, (x / max(moderate, 1e-12)) * 39.0))
    if x >= high:
        return 70.0 + min(30.0, ((x - high) / max(abs(high), 1e-12)) * 30.0)
    span = high - moderate or 1.0
    return 40.0 + ((x - moderate) / span) * 29.0


def _score_to_severity(score: int | None) -> str:
    if score is None:
        return "Unavailable"
    if score >= 70:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


def _confidence(evaluable_weight: float, score: int | None, limitations: list[str]) -> str:
    if score is None:
        return "unavailable"
    if evaluable_weight >= 0.75 and not limitations:
        return "high"
    if evaluable_weight >= 0.50:
        return "medium"
    return "low"


def _format_metric_value(value: Any) -> str:
    number = _as_float(value)
    if number is not None:
        if abs(number) <= 1.0:
            return f"{number * 100:.1f}%"
        return f"{number:.3f}"
    if isinstance(value, dict):
        investor = value.get("investor_currency")
        dominant = value.get("dominant_currency_exposure")
        if investor and dominant:
            return f"{investor}/{dominant}"
    if isinstance(value, str) and value.strip():
        return value.strip()
    return "n/a"


def _rank_evidence_rows(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    direction_rank = {
        "above_threshold": 0,
        "present": 1,
        "below_threshold": 2,
        "conflicting": 3,
        "missing": 4,
    }
    scored: list[tuple[int, int, dict[str, Any]]] = []
    for idx, row in enumerate(evidence):
        if not isinstance(row, dict):
            continue
        direction = str(row.get("direction") or "")
        metric = str(row.get("metric") or "")
        if not metric:
            continue
        score = direction_rank.get(direction, 5)
        scored.append((score, idx, row))
    scored.sort(key=lambda x: (x[0], x[1]))
    return [row for _, _, row in scored]


def _build_key_evidence(evidence: list[dict[str, Any]], *, limit: int = 5) -> list[str]:
    rows = _rank_evidence_rows(evidence)
    out: list[str] = []
    for row in rows:
        metric = str(row.get("metric") or "")
        interpretation = str(row.get("interpretation") or "").strip()
        direction = str(row.get("direction") or "")
        value_repr = _format_metric_value(row.get("value"))
        if direction == "missing":
            line = f"{metric}: missing upstream evidence."
        elif direction == "above_threshold":
            line = f"{metric}: {value_repr} (above threshold)."
        elif direction == "below_threshold":
            line = f"{metric}: {value_repr} (below threshold)."
        elif direction == "conflicting":
            line = f"{metric}: conflicting signals ({value_repr})."
        else:
            line = f"{metric}: {value_repr}."
        if interpretation:
            line = f"{line} {interpretation}"
        out.append(line.strip())
        if len(out) >= max(3, min(limit, 5)):
            break
    return out


def _build_why_status(
    *,
    severity: str,
    score: int | None,
    evidence: list[dict[str, Any]],
    limitations: list[str],
) -> str:
    top = _rank_evidence_rows(evidence)[:2]
    signal_bits: list[str] = []
    for row in top:
        metric = str(row.get("metric") or "")
        if not metric:
            continue
        direction = str(row.get("direction") or "")
        if direction == "above_threshold":
            signal_bits.append(f"{metric} is above threshold")
        elif direction == "present":
            signal_bits.append(f"{metric} is present")
        elif direction == "below_threshold":
            signal_bits.append(f"{metric} stays below threshold")
        elif direction == "missing":
            signal_bits.append(f"{metric} is missing")
    if severity == "Unavailable":
        if limitations:
            return f"Severity is Unavailable because required signals are incomplete: {limitations[0]}"
        return "Severity is Unavailable because required upstream evidence is incomplete."
    if signal_bits:
        return f"Severity is {severity} (score {score}) because " + "; ".join(signal_bits) + "."
    return f"Severity is {severity} (score {score}) based on available Block 2.1–2.5 evidence."


def _build_short_diagnosis(risk_title: str, severity: str, score: int | None, why_status: str) -> str:
    if severity == "Unavailable":
        lead = f"{risk_title} is currently Unavailable."
    else:
        lead = f"{risk_title} is {severity} (score {score}/100)."
    return f"{lead} {why_status}"


def _build_confidence_reason(confidence: str, evaluable_weight: float, limitations: list[str]) -> str | None:
    if confidence == "unavailable":
        return "Confidence is unavailable because the risk score could not be computed from current evidence."
    if confidence == "high":
        return "High confidence because most signals are evaluable and no material data limitations were detected."
    if confidence == "medium":
        return (
            f"Medium confidence: evaluable signal coverage is {evaluable_weight:.2f}; "
            "some evidence gaps may affect precision."
        )
    if limitations:
        return f"Low confidence due to limited evaluable coverage and data caveats: {limitations[0]}"
    return "Low confidence due to limited evaluable signal coverage."


def _linked_assets_from_alert(alert: dict[str, Any], *, source: str = "block_2_4", limit: int = 3) -> list[dict[str, Any]]:
    linked: list[dict[str, Any]] = []
    for item in alert.get("contributing_assets") or []:
        if not isinstance(item, dict):
            continue
        ticker = item.get("ticker")
        if not isinstance(ticker, str) or not ticker:
            continue
        linked.append({"ticker": ticker, "weight_pct": item.get("weight_pct"), "source": source})
        if len(linked) >= limit:
            break
    return linked


def _build_risk(
    risk_type: str,
    *,
    signals: list[dict[str, Any]],
    minimum_evaluable_weight: float,
    evidence: list[dict[str, Any]],
    limitations: list[str],
) -> dict[str, Any]:
    weighted = 0.0
    evaluable_weight = 0.0

    for sig in signals:
        value = sig.get("value")
        comp = _score_signal(
            _as_float(value),
            moderate=float(sig["moderate"]),
            high=float(sig["high"]),
        )
        if comp is None:
            continue
        w = float(sig["weight"])
        weighted += comp * w
        evaluable_weight += w

    score: int | None
    if evaluable_weight < minimum_evaluable_weight:
        score = None
        limitations = list(dict.fromkeys(limitations + ["insufficient evidence to score this risk type reliably"]))
    else:
        score = int(round(max(0.0, min(100.0, weighted / evaluable_weight))))

    severity = _score_to_severity(score)
    copy = _RISK_COPY[risk_type]
    why_status = _build_why_status(severity=severity, score=score, evidence=evidence, limitations=limitations)
    short_diagnosis = _build_short_diagnosis(copy["title"], severity, score, why_status)
    key_evidence = _build_key_evidence(evidence)

    return {
        "risk_type": risk_type,
        "risk_title": copy["title"],
        "score_0_100": score,
        "severity": severity,
        "confidence": _confidence(evaluable_weight, score, limitations),
        "evidence": evidence,
        "short_diagnosis": short_diagnosis,
        "why_status": why_status,
        "key_evidence": key_evidence,
        "linked_assets": [],
        "data_quality_warnings": [],
        "confidence_reason": _build_confidence_reason(_confidence(evaluable_weight, score, limitations), evaluable_weight, limitations),
        "signal_scores": None,
        "explanation": short_diagnosis,
        "why_it_matters": copy["why_it_matters"],
        "next_tests": list(copy["next_tests"]),
        "limitations": limitations,
    }


def _materialize_signals(
    risk_type: str,
    *,
    metrics: dict[str, Any],
    thresholds_vars: dict[str, float],
) -> tuple[list[dict[str, Any]], float]:
    table = RISK_RULE_TABLES[risk_type]
    rows = table.get("signals") or []
    signals: list[dict[str, Any]] = []
    for row in rows:
        metric = str(row["metric"])
        moderate = row.get("moderate")
        high = row.get("high")
        if isinstance(moderate, str):
            moderate = thresholds_vars.get(moderate)
        if isinstance(high, str):
            high = thresholds_vars.get(high)
        signals.append(
            {
                "value": metrics.get(metric),
                "weight": float(row["weight"]),
                "moderate": float(moderate) if moderate is not None else 0.0,
                "high": float(high) if high is not None else 0.0,
            }
        )
    return signals, float(table.get("minimum_evaluable_weight") or 0.0)


def build_block_2_6_portfolio_weakness_map(
    block_2_1: dict[str, Any] | None,
    block_2_2: dict[str, Any] | None,
    block_2_3: dict[str, Any] | None,
    block_2_4: dict[str, Any] | None,
    block_2_5: dict[str, Any] | None,
    *,
    thresholds: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build product-facing Portfolio Weakness Map from Blocks 2.1–2.5 only."""
    warnings: list[str] = []
    blocked_upstream_fields: list[dict[str, str]] = []
    table_errors = _validate_rule_tables(RISK_RULE_TABLES)
    if table_errors:
        warnings.append("rule table validation warning: " + "; ".join(table_errors))
    if not isinstance(block_2_1, dict):
        warnings.append("block_2_1 missing")
    if not isinstance(block_2_2, dict):
        warnings.append("block_2_2 missing")
    if not isinstance(block_2_3, dict):
        warnings.append("block_2_3 missing")
    if not isinstance(block_2_4, dict):
        warnings.append("block_2_4 missing")
    if not isinstance(block_2_5, dict):
        warnings.append("block_2_5 missing")

    forbidden = set(FORBIDDEN_STRESS_KEYS)
    forbidden_found = (
        _detect_forbidden_keys(block_2_1, forbidden)
        | _detect_forbidden_keys(block_2_2, forbidden)
        | _detect_forbidden_keys(block_2_3, forbidden)
        | _detect_forbidden_keys(block_2_4, forbidden)
        | _detect_forbidden_keys(block_2_5, forbidden)
    )
    if forbidden_found:
        warnings.append(
            "stress boundary warning: forbidden Stress Lab keys detected in upstream inputs "
            f"({', '.join(sorted(forbidden_found))}); Block 2.6 ignores them by contract"
        )

    equity_w = _breakdown_weight(block_2_1, "by_asset_class", {"equity"})
    risk_on_w = _breakdown_weight(block_2_1, "by_risk_role", {"risk_on"})
    risk_on_or_carry_w = _breakdown_weight(block_2_1, "by_risk_role", {"risk_on", "carry"})
    rates_w = _breakdown_weight(block_2_1, "by_main_risk_factor", {"real_rates", "rates", "duration"})
    credit_w = _breakdown_weight(block_2_1, "by_main_risk_factor", {"credit", "liquidity"})
    commodity_w = _breakdown_weight(block_2_1, "by_asset_class", {"commodity"})
    real_assets_w = _breakdown_weight(block_2_1, "by_asset_class", {"real_assets"})

    downside_beta = _as_float(_path(block_2_2, "benchmark_dependence", "downside_beta"))
    beta_portfolio = _as_float(_path(block_2_2, "benchmark_dependence", "beta_portfolio"))
    corr_base = _as_float(_path(block_2_2, "benchmark_dependence", "corr_base"))
    rolling_corr_latest = _rolling_correlation_latest(block_2_2)

    beta_rr = _factor_beta(block_2_3, "beta_rr")
    beta_eq = _factor_beta(block_2_3, "beta_eq")
    beta_usd = _factor_beta(block_2_3, "beta_usd")
    beta_credit = _factor_beta(block_2_3, "beta_credit")
    beta_inf = _factor_beta(block_2_3, "beta_inf")

    equity_rc = _bucket_share(block_2_5, "equity", "risk_contribution_pct")
    credit_rc = _bucket_share(block_2_5, "credit", "risk_contribution_pct")
    top1_rc = _top1_rc_share(block_2_5)

    thr_top1_mod = _threshold(thresholds, "top1_rc_moderate") or 0.25
    thr_top1_high = _threshold(thresholds, "top1_rc_high") or 0.35

    he_score = _hidden_alert_score(block_2_4, "hidden_equity_beta")
    dur_score = _hidden_alert_score(block_2_4, "duration_concentration")
    cl_score = _hidden_alert_score(block_2_4, "credit_liquidity_risk")
    corr_score = _hidden_alert_score(block_2_4, "correlation_concentration")
    tail_score = _hidden_alert_score(block_2_4, "tail_risk")

    # Block 2.4 heuristic_v2 integration (richer fields when present).
    he_alert = _hidden_alert_v2(block_2_4, "hidden_equity_beta")
    dur_alert = _hidden_alert_v2(block_2_4, "duration_concentration")
    cl_alert = _hidden_alert_v2(block_2_4, "credit_liquidity_risk")
    corr_alert = _hidden_alert_v2(block_2_4, "correlation_concentration")
    tail_alert = _hidden_alert_v2(block_2_4, "tail_risk")

    commodity_rc = _bucket_share(block_2_5, "commodity", "risk_contribution_pct")
    real_assets_rc = _bucket_share(block_2_5, "real_assets", "risk_contribution_pct")
    infl_linked_rc = _bucket_share(block_2_5, "inflation_linked", "risk_contribution_pct")

    dominant_currency, dominant_currency_weight = _dominant_breakdown_entry(block_2_1, "by_currency")
    usd_currency_weight = _breakdown_weight(block_2_1, "by_currency", {"usd"})
    investor_currency = _path(block_2_2, "investor_currency") or _path(block_2_1, "investor_currency")
    investor_mismatch_flag = None
    if isinstance(investor_currency, str) and dominant_currency:
        investor_mismatch_flag = 1.0 if investor_currency.strip().upper() != dominant_currency.strip().upper() else 0.0

    eq_var_share = _factor_variance_share(block_2_3, "equity")
    rr_var_share = _factor_variance_share(block_2_3, "real_rates")
    inf_var_share = _factor_variance_share(block_2_3, "inflation")
    credit_var_share = _factor_variance_share(block_2_3, "credit")
    usd_var_share = _factor_variance_share(block_2_3, "USD")

    # Prefer v2 alert scores when available (fallback to v1 score-only fields).
    he_score_v2 = he_alert.get("score") if isinstance(he_alert, dict) else None
    dur_score_v2 = dur_alert.get("score") if isinstance(dur_alert, dict) else None
    cl_score_v2 = cl_alert.get("score") if isinstance(cl_alert, dict) else None
    corr_score_v2 = corr_alert.get("score") if isinstance(corr_alert, dict) else None
    tail_score_v2 = tail_alert.get("score") if isinstance(tail_alert, dict) else None

    metrics: dict[str, Any] = {
        "equity_weight": equity_w,
        "risk_on_weight": risk_on_w,
        "risk_on_or_carry_weight": risk_on_or_carry_w,
        "rates_duration_weight": rates_w,
        "credit_liquidity_weight": credit_w,
        "commodity_weight": commodity_w,
        "real_assets_weight": real_assets_w,
        "downside_beta": downside_beta,
        "beta_portfolio_abs": None if beta_portfolio is None else abs(beta_portfolio),
        "corr_base_abs": None if corr_base is None else abs(corr_base),
        "rolling_corr_latest": rolling_corr_latest,
        "beta_rr_abs": None if beta_rr is None else abs(beta_rr),
        "beta_eq_abs": None if beta_eq is None else abs(beta_eq),
        "beta_usd_abs": None if beta_usd is None else abs(beta_usd),
        "beta_credit_abs": None if beta_credit is None else abs(beta_credit),
        "beta_inf_abs": None if beta_inf is None else abs(beta_inf),
        "equity_rc_pct": equity_rc,
        "credit_rc_pct": credit_rc,
        "top1_rc_share": top1_rc,
        "hidden_equity_beta_score_frac": None
        if (he_score_v2 if he_score_v2 is not None else he_score) is None
        else (he_score_v2 if he_score_v2 is not None else he_score) / 100.0,
        "duration_concentration_score_frac": None
        if (dur_score_v2 if dur_score_v2 is not None else dur_score) is None
        else (dur_score_v2 if dur_score_v2 is not None else dur_score) / 100.0,
        "credit_liquidity_risk_score_frac": None
        if (cl_score_v2 if cl_score_v2 is not None else cl_score) is None
        else (cl_score_v2 if cl_score_v2 is not None else cl_score) / 100.0,
        "correlation_concentration_score_frac": None
        if (corr_score_v2 if corr_score_v2 is not None else corr_score) is None
        else (corr_score_v2 if corr_score_v2 is not None else corr_score) / 100.0,
        "tail_risk_score_frac": None
        if (tail_score_v2 if tail_score_v2 is not None else tail_score) is None
        else (tail_score_v2 if tail_score_v2 is not None else tail_score) / 100.0,
        "commodity_rc_pct": commodity_rc,
        "real_assets_rc_pct": real_assets_rc,
        "inflation_linked_rc_pct": infl_linked_rc,
        "dominant_currency_weight": dominant_currency_weight,
        "usd_currency_weight": usd_currency_weight,
        "investor_currency_mismatch_flag": investor_mismatch_flag,
        "equity_factor_variance_share": eq_var_share,
        "real_rates_factor_variance_share": rr_var_share,
        "inflation_factor_variance_share": inf_var_share,
        "credit_factor_variance_share": credit_var_share,
        "usd_factor_variance_share": usd_var_share,
    }

    risks: list[dict[str, Any]] = []
    thresholds_vars = {"thr_top1_mod": thr_top1_mod, "thr_top1_high": thr_top1_high}

    def add_equity_shock() -> None:
        evidence: list[dict[str, Any]] = []
        limitations: list[str] = []
        if equity_w is None:
            limitations.append("equity weight not available from Block 2.1 breakdown")
        if risk_on_w is None:
            limitations.append("risk_on weight not available from Block 2.1 breakdown")
        evidence.append(
            _evidence(
                metric="equity_weight",
                value=equity_w,
                threshold_key=None,
                direction="missing" if equity_w is None else "present",
                source="block_2_1",
                interpretation="Higher equity weight typically increases sensitivity to equity drawdowns.",
            )
        )
        evidence.append(
            _evidence(
                metric="risk_on_weight",
                value=risk_on_w,
                threshold_key=None,
                direction="missing" if risk_on_w is None else "present",
                source="block_2_1",
                interpretation="Risk-on taxonomy weight adds a behavior-oriented proxy for equity-like vulnerability.",
            )
        )
        evidence.append(
            _evidence(
                metric="downside_beta",
                value=downside_beta,
                threshold_key=None,
                direction="missing" if downside_beta is None else "present",
                source="block_2_2",
                interpretation="Downside beta indicates whether market sensitivity rises in weak markets.",
            )
        )
        evidence.append(
            _evidence(
                metric="beta_portfolio",
                value=beta_portfolio,
                threshold_key=None,
                direction="missing" if beta_portfolio is None else "present",
                source="block_2_2",
                interpretation="Portfolio beta summarises base-benchmark market sensitivity in the primary window.",
            )
        )
        evidence.append(
            _evidence(
                metric="rolling_correlation_latest",
                value=rolling_corr_latest,
                threshold_key=None,
                direction="missing" if rolling_corr_latest is None else "present",
                source="block_2_2",
                interpretation="Rolling correlation is a stability proxy for how consistently the portfolio moves with the benchmark.",
            )
        )
        evidence.append(
            _evidence(
                metric="beta_eq",
                value=beta_eq,
                threshold_key="equity_beta_moderate_abs",
                direction="missing" if beta_eq is None else "present",
                source="block_2_3",
                interpretation="Equity factor beta adds behavior-based evidence beyond allocations.",
            )
        )
        evidence.append(
            _evidence(
                metric="equity_factor_variance_share",
                value=eq_var_share,
                threshold_key=None,
                direction="missing" if eq_var_share is None else "present",
                source="block_2_3",
                interpretation="Factor variance contribution (equity share) proxies how much equity explains portfolio variance in the factor model.",
            )
        )
        evidence.append(
            _evidence(
                metric="top1_rc_share",
                value=top1_rc,
                threshold_key="top1_rc_moderate",
                direction="missing" if top1_rc is None else ("above_threshold" if top1_rc >= thr_top1_mod else "below_threshold"),
                source="block_2_5",
                interpretation="Single-position risk concentration can amplify an equity drawdown profile.",
            )
        )
        evidence.append(
            _evidence(
                metric="hidden_equity_beta_score",
                value=he_alert.get("score"),
                threshold_key=None,
                direction="missing" if he_alert.get("score") is None else "present",
                source="block_2_4",
                interpretation="Hidden-equity-beta alert summarizes multi-signal equity-like behavior.",
            )
        )
        evidence.append(
            _evidence(
                metric="hidden_equity_beta_status",
                value=he_alert.get("status"),
                threshold_key=None,
                direction="missing" if not he_alert.get("status") else "present",
                source="block_2_4",
                interpretation="Block 2.4 alert status provides the hidden-exposure severity band.",
            )
        )
        if he_alert.get("confidence"):
            evidence.append(
                _evidence(
                    metric="hidden_equity_beta_confidence",
                    value=he_alert.get("confidence"),
                    threshold_key=None,
                    direction="present",
                    source="block_2_4",
                    interpretation="Block 2.4 confidence qualifies the reliability of the hidden-exposure alert.",
                )
            )
        if he_alert.get("limitations"):
            limitations.extend([f"Hidden exposure (2.4) — hidden_equity_beta: {x}" for x in he_alert["limitations"]])

        signals, min_w = _materialize_signals("equity_shock", metrics=metrics, thresholds_vars=thresholds_vars)
        row = (
            _build_risk(
                "equity_shock",
                signals=signals,
                minimum_evaluable_weight=min_w,
                evidence=evidence,
                limitations=limitations,
            )
        )
        row["linked_assets"] = _linked_assets_from_alert(he_alert)
        risks.append(row)

    def add_rates_shock() -> None:
        evidence: list[dict[str, Any]] = []
        limitations: list[str] = []
        if rates_w is None:
            limitations.append("rates/duration weight not available from Block 2.1 breakdown")
        evidence.append(
            _evidence(
                metric="rates_duration_weight",
                value=rates_w,
                threshold_key=None,
                direction="missing" if rates_w is None else "present",
                source="block_2_1",
                interpretation="Rates/duration-tagged capital weight is a first-order proxy for duration sensitivity.",
            )
        )
        evidence.append(
            _evidence(
                metric="beta_rr",
                value=beta_rr,
                threshold_key="factor_beta_moderate_abs",
                direction="missing" if beta_rr is None else "present",
                source="block_2_3",
                interpretation="Real-rates factor beta (when available) adds behavior-based evidence.",
            )
        )
        evidence.append(
            _evidence(
                metric="real_rates_factor_variance_share",
                value=rr_var_share,
                threshold_key=None,
                direction="missing" if rr_var_share is None else "present",
                source="block_2_3",
                interpretation="Real-rates factor variance share provides a model-based proxy for duration-driven variance.",
            )
        )
        evidence.append(
            _evidence(
                metric="duration_concentration_score",
                value=dur_alert.get("score"),
                threshold_key=None,
                direction="missing" if dur_alert.get("score") is None else "present",
                source="block_2_4",
                interpretation="Duration concentration alert summarizes multiple proxies for rate sensitivity.",
            )
        )
        evidence.append(
            _evidence(
                metric="duration_concentration_status",
                value=dur_alert.get("status"),
                threshold_key=None,
                direction="missing" if not dur_alert.get("status") else "present",
                source="block_2_4",
                interpretation="Block 2.4 duration-concentration status provides the hidden-exposure severity band.",
            )
        )
        if dur_alert.get("limitations"):
            limitations.extend([f"Hidden exposure (2.4) — duration_concentration: {x}" for x in dur_alert["limitations"]])
        evidence.append(
            _evidence(
                metric="top1_rc_share",
                value=top1_rc,
                threshold_key="top1_rc_moderate",
                direction="missing" if top1_rc is None else ("above_threshold" if top1_rc >= thr_top1_mod else "below_threshold"),
                source="block_2_5",
                interpretation="Concentration can make rate sensitivity hinge on a single sleeve.",
            )
        )
        signals, min_w = _materialize_signals("rates_shock", metrics=metrics, thresholds_vars=thresholds_vars)
        row = _build_risk(
                "rates_shock",
                signals=signals,
                minimum_evaluable_weight=min_w,
                evidence=evidence,
                limitations=limitations,
            )
        row["linked_assets"] = _linked_assets_from_alert(dur_alert)
        risks.append(row)

    def add_inflation_stagflation() -> None:
        evidence: list[dict[str, Any]] = []
        limitations: list[str] = ["inflation model evidence is limited in Core MVP; treat as a hypothesis only"]
        evidence.append(
            _evidence(
                metric="inflation_linked_rc_pct",
                value=infl_linked_rc,
                threshold_key=None,
                direction="missing" if infl_linked_rc is None else "present",
                source="block_2_5",
                interpretation="Inflation-linked sleeves can change inflation-shock sensitivity depending on construction.",
            )
        )
        evidence.append(
            _evidence(
                metric="commodity_weight",
                value=commodity_w,
                threshold_key=None,
                direction="missing" if commodity_w is None else "present",
                source="block_2_1",
                interpretation="Commodity allocation can be a partial inflation hedge but may add cyclical risk.",
            )
        )
        evidence.append(
            _evidence(
                metric="real_assets_weight",
                value=real_assets_w,
                threshold_key=None,
                direction="missing" if real_assets_w is None else "present",
                source="block_2_1",
                interpretation="Real assets can be an inflation hedge but can also behave like equities in stress.",
            )
        )
        evidence.append(
            _evidence(
                metric="beta_inf",
                value=beta_inf,
                threshold_key=None,
                direction="missing" if beta_inf is None else "present",
                source="block_2_3",
                interpretation="Inflation factor beta adds factor-based sensitivity evidence when available.",
            )
        )
        evidence.append(
            _evidence(
                metric="inflation_factor_variance_share",
                value=inf_var_share,
                threshold_key=None,
                direction="missing" if inf_var_share is None else "present",
                source="block_2_3",
                interpretation="Inflation factor variance share adds model-based evidence when available.",
            )
        )
        signals, min_w = _materialize_signals("inflation_stagflation", metrics=metrics, thresholds_vars=thresholds_vars)
        risks.append(
            _build_risk(
                "inflation_stagflation",
                signals=signals,
                minimum_evaluable_weight=min_w,
                evidence=evidence,
                limitations=limitations,
            )
        )

    def add_credit_shock() -> None:
        evidence: list[dict[str, Any]] = []
        limitations: list[str] = []
        evidence.append(
            _evidence(
                metric="credit_liquidity_weight",
                value=credit_w,
                threshold_key="credit_weight_high",
                direction="missing" if credit_w is None else "present",
                source="block_2_1",
                interpretation="Credit/liquidity-tagged capital weight proxies spread and carry exposure.",
            )
        )
        evidence.append(
            _evidence(
                metric="credit_rc_pct",
                value=credit_rc,
                threshold_key="credit_weight_high",
                direction="missing" if credit_rc is None else "present",
                source="block_2_5",
                interpretation="Credit risk contribution captures how much portfolio variance is driven by credit sleeves.",
            )
        )
        evidence.append(
            _evidence(
                metric="beta_credit",
                value=beta_credit,
                threshold_key=None,
                direction="missing" if beta_credit is None else "present",
                source="block_2_3",
                interpretation="Credit factor beta adds behavior-based evidence beyond allocations.",
            )
        )
        evidence.append(
            _evidence(
                metric="credit_factor_variance_share",
                value=credit_var_share,
                threshold_key=None,
                direction="missing" if credit_var_share is None else "present",
                source="block_2_3",
                interpretation="Credit factor variance share adds model-based evidence when available.",
            )
        )
        evidence.append(
            _evidence(
                metric="credit_liquidity_risk_score",
                value=cl_alert.get("score"),
                threshold_key=None,
                direction="missing" if cl_alert.get("score") is None else "present",
                source="block_2_4",
                interpretation="Credit/liquidity hidden-risk alert aggregates multiple proxies for risk-on credit behavior.",
            )
        )
        evidence.append(
            _evidence(
                metric="credit_liquidity_risk_status",
                value=cl_alert.get("status"),
                threshold_key=None,
                direction="missing" if not cl_alert.get("status") else "present",
                source="block_2_4",
                interpretation="Block 2.4 credit/liquidity status provides the hidden-exposure severity band.",
            )
        )
        if cl_alert.get("limitations"):
            limitations.extend([f"Hidden exposure (2.4) — credit_liquidity_risk: {x}" for x in cl_alert["limitations"]])
        signals, min_w = _materialize_signals("credit_shock", metrics=metrics, thresholds_vars=thresholds_vars)
        row = _build_risk(
                "credit_shock",
                signals=signals,
                minimum_evaluable_weight=min_w,
                evidence=evidence,
                limitations=limitations,
            )
        row["linked_assets"] = _linked_assets_from_alert(cl_alert)
        risks.append(row)

    def add_liquidity_shock() -> None:
        evidence: list[dict[str, Any]] = []
        limitations: list[str] = ["liquidity is proxied by taxonomy and credit/carry indicators only (no bid/ask data)"]
        evidence.append(
            _evidence(
                metric="credit_rc_pct",
                value=credit_rc,
                threshold_key="liquidity_risk_weight_high",
                direction="missing" if credit_rc is None else "present",
                source="block_2_5",
                interpretation="Liquidity events often propagate through credit and spread-sensitive sleeves.",
            )
        )
        evidence.append(
            _evidence(
                metric="correlation_concentration_score",
                value=corr_alert.get("score"),
                threshold_key=None,
                direction="missing" if corr_alert.get("score") is None else "present",
                source="block_2_4",
                interpretation="Higher correlation concentration can reduce diversification in liquidity stress.",
            )
        )
        evidence.append(
            _evidence(
                metric="credit_liquidity_risk_score",
                value=cl_alert.get("score"),
                threshold_key=None,
                direction="missing" if cl_alert.get("score") is None else "present",
                source="block_2_4",
                interpretation="Credit/liquidity hidden-risk alert acts as a proxy for liquidity fragility.",
            )
        )
        evidence.append(
            _evidence(
                metric="tail_risk_score",
                value=tail_alert.get("score"),
                threshold_key=None,
                direction="missing" if tail_alert.get("score") is None else "present",
                source="block_2_4",
                interpretation="Tail risk alert provides a proxy for left-tail vulnerability under liquidity events.",
            )
        )
        if corr_alert.get("limitations"):
            limitations.extend([f"Hidden exposure (2.4) — correlation_concentration: {x}" for x in corr_alert["limitations"]])
        if cl_alert.get("limitations"):
            limitations.extend([f"Hidden exposure (2.4) — credit_liquidity_risk: {x}" for x in cl_alert["limitations"]])
        if tail_alert.get("limitations"):
            limitations.extend([f"Hidden exposure (2.4) — tail_risk: {x}" for x in tail_alert["limitations"]])
        signals, min_w = _materialize_signals("liquidity_shock", metrics=metrics, thresholds_vars=thresholds_vars)
        row = _build_risk(
                "liquidity_shock",
                signals=signals,
                minimum_evaluable_weight=min_w,
                evidence=evidence,
                limitations=limitations,
            )
        row["linked_assets"] = (
            _linked_assets_from_alert(cl_alert, limit=2)
            + _linked_assets_from_alert(corr_alert, limit=2)
            + _linked_assets_from_alert(tail_alert, limit=2)
        )[:3]
        risks.append(row)

    def add_usd_shock() -> None:
        evidence: list[dict[str, Any]] = []
        limitations: list[str] = [
            "FX sensitivity is estimated only through exported factor diagnostics and currency breakdown; treat as a pre-stress hypothesis."
        ]

        def _block_usd_field(field: str, owner_block: str, reason: str) -> None:
            blocked_upstream_fields.append(
                {
                    "field": field,
                    "owner_block": owner_block,
                    "reason": reason,
                    "target_session": "session_04_usd_shock",
                }
            )

        if dominant_currency_weight is None:
            _block_usd_field(
                "block_2_1.capital_allocation_breakdown.by_currency",
                "block_2_1",
                "dominant_currency_weight_missing",
            )
            limitations.append("Dominant currency exposure is unavailable (Block 2.1 by_currency missing).")
        if usd_currency_weight is None:
            _block_usd_field(
                "block_2_1.capital_allocation_breakdown.by_currency.USD",
                "block_2_1",
                "usd_currency_weight_missing",
            )
            limitations.append("USD currency exposure is unavailable (Block 2.1 by_currency missing).")
        if investor_mismatch_flag is None:
            _block_usd_field(
                "block_2_2.investor_currency_or_block_2_1.investor_currency",
                "block_2_2",
                "investor_currency_mismatch_not_evaluable",
            )
            limitations.append("Investor-currency mismatch is not evaluable from available 2.1/2.2 fields.")
        if beta_usd is None:
            _block_usd_field("block_2_3.factor_beta_snapshot.beta_usd", "block_2_3", "beta_usd_missing")
            limitations.append("USD factor beta is unavailable in Block 2.3 export.")
        if usd_var_share is None:
            _block_usd_field(
                "block_2_3.factor_variance_contribution.contributions.USD",
                "block_2_3",
                "usd_factor_variance_share_missing",
            )
            limitations.append("USD factor variance share is unavailable in Block 2.3 export.")
        evidence.append(
            _evidence(
                metric="dominant_currency_weight",
                value=dominant_currency_weight,
                threshold_key=None,
                direction="missing" if dominant_currency_weight is None else "present",
                source="block_2_1",
                interpretation="Dominant currency exposure weight from Block 2.1 by_currency breakdown.",
            )
        )
        evidence.append(
            _evidence(
                metric="usd_currency_weight",
                value=usd_currency_weight,
                threshold_key=None,
                direction="missing" if usd_currency_weight is None else "present",
                source="block_2_1",
                interpretation="USD-labeled currency exposure weight from Block 2.1.",
            )
        )
        evidence.append(
            _evidence(
                metric="investor_currency_mismatch",
                value={"investor_currency": investor_currency, "dominant_currency_exposure": dominant_currency},
                threshold_key=None,
                direction="missing"
                if investor_mismatch_flag is None
                else ("above_threshold" if investor_mismatch_flag >= 0.5 else "below_threshold"),
                source="block_2_2",
                interpretation="Whether investor reporting currency differs from the dominant currency-exposure label.",
            )
        )
        evidence.append(
            _evidence(
                metric="beta_usd",
                value=beta_usd,
                threshold_key=None,
                direction="missing" if beta_usd is None else "present",
                source="block_2_3",
                interpretation="USD factor beta adds model-based FX sensitivity evidence when available.",
            )
        )
        evidence.append(
            _evidence(
                metric="usd_factor_variance_share",
                value=usd_var_share,
                threshold_key=None,
                direction="missing" if usd_var_share is None else "present",
                source="block_2_3",
                interpretation="USD factor variance share provides a model-based proxy for FX-driven variance when available.",
            )
        )
        signals, min_w = _materialize_signals("usd_shock", metrics=metrics, thresholds_vars=thresholds_vars)
        risks.append(
            _build_risk(
                "usd_shock",
                signals=signals,
                minimum_evaluable_weight=min_w,
                evidence=evidence,
                limitations=limitations,
            )
        )

    def add_commodity_shock() -> None:
        evidence: list[dict[str, Any]] = []
        limitations: list[str] = []
        evidence.append(
            _evidence(
                metric="commodity_weight",
                value=commodity_w,
                threshold_key=None,
                direction="missing" if commodity_w is None else "present",
                source="block_2_1",
                interpretation="Capital in commodity sleeves can drive sensitivity to commodity shocks.",
            )
        )
        evidence.append(
            _evidence(
                metric="real_assets_weight",
                value=real_assets_w,
                threshold_key=None,
                direction="missing" if real_assets_w is None else "present",
                source="block_2_1",
                interpretation="Real assets can move with commodities depending on the sleeve construction.",
            )
        )
        evidence.append(
            _evidence(
                metric="commodity_rc_pct",
                value=commodity_rc,
                threshold_key=None,
                direction="missing" if commodity_rc is None else "present",
                source="block_2_5",
                interpretation="Commodity risk contribution is a variance proxy for commodity sensitivity.",
            )
        )
        evidence.append(
            _evidence(
                metric="real_assets_rc_pct",
                value=real_assets_rc,
                threshold_key=None,
                direction="missing" if real_assets_rc is None else "present",
                source="block_2_5",
                interpretation="Real-assets risk contribution adds a variance proxy for real-asset sensitivity.",
            )
        )
        signals, min_w = _materialize_signals("commodity_shock", metrics=metrics, thresholds_vars=thresholds_vars)
        risks.append(
            _build_risk(
                "commodity_shock",
                signals=signals,
                minimum_evaluable_weight=min_w,
                evidence=evidence,
                limitations=limitations,
            )
        )

    def add_recession_severe() -> None:
        evidence: list[dict[str, Any]] = []
        limitations: list[str] = []
        evidence.append(
            _evidence(
                metric="equity_rc_pct",
                value=equity_rc,
                threshold_key=None,
                direction="missing" if equity_rc is None else "present",
                source="block_2_5",
                interpretation="Recessions often hit equity and cyclically sensitive sleeves.",
            )
        )
        evidence.append(
            _evidence(
                metric="credit_rc_pct",
                value=credit_rc,
                threshold_key=None,
                direction="missing" if credit_rc is None else "present",
                source="block_2_5",
                interpretation="Credit risk contribution can increase recession vulnerability through spread widening.",
            )
        )
        evidence.append(
            _evidence(
                metric="downside_beta",
                value=downside_beta,
                threshold_key=None,
                direction="missing" if downside_beta is None else "present",
                source="block_2_2",
                interpretation="Downside beta provides a behavior-based proxy for recession sensitivity.",
            )
        )
        evidence.append(
            _evidence(
                metric="tail_risk_score",
                value=tail_alert.get("score"),
                threshold_key=None,
                direction="missing" if tail_alert.get("score") is None else "present",
                source="block_2_4",
                interpretation="Tail risk alert score proxies left-tail vulnerability that often surfaces in recessions.",
            )
        )
        if tail_alert.get("limitations"):
            limitations.extend([f"Hidden exposure (2.4) — tail_risk: {x}" for x in tail_alert["limitations"]])
        signals, min_w = _materialize_signals("recession_severe", metrics=metrics, thresholds_vars=thresholds_vars)
        row = _build_risk(
                "recession_severe",
                signals=signals,
                minimum_evaluable_weight=min_w,
                evidence=evidence,
                limitations=limitations,
            )
        row["linked_assets"] = _linked_assets_from_alert(tail_alert)
        risks.append(row)

    # Keep output risk_types in the same order as RISK_TYPES.
    add_equity_shock()
    add_credit_shock()
    add_rates_shock()
    add_inflation_stagflation()
    add_liquidity_shock()
    add_usd_shock()
    add_commodity_shock()
    add_recession_severe()

    unavailable_count = sum(1 for r in risks if r.get("severity") == "Unavailable")
    if unavailable_count == len(risks):
        status = "unavailable"
        summary = "Portfolio weakness map is unavailable because required Blocks 2.1–2.5 evidence is missing."
    elif unavailable_count:
        status = "partial"
        summary = "Portfolio weakness map is partial; some risk types have insufficient evidence."
    else:
        status = "ok"
        summary = "Portfolio weakness map completed as a pre-stress hypothesis map using Blocks 2.1–2.5."

    next_tests_global: list[str] = []
    seen: set[str] = set()
    for risk in risks:
        for test in risk.get("next_tests") or []:
            t = str(test)
            if t and t not in seen:
                next_tests_global.append(t)
                seen.add(t)

    return {
        "block": "2.6_portfolio_weakness_map",
        "block_id": "2.6",
        "block_name": BLOCK_2_6_NAME,
        "status": status,
        "summary": summary,
        "data_quality_warnings": list(dict.fromkeys(warnings)),
        "metadata": {
            "rule_version": RULE_VERSION,
            "stress_lab_separation": "no_stress_pnl_or_attribution",
            "inputs": ["block_2_1", "block_2_2", "block_2_3", "block_2_4", "block_2_5"],
            "forbidden_stress_keys_detected": sorted(forbidden_found),
            "legacy_risk_aliases": dict(LEGACY_RISK_ALIASES),
            "diagnostics_meta": {
                "method": "rule_based_portfolio_weakness_map",
                "version": "v2",
                "ruleset": RULE_VERSION,
                "blocked_upstream_fields": blocked_upstream_fields,
            },
        },
        "risk_types": risks,
        "next_tests_global": next_tests_global,
    }


__all__ = [
    "BLOCK_2_6_ID",
    "BLOCK_2_6_NAME",
    "EVIDENCE_DIRECTIONS",
    "EVIDENCE_SOURCES",
    "FORBIDDEN_STRESS_KEYS",
    "RISK_TYPES",
    "RISK_RULE_TABLES",
    "RULE_VERSION",
    "STATUS_BANDS",
    "build_block_2_6_portfolio_weakness_map",
]

