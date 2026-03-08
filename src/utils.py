"""
Shared utilities for Portfolio Metrics Standard.
"""
from __future__ import annotations

import logging
import pandas as pd

logger = logging.getLogger("portfolio_metrics")


def setup_logging(level: int = logging.INFO) -> None:
    """Configure logging for portfolio metrics with console handler. Avoids duplicate handlers on repeated calls."""
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        logger.addHandler(handler)
    logger.setLevel(level)


def warn_insufficient_data(
    ticker: str,
    window_months: int,
    available_months: int,
    metric: str | None = None,
) -> None:
    """Log warning when insufficient data for calculation."""
    window_label = f"{window_months // 12}Y" if window_months >= 12 else f"{window_months}M"
    if metric:
        logger.warning(
            f"{ticker}: недостаточно данных для {metric} ({window_label}): "
            f"доступно {available_months} мес., требуется {window_months}"
        )
    else:
        logger.warning(
            f"{ticker}: недостаточно данных для окна {window_label}: "
            f"доступно {available_months} мес., требуется {window_months}"
        )


def warn_skipped_asset(ticker: str, reason: str) -> None:
    """Log warning when asset is skipped."""
    logger.warning(f"{ticker}: пропущен — {reason}")


def info_data_summary(ticker: str, available_months: int, start_date: str, end_date: str) -> None:
    """Log info about available data range."""
    logger.info(f"{ticker}: {available_months} мес. данных ({start_date} — {end_date})")


def coverage_ratio(
    series: pd.Series,
    analysis_end: pd.Timestamp,
    window_months: int,
) -> float:
    """Fraction of non-NaN observations in the window ending at analysis_end. Returns 0 if window empty."""
    from src.windows import slice_window

    try:
        sl = slice_window(series, analysis_end, window_months)
    except Exception:
        return 0.0
    if len(sl) == 0:
        return 0.0
    return float(sl.notna().sum() / len(sl))


def tickers_meeting_coverage(
    monthly_returns: pd.DataFrame,
    analysis_end: pd.Timestamp,
    window_months: int,
    coverage_threshold: float,
) -> list[str]:
    """Return list of tickers for which coverage (share of non-NaN in window) >= coverage_threshold."""
    eligible = []
    for t in monthly_returns.columns:
        r = monthly_returns[t]
        if coverage_ratio(r, analysis_end, window_months) >= coverage_threshold:
            eligible.append(t)
    return eligible


def ensure_month_end_index(series_or_df: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """Ensure index is DatetimeIndex with month-end (normalize to end-of-month for display)."""
    x = series_or_df
    if not isinstance(x.index, pd.DatetimeIndex):
        return x
    # Already month-end style; just ensure timezone-naive for consistency
    if x.index.tz is not None:
        x = x.copy()
        x.index = x.index.tz_localize(None)
    return x
