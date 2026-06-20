from __future__ import annotations

import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

import src.api.staged_review_state as staged_state_helpers
import src.api.reviews as review_service
from src.api.models import StagedProviderStatus
from src.api.staged_review_state import (
    ReviewAccessError,
    StagedReviewStateStore,
    public_staged_status_from_state,
    review_case_status_projection_from_state,
    review_case_screen_read_model_from_public_status,
    review_case_screen_read_model_from_state,
    staged_status_not_found,
)


PROVIDER_STATUS = {
    "live": StagedProviderStatus(
        source="live_provider",
        freshness="pending",
        message="Live mode uses the normal market-data provider path.",
    ),
    "demo_qa": StagedProviderStatus(
        source="frozen_fixture",
        freshness="fixed_demo_dataset",
        message="Demo / QA mode uses deterministic fixture data and skips external market-data providers.",
    ),
}


def _initial_state(review_id: str, *, owner_id: str | None = "owner_a") -> dict:
    return review_service._initial_staged_state(review_id, mode="live", owner_id=owner_id)


def test_staged_review_state_store_reads_writes_and_rejects_wrong_schema(tmp_path: Path) -> None:
    store = StagedReviewStateStore(schema_version="review_state_v1")
    state = _initial_state("review_state_store_case")

    store.write(tmp_path, state)

    stored_path = tmp_path / "review_state.json"
    assert stored_path.is_file()
    loaded = store.read(tmp_path)
    assert loaded["schema_version"] == "review_state_v1"
    assert loaded["review_id"] == "review_state_store_case"
    assert re.match(r"\d{4}-\d{2}-\d{2}T", loaded["updated_at"])

    loaded["schema_version"] = "old_state"
    stored_path.write_text(json.dumps(loaded), encoding="utf-8")
    with pytest.raises(ValueError, match="review_state_v1"):
        store.read(tmp_path)
    assert store.read_optional(tmp_path) is None


def test_staged_review_state_store_authorizes_owner_with_run_local_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    review_id = "review_state_store_owner"
    store = StagedReviewStateStore(schema_version="review_state_v1")
    store.write(tmp_path, _initial_state(review_id, owner_id="owner_a"))
    monkeypatch.setattr(staged_state_helpers, "safe_review_run_dir", lambda value: tmp_path)

    run_dir, state = store.read_authorized(review_id, "owner_a")

    assert run_dir == tmp_path
    assert state["owner_id"] == "owner_a"
    with pytest.raises(ReviewAccessError) as mismatch:
        store.read_authorized(review_id, "owner_b")
    assert mismatch.value.status_code == 403
    assert mismatch.value.code == "review_forbidden"

    ownerless_state = _initial_state(review_id, owner_id="owner_a")
    ownerless_state["owner_id"] = None
    store.write(tmp_path, ownerless_state)
    with pytest.raises(ReviewAccessError, match="Review owner is missing"):
        store.read_authorized(review_id, "owner_a")


def test_public_staged_status_projection_sanitizes_legacy_raw_refs() -> None:
    state = _initial_state("review_state_public_case")
    state["status"] = "partial"
    state["current_stage"] = "candidate"
    state["warnings"] = ["ok", ""]
    state["stages"]["xray"]["status"] = "completed"
    state["stages"]["xray"]["artifact_refs"] = [
        "D:\\secret\\portfolio_xray.json",
        "analysis_subject/portfolio_xray.json",
    ]
    state["artifacts"] = {
        "portfolio_xray": "D:\\secret\\portfolio_xray.json",
        "stress_report": "analysis_subject/stress_report.json",
    }
    state["safe_error"] = {
        "code": "PYTHON_STAGE_FAILED",
        "message": "Traceback in D:\\secret\\worker.py",
        "user_action": "retry",
        "retryable": True,
        "stage": "xray",
    }

    response = public_staged_status_from_state(
        state,
        schema_version="review_state_v1",
        initial_provider_status=PROVIDER_STATUS,
    )
    body = response.model_dump(mode="json")

    assert body["schema_version"] == "review_state_v1"
    assert body["status"] == "partial"
    assert body["current_stage"] == "candidate"
    assert body["stages"]["xray"]["artifact_refs"] == [
        "logical://xray",
        "analysis_subject/portfolio_xray.json",
    ]
    assert body["artifacts"] == {
        "portfolio_xray": "logical://portfolio_xray",
        "stress_report": "analysis_subject/stress_report.json",
    }
    assert body["warnings"] == ["ok"]
    serialized = json.dumps(body)
    assert "D:\\secret" not in serialized
    assert not re.search(r"[A-Z]:[\\/]", serialized)


def test_public_staged_status_projects_to_review_case_screen_read_model() -> None:
    state = _initial_state("review_state_screen_model_case")
    state["status"] = "partial"
    state["current_stage"] = "stress"
    state["stages"]["xray"].update(
        {
            "status": "completed",
            "started_at": "2026-06-20T08:01:00Z",
            "completed_at": "2026-06-20T08:02:00Z",
            "artifact_refs": [
                "D:\\private\\portfolio_xray.json",
                "analysis_subject/portfolio_xray.json",
            ],
        }
    )
    state["artifacts"] = {
        "portfolio_xray": "D:\\private\\portfolio_xray.json",
        "stress_report": "analysis_subject/stress_report.json",
    }

    response = public_staged_status_from_state(
        state,
        schema_version="review_state_v1",
        initial_provider_status=PROVIDER_STATUS,
    )
    model = review_case_screen_read_model_from_public_status(response)
    serialized = model.to_dict()

    assert serialized["schema_version"] == "review_case_screen_read_model_v1"
    assert serialized["review_id"] == "review_state_screen_model_case"
    assert serialized["progress"] == {
        "total_stage_count": 11,
        "terminal_stage_count": 1,
        "active_stage": "stress",
    }
    assert serialized["stages"][2]["artifact_refs"] == [
        "logical://xray",
        "analysis_subject/portfolio_xray.json",
    ]
    assert {
        "key": "portfolio_xray",
        "ref": "logical://portfolio_xray",
        "available": True,
        "producing_stages": [],
        "evidence_source_ids": [],
    } in serialized["artifacts"]
    assert "D:\\private" not in json.dumps(serialized)


def test_raw_state_projects_to_screen_read_model_through_public_sanitizer() -> None:
    state = _initial_state("review_state_raw_screen_model_case")
    state["current_stage"] = "xray"
    state["stages"]["input"]["status"] = "completed"
    state["stages"]["input"]["artifact_refs"] = ["C:\\secret\\payload.json"]

    model = review_case_screen_read_model_from_state(
        state,
        schema_version="review_state_v1",
        initial_provider_status=PROVIDER_STATUS,
    )
    serialized = model.to_dict()

    assert serialized["current_stage"] == "xray"
    assert serialized["stages"][0]["artifact_refs"] == ["logical://input"]
    assert "C:\\secret" not in json.dumps(serialized)


def test_review_case_status_projection_pairs_public_status_and_internal_read_model() -> None:
    state = _initial_state("review_state_projection_case")
    state["status"] = "partial"
    state["current_stage"] = "stress"
    state["stages"]["input"]["status"] = "completed"
    state["stages"]["xray"]["status"] = "completed"
    state["stages"]["xray"]["artifact_refs"] = [
        "C:\\private\\portfolio_xray.json",
        "analysis_subject/portfolio_xray.json",
    ]
    state["artifacts"] = {
        "portfolio_xray": "C:\\private\\portfolio_xray.json",
        "stress_report": "analysis_subject/stress_report.json",
    }

    expected_public = public_staged_status_from_state(
        state,
        schema_version="review_state_v1",
        initial_provider_status=PROVIDER_STATUS,
    )
    projection = review_case_status_projection_from_state(
        state,
        schema_version="review_state_v1",
        initial_provider_status=PROVIDER_STATUS,
        owner_id="owner_a",
    )

    assert projection.public_status.model_dump(mode="json") == expected_public.model_dump(mode="json")
    serialized_model = projection.screen_read_model.to_dict()
    assert serialized_model["review_id"] == "review_state_projection_case"
    assert serialized_model["progress"] == {
        "total_stage_count": 11,
        "terminal_stage_count": 2,
        "active_stage": "stress",
    }
    assert serialized_model["stages"][2]["artifact_refs"] == [
        "logical://xray",
        "analysis_subject/portfolio_xray.json",
    ]
    assert "C:\\private" not in json.dumps(serialized_model)


def test_fastapi_public_status_wrapper_uses_review_case_status_projection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _initial_state("review_state_fastapi_wrapper_case")
    expected_public = public_staged_status_from_state(
        state,
        schema_version="review_state_v1",
        initial_provider_status=PROVIDER_STATUS,
    )
    captured: dict[str, object] = {}

    def fake_projection(raw_state: dict, **kwargs: object) -> SimpleNamespace:
        captured["state"] = raw_state
        captured["kwargs"] = kwargs
        return SimpleNamespace(public_status=expected_public)

    monkeypatch.setattr(review_service, "review_case_status_projection_from_state", fake_projection)

    response = review_service._public_staged_status_from_state(state)

    assert response is expected_public
    assert captured["state"] is state
    assert captured["kwargs"] == {
        "schema_version": "review_state_v1",
        "initial_provider_status": review_service.STAGED_INITIAL_PROVIDER_STATUS,
    }


def test_staged_status_not_found_uses_safe_failed_envelope() -> None:
    response = staged_status_not_found(
        "missing_review",
        "Staged review state was not found.",
        schema_version="review_state_v1",
        initial_provider_status=PROVIDER_STATUS["live"],
    )
    body = response.model_dump(mode="json")

    assert body["status"] == "failed"
    assert body["current_stage"] == "input"
    assert body["safe_error"] == {
        "code": "ARTIFACT_MISSING",
        "message": "Staged review state was not found.",
        "user_action": "none",
        "retryable": False,
        "stage": "input",
    }
