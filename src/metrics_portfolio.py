"""
Portfolio-level metrics (CAGR, Vol, Sharpe, Sortino, Beta, Treynor, MDD, etc.) from portfolio monthly returns.
Same formulas as asset metrics; uses equity curve on monthly simple returns for CAGR.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.metrics_asset import (
    beta_base,
    cagr_from_equity,
    max_drawdown,
    sharpe,
    sortino,
    time_to_recovery,
    treynor,
    vol_annual,
)
from src.returns import equity_curve_simple
from src.utils import warn_insufficient_data

DDOF = 1


def portfolio_metrics_one_window(
    portfolio_returns: pd.Series,
    rf_monthly: pd.Series,
    analysis_end: pd.Timestamp,
    window_months: int,
    benchmark_returns: pd.Series | None = None,
    mar: float | None = None,
    *,
    periods_per_year: int = 12,
) -> dict[str, float | bool]:
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

    if available_months < 2:
        return {
            "window_months": window_months,
            "cagr": np.nan,
            "vol_annual": np.nan,
            "sharpe": np.nan,
            "sortino": np.nan,
            "beta_portfolio": np.nan,
            "treynor": np.nan,
            "max_drawdown": np.nan,
            "ttr_months": np.nan,
            "recovered": False,
        }

    beta_val = beta_base(r_slice, bench_slice, ddof=DDOF) if not bench_slice.empty else np.nan
    treynor_val = (
        treynor(r_slice, rf_slice, bench_slice, beta_val, ddof=DDOF, periods_per_year=periods_per_year)
        if not bench_slice.empty
        else np.nan
    )

    return {
        "window_months": window_months,
        "cagr": cagr_from_equity(r_slice, window_months, periods_per_year=periods_per_year),
        "vol_annual": vol_annual(r_slice, ddof=DDOF, periods_per_year=periods_per_year),
        "sharpe": sharpe(r_slice, rf_slice, ddof=DDOF, periods_per_year=periods_per_year),
        "sortino": sortino(r_slice, rf_slice, mar=mar, ddof=DDOF, periods_per_year=periods_per_year),
        "beta_portfolio": beta_val,
        "treynor": treynor_val,
        "max_drawdown": max_drawdown(r_slice)[0],
        "ttr_months": time_to_recovery(r_slice)[0] or np.nan,
        "recovered": time_to_recovery(r_slice)[1],
    }
