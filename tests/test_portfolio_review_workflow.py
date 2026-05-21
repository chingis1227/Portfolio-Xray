"""Tests for portfolio-first review workflow orchestration."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.config_schema import PortfolioConfig, validate_config
from src.portfolio_review_workflow import (
    build_portfolio_review_plan,
    resolve_review_candidate_profile,
    run_portfolio_review_plan,
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
    assert profile == "core_v1"


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


def test_default_plan_uses_core_v1_factory_profile(tmp_path: Path) -> None:
    plan = build_portfolio_review_plan(_cfg(), project_root=tmp_path, skip_pdf=True)
    factory_argv = plan.steps[1].argv
    assert "--profile" in factory_argv
    assert "core_v1" in factory_argv
    assert "default_v1" not in factory_argv


def test_full_mode_plan_uses_default_v1_profile(tmp_path: Path) -> None:
    plan = build_portfolio_review_plan(
        _cfg(),
        project_root=tmp_path,
        review_mode="full",
        skip_pdf=True,
    )
    factory_argv = plan.steps[1].argv
    assert "default_v1" in factory_argv


def test_default_plan_materializes_subject_before_candidates(tmp_path: Path) -> None:
    plan = build_portfolio_review_plan(_cfg(), project_root=tmp_path, skip_pdf=True)

    assert [step.stage for step in plan.steps] == ["diagnosis", "candidates"]
    assert "run_report.py" in " ".join(plan.steps[0].argv)
    assert "--materialize-analysis-subject" in plan.steps[0].argv
    assert "run_candidate_factory.py" in " ".join(plan.steps[1].argv)
    assert "--then-compare" in plan.steps[1].argv
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


def test_default_pdf_step_is_portfolio_first_scope(tmp_path: Path) -> None:
    plan = build_portfolio_review_plan(_cfg(), project_root=tmp_path)
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
