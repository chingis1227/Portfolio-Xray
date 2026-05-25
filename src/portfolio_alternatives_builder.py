"""On-demand Portfolio Alternatives Builder wrapper.

The builder turns a selected Launchpad method into an execution plan for one
existing candidate builder path. It does not implement formulas and does not
execute anything unless a caller explicitly runs the returned command.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

DEFAULT_ALTERNATIVES_OUTPUT_PROFILE = "site_api"
DEFAULT_ALTERNATIVES_EXECUTION_MODE = "standard"

# V1 method ids intentionally map to current candidate ids. Keeping this table
# explicit makes the product-facing method allowlist auditable and prevents the
# wrapper from reaching into optimizer/candidate internals.
METHOD_TO_CANDIDATE_ID: dict[str, str] = {
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


@dataclass(frozen=True)
class PortfolioAlternativeRequest:
    """A user-selected candidate hypothesis from Launchpad or equivalent UI."""

    candidate_method_id: str
    goal: str | None = None
    source_card_id: str | None = None
    constraint_preset: str | None = None
    max_asset_weight: float | None = None
    min_asset_weight: float | None = None
    volatility_target: float | None = None
    rebalancing_frequency: str | None = None
    transaction_cost_assumption: float | None = None


@dataclass(frozen=True)
class PortfolioAlternativeBuildPlan:
    """Execution plan for one existing candidate-builder path."""

    candidate_method_id: str
    candidate_id: str
    command: tuple[str, ...]
    artifact_contract: dict[str, Any]
    provenance: dict[str, Any]
    warnings: tuple[str, ...] = field(default_factory=tuple)


def supported_candidate_methods() -> tuple[str, ...]:
    """Return product-facing method ids supported by the V1 wrapper."""

    return tuple(METHOD_TO_CANDIDATE_ID)


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
    method_id = str(method.get("candidate_method_id") or "").strip()
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

    method_id = str(request.candidate_method_id or "").strip()
    candidate_id = METHOD_TO_CANDIDATE_ID.get(method_id)
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
