from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from src.candidate_run_context import (
    CandidateRunContext,
    FactoryFactorStressInputs,
    build_factory_factor_stress_inputs,
    prepare_candidate_run_context,
)
from src.config_schema import validate_config
from src.data_loader import MonthlyDataResult


def _monthly_panel(tickers: list[str], n_months: int = 130) -> MonthlyDataResult:
    rng = np.random.default_rng(42)
    dates = pd.date_range("2015-01-31", periods=n_months, freq="ME")
    monthly_returns = pd.DataFrame(
        {t: rng.normal(0.004, 0.02, size=n_months) for t in tickers},
        index=dates,
    )
    end = dates[-1]
    return MonthlyDataResult(
        monthly_prices=(1 + monthly_returns).cumprod() * 100.0,
        monthly_returns=monthly_returns,
        monthly_log_returns=np.log1p(monthly_returns),
        rf_monthly=pd.Series(0.001, index=dates),
        benchmark_returns=pd.Series(rng.normal(0.005, 0.018, size=n_months), index=dates),
        cash_returns=pd.Series(0.0, index=dates),
        fx_series_used={},
        analysis_end=end,
        analysis_end_str=end.strftime("%Y-%m-%d"),
        daily_cache_key="test_daily",
        monthly_cache_key="test_monthly",
    )


def _install_report_mocks(monkeypatch: pytest.MonkeyPatch, panel: MonthlyDataResult) -> None:
    daily_idx = panel.monthly_returns.index
    daily_returns = panel.monthly_returns / 4.0

    monkeypatch.setattr(
        "run_report.load_daily_asset_returns_shared",
        lambda **kwargs: (daily_returns, panel.cash_returns.reindex(daily_idx).fillna(0)),
    )
    monkeypatch.setattr(
        "run_report.run_stress",
        lambda **kwargs: {
            "status": "DIAG_PASS",
            "analysis_end": panel.analysis_end_str,
            "stress_suite_results": {"overall": "DIAG_PASS", "scenarios": []},
            "factor_betas_5y": {"beta_eq": 0.85},
            "factor_betas_10y": {"beta_eq": 0.82},
            "factor_betas": {"beta_eq": 0.85},
        },
    )
    monkeypatch.setattr(
        "run_report.portfolio_factor_regression_weekly",
        lambda **kwargs: {"betas": {"beta_eq": 0.85}, "r_squared": 0.4, "n_obs": 200},
    )
    monkeypatch.setattr(
        "run_report.compute_asset_factor_betas_weekly",
        lambda *args, **kwargs: pd.DataFrame({"beta_eq": [0.8]}, index=["VOO"]),
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


def test_prepare_candidate_run_context_resolves_robust_mv_lambda(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression: prepare must pass cli_lambda=None (Session 9 smoke blocker)."""
    panel = MagicMock()
    panel.monthly_returns = pd.DataFrame()
    panel.analysis_end_str = "2024-12-31"
    panel.analysis_end = pd.Timestamp("2024-12-31")
    lambda_calls: list[float | None] = []

    def capture_lambda(**kwargs):
        lambda_calls.append(kwargs.get("cli_lambda"))
        return (None, "none")

    monkeypatch.setattr(
        "src.candidate_run_context.load_monthly_data_shared",
        lambda **kwargs: panel,
    )
    monkeypatch.setattr(
        "src.candidate_run_context.build_factory_factor_stress_inputs",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        "src.candidate_run_context.resolve_robust_mv_lambda_for_baseline",
        capture_lambda,
    )
    monkeypatch.setattr("src.candidate_run_context.load_assets_metadata", lambda: {})
    monkeypatch.setattr(
        "src.candidate_run_context.resolve_cash_and_rf",
        lambda cfg: ("BIL", "FRED:DTB3"),
    )
    monkeypatch.setattr(
        "src.candidate_run_context.resolve_local_benchmarks",
        lambda *a, **k: {},
    )
    monkeypatch.setattr(
        "src.candidate_run_context.portfolio_total_tickers",
        lambda *a, **k: ["VOO"],
    )
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO"],
        }
    )
    prepare_candidate_run_context(cfg, project_root=Path("."), preload_factor_stress=False)
    assert lambda_calls == [None]


def test_prepare_candidate_run_context_loads_monthly_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    load_calls: list[str] = []
    panel = MagicMock()
    panel.monthly_returns = pd.DataFrame()
    panel.analysis_end_str = "2024-12-31"
    panel.analysis_end = pd.Timestamp("2024-12-31")

    monkeypatch.setattr(
        "src.candidate_run_context.load_monthly_data_shared",
        lambda **kwargs: (load_calls.append("monthly") or panel),
    )
    monkeypatch.setattr(
        "src.candidate_run_context.build_factory_factor_stress_inputs",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        "src.candidate_run_context.resolve_robust_mv_lambda_for_baseline",
        lambda **kwargs: (0.5, "file"),
    )
    monkeypatch.setattr(
        "src.candidate_run_context.load_assets_metadata",
        lambda: {},
    )
    monkeypatch.setattr(
        "src.candidate_run_context.resolve_cash_and_rf",
        lambda cfg: ("BIL", "FRED:DTB3"),
    )
    monkeypatch.setattr(
        "src.candidate_run_context.resolve_local_benchmarks",
        lambda *a, **k: {},
    )
    monkeypatch.setattr(
        "src.candidate_run_context.portfolio_total_tickers",
        lambda *a, **k: ["VOO", "BND"],
    )

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    ctx = prepare_candidate_run_context(cfg, project_root=Path("."), preload_factor_stress=False)
    assert load_calls == ["monthly"]
    assert ctx.analysis_end_str == "2024-12-31"
    assert ctx.monthly_returns is panel.monthly_returns


def test_run_report_skips_monthly_reload_with_run_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from run_report import run_portfolio_report_for_weights

    tickers = ["VOO", "BND", "GLD"]
    panel = _monthly_panel(tickers)
    load_calls: list[str] = []

    def guarded_load(**kwargs):
        load_calls.append("monthly")
        return panel

    monkeypatch.setattr("run_report.load_monthly_data_shared", guarded_load)
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
    weights = {"VOO": 0.4, "BND": 0.4, "GLD": 0.2}
    out_csv = tmp_path / "results_csv"
    out_final = tmp_path / "out"
    out_csv.mkdir(parents=True)
    out_final.mkdir(parents=True)

    run_context = CandidateRunContext(
        cfg=cfg,
        project_root=tmp_path,
        monthly_data=panel,
        assets_meta={},
        cash_proxy_ticker="BIL",
        rf_source="FRED:DTB3",
        local_benchmark_map={},
        report_tickers=tickers,
        primary_window=120,
        factor_stress=FactoryFactorStressInputs(
            daily_asset_returns_for_betas=panel.monthly_returns / 4.0,
            asset_betas_5y_universe=pd.DataFrame(),
            asset_betas_10y_universe=pd.DataFrame(),
            recession_factor_returns=pd.DataFrame(),
            scenario_episode_factor_returns=pd.DataFrame(),
            beta_source=None,
        ),
    )

    run_portfolio_report_for_weights(
        cfg,
        weights,
        run_timestamp="2026-05-22T00:00:00Z",
        output_dir_csv=out_csv,
        output_dir_final=out_final,
        report_profile="lightweight_comparison",
        run_context=run_context,
    )
    assert load_calls == []


def test_build_factory_factor_stress_inputs_when_daily_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO"],
        }
    )
    panel = _monthly_panel_from_cfg(cfg)
    monkeypatch.setattr(
        "src.candidate_run_context.load_daily_asset_returns_shared",
        lambda **kwargs: (pd.DataFrame(), pd.Series(dtype=float)),
    )
    monkeypatch.setattr(
        "src.candidate_run_context.build_factor_matrix",
        lambda *a, **k: pd.DataFrame(),
    )
    result = build_factory_factor_stress_inputs(
        cfg=cfg,
        monthly_data=panel,
        assets_meta={},
        cash_proxy_ticker="BIL",
        local_benchmark_map={},
        report_tickers=["VOO"],
    )
    assert result is not None
    assert result.daily_asset_returns_for_betas.empty
    assert "cached_daily_returns_empty" in result.beta_setup_reasons


def _monthly_panel_from_cfg(cfg: object) -> object:
    from src.data_loader import MonthlyDataResult
    import numpy as np

    tickers = list(cfg.tickers)  # type: ignore[attr-defined]
    dates = pd.date_range("2015-01-31", periods=80, freq="ME")
    rng = np.random.default_rng(1)
    monthly_returns = pd.DataFrame(
        {t: rng.normal(0.005, 0.02, len(dates)) for t in tickers},
        index=dates,
    )
    end = dates[-1]
    return MonthlyDataResult(
        monthly_prices=(1 + monthly_returns).cumprod() * 100,
        monthly_returns=monthly_returns,
        monthly_log_returns=np.log1p(monthly_returns),
        rf_monthly=pd.Series(0.001, index=dates),
        benchmark_returns=pd.Series(rng.normal(0.005, 0.018, len(dates)), index=dates),
        cash_returns=pd.Series(0.0, index=dates),
        fx_series_used={},
        analysis_end=end,
        analysis_end_str=end.strftime("%Y-%m-%d"),
        daily_cache_key="d",
        monthly_cache_key="m",
    )
