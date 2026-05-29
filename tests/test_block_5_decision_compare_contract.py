"""Block 5 Decision compare — Current vs Candidate + Decision Verdict contracts."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.core_mvp_validation_contract import (
    block_5_compare_handoff_violations,
    check_block_5_compare_handoff,
    check_current_vs_candidate_v1,
    check_decision_verdict_v1,
    current_vs_candidate_v1_product_contract_violations,
    decision_verdict_v1_product_contract_violations,
)
from src.candidate_comparison import write_candidate_comparison_outputs
from src.config_schema import validate_config
from src.current_vs_candidate import build_current_vs_candidate
from src.decision_verdict import build_decision_verdict
from src.live_core_e2e import (
    LIVE_CORE_E2E_PROFILE_PRODUCT_ONE_CANDIDATE,
    detect_live_core_e2e_profile,
    validate_live_core_artifacts,
)
from mvp_offline_fixtures import (
    five_ticker_mvp_config_dict,
    seed_analysis_subject_diagnosis_bundle,
    seed_blocks_1_5_mvp_smoke_workspace,
)


def _comparison() -> dict:
    return {
        "schema_version": "candidate_comparison_v1",
        "comparison_baseline_candidate_id": "analysis_subject",
        "analysis_end": "2026-04-30",
        "primary_window": "10y",
        "product_candidate_scope": {
            "scope_type": "explicit_candidates",
            "candidate_ids": ["equal_weight"],
            "baseline_candidate_id": "analysis_subject",
            "excludes_unselected_candidates": True,
        },
        "candidates": [
            {
                "candidate_id": "analysis_subject",
                "display_name": "Analysis Subject",
                "role": "analysis_subject",
                "status": "available",
                "artifact_root": "analysis_subject",
                "metrics": {"10y": {"cagr": 0.07, "vol_annual": 0.12, "max_drawdown": -0.25, "sharpe": 0.5}},
                "drawdown": {"max_drawdown": -0.25},
                "stress": {"scenarios": [{"portfolio_pnl_pct": -0.18}]},
                "construction_disclosure": {"disclosure_status": "available"},
                "missing_fields": [],
                "warnings": [],
                "source_files": ["snapshot_10y.json"],
            },
            {
                "candidate_id": "equal_weight",
                "display_name": "Equal Weight",
                "role": "benchmark",
                "status": "available",
                "artifact_root": "equal-weight portfolio",
                "metrics": {"10y": {"cagr": 0.075, "vol_annual": 0.10, "max_drawdown": -0.18, "sharpe": 0.55}},
                "drawdown": {"max_drawdown": -0.18},
                "stress": {"scenarios": [{"portfolio_pnl_pct": -0.12}]},
                "construction_disclosure": {"disclosure_status": "available"},
                "missing_fields": [],
                "warnings": [],
                "source_files": ["snapshot_10y.json"],
            },
        ],
    }


def test_current_vs_candidate_contract_accepts_one_candidate_view() -> None:
    comparison = _comparison()
    cvc = build_current_vs_candidate(
        comparison,
        selection={"favored_candidate_id": "equal_weight"},
        candidate_ids=["equal_weight"],
    )
    assert not current_vs_candidate_v1_product_contract_violations(cvc)
    checks = check_current_vs_candidate_v1(cvc)
    assert checks["product_contract_ok"] is True
    assert checks["view_mode"] == "one_candidate"


def test_decision_verdict_contract_accepts_core_compare() -> None:
    cvc = build_current_vs_candidate(_comparison(), candidate_ids=["equal_weight"])
    verdict = build_decision_verdict(
        selection={
            "decision_status": "no_material_rebalance",
            "baseline_candidate_id": "analysis_subject",
            "favored_candidate_id": "equal_weight",
            "no_trade": {"evaluated": True},
            "warnings": [],
        },
        current_vs_candidate=cvc,
    )
    assert not decision_verdict_v1_product_contract_violations(verdict)
    checks = check_decision_verdict_v1(verdict)
    assert checks["product_contract_ok"] is True
    assert checks["verdict_id"] == "no_material_rebalance_recommended"
    assert checks["verdict_family"] == "core_compare"


def test_block_5_handoff_links_comparison_cvc_verdict() -> None:
    comparison = _comparison()
    cvc = build_current_vs_candidate(comparison, candidate_ids=["equal_weight"])
    verdict = build_decision_verdict(
        selection={
            "decision_status": "selected_candidate",
            "baseline_candidate_id": "analysis_subject",
            "favored_candidate_id": "equal_weight",
            "warnings": [],
        },
        current_vs_candidate=cvc,
    )
    assert not block_5_compare_handoff_violations(comparison, cvc, verdict)
    handoff = check_block_5_compare_handoff(comparison, cvc, verdict)
    assert handoff["handoff_ok"] is True


def test_live_e2e_product_one_candidate_validates_block_5(tmp_path: Path) -> None:
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

    for folder in ("equal-weight portfolio",):
        snap_dir = tmp_path / folder
        snap_dir.mkdir(parents=True, exist_ok=True)
        with open(snap_dir / "snapshot_10y.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "analysis_end": "2026-04-30",
                    "metrics": {"cagr": 0.075, "vol_annual": 0.10, "max_drawdown": -0.16},
                },
                f,
            )

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
    assert result.evidence.get("block_5_view_mode") == "one_candidate"
    assert result.evidence.get("block_5_verdict_id") is not None


def test_live_e2e_fails_block_5_when_verdict_schema_wrong(tmp_path: Path) -> None:
    cfg = validate_config(five_ticker_mvp_config_dict())
    main = tmp_path / cfg.output_dir_final
    seed_blocks_1_5_mvp_smoke_workspace(tmp_path, cfg)
    seed_analysis_subject_diagnosis_bundle(main / "analysis_subject")

    factory_run = {
        "schema_version": "candidate_factory_run_v1",
        "factory_profile_id": "explicit_list",
        "generated_at": "2026-05-29T12:00:00+00:00",
        "steps": [{"candidate_id": "equal_weight", "execution_action": "succeeded"}],
    }
    with open(main / "candidate_factory_run.json", "w", encoding="utf-8") as f:
        json.dump(factory_run, f)
    paths = write_candidate_comparison_outputs(
        cfg,
        project_root=tmp_path,
        factory_run=factory_run,
        write_txt=False,
    )
    verdict_path = paths.get("decision_verdict_json") or main / "decision_verdict.json"
    verdict = json.loads(verdict_path.read_text(encoding="utf-8"))
    verdict["schema_version"] = "decision_verdict_v0"
    with open(verdict_path, "w", encoding="utf-8") as f:
        json.dump(verdict, f, indent=2)

    result = validate_live_core_artifacts(main, profile=LIVE_CORE_E2E_PROFILE_PRODUCT_ONE_CANDIDATE)
    assert not result.ok
    assert any("decision_verdict_v1" in err for err in result.errors)
