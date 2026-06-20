from __future__ import annotations

import pytest

from src.review_case import (
    ReviewCaseArtifactManifest,
    ReviewCaseArtifactManifestError,
)


def test_artifact_manifest_preserves_public_artifacts_map_shape() -> None:
    manifest = ReviewCaseArtifactManifest.from_mapping(
        {
            "portfolio_xray": "analysis_subject/portfolio_xray.json",
            "current_vs_candidate": "current_vs_candidate.json",
            "fallback": "logical://fallback",
        }
    )

    assert manifest.to_public_artifacts_map() == {
        "portfolio_xray": "analysis_subject/portfolio_xray.json",
        "current_vs_candidate": "current_vs_candidate.json",
        "fallback": "logical://fallback",
    }


@pytest.mark.parametrize(
    "bad_key",
    ["", " ", "../portfolio_xray", "analysis_subject/portfolio_xray", "portfolio\\xray"],
)
def test_artifact_manifest_rejects_unsafe_keys(bad_key: str) -> None:
    with pytest.raises(ReviewCaseArtifactManifestError):
        ReviewCaseArtifactManifest.from_mapping({bad_key: "analysis_subject/portfolio_xray.json"})


@pytest.mark.parametrize(
    "bad_ref",
    [
        "",
        "C:/Users/example/secret.json",
        "C:\\Users\\example\\secret.json",
        "/home/example/secret.json",
        "../outside.json",
        "analysis_subject/../outside.json",
    ],
)
def test_artifact_manifest_rejects_unsafe_refs(bad_ref: str) -> None:
    with pytest.raises(ReviewCaseArtifactManifestError):
        ReviewCaseArtifactManifest.from_mapping({"portfolio_xray": bad_ref})


def test_artifact_manifest_builds_existing_run_local_public_map(tmp_path) -> None:
    (tmp_path / "analysis_subject").mkdir()
    (tmp_path / "analysis_subject" / "portfolio_xray.json").write_text("{}", encoding="utf-8")
    (tmp_path / "current_vs_candidate.json").write_text("{}", encoding="utf-8")

    manifest = ReviewCaseArtifactManifest.from_existing_run_local_refs(
        tmp_path,
        {
            "portfolio_xray": "analysis_subject/portfolio_xray.json",
            "stress_report": "analysis_subject/stress_report.json",
            "current_vs_candidate": "current_vs_candidate.json",
        },
    )

    assert manifest.to_public_artifacts_map() == {
        "portfolio_xray": "analysis_subject/portfolio_xray.json",
        "current_vs_candidate": "current_vs_candidate.json",
    }
