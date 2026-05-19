"""
Portfolio analytics per metrics_specification.md §11 (238-507): rolling Sharpe/Sortino,
drawdown structure, rolling vol, vol-of-vol, VaR/ES, EEE.

Rolling metrics and drawdown structure use the main-metrics cadence (monthly by default).
Portfolio tail risk (VaR / ES) uses daily simple returns per metrics_specification.md § VAR AND
EXPECTED SHORTFALL.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.metrics_asset import beta_base, sharpe, sortino
from src.returns import equity_curve_simple
from src.returns_frequency import ReturnsFrequency, calendar_window_to_n_periods, periods_per_year
from src.windows import slice_calendar_window

DDOF = 1
REPORT_DECIMALS = 3

TAIL_RISK_METHOD = "historical"
TAIL_RISK_FREQUENCY = "daily"
TAIL_RISK_MIN_OBS_DAILY = 60
TAIL_RISK_CONFIDENCE_LEVELS = (0.95, 0.99)


def rolling_sharpe(
    portfolio_returns: pd.Series,
    rf_monthly: pd.Series,
    window_months: int,
    ddof: int = DDOF,
    *,
    returns_frequency: ReturnsFrequency = "monthly",
) -> pd.Series:
    """Rolling Sharpe over a calendar horizon of ``window_months`` mapped to bars at ``returns_frequency``."""
    wp = calendar_window_to_n_periods(window_months, returns_frequency)
    k = periods_per_year(returns_frequency)
    out = []
    for i in range(len(portfolio_returns) - wp + 1):
        r = portfolio_returns.iloc[i : i + wp]
        rf = rf_monthly.reindex(r.index).dropna()
        r = r.reindex(rf.index).dropna()
        common = r.index.intersection(rf.index)
        if len(common) < wp:
            out.append(np.nan)
            continue
        r = r.loc[common]
        rf = rf.loc[common]
        if len(r) < 2:
            out.append(np.nan)
            continue
        val = sharpe(r, rf, ddof=ddof, periods_per_year=k)
        out.append(val)
    if not out:
        return pd.Series(dtype=float)
    idx = portfolio_returns.index[wp - 1 :]
    return pd.Series(out, index=idx)


def rolling_sortino(
    portfolio_returns: pd.Series,
    rf_monthly: pd.Series,
    window_months: int,
    mar: float | None = None,
    ddof: int = DDOF,
    *,
    returns_frequency: ReturnsFrequency = "monthly",
) -> pd.Series:
    """Rolling Sortino over a calendar horizon of ``window_months`` at ``returns_frequency``."""
    wp = calendar_window_to_n_periods(window_months, returns_frequency)
    k = periods_per_year(returns_frequency)
    out = []
    for i in range(len(portfolio_returns) - wp + 1):
        r = portfolio_returns.iloc[i : i + wp]
        rf = rf_monthly.reindex(r.index).dropna()
        r = r.reindex(rf.index).dropna()
        common = r.index.intersection(rf.index)
        if len(common) < wp:
            out.append(np.nan)
            continue
        r = r.loc[common]
        rf = rf.loc[common]
        if len(r) < 2:
            out.append(np.nan)
            continue
        val = sortino(r, rf, mar=mar, ddof=ddof, periods_per_year=k)
        out.append(val)
    if not out:
        return pd.Series(dtype=float)
    idx = portfolio_returns.index[wp - 1 :]
    return pd.Series(out, index=idx)


def rolling_vol_annual(
    monthly_returns: pd.Series,
    window_months: int,
    ddof: int = DDOF,
    *,
    returns_frequency: ReturnsFrequency = "monthly",
) -> pd.Series:
    """Rolling volatility (annualized) over ``window_months`` calendar horizon at ``returns_frequency``."""
    wp = calendar_window_to_n_periods(window_months, returns_frequency)
    k = periods_per_year(returns_frequency)
    return monthly_returns.rolling(wp, min_periods=max(2, wp // 2)).std(ddof=ddof) * np.sqrt(float(k))


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


def compute_tail_risk_historical(
    daily_simple_returns: pd.Series,
    *,
    window_months: int,
    window_label: str,
    analysis_end: pd.Timestamp,
    min_obs: int = TAIL_RISK_MIN_OBS_DAILY,
) -> dict[str, Any]:
    """
    Historical VaR / ES on daily simple returns for a calendar window ending at analysis_end.

    Returns a disclosure block with method, frequency, window, n_obs, and 95%/99% levels.
    """
    r = slice_calendar_window(daily_simple_returns, analysis_end, window_months).dropna()
    n_obs = int(len(r))
    ae_str = pd.Timestamp(analysis_end).strftime("%Y-%m-%d")
    out: dict[str, Any] = {
        "method": TAIL_RISK_METHOD,
        "frequency": TAIL_RISK_FREQUENCY,
        "window_months": int(window_months),
        "window_label": str(window_label),
        "analysis_end": ae_str,
        "confidence_levels": list(TAIL_RISK_CONFIDENCE_LEVELS),
        "n_obs": n_obs,
        "metric_available": False,
        "unavailable_reason": None,
        "var_95": None,
        "var_99": None,
        "es_95": None,
        "es_99": None,
    }
    if n_obs < max(2, int(min_obs)):
        out["unavailable_reason"] = f"insufficient_daily_obs_lt_{min_obs}"
        return out
    for conf, suffix in ((0.95, "95"), (0.99, "99")):
        v = var_historical(r, conf)
        e = es_historical(r, conf)
        out[f"var_{suffix}"] = round(v, REPORT_DECIMALS) if np.isfinite(v) else None
        out[f"es_{suffix}"] = round(e, REPORT_DECIMALS) if np.isfinite(e) else None
    if all(out.get(k) is not None for k in ("var_95", "es_95", "var_99", "es_99")):
        out["metric_available"] = True
    else:
        out["unavailable_reason"] = "var_es_undefined"
    return out


def tail_risk_flat_fields(tail_risk: dict[str, Any] | None) -> dict[str, float | None]:
    """Backward-compatible flat var/es keys from a tail_risk block."""
    if not isinstance(tail_risk, dict):
        return {}
    if not tail_risk.get("metric_available"):
        return {
            "var_95": None,
            "var_99": None,
            "es_95": None,
            "es_99": None,
        }
    return {
        "var_95": tail_risk.get("var_95"),
        "var_99": tail_risk.get("var_99"),
        "es_95": tail_risk.get("es_95"),
        "es_99": tail_risk.get("es_99"),
    }


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


def rolling_beta(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    window_months: int,
    ddof: int = DDOF,
    *,
    returns_frequency: ReturnsFrequency = "monthly",
) -> pd.Series:
    """Rolling beta vs base benchmark (calendar window mapped to bars at returns_frequency)."""
    wp = calendar_window_to_n_periods(window_months, returns_frequency)
    bench = benchmark_returns.reindex(portfolio_returns.index)
    out: list[float] = []
    for i in range(len(portfolio_returns) - wp + 1):
        r = portfolio_returns.iloc[i : i + wp]
        b = bench.iloc[i : i + wp]
        val = beta_base(r, b, ddof=ddof)
        out.append(val)
    if not out:
        return pd.Series(dtype=float)
    idx = portfolio_returns.index[wp - 1 :]
    return pd.Series(out, index=idx)


def rolling_correlation(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    window_months: int,
    *,
    returns_frequency: ReturnsFrequency = "monthly",
) -> pd.Series:
    """Rolling Pearson correlation vs base benchmark on aligned simple returns."""
    wp = calendar_window_to_n_periods(window_months, returns_frequency)
    bench = benchmark_returns.reindex(portfolio_returns.index)
    out: list[float] = []
    for i in range(len(portfolio_returns) - wp + 1):
        r = portfolio_returns.iloc[i : i + wp].dropna()
        b = bench.iloc[i : i + wp].reindex(r.index).dropna()
        common = r.index.intersection(b.index)
        if len(common) < 2:
            out.append(np.nan)
            continue
        out.append(float(r.loc[common].corr(b.loc[common])))
    if not out:
        return pd.Series(dtype=float)
    idx = portfolio_returns.index[wp - 1 :]
    return pd.Series(out, index=idx)


def rolling_beta_correlation_block(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    *,
    returns_frequency: ReturnsFrequency = "monthly",
) -> dict[str, dict]:
    """Rolling beta/correlation summaries for 36m and 12m windows (metrics spec beta analysis)."""
    if benchmark_returns is None or benchmark_returns.empty:
        return {}
    block: dict[str, dict] = {}
    for wm, label in ((36, "36m"), (12, "12m")):
        rb = rolling_beta(
            portfolio_returns,
            benchmark_returns,
            wm,
            returns_frequency=returns_frequency,
        )
        rc = rolling_correlation(
            portfolio_returns,
            benchmark_returns,
            wm,
            returns_frequency=returns_frequency,
        )
        if not rb.dropna().empty:
            block[f"rolling_beta_{label}"] = rolling_summary(rb)
        if not rc.dropna().empty:
            block[f"rolling_correlation_{label}"] = rolling_summary(rc)
    return block
