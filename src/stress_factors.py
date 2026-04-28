"""
Stress testing: factor data (FRED + Yahoo) and beta estimation.
Primary stress-report factor betas use weekly returns/changes (see FACTOR_WEEKS_5Y / FACTOR_WEEKS_10Y).
Monthly helpers remain for legacy / diagnostics only.
Factors: equity (S&P/SPY), real rates (DFII10 Δ), inflation (T10YIE Δ), credit (BAMLH0A0HYM2 Δ), USD (DTWEXBGS), commodities (DBC/PDBC).
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
from scipy import stats

from src.data_fred import fetch_fred_series
from src.data_yf import fetch_daily
from src.pandas_compat import MONTH_END_FREQ

# Stress report: weekly regression windows ending at analysis_end (Friday week-ends after inner join)
FACTOR_WEEKS_3Y = 156   # ~3 calendar years (rolling diagnostics)
FACTOR_WEEKS_5Y = 260   # ~5 calendar years
FACTOR_WEEKS_10Y = 520  # ~10 calendar years
FACTOR_DOWNLOAD_BUFFER_WEEKS = 28  # extra history for factor/asset weekly alignment

# Breusch–Godfrey LM: lag orders (weekly residuals; same auxiliary regression as in stress spec §8.2)
FACTOR_REGRESSION_BG_LAGS: tuple[int, ...] = (1, 2, 4)
# HAC / Newey–West: max lag for weekly factor regression residuals (≈ 1 календарный месяц)
FACTOR_REGRESSION_HAC_LAGS: int = 4

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
STRESS_FACTOR_DEFINITIONS: tuple[FactorDefinition, ...] = tuple(spec for spec in FACTOR_DEFINITIONS if spec.stress_participates)
FACTOR_TO_BETA_KEY = {spec.column: spec.beta_key for spec in FACTOR_DEFINITIONS}
BETA_ROW_ORDER: tuple[str, ...] = tuple(spec.beta_key for spec in FACTOR_DEFINITIONS)
BETA_KEY_TO_DISPLAY_NAME = {spec.beta_key: spec.display_name for spec in FACTOR_DEFINITIONS}
FACTOR_COLUMN_ORDER: tuple[str, ...] = tuple(spec.column for spec in FACTOR_DEFINITIONS)


def get_factor_beta_row_order(*, stress_only: bool = False) -> tuple[str, ...]:
    specs = STRESS_FACTOR_DEFINITIONS if stress_only else FACTOR_DEFINITIONS
    return tuple(spec.beta_key for spec in specs)


def get_factor_display_name(beta_key: str) -> str:
    return BETA_KEY_TO_DISPLAY_NAME.get(beta_key, beta_key)


def _build_factor_frame(start: str, end: str, *, monthly: bool) -> pd.DataFrame:
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
        df = df.dropna()
    return df


def build_factor_matrix(
    start: str,
    end: str,
) -> pd.DataFrame:
    """
    Build weekly factor series aligned to common index.
    Columns follow FACTOR_DEFINITIONS and currently include equity, real_rates,
    inflation, credit, usd, commodity, vix, us_growth, and oil.
    Index: week-end dates. All in decimal (returns or changes).
    """
    return _build_factor_frame(start, end, monthly=False)


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
    factor_returns columns follow FACTOR_DEFINITIONS.
    Returns DataFrame: index = asset tickers, columns = beta_* keys from FACTOR_TO_BETA_KEY.
    """
    factor_cols = [c for c in FACTOR_COLUMN_ORDER if c in factor_returns.columns]
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


def _ols_with_inference(
    y: np.ndarray,
    X: np.ndarray,
    *,
    add_const: bool = True,
    alpha: float = 0.05,
) -> dict[str, Any] | None:
    """
    OLS with classical (non-HAC) inference.

    Returns dict with params/se/t/p/ci, R^2, adj R^2, df_resid, n_obs.
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

    adj_r2 = float("nan")
    if np.isfinite(r2) and n > 1 and df_resid > 0:
        adj_r2 = 1.0 - (1.0 - r2) * (n - 1) / df_resid

    return {
        "n_obs": int(n),
        "k": int(k),
        "df_resid": int(df_resid),
        "r2": float(r2),
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
        assessment_ru = "н/д: не удалось классифицировать."
        mv_for_rule = float("inf") if max_vif_is_infinite else float(max_vif_finite)
        cr_for_rule = float(cond_r) if np.isfinite(cond_r) else float("inf")
        if strongest is not None and (np.isfinite(mv_for_rule) or max_vif_is_infinite):
            mr = abs(float(strongest["rho"]))
            if max_vif_is_infinite or mv_for_rule >= 10 or cr_for_rule >= 80 or mr >= 0.95:
                severity = "high"
                assessment_ru = (
                    "Высокая: сильная линейная связь между факторами — отдельные β и p-value "
                    "интерпретировать осторожно даже при высоком R²."
                )
            elif mv_for_rule >= 5 or cr_for_rule >= 30 or mr >= 0.85:
                severity = "moderate"
                assessment_ru = (
                    "Умеренная: заметная коллинеарность; β по отдельным факторам могут быть менее устойчивыми."
                )
            else:
                severity = "low"
                assessment_ru = (
                    "Низкая: типичные VIF и cond(R); коллинеарность не доминирует, но попарные корреляции всё равно учитывать."
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


def portfolio_factor_regression_weekly(
    weights: dict[str, float],
    tickers: list[str],
    analysis_end_str: str,
    window_weeks: int,
    *,
    buffer_weeks: int = FACTOR_DOWNLOAD_BUFFER_WEEKS,
    alpha: float = 0.05,
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
        return {}

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

    # Align and take last wk weeks near analysis_end
    common = asset_weekly.index.intersection(factors.index).sort_values()
    common = common[common <= end_ts + pd.Timedelta(days=6)]
    if len(common) > wk:
        common = common[-wk:]
    if len(common) < 10:
        return {}

    Y = asset_weekly.reindex(common)
    Xdf = factors.reindex(common)
    # Require full factor rows and portfolio return defined
    Xdf = Xdf.dropna()
    Y = Y.reindex(Xdf.index)
    if Xdf.empty or len(Xdf) < 10:
        return {}

    # Portfolio weekly return as weighted sum across available tickers
    w_vec = np.array([float(weights.get(t, 0.0)) for t in Y.columns], dtype=float)
    # NaN returns for unavailable assets are treated as zero contribution.
    # This avoids NaN*0 propagation for zero-weight assets.
    y_port = (np.nan_to_num(Y.values, nan=0.0) * w_vec.reshape(1, -1)).sum(axis=1)

    # Drop NaNs (if any)
    valid = ~(np.isnan(y_port) | np.isnan(Xdf.values).any(axis=1))
    if valid.sum() < 10:
        return {}

    y_valid = y_port[valid].astype(float)
    X_valid = Xdf.values[valid].astype(float)
    inf = _ols_with_inference(y_valid, X_valid, add_const=True, alpha=alpha)
    if not inf:
        return {}

    factor_cols = list(Xdf.columns)
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
        "window_weeks": int(wk),
        "n_obs": int(inf["n_obs"]),
        "r2": float(inf["r2"]),
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


def factor_oos_beta_shock_explainability(
    *,
    weights: dict[str, float],
    tickers: list[str],
    historical_results: list[dict[str, Any]],
    factor_betas_5y: dict[str, float] | None,
    factor_betas_10y: dict[str, float] | None,
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
    b5 = factor_betas_5y or {}
    b10 = factor_betas_10y or {}
    if not historical_results:
        out["error"] = "historical_results_empty"
        return out

    def _model_pnl(beta_map: dict[str, float], shock: pd.Series) -> tuple[float, dict[str, float]]:
        total = 0.0
        contrib: dict[str, float] = {}
        for fac_col, shock_v in shock.items():
            bkey = FACTOR_TO_BETA_KEY.get(str(fac_col))
            if not bkey:
                continue
            c = float(beta_map.get(bkey, 0.0)) * float(shock_v)
            contrib[bkey] = c
            total += c
        return float(total), contrib

    abs_err_5: list[float] = []
    abs_err_10: list[float] = []
    abs_err_r3: list[float] = []

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

        out["episodes"].append({
            "episode": ep,
            "episode_start": str(start),
            "episode_end": str(end),
            "n_weeks_factors": int(len(fac)),
            "pnl_real_episode": float(pnl_real) if isinstance(pnl_real, (int, float)) else None,
            "pnl_model_5y": float(pnl5),
            "pnl_model_10y": float(pnl10),
            "pnl_model_roll3y_pre": float(pnl3),
            "abs_error_5y": (abs(pnl5 - float(pnl_real)) if isinstance(pnl_real, (int, float)) else None),
            "abs_error_10y": (abs(pnl10 - float(pnl_real)) if isinstance(pnl_real, (int, float)) else None),
            "abs_error_roll3y_pre": (abs(pnl3 - float(pnl_real)) if isinstance(pnl_real, (int, float)) else None),
            "factor_shock_sum": {k: float(v) for k, v in shock.items()},
            "factor_contrib_5y": {k: float(v) for k, v in c5.items()},
            "factor_contrib_10y": {k: float(v) for k, v in c10.items()},
            "factor_contrib_roll3y_pre": {k: float(v) for k, v in c3.items()},
            "roll3y_pre_analysis_end": pre_end,
            "roll3y_pre_betas": {k: float(v) for k, v in (b3.items() if isinstance(b3, dict) else [])},
        })

    if abs_err_5 and abs_err_10 and abs_err_r3:
        out["summary"] = {
            "mean_abs_error_5y": float(np.mean(abs_err_5)),
            "mean_abs_error_10y": float(np.mean(abs_err_10)),
            "mean_abs_error_roll3y_pre": float(np.mean(abs_err_r3)),
            "n_episodes_with_real_pnl": int(len(abs_err_5)),
        }
    return out


def compute_asset_factor_betas_weekly(
    tickers: list[str],
    analysis_end_str: str,
    window_weeks: int,
    *,
    buffer_weeks: int = FACTOR_DOWNLOAD_BUFFER_WEEKS,
    min_aligned_weeks: int | None = None,
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
    return estimate_betas(Y, X)


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
) -> pd.DataFrame:
    """
    Regress each asset monthly return on monthly factor changes. Same column naming as estimate_betas.
    """
    factor_cols = [c for c in FACTOR_COLUMN_ORDER if c in factor_monthly.columns]
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

    common = asset_weekly.index.intersection(factors.index).sort_values()
    common = common[common <= end_ts + pd.Timedelta(days=6)]
    if len(common) < 30:
        return {}
    y_df = asset_weekly.reindex(common)
    x_df = factors.reindex(common).dropna()
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
