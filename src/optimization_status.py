"""Shared optimizer/fallback quality status helpers.

These helpers normalize already-produced solver and builder disclosures. They do
not run optimizers, repair weights, or decide feasibility.
"""

from __future__ import annotations

from typing import Any

CLEAN_SOLVE = "clean_solve"
APPROXIMATE_FALLBACK = "approximate_fallback"
APPROXIMATE_SOLVER = "approximate_solver"
FAILED_SOLVER = "failed_solver"
FAILED = "failed"
UNKNOWN = "unknown"

_CLEAN_ALIASES = {"ok", "clean", "clean_solve", "success", "succeeded"}
_APPROXIMATE_ALIASES = {
    "fallback",
    "ok_fallback",
    "approximate",
    "approximate_fallback",
    "approximate_solver",
}
_FAILED_ALIASES = {"failed", "fail", "failed_solver", "fail_numerical"}


def normalize_optimization_quality_status(
    value: Any = None,
    *,
    solver_success: Any = None,
    solver_status: Any = None,
    fallback_used: Any = False,
) -> str:
    """Return the canonical Block 5 optimizer quality status."""
    if bool(fallback_used):
        return APPROXIMATE_FALLBACK

    raw = str(value or "").strip().lower()
    if raw in _CLEAN_ALIASES:
        return CLEAN_SOLVE
    if raw in _APPROXIMATE_ALIASES:
        if "fallback" in raw:
            return APPROXIMATE_FALLBACK
        return APPROXIMATE_SOLVER
    if raw in _FAILED_ALIASES or raw.startswith("fail"):
        return FAILED_SOLVER if "solver" in raw or "numerical" in raw else FAILED

    status_text = str(solver_status or "").strip().lower()
    if status_text in {"ok", "0"}:
        return CLEAN_SOLVE if solver_success is not False else APPROXIMATE_SOLVER
    if "fallback" in status_text:
        return APPROXIMATE_FALLBACK
    if status_text == "approximate":
        return APPROXIMATE_SOLVER
    if status_text.startswith("fail"):
        return FAILED_SOLVER

    if solver_success is True:
        return CLEAN_SOLVE
    if solver_success is False:
        return FAILED_SOLVER
    return UNKNOWN


def optimization_quality_family(value: Any, *, fallback_used: Any = False) -> str:
    """Group a quality status for factory/comparison/selection policy."""
    status = normalize_optimization_quality_status(value, fallback_used=fallback_used)
    if status == CLEAN_SOLVE:
        return "clean"
    if status in {APPROXIMATE_FALLBACK, APPROXIMATE_SOLVER}:
        return "approximate"
    if status in {FAILED_SOLVER, FAILED}:
        return "failed"
    return "unknown"


def optimizer_quality_from_solver_block(solver: dict[str, Any] | None) -> str:
    """Normalize quality from a metadata `solver` block."""
    solver = solver or {}
    return normalize_optimization_quality_status(
        solver.get("optimization_quality_status"),
        solver_success=(
            solver.get("success") if "success" in solver else solver.get("solver_success")
        ),
        solver_status=solver.get("status") or solver.get("solver_status"),
        fallback_used=solver.get("fallback_used", False),
    )

