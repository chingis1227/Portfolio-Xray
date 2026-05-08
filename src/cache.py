"""
Cache management for Portfolio Metrics Standard.

Two cache levels:
1. Daily cache — raw daily prices, invalidated daily or when tickers change
2. Monthly cache — monthly prices/returns, invalidated when month changes or config changes

Cache structure:
    cache/
    ├── daily/
    │   └── v_{hash}_{date}/
    │       ├── meta.json
    │       └── prices_daily.parquet
    └── monthly/
        └── v_{hash}_{month}/
            ├── meta.json
            ├── prices_monthly.parquet
            ├── returns_monthly.parquet
            ├── returns_log_monthly.parquet
            ├── rf_monthly.parquet
            └── fx_series.parquet
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.utils import logger

CACHE_DIR = Path("cache")


def _compute_hash(payload: dict[str, Any]) -> str:
    """Compute deterministic hash from dict."""
    raw = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def compute_daily_cache_key(
    tickers: list[str],
    start_date: str,
    end_date: str,
    data_date: str,
) -> str:
    """
    Compute cache key for daily prices.
    Invalidates when: tickers change, date range changes, or new day.
    
    Args:
        tickers: List of tickers to download
        start_date: Start date YYYY-MM-DD
        end_date: End date YYYY-MM-DD
        data_date: Current date YYYY-MM-DD (for daily invalidation)
    """
    payload = {
        "tickers": sorted(tickers),
        "start": start_date,
        "end": end_date,
        "data_date": data_date,
    }
    return _compute_hash(payload)


def compute_monthly_cache_key(
    tickers: list[str],
    investor_currency: str,
    benchmark: str,
    cash_proxy: str,
    rf_source: str,
    windows_months: list[int],
    data_month: str,
    extra_tickers: list[str] | None = None,
    returns_frequency: str = "monthly",
) -> str:
    """
    Compute cache key for monthly data.
    Invalidates when: any config param changes or new month.
    
    Args:
        tickers: Portfolio tickers
        investor_currency: Target currency
        benchmark: Benchmark ticker
        cash_proxy: Cash proxy ticker
        rf_source: Risk-free rate source
        windows_months: Analysis windows
        data_month: Last completed month YYYY-MM
        extra_tickers: Optional (e.g. local benchmark tickers) so cache differs when they change
    """
    all_tickers = sorted(tickers) + sorted(extra_tickers or [])
    payload = {
        "tickers": all_tickers,
        "investor_currency": investor_currency,
        "benchmark": benchmark,
        "cash_proxy": cash_proxy,
        "rf_source": rf_source,
        "windows": sorted(windows_months),
        "data_month": data_month,
        "returns_frequency": str(returns_frequency).strip().lower(),
    }
    return _compute_hash(payload)


def get_daily_cache_path(cache_key: str) -> Path:
    """Return path to daily cache directory."""
    return CACHE_DIR / "daily" / f"v_{cache_key}"


def get_monthly_cache_path(cache_key: str) -> Path:
    """Return path to monthly cache directory."""
    return CACHE_DIR / "monthly" / f"v_{cache_key}"


def cache_exists(cache_path: Path) -> bool:
    """Check if valid cache exists at path."""
    meta_path = cache_path / "meta.json"
    return meta_path.is_file()


def load_cache_meta(cache_path: Path) -> dict[str, Any] | None:
    """Load cache metadata."""
    meta_path = cache_path / "meta.json"
    if not meta_path.is_file():
        return None
    with open(meta_path, encoding="utf-8") as f:
        return json.load(f)


def save_cache_meta(cache_path: Path, config: dict[str, Any]) -> None:
    """Save cache metadata."""
    cache_path.mkdir(parents=True, exist_ok=True)
    meta = {
        "created_at": datetime.now().isoformat(),
        "config": config,
    }
    with open(cache_path / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)


# --- Daily cache operations ---

def save_daily_prices(cache_path: Path, prices: dict[str, pd.DataFrame]) -> None:
    """
    Save daily prices to cache.
    
    Args:
        cache_path: Path to cache directory
        prices: Dict of ticker -> DataFrame with 'Close' column
    """
    cache_path.mkdir(parents=True, exist_ok=True)
    
    all_dfs = []
    for ticker, df in prices.items():
        if df.empty or "Close" not in df.columns:
            continue
        s = df["Close"].copy()
        s.name = ticker
        all_dfs.append(s)
    
    if not all_dfs:
        logger.warning("No daily prices to cache")
        return
    
    combined = pd.concat(all_dfs, axis=1)
    combined.to_parquet(cache_path / "prices_daily.parquet")
    logger.info(f"Сохранён дневной кеш: {len(all_dfs)} тикеров, {len(combined)} дней")


def load_daily_prices(cache_path: Path) -> dict[str, pd.DataFrame] | None:
    """
    Load daily prices from cache.
    
    Returns:
        Dict of ticker -> DataFrame with 'Close' column, or None if not found
    """
    path = cache_path / "prices_daily.parquet"
    if not path.is_file():
        return None
    
    try:
        df = pd.read_parquet(path)
        result = {}
        for col in df.columns:
            ticker_df = df[[col]].copy()
            ticker_df.columns = ["Close"]
            ticker_df = ticker_df.dropna()
            result[col] = ticker_df
        logger.info(f"Загружен дневной кеш: {len(result)} тикеров")
        return result
    except Exception as e:
        logger.warning(f"Ошибка загрузки дневного кеша: {e}")
        return None


# --- Monthly cache operations ---

def save_monthly_data(
    cache_path: Path,
    monthly_prices: pd.DataFrame,
    monthly_returns: pd.DataFrame,
    monthly_log_returns: pd.DataFrame,
    rf_monthly: pd.Series,
    benchmark_returns: pd.Series,
    cash_returns: pd.Series,
    fx_series: dict[str, pd.Series] | None = None,
) -> None:
    """Save all monthly data to cache."""
    cache_path.mkdir(parents=True, exist_ok=True)
    
    monthly_prices.to_parquet(cache_path / "prices_monthly.parquet")
    monthly_returns.to_parquet(cache_path / "returns_monthly.parquet")
    monthly_log_returns.to_parquet(cache_path / "returns_log_monthly.parquet")
    rf_monthly.to_frame("rf").to_parquet(cache_path / "rf_monthly.parquet")
    benchmark_returns.to_frame("benchmark").to_parquet(cache_path / "benchmark_returns.parquet")
    cash_returns.to_frame("cash").to_parquet(cache_path / "cash_returns.parquet")
    
    if fx_series:
        fx_df = pd.DataFrame(fx_series)
        fx_df.to_parquet(cache_path / "fx_series.parquet")
    
    logger.info(f"Сохранён месячный кеш: {len(monthly_prices.columns)} тикеров, {len(monthly_prices)} месяцев")


def load_monthly_data(cache_path: Path) -> dict[str, Any] | None:
    """
    Load all monthly data from cache.
    
    Returns:
        Dict with keys: monthly_prices, monthly_returns, monthly_log_returns,
        rf_monthly, benchmark_returns, cash_returns, fx_series
        Or None if cache invalid/missing
    """
    required_files = [
        "prices_monthly.parquet",
        "returns_monthly.parquet",
        "returns_log_monthly.parquet",
        "rf_monthly.parquet",
        "benchmark_returns.parquet",
        "cash_returns.parquet",
    ]
    
    for f in required_files:
        if not (cache_path / f).is_file():
            logger.debug(f"Месячный кеш неполный: отсутствует {f}")
            return None
    
    try:
        result = {
            "monthly_prices": pd.read_parquet(cache_path / "prices_monthly.parquet"),
            "monthly_returns": pd.read_parquet(cache_path / "returns_monthly.parquet"),
            "monthly_log_returns": pd.read_parquet(cache_path / "returns_log_monthly.parquet"),
            "rf_monthly": pd.read_parquet(cache_path / "rf_monthly.parquet")["rf"],
            "benchmark_returns": pd.read_parquet(cache_path / "benchmark_returns.parquet")["benchmark"],
            "cash_returns": pd.read_parquet(cache_path / "cash_returns.parquet")["cash"],
            "fx_series": None,
        }
        
        fx_path = cache_path / "fx_series.parquet"
        if fx_path.is_file():
            fx_df = pd.read_parquet(fx_path)
            result["fx_series"] = {col: fx_df[col] for col in fx_df.columns}
        
        logger.info(f"Загружен месячный кеш: {len(result['monthly_prices'].columns)} тикеров")
        return result
    except Exception as e:
        logger.warning(f"Ошибка загрузки месячного кеша: {e}")
        return None


# --- Cache management utilities ---

def get_last_completed_month() -> str:
    """
    Return last completed month as YYYY-MM.
    If today is 2026-04-13, returns '2026-03'.
    """
    today = datetime.now()
    if today.month == 1:
        return f"{today.year - 1}-12"
    return f"{today.year}-{today.month - 1:02d}"


def get_current_date() -> str:
    """Return current date as YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")


def cleanup_old_cache(keep_versions: int = 3) -> None:
    """
    Remove old cache versions, keeping only the most recent ones.
    
    Args:
        keep_versions: Number of versions to keep per cache type
    """
    for cache_type in ["daily", "monthly"]:
        type_dir = CACHE_DIR / cache_type
        if not type_dir.is_dir():
            continue
        
        versions = sorted(type_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        
        for old_version in versions[keep_versions:]:
            if old_version.is_dir():
                import shutil
                shutil.rmtree(old_version)
                logger.info(f"Удалён старый кеш: {old_version.name}")


def clear_all_cache() -> None:
    """Remove all cached data."""
    if CACHE_DIR.is_dir():
        import shutil
        shutil.rmtree(CACHE_DIR)
        logger.info("Весь кеш очищен")
