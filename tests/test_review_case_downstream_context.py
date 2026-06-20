from __future__ import annotations

from src.review_case import review_case_downstream_evidence_chain_context


def test_downstream_context_projects_candidate_and_comparison_evidence() -> None:
    candidate_generation = {
        "source_artifacts": ["candidate_generation.json", "problem_classification.json"],
        "candidate": {
            "source_diagnosis_id": "high_concentration",
            "source_diagnosis_label": "High concentration",
            "source_diagnosis_role": "root_cause",
            "source_diagnosis_statement": "Portfolio concentration is the main review issue.",
            "hypothesis_to_test": "Test whether equal weight reduces concentration.",
            "success_criteria": ["Reduce single-name concentration", "Reduce single-name concentration"],
            "tradeoff_to_watch": "Potential tracking error increase.",
            "candidate_boundary": "Use only as a diagnostic candidate.",
        },
    }
    comparison_row = {
        "source_artifacts": ["current_vs_candidate.json", "candidate_generation.json"],
        "success_criteria_result": [
            {"criterion": "Improve stress drawdown"},
            {"criterion": "Improve stress drawdown"},
            {"summary": "Keep income comparable"},
        ],
    }

    context = review_case_downstream_evidence_chain_context(
        candidate_generation,
        comparison_row=comparison_row,
    )

    assert context.selected_diagnosis_id == "high_concentration"
    assert context.selected_diagnosis_label == "High concentration"
    assert context.selected_diagnosis_role == "root_cause"
    assert context.diagnosis_statement == "Portfolio concentration is the main review issue."
    assert context.tested_hypothesis == "Test whether equal weight reduces concentration."
    assert context.success_criteria == [
        "Reduce single-name concentration",
        "Improve stress drawdown",
        "Keep income comparable",
    ]
    assert context.tradeoff_to_watch == "Potential tracking error increase."
    assert context.candidate_boundary == "Use only as a diagnostic candidate."
    assert context.recommendation_boundary == (
        "Decision Verdict is non-binding decision support and does not execute trades."
    )
    assert context.source_artifacts == [
        "candidate_generation.json",
        "problem_classification.json",
        "current_vs_candidate.json",
    ]


def test_downstream_context_uses_fallback_artifacts_for_verdict_and_report_context() -> None:
    context = review_case_downstream_evidence_chain_context(
        {"candidate": {}},
        verdict={"verdict_id": "evidence_insufficient"},
        ai_context={"source_artifacts": {}},
    )

    assert context.source_artifacts == [
        "problem_classification.json",
        "candidate_generation.json",
        "current_vs_candidate.json",
        "decision_verdict.json",
        "ai_commentary_context.json",
    ]
    assert context.recommendation_boundary == (
        "Decision Verdict is non-binding decision support and does not execute trades."
    )


def test_downstream_context_prefers_candidate_boundary_and_limits_lists() -> None:
    candidate_generation = {
        "source_artifacts": [f"artifact_{index}.json" for index in range(12)],
        "candidate": {
            "decision_boundary": "Candidate boundary wins.",
            "success_criteria": [f"criterion {index}" for index in range(10)],
        },
    }
    context = review_case_downstream_evidence_chain_context(candidate_generation)

    assert context.candidate_boundary == "Candidate boundary wins."
    assert context.recommendation_boundary == "Candidate boundary wins."
    assert context.success_criteria == [f"criterion {index}" for index in range(8)]
    assert context.source_artifacts == [f"artifact_{index}.json" for index in range(10)]


def test_downstream_context_serializes_to_public_field_names() -> None:
    context = review_case_downstream_evidence_chain_context(
        {
            "candidate": {
                "source_diagnosis_id": "duration_risk",
                "hypothesis_to_test": "Test shorter duration.",
            },
        }
    )

    assert context.to_public_dict() == {
        "selected_diagnosis_id": "duration_risk",
        "selected_diagnosis_label": None,
        "selected_diagnosis_role": None,
        "diagnosis_statement": None,
        "tested_hypothesis": "Test shorter duration.",
        "success_criteria": [],
        "tradeoff_to_watch": None,
        "candidate_boundary": None,
        "recommendation_boundary": (
            "Decision Verdict is non-binding decision support and does not execute trades."
        ),
        "source_artifacts": [
            "problem_classification.json",
            "candidate_generation.json",
            "current_vs_candidate.json",
        ],
    }
