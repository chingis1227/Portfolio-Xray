"""
Configuration schema and validation for Portfolio Metrics Standard.

Validates all config fields, ensures required fields are present,
and tracks which constraint fields are pending user input.

Supports percent input in two formats:
  - Decimal: 0.15
  - Percent string: "15%" (automatically converted to 0.15)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from src.client_profiles import normalize_rc_block_targets


class ConfigValidationError(Exception):
    """Raised when config validation fails."""
    pass


@dataclass
class PortfolioConfig:
    """
    Strongly-typed configuration container for portfolio metrics.
    
    Fields marked as 'pending_user_input' are placeholders that may be
    filled in later without requiring code refactoring.
    """
    # Core settings
    investor_currency: str
    initial_investable_amount: float
    liquidity_need: float
    
    # Liquidity (life floor + cash policy)
    liquidity_need_months: float
    monthly_expenses: float
    portfolio_value: float | None
    cash_policy: str
    
    # Portfolio composition
    tickers: list[str]
    blocks: dict[str, list[str]]  # Growth, Duration, Inflation -> list of tickers; from this N, Nc, Ns, k_block are derived
    weights: dict[str, float]
    
    # Benchmark and risk-free
    benchmark_base_ticker: str
    rf_source: str | None
    cash_proxy_ticker: str | None
    local_benchmark_map: dict[str, str] | None
    
    # Portfolio assumptions
    allow_leverage: bool
    allow_short_selling: bool
    min_acceptable_return: float | None
    target_nominal_return_annual: float | None
    target_vol_annual: float | None
    target_max_drawdown_pct: float | None
    horizon_years: float | None
    
    # Client profile (optional): ultra_conservative | conservative | balanced | growth | aggressive
    client_profile: str | None
    # Optimization constraints (may be pending user input)
    rc_asset_cap_pct: float | None
    rc_block_targets: dict[str, float] | None
    stress_top3_rc_sum_cap_pct: float | None  # Top3 RC sum limit in stress (default 0.70)
    max_single_security_weight_pct: float | None
    min_single_security_weight_pct: float | None
    N_rc: int
    growth_core_candidates: list[str]
    donor_shift_mode: str
    
    # Analysis settings
    windows_months: list[int]
    coverage_threshold: float
    output_dir: str
    
    # Track pending fields
    pending_fields: list[str] = field(default_factory=list)
    
    def get_resolved_config(self) -> dict[str, Any]:
        """
        Return all config values as a dictionary for export.
        Uses canonical names (risk_free_source, base_benchmark_ticker, beta_local_mapping)
        so that run_metadata.json matches config.yml naming.
        """
        return {
            "investor_currency": self.investor_currency,
            "initial_investable_amount": self.initial_investable_amount,
            "liquidity_need": self.liquidity_need,
            "liquidity_need_months": self.liquidity_need_months,
            "monthly_expenses": self.monthly_expenses,
            "portfolio_value": self.portfolio_value,
            "cash_policy": self.cash_policy,
            "client_profile": self.client_profile,
            "risk_free_source": self.rf_source,
            "cash_proxy_ticker": self.cash_proxy_ticker,
            "base_benchmark_ticker": self.benchmark_base_ticker,
            "beta_local_mapping": self.local_benchmark_map,
            "tickers": self.tickers,
            "blocks": self.blocks,
            "weights": self.weights,
            "allow_leverage": self.allow_leverage,
            "allow_short_selling": self.allow_short_selling,
            "min_acceptable_return": self.min_acceptable_return,
            "target_nominal_return_annual": self.target_nominal_return_annual,
            "target_vol_annual": self.target_vol_annual,
            "target_max_drawdown_pct": self.target_max_drawdown_pct,
            "horizon_years": self.horizon_years,
            "rc_asset_cap_pct": self.rc_asset_cap_pct,
            "rc_block_targets": self.rc_block_targets,
            "stress_top3_rc_sum_cap_pct": self.stress_top3_rc_sum_cap_pct,
            "max_single_security_weight_pct": self.max_single_security_weight_pct,
            "min_single_security_weight_pct": self.min_single_security_weight_pct,
            "N_rc": self.N_rc,
            "growth_core_candidates": self.growth_core_candidates,
            "donor_shift_mode": self.donor_shift_mode,
            "windows_months": self.windows_months,
            "coverage_threshold": self.coverage_threshold,
            "output_dir": self.output_dir,
        }
    
    def get_pending_config_items(self) -> dict[str, Any]:
        """Return config items that are pending user input."""
        return {f: getattr(self, f) for f in self.pending_fields}
    
    def get_active_assumptions(self) -> dict[str, Any]:
        """Return assumptions that are actively used in calculations."""
        return {
            "investor_currency": self.investor_currency,
            "initial_investable_amount": self.initial_investable_amount,
            "rf_source": self.rf_source,
            "cash_proxy_ticker": self.cash_proxy_ticker,
            "benchmark_base_ticker": self.benchmark_base_ticker,
            "min_acceptable_return": self.min_acceptable_return,
            "target_nominal_return_annual": self.target_nominal_return_annual,
            "allow_leverage": self.allow_leverage,
            "allow_short_selling": self.allow_short_selling,
        }
    
    def get_future_constraint_fields(self) -> dict[str, Any]:
        """Return fields reserved for future portfolio optimization."""
        return {
            "rc_asset_cap_pct": self.rc_asset_cap_pct,
            "rc_block_targets": self.rc_block_targets,
            "stress_top3_rc_sum_cap_pct": self.stress_top3_rc_sum_cap_pct,
            "blocks": self.blocks,
            "max_single_security_weight_pct": self.max_single_security_weight_pct,
            "min_single_security_weight_pct": self.min_single_security_weight_pct,
            "target_vol_annual": self.target_vol_annual,
            "target_max_drawdown_pct": self.target_max_drawdown_pct,
            "horizon_years": self.horizon_years,
            "liquidity_need": self.liquidity_need,
            "liquidity_need_months": self.liquidity_need_months,
            "monthly_expenses": self.monthly_expenses,
            "portfolio_value": self.portfolio_value,
            "cash_policy": self.cash_policy,
            "N_rc": self.N_rc,
            "growth_core_candidates": self.growth_core_candidates,
            "donor_shift_mode": self.donor_shift_mode,
        }


REQUIRED_FIELDS = [
    "investor_currency",
    "tickers",
    "benchmark_base_ticker",
    "windows_months",
    "output_dir",
]
# Weights are optional: produced by optimization and exported (see Portfolio Construction Policy).

BOOLEAN_FIELDS = [
    "allow_leverage",
    "allow_short_selling",
]

PERCENT_FIELDS = [
    "min_acceptable_return",
    "target_nominal_return_annual",
    "target_vol_annual",
    "target_max_drawdown_pct",
    "rc_asset_cap_pct",
    "stress_top3_rc_sum_cap_pct",
    "max_single_security_weight_pct",
    "min_single_security_weight_pct",
    "coverage_threshold",
]

NONNEGATIVE_FIELDS = [
    "initial_investable_amount",
    "liquidity_need",
    "monthly_expenses",
    "coverage_threshold",
]

# portfolio_value validated separately (optional, non-negative when set)
CASH_POLICY_VALUES = ("required_floor", "allowed_for_scaling", "prohibited")
DONOR_SHIFT_MODES = ("proportional", "equal")

NUMERIC_FIELDS = [
    "horizon_years",
]

MAPPING_FIELDS = [
    "weights",
    "local_benchmark_map",
    "rc_block_targets",
    "blocks",
]

# These constraint fields may be null until the user provides final numeric values.
# The system supports them in config and passes them through all layers; no refactor needed when values are set.
PENDING_USER_INPUT_FIELDS = [
    "rc_asset_cap_pct",
    "rc_block_targets",
    "max_single_security_weight_pct",
    "min_single_security_weight_pct",
]

# Canonical config keys (config.yml) mapped to internal schema keys.
# These allow user-facing names while keeping internal names stable.
CONFIG_KEY_ALIASES = [
    ("base_benchmark_ticker", "benchmark_base_ticker"),
    ("risk_free_source", "rf_source"),
    ("beta_local_mapping", "local_benchmark_map"),
    ("max_single_asset_weight_pct", "max_single_security_weight_pct"),
    ("min_single_asset_weight_pct", "min_single_security_weight_pct"),
]


def _normalize_config_keys(cfg: dict[str, Any]) -> dict[str, Any]:
    """
    Copy canonical config keys into internal keys so both naming conventions work.
    config.yml can use: base_benchmark_ticker, risk_free_source, beta_local_mapping.
    Internal schema uses: benchmark_base_ticker, rf_source, local_benchmark_map.
    """
    result = dict(cfg)
    for canonical, internal in CONFIG_KEY_ALIASES:
        if canonical in result and result.get(internal) is None:
            result[internal] = result[canonical]
    return result


def _parse_percent_value(val: Any, field_name: str) -> float | None:
    """
    Parse a percent value that can be either:
      - None (returns None)
      - Numeric (int/float): returned as-is
      - String like "15%", "-20%": converted to 0.15, -0.20
    
    Raises ConfigValidationError if format is invalid.
    """
    if val is None:
        return None
    
    if isinstance(val, (int, float)):
        return float(val)
    
    if isinstance(val, str):
        val = val.strip()
        match = re.match(r'^(-?\d+(?:\.\d+)?)\s*%$', val)
        if match:
            return float(match.group(1)) / 100.0
        raise ConfigValidationError(
            f"Config field '{field_name}': invalid percent format '{val}'. "
            f"Use decimal (0.15) or percent string ('15%')."
        )
    
    raise ConfigValidationError(
        f"Config field '{field_name}' must be numeric or percent string, "
        f"got {type(val).__name__}: {val}"
    )


def _parse_numeric_value(val: Any, field_name: str) -> float | None:
    """
    Parse a numeric value (int or float).
    Returns None if val is None.
    """
    if val is None:
        return None
    
    if isinstance(val, (int, float)):
        return float(val)
    
    raise ConfigValidationError(
        f"Config field '{field_name}' must be numeric, got {type(val).__name__}: {val}"
    )


def _normalize_percent_fields(cfg: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize all percent fields: convert "15%" to 0.15.
    Returns a new dict with normalized values.
    """
    result = dict(cfg)
    
    for f in PERCENT_FIELDS:
        if f in result:
            result[f] = _parse_percent_value(result[f], f)
    
    for f in NUMERIC_FIELDS:
        if f in result:
            result[f] = _parse_numeric_value(result[f], f)
    
    # Handle rc_block_targets dict separately
    rc_targets = result.get("rc_block_targets")
    if rc_targets is not None and isinstance(rc_targets, dict):
        normalized_targets = {}
        for block_name, target_pct in rc_targets.items():
            normalized_targets[block_name] = _parse_percent_value(
                target_pct, f"rc_block_targets['{block_name}']"
            )
        result["rc_block_targets"] = normalized_targets
    
    # Handle weights dict (also supports percent format)
    weights = result.get("weights")
    if weights is not None and isinstance(weights, dict):
        normalized_weights = {}
        for ticker, w_val in weights.items():
            normalized_weights[ticker] = _parse_percent_value(
                w_val, f"weights['{ticker}']"
            )
        result["weights"] = normalized_weights
    
    return result


def _validate_required(cfg: dict[str, Any]) -> None:
    """Check that all required fields are present and non-empty."""
    missing = []
    for f in REQUIRED_FIELDS:
        if f not in cfg or cfg[f] is None:
            missing.append(f)
        elif isinstance(cfg[f], (list, dict, str)) and len(cfg[f]) == 0:
            missing.append(f)
    if missing:
        raise ConfigValidationError(
            f"Missing or empty required config fields: {missing}"
        )


def _validate_booleans(cfg: dict[str, Any]) -> None:
    """Validate boolean fields. Values: true / false."""
    for f in BOOLEAN_FIELDS:
        val = cfg.get(f)
        if val is not None and not isinstance(val, bool):
            raise ConfigValidationError(
                f"Config field '{f}' must be boolean (true/false), got {type(val).__name__}: {val}"
            )


def _validate_percent_field(name: str, val: Any) -> None:
    """Validate a percent/decimal field is numeric and within sensible bounds."""
    if val is None:
        return
    if not isinstance(val, (int, float)):
        raise ConfigValidationError(
            f"Config field '{name}' must be numeric, got {type(val).__name__}: {val}"
        )
    if name in ("coverage_threshold",) and not (0.0 <= val <= 1.0):
        raise ConfigValidationError(
            f"Config field '{name}' must be between 0 and 1, got {val}"
        )
    if name == "target_max_drawdown_pct" and val > 0:
        raise ConfigValidationError(
            f"Config field '{name}' should be negative (e.g., -0.20 or '-20%'), got {val}"
        )


def _validate_percents(cfg: dict[str, Any]) -> None:
    """Validate all percent fields."""
    for f in PERCENT_FIELDS:
        _validate_percent_field(f, cfg.get(f))


def _validate_nonnegative(cfg: dict[str, Any]) -> None:
    """Validate non-negative numeric fields."""
    for f in NONNEGATIVE_FIELDS:
        val = cfg.get(f)
        if val is not None:
            if not isinstance(val, (int, float)):
                raise ConfigValidationError(
                    f"Config field '{f}' must be numeric, got {type(val).__name__}: {val}"
                )
            if val < 0:
                raise ConfigValidationError(
                    f"Config field '{f}' must be non-negative, got {val}"
                )


def _validate_mappings(cfg: dict[str, Any]) -> None:
    """Validate mapping fields are dictionaries."""
    for f in MAPPING_FIELDS:
        val = cfg.get(f)
        if val is not None and not isinstance(val, dict):
            raise ConfigValidationError(
                f"Config field '{f}' must be a dictionary, got {type(val).__name__}"
            )


def _validate_tickers_weights(cfg: dict[str, Any]) -> None:
    """Validate tickers/weights consistency."""
    tickers = cfg.get("tickers", [])
    weights = cfg.get("weights", {})
    
    if not isinstance(tickers, list):
        raise ConfigValidationError(
            f"Config field 'tickers' must be a list, got {type(tickers).__name__}"
        )
    
    for w_ticker, w_val in weights.items():
        if w_ticker not in tickers:
            raise ConfigValidationError(
                f"Weight defined for ticker '{w_ticker}' which is not in tickers list"
            )
        if not isinstance(w_val, (int, float)):
            raise ConfigValidationError(
                f"Weight for '{w_ticker}' must be numeric, got {type(w_val).__name__}"
            )
        if w_val < 0:
            raise ConfigValidationError(
                f"Weight for '{w_ticker}' must be non-negative, got {w_val}"
            )


BLOCK_NAMES = ("Growth", "Duration", "Inflation")
STRESS_BLOCK_NAMES = ("Growth", "Duration", "Inflation", "Liquidity", "Tail")  # for stress report; Growth_HY, Growth_EM_debt → Growth
GROWTH_HY_KEY = "Growth_HY"  # sub-block of Growth (High Yield); RC_vol(HY) ≤ 10% × RC_vol(Growth)
GROWTH_EM_DEBT_KEY = "Growth_EM_debt"  # sub-block of Growth (EM Debt); RC_vol(EM Debt) ≤ 10% × RC_vol(Growth)

def _build_ticker_to_block_from_universe(blocks_universe: dict[str, list[str]]) -> dict[str, str]:
    """
    Build ticker -> block_name from blocks_universe. Raises if a ticker appears in more than one block.
    """
    ticker_to_block: dict[str, str] = {}
    for block_name, tickers in blocks_universe.items():
        if not isinstance(tickers, list):
            continue
        for t in tickers:
            t = str(t).strip()
            if not t:
                continue
            if t in ticker_to_block:
                raise ConfigValidationError(
                    f"blocks_universe.yml: ticker '{t}' appears in both '{ticker_to_block[t]}' and '{block_name}'. "
                    "One ticker must belong to exactly one block."
                )
            ticker_to_block[t] = block_name
    return ticker_to_block


def _effective_blocks_from_universe(
    config_tickers: list[str],
    blocks_universe: dict[str, list[str]],
) -> dict[str, list[str]]:
    """
    Resolve blocks for config_tickers using blocks_universe. Each config ticker must appear
    in exactly one block in the universe. Returns normalized blocks dict containing only
    the given tickers. Raises ConfigValidationError if any ticker is not in any block.
    """
    ticker_to_block = _build_ticker_to_block_from_universe(blocks_universe)
    unknown = [t for t in config_tickers if t not in ticker_to_block]
    if unknown:
        raise ConfigValidationError(
            f"Ticker(s) not found in blocks_universe.yml (no block assigned): {', '.join(unknown)}. "
            "Add them to a block in blocks_universe.yml or remove them from config tickers."
        )
    # Build effective blocks: only blocks that have at least one of our tickers
    effective: dict[str, list[str]] = {b: [] for b in BLOCK_NAMES}
    effective[GROWTH_HY_KEY] = []
    effective[GROWTH_EM_DEBT_KEY] = []
    effective["Liquidity"] = []
    effective["Tail"] = []
    for t in config_tickers:
        block = ticker_to_block[t]
        if block not in effective:
            effective[block] = []
        effective[block].append(t)
    return _normalize_blocks(effective)


def _normalize_blocks(blocks: dict[str, Any] | None) -> dict[str, list[str]]:
    """Return blocks with Growth, Duration, Inflation, optional Growth_HY, Growth_EM_debt, Liquidity, Tail; default empty lists if missing."""
    default = {b: [] for b in BLOCK_NAMES}
    default[GROWTH_HY_KEY] = []
    default[GROWTH_EM_DEBT_KEY] = []
    for b in ("Liquidity", "Tail"):
        default[b] = []
    if blocks is None:
        return default
    out = {b: list(blocks.get(b, [])) for b in BLOCK_NAMES}
    out[GROWTH_HY_KEY] = list(blocks.get(GROWTH_HY_KEY, []))
    out[GROWTH_EM_DEBT_KEY] = list(blocks.get(GROWTH_EM_DEBT_KEY, []))
    out["Liquidity"] = list(blocks.get("Liquidity", []))
    out["Tail"] = list(blocks.get("Tail", []))
    return out


def _validate_blocks(cfg: dict[str, Any]) -> None:
    """Validate blocks: optional; must have Growth, Duration, Inflation as lists; Growth_HY, Growth_EM_debt, Liquidity, Tail optional lists."""
    blocks = cfg.get("blocks")
    if blocks is None:
        return
    for key in BLOCK_NAMES:
        if key not in blocks:
            raise ConfigValidationError(
                f"Config field 'blocks' must contain keys {list(BLOCK_NAMES)}, missing '{key}'"
            )
        val = blocks[key]
        if not isinstance(val, list):
            raise ConfigValidationError(
                f"Config field 'blocks[\"{key}\"]' must be a list of tickers, got {type(val).__name__}"
            )
        for t in val:
            if not isinstance(t, str):
                raise ConfigValidationError(
                    f"Config field 'blocks[\"{key}\"]' must contain strings (tickers), got {type(t).__name__}"
                )
    for key in (GROWTH_HY_KEY, GROWTH_EM_DEBT_KEY, "Liquidity", "Tail"):
        val = blocks.get(key)
        if val is not None:
            if not isinstance(val, list):
                raise ConfigValidationError(
                    f"Config field 'blocks[\"{key}\"]' must be a list of tickers, got {type(val).__name__}"
                )
            for t in val:
                if not isinstance(t, str):
                    raise ConfigValidationError(
                        f"Config field 'blocks[\"{key}\"]' must contain strings (tickers), got {type(t).__name__}"
                    )


def _validate_rc_block_targets(cfg: dict[str, Any]) -> None:
    """Validate rc_block_targets structure if provided."""
    rc_targets = cfg.get("rc_block_targets")
    if rc_targets is None:
        return
    if not isinstance(rc_targets, dict):
        raise ConfigValidationError(
            f"Config field 'rc_block_targets' must be a dictionary"
        )
    for block_name, target_pct in rc_targets.items():
        if not isinstance(target_pct, (int, float)):
            raise ConfigValidationError(
                f"rc_block_targets['{block_name}'] must be numeric, got {type(target_pct).__name__}"
            )
        if target_pct < 0:
            raise ConfigValidationError(
                f"rc_block_targets['{block_name}'] must be non-negative, got {target_pct}"
            )


def _validate_windows(cfg: dict[str, Any]) -> None:
    """Validate windows_months field."""
    windows = cfg.get("windows_months", [])
    if not isinstance(windows, list):
        raise ConfigValidationError(
            f"Config field 'windows_months' must be a list, got {type(windows).__name__}"
        )
    for w in windows:
        if not isinstance(w, int) or w <= 0:
            raise ConfigValidationError(
                f"windows_months must contain positive integers, got {w}"
            )


def _validate_horizon_years(cfg: dict[str, Any]) -> None:
    """Validate horizon_years field (just a number)."""
    val = cfg.get("horizon_years")
    if val is None:
        return
    if not isinstance(val, (int, float)):
        raise ConfigValidationError(
            f"Config field 'horizon_years' must be a number (e.g., 10, 5, 0.5), "
            f"got {type(val).__name__}: {val}"
        )
    if val <= 0:
        raise ConfigValidationError(
            f"Config field 'horizon_years' must be positive, got {val}"
        )


def _validate_liquidity_need_months(cfg: dict[str, Any]) -> None:
    """Validate liquidity_need_months: any non-negative number (int or float)."""
    val = cfg.get("liquidity_need_months", 0)
    if val is None:
        return
    if not isinstance(val, (int, float)):
        raise ConfigValidationError(
            f"Config field 'liquidity_need_months' must be a number, got {type(val).__name__}: {val}"
        )
    try:
        v = float(val)
    except (TypeError, ValueError):
        raise ConfigValidationError(
            f"Config field 'liquidity_need_months' must be a number, got {val!r}"
        ) from None
    if v < 0 or not (v == v):  # reject NaN
        raise ConfigValidationError(
            f"Config field 'liquidity_need_months' must be non-negative, got {val}"
        )


def _validate_cash_policy(cfg: dict[str, Any]) -> None:
    """Validate cash_policy is one of required_floor, allowed_for_scaling, prohibited."""
    val = cfg.get("cash_policy", "allowed_for_scaling")
    if val is None:
        return
    if not isinstance(val, str):
        raise ConfigValidationError(
            f"Config field 'cash_policy' must be a string, got {type(val).__name__}: {val}"
        )
    if val not in CASH_POLICY_VALUES:
        raise ConfigValidationError(
            f"Config field 'cash_policy' must be one of {CASH_POLICY_VALUES}, got {val!r}"
        )


def _validate_portfolio_value(cfg: dict[str, Any]) -> None:
    """Validate portfolio_value optional, non-negative when set."""
    val = cfg.get("portfolio_value")
    if val is None:
        return
    if not isinstance(val, (int, float)):
        raise ConfigValidationError(
            f"Config field 'portfolio_value' must be numeric, got {type(val).__name__}: {val}"
        )
    if val < 0:
        raise ConfigValidationError(
            f"Config field 'portfolio_value' must be non-negative, got {val}"
        )


def _validate_alpha_shift_params(cfg: dict[str, Any]) -> None:
    """Validate N_rc, growth_core_candidates, donor_shift_mode."""
    n_rc = cfg.get("N_rc", 3)
    if n_rc is not None:
        if not isinstance(n_rc, int) or n_rc < 1:
            raise ConfigValidationError(
                f"Config field 'N_rc' must be a positive integer, got {n_rc}"
            )
    candidates = cfg.get("growth_core_candidates", ["VOO", "VT", "VTI"])
    if candidates is not None:
        if not isinstance(candidates, list):
            raise ConfigValidationError(
                f"Config field 'growth_core_candidates' must be a list of tickers, got {type(candidates).__name__}"
            )
        if not all(isinstance(t, str) and t for t in candidates):
            raise ConfigValidationError(
                "Config field 'growth_core_candidates' must be a list of non-empty strings (tickers)"
            )
    mode = cfg.get("donor_shift_mode", "proportional")
    if mode is not None and mode not in DONOR_SHIFT_MODES:
        raise ConfigValidationError(
            f"Config field 'donor_shift_mode' must be one of {DONOR_SHIFT_MODES}, got {mode!r}"
        )


def _identify_pending_fields(cfg: dict[str, Any]) -> list[str]:
    """Identify which constraint fields are still pending user input (null/None)."""
    pending = []
    for f in PENDING_USER_INPUT_FIELDS:
        if cfg.get(f) is None:
            pending.append(f)
    return pending


def validate_config(cfg: dict[str, Any], blocks_universe: dict[str, list[str]] | None = None) -> PortfolioConfig:
    """
    Validate config dict and return PortfolioConfig object.
    
    If blocks_universe is provided (from blocks_universe.yml), each ticker in config must
    appear in exactly one block there; effective blocks are derived from the universe.
    If any config ticker is not in the universe, ConfigValidationError is raised.
    
    Supports canonical config keys: base_benchmark_ticker, risk_free_source,
    beta_local_mapping (mapped to benchmark_base_ticker, rf_source, local_benchmark_map).
    Supports percent input in two formats: decimal 0.15 or string "15%".
    
    Raises ConfigValidationError if validation fails.
    Allows pending user input fields (rc_asset_cap_pct, max_single_security_weight_pct,
    min_single_security_weight_pct) to be null; they are carried in config and
    exported in metadata until the user provides final values.
    """
    # Normalize canonical keys (base_benchmark_ticker -> benchmark_base_ticker, etc.)
    cfg = _normalize_config_keys(cfg)
    # Normalize percent fields ("15%" -> 0.15)
    cfg = _normalize_percent_fields(cfg)
    
    # Then validate
    _validate_required(cfg)
    _validate_booleans(cfg)
    _validate_percents(cfg)
    _validate_nonnegative(cfg)
    _validate_mappings(cfg)
    if not blocks_universe:
        _validate_blocks(cfg)
    _validate_tickers_weights(cfg)
    _validate_rc_block_targets(cfg)
    _validate_windows(cfg)
    _validate_horizon_years(cfg)
    _validate_liquidity_need_months(cfg)
    _validate_cash_policy(cfg)
    _validate_portfolio_value(cfg)
    _validate_alpha_shift_params(cfg)
    
    # Resolve blocks: from universe (for config tickers) or from config
    if blocks_universe:
        blocks_final = _effective_blocks_from_universe(list(cfg["tickers"]), blocks_universe)
    else:
        blocks_final = _normalize_blocks(cfg.get("blocks"))
    
    pending = _identify_pending_fields(cfg)
    rc_raw = cfg.get("rc_block_targets")
    rc_normalized = normalize_rc_block_targets(rc_raw) if rc_raw else None

    return PortfolioConfig(
        investor_currency=cfg["investor_currency"],
        initial_investable_amount=cfg.get("initial_investable_amount", 1000),
        liquidity_need=cfg.get("liquidity_need", 0),
        liquidity_need_months=float(cfg.get("liquidity_need_months", 0)),
        monthly_expenses=cfg.get("monthly_expenses", 0.0),
        portfolio_value=cfg.get("portfolio_value"),
        cash_policy=cfg.get("cash_policy", "allowed_for_scaling"),
        client_profile=cfg.get("client_profile"),
        tickers=list(cfg["tickers"]),
        blocks=blocks_final,
        weights=dict(cfg.get("weights") or {}),
        benchmark_base_ticker=cfg["benchmark_base_ticker"],
        rf_source=cfg.get("rf_source"),
        cash_proxy_ticker=cfg.get("cash_proxy_ticker"),
        local_benchmark_map=cfg.get("local_benchmark_map"),
        allow_leverage=cfg.get("allow_leverage", False),
        allow_short_selling=cfg.get("allow_short_selling", False),
        min_acceptable_return=cfg.get("min_acceptable_return"),
        target_nominal_return_annual=cfg.get("target_nominal_return_annual"),
        target_vol_annual=cfg.get("target_vol_annual"),
        target_max_drawdown_pct=cfg.get("target_max_drawdown_pct"),
        horizon_years=cfg.get("horizon_years"),
        rc_asset_cap_pct=cfg.get("rc_asset_cap_pct"),
        rc_block_targets=rc_normalized,
        stress_top3_rc_sum_cap_pct=cfg.get("stress_top3_rc_sum_cap_pct", 0.70),
        max_single_security_weight_pct=cfg.get("max_single_security_weight_pct"),
        min_single_security_weight_pct=cfg.get("min_single_security_weight_pct"),
        N_rc=cfg.get("N_rc", 3),
        growth_core_candidates=list(cfg.get("growth_core_candidates", ["VOO", "VT", "VTI"])),
        donor_shift_mode=cfg.get("donor_shift_mode", "proportional"),
        windows_months=list(cfg["windows_months"]),
        coverage_threshold=cfg.get("coverage_threshold", 0.90),
        output_dir=cfg["output_dir"],
        pending_fields=pending,
    )
