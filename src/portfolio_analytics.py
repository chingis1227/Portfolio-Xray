"""
Portfolio analytics per metrics_specification.md §11 (238-507): rolling Sharpe/Sortino,
drawdown structure, rolling vol, vol-of-vol, VaR/ES, EEE. All on monthly simple returns, ddof=1.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.metrics_asset import sharpe, sortino
from src.returns import equity_curve_simple

DDOF = 1
REPORT_DECIMALS = 3


def rolling_sharpe(
    portfolio_returns: pd.Series,
    rf_monthly: pd.Series,
    window_months: int,
    ddof: int = DDOF,
) -> pd.Series:
    """Rolling Sharpe (window_months). Aligns portfolio and rf by inner join per window."""
    out = []
    for i in range(len(portfolio_returns) - window_months + 1):
        r = portfolio_returns.iloc[i : i + window_months]
        rf = rf_monthly.reindex(r.index).dropna()
        r = r.reindex(rf.index).dropna()
        common = r.index.intersection(rf.index)
        if len(common) < window_months:
            out.append(np.nan)
            continue
        r = r.loc[common]
        rf = rf.loc[common]
        if len(r) < 2:
            out.append(np.nan)
            continue
        val = sharpe(r, rf, ddof=ddof)
        out.append(val)
    if not out:
        return pd.Series(dtype=float)
    idx = portfolio_returns.index[window_months - 1 :]
    return pd.Series(out, index=idx)


def rolling_sortino(
    portfolio_returns: pd.Series,
    rf_monthly: pd.Series,
    window_months: int,
    mar: float | None = None,
    ddof: int = DDOF,
) -> pd.Series:
    """Rolling Sortino (window_months)."""
    out = []
    for i in range(len(portfolio_returns) - window_months + 1):
        r = portfolio_returns.iloc[i : i + window_months]
        rf = rf_monthly.reindex(r.index).dropna()
        r = r.reindex(rf.index).dropna()
        common = r.index.intersection(rf.index)
        if len(common) < window_months:
            out.append(np.nan)
            continue
        r = r.loc[common]
        rf = rf.loc[common]
        if len(r) < 2:
            out.append(np.nan)
            continue
        val = sortino(r, rf, mar=mar, ddof=ddof)
        out.append(val)
    if not out:
        return pd.Series(dtype=float)
    idx = portfolio_returns.index[window_months - 1 :]
    return pd.Series(out, index=idx)


def rolling_vol_annual(monthly_returns: pd.Series, window_months: int, ddof: int = DDOF) -> pd.Series:
    """Rolling volatility (annualized)."""
    r = monthly_returns.rolling(window_months, min_periods=max(2, window_months // 2)).std(ddof=ddof) * np.sqrt(12)
    return r


def drawdown_structure(monthly_simple_returns: pd.Series) -> dict:
    """
    Drawdown structure: depth, length, recovery; time underwater; stats for >5%, >10%, >20%.
    """
    r = monthly_simple_returns.dropna()
    if len(r) < 2:
        return {"drawdowns": [], "summary": {}, "by_threshold": {}}
    equity = equity_curve_simple(r)
    cummax = equity.cummax()
    dd = equity / cummax - 1
    drawdowns = []
    in_dd = False
    start_idx = None
    peak_val = None
    for i in range(len(dd)):
        if dd.iloc[i] < -1e-12 and not in_dd:
            in_dd = True
            start_idx = i
            peak_val = cummax.iloc[i]
        elif in_dd and (dd.iloc[i] >= -1e-12 or i == len(dd) - 1):
            end_idx = i if dd.iloc[i] >= -1e-12 else i
            depth = float(dd.iloc[start_idx : end_idx + 1].min())
            length_months = end_idx - start_idx + 1
            trough_pos = dd.iloc[start_idx : end_idx + 1].values.argmin() + start_idx
            recovery_months = None
            for j in range(trough_pos + 1, len(equity)):
                if equity.iloc[j] >= peak_val:
                    recovery_months = j - trough_pos
                    break
            drawdowns.append({
                "depth": round(depth, REPORT_DECIMALS),
                "length_months": length_months,
                "recovery_months": recovery_months,
            })
            in_dd = False
    recoveries = [d["recovery_months"] for d in drawdowns if d["recovery_months"] is not None]
    summary = {}
    if recoveries:
        summary["recovery_median_months"] = round(float(np.median(recoveries)), REPORT_DECIMALS)
        summary["recovery_p90_months"] = round(float(np.percentile(recoveries, 90)), REPORT_DECIMALS)
    below_peak = (equity < cummax).sum()
    summary["pct_time_underwater"] = round(float(below_peak / len(equity)), REPORT_DECIMALS) if len(equity) else None
    curr = 0
    max_underwater = 0
    for v in (equity < cummax).astype(int).values:
        curr = curr + 1 if v else 0
        max_underwater = max(max_underwater, curr)
    summary["longest_underwater_months"] = int(max_underwater)
    by_threshold = {}
    for thresh in (0.05, 0.10, 0.20):
        dd_deep = [d for d in drawdowns if d["depth"] <= -thresh]
        recoveries_t = [d["recovery_months"] for d in dd_deep if d["recovery_months"] is not None]
        by_threshold[f">{int(thresh*100)}%"] = {
            "count": len(dd_deep),
            "recovery_median": round(float(np.median(recoveries_t)), REPORT_DECIMALS) if recoveries_t else None,
            "recovery_p90": round(float(np.percentile(recoveries_t, 90)), REPORT_DECIMALS) if recoveries_t else None,
        }
    return {"drawdowns": drawdowns, "summary": summary, "by_threshold": by_threshold}


def var_historical(returns: pd.Series, confidence: float) -> float:
    """Historical VaR (percentile of returns)."""
    r = returns.dropna()
    if r.empty:
        return np.nan
    return float(np.percentile(r, (1 - confidence) * 100))


def es_historical(returns: pd.Series, confidence: float) -> float:
    """Historical Expected Shortfall (average of worst tail)."""
    r = returns.dropna()
    if r.empty:
        return np.nan
    var = np.percentile(r, (1 - confidence) * 100)
    tail = r[r <= var]
    if tail.empty:
        return float(var)
    return float(tail.mean())


def effective_equity_exposure(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    worst_pct: float = 0.10,
    ddof: int = DDOF,
) -> float:
    """EEE = crisis beta * 100%. Crisis beta on months where benchmark is in worst worst_pct."""
    common = portfolio_returns.align(benchmark_returns, join="inner")[0].dropna()
    bench = benchmark_returns.reindex(common.index).dropna()
    common = common.reindex(bench.index).dropna()
    if len(common) < 2:
        return np.nan
    threshold = np.percentile(bench, worst_pct * 100)
    crisis = bench <= threshold
    if crisis.sum() < 2:
        return np.nan
    r_p = common[crisis]
    r_b = bench[crisis]
    cov = r_p.cov(r_b)
    var_b = r_b.var(ddof=ddof)
    if var_b == 0:
        return np.nan
    beta_crisis = cov / var_b
    return round(float(beta_crisis * 100), REPORT_DECIMALS)


def rolling_summary(series: pd.Series) -> dict:
    """Summary for a rolling series: last, mean, p10, p90."""
    s = series.dropna()
    if s.empty:
        return {"last": None, "mean": None, "p10": None, "p90": None}
    return {
        "last": round(float(s.iloc[-1]), REPORT_DECIMALS),
        "mean": round(float(s.mean()), REPORT_DECIMALS),
        "p10": round(float(np.percentile(s, 10)), REPORT_DECIMALS),
        "p90": round(float(np.percentile(s, 90)), REPORT_DECIMALS),
    }
