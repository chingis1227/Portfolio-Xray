"""Smoke tests for Blocks 1–3 diagnostic journey view model."""

from __future__ import annotations

import json
from pathlib import Path

from diagnostic_journey.view_model import (
    _bridge_card_from_launchpad,
    _launchpad_method_ids,
    build_diagnostic_journey_view_model,
)
from mvp_offline_fixtures import (
    seed_analysis_subject_diagnosis_bundle,
    seed_blocks_1_5_mvp_smoke_workspace,
)
from src.config_schema import validate_config

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUBJECT = PROJECT_ROOT / "Main portfolio" / "analysis_subject"


def test_launchpad_method_ids_reads_v2_suggested_methods() -> None:
    card = {
        "suggested_methods": [{"candidate_method_id": "equal_weight"}],
        "default_method": "risk_parity",
    }
    assert _launchpad_method_ids(card) == ["risk_parity", "equal_weight"]


def test_bridge_card_from_launchpad_uses_v2_copy_fields() -> None:
    card = {
        "title": "Reduce drawdown risk",
        "goal": "Reduce drawdown",
        "description": "Test whether a lower-volatility mix improves worst-case loss.",
        "why_this_path_en": "Stress loss is material under the worst synthetic scenario.",
        "what_this_tests_en": "Minimum variance candidate vs current portfolio.",
        "suggested_methods": [{"candidate_method_id": "minimum_variance"}],
        "default_method": "minimum_variance",
    }
    bridge = _bridge_card_from_launchpad(card)
    assert bridge["title"] == "Reduce drawdown risk"
    assert "Stress loss" in bridge["why"]
    assert "Minimum variance" in bridge["suggested_test"]
    assert bridge["goal"]


def test_build_view_model_reads_block_4_v2_diagnosis(tmp_path: Path) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
            "analysis_subject": {"type": "current_portfolio", "weights": {"VOO": 0.6, "BND": 0.4}},
        }
    )
    main = tmp_path / "Main portfolio"
    subject = main / "analysis_subject"
    seed_blocks_1_5_mvp_smoke_workspace(tmp_path, cfg)
    seed_analysis_subject_diagnosis_bundle(subject)

    pc = json.loads((subject / "problem_classification.json").read_text(encoding="utf-8"))
    assert pc["schema_version"] == "problem_classification_v2"

    vm = build_diagnostic_journey_view_model(subject, project_root=tmp_path)
    diagnosis = vm["bridge"]["diagnosis"]
    assert diagnosis["schema_version"] == "problem_classification_v2"
    assert diagnosis.get("primary_headline")
    assert diagnosis.get("no_trade_outcome")
    if vm["bridge"]["cards"]:
        assert vm["bridge"]["cards"][0].get("why")


def test_build_view_model_from_live_subject_bundle():
    if not (SUBJECT / "portfolio_xray.json").is_file():
        return
    vm = build_diagnostic_journey_view_model(SUBJECT, project_root=PROJECT_ROOT)
    assert vm["has_data"] is True
    assert vm["has_xray"] is True
    assert vm["has_stress"] is True
    assert len(vm["block2_exec"]["findings"]) >= 5
    assert vm["block1"]["mode"] == "Current portfolio diagnosis"
    assert "pre-stress hypothesis" in vm["block2_weakness"]["pre_stress_note"].lower()
    assert "not recommendations" in vm["bridge"]["subtitle"].lower()
    assert "real_rates" not in vm["block2_exec"]["main_diagnosis"].lower()
    if (SUBJECT / "problem_classification.json").is_file():
        pc = json.loads((SUBJECT / "problem_classification.json").read_text(encoding="utf-8"))
        if pc.get("schema_version") == "problem_classification_v2":
            assert vm["bridge"]["diagnosis"].get("schema_version") == "problem_classification_v2"
            assert vm["bridge"]["diagnosis"].get("primary_headline")


def test_missing_bundle_is_safe():
    vm = build_diagnostic_journey_view_model(PROJECT_ROOT / "nonexistent_subject_dir")
    assert vm["has_data"] is False
