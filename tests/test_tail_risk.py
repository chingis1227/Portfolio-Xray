"""Tests for daily historical VaR / ES (Session 03 tail-risk alignment)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.portfolio_analytics import (
    TAIL_RISK_FREQUENCY,
    TAIL_RISK_METHOD,
    TAIL_RISK_MIN_OBS_DAILY,
    compute_tail_risk_historical,
    es_historical,
    tail_risk_flat_fields,
    var_historical,
)


def test_compute_tail_risk_historical_daily_metadata_and_values() -> None:
    rng = pd.date_range("2020-01-02", periods=300, freq="B")
    r = pd.Series(np.random.default_rng(42).normal(-0.0002, 0.01, len(rng)), index=rng)
    end = rng[-1]
    block = compute_tail_risk_historical(
        r,
        window_months=120,
        window_label="10y",
        analysis_end=end,
        min_obs=60,
    )
    assert block["method"] == TAIL_RISK_METHOD
    assert block["frequency"] == TAIL_RISK_FREQUENCY
    assert block["window_label"] == "10y"
    assert block["window_months"] == 120
    assert block["metric_available"] is True
    assert block["n_obs"] >= TAIL_RISK_MIN_OBS_DAILY
    assert block["var_95"] is not None
    assert block["es_95"] is not None
    assert block["es_95"] <= block["var_95"]


def test_compute_tail_risk_historical_insufficient_obs() -> None:
    rng = pd.date_range("2024-01-02", periods=30, freq="B")
    r = pd.Series(0.001, index=rng)
    block = compute_tail_risk_historical(
        r,
        window_months=36,
        window_label="3y",
        analysis_end=rng[-1],
    )
    assert block["metric_available"] is False
    assert "insufficient_daily_obs" in str(block["unavailable_reason"])


def test_tail_risk_flat_fields_from_block() -> None:
    block = {
        "metric_available": True,
        "var_95": -0.012,
        "var_99": -0.018,
        "es_95": -0.015,
        "es_99": -0.022,
    }
    flat = tail_risk_flat_fields(block)
    assert flat["var_95"] == -0.012
    assert flat["es_99"] == -0.022


def test_var_es_historical_ordering_on_synthetic_tail() -> None:
    r = pd.Series([-0.10, -0.08, -0.05, -0.02, 0.01, 0.02, 0.03] * 20)
    v95 = var_historical(r, 0.95)
    e95 = es_historical(r, 0.95)
    assert np.isfinite(v95)
    assert np.isfinite(e95)
    assert e95 <= v95
