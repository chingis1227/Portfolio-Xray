"""Golden JSON and schema contract tests for candidate_factory_run.json (Session 08 / RM-978)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from src.candidate_factory import (
    SCHEMA_VERSION,
    _BUILDER_STATUS_TO_REASON,
    factory_reason_from_builder_summary,
)

import candidate_factory_golden_inputs as golden_inputs

GOLDEN_FIXTURE_PATH = golden_inputs.FACTORY_GOLDEN_PATH
build_golden_factory_run = golden_inputs.build_golden_factory_run
normalize_factory_run = golden_inputs.normalize_factory_run
golden_factory_build_kwargs = golden_inputs.golden_factory_build_kwargs

FACTORY_TOP_LEVEL_REQUIRED = frozenset(
    {
        "schema_version",
        "diagnostic_only",
        "run_status",
        "generated_at",
        "factory_profile_id",
        "project_root",
        "output_dir_final",
        "config_path",
        "analysis_end",
        "config_fingerprint",
        "options",
        "steps",
        "summary",
        "warnings",
        "next_recommended_command",
    }
)

STEP_REQUIRED = frozenset(
    {
        "candidate_id",
        "display_name",
        "role",
        "artifact_root",
        "status",
        "entry_commands",
        "exit_code",
        "duration_seconds",
        "reason_code",
        "message",
    }
)

STEP_STATUS_VALUES = frozenset(
    {"succeeded", "failed", "skipped_existing", "skipped_dependency"}
)

SUMMARY_REQUIRED = frozenset(
    {
        "total",
        "succeeded",
        "failed",
        "skipped_existing",
        "skipped_dependency",
        "rebuilt_stale",
        "resumed_from_manifest",
    }
)

OPTIONS_REQUIRED = frozenset(
    {
        "skip_existing",
        "force",
        "fail_fast",
        "resume",
        "then_compare",
        "pdf_mode",
        "execution_mode",
        "full_candidate_reports",
        "selected_candidates_for_full_report",
    }
)

BUILDER_REASON_CODES = frozenset(_BUILDER_STATUS_TO_REASON.values()) | {"builder_failed"}


def _load_golden_fixture() -> dict[str, Any]:
    return json.loads(GOLDEN_FIXTURE_PATH.read_text(encoding="utf-8"))


def assert_factory_top_level_contract(doc: dict[str, Any]) -> None:
    assert FACTORY_TOP_LEVEL_REQUIRED <= set(doc)
    assert doc["schema_version"] == SCHEMA_VERSION
    assert doc["diagnostic_only"] is True
    assert isinstance(doc["steps"], list)
    assert isinstance(doc["warnings"], list)
    assert OPTIONS_REQUIRED <= set(doc["options"])
    assert SUMMARY_REQUIRED <= set(doc["summary"])


def assert_factory_steps_contract(doc: dict[str, Any]) -> None:
    for step in doc["steps"]:
        assert STEP_REQUIRED <= set(step)
        assert step["status"] in STEP_STATUS_VALUES
        if step["status"] == "succeeded":
            assert step["reason_code"] is None
        else:
            assert isinstance(step["reason_code"], str)
        if step.get("builder_status"):
            assert step["reason_code"] in BUILDER_REASON_CODES or step[
                "reason_code"
            ] in {
                "missing_snapshot_after_build",
                "stale_snapshot_after_build",
                "stale_config_fingerprint_after_build",
                "subprocess_failed",
                "skipped_dependency",
                "skipped_existing",
                "unknown_candidate_id",
            }


def factory_contract_fingerprint(doc: dict[str, Any]) -> dict[str, Any]:
    steps = doc["steps"]
    return {
        "schema_version": doc["schema_version"],
        "factory_profile_id": doc["factory_profile_id"],
        "run_status": doc.get("run_status"),
        "options_keys": sorted(doc["options"]),
        "summary_keys": sorted(doc["summary"]),
        "step_signatures": [
            {
                "candidate_id": s["candidate_id"],
                "status": s["status"],
                "reason_code": s["reason_code"],
                "freshness_status": s.get("freshness_status"),
                "has_robust_disclosure": "robust_paths_disclosure" in s,
            }
            for s in steps
        ],
        "has_config_fingerprint": bool(doc.get("config_fingerprint")),
    }


@pytest.fixture(scope="module")
def golden_fixture() -> dict[str, Any]:
    assert GOLDEN_FIXTURE_PATH.is_file(), f"Missing golden fixture: {GOLDEN_FIXTURE_PATH}"
    return _load_golden_fixture()


def test_golden_fixture_file_valid_json(golden_fixture: dict[str, Any]) -> None:
    assert golden_fixture["schema_version"] == SCHEMA_VERSION


def test_golden_factory_top_level_contract(golden_fixture: dict[str, Any]) -> None:
    assert_factory_top_level_contract(golden_fixture)


def test_golden_factory_steps_contract(golden_fixture: dict[str, Any]) -> None:
    assert_factory_steps_contract(golden_fixture)


def test_golden_factory_post_audit_surface(golden_fixture: dict[str, Any]) -> None:
    fp = factory_contract_fingerprint(golden_fixture)
    assert fp["has_config_fingerprint"] is True
    assert fp["factory_profile_id"] == "explicit_list"
    assert len(fp["step_signatures"]) == 2
    assert all(s["status"] == "succeeded" for s in fp["step_signatures"])


def test_live_factory_build_matches_golden_document() -> None:
    live = normalize_factory_run(build_golden_factory_run())
    golden = _load_golden_fixture()
    assert factory_contract_fingerprint(live) == factory_contract_fingerprint(golden)


def test_builder_reason_mapping_contract() -> None:
    for fail_status, reason in _BUILDER_STATUS_TO_REASON.items():
        mapped = factory_reason_from_builder_summary(
            {"status": fail_status, "reason": "fixture"}
        )
        assert mapped is not None
        assert mapped[0] == reason
    unknown = factory_reason_from_builder_summary(
        {"status": "FAIL_CUSTOM", "reason": "x"}
    )
    assert unknown is not None
    assert unknown[0] == "builder_failed"


def test_golden_factory_build_kwargs_stable_entrypoint() -> None:
    kwargs = golden_factory_build_kwargs()
    assert kwargs["explicit_candidates"] == ["equal_weight", "risk_parity"]
    live = normalize_factory_run(build_golden_factory_run())
    assert_factory_top_level_contract(live)
    assert_factory_steps_contract(live)
