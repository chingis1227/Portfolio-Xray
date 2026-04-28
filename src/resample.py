"""
Resample daily prices to effective month-end: last available trading day of each month.
No interpolation of asset returns; only calendar alignment.
"""
from __future__ import annotations

import pandas as pd

from src.pandas_compat import MONTH_END_FREQ


def to_month_end(daily_series: pd.Series) -> pd.Series:
    """
    Resample to effective month-end: for each month, take the last available value
    (last trading day of that month). Uses the active month-end frequency and last().
    """
    return daily_series.resample(MONTH_END_FREQ).last().dropna()


def to_month_end_df(daily_df: pd.DataFrame) -> pd.DataFrame:
    """Resample each column to effective month-end (last available per month)."""
    return daily_df.resample(MONTH_END_FREQ).last().dropna(how="all")
