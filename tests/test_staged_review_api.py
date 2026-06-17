from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

import httpx
import pytest

from src.api.app import app
import src.api.reviews as review_service


def _request(method: str, path: str, *, json_body: dict | None = None) -> httpx.Response:
    async def _send() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.request(method, path, json=json_body)

    return asyncio.run(_send())


def _portfolio_request(*, sample_mode: bool = False) -> dict:
    return {
        "portfolio": {
            "investor_currency": "USD",
            "holdings": [
                {"type": "instrument", "ticker": "VOO", "weight_pct": 60.0},
                {"type": "instrument", "ticker": "BND", "weight_pct": 40.0},
            ],
        },
        "options": {"mode": "diagnosis_only", "output_profile": "site_api", "sample_mode": sample_mode},
    }


def test_start_staged_review_writes_initial_state_and_returns_immediately(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    review_id = "frontend_review_staged_start"
    run_dir = tmp_path / review_id
    started: list[tuple[str, Path, str]] = []

    monkeypatch.setattr(review_service, "create_run_dir", lambda: (review_id, run_dir))
    monkeypatch.setattr(
        review_service,
        "_start_staged_background_worker",
        lambda review_id, payload_path, *, mode: started.append((review_id, payload_path, mode)),
    )

    response = _request("POST", "/api/v1/reviews/staged", json_body=_portfolio_request())

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "api_version": "v1",
        "schema_version": "review_started_v1",
        "review_id": review_id,
        "stage": "diagnosis",
        "status": "running",
        "current_stage": "input",
        "mode": "live",
        "warnings": [],
        "safe_error": None,
    }
    assert started == [(review_id, run_dir / "payload.json", "live")]
    state = json.loads((run_dir / "review_state.json").read_text(encoding="utf-8"))
    assert state["schema_version"] == "review_state_v1"
    assert state["review_id"] == review_id
    assert state["status"] == "running"
    assert state["current_stage"] == "input"
    assert state["stages"]["input"]["status"] == "running"
    assert state["stages"]["candidate"]["status"] == "pending"
    assert json.loads((run_dir / "payload.json").read_text(encoding="utf-8"))["holdings"][0]["ticker"] == "VOO"
    assert not re.search(r"[A-Z]:[\\/]", json.dumps(body) + json.dumps(state))


def test_start_staged_review_reports_sample_mode_as_demo_qa(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    review_id = "frontend_review_staged_demo"
    run_dir = tmp_path / review_id

    monkeypatch.setattr(review_service, "create_run_dir", lambda: (review_id, run_dir))
    monkeypatch.setattr(review_service, "_start_staged_background_worker", lambda *args, **kwargs: None)

    response = _request("POST", "/api/v1/reviews/staged", json_body=_portfolio_request(sample_mode=True))

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "demo_qa"
    state = json.loads((run_dir / "review_state.json").read_text(encoding="utf-8"))
    assert state["mode"] == "demo_qa"
    assert state["provider_status"]["source"] == "frozen_fixture"


def test_get_staged_review_status_returns_safe_public_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    review_id = "frontend_review_staged_status"
    run_dir = tmp_path / review_id
    run_dir.mkdir()
    state = review_service._initial_staged_state(review_id, mode="live")
    state["status"] = "partial"
    state["current_stage"] = "candidate"
    state["stages"]["xray"] = {
        "status": "completed",
        "started_at": "2026-06-14T08:00:00Z",
        "completed_at": "2026-06-14T08:00:01Z",
        "artifact_refs": ["D:\\secret\\portfolio_xray.json", "analysis_subject/stress_report.json"],
    }
    state["stages"]["candidate"] = {
        "status": "pending",
        "started_at": None,
        "completed_at": None,
        "artifact_refs": ["D:\\secret\\candidate_generation.json"],
    }
    state["artifacts"] = {
        "portfolio_xray": "D:\\secret\\portfolio_xray.json",
        "current_vs_candidate": "D:\\secret\\current_vs_candidate.json",
    }
    review_service._write_staged_state(run_dir, state)

    monkeypatch.setattr(review_service, "safe_review_run_dir", lambda value: run_dir)

    response = _request("GET", f"/api/v1/reviews/{review_id}/status")

    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "review_state_v1"
    assert body["review_id"] == review_id
    assert body["status"] == "partial"
    assert body["current_stage"] == "candidate"
    assert body["stages"]["xray"]["artifact_refs"][0] == "logical://xray"
    assert body["stages"]["candidate"]["status"] == "pending"
    assert body["stages"]["candidate"]["artifact_refs"][0] == "logical://candidate"
    assert body["artifacts"]["portfolio_xray"] == "logical://portfolio_xray"
    assert body["artifacts"]["current_vs_candidate"] == "logical://current_vs_candidate"
    serialized = json.dumps(body)
    assert "Traceback" not in serialized
    assert not re.search(r"[A-Z]:[\\/]", serialized)


def test_get_staged_review_status_missing_state_returns_safe_404(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    review_id = "frontend_review_staged_missing"
    run_dir = tmp_path / review_id
    run_dir.mkdir()

    monkeypatch.setattr(review_service, "safe_review_run_dir", lambda value: run_dir)

    response = _request("GET", f"/api/v1/reviews/{review_id}/status")

    assert response.status_code == 404
    body = response.json()
    assert body["status"] == "failed"
    assert body["safe_error"] == {
        "code": "ARTIFACT_MISSING",
        "message": "Staged review state was not found.",
        "user_action": "none",
        "retryable": False,
        "stage": "input",
    }
    assert "Traceback" not in json.dumps(body)


def test_background_runner_updates_state_after_diagnosis_completion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    review_id = "frontend_review_staged_complete"
    run_dir = tmp_path / review_id
    analysis_subject = run_dir / "analysis_subject"
    analysis_subject.mkdir(parents=True)
    payload_path = run_dir / "payload.json"
    payload_path.write_text(json.dumps(_portfolio_request()["portfolio"]), encoding="utf-8")
    state = review_service._initial_staged_state(review_id, mode="live")
    review_service._write_staged_state(run_dir, state)

    def fake_run_from_payload(
        payload_path: Path,
        *,
        mode: str,
        timeout_seconds: int,
        review_id: str,
        run_dir: Path,
    ) -> tuple[int, Path]:
        assert mode == review_service.MODE_DIAGNOSIS_PLUS_PROBLEM
        assert review_id == "frontend_review_staged_complete"
        for name in [
            "run_metadata.json",
            "portfolio_xray.json",
            "stress_report.json",
            "client_fit_check.json",
            "problem_classification.json",
            "candidate_launchpad.json",
            "portfolio_alternatives_builder.json",
        ]:
            (analysis_subject / name).write_text("{}", encoding="utf-8")
        (run_dir / "input.yml").write_text("tickers: []\n", encoding="utf-8")
        result_path = run_dir / "review_result.json"
        result_path.write_text(
            json.dumps({"review_id": review_id, "status": "completed"}),
            encoding="utf-8",
        )
        return 0, result_path

    monkeypatch.setattr(review_service, "safe_review_run_dir", lambda value: run_dir)
    monkeypatch.setattr(review_service, "run_from_payload", fake_run_from_payload)

    review_service._run_staged_review_background(review_id, payload_path, mode="live")

    updated = json.loads((run_dir / "review_state.json").read_text(encoding="utf-8"))
    assert updated["status"] == "partial"
    assert updated["current_stage"] == "candidate"
    assert updated["stages"]["xray"]["status"] == "completed"
    assert updated["stages"]["launchpad_builder"]["status"] == "completed"
    assert updated["stages"]["candidate"]["status"] == "pending"
    assert updated["artifacts"]["portfolio_xray"] == "analysis_subject/portfolio_xray.json"
    assert updated["safe_error"] is None


def test_demo_qa_background_runner_materializes_fixture_without_live_provider(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    review_id = "frontend_review_staged_demo_fixture"
    run_dir = tmp_path / review_id
    run_dir.mkdir()
    payload_path = run_dir / "payload.json"
    payload_path.write_text(
        json.dumps(
            {
                "investor_currency": "USD",
                "holdings": [
                    {"type": "instrument", "ticker": "VOO", "weight": 60.0},
                    {"type": "instrument", "ticker": "BND", "weight": 40.0},
                ],
            }
        ),
        encoding="utf-8",
    )
    state = review_service._initial_staged_state(review_id, mode="demo_qa")
    review_service._write_staged_state(run_dir, state)

    def fail_live_runner(*args, **kwargs):
        raise AssertionError("demo_qa must not call the live diagnosis runner")

    monkeypatch.setattr(review_service, "safe_review_run_dir", lambda value: run_dir)
    monkeypatch.setattr(review_service, "run_from_payload", fail_live_runner)

    review_service._run_staged_review_background(review_id, payload_path, mode="demo_qa")

    updated = json.loads((run_dir / "review_state.json").read_text(encoding="utf-8"))
    result = json.loads((run_dir / "review_result.json").read_text(encoding="utf-8"))
    assert updated["mode"] == "demo_qa"
    assert updated["status"] == "partial"
    assert updated["current_stage"] == "candidate"
    assert updated["provider_status"] == {
        "source": "frozen_fixture",
        "freshness": "fixed_demo_dataset",
        "message": "Demo / QA mode uses deterministic fixture data and skips external market-data providers.",
    }
    assert updated["stages"]["data_load"]["artifact_refs"] == ["analysis_subject/run_metadata.json"]
    assert updated["stages"]["client_fit"]["status"] == "completed"
    assert updated["artifacts"]["portfolio_xray"] == "analysis_subject/portfolio_xray.json"
    assert result["status"] == "completed"
    assert result["mode"] == "demo_qa"
    assert result["provider_status"]["source"] == "frozen_fixture"
    assert (run_dir / "analysis_subject" / "portfolio_xray.json").is_file()
    assert (run_dir / "analysis_subject" / "stress_report.json").is_file()
    assert (run_dir / "analysis_subject" / "problem_classification.json").is_file()
    serialized = json.dumps(updated)
    assert "Traceback" not in serialized
    assert not re.search(r"[A-Z]:[\\/]", serialized)


def test_background_runner_fails_safely_when_success_result_is_missing_required_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    review_id = "frontend_review_staged_missing_artifact"
    run_dir = tmp_path / review_id
    analysis_subject = run_dir / "analysis_subject"
    analysis_subject.mkdir(parents=True)
    payload_path = run_dir / "payload.json"
    payload_path.write_text(json.dumps(_portfolio_request()["portfolio"]), encoding="utf-8")
    state = review_service._initial_staged_state(review_id, mode="live")
    review_service._write_staged_state(run_dir, state)

    def fake_run_from_payload(
        payload_path: Path,
        *,
        mode: str,
        timeout_seconds: int,
        review_id: str,
        run_dir: Path,
    ) -> tuple[int, Path]:
        (run_dir / "input.yml").write_text("tickers: []\n", encoding="utf-8")
        (analysis_subject / "run_metadata.json").write_text("{}", encoding="utf-8")
        (analysis_subject / "portfolio_xray.json").write_text("{}", encoding="utf-8")
        result_path = run_dir / "review_result.json"
        result_path.write_text(
            json.dumps({"review_id": review_id, "status": "completed"}),
            encoding="utf-8",
        )
        return 0, result_path

    monkeypatch.setattr(review_service, "safe_review_run_dir", lambda value: run_dir)
    monkeypatch.setattr(review_service, "run_from_payload", fake_run_from_payload)

    review_service._run_staged_review_background(review_id, payload_path, mode="live")

    updated = json.loads((run_dir / "review_state.json").read_text(encoding="utf-8"))
    assert updated["status"] == "failed"
    assert updated["current_stage"] == "stress"
    assert updated["stages"]["xray"]["status"] == "completed"
    assert updated["stages"]["stress"]["status"] == "failed"
    assert updated["stages"]["problem_classification"]["status"] == "pending"
    assert updated["safe_error"] == {
        "code": "ARTIFACT_MISSING",
        "message": "Portfolio diagnosis completed but a required staged artifact was not found.",
        "user_action": "retry",
        "retryable": True,
        "stage": "stress",
    }
    assert "analysis_subject/stress_report.json" in updated["warnings"][0]
    assert "D:\\" not in json.dumps(updated)


def test_background_runner_preserves_completed_stages_and_sanitizes_runtime_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    review_id = "frontend_review_staged_runtime_failed"
    run_dir = tmp_path / review_id
    analysis_subject = run_dir / "analysis_subject"
    analysis_subject.mkdir(parents=True)
    payload_path = run_dir / "payload.json"
    payload_path.write_text(json.dumps(_portfolio_request()["portfolio"]), encoding="utf-8")
    state = review_service._initial_staged_state(review_id, mode="live")
    review_service._write_staged_state(run_dir, state)

    def fake_run_from_payload(
        payload_path: Path,
        *,
        mode: str,
        timeout_seconds: int,
        review_id: str,
        run_dir: Path,
    ) -> tuple[int, Path]:
        for name in [
            "run_metadata.json",
            "portfolio_xray.json",
            "stress_report.json",
        ]:
            (analysis_subject / name).write_text("{}", encoding="utf-8")
        (run_dir / "input.yml").write_text("tickers: []\n", encoding="utf-8")
        result_path = run_dir / "review_result.json"
        result_path.write_text(
            json.dumps(
                {
                    "review_id": review_id,
                    "status": "failed",
                    "error": "Traceback (most recent call last): File \"D:\\secret\\stage.py\" failed",
                    "details": ["backend_error"],
                }
            ),
            encoding="utf-8",
        )
        return 1, result_path

    monkeypatch.setattr(review_service, "safe_review_run_dir", lambda value: run_dir)
    monkeypatch.setattr(review_service, "run_from_payload", fake_run_from_payload)

    review_service._run_staged_review_background(review_id, payload_path, mode="live")

    updated = json.loads((run_dir / "review_state.json").read_text(encoding="utf-8"))
    serialized = json.dumps(updated)
    assert updated["status"] == "failed"
    assert updated["stages"]["stress"]["status"] == "completed"
    assert updated["stages"]["problem_classification"]["status"] == "failed"
    assert updated["safe_error"]["code"] == "PYTHON_STAGE_FAILED"
    assert updated["safe_error"]["stage"] == "problem_classification"
    assert "Traceback" not in serialized
    assert "D:\\secret" not in serialized
