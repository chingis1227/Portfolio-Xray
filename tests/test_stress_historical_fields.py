"""Historical stress result fields should include episode bounds and real episode PnL."""
from __future__ import annotations

import pandas as pd

from src.stress import run_stress


def test_historical_results_include_episode_bounds_and_pnl() -> None:
    idx = pd.date_range("2019-01-31", periods=72, freq="M")
    monthly_returns = pd.DataFrame(
        {
            "AAA": [0.01] * len(idx),
            "BBB": [0.005] * len(idx),
        },
        index=idx,
    )
    tickers = ["AAA", "BBB"]
    weights = {"AAA": 0.6, "BBB": 0.4}
    blocks = {
        "Growth": ["AAA"],
        "Duration": ["BBB"],
        "Inflation": [],
        "Liquidity": [],
        "Tail": [],
    }
    # Keep all betas zero for this field-level test.
    asset_betas = pd.DataFrame(index=tickers, columns=["beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd"]).fillna(0.0)
    portfolio_betas = {"beta_eq": 0.0, "beta_rr": 0.0, "beta_inf": 0.0, "beta_credit": 0.0, "beta_usd": 0.0, "beta_cmd": 0.0}

    out = run_stress(
        tickers=tickers,
        weights=weights,
        blocks=blocks,
        monthly_returns=monthly_returns,
        asset_betas=asset_betas,
        portfolio_betas=portfolio_betas,
        target_max_drawdown_pct=0.2,
        rc_asset_cap_pct=0.25,
        stress_top3_rc_sum_cap_pct=0.7,
    )
    hist = out.get("historical_results") or []
    assert hist, "historical_results should not be empty"
    for h in hist:
        assert "episode_start" in h
        assert "episode_end" in h
        assert "pnl_real_episode" in h
