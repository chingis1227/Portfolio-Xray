"""Golden JSON and schema contract tests for candidate_comparison.json (Session 08 / RM-978)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from src.candidate_comparison import (
    PRIMARY_WINDOW,
    SCHEMA_VERSION,
    WINDOWS,
    candidate_registry_ids,
)

import candidate_factory_golden_inputs as golden_inputs

GOLDEN_FIXTURE_PATH = golden_inputs.COMPARISON_GOLDEN_PATH
build_golden_comparison = golden_inputs.build_golden_comparison
normalize_comparison = golden_inputs.normalize_comparison

COMPARISON_TOP_LEVEL_REQUIRED = frozenset(
    {
        "schema_version",
        "diagnostic_only",
        "comparison_baseline_candidate_id",
        "generated_at",
        "analysis_end",
        "config_fingerprint",
        "investor_currency",
        "output_dir_final",
        "analysis_setup_summary",
        "windows",
        "primary_window",
        "candidates",
        "candidate_menu",
        "legacy_artifacts",
        "warnings",
    }
)

CANDIDATE_ROW_REQUIRED = frozenset(
    {
        "candidate_id",
        "display_name",
        "role",
        "construction_method",
        "weight_source",
        "artifact_root",
        "status",
        "construction_disclosure",
    }
)

CANDIDATE_STATUS_VALUES = frozenset({"available", "unavailable", "degraded"})

DISCLOSURE_REQUIRED = frozenset({"disclosure_status", "source_files"})

DISCLOSURE_STATUS_VALUES = frozenset({"available", "partial", "missing"})

MENU_REQUIRED = frozenset(
    {
        "is_partial_menu",
        "intended_menu_profile_id",
        "product_menu_profile_id",
        "intended_menu_status_counts",
        "product_menu_status_counts",
        "unavailable_reasons_summary",
        "refresh_command_core",
        "refresh_command_full",
    }
)


def _load_golden_fixture() -> dict[str, Any]:
    return json.loads(GOLDEN_FIXTURE_PATH.read_text(encoding="utf-8"))


def assert_comparison_top_level_contract(doc: dict[str, Any]) -> None:
    assert COMPARISON_TOP_LEVEL_REQUIRED <= set(doc)
    assert doc["schema_version"] == SCHEMA_VERSION
    assert doc["diagnostic_only"] is True
    assert doc["comparison_baseline_candidate_id"] == "analysis_subject"
    assert list(doc["windows"]) == list(WINDOWS)
    assert doc["primary_window"] == PRIMARY_WINDOW
    assert isinstance(doc["candidates"], list)
    assert isinstance(doc["candidate_menu"], dict)


def assert_comparison_candidates_contract(doc: dict[str, Any]) -> None:
    ids = candidate_registry_ids()
    assert [c["candidate_id"] for c in doc["candidates"]] == ids
    for row in doc["candidates"]:
        assert CANDIDATE_ROW_REQUIRED <= set(row)
        assert row["status"] in CANDIDATE_STATUS_VALUES
        disc = row["construction_disclosure"]
        assert DISCLOSURE_REQUIRED <= set(disc)
        assert disc["disclosure_status"] in DISCLOSURE_STATUS_VALUES


def assert_candidate_menu_contract(doc: dict[str, Any]) -> None:
    menu = doc["candidate_menu"]
    assert MENU_REQUIRED <= set(menu)


def comparison_contract_fingerprint(doc: dict[str, Any]) -> dict[str, Any]:
    candidates = doc["candidates"]
    return {
        "schema_version": doc["schema_version"],
        "baseline_id": doc["comparison_baseline_candidate_id"],
        "registry_len": len(candidates),
        "registry_ids": [c["candidate_id"] for c in candidates],
        "status_counts": {
            status: sum(1 for c in candidates if c["status"] == status)
            for status in sorted(CANDIDATE_STATUS_VALUES)
        },
        "disclosure_status_counts": {
            st: sum(
                1
                for c in candidates
                if c["construction_disclosure"]["disclosure_status"] == st
            )
            for st in sorted(DISCLOSURE_STATUS_VALUES)
        },
        "menu_partial": doc["candidate_menu"].get("is_partial_menu"),
        "menu_profile": doc["candidate_menu"].get("intended_menu_profile_id"),
        "menu_product_profile": doc["candidate_menu"].get("product_menu_profile_id"),
        "has_config_fingerprint": bool(doc.get("config_fingerprint")),
        "equal_weight_disclosure": next(
            c["construction_disclosure"]["disclosure_status"]
            for c in candidates
            if c["candidate_id"] == "equal_weight"
        ),
        "risk_parity_disclosure": next(
            c["construction_disclosure"]["disclosure_status"]
            for c in candidates
            if c["candidate_id"] == "risk_parity"
        ),
    }


@pytest.fixture(scope="module")
def golden_fixture() -> dict[str, Any]:
    assert GOLDEN_FIXTURE_PATH.is_file(), f"Missing golden fixture: {GOLDEN_FIXTURE_PATH}"
    return _load_golden_fixture()


def test_golden_fixture_file_valid_json(golden_fixture: dict[str, Any]) -> None:
    assert golden_fixture["schema_version"] == SCHEMA_VERSION


def test_golden_comparison_top_level_contract(golden_fixture: dict[str, Any]) -> None:
    assert_comparison_top_level_contract(golden_fixture)


def test_golden_comparison_candidates_contract(golden_fixture: dict[str, Any]) -> None:
    assert_comparison_candidates_contract(golden_fixture)


def test_golden_comparison_menu_contract(golden_fixture: dict[str, Any]) -> None:
    assert_candidate_menu_contract(golden_fixture)


def test_golden_comparison_post_audit_surface(golden_fixture: dict[str, Any]) -> None:
    fp = comparison_contract_fingerprint(golden_fixture)
    assert fp["registry_len"] == len(candidate_registry_ids())
    assert fp["has_config_fingerprint"] is True
    assert fp["equal_weight_disclosure"] == "available"
    assert fp["risk_parity_disclosure"] == "partial"
    assert fp["menu_profile"] == "default_v1"
    assert fp["menu_product_profile"] == "default_v1"


def test_live_comparison_build_matches_golden_document() -> None:
    live = normalize_comparison(build_golden_comparison())
    golden = _load_golden_fixture()
    assert comparison_contract_fingerprint(live) == comparison_contract_fingerprint(golden)


def test_registry_order_matches_spec(golden_fixture: dict[str, Any]) -> None:
    assert golden_fixture["candidates"][0]["candidate_id"] == "analysis_subject"
    assert golden_fixture["candidates"][1]["candidate_id"] == "policy"
    assert golden_fixture["candidates"][2]["candidate_id"] == "current"
