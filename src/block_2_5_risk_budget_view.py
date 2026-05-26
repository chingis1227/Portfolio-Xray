"""Block 2.5 Risk Budget View — capital weight vs RC_vol product diagnostics.

Read-only adapter over Block 2.1 capital weights and wire-time RC rows from
``resolve_rc_asset_for_xray``.  Does not recompute covariance, read stress_report,
or perform file I/O.
"""
from __future__ import annotations

from typing import Any

from src.io_export import REPORT_DECIMALS
from src.risk_budgeting import risk_budget_bucket_from_row

BLOCK_2_5_ID = "2.5_risk_budget_view"
BLOCK_2_5_NAME = "Risk Budget View"
RULE_VERSION = "rc_adapter_v1"

FORBIDDEN_STRESS_KEYS = frozenset(
    {
        "worst_stress_loss_contribution_pct",
        "worst_stress_scenario",
        "worst_stress_loss",
        "stress_scenario",
        "pnl_by_asset_pct",
    }
)


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


def _round_export(value: float) -> float:
    return round(value, REPORT_DECIMALS)


def _rc_window_label_from_sources(sources: list[str] | tuple[str, ...] | None) -> str:
    joined = " ".join(str(s) for s in sources or []).lower()
    if "rc_vol_10y" in joined:
        return "10Y (120M)"
    if "rc_vol_5y" in joined:
        return "5Y (60M)"
    if "rc_vol_3y" in joined:
        return "3Y (36M)"
    if "snapshot.rc_asset" in joined:
        return "10Y display subset (snapshot.RC_asset top-N)"
    if "rc_vol_map" in joined:
        return "RC_vol map (window per upstream CSV)"
    return "n/a"


def _weights_fraction_from_block_2_1(block_2_1: dict[str, Any] | None) -> dict[str, float]:
    if not isinstance(block_2_1, dict):
        return {}
    breakdown = block_2_1.get("capital_allocation_breakdown")
    if not isinstance(breakdown, dict):
        return {}
    by_asset = breakdown.get("by_asset")
    if not isinstance(by_asset, list):
        return {}
    out: dict[str, float] = {}
    for row in by_asset:
        if not isinstance(row, dict):
            continue
        ticker = row.get("name") or row.get("ticker")
        weight_pct = _as_float(row.get("weight_pct"))
        if ticker is None or weight_pct is None or weight_pct <= 0:
            continue
        out[str(ticker)] = weight_pct / 100.0
    return out


def _rc_map_from_rows(rc_asset_rows: list[dict[str, Any]] | None) -> dict[str, float]:
    out: dict[str, float] = {}
    for row in rc_asset_rows or []:
        if not isinstance(row, dict):
            continue
        ticker = row.get("ticker")
        rc = _as_float(row.get("rc_pct"))
        if rc is None:
            rc = _as_float(row.get("rc_vol"))
        if rc is None:
            rc = _as_float(row.get("value"))
        if ticker is None or rc is None:
            continue
        out[str(ticker)] = rc
    return out


def _asset_row(ticker: str, weight: float | None, rc: float | None) -> dict[str, Any]:
    gap = (rc - weight) if rc is not None and weight is not None else None
    row: dict[str, Any] = {"ticker": ticker}
    if weight is not None:
        row["weight_pct"] = _round_export(weight * 100.0)
    else:
        row["weight_pct"] = None
    if rc is not None:
        row["rc_vol"] = _round_export(rc)
        row["risk_contribution_pct"] = _round_export(rc * 100.0)
    else:
        row["rc_vol"] = None
        row["risk_contribution_pct"] = None
    if gap is not None:
        row["weight_vs_risk_gap"] = _round_export(gap)
        row["weight_vs_risk_gap_pp"] = _round_export(gap * 100.0)
    else:
        row["weight_vs_risk_gap"] = None
        row["weight_vs_risk_gap_pp"] = None
    return row


def _sort_assets(assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        assets,
        key=lambda row: (
            -(_as_float(row.get("rc_vol")) or 0.0),
            -abs(_as_float(row.get("weight_vs_risk_gap")) or 0.0),
            str(row.get("ticker")),
        ),
    )


def _block_status(
    weight_map: dict[str, float],
    rc_map: dict[str, float],
) -> tuple[str, list[str]]:
    warnings: list[str] = []
    if not rc_map:
        warnings.append("RC_vol diagnostics are missing.")
        return "unavailable", warnings
    if not weight_map:
        warnings.append("Block 2.1 capital weights are missing.")
        return "unavailable", warnings
    missing = sorted(ticker for ticker in weight_map if ticker not in rc_map)
    if missing:
        warnings.append(
            f"RC_vol missing for {len(missing)} positive-weight holding(s): {', '.join(missing)}."
        )
        return "partial", warnings
    return "ok", warnings


def _summary_asset_snapshot(row: dict[str, Any]) -> dict[str, Any] | None:
    ticker = row.get("ticker")
    rc_pct = _as_float(row.get("risk_contribution_pct"))
    if ticker is None or rc_pct is None:
        return None
    weight_pct = _as_float(row.get("weight_pct"))
    gap_pp = _as_float(row.get("weight_vs_risk_gap_pp"))
    return {
        "ticker": str(ticker),
        "weight_pct": _round_export(weight_pct) if weight_pct is not None else None,
        "rc_pct": _round_export(rc_pct),
        "weight_vs_risk_gap_pp": _round_export(gap_pp) if gap_pp is not None else None,
    }


def _normalize_taxonomy_rows(
    taxonomy_rows: dict[str, Any] | list[dict[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    if taxonomy_rows is None:
        return {}
    if isinstance(taxonomy_rows, dict):
        return {
            str(k).upper(): dict(v)
            for k, v in taxonomy_rows.items()
            if isinstance(v, dict)
        }
    if isinstance(taxonomy_rows, list):
        out: dict[str, dict[str, Any]] = {}
        for row in taxonomy_rows:
            if not isinstance(row, dict):
                continue
            ticker = row.get("ticker") or row.get("name")
            if ticker is None:
                continue
            out[str(ticker).upper()] = row
        return out
    return {}


def _taxonomy_row_for_ticker(
    ticker: str,
    taxonomy_rows: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    return taxonomy_rows.get(str(ticker).upper()) or taxonomy_rows.get(str(ticker))


def _risk_budget_bucket_contribution(
    weight_map: dict[str, float],
    rc_map: dict[str, float],
    taxonomy_rows: dict[str, Any] | list[dict[str, Any]] | None,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Aggregate capital weight and RC_vol by taxonomy risk-budget bucket."""
    tax = _normalize_taxonomy_rows(taxonomy_rows)
    warnings: list[str] = []
    if not tax:
        if weight_map or rc_map:
            warnings.append(
                "taxonomy_rows missing; risk_budget_bucket_contribution unavailable"
            )
        return [], warnings

    buckets_weight: dict[str, float] = {}
    buckets_rc: dict[str, float] = {}
    missing_tax: list[str] = []

    for ticker in sorted(set(weight_map) | set(rc_map)):
        weight = weight_map.get(ticker) or 0.0
        rc = rc_map.get(ticker)
        if weight <= 0 and rc is None:
            continue
        row = _taxonomy_row_for_ticker(ticker, tax)
        if row is None and weight > 0:
            missing_tax.append(ticker)
        bucket = risk_budget_bucket_from_row(row)
        if weight > 0:
            buckets_weight[bucket] = buckets_weight.get(bucket, 0.0) + weight
        if rc is not None:
            buckets_rc[bucket] = buckets_rc.get(bucket, 0.0) + rc

    if missing_tax:
        warnings.append(
            "Taxonomy row missing for "
            f"{len(missing_tax)} holding(s): {', '.join(missing_tax)}."
        )

    contribution: list[dict[str, Any]] = []
    for bucket in sorted(set(buckets_weight) | set(buckets_rc)):
        weight_frac = buckets_weight.get(bucket, 0.0)
        rc_frac = buckets_rc.get(bucket, 0.0)
        if weight_frac <= 0 and rc_frac <= 0:
            continue
        weight_pct = _round_export(weight_frac * 100.0)
        rc_pct = _round_export(rc_frac * 100.0)
        contribution.append(
            {
                "bucket": bucket,
                "weight_pct": weight_pct,
                "rc_pct": rc_pct,
                "gap_pp": _round_export((rc_frac - weight_frac) * 100.0),
            }
        )

    contribution.sort(
        key=lambda row: (-row["rc_pct"], -row["weight_pct"], str(row["bucket"]))
    )
    return contribution, warnings


def _portfolio_aggregates(assets: list[dict[str, Any]]) -> dict[str, Any]:
    rc_ranked: list[dict[str, Any]] = []
    gap_ranked: list[dict[str, Any]] = []
    for row in assets:
        snap = _summary_asset_snapshot(row)
        if snap is None:
            continue
        rc_ranked.append(snap)
        gap_pp = snap.get("weight_vs_risk_gap_pp")
        if gap_pp is not None:
            gap_ranked.append(snap)

    rc_ranked.sort(key=lambda item: (-item["rc_pct"], item["ticker"]))
    top3 = rc_ranked[:3]
    top3_share = (
        _round_export(sum(item["rc_pct"] for item in top3)) if top3 else None
    )

    overweight = sorted(
        (item for item in gap_ranked if (item["weight_vs_risk_gap_pp"] or 0) > 0),
        key=lambda item: (-item["weight_vs_risk_gap_pp"], item["ticker"]),
    )[:5]
    underweight = sorted(
        (item for item in gap_ranked if (item["weight_vs_risk_gap_pp"] or 0) < 0),
        key=lambda item: (item["weight_vs_risk_gap_pp"], item["ticker"]),
    )[:5]

    return {
        "top1_rc_asset": rc_ranked[0] if rc_ranked else {},
        "top3_rc_assets": top3,
        "top3_rc_share": top3_share,
        "top_risk_overweight_assets": overweight,
        "top_risk_underweight_assets": underweight,
    }


def _summary_for_status(
    status: str,
    *,
    top1: dict[str, Any],
    top3_share: float | None,
    top_overweight: list[dict[str, Any]],
    top_underweight: list[dict[str, Any]],
) -> str:
    if status == "unavailable":
        return "Risk budget view is unavailable because RC_vol evidence is missing."
    if status == "partial":
        base = (
            "Risk budget view is partial: capital weights are available but RC_vol is "
            "incomplete for some holdings."
        )
        if not top1.get("ticker"):
            return base
    elif not top1.get("ticker"):
        return "Risk budget view has no asset rows to display."

    ticker = top1.get("ticker")
    rc_pct = top1.get("rc_pct")
    gap_pp = top1.get("weight_vs_risk_gap_pp")
    if not ticker or rc_pct is None:
        return "Risk budget view compares capital weights to RC_vol for all positive-weight holdings."

    parts: list[str] = []
    gap_text = f" (weight vs risk gap {gap_pp:+.3f} pp)" if gap_pp is not None else ""
    parts.append(
        f"Largest RC_vol contributor is {ticker} at {rc_pct:.3f}% of portfolio variance risk"
        f"{gap_text}."
    )
    if top3_share is not None:
        parts.append(f"Top three holdings account for {top3_share:.3f}% of variance risk.")
    if top_overweight:
        lead = top_overweight[0]
        parts.append(
            f"Largest risk-overweight vs capital is {lead['ticker']} "
            f"({lead['weight_vs_risk_gap_pp']:+.3f} pp)."
        )
    elif top_underweight:
        lead = top_underweight[0]
        parts.append(
            f"Largest risk-underweight vs capital is {lead['ticker']} "
            f"({lead['weight_vs_risk_gap_pp']:+.3f} pp)."
        )
    if status == "partial":
        parts.insert(0, "Risk budget view is partial: RC_vol is incomplete for some holdings.")
    return " ".join(parts)


def build_block_2_5_risk_budget_view(
    block_2_1: dict[str, Any] | None,
    *,
    rc_asset_rows: list[dict[str, Any]] | None,
    rc_sources: list[str] | None = None,
    taxonomy_rows: dict[str, Any] | list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build product-facing Risk Budget View from Block 2.1 weights and RC rows.

    ``taxonomy_rows`` supplies wire-time universe rows for bucket labels only.
    """
    weight_map = _weights_fraction_from_block_2_1(block_2_1)
    rc_map = _rc_map_from_rows(rc_asset_rows)
    sources = [str(s) for s in (rc_sources or []) if str(s).strip()]

    status, rc_warnings = _block_status(weight_map, rc_map)

    if status == "unavailable":
        assets: list[dict[str, Any]] = []
    else:
        tickers = sorted(set(weight_map) | set(rc_map))
        assets = _sort_assets(
            [
                _asset_row(
                    ticker,
                    weight_map.get(ticker),
                    rc_map.get(ticker),
                )
                for ticker in tickers
                if ticker in weight_map or ticker in rc_map
            ]
        )
    data_quality_warnings: list[str] = []
    if not isinstance(block_2_1, dict):
        data_quality_warnings.append("block_2_1_asset_allocation missing")
    data_quality_warnings.extend(rc_warnings)

    bucket_contribution, bucket_warnings = _risk_budget_bucket_contribution(
        weight_map,
        rc_map,
        taxonomy_rows,
    )
    data_quality_warnings.extend(bucket_warnings)

    aggregates = _portfolio_aggregates(assets)

    return {
        "block": BLOCK_2_5_ID,
        "block_id": BLOCK_2_5_ID,
        "block_name": BLOCK_2_5_NAME,
        "status": status,
        "summary": _summary_for_status(
            status,
            top1=aggregates["top1_rc_asset"],
            top3_share=aggregates["top3_rc_share"],
            top_overweight=aggregates["top_risk_overweight_assets"],
            top_underweight=aggregates["top_risk_underweight_assets"],
        ),
        "data_quality_warnings": list(dict.fromkeys(data_quality_warnings)),
        "metadata": {
            "rc_sources": sources,
            "rc_window": _rc_window_label_from_sources(sources),
            "rule_version": RULE_VERSION,
            "diagnostic_only": True,
        },
        "top1_rc_asset": aggregates["top1_rc_asset"],
        "top3_rc_assets": aggregates["top3_rc_assets"],
        "top3_rc_share": aggregates["top3_rc_share"],
        "top_risk_overweight_assets": aggregates["top_risk_overweight_assets"],
        "top_risk_underweight_assets": aggregates["top_risk_underweight_assets"],
        "risk_budget_bucket_contribution": bucket_contribution,
        "assets": assets,
    }


__all__ = [
    "BLOCK_2_5_ID",
    "BLOCK_2_5_NAME",
    "FORBIDDEN_STRESS_KEYS",
    "RULE_VERSION",
    "build_block_2_5_risk_budget_view",
]
