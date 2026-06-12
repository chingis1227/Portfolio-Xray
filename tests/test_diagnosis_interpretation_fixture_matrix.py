"""Dynamic diagnosis interpretation fixture matrix (Session 11)."""

from __future__ import annotations

from src.api.reviews import _diagnosis_summary
from src.block_4.diagnosis_builder import build_block_4_diagnosis

from block_4_fixtures import all_block_4_archetypes


def _build_problem_docs() -> dict[str, dict]:
    docs: dict[str, dict] = {}
    for case in all_block_4_archetypes():
        result = build_block_4_diagnosis(
            portfolio_xray=case.portfolio_xray,
            stress_report=case.stress_report,
            analysis_end="2026-04-30",
            generated_at="2026-05-29T12:00:00Z",
        )
        docs[case.archetype_id] = result.problem_classification
    return docs


def test_dynamic_fixture_matrix_produces_distinct_diagnosis_chains() -> None:
    docs = _build_problem_docs()

    assert len(docs) == 10

    selected_ids = {
        str(doc["interpretation_chain"]["selected_diagnosis_id"])
        for doc in docs.values()
    }
    headlines = {
        str(doc["root_cause_narrative"]["statement_en"])
        for doc in docs.values()
    }
    leading_signals = {
        str((doc["diagnosis_evidence_items"] or [{}])[0].get("signal"))
        for doc in docs.values()
    }

    assert len(selected_ids) >= 7
    assert len(headlines) >= 7
    assert len(leading_signals) >= 7
    assert docs["concentrated_equity"]["interpretation_chain"]["selected_diagnosis_id"] == "high_concentration"
    assert docs["duration_heavy_bonds"]["interpretation_chain"]["selected_diagnosis_id"] in {
        "duration_rates_vulnerability",
        "poor_rates_up_behavior",
    }
    assert docs["insufficient_data"]["interpretation_chain"]["selected_diagnosis_id"] == (
        "evidence_insufficient_data_quality"
    )
    assert docs["acceptable_no_action"]["interpretation_chain"]["selected_diagnosis_id"] == (
        "current_portfolio_acceptable"
    )


def test_dynamic_fixture_matrix_interpretation_chain_is_source_backed() -> None:
    for archetype_id, doc in _build_problem_docs().items():
        chain = doc["interpretation_chain"]
        primary_id = doc["primary_problem"]["problem_id"]

        assert chain["diagnostic_only"] is True, archetype_id
        assert chain["selected_diagnosis_id"] == primary_id, archetype_id
        assert chain["recommendation_boundary_en"] == doc["next_diagnostic_step"]["decision_boundary"]
        assert doc["diagnosis_evidence_items"] == chain["diagnosis_evidence_items"]
        assert doc["root_cause_narrative"] == chain["root_cause_narrative"]
        assert doc["metric_to_diagnosis_trace"] == chain["metric_to_diagnosis_trace"]
        assert doc["professional_rationale_refs"] == chain["professional_rationale_refs"]

        evidence_ids = {row["evidence_item_id"] for row in doc["diagnosis_evidence_items"]}
        assert evidence_ids, archetype_id
        for row in doc["diagnosis_evidence_items"]:
            assert row["source_artifact"] in {"portfolio_xray.json", "stress_report.json"}, archetype_id
            assert row["source_block"], archetype_id
            assert row["interpretation_en"], archetype_id
            assert row["evidence_role"] in {
                "supports_selected_diagnosis",
                "supporting_symptom",
                "limits_selected_diagnosis",
                "context_for_selected_diagnosis",
            }, archetype_id

        for trace in doc["metric_to_diagnosis_trace"]:
            assert trace["evidence_item_id"] in evidence_ids, archetype_id
            assert trace["contributes_to_selected_diagnosis_id"] == primary_id, archetype_id
            assert trace["source_artifact"] in {"portfolio_xray.json", "stress_report.json"}, archetype_id


def test_dynamic_fixture_matrix_fastapi_diagnosis_summary_matches_chain() -> None:
    for archetype_id, doc in _build_problem_docs().items():
        summary = _diagnosis_summary({"problem_classification": doc})
        chain = doc["interpretation_chain"]

        assert summary.primary_diagnosis == chain["selected_diagnosis_id"], archetype_id
        assert summary.headline == doc["root_cause_narrative"]["statement_en"], archetype_id
        assert summary.recommendation_boundary == chain["recommendation_boundary_en"], archetype_id
        assert summary.diagnosis_evidence_items, archetype_id
        assert summary.metric_to_diagnosis_trace, archetype_id
        assert summary.root_cause_narrative is not None, archetype_id
        assert summary.root_cause_narrative.diagnosis_id == chain["selected_diagnosis_id"], archetype_id
        assert summary.professional_rationale_refs, archetype_id
        assert all(item.source_artifact for item in summary.diagnosis_evidence_items), archetype_id
