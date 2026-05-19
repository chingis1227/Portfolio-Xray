from __future__ import annotations

import json
from pathlib import Path

import pytest

import run_report
from src.analysis_setup import build_analysis_setup
from src.config_schema import validate_config


def test_materialization_resolves_explicit_current_subject_weights() -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "tickers": ["VOO", "BND"],
            "analysis_subject": {
                "type": "current_portfolio",
                "weights": {"VOO": 0.6, "BND": 0.4},
            },
        }
    )

    mat = run_report.resolve_analysis_subject_materialization(cfg)

    assert mat["status"] == "resolved"
    assert mat["weights"] == {"VOO": 0.6, "BND": 0.4}
    assert mat["weights_source"] == "config.analysis_subject.weights"
    assert mat["subject"]["portfolio_role"] == "user_current_portfolio"


def test_materialization_resolves_explicit_model_subject_weights() -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "tickers": ["VOO", "BND", "GLD"],
            "analysis_subject": {
                "type": "model_portfolio",
                "weights": {"VOO": 0.5, "BND": 0.3, "GLD": 0.2},
            },
        }
    )

    mat = run_report.resolve_analysis_subject_materialization(cfg)

    assert mat["status"] == "resolved"
    assert mat["weights"] == {"VOO": 0.5, "BND": 0.3, "GLD": 0.2}
    assert mat["subject"]["portfolio_role"] == "model_portfolio"


def test_materialization_resolves_universe_baseline_before_generated_policy_weights() -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "tickers": ["VOO", "BND"],
        }
    )
    cfg.weights = {"VOO": 0.9, "BND": 0.1}
    cfg.weights_source = "optimization_result_released"

    mat = run_report.resolve_analysis_subject_materialization(cfg)
    setup = build_analysis_setup(
        cfg,
        portfolio_weights=mat["weights"],
        weights_source=mat["weights_source"],
        portfolio_role_override="analysis_subject",
    )

    assert mat["status"] == "resolved"
    assert mat["weights"] == {"VOO": 0.5, "BND": 0.5}
    assert mat["subject"]["type"] == "universe_baseline"
    assert setup["analysis_portfolio"]["portfolio_role"] == "equal_weight_initial_baseline"
    assert setup["analysis_portfolio"]["recommendation_status"] == "baseline_not_recommendation"


def test_run_materialize_analysis_subject_writes_to_canonical_sidecar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "tickers": ["VOO", "BND"],
            "output_dir_final": str(tmp_path / "Main portfolio"),
            "analysis_subject": {
                "type": "current_portfolio",
                "weights": {"VOO": 0.55, "BND": 0.45},
            },
        }
    )
    calls: list[dict] = []

    def fake_run_portfolio_report_for_weights(*args, **kwargs):
        calls.append({"args": args, "kwargs": kwargs})
        out = kwargs["output_dir_final"]
        (out / "run_metadata.json").write_text(
            json.dumps({"analysis_setup": {"analysis_subject": {"type": "current_portfolio"}}}),
            encoding="utf-8",
        )
        return {}, {"portfolio_valid": True}

    monkeypatch.setattr(
        run_report,
        "run_portfolio_report_for_weights",
        fake_run_portfolio_report_for_weights,
    )

    run_report.run_materialize_analysis_subject_report(
        cfg,
        run_timestamp="2026-05-18T10:00:00",
        backtest_mode="dynamic_nan_safe",
        no_cache=True,
    )

    assert len(calls) == 1
    call = calls[0]
    assert call["args"][1] == {"VOO": 0.55, "BND": 0.45}
    assert call["kwargs"]["output_dir_final"] == tmp_path / "Main portfolio" / "analysis_subject"
    assert call["kwargs"]["output_dir_csv"] == tmp_path / "Main portfolio" / "analysis_subject" / "results_csv"
    assert call["kwargs"]["weights_source"] == "config.analysis_subject.weights"
    assert call["kwargs"]["portfolio_role_override"] == "analysis_subject"
    assert (tmp_path / "Main portfolio" / "analysis_subject" / "run_metadata.json").is_file()
