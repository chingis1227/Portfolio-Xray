"""Tests for `src.data_macro_sources.resolve_indicator` source-chain semantics."""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
import pytest

from src.data_macro_sources import (
    IndicatorSpec,
    SourceSpec,
    resolve_indicator,
)


def _spec(*, source_chain: tuple[SourceSpec, ...], requires_env: tuple[str, ...] = ()) -> IndicatorSpec:
    return IndicatorSpec(
        key="test_indicator",
        block="growth_labor",
        axis="growth",
        role="optional",
        sign="+",
        frequency="M",
        transform="level_and_three_m_change",
        source_chain=source_chain,
    )


def test_walks_chain_and_returns_first_non_empty_source() -> None:
    spec = _spec(
        source_chain=(
            SourceSpec(kind="fred", locator="FAKE_FRED"),
            SourceSpec(kind="yahoo", locator="FAKE_TICKER"),
            SourceSpec(kind="manual_csv", locator=""),
        ),
    )

    series_yahoo = pd.Series(
        [1.0, 2.0, 3.0],
        index=pd.date_range("2020-01-01", periods=3, freq="MS"),
    )

    def loader_fred(source, key, start, end):
        return pd.Series(dtype=float)

    def loader_yahoo(source, key, start, end):
        return series_yahoo

    def loader_manual(source, key, start, end):
        return pd.Series(dtype=float)

    series, meta = resolve_indicator(
        spec,
        "2010-01-01",
        "2025-01-01",
        loaders={
            "fred": loader_fred,
            "yahoo": loader_yahoo,
            "manual_csv": loader_manual,
        },
    )

    assert meta["available"] is True
    assert meta["source_used"] == "yahoo"
    assert len(series) == 3
    fred_attempt, yahoo_attempt = meta["sources_attempted"][:2]
    assert fred_attempt == {"kind": "fred", "status": "empty"}
    assert yahoo_attempt["kind"] == "yahoo" and yahoo_attempt["status"] == "ok"


def test_skips_keyed_api_when_env_missing() -> None:
    env_var = "MACRO_TEST_NONEXISTENT_KEY_XYZ"
    os.environ.pop(env_var, None)
    spec = _spec(
        source_chain=(
            SourceSpec(kind="keyed_api", locator="vendor", requires_env=(env_var,)),
            SourceSpec(kind="manual_csv", locator=""),
        ),
    )

    def loader_manual(source, key, start, end):
        return pd.Series(dtype=float)

    series, meta = resolve_indicator(
        spec,
        "2010-01-01",
        "2025-01-01",
        loaders={"manual_csv": loader_manual},
    )

    assert meta["available"] is False
    # The keyed_api attempt was internally skipped via the missing env var: its
    # default loader returns empty without raising. The fallback chain still
    # records each step.
    assert any(att["kind"] == "manual_csv" for att in meta["sources_attempted"])


def test_failing_loader_does_not_crash_chain() -> None:
    spec = _spec(
        source_chain=(
            SourceSpec(kind="fred", locator="FAKE"),
            SourceSpec(kind="manual_csv", locator=""),
        ),
    )

    def boom(source, key, start, end):
        raise RuntimeError("network down")

    fallback = pd.Series(
        [10.0],
        index=pd.date_range("2020-01-31", periods=1, freq="ME"),
    )

    def manual_loader(source, key, start, end):
        return fallback

    series, meta = resolve_indicator(
        spec,
        "2010-01-01",
        "2025-01-01",
        loaders={"fred": boom, "manual_csv": manual_loader},
    )

    assert meta["available"] is True
    assert meta["source_used"] == "manual_csv"
    fred_attempt = meta["sources_attempted"][0]
    assert fred_attempt["kind"] == "fred"
    assert fred_attempt["status"] == "error"


def test_historical_only_flag_propagates_from_source() -> None:
    spec = _spec(
        source_chain=(
            SourceSpec(kind="manual_csv", locator="", historical_only=True),
        ),
    )

    fallback = pd.Series(
        [1.0, 2.0],
        index=pd.date_range("2018-01-31", periods=2, freq="ME"),
    )

    def manual_loader(source, key, start, end):
        return fallback

    _, meta = resolve_indicator(
        spec,
        "2010-01-01",
        "2025-01-01",
        loaders={"manual_csv": manual_loader},
    )

    assert meta["available"] is True
    assert meta["historical_only"] is True


def test_unavailable_when_all_loaders_empty() -> None:
    spec = _spec(
        source_chain=(
            SourceSpec(kind="fred", locator="X"),
            SourceSpec(kind="manual_csv", locator=""),
        ),
    )

    def empty(*args, **kwargs):
        return pd.Series(dtype=float)

    series, meta = resolve_indicator(
        spec,
        "2010-01-01",
        "2025-01-01",
        loaders={"fred": empty, "manual_csv": empty},
    )

    assert series.empty
    assert meta["available"] is False
    assert meta["source_used"] == "unavailable"
    assert meta["last_observation_date"] is None
