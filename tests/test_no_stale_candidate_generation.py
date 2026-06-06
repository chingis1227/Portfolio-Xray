from __future__ import annotations

from pathlib import Path

import pytest

from src.candidate_comparison import write_block8_current_vs_candidate_only_outputs


class _Cfg:
    output_dir_final: str

    def __init__(self, output_dir_final: str) -> None:
        self.output_dir_final = output_dir_final


def test_block8_rejects_not_authoritative_candidate_generation(tmp_path: Path) -> None:
    output_dir = tmp_path / "Main portfolio"
    output_dir.mkdir()
    cfg = _Cfg("Main portfolio")
    stale_candidate_generation = {
        "schema_version": "candidate_generation_v1",
        "tombstone": "no_candidate_v1",
        "artifact_status": "not_authoritative",
        "candidate": {"candidate_id": "equal_weight"},
        "handoff_to_comparison": {"can_compare": True, "candidate_id": "equal_weight"},
    }

    with pytest.raises(ValueError, match="candidate_generation_not_authoritative"):
        write_block8_current_vs_candidate_only_outputs(
            cfg,  # type: ignore[arg-type]
            project_root=tmp_path,
            candidate_generation=stale_candidate_generation,
        )


def test_block8_rejects_inactive_candidate_generation(tmp_path: Path) -> None:
    output_dir = tmp_path / "Main portfolio"
    output_dir.mkdir()
    cfg = _Cfg("Main portfolio")
    inactive_candidate_generation = {
        "schema_version": "candidate_generation_v1",
        "candidate": {"candidate_id": "equal_weight"},
        "handoff_to_comparison": {"can_compare": True, "candidate_id": "equal_weight"},
        "product_run": {"run_id": "old", "active": False},
    }

    with pytest.raises(ValueError, match="candidate_generation_not_active"):
        write_block8_current_vs_candidate_only_outputs(
            cfg,  # type: ignore[arg-type]
            project_root=tmp_path,
            candidate_generation=inactive_candidate_generation,
        )
