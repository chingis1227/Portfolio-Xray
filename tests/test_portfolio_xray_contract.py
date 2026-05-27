"""Golden JSON and schema contract tests for portfolio_xray.json (Session 09 / RM-949)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from src.portfolio_xray import PORTFOLIO_XRAY_VERSION, XRAY_SECTION_KEYS, XRAY_THRESHOLDS

import portfolio_xray_golden_inputs as golden_inputs
from test_block_2_5_risk_budget import assert_block_2_5_product_contract

GOLDEN_FIXTURE_PATH = golden_inputs.GOLDEN_FIXTURE_PATH
build_golden_document = golden_inputs.build_golden_document
golden_build_kwargs = golden_inputs.golden_build_kwargs

TOP_LEVEL_REQUIRED = (
    "version",
    "diagnostic_only",
    "diagnostic_only_disclaimer",
    "analysis_setup_summary",
    "thresholds",
    "block_2_1_asset_allocation",
    "block_2_2_portfolio_metrics",
    "block_2_3_factor_exposure",
    "block_2_4_hidden_exposure",
    "block_2_5_risk_budget_view",
    "block_2_6_portfolio_weakness_map",
    "sections",
    "legacy_summary",
)

SECTION_REQUIRED = frozenset(
    {"status", "data_sources_used", "warnings", "items", "limitations"},
)

SECTION_STATUS_VALUES = frozenset({"available", "partial", "unavailable"})

PROVENANCE_SECTIONS = frozenset(
    {"risk_diagnostics", "factor_exposure", "risk_budget_view", "weakness_map"},
)

PROVENANCE_FULL = frozenset({"method", "frequency", "window", "n_obs", "benchmark"})
PROVENANCE_RISK_BUDGET = frozenset({"method", "frequency", "window", "benchmark"})


def _load_golden_fixture() -> dict[str, Any]:
    return json.loads(GOLDEN_FIXTURE_PATH.read_text(encoding="utf-8"))


def _round_floats(obj: Any, places: int = 6) -> Any:
    if isinstance(obj, float):
        return round(obj, places)
    if isinstance(obj, dict):
        return {k: _round_floats(v, places) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round_floats(v, places) for v in obj]
    return obj


def assert_top_level_contract(doc: dict[str, Any]) -> None:
    assert set(TOP_LEVEL_REQUIRED) <= set(doc)
    assert doc["version"] == PORTFOLIO_XRAY_VERSION
    assert doc["diagnostic_only"] is True
    assert "does not optimize" in doc["diagnostic_only_disclaimer"]
    assert isinstance(doc["analysis_setup_summary"], dict)
    assert isinstance(doc["legacy_summary"], dict)
    assert set(doc["thresholds"]) == set(XRAY_THRESHOLDS)
    assert doc["thresholds"] == XRAY_THRESHOLDS
    block = doc.get("block_2_1_asset_allocation")
    assert isinstance(block, dict)
    assert block.get("block") == "2.1_asset_allocation"
    block_22 = doc.get("block_2_2_portfolio_metrics")
    assert isinstance(block_22, dict)
    assert block_22.get("block") == "2.2_portfolio_metrics"
    block_23 = doc.get("block_2_3_factor_exposure")
    assert isinstance(block_23, dict)
    assert block_23.get("block") == "2.3_factor_exposure"
    block_24 = doc.get("block_2_4_hidden_exposure")
    assert isinstance(block_24, dict)
    assert block_24.get("block") == "2.4_hidden_exposure"
    block_25 = doc.get("block_2_5_risk_budget_view")
    assert isinstance(block_25, dict)
    assert_block_2_5_product_contract(block_25)
    block_26 = doc.get("block_2_6_portfolio_weakness_map")
    assert isinstance(block_26, dict)
    assert block_26.get("block") == "2.6_portfolio_weakness_map"
    assert set(doc["sections"]) == set(XRAY_SECTION_KEYS)


def assert_core_mvp_block_2_consumer_surface(doc: dict[str, Any]) -> None:
    """Core MVP consumers should read Block 2 product keys, not legacy mandate summary fields."""
    expected_keys = {
        "block_2_1_asset_allocation",
        "block_2_2_portfolio_metrics",
        "block_2_3_factor_exposure",
        "block_2_4_hidden_exposure",
        "block_2_5_risk_budget_view",
        "block_2_6_portfolio_weakness_map",
    }
    assert expected_keys <= set(doc)
    legacy = doc.get("legacy_summary") or {}
    assert legacy.get("_scope", {}).get("product_surface") is False
    verdict = legacy.get("portfolio_diagnostic_verdict") or {}
    assert "mandate_gate" not in verdict
    assert (verdict.get("legacy_policy_compatibility") or {}).get("core_mvp_product_surface") is False


def assert_sections_contract(doc: dict[str, Any]) -> None:
    sections = doc["sections"]
    assert set(sections) == set(XRAY_SECTION_KEYS)
    for key in XRAY_SECTION_KEYS:
        section = sections[key]
        assert SECTION_REQUIRED <= set(section)
        assert section["status"] in SECTION_STATUS_VALUES
        assert isinstance(section["data_sources_used"], list)
        assert isinstance(section["warnings"], list)
        assert isinstance(section["items"], list)
        assert isinstance(section["limitations"], list)
        if key in PROVENANCE_SECTIONS:
            required = PROVENANCE_RISK_BUDGET if key == "risk_budget_view" else PROVENANCE_FULL
            assert required <= set(section)


def contract_fingerprint(doc: dict[str, Any]) -> dict[str, Any]:
    """Stable structural fingerprint for golden vs live drift detection."""
    sections = doc["sections"]
    fp: dict[str, Any] = {
        "version": doc["version"],
        "threshold_keys": sorted(doc["thresholds"]),
        "section_status": {k: sections[k]["status"] for k in XRAY_SECTION_KEYS},
        "item_types": {
            k: sorted({item.get("type") for item in sections[k]["items"] if item.get("type")})
            for k in XRAY_SECTION_KEYS
        },
    }
    factor_items = sections["factor_exposure"]["items"]
    fp["factor_inference_horizons"] = sorted(
        item["horizon"]
        for item in factor_items
        if item.get("type") == "factor_regression_inference"
    )
    alloc_items = sections["asset_allocation"]["items"]
    fp["has_weight_concentration"] = any(
        item.get("type") == "weight_concentration" for item in alloc_items
    )
    risk_items = sections["risk_diagnostics"]["items"]
    fp["has_multi_window_metrics"] = any(
        item.get("type") == "multi_window_metrics" for item in risk_items
    )
    vol = next(
        (item for item in sections["weakness_map"]["items"] if item.get("risk") == "volatility_spike"),
        None,
    )
    if vol:
        fp["volatility_spike_evidence_mode"] = (vol.get("scenario_coverage") or {}).get("evidence_mode")
    archetype_items = sections["portfolio_archetype"]["items"]
    if archetype_items:
        fp["primary_archetype"] = archetype_items[0].get("primary_archetype")
    block = doc.get("block_2_1_asset_allocation")
    if isinstance(block, dict):
        fp["block_2_1_present"] = True
        fp["block_2_1_total_holdings"] = (block.get("portfolio_composition_snapshot") or {}).get(
            "total_holdings"
        )
    block_22 = doc.get("block_2_2_portfolio_metrics")
    if isinstance(block_22, dict):
        fp["block_2_2_present"] = True
        fp["block_2_2_primary_window_months"] = (block_22.get("metadata") or {}).get(
            "primary_window_months"
        )
    block_23 = doc.get("block_2_3_factor_exposure")
    if isinstance(block_23, dict):
        fp["block_2_3_present"] = True
        fp["block_2_3_status"] = block_23.get("status")
        fp["block_2_3_beta_keys"] = sorted((block_23.get("factor_beta_snapshot") or {}).keys())
    block_24 = doc.get("block_2_4_hidden_exposure")
    if isinstance(block_24, dict):
        fp["block_2_4_present"] = True
        fp["block_2_4_status"] = block_24.get("status")
    block_25 = doc.get("block_2_5_risk_budget_view")
    if isinstance(block_25, dict):
        fp["block_2_5_present"] = True
        fp["block_2_5_status"] = block_25.get("status")
        top1 = block_25.get("top1_rc_asset") or {}
        fp["block_2_5_top1_ticker"] = top1.get("ticker")
        fp["block_2_5_asset_tickers"] = sorted(
            row.get("ticker") for row in block_25.get("assets") or [] if row.get("ticker")
        )
        fp["block_2_5_buckets"] = sorted(
            row.get("bucket")
            for row in block_25.get("risk_budget_bucket_contribution") or []
            if row.get("bucket")
        )
    return fp


@pytest.fixture(scope="module")
def golden_fixture() -> dict[str, Any]:
    assert GOLDEN_FIXTURE_PATH.is_file(), f"Missing golden fixture: {GOLDEN_FIXTURE_PATH}"
    return _load_golden_fixture()


def test_golden_fixture_file_valid_json(golden_fixture: dict[str, Any]) -> None:
    assert golden_fixture["version"] == PORTFOLIO_XRAY_VERSION


def test_golden_top_level_contract(golden_fixture: dict[str, Any]) -> None:
    assert_top_level_contract(golden_fixture)


def test_golden_sections_contract(golden_fixture: dict[str, Any]) -> None:
    assert_sections_contract(golden_fixture)


def test_golden_post_audit_surface_items(golden_fixture: dict[str, Any]) -> None:
    fp = contract_fingerprint(golden_fixture)
    assert fp["factor_inference_horizons"] == ["10Y", "5Y"]
    assert fp["has_weight_concentration"] is True
    assert fp["has_multi_window_metrics"] is True
    assert fp["volatility_spike_evidence_mode"] == "factor_only"
    assert fp["primary_archetype"]


def test_golden_block_2_5_risk_budget_surface(golden_fixture: dict[str, Any]) -> None:
    block = golden_fixture["block_2_5_risk_budget_view"]
    assert_block_2_5_product_contract(block)
    assert block["status"] == "ok"
    assert block["top1_rc_asset"]["ticker"] == "SPY"
    assert block["top3_rc_share"] == 90.0
    assert block["top_risk_overweight_assets"][0]["ticker"] == "HYG"
    assert {row["ticker"] for row in block["assets"]} == {"GLD", "HYG", "SPY", "TLT"}
    assert block["metadata"]["rc_sources"] == ["snapshot.RC_asset"]


def test_live_build_matches_golden_document() -> None:
    live = build_golden_document()
    golden = _load_golden_fixture()
    assert contract_fingerprint(live) == contract_fingerprint(golden)
    live_r = _round_floats(live)
    golden_r = _round_floats(golden)
    assert set(golden_r) <= set(live_r)
    # Allow additive surface growth (new blocks) without immediately rewriting the golden fixture.
    # Sessions that intentionally update the golden fixture should keep this strict on shared keys.
    comparable_keys = set(golden_r) - {"legacy_summary"}
    assert {k: live_r[k] for k in comparable_keys} == {k: golden_r[k] for k in comparable_keys}


def test_live_build_kwargs_stable_entrypoint() -> None:
    kwargs = golden_build_kwargs()
    assert set(kwargs) >= {
        "analysis_setup",
        "weights",
        "rc_asset",
        "stress_report",
        "portfolio_metrics",
        "portfolio_windows",
    }
    live = build_golden_document()
    assert_top_level_contract(live)
    assert_sections_contract(live)
    assert_core_mvp_block_2_consumer_surface(live)
    assert list(live["sections"]) == list(XRAY_SECTION_KEYS)
