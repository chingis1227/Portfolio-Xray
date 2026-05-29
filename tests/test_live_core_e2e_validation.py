"""Offline unit tests for live core E2E artifact validation (RM-1021 / Session 05 R5)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.candidate_comparison import write_candidate_comparison_outputs
from src.config_schema import validate_config
from src.current_portfolio_stress_scorecard_block import RULESET_VERSION as SCORECARD_RULESET_VERSION
from src.hedge_gap_analysis_block import RULESET_VERSION
from src.live_core_e2e import (
    LIVE_CORE_E2E_PROFILE_CORE_BLOCKS_1_3,
    LIVE_CORE_E2E_PROFILE_DIAGNOSIS_ONLY,
    LIVE_CORE_E2E_PROFILE_PRODUCT_ONE_CANDIDATE,
    LIVE_CORE_E2E_PROFILE_RESEARCH_BATCH_CORE_FAST,
    detect_live_core_e2e_profile,
    validate_live_core_artifacts,
)
from src.product_bundle_hygiene import (
    NO_CANDIDATE_TOMBSTONE,
    apply_core_blocks_product_bundle_hygiene,
    apply_diagnosis_only_product_bundle_hygiene,
)
from mvp_offline_fixtures import (
    five_ticker_mvp_config_dict,
    seed_blocks_1_5_mvp_smoke_workspace,
    seed_analysis_subject_diagnosis_bundle,
)


def test_validate_live_core_artifacts_accepts_seeded_core_workspace(
    tmp_path: Path,
) -> None:
    cfg = validate_config(five_ticker_mvp_config_dict())
    seed_blocks_1_5_mvp_smoke_workspace(tmp_path, cfg)
    write_candidate_comparison_outputs(cfg, project_root=tmp_path)
    main = tmp_path / cfg.output_dir_final
    assert detect_live_core_e2e_profile(main) == LIVE_CORE_E2E_PROFILE_RESEARCH_BATCH_CORE_FAST
    result = validate_live_core_artifacts(main)
    assert result.ok, "\n".join(result.messages())
    assert result.profile == LIVE_CORE_E2E_PROFILE_RESEARCH_BATCH_CORE_FAST
    assert result.evidence["review_mode"] == "core"
    assert result.evidence["factory_profile_id"] == "core_fast"
    assert result.evidence["hedge_gap_ruleset_version"] == RULESET_VERSION
    assert result.evidence["hedge_gap_block_status"] == "unavailable"
    assert result.evidence["block_3_4_ruleset_version"] == SCORECARD_RULESET_VERSION
    assert result.evidence["block_3_4_block_status"] in {"ok", "partial", "unavailable"}


def test_validate_core_blocks_profile_after_hygiene(tmp_path: Path) -> None:
    cfg = validate_config(five_ticker_mvp_config_dict())
    seed_blocks_1_5_mvp_smoke_workspace(tmp_path, cfg)
    main = tmp_path / cfg.output_dir_final
    subject = main / "analysis_subject"
    seed_analysis_subject_diagnosis_bundle(subject)
    apply_core_blocks_product_bundle_hygiene(main, subject_dir=subject)

    assert detect_live_core_e2e_profile(main) == LIVE_CORE_E2E_PROFILE_CORE_BLOCKS_1_3
    result = validate_live_core_artifacts(main)
    assert result.ok, "\n".join(result.messages())
    assert result.profile == LIVE_CORE_E2E_PROFILE_CORE_BLOCKS_1_3


def test_validate_diagnosis_only_profile_with_tombstones(tmp_path: Path) -> None:
    cfg = validate_config(five_ticker_mvp_config_dict())
    seed_blocks_1_5_mvp_smoke_workspace(tmp_path, cfg)
    main = tmp_path / cfg.output_dir_final
    subject = main / "analysis_subject"
    seed_analysis_subject_diagnosis_bundle(subject)
    (main / "candidate_factory_run.json").unlink()
    apply_diagnosis_only_product_bundle_hygiene(
        main,
        analysis_end="2026-04-30",
        investor_currency="USD",
    )

    assert detect_live_core_e2e_profile(main) == LIVE_CORE_E2E_PROFILE_DIAGNOSIS_ONLY
    result = validate_live_core_artifacts(main)
    assert result.ok, "\n".join(result.messages())
    assert result.profile == LIVE_CORE_E2E_PROFILE_DIAGNOSIS_ONLY

    with open(main / "candidate_comparison.json", encoding="utf-8") as f:
        comparison = json.load(f)
    assert comparison["tombstone"] == NO_CANDIDATE_TOMBSTONE


def test_validate_product_one_candidate_profile(tmp_path: Path) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO"],
            "analysis_subject": {"type": "current_portfolio", "weights": {"VOO": 1.0}},
        }
    )
    main = tmp_path / "Main portfolio"
    seed_blocks_1_5_mvp_smoke_workspace(tmp_path, cfg)
    seed_analysis_subject_diagnosis_bundle(main / "analysis_subject")

    for folder in ("equal-weight portfolio", "risk-parity portfolio"):
        snap_dir = tmp_path / folder
        snap_dir.mkdir(parents=True, exist_ok=True)
        snap_path = snap_dir / "snapshot_10y.json"
        if not snap_path.is_file():
            metrics = (
                {"cagr": 0.075, "vol_annual": 0.10, "max_drawdown": -0.16}
                if "equal" in folder
                else {"cagr": 0.09, "vol_annual": 0.08, "max_drawdown": -0.10}
            )
            with open(snap_path, "w", encoding="utf-8") as f:
                json.dump({"analysis_end": "2026-04-30", "metrics": metrics}, f)

    factory_run = {
        "schema_version": "candidate_factory_run_v1",
        "factory_profile_id": "explicit_list",
        "generated_at": "2026-05-29T12:00:00+00:00",
        "steps": [{"candidate_id": "equal_weight", "execution_action": "succeeded"}],
    }
    with open(main / "candidate_factory_run.json", "w", encoding="utf-8") as f:
        json.dump(factory_run, f)
    write_candidate_comparison_outputs(
        cfg,
        project_root=tmp_path,
        factory_run=factory_run,
        write_txt=False,
    )

    assert detect_live_core_e2e_profile(main) == LIVE_CORE_E2E_PROFILE_PRODUCT_ONE_CANDIDATE
    result = validate_live_core_artifacts(main)
    assert result.ok, "\n".join(result.messages())
    assert result.profile == LIVE_CORE_E2E_PROFILE_PRODUCT_ONE_CANDIDATE
    assert result.evidence["factory_profile_id"] == "explicit_list"
    assert result.evidence["product_candidate_ids"] == ["equal_weight"]
    assert result.evidence["comparison_candidate_count"] <= 3


def test_unknown_profile_raises() -> None:
    with pytest.raises(ValueError, match="Unknown live core E2E profile"):
        validate_live_core_artifacts(Path("."), profile="not_a_profile")
