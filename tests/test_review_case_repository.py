from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.review_case import (
    ReviewCase,
    ReviewCaseRepositoryError,
    ReviewCaseValidationError,
    RunLocalReviewCaseRepository,
)


def _case(review_id: str = "frontend_review_repository") -> ReviewCase:
    return ReviewCase.initial(
        review_id,
        mode="live",
        owner_id="local-dev-user",
        now="2026-06-19T13:00:00Z",
        provider_status={
            "source": "live_provider",
            "freshness": "pending",
            "message": "Live mode uses the normal market-data provider path.",
        },
    )


def test_run_local_repository_saves_and_loads_review_case(tmp_path: Path) -> None:
    repository = RunLocalReviewCaseRepository(tmp_path, schema_version="review_state_v1")

    repository.save(_case())

    state_path = tmp_path / "review_state.json"
    assert state_path.is_file()
    assert not (tmp_path / "review_state.json.tmp").exists()
    raw_state = json.loads(state_path.read_text(encoding="utf-8"))
    assert raw_state["schema_version"] == "review_state_v1"
    assert raw_state["review_id"] == "frontend_review_repository"
    assert raw_state["stages"]["input"]["artifact_refs"] == ["payload.json"]

    loaded = repository.load()

    assert loaded == _case()


def test_run_local_repository_load_optional_returns_none_when_missing(tmp_path: Path) -> None:
    repository = RunLocalReviewCaseRepository(tmp_path, schema_version="review_state_v1")

    assert repository.load_optional() is None


def test_run_local_repository_rejects_wrong_schema_version(tmp_path: Path) -> None:
    repository = RunLocalReviewCaseRepository(tmp_path, schema_version="review_state_v1")
    (tmp_path / "review_state.json").write_text(
        json.dumps({"schema_version": "old_state_v0"}),
        encoding="utf-8",
    )

    with pytest.raises(ReviewCaseValidationError, match="unexpected schema version"):
        repository.load()


def test_run_local_repository_rejects_invalid_json_shape(tmp_path: Path) -> None:
    repository = RunLocalReviewCaseRepository(tmp_path, schema_version="review_state_v1")
    (tmp_path / "review_state.json").write_text("[]", encoding="utf-8")

    with pytest.raises(ReviewCaseRepositoryError, match="JSON object"):
        repository.load()
