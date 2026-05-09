"""Unit tests for multi-frequency returns helpers and rolling analytics."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.portfolio_analytics import rolling_sharpe, rolling_vol_annual
from src.returns_frequency import (
    calendar_window_to_n_periods,
    compute_frequency_disclosure,
    normalize_returns_frequency,
    per_period_eff_from_annual_simple,
    periods_per_year,
    rf_series_annual_pct_to_returns_frequency,
)
from src.windows import slice_calendar_window


def test_normalize_returns_frequency_default_and_enum() -> None:
    assert normalize_returns_frequency(None) == "monthly"
    assert normalize_returns_frequency("WEEKLY") == "weekly"
    assert normalize_returns_frequency("daily") == "daily"
    with pytest.raises(ValueError):
        normalize_returns_frequency("hourly")


def test_periods_per_year_and_calendar_window_mapping() -> None:
    assert periods_per_year("monthly") == 12
    assert periods_per_year("weekly") == 52
    assert periods_per_year("daily") == 252
    assert calendar_window_to_n_periods(36, "monthly") == 36
    assert calendar_window_to_n_periods(12, "weekly") == 52  # rounded
    wm = calendar_window_to_n_periods(36, "daily")
    assert wm >= 750  # ~3y trading days


def test_per_period_mar_compounding_weekly_vs_monthly() -> None:
    mar_a = 0.06  # 6% annual simple
    m = per_period_eff_from_annual_simple(mar_a, "monthly")
    w = per_period_eff_from_annual_simple(mar_a, "weekly")
    assert abs((1 + m) ** 12 - 1.06) < 1e-9
    assert abs((1 + w) ** 52 - 1.06) < 1e-9
    assert m > w


def test_frequency_disclosure_quiet_monthly_mismatch_legacy() -> None:
    fd = compute_frequency_disclosure(
        returns_frequency="monthly",
        factor_stress_frequency="weekly",
        macro_regime_frequency="monthly",
    )
    assert fd["frequency_mismatch_warning"] is False


def test_frequency_disclosure_warns_weekly_vs_stress_weekly_but_monthly_macro() -> None:
    fd = compute_frequency_disclosure(
        returns_frequency="weekly",
        optimization_frequency="weekly",
        factor_stress_frequency="weekly",
        macro_regime_frequency="monthly",
    )
    assert fd["frequency_mismatch_warning"] is True


def test_rf_series_annual_pct_to_returns_frequency_monthly_shapes() -> None:
    idx = pd.date_range("2020-01-01", periods=400, freq="D")
    s = pd.Series(5.0, index=idx)
    rm = rf_series_annual_pct_to_returns_frequency(s, freq="monthly")
    rw = rf_series_annual_pct_to_returns_frequency(s, freq="weekly")
    assert len(rm) >= 12
    assert len(rw) >= 52
    assert float(rm.iloc[0]) > 0 and float(rw.iloc[0]) > 0


def test_slice_calendar_window_truncates_monthly_series() -> None:
    ix = pd.date_range("2020-01-31", periods=24, freq="ME")
    r = pd.Series(np.linspace(-0.01, 0.02, len(ix)), index=ix)
    end = ix[-6]
    sl = slice_calendar_window(r, end, 120)
    assert len(sl) <= len(r)


def test_rolling_sharpe_respects_calendar_weekly_window_lengths() -> None:
    rng = pd.date_range("2018-01-05", periods=520, freq="W-FRI")
    pr = pd.Series(np.random.default_rng(0).normal(0.001, 0.02, len(rng)), index=rng)
    rf = pd.Series(0.0001, index=rng)
    rs = rolling_sharpe(pr, rf, 36, returns_frequency="weekly")
    wp = calendar_window_to_n_periods(36, "weekly")
    assert len(rs) == len(pr) - wp + 1
    rv = rolling_vol_annual(pr, 12, returns_frequency="weekly")
    assert rv.notna().sum() >= 1

