from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import run_report
from src.analysis_setup import build_analysis_setup
from src.candidate_comparison import analysis_subject_meets_minimum, sidecar_meets_minimum
from src.candidate_run_context import ReviewRunContext
from src.config_schema import validate_config
from src.report_profile import REPORT_PROFILE_FULL, REPORT_PROFILE_LIGHTWEIGHT


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


def test_resolve_analysis_subject_report_profile_by_review_mode() -> None:
    assert (
        run_report.resolve_analysis_subject_report_profile(review_mode="core")
        == REPORT_PROFILE_LIGHTWEIGHT
    )
    assert (
        run_report.resolve_analysis_subject_report_profile(review_mode="full")
        == REPORT_PROFILE_FULL
    )
    assert (
        run_report.resolve_analysis_subject_report_profile(
            review_mode="full",
            report_profile=REPORT_PROFILE_LIGHTWEIGHT,
        )
        == REPORT_PROFILE_LIGHTWEIGHT
    )


def test_should_use_review_run_context_for_subject_defaults() -> None:
    assert run_report.should_use_review_run_context_for_subject(review_mode="core") is False
    assert run_report.should_use_review_run_context_for_subject(review_mode="full") is False
    assert (
        run_report.should_use_review_run_context_for_subject(
            review_mode="core",
            use_review_run_context=True,
        )
        is True
    )
    assert (
        run_report.should_use_review_run_context_for_subject(
            review_mode="core",
            use_review_run_context=False,
        )
        is False
    )


def test_run_materialize_analysis_subject_core_can_opt_into_lightweight_context(
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
    review_ctx = MagicMock(spec=ReviewRunContext)
    calls: list[dict] = []

    def fake_run_portfolio_report_for_weights(*args, **kwargs):
        calls.append(kwargs)
        out = kwargs["output_dir_final"]
        (out / "snapshot_10y.json").write_text(
            json.dumps({"metrics": {"cagr": 0.1}, "weights": {"VOO": 0.55, "BND": 0.45}}),
            encoding="utf-8",
        )
        (out / "run_metadata.json").write_text(
            json.dumps(
                {
                    "analysis_setup": {
                        "analysis_subject": {"type": "current_portfolio", "id": "analysis_subject"},
                        "analysis_portfolio": {"portfolio_role": "user_current_portfolio"},
                    }
                }
            ),
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
        lambda *a, **k: review_ctx,
    )

    returned = run_report.run_materialize_analysis_subject_report(
        cfg,
        run_timestamp="2026-05-18T10:00:00",
        backtest_mode="dynamic_nan_safe",
        no_cache=True,
        review_mode="core",
        project_root=tmp_path,
        use_review_run_context=True,
    )

    assert returned is review_ctx
    assert len(calls) == 1
    assert calls[0]["report_profile"] == REPORT_PROFILE_LIGHTWEIGHT
    assert calls[0]["run_context"] is review_ctx
    assert calls[0]["enable_report_timing"] is True
    sidecar = tmp_path / "Main portfolio" / "analysis_subject"
    assert sidecar_meets_minimum(sidecar, expected_portfolio_role="user_current_portfolio")
    assert analysis_subject_meets_minimum(tmp_path / "Main portfolio") is True


def test_run_materialize_analysis_subject_core_can_skip_review_context(
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

    def fail_if_prepare_review_run_context(*args, **kwargs):
        raise AssertionError("prepare_review_run_context must not run")

    def fake_run_portfolio_report_for_weights(*args, **kwargs):
        calls.append(kwargs)
        out = kwargs["output_dir_final"]
        (out / "run_metadata.json").write_text(
            json.dumps({"analysis_setup": {"analysis_subject": {"type": "current_portfolio"}}}),
            encoding="utf-8",
        )
        return {}, {"portfolio_valid": True}

    monkeypatch.setattr(
        run_report,
        "prepare_review_run_context",
        fail_if_prepare_review_run_context,
    )
    monkeypatch.setattr(
        run_report,
        "run_portfolio_report_for_weights",
        fake_run_portfolio_report_for_weights,
    )

    returned = run_report.run_materialize_analysis_subject_report(
        cfg,
        run_timestamp="2026-05-18T10:00:00",
        backtest_mode="dynamic_nan_safe",
        no_cache=True,
        review_mode="core",
        project_root=tmp_path,
        use_review_run_context=False,
    )

    assert returned is None
    assert len(calls) == 1
    assert calls[0]["report_profile"] == REPORT_PROFILE_LIGHTWEIGHT
    assert calls[0]["run_context"] is None
    assert calls[0]["enable_report_timing"] is False


def test_analysis_subject_lightweight_profile_still_allows_kalman_path() -> None:
    assert (
        run_report.should_skip_kalman_for_lightweight_run(
            lightweight=True,
            portfolio_role_override="analysis_subject",
            output_profile="site_api",
        )
        is False
    )
    assert (
        run_report.should_skip_kalman_for_lightweight_run(
            lightweight=True,
            portfolio_role_override="candidate",
            output_profile="lightweight_comparison",
        )
        is True
    )


def test_run_materialize_analysis_subject_full_uses_full_profile_without_context(
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
    prep_called = {"count": 0}

    def fake_prep(*args, **kwargs):
        prep_called["count"] += 1
        return MagicMock(spec=ReviewRunContext)

    def fake_run_portfolio_report_for_weights(*args, **kwargs):
        calls.append(kwargs)
        return {}, {}

    monkeypatch.setattr(run_report, "prepare_review_run_context", fake_prep)
    monkeypatch.setattr(
        run_report,
        "run_portfolio_report_for_weights",
        fake_run_portfolio_report_for_weights,
    )

    returned = run_report.run_materialize_analysis_subject_report(
        cfg,
        run_timestamp="2026-05-18T10:00:00",
        backtest_mode="dynamic_nan_safe",
        no_cache=False,
        review_mode="full",
        project_root=tmp_path,
    )

    assert returned is None
    assert prep_called["count"] == 0
    assert calls[0]["report_profile"] == REPORT_PROFILE_FULL
    assert calls[0]["run_context"] is None
    assert calls[0]["enable_report_timing"] is False
