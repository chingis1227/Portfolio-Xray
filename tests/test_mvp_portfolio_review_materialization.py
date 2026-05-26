"""Portfolio review integration for Core MVP input (Input Layer Session 07)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import run_report
from mvp_offline_fixtures import (
    FIVE_TICKER_MVP_TICKERS,
    five_ticker_mvp_core_input_dict,
    seed_product_bundle_offline_workspace,
    validate_mvp_fixture,
)
from src.config_schema import validate_config
from src.portfolio_review_workflow import (
    RUNTIME_MODE_PRODUCT_DIAGNOSIS_ONLY,
    build_portfolio_review_plan,
)
from src.real_cash import collect_real_cash_tickers


@pytest.mark.parametrize(
    "fixture_name",
    ["minimal_usd_no_cash.yml", "minimal_usd_with_cash.yml"],
)
def test_mvp_fixture_materialization_resolves_current_portfolio(fixture_name: str) -> None:
    cfg = validate_mvp_fixture(fixture_name)
    mat = run_report.resolve_analysis_subject_materialization(cfg)

    assert mat["status"] == "resolved"
    assert mat["subject"]["type"] == "current_portfolio"
    assert mat["subject"]["portfolio_role"] == "user_current_portfolio"
    assert mat["weights_source"] == "config.analysis_subject.weights"
    assert sum(mat["weights"].values()) == pytest.approx(1.0, abs=1e-6)


def test_mvp_fixture_with_cash_materialization_keeps_cash_usd() -> None:
    cfg = validate_mvp_fixture("minimal_usd_with_cash.yml")
    mat = run_report.resolve_analysis_subject_materialization(cfg)

    assert "Cash USD" in mat["weights"]
    assert mat["weights"]["Cash USD"] == pytest.approx(0.10)
    assert collect_real_cash_tickers(tickers=cfg.tickers, weights=cfg.weights) == ["Cash USD"]


def test_five_ticker_current_weights_materializes_without_explicit_subject() -> None:
    cfg = validate_config(five_ticker_mvp_core_input_dict())
    mat = run_report.resolve_analysis_subject_materialization(cfg)

    assert cfg.analysis_mode == "analyze_current_weights"
    assert cfg.analysis_subject["type"] == "current_portfolio"
    assert mat["status"] == "resolved"
    assert set(mat["weights"]) == set(FIVE_TICKER_MVP_TICKERS)
    assert sum(mat["weights"].values()) == pytest.approx(1.0, abs=1e-6)


def test_mvp_fixture_portfolio_review_plan_materializes_subject_first(tmp_path: Path) -> None:
    cfg = validate_mvp_fixture("minimal_usd_no_cash.yml")
    plan = build_portfolio_review_plan(
        cfg,
        project_root=tmp_path,
        skip_candidates=True,
        skip_compare=True,
        skip_pdf=True,
    )

    assert [step.stage for step in plan.steps] == ["diagnosis"]
    assert plan.runtime_mode == RUNTIME_MODE_PRODUCT_DIAGNOSIS_ONLY
    subject_argv = " ".join(plan.steps[0].argv)
    assert "run_report.py" in subject_argv
    assert "--materialize-analysis-subject" in subject_argv
    assert "--review-mode" in subject_argv
    assert "core" in subject_argv
    assert "run_optimization.py" not in subject_argv


def test_mvp_fixture_one_candidate_product_path(tmp_path: Path) -> None:
    cfg = validate_mvp_fixture("minimal_usd_no_cash.yml")
    plan = build_portfolio_review_plan(
        cfg,
        project_root=tmp_path,
        candidate_ids="equal_weight",
        skip_pdf=True,
    )

    assert [step.stage for step in plan.steps] == ["diagnosis", "candidates"]
    factory_argv = plan.steps[1].argv
    assert "--candidates" in factory_argv
    assert "equal_weight" in factory_argv
    assert "--then-compare" in factory_argv
    assert "run_optimization.py" not in " ".join(" ".join(step.argv) for step in plan.steps)


def test_run_materialize_mvp_fixture_passes_resolved_weights(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = validate_mvp_fixture("minimal_usd_no_cash.yml")
    cfg.output_dir_final = str(tmp_path / "Main portfolio")
    expected_weights = {str(k): float(v) for k, v in (cfg.weights or {}).items()}
    calls: list[dict[str, Any]] = []

    def fake_run_portfolio_report_for_weights(_cfg, weights, **kwargs):
        calls.append({"weights": weights, "kwargs": kwargs})
        out = Path(kwargs["output_dir_final"])
        out.mkdir(parents=True, exist_ok=True)
        (out / "run_metadata.json").write_text("{}", encoding="utf-8")
        (out / "snapshot_10y.json").write_text(
            json.dumps({"metrics": {"cagr": 0.06}, "final_weights_total": weights}),
            encoding="utf-8",
        )
        (out / "stress_report.json").write_text("{}", encoding="utf-8")
        return {}, {"portfolio_valid": True}

    monkeypatch.setattr(
        run_report,
        "run_portfolio_report_for_weights",
        fake_run_portfolio_report_for_weights,
    )
    monkeypatch.setattr(
        run_report,
        "prepare_review_run_context",
        lambda *a, **k: None,
    )

    run_report.run_materialize_analysis_subject_report(
        cfg,
        run_timestamp="2026-05-26T12:00:00",
        backtest_mode="dynamic_nan_safe",
        no_cache=True,
        review_mode="core",
        project_root=tmp_path,
    )

    assert len(calls) == 1
    assert calls[0]["weights"] == expected_weights
    assert calls[0]["kwargs"]["weights_source"] == "config.analysis_subject.weights"
    assert calls[0]["kwargs"]["portfolio_role_override"] == "analysis_subject"
    sidecar = tmp_path / "Main portfolio" / "analysis_subject"
    assert sidecar.is_dir()


def test_offline_product_bundle_seed_run_metadata_core_mvp_profile(
    tmp_path: Path,
) -> None:
    cfg = validate_mvp_fixture("minimal_usd_no_cash.yml")
    seeded = seed_product_bundle_offline_workspace(tmp_path, cfg)
    run_metadata = json.loads(
        (seeded["analysis_subject_dir"] / "run_metadata.json").read_text(encoding="utf-8")
    )
    assumptions = run_metadata["input_assumptions"]

    assert assumptions["input_surface"]["profile"] == "core_mvp"
    assert assumptions["input_surface"]["core_mvp_requirements_met"] is True
    assert assumptions["field_tiers"]["run_disclosure"]["core_mvp"]["requirements_met"] is True
    assert run_metadata["analysis_setup"]["analysis_subject"]["type"] == "current_portfolio"
