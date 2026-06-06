from __future__ import annotations

from scripts.run_blocks_5_to_9_vertical_flow import select_demo_launchpad_card


def test_vertical_demo_falls_back_to_targeted_card_when_no_reference_exists() -> None:
    launchpad = {
        "cards": [
            {
                "card_id": "targeted_equal_weight",
                "source_diagnosis_id": "high_concentration",
                "card_type": "targeted_hypothesis_test",
                "goal": "Reduce concentration",
                "suggested_methods": [
                    {"candidate_method_id": "equal_weight", "method_role": "targeted_hypothesis"},
                    {"candidate_method_id": "risk_parity", "method_role": "targeted_hypothesis"},
                ],
            }
        ]
    }

    selected = select_demo_launchpad_card(launchpad)

    assert selected is not None
    assert selected["card_id"] == "targeted_equal_weight"
