"""
Stress testing: factor data (FRED + Yahoo) and beta estimation.
Per docs/docs/stress_testing_spec.md: 156-week window, weekly returns/changes.
Factors: equity (S&P/SPY), real rates (DFII10 Δ), inflation (T10YIE Δ), credit (BAMLH0A0HYM2 Δ), USD (DTWEXBGS), commodities (DBC/PDBC).
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.data_fred import fetch_fred_series
from src.data_yf import fetch_daily

# 156 weeks ≈ 3 years
FACTOR_WEEKS = 156

# FRED series (fallback when project series not used)
FRED_EQUITY_LEVEL = "SP500"
FRED_REAL_10Y = "DFII10"
FRED_BREAKEVEN_10Y = "T10YIE"
FRED_HY_SPREAD = "BAMLH0A0HYM2"
FRED_DXY = "DTWEXBGS"

# ETF proxies (preferred for equity/commodity when available)
ETF_EQUITY = "SPY"
ETF_COMMODITY = "DBC"


def _week_end(series: pd.Series) -> pd.Series:
    """Resample to week-end (Friday)."""
    return series.resample("W-FRI").last().dropna()


def _weekly_return(prices: pd.Series) -> pd.Series:
    """Weekly simple return from price series (week-end)."""
    w = _week_end(prices)
    return w.pct_change().dropna()


def fetch_equity_weekly(start: str, end: str) -> pd.Series:
    """Weekly equity return: try SPY (Yahoo), else FRED SP500 level -> return."""
    try:
        df = fetch_daily(ETF_EQUITY, start, end)
        if not df.empty and "Close" in df.columns:
            return _weekly_return(df["Close"])
    except Exception:
        pass
    try:
        s = fetch_fred_series(FRED_EQUITY_LEVEL, start, end)
        if not s.empty:
            return _weekly_return(s)
    except Exception:
        pass
    return pd.Series(dtype=float)


def fetch_real_rates_weekly(start: str, end: str) -> pd.Series:
    """Weekly change in 10Y real yield (FRED DFII10). In decimal (e.g. 0.02 = 200 bps)."""
    try:
        s = fetch_fred_series(FRED_REAL_10Y, start, end)
        if s.empty or len(s) < 2:
            return pd.Series(dtype=float)
        w = _week_end(s)
        # FRED is in percent (e.g. 2.0 for 2%); convert to decimal for delta
        w_dec = w / 100.0
        return w_dec.diff().dropna()
    except Exception:
        return pd.Series(dtype=float)


def fetch_inflation_surprise_weekly(start: str, end: str) -> pd.Series:
    """Weekly change in 10Y breakeven (FRED T10YIE) as inflation surprise proxy. Decimal."""
    try:
        s = fetch_fred_series(FRED_BREAKEVEN_10Y, start, end)
        if s.empty or len(s) < 2:
            return pd.Series(dtype=float)
        w = _week_end(s)
        w_dec = w / 100.0
        return w_dec.diff().dropna()
    except Exception:
        return pd.Series(dtype=float)


def fetch_credit_spread_weekly(start: str, end: str) -> pd.Series:
    """Weekly change in HY spread (FRED BAMLH0A0HYM2). In bps -> decimal (e.g. 0.01 = 100 bps)."""
    try:
        s = fetch_fred_series(FRED_HY_SPREAD, start, end)
        if s.empty or len(s) < 2:
            return pd.Series(dtype=float)
        w = _week_end(s)
        # spread in bps; convert to decimal for regression (e.g. 400 bps = 0.04)
        w_dec = w / 10000.0
        return w_dec.diff().dropna()
    except Exception:
        return pd.Series(dtype=float)


def fetch_usd_weekly(start: str, end: str) -> pd.Series:
    """Weekly % change in DXY (FRED DTWEXBGS)."""
    try:
        s = fetch_fred_series(FRED_DXY, start, end)
        if s.empty or len(s) < 2:
            return pd.Series(dtype=float)
        w = _week_end(s)
        return w.pct_change().dropna()
    except Exception:
        return pd.Series(dtype=float)


def fetch_commodity_weekly(start: str, end: str) -> pd.Series:
    """Weekly commodity return (DBC ETF)."""
    try:
        df = fetch_daily(ETF_COMMODITY, start, end)
        if not df.empty and "Close" in df.columns:
            return _weekly_return(df["Close"])
    except Exception:
        pass
    return pd.Series(dtype=float)


def build_factor_matrix(
    start: str,
    end: str,
) -> pd.DataFrame:
    """
    Build weekly factor series aligned to common index.
    Columns: equity, real_rates, inflation, credit, usd, commodity.
    Index: week-end dates. All in decimal (returns or changes).
    """
    eq = fetch_equity_weekly(start, end)
    rr = fetch_real_rates_weekly(start, end)
    inf = fetch_inflation_surprise_weekly(start, end)
    cr = fetch_credit_spread_weekly(start, end)
    usd = fetch_usd_weekly(start, end)
    cmd = fetch_commodity_weekly(start, end)

    df = pd.DataFrame({
        "equity": eq,
        "real_rates": rr,
        "inflation": inf,
        "credit": cr,
        "usd": usd,
        "commodity": cmd,
    })
    df = df.dropna(how="all")
    # Optionally drop columns with very low fill (< 50% non-null) so inner join keeps more dates
    min_fill_ratio = 0.5
    cols_to_drop = [c for c in df.columns if df[c].notna().sum() < len(df) * min_fill_ratio]
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
    # Single explicit inner join: common index (dates) where all factors have values
    df = df.dropna()
    return df


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
) -> pd.DataFrame:
    """
    Regress each asset's weekly return on factor columns. OLS, no constant (or with constant).
    factor_returns columns: equity, real_rates, inflation, credit, usd, commodity.
    Returns DataFrame: index = asset tickers, columns = beta_equity, beta_real_rates, ... beta_commodity.
    """
    factor_cols = [c for c in ["equity", "real_rates", "inflation", "credit", "usd", "commodity"] if c in factor_returns.columns]
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
    # Short names for stress scenario shocks: eq, rr, inf, credit, usd, cmd
    name_map = {
        "equity": "beta_eq",
        "real_rates": "beta_rr",
        "inflation": "beta_inf",
        "credit": "beta_credit",
        "usd": "beta_usd",
        "commodity": "beta_cmd",
    }
    df = pd.DataFrame(betas).T
    df = df.rename(columns={c: name_map.get(c, f"beta_{c}") for c in factor_cols})
    return df


def _month_end(s: pd.Series) -> pd.Series:
    return s.resample("ME").last().dropna()


def build_factor_matrix_monthly(
    start: str,
    end: str,
) -> pd.DataFrame:
    """
    Build monthly factor series (month-end). For use when only monthly returns available.
    Columns: equity, real_rates, inflation, credit, usd, commodity. Decimal.
    """
    try:
        df_eq = fetch_daily(ETF_EQUITY, start, end)
        if not df_eq.empty and "Close" in df_eq.columns:
            eq = _month_end(df_eq["Close"]).pct_change().dropna()
        else:
            eq = pd.Series(dtype=float)
    except Exception:
        eq = pd.Series(dtype=float)
    try:
        rr = fetch_fred_series(FRED_REAL_10Y, start, end)
        if not rr.empty:
            rr = _month_end(rr)
            rr = (rr / 100.0).diff().dropna()
    except Exception:
        rr = pd.Series(dtype=float)
    try:
        inf = fetch_fred_series(FRED_BREAKEVEN_10Y, start, end)
        if not inf.empty:
            inf = _month_end(inf)
            inf = (inf / 100.0).diff().dropna()
    except Exception:
        inf = pd.Series(dtype=float)
    try:
        cr = fetch_fred_series(FRED_HY_SPREAD, start, end)
        if not cr.empty:
            cr = _month_end(cr)
            cr = (cr / 10000.0).diff().dropna()
    except Exception:
        cr = pd.Series(dtype=float)
    try:
        usd = fetch_fred_series(FRED_DXY, start, end)
        if not usd.empty:
            usd = _month_end(usd).pct_change().dropna()
    except Exception:
        usd = pd.Series(dtype=float)
    try:
        df_cmd = fetch_daily(ETF_COMMODITY, start, end)
        if not df_cmd.empty and "Close" in df_cmd.columns:
            cmd = _month_end(df_cmd["Close"]).pct_change().dropna()
        else:
            cmd = pd.Series(dtype=float)
    except Exception:
        cmd = pd.Series(dtype=float)

    df = pd.DataFrame({
        "equity": eq,
        "real_rates": rr,
        "inflation": inf,
        "credit": cr,
        "usd": usd,
        "commodity": cmd,
    })
    return df.dropna(how="all")


def estimate_betas_monthly(
    monthly_asset_returns: pd.DataFrame,
    factor_monthly: pd.DataFrame,
    min_observations: int = 24,
) -> pd.DataFrame:
    """
    Regress each asset monthly return on monthly factor changes. Same column naming as estimate_betas.
    """
    factor_cols = [c for c in ["equity", "real_rates", "inflation", "credit", "usd", "commodity"] if c in factor_monthly.columns]
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
    name_map = {
        "equity": "beta_eq",
        "real_rates": "beta_rr",
        "inflation": "beta_inf",
        "credit": "beta_credit",
        "usd": "beta_usd",
        "commodity": "beta_cmd",
    }
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
    df = df.rename(columns={c: name_map.get(c, f"beta_{c}") for c in factor_cols})
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
