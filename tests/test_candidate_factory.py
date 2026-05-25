from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from src import candidate_factory as candidate_factory_module
from src.candidate_factory import (
    CORE_FAST_PROFILE_ID,
    CORE_V1_CANDIDATE_ORDER,
    MANIFEST_FILENAME,
    SCHEMA_VERSION,
    FactoryValidationError,
    build_factory_run_txt,
    candidate_factory_product_boundary,
    candidate_factory_profile_classification,
    compute_factory_run_checksum,
    compute_next_recommended_command,
    factory_exit_code,
    factory_reason_from_builder_summary,
    resolve_full_report_candidate_ids,
    resolve_parallel_lightweight_report_options,
    resolve_profile_candidate_ids,
    run_candidate_factory,
    validate_candidate_ids,
    write_candidate_factory_outputs,
)
from src.report_profile import REPORT_PROFILE_FULL
from src.candidate_run_context import CandidateRunContext
from src.candidate_weights import (
    CANDIDATE_WEIGHTS_BUILD_FILENAME,
    build_candidate_weights,
    write_candidate_weights,
)
from src.data_loader import MonthlyDataResult
from src.portfolio_variants import (
    build_equal_weight_baseline,
    build_minimum_variance_baseline,
    build_risk_parity_baseline,
)
from src.variant_builder_runtime import (
    BUILDER_RUNTIME_TIMING_FILENAME,
    ENV_SKIP_VARIANT_PDF,
    subprocess_env_for_pdf_mode,
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


def test_core_fast_profile_matches_core_v1_candidate_order() -> None:
    core_v1 = resolve_profile_candidate_ids(profile_id="core_v1", explicit_candidates=None)
    core_fast = resolve_profile_candidate_ids(
        profile_id=CORE_FAST_PROFILE_ID, explicit_candidates=None
    )
    assert core_fast == core_v1
    assert core_fast == list(CORE_V1_CANDIDATE_ORDER)


def test_candidate_factory_product_boundary_is_not_default_ux() -> None:
    boundary = candidate_factory_product_boundary()
    assert boundary["runtime_surface"] == "backend_advanced_research"
    assert boundary["default_product_ux"] is False
    assert boundary["preserve_batch_factory"] is True
    assert boundary["product_front_door"] == "run_portfolio_review.py"
    assert boundary["one_candidate_product_wrapper"] == "src.portfolio_alternatives_builder"


def test_candidate_factory_profile_product_classification() -> None:
    assert (
        candidate_factory_profile_classification(CORE_FAST_PROFILE_ID)
        == "backend_routine_core_batch"
    )
    assert (
        candidate_factory_profile_classification("default_v1")
        == "advanced_research_full_batch"
    )
    assert (
        candidate_factory_profile_classification("robust_suite")
        == "advanced_research_subset_batch"
    )
    assert (
        candidate_factory_profile_classification("custom_profile")
        == "advanced_research_custom_batch"
    )


def test_review_mode_for_factory_profile_core_and_legacy() -> None:
    from src.candidate_factory import (
        CORE_FAST_PROFILE_ID,
        review_mode_for_factory_profile,
    )

    assert review_mode_for_factory_profile(CORE_FAST_PROFILE_ID) == "core"
    assert review_mode_for_factory_profile("core_v1") == "core"
    assert review_mode_for_factory_profile("default_v1") == "full"
    assert review_mode_for_factory_profile("unknown") is None


def test_resolve_parallel_lightweight_report_options_core_fast_default() -> None:
    requested, workers, applied = resolve_parallel_lightweight_report_options(
        profile_id=CORE_FAST_PROFILE_ID,
    )
    assert requested is True
    assert workers == 4
    assert applied is True

    requested, workers, applied = resolve_parallel_lightweight_report_options(
        profile_id="core_v1",
    )
    assert requested is False
    assert workers is None
    assert applied is False

    requested, workers, applied = resolve_parallel_lightweight_report_options(
        profile_id=CORE_FAST_PROFILE_ID,
        parallel_lightweight_reports=False,
    )
    assert requested is False
    assert applied is False


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


def test_factory_step_surfaces_optimizer_fallback_quality(tmp_path: Path) -> None:
    mv_dir = tmp_path / "minimum variance portfolio"
    mv_dir.mkdir(parents=True)

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    fp = compute_candidate_config_fingerprint(cfg)

    def runner(cmd, cwd):  # noqa: ANN001
        (mv_dir / "snapshot_10y.json").write_text(
            json.dumps(
                {
                    "analysis_end": None,
                    "candidate_config_fingerprint": fp,
                }
            ),
            encoding="utf-8",
        )
        (mv_dir / "baseline_weights_metadata.json").write_text(
            json.dumps(
                {
                    "optimizer_run_metadata": {
                        "schema_version": "candidate_optimizer_run_metadata_v1",
                        "solver": {
                            "success": True,
                            "status": "OK_FALLBACK",
                            "fallback_used": True,
                            "fallback_reason": "fixture_retry",
                            "optimization_quality_status": "approximate_fallback",
                        },
                    }
                }
            ),
            encoding="utf-8",
        )
        return 0

    doc = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        explicit_candidates=["minimum_variance"],
        skip_existing=False,
        runner=runner,
    )
    step = doc["steps"][0]
    assert step["status"] == "succeeded"
    assert step["optimization_status_source"] == (
        "baseline_weights_metadata.json.optimizer_run_metadata"
    )
    assert step["optimization_quality_status"] == "approximate_fallback"
    assert step["optimization_quality_family"] == "approximate"
    assert step["optimizer_fallback_used"] is True
    assert step["optimizer_fallback_reason"] == "fixture_retry"


def test_robust_scenario_factory_step_surfaces_solver_quality(tmp_path: Path) -> None:
    main = tmp_path / "Main portfolio"
    main.mkdir()
    (main / "scenario_library_normalized.json").write_text("{}", encoding="utf-8")
    (main / "stress_report.json").write_text("{}", encoding="utf-8")
    robust_dir = tmp_path / "robust scenario portfolio"
    robust_dir.mkdir()

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    fp = compute_candidate_config_fingerprint(cfg)

    def runner(cmd, cwd):  # noqa: ANN001
        (robust_dir / "snapshot_10y.json").write_text(
            json.dumps(
                {
                    "analysis_end": None,
                    "candidate_config_fingerprint": fp,
                }
            ),
            encoding="utf-8",
        )
        (robust_dir / "baseline_weights_metadata.json").write_text(
            json.dumps(
                {
                    "optimizer_run_metadata": {
                        "schema_version": "robust_scenario_optimizer_run_metadata_v1",
                        "optimizer_role": "candidate_only",
                        "method_id": "robust_scenario_optimization_v1",
                        "solver": {
                            "name": "SLSQP",
                            "success": True,
                            "status": "OK",
                            "fallback_used": False,
                            "fallback_reason": None,
                            "optimization_quality_status": "clean_solve",
                        },
                    }
                }
            ),
            encoding="utf-8",
        )
        return 0

    doc = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        explicit_candidates=["robust_scenario"],
        skip_existing=False,
        runner=runner,
    )
    step = doc["steps"][0]
    assert step["status"] == "succeeded"
    assert step["optimization_status_source"] == (
        "baseline_weights_metadata.json.optimizer_run_metadata"
    )
    assert step["optimization_quality_status"] == "clean_solve"
    assert step["optimization_quality_family"] == "clean"
    assert step["optimizer_fallback_used"] is False
    assert step["optimizer_solver_status"] == "OK"


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
    txt = paths["candidate_factory_run_txt"].read_text(encoding="utf-8")
    assert "Next:" in txt
    assert "Execution:" in txt
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
    assert ew_step["execution_action"] == "resumed_from_manifest"
    assert ew_step["status"] == "succeeded"
    assert rp_step["execution_action"] == "builder_invoked"
    assert rp_step["status"] == "succeeded"
    assert second["summary"]["resumed_from_manifest"] == 1
    assert second["execution_summary"]["builder_invoked"] == 1
    assert second["execution_summary"]["resumed_from_manifest"] == 1
    assert any(
        w.startswith("resume_manifest_reused_completed_step_despite_no_skip_existing:equal_weight")
        for w in second["warnings"]
    )
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


def test_factory_default_pdf_mode_none(tmp_path: Path) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO"],
        }
    )

    def runner(cmd, cwd, env=None):  # noqa: ANN001
        assert env is not None
        assert env.get(ENV_SKIP_VARIANT_PDF) == "1"
        return 0

    doc = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        explicit_candidates=["equal_weight"],
        skip_existing=False,
        runner=runner,
    )
    assert doc["options"]["pdf_mode"] == "none"


def test_factory_pdf_mode_per_candidate_unsets_skip_env(tmp_path: Path) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO"],
        }
    )
    seen_env: dict[str, str] = {}

    def runner(cmd, cwd, env=None):  # noqa: ANN001
        seen_env.update(env or {})
        return 0

    run_candidate_factory(
        cfg,
        project_root=tmp_path,
        explicit_candidates=["equal_weight"],
        skip_existing=False,
        pdf_mode="per_candidate",
        runner=runner,
    )
    assert ENV_SKIP_VARIANT_PDF not in seen_env


def test_subprocess_env_for_pdf_mode_final_only_sets_skip() -> None:
    env = subprocess_env_for_pdf_mode("final_only")
    assert env[ENV_SKIP_VARIANT_PDF] == "1"


def test_factory_step_timing_from_builder_runtime_file(tmp_path: Path) -> None:
    ew_dir = tmp_path / "equal-weight portfolio"
    ew_dir.mkdir(parents=True)
    timing = {
        "builder_core_seconds": 0.5,
        "report_seconds": 120.0,
        "pdf_seconds": 0.0,
        "total_seconds": 120.5,
    }
    (ew_dir / BUILDER_RUNTIME_TIMING_FILENAME).write_text(
        json.dumps(timing), encoding="utf-8"
    )
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
        skip_existing=False,
        runner=lambda cmd, cwd: 0,
    )
    step = doc["steps"][0]
    assert step["builder_core_seconds"] == 0.5
    assert step["report_seconds"] == 120.0
    assert step["pdf_seconds"] == 0.0
    assert step["total_seconds"] == 120.5
    assert doc["timing_summary"]["steps_with_timing"] == 1
    assert doc["timing_summary"]["report_seconds"] == 120.0
    txt = build_factory_run_txt(doc)
    assert "Timing (seconds):" in txt
    assert "PDF mode: none" in txt


def _synthetic_weights_context(tickers: list[str]) -> CandidateRunContext:
    import numpy as np
    import pandas as pd

    from src.config_schema import PortfolioConfig

    dates = pd.date_range("2015-01-31", periods=80, freq="ME")
    rng = np.random.default_rng(7)
    returns = pd.DataFrame(
        {t: rng.normal(0.005, 0.02, len(dates)) for t in tickers},
        index=dates,
    )
    end_ts = returns.index[-1]
    end = end_ts.strftime("%Y-%m-%d")
    n = len(tickers)
    eq = 1.0 / n if n else 0.0
    cfg = PortfolioConfig(
        investor_currency="USD",
        initial_investable_amount=100_000.0,
        liquidity_need=0.0,
        liquidity_need_months=6.0,
        monthly_expenses=0.0,
        portfolio_value=100_000.0,
        cash_policy="allowed_for_scaling",
        tickers=list(tickers),
        weights={t: eq for t in tickers},
        benchmark_base_ticker="VOO",
        rf_source="FRED:DTB3",
        cash_proxy_ticker="BIL",
        local_benchmark_map=None,
        allow_leverage=False,
        allow_short_selling=False,
        min_acceptable_return=None,
        target_nominal_return_annual=None,
        target_vol_annual=None,
        target_max_drawdown_pct=None,
        horizon_years=None,
        client_profile=None,
        max_single_security_weight_pct=None,
        min_single_security_weight_pct=None,
        N_rc=5,
        donor_shift_mode="proportional",
        windows_months=[36, 60, 120],
        coverage_threshold=0.90,
        output_dir="results_csv",
        output_dir_final="Main portfolio",
    )
    monthly_data = MonthlyDataResult(
        monthly_prices=(1 + returns).cumprod() * 100,
        monthly_returns=returns,
        monthly_log_returns=np.log1p(returns),
        rf_monthly=pd.Series(0.001, index=dates),
        benchmark_returns=pd.Series(rng.normal(0.005, 0.018, len(dates)), index=dates),
        cash_returns=pd.Series(0.0, index=dates),
        fx_series_used={},
        analysis_end=end_ts,
        analysis_end_str=end,
        daily_cache_key="test_daily",
        monthly_cache_key="test_monthly",
    )
    return CandidateRunContext(
        cfg=cfg,
        project_root=Path("."),
        monthly_data=monthly_data,
        assets_meta={},
        cash_proxy_ticker="BIL",
        rf_source="FRED:DTB3",
        local_benchmark_map={},
        report_tickers=list(tickers),
        primary_window=len(dates),
    )


def test_build_candidate_weights_matches_direct_build_pilot_ids() -> None:
    tickers = ["VOO", "BND", "GLD"]
    context = _synthetic_weights_context(tickers)
    for candidate_id, direct_fn in (
        ("equal_weight", build_equal_weight_baseline),
        ("risk_parity", build_risk_parity_baseline),
        ("minimum_variance", build_minimum_variance_baseline),
    ):
        direct = direct_fn(
            context.cfg,
            context.monthly_returns,
            context.analysis_end_str,
            context.primary_window,
        )
        via_api = build_candidate_weights(context, candidate_id)
        assert via_api.status == direct.status
        assert via_api.weights == direct.weights


def test_execution_mode_standard_runs_lightweight_report_phase(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    context = _synthetic_weights_context(["VOO", "BND", "GLD"])
    monkeypatch.setattr(
        "src.candidate_factory.prepare_candidate_run_context",
        lambda cfg, project_root, no_cache=False: context,
    )
    report_calls: list[dict[str, object]] = []
    manifest_writes: list[Path] = []
    manifest_writes_during_report: list[tuple[int, int]] = []
    original_write_factory_manifest = candidate_factory_module.write_factory_manifest

    def tracking_write_factory_manifest(manifest: dict, output_dir: Path) -> Path:
        manifest_writes.append(output_dir)
        return original_write_factory_manifest(manifest, output_dir)

    monkeypatch.setattr(
        "src.candidate_factory.write_factory_manifest",
        tracking_write_factory_manifest,
    )

    def fake_report(*args, **kwargs):
        writes_before = len(manifest_writes)
        report_calls.append(
            {
                "profile": kwargs.get("report_profile"),
                "run_context": kwargs.get("run_context"),
            }
        )
        profile = kwargs.get("report_profile")
        out = kwargs["output_dir_final"]
        out.mkdir(parents=True, exist_ok=True)
        snap = {
            "analysis_end": context.analysis_end_str,
            "window_label": "10y",
            "metrics": {
                "cagr": 0.07,
                "vol_annual": 0.11,
                "max_drawdown": -0.15,
                "sharpe": 0.8,
                "sortino": 1.0,
                "beta_portfolio": 0.7,
                "correlation_benchmark": 0.9,
            },
            "stress_suite_results": {
                "overall": "DIAG_PASS",
                "fail_reason_code": None,
                "failed_scenario": None,
                "scenarios": [],
            },
            "RC_asset": [{"ticker": "VOO", "rc_vol": 0.5}, {"ticker": "BND", "rc_vol": 0.3}],
            "final_weights_total": {"VOO": 0.33, "BND": 0.33, "GLD": 0.34},
        }
        (out / "snapshot_10y.json").write_text(json.dumps(snap), encoding="utf-8")
        (out / "stress_report.json").write_text(
            json.dumps({"status": "DIAG_PASS", "analysis_end": context.analysis_end_str}),
            encoding="utf-8",
        )
        manifest_writes_during_report.append((writes_before, len(manifest_writes)))
        return snap["metrics"], {"stress_report": {"status": "DIAG_PASS"}, "portfolio_valid": True}

    monkeypatch.setattr(
        "run_report.run_portfolio_report_for_weights",
        fake_report,
    )

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND", "GLD"],
        }
    )
    doc = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        explicit_candidates=["equal_weight", "risk_parity"],
        skip_existing=False,
        execution_mode="standard",
        runner=lambda cmd, cwd: pytest.fail("subprocess should not run"),
    )
    assert report_calls
    assert all(c["profile"] == "lightweight_comparison" for c in report_calls)
    assert all(c["run_context"] is context for c in report_calls)
    assert len(manifest_writes) == 3
    assert manifest_writes_during_report == [(0, 0), (1, 1)]
    for cid in ("equal_weight", "risk_parity"):
        step = next(s for s in doc["steps"] if s["candidate_id"] == cid)
        assert step["status"] == "succeeded"
        assert step["phases_completed"] == ["weights", "report"]
        assert step["report_profile"] == "lightweight_comparison"
        art = tmp_path / step["artifact_root"]
        assert (art / "snapshot_10y.json").is_file()
        assert (art / "stress_report.json").is_file()


def _comparison_critical_snapshot_fields(snap: dict) -> dict:
    return {
        "analysis_end": snap.get("analysis_end"),
        "window_label": snap.get("window_label"),
        "metrics": snap.get("metrics"),
        "stress_suite_results": snap.get("stress_suite_results"),
        "RC_asset": snap.get("RC_asset"),
        "final_weights_total": snap.get("final_weights_total"),
    }


def _install_standard_factory_report_fake(
    monkeypatch: pytest.MonkeyPatch,
    context: CandidateRunContext,
    *,
    per_candidate_metrics: dict[str, dict] | None = None,
) -> None:
    per_candidate_metrics = per_candidate_metrics or {}

    def fake_report(*args, **kwargs):
        cid = str(kwargs.get("weights_source")).split(".")[-1]
        out = kwargs["output_dir_final"]
        out.mkdir(parents=True, exist_ok=True)
        metrics = per_candidate_metrics.get(
            cid,
            {
                "cagr": 0.07,
                "vol_annual": 0.11,
                "max_drawdown": -0.15,
                "sharpe": 0.8,
                "sortino": 1.0,
                "beta_portfolio": 0.7,
                "correlation_benchmark": 0.9,
            },
        )
        snap = {
            "analysis_end": context.analysis_end_str,
            "window_label": "10y",
            "metrics": metrics,
            "stress_suite_results": {
                "overall": "DIAG_PASS",
                "fail_reason_code": None,
                "failed_scenario": None,
                "scenarios": [],
            },
            "RC_asset": [{"ticker": "VOO", "rc_vol": 0.5}, {"ticker": "BND", "rc_vol": 0.3}],
            "final_weights_total": {"VOO": 0.5, "BND": 0.5},
        }
        (out / "snapshot_10y.json").write_text(json.dumps(snap), encoding="utf-8")
        (out / "stress_report.json").write_text(
            json.dumps({"status": "DIAG_PASS", "analysis_end": context.analysis_end_str}),
            encoding="utf-8",
        )
        return snap["metrics"], {"stress_report": {"status": "DIAG_PASS"}, "portfolio_valid": True}

    monkeypatch.setattr("run_report.run_portfolio_report_for_weights", fake_report)


def test_core_fast_profile_enables_parallel_lightweight_by_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    context = _synthetic_weights_context(["VOO", "BND", "GLD"])
    monkeypatch.setattr(
        "src.candidate_factory.prepare_candidate_run_context",
        lambda cfg, project_root, no_cache=False: context,
    )
    _install_standard_factory_report_fake(monkeypatch, context)

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND", "GLD"],
        }
    )
    doc = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        profile_id=CORE_FAST_PROFILE_ID,
        skip_existing=False,
        execution_mode="standard",
        runner=lambda cmd, cwd: pytest.fail("subprocess should not run"),
    )

    assert doc["factory_profile_id"] == CORE_FAST_PROFILE_ID
    assert doc["options"]["parallel_lightweight_reports"] is True
    assert doc["options"]["parallel_lightweight_reports_profile_default"] is True
    assert doc["options"]["parallel_lightweight_reports_effective"] is True
    assert doc["options"]["lightweight_report_workers"] == 4
    parallel = doc["parallel_lightweight_report_summary"]
    assert parallel is not None
    assert parallel["status"] == "parallel"
    assert parallel["workers"] == 4
    assert parallel["submitted_count"] == len(CORE_V1_CANDIDATE_ORDER)


def test_core_v1_profile_stays_sequential_without_explicit_parallel_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    context = _synthetic_weights_context(["VOO", "BND", "GLD"])
    monkeypatch.setattr(
        "src.candidate_factory.prepare_candidate_run_context",
        lambda cfg, project_root, no_cache=False: context,
    )
    _install_standard_factory_report_fake(monkeypatch, context)

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND", "GLD"],
        }
    )
    doc = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        profile_id="core_v1",
        skip_existing=False,
        execution_mode="standard",
        runner=lambda cmd, cwd: pytest.fail("subprocess should not run"),
    )

    assert doc["options"]["parallel_lightweight_reports"] is False
    assert doc["options"]["parallel_lightweight_reports_profile_default"] is False
    assert doc["options"]["parallel_lightweight_reports_effective"] is False
    assert doc.get("parallel_lightweight_report_summary") is None


def test_core_fast_parallel_matches_core_v1_sequential_comparison_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tickers = ["VOO", "BND", "GLD"]
    context = _synthetic_weights_context(tickers)
    monkeypatch.setattr(
        "src.candidate_factory.prepare_candidate_run_context",
        lambda cfg, project_root, no_cache=False: context,
    )
    per_candidate_metrics = {
        cid: {
            "cagr": 0.05 + 0.01 * idx,
            "vol_annual": 0.10 + 0.01 * idx,
            "max_drawdown": -0.12,
            "sharpe": 0.7 + 0.05 * idx,
            "sortino": 0.9,
            "beta_portfolio": 0.6,
            "correlation_benchmark": 0.85,
        }
        for idx, cid in enumerate(CORE_V1_CANDIDATE_ORDER)
    }
    _install_standard_factory_report_fake(
        monkeypatch, context, per_candidate_metrics=per_candidate_metrics
    )

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": tickers,
        }
    )

    def _snapshots_by_candidate(doc: dict) -> dict[str, dict]:
        out: dict[str, dict] = {}
        for step in doc["steps"]:
            if step["status"] != "succeeded":
                continue
            art = tmp_path / step["artifact_root"]
            snap = json.loads((art / "snapshot_10y.json").read_text(encoding="utf-8"))
            out[step["candidate_id"]] = _comparison_critical_snapshot_fields(snap)
        return out

    sequential_doc = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        profile_id="core_v1",
        skip_existing=False,
        execution_mode="standard",
        parallel_lightweight_reports=False,
        runner=lambda cmd, cwd: pytest.fail("subprocess should not run"),
    )
    parallel_doc = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        profile_id=CORE_FAST_PROFILE_ID,
        skip_existing=False,
        execution_mode="standard",
        runner=lambda cmd, cwd: pytest.fail("subprocess should not run"),
    )

    assert sequential_doc["summary"]["succeeded"] == len(CORE_V1_CANDIDATE_ORDER)
    assert parallel_doc["summary"]["succeeded"] == len(CORE_V1_CANDIDATE_ORDER)
    assert parallel_doc["options"]["parallel_lightweight_reports_effective"] is True

    sequential_snaps = _snapshots_by_candidate(sequential_doc)
    parallel_snaps = _snapshots_by_candidate(parallel_doc)
    assert set(sequential_snaps) == set(CORE_V1_CANDIDATE_ORDER)
    assert sequential_snaps == parallel_snaps


def test_parallel_lightweight_reports_overlap_and_keep_menu_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    context = _synthetic_weights_context(["VOO", "BND", "GLD"])
    monkeypatch.setattr(
        "src.candidate_factory.prepare_candidate_run_context",
        lambda cfg, project_root, no_cache=False: context,
    )
    barrier = threading.Barrier(2, timeout=3.0)
    lock = threading.Lock()
    active = 0
    max_active = 0
    started: list[str] = []
    completed: list[str] = []
    risk_parity_finished = threading.Event()

    def fake_report(*args, **kwargs):
        nonlocal active, max_active
        cid = str(kwargs.get("weights_source")).split(".")[-1]
        with lock:
            started.append(cid)
            active += 1
            max_active = max(max_active, active)
        try:
            barrier.wait()
            out = kwargs["output_dir_final"]
            out.mkdir(parents=True, exist_ok=True)
            snap = {
                "analysis_end": context.analysis_end_str,
                "window_label": "10y",
                "metrics": {"cagr": 0.07, "vol_annual": 0.11},
                "stress_suite_results": {"overall": "DIAG_PASS", "scenarios": []},
                "RC_asset": [],
                "final_weights_total": {"VOO": 0.5, "BND": 0.5},
            }
            (out / "snapshot_10y.json").write_text(json.dumps(snap), encoding="utf-8")
            (out / "stress_report.json").write_text("{}", encoding="utf-8")
            if cid == "risk_parity":
                completed.append(cid)
                risk_parity_finished.set()
            else:
                assert risk_parity_finished.wait(timeout=3.0)
                completed.append(cid)
            return snap["metrics"], {"stress_report": {}, "portfolio_valid": True}
        finally:
            with lock:
                active -= 1

    monkeypatch.setattr("run_report.run_portfolio_report_for_weights", fake_report)

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND", "GLD"],
        }
    )
    doc = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        explicit_candidates=["equal_weight", "risk_parity"],
        skip_existing=False,
        execution_mode="standard",
        parallel_lightweight_reports=True,
        lightweight_report_workers=2,
        runner=lambda cmd, cwd: pytest.fail("subprocess should not run"),
    )

    assert set(started) == {"equal_weight", "risk_parity"}
    assert completed == ["risk_parity", "equal_weight"]
    assert max_active == 2
    assert doc["options"]["parallel_lightweight_reports_effective"] is True
    parallel = doc["parallel_lightweight_report_summary"]
    assert parallel["status"] == "parallel"
    assert parallel["workers"] == 2
    assert parallel["submitted_count"] == 2
    assert parallel["completed_count"] == 2
    assert parallel["submitted_candidate_ids"] == ["equal_weight", "risk_parity"]
    assert parallel["registered_candidate_ids"] == ["equal_weight", "risk_parity"]
    assert parallel["wall_clock_seconds"] >= 0
    assert [s["candidate_id"] for s in doc["steps"]] == ["equal_weight", "risk_parity"]
    assert [s["status"] for s in doc["steps"]] == ["succeeded", "succeeded"]
    txt = build_factory_run_txt(doc)
    assert "Parallel lightweight reports: status=parallel" in txt


def test_parallel_lightweight_report_failure_continues_without_fail_fast(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    context = _synthetic_weights_context(["VOO", "BND", "GLD"])
    monkeypatch.setattr(
        "src.candidate_factory.prepare_candidate_run_context",
        lambda cfg, project_root, no_cache=False: context,
    )

    def fake_report(*args, **kwargs):
        cid = str(kwargs.get("weights_source")).split(".")[-1]
        if cid == "equal_weight":
            raise RuntimeError("fixture report failure")
        out = kwargs["output_dir_final"]
        out.mkdir(parents=True, exist_ok=True)
        snap = {
            "analysis_end": context.analysis_end_str,
            "window_label": "10y",
            "metrics": {"cagr": 0.07, "vol_annual": 0.11},
            "stress_suite_results": {"overall": "DIAG_PASS", "scenarios": []},
            "RC_asset": [],
            "final_weights_total": {"VOO": 0.5, "BND": 0.5},
        }
        (out / "snapshot_10y.json").write_text(json.dumps(snap), encoding="utf-8")
        (out / "stress_report.json").write_text("{}", encoding="utf-8")
        return snap["metrics"], {"stress_report": {}, "portfolio_valid": True}

    monkeypatch.setattr("run_report.run_portfolio_report_for_weights", fake_report)

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND", "GLD"],
        }
    )
    doc = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        explicit_candidates=["equal_weight", "risk_parity"],
        skip_existing=False,
        execution_mode="standard",
        parallel_lightweight_reports=True,
        lightweight_report_workers=2,
        runner=lambda cmd, cwd: pytest.fail("subprocess should not run"),
    )

    assert [s["candidate_id"] for s in doc["steps"]] == ["equal_weight", "risk_parity"]
    assert [s["status"] for s in doc["steps"]] == ["failed", "succeeded"]
    assert doc["steps"][0]["execution_action"] == "lightweight_report_failed"
    assert doc["summary"]["failed"] == 1
    assert doc["summary"]["succeeded"] == 1
    assert factory_exit_code(doc) == 1


def test_parallel_lightweight_reports_requested_fail_fast_uses_sequential_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    context = _synthetic_weights_context(["VOO", "BND", "GLD"])
    monkeypatch.setattr(
        "src.candidate_factory.prepare_candidate_run_context",
        lambda cfg, project_root, no_cache=False: context,
    )
    calls: list[str] = []

    def fake_report(*args, **kwargs):
        cid = str(kwargs.get("weights_source")).split(".")[-1]
        calls.append(cid)
        raise RuntimeError("fixture report failure")

    monkeypatch.setattr("run_report.run_portfolio_report_for_weights", fake_report)

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND", "GLD"],
        }
    )
    doc = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        explicit_candidates=["equal_weight", "risk_parity"],
        skip_existing=False,
        fail_fast=True,
        execution_mode="standard",
        parallel_lightweight_reports=True,
        lightweight_report_workers=2,
        runner=lambda cmd, cwd: pytest.fail("subprocess should not run"),
    )

    assert calls == ["equal_weight"]
    assert doc["options"]["parallel_lightweight_reports"] is True
    assert doc["options"]["parallel_lightweight_reports_effective"] is False
    parallel = doc["parallel_lightweight_report_summary"]
    assert parallel["status"] == "sequential_fallback"
    assert parallel["fallback_reasons"] == ["fail_fast"]
    assert parallel["submitted_count"] == 0
    assert parallel["completed_count"] == 0
    assert [s["candidate_id"] for s in doc["steps"]] == ["equal_weight"]
    assert doc["steps"][0]["status"] == "failed"


def test_execution_mode_standard_builds_weights_without_subprocess(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    context = _synthetic_weights_context(["VOO", "BND", "GLD"])
    monkeypatch.setattr(
        "src.candidate_factory.prepare_candidate_run_context",
        lambda cfg, project_root, no_cache=False: context,
    )

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND", "GLD"],
        }
    )
    calls: list[list[str]] = []

    monkeypatch.setattr(
        "run_report.run_portfolio_report_for_weights",
        lambda *a, **k: ({}, {"stress_report": {}, "portfolio_valid": True}),
    )
    doc = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        explicit_candidates=["equal_weight"],
        skip_existing=False,
        execution_mode="fast",
        runner=lambda cmd, cwd: (calls.append(cmd) or 0),
    )
    assert not calls
    step = doc["steps"][0]
    assert step["status"] == "succeeded"
    assert step["execution_action"] == "weights_built"
    assert step["phases_completed"] == ["weights"]
    assert doc["execution_summary"]["build_steps_executed"] == 1
    assert doc["execution_summary"]["in_process_build_steps"] == 1
    assert doc["execution_summary"]["rebuilt_candidate_ids"] == ["equal_weight"]
    art = tmp_path / step["artifact_root"]
    assert (art / "weights.json").is_file()
    assert (art / CANDIDATE_WEIGHTS_BUILD_FILENAME).is_file()
    assert not (art / "snapshot_10y.json").is_file()
    assert doc["options"]["execution_mode"] == "fast"


def test_weights_build_manifest_skip_existing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    context = _synthetic_weights_context(["VOO", "BND"])
    monkeypatch.setattr(
        "src.candidate_factory.prepare_candidate_run_context",
        lambda cfg, project_root, no_cache=False: context,
    )
    subject_dir = tmp_path / "Main portfolio" / "analysis_subject"
    subject_dir.mkdir(parents=True)
    (subject_dir / "run_metadata.json").write_text(
        json.dumps({"run_info": {"analysis_end_date": context.analysis_end_str}}),
        encoding="utf-8",
    )
    ew_dir = tmp_path / "equal-weight portfolio"
    ew_dir.mkdir(parents=True)
    fp = compute_candidate_config_fingerprint(
        validate_config(
            {
                "investor_currency": "USD",
                "analysis_mode": "optimize_from_universe",
                "output_dir_final": "Main portfolio",
                "tickers": ["VOO", "BND"],
            }
        )
    )
    write_candidate_weights(
        context,
        "equal_weight",
        build_candidate_weights(context, "equal_weight"),
        artifact_dir=ew_dir,
        config_fingerprint=fp,
    )

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    calls: list[list[str]] = []

    doc = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        explicit_candidates=["equal_weight"],
        skip_existing=True,
        execution_mode="fast",
        runner=lambda cmd, cwd: (calls.append(cmd) or 0),
    )
    assert not calls
    step = doc["steps"][0]
    assert step["status"] == "skipped_existing"
    assert step["execution_action"] == "reused_existing_weights"
    assert doc["execution_summary"]["reused_existing"] == 1
    assert doc["execution_summary"]["reused_existing_weights"] == 1
    assert doc["execution_summary"]["reused_candidate_ids"] == ["equal_weight"]


def test_resolve_full_report_candidate_ids_selected_subset() -> None:
    ids = resolve_full_report_candidate_ids(
        ["equal_weight", "risk_parity", "minimum_variance"],
        full_candidate_reports=False,
        selected=["equal_weight", "risk_parity"],
    )
    assert ids == ["equal_weight", "risk_parity"]


def test_resolve_full_report_candidate_ids_unknown_raises() -> None:
    with pytest.raises(FactoryValidationError, match="Unknown candidate"):
        resolve_full_report_candidate_ids(
            ["equal_weight"],
            full_candidate_reports=False,
            selected=["not_a_real_id"],
        )


def test_full_candidate_reports_runs_full_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    context = _synthetic_weights_context(["VOO", "BND", "GLD"])
    monkeypatch.setattr(
        "src.candidate_factory.prepare_candidate_run_context",
        lambda cfg, project_root, no_cache=False: context,
    )
    report_calls: list[str] = []

    def fake_report(*args, **kwargs):
        profile = kwargs.get("report_profile")
        report_calls.append(str(profile))
        out = kwargs["output_dir_final"]
        out.mkdir(parents=True, exist_ok=True)
        snap = {
            "analysis_end": context.analysis_end_str,
            "window_label": "10y",
            "metrics": {"cagr": 0.07, "vol_annual": 0.11},
            "stress_suite_results": {"overall": "DIAG_PASS", "scenarios": []},
            "RC_asset": [],
            "final_weights_total": {"VOO": 0.5, "BND": 0.5},
        }
        (out / "snapshot_10y.json").write_text(json.dumps(snap), encoding="utf-8")
        (out / "stress_report.json").write_text("{}", encoding="utf-8")
        if profile == REPORT_PROFILE_FULL:
            (out / "report.html").write_text("<html></html>", encoding="utf-8")
        return snap["metrics"], {"stress_report": {}, "portfolio_valid": True}

    monkeypatch.setattr(
        "run_report.run_portfolio_report_for_weights",
        fake_report,
    )

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND", "GLD"],
        }
    )
    doc = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        explicit_candidates=["equal_weight", "risk_parity"],
        skip_existing=False,
        execution_mode="standard",
        selected_candidates_for_full_report=["equal_weight"],
        runner=lambda cmd, cwd: pytest.fail("subprocess should not run"),
    )
    assert report_calls.count("lightweight_comparison") == 2
    assert report_calls.count(REPORT_PROFILE_FULL) == 1
    full_steps = [
        s
        for s in doc["steps"]
        if s.get("execution_action") in ("full_report_built", "full_report_skipped_existing")
    ]
    assert len(full_steps) == 1
    assert full_steps[0]["candidate_id"] == "equal_weight"
    assert full_steps[0]["execution_action"] == "full_report_built"
    assert doc["options"]["selected_candidates_for_full_report"] == ["equal_weight"]


def test_full_report_skips_existing_report_html(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    context = _synthetic_weights_context(["VOO", "BND"])
    monkeypatch.setattr(
        "src.candidate_factory.prepare_candidate_run_context",
        lambda cfg, project_root, no_cache=False: context,
    )
    ew_dir = tmp_path / "equal-weight portfolio"
    ew_dir.mkdir(parents=True)
    (ew_dir / "weights.json").write_text(
        json.dumps({"VOO": 0.5, "BND": 0.5}), encoding="utf-8"
    )
    (ew_dir / "report.html").write_text("<html>existing</html>", encoding="utf-8")

    monkeypatch.setattr(
        "run_report.run_portfolio_report_for_weights",
        lambda *a, **k: pytest.fail("report should be skipped"),
    )

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    doc = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        explicit_candidates=["equal_weight"],
        skip_existing=True,
        execution_mode="fast",
        full_candidate_reports=True,
        runner=lambda cmd, cwd: pytest.fail("subprocess"),
    )
    step = next(
        s
        for s in doc["steps"]
        if s.get("execution_action") == "full_report_skipped_existing"
    )
    assert step["candidate_id"] == "equal_weight"
