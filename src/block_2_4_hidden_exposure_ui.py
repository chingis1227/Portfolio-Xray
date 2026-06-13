"""Block 2.4 Hidden Exposure — UI Pareto view model (presentation only).

Maps `portfolio_xray.json` → `block_2_4_hidden_exposure` to compact Hidden Risk Cards.
Does not score alerts or read Stress Lab; see docs/specs/block_2_4_hidden_exposure_ui_pareto_spec.md.
"""
from __future__ import annotations

import re
from typing import Any

from src.block_2_4_hidden_exposure import ALERT_IDS

PARETO_VERSION = "hidden_risk_cards_pareto_v1"
SECTION_TITLE = "Hidden exposure"
MAX_TOP_CARDS = 3
MAX_KEY_EVIDENCE = 5
MAX_LINKED_ASSETS = 3
MAX_NEXT_TESTS = 3

CARD_TITLES: dict[str, str] = {
    "hidden_equity_beta": "Hidden Equity Beta",
    "duration_concentration": "Duration Concentration",
    "credit_liquidity_risk": "Credit / Liquidity Risk",
    "correlation_concentration": "Correlation Concentration",
    "weak_hedge_behavior": "Weak Hedge Behavior",
    "tail_risk": "Tail Risk",
}

RISK_LEVEL_BY_STATUS: dict[str, tuple[str, str]] = {
    "Low": ("low", "Low hidden risk"),
    "Medium": ("medium", "Medium hidden risk"),
    "High": ("high", "High hidden risk"),
    "Unavailable": ("unavailable", "Not enough data"),
}

SCENARIO_LABELS: dict[str, str] = {
    "equity_shock": "Equity shock",
    "rates_shock": "Rates shock",
    "inflation_stagflation": "Inflation / stagflation",
    "credit_shock": "Credit spread shock",
    "liquidity_shock": "Liquidity shock",
    "recession_severe": "Severe recession",
    "commodity_shock": "Commodity shock",
    "usd_shock": "USD shock",
    "volatility_spike": "Volatility spike",
}

METRIC_LABELS: dict[str, str] = {
    "beta_portfolio": "Portfolio beta vs benchmark",
    "downside_beta": "Downside beta",
    "beta_eq": "Equity factor beta (5Y)",
    "equity_weight": "Equity allocation weight",
    "risk_on_weight": "Risk-on allocation weight",
    "highest_pair_correlation": "Highest pairwise correlation",
    "duplicate_exposure_weight": "Duplicate exposure overlap",
    "max_drawdown": "Maximum drawdown",
    "hedge_labeled_weight": "Hedge-labeled weight",
    "hedge_gap_summary": "Stress hedge gap (summary)",
    "fixed_income_weight": "Fixed income weight",
    "rates_or_duration_weight": "Rates / duration weight",
    "beta_rr": "Real rates factor beta",
    "beta_inf": "Inflation factor beta",
    "beta_credit": "Credit factor beta",
    "credit_liquidity_weight": "Credit / liquidity weight",
    "risk_on_or_carry_weight": "Risk-on or carry weight",
    "avg_pairwise_correlation": "Average pairwise correlation",
    "lowest_pair_correlation": "Lowest pairwise correlation",
    "dominant_main_risk_factor_weight": "Dominant risk-factor weight",
    "es_95": "Expected shortfall (95%)",
    "es_99": "Expected shortfall (99%)",
    "var_95": "Value at risk (95%)",
    "var_99": "Value at risk (99%)",
    "downside_deviation": "Downside deviation",
    "pct_time_underwater": "Time underwater",
}

EVIDENCE_PRIORITY: dict[str, tuple[str, ...]] = {
    "hidden_equity_beta": (
        "beta_portfolio",
        "downside_beta",
        "beta_eq",
        "rolling_correlation",
        "equity_weight",
        "risk_on_weight",
    ),
    "duration_concentration": (
        "fixed_income_weight",
        "rates_or_duration_weight",
        "beta_rr",
        "beta_inf",
    ),
    "credit_liquidity_risk": (
        "beta_credit",
        "credit_liquidity_weight",
        "risk_on_or_carry_weight",
        "downside_beta",
    ),
    "correlation_concentration": (
        "highest_pair_correlation",
        "duplicate_exposure_weight",
        "dominant_main_risk_factor_weight",
        "avg_pairwise_correlation",
        "lowest_pair_correlation",
    ),
    "weak_hedge_behavior": (
        "hedge_labeled_weight",
        "equity_or_credit_beta",
        "downside_beta",
        "rolling_correlation",
        "hedge_gap_summary",
    ),
    "tail_risk": (
        "es_95",
        "es_99",
        "max_drawdown",
        "var_95",
        "var_99",
        "downside_deviation",
        "pct_time_underwater",
        "downside_beta",
    ),
}

SOURCE_HINTS: dict[str, str] = {
    "block_2_1": "Allocation",
    "block_2_2": "Portfolio metrics",
    "block_2_3": "Factor exposure",
    "block_3_stress": "Stress cross-check",
    "taxonomy": "Taxonomy",
    "portfolio_analytics": "Portfolio metrics",
}

_DIRECTION_RANK = {
    "above_threshold": 0,
    "conflicting": 1,
    "present": 2,
    "below_threshold": 3,
    "missing": 4,
}

_UNAVAILABLE_DIAGNOSIS = (
    "We do not have enough aligned data to assess this hidden risk dimension."
)


def build_hidden_risk_cards_pareto(block_2_4: dict[str, Any] | None) -> dict[str, Any]:
    """Build UI Pareto view model from Block 2.4 product JSON."""
    if not isinstance(block_2_4, dict):
        return _empty_pareto()

    alerts = block_2_4.get("alerts") if isinstance(block_2_4.get("alerts"), dict) else {}
    all_cards = [_build_card(alert_id, alerts.get(alert_id) or {}) for alert_id in ALERT_IDS]
    top_ids = _top_card_ids(block_2_4, alerts)
    top_cards = [card for card in all_cards if card["card_id"] in top_ids]
    top_cards.sort(key=lambda c: top_ids.index(c["card_id"]))

    return {
        "version": PARETO_VERSION,
        "section_title": SECTION_TITLE,
        "section_summary": str(block_2_4.get("summary") or "").strip(),
        "block_status_chip": str(block_2_4.get("status") or "unavailable"),
        "top_cards": top_cards,
        "all_cards": all_cards,
    }


def _empty_pareto() -> dict[str, Any]:
    return {
        "version": PARETO_VERSION,
        "section_title": SECTION_TITLE,
        "section_summary": "",
        "block_status_chip": "unavailable",
        "top_cards": [],
        "all_cards": [],
    }


def _top_card_ids(block_2_4: dict[str, Any], alerts: dict[str, Any]) -> list[str]:
    top_hidden = block_2_4.get("top_hidden_risks")
    if isinstance(top_hidden, list) and top_hidden:
        ids: list[str] = []
        for row in top_hidden[:MAX_TOP_CARDS]:
            if not isinstance(row, dict):
                continue
            alert_id = row.get("alert_id")
            if isinstance(alert_id, str) and alert_id in ALERT_IDS:
                ids.append(alert_id)
        if ids:
            return ids

    scored: list[tuple[int, str]] = []
    for alert_id in ALERT_IDS:
        alert = alerts.get(alert_id) if isinstance(alerts.get(alert_id), dict) else {}
        if str(alert.get("status") or "") == "Unavailable":
            continue
        score = alert.get("score")
        if isinstance(score, (int, float)) and not isinstance(score, bool):
            scored.append((int(score), alert_id))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [alert_id for _, alert_id in scored[:MAX_TOP_CARDS]]


def _build_card(alert_id: str, alert: dict[str, Any]) -> dict[str, Any]:
    status = str(alert.get("status") or "Unavailable")
    risk_level, risk_level_label = RISK_LEVEL_BY_STATUS.get(status, ("unavailable", "Not enough data"))
    if status == "High" and str(alert.get("confidence") or "").lower() == "low":
        risk_level, risk_level_label = ("medium", "Medium hidden risk")

    card: dict[str, Any] = {
        "card_id": alert_id,
        "card_title": CARD_TITLES.get(alert_id, alert_id.replace("_", " ").title()),
        "risk_level": risk_level,
        "risk_level_label": risk_level_label,
        "short_diagnosis": _short_diagnosis(alert),
        "key_evidence": _key_evidence(alert_id, alert.get("evidence")),
        "linked_assets": _linked_assets(alert.get("contributing_assets")),
        "next_tests": _next_tests(alert.get("next_tests")),
    }

    confidence = str(alert.get("confidence") or "").lower()
    if status == "Medium" and confidence == "low":
        card["indicative_only"] = True

    if alert_id == "weak_hedge_behavior":
        confirmation = str(alert.get("confirmation_status") or "")
        if confirmation == "preliminary":
            card["confirmation_badge"] = "Preliminary"
        elif confirmation == "confirmed":
            card["confirmation_badge"] = "Stress-checked"
        warnings = alert.get("data_quality_warnings")
        if isinstance(warnings, list) and "preliminary_without_stress_lab" in warnings:
            card["stress_lab_note"] = (
                "Confirm in Stress Lab before treating hedges as effective."
            )

    return card


def _short_diagnosis(alert: dict[str, Any]) -> str:
    status = str(alert.get("status") or "")
    if status == "Unavailable":
        reasons = alert.get("insufficient_evidence_reasons")
        if isinstance(reasons, list) and reasons:
            first = str(reasons[0]).strip()
            if first:
                return first if len(first) <= 200 else first[:197] + "..."
        return _UNAVAILABLE_DIAGNOSIS

    explanation = str(alert.get("explanation") or "").strip()
    if not explanation:
        return _UNAVAILABLE_DIAGNOSIS
    parts = re.split(r"(...<=[.!...])\s+", explanation, maxsplit=1)
    return parts[0].strip() if parts else explanation


def _key_evidence(alert_id: str, evidence: Any) -> list[dict[str, str]]:
    if not isinstance(evidence, list):
        return []

    priority = EVIDENCE_PRIORITY.get(alert_id, ())
    rank: dict[str, int] = {metric: idx for idx, metric in enumerate(priority)}

    def sort_key(row: dict[str, Any]) -> tuple[int, int, str]:
        metric = str(row.get("metric") or "")
        direction = str(row.get("direction") or "missing")
        return (
            rank.get(metric, len(priority) + 1),
            _DIRECTION_RANK.get(direction, 99),
            metric,
        )

    rows = [row for row in evidence if isinstance(row, dict)]
    rows.sort(key=sort_key)

    selected: list[dict[str, str]] = []
    for row in rows:
        if len(selected) >= MAX_KEY_EVIDENCE:
            break
        if str(row.get("direction") or "") == "missing" and len(selected) >= 3:
            continue
        ui_row = _evidence_row(row)
        if ui_row:
            selected.append(ui_row)
    return selected


def _evidence_row(row: dict[str, Any]) -> dict[str, str] | None:
    metric = str(row.get("metric") or "").strip()
    if not metric:
        return None
    label = METRIC_LABELS.get(metric, metric.replace("_", " ").title())
    value = row.get("value")
    interpretation = str(row.get("interpretation") or "").strip()
    value_display = _format_evidence_value(value)
    if interpretation and value_display:
        value_display = f"{value_display} — {interpretation}"
    elif interpretation:
        value_display = interpretation
    elif not value_display:
        value_display = "—"
    source = str(row.get("source") or "")
    return {
        "label": label,
        "value_display": value_display,
        "source_hint": SOURCE_HINTS.get(source, "Portfolio metrics"),
    }


def _format_evidence_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int, float)):
        if abs(value) < 1 and value != 0:
            return f"{value:.3f}".rstrip("0").rstrip(".")
        return f"{value:.2f}".rstrip("0").rstrip(".")
    if isinstance(value, dict):
        if "share" in value and "factor" in value:
            share = value.get("share")
            factor = value.get("factor")
            if isinstance(share, (int, float)):
                return f"{factor}: {float(share):.1%} share"
        return str(value)
    return str(value).strip()


def _linked_assets(contributing_assets: Any) -> list[dict[str, str]]:
    if not isinstance(contributing_assets, list):
        return []
    out: list[dict[str, str]] = []
    for row in contributing_assets[:MAX_LINKED_ASSETS]:
        if not isinstance(row, dict):
            continue
        ticker = str(row.get("ticker") or "").strip()
        if not ticker:
            continue
        weight_pct = row.get("weight_pct")
        weight_display = ""
        if isinstance(weight_pct, (int, float)) and not isinstance(weight_pct, bool):
            weight_display = f"{float(weight_pct) * 100:.1f}%"
        role_parts = [
            str(row.get("expected_role") or "").strip(),
            str(row.get("behavior_flag") or "").strip(),
        ]
        role_label = " · ".join(part for part in role_parts if part)
        out.append(
            {
                "ticker": ticker,
                "weight_display": weight_display,
                "role_label": role_label or str(row.get("expected_role") or ""),
            }
        )
    return out


def _next_tests(next_tests: Any) -> list[dict[str, str]]:
    if not isinstance(next_tests, list):
        return []
    out: list[dict[str, str]] = []
    for scenario_id in next_tests[:MAX_NEXT_TESTS]:
        if not isinstance(scenario_id, str) or not scenario_id.strip():
            continue
        sid = scenario_id.strip()
        label = SCENARIO_LABELS.get(sid, sid.replace("_", " ").title())
        out.append({"scenario_id": sid, "label": label})
    return out
