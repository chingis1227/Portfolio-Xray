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
RULE_VERSION = "heuristic_v1"

RISK_TYPES: tuple[str, ...] = (
    "equity_crash",
    "rates_up",
    "inflation_shock",
    "credit_spreads",
    "liquidity_shock",
    "usd_shock",
    "commodity_shock",
    "volatility_spike",
    "recession",
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
    "equity_crash": {
        "minimum_evaluable_weight": 0.55,
        "signals": [
            {"metric": "equity_weight", "weight": 0.35, "moderate": 0.35, "high": 0.55},
            {"metric": "downside_beta", "weight": 0.30, "moderate": 0.90, "high": 1.20},
            {"metric": "top1_rc_share", "weight": 0.20, "moderate": "thr_top1_mod", "high": "thr_top1_high"},
            {"metric": "hidden_equity_beta_score_frac", "weight": 0.15, "moderate": 0.40, "high": 0.70},
        ],
    },
    "rates_up": {
        "minimum_evaluable_weight": 0.55,
        "signals": [
            {"metric": "rates_duration_weight", "weight": 0.45, "moderate": 0.25, "high": 0.45},
            {"metric": "beta_rr_abs", "weight": 0.25, "moderate": 0.25, "high": 0.50},
            {"metric": "duration_concentration_score_frac", "weight": 0.20, "moderate": 0.40, "high": 0.70},
            {"metric": "top1_rc_share", "weight": 0.10, "moderate": "thr_top1_mod", "high": "thr_top1_high"},
        ],
    },
    "inflation_shock": {
        "minimum_evaluable_weight": 0.55,
        "signals": [
            {"metric": "inflation_linked_rc_pct", "weight": 0.35, "moderate": 0.05, "high": 0.15},
            {"metric": "commodity_weight", "weight": 0.35, "moderate": 0.05, "high": 0.15},
            {"metric": "real_assets_weight", "weight": 0.30, "moderate": 0.05, "high": 0.15},
        ],
    },
    "credit_spreads": {
        "minimum_evaluable_weight": 0.55,
        "signals": [
            {"metric": "credit_liquidity_weight", "weight": 0.40, "moderate": 0.20, "high": 0.35},
            {"metric": "credit_rc_pct", "weight": 0.35, "moderate": 0.20, "high": 0.35},
            {"metric": "credit_liquidity_risk_score_frac", "weight": 0.25, "moderate": 0.40, "high": 0.70},
        ],
    },
    "liquidity_shock": {
        "minimum_evaluable_weight": 0.55,
        "signals": [
            {"metric": "credit_rc_pct", "weight": 0.35, "moderate": 0.15, "high": 0.30},
            {"metric": "correlation_concentration_score_frac", "weight": 0.35, "moderate": 0.40, "high": 0.70},
            {"metric": "credit_liquidity_risk_score_frac", "weight": 0.30, "moderate": 0.40, "high": 0.70},
        ],
    },
    "usd_shock": {
        "minimum_evaluable_weight": 0.10,
        "signals": [],
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
    "volatility_spike": {
        "minimum_evaluable_weight": 0.55,
        "signals": [
            {"metric": "tail_risk_score_frac", "weight": 0.45, "moderate": 0.40, "high": 0.70},
            {"metric": "correlation_concentration_score_frac", "weight": 0.30, "moderate": 0.40, "high": 0.70},
            {"metric": "equity_rc_pct", "weight": 0.25, "moderate": 0.35, "high": 0.55},
        ],
    },
    "recession": {
        "minimum_evaluable_weight": 0.55,
        "signals": [
            {"metric": "equity_rc_pct", "weight": 0.40, "moderate": 0.35, "high": 0.55},
            {"metric": "credit_rc_pct", "weight": 0.30, "moderate": 0.20, "high": 0.35},
            {"metric": "downside_beta", "weight": 0.30, "moderate": 0.90, "high": 1.20},
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
    "equity_crash": {
        "title": "Equity crash risk",
        "why_it_matters": (
            "Equity crashes can dominate multi-asset portfolios when equity exposure is high or when "
            "diversifiers behave like equity in risk-off markets."
        ),
        "next_tests": ["equity_shock", "recession_severe", "liquidity_shock"],
    },
    "rates_up": {
        "title": "Rates up / duration risk",
        "why_it_matters": (
            "Rate shocks can hurt duration-sensitive sleeves even when the headline allocation looks balanced."
        ),
        "next_tests": ["rates_shock", "inflation_stagflation"],
    },
    "inflation_shock": {
        "title": "Inflation shock risk",
        "why_it_matters": (
            "Inflation shocks can pressure both bonds and equities while changing the role of real assets and "
            "inflation-linked exposure."
        ),
        "next_tests": ["inflation_stagflation", "commodity_shock"],
    },
    "credit_spreads": {
        "title": "Credit spreads widening",
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
    "volatility_spike": {
        "title": "Volatility spike risk",
        "why_it_matters": (
            "Volatility spikes can magnify drawdowns and reveal hidden correlation or leverage-like behavior."
        ),
        "next_tests": ["volatility_spike", "liquidity_shock"],
    },
    "recession": {
        "title": "Recession risk",
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

    copy = _RISK_COPY[risk_type]
    severity = _score_to_severity(score)
    explanation = (
        "This score is a pre-stress heuristic based on already-computed portfolio diagnostics."
        " It does not estimate scenario losses or attribution."
    )
    if severity == "Unavailable":
        explanation += " Required upstream evidence is missing or incomplete."
    else:
        explanation += " Use the suggested next tests to validate this hypothesis in Stress Test Lab."

    return {
        "risk_type": risk_type,
        "risk_title": copy["title"],
        "score_0_100": score,
        "severity": severity,
        "confidence": _confidence(evaluable_weight, score, limitations),
        "evidence": evidence,
        "explanation": explanation,
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
    rates_w = _breakdown_weight(block_2_1, "by_main_risk_factor", {"real_rates", "rates", "duration"})
    credit_w = _breakdown_weight(block_2_1, "by_main_risk_factor", {"credit", "liquidity"})
    commodity_w = _breakdown_weight(block_2_1, "by_asset_class", {"commodity"})
    real_assets_w = _breakdown_weight(block_2_1, "by_asset_class", {"real_assets"})

    downside_beta = _as_float(_path(block_2_2, "benchmark_dependence", "downside_beta"))
    beta_rr = _as_float(_path(block_2_3, "factor_beta_snapshot", "beta_rr"))

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

    commodity_rc = _bucket_share(block_2_5, "commodity", "risk_contribution_pct")
    real_assets_rc = _bucket_share(block_2_5, "real_assets", "risk_contribution_pct")
    infl_linked_rc = _bucket_share(block_2_5, "inflation_linked", "risk_contribution_pct")

    metrics: dict[str, Any] = {
        "equity_weight": equity_w,
        "rates_duration_weight": rates_w,
        "credit_liquidity_weight": credit_w,
        "commodity_weight": commodity_w,
        "real_assets_weight": real_assets_w,
        "downside_beta": downside_beta,
        "beta_rr_abs": None if beta_rr is None else abs(beta_rr),
        "equity_rc_pct": equity_rc,
        "credit_rc_pct": credit_rc,
        "top1_rc_share": top1_rc,
        "hidden_equity_beta_score_frac": None if he_score is None else he_score / 100.0,
        "duration_concentration_score_frac": None if dur_score is None else dur_score / 100.0,
        "credit_liquidity_risk_score_frac": None if cl_score is None else cl_score / 100.0,
        "correlation_concentration_score_frac": None if corr_score is None else corr_score / 100.0,
        "tail_risk_score_frac": None if tail_score is None else tail_score / 100.0,
        "commodity_rc_pct": commodity_rc,
        "real_assets_rc_pct": real_assets_rc,
        "inflation_linked_rc_pct": infl_linked_rc,
    }

    risks: list[dict[str, Any]] = []
    thresholds_vars = {"thr_top1_mod": thr_top1_mod, "thr_top1_high": thr_top1_high}

    def add_equity_crash() -> None:
        evidence: list[dict[str, Any]] = []
        limitations: list[str] = []
        if equity_w is None:
            limitations.append("equity weight not available from Block 2.1 breakdown")
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
                value=he_score,
                threshold_key=None,
                direction="missing" if he_score is None else "present",
                source="block_2_4",
                interpretation="Hidden-equity-beta alert summarizes multi-signal equity-like behavior.",
            )
        )

        signals, min_w = _materialize_signals("equity_crash", metrics=metrics, thresholds_vars=thresholds_vars)
        risks.append(
            _build_risk(
                "equity_crash",
                signals=signals,
                minimum_evaluable_weight=min_w,
                evidence=evidence,
                limitations=limitations,
            )
        )

    def add_rates_up() -> None:
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
                metric="duration_concentration_score",
                value=dur_score,
                threshold_key=None,
                direction="missing" if dur_score is None else "present",
                source="block_2_4",
                interpretation="Duration concentration alert summarizes multiple proxies for rate sensitivity.",
            )
        )
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
        signals, min_w = _materialize_signals("rates_up", metrics=metrics, thresholds_vars=thresholds_vars)
        risks.append(
            _build_risk(
                "rates_up",
                signals=signals,
                minimum_evaluable_weight=min_w,
                evidence=evidence,
                limitations=limitations,
            )
        )

    def add_inflation_shock() -> None:
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
        signals, min_w = _materialize_signals("inflation_shock", metrics=metrics, thresholds_vars=thresholds_vars)
        risks.append(
            _build_risk(
                "inflation_shock",
                signals=signals,
                minimum_evaluable_weight=min_w,
                evidence=evidence,
                limitations=limitations,
            )
        )

    def add_credit_spreads() -> None:
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
                metric="credit_liquidity_risk_score",
                value=cl_score,
                threshold_key=None,
                direction="missing" if cl_score is None else "present",
                source="block_2_4",
                interpretation="Credit/liquidity hidden-risk alert aggregates multiple proxies for risk-on credit behavior.",
            )
        )
        signals, min_w = _materialize_signals("credit_spreads", metrics=metrics, thresholds_vars=thresholds_vars)
        risks.append(
            _build_risk(
                "credit_spreads",
                signals=signals,
                minimum_evaluable_weight=min_w,
                evidence=evidence,
                limitations=limitations,
            )
        )

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
                value=corr_score,
                threshold_key=None,
                direction="missing" if corr_score is None else "present",
                source="block_2_4",
                interpretation="Higher correlation concentration can reduce diversification in liquidity stress.",
            )
        )
        evidence.append(
            _evidence(
                metric="credit_liquidity_risk_score",
                value=cl_score,
                threshold_key=None,
                direction="missing" if cl_score is None else "present",
                source="block_2_4",
                interpretation="Credit/liquidity hidden-risk alert acts as a proxy for liquidity fragility.",
            )
        )
        signals, min_w = _materialize_signals("liquidity_shock", metrics=metrics, thresholds_vars=thresholds_vars)
        risks.append(
            _build_risk(
                "liquidity_shock",
                signals=signals,
                minimum_evaluable_weight=min_w,
                evidence=evidence,
                limitations=limitations,
            )
        )

    def add_usd_shock() -> None:
        evidence: list[dict[str, Any]] = []
        limitations: list[str] = [
            "FX sensitivity is not directly estimated in Blocks 2.1–2.5; rely on Stress Test Lab for validation"
        ]
        evidence.append(
            _evidence(
                metric="usd_sensitivity",
                value=None,
                threshold_key=None,
                direction="missing",
                source="block_2_2",
                interpretation="No direct USD beta is available in Core MVP blocks.",
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

    def add_volatility_spike() -> None:
        evidence: list[dict[str, Any]] = []
        limitations: list[str] = ["volatility spike is proxied by tail/correlation diagnostics only"]
        evidence.append(
            _evidence(
                metric="tail_risk_score",
                value=tail_score,
                threshold_key=None,
                direction="missing" if tail_score is None else "present",
                source="block_2_4",
                interpretation="Tail risk alert score proxies left-tail vulnerability.",
            )
        )
        evidence.append(
            _evidence(
                metric="correlation_concentration_score",
                value=corr_score,
                threshold_key=None,
                direction="missing" if corr_score is None else "present",
                source="block_2_4",
                interpretation="Correlation concentration can worsen the impact of volatility spikes.",
            )
        )
        evidence.append(
            _evidence(
                metric="equity_rc_pct",
                value=equity_rc,
                threshold_key=None,
                direction="missing" if equity_rc is None else "present",
                source="block_2_5",
                interpretation="High equity risk contribution can amplify volatility spike sensitivity.",
            )
        )
        signals, min_w = _materialize_signals("volatility_spike", metrics=metrics, thresholds_vars=thresholds_vars)
        risks.append(
            _build_risk(
                "volatility_spike",
                signals=signals,
                minimum_evaluable_weight=min_w,
                evidence=evidence,
                limitations=limitations,
            )
        )

    def add_recession() -> None:
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
        signals, min_w = _materialize_signals("recession", metrics=metrics, thresholds_vars=thresholds_vars)
        risks.append(
            _build_risk(
                "recession",
                signals=signals,
                minimum_evaluable_weight=min_w,
                evidence=evidence,
                limitations=limitations,
            )
        )

    add_equity_crash()
    add_rates_up()
    add_inflation_shock()
    add_credit_spreads()
    add_liquidity_shock()
    add_usd_shock()
    add_commodity_shock()
    add_volatility_spike()
    add_recession()

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

