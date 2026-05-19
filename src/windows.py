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


def slice_calendar_window(
    series_or_df: pd.Series | pd.DataFrame,
    analysis_end: pd.Timestamp,
    horizon_months: int,
) -> pd.Series | pd.DataFrame:
    """
    Calendar window (start, analysis_end] with start = analysis_end - horizon_months.

    All observations strictly after start and on or before analysis_end are included.
    The number of rows may be less than horizon_months if the index has gaps.
    """
    idx = series_or_df.index
    if not isinstance(idx, pd.DatetimeIndex):
        raise ValueError("series_or_df must have DatetimeIndex")
    ae = pd.Timestamp(analysis_end).normalize()
    start = ae - pd.DateOffset(months=int(horizon_months))
    mask = (idx > start) & (idx <= ae)
    return series_or_df.loc[mask]


def slice_window(
    series_or_df: pd.Series | pd.DataFrame,
    analysis_end: pd.Timestamp,
    window_months: int,
) -> pd.Series | pd.DataFrame:
    """
    Slice to the calendar window ending at analysis_end (see slice_calendar_window).

    Deprecated row-count semantics: callers should treat window_months as calendar horizon.
    """
    return slice_calendar_window(series_or_df, analysis_end, window_months)


def truncate_to_analysis_end(
    series_or_df: pd.Series | pd.DataFrame,
    analysis_end: pd.Timestamp | str,
) -> pd.Series | pd.DataFrame:
    """
    Keep rows on or before analysis_end (analysis-effective panel).

    Raw cached return panels may include later incomplete period stamps; diagnostic
    consumers and reproducibility exports must use this helper (or equivalent) before
    computing or disclosing ``data_end``.
    """
    if series_or_df is None or len(series_or_df) == 0:
        return series_or_df
    idx = series_or_df.index
    if not isinstance(idx, pd.DatetimeIndex):
        raise ValueError("series_or_df must have DatetimeIndex")
    ae = pd.Timestamp(analysis_end).normalize()
    mask = idx <= ae
    return series_or_df.loc[mask]
