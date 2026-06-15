"""
Fetch risk-free series from FRED (e.g. DTB3). Returns monthly effective rate at month-end.
"""
from __future__ import annotations

import io
import os
import socket
import time
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd

from src.pandas_compat import MONTH_END_FREQ


DEFAULT_FRED_TIMEOUT_SECONDS = 10.0
DEFAULT_FRED_RETRIES = 2
DEFAULT_FRED_RETRY_SLEEP_SECONDS = 0.5
FRED_API_OBSERVATIONS_URL = "https://api.stlouisfed.org/fred/series/observations"
FRED_CSV_GRAPH_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
_FRED_SERIES_MEMORY_CACHE: dict[tuple[str, str, str, bool, float, int], pd.Series] = {}


def clear_fred_series_memory_cache() -> None:
    """Clear process-local FRED cache; primarily useful for tests."""

    _FRED_SERIES_MEMORY_CACHE.clear()


def _copy_series(series: pd.Series) -> pd.Series:
    copied = series.copy(deep=True)
    copied.attrs = dict(getattr(series, "attrs", {}) or {})
    return copied


def _fred_api_key(api_key: str | None = None) -> str | None:
    key = (api_key or os.environ.get("FRED_API_KEY") or "").strip()
    return key or None


def _read_url(url: str, *, timeout: float) -> bytes:
    try:
        with urlopen(url, timeout=float(timeout)) as resp:
            return resp.read()
    except (URLError, TimeoutError, socket.timeout) as ex:
        raise RuntimeError(f"FRED download failed: {ex}") from ex


def _parse_fred_values_frame(df: pd.DataFrame, series_id: str) -> pd.Series:
    if df.empty:
        return pd.Series(dtype=float)
    date_col = "observation_date" if "observation_date" in df.columns else "date" if "date" in df.columns else df.columns[0]
    col = series_id if series_id in df.columns else "value" if "value" in df.columns else df.columns[-1]
    values = pd.to_numeric(df[col].replace(".", pd.NA), errors="coerce")
    dates = pd.DatetimeIndex(pd.to_datetime(df[date_col])).tz_localize(None)
    s = pd.Series(values.to_numpy(), index=dates, name=series_id)
    return s.dropna().astype(float)


def _attach_source_attrs(series: pd.Series, *, source_used: str, warnings: list[str] | None = None) -> pd.Series:
    out = series.copy()
    out.attrs["source_used"] = source_used
    out.attrs["fred_source_used"] = source_used
    if warnings:
        out.attrs["warnings"] = list(warnings)
        out.attrs["fred_warnings"] = list(warnings)
    return out


def _fetch_fred_series_api(
    series_id: str,
    start: str,
    end: str,
    *,
    api_key: str,
    timeout: float = DEFAULT_FRED_TIMEOUT_SECONDS,
) -> pd.Series:
    """Fetch FRED observations through the official API endpoint."""
    query = {
        "series_id": str(series_id),
        "api_key": str(api_key),
        "file_type": "json",
    }
    if start:
        query["observation_start"] = str(pd.Timestamp(start).date())
    if end:
        query["observation_end"] = str(pd.Timestamp(end).date())
    url = FRED_API_OBSERVATIONS_URL + "?" + urlencode(query)
    raw = _read_url(url, timeout=timeout)
    import json

    parsed = json.loads(raw.decode("utf-8"))
    if "error_message" in parsed:
        raise RuntimeError(f"FRED API failed for {series_id}: {parsed['error_message']}")
    df = pd.DataFrame(parsed.get("observations", []))
    return _parse_fred_values_frame(df, series_id)


def _fetch_fred_series_csv(
    series_id: str,
    start: str,
    end: str,
    *,
    timeout: float = DEFAULT_FRED_TIMEOUT_SECONDS,
) -> pd.Series:
    """Fetch FRED series via the public graph CSV endpoint (no pandas_datareader)."""
    query = {"id": str(series_id)}
    if start:
        query["cosd"] = str(pd.Timestamp(start).date())
    if end:
        query["coed"] = str(pd.Timestamp(end).date())
    url = FRED_CSV_GRAPH_URL + "?" + urlencode(query)
    try:
        raw = _read_url(url, timeout=timeout)
    except Exception as ex:
        raise RuntimeError(f"FRED CSV download failed for {series_id}: {ex}") from ex
    df = pd.read_csv(io.BytesIO(raw))
    s = _parse_fred_values_frame(df, series_id)
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

    Policy: when ``FRED_API_KEY`` is available, the official FRED API is the
    primary source. The public graph CSV endpoint is only an explicit fallback
    when no API key is configured or when the API request fails. The returned
    Series carries ``source_used``/``fred_source_used`` attrs:
    ``fred_api`` or ``fred_csv_fallback``.
    Returns Series with DatetimeIndex and annual percent (e.g. DTB3).
    """
    attempts = max(1, int(retries) + 1)
    last_exc: Exception | None = None
    key = _fred_api_key(api_key)
    cache_key = (str(series_id), str(start), str(end), bool(key), float(timeout), int(retries))
    cached = _FRED_SERIES_MEMORY_CACHE.get(cache_key)
    if cached is not None:
        return _copy_series(cached)
    warnings: list[str] = []

    if key:
        for attempt in range(attempts):
            try:
                series = _attach_source_attrs(
                    _fetch_fred_series_api(series_id, start, end, api_key=key, timeout=timeout),
                    source_used="fred_api",
                )
                _FRED_SERIES_MEMORY_CACHE[cache_key] = _copy_series(series)
                return series
            except Exception as exc:
                last_exc = exc
                if attempt < attempts - 1:
                    time.sleep(max(0.0, float(retry_sleep)))
        warnings.append(f"fred_api_failed_csv_fallback:{type(last_exc).__name__}:{last_exc}")
    else:
        warnings.append("fred_api_key_missing_csv_fallback")

    for attempt in range(attempts):
        try:
            series = _attach_source_attrs(
                _fetch_fred_series_csv(series_id, start, end, timeout=timeout),
                source_used="fred_csv_fallback",
                warnings=warnings,
            )
            _FRED_SERIES_MEMORY_CACHE[cache_key] = _copy_series(series)
            return series
        except Exception as exc:
            last_exc = exc
            if attempt < attempts - 1:
                time.sleep(max(0.0, float(retry_sleep)))

    msg = str(last_exc or "").lower()
    if "timed out" in msg or "timeout" in msg:
        raise RuntimeError(
            f"FRED fetch timed out for {series_id} after {attempts} attempts "
            f"with timeout={float(timeout)}s; source_used=fred_csv_fallback"
        ) from last_exc

    raise RuntimeError(f"FRED download failed for {series_id}; source_used=fred_csv_fallback: {last_exc}") from last_exc


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
