"""Offline unit tests for live full E2E artifact validation (RM-1029)."""

from __future__ import annotations

from pathlib import Path

from src.candidate_comparison import write_candidate_comparison_outputs
from src.candidate_factory import DEFAULT_V1_CANDIDATE_ORDER
from src.config_schema import validate_config
from src.live_full_e2e import validate_live_full_artifacts
from mvp_offline_fixtures import (
    DEFAULT_ANALYSIS_END,
    five_ticker_mvp_config_dict,
    seed_blocks_1_5_mvp_smoke_workspace,
    write_json,
)


def _upgrade_workspace_to_full_menu(main: Path, config_fingerprint: str) -> None:
    factory_path = main / "candidate_factory_run.json"
    import json

    doc = json.loads(factory_path.read_text(encoding="utf-8"))
    steps = []
    for candidate_id in DEFAULT_V1_CANDIDATE_ORDER:
        steps.append(
            {
                "candidate_id": candidate_id,
                "status": "succeeded",
                "reason_code": None,
                "resume_from_manifest": False,
            }
        )
    doc["factory_profile_id"] = "default_v1"
    doc["steps"] = steps
    doc["summary"] = {
        "total": len(steps),
        "succeeded": len(steps),
        "failed": 0,
        "skipped_existing": 0,
        "skipped_dependency": 0,
        "resumed_from_manifest": 0,
    }
    write_json(factory_path, doc)
    write_json(
        main / "candidate_factory_manifest.json",
        {
            "schema_version": "candidate_factory_manifest_v1",
            "factory_profile_id": "default_v1",
            "analysis_end": DEFAULT_ANALYSIS_END,
            "config_fingerprint": config_fingerprint,
            "completed_steps": [
                {"candidate_id": cid, "status": "succeeded"} for cid in DEFAULT_V1_CANDIDATE_ORDER
            ],
        },
    )


def test_validate_live_full_artifacts_accepts_seeded_full_workspace(
    tmp_path: Path,
) -> None:
    cfg = validate_config(five_ticker_mvp_config_dict())
    seeded = seed_blocks_1_5_mvp_smoke_workspace(tmp_path, cfg)
    main = tmp_path / cfg.output_dir_final
    _upgrade_workspace_to_full_menu(main, seeded["config_fingerprint"])
    write_candidate_comparison_outputs(cfg, project_root=tmp_path)
    comparison_path = main / "candidate_comparison.json"
    import json

    comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
    menu = comparison.setdefault("candidate_menu", {})
    menu["review_mode"] = "full"
    menu["factory_profile_id"] = "default_v1"
    menu["is_partial_menu"] = False
    menu["factory_evidence_status"] = "current"
    write_json(comparison_path, comparison)

    result = validate_live_full_artifacts(main)
    assert result.ok, "\n".join(result.messages())
    assert result.evidence["review_mode"] == "full"
    assert result.evidence["factory_profile_id"] == "default_v1"
    assert result.evidence["factory_step_count"] == len(DEFAULT_V1_CANDIDATE_ORDER)


def test_validate_live_full_resume_expects_manifest(tmp_path: Path) -> None:
    cfg = validate_config(five_ticker_mvp_config_dict())
    seeded = seed_blocks_1_5_mvp_smoke_workspace(tmp_path, cfg)
    main = tmp_path / cfg.output_dir_final
    _upgrade_workspace_to_full_menu(main, seeded["config_fingerprint"])
    factory_path = main / "candidate_factory_run.json"
    import json

    doc = json.loads(factory_path.read_text(encoding="utf-8"))
    doc["options"]["resume"] = True
    doc["summary"]["resumed_from_manifest"] = 3
    write_json(factory_path, doc)
    write_candidate_comparison_outputs(cfg, project_root=tmp_path)
    comparison = json.loads((main / "candidate_comparison.json").read_text(encoding="utf-8"))
    comparison["candidate_menu"]["review_mode"] = "full"
    write_json(main / "candidate_comparison.json", comparison)

    result = validate_live_full_artifacts(main, expect_resume_evidence=True)
    assert result.ok, "\n".join(result.messages())
    assert result.evidence.get("factory_manifest_present") is True
