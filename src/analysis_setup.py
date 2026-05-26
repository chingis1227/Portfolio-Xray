"""Resolved Analysis Setup contract for the input and assumptions layer."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from src.client_profiles import get_profile_defaults
from src.config_schema import ConfigValidationError, PortfolioConfig
from src.returns_frequency import (
    normalize_returns_frequency,
    resolve_returns_frequencies,
)


ANALYSIS_SETUP_VERSION = "analysis_setup_v1"
ANALYSIS_SUBJECT_VERSION = "analysis_subject_v1"
ANALYSIS_SUBJECT_TYPES = ("current_portfolio", "model_portfolio", "universe_baseline")

_SUBJECT_DEFAULT_DISPLAY = {
    "current_portfolio": "Current Portfolio",
    "model_portfolio": "Model Portfolio",
    "universe_baseline": "Universe Baseline",
}
_SUBJECT_PORTFOLIO_ROLE = {
    "current_portfolio": "user_current_portfolio",
    "model_portfolio": "model_portfolio",
    "universe_baseline": "equal_weight_initial_baseline",
}
_SUBJECT_PRODUCT_INPUT_CASE = {
    "current_portfolio": "user_current",
    "model_portfolio": "model_portfolio",
    "universe_baseline": "universe_only",
}
_SUBJECT_RECOMMENDATION_STATUS = {
    "current_portfolio": "diagnostic_current_portfolio_not_recommendation",
    "model_portfolio": "diagnostic_model_portfolio_not_recommendation",
    "universe_baseline": "baseline_not_recommendation",
}


def _round_weight(value: float) -> float:
    return round(float(value), 10)


def positive_weights(weights: dict[str, float] | None) -> dict[str, float]:
    """Return positive numeric weights keyed by normalized ticker string."""
    out: dict[str, float] = {}
    for ticker, value in (weights or {}).items():
        try:
            w = float(value)
        except (TypeError, ValueError):
            continue
        if w > 0:
            out[str(ticker)] = w
    return out


def weight_status(weights: dict[str, float] | None) -> dict[str, Any]:
    """Serializable status for a weight map without changing the weights."""
    positive = positive_weights(weights)
    total = float(sum(positive.values()))
    if not positive:
        status = "absent"
    elif abs(total - 1.0) <= 1e-6:
        status = "fully_invested"
    elif total < 1.0:
        status = "partial_with_cash_remainder"
    else:
        status = "overallocated"
    return {
        "status": status,
        "has_weights": bool(positive),
        "positive_weight_tickers": sorted(positive),
        "positive_weight_count": len(positive),
        "weight_sum": _round_weight(total),
        "cash_remainder": _round_weight(max(0.0, 1.0 - total)),
    }


def _rounded_weight_map(weights: dict[str, float] | None) -> dict[str, float]:
    return {str(t): _round_weight(w) for t, w in positive_weights(weights).items()}


def _equal_weight_map(tickers: list[str]) -> dict[str, float]:
    clean = [str(t) for t in tickers if str(t).strip()]
    if not clean:
        return {}
    weight = 1.0 / len(clean)
    return {ticker: _round_weight(weight) for ticker in clean}


def _clean_tickers(tickers: list[str] | None) -> list[str]:
    out: list[str] = []
    for raw in tickers or []:
        ticker = str(raw).strip()
        if ticker and ticker not in out:
            out.append(ticker)
    return out


def _upper_ticker(value: Any) -> str:
    return str(value or "").strip().upper()


_KNOWN_TAXONOMY_TICKERS: frozenset[str] | None = None


def _load_taxonomy_ticker_set(path: Path, loader_name: str) -> set[str]:
    if not path.is_file():
        return set()
    if loader_name == "etf":
        from src.etf_universe import UniverseValidationError, load_etf_universe

        loader = load_etf_universe
        label = "ETF"
    else:
        from src.stock_universe import UniverseValidationError, load_stock_universe

        loader = load_stock_universe
        label = "stock"
    try:
        records = loader(path)
    except UniverseValidationError as exc:
        raise ConfigValidationError(
            f"Cannot preflight analysis_subject tickers: {label} universe invalid ({path}): {exc}"
        ) from exc
    return {_upper_ticker(row.get("ticker")) for row in records if _upper_ticker(row.get("ticker"))}


def _known_taxonomy_tickers() -> frozenset[str]:
    global _KNOWN_TAXONOMY_TICKERS
    if _KNOWN_TAXONOMY_TICKERS is not None:
        return _KNOWN_TAXONOMY_TICKERS
    from src.etf_universe import DEFAULT_UNIVERSE_PATH as ETF_PATH
    from src.stock_universe import DEFAULT_UNIVERSE_PATH as STOCK_PATH

    known = _load_taxonomy_ticker_set(ETF_PATH, "etf") | _load_taxonomy_ticker_set(STOCK_PATH, "stock")
    if not known:
        raise ConfigValidationError(
            "Cannot preflight analysis_subject tickers: neither ETF nor stock taxonomy file is available."
        )
    _KNOWN_TAXONOMY_TICKERS = frozenset(known)
    return _KNOWN_TAXONOMY_TICKERS


def preflight_explicit_analysis_subject_tickers(
    tickers: list[str] | None,
    *,
    extra_allowed: Iterable[str] | None = None,
) -> None:
    """Reject unknown tickers for explicit portfolio-first subjects before report runs."""
    from src.real_cash import is_real_cash_ticker

    clean = [_upper_ticker(t) for t in _clean_tickers(tickers)]
    allowed = set(_known_taxonomy_tickers())
    for raw in extra_allowed or []:
        token = _upper_ticker(raw)
        if token:
            allowed.add(token)
    for raw in _clean_tickers(tickers):
        if is_real_cash_ticker(raw):
            allowed.add(_upper_ticker(raw))
    unknown = sorted({t for t in clean if t and t not in allowed})
    if unknown:
        raise ConfigValidationError(
            "analysis_subject tickers must be listed in config/etf_universe.yml or "
            f"config/stock_universe.yml; unknown={unknown}"
        )


def _default_subject_display(subject_type: str) -> str:
    return _SUBJECT_DEFAULT_DISPLAY.get(subject_type, "Analysis Subject")


def _is_generated_weight_source(source: str | None) -> bool:
    text = str(source or "")
    return "portfolio_weights.yml" in text or text.startswith("optimization_result")


def _analysis_subject_payload(
    *,
    subject_type: str,
    tickers: list[str],
    weights: dict[str, float] | None,
    weight_source: str,
    resolution_source: str,
    subject_id: str = "analysis_subject",
    display_name: str | None = None,
    notes: list[str] | None = None,
    warnings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    blockers: list[dict[str, Any]] = []
    clean_tickers = _clean_tickers(tickers)
    resolved_weights = positive_weights(weights)
    if not clean_tickers:
        blockers.append(
            {
                "code": "ANALYSIS_SUBJECT_TICKERS_EMPTY",
                "message": "analysis_subject requires at least one ticker.",
            }
        )
    if subject_type in ("current_portfolio", "model_portfolio") and not resolved_weights:
        blockers.append(
            {
                "code": "ANALYSIS_SUBJECT_WEIGHTS_MISSING",
                "message": f"analysis_subject.type={subject_type!r} requires positive weights.",
            }
        )
    if subject_type == "universe_baseline" and not resolved_weights:
        resolved_weights = _equal_weight_map(clean_tickers)
    status = "blocked" if blockers else "resolved"
    return {
        "version": ANALYSIS_SUBJECT_VERSION,
        "id": subject_id or "analysis_subject",
        "type": subject_type,
        "display_name": display_name or _default_subject_display(subject_type),
        "tickers": clean_tickers,
        "ticker_count": len(clean_tickers),
        "weights": _rounded_weight_map(resolved_weights),
        "weight_status": weight_status(resolved_weights),
        "weight_source": weight_source,
        "portfolio_role": _SUBJECT_PORTFOLIO_ROLE.get(subject_type, "unresolved"),
        "product_input_case": _SUBJECT_PRODUCT_INPUT_CASE.get(subject_type, "legacy_or_unknown"),
        "recommendation_status": _SUBJECT_RECOMMENDATION_STATUS.get(
            subject_type, "not_recommendation"
        ),
        "resolution_source": resolution_source,
        "resolution_status": status,
        "blocking_errors": blockers,
        "warnings": list(warnings or []),
        "notes": list(notes or []),
    }


def resolve_analysis_subject(
    cfg: PortfolioConfig,
    *,
    portfolio_weights: dict[str, float] | None = None,
    weights_source: str | None = None,
    portfolio_role_override: str | None = None,
) -> dict[str, Any]:
    """Resolve the portfolio-first subject without loading files or mutating config."""
    explicit = getattr(cfg, "analysis_subject", {}) or {}
    if isinstance(explicit, dict) and explicit.get("type"):
        subject_type = str(explicit.get("type")).strip().lower()
        tickers = _clean_tickers(explicit.get("tickers") or list(getattr(cfg, "tickers", []) or []))
        weights = dict(explicit.get("weights") or {})
        if subject_type == "universe_baseline" and not weights:
            weights = _equal_weight_map(tickers)
        source = (
            "system.analysis_subject.equal_weight_baseline"
            if subject_type == "universe_baseline"
            else "config.analysis_subject.weights"
        )
        return _analysis_subject_payload(
            subject_type=subject_type,
            subject_id=str(explicit.get("id") or "analysis_subject"),
            display_name=str(explicit.get("display_name") or "").strip() or None,
            tickers=tickers,
            weights=weights,
            weight_source=source,
            resolution_source="config.analysis_subject",
            notes=["explicit analysis_subject takes precedence over compatibility inference"],
        )

    if portfolio_role_override == "user_current_portfolio" and positive_weights(portfolio_weights):
        return _analysis_subject_payload(
            subject_type="current_portfolio",
            tickers=list((portfolio_weights or {}).keys()),
            weights=portfolio_weights,
            weight_source=weights_source or "config.current_weights",
            resolution_source="runtime.portfolio_role_override",
            notes=["materialized current portfolio sidecar resolved as analysis_subject"],
        )

    analysis_mode = getattr(cfg, "analysis_mode", "optimize_from_universe")
    current_weights = dict(getattr(cfg, "current_weights", {}) or {})
    cfg_weights = dict(getattr(cfg, "weights", {}) or {})
    effective_source = weights_source or getattr(cfg, "weights_source", "none")

    if analysis_mode == "analyze_current_weights" and positive_weights(current_weights):
        return _analysis_subject_payload(
            subject_type="current_portfolio",
            tickers=list(getattr(cfg, "tickers", []) or []),
            weights=current_weights,
            weight_source="config.current_weights",
            resolution_source="compat.analysis_mode.analyze_current_weights",
        )

    if (
        positive_weights(cfg_weights)
        and str(getattr(cfg, "weights_source", "")) == "config.weights"
        and not _is_generated_weight_source(effective_source)
    ):
        return _analysis_subject_payload(
            subject_type="model_portfolio",
            tickers=list(getattr(cfg, "tickers", []) or []),
            weights=cfg_weights,
            weight_source="config.weights",
            resolution_source="compat.legacy_fixed_weights",
            notes=["legacy fixed report weights are treated as a model_portfolio subject"],
        )

    warnings: list[dict[str, Any]] = []
    if analysis_mode == "optimize_from_universe" and positive_weights(current_weights):
        warnings.append(
            {
                "code": "CURRENT_WEIGHTS_CONTEXT_NOT_DEFAULT_SUBJECT",
                "message": (
                    "current_weights are available as legacy policy-context input, but without an "
                    "explicit analysis_subject or materialization override the default subject is the universe baseline."
                ),
            }
        )
    if _is_generated_weight_source(effective_source):
        warnings.append(
            {
                "code": "GENERATED_POLICY_WEIGHTS_NOT_ANALYSIS_SUBJECT",
                "message": "Generated policy weights remain legacy report inputs and are not the default analysis_subject.",
            }
        )

    return _analysis_subject_payload(
        subject_type="universe_baseline",
        tickers=list(getattr(cfg, "tickers", []) or []),
        weights=_equal_weight_map(list(getattr(cfg, "tickers", []) or [])),
        weight_source="system.equal_weight_universe_baseline",
        resolution_source="compat.analysis_mode.optimize_from_universe",
        warnings=warnings,
        notes=["default portfolio-first subject inferred from configured ticker universe"],
    )


def _same_number(left: Any, right: Any) -> bool:
    try:
        return abs(float(left) - float(right)) <= 1e-12
    except (TypeError, ValueError):
        return False


def _mandate_source(cfg: PortfolioConfig, field_name: str, value: Any) -> str:
    if value is None:
        return "not_set"
    profile = getattr(cfg, "client_profile", None)
    defaults = get_profile_defaults(profile) if profile else {}
    if field_name in defaults and _same_number(value, defaults[field_name]):
        return "profile_preset"
    if field_name in ("allow_leverage", "allow_short_selling") and value is False:
        return "system_default"
    return "user_override_or_config"


def _mandate_entry(
    cfg: PortfolioConfig,
    field_name: str,
    *,
    enforcement: str,
    applies_to: list[str],
) -> dict[str, Any]:
    value = getattr(cfg, field_name, None)
    return {
        "value": value,
        "source": _mandate_source(cfg, field_name, value),
        "enforcement": enforcement,
        "applies_to": applies_to,
    }


def _effective_covariance_method(cfg: PortfolioConfig) -> str:
    if getattr(cfg, "covariance_shrinkage", False):
        return "sample_covariance_with_ledoit_wolf_shrinkage"
    return "sample_covariance"


def _product_input_case(
    analysis_mode: str,
    current_weights: dict[str, float],
    analysis_subject: dict[str, Any] | None = None,
) -> str:
    if isinstance(analysis_subject, dict) and analysis_subject.get("product_input_case"):
        return str(analysis_subject["product_input_case"])
    if analysis_mode == "analyze_current_weights" and positive_weights(current_weights):
        return "user_current"
    if analysis_mode == "optimize_from_universe" and positive_weights(current_weights):
        return "construction_from_universe_with_current_context"
    if analysis_mode == "optimize_from_universe":
        return "universe_only"
    return "legacy_or_unknown"


def _analysis_portfolio(
    cfg: PortfolioConfig,
    *,
    portfolio_weights: dict[str, float] | None,
    weights_source: str | None,
    cash_proxy_ticker: str | None,
    analysis_subject: dict[str, Any] | None = None,
    portfolio_role_override: str | None = None,
) -> dict[str, Any]:
    analysis_mode = getattr(cfg, "analysis_mode", "optimize_from_universe")
    current_weights = dict(getattr(cfg, "current_weights", {}) or {})
    effective_source = weights_source or getattr(cfg, "weights_source", "unknown")
    effective_weights = dict(portfolio_weights if portfolio_weights is not None else (cfg.weights or {}))

    role = "unresolved"
    recommendation_status = "not_recommendation"
    notes: list[str] = []
    resolved_weights: dict[str, float] = {}

    if (
        portfolio_role_override == "analysis_subject"
        and isinstance(analysis_subject, dict)
        and analysis_subject.get("resolution_status") == "resolved"
        and positive_weights(analysis_subject.get("weights") or effective_weights)
    ):
        role = str(analysis_subject.get("portfolio_role") or "unresolved")
        effective_source = str(analysis_subject.get("weight_source") or effective_source)
        resolved_weights = dict(analysis_subject.get("weights") or effective_weights)
        recommendation_status = str(
            analysis_subject.get("recommendation_status") or "not_recommendation"
        )
        notes.append("materialized analysis_subject diagnostics sidecar")
    elif portfolio_role_override == "user_current_portfolio" and positive_weights(effective_weights):
        role = "user_current_portfolio"
        effective_source = weights_source or "config.current_weights"
        resolved_weights = effective_weights
        recommendation_status = "diagnostic_current_portfolio_not_recommendation"
        notes.append("materialized current portfolio sidecar for current-vs-policy comparison")
    elif (
        isinstance(analysis_subject, dict)
        and analysis_subject.get("resolution_status") == "resolved"
        and str(effective_source).startswith(("config.analysis_subject", "system.analysis_subject"))
    ):
        role = str(analysis_subject.get("portfolio_role") or "unresolved")
        effective_source = str(analysis_subject.get("weight_source") or effective_source)
        resolved_weights = dict(analysis_subject.get("weights") or {})
        recommendation_status = str(
            analysis_subject.get("recommendation_status") or "not_recommendation"
        )
        notes.append("analysis_portfolio mirrors explicit analysis_subject for this run")
    elif analysis_mode == "analyze_current_weights" and positive_weights(current_weights):
        role = "user_current_portfolio"
        effective_source = "config.current_weights"
        resolved_weights = current_weights
        recommendation_status = "diagnostic_current_portfolio_not_recommendation"
    elif analysis_mode == "analyze_current_weights" and positive_weights(effective_weights):
        role = "legacy_fixed_report_portfolio"
        resolved_weights = effective_weights
        recommendation_status = "fixed_report_portfolio_not_recommendation"
        notes.append("legacy weights are accepted for backward-compatible fixed-weight reporting")
    elif positive_weights(effective_weights):
        resolved_weights = effective_weights
        if "portfolio_weights.yml" in str(effective_source) or str(effective_source).startswith("optimization_result"):
            role = "generated_policy_portfolio"
            recommendation_status = (
                "generated_policy_output_released"
                if str(effective_source) == "optimization_result_released"
                else "generated_policy_output_not_user_input"
            )
        elif effective_source == "config.weights":
            role = "legacy_fixed_report_portfolio"
            recommendation_status = "fixed_report_portfolio_not_recommendation"
        else:
            role = "fixed_report_portfolio"
            recommendation_status = "fixed_report_portfolio_not_recommendation"
    else:
        role = "equal_weight_initial_baseline"
        effective_source = "system.equal_weight_initial_baseline"
        resolved_weights = _equal_weight_map(list(getattr(cfg, "tickers", []) or []))
        recommendation_status = "baseline_not_recommendation"
        notes.append(
            "target MVP universe-only baseline; current CLI report flow still requires fixed or generated weights"
        )

    from src.real_cash import enrich_cash_handling

    cash_proxy = str(cash_proxy_ticker or getattr(cfg, "cash_proxy_ticker", "") or "")
    positive = positive_weights(resolved_weights)
    total = float(sum(positive.values()))
    cash_weight = float(positive.get(cash_proxy, 0.0)) if cash_proxy else 0.0

    cash_handling = enrich_cash_handling(
        {
            "cash_proxy_ticker": cash_proxy or None,
            "cash_proxy_weight": _round_weight(cash_weight),
            "unallocated_weight_gap": _round_weight(max(0.0, 1.0 - total)),
            "cash_proxy_is_explicit_weight": bool(cash_proxy and cash_proxy in positive),
        },
        resolved_weights=positive,
        cash_proxy_ticker=cash_proxy or None,
    )

    return {
        "portfolio_role": role,
        "weight_source": effective_source,
        "weights": _rounded_weight_map(resolved_weights),
        "weight_status": weight_status(resolved_weights),
        "cash_handling": cash_handling,
        "recommendation_status": recommendation_status,
        "notes": notes,
    }


def _validation_result(
    cfg: PortfolioConfig,
    *,
    product_input_case: str,
    analysis_subject: dict[str, Any],
    analysis_portfolio: dict[str, Any],
) -> dict[str, Any]:
    warnings: list[dict[str, Any]] = []
    notices: list[dict[str, Any]] = [
        {
            "code": "INPUT_ASSUMPTIONS_IS_REPORT_VIEW",
            "message": "input_assumptions is exported from analysis_setup and must not be treated as a separate business-logic source.",
        },
        {
            "code": "HORIZON_METADATA_ONLY_V1",
            "message": "horizon_years is report/context metadata only in V1 and does not affect calculations.",
        },
    ]
    conflicts: list[dict[str, Any]] = [
        {
            "code": "UNIVERSE_ONLY_BASELINE_POLICY",
            "target_mvp_mode": "create equal_weight_initial_baseline before diagnostics",
            "current_repo_mode": "optimize_from_universe is optimizer-first; run_report requires fixed/generated weights unless SPEC/code is updated",
        },
    ]

    weight_state = (analysis_portfolio.get("weight_status") or {}).get("status")
    if weight_state in ("partial_with_cash_remainder", "overallocated"):
        warnings.append(
            {
                "code": "WEIGHT_SUM_NOT_FULLY_INVESTED",
                "message": "resolved analysis portfolio weights are not exactly fully invested; current behavior is documented but not changed here.",
                "weight_status": weight_state,
            }
        )
    if analysis_portfolio.get("portfolio_role") == "equal_weight_initial_baseline":
        notices.append(
            {
                "code": "EQUAL_WEIGHT_BASELINE_NOT_RECOMMENDATION",
                "message": "Equal Weight Initial Portfolio is a starting baseline, not a recommendation unless later selected by explicit candidate comparison.",
            }
        )

    status = "valid"
    blocking_errors = list(analysis_subject.get("blocking_errors") or [])
    for warning in analysis_subject.get("warnings") or []:
        warnings.append(dict(warning))
    if blocking_errors:
        status = "invalid"
    if warnings:
        status = "valid_with_action_required_warnings" if status != "invalid" else status

    return {
        "status": status,
        "blocking_errors": blocking_errors,
        "action_required_warnings": warnings,
        "informational_notices": notices,
        "legacy_current_repo_conflicts": conflicts,
        "product_input_case": product_input_case,
        "analysis_subject_status": analysis_subject.get("resolution_status"),
        "backward_compatibility": "preserved",
        "no_silent_behavior_change": True,
    }


def build_analysis_setup(
    cfg: PortfolioConfig,
    *,
    portfolio_weights: dict[str, float] | None = None,
    weights_source: str | None = None,
    cash_proxy_ticker: str | None = None,
    rf_source: str | None = None,
    local_benchmark_map: dict[str, str] | None = None,
    analysis_end: str | None = None,
    windows_months: list[int] | None = None,
    returns_frequency: str | None = None,
    periods_per_year: int | None = None,
    run_context: str | None = None,
    portfolio_role_override: str | None = None,
) -> dict[str, Any]:
    """Return the resolved runtime contract for the analysis input layer.

    This function is intentionally side-effect free. It summarizes already-resolved
    config/runtime values and does not load files, fetch data, mutate config, or
    release weights.
    """
    freq_res = resolve_returns_frequencies(
        returns_frequency or getattr(cfg, "returns_frequency", None)
    )
    frequency = freq_res.main_metrics
    configured_frequency = freq_res.configured
    window_values = list(windows_months if windows_months is not None else (cfg.windows_months or []))
    current_weights = dict(getattr(cfg, "current_weights", {}) or {})
    analysis_mode = getattr(cfg, "analysis_mode", "optimize_from_universe")
    analysis_subject = resolve_analysis_subject(
        cfg,
        portfolio_weights=portfolio_weights,
        weights_source=weights_source,
        portfolio_role_override=portfolio_role_override,
    )
    product_input_case = _product_input_case(analysis_mode, current_weights, analysis_subject)
    analysis_portfolio = _analysis_portfolio(
        cfg,
        portfolio_weights=portfolio_weights,
        weights_source=weights_source,
        cash_proxy_ticker=cash_proxy_ticker,
        analysis_subject=analysis_subject,
        portfolio_role_override=portfolio_role_override,
    )

    setup = {
        "version": ANALYSIS_SETUP_VERSION,
        "run_context": run_context,
        "portfolio_input": {
            "source_analysis_mode": analysis_mode,
            "product_input_case": product_input_case,
            "analysis_subject_id": analysis_subject.get("id"),
            "analysis_subject_type": analysis_subject.get("type"),
            "analysis_subject_resolution_source": analysis_subject.get("resolution_source"),
            "tickers": list(cfg.tickers),
            "selected_ticker_count": len(cfg.tickers),
            "current_weights_provided": bool(positive_weights(current_weights)),
            "current_weights": weight_status(current_weights),
            "investor_currency": cfg.investor_currency,
            "benchmark_request": "resolved_from_config_or_currency_default",
            "base_benchmark_ticker": cfg.benchmark_base_ticker,
            "risk_profile": cfg.client_profile,
            "investment_horizon_years": {
                "value": cfg.horizon_years,
                "role": "report_metadata",
                "affects_calculations": False,
            },
        },
        "analysis_subject": analysis_subject,
        "analysis_portfolio": analysis_portfolio,
        "resolved_mandate": {
            "client_profile": cfg.client_profile,
            "target_nominal_return_annual": _mandate_entry(
                cfg,
                "target_nominal_return_annual",
                enforcement="soft",
                applies_to=["optimizer_objective", "comparison", "reporting"],
            ),
            "target_vol_annual": _mandate_entry(
                cfg,
                "target_vol_annual",
                enforcement="soft",
                applies_to=["optimizer_objective", "comparison", "reporting"],
            ),
            "target_max_drawdown_pct": _mandate_entry(
                cfg,
                "target_max_drawdown_pct",
                enforcement="mandate_gate",
                applies_to=["optimization_release", "diagnostics", "reporting"],
            ),
            "min_acceptable_return": _mandate_entry(
                cfg,
                "min_acceptable_return",
                enforcement="soft",
                applies_to=["reporting"],
            ),
            "max_single_security_weight_pct": _mandate_entry(
                cfg,
                "max_single_security_weight_pct",
                enforcement="hard",
                applies_to=["optimizer", "candidate_factory"],
            ),
            "min_single_security_weight_pct": _mandate_entry(
                cfg,
                "min_single_security_weight_pct",
                enforcement="hard",
                applies_to=["optimizer", "candidate_factory"],
            ),
            "allow_leverage": _mandate_entry(
                cfg,
                "allow_leverage",
                enforcement="hard",
                applies_to=["optimizer", "candidate_factory", "validation"],
            ),
            "allow_short_selling": _mandate_entry(
                cfg,
                "allow_short_selling",
                enforcement="hard",
                applies_to=["optimizer", "candidate_factory", "validation"],
            ),
            "cash_policy": {
                "value": cfg.cash_policy,
                "source": "user_override_or_config",
                "enforcement": "hard",
                "applies_to": ["optimizer", "portfolio_construction", "reporting"],
            },
            "liquidity_need_months": {
                "value": cfg.liquidity_need_months,
                "source": "user_override_or_config",
                "enforcement": "hard_when_cash_floor_applies",
                "applies_to": ["optimizer", "portfolio_construction"],
            },
            "monthly_expenses": {
                "value": cfg.monthly_expenses,
                "source": "user_override_or_config",
                "enforcement": "hard_when_cash_floor_applies",
                "applies_to": ["optimizer", "portfolio_construction"],
            },
            "portfolio_value": {
                "value": cfg.portfolio_value,
                "source": "user_override_or_config",
                "enforcement": "input_context",
                "applies_to": ["liquidity_floor_resolution"],
            },
        },
        "resolved_assumptions": {
            "analysis_end": analysis_end,
            "analysis_windows": window_values,
            "primary_window_months": cfg.primary_window_months,
            "secondary_window_months": cfg.secondary_window_months,
            "return_frequency": frequency,
            "configured_return_frequency": configured_frequency,
            "main_metrics_return_frequency_forced": freq_res.forced_to_monthly,
            "periods_per_year": periods_per_year,
            "expected_return_method": "historical_baseline",
            "covariance_method": _effective_covariance_method(cfg),
            "risk_free_rate": {
                "source": rf_source or cfg.rf_source,
                "resolution_policy": "config_or_currency_default",
            },
            "cash_proxy": {
                "ticker": cash_proxy_ticker or cfg.cash_proxy_ticker,
                "resolution_policy": "config_or_currency_default",
            },
            "base_benchmark_ticker": cfg.benchmark_base_ticker,
            "local_benchmark_map": dict(local_benchmark_map or cfg.local_benchmark_map or {}),
            "missing_data_policy": cfg.backtest_mode,
            "coverage_threshold": cfg.coverage_threshold,
            "young_etf_optimization_policy": dict(cfg.young_etf_optimization_policy or {}),
            "transaction_cost_bps": {
                "value": None,
                "current_repo_status": "not_implemented",
                "target_mvp_default": 10,
            },
            "rebalance_frequency": {
                "value": None,
                "current_repo_status": "not_implemented",
                "target_mvp_default": "quarterly",
            },
            "stress_severity": {
                "value": "standard",
                "current_repo_status": "implicit_current_scenario_set",
            },
        },
    }
    setup["validation_result"] = _validation_result(
        cfg,
        product_input_case=product_input_case,
        analysis_subject=analysis_subject,
        analysis_portfolio=analysis_portfolio,
    )
    return setup


__all__ = [
    "ANALYSIS_SETUP_VERSION",
    "ANALYSIS_SUBJECT_VERSION",
    "build_analysis_setup",
    "positive_weights",
    "preflight_explicit_analysis_subject_tickers",
    "resolve_analysis_subject",
    "weight_status",
]
