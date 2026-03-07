"""
Resample daily prices to effective month-end: last available trading day of each month.
No interpolation of asset returns; only calendar alignment.
"""
from __future__ import annotations

import pandas as pd


def to_month_end(daily_series: pd.Series) -> pd.Series:
    """
    Resample to effective month-end: for each month, take the last available value
    (last trading day of that month). Uses 'ME' (month end) and last().
    """
    return daily_series.resample("ME").last().dropna()


def to_month_end_df(daily_df: pd.DataFrame) -> pd.DataFrame:
    """Resample each column to effective month-end (last available per month)."""
    return daily_df.resample("ME").last().dropna(how="all")
