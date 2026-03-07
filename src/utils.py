"""
Shared utilities for Portfolio Metrics Standard.
"""
from __future__ import annotations

import logging
import pandas as pd

logger = logging.getLogger("portfolio_metrics")


def setup_logging(level: int = logging.INFO) -> None:
    """Configure logging for portfolio metrics with console handler."""
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
