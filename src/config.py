"""
Load config.yml and assets.yml for Portfolio Metrics Standard.

Provides:
- load_config(): Load raw config dict
- load_validated_config(): Load and validate config, return PortfolioConfig object
- resolve_cash_and_rf(): Get cash proxy and risk-free source with currency defaults
- resolve_local_benchmarks(): Get local benchmark mapping for Beta_local
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from src.client_profiles import apply_profile_to_config
from src.config_schema import (
    ConfigValidationError,
    PortfolioConfig,
    validate_config,
)


def _load_yaml(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load main config from config.yml (raw dict, no validation)."""
    if config_path is None:
        config_path = Path(__file__).resolve().parent.parent / "config.yml"
    path = Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(f"Config not found: {path}")
    return _load_yaml(path)


def load_blocks_universe(config_path: str | Path | None = None) -> dict[str, list[str]] | None:
    """
    Load blocks_universe.yml from the same directory as config (or project root if config_path not set).
    Returns { block_name: [ticker, ...] } or None if file does not exist.
    Used to resolve which block each config ticker belongs to; unknown tickers then fail validation.
    """
    if config_path is None:
        base = Path(__file__).resolve().parent.parent
    else:
        base = Path(config_path).resolve().parent
    path = base / "blocks_universe.yml"
    if not path.is_file():
        return None
    data = _load_yaml(path)
    if not data or not isinstance(data, dict):
        return None
    out = {}
    for key, val in data.items():
        if isinstance(val, list):
            out[str(key)] = [str(t) for t in val]
    return out if out else None


def load_validated_config(config_path: str | Path | None = None) -> PortfolioConfig:
    """
    Load config from config.yml and validate it.
    If blocks_universe.yml exists next to config, tickers from config are validated against it:
    each ticker must appear in exactly one block; blocks for this run are derived from the universe.
    If a ticker is not in any block, ConfigValidationError is raised with a clear message.
    If client_profile is set, missing target/risk_budget fields are filled from that profile (midpoints).
    Returns a strongly-typed PortfolioConfig object.
    Raises ConfigValidationError if validation fails.
    """
    raw = load_config(config_path)
    raw = apply_profile_to_config(raw)
    blocks_universe = load_blocks_universe(
        config_path if config_path is not None else Path(__file__).resolve().parent.parent / "config.yml"
    )
    return validate_config(raw, blocks_universe=blocks_universe)


def load_assets_metadata(assets_path: str | Path | None = None) -> dict[str, dict[str, Any]]:
    """Load asset overrides from assets.yml. Returns { ticker: { currency: "EUR", ... } }."""
    if assets_path is None:
        assets_path = Path(__file__).resolve().parent.parent / "assets.yml"
    path = Path(assets_path)
    if not path.is_file():
        return {}
    data = _load_yaml(path)
    return {k: v if isinstance(v, dict) else {} for k, v in data.items()}


def get_asset_currency(ticker: str, metadata: dict[str, dict[str, Any]], fallback: str = "USD") -> str:
    """Return currency for ticker from assets metadata, else fallback."""
    return (metadata.get(ticker) or {}).get("currency") or fallback


# Default cash proxy ticker and rf_source per investor_currency (used when not set in config)
DEFAULT_CASH_AND_RF: dict[str, tuple[str, str]] = {
    "USD": ("BIL", "FRED:DTB3"),
    "EUR": ("PEU", "ECB:€STR"),
}

# Default local benchmarks for Beta_local calculation
# Based on portfolio-metrics.mdc specification
DEFAULT_LOCAL_BENCHMARKS: dict[str, str] = {
    # --- Equity by region ---
    "VOO": "SPY",    # US equity (S&P 500)
    "SPY": "SPY",    # US equity (S&P 500)
    "IVV": "SPY",    # US equity (S&P 500)
    "QQQ": "SPY",    # US equity (Nasdaq-100 -> S&P 500)
    "VTI": "SPY",    # US total market -> S&P 500
    "SCHD": "SPY",   # US dividend -> S&P 500
    "VGK": "VGK",    # Europe equity
    "EWU": "VGK",    # UK equity -> Europe proxy
    "EWG": "VGK",    # Germany equity -> Europe proxy
    "EWJ": "EWJ",    # Japan equity
    "VWO": "VWO",    # EM equity
    "MCHI": "VWO",   # China equity -> EM proxy
    "FXI": "VWO",    # China equity -> EM proxy
    "AAXJ": "AAXJ",  # Asia ex-Japan equity
    "EWC": "EWC",    # Canada equity
    "EWA": "EWA",    # Australia equity
    "VXUS": "VXUS",  # Global ex-US equity
    "VT": "SPY",     # Global equity -> S&P 500 (base)
    "VEA": "VXUS",   # Developed ex-US -> Global ex-US
    "IEFA": "VXUS",  # Developed ex-US -> Global ex-US

    # --- Bonds ---
    "BND": "BND",    # US Aggregate IG
    "AGG": "BND",    # US Aggregate IG -> BND
    "IEF": "IEF",    # US Treasuries 7-10Y
    "TLT": "TLT",    # US Long Treasuries 20+Y
    "SHY": "IEF",    # US Short Treasuries -> 7-10Y proxy
    "TIP": "TIP",    # US TIPS
    "HYG": "HYG",    # US High Yield
    "JNK": "HYG",    # US High Yield -> HYG
    "LQD": "LQD",    # US IG Corporates
    "BIL": "BIL",    # Short T-Bills / Cash proxy

    # --- Commodities / Real Assets ---
    "PDBC": "PDBC",  # Broad commodities
    "DBC": "PDBC",   # Broad commodities -> PDBC
    "DBB": "DBB",    # Industrial metals
    "XLE": "XLE",    # Energy sector

    # --- Gold (special rule: Beta_local = Beta_base = S&P 500) ---
    "GLD": "SPY",
    "IAU": "SPY",
    "SGOL": "SPY",

    # --- Crypto (special rule: Beta_local = Beta_base = S&P 500) ---
    "BTC-USD": "SPY",
    "ETH-USD": "SPY",
    "GBTC": "SPY",
    "ETHE": "SPY",
}


def resolve_cash_and_rf(cfg: dict[str, Any] | PortfolioConfig) -> tuple[str, str]:
    """
    Return (cash_proxy_ticker, rf_source) from config. If either is missing,
    use defaults for investor_currency (USD -> BIL, FRED:DTB3; EUR -> PEU, ECB:€STR).
    Config keys: risk_free_source, cash_proxy_ticker (or legacy rf_source in raw dict).
    
    Accepts either raw config dict or PortfolioConfig object.
    """
    if isinstance(cfg, PortfolioConfig):
        currency = cfg.investor_currency.upper()
        cash = cfg.cash_proxy_ticker
        rf = cfg.rf_source
    else:
        currency = (cfg.get("investor_currency") or "USD").upper()
        cash = cfg.get("cash_proxy_ticker")
        rf = cfg.get("rf_source")
    
    default_cash, default_rf = DEFAULT_CASH_AND_RF.get(currency, ("", ""))
    cash = cash or default_cash
    rf = rf or default_rf
    
    if not cash or not rf:
        raise ConfigValidationError(
            f"No default for investor_currency={currency}. "
            "Set cash_proxy_ticker and risk_free_source (or rf_source) explicitly in config.yml, or use USD/EUR."
        )
    return cash, rf


def get_local_benchmark(
    ticker: str,
    config_override: dict[str, str] | None = None,
    base_benchmark: str = "SPY",
) -> str:
    """
    Return local benchmark for Beta_local calculation.
    
    Priority:
    1. config_override (from config.yml beta_local_mapping / local_benchmark_map)
    2. DEFAULT_LOCAL_BENCHMARKS (built-in dictionary)
    3. base_benchmark fallback (SPY by default)
    
    Special rules (per specification):
    - Gold (GLD, IAU): always SPY (Beta_local = Beta_base)
    - Crypto (BTC-USD, ETH-USD): always SPY (Beta_local = Beta_base)
    """
    if config_override and ticker in config_override:
        return config_override[ticker]
    return DEFAULT_LOCAL_BENCHMARKS.get(ticker, base_benchmark)


def resolve_local_benchmarks(
    tickers: list[str],
    config_override: dict[str, str] | None = None,
    base_benchmark: str = "SPY",
) -> dict[str, str]:
    """
    Return dict { ticker: local_benchmark } for all tickers.
    Uses get_local_benchmark() for each ticker.
    """
    return {
        t: get_local_benchmark(t, config_override, base_benchmark)
        for t in tickers
    }


def get_mar_from_config(cfg: PortfolioConfig) -> float | None:
    """
    Get Minimum Acceptable Return from config for Sortino/downside metrics.
    
    Returns annual MAR rate or None if not specified (will default to rf_monthly).
    """
    return cfg.min_acceptable_return


def get_target_return_from_config(cfg: PortfolioConfig) -> float | None:
    """
    Get target nominal annual return from config for comparison with realized CAGR.
    """
    return cfg.target_nominal_return_annual
