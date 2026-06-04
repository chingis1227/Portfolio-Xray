"""
Portfolio-first review workflow orchestration.

This is a thin subprocess wrapper. It orders existing entrypoints so the
resolved analysis_subject is diagnosed before candidate generation or
comparison artifacts are produced.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal, Sequence

from src.candidate_factory import REVIEW_MODE_PROFILES
from src.candidate_weights import normalize_execution_mode
from src.config_schema import PortfolioConfig
from src.output_policy import DEFAULT_OUTPUT_PROFILE
from src.workflow_state import WorkflowStateAssessment, resolve_workflow_state

RunSubprocess = Callable[..., subprocess.CompletedProcess[Any]]

REVIEW_MODES = frozenset(REVIEW_MODE_PROFILES.keys())
DEFAULT_REVIEW_MODE = "core"
# Phased factory (weights + lightweight_comparison) — default for portfolio-first review.
REVIEW_DEFAULT_FACTORY_EXECUTION_MODE = "standard"

RuntimeMode = Literal[
    "product_diagnosis_only",
    "product_one_candidate",
    "product_shortlist",
    "research_batch",
    "legacy_policy",
]

RUNTIME_MODE_PRODUCT_DIAGNOSIS_ONLY: RuntimeMode = "product_diagnosis_only"
RUNTIME_MODE_PRODUCT_ONE_CANDIDATE: RuntimeMode = "product_one_candidate"
RUNTIME_MODE_PRODUCT_SHORTLIST: RuntimeMode = "product_shortlist"
RUNTIME_MODE_RESEARCH_BATCH: RuntimeMode = "research_batch"
RUNTIME_MODE_LEGACY_POLICY: RuntimeMode = "legacy_policy"


@dataclass(frozen=True)
class PortfolioReviewStep:
    stage: str
    label: str
    argv: tuple[str, ...]


@dataclass(frozen=True)
class PortfolioReviewPlan:
    steps: tuple[PortfolioReviewStep, ...]
    workflow_state: WorkflowStateAssessment
    runtime_mode: RuntimeMode


def _python(project_root: Path) -> str:
    return sys.executable


def resolve_review_candidate_profile(
    *,
    review_mode: str = DEFAULT_REVIEW_MODE,
    candidate_profile: str | None = None,
) -> tuple[str, str]:
    """Return (review_mode, factory_profile_id). Explicit profile overrides mode."""
    mode = review_mode if review_mode in REVIEW_MODE_PROFILES else DEFAULT_REVIEW_MODE
    if candidate_profile:
        return mode, candidate_profile
    return mode, REVIEW_MODE_PROFILES[mode]


def resolve_factory_execution_mode(
    *,
    factory_execution_mode: str | None = None,
) -> str:
    """Return factory --execution-mode for review-orchestrated runs."""
    if factory_execution_mode:
        return normalize_execution_mode(factory_execution_mode)
    return REVIEW_DEFAULT_FACTORY_EXECUTION_MODE


def _parse_candidate_ids(candidate_ids: str | None) -> tuple[str, ...]:
    if not candidate_ids:
        return ()
    return tuple(part.strip() for part in candidate_ids.split(",") if part.strip())


def resolve_portfolio_review_runtime_mode(
    *,
    skip_candidates: bool = False,
    skip_compare: bool = False,
    review_mode: str = DEFAULT_REVIEW_MODE,
    candidate_profile: str | None = None,
    candidate_ids: str | None = None,
) -> RuntimeMode:
    """Classify the review run without changing its execution behavior.

    This is a routing label for the Documentation/Runtime Truth Reset. It is deliberately
    conservative: existing profile-based candidate runs are classified as research batch until
    later sessions change default behavior.
    """
    parsed_candidate_ids = _parse_candidate_ids(candidate_ids)
    if len(parsed_candidate_ids) == 1:
        return RUNTIME_MODE_PRODUCT_ONE_CANDIDATE
    if len(parsed_candidate_ids) > 1:
        return RUNTIME_MODE_PRODUCT_SHORTLIST
    if skip_candidates and skip_compare:
        return RUNTIME_MODE_PRODUCT_DIAGNOSIS_ONLY
    return RUNTIME_MODE_RESEARCH_BATCH


def build_portfolio_review_plan(
    cfg: PortfolioConfig,
    *,
    project_root: Path,
    no_cache: bool = False,
    skip_candidates: bool = False,
    review_mode: str = DEFAULT_REVIEW_MODE,
    candidate_profile: str | None = None,
    candidate_ids: str | None = None,
    skip_existing_candidates: bool = True,
    force_candidates: bool = False,
    resume_candidates: bool = False,
    fail_fast: bool = False,
    skip_compare: bool = False,
    skip_pdf: bool = True,
    legacy_full_pdf: bool = False,
    factory_execution_mode: str | None = None,
    output_profile: str = DEFAULT_OUTPUT_PROFILE,
    no_parallel_lightweight_reports: bool = False,
) -> PortfolioReviewPlan:
    """Build ordered CLI steps for the portfolio-first review workflow."""
    resolved_mode, factory_profile = resolve_review_candidate_profile(
        review_mode=review_mode,
        candidate_profile=candidate_profile,
    )
    runtime_mode = resolve_portfolio_review_runtime_mode(
        skip_candidates=skip_candidates,
        skip_compare=skip_compare,
        review_mode=resolved_mode,
        candidate_profile=candidate_profile,
        candidate_ids=candidate_ids,
    )
    resolved_execution_mode = resolve_factory_execution_mode(
        factory_execution_mode=factory_execution_mode,
    )
    if legacy_full_pdf:
        skip_pdf = False
    py = _python(project_root)
    cache_flags: list[str] = ["--no-cache"] if no_cache else []
    steps: list[PortfolioReviewStep] = []

    def add(stage: str, label: str, argv: Sequence[str]) -> None:
        steps.append(PortfolioReviewStep(stage=stage, label=label, argv=tuple(argv)))

    subject_type = "analysis_subject"
    if getattr(cfg, "analysis_subject", None):
        subject_type = str((cfg.analysis_subject or {}).get("type") or subject_type)

    subject_argv = [
        py,
        str(project_root / "run_report.py"),
        "--materialize-analysis-subject",
        "--output-profile",
        output_profile,
        "--review-mode",
        resolved_mode,
        *cache_flags,
    ]
    use_shared_review_context = resolved_mode == "core" and not skip_candidates
    if use_shared_review_context:
        subject_argv.append("--use-review-run-context")
    elif resolved_mode == "core":
        subject_argv.append("--no-review-run-context")
    add(
        "diagnosis",
        f"Materialize {subject_type} diagnostics",
        subject_argv,
    )

    compare_via_factory = False
    if not skip_candidates:
        factory_argv = [
            py,
            str(project_root / "run_candidate_factory.py"),
        ]
        if candidate_ids:
            factory_argv.extend(["--candidates", candidate_ids])
        else:
            factory_argv.extend(["--profile", factory_profile])
        if not skip_existing_candidates:
            factory_argv.append("--no-skip-existing")
        if force_candidates:
            factory_argv.append("--force")
        if resume_candidates:
            factory_argv.append("--resume")
        if fail_fast:
            factory_argv.append("--fail-fast")
        factory_argv.extend(["--execution-mode", resolved_execution_mode])
        factory_argv.extend(["--output-profile", output_profile])
        if no_parallel_lightweight_reports:
            factory_argv.append("--no-parallel-lightweight-reports")
        if not skip_compare:
            # Comparison rebuild uses factory_then_compare context (in-memory factory doc,
            # factory JSON written before compare) — see candidate_comparison.py P17-G6 / RM-1025.
            factory_argv.append("--then-compare")
            compare_via_factory = True
        factory_label = (
            f"Candidate factory ({factory_profile}, review_mode={resolved_mode}, "
            f"execution_mode={resolved_execution_mode}) without legacy policy optimization"
        )
        add("candidates", factory_label, factory_argv)

    if not skip_compare and not compare_via_factory:
        add(
            "comparison",
            "Candidate comparison and decision package",
            [py, str(project_root / "run_compare_variants.py"), "--output-profile", output_profile],
        )

    if not skip_pdf:
        pdf_argv = [py, str(project_root / "rebuild_pdf_reports.py")]
        if legacy_full_pdf:
            label = "Rebuild full legacy PDF suite"
        else:
            pdf_argv.append("--portfolio-first")
            label = "Rebuild portfolio-first PDFs (subject + decision package)"
        add("action", label, pdf_argv)

    workflow_state = resolve_workflow_state(
        candidate_ids=candidate_ids,
        factory_profile=None if skip_candidates else factory_profile,
        skip_candidates=skip_candidates,
        skip_compare=skip_compare,
    )

    return PortfolioReviewPlan(
        steps=tuple(steps),
        workflow_state=workflow_state,
        runtime_mode=runtime_mode,
    )


def run_portfolio_review_plan(
    plan: PortfolioReviewPlan,
    *,
    project_root: Path,
    dry_run: bool = False,
    runner: RunSubprocess = subprocess.run,
) -> int:
    """Execute review steps in order; stop on the first non-zero exit."""
    for step in plan.steps:
        cmd = list(step.argv)
        if dry_run:
            print(f"[dry-run] ({step.stage}) {step.label}: {' '.join(cmd)}")
            continue
        print(f"\n=== {step.stage}: {step.label} ===")
        print("Running:", " ".join(cmd))
        completed = runner(
            cmd,
            cwd=str(project_root),
            check=False,
        )
        code = int(completed.returncode)
        if code != 0:
            print(f"Step failed with exit code {code}.")
            return code
    return 0


def summarize_plan(
    plan: PortfolioReviewPlan,
    *,
    review_mode: str = DEFAULT_REVIEW_MODE,
    factory_profile: str | None = None,
) -> str:
    profile_note = f" (factory profile: {factory_profile})" if factory_profile else ""
    lines = [
        "Portfolio review workflow: analysis_subject-first",
        f"Review mode: {review_mode}{profile_note}",
        f"Runtime mode: {plan.runtime_mode}",
        (
            "Workflow state: "
            f"{plan.workflow_state.state} "
            f"(candidate_count={plan.workflow_state.candidate_count}, "
            f"source={plan.workflow_state.source})"
        ),
        "Stages: input -> " + " -> ".join(step.stage for step in plan.steps),
    ]
    for step in plan.steps:
        lines.append(f"  - [{step.stage}] {step.label}")
    return "\n".join(lines)
