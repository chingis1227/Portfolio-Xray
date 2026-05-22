from __future__ import annotations

import numpy as np
import pandas as pd

from src.stress import run_stress
from src.stress_factors import (
    compute_asset_factor_betas_from_daily_returns,
    portfolio_factor_betas,
)


def test_cached_daily_returns_produce_asset_and_portfolio_factor_betas(monkeypatch) -> None:
    weeks = pd.date_range("2020-01-03", periods=140, freq="W-FRI")
    daily_idx = pd.bdate_range(weeks.min() - pd.Timedelta(days=4), weeks.max())
    weekly_factor = pd.DataFrame(
        {
            "equity": np.linspace(-0.01, 0.015, len(weeks)),
            "real_rates": np.linspace(0.002, -0.002, len(weeks)),
            "credit": np.sin(np.linspace(0, 6, len(weeks))) * 0.003,
        },
        index=weeks,
    )

    daily_returns = pd.DataFrame(0.0, index=daily_idx, columns=["AAA", "BBB"])
    friday_rows = daily_returns.index.isin(weeks)
    daily_returns.loc[friday_rows, "AAA"] = (
        0.9 * weekly_factor["equity"].to_numpy()
        + 0.2 * weekly_factor["real_rates"].to_numpy()
    )
    daily_returns.loc[friday_rows, "BBB"] = (
        0.4 * weekly_factor["equity"].to_numpy()
        - 0.1 * weekly_factor["real_rates"].to_numpy()
        + 0.5 * weekly_factor["credit"].to_numpy()
    )

    monkeypatch.setattr(
        "src.stress_factors.build_factor_matrix",
        lambda start, end, require_complete_rows=True: weekly_factor,
    )

    betas = compute_asset_factor_betas_from_daily_returns(
        daily_returns,
        "2022-09-09",
        window_weeks=120,
        min_aligned_weeks=52,
    )

    assert set(betas.index) == {"AAA", "BBB"}
    assert {"beta_eq", "beta_rr"}.issubset(set(betas.columns))

    portfolio_betas = portfolio_factor_betas({"AAA": 0.6, "BBB": 0.4}, betas)
    out = run_stress(
        tickers=["AAA", "BBB"],
        weights={"AAA": 0.6, "BBB": 0.4},
        monthly_returns=pd.DataFrame(
            {"AAA": [0.01, -0.02, 0.015], "BBB": [0.005, -0.01, 0.012]},
            index=pd.date_range("2022-01-31", periods=3, freq="ME"),
        ),
        asset_betas=betas,
        portfolio_betas=portfolio_betas,
        target_max_drawdown_pct=0.25,
        beta_data_source="cached_daily_returns_weekly_ols",
    )
    first = out["scenario_results"][0]
    assert first["beta_coverage_ratio"] > 0
    assert first["pnl_by_factor_pct"]
    assert first["synthetic_assumptions"]["beta_data_source"] == "cached_daily_returns_weekly_ols"
    assert first["synthetic_assumptions"]["covered_assets"] == ["AAA", "BBB"]


def test_cached_daily_returns_can_use_cached_equity_proxy_when_factor_matrix_empty(monkeypatch) -> None:
    weeks = pd.date_range("2021-01-01", periods=80, freq="W-FRI")
    daily_idx = pd.bdate_range(weeks.min() - pd.Timedelta(days=4), weeks.max())
    daily_returns = pd.DataFrame(0.0, index=daily_idx, columns=["SPY", "AAA"])
    weekly_equity = np.linspace(-0.015, 0.012, len(weeks))
    friday_rows = daily_returns.index.isin(weeks)
    daily_returns.loc[friday_rows, "SPY"] = weekly_equity
    daily_returns.loc[friday_rows, "AAA"] = 0.8 * weekly_equity

    monkeypatch.setattr(
        "src.stress_factors.build_factor_matrix",
        lambda start, end, require_complete_rows=True: pd.DataFrame(),
    )

    betas = compute_asset_factor_betas_from_daily_returns(
        daily_returns,
        "2022-07-08",
        window_weeks=70,
        min_aligned_weeks=52,
        asset_tickers=["AAA"],
        equity_factor_ticker="SPY",
    )
    assert list(betas.index) == ["AAA"]
    assert "beta_eq" in betas.columns
    assert abs(float(betas.loc["AAA", "beta_eq"]) - 0.8) < 0.05
