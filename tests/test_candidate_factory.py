from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.candidate_factory import (
    SCHEMA_VERSION,
    FactoryValidationError,
    build_factory_run_txt,
    factory_exit_code,
    resolve_profile_candidate_ids,
    run_candidate_factory,
    validate_candidate_ids,
    write_candidate_factory_outputs,
)
from src.config_schema import validate_config


def test_default_v1_profile_has_sixteen_candidates() -> None:
    ids = resolve_profile_candidate_ids(profile_id="default_v1", explicit_candidates=None)
    assert len(ids) == 16
    assert ids[0] == "equal_weight"
    assert ids[-1] == "robust_scenario"


def test_core_v1_profile_has_six_lightweight_candidates() -> None:
    ids = resolve_profile_candidate_ids(profile_id="core_v1", explicit_candidates=None)
    assert len(ids) == 6
    assert "equal_weight" in ids
    assert "hierarchical_risk_parity" in ids
    assert "minimum_variance" not in ids
    assert "robust_scenario" not in ids


def test_validate_unknown_candidate() -> None:
    assert validate_candidate_ids(["not_a_real_id"]) == ["not_a_real_id"]


def test_skip_existing_when_snapshot_present(tmp_path: Path) -> None:
    ew_dir = tmp_path / "equal-weight portfolio"
    ew_dir.mkdir(parents=True)
    (ew_dir / "snapshot_10y.json").write_text("{}", encoding="utf-8")

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO"],
        }
    )

    doc = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        explicit_candidates=["equal_weight"],
        skip_existing=True,
        force=False,
        runner=lambda cmd, cwd: 0,
    )
    ew_step = doc["steps"][0]
    assert ew_step["status"] == "skipped_existing"
    assert ew_step["reason_code"] == "skipped_existing"


def test_skip_existing_requires_matching_analysis_end(tmp_path: Path) -> None:
    subject_dir = tmp_path / "Main portfolio" / "analysis_subject"
    subject_dir.mkdir(parents=True)
    (subject_dir / "run_metadata.json").write_text(
        json.dumps({"run_info": {"analysis_end_date": "2026-05-15"}}),
        encoding="utf-8",
    )
    ew_dir = tmp_path / "equal-weight portfolio"
    ew_dir.mkdir(parents=True)
    (ew_dir / "snapshot_10y.json").write_text(
        json.dumps({"analysis_end": "2026-05-15"}),
        encoding="utf-8",
    )

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO"],
        }
    )

    doc = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        explicit_candidates=["equal_weight"],
        skip_existing=True,
        force=False,
        runner=lambda cmd, cwd: 0,
    )
    ew_step = doc["steps"][0]
    assert ew_step["status"] == "skipped_existing"
    assert ew_step["freshness_status"] == "fresh"
    assert ew_step["expected_analysis_end"] == "2026-05-15"
    assert ew_step["snapshot_analysis_end"] == "2026-05-15"


def test_stale_existing_snapshot_is_rebuilt_not_skipped(tmp_path: Path) -> None:
    subject_dir = tmp_path / "Main portfolio" / "analysis_subject"
    subject_dir.mkdir(parents=True)
    (subject_dir / "run_metadata.json").write_text(
        json.dumps({"run_info": {"analysis_end_date": "2026-05-15"}}),
        encoding="utf-8",
    )
    ew_dir = tmp_path / "equal-weight portfolio"
    ew_dir.mkdir(parents=True)
    snapshot = ew_dir / "snapshot_10y.json"
    snapshot.write_text(json.dumps({"analysis_end": "2026-04-30"}), encoding="utf-8")

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO"],
        }
    )

    calls = []

    def runner(cmd, cwd):  # noqa: ANN001
        calls.append(cmd)
        snapshot.write_text(json.dumps({"analysis_end": "2026-05-15"}), encoding="utf-8")
        return 0

    doc = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        explicit_candidates=["equal_weight"],
        skip_existing=True,
        force=False,
        runner=runner,
    )
    ew_step = doc["steps"][0]
    assert calls
    assert ew_step["status"] == "succeeded"
    assert ew_step["freshness_status"] == "fresh"
    assert doc["summary"]["rebuilt_stale"] == 1
    assert any(w.startswith("stale_candidate_snapshot_rebuild_attempted:equal_weight") for w in doc["warnings"])


def test_stale_snapshot_after_build_fails_explicitly(tmp_path: Path) -> None:
    subject_dir = tmp_path / "Main portfolio" / "analysis_subject"
    subject_dir.mkdir(parents=True)
    (subject_dir / "run_metadata.json").write_text(
        json.dumps({"run_info": {"analysis_end_date": "2026-05-15"}}),
        encoding="utf-8",
    )
    ew_dir = tmp_path / "equal-weight portfolio"
    ew_dir.mkdir(parents=True)
    (ew_dir / "snapshot_10y.json").write_text(
        json.dumps({"analysis_end": "2026-04-30"}),
        encoding="utf-8",
    )

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO"],
        }
    )

    doc = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        explicit_candidates=["equal_weight"],
        skip_existing=True,
        force=False,
        runner=lambda cmd, cwd: 0,
    )
    ew_step = doc["steps"][0]
    assert ew_step["status"] == "failed"
    assert ew_step["reason_code"] == "stale_snapshot_after_build"
    assert ew_step["freshness_status"] == "stale"


def test_robust_scenario_skipped_dependency(tmp_path: Path) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO"],
        }
    )
    doc = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        explicit_candidates=["robust_scenario"],
        skip_existing=False,
        runner=lambda cmd, cwd: 0,
    )
    step = doc["steps"][0]
    assert step["status"] == "skipped_dependency"
    assert step["reason_code"] == "skipped_dependency"
    assert len(step["entry_commands"]) == 2


def test_subprocess_failure_and_fail_fast(tmp_path: Path) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO"],
        }
    )

    def runner(cmd, cwd):  # noqa: ANN001
        script = Path(cmd[1]).name
        if script == "run_equal_weight.py":
            return 1
        return 0

    doc = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        profile_id="core_benchmarks",
        skip_existing=False,
        fail_fast=True,
        runner=runner,
    )
    assert len(doc["steps"]) == 1
    assert doc["steps"][0]["status"] == "failed"
    assert doc["steps"][0]["reason_code"] == "subprocess_failed"
    assert factory_exit_code(doc) == 1


def test_missing_snapshot_after_zero_exit(tmp_path: Path) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO"],
        }
    )
    doc = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        explicit_candidates=["equal_weight"],
        skip_existing=False,
        runner=lambda cmd, cwd: 0,
    )
    step = doc["steps"][0]
    assert step["status"] == "failed"
    assert step["reason_code"] == "missing_snapshot_after_build"


def test_write_outputs_contract(tmp_path: Path) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO"],
        }
    )
    doc = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        explicit_candidates=["equal_weight"],
        skip_existing=False,
        runner=lambda cmd, cwd: 0,
    )
    doc["schema_version"] = SCHEMA_VERSION
    out = tmp_path / "Main portfolio"
    paths = write_candidate_factory_outputs(doc, output_dir=out)
    assert paths["candidate_factory_run_json"].is_file()
    loaded = json.loads(paths["candidate_factory_run_json"].read_text(encoding="utf-8"))
    assert loaded["schema_version"] == SCHEMA_VERSION
    assert "Next:" in paths["candidate_factory_run_txt"].read_text(encoding="utf-8")
    assert "buy" not in build_factory_run_txt(doc).lower()


def test_factory_validation_error_on_unknown_profile() -> None:
    with pytest.raises(FactoryValidationError):
        resolve_profile_candidate_ids(profile_id="no_such_profile", explicit_candidates=None)


def test_factory_validation_unknown_candidates() -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO"],
        }
    )
    with pytest.raises(FactoryValidationError):
        run_candidate_factory(
            cfg,
            project_root=Path("/tmp/unused"),
            explicit_candidates=["bogus_id"],
        )
