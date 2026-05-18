"""
File-first MVP workflow orchestration (thin subprocess wrapper only).

See docs/operational_runbook.md and docs/specs/current_vs_policy_workflow_spec.md.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

from src.config_schema import PortfolioConfig

WorkflowName = str
RunSubprocess = Callable[..., subprocess.CompletedProcess[Any]]

WORKFLOW_POLICY_ONLY = "policy-only"
WORKFLOW_POLICY_CURRENT = "policy-current"
WORKFLOW_DIAGNOSIS_ONLY = "diagnosis-only"
WORKFLOW_FULL_DECISION = "full-decision"

WORKFLOW_CHOICES = (
    WORKFLOW_POLICY_ONLY,
    WORKFLOW_POLICY_CURRENT,
    WORKFLOW_DIAGNOSIS_ONLY,
    WORKFLOW_FULL_DECISION,
)


@dataclass(frozen=True)
class WorkflowStep:
    stage: str
    label: str
    argv: tuple[str, ...]


@dataclass(frozen=True)
class MvpWorkflowPlan:
    workflow: WorkflowName
    steps: tuple[WorkflowStep, ...]


def _python(project_root: Path) -> str:
    return sys.executable


def _has_current_weights(cfg: PortfolioConfig) -> bool:
    weights = cfg.current_weights or {}
    return bool(weights) and sum(float(v) for v in weights.values() if v is not None) > 0


def build_mvp_workflow_plan(
    cfg: PortfolioConfig,
    *,
    project_root: Path,
    workflow: WorkflowName = WORKFLOW_POLICY_ONLY,
    skip_optimize: bool = False,
    no_cache: bool = False,
    no_report: bool = False,
    config_path: Path | None = None,
    optimizer_profile: str | None = None,
    skip_compare: bool = False,
    skip_factory: bool = False,
    factory_profile: str = "default_v1",
    factory_candidates: str | None = None,
    skip_pdf: bool = False,
) -> MvpWorkflowPlan:
    """Build ordered CLI steps for input -> diagnosis -> comparison -> action."""
    if workflow not in WORKFLOW_CHOICES:
        raise ValueError(f"unknown workflow {workflow!r}; expected one of {WORKFLOW_CHOICES}")

    py = _python(project_root)
    cfg_flag: list[str] = []
    if config_path is not None:
        cfg_flag = ["--config", str(config_path)]

    cache_flags: list[str] = ["--no-cache"] if no_cache else []
    steps: list[WorkflowStep] = []
    compare_via_factory = False

    def add(stage: str, label: str, argv: Sequence[str]) -> None:
        steps.append(WorkflowStep(stage=stage, label=label, argv=tuple(argv)))

    mode = (cfg.analysis_mode or "optimize_from_universe").strip().lower()

    if workflow == WORKFLOW_DIAGNOSIS_ONLY or mode == "analyze_current_weights":
        add(
            "diagnosis",
            "Policy/current diagnostics (run_report)",
            [py, str(project_root / "run_report.py"), *cache_flags, *cfg_flag],
        )
        if not skip_compare:
            add(
                "comparison",
                "Candidate comparison and decision package",
                [py, str(project_root / "run_compare_variants.py")],
            )
        if not skip_pdf:
            add(
                "action",
                "Rebuild PDF reports",
                [py, str(project_root / "rebuild_pdf_reports.py")],
            )
        return MvpWorkflowPlan(workflow=workflow, steps=tuple(steps))

    need_explicit_report = skip_optimize or no_report

    if not skip_optimize:
        opt_argv = [py, str(project_root / "run_optimization.py"), *cache_flags, *cfg_flag]
        if optimizer_profile:
            opt_argv.extend(["--profile", optimizer_profile])
        if no_report:
            opt_argv.append("--no-report")
        add("diagnosis", "Policy optimization (and report unless --no-report)", tuple(opt_argv))

    if need_explicit_report:
        add(
            "diagnosis",
            "Policy report and diagnostics",
            [py, str(project_root / "run_report.py"), *cache_flags, *cfg_flag],
        )

    if workflow in (WORKFLOW_POLICY_CURRENT, WORKFLOW_FULL_DECISION):
        if _has_current_weights(cfg):
            add(
                "diagnosis",
                "Current portfolio materialization",
                [
                    py,
                    str(project_root / "run_report.py"),
                    "--materialize-current",
                    *cache_flags,
                    *cfg_flag,
                ],
            )

    if workflow == WORKFLOW_FULL_DECISION and not skip_factory:
        factory_argv = [
            py,
            str(project_root / "run_candidate_factory.py"),
            *cfg_flag,
        ]
        if factory_candidates:
            factory_argv.extend(["--candidates", factory_candidates])
        else:
            factory_argv.extend(["--profile", factory_profile])
        if not skip_compare:
            factory_argv.append("--then-compare")
            compare_via_factory = True
        add("comparison", "Candidate factory", tuple(factory_argv))

    if not skip_compare and not compare_via_factory:
        add(
            "comparison",
            "Candidate comparison and decision package",
            [py, str(project_root / "run_compare_variants.py")],
        )

    if not skip_pdf:
        add(
            "action",
            "Rebuild PDF reports",
            [py, str(project_root / "rebuild_pdf_reports.py")],
        )

    return MvpWorkflowPlan(workflow=workflow, steps=tuple(steps))


def run_mvp_workflow_plan(
    plan: MvpWorkflowPlan,
    *,
    project_root: Path,
    dry_run: bool = False,
    runner: RunSubprocess = subprocess.run,
) -> int:
    """Execute plan steps in order; stop on first non-zero exit."""
    for step in plan.steps:
        if not step.argv:
            continue
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


def summarize_plan(plan: MvpWorkflowPlan) -> str:
    lines = [f"MVP workflow: {plan.workflow}", "Stages: input -> diagnosis -> comparison -> action"]
    for step in plan.steps:
        if step.argv:
            lines.append(f"  - [{step.stage}] {step.label}")
        else:
            lines.append(f"  - [{step.stage}] {step.label} (skipped)")
    return "\n".join(lines)
