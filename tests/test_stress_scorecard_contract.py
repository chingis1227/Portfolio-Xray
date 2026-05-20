"""Contract tests for stress_scorecard_v1 and stress_conclusions (Stress Lab Session 02)."""
from __future__ import annotations

import pandas as pd

from src.stress import run_stress


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
        hedge_assets=["AAA"],
    )
    defaults.update(kwargs)
    return run_stress(**defaults)  # type: ignore[arg-type]


def test_scorecard_and_conclusions_required_fields() -> None:
    out = _minimal_run()
    scorecard = out["stress_scorecard_v1"]
    conclusions = out["stress_conclusions"]

    assert scorecard["version"] == "stress_scorecard_v1"
    assert conclusions["version"] == "stress_conclusions_v1"
    assert scorecard["overall_status"] in {"DIAG_PASS", "DIAG_PASS_WITH_WARNING", "DIAG_ATTENTION"}
    assert scorecard["overall_confidence"] in {"low", "medium", "high"}
    assert conclusions["overall_confidence"] == scorecard["overall_confidence"]
    assert scorecard["n_synthetic_scenarios"] == len(scorecard["synthetic_scenarios"])
    assert scorecard["n_historical_episodes"] == len(scorecard["historical_episodes"])

    assert conclusions["hedge_gap_status"] == out["hedge_gap_analysis"]["status"]
    assert "loss_severity" in conclusions["worst_synthetic_scenario"]
    assert "loss_severity" in conclusions["worst_historical_episode"]


def test_scorecard_synthetic_row_contract() -> None:
    out = _minimal_run()
    rows = out["stress_scorecard_v1"]["synthetic_scenarios"]
    assert rows
    row = rows[0]
    for key in (
        "scenario_id",
        "portfolio_pnl_pct",
        "pass",
        "loss_ok",
        "loss_severity",
        "beta_coverage_ratio",
        "beta_confidence",
        "top3_loss_assets",
        "top1_rc_asset",
        "top1_rc_pct",
        "top3_rc_assets",
        "top3_rc_sum_pct",
        "diagnostic_codes",
    ):
        assert key in row
    assert row["loss_severity"] in {"low", "moderate", "high", "unknown"}
    assert row["beta_confidence"] in {"low", "medium", "high"}


def test_scorecard_historical_row_contract() -> None:
    out = _minimal_run()
    rows = out["stress_scorecard_v1"]["historical_episodes"]
    assert rows
    row = rows[0]
    for key in (
        "episode",
        "pnl_real_episode",
        "max_dd",
        "pass",
        "loss_severity",
        "data_quality",
        "coverage_ratio",
        "n_obs",
    ):
        assert key in row
    assert row["data_quality"] in {
        "insufficient_data",
        "low_confidence",
        "usable_with_gaps",
        "reliable",
    }


def test_conclusions_top_loss_and_helped_assets() -> None:
    out = _minimal_run()
    conclusions = out["stress_conclusions"]
    scorecard = out["stress_scorecard_v1"]
    worst_syn = min(
        scorecard["synthetic_scenarios"],
        key=lambda r: float(r["portfolio_pnl_pct"]),
    )
    assert conclusions["worst_synthetic_scenario"]["scenario_id"] == worst_syn["scenario_id"]
    assert conclusions["top_loss_assets_worst_scenario"] == worst_syn["top3_loss_assets"]
    assert isinstance(conclusions["helped_assets_worst_scenario"], list)


def test_empty_report_scorecard_contract() -> None:
    out = _minimal_run(monthly_returns=pd.DataFrame())
    scorecard = out["stress_scorecard_v1"]
    conclusions = out["stress_conclusions"]
    assert scorecard["overall_confidence"] == "low"
    assert conclusions["overall_confidence"] == "low"
    assert scorecard["n_synthetic_scenarios"] == 0
    assert conclusions["hedge_gap_status"] == "insufficient_data"
