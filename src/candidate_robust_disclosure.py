"""
Robust-suite path disclosure for Candidate Portfolio Factory and comparison (Block 4 Session 07).

See docs/specs/candidate_factory_spec.md and docs/specs/candidate_comparison_spec.md.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.robust_mv_lambda_resolve import (
    DEFAULT_CALIBRATION_DIRNAME,
    SELECTED_LAMBDA_FILENAME,
    resolve_robust_mv_lambda_for_baseline,
)

ROBUST_MV_CANDIDATE_IDS = frozenset({"robust_mv_constrained", "robust_mv_uncapped"})
ROBUST_SCENARIO_CANDIDATE_ID = "robust_scenario"
ROBUST_SUITE_CANDIDATE_IDS = ROBUST_MV_CANDIDATE_IDS | {ROBUST_SCENARIO_CANDIDATE_ID}

ROBUST_SCENARIO_PREREQUISITES = (
    "scenario_library_normalized.json",
    "stress_report.json",
)

_LAMBDA_SOURCE_LABELS: dict[str, str] = {
    "cli_override": "CLI --robust-mv-lambda (factory does not pass this; builders only)",
    "calibration_file": "analysis_robust_mv_lambda_calibration/selected_lambda.txt",
    "none": "missing — run run_robust_mv_lambda_calibration.py before robust MV builders",
}

_CALIBRATION_COMMAND = "python run_robust_mv_lambda_calibration.py"


def is_robust_suite_candidate(candidate_id: str) -> bool:
    return candidate_id in ROBUST_SUITE_CANDIDATE_IDS


def build_robust_mv_lambda_disclosure(*, project_root: Path) -> dict[str, Any]:
    """Pre-build λ resolution snapshot (factory does not run calibration)."""
    lam, resolution_key = resolve_robust_mv_lambda_for_baseline(
        project_root=project_root,
        cli_lambda=None,
    )
    cal_dir = project_root / DEFAULT_CALIBRATION_DIRNAME
    cal_file = cal_dir / SELECTED_LAMBDA_FILENAME
    try:
        cal_rel = str(cal_dir.relative_to(project_root)).replace("\\", "/")
    except ValueError:
        cal_rel = DEFAULT_CALIBRATION_DIRNAME
    cal_file_rel = f"{cal_rel}/{SELECTED_LAMBDA_FILENAME}"
    return {
        "kind": "robust_mv_lambda",
        "factory_runs_lambda_calibration": False,
        "calibration_command": _CALIBRATION_COMMAND,
        "calibration_dir": cal_rel,
        "calibration_file": cal_file_rel,
        "calibration_file_present": cal_file.is_file(),
        "lambda_resolution_key": resolution_key,
        "lambda_source_label": _LAMBDA_SOURCE_LABELS.get(
            resolution_key, resolution_key
        ),
        "robust_mv_lambda": lam,
        "lambda_ready_for_build": lam is not None,
    }


def build_robust_scenario_prerequisites_disclosure(
    *,
    project_root: Path,
    output_dir_final: str,
) -> dict[str, Any]:
    """
    Main-folder shared stress/scenario inputs (not per-candidate stress calibration).
    """
    final_dir = project_root / output_dir_final
    artifacts: dict[str, Any] = {}
    for name in ROBUST_SCENARIO_PREREQUISITES:
        rel = f"{output_dir_final}/{name}".replace("\\", "/")
        path = final_dir / name
        artifacts[name] = {
            "relative_path": rel,
            "present": path.is_file(),
        }
    prerequisites_met = all(a["present"] for a in artifacts.values())
    missing = [n for n, a in artifacts.items() if not a["present"]]
    return {
        "kind": "robust_scenario_main_prerequisites",
        "shared_calibration_scope": "main_output_dir_final",
        "shared_calibration_note": (
            "Scenario library and stress_report are produced by the Main/policy report path "
            "(run_report.py / run_optimization.py), not by the candidate folder. "
            "robust_scenario reuses this calibration; per-candidate stress_report.json "
            "after build is a separate diagnostic for that portfolio only."
        ),
        "output_dir_final": output_dir_final.replace("\\", "/"),
        "prerequisite_artifacts": artifacts,
        "prerequisites_met": prerequisites_met,
        "missing_artifacts": missing,
        "recommended_before_factory": (
            "python run_report.py (after policy weights exist) or "
            "python run_optimization.py (includes report when reporting enabled)"
        ),
    }


def build_robust_paths_disclosure(
    *,
    candidate_id: str,
    project_root: Path,
    output_dir_final: str,
    baseline_metadata: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Aggregate disclosure for factory steps and comparison rows."""
    if candidate_id in ROBUST_MV_CANDIDATE_IDS:
        disc = build_robust_mv_lambda_disclosure(project_root=project_root)
        if baseline_metadata and baseline_metadata.get("robust_mv_lambda") is not None:
            disc["robust_mv_lambda_from_baseline_metadata"] = baseline_metadata[
                "robust_mv_lambda"
            ]
        return disc
    if candidate_id == ROBUST_SCENARIO_CANDIDATE_ID:
        return build_robust_scenario_prerequisites_disclosure(
            project_root=project_root,
            output_dir_final=output_dir_final,
        )
    return None


def merge_robust_paths_into_step(
    step: dict[str, Any],
    *,
    candidate_id: str,
    project_root: Path,
    output_dir_final: str,
    baseline_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    disc = build_robust_paths_disclosure(
        candidate_id=candidate_id,
        project_root=project_root,
        output_dir_final=output_dir_final,
        baseline_metadata=baseline_metadata,
    )
    if disc is not None:
        step["robust_paths_disclosure"] = disc
    return step
