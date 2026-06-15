from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

import httpx
import pytest

from scripts.generate_fastapi_api_types import OUTPUT_PATH, render_types
from src.api.app import app
import src.api.reviews as review_service


def _request(method: str, path: str, *, json_body: dict | None = None) -> httpx.Response:
    async def _send() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.request(method, path, json=json_body)

    return asyncio.run(_send())


def _write_staged_state_for_test(run_dir: Path, review_id: str, *, current_stage: str = "candidate") -> None:
    state = review_service._initial_staged_state(review_id, mode="live")
    state["status"] = "partial"
    state["current_stage"] = current_stage
    for stage in [
        "input",
        "data_load",
        "xray",
        "stress",
        "client_fit",
        "problem_classification",
        "launchpad_builder",
    ]:
        state["stages"][stage]["status"] = "completed"
    review_service._write_staged_state(run_dir, state)


def test_health_endpoint_returns_public_envelope() -> None:
    response = _request("GET", "/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["api_version"] == "v1"
    assert body["schema_version"] == "health_v1"
    assert body["review_id"] is None
    assert body["stage"] == "health"
    assert body["status"] == "ok"
    assert body["warnings"] == []
    assert body["safe_error"] is None
    assert body["lineage"] == {
        "review_id": None,
        "selected_card_id": None,
        "builder_setup_id": None,
        "candidate_id": None,
        "comparison_id": None,
        "verdict_id": None,
        "product_run_id": None,
    }
    assert body["evidence"] == {
        "source_artifacts": [],
        "data_quality": "ok",
        "confidence": "high",
    }
    assert body["data"] == {
        "service": "portfolio-mri-api",
        "status": "ok",
        "api_version": "v1",
        "openapi_available": True,
    }


def test_openapi_includes_session_03_typed_mvp_surface() -> None:
    response = _request("GET", "/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Portfolio MRI Local API"
    assert schema["info"]["version"] == "0.1.0"
    expected_paths = {
        "/api/v1/health": "get",
        "/api/v1/reviews": "post",
        "/api/v1/reviews/staged": "post",
        "/api/v1/reviews/{review_id}": "get",
        "/api/v1/reviews/{review_id}/status": "get",
        "/api/v1/reviews/{review_id}/builder": "post",
        "/api/v1/reviews/{review_id}/candidate": "post",
        "/api/v1/reviews/{review_id}/comparison": "post",
        "/api/v1/reviews/{review_id}/verdict": "post",
        "/api/v1/reviews/{review_id}/report": "post",
    }
    for path, method in expected_paths.items():
        assert path in schema["paths"]
        assert method in schema["paths"][path]
        assert schema["paths"][path][method]["operationId"]

    schemas = schema["components"]["schemas"]
    for schema_name in [
        "CreateReviewRequest",
        "StagedReviewStartedResponse",
        "StagedReviewStatusResponse",
        "StagedStageState",
        "StagedProviderStatus",
        "StagedSafeError",
        "ClientFitInput",
        "ClientFitRangeInput",
        "ClientFitDisplaySummary",
        "ClientFitTargetDisplayRow",
        "CreateReviewResponse",
        "ReviewRecoveryResponse",
        "BuilderRequest",
        "BuilderResponse",
        "BuilderSetupIdRequest",
        "CandidateResponse",
        "CandidateIdRequest",
        "ComparisonResponse",
        "ComparisonIdRequest",
        "VerdictResponse",
        "VerdictIdRequest",
        "ReportResponse",
        "SafeError",
        "ApiLineage",
        "ApiEvidence",
    ]:
        assert schema_name in schemas

    create_review = schema["paths"]["/api/v1/reviews"]["post"]
    request_ref = create_review["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    assert request_ref.endswith("/CreateReviewRequest")
    create_request_schema = schemas["CreateReviewRequest"]
    assert "client_fit" in create_request_schema["properties"]
    assert create_request_schema["properties"]["client_fit"]["anyOf"][0]["$ref"].endswith("/ClientFitInput")
    response_ref = create_review["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
    assert response_ref.endswith("/CreateReviewResponse")

    recover_review = schema["paths"]["/api/v1/reviews/{review_id}"]["get"]
    recovery_ref = recover_review["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
    assert recovery_ref.endswith("/ReviewRecoveryResponse")

    staged_review = schema["paths"]["/api/v1/reviews/staged"]["post"]
    staged_request_ref = staged_review["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    assert staged_request_ref.endswith("/CreateReviewRequest")
    staged_response_ref = staged_review["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
    assert staged_response_ref.endswith("/StagedReviewStartedResponse")
    staged_status = schema["paths"]["/api/v1/reviews/{review_id}/status"]["get"]
    staged_status_ref = staged_status["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
    assert staged_status_ref.endswith("/StagedReviewStatusResponse")


def test_staged_failure_classifier_uses_stderr_tail_for_fred_http_failure() -> None:
    result = {
        "status": "failed",
        "error": "Backend run failed.",
        "details": "python_stage_failed",
        "stderr_tail": (
            'Traceback (most recent call last):\n'
            '  File "D:\\repo\\src\\data_fred.py", line 10, in fetch\n'
            "urllib.error.HTTPError: HTTP Error 404: FRED series DTB3 download failed"
        ),
    }

    code, message, user_action, retryable, stage = review_service._classify_staged_failure(result, 1)

    assert code == "DATA_PROVIDER_FAILED"
    assert message == "Backend run failed."
    assert user_action == "retry"
    assert retryable is True
    assert stage == "data_load"
    safe_error = review_service._staged_safe_error(
        code=code,
        message=result["stderr_tail"],
        user_action=user_action,
        retryable=retryable,
        stage=stage,
    ).model_dump(mode="json")
    assert "Traceback" not in json.dumps(safe_error)
    assert not re.search(r"[A-Z]:[\\/]", json.dumps(safe_error))


def test_staged_failure_classifier_timeout_stays_timeout_from_tail() -> None:
    result = {
        "status": "failed",
        "error": "Backend run failed.",
        "details": "python_stage_failed",
        "stdout_tail": "Market data provider request timeout while loading Yahoo prices.",
    }

    code, _message, user_action, retryable, stage = review_service._classify_staged_failure(result, 1)

    assert code == "TIMEOUT"
    assert user_action == "retry"
    assert retryable is True
    assert stage == "data_load"


def test_staged_failure_classifier_unknown_python_failure_remains_python_stage_failed() -> None:
    result = {
        "status": "failed",
        "error": "Backend run failed.",
        "details": "python_stage_failed",
        "stderr_tail": "ValueError: unexpected internal state while formatting diagnostics.",
    }

    code, _message, user_action, retryable, stage = review_service._classify_staged_failure(result, 1)

    assert code == "PYTHON_STAGE_FAILED"
    assert user_action == "retry"
    assert retryable is True
    assert stage == "data_load"


def _fake_review_result(review_id: str = "frontend_review_fastapi_unit") -> dict:
    return {
        "review_id": review_id,
        "status": "completed",
        "mode": "diagnosis_plus_problem",
        "portfolio_input": {
            "investor_currency": "USD",
            "total_weight": 100.0,
            "holdings": [
                {"type": "instrument", "ticker": "VOO", "weight": 60.0},
                {"type": "instrument", "ticker": "BND", "weight": 40.0},
            ],
        },
        "paths": {
            "run_dir": f"runs/{review_id}",
            "portfolio_xray": f"runs/{review_id}/analysis_subject/portfolio_xray.json",
            "stress_report": f"runs/{review_id}/analysis_subject/stress_report.json",
            "run_metadata": f"runs/{review_id}/analysis_subject/run_metadata.json",
            "output_manifest": f"runs/{review_id}/analysis_subject/output_manifest.json",
            "problem_classification": f"runs/{review_id}/analysis_subject/problem_classification.json",
            "candidate_launchpad": f"runs/{review_id}/analysis_subject/candidate_launchpad.json",
            "portfolio_alternatives_builder": f"runs/{review_id}/analysis_subject/portfolio_alternatives_builder.json",
            "client_fit_check": f"runs/{review_id}/analysis_subject/client_fit_check.json",
            "ai_commentary_context": f"runs/{review_id}/analysis_subject/ai_commentary_context.json",
        },
        "outputs": {
            "run_metadata": {"analysis_end": "2026-05-31"},
            "portfolio_xray": {"schema_version": "portfolio_xray_v2"},
            "stress_report": {"schema_version": "stress_report_v1"},
            "output_manifest": {"schema_version": "output_manifest_v1"},
            "client_fit_check": {
                "schema_version": "client_fit_check_v1",
                "client_fit_status": "watch",
                "profile": {"preset_id": "balanced", "source_quality": "medium"},
                "checks": [
                    {
                        "dimension": "volatility_vs_target",
                        "portfolio_value": 0.115,
                        "client_range": {"min": 0.07, "max": 0.10},
                        "status": "watch",
                        "interpretation": "Volatility is slightly outside the stated comfort range.",
                    }
                ],
                "recommendation_boundary": "Client Fit is non-binding decision support.",
            },
            "problem_classification": {
                "analysis_end": "2026-05-31",
                "primary_diagnosis": {
                    "diagnosis_id": "high_concentration",
                    "label_en": "High concentration",
                    "thesis_en": "A few holdings dominate the current portfolio.",
                    "confidence": "medium",
                    "key_evidence": [
                        {
                            "interpretation_en": "Top three holdings sum to 72% of capital.",
                            "source_artifact": "portfolio_xray.json",
                        }
                    ],
                },
                "next_diagnostic_step": {
                    "label": "Test a concentration-reduction hypothesis."
                },
                "interpretation_chain": {
                    "schema_version": "diagnosis_interpretation_chain_v1",
                    "diagnostic_only": True,
                    "selected_diagnosis_id": "high_concentration",
                    "selected_diagnosis_role": "root_cause",
                    "source_artifacts": ["portfolio_xray.json", "stress_report.json"],
                    "root_cause_narrative": {
                        "diagnosis_id": "high_concentration",
                        "label_en": "High concentration",
                        "diagnosis_role": "root_cause",
                        "n_supporting_evidence_items": 1,
                        "n_rejected_alternatives": 1,
                        "statement_en": "High concentration is the root-cause diagnosis.",
                        "root_cause_over_symptom_en": "Root causes outrank symptoms when supported.",
                        "portfolio_manager_interpretation_en": "Capital is too dependent on a small number of positions.",
                        "confidence_context_en": "Confidence is medium because evidence is source-backed.",
                        "source_refs": ["docs/specs/block_4_diagnosis_v3_spec.md#primary-selection-order"],
                    },
                    "diagnosis_evidence_items": [
                        {
                            "evidence_item_id": "ev_top3_weight",
                            "linked_problem_id": "high_concentration",
                            "evidence_role": "supports_selected_diagnosis",
                            "signal": "top3_capital_weight",
                            "source_artifact": "portfolio_xray.json",
                            "source_block": "block_2_1_asset_allocation",
                            "source_field_path": "block_2_1_asset_allocation.concentration.top3_weight",
                            "observed_value": 0.72,
                            "interpretation_en": "Top three holdings sum to 72% of capital.",
                            "why_relevant_to_diagnosis_en": "High top-three weight supports concentration.",
                            "severity": "medium",
                            "confidence": "medium",
                        }
                    ],
                    "metric_to_diagnosis_trace": [
                        {
                            "trace_id": "trace_01_top3_capital_weight",
                            "source_artifact": "portfolio_xray.json",
                            "source_block": "block_2_1_asset_allocation",
                            "source_field_path": "block_2_1_asset_allocation.concentration.top3_weight",
                            "metric_or_signal": "top3_capital_weight",
                            "evidence_item_id": "ev_top3_weight",
                            "linked_problem_id": "high_concentration",
                            "contributes_to_selected_diagnosis_id": "high_concentration",
                            "contribution": "supports_selected_diagnosis",
                            "interpretation_en": "Top-three concentration is elevated.",
                        }
                    ],
                    "rejected_alternatives": [
                        {
                            "problem_id": "high_volatility",
                            "label_en": "High volatility",
                            "reason_code": "symptom_supports_selected_root_cause",
                            "reason_en": "Volatility is treated as a symptom of concentration.",
                            "top_evidence_item_ids": ["ev_top3_weight"],
                        }
                    ],
                    "professional_rationale_refs": [
                        {
                            "ref_id": "block_4_diagnosis_contract",
                            "source": "docs/specs/block_4_diagnosis_v3_spec.md",
                            "reason_en": "Defines root-cause priority.",
                        }
                    ],
                    "next_step_link": {
                        "step_type": "targeted_hypothesis_test",
                        "label": "Test reduce concentration",
                        "decision_boundary": "Decision Verdict decides after comparison.",
                    },
                    "recommendation_boundary_en": "Decision Verdict decides after comparison.",
                },
            },
            "candidate_launchpad": {
                "cards": [
                    {
                        "card_id": "launchpad_01_reduce_concentration",
                        "title": "Reduce Concentration",
                        "default_method": "equal_weight",
                        "suggested_methods": [{"candidate_method_id": "equal_weight"}],
                        "card_type": "targeted_hypothesis_test",
                        "is_rebalance_recommendation": False,
                    },
                    {
                        "card_id": "launchpad_02_monitor",
                        "title": "Monitor",
                        "suggested_methods": [],
                        "card_type": "monitor_or_data_step",
                        "is_rebalance_recommendation": False,
                    },
                ]
            },
            "portfolio_alternatives_builder": {"can_generate_candidate": True},
        },
    }


def test_create_review_runs_diagnosis_adapter_and_returns_public_envelope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result_path = tmp_path / "review_result.json"

    def fake_run_from_payload(payload_path: Path, *, mode: str, timeout_seconds: int) -> tuple[int, Path]:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        assert payload["holdings"] == [
            {"type": "instrument", "ticker": "VOO", "weight": 60.0},
            {"type": "instrument", "ticker": "BND", "weight": 30.0},
            {"type": "cash", "currency": "USD", "weight": 10.0},
        ]
        assert payload["client_fit"] == {
            "preset_id": "balanced",
            "source": "questionnaire",
            "source_quality": "medium",
            "source_quality_reason": "Based on the short questionnaire.",
            "horizon_years": 7.0,
            "target_return_range": {"min": 0.05, "max": 0.07},
            "target_vol_range": {"min": 0.07, "max": 0.1},
            "target_max_drawdown_pct": -0.2,
        }
        assert mode == review_service.MODE_DIAGNOSIS_PLUS_PROBLEM
        assert timeout_seconds == review_service.DEFAULT_TIMEOUT_SECONDS
        result_path.write_text(json.dumps(_fake_review_result()), encoding="utf-8")
        return 0, result_path

    monkeypatch.setattr(review_service, "PAYLOAD_DIR", tmp_path / "payloads")
    monkeypatch.setattr(review_service, "run_from_payload", fake_run_from_payload)

    response = _request(
        "POST",
        "/api/v1/reviews",
        json_body={
            "portfolio": {
                "investor_currency": "USD",
                "holdings": [
                    {"type": "instrument", "ticker": "VOO", "weight_pct": 60.0},
                    {"type": "instrument", "ticker": "BND", "weight_pct": 30.0},
                    {"type": "cash", "currency": "USD", "weight_pct": 10.0},
                ],
            },
            "client_fit": {
                "preset_id": "balanced",
                "source": "questionnaire",
                "source_quality": "medium",
                "source_quality_reason": "Based on the short questionnaire.",
                "horizon_years": 7,
                "target_return_range": {"min": 0.05, "max": 0.07},
                "target_vol_range": {"min": 0.07, "max": 0.10},
                "target_max_drawdown_pct": -0.20,
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["stage"] == "diagnosis"
    assert body["status"] == "ok"
    assert body["review_id"] == "frontend_review_fastapi_unit"
    assert body["safe_error"] is None
    assert body["lineage"]["review_id"] == "frontend_review_fastapi_unit"
    assert body["data"]["review_summary"]["investor_currency"] == "USD"
    assert body["data"]["review_summary"]["input_weight_total_pct"] == 100.0
    assert body["data"]["diagnosis"]["primary_diagnosis"] == "high_concentration"
    assert body["data"]["diagnosis"]["headline"] == "High concentration is the root-cause diagnosis."
    assert body["data"]["diagnosis"]["confidence"] == "medium"
    assert body["data"]["diagnosis"]["selected_diagnosis_role"] == "root_cause"
    assert body["data"]["diagnosis"]["source_artifacts"] == ["portfolio_xray.json", "stress_report.json"]
    assert body["data"]["diagnosis"]["root_cause_narrative"] == {
        "diagnosis_id": "high_concentration",
        "label": "High concentration",
        "diagnosis_role": "root_cause",
        "statement": "High concentration is the root-cause diagnosis.",
        "root_cause_over_symptom": "Root causes outrank symptoms when supported.",
        "portfolio_manager_interpretation": "Capital is too dependent on a small number of positions.",
        "confidence_context": "Confidence is medium because evidence is source-backed.",
        "supporting_evidence_count": 1,
        "rejected_alternative_count": 1,
        "source_refs": ["docs/specs/block_4_diagnosis_v3_spec.md#primary-selection-order"],
    }
    assert body["data"]["diagnosis"]["diagnosis_evidence_items"][0]["evidence_item_id"] == "ev_top3_weight"
    assert body["data"]["diagnosis"]["diagnosis_evidence_items"][0]["observed_value"] == 0.72
    assert body["data"]["diagnosis"]["metric_to_diagnosis_trace"][0]["evidence_item_id"] == "ev_top3_weight"
    assert body["data"]["diagnosis"]["rejected_alternatives"][0]["problem_id"] == "high_volatility"
    assert body["data"]["diagnosis"]["professional_rationale_refs"][0]["ref_id"] == "block_4_diagnosis_contract"
    assert body["data"]["diagnosis"]["recommendation_boundary"] == "Decision Verdict decides after comparison."
    assert body["data"]["client_fit"]["status_label"] == "Client Fit watch"
    assert body["data"]["client_fit"]["status_tone"] == "amber"
    assert body["data"]["client_fit"]["profile_label"] == "balanced"
    assert body["data"]["client_fit"]["target_rows"][0]["dimension_label"] == "Volatility comfort range"
    assert body["data"]["client_fit"]["target_rows"][0]["target_or_limit_label"] == "7.0% to 10.0%"
    assert "schema_version" not in body["data"]["client_fit"]
    assert "source_artifacts" not in body["data"]["client_fit"]
    assert body["data"]["launchpad"][0]["generation_allowed"] is True
    assert body["data"]["launchpad"][0]["is_rebalance_recommendation"] is False
    assert body["data"]["next_allowed_actions"] == ["prepare_builder", "recover_review"]
    assert {item["kind"] for item in body["data"]["artifact_refs"]} >= {
        "portfolio_xray",
        "stress_report",
        "problem_classification",
        "candidate_launchpad",
        "client_fit_check",
    }
    assert body["evidence"]["source_artifacts"] == body["data"]["artifact_refs"]
    serialized = json.dumps(body)
    assert "Traceback" not in serialized
    assert not re.search(r"[A-Z]:[\\/]", serialized)


def test_create_review_rejects_client_fit_liquidity_field() -> None:
    response = _request(
        "POST",
        "/api/v1/reviews",
        json_body={
            "portfolio": {
                "investor_currency": "USD",
                "holdings": [
                    {"type": "instrument", "ticker": "VOO", "weight_pct": 60.0},
                    {"type": "instrument", "ticker": "BND", "weight_pct": 40.0},
                ],
            },
            "client_fit": {
                "preset_id": "balanced",
                "source": "questionnaire",
                "source_quality": "medium",
                "liquidity_need_months": 6,
            },
        },
    )

    assert response.status_code == 422


def test_recover_review_restores_only_diagnosis_stages(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    review_id = "frontend_review_fastapi_recover"
    run_dir = tmp_path / review_id
    run_dir.mkdir()
    (run_dir / "review_result.json").write_text(
        json.dumps(_fake_review_result(review_id)),
        encoding="utf-8",
    )

    monkeypatch.setattr(review_service, "safe_review_run_dir", lambda value: run_dir)

    response = _request("GET", f"/api/v1/reviews/{review_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["stage"] == "recovery"
    assert body["status"] == "ok"
    assert body["review_id"] == review_id
    assert body["data"]["downstream_artifacts_restored_as_active"] is False
    assert body["data"]["restored_active_stages"] == ["diagnosis", "evidence", "hypothesis_setup"]
    assert body["data"]["launchpad"][0]["card_id"] == "launchpad_01_reduce_concentration"
    assert "not restored as active state" in body["warnings"][0]


def _fake_builder_document() -> dict:
    return {
        "status": "ok",
        "selected_card_id": "launchpad_01_reduce_concentration",
        "can_generate_candidate": True,
        "builder_prefill": {
            "builder_prefill_id": "builder_prefill_launchpad_01_reduce_concentration",
            "source_card_id": "launchpad_01_reduce_concentration",
            "suggested_method": "equal_weight",
            "success_criteria": ["Reduce top holding concentration."],
            "tradeoff_to_watch": "Return drag.",
            "decision_boundary": "Decision Verdict decides; this is not a recommendation.",
        },
        "candidate_setup": {
            "candidate_setup_id": "candidate_setup_builder_prefill_launchpad_01_reduce_concentration",
            "builder_prefill_id": "builder_prefill_launchpad_01_reduce_concentration",
            "source_card_id": "launchpad_01_reduce_concentration",
            "source_diagnosis_id": "high_concentration",
            "selected_method": "equal_weight",
            "parameters": {"mode": "capped"},
            "constraints": {"mode": "capped"},
            "success_criteria": ["Reduce top holding concentration."],
            "tradeoff_to_watch": "Return drag.",
            "decision_boundary": "Decision Verdict decides; this is not a recommendation.",
            "is_rebalance_recommendation": False,
        },
        "validation": {
            "validation_status": "valid",
            "can_generate_candidate": True,
            "validation_warnings": [],
        },
    }


def test_prepare_builder_runs_adapter_and_returns_public_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_prepare_selected_builder_setup(**kwargs):
        assert kwargs["review_id"] == "frontend_review_fastapi_unit"
        assert kwargs["selected_card_id"] == "launchpad_01_reduce_concentration"
        assert kwargs["method"] == "equal_weight"
        return {
            "review_id": kwargs["review_id"],
            "status": "completed",
            "stage": "builder_setup",
            "selected_card_id": kwargs["selected_card_id"],
            "can_generate_candidate": True,
            "path": "runs/frontend_review_fastapi_unit/analysis_subject/portfolio_alternatives_builder.json",
            "portfolio_alternatives_builder": _fake_builder_document(),
        }

    monkeypatch.setattr(
        review_service,
        "prepare_selected_builder_setup",
        fake_prepare_selected_builder_setup,
    )

    response = _request(
        "POST",
        "/api/v1/reviews/frontend_review_fastapi_unit/builder",
        json_body={
            "selected_card_id": "launchpad_01_reduce_concentration",
            "overrides": {"method_id": "equal_weight"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["stage"] == "builder"
    assert body["status"] == "ok"
    assert body["safe_error"] is None
    assert body["lineage"]["review_id"] == "frontend_review_fastapi_unit"
    assert body["lineage"]["selected_card_id"] == "launchpad_01_reduce_concentration"
    assert (
        body["lineage"]["builder_setup_id"]
        == "candidate_setup_builder_prefill_launchpad_01_reduce_concentration"
    )
    assert body["data"]["candidate_generation_allowed"] is True
    assert body["data"]["next_allowed_actions"] == ["generate_candidate"]
    assert body["data"]["builder_setup"]["method_id"] == "equal_weight"
    assert body["data"]["builder_setup"]["generation_readiness"] == "ready"
    assert body["evidence"]["source_artifacts"][0]["kind"] == "portfolio_alternatives_builder"
    assert "D:\\" not in json.dumps(body)


def test_generate_candidate_runs_adapter_and_returns_public_envelope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    review_id = "frontend_review_fastapi_candidate"
    run_dir = tmp_path / review_id
    subject_dir = run_dir / "analysis_subject"
    subject_dir.mkdir(parents=True)
    builder_doc = _fake_builder_document()
    (subject_dir / "portfolio_alternatives_builder.json").write_text(
        json.dumps(builder_doc),
        encoding="utf-8",
    )

    def fake_generate_selected_candidate(**kwargs):
        assert kwargs["review_id"] == review_id
        assert kwargs["selected_card_id"] == "launchpad_01_reduce_concentration"
        assert kwargs["factory_execution_mode"] == "fast"
        result = {
            "review_id": review_id,
            "status": "completed",
            "stage": "candidate_generation",
            "selected_card_id": kwargs["selected_card_id"],
            "candidate_id": "equal_weight",
            "generation_status": "generated",
            "can_compare": True,
            "path": f"runs/{review_id}/candidate_generation.json",
            "candidate_generation": {
                "generation_status": "generated",
                "warnings": [],
                "candidate": {
                    "candidate_id": "equal_weight",
                    "candidate_name": "Equal Weight",
                    "source_card_id": "launchpad_01_reduce_concentration",
                    "source_diagnosis_id": "high_concentration",
                    "hypothesis_to_test": "Test whether equal weighting reduces concentration.",
                    "success_criteria": ["Reduce top holding concentration."],
                    "tradeoff_to_watch": "Return drag.",
                    "decision_boundary": "Decision Verdict decides; this is not a recommendation.",
                    "weights": {"VOO": 0.5, "BND": 0.5},
                    "is_rebalance_recommendation": False,
                },
                "handoff_to_comparison": {
                    "can_compare": True,
                    "candidate_id": "equal_weight",
                    "does_not_create_verdict": True,
                },
            },
        }
        (run_dir / "candidate_generation.json").write_text(
            json.dumps(result["candidate_generation"]),
            encoding="utf-8",
        )
        return result

    monkeypatch.setattr(review_service, "safe_review_run_dir", lambda value: run_dir)
    monkeypatch.setattr(review_service, "generate_selected_candidate", fake_generate_selected_candidate)
    _write_staged_state_for_test(run_dir, review_id, current_stage="candidate")

    response = _request(
        "POST",
        f"/api/v1/reviews/{review_id}/candidate",
        json_body={"builder_setup_id": "candidate_setup_builder_prefill_launchpad_01_reduce_concentration"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["stage"] == "candidate"
    assert body["status"] == "ok"
    assert body["safe_error"] is None
    assert body["lineage"]["review_id"] == review_id
    assert body["lineage"]["selected_card_id"] == "launchpad_01_reduce_concentration"
    assert body["lineage"]["candidate_id"] == "equal_weight"
    assert body["data"]["candidate"]["generation_status"] == "generated"
    assert body["data"]["candidate"]["weight_summary"] == {"VOO": 0.5, "BND": 0.5}
    assert body["data"]["is_rebalance_recommendation"] is False
    assert body["data"]["next_allowed_actions"] == ["run_comparison"]
    assert {item["kind"] for item in body["evidence"]["source_artifacts"]} >= {
        "portfolio_alternatives_builder",
        "candidate_generation",
        "candidate_factory_run",
    }
    assert "Traceback" not in json.dumps(body)
    assert not re.search(r"[A-Z]:[\\/]", json.dumps(body))
    staged_state = json.loads((run_dir / "review_state.json").read_text(encoding="utf-8"))
    assert staged_state["status"] == "partial"
    assert staged_state["current_stage"] == "comparison"
    assert staged_state["stages"]["candidate"]["status"] == "completed"
    assert staged_state["stages"]["candidate"]["artifact_refs"] == ["candidate_generation.json"]


def _write_candidate_generation(run_dir: Path) -> None:
    (run_dir / "candidate_generation.json").write_text(
        json.dumps(
            {
                "generation_status": "generated",
                "selected_card_id": "launchpad_01_reduce_concentration",
                "candidate": {
                    "candidate_id": "equal_weight",
                    "candidate_name": "Equal Weight",
                    "source_card_id": "launchpad_01_reduce_concentration",
                    "source_diagnosis_id": "high_concentration",
                    "source_diagnosis_label": "High concentration",
                    "source_diagnosis_role": "root_cause",
                    "source_diagnosis_statement": "High concentration is the diagnosis being tested.",
                    "hypothesis_to_test": "Test whether equal weighting reduces concentration.",
                    "success_criteria": ["Reduce top holding concentration."],
                    "tradeoff_to_watch": "Return drag.",
                    "decision_boundary": "Decision Verdict decides; this is not a recommendation.",
                },
            }
        ),
        encoding="utf-8",
    )


def _write_client_fit_check(run_dir: Path, *, status: str = "fit") -> None:
    analysis_subject = run_dir / "analysis_subject"
    analysis_subject.mkdir(exist_ok=True)
    (analysis_subject / "client_fit_check.json").write_text(
        json.dumps(
            {
                "schema_version": "client_fit_check_v1",
                "client_fit_status": status,
                "profile": {"preset_id": "balanced", "source_quality": "medium"},
                "checks": [
                    {
                        "dimension": "worst_stress_loss_vs_limit",
                        "portfolio_value": -0.18,
                        "client_limit": -0.20,
                        "status": status,
                        "interpretation": "Worst stress loss is within the stated drawdown limit.",
                    }
                ],
                "recommendation_boundary": "Client Fit is non-binding decision support.",
            }
        ),
        encoding="utf-8",
    )


def _current_vs_candidate_doc() -> dict:
    return {
        "schema_version": "current_vs_candidate_v1",
        "comparison_status": "available",
        "view_mode": "one_candidate",
        "baseline": {"display_name": "Current portfolio"},
        "selected_candidate_ids": ["equal_weight"],
        "comparisons": [
            {
                "candidate_id": "equal_weight",
                "display_name": "Equal Weight",
                "what_improved": [{"label": "Concentration improved"}],
                "what_worsened": [{"label": "Expected return fell"}],
                "what_stayed_similar": [{"label": "Volatility stayed similar"}],
                "unavailable_metrics": [{"field": "turnover"}],
                "success_criteria_result": {"overall_status": "met"},
                "materiality_for_decision_review": {"status": "review_candidate"},
            }
        ],
        "warnings": [],
    }


def test_run_comparison_runs_adapter_and_returns_public_envelope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    review_id = "frontend_review_fastapi_compare"
    run_dir = tmp_path / review_id
    run_dir.mkdir()
    _write_candidate_generation(run_dir)
    _write_client_fit_check(run_dir)

    def fake_compare_selected_candidate(**kwargs):
        assert kwargs["review_id"] == review_id
        assert kwargs["selected_card_id"] == "launchpad_01_reduce_concentration"
        result = {
            "review_id": review_id,
            "status": "completed",
            "stage": "current_vs_candidate",
            "selected_card_id": kwargs["selected_card_id"],
            "candidate_id": "equal_weight",
            "paths": {
                "candidate_comparison": f"runs/{review_id}/candidate_comparison.json",
                "current_vs_candidate": f"runs/{review_id}/current_vs_candidate.json",
                "site_explanation_bundle": f"runs/{review_id}/site_explanation_bundle.json",
            },
            "current_vs_candidate": _current_vs_candidate_doc(),
        }
        (run_dir / "current_vs_candidate.json").write_text(
            json.dumps(result["current_vs_candidate"]),
            encoding="utf-8",
        )
        (run_dir / "candidate_comparison.json").write_text(json.dumps({"status": "ok"}), encoding="utf-8")
        return result

    monkeypatch.setattr(review_service, "safe_review_run_dir", lambda value: run_dir)
    monkeypatch.setattr(review_service, "compare_selected_candidate", fake_compare_selected_candidate)
    _write_staged_state_for_test(run_dir, review_id, current_stage="comparison")

    response = _request(
        "POST",
        f"/api/v1/reviews/{review_id}/comparison",
        json_body={"candidate_id": "equal_weight"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["stage"] == "comparison"
    assert body["status"] == "ok"
    assert body["safe_error"] is None
    assert body["lineage"]["selected_card_id"] == "launchpad_01_reduce_concentration"
    assert body["lineage"]["candidate_id"] == "equal_weight"
    assert body["lineage"]["comparison_id"] == "current_vs_candidate:equal_weight"
    assert body["data"]["comparison"]["candidate_label"] == "Equal Weight"
    assert body["data"]["comparison"]["success_criteria_result"] == "passed"
    assert body["data"]["comparison"]["materiality"] == "material"
    assert body["data"]["comparison"]["what_improved"] == ["Concentration improved"]
    assert body["data"]["evidence_chain_context"]["selected_diagnosis_id"] == "high_concentration"
    assert body["data"]["evidence_chain_context"]["tested_hypothesis"] == (
        "Test whether equal weighting reduces concentration."
    )
    assert body["data"]["evidence_chain_context"]["success_criteria"] == [
        "Reduce top holding concentration."
    ]
    assert body["data"]["client_fit"]["status_label"] == "Within stated Client Fit profile"
    assert body["data"]["client_fit"]["target_rows"][0]["dimension_label"] == "Worst stress loss limit"
    assert "client_fit_check.json" not in json.dumps(body["data"]["client_fit"])
    assert body["data"]["next_allowed_actions"] == ["generate_verdict"]
    assert {item["kind"] for item in body["evidence"]["source_artifacts"]} >= {
        "candidate_generation",
        "candidate_comparison",
        "current_vs_candidate",
    }
    assert not re.search(r"[A-Z]:[\\/]", json.dumps(body))
    staged_state = json.loads((run_dir / "review_state.json").read_text(encoding="utf-8"))
    assert staged_state["status"] == "partial"
    assert staged_state["current_stage"] == "verdict"
    assert staged_state["stages"]["comparison"]["status"] == "completed"
    assert set(staged_state["stages"]["comparison"]["artifact_refs"]) >= {
        "current_vs_candidate.json",
        "candidate_comparison.json",
    }


def test_generate_verdict_runs_adapter_and_returns_public_envelope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    review_id = "frontend_review_fastapi_verdict"
    run_dir = tmp_path / review_id
    run_dir.mkdir()
    _write_candidate_generation(run_dir)
    _write_client_fit_check(run_dir)
    (run_dir / "current_vs_candidate.json").write_text(
        json.dumps(_current_vs_candidate_doc()),
        encoding="utf-8",
    )

    def fake_write_selected_candidate_verdict(**kwargs):
        assert kwargs["review_id"] == review_id
        assert kwargs["selected_card_id"] == "launchpad_01_reduce_concentration"
        result = {
            "review_id": review_id,
            "status": "completed",
            "stage": "decision_verdict",
            "selected_card_id": kwargs["selected_card_id"],
            "candidate_id": "equal_weight",
            "path": f"runs/{review_id}/decision_verdict.json",
            "decision_verdict": {
                "schema_version": "decision_verdict_v1",
                "verdict_id": "rebalance_to_selected_candidate",
                "reviewed_candidate_id": "equal_weight",
                "confidence": "medium",
                "rationale_summary": "The candidate materially improves the diagnosed risk.",
                "recommended_action": "Review the candidate as decision support only.",
                "confidence_limitations": ["Costs are estimated."],
                "evidence_summary": {
                    "client_fit_decision_context": {
                        "client_fit_status": "fit",
                        "diagnostic_quality_status": "issue",
                        "decision_action": "rebalance_review",
                        "status_label": "Within stated Client Fit profile",
                        "status_tone": "green",
                        "profile_label": "balanced",
                        "source_quality_label": "medium",
                        "boundary_en": "Client Fit is bounded display context only.",
                        "next_best_test_en": "Read the verdict next to the objective diagnosis.",
                    }
                },
                "guardrails": {"does_not_execute_trades": True},
            },
            "site_explanation_bundle_path": f"runs/{review_id}/site_explanation_bundle.json",
        }
        (run_dir / "decision_verdict.json").write_text(
            json.dumps(result["decision_verdict"]),
            encoding="utf-8",
        )
        return result

    monkeypatch.setattr(review_service, "safe_review_run_dir", lambda value: run_dir)
    monkeypatch.setattr(
        review_service,
        "write_selected_candidate_verdict",
        fake_write_selected_candidate_verdict,
    )
    _write_staged_state_for_test(run_dir, review_id, current_stage="verdict")

    response = _request(
        "POST",
        f"/api/v1/reviews/{review_id}/verdict",
        json_body={"comparison_id": "current_vs_candidate:equal_weight"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["stage"] == "verdict"
    assert body["status"] == "ok"
    assert body["safe_error"] is None
    assert body["lineage"]["comparison_id"] == "current_vs_candidate:equal_weight"
    assert body["lineage"]["verdict_id"] == "rebalance_to_selected_candidate"
    assert body["data"]["verdict"]["verdict"] == "rebalance_review"
    assert body["data"]["verdict"]["evidence_used"] == [
        "Concentration improved",
        "Expected return fell",
        "turnover",
    ]
    assert body["data"]["evidence_chain_context"]["selected_diagnosis_id"] == "high_concentration"
    assert body["data"]["verdict"]["decision_support_only"] is True
    assert body["data"]["client_fit"]["status_label"] == "Within stated Client Fit profile"
    assert body["data"]["client_fit"]["next_best_test"] == "Read the verdict next to the objective diagnosis."
    assert "schema_version" not in body["data"]["client_fit"]
    assert body["data"]["next_allowed_actions"] == ["generate_report"]
    assert "Traceback" not in json.dumps(body)
    staged_state = json.loads((run_dir / "review_state.json").read_text(encoding="utf-8"))
    assert staged_state["status"] == "partial"
    assert staged_state["current_stage"] == "report"
    assert staged_state["stages"]["verdict"]["status"] == "completed"
    assert staged_state["stages"]["verdict"]["artifact_refs"] == ["decision_verdict.json"]


def test_generate_report_runs_adapter_and_returns_grounded_preview(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    review_id = "frontend_review_fastapi_report"
    run_dir = tmp_path / review_id
    run_dir.mkdir()
    _write_candidate_generation(run_dir)
    _write_client_fit_check(run_dir)
    (run_dir / "decision_verdict.json").write_text(
        json.dumps(
            {
                "schema_version": "decision_verdict_v1",
                "verdict_id": "no_material_rebalance_recommended",
                "reviewed_candidate_id": "equal_weight",
                "evidence_summary": {
                    "client_fit_decision_context": {
                        "client_fit_status": "fit",
                        "diagnostic_quality_status": "clean",
                        "decision_action": "keep_current",
                        "status_label": "Within stated Client Fit profile",
                        "status_tone": "green",
                        "profile_label": "balanced",
                        "source_quality_label": "medium",
                    }
                },
                "guardrails": {"does_not_execute_trades": True},
            }
        ),
        encoding="utf-8",
    )

    def fake_write_selected_report_context(**kwargs):
        assert kwargs["review_id"] == review_id
        assert kwargs["selected_card_id"] == "launchpad_01_reduce_concentration"
        result = {
            "review_id": review_id,
            "status": "completed",
            "stage": "report_commentary",
            "selected_card_id": kwargs["selected_card_id"],
            "candidate_id": "equal_weight",
            "path": f"runs/{review_id}/ai_commentary_context.json",
            "ai_commentary_context": {
                "schema_version": "ai_commentary_context_v1",
                "grounding_phase": "post_compare",
                "client_explanation_draft": {
                    "sentences": [
                        {"topic": "diagnosis", "text": "The current portfolio is concentrated."},
                        {"topic": "current_vs_candidate_comparison", "text": "The tested candidate reduced concentration but added return drag."},
                        {"topic": "decision_verdict", "text": "The verdict is no material rebalance."},
                    ]
                },
                "light_decision_journal": {
                    "decision_verdict": "no_material_rebalance_recommended",
                    "key_assumptions_and_limits": ["Evidence is deterministic."],
                    "next_review_trigger": "Review if concentration rises again.",
                },
                "evidence_references": [
                    {"artifact": "decision_verdict.json", "field_path": "verdict_id"},
                    {"artifact": "current_vs_candidate.json", "field_path": "comparisons[0]"},
                ],
                "source_artifacts": {
                    "decision_verdict": "decision_verdict.json",
                    "monitoring_diff": None,
                },
                "warnings": [],
            },
            "site_explanation_bundle_path": f"runs/{review_id}/site_explanation_bundle.json",
        }
        (run_dir / "ai_commentary_context.json").write_text(
            json.dumps(result["ai_commentary_context"]),
            encoding="utf-8",
        )
        return result

    monkeypatch.setattr(review_service, "safe_review_run_dir", lambda value: run_dir)
    monkeypatch.setattr(
        review_service,
        "write_selected_report_context",
        fake_write_selected_report_context,
    )
    _write_staged_state_for_test(run_dir, review_id, current_stage="report")

    response = _request(
        "POST",
        f"/api/v1/reviews/{review_id}/report",
        json_body={"verdict_id": "no_material_rebalance_recommended"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["stage"] == "report"
    assert body["status"] == "ok"
    assert body["safe_error"] is None
    assert body["lineage"]["verdict_id"] == "no_material_rebalance_recommended"
    assert body["data"]["llm_generated"] is False
    assert body["data"]["report_preview"]["executive_summary"] == "The current portfolio is concentrated."
    assert body["data"]["report_preview"]["comparison_tradeoffs"] == [
        "The tested candidate reduced concentration but added return drag."
    ]
    assert body["data"]["evidence_chain_context"]["selected_diagnosis_id"] == "high_concentration"
    assert body["data"]["evidence_chain_context"]["source_artifacts"] == [
        "decision_verdict",
        "monitoring_diff",
    ]
    assert body["data"]["client_fit"]["status_label"] == "Within stated Client Fit profile"
    assert body["data"]["grounding"]["unavailable_sections"] == ["monitoring_diff"]
    assert {item["kind"] for item in body["data"]["grounding"]["source_refs"]} >= {
        "decision_verdict",
        "current_vs_candidate",
    }
    staged_state = json.loads((run_dir / "review_state.json").read_text(encoding="utf-8"))
    assert staged_state["status"] == "completed"
    assert staged_state["current_stage"] == "report"
    assert staged_state["stages"]["report"]["status"] == "completed"
    assert staged_state["stages"]["report"]["artifact_refs"] == ["ai_commentary_context.json"]


def test_generated_frontend_api_types_match_openapi_schema() -> None:
    schema = app.openapi()
    expected = render_types(schema)
    generated = OUTPUT_PATH.read_text(encoding="utf-8")

    assert generated == expected
    assert '"/api/v1/reviews/{review_id}/report"' in generated
    assert '"/api/v1/reviews/staged"' in generated
    assert '"/api/v1/reviews/{review_id}/status"' in generated
    assert '"createReview"' in generated
    assert '"startStagedReview"' in generated
    assert '"getStagedReviewStatus"' in generated
    assert 'export type CreateReviewRequest = Components["schemas"]["CreateReviewRequest"];' in generated
    assert 'export type StagedReviewStatusResponse = Components["schemas"]["StagedReviewStatusResponse"];' in generated
    assert 'export type ReportResponse = Components["schemas"]["ReportResponse"];' in generated
