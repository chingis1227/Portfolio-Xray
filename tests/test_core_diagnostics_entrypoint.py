"""Tests for run_core_diagnostics.py and Blocks 1-3 product bundle scope."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from run_portfolio_review import resolve_candidate_execution_flags
from src.config_schema import validate_config
from src.core_diagnostics_workflow import build_core_diagnostics_plan
from src.portfolio_review_workflow import build_portfolio_review_plan
from src.product_bundle_scope import (
    PRODUCT_BUNDLE_SCOPE_CORE_BLOCKS_1_3,
    is_core_blocks_1_3_only,
)


def _cfg(**overrides):
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


def test_core_diagnostics_plan_invokes_core_diagnostics_only_flag(tmp_path: Path) -> None:
    plan = build_core_diagnostics_plan(_cfg(), project_root=tmp_path)
    assert len(plan.steps) == 1
    argv = " ".join(plan.steps[0].argv)
    assert "--materialize-analysis-subject" in argv
    assert "--core-diagnostics-only" in argv
    assert "--output-profile" in argv
    assert "site_api" in argv
    assert "run_candidate_factory" not in argv
    assert "run_compare_variants" not in argv


def test_product_bundle_scope_core_blocks_1_3() -> None:
    assert is_core_blocks_1_3_only(PRODUCT_BUNDLE_SCOPE_CORE_BLOCKS_1_3)
    assert not is_core_blocks_1_3_only("full_product")


def test_portfolio_review_default_skips_candidates() -> None:
    skip_c, skip_cmp, run_c = resolve_candidate_execution_flags()
    assert skip_c is True
    assert skip_cmp is True
    assert run_c is False


def test_portfolio_review_one_candidate_runs_factory(tmp_path: Path) -> None:
    skip_c, skip_cmp, run_c = resolve_candidate_execution_flags(candidates="equal_weight")
    assert skip_c is False
    assert skip_cmp is False
    assert run_c is True
    plan = build_portfolio_review_plan(
        _cfg(),
        project_root=tmp_path,
        skip_candidates=skip_c,
        skip_compare=skip_cmp,
        candidate_ids="equal_weight",
    )
    argv = " ".join(" ".join(s.argv) for s in plan.steps)
    assert "run_candidate_factory.py" in argv
    assert "--candidates" in argv
    assert "equal_weight" in argv


def test_portfolio_review_diagnosis_plan_has_no_factory(tmp_path: Path) -> None:
    plan = build_portfolio_review_plan(
        _cfg(),
        project_root=tmp_path,
        skip_candidates=True,
        skip_compare=True,
    )
    argv = " ".join(" ".join(s.argv) for s in plan.steps)
    assert "run_candidate_factory.py" not in argv
    assert "run_compare_variants.py" not in argv
    assert "--materialize-analysis-subject" in argv
    assert "--core-diagnostics-only" not in argv


def test_materialize_analysis_subject_passes_core_bundle_scope(tmp_path: Path) -> None:
    from run_report import run_materialize_analysis_subject_report

    cfg = _cfg()
    captured: dict[str, object] = {}

    def _fake_report(*_a, **kwargs):
        captured["product_bundle_scope"] = kwargs.get("product_bundle_scope")
        return None, {}

    with patch(
        "run_report.run_portfolio_report_for_weights",
        side_effect=_fake_report,
    ):
        run_materialize_analysis_subject_report(
            cfg,
            run_timestamp="2026-05-29T00:00:00",
            backtest_mode="dynamic_nan_safe",
            no_cache=True,
            core_diagnostics_only=True,
        )
    assert captured.get("product_bundle_scope") == PRODUCT_BUNDLE_SCOPE_CORE_BLOCKS_1_3


def test_legacy_wrapper_delegates_to_legacy_runners() -> None:
    root = Path(__file__).resolve().parents[1]
    wrapper = (root / "run_equal_weight.py").read_text(encoding="utf-8")
    assert "legacy/runners/run_equal_weight.py" in wrapper
    assert (root / "legacy/runners/run_equal_weight.py").is_file()
