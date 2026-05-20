"""Contract tests for hedge_gap_analysis (Stress Lab Session 04)."""
from __future__ import annotations

import pandas as pd

from src.stress import _build_hedge_gap_analysis, run_stress


def _minimal_run(**kwargs: object) -> dict:
    idx = pd.date_range("2015-01-31", periods=120, freq="ME")
    monthly_returns = pd.DataFrame({"AAA": [0.01] * len(idx), "BBB": [0.01] * len(idx)}, index=idx)
    tickers = ["AAA", "BBB"]
    weights = {"AAA": 0.8, "BBB": 0.2}
    asset_betas = pd.DataFrame(columns=["beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd"])
    portfolio_betas = {k: 0.0 for k in ("beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd")}
    defaults = dict(
        tickers=tickers,
        weights=weights,
        monthly_returns=monthly_returns,
        asset_betas=asset_betas,
        portfolio_betas=portfolio_betas,
        target_max_drawdown_pct=0.2,
        cash_proxy_ticker="",
    )
    defaults.update(kwargs)
    return run_stress(**defaults)  # type: ignore[arg-type]


def test_hedge_gap_contract_required_fields() -> None:
    out = _minimal_run(hedge_assets=["AAA"])
    hg = out["hedge_gap_analysis"]
    for key in (
        "method",
        "hedge_assets_considered",
        "n_hedge_assets_considered",
        "worst_scenario_id",
        "worst_scenario_portfolio_pnl_pct",
        "hedge_assets_negative_in_worst_scenario",
        "gap_detected",
        "status",
    ):
        assert key in hg
    assert hg["method"] == "stress_scenario_hedge_evidence_v1"
    assert hg["status"] in {"gap_detected", "no_gap_detected", "insufficient_data"}
    assert isinstance(hg["gap_detected"], bool)
    assert out["stress_conclusions"]["hedge_gap_status"] == hg["status"]


def test_hedge_gap_insufficient_data_without_hedge_labels() -> None:
    out = _minimal_run(hedge_assets=[])
    hg = out["hedge_gap_analysis"]
    assert hg["status"] == "insufficient_data"
    assert hg["gap_detected"] is False
    assert hg["n_hedge_assets_considered"] == 0


def test_hedge_gap_insufficient_data_empty_report() -> None:
    out = _minimal_run(monthly_returns=pd.DataFrame())
    hg = out["hedge_gap_analysis"]
    assert hg["status"] == "insufficient_data"
    assert hg["worst_scenario_portfolio_pnl_pct"] is None


def test_build_hedge_gap_detected_when_portfolio_loss_and_hedge_non_positive() -> None:
    worst = {
        "scenario_id": "equity_shock",
        "portfolio_pnl_pct": -0.12,
        "pnl_by_asset_pct": {"AAA": -0.05, "BBB": 0.01},
    }
    hg = _build_hedge_gap_analysis(worst_scenario_row=worst, hedge_assets=["AAA"])
    assert hg["status"] == "gap_detected"
    assert hg["gap_detected"] is True
    assert hg["worst_scenario_portfolio_pnl_pct"] == -0.12
    assert hg["hedge_assets_negative_in_worst_scenario"] == [{"ticker": "AAA", "pnl_pct": -0.05}]


def test_build_hedge_gap_no_gap_when_portfolio_not_losing() -> None:
    worst = {
        "scenario_id": "equity_shock",
        "portfolio_pnl_pct": 0.02,
        "pnl_by_asset_pct": {"AAA": -0.01, "BBB": 0.03},
    }
    hg = _build_hedge_gap_analysis(worst_scenario_row=worst, hedge_assets=["AAA"])
    assert hg["status"] == "no_gap_detected"
    assert hg["gap_detected"] is False
    assert hg["hedge_assets_negative_in_worst_scenario"] == []


def test_build_hedge_gap_no_gap_when_hedge_positive_in_loss_scenario() -> None:
    worst = {
        "scenario_id": "recession_severe",
        "portfolio_pnl_pct": -0.2,
        "pnl_by_asset_pct": {"AAA": 0.03, "BBB": -0.25},
    }
    hg = _build_hedge_gap_analysis(worst_scenario_row=worst, hedge_assets=["AAA"])
    assert hg["status"] == "no_gap_detected"
    assert hg["gap_detected"] is False


def test_run_stress_gap_detected_with_equity_beta_and_hedge_label() -> None:
    idx = pd.date_range("2015-01-31", periods=60, freq="ME")
    monthly_returns = pd.DataFrame({"AAA": [0.01] * len(idx), "BBB": [0.01] * len(idx)}, index=idx)
    portfolio_betas = {
        "beta_eq": 1.0,
        "beta_rr": 0.0,
        "beta_inf": 0.0,
        "beta_credit": 0.0,
        "beta_usd": 0.0,
        "beta_cmd": 0.0,
    }
    out = run_stress(
        tickers=["AAA", "BBB"],
        weights={"AAA": 0.5, "BBB": 0.5},
        monthly_returns=monthly_returns,
        asset_betas=pd.DataFrame(columns=list(portfolio_betas.keys())),
        portfolio_betas=portfolio_betas,
        target_max_drawdown_pct=0.5,
        cash_proxy_ticker="",
        hedge_assets=["AAA"],
    )
    hg = out["hedge_gap_analysis"]
    assert hg["n_hedge_assets_considered"] == 1
    assert hg["worst_scenario_portfolio_pnl_pct"] is not None
    assert float(hg["worst_scenario_portfolio_pnl_pct"]) < 0
    assert hg["status"] == "gap_detected"
    assert hg["gap_detected"] is True
    assert hg["hedge_assets_negative_in_worst_scenario"]
