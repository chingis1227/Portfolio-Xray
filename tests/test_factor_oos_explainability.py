"""Tests for OOS beta×shock episode explainability output."""
from __future__ import annotations

import pandas as pd

from src import stress_factors as sf


def test_factor_oos_beta_shock_explainability_basic(monkeypatch) -> None:
    # Deterministic factor matrix for any requested episode window.
    idx = pd.date_range("2020-01-03", periods=4, freq="W-FRI")
    fac = pd.DataFrame(
        {
            "equity": [-0.10, -0.05, 0.02, -0.01],
            "real_rates": [0.01, 0.00, 0.00, 0.005],
            "inflation": [0.00, 0.00, 0.00, 0.00],
            "credit": [0.01, 0.01, 0.00, 0.00],
            "usd": [0.02, -0.01, 0.00, 0.00],
            "commodity": [0.01, 0.00, 0.00, 0.00],
            "vix": [0.03, 0.02, -0.01, 0.00],
            "us_growth": [0.00, 0.01, 0.00, -0.01],
            "oil": [0.04, -0.02, 0.01, 0.00],
        },
        index=idx,
    )

    monkeypatch.setattr(sf, "build_factor_matrix", lambda *_args, **_kwargs: fac.copy())
    monkeypatch.setattr(
        sf,
        "portfolio_factor_regression_weekly",
        lambda **_kwargs: {
            "betas": {
                "beta_eq": 0.5,
                "beta_rr": -1.0,
                "beta_credit": -0.2,
                "beta_usd": -0.1,
                "beta_cmd": 0.1,
                "beta_vix": 0.3,
                "beta_us_growth": 0.2,
                "beta_oil": -0.4,
            }
        },
    )

    hist = [
        {
            "episode": "X",
            "episode_start": "2020-02-01",
            "episode_end": "2020-03-31",
            "pnl_real_episode": -0.03,
        }
    ]
    out = sf.factor_oos_beta_shock_explainability(
        weights={"AAA": 1.0},
        tickers=["AAA"],
        historical_results=hist,
        factor_betas_5y={
            "beta_eq": 0.4,
            "beta_rr": -1.1,
            "beta_credit": -0.3,
            "beta_usd": -0.2,
            "beta_cmd": 0.0,
            "beta_vix": 0.25,
            "beta_us_growth": 0.05,
            "beta_oil": -0.2,
        },
        factor_betas_10y={
            "beta_eq": 0.3,
            "beta_rr": -0.9,
            "beta_credit": -0.1,
            "beta_usd": -0.2,
            "beta_cmd": 0.1,
            "beta_vix": 0.15,
            "beta_us_growth": 0.02,
            "beta_oil": -0.1,
        },
        rolling_window_weeks=sf.FACTOR_WEEKS_3Y,
    )
    assert out.get("method") == "episode_beta_times_realized_factor_shock"
    assert out.get("episodes")
    ep = out["episodes"][0]
    assert ep["episode"] == "X"
    assert ep["pnl_real_episode"] == -0.03
    assert "pnl_model_5y" in ep and "pnl_model_10y" in ep and "pnl_model_roll3y_pre" in ep
    assert "abs_error_5y" in ep and "abs_error_roll3y_pre" in ep
    assert "beta_vix" in ep["factor_contrib_5y"]
    assert "beta_us_growth" in ep["factor_contrib_10y"]
    assert "beta_oil" in ep["factor_contrib_roll3y_pre"]
    summary = out.get("summary") or {}
    assert "mean_abs_error_5y" in summary

    enriched = sf.enrich_historical_results_with_factor_attribution(hist, out, beta_source="5y")
    assert enriched[0]["factor_attribution_method"] == sf.HISTORICAL_FACTOR_ATTRIBUTION_METHOD
    assert enriched[0]["factor_attribution_beta_source"] == "5y"
    assert "not a pure realized causal decomposition" in enriched[0]["historical_factor_attribution"]["caveat"]
    assert enriched[0]["pnl_by_factor_pct"]["beta_eq"] == ep["factor_contrib_5y"]["beta_eq"]
    assert enriched[0]["factor_model_pnl_pct"] == ep["pnl_model_5y"]
    assert enriched[0]["factor_model_error_pct"] == ep["pnl_model_5y"] - hist[0]["pnl_real_episode"]
    assert enriched[0]["top_factor_drivers"][0]["beta_key"] == "beta_eq"
    assert enriched[0]["largest_negative_factor"]["beta_key"] == "beta_eq"
