from __future__ import annotations

from scripts.run_blocks_5_to_9_vertical_flow import select_demo_launchpad_card


def _method(method_id: str, *, role: str = "targeted_hypothesis") -> dict:
    return {"candidate_method_id": method_id, "method_role": role}


def test_default_vertical_demo_prefers_reference_equal_weight_card() -> None:
    launchpad = {
        "cards": [
            {
                "card_id": "targeted",
                "source_diagnosis_id": "weak_crisis_resilience",
                "card_type": "targeted_hypothesis_test",
                "suggested_methods": [_method("minimum_cvar")],
            },
            {
                "card_id": "reference",
                "source_diagnosis_id": "mixed_evidence_no_action",
                "card_type": "reference_benchmark_test",
                "launch_status": "reference_test",
                "goal": "Compare against simple references",
                "suggested_methods": [
                    _method("equal_weight", role="reference_benchmark"),
                    _method("risk_parity", role="reference_benchmark"),
                ],
            },
        ]
    }

    selected = select_demo_launchpad_card(launchpad)

    assert selected is not None
    assert selected["card_id"] == "reference"
