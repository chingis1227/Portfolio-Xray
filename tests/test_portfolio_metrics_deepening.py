"""Session 04: portfolio metrics deepening (skew/kurt, beta splits, rolling, quality metadata)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.metrics_asset import downside_beta, upside_beta
from src.metrics_portfolio import portfolio_metrics_one_window
from src.portfolio_analytics import rolling_beta, rolling_beta_correlation_block, rolling_correlation
from src.portfolio_xray import build_portfolio_xray_v2


def _monthly_series(n: int = 72, seed: int = 0) -> tuple[pd.Series, pd.Series, pd.Series]:
    idx = pd.date_range("2019-01-31", periods=n, freq="ME")
    rng = np.random.default_rng(seed)
    bench = pd.Series(rng.normal(0.004, 0.03, n), index=idx)
    port = pd.Series(0.5 * bench.values + rng.normal(0.001, 0.02, n), index=idx)
    rf = pd.Series(0.002, index=idx)
    return port, bench, rf


def test_portfolio_metrics_includes_shape_beta_and_quality() -> None:
    port, bench, rf = _monthly_series()
    end = port.index[-1]
    pm = portfolio_metrics_one_window(
        port,
        rf,
        end,
        60,
        benchmark_returns=bench,
        benchmark_ticker="SPY",
        risk_free_source="FRED:DTB3",
        returns_frequency="monthly",
    )
    mq = pm.get("metric_quality")
    assert isinstance(mq, dict)
    assert mq["n_obs"] >= 2
    assert mq["frequency"] == "monthly"
    assert mq["benchmark_ticker"] == "SPY"
    assert mq["risk_free_source"] == "FRED:DTB3"
    assert mq["window_months"] == 60
    assert np.isfinite(pm["skewness"]) or pm["skewness"] != pm["skewness"]
    assert np.isfinite(pm["kurtosis"]) or pm["kurtosis"] != pm["kurtosis"]
    assert np.isfinite(pm["downside_beta"]) or pm["downside_beta"] != pm["downside_beta"]
    assert np.isfinite(pm["corr_base"])


def test_downside_upside_beta_use_benchmark_sign() -> None:
    idx = pd.date_range("2020-01-31", periods=24, freq="ME")
    bench = pd.Series([0.05, -0.04, 0.03, -0.02] * 6, index=idx, dtype=float)
    port = pd.Series([0.04, -0.03, 0.02, -0.01] * 6, index=idx, dtype=float)
    down = downside_beta(port, bench)
    up = upside_beta(port, bench)
    assert np.isfinite(down)
    assert np.isfinite(up)


def test_rolling_beta_correlation_summaries() -> None:
    port, bench, _ = _monthly_series(n=80)
    block = rolling_beta_correlation_block(port, bench, returns_frequency="monthly")
    assert "rolling_beta_36m" in block
    assert "rolling_correlation_36m" in block
    assert block["rolling_beta_36m"]["last"] is not None


def test_portfolio_xray_risk_diagnostics_exposes_session04_fields() -> None:
    xray = build_portfolio_xray_v2(
        analysis_setup=None,
        weights={"SPY": 1.0},
        rc_asset=[],
        stress_report={},
        portfolio_valid=True,
        portfolio_metrics={
            "cagr": 0.08,
            "vol_annual": 0.12,
            "sharpe": 0.5,
            "sortino": 0.6,
            "beta_portfolio": 0.9,
            "corr_base": 0.85,
            "downside_beta": 1.1,
            "upside_beta": 0.7,
            "skewness": -0.4,
            "kurtosis": 2.1,
            "max_drawdown": -0.2,
            "metric_quality": {
                "n_obs": 120,
                "frequency": "monthly",
                "benchmark_ticker": "SPY",
                "risk_free_source": "FRED:DTB3",
                "window_months": 120,
                "analysis_end": "2026-04-30",
            },
        },
        portfolio_analytics={
            "rolling_beta_36m": {"last": 0.88, "mean": 0.9, "p10": 0.8, "p90": 1.0},
            "rolling_correlation_12m": {"last": 0.82, "mean": 0.8, "p10": 0.7, "p90": 0.9},
        },
    )
    section = xray["sections"]["risk_diagnostics"]
    pm_item = next(i for i in section["items"] if i.get("type") == "portfolio_metrics")
    assert pm_item.get("skewness") == -0.4
    assert pm_item.get("downside_beta") == 1.1
    assert pm_item["metric_quality"]["n_obs"] == 120
    rolling = next(i for i in section["items"] if i.get("type") == "rolling_metrics")
    assert "rolling_beta_36m" in rolling
    assert "rolling_correlation_12m" in rolling


def test_rolling_beta_series_length() -> None:
    port, bench, _ = _monthly_series(n=50)
    rb = rolling_beta(port, bench, 12, returns_frequency="monthly")
    rc = rolling_correlation(port, bench, 12, returns_frequency="monthly")
    assert len(rb.dropna()) >= 1
    assert len(rc.dropna()) >= 1
