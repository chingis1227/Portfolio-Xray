"""
Window end logic: analysis_end and slice_window.
Per metrics_specification: analysis_end = last effective month-end strictly before today.
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd


def get_analysis_end(monthly_index: pd.DatetimeIndex, today: datetime | pd.Timestamp | None = None) -> pd.Timestamp:
    """
    Return the last effective month-end strictly before today.

    Args:
        monthly_index: DatetimeIndex of month-end dates (e.g. from resampled prices).
        today: Reference date; if None, use datetime.now() (date only, no time).

    Returns:
        Single Timestamp: the maximum month-end in monthly_index that is < today.
    """
    if today is None:
        today = pd.Timestamp(datetime.now().date())
    else:
        today = pd.Timestamp(today).normalize()
    # Month-end dates in index that are strictly before today
    before = monthly_index[monthly_index < today]
    if len(before) == 0:
        raise ValueError(
            f"No month-end date in index strictly before today={today}. "
            "Ensure monthly series has at least one month-end before today."
        )
    return before.max()


def slice_window(
    series_or_df: pd.Series | pd.DataFrame,
    analysis_end: pd.Timestamp,
    window_months: int,
) -> pd.Series | pd.DataFrame:
    """
    Slice series or DataFrame to the window ending at analysis_end with length window_months.

    Window = [start_month, ..., analysis_end] inclusive, with exactly window_months observations
    (months). Start is chosen so that the number of month-end dates from start to analysis_end
    (inclusive) is window_months.

    Args:
        series_or_df: Data with DatetimeIndex (month-end).
        analysis_end: Last month-end of the window.
        window_months: Number of months in the window.

    Returns:
        Sliced series or DataFrame.
    """
    idx = series_or_df.index
    if not isinstance(idx, pd.DatetimeIndex):
        raise ValueError("series_or_df must have DatetimeIndex")
    # Find position of analysis_end (or last index <= analysis_end)
    end_loc = idx.get_indexer([analysis_end], method="ffill")[0]
    if end_loc < 0:
        end_loc = idx.get_indexer([analysis_end], method="bfill")[0]
    if end_loc < 0:
        raise ValueError(f"analysis_end {analysis_end} not in index")
    start_loc = max(0, end_loc - window_months + 1)
    return series_or_df.iloc[start_loc : end_loc + 1]
