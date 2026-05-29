"""Block 2.4 Hidden Exposure — rule-based product diagnostics.

This module is intentionally an adapter over already-built product blocks 2.1,
2.2, and 2.3.  It does not read generated artifacts, run Stress Lab, optimize,
generate candidates, or fit factor models.
"""
from __future__ import annotations

import math
from typing import Any

from src.block_2_3_factor_exposure import PRODUCTION_BETA_KEYS

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
    "block_3_stress",
    "taxonomy",
    "portfolio_analytics",
}

CONFIRMATION_STATUSES = {
    "preliminary",
    "confirmed",
    "unavailable",
    "not_applicable",
}

HEDGE_LABELED_RISK_ROLES = frozenset({"defensive", "crisis_hedge", "inflation_hedge"})
WEAK_HEDGE_OOS_MAE_MODERATE = 0.05
WEAK_HEDGE_OOS_MAE_HIGH = 0.10
WEAK_HEDGE_OFFSET_COVERAGE_WEAK = 0.25
PCA_PC1_MODERATE = 0.40
PCA_PC1_HIGH = 0.60
LEGACY_PCA_RAW_SECTION = "correlation_or_common_factor_concentration"
LEGACY_PCA_RESIDUAL_SECTION = "residual_pca_concentration"

RULE_VERSION = "heuristic_v2"
CONFIDENCE_MODEL_VERSION = "v2"
MAX_CONTRIBUTING_ASSETS = 3
DIVERSIFYING_PAIR_CORR_THRESHOLD = 0.30
HIGH_AVG_PAIRWISE_CORR_THRESHOLD = 0.55
FACTOR_BETA_MODERATE_ABS = 0.35
FACTOR_BETA_HIGH_ABS = 0.50
FACTOR_VARIANCE_DOMINANT_SHARE = 0.25

_CONTRIBUTOR_NO_PER_ASSET_BETA_LIMITATION = (
    "Per-asset factor betas are not computed in Block 2.4; contributing_assets labels use "
    "Block 2.1 weights and taxonomy proxies only."
)
_CONTRIBUTOR_TAXONOMY_UNAVAILABLE_LIMITATION = (
    "taxonomy_rows were not available at wire time; contributing_assets use capital weights only."
)

BLOCKED_UPSTREAM_FIELDS: tuple[dict[str, str], ...] = (
    {
        "field": "duration_bucket",
        "reason": "Not aggregated in Block 2.1 Core MVP product surface.",
        "owner_block": "block_2_1",
        "target_session": "04b",
    },
    {
        "field": "credit_quality",
        "reason": "Not aggregated in Block 2.1 Core MVP product surface.",
        "owner_block": "block_2_1",
        "target_session": "04b",
    },
    {
        "field": "by_subtype",
        "reason": "Credit-sensitive subtype weights are not in Block 2.1 breakdown.",
        "owner_block": "block_2_1",
        "target_session": "04b",
    },
    {
        "field": "issuer",
        "reason": "Issuer concentration is not aggregated in Block 2.1.",
        "owner_block": "block_2_1",
        "target_session": "04b",
    },
    {
        "field": "thematic_primary",
        "reason": "Thematic overlap is not aggregated in Block 2.1.",
        "owner_block": "block_2_1",
        "target_session": "04b",
    },
    {
        "field": "rolling_correlation_instability",
        "reason": "Rolling correlation instability summary is not in Block 2.2 product surface.",
        "owner_block": "block_2_2",
        "target_session": "04b",
    },
    {
        "field": "rolling_rates_beta",
        "reason": "Rolling rates beta is not in Block 2.2/2.3 product surface.",
        "owner_block": "block_2_2",
        "target_session": "04b",
    },
    {
        "field": "asset_level_credit_equity_correlation",
        "reason": "Asset-level credit-equity correlation is outside Core MVP product blocks.",
        "owner_block": "n/a",
        "target_session": "overengineer",
    },
    {
        "field": "per_asset_tail_es",
        "reason": "Per-asset tail ES is not in Block 2.2 product surface.",
        "owner_block": "block_2_2",
        "target_session": "advanced",
    },
)

_ALERT_LIMITATIONS: dict[str, list[str]] = {
    "hidden_equity_beta": [],
    "duration_concentration": [
        "duration_bucket is not aggregated in Block 2.1; rates sensitivity uses "
        "main_risk_factor and fixed_income proxies only."
    ],
    "credit_liquidity_risk": [
        "credit_quality and credit-sensitive subtype weights are not aggregated in "
        "Block 2.1 product output."
    ],
    "correlation_concentration": [
        "Full FX factor decomposition is not in Core MVP; currency evidence uses Block 2.1 "
        "by_currency and concentration_flags only.",
        "PCA common-factor cluster concentration is not scored in Block 2.4 product alerts; "
        "when portfolio_pca is available, interpret legacy sections.hidden_risk_detector "
        f"categories {LEGACY_PCA_RAW_SECTION!r} and {LEGACY_PCA_RESIDUAL_SECTION!r} "
        "(wire-time cross-ref evidence only).",
    ],
    "weak_hedge_behavior": [
        "Hedge effectiveness is preliminary without Stress Lab confirmation; this alert "
        "does not claim actual hedge failure."
    ],
    "tail_risk": [
        "Rolling Sharpe instability is not exported in Block 2.2 product surface; "
        "vol_of_vol and rel_vol_of_vol are used as volatility-regime proxy evidence only.",
        "Formal sudden volatility-regime detection is outside Core MVP; interpret rolling "
        "volatility latest as indicative, not a regime classifier.",
    ],
}

# Block 2.2 warning substrings propagated to alerts that depend on Block 2.2 metrics.
_BLOCK_22_WARNING_PROPAGATION: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "short history",
        (
            "hidden_equity_beta",
            "credit_liquidity_risk",
            "correlation_concentration",
            "weak_hedge_behavior",
            "tail_risk",
        ),
    ),
    (
        "tail risk",
        ("tail_risk",),
    ),
    (
        "correlation breakdown",
        (
            "correlation_concentration",
            "hidden_equity_beta",
            "weak_hedge_behavior",
        ),
    ),
)

# Production betas used for confidence v2 factor-signal checks per alert.
_ALERT_FACTOR_BETA_KEYS: dict[str, tuple[str, ...]] = {
    "hidden_equity_beta": ("beta_eq", "beta_us_growth"),
    "duration_concentration": ("beta_rr", "beta_inf"),
    "credit_liquidity_risk": ("beta_credit",),
    "correlation_concentration": (),
    "weak_hedge_behavior": ("beta_eq", "beta_credit", "beta_usd", "beta_cmd", "beta_vix", "beta_rr"),
    "tail_risk": ("beta_vix",),
}

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
            "es_95": {"weight": 0.10, "moderate": -0.015, "high": -0.025, "adverse": "lte"},
            "es_99": {"weight": 0.08, "moderate": -0.025, "high": -0.040, "adverse": "lte"},
            "var_95": {"weight": 0.10, "moderate": -0.012, "high": -0.020, "adverse": "lte"},
            "var_99": {"weight": 0.08, "moderate": -0.020, "high": -0.035, "adverse": "lte"},
            "downside_deviation": {"weight": 0.08, "moderate": 0.08, "high": 0.12, "abs": False},
            "max_drawdown": {"weight": 0.12, "moderate": -0.12, "high": -0.20, "adverse": "lte"},
            "pct_time_underwater": {"weight": 0.10, "moderate": 0.25, "high": 0.45, "abs": False},
            "longest_underwater_months": {"weight": 0.08, "moderate": 12.0, "high": 24.0, "abs": False},
            "unrecovered_drawdown": {"weight": 0.08, "moderate": 0.5, "high": 1.0, "abs": False},
            "count_drawdowns_gt_5": {"weight": 0.05, "moderate": 1.0, "high": 3.0, "abs": False},
            "count_drawdowns_gt_10": {"weight": 0.05, "moderate": 1.0, "high": 3.0, "abs": False},
            "downside_beta": {"weight": 0.08, "moderate": 0.90, "high": 1.20, "abs": False},
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
    _, weight = _dominant_breakdown_entry(block_2_1, dimension)
    return weight


def _dominant_breakdown_entry(
    block_2_1: dict[str, Any] | None,
    dimension: str,
) -> tuple[str | None, float | None]:
    rows = _path(block_2_1, "capital_allocation_breakdown", dimension)
    if not isinstance(rows, list) or not rows:
        return None, None
    best_name: str | None = None
    best_weight: float | None = None
    for row in rows:
        if not isinstance(row, dict):
            continue
        weight = _pct_to_fraction(row.get("weight_pct"))
        if weight is None:
            continue
        name = str(row.get("name") or "").strip()
        if best_weight is None or weight > best_weight:
            best_weight = weight
            best_name = name or None
    return best_name, best_weight


def _breakdown_single_label_weight(
    block_2_1: dict[str, Any] | None,
    dimension: str,
    label: str,
) -> float | None:
    rows = _path(block_2_1, "capital_allocation_breakdown", dimension)
    if not isinstance(rows, list):
        return None
    target = label.strip().lower()
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "").strip().lower()
        if name == target:
            return _pct_to_fraction(row.get("weight_pct"))
    return None


def _concentration_flags(block_2_1: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows = _path(block_2_1, "concentration_flags")
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _concentration_flags_by_id(block_2_1: dict[str, Any] | None, flag_ids: set[str]) -> list[dict[str, Any]]:
    return [row for row in _concentration_flags(block_2_1) if str(row.get("flag_id") or "") in flag_ids]


def _concentration_flag_evidence(
    block_2_1: dict[str, Any] | None,
    *,
    flag_ids: set[str],
    metric: str,
    interpretation: str,
) -> dict[str, Any] | None:
    flags = _concentration_flags_by_id(block_2_1, flag_ids)
    if not flags:
        return None
    return _evidence(
        metric=metric,
        value=flags,
        threshold="concentration_flag_present",
        direction="present",
        source="block_2_1",
        interpretation=interpretation,
    )


def _investor_currency(
    block_2_1: dict[str, Any] | None,
    block_2_2: dict[str, Any] | None,
) -> str | None:
    for doc in (block_2_2, block_2_1):
        if not isinstance(doc, dict):
            continue
        value = doc.get("investor_currency")
        if value is None:
            continue
        text = str(value).strip().upper()
        if text and text != "UNKNOWN":
            return text
    return None


def _investor_currency_mismatch(
    block_2_1: dict[str, Any] | None,
    block_2_2: dict[str, Any] | None,
) -> bool | None:
    investor = _investor_currency(block_2_1, block_2_2)
    dominant_label, _ = _dominant_breakdown_entry(block_2_1, "by_currency")
    if investor is None or not dominant_label:
        return None
    dominant = str(dominant_label).strip().upper()
    if not dominant or dominant == "UNKNOWN":
        return None
    return investor != dominant


def _numeric_evidence_direction(value: float, *, moderate: float, high: float) -> str:
    if value >= high:
        return "above_threshold"
    if value >= moderate:
        return "above_threshold"
    return "below_threshold"


def _equity_taxonomy_evidence(block_2_1: dict[str, Any] | None) -> list[dict[str, Any]]:
    extra: list[dict[str, Any]] = []
    equity_weight = _breakdown_weight(block_2_1, "by_asset_class", {"equity", "stocks", "stock"})
    if equity_weight is not None:
        extra.append(
            _evidence(
                metric="equity_weight",
                value=equity_weight,
                threshold={"moderate_gte": 0.35, "high_gte": 0.55},
                direction=_numeric_evidence_direction(equity_weight, moderate=0.35, high=0.55),
                source="block_2_1",
                interpretation="Equity asset-class weight from Block 2.1 capital breakdown.",
            )
        )
    risk_on_weight = _breakdown_weight(block_2_1, "by_risk_role", {"risk_on"})
    if risk_on_weight is not None:
        extra.append(
            _evidence(
                metric="risk_on_weight",
                value=risk_on_weight,
                threshold={"moderate_gte": 0.20, "high_gte": 0.35},
                direction=_numeric_evidence_direction(risk_on_weight, moderate=0.20, high=0.35),
                source="block_2_1",
                interpretation="Risk-on role weight from Block 2.1 taxonomy-derived breakdown.",
            )
        )
    return extra


def _currency_concentration_evidence(
    block_2_1: dict[str, Any] | None,
    block_2_2: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    extra: list[dict[str, Any]] = []
    dominant_label, dominant_weight = _dominant_breakdown_entry(block_2_1, "by_currency")
    if dominant_weight is not None:
        extra.append(
            _evidence(
                metric="dominant_currency_weight",
                value=dominant_weight,
                threshold={"moderate_gte": 0.70, "high_gte": 0.85},
                direction=_numeric_evidence_direction(dominant_weight, moderate=0.70, high=0.85),
                source="block_2_1",
                interpretation=(
                    f"Dominant currency exposure ({dominant_label or 'unknown'}) "
                    "from Block 2.1 by_currency breakdown."
                ),
            )
        )
    usd_weight = _breakdown_single_label_weight(block_2_1, "by_currency", "USD")
    if usd_weight is not None:
        extra.append(
            _evidence(
                metric="usd_exposure_weight",
                value=usd_weight,
                threshold={"moderate_gte": 0.70, "high_gte": 0.85},
                direction=_numeric_evidence_direction(usd_weight, moderate=0.70, high=0.85),
                source="block_2_1",
                interpretation="USD-labeled currency exposure weight from Block 2.1.",
            )
        )
    currency_flag = _concentration_flag_evidence(
        block_2_1,
        flag_ids={"single_currency_dominance"},
        metric="single_currency_dominance_flags",
        interpretation="Block 2.1 concentration flags for single-currency dominance.",
    )
    if currency_flag is not None:
        extra.append(currency_flag)
    mismatch = _investor_currency_mismatch(block_2_1, block_2_2)
    if mismatch is not None:
        investor = _investor_currency(block_2_1, block_2_2)
        dominant_label, _ = _dominant_breakdown_entry(block_2_1, "by_currency")
        extra.append(
            _evidence(
                metric="investor_currency_mismatch",
                value=mismatch,
                threshold={
                    "investor_currency": investor,
                    "dominant_currency_exposure": dominant_label,
                },
                direction="present" if mismatch else "below_threshold",
                source="block_2_2",
                interpretation=(
                    "Whether investor reporting currency differs from the dominant "
                    "currency-exposure label in Block 2.1."
                ),
            )
        )
    return extra


def _normalize_taxonomy_rows(
    taxonomy_rows: dict[str, dict[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    if not isinstance(taxonomy_rows, dict):
        return {}
    return {str(k).upper(): v for k, v in taxonomy_rows.items() if isinstance(v, dict)}


def _taxonomy_for_ticker(
    ticker: str,
    taxonomy_rows: dict[str, dict[str, Any]] | None,
) -> dict[str, Any]:
    rows = _normalize_taxonomy_rows(taxonomy_rows)
    key = str(ticker).upper()
    return rows.get(key) or rows.get(str(ticker)) or {}


def _tax_label(tax: dict[str, Any], field: str, *, default: str = "unknown") -> str:
    value = tax.get(field)
    if value is None:
        return default
    text = str(value).strip().lower()
    return text or default


def _tax_risk_roles(tax: dict[str, Any]) -> set[str]:
    value = tax.get("risk_role")
    if isinstance(value, list):
        return {str(v).strip().lower() for v in value if str(v).strip()} or {"unknown"}
    if isinstance(value, str) and value.strip():
        return {value.strip().lower()}
    return {"unknown"}


def _holdings_from_block_2_1(
    block_2_1: dict[str, Any] | None,
    taxonomy_rows: dict[str, dict[str, Any]] | None,
) -> list[tuple[str, float, dict[str, Any]]]:
    rows = _path(block_2_1, "capital_allocation_breakdown", "by_asset")
    if not isinstance(rows, list):
        return []
    holdings: list[tuple[str, float, dict[str, Any]]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        ticker = str(row.get("name") or "").strip().upper()
        if not ticker:
            continue
        weight = _pct_to_fraction(row.get("weight_pct"))
        if weight is None or weight <= 0:
            continue
        holdings.append((ticker, weight, _taxonomy_for_ticker(ticker, taxonomy_rows)))
    return sorted(holdings, key=lambda item: (-item[1], item[0]))


def _contributing_asset_row(
    ticker: str,
    weight_frac: float,
    tax: dict[str, Any],
    *,
    behavior_flag: str,
    expected_role: str | None = None,
) -> dict[str, Any]:
    role = expected_role or sorted(_tax_risk_roles(tax))[0]
    return {
        "ticker": ticker,
        "weight_pct": round(weight_frac, 3),
        "expected_role": role,
        "behavior_flag": behavior_flag,
        "source": "block_2_1",
    }


def _top_contributors(
    candidates: list[dict[str, Any]],
    *,
    max_count: int = MAX_CONTRIBUTING_ASSETS,
) -> list[dict[str, Any]]:
    return candidates[:max_count]


def _is_equity_asset_class(tax: dict[str, Any]) -> bool:
    return _tax_label(tax, "asset_class") in {"equity", "stocks", "stock"}


def _is_equity_main_risk_factor(tax: dict[str, Any]) -> bool:
    return _tax_label(tax, "main_risk_factor") == "equity"


def _contributors_hidden_equity_beta(
    holdings: list[tuple[str, float, dict[str, Any]]],
) -> list[dict[str, Any]]:
    ranked: list[tuple[bool, float, str, float, dict[str, Any]]] = []
    for ticker, weight, tax in holdings:
        if not (_is_equity_asset_class(tax) or _is_equity_main_risk_factor(tax)):
            continue
        equity_like = _is_equity_main_risk_factor(tax) and not _is_equity_asset_class(tax)
        ranked.append((equity_like, weight, ticker, weight, tax))
    ranked.sort(key=lambda row: (-int(row[0]), -row[1], row[2]))
    out: list[dict[str, Any]] = []
    for equity_like, _, ticker, weight, tax in ranked:
        flag = "equity_like_non_equity_label" if equity_like else "equity_aligned"
        out.append(_contributing_asset_row(ticker, weight, tax, behavior_flag=flag))
    return _top_contributors(out)


def _contributors_duration_concentration(
    holdings: list[tuple[str, float, dict[str, Any]]],
) -> list[dict[str, Any]]:
    duration_mrf = {"real_rates", "rates", "duration"}
    fi_class = {"fixed_income", "bonds", "bond"}
    ranked: list[tuple[int, float, str, float, dict[str, Any]]] = []
    for ticker, weight, tax in holdings:
        mrf = _tax_label(tax, "main_risk_factor")
        ac = _tax_label(tax, "asset_class")
        if mrf not in duration_mrf and ac not in fi_class:
            continue
        priority = 2 if mrf in duration_mrf else 1
        ranked.append((priority, weight, ticker, weight, tax))
    ranked.sort(key=lambda row: (-row[0], -row[1], row[2]))
    return _top_contributors(
        [
            _contributing_asset_row(
                ticker,
                weight,
                tax,
                behavior_flag="rates_duration_exposure",
                expected_role=_tax_label(tax, "main_risk_factor"),
            )
            for _, _, ticker, weight, tax in ranked
        ]
    )


def _contributors_credit_liquidity_risk(
    holdings: list[tuple[str, float, dict[str, Any]]],
) -> list[dict[str, Any]]:
    credit_mrf = {"credit", "liquidity"}
    risk_roles = {"risk_on", "carry", "liquidity"}
    ranked: list[tuple[int, float, str, float, dict[str, Any]]] = []
    for ticker, weight, tax in holdings:
        mrf = _tax_label(tax, "main_risk_factor")
        roles = _tax_risk_roles(tax)
        if mrf not in credit_mrf and not roles.intersection(risk_roles):
            continue
        priority = 2 if mrf in credit_mrf else 1
        ranked.append((priority, weight, ticker, weight, tax))
    ranked.sort(key=lambda row: (-row[0], -row[1], row[2]))
    return _top_contributors(
        [
            _contributing_asset_row(
                ticker,
                weight,
                tax,
                behavior_flag="credit_liquidity_sensitive",
                expected_role=sorted(_tax_risk_roles(tax))[0],
            )
            for _, _, ticker, weight, tax in ranked
        ]
    )


def _priority_tickers_correlation(
    block_2_1: dict[str, Any] | None,
    block_2_2: dict[str, Any] | None,
) -> list[str]:
    order: list[str] = []
    seen: set[str] = set()
    for group in _duplicate_exposure_rows(block_2_1):
        for ticker in group.get("tickers") or []:
            symbol = str(ticker).strip().upper()
            if symbol and symbol not in seen:
                seen.add(symbol)
                order.append(symbol)
    for pair_key in ("top3_highest_correlation_pairs", "top3_lowest_correlation_pairs"):
        for row in _correlation_pair_rows(block_2_2, pair_key):
            for key in ("ticker_a", "ticker_b"):
                symbol = str(row.get(key) or "").strip().upper()
                if symbol and symbol not in seen:
                    seen.add(symbol)
                    order.append(symbol)
    return order


def _contributors_correlation_concentration(
    holdings: list[tuple[str, float, dict[str, Any]]],
    block_2_1: dict[str, Any] | None,
    block_2_2: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    by_ticker = {ticker: (weight, tax) for ticker, weight, tax in holdings}
    duplicate_tickers = {
        str(t).upper()
        for group in _duplicate_exposure_rows(block_2_1)
        for t in (group.get("tickers") or [])
        if str(t).strip()
    }
    out: list[dict[str, Any]] = []
    for ticker in _priority_tickers_correlation(block_2_1, block_2_2):
        if ticker not in by_ticker:
            continue
        weight, tax = by_ticker[ticker]
        flag = "duplicate_exposure_group_member" if ticker in duplicate_tickers else "high_correlation_pair_member"
        out.append(_contributing_asset_row(ticker, weight, tax, behavior_flag=flag))
        if len(out) >= MAX_CONTRIBUTING_ASSETS:
            return out
    for ticker, weight, tax in holdings:
        if any(row["ticker"] == ticker for row in out):
            continue
        out.append(
            _contributing_asset_row(
                ticker,
                weight,
                tax,
                behavior_flag="largest_capital_weight_fallback",
            )
        )
        if len(out) >= MAX_CONTRIBUTING_ASSETS:
            break
    return out


def _contributors_weak_hedge_behavior(
    holdings: list[tuple[str, float, dict[str, Any]]],
) -> list[dict[str, Any]]:
    hedge_roles = {"defensive", "crisis_hedge", "inflation_hedge"}
    ranked: list[tuple[str, float, dict[str, Any]]] = []
    for ticker, weight, tax in holdings:
        if not _tax_risk_roles(tax).intersection(hedge_roles):
            continue
        ranked.append((ticker, weight, tax))
    ranked.sort(key=lambda row: (-row[1], row[0]))
    return _top_contributors(
        [
            _contributing_asset_row(
                ticker,
                weight,
                tax,
                behavior_flag="hedge_labeled",
                expected_role=sorted(_tax_risk_roles(tax).intersection(hedge_roles))[0],
            )
            for ticker, weight, tax in ranked
        ]
    )


def _contributors_tail_risk(
    holdings: list[tuple[str, float, dict[str, Any]]],
) -> list[dict[str, Any]]:
    return _top_contributors(
        [
            _contributing_asset_row(
                ticker,
                weight,
                tax,
                behavior_flag="largest_capital_weight",
                expected_role=_tax_label(tax, "asset_class"),
            )
            for ticker, weight, tax in holdings
        ]
    )


def _attach_contributing_assets(
    alerts: dict[str, dict[str, Any]],
    *,
    block_2_1: dict[str, Any] | None,
    block_2_2: dict[str, Any] | None,
    block_2_3: dict[str, Any] | None,
    taxonomy_rows: dict[str, dict[str, Any]] | None,
) -> None:
    holdings = _holdings_from_block_2_1(block_2_1, taxonomy_rows)
    contributor_limitations = [_CONTRIBUTOR_NO_PER_ASSET_BETA_LIMITATION]
    if not _normalize_taxonomy_rows(taxonomy_rows):
        contributor_limitations.append(_CONTRIBUTOR_TAXONOMY_UNAVAILABLE_LIMITATION)

    builders = {
        "hidden_equity_beta": lambda: _contributors_hidden_equity_beta(holdings),
        "duration_concentration": lambda: _contributors_duration_concentration(holdings),
        "credit_liquidity_risk": lambda: _contributors_credit_liquidity_risk(holdings),
        "correlation_concentration": lambda: _contributors_correlation_concentration(
            holdings, block_2_1, block_2_2
        ),
        "weak_hedge_behavior": lambda: _contributors_weak_hedge_behavior(holdings),
        "tail_risk": lambda: _contributors_tail_risk(holdings),
    }
    for alert_id, builder in builders.items():
        alert = alerts[alert_id]
        alert["contributing_assets"] = builder()
        alert["limitations"] = list(
            dict.fromkeys(list(alert.get("limitations") or []) + contributor_limitations)
        )


def _duplicate_exposure_rows(block_2_1: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows = _path(block_2_1, "duplicate_exposure_flags")
    if not isinstance(rows, list):
        return []
    out: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        weight = None
        for key in ("combined_weight", "combined_weight_pct", "observed", "group_weight", "weight", "duplicate_weight"):
            weight = _pct_to_fraction(row.get(key))
            if weight is not None:
                break
        out.append(
            {
                "duplicate_group_id": row.get("duplicate_group_id"),
                "tickers": row.get("tickers"),
                "canonical_ticker": row.get("canonical_ticker"),
                "combined_weight": weight,
                "severity": row.get("severity"),
            }
        )
    return out


def _duplicate_exposure_weight(block_2_1: dict[str, Any] | None) -> float | None:
    rows = _duplicate_exposure_rows(block_2_1)
    if not rows and _path(block_2_1, "duplicate_exposure_flags") is None:
        return None
    weights = [row["combined_weight"] for row in rows if row.get("combined_weight") is not None]
    return max(weights) if weights else 0.0


def _duplicate_exposure_group_evidence(block_2_1: dict[str, Any] | None) -> dict[str, Any] | None:
    groups = _duplicate_exposure_rows(block_2_1)
    if not groups:
        return None
    return _evidence(
        metric="duplicate_exposure_groups",
        value=groups,
        threshold="present_when_duplicate_exposure_flags_exist",
        direction="present",
        source="block_2_1",
        interpretation=(
            "Duplicate exposure groups list overlapping holdings with combined weights "
            "from Block 2.1 duplicate_exposure_flags."
        ),
    )


def _factor_beta(block_2_3: dict[str, Any] | None, key: str) -> float | None:
    return _as_float(_path(block_2_3, "factor_beta_snapshot", key))


def _factor_confidence(block_2_3: dict[str, Any] | None, key: str) -> str | None:
    value = _path(block_2_3, "factor_significance_confidence", key, "status")
    return str(value) if value else None


def _factor_confidence_map(block_2_3: dict[str, Any] | None) -> dict[str, str]:
    conf = _path(block_2_3, "factor_significance_confidence")
    if not isinstance(conf, dict):
        return {}
    out: dict[str, str] = {}
    for beta_key in PRODUCTION_BETA_KEYS:
        row = conf.get(beta_key)
        if not isinstance(row, dict):
            continue
        status = row.get("status")
        if status is None:
            continue
        text = str(status).strip()
        if text:
            out[beta_key] = text
    return out


def _production_factor_betas_5y(block_2_3: dict[str, Any] | None) -> dict[str, float]:
    snapshot = _path(block_2_3, "factor_beta_snapshot")
    if not isinstance(snapshot, dict):
        return {}
    out: dict[str, float] = {}
    for beta_key in PRODUCTION_BETA_KEYS:
        value = _as_float(snapshot.get(beta_key))
        if value is not None:
            out[beta_key] = value
    return out


def _beta_abs_direction(value: float) -> str:
    return _numeric_evidence_direction(abs(value), moderate=FACTOR_BETA_MODERATE_ABS, high=FACTOR_BETA_HIGH_ABS)


def _factor_variance_contribution_evidence(block_2_3: dict[str, Any] | None) -> list[dict[str, Any]]:
    vc = _path(block_2_3, "factor_variance_contribution")
    if not isinstance(vc, dict) or vc.get("status") != "available":
        return []
    contributions = vc.get("contributions")
    if not isinstance(contributions, dict) or not contributions:
        return []
    extra: list[dict[str, Any]] = [
        _evidence(
            metric="factor_variance_contribution",
            value=contributions,
            threshold="normalized_gross_variance_share_by_factor",
            direction="present",
            source="block_2_3",
            interpretation=(
                "Normalized factor variance contribution shares from Block 2.3 "
                "(adapted from stress_report factor_variance_decomposition)."
            ),
        )
    ]
    numeric = {str(k): _as_float(v) for k, v in contributions.items()}
    numeric = {k: v for k, v in numeric.items() if v is not None}
    if numeric:
        dominant_factor = max(numeric, key=lambda name: numeric[name])
        dominant_share = numeric[dominant_factor]
        extra.append(
            _evidence(
                metric="dominant_factor_variance_share",
                value={"factor": dominant_factor, "share": dominant_share},
                threshold={"moderate_gte": FACTOR_VARIANCE_DOMINANT_SHARE, "high_gte": 0.40},
                direction=_numeric_evidence_direction(
                    dominant_share,
                    moderate=FACTOR_VARIANCE_DOMINANT_SHARE,
                    high=0.40,
                ),
                source="block_2_3",
                interpretation="Dominant factor by normalized variance contribution share.",
            )
        )
    r_squared = _as_float(vc.get("r_squared"))
    if r_squared is not None:
        extra.append(
            _evidence(
                metric="factor_variance_r_squared",
                value=r_squared,
                threshold="informational_only",
                direction="present",
                source="block_2_3",
                interpretation="Factor model R-squared from Block 2.3 variance decomposition metadata.",
            )
        )
    return extra


def _factor_risk_ranking_evidence(block_2_3: dict[str, Any] | None) -> list[dict[str, Any]]:
    ranking = _path(block_2_3, "factor_risk_ranking")
    if not isinstance(ranking, list) or not ranking:
        return []
    return [
        _evidence(
            metric="factor_risk_ranking",
            value=ranking,
            threshold="top3_by_variance_contribution_or_abs_beta",
            direction="present",
            source="block_2_3",
            interpretation="Top factor risk ranking rows from Block 2.3 (variance contribution preferred).",
        )
    ]


def _production_factor_confidence_evidence(block_2_3: dict[str, Any] | None) -> list[dict[str, Any]]:
    conf = _factor_confidence_map(block_2_3)
    if not conf:
        return []
    return [
        _evidence(
            metric="production_factor_confidence",
            value=conf,
            threshold="significant_weak_evidence_or_unstable_low_confidence",
            direction="present",
            source="block_2_3",
            interpretation=(
                "Factor signal confidence for all production betas from Block 2.3 "
                "factor_significance_confidence (OLS/HAC evidence only)."
            ),
        )
    ]


def _factor_beta_stability_evidence(
    block_2_3: dict[str, Any] | None,
    beta_keys: tuple[str, ...],
) -> list[dict[str, Any]]:
    stability = _path(block_2_3, "factor_beta_stability")
    if not isinstance(stability, dict):
        return []
    subset: dict[str, Any] = {}
    for beta_key in beta_keys:
        row = stability.get(beta_key)
        if isinstance(row, dict) and row.get("beta_stability_label"):
            subset[beta_key] = row
    if not subset:
        return []
    unstable = [
        key
        for key, row in subset.items()
        if str(row.get("beta_stability_label")) in {"unstable", "moderately_changed"}
    ]
    direction = "present" if unstable else "below_threshold"
    return [
        _evidence(
            metric="factor_beta_stability",
            value=subset,
            threshold="stable_moderately_changed_unstable_across_3y_5y_10y",
            direction=direction,
            source="block_2_3",
            interpretation=(
                "Point-in-time 3Y/5Y/10Y beta stability labels from Block 2.3 "
                "(not rolling beta summaries)."
            ),
        )
    ]


def _kalman_current_beta_evidence(
    block_2_3: dict[str, Any] | None,
    beta_keys: tuple[str, ...],
) -> list[dict[str, Any]]:
    kalman = _path(block_2_3, "kalman_current_beta")
    if not isinstance(kalman, dict) or not kalman.get("available"):
        return []
    betas = kalman.get("betas")
    if not isinstance(betas, dict):
        return []
    subset: dict[str, float] = {}
    for beta_key in beta_keys:
        value = _as_float(betas.get(beta_key))
        if value is not None:
            subset[beta_key] = value
    if not subset:
        return []
    return [
        _evidence(
            metric="kalman_current_betas",
            value=subset,
            threshold="informational_dynamic_beta",
            direction="present",
            source="block_2_3",
            interpretation=(
                "Kalman current factor betas from Block 2.3 (evidence only; "
                "does not replace 5Y score weights under heuristic_v1)."
            ),
        )
    ]


def _supplemental_factor_beta_evidence(
    block_2_3: dict[str, Any] | None,
    beta_keys: tuple[str, ...],
) -> list[dict[str, Any]]:
    """Informational betas not wired into heuristic_v1 alert score weights."""
    extra: list[dict[str, Any]] = []
    for beta_key in beta_keys:
        value = _factor_beta(block_2_3, beta_key)
        if value is None:
            continue
        extra.append(
            _evidence(
                metric=beta_key,
                value=value,
                threshold={
                    "moderate_abs_gte": FACTOR_BETA_MODERATE_ABS,
                    "high_abs_gte": FACTOR_BETA_HIGH_ABS,
                },
                direction=_beta_abs_direction(value),
                source="block_2_3",
                interpretation=f"5Y {beta_key} from Block 2.3 factor_beta_snapshot (informational under heuristic_v1).",
            )
        )
    return extra


def _full_production_factor_betas_evidence(block_2_3: dict[str, Any] | None) -> list[dict[str, Any]]:
    snapshot = _production_factor_betas_5y(block_2_3)
    if not snapshot:
        return []
    return [
        _evidence(
            metric="production_factor_betas_5y",
            value=snapshot,
            threshold="all_production_beta_keys",
            direction="present",
            source="block_2_3",
            interpretation=(
                "Full production factor beta snapshot from Block 2.3; "
                "score weights still use a subset until heuristic_v2."
            ),
        )
    ]


def _factor_subsignal_evidence(
    block_2_3: dict[str, Any] | None,
    *,
    include_variance: bool = False,
    include_ranking: bool = False,
    include_all_confidence: bool = False,
    include_full_beta_snapshot: bool = False,
    stability_keys: tuple[str, ...] = (),
    kalman_keys: tuple[str, ...] = (),
    supplemental_beta_keys: tuple[str, ...] = (),
) -> list[dict[str, Any]]:
    extra: list[dict[str, Any]] = []
    if include_variance:
        extra.extend(_factor_variance_contribution_evidence(block_2_3))
    if include_ranking:
        extra.extend(_factor_risk_ranking_evidence(block_2_3))
    if include_all_confidence:
        extra.extend(_production_factor_confidence_evidence(block_2_3))
    if include_full_beta_snapshot:
        extra.extend(_full_production_factor_betas_evidence(block_2_3))
    extra.extend(_factor_beta_stability_evidence(block_2_3, stability_keys))
    extra.extend(_kalman_current_beta_evidence(block_2_3, kalman_keys))
    extra.extend(_supplemental_factor_beta_evidence(block_2_3, supplemental_beta_keys))
    return extra


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


def _correlation_pair_rows(block_2_2: dict[str, Any] | None, key: str) -> list[dict[str, Any]]:
    rows = _path(block_2_2, "correlation_breakdown", key)
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _top_pair_correlation(block_2_2: dict[str, Any] | None) -> float | None:
    rows = _correlation_pair_rows(block_2_2, "top3_highest_correlation_pairs")
    if not rows:
        return None
    values = [_as_float(row.get("correlation")) for row in rows]
    values = [v for v in values if v is not None]
    return max(values) if values else None


def _lowest_pair_correlation(block_2_2: dict[str, Any] | None) -> float | None:
    rows = _correlation_pair_rows(block_2_2, "top3_lowest_correlation_pairs")
    if not rows:
        return None
    values = [_as_float(row.get("correlation")) for row in rows]
    values = [v for v in values if v is not None]
    return min(values) if values else None


def _avg_pairwise_correlation(block_2_2: dict[str, Any] | None) -> float | None:
    return _as_float(_path(block_2_2, "correlation_breakdown", "avg_pairwise_correlation"))


def _lack_of_diversifying_pairs(block_2_2: dict[str, Any] | None) -> bool | None:
    """True when reported lowest pairs and average correlation suggest few diversifiers."""
    lowest = _lowest_pair_correlation(block_2_2)
    avg = _avg_pairwise_correlation(block_2_2)
    if lowest is None and avg is None:
        return None
    if lowest is not None and lowest < DIVERSIFYING_PAIR_CORR_THRESHOLD:
        return False
    if avg is not None and avg < HIGH_AVG_PAIRWISE_CORR_THRESHOLD:
        return False
    return True


def _correlation_subsignal_evidence(block_2_2: dict[str, Any] | None) -> list[dict[str, Any]]:
    extra: list[dict[str, Any]] = []
    lowest_rows = _correlation_pair_rows(block_2_2, "top3_lowest_correlation_pairs")
    if lowest_rows:
        extra.append(
            _evidence(
                metric="top3_lowest_correlation_pairs",
                value=lowest_rows,
                threshold="ascending_correlation_among_valid_pairs",
                direction="present",
                source="block_2_2",
                interpretation=(
                    "Lowest pairwise holding correlations from Block 2.2; "
                    "checks whether any holdings diversify one another."
                ),
            )
        )
    lowest = _lowest_pair_correlation(block_2_2)
    if lowest is not None:
        extra.append(
            _evidence(
                metric="lowest_pair_correlation",
                value=lowest,
                threshold={"diversifying_lt": DIVERSIFYING_PAIR_CORR_THRESHOLD},
                direction=(
                    "below_threshold"
                    if lowest < DIVERSIFYING_PAIR_CORR_THRESHOLD
                    else "above_threshold"
                ),
                source="block_2_2",
                interpretation="Minimum correlation among Block 2.2 lowest-reported pairs.",
            )
        )
    avg = _avg_pairwise_correlation(block_2_2)
    if avg is not None:
        extra.append(
            _evidence(
                metric="avg_pairwise_correlation",
                value=avg,
                threshold={"moderate_gte": HIGH_AVG_PAIRWISE_CORR_THRESHOLD},
                direction=_numeric_evidence_direction(avg, moderate=HIGH_AVG_PAIRWISE_CORR_THRESHOLD, high=0.70),
                source="block_2_2",
                interpretation="Average off-diagonal pairwise correlation from Block 2.2 correlation matrix.",
            )
        )
    lack = _lack_of_diversifying_pairs(block_2_2)
    if lack is not None:
        extra.append(
            _evidence(
                metric="lack_of_diversifying_pairs",
                value=lack,
                threshold={
                    "diversifying_pair_lt": DIVERSIFYING_PAIR_CORR_THRESHOLD,
                    "high_avg_pairwise_gte": HIGH_AVG_PAIRWISE_CORR_THRESHOLD,
                },
                direction="present" if lack else "below_threshold",
                source="block_2_2",
                interpretation=(
                    "Derived flag: true when lowest reported pairs stay above the diversifying "
                    "threshold and average pairwise correlation is elevated."
                ),
            )
        )
    return extra


def _ticker_equity_like_non_equity(ticker: str, taxonomy_rows: dict[str, dict[str, Any]] | None) -> bool:
    tax = _taxonomy_for_ticker(ticker, taxonomy_rows)
    return _is_equity_main_risk_factor(tax) and not _is_equity_asset_class(tax)


def _equity_like_correlation_evidence(
    block_2_2: dict[str, Any] | None,
    taxonomy_rows: dict[str, dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    if not _normalize_taxonomy_rows(taxonomy_rows):
        return []
    seen: set[tuple[str, str]] = set()
    pairs: list[dict[str, Any]] = []
    for key in ("top3_highest_correlation_pairs", "top3_lowest_correlation_pairs"):
        for row in _correlation_pair_rows(block_2_2, key):
            ticker_a = str(row.get("ticker_a") or "").strip().upper()
            ticker_b = str(row.get("ticker_b") or "").strip().upper()
            if not ticker_a or not ticker_b:
                continue
            equity_like = _ticker_equity_like_non_equity(ticker_a, taxonomy_rows) or _ticker_equity_like_non_equity(
                ticker_b, taxonomy_rows
            )
            if not equity_like:
                continue
            pair_key = tuple(sorted((ticker_a, ticker_b)))
            if pair_key in seen:
                continue
            seen.add(pair_key)
            pairs.append(row)
    if not pairs:
        return []
    return [
        _evidence(
            metric="equity_like_high_correlation_pairs",
            value=pairs,
            threshold="pair_includes_equity_like_non_equity_label",
            direction="present",
            source="block_2_2",
            interpretation=(
                "Correlation pairs where at least one holding is equity-like by taxonomy "
                "(main_risk_factor equity with non-equity asset_class label)."
            ),
        )
    ]


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


def _propagate_block_2_2_warnings(alert_id: str, block_2_2: dict[str, Any] | None) -> list[str]:
    rows = _path(block_2_2, "data_quality_warnings")
    if not isinstance(rows, list):
        return []
    propagated: list[str] = []
    for warning in rows:
        if not isinstance(warning, str) or not warning.strip():
            continue
        lower = warning.lower()
        for fragment, alert_ids in _BLOCK_22_WARNING_PROPAGATION:
            if fragment in lower and alert_id in alert_ids:
                if warning not in propagated:
                    propagated.append(warning)
                break
    return propagated


def _signal_elevated(value: float | None, moderate: float, *, abs_value: bool = False) -> bool | None:
    if value is None:
        return None
    compare = abs(value) if abs_value else value
    return compare >= moderate


def _cross_signal_agreement(
    alert_id: str,
    *,
    block_2_1: dict[str, Any] | None,
    block_2_2: dict[str, Any] | None,
    block_2_3: dict[str, Any] | None,
    signal_values: dict[str, tuple[float | None, str, str]],
) -> str:
    """Classify agreement across taxonomy (2.1), metrics (2.2), and factors (2.3)."""
    elevated: list[bool | None] = []

    if alert_id == "hidden_equity_beta":
        elevated.extend(
            [
                _signal_elevated(
                    _breakdown_weight(block_2_1, "by_asset_class", {"equity", "stocks", "stock"}),
                    0.35,
                ),
                _signal_elevated(_breakdown_weight(block_2_1, "by_risk_role", {"risk_on"}), 0.20),
            ]
        )
        beta_portfolio = signal_values.get("beta_portfolio", (None, "", ""))[0]
        downside_beta = signal_values.get("downside_beta", (None, "", ""))[0]
        rolling_corr = signal_values.get("rolling_correlation", (None, "", ""))[0]
        beta_eq = signal_values.get("beta_eq", (None, "", ""))[0]
        elevated.extend(
            [
                _signal_elevated(beta_portfolio, 0.70),
                _signal_elevated(downside_beta, 0.90),
                _signal_elevated(rolling_corr, 0.70),
                _signal_elevated(beta_eq, 0.35, abs_value=True),
            ]
        )
    elif alert_id == "duration_concentration":
        elevated.extend(
            [
                _signal_elevated(signal_values.get("rates_or_duration_weight", (None, "", ""))[0], 0.25),
                _signal_elevated(signal_values.get("fixed_income_weight", (None, "", ""))[0], 0.35),
                _signal_elevated(signal_values.get("beta_rr", (None, "", ""))[0], 0.25, abs_value=True),
            ]
        )
        beta_inf = _factor_beta(block_2_3, "beta_inf")
        elevated.append(_signal_elevated(beta_inf, 0.25, abs_value=True))
    elif alert_id == "credit_liquidity_risk":
        elevated.extend(
            [
                _signal_elevated(signal_values.get("credit_liquidity_weight", (None, "", ""))[0], 0.20),
                _signal_elevated(signal_values.get("risk_on_or_carry_weight", (None, "", ""))[0], 0.20),
                _signal_elevated(signal_values.get("beta_credit", (None, "", ""))[0], 0.25, abs_value=True),
                _signal_elevated(signal_values.get("downside_beta", (None, "", ""))[0], 0.90),
            ]
        )
    elif alert_id == "correlation_concentration":
        elevated.extend(
            [
                _signal_elevated(signal_values.get("highest_pair_correlation", (None, "", ""))[0], 0.75),
                _signal_elevated(signal_values.get("duplicate_exposure_weight", (None, "", ""))[0], 0.10),
                _signal_elevated(
                    signal_values.get("dominant_main_risk_factor_weight", (None, "", ""))[0],
                    0.60,
                ),
            ]
        )
    elif alert_id == "weak_hedge_behavior":
        elevated.extend(
            [
                _signal_elevated(signal_values.get("hedge_labeled_weight", (None, "", ""))[0], 0.15),
                _signal_elevated(signal_values.get("downside_beta", (None, "", ""))[0], 0.90),
                _signal_elevated(signal_values.get("rolling_correlation", (None, "", ""))[0], 0.70),
                _signal_elevated(
                    signal_values.get("equity_or_credit_beta", (None, "", ""))[0],
                    0.35,
                    abs_value=True,
                ),
            ]
        )
    elif alert_id == "tail_risk":
        for metric, rule in ALERT_RULES["tail_risk"]["signals"].items():
            value = signal_values.get(metric, (None, "", ""))[0]
            adverse = rule.get("adverse") == "lte"
            moderate = float(rule["moderate"])
            if adverse:
                elevated.append(value is not None and value <= moderate)
            elif rule.get("abs"):
                elevated.append(_signal_elevated(value, moderate, abs_value=True))
            else:
                elevated.append(_signal_elevated(value, moderate))

    known = [flag for flag in elevated if flag is not None]
    if len(known) < 2:
        return "single_source"
    highs = sum(1 for flag in known if flag)
    lows = len(known) - highs
    if highs >= 2 and lows == 0:
        return "agree"
    if lows >= 2 and highs == 0:
        return "agree"
    if highs >= 1 and lows >= 1:
        return "conflict"
    return "partial"


def _factor_confidence_penalty(block_2_3: dict[str, Any] | None, alert_id: str) -> str | None:
    beta_keys = _ALERT_FACTOR_BETA_KEYS.get(alert_id, ())
    if not beta_keys:
        return None
    conf = _factor_confidence_map(block_2_3)
    if not conf:
        return "factor_evidence_missing"
    statuses = [conf.get(key) for key in beta_keys if key in conf]
    if not statuses:
        return "factor_evidence_missing"
    if any(status == "unstable_low_confidence" for status in statuses):
        return "unstable_low_confidence"
    if any(status == "weak_evidence" for status in statuses):
        return "weak_factor_evidence"
    return None


def _confidence_v2(
    *,
    alert_id: str,
    evaluable_weight: float,
    score: int | None,
    warnings: list[str],
    limitations: list[str],
    agreement: str,
    factor_penalty: str | None,
    is_preliminary: bool,
) -> str:
    if score is None:
        return "unavailable"
    if evaluable_weight < 0.50 or agreement == "conflict":
        return "low"
    if factor_penalty == "unstable_low_confidence":
        return "low"
    if is_preliminary:
        return "medium"
    if (
        evaluable_weight >= 0.75
        and not warnings
        and not limitations
        and agreement == "agree"
        and factor_penalty is None
    ):
        return "high"
    if evaluable_weight >= 0.50:
        if factor_penalty in {"weak_factor_evidence", "factor_evidence_missing"} and agreement != "agree":
            return "low"
        return "medium"
    return "low"


def _apply_confidence_status_cap(alert: dict[str, Any]) -> dict[str, Any]:
    """heuristic_v2: never emit High status when confidence is low."""
    if alert.get("confidence") != "low" or alert.get("status") != "High":
        return alert
    capped = dict(alert)
    capped["status"] = "Medium"
    score = capped.get("score")
    if isinstance(score, int) and score >= 70:
        capped["score"] = min(score, 69)
    notes = list(capped.get("calculation_notes") or [])
    cap_note = "status_capped_to_medium_due_to_low_confidence=heuristic_v2"
    if cap_note not in notes:
        notes.append(cap_note)
    capped["calculation_notes"] = notes
    return capped


def _confidence_reason(
    *,
    alert_id: str,
    score: int | None,
    evaluable_weight: float,
    confidence: str,
    warnings: list[str],
    insufficient: list[str],
    limitations: list[str],
    agreement: str,
    factor_penalty: str | None,
    status_capped: bool,
    is_preliminary: bool,
) -> str | None:
    if score is None:
        if insufficient:
            missing = ", ".join(insufficient[:3])
            suffix = " (and others)" if len(insufficient) > 3 else ""
            return f"Unavailable because required signals are missing: {missing}{suffix}."
        return (
            f"Unavailable because evaluable signal weight ({round(evaluable_weight, 3)}) "
            f"is below the minimum for {alert_id}."
        )

    parts: list[str] = [
        f"{confidence.capitalize()} confidence (model {CONFIDENCE_MODEL_VERSION}): "
        f"evaluable signal weight {round(evaluable_weight, 3)}; "
        f"cross-signal agreement={agreement}."
    ]
    if factor_penalty:
        parts.append(f"Factor signal confidence penalty: {factor_penalty}.")
    if is_preliminary:
        parts.append("Alert is preliminary without Stress Lab confirmation.")
    if warnings:
        parts.append(f"Data-quality warnings: {'; '.join(warnings)}.")
    if limitations:
        parts.append(f"Limitations: {'; '.join(limitations[:2])}.")
    if insufficient:
        parts.append(f"Missing scored signals: {'; '.join(insufficient[:3])}.")
    if status_capped:
        parts.append("Risk status capped to Medium because confidence is low under heuristic_v2.")
    if confidence == "high":
        parts.append("Multiple independent Block 2.1–2.3 sources agree and factor evidence is stable.")
    return " ".join(parts)


def _weighted_alert(
    alert_id: str,
    *,
    signal_values: dict[str, tuple[float | None, str, str]],
    block_2_1: dict[str, Any] | None = None,
    block_2_2: dict[str, Any] | None = None,
    block_2_3: dict[str, Any] | None = None,
    evidence_extra: list[dict[str, Any]] | None = None,
    warnings: list[str] | None = None,
    insufficient_extra: list[str] | None = None,
    calculation_extra: list[str] | None = None,
    limitations_extra: list[str] | None = None,
    contributing_assets: list[dict[str, Any]] | None = None,
    is_preliminary: bool = False,
    confirmation_status: str = "not_applicable",
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

    propagated = _propagate_block_2_2_warnings(alert_id, block_2_2)
    data_quality_warnings = list(dict.fromkeys(list(warnings or []) + propagated))
    alert_limitations = list(
        dict.fromkeys(list(_ALERT_LIMITATIONS.get(alert_id, [])) + list(limitations_extra or []))
    )
    agreement = _cross_signal_agreement(
        alert_id,
        block_2_1=block_2_1,
        block_2_2=block_2_2,
        block_2_3=block_2_3,
        signal_values=signal_values,
    )
    factor_penalty = _factor_confidence_penalty(block_2_3, alert_id)
    notes = [
        f"ruleset={RULE_VERSION}",
        f"confidence_model={CONFIDENCE_MODEL_VERSION}",
        "score is a weighted average of available signal scores (renormalized by evaluable weight)",
        f"evaluable_signal_weight={round(evaluable_weight, 3)}",
        f"cross_signal_agreement={agreement}",
    ]
    if factor_penalty:
        notes.append(f"factor_confidence_penalty={factor_penalty}")
    notes.extend(calculation_extra or [])
    copy = _ALERT_COPY[alert_id]
    confidence = _confidence_v2(
        alert_id=alert_id,
        evaluable_weight=evaluable_weight,
        score=score,
        warnings=data_quality_warnings,
        limitations=alert_limitations,
        agreement=agreement,
        factor_penalty=factor_penalty,
        is_preliminary=is_preliminary,
    )
    status_before_cap = status
    alert: dict[str, Any] = {
        "status": status,
        "score": score,
        "evidence": evidence,
        "explanation": copy["explanation"],
        "why_it_matters": copy["why_it_matters"],
        "next_tests": list(rule_set["next_tests"]),
        "confidence": confidence,
        "limitations": alert_limitations,
        "data_quality_warnings": data_quality_warnings,
        "insufficient_evidence_reasons": list(dict.fromkeys(insufficient)),
        "calculation_notes": notes,
        "contributing_assets": list(contributing_assets or []),
    }
    alert = _apply_confidence_status_cap(alert)
    status_capped = status_before_cap == "High" and alert.get("status") == "Medium"
    alert["confirmation_status"] = (
        "unavailable" if score is None else confirmation_status
    )
    alert["confidence_reason"] = _confidence_reason(
        alert_id=alert_id,
        score=alert.get("score"),
        evaluable_weight=evaluable_weight,
        confidence=confidence,
        warnings=data_quality_warnings,
        insufficient=list(dict.fromkeys(insufficient)),
        limitations=alert_limitations,
        agreement=agreement,
        factor_penalty=factor_penalty,
        status_capped=status_capped,
        is_preliminary=is_preliminary,
    )
    return alert


def _hidden_equity_beta(
    block_2_1: dict[str, Any] | None,
    block_2_2: dict[str, Any] | None,
    block_2_3: dict[str, Any] | None,
    *,
    taxonomy_rows: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    beta_eq = _factor_beta(block_2_3, "beta_eq")
    conf = _factor_confidence(block_2_3, "beta_eq")
    extra = _equity_taxonomy_evidence(block_2_1)
    extra.extend(_equity_like_correlation_evidence(block_2_2, taxonomy_rows))
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
    extra.extend(
        _factor_subsignal_evidence(
            block_2_3,
            include_variance=True,
            include_ranking=True,
            include_all_confidence=True,
            include_full_beta_snapshot=True,
            stability_keys=("beta_eq", "beta_us_growth"),
            kalman_keys=("beta_eq",),
            supplemental_beta_keys=("beta_us_growth",),
        )
    )
    return _weighted_alert(
        "hidden_equity_beta",
        block_2_1=block_2_1,
        block_2_2=block_2_2,
        block_2_3=block_2_3,
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
        calculation_extra=["equity beta thresholds are heuristic_v2 product diagnostics"],
    )


def _duration_concentration(
    block_2_1: dict[str, Any] | None,
    block_2_2: dict[str, Any] | None,
    block_2_3: dict[str, Any] | None,
    *,
    stress_enrichment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rates_weight = _breakdown_weight(block_2_1, "by_main_risk_factor", {"real_rates", "rates", "duration"})
    fixed_income = _breakdown_weight(block_2_1, "by_asset_class", {"fixed_income", "bonds", "bond"})
    extra: list[dict[str, Any]] = []
    mrf_flag = _concentration_flag_evidence(
        block_2_1,
        flag_ids={"single_main_risk_factor_dominance"},
        metric="main_risk_factor_dominance_flags",
        interpretation="Block 2.1 concentration flags for dominant main risk factor bucket.",
    )
    if mrf_flag is not None:
        extra.append(mrf_flag)
    extra.extend(
        _factor_subsignal_evidence(
            block_2_3,
            include_variance=True,
            include_ranking=True,
            stability_keys=("beta_rr", "beta_inf"),
            kalman_keys=("beta_rr", "beta_inf"),
            supplemental_beta_keys=("beta_inf",),
        )
    )
    extra.extend(_inflation_stress_cross_ref_evidence(stress_enrichment))
    return _weighted_alert(
        "duration_concentration",
        block_2_1=block_2_1,
        block_2_2=block_2_2,
        block_2_3=block_2_3,
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
        warnings=(
            []
            if rates_weight is not None
            else [
                "duration_bucket not present in Block 2.1 product output; "
                "using main_risk_factor/fixed_income proxies"
            ]
        ),
        evidence_extra=extra,
        calculation_extra=[
            "duration thresholds are heuristic_v2 because live duration is not available in Block 2.1"
        ],
    )


def _stress_scenario_rows(stress_report: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(stress_report, dict):
        return []
    return [row for row in stress_report.get("scenario_results") or [] if isinstance(row, dict)]


def _worst_scenario_by_loss(stress_report: dict[str, Any] | None) -> dict[str, Any] | None:
    worst: tuple[float, dict[str, Any]] | None = None
    for row in _stress_scenario_rows(stress_report):
        pnl = _as_float(row.get("portfolio_pnl_pct"))
        if pnl is None:
            continue
        if worst is None or pnl < worst[0]:
            worst = (pnl, row)
    return worst[1] if worst else None


def _hedge_labeled_tickers(
    block_2_1: dict[str, Any] | None,
    taxonomy_rows: dict[str, dict[str, Any]] | None,
) -> list[str]:
    tickers: list[str] = []
    for ticker, _weight, tax in _holdings_from_block_2_1(block_2_1, taxonomy_rows):
        if _tax_risk_roles(tax).intersection(HEDGE_LABELED_RISK_ROLES):
            tickers.append(ticker)
    return tickers


def _compact_hedge_gap_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "risk_type": row.get("risk_type"),
        "linked_scenario_id": row.get("linked_scenario_id"),
        "offset_coverage_ratio": row.get("offset_coverage_ratio"),
        "portfolio_loss_pct": row.get("portfolio_loss_pct"),
        "data_availability": row.get("data_availability"),
        "assets_hurt_count": len(row.get("assets_hurt") or []),
        "assets_helped_count": len(row.get("assets_helped") or []),
    }


def _worst_scenario_hedge_check(
    stress_report: dict[str, Any] | None,
    hedge_tickers: list[str],
) -> dict[str, Any] | None:
    if not hedge_tickers:
        return None
    worst = _worst_scenario_by_loss(stress_report)
    if not isinstance(worst, dict):
        return None
    pnl_by_asset = worst.get("pnl_by_asset_pct")
    if not isinstance(pnl_by_asset, dict):
        return None
    portfolio_pnl = _as_float(worst.get("portfolio_pnl_pct"))
    failing: list[dict[str, Any]] = []
    for ticker in hedge_tickers:
        asset_pnl = _as_float(pnl_by_asset.get(ticker))
        if asset_pnl is None:
            continue
        if portfolio_pnl is not None and portfolio_pnl < 0 and asset_pnl <= 0:
            failing.append({"ticker": ticker, "pnl_pct": asset_pnl})
    return {
        "worst_scenario_id": worst.get("scenario_id"),
        "portfolio_pnl_pct": portfolio_pnl,
        "hedge_assets_negative_with_portfolio_loss": failing,
    }


def _pca_layer_from_stress_report(
    stress_report: dict[str, Any] | None,
    *,
    layer: str,
) -> dict[str, Any]:
    if not isinstance(stress_report, dict):
        return {}
    pca = stress_report.get("portfolio_pca")
    if not isinstance(pca, dict):
        return {}
    block = pca.get(layer)
    if not isinstance(block, dict):
        return {}
    cov = block.get("covariance_pca")
    return cov if isinstance(cov, dict) else {}


def build_block_2_4_legacy_enrichment(stress_report: dict[str, Any] | None) -> dict[str, Any] | None:
    """Build a compact legacy X-Ray wire-time summary for Block 2.4 (does not run Stress Lab).

    Surfaces portfolio PCA PC1 shares for cross-reference on ``correlation_concentration``
    only; scores remain heuristic_v2 over Blocks 2.1–2.3.
    """
    if not isinstance(stress_report, dict):
        return None

    sources: list[str] = []
    raw_pca = _pca_layer_from_stress_report(stress_report, layer="raw")
    residual_pca = _pca_layer_from_stress_report(stress_report, layer="residual")
    raw_pc1 = _as_float(raw_pca.get("pc1_explained_variance_ratio"))
    residual_pc1 = _as_float(residual_pca.get("pc1_explained_variance_ratio"))

    if raw_pc1 is not None:
        sources.append("portfolio_pca.raw")
    if residual_pc1 is not None:
        sources.append("portfolio_pca.residual")

    factor_residual_share: float | None = None
    decomp = stress_report.get("factor_variance_decomposition")
    if isinstance(decomp, dict):
        factor_residual_share = _as_float(decomp.get("residual_share"))
        if factor_residual_share is not None:
            sources.append("factor_variance_decomposition")

    if not sources:
        return None

    return {
        "available": True,
        "sources": list(dict.fromkeys(sources)),
        "raw_pc1_explained_variance_ratio": raw_pc1,
        "residual_pc1_explained_variance_ratio": residual_pc1,
        "factor_residual_share": factor_residual_share,
        "legacy_section_refs": {
            "raw_pca": LEGACY_PCA_RAW_SECTION,
            "residual_pca": LEGACY_PCA_RESIDUAL_SECTION,
        },
        "threshold_keys": ["pca_pc1_moderate", "pca_pc1_high"],
    }


def _pca_pc1_direction(pc1: float | None) -> str:
    if pc1 is None:
        return "missing"
    if pc1 >= PCA_PC1_HIGH:
        return "above_threshold"
    if pc1 >= PCA_PC1_MODERATE:
        return "present"
    return "below_threshold"


def _legacy_pca_cross_ref_evidence(legacy_enrichment: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(legacy_enrichment, dict) or not legacy_enrichment.get("available"):
        return []

    refs = legacy_enrichment.get("legacy_section_refs")
    if not isinstance(refs, dict):
        refs = {}
    extra: list[dict[str, Any]] = []

    raw_pc1 = _as_float(legacy_enrichment.get("raw_pc1_explained_variance_ratio"))
    if raw_pc1 is not None:
        extra.append(
            _evidence(
                metric="legacy_pca_pc1_raw",
                value={
                    "pc1_explained_variance_ratio": raw_pc1,
                    "legacy_section": refs.get("raw_pca", LEGACY_PCA_RAW_SECTION),
                    "threshold_keys": legacy_enrichment.get("threshold_keys")
                    or ["pca_pc1_moderate", "pca_pc1_high"],
                },
                threshold="pca_pc1_moderate_high_legacy",
                direction=_pca_pc1_direction(raw_pc1),
                source="portfolio_analytics",
                interpretation=(
                    "Raw covariance PCA PC1 from stress_report.portfolio_pca (legacy "
                    "hidden_risk_detector cross-ref; not scored in Block 2.4)."
                ),
            )
        )

    residual_pc1 = _as_float(legacy_enrichment.get("residual_pc1_explained_variance_ratio"))
    if residual_pc1 is not None:
        extra.append(
            _evidence(
                metric="legacy_pca_pc1_residual",
                value={
                    "pc1_explained_variance_ratio": residual_pc1,
                    "legacy_section": refs.get("residual_pca", LEGACY_PCA_RESIDUAL_SECTION),
                    "threshold_keys": legacy_enrichment.get("threshold_keys")
                    or ["pca_pc1_moderate", "pca_pc1_high"],
                },
                threshold="pca_pc1_moderate_high_legacy",
                direction=_pca_pc1_direction(residual_pc1),
                source="portfolio_analytics",
                interpretation=(
                    "Residual PCA PC1 after named factors (legacy hidden_risk_detector "
                    "cross-ref; not scored in Block 2.4)."
                ),
            )
        )

    factor_residual = _as_float(legacy_enrichment.get("factor_residual_share"))
    if factor_residual is not None:
        extra.append(
            _evidence(
                metric="legacy_factor_residual_share",
                value={
                    "residual_share": factor_residual,
                    "legacy_section": LEGACY_PCA_RESIDUAL_SECTION,
                },
                threshold="informational_factor_variance_decomposition",
                direction="present",
                source="portfolio_analytics",
                interpretation=(
                    "Factor-adjusted residual variance share from stress_report "
                    "(informational legacy cross-ref only)."
                ),
            )
        )

    return extra


def build_block_2_4_stress_enrichment(
    stress_report: dict[str, Any] | None,
    *,
    block_2_1: dict[str, Any] | None = None,
    taxonomy_rows: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    """Build a compact Block 3 wire-time summary for Block 2.4 (does not run Stress Lab)."""
    if not isinstance(stress_report, dict):
        return None

    hedge_tickers = _hedge_labeled_tickers(block_2_1, taxonomy_rows)
    sources: list[str] = []
    hedge_gap_summary: dict[str, Any] | None = None
    hedge_gap_by_risk_type: dict[str, dict[str, Any]] = {}

    hedge_gap = stress_report.get("hedge_gap_analysis_v1")
    if isinstance(hedge_gap, dict):
        sources.append("hedge_gap_analysis_v1")
        summary = hedge_gap.get("summary")
        if isinstance(summary, dict):
            hedge_gap_summary = {
                "main_hedge_gap": summary.get("main_hedge_gap"),
                "weakest_protection_area": summary.get("weakest_protection_area"),
                "strongest_protection_area": summary.get("strongest_protection_area"),
                "diagnosis_summary_en": summary.get("diagnosis_summary_en"),
            }
        for row in hedge_gap.get("by_risk_type") or []:
            if not isinstance(row, dict):
                continue
            risk_type = str(row.get("risk_type") or "").strip()
            if risk_type:
                hedge_gap_by_risk_type[risk_type] = _compact_hedge_gap_row(row)

    worst_scenario_hedge_check = _worst_scenario_hedge_check(stress_report, hedge_tickers)
    if worst_scenario_hedge_check is not None:
        sources.append("scenario_results_worst_loss")

    factor_oos_mae_5y: float | None = None
    oos = stress_report.get("factor_beta_shock_oos")
    if isinstance(oos, dict):
        summary = oos.get("summary")
        if isinstance(summary, dict):
            factor_oos_mae_5y = _as_float(summary.get("mean_abs_error_5y"))
            if factor_oos_mae_5y is not None:
                sources.append("factor_beta_shock_oos")

    if not sources:
        return None

    return {
        "available": True,
        "sources": list(dict.fromkeys(sources)),
        "hedge_tickers": hedge_tickers,
        "hedge_gap_summary": hedge_gap_summary,
        "hedge_gap_by_risk_type": hedge_gap_by_risk_type,
        "worst_scenario_hedge_check": worst_scenario_hedge_check,
        "factor_oos_mae_5y": factor_oos_mae_5y,
    }


def _inflation_stress_cross_ref_evidence(
    stress_enrichment: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if not isinstance(stress_enrichment, dict) or not stress_enrichment.get("available"):
        return []
    by_risk = stress_enrichment.get("hedge_gap_by_risk_type")
    if not isinstance(by_risk, dict):
        return []
    extra: list[dict[str, Any]] = []
    for risk_type, metric in (
        ("stagflation_protection", "stagflation_offset_coverage"),
        ("commodity_inflation_shock_protection", "commodity_shock_offset_coverage"),
    ):
        row = by_risk.get(risk_type)
        if not isinstance(row, dict):
            continue
        extra.append(
            _evidence(
                metric=metric,
                value={
                    "risk_type": risk_type,
                    "linked_scenario_id": row.get("linked_scenario_id"),
                    "offset_coverage_ratio": row.get("offset_coverage_ratio"),
                    "portfolio_loss_pct": row.get("portfolio_loss_pct"),
                    "data_availability": row.get("data_availability"),
                },
                threshold="informational_block_3_hedge_gap",
                direction=(
                    "present"
                    if row.get("data_availability") == "available"
                    else "missing"
                ),
                source="block_3_stress",
                interpretation=(
                    "Block 3.3 hedge-gap offset coverage for inflation/stagflation or "
                    "commodity shock scenarios (wire-time summary only)."
                ),
            )
        )
    return extra


def _weak_hedge_stress_supports_hypothesis(stress_enrichment: dict[str, Any]) -> bool:
    oos_mae = _as_float(stress_enrichment.get("factor_oos_mae_5y"))
    if oos_mae is not None and oos_mae >= WEAK_HEDGE_OOS_MAE_MODERATE:
        return True

    worst_check = stress_enrichment.get("worst_scenario_hedge_check")
    if isinstance(worst_check, dict):
        failing = worst_check.get("hedge_assets_negative_with_portfolio_loss") or []
        if failing:
            return True

    summary = stress_enrichment.get("hedge_gap_summary")
    if isinstance(summary, dict):
        main_gap = summary.get("main_hedge_gap")
        if isinstance(main_gap, dict):
            ratio = _as_float(main_gap.get("offset_coverage_ratio"))
            if ratio is not None and ratio < WEAK_HEDGE_OFFSET_COVERAGE_WEAK:
                return True

    by_risk = stress_enrichment.get("hedge_gap_by_risk_type")
    if isinstance(by_risk, dict):
        for row in by_risk.values():
            if not isinstance(row, dict):
                continue
            ratio = _as_float(row.get("offset_coverage_ratio"))
            if ratio is not None and ratio < WEAK_HEDGE_OFFSET_COVERAGE_WEAK:
                return True
    return False


def _weak_hedge_stress_evidence(
    stress_enrichment: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if not isinstance(stress_enrichment, dict) or not stress_enrichment.get("available"):
        return []

    extra: list[dict[str, Any]] = []
    summary = stress_enrichment.get("hedge_gap_summary")
    if isinstance(summary, dict) and any(summary.values()):
        extra.append(
            _evidence(
                metric="hedge_gap_summary",
                value=summary,
                threshold="block_3_3_main_hedge_gap",
                direction="present",
                source="block_3_stress",
                interpretation=(
                    "Block 3.3 hedge-gap summary (main hedge gap and weakest protection area)."
                ),
            )
        )

    by_risk = stress_enrichment.get("hedge_gap_by_risk_type")
    if isinstance(by_risk, dict) and by_risk:
        extra.append(
            _evidence(
                metric="hedge_gap_by_risk_type",
                value=by_risk,
                threshold="block_3_3_offset_coverage",
                direction="present",
                source="block_3_stress",
                interpretation=(
                    "Per-risk-type offset coverage ratios from Block 3.3 hedge_gap_analysis_v1."
                ),
            )
        )

    worst_check = stress_enrichment.get("worst_scenario_hedge_check")
    if isinstance(worst_check, dict):
        failing = worst_check.get("hedge_assets_negative_with_portfolio_loss") or []
        extra.append(
            _evidence(
                metric="worst_scenario_hedge_offset_check",
                value=worst_check,
                threshold="hedge_labeled_assets_must_help_when_portfolio_loses",
                direction="conflicting" if failing else "below_threshold",
                source="block_3_stress",
                interpretation=(
                    "Whether hedge-labeled holdings offset portfolio loss in the worst "
                    "available synthetic scenario."
                ),
            )
        )

    oos_mae = _as_float(stress_enrichment.get("factor_oos_mae_5y"))
    if oos_mae is not None:
        direction = "above_threshold" if oos_mae >= WEAK_HEDGE_OOS_MAE_MODERATE else "below_threshold"
        extra.append(
            _evidence(
                metric="factor_oos_mae_5y",
                value=oos_mae,
                threshold={
                    "moderate_gte": WEAK_HEDGE_OOS_MAE_MODERATE,
                    "high_gte": WEAK_HEDGE_OOS_MAE_HIGH,
                },
                direction=direction,
                source="block_3_stress",
                interpretation=(
                    "Factor beta shock out-of-sample mean absolute error (5Y beta) from stress_report."
                ),
            )
        )
    return extra


def _weak_hedge_behavior(
    block_2_1: dict[str, Any] | None,
    block_2_2: dict[str, Any] | None,
    block_2_3: dict[str, Any] | None,
    *,
    stress_enrichment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    hedge_weight = _breakdown_weight(
        block_2_1,
        "by_risk_role",
        set(HEDGE_LABELED_RISK_ROLES),
    )
    eq = _factor_beta(block_2_3, "beta_eq")
    credit = _factor_beta(block_2_3, "beta_credit")
    max_risk_beta = max([abs(v) for v in (eq, credit) if v is not None], default=None)
    extra = _factor_subsignal_evidence(
        block_2_3,
        include_variance=True,
        stability_keys=("beta_usd", "beta_cmd", "beta_vix", "beta_rr"),
        kalman_keys=("beta_usd", "beta_cmd", "beta_vix", "beta_rr"),
        supplemental_beta_keys=("beta_usd", "beta_cmd", "beta_vix", "beta_rr"),
    )
    extra.extend(_weak_hedge_stress_evidence(stress_enrichment))

    stress_available = isinstance(stress_enrichment, dict) and stress_enrichment.get("available")
    warnings: list[str] = []
    limitations_extra: list[str] = []
    calculation_extra = [
        "weak hedge thresholds are heuristic_v2 product diagnostics",
        "offset factor betas (usd/cmd/vix/rr) are informational evidence only under heuristic_v2",
    ]
    is_preliminary = True
    confirmation_status = "preliminary"

    if stress_available:
        is_preliminary = False
        confirmation_status = "confirmed"
        calculation_extra.append("stress_enrichment_wire_time=block_3_summary")
        if _weak_hedge_stress_supports_hypothesis(stress_enrichment):
            calculation_extra.append("stress_evidence_supports_weak_hedge_hypothesis")
            limitations_extra.append(
                "Stress Lab wire-time evidence supports a weak-hedge hypothesis; "
                "this remains diagnostic-only and is not a mandate or trade instruction."
            )
        else:
            limitations_extra.append(
                "Stress Lab wire-time summary is available but does not strongly indicate "
                "weak hedge behavior under current rules."
            )
    else:
        warnings.append("preliminary_without_stress_lab")
        calculation_extra.extend(
            [
                "weak hedge behavior is preliminary_without_stress_lab",
                "does not claim actual hedge failure without stress contribution data",
            ]
        )

    return _weighted_alert(
        "weak_hedge_behavior",
        block_2_1=block_2_1,
        block_2_2=block_2_2,
        block_2_3=block_2_3,
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
        evidence_extra=extra,
        warnings=warnings,
        is_preliminary=is_preliminary,
        confirmation_status=confirmation_status,
        limitations_extra=limitations_extra,
        calculation_extra=calculation_extra,
    )


def _credit_liquidity_risk(block_2_1: dict[str, Any] | None, block_2_2: dict[str, Any] | None, block_2_3: dict[str, Any] | None) -> dict[str, Any]:
    credit = _breakdown_weight(block_2_1, "by_main_risk_factor", {"credit", "liquidity"})
    risk_roles = _breakdown_weight(block_2_1, "by_risk_role", {"risk_on", "carry", "liquidity"})
    extra: list[dict[str, Any]] = []
    for flag_ids, metric, interpretation in (
        (
            {"single_region_dominance"},
            "region_concentration_flags",
            "Block 2.1 concentration flags for single-region dominance.",
        ),
        (
            {"single_asset_class_dominance"},
            "asset_class_concentration_flags",
            "Block 2.1 concentration flags for single asset-class dominance.",
        ),
    ):
        row = _concentration_flag_evidence(
            block_2_1,
            flag_ids=flag_ids,
            metric=metric,
            interpretation=interpretation,
        )
        if row is not None:
            extra.append(row)
    extra.extend(
        _factor_subsignal_evidence(
            block_2_3,
            include_variance=True,
            include_ranking=True,
            stability_keys=("beta_credit",),
            kalman_keys=("beta_credit",),
            supplemental_beta_keys=("beta_us_growth",),
        )
    )
    return _weighted_alert(
        "credit_liquidity_risk",
        block_2_1=block_2_1,
        block_2_2=block_2_2,
        block_2_3=block_2_3,
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
        evidence_extra=extra,
        calculation_extra=["credit/liquidity thresholds are heuristic_v2 product diagnostics"],
    )


def _correlation_concentration(
    block_2_1: dict[str, Any] | None,
    block_2_2: dict[str, Any] | None,
    block_2_3: dict[str, Any] | None = None,
    *,
    legacy_enrichment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    pair = _top_pair_correlation(block_2_2)
    duplicate = _duplicate_exposure_weight(block_2_1)
    dominant = _dominant_breakdown_weight(block_2_1, "by_main_risk_factor")
    extra: list[dict[str, Any]] = []
    group_evidence = _duplicate_exposure_group_evidence(block_2_1)
    if group_evidence is not None:
        extra.append(group_evidence)
    extra.extend(_currency_concentration_evidence(block_2_1, block_2_2))
    extra.extend(_correlation_subsignal_evidence(block_2_2))
    extra.extend(
        _factor_subsignal_evidence(
            block_2_3,
            include_variance=True,
            include_ranking=True,
        )
    )
    extra.extend(_legacy_pca_cross_ref_evidence(legacy_enrichment))
    calculation_extra = ["correlation concentration thresholds are heuristic_v2 product diagnostics"]
    if isinstance(legacy_enrichment, dict) and legacy_enrichment.get("available"):
        calculation_extra.append("legacy_pca_cross_ref_wire_time=sections.hidden_risk_detector")
    return _weighted_alert(
        "correlation_concentration",
        block_2_1=block_2_1,
        block_2_2=block_2_2,
        block_2_3=block_2_3,
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
        evidence_extra=extra,
        calculation_extra=calculation_extra,
    )


def _unrecovered_drawdown_flag(block_2_2: dict[str, Any] | None) -> float | None:
    recovered = _path(block_2_2, "drawdown_diagnostics", "recovered")
    if recovered is None:
        return None
    if isinstance(recovered, bool):
        return 0.0 if recovered else 1.0
    return None


def _longest_underwater_months(block_2_2: dict[str, Any] | None) -> float | None:
    value = _path(block_2_2, "drawdown_diagnostics", "longest_underwater")
    if value is None:
        return None
    number = _as_float(value)
    if number is None:
        return None
    return number


def _rolling_vol_latest(block_2_2: dict[str, Any] | None) -> float | None:
    return _as_float(
        _path(
            block_2_2,
            "rolling_diagnostics",
            "core_view",
            "rolling_volatility_12m",
            "latest",
        )
    )


def _tail_drawdown_evidence(block_2_2: dict[str, Any] | None) -> list[dict[str, Any]]:
    extra: list[dict[str, Any]] = []
    recovered = _path(block_2_2, "drawdown_diagnostics", "recovered")
    if recovered is not None:
        extra.append(
            _evidence(
                metric="drawdown_recovered",
                value=bool(recovered),
                threshold="false_elevates_unrecovered_drawdown_score",
                direction="conflicting" if recovered is False else "below_threshold",
                source="block_2_2",
                interpretation="Whether the deepest drawdown episode has recovered per Block 2.2.",
            )
        )
    recovery_months = _as_float(_path(block_2_2, "drawdown_diagnostics", "recovery_months"))
    if recovery_months is not None:
        extra.append(
            _evidence(
                metric="recovery_months",
                value=recovery_months,
                threshold="informational_only",
                direction="present",
                source="block_2_2",
                interpretation="Months to recover from the deepest drawdown episode when available.",
            )
        )
    return extra


def _tail_vol_instability_evidence(block_2_2: dict[str, Any] | None) -> list[dict[str, Any]]:
    extra: list[dict[str, Any]] = []
    metadata = _path(block_2_2, "metadata")
    if isinstance(metadata, dict):
        for metric in ("vol_of_vol", "rel_vol_of_vol"):
            value = _as_float(metadata.get(metric))
            if value is None:
                continue
            extra.append(
                _evidence(
                    metric=metric,
                    value=value,
                    threshold={"moderate_gte": 0.15, "high_gte": 0.25},
                    direction=_numeric_evidence_direction(value, moderate=0.15, high=0.25),
                    source="block_2_2",
                    interpretation=(
                        f"{metric} from Block 2.2 metadata; proxy for volatility instability "
                        "(not a formal regime-change detector)."
                    ),
                )
            )
    rolling_vol = _rolling_vol_latest(block_2_2)
    if rolling_vol is not None:
        extra.append(
            _evidence(
                metric="rolling_volatility_12m_latest",
                value=rolling_vol,
                threshold="informational_latest_panel",
                direction="present",
                source="block_2_2",
                interpretation=(
                    "Latest 12-month rolling annualized volatility from Block 2.2 panel "
                    "(full series in referenced CSV)."
                ),
            )
        )
    return extra


def _tail_supplemental_evidence(block_2_2: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Informational tail metrics retained from heuristic_v1 scoring set."""
    extra: list[dict[str, Any]] = []
    for metric, path_keys, interpretation in (
        (
            "eee_10",
            ("tail_risk_diagnostics", "eee_10"),
            "Expected exceedance estimate at 10% when available.",
        ),
        (
            "skewness",
            ("return_risk_metrics", "skewness"),
            "Negative skewness can indicate left-tail asymmetry.",
        ),
        (
            "kurtosis",
            ("return_risk_metrics", "kurtosis"),
            "High kurtosis can indicate fat tails.",
        ),
        (
            "count_drawdowns_gt_20",
            ("drawdown_diagnostics", "count_drawdowns_gt_20"),
            "Count of drawdowns deeper than 20%.",
        ),
    ):
        value = _as_float(_path(block_2_2, *path_keys))
        if value is None:
            continue
        extra.append(
            _evidence(
                metric=metric,
                value=value,
                threshold="informational_only",
                direction="present",
                source="block_2_2",
                interpretation=interpretation,
            )
        )
    return extra


def _tail_risk(block_2_2: dict[str, Any] | None, block_2_3: dict[str, Any] | None = None) -> dict[str, Any]:
    extra = _factor_subsignal_evidence(
        block_2_3,
        include_variance=True,
        include_ranking=True,
        stability_keys=("beta_vix",),
        kalman_keys=("beta_vix",),
        supplemental_beta_keys=("beta_vix",),
    )
    extra.extend(_tail_drawdown_evidence(block_2_2))
    extra.extend(_tail_vol_instability_evidence(block_2_2))
    extra.extend(_tail_supplemental_evidence(block_2_2))
    return _weighted_alert(
        "tail_risk",
        block_2_2=block_2_2,
        block_2_3=block_2_3,
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
            "var_95": (
                _as_float(_path(block_2_2, "tail_risk_diagnostics", "var_95")),
                "block_2_2",
                "Daily historical VaR95 from Block 2.2 tail diagnostics.",
            ),
            "var_99": (
                _as_float(_path(block_2_2, "tail_risk_diagnostics", "var_99")),
                "block_2_2",
                "Daily historical VaR99 from Block 2.2 tail diagnostics.",
            ),
            "downside_deviation": (
                _as_float(_path(block_2_2, "tail_risk_diagnostics", "downside_deviation")),
                "block_2_2",
                "Annualized downside deviation from Block 2.2.",
            ),
            "max_drawdown": (
                _as_float(_path(block_2_2, "drawdown_diagnostics", "max_drawdown")),
                "block_2_2",
                "Maximum drawdown depth from Block 2.2 drawdown diagnostics.",
            ),
            "pct_time_underwater": (
                _as_float(_path(block_2_2, "drawdown_diagnostics", "pct_time_underwater")),
                "block_2_2",
                "Share of months spent below prior peak equity.",
            ),
            "longest_underwater_months": (
                _longest_underwater_months(block_2_2),
                "block_2_2",
                "Longest underwater spell in months from Block 2.2.",
            ),
            "unrecovered_drawdown": (
                _unrecovered_drawdown_flag(block_2_2),
                "block_2_2",
                "1.0 when deepest drawdown is not yet recovered; 0.0 when recovered.",
            ),
            "count_drawdowns_gt_5": (
                _as_float(_path(block_2_2, "drawdown_diagnostics", "count_drawdowns_gt_5")),
                "block_2_2",
                "Count of drawdowns deeper than 5%.",
            ),
            "count_drawdowns_gt_10": (
                _as_float(_path(block_2_2, "drawdown_diagnostics", "count_drawdowns_gt_10")),
                "block_2_2",
                "Count of drawdowns deeper than 10%.",
            ),
            "downside_beta": (
                _as_float(_path(block_2_2, "benchmark_dependence", "downside_beta")),
                "block_2_2",
                "Downside beta adds tail-behavior context.",
            ),
        },
        evidence_extra=extra,
        calculation_extra=[
            "tail risk scored signals renormalized in Session 07 (var, drawdown persistence, underwater)",
            "tail risk thresholds are heuristic_v2 product diagnostics",
        ],
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
    *,
    taxonomy_rows: dict[str, dict[str, Any]] | None = None,
    stress_enrichment: dict[str, Any] | None = None,
    legacy_enrichment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build product-facing Hidden Exposure diagnostics from Blocks 2.1–2.3 only.

    Optional ``stress_enrichment`` is a compact Block 3 wire-time summary built by
    ``build_block_2_4_stress_enrichment``; optional ``legacy_enrichment`` is a compact
    PCA summary from ``build_block_2_4_legacy_enrichment``. Block 2.4 does not run Stress Lab.
    """
    inputs = [isinstance(block_2_1, dict), isinstance(block_2_2, dict), isinstance(block_2_3, dict)]
    data_quality_warnings: list[str] = []
    if not inputs[0]:
        data_quality_warnings.append("block_2_1 missing")
    if not inputs[1]:
        data_quality_warnings.append("block_2_2 missing")
    if not inputs[2]:
        data_quality_warnings.append("block_2_3 missing")
    if isinstance(block_2_2, dict):
        for warning in block_2_2.get("data_quality_warnings") or []:
            if isinstance(warning, str) and warning and warning not in data_quality_warnings:
                data_quality_warnings.append(warning)

    alerts = {
        "hidden_equity_beta": _hidden_equity_beta(
            block_2_1, block_2_2, block_2_3, taxonomy_rows=taxonomy_rows
        ),
        "duration_concentration": _duration_concentration(
            block_2_1,
            block_2_2,
            block_2_3,
            stress_enrichment=stress_enrichment,
        ),
        "credit_liquidity_risk": _credit_liquidity_risk(block_2_1, block_2_2, block_2_3),
        "correlation_concentration": _correlation_concentration(
            block_2_1,
            block_2_2,
            block_2_3,
            legacy_enrichment=legacy_enrichment,
        ),
        "weak_hedge_behavior": _weak_hedge_behavior(
            block_2_1,
            block_2_2,
            block_2_3,
            stress_enrichment=stress_enrichment,
        ),
        "tail_risk": _tail_risk(block_2_2, block_2_3),
    }
    _attach_contributing_assets(
        alerts,
        block_2_1=block_2_1,
        block_2_2=block_2_2,
        block_2_3=block_2_3,
        taxonomy_rows=taxonomy_rows,
    )

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
            "version": "v2",
            "ruleset": RULE_VERSION,
            "threshold_policy": RULE_VERSION,
            "confidence_model": CONFIDENCE_MODEL_VERSION,
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
            "blocked_upstream_fields": [dict(row) for row in BLOCKED_UPSTREAM_FIELDS],
            "stress_enrichment_wire_time": bool(
                isinstance(stress_enrichment, dict) and stress_enrichment.get("available")
            ),
            "stress_enrichment_sources": (
                list(stress_enrichment.get("sources") or [])
                if isinstance(stress_enrichment, dict)
                else []
            ),
            "legacy_enrichment_wire_time": bool(
                isinstance(legacy_enrichment, dict) and legacy_enrichment.get("available")
            ),
            "legacy_enrichment_sources": (
                list(legacy_enrichment.get("sources") or [])
                if isinstance(legacy_enrichment, dict)
                else []
            ),
        },
    }


__all__ = [
    "ALERT_IDS",
    "ALERT_RULES",
    "CONFIRMATION_STATUSES",
    "CONFIDENCE_MODEL_VERSION",
    "DIVERSIFYING_PAIR_CORR_THRESHOLD",
    "FACTOR_BETA_HIGH_ABS",
    "FACTOR_BETA_MODERATE_ABS",
    "FACTOR_VARIANCE_DOMINANT_SHARE",
    "HIGH_AVG_PAIRWISE_CORR_THRESHOLD",
    "BLOCKED_UPSTREAM_FIELDS",
    "BLOCK_2_4_ID",
    "BLOCK_2_4_NAME",
    "EVIDENCE_DIRECTIONS",
    "EVIDENCE_SOURCES",
    "MAX_CONTRIBUTING_ASSETS",
    "RULE_VERSION",
    "STATUS_BANDS",
    "LEGACY_PCA_RAW_SECTION",
    "LEGACY_PCA_RESIDUAL_SECTION",
    "PCA_PC1_HIGH",
    "PCA_PC1_MODERATE",
    "build_block_2_4_hidden_exposure",
    "build_block_2_4_legacy_enrichment",
    "build_block_2_4_stress_enrichment",
]
