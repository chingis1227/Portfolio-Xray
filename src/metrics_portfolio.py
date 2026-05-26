"""
Portfolio-level metrics (CAGR, Vol, Sharpe, Sortino, Beta, Treynor, MDD, etc.) from portfolio monthly returns.
Same formulas as asset metrics; uses equity curve on monthly simple returns for CAGR.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.metrics_asset import (
    beta_base,
    cagr_from_equity,
    corr_base,
    downside_beta,
    downside_deviation_annual,
    kurtosis_log,
    max_drawdown,
    sharpe,
    skewness_log,
    sortino,
    time_to_recovery,
    treynor,
    upside_beta,
    vol_annual,
)
from src.returns import equity_curve_simple
from src.utils import warn_insufficient_data

DDOF = 1


def log_returns_from_simple_monthly(monthly_simple_returns: pd.Series) -> pd.Series:
    """Monthly log returns from simple returns: ln(1 + r_t)."""
    r = monthly_simple_returns.dropna()
    if r.empty:
        return pd.Series(dtype=float)
    return np.log(1.0 + r)


def build_portfolio_metric_quality(
    *,
    n_obs: int,
    frequency: str,
    benchmark_ticker: str | None,
    risk_free_source: str | None,
    window_months: int,
    analysis_end: str,
) -> dict[str, Any]:
    """Quality/disclosure metadata for portfolio window metrics."""
    return {
        "n_obs": int(n_obs),
        "frequency": str(frequency),
        "benchmark_ticker": benchmark_ticker,
        "risk_free_source": risk_free_source,
        "window_months": int(window_months),
        "analysis_end": str(analysis_end),
    }


def portfolio_metrics_one_window(
    portfolio_returns: pd.Series,
    rf_monthly: pd.Series,
    analysis_end: pd.Timestamp,
    window_months: int,
    benchmark_returns: pd.Series | None = None,
    mar: float | None = None,
    *,
    periods_per_year: int = 12,
    benchmark_ticker: str | None = None,
    risk_free_source: str | None = None,
    returns_frequency: str = "monthly",
) -> dict[str, Any]:
    """Compute portfolio metrics for one window. Same definitions as asset metrics. mar=None => MAR = rf per period."""
    from src.windows import slice_calendar_window

    r_slice = slice_calendar_window(portfolio_returns, analysis_end, window_months)
    rf_slice = slice_calendar_window(rf_monthly, analysis_end, window_months)
    r_slice = r_slice.dropna()

    if benchmark_returns is not None and not benchmark_returns.empty:
        bench_slice = slice_calendar_window(benchmark_returns, analysis_end, window_months)
    else:
        bench_slice = pd.Series(dtype=float)

    available_months = len(r_slice)
    if periods_per_year == 12 and available_months < window_months:
        warn_insufficient_data("PORTFOLIO", window_months, available_months)

    ae_str = pd.Timestamp(analysis_end).strftime("%Y-%m-%d")

    if available_months < 2:
        return {
            "window_months": window_months,
            "cagr": np.nan,
            "vol_annual": np.nan,
            "sharpe": np.nan,
            "sortino": np.nan,
            "beta_portfolio": np.nan,
            "corr_base": np.nan,
            "downside_beta": np.nan,
            "upside_beta": np.nan,
            "skewness": np.nan,
            "kurtosis": np.nan,
            "treynor": np.nan,
            "downside_deviation": np.nan,
            "max_drawdown": np.nan,
            "ttr_months": np.nan,
            "recovered": False,
            "metric_quality": build_portfolio_metric_quality(
                n_obs=available_months,
                frequency=returns_frequency,
                benchmark_ticker=benchmark_ticker,
                risk_free_source=risk_free_source,
                window_months=window_months,
                analysis_end=ae_str,
            ),
        }

    beta_val = beta_base(r_slice, bench_slice, ddof=DDOF) if not bench_slice.empty else np.nan
    treynor_val = (
        treynor(r_slice, rf_slice, bench_slice, beta_val, ddof=DDOF, periods_per_year=periods_per_year)
        if not bench_slice.empty
        else np.nan
    )
    corr_val = corr_base(r_slice, bench_slice) if not bench_slice.empty else np.nan
    down_beta = downside_beta(r_slice, bench_slice, ddof=DDOF) if not bench_slice.empty else np.nan
    up_beta = upside_beta(r_slice, bench_slice, ddof=DDOF) if not bench_slice.empty else np.nan
    lr_slice = log_returns_from_simple_monthly(r_slice)

    ttr_months, recovered = time_to_recovery(r_slice)

    return {
        "window_months": window_months,
        "cagr": cagr_from_equity(r_slice, window_months, periods_per_year=periods_per_year),
        "vol_annual": vol_annual(r_slice, ddof=DDOF, periods_per_year=periods_per_year),
        "sharpe": sharpe(r_slice, rf_slice, ddof=DDOF, periods_per_year=periods_per_year),
        "sortino": sortino(r_slice, rf_slice, mar=mar, ddof=DDOF, periods_per_year=periods_per_year),
        "beta_portfolio": beta_val,
        "corr_base": corr_val,
        "downside_beta": down_beta,
        "upside_beta": up_beta,
        "skewness": skewness_log(lr_slice),
        "kurtosis": kurtosis_log(lr_slice),
        "treynor": treynor_val,
        "downside_deviation": downside_deviation_annual(
            r_slice, rf_slice, mar=mar, periods_per_year=periods_per_year
        ),
        "max_drawdown": max_drawdown(r_slice)[0],
        "ttr_months": ttr_months if ttr_months is not None else np.nan,
        "recovered": recovered,
        "metric_quality": build_portfolio_metric_quality(
            n_obs=available_months,
            frequency=returns_frequency,
            benchmark_ticker=benchmark_ticker,
            risk_free_source=risk_free_source,
            window_months=window_months,
            analysis_end=ae_str,
        ),
    }
