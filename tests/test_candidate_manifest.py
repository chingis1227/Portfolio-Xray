from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.candidate_manifest import (
    CANDIDATE_MANIFEST_FILENAME,
    CANDIDATE_MANIFEST_SCHEMA,
    RUN_STATUS_ABORTED_FAIL_FAST,
    RUN_STATUS_ALL_FAILED,
    RUN_STATUS_FULL_SUCCESS,
    RUN_STATUS_PARTIAL_SUCCESS,
    build_candidate_manifest,
    compute_factory_run_status,
    load_candidate_manifest,
    write_candidate_manifest,
)
from src.candidate_factory import factory_exit_code, run_candidate_factory
from src.config_schema import validate_config
from src.snapshot import (
    CANDIDATE_CONFIG_FINGERPRINT_KEY,
    compute_candidate_config_fingerprint,
)


def _write_fresh_snapshot(path: Path, cfg: object, *, analysis_end: str = "2026-04-30") -> None:
    path.write_text(
        json.dumps(
            {
                "analysis_end": analysis_end,
                CANDIDATE_CONFIG_FINGERPRINT_KEY: compute_candidate_config_fingerprint(cfg),
                "metrics": {},
            }
        ),
        encoding="utf-8",
    )


def test_compute_factory_run_status_matrix() -> None:
    assert (
        compute_factory_run_status(
            {"failed": 0, "succeeded": 3},
            fail_fast=False,
            fail_fast_aborted=False,
        )
        == RUN_STATUS_FULL_SUCCESS
    )
    assert (
        compute_factory_run_status(
            {"failed": 1, "succeeded": 2, "skipped_existing": 0},
            fail_fast=False,
            fail_fast_aborted=False,
        )
        == RUN_STATUS_PARTIAL_SUCCESS
    )
    assert (
        compute_factory_run_status(
            {"failed": 2, "succeeded": 0, "skipped_existing": 0},
            fail_fast=False,
            fail_fast_aborted=False,
        )
        == RUN_STATUS_ALL_FAILED
    )
    assert (
        compute_factory_run_status(
            {"failed": 1, "succeeded": 0, "skipped_existing": 0},
            fail_fast=True,
            fail_fast_aborted=True,
        )
        == RUN_STATUS_ABORTED_FAIL_FAST
    )


def test_build_candidate_manifest_ready(tmp_path: Path) -> None:
    art = tmp_path / "equal-weight portfolio"
    art.mkdir()
    (art / "weights.json").write_text("{}", encoding="utf-8")
    (art / "snapshot_10y.json").write_text("{}", encoding="utf-8")
    (art / "stress_report.json").write_text("{}", encoding="utf-8")

    step = {
        "candidate_id": "equal_weight",
        "display_name": "Equal-Weight",
        "role": "benchmark",
        "artifact_root": "equal-weight portfolio",
        "status": "succeeded",
        "execution_action": "lightweight_report_built",
        "phases_completed": ["weights", "report"],
        "report_profile": "lightweight_comparison",
        "freshness_status": "fresh",
    }
    manifest = build_candidate_manifest(step, artifact_dir=art)
    assert manifest["schema_version"] == CANDIDATE_MANIFEST_SCHEMA
    assert manifest["comparison_readiness"]["ready_for_comparison"] is True
    assert manifest["comparison_readiness"]["status"] == "ready"
    assert manifest.get("partial_failure") is None


def test_build_candidate_manifest_partial_weights_only(tmp_path: Path) -> None:
    art = tmp_path / "equal-weight portfolio"
    art.mkdir()
    (art / "weights.json").write_text("{}", encoding="utf-8")

    step = {
        "candidate_id": "equal_weight",
        "display_name": "Equal-Weight",
        "role": "benchmark",
        "artifact_root": "equal-weight portfolio",
        "status": "failed",
        "execution_action": "lightweight_report_failed",
        "reason_code": "builder_failed",
        "message": "report phase error",
        "phases_completed": ["weights", "report"],
    }
    manifest = build_candidate_manifest(step, artifact_dir=art)
    assert manifest["comparison_readiness"]["ready_for_comparison"] is False
    assert manifest["comparison_readiness"]["status"] == "weights_only"
    partial = manifest.get("partial_failure") or {}
    assert partial.get("report_phase") == "failed"
    assert partial.get("weights_phase") == "succeeded"


def test_factory_writes_candidate_manifest_and_run_status(tmp_path: Path) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    main = tmp_path / "Main portfolio"
    main.mkdir(parents=True)
    _write_fresh_snapshot(main / "snapshot_10y.json", cfg)
    ew_dir = tmp_path / "equal-weight portfolio"
    ew_dir.mkdir(parents=True)
    _write_fresh_snapshot(ew_dir / "snapshot_10y.json", cfg)

    doc = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        explicit_candidates=["equal_weight"],
        skip_existing=True,
        force=False,
        runner=lambda cmd, cwd: 0,
    )
    assert doc["run_status"] == RUN_STATUS_FULL_SUCCESS
    manifest_path = ew_dir / CANDIDATE_MANIFEST_FILENAME
    assert manifest_path.is_file()
    loaded = load_candidate_manifest(ew_dir)
    assert loaded is not None
    assert loaded["comparison_readiness"]["ready_for_comparison"] is True
    ew_step = next(s for s in doc["steps"] if s["candidate_id"] == "equal_weight")
    assert ew_step.get("candidate_manifest_path") == "equal-weight portfolio/candidate_manifest.json"


def test_partial_failure_continues_without_fail_fast(tmp_path: Path) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO"],
        }
    )
    main = tmp_path / "Main portfolio"
    main.mkdir(parents=True)
    _write_fresh_snapshot(main / "snapshot_10y.json", cfg)
    rp_dir = tmp_path / "risk parity portfolio"
    rp_dir.mkdir(parents=True)
    _write_fresh_snapshot(rp_dir / "snapshot_10y.json", cfg)

    def runner(cmd, cwd):  # noqa: ANN001
        script = Path(cmd[1]).name
        if script == "run_equal_weight.py":
            return 1
        return 0

    doc = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        explicit_candidates=["equal_weight", "risk_parity"],
        skip_existing=True,
        fail_fast=False,
        runner=runner,
    )
    assert doc["run_status"] == RUN_STATUS_PARTIAL_SUCCESS
    assert len(doc["steps"]) == 2
    assert factory_exit_code(doc) == 1
    failed = [s for s in doc["steps"] if s["status"] == "failed"]
    assert len(failed) == 1
    ew_dir = tmp_path / "equal-weight portfolio"
    if ew_dir.is_dir():
        cm = load_candidate_manifest(ew_dir)
        if cm is not None:
            assert cm["comparison_readiness"]["ready_for_comparison"] is False
