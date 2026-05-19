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
from src.windows import slice_calendar_window


DDOF = 1


def _align(*series: pd.Series) -> tuple[pd.Series, ...]:
    """Inner join: keep only dates where all series have non-NaN. Return aligned series."""
    if not series:
        return ()
    df = pd.DataFrame({i: s for i, s in enumerate(series)})
    df = df.dropna()
    return tuple(df[i] for i in range(len(series)))


def cagr_from_equity(
    monthly_simple_returns: pd.Series,
    window_months: int,
    *,
    periods_per_year: int = 12,
) -> float:
    """CAGR from equity curve: (Equity_end / Equity_start)^(k / N) - 1, k = periods_per_year."""
    r = monthly_simple_returns.dropna()
    if len(r) < 2:
        return np.nan
    equity = equity_curve_simple(r)
    equity_start = 1.0
    equity_end = equity.iloc[-1]
    n = len(r)
    k = float(periods_per_year)
    return (equity_end / equity_start) ** (k / n) - 1


def vol_annual(monthly_simple_returns: pd.Series, ddof: int = DDOF, *, periods_per_year: int = 12) -> float:
    """Annualized vol = per-period_std * sqrt(periods_per_year), ddof=1."""
    r = monthly_simple_returns.dropna()
    if len(r) < 2:
        return np.nan
    return float(r.std(ddof=ddof) * np.sqrt(float(periods_per_year)))


def sharpe(
    monthly_simple_returns: pd.Series,
    rf_monthly: pd.Series,
    ddof: int = DDOF,
    *,
    periods_per_year: int = 12,
) -> float:
    """Sharpe = (mean(excess)*k) / (std(r)*sqrt(k)), k=periods_per_year. Denominator uses raw returns."""
    r, rf = _align(monthly_simple_returns, rf_monthly)
    if len(r) < 2:
        return np.nan
    excess = r - rf
    k = float(periods_per_year)
    return float((excess.mean() * k) / (r.std(ddof=ddof) * np.sqrt(k)))


def sortino(
    monthly_simple_returns: pd.Series,
    rf_monthly: pd.Series,
    mar: float | None = None,
    ddof: int = DDOF,
    *,
    periods_per_year: int = 12,
) -> float:
    """Sortino relative to MAR. Default MAR = rf per period; downside on same grid as returns."""
    r, rf = _align(monthly_simple_returns, rf_monthly)
    if len(r) < 2:
        return np.nan
    excess = r - rf
    mar_use = rf if mar is None else mar
    downside = np.minimum(0, r - mar_use)
    dd_period = np.sqrt(np.mean(np.asarray(downside) ** 2))
    if dd_period == 0:
        return np.nan
    k = float(periods_per_year)
    dd_annual = dd_period * np.sqrt(k)
    return float((excess.mean() * k) / dd_annual)


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


def downside_beta(
    asset_returns: pd.Series,
    benchmark_returns: pd.Series,
    ddof: int = DDOF,
) -> float:
    """Beta on months where benchmark return < 0 (monthly simple returns, aligned dates)."""
    ra, rb = _align(asset_returns, benchmark_returns)
    mask = rb < 0
    if mask.sum() < 2:
        return np.nan
    return beta_base(ra[mask], rb[mask], ddof=ddof)


def upside_beta(
    asset_returns: pd.Series,
    benchmark_returns: pd.Series,
    ddof: int = DDOF,
) -> float:
    """Beta on months where benchmark return > 0 (monthly simple returns, aligned dates)."""
    ra, rb = _align(asset_returns, benchmark_returns)
    mask = rb > 0
    if mask.sum() < 2:
        return np.nan
    return beta_base(ra[mask], rb[mask], ddof=ddof)


def corr_base(asset_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """Pearson correlation vs base benchmark on aligned monthly simple returns."""
    ra, rb = _align(asset_returns, benchmark_returns)
    if len(ra) < 2:
        return np.nan
    return float(ra.corr(rb))


def treynor(
    monthly_simple_returns: pd.Series,
    rf_monthly: pd.Series,
    benchmark_returns: pd.Series,
    beta: float,
    ddof: int = DDOF,
    *,
    periods_per_year: int = 12,
) -> float:
    """Treynor = (mean(excess)*k) / beta_base, k=periods_per_year."""
    if beta == 0 or np.isnan(beta):
        return np.nan
    r, rf = _align(monthly_simple_returns, rf_monthly)
    if len(r) < 2:
        return np.nan
    excess = r - rf
    return float((excess.mean() * float(periods_per_year)) / beta)


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


def _max_drawdown_peak_trough(equity: pd.Series) -> tuple[float, int | None, int | None]:
    """Return max drawdown plus integer positions for its preceding peak and trough."""

    if equity.empty:
        return np.nan, None, None
    cummax = equity.cummax()
    dd = equity / cummax - 1
    dd_values = dd.to_numpy(dtype=float)
    if len(dd_values) == 0 or np.all(np.isnan(dd_values)):
        return np.nan, None, None
    trough_pos = int(np.nanargmin(dd_values))
    mdd = float(dd_values[trough_pos])
    peak_val = float(cummax.iloc[trough_pos])
    prior_equity = equity.iloc[: trough_pos + 1].to_numpy(dtype=float)
    peak_candidates = np.flatnonzero(np.isclose(prior_equity, peak_val, rtol=1e-12, atol=1e-12))
    peak_pos = int(peak_candidates[-1]) if len(peak_candidates) else trough_pos
    return mdd, peak_pos, trough_pos


def max_drawdown(monthly_simple_returns: pd.Series) -> tuple[float, pd.Timestamp | None]:
    """MDD from monthly equity curve. dd = equity / cummax(equity) - 1. Returns (mdd, peak_date)."""
    r = monthly_simple_returns.dropna()
    if len(r) < 2:
        return np.nan, None
    equity = equity_curve_simple(r)
    mdd, peak_pos, _ = _max_drawdown_peak_trough(equity)
    peak_date = equity.index[peak_pos] if peak_pos is not None else None
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
    Months from the max-drawdown peak to first post-trough month equity >= prior peak.
    If not recovered: ttr=None, recovered=False. If no drawdown occurs: ttr=0, recovered=True.
    """
    r = monthly_simple_returns.dropna()
    if len(r) < 2:
        return None, False
    equity = equity_curve_simple(r)
    mdd, peak_pos, trough_pos = _max_drawdown_peak_trough(equity)
    if peak_pos is None or trough_pos is None or not np.isfinite(mdd):
        return None, False
    if mdd >= 0:
        return 0.0, True

    peak_val = float(equity.iloc[peak_pos])
    after_trough = equity.iloc[trough_pos + 1 :]
    if after_trough.empty:
        return None, False
    recovery_candidates = np.flatnonzero(after_trough.to_numpy(dtype=float) >= peak_val)
    if len(recovery_candidates) == 0:
        return None, False
    recovery_pos = trough_pos + 1 + int(recovery_candidates[0])
    return float(recovery_pos - peak_pos), True


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
    *,
    periods_per_year: int = 12,
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
    r_slice = slice_calendar_window(monthly_simple, analysis_end, window_months)
    lr_slice = slice_calendar_window(monthly_log, analysis_end, window_months)
    rf_slice = slice_calendar_window(rf_monthly, analysis_end, window_months)
    bench_slice = slice_calendar_window(benchmark_returns, analysis_end, window_months)
    r_slice = r_slice.dropna()
    available_months = len(r_slice)
    if periods_per_year == 12 and available_months < window_months:
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
    cagr = cagr_from_equity(r_slice, window_months, periods_per_year=periods_per_year)
    vol = vol_annual(r_slice, periods_per_year=periods_per_year)
    beta = beta_base(r_slice, bench_slice)
    
    # Beta_local: use local benchmark if provided, else same as beta_base
    if local_benchmark_returns is not None:
        local_bench_slice = slice_calendar_window(local_benchmark_returns, analysis_end, window_months)
        beta_loc = beta_base(r_slice, local_bench_slice)
    else:
        beta_loc = beta
    
    ttr_months, recovered = time_to_recovery(r_slice)

    return {
        "ticker": ticker,
        "window_months": window_months,
        "cagr": cagr,
        "vol_annual": vol,
        "sharpe": sharpe(r_slice, rf_slice, periods_per_year=periods_per_year),
        "sortino": sortino(r_slice, rf_slice, mar=mar, periods_per_year=periods_per_year),
        "beta_base": beta,
        "beta_local": beta_loc,
        "treynor": treynor(r_slice, rf_slice, bench_slice, beta, periods_per_year=periods_per_year),
        "skewness": skewness_log(lr_slice),
        "kurtosis": kurtosis_log(lr_slice),
        "max_drawdown": max_drawdown(r_slice)[0],
        "ttr_months": ttr_months if ttr_months is not None else np.nan,
        "recovered": recovered,
    }
