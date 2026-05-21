"""Golden JSON and schema contract tests for Block 5 optimizer disclosure (Session 11 / RM-1001)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from src.optimization_readiness import SCHEMA_VERSION as READINESS_SCHEMA_VERSION
from src.portfolio_variants import CANDIDATE_OPTIMIZER_RUN_METADATA_SCHEMA_VERSION

import optimization_engine_golden_inputs as golden_inputs

LEGACY_GOLDEN_PATH = golden_inputs.LEGACY_METADATA_GOLDEN_PATH
CANDIDATE_GOLDEN_PATH = golden_inputs.CANDIDATE_METADATA_GOLDEN_PATH
BLOCK5_GOLDEN_PATH = golden_inputs.COMPARISON_BLOCK5_GOLDEN_PATH

build_golden_legacy_policy_metadata = golden_inputs.build_golden_legacy_policy_metadata
build_golden_candidate_optimizer_metadata = golden_inputs.build_golden_candidate_optimizer_metadata
build_golden_comparison_block5 = golden_inputs.build_golden_comparison_block5

LEGACY_SCHEMA_VERSION = "legacy_policy_optimizer_run_metadata_v1"

LEGACY_TOP_LEVEL_REQUIRED = frozenset(
    {
        "schema_version",
        "optimizer_role",
        "entrypoint",
        "method_id",
        "objective",
        "input_window",
        "input_fingerprints",
        "expected_returns",
        "covariance",
        "young_etf_methodology",
        "universe",
        "constraints",
        "cash_policy",
        "solver",
        "release",
    }
)

CANDIDATE_TOP_LEVEL_REQUIRED = frozenset(
    {
        "schema_version",
        "optimizer_role",
        "candidate_only",
        "method_id",
        "entrypoint_family",
        "objective",
        "input_window",
        "input_fingerprints",
        "expected_return",
        "covariance",
        "young_etf_methodology",
        "universe",
        "constraints",
        "solver",
        "parameters",
        "outputs",
        "notes",
    }
)

BLOCK5_DISCLOSURE_KEYS = frozenset(
    {
        "optimizer_methodology",
        "optimizer_quality",
        "optimization_readiness",
    }
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_legacy_metadata_contract(meta: dict[str, Any]) -> None:
    assert LEGACY_TOP_LEVEL_REQUIRED <= set(meta)
    assert meta["schema_version"] == LEGACY_SCHEMA_VERSION
    assert meta["optimizer_role"] == "legacy_policy"
    assert meta["objective"]["objective_mode"] == "max_return"
    assert meta["covariance"]["methodology"]["schema_version"] == "optimizer_covariance_methodology_v1"
    assert meta["young_etf_methodology"]["schema_version"] == "optimizer_young_etf_methodology_v1"
    assert len(meta["input_fingerprints"]["returns_panel_fingerprint"]) == 64
    assert meta["solver"]["optimization_quality_status"] == "clean_solve"


def assert_candidate_metadata_contract(meta: dict[str, Any]) -> None:
    assert CANDIDATE_TOP_LEVEL_REQUIRED <= set(meta)
    assert meta["schema_version"] == CANDIDATE_OPTIMIZER_RUN_METADATA_SCHEMA_VERSION
    assert meta["optimizer_role"] == "candidate_only"
    assert meta["candidate_only"] is True
    assert meta["method_id"] == "minimum_variance_constrained"
    assert meta["expected_return"]["method"] == "not_used"
    assert meta["covariance"]["methodology"]["schema_version"] == "optimizer_covariance_methodology_v1"
    assert meta["solver"]["optimization_quality_status"] == "clean_solve"
    assert meta["notes"]["does_not_write_policy_weights"] is True


def legacy_metadata_fingerprint(meta: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": meta["schema_version"],
        "role": meta["optimizer_role"],
        "objective_mode": meta["objective"]["objective_mode"],
        "covariance_method": meta["covariance"]["method"],
        "young_etf_enabled": meta["young_etf_methodology"]["enabled"],
        "quality_status": meta["solver"]["optimization_quality_status"],
        "fallback_used": meta["solver"]["fallback_used"],
        "has_methodology_summary": bool(meta["covariance"].get("methodology_summary")),
        "panel_rows": meta["input_window"]["returns_panel_rows"],
    }


def candidate_metadata_fingerprint(meta: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": meta["schema_version"],
        "method_id": meta["method_id"],
        "expected_return_method": meta["expected_return"]["method"],
        "covariance_method": meta["covariance"]["method"],
        "young_etf_enabled": meta["young_etf_methodology"]["enabled"],
        "quality_status": meta["solver"]["optimization_quality_status"],
        "has_notes": bool(meta.get("notes")),
    }


def block5_disclosure_fingerprint(doc: dict[str, Any]) -> dict[str, Any]:
    disc = doc["construction_disclosure"]
    methodology = disc.get("optimizer_methodology") or {}
    quality = disc.get("optimizer_quality") or {}
    readiness = disc.get("optimization_readiness") or {}
    return {
        "candidate_id": doc["candidate_id"],
        "role": doc["role"],
        "status": doc["status"],
        "disclosure_status": disc.get("disclosure_status"),
        "has_block5_keys": BLOCK5_DISCLOSURE_KEYS <= set(disc),
        "methodology_schema": methodology.get("source_schema_version"),
        "method_id": methodology.get("method_id"),
        "quality_family": quality.get("optimization_quality_family"),
        "readiness_schema": readiness.get("schema_version"),
        "readiness_overall": readiness.get("overall_status"),
        "fair_comparison_ready": readiness.get("fair_comparison_ready"),
        "gaps_len": len(readiness.get("gaps") or []),
    }


@pytest.fixture(scope="module")
def legacy_golden() -> dict[str, Any]:
    assert LEGACY_GOLDEN_PATH.is_file(), f"Missing golden fixture: {LEGACY_GOLDEN_PATH}"
    return _load_json(LEGACY_GOLDEN_PATH)


@pytest.fixture(scope="module")
def candidate_golden() -> dict[str, Any]:
    assert CANDIDATE_GOLDEN_PATH.is_file(), f"Missing golden fixture: {CANDIDATE_GOLDEN_PATH}"
    return _load_json(CANDIDATE_GOLDEN_PATH)


@pytest.fixture(scope="module")
def block5_golden() -> dict[str, Any]:
    assert BLOCK5_GOLDEN_PATH.is_file(), f"Missing golden fixture: {BLOCK5_GOLDEN_PATH}"
    return _load_json(BLOCK5_GOLDEN_PATH)


def test_legacy_golden_fixture_valid_json(legacy_golden: dict[str, Any]) -> None:
    assert legacy_golden["schema_version"] == LEGACY_SCHEMA_VERSION


def test_legacy_golden_metadata_contract(legacy_golden: dict[str, Any]) -> None:
    assert_legacy_metadata_contract(legacy_golden)


def test_candidate_golden_fixture_valid_json(candidate_golden: dict[str, Any]) -> None:
    assert candidate_golden["schema_version"] == CANDIDATE_OPTIMIZER_RUN_METADATA_SCHEMA_VERSION


def test_candidate_golden_metadata_contract(candidate_golden: dict[str, Any]) -> None:
    assert_candidate_metadata_contract(candidate_golden)


def test_block5_golden_fixture_valid_json(block5_golden: dict[str, Any]) -> None:
    assert block5_golden["candidate_id"] == "minimum_variance"


def test_block5_golden_post_audit_surface(block5_golden: dict[str, Any]) -> None:
    fp = block5_disclosure_fingerprint(block5_golden)
    assert fp["has_block5_keys"] is True
    assert fp["methodology_schema"] == CANDIDATE_OPTIMIZER_RUN_METADATA_SCHEMA_VERSION
    assert fp["readiness_schema"] == READINESS_SCHEMA_VERSION
    assert fp["quality_family"] == "clean"
    assert fp["disclosure_status"] == "available"
    assert fp["status"] == "degraded"
    assert fp["readiness_overall"] == "partial"
    assert fp["fair_comparison_ready"] is False
    assert fp["gaps_len"] == 0


def test_live_legacy_metadata_matches_golden_document() -> None:
    live = build_golden_legacy_policy_metadata()
    golden = _load_json(LEGACY_GOLDEN_PATH)
    assert legacy_metadata_fingerprint(live) == legacy_metadata_fingerprint(golden)
    assert live == golden


def test_live_candidate_metadata_matches_golden_document() -> None:
    live = build_golden_candidate_optimizer_metadata()
    golden = _load_json(CANDIDATE_GOLDEN_PATH)
    assert candidate_metadata_fingerprint(live) == candidate_metadata_fingerprint(golden)
    assert live == golden


def test_live_comparison_block5_matches_golden_document() -> None:
    live = build_golden_comparison_block5()
    golden = _load_json(BLOCK5_GOLDEN_PATH)
    assert block5_disclosure_fingerprint(live) == block5_disclosure_fingerprint(golden)
    assert live == golden
