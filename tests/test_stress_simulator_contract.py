"""Contract tests for What Happens If simulator API (Stress Lab Session 09, no UI)."""
from __future__ import annotations

import pandas as pd
import pytest

from src.stress import (
    CUSTOM_SHOCK_SIMULATOR_VERSION,
    SCENARIOS,
    run_stress,
    shock_vector_from_scenario,
    simulate_custom_shock,
)


def _fixture_run() -> tuple[dict, list[str], dict[str, float], pd.DataFrame, dict[str, float]]:
    idx = pd.date_range("2010-01-31", periods=120, freq="ME")
    tickers = ["AAA", "BBB"]
    monthly_returns = pd.DataFrame(
        {"AAA": [0.01] * len(idx), "BBB": [-0.005] * len(idx)},
        index=idx,
    )
    weights = {"AAA": 0.6, "BBB": 0.4}
    asset_betas = pd.DataFrame(
        {
            "beta_eq": [1.2, 0.5],
            "beta_rr": [-0.2, 0.1],
            "beta_inf": [0.0, 0.05],
            "beta_credit": [-0.3, 0.2],
            "beta_usd": [0.1, -0.1],
            "beta_cmd": [0.15, 0.25],
        },
        index=tickers,
    )
    portfolio_betas = {
        "beta_eq": 0.92,
        "beta_rr": -0.08,
        "beta_inf": 0.02,
        "beta_credit": -0.1,
        "beta_usd": 0.04,
        "beta_cmd": 0.19,
    }
    out = run_stress(
        tickers=tickers,
        weights=weights,
        monthly_returns=monthly_returns,
        asset_betas=asset_betas,
        portfolio_betas=portfolio_betas,
        target_max_drawdown_pct=0.25,
        cash_proxy_ticker="",
    )
    return out, tickers, weights, asset_betas, portfolio_betas


def test_simulate_custom_shock_contract_fields() -> None:
    tickers = ["AAA"]
    weights = {"AAA": 1.0}
    asset_betas = pd.DataFrame(
        {
            "beta_eq": [1.0],
            "beta_rr": [0.0],
            "beta_inf": [0.0],
            "beta_credit": [0.0],
            "beta_usd": [0.0],
            "beta_cmd": [0.0],
        },
        index=tickers,
    )
    portfolio_betas = {
        "beta_eq": 1.0,
        "beta_rr": 0.0,
        "beta_inf": 0.0,
        "beta_credit": 0.0,
        "beta_usd": 0.0,
        "beta_cmd": 0.0,
    }
    out = simulate_custom_shock(
        tickers=tickers,
        weights=weights,
        asset_betas=asset_betas,
        portfolio_betas=portfolio_betas,
        shock_vector={"shock_eq": -0.2},
        scenario_id="equity_shock",
    )
    assert out["version"] == CUSTOM_SHOCK_SIMULATOR_VERSION
    assert out["method"] == "linear_factor_shock_v1"
    assert out["scenario_id"] == "equity_shock"
    assert out["portfolio_pnl_pct"] == out["model_pnl_pct"] == -0.2
    assert out["pnl_by_factor_pct"]["eq"] == -0.2
    assert "synthetic_assumptions" in out
    assert out["synthetic_assumptions"]["version"] == "synthetic_assumptions_v1"


def test_shock_vector_from_scenario_matches_scenarios_dict() -> None:
    for scenario_id, params in SCENARIOS.items():
        expected = {k: float(v) for k, v in params.items() if k.startswith("shock_")}
        got = shock_vector_from_scenario(scenario_id)
        assert got == pytest.approx(expected, rel=0, abs=1e-9)


@pytest.mark.parametrize("scenario_id", list(SCENARIOS.keys()))
def test_custom_shock_matches_builtin_scenario_pnl(scenario_id: str) -> None:
    out, tickers, weights, asset_betas, portfolio_betas = _fixture_run()
    builtin = next(r for r in out["scenario_results"] if r["scenario_id"] == scenario_id)
    shock = shock_vector_from_scenario(scenario_id)
    custom = simulate_custom_shock(
        tickers=tickers,
        weights=weights,
        asset_betas=asset_betas,
        portfolio_betas=portfolio_betas,
        shock_vector=shock,
        scenario_id=scenario_id,
    )
    assert custom["shock_vector"] == builtin["shock_vector"]
    assert custom["portfolio_pnl_pct"] == builtin["portfolio_pnl_pct"]
    assert custom["model_pnl_pct"] == builtin["portfolio_pnl_pct"]
    assert custom["pnl_by_asset_pct"] == builtin["pnl_by_asset_pct"]
    assert custom["pnl_by_factor_pct"] == builtin["pnl_by_factor_pct"]
    assert custom["top3_loss_assets"] == builtin["top3_loss_assets"]
    assert custom["beta_coverage_ratio"] == builtin["beta_coverage_ratio"]
    assert custom["beta_fallback_assets"] == builtin["beta_fallback_assets"]


def test_custom_shock_matches_calibrated_recession_severe() -> None:
    out, tickers, weights, asset_betas, portfolio_betas = _fixture_run()
    builtin = next(r for r in out["scenario_results"] if r["scenario_id"] == "recession_severe")
    shock = shock_vector_from_scenario("recession_severe")
    custom = simulate_custom_shock(
        tickers=tickers,
        weights=weights,
        asset_betas=asset_betas,
        portfolio_betas=portfolio_betas,
        shock_vector=shock,
        scenario_id="recession_severe",
    )
    assert custom["portfolio_pnl_pct"] == builtin["portfolio_pnl_pct"]
    assert custom["pnl_by_asset_pct"] == builtin["pnl_by_asset_pct"]
    assert custom["pnl_by_factor_pct"] == builtin["pnl_by_factor_pct"]
