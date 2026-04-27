"""
Load config.yml and assets.yml for Portfolio Metrics Standard.

Provides:
- load_config(): Load raw config dict
- load_validated_config(): Load and validate config, return PortfolioConfig object
- resolve_cash_and_rf(): Get cash proxy and risk-free source with currency defaults
- resolve_local_benchmarks(): Get local benchmark mapping for Beta_local
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

_cfg_log = logging.getLogger(__name__)

from src.client_profiles import apply_profile_to_config, get_profile_defaults

# Keys written back to config.yml when profile is applied (so file stays in sync with client_profile)
_PROFILE_SYNC_KEYS = (
    "target_nominal_return_annual",
    "target_vol_annual",
    "target_max_drawdown_pct",
    "liquidity_floor_pct",
)
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


WEIGHTS_FILENAME = "portfolio_weights.yml"


def _weights_file_path(config_path: str | Path | None) -> Path:
    """Path to portfolio_weights.yml: same directory as config.yml."""
    if config_path is None:
        base = Path(__file__).resolve().parent.parent
    else:
        base = Path(config_path).resolve().parent
    return base / WEIGHTS_FILENAME


def load_weights_file(weights_path: str | Path | None = None, config_path: str | Path | None = None) -> dict[str, float]:
    """
    Load portfolio weights from portfolio_weights.yml.
    Used when config.yml has no weights (weights are produced by optimization).
    Returns { ticker: weight } or {} if file missing or empty.
    """
    if weights_path is not None:
        path = Path(weights_path)
    else:
        path = _weights_file_path(config_path)
    if not path.is_file():
        return {}
    data = _load_yaml(path)
    if not data or not isinstance(data, dict):
        return {}
    out = {}
    for k, v in data.items():
        if isinstance(v, (int, float)) and k and isinstance(k, str):
            out[str(k)] = float(v)
    return out


def _sync_profile_fields_to_config_file(path: Path, merged: dict[str, Any]) -> None:
    """
    Write profile-derived fields back to config.yml so the file matches the selected profile.
    Uses ruamel.yaml to preserve comments and structure.
    """
    try:
        from ruamel.yaml import YAML
    except ImportError:
        return
    path = Path(path)
    if not path.is_file():
        return
    yaml_rt = YAML()
    yaml_rt.preserve_quotes = True
    yaml_rt.width = 4096
    with open(path, encoding="utf-8") as f:
        data = yaml_rt.load(f)
    if data is None:
        return
    # Only update keys that already exist in the file, so a minimal client-facing config stays minimal.
    changed = False
    for key in _PROFILE_SYNC_KEYS:
        if key not in merged or key not in data:
            continue
        val = merged[key]
        if data.get(key) != val:
            data[key] = val
            changed = True
    if changed:
        with open(path, "w", encoding="utf-8") as f:
            yaml_rt.dump(data, f)


def load_validated_config(config_path: str | Path | None = None) -> PortfolioConfig:
    """
    Load config from config.yml and validate it.
    If client_profile is set, target fields are filled from that profile (midpoints)
    and written back to config.yml so the file stays in sync (comments preserved).
    Used by optimization, run_report (policy portfolio), Equal-Weight and Risk-Parity baselines, and comparisons.
    If portfolio_weights.yml is merged, its ticker set must exactly match config tickers or validation fails.
    Returns a strongly-typed PortfolioConfig object.
    Raises ConfigValidationError if validation fails.
    """
    path = (Path(config_path).resolve() if config_path is not None
            else Path(__file__).resolve().parent.parent / "config.yml")
    raw = load_config(path)
    raw = apply_profile_to_config(raw)
    if raw.get("client_profile") and get_profile_defaults(raw["client_profile"]):
        _sync_profile_fields_to_config_file(path, raw)
    # If config has no weights, load from portfolio_weights.yml in output_dir_final (e.g. Main portfolio)
    # but only when ticker universe exactly matches config.yml.
    if not raw.get("weights"):
        output_dir_final = raw.get("output_dir_final") or "Main portfolio"
        weights_path = path.parent / output_dir_final / WEIGHTS_FILENAME
        file_weights = load_weights_file(weights_path=weights_path)
        if file_weights:
            cfg_tickers = [str(t) for t in (raw.get("tickers") or []) if isinstance(t, str)]
            cfg_tickers_set = set(cfg_tickers)
            weights_tickers_set = set(file_weights.keys())
            if cfg_tickers_set != weights_tickers_set:
                missing_in_weights = sorted(cfg_tickers_set - weights_tickers_set)
                stale_in_weights = sorted(weights_tickers_set - cfg_tickers_set)
                raise ConfigValidationError(
                    "portfolio_weights.yml не соответствует текущему config.yml по составу тикеров. "
                    f"config_only={missing_in_weights}; weights_only={stale_in_weights}. "
                    "Обновите/удалите portfolio_weights.yml, либо задайте актуальные weights прямо в config.yml."
                )
            raw["weights"] = file_weights
    portfolio_cfg = validate_config(raw)
    _cfg_log.info("Config source: %s", path)
    _cfg_log.info("Config tickers (%d): %s", len(portfolio_cfg.tickers), portfolio_cfg.tickers)
    return portfolio_cfg


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
        rf = cfg.get("rf_source") or cfg.get("risk_free_source")
    
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


def apply_profile_override(cfg: PortfolioConfig, profile_id: str) -> None:
    """
    Apply profile defaults to an already-loaded PortfolioConfig (e.g. from --profile CLI).
    Single source of truth: do not re-read config file. Mutates cfg in place.
    """
    defaults = get_profile_defaults(profile_id)
    if not defaults:
        return
    if "target_nominal_return_annual" in defaults:
        cfg.target_nominal_return_annual = defaults["target_nominal_return_annual"]
    if "target_vol_annual" in defaults:
        cfg.target_vol_annual = defaults["target_vol_annual"]
    if "target_max_drawdown_pct" in defaults:
        cfg.target_max_drawdown_pct = defaults["target_max_drawdown_pct"]
    if "liquidity_floor_pct" in defaults:
        cfg.liquidity_floor_pct = defaults["liquidity_floor_pct"]
    if cfg.min_single_security_weight_pct is None and "min_single_security_weight_pct" in defaults:
        cfg.min_single_security_weight_pct = defaults["min_single_security_weight_pct"]
    cfg.client_profile = profile_id
