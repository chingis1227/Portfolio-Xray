"""
Returns frequency: monthly (default), weekly (W-FRI), daily (trading days).

Annualization uses periods_per_year: 12 / 52 / 252. Daily uses 252 trading days
per metrics convention (see metrics_daily.TRADING_DAYS_PER_YEAR).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Literal, TypedDict

import pandas as pd

ReturnsFrequency = Literal["monthly", "weekly", "daily"]

# Canonical cadence for portfolio metrics, covariance, RC_vol, optimizer inputs, and backtest.
MAIN_METRICS_RETURNS_FREQUENCY: ReturnsFrequency = "monthly"

# Production factor / stress regression cadence (Phase 2 may generalize).
FACTOR_STRESS_FREQUENCY_DEFAULT: ReturnsFrequency = "weekly"
# Macro regime classifier v1 is month-based labels.
MACRO_REGIME_FREQUENCY_DEFAULT: ReturnsFrequency = "monthly"


class FrequencyDisclosure(TypedDict, total=False):
    optimization_frequency: ReturnsFrequency
    returns_frequency: ReturnsFrequency
    configured_returns_frequency: ReturnsFrequency
    main_metrics_returns_frequency: ReturnsFrequency
    main_metrics_frequency_forced: bool
    factor_stress_frequency: ReturnsFrequency
    macro_regime_frequency: ReturnsFrequency
    frequency_mismatch_warning: bool
    macro_regime_frequency_notes: str


@dataclass(frozen=True)
class ReturnsFrequencyResolution:
    """Configured cadence vs enforced main-metrics cadence."""

    configured: ReturnsFrequency
    main_metrics: ReturnsFrequency
    forced_to_monthly: bool


def resolve_returns_frequencies(raw: str | None) -> ReturnsFrequencyResolution:
    """
    Map config ``returns_frequency`` to the effective main-metrics cadence.

    Non-monthly config values are retained for disclosure only; main portfolio
    metrics, covariance, RC_vol, correlation, optimizer inputs, and backtest always
    use ``MAIN_METRICS_RETURNS_FREQUENCY`` (monthly per metrics_specification.md).
    """
    configured = normalize_returns_frequency(raw)
    main = MAIN_METRICS_RETURNS_FREQUENCY
    return ReturnsFrequencyResolution(
        configured=configured,
        main_metrics=main,
        forced_to_monthly=configured != main,
    )


def main_metrics_frequency_override_note(resolution: ReturnsFrequencyResolution) -> str:
    if not resolution.forced_to_monthly:
        return ""
    return (
        f"Config returns_frequency={resolution.configured} does not drive main portfolio "
        f"metrics, covariance, RC_vol, correlation, optimizer inputs, or backtest; "
        f"main_metrics_returns_frequency={resolution.main_metrics} per metrics_specification.md. "
        "Regime factor analytics and other explicitly daily paths may still load daily series."
    )


def normalize_returns_frequency(raw: str | None) -> ReturnsFrequency:
    if raw is None:
        return "monthly"
    s = str(raw).strip().lower()
    if s in ("monthly", "weekly", "daily"):
        return s  # type: ignore[return-value]
    raise ValueError(f"returns_frequency must be monthly|weekly|daily, got {raw!r}")


def periods_per_year(freq: ReturnsFrequency) -> int:
    if freq == "monthly":
        return 12
    if freq == "weekly":
        return 52
    return 252


def annualize_sigma_per_period(sigma_period: float, freq: ReturnsFrequency) -> float:
    k = periods_per_year(freq)
    return float(sigma_period) * math.sqrt(float(k))


def per_period_eff_from_annual_simple(r_a: float, freq: ReturnsFrequency) -> float:
    """
    Convert annualized simple rate r_a (e.g. 0.05 for 5%) to per-period compounding rate:
        (1 + r_a)^(1/k) - 1, k = periods_per_year(freq).
    """
    k = float(periods_per_year(freq))
    return float((1.0 + float(r_a)) ** (1.0 / k) - 1.0)


def rf_series_annual_pct_to_returns_frequency(
    rf_annual_percent: pd.Series,
    *,
    freq: ReturnsFrequency,
) -> pd.Series:
    """
    From FRED-style annual percent (e.g. 5.0) at irregular/daily stamps, produce
    effective per-period risk-free aligned to freq:
      - monthly: last available annual % in calendar month → (1+r/100)^(1/12)-1
      - weekly: last available in week ending Friday → (1+r/100)^(1/52)-1
      - daily: per trading day observation → (1+r/100)^(1/252)-1
    """
    s = rf_annual_percent.astype(float).sort_index()
    s.index = pd.to_datetime(s.index).tz_localize(None)
    s = s.ffill()
    k = float(periods_per_year(freq))
    if freq == "monthly":
        from src.pandas_compat import MONTH_END_FREQ

        tail = s.resample(MONTH_END_FREQ).last().dropna()
    elif freq == "weekly":
        tail = s.resample("W-FRI").last().dropna()
    else:
        tail = s.dropna()
    eff = (1.0 + tail / 100.0) ** (1.0 / k) - 1.0
    return eff


def build_levels_and_returns_from_daily_prices(
    prices_daily_by_ticker: dict[str, pd.Series],
    *,
    freq: ReturnsFrequency,
    tickers: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Build levels (adjusted close aggregated to freq), simple returns, log returns.
    All series aligned on common index intersection per ticker then concat.
    """
    from src.resample import to_month_end
    from src.returns import log_returns_df, simple_returns_df

    levels_cols: dict[str, pd.Series] = {}
    for t in tickers:
        s = prices_daily_by_ticker.get(t)
        if s is None or s.empty:
            continue
        s = s.sort_index().astype(float)
        s.index = pd.to_datetime(s.index).tz_localize(None)
        if freq == "monthly":
            lev = to_month_end(s)
        elif freq == "weekly":
            lev = s.resample("W-FRI").last()
        else:
            lev = s
        lev = lev.dropna()
        if not lev.empty:
            levels_cols[str(t)] = lev
    if not levels_cols:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    levels = pd.DataFrame(levels_cols).sort_index().dropna(how="all")
    simple_r = simple_returns_df(levels)
    log_r = log_returns_df(levels)
    return levels, simple_r, log_r


def analysis_end_rule_description(freq: ReturnsFrequency) -> str:
    if freq == "monthly":
        return "last_index_timestamp_strictly_before_today_month_end_panel"
    if freq == "weekly":
        return "last_index_timestamp_strictly_before_today_weekly_FRI_panel"
    return "last_index_timestamp_strictly_before_today_daily_panel"


def compute_frequency_disclosure(
    *,
    returns_frequency: ReturnsFrequency,
    optimization_frequency: ReturnsFrequency | None = None,
    configured_returns_frequency: ReturnsFrequency | None = None,
    factor_stress_frequency: ReturnsFrequency,
    macro_regime_frequency: ReturnsFrequency,
    macro_regime_frequency_notes: str | None = None,
) -> dict[str, Any]:
    """
    Machine-readable frequency alignment.

    ``returns_frequency`` is the effective main-metrics cadence (monthly). When
    ``configured_returns_frequency`` differs, ``main_metrics_frequency_forced`` is True
    and notes should explain the override.

    When main metrics are monthly (default), frequency_mismatch_warning is False so legacy
    pipelines (monthly metrics + weekly factor stress + monthly macro regime) stay quiet.
    """
    opt = optimization_frequency or returns_frequency
    configured = configured_returns_frequency or returns_frequency
    forced = configured != returns_frequency
    notes_parts: list[str] = []
    if forced:
        notes_parts.append(main_metrics_frequency_override_note(resolve_returns_frequencies(configured)))
    if macro_regime_frequency_notes:
        notes_parts.append(str(macro_regime_frequency_notes).strip())
    notes = " ".join(p for p in notes_parts if p).strip()
    mismatch = False
    if returns_frequency != "monthly":
        mismatch = (opt != factor_stress_frequency) or (opt != macro_regime_frequency)
    out: dict[str, Any] = {
        "optimization_frequency": opt,
        "returns_frequency": returns_frequency,
        "configured_returns_frequency": configured,
        "main_metrics_returns_frequency": returns_frequency,
        "main_metrics_frequency_forced": bool(forced),
        "factor_stress_frequency": factor_stress_frequency,
        "macro_regime_frequency": macro_regime_frequency,
        "frequency_mismatch_warning": bool(mismatch),
    }
    if notes:
        out["macro_regime_frequency_notes"] = notes
    return out


def frequency_disclosure_from_resolution(
    resolution: ReturnsFrequencyResolution,
    *,
    factor_stress_frequency: ReturnsFrequency,
    macro_regime_frequency: ReturnsFrequency,
    extra_notes: str | None = None,
) -> dict[str, Any]:
    """Build frequency_disclosure for report/stress artifacts from a resolution."""
    return compute_frequency_disclosure(
        returns_frequency=resolution.main_metrics,
        optimization_frequency=resolution.main_metrics,
        configured_returns_frequency=resolution.configured,
        factor_stress_frequency=factor_stress_frequency,
        macro_regime_frequency=macro_regime_frequency,
        macro_regime_frequency_notes=extra_notes,
    )


def minimum_inner_join_span_timedelta() -> pd.Timedelta:
    """~11 months minimum calendar span for optimization inner join (legacy monthly rule)."""
    return pd.Timedelta(days=330)


def count_observations_in_calendar_span(
    index: pd.DatetimeIndex,
    *,
    analysis_end: pd.Timestamp,
    horizon_months: int,
) -> int:
    """Number of timestamps in (analysis_end - horizon_months, analysis_end] (inclusive)."""
    start = analysis_end - pd.DateOffset(months=int(horizon_months))
    mask = (index > start) & (index <= analysis_end)
    return int(mask.sum())


def calendar_window_to_n_periods(window_months: int, freq: ReturnsFrequency) -> int:
    """
    Map calendar horizon in months to an approximate count of bars at `freq`
    (for rolling Sharpe/Sortino on the return index).
    """
    wm = int(window_months)
    if wm < 1:
        return 2
    if freq == "monthly":
        return max(2, wm)
    if freq == "weekly":
        return max(2, int(round(wm * 52.0 / 12.0)))
    return max(2, int(round(wm * 252.0 / 12.0)))
