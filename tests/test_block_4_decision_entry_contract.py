"""Block 4 Decision entry — Problem Classification + Candidate Launchpad contracts."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.core_mvp_validation_contract import (
    block_4_diagnosis_handoff_violations,
    candidate_launchpad_v1_product_contract_violations,
    check_block_4_diagnosis_handoff,
    check_candidate_launchpad_v1,
    check_problem_classification_v1,
    problem_classification_v1_product_contract_violations,
)
from src.candidate_launchpad import build_candidate_launchpad, write_candidate_launchpad_outputs
from src.config_schema import validate_config
from src.live_core_e2e import (
    LIVE_CORE_E2E_PROFILE_DIAGNOSIS_ONLY,
    detect_live_core_e2e_profile,
    validate_live_core_artifacts,
)
from src.problem_classification import build_problem_classification, write_problem_classification_outputs
from src.product_bundle_hygiene import apply_diagnosis_only_product_bundle_hygiene
from mvp_offline_fixtures import (
    five_ticker_mvp_config_dict,
    seed_analysis_subject_diagnosis_bundle,
    seed_blocks_1_5_mvp_smoke_workspace,
)


def _minimal_problem_row(*, problem_id: str = "high_volatility") -> dict:
    return {
        "problem_id": problem_id,
        "label": "High volatility",
        "severity": "high",
        "confidence": "medium",
        "evidence": [{"source_artifact": "portfolio_xray.json", "summary": "test"}],
        "reasonable_paths_to_test": ["Reduce volatility"],
    }


def test_problem_classification_contract_accepts_valid_doc() -> None:
    doc = build_problem_classification(
        portfolio_xray={"sections": {}, "block_2_6_portfolio_weakness_map": {"risk_types": []}},
        stress_report={"stress_conclusions": {"overall_confidence": "medium"}},
        analysis_end="2026-04-30",
    )
    assert not problem_classification_v1_product_contract_violations(doc)
    checks = check_problem_classification_v1(doc)
    assert checks["product_contract_ok"] is True
    assert checks["n_problems"] >= 1


def test_problem_classification_contract_rejects_too_many_problems() -> None:
    doc = {
        "schema_version": "problem_classification_v1",
        "diagnostic_only": True,
        "problems": [_minimal_problem_row(problem_id="high_volatility") for _ in range(4)],
        "summary": {
            "n_problems": 4,
            "primary_problem_id": "high_volatility",
            "current_portfolio_acceptable": False,
        },
    }
    violations = problem_classification_v1_product_contract_violations(doc)
    assert any("at most 3 problems" in row for row in violations)


def test_launchpad_contract_rejects_weights_on_card() -> None:
    doc = {
        "schema_version": "candidate_launchpad_v1",
        "diagnostic_only": True,
        "cards": [
            {
                "card_id": "launchpad_01_reduce_volatility",
                "goal": "Reduce volatility",
                "description": "Test",
                "source_problem_id": "high_volatility",
                "source_problem_label": "High volatility",
                "rationale": {"severity": "high", "confidence": "medium", "evidence": []},
                "suggested_methods": [{"candidate_method_id": "equal_weight"}],
                "generates_portfolio": False,
                "requires_user_action": True,
                "weights": {"VOO": 1.0},
            }
        ],
        "summary": {
            "n_cards": 1,
            "primary_card_id": "launchpad_01_reduce_volatility",
            "has_portfolio_generating_options": True,
            "has_keep_current_option": False,
        },
    }
    violations = candidate_launchpad_v1_product_contract_violations(doc)
    assert any("must not include weights" in row for row in violations)


def test_block_4_handoff_links_launchpad_to_problem_classification(tmp_path: Path) -> None:
    pc_path = write_problem_classification_outputs(
        output_dir=tmp_path,
        portfolio_xray={"sections": {}},
        stress_report={},
        analysis_end="2026-04-30",
    )
    pc = json.loads(pc_path.read_text(encoding="utf-8"))
    lp_path = write_candidate_launchpad_outputs(
        output_dir=tmp_path,
        problem_classification=pc,
        analysis_end="2026-04-30",
    )
    lp = json.loads(lp_path.read_text(encoding="utf-8"))
    assert not block_4_diagnosis_handoff_violations(pc, lp)
    handoff = check_block_4_diagnosis_handoff(pc, lp)
    assert handoff["handoff_ok"] is True


def test_live_e2e_diagnosis_only_validates_block_4_contract(tmp_path: Path) -> None:
    cfg = validate_config(five_ticker_mvp_config_dict())
    seed_blocks_1_5_mvp_smoke_workspace(tmp_path, cfg)
    main = tmp_path / cfg.output_dir_final
    subject = main / "analysis_subject"
    seed_analysis_subject_diagnosis_bundle(subject)
    apply_diagnosis_only_product_bundle_hygiene(
        main,
        analysis_end="2026-04-30",
        investor_currency="USD",
    )

    assert detect_live_core_e2e_profile(main) == LIVE_CORE_E2E_PROFILE_DIAGNOSIS_ONLY
    result = validate_live_core_artifacts(main)
    assert result.ok, "\n".join(result.messages())
    assert result.evidence.get("block_4_n_problems", 0) >= 1
    assert result.evidence.get("block_4_n_cards", 0) >= 1


def test_live_e2e_fails_block_4_when_launchpad_contract_broken(tmp_path: Path) -> None:
    cfg = validate_config(five_ticker_mvp_config_dict())
    seed_blocks_1_5_mvp_smoke_workspace(tmp_path, cfg)
    main = tmp_path / cfg.output_dir_final
    subject = main / "analysis_subject"
    seed_analysis_subject_diagnosis_bundle(subject)

    lp_path = subject / "candidate_launchpad.json"
    lp = json.loads(lp_path.read_text(encoding="utf-8"))
    lp["schema_version"] = "candidate_launchpad_v0"
    with open(lp_path, "w", encoding="utf-8") as f:
        json.dump(lp, f, indent=2)

    apply_diagnosis_only_product_bundle_hygiene(
        main,
        analysis_end="2026-04-30",
        investor_currency="USD",
    )
    result = validate_live_core_artifacts(main, profile=LIVE_CORE_E2E_PROFILE_DIAGNOSIS_ONLY)
    assert not result.ok
    assert any("candidate_launchpad_v1" in err for err in result.errors)
