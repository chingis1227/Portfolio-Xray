from __future__ import annotations

import json
from typing import Any

import pytest

from src.block_2_5_risk_budget_view import (
    BLOCK_2_5_ID,
    BLOCK_2_5_NAME,
    FORBIDDEN_STRESS_KEYS,
    RULE_VERSION,
    build_block_2_5_risk_budget_view,
)
from src.portfolio_xray import build_portfolio_xray_v2

BLOCK_2_5_TOP_LEVEL_KEYS = frozenset(
    {
        "block",
        "block_id",
        "block_name",
        "status",
        "summary",
        "data_quality_warnings",
        "metadata",
        "top1_rc_asset",
        "top3_rc_assets",
        "top3_rc_share",
        "top_risk_overweight_assets",
        "top_risk_underweight_assets",
        "risk_budget_bucket_contribution",
        "assets",
    }
)

ASSET_ROW_KEYS = frozenset(
    {
        "ticker",
        "weight_pct",
        "rc_vol",
        "risk_contribution_pct",
        "weight_vs_risk_gap",
        "weight_vs_risk_gap_pp",
    }
)

SUMMARY_ASSET_KEYS = frozenset(
    {"ticker", "weight_pct", "rc_pct", "weight_vs_risk_gap_pp"}
)

BUCKET_CONTRIBUTION_KEYS = frozenset(
    {"bucket", "weight_pct", "rc_pct", "gap_pp"}
)

BLOCK_2_5_STATUS_VALUES = frozenset({"ok", "partial", "unavailable"})


def assert_block_2_5_product_contract(block: dict[str, Any]) -> None:
    """§2.5.1 product block shape for golden and live portfolio_xray.json."""
    assert isinstance(block, dict)
    assert set(block) == BLOCK_2_5_TOP_LEVEL_KEYS
    assert block["block"] == BLOCK_2_5_ID
    assert block["block_id"] == BLOCK_2_5_ID
    assert block["block_name"] == BLOCK_2_5_NAME
    assert block["status"] in BLOCK_2_5_STATUS_VALUES
    assert isinstance(block["summary"], str)
    assert isinstance(block["data_quality_warnings"], list)
    metadata = block["metadata"]
    assert isinstance(metadata, dict)
    assert metadata["rule_version"] == RULE_VERSION
    assert metadata["diagnostic_only"] is True
    assert isinstance(metadata.get("rc_sources"), list)
    assert isinstance(metadata.get("rc_window"), str)

    assert isinstance(block["top1_rc_asset"], dict)
    assert isinstance(block["top3_rc_assets"], list)
    assert isinstance(block["top_risk_overweight_assets"], list)
    assert isinstance(block["top_risk_underweight_assets"], list)
    assert isinstance(block["risk_budget_bucket_contribution"], list)
    assert isinstance(block["assets"], list)

    for row in block["assets"]:
        assert set(row) == ASSET_ROW_KEYS
    for row in block["top3_rc_assets"]:
        assert set(row) == SUMMARY_ASSET_KEYS
    for row in block["risk_budget_bucket_contribution"]:
        assert set(row) == BUCKET_CONTRIBUTION_KEYS

    found: set[str] = set()
    _collect_keys(block, keys=found)
    assert not found

    serialized = json.dumps(block)
    for forbidden in FORBIDDEN_STRESS_KEYS:
        assert forbidden not in serialized


def _block_2_1(weights: dict[str, float]) -> dict:
    by_asset = [
        {"name": ticker, "weight_pct": round(weight * 100.0, 3)}
        for ticker, weight in sorted(weights.items())
    ]
    return {
        "block": "2.1_asset_allocation",
        "capital_allocation_breakdown": {"by_asset": by_asset},
    }


def _rc_rows(rc_by_ticker: dict[str, float]) -> list[dict[str, float]]:
    return [{"ticker": ticker, "rc_pct": rc} for ticker, rc in sorted(rc_by_ticker.items())]


def _collect_keys(obj: Any, *, keys: set[str]) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in FORBIDDEN_STRESS_KEYS:
                keys.add(key)
            _collect_keys(value, keys=keys)
    elif isinstance(obj, list):
        for item in obj:
            _collect_keys(item, keys=keys)


def test_block_2_5_contract_envelope() -> None:
    block = build_block_2_5_risk_budget_view(
        _block_2_1({"VOO": 0.5, "BND": 0.5}),
        rc_asset_rows=_rc_rows({"VOO": 0.6, "BND": 0.4}),
        rc_sources=["rc_vol_map"],
    )

    assert_block_2_5_product_contract(block)
    assert block["status"] == "ok"
    assert block["metadata"]["rc_sources"] == ["rc_vol_map"]
    assert set(block["top1_rc_asset"]) == SUMMARY_ASSET_KEYS
    assert block["top1_rc_asset"]["ticker"] == "VOO"
    assert len(block["top3_rc_assets"]) == 2
    assert block["top3_rc_share"] == pytest.approx(100.0)
    assert block["risk_budget_bucket_contribution"] == []


def test_block_2_5_asset_rows_and_weight_vs_risk_gaps() -> None:
    block = build_block_2_5_risk_budget_view(
        _block_2_1({"VOO": 0.4, "BND": 0.6}),
        rc_asset_rows=_rc_rows({"VOO": 0.55, "BND": 0.45}),
        rc_sources=["results_csv/rc_vol_10y.csv"],
    )

    assert block["status"] == "ok"
    assert len(block["assets"]) == 2
    by_ticker = {row["ticker"]: row for row in block["assets"]}
    assert set(by_ticker) == {"BND", "VOO"}
    for row in by_ticker.values():
        assert set(row) == ASSET_ROW_KEYS

    voo = by_ticker["VOO"]
    assert voo["weight_pct"] == 40.0
    assert voo["rc_vol"] == 0.55
    assert voo["risk_contribution_pct"] == 55.0
    assert voo["weight_vs_risk_gap"] == pytest.approx(0.15)
    assert voo["weight_vs_risk_gap_pp"] == pytest.approx(15.0)

    bnd = by_ticker["BND"]
    assert bnd["weight_pct"] == 60.0
    assert bnd["rc_vol"] == 0.45
    assert bnd["weight_vs_risk_gap"] == pytest.approx(-0.15)
    assert bnd["weight_vs_risk_gap_pp"] == pytest.approx(-15.0)

    assert block["assets"][0]["ticker"] == "VOO"
    assert block["metadata"]["rc_window"] == "10Y (120M)"
    assert block["top1_rc_asset"]["ticker"] == "VOO"
    assert block["top1_rc_asset"]["rc_pct"] == 55.0
    assert block["top_risk_overweight_assets"][0]["ticker"] == "VOO"
    assert block["top_risk_underweight_assets"][0]["ticker"] == "BND"
    assert "Top three holdings account for" in block["summary"]
    assert "risk-overweight" in block["summary"]


def test_block_2_5_portfolio_aggregates_top3_and_gap_lists() -> None:
    block = build_block_2_5_risk_budget_view(
        _block_2_1(
            {
                "AAA": 0.10,
                "BBB": 0.20,
                "CCC": 0.15,
                "DDD": 0.25,
                "EEE": 0.30,
            }
        ),
        rc_asset_rows=_rc_rows(
            {
                "AAA": 0.05,
                "BBB": 0.10,
                "CCC": 0.15,
                "DDD": 0.30,
                "EEE": 0.40,
            }
        ),
        rc_sources=["rc_vol_map"],
    )

    assert block["status"] == "ok"
    assert [row["ticker"] for row in block["top3_rc_assets"]] == ["EEE", "DDD", "CCC"]
    assert block["top3_rc_share"] == pytest.approx(85.0)
    assert block["top1_rc_asset"]["ticker"] == "EEE"
    assert block["top1_rc_asset"]["rc_pct"] == 40.0

    overweight = block["top_risk_overweight_assets"]
    underweight = block["top_risk_underweight_assets"]
    assert [row["ticker"] for row in overweight] == ["EEE", "DDD"]
    assert overweight[0]["weight_vs_risk_gap_pp"] == pytest.approx(10.0)
    assert [row["ticker"] for row in underweight] == ["BBB", "AAA"]
    assert underweight[0]["weight_vs_risk_gap_pp"] == pytest.approx(-10.0)
    for row in overweight + underweight + block["top3_rc_assets"]:
        assert set(row) == SUMMARY_ASSET_KEYS


def test_block_2_5_partial_when_rc_missing_for_weighted_holding() -> None:
    block = build_block_2_5_risk_budget_view(
        _block_2_1({"VOO": 0.5, "BND": 0.5}),
        rc_asset_rows=_rc_rows({"VOO": 0.7}),
        rc_sources=["rc_vol_map"],
    )

    assert block["status"] == "partial"
    assert any("BND" in warning for warning in block["data_quality_warnings"])
    bnd = next(row for row in block["assets"] if row["ticker"] == "BND")
    assert bnd["rc_vol"] is None
    assert bnd["weight_vs_risk_gap"] is None
    assert block["top1_rc_asset"]["ticker"] == "VOO"
    assert block["top3_rc_assets"] == [block["top1_rc_asset"]]
    assert block["top3_rc_share"] == pytest.approx(70.0)
    assert "partial" in block["summary"].lower()


def test_block_2_5_unavailable_without_rc_evidence() -> None:
    block = build_block_2_5_risk_budget_view(
        _block_2_1({"VOO": 1.0}),
        rc_asset_rows=[],
        rc_sources=[],
    )

    assert block["status"] == "unavailable"
    assert block["assets"] == []
    assert block["top1_rc_asset"] == {}
    assert block["top3_rc_assets"] == []
    assert block["top3_rc_share"] is None
    assert any("RC_vol" in warning for warning in block["data_quality_warnings"])


def test_block_2_5_bucket_contribution_aggregates_by_taxonomy() -> None:
    taxonomy = {
        "VOO": {"asset_class": "equity", "subtype": "broad_market"},
        "BND": {"asset_class": "fixed_income", "subtype": "aggregate"},
        "TIP": {"asset_class": "fixed_income", "subtype": "tips"},
    }
    block = build_block_2_5_risk_budget_view(
        _block_2_1({"VOO": 0.4, "BND": 0.35, "TIP": 0.25}),
        rc_asset_rows=_rc_rows({"VOO": 0.5, "BND": 0.3, "TIP": 0.2}),
        rc_sources=["rc_vol_map"],
        taxonomy_rows=taxonomy,
    )

    buckets = {row["bucket"]: row for row in block["risk_budget_bucket_contribution"]}
    assert set(buckets) == {"equity", "fixed_income", "inflation_linked"}
    for row in buckets.values():
        assert set(row) == BUCKET_CONTRIBUTION_KEYS

    assert buckets["equity"]["weight_pct"] == 40.0
    assert buckets["equity"]["rc_pct"] == 50.0
    assert buckets["equity"]["gap_pp"] == pytest.approx(10.0)

    assert buckets["fixed_income"]["weight_pct"] == 35.0
    assert buckets["fixed_income"]["rc_pct"] == 30.0
    assert buckets["fixed_income"]["gap_pp"] == pytest.approx(-5.0)

    assert buckets["inflation_linked"]["weight_pct"] == 25.0
    assert buckets["inflation_linked"]["rc_pct"] == 20.0
    assert buckets["inflation_linked"]["gap_pp"] == pytest.approx(-5.0)

    ordered = block["risk_budget_bucket_contribution"]
    assert [row["bucket"] for row in ordered] == [
        "equity",
        "fixed_income",
        "inflation_linked",
    ]
    assert sum(row["weight_pct"] for row in ordered) == pytest.approx(100.0)
    assert sum(row["rc_pct"] for row in ordered) == pytest.approx(100.0)


def test_block_2_5_bucket_contribution_empty_without_taxonomy() -> None:
    block = build_block_2_5_risk_budget_view(
        _block_2_1({"VOO": 0.5, "BND": 0.5}),
        rc_asset_rows=_rc_rows({"VOO": 0.55, "BND": 0.45}),
        rc_sources=["rc_vol_map"],
    )

    assert block["risk_budget_bucket_contribution"] == []
    assert any(
        "taxonomy_rows missing" in warning
        for warning in block["data_quality_warnings"]
    )


def test_block_2_5_bucket_contribution_unknown_when_taxonomy_row_missing() -> None:
    block = build_block_2_5_risk_budget_view(
        _block_2_1({"VOO": 0.6, "ZZZ": 0.4}),
        rc_asset_rows=_rc_rows({"VOO": 0.55, "ZZZ": 0.45}),
        rc_sources=["rc_vol_map"],
        taxonomy_rows={"VOO": {"asset_class": "equity", "subtype": "broad_market"}},
    )

    buckets = {row["bucket"]: row for row in block["risk_budget_bucket_contribution"]}
    assert buckets["equity"]["weight_pct"] == 60.0
    assert buckets["unknown"]["weight_pct"] == 40.0
    assert buckets["unknown"]["rc_pct"] == 45.0
    assert any("ZZZ" in warning for warning in block["data_quality_warnings"])


def test_block_2_5_no_stress_keys_in_product_block() -> None:
    block = build_block_2_5_risk_budget_view(
        _block_2_1({"VOO": 0.5, "BND": 0.5}),
        rc_asset_rows=_rc_rows({"VOO": 0.55, "BND": 0.45}),
        rc_sources=["rc_vol_map"],
    )

    found: set[str] = set()
    _collect_keys(block, keys=found)
    assert not found

    serialized = json.dumps(block)
    for forbidden in FORBIDDEN_STRESS_KEYS:
        assert forbidden not in serialized


def test_portfolio_xray_v2_includes_block_2_5_without_removing_legacy_section() -> None:
    xray = build_portfolio_xray_v2(
        analysis_setup={"analysis_portfolio": {"portfolio_role": "test"}},
        weights={"SPY": 0.6, "BND": 0.4},
        rc_asset=[],
        rc_vol_map={"SPY": 0.7, "BND": 0.3},
        stress_report={"factor_betas_5y": {"beta_eq": 0.4}},
        portfolio_valid=True,
        portfolio_metrics={"beta_portfolio": 0.8},
        taxonomy_rows={
            "SPY": {"asset_class": "equity", "subtype": "broad_market"},
            "BND": {"asset_class": "fixed_income", "subtype": "core_bond"},
        },
    )

    block = xray["block_2_5_risk_budget_view"]
    assert_block_2_5_product_contract(block)
    assert block["status"] == "ok"
    assert {row["ticker"] for row in block["assets"]} == {"BND", "SPY"}
    assert "risk_budget_view" in xray["sections"]
    legacy = xray["sections"]["risk_budget_view"]
    assert legacy["status"] in {"available", "partial", "unavailable"}
    assert any(
        item.get("type") == "asset_risk_budget" for item in legacy.get("items") or []
    )
