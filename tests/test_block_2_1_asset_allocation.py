from __future__ import annotations

from typing import Any

import pytest

from mvp_offline_fixtures import validate_mvp_fixture
from src.analysis_setup import build_analysis_setup, resolved_analysis_weights
from src.block_2_1_asset_allocation import (
    ALLOCATION_CONCENTRATION_THRESHOLDS,
    BLOCK_2_1_ID,
    REAL_CASH_TAXONOMY_SOURCE,
    build_block_2_1_asset_allocation,
    enrich_taxonomy_with_real_cash,
)
from src.block_2_2_portfolio_metrics import BLOCK_2_2_ID
from src.config import resolve_cash_and_rf
from src.portfolio_xray import build_portfolio_xray_v2


def _taxonomy_rows() -> dict[str, dict]:
    return {
        "VOO": {
            "asset_class": "equity",
            "region": "US",
            "currency_exposure": "USD",
            "risk_role": ["risk_on"],
            "main_risk_factor": "equity",
            "duplicate_group_id": "",
            "canonical_ticker": "",
        },
        "BND": {
            "asset_class": "fixed_income",
            "region": "US",
            "currency_exposure": "USD",
            "risk_role": ["defensive"],
            "main_risk_factor": "credit",
            "duplicate_group_id": "",
            "canonical_ticker": "",
        },
    }


def _mvp_analysis_setup() -> dict:
    return {
        "version": "analysis_setup_v1",
        "portfolio_input": {
            "source_analysis_mode": "analyze_current_weights",
            "investor_currency": "USD",
            "analysis_subject_type": "current_portfolio",
        },
        "analysis_subject": {"type": "current_portfolio"},
        "analysis_portfolio": {"weights": {"VOO": 0.5, "BND": 0.5}},
    }


BLOCK_2_1_TOP_LEVEL_KEYS = frozenset(
    {
        "block",
        "analysis_subject",
        "analysis_mode",
        "investor_currency",
        "portfolio_composition_snapshot",
        "capital_allocation_breakdown",
        "concentration_flags",
        "duplicate_exposure_flags",
        "actual_economic_exposure_summary",
        "data_quality_warnings",
        "metadata",
    }
)

BREAKDOWN_KEYS = frozenset(
    {
        "by_asset",
        "by_asset_class",
        "by_main_risk_factor",
        "by_risk_role",
        "by_region",
        "by_currency",
    }
)

CONCENTRATION_FLAG_KEYS = frozenset(
    {
        "flag_id",
        "severity",
        "metric",
        "dimension",
        "label",
        "threshold",
        "observed",
        "message",
    }
)

DUPLICATE_FLAG_KEYS = frozenset(
    {
        "duplicate_group_id",
        "tickers",
        "combined_weight",
        "combined_weight_pct",
        "canonical_ticker",
        "severity",
        "message",
    }
)


def assert_block_2_1_product_contract(block: dict[str, Any]) -> None:
    """Normative shape guard (portfolio_xray_diagnostics_spec.md §2.1.1)."""
    assert set(block) >= BLOCK_2_1_TOP_LEVEL_KEYS
    assert block["block"] == BLOCK_2_1_ID
    assert isinstance(block["concentration_flags"], list)
    assert isinstance(block["duplicate_exposure_flags"], list)
    assert isinstance(block["data_quality_warnings"], list)

    snap = block["portfolio_composition_snapshot"]
    for key in (
        "total_holdings",
        "top1_holding",
        "top3_holdings",
        "top3_weight_pct",
        "dominant_asset_class",
        "dominant_risk_role",
        "dominant_main_risk_factor",
        "dominant_region",
        "dominant_currency",
    ):
        assert key in snap

    breakdown = block["capital_allocation_breakdown"]
    assert set(breakdown) == BREAKDOWN_KEYS
    for rows in breakdown.values():
        assert isinstance(rows, list)
        for row in rows:
            assert "name" in row and "weight_pct" in row

    economic = block["actual_economic_exposure_summary"]
    assert isinstance(economic.get("headline"), str)
    assert isinstance(economic.get("key_points"), list)

    metadata = block["metadata"]
    assert metadata.get("source") == "core_mvp_input"
    assert metadata.get("cash_proxy_used_for_real_cash") is False
    assert metadata.get("allocation_concentration_thresholds") == ALLOCATION_CONCENTRATION_THRESHOLDS

    for flag in block["concentration_flags"]:
        assert CONCENTRATION_FLAG_KEYS <= set(flag)
        assert flag["severity"] in {"medium", "high"}
        assert 0 <= float(flag["threshold"]) <= 1
        assert 0 <= float(flag["observed"]) <= 1

    for dup in block["duplicate_exposure_flags"]:
        assert DUPLICATE_FLAG_KEYS <= set(dup)
        assert len(dup["tickers"]) >= 2
        assert dup["severity"] in {"medium", "high"}


def _breakdown_sorted_descending(rows: list[dict[str, Any]]) -> None:
    pairs = [(r["name"], float(r["weight_pct"])) for r in rows]
    for i in range(len(pairs) - 1):
        left_w, right_w = pairs[i][1], pairs[i + 1][1]
        if left_w < right_w - 1e-9:
            pytest.fail(f"breakdown not sorted by weight: {pairs}")
        if abs(left_w - right_w) < 1e-9 and pairs[i][0] > pairs[i + 1][0]:
            pytest.fail(f"breakdown tie-break not lexicographic: {pairs}")


def test_build_block_2_1_basic_snapshot_and_breakdowns() -> None:
    doc = build_block_2_1_asset_allocation(
        analysis_setup=_mvp_analysis_setup(),
        weights={"VOO": 0.6, "BND": 0.4},
        taxonomy_rows=_taxonomy_rows(),
        taxonomy_sources={"VOO": "test", "BND": "test"},
    )
    assert doc["block"] == BLOCK_2_1_ID
    assert doc["analysis_subject"] == "current_portfolio"
    assert doc["analysis_mode"] == "analyze_current_weights"
    snap = doc["portfolio_composition_snapshot"]
    assert snap["total_holdings"] == 2
    assert snap["top1_holding"]["ticker"] == "VOO"
    assert snap["top1_holding"]["weight_pct"] == pytest.approx(60.0)
    assert snap["top3_weight_pct"] == pytest.approx(100.0)
    assert snap["dominant_asset_class"]["name"] == "equity"
    assert snap["dominant_asset_class"]["weight_pct"] == pytest.approx(60.0)


def test_real_cash_in_allocation_without_cash_proxy() -> None:
    weights = {"VOO": 0.9, "Cash USD": 0.1}
    rows, sources = enrich_taxonomy_with_real_cash(
        weights,
        {k.upper(): v for k, v in _taxonomy_rows().items()},
        {"VOO": "test"},
        investor_currency="USD",
    )
    assert sources["CASH USD"] == REAL_CASH_TAXONOMY_SOURCE
    doc = build_block_2_1_asset_allocation(
        analysis_setup=_mvp_analysis_setup(),
        weights=weights,
        taxonomy_rows=rows,
        taxonomy_sources=sources,
    )
    by_asset = {r["name"]: r["weight_pct"] for r in doc["capital_allocation_breakdown"]["by_asset"]}
    assert by_asset["Cash USD"] == pytest.approx(10.0)
    by_currency = {
        r["name"]: r["weight_pct"] for r in doc["capital_allocation_breakdown"]["by_currency"]
    }
    assert by_currency["USD"] == pytest.approx(100.0)
    cash_rows = [r for r in doc["capital_allocation_breakdown"]["by_asset_class"] if r["name"] == "cash"]
    assert cash_rows and cash_rows[0]["weight_pct"] == pytest.approx(10.0)
    assert doc["metadata"]["cash_proxy_used_for_real_cash"] is False
    assert doc["metadata"]["cash_treatment"] == "real_cash_position_if_present"


def test_top1_concentration_flags_medium_and_high() -> None:
    doc = build_block_2_1_asset_allocation(
        analysis_setup=_mvp_analysis_setup(),
        weights={"VOO": 0.35, "BND": 0.65},
        taxonomy_rows=_taxonomy_rows(),
        taxonomy_sources={"VOO": "test", "BND": "test"},
    )
    flags = doc["concentration_flags"]
    top_flags = [f for f in flags if f["flag_id"] == "top_holding_concentration"]
    severities = {f["severity"] for f in top_flags}
    assert "medium" in severities
    assert "high" in severities
    assert doc["portfolio_composition_snapshot"]["top1_holding"]["weight_pct"] == pytest.approx(65.0)


def test_duplicate_exposure_flags_medium_only_below_high_band() -> None:
    rows = {
        "SMH": {
            "asset_class": "equity",
            "region": "US",
            "currency_exposure": "USD",
            "risk_role": ["risk_on"],
            "main_risk_factor": "equity",
            "duplicate_group_id": "semiconductors",
            "canonical_ticker": "SMH",
        },
        "SOXX": {
            "asset_class": "equity",
            "region": "US",
            "currency_exposure": "USD",
            "risk_role": ["risk_on"],
            "main_risk_factor": "equity",
            "duplicate_group_id": "semiconductors",
            "canonical_ticker": "SMH",
        },
    }
    doc = build_block_2_1_asset_allocation(
        analysis_setup=_mvp_analysis_setup(),
        weights={"SMH": 0.09, "SOXX": 0.09},
        taxonomy_rows=rows,
        taxonomy_sources={"SMH": "test", "SOXX": "test"},
    )
    assert len(doc["duplicate_exposure_flags"]) == 1
    assert doc["duplicate_exposure_flags"][0]["severity"] == "medium"
    assert doc["duplicate_exposure_flags"][0]["combined_weight_pct"] == pytest.approx(18.0)


def test_duplicate_exposure_flags_two_tickers_same_group() -> None:
    rows = {
        "SMH": {
            "asset_class": "equity",
            "region": "US",
            "currency_exposure": "USD",
            "risk_role": ["risk_on"],
            "main_risk_factor": "equity",
            "duplicate_group_id": "semiconductors",
            "canonical_ticker": "SMH",
        },
        "SOXX": {
            "asset_class": "equity",
            "region": "US",
            "currency_exposure": "USD",
            "risk_role": ["risk_on"],
            "main_risk_factor": "equity",
            "duplicate_group_id": "semiconductors",
            "canonical_ticker": "SMH",
        },
    }
    doc = build_block_2_1_asset_allocation(
        analysis_setup=_mvp_analysis_setup(),
        weights={"SMH": 0.12, "SOXX": 0.08},
        taxonomy_rows=rows,
        taxonomy_sources={"SMH": "test", "SOXX": "test"},
    )
    assert len(doc["duplicate_exposure_flags"]) == 1
    dup = doc["duplicate_exposure_flags"][0]
    assert dup["duplicate_group_id"] == "semiconductors"
    assert set(dup["tickers"]) == {"SMH", "SOXX"}
    assert dup["combined_weight_pct"] == pytest.approx(20.0)
    assert dup["severity"] == "high"


def test_unknown_taxonomy_warns_not_crash() -> None:
    doc = build_block_2_1_asset_allocation(
        analysis_setup=_mvp_analysis_setup(),
        weights={"VOO": 0.6, "UNKNOWN": 0.4},
        taxonomy_rows=_taxonomy_rows(),
        taxonomy_sources={"VOO": "test"},
    )
    assert any("taxonomy" in w.lower() for w in doc["data_quality_warnings"])
    unknown_rows = [
        r for r in doc["capital_allocation_breakdown"]["by_asset_class"] if r["name"] == "unknown"
    ]
    assert unknown_rows and unknown_rows[0]["weight_pct"] == pytest.approx(40.0)


def test_build_portfolio_xray_v2_includes_block_2_1() -> None:
    xray = build_portfolio_xray_v2(
        analysis_setup=_mvp_analysis_setup(),
        weights={"VOO": 0.6, "BND": 0.4},
        rc_asset=[],
        stress_report={},
        portfolio_valid=True,
        taxonomy_rows=_taxonomy_rows(),
        taxonomy_sources={"VOO": "test", "BND": "test"},
    )
    block = xray.get("block_2_1_asset_allocation")
    assert isinstance(block, dict)
    assert block.get("block") == BLOCK_2_1_ID
    assert block.get("portfolio_composition_snapshot", {}).get("total_holdings") == 2
    assert block.get("portfolio_composition_snapshot", {}).get("top1_holding", {}).get("ticker") == "VOO"


def test_build_portfolio_xray_v2_includes_block_2_2() -> None:
    xray = build_portfolio_xray_v2(
        analysis_setup=_mvp_analysis_setup(),
        weights={"VOO": 0.6, "BND": 0.4},
        rc_asset=[],
        stress_report={},
        portfolio_valid=True,
        portfolio_metrics={
            "window_months": 120,
            "cagr": 0.07,
            "vol_annual": 0.11,
            "sharpe": 0.5,
            "max_drawdown": -0.18,
            "downside_deviation": 0.06,
            "metric_quality": {"n_obs": 118, "window_months": 120, "benchmark_ticker": "VOO"},
        },
        taxonomy_rows=_taxonomy_rows(),
        taxonomy_sources={"VOO": "test", "BND": "test"},
    )
    block = xray.get("block_2_2_portfolio_metrics")
    assert isinstance(block, dict)
    assert block.get("block") == BLOCK_2_2_ID
    assert block.get("return_risk_metrics", {}).get("portfolio_cagr") == 0.07
    assert block.get("tail_risk_diagnostics", {}).get("downside_deviation") == 0.06
    assert block.get("metadata", {}).get("primary_window_months") == 120


def test_allocation_threshold_registry_matches_spec() -> None:
    assert ALLOCATION_CONCENTRATION_THRESHOLDS["top_holding_concentration_high"] == 0.30
    assert ALLOCATION_CONCENTRATION_THRESHOLDS["top3_concentration_medium"] == 0.50


def _mvp_analysis_setup_from_fixture(fixture_name: str) -> dict:
    cfg = validate_mvp_fixture(fixture_name)
    cash_proxy, rf_source = resolve_cash_and_rf(cfg)
    return build_analysis_setup(
        cfg,
        portfolio_weights=dict(cfg.weights or {}),
        weights_source=cfg.weights_source,
        cash_proxy_ticker=cash_proxy,
        rf_source=rf_source,
        analysis_end="2026-04-30",
        windows_months=[36, 60, 120],
        returns_frequency="monthly",
        periods_per_year=12,
        run_context="report",
    )


def _xray_from_fixture(fixture_name: str) -> dict:
    setup = _mvp_analysis_setup_from_fixture(fixture_name)
    return build_portfolio_xray_v2(
        analysis_setup=setup,
        weights=None,
        rc_asset=[],
        stress_report={},
        portfolio_valid=True,
    )


def test_resolved_analysis_weights_prefers_explicit_then_setup() -> None:
    setup = _mvp_analysis_setup()
    from_setup = resolved_analysis_weights(setup, weights=None)
    assert from_setup["VOO"] == pytest.approx(0.5)
    explicit = resolved_analysis_weights(setup, weights={"VOO": 0.7, "BND": 0.3})
    assert explicit == {"VOO": 0.7, "BND": 0.3}
    assert resolved_analysis_weights(setup, weights={}) == from_setup


def test_mvp_cash_fixture_block_2_1_from_analysis_setup_weights() -> None:
    setup = _mvp_analysis_setup_from_fixture("minimal_usd_with_cash.yml")
    assert resolved_analysis_weights(setup)["Cash USD"] == pytest.approx(0.10)

    xray = build_portfolio_xray_v2(
        analysis_setup=setup,
        weights=None,
        rc_asset=[],
        stress_report={},
        portfolio_valid=True,
    )
    block = xray["block_2_1_asset_allocation"]
    by_asset = {r["name"]: r["weight_pct"] for r in block["capital_allocation_breakdown"]["by_asset"]}
    assert by_asset["Cash USD"] == pytest.approx(10.0)
    assert block["metadata"]["cash_treatment"] == "real_cash_position_if_present"
    assert block["metadata"]["cash_proxy_used_for_real_cash"] is False

    cash_holdings = [
        item
        for item in xray["sections"]["asset_allocation"]["items"]
        if item.get("type") == "holding" and item.get("ticker") == "Cash USD"
    ]
    assert len(cash_holdings) == 1
    assert cash_holdings[0].get("asset_class") == "cash"
    assert cash_holdings[0].get("taxonomy_source") == REAL_CASH_TAXONOMY_SOURCE


def test_legacy_summary_cash_weight_uses_real_cash_not_proxy() -> None:
    setup = _mvp_analysis_setup_from_fixture("minimal_usd_with_cash.yml")
    xray = build_portfolio_xray_v2(
        analysis_setup=setup,
        weights=None,
        rc_asset=[],
        stress_report={},
        portfolio_valid=True,
    )
    alloc = xray["legacy_summary"]["asset_allocation_summary"]
    assert alloc["cash_proxy_ticker"] == "BIL"
    assert alloc["cash_weight"] == pytest.approx(0.10)
    assert "BIL" not in resolved_analysis_weights(setup)


def test_block_2_1_product_contract_shape_on_builder_output() -> None:
    doc = build_block_2_1_asset_allocation(
        analysis_setup=_mvp_analysis_setup(),
        weights={"VOO": 0.6, "BND": 0.4},
        taxonomy_rows=_taxonomy_rows(),
        taxonomy_sources={"VOO": "test", "BND": "test"},
    )
    assert_block_2_1_product_contract(doc)
    for key in BREAKDOWN_KEYS:
        _breakdown_sorted_descending(doc["capital_allocation_breakdown"][key])


def test_demo_fixture_block_2_1_snapshot_and_real_cash() -> None:
    """Session 05/06: config.yml ×0.95 + 5% Cash USD against merged universe taxonomy."""
    setup = _mvp_analysis_setup_from_fixture("demo_usd_asset_allocation_with_cash_5pct.yml")
    weights = resolved_analysis_weights(setup)
    assert weights["Cash USD"] == pytest.approx(0.05)
    assert sum(weights.values()) == pytest.approx(1.0)

    xray = _xray_from_fixture("demo_usd_asset_allocation_with_cash_5pct.yml")
    block = xray["block_2_1_asset_allocation"]
    assert_block_2_1_product_contract(block)

    snap = block["portfolio_composition_snapshot"]
    assert snap["total_holdings"] == 9
    assert snap["top1_holding"] == {"ticker": "SCHD", "weight_pct": 16.15}
    assert [h["ticker"] for h in snap["top3_holdings"]] == ["SCHD", "BND", "QQQ"]
    assert snap["top3_weight_pct"] == pytest.approx(43.7)
    assert snap["dominant_asset_class"] == {"name": "fixed_income", "weight_pct": 39.9}

    by_asset = {r["name"]: r["weight_pct"] for r in block["capital_allocation_breakdown"]["by_asset"]}
    assert by_asset["Cash USD"] == pytest.approx(5.0)
    assert by_asset["SCHD"] == pytest.approx(16.15)

    cash_class = [
        r
        for r in block["capital_allocation_breakdown"]["by_asset_class"]
        if r["name"] == "cash"
    ]
    assert cash_class and cash_class[0]["weight_pct"] == pytest.approx(5.0)

    assert block["metadata"]["cash_treatment"] == "real_cash_position_if_present"
    assert REAL_CASH_TAXONOMY_SOURCE in block["metadata"]["taxonomy_sources"]
    assert xray["legacy_summary"]["asset_allocation_summary"]["cash_weight"] == pytest.approx(0.05)

    cash_holdings = [
        item
        for item in xray["sections"]["asset_allocation"]["items"]
        if item.get("type") == "holding" and item.get("ticker") == "Cash USD"
    ]
    assert len(cash_holdings) == 1
    assert cash_holdings[0].get("asset_class") == "cash"
    assert cash_holdings[0].get("taxonomy_source") == REAL_CASH_TAXONOMY_SOURCE


def test_demo_fixture_block_2_1_concentration_and_economic_summary() -> None:
    block = _xray_from_fixture("demo_usd_asset_allocation_with_cash_5pct.yml")[
        "block_2_1_asset_allocation"
    ]
    flag_pairs = {(f["flag_id"], f["severity"]) for f in block["concentration_flags"]}
    assert ("single_region_dominance", "medium") in flag_pairs
    assert ("single_currency_dominance", "medium") in flag_pairs
    assert ("single_currency_dominance", "high") in flag_pairs
    assert block["duplicate_exposure_flags"] == []

    economic = block["actual_economic_exposure_summary"]
    assert "fixed_income" in economic["headline"]
    assert len(economic["key_points"]) >= 2
    assert any("SCHD" in point for point in economic["key_points"])
    assert any("bank cash" in point.lower() for point in economic["key_points"])
