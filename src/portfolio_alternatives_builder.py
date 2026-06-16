"""On-demand Portfolio Alternatives Builder wrapper.

The builder turns a selected Launchpad method into an execution plan for one
existing candidate builder path. It does not implement formulas and does not
execute anything unless a caller explicitly runs the returned command.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

DEFAULT_ALTERNATIVES_OUTPUT_PROFILE = "site_api"
DEFAULT_ALTERNATIVES_EXECUTION_MODE = "standard"
PORTFOLIO_ALTERNATIVES_BUILDER_FILENAME = "portfolio_alternatives_builder.json"
PORTFOLIO_ALTERNATIVES_BUILDER_SCHEMA_VERSION = "portfolio_alternatives_builder_v1"

BUILDER_PREFILL_REQUIRED_FIELDS: tuple[str, ...] = (
    "builder_prefill_id",
    "source_card_id",
    "source_diagnosis_id",
    "source_problem_id",
    "card_type",
    "launch_status",
    "method_role",
    "hypothesis_to_test",
    "next_diagnostic_step",
    "goal",
    "suggested_method",
    "alternative_methods",
    "constraint_preset",
    "max_asset_weight",
    "min_asset_weight",
    "volatility_target",
    "rebalancing_frequency",
    "transaction_cost_bps",
    "success_criteria",
    "tradeoff_to_watch",
    "when_to_skip",
    "decision_boundary",
    "is_rebalance_recommendation",
    "created_from",
    "status",
    "warnings",
)

BUILDER_PREFILL_PROHIBITED_FIELDS = frozenset(
    {
        "candidate_id",
        "weights",
        "candidate_status",
        "comparison_status",
    }
)

BUILDER_PREFILL_ALLOWED_STATUSES = frozenset(
    {
        "ready_for_user_confirmation",
        "blocked",
        "monitor_only",
        "custom_draft",
    }
)

BUILDER_STRATEGY_GOAL_METHODS: dict[str, tuple[str, ...]] = {
    "improve_crisis_resilience": (
        "minimum_cvar",
        "maximum_diversification",
        "minimum_variance",
    ),
    "reduce_drawdown_risk": (
        "minimum_cvar",
        "minimum_variance",
        "risk_parity",
    ),
    "improve_diversification": (
        "risk_parity",
        "hierarchical_risk_parity",
        "maximum_diversification",
    ),
    "reduce_concentration": (
        "equal_weight",
        "risk_parity",
        "maximum_diversification",
    ),
    "reduce_volatility": (
        "minimum_variance",
        "risk_parity",
        "equal_weight",
    ),
    "reduce_equity_beta": (
        "minimum_variance",
        "risk_parity",
        "minimum_cvar",
    ),
    "reduce_duration_rates_sensitivity": (
        "minimum_cvar",
        "minimum_variance",
        "risk_parity",
    ),
    "improve_hedge_behavior": (
        "minimum_cvar",
        "maximum_diversification",
        "risk_parity",
    ),
    "reduce_tail_risk": (
        "minimum_cvar",
        "minimum_variance",
        "maximum_diversification",
    ),
    "reduce_credit_liquidity_risk": (
        "minimum_cvar",
        "minimum_variance",
        "risk_parity",
    ),
    "improve_return_risk_balance": (
        "maximum_diversification",
        "risk_parity",
        "minimum_variance",
    ),
    "compare_simple_benchmark": (
        "equal_weight",
        "risk_parity",
    ),
}

BUILDER_STRATEGY_GOAL_ALIASES: dict[str, str] = {
    "compare_against_simple_benchmark": "compare_simple_benchmark",
    "compare_against_simple_references": "compare_simple_benchmark",
    "compare_simple_references": "compare_simple_benchmark",
    "reduce_drawdown": "reduce_drawdown_risk",
    "reduce_duration_rates_sensitivity": "reduce_duration_rates_sensitivity",
    "reduce_duration_rates": "reduce_duration_rates_sensitivity",
    "improve_return_risk_balance": "improve_return_risk_balance",
}

BUILDER_STRATEGY_CONSTRAINT_HINTS: dict[str, dict[str, Any]] = {
    "reduce_concentration": {
        "constraint_preset": "custom",
        "max_asset_weight": 0.15,
        "min_asset_weight": 0.0,
    },
    "compare_simple_benchmark": {
        "constraint_preset": "basic_reference",
        "max_asset_weight": None,
        "min_asset_weight": None,
    },
}

SIMPLE_BUILDER_EDITABLE_FIELDS: tuple[str, ...] = (
    "goal",
    "method",
    "mode",
    "constraint_preset",
    "max_asset_weight",
    "min_asset_weight",
)

SIMPLE_BUILDER_ALLOWED_PRESETS = frozenset(
    {
        "conservative",
        "balanced",
        "aggressive",
        "custom",
        "basic_reference",
        "uncapped",
    }
)

SIMPLE_BUILDER_ALLOWED_MODES = frozenset({"capped", "uncapped"})

UNCAPPED_MODE_CONCENTRATION_WARNING = (
    "Uncapped mode may create concentrated portfolios. Use only for diagnostic "
    "comparison, not as an automatic rebalance recommendation."
)

CLIENT_FIT_OPTIMIZER_BOUNDARY_EN = (
    "Client Fit targets are shown only as hypothesis-test and display criteria. "
    "They do not change optimizer objectives, constraints, mandate gates, analysis "
    "windows, candidate weights, or factory commands in Client Fit V1."
)

CONSTRAINT_PRESETS: dict[str, dict[str, Any]] = {
    "conservative": {
        "min_asset_weight": 0.0,
        "max_asset_weight": 0.15,
        "mode": "capped",
        "capped": True,
    },
    "balanced": {
        "min_asset_weight": 0.0,
        "max_asset_weight": 0.20,
        "mode": "capped",
        "capped": True,
    },
    "aggressive": {
        "min_asset_weight": 0.0,
        "max_asset_weight": 0.30,
        "mode": "capped",
        "capped": True,
    },
    "basic_reference": {
        "min_asset_weight": None,
        "max_asset_weight": None,
        "mode": "capped",
        "capped": True,
    },
    "custom": {
        "min_asset_weight": None,
        "max_asset_weight": None,
        "mode": "capped",
        "capped": True,
    },
    "uncapped": {
        "min_asset_weight": 0.0,
        "max_asset_weight": None,
        "mode": "uncapped",
        "capped": False,
    },
}

SIMPLE_BUILDER_PROHIBITED_ADVANCED_FIELDS = frozenset(
    {
        "tax_aware_optimization",
        "turnover_aware_objective",
        "asset_class_bounds",
        "custom_risk_budgets",
        "robust_mv_lambda",
        "advanced_cvar_settings",
        "cvar_alpha",
        "cvar_confidence_level",
        "covariance_selector",
        "expected_return_model_selector",
        "volatility_target",
        "rebalancing_frequency",
        "transaction_cost_bps",
        "transaction_cost_assumption",
        "leverage",
        "shorting",
        "allow_shorting",
    }
)

BUILDER_VALIDATION_STATUSES = frozenset(
    {
        "valid",
        "blocked_by_data_quality",
        "invalid_method",
        "missing_goal",
        "missing_method",
        "invalid_constraints",
        "infeasible_constraints_risk",
        "reference_benchmark_boundary_violation",
    }
)

CANDIDATE_SETUP_REQUIRED_FIELDS: tuple[str, ...] = (
    "candidate_setup_id",
    "builder_prefill_id",
    "source_card_id",
    "source_diagnosis_id",
    "source_launchpad_card_type",
    "goal",
    "hypothesis_to_test",
    "selected_method",
    "original_suggested_method",
    "method_changed_by_user",
    "parameters",
    "constraints",
    "success_criteria",
    "tradeoff_to_watch",
    "when_to_skip",
    "decision_boundary",
    "is_rebalance_recommendation",
    "can_generate_candidate",
    "validation_status",
    "validation_warnings",
    "created_at",
)

CANDIDATE_SETUP_PROHIBITED_FIELDS = frozenset(
    {
        "candidate_id",
        "weights",
        "portfolio_metrics",
        "stress_results",
        "comparison",
        "verdict",
    }
)

# Guided Block 6 method ids are intentionally smaller than the backend factory
# menu. They are product-facing setup choices, not optimizer internals.
GUIDED_METHOD_TO_CANDIDATE_ID_BY_MODE: dict[str, dict[str, str]] = {
    "equal_weight": {"capped": "equal_weight", "uncapped": "equal_weight"},
    "risk_parity": {"capped": "risk_parity", "uncapped": "risk_parity"},
    "hierarchical_risk_parity": {
        "capped": "hierarchical_risk_parity",
        "uncapped": "hierarchical_risk_parity",
    },
    "minimum_variance": {
        "capped": "minimum_variance",
        "uncapped": "minimum_variance_uncapped",
    },
    "minimum_cvar": {
        "capped": "minimum_cvar_constrained",
        "uncapped": "minimum_cvar_uncapped",
    },
    "maximum_diversification": {
        "capped": "maximum_diversification",
        "uncapped": "maximum_diversification_uncapped",
    },
}

GUIDED_METHODS = frozenset(GUIDED_METHOD_TO_CANDIDATE_ID_BY_MODE)

METHOD_ALIASES: dict[str, str] = {
    "minimum_cvar_constrained": "minimum_cvar",
    "minimum_cvar_uncapped": "minimum_cvar",
    "minimum_variance_uncapped": "minimum_variance",
    "maximum_diversification_uncapped": "maximum_diversification",
}

# Hidden backend methods remain callable by explicit legacy helpers, but are not
# accepted by guided Block 6 validation and are not shown by the strategy menu.
HIDDEN_METHOD_CLASSIFICATIONS: dict[str, str] = {
    "equal_weight_by_asset_class": "advanced_hidden",
    "risk_budget_by_asset": "advanced_hidden",
    "risk_budget_by_asset_class": "advanced_hidden",
    "minimum_variance_advanced": "advanced_hidden",
    "robust_mv_constrained": "advanced_hidden",
    "robust_mv_uncapped": "advanced_hidden",
    "robust_scenario": "advanced_hidden",
    "legacy_policy_optimizer": "legacy_supported",
}

LEGACY_METHOD_TO_CANDIDATE_ID: dict[str, str] = {
    "equal_weight": "equal_weight",
    "equal_weight_by_asset_class": "equal_weight_by_asset_class",
    "risk_parity": "risk_parity",
    "hierarchical_risk_parity": "hierarchical_risk_parity",
    "risk_budget_by_asset": "risk_budget_by_asset",
    "risk_budget_by_asset_class": "risk_budget_by_asset_class",
    "minimum_variance": "minimum_variance",
    "minimum_variance_uncapped": "minimum_variance_uncapped",
    "minimum_variance_advanced": "minimum_variance_advanced",
    "minimum_cvar_constrained": "minimum_cvar_constrained",
    "minimum_cvar_uncapped": "minimum_cvar_uncapped",
    "maximum_diversification": "maximum_diversification",
    "maximum_diversification_uncapped": "maximum_diversification_uncapped",
    "robust_mv_constrained": "robust_mv_constrained",
    "robust_mv_uncapped": "robust_mv_uncapped",
    "robust_scenario": "robust_scenario",
}


class PortfolioAlternativesBuilderError(ValueError):
    """Raised when an on-demand alternative request is unsupported."""


def builder_prefill_contract_violations(prefill: Mapping[str, Any] | None) -> list[str]:
    """Return strict BuilderPrefill contract violations for Block 6 Session 01."""

    prefix = "builder_prefill"
    if not isinstance(prefill, Mapping):
        return [f"{prefix}: document is missing or not an object"]

    violations: list[str] = []
    missing = [field for field in BUILDER_PREFILL_REQUIRED_FIELDS if field not in prefill]
    if missing:
        violations.append(f"{prefix}: missing fields: {', '.join(missing)}")

    forbidden = sorted(BUILDER_PREFILL_PROHIBITED_FIELDS & set(prefill))
    if forbidden:
        violations.append(f"{prefix}: prohibited fields present: {', '.join(forbidden)}")

    status = str(prefill.get("status") or "").strip()
    if status not in BUILDER_PREFILL_ALLOWED_STATUSES:
        violations.append(f"{prefix}: invalid status {prefill.get('status')!r}")

    if prefill.get("is_rebalance_recommendation") is not False:
        violations.append(f"{prefix}: is_rebalance_recommendation must be false")

    warnings = prefill.get("warnings")
    if not isinstance(warnings, list):
        violations.append(f"{prefix}: warnings must be a list")

    alternative_methods = prefill.get("alternative_methods")
    if not isinstance(alternative_methods, list):
        violations.append(f"{prefix}: alternative_methods must be a list")

    success_criteria = prefill.get("success_criteria")
    if not isinstance(success_criteria, list):
        violations.append(f"{prefix}: success_criteria must be a list")

    return violations


@dataclass(frozen=True)
class PortfolioAlternativeRequest:
    """A user-selected candidate hypothesis from Launchpad or equivalent UI."""

    candidate_method_id: str
    goal: str | None = None
    source_card_id: str | None = None
    mode: str | None = None
    constraint_preset: str | None = None
    max_asset_weight: float | None = None
    min_asset_weight: float | None = None
    volatility_target: float | None = None
    rebalancing_frequency: str | None = None
    transaction_cost_assumption: float | None = None


def launchpad_card_to_builder_prefill(
    card: Mapping[str, Any],
    *,
    next_diagnostic_step: Mapping[str, Any] | None = None,
    client_fit_check: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Map one Launchpad v3 card to a UI-safe Builder prefill object.

    The returned object is diagnostic setup only: it does not build a candidate
    plan, run subprocesses, write weights, or recommend a rebalance.
    """

    suggested_methods = _launchpad_method_rows(card.get("suggested_methods"))
    method_ids = _candidate_method_ids(suggested_methods)
    card_type = _optional_string(card.get("card_type"))
    launch_status = _optional_string(card.get("launch_status"))
    method_role_hint = _method_role_hint(suggested_methods, card_type)
    strategy = select_builder_strategy(
        _optional_string(card.get("goal")),
        card_type=card_type,
        method_role=method_role_hint,
    )
    suggested_method = _pick_suggested_method(
        card.get("default_method"),
        method_ids,
        preferred_method=strategy.get("selected_method"),
    )
    strategy = select_builder_strategy(
        _optional_string(card.get("goal")),
        card_type=card_type,
        method_role=method_role_hint,
        selected_method=suggested_method,
    )
    selected_method_row = _method_row_for_id(suggested_methods, suggested_method)
    source_diagnosis_id = _optional_string(
        card.get("source_diagnosis_id") or card.get("source_problem_id")
    )
    source_problem_id = _optional_string(
        card.get("source_problem_id") or card.get("source_diagnosis_id")
    )
    source_card_id = _optional_string(card.get("card_id"))
    builder_mode = _builder_mode_for_card(
        card,
        suggested_method=suggested_method,
        card_type=card_type,
        launch_status=launch_status,
    )
    candidate_generation_allowed = (
        suggested_method is not None and builder_mode == "guided_from_diagnosis"
    )
    client_fit_test_criteria = _client_fit_test_criteria(client_fit_check)
    success_criteria = list(card.get("success_criteria") or [])
    if client_fit_test_criteria:
        success_criteria.extend(
            row["criterion_en"]
            for row in client_fit_test_criteria["target_rows"]
            if row.get("criterion_en")
        )

    prefill = {
        "builder_prefill_id": _builder_prefill_id(source_card_id, source_diagnosis_id),
        "builder_mode": builder_mode,
        "source": "candidate_launchpad_v3",
        "source_diagnosis_id": source_diagnosis_id,
        "source_problem_id": source_problem_id,
        "source_card_id": source_card_id,
        "goal": _optional_string(card.get("goal")),
        "hypothesis_to_test": _optional_string(card.get("hypothesis_to_test")),
        "next_diagnostic_step": (
            dict(next_diagnostic_step) if next_diagnostic_step is not None else None
        ),
        "suggested_method": suggested_method,
        "alternative_methods": [
            method_id
            for method_id in method_ids
            if method_id != suggested_method and method_id in GUIDED_METHODS
        ],
        "suggested_methods": suggested_methods,
        "strategy_selector": strategy,
        "original_suggested_method": strategy["original_suggested_method"],
        "selected_method": strategy["selected_method"],
        "method_changed_by_user": strategy["method_changed_by_user"],
        "constraint_preset": _optional_string(card.get("constraint_preset")),
        "max_asset_weight": card.get("max_asset_weight"),
        "min_asset_weight": card.get("min_asset_weight"),
        "volatility_target": card.get("volatility_target"),
        "rebalancing_frequency": _optional_string(card.get("rebalancing_frequency")),
        "transaction_cost_bps": card.get("transaction_cost_bps")
        if card.get("transaction_cost_bps") is not None
        else card.get("transaction_cost_assumption"),
        "success_criteria": success_criteria,
        "tradeoff_to_watch": _optional_string(
            card.get("tradeoff_to_watch") or card.get("expected_tradeoff_to_check_en")
        ),
        "when_to_skip": _optional_string(
            card.get("when_to_skip") or card.get("when_to_skip_this_test_en")
        ),
        "card_type": card_type,
        "launch_status": launch_status,
        "method_role": _builder_method_role(selected_method_row, card_type),
        "is_rebalance_recommendation": False,
        "decision_boundary": _optional_string(card.get("decision_boundary")),
        "candidate_generation_allowed": candidate_generation_allowed,
        "created_from": "candidate_launchpad_v3",
        "status": _builder_prefill_status(builder_mode),
        "warnings": [],
    }
    if isinstance(card.get("client_fit_context"), Mapping):
        prefill["client_fit_context"] = dict(card["client_fit_context"])
    if _optional_string(card.get("client_fit_relevance_en")):
        prefill["client_fit_relevance_en"] = _optional_string(card.get("client_fit_relevance_en"))
    if client_fit_test_criteria:
        prefill["client_fit_test_criteria"] = client_fit_test_criteria
        prefill["client_fit_optimizer_boundary"] = CLIENT_FIT_OPTIMIZER_BOUNDARY_EN
    return prefill


def select_builder_strategy(
    goal: str | None,
    *,
    card_type: str | None = None,
    method_role: str | None = None,
    selected_method: str | None = None,
) -> dict[str, Any]:
    """Select a guided Builder method for one goal.

    This is Block 6 setup state only. It does not validate, build, execute, or
    write candidate portfolios, and it never recommends a rebalance.
    """

    goal_id = _normalize_builder_goal(goal)
    guided_methods = list(BUILDER_STRATEGY_GOAL_METHODS.get(goal_id or "", ()))
    original_suggested_method = guided_methods[0] if guided_methods else None
    selected_method_text = _normalize_builder_method_id(selected_method)
    effective_selected_method = selected_method_text or original_suggested_method
    method_changed_by_user = (
        selected_method_text is not None
        and selected_method_text != original_suggested_method
    )
    strategy_method_role = _strategy_method_role(
        card_type=card_type,
        method_role=method_role,
        goal_id=goal_id,
        selected_method=effective_selected_method,
    )

    warnings: list[str] = []
    if goal_id is None and selected_method_text is None:
        warnings.append("unknown_goal_no_guided_method")
    if (
        selected_method_text is not None
        and guided_methods
        and selected_method_text not in guided_methods
    ):
        warnings.append("selected_method_outside_guided_goal_methods")

    constraints = {
        "constraint_preset": "balanced" if guided_methods else None,
        "max_asset_weight": None,
        "min_asset_weight": None,
    }
    constraints.update(BUILDER_STRATEGY_CONSTRAINT_HINTS.get(goal_id or "", {}))

    return {
        "goal": _optional_string(goal),
        "goal_id": goal_id,
        "method_role": strategy_method_role,
        "guided_methods": guided_methods,
        "original_suggested_method": original_suggested_method,
        "selected_method": effective_selected_method,
        "method_changed_by_user": method_changed_by_user,
        "alternative_methods": [
            method_id
            for method_id in guided_methods
            if method_id != effective_selected_method
        ],
        "constraint_preset": constraints["constraint_preset"],
        "max_asset_weight": constraints["max_asset_weight"],
        "min_asset_weight": constraints["min_asset_weight"],
        "shows_raw_optimizer_menu": False,
        "is_rebalance_recommendation": False,
        "warnings": warnings,
    }


def build_builder_prefill_from_launchpad_card(
    card: Mapping[str, Any],
    *,
    next_diagnostic_step: Mapping[str, Any] | None = None,
    client_fit_check: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Backward-compatible name for :func:`launchpad_card_to_builder_prefill`."""

    return launchpad_card_to_builder_prefill(
        card,
        next_diagnostic_step=next_diagnostic_step,
        client_fit_check=client_fit_check,
    )


def _client_fit_test_criteria(
    client_fit_check: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    """Return display-only Client Fit criteria for Builder and CandidateSetup.

    These rows are deliberately not mapped into ``parameters`` or ``constraints``.
    They are success criteria for the later comparison screen, not optimizer inputs.
    """

    if not isinstance(client_fit_check, Mapping):
        return None
    profile = client_fit_check.get("profile")
    if not isinstance(profile, Mapping):
        return None
    status = _optional_string(client_fit_check.get("client_fit_status")) or "not_provided"
    if status == "not_provided":
        return None

    rows: list[dict[str, Any]] = []
    target_return_range = profile.get("target_return_range")
    if isinstance(target_return_range, Mapping):
        rows.append(
            {
                "dimension": "return",
                "metric_field": "cagr",
                "criterion_en": "Compare return against the stated Client Fit target range.",
                "target_range": dict(target_return_range),
                "usage": "display_test_criterion",
            }
        )
    target_vol_range = profile.get("target_vol_range")
    if isinstance(target_vol_range, Mapping):
        rows.append(
            {
                "dimension": "volatility",
                "metric_field": "vol_annual",
                "criterion_en": "Compare volatility against the stated Client Fit comfort range.",
                "target_range": dict(target_vol_range),
                "usage": "display_test_criterion",
            }
        )
    target_max_drawdown = profile.get("target_max_drawdown_pct")
    if target_max_drawdown is not None:
        rows.extend(
            [
                {
                    "dimension": "historical_drawdown",
                    "metric_field": "max_drawdown",
                    "criterion_en": (
                        "Compare historical drawdown against the stated maximum temporary loss."
                    ),
                    "target_limit": target_max_drawdown,
                    "usage": "display_test_criterion",
                },
                {
                    "dimension": "stress_loss",
                    "metric_field": "worst_stress_loss",
                    "criterion_en": (
                        "Compare worst stress loss against the stated maximum temporary loss."
                    ),
                    "target_limit": target_max_drawdown,
                    "usage": "display_test_criterion",
                },
            ]
        )
    horizon = profile.get("horizon_years")
    if horizon is not None:
        rows.append(
            {
                "dimension": "horizon",
                "metric_field": None,
                "criterion_en": (
                    "Keep the stated horizon visible as interpretation context; do not change "
                    "the analysis window."
                ),
                "horizon_years": horizon,
                "usage": "display_context_only",
            }
        )
    if not rows:
        return None
    return {
        "schema_version": "builder_client_fit_test_criteria_v1",
        "source_artifact": "client_fit_check.json",
        "client_fit_status": status,
        "profile": {
            "preset_id": profile.get("preset_id"),
            "source_quality": profile.get("source_quality"),
            "horizon_years": horizon,
        },
        "target_rows": rows,
        "optimizer_boundary_en": CLIENT_FIT_OPTIMIZER_BOUNDARY_EN,
    }


def build_simple_builder_parameters(
    prefill: Mapping[str, Any],
    *,
    overrides: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the Block 6 Simple Mode editable setup from one BuilderPrefill.

    Simple Mode is setup state only. It exposes the small editable field set
    required by Block 6 Session 04 and deliberately omits advanced optimizer
    controls, candidate ids, weights, comparison results, and verdict state.
    """

    if not isinstance(prefill, Mapping):
        raise PortfolioAlternativesBuilderError("builder_prefill_missing_or_invalid")

    edits = dict(overrides or {})
    advanced = sorted(SIMPLE_BUILDER_PROHIBITED_ADVANCED_FIELDS & set(edits))
    if advanced:
        raise PortfolioAlternativesBuilderError(
            f"advanced_simple_mode_fields_not_supported:{','.join(advanced)}"
        )

    strategy = prefill.get("strategy_selector")
    strategy = strategy if isinstance(strategy, Mapping) else {}
    method = _first_present(
        edits.get("method"),
        edits.get("selected_method"),
        prefill.get("selected_method"),
        prefill.get("suggested_method"),
        strategy.get("selected_method"),
    )
    original_suggested_method = _normalize_builder_method_id(
        prefill.get("original_suggested_method")
        or strategy.get("original_suggested_method")
        or prefill.get("suggested_method")
    )
    selected_method = _normalize_builder_method_id(method)
    user_supplied_method = edits.get("method") is not None or edits.get("selected_method") is not None
    method_changed_by_user = bool(
        selected_method is not None
        and selected_method != original_suggested_method
        and (user_supplied_method or prefill.get("method_changed_by_user") is True)
    )

    method_role = _optional_string(prefill.get("method_role"))
    default_preset = (
        _normalize_constraint_preset(prefill.get("constraint_preset"))
        or _normalize_constraint_preset(strategy.get("constraint_preset"))
        or ("basic_reference" if method_role == "reference_benchmark" else "balanced")
    )
    requested_preset = _normalize_constraint_preset(
        _first_present(edits.get("constraint_preset"), default_preset)
    )
    mode = _normalize_builder_mode(
        _first_present(edits.get("mode"), edits.get("constraint_mode")),
        preset=requested_preset,
        selected_method=method,
    )
    preset_values = CONSTRAINT_PRESETS.get(requested_preset or "", {})
    default_min_asset_weight = (
        0.0
        if mode == "uncapped"
        else _first_present(
            preset_values.get("min_asset_weight"),
            prefill.get("min_asset_weight"),
            strategy.get("min_asset_weight"),
        )
    )
    default_max_asset_weight = (
        None
        if mode == "uncapped"
        else _first_present(
            preset_values.get("max_asset_weight"),
            prefill.get("max_asset_weight"),
            strategy.get("max_asset_weight"),
        )
    )
    warning_list = list(prefill.get("warnings") or [])
    if mode == "uncapped" and UNCAPPED_MODE_CONCENTRATION_WARNING not in warning_list:
        warning_list.append(UNCAPPED_MODE_CONCENTRATION_WARNING)

    setup: dict[str, Any] = {
        "builder_prefill_id": prefill.get("builder_prefill_id"),
        "source_card_id": prefill.get("source_card_id"),
        "source_diagnosis_id": prefill.get("source_diagnosis_id"),
        "source_problem_id": prefill.get("source_problem_id"),
        "builder_mode": prefill.get("builder_mode"),
        "status": prefill.get("status"),
        "simple_mode": True,
        "editable_fields": list(SIMPLE_BUILDER_EDITABLE_FIELDS),
        "goal": _optional_string(_first_present(edits.get("goal"), prefill.get("goal"))),
        "method": selected_method,
        "selected_method": selected_method,
        "original_suggested_method": original_suggested_method,
        "method_changed_by_user": method_changed_by_user,
        "method_role": method_role,
        "mode": mode,
        "capped": mode == "capped",
        "uncapped": mode == "uncapped",
        "constraint_preset": requested_preset,
        "max_asset_weight": _simple_number_or_none(
            None
            if mode == "uncapped"
            else _first_present(
                    edits.get("max_asset_weight"),
                    default_max_asset_weight,
            )
        ),
        "min_asset_weight": _simple_number_or_none(
            0.0
            if mode == "uncapped"
            else _first_present(
                    edits.get("min_asset_weight"),
                    default_min_asset_weight,
            )
        ),
        "hypothesis_to_test": prefill.get("hypothesis_to_test"),
        "success_criteria": list(prefill.get("success_criteria") or []),
        "client_fit_context": (
            dict(prefill["client_fit_context"])
            if isinstance(prefill.get("client_fit_context"), Mapping)
            else None
        ),
        "client_fit_relevance_en": prefill.get("client_fit_relevance_en"),
        "client_fit_test_criteria": (
            dict(prefill["client_fit_test_criteria"])
            if isinstance(prefill.get("client_fit_test_criteria"), Mapping)
            else None
        ),
        "client_fit_optimizer_boundary": prefill.get("client_fit_optimizer_boundary"),
        "tradeoff_to_watch": prefill.get("tradeoff_to_watch"),
        "when_to_skip": prefill.get("when_to_skip"),
        "decision_boundary": prefill.get("decision_boundary"),
        "is_rebalance_recommendation": False,
        "card_type": prefill.get("card_type"),
        "launch_status": prefill.get("launch_status"),
        "candidate_generation_allowed": bool(prefill.get("candidate_generation_allowed")),
        "advanced_settings_exposed": False,
        "prohibited_advanced_fields": [],
        "warnings": warning_list,
    }
    asset_count = _simple_number_or_none(
        _first_present(
            edits.get("asset_count"),
            edits.get("n_assets"),
            prefill.get("asset_count"),
            prefill.get("n_assets"),
            strategy.get("asset_count"),
            strategy.get("n_assets"),
        )
    )
    if asset_count is not None:
        setup["asset_count"] = int(asset_count)
    setup["parameters"] = {
        field: setup[field]
        for field in SIMPLE_BUILDER_EDITABLE_FIELDS
    }
    setup["constraints"] = {
        "constraint_preset": setup["constraint_preset"],
        "mode": setup["mode"],
        "capped": setup["capped"],
        "uncapped": setup["uncapped"],
        "max_asset_weight": setup["max_asset_weight"],
        "min_asset_weight": setup["min_asset_weight"],
    }
    return setup


def validate_builder_setup(setup: Mapping[str, Any]) -> dict[str, Any]:
    """Validate Block 6 Builder setup before any Block 7 candidate generation.

    Validation returns one explicit status. It does not build candidates, run
    optimizers, write weights, compare portfolios, or create a verdict.
    """

    if not isinstance(setup, Mapping):
        return _builder_validation_result(
            "invalid_constraints",
            ["setup_missing_or_invalid"],
            can_generate_candidate=False,
        )

    if _setup_is_data_quality_blocker(setup):
        return _builder_validation_result(
            "blocked_by_data_quality",
            ["data_quality_blocker"],
            can_generate_candidate=False,
        )

    goal = _optional_string(setup.get("goal"))
    if goal is None:
        return _builder_validation_result(
            "missing_goal",
            ["missing_goal"],
            can_generate_candidate=False,
        )

    method = _selected_setup_method(setup)
    if method is None:
        return _builder_validation_result(
            "missing_method",
            ["missing_method"],
            can_generate_candidate=False,
        )
    if method not in GUIDED_METHODS:
        return _builder_validation_result(
            "invalid_method",
            [f"unsupported_method:{method}"],
            can_generate_candidate=False,
        )

    reference_errors = _reference_boundary_errors(setup)
    if reference_errors:
        return _builder_validation_result(
            "reference_benchmark_boundary_violation",
            reference_errors,
            can_generate_candidate=False,
        )

    constraint_errors = _constraint_sanity_errors(setup)
    if constraint_errors:
        return _builder_validation_result(
            "invalid_constraints",
            constraint_errors,
            can_generate_candidate=False,
        )

    feasibility_warnings = _constraint_feasibility_warnings(setup)
    if feasibility_warnings:
        return _builder_validation_result(
            "infeasible_constraints_risk",
            feasibility_warnings,
            can_generate_candidate=False,
        )

    targeted_errors = _targeted_setup_errors(setup)
    if targeted_errors:
        return _builder_validation_result(
            "invalid_constraints",
            targeted_errors,
            can_generate_candidate=False,
        )

    can_generate = setup.get("candidate_generation_allowed")
    return _builder_validation_result(
        "valid",
        [],
        warnings=list(setup.get("warnings") or []),
        can_generate_candidate=can_generate is not False,
    )


def candidate_setup_contract_violations(
    candidate_setup: Mapping[str, Any] | None,
) -> list[str]:
    """Return strict CandidateSetup contract violations for Block 6."""

    prefix = "candidate_setup"
    if not isinstance(candidate_setup, Mapping):
        return [f"{prefix}: document is missing or not an object"]

    violations: list[str] = []
    missing = [
        field for field in CANDIDATE_SETUP_REQUIRED_FIELDS if field not in candidate_setup
    ]
    if missing:
        violations.append(f"{prefix}: missing fields: {', '.join(missing)}")

    forbidden = sorted(CANDIDATE_SETUP_PROHIBITED_FIELDS & set(candidate_setup))
    if forbidden:
        violations.append(f"{prefix}: prohibited fields present: {', '.join(forbidden)}")

    if candidate_setup.get("is_rebalance_recommendation") is not False:
        violations.append(f"{prefix}: is_rebalance_recommendation must be false")

    if candidate_setup.get("validation_status") != "valid":
        violations.append(f"{prefix}: validation_status must be 'valid'")

    if candidate_setup.get("can_generate_candidate") is not True:
        violations.append(f"{prefix}: can_generate_candidate must be true")

    for field in ("parameters", "constraints"):
        if not isinstance(candidate_setup.get(field), Mapping):
            violations.append(f"{prefix}: {field} must be an object")

    if not isinstance(candidate_setup.get("success_criteria"), list):
        violations.append(f"{prefix}: success_criteria must be a list")
    if not isinstance(candidate_setup.get("validation_warnings"), list):
        violations.append(f"{prefix}: validation_warnings must be a list")

    return violations


def builder_prefill_to_candidate_setup(
    prefill: Mapping[str, Any],
    *,
    edits: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Build a validated CandidateSetup from one BuilderPrefill plus user edits.

    CandidateSetup is the Block 6 handoff to Block 7. It is not a candidate
    portfolio and deliberately excludes candidate ids, weights, metrics,
    stress results, comparison output, and verdict state.
    """

    setup, validation = _build_setup_and_validation(prefill, edits=edits)
    if validation.get("validation_status") != "valid":
        return None

    candidate_setup = _candidate_setup_from_validated_setup(setup, validation)
    violations = candidate_setup_contract_violations(candidate_setup)
    if violations:
        raise PortfolioAlternativesBuilderError(
            "candidate_setup_contract_violation:" + "; ".join(violations)
        )
    return candidate_setup


def build_portfolio_alternatives_builder_document(
    builder_prefill: Mapping[str, Any],
    candidate_setup: Mapping[str, Any] | None,
    validation: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the product-facing Block 6 Builder artifact document."""

    validation_status = _optional_string(validation.get("validation_status"))
    can_generate = bool(validation.get("can_generate_candidate")) and isinstance(
        candidate_setup, Mapping
    )
    is_data_quality = validation_status == "blocked_by_data_quality"
    status = "ok" if can_generate and validation_status == "valid" else "blocked"
    reason = None
    if is_data_quality:
        reason = "data_quality_blocker"
    elif status == "blocked":
        reason = validation_status or "builder_validation_failed"

    doc: dict[str, Any] = {
        "schema_version": PORTFOLIO_ALTERNATIVES_BUILDER_SCHEMA_VERSION,
        "diagnostic_only": True,
        "status": status,
        "reason": reason,
        "can_generate_candidate": can_generate,
        "generated_at": _utc_now_iso(),
        "source_artifacts": {
            "candidate_launchpad": "candidate_launchpad.json",
            "problem_classification": "problem_classification.json",
            "client_fit_check": "client_fit_check.json"
            if (
                isinstance(builder_prefill.get("client_fit_test_criteria"), Mapping)
                or isinstance(builder_prefill.get("client_fit_context"), Mapping)
            )
            else None,
        },
        "selected_card_id": builder_prefill.get("source_card_id"),
        "builder_prefill": dict(builder_prefill),
        "candidate_setup": dict(candidate_setup) if isinstance(candidate_setup, Mapping) else None,
        "validation": dict(validation),
        "guardrails": {
            "does_not_generate_candidate": True,
            "does_not_write_weights": True,
            "does_not_write_comparison_or_verdict": True,
            "is_rebalance_recommendation": False,
            "client_fit_targets_are_not_optimizer_mandates": True,
        },
    }
    if is_data_quality:
        doc["candidate_setup"] = None
    return doc


def write_portfolio_alternatives_builder_outputs(
    output_dir: str | Path,
    *,
    candidate_launchpad: Mapping[str, Any] | None,
    problem_classification: Mapping[str, Any] | None = None,
    client_fit_check: Mapping[str, Any] | None = None,
) -> dict[str, Path]:
    """Write ``portfolio_alternatives_builder.json`` beside Launchpad output.

    The writer selects the first Launchpad card as the primary Builder card. It
    only materializes Block 6 setup state and never invokes Block 7 candidate
    generation.
    """

    if not isinstance(candidate_launchpad, Mapping):
        return {}
    cards = candidate_launchpad.get("cards")
    if not isinstance(cards, Sequence) or isinstance(cards, (str, bytes)) or not cards:
        return {}
    primary_card = cards[0]
    if not isinstance(primary_card, Mapping):
        return {}

    next_step = None
    if isinstance(problem_classification, Mapping):
        raw_next_step = problem_classification.get("next_diagnostic_step")
        next_step = raw_next_step if isinstance(raw_next_step, Mapping) else None

    prefill = launchpad_card_to_builder_prefill(
        primary_card,
        next_diagnostic_step=next_step,
        client_fit_check=client_fit_check,
    )
    setup, validation = _build_setup_and_validation(prefill)
    candidate_setup = (
        _candidate_setup_from_validated_setup(setup, validation)
        if validation.get("validation_status") == "valid"
        else None
    )
    doc = build_portfolio_alternatives_builder_document(
        prefill,
        candidate_setup,
        validation,
    )

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / PORTFOLIO_ALTERNATIVES_BUILDER_FILENAME
    with path.open("w", encoding="utf-8") as handle:
        json.dump(doc, handle, indent=2, ensure_ascii=False, default=str)
    return {"portfolio_alternatives_builder_json": path}


def _builder_prefill_id(
    source_card_id: str | None,
    source_diagnosis_id: str | None,
) -> str:
    raw = source_card_id or source_diagnosis_id or "unspecified"
    safe = "".join(char.lower() if char.isalnum() else "_" for char in str(raw))
    safe = "_".join(part for part in safe.split("_") if part)
    return f"builder_prefill_{safe or 'unspecified'}"


def _builder_prefill_status(builder_mode: str) -> str:
    if builder_mode == "guided_from_diagnosis":
        return "ready_for_user_confirmation"
    if builder_mode == "blocked_data_quality":
        return "blocked"
    if builder_mode == "monitor_only":
        return "monitor_only"
    return "custom_draft"


def _launchpad_method_rows(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, Mapping):
            continue
        method_id = _normalize_builder_method_id(item.get("candidate_method_id"))
        if method_id is None or method_id not in GUIDED_METHODS or method_id in seen:
            continue
        row = dict(item)
        row["candidate_method_id"] = method_id
        rows.append(row)
        seen.add(method_id)
    return rows


def _candidate_method_ids(method_rows: Sequence[Mapping[str, Any]]) -> list[str]:
    method_ids: list[str] = []
    for row in method_rows:
        method_id = _normalize_builder_method_id(row.get("candidate_method_id"))
        if method_id and method_id in GUIDED_METHODS:
            method_ids.append(method_id)
    return method_ids


def _pick_suggested_method(
    default_method: Any,
    method_ids: Sequence[str],
    *,
    preferred_method: Any = None,
) -> str | None:
    preferred_id = str(preferred_method or "").strip()
    preferred_id = _normalize_builder_method_id(preferred_id) or ""
    if preferred_id and preferred_id in method_ids:
        return preferred_id
    default_id = _normalize_builder_method_id(default_method)
    if default_id and default_id in method_ids:
        return default_id
    if method_ids:
        return method_ids[0]
    return None


def _method_row_for_id(
    method_rows: Sequence[Mapping[str, Any]],
    method_id: str | None,
) -> Mapping[str, Any] | None:
    if method_id is None:
        return None
    normalized_method_id = _normalize_builder_method_id(method_id)
    for row in method_rows:
        if _normalize_builder_method_id(row.get("candidate_method_id")) == normalized_method_id:
            return row
    return None


def _builder_method_role(
    method_row: Mapping[str, Any] | None,
    card_type: str | None,
) -> str | None:
    if method_row is None:
        return None
    role = str(method_row.get("method_role") or "").strip()
    if role == "reference_benchmark" or card_type == "reference_benchmark_test":
        return "reference_benchmark"
    if role in {"targeted_hypothesis", "targeted_candidate_method", ""}:
        return "targeted_candidate_method"
    return role


def _method_role_hint(
    method_rows: Sequence[Mapping[str, Any]],
    card_type: str | None,
) -> str | None:
    if card_type == "reference_benchmark_test":
        return "reference_benchmark"
    for row in method_rows:
        role = str(row.get("method_role") or "").strip()
        if role == "reference_benchmark":
            return "reference_benchmark"
        if role:
            return role
    return None


def _strategy_method_role(
    *,
    card_type: str | None,
    method_role: str | None,
    goal_id: str | None,
    selected_method: str | None,
) -> str | None:
    role = str(method_role or "").strip()
    if role == "reference_benchmark" or card_type == "reference_benchmark_test":
        return "reference_benchmark"
    if goal_id == "compare_simple_benchmark":
        return "reference_benchmark"
    if selected_method is not None:
        if role == "custom_user_selected":
            return "custom_user_selected"
        return "targeted_candidate_method"
    return None


def _builder_mode_for_card(
    card: Mapping[str, Any],
    *,
    suggested_method: str | None,
    card_type: str | None,
    launch_status: str | None,
) -> str:
    if suggested_method is not None:
        return "guided_from_diagnosis"
    if _is_data_quality_card(card, card_type=card_type, launch_status=launch_status):
        return "blocked_data_quality"
    return "monitor_only"


def _is_data_quality_card(
    card: Mapping[str, Any],
    *,
    card_type: str | None,
    launch_status: str | None,
) -> bool:
    searchable_values = (
        card.get("card_id"),
        card.get("goal"),
        card.get("source_diagnosis_id"),
        card.get("source_problem_id"),
        card_type,
        launch_status,
    )
    text = " ".join(str(value or "").lower() for value in searchable_values)
    return any(marker in text for marker in ("data_quality", "data quality", "insufficient"))


def _optional_string(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _normalize_builder_method_id(value: Any) -> str | None:
    method_id = _optional_string(value)
    if method_id is None:
        return None
    return METHOD_ALIASES.get(method_id, method_id)


def _normalize_constraint_preset(value: Any) -> str | None:
    preset = _optional_string(value)
    if preset is None:
        return None
    normalized = preset.lower().strip().replace("-", "_").replace(" ", "_")
    if normalized == "concentration_cap":
        return "conservative"
    return normalized


def _normalize_builder_mode(
    value: Any,
    *,
    preset: str | None,
    selected_method: str | None,
) -> str:
    mode = _optional_string(value)
    if mode is not None:
        normalized = mode.lower().strip().replace("-", "_").replace(" ", "_")
        if normalized in SIMPLE_BUILDER_ALLOWED_MODES:
            return normalized
    if preset == "uncapped":
        return "uncapped"
    raw_selected = _optional_string(selected_method)
    if raw_selected in {
        "minimum_variance_uncapped",
        "minimum_cvar_uncapped",
        "maximum_diversification_uncapped",
    }:
        return "uncapped"
    return "capped"


def _hidden_method_warnings(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    hidden: list[str] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        method_id = _optional_string(item.get("candidate_method_id"))
        classification = HIDDEN_METHOD_CLASSIFICATIONS.get(method_id or "")
        if classification:
            hidden.append(f"{classification}:{method_id}")
    return hidden


def _normalize_builder_goal(goal: str | None) -> str | None:
    text = _optional_string(goal)
    if text is None:
        return None
    normalized = "".join(char.lower() if char.isalnum() else "_" for char in text)
    normalized = "_".join(part for part in normalized.split("_") if part)
    normalized = BUILDER_STRATEGY_GOAL_ALIASES.get(normalized, normalized)
    if normalized in BUILDER_STRATEGY_GOAL_METHODS:
        return normalized
    return None


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _simple_number_or_none(value: Any) -> float | int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _selected_setup_method(setup: Mapping[str, Any]) -> str | None:
    return _normalize_builder_method_id(
        setup.get("method")
        or setup.get("selected_method")
        or setup.get("suggested_method")
    )


def _setup_is_data_quality_blocker(setup: Mapping[str, Any]) -> bool:
    searchable_values = (
        setup.get("builder_mode"),
        setup.get("status"),
        setup.get("source_diagnosis_id"),
        setup.get("source_problem_id"),
        setup.get("source_card_id"),
        setup.get("goal"),
        setup.get("launch_status"),
    )
    text = " ".join(str(value or "").lower() for value in searchable_values)
    return any(
        marker in text
        for marker in (
            "blocked_data_quality",
            "evidence_insufficient_data_quality",
            "data_quality",
            "data quality",
            "resolve_data",
        )
    )


def _reference_boundary_errors(setup: Mapping[str, Any]) -> list[str]:
    card_type = _optional_string(setup.get("card_type"))
    method_role = _optional_string(setup.get("method_role"))
    is_reference = card_type == "reference_benchmark_test" or method_role == "reference_benchmark"
    if not is_reference:
        return []

    errors: list[str] = []
    if method_role != "reference_benchmark":
        errors.append("reference_benchmark_method_role_required")
    if setup.get("is_rebalance_recommendation") is not False:
        errors.append("reference_benchmark_must_not_be_rebalance_recommendation")
    boundary = _optional_string(setup.get("decision_boundary"))
    if boundary is None:
        errors.append("reference_benchmark_decision_boundary_required")
    elif "rebalance recommendation" not in boundary.lower():
        errors.append("reference_benchmark_decision_boundary_must_block_rebalance")
    return errors


def _targeted_setup_errors(setup: Mapping[str, Any]) -> list[str]:
    method_role = _optional_string(setup.get("method_role"))
    card_type = _optional_string(setup.get("card_type"))
    is_targeted = method_role == "targeted_candidate_method" or card_type == "targeted_hypothesis_test"
    if not is_targeted:
        return []

    errors: list[str] = []
    if _optional_string(setup.get("hypothesis_to_test")) is None:
        errors.append("targeted_setup_missing_hypothesis_to_test")
    success = setup.get("success_criteria")
    if not isinstance(success, list) or not success:
        errors.append("targeted_setup_missing_success_criteria")
    if _optional_string(setup.get("tradeoff_to_watch")) is None:
        errors.append("targeted_setup_missing_tradeoff_to_watch")
    return errors


def _constraint_sanity_errors(setup: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    preset = _normalize_constraint_preset(setup.get("constraint_preset"))
    if preset is not None and preset not in SIMPLE_BUILDER_ALLOWED_PRESETS:
        errors.append(f"unsupported_constraint_preset:{preset}")
    mode = _optional_string(setup.get("mode"))
    if mode is not None and mode not in SIMPLE_BUILDER_ALLOWED_MODES:
        errors.append(f"unsupported_mode:{mode}")
    if mode == "uncapped":
        if setup.get("capped") is not False:
            errors.append("uncapped_mode_requires_capped_false")
        if setup.get("uncapped") is not True:
            errors.append("uncapped_mode_requires_uncapped_true")
        if setup.get("max_asset_weight") is not None:
            errors.append("uncapped_mode_requires_null_max_asset_weight")

    min_weight = _simple_number_or_none(setup.get("min_asset_weight"))
    max_weight = _simple_number_or_none(setup.get("max_asset_weight"))
    volatility_target = _simple_number_or_none(setup.get("volatility_target"))
    transaction_cost_bps = _simple_number_or_none(setup.get("transaction_cost_bps"))

    if min_weight is not None and min_weight < 0:
        errors.append("min_asset_weight_must_be_non_negative")
    if max_weight is not None and max_weight <= 0:
        errors.append("max_asset_weight_must_be_positive")
    if min_weight is not None and min_weight > 1:
        errors.append("min_asset_weight_must_not_exceed_one")
    if max_weight is not None and max_weight > 1:
        errors.append("max_asset_weight_must_not_exceed_one")
    if min_weight is not None and max_weight is not None and max_weight < min_weight:
        errors.append("max_asset_weight_below_min_asset_weight")
    if volatility_target is not None and volatility_target <= 0:
        errors.append("volatility_target_must_be_positive_when_set")
    if transaction_cost_bps is not None and transaction_cost_bps < 0:
        errors.append("transaction_cost_bps_must_be_non_negative")

    advanced = sorted(SIMPLE_BUILDER_PROHIBITED_ADVANCED_FIELDS & set(setup))
    if advanced:
        errors.append(f"advanced_fields_not_supported:{','.join(advanced)}")
    return errors


def _constraint_feasibility_warnings(setup: Mapping[str, Any]) -> list[str]:
    asset_count = setup.get("asset_count") or setup.get("n_assets")
    if isinstance(asset_count, bool):
        return []
    try:
        n_assets = int(asset_count)
    except (TypeError, ValueError):
        return []
    if n_assets <= 0:
        return []

    warnings: list[str] = []
    min_weight = _simple_number_or_none(setup.get("min_asset_weight"))
    max_weight = _simple_number_or_none(setup.get("max_asset_weight"))
    if max_weight is not None and max_weight * n_assets < 1:
        warnings.append("max_asset_weight_too_low_for_asset_count")
    if min_weight is not None and min_weight * n_assets > 1:
        warnings.append("min_asset_weight_too_high_for_asset_count")
    return warnings


def _builder_validation_result(
    status: str,
    errors: Sequence[str],
    *,
    warnings: Sequence[str] | None = None,
    can_generate_candidate: bool,
) -> dict[str, Any]:
    if status not in BUILDER_VALIDATION_STATUSES:
        raise PortfolioAlternativesBuilderError(f"unknown_builder_validation_status:{status}")
    return {
        "validation_status": status,
        "can_generate_candidate": bool(can_generate_candidate),
        "validation_errors": list(errors),
        "validation_warnings": list(warnings or []),
    }


def _build_setup_and_validation(
    prefill: Mapping[str, Any],
    *,
    edits: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    setup = build_simple_builder_parameters(prefill, overrides=edits)
    validation = validate_builder_setup(setup)
    return setup, validation


def _candidate_setup_from_validated_setup(
    setup: Mapping[str, Any],
    validation: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "candidate_setup_id": _candidate_setup_id(setup.get("builder_prefill_id")),
        "builder_prefill_id": setup.get("builder_prefill_id"),
        "source_card_id": setup.get("source_card_id"),
        "source_diagnosis_id": setup.get("source_diagnosis_id"),
        "source_launchpad_card_type": setup.get("card_type"),
        "goal": setup.get("goal"),
        "hypothesis_to_test": setup.get("hypothesis_to_test"),
        "selected_method": _selected_setup_method(setup),
        "original_suggested_method": setup.get("original_suggested_method"),
        "method_changed_by_user": bool(setup.get("method_changed_by_user")),
        "parameters": dict(setup.get("parameters") or {}),
        "constraints": dict(setup.get("constraints") or {}),
        "success_criteria": list(setup.get("success_criteria") or []),
        "client_fit_context": (
            dict(setup["client_fit_context"])
            if isinstance(setup.get("client_fit_context"), Mapping)
            else None
        ),
        "client_fit_relevance_en": setup.get("client_fit_relevance_en"),
        "client_fit_test_criteria": (
            dict(setup["client_fit_test_criteria"])
            if isinstance(setup.get("client_fit_test_criteria"), Mapping)
            else None
        ),
        "client_fit_optimizer_boundary": setup.get("client_fit_optimizer_boundary"),
        "tradeoff_to_watch": setup.get("tradeoff_to_watch"),
        "when_to_skip": setup.get("when_to_skip"),
        "decision_boundary": setup.get("decision_boundary"),
        "is_rebalance_recommendation": False,
        "can_generate_candidate": bool(validation.get("can_generate_candidate")),
        "validation_status": validation.get("validation_status"),
        "validation_warnings": list(validation.get("validation_warnings") or []),
        "created_at": _utc_now_iso(),
    }


def _candidate_setup_id(builder_prefill_id: Any) -> str:
    raw = _optional_string(builder_prefill_id) or "unspecified"
    safe = "".join(char.lower() if char.isalnum() else "_" for char in raw)
    safe = "_".join(part for part in safe.split("_") if part)
    return f"candidate_setup_{safe or 'unspecified'}"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class PortfolioAlternativeBuildPlan:
    """Execution plan for one existing candidate-builder path."""

    candidate_method_id: str
    candidate_id: str
    command: tuple[str, ...]
    artifact_contract: dict[str, Any]
    provenance: dict[str, Any]
    warnings: tuple[str, ...] = field(default_factory=tuple)


def candidate_id_for_builder_method(method_id: str | None, *, mode: str = "capped") -> str | None:
    """Map a guided Block 6 method and mode to the current backend candidate id."""

    normalized_method = _normalize_builder_method_id(method_id)
    normalized_mode = _normalize_builder_mode(mode, preset=None, selected_method=method_id)
    if normalized_method is None or normalized_method not in GUIDED_METHODS:
        return None
    by_mode = GUIDED_METHOD_TO_CANDIDATE_ID_BY_MODE[normalized_method]
    return by_mode[normalized_mode]


def supported_candidate_methods(*, include_hidden: bool = False) -> tuple[str, ...]:
    """Return guided product method ids, optionally including hidden legacy ids."""

    guided = tuple(GUIDED_METHOD_TO_CANDIDATE_ID_BY_MODE)
    if not include_hidden:
        return guided
    hidden = tuple(
        method_id
        for method_id in LEGACY_METHOD_TO_CANDIDATE_ID
        if method_id not in guided
    )
    return guided + hidden


def request_from_launchpad_card(
    card: Mapping[str, Any],
    *,
    method_index: int = 0,
) -> PortfolioAlternativeRequest:
    """Build a request from one Candidate Launchpad card.

    Cards remain non-portfolio artifacts. This helper only extracts a selected
    suggested method into a request object.
    """

    methods = card.get("suggested_methods")
    if not isinstance(methods, Sequence) or isinstance(methods, (str, bytes)):
        raise PortfolioAlternativesBuilderError("launchpad_card_has_no_suggested_methods")
    if len(methods) == 0:
        raise PortfolioAlternativesBuilderError("launchpad_card_has_no_suggested_methods")
    if method_index < 0 or method_index >= len(methods):
        raise PortfolioAlternativesBuilderError("launchpad_method_index_out_of_range")
    method = methods[method_index]
    if not isinstance(method, Mapping):
        raise PortfolioAlternativesBuilderError("launchpad_method_entry_invalid")
    method_id = _normalize_builder_method_id(method.get("candidate_method_id"))
    if not method_id:
        raise PortfolioAlternativesBuilderError("launchpad_method_id_missing")
    return PortfolioAlternativeRequest(
        candidate_method_id=method_id,
        goal=str(card.get("goal") or "") or None,
        source_card_id=str(card.get("card_id") or "") or None,
    )


def build_portfolio_alternative_plan(
    request: PortfolioAlternativeRequest,
    *,
    project_root: str | Path,
    python_executable: str | None = None,
    output_profile: str = DEFAULT_ALTERNATIVES_OUTPUT_PROFILE,
    execution_mode: str = DEFAULT_ALTERNATIVES_EXECUTION_MODE,
    then_compare: bool = True,
) -> PortfolioAlternativeBuildPlan:
    """Create a one-candidate plan that delegates to current factory plumbing."""

    raw_method_id = str(request.candidate_method_id or "").strip()
    method_id = _normalize_builder_method_id(raw_method_id) or raw_method_id
    mode = _normalize_builder_mode(
        request.mode,
        preset=_normalize_constraint_preset(request.constraint_preset),
        selected_method=raw_method_id,
    )
    candidate_id = candidate_id_for_builder_method(method_id, mode=mode)
    if candidate_id is None:
        candidate_id = LEGACY_METHOD_TO_CANDIDATE_ID.get(raw_method_id)
    if not candidate_id:
        raise PortfolioAlternativesBuilderError(f"unsupported_candidate_method:{method_id}")

    root = Path(project_root)
    py = python_executable or sys.executable
    command: list[str] = [
        py,
        str(root / "run_candidate_factory.py"),
        "--candidates",
        candidate_id,
        "--execution-mode",
        execution_mode,
        "--output-profile",
        output_profile,
    ]
    if then_compare:
        command.append("--then-compare")

    warnings: list[str] = []
    if any(
        value is not None
        for value in (
            request.constraint_preset,
            request.max_asset_weight,
            request.min_asset_weight,
            request.volatility_target,
            request.rebalancing_frequency,
            request.transaction_cost_assumption,
        )
    ):
        warnings.append("request_parameters_recorded_not_applied_v1")

    return PortfolioAlternativeBuildPlan(
        candidate_method_id=method_id,
        candidate_id=candidate_id,
        command=tuple(command),
        artifact_contract={
            "factory_run": "candidate_factory_run.json",
            "candidate_comparison": "candidate_comparison.json" if then_compare else None,
            "candidate_artifact_root": "resolved_by_candidate_factory_registry",
        },
        provenance={
            "source": "portfolio_alternatives_builder_v1",
            "goal": request.goal,
            "source_card_id": request.source_card_id,
            "method": method_id,
            "mode": mode,
            "delegates_to": "run_candidate_factory.py",
            "does_not_change_formulas": True,
            "does_not_generate_weights_until_executed": True,
        },
        warnings=tuple(warnings),
    )


RunSubprocess = Callable[..., subprocess.CompletedProcess[Any]]


def run_portfolio_alternative_plan(
    plan: PortfolioAlternativeBuildPlan,
    *,
    project_root: str | Path,
    dry_run: bool = True,
    runner: RunSubprocess = subprocess.run,
) -> subprocess.CompletedProcess[Any] | None:
    """Run a prepared plan only when explicitly requested by a caller.

    Default ``dry_run=True`` makes accidental execution impossible in tests and
    planning flows.
    """

    if dry_run:
        return None
    return runner(
        list(plan.command),
        cwd=str(Path(project_root)),
        check=False,
    )
