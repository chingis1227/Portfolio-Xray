"""Synthetic stress pass = mandate portfolio PnL only; RC Top1/Top3 are diagnostics only."""
from __future__ import annotations

import pandas as pd

from src.stress import HISTORICAL_EPISODES, run_stress


def test_historical_episodes_include_dotcom() -> None:
    ids = [t[0] for t in HISTORICAL_EPISODES]
    assert ids[0] == "dotcom"
    assert "2008" in ids and "2020" in ids and "2022" in ids


def test_synthetic_pass_ignores_rc_when_loss_ok() -> None:
    # Long history so historical episodes (incl. dotcom) are not all borderline-empty.
    idx = pd.date_range("1995-01-31", periods=360, freq="ME")
    monthly_returns = pd.DataFrame(
        {"AAA": [0.008] * len(idx), "BBB": [0.008] * len(idx)},
        index=idx,
    )
    tickers = ["AAA", "BBB"]
    weights = {"AAA": 0.99, "BBB": 0.01}
    # Empty index → per-asset returns use shock_eq proxy (betas not applied row-wise).
    asset_betas = pd.DataFrame(columns=["beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd"])
    portfolio_betas = {k: 0.0 for k in ("beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd")}

    out = run_stress(
        tickers=tickers,
        weights=weights,
        monthly_returns=monthly_returns,
        asset_betas=asset_betas,
        portfolio_betas=portfolio_betas,
        target_max_drawdown_pct=0.5,
        cash_proxy_ticker="",
    )
    eq = next((r for r in out["scenario_results"] if r["scenario_id"] == "equity_shock"), None)
    assert eq is not None
    assert eq["loss_ok"] is True
    assert eq["pass"] is True
    assert "pnl_by_asset_pct" in eq and set(eq["pnl_by_asset_pct"]) == {"AAA", "BBB"}
    assert "top1_rc_pct" in eq and eq["top1_rc_pct"] is not None
    assert "rc_diagnostic_codes" not in eq
    assert eq["pnl_by_factor_pct"] == {}

    assert out["status"] == "DIAG_PASS"
    assert out.get("warning_code") in (None, "")
    assert "rc_attention_codes" not in out
    assert not any(str(c).startswith("DIAG_RC_") for c in (out.get("diagnostic_codes") or []))


def test_synthetic_pass_false_on_loss_only() -> None:
    idx = pd.date_range("2015-01-31", periods=60, freq="M")
    monthly_returns = pd.DataFrame(
        {"AAA": [0.01] * len(idx), "BBB": [0.01] * len(idx)},
        index=idx,
    )
    tickers = ["AAA", "BBB"]
    weights = {"AAA": 0.5, "BBB": 0.5}
    asset_betas = pd.DataFrame(columns=["beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd"])
    portfolio_betas = {k: 0.0 for k in ("beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd")}

    out = run_stress(
        tickers=tickers,
        weights=weights,
        monthly_returns=monthly_returns,
        asset_betas=asset_betas,
        portfolio_betas=portfolio_betas,
        target_max_drawdown_pct=0.05,
        cash_proxy_ticker="",
    )
    eq = next((r for r in out["scenario_results"] if r["scenario_id"] == "equity_shock"), None)
    assert eq is not None
    assert eq["loss_ok"] is False
    assert eq["pass"] is False
    assert out["status"] == "DIAG_ATTENTION"
    assert any(str(c).startswith("DIAG_LOSS_") for c in out.get("diagnostic_codes") or [])


def test_pnl_by_factor_pct_uses_portfolio_betas() -> None:
    idx = pd.date_range("2015-01-31", periods=60, freq="M")
    monthly_returns = pd.DataFrame(
        {"AAA": [0.01] * len(idx), "BBB": [0.01] * len(idx)},
        index=idx,
    )
    tickers = ["AAA", "BBB"]
    weights = {"AAA": 0.5, "BBB": 0.5}
    asset_betas = pd.DataFrame(columns=["beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd", "beta_vix", "beta_us_growth", "beta_oil"])
    portfolio_betas = {
        "beta_eq": 1.0,
        "beta_rr": 0.0,
        "beta_inf": 0.0,
        "beta_credit": 0.0,
        "beta_usd": 0.0,
        "beta_cmd": 0.0,
        "beta_vix": 99.0,
        "beta_us_growth": -99.0,
        "beta_oil": 77.0,
    }

    out = run_stress(
        tickers=tickers,
        weights=weights,
        monthly_returns=monthly_returns,
        asset_betas=asset_betas,
        portfolio_betas=portfolio_betas,
        target_max_drawdown_pct=0.5,
        cash_proxy_ticker="",
    )
    eq = next((r for r in out["scenario_results"] if r["scenario_id"] == "equity_shock"), None)
    assert eq is not None
    assert eq.get("pnl_by_factor_pct", {}).get("eq") == round(-0.4 * 1.0, 4)
    assert set(eq.get("pnl_by_factor_pct", {}).keys()) == {"eq"}
    assert "beta_vix" in out["factor_betas"]
    assert "beta_us_growth" in out["factor_betas"]
    assert "beta_oil" not in out["factor_betas"]


def test_inflation_stagflation_includes_direct_inflation_shock() -> None:
    idx = pd.date_range("2015-01-31", periods=60, freq="M")
    monthly_returns = pd.DataFrame({"AAA": [0.01] * len(idx)}, index=idx)
    tickers = ["AAA"]
    weights = {"AAA": 1.0}
    asset_betas = pd.DataFrame(
        {
            "beta_eq": [0.0],
            "beta_rr": [0.0],
            "beta_inf": [-4.0],
            "beta_credit": [0.0],
            "beta_usd": [0.0],
            "beta_cmd": [0.0],
        },
        index=tickers,
    )
    portfolio_betas = {
        "beta_eq": 0.0,
        "beta_rr": 0.0,
        "beta_inf": -4.0,
        "beta_credit": 0.0,
        "beta_usd": 0.0,
        "beta_cmd": 0.0,
    }

    out = run_stress(
        tickers=tickers,
        weights=weights,
        monthly_returns=monthly_returns,
        asset_betas=asset_betas,
        portfolio_betas=portfolio_betas,
        target_max_drawdown_pct=0.5,
        cash_proxy_ticker="",
    )

    stagflation = next((r for r in out["scenario_results"] if r["scenario_id"] == "inflation_stagflation"), None)
    assert stagflation is not None
    assert stagflation["shock_vector"]["shock_inf"] == 0.005
    assert stagflation["pnl_by_factor_pct"]["inf"] == -0.02
    assert stagflation["portfolio_pnl_pct"] == -0.02


def test_recession_severe_is_calibrated_from_worst_2008_2020_model_pnl() -> None:
    idx = pd.date_range("2007-01-31", "2021-12-31", freq="M")
    monthly_returns = pd.DataFrame({"AAA": [0.0] * len(idx)}, index=idx)
    factor_returns = pd.DataFrame(
        {
            "equity": [-0.30, -0.20],
            "real_rates": [-0.01, -0.005],
            "inflation": [-0.003, -0.001],
            "credit": [0.04, 0.02],
            "usd": [0.05, 0.03],
            "commodity": [-0.10, -0.05],
        },
        index=pd.to_datetime(["2008-10-03", "2020-03-06"]),
    )
    tickers = ["AAA"]
    weights = {"AAA": 1.0}
    asset_betas = pd.DataFrame(
        {
            "beta_eq": [1.0],
            "beta_rr": [0.0],
            "beta_inf": [0.0],
            "beta_credit": [-2.0],
            "beta_usd": [-0.5],
            "beta_cmd": [0.1],
        },
        index=tickers,
    )
    portfolio_betas = {
        "beta_eq": 1.0,
        "beta_rr": 0.0,
        "beta_inf": 0.0,
        "beta_credit": -2.0,
        "beta_usd": -0.5,
        "beta_cmd": 0.1,
    }

    out = run_stress(
        tickers=tickers,
        weights=weights,
        monthly_returns=monthly_returns,
        asset_betas=asset_betas,
        portfolio_betas=portfolio_betas,
        target_max_drawdown_pct=0.4,
        cash_proxy_ticker="",
        factor_returns=factor_returns,
    )

    recession = next((r for r in out["scenario_results"] if r["scenario_id"] == "recession_severe"), None)
    assert recession is not None
    assert recession["calibration_source_episode"] == "2008"
    assert recession["shock_vector"]["shock_eq"] == -0.30
    assert recession["shock_vector"]["shock_credit"] == 0.04
    assert recession["portfolio_pnl_pct"] == -0.415
    assert recession["vol_mult"] == 1.60
    assert recession["risk_on_corr"] == 0.95
    assert "DIAG_LOSS_RECESSION_SEVERE" in recession["diagnostic_codes"]
    assert "DIAG_LOSS_RECESSION_SEVERE" in out["diagnostic_codes"]

    calibration = out.get("recession_calibration") or {}
    assert calibration["status"] == "calibrated"
    assert calibration["selected_source_episode"] == "2008"
    assert calibration["model_pnl_by_episode"]["2008"] == -0.415
    assert calibration["model_pnl_by_episode"]["2020"] == -0.26
    validation = {row["episode"]: row for row in calibration["model_vs_realized"]}
    assert validation["2008"]["model_pnl_pct"] == -0.415
    assert validation["2008"]["realized_pnl_pct"] == 0.0
