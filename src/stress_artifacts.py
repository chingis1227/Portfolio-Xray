"""
Stress artifact path helpers for portfolio-first consumers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ANALYSIS_SUBJECT_SUBDIR = "analysis_subject"
BASELINE_PRIORITY_CANDIDATE_IDS = frozenset({"analysis_subject", "current"})


def _candidate_folder(candidate: dict[str, Any], *, project_root: Path) -> Path | None:
    root = candidate.get("artifact_root")
    if not root:
        return None
    folder = Path(str(root))
    if folder.is_absolute():
        return folder
    return project_root / str(root).replace("\\", "/")


def _analysis_subject_folder(*, project_root: Path, output_dir_final: str | Path) -> Path:
    output_dir_final = project_root / str(output_dir_final)
    return output_dir_final / ANALYSIS_SUBJECT_SUBDIR


def resolve_candidate_stress_report_path(
    candidate: dict[str, Any],
    *,
    project_root: Path,
    output_dir_final: str | Path | None,
) -> Path | None:
    """
    Resolve stress_report path with portfolio-first priority for baseline contexts.

    Priority:
    1) analysis_subject/stress_report.json for baseline candidates (analysis_subject/current)
    2) candidate artifact_root/stress_report.json
    3) analysis_subject/stress_report.json as fallback if candidate report is missing
    """
    subject_report = None
    if output_dir_final:
        subject_report = _analysis_subject_folder(
            project_root=project_root,
            output_dir_final=output_dir_final,
        ) / "stress_report.json"
    candidate_report = None
    folder = _candidate_folder(candidate, project_root=project_root)
    if folder is not None:
        candidate_report = folder / "stress_report.json"

    candidate_id = str(candidate.get("candidate_id") or "")
    if (
        candidate_id in BASELINE_PRIORITY_CANDIDATE_IDS
        and subject_report is not None
        and subject_report.is_file()
    ):
        return subject_report
    if candidate_report is not None and candidate_report.is_file():
        return candidate_report
    if subject_report is not None and subject_report.is_file():
        return subject_report
    return None


def resolve_analysis_subject_stress_report_path(
    *,
    project_root: Path,
    output_dir_final: str | Path | None,
) -> Path | None:
    if not output_dir_final:
        return None
    path = _analysis_subject_folder(
        project_root=project_root,
        output_dir_final=output_dir_final,
    ) / "stress_report.json"
    if path.is_file():
        return path
    return None

