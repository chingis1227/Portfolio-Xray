"""Offline unit tests for live core E2E artifact validation (RM-1021)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.candidate_comparison import write_candidate_comparison_outputs
from src.config_schema import validate_config
from src.live_core_e2e import validate_live_core_artifacts
from mvp_offline_fixtures import five_ticker_mvp_config_dict, seed_blocks_1_5_mvp_smoke_workspace


def test_validate_live_core_artifacts_accepts_seeded_core_workspace(
    tmp_path: Path,
) -> None:
    cfg = validate_config(five_ticker_mvp_config_dict())
    seed_blocks_1_5_mvp_smoke_workspace(tmp_path, cfg)
    write_candidate_comparison_outputs(cfg, project_root=tmp_path)
    main = tmp_path / cfg.output_dir_final
    result = validate_live_core_artifacts(main)
    assert result.ok, "\n".join(result.messages())
    assert result.evidence["review_mode"] == "core"
    assert result.evidence["factory_profile_id"] == "core_v1"
