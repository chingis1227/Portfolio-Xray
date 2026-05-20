from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.candidate_factory import (
    MANIFEST_FILENAME,
    SCHEMA_VERSION,
    FactoryValidationError,
    build_factory_run_txt,
    compute_factory_run_checksum,
    compute_next_recommended_command,
    factory_exit_code,
    factory_reason_from_builder_summary,
    resolve_profile_candidate_ids,
    run_candidate_factory,
    validate_candidate_ids,
    write_candidate_factory_outputs,
)
from src.config_schema import validate_config
from src.snapshot import compute_candidate_config_fingerprint


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

    calls: list[list[str]] = []

    def runner(cmd, cwd):  # noqa: ANN001
        calls.append(cmd)
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
    assert ew_step["freshness_status"] == "unchecked"
    assert any(
        w.startswith("unchecked_candidate_snapshot_rebuild_attempted:equal_weight:")
        for w in doc["warnings"]
    )


def test_unchecked_snapshot_rebuild_increments_rebuilt_stale(tmp_path: Path) -> None:
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

    doc = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        explicit_candidates=["equal_weight"],
        skip_existing=True,
        force=False,
        runner=lambda cmd, cwd: 0,
    )
    ew_step = doc["steps"][0]
    assert ew_step["status"] == "succeeded"
    assert doc["summary"]["rebuilt_stale"] == 1


def test_skip_existing_requires_matching_analysis_end(tmp_path: Path) -> None:
    subject_dir = tmp_path / "Main portfolio" / "analysis_subject"
    subject_dir.mkdir(parents=True)
    (subject_dir / "run_metadata.json").write_text(
        json.dumps({"run_info": {"analysis_end_date": "2026-05-15"}}),
        encoding="utf-8",
    )
    ew_dir = tmp_path / "equal-weight portfolio"
    ew_dir.mkdir(parents=True)
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO"],
        }
    )
    fp = compute_candidate_config_fingerprint(cfg)
    (ew_dir / "snapshot_10y.json").write_text(
        json.dumps({"analysis_end": "2026-05-15", "candidate_config_fingerprint": fp}),
        encoding="utf-8",
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

    fp = compute_candidate_config_fingerprint(cfg)

    def runner(cmd, cwd):  # noqa: ANN001
        calls.append(cmd)
        snapshot.write_text(
            json.dumps(
                {"analysis_end": "2026-05-15", "candidate_config_fingerprint": fp}
            ),
            encoding="utf-8",
        )
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


def test_stale_config_fingerprint_rebuilds_same_analysis_end(tmp_path: Path) -> None:
    subject_dir = tmp_path / "Main portfolio" / "analysis_subject"
    subject_dir.mkdir(parents=True)
    (subject_dir / "run_metadata.json").write_text(
        json.dumps({"run_info": {"analysis_end_date": "2026-05-15"}}),
        encoding="utf-8",
    )
    ew_dir = tmp_path / "equal-weight portfolio"
    ew_dir.mkdir(parents=True)
    snapshot = ew_dir / "snapshot_10y.json"
    snapshot.write_text(
        json.dumps(
            {
                "analysis_end": "2026-05-15",
                "candidate_config_fingerprint": "deadbeef" * 8,
            }
        ),
        encoding="utf-8",
    )

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    fp = compute_candidate_config_fingerprint(cfg)
    calls = []

    def runner(cmd, cwd):  # noqa: ANN001
        calls.append(cmd)
        snapshot.write_text(
            json.dumps(
                {"analysis_end": "2026-05-15", "candidate_config_fingerprint": fp}
            ),
            encoding="utf-8",
        )
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
    assert doc["config_fingerprint"] == fp
    assert any(
        w.startswith("stale_candidate_config_fingerprint_rebuild_attempted:equal_weight:")
        for w in doc["warnings"]
    )


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
    disc = step.get("robust_paths_disclosure") or {}
    assert disc.get("kind") == "robust_scenario_main_prerequisites"
    assert disc.get("prerequisites_met") is False
    assert "scenario_library_normalized.json" in (disc.get("missing_artifacts") or [])
    assert "stress_report.json" in (disc.get("missing_artifacts") or [])
    assert "scenario_library_normalized.json" in step["message"]


def test_robust_mv_lambda_disclosure_missing_calibration(tmp_path: Path) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )

    def runner(cmd, cwd):  # noqa: ANN001
        script = Path(cmd[1]).name
        if script.startswith("run_robust_mean_variance"):
            return 2
        return 0

    doc = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        explicit_candidates=["robust_mv_constrained"],
        skip_existing=False,
        runner=runner,
    )
    step = doc["steps"][0]
    disc = step.get("robust_paths_disclosure") or {}
    assert disc.get("kind") == "robust_mv_lambda"
    assert disc.get("lambda_resolution_key") == "none"
    assert disc.get("lambda_ready_for_build") is False
    assert disc.get("factory_runs_lambda_calibration") is False


def test_robust_mv_lambda_disclosure_from_calibration_file(tmp_path: Path) -> None:
    cal = tmp_path / "analysis_robust_mv_lambda_calibration"
    cal.mkdir(parents=True)
    (cal / "selected_lambda.txt").write_text("0.5\n", encoding="utf-8")
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
        explicit_candidates=["robust_mv_uncapped"],
        skip_existing=False,
        runner=lambda cmd, cwd: 1,
    )
    step = doc["steps"][0]
    disc = step.get("robust_paths_disclosure") or {}
    assert disc.get("robust_mv_lambda") == 0.5
    assert disc.get("lambda_resolution_key") == "calibration_file"
    assert disc.get("lambda_ready_for_build") is True


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


def test_factory_reason_from_builder_summary_mapping() -> None:
    mapped = factory_reason_from_builder_summary(
        {"status": "FAIL_CONFIG", "reason": "missing risk_budgeting.targets"}
    )
    assert mapped is not None
    assert mapped[0] == "builder_fail_config"
    assert "FAIL_CONFIG" in mapped[1]
    assert "missing risk_budgeting.targets" in mapped[1]
    assert mapped[2] == "FAIL_CONFIG"
    assert mapped[3] == "missing risk_budgeting.targets"

    unknown = factory_reason_from_builder_summary(
        {"status": "FAIL_CUSTOM_DIAGNOSTIC", "reason": "solver blew up"}
    )
    assert unknown is not None
    assert unknown[0] == "builder_failed"

    assert factory_reason_from_builder_summary({"status": "OK"}) is None


def test_builder_fail_config_when_snapshot_missing_exit_zero(tmp_path: Path) -> None:
    ew_dir = tmp_path / "equal-weight portfolio"
    ew_dir.mkdir(parents=True)
    (ew_dir / "summary.json").write_text(
        json.dumps(
            {
                "portfolio_type": "Equal-Weight",
                "status": "FAIL_INFEASIBLE_UNIVERSE",
                "reason": "Fewer than two eligible tickers after filters.",
            }
        ),
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
        skip_existing=False,
        runner=lambda cmd, cwd: 0,
    )
    step = doc["steps"][0]
    assert step["status"] == "failed"
    assert step["reason_code"] == "builder_infeasible_universe"
    assert step["builder_status"] == "FAIL_INFEASIBLE_UNIVERSE"
    assert "Fewer than two eligible" in step["message"]
    assert step["exit_code"] == 0
    assert step["freshness_status"] == "missing"


def test_builder_fail_config_on_nonzero_exit_with_summary(tmp_path: Path) -> None:
    rb_dir = tmp_path / "risk budget by asset portfolio"
    rb_dir.mkdir(parents=True)
    (rb_dir / "summary.json").write_text(
        json.dumps(
            {
                "portfolio_type": "Risk budget (asset)",
                "status": "FAIL_CONFIG",
                "reason": "risk_budgeting.targets missing key: Commodities",
            }
        ),
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
        explicit_candidates=["risk_budget_by_asset"],
        skip_existing=False,
        runner=lambda cmd, cwd: 1,
    )
    step = doc["steps"][0]
    assert step["reason_code"] == "builder_fail_config"
    assert step["builder_status"] == "FAIL_CONFIG"
    assert "Commodities" in step["message"]
    assert step["exit_code"] == 1


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


def test_compute_next_recommended_command_suggests_resume_on_failure() -> None:
    doc = {
        "factory_profile_id": "default_v1",
        "steps": [{"candidate_id": "equal_weight", "status": "failed"}],
        "summary": {"failed": 1},
        "warnings": [],
        "options": {},
    }
    assert compute_next_recommended_command(doc) == (
        "python run_candidate_factory.py --profile default_v1 --resume"
    )


def test_compute_next_recommended_command_explicit_list_resume() -> None:
    doc = {
        "factory_profile_id": "explicit_list",
        "steps": [
            {"candidate_id": "equal_weight", "status": "failed"},
            {"candidate_id": "risk_parity", "status": "succeeded"},
        ],
        "summary": {"failed": 1},
        "warnings": [],
        "options": {},
    }
    assert compute_next_recommended_command(doc) == (
        "python run_candidate_factory.py --candidates equal_weight,risk_parity --resume"
    )


def test_build_factory_run_txt_lists_reason_code_for_failed_step() -> None:
    doc = {
        "factory_profile_id": "core_v1",
        "generated_at": "2026-05-20T12:00:00+00:00",
        "summary": {"total": 1, "failed": 1, "succeeded": 0},
        "steps": [
            {
                "candidate_id": "max_return",
                "status": "failed",
                "reason_code": "builder_infeasible_universe",
                "message": "Builder reported FAIL_INFEASIBLE_UNIVERSE.",
                "builder_status": "FAIL_INFEASIBLE_UNIVERSE",
            }
        ],
        "warnings": [],
        "next_recommended_command": "python run_candidate_factory.py --profile core_v1 --resume",
    }
    txt = build_factory_run_txt(doc)
    assert "builder_infeasible_universe" in txt
    assert "max_return" in txt
    assert "CLI exit code (factory only): 1" in txt
    assert "section 8" in txt


def test_factory_validation_error_on_unknown_profile() -> None:
    with pytest.raises(FactoryValidationError):
        resolve_profile_candidate_ids(profile_id="no_such_profile", explicit_candidates=None)


def test_resume_skips_prior_succeeded_without_rerun(tmp_path: Path) -> None:
    subject_dir = tmp_path / "Main portfolio" / "analysis_subject"
    subject_dir.mkdir(parents=True)
    (subject_dir / "run_metadata.json").write_text(
        json.dumps({"run_info": {"analysis_end_date": "2026-04-30"}}),
        encoding="utf-8",
    )
    ew_dir = tmp_path / "equal-weight portfolio"
    ew_dir.mkdir(parents=True)
    rp_dir = tmp_path / "risk parity portfolio"
    rp_dir.mkdir(parents=True)
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    fp = compute_candidate_config_fingerprint(cfg)
    candidates = ["equal_weight", "risk_parity"]

    def _write_snapshot(folder: Path, metrics: dict[str, float]) -> None:
        (folder / "snapshot_10y.json").write_text(
            json.dumps(
                {
                    "analysis_end": "2026-04-30",
                    "candidate_config_fingerprint": fp,
                    "metrics": metrics,
                }
            ),
            encoding="utf-8",
        )

    calls: list[str] = []

    def runner_first(cmd, cwd):  # noqa: ANN001
        script = Path(cmd[1]).name
        calls.append(script)
        if script == "run_equal_weight.py":
            _write_snapshot(ew_dir, {"cagr": 0.07})
            return 0
        return 1

    first = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        explicit_candidates=candidates,
        skip_existing=False,
        runner=runner_first,
    )
    assert first["steps"][0]["status"] == "succeeded"
    assert first["steps"][1]["status"] == "failed"
    assert (tmp_path / "Main portfolio" / MANIFEST_FILENAME).is_file()

    calls.clear()

    def runner_resume(cmd, cwd):  # noqa: ANN001
        script = Path(cmd[1]).name
        calls.append(script)
        if script == "run_risk_parity.py":
            _write_snapshot(rp_dir, {"cagr": 0.06})
        return 0

    second = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        explicit_candidates=candidates,
        skip_existing=False,
        resume=True,
        runner=runner_resume,
    )
    assert calls == ["run_risk_parity.py"]
    ew_step = second["steps"][0]
    rp_step = second["steps"][1]
    assert ew_step["resume_from_manifest"] is True
    assert ew_step["status"] == "succeeded"
    assert rp_step["status"] == "succeeded"
    assert second["summary"]["resumed_from_manifest"] == 1
    assert second["manifest"]["resume_manifest_active"] is True


def test_resume_retries_failed_step_from_manifest(tmp_path: Path) -> None:
    subject_dir = tmp_path / "Main portfolio" / "analysis_subject"
    subject_dir.mkdir(parents=True)
    (subject_dir / "run_metadata.json").write_text(
        json.dumps({"run_info": {"analysis_end_date": "2026-04-30"}}),
        encoding="utf-8",
    )
    ew_dir = tmp_path / "equal-weight portfolio"
    ew_dir.mkdir(parents=True)
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO"],
        }
    )
    checksum = compute_factory_run_checksum(
        factory_profile_id="explicit_list",
        candidate_ids=["equal_weight"],
        analysis_end="2026-04-30",
        config_fingerprint=compute_candidate_config_fingerprint(cfg),
    )
    manifest = {
        "schema_version": "candidate_factory_manifest_v1",
        "run_checksum": checksum,
        "factory_profile_id": "explicit_list",
        "candidate_ids": ["equal_weight"],
        "analysis_end": "2026-04-30",
        "config_fingerprint": compute_candidate_config_fingerprint(cfg),
        "project_root": str(tmp_path),
        "output_dir_final": "Main portfolio",
        "completed_steps": {
            "equal_weight": {
                "candidate_id": "equal_weight",
                "status": "failed",
                "reason_code": "subprocess_failed",
                "recorded_at": "2026-05-20T00:00:00+00:00",
            }
        },
        "last_completed_candidate_id": "equal_weight",
    }
    (tmp_path / "Main portfolio").mkdir(parents=True, exist_ok=True)
    (tmp_path / "Main portfolio" / MANIFEST_FILENAME).write_text(
        json.dumps(manifest), encoding="utf-8"
    )

    calls: list[str] = []

    def runner(cmd, cwd):  # noqa: ANN001
        calls.append(Path(cmd[1]).name)
        (ew_dir / "snapshot_10y.json").write_text(
            json.dumps(
                {
                    "analysis_end": "2026-04-30",
                    "candidate_config_fingerprint": compute_candidate_config_fingerprint(cfg),
                }
            ),
            encoding="utf-8",
        )
        return 0

    doc = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        explicit_candidates=["equal_weight"],
        skip_existing=False,
        resume=True,
        runner=runner,
    )
    assert calls == ["run_equal_weight.py"]
    assert doc["steps"][0]["status"] == "succeeded"
    assert doc["steps"][0].get("resume_from_manifest") is not True


def test_resume_manifest_checksum_mismatch_runs_without_skip(tmp_path: Path) -> None:
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
    stale_manifest = {
        "schema_version": "candidate_factory_manifest_v1",
        "run_checksum": "deadbeef",
        "completed_steps": {
            "equal_weight": {"candidate_id": "equal_weight", "status": "succeeded"}
        },
    }
    (tmp_path / "Main portfolio").mkdir(parents=True, exist_ok=True)
    (tmp_path / "Main portfolio" / MANIFEST_FILENAME).write_text(
        json.dumps(stale_manifest), encoding="utf-8"
    )

    calls: list[str] = []

    def runner(cmd, cwd):  # noqa: ANN001
        calls.append(Path(cmd[1]).name)
        return 0

    doc = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        explicit_candidates=["equal_weight"],
        skip_existing=True,
        resume=True,
        runner=runner,
    )
    assert calls == ["run_equal_weight.py"]
    assert any(w.startswith("resume_manifest_stale:") for w in doc["warnings"])
    assert doc["manifest"]["resume_manifest_active"] is False


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
