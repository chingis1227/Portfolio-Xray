"""Exported Input & Assumptions view projected from Analysis Setup."""
from __future__ import annotations

from typing import Any

from src.analysis_setup import build_analysis_setup, weight_status
from src.config_schema import PortfolioConfig
from src.data_trust_signals import build_input_data_trust_signals


def _mandate_value(analysis_setup: dict[str, Any], key: str) -> Any:
    entry = (analysis_setup.get("resolved_mandate") or {}).get(key)
    if isinstance(entry, dict):
        return entry.get("value")
    return entry


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

    return {
        "version": "input_assumptions_v1",
        "source_analysis_setup_version": analysis_setup.get("version"),
        "run_context": analysis_setup.get("run_context"),
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
        "data_trust_signals": build_input_data_trust_signals(
            young_etf_optimization_policy=dict(
                resolved_assumptions.get("young_etf_optimization_policy") or {}
            ),
            validation_result=validation_result,
        ),
    }


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
    "build_input_assumptions_from_analysis_setup",
    "build_input_assumptions_summary",
]
