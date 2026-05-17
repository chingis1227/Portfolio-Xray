"""
Stress testing: factor data (FRED + Yahoo) and beta estimation.
Primary stress-report factor betas use weekly returns/changes (see FACTOR_WEEKS_5Y / FACTOR_WEEKS_10Y).
Monthly helpers remain for legacy / diagnostics only.
Factors: equity (S&P/SPY), real rates (DFII10 Δ), inflation (T10YIE Δ), credit (BAMLH0A0HYM2 Δ), USD (DTWEXBGS), commodities (DBC/PDBC).
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
from scipy import stats

from src.data_fred import fetch_fred_series
from src.data_yf import fetch_daily
from src.pandas_compat import MONTH_END_FREQ

_LOG = logging.getLogger(__name__)

# Stress report: weekly regression windows ending at analysis_end (Friday week-ends after inner join)
FACTOR_WEEKS_3Y = 156   # ~3 calendar years (rolling diagnostics)
FACTOR_WEEKS_5Y = 260   # ~5 calendar years
FACTOR_WEEKS_10Y = 520  # ~10 calendar years
FACTOR_DOWNLOAD_BUFFER_WEEKS = 28  # extra history for factor/asset weekly alignment
FACTOR_COVARIANCE_BASE_WEEKS = FACTOR_WEEKS_5Y
FACTOR_COVARIANCE_STABILITY_WEEKS = 104  # ~2 calendar years
FACTOR_COVARIANCE_STABILITY_THRESHOLD_PCT = 35.0
FACTOR_COVARIANCE_RC_STABILITY_THRESHOLD_PCT = 30.0
FACTOR_COVARIANCE_OVERLAY_CORR_FLOOR = 0.70
FACTOR_COVARIANCE_FORECAST_TRAIN_WEEKS = FACTOR_WEEKS_5Y
FACTOR_COVARIANCE_FORECAST_HOLDOUT_WEEKS = 52
FACTOR_COVARIANCE_FORECAST_STEP_WEEKS = 52
FACTOR_VARIANCE_DECOMP_MIN_OBS = 30
FACTOR_VARIANCE_DECOMP_EPS = 1e-12
FACTOR_VARIANCE_DECOMP_NEUTRAL_THRESHOLD = 1e-4
PORTFOLIO_PCA_MIN_OBS = 52
PORTFOLIO_PCA_ROLLING_WINDOW_WEEKS = 52
PORTFOLIO_PCA_ROLLING_STEP_WEEKS = 4
PORTFOLIO_PCA_EPS = 1e-12

# Breusch-Godfrey LM: lag orders (weekly residuals; same auxiliary regression as in stress spec Section 8.2)
FACTOR_REGRESSION_BG_LAGS: tuple[int, ...] = (1, 2, 4)
# HAC / Newey-West: max lag for weekly factor regression residuals (about one calendar month)
FACTOR_REGRESSION_HAC_LAGS: int = 4

FACTOR_MONTHS_3Y = 36
FACTOR_MONTHS_5Y = 60
FACTOR_MONTHS_10Y = 120
# ~10 calendar years of US equity trading sessions (regime_factor_analytics_v1 daily window)
FACTOR_TRADING_DAYS_10Y = 252 * 10
FACTOR_OOS_HOLDOUT_WEEKS = 52
FACTOR_OOS_HOLDOUT_MONTHS = 12
FACTOR_STABILITY_MIN_ABS_BETA = 0.05
FACTOR_STABILITY_ZERO_EPS = 0.01
FACTOR_BETA_ADJUSTED_CONFIDENCE_BY_SEVERITY: dict[str, float] = {
    "low": 1.00,
    "moderate": 0.75,
    "high": 0.50,
    "unknown": 0.60,
}
FACTOR_BETA_ADJUSTED_ANCHOR_SOURCE = "10y_when_available_else_5y_raw"
FACTOR_BETA_ADJUSTED_METHOD = "severity_weighted_shrinkage_to_10y_anchor"
FACTOR_BETA_DIVERGENCE_RELATIVE_GAP_STRONG_GTE = 1.0
FACTOR_RAW_VS_ADJUSTED_PNL_RELATIVE_DELTA_MATERIAL_GTE = 0.25
FACTOR_RAW_VS_ADJUSTED_PNL_ABS_DELTA_MATERIAL_GTE = 0.01
FACTOR_KALMAN_BETA_CAP_ABS = 3.0
FACTOR_KALMAN_DIVERGENCE_ABS_GAP_GTE = 0.25
FACTOR_KALMAN_DIVERGENCE_RELATIVE_GAP_GTE = 0.75
FACTOR_KALMAN_DIVERGENCE_MIN_ABS_DENOMINATOR = 0.05
FACTOR_KALMAN_UNCERTAINTY_LOW_LTE = 0.15
FACTOR_KALMAN_UNCERTAINTY_MODERATE_LTE = 0.35
FACTOR_KALMAN_MIN_OBSERVATIONS = 30
FACTOR_KALMAN_INIT_OBSERVATIONS = 104
FACTOR_STABILITY_THRESHOLDS: dict[str, Any] = {
    "sign": {
        "dominant_share_high_lt": 0.65,
        "dominant_share_moderate_lt": 0.80,
        "zero_cross_high_eps": FACTOR_STABILITY_ZERO_EPS,
    },
    "magnitude": {
        "relative_band_moderate_gte": 1.0,
        "relative_band_high_gte": 2.0,
        "min_abs_beta_denominator": FACTOR_STABILITY_MIN_ABS_BETA,
    },
    "specification": {
        "relative_median_span_moderate_gte": 1.0,
        "relative_median_span_high_gte": 2.0,
    },
    "oos": {
        "sign_match_share_high_lt": 0.65,
        "sign_match_share_moderate_lt": 0.80,
        "relative_magnitude_degradation_moderate_gte": 1.0,
        "relative_magnitude_degradation_high_gte": 2.0,
        "holdout_weeks": FACTOR_OOS_HOLDOUT_WEEKS,
        "holdout_months": FACTOR_OOS_HOLDOUT_MONTHS,
    },
    "severity_distribution": {
        "high_share_warning_gt": 0.70,
        "low_share_warning_gt": 0.80,
        "suggested_magnitude_thresholds_if_strict": [1.5, 2.5],
    },
}
_SEVERITY_RANK = {"unknown": 0, "low": 1, "moderate": 2, "high": 3}

# Macro regime classifier version v1: macro_two_axis_v1 (monthly, two-axis macro data).
# See src/stress_factors_macro.py for the full implementation and
# docs/docs/stress_testing_spec.md §8.8.2 for the contract.
MACRO_REGIME_METHOD_VERSION = "macro_two_axis_v1"
MACRO_REGIME_METHOD_DISCLAIMER = (
    "macro_two_axis_v1 is a diagnostic-only macro regime classifier. It does not "
    "affect optimizer weights, mandate gates, stress pass/fail, or weight release."
)
MACRO_REGIME_STABILITY_WARNING = (
    "Stability threshold is a global heuristic, not factor-specific calibration."
)
MACRO_REGIME_NEUTRAL_BAND = 0.25
MACRO_REGIME_STABILITY_BETA_GAP = 0.25
# Per-regime n_obs gating thresholds in monthly observations. See ExecPlan v1.
MACRO_REGIME_INSUFFICIENT_MAX_ROWS = 12
MACRO_REGIME_LOW_CONFIDENCE_MIN_ROWS = 12
MACRO_REGIME_USABLE_MIN_ROWS = 24
MACRO_REGIME_RELIABLE_MIN_ROWS = 60
MACRO_REGIME_NAMES = (
    "goldilocks",
    "reflation",
    "stagflation",
    "recession_disinflation",
    "neutral_transition",
)

# FRED series (fallback when project series not used)
FRED_EQUITY_LEVEL = "SP500"
FRED_REAL_10Y = "DFII10"
FRED_BREAKEVEN_10Y = "T10YIE"
FRED_HY_SPREAD = "BAMLH0A0HYM2"
FRED_DXY = "DTWEXBGS"
FRED_VIX = "VIXCLS"
FRED_US_GROWTH = "WEI"
FRED_WTI_OIL = "DCOILWTICO"

# ETF proxies (preferred for equity/commodity when available)
ETF_EQUITY = "SPY"
ETF_COMMODITY = "DBC"


@dataclass(frozen=True)
class FactorDefinition:
    column: str
    beta_key: str
    display_name: str
    source_label: str
    weekly_loader: Callable[[str, str], pd.Series]
    monthly_loader: Callable[[str, str], pd.Series]
    stress_participates: bool = True


def _week_end(series: pd.Series) -> pd.Series:
    """Resample to week-end (Friday)."""
    return series.resample("W-FRI").last().dropna()


def _shift_index_days(series: pd.Series, days: int) -> pd.Series:
    if series.empty:
        return series
    out = series.copy()
    out.index = pd.to_datetime(out.index).tz_localize(None) + pd.Timedelta(days=int(days))
    return out.sort_index()


def _weekly_return(prices: pd.Series) -> pd.Series:
    """Weekly simple return from price series (week-end)."""
    w = _week_end(prices)
    return w.pct_change().dropna()


def _month_end(s: pd.Series) -> pd.Series:
    return s.resample(MONTH_END_FREQ).last().dropna()


def _monthly_return(prices: pd.Series) -> pd.Series:
    m = _month_end(prices)
    return m.pct_change().dropna()


def _business_daily_last(series: pd.Series) -> pd.Series:
    """Resample to business days using last observation carried forward."""

    if series is None or series.empty:
        return pd.Series(dtype=float)
    out = series.copy()
    out.index = pd.to_datetime(out.index).tz_localize(None)
    out = out.sort_index()
    return out.resample("B").last().ffill()


def _fred_daily_pct_change(series_id: str, start: str, end: str) -> pd.Series:
    try:
        s = fetch_fred_series(series_id, start, end)
        if s.empty or len(s) < 2:
            return pd.Series(dtype=float)
        d = _business_daily_last(s)
        return d.pct_change().dropna()
    except Exception:
        return pd.Series(dtype=float)


def _fred_daily_decimal_diff(series_id: str, start: str, end: str) -> pd.Series:
    try:
        s = fetch_fred_series(series_id, start, end)
        if s.empty or len(s) < 2:
            return pd.Series(dtype=float)
        d = _business_daily_last(s)
        return (d / 100.0).diff().dropna()
    except Exception:
        return pd.Series(dtype=float)


def _yahoo_daily_return(ticker: str, start: str, end: str) -> pd.Series:
    try:
        df = fetch_daily(ticker, start, end)
        if df.empty or "Close" not in df.columns:
            return pd.Series(dtype=float)
        r = df["Close"].astype(float).pct_change().dropna()
        return r
    except Exception:
        return pd.Series(dtype=float)


def _fred_weekly_pct_change(series_id: str, start: str, end: str) -> pd.Series:
    try:
        s = fetch_fred_series(series_id, start, end)
        if s.empty or len(s) < 2:
            return pd.Series(dtype=float)
        return _week_end(s).pct_change().dropna()
    except Exception:
        return pd.Series(dtype=float)


def _fred_monthly_pct_change(series_id: str, start: str, end: str) -> pd.Series:
    try:
        s = fetch_fred_series(series_id, start, end)
        if s.empty or len(s) < 2:
            return pd.Series(dtype=float)
        return _month_end(s).pct_change().dropna()
    except Exception:
        return pd.Series(dtype=float)


def _fred_weekly_decimal_diff(series_id: str, start: str, end: str) -> pd.Series:
    try:
        s = fetch_fred_series(series_id, start, end)
        if s.empty or len(s) < 2:
            return pd.Series(dtype=float)
        return (_week_end(s) / 100.0).diff().dropna()
    except Exception:
        return pd.Series(dtype=float)


def _fred_monthly_decimal_diff(series_id: str, start: str, end: str) -> pd.Series:
    try:
        s = fetch_fred_series(series_id, start, end)
        if s.empty or len(s) < 2:
            return pd.Series(dtype=float)
        return (_month_end(s) / 100.0).diff().dropna()
    except Exception:
        return pd.Series(dtype=float)


def _yahoo_weekly_return(ticker: str, start: str, end: str) -> pd.Series:
    try:
        df = fetch_daily(ticker, start, end)
        if not df.empty and "Close" in df.columns:
            return _weekly_return(df["Close"])
    except Exception:
        pass
    return pd.Series(dtype=float)


def _yahoo_monthly_return(ticker: str, start: str, end: str) -> pd.Series:
    try:
        df = fetch_daily(ticker, start, end)
        if not df.empty and "Close" in df.columns:
            return _monthly_return(df["Close"])
    except Exception:
        pass
    return pd.Series(dtype=float)


def fetch_equity_weekly(start: str, end: str) -> pd.Series:
    """Weekly equity return: try SPY (Yahoo), else FRED SP500 level -> return."""
    out = _yahoo_weekly_return(ETF_EQUITY, start, end)
    if not out.empty:
        return out
    try:
        s = fetch_fred_series(FRED_EQUITY_LEVEL, start, end)
        if not s.empty:
            return _weekly_return(s)
    except Exception:
        pass
    return pd.Series(dtype=float)


def fetch_equity_monthly(start: str, end: str) -> pd.Series:
    """Monthly equity return: try SPY (Yahoo), else FRED SP500 level -> return."""
    out = _yahoo_monthly_return(ETF_EQUITY, start, end)
    if not out.empty:
        return out
    try:
        s = fetch_fred_series(FRED_EQUITY_LEVEL, start, end)
        if not s.empty:
            return _monthly_return(s)
    except Exception:
        pass
    return pd.Series(dtype=float)


def fetch_real_rates_weekly(start: str, end: str) -> pd.Series:
    """Weekly change in 10Y real yield (FRED DFII10). In decimal (e.g. 0.02 = 200 bps)."""
    return _fred_weekly_decimal_diff(FRED_REAL_10Y, start, end)


def fetch_real_rates_monthly(start: str, end: str) -> pd.Series:
    return _fred_monthly_decimal_diff(FRED_REAL_10Y, start, end)


def fetch_inflation_surprise_weekly(start: str, end: str) -> pd.Series:
    """Weekly change in 10Y breakeven (FRED T10YIE) as inflation surprise proxy. Decimal."""
    return _fred_weekly_decimal_diff(FRED_BREAKEVEN_10Y, start, end)


def fetch_inflation_surprise_monthly(start: str, end: str) -> pd.Series:
    return _fred_monthly_decimal_diff(FRED_BREAKEVEN_10Y, start, end)


def fetch_credit_spread_weekly(start: str, end: str) -> pd.Series:
    """Weekly change in HY spread (FRED BAMLH0A0HYM2). Percent -> decimal (e.g. 4.0% -> 0.04)."""
    return _fred_weekly_decimal_diff(FRED_HY_SPREAD, start, end)


def fetch_credit_spread_monthly(start: str, end: str) -> pd.Series:
    return _fred_monthly_decimal_diff(FRED_HY_SPREAD, start, end)


def fetch_usd_weekly(start: str, end: str) -> pd.Series:
    """Weekly % change in DXY (FRED DTWEXBGS)."""
    return _fred_weekly_pct_change(FRED_DXY, start, end)


def fetch_usd_monthly(start: str, end: str) -> pd.Series:
    return _fred_monthly_pct_change(FRED_DXY, start, end)


def fetch_commodity_weekly(start: str, end: str) -> pd.Series:
    """Weekly commodity return (DBC ETF)."""
    return _yahoo_weekly_return(ETF_COMMODITY, start, end)


def fetch_commodity_monthly(start: str, end: str) -> pd.Series:
    return _yahoo_monthly_return(ETF_COMMODITY, start, end)


def fetch_vix_weekly(start: str, end: str) -> pd.Series:
    """Weekly % change in VIX level (FRED VIXCLS)."""
    return _fred_weekly_pct_change(FRED_VIX, start, end)


def fetch_vix_monthly(start: str, end: str) -> pd.Series:
    return _fred_monthly_pct_change(FRED_VIX, start, end)


def fetch_us_growth_weekly(start: str, end: str) -> pd.Series:
    """
    Weekly change in WEI.

    FRED WEI is week-ending Saturday. Shift to Friday before inner joins so it aligns
    with the rest of the weekly factor matrix.
    """
    try:
        s = fetch_fred_series(FRED_US_GROWTH, start, end)
        if s.empty or len(s) < 2:
            return pd.Series(dtype=float)
        return _shift_index_days(s, -1).diff().dropna()
    except Exception:
        return pd.Series(dtype=float)


def fetch_us_growth_monthly(start: str, end: str) -> pd.Series:
    try:
        s = fetch_fred_series(FRED_US_GROWTH, start, end)
        if s.empty or len(s) < 2:
            return pd.Series(dtype=float)
        return _month_end(_shift_index_days(s, -1)).diff().dropna()
    except Exception:
        return pd.Series(dtype=float)


def fetch_oil_weekly(start: str, end: str) -> pd.Series:
    """Weekly % change in WTI spot oil (FRED DCOILWTICO)."""
    return _fred_weekly_pct_change(FRED_WTI_OIL, start, end)


def fetch_oil_monthly(start: str, end: str) -> pd.Series:
    return _fred_monthly_pct_change(FRED_WTI_OIL, start, end)


def fetch_equity_daily(start: str, end: str) -> pd.Series:
    out = _yahoo_daily_return(ETF_EQUITY, start, end)
    if not out.empty:
        return out
    try:
        s = fetch_fred_series(FRED_EQUITY_LEVEL, start, end)
        if not s.empty:
            d = _business_daily_last(s)
            return d.pct_change().dropna()
    except Exception:
        pass
    return pd.Series(dtype=float)


def fetch_real_rates_daily(start: str, end: str) -> pd.Series:
    return _fred_daily_decimal_diff(FRED_REAL_10Y, start, end)


def fetch_inflation_surprise_daily(start: str, end: str) -> pd.Series:
    return _fred_daily_decimal_diff(FRED_BREAKEVEN_10Y, start, end)


def fetch_credit_spread_daily(start: str, end: str) -> pd.Series:
    return _fred_daily_decimal_diff(FRED_HY_SPREAD, start, end)


def fetch_usd_daily(start: str, end: str) -> pd.Series:
    return _fred_daily_pct_change(FRED_DXY, start, end)


def fetch_commodity_daily(start: str, end: str) -> pd.Series:
    return _yahoo_daily_return(ETF_COMMODITY, start, end)


def fetch_vix_daily(start: str, end: str) -> pd.Series:
    return _fred_daily_pct_change(FRED_VIX, start, end)


def fetch_us_growth_daily(start: str, end: str) -> pd.Series:
    """Daily diffs of FRED WEI forward-filled to business days (Wed release shifted to Fri in weekly path)."""

    try:
        s = fetch_fred_series(FRED_US_GROWTH, start, end)
        if s.empty or len(s) < 2:
            return pd.Series(dtype=float)
        d = _business_daily_last(_shift_index_days(s, -1))
        return d.diff().dropna()
    except Exception:
        return pd.Series(dtype=float)


def fetch_oil_daily(start: str, end: str) -> pd.Series:
    return _fred_daily_pct_change(FRED_WTI_OIL, start, end)


FACTOR_DEFINITIONS: tuple[FactorDefinition, ...] = (
    FactorDefinition("equity", "beta_eq", "Equity", "SPY or FRED:SP500", lambda start, end: fetch_equity_weekly(start, end), lambda start, end: fetch_equity_monthly(start, end), True),
    FactorDefinition("real_rates", "beta_rr", "Real rates", "FRED:DFII10", lambda start, end: fetch_real_rates_weekly(start, end), lambda start, end: fetch_real_rates_monthly(start, end), True),
    FactorDefinition("inflation", "beta_inf", "Inflation", "FRED:T10YIE", lambda start, end: fetch_inflation_surprise_weekly(start, end), lambda start, end: fetch_inflation_surprise_monthly(start, end), True),
    FactorDefinition("credit", "beta_credit", "Credit (HY)", "FRED:BAMLH0A0HYM2", lambda start, end: fetch_credit_spread_weekly(start, end), lambda start, end: fetch_credit_spread_monthly(start, end), True),
    FactorDefinition("usd", "beta_usd", "USD", "FRED:DTWEXBGS", lambda start, end: fetch_usd_weekly(start, end), lambda start, end: fetch_usd_monthly(start, end), True),
    FactorDefinition("commodity", "beta_cmd", "Commodity", "DBC", lambda start, end: fetch_commodity_weekly(start, end), lambda start, end: fetch_commodity_monthly(start, end), True),
    FactorDefinition("vix", "beta_vix", "VIX", "FRED:VIXCLS", lambda start, end: fetch_vix_weekly(start, end), lambda start, end: fetch_vix_monthly(start, end), False),
    FactorDefinition("us_growth", "beta_us_growth", "US Growth (WEI)", "FRED:WEI", lambda start, end: fetch_us_growth_weekly(start, end), lambda start, end: fetch_us_growth_monthly(start, end), False),
    FactorDefinition("oil", "beta_oil", "Oil (WTI)", "FRED:DCOILWTICO", lambda start, end: fetch_oil_weekly(start, end), lambda start, end: fetch_oil_monthly(start, end), False),
)
BASE_FACTOR_DEFINITIONS: tuple[FactorDefinition, ...] = tuple(
    spec for spec in FACTOR_DEFINITIONS if spec.column != "oil"
)
STRESS_FACTOR_DEFINITIONS: tuple[FactorDefinition, ...] = tuple(spec for spec in FACTOR_DEFINITIONS if spec.stress_participates)
FACTOR_TO_BETA_KEY = {spec.column: spec.beta_key for spec in FACTOR_DEFINITIONS}
BETA_KEY_TO_FACTOR = {spec.beta_key: spec.column for spec in FACTOR_DEFINITIONS}
BETA_ROW_ORDER: tuple[str, ...] = tuple(spec.beta_key for spec in FACTOR_DEFINITIONS)
BETA_KEY_TO_DISPLAY_NAME = {spec.beta_key: spec.display_name for spec in FACTOR_DEFINITIONS}
FACTOR_COLUMN_ORDER: tuple[str, ...] = tuple(spec.column for spec in FACTOR_DEFINITIONS)
BASE_FACTOR_COLUMN_ORDER: tuple[str, ...] = tuple(spec.column for spec in BASE_FACTOR_DEFINITIONS)
BASE_BETA_ROW_ORDER: tuple[str, ...] = tuple(spec.beta_key for spec in BASE_FACTOR_DEFINITIONS)
FACTOR_BETA_TO_SYNTHETIC_SHOCK_KEY = {
    "beta_eq": "shock_eq",
    "beta_rr": "shock_rr",
    "beta_credit": "shock_credit",
    "beta_inf": "shock_inf",
    "beta_usd": "shock_usd",
    "beta_cmd": "shock_cmd",
    "beta_vix": "shock_vix",
    "beta_us_growth": "shock_us_growth",
    "beta_oil": "shock_oil",
}


def get_factor_beta_row_order(*, stress_only: bool = False, base_only: bool = False) -> tuple[str, ...]:
    specs = BASE_FACTOR_DEFINITIONS if base_only else STRESS_FACTOR_DEFINITIONS if stress_only else FACTOR_DEFINITIONS
    return tuple(spec.beta_key for spec in specs)


def get_factor_display_name(beta_key: str) -> str:
    return BETA_KEY_TO_DISPLAY_NAME.get(beta_key, beta_key)


def _factor_order(*, extended: bool = False) -> tuple[str, ...]:
    return FACTOR_COLUMN_ORDER if extended else BASE_FACTOR_COLUMN_ORDER


def _beta_order(*, extended: bool = False) -> tuple[str, ...]:
    return BETA_ROW_ORDER if extended else BASE_BETA_ROW_ORDER


def _select_factor_columns(
    factor_returns: pd.DataFrame,
    factor_columns: tuple[str, ...] | list[str] | None = None,
    *,
    extended: bool = False,
) -> list[str]:
    order = tuple(factor_columns) if factor_columns is not None else _factor_order(extended=extended)
    return [c for c in order if c in factor_returns.columns]


def _ordered_beta_keys_with_order(
    *maps: Any,
    beta_order: tuple[str, ...],
    include_extra: bool = True,
) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for key in beta_order:
        if any(isinstance(m, dict) and key in m for m in maps):
            ordered.append(key)
            seen.add(key)
    if not include_extra:
        return ordered
    extra = sorted(
        {
            str(key)
            for m in maps
            if isinstance(m, dict)
            for key in m.keys()
            if str(key) not in seen
        }
    )
    ordered.extend(extra)
    return ordered


def _ordered_beta_keys(*maps: Any) -> list[str]:
    return _ordered_beta_keys_with_order(*maps, beta_order=BETA_ROW_ORDER)


def _ordered_base_beta_keys(*maps: Any) -> list[str]:
    return _ordered_beta_keys_with_order(*maps, beta_order=BASE_BETA_ROW_ORDER, include_extra=False)


def _filter_beta_map_to_base(values: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(values, dict):
        return {}
    return {k: v for k, v in values.items() if str(k) in BASE_BETA_ROW_ORDER}


def _build_factor_frame(
    start: str,
    end: str,
    *,
    monthly: bool,
    require_complete_rows: bool = True,
) -> pd.DataFrame:
    data: dict[str, pd.Series] = {}
    for spec in FACTOR_DEFINITIONS:
        loader = spec.monthly_loader if monthly else spec.weekly_loader
        try:
            series = loader(start, end)
        except Exception:
            series = pd.Series(dtype=float)
        data[spec.column] = series if series is not None else pd.Series(dtype=float)

    ordered_cols = [spec.column for spec in FACTOR_DEFINITIONS]
    df = pd.DataFrame({col: data[col] for col in ordered_cols})
    df = df.dropna(how="all")
    if df.empty:
        return df
    if not monthly:
        min_fill_ratio = 0.5
        cols_to_drop = [c for c in ordered_cols if c in df.columns and df[c].notna().sum() < len(df) * min_fill_ratio]
        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)
        # Inner join across all columns drops early-history rows when any factor is missing.
        # Episode factor sums (historical stress fallback) sum each column with its own NaNs dropped,
        # so incomplete rows must be retained when require_complete_rows is False.
        if require_complete_rows:
            df = df.dropna()
    return df


def build_factor_matrix(
    start: str,
    end: str,
    *,
    require_complete_rows: bool = True,
) -> pd.DataFrame:
    """
    Build weekly factor series aligned to common index.
    Columns follow FACTOR_DEFINITIONS and currently include equity, real_rates,
    inflation, credit, usd, commodity, vix, us_growth, and oil.
    Index: week-end dates. All in decimal (returns or changes).

    When ``require_complete_rows`` is False, rows with partial NaNs are kept so
    per-column episode sums (e.g. dotcom) still have data; callers that need a
    strict inner join for regressions should keep the default True.
    """
    return _build_factor_frame(start, end, monthly=False, require_complete_rows=require_complete_rows)


def build_factor_matrix_monthly(
    start: str,
    end: str,
) -> pd.DataFrame:
    """
    Build monthly factor series (effective month-end), same columns as
    ``build_factor_matrix``. Index: month-end timestamps. Used for
    ``regime_factor_analytics_v1`` alignment with macro_two_axis monthly labels.
    """
    return _build_factor_frame(start, end, monthly=True)


_DAILY_FACTOR_LOADERS: dict[str, Callable[[str, str], pd.Series]] = {
    "equity": fetch_equity_daily,
    "real_rates": fetch_real_rates_daily,
    "inflation": fetch_inflation_surprise_daily,
    "credit": fetch_credit_spread_daily,
    "usd": fetch_usd_daily,
    "commodity": fetch_commodity_daily,
    "vix": fetch_vix_daily,
    "us_growth": fetch_us_growth_daily,
    "oil": fetch_oil_daily,
}


def _build_factor_frame_daily(start: str, end: str) -> pd.DataFrame:
    data: dict[str, pd.Series] = {}
    for spec in FACTOR_DEFINITIONS:
        loader = _DAILY_FACTOR_LOADERS.get(spec.column)
        if loader is None:
            series = pd.Series(dtype=float)
        else:
            try:
                series = loader(start, end)
            except Exception:
                series = pd.Series(dtype=float)
        data[spec.column] = series if series is not None else pd.Series(dtype=float)

    ordered_cols = [spec.column for spec in FACTOR_DEFINITIONS]
    df = pd.DataFrame({col: data[col] for col in ordered_cols})
    df = df.dropna(how="all")
    if df.empty:
        return df
    min_fill_ratio = 0.45
    cols_to_drop = [
        c
        for c in ordered_cols
        if c in df.columns and df[c].notna().sum() < len(df) * min_fill_ratio
    ]
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
    df = df.dropna()
    return df


def build_factor_matrix_daily(
    start: str,
    end: str,
) -> pd.DataFrame:
    """
    Build daily factor changes/returns on a shared **business-day** index
    (complete-case inner join across retained columns). Column semantics match
    ``build_factor_matrix`` (weekly) but sampled at daily frequency.
    """
    return _build_factor_frame_daily(start, end)


def asset_daily_returns_from_daily(
    daily_prices: dict[str, pd.Series],
    start: str,
    end: str,
) -> pd.DataFrame:
    """Daily simple returns from daily price series (dict of Close levels)."""

    out: dict[str, pd.Series] = {}
    for ticker, prices in daily_prices.items():
        if prices is None or prices.empty:
            continue
        p = prices.loc[start:end] if hasattr(prices.index, "slice_indexer") else prices
        if p.empty or len(p) < 2:
            continue
        p = p.sort_index()
        r = p.astype(float).pct_change().dropna()
        if not r.empty:
            out[str(ticker)] = r
    if not out:
        return pd.DataFrame()
    df = pd.DataFrame(out)
    return df.dropna(how="all")


def asset_weekly_returns_from_daily(
    daily_prices: dict[str, pd.Series],
    start: str,
    end: str,
) -> pd.DataFrame:
    """Build weekly returns DataFrame from daily price dict. Columns = tickers."""
    out = {}
    for ticker, prices in daily_prices.items():
        if prices is None or prices.empty:
            continue
        p = prices.loc[start:end] if hasattr(prices.index, "slice_indexer") else prices
        if p.empty or len(p) < 2:
            continue
        w = _week_end(p)
        ret = w.pct_change().dropna()
        if not ret.empty:
            out[ticker] = ret
    if not out:
        return pd.DataFrame()
    df = pd.DataFrame(out)
    return df.dropna(how="all")


def estimate_betas(
    asset_returns: pd.DataFrame,
    factor_returns: pd.DataFrame,
    *,
    factor_columns: tuple[str, ...] | list[str] | None = None,
) -> pd.DataFrame:
    """
    Regress each asset's weekly return on factor columns. OLS, no constant (or with constant).
    Production defaults to BASE_FACTOR_DEFINITIONS; diagnostics may pass FACTOR_COLUMN_ORDER.
    Returns DataFrame: index = asset tickers, columns = beta_* keys from FACTOR_TO_BETA_KEY.
    """
    factor_cols = _select_factor_columns(factor_returns, factor_columns)
    if not factor_cols:
        return pd.DataFrame()

    # Align
    common = asset_returns.index.intersection(factor_returns.index)
    if len(common) < 10:
        return pd.DataFrame()

    Y = asset_returns.loc[common].dropna(how="all")
    X = factor_returns.loc[common, factor_cols].dropna()
    common = Y.index.intersection(X.index)
    if len(common) < 10:
        return pd.DataFrame()

    Y = Y.loc[common]
    X = X.loc[common]
    # Add constant for intercept (optional; user said betas so we regress returns on factors)
    X_const = np.column_stack([np.ones(len(X)), X.values])
    betas = {}
    for ticker in Y.columns:
        y = Y[ticker].values
        valid = ~(np.isnan(y) | np.isnan(X.values).any(axis=1))
        if valid.sum() < 10:
            continue
        try:
            # OLS: y = X_const @ b => b = (X'X)^{-1} X'y
            xv = X_const[valid]
            yv = y[valid]
            b = np.linalg.lstsq(xv, yv, rcond=None)[0]
            # b[0] = intercept, b[1:] = factor betas
            betas[ticker] = dict(zip(factor_cols, b[1:]))
        except Exception:
            continue

    if not betas:
        return pd.DataFrame()
    df = pd.DataFrame(betas).T
    df = df.rename(columns={c: FACTOR_TO_BETA_KEY.get(c, f"beta_{c}") for c in factor_cols})
    return df


def _portfolio_pca_unavailable(reason: str, **extra: Any) -> dict[str, Any]:
    out: dict[str, Any] = {
        "status": "unavailable",
        "reason": reason,
        "method": "portfolio_asset_pca_weekly",
        "variance_scale": "weekly",
        "ddof": 1,
    }
    out.update(extra)
    return out


def _pc1_severity(pc1_share: float | None, concentration_ratio: float | None) -> str:
    if pc1_share is None or concentration_ratio is None:
        return "unknown"
    if pc1_share >= 0.75 or concentration_ratio >= 4.0:
        return "extreme"
    if pc1_share >= 0.60 or concentration_ratio >= 3.0:
        return "high"
    if pc1_share >= 0.40 or concentration_ratio >= 2.0:
        return "moderate"
    return "low"


def _enb_severity(enb_ratio: float | None) -> str:
    if enb_ratio is None:
        return "unknown"
    if enb_ratio < 0.35:
        return "high"
    if enb_ratio < 0.55:
        return "moderate"
    return "low"


def _portfolio_pca_clean_returns(
    asset_returns: pd.DataFrame,
    *,
    window_weeks: int,
    min_obs: int = PORTFOLIO_PCA_MIN_OBS,
) -> tuple[pd.DataFrame, list[str], list[str], dict[str, str]]:
    if asset_returns is None or asset_returns.empty:
        return pd.DataFrame(), [], [], {}

    raw = asset_returns.copy()
    raw.index = pd.to_datetime(raw.index).tz_localize(None)
    raw = raw.sort_index()
    raw = raw.apply(pd.to_numeric, errors="coerce")

    eligible = [str(c) for c in raw.columns if raw[c].notna().sum() >= min_obs]
    excluded_reasons = {
        str(c): "insufficient_non_null_observations"
        for c in raw.columns
        if str(c) not in set(eligible)
    }
    if len(eligible) < 2:
        return pd.DataFrame(), eligible, list(excluded_reasons.keys()), excluded_reasons

    aligned = raw.loc[:, eligible].dropna(how="any")
    if window_weeks and len(aligned) > int(window_weeks):
        aligned = aligned.tail(int(window_weeks))
    if len(aligned) < min_obs:
        return pd.DataFrame(), eligible, list(excluded_reasons.keys()), excluded_reasons
    return aligned.astype(float), list(aligned.columns), list(excluded_reasons.keys()), excluded_reasons


def _portfolio_pca_matrix(data: pd.DataFrame, mode: str) -> tuple[np.ndarray, np.ndarray, list[str], pd.DataFrame] | None:
    if data.shape[0] < 2 or data.shape[1] < 2:
        return None
    cols = [str(c) for c in data.columns]
    centered = data.loc[:, cols].astype(float) - data.loc[:, cols].astype(float).mean(axis=0)
    if mode == "covariance":
        matrix = centered.cov(ddof=1).values.astype(float)
        score_frame = centered
    elif mode == "correlation":
        std = data.loc[:, cols].astype(float).std(axis=0, ddof=1).replace(0.0, np.nan)
        if std.isna().any():
            return None
        score_frame = centered.divide(std, axis=1)
        matrix = score_frame.cov(ddof=1).values.astype(float)
    else:
        return None
    matrix = (matrix + matrix.T) / 2.0
    return matrix, score_frame.values.astype(float), cols, score_frame


def _portfolio_pca_top_loadings(loadings: dict[str, float], *, limit: int = 3) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = [{"asset": asset, "loading": float(value)} for asset, value in loadings.items()]
    positives = sorted([r for r in rows if r["loading"] > 0], key=lambda r: r["loading"], reverse=True)[:limit]
    negatives = sorted([r for r in rows if r["loading"] < 0], key=lambda r: r["loading"])[:limit]
    return positives, negatives


def _portfolio_pca_core(data: pd.DataFrame, *, mode: str, factor_returns: pd.DataFrame | None = None) -> dict[str, Any]:
    pca_input = _portfolio_pca_matrix(data, mode)
    interpretation = "risk_dominance" if mode == "covariance" else "structure"
    if pca_input is None:
        return {
            "status": "unavailable",
            "reason": "degenerate_pca_input",
            "pca_type": f"{mode}_pca",
            "interpretation": interpretation,
        }

    matrix, score_values, cols, _score_frame = pca_input
    try:
        eigenvalues, eigenvectors = np.linalg.eigh(matrix)
    except Exception as ex:
        return {
            "status": "unavailable",
            "reason": "eigendecomposition_failed",
            "error": str(ex),
            "pca_type": f"{mode}_pca",
            "interpretation": interpretation,
        }

    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = np.maximum(eigenvalues[order].astype(float), 0.0)
    eigenvectors = eigenvectors[:, order].astype(float)

    for j in range(eigenvectors.shape[1]):
        max_idx = int(np.argmax(np.abs(eigenvectors[:, j])))
        if eigenvectors[max_idx, j] < 0:
            eigenvectors[:, j] *= -1.0

    total = float(np.sum(eigenvalues))
    if not np.isfinite(total) or total <= PORTFOLIO_PCA_EPS:
        return {
            "status": "unavailable",
            "reason": "degenerate_eigenvalues",
            "pca_type": f"{mode}_pca",
            "interpretation": interpretation,
        }

    ratios = eigenvalues / total
    cumulative = np.cumsum(ratios)
    n_assets = len(cols)
    pc1_share = float(ratios[0]) if len(ratios) else None
    concentration = float(pc1_share * n_assets) if pc1_share is not None else None
    enb = float(1.0 / np.sum(ratios**2)) if np.sum(ratios**2) > PORTFOLIO_PCA_EPS else None
    enb_ratio = float(enb / n_assets) if enb is not None and n_assets else None
    scores = score_values @ eigenvectors

    components: list[dict[str, Any]] = []
    for i, eig in enumerate(eigenvalues):
        loadings = {asset: float(eigenvectors[idx, i]) for idx, asset in enumerate(cols)}
        top_pos, top_neg = _portfolio_pca_top_loadings(loadings)
        components.append(
            {
                "component": f"PC{i + 1}",
                "eigenvalue": float(eig),
                "explained_variance_ratio": float(ratios[i]),
                "cumulative_explained_variance_ratio": float(cumulative[i]),
                "loadings": loadings,
                "top_positive_loadings": top_pos,
                "top_negative_loadings": top_neg,
            }
        )

    return {
        "status": "available",
        "pca_type": f"{mode}_pca",
        "interpretation": interpretation,
        "n_obs": int(data.shape[0]),
        "n_assets": int(n_assets),
        "assets": cols,
        "eigenvalues": [float(x) for x in eigenvalues],
        "explained_variance_ratio": [float(x) for x in ratios],
        "cumulative_explained_variance_ratio": [float(x) for x in cumulative],
        "components": components,
        "pc1_explained_variance_ratio": pc1_share,
        "pc1_concentration_ratio": concentration,
        "pc1_severity": _pc1_severity(pc1_share, concentration),
        "effective_number_of_bets": enb,
        "effective_number_of_bets_ratio": enb_ratio,
        "enb_severity": _enb_severity(enb_ratio),
        "_pc1_scores": pd.Series(scores[:, 0], index=data.index, dtype=float),
    }


def _portfolio_pca_factor_correlations(pc1_scores: pd.Series, factor_returns: pd.DataFrame | None) -> dict[str, Any]:
    if factor_returns is None or factor_returns.empty or pc1_scores.empty:
        return {"status": "unavailable", "reason": "missing_factor_returns"}
    factors = factor_returns.copy()
    factors.index = pd.to_datetime(factors.index).tz_localize(None)
    cols = [c for c in FACTOR_COLUMN_ORDER if c in factors.columns]
    if not cols:
        return {"status": "unavailable", "reason": "missing_factor_columns"}
    common = pc1_scores.index.intersection(factors.index).sort_values()
    if len(common) < 10:
        return {"status": "unavailable", "reason": "insufficient_common_rows", "n_obs": int(len(common))}
    y = pc1_scores.reindex(common).astype(float)
    x = factors.reindex(common).loc[:, cols].astype(float)
    out: dict[str, float | None] = {}
    for col in cols:
        pair = pd.concat([y.rename("pc1"), x[col].rename(col)], axis=1).dropna()
        if len(pair) < 10 or pair["pc1"].std(ddof=1) <= PORTFOLIO_PCA_EPS or pair[col].std(ddof=1) <= PORTFOLIO_PCA_EPS:
            out[str(col)] = None
        else:
            out[str(col)] = float(pair["pc1"].corr(pair[col]))
    top = sorted(
        [{"factor": k, "correlation": v, "abs_correlation": abs(float(v))} for k, v in out.items() if v is not None],
        key=lambda row: row["abs_correlation"],
        reverse=True,
    )[:3]
    return {
        "status": "available",
        "n_obs": int(len(common)),
        "correlations": out,
        "top_abs_correlations": top,
    }


def _portfolio_pca_rolling_pc1(data: pd.DataFrame, *, mode: str) -> dict[str, Any]:
    n = len(data)
    window = PORTFOLIO_PCA_ROLLING_WINDOW_WEEKS
    step = PORTFOLIO_PCA_ROLLING_STEP_WEEKS
    if n < window or data.shape[1] < 2:
        return {
            "status": "unavailable",
            "reason": "insufficient_rolling_observations",
            "window_weeks": window,
            "step_weeks": step,
            "n_obs": int(n),
        }
    endpoints = list(range(window, n + 1, step))
    if endpoints[-1] != n:
        endpoints.append(n)
    rows: list[dict[str, Any]] = []
    for end in endpoints:
        sub = data.iloc[end - window : end]
        pca = _portfolio_pca_core(sub, mode=mode, factor_returns=None)
        if pca.get("status") != "available":
            continue
        rows.append(
            {
                "end_date": pd.Timestamp(sub.index[-1]).strftime("%Y-%m-%d"),
                "n_obs": int(len(sub)),
                "pc1_explained_variance_ratio": float(pca["pc1_explained_variance_ratio"]),
                "pc1_concentration_ratio": float(pca["pc1_concentration_ratio"]),
                "pc1_severity": pca["pc1_severity"],
                "effective_number_of_bets": float(pca["effective_number_of_bets"]),
                "effective_number_of_bets_ratio": float(pca["effective_number_of_bets_ratio"]),
                "enb_severity": pca["enb_severity"],
            }
        )
    if not rows:
        return {
            "status": "unavailable",
            "reason": "no_valid_rolling_windows",
            "window_weeks": window,
            "step_weeks": step,
            "n_obs": int(n),
        }
    vals = np.asarray([float(r["pc1_explained_variance_ratio"]) for r in rows], dtype=float)
    x = np.arange(len(vals), dtype=float) * step
    slope_per_year = 0.0
    if len(vals) >= 2 and np.var(x) > PORTFOLIO_PCA_EPS:
        slope_per_week = float(np.polyfit(x, vals, 1)[0])
        slope_per_year = slope_per_week * 52.0
    latest = float(vals[-1])
    mean = float(np.mean(vals))
    std = float(np.std(vals, ddof=1)) if len(vals) >= 2 else 0.0
    p10 = float(np.percentile(vals, 10))
    p90 = float(np.percentile(vals, 90))
    severity = "low"
    if slope_per_year > 0.10 or latest > p90:
        severity = "high"
    elif slope_per_year > 0.05 or latest > mean + std:
        severity = "moderate"
    return {
        "status": "available",
        "window_weeks": window,
        "step_weeks": step,
        "rows": rows,
        "summary": {
            "latest": latest,
            "mean": mean,
            "std": std,
            "min": float(np.min(vals)),
            "max": float(np.max(vals)),
            "p10": p10,
            "p90": p90,
            "trend_slope_per_year": slope_per_year,
            "latest_minus_mean": latest - mean,
            "latest_minus_p10": latest - p10,
            "latest_minus_p90": latest - p90,
            "n_windows": int(len(rows)),
            "stability_severity": severity,
        },
    }


def _portfolio_pca_finalize_block(block: dict[str, Any], data: pd.DataFrame, factor_returns: pd.DataFrame | None) -> dict[str, Any]:
    for mode, key in (("covariance", "covariance_pca"), ("correlation", "correlation_pca")):
        pca = _portfolio_pca_core(data, mode=mode, factor_returns=factor_returns)
        scores = pca.pop("_pc1_scores", None)
        if pca.get("status") == "available" and isinstance(scores, pd.Series):
            pca["pc1_factor_correlations"] = _portfolio_pca_factor_correlations(scores, factor_returns)
            pca["rolling_pc1"] = _portfolio_pca_rolling_pc1(data, mode=mode)
        block[key] = pca
    return block


def _portfolio_pca_residual_returns(asset_returns: pd.DataFrame, factor_returns: pd.DataFrame | None) -> tuple[pd.DataFrame, dict[str, Any]]:
    if factor_returns is None or factor_returns.empty:
        return pd.DataFrame(), {"status": "unavailable", "reason": "missing_factor_returns"}
    factors = factor_returns.copy()
    factors.index = pd.to_datetime(factors.index).tz_localize(None)
    factor_cols = [c for c in FACTOR_COLUMN_ORDER if c in factors.columns]
    if not factor_cols:
        return pd.DataFrame(), {"status": "unavailable", "reason": "missing_factor_columns"}
    common = asset_returns.index.intersection(factors.index).sort_values()
    y_frame = asset_returns.reindex(common).dropna(how="any")
    x_frame = factors.reindex(y_frame.index).loc[:, factor_cols].dropna(how="any")
    y_frame = y_frame.reindex(x_frame.index).dropna(how="any")
    x_frame = x_frame.reindex(y_frame.index)
    if len(y_frame) < PORTFOLIO_PCA_MIN_OBS or y_frame.shape[1] < 2:
        return pd.DataFrame(), {
            "status": "unavailable",
            "reason": "insufficient_residual_common_rows",
            "n_obs": int(len(y_frame)),
        }
    X = np.column_stack([np.ones(len(x_frame)), x_frame.values.astype(float)])
    residuals: dict[str, np.ndarray] = {}
    for asset in y_frame.columns:
        y = y_frame[asset].values.astype(float)
        try:
            beta, *_ = np.linalg.lstsq(X, y, rcond=None)
            residuals[str(asset)] = y - X @ beta
        except Exception:
            continue
    if len(residuals) < 2:
        return pd.DataFrame(), {"status": "unavailable", "reason": "insufficient_residual_assets"}
    return pd.DataFrame(residuals, index=y_frame.index), {
        "status": "available",
        "factor_cols": list(factor_cols),
        "n_obs": int(len(y_frame)),
    }


def portfolio_pca_diagnostics_from_weekly_returns(
    asset_returns: pd.DataFrame,
    *,
    factor_returns: pd.DataFrame | None = None,
    window_weeks: int = FACTOR_WEEKS_5Y,
) -> dict[str, Any]:
    """Portfolio-asset PCA diagnostics from weekly returns; no network access."""
    clean, included, excluded, excluded_reasons = _portfolio_pca_clean_returns(
        asset_returns,
        window_weeks=window_weeks,
    )
    base = {
        "method": "portfolio_asset_pca_weekly",
        "variance_scale": "weekly",
        "ddof": 1,
        "window_weeks": int(window_weeks),
        "included_assets": included,
        "excluded_assets": excluded,
        "excluded_asset_reasons": excluded_reasons,
        "n_obs": int(len(clean)),
        "n_assets": int(clean.shape[1]) if not clean.empty else int(len(included)),
    }
    if clean.empty or clean.shape[1] < 2 or len(clean) < PORTFOLIO_PCA_MIN_OBS:
        return _portfolio_pca_unavailable(
            "insufficient_aligned_weekly_returns",
            **base,
        )

    out: dict[str, Any] = {"status": "available", **base}
    raw_block: dict[str, Any] = {
        "status": "available",
        "return_layer": "raw",
        "n_obs": int(len(clean)),
        "n_assets": int(clean.shape[1]),
    }
    out["raw"] = _portfolio_pca_finalize_block(raw_block, clean, factor_returns)

    residual_returns, residual_meta = _portfolio_pca_residual_returns(clean, factor_returns)
    residual_block: dict[str, Any] = {
        "return_layer": "residual",
        **residual_meta,
    }
    if residual_meta.get("status") == "available":
        residual_block["n_assets"] = int(residual_returns.shape[1])
        out["residual"] = _portfolio_pca_finalize_block(residual_block, residual_returns, factor_returns)
    else:
        out["residual"] = residual_block
    return out


def portfolio_pca_diagnostics(
    *,
    weights: dict[str, float],
    tickers: list[str],
    analysis_end_str: str,
    window_weeks: int = FACTOR_WEEKS_5Y,
    factor_returns: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """Download portfolio asset history and build weekly PCA diagnostics."""
    from src.data_yf import download_all

    use = [str(t).strip() for t in tickers if str(t).strip() and float(weights.get(t, 0.0)) > 0.0]
    if not use:
        use = [str(t).strip() for t in tickers if str(t).strip()]
    if len(use) < 2:
        return _portfolio_pca_unavailable(
            "insufficient_tickers",
            window_weeks=int(window_weeks),
            included_assets=use,
            excluded_assets=[],
            n_assets=len(use),
            n_obs=0,
        )

    end_ts = pd.Timestamp(analysis_end_str)
    end_dl = (end_ts + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    start_ts = end_ts - pd.DateOffset(weeks=int(window_weeks) + FACTOR_DOWNLOAD_BUFFER_WEEKS)
    start_dl = start_ts.strftime("%Y-%m-%d")

    daily = download_all(use, start_dl, end_dl)
    daily_prices: dict[str, pd.Series] = {}
    excluded: dict[str, str] = {}
    for ticker in use:
        df = daily.get(ticker)
        if df is None or df.empty or "Close" not in df.columns:
            excluded[ticker] = "missing_daily_close"
            continue
        daily_prices[ticker] = df["Close"].copy()

    weekly = asset_weekly_returns_from_daily(daily_prices, start_dl, end_dl)
    if weekly.empty:
        return _portfolio_pca_unavailable(
            "empty_weekly_returns",
            window_weeks=int(window_weeks),
            included_assets=[],
            excluded_assets=list(excluded.keys()),
            excluded_asset_reasons=excluded,
            n_assets=0,
            n_obs=0,
        )

    factors = factor_returns
    if factors is None or factors.empty:
        try:
            factors = build_factor_matrix(start_dl, end_dl)
        except Exception:
            factors = pd.DataFrame()

    out = portfolio_pca_diagnostics_from_weekly_returns(
        weekly,
        factor_returns=factors,
        window_weeks=window_weeks,
    )
    merged_reasons = dict(out.get("excluded_asset_reasons") or {})
    merged_reasons.update(excluded)
    out["excluded_asset_reasons"] = merged_reasons
    out["excluded_assets"] = sorted(set(out.get("excluded_assets") or []) | set(excluded.keys()))
    out["download_window"] = {"start": start_dl, "end": end_dl}
    return out


def _ols_with_inference(
    y: np.ndarray,
    X: np.ndarray,
    *,
    add_const: bool = True,
    alpha: float = 0.05,
) -> dict[str, Any] | None:
    """
    OLS with classical (non-HAC) inference.

    Returns dict with params/se/t/p/ci, R^2, 1 - R^2, adj R^2, df_resid, n_obs.
    """
    if y.ndim != 1:
        y = y.reshape(-1)
    if add_const:
        X = np.column_stack([np.ones(len(X)), X])
    n, k = X.shape
    if n <= k + 1:
        return None

    try:
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    except Exception:
        return None

    y_hat = X @ beta
    resid = y - y_hat
    rss = float(np.dot(resid, resid))
    tss = float(np.dot(y - float(np.mean(y)), y - float(np.mean(y))))
    r2 = 1.0 - (rss / tss) if tss > 0 else float("nan")
    df_resid = n - k
    s2 = rss / df_resid if df_resid > 0 else float("nan")

    try:
        XtX_inv = np.linalg.inv(X.T @ X)
    except Exception:
        return None

    cov_beta = s2 * XtX_inv
    se = np.sqrt(np.maximum(np.diag(cov_beta), 0.0))
    with np.errstate(divide="ignore", invalid="ignore"):
        tvals = beta / se

    # Two-sided p-values under Student-t(df_resid)
    pvals = 2.0 * stats.t.sf(np.abs(tvals), df=df_resid)
    tcrit = float(stats.t.ppf(1.0 - alpha / 2.0, df=df_resid))
    ci_low = beta - tcrit * se
    ci_high = beta + tcrit * se

    idiosyncratic_risk = 1.0 - r2 if np.isfinite(r2) else float("nan")

    adj_r2 = float("nan")
    if np.isfinite(r2) and n > 1 and df_resid > 0:
        adj_r2 = 1.0 - (1.0 - r2) * (n - 1) / df_resid

    return {
        "n_obs": int(n),
        "k": int(k),
        "df_resid": int(df_resid),
        "r2": float(r2),
        "idiosyncratic_risk": float(idiosyncratic_risk),
        "adj_r2": float(adj_r2),
        "se_type": "classic_ols",
        "ci_level": float(1.0 - alpha),
        "params": beta.astype(float),
        "se": se.astype(float),
        "t": tvals.astype(float),
        "p": pvals.astype(float),
        "ci_low": ci_low.astype(float),
        "ci_high": ci_high.astype(float),
    }


def durbin_watson_statistic(residuals: np.ndarray) -> float | None:
    """Durbin–Watson for OLS residuals (time order as given). ~2 suggests little first-order serial correlation."""
    u = np.asarray(residuals, dtype=float).ravel()
    if u.size < 2:
        return None
    den = float(np.dot(u, u))
    if den <= 1e-20:
        return None
    du = np.diff(u)
    return float(np.dot(du, du) / den)


def _breusch_godfrey_lm_single(
    resid: np.ndarray,
    X_factors: np.ndarray,
    nlags: int,
) -> dict[str, Any] | None:
    """One BG LM statistic: regress u_t on [1, X_t, u_{t-1}..u_{t-p}]; LM = T * R²_aux ~ chi2(p)."""
    u = np.asarray(resid, dtype=float).ravel()
    Xf = np.asarray(X_factors, dtype=float)
    n = u.size
    p = int(nlags)
    kf = Xf.shape[1]
    if n <= p + kf + 2 or Xf.shape[0] != n:
        return None
    rows: list[np.ndarray] = []
    for t in range(p, n):
        lags = np.array([u[t - j] for j in range(1, p + 1)], dtype=float)
        row = np.concatenate([[1.0], Xf[t].astype(float), lags])
        rows.append(row)
    Z = np.asarray(rows, dtype=float)
    yy = u[p:]
    gam, *_ = np.linalg.lstsq(Z, yy, rcond=None)
    fit = Z @ gam
    yyc = yy - float(np.mean(yy))
    sst = float(np.dot(yyc, yyc))
    sse = float(np.sum((yy - fit) ** 2))
    r2 = 1.0 - sse / sst if sst > 1e-20 else 0.0
    t_obs = int(Z.shape[0])
    lm = float(t_obs * r2)
    pv = float(1.0 - stats.chi2.cdf(lm, df=p))
    return {
        "lags": p,
        "lm_statistic": round(lm, 4),
        "df_chi2": p,
        "p_value": float(pv),
        "n_aux_observations": t_obs,
        "aux_r_squared": round(float(r2), 6),
    }


def factor_regression_serial_diagnostics(
    y: np.ndarray,
    X_factors: np.ndarray,
    *,
    bg_lags: tuple[int, ...] = FACTOR_REGRESSION_BG_LAGS,
) -> dict[str, Any]:
    """
    Serial-correlation diagnostics on **OLS residuals** of y ~ (const + X_factors).

    - Durbin–Watson on the residual series (same ordering as weekly regression).
    - Breusch–Godfrey LM for each ``p`` in ``bg_lags`` (chi-square with ``p`` df under H0).
    """
    base: dict[str, Any] = {
        "method": "durbin_watson_breusch_godfrey_lm",
        "h0": "no_autocorrelation_in_ols_residuals_up_to_lag_p",
        "bg_lags_requested": list(bg_lags),
    }
    try:
        yv = np.asarray(y, dtype=float).ravel()
        Xf = np.asarray(X_factors, dtype=float)
        if Xf.ndim != 2 or yv.size != Xf.shape[0] or yv.size < 5:
            return {**base, "error": "bad_shape"}
        if not np.isfinite(yv).all() or not np.isfinite(Xf).all():
            return {**base, "error": "non_finite"}
        n = yv.size
        Z = np.column_stack([np.ones(n), Xf])
        beta, *_ = np.linalg.lstsq(Z, yv, rcond=None)
        resid = yv - Z @ beta
        dw = durbin_watson_statistic(resid)
        bg_rows: list[dict[str, Any]] = []
        for p in bg_lags:
            row = _breusch_godfrey_lm_single(resid, Xf, p)
            if row:
                bg_rows.append(row)
        return {
            **base,
            "durbin_watson": round(float(dw), 4) if dw is not None else None,
            "breusch_godfrey": bg_rows,
            "notes": (
                "BG: auxiliary regression u_t on intercept, X_t, u_{t-1}..u_{t-p}; "
                "LM = T * R²_aux; asymptotic chi²(p) under H0. Same sample ordering as factor OLS."
            ),
        }
    except Exception as ex:
        return {**base, "error": str(ex)}


def factor_regression_heteroskedasticity_diagnostics(
    y: np.ndarray,
    X_factors: np.ndarray,
) -> dict[str, Any]:
    """
    Breusch-Pagan heteroskedasticity diagnostic on OLS residuals.

    Uses the same weekly rows as portfolio factor OLS: y ~ intercept + X_factors.
    Auxiliary regression is u_hat^2 ~ intercept + X_factors.
    """
    base: dict[str, Any] = {
        "method": "breusch_pagan_lm",
        "h0": "homoskedastic_ols_residuals",
        "auxiliary_regression": "squared_ols_residuals_on_intercept_and_factors",
    }
    try:
        yv = np.asarray(y, dtype=float).ravel()
        Xf = np.asarray(X_factors, dtype=float)
        if Xf.ndim != 2 or yv.size != Xf.shape[0] or yv.size < 5:
            return {**base, "error": "bad_shape"}
        if not np.isfinite(yv).all() or not np.isfinite(Xf).all():
            return {**base, "error": "non_finite"}
        n, k_factors = Xf.shape
        Z = np.column_stack([np.ones(n), Xf])
        if n <= Z.shape[1] + 1:
            return {**base, "error": "insufficient_observations"}

        beta, *_ = np.linalg.lstsq(Z, yv, rcond=None)
        resid = yv - Z @ beta
        resid_sq = resid ** 2.0
        centered = resid_sq - float(np.mean(resid_sq))
        ss_tot = float(np.dot(centered, centered))
        if ss_tot <= 1e-20:
            return {**base, "error": "constant_squared_residuals"}

        gamma, *_ = np.linalg.lstsq(Z, resid_sq, rcond=None)
        fitted = Z @ gamma
        ss_res = float(np.sum((resid_sq - fitted) ** 2.0))
        r2_aux = max(0.0, min(1.0, 1.0 - ss_res / ss_tot))

        lm = float(n * r2_aux)
        df_chi2 = int(k_factors)
        p_value = float(1.0 - stats.chi2.cdf(lm, df=df_chi2)) if df_chi2 > 0 else float("nan")

        df_num = int(k_factors)
        df_den = int(n - k_factors - 1)
        f_stat: float | None = None
        f_p_value: float | None = None
        if df_num > 0 and df_den > 0 and r2_aux < 1.0:
            f_stat = float((r2_aux / df_num) / ((1.0 - r2_aux) / df_den))
            f_p_value = float(1.0 - stats.f.cdf(f_stat, df_num, df_den))

        return {
            **base,
            "breusch_pagan": {
                "lm_statistic": round(lm, 4),
                "df_chi2": df_chi2,
                "p_value": p_value,
                "n_aux_observations": int(n),
                "aux_r_squared": round(float(r2_aux), 6),
                "f_statistic": round(float(f_stat), 4) if f_stat is not None else None,
                "f_df_num": df_num,
                "f_df_den": df_den,
                "f_p_value": f_p_value,
            },
            "notes": (
                "Breusch-Pagan: auxiliary regression u_hat^2 on intercept and factor regressors; "
                "LM = T * R^2_aux; asymptotic chi-square(k_factors) under H0."
            ),
        }
    except Exception as ex:
        return {**base, "error": str(ex)}


def _newey_west_covariance(X: np.ndarray, resid: np.ndarray, max_lags: int) -> np.ndarray:
    """
    Newey–West / HAC covariance for OLS beta with Bartlett kernel.

    X must include the intercept column; residuals from the same regression.
    """
    Z = np.asarray(X, dtype=float)
    u = np.asarray(resid, dtype=float).ravel()
    n, k = Z.shape
    L = int(max_lags)
    S = np.zeros((k, k), dtype=float)
    for t in range(n):
        S += (u[t] ** 2.0) * np.outer(Z[t], Z[t])
    for ell in range(1, L + 1):
        w = 1.0 - ell / float(L + 1)
        G = np.zeros((k, k), dtype=float)
        for t in range(ell, n):
            G += u[t] * u[t - ell] * np.outer(Z[t], Z[t - ell])
        S += w * (G + G.T)
    XtX_inv = np.linalg.inv(Z.T @ Z)
    cov = XtX_inv @ S @ XtX_inv
    cov *= n / max(n - k, 1)
    return cov


def factor_multicollinearity_diagnostics(
    X: np.ndarray,
    factor_columns: list[str],
    *,
    corr_decimals: int = 4,
    vif_decimals: int = 3,
) -> dict[str, Any]:
    """
    Multicollinearity diagnostics on the **same** factor rows used in portfolio OLS.

    - **correlation**: sample Pearson corr matrix of regressors (no intercept).
    - **cond_correlation_matrix**: cond(R) = λ_max / λ_min (eigvalsh on R, min clipped at 1e-15).
    - **vif**: classic VIF from auxiliary OLS of each column on all others (raw scale); meaningful when k >= 2.
    - **severity**: low | moderate | high | unknown (see docs/stress_testing_spec.md thresholds).

    Does not raise; returns ``error`` string on failure.
    """
    base: dict[str, Any] = {
        "method": "pearson_sample_corr_vif_raw_regressors",
    }
    try:
        Xa = np.asarray(X, dtype=float)
        if Xa.ndim != 2:
            return {**base, "error": "x_not_2d"}
        n, k = Xa.shape
        if n < 3 or k < 1:
            return {**base, "error": "insufficient_shape"}
        if not np.isfinite(Xa).all():
            return {**base, "error": "non_finite_x"}
        names = list(factor_columns)
        if len(names) != k:
            names = [f"f{i}" for i in range(k)]

        R = np.corrcoef(Xa.T)
        if not np.isfinite(R).all():
            return {**base, "error": "corr_nan_constant_column"}

        corr_nested: dict[str, dict[str, float]] = {}
        for i, ni in enumerate(names):
            corr_nested[ni] = {}
            for j, nj in enumerate(names):
                corr_nested[ni][nj] = round(float(R[i, j]), corr_decimals)

        pairs: list[dict[str, Any]] = []
        max_abs = -1.0
        strongest: dict[str, Any] | None = None
        for i in range(k):
            for j in range(i + 1, k):
                rho = float(R[i, j])
                pairs.append(
                    {
                        "factor_i": names[i],
                        "factor_j": names[j],
                        "rho": round(rho, corr_decimals),
                    }
                )
                if abs(rho) > max_abs:
                    max_abs = abs(rho)
                    strongest = {
                        "factor_i": names[i],
                        "factor_j": names[j],
                        "rho": round(rho, corr_decimals),
                    }
        pairs.sort(key=lambda d: abs(float(d["rho"])), reverse=True)

        ev = np.linalg.eigvalsh(R)
        ev = np.clip(ev, 0.0, None)
        lam_min = float(ev[0]) if len(ev) else float("nan")
        lam_max = float(ev[-1]) if len(ev) else float("nan")
        cond_r = float(lam_max / lam_min) if lam_min > 1e-15 else float("inf")

        vif_map: dict[str, float | None] = {}
        max_vif_finite = float("nan")
        max_vif_name_finite: str | None = None
        any_vif_infinite = False
        first_inf_factor: str | None = None
        if k >= 2:
            for j in range(k):
                y = Xa[:, j]
                Xo = np.delete(Xa, j, axis=1)
                Z = np.column_stack([np.ones(n), Xo])
                beta, *_ = np.linalg.lstsq(Z, y, rcond=None)
                resid = y - Z @ beta
                ss_res = float(np.dot(resid, resid))
                ym = y - float(np.mean(y))
                ss_tot = float(np.dot(ym, ym))
                r2_aux = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
                # Treat near-unity auxiliary R² as singular (duplicate / collinear columns).
                if r2_aux >= 1.0 - 1e-10:
                    vif_map[names[j]] = None
                    any_vif_infinite = True
                    if first_inf_factor is None:
                        first_inf_factor = names[j]
                else:
                    vj = 1.0 / (1.0 - r2_aux)
                    vif_map[names[j]] = round(float(vj), vif_decimals)
                    if not np.isfinite(max_vif_finite) or vj > max_vif_finite:
                        max_vif_finite = float(vj)
                        max_vif_name_finite = names[j]

        max_vif_is_infinite = any_vif_infinite
        max_vif_out: float | None = None
        max_vif_name: str | None = None
        if max_vif_is_infinite:
            max_vif_name = first_inf_factor
        elif np.isfinite(max_vif_finite):
            max_vif_out = round(float(max_vif_finite), vif_decimals)
            max_vif_name = max_vif_name_finite

        cond_r_out: float | None = round(float(cond_r), 3) if np.isfinite(cond_r) else None

        # Severity (aligned with stress_testing_spec.md)
        severity = "unknown"
        assessment_ru = "N/A: classification was not available."
        mv_for_rule = float("inf") if max_vif_is_infinite else float(max_vif_finite)
        cr_for_rule = float(cond_r) if np.isfinite(cond_r) else float("inf")
        if strongest is not None and (np.isfinite(mv_for_rule) or max_vif_is_infinite):
            mr = abs(float(strongest["rho"]))
            if max_vif_is_infinite or mv_for_rule >= 10 or cr_for_rule >= 80 or mr >= 0.95:
                severity = "high"
                assessment_ru = (
                    "High: strong linear relationships between factors; individual beta and p-value "
                    "estimates should be interpreted carefully even when R^2 is high."
                )
            elif mv_for_rule >= 5 or cr_for_rule >= 30 or mr >= 0.85:
                severity = "moderate"
                assessment_ru = (
                    "Moderate: visible collinearity; beta estimates for individual factors may be less stable."
                )
            else:
                severity = "low"
                assessment_ru = (
                    "Low: typical VIF and cond(R); collinearity is not dominant, but pairwise correlations still matter."
                )

        return {
            **base,
            "n_obs_factors": int(n),
            "n_factors": int(k),
            "correlation": corr_nested,
            "pairwise_correlations": pairs,
            "cond_correlation_matrix": cond_r_out,
            "cond_correlation_matrix_singular": (not np.isfinite(cond_r)),
            "corr_eigenvalues_min_max": [round(lam_min, 6), round(lam_max, 6)],
            "vif_by_factor": vif_map,
            "max_vif": max_vif_out,
            "max_vif_is_infinite": bool(max_vif_is_infinite),
            "max_vif_factor": max_vif_name,
            "strongest_pair": strongest,
            "severity": severity,
            "assessment_ru": assessment_ru,
        }
    except Exception as ex:
        return {**base, "error": str(ex)}


def _portfolio_factor_weekly_ols_rows(
    *,
    weights: dict[str, float],
    tickers: list[str],
    analysis_end_str: str,
    window_weeks: int,
    buffer_weeks: int = FACTOR_DOWNLOAD_BUFFER_WEEKS,
    factor_columns: tuple[str, ...] | list[str] | None = None,
) -> dict[str, Any]:
    """Return the exact weekly portfolio/factor rows used by portfolio OLS."""
    from src.data_yf import download_all

    wk = int(window_weeks)
    end_ts = pd.Timestamp(analysis_end_str)
    end_dl = (end_ts + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    start_ts = end_ts - pd.DateOffset(weeks=wk + int(buffer_weeks))
    start_dl = start_ts.strftime("%Y-%m-%d")

    use = [t for t in tickers if float(weights.get(t, 0.0)) > 0]
    if not use:
        use = list(tickers)
    use = [str(t).strip() for t in use if t and str(t).strip()]
    if not use:
        return {"error": "no_tickers", "n_obs": 0}

    daily = download_all(use, start_dl, end_dl)
    daily_prices: dict[str, pd.Series] = {}
    for t in use:
        df = daily.get(t)
        if df is None or df.empty or "Close" not in df.columns:
            continue
        daily_prices[t] = df["Close"].copy()

    asset_weekly = asset_weekly_returns_from_daily(daily_prices, start_dl, end_dl)
    factors = build_factor_matrix(start_dl, end_dl)
    if asset_weekly.empty or factors.empty:
        return {"error": "empty_weekly_inputs", "n_obs": 0}
    factor_cols = _select_factor_columns(factors, factor_columns)
    if not factor_cols:
        return {"error": "missing_factor_columns", "n_obs": 0}

    common = asset_weekly.index.intersection(factors.index).sort_values()
    common = common[common <= end_ts + pd.Timedelta(days=6)]
    if len(common) > wk:
        common = common[-wk:]
    if len(common) < 10:
        return {"error": "insufficient_common_rows", "n_obs": int(len(common))}

    y_frame = asset_weekly.reindex(common)
    x_frame = factors.reindex(common).loc[:, factor_cols].dropna()
    y_frame = y_frame.reindex(x_frame.index)
    if x_frame.empty or len(x_frame) < 10:
        return {"error": "insufficient_factor_rows", "n_obs": int(len(x_frame))}

    w_vec = np.array([float(weights.get(t, 0.0)) for t in y_frame.columns], dtype=float)
    y_port = (np.nan_to_num(y_frame.values, nan=0.0) * w_vec.reshape(1, -1)).sum(axis=1)

    valid = ~(np.isnan(y_port) | np.isnan(x_frame.values).any(axis=1))
    if valid.sum() < 10:
        return {"error": "insufficient_valid_rows", "n_obs": int(valid.sum())}

    return {
        "y": y_port[valid].astype(float),
        "X": x_frame.values[valid].astype(float),
        "factor_cols": list(x_frame.columns),
        "dates": [pd.Timestamp(x).strftime("%Y-%m-%d") for x in x_frame.index[valid]],
        "n_obs": int(valid.sum()),
        "window_weeks": int(wk),
    }


def portfolio_factor_regression_weekly(
    weights: dict[str, float],
    tickers: list[str],
    analysis_end_str: str,
    window_weeks: int,
    *,
    buffer_weeks: int = FACTOR_DOWNLOAD_BUFFER_WEEKS,
    alpha: float = 0.05,
    factor_columns: tuple[str, ...] | list[str] | None = None,
) -> dict[str, Any]:
    """
    Portfolio-level factor regression (weekly) with inference.

    This is separate from "portfolio betas = sum(w_i * beta_i)" and provides:
    - betas, t-stats, p-values, CI
    - R^2 / adj R^2
    - n_obs
    - ``factor_multicollinearity``: pairwise correlations, VIF, cond(R), severity (see stress spec §8.1)
    - ``serial_correlation_diagnostics``: Durbin–Watson, Breusch–Godfrey LM (see stress spec §8.2)
    - ``heteroskedasticity_diagnostics``: Breusch-Pagan LM/F test (see stress spec §8.3)
    """
    rows = _portfolio_factor_weekly_ols_rows(
        weights=weights,
        tickers=tickers,
        analysis_end_str=analysis_end_str,
        window_weeks=window_weeks,
        buffer_weeks=buffer_weeks,
        factor_columns=factor_columns,
    )
    if rows.get("error"):
        return {}

    y_valid = np.asarray(rows["y"], dtype=float)
    X_valid = np.asarray(rows["X"], dtype=float)
    inf = _ols_with_inference(y_valid, X_valid, add_const=True, alpha=alpha)
    if not inf:
        return {}

    factor_cols = list(rows["factor_cols"])
    # params[0] is intercept
    params = inf["params"]
    se = inf["se"]
    tvals = inf["t"]
    pvals = inf["p"]
    ci_low = inf["ci_low"]
    ci_high = inf["ci_high"]

    beta_keys = [FACTOR_TO_BETA_KEY.get(c, f"beta_{c}") for c in factor_cols]

    # Diagnostics on the same rows as OLS
    mc = factor_multicollinearity_diagnostics(X_valid, factor_cols)
    ser = factor_regression_serial_diagnostics(y_valid, X_valid, bg_lags=FACTOR_REGRESSION_BG_LAGS)
    het = factor_regression_heteroskedasticity_diagnostics(y_valid, X_valid)
    factor_cov = pd.DataFrame(X_valid, columns=factor_cols).cov(ddof=1).reindex(index=factor_cols, columns=factor_cols)
    portfolio_variance = float(np.var(y_valid, ddof=1)) if len(y_valid) >= 2 else float("nan")
    beta_vec = np.asarray(params[1:], dtype=float)
    factor_variance = (
        float(beta_vec.T @ factor_cov.values.astype(float) @ beta_vec)
        if len(beta_vec) == len(factor_cols)
        else float("nan")
    )
    variance_based_explained_share = (
        float(factor_variance / portfolio_variance)
        if np.isfinite(factor_variance)
        and np.isfinite(portfolio_variance)
        and portfolio_variance > FACTOR_VARIANCE_DECOMP_EPS
        else None
    )

    # HAC / Newey–West inference (same params, different standard errors)
    Z_full = np.column_stack([np.ones(len(X_valid)), X_valid])
    cov_hac = _newey_west_covariance(Z_full, y_valid - Z_full @ inf["params"], max_lags=FACTOR_REGRESSION_HAC_LAGS)
    se_hac = np.sqrt(np.maximum(np.diag(cov_hac), 0.0))
    df_resid = int(inf.get("df_resid", max(len(y_valid) - Z_full.shape[1], 1)))
    with np.errstate(divide="ignore", invalid="ignore"):
        t_hac = inf["params"] / se_hac
    p_hac = 2.0 * stats.t.sf(np.abs(t_hac), df=df_resid)
    tcrit_hac = float(stats.t.ppf(1.0 - alpha / 2.0, df=df_resid))
    ci_low_hac = inf["params"] - tcrit_hac * se_hac
    ci_high_hac = inf["params"] + tcrit_hac * se_hac

    out: dict[str, Any] = {
        "window_weeks": int(window_weeks),
        "n_obs": int(inf["n_obs"]),
        "variance_scale": "weekly",
        "portfolio_variance": portfolio_variance,
        "factor_variance": factor_variance,
        "variance_based_explained_share": variance_based_explained_share,
        "factor_order": factor_cols,
        "r2": float(inf["r2"]),
        "idiosyncratic_risk": float(inf["idiosyncratic_risk"]),
        "adj_r2": float(inf["adj_r2"]),
        "alpha": float(alpha),
        "se_type": str(inf.get("se_type", "classic_ols")),
        "ci_level": float(inf.get("ci_level", 0.95)),
        "intercept": float(params[0]),
        "betas": {k: float(v) for k, v in zip(beta_keys, params[1:])},
        "t": {k: float(v) for k, v in zip(beta_keys, tvals[1:])},
        "p": {k: float(v) for k, v in zip(beta_keys, pvals[1:])},
        "ci_low": {k: float(v) for k, v in zip(beta_keys, ci_low[1:])},
        "ci_high": {k: float(v) for k, v in zip(beta_keys, ci_high[1:])},
        "hac_inference": {
            "se_type": "hac_newey_west",
            "kernel": "bartlett",
            "max_lags": int(FACTOR_REGRESSION_HAC_LAGS),
            "se": se_hac.tolist(),
            "t": t_hac.tolist(),
            "p": p_hac.tolist(),
            "ci_low": ci_low_hac.tolist(),
            "ci_high": ci_high_hac.tolist(),
        },
        "heteroskedasticity_diagnostics": het,
        "serial_correlation_diagnostics": ser,
        "factor_multicollinearity": mc,
    }
    return out


def _kalman_uncertainty_class(std: float | None) -> str:
    if std is None or not np.isfinite(float(std)):
        return "unknown"
    v = float(std)
    if v <= FACTOR_KALMAN_UNCERTAINTY_LOW_LTE:
        return "low"
    if v <= FACTOR_KALMAN_UNCERTAINTY_MODERATE_LTE:
        return "moderate"
    return "high"


def _kalman_uncertainty_distribution(uncertainty_by_beta: dict[str, str]) -> dict[str, Any]:
    counts = {k: 0 for k in ("low", "moderate", "high", "unknown")}
    for val in uncertainty_by_beta.values():
        key = str(val) if str(val) in counts else "unknown"
        counts[key] += 1
    total = sum(counts.values())
    shares = {k: (float(v) / total if total else 0.0) for k, v in counts.items()}
    return {"counts": counts, "shares": shares}


def _kalman_beta_comparison(
    latest: dict[str, float],
    benchmark: dict[str, Any] | None,
) -> dict[str, Any]:
    by_beta: dict[str, dict[str, Any]] = {}
    for beta_key in sorted(set(latest).union(benchmark or {}), key=lambda b: BETA_ROW_ORDER.index(b) if b in BETA_ROW_ORDER else len(BETA_ROW_ORDER)):
        k_val = latest.get(beta_key)
        b_val_raw = (benchmark or {}).get(beta_key)
        try:
            if k_val is None or b_val_raw is None:
                continue
            b_val = float(b_val_raw)
            gap = float(k_val) - b_val
            abs_gap = abs(gap)
            rel_gap = abs_gap / max(abs(b_val), FACTOR_KALMAN_DIVERGENCE_MIN_ABS_DENOMINATOR)
            sign_diff = (float(k_val) * b_val) < 0.0
            by_beta[beta_key] = {
                "kalman": float(k_val),
                "benchmark": b_val,
                "gap": gap,
                "abs_gap": abs_gap,
                "relative_gap": rel_gap,
                "sign_difference": bool(sign_diff),
            }
        except (TypeError, ValueError):
            continue
    return {"by_beta": by_beta}


def _kalman_divergence_vs_5y(
    latest: dict[str, float],
    factor_betas_5y: dict[str, Any] | None,
) -> dict[str, Any]:
    comparison = _kalman_beta_comparison(latest, factor_betas_5y)
    by_beta: dict[str, dict[str, Any]] = {}
    divergent: list[str] = []
    for beta_key, row in (comparison.get("by_beta") or {}).items():
        sign_difference = bool(row.get("sign_difference"))
        abs_gap = float(row.get("abs_gap", 0.0))
        relative_gap = float(row.get("relative_gap", 0.0))
        is_divergent = (
            sign_difference
            or abs_gap >= FACTOR_KALMAN_DIVERGENCE_ABS_GAP_GTE
            or relative_gap >= FACTOR_KALMAN_DIVERGENCE_RELATIVE_GAP_GTE
        )
        by_beta[beta_key] = {
            **row,
            "divergent": bool(is_divergent),
            "reason": (
                "sign_difference"
                if sign_difference
                else "abs_gap"
                if abs_gap >= FACTOR_KALMAN_DIVERGENCE_ABS_GAP_GTE
                else "relative_gap"
                if relative_gap >= FACTOR_KALMAN_DIVERGENCE_RELATIVE_GAP_GTE
                else "none"
            ),
        }
        if is_divergent:
            divergent.append(beta_key)
    return {
        "method": "kalman_vs_5y_sign_or_gap",
        "thresholds": {
            "abs_gap_gte": FACTOR_KALMAN_DIVERGENCE_ABS_GAP_GTE,
            "relative_gap_gte": FACTOR_KALMAN_DIVERGENCE_RELATIVE_GAP_GTE,
            "relative_gap_denominator_floor": FACTOR_KALMAN_DIVERGENCE_MIN_ABS_DENOMINATOR,
        },
        "divergence_any": bool(divergent),
        "divergent_betas": divergent,
        "by_beta": by_beta,
    }


def _empty_kalman_report(reason: str, n_observations: int = 0) -> dict[str, Any]:
    return {
        "status": "unavailable",
        "method": "kalman_random_walk_weekly_factor_betas",
        "latest": {},
        "latest_raw": {},
        "latest_date": None,
        "window_weeks": 0,
        "n_observations": int(n_observations),
        "beta_cap_abs": FACTOR_KALMAN_BETA_CAP_ABS,
        "cap_diagnostics": {},
        "state_uncertainty": {},
        "uncertainty_by_beta": {},
        "uncertainty_severity_distribution": _kalman_uncertainty_distribution({}),
        "high_uncertainty_betas": [],
        "comparison_vs_5y": {"by_beta": {}},
        "comparison_vs_10y": {"by_beta": {}},
        "divergence_vs_5y": {
            "method": "kalman_vs_5y_sign_or_gap",
            "divergence_any": False,
            "divergent_betas": [],
            "by_beta": {},
        },
        "diagnostics": {"warning_codes": [str(reason)], "initialization_status": "failed"},
    }


def kalman_factor_betas_from_frames(
    portfolio_returns: pd.Series,
    factor_returns: pd.DataFrame,
    *,
    factor_betas_5y: dict[str, Any] | None = None,
    factor_betas_10y: dict[str, Any] | None = None,
    window_weeks: int = FACTOR_WEEKS_10Y,
    beta_cap_abs: float = FACTOR_KALMAN_BETA_CAP_ABS,
    min_observations: int = FACTOR_KALMAN_MIN_OBSERVATIONS,
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    """
    Kalman-filter portfolio factor betas on already-built weekly data.

    The model is diagnostic only: beta states follow a random walk and reported
    betas are capped while raw filtered states remain in diagnostics.
    """
    if portfolio_returns is None or factor_returns is None or factor_returns.empty:
        return _empty_kalman_report("empty_inputs"), pd.DataFrame(), pd.DataFrame()

    y = pd.Series(portfolio_returns, dtype=float).copy()
    y.index = pd.to_datetime(y.index).tz_localize(None)
    factors = factor_returns.copy()
    factors.index = pd.to_datetime(factors.index).tz_localize(None)
    factor_cols = [c for c in FACTOR_COLUMN_ORDER if c in factors.columns]
    if not factor_cols:
        return _empty_kalman_report("missing_factor_columns"), pd.DataFrame(), pd.DataFrame()

    common = y.dropna().index.intersection(factors[factor_cols].dropna().index).sort_values()
    if int(window_weeks) > 0 and len(common) > int(window_weeks):
        common = common[-int(window_weeks):]
    if len(common) < int(min_observations):
        return _empty_kalman_report("insufficient_observations", len(common)), pd.DataFrame(), pd.DataFrame()

    y_arr = y.reindex(common).values.astype(float)
    x_arr = factors.reindex(common).loc[:, factor_cols].values.astype(float)
    n_obs, n_factors = x_arr.shape
    beta_keys = [FACTOR_TO_BETA_KEY.get(c, f"beta_{c}") for c in factor_cols]

    init_n = min(FACTOR_KALMAN_INIT_OBSERVATIONS, n_obs)
    init_n = max(init_n, n_factors + 2)
    init_n = min(init_n, n_obs)
    z_init = np.column_stack([np.ones(init_n), x_arr[:init_n]])
    try:
        state = np.linalg.lstsq(z_init, y_arr[:init_n], rcond=None)[0].astype(float)
    except Exception:
        return _empty_kalman_report("initial_ols_failed", n_obs), pd.DataFrame(), pd.DataFrame()

    resid = y_arr[:init_n] - z_init @ state
    resid_var = float(np.var(resid, ddof=1)) if len(resid) >= 2 else 0.0
    y_var = float(np.var(y_arr, ddof=1)) if len(y_arr) >= 2 else 0.0
    r_var = max(resid_var, y_var * 1e-4, 1e-8)

    try:
        p_state = np.linalg.pinv(z_init.T @ z_init) * r_var
    except Exception:
        p_state = np.eye(n_factors + 1) * 0.05
    p_state = np.asarray(p_state, dtype=float)
    p_state = (p_state + p_state.T) / 2.0
    p_state += np.eye(n_factors + 1) * 1e-8

    q_diag = np.empty(n_factors + 1, dtype=float)
    q_diag[0] = max(r_var * 0.01, 1e-10)
    for i, beta in enumerate(state[1:], start=1):
        scale = max(abs(float(beta)), 0.10)
        initial_beta_variance = max(float(p_state[i, i]), 1e-8)
        q_diag[i] = max(initial_beta_variance * 0.05, (0.02 * scale) ** 2)
    q_state = np.diag(q_diag)
    identity = np.eye(n_factors + 1)

    raw_rows: list[dict[str, float]] = []
    capped_rows: list[dict[str, float]] = []
    std_rows: list[dict[str, float]] = []
    idx: list[pd.Timestamp] = []
    for i in range(n_obs):
        h = np.concatenate([[1.0], x_arr[i]]).astype(float)
        p_pred = p_state + q_state
        state_pred = state
        s_val = float(h @ p_pred @ h.T + r_var)
        if not np.isfinite(s_val) or s_val <= 1e-12:
            s_val = 1e-12
        k_gain = (p_pred @ h.T) / s_val
        innovation = float(y_arr[i] - h @ state_pred)
        state = state_pred + k_gain * innovation
        kh = np.outer(k_gain, h)
        p_state = (identity - kh) @ p_pred @ (identity - kh).T + np.outer(k_gain, k_gain) * r_var
        p_state = (p_state + p_state.T) / 2.0

        beta_raw = state[1:].astype(float)
        beta_capped = np.clip(beta_raw, -float(beta_cap_abs), float(beta_cap_abs))
        beta_std = np.sqrt(np.maximum(np.diag(p_state)[1:], 0.0))
        raw_rows.append({k: float(v) for k, v in zip(beta_keys, beta_raw)})
        capped_rows.append({k: float(v) for k, v in zip(beta_keys, beta_capped)})
        std_rows.append({k: float(v) for k, v in zip(beta_keys, beta_std)})
        idx.append(pd.Timestamp(common[i]))

    raw_df = pd.DataFrame(raw_rows, index=pd.DatetimeIndex(idx, name="date"))
    capped_df = pd.DataFrame(capped_rows, index=pd.DatetimeIndex(idx, name="date"))
    std_df = pd.DataFrame(std_rows, index=pd.DatetimeIndex(idx, name="date"))
    latest_raw = {k: float(v) for k, v in raw_df.iloc[-1].items()}
    latest = {k: float(v) for k, v in capped_df.iloc[-1].items()}
    state_uncertainty = {k: float(v) for k, v in std_df.iloc[-1].items()}
    uncertainty_by_beta = {k: _kalman_uncertainty_class(v) for k, v in state_uncertainty.items()}
    high_uncertainty_betas = [k for k, v in uncertainty_by_beta.items() if v == "high"]
    cap_diagnostics = {
        k: {
            "was_capped": bool(abs(latest_raw[k]) > float(beta_cap_abs)),
            "raw_value": float(latest_raw[k]),
            "capped_value": float(latest[k]),
        }
        for k in latest
    }

    comparison_vs_5y = _kalman_beta_comparison(latest, factor_betas_5y)
    comparison_vs_10y = _kalman_beta_comparison(latest, factor_betas_10y)
    divergence_vs_5y = _kalman_divergence_vs_5y(latest, factor_betas_5y)
    latest_rows = []
    for beta_key in _ordered_beta_keys_for_kalman(latest):
        row5 = (comparison_vs_5y.get("by_beta") or {}).get(beta_key) or {}
        row10 = (comparison_vs_10y.get("by_beta") or {}).get(beta_key) or {}
        div = (divergence_vs_5y.get("by_beta") or {}).get(beta_key) or {}
        latest_rows.append(
            {
                "beta": beta_key,
                "latest_raw": latest_raw.get(beta_key),
                "latest": latest.get(beta_key),
                "beta_5y": row5.get("benchmark"),
                "beta_10y": row10.get("benchmark"),
                "gap_vs_5y": row5.get("gap"),
                "relative_gap_vs_5y": row5.get("relative_gap"),
                "divergence_vs_5y": bool(div.get("divergent", False)),
                "divergence_reason": div.get("reason", "none"),
                "state_uncertainty": state_uncertainty.get(beta_key),
                "uncertainty_class": uncertainty_by_beta.get(beta_key, "unknown"),
                "was_capped": cap_diagnostics.get(beta_key, {}).get("was_capped", False),
            }
        )

    report = {
        "status": "available",
        "method": "kalman_random_walk_weekly_factor_betas",
        "latest": latest,
        "latest_raw": latest_raw,
        "latest_date": idx[-1].strftime("%Y-%m-%d"),
        "window_weeks": int(window_weeks),
        "n_observations": int(n_obs),
        "beta_cap_abs": float(beta_cap_abs),
        "cap_diagnostics": cap_diagnostics,
        "state_uncertainty": state_uncertainty,
        "uncertainty_by_beta": uncertainty_by_beta,
        "uncertainty_severity_distribution": _kalman_uncertainty_distribution(uncertainty_by_beta),
        "high_uncertainty_betas": high_uncertainty_betas,
        "comparison_vs_5y": comparison_vs_5y,
        "comparison_vs_10y": comparison_vs_10y,
        "divergence_vs_5y": divergence_vs_5y,
        "diagnostics": {
            "initialization_status": "ols_initialized",
            "initialization_observations": int(init_n),
            "observation_variance": float(r_var),
            "initial_residual_variance": float(resid_var),
            "state_noise_diagonal": [float(v) for v in q_diag.tolist()],
            "factor_order": list(factor_cols),
            "beta_order": list(beta_keys),
            "warning_codes": [],
        },
    }
    return report, capped_df, pd.DataFrame(latest_rows)


def _ordered_beta_keys_for_kalman(*maps: dict[str, Any]) -> list[str]:
    keys: set[str] = set()
    for m in maps:
        if isinstance(m, dict):
            keys.update(str(k) for k in m.keys())
    return sorted(keys, key=lambda b: BETA_ROW_ORDER.index(b) if b in BETA_ROW_ORDER else len(BETA_ROW_ORDER))


def compute_portfolio_kalman_factor_betas_weekly(
    weights: dict[str, float],
    tickers: list[str],
    analysis_end_str: str,
    *,
    factor_betas_5y: dict[str, Any] | None = None,
    factor_betas_10y: dict[str, Any] | None = None,
    window_weeks: int = FACTOR_WEEKS_10Y,
    buffer_weeks: int = FACTOR_DOWNLOAD_BUFFER_WEEKS,
    beta_cap_abs: float = FACTOR_KALMAN_BETA_CAP_ABS,
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    rows = _portfolio_factor_weekly_ols_rows(
        weights=weights,
        tickers=tickers,
        analysis_end_str=analysis_end_str,
        window_weeks=window_weeks,
        buffer_weeks=buffer_weeks,
        factor_columns=FACTOR_COLUMN_ORDER,
    )
    if rows.get("error"):
        return _empty_kalman_report(str(rows.get("error")), int(rows.get("n_obs", 0))), pd.DataFrame(), pd.DataFrame()
    y = pd.Series(
        np.asarray(rows["y"], dtype=float),
        index=pd.to_datetime(rows["dates"]),
        name="portfolio_return",
    )
    factors = pd.DataFrame(
        np.asarray(rows["X"], dtype=float),
        index=pd.to_datetime(rows["dates"]),
        columns=list(rows["factor_cols"]),
    )
    report, history_df, latest_df = kalman_factor_betas_from_frames(
        y,
        factors,
        factor_betas_5y=factor_betas_5y,
        factor_betas_10y=factor_betas_10y,
        window_weeks=window_weeks,
        beta_cap_abs=beta_cap_abs,
    )
    if report.get("status") == "available":
        report["window_weeks"] = int(rows.get("window_weeks", window_weeks))
    return report, history_df, latest_df


def attach_kalman_factor_betas_to_stress_report(
    stress_report: dict[str, Any],
    *,
    weights: dict[str, float],
    tickers: list[str],
    analysis_end_str: str,
    output_dir_csv: Path | str | None = None,
    window_weeks: int = FACTOR_WEEKS_10Y,
) -> dict[str, Any]:
    report, history_df, latest_df = compute_portfolio_kalman_factor_betas_weekly(
        weights=weights,
        tickers=tickers,
        analysis_end_str=analysis_end_str,
        factor_betas_5y=stress_report.get("factor_betas_5y") or stress_report.get("factor_betas") or {},
        factor_betas_10y=stress_report.get("factor_betas_10y") or {},
        window_weeks=window_weeks,
    )
    artifacts: dict[str, str] = {}
    if output_dir_csv is not None and report.get("status") == "available":
        out_dir = Path(output_dir_csv)
        out_dir.mkdir(parents=True, exist_ok=True)
        if not history_df.empty:
            history_path = out_dir / "kalman_factor_betas_weekly.csv"
            history_df.round(6).to_csv(history_path, index=True)
            artifacts["weekly_csv"] = history_path.name
        if not latest_df.empty:
            latest_path = out_dir / "kalman_factor_betas_latest.csv"
            latest_df.round(6).to_csv(latest_path, index=False)
            artifacts["latest_csv"] = latest_path.name
    if artifacts:
        report["artifacts"] = artifacts
    stress_report["factor_betas_kalman"] = report
    return stress_report


def factor_oos_beta_shock_explainability(
    *,
    weights: dict[str, float],
    tickers: list[str],
    historical_results: list[dict[str, Any]],
    factor_betas_5y: dict[str, float] | None,
    factor_betas_10y: dict[str, float] | None,
    factor_betas_adjusted: dict[str, float] | None = None,
    rolling_window_weeks: int = FACTOR_WEEKS_3Y,
) -> dict[str, Any]:
    """
    Out-of-sample explainability of episode PnL via beta × realized factor shock.

    For each episode (expects episode_start / episode_end in historical_results):
    - computes weekly factor shocks over the episode (sum of weekly factor series),
    - computes model PnL for fixed 5Y/10Y betas and rolling-pre-episode betas,
    - compares against pnl_real_episode when present.
    """
    out: dict[str, Any] = {
        "method": "episode_beta_times_realized_factor_shock",
        "rolling_pre_window_weeks": int(rolling_window_weeks),
        "episodes": [],
        "summary": {},
    }
    b5 = _filter_beta_map_to_base(factor_betas_5y)
    b10 = _filter_beta_map_to_base(factor_betas_10y)
    badj = _filter_beta_map_to_base(factor_betas_adjusted)
    if not historical_results:
        out["error"] = "historical_results_empty"
        return out

    def _model_pnl(beta_map: dict[str, float], shock: pd.Series) -> tuple[float, dict[str, float]]:
        total = 0.0
        contrib: dict[str, float] = {}
        for fac_col, shock_v in shock.items():
            bkey = FACTOR_TO_BETA_KEY.get(str(fac_col))
            if not bkey or bkey not in BASE_BETA_ROW_ORDER:
                continue
            c = float(beta_map.get(bkey, 0.0)) * float(shock_v)
            contrib[bkey] = c
            total += c
        return float(total), contrib

    abs_err_5: list[float] = []
    abs_err_10: list[float] = []
    abs_err_r3: list[float] = []
    abs_err_adj: list[float] = []

    for row in historical_results:
        ep = str(row.get("episode", ""))
        start = row.get("episode_start")
        end = row.get("episode_end")
        if not start or not end:
            out["episodes"].append({
                "episode": ep,
                "error": "missing_episode_start_end",
            })
            continue
        fac = build_factor_matrix(str(start), str(end))
        if fac.empty:
            out["episodes"].append({
                "episode": ep,
                "episode_start": start,
                "episode_end": end,
                "error": "empty_factor_matrix",
            })
            continue
        shock = fac.sum()
        pnl5, c5 = _model_pnl(b5, shock)
        pnl10, c10 = _model_pnl(b10, shock)
        pnl_adj, c_adj = _model_pnl(badj, shock)

        pre_end = (pd.Timestamp(start) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        r3 = portfolio_factor_regression_weekly(
            weights=weights,
            tickers=tickers,
            analysis_end_str=pre_end,
            window_weeks=rolling_window_weeks,
        )
        b3 = r3.get("betas", {}) if isinstance(r3, dict) else {}
        pnl3, c3 = _model_pnl(b3 if isinstance(b3, dict) else {}, shock)

        pnl_real = row.get("pnl_real_episode")
        if isinstance(pnl_real, (int, float)) and np.isfinite(pnl_real):
            abs_err_5.append(abs(pnl5 - float(pnl_real)))
            abs_err_10.append(abs(pnl10 - float(pnl_real)))
            abs_err_r3.append(abs(pnl3 - float(pnl_real)))
            if badj:
                abs_err_adj.append(abs(pnl_adj - float(pnl_real)))

        out["episodes"].append({
            "episode": ep,
            "episode_start": str(start),
            "episode_end": str(end),
            "n_weeks_factors": int(len(fac)),
            "pnl_real_episode": float(pnl_real) if isinstance(pnl_real, (int, float)) else None,
            "pnl_model_5y": float(pnl5),
            "pnl_model_10y": float(pnl10),
            "pnl_model_adjusted": float(pnl_adj),
            "pnl_model_roll3y_pre": float(pnl3),
            "abs_error_5y": (abs(pnl5 - float(pnl_real)) if isinstance(pnl_real, (int, float)) else None),
            "abs_error_10y": (abs(pnl10 - float(pnl_real)) if isinstance(pnl_real, (int, float)) else None),
            "abs_error_adjusted": (abs(pnl_adj - float(pnl_real)) if isinstance(pnl_real, (int, float)) else None),
            "abs_error_roll3y_pre": (abs(pnl3 - float(pnl_real)) if isinstance(pnl_real, (int, float)) else None),
            "factor_shock_sum": {k: float(v) for k, v in shock.items()},
            "factor_contrib_5y": {k: float(v) for k, v in c5.items()},
            "factor_contrib_10y": {k: float(v) for k, v in c10.items()},
            "factor_contrib_adjusted": {k: float(v) for k, v in c_adj.items()},
            "factor_contrib_roll3y_pre": {k: float(v) for k, v in c3.items()},
            "roll3y_pre_analysis_end": pre_end,
            "roll3y_pre_betas": {k: float(v) for k, v in (b3.items() if isinstance(b3, dict) else [])},
        })

    if abs_err_5 and abs_err_10 and abs_err_r3:
        summary: dict[str, Any] = {
            "mean_abs_error_5y": float(np.mean(abs_err_5)),
            "mean_abs_error_10y": float(np.mean(abs_err_10)),
            "mean_abs_error_roll3y_pre": float(np.mean(abs_err_r3)),
            "n_episodes_with_real_pnl": int(len(abs_err_5)),
        }
        if abs_err_adj:
            summary["mean_abs_error_adjusted"] = float(np.mean(abs_err_adj))
        out["summary"] = summary
    return out


HISTORICAL_FACTOR_ATTRIBUTION_METHOD = "model_based_beta_times_realized_factor_shock"
HISTORICAL_FACTOR_ATTRIBUTION_CAVEAT = (
    "Model-based attribution: beta times realized factor shock. "
    "This is not a pure realized causal decomposition."
)


def _factor_driver_rows(contrib: dict[str, Any], *, top_n: int = 3) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for beta_key, value in (contrib or {}).items():
        v = _safe_float(value)
        if v is None:
            continue
        rows.append(
            {
                "beta_key": str(beta_key),
                "factor": get_factor_display_name(str(beta_key)),
                "pnl_pct": float(v),
                "abs_pnl_pct": abs(float(v)),
                "direction": "loss" if v < 0 else "gain" if v > 0 else "flat",
            }
        )
    rows.sort(key=lambda row: row["abs_pnl_pct"], reverse=True)
    for idx, row in enumerate(rows[:top_n], start=1):
        row["rank"] = idx
    return rows[:top_n]


def build_factor_beta_adjustment_overlay(
    factor_betas_5y: dict[str, Any] | None,
    factor_betas_10y: dict[str, Any] | None,
    factor_betas_stability: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build stability-adjusted factor beta overlay without changing raw beta outputs."""
    raw_5y = _filter_beta_map_to_base(factor_betas_5y)
    raw_10y = _filter_beta_map_to_base(factor_betas_10y)
    stability_by_beta = (
        (factor_betas_stability or {}).get("by_beta")
        if isinstance(factor_betas_stability, dict)
        else {}
    ) or {}
    beta_keys = _ordered_base_beta_keys(raw_5y, raw_10y, stability_by_beta)
    adjusted: dict[str, float] = {}
    confidence_by_beta: dict[str, float] = {}
    severity_by_beta: dict[str, str] = {}
    reason_by_beta: dict[str, str] = {}
    divergence_by_beta: dict[str, Any] = {}
    strong_divergence_betas: list[str] = []

    for beta_key in beta_keys:
        raw5 = _safe_float(raw_5y.get(beta_key))
        raw10 = _safe_float(raw_10y.get(beta_key))
        sev = "unknown"
        if isinstance(stability_by_beta.get(beta_key), dict):
            sev = str(stability_by_beta[beta_key].get("combined_severity", "unknown"))
        if sev not in FACTOR_BETA_ADJUSTED_CONFIDENCE_BY_SEVERITY:
            sev = "unknown"
        confidence = float(FACTOR_BETA_ADJUSTED_CONFIDENCE_BY_SEVERITY[sev])
        confidence_by_beta[beta_key] = confidence
        severity_by_beta[beta_key] = sev

        beta_anchor = raw10 if raw10 is not None else raw5
        beta_source = raw5 if raw5 is not None else raw10
        if beta_source is None:
            adjusted[beta_key] = 0.0
            reason_by_beta[beta_key] = "beta_missing_keep_zero"
        elif beta_anchor is None:
            adjusted[beta_key] = float(beta_source)
            reason_by_beta[beta_key] = "anchor_missing_keep_raw"
        else:
            adjusted_val = confidence * float(beta_source) + (1.0 - confidence) * float(beta_anchor)
            adjusted[beta_key] = float(adjusted_val)
            if raw10 is None:
                reason_by_beta[beta_key] = "10y_anchor_missing_keep_5y_raw"
            elif sev == "low":
                reason_by_beta[beta_key] = "low_severity_keep_5y_raw"
            else:
                reason_by_beta[beta_key] = f"{sev}_severity_shrink_toward_10y_anchor"

        abs_gap = abs(float(raw5) - float(raw10)) if raw5 is not None and raw10 is not None else None
        rel_gap = (
            abs_gap / max(abs(float(raw5)), FACTOR_STABILITY_MIN_ABS_BETA)
            if abs_gap is not None and raw5 is not None
            else None
        )
        sign_mismatch = (
            raw5 is not None and raw10 is not None and _beta_sign(float(raw5)) * _beta_sign(float(raw10)) < 0
        )
        strong_divergence = bool(
            sign_mismatch
            or (
                rel_gap is not None
                and rel_gap >= FACTOR_BETA_DIVERGENCE_RELATIVE_GAP_STRONG_GTE
            )
        )
        divergence_by_beta[beta_key] = {
            "beta_5y": float(raw5) if raw5 is not None else None,
            "beta_10y": float(raw10) if raw10 is not None else None,
            "absolute_gap": float(abs_gap) if abs_gap is not None else None,
            "relative_gap": float(rel_gap) if rel_gap is not None else None,
            "sign_mismatch": bool(sign_mismatch),
            "strong_divergence": strong_divergence,
        }
        if strong_divergence:
            strong_divergence_betas.append(beta_key)

    return {
        "raw": {str(k): float(v) for k, v in raw_5y.items() if _safe_float(v) is not None},
        "adjusted": adjusted,
        "confidence_by_beta": confidence_by_beta,
        "severity_by_beta": severity_by_beta,
        "anchor_source": FACTOR_BETA_ADJUSTED_ANCHOR_SOURCE,
        "shrinkage_method": FACTOR_BETA_ADJUSTED_METHOD,
        "adjustment_reason_by_beta": reason_by_beta,
        "beta_5y_vs_10y_divergence": {
            "by_beta": divergence_by_beta,
            "strong_divergence_any": bool(strong_divergence_betas),
            "strong_divergence_betas": strong_divergence_betas,
            "relative_gap_strong_gte": FACTOR_BETA_DIVERGENCE_RELATIVE_GAP_STRONG_GTE,
        },
    }


def build_synthetic_factor_pnl_adjusted_overlay(
    scenario_results: list[dict[str, Any]],
    raw_betas: dict[str, Any] | None,
    adjusted_betas: dict[str, Any] | None,
) -> dict[str, Any]:
    """Compute synthetic factor PnL using raw and adjusted betas side by side."""
    overlay_rows: list[dict[str, Any]] = []
    raw_map = raw_betas or {}
    adj_map = adjusted_betas or {}
    for row in scenario_results or []:
        if not isinstance(row, dict):
            continue
        shock = row.get("shock_vector") or {}
        if not isinstance(shock, dict):
            continue
        pnl_raw, contrib_raw = 0.0, {}
        pnl_adj, contrib_adj = 0.0, {}
        for beta_key in _ordered_beta_keys(raw_map, adj_map):
            shock_key = FACTOR_BETA_TO_SYNTHETIC_SHOCK_KEY.get(beta_key)
            if shock_key is None:
                continue
            shock_val = _safe_float(shock.get(shock_key))
            if shock_val is None:
                continue
            raw_val = float(raw_map.get(beta_key, 0.0))
            adj_val = float(adj_map.get(beta_key, 0.0))
            contrib_raw[beta_key] = float(raw_val * shock_val)
            contrib_adj[beta_key] = float(adj_val * shock_val)
            pnl_raw += contrib_raw[beta_key]
            pnl_adj += contrib_adj[beta_key]
        pnl_delta = float(pnl_adj - pnl_raw)
        pnl_abs_delta = abs(pnl_delta)
        pnl_relative_delta = pnl_abs_delta / max(abs(float(pnl_raw)), 0.01)
        overlay_rows.append(
            {
                "scenario_id": str(row.get("scenario_id", "")),
                "pnl_model_raw": float(pnl_raw),
                "pnl_model_adjusted": float(pnl_adj),
                "adjusted_minus_raw": pnl_delta,
                "pnl_abs_delta": float(pnl_abs_delta),
                "pnl_relative_delta": float(pnl_relative_delta),
                "pnl_by_factor_pct_raw": {str(k): float(v) for k, v in contrib_raw.items() if abs(float(v)) > 0.0},
                "pnl_by_factor_pct_adjusted": {str(k): float(v) for k, v in contrib_adj.items() if abs(float(v)) > 0.0},
            }
        )
    return {
        "method": "raw_vs_stability_adjusted_beta_overlay",
        "scenarios": overlay_rows,
    }


def build_raw_vs_adjusted_pnl_signal(
    synthetic_overlay: dict[str, Any] | None,
    factor_beta_shock_oos_raw: dict[str, Any] | None,
    factor_beta_shock_oos_adjusted: dict[str, Any] | None,
) -> dict[str, Any]:
    """Summarize when adjusted beta materially changes factor-model PnL."""
    synthetic_rows: list[dict[str, Any]] = []
    historical_rows: list[dict[str, Any]] = []
    material_scenarios: list[str] = []
    material_historical: list[str] = []

    for row in (synthetic_overlay or {}).get("scenarios") or []:
        if not isinstance(row, dict):
            continue
        pnl_raw = _safe_float(row.get("pnl_model_raw"))
        pnl_adjusted = _safe_float(row.get("pnl_model_adjusted"))
        if pnl_raw is None or pnl_adjusted is None:
            continue
        pnl_delta = float(pnl_adjusted - pnl_raw)
        pnl_abs_delta = abs(pnl_delta)
        pnl_relative_delta = pnl_abs_delta / max(abs(float(pnl_raw)), 0.01)
        material = bool(
            pnl_relative_delta >= FACTOR_RAW_VS_ADJUSTED_PNL_RELATIVE_DELTA_MATERIAL_GTE
            or pnl_abs_delta >= FACTOR_RAW_VS_ADJUSTED_PNL_ABS_DELTA_MATERIAL_GTE
        )
        signal_row = {
            "scenario_id": str(row.get("scenario_id", "")),
            "pnl_raw": float(pnl_raw),
            "pnl_adjusted": float(pnl_adjusted),
            "pnl_delta": float(pnl_delta),
            "pnl_abs_delta": float(pnl_abs_delta),
            "pnl_relative_delta": float(pnl_relative_delta),
            "material_difference": material,
        }
        synthetic_rows.append(signal_row)
        if material:
            material_scenarios.append(signal_row["scenario_id"])

    raw_by_episode = {
        str(row.get("episode")): row
        for row in (factor_beta_shock_oos_raw or {}).get("episodes") or []
        if isinstance(row, dict)
    }
    adjusted_by_episode = {
        str(row.get("episode")): row
        for row in (factor_beta_shock_oos_adjusted or {}).get("episodes") or []
        if isinstance(row, dict)
    }
    for episode in sorted(set(raw_by_episode).intersection(adjusted_by_episode)):
        raw_row = raw_by_episode[episode]
        adj_row = adjusted_by_episode[episode]
        pnl_raw = _safe_float(raw_row.get("pnl_model_5y"))
        pnl_adjusted = _safe_float(adj_row.get("pnl_model_adjusted"))
        if pnl_raw is None or pnl_adjusted is None:
            continue
        pnl_delta = float(pnl_adjusted - pnl_raw)
        pnl_abs_delta = abs(pnl_delta)
        pnl_relative_delta = pnl_abs_delta / max(abs(float(pnl_raw)), 0.01)
        material = bool(
            pnl_relative_delta >= FACTOR_RAW_VS_ADJUSTED_PNL_RELATIVE_DELTA_MATERIAL_GTE
            or pnl_abs_delta >= FACTOR_RAW_VS_ADJUSTED_PNL_ABS_DELTA_MATERIAL_GTE
        )
        signal_row = {
            "episode": episode,
            "pnl_raw": float(pnl_raw),
            "pnl_adjusted": float(pnl_adjusted),
            "pnl_delta": float(pnl_delta),
            "pnl_abs_delta": float(pnl_abs_delta),
            "pnl_relative_delta": float(pnl_relative_delta),
            "material_difference": material,
        }
        historical_rows.append(signal_row)
        if material:
            material_historical.append(episode)

    return {
        "synthetic": synthetic_rows,
        "historical": historical_rows,
        "material_difference_any": bool(material_scenarios or material_historical),
        "material_scenarios": material_scenarios,
        "material_historical_episodes": material_historical,
        "relative_delta_material_gte": FACTOR_RAW_VS_ADJUSTED_PNL_RELATIVE_DELTA_MATERIAL_GTE,
        "abs_delta_material_gte": FACTOR_RAW_VS_ADJUSTED_PNL_ABS_DELTA_MATERIAL_GTE,
    }


def build_factor_beta_diagnostic_overlay(
    *,
    weights: dict[str, float],
    tickers: list[str],
    scenario_results: list[dict[str, Any]],
    historical_results: list[dict[str, Any]],
    factor_betas_5y: dict[str, Any] | None,
    factor_betas_10y: dict[str, Any] | None,
    factor_betas_stability: dict[str, Any] | None,
    factor_beta_shock_oos_raw: dict[str, Any] | None = None,
    rolling_window_weeks: int = FACTOR_WEEKS_3Y,
) -> dict[str, Any]:
    """Build the full adjusted-beta overlay package for stress diagnostics."""
    factor_betas_adjusted = build_factor_beta_adjustment_overlay(
        factor_betas_5y,
        factor_betas_10y,
        factor_betas_stability,
    )
    adjusted_map = factor_betas_adjusted.get("adjusted") if isinstance(factor_betas_adjusted, dict) else {}
    synthetic_overlay = build_synthetic_factor_pnl_adjusted_overlay(
        scenario_results,
        factor_betas_5y,
        adjusted_map if isinstance(adjusted_map, dict) else {},
    )
    factor_beta_shock_oos_adjusted = factor_oos_beta_shock_explainability(
        weights=weights,
        tickers=tickers,
        historical_results=historical_results,
        factor_betas_5y=factor_betas_5y,
        factor_betas_10y=factor_betas_10y,
        factor_betas_adjusted=adjusted_map if isinstance(adjusted_map, dict) else {},
        rolling_window_weeks=rolling_window_weeks,
    )
    historical_results_adjusted = enrich_historical_results_with_adjusted_factor_attribution(
        historical_results,
        factor_beta_shock_oos_adjusted,
    )
    raw_oos = factor_beta_shock_oos_raw
    if not isinstance(raw_oos, dict) or not raw_oos:
        raw_oos = factor_oos_beta_shock_explainability(
            weights=weights,
            tickers=tickers,
            historical_results=historical_results,
            factor_betas_5y=factor_betas_5y,
            factor_betas_10y=factor_betas_10y,
            rolling_window_weeks=rolling_window_weeks,
        )
    raw_vs_adjusted_signal = build_raw_vs_adjusted_pnl_signal(
        synthetic_overlay,
        raw_oos,
        factor_beta_shock_oos_adjusted,
    )
    return {
        "factor_betas_adjusted": factor_betas_adjusted,
        "synthetic_factor_pnl_adjusted": synthetic_overlay,
        "factor_beta_shock_oos_adjusted": factor_beta_shock_oos_adjusted,
        "historical_results_adjusted": historical_results_adjusted,
        "raw_vs_adjusted_pnl_signal": raw_vs_adjusted_signal,
    }


def _pair_corr_from_multicollinearity(mc: dict[str, Any] | None, left: str, right: str) -> float | None:
    if not isinstance(mc, dict):
        return None
    corr = mc.get("correlation")
    if isinstance(corr, dict):
        for a, b in ((left, right), (right, left)):
            value = (corr.get(a) or {}).get(b) if isinstance(corr.get(a), dict) else None
            v = _safe_float(value)
            if v is not None:
                return v
    for row in mc.get("pairwise_correlations") or []:
        if not isinstance(row, dict):
            continue
        pair = {str(row.get("factor_i")), str(row.get("factor_j"))}
        if pair == {left, right}:
            return _safe_float(row.get("rho"))
    return None


def _oil_collinearity_severity(correlation: float | None, vif: float | None) -> str:
    corr_abs = abs(float(correlation)) if correlation is not None else 0.0
    vif_v = float(vif) if vif is not None else 0.0
    if corr_abs >= 0.95 or vif_v >= 10.0:
        return "high"
    if corr_abs >= 0.85 or vif_v >= 5.0:
        return "moderate"
    return "low"


def build_diagnostic_oil_beta(
    *,
    factor_betas_5y_extended: dict[str, Any] | None = None,
    factor_betas_10y_extended: dict[str, Any] | None = None,
    factor_regression_5y_extended: dict[str, Any] | None = None,
    factor_regression_10y_extended: dict[str, Any] | None = None,
    factor_covariance: dict[str, Any] | None = None,
    kalman_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Oil is diagnostic/stress-only; expose its warning signals outside production betas."""
    b5 = factor_betas_5y_extended or {}
    b10 = factor_betas_10y_extended or {}
    fr5 = factor_regression_5y_extended or {}
    fr10 = factor_regression_10y_extended or {}
    mc5 = fr5.get("factor_multicollinearity") if isinstance(fr5, dict) else {}
    mc10 = fr10.get("factor_multicollinearity") if isinstance(fr10, dict) else {}
    corr5 = _pair_corr_from_multicollinearity(mc5, "oil", "commodity")
    corr10 = _pair_corr_from_multicollinearity(mc10, "oil", "commodity")
    vifs5 = (mc5 or {}).get("vif_by_factor") if isinstance(mc5, dict) else {}
    vifs10 = (mc10 or {}).get("vif_by_factor") if isinstance(mc10, dict) else {}
    oil_vif_5y = _safe_float((vifs5 or {}).get("oil")) if isinstance(vifs5, dict) else None
    commodity_vif_5y = _safe_float((vifs5 or {}).get("commodity")) if isinstance(vifs5, dict) else None
    oil_vif_10y = _safe_float((vifs10 or {}).get("oil")) if isinstance(vifs10, dict) else None
    commodity_vif_10y = _safe_float((vifs10 or {}).get("commodity")) if isinstance(vifs10, dict) else None
    cov_corr_base = None
    if isinstance(factor_covariance, dict):
        cov_corr_base = (
            ((factor_covariance.get("base") or {}).get("correlations") or {}).get("oil") or {}
        ).get("commodity")
        cov_corr_base = _safe_float(cov_corr_base)
    kalman_oil: dict[str, Any] = {}
    if isinstance(kalman_report, dict):
        kalman_oil = {
            "latest": (kalman_report.get("latest") or {}).get("beta_oil"),
            "latest_raw": (kalman_report.get("latest_raw") or {}).get("beta_oil"),
            "state_uncertainty": (kalman_report.get("state_uncertainty") or {}).get("beta_oil"),
            "uncertainty_class": (kalman_report.get("uncertainty_by_beta") or {}).get("beta_oil"),
            "latest_date": kalman_report.get("latest_date"),
        }
    primary_corr = corr5 if corr5 is not None else cov_corr_base
    primary_vif = oil_vif_5y if oil_vif_5y is not None else oil_vif_10y
    return {
        "role": "diagnostic_warning_only",
        "production_status": "deprecated_removed_from_production_beta_outputs",
        "factor": "oil",
        "beta_key": "beta_oil",
        "commodity_factor": "commodity",
        "commodity_beta_key": "beta_cmd",
        "beta_oil_5y": _safe_float(b5.get("beta_oil")),
        "beta_oil_10y": _safe_float(b10.get("beta_oil")),
        "beta_commodity_5y": _safe_float(b5.get("beta_cmd")),
        "beta_commodity_10y": _safe_float(b10.get("beta_cmd")),
        "oil_commodity_correlation": {
            "factor_regression_5y": corr5,
            "factor_regression_10y": corr10,
            "factor_covariance_base": cov_corr_base,
        },
        "oil_commodity_vif": {
            "oil_5y": oil_vif_5y,
            "commodity_5y": commodity_vif_5y,
            "oil_10y": oil_vif_10y,
            "commodity_10y": commodity_vif_10y,
        },
        "collinearity_signal": {
            "severity": _oil_collinearity_severity(primary_corr, primary_vif),
            "basis": "Oil/Commodity correlation and Oil VIF from extended diagnostic rows.",
        },
        "kalman_oil": kalman_oil,
    }


def _enrich_historical_results_with_factor_attribution(
    historical_results: list[dict[str, Any]],
    factor_beta_shock_oos: dict[str, Any] | None,
    *,
    beta_source: str = "5y",
    field_suffix: str = "",
) -> list[dict[str, Any]]:
    """Attach per-episode model-based factor attribution to historical stress rows."""
    if not historical_results:
        return []

    source = str(beta_source).lower().strip()
    source_map = {
        "5y": ("factor_contrib_5y", "pnl_model_5y"),
        "10y": ("factor_contrib_10y", "pnl_model_10y"),
        "adjusted": ("factor_contrib_adjusted", "pnl_model_adjusted"),
        "roll3y_pre": ("factor_contrib_roll3y_pre", "pnl_model_roll3y_pre"),
        "rolling_3y_pre": ("factor_contrib_roll3y_pre", "pnl_model_roll3y_pre"),
    }
    contrib_key, model_key = source_map.get(source, source_map["5y"])
    source = source if source in source_map else "5y"

    episodes = (factor_beta_shock_oos or {}).get("episodes") if isinstance(factor_beta_shock_oos, dict) else None
    by_episode = {
        str(row.get("episode")): row
        for row in (episodes or [])
        if isinstance(row, dict) and row.get("episode") is not None
    }

    enriched: list[dict[str, Any]] = []
    attr_key = "historical_factor_attribution" + field_suffix
    pnl_by_factor_key = "pnl_by_factor_pct" + field_suffix
    top_drivers_key = "top_factor_drivers" + field_suffix
    largest_negative_key = "largest_negative_factor" + field_suffix
    model_pnl_key = "factor_model_pnl_pct" + field_suffix
    model_error_key = "factor_model_error_pct" + field_suffix
    model_abs_error_key = "factor_model_abs_error_pct" + field_suffix
    method_key = "factor_attribution_method" + field_suffix
    beta_source_key = "factor_attribution_beta_source" + field_suffix
    for hist_row in historical_results:
        row = dict(hist_row)
        episode_id = str(row.get("episode"))
        ep = by_episode.get(episode_id)
        base_attr: dict[str, Any] = {
            "method": HISTORICAL_FACTOR_ATTRIBUTION_METHOD,
            "caveat": HISTORICAL_FACTOR_ATTRIBUTION_CAVEAT,
            "beta_source": source,
        }
        if not isinstance(ep, dict) or ep.get("error"):
            row[attr_key] = {
                **base_attr,
                "error": ep.get("error") if isinstance(ep, dict) else "episode_attribution_unavailable",
            }
            enriched.append(row)
            continue

        contrib = ep.get(contrib_key) if isinstance(ep.get(contrib_key), dict) else {}
        pnl_by_factor = {
            str(k): float(v)
            for k, v in (contrib or {}).items()
            if _safe_float(v) is not None
        }
        drivers = _factor_driver_rows(pnl_by_factor)
        negative = [
            {
                "beta_key": str(k),
                "factor": get_factor_display_name(str(k)),
                "pnl_pct": float(v),
                "abs_pnl_pct": abs(float(v)),
                "direction": "loss",
            }
            for k, v in pnl_by_factor.items()
            if float(v) < 0
        ]
        negative.sort(key=lambda item: item["pnl_pct"])
        largest_negative = negative[0] if negative else None

        model_pnl = _safe_float(ep.get(model_key))
        realized = _safe_float(row.get("pnl_real_episode"))
        model_error = (model_pnl - realized) if model_pnl is not None and realized is not None else None
        abs_error = abs(model_error) if model_error is not None else None

        attribution = {
            **base_attr,
            "factor_model_pnl_pct": model_pnl,
            "factor_model_error_pct": model_error,
            "factor_model_abs_error_pct": abs_error,
            "factor_shock_sum": {
                str(k): float(v)
                for k, v in (ep.get("factor_shock_sum") or {}).items()
                if _safe_float(v) is not None
            },
            "pnl_by_factor_pct": pnl_by_factor,
            "top_factor_drivers": drivers,
            "largest_negative_factor": largest_negative,
        }
        row[attr_key] = attribution
        row[pnl_by_factor_key] = pnl_by_factor
        row[top_drivers_key] = drivers
        row[largest_negative_key] = largest_negative
        row[model_pnl_key] = model_pnl
        row[model_error_key] = model_error
        row[model_abs_error_key] = abs_error
        row[method_key] = HISTORICAL_FACTOR_ATTRIBUTION_METHOD
        row[beta_source_key] = source
        enriched.append(row)
    return enriched


def enrich_historical_results_with_factor_attribution(
    historical_results: list[dict[str, Any]],
    factor_beta_shock_oos: dict[str, Any] | None,
    *,
    beta_source: str = "5y",
) -> list[dict[str, Any]]:
    return _enrich_historical_results_with_factor_attribution(
        historical_results,
        factor_beta_shock_oos,
        beta_source=beta_source,
    )


def enrich_historical_results_with_adjusted_factor_attribution(
    historical_results: list[dict[str, Any]],
    factor_beta_shock_oos_adjusted: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    return _enrich_historical_results_with_factor_attribution(
        historical_results,
        factor_beta_shock_oos_adjusted,
        beta_source="adjusted",
        field_suffix="_adjusted",
    )


def compute_asset_factor_betas_weekly(
    tickers: list[str],
    analysis_end_str: str,
    window_weeks: int,
    *,
    buffer_weeks: int = FACTOR_DOWNLOAD_BUFFER_WEEKS,
    min_aligned_weeks: int | None = None,
    factor_columns: tuple[str, ...] | list[str] | None = None,
) -> pd.DataFrame:
    """
    Per-asset factor betas via OLS on weekly data (same estimators as estimate_betas).

    - Downloads daily Adj Close (via fetch_daily / download_all), converts to week-end returns.
    - Builds weekly factor matrix (build_factor_matrix).
    - Takes the last ``window_weeks`` aligned week-end dates ending at/around analysis_end.

    Returns empty DataFrame if insufficient aligned history.
    """
    from src.data_yf import download_all

    tickers = [str(t).strip() for t in tickers if t and str(t).strip()]
    if not tickers:
        return pd.DataFrame()

    wk = int(window_weeks)
    if min_aligned_weeks is None:
        min_aligned_weeks = max(52, min(104, wk // 4))

    end_ts = pd.Timestamp(analysis_end_str)
    end_dl = (end_ts + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    start_ts = end_ts - pd.DateOffset(weeks=wk + int(buffer_weeks))
    start_dl = start_ts.strftime("%Y-%m-%d")

    daily = download_all(tickers, start_dl, end_dl)
    daily_prices: dict[str, pd.Series] = {}
    for t in tickers:
        df = daily.get(t)
        if df is None or df.empty or "Close" not in df.columns:
            continue
        daily_prices[t] = df["Close"].copy()

    asset_weekly = asset_weekly_returns_from_daily(daily_prices, start_dl, end_dl)
    factors = build_factor_matrix(start_dl, end_dl)
    if asset_weekly.empty or factors.empty:
        return pd.DataFrame()

    common = asset_weekly.index.intersection(factors.index).sort_values()
    # Allow week-end label shortly after month-end analysis_end
    common = common[common <= end_ts + pd.Timedelta(days=6)]
    if len(common) > wk:
        common = common[-wk:]

    if len(common) < int(min_aligned_weeks):
        return pd.DataFrame()

    Y = asset_weekly.reindex(common)
    X = factors.reindex(common)
    return estimate_betas(Y, X, factor_columns=factor_columns)


def build_factor_matrix_monthly(
    start: str,
    end: str,
) -> pd.DataFrame:
    """
    Build monthly factor series (month-end). For use when only monthly returns available.
    Columns follow FACTOR_DEFINITIONS. Decimal.
    """
    return _build_factor_frame(start, end, monthly=True)


def estimate_betas_monthly(
    monthly_asset_returns: pd.DataFrame,
    factor_monthly: pd.DataFrame,
    min_observations: int = 24,
    *,
    factor_columns: tuple[str, ...] | list[str] | None = None,
) -> pd.DataFrame:
    """
    Regress each asset monthly return on monthly factor changes. Same column naming as estimate_betas.
    """
    factor_cols = _select_factor_columns(factor_monthly, factor_columns)
    if not factor_cols:
        return pd.DataFrame()

    common = monthly_asset_returns.index.intersection(factor_monthly.index)
    if len(common) < min_observations:
        return pd.DataFrame()

    Y = monthly_asset_returns.reindex(common).dropna(how="all")
    X = factor_monthly.loc[common, factor_cols].dropna()
    common = Y.index.intersection(X.index)
    if len(common) < min_observations:
        return pd.DataFrame()

    Y = Y.loc[common]
    X = X.loc[common]
    X_const = np.column_stack([np.ones(len(X)), X.values])
    betas = {}
    for ticker in Y.columns:
        y = Y[ticker].values
        valid = ~(np.isnan(y) | np.isnan(X.values).any(axis=1))
        if valid.sum() < min_observations:
            continue
        try:
            xv, yv = X_const[valid], y[valid]
            b = np.linalg.lstsq(xv, yv, rcond=None)[0]
            betas[ticker] = dict(zip(factor_cols, b[1:]))
        except Exception:
            continue
    if not betas:
        return pd.DataFrame()
    df = pd.DataFrame(betas).T
    df = df.rename(columns={c: FACTOR_TO_BETA_KEY.get(c, f"beta_{c}") for c in factor_cols})
    return df


def portfolio_factor_betas(
    weights: dict[str, float],
    asset_betas: pd.DataFrame,
) -> dict[str, float]:
    """Portfolio factor betas = weighted sum of asset betas. Keys: beta_eq, beta_rr, ..."""
    if asset_betas.empty:
        return {}
    out = {}
    for col in asset_betas.columns:
        w = np.array([weights.get(t, 0.0) for t in asset_betas.index])
        b = asset_betas[col].fillna(0).values
        out[col] = float(np.dot(w, b))
    return out


def asset_factor_betas_dict_from_df(asset_betas: pd.DataFrame | None) -> dict[str, Any]:
    """
    Nested dict for ``stress_report[\"asset_factor_betas\"]``, consumed by
    ``historical_stress_fallback.asset_betas_from_stress_report`` and robust optimization.
    """
    if asset_betas is None or asset_betas.empty:
        return {}
    out: dict[str, Any] = {}
    for ticker in asset_betas.index:
        row = asset_betas.loc[ticker]
        betas: dict[str, float] = {}
        for col in asset_betas.columns:
            key = str(col)
            if not key.startswith("beta_"):
                continue
            v = row[col]
            if pd.notna(v):
                betas[key] = float(v)
        if betas:
            out[str(ticker)] = {"betas": betas}
    return out


def _rolling_window_betas(
    y: np.ndarray,
    x_df: pd.DataFrame,
    *,
    window_weeks: int,
) -> pd.DataFrame:
    """Compute rolling OLS betas (with intercept, betas only returned)."""
    if len(x_df) != len(y) or len(x_df) < int(window_weeks):
        return pd.DataFrame()
    cols = list(x_df.columns)
    out_rows: list[dict[str, float]] = []
    out_idx: list[pd.Timestamp] = []
    w = int(window_weeks)
    for end_i in range(w - 1, len(x_df)):
        start_i = end_i - w + 1
        xx = x_df.iloc[start_i:end_i + 1]
        yy = y[start_i:end_i + 1]
        valid = ~(np.isnan(yy) | np.isnan(xx.values).any(axis=1))
        if int(valid.sum()) < max(10, w // 3):
            continue
        try:
            x_const = np.column_stack([np.ones(int(valid.sum())), xx.values[valid]])
            b = np.linalg.lstsq(x_const, yy[valid], rcond=None)[0]
        except Exception:
            continue
        row = {
            FACTOR_TO_BETA_KEY.get(c, f"beta_{c}"): float(v)
            for c, v in zip(cols, b[1:])
        }
        out_rows.append(row)
        out_idx.append(pd.Timestamp(x_df.index[end_i]))
    if not out_rows:
        return pd.DataFrame()
    return pd.DataFrame(out_rows, index=pd.DatetimeIndex(out_idx, name="date")).sort_index()


def compute_portfolio_rolling_factor_betas_weekly(
    weights: dict[str, float],
    tickers: list[str],
    analysis_end_str: str,
    rolling_windows_weeks: dict[str, int],
    *,
    years_back: int = 20,
    factor_columns: tuple[str, ...] | list[str] | None = None,
) -> dict[str, pd.DataFrame]:
    """
    Compute rolling portfolio factor betas on weekly data for multiple window sizes.

    Returns dict[label -> DataFrame(index=date, columns beta_*)].
    """
    from src.data_yf import download_all

    use = [t for t in tickers if float(weights.get(t, 0.0)) > 0]
    if not use:
        use = list(tickers)
    use = [str(t).strip() for t in use if t and str(t).strip()]
    if not use:
        return {}

    end_ts = pd.Timestamp(analysis_end_str)
    end_dl = (end_ts + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    start_dl = (end_ts - pd.DateOffset(years=max(3, int(years_back)))).strftime("%Y-%m-%d")

    daily = download_all(use, start_dl, end_dl)
    daily_prices: dict[str, pd.Series] = {}
    for t in use:
        df = daily.get(t)
        if df is None or df.empty or "Close" not in df.columns:
            continue
        daily_prices[t] = df["Close"].copy()

    asset_weekly = asset_weekly_returns_from_daily(daily_prices, start_dl, end_dl)
    factors = build_factor_matrix(start_dl, end_dl)
    if asset_weekly.empty or factors.empty:
        return {}
    factor_cols = _select_factor_columns(factors, factor_columns)
    if not factor_cols:
        return {}

    common = asset_weekly.index.intersection(factors.index).sort_values()
    common = common[common <= end_ts + pd.Timedelta(days=6)]
    if len(common) < 30:
        return {}
    y_df = asset_weekly.reindex(common)
    x_df = factors.reindex(common).loc[:, factor_cols].dropna()
    y_df = y_df.reindex(x_df.index)

    w_vec = np.array([float(weights.get(t, 0.0)) for t in y_df.columns], dtype=float)
    # NaN returns for unavailable assets are treated as zero contribution.
    y_port = (np.nan_to_num(y_df.values, nan=0.0) * w_vec.reshape(1, -1)).sum(axis=1)

    valid = ~(np.isnan(y_port) | np.isnan(x_df.values).any(axis=1))
    if int(valid.sum()) < 30:
        return {}
    x_use = x_df.loc[valid]
    y_use = y_port[valid]

    out: dict[str, pd.DataFrame] = {}
    for label, weeks in (rolling_windows_weeks or {}).items():
        df = _rolling_window_betas(y_use, x_use, window_weeks=int(weeks))
        out[str(label)] = df
    return out


def compute_portfolio_rolling_factor_betas_monthly(
    monthly_returns: pd.DataFrame,
    weights: dict[str, float],
    analysis_end_str: str,
    rolling_windows_months: dict[str, int],
    *,
    years_back: int = 20,
    factor_columns: tuple[str, ...] | list[str] | None = None,
) -> dict[str, pd.DataFrame]:
    """
    Compute rolling portfolio factor betas on monthly returns for multiple window sizes.

    Returns dict[label -> DataFrame(index=date, columns beta_*)].
    """
    if monthly_returns is None or monthly_returns.empty:
        return {}
    use = [t for t in monthly_returns.columns if float(weights.get(str(t), 0.0)) > 0]
    if not use:
        use = [str(c) for c in monthly_returns.columns]
    if not use:
        return {}

    end_ts = pd.Timestamp(analysis_end_str)
    start_ts = end_ts - pd.DateOffset(years=max(3, int(years_back)))
    factors = build_factor_matrix_monthly(start_ts.strftime("%Y-%m-%d"), end_ts.strftime("%Y-%m-%d"))
    if factors.empty:
        return {}
    factor_cols = _select_factor_columns(factors, factor_columns)
    if not factor_cols:
        return {}

    returns = monthly_returns[[c for c in use if c in monthly_returns.columns]].copy()
    if returns.empty:
        return {}
    returns.index = pd.to_datetime(returns.index).tz_localize(None)
    factors.index = pd.to_datetime(factors.index).tz_localize(None)

    common = returns.index.intersection(factors.index).sort_values()
    common = common[common <= end_ts + pd.Timedelta(days=31)]
    if len(common) < 12:
        return {}
    y_df = returns.reindex(common)
    x_df = factors.reindex(common).loc[:, factor_cols].dropna()
    y_df = y_df.reindex(x_df.index)

    w_vec = np.array([float(weights.get(str(t), 0.0)) for t in y_df.columns], dtype=float)
    y_port = (np.nan_to_num(y_df.values, nan=0.0) * w_vec.reshape(1, -1)).sum(axis=1)
    valid = ~(np.isnan(y_port) | np.isnan(x_df.values).any(axis=1))
    if int(valid.sum()) < 12:
        return {}

    x_use = x_df.loc[valid]
    y_use = y_port[valid]
    out: dict[str, pd.DataFrame] = {}
    for label, months in (rolling_windows_months or {}).items():
        df = _rolling_window_betas(y_use, x_use, window_weeks=int(months))
        out[str(label)] = df
    return out


def _severity_max(values: list[str]) -> str:
    vals = [str(v) for v in values if str(v) in _SEVERITY_RANK]
    if not vals:
        return "unknown"
    return max(vals, key=lambda v: _SEVERITY_RANK[v])


def _beta_sign(value: float, *, eps: float = 1e-12) -> int:
    if not np.isfinite(value) or abs(value) <= eps:
        return 0
    return 1 if value > 0 else -1


def _sign_label(sign: int) -> str:
    if sign > 0:
        return "positive"
    if sign < 0:
        return "negative"
    return "zero"


def _safe_float(value: Any) -> float | None:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(v):
        return None
    return v


def _ols_beta_map(y: np.ndarray, x_df: pd.DataFrame, *, min_obs: int) -> dict[str, float] | None:
    cols = list(x_df.columns)
    yv = np.asarray(y, dtype=float).ravel()
    xv = x_df.values.astype(float)
    valid = ~(np.isnan(yv) | np.isnan(xv).any(axis=1))
    n_valid = int(valid.sum())
    if n_valid < max(int(min_obs), len(cols) + 2):
        return None
    try:
        x_const = np.column_stack([np.ones(n_valid), xv[valid]])
        beta = np.linalg.lstsq(x_const, yv[valid], rcond=None)[0]
    except Exception:
        return None
    return {
        FACTOR_TO_BETA_KEY.get(c, f"beta_{c}"): float(v)
        for c, v in zip(cols, beta[1:])
    }


def _rolling_forward_oos_beta_records(
    y: np.ndarray,
    x_df: pd.DataFrame,
    *,
    window_periods: int,
    holdout_periods: int,
) -> pd.DataFrame:
    """Estimate beta on a rolling window and compare it with beta over the following holdout."""
    if len(x_df) != len(y) or len(x_df) < int(window_periods) + int(holdout_periods):
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    w = int(window_periods)
    h = int(holdout_periods)
    for end_i in range(w - 1, len(x_df) - h):
        ins_x = x_df.iloc[end_i - w + 1:end_i + 1]
        ins_y = y[end_i - w + 1:end_i + 1]
        oos_x = x_df.iloc[end_i + 1:end_i + 1 + h]
        oos_y = y[end_i + 1:end_i + 1 + h]
        ins = _ols_beta_map(ins_y, ins_x, min_obs=max(10, w // 3))
        oos = _ols_beta_map(oos_y, oos_x, min_obs=max(10, h // 3))
        if not ins or not oos:
            continue
        for beta_key in sorted(set(ins).intersection(oos), key=lambda b: BASE_BETA_ROW_ORDER.index(b) if b in BASE_BETA_ROW_ORDER else len(BASE_BETA_ROW_ORDER)):
            ins_v = float(ins[beta_key])
            oos_v = float(oos[beta_key])
            denom = max(abs(ins_v), FACTOR_STABILITY_MIN_ABS_BETA)
            rows.append(
                {
                    "estimation_end": pd.Timestamp(x_df.index[end_i]),
                    "oos_end": pd.Timestamp(x_df.index[end_i + h]),
                    "beta": beta_key,
                    "insample_beta": ins_v,
                    "oos_beta": oos_v,
                    "sign_match": bool(_beta_sign(ins_v) == _beta_sign(oos_v)),
                    "relative_magnitude_degradation": float(abs(oos_v - ins_v) / denom),
                }
            )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def compute_portfolio_factor_beta_oos_weekly(
    weights: dict[str, float],
    tickers: list[str],
    analysis_end_str: str,
    rolling_windows_weeks: dict[str, int],
    *,
    holdout_weeks: int = FACTOR_OOS_HOLDOUT_WEEKS,
    years_back: int = 20,
    factor_columns: tuple[str, ...] | list[str] | None = None,
) -> dict[str, pd.DataFrame]:
    """Rolling-forward OOS beta diagnostics on weekly data."""
    from src.data_yf import download_all

    use = [t for t in tickers if float(weights.get(t, 0.0)) > 0]
    if not use:
        use = list(tickers)
    use = [str(t).strip() for t in use if t and str(t).strip()]
    if not use:
        return {}

    end_ts = pd.Timestamp(analysis_end_str)
    end_dl = (end_ts + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    start_dl = (end_ts - pd.DateOffset(years=max(3, int(years_back)))).strftime("%Y-%m-%d")
    daily = download_all(use, start_dl, end_dl)
    daily_prices: dict[str, pd.Series] = {}
    for t in use:
        df = daily.get(t)
        if df is None or df.empty or "Close" not in df.columns:
            continue
        daily_prices[t] = df["Close"].copy()

    asset_weekly = asset_weekly_returns_from_daily(daily_prices, start_dl, end_dl)
    factors = build_factor_matrix(start_dl, end_dl)
    if asset_weekly.empty or factors.empty:
        return {}
    factor_cols = _select_factor_columns(factors, factor_columns)
    if not factor_cols:
        return {}

    common = asset_weekly.index.intersection(factors.index).sort_values()
    common = common[common <= end_ts + pd.Timedelta(days=6)]
    if len(common) < 30:
        return {}
    y_df = asset_weekly.reindex(common)
    x_df = factors.reindex(common).loc[:, factor_cols].dropna()
    y_df = y_df.reindex(x_df.index)
    w_vec = np.array([float(weights.get(t, 0.0)) for t in y_df.columns], dtype=float)
    y_port = (np.nan_to_num(y_df.values, nan=0.0) * w_vec.reshape(1, -1)).sum(axis=1)
    valid = ~(np.isnan(y_port) | np.isnan(x_df.values).any(axis=1))
    if int(valid.sum()) < 30:
        return {}
    x_use = x_df.loc[valid]
    y_use = y_port[valid]
    return {
        str(label): _rolling_forward_oos_beta_records(
            y_use,
            x_use,
            window_periods=int(weeks),
            holdout_periods=int(holdout_weeks),
        )
        for label, weeks in (rolling_windows_weeks or {}).items()
    }


def compute_portfolio_factor_beta_oos_monthly(
    monthly_returns: pd.DataFrame,
    weights: dict[str, float],
    analysis_end_str: str,
    rolling_windows_months: dict[str, int],
    *,
    holdout_months: int = FACTOR_OOS_HOLDOUT_MONTHS,
    years_back: int = 20,
    factor_columns: tuple[str, ...] | list[str] | None = None,
) -> dict[str, pd.DataFrame]:
    """Rolling-forward OOS beta diagnostics on monthly data."""
    if monthly_returns is None or monthly_returns.empty:
        return {}
    use = [t for t in monthly_returns.columns if float(weights.get(str(t), 0.0)) > 0]
    if not use:
        use = [str(c) for c in monthly_returns.columns]
    if not use:
        return {}

    end_ts = pd.Timestamp(analysis_end_str)
    start_ts = end_ts - pd.DateOffset(years=max(3, int(years_back)))
    factors = build_factor_matrix_monthly(start_ts.strftime("%Y-%m-%d"), end_ts.strftime("%Y-%m-%d"))
    if factors.empty:
        return {}
    factor_cols = _select_factor_columns(factors, factor_columns)
    if not factor_cols:
        return {}
    returns = monthly_returns[[c for c in use if c in monthly_returns.columns]].copy()
    returns.index = pd.to_datetime(returns.index).tz_localize(None)
    factors.index = pd.to_datetime(factors.index).tz_localize(None)
    common = returns.index.intersection(factors.index).sort_values()
    common = common[common <= end_ts + pd.Timedelta(days=31)]
    if len(common) < 12:
        return {}
    y_df = returns.reindex(common)
    x_df = factors.reindex(common).loc[:, factor_cols].dropna()
    y_df = y_df.reindex(x_df.index)
    w_vec = np.array([float(weights.get(str(t), 0.0)) for t in y_df.columns], dtype=float)
    y_port = (np.nan_to_num(y_df.values, nan=0.0) * w_vec.reshape(1, -1)).sum(axis=1)
    valid = ~(np.isnan(y_port) | np.isnan(x_df.values).any(axis=1))
    if int(valid.sum()) < 12:
        return {}
    x_use = x_df.loc[valid]
    y_use = y_port[valid]
    return {
        str(label): _rolling_forward_oos_beta_records(
            y_use,
            x_use,
            window_periods=int(months),
            holdout_periods=int(holdout_months),
        )
        for label, months in (rolling_windows_months or {}).items()
    }


def factor_beta_oos_stability_diagnostics(
    oos_records_by_frequency: dict[str, dict[str, pd.DataFrame]],
) -> dict[str, Any]:
    """Summarize rolling-forward OOS beta records by factor beta."""
    by_beta_rows: dict[str, list[dict[str, Any]]] = {}
    for frequency, by_window in (oos_records_by_frequency or {}).items():
        for window, df in (by_window or {}).items():
            if df is None or df.empty or "beta" not in df.columns:
                continue
            for beta_key, part in df.groupby("beta"):
                sign_share = float(part["sign_match"].astype(float).mean())
                degradation = float(pd.to_numeric(part["relative_magnitude_degradation"], errors="coerce").median())
                if sign_share < FACTOR_STABILITY_THRESHOLDS["oos"]["sign_match_share_high_lt"] or degradation >= FACTOR_STABILITY_THRESHOLDS["oos"]["relative_magnitude_degradation_high_gte"]:
                    severity = "high"
                elif sign_share < FACTOR_STABILITY_THRESHOLDS["oos"]["sign_match_share_moderate_lt"] or degradation >= FACTOR_STABILITY_THRESHOLDS["oos"]["relative_magnitude_degradation_moderate_gte"]:
                    severity = "moderate"
                else:
                    severity = "low"
                by_beta_rows.setdefault(str(beta_key), []).append(
                    {
                        "frequency": str(frequency),
                        "window": str(window),
                        "n_tests": int(len(part)),
                        "sign_match_share": sign_share,
                        "relative_magnitude_degradation": degradation,
                        "severity": severity,
                    }
                )

    out_by_beta: dict[str, Any] = {}
    for beta_key, rows in by_beta_rows.items():
        severities = [str(r.get("severity", "unknown")) for r in rows]
        n_total = int(sum(int(r.get("n_tests", 0)) for r in rows))
        sign_values = [float(r["sign_match_share"]) for r in rows if _safe_float(r.get("sign_match_share")) is not None]
        deg_values = [float(r["relative_magnitude_degradation"]) for r in rows if _safe_float(r.get("relative_magnitude_degradation")) is not None]
        out_by_beta[beta_key] = {
            "severity": _severity_max(severities),
            "n_tests": n_total,
            "sign_match_share": float(np.mean(sign_values)) if sign_values else None,
            "relative_magnitude_degradation": float(np.median(deg_values)) if deg_values else None,
            "by_specification": rows,
        }
    return {
        "method": "rolling_forward_next_1y",
        "thresholds": FACTOR_STABILITY_THRESHOLDS["oos"],
        "by_beta": {
            beta: out_by_beta[beta]
            for beta in sorted(out_by_beta, key=lambda b: BASE_BETA_ROW_ORDER.index(b) if b in BASE_BETA_ROW_ORDER else len(BASE_BETA_ROW_ORDER))
            if beta in BASE_BETA_ROW_ORDER
        },
    }


def _severity_distribution(severities: list[str]) -> dict[str, Any]:
    counts = {k: 0 for k in ("low", "moderate", "high", "unknown")}
    for sev in severities:
        counts[str(sev) if str(sev) in counts else "unknown"] += 1
    total = int(sum(counts.values()))
    shares = {k: (float(v) / total if total else 0.0) for k, v in counts.items()}
    return {"counts": counts, "shares": shares, "n": total}


def _severity_distribution_warning(distribution: dict[str, Any]) -> str | None:
    shares = distribution.get("shares") if isinstance(distribution, dict) else {}
    high_share = float(shares.get("high", 0.0)) if isinstance(shares, dict) else 0.0
    low_share = float(shares.get("low", 0.0)) if isinstance(shares, dict) else 0.0
    dist_cfg = FACTOR_STABILITY_THRESHOLDS["severity_distribution"]
    if high_share > float(dist_cfg["high_share_warning_gt"]):
        return "thresholds_may_be_too_strict_consider_relaxing_magnitude_to_1_5_2_5"
    if low_share > float(dist_cfg["low_share_warning_gt"]):
        return "thresholds_may_be_too_soft"
    return None


def factor_beta_stability_diagnostics(
    rolling_betas_by_frequency: dict[str, dict[str, pd.DataFrame]],
    *,
    oos_stability: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute sign, magnitude, specification, and OOS stability diagnostics for factor betas."""
    by_beta_values: dict[str, list[float]] = {}
    by_beta_specs: dict[str, list[dict[str, Any]]] = {}
    for frequency, by_window in (rolling_betas_by_frequency or {}).items():
        for window, df in (by_window or {}).items():
            if df is None or df.empty:
                continue
            for col in df.columns:
                s = pd.to_numeric(df[col], errors="coerce").dropna()
                if s.empty:
                    continue
                vals = [float(v) for v in s.tolist() if np.isfinite(float(v))]
                if not vals:
                    continue
                by_beta_values.setdefault(str(col), []).extend(vals)
                med = float(np.median(vals))
                by_beta_specs.setdefault(str(col), []).append(
                    {
                        "frequency": str(frequency),
                        "window": str(window),
                        "n_points": int(len(vals)),
                        "median": med,
                        "p10": float(np.quantile(vals, 0.10)),
                        "p90": float(np.quantile(vals, 0.90)),
                        "sign": _sign_label(_beta_sign(med)),
                    }
                )

    oos_by_beta = ((oos_stability or {}).get("by_beta") or {}) if isinstance(oos_stability, dict) else {}
    beta_keys = sorted(
        set(by_beta_values).union(oos_by_beta).intersection(BASE_BETA_ROW_ORDER),
        key=lambda b: BASE_BETA_ROW_ORDER.index(b) if b in BASE_BETA_ROW_ORDER else len(BASE_BETA_ROW_ORDER),
    )
    out_by_beta: dict[str, Any] = {}
    combined_severities: list[str] = []
    for beta_key in beta_keys:
        values = by_beta_values.get(beta_key, [])
        if values:
            signs = [_beta_sign(v) for v in values]
            non_zero_signs = [s for s in signs if s != 0]
            pos = int(sum(1 for s in non_zero_signs if s > 0))
            neg = int(sum(1 for s in non_zero_signs if s < 0))
            dominant = 1 if pos >= neg else -1
            dominant_count = max(pos, neg)
            dominant_share = float(dominant_count / len(non_zero_signs)) if non_zero_signs else 0.0
            sign_change_count = int(sum(1 for a, b in zip(non_zero_signs, non_zero_signs[1:]) if a != b))
            p10 = float(np.quantile(values, 0.10))
            p90 = float(np.quantile(values, 0.90))
            median = float(np.median(values))
            zero_cross_high = p10 < -FACTOR_STABILITY_ZERO_EPS and p90 > FACTOR_STABILITY_ZERO_EPS
            zero_cross = p10 <= 0.0 <= p90
            if dominant_share < FACTOR_STABILITY_THRESHOLDS["sign"]["dominant_share_high_lt"] or zero_cross_high:
                sign_sev = "high"
            elif dominant_share < FACTOR_STABILITY_THRESHOLDS["sign"]["dominant_share_moderate_lt"] or zero_cross:
                sign_sev = "moderate"
            else:
                sign_sev = "low"
            band = float(p90 - p10)
            rel_band = float(band / max(abs(median), FACTOR_STABILITY_MIN_ABS_BETA))
            if rel_band >= FACTOR_STABILITY_THRESHOLDS["magnitude"]["relative_band_high_gte"]:
                mag_sev = "high"
            elif rel_band >= FACTOR_STABILITY_THRESHOLDS["magnitude"]["relative_band_moderate_gte"]:
                mag_sev = "moderate"
            else:
                mag_sev = "low"
            sign_stability = {
                "dominant_sign": _sign_label(dominant),
                "dominant_sign_share": dominant_share,
                "sign_change_count": sign_change_count,
                "p10": p10,
                "p90": p90,
                "severity": sign_sev,
            }
            magnitude_stability = {
                "median": median,
                "p90_minus_p10": band,
                "relative_band": rel_band,
                "severity": mag_sev,
            }
        else:
            sign_stability = {
                "dominant_sign": "unknown",
                "dominant_sign_share": None,
                "sign_change_count": 0,
                "p10": None,
                "p90": None,
                "severity": "unknown",
            }
            magnitude_stability = {
                "median": None,
                "p90_minus_p10": None,
                "relative_band": None,
                "severity": "unknown",
            }

        specs = by_beta_specs.get(beta_key, [])
        medians = [float(s["median"]) for s in specs if _safe_float(s.get("median")) is not None]
        spec_signs = {_beta_sign(v) for v in medians if _beta_sign(v) != 0}
        if medians:
            med_span = float(max(medians) - min(medians))
            med_anchor = float(np.median(medians))
            rel_med_span = float(med_span / max(abs(med_anchor), FACTOR_STABILITY_MIN_ABS_BETA))
            sign_disagreement = len(spec_signs) > 1
            if sign_disagreement or rel_med_span >= FACTOR_STABILITY_THRESHOLDS["specification"]["relative_median_span_high_gte"]:
                spec_sev = "high"
            elif rel_med_span >= FACTOR_STABILITY_THRESHOLDS["specification"]["relative_median_span_moderate_gte"]:
                spec_sev = "moderate"
            else:
                spec_sev = "low"
        else:
            med_span = None
            rel_med_span = None
            sign_disagreement = False
            spec_sev = "unknown"
        specification_sensitivity = {
            "median_span": med_span,
            "relative_median_span": rel_med_span,
            "sign_disagreement": bool(sign_disagreement),
            "severity": spec_sev,
            "by_specification": specs,
        }

        oos = oos_by_beta.get(beta_key, {"severity": "unknown", "n_tests": 0})
        combined = _severity_max([
            str(sign_stability.get("severity", "unknown")),
            str(magnitude_stability.get("severity", "unknown")),
            str(specification_sensitivity.get("severity", "unknown")),
            str(oos.get("severity", "unknown")) if isinstance(oos, dict) else "unknown",
        ])
        combined_severities.append(combined)
        out_by_beta[beta_key] = {
            "combined_severity": combined,
            "sign_stability": sign_stability,
            "magnitude_stability": magnitude_stability,
            "specification_sensitivity": specification_sensitivity,
            "oos_stability": oos,
        }

    distribution = _severity_distribution(combined_severities)
    return {
        "method": "rolling_beta_sign_magnitude_specification_sensitivity",
        "thresholds": FACTOR_STABILITY_THRESHOLDS,
        "by_beta": out_by_beta,
        "severity_distribution": distribution,
        "severity_distribution_warning": _severity_distribution_warning(distribution),
        "overall_severity": _severity_max(combined_severities),
    }


def factor_beta_stability_rows(stability: dict[str, Any]) -> pd.DataFrame:
    """Flatten stability diagnostics for CSV export."""
    rows: list[dict[str, Any]] = []
    by_beta = stability.get("by_beta") if isinstance(stability, dict) else {}
    if not isinstance(by_beta, dict):
        return pd.DataFrame()
    for beta_key, payload in by_beta.items():
        if not isinstance(payload, dict):
            continue
        sign = payload.get("sign_stability") or {}
        mag = payload.get("magnitude_stability") or {}
        spec = payload.get("specification_sensitivity") or {}
        oos = payload.get("oos_stability") or {}
        rows.append(
            {
                "beta": beta_key,
                "combined_severity": payload.get("combined_severity"),
                "sign_severity": sign.get("severity"),
                "dominant_sign": sign.get("dominant_sign"),
                "dominant_sign_share": sign.get("dominant_sign_share"),
                "sign_change_count": sign.get("sign_change_count"),
                "magnitude_severity": mag.get("severity"),
                "p90_minus_p10": mag.get("p90_minus_p10"),
                "relative_band": mag.get("relative_band"),
                "specification_severity": spec.get("severity"),
                "relative_median_span": spec.get("relative_median_span"),
                "specification_sign_disagreement": spec.get("sign_disagreement"),
                "oos_severity": oos.get("severity") if isinstance(oos, dict) else None,
                "oos_sign_match_share": oos.get("sign_match_share") if isinstance(oos, dict) else None,
                "oos_relative_magnitude_degradation": oos.get("relative_magnitude_degradation") if isinstance(oos, dict) else None,
                "oos_n_tests": oos.get("n_tests") if isinstance(oos, dict) else None,
            }
        )
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    beta_rank = {beta_key: idx for idx, beta_key in enumerate(BASE_BETA_ROW_ORDER)}
    df["beta_rank"] = df["beta"].map(lambda beta: beta_rank.get(str(beta), len(beta_rank)))
    return df.sort_values(["beta_rank", "beta"]).drop(columns=["beta_rank"]).reset_index(drop=True)


FACTOR_COVARIANCE_STRESS_EPISODES: tuple[tuple[str, str, str], ...] = (
    ("2008", "2007-10-01", "2009-03-31"),
    ("2020", "2020-02-01", "2020-04-30"),
    ("2022", "2021-11-01", "2022-10-31"),
)


def _ordered_factor_frame(factors: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Return factor frame in canonical order; missing columns are explicit zero series."""
    if factors is None or factors.empty:
        return pd.DataFrame(columns=list(FACTOR_COLUMN_ORDER)), list(FACTOR_COLUMN_ORDER)
    df = factors.copy()
    df.index = pd.to_datetime(df.index).tz_localize(None)
    missing = [col for col in FACTOR_COLUMN_ORDER if col not in df.columns]
    for col in missing:
        df[col] = 0.0
    df = df.loc[:, list(FACTOR_COLUMN_ORDER)].sort_index()
    df = df.apply(pd.to_numeric, errors="coerce").dropna(how="all")
    return df.fillna(0.0), missing


def _factor_covariance_matrix(factors: pd.DataFrame) -> pd.DataFrame:
    if factors is None or factors.empty or len(factors) < 2:
        return pd.DataFrame(0.0, index=FACTOR_COLUMN_ORDER, columns=FACTOR_COLUMN_ORDER)
    cov = factors.loc[:, list(FACTOR_COLUMN_ORDER)].cov(ddof=1)
    return cov.reindex(index=FACTOR_COLUMN_ORDER, columns=FACTOR_COLUMN_ORDER).fillna(0.0)


def _correlation_from_covariance(cov: pd.DataFrame) -> pd.DataFrame:
    if cov is None or cov.empty:
        return pd.DataFrame(0.0, index=FACTOR_COLUMN_ORDER, columns=FACTOR_COLUMN_ORDER)
    vals = cov.reindex(index=FACTOR_COLUMN_ORDER, columns=FACTOR_COLUMN_ORDER).fillna(0.0).values.astype(float)
    vol = np.sqrt(np.maximum(np.diag(vals), 0.0))
    corr = np.zeros_like(vals)
    for i in range(len(vol)):
        for j in range(len(vol)):
            den = vol[i] * vol[j]
            if den > 1e-20:
                corr[i, j] = vals[i, j] / den
            else:
                corr[i, j] = 1.0 if i == j else 0.0
    corr = np.clip(corr, -1.0, 1.0)
    np.fill_diagonal(corr, 1.0)
    return pd.DataFrame(corr, index=FACTOR_COLUMN_ORDER, columns=FACTOR_COLUMN_ORDER)


def _repair_covariance_psd(cov: pd.DataFrame, eps: float = 1e-12) -> tuple[pd.DataFrame, bool]:
    vals = cov.reindex(index=FACTOR_COLUMN_ORDER, columns=FACTOR_COLUMN_ORDER).fillna(0.0).values.astype(float)
    vals = (vals + vals.T) / 2.0
    try:
        eigvals, eigvecs = np.linalg.eigh(vals)
    except Exception:
        diag = np.maximum(np.diag(vals), eps)
        repaired = np.diag(diag)
        return pd.DataFrame(repaired, index=FACTOR_COLUMN_ORDER, columns=FACTOR_COLUMN_ORDER), True
    repaired_needed = bool(np.min(eigvals) < -eps)
    if not repaired_needed:
        return pd.DataFrame(vals, index=FACTOR_COLUMN_ORDER, columns=FACTOR_COLUMN_ORDER), False
    eigvals = np.maximum(eigvals, eps)
    repaired = eigvecs @ np.diag(eigvals) @ eigvecs.T
    repaired = (repaired + repaired.T) / 2.0
    return pd.DataFrame(repaired, index=FACTOR_COLUMN_ORDER, columns=FACTOR_COLUMN_ORDER), True


def _matrix_to_nested(df: pd.DataFrame) -> dict[str, dict[str, float]]:
    ordered = df.reindex(index=FACTOR_COLUMN_ORDER, columns=FACTOR_COLUMN_ORDER).fillna(0.0)
    return {
        str(i): {str(j): float(ordered.loc[i, j]) for j in FACTOR_COLUMN_ORDER}
        for i in FACTOR_COLUMN_ORDER
    }


def _regime_block(
    *,
    label: str,
    classification: str,
    cov: pd.DataFrame,
    n_obs: int,
    window: dict[str, Any] | None = None,
    episodes_used: list[str] | None = None,
    psd_repaired: bool = False,
    overlay_deltas: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    corr = _correlation_from_covariance(cov)
    out: dict[str, Any] = {
        "label": label,
        "classification": classification,
        "n_obs": int(n_obs),
        "matrix": _matrix_to_nested(cov),
        "variances": {str(k): float(cov.loc[k, k]) for k in FACTOR_COLUMN_ORDER},
        "correlations": _matrix_to_nested(corr),
        "psd_repaired": bool(psd_repaired),
    }
    if window is not None:
        out["window"] = window
    if episodes_used is not None:
        out["episodes_used"] = list(episodes_used)
    if overlay_deltas is not None:
        out["overlay_deltas"] = overlay_deltas
    return out


def _stress_empirical_rows(factors: pd.DataFrame) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    for _ep, start, end in FACTOR_COVARIANCE_STRESS_EPISODES:
        sub = factors.loc[str(start):str(end)] if hasattr(factors.index, "slice_indexer") else pd.DataFrame()
        if sub is not None and not sub.empty:
            parts.append(sub)
    if not parts:
        return pd.DataFrame(columns=list(FACTOR_COLUMN_ORDER))
    return pd.concat(parts).sort_index().loc[:, list(FACTOR_COLUMN_ORDER)]


def _build_stress_overlay_covariance(
    base_cov: pd.DataFrame,
    stress_empirical_cov: pd.DataFrame,
) -> tuple[pd.DataFrame, list[dict[str, Any]], bool]:
    base_corr = _correlation_from_covariance(base_cov)
    stress_corr = _correlation_from_covariance(stress_empirical_cov)
    stress_vals = stress_empirical_cov.reindex(index=FACTOR_COLUMN_ORDER, columns=FACTOR_COLUMN_ORDER).fillna(0.0)
    vols = np.sqrt(np.maximum(np.diag(stress_vals.values.astype(float)), 0.0))
    corr_overlay = stress_corr.values.astype(float).copy()
    stress_factor_set = {spec.column for spec in STRESS_FACTOR_DEFINITIONS}
    deltas: list[dict[str, Any]] = []

    for i, fi in enumerate(FACTOR_COLUMN_ORDER):
        for j, fj in enumerate(FACTOR_COLUMN_ORDER):
            if i >= j:
                continue
            pre_corr = float(stress_corr.loc[fi, fj])
            base_abs = abs(float(base_corr.loc[fi, fj]))
            stress_abs = abs(pre_corr)
            target_abs = max(base_abs, stress_abs)
            reasons = []
            if target_abs > stress_abs + 1e-12:
                reasons.append("base_abs_corr_exceeds_stress_empirical")
            if fi in stress_factor_set and fj in stress_factor_set and target_abs < FACTOR_COVARIANCE_OVERLAY_CORR_FLOOR:
                target_abs = FACTOR_COVARIANCE_OVERLAY_CORR_FLOOR
                reasons.append("stress_factor_corr_floor")
            if not reasons:
                continue
            sign_anchor = pre_corr
            if abs(sign_anchor) <= 1e-12:
                sign_anchor = float(base_corr.loc[fi, fj])
            sign = 1.0 if sign_anchor >= 0.0 else -1.0
            target_corr = float(np.clip(sign * target_abs, -0.999999, 0.999999))
            corr_overlay[i, j] = corr_overlay[j, i] = target_corr
            pre_cov = float(stress_vals.loc[fi, fj])
            target_cov = float(target_corr * vols[i] * vols[j])
            denom = abs(pre_cov)
            deltas.append(
                {
                    "factor_i": str(fi),
                    "factor_j": str(fj),
                    "change_type": "correlation_and_covariance",
                    "pre_overlay_corr": pre_corr,
                    "target_overlay_corr": target_corr,
                    "pre_overlay_cov": pre_cov,
                    "target_overlay_cov": target_cov,
                    "absolute_delta": abs(target_cov - pre_cov),
                    "relative_delta": (abs(target_cov - pre_cov) / denom) if denom > 1e-12 else None,
                    "clamp_reason": "+".join(reasons),
                }
            )

    np.fill_diagonal(corr_overlay, 1.0)
    cov_overlay = np.outer(vols, vols) * corr_overlay
    np.fill_diagonal(cov_overlay, vols**2)
    cov_df = pd.DataFrame(cov_overlay, index=FACTOR_COLUMN_ORDER, columns=FACTOR_COLUMN_ORDER)
    repaired_cov, repaired = _repair_covariance_psd(cov_df)
    for row in deltas:
        fi = str(row["factor_i"])
        fj = str(row["factor_j"])
        post_cov = float(repaired_cov.loc[fi, fj])
        post_corr = float(_correlation_from_covariance(repaired_cov).loc[fi, fj])
        pre_cov = float(row["pre_overlay_cov"])
        row["post_overlay_corr"] = post_corr
        row["post_overlay_cov"] = post_cov
        row["absolute_delta"] = abs(post_cov - pre_cov)
        row["relative_delta"] = (abs(post_cov - pre_cov) / abs(pre_cov)) if abs(pre_cov) > 1e-12 else None
        row["psd_repair_applied"] = bool(repaired)
    return repaired_cov, deltas, repaired


def _exposure_vector(portfolio_betas: dict[str, Any] | None) -> tuple[np.ndarray, dict[str, Any]]:
    beta_map = portfolio_betas or {}
    betas_used: dict[str, float] = {}
    missing: list[str] = []
    values: list[float] = []
    for factor in FACTOR_COLUMN_ORDER:
        beta_key = FACTOR_TO_BETA_KEY.get(factor, f"beta_{factor}")
        value = _safe_float(beta_map.get(beta_key)) if isinstance(beta_map, dict) else None
        if value is None:
            value = 0.0
            missing.append(beta_key)
        betas_used[beta_key] = float(value)
        values.append(float(value))
    return np.asarray(values, dtype=float), {
        "factor_order": list(FACTOR_COLUMN_ORDER),
        "beta_order": [FACTOR_TO_BETA_KEY.get(f, f"beta_{f}") for f in FACTOR_COLUMN_ORDER],
        "betas_used": betas_used,
        "zero_filled_beta_keys": missing,
    }


def _portfolio_factor_risk(
    cov: pd.DataFrame,
    beta_vec: np.ndarray,
    *,
    label: str,
    classification: str,
) -> dict[str, Any]:
    vals = cov.reindex(index=FACTOR_COLUMN_ORDER, columns=FACTOR_COLUMN_ORDER).fillna(0.0).values.astype(float)
    variance = float(beta_vec.T @ vals @ beta_vec)
    variance = max(variance, 0.0)
    return {
        "label": label,
        "classification": classification,
        "portfolio_factor_variance": variance,
        "portfolio_factor_vol": float(np.sqrt(variance)),
    }


def _factor_rc(cov: pd.DataFrame, beta_vec: np.ndarray) -> pd.DataFrame:
    vals = cov.reindex(index=FACTOR_COLUMN_ORDER, columns=FACTOR_COLUMN_ORDER).fillna(0.0).values.astype(float)
    variance = float(beta_vec.T @ vals @ beta_vec)
    rows: list[dict[str, Any]] = []
    marginal = vals @ beta_vec
    for idx, factor in enumerate(FACTOR_COLUMN_ORDER):
        contribution = float(beta_vec[idx] * marginal[idx])
        rc = float(contribution / variance) if variance > 1e-20 else 0.0
        rows.append(
            {
                "factor": str(factor),
                "beta_key": FACTOR_TO_BETA_KEY.get(str(factor), f"beta_{factor}"),
                "component_variance": contribution,
                "rc_share": rc,
            }
        )
    return pd.DataFrame(rows)


def _macro_order() -> tuple[str, ...]:
    return BASE_FACTOR_COLUMN_ORDER


def _macro_beta_keys() -> list[str]:
    return [FACTOR_TO_BETA_KEY.get(f, f"beta_{f}") for f in _macro_order()]


def _rolling_zscore(series: pd.Series, *, window: int, min_periods: int) -> pd.Series:
    s = pd.Series(series, dtype=float)
    mean = s.rolling(window=window, min_periods=min_periods).mean()
    std = s.rolling(window=window, min_periods=min_periods).std(ddof=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        z = (s - mean) / std
    return z.replace([np.inf, -np.inf], np.nan)


def _macro_quality_status(n_obs: int) -> str:
    """Map a monthly observation count to a quality label for ``macro_two_axis_v1``.

    n == 0 -> "no_observations". n < 12 -> "insufficient_data" (estimates
    suppressed downstream). 12 <= n < 24 -> "low_confidence". 24 <= n < 60 ->
    "usable". n >= 60 -> "reliable".
    """

    n = int(n_obs or 0)
    if n <= 0:
        return "no_observations"
    if n < MACRO_REGIME_INSUFFICIENT_MAX_ROWS:
        return "insufficient_data"
    if n < MACRO_REGIME_USABLE_MIN_ROWS:
        return "low_confidence"
    if n < MACRO_REGIME_RELIABLE_MIN_ROWS:
        return "usable"
    return "reliable"


def _macro_covariance_matrix(factors: pd.DataFrame) -> pd.DataFrame:
    order = list(_macro_order())
    if factors is None or factors.empty or len(factors) < 2:
        return pd.DataFrame(0.0, index=order, columns=order)
    return factors.reindex(columns=order).fillna(0.0).cov(ddof=1).reindex(index=order, columns=order).fillna(0.0)


def _macro_correlation_from_covariance(cov: pd.DataFrame) -> pd.DataFrame:
    order = list(_macro_order())
    vals = cov.reindex(index=order, columns=order).fillna(0.0).values.astype(float)
    vol = np.sqrt(np.maximum(np.diag(vals), 0.0))
    corr = np.zeros_like(vals)
    for i in range(len(vol)):
        for j in range(len(vol)):
            den = vol[i] * vol[j]
            if den > 1e-20:
                corr[i, j] = vals[i, j] / den
            else:
                corr[i, j] = 1.0 if i == j else 0.0
    corr = np.clip(corr, -1.0, 1.0)
    np.fill_diagonal(corr, 1.0)
    return pd.DataFrame(corr, index=order, columns=order)


def _macro_matrix_to_nested(df: pd.DataFrame) -> dict[str, dict[str, float]]:
    order = list(_macro_order())
    ordered = df.reindex(index=order, columns=order).fillna(0.0)
    return {str(i): {str(j): float(ordered.loc[i, j]) for j in order} for i in order}


def _macro_covariance_block(cov: pd.DataFrame, *, label: str, n_obs: int, source: str) -> dict[str, Any]:
    corr = _macro_correlation_from_covariance(cov)
    order = list(_macro_order())
    return {
        "label": label,
        "source": source,
        "n_obs": int(n_obs),
        "matrix": _macro_matrix_to_nested(cov),
        "variances": {str(k): float(cov.reindex(index=order, columns=order).fillna(0.0).loc[k, k]) for k in order},
        "correlations": _macro_matrix_to_nested(corr),
    }


def _macro_factor_risk(cov: pd.DataFrame, beta_map: dict[str, float], *, label: str) -> dict[str, Any]:
    order = list(_macro_order())
    beta_vec = np.array([float(beta_map.get(FACTOR_TO_BETA_KEY.get(f, f"beta_{f}"), 0.0)) for f in order], dtype=float)
    vals = cov.reindex(index=order, columns=order).fillna(0.0).values.astype(float)
    variance = float(beta_vec.T @ vals @ beta_vec)
    variance = max(variance, 0.0)
    return {
        "label": label,
        "portfolio_factor_variance": variance,
        "portfolio_factor_vol": float(np.sqrt(variance)),
    }


def _macro_factor_rc(cov: pd.DataFrame, beta_map: dict[str, float]) -> list[dict[str, Any]]:
    order = list(_macro_order())
    beta_vec = np.array([float(beta_map.get(FACTOR_TO_BETA_KEY.get(f, f"beta_{f}"), 0.0)) for f in order], dtype=float)
    vals = cov.reindex(index=order, columns=order).fillna(0.0).values.astype(float)
    variance = float(beta_vec.T @ vals @ beta_vec)
    marginal = vals @ beta_vec
    rows: list[dict[str, Any]] = []
    for idx, factor in enumerate(order):
        contribution = float(beta_vec[idx] * marginal[idx])
        rc = float(contribution / variance) if variance > 1e-20 else 0.0
        if contribution > 1e-20:
            sign = "positive"
            interpretation = "risk_adder"
        elif contribution < -1e-20:
            sign = "negative"
            interpretation = "hedging_or_diversifying_contribution"
        else:
            sign = "zero"
            interpretation = "neutral"
        rows.append(
            {
                "factor": str(factor),
                "beta_key": FACTOR_TO_BETA_KEY.get(str(factor), f"beta_{factor}"),
                "component_variance": contribution,
                "rc_share": rc,
                "rc_sign": sign,
                "interpretation": interpretation,
            }
        )
    return rows


def _macro_regression_from_arrays(
    y: np.ndarray,
    X: np.ndarray,
    factor_cols: list[str],
    *,
    label: str,
    n_obs: int,
    alpha: float = 0.05,
) -> dict[str, Any]:
    inf = _ols_with_inference(np.asarray(y, dtype=float), np.asarray(X, dtype=float), add_const=True, alpha=alpha)
    if not inf:
        return {"status": "unavailable", "label": label, "n_obs": int(n_obs)}
    beta_keys = [FACTOR_TO_BETA_KEY.get(c, f"beta_{c}") for c in factor_cols]
    params = inf["params"]
    Z = np.column_stack([np.ones(len(X)), X])
    cov_hac = _newey_west_covariance(Z, np.asarray(y, dtype=float) - Z @ params, max_lags=FACTOR_REGRESSION_HAC_LAGS)
    se_hac = np.sqrt(np.maximum(np.diag(cov_hac), 0.0))
    df_resid = int(inf.get("df_resid", max(len(y) - Z.shape[1], 1)))
    with np.errstate(divide="ignore", invalid="ignore"):
        t_hac = params / se_hac
    p_hac = 2.0 * stats.t.sf(np.abs(t_hac), df=df_resid)
    tcrit_hac = float(stats.t.ppf(1.0 - alpha / 2.0, df=df_resid))
    ci_low_hac = params - tcrit_hac * se_hac
    ci_high_hac = params + tcrit_hac * se_hac
    return {
        "status": "available",
        "label": label,
        "n_obs": int(inf["n_obs"]),
        "variance_scale": "weekly",
        "factor_order": list(factor_cols),
        "r2": float(inf["r2"]),
        "adj_r2": float(inf["adj_r2"]),
        "idiosyncratic_risk": float(inf["idiosyncratic_risk"]),
        "intercept": float(params[0]),
        "betas": {k: float(v) for k, v in zip(beta_keys, params[1:])},
        "t": {k: float(v) for k, v in zip(beta_keys, inf["t"][1:])},
        "p": {k: float(v) for k, v in zip(beta_keys, inf["p"][1:])},
        "ci_low": {k: float(v) for k, v in zip(beta_keys, inf["ci_low"][1:])},
        "ci_high": {k: float(v) for k, v in zip(beta_keys, inf["ci_high"][1:])},
        "hac_inference": {
            "se_type": "hac_newey_west",
            "kernel": "bartlett",
            "max_lags": int(FACTOR_REGRESSION_HAC_LAGS),
            "se": {k: float(v) for k, v in zip(["intercept", *beta_keys], se_hac)},
            "t": {k: float(v) for k, v in zip(["intercept", *beta_keys], t_hac)},
            "p": {k: float(v) for k, v in zip(["intercept", *beta_keys], p_hac)},
            "ci_low": {k: float(v) for k, v in zip(["intercept", *beta_keys], ci_low_hac)},
            "ci_high": {k: float(v) for k, v in zip(["intercept", *beta_keys], ci_high_hac)},
        },
    }


def _macro_empty_regression(label: str, n_obs: int, betas: dict[str, float]) -> dict[str, Any]:
    return {
        "status": "fallback_reference",
        "label": label,
        "n_obs": int(n_obs),
        "factor_order": list(_macro_order()),
        "betas": {k: float(betas.get(k, 0.0)) for k in _macro_beta_keys()},
    }


def _macro_policy_signal(regime_betas: dict[str, dict[str, float]], quality_by_regime: dict[str, str]) -> dict[str, Any]:
    usable_regimes = {
        regime: betas
        for regime, betas in regime_betas.items()
        if quality_by_regime.get(regime) in {"low_confidence", "usable", "reliable"}
    }
    by_beta: dict[str, Any] = {}
    counts = {
        "green/general_signal": 0,
        "yellow/regime_only": 0,
        "red/do_not_use_as_single_signal": 0,
    }
    for beta_key in _macro_beta_keys():
        vals = {
            regime: float(betas.get(beta_key, 0.0))
            for regime, betas in usable_regimes.items()
            if beta_key in betas
        }
        nonzero_signs = {1 if v > 0 else -1 for v in vals.values() if abs(v) > FACTOR_STABILITY_ZERO_EPS}
        sign_flip = len(nonzero_signs) > 1
        max_gap = 0.0
        if vals:
            arr = list(vals.values())
            max_gap = float(max(arr) - min(arr))
        if sign_flip:
            signal = "red/do_not_use_as_single_signal"
        elif len(vals) < len(MACRO_REGIME_NAMES) or max_gap >= MACRO_REGIME_STABILITY_BETA_GAP:
            signal = "yellow/regime_only"
        else:
            signal = "green/general_signal"
        counts[signal] += 1
        by_beta[beta_key] = {
            "policy_signal": signal,
            "sign_flip": bool(sign_flip),
            "max_abs_regime_beta_gap": abs(max_gap),
            "available_regimes": sorted(vals.keys()),
            "regime_betas": vals,
        }
    top_unstable = sorted(
        [{"beta_key": k, **v} for k, v in by_beta.items()],
        key=lambda row: (row["policy_signal"].startswith("red"), row["max_abs_regime_beta_gap"]),
        reverse=True,
    )[:5]
    return {
        "threshold_abs_beta_gap": float(MACRO_REGIME_STABILITY_BETA_GAP),
        "warning": MACRO_REGIME_STABILITY_WARNING,
        "by_beta": by_beta,
        "policy_signal_counts": counts,
        "top_unstable_betas": top_unstable,
    }


def macro_regime_diagnostics_from_frames(
    portfolio_returns_monthly: pd.Series,
    factor_returns_monthly: pd.DataFrame,
    indicator_panel: pd.DataFrame,
    indicator_meta: dict[str, Any],
    analysis_end_str: str,
    *,
    neutral_band: float = 0.20,
    scoring_method: str | None = None,
    clipped_z_max_abs: float | None = None,
    persistence_months: int | None = None,
) -> dict[str, Any]:
    """Thin shim over `src.stress_factors_macro.macro_two_axis_diagnostics_from_frames`.

    Kept on this module so historical import sites and external consumers continue
    to resolve `from src.stress_factors import macro_regime_diagnostics_from_frames`.
    """

    from src.stress_factors_macro import (
        MACRO_CLIPPED_Z_MAX_ABS_DEFAULT,
        MACRO_PERSISTENCE_MONTHS_DEFAULT,
        MACRO_SCORING_METHOD_DEFAULT,
        macro_two_axis_diagnostics_from_frames,
    )

    return macro_two_axis_diagnostics_from_frames(
        portfolio_returns_monthly,
        factor_returns_monthly,
        indicator_panel,
        indicator_meta or {},
        analysis_end_str,
        neutral_band=neutral_band,
        scoring_method=scoring_method or MACRO_SCORING_METHOD_DEFAULT,
        clipped_z_max_abs=(
            clipped_z_max_abs
            if clipped_z_max_abs is not None
            else MACRO_CLIPPED_Z_MAX_ABS_DEFAULT
        ),
        persistence_months=(
            int(persistence_months)
            if persistence_months is not None
            else MACRO_PERSISTENCE_MONTHS_DEFAULT
        ),
    )


def macro_regime_diagnostics(
    *,
    weights: dict[str, float],
    tickers: list[str],
    analysis_end_str: str,
    factor_returns: pd.DataFrame | None = None,
    factor_returns_monthly: pd.DataFrame | None = None,
    neutral_band: float = 0.20,
    months_back: int = 420,
    scoring_method: str | None = None,
    clipped_z_max_abs: float | None = None,
    persistence_months: int | None = None,
) -> dict[str, Any]:
    """Thin shim over `src.stress_factors_macro.macro_two_axis_diagnostics`.

    The legacy keyword ``factor_returns`` is preserved for back-compat with
    ``run_optimization.py`` / ``run_report.py`` call sites that pass weekly factor
    returns; in v1 those are ignored (the new monthly path builds its own factor
    matrix). New callers should use ``factor_returns_monthly`` explicitly.
    """

    from src.stress_factors_macro import (
        MACRO_CLIPPED_Z_MAX_ABS_DEFAULT,
        MACRO_PERSISTENCE_MONTHS_DEFAULT,
        MACRO_SCORING_METHOD_DEFAULT,
        macro_two_axis_diagnostics,
    )

    return macro_two_axis_diagnostics(
        weights=weights,
        tickers=tickers,
        analysis_end_str=analysis_end_str,
        factor_returns_monthly=factor_returns_monthly,
        neutral_band=neutral_band,
        months_back=months_back,
        scoring_method=scoring_method or MACRO_SCORING_METHOD_DEFAULT,
        clipped_z_max_abs=(
            clipped_z_max_abs
            if clipped_z_max_abs is not None
            else MACRO_CLIPPED_Z_MAX_ABS_DEFAULT
        ),
        persistence_months=(
            int(persistence_months)
            if persistence_months is not None
            else MACRO_PERSISTENCE_MONTHS_DEFAULT
        ),
    )


def macro_regime_csv_frames(report: dict[str, Any]) -> dict[str, pd.DataFrame]:
    """Thin shim over `src.stress_factors_macro.macro_regime_csv_frames`."""

    from src.stress_factors_macro import macro_regime_csv_frames as _impl

    return _impl(report)


def _factor_decomp_cross_check(
    *,
    factor_variance: float | None,
    portfolio_total_variance: float | None,
    r2: float | None,
) -> dict[str, Any]:
    base = {
        "method": "factor_variance_divided_by_portfolio_variance_vs_r2",
        "status": "unavailable",
        "reason": None,
        "variance_based_explained_share": None,
        "r2": r2,
        "absolute_difference": None,
        "relative_difference": None,
        "warning_code": None,
    }
    if factor_variance is None or not np.isfinite(factor_variance):
        return {**base, "reason": "invalid_factor_variance"}
    if portfolio_total_variance is None or not np.isfinite(portfolio_total_variance) or portfolio_total_variance <= FACTOR_VARIANCE_DECOMP_EPS:
        return {**base, "reason": "invalid_portfolio_total_variance"}
    if r2 is None or not np.isfinite(r2):
        return {**base, "reason": "invalid_r2"}

    variance_based = float(factor_variance / portfolio_total_variance)
    abs_diff = abs(variance_based - float(r2))
    rel_diff = abs_diff / max(abs(float(r2)), 0.05)
    status = "pass"
    warning_code = None
    if abs_diff > 0.02:
        status = "high_warning"
        warning_code = "WARN_FACTOR_VARIANCE_DECOMP_HIGH_MISMATCH"
    elif abs_diff > 0.005:
        status = "warning"
        warning_code = "WARN_FACTOR_VARIANCE_DECOMP_MISMATCH"
    return {
        **base,
        "status": status,
        "reason": None,
        "variance_based_explained_share": variance_based,
        "absolute_difference": float(abs_diff),
        "relative_difference": float(rel_diff),
        "warning_code": warning_code,
    }


def _residual_diagnostics(residual_share: float | None) -> dict[str, Any]:
    if residual_share is None or not np.isfinite(residual_share):
        return {
            "residual_severity": "unknown",
            "residual_interpretation": "Residual share is unavailable.",
            "residual_recommendation": "Review factor data and regression availability before interpreting factor decomposition.",
        }
    if residual_share >= 0.60:
        return {
            "residual_severity": "high",
            "residual_interpretation": "The current factor model leaves most weekly portfolio variance unexplained.",
            "residual_recommendation": "Review omitted factors, nonlinear exposures, asset-specific risk, factor definitions, and beta stability before relying on factor rankings.",
        }
    if residual_share >= 0.35:
        return {
            "residual_severity": "moderate",
            "residual_interpretation": "A material share of weekly portfolio variance remains outside the current factor model.",
            "residual_recommendation": "Use factor rankings with caution and review omitted factors or unstable beta estimates.",
        }
    return {
        "residual_severity": "low",
        "residual_interpretation": "The current factor model explains most weekly portfolio variance.",
        "residual_recommendation": "Factor decomposition is suitable as a diagnostic risk-management signal.",
    }


def _factor_variance_decomposition_unavailable(
    reason: str,
    *,
    window: str = "5y_weekly",
    n_obs: int | None = None,
) -> dict[str, Any]:
    cross_check = _factor_decomp_cross_check(factor_variance=None, portfolio_total_variance=None, r2=None)
    cross_check["reason"] = reason
    return {
        "status": "unavailable",
        "reason": reason,
        "method": "r2_scaled_factor_rc_plus_residual",
        "window": window,
        "variance_scale": "weekly",
        "ddof": 1,
        "n_obs": n_obs,
        "neutral_threshold": FACTOR_VARIANCE_DECOMP_NEUTRAL_THRESHOLD,
        "r2": None,
        "residual_share": None,
        **_residual_diagnostics(None),
        "portfolio_total_variance": None,
        "factor_variance": None,
        "explained_factor_share_r2_scaled": None,
        "variance_based_explained_share": None,
        "cross_check": cross_check,
        "warnings": [],
        "rows": [],
        "risk_adders": [],
        "hedgers": [],
        "neutral_factors": [],
        "gross_top_contributors_abs": [],
        "stability": {
            "status": "unknown",
            "reason": "current_decomposition_unavailable",
            "overall_severity": "unknown",
            "by_factor": {},
            "r2": {"current": None, "p10": None, "p90": None, "severity": "unknown"},
        },
    }


def _factor_direction(value: float, *, neutral_threshold: float = FACTOR_VARIANCE_DECOMP_NEUTRAL_THRESHOLD) -> str:
    if not np.isfinite(value) or abs(value) < neutral_threshold:
        return "neutral"
    return "risk_adder" if value > 0.0 else "hedger"


def _factor_variance_decomposition_stability(
    snapshots: list[dict[str, Any]],
    *,
    current_r2: float | None,
) -> dict[str, Any]:
    usable = [s for s in snapshots if isinstance(s, dict) and s.get("status") == "available" and s.get("rows")]
    if len(usable) < 2:
        return {
            "status": "unknown",
            "reason": "insufficient_rolling_observations",
            "overall_severity": "unknown",
            "by_factor": {},
            "r2": {"current": current_r2, "p10": None, "p90": None, "severity": "unknown"},
        }

    by_factor: dict[str, dict[str, Any]] = {}
    severities: list[str] = []
    factors = [str(row.get("factor")) for row in usable[0].get("rows", []) if row.get("direction") != "residual"]
    for factor in factors:
        signs: list[int] = []
        for snap in usable:
            row = next((r for r in snap.get("rows", []) if r.get("factor") == factor), None)
            if not isinstance(row, dict):
                continue
            value = _safe_float(row.get("net_total_variance_share"))
            if value is None:
                continue
            signs.append(_beta_sign(value, eps=FACTOR_VARIANCE_DECOMP_NEUTRAL_THRESHOLD))
        if not signs:
            severity = "unknown"
            share = None
        else:
            counts = {s: signs.count(s) for s in (-1, 0, 1)}
            share = float(max(counts.values()) / len(signs))
            if share < 0.65:
                severity = "high"
            elif share < 0.80:
                severity = "moderate"
            else:
                severity = "low"
        by_factor[factor] = {
            "sign_stability_share": share,
            "severity": severity,
        }
        severities.append(severity)

    r2_values = [
        _safe_float(s.get("r2"))
        for s in usable
        if _safe_float(s.get("r2")) is not None
    ]
    r2_values = [v for v in r2_values if v is not None]
    if len(r2_values) < 2:
        r2_diag = {"current": current_r2, "p10": None, "p90": None, "severity": "unknown"}
        severities.append("unknown")
    else:
        p10 = float(np.quantile(r2_values, 0.10))
        p90 = float(np.quantile(r2_values, 0.90))
        if p10 < 0.25:
            r2_sev = "high"
        elif p10 < 0.40:
            r2_sev = "moderate"
        else:
            r2_sev = "low"
        r2_diag = {"current": current_r2, "p10": p10, "p90": p90, "severity": r2_sev}
        severities.append(r2_sev)

    return {
        "status": "available",
        "reason": None,
        "overall_severity": _severity_max(severities),
        "by_factor": by_factor,
        "r2": r2_diag,
    }


def _factor_variance_decomposition_from_rows(
    y: np.ndarray,
    X: np.ndarray,
    factor_cols: list[str],
    *,
    window: str = "5y_weekly",
    include_stability: bool = True,
    stability_snapshots: list[dict[str, Any]] | None = None,
    neutral_threshold: float = FACTOR_VARIANCE_DECOMP_NEUTRAL_THRESHOLD,
) -> dict[str, Any]:
    y_arr = np.asarray(y, dtype=float).reshape(-1)
    x_arr = np.asarray(X, dtype=float)
    cols = [str(c) for c in factor_cols]
    if x_arr.ndim != 2 or y_arr.ndim != 1 or x_arr.shape[0] != len(y_arr) or x_arr.shape[1] != len(cols) or len(set(cols)) != len(cols):
        return _factor_variance_decomposition_unavailable("factor_dimension_mismatch", window=window, n_obs=int(len(y_arr)))
    n_obs = int(len(y_arr))
    if n_obs < FACTOR_VARIANCE_DECOMP_MIN_OBS:
        return _factor_variance_decomposition_unavailable("insufficient_observations", window=window, n_obs=n_obs)
    valid = ~(np.isnan(y_arr) | np.isnan(x_arr).any(axis=1))
    y_arr = y_arr[valid]
    x_arr = x_arr[valid]
    n_obs = int(len(y_arr))
    if n_obs < FACTOR_VARIANCE_DECOMP_MIN_OBS:
        return _factor_variance_decomposition_unavailable("insufficient_observations", window=window, n_obs=n_obs)

    inf = _ols_with_inference(y_arr, x_arr, add_const=True)
    if not inf:
        return _factor_variance_decomposition_unavailable("ols_failed", window=window, n_obs=n_obs)

    beta_vec = np.asarray(inf["params"][1:], dtype=float)
    factor_cov = pd.DataFrame(x_arr, columns=cols).cov(ddof=1).reindex(index=cols, columns=cols)
    if beta_vec.shape[0] != len(cols) or factor_cov.shape != (len(cols), len(cols)) or list(factor_cov.index) != cols or list(factor_cov.columns) != cols:
        return _factor_variance_decomposition_unavailable("factor_dimension_mismatch", window=window, n_obs=n_obs)

    portfolio_total_variance = float(np.var(y_arr, ddof=1))
    if not np.isfinite(portfolio_total_variance) or portfolio_total_variance <= FACTOR_VARIANCE_DECOMP_EPS:
        out = _factor_variance_decomposition_unavailable("degenerate_portfolio_variance", window=window, n_obs=n_obs)
        out["portfolio_total_variance"] = portfolio_total_variance if np.isfinite(portfolio_total_variance) else None
        out["cross_check"] = _factor_decomp_cross_check(factor_variance=None, portfolio_total_variance=portfolio_total_variance, r2=_safe_float(inf.get("r2")))
        return out

    cov_vals = factor_cov.values.astype(float)
    marginal = cov_vals @ beta_vec
    factor_variance = float(beta_vec.T @ cov_vals @ beta_vec)
    if not np.isfinite(factor_variance) or factor_variance <= FACTOR_VARIANCE_DECOMP_EPS:
        out = _factor_variance_decomposition_unavailable("degenerate_factor_variance", window=window, n_obs=n_obs)
        out["portfolio_total_variance"] = portfolio_total_variance
        out["factor_variance"] = factor_variance if np.isfinite(factor_variance) else None
        out["cross_check"] = _factor_decomp_cross_check(factor_variance=factor_variance, portfolio_total_variance=portfolio_total_variance, r2=_safe_float(inf.get("r2")))
        return out

    r2 = _safe_float(inf.get("r2"))
    if r2 is None:
        out = _factor_variance_decomposition_unavailable("invalid_r2", window=window, n_obs=n_obs)
        out["portfolio_total_variance"] = portfolio_total_variance
        out["factor_variance"] = factor_variance
        out["cross_check"] = _factor_decomp_cross_check(factor_variance=factor_variance, portfolio_total_variance=portfolio_total_variance, r2=None)
        return out

    residual_share = float(1.0 - r2)
    components = beta_vec * marginal
    gross_abs = np.abs(components)
    gross_denom = float(gross_abs.sum())
    rows: list[dict[str, Any]] = []
    beta_keys = [FACTOR_TO_BETA_KEY.get(c, f"beta_{c}") for c in cols]
    for factor, beta_key, comp, gross_comp in zip(cols, beta_keys, components, gross_abs):
        factor_rc_share = float(comp / factor_variance)
        net_total_share = float(factor_rc_share * r2)
        gross_factor_rc_share = float(gross_comp / gross_denom) if gross_denom > FACTOR_VARIANCE_DECOMP_EPS else 0.0
        gross_total_share = float(gross_factor_rc_share * r2)
        rows.append(
            {
                "factor": str(factor),
                "beta_key": str(beta_key),
                "net_component_variance": float(comp),
                "factor_rc_share": factor_rc_share,
                "net_total_variance_share": net_total_share,
                "gross_component_variance_abs": float(gross_comp),
                "gross_factor_rc_share": gross_factor_rc_share,
                "gross_total_variance_share": gross_total_share,
                "direction": _factor_direction(net_total_share, neutral_threshold=neutral_threshold),
            }
        )

    residual_diag = _residual_diagnostics(residual_share)
    residual_row = {
        "factor": "Residual",
        "beta_key": None,
        "net_component_variance": None,
        "factor_rc_share": None,
        "net_total_variance_share": residual_share,
        "gross_component_variance_abs": None,
        "gross_factor_rc_share": None,
        "gross_total_variance_share": residual_share,
        "direction": "residual",
    }
    rows_with_residual = rows + [residual_row]
    risk_adders = sorted([r for r in rows if r["direction"] == "risk_adder"], key=lambda r: r["net_total_variance_share"], reverse=True)
    hedgers = sorted([r for r in rows if r["direction"] == "hedger"], key=lambda r: abs(r["net_total_variance_share"]), reverse=True)
    neutral_factors = sorted([r for r in rows if r["direction"] == "neutral"], key=lambda r: abs(r["net_total_variance_share"]), reverse=True)
    gross_top = sorted(rows, key=lambda r: r["gross_total_variance_share"], reverse=True)

    cross_check = _factor_decomp_cross_check(
        factor_variance=factor_variance,
        portfolio_total_variance=portfolio_total_variance,
        r2=r2,
    )
    warnings: list[str] = []
    if cross_check.get("warning_code"):
        warnings.append(str(cross_check["warning_code"]))
    if any(abs(float(r["net_total_variance_share"])) > 1.0 for r in rows):
        warnings.append("WARN_FACTOR_VARIANCE_DECOMP_EXTREME_NET_SHARE")
    gross_total_variance_share_sum = float(sum(float(r["gross_total_variance_share"]) for r in rows))
    if gross_total_variance_share_sum > r2 + 0.25:
        warnings.append("WARN_FACTOR_VARIANCE_DECOMP_HIGH_GROSS_CONCENTRATION")
    net_share_sum = float(sum(float(r["net_total_variance_share"]) for r in rows))
    if abs(net_share_sum - r2) > 1e-6:
        warnings.append("WARN_FACTOR_VARIANCE_DECOMP_SHARE_SUM_MISMATCH")
    warnings = list(dict.fromkeys(warnings))

    stability = (
        _factor_variance_decomposition_stability(stability_snapshots or [], current_r2=r2)
        if include_stability
        else {
            "status": "unknown",
            "reason": "not_computed_for_snapshot",
            "overall_severity": "unknown",
            "by_factor": {},
            "r2": {"current": r2, "p10": None, "p90": None, "severity": "unknown"},
        }
    )
    return {
        "status": "available",
        "reason": None,
        "method": "r2_scaled_factor_rc_plus_residual",
        "window": window,
        "variance_scale": "weekly",
        "ddof": 1,
        "n_obs": n_obs,
        "neutral_threshold": float(neutral_threshold),
        "r2": r2,
        "residual_share": residual_share,
        **residual_diag,
        "portfolio_total_variance": portfolio_total_variance,
        "factor_variance": factor_variance,
        "explained_factor_share_r2_scaled": r2,
        "variance_based_explained_share": cross_check.get("variance_based_explained_share"),
        "factor_rc_share_sum": float(sum(float(r["factor_rc_share"]) for r in rows)),
        "net_total_variance_share_sum": net_share_sum,
        "gross_total_variance_share_sum": gross_total_variance_share_sum,
        "cross_check": cross_check,
        "warnings": warnings,
        "rows": rows_with_residual,
        "risk_adders": risk_adders,
        "hedgers": hedgers,
        "neutral_factors": neutral_factors,
        "gross_top_contributors_abs": gross_top,
        "stability": stability,
    }


def factor_variance_decomposition_weekly(
    *,
    weights: dict[str, float],
    tickers: list[str],
    analysis_end_str: str,
    window_weeks: int = FACTOR_WEEKS_5Y,
    rolling_windows_weeks: dict[str, int] | None = None,
) -> dict[str, Any]:
    rows = _portfolio_factor_weekly_ols_rows(
        weights=weights,
        tickers=tickers,
        analysis_end_str=analysis_end_str,
        window_weeks=window_weeks,
    )
    if rows.get("error"):
        return _factor_variance_decomposition_unavailable(
            str(rows.get("error")),
            window="5y_weekly",
            n_obs=rows.get("n_obs"),
        )

    snapshots: list[dict[str, Any]] = []
    windows = rolling_windows_weeks or {"3y": FACTOR_WEEKS_3Y, "5y": FACTOR_WEEKS_5Y, "10y": FACTOR_WEEKS_10Y}
    for label, weeks in windows.items():
        snap_rows = _portfolio_factor_weekly_ols_rows(
            weights=weights,
            tickers=tickers,
            analysis_end_str=analysis_end_str,
            window_weeks=int(weeks),
        )
        if snap_rows.get("error"):
            continue
        snap = _factor_variance_decomposition_from_rows(
            np.asarray(snap_rows["y"], dtype=float),
            np.asarray(snap_rows["X"], dtype=float),
            list(snap_rows["factor_cols"]),
            window=f"{label}_weekly",
            include_stability=False,
        )
        if snap.get("status") == "available":
            snapshots.append(snap)

    out = _factor_variance_decomposition_from_rows(
        np.asarray(rows["y"], dtype=float),
        np.asarray(rows["X"], dtype=float),
        list(rows["factor_cols"]),
        window="5y_weekly",
        include_stability=True,
        stability_snapshots=snapshots,
    )
    for warning in out.get("warnings") or []:
        _LOG.warning("Factor variance decomposition warning: %s", warning)
    return out


def _rc_stability(base_rc: pd.DataFrame, stress_rc: pd.DataFrame) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    base_by = base_rc.set_index("factor")["rc_share"] if not base_rc.empty else pd.Series(dtype=float)
    stress_by = stress_rc.set_index("factor")["rc_share"] if not stress_rc.empty else pd.Series(dtype=float)
    threshold = FACTOR_COVARIANCE_RC_STABILITY_THRESHOLD_PCT / 100.0
    for factor in FACTOR_COLUMN_ORDER:
        base_v = float(base_by.get(factor, 0.0))
        stress_v = float(stress_by.get(factor, 0.0))
        abs_shift = abs(stress_v - base_v)
        denom = max(abs(base_v), 1e-12)
        rel_shift = abs_shift / denom
        rows.append(
            {
                "factor": str(factor),
                "beta_key": FACTOR_TO_BETA_KEY.get(str(factor), f"beta_{factor}"),
                "base_rc_share": base_v,
                "stress_empirical_rc_share": stress_v,
                "absolute_shift": abs_shift,
                "relative_shift": rel_shift,
                "RC_stability_flag": bool(rel_shift > threshold),
            }
        )
    return {
        "threshold_pct": FACTOR_COVARIANCE_RC_STABILITY_THRESHOLD_PCT,
        "overall_flag": any(bool(r["RC_stability_flag"]) for r in rows),
        "by_factor": rows,
    }


def _rolling_beta_std_map(rolling_betas_weekly: dict[str, pd.DataFrame] | None) -> dict[str, float]:
    rb = rolling_betas_weekly or {}
    preferred = rb.get("5y")
    frames = [preferred] if isinstance(preferred, pd.DataFrame) and not preferred.empty else [
        df for df in rb.values() if isinstance(df, pd.DataFrame) and not df.empty
    ]
    out: dict[str, float] = {}
    for beta_key in BETA_ROW_ORDER:
        vals: list[float] = []
        for df in frames:
            if beta_key in df.columns:
                vals.extend(pd.to_numeric(df[beta_key], errors="coerce").dropna().astype(float).tolist())
        out[beta_key] = float(np.std(vals, ddof=1)) if len(vals) >= 2 else 0.0
    return out


def _beta_sensitivity(
    covariances: dict[str, tuple[pd.DataFrame, str]],
    beta_vec: np.ndarray,
    beta_std: dict[str, float],
) -> dict[str, Any]:
    std_vec = np.asarray(
        [float(beta_std.get(FACTOR_TO_BETA_KEY.get(f, f"beta_{f}"), 0.0)) for f in FACTOR_COLUMN_ORDER],
        dtype=float,
    )
    minus_vec = beta_vec - std_vec
    plus_vec = beta_vec + std_vec
    out: dict[str, Any] = {}
    for label, (cov, classification) in covariances.items():
        base = _portfolio_factor_risk(cov, beta_vec, label=label, classification=classification)
        minus = _portfolio_factor_risk(cov, minus_vec, label=label, classification=classification)
        plus = _portfolio_factor_risk(cov, plus_vec, label=label, classification=classification)
        variances = [
            base["portfolio_factor_variance"],
            minus["portfolio_factor_variance"],
            plus["portfolio_factor_variance"],
        ]
        vols = [
            base["portfolio_factor_vol"],
            minus["portfolio_factor_vol"],
            plus["portfolio_factor_vol"],
        ]
        out[label] = {
            "label": label,
            "classification": classification,
            "method": "portfolio_betas_plus_minus_one_rolling_beta_std",
            "beta_std": {k: float(v) for k, v in beta_std.items()},
            "variance_current": base["portfolio_factor_variance"],
            "variance_minus_1std": minus["portfolio_factor_variance"],
            "variance_plus_1std": plus["portfolio_factor_variance"],
            "variance_min": float(min(variances)),
            "variance_max": float(max(variances)),
            "vol_current": base["portfolio_factor_vol"],
            "vol_minus_1std": minus["portfolio_factor_vol"],
            "vol_plus_1std": plus["portfolio_factor_vol"],
            "vol_min": float(min(vols)),
            "vol_max": float(max(vols)),
        }
    return out


def _pairwise_covariance_comparison(
    lhs: pd.DataFrame,
    rhs: pd.DataFrame,
    *,
    lhs_label: str,
    rhs_label: str,
) -> list[dict[str, Any]]:
    lhs_cov = lhs.reindex(index=FACTOR_COLUMN_ORDER, columns=FACTOR_COLUMN_ORDER).fillna(0.0)
    rhs_cov = rhs.reindex(index=FACTOR_COLUMN_ORDER, columns=FACTOR_COLUMN_ORDER).fillna(0.0)
    lhs_corr = _correlation_from_covariance(lhs_cov)
    rhs_corr = _correlation_from_covariance(rhs_cov)
    rows: list[dict[str, Any]] = []
    for i, fi in enumerate(FACTOR_COLUMN_ORDER):
        for j, fj in enumerate(FACTOR_COLUMN_ORDER):
            if i >= j:
                continue
            lhs_c = float(lhs_cov.loc[fi, fj])
            rhs_c = float(rhs_cov.loc[fi, fj])
            lhs_r = float(lhs_corr.loc[fi, fj])
            rhs_r = float(rhs_corr.loc[fi, fj])
            rows.append(
                {
                    "factor_i": str(fi),
                    "factor_j": str(fj),
                    f"{lhs_label}_cov": lhs_c,
                    f"{rhs_label}_cov": rhs_c,
                    "cov_delta": rhs_c - lhs_c,
                    "abs_cov_delta": abs(rhs_c - lhs_c),
                    f"{lhs_label}_corr": lhs_r,
                    f"{rhs_label}_corr": rhs_r,
                    "corr_delta": rhs_r - lhs_r,
                    "abs_corr_delta": abs(rhs_r - lhs_r),
                }
            )
    rows.sort(key=lambda row: (row["abs_corr_delta"], row["abs_cov_delta"]), reverse=True)
    return rows


def _covariance_stability_check(base_5y_cov: pd.DataFrame, base_2y_cov: pd.DataFrame) -> dict[str, Any]:
    threshold = FACTOR_COVARIANCE_STABILITY_THRESHOLD_PCT / 100.0
    by_pair: list[dict[str, Any]] = []
    by_var: list[dict[str, Any]] = []
    abs_fallback_floor = 1e-8
    for i, fi in enumerate(FACTOR_COLUMN_ORDER):
        v5 = float(base_5y_cov.loc[fi, fi])
        v2 = float(base_2y_cov.loc[fi, fi])
        abs_delta = abs(v2 - v5)
        rel = abs_delta / abs(v5) if abs(v5) > abs_fallback_floor else None
        flag = bool((rel is not None and rel > threshold) or (rel is None and abs_delta > abs_fallback_floor))
        by_var.append(
            {
                "factor": str(fi),
                "base_5y_variance": v5,
                "base_2y_variance": v2,
                "absolute_delta": abs_delta,
                "relative_deviation": rel,
                "flag": flag,
            }
        )
        for j, fj in enumerate(FACTOR_COLUMN_ORDER):
            if i >= j:
                continue
            c5 = float(base_5y_cov.loc[fi, fj])
            c2 = float(base_2y_cov.loc[fi, fj])
            abs_delta = abs(c2 - c5)
            rel = abs_delta / abs(c5) if abs(c5) > abs_fallback_floor else None
            flag = bool((rel is not None and rel > threshold) or (rel is None and abs_delta > abs_fallback_floor))
            by_pair.append(
                {
                    "factor_i": str(fi),
                    "factor_j": str(fj),
                    "base_5y_cov": c5,
                    "base_2y_cov": c2,
                    "absolute_delta": abs_delta,
                    "relative_deviation": rel,
                    "flag": flag,
                }
            )
    return {
        "classification": "data_driven",
        "threshold_pct": FACTOR_COVARIANCE_STABILITY_THRESHOLD_PCT,
        "overall_flag": any(bool(r["flag"]) for r in by_pair + by_var),
        "by_pair": sorted(by_pair, key=lambda row: (row["relative_deviation"] is not None, row["relative_deviation"] or 0.0, row["absolute_delta"]), reverse=True),
        "by_factor_variance": sorted(by_var, key=lambda row: (row["relative_deviation"] is not None, row["relative_deviation"] or 0.0, row["absolute_delta"]), reverse=True),
    }


def _factor_covariance_forecast_quality_unavailable(reason: str, *, n_obs: int | None = None) -> dict[str, Any]:
    return {
        "status": "unavailable",
        "reason": reason,
        "method": "rolling_5y_covariance_vs_next_1y_realized_factor_risk",
        "variance_scale": "weekly",
        "train_weeks": FACTOR_COVARIANCE_FORECAST_TRAIN_WEEKS,
        "holdout_weeks": FACTOR_COVARIANCE_FORECAST_HOLDOUT_WEEKS,
        "step_weeks": FACTOR_COVARIANCE_FORECAST_STEP_WEEKS,
        "ddof": 1,
        "n_obs": n_obs,
        "summary": {
            "n_forecasts": 0,
            "median_abs_vol_error_pct": None,
            "mean_abs_vol_error_pct": None,
            "mean_signed_vol_error_pct": None,
            "hit_rate_abs_vol_error_le_10pct": None,
            "hit_rate_abs_vol_error_le_20pct": None,
            "hit_rate_abs_vol_error_le_30pct": None,
            "median_corr_rmse": None,
            "median_covariance_relative_frobenius_error": None,
            "overall_severity": "unknown",
        },
        "rows": [],
    }


def _offdiag_corr_rmse_and_worst_pair(forecast_cov: pd.DataFrame, realized_cov: pd.DataFrame) -> tuple[float | None, dict[str, Any] | None]:
    forecast_corr = _correlation_from_covariance(forecast_cov)
    realized_corr = _correlation_from_covariance(realized_cov)
    diffs: list[float] = []
    worst: dict[str, Any] | None = None
    for i, fi in enumerate(FACTOR_COLUMN_ORDER):
        for j, fj in enumerate(FACTOR_COLUMN_ORDER):
            if i >= j:
                continue
            forecast_v = float(forecast_corr.loc[fi, fj])
            realized_v = float(realized_corr.loc[fi, fj])
            diff = realized_v - forecast_v
            diffs.append(diff)
            row = {
                "factor_i": str(fi),
                "factor_j": str(fj),
                "forecast_corr": forecast_v,
                "realized_corr": realized_v,
                "corr_error": diff,
                "abs_corr_error": abs(diff),
            }
            if worst is None or row["abs_corr_error"] > worst["abs_corr_error"]:
                worst = row
    if not diffs:
        return None, worst
    return float(np.sqrt(np.mean(np.square(diffs)))), worst


def _factor_covariance_forecast_quality(
    factors: pd.DataFrame,
    beta_vec: np.ndarray,
    *,
    train_weeks: int = FACTOR_COVARIANCE_FORECAST_TRAIN_WEEKS,
    holdout_weeks: int = FACTOR_COVARIANCE_FORECAST_HOLDOUT_WEEKS,
    step_weeks: int = FACTOR_COVARIANCE_FORECAST_STEP_WEEKS,
) -> dict[str, Any]:
    ordered = factors.loc[:, list(FACTOR_COLUMN_ORDER)].sort_index()
    ordered = ordered.apply(pd.to_numeric, errors="coerce").dropna(how="any")
    min_obs = int(train_weeks + holdout_weeks)
    if len(ordered) < min_obs:
        return _factor_covariance_forecast_quality_unavailable(
            "insufficient_factor_history",
            n_obs=int(len(ordered)),
        )

    beta_arr = np.asarray(beta_vec, dtype=float).reshape(-1)
    if beta_arr.shape[0] != len(FACTOR_COLUMN_ORDER):
        return _factor_covariance_forecast_quality_unavailable(
            "factor_dimension_mismatch",
            n_obs=int(len(ordered)),
        )

    rows: list[dict[str, Any]] = []
    for start in range(0, len(ordered) - min_obs + 1, int(step_weeks)):
        train_rows = ordered.iloc[start : start + train_weeks]
        holdout_rows = ordered.iloc[start + train_weeks : start + train_weeks + holdout_weeks]
        if len(train_rows) < train_weeks or len(holdout_rows) < holdout_weeks:
            continue

        forecast_cov = _factor_covariance_matrix(train_rows)
        realized_cov = _factor_covariance_matrix(holdout_rows)
        forecast_vals = forecast_cov.values.astype(float)
        realized_vals = realized_cov.values.astype(float)
        model_variance = max(float(beta_arr.T @ forecast_vals @ beta_arr), 0.0)
        realized_factor_returns = holdout_rows.values.astype(float) @ beta_arr
        realized_variance = float(np.var(realized_factor_returns, ddof=1)) if len(realized_factor_returns) >= 2 else np.nan
        if not np.isfinite(realized_variance):
            continue
        realized_variance = max(realized_variance, 0.0)
        model_vol = float(np.sqrt(model_variance))
        realized_vol = float(np.sqrt(realized_variance))

        if model_vol > 1e-12:
            signed_error = float((realized_vol - model_vol) / model_vol)
            abs_error = abs(signed_error)
        elif realized_vol <= 1e-12:
            signed_error = 0.0
            abs_error = 0.0
        else:
            signed_error = None
            abs_error = None

        corr_rmse, worst_pair = _offdiag_corr_rmse_and_worst_pair(forecast_cov, realized_cov)
        denom = float(np.linalg.norm(forecast_vals, ord="fro"))
        cov_rel_frob = (
            float(np.linalg.norm(realized_vals - forecast_vals, ord="fro") / denom)
            if denom > 1e-12
            else None
        )

        rows.append(
            {
                "cutoff_date": str(pd.Timestamp(train_rows.index[-1]).date()),
                "realized_end_date": str(pd.Timestamp(holdout_rows.index[-1]).date()),
                "n_train": int(len(train_rows)),
                "n_holdout": int(len(holdout_rows)),
                "model_factor_variance": model_variance,
                "model_factor_vol": model_vol,
                "realized_factor_variance": realized_variance,
                "realized_factor_vol": realized_vol,
                "signed_vol_error_pct": signed_error,
                "abs_vol_error_pct": abs_error,
                "corr_rmse": corr_rmse,
                "covariance_relative_frobenius_error": cov_rel_frob,
                "worst_corr_error_pair": worst_pair,
                "worst_corr_error_factor_i": (worst_pair or {}).get("factor_i"),
                "worst_corr_error_factor_j": (worst_pair or {}).get("factor_j"),
                "worst_corr_error": (worst_pair or {}).get("corr_error"),
                "worst_abs_corr_error": (worst_pair or {}).get("abs_corr_error"),
            }
        )

    if not rows:
        return _factor_covariance_forecast_quality_unavailable("no_valid_forecast_windows", n_obs=int(len(ordered)))

    abs_errors = [
        float(row["abs_vol_error_pct"])
        for row in rows
        if row.get("abs_vol_error_pct") is not None and np.isfinite(float(row["abs_vol_error_pct"]))
    ]
    signed_errors = [
        float(row["signed_vol_error_pct"])
        for row in rows
        if row.get("signed_vol_error_pct") is not None and np.isfinite(float(row["signed_vol_error_pct"]))
    ]
    corr_rmses = [
        float(row["corr_rmse"])
        for row in rows
        if row.get("corr_rmse") is not None and np.isfinite(float(row["corr_rmse"]))
    ]
    frob_errors = [
        float(row["covariance_relative_frobenius_error"])
        for row in rows
        if row.get("covariance_relative_frobenius_error") is not None
        and np.isfinite(float(row["covariance_relative_frobenius_error"]))
    ]
    median_abs = float(np.median(abs_errors)) if abs_errors else None
    hit20 = float(np.mean([v <= 0.20 for v in abs_errors])) if abs_errors else None
    if median_abs is None or hit20 is None:
        severity = "unknown"
    elif median_abs > 0.35 or hit20 < 0.35:
        severity = "high"
    elif median_abs <= 0.15 and hit20 >= 0.60:
        severity = "low"
    else:
        severity = "moderate"

    return {
        "status": "available",
        "reason": None,
        "method": "rolling_5y_covariance_vs_next_1y_realized_factor_risk",
        "variance_scale": "weekly",
        "train_weeks": int(train_weeks),
        "holdout_weeks": int(holdout_weeks),
        "step_weeks": int(step_weeks),
        "ddof": 1,
        "n_obs": int(len(ordered)),
        "summary": {
            "n_forecasts": int(len(rows)),
            "median_abs_vol_error_pct": median_abs,
            "mean_abs_vol_error_pct": float(np.mean(abs_errors)) if abs_errors else None,
            "mean_signed_vol_error_pct": float(np.mean(signed_errors)) if signed_errors else None,
            "hit_rate_abs_vol_error_le_10pct": float(np.mean([v <= 0.10 for v in abs_errors])) if abs_errors else None,
            "hit_rate_abs_vol_error_le_20pct": hit20,
            "hit_rate_abs_vol_error_le_30pct": float(np.mean([v <= 0.30 for v in abs_errors])) if abs_errors else None,
            "median_corr_rmse": float(np.median(corr_rmses)) if corr_rmses else None,
            "median_covariance_relative_frobenius_error": float(np.median(frob_errors)) if frob_errors else None,
            "overall_severity": severity,
        },
        "rows": rows,
    }


def factor_covariance_analytics(
    *,
    analysis_end_str: str,
    portfolio_betas: dict[str, Any] | None,
    rolling_betas_weekly: dict[str, pd.DataFrame] | None = None,
    factor_returns: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """Build explicit base / stress_empirical / stress_overlay factor covariance analytics."""
    end_ts = pd.Timestamp(analysis_end_str)
    if factor_returns is None or factor_returns.empty:
        start = (end_ts - pd.DateOffset(years=20)).strftime("%Y-%m-%d")
        factors_raw = build_factor_matrix(start, (end_ts + pd.Timedelta(days=1)).strftime("%Y-%m-%d"))
    else:
        factors_raw = factor_returns.copy()
    factors, missing_factor_columns = _ordered_factor_frame(factors_raw)
    factors = factors.loc[factors.index <= end_ts + pd.Timedelta(days=6)]
    if len(factors) < 2:
        return {
            "error": "insufficient_factor_history",
            "factor_order": list(FACTOR_COLUMN_ORDER),
            "missing_factor_columns_zero_filled": missing_factor_columns,
        }

    base_rows = factors.tail(FACTOR_COVARIANCE_BASE_WEEKS)
    base_2y_rows = factors.tail(FACTOR_COVARIANCE_STABILITY_WEEKS)
    stress_rows = _stress_empirical_rows(factors)
    if stress_rows.empty:
        stress_rows = pd.DataFrame(0.0, index=base_rows.index[:0], columns=FACTOR_COLUMN_ORDER)

    base_cov = _factor_covariance_matrix(base_rows)
    base_2y_cov = _factor_covariance_matrix(base_2y_rows)
    stress_emp_cov = _factor_covariance_matrix(stress_rows)
    overlay_cov, overlay_deltas, overlay_repaired = _build_stress_overlay_covariance(base_cov, stress_emp_cov)

    beta_vec, exposure = _exposure_vector(portfolio_betas)
    covariances = {
        "base": (base_cov, "data_driven"),
        "stress_empirical": (stress_emp_cov, "data_driven"),
        "stress_overlay": (overlay_cov, "hypothetical"),
    }
    risk = {
        label: _portfolio_factor_risk(cov, beta_vec, label=label, classification=classification)
        for label, (cov, classification) in covariances.items()
    }
    rc_frames = {label: _factor_rc(cov, beta_vec) for label, (cov, _classification) in covariances.items()}
    beta_std = _rolling_beta_std_map(rolling_betas_weekly)
    empirical_change = _pairwise_covariance_comparison(base_cov, stress_emp_cov, lhs_label="base", rhs_label="stress_empirical")
    overlay_amplification = _pairwise_covariance_comparison(stress_emp_cov, overlay_cov, lhs_label="stress_empirical", rhs_label="stress_overlay")
    forecast_quality = _factor_covariance_forecast_quality(factors, beta_vec)

    return {
        "method": "weekly_factor_covariance_regime_separated",
        "factor_order": list(FACTOR_COLUMN_ORDER),
        "beta_order": [FACTOR_TO_BETA_KEY.get(f, f"beta_{f}") for f in FACTOR_COLUMN_ORDER],
        "missing_factor_columns_zero_filled": missing_factor_columns,
        "exposure_vector": exposure,
        "base": _regime_block(
            label="base",
            classification="data_driven",
            cov=base_cov,
            n_obs=len(base_rows),
            window={
                "weeks": FACTOR_COVARIANCE_BASE_WEEKS,
                "frequency": "weekly",
                "analysis_end": str(analysis_end_str),
            },
        ),
        "stress_empirical": _regime_block(
            label="stress_empirical",
            classification="data_driven",
            cov=stress_emp_cov,
            n_obs=len(stress_rows),
            episodes_used=[ep for ep, _start, _end in FACTOR_COVARIANCE_STRESS_EPISODES],
        ),
        "stress_overlay": _regime_block(
            label="stress_overlay",
            classification="hypothetical",
            cov=overlay_cov,
            n_obs=len(stress_rows),
            episodes_used=[ep for ep, _start, _end in FACTOR_COVARIANCE_STRESS_EPISODES],
            psd_repaired=overlay_repaired,
            overlay_deltas=overlay_deltas,
        ),
        "portfolio_factor_risk": risk,
        "portfolio_factor_rc": {
            label: frame.to_dict(orient="records")
            for label, frame in rc_frames.items()
        },
        "beta_sensitivity": _beta_sensitivity(covariances, beta_vec, beta_std),
        "RC_stability_flag": _rc_stability(rc_frames["base"], rc_frames["stress_empirical"]),
        "covariance_stability_check": _covariance_stability_check(base_cov, base_2y_cov),
        "forecast_quality": forecast_quality,
        "comparison": {
            "empirical_change": empirical_change,
            "overlay_amplification": overlay_amplification,
        },
    }


def rolling_beta_summary(rolling_betas: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Summary stats for rolling betas by window/beta:
    mean, median, p10, p90, n_points.
    """
    rows: list[dict[str, Any]] = []
    for label, df in (rolling_betas or {}).items():
        if df is None or df.empty:
            continue
        for col in df.columns:
            s = pd.to_numeric(df[col], errors="coerce").dropna()
            if s.empty:
                continue
            rows.append(
                {
                    "window": str(label),
                    "beta": str(col),
                    "n_points": int(len(s)),
                    "mean": float(s.mean()),
                    "median": float(s.median()),
                    "p10": float(s.quantile(0.10)),
                    "p90": float(s.quantile(0.90)),
                }
            )
    if not rows:
        return pd.DataFrame(columns=["window", "beta", "n_points", "mean", "median", "p10", "p90"])
    beta_rank = {beta_key: idx for idx, beta_key in enumerate(BETA_ROW_ORDER)}
    out_df = pd.DataFrame(rows)
    out_df["beta_rank"] = out_df["beta"].map(lambda beta: beta_rank.get(str(beta), len(beta_rank)))
    out_df = out_df.sort_values(["window", "beta_rank", "beta"]).drop(columns=["beta_rank"]).reset_index(drop=True)
    return out_df


def write_rolling_betas_plot_html(
    rolling_betas: dict[str, pd.DataFrame],
    output_path: str | Path,
) -> Path:
    """Write interactive Plotly HTML with one chart per beta, lines by rolling window."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    payload: dict[str, Any] = {}
    beta_names: set[str] = set()
    for label, df in (rolling_betas or {}).items():
        if df is None or df.empty:
            continue
        beta_names.update(df.columns.tolist())
        payload[str(label)] = {
            "dates": [pd.Timestamp(x).strftime("%Y-%m-%d") for x in df.index],
            "series": {c: [None if pd.isna(v) else float(v) for v in df[c].tolist()] for c in df.columns},
        }

    beta_list = [beta for beta in BETA_ROW_ORDER if beta in beta_names]
    beta_list.extend(sorted(beta for beta in beta_names if beta not in beta_list))
    beta_title_map = {beta: get_factor_display_name(beta) for beta in beta_list}
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Rolling Factor Betas</title>
  <!-- Styling per DESIGN.md (project root): Inter/DM Sans, RUI tokens, flat (no chart chrome shadows in layout). -->
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@9..40,500&family=Inter:ital,opsz,wght@0,14..32,400;500&display=swap" />
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    :root {{
      --rui-dark: #191c1f; --rui-border: #c9c9cd; --rui-surface: #f4f4f4; --rui-white: #ffffff;
      --rui-blue: #494fdf; --rui-mid: #505a63;
    }}
    body {{ font-family: "Inter", system-ui, sans-serif; color: var(--rui-dark); background: var(--rui-white); margin: 0; padding: 2rem 1.5rem; letter-spacing: 0.02em; line-height: 1.5; }}
    h2 {{ font-family: "DM Sans", "Inter", sans-serif; font-size: 1.5rem; font-weight: 500; margin: 0 0 0.5rem; letter-spacing: -0.02em; }}
    p.meta {{ color: var(--rui-mid); font-size: 0.9rem; margin: 0 0 1.5rem; }}
    .chart {{ width: 100%; height: 360px; margin-bottom: 1.5rem; border: 1px solid var(--rui-border); border-radius: 20px; padding: 0.5rem; background: var(--rui-surface); box-shadow: none; }}
  </style>
</head>
<body>
  <h2>Rolling factor betas (portfolio)</h2>
  <p class="meta">Windows: {", ".join(sorted(payload.keys())) if payload else "n/a"}</p>
  <div id="charts"></div>
  <script>
    const dataByWindow = {json.dumps(payload, ensure_ascii=False)};
    const betaList = {json.dumps(beta_list, ensure_ascii=False)};
    const betaTitleMap = {json.dumps(beta_title_map, ensure_ascii=False)};
    const windows = Object.keys(dataByWindow).sort();
    const rui = {{ white: "#ffffff", dark: "#191c1f", border: "#c9c9cd", blue: "#494fdf", success: "#00a87e", warn: "#ec7e00" }};
    const layoutBase = {{
      font: {{ family: "Inter, system-ui, sans-serif", size: 13, color: rui.dark }},
      title: {{ font: {{ family: "DM Sans, Inter, sans-serif", size: 16 }}, }},
      paper_bgcolor: rui.white,
      plot_bgcolor: "#f4f4f4",
      xaxis: {{ gridcolor: rui.border, linecolor: rui.border, title: {{ standoff: 8 }} }},
      yaxis: {{ gridcolor: rui.border, linecolor: rui.border }},
      legend: {{ orientation: "h", bgcolor: "rgba(0,0,0,0)", font: {{ size: 12 }} }}
    }};
    const colorway = [rui.dark, rui.blue, rui.success, rui.warn, "#376cd5", "#e23b4a"];
    const root = document.getElementById("charts");
    betaList.forEach((beta) => {{
      const id = "chart_" + beta;
      const div = document.createElement("div");
      div.className = "chart";
      div.id = id;
      root.appendChild(div);
      const traces = [];
      windows.forEach((w) => {{
        const d = dataByWindow[w];
        if (!d || !d.series || !(beta in d.series)) return;
        traces.push({{
          x: d.dates,
          y: d.series[beta],
          mode: "lines",
          name: w
        }});
      }});
      const layout = Object.assign({{}}, layoutBase, {{
        title: betaTitleMap[beta] || beta,
        xaxis: Object.assign({{}}, layoutBase.xaxis, {{ title: "Date" }}),
        yaxis: Object.assign({{}}, layoutBase.yaxis, {{ title: "Beta" }}),
        colorway: colorway
      }});
      Plotly.newPlot(id, traces, layout, {{ responsive: true, displayModeBar: true }});
    }});
  </script>
</body>
</html>
"""
    out.write_text(html, encoding="utf-8")
    return out


def write_rolling_betas_plot_pngs(
    rolling_betas: dict[str, pd.DataFrame],
    output_dir: str | Path,
    *,
    prefix: str = "rolling_factor_betas",
    dpi: int = 150,
) -> dict[str, str]:
    """
    Save one PNG per rolling window (e.g. 3y, 5y, 10y): 2×3 subplots, one line per factor beta over time.
    Returns mapping window_label -> filename (not full path).
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    saved: dict[str, str] = {}
    for label, df in (rolling_betas or {}).items():
        if df is None or df.empty:
            continue
        beta_order = [beta for beta in BETA_ROW_ORDER if beta in df.columns]
        beta_order.extend(sorted(beta for beta in df.columns if beta not in beta_order))
        if not beta_order:
            continue
        n_plots = len(beta_order)
        n_cols = int(np.ceil(np.sqrt(n_plots)))
        n_rows = int(np.ceil(n_plots / n_cols))
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(max(12, 4 * n_cols), max(7, 3.2 * n_rows)))
        axes_arr = np.atleast_1d(axes).reshape(-1)
        fig.suptitle(f"Rolling factor betas — {label} window (weekly OLS)", fontsize=12)

        for ax, col in zip(axes_arr, beta_order):
            ax.set_title(get_factor_display_name(col), fontsize=10)
            ax.grid(True, alpha=0.3)
            if col not in df.columns:
                ax.text(0.5, 0.5, "n/a", ha="center", va="center", transform=ax.transAxes)
                continue
            s = pd.to_numeric(df[col], errors="coerce").dropna()
            if s.empty:
                ax.text(0.5, 0.5, "no data", ha="center", va="center", transform=ax.transAxes)
                continue
            ax.plot(s.index, s.values, color="C0", linewidth=0.9)
            ax.tick_params(axis="x", rotation=25, labelsize=7)
            ax.set_ylabel("β", fontsize=8)

        for ax in axes_arr[n_plots:]:
            ax.axis("off")

        plt.tight_layout()
        fname = f"{prefix}_{label}.png"
        path = out_dir / fname
        fig.savefig(path, dpi=int(dpi), bbox_inches="tight")
        plt.close(fig)
        saved[str(label)] = fname

    return saved
