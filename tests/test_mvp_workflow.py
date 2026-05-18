"""Tests for file-first MVP workflow orchestration."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.config_schema import PortfolioConfig, validate_config
from src.mvp_workflow import (
    WORKFLOW_FULL_DECISION,
    WORKFLOW_POLICY_CURRENT,
    WORKFLOW_POLICY_ONLY,
    build_mvp_workflow_plan,
    run_mvp_workflow_plan,
)


def _cfg(**overrides) -> PortfolioConfig:
    base = {
        "tickers": ["VOO", "BND"],
        "investor_currency": "USD",
        "analysis_mode": "optimize_from_universe",
    }
    base.update(overrides)
    return validate_config(base)


def test_policy_only_plan_includes_optimize_and_compare(tmp_path: Path) -> None:
    plan = build_mvp_workflow_plan(_cfg(), project_root=tmp_path, workflow=WORKFLOW_POLICY_ONLY)
    labels = [s.label for s in plan.steps if s.argv]
    assert any("optimization" in label.lower() for label in labels)
    assert any("comparison" in label.lower() for label in labels)
    assert not any("materialize" in label.lower() for label in labels)


def test_policy_current_adds_materialize_when_weights_set(tmp_path: Path) -> None:
    plan = build_mvp_workflow_plan(
        _cfg(current_weights={"VOO": 0.6, "BND": 0.4}),
        project_root=tmp_path,
        workflow=WORKFLOW_POLICY_CURRENT,
    )
    argv_joined = " ".join(" ".join(s.argv) for s in plan.steps if s.argv)
    assert "--materialize-current" in argv_joined


def test_full_decision_runs_factory_then_compare_via_flag(tmp_path: Path) -> None:
    plan = build_mvp_workflow_plan(
        _cfg(),
        project_root=tmp_path,
        workflow=WORKFLOW_FULL_DECISION,
    )
    factory_steps = [s for s in plan.steps if s.argv and "run_candidate_factory" in " ".join(s.argv)]
    assert len(factory_steps) == 1
    assert "--then-compare" in factory_steps[0].argv
    assert not any(
        s.argv and "run_compare_variants" in " ".join(s.argv) for s in plan.steps
    )


def test_skip_optimize_uses_report_only(tmp_path: Path) -> None:
    plan = build_mvp_workflow_plan(
        _cfg(),
        project_root=tmp_path,
        workflow=WORKFLOW_POLICY_ONLY,
        skip_optimize=True,
    )
    argv_joined = " ".join(" ".join(s.argv) for s in plan.steps if s.argv)
    assert "run_optimization.py" not in argv_joined
    assert "run_report.py" in argv_joined


def test_dry_run_does_not_execute(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    plan = build_mvp_workflow_plan(_cfg(), project_root=tmp_path, workflow=WORKFLOW_POLICY_ONLY)

    def _boom(*_args, **_kwargs):
        raise AssertionError("subprocess should not run in dry-run mode")

    monkeypatch.setattr("src.mvp_workflow.subprocess.run", _boom)
    assert run_mvp_workflow_plan(plan, project_root=tmp_path, dry_run=True) == 0
