"""
Monthly simple and log returns from month-end prices. Never interpolate asset returns.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def simple_returns(month_end_prices: pd.Series) -> pd.Series:
    """r_t = P_t / P_{t-1} - 1. First period is NaN."""
    return month_end_prices.pct_change(fill_method=None).dropna()


def log_returns(month_end_prices: pd.Series) -> pd.Series:
    """lr_t = ln(P_t / P_{t-1}). First period is NaN."""
    return np.log(month_end_prices / month_end_prices.shift(1)).dropna()


def simple_returns_df(month_end_prices: pd.DataFrame) -> pd.DataFrame:
    """Simple returns for each column. First row NaN then dropped per column."""
    return month_end_prices.pct_change(fill_method=None).dropna(how="all")


def log_returns_df(month_end_prices: pd.DataFrame) -> pd.DataFrame:
    """Log returns for each column."""
    return np.log(month_end_prices / month_end_prices.shift(1)).dropna(how="all")


def equity_curve_simple(monthly_simple_returns: pd.Series) -> pd.Series:
    """Equity = cumprod(1 + r_simple). First value is (1+r_0), so Equity_start=1.0 for CAGR."""
    r = monthly_simple_returns.dropna()
    return (1 + r).cumprod()
