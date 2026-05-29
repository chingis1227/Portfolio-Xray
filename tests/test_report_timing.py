"""Per-block report timing instrumentation (Session 1 shared evidence)."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from run_report import run_portfolio_report_for_weights
from src.candidate_factory import run_candidate_factory
from src.config_schema import validate_config
from src.data_loader import MonthlyDataResult
from src.report_timing import (
    ENV_PORTFOLIO_REPORT_TIMING,
    REPORT_TIMING_BLOCK_KEYS,
    aggregate_report_timing_from_steps,
    portfolio_report_timing_enabled,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_run_report_timing_blocks_registered_in_module() -> None:
    """Every report_timing.block name in run_report.py must be in REPORT_TIMING_BLOCK_KEYS."""
    run_report_text = (REPO_ROOT / "run_report.py").read_text(encoding="utf-8")
    used = set(re.findall(r'report_timing\.block\("([^"]+)"\)', run_report_text))
    assert used, "expected at least one report_timing.block(...) in run_report.py"
    missing = sorted(used - set(REPORT_TIMING_BLOCK_KEYS))
    assert not missing, (
        "report_timing blocks used in run_report.py but missing from "
        f"REPORT_TIMING_BLOCK_KEYS: {missing}"
    )


def _monthly_panel(tickers: list[str], n_months: int = 130) -> MonthlyDataResult:
    rng = np.random.default_rng(42)
    dates = pd.date_range("2015-01-31", periods=n_months, freq="ME")
    monthly_returns = pd.DataFrame(
        {t: rng.normal(0.004, 0.02, size=n_months) for t in tickers},
        index=dates,
    )
    monthly_log_returns = np.log1p(monthly_returns)
    monthly_prices = (1 + monthly_returns).cumprod() * 100.0
    rf = pd.Series(0.001, index=dates)
    bench = pd.Series(rng.normal(0.005, 0.018, size=n_months), index=dates)
    cash = pd.Series(0.0, index=dates)
    end = dates[-1]
    return MonthlyDataResult(
        monthly_prices=monthly_prices,
        monthly_returns=monthly_returns,
        monthly_log_returns=monthly_log_returns,
        rf_monthly=rf,
        benchmark_returns=bench,
        cash_returns=cash,
        fx_series_used={},
        analysis_end=end,
        analysis_end_str=end.strftime("%Y-%m-%d"),
        daily_cache_key="test_daily",
        monthly_cache_key="test_monthly",
    )


def _minimal_stress_report(analysis_end: str) -> dict:
    return {
        "status": "DIAG_PASS",
        "fail_reason_code": None,
        "failed_scenario": None,
        "analysis_end": analysis_end,
        "stress_suite_results": {
            "overall": "DIAG_PASS",
            "fail_reason_code": None,
            "failed_scenario": None,
            "scenarios": [
                {"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.05, "pass": True}
            ],
        },
        "factor_betas_5y": {"beta_eq": 0.85},
        "factor_betas_10y": {"beta_eq": 0.82},
        "factor_betas": {"beta_eq": 0.85},
        "factor_regression_5y": {"betas": {"beta_eq": 0.85}, "r_squared": 0.4},
        "factor_regression_10y": {"betas": {"beta_eq": 0.82}, "r_squared": 0.38},
        "historical_results": [],
        "scenario_results": [],
    }


def _install_report_mocks(monkeypatch: pytest.MonkeyPatch, panel: MonthlyDataResult) -> None:
    daily_idx = panel.monthly_returns.index
    daily_returns = panel.monthly_returns / 4.0

    monkeypatch.setattr("run_report.load_monthly_data_shared", lambda **kwargs: panel)
    monkeypatch.setattr(
        "run_report.load_daily_asset_returns_shared",
        lambda **kwargs: (daily_returns, panel.cash_returns.reindex(daily_idx).fillna(0)),
    )
    monkeypatch.setattr(
        "run_report.run_stress",
        lambda **kwargs: _minimal_stress_report(panel.analysis_end_str),
    )
    monkeypatch.setattr(
        "run_report.portfolio_factor_regression_weekly",
        lambda **kwargs: {"betas": {"beta_eq": 0.85}, "r_squared": 0.4, "n_obs": 200},
    )
    monkeypatch.setattr(
        "run_report.compute_asset_factor_betas_weekly",
        lambda *args, **kwargs: pd.DataFrame({"beta_eq": [0.8, 0.7]}, index=["VOO", "BND"]),
    )
    monkeypatch.setattr(
        "run_report.compute_asset_factor_betas_from_daily_returns",
        lambda *args, **kwargs: pd.DataFrame(),
    )
    monkeypatch.setattr(
        "run_report.build_scenario_library",
        lambda **kwargs: {"version": "test", "scenarios": [], "n_scenarios": 0},
    )
    monkeypatch.setattr(
        "run_report.build_scenario_library_normalized",
        lambda **kwargs: {"version": "test", "scenarios": [], "n_scenarios": 0},
    )
    monkeypatch.setattr(
        "run_report.macro_regime_diagnostics",
        lambda **kwargs: {"labels_monthly": [{"date": "2020-01-31", "regime": "expansion"}]},
    )
    monkeypatch.setattr(
        "run_report.factor_covariance_analytics",
        lambda **kwargs: {"factor_order": [], "base": {"matrix": {}}},
    )
    monkeypatch.setattr(
        "run_report.factor_variance_decomposition_weekly",
        lambda **kwargs: {"status": "unavailable", "rows": []},
    )
    monkeypatch.setattr(
        "run_report.portfolio_pca_diagnostics",
        lambda **kwargs: {"raw": {"status": "unavailable"}},
    )
    monkeypatch.setattr(
        "run_report.factor_oos_beta_shock_explainability",
        lambda **kwargs: {},
    )
    monkeypatch.setattr(
        "run_report.build_factor_beta_diagnostic_overlay",
        lambda **kwargs: {"historical_results_adjusted": []},
    )
    monkeypatch.setattr(
        "run_report.build_stress_scenario_analytics",
        lambda **kwargs: {},
    )


@pytest.fixture
def report_cfg() -> object:
    return validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND", "GLD"],
            "windows_months": [36, 60, 120],
            "cash_proxy_ticker": "BIL",
        }
    )


@pytest.fixture
def report_weights() -> dict[str, float]:
    return {"VOO": 0.4, "BND": 0.4, "GLD": 0.2}


def test_portfolio_report_timing_disabled_by_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    report_cfg: object,
    report_weights: dict[str, float],
) -> None:
    monkeypatch.delenv(ENV_PORTFOLIO_REPORT_TIMING, raising=False)
    panel = _monthly_panel(list(report_weights))
    _install_report_mocks(monkeypatch, panel)
    out = tmp_path / "out"
    csv_dir = out / "results_csv"
    csv_dir.mkdir(parents=True)
    _, meta = run_portfolio_report_for_weights(
        report_cfg,
        report_weights,
        run_timestamp="2026-05-23T12:00:00+00:00",
        output_dir_csv=csv_dir,
        output_dir_final=out,
        no_cache=True,
        report_profile="lightweight_comparison",
        enable_report_timing=False,
    )
    assert "report_timing" not in meta


def test_portfolio_report_timing_present_when_enabled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    report_cfg: object,
    report_weights: dict[str, float],
) -> None:
    monkeypatch.delenv(ENV_PORTFOLIO_REPORT_TIMING, raising=False)
    panel = _monthly_panel(list(report_weights))
    _install_report_mocks(monkeypatch, panel)
    out = tmp_path / "out"
    csv_dir = out / "results_csv"
    csv_dir.mkdir(parents=True)
    _, meta = run_portfolio_report_for_weights(
        report_cfg,
        report_weights,
        run_timestamp="2026-05-23T12:00:00+00:00",
        output_dir_csv=csv_dir,
        output_dir_final=out,
        no_cache=True,
        report_profile="lightweight_comparison",
        enable_report_timing=True,
    )
    timing = meta.get("report_timing")
    assert isinstance(timing, dict)
    assert timing
    for key in timing:
        assert key in REPORT_TIMING_BLOCK_KEYS
        assert isinstance(timing[key], (int, float))
        assert timing[key] >= 0


def test_portfolio_report_timing_env_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    report_cfg: object,
    report_weights: dict[str, float],
) -> None:
    assert not portfolio_report_timing_enabled(enable_report_timing=None)
    monkeypatch.setenv(ENV_PORTFOLIO_REPORT_TIMING, "1")
    assert portfolio_report_timing_enabled(enable_report_timing=None)
    panel = _monthly_panel(list(report_weights))
    _install_report_mocks(monkeypatch, panel)
    out = tmp_path / "out"
    csv_dir = out / "results_csv"
    csv_dir.mkdir(parents=True)
    _, meta = run_portfolio_report_for_weights(
        report_cfg,
        report_weights,
        run_timestamp="2026-05-23T12:00:00+00:00",
        output_dir_csv=csv_dir,
        output_dir_final=out,
        no_cache=True,
        report_profile="lightweight_comparison",
    )
    assert isinstance(meta.get("report_timing"), dict)


def test_factory_aggregates_report_timing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.candidate_run_context import CandidateRunContext

    tickers = ["VOO", "BND", "GLD"]
    panel = _monthly_panel(tickers)
    _install_report_mocks(monkeypatch, panel)

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": tickers,
            "windows_months": [36, 60, 120],
            "cash_proxy_ticker": "BIL",
        }
    )
    context = CandidateRunContext(
        cfg=cfg,
        project_root=tmp_path,
        monthly_data=panel,
        assets_meta={},
        cash_proxy_ticker="BIL",
        rf_source="FRED:DTB3",
        local_benchmark_map={},
        report_tickers=tickers,
        primary_window=len(panel.monthly_returns),
    )
    monkeypatch.setattr(
        "src.candidate_factory.prepare_candidate_run_context",
        lambda cfg, project_root, no_cache=False: context,
    )

    doc = run_candidate_factory(
        cfg,
        project_root=tmp_path,
        explicit_candidates=["equal_weight", "risk_parity"],
        skip_existing=False,
        execution_mode="standard",
        runner=lambda cmd, cwd: pytest.fail("subprocess should not run"),
    )
    timed_steps = [s for s in doc["steps"] if s.get("report_timing")]
    assert len(timed_steps) == 2
    agg = doc["timing_summary"].get("report_timing_aggregate")
    assert isinstance(agg, dict)
    assert agg.get("candidates_with_report_timing") == 2
    totals = agg.get("report_blocks_seconds_total") or {}
    assert isinstance(totals, dict)
    assert totals
