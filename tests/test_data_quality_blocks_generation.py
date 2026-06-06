from __future__ import annotations

import pytest

from scripts.run_blocks_5_to_9_vertical_flow import VerticalFlowError, build_selected_builder_document


def test_data_quality_launchpad_card_blocks_vertical_candidate_generation(tmp_path) -> None:
    diagnosis_docs = {
        "problem_classification": {},
        "candidate_launchpad": {
            "cards": [
                {
                    "card_id": "resolve_data",
                    "source_diagnosis_id": "evidence_insufficient_data_quality",
                    "card_type": "monitor_or_data_step",
                    "launch_status": "monitor_or_resolve_data",
                    "goal": "Review data quality",
                    "hypothesis_to_test": "Resolve data quality first.",
                    "suggested_methods": [],
                    "success_criteria": ["Resolve data-quality blockers."],
                    "is_rebalance_recommendation": False,
                    "decision_boundary": "This is not a rebalance recommendation.",
                }
            ]
        },
    }

    with pytest.raises(VerticalFlowError, match="launchpad_card_or_builder_prefill_missing"):
        build_selected_builder_document(
            output_dir=tmp_path / "Main portfolio",
            diagnosis_docs=diagnosis_docs,
            method="equal_weight",
        )
