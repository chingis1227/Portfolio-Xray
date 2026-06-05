"""
Fetch risk-free series from FRED (e.g. DTB3). Returns monthly effective rate at month-end.
"""
from __future__ import annotations

import io
import os
import socket
import time
from urllib.error import URLError
from urllib.request import urlopen

import pandas as pd

from src.pandas_compat import MONTH_END_FREQ


DEFAULT_FRED_TIMEOUT_SECONDS = 10.0
DEFAULT_FRED_RETRIES = 2
DEFAULT_FRED_RETRY_SLEEP_SECONDS = 0.5


def _fetch_fred_series_csv(
    series_id: str,
    start: str,
    end: str,
    *,
    timeout: float = DEFAULT_FRED_TIMEOUT_SECONDS,
) -> pd.Series:
    """Fetch FRED series via the public graph CSV endpoint (no pandas_datareader)."""
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        with urlopen(url, timeout=float(timeout)) as resp:
            raw = resp.read()
    except (URLError, TimeoutError, socket.timeout) as ex:
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
    *,
    timeout: float = DEFAULT_FRED_TIMEOUT_SECONDS,
    retries: int = DEFAULT_FRED_RETRIES,
    retry_sleep: float = DEFAULT_FRED_RETRY_SLEEP_SECONDS,
) -> pd.Series:
    """
    Fetch FRED series with bounded network waits and a small retry budget.

    The project uses the public FRED CSV endpoint first because it accepts a
    direct socket timeout. ``pandas_datareader`` remains as a compatibility
    fallback for non-timeout CSV failures, but all normal live fetches are now
    bounded by ``timeout`` and ``retries`` instead of waiting indefinitely.
    Returns Series with DatetimeIndex and annual percent (e.g. DTB3).
    """
    attempts = max(1, int(retries) + 1)
    last_exc: Exception | None = None
    for attempt in range(attempts):
        try:
            return _fetch_fred_series_csv(series_id, start, end, timeout=timeout)
        except Exception as exc:
            last_exc = exc
            if attempt < attempts - 1:
                time.sleep(max(0.0, float(retry_sleep)))

    # Compatibility fallback for callers that rely on pandas_datareader/FRED_API_KEY.
    # It is deliberately skipped for timeout-shaped CSV failures so a broken
    # network cannot hang the run after the bounded CSV attempts already failed.
    msg = str(last_exc or "").lower()
    if "timed out" in msg or "timeout" in msg:
        raise RuntimeError(
            f"FRED fetch timed out for {series_id} after {attempts} attempts "
            f"with timeout={float(timeout)}s"
        ) from last_exc

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
    except Exception as exc:
        raise RuntimeError(f"FRED download failed for {series_id}: {exc}") from exc


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
