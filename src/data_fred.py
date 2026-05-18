"""
Fetch risk-free series from FRED (e.g. DTB3). Returns monthly effective rate at month-end.
"""
from __future__ import annotations

import io
import os
from urllib.error import URLError
from urllib.request import urlopen

import pandas as pd

from src.pandas_compat import MONTH_END_FREQ


def _fetch_fred_series_csv(series_id: str, start: str, end: str) -> pd.Series:
    """Fetch FRED series via the public graph CSV endpoint (no pandas_datareader)."""
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        with urlopen(url, timeout=60) as resp:
            raw = resp.read()
    except URLError as ex:
        raise RuntimeError(f"FRED CSV download failed for {series_id}: {ex}") from ex
    df = pd.read_csv(io.BytesIO(raw))
    if df.empty:
        return pd.Series(dtype=float)
    date_col = "observation_date" if "observation_date" in df.columns else df.columns[0]
    col = series_id if series_id in df.columns else df.columns[-1]
    s = df.set_index(date_col)[col].astype(float)
    s.index = pd.to_datetime(s.index).tz_localize(None)
    s = s.dropna()
    if start:
        s = s.loc[s.index >= pd.Timestamp(start)]
    if end:
        s = s.loc[s.index <= pd.Timestamp(end)]
    return s


def fetch_fred_series(
    series_id: str,
    start: str,
    end: str,
    api_key: str | None = None,
) -> pd.Series:
    """
    Fetch FRED series. If pandas_datareader is available, uses it; else optional API key for direct FRED call.
    Returns Series with DatetimeIndex and annual percent (e.g. DTB3).
    """
    try:
        from pandas_datareader import get_data_fred

        key = api_key or os.environ.get("FRED_API_KEY")
        if key:
            os.environ["FRED_API_KEY"] = key
        df = get_data_fred(series_id, start=start, end=end)
        if df is None or df.empty:
            return pd.Series(dtype=float)
        if isinstance(df, pd.DataFrame):
            col = df.columns[0]
            s = df[col]
        else:
            s = df
        s = s.dropna()
        s.index = pd.to_datetime(s.index).tz_localize(None)
        return s.astype(float)
    except Exception:
        return _fetch_fred_series_csv(series_id, start, end)


def annual_percent_to_monthly_effective(annual_pct: pd.Series) -> pd.Series:
    """
    Convert FRED-style annual percent (e.g. 5.0 for 5%) to monthly effective rate.
    rf_monthly = (1 + y/100)^(1/12) - 1
    """
    return (1 + annual_pct / 100) ** (1 / 12) - 1


def resample_rf_to_month_end(rf_daily_or_irregular: pd.Series) -> pd.Series:
    """
    Resample to month-end: last available value in each month.
    """
    return rf_daily_or_irregular.resample(MONTH_END_FREQ).last().dropna()
