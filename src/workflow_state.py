"""Pure workflow-state helpers for diagnosis-first Portfolio MRI migration.

This module intentionally does not execute workflows, read generated artifacts,
or change existing CLI behavior. It classifies already-known review intent into
the target product states used by the code migration plan:

- diagnosis-only
- one candidate
- multiple candidates
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence

WORKFLOW_STATE_DIAGNOSIS_ONLY = "diagnosis_only"
WORKFLOW_STATE_ONE_CANDIDATE = "one_candidate"
WORKFLOW_STATE_MULTIPLE_CANDIDATES = "multiple_candidates"

WORKFLOW_STATES = frozenset(
    {
        WORKFLOW_STATE_DIAGNOSIS_ONLY,
        WORKFLOW_STATE_ONE_CANDIDATE,
        WORKFLOW_STATE_MULTIPLE_CANDIDATES,
    }
)

# Keep this local and static so workflow-state classification stays pure and
# cannot accidentally import/run candidate factory code. Counts mirror current
# candidate factory spec/profile definitions at Session 02 time.
FACTORY_PROFILE_CANDIDATE_COUNTS: dict[str, int] = {
    "core_benchmarks": 3,
    "risk_budgets": 3,
    "classic_optimizers": 7,
    "robust_suite": 3,
    "default_v1": 16,
    "core_v1": 6,
    "core_fast": 6,
}


@dataclass(frozen=True)
class WorkflowStateAssessment:
    """Resolved target workflow state plus transparent classification evidence."""

    state: str
    candidate_count: int
    candidate_ids: tuple[str, ...]
    source: str
    comparison_expected: bool
    warnings: tuple[str, ...] = ()

    @property
    def is_diagnosis_only(self) -> bool:
        return self.state == WORKFLOW_STATE_DIAGNOSIS_ONLY

    @property
    def is_one_candidate(self) -> bool:
        return self.state == WORKFLOW_STATE_ONE_CANDIDATE

    @property
    def is_multiple_candidates(self) -> bool:
        return self.state == WORKFLOW_STATE_MULTIPLE_CANDIDATES


def parse_candidate_ids(raw: str | Iterable[str] | None) -> tuple[str, ...]:
    """Normalize comma-separated or iterable candidate ids without validation.

    Validation remains owned by candidate factory/comparison modules. This
    helper only needs a stable count for workflow-state classification.
    """

    if raw is None:
        return ()
    if isinstance(raw, str):
        return tuple(part.strip() for part in raw.split(",") if part.strip())
    return tuple(str(part).strip() for part in raw if str(part).strip())


def _state_for_count(candidate_count: int) -> str:
    if candidate_count <= 0:
        return WORKFLOW_STATE_DIAGNOSIS_ONLY
    if candidate_count == 1:
        return WORKFLOW_STATE_ONE_CANDIDATE
    return WORKFLOW_STATE_MULTIPLE_CANDIDATES


def resolve_workflow_state(
    *,
    candidate_ids: str | Iterable[str] | None = None,
    candidate_count: int | None = None,
    factory_profile: str | None = None,
    artifact_candidate_ids: str | Iterable[str] | None = None,
    skip_candidates: bool = False,
    skip_compare: bool = False,
) -> WorkflowStateAssessment:
    """Classify review intent into the target diagnosis-first workflow states.

    Precedence is deliberately explicit:

    1. explicit ``candidate_count`` when supplied by a caller that already
       resolved candidates;
    2. explicit ``candidate_ids`` from request/options;
    3. existing artifact candidate ids for compare-existing-artifacts flows;
    4. known factory profile counts;
    5. diagnosis-only with an explanatory warning when no candidate evidence is
       available or the profile is unknown.
    """

    warnings: list[str] = []
    ids = parse_candidate_ids(candidate_ids)
    artifact_ids = parse_candidate_ids(artifact_candidate_ids)
    source = "none"

    if candidate_count is not None:
        resolved_count = max(0, int(candidate_count))
        source = "candidate_count"
    elif ids:
        resolved_count = len(ids)
        source = "candidate_ids"
    elif artifact_ids:
        resolved_count = len(artifact_ids)
        ids = artifact_ids
        source = "artifact_candidate_ids"
    elif factory_profile:
        resolved_count = FACTORY_PROFILE_CANDIDATE_COUNTS.get(str(factory_profile), 0)
        source = "factory_profile"
        if resolved_count == 0:
            warnings.append(f"unknown_factory_profile:{factory_profile}")
    else:
        resolved_count = 0
        if not skip_candidates:
            warnings.append("candidate_scope_unresolved")

    if skip_candidates and not ids and not artifact_ids and source == "factory_profile":
        warnings.append("skip_candidates_ignores_factory_profile_without_artifact_ids")
        resolved_count = 0
        source = "skip_candidates"
    elif skip_candidates and resolved_count == 0:
        source = "skip_candidates"

    state = _state_for_count(resolved_count)
    return WorkflowStateAssessment(
        state=state,
        candidate_count=resolved_count,
        candidate_ids=ids,
        source=source,
        comparison_expected=not bool(skip_compare),
        warnings=tuple(warnings),
    )


def classify_review_plan(plan: Any) -> WorkflowStateAssessment:
    """Classify an existing PortfolioReviewPlan without executing it.

    This adapter intentionally uses duck typing so ``src.workflow_state`` does
    not import ``src.portfolio_review_workflow`` and create an orchestration
    dependency. It inspects stages and argv only.
    """

    steps: Sequence[Any] = tuple(getattr(plan, "steps", ()) or ())
    stage_names = tuple(str(getattr(step, "stage", "")) for step in steps)
    comparison_expected = "comparison" in stage_names or "candidates" in stage_names

    for step in steps:
        if str(getattr(step, "stage", "")) != "candidates":
            continue
        argv = tuple(str(part) for part in (getattr(step, "argv", ()) or ()))
        if "--candidates" in argv:
            idx = argv.index("--candidates")
            raw = argv[idx + 1] if idx + 1 < len(argv) else ""
            return resolve_workflow_state(
                candidate_ids=raw,
                skip_compare=not comparison_expected,
            )
        if "--profile" in argv:
            idx = argv.index("--profile")
            profile = argv[idx + 1] if idx + 1 < len(argv) else ""
            return resolve_workflow_state(
                factory_profile=profile,
                skip_compare=not comparison_expected,
            )
        return resolve_workflow_state(
            skip_compare=not comparison_expected,
        )

    assessment = resolve_workflow_state(
        skip_candidates=True,
        skip_compare=not comparison_expected,
    )
    if "comparison" in stage_names:
        return WorkflowStateAssessment(
            state=assessment.state,
            candidate_count=assessment.candidate_count,
            candidate_ids=assessment.candidate_ids,
            source="comparison_existing_artifacts_unknown",
            comparison_expected=True,
            warnings=assessment.warnings + ("comparison_candidate_scope_unknown",),
        )
    return assessment
