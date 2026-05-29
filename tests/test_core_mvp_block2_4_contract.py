from __future__ import annotations

from typing import Any

import portfolio_xray_golden_inputs as golden_inputs
from scripts.core_mvp_validation_contract import (
    assert_block_2_4_product_contract,
    block_2_4_product_contract_violations,
    check_block_2_4_hidden_exposure,
    core_mvp_block2_block_status,
)
from src.block_2_4_hidden_exposure import ALERT_IDS, RULE_VERSION


def _minimal_valid_block() -> dict[str, Any]:
    block = golden_inputs.build_golden_document()["block_2_4_hidden_exposure"]
    assert_block_2_4_product_contract(block)
    return block


def test_golden_fixture_passes_block_2_4_core_mvp_contract() -> None:
    block = golden_inputs.build_golden_document()["block_2_4_hidden_exposure"]
    assert not block_2_4_product_contract_violations(block)
    checks = check_block_2_4_hidden_exposure(block)
    assert checks["institutional_v2_surface_ok"] is True
    assert checks["stress_boundary_ok"] is True
    assert checks["ruleset"] == RULE_VERSION
    assert checks["alert_count"] == len(ALERT_IDS)


def test_block_2_4_contract_detects_missing_heuristic_v2_ruleset() -> None:
    block = _minimal_valid_block()
    block["diagnostics_meta"]["ruleset"] = "heuristic_v1"
    violations = block_2_4_product_contract_violations(block)
    assert any("ruleset" in row for row in violations)


def test_block_2_4_contract_detects_missing_alert_field() -> None:
    block = _minimal_valid_block()
    del block["alerts"]["tail_risk"]["limitations"]
    violations = block_2_4_product_contract_violations(block)
    assert any("tail_risk" in row and "limitations" in row for row in violations)


def test_block_2_4_contract_detects_forbidden_embedded_stress_key() -> None:
    block = _minimal_valid_block()
    block["stress_results_v1"] = {"status": "ok"}
    violations = block_2_4_product_contract_violations(block)
    assert any("forbidden embedded stress key" in row for row in violations)
    checks = check_block_2_4_hidden_exposure(block)
    assert checks["stress_boundary_ok"] is False


def test_core_mvp_block_status_partial_when_block_2_4_contract_violated() -> None:
    block = _minimal_valid_block()
    block["block"] = "wrong_id"
    status = core_mvp_block2_block_status(
        block,
        "block_2_4_hidden_exposure",
        missing_fields=[],
        warnings=[],
    )
    assert status == "partial"


def test_core_mvp_block_status_ok_for_valid_block_2_4() -> None:
    block = _minimal_valid_block()
    status = core_mvp_block2_block_status(
        block,
        "block_2_4_hidden_exposure",
        missing_fields=[],
        warnings=[],
    )
    assert status == "ok"


def test_validate_script_helper_reports_block_id() -> None:
    block = _minimal_valid_block()
    checks = check_block_2_4_hidden_exposure(block)
    assert checks["blocked_upstream_registry_count"] > 0
    assert checks["does_not_run_stress_lab"] is True
