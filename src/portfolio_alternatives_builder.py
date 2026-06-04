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


def build_builder_prefill_from_launchpad_card(
    card: Mapping[str, Any],
    *,
    next_diagnostic_step: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a UI-safe Builder prefill object from one Launchpad v3 card.

    The returned object is diagnostic setup only: it does not build a candidate
    plan, run subprocesses, write weights, or recommend a rebalance.
    """

    suggested_methods = _launchpad_method_rows(card.get("suggested_methods"))
    method_ids = _candidate_method_ids(suggested_methods)
    suggested_method = _pick_suggested_method(card.get("default_method"), method_ids)
    selected_method_row = _method_row_for_id(suggested_methods, suggested_method)
    card_type = _optional_string(card.get("card_type"))
    launch_status = _optional_string(card.get("launch_status"))
    builder_mode = _builder_mode_for_card(
        card,
        suggested_method=suggested_method,
        card_type=card_type,
        launch_status=launch_status,
    )
    candidate_generation_allowed = (
        suggested_method is not None and builder_mode == "guided_from_diagnosis"
    )

    return {
        "builder_mode": builder_mode,
        "source": "candidate_launchpad_v3",
        "source_diagnosis_id": _optional_string(
            card.get("source_diagnosis_id") or card.get("source_problem_id")
        ),
        "source_card_id": _optional_string(card.get("card_id")),
        "goal": _optional_string(card.get("goal")),
        "hypothesis_to_test": _optional_string(card.get("hypothesis_to_test")),
        "next_diagnostic_step": (
            dict(next_diagnostic_step) if next_diagnostic_step is not None else None
        ),
        "suggested_method": suggested_method,
        "alternative_methods": [method_id for method_id in method_ids if method_id != suggested_method],
        "suggested_methods": suggested_methods,
        "constraint_preset": _optional_string(card.get("constraint_preset")),
        "max_asset_weight": card.get("max_asset_weight"),
        "min_asset_weight": card.get("min_asset_weight"),
        "volatility_target": card.get("volatility_target"),
        "success_criteria": list(card.get("success_criteria") or []),
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
    }


def _launchpad_method_rows(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _candidate_method_ids(method_rows: Sequence[Mapping[str, Any]]) -> list[str]:
    method_ids: list[str] = []
    for row in method_rows:
        method_id = str(row.get("candidate_method_id") or "").strip()
        if method_id:
            method_ids.append(method_id)
    return method_ids


def _pick_suggested_method(default_method: Any, method_ids: Sequence[str]) -> str | None:
    default_id = str(default_method or "").strip()
    if default_id:
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
    for row in method_rows:
        if str(row.get("candidate_method_id") or "").strip() == method_id:
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
