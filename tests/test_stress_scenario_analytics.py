"""Tests for stress_scenario_analytics_v1 (diagnostic per-scenario covariance / RC exports)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.stress_factors import FACTOR_COLUMN_ORDER, FACTOR_TO_BETA_KEY
from src.stress_scenario_analytics import (
    STRESS_SCENARIO_ANALYTICS_VERSION,
    build_stress_scenario_analytics,
    quality_status_from_n_months,
)


def _beta_map(val: float = 0.1) -> dict[str, float]:
    return {FACTOR_TO_BETA_KEY[f]: float(val) for f in FACTOR_COLUMN_ORDER if f in FACTOR_TO_BETA_KEY}


def _factor_cov_nested(scale: float = 1e-4) -> dict[str, dict[str, float]]:
    """Tiny diagonal weekly factor covariance nest (production factor order)."""
    out: dict[str, dict[str, float]] = {}
    for f in FACTOR_COLUMN_ORDER:
        row: dict[str, float] = {}
        for g in FACTOR_COLUMN_ORDER:
            row[str(g)] = float(scale) if f == g else 0.0
        out[str(f)] = row
    return out


def _minimal_stress_report(*, with_regression: bool = True) -> dict:
    betas = _beta_map(0.05)
    reg5: dict = {"betas": betas, "n_obs": 200, "r2": 0.2, "adj_r2": 0.15}
    reg10: dict = {"betas": betas, "n_obs": 400, "r2": 0.22, "adj_r2": 0.16}
    if not with_regression:
        reg5 = {}
        reg10 = {}
    return {
        "scenario_results": [
            {
                "scenario_id": "equity_shock",
                "shock_vector": {
                    "shock_eq": -0.10,
                    "shock_rr": 0.0,
                    "shock_credit": 0.0,
                    "shock_inf": 0.0,
                    "shock_usd": 0.0,
                    "shock_cmd": 0.0,
                },
                "portfolio_pnl_pct": -1.25,
            }
        ],
        "historical_results": [
            {
                "episode": "hist_a",
                "episode_start": "2020-01-31",
                "episode_end": "2020-06-30",
                "pnl_real_episode": -12.5,
            }
        ],
        "factor_betas_5y": betas,
        "factor_betas_10y": betas,
        "factor_regression_5y": reg5,
        "factor_regression_10y": reg10,
        "factor_covariance": {
            "base": {
                "matrix": _factor_cov_nested(1e-4),
                "n_obs": 260,
                "window": {"analysis_end": "2024-01-31"},
            },
        },
        "factor_betas_adjusted": {"adjusted": {k: v * 0.95 for k, v in betas.items()}},
        "synthetic_factor_pnl_adjusted": {
            "scenarios": [
                {
                    "scenario_id": "equity_shock",
                    "pnl_model_raw": -1.2,
                    "pnl_model_adjusted": -1.0,
                }
            ]
        },
    }


def test_quality_status_bins():
    assert quality_status_from_n_months(5) == "insufficient_data"
    assert quality_status_from_n_months(15) == "low_confidence"
    assert quality_status_from_n_months(30) == "usable"
    assert quality_status_from_n_months(70) == "reliable"


def test_historical_actual_pnl_and_synthetic_pnl_layers():
    idx = pd.date_range("2018-01-31", periods=60, freq="ME")
    rng = np.random.default_rng(0)
    monthly_returns = pd.DataFrame(
        {"VOO": rng.normal(0.005, 0.03, len(idx)), "UNKNOWNXYZ99": rng.normal(0.004, 0.03, len(idx))},
        index=idx,
    )
    rep = _minimal_stress_report()
    weekly = pd.DataFrame(
        rng.normal(0.0, 0.01, (80, len(FACTOR_COLUMN_ORDER))),
        columns=list(FACTOR_COLUMN_ORDER),
        index=pd.date_range("2019-01-04", periods=80, freq="W-FRI"),
    )
    out = build_stress_scenario_analytics(
        stress_report=rep,
        weights={"VOO": 0.5, "UNKNOWNXYZ99": 0.5},
        tickers=["VOO", "UNKNOWNXYZ99"],
        monthly_returns=monthly_returns,
        factor_returns_weekly=weekly,
        cash_proxy_ticker="BIL",
        output_dir_csv=None,
    )
    assert out["version"] == STRESS_SCENARIO_ANALYTICS_VERSION
    h = out["scenarios"]["hist_a"]
    assert h["scenario_type"] == "historical"
    assert h["actual_pnl"] == -12.5
    assert h["pnl_raw"] is None
    s = out["scenarios"]["equity_shock"]
    assert s["scenario_type"] == "synthetic"
    assert s["pnl_raw"] == -1.25
    assert s["pnl_shrinkage_adjusted"] == -1.0
    assert s["conservative_pnl"] == -1.25


def test_regression_available_without_status_field():
    """Weekly factor_regression_* payloads omit ``status``; betas alone should suffice."""
    rep = _minimal_stress_report(with_regression=True)
    rep["factor_regression_5y"] = {"betas": _beta_map(0.1), "n_obs": 80}
    idx = pd.date_range("2018-01-31", periods=40, freq="ME")
    monthly_returns = pd.DataFrame({"A": np.linspace(-0.02, 0.02, len(idx))}, index=idx)
    out = build_stress_scenario_analytics(
        stress_report=rep,
        weights={"A": 1.0},
        tickers=["A"],
        monthly_returns=monthly_returns,
        factor_returns_weekly=None,
        cash_proxy_ticker="BIL",
        output_dir_csv=None,
    )
    assert out["scenarios"]["equity_shock"]["factor_betas_available"] is True


def test_asset_rc_shares_sum_to_one():
    idx = pd.date_range("2018-01-31", periods=48, freq="ME")
    rng = np.random.default_rng(1)
    monthly_returns = pd.DataFrame(
        {"X": rng.normal(0, 0.02, len(idx)), "Y": rng.normal(0, 0.02, len(idx))},
        index=idx,
    )
    rep = _minimal_stress_report()
    build_stress_scenario_analytics(
        stress_report=rep,
        weights={"X": 0.4, "Y": 0.6},
        tickers=["X", "Y"],
        monthly_returns=monthly_returns,
        factor_returns_weekly=pd.DataFrame(
            0.0,
            index=pd.date_range("2018-01-05", periods=120, freq="W-FRI"),
            columns=list(FACTOR_COLUMN_ORDER),
        ),
        cash_proxy_ticker="BIL",
        output_dir_csv=None,
    )
    from src.stress_scenario_analytics import _factor_risk_contrib_rows, _nested_cov_to_df

    cov_df = _nested_cov_to_df(rep["factor_covariance"]["base"]["matrix"])
    rows, _summ = _factor_risk_contrib_rows(cov_df, rep["factor_betas_5y"])
    total_rc = sum(float(r["rc_share"]) for r in rows)
    assert abs(total_rc - 1.0) < 1e-5


def test_historical_short_window_quality_and_factor_fallback_warning():
    idx = pd.date_range("2018-01-31", periods=30, freq="ME")
    monthly_returns = pd.DataFrame({"A": 0.01 * np.ones(len(idx)), "B": -0.005 * np.ones(len(idx))}, index=idx)
    rep = _minimal_stress_report()
    rep["historical_results"] = [
        {
            "episode": "shorty",
            "episode_start": "2020-01-31",
            "episode_end": "2020-04-30",
            "pnl_real_episode": -3.0,
        }
    ]
    out = build_stress_scenario_analytics(
        stress_report=rep,
        weights={"A": 0.5, "B": 0.5},
        tickers=["A", "B"],
        monthly_returns=monthly_returns,
        factor_returns_weekly=pd.DataFrame(),  # triggers fallback for factor episode cov
        cash_proxy_ticker="BIL",
        output_dir_csv=None,
    )
    h = out["scenarios"]["shorty"]
    assert h["asset_covariance"]["quality_status"] == "insufficient_data"
    assert "factor_returns_missing_fallback_base" in (h["factor_covariance"].get("warnings") or [])


def test_historical_factor_cov_fallback_when_few_weekly_points():
    idx = pd.date_range("2018-01-31", periods=30, freq="ME")
    monthly_returns = pd.DataFrame({"A": 0.01 * np.ones(len(idx)), "B": -0.005 * np.ones(len(idx))}, index=idx)
    rep = _minimal_stress_report()
    rep["historical_results"] = [
        {
            "episode": "sparse_w",
            "episode_start": "2020-01-31",
            "episode_end": "2020-04-30",
            "pnl_real_episode": -1.0,
        }
    ]
    widx = pd.to_datetime(["2020-03-06"])
    weekly = pd.DataFrame(0.001, index=widx, columns=list(FACTOR_COLUMN_ORDER))
    out = build_stress_scenario_analytics(
        stress_report=rep,
        weights={"A": 0.5, "B": 0.5},
        tickers=["A", "B"],
        monthly_returns=monthly_returns,
        factor_returns_weekly=weekly,
        cash_proxy_ticker="BIL",
        output_dir_csv=None,
    )
    assert "factor_cov_fallback_full_sample" in (
        out["scenarios"]["sparse_w"]["factor_covariance"].get("warnings") or []
    )


def test_export_csv_rounding(tmp_path):
    idx = pd.date_range("2018-01-31", periods=36, freq="ME")
    monthly_returns = pd.DataFrame({"C": np.random.default_rng(2).normal(0, 0.02, len(idx))}, index=idx)
    rep = _minimal_stress_report()
    build_stress_scenario_analytics(
        stress_report=rep,
        weights={"C": 1.0},
        tickers=["C"],
        monthly_returns=monthly_returns,
        factor_returns_weekly=None,
        cash_proxy_ticker="BIL",
        output_dir_csv=tmp_path,
    )
    p = tmp_path / "stress_scenario_analytics_summary.csv"
    assert p.exists()
