"""Block 2.6 — Stress Lab boundary tests (Session 08 heuristic_v2)."""
from __future__ import annotations

import inspect
import json
from typing import Any

import pytest

from src.block_2_6_portfolio_weakness_map import (
    FORBIDDEN_STRESS_KEYS,
    RISK_TYPES,
    build_block_2_6_portfolio_weakness_map,
)
from src.scenario_library import SYNTHETIC_SCENARIO_IDS

from test_block_2_6_portfolio_weakness_map import (
    _block_2_1,
    _block_2_2,
    _block_2_3,
    _block_2_4,
    _block_2_5,
)


def _collect_keys(obj: Any, *, keys: set[str]) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in FORBIDDEN_STRESS_KEYS:
                keys.add(key)
            _collect_keys(value, keys=keys)
    elif isinstance(obj, list):
        for item in obj:
            _collect_keys(item, keys=keys)


def test_module_does_not_import_stress() -> None:
    """Block 2.6 must stay isolated from src.stress (pre-stress adapter only)."""
    from src import block_2_6_portfolio_weakness_map as mod

    source = inspect.getsource(mod)
    assert "from src.stress" not in source
    assert "import src.stress" not in source


def test_canonical_risk_types_match_stress_lab_synthetic_ids() -> None:
    assert tuple(RISK_TYPES) == SYNTHETIC_SCENARIO_IDS
    assert len(RISK_TYPES) == 8


def test_product_block_serializes_without_forbidden_stress_keys() -> None:
    block = build_block_2_6_portfolio_weakness_map(
        _block_2_1(),
        _block_2_2(),
        _block_2_3(),
        _block_2_4(),
        _block_2_5(),
    )
    found: set[str] = set()
    _collect_keys(block, keys=found)
    assert not found

    serialized = json.dumps(block)
    for forbidden in FORBIDDEN_STRESS_KEYS:
        assert forbidden not in serialized


@pytest.mark.parametrize("forbidden_key", FORBIDDEN_STRESS_KEYS)
def test_upstream_forbidden_stress_keys_do_not_change_risk_scores(forbidden_key: str) -> None:
    """Injecting Stress Lab keys into upstream blocks must not alter scores (ignored by contract)."""
    clean = build_block_2_6_portfolio_weakness_map(
        _block_2_1(),
        _block_2_2(),
        _block_2_3(),
        _block_2_4(),
        _block_2_5(),
    )
    polluted_24 = _block_2_4()
    polluted_24[forbidden_key] = {"scenario_id": "equity_shock", "pnl": -0.12}
    polluted = build_block_2_6_portfolio_weakness_map(
        _block_2_1(),
        _block_2_2(),
        _block_2_3(),
        polluted_24,
        _block_2_5(),
    )

    clean_scores = {r["risk_type"]: r["score_0_100"] for r in clean["risk_types"]}
    polluted_scores = {r["risk_type"]: r["score_0_100"] for r in polluted["risk_types"]}
    assert clean_scores == polluted_scores
    assert forbidden_key in (polluted.get("metadata") or {}).get("forbidden_stress_keys_detected", [])
