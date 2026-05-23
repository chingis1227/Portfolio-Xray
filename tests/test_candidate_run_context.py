from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from src.candidate_run_context import (
    CandidateRunContext,
    FactoryFactorStressInputs,
    FactoryInvariantMetrics,
    SCHEMA_VERSION,
    build_factory_factor_stress_inputs,
    build_factory_invariant_metrics,
    daily_panel_for_candidate_report,
    extended_diagnostic_betas_for_candidate,
    invariant_metrics_usable_for_report,
    prepare_candidate_run_context,
    slice_asset_metrics_for_tickers,
    weekly_factor_frames_for_candidate,
)
import src.stress_factors as sf
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
        "src.candidate_run_context.build_factory_invariant_metrics",
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
        "src.candidate_run_context.build_factory_invariant_metrics",
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
            cash_returns_daily=panel.cash_returns.reindex(panel.monthly_returns.index).fillna(0),
            asset_betas_5y_universe=pd.DataFrame(),
            asset_betas_10y_universe=pd.DataFrame(),
            asset_betas_5y_extended_universe=pd.DataFrame(),
            asset_betas_10y_extended_universe=pd.DataFrame(),
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


def test_build_factory_invariant_metrics_precomputes_windows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tickers = ["VOO", "BND", "GLD"]
    panel = _monthly_panel(tickers, n_months=140)
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
    inv = build_factory_invariant_metrics(
        cfg=cfg,
        monthly_data=panel,
        local_benchmark_map={},
        report_tickers=tickers + ["BIL"],
    )
    assert inv is not None
    assert len(inv.asset_metrics_all) == 3
    assert all(len(rows) > 0 for rows in inv.asset_metrics_all)
    assert set(inv.correlation_by_window) == {36, 60, 120}
    assert not inv.stress_cov_base.empty
    assert set(inv.stress_cov_asset_cols) >= set(tickers)


def test_invariant_metrics_usable_for_subset_tickers() -> None:
    inv = FactoryInvariantMetrics(
        asset_metrics_all=([{"ticker": "VOO"}],),
        correlation_by_window={36: pd.DataFrame([[1.0]], index=["VOO"], columns=["VOO"])},
        stress_cov_base=pd.DataFrame([[1.0]], index=["VOO"], columns=["VOO"]),
        stress_cov_asset_cols=("VOO", "BND"),
        windows_months=(36,),
        universe_tickers=("VOO", "BND", "GLD"),
    )
    assert invariant_metrics_usable_for_report(inv, tickers=["VOO", "BND"], windows_months=[36])
    assert not invariant_metrics_usable_for_report(
        inv, tickers=["VOO", "XYZ"], windows_months=[36]
    )


def test_slice_asset_metrics_for_tickers_filters_rows() -> None:
    rows = (
        [{"ticker": "VOO", "cagr": 0.1}, {"ticker": "BND", "cagr": 0.05}],
        [{"ticker": "VOO", "cagr": 0.08}],
    )
    sliced = slice_asset_metrics_for_tickers(rows, ["VOO"])
    assert len(sliced[0]) == 1
    assert sliced[0][0]["ticker"] == "VOO"
    assert len(sliced[1]) == 1


def test_run_report_reuses_invariant_asset_metrics_and_corr(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from run_report import run_portfolio_report_for_weights
    from src.config import portfolio_total_tickers

    tickers = ["VOO", "BND", "GLD"]
    weights = {"VOO": 0.4, "BND": 0.4, "GLD": 0.2}
    panel = _monthly_panel(tickers + ["BIL"], n_months=140)
    asset_metric_calls: list[str] = []
    cov_calls: list[str] = []

    def counting_asset_metrics(*args, **kwargs):
        asset_metric_calls.append(str(args[0]))
        return {"ticker": args[0], "cagr": 0.1, "vol": 0.15, "sharpe": 1.0}

    monkeypatch.setattr(
        "run_report.asset_metrics_one_window",
        counting_asset_metrics,
    )
    monkeypatch.setattr(
        "src.stress.cov_matrix_monthly",
        lambda *a, **k: (cov_calls.append("cov") or pd.DataFrame()),
    )
    monkeypatch.setattr("run_report.load_monthly_data_shared", lambda **kwargs: panel)
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
    report_tickers = portfolio_total_tickers(cfg.tickers, weights, "BIL")
    inv = build_factory_invariant_metrics(
        cfg=cfg,
        monthly_data=panel,
        local_benchmark_map={},
        report_tickers=report_tickers,
    )
    assert inv is not None

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
        report_tickers=report_tickers,
        primary_window=120,
        invariant_metrics=inv,
    )

    run_portfolio_report_for_weights(
        cfg,
        weights,
        run_timestamp="2026-05-23T00:00:00Z",
        output_dir_csv=out_csv,
        output_dir_final=out_final,
        report_profile="lightweight_comparison",
        run_context=run_context,
    )
    assert asset_metric_calls == []
    assert cov_calls == []


def test_run_stress_reuses_shared_cov_base() -> None:
    from src.stress import run_stress

    tickers = ["VOO", "BND"]
    dates = pd.date_range("2015-01-31", periods=48, freq="ME")
    rng = np.random.default_rng(7)
    monthly_returns = pd.DataFrame(
        {t: rng.normal(0.004, 0.02, len(dates)) for t in tickers},
        index=dates,
    )
    asset_betas = pd.DataFrame(
        {"beta_eq": [0.9, 0.5], "beta_rates": [0.1, 0.2]},
        index=tickers,
    )
    shared_cov = monthly_returns.corr()
    weights = {"VOO": 0.6, "BND": 0.4}

    report_shared = run_stress(
        tickers=tickers,
        weights=weights,
        monthly_returns=monthly_returns,
        asset_betas=asset_betas,
        portfolio_betas={"beta_eq": 0.8},
        target_max_drawdown_pct=0.25,
        cov_base=shared_cov,
    )
    report_recompute = run_stress(
        tickers=tickers,
        weights=weights,
        monthly_returns=monthly_returns,
        asset_betas=asset_betas,
        portfolio_betas={"beta_eq": 0.8},
        target_max_drawdown_pct=0.25,
        cov_base=None,
    )
    assert report_shared.get("status") == report_recompute.get("status")
    scenarios_a = report_shared.get("stress_suite_results", {}).get("scenarios", [])
    scenarios_b = report_recompute.get("stress_suite_results", {}).get("scenarios", [])
    assert len(scenarios_a) == len(scenarios_b)
    for row_a, row_b in zip(scenarios_a, scenarios_b):
        assert row_a.get("scenario_id") == row_b.get("scenario_id")
        assert row_a.get("portfolio_pnl_pct") == pytest.approx(
            row_b.get("portfolio_pnl_pct"), rel=1e-9, abs=1e-9
        )
        assert row_a.get("top1_rc_pct") == pytest.approx(
            row_b.get("top1_rc_pct"), rel=1e-9, abs=1e-9
        )


def test_build_factory_factor_stress_inputs_precomputes_weekly_factor_frames(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    panel = _monthly_panel_from_cfg(cfg)
    daily_idx = pd.date_range("2018-01-02", periods=600, freq="B")
    daily = pd.DataFrame(
        {t: np.random.default_rng(7).normal(0.0005, 0.01, len(daily_idx)) for t in ["VOO", "BND"]},
        index=daily_idx,
    )
    weekly_factor_build_calls: list[str] = []
    episode_factor_build_calls: list[str] = []

    def weekly_factor_matrix(*args, **kwargs):
        weekly_factor_build_calls.append("weekly")
        idx = pd.date_range("2018-01-05", periods=300, freq="W-FRI")
        return pd.DataFrame(
            np.random.default_rng(8).normal(0.01, 0.02, (len(idx), len(sf.FACTOR_COLUMN_ORDER))),
            index=idx,
            columns=list(sf.FACTOR_COLUMN_ORDER),
        )

    monkeypatch.setattr(
        "src.candidate_run_context.load_daily_asset_returns_shared",
        lambda **kwargs: (daily, pd.Series(0.0, index=daily_idx)),
    )
    monkeypatch.setattr("src.stress_factors.build_factor_matrix", weekly_factor_matrix)
    def episode_factor_matrix(*_args, **_kwargs):
        episode_factor_build_calls.append("episode")
        return pd.DataFrame()

    monkeypatch.setattr("src.candidate_run_context.build_factor_matrix", episode_factor_matrix)
    monkeypatch.setattr(
        "src.candidate_run_context.compute_asset_factor_betas_from_daily_returns",
        lambda *a, **k: pd.DataFrame({"beta_eq": [0.7]}, index=["VOO"]),
    )
    result = build_factory_factor_stress_inputs(
        cfg=cfg,
        monthly_data=panel,
        assets_meta={},
        cash_proxy_ticker="BIL",
        local_benchmark_map={},
        report_tickers=["VOO", "BND"],
    )
    assert result is not None
    assert result.weekly_factor_frames is not None
    assert not result.weekly_factor_frames.asset_weekly.empty
    assert weekly_factor_build_calls == ["weekly"]
    assert len(episode_factor_build_calls) == 2
    assert weekly_factor_frames_for_candidate(result, tickers=["VOO", "BND"]) is not None
    assert weekly_factor_frames_for_candidate(result, tickers=["VOO", "MISSING"]) is None


def test_portfolio_factor_regression_reuses_shared_frames(monkeypatch: pytest.MonkeyPatch) -> None:
    idx = pd.date_range("2020-01-03", periods=120, freq="W-FRI")
    rng = np.random.default_rng(99)
    factors = pd.DataFrame(
        rng.normal(scale=0.02, size=(len(idx), len(sf.BASE_FACTOR_COLUMN_ORDER))),
        index=idx,
        columns=list(sf.BASE_FACTOR_COLUMN_ORDER),
    )
    asset_weekly = pd.DataFrame(
        {"AAA": 0.5 * factors["equity"] + rng.normal(scale=0.01, size=len(idx))},
        index=idx,
    )
    frames = sf.PortfolioFactorWeeklyFrames(
        asset_weekly=asset_weekly,
        factors=factors,
        analysis_end_str="2022-06-24",
        buffer_weeks=sf.FACTOR_DOWNLOAD_BUFFER_WEEKS,
        universe_tickers=("AAA",),
    )

    def fail_download(*_args, **_kwargs):
        raise AssertionError("download_all should not run when shared_frames are provided")

    import src.data_yf as data_yf

    monkeypatch.setattr(data_yf, "download_all", fail_download)
    monkeypatch.setattr(sf, "build_factor_matrix", fail_download)

    out = sf.portfolio_factor_regression_weekly(
        weights={"AAA": 1.0},
        tickers=["AAA"],
        analysis_end_str="2022-06-24",
        window_weeks=60,
        shared_frames=frames,
    )
    assert out.get("betas")
    assert out.get("n_obs", 0) >= 10


def test_build_factory_factor_stress_inputs_precomputes_extended_betas(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    panel = _monthly_panel_from_cfg(cfg)
    daily = panel.monthly_returns / 4.0
    extended_calls: list[str] = []

    def track_extended(*args, **kwargs):
        if kwargs.get("factor_columns") is not None:
            window_weeks = kwargs.get("window_weeks", args[2] if len(args) > 2 else None)
            extended_calls.append(str(window_weeks))
        return pd.DataFrame({"beta_eq": [0.7, 0.4]}, index=["VOO", "BND"])

    monkeypatch.setattr(
        "src.candidate_run_context.load_daily_asset_returns_shared",
        lambda **kwargs: (daily, panel.cash_returns.reindex(daily.index).fillna(0)),
    )
    monkeypatch.setattr(
        "src.candidate_run_context.compute_asset_factor_betas_from_daily_returns",
        track_extended,
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
        report_tickers=["VOO", "BND"],
    )
    assert result is not None
    assert not result.asset_betas_5y_extended_universe.empty
    assert not result.asset_betas_10y_extended_universe.empty
    assert extended_calls == ["260", "520"]


def test_extended_diagnostic_betas_for_candidate_slices_universe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    extended_calls: list[str] = []

    def fail_compute(*args, **kwargs):
        extended_calls.append("compute")
        return pd.DataFrame()

    monkeypatch.setattr(
        "src.candidate_run_context.compute_asset_factor_betas_from_daily_returns",
        fail_compute,
    )
    factory = FactoryFactorStressInputs(
        daily_asset_returns_for_betas=pd.DataFrame(),
        cash_returns_daily=pd.Series(dtype=float),
        asset_betas_5y_universe=pd.DataFrame(),
        asset_betas_10y_universe=pd.DataFrame(),
        asset_betas_5y_extended_universe=pd.DataFrame(
            {"beta_eq": [0.9, 0.5]}, index=["VOO", "BND"]
        ),
        asset_betas_10y_extended_universe=pd.DataFrame(
            {"beta_eq": [0.85, 0.45]}, index=["VOO", "BND"]
        ),
        recession_factor_returns=pd.DataFrame(),
        scenario_episode_factor_returns=pd.DataFrame(),
        beta_source="cached_daily_returns_weekly_ols",
    )
    b5, b10 = extended_diagnostic_betas_for_candidate(
        factory,
        weights={"VOO": 0.6, "BND": 0.4},
        beta_tickers=["VOO", "BND"],
        benchmark_base_ticker="VOO",
        analysis_end_str="2024-12-31",
    )
    assert extended_calls == []
    assert b5.get("beta_eq") == pytest.approx(0.6 * 0.9 + 0.4 * 0.5)
    assert b10.get("beta_eq") == pytest.approx(0.6 * 0.85 + 0.4 * 0.45)


def test_daily_panel_for_candidate_report_slices_factory_panel() -> None:
    idx = pd.date_range("2020-01-01", periods=5, freq="D")
    daily = pd.DataFrame(
        {"VOO": [0.01] * 5, "BND": [0.005] * 5, "BIL": [0.0] * 5},
        index=idx,
    )
    cash = pd.Series([0.0] * 5, index=idx)
    factory = FactoryFactorStressInputs(
        daily_asset_returns_for_betas=daily,
        cash_returns_daily=cash,
        asset_betas_5y_universe=pd.DataFrame(),
        asset_betas_10y_universe=pd.DataFrame(),
        asset_betas_5y_extended_universe=pd.DataFrame(),
        asset_betas_10y_extended_universe=pd.DataFrame(),
        recession_factor_returns=pd.DataFrame(),
        scenario_episode_factor_returns=pd.DataFrame(),
        beta_source=None,
    )
    panel = daily_panel_for_candidate_report(
        factory, tickers=["VOO", "BND"], cash_proxy_ticker="BIL"
    )
    assert panel is not None
    sub, sub_cash = panel
    assert list(sub.columns) == ["VOO", "BND", "BIL"]
    assert len(sub_cash) == len(sub)


def test_run_report_reuses_factory_daily_panel_for_tail_risk(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from run_report import run_portfolio_report_for_weights

    tickers = ["VOO", "BND", "GLD"]
    panel = _monthly_panel(tickers)
    daily_load_calls: list[str] = []

    def counting_daily_load(**kwargs):
        daily_load_calls.append("daily")
        return panel.monthly_returns / 4.0, panel.cash_returns.reindex(
            panel.monthly_returns.index
        ).fillna(0)

    monkeypatch.setattr("run_report.load_daily_asset_returns_shared", counting_daily_load)
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
    report_tickers = tickers + ["BIL"]
    daily_panel = panel.monthly_returns / 4.0
    run_context = CandidateRunContext(
        cfg=cfg,
        project_root=tmp_path,
        monthly_data=panel,
        assets_meta={},
        cash_proxy_ticker="BIL",
        rf_source="FRED:DTB3",
        local_benchmark_map={},
        report_tickers=report_tickers,
        primary_window=120,
        factor_stress=FactoryFactorStressInputs(
            daily_asset_returns_for_betas=daily_panel.reindex(
                columns=[c for c in report_tickers if c in daily_panel.columns]
            ),
            cash_returns_daily=panel.cash_returns.reindex(daily_panel.index).fillna(0),
            asset_betas_5y_universe=pd.DataFrame({"beta_eq": [0.8]}, index=["VOO"]),
            asset_betas_10y_universe=pd.DataFrame({"beta_eq": [0.75]}, index=["VOO"]),
            asset_betas_5y_extended_universe=pd.DataFrame(),
            asset_betas_10y_extended_universe=pd.DataFrame(),
            recession_factor_returns=pd.DataFrame(),
            scenario_episode_factor_returns=pd.DataFrame(),
            beta_source="cached_daily_returns_weekly_ols",
        ),
    )
    out_csv = tmp_path / "results_csv"
    out_final = tmp_path / "out"
    out_csv.mkdir(parents=True)
    out_final.mkdir(parents=True)

    run_portfolio_report_for_weights(
        cfg,
        weights,
        run_timestamp="2026-05-23T00:00:00Z",
        output_dir_csv=out_csv,
        output_dir_final=out_final,
        report_profile="lightweight_comparison",
        run_context=run_context,
    )
    assert daily_load_calls == []


def test_lightweight_skips_save_inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from run_report import run_portfolio_report_for_weights

    tickers = ["VOO", "BND"]
    panel = _monthly_panel(tickers)
    save_calls: list[str] = []

    monkeypatch.setattr(
        "run_report.save_inputs",
        lambda *a, **k: save_calls.append("save"),
    )
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
    out_csv = tmp_path / "results_csv"
    out_final = tmp_path / "out"
    out_csv.mkdir(parents=True)
    out_final.mkdir(parents=True)

    run_portfolio_report_for_weights(
        cfg,
        {"VOO": 0.5, "BND": 0.5},
        run_timestamp="2026-05-23T00:00:00Z",
        output_dir_csv=out_csv,
        output_dir_final=out_final,
        report_profile="lightweight_comparison",
        run_context=CandidateRunContext(
            cfg=cfg,
            project_root=tmp_path,
            monthly_data=panel,
            assets_meta={},
            cash_proxy_ticker="BIL",
            rf_source="FRED:DTB3",
            local_benchmark_map={},
            report_tickers=tickers,
            primary_window=120,
        ),
    )
    assert save_calls == []
    assert not (out_csv / "inputs").exists()


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


def test_prepare_candidate_run_context_schema_v4() -> None:
    assert SCHEMA_VERSION == "candidate_run_context_v5"


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
