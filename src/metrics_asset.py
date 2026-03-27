"""
Per-asset metrics per window: CAGR, Vol, Sharpe, Sortino, Beta, Treynor, Skew, Kurt, MDD, TTR.
All use monthly simple returns and ddof=1 unless stated. Aligned by inner join for excess/beta.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from src.returns import equity_curve_simple
from src.utils import warn_insufficient_data
from src.windows import slice_window


DDOF = 1


def _align(*series: pd.Series) -> tuple[pd.Series, ...]:
    """Inner join: keep only dates where all series have non-NaN. Return aligned series."""
    if not series:
        return ()
    df = pd.DataFrame({i: s for i, s in enumerate(series)})
    df = df.dropna()
    return tuple(df[i] for i in range(len(series)))


def cagr_from_equity(monthly_simple_returns: pd.Series, window_months: int) -> float:
    """CAGR = (Equity_end / Equity_start)^(12 / N_months) - 1, Equity = cumprod(1 + r)."""
    r = monthly_simple_returns.dropna()
    if len(r) < 2:
        return np.nan
    equity = equity_curve_simple(r)
    equity_start = 1.0
    equity_end = equity.iloc[-1]
    n = len(r)
    return (equity_end / equity_start) ** (12 / n) - 1


def vol_annual(monthly_simple_returns: pd.Series, ddof: int = DDOF) -> float:
    """Annualized vol = monthly_std * sqrt(12), ddof=1."""
    r = monthly_simple_returns.dropna()
    if len(r) < 2:
        return np.nan
    return float(r.std(ddof=ddof) * np.sqrt(12))


def sharpe(
    monthly_simple_returns: pd.Series,
    rf_monthly: pd.Series,
    ddof: int = DDOF,
) -> float:
    """Sharpe = (mean(r_simple - rf_monthly)*12) / (std(r_simple, ddof=1)*sqrt(12)). Denominator uses raw returns."""
    r, rf = _align(monthly_simple_returns, rf_monthly)
    if len(r) < 2:
        return np.nan
    excess = r - rf
    return float((excess.mean() * 12) / (r.std(ddof=ddof) * np.sqrt(12)))


def sortino(
    monthly_simple_returns: pd.Series,
    rf_monthly: pd.Series,
    mar: float | None = None,
    ddof: int = DDOF,
) -> float:
    """Sortino relative to MAR. Default MAR_monthly = rf_monthly; override with custom mar (scalar). Downside = min(0, r - MAR)."""
    r, rf = _align(monthly_simple_returns, rf_monthly)
    if len(r) < 2:
        return np.nan
    excess = r - rf
    mar_use = rf if mar is None else mar
    downside = np.minimum(0, r - mar_use)
    dd_monthly = np.sqrt(np.mean(np.asarray(downside) ** 2))
    if dd_monthly == 0:
        return np.nan
    dd_annual = dd_monthly * np.sqrt(12)
    return float((excess.mean() * 12) / dd_annual)


def beta_base(
    asset_returns: pd.Series,
    benchmark_returns: pd.Series,
    ddof: int = DDOF,
) -> float:
    """Beta = cov(r_asset, r_bench) / var(r_bench), same dates, ddof=1."""
    ra, rb = _align(asset_returns, benchmark_returns)
    if len(ra) < 2:
        return np.nan
    cov = ra.cov(rb)
    var_b = rb.var(ddof=ddof)
    if var_b == 0:
        return np.nan
    return float(cov / var_b)


def treynor(
    monthly_simple_returns: pd.Series,
    rf_monthly: pd.Series,
    benchmark_returns: pd.Series,
    beta: float,
    ddof: int = DDOF,
) -> float:
    """Treynor = (mean(excess)*12) / beta_base. beta from same window."""
    if beta == 0 or np.isnan(beta):
        return np.nan
    r, rf = _align(monthly_simple_returns, rf_monthly)
    if len(r) < 2:
        return np.nan
    excess = r - rf
    return float((excess.mean() * 12) / beta)


def skewness_log(monthly_log_returns: pd.Series) -> float:
    """Skewness on monthly log returns (diagnostic)."""
    lr = monthly_log_returns.dropna()
    if len(lr) < 3:
        return np.nan
    return float(stats.skew(lr))


def kurtosis_log(monthly_log_returns: pd.Series) -> float:
    """Kurtosis on monthly log returns (diagnostic)."""
    lr = monthly_log_returns.dropna()
    if len(lr) < 4:
        return np.nan
    return float(stats.kurtosis(lr))


def max_drawdown(monthly_simple_returns: pd.Series) -> tuple[float, pd.Timestamp | None]:
    """MDD from monthly equity curve. dd = equity / cummax(equity) - 1. Returns (mdd, peak_date)."""
    r = monthly_simple_returns.dropna()
    if len(r) < 2:
        return np.nan, None
    equity = equity_curve_simple(r)
    cummax = equity.cummax()
    dd = equity / cummax - 1
    mdd = float(dd.min())
    peak_date = cummax.idxmax() if not dd.empty else None
    return mdd, peak_date


def mandate_max_drawdown_full_history_check(
    monthly_returns: pd.DataFrame,
    final_weights: dict[str, float],
    max_dd_limit_frac: float | None,
) -> dict[str, Any]:
    """
    Mandate gate: portfolio max drawdown on full overlapping monthly history
    (rows where all held assets have returns). Used by run_optimization and run_report.
    """
    out: dict[str, Any] = {
        "pass": None,
        "max_drawdown_realized": None,
        "limit_pct": None,
        "history_start": None,
        "history_end": None,
        "months_used": 0,
    }
    if max_dd_limit_frac is None:
        return out
    cols = [t for t in final_weights if t in monthly_returns.columns and final_weights.get(t, 0) > 0]
    if len(cols) < 1:
        return out
    ret_full = monthly_returns[cols].dropna(how="any")
    if len(ret_full) < 2:
        return out
    w_series = pd.Series({t: float(final_weights[t]) for t in cols})
    port_ret = ret_full.dot(w_series).dropna()
    if len(port_ret) < 2:
        return out
    mdd, _ = max_drawdown(port_ret)
    out["months_used"] = int(len(port_ret))
    out["history_start"] = str(port_ret.index[0])
    out["history_end"] = str(port_ret.index[-1])
    out["limit_pct"] = float(max_dd_limit_frac)
    if mdd is None or mdd != mdd:
        return out
    out["max_drawdown_realized"] = float(mdd)
    out["pass"] = bool(mdd >= -float(max_dd_limit_frac))
    return out


def time_to_recovery(monthly_simple_returns: pd.Series) -> tuple[float | None, bool]:
    """
    Months from peak to first month equity >= prior peak. If not recovered: ttr=NaN, recovered=False.
    """
    r = monthly_simple_returns.dropna()
    if len(r) < 2:
        return None, False
    equity = equity_curve_simple(r)
    cummax = equity.cummax()
    peak_val = cummax.iloc[-1]
    peak_date = equity.index[equity.values == peak_val][-1] if peak_val > 0 else equity.index[0]
    # Find first month after peak where equity >= peak_val
    after_peak = equity.index > peak_date
    if not np.any(after_peak):
        return None, False
    recovered = np.any(equity.loc[after_peak].values >= peak_val)
    if not recovered:
        return None, False
    first_recovery_idx = np.where(equity.loc[after_peak].values >= peak_val)[0][0]
    recovery_date = equity.loc[after_peak].index[first_recovery_idx]
    ttr_months = (recovery_date - peak_date).days / 30.44  # approximate months
    return float(ttr_months), True


def asset_metrics_one_window(
    ticker: str,
    monthly_simple: pd.Series,
    monthly_log: pd.Series,
    rf_monthly: pd.Series,
    benchmark_returns: pd.Series,
    analysis_end: pd.Timestamp,
    window_months: int,
    mar: float | None = None,
    local_benchmark_returns: pd.Series | None = None,
) -> dict[str, float | bool]:
    """
    Compute all asset metrics for one ticker in one window. Returns flat dict.
    
    Args:
        ticker: Asset ticker symbol
        monthly_simple: Monthly simple returns for the asset
        monthly_log: Monthly log returns for the asset
        rf_monthly: Risk-free rate (monthly)
        benchmark_returns: Base benchmark returns for Beta_base (e.g., SPY for USD investor)
        analysis_end: End date of analysis window
        window_months: Window length in months
        mar: Minimum Acceptable Return for Sortino (None => MAR = rf_monthly)
        local_benchmark_returns: Local benchmark returns for Beta_local (e.g., BND for bond assets).
                                 If None, Beta_local = Beta_base.
    """
    r_slice = slice_window(monthly_simple, analysis_end, window_months)
    lr_slice = slice_window(monthly_log, analysis_end, window_months)
    rf_slice = slice_window(rf_monthly, analysis_end, window_months)
    bench_slice = slice_window(benchmark_returns, analysis_end, window_months)
    r_slice = r_slice.dropna()
    available_months = len(r_slice)
    if available_months < window_months:
        warn_insufficient_data(ticker, window_months, available_months)
    if available_months < 2:
        return {
            "ticker": ticker,
            "window_months": window_months,
            "cagr": np.nan,
            "vol_annual": np.nan,
            "sharpe": np.nan,
            "sortino": np.nan,
            "beta_base": np.nan,
            "beta_local": np.nan,
            "treynor": np.nan,
            "skewness": np.nan,
            "kurtosis": np.nan,
            "max_drawdown": np.nan,
            "ttr_months": np.nan,
            "recovered": False,
        }
    cagr = cagr_from_equity(r_slice, window_months)
    vol = vol_annual(r_slice)
    beta = beta_base(r_slice, bench_slice)
    
    # Beta_local: use local benchmark if provided, else same as beta_base
    if local_benchmark_returns is not None:
        local_bench_slice = slice_window(local_benchmark_returns, analysis_end, window_months)
        beta_loc = beta_base(r_slice, local_bench_slice)
    else:
        beta_loc = beta
    
    return {
        "ticker": ticker,
        "window_months": window_months,
        "cagr": cagr,
        "vol_annual": vol,
        "sharpe": sharpe(r_slice, rf_slice),
        "sortino": sortino(r_slice, rf_slice, mar=mar),
        "beta_base": beta,
        "beta_local": beta_loc,
        "treynor": treynor(r_slice, rf_slice, bench_slice, beta),
        "skewness": skewness_log(lr_slice),
        "kurtosis": kurtosis_log(lr_slice),
        "max_drawdown": max_drawdown(r_slice)[0],
        "ttr_months": time_to_recovery(r_slice)[0] or np.nan,
        "recovered": time_to_recovery(r_slice)[1],
    }
