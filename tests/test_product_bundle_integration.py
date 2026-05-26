"""Offline integration gate for the Core MVP product-facing JSON bundle."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from src.candidate_comparison import write_candidate_comparison_outputs
from src.config_schema import PortfolioConfig, validate_config
from src.product_bundle_paths import PRODUCT_BUNDLE_MANIFEST_KEYS
from mvp_offline_fixtures import (
    DEFAULT_ANALYSIS_END,
    PRODUCT_BUNDLE_ARTIFACTS,
    seed_product_bundle_offline_workspace,
)


def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*_args, **_kwargs):
        raise AssertionError("product bundle integration test must not use live network data")

    import src.data_fred as data_fred
    import src.data_yf as data_yf

    monkeypatch.setattr(data_yf, "download_all", _boom)
    monkeypatch.setattr(data_fred, "fetch_fred_series", _boom, raising=False)


def _cfg() -> PortfolioConfig:
    return validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND", "GLD"],
            "analysis_subject": {
                "type": "current_portfolio",
                "display_name": "Product bundle offline subject",
                "weights": {"VOO": 0.55, "BND": 0.35, "GLD": 0.10},
            },
        }
    )


def _load(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def test_product_bundle_offline_after_compare_writes_six_artifacts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """analysis_subject diagnosis + one candidate -> compare emits full product bundle."""
    _block_network(monkeypatch)
    cfg = _cfg()
    seeded = seed_product_bundle_offline_workspace(tmp_path, cfg)
    main_dir = seeded["main_dir"]

    paths = write_candidate_comparison_outputs(cfg, project_root=tmp_path)
    assert paths.get("candidate_comparison_json") is not None

    missing: list[str] = []
    for rel_path, schema_version in PRODUCT_BUNDLE_ARTIFACTS:
        artifact_path = main_dir / rel_path
        if not artifact_path.is_file():
            missing.append(rel_path)
            continue
        doc = _load(artifact_path)
        assert doc.get("schema_version") == schema_version, rel_path

    assert not missing, (
        "Product bundle artifacts missing after write_candidate_comparison_outputs: "
        + ", ".join(missing)
    )

    current_vs = _load(main_dir / "current_vs_candidate.json")
    assert current_vs["view_mode"] in ("one_candidate", "shortlist", "diagnosis_only")
    assert current_vs["diagnostic_only"] is True
    if current_vs["view_mode"] == "one_candidate":
        assert len(current_vs.get("comparisons") or []) == 1

    launchpad = _load(main_dir / "analysis_subject/candidate_launchpad.json")
    assert launchpad["diagnostic_only"] is True
    assert launchpad.get("analysis_end") == DEFAULT_ANALYSIS_END

    problem = _load(main_dir / "analysis_subject/problem_classification.json")
    assert problem["diagnostic_only"] is True
    assert problem.get("problems")

    ai_ctx = _load(main_dir / "ai_commentary_context.json")
    assert ai_ctx.get("purpose") == "grounded_ai_commentary_context"
    assert ai_ctx.get("guardrails", {}).get("does_not_call_llm") is True

    verdict = _load(main_dir / "decision_verdict.json")
    assert verdict.get("verdict_id")
    assert verdict.get("source_artifacts", {}).get("selection_decision") == "selection_decision.json"

    what_changed = _load(main_dir / "what_changed_summary.json")
    assert what_changed["schema_version"] == "what_changed_summary_v1"
    assert what_changed.get("source_artifacts", {}).get("problem_classification") == (
        "problem_classification.json"
    )
    assert what_changed.get("problem_ids"), (
        "what_changed_summary must resolve problem ids from analysis_subject sidecar"
    )

    assert (main_dir / "problem_classification.json").is_file() is False
    assert (main_dir / "candidate_launchpad.json").is_file() is False

    assert ai_ctx.get("source_artifacts", {}).get("problem_classification") == (
        "problem_classification.json"
    )
    assert ai_ctx.get("source_artifacts", {}).get("candidate_launchpad") == (
        "candidate_launchpad.json"
    )
    evidence = {(r.get("artifact"), r.get("field_path")) for r in ai_ctx.get("evidence_references") or []}
    assert ("problem_classification.json", "problems[0]") in evidence
    assert ("candidate_launchpad.json", "cards[0]") in evidence

    manifest = _load(main_dir / "output_manifest.json")
    generated = manifest.get("generated_paths") or {}
    assert manifest.get("advanced_package_generated") is True
    assert manifest.get("primary_output_surface") == "product_bundle"
    assert manifest.get("product_bundle_manifest_keys") == list(PRODUCT_BUNDLE_MANIFEST_KEYS)
    assert list(generated)[: len(PRODUCT_BUNDLE_MANIFEST_KEYS)] == list(
        PRODUCT_BUNDLE_MANIFEST_KEYS
    )
    for key in PRODUCT_BUNDLE_MANIFEST_KEYS:
        assert key in generated, f"output_manifest missing product bundle key: {key}"
    assert "analysis_subject/problem_classification.json" in generated[
        "problem_classification_json"
    ]
    assert "analysis_subject/candidate_launchpad.json" in generated[
        "candidate_launchpad_json"
    ]
    categories = manifest.get("artifact_categories") or {}
    assert categories.get("product_bundle") == list(PRODUCT_BUNDLE_MANIFEST_KEYS)
    assert "candidate_comparison_json" in (categories.get("technical_comparison") or [])
    assert "portfolio_health_score_json" in (categories.get("advanced_evidence") or [])
    assert "run_result_json" in (categories.get("legacy_compatibility") or [])
    by_category = manifest.get("generated_paths_by_category") or {}
    assert by_category.get("product_bundle")
    discovery = manifest.get("product_discovery") or {}
    assert discovery.get("primary_output_surface") == "product_bundle"
    assert discovery.get("product_bundle_complete") is True
    assert set((discovery.get("product_bundle_paths") or {}).keys()) == set(
        PRODUCT_BUNDLE_MANIFEST_KEYS
    )
