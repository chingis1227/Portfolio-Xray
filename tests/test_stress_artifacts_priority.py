from __future__ import annotations

from pathlib import Path

from src.stress_artifacts import (
    resolve_analysis_subject_stress_report_path,
    resolve_candidate_stress_report_path,
)


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}", encoding="utf-8")


def test_baseline_candidate_prefers_analysis_subject_report(tmp_path: Path) -> None:
    _touch(tmp_path / "Main portfolio" / "analysis_subject" / "stress_report.json")
    _touch(tmp_path / "Main portfolio" / "stress_report.json")

    candidate = {"candidate_id": "current", "artifact_root": "Main portfolio"}
    resolved = resolve_candidate_stress_report_path(
        candidate,
        project_root=tmp_path,
        output_dir_final="Main portfolio",
    )
    assert resolved == tmp_path / "Main portfolio" / "analysis_subject" / "stress_report.json"


def test_nonbaseline_candidate_uses_own_report_before_subject(tmp_path: Path) -> None:
    _touch(tmp_path / "Main portfolio" / "analysis_subject" / "stress_report.json")
    _touch(tmp_path / "risk parity portfolio" / "stress_report.json")

    candidate = {"candidate_id": "risk_parity", "artifact_root": "risk parity portfolio"}
    resolved = resolve_candidate_stress_report_path(
        candidate,
        project_root=tmp_path,
        output_dir_final="Main portfolio",
    )
    assert resolved == tmp_path / "risk parity portfolio" / "stress_report.json"


def test_subject_path_resolver_returns_none_when_absent(tmp_path: Path) -> None:
    resolved = resolve_analysis_subject_stress_report_path(
        project_root=tmp_path,
        output_dir_final="Main portfolio",
    )
    assert resolved is None

