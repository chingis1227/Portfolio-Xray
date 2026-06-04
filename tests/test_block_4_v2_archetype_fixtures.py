"""Block 4 v3 — ten portfolio archetype end-to-end fixtures (Session 11)."""

from __future__ import annotations

import pytest

from scripts.core_mvp_validation_contract import (
    block_4_v3_diagnosis_handoff_violations,
    candidate_launchpad_v3_product_contract_violations,
    check_block_4_v3_diagnosis_handoff,
    check_candidate_launchpad_v3,
    check_problem_classification_v3,
    problem_classification_v3_product_contract_violations,
)
from src.block_4.diagnosis_builder import (
    PROBLEM_CLASSIFICATION_V3_VERSION,
    build_block_4_diagnosis,
)
from src.block_4.no_trade_gate import OUTCOME_DO_NOT_ACT, OUTCOME_MONITOR, OUTCOME_PROCEED
from block_4_fixtures import (
    Block4ArchetypeCase,
    all_block_4_archetypes,
    archetype_by_id,
    load_archetype_manifest,
)

pytestmark = pytest.mark.block_4_v3


def _assert_archetype(case: Block4ArchetypeCase) -> None:
    result = build_block_4_diagnosis(
        portfolio_xray=case.portfolio_xray,
        stress_report=case.stress_report,
        analysis_end="2026-04-30",
        generated_at="2026-05-29T12:00:00Z",
    )
    pc = result.problem_classification
    lp = result.candidate_launchpad

    assert pc["schema_version"] == PROBLEM_CLASSIFICATION_V3_VERSION
    assert result.primary_problem_id in case.expected_primary_ids, (
        f"{case.archetype_id}: expected primary in {case.expected_primary_ids}, "
        f"got {result.primary_problem_id}"
    )
    assert result.gate.outcome in case.expected_outcomes, (
        f"{case.archetype_id}: expected outcome in {case.expected_outcomes}, "
        f"got {result.gate.outcome}"
    )

    secondary = pc.get("secondary_problems") or []
    assert len(secondary) <= 2

    primary = pc["primary_problem"]
    evidence_refs = primary.get("evidence_refs") or []
    assert evidence_refs
    for ref in evidence_refs:
        assert ref.get("source_block")
        assert ref.get("source_artifact") in {"portfolio_xray.json", "stress_report.json"}
        assert ref.get("evidence_path") in {"primary", "legacy_fallback", "pre_stress_only"}

    assert not problem_classification_v3_product_contract_violations(pc)
    assert not candidate_launchpad_v3_product_contract_violations(lp)
    assert not block_4_v3_diagnosis_handoff_violations(pc, lp)
    assert check_problem_classification_v3(pc)["product_contract_ok"] is True
    assert check_candidate_launchpad_v3(lp)["product_contract_ok"] is True
    assert check_block_4_v3_diagnosis_handoff(pc, lp)["handoff_ok"] is True

    assert pc["summary"]["no_trade_outcome"] == result.gate.outcome
    assert lp["launchpad_outcome"] == result.gate.outcome

    if case.launchpad_may_proceed:
        assert result.gate.outcome == OUTCOME_PROCEED
        assert result.gate.launchpad_suppressed is False
        cards = lp.get("cards") or []
        assert cards
        assert all(card.get("default_method") for card in cards)
    elif result.gate.outcome == OUTCOME_DO_NOT_ACT:
        assert result.gate.launchpad_suppressed is True
    elif result.gate.outcome == OUTCOME_MONITOR:
        assert result.gate.launchpad_suppressed is True


@pytest.mark.parametrize(
    "archetype_id",
    [case.archetype_id for case in all_block_4_archetypes()],
    ids=[case.archetype_id for case in all_block_4_archetypes()],
)
def test_block_4_archetype_end_to_end(archetype_id: str) -> None:
    _assert_archetype(archetype_by_id(archetype_id))


def test_archetype_manifest_lists_ten_cases() -> None:
    manifest = load_archetype_manifest()
    entries = manifest.get("archetypes") or []
    assert len(entries) == 10
    manifest_ids = {str(row["archetype_id"]) for row in entries}
    code_ids = {case.archetype_id for case in all_block_4_archetypes()}
    assert manifest_ids == code_ids


def test_weak_hedge_elevates_crisis_over_labeled_hedge() -> None:
    case = archetype_by_id("weak_hedge")
    result = build_block_4_diagnosis(
        portfolio_xray=case.portfolio_xray,
        stress_report=case.stress_report,
        analysis_end="2026-04-30",
    )
    rejected_ids = {
        row["problem_id"] for row in (result.problem_classification.get("rejected_problems") or [])
    }
    assert result.primary_problem_id == "weak_crisis_resilience"
    assert "weak_hedge_behavior" in rejected_ids


def test_concentrated_equity_rejects_benign_concentration_demotion() -> None:
    case = archetype_by_id("concentrated_equity")
    result = build_block_4_diagnosis(
        portfolio_xray=case.portfolio_xray,
        stress_report=case.stress_report,
        analysis_end="2026-04-30",
    )
    assert result.primary_problem_id == "high_concentration"
    assert result.gate.outcome == OUTCOME_PROCEED


def test_insufficient_and_conflict_suppress_launchpad() -> None:
    for archetype_id in ("insufficient_data", "conflicting_signals"):
        case = archetype_by_id(archetype_id)
        result = build_block_4_diagnosis(
            portfolio_xray=case.portfolio_xray,
            stress_report=case.stress_report,
            analysis_end="2026-04-30",
        )
        assert result.gate.outcome == OUTCOME_DO_NOT_ACT
        assert result.candidate_launchpad["launchpad_outcome"] == OUTCOME_DO_NOT_ACT


def test_acceptable_no_action_monitors_only() -> None:
    case = archetype_by_id("acceptable_no_action")
    result = build_block_4_diagnosis(
        portfolio_xray=case.portfolio_xray,
        stress_report=case.stress_report,
        analysis_end="2026-04-30",
    )
    assert result.primary_problem_id == "current_portfolio_acceptable"
    assert result.gate.outcome == OUTCOME_MONITOR
