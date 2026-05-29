"""Contract tests for Block 2.4 UI Pareto presenter."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.block_2_4_hidden_exposure import ALERT_IDS
from src.block_2_4_hidden_exposure_ui import (
    PARETO_VERSION,
    build_hidden_risk_cards_pareto,
)

GOLDEN = Path(__file__).resolve().parent / "fixtures" / "portfolio_xray_golden_v2.json"


@pytest.fixture(scope="module")
def golden_block_2_4() -> dict:
    data = json.loads(GOLDEN.read_text(encoding="utf-8"))
    block = data.get("block_2_4_hidden_exposure")
    assert isinstance(block, dict)
    return block


def test_build_pareto_from_golden(golden_block_2_4: dict) -> None:
    pareto = build_hidden_risk_cards_pareto(golden_block_2_4)
    assert pareto["version"] == PARETO_VERSION
    assert pareto["section_title"] == "Hidden exposure"
    assert len(pareto["all_cards"]) == len(ALERT_IDS)
    assert len(pareto["top_cards"]) <= 3
    for card in pareto["all_cards"]:
        assert card["card_id"] in ALERT_IDS
        assert card["card_title"]
        assert card["risk_level"] in {"low", "medium", "high", "unavailable"}
        assert card["short_diagnosis"]
        assert isinstance(card["key_evidence"], list)
        assert len(card["key_evidence"]) <= 5
        assert isinstance(card["linked_assets"], list)
        assert len(card["linked_assets"]) <= 3
        assert isinstance(card["next_tests"], list)
        assert len(card["next_tests"]) <= 3


def test_unavailable_card_uses_not_enough_data_label() -> None:
    block = {
        "summary": "partial",
        "status": "partial",
        "alerts": {
            alert_id: {
                "status": "Unavailable",
                "score": None,
                "evidence": [],
                "contributing_assets": [],
                "next_tests": [],
                "insufficient_evidence_reasons": ["Missing factor panel."],
            }
            for alert_id in ALERT_IDS
        },
        "top_hidden_risks": [],
    }
    pareto = build_hidden_risk_cards_pareto(block)
    for card in pareto["all_cards"]:
        assert card["risk_level"] == "unavailable"
        assert card["risk_level_label"] == "Not enough data"
        assert card["linked_assets"] == []


def test_empty_input_returns_empty_pareto() -> None:
    pareto = build_hidden_risk_cards_pareto(None)
    assert pareto["top_cards"] == []
    assert pareto["all_cards"] == []
