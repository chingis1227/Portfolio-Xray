"""
Shared data loading and caching: daily → FX → resampled levels → returns, rf, benchmark, cash.

``monthly_prices`` / ``monthly_returns`` / ``rf_monthly`` names are historical: when
``returns_frequency`` is weekly or daily, these panels use that index cadence.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.cache import (
    CACHE_DIR,
    compute_asset_metadata_fingerprint,
    compute_daily_cache_key,
    compute_monthly_cache_key,
    get_daily_cache_path,
    get_monthly_cache_path,
    cache_exists,
    load_cache_meta,
    save_cache_meta,
    save_daily_prices,
    save_monthly_data,
    load_daily_prices,
    load_monthly_data,
    get_last_completed_month,
    get_current_date,
)
from src.config import get_asset_currency, resolve_cash_and_rf
from src.data_ecb import fetch_estr
from src.data_fred import fetch_fred_series
from src.data_provider import download_all_prices, normalize_market_data_provider
from src.data_yf import infer_currency_from_ticker
from src.fx import convert_prices_to_investor_currency
from src.returns_frequency import (
    ReturnsFrequency,
    build_levels_and_returns_from_daily_prices,
    main_metrics_frequency_override_note,
    resolve_returns_frequencies,
    rf_series_annual_pct_to_returns_frequency,
)
from src.real_cash import (
    collect_real_cash_tickers,
    inject_real_cash_return_panels,
    partition_market_data_tickers,
)
from src.utils import logger
from src.windows import get_analysis_end, truncate_to_analysis_end


@dataclass
class MonthlyDataResult:
    """Loaded return panel. Field names are legacy; index follows ``returns_frequency``."""

    monthly_prices: pd.DataFrame
    monthly_returns: pd.DataFrame
    monthly_log_returns: pd.DataFrame
    rf_monthly: pd.Series
    benchmark_returns: pd.Series
    cash_returns: pd.Series
    fx_series_used: dict[str, pd.Series]
    analysis_end: pd.Timestamp
    analysis_end_str: str
    daily_cache_key: str
    monthly_cache_key: str
    returns_frequency: ReturnsFrequency = "monthly"
    configured_returns_frequency: ReturnsFrequency = "monthly"
    risk_free_metadata: dict[str, Any] | None = None
    risk_free_warnings: tuple[str, ...] = ()


RISK_FREE_FALLBACK_REASON_FRED_TIMEOUT_CACHED_RF = "fred_timeout_cached_rf"
RISK_FREE_FALLBACK_WARNING_CODE = (
    f"risk_free_fallback_used:{RISK_FREE_FALLBACK_REASON_FRED_TIMEOUT_CACHED_RF}"
)


def _exception_looks_like_timeout(exc: BaseException) -> bool:
    """Return True when an exception chain looks like a network timeout."""
    stack: list[BaseException] = [exc]
    seen: set[int] = set()
    while stack:
        cur = stack.pop()
        ident = id(cur)
        if ident in seen:
            continue
        seen.add(ident)
        if isinstance(cur, TimeoutError):
            return True
        msg = str(cur).lower()
        if "timed out" in msg or "timeout" in msg:
            return True
        cause = getattr(cur, "__cause__", None)
        context = getattr(cur, "__context__", None)
        if isinstance(cause, BaseException):
            stack.append(cause)
        if isinstance(context, BaseException):
            stack.append(context)
    return False


def _coerce_cache_series_index(series: pd.Series) -> pd.Series:
    """Normalize a cached risk-free series index before approval checks."""
    out = series.copy()
    out.index = pd.to_datetime(out.index).tz_localize(None)
    return out.astype(float).sort_index().dropna()


def _series_bound_str(series: pd.Series, attr: str) -> str | None:
    if series.empty:
        return None
    value = getattr(series.index, attr)()
    return pd.Timestamp(value).strftime("%Y-%m-%d")


def _cache_key_from_path(cache_path: Path) -> str:
    name = cache_path.name
    return name[2:] if name.startswith("v_") else name


def _load_approved_cached_risk_free_series(
    *,
    rf_source: str,
    investor_currency: str,
    returns_frequency: str,
    required_analysis_end: pd.Timestamp | None,
) -> tuple[pd.Series | None, dict[str, Any]]:
    """
    Return an approved cached risk-free series plus provenance metadata.

    A cached series is approved only when its cache metadata matches the requested
    risk-free source, investor currency, and main-metrics return frequency, and
    the cached observations cover the analysis-effective end date. The risk-free
    series is independent from the portfolio ticker list, so matching tickers are
    intentionally not required.
    """
    monthly_root = CACHE_DIR / "monthly"
    searched = {
        "risk_free_cache_search_root": str(monthly_root),
        "risk_free_cache_approval_criteria": {
            "rf_source": rf_source,
            "investor_currency": str(investor_currency).upper(),
            "returns_frequency": str(returns_frequency).strip().lower(),
            "required_analysis_end": (
                pd.Timestamp(required_analysis_end).strftime("%Y-%m-%d")
                if required_analysis_end is not None
                else None
            ),
        },
        "risk_free_cache_candidates_scanned": 0,
        "risk_free_cache_skip_reasons": [],
    }
    if not monthly_root.is_dir():
        searched["risk_free_cache_missing"] = True
        return None, searched

    cache_paths = sorted(
        [p for p in monthly_root.iterdir() if p.is_dir() and p.name.startswith("v_")],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    skip_reasons: list[dict[str, Any]] = []
    requested_currency = str(investor_currency).strip().upper()
    requested_frequency = str(returns_frequency).strip().lower()
    required_end = pd.Timestamp(required_analysis_end).normalize() if required_analysis_end is not None else None

    for cache_path in cache_paths:
        searched["risk_free_cache_candidates_scanned"] += 1
        cache_key = _cache_key_from_path(cache_path)
        try:
            meta = load_cache_meta(cache_path) or {}
        except Exception as exc:
            skip_reasons.append(
                {"cache_key": cache_key, "reason": "metadata_load_failed", "detail": str(exc)}
            )
            continue
        cfg_meta = meta.get("config") if isinstance(meta.get("config"), dict) else {}
        cached_source = str(cfg_meta.get("rf_source") or "")
        cached_currency = str(cfg_meta.get("investor_currency") or "").strip().upper()
        cached_frequency = str(cfg_meta.get("returns_frequency") or "monthly").strip().lower()
        if cached_source != rf_source:
            skip_reasons.append({"cache_key": cache_key, "reason": "rf_source_mismatch"})
            continue
        if cached_currency != requested_currency:
            skip_reasons.append({"cache_key": cache_key, "reason": "investor_currency_mismatch"})
            continue
        if cached_frequency != requested_frequency:
            skip_reasons.append({"cache_key": cache_key, "reason": "returns_frequency_mismatch"})
            continue
        rf_path = cache_path / "rf_monthly.parquet"
        if not rf_path.is_file():
            skip_reasons.append({"cache_key": cache_key, "reason": "rf_monthly_missing"})
            continue
        try:
            rf_frame = pd.read_parquet(rf_path)
            if "rf" not in rf_frame.columns:
                skip_reasons.append({"cache_key": cache_key, "reason": "rf_column_missing"})
                continue
            rf_series = _coerce_cache_series_index(rf_frame["rf"])
        except Exception as exc:
            skip_reasons.append(
                {"cache_key": cache_key, "reason": "rf_monthly_load_failed", "detail": str(exc)}
            )
            continue
        if rf_series.empty:
            skip_reasons.append({"cache_key": cache_key, "reason": "rf_monthly_empty"})
            continue
        cached_end = pd.Timestamp(rf_series.index.max()).normalize()
        if required_end is not None and cached_end < required_end:
            skip_reasons.append(
                {
                    "cache_key": cache_key,
                    "reason": "rf_monthly_does_not_cover_analysis_end",
                    "cached_end": cached_end.strftime("%Y-%m-%d"),
                    "required_analysis_end": required_end.strftime("%Y-%m-%d"),
                }
            )
            continue

        metadata = {
            **searched,
            "risk_free_cache_skip_reasons": skip_reasons[-10:],
            "risk_free_cache_key": cache_key,
            "risk_free_cache_path": str(cache_path),
            "risk_free_cache_created_at": meta.get("created_at"),
            "risk_free_cache_data_month": cfg_meta.get("data_month"),
            "risk_free_cached_observation_start": _series_bound_str(rf_series, "min"),
            "risk_free_cached_observation_end": _series_bound_str(rf_series, "max"),
            "risk_free_cached_observations": int(rf_series.shape[0]),
        }
        return rf_series, metadata

    searched["risk_free_cache_skip_reasons"] = skip_reasons[-10:]
    return None, searched


def _risk_free_fallback_warning(metadata: dict[str, Any]) -> str:
    return (
        "Risk-free FRED source timed out; using approved cached risk-free series "
        f"from cache key {metadata.get('risk_free_cache_key')} "
        f"(cached through {metadata.get('risk_free_cached_observation_end')}). "
        "Run with live FRED available to refresh provenance."
    )


def load_monthly_data_shared(
    tickers: list[str],
    benchmark_base_ticker: str,
    cash_proxy_ticker: str,
    rf_source: str,
    investor_currency: str,
    windows_months: list[int],
    assets_meta: dict[str, dict[str, Any]],
    no_cache: bool = False,
    local_benchmark_map: dict[str, str] | None = None,
    returns_frequency: str | None = None,
    data_provider: str | None = None,
    allow_risk_free_cached_fallback: bool = False,
) -> MonthlyDataResult:
    """
    Load or build prices/returns, rf, benchmark, cash at the main-metrics cadence (monthly).

    ``returns_frequency`` in config may be weekly/daily for disclosure only; the returned
    panel always follows ``MAIN_METRICS_RETURNS_FREQUENCY``.

    Uses daily and panel cache. If local_benchmark_map is provided, its values are included
    in downloaded and converted tickers so Beta_local can use local benchmark returns.
    """
    freq_res = resolve_returns_frequencies(returns_frequency)
    rf_mode = freq_res.main_metrics
    resolved_data_provider = normalize_market_data_provider(data_provider)
    if freq_res.forced_to_monthly:
        logger.warning(main_metrics_frequency_override_note(freq_res))
    local_bench_tickers = list(local_benchmark_map.values()) if local_benchmark_map else []
    panel_tickers = list(
        dict.fromkeys(list(tickers) + [benchmark_base_ticker, cash_proxy_ticker] + local_bench_tickers)
    )
    real_cash_tickers = collect_real_cash_tickers(tickers=panel_tickers)
    all_tickers, _panel_real_cash = partition_market_data_tickers(panel_tickers)
    real_cash_tickers = list(dict.fromkeys(real_cash_tickers + _panel_real_cash))

    currency_by_ticker = {}
    for t in all_tickers:
        currency_by_ticker[t] = get_asset_currency(t, assets_meta, infer_currency_from_ticker(t))
    asset_metadata_fingerprint = compute_asset_metadata_fingerprint(currency_by_ticker)

    max_window = max(windows_months)
    end_date = datetime.now()
    start_date = datetime(end_date.year - (max_window // 12) - 2, end_date.month, 1)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    current_date = get_current_date()
    data_month = get_last_completed_month()
    daily_cache_key = compute_daily_cache_key(
        tickers=all_tickers,
        start_date=start_str,
        end_date=end_str,
        data_date=current_date,
        data_provider=resolved_data_provider,
    )
    daily_cache_path = get_daily_cache_path(daily_cache_key)
    monthly_cache_key = compute_monthly_cache_key(
        tickers=tickers,
        investor_currency=investor_currency,
        benchmark=benchmark_base_ticker,
        cash_proxy=cash_proxy_ticker,
        rf_source=rf_source,
        windows_months=windows_months,
        data_month=data_month,
        asset_metadata_fingerprint=asset_metadata_fingerprint,
        extra_tickers=local_bench_tickers if local_bench_tickers else None,
        returns_frequency=rf_mode,
        data_provider=resolved_data_provider,
    )
    monthly_cache_path = get_monthly_cache_path(monthly_cache_key)

    monthly_data = None
    monthly_cache_meta: dict[str, Any] | None = None
    monthly_cache_config: dict[str, Any] = {}
    risk_free_metadata: dict[str, Any] = {
        "risk_free_fallback_used": False,
        "risk_free_fallback_reason": None,
        "risk_free_source_requested": rf_source,
        "risk_free_source_used": rf_source,
    }
    risk_free_warnings: tuple[str, ...] = ()
    if not no_cache and cache_exists(monthly_cache_path):
        try:
            monthly_cache_meta = load_cache_meta(monthly_cache_path)
        except Exception:
            monthly_cache_meta = None
        monthly_cache_config = (monthly_cache_meta or {}).get("config") or {}
        cached_freq = str(monthly_cache_config.get("returns_frequency", "monthly")).strip().lower()
        if cached_freq == rf_mode:
            logger.info("Return panel cache found; loading...")
            monthly_data = load_monthly_data(monthly_cache_path)

    if monthly_data is not None:
        monthly_prices = monthly_data["monthly_prices"]
        monthly_returns = monthly_data["monthly_returns"]
        monthly_log_returns = monthly_data["monthly_log_returns"]
        monthly_prices, monthly_returns, monthly_log_returns = inject_real_cash_return_panels(
            monthly_prices,
            monthly_returns,
            monthly_log_returns,
            real_cash_tickers,
        )
        rf_monthly = monthly_data["rf_monthly"]
        benchmark_returns = monthly_data["benchmark_returns"]
        cash_returns = monthly_data["cash_returns"]
        fx_series_used = monthly_data["fx_series"] or {}
        if monthly_cache_config.get("risk_free_fallback_used") is True:
            risk_free_metadata = {
                "risk_free_fallback_used": True,
                "risk_free_fallback_reason": monthly_cache_config.get("risk_free_fallback_reason"),
                "risk_free_source_requested": rf_source,
                "risk_free_source_used": monthly_cache_config.get(
                    "risk_free_source_used",
                    "approved_cached_risk_free_series",
                ),
                "risk_free_cache_key": _cache_key_from_path(monthly_cache_path),
                "risk_free_cache_path": str(monthly_cache_path),
                "risk_free_cache_created_at": (monthly_cache_meta or {}).get("created_at"),
                "risk_free_cache_data_month": monthly_cache_config.get("data_month"),
                "risk_free_operator_warning": (
                    "Return panel cache was created with approved cached risk-free fallback; "
                    "run with live FRED available to refresh provenance."
                ),
            }
            risk_free_warnings = (
                RISK_FREE_FALLBACK_WARNING_CODE,
                str(risk_free_metadata["risk_free_operator_warning"]),
            )
            logger.warning(str(risk_free_metadata["risk_free_operator_warning"]))
    else:
        daily = None
        if not no_cache and cache_exists(daily_cache_path):
            logger.info("Daily cache found; loading...")
            daily = load_daily_prices(daily_cache_path)

        if daily is None:
            logger.info("Loading data via market data provider: %s", resolved_data_provider)
            provider_result = download_all_prices(
                all_tickers,
                start_str,
                end_str,
                currency_by_ticker,
                provider=resolved_data_provider,
            )
            daily_raw = provider_result.prices
            daily = {t: df for t, df in daily_raw.items() if not df.empty and "Close" in df.columns}
            if not daily:
                logger.warning(
                    "Daily price cache not saved because market data produced no usable prices."
                )
            else:
                save_cache_meta(
                    daily_cache_path,
                    {
                        "tickers": all_tickers,
                        "start": start_str,
                        "end": end_str,
                        "data_date": current_date,
                        "data_provider": resolved_data_provider,
                        "provider_by_ticker": provider_result.provider_by_ticker,
                    },
                )
                save_daily_prices(daily_cache_path, daily)

        prices_daily = {t: df["Close"] for t, df in daily.items()}
        prices_daily_sub = {t: prices_daily[t] for t in all_tickers if t in prices_daily}
        fx_cache: dict[str, pd.Series | None] = {}
        prices_inv = convert_prices_to_investor_currency(
            prices_daily_sub,
            currency_by_ticker,
            investor_currency,
            start_str,
            end_str,
            fx_cache=fx_cache,
            ffill_fx=True,
        )
        fx_series_used = {k: v for k, v in fx_cache.items() if v is not None}

        monthly_prices, monthly_returns, monthly_log_returns = build_levels_and_returns_from_daily_prices(
            prices_inv,
            freq=rf_mode,
            tickers=all_tickers,
        )
        monthly_prices, monthly_returns, monthly_log_returns = inject_real_cash_return_panels(
            monthly_prices,
            monthly_returns,
            monthly_log_returns,
            real_cash_tickers,
        )

        logger.info(f"Loading risk-free rate from {rf_source}...")
        if rf_source.startswith("FRED:"):
            series_id = rf_source.split(":", 1)[1]
            try:
                rf_annual = fetch_fred_series(series_id, start_str, end_str)
                rf_monthly = rf_series_annual_pct_to_returns_frequency(rf_annual, freq=rf_mode)
            except Exception as exc:
                if (
                    allow_risk_free_cached_fallback
                    and not no_cache
                    and _exception_looks_like_timeout(exc)
                ):
                    preliminary_analysis_end = None
                    if not monthly_prices.empty:
                        preliminary_analysis_end = get_analysis_end(
                            monthly_prices.index,
                            pd.Timestamp(datetime.now().date()),
                        )
                    cached_rf, cache_meta = _load_approved_cached_risk_free_series(
                        rf_source=rf_source,
                        investor_currency=investor_currency,
                        returns_frequency=rf_mode,
                        required_analysis_end=preliminary_analysis_end,
                    )
                    if cached_rf is None:
                        raise RuntimeError(
                            f"FRED risk-free fetch timed out for {rf_source}; "
                            "no approved cached risk-free series was found. "
                            "Approval requires matching rf_source, investor_currency, "
                            "returns_frequency, and coverage through the analysis-effective end date."
                        ) from exc
                    rf_monthly = cached_rf
                    warning = _risk_free_fallback_warning(cache_meta)
                    logger.warning(warning)
                    risk_free_metadata = {
                        **cache_meta,
                        "risk_free_fallback_used": True,
                        "risk_free_fallback_reason": RISK_FREE_FALLBACK_REASON_FRED_TIMEOUT_CACHED_RF,
                        "risk_free_source_requested": rf_source,
                        "risk_free_source_used": "approved_cached_risk_free_series",
                        "risk_free_fetch_error_type": type(exc).__name__,
                        "risk_free_fetch_error": str(exc),
                        "risk_free_operator_warning": warning,
                    }
                    risk_free_warnings = (RISK_FREE_FALLBACK_WARNING_CODE, warning)
                else:
                    raise
        elif rf_source.startswith("ECB:") and "€STR" in rf_source:
            rf_annual = fetch_estr(start_str, end_str)
            rf_monthly = rf_series_annual_pct_to_returns_frequency(rf_annual, freq=rf_mode)
        else:
            raise ValueError(f"Unsupported rf_source: {rf_source!r}. Use FRED:DTB3 or ECB:€STR.")

        # Align rf to returns index intersection (forward-fill stale RF stamps)
        if not monthly_returns.empty:
            full_idx = monthly_returns.sort_index().index
            rf_monthly = rf_monthly.reindex(full_idx).ffill()

        benchmark_returns = monthly_returns.get(benchmark_base_ticker)
        if benchmark_returns is None:
            benchmark_returns = pd.Series(dtype=float)
        else:
            benchmark_returns = benchmark_returns.dropna()
        cash_returns = monthly_returns.get(cash_proxy_ticker)
        if cash_returns is None:
            cash_returns = pd.Series(dtype=float)
        else:
            cash_returns = cash_returns.dropna()

        if monthly_prices.empty or monthly_returns.empty:
            logger.warning(
                "Return panel cache not saved because market data produced an empty panel."
            )
        else:
            save_cache_meta(
                monthly_cache_path,
                {
                    "tickers": tickers,
                    "investor_currency": investor_currency,
                    "benchmark": benchmark_base_ticker,
                    "cash_proxy": cash_proxy_ticker,
                    "rf_source": rf_source,
                    "windows_months": windows_months,
                    "data_month": data_month,
                    "asset_metadata_fingerprint": asset_metadata_fingerprint,
                    "asset_currency_by_ticker": currency_by_ticker,
                    "returns_frequency": rf_mode,
                    "data_provider": resolved_data_provider,
                    "risk_free_fallback_used": risk_free_metadata.get("risk_free_fallback_used", False),
                    "risk_free_fallback_reason": risk_free_metadata.get("risk_free_fallback_reason"),
                    "risk_free_source_used": risk_free_metadata.get("risk_free_source_used", rf_source),
                },
            )
            save_monthly_data(
                monthly_cache_path,
                monthly_prices,
                monthly_returns,
                monthly_log_returns,
                rf_monthly,
                benchmark_returns,
                cash_returns,
                fx_series_used,
            )

    today_ts = pd.Timestamp(datetime.now().date())
    analysis_end = get_analysis_end(monthly_prices.index, today_ts)
    analysis_end_str = analysis_end.strftime("%Y-%m-%d")

    return MonthlyDataResult(
        monthly_prices=monthly_prices,
        monthly_returns=monthly_returns,
        monthly_log_returns=monthly_log_returns,
        rf_monthly=rf_monthly,
        benchmark_returns=benchmark_returns,
        cash_returns=cash_returns,
        fx_series_used=fx_series_used,
        analysis_end=analysis_end,
        analysis_end_str=analysis_end_str,
        daily_cache_key=daily_cache_key,
        monthly_cache_key=monthly_cache_key,
        returns_frequency=rf_mode,
        configured_returns_frequency=freq_res.configured,
        risk_free_metadata=risk_free_metadata,
        risk_free_warnings=risk_free_warnings,
    )


def load_daily_asset_returns_shared(
    *,
    tickers: list[str],
    benchmark_base_ticker: str,
    cash_proxy_ticker: str,
    investor_currency: str,
    windows_months: list[int],
    assets_meta: dict[str, dict[str, Any]],
    daily_cache_key: str,
    analysis_end: pd.Timestamp,
    no_cache: bool = False,
    local_benchmark_map: dict[str, str] | None = None,
    data_provider: str | None = None,
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Daily simple returns in investor currency for portfolio tickers and cash proxy.

    Uses the same daily price cache as ``load_monthly_data_shared``. Rows are truncated to
    ``analysis_end`` for analysis-effective tail-risk panels.
    """
    local_bench_tickers = list(local_benchmark_map.values()) if local_benchmark_map else []
    resolved_data_provider = normalize_market_data_provider(data_provider)
    panel_tickers = list(
        dict.fromkeys(list(tickers) + [benchmark_base_ticker, cash_proxy_ticker] + local_bench_tickers)
    )
    real_cash_tickers = collect_real_cash_tickers(tickers=panel_tickers)
    all_tickers, _panel_real_cash = partition_market_data_tickers(panel_tickers)
    real_cash_tickers = list(dict.fromkeys(real_cash_tickers + _panel_real_cash))
    currency_by_ticker = {}
    for t in all_tickers:
        currency_by_ticker[t] = get_asset_currency(t, assets_meta, infer_currency_from_ticker(t))

    max_window = max(windows_months)
    end_date = datetime.now()
    start_date = datetime(end_date.year - (max_window // 12) - 2, end_date.month, 1)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    daily_cache_path = get_daily_cache_path(daily_cache_key)
    daily = None
    if not no_cache and cache_exists(daily_cache_path):
        logger.info("Daily cache found for tail-risk panel; loading...")
        daily = load_daily_prices(daily_cache_path)

    if daily is None:
        logger.info("Loading daily prices for tail-risk panel via market data provider: %s", resolved_data_provider)
        provider_result = download_all_prices(
            all_tickers,
            start_str,
            end_str,
            currency_by_ticker,
            provider=resolved_data_provider,
        )
        daily_raw = provider_result.prices
        daily = {t: df for t, df in daily_raw.items() if not df.empty and "Close" in df.columns}
        save_cache_meta(
            daily_cache_path,
            {
                "tickers": all_tickers,
                "start": start_str,
                "end": end_str,
                "data_date": get_current_date(),
                "data_provider": resolved_data_provider,
                "provider_by_ticker": provider_result.provider_by_ticker,
            },
        )
        save_daily_prices(daily_cache_path, daily)

    prices_daily = {t: df["Close"] for t, df in daily.items()}
    prices_daily_sub = {t: prices_daily[t] for t in all_tickers if t in prices_daily}
    fx_cache: dict[str, pd.Series | None] = {}
    prices_inv = convert_prices_to_investor_currency(
        prices_daily_sub,
        currency_by_ticker,
        investor_currency,
        start_str,
        end_str,
        fx_cache=fx_cache,
        ffill_fx=True,
    )
    _, daily_returns, daily_log = build_levels_and_returns_from_daily_prices(
        prices_inv,
        freq="daily",
        tickers=all_tickers,
    )
    _, daily_returns, _ = inject_real_cash_return_panels(
        pd.DataFrame(),
        daily_returns,
        daily_log,
        real_cash_tickers,
    )
    daily_returns = truncate_to_analysis_end(daily_returns, analysis_end)
    cash_col = cash_proxy_ticker if cash_proxy_ticker in daily_returns.columns else None
    if cash_col is not None:
        cash_returns_daily = daily_returns[cash_col].dropna()
    else:
        cash_returns_daily = pd.Series(0.0, index=daily_returns.index)
    asset_cols = [t for t in tickers if t in daily_returns.columns]
    return daily_returns[asset_cols].copy(), cash_returns_daily
