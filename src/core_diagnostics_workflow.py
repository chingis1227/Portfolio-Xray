"""
Core diagnostics workflow (Blocks 1-3 only).

Input Layer -> Portfolio X-Ray -> Stress Test Lab.
No candidate generation, comparison, or Blocks 4+ product adapters.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

from src.config_schema import PortfolioConfig
from src.output_policy import DEFAULT_OUTPUT_PROFILE

RunSubprocess = Callable[..., subprocess.CompletedProcess[Any]]


@dataclass(frozen=True)
class CoreDiagnosticsStep:
    label: str
    argv: tuple[str, ...]


@dataclass(frozen=True)
class CoreDiagnosticsPlan:
    steps: tuple[CoreDiagnosticsStep, ...]


def _python(project_root: Path) -> str:
    return sys.executable


def build_core_diagnostics_plan(
    cfg: PortfolioConfig,
    *,
    project_root: Path,
    no_cache: bool = False,
    output_profile: str = DEFAULT_OUTPUT_PROFILE,
) -> CoreDiagnosticsPlan:
    """Build CLI steps for Blocks 1-3 core diagnostics materialization."""
    py = _python(project_root)
    cache_flags: list[str] = ["--no-cache"] if no_cache else []
    argv = [
        py,
        str(project_root / "run_report.py"),
        "--materialize-analysis-subject",
        "--core-diagnostics-only",
        "--output-profile",
        output_profile,
        "--review-mode",
        "core",
        "--use-review-run-context",
        *cache_flags,
    ]
    subject_type = "analysis_subject"
    if getattr(cfg, "analysis_subject", None):
        subject_type = str((cfg.analysis_subject or {}).get("type") or subject_type)
    return CoreDiagnosticsPlan(
        steps=(
            CoreDiagnosticsStep(
                label=f"Core diagnostics: {subject_type} (Blocks 1-3)",
                argv=tuple(argv),
            ),
        )
    )


def run_core_diagnostics_plan(
    plan: CoreDiagnosticsPlan,
    *,
    project_root: Path,
    dry_run: bool = False,
    runner: RunSubprocess = subprocess.run,
) -> int:
    for step in plan.steps:
        cmd = list(step.argv)
        if dry_run:
            print(f"[dry-run] {step.label}: {' '.join(cmd)}")
            continue
        print(f"\n=== core_diagnostics: {step.label} ===")
        print("Running:", " ".join(cmd))
        completed = runner(cmd, cwd=str(project_root), check=False)
        if int(completed.returncode) != 0:
            print(f"Step failed with exit code {completed.returncode}.")
            return int(completed.returncode)
    return 0


def summarize_core_diagnostics_plan(plan: CoreDiagnosticsPlan) -> str:
    lines = [
        "Core diagnostics workflow (Blocks 1-3 only)",
        "Runtime mode: core_diagnostics_only",
        "Flow: Input -> Portfolio X-Ray -> Stress Test Lab",
        "Candidates: disabled",
    ]
    for step in plan.steps:
        lines.append(f"  - {step.label}")
    return "\n".join(lines)
