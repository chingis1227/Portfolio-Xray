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
from typing import Any, Callable, Sequence

from src.candidate_factory import REVIEW_MODE_PROFILES
from src.candidate_weights import normalize_execution_mode
from src.config_schema import PortfolioConfig
from src.output_policy import DEFAULT_OUTPUT_PROFILE

RunSubprocess = Callable[..., subprocess.CompletedProcess[Any]]

REVIEW_MODES = frozenset(REVIEW_MODE_PROFILES.keys())
DEFAULT_REVIEW_MODE = "core"
# Phased factory (weights + lightweight_comparison) — default for portfolio-first review.
REVIEW_DEFAULT_FACTORY_EXECUTION_MODE = "standard"


@dataclass(frozen=True)
class PortfolioReviewStep:
    stage: str
    label: str
    argv: tuple[str, ...]


@dataclass(frozen=True)
class PortfolioReviewPlan:
    steps: tuple[PortfolioReviewStep, ...]


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
    if resolved_mode == "core":
        subject_argv.append("--use-review-run-context")
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

    return PortfolioReviewPlan(steps=tuple(steps))


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
        "Stages: input -> " + " -> ".join(step.stage for step in plan.steps),
    ]
    for step in plan.steps:
        lines.append(f"  - [{step.stage}] {step.label}")
    return "\n".join(lines)
