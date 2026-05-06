"""Unit tests for macro indicator transforms, sign map and registry layout."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src import stress_factors_macro as sfm
from src.pandas_compat import MONTH_END_FREQ


def _daily_index(n: int, start: str = "2018-01-01") -> pd.DatetimeIndex:
    return pd.date_range(start=start, periods=n, freq="B")


def _monthly_index(n: int, start: str = "2018-01-31") -> pd.DatetimeIndex:
    return pd.date_range(start=start, periods=n, freq=MONTH_END_FREQ)


# ---------------------------------------------------------------------------
# Sign map / registry hygiene
# ---------------------------------------------------------------------------


def test_registry_signs_match_growth_inflation_axes() -> None:
    expected_negative_growth = {"unrate", "hy_oas", "nfci"}
    for spec in sfm.INDICATORS:
        if spec.key in expected_negative_growth:
            assert spec.sign == "-", spec.key
            assert spec.axis == "growth"
        else:
            assert spec.sign == "+", spec.key


def test_registry_blocks_cover_five_per_axis() -> None:
    growth_blocks = {s.block for s in sfm.INDICATORS if s.axis == "growth"}
    inflation_blocks = {s.block for s in sfm.INDICATORS if s.axis == "inflation"}
    assert growth_blocks == set(sfm.GROWTH_BLOCKS)
    assert inflation_blocks == set(sfm.INFLATION_BLOCKS)
    optional_keys = {s.key for s in sfm.INDICATORS if s.role == "optional"}
    # Optional indicators include the planned ISM / nowcast set.
    assert {"ism_manuf_pmi", "ism_services_pmi", "gdpnow", "ny_fed_nowcast"}.issubset(
        optional_keys
    )


def test_optional_blocks_set_includes_growth_nowcast() -> None:
    assert "growth_nowcast" in sfm.OPTIONAL_BLOCKS


# ---------------------------------------------------------------------------
# Transforms
# ---------------------------------------------------------------------------


def test_three_m_avg_mom_for_payems() -> None:
    idx = _monthly_index(8)
    raw = pd.Series([100, 101, 103, 104, 110, 105, 106, 109], index=idx)
    out = sfm.apply_transform("three_m_avg_mom", raw)
    momentum = out["momentum"]
    # Expected M/M change: NaN, 1, 2, 1, 6, -5, 1, 3
    # 3m avg of [1,2,1] at idx[3] = (1+2+1)/3 = 1.333...
    assert pytest.approx(float(momentum.iloc[3]), rel=1e-6) == 4.0 / 3.0
    # 3m avg of [-5,1,3] at idx[7] = -1/3
    assert pytest.approx(float(momentum.iloc[7]), rel=1e-6) == -1.0 / 3.0


def test_three_m_change_for_unrate() -> None:
    idx = _monthly_index(6)
    raw = pd.Series([3.5, 3.6, 3.7, 4.1, 4.4, 5.2], index=idx)
    out = sfm.apply_transform("three_m_change", raw)
    momentum = out["momentum"]
    assert pytest.approx(float(momentum.iloc[3]), rel=1e-6) == 4.1 - 3.5
    assert pytest.approx(float(momentum.iloc[5]), rel=1e-6) == 5.2 - 3.7


def test_three_m_annualized_for_core_cpi() -> None:
    idx = _monthly_index(6)
    raw = pd.Series([100.0, 101.0, 102.5, 103.8, 105.0, 106.2], index=idx)
    out = sfm.apply_transform("three_m_annualized", raw)
    momentum = out["momentum"]
    expected_idx_3 = (103.8 / 100.0) ** 4 - 1.0
    assert pytest.approx(float(momentum.iloc[3]), rel=1e-6) == expected_idx_3


def test_three_m_yoy_for_real_pce() -> None:
    idx = _monthly_index(15)
    raw = pd.Series(np.linspace(100.0, 110.0, num=15), index=idx)
    out = sfm.apply_transform("three_m_yoy", raw)
    momentum = out["momentum"].dropna()
    assert not momentum.empty
    assert (momentum.iloc[-3:] > 0).all()


def test_oil_monthly_avg_three_m_change_uses_monthly_average() -> None:
    """Daily WTI prices must be aggregated by monthly mean before 3m diff."""

    idx = _daily_index(180)
    np.random.seed(1)
    daily = pd.Series(
        np.linspace(60.0, 90.0, num=180) + np.random.default_rng(1).normal(scale=2.0, size=180),
        index=idx,
    )
    out = sfm.apply_transform("oil_monthly_avg_three_m_change", daily)
    level = out["level"]
    momentum = out["momentum"]
    monthly_avg_manual = daily.resample(MONTH_END_FREQ).mean()
    pd.testing.assert_series_equal(
        level.dropna(), monthly_avg_manual.dropna(), check_names=False
    )
    expected_diff = monthly_avg_manual.diff(3).dropna()
    pd.testing.assert_series_equal(
        momentum.dropna(), expected_diff.dropna(), check_names=False
    )


def test_quarterly_ffill_monthly_yoy_for_eci() -> None:
    """ECI is quarterly; transform should ffill to monthly and apply 12m yoy."""

    quarterly_idx = pd.date_range("2015-03-31", periods=24, freq="QE")
    raw = pd.Series(np.linspace(100.0, 130.0, num=len(quarterly_idx)), index=quarterly_idx)
    out = sfm.apply_transform("quarterly_ffill_monthly_yoy", raw)
    level = out["level"]
    momentum = out["momentum"]
    # Resampled to monthly frequency.
    assert level.index.inferred_freq in {"M", "ME"}
    # Forward fill: every quarter end value must repeat to next quarter end.
    q_jun = pd.Timestamp("2016-06-30")
    q_jul = pd.Timestamp("2016-07-31")
    assert pytest.approx(level.loc[q_jul]) == level.loc[q_jun]
    # YoY momentum shifts by 12 monthly rows.
    assert momentum.iloc[24] == pytest.approx(level.iloc[24] / level.iloc[12] - 1.0, rel=1e-9)


# ---------------------------------------------------------------------------
# fetch_macro_indicators with stub resolver — graceful when sources fail
# ---------------------------------------------------------------------------


def test_fetch_macro_indicators_handles_partial_availability() -> None:
    idx = _monthly_index(160)

    def fake_resolver(spec, start, end):
        if spec.key in {"payems", "unrate", "core_cpi_3m_ann"}:
            series = pd.Series(np.linspace(100, 200, num=len(idx)), index=idx)
            return series, {
                "available": True,
                "source_used": "fred",
                "source_locator": spec.source_chain[0].locator,
                "frequency_native": spec.frequency,
                "last_observation_date": str(idx[-1].date()),
                "first_observation_date": str(idx[0].date()),
                "historical_only": False,
            }
        return pd.Series(dtype=float), {
            "available": False,
            "source_used": "unavailable",
            "frequency_native": spec.frequency,
            "historical_only": spec.historical_only,
        }

    panel, meta = sfm.fetch_macro_indicators("2010-01-01", "2026-01-01", resolver=fake_resolver)
    assert "payems__level" in panel.columns
    assert "unrate__level" in panel.columns
    assert meta["data_sources_used"]["payems"] == "fred"
    assert meta["data_sources_used"]["gdpnow"] == "unavailable"
    assert "payems" in meta["available_indicators"]
    assert "gdpnow" in meta["unavailable_indicators"]
