"""Contract tests for stress_scorecard_v1 and stress_conclusions (Stress Lab Session 02)."""
from __future__ import annotations

import pandas as pd

from src.stress import _select_worst_historical_row, _worst_scenario_factor_drivers, run_stress


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
        "return_method",
        "proxy_used",
    ):
        assert key in row
    assert row["return_method"] == "realized_portfolio_monthly"
    assert row["proxy_used"] is False
    assert row["data_quality"] in {
        "insufficient_data",
        "low_confidence",
        "usable_with_gaps",
        "reliable",
    }


def test_worst_historical_episode_by_max_dd_not_pnl() -> None:
    """Worst historical must follow max_dd (pass/fail gate), not cumulative episode PnL."""
    rows = [
        {
            "episode": "shallow_dd_positive_pnl",
            "max_dd": -0.10,
            "pnl_real_episode": -0.25,
            "pass": True,
            "data_quality": "reliable",
        },
        {
            "episode": "deep_dd_recovered_pnl",
            "max_dd": -0.40,
            "pnl_real_episode": 0.05,
            "pass": False,
            "data_quality": "reliable",
        },
    ]
    worst = _select_worst_historical_row(rows)
    assert worst is not None
    assert worst["episode"] == "deep_dd_recovered_pnl"
    assert float(worst["max_dd"]) < float(rows[0]["max_dd"])
    assert float(worst["pnl_real_episode"]) > float(rows[0]["pnl_real_episode"])


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


def test_conclusions_factor_drivers_from_worst_scenario() -> None:
    """Factor loss/help channels in conclusions mirror worst synthetic pnl_by_factor_pct."""
    worst_row = {
        "scenario_id": "recession_severe",
        "portfolio_pnl_pct": -0.25,
        "pnl_by_factor_pct": {
            "eq": -0.18,
            "rr": -0.05,
            "credit": 0.03,
            "cmd": 0.01,
        },
    }
    top_loss, helped = _worst_scenario_factor_drivers(worst_row)
    assert len(top_loss) == 2
    assert top_loss[0]["factor_short"] == "eq"
    assert top_loss[0]["beta_key"] == "beta_eq"
    assert top_loss[0]["direction"] == "loss"
    assert top_loss[0]["rank"] == 1
    assert top_loss[1]["factor_short"] == "rr"
    assert len(helped) == 2
    assert helped[0]["factor_short"] == "credit"
    assert helped[0]["direction"] == "gain"

    out = _minimal_run()
    conclusions = out["stress_conclusions"]
    assert "top_factor_drivers_worst_scenario" in conclusions
    assert "helped_factors_worst_scenario" in conclusions
    assert isinstance(conclusions["top_factor_drivers_worst_scenario"], list)
    assert isinstance(conclusions["helped_factors_worst_scenario"], list)

    worst_syn = min(
        out["scenario_results"],
        key=lambda r: float(r["portfolio_pnl_pct"]),
    )
    expected_top, expected_helped = _worst_scenario_factor_drivers(worst_syn)
    assert conclusions["top_factor_drivers_worst_scenario"] == expected_top
    assert conclusions["helped_factors_worst_scenario"] == expected_helped


def test_empty_report_scorecard_contract() -> None:
    out = _minimal_run(monthly_returns=pd.DataFrame())
    scorecard = out["stress_scorecard_v1"]
    conclusions = out["stress_conclusions"]
    assert scorecard["overall_confidence"] == "low"
    assert conclusions["overall_confidence"] == "low"
    assert scorecard["n_synthetic_scenarios"] == 0
    assert conclusions["hedge_gap_status"] == "not_applicable"
    assert conclusions["top_factor_drivers_worst_scenario"] == []
    assert conclusions["helped_factors_worst_scenario"] == []
