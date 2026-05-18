from __future__ import annotations

import numpy as np
import pandas as pd

from src.metrics_asset import max_drawdown, time_to_recovery
from src.metrics_daily import time_to_recovery_daily
from src.metrics_portfolio import portfolio_metrics_one_window


def _monthly(values: list[float]) -> pd.Series:
    return pd.Series(values, index=pd.date_range("2020-01-31", periods=len(values), freq="ME"))


def _daily(values: list[float]) -> pd.Series:
    return pd.Series(values, index=pd.bdate_range("2020-01-02", periods=len(values)))


def test_time_to_recovery_uses_max_drawdown_peak_even_after_later_high() -> None:
    returns = _monthly([0.0, -0.20, -0.125, 2 / 7, 1 / 9, 0.10])

    mdd, peak_date = max_drawdown(returns)
    ttr_months, recovered = time_to_recovery(returns)

    assert np.isclose(mdd, -0.30)
    assert peak_date == returns.index[0]
    assert ttr_months == 4.0
    assert recovered is True


def test_time_to_recovery_marks_unrecovered_max_drawdown_path() -> None:
    returns = _monthly([0.0, -0.20, -0.125, 0.05, 0.04])

    ttr_months, recovered = time_to_recovery(returns)

    assert ttr_months is None
    assert recovered is False


def test_portfolio_metrics_preserve_zero_ttr_when_no_drawdown() -> None:
    returns = _monthly([0.01, 0.02, 0.015, 0.005])
    rf = pd.Series(0.0, index=returns.index)

    metrics = portfolio_metrics_one_window(
        returns,
        rf,
        analysis_end=returns.index[-1],
        window_months=len(returns),
    )

    assert metrics["max_drawdown"] == 0.0
    assert metrics["ttr_months"] == 0.0
    assert metrics["recovered"] is True


def test_daily_time_to_recovery_uses_max_drawdown_peak() -> None:
    returns = _daily([0.0, -0.20, -0.125, 2 / 7, 1 / 9, 0.10])

    ttr_days, recovered, unit = time_to_recovery_daily(returns)

    assert ttr_days == 4.0
    assert recovered is True
    assert unit == "trading_days"
