"""Block 2.4 Hidden Exposure — rule-based product diagnostics.

This module is intentionally an adapter over already-built product blocks 2.1,
2.2, and 2.3.  It does not read generated artifacts, run Stress Lab, optimize,
generate candidates, or fit factor models.
"""
from __future__ import annotations

import math
from typing import Any

BLOCK_2_4_ID = "2.4_hidden_exposure"
BLOCK_2_4_NAME = "Hidden Exposure / Hidden Risk Detector"

ALERT_IDS: tuple[str, ...] = (
    "hidden_equity_beta",
    "duration_concentration",
    "credit_liquidity_risk",
    "correlation_concentration",
    "weak_hedge_behavior",
    "tail_risk",
)

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
    "taxonomy",
    "portfolio_analytics",
}

RULE_VERSION = "heuristic_v1"

ALERT_RULES: dict[str, dict[str, Any]] = {
    "hidden_equity_beta": {
        "minimum_evaluable_weight": 0.40,
        "signals": {
            "beta_portfolio": {"weight": 0.25, "moderate": 0.70, "high": 1.00, "abs": False},
            "downside_beta": {"weight": 0.25, "moderate": 0.90, "high": 1.20, "abs": False},
            "rolling_correlation": {"weight": 0.20, "moderate": 0.70, "high": 0.85, "abs": False},
            "beta_eq": {"weight": 0.30, "moderate": 0.35, "high": 0.65, "abs": True},
        },
        "next_tests": ["equity_shock", "liquidity_shock", "recession_severe"],
    },
    "duration_concentration": {
        "minimum_evaluable_weight": 0.35,
        "signals": {
            "rates_or_duration_weight": {"weight": 0.45, "moderate": 0.25, "high": 0.45, "abs": False},
            "fixed_income_weight": {"weight": 0.20, "moderate": 0.35, "high": 0.55, "abs": False},
            "beta_rr": {"weight": 0.35, "moderate": 0.25, "high": 0.50, "abs": True},
        },
        "next_tests": ["rates_shock", "inflation_stagflation"],
    },
    "credit_liquidity_risk": {
        "minimum_evaluable_weight": 0.35,
        "signals": {
            "credit_liquidity_weight": {"weight": 0.35, "moderate": 0.20, "high": 0.35, "abs": False},
            "risk_on_or_carry_weight": {"weight": 0.20, "moderate": 0.20, "high": 0.35, "abs": False},
            "beta_credit": {"weight": 0.25, "moderate": 0.25, "high": 0.50, "abs": True},
            "downside_beta": {"weight": 0.20, "moderate": 0.90, "high": 1.20, "abs": False},
        },
        "next_tests": ["credit_shock", "liquidity_shock", "recession_severe"],
    },
    "correlation_concentration": {
        "minimum_evaluable_weight": 0.35,
        "signals": {
            "highest_pair_correlation": {"weight": 0.45, "moderate": 0.75, "high": 0.90, "abs": False},
            "duplicate_exposure_weight": {"weight": 0.25, "moderate": 0.10, "high": 0.20, "abs": False},
            "dominant_main_risk_factor_weight": {"weight": 0.30, "moderate": 0.60, "high": 0.75, "abs": False},
        },
        "next_tests": ["equity_shock", "recession_severe", "liquidity_shock"],
    },
    "weak_hedge_behavior": {
        "minimum_evaluable_weight": 0.30,
        "signals": {
            "hedge_labeled_weight": {"weight": 0.25, "moderate": 0.15, "high": 0.30, "abs": False},
            "downside_beta": {"weight": 0.30, "moderate": 0.90, "high": 1.20, "abs": False},
            "rolling_correlation": {"weight": 0.25, "moderate": 0.70, "high": 0.85, "abs": False},
            "equity_or_credit_beta": {"weight": 0.20, "moderate": 0.35, "high": 0.65, "abs": True},
        },
        "next_tests": ["equity_shock", "recession_severe", "liquidity_shock", "inflation_stagflation"],
    },
    "tail_risk": {
        "minimum_evaluable_weight": 0.40,
        "signals": {
            "es_95": {"weight": 0.22, "moderate": -0.015, "high": -0.025, "adverse": "lte"},
            "es_99": {"weight": 0.16, "moderate": -0.025, "high": -0.040, "adverse": "lte"},
            "eee_10": {"weight": 0.10, "moderate": -0.030, "high": -0.060, "adverse": "lte"},
            "skewness": {"weight": 0.10, "moderate": -0.50, "high": -1.00, "adverse": "lte"},
            "kurtosis": {"weight": 0.10, "moderate": 4.0, "high": 7.0, "abs": False},
            "count_drawdowns_gt_10": {"weight": 0.10, "moderate": 1.0, "high": 3.0, "abs": False},
            "count_drawdowns_gt_20": {"weight": 0.08, "moderate": 1.0, "high": 2.0, "abs": False},
            "downside_beta": {"weight": 0.14, "moderate": 0.90, "high": 1.20, "abs": False},
        },
        "next_tests": ["recession_severe", "equity_shock", "liquidity_shock"],
    },
}

_ALERT_COPY: dict[str, dict[str, str]] = {
    "hidden_equity_beta": {
        "explanation": "The detector checks whether portfolio behavior is more equity-like than labels alone suggest.",
        "why_it_matters": "A diversified-looking portfolio can still fall like an equity portfolio in risk-off markets.",
    },
    "duration_concentration": {
        "explanation": "The detector checks whether fixed income, rates labels, or real-rate beta create hidden duration sensitivity.",
        "why_it_matters": "The main vulnerability may be rate sensitivity rather than headline equity exposure.",
    },
    "credit_liquidity_risk": {
        "explanation": "The detector checks whether income, carry, credit, or liquidity-sensitive exposure behaves like risk-on risk.",
        "why_it_matters": "Bond or income exposure can amplify losses when credit spreads and liquidity conditions worsen.",
    },
    "correlation_concentration": {
        "explanation": "The detector checks whether different holdings or labels still move together.",
        "why_it_matters": "Many tickers do not guarantee diversification if they share the same behavior or risk driver.",
    },
    "weak_hedge_behavior": {
        "explanation": "The detector gives a preliminary read on whether hedge-labeled exposure is likely to offset risk.",
        "why_it_matters": "A hedge label is not enough; protection must be checked later against stress and crisis behavior.",
    },
    "tail_risk": {
        "explanation": "The detector checks whether rare but large losses are visible in tail and drawdown diagnostics.",
        "why_it_matters": "Ordinary volatility can look acceptable while expected shortfall and drawdowns remain material.",
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


def _dominant_breakdown_weight(block_2_1: dict[str, Any] | None, dimension: str) -> float | None:
    rows = _path(block_2_1, "capital_allocation_breakdown", dimension)
    if not isinstance(rows, list) or not rows:
        return None
    values = [_pct_to_fraction(row.get("weight_pct")) for row in rows if isinstance(row, dict)]
    values = [v for v in values if v is not None]
    return max(values) if values else None


def _duplicate_exposure_weight(block_2_1: dict[str, Any] | None) -> float | None:
    rows = _path(block_2_1, "duplicate_exposure_flags")
    if not isinstance(rows, list):
        return None
    weights: list[float] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        for key in ("observed", "group_weight", "weight", "duplicate_weight"):
            value = _pct_to_fraction(row.get(key))
            if value is not None:
                weights.append(value)
                break
    return max(weights) if weights else 0.0


def _factor_beta(block_2_3: dict[str, Any] | None, key: str) -> float | None:
    return _as_float(_path(block_2_3, "factor_beta_snapshot", key))


def _factor_confidence(block_2_3: dict[str, Any] | None, key: str) -> str | None:
    value = _path(block_2_3, "factor_significance_confidence", key, "status")
    return str(value) if value else None


def _rolling_correlation(block_2_2: dict[str, Any] | None) -> float | None:
    return _as_float(
        _path(
            block_2_2,
            "rolling_diagnostics",
            "core_view",
            "rolling_beta_or_correlation",
            "latest_correlation",
        )
    )


def _top_pair_correlation(block_2_2: dict[str, Any] | None) -> float | None:
    rows = _path(block_2_2, "correlation_breakdown", "top3_highest_correlation_pairs")
    if not isinstance(rows, list) or not rows:
        return None
    values = [_as_float(row.get("correlation")) for row in rows if isinstance(row, dict)]
    values = [v for v in values if v is not None]
    return max(values) if values else None


def _evidence(
    *,
    metric: str,
    value: Any,
    threshold: Any,
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
        "threshold": threshold,
        "direction": direction,
        "source": source,
        "interpretation": interpretation,
    }


def _direction(value: float | None, rule: dict[str, Any]) -> str:
    if value is None:
        return "missing"
    moderate = float(rule["moderate"])
    adverse = rule.get("adverse")
    compare_value = abs(value) if rule.get("abs") else value
    if adverse == "lte":
        return "above_threshold" if compare_value <= moderate else "below_threshold"
    return "above_threshold" if compare_value >= moderate else "below_threshold"


def _score_signal(value: float | None, rule: dict[str, Any]) -> float | None:
    if value is None:
        return None
    moderate = float(rule["moderate"])
    high = float(rule["high"])
    adverse = rule.get("adverse")
    x = abs(value) if rule.get("abs") else value
    if adverse == "lte":
        if x > moderate:
            return max(0.0, min(39.0, (abs(x) / max(abs(moderate), 1e-12)) * 39.0))
        if x <= high:
            return 70.0 + min(30.0, (abs(x - high) / max(abs(high), 1e-12)) * 30.0)
        span = abs(high - moderate) or 1.0
        return 40.0 + ((moderate - x) / span) * 29.0
    if x < moderate:
        return max(0.0, min(39.0, (x / max(moderate, 1e-12)) * 39.0))
    if x >= high:
        return 70.0 + min(30.0, ((x - high) / max(abs(high), 1e-12)) * 30.0)
    span = high - moderate or 1.0
    return 40.0 + ((x - moderate) / span) * 29.0


def _score_to_status(score: float | None) -> str:
    if score is None:
        return "Unavailable"
    if score >= 70:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


def _confidence(evaluable_weight: float, score: int | None, warnings: list[str]) -> str:
    if score is None:
        return "unavailable"
    if evaluable_weight >= 0.75 and not warnings:
        return "high"
    if evaluable_weight >= 0.50:
        return "medium"
    return "low"


def _weighted_alert(
    alert_id: str,
    *,
    signal_values: dict[str, tuple[float | None, str, str]],
    evidence_extra: list[dict[str, Any]] | None = None,
    warnings: list[str] | None = None,
    insufficient_extra: list[str] | None = None,
    calculation_extra: list[str] | None = None,
) -> dict[str, Any]:
    rule_set = ALERT_RULES[alert_id]
    evidence: list[dict[str, Any]] = []
    weighted = 0.0
    evaluable_weight = 0.0
    insufficient = list(insufficient_extra or [])

    for metric, rule in rule_set["signals"].items():
        value, source, interpretation = signal_values.get(metric, (None, "block_2_2", f"{metric} missing."))
        direction = _direction(value, rule)
        threshold: Any
        if rule.get("adverse") == "lte":
            threshold = {"moderate_lte": rule["moderate"], "high_lte": rule["high"]}
        else:
            threshold = {"moderate_gte": rule["moderate"], "high_gte": rule["high"]}
        evidence.append(
            _evidence(
                metric=metric,
                value=value,
                threshold=threshold,
                direction=direction,
                source=source,
                interpretation=interpretation,
            )
        )
        component = _score_signal(value, rule)
        if component is None:
            insufficient.append(f"{metric} missing")
            continue
        weight = float(rule["weight"])
        weighted += component * weight
        evaluable_weight += weight

    evidence.extend(evidence_extra or [])
    min_weight = float(rule_set["minimum_evaluable_weight"])
    score: int | None
    if evaluable_weight < min_weight:
        score = None
        status = "Unavailable"
        insufficient.append(
            f"evaluable signal weight {round(evaluable_weight, 3)} below minimum {min_weight}"
        )
    else:
        score = int(round(max(0.0, min(100.0, weighted / evaluable_weight))))
        status = _score_to_status(score)

    data_quality_warnings = list(dict.fromkeys(warnings or []))
    notes = [
        f"ruleset={RULE_VERSION}",
        "score is a weighted average of available signal scores",
        f"evaluable_signal_weight={round(evaluable_weight, 3)}",
    ]
    notes.extend(calculation_extra or [])
    copy = _ALERT_COPY[alert_id]
    return {
        "status": status,
        "score": score,
        "evidence": evidence,
        "explanation": copy["explanation"],
        "why_it_matters": copy["why_it_matters"],
        "next_tests": list(rule_set["next_tests"]),
        "confidence": _confidence(evaluable_weight, score, data_quality_warnings),
        "data_quality_warnings": data_quality_warnings,
        "insufficient_evidence_reasons": list(dict.fromkeys(insufficient)),
        "calculation_notes": notes,
    }


def _hidden_equity_beta(block_2_2: dict[str, Any] | None, block_2_3: dict[str, Any] | None) -> dict[str, Any]:
    beta_eq = _factor_beta(block_2_3, "beta_eq")
    conf = _factor_confidence(block_2_3, "beta_eq")
    extra = []
    if conf:
        extra.append(
            _evidence(
                metric="beta_eq_confidence",
                value=conf,
                threshold="significant_or_weak_evidence",
                direction="present" if conf in {"significant", "weak_evidence"} else "conflicting",
                source="block_2_3",
                interpretation="Factor confidence qualifies the equity beta evidence.",
            )
        )
    return _weighted_alert(
        "hidden_equity_beta",
        signal_values={
            "beta_portfolio": (
                _as_float(_path(block_2_2, "benchmark_dependence", "beta_portfolio")),
                "block_2_2",
                "Portfolio beta to the configured benchmark.",
            ),
            "downside_beta": (
                _as_float(_path(block_2_2, "benchmark_dependence", "downside_beta")),
                "block_2_2",
                "Downside beta checks if market sensitivity rises in weak markets.",
            ),
            "rolling_correlation": (
                _rolling_correlation(block_2_2),
                "block_2_2",
                "Latest rolling correlation to the configured benchmark.",
            ),
            "beta_eq": (beta_eq, "block_2_3", "5Y equity factor beta from Block 2.3."),
        },
        evidence_extra=extra,
        calculation_extra=["equity beta thresholds are heuristic_v1 product diagnostics"],
    )


def _duration_concentration(block_2_1: dict[str, Any] | None, block_2_3: dict[str, Any] | None) -> dict[str, Any]:
    rates_weight = _breakdown_weight(block_2_1, "by_main_risk_factor", {"real_rates", "rates", "duration"})
    fixed_income = _breakdown_weight(block_2_1, "by_asset_class", {"fixed_income", "bonds", "bond"})
    return _weighted_alert(
        "duration_concentration",
        signal_values={
            "rates_or_duration_weight": (
                rates_weight,
                "block_2_1",
                "Capital weight tagged to rates/duration main risk factor.",
            ),
            "fixed_income_weight": (
                fixed_income,
                "block_2_1",
                "Fixed income allocation can carry duration exposure.",
            ),
            "beta_rr": (_factor_beta(block_2_3, "beta_rr"), "block_2_3", "Real-rates factor beta."),
        },
        warnings=[] if rates_weight is not None else ["duration_bucket not present in Block 2.1 product output; using main_risk_factor/fixed_income proxies"],
        calculation_extra=["duration thresholds are heuristic_v1 because live duration is not available in Block 2.1"],
    )


def _credit_liquidity_risk(block_2_1: dict[str, Any] | None, block_2_2: dict[str, Any] | None, block_2_3: dict[str, Any] | None) -> dict[str, Any]:
    credit = _breakdown_weight(block_2_1, "by_main_risk_factor", {"credit", "liquidity"})
    risk_roles = _breakdown_weight(block_2_1, "by_risk_role", {"risk_on", "carry", "liquidity"})
    return _weighted_alert(
        "credit_liquidity_risk",
        signal_values={
            "credit_liquidity_weight": (
                credit,
                "block_2_1",
                "Capital weight tagged to credit or liquidity main risk factors.",
            ),
            "risk_on_or_carry_weight": (
                risk_roles,
                "block_2_1",
                "Risk-role labels that indicate carry, liquidity, or risk-on behavior.",
            ),
            "beta_credit": (_factor_beta(block_2_3, "beta_credit"), "block_2_3", "Credit factor beta."),
            "downside_beta": (
                _as_float(_path(block_2_2, "benchmark_dependence", "downside_beta")),
                "block_2_2",
                "Downside beta can reveal risk-on behavior in bad markets.",
            ),
        },
        calculation_extra=["credit/liquidity thresholds are heuristic_v1 product diagnostics"],
    )


def _correlation_concentration(block_2_1: dict[str, Any] | None, block_2_2: dict[str, Any] | None) -> dict[str, Any]:
    pair = _top_pair_correlation(block_2_2)
    duplicate = _duplicate_exposure_weight(block_2_1)
    dominant = _dominant_breakdown_weight(block_2_1, "by_main_risk_factor")
    return _weighted_alert(
        "correlation_concentration",
        signal_values={
            "highest_pair_correlation": (
                pair,
                "block_2_2",
                "Highest pairwise holding correlation from Block 2.2.",
            ),
            "duplicate_exposure_weight": (
                duplicate,
                "block_2_1",
                "Duplicate exposure flags indicate holdings that may overlap economically.",
            ),
            "dominant_main_risk_factor_weight": (
                dominant,
                "block_2_1",
                "Dominant main-risk-factor allocation from taxonomy-derived breakdown.",
            ),
        },
        calculation_extra=["correlation concentration thresholds are heuristic_v1 product diagnostics"],
    )


def _weak_hedge_behavior(block_2_1: dict[str, Any] | None, block_2_2: dict[str, Any] | None, block_2_3: dict[str, Any] | None) -> dict[str, Any]:
    hedge_weight = _breakdown_weight(
        block_2_1,
        "by_risk_role",
        {"defensive", "crisis_hedge", "inflation_hedge"},
    )
    eq = _factor_beta(block_2_3, "beta_eq")
    credit = _factor_beta(block_2_3, "beta_credit")
    max_risk_beta = max([abs(v) for v in (eq, credit) if v is not None], default=None)
    return _weighted_alert(
        "weak_hedge_behavior",
        signal_values={
            "hedge_labeled_weight": (
                hedge_weight,
                "block_2_1",
                "Capital weight with defensive/crisis/inflation hedge risk roles.",
            ),
            "downside_beta": (
                _as_float(_path(block_2_2, "benchmark_dependence", "downside_beta")),
                "block_2_2",
                "High downside beta may mean hedge labels are not enough by themselves.",
            ),
            "rolling_correlation": (
                _rolling_correlation(block_2_2),
                "block_2_2",
                "High rolling correlation with benchmark weakens preliminary hedge confidence.",
            ),
            "equity_or_credit_beta": (
                max_risk_beta,
                "block_2_3",
                "Residual equity/credit sensitivity can dominate hedge-labeled sleeves.",
            ),
        },
        warnings=["preliminary_without_stress_lab"],
        calculation_extra=[
            "weak hedge behavior is preliminary_without_stress_lab",
            "does not claim actual hedge failure without stress contribution data",
            "weak hedge thresholds are heuristic_v1 product diagnostics",
        ],
    )


def _tail_risk(block_2_2: dict[str, Any] | None) -> dict[str, Any]:
    return _weighted_alert(
        "tail_risk",
        signal_values={
            "es_95": (
                _as_float(_path(block_2_2, "tail_risk_diagnostics", "es_95")),
                "portfolio_analytics",
                "Daily historical ES95 from Block 2.2 tail diagnostics.",
            ),
            "es_99": (
                _as_float(_path(block_2_2, "tail_risk_diagnostics", "es_99")),
                "portfolio_analytics",
                "Daily historical ES99 from Block 2.2 tail diagnostics.",
            ),
            "eee_10": (
                _as_float(_path(block_2_2, "tail_risk_diagnostics", "eee_10")),
                "portfolio_analytics",
                "Expected exceedance estimate at 10% when available.",
            ),
            "skewness": (
                _as_float(_path(block_2_2, "return_risk_metrics", "skewness")),
                "block_2_2",
                "Negative skewness can indicate left-tail asymmetry.",
            ),
            "kurtosis": (
                _as_float(_path(block_2_2, "return_risk_metrics", "kurtosis")),
                "block_2_2",
                "High kurtosis can indicate fat tails.",
            ),
            "count_drawdowns_gt_10": (
                _as_float(_path(block_2_2, "drawdown_diagnostics", "count_drawdowns_gt_10")),
                "block_2_2",
                "Count of drawdowns deeper than 10%.",
            ),
            "count_drawdowns_gt_20": (
                _as_float(_path(block_2_2, "drawdown_diagnostics", "count_drawdowns_gt_20")),
                "block_2_2",
                "Count of drawdowns deeper than 20%.",
            ),
            "downside_beta": (
                _as_float(_path(block_2_2, "benchmark_dependence", "downside_beta")),
                "block_2_2",
                "Downside beta adds tail-behavior context.",
            ),
        },
        calculation_extra=["tail risk thresholds are heuristic_v1 product diagnostics"],
    )


def _top_hidden_risks(alerts: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for alert_id, alert in alerts.items():
        score = alert.get("score")
        if isinstance(score, (int, float)):
            rows.append(
                {
                    "alert_id": alert_id,
                    "status": alert.get("status"),
                    "score": score,
                    "confidence": alert.get("confidence"),
                }
            )
    return sorted(rows, key=lambda row: (-row["score"], row["alert_id"]))[:3]


def build_block_2_4_hidden_exposure(
    block_2_1: dict[str, Any] | None,
    block_2_2: dict[str, Any] | None,
    block_2_3: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build product-facing Hidden Exposure diagnostics from Blocks 2.1–2.3 only."""
    inputs = [isinstance(block_2_1, dict), isinstance(block_2_2, dict), isinstance(block_2_3, dict)]
    data_quality_warnings: list[str] = []
    if not inputs[0]:
        data_quality_warnings.append("block_2_1 missing")
    if not inputs[1]:
        data_quality_warnings.append("block_2_2 missing")
    if not inputs[2]:
        data_quality_warnings.append("block_2_3 missing")

    alerts = {
        "hidden_equity_beta": _hidden_equity_beta(block_2_2, block_2_3),
        "duration_concentration": _duration_concentration(block_2_1, block_2_3),
        "credit_liquidity_risk": _credit_liquidity_risk(block_2_1, block_2_2, block_2_3),
        "correlation_concentration": _correlation_concentration(block_2_1, block_2_2),
        "weak_hedge_behavior": _weak_hedge_behavior(block_2_1, block_2_2, block_2_3),
        "tail_risk": _tail_risk(block_2_2),
    }

    unavailable_count = sum(1 for row in alerts.values() if row.get("status") == "Unavailable")
    if unavailable_count == len(alerts):
        status = "unavailable"
        summary = "Hidden exposure diagnostics are unavailable because required Blocks 2.1–2.3 evidence is missing."
    elif unavailable_count:
        status = "partial"
        summary = "Hidden exposure diagnostics are partial; some alerts have insufficient evidence."
    else:
        status = "ok"
        summary = "Hidden exposure diagnostics completed using rule-based evidence from Blocks 2.1, 2.2, and 2.3."

    return {
        "block": BLOCK_2_4_ID,
        "block_id": "2.4",
        "block_name": BLOCK_2_4_NAME,
        "status": status,
        "summary": summary,
        "alerts": alerts,
        "top_hidden_risks": _top_hidden_risks(alerts),
        "data_quality_warnings": data_quality_warnings,
        "diagnostics_meta": {
            "method": "rule_based_hidden_exposure_detector",
            "version": "v1",
            "ruleset": RULE_VERSION,
            "threshold_policy": "heuristic_v1",
            "signal_weights": {
                alert_id: {name: spec["weight"] for name, spec in rule["signals"].items()}
                for alert_id, rule in ALERT_RULES.items()
            },
            "status_bands": STATUS_BANDS,
            "does_not_optimize": True,
            "does_not_generate_candidates": True,
            "does_not_run_stress_lab": True,
            "does_not_recalculate_factor_models": True,
            "input_blocks": [
                "block_2_1_asset_allocation",
                "block_2_2_portfolio_metrics",
                "block_2_3_factor_exposure",
            ],
        },
    }


__all__ = [
    "ALERT_IDS",
    "ALERT_RULES",
    "BLOCK_2_4_ID",
    "BLOCK_2_4_NAME",
    "EVIDENCE_DIRECTIONS",
    "EVIDENCE_SOURCES",
    "STATUS_BANDS",
    "build_block_2_4_hidden_exposure",
]
