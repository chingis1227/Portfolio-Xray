from __future__ import annotations

"""
Portfolio variants (baseline constructions) outside the policy framework.

This module intentionally does NOT apply RC caps, discretionary overlays, or hidden policy filters to Equal-Weight, Risk-Parity, or Minimum-Variance baselines:

- no RC caps as optimization targets (RC_vol stays a report diagnostic)
- no ProLiquidity / mandate-specific layers on these baselines
- Minimum-Variance uses the same **feasibility/config box bounds** as ``run_optimization.py`` (:func:`src.optimization._build_bounds`), not extra custom mandate constraints

These variants are pure asset-level baselines built on the same eligible universe
and then evaluated by the existing metrics / stress-test / client-fit pipeline.

**Maximum diversification (constrained)** maximizes the diversification ratio
``(sigma' w) / sqrt(w' Sigma w)`` on monthly ``Sigma`` under the **same box bounds**
as the policy optimizer; see ``build_maximum_diversification_constrained``.

**Maximum diversification (unconstrained long-only)** maximizes the same diversification ratio
with only ``sum(w)=1`` and ``w_i >= 0`` (scipy bounds ``[0,1]`` per name); **no** policy
min/max, feasibility caps, or Young per-ticker caps as optimization constraints; see
``build_maximum_diversification_unconstrained``.

**Minimum CVaR (Rockafellar–Uryasev LP)** on monthly simple scenario returns: **uncapped**
``build_minimum_cvar_uncapped`` uses ``w_i \\in [0,1]`` and no project caps; **constrained**
``build_minimum_cvar_constrained`` uses the same ``_build_bounds`` box as MinVar/MaxDiv.

**Hierarchical Risk Parity (canonical)** builds long-only weights via correlation
distance, hierarchical clustering, and recursive bisection on monthly ``Sigma`` shared
with MinVar/MD via ``_mv_covariance_for_eligible``; **no** ``_build_bounds`` box and
**no** optimizer projection—unconstrained baseline comparable to canonical Risk Parity;
see ``build_hierarchical_risk_parity_baseline``.

Three Minimum-Variance construction modes:

- **minimum_variance_constrained** — **primary** project baseline for the lowest-volatility portfolio
  under the same long-only box bounds as ``run_optimization`` (feasibility + config min/max + Young
  caps when dual covariance is enabled). Answers: *what is the lowest volatility achievable under
  these constraints?*
- **minimum_variance_uncapped_long_only** — only ``w \\ge 0``, ``\\sum w = 1`` (no min/max
  weight, no young caps, no basket caps). Diagnostic / relaxed-bounds reference, not the primary
  constrained lowest-vol baseline.
- **minimum_variance_advanced_controls** — **not** that primary constrained baseline. Same box bounds
  as constrained plus optional **maximum** vol cap ``w'\\Sigma w \\le \\sigma_{target}^2 / 12`` on
  monthly ``\\Sigma``. Uses **Ledoit--Wolf** monthly ``\\Sigma`` for this variant regardless of
  ``covariance_shrinkage`` in config. **Default** ``minimum_variance_turnover_lambda = 0``: pure
  variance minimization on this advanced path (no L1). When ``minimum_variance_turnover_lambda > 0``
  and a valid **current** weight reference exists on the eligible universe, the problem becomes
  **rebalance-aware / turnover-controlled** minimum variance (L1 vs current weights only; equal-weight
  is never used)—*move toward lower risk without straying too far from current weights*, not the pure
  lowest-volatility-under-constraints answer.
"""

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Iterable, Tuple

import numpy as np
import pandas as pd
import yaml
from scipy.optimize import linprog, minimize

from src.config_schema import PortfolioConfig
from src.optimization_status import normalize_optimization_quality_status
from src.optimizer_input_fingerprints import (
    optimizer_config_fingerprint,
    returns_panel_disclosure,
    universe_fingerprint,
)
from src.optimizer_methodology import (
    covariance_methodology_disclosure,
    young_etf_methodology_disclosure,
)
from src.hrp_weights import hrp_long_only_weights
from src.optimization import MIN_WEIGHT_DEFAULT, _build_bounds
from src.risk_contrib import cov_matrix_monthly, rc_vol_window
from src.risk_budgeting import (
    load_merged_universe_rows,
    normalize_budget_map,
    pc_from_w,
    resolve_class_risk_targets,
    risk_budget_bucket_from_row,
    solve_asset_risk_budget_spinu,
    solve_class_risk_budget_slsqp,
    TAXONOMY_ETF_REL,
    TAXONOMY_STOCK_REL,
)
from src.risk_parity_spinu import repair_covariance_psd, spinu_ccd_equal_budget
from src.robust_mv import (
    concentration_metrics,
    james_stein_shrink_means,
    normalize_robust_mv_covariance_method,
    psd_status_after_repair,
    shrunk_covariance_monthly,
    solve_robust_mean_variance,
)
from src.windows import slice_window
from src.young_etfs_dual_cov import build_dual_covariance_and_mu, per_ticker_young_weight_caps


BASELINE_EQ_LABEL = "Equal-Weight Portfolio"
BASELINE_EQ_BY_CLASS_LABEL = "Equal-Weight by Asset-Class Portfolio"
BASELINE_RP_LABEL = "Risk Parity Portfolio"
BASELINE_MV_LABEL = "Minimum Variance Portfolio"
BASELINE_MV_UNCAPPED_LABEL = "Minimum Variance (Uncapped Long-Only) Portfolio"
BASELINE_MV_ADVANCED_LABEL = "Minimum Variance (Advanced Controls) Portfolio"
BASELINE_MD_LABEL = "Maximum Diversification Portfolio"
BASELINE_MD_UNCONSTRAINED_LABEL = "Maximum Diversification (Unconstrained Long-Only) Portfolio"
BASELINE_HRP_LABEL = "Hierarchical Risk Parity Portfolio"
BASELINE_MCVAR_UNCAPPED_LABEL = "Minimum CVaR (Uncapped) Portfolio"
BASELINE_MCVAR_CONSTRAINED_LABEL = "Minimum CVaR (Constrained) Portfolio"
BASELINE_ROBUST_MV_UNCAPPED_LABEL = "Robust Mean–Variance (Uncapped Long-Only) Portfolio"
BASELINE_ROBUST_MV_CONSTRAINED_LABEL = "Robust Mean–Variance (Constrained) Portfolio"
BASELINE_RISK_BUDGET_BY_ASSET_CLASS_LABEL = "Risk Budget by Asset-Class Portfolio"
BASELINE_RISK_BUDGET_BY_ASSET_LABEL = "Risk Budget by Asset Portfolio"

# Roles for reporting / metadata (which question each variant answers).
MV_BASELINE_ROLE_PRIMARY_LOWEST_VOL_UNDER_CONSTRAINTS = (
    "primary_lowest_volatility_under_project_constraints"
)
MV_BASELINE_ROLE_REBALANCE_AWARE_TURNOVER_CONTROLLED = (
    "rebalance_aware_turnover_controlled_minimum_variance"
)
MV_BASELINE_ROLE_ADVANCED_CONTROLS_PURE_PATH = "advanced_controls_pure_minimum_variance"

OPTIMIZER_NAME_MINIMUM_VARIANCE_CONSTRAINED = "minimum_variance_constrained"
OPTIMIZER_NAME_MINIMUM_VARIANCE_UNCAPPED = "minimum_variance_uncapped_long_only"
OPTIMIZER_NAME_MINIMUM_VARIANCE_ADVANCED = "minimum_variance_advanced_controls"
OPTIMIZER_NAME_MAXIMUM_DIVERSIFICATION_CONSTRAINED = "maximum_diversification_constrained"
OPTIMIZER_NAME_MAXIMUM_DIVERSIFICATION_UNCONSTRAINED = "maximum_diversification_unconstrained"
OPTIMIZER_NAME_HIERARCHICAL_RISK_PARITY = "hierarchical_risk_parity"
OPTIMIZER_NAME_MINIMUM_CVAR_UNCAPPED = "minimum_cvar_uncapped"
OPTIMIZER_NAME_MINIMUM_CVAR_CONSTRAINED = "minimum_cvar_constrained"
OPTIMIZER_NAME_ROBUST_MEAN_VARIANCE_UNCAPPED = "robust_mean_variance_uncapped"
OPTIMIZER_NAME_ROBUST_MEAN_VARIANCE_CONSTRAINED = "robust_mean_variance_constrained"
OPTIMIZER_NAME_RISK_BUDGET_BY_ASSET_CLASS = "risk_budget_by_asset_class"
OPTIMIZER_NAME_RISK_BUDGET_BY_ASSET = "risk_budget_by_asset"

ROBUST_MV_SOLVER = "SLSQP"
ROBUST_MV_OBJECTIVE_MIN = (
    "minimize lambda * w' Sigma w - mu' w on monthly shrunk Sigma and James–Stein shrunk mu"
)

# Exported on successful Robust MV builds for audit / reporting (see AGENTS.md / SPEC.md).
ROBUST_MV_VARIANT_ROLE = "return_aware_statistical_benchmark"
ROBUST_MV_VARIANT_SUMMARY = (
    "Robust Mean–Variance is a benchmark portfolio construction method: it estimates weights "
    "from a mean–variance optimum using statistically stabilized inputs—James–Stein shrinkage "
    "for expected returns, Ledoit–Wolf or OAS shrinkage for the covariance matrix—and an "
    "internal risk-aversion parameter λ on monthly portfolio variance that trades off expected "
    "return versus variance. λ is not intended as a client-facing dial; the project provides "
    "`run_robust_mv_lambda_calibration.py` to evaluate a λ grid against IPS-style limits "
    "(volatility, mandate maximum drawdown, diagnostic synthetic stress loss alignment where "
    "configured, concentration caps where configured). Interpret calibrated Robust MV outputs "
    "as a return-aware statistical benchmark, a sanity check versus the policy optimizer "
    "pipeline, and a comparison point versus Equal Weight, Equal Weight by asset class, Risk "
    "Parity, HRP, Minimum Variance, Maximum Diversification, and Minimum CVaR—not a replacement "
    "for `run_optimization.py`."
)

MINIMUM_CVAR_SOLVER = "HiGHS"
MINIMUM_CVAR_OBJECTIVE = (
    "Rockafellar-Uryasev LP: min alpha + 1/(T*(1-gamma))*sum(z_t) "
    "s.t. z_t >= -(R w)_t - alpha, z_t>=0, sum(w)=1, box bounds on w"
)

MINIMUM_VARIANCE_SOLVER = "SLSQP"
MINIMUM_VARIANCE_OBJECTIVE = "0.5 * w.T @ covariance @ w"
MAXIMUM_DIVERSIFICATION_SOLVER = "SLSQP"
MAXIMUM_DIVERSIFICATION_OBJECTIVE = "(sigma' w) / sqrt(w' Sigma w) on monthly Sigma; DR dimensionless"
CANDIDATE_OPTIMIZER_RUN_METADATA_SCHEMA_VERSION = "candidate_optimizer_run_metadata_v1"


def _copy_present(diagnostics: Dict[str, object], keys: Iterable[str]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k in keys:
        if k in diagnostics:
            out[k] = diagnostics[k]
    return out


def _bounds_export(bounds: list[tuple[float, float]], cols: list[str]) -> Dict[str, Dict[str, float]]:
    return {
        str(cols[i]): {"min": float(bounds[i][0]), "max": float(bounds[i][1])}
        for i in range(len(cols))
    }


def _optimization_quality_status(diagnostics: Dict[str, object]) -> str:
    fallback_used = bool(diagnostics.get("fallback_used", False))
    solver_success = diagnostics.get("solver_success")
    solver_status = diagnostics.get("solver_status")
    if solver_success is None:
        solver_success = diagnostics.get("linprog_success")
    if solver_status is None:
        solver_status = diagnostics.get("linprog_status")
    return normalize_optimization_quality_status(
        "failed" if diagnostics.get("reason") else None,
        solver_success=solver_success,
        solver_status=solver_status,
        fallback_used=fallback_used,
    )


OPTIMIZER_INPUT_FINGERPRINT_EXPORT_KEYS = (
    "returns_panel_fingerprint",
    "config_fingerprint",
    "universe_fingerprint",
    "returns_panel_rows",
    "returns_panel_start",
    "returns_panel_end",
    "estimator_input_columns",
)


def _estimator_returns_window(
    monthly_returns: pd.DataFrame,
    analysis_end: str,
    window_months: int,
    cols: list[str],
) -> pd.DataFrame:
    available = [str(c) for c in cols if str(c) in monthly_returns.columns]
    if not available:
        return pd.DataFrame(index=pd.DatetimeIndex([]))
    return slice_window(monthly_returns[available], analysis_end, window_months)


def _attach_optimizer_input_fingerprints(
    diagnostics: Dict[str, object],
    cfg: PortfolioConfig,
    monthly_returns: pd.DataFrame,
    analysis_end: str,
    window_months: int,
    cols: list[str],
    *,
    extra_config: dict[str, Any] | None = None,
    returns_window: pd.DataFrame | None = None,
) -> None:
    panel = returns_window if returns_window is not None else _estimator_returns_window(
        monthly_returns, analysis_end, window_months, cols
    )
    disclosure = returns_panel_disclosure(panel)
    diagnostics.update(disclosure)
    diagnostics["estimator_input_columns"] = [str(c) for c in cols]
    diagnostics["config_fingerprint"] = optimizer_config_fingerprint(
        cfg,
        extra={
            "optimizer_name": diagnostics.get("optimizer_name"),
            "analysis_end": str(analysis_end),
            "window_months": int(window_months),
            **(extra_config or {}),
        },
    )
    diagnostics["universe_fingerprint"] = universe_fingerprint(cols)


def _attach_young_etf_methodology_diagnostics(
    diagnostics: Dict[str, object],
    cfg: PortfolioConfig,
    *,
    young_mode: str | None,
    young_diagnostics: dict[str, Any] | None,
    per_ticker_caps: dict[str, float] | None,
    role: str,
) -> None:
    policy = getattr(cfg, "young_etf_optimization_policy", None) or {}
    diagnostics["young_etf_policy_enabled"] = bool(policy.get("enabled", True))
    diagnostics["young_etf_policy_role"] = role
    diagnostics["young_etf_policy"] = dict(policy)
    diagnostics["young_etf_dual_mode"] = young_mode
    if young_diagnostics is not None:
        diagnostics["young_etf_diagnostics"] = young_diagnostics
    if per_ticker_caps:
        diagnostics["per_ticker_young_caps"] = dict(per_ticker_caps)


def _candidate_optimizer_run_metadata(diagnostics: Dict[str, object]) -> Dict[str, Any]:
    """Normalized candidate-only optimizer disclosure for baseline metadata exports."""
    optimizer_name = diagnostics.get("optimizer_name")
    objective = diagnostics.get("objective", diagnostics.get("objective_minimize"))
    solver_success = diagnostics.get("solver_success")
    solver_status = diagnostics.get("solver_status")
    solver_message = diagnostics.get("solver_message")
    if solver_success is None:
        solver_success = diagnostics.get("linprog_success")
    if solver_status is None:
        solver_status = diagnostics.get("linprog_status")
    if solver_message is None:
        solver_message = diagnostics.get("linprog_message")

    parameters = _copy_present(
        diagnostics,
        (
            "robust_mv_lambda",
            "cvar_confidence_level",
            "tail_fraction",
            "n_scenarios",
            "tail_effective_obs",
            "lambda_turnover",
            "lambda_turnover_effective",
            "l1_penalty_used",
            "l1_reference_source",
            "volatility_target_used",
            "target_volatility",
            "target_variance_monthly_cap",
            "volatility_constraint_feasible",
            "volatility_constraint_binding",
        ),
    )
    expected_return_method = "not_used"
    if optimizer_name in (
        OPTIMIZER_NAME_ROBUST_MEAN_VARIANCE_CONSTRAINED,
        OPTIMIZER_NAME_ROBUST_MEAN_VARIANCE_UNCAPPED,
    ):
        expected_return_method = str(diagnostics.get("mu_shrinkage_method") or "james_stein")
    young_methodology = young_etf_methodology_disclosure(
        enabled=bool(diagnostics.get("young_etf_policy_enabled", False)),
        role=str(diagnostics.get("young_etf_policy_role") or "not_used"),
        mode=diagnostics.get("young_etf_dual_mode"),
        policy=diagnostics.get("young_etf_policy")
        if isinstance(diagnostics.get("young_etf_policy"), dict)
        else None,
        diagnostics=diagnostics.get("young_etf_diagnostics")
        if isinstance(diagnostics.get("young_etf_diagnostics"), dict)
        else None,
        per_ticker_caps=diagnostics.get("per_ticker_young_caps")
        if isinstance(diagnostics.get("per_ticker_young_caps"), dict)
        else None,
    )
    covariance_methodology = covariance_methodology_disclosure(
        method=diagnostics.get("covariance_method"),
        source=str(diagnostics.get("covariance_source") or "monthly_return_panel"),
        analysis_end=diagnostics.get("analysis_end"),
        window_months=diagnostics.get("window_months"),
        returns_panel_fingerprint=diagnostics.get("returns_panel_fingerprint"),
        shrinkage_enabled=diagnostics.get(
            "shrinkage_used", diagnostics.get("shrinkage_applied")
        ),
        psd_repair_used=diagnostics.get("psd_repair_used"),
        psd_status=diagnostics.get("psd_status"),
        young_etf=young_methodology,
    )

    return {
        "schema_version": CANDIDATE_OPTIMIZER_RUN_METADATA_SCHEMA_VERSION,
        "optimizer_role": "candidate_only",
        "candidate_only": True,
        "method_id": optimizer_name,
        "entrypoint_family": "candidate_portfolio_builder",
        "objective": objective,
        "input_window": {
            "analysis_end": diagnostics.get("analysis_end"),
            "window_months": diagnostics.get("window_months"),
            "return_frequency": "monthly_simple",
            "returns_panel_start": diagnostics.get("returns_panel_start"),
            "returns_panel_end": diagnostics.get("returns_panel_end"),
            "returns_panel_rows": diagnostics.get("returns_panel_rows"),
        },
        "input_fingerprints": {
            "returns_panel_fingerprint": diagnostics.get("returns_panel_fingerprint"),
            "config_fingerprint": diagnostics.get("config_fingerprint"),
            "universe_fingerprint": diagnostics.get("universe_fingerprint"),
        },
        "expected_return": {
            "uses_expected_returns": expected_return_method != "not_used",
            "method": expected_return_method,
            "analysis_end": diagnostics.get("analysis_end"),
            "returns_panel_fingerprint": diagnostics.get("returns_panel_fingerprint"),
        },
        "covariance": {
            "method": diagnostics.get("covariance_method"),
            "analysis_end": diagnostics.get("analysis_end"),
            "shrinkage_used": diagnostics.get(
                "shrinkage_used", diagnostics.get("shrinkage_applied")
            ),
            "psd_repair_used": diagnostics.get("psd_repair_used"),
            "psd_status": diagnostics.get("psd_status"),
            "young_etf_dual_mode": diagnostics.get("young_etf_dual_mode"),
            "returns_panel_fingerprint": diagnostics.get("returns_panel_fingerprint"),
            "methodology": covariance_methodology,
            "methodology_summary": covariance_methodology["human_summary"],
        },
        "young_etf_methodology": young_methodology,
        "universe": {
            "eligible_universe": diagnostics.get("eligible_universe")
            or diagnostics.get("universe_eligible"),
            "estimator_input_columns": diagnostics.get("estimator_input_columns"),
            "universe_fingerprint": diagnostics.get("universe_fingerprint"),
        },
        "constraints": {
            "active_constraints": diagnostics.get("active_constraints"),
            "constraints_used": diagnostics.get("constraints_used"),
            "constraints_not_used": diagnostics.get("constraints_not_used"),
            "bounds_used": diagnostics.get("bounds_used"),
            "constraint_summary": diagnostics.get("constraint_summary"),
            "binding_constraints": diagnostics.get("binding_constraints"),
        },
        "solver": {
            "name": diagnostics.get("solver"),
            "success": solver_success,
            "status": solver_status,
            "message": solver_message,
            "fallback_used": bool(diagnostics.get("fallback_used", False)),
            "fallback_reason": diagnostics.get("fallback_reason"),
            "optimization_quality_status": _optimization_quality_status(diagnostics),
        },
        "parameters": parameters,
        "outputs": {
            "final_weights": diagnostics.get("final_weights"),
            "portfolio_variance": diagnostics.get("portfolio_variance"),
            "annualized_volatility": diagnostics.get("annualized_volatility"),
            "objective_value": diagnostics.get(
                "objective_value", diagnostics.get("cvar_objective_value")
            ),
        },
        "notes": {
            "does_not_write_policy_weights": True,
            "does_not_apply_proliquidity": True,
            "does_not_apply_legacy_mandate_release_gate": True,
        },
    }


def _metadata_with_candidate_optimizer_run_metadata(
    diagnostics: Dict[str, object],
    keys: Iterable[str],
) -> Dict[str, Any]:
    out = _copy_present(diagnostics, tuple(keys) + OPTIMIZER_INPUT_FINGERPRINT_EXPORT_KEYS)
    out["optimizer_run_metadata"] = _candidate_optimizer_run_metadata(diagnostics)
    return out

MINIMUM_VARIANCE_METADATA_EXPORT_KEYS = (
    "optimizer_name",
    "solver",
    "objective",
    "analysis_end",
    "window_months",
    "minimum_variance_baseline_role",
    "minimum_variance_interpretation",
    "covariance_method",
    "shrinkage_used",
    "psd_repair_used",
    "young_etf_dual_mode",
    "eligible_universe",
    "final_weights",
    "portfolio_variance",
    "annualized_volatility",
    "solver_status",
    "solver_success",
    "solver_message",
    "max_weight",
    "min_weight",
    "active_constraints",
    "bounds_used",
    "constraint_summary",
    "fallback_used",
)


def minimum_variance_baseline_metadata_export(diagnostics: Dict[str, object]) -> Dict[str, Any]:
    """Structured fields for ``baseline_weights_metadata.json`` / summary blobs (constrained variant)."""
    return _metadata_with_candidate_optimizer_run_metadata(
        diagnostics, MINIMUM_VARIANCE_METADATA_EXPORT_KEYS
    )


MINIMUM_VARIANCE_UNCAPPED_METADATA_EXPORT_KEYS = (
    "optimizer_name",
    "solver",
    "objective",
    "analysis_end",
    "window_months",
    "constraints_used",
    "constraints_not_used",
    "covariance_method",
    "shrinkage_used",
    "psd_repair_used",
    "eligible_universe",
    "final_weights",
    "portfolio_variance",
    "annualized_volatility",
    "solver_status",
    "solver_success",
    "solver_message",
    "bounds_used",
    "constraint_summary",
    "fallback_used",
)


def minimum_variance_uncapped_metadata_export(diagnostics: Dict[str, object]) -> Dict[str, Any]:
    return _metadata_with_candidate_optimizer_run_metadata(
        diagnostics, MINIMUM_VARIANCE_UNCAPPED_METADATA_EXPORT_KEYS
    )


MINIMUM_VARIANCE_ADVANCED_METADATA_EXPORT_KEYS = (
    "optimizer_name",
    "solver",
    "objective",
    "analysis_end",
    "window_months",
    "minimum_variance_baseline_role",
    "minimum_variance_interpretation",
    "lambda_turnover",
    "lambda_turnover_effective",
    "l1_penalty_used",
    "l1_reference_source",
    "current_portfolio_weights_available",
    "l1_distance_to_current_portfolio",
    "l1_penalty_value",
    "l1_disabled_reason",
    "volatility_target_used",
    "target_volatility",
    "target_variance_monthly_cap",
    "volatility_constraint_binding",
    "volatility_constraint_feasible",
    "active_constraints",
    "bounds_used",
    "constraint_summary",
    "binding_constraints",
    "covariance_method",
    "shrinkage_used",
    "young_etf_dual_mode",
    "psd_repair_used",
    "solver_status",
    "solver_success",
    "solver_message",
    "final_weights",
    "annualized_volatility",
    "portfolio_variance",
    "fallback_used",
)


def minimum_variance_advanced_metadata_export(diagnostics: Dict[str, object]) -> Dict[str, Any]:
    return _metadata_with_candidate_optimizer_run_metadata(
        diagnostics, MINIMUM_VARIANCE_ADVANCED_METADATA_EXPORT_KEYS
    )


def advanced_minimum_variance_weights_txt_label(diagnostics: Dict[str, object]) -> str:
    """Label for ``weights.txt``; when L1 is active, state rebalance-aware / not pure lowest-vol."""
    if diagnostics.get("l1_penalty_used"):
        return (
            f"{BASELINE_MV_ADVANCED_LABEL} — rebalance-aware / turnover-controlled "
            f"(L1 vs current portfolio weights; not pure lowest-volatility-under-constraints)"
        )
    return BASELINE_MV_ADVANCED_LABEL


MAXIMUM_DIVERSIFICATION_METADATA_EXPORT_KEYS = (
    "optimizer_name",
    "solver",
    "objective",
    "analysis_end",
    "window_months",
    "covariance_method",
    "shrinkage_used",
    "psd_repair_used",
    "young_etf_dual_mode",
    "eligible_universe",
    "final_weights",
    "portfolio_variance",
    "annualized_volatility",
    "diversification_ratio",
    "weighted_avg_asset_vol_monthly",
    "solver_status",
    "solver_success",
    "solver_message",
    "max_weight",
    "min_weight",
    "active_constraints",
    "bounds_used",
    "constraint_summary",
    "fallback_used",
)


def maximum_diversification_baseline_metadata_export(diagnostics: Dict[str, object]) -> Dict[str, Any]:
    """Structured fields for maximum-diversification ``baseline_weights_metadata.json``."""
    return _metadata_with_candidate_optimizer_run_metadata(
        diagnostics, MAXIMUM_DIVERSIFICATION_METADATA_EXPORT_KEYS
    )


HIERARCHICAL_RISK_PARITY_METADATA_EXPORT_KEYS = (
    "optimizer_name",
    "covariance_method",
    "shrinkage_used",
    "psd_repair_used",
    "young_etf_dual_mode",
    "eligible_universe",
    "final_weights",
    "portfolio_variance",
    "annualized_volatility",
    "hrp_linkage_method",
    "hrp_linkage_fallback_from_ward",
    "hrp_distance",
    "hrp_seriation_indices",
    "hrp_weights_sum",
)


def hierarchical_risk_parity_baseline_metadata_export(diagnostics: Dict[str, object]) -> Dict[str, Any]:
    """Structured fields for HRP ``baseline_weights_metadata.json``."""
    out: Dict[str, Any] = {}
    for k in HIERARCHICAL_RISK_PARITY_METADATA_EXPORT_KEYS:
        if k in diagnostics:
            out[k] = diagnostics[k]
    return out


MINIMUM_CVAR_METADATA_EXPORT_KEYS = (
    "optimizer_name",
    "solver",
    "objective",
    "analysis_end",
    "window_months",
    "cvar_confidence_level",
    "tail_fraction",
    "n_scenarios",
    "cvar_objective_value",
    "empirical_cvar_loss",
    "linprog_status",
    "linprog_success",
    "linprog_message",
    "tail_effective_obs",
    "tail_scenarios_used",
    "covariance_method",
    "shrinkage_used",
    "psd_repair_used",
    "young_etf_dual_mode",
    "eligible_universe",
    "final_weights",
    "portfolio_variance",
    "annualized_volatility",
    "max_weight",
    "min_weight",
    "weight_bounds_note",
    "bounds_used",
    "constraint_summary",
)


def minimum_cvar_baseline_metadata_export(diagnostics: Dict[str, object]) -> Dict[str, Any]:
    """Structured fields for minimum-CVaR ``baseline_weights_metadata.json`` (uncapped or constrained)."""
    return _metadata_with_candidate_optimizer_run_metadata(
        diagnostics, MINIMUM_CVAR_METADATA_EXPORT_KEYS
    )


ROBUST_MV_METADATA_EXPORT_KEYS = (
    "robust_mv_variant_role",
    "robust_mv_variant_summary",
    "optimizer_name",
    "solver",
    "objective_minimize",
    "analysis_end",
    "robust_mv_lambda",
    "mu_shrinkage_method",
    "covariance_method",
    "covariance_shrinkage_sklearn",
    "shrinkage_applied",
    "psd_status",
    "psd_repair_used",
    "window_months",
    "eligible_universe",
    "raw_mu",
    "shrunk_mu",
    "shrinkage_target",
    "shrinkage_intensity",
    "bounds_used",
    "constraint_summary",
    "solver_status",
    "solver_success",
    "solver_message",
    "objective_value",
    "max_weight",
    "min_weight",
    "concentration_metrics",
    "final_weights",
    "portfolio_variance",
    "annualized_volatility",
)


def robust_mean_variance_baseline_metadata_export(diagnostics: Dict[str, object]) -> Dict[str, Any]:
    """Structured fields for Robust Mean–Variance ``baseline_weights_metadata.json`` / summaries."""
    return _metadata_with_candidate_optimizer_run_metadata(
        diagnostics, ROBUST_MV_METADATA_EXPORT_KEYS
    )


RISK_BUDGET_METADATA_EXPORT_KEYS = (
    "risk_budgeting_method",
    "optimizer_name",
    "solver",
    "covariance_method",
    "preset_used",
    "manual_override_used",
    "target_risk_budgets",
    "realized_risk_contributions",
    "risk_budget_tracking_error",
    "max_budget_deviation",
    "budget_buckets_used",
    "tickers_per_bucket",
    "asset_classes_used",
    "tickers_per_class",
    "excluded_missing_asset_class",
    "taxonomy_universe_files",
    "ticker_taxonomy_source",
    "solver_status",
    "solver_success",
    "solver_message",
    "fallback_used",
    "unused_target_buckets",
    "targets_renormalized",
    "warnings",
    "reason",
    "universe_eligible",
    "universe_coverage",
    "spinu_converged",
    "spinu_iterations",
    "nit",
    "cov_psd_repaired",
    "eligible_universe",
    "final_weights",
)


def risk_budgeting_baseline_metadata_export(diagnostics: Dict[str, object]) -> Dict[str, Any]:
    """Structured fields for risk budgeting ``baseline_weights_metadata.json``."""
    out: Dict[str, Any] = {}
    for k in RISK_BUDGET_METADATA_EXPORT_KEYS:
        if k in diagnostics:
            out[k] = diagnostics[k]
    return out


EQUAL_WEIGHT_METHOD_BY_ASSETS = "equal_weight_by_assets"
EQUAL_WEIGHT_METHOD_BY_ASSET_CLASS = "equal_weight_by_asset_class_then_assets"
L1_REFERENCE_CURRENT_PORTFOLIO = "current_portfolio"

EQUAL_WEIGHT_METADATA_EXPORT_KEYS = (
    "equal_weight_method",
    "asset_classes_used",
    "class_weights",
    "tickers_per_class",
    "excluded_missing_asset_class",
    "warnings",
    "reason",
    "baseline_weights_note",
    "universe_eligible",
)


def equal_weight_baseline_metadata_export(diagnostics: Dict[str, object]) -> Dict[str, Any]:
    """Structured fields for ``baseline_weights_metadata.json`` / summary blobs."""
    out: Dict[str, Any] = {}
    for k in EQUAL_WEIGHT_METADATA_EXPORT_KEYS:
        if k in diagnostics:
            out[k] = diagnostics[k]
    return out


@dataclass
class BaselineWeightsResult:
    weights: Dict[str, float]
    status: str
    diagnostics: Dict[str, object]


def _eligible_universe_from_returns(
    cfg: PortfolioConfig,
    monthly_returns: pd.DataFrame,
    analysis_end: str,
    window_months: int,
) -> Tuple[list[str], Dict[str, float]]:
    """
    Derive the eligible investable universe for baselines.

    Rules:
    - Use the same tickers universe as config.tickers.
    - Exclude assets only if they fail the same minimum data / coverage checks
      as used elsewhere for portfolio analytics (simple window coverage filter).
    - No hidden filters.
    """
    tickers = [t for t in cfg.tickers if t in monthly_returns.columns]
    coverage_threshold = getattr(cfg, "coverage_threshold", 0.90) or 0.90
    end_ts = pd.Timestamp(analysis_end)
    eligible: list[str] = []
    coverage: Dict[str, float] = {}

    # Simple coverage: share of non-NaN points in the window.
    for t in tickers:
        series = monthly_returns[t]
        window = slice_window(series, analysis_end, window_months).dropna()
        if window.empty:
            coverage[t] = 0.0
            continue
        total = (end_ts.to_period("M") - window.index.min().to_period("M")).n + 1
        cov_ratio = len(window) / float(total) if total > 0 else 0.0
        coverage[t] = cov_ratio
        if cov_ratio >= coverage_threshold:
            eligible.append(t)

    return eligible, coverage


def _project_root_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def load_ticker_asset_class_map(
    *,
    etf_universe_path: Path | None = None,
    stock_universe_path: Path | None = None,
) -> dict[str, str]:
    """
    Merge ETF and stock taxonomy YAML maps (ticker -> asset_class).
    ETFs are loaded first; stock entries fill tickers missing from ETFs.
    """

    root = _project_root_dir()
    etf_p = etf_universe_path or (root / "config" / "etf_universe.yml")
    stock_p = stock_universe_path or (root / "config" / "stock_universe.yml")
    merged: dict[str, str] = {}
    secondary: dict[str, str] = {}

    for path, is_primary in ((etf_p, True), (stock_p, False)):
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        if not isinstance(data, list):
            continue
        for row in data:
            if not isinstance(row, dict):
                continue
            ticker = row.get("ticker")
            ac = row.get("asset_class")
            if not isinstance(ticker, str) or not isinstance(ac, str):
                continue
            tik = ticker.strip()
            acl = ac.strip()
            if not tik or not acl:
                continue
            if is_primary:
                merged[tik] = acl
            else:
                secondary[tik] = acl

    for tik, acl in secondary.items():
        merged.setdefault(tik, acl)

    return merged


def build_equal_weight_baseline(
    cfg: PortfolioConfig,
    monthly_returns: pd.DataFrame,
    analysis_end: str,
    window_months: int,
) -> BaselineWeightsResult:
    """
    Equal-Weight Portfolio:
    - Universe: same eligible tickers as main engine, but without policy logic.
    - If N eligible assets, each weight = 1/N.
    - Long-only, fully invested; no caps, no RC constraints, no overlays.
    """
    eligible, coverage = _eligible_universe_from_returns(
        cfg, monthly_returns, analysis_end, window_months
    )
    diagnostics: Dict[str, object] = {
        "universe_eligible": eligible,
        "universe_coverage": coverage,
        "equal_weight_method": EQUAL_WEIGHT_METHOD_BY_ASSETS,
    }

    if len(eligible) < 2:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_INFEASIBLE_UNIVERSE",
            diagnostics={
                **diagnostics,
                "asset_classes_used": [],
                "class_weights": {},
                "tickers_per_class": {},
                "excluded_missing_asset_class": [],
                "reason": "Fewer than 2 eligible assets for Equal-Weight baseline",
            },
        )

    n = len(eligible)
    w_eq = 1.0 / float(n)
    weights: Dict[str, float] = {t: 0.0 for t in cfg.tickers}
    for t in eligible:
        weights[t] = w_eq

    diagnostics["asset_classes_used"] = []
    diagnostics["class_weights"] = {}
    diagnostics["tickers_per_class"] = {}
    diagnostics["excluded_missing_asset_class"] = []
    diagnostics["baseline_weights_note"] = (
        "Per-asset Equal-Weight baseline; taxonomy fields intentionally empty "
        "(use equal_weight_by_asset_class_then_assets for class-balanced weights metadata)."
    )

    return BaselineWeightsResult(
        weights=weights,
        status="OK",
        diagnostics=diagnostics,
    )


def build_equal_weight_by_asset_class_baseline(
    cfg: PortfolioConfig,
    monthly_returns: pd.DataFrame,
    analysis_end: str,
    window_months: int,
    *,
    asset_class_lookup: dict[str, str] | None = None,
    etf_universe_path: Path | None = None,
    stock_universe_path: Path | None = None,
) -> BaselineWeightsResult:
    """
    Equal-weight over asset classes (each class receives 1 / n_classes),
    then equal-weight within each class among classified eligible assets.

    Eligible-universe filtering matches :func:`build_equal_weight_baseline`.
    Tickers without ``asset_class`` in the merged taxonomy lookup are excluded
    from the portfolio weights and listed in diagnostics.
    """

    eligible, coverage = _eligible_universe_from_returns(
        cfg, monthly_returns, analysis_end, window_months
    )
    taxonomy = (
        asset_class_lookup
        if asset_class_lookup is not None
        else load_ticker_asset_class_map(
            etf_universe_path=etf_universe_path,
            stock_universe_path=stock_universe_path,
        )
    )

    excluded_missing: list[str] = []
    tickers_kept: list[str] = []
    for t in eligible:
        ac = taxonomy.get(t)
        if not ac:
            excluded_missing.append(t)
        else:
            tickers_kept.append(t)

    by_class: Dict[str, list[str]] = {}
    for t in tickers_kept:
        acl = taxonomy[t]
        by_class.setdefault(acl, []).append(t)

    for k in list(by_class.keys()):
        by_class[k] = sorted(by_class[k])

    nonempty_classes = sorted(by_class.keys())
    diagnostics: Dict[str, object] = {
        "universe_eligible": eligible,
        "universe_coverage": coverage,
        "equal_weight_method": EQUAL_WEIGHT_METHOD_BY_ASSET_CLASS,
        "asset_classes_used": list(nonempty_classes),
        "excluded_missing_asset_class": sorted(set(excluded_missing)),
        "tickers_per_class": {cl: list(tks) for cl, tks in sorted(by_class.items())},
        "baseline_weights_note": (
            "Class-balanced Equal-Weight: equal budget per asset class "
            "(non-empty classes only), equal split inside each class."
        ),
    }

    warns: list[str] = []
    if excluded_missing:
        warns.append(
            "Excluded eligible tickers with no asset_class in taxonomy: "
            + ", ".join(sorted(set(excluded_missing)))
        )

    if not nonempty_classes:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_INFEASIBLE_UNIVERSE",
            diagnostics={
                **diagnostics,
                "class_weights": {},
                "reason": (
                    "No eligible tickers with asset_class taxonomy after exclusions"
                ),
                "warnings": warns,
            },
        )

    if len(tickers_kept) < 2:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_INFEASIBLE_UNIVERSE",
            diagnostics={
                **diagnostics,
                "class_weights": {
                    cl: round(1.0 / len(nonempty_classes), 14)
                    for cl in nonempty_classes
                },
                "reason": (
                    "Fewer than 2 taxonomy-classified eligible assets for "
                    "Equal-Weight by Asset-Class baseline"
                ),
                "warnings": warns,
            },
        )

    n_classes = len(nonempty_classes)
    class_budget = 1.0 / float(n_classes)
    cw = {cl: class_budget for cl in nonempty_classes}
    diagnostics["class_weights"] = {cl: float(cw[cl]) for cl in nonempty_classes}

    if warns:
        diagnostics["warnings"] = warns

    weights: Dict[str, float] = {t: 0.0 for t in cfg.tickers}

    for cl in nonempty_classes:
        members = by_class[cl]
        if not members:
            continue
        w_each = float(class_budget) / float(len(members))
        for tik in members:
            weights[tik] = w_each

    return BaselineWeightsResult(
        weights=weights,
        status="OK",
        diagnostics=diagnostics,
    )


def _pc_from_w_static(w_vec: np.ndarray, cov: np.ndarray) -> np.ndarray:
    var_p = float(w_vec @ cov @ w_vec)
    if var_p <= 1e-16:
        return np.ones_like(w_vec) / float(len(w_vec))
    m = cov @ w_vec
    return (w_vec * m) / var_p


def _risk_parity_slsqp_fallback(
    cov: np.ndarray,
    cols: list[str],
    *,
    tol: float = 1e-8,
) -> Tuple[np.ndarray, Any, str]:
    """Emergency fallback: SLSQP minimizing squared RC deviation from 1/n."""
    n = len(cols)
    target_rc = 1.0 / float(n)

    def objective(w_vec: np.ndarray) -> float:
        pc = _pc_from_w_static(w_vec, cov)
        diff = pc - target_rc
        return float(np.dot(diff, diff))

    x0 = np.ones(n) / float(n)
    bounds = [(0.0, 1.0)] * n
    constraints = [{"type": "eq", "fun": lambda w_vec: float(np.sum(w_vec) - 1.0)}]

    res = minimize(
        objective,
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 5000, "ftol": tol},
    )

    if res.x is None or not np.all(np.isfinite(res.x)):
        return np.array([]), res, "FAIL_NUMERICAL"
    w = np.clip(res.x, 0.0, None)
    s = float(w.sum())
    if s <= 1e-12:
        return np.array([]), res, "FAIL_NUMERICAL"
    w = w / s
    status = "OK" if res.success else "APPROXIMATE"
    return w, res, status


def _risk_parity_solver(
    cov_df: pd.DataFrame,
    tickers: Iterable[str],
    *,
    tol: float = 1e-8,
    spinu_max_iter: int = 50_000,
    spinu_tol: float = 1e-10,
    spinu_eps_floor: float = 1e-12,
    max_rc_error_spinu_abort: float = 1e-2,
) -> Tuple[Dict[str, float], Dict[str, object]]:
    """
    Pure asset-level risk parity (equal RC_vol share). Primary: Spinu CCD on::

        0.5 x'Σx - sum_i (1/N) log(x_i)

    Fallback: SLSQP on squared RC deviation (legacy emergency path).
    Σ is PSD-repaired from the input covariance (Ledoit-Wolf upstream).
    """
    cols = [t for t in tickers if t in cov_df.columns and t in cov_df.index]
    n = len(cols)
    if n == 0:
        return {}, {"status": "FAIL_NO_ASSETS"}

    cov_raw = cov_df.reindex(index=cols, columns=cols).fillna(0.0).values
    cov, cov_psd_repaired = repair_covariance_psd(cov_raw)
    target_rc = 1.0 / float(n)

    w, spinu_diag = spinu_ccd_equal_budget(
        cov,
        eps_floor=spinu_eps_floor,
        max_iter=spinu_max_iter,
        tol=spinu_tol,
        init="inv_vol",
    )

    spinu_ok = (
        bool(spinu_diag.get("converged"))
        and np.all(np.isfinite(w))
        and abs(float(np.sum(w)) - 1.0) < 1e-8
        and float(spinu_diag.get("max_rc_error", 1.0)) <= max_rc_error_spinu_abort
        and np.all(w > 0)
    )

    fallback_used = False
    slsqp_res = None
    iterations_spinu = int(spinu_diag.get("iterations") or 0)

    if spinu_ok:
        status = "OK"
        rp_solver = "spinu_ccd"
        pc_final = _pc_from_w_static(w, cov)
        diagnostics: Dict[str, object] = {
            "status": status,
            "risk_parity_solver": rp_solver,
            "spinu_converged": bool(spinu_diag.get("converged")),
            "fallback_used": False,
            "cov_psd_repaired": cov_psd_repaired,
            "spinu_iterations": iterations_spinu,
            "spinu_max_coord_delta": spinu_diag.get("max_coord_delta"),
            "spinu_objective": spinu_diag.get("objective"),
            "iterations": iterations_spinu,
            "max_rc_error": float(np.max(np.abs(pc_final - target_rc))),
            "rc_target": target_rc,
            "rc_by_asset": {cols[i]: float(pc_final[i]) for i in range(n)},
        }
        weights = {t: float(w[i]) for i, t in enumerate(cols)}
        return weights, diagnostics

    # Emergency fallback: SLSQP
    fallback_used = True
    w_fb, slsqp_res, fb_status = _risk_parity_slsqp_fallback(cov, cols, tol=tol)
    if w_fb.size == 0:
        return {}, {
            "status": "FAIL_NUMERICAL",
            "risk_parity_solver": "slsqp_fallback_failed",
            "spinu_converged": bool(spinu_diag.get("converged")),
            "fallback_used": True,
            "cov_psd_repaired": cov_psd_repaired,
            "spinu_iterations": iterations_spinu,
            "spinu_max_rc_error": spinu_diag.get("max_rc_error"),
        }

    w = w_fb
    pc_final = _pc_from_w_static(w, cov)
    diagnostics = {
        "status": fb_status,
        "risk_parity_solver": "slsqp_fallback",
        "spinu_converged": bool(spinu_diag.get("converged")),
        "fallback_used": True,
        "cov_psd_repaired": cov_psd_repaired,
        "spinu_iterations": iterations_spinu,
        "spinu_max_coord_delta": spinu_diag.get("max_coord_delta"),
        "spinu_max_rc_error": spinu_diag.get("max_rc_error"),
        "iterations": int(slsqp_res.nit) if slsqp_res is not None and hasattr(slsqp_res, "nit") else None,
        "max_rc_error": float(np.max(np.abs(pc_final - target_rc))),
        "rc_target": target_rc,
        "rc_by_asset": {cols[i]: float(pc_final[i]) for i in range(n)},
    }
    weights = {t: float(w[i]) for i, t in enumerate(cols)}
    return weights, diagnostics


def build_risk_parity_baseline(
    cfg: PortfolioConfig,
    monthly_returns: pd.DataFrame,
    analysis_end: str,
    window_months: int,
) -> BaselineWeightsResult:
    """
    Risk-Parity Portfolio:
    - Universe: same eligible tickers as main engine.
    - Objective: equalized asset-level RC_vol as defined in metrics_specification.md.
    - Solver: Spinu cyclical coordinate descent on 0.5 x'Σx - (1/N)Σ log(x_i) with b_i=1/N,
      Σ = PSD-repaired Ledoit-Wolf monthly covariance; emergency fallback SLSQP on squared RC dispersion.
    - Constraints: long-only, fully invested. No caps.
    - If solver is unstable/infeasible, returns best feasible approximation and marks status.
    """
    eligible, coverage = _eligible_universe_from_returns(
        cfg, monthly_returns, analysis_end, window_months
    )
    diagnostics = {
        "universe_eligible": eligible,
        "universe_coverage": coverage,
    }

    if len(eligible) < 2:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_INFEASIBLE_UNIVERSE",
            diagnostics={
                **diagnostics,
                "reason": "Fewer than 2 eligible assets for Risk-Parity baseline",
            },
        )

    # Covariance on monthly simple returns, ddof=1, inner join on eligible assets.
    returns_slice = slice_window(
        monthly_returns[eligible], analysis_end, window_months
    ).dropna(how="any")
    if returns_slice.shape[0] < 2:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_DATA",
            diagnostics={
                **diagnostics,
                "reason": f"Insufficient history for covariance (rows={returns_slice.shape[0]})",
            },
        )

    # User-requested RP setting: covariance via Ledoit-Wolf shrinkage for stability.
    cov_df = cov_matrix_monthly(returns_slice, ddof=1, use_shrinkage=True)
    w_rp, diag = _risk_parity_solver(cov_df, eligible)

    # Normalize to full universe, long-only, fully invested.
    total = float(sum(max(0.0, w) for w in w_rp.values()))
    if total <= 0:
        weights = {t: 0.0 for t in cfg.tickers}
        status = "FAIL_NUMERICAL"
    else:
        weights = {t: 0.0 for t in cfg.tickers}
        for t, w in w_rp.items():
            weights[t] = max(0.0, float(w) / total)
        status = "OK" if diag.get("status") == "OK" else "APPROXIMATE"

    diagnostics.update(diag)
    return BaselineWeightsResult(
        weights=weights,
        status=status,
        diagnostics=diagnostics,
    )


def build_risk_budget_by_asset_class_baseline(
    cfg: PortfolioConfig,
    monthly_returns: pd.DataFrame,
    analysis_end: str,
    window_months: int,
    *,
    etf_universe_path: Path | None = None,
    stock_universe_path: Path | None = None,
) -> BaselineWeightsResult:
    """
    Risk budgeting on **aggregated percentage variance contributions** by taxonomy bucket.
    Solver: SLSQP. Covariance: Ledoit–Wolf monthly + PSD repair (same path as Risk Parity).
    """
    eligible, coverage = _eligible_universe_from_returns(
        cfg, monthly_returns, analysis_end, window_months
    )
    risk_cfg_raw = getattr(cfg, "risk_budgeting", None) or {}
    risk_cfg: Dict[str, Any] = dict(risk_cfg_raw) if isinstance(risk_cfg_raw, dict) else {}
    missing_mode = str(risk_cfg.get("missing_taxonomy") or "exclude").strip().lower()
    drop_empty = bool(risk_cfg.get("drop_empty_buckets", False))

    base_diag: Dict[str, object] = {
        "risk_budgeting_method": "risk_budget_by_asset_class",
        "optimizer_name": OPTIMIZER_NAME_RISK_BUDGET_BY_ASSET_CLASS,
        "solver": "SLSQP",
        "covariance_method": "ledoit_wolf_monthly",
        "universe_eligible": eligible,
        "universe_coverage": coverage,
        "taxonomy_universe_files": [TAXONOMY_ETF_REL, TAXONOMY_STOCK_REL],
    }

    if len(eligible) < 2:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_INFEASIBLE_UNIVERSE",
            diagnostics={
                **base_diag,
                "reason": "Fewer than 2 eligible assets for risk budget (class) baseline",
            },
        )

    try:
        targets_full, preset_used, manual_override, rw = resolve_class_risk_targets(risk_cfg)
    except KeyError as e:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_CONFIG",
            diagnostics={**base_diag, "reason": str(e)},
        )

    warnings: list[str] = list(rw)
    universe_rows, ticker_src = load_merged_universe_rows(
        etf_universe_path=etf_universe_path,
        stock_universe_path=stock_universe_path,
    )
    excluded_missing: list[str] = []
    tickers_kept: list[str] = []
    bucket_by: Dict[str, str] = {}
    ticker_row_src: Dict[str, str | None] = {}

    for t in eligible:
        row = universe_rows.get(t)
        if row is None:
            if missing_mode == "exclude":
                excluded_missing.append(t)
                continue
            bucket_by[t] = "unknown"
            ticker_row_src[t] = None
            tickers_kept.append(t)
            continue
        bucket = risk_budget_bucket_from_row(row)
        if bucket == "unknown" and missing_mode == "exclude":
            excluded_missing.append(t)
            continue
        bucket_by[t] = bucket
        ticker_row_src[t] = ticker_src.get(t)
        tickers_kept.append(t)

    base_diag["preset_used"] = preset_used
    base_diag["manual_override_used"] = manual_override
    base_diag["target_risk_budgets"] = dict(targets_full)
    base_diag["excluded_missing_asset_class"] = sorted(set(excluded_missing))
    base_diag["ticker_taxonomy_source"] = {k: ticker_row_src.get(k) for k in tickers_kept}

    if len(tickers_kept) < 2:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_INFEASIBLE_UNIVERSE",
            diagnostics={
                **base_diag,
                "reason": "Fewer than 2 taxonomy-classified eligible assets after exclusions",
                "warnings": warnings,
            },
        )

    present_buckets = sorted(set(bucket_by[t] for t in tickers_kept))
    unused_positive: list[str] = []
    for k, v in targets_full.items():
        if float(v) > 1e-12 and k not in present_buckets:
            unused_positive.append(k)

    targets_renormalized = False
    if unused_positive:
        if not drop_empty:
            return BaselineWeightsResult(
                weights={t: 0.0 for t in cfg.tickers},
                status="FAIL_INFEASIBLE_TARGETS",
                diagnostics={
                    **base_diag,
                    "unused_target_buckets": unused_positive,
                    "budget_buckets_used": present_buckets,
                    "reason": "Positive risk budget on bucket(s) with no eligible assets "
                    "(set risk_budgeting.drop_empty_buckets: true to renormalize)",
                    "warnings": warnings,
                },
            )
        targets_renormalized = True
        warnings.append(
            "Dropped target mass on buckets with no eligible assets: " + ", ".join(unused_positive)
        )

    raw_eff = {k: float(targets_full.get(k, 0.0)) for k in present_buckets}
    mass = float(sum(raw_eff.values()))
    if mass <= 1e-15:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_INFEASIBLE_TARGETS",
            diagnostics={
                **base_diag,
                "reason": "Effective target risk budgets sum to zero on present buckets",
                "budget_buckets_used": present_buckets,
                "warnings": warnings,
            },
        )
    b_active = np.array([raw_eff[k] / mass for k in present_buckets], dtype=float)
    bucket_to_idx = {b: i for i, b in enumerate(present_buckets)}
    bi = np.array([bucket_to_idx[bucket_by[t]] for t in tickers_kept], dtype=int)

    returns_slice = slice_window(
        monthly_returns[tickers_kept], analysis_end, window_months
    ).dropna(how="any")
    if returns_slice.shape[0] < 2:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_DATA",
            diagnostics={
                **base_diag,
                "reason": f"Insufficient history for covariance (rows={returns_slice.shape[0]})",
                "warnings": warnings,
            },
        )

    cov_df = cov_matrix_monthly(returns_slice, ddof=1, use_shrinkage=True)
    cov_raw = cov_df.reindex(index=tickers_kept, columns=tickers_kept).fillna(0.0).values
    cov_rep, cov_psd_repaired = repair_covariance_psd(cov_raw)
    base_diag["cov_psd_repaired"] = cov_psd_repaired

    w_vec, sdiag = solve_class_risk_budget_slsqp(cov_rep, bi, b_active)
    w_vec = np.maximum(w_vec, 0.0)
    s = float(np.sum(w_vec))
    w_vec = w_vec / s if s > 1e-15 else np.full(len(tickers_kept), 1.0 / len(tickers_kept))

    realized_list = sdiag.get("realized_class_risk") or []
    realized_map = {present_buckets[i]: float(realized_list[i]) for i in range(len(present_buckets))}
    tickers_per_bucket: Dict[str, list[str]] = {}
    for t in tickers_kept:
        tickers_per_bucket.setdefault(bucket_by[t], []).append(t)
    for k in tickers_per_bucket:
        tickers_per_bucket[k] = sorted(tickers_per_bucket[k])

    weights = {t: 0.0 for t in cfg.tickers}
    for i, t in enumerate(tickers_kept):
        weights[t] = float(w_vec[i])

    port_var_m = float(w_vec @ cov_rep @ w_vec)
    ann_vol = float(np.sqrt(max(port_var_m, 0.0)) * np.sqrt(12))

    diag_out: Dict[str, object] = {
        **base_diag,
        **sdiag,
        "target_risk_budgets_effective": {k: float(b_active[i]) for i, k in enumerate(present_buckets)},
        "realized_risk_contributions": realized_map,
        "budget_buckets_used": present_buckets,
        "tickers_per_bucket": tickers_per_bucket,
        "asset_classes_used": present_buckets,
        "tickers_per_class": tickers_per_bucket,
        "targets_renormalized": targets_renormalized,
        "unused_target_buckets": unused_positive if unused_positive else [],
        "warnings": warnings,
        "eligible_universe": tickers_kept,
        "final_weights": {t: weights[t] for t in tickers_kept},
        "portfolio_variance": port_var_m,
        "annualized_volatility": ann_vol,
    }
    st = str(sdiag.get("solver_status") or "OK")
    status = "OK" if st == "OK" else "APPROXIMATE"
    return BaselineWeightsResult(weights=weights, status=status, diagnostics=diag_out)


def build_risk_budget_by_asset_baseline(
    cfg: PortfolioConfig,
    monthly_returns: pd.DataFrame,
    analysis_end: str,
    window_months: int,
) -> BaselineWeightsResult:
    """Per-asset risk budgets via Spinu CCD (fallback SLSQP)."""
    eligible, coverage = _eligible_universe_from_returns(
        cfg, monthly_returns, analysis_end, window_months
    )
    risk_cfg_raw = getattr(cfg, "risk_budgeting", None) or {}
    risk_cfg: Dict[str, Any] = dict(risk_cfg_raw) if isinstance(risk_cfg_raw, dict) else {}

    base_diag: Dict[str, object] = {
        "risk_budgeting_method": "risk_budget_by_asset",
        "optimizer_name": OPTIMIZER_NAME_RISK_BUDGET_BY_ASSET,
        "covariance_method": "ledoit_wolf_monthly",
        "universe_eligible": eligible,
        "universe_coverage": coverage,
        "preset_used": str(risk_cfg.get("preset") or "balanced"),
        "taxonomy_universe_files": [TAXONOMY_ETF_REL, TAXONOMY_STOCK_REL],
    }

    at = risk_cfg.get("asset_targets") or {}
    if not isinstance(at, dict) or len(at) == 0:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_CONFIG",
            diagnostics={
                **base_diag,
                "reason": "risk_budgeting.asset_targets is required and must be non-empty "
                "for per-asset risk budgeting",
                "manual_override_used": False,
            },
        )

    elig_set = set(eligible)
    filt: Dict[str, float] = {}
    for k, v in at.items():
        t = str(k).strip()
        if t in elig_set:
            filt[t] = float(v)
    missing_elig = elig_set - set(filt.keys())
    if missing_elig:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_CONFIG",
            diagnostics={
                **base_diag,
                "reason": "asset_targets must include every eligible ticker with positive budget",
                "missing_eligible_assets_for_targets": sorted(missing_elig),
                "manual_override_used": True,
            },
        )

    extra = set(filt.keys()) - elig_set
    if extra:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_CONFIG",
            diagnostics={
                **base_diag,
                "reason": "asset_targets contains tickers not in eligible universe",
                "extra_keys": sorted(extra),
                "manual_override_used": True,
            },
        )

    try:
        b_map, _ = normalize_budget_map(filt, allowed_keys=None)
    except ValueError as e:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_CONFIG",
            diagnostics={**base_diag, "reason": str(e), "manual_override_used": True},
        )

    tickers_kept = sorted(elig_set)
    b_vec = np.array([b_map[t] for t in tickers_kept], dtype=float)

    base_diag["manual_override_used"] = True
    base_diag["target_risk_budgets"] = dict(b_map)

    if len(tickers_kept) < 2:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_INFEASIBLE_UNIVERSE",
            diagnostics={**base_diag, "reason": "Fewer than 2 eligible assets"},
        )

    returns_slice = slice_window(
        monthly_returns[tickers_kept], analysis_end, window_months
    ).dropna(how="any")
    if returns_slice.shape[0] < 2:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_DATA",
            diagnostics={
                **base_diag,
                "reason": f"Insufficient history for covariance (rows={returns_slice.shape[0]})",
            },
        )

    cov_df = cov_matrix_monthly(returns_slice, ddof=1, use_shrinkage=True)
    cov_raw = cov_df.reindex(index=tickers_kept, columns=tickers_kept).fillna(0.0).values
    cov_rep, cov_psd_repaired = repair_covariance_psd(cov_raw)
    base_diag["cov_psd_repaired"] = cov_psd_repaired

    w_vec, adiag = solve_asset_risk_budget_spinu(cov_rep, b_vec)
    weights = {t: 0.0 for t in cfg.tickers}
    for i, t in enumerate(tickers_kept):
        weights[t] = float(w_vec[i])

    pc = pc_from_w(w_vec, cov_rep)
    realized_assets = {tickers_kept[i]: float(pc[i]) for i in range(len(tickers_kept))}
    port_var_m = float(w_vec @ cov_rep @ w_vec)
    ann_vol = float(np.sqrt(max(port_var_m, 0.0)) * np.sqrt(12))

    diag_out: Dict[str, object] = {
        **base_diag,
        **adiag,
        "realized_risk_contributions": realized_assets,
        "rc_by_asset": realized_assets,
        "risk_budget_tracking_error": adiag.get("risk_budget_tracking_error"),
        "max_budget_deviation": adiag.get("max_budget_deviation"),
        "eligible_universe": tickers_kept,
        "final_weights": {t: weights[t] for t in tickers_kept},
        "portfolio_variance": port_var_m,
        "annualized_volatility": ann_vol,
        "excluded_missing_asset_class": [],
        "solver_status": "OK"
        if (adiag.get("solver") == "spinu_ccd" and not adiag.get("fallback_used"))
        else ("OK" if adiag.get("solver_success") else "APPROXIMATE"),
        "solver_success": bool(
            (adiag.get("solver") == "spinu_ccd" and not adiag.get("fallback_used"))
            or adiag.get("solver_success")
        ),
    }
    st = str(diag_out.get("solver_status"))
    status = "OK" if st == "OK" else "APPROXIMATE"
    return BaselineWeightsResult(weights=weights, status=status, diagnostics=diag_out)


def _budget_simplex_intersects_box(bounds: list[tuple[float, float]]) -> bool:
    s_lo = float(sum(b[0] for b in bounds))
    s_hi = float(sum(b[1] for b in bounds))
    return s_lo <= 1.0 + 1e-9 and s_hi >= 1.0 - 1e-9


def _mv_covariance_for_eligible(
    cfg: PortfolioConfig,
    monthly_returns: pd.DataFrame,
    analysis_end: str,
    window_months: int,
    eligible: list[str],
    *,
    force_shrinkage: bool | None = None,
) -> tuple[
    np.ndarray,
    list[str],
    str,
    bool,
    bool,
    str | None,
    dict[str, float] | None,
    dict[str, Any] | None,
] | None:
    """
    Shared monthly Σ for Minimum-Variance variants (eligible inner join, dual cov optional).

    Returns
    -------
    (cov_psd, cols, covariance_method, shrinkage_used, psd_repair_applied,
    young_etf_dual_mode, per_ticker_young_caps, young_etf_diagnostics)
    or None if fewer than two return rows after dropna.

    ``per_ticker_young_caps`` is ``None`` when dual covariance is disabled or no caps apply.
    """
    returns_slice = slice_window(
        monthly_returns[eligible], analysis_end, window_months
    ).dropna(how="any")
    if returns_slice.shape[0] < 2:
        return None
    cols = [str(c) for c in returns_slice.columns]
    young_pol = getattr(cfg, "young_etf_optimization_policy", None) or {}
    dual_enabled = bool(young_pol.get("enabled", True))
    if force_shrinkage is None:
        use_shrinkage = bool(getattr(cfg, "covariance_shrinkage", False))
    else:
        use_shrinkage = bool(force_shrinkage)
    young_mode: str | None = None
    per_ticker_caps: dict[str, float] | None = None
    young_diagnostics: dict[str, Any] | None = None
    if dual_enabled:
        cov_df, _mu, ydiag = build_dual_covariance_and_mu(
            monthly_returns,
            cols,
            window_months,
            young_pol,
            use_shrinkage_on_core=use_shrinkage,
            analysis_end=pd.Timestamp(analysis_end),
        )
        young_diagnostics = ydiag
        cols = [str(c) for c in cov_df.columns]
        covariance_method = f"young_etf_dual:{ydiag.get('mode', '')}"
        m = ydiag.get("mode")
        young_mode = str(m) if m is not None else None
        per_ticker_caps = per_ticker_young_weight_caps(
            ydiag["tickers"],
            float(young_pol.get("max_weight_candidate_or_new_pct", 0.02)),
        )
        if not per_ticker_caps:
            per_ticker_caps = None
    else:
        cov_df = cov_matrix_monthly(returns_slice[cols], ddof=1, use_shrinkage=use_shrinkage)
        covariance_method = "ledoit_wolf_monthly" if use_shrinkage else "sample_monthly_ddof1"
    cov_np_raw = cov_df.reindex(index=cols, columns=cols).fillna(0.0).values
    cov_np, psd_repaired = repair_covariance_psd(cov_np_raw)
    return (
        cov_np,
        cols,
        covariance_method,
        use_shrinkage,
        bool(psd_repaired),
        young_mode,
        per_ticker_caps,
        young_diagnostics,
    )


MV_UNCAPPED_CONSTRAINTS_USED = ("long_only", "no_short", "fully_invested")
MV_UNCAPPED_CONSTRAINTS_NOT_USED = (
    "min_weight",
    "max_weight",
    "basket_caps",
    "young_etf_caps",
    "turnover_penalty",
    "volatility_target",
    "tracking_error",
    "factor_exposure",
)


def _minimum_variance_w_only_vol_cap_slsqp(
    cov: np.ndarray,
    bounds: list[tuple[float, float]],
    v_max_monthly: float,
    *,
    maxiter: int = 2000,
) -> tuple[np.ndarray, Any, bool]:
    """Minimize 0.5 w'Σw subject to sum w = 1, box bounds, and w'Σw <= v_max_monthly."""
    n = len(bounds)
    lo = np.array([float(b[0]) for b in bounds], dtype=float)
    hi = np.array([float(b[1]) for b in bounds], dtype=float)
    w0, _r0, _fb = _minimum_variance_slsqp(cov, bounds, maxiter=maxiter)
    x0 = np.clip(w0, lo, hi)
    if float(x0.sum()) > 1e-12:
        x0 = x0 / float(x0.sum())

    def objective(w_vec: np.ndarray) -> float:
        return 0.5 * float(w_vec @ cov @ w_vec)

    def grad_obj(w_vec: np.ndarray) -> np.ndarray:
        return cov @ w_vec

    def vol_ineq(w_vec: np.ndarray) -> float:
        return float(v_max_monthly - float(w_vec @ cov @ w_vec))

    def vol_ineq_jac(w_vec: np.ndarray) -> np.ndarray:
        return -2.0 * (cov @ w_vec)

    cons = [
        {"type": "eq", "fun": lambda w: float(np.sum(w) - 1.0), "jac": lambda w: np.ones(n)},
        {"type": "ineq", "fun": vol_ineq, "jac": vol_ineq_jac},
    ]
    res = minimize(
        objective,
        x0,
        method="SLSQP",
        jac=grad_obj,
        bounds=list(zip(lo, hi)),
        constraints=cons,
        options={"maxiter": maxiter, "ftol": 1e-9},
    )
    fallback_used = False
    if not getattr(res, "success", False) or not np.all(np.isfinite(res.x)):
        res = minimize(
            objective,
            x0,
            method="SLSQP",
            jac=grad_obj,
            bounds=list(zip(lo, hi)),
            constraints=cons,
            options={"maxiter": maxiter, "ftol": 1e-11},
        )
    w_out = np.asarray(res.x, dtype=float)
    if not getattr(res, "success", False) or not np.all(np.isfinite(w_out)):
        w_out, res, fallback_used = _minimum_variance_slsqp(cov, bounds, maxiter=maxiter)
        return w_out, res, True
    return w_out, res, fallback_used


def _minimum_variance_l1_extended_slsqp(
    cov: np.ndarray,
    bounds_w: list[tuple[float, float]],
    w_ref: np.ndarray,
    *,
    lambda_turnover: float,
    v_max_monthly: float | None,
    maxiter: int = 3000,
) -> tuple[np.ndarray, Any, bool]:
    """
    Minimize 0.5 w'Σw + λ Σ t_i subject to Σw=1, box w, t_i >= |w_i - w_ref_i|, t_i>=0,
    and optionally w'Σw <= v_max_monthly. Vector x = [w; t], dim 2n.
    """
    n = len(bounds_w)
    lo_w = np.array([float(b[0]) for b in bounds_w], dtype=float)
    hi_w = np.array([float(b[1]) for b in bounds_w], dtype=float)
    lam = float(lambda_turnover)
    w0, _, _ = _minimum_variance_slsqp(cov, bounds_w, maxiter=maxiter)
    w0 = np.clip(w0, lo_w, hi_w)
    if float(w0.sum()) > 1e-12:
        w0 = w0 / float(w0.sum())
    t0 = np.abs(w0 - w_ref) + 1e-8
    x0 = np.concatenate([w0, t0])
    bounds_xt = list(zip(lo_w, hi_w)) + [(0.0, 3.0)] * n

    def objective(x: np.ndarray) -> float:
        w = x[:n]
        t = x[n:]
        return 0.5 * float(w @ cov @ w) + lam * float(np.sum(t))

    def grad_obj(x: np.ndarray) -> np.ndarray:
        w = x[:n]
        g = np.zeros(2 * n, dtype=float)
        g[:n] = cov @ w
        g[n:] = lam
        return g

    def eq_fun(x: np.ndarray) -> float:
        return float(np.sum(x[:n]) - 1.0)

    def eq_jac(x: np.ndarray) -> np.ndarray:
        j = np.zeros(2 * n, dtype=float)
        j[:n] = 1.0
        return j

    n_ineq = 2 * n + (1 if v_max_monthly is not None else 0)

    def ineq_fun(x: np.ndarray) -> np.ndarray:
        w = x[:n]
        t = x[n:]
        out = np.empty(n_ineq, dtype=float)
        row = 0
        for i in range(n):
            out[row] = float(t[i] - w[i] + w_ref[i])
            row += 1
            out[row] = float(t[i] + w[i] - w_ref[i])
            row += 1
        if v_max_monthly is not None:
            out[row] = float(v_max_monthly - float(w @ cov @ w))
        return out

    def ineq_jac(x: np.ndarray) -> np.ndarray:
        w = x[:n]
        J = np.zeros((n_ineq, 2 * n), dtype=float)
        row = 0
        for i in range(n):
            J[row, i] = -1.0
            J[row, n + i] = 1.0
            row += 1
            J[row, i] = 1.0
            J[row, n + i] = 1.0
            row += 1
        if v_max_monthly is not None:
            J[row, :n] = -2.0 * (cov @ w)
        return J

    cons = (
        {"type": "eq", "fun": eq_fun, "jac": eq_jac},
        {"type": "ineq", "fun": ineq_fun, "jac": ineq_jac},
    )
    res = minimize(
        objective,
        x0,
        method="SLSQP",
        jac=grad_obj,
        bounds=bounds_xt,
        constraints=cons,
        options={"maxiter": maxiter, "ftol": 1e-9},
    )
    fallback_used = False
    if not getattr(res, "success", False) or not np.all(np.isfinite(res.x)):
        res = minimize(
            objective,
            x0,
            method="SLSQP",
            jac=grad_obj,
            bounds=bounds_xt,
            constraints=cons,
            options={"maxiter": maxiter, "ftol": 1e-11},
        )
    x_out = np.asarray(res.x, dtype=float) if getattr(res, "x", None) is not None else None
    if x_out is None or not np.all(np.isfinite(x_out)) or not getattr(res, "success", False):
        # fall back to vol-only or plain MV inside caller; signal failure
        return np.full(n, np.nan), res, True
    return x_out[:n].copy(), res, fallback_used


def _finalize_mv_weights(
    w_vec: np.ndarray,
    cols: list[str],
    cfg: PortfolioConfig,
    cov_np: np.ndarray,
    bounds: list[tuple[float, float]],
    res: Any,
    fallback_used: bool,
    *,
    diagnostics: Dict[str, object],
) -> BaselineWeightsResult:
    """Clip, renormalize, pack full-ticker weights, common diagnostics."""
    if (not np.all(np.isfinite(w_vec))) or w_vec.shape[0] != len(cols):
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_NUMERICAL",
            diagnostics={
                **diagnostics,
                "reason": "Minimum-variance solver returned non-finite weights",
                "fallback_used": bool(fallback_used),
                "solver_success": bool(getattr(res, "success", False)),
                "solver_message": str(getattr(res, "message", "")),
            },
        )
    lo_arr = np.array([b[0] for b in bounds], dtype=float)
    hi_arr = np.array([b[1] for b in bounds], dtype=float)
    w_vec = np.clip(w_vec, lo_arr, hi_arr)
    ssum = float(w_vec.sum())
    if ssum > 1e-12:
        w_vec = w_vec / ssum
    else:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_NUMERICAL",
            diagnostics={**diagnostics, "reason": "Normalized weights sum to ~0"},
        )

    var_p = float(w_vec @ cov_np @ w_vec)
    ann_vol = float(np.sqrt(max(var_p, 0.0) * 12.0))
    weights: Dict[str, float] = {t: 0.0 for t in cfg.tickers}
    for i, t in enumerate(cols):
        weights[t] = float(w_vec[i])
    w_nonzero = {t: float(weights[t]) for t in cols if weights[t] > 1e-14}
    diagnostics.update(
        {
            "eligible_universe": list(cols),
            "final_weights": dict(sorted(w_nonzero.items(), key=lambda x: (-x[1], x[0]))),
            "portfolio_variance": var_p,
            "annualized_volatility": ann_vol,
            "solver_status": getattr(res, "status", None),
            "solver_success": bool(getattr(res, "success", False)),
            "solver_message": str(getattr(res, "message", "")),
            "max_weight": float(np.max(w_vec)) if len(w_vec) else 0.0,
            "min_weight": float(np.min(w_vec)) if len(w_vec) else 0.0,
            "fallback_used": bool(fallback_used),
        }
    )
    tol_sum = 1e-5
    tol_b = 1e-5
    sum_ok = abs(float(np.sum(w_vec)) - 1.0) < tol_sum
    in_bounds = bool(np.all(w_vec >= lo_arr - tol_b) and np.all(w_vec <= hi_arr + tol_b))
    solver_ok = bool(getattr(res, "success", False)) and not fallback_used
    if solver_ok and sum_ok and in_bounds:
        status = "OK"
    elif sum_ok and in_bounds and var_p == var_p:
        status = "APPROXIMATE"
    else:
        status = "FAIL_NUMERICAL"
    return BaselineWeightsResult(weights=weights, status=status, diagnostics=diagnostics)


def _finalize_md_weights(
    w_vec: np.ndarray,
    cols: list[str],
    cfg: PortfolioConfig,
    cov_np: np.ndarray,
    bounds: list[tuple[float, float]],
    res: Any,
    fallback_used: bool,
    *,
    diagnostics: Dict[str, object],
) -> BaselineWeightsResult:
    """Clip, renormalize, pack weights; diversification ratio from final monthly Sigma."""
    if (not np.all(np.isfinite(w_vec))) or w_vec.shape[0] != len(cols):
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_NUMERICAL",
            diagnostics={
                **diagnostics,
                "reason": "Maximum-diversification solver returned non-finite weights",
                "fallback_used": bool(fallback_used),
                "solver_success": bool(getattr(res, "success", False)),
                "solver_message": str(getattr(res, "message", "")),
            },
        )
    lo_arr = np.array([b[0] for b in bounds], dtype=float)
    hi_arr = np.array([b[1] for b in bounds], dtype=float)
    w_vec = np.clip(w_vec, lo_arr, hi_arr)
    ssum = float(w_vec.sum())
    if ssum > 1e-12:
        w_vec = w_vec / ssum
    else:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_NUMERICAL",
            diagnostics={**diagnostics, "reason": "Normalized weights sum to ~0"},
        )

    cov_a = np.asarray(cov_np, dtype=float)
    sigma = np.sqrt(np.maximum(np.diag(cov_a), 0.0))
    wag_m = float(sigma @ w_vec)
    var_p = float(w_vec @ cov_a @ w_vec)
    den_m = np.sqrt(max(var_p, 0.0))
    dr_val = wag_m / den_m if den_m > 1e-30 else float("nan")
    ann_vol = float(np.sqrt(max(var_p, 0.0) * 12.0))
    weights: Dict[str, float] = {t: 0.0 for t in cfg.tickers}
    for i, t in enumerate(cols):
        weights[t] = float(w_vec[i])
    w_nonzero = {t: float(weights[t]) for t in cols if weights[t] > 1e-14}
    diagnostics.update(
        {
            "eligible_universe": list(cols),
            "final_weights": dict(sorted(w_nonzero.items(), key=lambda x: (-x[1], x[0]))),
            "portfolio_variance": var_p,
            "annualized_volatility": ann_vol,
            "diversification_ratio": float(dr_val),
            "weighted_avg_asset_vol_monthly": float(wag_m),
            "solver_status": getattr(res, "status", None),
            "solver_success": bool(getattr(res, "success", False)),
            "solver_message": str(getattr(res, "message", "")),
            "max_weight": float(np.max(w_vec)) if len(w_vec) else 0.0,
            "min_weight": float(np.min(w_vec)) if len(w_vec) else 0.0,
            "fallback_used": bool(fallback_used),
        }
    )
    tol_sum = 1e-5
    tol_b = 1e-5
    sum_ok = abs(float(np.sum(w_vec)) - 1.0) < tol_sum
    in_bounds = bool(np.all(w_vec >= lo_arr - tol_b) and np.all(w_vec <= hi_arr + tol_b))
    solver_ok = bool(getattr(res, "success", False)) and not fallback_used
    if solver_ok and sum_ok and in_bounds:
        status = "OK"
    elif sum_ok and in_bounds and var_p == var_p:
        status = "APPROXIMATE"
    else:
        status = "FAIL_NUMERICAL"
    return BaselineWeightsResult(weights=weights, status=status, diagnostics=diagnostics)


def _minimum_variance_slsqp(
    cov: np.ndarray,
    bounds: list[tuple[float, float]],
    *,
    maxiter: int = 2000,
) -> tuple[np.ndarray, Any, bool]:
    """
    Constrained minimum-variance via SLSQP on 0.5 w'Σw with jac Σw, sum(w)=1, box bounds.

    Returns
    -------
    weights :
        Length-N dense weight vector aligned to ``bounds``.
    result :
        ``scipy.optimize.OptimizeResult`` or a minimal namespace for clip fallback.
    fallback_used :
        True if a normalized boundary clip fallback replaced a failed SLSQP run.
    """
    n = len(bounds)
    lo = np.array([float(b[0]) for b in bounds], dtype=float)
    hi = np.array([float(b[1]) for b in bounds], dtype=float)
    diag = np.diag(np.asarray(cov, dtype=float))
    inv_vol = np.zeros(n, dtype=float)
    for i in range(n):
        v = float(diag[i])
        if v > 1e-18:
            inv_vol[i] = 1.0 / float(np.sqrt(v))
    if float(np.sum(inv_vol)) < 1e-12:
        x0 = np.ones(n, dtype=float) / float(n)
    else:
        x0 = inv_vol / float(np.sum(inv_vol))
    x0 = np.clip(x0, lo, hi)
    sw = float(x0.sum())
    if sw > 1e-12:
        x0 = x0 / sw
    else:
        mid = 0.5 * (lo + hi)
        s_mid = float(np.sum(mid))
        x0 = mid / s_mid if s_mid > 1e-12 else np.ones(n, dtype=float) / float(n)

    def penalty_feas(w_vec: np.ndarray) -> float:
        s = float(np.sum(w_vec) - 1.0)
        return s * s

    feas = minimize(
        penalty_feas,
        x0,
        method="L-BFGS-B",
        bounds=list(zip(lo, hi)),
        options={"maxiter": 400},
    )
    x_start = np.asarray(feas.x, dtype=float).copy()
    if not np.all(np.isfinite(x_start)):
        x_start = np.clip(x0, lo, hi)

    def objective(w_vec: np.ndarray) -> float:
        return 0.5 * float(w_vec @ cov @ w_vec)

    def grad_obj(w_vec: np.ndarray) -> np.ndarray:
        return cov @ w_vec

    cons = [{"type": "eq", "fun": lambda w_vec: float(np.sum(w_vec) - 1.0)}]
    scipy_bounds = list(zip(lo, hi))

    res = minimize(
        objective,
        x_start,
        method="SLSQP",
        jac=grad_obj,
        bounds=scipy_bounds,
        constraints=cons,
        options={"maxiter": maxiter, "ftol": 1e-9},
    )
    fallback_used = False
    if not getattr(res, "success", False) or not np.all(np.isfinite(res.x)):
        res = minimize(
            objective,
            x_start,
            method="SLSQP",
            jac=grad_obj,
            bounds=scipy_bounds,
            constraints=cons,
            options={"maxiter": maxiter, "ftol": 1e-12},
        )

    x_out = np.asarray(res.x, dtype=float) if getattr(res, "x", None) is not None else None
    if (
        not getattr(res, "success", False)
        or x_out is None
        or not np.all(np.isfinite(x_out))
    ):
        fx = getattr(feas, "x", None)
        if fx is not None and np.all(np.isfinite(fx)):
            w_fb = np.clip(np.asarray(fx, dtype=float), lo, hi)
        elif getattr(res, "x", None) is not None:
            w_fb = np.clip(np.asarray(res.x, dtype=float), lo, hi)
        else:
            w_fb = None

        if w_fb is None:
            res = SimpleNamespace(
                success=False,
                x=np.full(n, np.nan),
                status=getattr(res, "status", None),
                message="SLSQP failed and no feasible fallback available",
                nit=getattr(res, "nit", None),
            )
        else:
            s = float(w_fb.sum())
            if s > 1e-12:
                w_fb = w_fb / s
                res = SimpleNamespace(
                    success=True,
                    x=w_fb,
                    status=getattr(res, "status", None),
                    message="Normalized feasible point after SLSQP non-convergence",
                    nit=getattr(res, "nit", None),
                )
                fallback_used = True
            else:
                res = SimpleNamespace(
                    success=False,
                    x=np.full(n, np.nan),
                    status=getattr(res, "status", None),
                    message="Fallback normalization failed",
                    nit=getattr(res, "nit", None),
                )

    w_final = np.asarray(res.x, dtype=float)
    return w_final, res, fallback_used


def _maximum_diversification_dr_value_grad(
    w_vec: np.ndarray, cov: np.ndarray, sigma: np.ndarray
) -> tuple[float, np.ndarray]:
    """Return (DR, gradient of DR) for DR = (sigma' w) / sqrt(w' Sigma w)."""
    w_vec = np.asarray(w_vec, dtype=float)
    cov = np.asarray(cov, dtype=float)
    sigma = np.asarray(sigma, dtype=float)
    var_v = float(w_vec @ cov @ w_vec)
    den = float(np.sqrt(max(var_v, 1e-30)))
    num = float(sigma @ w_vec)
    dr = num / den
    gw = sigma / den - (cov @ w_vec) * (num / (den**3))
    return float(dr), np.asarray(gw, dtype=float)


def _maximum_diversification_slsqp(
    cov: np.ndarray,
    bounds: list[tuple[float, float]],
    *,
    maxiter: int = 2000,
) -> tuple[np.ndarray, Any, bool]:
    """
    Constrained maximum diversification via SLSQP on ``-DR`` with analytic Jacobian.

    Uses the same feasible start heuristic as Minimum Variance (inverse-vol in the box).
    """
    n = len(bounds)
    cov_np = np.asarray(cov, dtype=float)
    sigma = np.sqrt(np.maximum(np.diag(cov_np), 0.0)).astype(float)
    lo = np.array([float(b[0]) for b in bounds], dtype=float)
    hi = np.array([float(b[1]) for b in bounds], dtype=float)
    inv_vol = np.zeros(n, dtype=float)
    for i in range(n):
        v = float(sigma[i])
        if v > 1e-18:
            inv_vol[i] = 1.0 / v
    if float(np.sum(inv_vol)) < 1e-12:
        x0 = np.ones(n, dtype=float) / float(n)
    else:
        x0 = inv_vol / float(np.sum(inv_vol))
    x0 = np.clip(x0, lo, hi)
    sw = float(x0.sum())
    if sw > 1e-12:
        x0 = x0 / sw
    else:
        mid = 0.5 * (lo + hi)
        s_mid = float(np.sum(mid))
        x0 = mid / s_mid if s_mid > 1e-12 else np.ones(n, dtype=float) / float(n)

    def penalty_feas(w_v: np.ndarray) -> float:
        s = float(np.sum(w_v) - 1.0)
        return s * s

    feas = minimize(
        penalty_feas,
        x0,
        method="L-BFGS-B",
        bounds=list(zip(lo, hi)),
        options={"maxiter": 400},
    )
    x_start = np.asarray(feas.x, dtype=float).copy()
    if not np.all(np.isfinite(x_start)):
        x_start = np.clip(x0, lo, hi)

    def objective(w_v: np.ndarray) -> float:
        dr_val, _g = _maximum_diversification_dr_value_grad(w_v, cov_np, sigma)
        return -float(dr_val)

    def grad_obj(w_v: np.ndarray) -> np.ndarray:
        _dr_val, g = _maximum_diversification_dr_value_grad(w_v, cov_np, sigma)
        return -g

    cons = [{"type": "eq", "fun": lambda w_v: float(np.sum(w_v) - 1.0)}]
    scipy_bounds = list(zip(lo, hi))

    res = minimize(
        objective,
        x_start,
        method="SLSQP",
        jac=grad_obj,
        bounds=scipy_bounds,
        constraints=cons,
        options={"maxiter": maxiter, "ftol": 1e-9},
    )
    fallback_used = False
    if not getattr(res, "success", False) or not np.all(np.isfinite(res.x)):
        res = minimize(
            objective,
            x_start,
            method="SLSQP",
            jac=grad_obj,
            bounds=scipy_bounds,
            constraints=cons,
            options={"maxiter": maxiter, "ftol": 1e-12},
        )
    if not getattr(res, "success", False) or not np.all(np.isfinite(res.x)):
        res = minimize(
            objective,
            x_start,
            method="SLSQP",
            bounds=scipy_bounds,
            constraints=cons,
            options={"maxiter": maxiter, "ftol": 1e-9},
        )

    x_out = np.asarray(res.x, dtype=float) if getattr(res, "x", None) is not None else None
    if not getattr(res, "success", False) or x_out is None or not np.all(np.isfinite(x_out)):
        fx = getattr(feas, "x", None)
        if fx is not None and np.all(np.isfinite(fx)):
            w_fb = np.clip(np.asarray(fx, dtype=float), lo, hi)
        elif getattr(res, "x", None) is not None:
            w_fb = np.clip(np.asarray(res.x, dtype=float), lo, hi)
        else:
            w_fb = None

        if w_fb is None:
            res = SimpleNamespace(
                success=False,
                x=np.full(n, np.nan),
                status=getattr(res, "status", None),
                message="SLSQP failed and no feasible fallback available",
                nit=getattr(res, "nit", None),
            )
        else:
            s_fb = float(w_fb.sum())
            if s_fb > 1e-12:
                w_fb = w_fb / s_fb
                res = SimpleNamespace(
                    success=True,
                    x=w_fb,
                    status=getattr(res, "status", None),
                    message="Normalized feasible point after SLSQP non-convergence",
                    nit=getattr(res, "nit", None),
                )
                fallback_used = True
            else:
                res = SimpleNamespace(
                    success=False,
                    x=np.full(n, np.nan),
                    status=getattr(res, "status", None),
                    message="Fallback normalization failed",
                    nit=getattr(res, "nit", None),
                )

    w_final = np.asarray(res.x, dtype=float)
    return w_final, res, fallback_used


def build_minimum_variance_constrained(
    cfg: PortfolioConfig,
    monthly_returns: pd.DataFrame,
    analysis_end: str,
    window_months: int,
) -> BaselineWeightsResult:
    """
    **minimum_variance_constrained**: same long-only box bounds as :func:`src.optimization._build_bounds`
    (feasibility cap, config min/max, Young-ETF per-ticker caps when dual covariance is enabled).
    """
    eligible, coverage = _eligible_universe_from_returns(
        cfg, monthly_returns, analysis_end, window_months
    )
    diagnostics: Dict[str, object] = {
        "universe_eligible": eligible,
        "universe_coverage": coverage,
        "optimizer_name": OPTIMIZER_NAME_MINIMUM_VARIANCE_CONSTRAINED,
        "solver": MINIMUM_VARIANCE_SOLVER,
        "objective": MINIMUM_VARIANCE_OBJECTIVE,
        "analysis_end": str(analysis_end),
        "window_months": int(window_months),
        "minimum_variance_baseline_role": MV_BASELINE_ROLE_PRIMARY_LOWEST_VOL_UNDER_CONSTRAINTS,
        "minimum_variance_interpretation": (
            "Primary baseline for the lowest portfolio volatility achievable under the project's "
            "optimizer-equivalent long-only box bounds (feasibility cap, config min/max per name, "
            "Young-ETF per-ticker caps when dual covariance is enabled). "
            "This is the canonical answer to: lowest volatility under these constraints."
        ),
        "active_constraints": [
            "equality: sum(weights) = 1",
            "box: per-asset bounds from feasibility cap and config (min_single / max_single / young caps)",
        ],
    }

    if len(eligible) < 2:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_INFEASIBLE_UNIVERSE",
            diagnostics={
                **diagnostics,
                "reason": "Fewer than 2 eligible assets for Minimum-Variance (constrained)",
            },
        )

    cov_pack = _mv_covariance_for_eligible(
        cfg, monthly_returns, analysis_end, window_months, eligible
    )
    if cov_pack is None:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_DATA",
            diagnostics={
                **diagnostics,
                "reason": "Insufficient history for covariance after inner join",
            },
        )
    (
        cov_np,
        cols,
        covariance_method,
        shrinkage_used,
        psd_repaired,
        young_mode,
        per_ticker_caps,
        young_diagnostics,
    ) = cov_pack
    diagnostics["covariance_method"] = covariance_method
    diagnostics["shrinkage_used"] = bool(shrinkage_used)
    diagnostics["psd_repair_used"] = bool(psd_repaired)
    _attach_young_etf_methodology_diagnostics(
        diagnostics,
        cfg,
        young_mode=young_mode,
        young_diagnostics=young_diagnostics,
        per_ticker_caps=per_ticker_caps,
        role="covariance_and_per_ticker_caps",
    )
    _attach_optimizer_input_fingerprints(
        diagnostics, cfg, monthly_returns, analysis_end, window_months, cols
    )

    min_w = (
        float(cfg.min_single_security_weight_pct)
        if cfg.min_single_security_weight_pct is not None
        and float(cfg.min_single_security_weight_pct) > 0
        else float(MIN_WEIGHT_DEFAULT)
    )
    bounds = _build_bounds(
        cols,
        len(cols),
        min_w,
        cfg.max_single_security_weight_pct,
        per_ticker_caps,
    )
    diagnostics["bounds_used"] = _bounds_export(bounds, cols)
    diagnostics["constraint_summary"] = {
        "sum_weights": "equality_1",
        "box_source": "_build_bounds",
        "young_caps_applied": isinstance(per_ticker_caps, dict) and len(per_ticker_caps) > 0,
    }

    if not _budget_simplex_intersects_box(bounds):
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_INFEASIBLE_BOUNDS",
            diagnostics={
                **diagnostics,
                "reason": (
                    "Weight bounds infeasible for a fully invested portfolio "
                    "(sum of lower bounds > 1 or sum of upper bounds < 1)"
                ),
                "bounds_detail": {
                    cols[i]: {"min": float(bounds[i][0]), "max": float(bounds[i][1])}
                    for i in range(len(cols))
                },
            },
        )

    w_vec, res, fallback_used = _minimum_variance_slsqp(cov_np, bounds)
    return _finalize_mv_weights(
        w_vec, cols, cfg, cov_np, bounds, res, fallback_used, diagnostics=diagnostics
    )


def build_minimum_variance_baseline(
    cfg: PortfolioConfig,
    monthly_returns: pd.DataFrame,
    analysis_end: str,
    window_months: int,
) -> BaselineWeightsResult:
    """Backward-compatible alias for :func:`build_minimum_variance_constrained`."""
    return build_minimum_variance_constrained(cfg, monthly_returns, analysis_end, window_months)


def build_maximum_diversification_constrained(
    cfg: PortfolioConfig,
    monthly_returns: pd.DataFrame,
    analysis_end: str,
    window_months: int,
) -> BaselineWeightsResult:
    """
    **maximum_diversification_constrained**: maximize diversification ratio DR on monthly ``Sigma``
    subject to ``sum(weights)=1`` and the same box bounds as :func:`build_minimum_variance_constrained`.
    """
    eligible, coverage = _eligible_universe_from_returns(
        cfg, monthly_returns, analysis_end, window_months
    )
    diagnostics: Dict[str, object] = {
        "universe_eligible": eligible,
        "universe_coverage": coverage,
        "optimizer_name": OPTIMIZER_NAME_MAXIMUM_DIVERSIFICATION_CONSTRAINED,
        "solver": MAXIMUM_DIVERSIFICATION_SOLVER,
        "objective": MAXIMUM_DIVERSIFICATION_OBJECTIVE,
        "analysis_end": str(analysis_end),
        "window_months": int(window_months),
        "active_constraints": [
            "equality: sum(weights) = 1",
            "box: per-asset bounds from feasibility cap and config (min_single / max_single / young caps)",
        ],
    }

    if len(eligible) < 2:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_INFEASIBLE_UNIVERSE",
            diagnostics={
                **diagnostics,
                "reason": "Fewer than 2 eligible assets for Maximum Diversification (constrained)",
            },
        )

    cov_pack = _mv_covariance_for_eligible(
        cfg, monthly_returns, analysis_end, window_months, eligible
    )
    if cov_pack is None:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_DATA",
            diagnostics={
                **diagnostics,
                "reason": "Insufficient history for covariance after inner join",
            },
        )
    (
        cov_np,
        cols,
        covariance_method,
        shrinkage_used,
        psd_repaired,
        young_mode,
        per_ticker_caps,
        young_diagnostics,
    ) = cov_pack
    diagnostics["covariance_method"] = covariance_method
    diagnostics["shrinkage_used"] = bool(shrinkage_used)
    diagnostics["psd_repair_used"] = bool(psd_repaired)
    _attach_young_etf_methodology_diagnostics(
        diagnostics,
        cfg,
        young_mode=young_mode,
        young_diagnostics=young_diagnostics,
        per_ticker_caps=per_ticker_caps,
        role="covariance_and_per_ticker_caps",
    )
    _attach_optimizer_input_fingerprints(
        diagnostics, cfg, monthly_returns, analysis_end, window_months, cols
    )

    min_w = (
        float(cfg.min_single_security_weight_pct)
        if cfg.min_single_security_weight_pct is not None
        and float(cfg.min_single_security_weight_pct) > 0
        else float(MIN_WEIGHT_DEFAULT)
    )
    bounds = _build_bounds(
        cols,
        len(cols),
        min_w,
        cfg.max_single_security_weight_pct,
        per_ticker_caps,
    )
    diagnostics["bounds_used"] = _bounds_export(bounds, cols)
    diagnostics["constraint_summary"] = {
        "sum_weights": "equality_1",
        "box_source": "_build_bounds",
        "young_caps_applied": isinstance(per_ticker_caps, dict) and len(per_ticker_caps) > 0,
    }

    if not _budget_simplex_intersects_box(bounds):
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_INFEASIBLE_BOUNDS",
            diagnostics={
                **diagnostics,
                "reason": (
                    "Weight bounds infeasible for a fully invested portfolio "
                    "(sum of lower bounds > 1 or sum of upper bounds < 1)"
                ),
                "bounds_detail": {
                    cols[i]: {"min": float(bounds[i][0]), "max": float(bounds[i][1])}
                    for i in range(len(cols))
                },
            },
        )

    w_vec, res, fallback_used = _maximum_diversification_slsqp(cov_np, bounds)
    return _finalize_md_weights(
        w_vec, cols, cfg, cov_np, bounds, res, fallback_used, diagnostics=diagnostics
    )


def build_maximum_diversification_unconstrained(
    cfg: PortfolioConfig,
    monthly_returns: pd.DataFrame,
    analysis_end: str,
    window_months: int,
) -> BaselineWeightsResult:
    """
    **maximum_diversification_unconstrained**: maximize diversification ratio DR on monthly ``Sigma``
    subject to ``sum(weights)=1`` and **long-only** weights via per-asset bounds ``[0, 1]``.

    Does **not** apply project policy box bounds (no min/max single name from config, no feasibility
    per-asset caps, no Young per-ticker caps as optimizer bounds). Covariance / eligible-universe
    path matches :func:`build_maximum_diversification_constrained`.
    """
    eligible, coverage = _eligible_universe_from_returns(
        cfg, monthly_returns, analysis_end, window_months
    )
    diagnostics: Dict[str, object] = {
        "universe_eligible": eligible,
        "universe_coverage": coverage,
        "optimizer_name": OPTIMIZER_NAME_MAXIMUM_DIVERSIFICATION_UNCONSTRAINED,
        "solver": MAXIMUM_DIVERSIFICATION_SOLVER,
        "objective": MAXIMUM_DIVERSIFICATION_OBJECTIVE,
        "analysis_end": str(analysis_end),
        "window_months": int(window_months),
        "active_constraints": [
            "equality: sum(weights) = 1",
            "long-only: weights >= 0",
        ],
    }

    if len(eligible) < 2:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_INFEASIBLE_UNIVERSE",
            diagnostics={
                **diagnostics,
                "reason": "Fewer than 2 eligible assets for Maximum Diversification (unconstrained)",
            },
        )

    cov_pack = _mv_covariance_for_eligible(
        cfg, monthly_returns, analysis_end, window_months, eligible
    )
    if cov_pack is None:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_DATA",
            diagnostics={
                **diagnostics,
                "reason": "Insufficient history for covariance after inner join",
            },
        )
    (
        cov_np,
        cols,
        covariance_method,
        shrinkage_used,
        psd_repaired,
        young_mode,
        _per_ticker_caps,
        young_diagnostics,
    ) = cov_pack
    diagnostics["covariance_method"] = covariance_method
    diagnostics["shrinkage_used"] = bool(shrinkage_used)
    diagnostics["psd_repair_used"] = bool(psd_repaired)
    _attach_young_etf_methodology_diagnostics(
        diagnostics,
        cfg,
        young_mode=young_mode,
        young_diagnostics=young_diagnostics,
        per_ticker_caps=None,
        role="covariance_only",
    )
    _attach_optimizer_input_fingerprints(
        diagnostics, cfg, monthly_returns, analysis_end, window_months, cols
    )

    bounds = [(0.0, 1.0)] * len(cols)
    diagnostics["bounds_used"] = _bounds_export(bounds, cols)
    diagnostics["constraint_summary"] = {
        "sum_weights": "equality_1",
        "box_source": "long_only_unit_box",
        "young_caps_applied": False,
    }
    if not _budget_simplex_intersects_box(bounds):
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_INFEASIBLE_BOUNDS",
            diagnostics={
                **diagnostics,
                "reason": "Long-only unit hypercube unexpectedly infeasible for sum(weights)=1",
            },
        )

    w_vec, res, fallback_used = _maximum_diversification_slsqp(cov_np, bounds)
    return _finalize_md_weights(
        w_vec, cols, cfg, cov_np, bounds, res, fallback_used, diagnostics=diagnostics
    )


def build_hierarchical_risk_parity_baseline(
    cfg: PortfolioConfig,
    monthly_returns: pd.DataFrame,
    analysis_end: str,
    window_months: int,
) -> BaselineWeightsResult:
    """
    **hierarchical_risk_parity** (canonical baseline): cluster assets by correlation distance,
    quasi-diagonalize monthly Σ, recursive bisection (inverse-variance between clusters).

    Unconstrained diversification baseline comparable to Risk Parity: **long-only**, **sum(w)=1**,
    **no** policy min/max box, **no** Young caps as optimization constraints, **no** SLSQP projection.
    Uses the same monthly Σ estimation path as constrained MinVar / MaxDiv via
    :func:`_mv_covariance_for_eligible` (Ledoit–Wolf/shrinkage and Young dual per config; PSD repair).
    """
    eligible, coverage = _eligible_universe_from_returns(
        cfg, monthly_returns, analysis_end, window_months
    )
    diagnostics: Dict[str, object] = {
        "universe_eligible": eligible,
        "universe_coverage": coverage,
        "optimizer_name": OPTIMIZER_NAME_HIERARCHICAL_RISK_PARITY,
        "hrp_interpretation": (
            "Pure HRP baseline: hierarchical clustering on correlation distance, recursive bisection. "
            "No matrix inversion; no optimizer box projection. Comparable to canonical Risk Parity as "
            "an unconstrained diversification reference."
        ),
    }

    if len(eligible) < 2:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_INFEASIBLE_UNIVERSE",
            diagnostics={
                **diagnostics,
                "reason": "Fewer than 2 eligible assets for Hierarchical Risk Parity baseline",
            },
        )

    cov_pack = _mv_covariance_for_eligible(
        cfg, monthly_returns, analysis_end, window_months, eligible
    )
    if cov_pack is None:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_DATA",
            diagnostics={
                **diagnostics,
                "reason": "Insufficient history for covariance after inner join",
            },
        )
    (
        cov_np,
        cols,
        covariance_method,
        shrinkage_used,
        psd_repaired,
        young_mode,
        _caps,
        young_diagnostics,
    ) = cov_pack
    diagnostics["covariance_method"] = covariance_method
    diagnostics["shrinkage_used"] = bool(shrinkage_used)
    diagnostics["psd_repair_used"] = bool(psd_repaired)
    _attach_young_etf_methodology_diagnostics(
        diagnostics,
        cfg,
        young_mode=young_mode,
        young_diagnostics=young_diagnostics,
        per_ticker_caps=None,
        role="covariance_only",
    )

    try:
        w_arr, hrp_meta = hrp_long_only_weights(cov_np, prefer_ward=True)
    except Exception as exc:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_NUMERICAL",
            diagnostics={
                **diagnostics,
                "reason": f"HRP construction failed: {exc}",
            },
        )

    if w_arr.size != len(cols) or not np.all(np.isfinite(w_arr)):
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_NUMERICAL",
            diagnostics={**diagnostics, "reason": "HRP returned non-finite weights"},
        )

    w_vec = np.clip(np.asarray(w_arr, dtype=float), 0.0, None)
    ssum = float(w_vec.sum())
    if ssum <= 1e-18:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_NUMERICAL",
            diagnostics={**diagnostics, "reason": "HRP weights sum to ~0"},
        )
    w_vec = w_vec / ssum

    var_p = float(w_vec @ cov_np @ w_vec)
    ann_vol = float(np.sqrt(max(var_p, 0.0) * 12.0))
    weights: Dict[str, float] = {t: 0.0 for t in cfg.tickers}
    for i, t in enumerate(cols):
        weights[t] = float(w_vec[i])
    w_nonzero = {t: float(weights[t]) for t in cols if weights[t] > 1e-14}
    diagnostics.update(
        {
            "eligible_universe": list(cols),
            "final_weights": dict(sorted(w_nonzero.items(), key=lambda x: (-x[1], x[0]))),
            "portfolio_variance": var_p,
            "annualized_volatility": ann_vol,
            "hrp_linkage_method": hrp_meta.get("linkage_method"),
            "hrp_linkage_fallback_from_ward": bool(hrp_meta.get("linkage_fallback_from_ward")),
            "hrp_distance": hrp_meta.get("distance"),
            "hrp_seriation_indices": hrp_meta.get("seriation_indices"),
            "hrp_weights_sum": float(hrp_meta.get("weights_sum", np.sum(w_vec))),
        }
    )
    return BaselineWeightsResult(weights=weights, status="OK", diagnostics=diagnostics)


def _minimum_cvar_tail_effective_obs(T: int, gamma: float) -> int:
    """Discrete tail count for reporting: at least one scenario in the tail mass (1-gamma)."""
    return max(1, int(np.ceil(float(T) * (1.0 - float(gamma)))))


def _minimum_cvar_empirical_loss_cvar(R: np.ndarray, w: np.ndarray, gamma: float) -> float:
    """
    Sample CVaR of loss L_t = -(Rw)_t: mean of the worst ceil(T*(1-gamma)) losses.
    Aligns with common discrete CVaR reporting (not identical to LP alpha+z average unless linear loss).
    """
    R = np.asarray(R, dtype=float)
    w = np.asarray(w, dtype=float)
    L = -(R @ w)
    T = int(L.shape[0])
    if T < 1:
        return float("nan")
    k = _minimum_cvar_tail_effective_obs(T, gamma)
    order = np.argsort(-L)
    return float(np.mean(L[order[:k]]))


def _minimum_cvar_linprog(
    R: np.ndarray,
    gamma: float,
    w_bounds: list[tuple[float, float]],
    scenario_dates: pd.DatetimeIndex | None = None,
    *,
    z_active_tol_abs: float = 1e-8,
) -> Dict[str, Any]:
    """
    Rockafellar-Uryasev: minimize alpha + (1/(T*(1-gamma))) * sum(z)
    s.t. z_t >= -(Rw)_t - alpha, z>=0, sum(w)=1, box bounds on w.

    Variables: [w_0..w_{n-1}, alpha, z_0..z_{T-1}].
    """
    R = np.asarray(R, dtype=float)
    if R.ndim != 2:
        return {"ok": False, "reason": "R_not_matrix"}
    T, n = int(R.shape[0]), int(R.shape[1])
    if T < 1 or n < 1:
        return {"ok": False, "reason": "empty_R"}
    if len(w_bounds) != n:
        return {"ok": False, "reason": "bounds_dim_mismatch"}
    gamma_f = float(gamma)
    if not (0.0 < gamma_f < 1.0):
        return {"ok": False, "reason": "gamma_out_of_range"}
    one_minus = 1.0 - gamma_f
    lam = 1.0 / (float(T) * one_minus)
    tail_effective_obs = _minimum_cvar_tail_effective_obs(T, gamma_f)

    n_vars = n + 1 + T
    c = np.zeros(n_vars, dtype=float)
    c[n] = 1.0
    c[n + 1 :] = lam

    A_ub = np.zeros((T, n_vars), dtype=float)
    for t in range(T):
        A_ub[t, :n] = -R[t, :]
        A_ub[t, n] = -1.0
        A_ub[t, n + 1 + t] = -1.0
    b_ub = np.zeros(T, dtype=float)

    A_eq = np.zeros((1, n_vars), dtype=float)
    A_eq[0, :n] = 1.0
    b_eq = np.array([1.0], dtype=float)

    bounds: list[tuple[float | None, float | None]] = [
        (float(lo), float(hi)) for lo, hi in w_bounds
    ] + [(None, None)]
    bounds += [(0.0, None)] * T

    res = linprog(
        c,
        A_ub=A_ub,
        b_ub=b_ub,
        A_eq=A_eq,
        b_eq=b_eq,
        bounds=bounds,
        method="highs",
    )

    ok = bool(res.success) and res.x is not None and np.all(np.isfinite(res.x))
    if not ok:
        return {
            "ok": False,
            "reason": "linprog_failed",
            "linprog_success": bool(res.success),
            "linprog_status": int(res.status) if res.status is not None else None,
            "linprog_message": str(res.message) if res.message is not None else "",
            "n_scenarios": T,
            "tail_effective_obs": tail_effective_obs,
            "tail_fraction": one_minus,
        }

    x = np.asarray(res.x, dtype=float)
    w = x[:n].copy()
    alpha = float(x[n])
    z = x[n + 1 :].copy()
    obj = float(res.fun)

    z_max = float(np.max(z)) if z.size else 0.0
    thr = z_active_tol_abs
    if z_max > 0.0:
        thr = max(thr, z_active_tol_abs * z_max)
    tail_scenarios_used: list[Dict[str, Any]] = []
    for t in range(T):
        if z[t] > thr:
            entry: Dict[str, Any] = {"index": t, "z": float(z[t])}
            if scenario_dates is not None and t < len(scenario_dates):
                ts = scenario_dates[t]
                if isinstance(ts, pd.Timestamp):
                    entry["date"] = ts.strftime("%Y-%m-%d")
                else:
                    entry["date"] = str(ts)[:10]
            tail_scenarios_used.append(entry)

    return {
        "ok": True,
        "w": w,
        "alpha": alpha,
        "z": z,
        "cvar_objective_value": obj,
        "linprog_success": True,
        "linprog_status": int(res.status) if res.status is not None else None,
        "linprog_message": str(res.message) if res.message is not None else "",
        "n_scenarios": T,
        "tail_effective_obs": tail_effective_obs,
        "tail_fraction": one_minus,
        "tail_scenarios_used": tail_scenarios_used,
        "lambda_cvar": lam,
    }


def _finalize_minimum_cvar_weights(
    cols: list[str],
    cfg: PortfolioConfig,
    cov_np: np.ndarray,
    bounds: list[tuple[float, float]],
    lp_out: Dict[str, Any],
    *,
    diagnostics: Dict[str, object],
    gamma: float,
    R: np.ndarray,
) -> BaselineWeightsResult:
    if not lp_out.get("ok"):
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_NUMERICAL",
            diagnostics={
                **diagnostics,
                "reason": lp_out.get("reason", "minimum_cvar_linprog_failed"),
                "linprog_success": lp_out.get("linprog_success"),
                "linprog_status": lp_out.get("linprog_status"),
                "linprog_message": lp_out.get("linprog_message"),
            },
        )

    w_raw = np.asarray(lp_out["w"], dtype=float)
    if not np.all(np.isfinite(w_raw)) or w_raw.shape[0] != len(cols):
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_NUMERICAL",
            diagnostics={**diagnostics, "reason": "non_finite_weights"},
        )

    lo_arr = np.array([b[0] for b in bounds], dtype=float)
    hi_arr = np.array([b[1] for b in bounds], dtype=float)
    w_vec = np.clip(w_raw, lo_arr, hi_arr)
    ssum = float(w_vec.sum())
    if ssum > 1e-12:
        w_vec = w_vec / ssum
    else:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_NUMERICAL",
            diagnostics={**diagnostics, "reason": "weights_sum_zero_after_clip"},
        )

    cov_a = np.asarray(cov_np, dtype=float)
    var_p = float(w_vec @ cov_a @ w_vec)
    ann_vol = float(np.sqrt(max(var_p, 0.0) * 12.0))
    weights: Dict[str, float] = {t: 0.0 for t in cfg.tickers}
    for i, t in enumerate(cols):
        weights[t] = float(w_vec[i])
    w_nonzero = {t: float(weights[t]) for t in cols if weights[t] > 1e-14}
    emp_cvar = _minimum_cvar_empirical_loss_cvar(R, w_vec, gamma)

    diagnostics.update(
        {
            "eligible_universe": list(cols),
            "final_weights": dict(sorted(w_nonzero.items(), key=lambda x: (-x[1], x[0]))),
            "portfolio_variance": var_p,
            "annualized_volatility": ann_vol,
            "cvar_confidence_level": float(gamma),
            "tail_fraction": float(lp_out["tail_fraction"]),
            "n_scenarios": int(lp_out["n_scenarios"]),
            "cvar_objective_value": float(lp_out["cvar_objective_value"]),
            "empirical_cvar_loss": emp_cvar,
            "linprog_status": lp_out.get("linprog_status"),
            "linprog_success": bool(lp_out.get("linprog_success")),
            "linprog_message": lp_out.get("linprog_message"),
            "tail_effective_obs": int(lp_out["tail_effective_obs"]),
            "tail_scenarios_used": lp_out.get("tail_scenarios_used", []),
            "max_weight": float(np.max(w_vec)) if len(w_vec) else 0.0,
            "min_weight": float(np.min(w_vec)) if len(w_vec) else 0.0,
        }
    )
    tol_sum = 1e-5
    tol_b = 1e-5
    sum_ok = abs(float(np.sum(w_vec)) - 1.0) < tol_sum
    in_bounds = bool(np.all(w_vec >= lo_arr - tol_b) and np.all(w_vec <= hi_arr + tol_b))
    if sum_ok and in_bounds:
        status = "OK"
    elif sum_ok and in_bounds and var_p == var_p:
        status = "APPROXIMATE"
    else:
        status = "FAIL_NUMERICAL"
    return BaselineWeightsResult(weights=weights, status=status, diagnostics=diagnostics)


def _minimum_cvar_resolve_gamma(
    cfg: PortfolioConfig, confidence_level: float | None
) -> float:
    if confidence_level is not None:
        return float(confidence_level)
    return float(getattr(cfg, "minimum_cvar_confidence_level", 0.95))


def build_minimum_cvar_uncapped(
    cfg: PortfolioConfig,
    monthly_returns: pd.DataFrame,
    analysis_end: str,
    window_months: int,
    *,
    confidence_level: float | None = None,
) -> BaselineWeightsResult:
    """
    **minimum_cvar_uncapped**: minimize sample CVaR of loss L=-(Rw) on monthly scenarios R;
    long-only, sum(w)=1, **w_i in [0,1]** per asset (no config min/max or Young caps in the LP).
    """
    gamma = _minimum_cvar_resolve_gamma(cfg, confidence_level)
    eligible, coverage = _eligible_universe_from_returns(
        cfg, monthly_returns, analysis_end, window_months
    )
    diagnostics: Dict[str, object] = {
        "universe_eligible": eligible,
        "universe_coverage": coverage,
        "optimizer_name": OPTIMIZER_NAME_MINIMUM_CVAR_UNCAPPED,
        "solver": MINIMUM_CVAR_SOLVER,
        "objective": MINIMUM_CVAR_OBJECTIVE,
        "analysis_end": str(analysis_end),
        "window_months": int(window_months),
        "active_constraints": [
            "equality: sum(weights) = 1",
            "long-only: 0 <= w_i <= 1 per asset (no project caps)",
            "Rockafellar-Uryasev auxiliary z_t >= 0",
        ],
        "weight_bounds_note": "[0,1] per asset; no config/young caps",
    }
    if not (0.0 < gamma < 1.0):
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_NUMERICAL",
            diagnostics={**diagnostics, "reason": "cvar_confidence_level must be in (0,1)"},
        )
    if len(eligible) < 2:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_INFEASIBLE_UNIVERSE",
            diagnostics={
                **diagnostics,
                "reason": "Fewer than 2 eligible assets for Minimum CVaR (uncapped)",
            },
        )

    cov_pack = _mv_covariance_for_eligible(
        cfg, monthly_returns, analysis_end, window_months, eligible
    )
    if cov_pack is None:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_DATA",
            diagnostics={
                **diagnostics,
                "reason": "Insufficient history for covariance/scenarios after inner join",
            },
        )
    (
        cov_np,
        cols,
        covariance_method,
        shrinkage_used,
        psd_repaired,
        young_mode,
        _caps,
        young_diagnostics,
    ) = cov_pack
    diagnostics["covariance_method"] = covariance_method
    diagnostics["shrinkage_used"] = bool(shrinkage_used)
    diagnostics["psd_repair_used"] = bool(psd_repaired)
    _attach_young_etf_methodology_diagnostics(
        diagnostics,
        cfg,
        young_mode=young_mode,
        young_diagnostics=young_diagnostics,
        per_ticker_caps=None,
        role="covariance_only",
    )

    returns_slice = slice_window(
        monthly_returns[cols], analysis_end, window_months
    ).dropna(how="any")
    if returns_slice.shape[0] < 2:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_DATA",
            diagnostics={
                **diagnostics,
                "reason": f"Insufficient scenario rows after dropna (rows={returns_slice.shape[0]})",
            },
        )
    R = returns_slice[cols].to_numpy(dtype=float)
    scenario_dates = returns_slice.index
    _attach_optimizer_input_fingerprints(
        diagnostics,
        cfg,
        monthly_returns,
        analysis_end,
        window_months,
        cols,
        extra_config={"cvar_confidence_level": gamma},
        returns_window=returns_slice[cols],
    )

    n = len(cols)
    bounds = [(0.0, 1.0)] * n
    diagnostics["bounds_used"] = _bounds_export(bounds, cols)
    diagnostics["constraint_summary"] = {
        "sum_weights": "equality_1",
        "box_source": "long_only_unit_box",
        "young_caps_applied": False,
        "auxiliary_variables": "rockafellar_uryasev_z",
    }
    if not _budget_simplex_intersects_box(bounds):
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_INFEASIBLE_BOUNDS",
            diagnostics={
                **diagnostics,
                "reason": "Unit-box simplex unexpectedly infeasible for sum(weights)=1",
            },
        )

    lp_out = _minimum_cvar_linprog(R, gamma, bounds, scenario_dates=scenario_dates)
    return _finalize_minimum_cvar_weights(
        cols,
        cfg,
        cov_np,
        bounds,
        lp_out,
        diagnostics=diagnostics,
        gamma=gamma,
        R=R,
    )


def build_minimum_cvar_constrained(
    cfg: PortfolioConfig,
    monthly_returns: pd.DataFrame,
    analysis_end: str,
    window_months: int,
    *,
    confidence_level: float | None = None,
) -> BaselineWeightsResult:
    """
    **minimum_cvar_constrained**: same CVaR objective as uncapped but **box bounds** from
    :func:`src.optimization._build_bounds` (config min/max and Young per-ticker caps when active).
    """
    gamma = _minimum_cvar_resolve_gamma(cfg, confidence_level)
    eligible, coverage = _eligible_universe_from_returns(
        cfg, monthly_returns, analysis_end, window_months
    )
    diagnostics: Dict[str, object] = {
        "universe_eligible": eligible,
        "universe_coverage": coverage,
        "optimizer_name": OPTIMIZER_NAME_MINIMUM_CVAR_CONSTRAINED,
        "solver": MINIMUM_CVAR_SOLVER,
        "objective": MINIMUM_CVAR_OBJECTIVE,
        "analysis_end": str(analysis_end),
        "window_months": int(window_months),
        "active_constraints": [
            "equality: sum(weights) = 1",
            "box: per-asset bounds from feasibility cap and config (min_single / max_single / young caps)",
            "Rockafellar-Uryasev auxiliary z_t >= 0",
        ],
    }
    if not (0.0 < gamma < 1.0):
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_NUMERICAL",
            diagnostics={**diagnostics, "reason": "cvar_confidence_level must be in (0,1)"},
        )
    if len(eligible) < 2:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_INFEASIBLE_UNIVERSE",
            diagnostics={
                **diagnostics,
                "reason": "Fewer than 2 eligible assets for Minimum CVaR (constrained)",
            },
        )

    cov_pack = _mv_covariance_for_eligible(
        cfg, monthly_returns, analysis_end, window_months, eligible
    )
    if cov_pack is None:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_DATA",
            diagnostics={
                **diagnostics,
                "reason": "Insufficient history for covariance/scenarios after inner join",
            },
        )
    (
        cov_np,
        cols,
        covariance_method,
        shrinkage_used,
        psd_repaired,
        young_mode,
        per_ticker_caps,
        young_diagnostics,
    ) = cov_pack
    diagnostics["covariance_method"] = covariance_method
    diagnostics["shrinkage_used"] = bool(shrinkage_used)
    diagnostics["psd_repair_used"] = bool(psd_repaired)
    _attach_young_etf_methodology_diagnostics(
        diagnostics,
        cfg,
        young_mode=young_mode,
        young_diagnostics=young_diagnostics,
        per_ticker_caps=per_ticker_caps,
        role="covariance_and_per_ticker_caps",
    )

    returns_slice = slice_window(
        monthly_returns[cols], analysis_end, window_months
    ).dropna(how="any")
    if returns_slice.shape[0] < 2:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_DATA",
            diagnostics={
                **diagnostics,
                "reason": f"Insufficient scenario rows after dropna (rows={returns_slice.shape[0]})",
            },
        )
    R = returns_slice[cols].to_numpy(dtype=float)
    scenario_dates = returns_slice.index
    n = len(cols)
    _attach_optimizer_input_fingerprints(
        diagnostics,
        cfg,
        monthly_returns,
        analysis_end,
        window_months,
        cols,
        extra_config={"cvar_confidence_level": gamma},
        returns_window=returns_slice[cols],
    )

    min_w = (
        float(cfg.min_single_security_weight_pct)
        if cfg.min_single_security_weight_pct is not None
        and float(cfg.min_single_security_weight_pct) > 0
        else float(MIN_WEIGHT_DEFAULT)
    )
    bounds = _build_bounds(
        cols,
        len(cols),
        min_w,
        cfg.max_single_security_weight_pct,
        per_ticker_caps,
    )
    diagnostics["bounds_used"] = _bounds_export(bounds, cols)
    young_applied = isinstance(per_ticker_caps, dict) and len(per_ticker_caps) > 0
    diagnostics["constraint_summary"] = {
        "sum_weights": "equality_1",
        "box_source": "_build_bounds",
        "young_caps_applied": young_applied,
        "auxiliary_variables": "rockafellar_uryasev_z",
    }

    if not _budget_simplex_intersects_box(bounds):
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_INFEASIBLE_BOUNDS",
            diagnostics={
                **diagnostics,
                "reason": (
                    "Weight bounds infeasible for a fully invested portfolio "
                    "(sum of lower bounds > 1 or sum of upper bounds < 1)"
                ),
            },
        )

    lp_out = _minimum_cvar_linprog(R, gamma, bounds, scenario_dates=scenario_dates)
    return _finalize_minimum_cvar_weights(
        cols,
        cfg,
        cov_np,
        bounds,
        lp_out,
        diagnostics=diagnostics,
        gamma=gamma,
        R=R,
    )


def build_minimum_variance_uncapped_long_only(
    cfg: PortfolioConfig,
    monthly_returns: pd.DataFrame,
    analysis_end: str,
    window_months: int,
) -> BaselineWeightsResult:
    """**minimum_variance_uncapped_long_only**: only ``w >= 0``, ``sum w = 1``, no min/max or Young caps."""
    eligible, coverage = _eligible_universe_from_returns(
        cfg, monthly_returns, analysis_end, window_months
    )
    diagnostics: Dict[str, object] = {
        "universe_eligible": eligible,
        "universe_coverage": coverage,
        "optimizer_name": OPTIMIZER_NAME_MINIMUM_VARIANCE_UNCAPPED,
        "constraints_used": list(MV_UNCAPPED_CONSTRAINTS_USED),
        "constraints_not_used": list(MV_UNCAPPED_CONSTRAINTS_NOT_USED),
        "solver": MINIMUM_VARIANCE_SOLVER,
        "objective": MINIMUM_VARIANCE_OBJECTIVE,
        "analysis_end": str(analysis_end),
        "window_months": int(window_months),
    }

    if len(eligible) < 2:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_INFEASIBLE_UNIVERSE",
            diagnostics={
                **diagnostics,
                "reason": "Fewer than 2 eligible assets for Minimum-Variance (uncapped)",
            },
        )

    cov_pack = _mv_covariance_for_eligible(
        cfg, monthly_returns, analysis_end, window_months, eligible
    )
    if cov_pack is None:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_DATA",
            diagnostics={
                **diagnostics,
                "reason": "Insufficient history for covariance after inner join",
            },
        )
    (
        cov_np,
        cols,
        covariance_method,
        shrinkage_used,
        psd_repaired,
        young_mode,
        _caps,
        young_diagnostics,
    ) = cov_pack
    diagnostics["covariance_method"] = covariance_method
    diagnostics["shrinkage_used"] = bool(shrinkage_used)
    diagnostics["psd_repair_used"] = bool(psd_repaired)
    _attach_young_etf_methodology_diagnostics(
        diagnostics,
        cfg,
        young_mode=young_mode,
        young_diagnostics=young_diagnostics,
        per_ticker_caps=None,
        role="covariance_only",
    )
    _attach_optimizer_input_fingerprints(
        diagnostics, cfg, monthly_returns, analysis_end, window_months, cols
    )
    n = len(cols)
    bounds = [(0.0, 1.0)] * n
    diagnostics["bounds_used"] = _bounds_export(bounds, cols)
    diagnostics["constraint_summary"] = {
        "sum_weights": "equality_1",
        "box_source": "long_only_unit_box",
        "young_caps_applied": False,
    }
    if not _budget_simplex_intersects_box(bounds):
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_INFEASIBLE_BOUNDS",
            diagnostics={**diagnostics, "reason": "Uncapped simplex unexpectedly infeasible"},
        )
    w_vec, res, fallback_used = _minimum_variance_slsqp(cov_np, bounds)
    return _finalize_mv_weights(
        w_vec, cols, cfg, cov_np, bounds, res, fallback_used, diagnostics=diagnostics
    )


def _advanced_l1_reference_current_weights(
    cfg: PortfolioConfig, cols: list[str]
) -> tuple[np.ndarray | None, bool, str | None]:
    """
    Current-portfolio weights aligned to ``cols`` (long-only slice, renormalized on eligible names).
    No equal-weight or other fallback reference vector.
    """
    src = getattr(cfg, "weights", None) or {}
    if not isinstance(src, dict) or not src:
        return None, False, "Current portfolio weights missing or empty in config"
    w = np.zeros(len(cols), dtype=float)
    for i, c in enumerate(cols):
        try:
            w[i] = max(0.0, float(src.get(c, 0.0) or 0.0))
        except (TypeError, ValueError):
            w[i] = 0.0
    s = float(w.sum())
    if s < 1e-12:
        return None, False, "No positive current portfolio weight on eligible tickers"
    return w / s, True, None


def build_minimum_variance_advanced_controls(
    cfg: PortfolioConfig,
    monthly_returns: pd.DataFrame,
    analysis_end: str,
    window_months: int,
) -> BaselineWeightsResult:
    """
    **minimum_variance_advanced_controls**: minimize ``0.5 w'Σw`` on monthly **Ledoit--Wolf Σ**
    (forced for this variant) subject to ``sum(w)=1``, long-only **box** bounds (same as constrained
    MinVar / policy feasibility caps), and optionally ``w'Σw ≤ σ²_target / 12`` when
    ``target_vol_annual = σ_target`` is set.

    **Not the primary lowest-volatility-under-constraints baseline** (that is
    **minimum_variance_constrained**). This variant adds Ledoit--Wolf covariance, optional max vol cap,
    and optional **rebalance-aware / turnover control** via L1 vs **current** weights only.

    **L1 turnover:** optional. With **default** ``minimum_variance_turnover_lambda = 0``, behavior is
    pure minimum-variance on this path (no L1). When ``minimum_variance_turnover_lambda > 0`` and
    **current** portfolio weights (``cfg.weights``) yield a positive, renormalized slice on the
    **eligible** advanced-universe columns, set ``l1_reference_source = "current_portfolio"`` and add
    ``λ \\sum_i |w_i - w^{\\mathrm{current}}_i|``. Equal-weight baselines are **never** used.
    Otherwise L1 is off and ``l1_disabled_reason`` explains why.

    Bucket / asset-class caps are **not** modeled beyond what :func:`src.optimization._build_bounds`
    already encodes (e.g. Young-ETF per-ticker caps when dual covariance is on).
    """
    eligible, coverage = _eligible_universe_from_returns(
        cfg, monthly_returns, analysis_end, window_months
    )
    lam_raw = getattr(cfg, "minimum_variance_turnover_lambda", None)
    try:
        lam_cfg = float(lam_raw) if lam_raw is not None else 0.0
        if lam_cfg != lam_cfg:  # NaN
            lam_cfg = 0.0
    except (TypeError, ValueError):
        lam_cfg = 0.0

    tv = getattr(cfg, "target_vol_annual", None)
    v_max: float | None = None
    target_vol_f: float | None = None
    if tv is not None and float(tv) > 0:
        target_vol_f = float(tv)
        v_max = float((target_vol_f / float(np.sqrt(12.0))) ** 2)

    diagnostics: Dict[str, object] = {
        "universe_eligible": eligible,
        "universe_coverage": coverage,
        "optimizer_name": OPTIMIZER_NAME_MINIMUM_VARIANCE_ADVANCED,
        "solver": MINIMUM_VARIANCE_SOLVER,
        "objective": MINIMUM_VARIANCE_OBJECTIVE,
        "analysis_end": str(analysis_end),
        "window_months": int(window_months),
        "minimum_variance_baseline_role": MV_BASELINE_ROLE_ADVANCED_CONTROLS_PURE_PATH,
        "minimum_variance_interpretation": (
            "Advanced minimum-variance controls variant (Ledoit–Wolf monthly Σ; optional maximum "
            "volatility cap; optional L1 vs current weights). "
            "Not the primary lowest-volatility-under-constraints baseline—use minimum_variance_constrained "
            "for that. Role refines when the run completes (pure advanced path vs rebalance-aware L1)."
        ),
        "lambda_turnover": float(lam_cfg),
        "lambda_turnover_effective": 0.0,
        "l1_penalty_used": False,
        "l1_reference_source": None,
        "current_portfolio_weights_available": False,
        "l1_distance_to_current_portfolio": None,
        "l1_penalty_value": None,
        "l1_disabled_reason": None,
        "volatility_target_used": v_max is not None,
        "target_volatility": target_vol_f,
        "target_variance_monthly_cap": v_max,
        "volatility_constraint_feasible": True,
        "volatility_constraint_binding": False,
        "active_constraints": [
            "equality: sum(weights) = 1",
            "box: per-asset bounds (feasibility + config + young caps when dual Σ enabled)",
        ]
        + (
            ["inequality: w.T@Sigma@w <= target_vol_annual**2/12 (monthly Σ)"]
            if v_max is not None
            else []
        ),
        "binding_constraints": [],
    }

    if len(eligible) < 2:
        diagnostics["lambda_turnover_effective"] = 0.0
        diagnostics["l1_disabled_reason"] = "Fewer than 2 eligible assets; L1 not evaluated."
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_INFEASIBLE_UNIVERSE",
            diagnostics={
                **diagnostics,
                "reason": "Fewer than 2 eligible assets for Minimum-Variance (advanced)",
            },
        )

    cov_pack = _mv_covariance_for_eligible(
        cfg,
        monthly_returns,
        analysis_end,
        window_months,
        eligible,
        force_shrinkage=True,
    )
    if cov_pack is None:
        diagnostics["lambda_turnover_effective"] = 0.0
        diagnostics["l1_disabled_reason"] = "Insufficient return history for covariance; L1 not evaluated."
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_DATA",
            diagnostics={
                **diagnostics,
                "reason": "Insufficient history for covariance after inner join",
            },
        )
    (
        cov_np,
        cols,
        covariance_method,
        shrinkage_used,
        psd_repaired,
        young_mode,
        per_ticker_caps,
        young_diagnostics,
    ) = cov_pack
    diagnostics["covariance_method"] = covariance_method
    diagnostics["shrinkage_used"] = bool(shrinkage_used)
    diagnostics["psd_repair_used"] = bool(psd_repaired)
    _attach_young_etf_methodology_diagnostics(
        diagnostics,
        cfg,
        young_mode=young_mode,
        young_diagnostics=young_diagnostics,
        per_ticker_caps=per_ticker_caps,
        role="covariance_and_per_ticker_caps",
    )
    _attach_optimizer_input_fingerprints(
        diagnostics,
        cfg,
        monthly_returns,
        analysis_end,
        window_months,
        cols,
        extra_config={
            "minimum_variance_turnover_lambda": lam_cfg,
            "target_vol_annual": getattr(cfg, "target_vol_annual", None),
        },
    )

    min_w = (
        float(cfg.min_single_security_weight_pct)
        if cfg.min_single_security_weight_pct is not None
        and float(cfg.min_single_security_weight_pct) > 0
        else float(MIN_WEIGHT_DEFAULT)
    )
    bounds = _build_bounds(
        cols,
        len(cols),
        min_w,
        cfg.max_single_security_weight_pct,
        per_ticker_caps,
    )
    diagnostics["bounds_used"] = _bounds_export(bounds, cols)
    diagnostics["constraint_summary"] = {
        "sum_weights": "equality_1",
        "box_source": "_build_bounds",
        "young_caps_applied": isinstance(per_ticker_caps, dict) and len(per_ticker_caps) > 0,
        "volatility_cap_configured": v_max is not None,
        "l1_turnover_configured": lam_cfg > 1e-18,
    }
    if not _budget_simplex_intersects_box(bounds):
        diagnostics["lambda_turnover_effective"] = 0.0
        diagnostics["l1_disabled_reason"] = "Weight bounds infeasible; L1 not evaluated."
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_INFEASIBLE_BOUNDS",
            diagnostics={
                **diagnostics,
                "reason": "Weight bounds infeasible for fully invested portfolio",
                "bounds_detail": {
                    cols[i]: {"min": float(bounds[i][0]), "max": float(bounds[i][1])}
                    for i in range(len(cols))
                },
            },
        )

    w_ref, ref_ok, ref_warn = _advanced_l1_reference_current_weights(cfg, cols)
    diagnostics["current_portfolio_weights_available"] = bool(ref_ok)

    if lam_cfg <= 1e-18:
        lam_solve = 0.0
        l1_dr: str | None = (
            "minimum_variance_turnover_lambda is zero or negative; "
            "L1 turnover penalty disabled."
        )
    elif not ref_ok:
        lam_solve = 0.0
        l1_dr = (ref_warn or "Current portfolio weights unavailable on eligible universe; L1 disabled.")
    else:
        lam_solve = float(lam_cfg)
        l1_dr = None

    diagnostics["lambda_turnover_effective"] = float(lam_solve)
    diagnostics["l1_disabled_reason"] = l1_dr

    if lam_solve > 1e-18 and ref_ok and w_ref is not None:
        diagnostics["l1_reference_source"] = L1_REFERENCE_CURRENT_PORTFOLIO

    turnover_use = bool(lam_solve > 1e-18 and w_ref is not None and ref_ok)

    if v_max is not None:
        w_mv, _, _ = _minimum_variance_slsqp(cov_np, bounds)
        var_lb = float(w_mv @ cov_np @ w_mv)
        if var_lb > v_max + 1e-12:
            diagnostics["volatility_constraint_feasible"] = False
            diagnostics["reason"] = (
                "Infeasible volatility target: minimum achievable variance on constrained "
                f"box exceeds cap (min_var_monthly={var_lb:.6g}, max_allowed={v_max:.6g})."
            )
            return BaselineWeightsResult(
                weights={t: 0.0 for t in cfg.tickers},
                status="FAIL_INFEASIBLE_VOL_TARGET",
                diagnostics=diagnostics,
            )

    w_vec: np.ndarray
    res: Any
    fallback_used: bool
    l1_penalty_used_flag = False

    if turnover_use and w_ref is not None:
        diagnostics["objective"] = (
            "0.5*w.T@Sigma@w + lambda_turnover*sum(abs(w-w_current)) [L1 vs current portfolio]"
        )
        w_vec, res, fallback_used = _minimum_variance_l1_extended_slsqp(
            cov_np,
            bounds,
            w_ref,
            lambda_turnover=lam_solve,
            v_max_monthly=v_max,
        )
        if not np.all(np.isfinite(w_vec)):
            lam_solve = 0.0
            diagnostics["lambda_turnover_effective"] = 0.0
            diagnostics["l1_reference_source"] = None
            diagnostics["l1_disabled_reason"] = (
                "L1 slack optimization did not converge; used fallback without L1 turnover term."
            )
            if v_max is not None:
                w_vec, res, fallback_used = _minimum_variance_w_only_vol_cap_slsqp(
                    cov_np, bounds, v_max
                )
                diagnostics["solver_message"] = (
                    str(getattr(res, "message", ""))
                    + " | L1 slack formulation failed; fell back to vol-capped MV without turnover penalty."
                )
            else:
                w_vec, res, fallback_used = _minimum_variance_slsqp(cov_np, bounds)
                diagnostics["solver_message"] = (
                    str(getattr(res, "message", ""))
                    + " | L1 slack formulation failed; fell back to MV without turnover penalty."
                )
        else:
            l1_penalty_used_flag = True
            diagnostics["l1_disabled_reason"] = None
    elif v_max is not None:
        w_vec, res, fallback_used = _minimum_variance_w_only_vol_cap_slsqp(
            cov_np, bounds, v_max
        )
    else:
        w_vec, res, fallback_used = _minimum_variance_slsqp(cov_np, bounds)

    out = _finalize_mv_weights(
        w_vec, cols, cfg, cov_np, bounds, res, fallback_used, diagnostics=diagnostics
    )
    if out.status in ("FAIL_NUMERICAL",) and out.weights == {t: 0.0 for t in cfg.tickers}:
        return out

    w_fin = np.array([out.weights[c] for c in cols], dtype=float)
    diagnostics["l1_penalty_used"] = bool(l1_penalty_used_flag)
    if w_ref is not None:
        dist = float(np.sum(np.abs(w_fin - w_ref)))
        diagnostics["l1_distance_to_current_portfolio"] = dist
        if l1_penalty_used_flag and lam_solve > 1e-18:
            diagnostics["l1_penalty_value"] = float(lam_solve * dist)
        else:
            diagnostics["l1_penalty_value"] = 0.0
    else:
        diagnostics["l1_distance_to_current_portfolio"] = None
        diagnostics["l1_penalty_value"] = 0.0

    if l1_penalty_used_flag:
        diagnostics["l1_disabled_reason"] = None

    var_m = float(w_fin @ cov_np @ w_fin)
    if v_max is not None:
        bind_tol = max(1e-9, 1e-6 * abs(v_max))
        diagnostics["volatility_constraint_binding"] = bool(abs(v_max - var_m) <= bind_tol)
        diagnostics["volatility_constraint_feasible"] = bool(var_m <= v_max + 1e-8)

    lo_arr = np.array([b[0] for b in bounds], dtype=float)
    hi_arr = np.array([b[1] for b in bounds], dtype=float)
    binding: list[str] = []
    for i, c in enumerate(cols):
        if abs(w_fin[i] - lo_arr[i]) < 1e-5:
            binding.append(f"min_bound:{c}")
        if abs(w_fin[i] - hi_arr[i]) < 1e-5:
            binding.append(f"max_bound:{c}")
    if diagnostics.get("volatility_constraint_binding"):
        binding.append("volatility_cap")
    diagnostics["binding_constraints"] = binding

    if bool(diagnostics.get("l1_penalty_used")):
        diagnostics["minimum_variance_baseline_role"] = (
            MV_BASELINE_ROLE_REBALANCE_AWARE_TURNOVER_CONTROLLED
        )
        diagnostics["minimum_variance_interpretation"] = (
            "Rebalance-aware / turnover-controlled minimum variance: adds an L1 penalty vs "
            "current portfolio weights to limit drift while moving toward lower risk. "
            "This is not the pure lowest-volatility portfolio under the project's box constraints; "
            "for that baseline use minimum_variance_constrained (and set turnover lambda to 0 here "
            "or compare against constrained MinVar outputs)."
        )
    else:
        diagnostics["minimum_variance_baseline_role"] = MV_BASELINE_ROLE_ADVANCED_CONTROLS_PURE_PATH
        diagnostics["minimum_variance_interpretation"] = (
            "Pure minimum variance on the advanced-controls path (Ledoit–Wolf Σ; optional maximum "
            "volatility cap; no active L1 turnover penalty or λ not effective). "
            "Still not the designated primary lowest-volatility-under-constraints baseline for "
            "cross-benchmark use—that role belongs to minimum_variance_constrained."
        )

    out.diagnostics.update(diagnostics)
    return out


def _finalize_robust_mv_weights(
    w_vec: np.ndarray,
    cols: list[str],
    cfg: PortfolioConfig,
    cov_np: np.ndarray,
    bounds: list[tuple[float, float]],
    res: Any,
    *,
    diagnostics: Dict[str, object],
) -> BaselineWeightsResult:
    """Clip to bounds, renormalize, pack full-ticker weights; fill solver and risk diagnostics."""
    if (not np.all(np.isfinite(w_vec))) or w_vec.shape[0] != len(cols):
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_NUMERICAL",
            diagnostics={
                **diagnostics,
                "reason": "Robust MV solver returned non-finite weights",
                "solver_success": bool(getattr(res, "success", False)),
                "solver_message": str(getattr(res, "message", "")),
            },
        )
    lo_arr = np.array([b[0] for b in bounds], dtype=float)
    hi_arr = np.array([b[1] for b in bounds], dtype=float)
    w_vec = np.clip(w_vec, lo_arr, hi_arr)
    ssum = float(w_vec.sum())
    if ssum > 1e-12:
        w_vec = w_vec / ssum
    else:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_NUMERICAL",
            diagnostics={**diagnostics, "reason": "Normalized weights sum to ~0"},
        )

    var_p = float(w_vec @ cov_np @ w_vec)
    ann_vol = float(np.sqrt(max(var_p, 0.0) * 12.0))
    weights: Dict[str, float] = {t: 0.0 for t in cfg.tickers}
    for i, t in enumerate(cols):
        weights[t] = float(w_vec[i])
    w_nonzero = {t: float(weights[t]) for t in cols if weights[t] > 1e-14}
    diag_cm = concentration_metrics(w_nonzero)
    diagnostics.update(
        {
            "eligible_universe": list(cols),
            "final_weights": dict(sorted(w_nonzero.items(), key=lambda x: (-x[1], x[0]))),
            "portfolio_variance": var_p,
            "annualized_volatility": ann_vol,
            "solver_status": getattr(res, "status", None),
            "solver_success": bool(getattr(res, "success", False)),
            "solver_message": str(getattr(res, "message", "")),
            "max_weight": float(np.max(w_vec)) if len(w_vec) else 0.0,
            "min_weight": float(np.min(w_vec)) if len(w_vec) else 0.0,
            "concentration_metrics": diag_cm,
        }
    )
    tol_sum = 1e-5
    tol_b = 1e-5
    sum_ok = abs(float(np.sum(w_vec)) - 1.0) < tol_sum
    in_bounds = bool(np.all(w_vec >= lo_arr - tol_b) and np.all(w_vec <= hi_arr + tol_b))
    solver_ok = bool(getattr(res, "success", False))
    if solver_ok and sum_ok and in_bounds:
        status = "OK"
    elif sum_ok and in_bounds and var_p == var_p:
        status = "APPROXIMATE"
    else:
        status = "FAIL_NUMERICAL"
    return BaselineWeightsResult(weights=weights, status=status, diagnostics=diagnostics)


def _build_robust_mean_variance_core(
    cfg: PortfolioConfig,
    monthly_returns: pd.DataFrame,
    analysis_end: str,
    window_months: int,
    *,
    constrained: bool,
) -> BaselineWeightsResult:
    """Shared Robust Mean–Variance baseline (James–Stein mu; LW/OAS Sigma; SLSQP)."""
    mu_method_raw = getattr(cfg, "robust_mv_mu_shrinkage_method", "james_stein") or "james_stein"
    mu_method = str(mu_method_raw).strip().lower().replace("-", "_")
    if mu_method != "james_stein":
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_CONFIG",
            diagnostics={
                "robust_mv_variant_role": ROBUST_MV_VARIANT_ROLE,
                "robust_mv_variant_summary": ROBUST_MV_VARIANT_SUMMARY,
                "reason": (
                    f"Unsupported robust_mv_mu_shrinkage_method {mu_method_raw!r}; "
                    "only james_stein is implemented"
                ),
            },
        )

    lam_raw = getattr(cfg, "robust_mv_lambda", None)
    if lam_raw is None:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_CONFIG",
            diagnostics={
                "robust_mv_variant_role": ROBUST_MV_VARIANT_ROLE,
                "robust_mv_variant_summary": ROBUST_MV_VARIANT_SUMMARY,
                "reason": (
                    "robust_mv_lambda is unset in PortfolioConfig: run "
                    "`python run_robust_mv_lambda_calibration.py` so baseline scripts can read "
                    "`analysis_robust_mv_lambda_calibration/selected_lambda.txt`, "
                    "pass `--robust-mv-lambda` on the baseline CLI, or set λ programmatically "
                    "(replace(cfg, robust_mv_lambda=…)) for tests."
                ),
            },
        )

    lam = float(lam_raw)
    if lam < 0:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_CONFIG",
            diagnostics={
                "robust_mv_variant_role": ROBUST_MV_VARIANT_ROLE,
                "robust_mv_variant_summary": ROBUST_MV_VARIANT_SUMMARY,
                "reason": "robust_mv_lambda must be >= 0",
            },
        )

    opt_name = (
        OPTIMIZER_NAME_ROBUST_MEAN_VARIANCE_CONSTRAINED
        if constrained
        else OPTIMIZER_NAME_ROBUST_MEAN_VARIANCE_UNCAPPED
    )
    eligible, coverage = _eligible_universe_from_returns(
        cfg, monthly_returns, analysis_end, window_months
    )
    diagnostics: Dict[str, object] = {
        "universe_eligible": eligible,
        "universe_coverage": coverage,
        "optimizer_name": opt_name,
        "solver": ROBUST_MV_SOLVER,
        "objective_minimize": ROBUST_MV_OBJECTIVE_MIN,
        "analysis_end": str(analysis_end),
        "robust_mv_lambda": lam,
        "mu_shrinkage_method": "james_stein",
        "window_months": int(window_months),
        "robust_mv_variant_role": ROBUST_MV_VARIANT_ROLE,
        "robust_mv_variant_summary": ROBUST_MV_VARIANT_SUMMARY,
    }

    if len(eligible) < 2:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_INFEASIBLE_UNIVERSE",
            diagnostics={
                **diagnostics,
                "reason": "Fewer than 2 eligible assets for Robust Mean–Variance baseline",
            },
        )

    returns_slice = slice_window(monthly_returns[eligible], analysis_end, window_months).dropna(
        how="any"
    )
    cols = [str(c) for c in returns_slice.columns]
    if len(cols) < 2 or len(returns_slice) < 2:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_DATA",
            diagnostics={
                **diagnostics,
                "reason": (
                    f"Insufficient synchronous history for Robust MV "
                    f"(rows={len(returns_slice)}, assets={len(cols)})"
                ),
            },
        )
    _attach_optimizer_input_fingerprints(
        diagnostics,
        cfg,
        monthly_returns,
        analysis_end,
        window_months,
        cols,
        extra_config={
            "robust_mv_lambda": lam,
            "robust_mv_covariance_method": getattr(cfg, "robust_mv_covariance_method", None),
            "robust_mv_mu_shrinkage_method": mu_method,
            "constrained": constrained,
        },
        returns_window=returns_slice[cols],
    )

    try:
        cov_method_key = normalize_robust_mv_covariance_method(
            getattr(cfg, "robust_mv_covariance_method", None)
        )
    except ValueError as e:
        return BaselineWeightsResult(
            weights={t: 0.0 for t in cfg.tickers},
            status="FAIL_CONFIG",
            diagnostics={**diagnostics, "reason": str(e)},
        )

    cov_df, cov_fit_meta = shrunk_covariance_monthly(returns_slice, cov_method_key)
    cov_df = cov_df.reindex(index=cols, columns=cols).fillna(0.0)
    cov_np_raw = cov_df.values.astype(float)
    cov_np, repaired = repair_covariance_psd(cov_np_raw)
    finite_cov = bool(np.all(np.isfinite(cov_np)))
    psd_stat = psd_status_after_repair(cov_np, repaired, finite_cov)

    diagnostics["covariance_method"] = str(cov_fit_meta.get("covariance_method", cov_method_key))
    diagnostics["covariance_shrinkage_sklearn"] = cov_fit_meta.get("shrinkage_applied")
    diagnostics["shrinkage_applied"] = cov_fit_meta.get("shrinkage_applied")
    diagnostics["psd_status"] = psd_stat
    diagnostics["psd_repair_used"] = bool(repaired)

    mu_pack = james_stein_shrink_means(returns_slice)
    raw_mu_s = mu_pack["raw_mu"].reindex(cols).fillna(0.0)
    shrunk_mu_s = mu_pack["shrunk_mu"].reindex(cols).fillna(0.0)
    mu_vec = shrunk_mu_s.values.astype(float)

    diagnostics["raw_mu"] = {str(k): round(float(raw_mu_s.loc[k]), 8) for k in cols}
    diagnostics["shrunk_mu"] = {str(k): round(float(shrunk_mu_s.loc[k]), 8) for k in cols}
    diagnostics["shrinkage_target"] = float(mu_pack["shrinkage_target"])
    diagnostics["shrinkage_intensity"] = float(mu_pack["shrinkage_intensity"])

    per_ticker_caps: dict[str, float] | None = None
    young_mode_for_caps: str | None = None
    young_diagnostics_for_caps: dict[str, Any] | None = None
    if constrained:
        young_pol = getattr(cfg, "young_etf_optimization_policy", None) or {}
        if bool(young_pol.get("enabled", True)):
            try:
                _cov_d, _mu_d, ydiag = build_dual_covariance_and_mu(
                    monthly_returns,
                    cols,
                    window_months,
                    young_pol,
                    use_shrinkage_on_core=bool(getattr(cfg, "covariance_shrinkage", False)),
                    analysis_end=pd.Timestamp(analysis_end),
                )
                del _cov_d, _mu_d
                young_diagnostics_for_caps = ydiag
                young_mode_for_caps = str(ydiag.get("mode")) if ydiag.get("mode") is not None else None
                per_ticker_caps = per_ticker_young_weight_caps(
                    ydiag["tickers"],
                    float(young_pol.get("max_weight_candidate_or_new_pct", 0.02)),
                )
                if not per_ticker_caps:
                    per_ticker_caps = None
            except Exception as e:
                return BaselineWeightsResult(
                    weights={t: 0.0 for t in cfg.tickers},
                    status="FAIL_DATA",
                    diagnostics={
                        **diagnostics,
                        "reason": f"Young-ETF dual policy setup failed for caps: {e}",
                    },
                )
        _attach_young_etf_methodology_diagnostics(
            diagnostics,
            cfg,
            young_mode=young_mode_for_caps,
            young_diagnostics=young_diagnostics_for_caps,
            per_ticker_caps=per_ticker_caps,
            role="per_ticker_caps_only",
        )

        min_w = (
            float(cfg.min_single_security_weight_pct)
            if cfg.min_single_security_weight_pct is not None
            and float(cfg.min_single_security_weight_pct) > 0
            else float(MIN_WEIGHT_DEFAULT)
        )
        bounds = _build_bounds(
            cols,
            len(cols),
            min_w,
            cfg.max_single_security_weight_pct,
            per_ticker_caps,
        )
        if not _budget_simplex_intersects_box(bounds):
            return BaselineWeightsResult(
                weights={t: 0.0 for t in cfg.tickers},
                status="FAIL_INFEASIBLE_BOUNDS",
                diagnostics={
                    **diagnostics,
                    "reason": (
                        "Weight bounds infeasible for a fully invested portfolio "
                        "(sum of lower bounds > 1 or sum of upper bounds < 1)"
                    ),
                    "bounds_detail": {
                        cols[i]: {"min": float(bounds[i][0]), "max": float(bounds[i][1])}
                        for i in range(len(cols))
                    },
                },
            )
        diagnostics["bounds_used"] = {
            cols[i]: {"min": float(bounds[i][0]), "max": float(bounds[i][1])} for i in range(len(cols))
        }
        diagnostics["constraint_summary"] = (
            "equality: sum(weights)=1; box bounds from feasibility cap, "
            "config min/max per name, Young-ETF per-ticker caps when dual policy enabled"
        )
        diagnostics["active_constraints"] = diagnostics["constraint_summary"]
    else:
        bounds = [(0.0, 1.0)] * len(cols)
        diagnostics["bounds_used"] = {"mode": "uncapped_long_only", "per_asset_bounds": [0.0, 1.0]}
        diagnostics["constraint_summary"] = (
            "long-only [0,1] per asset, sum(weights)=1; no project feasibility caps or Young caps"
        )

    w_vec, res, obj_val = solve_robust_mean_variance(mu_vec, cov_np, bounds, lam)
    diagnostics["objective_value"] = float(obj_val)

    return _finalize_robust_mv_weights(
        w_vec, cols, cfg, cov_np, bounds, res, diagnostics=diagnostics
    )


def build_robust_mean_variance_uncapped(
    cfg: PortfolioConfig,
    monthly_returns: pd.DataFrame,
    analysis_end: str,
    window_months: int,
) -> BaselineWeightsResult:
    """Robust Mean–Variance with only long-only [0,1] and sum(w)=1 (no project / Young caps)."""
    return _build_robust_mean_variance_core(
        cfg, monthly_returns, analysis_end, window_months, constrained=False
    )


def build_robust_mean_variance_constrained(
    cfg: PortfolioConfig,
    monthly_returns: pd.DataFrame,
    analysis_end: str,
    window_months: int,
) -> BaselineWeightsResult:
    """Robust Mean–Variance under the same box bounds as constrained MinVar / MaxDiv / Min CVaR."""
    return _build_robust_mean_variance_core(
        cfg, monthly_returns, analysis_end, window_months, constrained=True
    )


def export_baseline_weights_txt(
    weights: Dict[str, float],
    rc_series: pd.Series | None,
    label: str,
    output_dir: Path,
) -> None:
    """
    Human-readable weights.txt for baseline variants.
    For Risk-Parity, include realized RC_vol if available.
    """
    lines = [
        f"{label} — final weights",
        "=" * 50,
        "",
    ]
    rc_map = {}
    if rc_series is not None and not rc_series.empty:
        rc_map = {str(t): float(v) for t, v in rc_series.dropna().items()}

    non_zero = {t: w for t, w in weights.items() if w and abs(w) > 1e-12}
    for t in sorted(non_zero.keys(), key=lambda x: (-non_zero[x], x)):
        w = non_zero[t]
        if rc_map:
            rc = rc_map.get(t)
            if rc is not None:
                lines.append(f"  {t}: weight={w:.1%}, RC_vol={rc:.1%}")
            else:
                lines.append(f"  {t}: weight={w:.1%}")
        else:
            lines.append(f"  {t}: weight={w:.1%}")
    lines.append("")
    lines.append(f"Sum of weights: {sum(weights.values()):.1%}")

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "weights.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

