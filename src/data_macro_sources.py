"""
Source resolver for macro indicators used by the two-axis macro regime classifier
(`macro_two_axis_v1`, see `docs/exec_plans/2026-05-05_macro_two_axis_regime_v1.md`
and `docs/docs/stress_testing_spec.md` §8.8.2).

Goals:
- Unified per-indicator source chain: FRED → Yahoo → official CSV → official API →
  keyed third-party API → manual CSV.
- Graceful degradation: any loader raising or returning empty data falls through to
  the next source; if every source fails, the indicator is marked `available=False`
  without raising.
- Manual-CSV fallback is always supported via either a fixed path
  ``cache/macro/<key>.csv`` or an env override ``<KEY>_CSV_PATH``.

Outputs are normalized to a monthly-friendly ``pd.Series`` (DatetimeIndex, float).
Caller-side transforms (in `src.stress_factors_macro`) take care of frequency
alignment (`level`, `m_over_m_change`, `three_m_avg_mom`, etc.).
"""
from __future__ import annotations

from dataclasses import dataclass, field
import logging
import os
from pathlib import Path
from typing import Any, Callable, Literal

import numpy as np
import pandas as pd

_LOG = logging.getLogger(__name__)

SourceKind = Literal[
    "fred",
    "yahoo",
    "official_csv",
    "official_api",
    "keyed_api",
    "manual_csv",
]

SOURCE_HIERARCHY: tuple[SourceKind, ...] = (
    "fred",
    "yahoo",
    "official_csv",
    "official_api",
    "keyed_api",
    "manual_csv",
)


@dataclass(frozen=True)
class SourceSpec:
    """A single concrete data source for an indicator.

    ``locator`` semantics depend on ``kind``:
        - fred: FRED series id (e.g. "PAYEMS").
        - yahoo: yfinance ticker (e.g. "CL=F" for WTI futures).
        - official_csv: HTTPS URL of an official CSV (Atlanta Fed / NY Fed / ISM).
        - official_api: URL or endpoint name of an official API.
        - keyed_api: vendor name; the indicator's `requires_env` declares the env vars
          carrying the API key. If any required env var is missing, the source is
          skipped (``available=False``) without raising.
        - manual_csv: relative path under the workspace (default
          ``cache/macro/<key>.csv``); ``<KEY>_CSV_PATH`` env var overrides.
    """

    kind: SourceKind
    locator: str
    requires_env: tuple[str, ...] = ()
    historical_only: bool = False


@dataclass(frozen=True)
class IndicatorSpec:
    """Static description of one macro indicator used by the regime classifier."""

    key: str
    block: str
    axis: Literal["growth", "inflation"]
    role: Literal["required", "optional"]
    sign: Literal["+", "-"]
    frequency: Literal["M", "Q"]
    transform: str
    source_chain: tuple[SourceSpec, ...]
    historical_only: bool = False  # propagated from any source flagged historical-only
    description: str = ""


def _empty_series() -> pd.Series:
    return pd.Series(dtype=float)


def _coerce_index(s: pd.Series) -> pd.Series:
    if s is None or len(s) == 0:
        return _empty_series()
    out = s.dropna().astype(float)
    out.index = pd.to_datetime(out.index, errors="coerce").tz_localize(None)
    out = out[~out.index.isna()]
    return out.sort_index()


def _load_fred(locator: str, start: str, end: str) -> pd.Series:
    try:
        from src.data_fred import fetch_fred_series

        s = fetch_fred_series(locator, start, end)
        return _coerce_index(s)
    except Exception as exc:
        _LOG.debug("FRED source %s failed: %s", locator, exc)
        return _empty_series()


def _load_yahoo(locator: str, start: str, end: str) -> pd.Series:
    try:
        from src.data_yf import fetch_daily

        df = fetch_daily(locator, start, end)
        if df is None or df.empty or "Close" not in df.columns:
            return _empty_series()
        return _coerce_index(df["Close"])
    except Exception as exc:
        _LOG.debug("Yahoo source %s failed: %s", locator, exc)
        return _empty_series()


def _load_official_csv(url: str, start: str, end: str) -> pd.Series:
    """Best-effort loader for small published official CSVs.

    Avoids long downloads in tests by short-circuiting when ``MACRO_OFFLINE`` is
    set. The caller-side `manual_csv` fallback is normally what is exercised in
    test/no-network environments.
    """

    if os.environ.get("MACRO_OFFLINE", "").strip():
        return _empty_series()
    try:
        df = pd.read_csv(url)
    except Exception as exc:
        _LOG.debug("official_csv %s failed: %s", url, exc)
        return _empty_series()
    return _df_to_value_series(df, start, end)


def _load_keyed_api(locator: str, requires_env: tuple[str, ...], start: str, end: str) -> pd.Series:
    missing = [k for k in requires_env if not os.environ.get(k)]
    if missing:
        _LOG.debug("keyed_api %s skipped: missing env %s", locator, missing)
        return _empty_series()
    # Stub: callers can extend with vendor-specific fetchers when the key is set.
    return _empty_series()


def _load_manual_csv(key: str, locator: str, start: str, end: str) -> pd.Series:
    """Manual CSV fallback.

    Resolution order:
        1. Environment override `<KEY>_CSV_PATH`.
        2. Locator from the SourceSpec (treated as workspace-relative if not absolute).
        3. Default ``cache/macro/<key>.csv``.

    Schema: at least two columns where the first is parseable as a date and the
    second is the indicator value. Extra columns are ignored. Header row is
    optional; if absent we name the first two columns ``date,value``.
    """

    env_path = os.environ.get(f"{key.upper()}_CSV_PATH")
    candidates: list[Path] = []
    if env_path:
        candidates.append(Path(env_path))
    if locator:
        candidates.append(Path(locator))
    candidates.append(Path("cache") / "macro" / f"{key}.csv")

    for path in candidates:
        try:
            if not path.is_file():
                continue
        except OSError:
            continue
        try:
            df = pd.read_csv(path)
        except Exception as exc:
            _LOG.debug("manual_csv %s failed: %s", path, exc)
            continue
        s = _df_to_value_series(df, start, end)
        if not s.empty:
            return s
    return _empty_series()


def _df_to_value_series(df: pd.DataFrame, start: str, end: str) -> pd.Series:
    if df is None or df.empty:
        return _empty_series()
    cols = list(df.columns)
    date_col: str | None = None
    val_col: str | None = None
    for c in cols:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            date_col = c
            break
    if date_col is None:
        for c in cols:
            try:
                pd.to_datetime(df[c], errors="raise")
                date_col = c
                break
            except Exception:
                continue
    if date_col is None:
        return _empty_series()
    for c in cols:
        if c == date_col:
            continue
        if pd.api.types.is_numeric_dtype(df[c]):
            val_col = c
            break
    if val_col is None:
        for c in cols:
            if c == date_col:
                continue
            try:
                pd.to_numeric(df[c], errors="raise")
                val_col = c
                break
            except Exception:
                continue
    if val_col is None:
        return _empty_series()
    s = pd.Series(
        pd.to_numeric(df[val_col], errors="coerce").values,
        index=pd.to_datetime(df[date_col], errors="coerce"),
        dtype=float,
    )
    s = _coerce_index(s)
    if start:
        s = s.loc[s.index >= pd.Timestamp(start)]
    if end:
        s = s.loc[s.index <= pd.Timestamp(end)]
    return s


_LOADERS: dict[SourceKind, Callable[..., pd.Series]] = {
    "fred": lambda spec, key, start, end: _load_fred(spec.locator, start, end),
    "yahoo": lambda spec, key, start, end: _load_yahoo(spec.locator, start, end),
    "official_csv": lambda spec, key, start, end: _load_official_csv(spec.locator, start, end),
    "official_api": lambda spec, key, start, end: _empty_series(),
    "keyed_api": lambda spec, key, start, end: _load_keyed_api(spec.locator, spec.requires_env, start, end),
    "manual_csv": lambda spec, key, start, end: _load_manual_csv(key, spec.locator, start, end),
}


def resolve_indicator(
    spec: IndicatorSpec,
    start: str,
    end: str,
    *,
    loaders: dict[SourceKind, Callable[..., pd.Series]] | None = None,
) -> tuple[pd.Series, dict[str, Any]]:
    """Walk the indicator's source_chain and return the first non-empty series.

    Returns (series, meta). When every source is empty, returns
    (empty Series, meta with available=False, source_used="unavailable",
    sources_attempted=[...]). Never raises.

    ``loaders`` is an optional override map used by tests to inject deterministic
    sources without network access.
    """

    use_loaders = loaders or _LOADERS
    attempted: list[dict[str, Any]] = []
    historical_only_seen = bool(spec.historical_only)
    for source in spec.source_chain:
        kind = source.kind
        loader = use_loaders.get(kind)
        if loader is None:
            attempted.append({"kind": kind, "status": "no_loader"})
            continue
        try:
            series = loader(source, spec.key, start, end)
        except Exception as exc:  # defensive: loaders should be fail-closed
            _LOG.debug("loader %s for %s raised: %s", kind, spec.key, exc)
            attempted.append({"kind": kind, "status": "error", "error": str(exc)})
            continue
        series = _coerce_index(series)
        if series.empty:
            attempted.append({"kind": kind, "status": "empty"})
            continue
        meta = {
            "available": True,
            "source_used": kind,
            "source_locator": source.locator,
            "sources_attempted": attempted + [{"kind": kind, "status": "ok"}],
            "frequency_native": spec.frequency,
            "last_observation_date": str(series.index[-1].date()),
            "first_observation_date": str(series.index[0].date()),
            "historical_only": bool(source.historical_only or historical_only_seen),
        }
        return series, meta

    return _empty_series(), {
        "available": False,
        "source_used": "unavailable",
        "source_locator": None,
        "sources_attempted": attempted,
        "frequency_native": spec.frequency,
        "last_observation_date": None,
        "first_observation_date": None,
        "historical_only": historical_only_seen,
    }


__all__ = [
    "IndicatorSpec",
    "SourceSpec",
    "SourceKind",
    "SOURCE_HIERARCHY",
    "resolve_indicator",
]
