"""Tests for portfolio-first review workflow orchestration."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.config_schema import PortfolioConfig, validate_config
from src.candidate_factory import CORE_FAST_PROFILE_ID
from src.portfolio_review_workflow import (
    REVIEW_DEFAULT_FACTORY_EXECUTION_MODE,
    build_portfolio_review_plan,
    resolve_factory_execution_mode,
    resolve_review_candidate_profile,
    run_portfolio_review_plan,
)
from src.workflow_state import (
    WORKFLOW_STATE_DIAGNOSIS_ONLY,
    WORKFLOW_STATE_MULTIPLE_CANDIDATES,
    WORKFLOW_STATE_ONE_CANDIDATE,
)


def _cfg(**overrides) -> PortfolioConfig:
    base = {
        "tickers": ["VOO", "BND"],
        "investor_currency": "USD",
        "analysis_subject": {
            "type": "current_portfolio",
            "weights": {"VOO": 0.6, "BND": 0.4},
        },
    }
    base.update(overrides)
    return validate_config(base)


def _argv_text(plan) -> str:  # noqa: ANN001
    return " ".join(" ".join(step.argv) for step in plan.steps)


def test_resolve_review_candidate_profile_defaults_to_core() -> None:
    mode, profile = resolve_review_candidate_profile()
    assert mode == "core"
    assert profile == CORE_FAST_PROFILE_ID


def test_resolve_review_candidate_profile_full_mode() -> None:
    mode, profile = resolve_review_candidate_profile(review_mode="full")
    assert mode == "full"
    assert profile == "default_v1"


def test_resolve_review_candidate_profile_explicit_override() -> None:
    mode, profile = resolve_review_candidate_profile(
        review_mode="core",
        candidate_profile="default_v1",
    )
    assert mode == "core"
    assert profile == "default_v1"


def test_resolve_factory_execution_mode_defaults_to_standard() -> None:
    assert resolve_factory_execution_mode() == "standard"
    assert REVIEW_DEFAULT_FACTORY_EXECUTION_MODE == "standard"


def test_resolve_factory_execution_mode_honors_explicit_override() -> None:
    assert resolve_factory_execution_mode(factory_execution_mode="legacy_full") == "legacy_full"
    assert resolve_factory_execution_mode(factory_execution_mode="fast") == "fast"


def test_default_plan_uses_core_fast_factory_profile(tmp_path: Path) -> None:
    plan = build_portfolio_review_plan(_cfg(), project_root=tmp_path, skip_pdf=True)
    factory_argv = plan.steps[1].argv
    assert "--profile" in factory_argv
    assert CORE_FAST_PROFILE_ID in factory_argv
    assert "core_v1" not in factory_argv
    assert "default_v1" not in factory_argv
    assert "--execution-mode" in factory_argv
    assert "standard" in factory_argv
    assert "--no-parallel-lightweight-reports" not in factory_argv
    assert plan.workflow_state.state == WORKFLOW_STATE_MULTIPLE_CANDIDATES
    assert plan.workflow_state.candidate_count == 6
    assert plan.workflow_state.source == "factory_profile"


def test_core_mode_plan_uses_core_v1_when_profile_overridden(tmp_path: Path) -> None:
    plan = build_portfolio_review_plan(
        _cfg(),
        project_root=tmp_path,
        candidate_profile="core_v1",
        skip_pdf=True,
    )
    factory_argv = plan.steps[1].argv
    assert "core_v1" in factory_argv
    assert CORE_FAST_PROFILE_ID not in factory_argv


def test_no_parallel_lightweight_reports_forwarded_to_factory(tmp_path: Path) -> None:
    plan = build_portfolio_review_plan(
        _cfg(),
        project_root=tmp_path,
        no_parallel_lightweight_reports=True,
        skip_pdf=True,
    )
    factory_argv = plan.steps[1].argv
    assert "--no-parallel-lightweight-reports" in factory_argv


def test_full_mode_plan_uses_default_v1_profile(tmp_path: Path) -> None:
    plan = build_portfolio_review_plan(
        _cfg(),
        project_root=tmp_path,
        review_mode="full",
        skip_pdf=True,
    )
    factory_argv = plan.steps[1].argv
    assert "default_v1" in factory_argv
    idx = factory_argv.index("--execution-mode")
    assert factory_argv[idx + 1] == "standard"
    assert plan.workflow_state.state == WORKFLOW_STATE_MULTIPLE_CANDIDATES
    assert plan.workflow_state.candidate_count == 16


def test_full_mode_legacy_factory_execution_override(tmp_path: Path) -> None:
    plan = build_portfolio_review_plan(
        _cfg(),
        project_root=tmp_path,
        review_mode="full",
        factory_execution_mode="legacy_full",
        skip_pdf=True,
    )
    factory_argv = plan.steps[1].argv
    idx = factory_argv.index("--execution-mode")
    assert factory_argv[idx + 1] == "legacy_full"


def test_default_plan_materializes_subject_before_candidates(tmp_path: Path) -> None:
    plan = build_portfolio_review_plan(_cfg(), project_root=tmp_path)

    assert [step.stage for step in plan.steps] == ["diagnosis", "candidates"]
    assert "run_report.py" in " ".join(plan.steps[0].argv)
    assert "--materialize-analysis-subject" in plan.steps[0].argv
    assert "--output-profile" in plan.steps[0].argv
    assert "site_api" in plan.steps[0].argv
    assert "--review-mode" in plan.steps[0].argv
    assert "core" in plan.steps[0].argv
    assert "--use-review-run-context" in plan.steps[0].argv


def test_full_mode_plan_materializes_subject_with_full_review_mode(tmp_path: Path) -> None:
    plan = build_portfolio_review_plan(
        _cfg(),
        project_root=tmp_path,
        review_mode="full",
        skip_pdf=True,
    )
    subject_argv = plan.steps[0].argv
    idx = subject_argv.index("--review-mode")
    assert subject_argv[idx + 1] == "full"
    assert "--use-review-run-context" not in subject_argv
    assert "run_candidate_factory.py" in " ".join(plan.steps[1].argv)
    assert "--then-compare" in plan.steps[1].argv
    assert "--output-profile" in plan.steps[1].argv
    assert "run_optimization.py" not in _argv_text(plan)


def test_skip_candidates_compares_existing_artifacts(tmp_path: Path) -> None:
    plan = build_portfolio_review_plan(
        _cfg(),
        project_root=tmp_path,
        skip_candidates=True,
        skip_pdf=True,
    )

    assert [step.stage for step in plan.steps] == ["diagnosis", "comparison"]
    assert "run_compare_variants.py" in " ".join(plan.steps[1].argv)
    assert "run_candidate_factory.py" not in _argv_text(plan)
    assert "run_optimization.py" not in _argv_text(plan)
    assert plan.workflow_state.state == WORKFLOW_STATE_DIAGNOSIS_ONLY
    assert plan.workflow_state.source == "skip_candidates"


def test_candidate_options_are_forwarded_without_policy_step(tmp_path: Path) -> None:
    plan = build_portfolio_review_plan(
        _cfg(),
        project_root=tmp_path,
        candidate_ids="equal_weight,risk_parity",
        skip_existing_candidates=False,
        force_candidates=True,
        resume_candidates=True,
        fail_fast=True,
        skip_compare=True,
        skip_pdf=True,
    )
    argv = plan.steps[1].argv

    assert "--candidates" in argv
    assert "equal_weight,risk_parity" in argv
    assert "--no-skip-existing" in argv
    assert "--force" in argv
    assert "--resume" in argv
    assert "--fail-fast" in argv
    assert "--then-compare" not in argv
    assert "run_optimization.py" not in _argv_text(plan)
    assert plan.workflow_state.state == WORKFLOW_STATE_MULTIPLE_CANDIDATES
    assert plan.workflow_state.candidate_count == 2
    assert plan.workflow_state.comparison_expected is False


def test_single_candidate_plan_records_one_candidate_state(tmp_path: Path) -> None:
    plan = build_portfolio_review_plan(
        _cfg(),
        project_root=tmp_path,
        candidate_ids="equal_weight",
        skip_pdf=True,
    )

    assert plan.workflow_state.state == WORKFLOW_STATE_ONE_CANDIDATE
    assert plan.workflow_state.candidate_count == 1
    assert plan.workflow_state.candidate_ids == ("equal_weight",)


def test_full_mode_resume_candidates_forwards_factory_resume(tmp_path: Path) -> None:
    plan = build_portfolio_review_plan(
        _cfg(),
        project_root=tmp_path,
        review_mode="full",
        resume_candidates=True,
        skip_pdf=True,
    )
    factory_argv = plan.steps[1].argv

    assert "--profile" in factory_argv
    assert "default_v1" in factory_argv
    assert "--resume" in factory_argv
    assert "--then-compare" in factory_argv
    assert "run_optimization.py" not in _argv_text(plan)


def test_dry_run_does_not_execute(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    plan = build_portfolio_review_plan(_cfg(), project_root=tmp_path)

    def _boom(*_args, **_kwargs):
        raise AssertionError("subprocess should not run in dry-run mode")

    monkeypatch.setattr("src.portfolio_review_workflow.subprocess.run", _boom)
    assert run_portfolio_review_plan(plan, project_root=tmp_path, dry_run=True) == 0


def test_default_plan_skips_pdf_step(tmp_path: Path) -> None:
    plan = build_portfolio_review_plan(_cfg(), project_root=tmp_path)

    assert all(step.stage != "action" for step in plan.steps)
    assert "rebuild_pdf_reports.py" not in _argv_text(plan)


def test_explicit_pdf_step_is_portfolio_first_scope(tmp_path: Path) -> None:
    plan = build_portfolio_review_plan(_cfg(), project_root=tmp_path, skip_pdf=False)
    pdf_step = plan.steps[-1]

    assert pdf_step.stage == "action"
    assert "--portfolio-first" in pdf_step.argv
    assert "rebuild_pdf_reports.py" in " ".join(pdf_step.argv)


def test_legacy_full_pdf_rebuilds_entire_suite(tmp_path: Path) -> None:
    plan = build_portfolio_review_plan(_cfg(), project_root=tmp_path, legacy_full_pdf=True)
    pdf_step = plan.steps[-1]

    assert pdf_step.stage == "action"
    assert "--portfolio-first" not in pdf_step.argv
    assert "rebuild_pdf_reports.py" in " ".join(pdf_step.argv)
