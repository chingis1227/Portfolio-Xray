"""Tests for regime_portfolio_metrics_v1 (diagnostic daily regime analytics)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.metrics_daily import TRADING_DAYS_PER_YEAR, vol_annual_daily, cagr_from_equity_daily
from src.regime_portfolio_metrics import (
    REGIME_PORTFOLIO_METRICS_VERSION,
    build_regime_portfolio_metrics,
    expand_rf_monthly_to_daily,
    regime_portfolio_metrics_for_stress_report,
    regime_portfolio_metrics_summary,
    regime_portfolio_metrics_csv_frames,
)
from src.stress_factors_macro import MACRO_PRIMARY_REGIME_NAMES


def _bdaily(start: str, n: int) -> pd.DatetimeIndex:
    return pd.bdate_range(start, periods=n)


def test_expand_rf_monthly_ffill_to_daily():
    idx_m = pd.date_range("2020-01-31", periods=3, freq="ME")
    rf = pd.Series([0.001, 0.0011, 0.0012], index=idx_m)
    idx_d = _bdaily("2020-01-02", 40)
    out = expand_rf_monthly_to_daily(rf, idx_d)
    assert len(out) == len(idx_d)
    assert np.isfinite(out.loc["2020-01-02"])


def test_regime_portfolio_metrics_ffill_and_filter():
    idx_d = _bdaily("2020-01-02", 200)
    rng = np.random.default_rng(42)
    assets = pd.DataFrame(
        {
            "A": rng.normal(0.0002, 0.01, len(idx_d)),
            "B": rng.normal(0.0001, 0.01, len(idx_d)),
        },
        index=idx_d,
    )
    idx_m = pd.date_range("2019-12-31", periods=8, freq="ME")
    regimes_m = pd.Series(["goldilocks"] * 4 + ["reflation"] * 4, index=idx_m)
    labels_ff = (
        pd.Series(regimes_m.values, index=pd.to_datetime(regimes_m.index).normalize())
        .astype(str)
        .sort_index()
        .reindex(idx_d, method="ffill")
    )
    rf_m = pd.Series([0.001] * 6, index=pd.date_range("2019-10-31", periods=6, freq="ME"))
    rf_d = expand_rf_monthly_to_daily(rf_m, idx_d)
    bench = pd.Series(rng.normal(0.0002, 0.008, len(idx_d)), index=idx_d)

    out = build_regime_portfolio_metrics(
        daily_asset_returns=assets,
        daily_regime_labels_ffill=labels_ff,
        weights={"A": 0.6, "B": 0.4},
        rf_daily=rf_d,
        benchmark_daily_returns=bench,
        mar_daily=None,
        regime_factor_analytics_payload=None,
    )
    assert out["version"] == REGIME_PORTFOLIO_METRICS_VERSION
    assert out["frequency"] == "daily"
    assert out["annualization_factor"] == 252
    assert out["regime_label_alignment"] == "monthly_label_forward_filled_to_daily"

    g = out["regimes"]["goldilocks"]
    r = out["regimes"]["reflation"]
    assert g["n_obs_days"] + r["n_obs_days"] == len(idx_d)
    assert g["quality_status"] in {"usable", "low_confidence", "reliable", "insufficient_data"}

    slim = regime_portfolio_metrics_for_stress_report(out)
    assert "regimes" in slim
    assert "covariance" not in (slim["regimes"]["goldilocks"].get("asset_covariance") or {})
    summ = regime_portfolio_metrics_summary(out)
    assert summ["regimes"]["goldilocks"]["n_obs_days"] == g["n_obs_days"]
    frames = regime_portfolio_metrics_csv_frames(out)
    assert not frames["regime_portfolio_metrics_portfolio.csv"].empty


def test_vol_and_cagr_annualization_daily():
    rng = np.random.default_rng(0)
    r = pd.Series(rng.normal(0.0003, 0.015, 120))
    v = vol_annual_daily(r)
    assert abs(v - float(r.std(ddof=1) * np.sqrt(float(TRADING_DAYS_PER_YEAR)))) < 1e-9
    cg = cagr_from_equity_daily(r)
    assert np.isfinite(cg)


def test_covariance_ledoit_wolf_meta_and_rc_vol():
    idx_d = _bdaily("2019-06-03", 180)
    rng = np.random.default_rng(1)
    assets = pd.DataFrame(
        rng.normal(0.0, 0.012, (len(idx_d), 3)),
        index=idx_d,
        columns=["A", "B", "C"],
    )
    lab = pd.Series(["stagflation"] * len(idx_d), index=idx_d)
    rf_d = pd.Series(0.0001, index=idx_d)
    bench = pd.Series(rng.normal(0.0, 0.01, len(idx_d)), index=idx_d)
    out = build_regime_portfolio_metrics(
        daily_asset_returns=assets,
        daily_regime_labels_ffill=lab,
        weights={"A": 0.2, "B": 0.3, "C": 0.5},
        rf_daily=rf_d,
        benchmark_daily_returns=bench,
        regime_factor_analytics_payload=None,
    )
    blk = out["regimes"]["stagflation"]
    assert blk["covariance_available"] is True
    ac = blk["asset_covariance"]
    assert ac.get("covariance_estimator") == "ledoit_wolf"
    assert ac.get("covariance_scaled_to_annual") is True
    rc = blk["rc_vol"]
    assert rc.get("available") is True
    assert abs(sum(rc["rc_by_asset"].values()) - 1.0) < 1e-6


def test_small_sample_marks_metrics_unavailable():
    idx_d = _bdaily("2021-01-04", 30)
    rng = np.random.default_rng(2)
    assets = pd.DataFrame(
        rng.normal(0.0, 0.02, (len(idx_d), 2)),
        index=idx_d,
        columns=["A", "B"],
    )
    lab = pd.Series(["goldilocks"] * len(idx_d), index=idx_d)
    rf_d = pd.Series(0.0001, index=idx_d)
    bench = pd.Series(rng.normal(0.0, 0.015, len(idx_d)), index=idx_d)
    out = build_regime_portfolio_metrics(
        daily_asset_returns=assets,
        daily_regime_labels_ffill=lab,
        weights={"A": 0.5, "B": 0.5},
        rf_daily=rf_d,
        benchmark_daily_returns=bench,
    )
    g = out["regimes"]["goldilocks"]
    assert g["quality_status"] == "insufficient_data"
    pm = g["portfolio_metrics"]
    vr = pm.get("var_95") or {}
    assert vr.get("metric_available") is False
    assert "historical" in (vr.get("unavailable_reason") or "").lower() or "n_ge" in (vr.get("unavailable_reason") or "")


def test_all_primary_regimes_present():
    idx_d = _bdaily("2018-01-03", 80)
    rng = np.random.default_rng(3)
    assets = pd.DataFrame(rng.normal(0.0, 0.01, (len(idx_d), 2)), index=idx_d, columns=["A", "B"])
    lab = pd.Series(["goldilocks"] * len(idx_d), index=idx_d)
    rf_d = pd.Series(0.0001, index=idx_d)
    bench = pd.Series(rng.normal(0.0, 0.01, len(idx_d)), index=idx_d)
    out = build_regime_portfolio_metrics(
        daily_asset_returns=assets,
        daily_regime_labels_ffill=lab,
        weights={"A": 1.0, "B": 0.0},
        rf_daily=rf_d,
        benchmark_daily_returns=bench,
    )
    for name in MACRO_PRIMARY_REGIME_NAMES:
        assert name in out["regimes"]
        assert "n_obs_days" in out["regimes"][name]
