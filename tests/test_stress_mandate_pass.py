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
    asset_betas = pd.DataFrame(columns=["beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd"])
    portfolio_betas = {
        "beta_eq": 1.0,
        "beta_rr": 0.0,
        "beta_inf": 0.0,
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
    eq = next((r for r in out["scenario_results"] if r["scenario_id"] == "equity_shock"), None)
    assert eq is not None
    assert eq.get("pnl_by_factor_pct", {}).get("eq") == round(-0.4 * 1.0, 4)
