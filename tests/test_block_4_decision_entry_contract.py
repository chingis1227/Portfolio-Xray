"""Block 4 Decision entry — Problem Classification + Candidate Launchpad v2 contracts."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.core_mvp_validation_contract import (
    CANDIDATE_LAUNCHPAD_V2_VERSION,
    PROBLEM_CLASSIFICATION_V2_VERSION,
    block_4_v2_diagnosis_handoff_violations,
    candidate_launchpad_v2_product_contract_violations,
    check_block_4_v2_diagnosis_handoff,
    check_candidate_launchpad_v2,
    check_problem_classification_v2,
    problem_classification_v2_product_contract_violations,
)
from src.block_4.diagnosis_builder import build_block_4_diagnosis, write_block_4_diagnosis_outputs
from src.config_schema import validate_config
from src.live_core_e2e import (
    LIVE_CORE_E2E_PROFILE_DIAGNOSIS_ONLY,
    detect_live_core_e2e_profile,
    validate_live_core_artifacts,
)
from src.product_bundle_hygiene import apply_diagnosis_only_product_bundle_hygiene
from mvp_offline_fixtures import (
    five_ticker_mvp_config_dict,
    seed_analysis_subject_diagnosis_bundle,
    seed_blocks_1_5_mvp_smoke_workspace,
)


def test_problem_classification_v2_contract_accepts_facade_output() -> None:
    diagnosis = build_block_4_diagnosis(
        portfolio_xray={"block_2_6_portfolio_weakness_map": {"risk_types": []}},
        stress_report={"stress_conclusions": {"overall_confidence": "medium"}},
        analysis_end="2026-04-30",
    )
    doc = diagnosis.problem_classification
    assert doc["schema_version"] == PROBLEM_CLASSIFICATION_V2_VERSION
    assert not problem_classification_v2_product_contract_violations(doc)
    checks = check_problem_classification_v2(doc)
    assert checks["product_contract_ok"] is True
    assert checks["primary_problem_id"]


def test_problem_classification_v2_rejects_v1_schema() -> None:
    violations = problem_classification_v2_product_contract_violations(
        {"schema_version": "problem_classification_v1", "diagnostic_only": True}
    )
    assert any("schema_version expected" in row for row in violations)


def test_launchpad_v2_contract_rejects_weights_on_card() -> None:
    doc = {
        "schema_version": CANDIDATE_LAUNCHPAD_V2_VERSION,
        "diagnostic_only": True,
        "ruleset_version": "block_4_v2_2026_06",
        "launchpad_outcome": "proceed_to_launchpad",
        "cards": [
            {
                "card_id": "launchpad_01_reduce_volatility",
                "title": "Reduce volatility",
                "goal": "Reduce volatility",
                "description": "Test",
                "why_this_path_en": "Volatility is elevated.",
                "what_this_tests_en": "Minimum variance candidate.",
                "expected_tradeoff_to_check_en": "Return vs vol trade-off.",
                "when_to_skip_this_test_en": "If monitor outcome applies.",
                "not_a_recommendation_disclaimer_en": (
                    "This card suggests a hypothesis to test, not a buy or sell instruction."
                ),
                "priority_rank": 1,
                "source_problem_id": "high_volatility",
                "suggested_methods": [{"candidate_method_id": "equal_weight"}],
                "default_method": "equal_weight",
                "simple_constraints": [],
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
            "launchpad_outcome": "proceed_to_launchpad",
        },
    }
    violations = candidate_launchpad_v2_product_contract_violations(doc)
    assert any("must not include weights" in row for row in violations)


def test_block_4_v2_handoff_links_launchpad_to_problem_classification(tmp_path: Path) -> None:
    write_block_4_diagnosis_outputs(
        output_dir=tmp_path,
        portfolio_xray={"block_2_6_portfolio_weakness_map": {"risk_types": []}},
        stress_report={"stress_conclusions": {"overall_confidence": "medium"}},
        analysis_end="2026-04-30",
    )
    pc = json.loads((tmp_path / "problem_classification.json").read_text(encoding="utf-8"))
    lp = json.loads((tmp_path / "candidate_launchpad.json").read_text(encoding="utf-8"))
    assert not block_4_v2_diagnosis_handoff_violations(pc, lp)
    handoff = check_block_4_v2_diagnosis_handoff(pc, lp)
    assert handoff["handoff_ok"] is True


def test_live_e2e_diagnosis_only_validates_block_4_v2_contract(tmp_path: Path) -> None:
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
    assert result.evidence.get("block_4_schema_version") == PROBLEM_CLASSIFICATION_V2_VERSION
    assert result.evidence.get("block_4_primary_problem_id")
    assert result.evidence.get("block_4_n_cards", 0) >= 0


def test_live_e2e_fails_block_4_when_launchpad_v2_contract_broken(tmp_path: Path) -> None:
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
    assert any("candidate_launchpad_v2" in err for err in result.errors)
