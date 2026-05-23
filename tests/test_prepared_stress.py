from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.stress import (
    SCENARIOS,
    _scenario_return_per_asset,
    build_prepared_synthetic_stress_inputs,
    prepared_synthetic_stress_usable,
    run_stress,
)


def _sample_stress_inputs() -> tuple[list[str], pd.DataFrame, pd.DataFrame, dict[str, float]]:
    tickers = ["VOO", "BND", "BIL"]
    dates = pd.date_range("2015-01-31", periods=48, freq="ME")
    rng = np.random.default_rng(11)
    monthly_returns = pd.DataFrame(
        {t: rng.normal(0.004, 0.02, len(dates)) for t in tickers},
        index=dates,
    )
    asset_betas = pd.DataFrame(
        {
            "beta_eq": [0.95, 0.45, 0.0],
            "beta_rr": [0.05, 0.15, 0.0],
            "beta_credit": [0.02, 0.25, 0.0],
            "beta_inf": [0.01, 0.05, 0.0],
            "beta_usd": [0.0, 0.02, 0.0],
            "beta_cmd": [0.03, 0.04, 0.0],
        },
        index=tickers,
    )
    weights = {"VOO": 0.55, "BND": 0.35, "BIL": 0.10}
    return tickers, monthly_returns, asset_betas, weights


def test_build_prepared_synthetic_matches_scenario_return_per_asset() -> None:
    tickers, _, asset_betas, _ = _sample_stress_inputs()
    cov_base = asset_betas[["beta_eq"]].copy()  # placeholder shape
    cov_base = pd.DataFrame(
        np.outer([0.02, 0.015, 0.001], [0.02, 0.015, 0.001]) * np.eye(3) * 12,
        index=tickers,
        columns=tickers,
    )
    prepared = build_prepared_synthetic_stress_inputs(
        asset_cols=tickers,
        asset_betas=asset_betas,
        cov_base=cov_base,
        cash_proxy_ticker="BIL",
    )
    assert prepared is not None
    assert set(prepared.r_asset_by_scenario.keys()) == set(SCENARIOS.keys())
    for scenario_id, params in SCENARIOS.items():
        shock = {
            k: v
            for k, v in params.items()
            if k.startswith("shock_") and isinstance(v, (int, float))
        }
        expected = _scenario_return_per_asset(shock, asset_betas, tickers).reindex(tickers).fillna(0)
        got = prepared.r_asset_by_scenario[scenario_id]
        pd.testing.assert_series_equal(got, expected, check_names=False)


def test_prepared_synthetic_stress_usable_requires_cov_method_match() -> None:
    tickers, _, asset_betas, _ = _sample_stress_inputs()
    cov_base = pd.DataFrame(np.eye(3) * 0.0004, index=tickers, columns=tickers)
    prepared = build_prepared_synthetic_stress_inputs(
        asset_cols=tickers,
        asset_betas=asset_betas,
        cov_base=cov_base,
        stress_cov_method="taxonomy_blend_v1",
    )
    assert prepared is not None
    assert prepared_synthetic_stress_usable(prepared, asset_cols=tickers)
    assert not prepared_synthetic_stress_usable(
        prepared,
        asset_cols=tickers,
        stress_cov_method="uniform_legacy",
    )
    assert not prepared_synthetic_stress_usable(prepared, asset_cols=["VOO", "MISSING"])


def test_run_stress_prepared_synthetic_parity() -> None:
    tickers, monthly_returns, asset_betas, weights = _sample_stress_inputs()
    cov_base = monthly_returns[tickers].cov()
    prepared = build_prepared_synthetic_stress_inputs(
        asset_cols=tickers,
        asset_betas=asset_betas,
        cov_base=cov_base,
        cash_proxy_ticker="BIL",
    )
    assert prepared is not None

    kwargs = dict(
        tickers=tickers,
        weights=weights,
        monthly_returns=monthly_returns,
        asset_betas=asset_betas,
        portfolio_betas={"beta_eq": 0.82, "beta_credit": 0.1},
        target_max_drawdown_pct=0.25,
        cash_proxy_ticker="BIL",
        cov_base=cov_base,
    )
    report_live = run_stress(**kwargs, prepared_synthetic=None)
    report_prepared = run_stress(**kwargs, prepared_synthetic=prepared)

    assert report_live.get("status") == report_prepared.get("status")
    rows_live = report_live.get("scenario_results") or []
    rows_prepared = report_prepared.get("scenario_results") or []
    assert len(rows_live) == len(rows_prepared)
    for row_a, row_b in zip(rows_live, rows_prepared):
        assert row_a.get("scenario_id") == row_b.get("scenario_id")
        assert row_a.get("portfolio_pnl_pct") == pytest.approx(
            row_b.get("portfolio_pnl_pct"), rel=1e-9, abs=1e-9
        )
        assert row_a.get("top1_rc_pct") == pytest.approx(
            row_b.get("top1_rc_pct"), rel=1e-9, abs=1e-9
        )
        assert row_a.get("top3_rc_sum_pct") == pytest.approx(
            row_b.get("top3_rc_sum_pct"), rel=1e-9, abs=1e-9
        )
        assert row_a.get("pass") == row_b.get("pass")


def test_prepare_candidate_run_context_includes_prepared_synthetic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.candidate_run_context import SCHEMA_VERSION, prepare_candidate_run_context
    from src.config_schema import validate_config
    from src.data_loader import MonthlyDataResult

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    tickers = ["VOO", "BND"]
    dates = pd.date_range("2015-01-31", periods=130, freq="ME")
    rng = np.random.default_rng(3)
    monthly_returns = pd.DataFrame(
        {t: rng.normal(0.004, 0.02, len(dates)) for t in tickers},
        index=dates,
    )
    panel = MonthlyDataResult(
        monthly_prices=(1 + monthly_returns).cumprod() * 100.0,
        monthly_returns=monthly_returns,
        monthly_log_returns=np.log1p(monthly_returns),
        rf_monthly=pd.Series(0.001, index=dates),
        benchmark_returns=pd.Series(rng.normal(0.005, 0.018, len(dates)), index=dates),
        cash_returns=pd.Series(0.0, index=dates),
        fx_series_used={},
        analysis_end=dates[-1],
        analysis_end_str=dates[-1].strftime("%Y-%m-%d"),
        daily_cache_key="test_daily",
        monthly_cache_key="test_monthly",
    )
    betas = pd.DataFrame(
        {"beta_eq": [0.9, 0.5], "beta_rr": [0.1, 0.2]},
        index=tickers,
    )

    monkeypatch.setattr(
        "src.candidate_run_context.load_monthly_data_shared",
        lambda **kwargs: panel,
    )
    monkeypatch.setattr(
        "src.candidate_run_context.load_assets_metadata",
        lambda: {},
    )
    monkeypatch.setattr(
        "src.candidate_run_context.resolve_robust_mv_lambda_for_baseline",
        lambda **kwargs: (None, "test"),
    )
    monkeypatch.setattr(
        "src.candidate_run_context.build_factory_factor_stress_inputs",
        lambda **kwargs: type(
            "FS",
            (),
            {
                "asset_betas_5y_universe": betas,
                "asset_betas_10y_universe": betas,
                "asset_betas_5y_extended_universe": betas,
                "asset_betas_10y_extended_universe": betas,
                "daily_asset_returns_for_betas": pd.DataFrame(),
                "cash_returns_daily": pd.Series(dtype=float),
                "recession_factor_returns": pd.DataFrame(),
                "scenario_episode_factor_returns": pd.DataFrame(),
                "weekly_factor_frames": None,
                "beta_source": "test",
                "beta_setup_reasons": (),
            },
        )(),
    )

    ctx = prepare_candidate_run_context(cfg, project_root=Path("."))
    assert SCHEMA_VERSION == "candidate_run_context_v5"
    assert ctx.prepared_synthetic_stress is not None
    assert "equity_shock" in ctx.prepared_synthetic_stress.r_asset_by_scenario
