"""Exported Input & Assumptions view projected from Analysis Setup."""
from __future__ import annotations

from typing import Any, Literal

from src.analysis_setup import (
    CORE_MVP_REQUIRED_INPUT_GROUPS,
    LEGACY_ADVANCED_MANDATE_FIELDS,
    build_analysis_setup,
    weight_status,
)
from src.config_schema import PortfolioConfig
from src.data_trust_signals import build_input_data_trust_signals
from src.review_bundle_context import (
    input_assumptions_review_summary_lines,
    merge_review_bundle_into_input_trust_lines,
    mode_subject_summary_from_analysis_setup,
)


INPUT_SURFACE_VERSION = "input_surface_v1"
FIELD_TIERS_VERSION = "field_tiers_v1"

InputSurfaceProfile = Literal["core_mvp", "legacy_advanced"]

TIER_DEFINITIONS: dict[str, str] = {
    "core_mvp": "Required user input for portfolio-first Core MVP (tickers, weights, investor_currency).",
    "system_default": "Resolved from currency/config or injected for Core MVP (RF, benchmark, cash proxy, analysis_subject).",
    "client_fit_v1": "Implemented Client Fit V1 display/context inputs (profile, targets, horizon).",
    "risk_guardrail_later": "Liquidity suitability after diagnosis (months, expenses).",
    "candidate_builder": "Alternative portfolio construction (caps, cash_policy, leverage flags).",
    "assumption_testing": "Sensitivity / advanced technical settings (windows, frequency overrides).",
    "legacy_advanced": "Legacy policy optimizer and full config UI advanced panel.",
}

FIELD_TIER_REGISTRY: dict[str, str] = {
    "tickers": "core_mvp",
    "weights": "core_mvp",
    "current_weights": "core_mvp",
    "analysis_subject.weights": "core_mvp",
    "investor_currency": "core_mvp",
    "analysis_mode": "system_default",
    "analysis_subject": "system_default",
    "analysis_subject.type": "system_default",
    "analysis_subject.id": "system_default",
    "analysis_subject.display_name": "system_default",
    "analysis_subject.tickers": "system_default",
    "initial_investable_amount": "risk_guardrail_later",
    "portfolio_value": "risk_guardrail_later",
    "client_fit": "client_fit_v1",
    "client_profile": "client_fit_v1",
    "target_nominal_return_annual": "client_fit_v1",
    "target_vol_annual": "client_fit_v1",
    "target_max_drawdown_pct": "client_fit_v1",
    "min_acceptable_return": "client_fit_v1",
    "horizon_years": "client_fit_v1",
    "liquidity_need_months": "risk_guardrail_later",
    "monthly_expenses": "risk_guardrail_later",
    "liquidity_need": "risk_guardrail_later",
    "cash_policy": "candidate_builder",
    "allow_leverage": "candidate_builder",
    "allow_short_selling": "candidate_builder",
    "max_single_security_weight_pct": "candidate_builder",
    "min_single_security_weight_pct": "candidate_builder",
    "risk_free_source": "system_default",
    "rf_source": "system_default",
    "cash_proxy_ticker": "system_default",
    "base_benchmark_ticker": "system_default",
    "benchmark_base_ticker": "system_default",
    "local_benchmark_map": "system_default",
    "market_data_provider": "assumption_testing",
    "windows_months": "assumption_testing",
    "returns_frequency": "assumption_testing",
    "coverage_threshold": "assumption_testing",
    "backtest_mode": "assumption_testing",
    "primary_window_months": "assumption_testing",
    "secondary_window_months": "assumption_testing",
    "optimization_windows_months": "assumption_testing",
    "robustness_policy": "assumption_testing",
    "covariance_shrinkage": "assumption_testing",
    "young_etf_optimization_policy": "assumption_testing",
    "output_dir": "assumption_testing",
    "output_dir_final": "assumption_testing",
    "beta_local_mapping": "assumption_testing",
    "N_rc": "legacy_advanced",
    "donor_shift_mode": "legacy_advanced",
    "optimization_soft_vol_penalty_lambda": "legacy_advanced",
    "optimization_soft_return_penalty_lambda": "legacy_advanced",
    "minimum_variance_turnover_lambda": "legacy_advanced",
    "strict_stress_gate": "legacy_advanced",
}


def _mandate_value(analysis_setup: dict[str, Any], key: str) -> Any:
    entry = (analysis_setup.get("resolved_mandate") or {}).get(key)
    if isinstance(entry, dict):
        return entry.get("value")
    return entry


def _mandate_entry_source(analysis_setup: dict[str, Any], key: str) -> str | None:
    entry = (analysis_setup.get("resolved_mandate") or {}).get(key)
    if isinstance(entry, dict):
        return str(entry.get("source") or "")
    return None


def _mandate_entry_populated(analysis_setup: dict[str, Any], key: str) -> bool:
    source = _mandate_entry_source(analysis_setup, key)
    if source in (None, "", "not_set"):
        return False
    value = _mandate_value(analysis_setup, key)
    if value is None:
        return False
    if isinstance(value, (int, float)) and key in (
        "liquidity_need_months",
        "monthly_expenses",
        "portfolio_value",
    ):
        return float(value) > 0
    if isinstance(value, bool) and key in ("allow_leverage", "allow_short_selling"):
        return value is True
    if isinstance(value, str) and key == "cash_policy":
        return value.strip().lower() not in ("", "none")
    return True


def _positive_weight_sum(status: dict[str, Any] | None) -> bool:
    if not isinstance(status, dict):
        return False
    if status.get("has_weights"):
        return True
    try:
        return float(status.get("weight_sum") or 0.0) > 0
    except (TypeError, ValueError):
        return False


def _user_allocation_supplied(analysis_setup: dict[str, Any]) -> bool:
    portfolio_input = analysis_setup.get("portfolio_input") or {}
    analysis_subject = analysis_setup.get("analysis_subject") or {}
    subject_type = str(analysis_subject.get("type") or "")

    if portfolio_input.get("current_weights_provided"):
        return True
    if subject_type in ("current_portfolio", "model_portfolio"):
        return _positive_weight_sum(analysis_subject.get("weight_status"))
    return False


def _infer_input_surface_profile(analysis_setup: dict[str, Any]) -> InputSurfaceProfile:
    portfolio_input = analysis_setup.get("portfolio_input") or {}
    analysis_subject = analysis_setup.get("analysis_subject") or {}
    analysis_mode = str(portfolio_input.get("source_analysis_mode") or "")
    subject_type = str(analysis_subject.get("type") or "")

    has_user_allocation = _user_allocation_supplied(analysis_setup)
    if analysis_mode == "analyze_current_weights" and has_user_allocation:
        return "core_mvp"
    if subject_type in ("current_portfolio", "model_portfolio") and has_user_allocation:
        return "core_mvp"
    return "legacy_advanced"


def _allocation_source_label(analysis_setup: dict[str, Any]) -> str:
    portfolio_input = analysis_setup.get("portfolio_input") or {}
    analysis_subject = analysis_setup.get("analysis_subject") or {}
    analysis_portfolio = analysis_setup.get("analysis_portfolio") or {}

    if portfolio_input.get("current_weights_provided"):
        return "current_weights"
    weight_source = str(
        analysis_subject.get("weight_source")
        or analysis_portfolio.get("weight_source")
        or "unknown"
    )
    if weight_source.startswith("config.analysis_subject"):
        return "analysis_subject.weights"
    if weight_source == "config.current_weights":
        return "current_weights"
    if weight_source == "config.weights":
        return "weights"
    return weight_source


def build_input_surface(analysis_setup: dict[str, Any]) -> dict[str, Any]:
    """Disclose which product input surface applies and what the user supplied on the first screen."""
    portfolio_input = analysis_setup.get("portfolio_input") or {}
    analysis_subject = analysis_setup.get("analysis_subject") or {}
    analysis_portfolio = analysis_setup.get("analysis_portfolio") or {}
    cash_handling = analysis_portfolio.get("cash_handling") or {}

    profile = _infer_input_surface_profile(analysis_setup)
    resolution_source = str(analysis_subject.get("resolution_source") or "")
    compat_injected = resolution_source.startswith("compat.")

    allocation_supplied = _user_allocation_supplied(analysis_setup)
    ticker_count = int(portfolio_input.get("selected_ticker_count") or 0)

    notes: list[str] = []
    if profile == "core_mvp":
        notes.append(
            "Core MVP portfolio-first path: only tickers, allocation, and investor_currency are "
            "required on the first screen; other fields are system-resolved or deferred layers."
        )
    else:
        notes.append(
            "Legacy or optimizer-first path: universe baseline or policy optimization may apply; "
            "see analysis_mode and analysis_subject for weight semantics."
        )
    if compat_injected:
        notes.append(
            f"Compatibility resolver applied analysis_subject from {resolution_source}."
        )

    return {
        "version": INPUT_SURFACE_VERSION,
        "profile": profile,
        "product_path": (
            "portfolio_first_diagnosis"
            if profile == "core_mvp"
            else "legacy_policy_or_universe_baseline"
        ),
        "first_screen": {
            "tickers": {
                "tier": "core_mvp",
                "required": True,
                "supplied": ticker_count > 0,
                "configured_ticker_count": ticker_count,
            },
            "allocation": {
                "tier": "core_mvp",
                "required": True,
                "supplied": allocation_supplied,
                "source": _allocation_source_label(analysis_setup),
            },
            "investor_currency": {
                "tier": "core_mvp",
                "required": True,
                "supplied": bool(str(portfolio_input.get("investor_currency") or "").strip()),
                "value": portfolio_input.get("investor_currency"),
            },
        },
        "core_mvp_requirements_met": (
            ticker_count > 0
            and allocation_supplied
            and bool(str(portfolio_input.get("investor_currency") or "").strip())
        ),
        "system_injected": {
            "analysis_mode": portfolio_input.get("source_analysis_mode"),
            "analysis_subject_type": analysis_subject.get("type"),
            "resolution_source": resolution_source or None,
            "compat_resolver_applied": compat_injected,
        },
        "real_cash": {
            "holdings": list(cash_handling.get("real_cash_holdings") or []),
            "weight_total": cash_handling.get("real_cash_weight_total", 0.0),
            "distinct_from_cash_proxy": bool(cash_handling.get("real_cash_distinct_from_cash_proxy")),
            "return_assumption": cash_handling.get("real_cash_return_assumption"),
        },
        "notes": notes,
    }


def build_field_tiers(
    analysis_setup: dict[str, Any],
    *,
    input_surface: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Export field tier registry plus per-run populated/disclosure summary."""
    portfolio_input = analysis_setup.get("portfolio_input") or {}
    resolved_mandate = analysis_setup.get("resolved_mandate") or {}
    resolved_assumptions = analysis_setup.get("resolved_assumptions") or {}
    profile = _infer_input_surface_profile(analysis_setup)

    user_configured: list[str] = []
    populated_by_tier: dict[str, list[str]] = {tier: [] for tier in TIER_DEFINITIONS}

    def _mark(field: str, *, tier: str | None = None, user_configured_flag: bool = False) -> None:
        resolved_tier = tier or FIELD_TIER_REGISTRY.get(field, "legacy_advanced")
        if field not in populated_by_tier[resolved_tier]:
            populated_by_tier[resolved_tier].append(field)
        if user_configured_flag and field not in user_configured:
            user_configured.append(field)

    if portfolio_input.get("selected_ticker_count", 0) > 0:
        _mark("tickers")
    if portfolio_input.get("current_weights_provided"):
        _mark("current_weights", user_configured_flag=True)
    if _user_allocation_supplied(analysis_setup):
        _mark("analysis_subject.weights", user_configured_flag=True)
    if str(portfolio_input.get("investor_currency") or "").strip():
        _mark("investor_currency")

    _mark("analysis_mode")
    if (analysis_setup.get("analysis_subject") or {}).get("type"):
        _mark("analysis_subject.type")

    client_profile = resolved_mandate.get("client_profile")
    if client_profile:
        _mark("client_profile", user_configured_flag=True)

    if resolved_assumptions.get("base_benchmark_ticker"):
        _mark("base_benchmark_ticker")
    cash_proxy = (resolved_assumptions.get("cash_proxy") or {}).get("ticker")
    if cash_proxy:
        _mark("cash_proxy_ticker")
    rf = (resolved_assumptions.get("risk_free_rate") or {}).get("source")
    if rf:
        _mark("risk_free_source")

    for key in (
        "client_profile",
        "target_nominal_return_annual",
        "target_vol_annual",
        "target_max_drawdown_pct",
        "min_acceptable_return",
        "max_single_security_weight_pct",
        "min_single_security_weight_pct",
        "allow_leverage",
        "allow_short_selling",
        "cash_policy",
        "liquidity_need_months",
        "monthly_expenses",
        "portfolio_value",
    ):
        if not _mandate_entry_populated(analysis_setup, key):
            continue
        _mark(key, user_configured_flag=_mandate_entry_source(analysis_setup, key) in (
            "user_override_or_config",
            "profile_preset",
        ))

    horizon = (portfolio_input.get("investment_horizon_years") or {}).get("value")
    if horizon is not None:
        _mark("horizon_years", user_configured_flag=True)

    if resolved_assumptions.get("analysis_windows"):
        _mark("windows_months")
    if resolved_assumptions.get("configured_return_frequency"):
        freq = resolved_assumptions.get("configured_return_frequency")
        if freq and freq != "monthly":
            _mark("returns_frequency", user_configured_flag=True)
    if resolved_assumptions.get("missing_data_policy"):
        _mark("backtest_mode")
    if resolved_assumptions.get("coverage_threshold") is not None:
        _mark("coverage_threshold")
    if resolved_assumptions.get("covariance_method") == "sample_covariance_with_ledoit_wolf_shrinkage":
        _mark("covariance_shrinkage", user_configured_flag=True)
    young = resolved_assumptions.get("young_etf_optimization_policy") or {}
    if isinstance(young, dict) and young.get("enabled"):
        _mark("young_etf_optimization_policy", user_configured_flag=True)

    deferred_tiers_present = [
        tier
        for tier in (
            "client_fit_v1",
            "risk_guardrail_later",
            "candidate_builder",
            "assumption_testing",
            "legacy_advanced",
        )
        if populated_by_tier.get(tier)
    ]

    surface = input_surface if input_surface is not None else build_input_surface(analysis_setup)
    first_screen = surface.get("first_screen") or {}
    core_user_supplied = [
        key
        for key in ("tickers", "allocation", "investor_currency")
        if isinstance(first_screen.get(key), dict) and first_screen[key].get("supplied")
    ]

    registry_payload: dict[str, Any] = dict(FIELD_TIER_REGISTRY)
    if profile == "core_mvp":
        registry_payload = {
            "_scope": {
                "tier": "legacy_advanced",
                "product_surface": False,
                "not_required_for_core_mvp": True,
                "consumer_guidance": (
                    "Field tier registry contains deferred/client-fit/legacy mapping hints. "
                    "For Core MVP product-facing surface use input_surface.core_mvp + "
                    "run_disclosure.core_mvp only."
                ),
            },
            **registry_payload,
        }

    return {
        "version": FIELD_TIERS_VERSION,
        "tier_definitions": dict(TIER_DEFINITIONS),
        "registry": registry_payload,
        "run_disclosure": {
            "input_surface_profile": profile,
            "core_mvp": {
                "required_field_keys": ["tickers", "allocation", "investor_currency"],
                "user_supplied": core_user_supplied,
                "requirements_met": surface.get("core_mvp_requirements_met"),
            },
            "populated_by_tier": populated_by_tier,
            "user_configured_fields": sorted(user_configured),
            "deferred_tiers_with_values": deferred_tiers_present,
            "client_profile": resolved_mandate.get("client_profile"),
        },
    }


def build_input_assumptions_from_analysis_setup(analysis_setup: dict[str, Any]) -> dict[str, Any]:
    """Project the report/export view from the resolved analysis setup contract."""
    portfolio_input = analysis_setup.get("portfolio_input") or {}
    analysis_subject = analysis_setup.get("analysis_subject") or {}
    analysis_portfolio = analysis_setup.get("analysis_portfolio") or {}
    resolved_assumptions = analysis_setup.get("resolved_assumptions") or {}
    validation_result = analysis_setup.get("validation_result") or {}
    current_weights_status = portfolio_input.get("current_weights")
    if not isinstance(current_weights_status, dict):
        current_weights_status = weight_status({})

    input_surface = build_input_surface(analysis_setup)
    field_tiers = build_field_tiers(analysis_setup, input_surface=input_surface)
    core_surface = analysis_setup.get("core_mvp_input_surface")
    if not isinstance(core_surface, dict):
        core_surface = {
            "required_user_input_groups": list(CORE_MVP_REQUIRED_INPUT_GROUPS),
            "core_mvp_requirements_met": input_surface.get("core_mvp_requirements_met"),
        }

    return {
        "version": "input_assumptions_v1",
        "source_analysis_setup_version": analysis_setup.get("version"),
        "run_context": analysis_setup.get("run_context"),
        "core_mvp_input_contract": {
            "source": "analysis_setup.core_mvp_input_surface",
            "product_surface": True,
            "required_user_input_groups": list(CORE_MVP_REQUIRED_INPUT_GROUPS),
            "fields": dict(core_surface.get("fields") or {}),
            "core_mvp_requirements_met": core_surface.get("core_mvp_requirements_met"),
            "excluded_legacy_advanced_fields": list(LEGACY_ADVANCED_MANDATE_FIELDS),
            "consumer_guidance": (
                "Core MVP UI/API consumers should use input_surface, field_tiers, and this "
                "core_mvp_input_contract. mandate_and_constraints is legacy/advanced disclosure only."
            ),
        },
        "portfolio_input": {
            "analysis_mode": portfolio_input.get("source_analysis_mode"),
            "product_input_case": portfolio_input.get("product_input_case"),
            "analysis_subject_id": portfolio_input.get("analysis_subject_id"),
            "analysis_subject_type": portfolio_input.get("analysis_subject_type"),
            "tickers": list(portfolio_input.get("tickers") or []),
            "configured_ticker_count": portfolio_input.get("selected_ticker_count", 0),
            "current_weights_provided": bool(portfolio_input.get("current_weights_provided")),
            "reported_weights_source": analysis_portfolio.get("weight_source", "unknown"),
            "reported_weights": analysis_portfolio.get("weight_status") or weight_status({}),
            "current_weights": current_weights_status,
            "analysis_portfolio_role": analysis_portfolio.get("portfolio_role"),
            "recommendation_status": analysis_portfolio.get("recommendation_status"),
            "weights_semantics": (
                "analysis_setup is the resolved runtime contract. input_assumptions is its exported "
                "reporting view. Current/input weights, initial baseline weights, generated/candidate "
                "weights, and selected/target weights must remain distinct."
            ),
        },
        "analysis_subject": {
            "id": analysis_subject.get("id"),
            "type": analysis_subject.get("type"),
            "display_name": analysis_subject.get("display_name"),
            "resolution_source": analysis_subject.get("resolution_source"),
            "resolution_status": analysis_subject.get("resolution_status"),
            "tickers": list(analysis_subject.get("tickers") or []),
            "ticker_count": analysis_subject.get("ticker_count", 0),
            "weight_source": analysis_subject.get("weight_source"),
            "weight_status": analysis_subject.get("weight_status") or weight_status({}),
            "portfolio_role": analysis_subject.get("portfolio_role"),
            "recommendation_status": analysis_subject.get("recommendation_status"),
        },
        "currency_and_market": {
            "investor_currency": portfolio_input.get("investor_currency"),
            "base_benchmark_ticker": resolved_assumptions.get("base_benchmark_ticker")
            or portfolio_input.get("base_benchmark_ticker"),
            "cash_proxy_ticker": (resolved_assumptions.get("cash_proxy") or {}).get("ticker"),
            "risk_free_source": (resolved_assumptions.get("risk_free_rate") or {}).get("source"),
            "local_benchmark_map": dict(resolved_assumptions.get("local_benchmark_map") or {}),
        },
        "mandate_and_constraints": {
            "_scope": {
                "tier": "legacy_advanced",
                "product_surface": False,
                "not_required_for_core_mvp": True,
                "consumer_guidance": (
                    "Do not use this block as the Core MVP input surface. It is retained for "
                    "legacy optimizer/client-fit/liquidity compatibility only."
                ),
            },
            "client_profile": (analysis_setup.get("resolved_mandate") or {}).get("client_profile"),
            "target_nominal_return_annual": _mandate_value(analysis_setup, "target_nominal_return_annual"),
            "target_vol_annual": _mandate_value(analysis_setup, "target_vol_annual"),
            "target_max_drawdown_pct": _mandate_value(analysis_setup, "target_max_drawdown_pct"),
            "min_acceptable_return": _mandate_value(analysis_setup, "min_acceptable_return"),
            "max_single_security_weight_pct": _mandate_value(analysis_setup, "max_single_security_weight_pct"),
            "min_single_security_weight_pct": _mandate_value(analysis_setup, "min_single_security_weight_pct"),
            "allow_leverage": _mandate_value(analysis_setup, "allow_leverage"),
            "allow_short_selling": _mandate_value(analysis_setup, "allow_short_selling"),
            "cash_policy": _mandate_value(analysis_setup, "cash_policy"),
            "liquidity_need_months": _mandate_value(analysis_setup, "liquidity_need_months"),
            "monthly_expenses": _mandate_value(analysis_setup, "monthly_expenses"),
            "portfolio_value": _mandate_value(analysis_setup, "portfolio_value"),
            "horizon_years": (portfolio_input.get("investment_horizon_years") or {}).get("value"),
            "horizon_role": "report_context_only_not_optimizer_constraint",
        },
        "calculation_assumptions": {
            "analysis_end": resolved_assumptions.get("analysis_end"),
            "windows_months": list(resolved_assumptions.get("analysis_windows") or []),
            "primary_window_months": resolved_assumptions.get("primary_window_months"),
            "secondary_window_months": resolved_assumptions.get("secondary_window_months"),
            "returns_frequency": resolved_assumptions.get("return_frequency"),
            "configured_returns_frequency": resolved_assumptions.get("configured_return_frequency"),
            "main_metrics_returns_frequency_forced": resolved_assumptions.get(
                "main_metrics_return_frequency_forced"
            ),
            "periods_per_year": resolved_assumptions.get("periods_per_year"),
            "coverage_threshold": resolved_assumptions.get("coverage_threshold"),
            "backtest_mode": resolved_assumptions.get("missing_data_policy"),
            "covariance_shrinkage": (
                resolved_assumptions.get("covariance_method")
                == "sample_covariance_with_ledoit_wolf_shrinkage"
            ),
            "covariance_method": resolved_assumptions.get("covariance_method"),
            "young_etf_optimization_policy": dict(
                resolved_assumptions.get("young_etf_optimization_policy") or {}
            ),
            "transaction_cost_bps": resolved_assumptions.get("transaction_cost_bps"),
            "rebalance_frequency": resolved_assumptions.get("rebalance_frequency"),
        },
        "validation_result": {
            "status": validation_result.get("status"),
            "legacy_current_repo_conflicts": list(
                validation_result.get("legacy_current_repo_conflicts") or []
            ),
        },
        "current_v1_gaps": {
            "transaction_costs": "not_implemented",
            "manual_ui_controls": "not_implemented_cli_file_driven",
            "investment_horizon_optimizer_effect": "not_implemented_report_context_only",
            "formal_selection_engine": "selection_decision_v1",
        },
        "review_bundle_disclosure": {
            "mode_subject_consistency": mode_subject_summary_from_analysis_setup(
                analysis_setup
            ),
        },
        "data_trust_signals": _build_input_data_trust_with_review_bundle(
            analysis_setup=analysis_setup,
            young_etf_optimization_policy=dict(
                resolved_assumptions.get("young_etf_optimization_policy") or {}
            ),
            validation_result=validation_result,
        ),
        "input_surface": input_surface,
        "field_tiers": field_tiers,
    }


def _build_input_data_trust_with_review_bundle(
    *,
    analysis_setup: dict[str, Any],
    young_etf_optimization_policy: dict[str, Any],
    validation_result: dict[str, Any],
) -> dict[str, Any]:
    trust = build_input_data_trust_signals(
        young_etf_optimization_policy=young_etf_optimization_policy,
        validation_result=validation_result,
    )
    review_lines = input_assumptions_review_summary_lines(analysis_setup)
    trust["user_summary_lines"] = merge_review_bundle_into_input_trust_lines(
        list(trust.get("user_summary_lines") or []),
        review_lines,
    )
    return trust


def build_input_assumptions_summary(
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
) -> dict[str, Any]:
    """Return the exported/reporting view of the resolved analysis setup."""
    analysis_setup = build_analysis_setup(
        cfg,
        portfolio_weights=portfolio_weights,
        weights_source=weights_source,
        cash_proxy_ticker=cash_proxy_ticker,
        rf_source=rf_source,
        local_benchmark_map=local_benchmark_map,
        analysis_end=analysis_end,
        windows_months=windows_months,
        returns_frequency=returns_frequency,
        periods_per_year=periods_per_year,
        run_context=run_context,
    )
    return build_input_assumptions_from_analysis_setup(analysis_setup)


__all__ = [
    "FIELD_TIER_REGISTRY",
    "FIELD_TIERS_VERSION",
    "INPUT_SURFACE_VERSION",
    "TIER_DEFINITIONS",
    "build_field_tiers",
    "build_input_assumptions_from_analysis_setup",
    "build_input_assumptions_summary",
    "build_input_surface",
]
