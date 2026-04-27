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
    # Derived: liquidity_need_total = liquidity_need_months * monthly_expenses (single source: months + expenses)
    liquidity_need: float
    
    # Liquidity (life floor): single source of truth for portfolio logic
    liquidity_need_months: float
    monthly_expenses: float
    portfolio_value: float | None
    cash_policy: str
    
    # Portfolio composition
    tickers: list[str]
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
    # Report-only: comparison target (target vs realized CAGR); not an optimization constraint
    target_nominal_return_annual: float | None
    target_vol_annual: float | None
    target_max_drawdown_pct: float | None
    horizon_years: float | None  # report-only; not used by optimizer
    
    # Client profile (optional): ultra_conservative | conservative | balanced | growth | aggressive
    client_profile: str | None
    # Optimization constraints (may be pending user input)
    rc_asset_cap_pct: float | None
    stress_top3_rc_sum_cap_pct: float | None  # Top3 RC sum limit in stress (default 0.70)
    max_single_security_weight_pct: float | None
    min_single_security_weight_pct: float | None
    N_rc: int
    growth_core_candidates: list[str]
    donor_shift_mode: str

    # Analysis settings
    windows_months: list[int]
    coverage_threshold: float
    output_dir: str  # CSV only (e.g. results_csv)
    output_dir_final: str  # Weights, JSON, report (e.g. Main portfolio)
    # Backtest mode: "dynamic_nan_safe" (default, policy-compliant) | "simple" (opt-in, no within-block/RC-gating)
    backtest_mode: str = "dynamic_nan_safe"

    # Dual-horizon: primary/secondary are the source of truth; optimization_windows_months is derived when missing
    optimization_windows_months: list[int] = field(default_factory=lambda: [120, 60])
    primary_window_months: int = 120
    secondary_window_months: int = 60
    robustness_policy: dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_ROBUSTNESS_POLICY))

    # Track pending fields
    pending_fields: list[str] = field(default_factory=list)

    # Liquidity floor from profile or explicit config; used by ProLiquidity when set (else derived from liquidity_need_months * monthly_expenses / portfolio_value)
    liquidity_floor_pct: float | None = None
    # Reserve this fraction of total portfolio for Tail block tickers (e.g. VIXY) after ProLiquidity; non-Tail weights scaled by (1 - tail_target_weight_pct).
    tail_target_weight_pct: float | None = None
    # RC post-processing: "strict" = do not write weights if RC caps unresolved; "permissive" = write but flag violation
    rc_policy_mode: str = "strict"
    # RC soft-control strength in optimizer objective (higher => stronger push against RC cap violations)
    rc_cap_penalty_lambda: float = 25.0
    # Soft penalties for max_return vs target_vol / target return; 0 => runtime uses 12 / 8 in run_optimization
    optimization_soft_vol_penalty_lambda: float = 0.0
    optimization_soft_return_penalty_lambda: float = 0.0
    # Deprecated: stress is diagnostic-only (DIAG_*); ignored for blocking. Kept for config compatibility.
    strict_stress_gate: bool = False
    # When True, use Ledoit-Wolf shrinkage for covariance in optimization/RC (more stable weights)
    covariance_shrinkage: bool = False
    # Dual covariance + caps for short-history assets in optimization (optional merge in validate)
    young_etf_optimization_policy: dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_YOUNG_ETF_OPTIMIZATION_POLICY))

    def get_resolved_config(self) -> dict[str, Any]:
        """
        Return all config values as a dictionary for export.
        Uses canonical names for user-facing output (run_metadata.json, config.yml):
        - risk_free_source (internal: rf_source)
        - base_benchmark_ticker (internal: benchmark_base_ticker)
        - beta_local_mapping (internal: local_benchmark_map)
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
            "weights": self.weights,
            "allow_leverage": self.allow_leverage,
            "allow_short_selling": self.allow_short_selling,
            "min_acceptable_return": self.min_acceptable_return,
            "target_nominal_return_annual": self.target_nominal_return_annual,
            "target_vol_annual": self.target_vol_annual,
            "target_max_drawdown_pct": self.target_max_drawdown_pct,
            "horizon_years": self.horizon_years,
            "rc_asset_cap_pct": self.rc_asset_cap_pct,
            "stress_top3_rc_sum_cap_pct": self.stress_top3_rc_sum_cap_pct,
            "max_single_security_weight_pct": self.max_single_security_weight_pct,
            "min_single_security_weight_pct": self.min_single_security_weight_pct,
            "N_rc": self.N_rc,
            "growth_core_candidates": self.growth_core_candidates,
            "donor_shift_mode": self.donor_shift_mode,
            "rc_policy_mode": self.rc_policy_mode,
            "rc_cap_penalty_lambda": self.rc_cap_penalty_lambda,
            "optimization_soft_vol_penalty_lambda": self.optimization_soft_vol_penalty_lambda,
            "optimization_soft_return_penalty_lambda": self.optimization_soft_return_penalty_lambda,
            "strict_stress_gate": self.strict_stress_gate,
            "covariance_shrinkage": self.covariance_shrinkage,
            "young_etf_optimization_policy": dict(self.young_etf_optimization_policy or {}),
            "windows_months": self.windows_months,
            "coverage_threshold": self.coverage_threshold,
            "output_dir": self.output_dir,
            "output_dir_final": self.output_dir_final,
            "optimization_windows_months": self.optimization_windows_months,
            "primary_window_months": self.primary_window_months,
            "secondary_window_months": self.secondary_window_months,
            "robustness_policy": self.robustness_policy,
            "liquidity_floor_pct": self.liquidity_floor_pct,
            "tail_target_weight_pct": self.tail_target_weight_pct,
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
            "stress_top3_rc_sum_cap_pct": self.stress_top3_rc_sum_cap_pct,
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
            "rc_policy_mode": self.rc_policy_mode,
            "rc_cap_penalty_lambda": self.rc_cap_penalty_lambda,
            "optimization_soft_vol_penalty_lambda": self.optimization_soft_vol_penalty_lambda,
            "optimization_soft_return_penalty_lambda": self.optimization_soft_return_penalty_lambda,
            "strict_stress_gate": self.strict_stress_gate,
            "covariance_shrinkage": self.covariance_shrinkage,
            "young_etf_optimization_policy": dict(self.young_etf_optimization_policy or {}),
        }


# If optional fields (benchmark_base_ticker, windows_months, output_dir) are missing,
# _inject_optional_defaults() fills them before validation so the pipeline always has a complete config.
REQUIRED_FIELDS = [
    "investor_currency",
    "tickers",
]
# Default base benchmark by investor currency (portfolio_construction_policy / metrics_spec).
DEFAULT_BENCHMARK_BY_CURRENCY: dict[str, str] = {
    "USD": "SPY",
    "EUR": "VGK",
    "JPY": "EWJ",
    "CHF": "EWL",
}
DEFAULT_WINDOWS_MONTHS = [36, 60, 120]
DEFAULT_OUTPUT_DIR = "results_csv"
DEFAULT_OUTPUT_DIR_FINAL = "Main portfolio"
# Dual-horizon: primary 10Y, secondary 5Y; robustness check does not replace 10Y by default
DEFAULT_OPTIMIZATION_WINDOWS_MONTHS = [120, 60]
DEFAULT_PRIMARY_WINDOW_MONTHS = 120
DEFAULT_SECONDARY_WINDOW_MONTHS = 60
DEFAULT_ROBUSTNESS_POLICY = {
    "enabled": True,
    "max_weight_change_allowed": 0.10,
    "max_asset_rc_dev_allowed": 0.05,
    "min_effective_months": 36,
}
# Young-ETF dual covariance + eligibility for optimization (see docs/data_policy_nan_young_etfs.md)
DEFAULT_YOUNG_ETF_OPTIMIZATION_POLICY = {
    "enabled": True,
    "eligible_months": 48,
    "candidate_months_min": 12,
    "new_shrinkage_alpha": 0.1,
    "candidate_alpha_min": 0.1,
    "candidate_alpha_at_eligible": 1.0,
    "max_weight_candidate_or_new_pct": 0.02,
    "aggregate_candidate_new_warn_pct": 0.10,
}
# Weights are optional: produced by optimization and exported (see Portfolio Construction Policy).

BOOLEAN_FIELDS = [
    "allow_leverage",
    "allow_short_selling",
    "strict_stress_gate",
    "covariance_shrinkage",
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
    "tail_target_weight_pct",
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
RC_POLICY_MODES = ("strict", "permissive")
BACKTEST_MODES = ("dynamic_nan_safe", "simple")

NUMERIC_FIELDS = [
    "horizon_years",
]

MAPPING_FIELDS = [
    "weights",
    "local_benchmark_map",
]

# These constraint fields may be null until the user provides final numeric values.
# The system supports them in config and passes them through all layers; no refactor needed when values are set.
PENDING_USER_INPUT_FIELDS = [
    "rc_asset_cap_pct",
    "max_single_security_weight_pct",
    "min_single_security_weight_pct",
]

# -----------------------------------------------------------------------------
# Naming convention (canonical vs internal):
# - config.yml and run_metadata.json export: use canonical names for users.
# - Code and PortfolioConfig attributes: use internal names.
# Example: base_benchmark_ticker (canonical) <-> benchmark_base_ticker (internal).
# Both spellings are accepted in config.yml; internal name is the single source in code.
# -----------------------------------------------------------------------------
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


def _inject_optional_defaults(cfg: dict[str, Any]) -> None:
    """
    Inject default values for optional config fields when they are missing.
    If benchmark_base_ticker, windows_months, or output_dir are not provided,
    the system inserts predefined defaults before validation and execution.
    This keeps the user's config minimal while ensuring the pipeline always runs with a complete configuration.
    Mutates cfg in place.
    """
    currency = (cfg.get("investor_currency") or "USD").upper()
    if not cfg.get("benchmark_base_ticker"):
        cfg["benchmark_base_ticker"] = DEFAULT_BENCHMARK_BY_CURRENCY.get(currency, "SPY")
    if not cfg.get("windows_months"):
        cfg["windows_months"] = list(DEFAULT_WINDOWS_MONTHS)
    if not cfg.get("output_dir"):
        cfg["output_dir"] = DEFAULT_OUTPUT_DIR
    if not cfg.get("output_dir_final"):
        cfg["output_dir_final"] = DEFAULT_OUTPUT_DIR_FINAL
    if cfg.get("primary_window_months") is None:
        cfg["primary_window_months"] = DEFAULT_PRIMARY_WINDOW_MONTHS
    if cfg.get("secondary_window_months") is None:
        cfg["secondary_window_months"] = DEFAULT_SECONDARY_WINDOW_MONTHS
    # optimization_windows_months: optional; derived from primary/secondary when not set (for backward compatibility)
    if not cfg.get("optimization_windows_months"):
        cfg["optimization_windows_months"] = [
            cfg.get("primary_window_months") or DEFAULT_PRIMARY_WINDOW_MONTHS,
            cfg.get("secondary_window_months") or DEFAULT_SECONDARY_WINDOW_MONTHS,
        ]
    if not cfg.get("robustness_policy"):
        cfg["robustness_policy"] = dict(DEFAULT_ROBUSTNESS_POLICY)
    else:
        # Merge with defaults so missing keys get defaults
        rp = dict(DEFAULT_ROBUSTNESS_POLICY)
        rp.update({k: v for k, v in cfg["robustness_policy"].items() if v is not None})
        legacy_rc = rp.pop("max_rc_block_dev_allowed", None)
        if legacy_rc is not None and cfg["robustness_policy"].get("max_asset_rc_dev_allowed") is None:
            rp["max_asset_rc_dev_allowed"] = legacy_rc
        cfg["robustness_policy"] = rp
    # Young-ETF optimization policy: merge user dict over defaults
    ypol_base = dict(DEFAULT_YOUNG_ETF_OPTIMIZATION_POLICY)
    ypol_user = cfg.get("young_etf_optimization_policy")
    if isinstance(ypol_user, dict):
        ypol_base.update({k: v for k, v in ypol_user.items() if v is not None})
    cfg["young_etf_optimization_policy"] = ypol_base
    # Backtest mode default (production report uses dynamic NaN-safe by default)
    raw = cfg.get("backtest_mode")
    if not raw:
        cfg["backtest_mode"] = "dynamic_nan_safe"
    else:
        # Legacy: map old values to new enums
        if raw.strip().lower() in ("production", "simple"):
            cfg["backtest_mode"] = "simple"
        elif raw.strip().lower() in ("research", "dynamic_nan_safe"):
            cfg["backtest_mode"] = "dynamic_nan_safe"
        elif raw.strip().lower() not in ("dynamic_nan_safe", "simple"):
            cfg["backtest_mode"] = "dynamic_nan_safe"


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


def _parse_float_optional(val: Any) -> float | None:
    """Return float(val) if val is present and numeric, else None. Used for optional decimals (e.g. liquidity_floor_pct)."""
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


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


def _validate_tail_target_weight_pct(cfg: dict[str, Any]) -> None:
    v = cfg.get("tail_target_weight_pct")
    if v is None:
        return
    if not isinstance(v, (int, float)):
        raise ConfigValidationError(
            f"Config field 'tail_target_weight_pct' must be numeric, got {type(v).__name__}"
        )
    x = float(v)
    if x < 0 or x > 0.25:
        raise ConfigValidationError(
            f"Config field 'tail_target_weight_pct' must be between 0 and 0.25, got {x}"
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


def _validate_robustness_policy(cfg: dict[str, Any]) -> None:
    """Validate robustness_policy: enabled (bool), thresholds (numeric), min_effective_months (int)."""
    rp = cfg.get("robustness_policy")
    if not rp or not isinstance(rp, dict):
        return
    if "enabled" in rp and rp["enabled"] is not None and not isinstance(rp["enabled"], bool):
        raise ConfigValidationError(
            f"robustness_policy.enabled must be boolean, got {type(rp['enabled']).__name__}"
        )
    for key, default in [
        ("max_weight_change_allowed", 0.10),
        ("max_asset_rc_dev_allowed", 0.05),
    ]:
        val = rp.get(key)
        if val is not None:
            if not isinstance(val, (int, float)) or val < 0:
                raise ConfigValidationError(
                    f"robustness_policy.{key} must be non-negative number, got {val}"
                )
    if rp.get("min_effective_months") is not None:
        v = rp["min_effective_months"]
        if not isinstance(v, int) or v < 1:
            raise ConfigValidationError(
                f"robustness_policy.min_effective_months must be positive integer, got {v}"
            )


def _validate_optimization_windows(cfg: dict[str, Any]) -> None:
    """Validate primary_window_months, secondary_window_months, optimization_windows_months."""
    for key in ("primary_window_months", "secondary_window_months"):
        val = cfg.get(key)
        if val is not None:
            if not isinstance(val, int) or val < 1:
                raise ConfigValidationError(
                    f"Config field '{key}' must be positive integer, got {val}"
                )
    ow = cfg.get("optimization_windows_months")
    if ow is not None:
        if not isinstance(ow, list):
            raise ConfigValidationError(
                "optimization_windows_months must be a list of integers"
            )
        for w in ow:
            if not isinstance(w, int) or w <= 0:
                raise ConfigValidationError(
                    f"optimization_windows_months must contain positive integers, got {w}"
                )


def _validate_backtest_mode(cfg: dict[str, Any]) -> None:
    """Validate backtest_mode is one of dynamic_nan_safe, simple."""
    val = cfg.get("backtest_mode", "dynamic_nan_safe")
    if val is None:
        return
    if not isinstance(val, str):
        raise ConfigValidationError(
            f"Config field 'backtest_mode' must be a string, got {type(val).__name__}: {val}"
        )
    if val.strip().lower() not in BACKTEST_MODES:
        raise ConfigValidationError(
            f"Config field 'backtest_mode' must be one of {BACKTEST_MODES}, got {val!r}"
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


def _validate_rc_policy_mode(cfg: dict[str, Any]) -> None:
    """Validate rc_policy_mode (strict | permissive)."""
    mode = cfg.get("rc_policy_mode", "strict")
    if mode is not None and mode not in RC_POLICY_MODES:
        raise ConfigValidationError(
            f"Config field 'rc_policy_mode' must be one of {RC_POLICY_MODES}, got {mode!r}"
        )


def _validate_rc_cap_penalty_lambda(cfg: dict[str, Any]) -> None:
    lam = cfg.get("rc_cap_penalty_lambda", 25.0)
    try:
        lf = float(lam)
    except (TypeError, ValueError):
        raise ConfigValidationError(
            f"Config field 'rc_cap_penalty_lambda' must be a positive number, got {lam!r}"
        ) from None
    if lf <= 0:
        raise ConfigValidationError(
            f"Config field 'rc_cap_penalty_lambda' must be positive, got {lf}"
        )


def _validate_optimization_soft_penalty_lambdas(cfg: dict[str, Any]) -> None:
    """Optional soft IPS alignment lambdas (>= 0; 0 = do not use in optimizer unless caller passes explicitly)."""
    for key in ("optimization_soft_vol_penalty_lambda", "optimization_soft_return_penalty_lambda"):
        v = cfg.get(key, 0.0)
        try:
            f = float(v)
        except (TypeError, ValueError):
            raise ConfigValidationError(
                f"Config field {key!r} must be a non-negative number, got {v!r}"
            ) from None
        if f < 0:
            raise ConfigValidationError(
                f"Config field {key!r} must be non-negative, got {f}"
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

    ``blocks_universe`` is accepted for backward compatibility and ignored (no blocks_universe.yml).

    Supports canonical config keys: base_benchmark_ticker, risk_free_source,
    beta_local_mapping (mapped to benchmark_base_ticker, rf_source, local_benchmark_map).
    Supports percent input in two formats: decimal 0.15 or string "15%".

    Raises ConfigValidationError if validation fails.
    """
    del blocks_universe  # legacy parameter; ignored
    cfg = _normalize_config_keys(cfg)
    cfg = _normalize_percent_fields(cfg)
    _inject_optional_defaults(cfg)

    _validate_required(cfg)
    _validate_booleans(cfg)
    _validate_percents(cfg)
    _validate_nonnegative(cfg)
    _validate_mappings(cfg)
    _validate_tickers_weights(cfg)
    _validate_windows(cfg)
    _validate_horizon_years(cfg)
    _validate_liquidity_need_months(cfg)
    _validate_cash_policy(cfg)
    _validate_tail_target_weight_pct(cfg)
    _validate_portfolio_value(cfg)
    _validate_alpha_shift_params(cfg)
    _validate_rc_policy_mode(cfg)
    _validate_rc_cap_penalty_lambda(cfg)
    _validate_optimization_soft_penalty_lambdas(cfg)
    _validate_backtest_mode(cfg)
    _validate_robustness_policy(cfg)
    _validate_optimization_windows(cfg)

    pending = _identify_pending_fields(cfg)

    return PortfolioConfig(
        investor_currency=cfg["investor_currency"],
        initial_investable_amount=cfg.get("initial_investable_amount", 1000),
        liquidity_need=float(cfg.get("liquidity_need_months", 0)) * float(cfg.get("monthly_expenses", 0) or 0),
        liquidity_need_months=float(cfg.get("liquidity_need_months", 0)),
        monthly_expenses=float(cfg.get("monthly_expenses", 0) or 0),
        portfolio_value=cfg.get("portfolio_value"),
        cash_policy=cfg.get("cash_policy", "allowed_for_scaling"),
        client_profile=cfg.get("client_profile"),
        tickers=list(cfg["tickers"]),
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
        stress_top3_rc_sum_cap_pct=cfg.get("stress_top3_rc_sum_cap_pct", 0.70),
        max_single_security_weight_pct=cfg.get("max_single_security_weight_pct"),
        min_single_security_weight_pct=cfg.get("min_single_security_weight_pct"),
        N_rc=cfg.get("N_rc", 3),
        growth_core_candidates=list(cfg.get("growth_core_candidates", ["VOO", "VT", "VTI"])),
        donor_shift_mode=cfg.get("donor_shift_mode", "proportional"),
        rc_policy_mode=cfg.get("rc_policy_mode", "strict"),
        rc_cap_penalty_lambda=float(cfg.get("rc_cap_penalty_lambda", 25.0)),
        optimization_soft_vol_penalty_lambda=float(cfg.get("optimization_soft_vol_penalty_lambda", 0.0)),
        optimization_soft_return_penalty_lambda=float(cfg.get("optimization_soft_return_penalty_lambda", 0.0)),
        strict_stress_gate=bool(cfg.get("strict_stress_gate", False)),
        covariance_shrinkage=bool(cfg.get("covariance_shrinkage", False)),
        young_etf_optimization_policy=dict(cfg.get("young_etf_optimization_policy") or DEFAULT_YOUNG_ETF_OPTIMIZATION_POLICY),
        liquidity_floor_pct=_parse_float_optional(cfg.get("liquidity_floor_pct")),
        tail_target_weight_pct=_parse_float_optional(cfg.get("tail_target_weight_pct")),
        windows_months=list(cfg["windows_months"]),
        coverage_threshold=cfg.get("coverage_threshold", 0.90),
        output_dir=cfg["output_dir"],
        output_dir_final=cfg.get("output_dir_final", DEFAULT_OUTPUT_DIR_FINAL),
        backtest_mode=cfg.get("backtest_mode", "dynamic_nan_safe"),
        optimization_windows_months=list(cfg.get("optimization_windows_months", DEFAULT_OPTIMIZATION_WINDOWS_MONTHS)),
        primary_window_months=int(cfg.get("primary_window_months", DEFAULT_PRIMARY_WINDOW_MONTHS)),
        secondary_window_months=int(cfg.get("secondary_window_months", DEFAULT_SECONDARY_WINDOW_MONTHS)),
        robustness_policy=dict(cfg.get("robustness_policy", DEFAULT_ROBUSTNESS_POLICY)),
        pending_fields=pending,
    )
