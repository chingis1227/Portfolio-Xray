"""Factor matrix construction and dynamic analytics output tests."""
from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from src import stress_factors as sf


def _test_output_dir(name: str) -> Path:
    root = Path.cwd() / "output" / "codex_test_artifacts" / name
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_build_factor_matrix_includes_vix_us_growth_oil_and_shifts_wei_to_friday(monkeypatch) -> None:
    daily_idx = pd.date_range("2024-01-01", "2024-01-19", freq="B")
    saturday_idx = pd.to_datetime(["2024-01-06", "2024-01-13", "2024-01-20"])

    daily_close_map = {
        "SPY": pd.Series(np.linspace(100.0, 109.0, len(daily_idx)), index=daily_idx),
        "DBC": pd.Series(np.linspace(20.0, 24.5, len(daily_idx)), index=daily_idx),
    }
    fred_map = {
        sf.FRED_REAL_10Y: pd.Series(np.linspace(1.00, 1.18, len(daily_idx)), index=daily_idx),
        sf.FRED_BREAKEVEN_10Y: pd.Series(np.linspace(2.00, 2.09, len(daily_idx)), index=daily_idx),
        sf.FRED_HY_SPREAD: pd.Series(np.linspace(4.00, 4.18, len(daily_idx)), index=daily_idx),
        sf.FRED_DXY: pd.Series(np.linspace(100.0, 101.8, len(daily_idx)), index=daily_idx),
        sf.FRED_VIX: pd.Series(np.linspace(14.0, 17.6, len(daily_idx)), index=daily_idx),
        sf.FRED_WTI_OIL: pd.Series(np.linspace(70.0, 75.4, len(daily_idx)), index=daily_idx),
        sf.FRED_US_GROWTH: pd.Series([1.0, 1.2, 1.5], index=saturday_idx),
    }

    monkeypatch.setattr(
        sf,
        "fetch_daily",
        lambda ticker, *_args, **_kwargs: pd.DataFrame({"Close": daily_close_map[ticker]}),
    )
    monkeypatch.setattr(sf, "fetch_fred_series", lambda series_id, *_args, **_kwargs: fred_map[series_id].copy())

    out = sf.build_factor_matrix("2024-01-01", "2024-01-20")

    assert list(out.columns) == [
        "equity",
        "real_rates",
        "inflation",
        "credit",
        "usd",
        "commodity",
        "vix",
        "us_growth",
        "oil",
    ]
    assert list(out.index) == [pd.Timestamp("2024-01-12"), pd.Timestamp("2024-01-19")]
    assert np.isclose(out.loc[pd.Timestamp("2024-01-12"), "us_growth"], 0.2)
    assert np.isclose(out.loc[pd.Timestamp("2024-01-19"), "us_growth"], 0.3)
    expected_vix = sf._week_end(fred_map[sf.FRED_VIX]).pct_change().dropna()
    expected_oil = sf._week_end(fred_map[sf.FRED_WTI_OIL]).pct_change().dropna()
    assert np.isclose(out.loc[pd.Timestamp("2024-01-12"), "vix"], expected_vix.loc[pd.Timestamp("2024-01-12")])
    assert np.isclose(out.loc[pd.Timestamp("2024-01-12"), "oil"], expected_oil.loc[pd.Timestamp("2024-01-12")])


def test_credit_factor_falls_back_to_baa10y_when_hy_oas_history_is_short(monkeypatch) -> None:
    daily_idx = pd.date_range("2020-01-01", "2024-12-31", freq="B")
    short_credit_idx = pd.date_range("2024-01-01", "2024-12-31", freq="B")

    daily_close_map = {
        "SPY": pd.Series(np.linspace(100.0, 180.0, len(daily_idx)), index=daily_idx),
        "DBC": pd.Series(np.linspace(20.0, 30.0, len(daily_idx)), index=daily_idx),
    }
    fred_map = {
        sf.FRED_REAL_10Y: pd.Series(np.linspace(1.00, 1.60, len(daily_idx)), index=daily_idx),
        sf.FRED_BREAKEVEN_10Y: pd.Series(np.linspace(2.00, 2.25, len(daily_idx)), index=daily_idx),
        sf.FRED_HY_SPREAD: pd.Series(np.linspace(4.00, 4.30, len(short_credit_idx)), index=short_credit_idx),
        sf.FRED_CREDIT_SPREAD_FALLBACK: pd.Series(np.linspace(1.50, 2.10, len(daily_idx)), index=daily_idx),
        sf.FRED_DXY: pd.Series(np.linspace(100.0, 105.0, len(daily_idx)), index=daily_idx),
        sf.FRED_VIX: pd.Series(np.linspace(14.0, 20.0, len(daily_idx)), index=daily_idx),
        sf.FRED_WTI_OIL: pd.Series(np.linspace(70.0, 80.0, len(daily_idx)), index=daily_idx),
        sf.FRED_US_GROWTH: pd.Series(
            np.linspace(1.0, 1.6, len(pd.date_range("2020-01-04", "2024-12-28", freq="W-SAT"))),
            index=pd.date_range("2020-01-04", "2024-12-28", freq="W-SAT"),
        ),
    }

    monkeypatch.setattr(
        sf,
        "fetch_daily",
        lambda ticker, *_args, **_kwargs: pd.DataFrame({"Close": daily_close_map[ticker]}),
    )
    monkeypatch.setattr(sf, "fetch_fred_series", lambda series_id, *_args, **_kwargs: fred_map[series_id].copy())

    out = sf.build_factor_matrix("2020-01-01", "2024-12-31")
    diag = out.attrs["factor_load_diagnostics"]["by_factor"]["credit"]

    assert "credit" in out.columns
    assert diag["status"] == "available"
    assert diag["source"] == f"FRED:{sf.FRED_CREDIT_SPREAD_FALLBACK}"
    assert diag["primary_source"] == f"FRED:{sf.FRED_HY_SPREAD}"
    assert diag["fallback_used"] is True
    assert "insufficient coverage" in diag["fallback_reason"]


def test_base_factor_contract_excludes_oil_but_extended_registry_keeps_it() -> None:
    assert sf.BASE_FACTOR_COLUMN_ORDER == (
        "equity",
        "real_rates",
        "inflation",
        "credit",
        "usd",
        "commodity",
        "vix",
        "us_growth",
    )
    assert sf.BASE_BETA_ROW_ORDER == (
        "beta_eq",
        "beta_rr",
        "beta_inf",
        "beta_credit",
        "beta_usd",
        "beta_cmd",
        "beta_vix",
        "beta_us_growth",
    )
    assert "oil" not in sf.BASE_FACTOR_COLUMN_ORDER
    assert "beta_oil" not in sf.BASE_BETA_ROW_ORDER
    assert sf.FACTOR_COLUMN_ORDER[-1] == "oil"
    assert sf.BETA_ROW_ORDER[-1] == "beta_oil"


def test_portfolio_factor_regression_weekly_uses_base_by_default_and_extended_when_requested(monkeypatch) -> None:
    idx = pd.date_range("2024-01-05", periods=30, freq="W-FRI")
    rng = np.random.default_rng(123)
    factors = pd.DataFrame(
        rng.normal(scale=0.05, size=(len(idx), len(sf.FACTOR_COLUMN_ORDER))),
        index=idx,
        columns=list(sf.FACTOR_COLUMN_ORDER),
    )
    y = (
        0.4 * factors["equity"]
        - 0.3 * factors["credit"]
        + 0.2 * factors["vix"]
        + 0.1 * factors["us_growth"]
        - 0.15 * factors["oil"]
        + rng.normal(scale=0.01, size=len(idx))
    )
    asset_weekly = pd.DataFrame({"AAA": y}, index=idx)

    monkeypatch.setattr(sf, "asset_weekly_returns_from_daily", lambda *_args, **_kwargs: asset_weekly.copy())
    monkeypatch.setattr(sf, "build_factor_matrix", lambda *_args, **_kwargs: factors.copy())

    import src.data_yf as data_yf

    monkeypatch.setattr(
        data_yf,
        "download_all",
        lambda *_args, **_kwargs: {"AAA": pd.DataFrame({"Close": [1.0, 2.0]}, index=pd.to_datetime(["2024-01-01", "2024-01-02"]))},
    )

    out = sf.portfolio_factor_regression_weekly(
        weights={"AAA": 1.0},
        tickers=["AAA"],
        analysis_end_str="2024-08-30",
        window_weeks=30,
    )

    expected_beta_keys = [sf.FACTOR_TO_BETA_KEY[col] for col in sf.BASE_FACTOR_COLUMN_ORDER]
    assert list(out["betas"].keys()) == expected_beta_keys
    assert "beta_vix" in out["betas"]
    assert "beta_us_growth" in out["betas"]
    assert "beta_oil" not in out["betas"]
    assert np.isclose(out["idiosyncratic_risk"], 1.0 - out["r2"])
    assert len(out["hac_inference"]["t"]) == len(expected_beta_keys) + 1

    extended = sf.portfolio_factor_regression_weekly(
        weights={"AAA": 1.0},
        tickers=["AAA"],
        analysis_end_str="2024-08-30",
        window_weeks=30,
        factor_columns=sf.FACTOR_COLUMN_ORDER,
    )
    extended_beta_keys = [sf.FACTOR_TO_BETA_KEY[col] for col in sf.FACTOR_COLUMN_ORDER]
    assert list(extended["betas"].keys()) == extended_beta_keys
    assert "beta_oil" in extended["betas"]


def test_compute_portfolio_rolling_factor_betas_monthly_outputs_windows(monkeypatch) -> None:
    idx = pd.date_range("2010-01-31", periods=150, freq="ME")
    rng = np.random.default_rng(456)
    factors = pd.DataFrame(
        rng.normal(scale=0.03, size=(len(idx), len(sf.FACTOR_COLUMN_ORDER))),
        index=idx,
        columns=list(sf.FACTOR_COLUMN_ORDER),
    )
    y = (
        0.5 * factors["equity"]
        - 0.2 * factors["credit"]
        + 0.1 * factors["oil"]
        + rng.normal(scale=0.01, size=len(idx))
    )
    monthly_returns = pd.DataFrame({"AAA": y}, index=idx)

    monkeypatch.setattr(sf, "build_factor_matrix_monthly", lambda *_args, **_kwargs: factors.copy())

    out = sf.compute_portfolio_rolling_factor_betas_monthly(
        monthly_returns=monthly_returns,
        weights={"AAA": 1.0},
        analysis_end_str="2022-06-30",
        rolling_windows_months={"3y": sf.FACTOR_MONTHS_3Y, "5y": sf.FACTOR_MONTHS_5Y, "10y": sf.FACTOR_MONTHS_10Y},
    )

    assert set(out) == {"3y", "5y", "10y"}
    assert "beta_eq" in out["3y"].columns
    assert "beta_oil" not in out["5y"].columns
    assert not out["10y"].empty

    extended = sf.compute_portfolio_rolling_factor_betas_monthly(
        monthly_returns=monthly_returns,
        weights={"AAA": 1.0},
        analysis_end_str="2022-06-30",
        rolling_windows_months={"5y": sf.FACTOR_MONTHS_5Y},
        factor_columns=sf.FACTOR_COLUMN_ORDER,
    )
    assert "beta_oil" in extended["5y"].columns


def test_write_rolling_betas_plot_pngs_handles_nine_factors() -> None:
    idx = pd.date_range("2024-01-05", periods=15, freq="W-FRI")
    rolling_df = pd.DataFrame(
        {
            beta_key: np.linspace(-0.2 + i * 0.05, 0.2 + i * 0.05, len(idx))
            for i, beta_key in enumerate(sf.BETA_ROW_ORDER)
        },
        index=idx,
    )
    out_dir = _test_output_dir("factor_png")
    try:
        out = sf.write_rolling_betas_plot_pngs({"3y": rolling_df}, out_dir)
        assert out["3y"] == "rolling_factor_betas_3y.png"
        assert (out_dir / out["3y"]).is_file()
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)
