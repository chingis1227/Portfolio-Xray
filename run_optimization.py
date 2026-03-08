"""
Run portfolio optimization (risk budget + ProLiquidity) and output weights.
Uses config.yml; client_profile (e.g. Growth) supplies rc_block_targets.
Run from project root: python run_optimization.py [--no-cache] [--write-config]

Output: final weights are written to portfolio_weights.yml. Use --write-config to also write them into config.yml (legacy).
"""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml

from src.cache import (
    compute_daily_cache_key,
    compute_monthly_cache_key,
    get_daily_cache_path,
    get_monthly_cache_path,
    cache_exists,
    save_cache_meta,
    save_daily_prices,
    load_daily_prices,
    save_monthly_data,
    load_monthly_data,
    get_last_completed_month,
    get_current_date,
)
from src.config import (
    load_validated_config,
    load_assets_metadata,
    get_asset_currency,
    resolve_cash_and_rf,
    WEIGHTS_FILENAME,
)
from src.client_profiles import get_profile_defaults
from src.config_schema import ConfigValidationError
from src.data_ecb import fetch_estr
from src.data_fred import (
    fetch_fred_series,
    annual_percent_to_monthly_effective,
    resample_rf_to_month_end,
)
from src.data_yf import download_all, infer_currency_from_ticker
from src.fx import convert_prices_to_investor_currency
from src.optimization import (
    get_risk_portfolio_tickers,
    run_risk_budget_optimization,
    proliquidity,
    portfolio_vol_annual,
)
from src.resample import to_month_end
from src.returns import simple_returns_df, log_returns_df
from src.risk_contrib import cov_matrix_monthly
from src.utils import setup_logging, logger


def get_client_profile_from_config_file() -> str | None:
    """Read client_profile directly from config.yml so we always use the latest value from disk."""
    config_path = Path(__file__).resolve().parent / "config.yml"
    if not config_path.is_file():
        return None
    try:
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        profile = data.get("client_profile")
        return profile.strip() if isinstance(profile, str) and profile else None
    except Exception:
        return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Portfolio optimization — risk budget + ProLiquidity")
    parser.add_argument("--no-cache", action="store_true", help="Ignore cache, download fresh data")
    parser.add_argument("--write-config", action="store_true", help="Write optimized weights to config.yml")
    parser.add_argument("--profile", type=str, default=None, help="Override client_profile (e.g. Growth, conservative)")
    return parser.parse_args()


def load_monthly_returns(cfg, args) -> tuple[pd.DataFrame, str]:
    """Load or build monthly returns; return (monthly_returns_df, analysis_end_str)."""
    investor_currency = cfg.investor_currency
    tickers = cfg.tickers
    benchmark_base_ticker = cfg.benchmark_base_ticker
    windows_months = cfg.windows_months
    cash_proxy_ticker, rf_source = resolve_cash_and_rf(cfg)
    assets_meta = load_assets_metadata()
    all_tickers = list(set(
        tickers + [benchmark_base_ticker, cash_proxy_ticker]
    ))
    currency_by_ticker = {}
    for t in all_tickers:
        currency_by_ticker[t] = get_asset_currency(t, assets_meta, infer_currency_from_ticker(t))

    max_window = max(windows_months)
    end_date = datetime.now()
    start_date = datetime(end_date.year - (max_window // 12) - 2, end_date.month, 1)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    current_date = get_current_date()
    data_month = get_last_completed_month()
    daily_cache_key = compute_daily_cache_key(
        tickers=all_tickers, start_date=start_str, end_date=end_str, data_date=current_date,
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
    )
    monthly_cache_path = get_monthly_cache_path(monthly_cache_key)

    monthly_data = None
    if not args.no_cache and cache_exists(monthly_cache_path):
        logger.info("Загружаю месячный кеш...")
        monthly_data = load_monthly_data(monthly_cache_path)

    if monthly_data is not None:
        monthly_returns = monthly_data["monthly_returns"]
        monthly_prices = monthly_data["monthly_prices"]
    else:
        daily = None
        if not args.no_cache and cache_exists(daily_cache_path):
            daily = load_daily_prices(daily_cache_path)
        if daily is None:
            logger.info("Загружаю данные из Yahoo Finance...")
            daily_raw = download_all(all_tickers, start_str, end_str, currency_by_ticker)
            daily = {t: df for t, df in daily_raw.items() if not df.empty and "Close" in df.columns}
            save_cache_meta(daily_cache_path, {"tickers": all_tickers, "start": start_str, "end": end_str, "data_date": current_date})
            save_daily_prices(daily_cache_path, daily)
        prices_daily = {t: df["Close"] for t, df in daily.items()}
        used_tickers = list(set(tickers + [benchmark_base_ticker, cash_proxy_ticker]))
        prices_daily_sub = {t: prices_daily[t] for t in used_tickers if t in prices_daily}
        prices_inv = convert_prices_to_investor_currency(
            prices_daily_sub, currency_by_ticker, investor_currency,
            start_str, end_str, fx_cache={}, ffill_fx=True,
        )
        monthly_prices = pd.DataFrame({t: to_month_end(s) for t, s in prices_inv.items()})
        monthly_prices = monthly_prices.dropna(how="all")
        monthly_returns = simple_returns_df(monthly_prices)
        if rf_source.startswith("FRED:"):
            series_id = rf_source.split(":", 1)[1]
            rf_annual = fetch_fred_series(series_id, start_str, end_str)
            rf_monthly = annual_percent_to_monthly_effective(rf_annual)
            rf_monthly = resample_rf_to_month_end(rf_monthly)
        elif rf_source.startswith("ECB:") and "€STR" in rf_source:
            rf_annual = fetch_estr(start_str, end_str)
            rf_monthly = annual_percent_to_monthly_effective(rf_annual)
            rf_monthly = resample_rf_to_month_end(rf_monthly)
        else:
            raise ValueError(f"Unsupported rf_source: {rf_source!r}")
        benchmark_returns = monthly_returns.get(benchmark_base_ticker)
        cash_returns = monthly_returns.get(cash_proxy_ticker)
        save_monthly_data(
            monthly_cache_path,
            monthly_prices,
            monthly_returns,
            log_returns_df(monthly_prices),
            rf_monthly,
            benchmark_returns.dropna() if benchmark_returns is not None else pd.Series(dtype=float),
            cash_returns.dropna() if cash_returns is not None else pd.Series(dtype=float),
            {},
        )

    from src.windows import get_analysis_end
    today_ts = pd.Timestamp(datetime.now().date())
    analysis_end = get_analysis_end(monthly_prices.index, today_ts)
    analysis_end_str = analysis_end.strftime("%Y-%m-%d")
    return monthly_returns, analysis_end_str


def main() -> None:
    args = parse_args()
    setup_logging()

    try:
        cfg = load_validated_config()
    except ConfigValidationError as e:
        logger.error(f"Ошибка конфигурации: {e}")
        raise SystemExit(1)

    # Apply profile: from --profile CLI, or from config.yml on disk (so we always see latest client_profile)
    # Приоритет: 1) config.yml на диске, 2) загруженный конфиг, 3) --profile из терминала
    profile_source = (get_client_profile_from_config_file() or cfg.client_profile or args.profile or "").strip()
    profile_display = profile_source or "—"
    if profile_source:
        defaults = get_profile_defaults(profile_source)
        if defaults:
            if defaults.get("target_vol_annual") is not None:
                cfg.target_vol_annual = defaults["target_vol_annual"]
            if defaults.get("rc_block_targets") is not None:
                cfg.rc_block_targets = dict(defaults["rc_block_targets"])
            logger.info("Профиль %s: target_vol=%.2f%%, rc_block_targets=%s", profile_display, (cfg.target_vol_annual or 0) * 100, cfg.rc_block_targets)

    if not cfg.rc_block_targets:
        logger.error(
            "rc_block_targets не заданы. Укажите client_profile (например Growth) в config.yml "
            "или задайте rc_block_targets вручную (Growth, Duration, Inflation; сумма = 1)."
        )
        raise SystemExit(1)

    risk_tickers = get_risk_portfolio_tickers(cfg.blocks)
    if not risk_tickers:
        logger.error("В конфиге нет тикеров в блоках Growth, Duration или Inflation.")
        raise SystemExit(1)

    logger.info("Загрузка данных...")
    monthly_returns, analysis_end_str = load_monthly_returns(cfg, args)
    window_months = cfg.windows_months[0] if cfg.windows_months else 60

    weights_risk, status = run_risk_budget_optimization(
        monthly_returns,
        cfg.blocks,
        cfg.rc_block_targets,
        cfg.growth_core_candidates,
        rc_asset_cap_pct=cfg.rc_asset_cap_pct,
        min_single_security_weight_pct=cfg.min_single_security_weight_pct,
        window_months=window_months,
    )

    if not weights_risk:
        logger.error(f"Оптимизация не удалась: {status}")
        raise SystemExit(1)

    logger.info(f"RiskPortfolio: {status}")

    # Covariance for vol (same window)
    cols = [t for t in weights_risk if t in monthly_returns.columns]
    ret_slice = monthly_returns[cols].dropna(how="all")
    ret_slice = ret_slice.iloc[-window_months:]
    cov_df = cov_matrix_monthly(ret_slice, ddof=1)
    current_vol = portfolio_vol_annual(weights_risk, cov_df)

    # ProLiquidity
    pv = cfg.portfolio_value if cfg.portfolio_value is not None and cfg.portfolio_value > 0 else cfg.initial_investable_amount
    liquidity_amount = cfg.liquidity_need_months * (cfg.monthly_expenses or 0)
    liquidity_floor_pct = max(0.0, min(1.0, liquidity_amount / pv)) if pv > 0 else 0.0

    # Use profile target_vol (Growth = 12%, etc.)
    target_vol = cfg.target_vol_annual if cfg.target_vol_annual is not None and cfg.target_vol_annual > 0 else 0.12
    cash_proxy = cfg.cash_proxy_ticker or "BIL"
    final_weights = proliquidity(
        weights_risk,
        cash_proxy,
        current_vol,
        target_vol,
        liquidity_floor_pct,
        cfg.cash_policy,
    )

    # Ensure all config tickers appear (zero if not in optimization)
    for t in cfg.tickers:
        if t not in final_weights:
            final_weights[t] = 0.0

    # Round for display
    rounded = {t: round(w, 3) for t, w in final_weights.items() if w > 0}
    print("\n" + "=" * 60)
    print("ВЕСА ПОСЛЕ ОПТИМИЗАЦИИ (профиль: %s)" % profile_display)
    print("=" * 60)
    for t in sorted(rounded.keys(), key=lambda x: (-rounded[x], x)):
        print(f"  {t}: {rounded[t]:.3f}")
    print("=" * 60)
    print("Сумма весов: %.3f" % sum(final_weights.values()))
    print("Целевая волатильность: %.2f%%" % (target_vol * 100))
    print("Волатильность RiskPortfolio (оценка): %.2f%%" % (current_vol * 100))
    print("")

    # Always write weights to portfolio_weights.yml (used by run_report when config has no weights)
    weights_path = Path(__file__).resolve().parent / WEIGHTS_FILENAME
    with open(weights_path, "w", encoding="utf-8") as f:
        yaml.dump(rounded, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    print("Веса записаны в %s." % weights_path.name)

    if args.write_config:
        config_path = Path(__file__).resolve().parent / "config.yml"
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        data["weights"] = rounded
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        print("Веса также записаны в config.yml (weights).")


if __name__ == "__main__":
    main()
