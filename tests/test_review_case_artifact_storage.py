from __future__ import annotations

import pytest

from src.review_case import (
    ReviewCaseArtifactStorageError,
    review_case_artifact_object_key,
    review_case_artifact_storage_backend,
    review_case_artifact_storage_config,
    run_local_review_case_artifact_storage,
)


def test_default_artifact_storage_backend_is_run_local_when_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PMRI_REVIEW_CASE_ARTIFACT_STORAGE_BACKEND", raising=False)

    config = review_case_artifact_storage_config()

    assert review_case_artifact_storage_backend() == "run_local"
    assert config.operational_metadata() == {
        "backend": "run_local",
        "requested_backend": "run_local",
        "key_prefix": "review-cases",
        "bucket_configured": False,
        "endpoint_url_configured": False,
        "warnings": [],
    }


def test_run_local_artifact_storage_builds_manifest_from_existing_files(tmp_path) -> None:
    (tmp_path / "analysis_subject").mkdir()
    (tmp_path / "analysis_subject" / "portfolio_xray.json").write_text("{}", encoding="utf-8")
    (tmp_path / "decision_verdict.json").write_text("{}", encoding="utf-8")

    manifest = run_local_review_case_artifact_storage().manifest_from_existing_refs(
        tmp_path,
        {
            "portfolio_xray": "analysis_subject/portfolio_xray.json",
            "stress_report": "analysis_subject/stress_report.json",
            "decision_verdict": "decision_verdict.json",
        },
    )

    assert manifest.to_public_artifacts_map() == {
        "portfolio_xray": "analysis_subject/portfolio_xray.json",
        "decision_verdict": "decision_verdict.json",
    }


def test_run_local_artifact_storage_preserves_safe_existing_reference(tmp_path) -> None:
    (tmp_path / "analysis_subject").mkdir()
    (tmp_path / "analysis_subject" / "stress_report.json").write_text("{}", encoding="utf-8")

    storage = run_local_review_case_artifact_storage()

    assert storage.reference_for_artifact(
        tmp_path,
        "stress_report",
        "analysis_subject/stress_report.json",
    ) == "analysis_subject/stress_report.json"
    assert storage.artifact_exists(tmp_path, "logical://fallback") is False


def test_artifact_object_key_is_stable_and_safe_for_future_remote_storage() -> None:
    assert review_case_artifact_object_key(
        "frontend_review_20260620T120000Z",
        "analysis_subject/portfolio_xray.json",
        key_prefix="prod/review-cases",
    ) == "prod/review-cases/frontend_review_20260620T120000Z/analysis_subject/portfolio_xray.json"


@pytest.mark.parametrize(
    ("review_id", "artifact_ref", "key_prefix"),
    [
        ("frontend/review", "analysis_subject/portfolio_xray.json", "review-cases"),
        ("frontend_review", "logical://portfolio_xray", "review-cases"),
        ("frontend_review", "../portfolio_xray.json", "review-cases"),
        ("frontend_review", "analysis_subject/portfolio_xray.json", "../review-cases"),
        ("frontend_review", "analysis_subject/portfolio_xray.json", "review cases"),
    ],
)
def test_artifact_object_key_rejects_unsafe_inputs(
    review_id: str,
    artifact_ref: str,
    key_prefix: str,
) -> None:
    with pytest.raises(ReviewCaseArtifactStorageError):
        review_case_artifact_object_key(review_id, artifact_ref, key_prefix=key_prefix)


def test_remote_artifact_storage_opt_in_is_inactive_and_falls_back_to_run_local() -> None:
    config = review_case_artifact_storage_config(
        {
            "PMRI_REVIEW_CASE_ARTIFACT_STORAGE_BACKEND": "r2",
            "PMRI_REVIEW_CASE_ARTIFACT_BUCKET": "pmri-review-cases",
            "PMRI_REVIEW_CASE_ARTIFACT_ENDPOINT_URL": "https://example.r2.cloudflarestorage.com",
            "PMRI_REVIEW_CASE_ARTIFACT_KEY_PREFIX": "prod/reviews",
        }
    )

    assert config.backend == "run_local"
    assert config.requested_backend == "r2"
    assert config.key_prefix == "prod/reviews"
    assert config.warnings == ("remote_artifact_storage_inactive",)
    assert config.operational_metadata() == {
        "backend": "run_local",
        "requested_backend": "r2",
        "key_prefix": "prod/reviews",
        "bucket_configured": True,
        "endpoint_url_configured": True,
        "warnings": ["remote_artifact_storage_inactive"],
    }


def test_artifact_storage_config_sanitizes_unsupported_backend_and_invalid_values() -> None:
    config = review_case_artifact_storage_config(
        {
            "PMRI_REVIEW_CASE_ARTIFACT_STORAGE_BACKEND": "ftp",
            "PMRI_REVIEW_CASE_ARTIFACT_BUCKET": "../secret",
            "PMRI_REVIEW_CASE_ARTIFACT_KEY_PREFIX": "../bad prefix",
        }
    )

    assert config.backend == "run_local"
    assert config.requested_backend == "ftp"
    assert config.key_prefix == "review-cases"
    assert config.bucket_name is None
    assert config.warnings == (
        "unsupported_artifact_storage_backend",
        "invalid_artifact_key_prefix",
        "invalid_artifact_bucket_name",
    )
