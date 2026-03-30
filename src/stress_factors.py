"""
Stress testing: factor data (FRED + Yahoo) and beta estimation.
Primary stress-report factor betas use weekly returns/changes (see FACTOR_WEEKS_5Y / FACTOR_WEEKS_10Y).
Monthly helpers remain for legacy / diagnostics only.
Factors: equity (S&P/SPY), real rates (DFII10 Δ), inflation (T10YIE Δ), credit (BAMLH0A0HYM2 Δ), USD (DTWEXBGS), commodities (DBC/PDBC).
"""
from __future__ import annotations

from typing import Any
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from src.data_fred import fetch_fred_series
from src.data_yf import fetch_daily

# Stress report: weekly regression windows ending at analysis_end (Friday week-ends after inner join)
FACTOR_WEEKS_3Y = 156   # ~3 calendar years (rolling diagnostics)
FACTOR_WEEKS_5Y = 260   # ~5 calendar years
FACTOR_WEEKS_10Y = 520  # ~10 calendar years
FACTOR_DOWNLOAD_BUFFER_WEEKS = 28  # extra history for factor/asset weekly alignment

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
    """Weekly change in HY spread (FRED BAMLH0A0HYM2). Percent -> decimal (e.g. 4.0% -> 0.04)."""
    try:
        s = fetch_fred_series(FRED_HY_SPREAD, start, end)
        if s.empty or len(s) < 2:
            return pd.Series(dtype=float)
        w = _week_end(s)
        # FRED series is in percent points; convert to decimal, then take weekly delta.
        # Example: 4.0 (%) -> 0.04 (decimal spread level).
        w_dec = w / 100.0
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

    inf = _ols_with_inference(y_port[valid], Xdf.values[valid], add_const=True, alpha=alpha)
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

    name_map = {
        "equity": "beta_eq",
        "real_rates": "beta_rr",
        "inflation": "beta_inf",
        "credit": "beta_credit",
        "usd": "beta_usd",
        "commodity": "beta_cmd",
    }
    beta_keys = [name_map.get(c, f"beta_{c}") for c in factor_cols]

    X_valid = Xdf.values[valid].astype(float)
    mc = factor_multicollinearity_diagnostics(X_valid, factor_cols)

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
        "factor_multicollinearity": mc,
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
            # Keep units consistent with weekly pipeline: percent points -> decimal.
            cr = (cr / 100.0).diff().dropna()
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
    name_map = {
        "equity": "beta_eq",
        "real_rates": "beta_rr",
        "inflation": "beta_inf",
        "credit": "beta_credit",
        "usd": "beta_usd",
        "commodity": "beta_cmd",
    }
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
            name_map.get(c, f"beta_{c}"): float(v)
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
    return pd.DataFrame(rows).sort_values(["window", "beta"]).reset_index(drop=True)


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

    beta_list = sorted(beta_names)
    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Rolling Factor Betas</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 16px; }}
    .chart {{ width: 100%; height: 360px; margin-bottom: 24px; }}
  </style>
</head>
<body>
  <h2>Rolling factor betas (portfolio)</h2>
  <p>Windows: {", ".join(sorted(payload.keys())) if payload else "n/a"}</p>
  <div id="charts"></div>
  <script>
    const dataByWindow = {json.dumps(payload, ensure_ascii=False)};
    const betaList = {json.dumps(beta_list, ensure_ascii=False)};
    const windows = Object.keys(dataByWindow).sort();
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
      Plotly.newPlot(id, traces, {{
        title: beta,
        xaxis: {{ title: "Date" }},
        yaxis: {{ title: "Beta" }},
        legend: {{ orientation: "h" }}
      }}, {{responsive: true}});
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

    beta_order = [
        "beta_eq",
        "beta_rr",
        "beta_inf",
        "beta_credit",
        "beta_usd",
        "beta_cmd",
    ]
    short_title = {
        "beta_eq": "Equity",
        "beta_rr": "Real rates",
        "beta_inf": "Inflation",
        "beta_credit": "Credit (HY)",
        "beta_usd": "USD",
        "beta_cmd": "Commodity",
    }

    saved: dict[str, str] = {}
    for label, df in (rolling_betas or {}).items():
        if df is None or df.empty:
            continue
        fig, axes = plt.subplots(2, 3, figsize=(14, 8))
        fig.suptitle(f"Rolling factor betas — {label} window (weekly OLS)", fontsize=12)

        for ax, col in zip(axes.flat, beta_order):
            ax.set_title(short_title.get(col, col), fontsize=10)
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

        plt.tight_layout()
        fname = f"{prefix}_{label}.png"
        path = out_dir / fname
        fig.savefig(path, dpi=int(dpi), bbox_inches="tight")
        plt.close(fig)
        saved[str(label)] = fname

    return saved
