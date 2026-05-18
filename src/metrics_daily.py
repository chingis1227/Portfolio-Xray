"""
Daily-frequency analogs of metrics in metrics_specification.md / metrics_asset.py.

Used for diagnostic regime-sliced analytics. Annualization uses 252 trading days.
Formulas mirror the monthly versions with 12 → 252 and n_months → n_trading_days.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from src.returns import equity_curve_simple

DDOF = 1
TRADING_DAYS_PER_YEAR = 252


def _align(*series: pd.Series) -> tuple[pd.Series, ...]:
    if not series:
        return ()
    df = pd.DataFrame({i: s for i, s in enumerate(series)})
    df = df.dropna()
    return tuple(df[i] for i in range(len(series)))


def cagr_from_equity_daily(daily_simple_returns: pd.Series) -> float:
    """CAGR from daily simple returns: (Equity_end / 1)^(252/N) - 1."""

    r = daily_simple_returns.dropna()
    if len(r) < 2:
        return float("nan")
    equity = equity_curve_simple(r)
    equity_end = float(equity.iloc[-1])
    n = len(r)
    if equity_end <= 0:
        return float("nan")
    return float(equity_end ** (TRADING_DAYS_PER_YEAR / n) - 1.0)


def vol_annual_daily(daily_simple_returns: pd.Series, ddof: int = DDOF) -> float:
    """Annualized vol = std(daily, ddof=1) * sqrt(252)."""

    r = daily_simple_returns.dropna()
    if len(r) < 2:
        return float("nan")
    return float(r.std(ddof=ddof) * np.sqrt(float(TRADING_DAYS_PER_YEAR)))


def sharpe_daily(
    daily_simple_returns: pd.Series,
    rf_daily: pd.Series,
    ddof: int = DDOF,
) -> float:
    """Sharpe: (mean(r - rf) * 252) / (std(r, ddof=1) * sqrt(252)); denominator uses raw r."""

    r, rf = _align(daily_simple_returns, rf_daily)
    if len(r) < 2:
        return float("nan")
    excess = r - rf
    den = r.std(ddof=ddof) * np.sqrt(float(TRADING_DAYS_PER_YEAR))
    if den == 0 or not np.isfinite(den):
        return float("nan")
    return float((excess.mean() * TRADING_DAYS_PER_YEAR) / den)


def sortino_daily(
    daily_simple_returns: pd.Series,
    rf_daily: pd.Series,
    mar_daily: float | pd.Series | None = None,
    ddof: int = DDOF,
) -> float:
    """Sortino: (mean(excess) * 252) / (dd_annual); dd from downside vs MAR (default rf)."""

    r, rf = _align(daily_simple_returns, rf_daily)
    if len(r) < 2:
        return float("nan")
    if isinstance(mar_daily, pd.Series):
        r2, mar_s = _align(r, mar_daily.reindex(r.index))
        rf2 = rf.reindex(r2.index).dropna()
        r2 = r2.reindex(rf2.index).dropna()
        rf2 = rf2.reindex(r2.index)
        mar_s = mar_s.reindex(r2.index)
        if len(r2) < 2:
            return float("nan")
        downside = np.minimum(0.0, (r2 - mar_s).to_numpy(dtype=float))
        excess_vals = (r2 - rf2).to_numpy(dtype=float)
    else:
        mar = rf if mar_daily is None else float(mar_daily)
        downside = np.minimum(0.0, (r - mar).to_numpy(dtype=float))
        excess_vals = (r - rf).to_numpy(dtype=float)
    dd_daily = float(np.sqrt(np.mean(downside**2)))
    if dd_daily == 0:
        return float("nan")
    dd_annual = dd_daily * np.sqrt(float(TRADING_DAYS_PER_YEAR))
    return float((float(np.mean(excess_vals)) * TRADING_DAYS_PER_YEAR) / dd_annual)


def beta_base_daily(
    asset_returns: pd.Series,
    benchmark_returns: pd.Series,
    ddof: int = DDOF,
) -> float:
    """Beta = cov(asset, bench) / var(bench), ddof=1, inner join."""

    ra, rb = _align(asset_returns, benchmark_returns)
    if len(ra) < 2:
        return float("nan")
    var_b = float(rb.var(ddof=ddof))
    if var_b == 0 or not np.isfinite(var_b):
        return float("nan")
    return float(ra.cov(rb) / var_b)


def treynor_daily(
    daily_simple_returns: pd.Series,
    rf_daily: pd.Series,
    beta: float,
) -> float:
    """Treynor = (mean(excess) * 252) / beta."""

    if beta == 0 or not np.isfinite(beta):
        return float("nan")
    r, rf = _align(daily_simple_returns, rf_daily)
    if len(r) < 2:
        return float("nan")
    excess = r - rf
    return float((float(excess.mean()) * TRADING_DAYS_PER_YEAR) / beta)


def skewness_log_daily(daily_log_returns: pd.Series) -> float:
    lr = daily_log_returns.dropna()
    if len(lr) < 3:
        return float("nan")
    return float(stats.skew(lr))


def kurtosis_log_daily(daily_log_returns: pd.Series) -> float:
    lr = daily_log_returns.dropna()
    if len(lr) < 4:
        return float("nan")
    return float(stats.kurtosis(lr))


def max_drawdown_daily(daily_simple_returns: pd.Series) -> tuple[float, pd.Timestamp | None]:
    """MDD from daily equity curve."""

    r = daily_simple_returns.dropna()
    if len(r) < 2:
        return float("nan"), None
    equity = equity_curve_simple(r)
    mdd, peak_pos, _ = _max_drawdown_peak_trough_daily(equity)
    peak_date = equity.index[peak_pos] if peak_pos is not None else None
    return mdd, peak_date


def _max_drawdown_peak_trough_daily(equity: pd.Series) -> tuple[float, int | None, int | None]:
    """Return max drawdown plus integer positions for its preceding peak and trough."""

    if equity.empty:
        return float("nan"), None, None
    cummax = equity.cummax()
    dd = equity / cummax - 1
    dd_values = dd.to_numpy(dtype=float)
    if len(dd_values) == 0 or np.all(np.isnan(dd_values)):
        return float("nan"), None, None
    trough_pos = int(np.nanargmin(dd_values))
    mdd = float(dd_values[trough_pos])
    peak_val = float(cummax.iloc[trough_pos])
    prior_equity = equity.iloc[: trough_pos + 1].to_numpy(dtype=float)
    peak_candidates = np.flatnonzero(np.isclose(prior_equity, peak_val, rtol=1e-12, atol=1e-12))
    peak_pos = int(peak_candidates[-1]) if len(peak_candidates) else trough_pos
    return mdd, peak_pos, trough_pos


def time_to_recovery_daily(
    daily_simple_returns: pd.Series,
) -> tuple[float | None, bool, str]:
    """
    Trading days from the max-drawdown peak to first post-trough day equity >= peak level.

    Uses index positions (business-day index expected).
    """

    r = daily_simple_returns.dropna()
    if len(r) < 2:
        return None, False, "trading_days"
    equity = equity_curve_simple(r)
    mdd, peak_pos, trough_pos = _max_drawdown_peak_trough_daily(equity)
    if peak_pos is None or trough_pos is None or not np.isfinite(mdd):
        return None, False, "trading_days"
    if mdd >= 0:
        return 0.0, True, "trading_days"

    peak_val = float(equity.iloc[peak_pos])
    after_trough = equity.iloc[trough_pos + 1 :]
    if after_trough.empty:
        return None, False, "trading_days"
    recovery_candidates = np.flatnonzero(after_trough.to_numpy(dtype=float) >= peak_val)
    if len(recovery_candidates) == 0:
        return None, False, "trading_days"
    recovery_pos = trough_pos + 1 + int(recovery_candidates[0])
    ttr = float(recovery_pos - peak_pos)
    return ttr, True, "trading_days"


def log_returns_from_simple_daily(simple_daily: pd.Series) -> pd.Series:
    """lr = ln(1 + r) for small-s compatible log returns from simple returns."""

    r = simple_daily.dropna()
    return pd.Series(np.log1p(r.values), index=r.index)
