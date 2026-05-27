"""Block 2.1 Asset Allocation — product-facing capital structure diagnostics."""
from __future__ import annotations

from typing import Any

from src.io_export import REPORT_DECIMALS
from src.real_cash import collect_real_cash_tickers, is_real_cash_ticker

BLOCK_2_1_ID = "2.1_asset_allocation"
REAL_CASH_TAXONOMY_SOURCE = "real_cash_synthetic_v1"

# Canonical registry: docs/specs/portfolio_xray_diagnostics_spec.md §2.1.2
ALLOCATION_CONCENTRATION_THRESHOLDS: dict[str, float] = {
    "top_holding_concentration_medium": 0.20,
    "top_holding_concentration_high": 0.30,
    "top3_concentration_medium": 0.50,
    "top3_concentration_high": 0.65,
    "single_asset_class_dominance_medium": 0.60,
    "single_asset_class_dominance_high": 0.75,
    "single_main_risk_factor_dominance_medium": 0.60,
    "single_main_risk_factor_dominance_high": 0.75,
    "single_region_dominance_medium": 0.70,
    "single_region_dominance_high": 0.85,
    "single_currency_dominance_medium": 0.70,
    "single_currency_dominance_high": 0.85,
}

DUPLICATE_EXPOSURE_MEDIUM = 0.10
DUPLICATE_EXPOSURE_HIGH = 0.20


def _as_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        out = float(value)
        if out != out:
            return None
        return out
    except (TypeError, ValueError):
        return None


def _positive_weights(weights: dict[str, Any] | None) -> dict[str, float]:
    out: dict[str, float] = {}
    for ticker, value in (weights or {}).items():
        number = _as_float(value)
        if number is not None and number > 0:
            out[str(ticker)] = number
    return out


def _weight_pct_fraction(weight_fraction: float) -> float:
    return round(weight_fraction * 100.0, REPORT_DECIMALS)


def _breakdown_rows(totals: dict[str, float]) -> list[dict[str, Any]]:
    return [
        {"name": name, "weight_pct": _weight_pct_fraction(weight)}
        for name, weight in sorted(totals.items(), key=lambda x: (-x[1], x[0]))
    ]


def _dominant_bucket(totals: dict[str, float]) -> dict[str, Any] | None:
    if not totals:
        return None
    max_weight = max(totals.values())
    names = sorted(name for name, weight in totals.items() if weight == max_weight)
    if not names:
        return None
    name = names[0]
    return {"name": name, "weight_pct": _weight_pct_fraction(max_weight)}


def _synthetic_real_cash_row(ticker: str, *, investor_currency: str | None) -> dict[str, Any]:
    upper = str(ticker).strip().upper()
    currency = "unknown"
    region = "unknown"
    if upper == "CASH":
        currency = str(investor_currency or "unknown").strip().upper() or "unknown"
        region = "US" if currency == "USD" else "unknown"
    elif upper.startswith("CASH "):
        parts = upper.split()
        if len(parts) >= 2:
            currency = parts[1]
            region = "US" if currency == "USD" else "unknown"
    elif ticker.lower().startswith("cash ") and len(ticker.split()) >= 2:
        currency = ticker.split()[1].strip().upper()
        region = "US" if currency == "USD" else "unknown"
    return {
        "asset_class": "cash",
        "region": region,
        "currency_exposure": currency,
        "risk_role": ["cash", "liquidity", "defensive"],
        "main_risk_factor": "cash",
        "secondary_risk_factors": [],
        "duplicate_group_id": "",
        "canonical_ticker": "",
    }


def enrich_taxonomy_with_real_cash(
    weights: dict[str, float],
    taxonomy_rows: dict[str, dict[str, Any]],
    taxonomy_sources: dict[str, str],
    *,
    investor_currency: str | None = None,
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    """Overlay synthetic taxonomy rows for real-cash holdings (does not alter ETF YAML)."""
    rows = {str(k).upper(): dict(v) for k, v in taxonomy_rows.items() if isinstance(v, dict)}
    sources = {str(k).upper(): str(v) for k, v in taxonomy_sources.items()}
    for label in collect_real_cash_tickers(weights=weights):
        key = label.upper()
        rows[key] = _synthetic_real_cash_row(label, investor_currency=investor_currency)
        sources[key] = REAL_CASH_TAXONOMY_SOURCE
    return rows, sources


def _row_for_ticker(ticker: str, rows: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    return rows.get(str(ticker).upper()) or rows.get(str(ticker))


def _aggregate_dimension(
    holdings: list[tuple[str, float, dict[str, Any]]],
    field: str,
    *,
    list_field: bool = False,
) -> dict[str, float]:
    totals: dict[str, float] = {}
    for _ticker, weight, tax in holdings:
        value = tax.get(field)
        if list_field:
            tags = value if isinstance(value, list) else []
            tags = [str(v).strip() for v in tags if str(v).strip()] or ["unknown"]
            split = weight / max(len(tags), 1)
            for tag in tags:
                totals[tag] = totals.get(tag, 0.0) + split
        else:
            label = str(value or "unknown").strip() or "unknown"
            totals[label] = totals.get(label, 0.0) + weight
    return totals


def _holding_rows(
    weight_map: dict[str, float],
    taxonomy_rows: dict[str, dict[str, Any]],
) -> tuple[list[tuple[str, float, dict[str, Any]]], float]:
    holdings: list[tuple[str, float, dict[str, Any]]] = []
    unknown_weight = 0.0
    for ticker, weight in weight_map.items():
        tax = _row_for_ticker(ticker, taxonomy_rows) or {}
        if not tax:
            unknown_weight += weight
            tax = {
                "asset_class": "unknown",
                "region": "unknown",
                "currency_exposure": "unknown",
                "main_risk_factor": "unknown",
                "risk_role": ["unknown"],
                "duplicate_group_id": "",
                "canonical_ticker": "",
            }
        holdings.append((ticker, weight, tax))
    return holdings, unknown_weight


def _concentration_flag(
    *,
    flag_id: str,
    severity: str,
    metric: str,
    observed: float,
    threshold: float,
    dimension: str | None = None,
    label: str | None = None,
) -> dict[str, Any]:
    pct_obs = _weight_pct_fraction(observed)
    pct_thr = _weight_pct_fraction(threshold)
    if dimension and label:
        message = (
            f"{label} {dimension.replace('_', ' ')} concentration is {pct_obs:.3f}% "
            f"({severity} diagnostic threshold {pct_thr:.3f}%)."
        )
    elif flag_id == "top_holding_concentration":
        message = (
            f"Top holding weight is {pct_obs:.3f}% "
            f"({severity} diagnostic threshold {pct_thr:.3f}%)."
        )
    elif flag_id == "top3_concentration":
        message = (
            f"Top three holdings sum to {pct_obs:.3f}% "
            f"({severity} diagnostic threshold {pct_thr:.3f}%)."
        )
    else:
        message = (
            f"Observed share {pct_obs:.3f}% exceeds {severity} threshold {pct_thr:.3f}%."
        )
    return {
        "flag_id": flag_id,
        "severity": severity,
        "metric": metric,
        "dimension": dimension,
        "label": label,
        "threshold": threshold,
        "observed": observed,
        "message": message,
    }


def _build_concentration_flags(
    *,
    top1: float,
    top3: float,
    asset_class: dict[str, float],
    main_risk_factor: dict[str, float],
    region: dict[str, float],
    currency: dict[str, float],
) -> list[dict[str, Any]]:
    flags: list[dict[str, Any]] = []
    pairs = (
        ("top_holding_concentration", top1, "top1_weight", None, None),
        ("top3_concentration", top3, "top3_weight", None, None),
    )
    for flag_id, observed, metric, dimension, label in pairs:
        for severity, key in (("medium", f"{flag_id}_medium"), ("high", f"{flag_id}_high")):
            threshold = ALLOCATION_CONCENTRATION_THRESHOLDS[key]
            if observed >= threshold:
                flags.append(
                    _concentration_flag(
                        flag_id=flag_id,
                        severity=severity,
                        metric=metric,
                        observed=observed,
                        threshold=threshold,
                        dimension=dimension,
                        label=label,
                    )
                )

    bucket_specs = (
        ("single_asset_class_dominance", asset_class, "asset_class"),
        ("single_main_risk_factor_dominance", main_risk_factor, "main_risk_factor"),
        ("single_region_dominance", region, "region"),
        ("single_currency_dominance", currency, "currency_exposure"),
    )
    for flag_id, totals, dimension in bucket_specs:
        if not totals:
            continue
        observed = max(totals.values())
        label = sorted(name for name, w in totals.items() if w == observed)[0]
        for severity, key in (("medium", f"{flag_id}_medium"), ("high", f"{flag_id}_high")):
            threshold = ALLOCATION_CONCENTRATION_THRESHOLDS[key]
            if observed >= threshold:
                flags.append(
                    _concentration_flag(
                        flag_id=flag_id,
                        severity=severity,
                        metric=f"{dimension}_weight",
                        observed=observed,
                        threshold=threshold,
                        dimension=dimension,
                        label=label,
                    )
                )
    return flags


def _build_duplicate_flags(
    holdings: list[tuple[str, float, dict[str, Any]]],
) -> list[dict[str, Any]]:
    groups: dict[str, list[tuple[str, float, str | None]]] = {}
    for ticker, weight, tax in holdings:
        group_id = str(tax.get("duplicate_group_id") or "").strip()
        if not group_id:
            continue
        canonical = str(tax.get("canonical_ticker") or "").strip() or None
        groups.setdefault(group_id, []).append((ticker, weight, canonical))

    flags: list[dict[str, Any]] = []
    for group_id, members in sorted(groups.items()):
        if len(members) < 2:
            continue
        tickers = [t for t, _, _ in members]
        combined = sum(w for _, w, _ in members)
        canonicals = {c for _, _, c in members if c}
        canonical = sorted(canonicals)[0] if len(canonicals) == 1 else (sorted(canonicals)[0] if canonicals else None)
        severity = "high" if combined >= DUPLICATE_EXPOSURE_HIGH else (
            "medium" if combined >= DUPLICATE_EXPOSURE_MEDIUM else None
        )
        if severity is None:
            continue
        pct = _weight_pct_fraction(combined)
        flags.append(
            {
                "duplicate_group_id": group_id,
                "tickers": tickers,
                "combined_weight": round(combined, REPORT_DECIMALS),
                "combined_weight_pct": pct,
                "canonical_ticker": canonical,
                "severity": severity,
                "message": (
                    f"Duplicate exposure group {group_id!r} combines {pct:.3f}% across "
                    f"{len(tickers)} holdings ({', '.join(tickers)})."
                ),
            }
        )
    return flags


def _economic_summary(
    *,
    snapshot: dict[str, Any],
    breakdown: dict[str, Any],
    concentration_flags: list[dict[str, Any]],
    duplicate_flags: list[dict[str, Any]],
    data_quality_warnings: list[str],
    real_cash_labels: list[str],
) -> dict[str, Any]:
    dom_class = snapshot.get("dominant_asset_class") or {}
    dom_factor = snapshot.get("dominant_main_risk_factor") or {}
    dom_region = snapshot.get("dominant_region") or {}
    top1 = snapshot.get("top1_holding") or {}
    headline_parts: list[str] = []
    if dom_class.get("name"):
        headline_parts.append(
            f"capital is weighted toward {dom_class['name']} ({dom_class.get('weight_pct', 0):.3f}%)"
        )
    if dom_factor.get("name"):
        headline_parts.append(
            f"main risk factor exposure is {dom_factor['name']} ({dom_factor.get('weight_pct', 0):.3f}%)"
        )
    if not headline_parts:
        headline = "Portfolio capital structure is diversified across labeled economic buckets."
    else:
        headline = "The portfolio's economic structure is " + " and ".join(headline_parts) + "."

    key_points: list[str] = []
    if top1.get("ticker"):
        key_points.append(
            f"Largest holding: {top1['ticker']} at {top1.get('weight_pct', 0):.3f}% of capital."
        )
    if dom_region.get("name"):
        key_points.append(
            f"Dominant region label: {dom_region['name']} ({dom_region.get('weight_pct', 0):.3f}%)."
        )
    by_class = breakdown.get("by_asset_class") or []
    if by_class:
        top_buckets = ", ".join(
            f"{row['name']} {row['weight_pct']:.3f}%" for row in by_class[:3]
        )
        key_points.append(f"Asset class mix (top buckets): {top_buckets}.")
    if real_cash_labels:
        key_points.append(
            "Explicit bank cash is modeled as a zero-return holding (not the technical cash proxy ETF)."
        )
    for flag in concentration_flags:
        if flag.get("severity") == "high":
            key_points.append(str(flag.get("message")))
    for dup in duplicate_flags:
        key_points.append(str(dup.get("message")))
    for warning in data_quality_warnings[:3]:
        key_points.append(warning)
    if not key_points:
        key_points.append("No material concentration or duplicate-exposure flags under Block 2.1 rules.")
    return {"headline": headline, "key_points": key_points[:5]}


def _setup_context(analysis_setup: dict[str, Any] | None) -> tuple[str, str, str]:
    if not isinstance(analysis_setup, dict):
        return "unknown", "unknown", "unknown"
    portfolio_input = analysis_setup.get("portfolio_input")
    if not isinstance(portfolio_input, dict):
        portfolio_input = {}
    subject = analysis_setup.get("analysis_subject")
    subject_type = "unknown"
    if isinstance(subject, dict) and subject.get("type"):
        subject_type = str(subject["type"])
    elif portfolio_input.get("analysis_subject_type"):
        subject_type = str(portfolio_input["analysis_subject_type"])
    analysis_mode = str(
        portfolio_input.get("source_analysis_mode")
        or analysis_setup.get("analysis_mode")
        or "unknown"
    )
    investor_currency = str(portfolio_input.get("investor_currency") or "unknown")
    return subject_type, analysis_mode, investor_currency


def build_block_2_1_asset_allocation(
    *,
    analysis_setup: dict[str, Any] | None,
    weights: dict[str, Any] | None,
    taxonomy_rows: dict[str, dict[str, Any]] | None,
    taxonomy_sources: dict[str, str] | None,
) -> dict[str, Any]:
    """Build Block 2.1 product contract from weights and taxonomy annotations."""
    subject_type, analysis_mode, investor_currency = _setup_context(analysis_setup)
    weight_map = _positive_weights(weights)

    rows_in = taxonomy_rows if isinstance(taxonomy_rows, dict) else {}
    sources_in = taxonomy_sources if isinstance(taxonomy_sources, dict) else {}
    tax_rows, tax_sources = enrich_taxonomy_with_real_cash(
        weight_map,
        {str(k).upper(): v for k, v in rows_in.items() if isinstance(v, dict)},
        {str(k).upper(): str(v) for k, v in sources_in.items()},
        investor_currency=investor_currency,
    )

    data_quality_warnings: list[str] = []
    informational_disclosures: list[str] = []
    real_cash_labels = collect_real_cash_tickers(weights=weight_map)

    if not weight_map:
        data_quality_warnings.append("No positive capital weights available for Block 2.1 allocation.")
        return {
            "block": BLOCK_2_1_ID,
            "analysis_subject": subject_type,
            "analysis_mode": analysis_mode,
            "investor_currency": investor_currency,
            "portfolio_composition_snapshot": {
                "total_holdings": 0,
                "top1_holding": {"ticker": None, "weight_pct": None},
                "top3_holdings": [],
                "top3_weight_pct": None,
                "dominant_asset_class": None,
                "dominant_risk_role": None,
                "dominant_main_risk_factor": None,
                "dominant_region": None,
                "dominant_currency": None,
            },
            "capital_allocation_breakdown": {
                "by_asset": [],
                "by_asset_class": [],
                "by_main_risk_factor": [],
                "by_risk_role": [],
                "by_region": [],
                "by_currency": [],
            },
            "concentration_flags": [],
            "duplicate_exposure_flags": [],
            "actual_economic_exposure_summary": {
                "headline": "Capital allocation diagnostics are unavailable because no positive weights were provided.",
                "key_points": [],
            },
            "data_quality_warnings": data_quality_warnings,
            "metadata": {
                "source": "core_mvp_input",
                "cash_treatment": "market_tickers_only",
                "cash_proxy_used_for_real_cash": False,
                "taxonomy_sources": sorted(set(tax_sources.values())),
                "allocation_concentration_thresholds": dict(ALLOCATION_CONCENTRATION_THRESHOLDS),
            },
        }

    holdings, unknown_weight = _holding_rows(weight_map, tax_rows)
    if unknown_weight > 0:
        data_quality_warnings.append(
            f"{_weight_pct_fraction(unknown_weight):.3f}% of capital weight lacks ETF/stock taxonomy coverage."
        )
    if real_cash_labels:
        informational_disclosures.append(
            "Cash holdings are treated as real cash positions with zero return, zero volatility, and no price download; this is expected policy behavior and not a taxonomy failure."
        )

    sorted_holdings = sorted(holdings, key=lambda x: (-x[1], x[0]))
    top3 = sorted_holdings[:3]
    top1_ticker, top1_w = top3[0][0], top3[0][1]
    top3_sum = sum(w for _, w, _ in top3)

    asset_class = _aggregate_dimension(holdings, "asset_class")
    main_factor = _aggregate_dimension(holdings, "main_risk_factor")
    risk_role = _aggregate_dimension(holdings, "risk_role", list_field=True)
    region = _aggregate_dimension(holdings, "region")
    currency = _aggregate_dimension(holdings, "currency_exposure")

    by_asset = _breakdown_rows({ticker: weight for ticker, weight, _ in holdings})

    snapshot = {
        "total_holdings": len(holdings),
        "top1_holding": {"ticker": top1_ticker, "weight_pct": _weight_pct_fraction(top1_w)},
        "top3_holdings": [
            {"ticker": ticker, "weight_pct": _weight_pct_fraction(weight)} for ticker, weight, _ in top3
        ],
        "top3_weight_pct": _weight_pct_fraction(top3_sum),
        "dominant_asset_class": _dominant_bucket(asset_class),
        "dominant_risk_role": _dominant_bucket(risk_role),
        "dominant_main_risk_factor": _dominant_bucket(main_factor),
        "dominant_region": _dominant_bucket(region),
        "dominant_currency": _dominant_bucket(currency),
    }

    breakdown = {
        "by_asset": by_asset,
        "by_asset_class": _breakdown_rows(asset_class),
        "by_main_risk_factor": _breakdown_rows(main_factor),
        "by_risk_role": _breakdown_rows(risk_role),
        "by_region": _breakdown_rows(region),
        "by_currency": _breakdown_rows(currency),
    }

    concentration_flags = _build_concentration_flags(
        top1=top1_w,
        top3=top3_sum,
        asset_class=asset_class,
        main_risk_factor=main_factor,
        region=region,
        currency=currency,
    )
    duplicate_flags = _build_duplicate_flags(holdings)

    cash_treatment = "real_cash_position_if_present" if real_cash_labels else "market_tickers_only"
    metadata = {
        "source": "core_mvp_input",
        "cash_treatment": cash_treatment,
        "cash_proxy_used_for_real_cash": False,
        "taxonomy_sources": sorted(set(tax_sources.values())),
        "allocation_concentration_thresholds": dict(ALLOCATION_CONCENTRATION_THRESHOLDS),
    }

    economic = _economic_summary(
        snapshot=snapshot,
        breakdown=breakdown,
        concentration_flags=concentration_flags,
        duplicate_flags=duplicate_flags,
        data_quality_warnings=data_quality_warnings,
        real_cash_labels=real_cash_labels,
    )

    return {
        "block": BLOCK_2_1_ID,
        "analysis_subject": subject_type,
        "analysis_mode": analysis_mode,
        "investor_currency": investor_currency,
        "portfolio_composition_snapshot": snapshot,
        "capital_allocation_breakdown": breakdown,
        "concentration_flags": concentration_flags,
        "duplicate_exposure_flags": duplicate_flags,
        "actual_economic_exposure_summary": economic,
        "data_quality_warnings": data_quality_warnings,
        "informational_disclosures": informational_disclosures,
        "metadata": metadata,
    }


__all__ = [
    "ALLOCATION_CONCENTRATION_THRESHOLDS",
    "BLOCK_2_1_ID",
    "REAL_CASH_TAXONOMY_SOURCE",
    "build_block_2_1_asset_allocation",
    "enrich_taxonomy_with_real_cash",
]
