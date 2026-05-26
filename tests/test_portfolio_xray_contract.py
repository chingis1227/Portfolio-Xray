"""Golden JSON and schema contract tests for portfolio_xray.json (Session 09 / RM-949)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from src.portfolio_xray import PORTFOLIO_XRAY_VERSION, XRAY_SECTION_KEYS, XRAY_THRESHOLDS

import portfolio_xray_golden_inputs as golden_inputs

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
    assert set(doc["sections"]) == set(XRAY_SECTION_KEYS)


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


def test_live_build_matches_golden_document() -> None:
    live = build_golden_document()
    golden = _load_golden_fixture()
    assert contract_fingerprint(live) == contract_fingerprint(golden)
    assert _round_floats(live) == _round_floats(golden)


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
    assert list(live["sections"]) == list(XRAY_SECTION_KEYS)
