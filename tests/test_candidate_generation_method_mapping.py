from __future__ import annotations

import pytest

from src.candidate_generation import (
    UNCAPPED_MODE_CONCENTRATION_WARNING,
    build_candidate_generation_document,
)
from src.portfolio_alternatives_builder import (
    builder_prefill_to_candidate_setup,
    launchpad_card_to_builder_prefill,
)


def _launchpad_card(method: str) -> dict[str, object]:
    return {
        "card_id": f"launchpad_01_{method}",
        "goal": "Improve crisis resilience",
        "source_problem_id": "weak_crisis_resilience",
        "source_diagnosis_id": "weak_crisis_resilience",
        "hypothesis_to_test": "Test whether the selected method improves the diagnosis.",
        "default_method": method,
        "suggested_methods": [{"candidate_method_id": method, "method_role": "targeted_hypothesis"}],
        "success_criteria": ["Improve the diagnosed weakness."],
        "tradeoff_to_watch": "Risk improvement versus concentration and turnover.",
        "when_to_skip": "Skip if diagnosis no longer applies.",
        "card_type": "targeted_hypothesis_test",
        "launch_status": "hypothesis_test",
        "is_rebalance_recommendation": False,
        "decision_boundary": "This is not a rebalance recommendation.",
    }


def _candidate_setup(method: str, *, mode: str = "capped") -> dict[str, object]:
    prefill = launchpad_card_to_builder_prefill(_launchpad_card(method))
    edits: dict[str, object] = {}
    if mode == "uncapped":
        edits = {"mode": "uncapped", "constraint_preset": "uncapped"}
    setup = builder_prefill_to_candidate_setup(prefill, edits=edits or None)
    assert setup is not None
    return setup


@pytest.mark.parametrize(
    ("method", "mode", "expected_variant"),
    [
        ("equal_weight", "capped", "equal_weight"),
        ("risk_parity", "capped", "risk_parity"),
        ("hierarchical_risk_parity", "capped", "hierarchical_risk_parity"),
        ("minimum_variance", "capped", "minimum_variance"),
        ("minimum_variance", "uncapped", "minimum_variance_uncapped"),
        ("minimum_cvar", "capped", "minimum_cvar_constrained"),
        ("minimum_cvar", "uncapped", "minimum_cvar_uncapped"),
        ("maximum_diversification", "capped", "maximum_diversification"),
        ("maximum_diversification", "uncapped", "maximum_diversification_uncapped"),
    ],
)
def test_candidate_generation_maps_guided_method_and_mode_to_backend_variant(
    method: str,
    mode: str,
    expected_variant: str,
) -> None:
    document = build_candidate_generation_document(
        _candidate_setup(method, mode=mode),
        weights={"VOO": 1.0},
    )

    assert document["candidate"]["method"] == method
    assert document["candidate"]["method_variant"] == expected_variant
    assert document["method_availability"]["backend_candidate_id"] == expected_variant
    assert document["method_availability"]["available"] is True


def test_uncapped_candidate_generation_preserves_warning_and_null_cap() -> None:
    document = build_candidate_generation_document(
        _candidate_setup("minimum_cvar", mode="uncapped"),
        weights={"VOO": 1.0},
    )

    candidate = document["candidate"]
    assert candidate["method_variant"] == "minimum_cvar_uncapped"
    assert candidate["capped"] is False
    assert candidate["uncapped"] is True
    assert candidate["min_asset_weight"] == 0.0
    assert candidate["max_asset_weight"] is None
    assert candidate["constraint_preset"] == "uncapped"
    assert UNCAPPED_MODE_CONCENTRATION_WARNING in document["warnings"]
