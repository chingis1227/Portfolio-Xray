from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from run_report import run_portfolio_report_for_weights
from src.candidate_comparison import _evaluate_artifact_candidate, _metric_fields_from_snapshot
from src.config_schema import validate_config
from src.data_loader import MonthlyDataResult
from src.report_profile import (
    REPORT_PROFILE_FULL,
    REPORT_PROFILE_LIGHTWEIGHT,
    normalize_report_profile,
)


def test_normalize_report_profile_defaults_to_full() -> None:
    assert normalize_report_profile(None) == REPORT_PROFILE_FULL
    assert normalize_report_profile("lightweight_comparison") == REPORT_PROFILE_LIGHTWEIGHT


def test_normalize_report_profile_rejects_unknown() -> None:
    with pytest.raises(ValueError, match="Invalid report_profile"):
        normalize_report_profile("turbo")


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
    }


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


def _install_report_mocks(monkeypatch: pytest.MonkeyPatch, panel: MonthlyDataResult) -> None:
    daily_idx = panel.monthly_returns.index
    daily_returns = panel.monthly_returns / 4.0

    monkeypatch.setattr(
        "run_report.load_monthly_data_shared",
        lambda **kwargs: panel,
    )
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
        lambda *args, **kwargs: pd.DataFrame(
            {"beta_eq": [0.8, 0.7]},
            index=["VOO", "BND"],
        ),
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


def test_snapshot_metrics_match_full_and_lightweight_profiles(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    report_cfg: object,
    report_weights: dict[str, float],
) -> None:
    tickers = list(report_weights)
    panel = _monthly_panel(tickers)
    _install_report_mocks(monkeypatch, panel)

    metrics_by_profile: dict[str, dict] = {}
    for profile in (REPORT_PROFILE_FULL, REPORT_PROFILE_LIGHTWEIGHT):
        out = tmp_path / profile
        csv_dir = out / "results_csv"
        csv_dir.mkdir(parents=True)
        run_portfolio_report_for_weights(
            report_cfg,
            report_weights,
            run_timestamp="2026-05-22T12:00:00+00:00",
            output_dir_csv=csv_dir,
            output_dir_final=out,
            no_cache=True,
            report_profile=profile,
        )
        snap = json.loads((out / "snapshot_10y.json").read_text(encoding="utf-8"))
        metrics_by_profile[profile] = _metric_fields_from_snapshot(snap["metrics"])

    assert metrics_by_profile[REPORT_PROFILE_FULL] == metrics_by_profile[REPORT_PROFILE_LIGHTWEIGHT]
    assert (tmp_path / REPORT_PROFILE_LIGHTWEIGHT / "stress_report.json").is_file()
    assert not (tmp_path / REPORT_PROFILE_LIGHTWEIGHT / "report.html").is_file()
    assert not (tmp_path / REPORT_PROFILE_LIGHTWEIGHT / "commentary.txt").is_file()


def test_lightweight_artifacts_yield_available_comparison_row(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    report_cfg: object,
    report_weights: dict[str, float],
) -> None:
    tickers = list(report_weights)
    panel = _monthly_panel(tickers)
    _install_report_mocks(monkeypatch, panel)
    out = tmp_path / "equal-weight portfolio"
    csv_dir = out / "results_csv"
    csv_dir.mkdir(parents=True)
    run_portfolio_report_for_weights(
        report_cfg,
        report_weights,
        run_timestamp="2026-05-22T12:00:00+00:00",
        output_dir_csv=csv_dir,
        output_dir_final=out,
        no_cache=True,
        report_profile=REPORT_PROFILE_LIGHTWEIGHT,
    )
    status, reason, _, missing, _ = _evaluate_artifact_candidate(
        out,
        candidate_id="equal_weight",
        expected_analysis_end=panel.analysis_end_str,
        expected_config_fingerprint=None,
    )
    assert status == "available"
    assert reason is None
    assert "stress.overall" not in missing
