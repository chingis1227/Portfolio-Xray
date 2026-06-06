"""Unit tests for diagnosis bundle path resolution (RM-ARCH-011)."""

from __future__ import annotations

import json
from pathlib import Path

from src.block_2_2_portfolio_metrics import BLOCK_2_2_ID
from src.block_2_3_factor_exposure import BLOCK_2_3_ID
from src.block_2_4_hidden_exposure import BLOCK_2_4_ID
from src.block_2_5_risk_budget_view import BLOCK_2_5_ID
from src.block_2_6_portfolio_weakness_map import BLOCK_2_6_ID
from src.product_bundle_paths import (
    ADVANCED_EVIDENCE_MANIFEST_KEYS,
    LEGACY_COMPATIBILITY_MANIFEST_KEYS,
    PRODUCT_BUNDLE_DIAGNOSIS_MANIFEST_KEYS,
    PRODUCT_BUNDLE_POST_COMPARE_MANIFEST_KEYS,
    PORTFOLIO_XRAY_BLOCK_2_2_KEY,
    PORTFOLIO_XRAY_BLOCK_2_3_KEY,
    PORTFOLIO_XRAY_BLOCK_2_4_KEY,
    PORTFOLIO_XRAY_BLOCK_2_5_KEY,
    PORTFOLIO_XRAY_BLOCK_2_6_KEY,
    PRODUCT_BUNDLE_MANIFEST_KEYS,
    build_generated_paths_by_category,
    build_output_manifest_discovery_extra,
    build_product_first_generated_paths,
    discover_paths_by_category,
    discover_product_bundle_paths,
    load_diagnosis_bundle_docs,
    manifest_key_category,
    product_bundle_artifact_categories,
    product_bundle_generated_paths_for_manifest,
    portfolio_xray_has_block_2_2,
    portfolio_xray_has_block_2_3,
    portfolio_xray_has_block_2_4,
    portfolio_xray_has_block_2_5,
    portfolio_xray_has_block_2_6,
    product_bundle_manifest_extra,
    resolve_candidate_launchpad_path,
    resolve_problem_classification_path,
)
from mvp_offline_fixtures import seed_analysis_subject_diagnosis_bundle, write_json


def _write_problem(root: Path, *, subdir: str | None, problem_id: str) -> None:
    payload = {
        "schema_version": "problem_classification_v1",
        "diagnostic_only": True,
        "problems": [{"problem_id": problem_id, "severity": "medium", "status": "open"}],
    }
    if subdir:
        write_json(root / subdir / "problem_classification.json", payload)
    else:
        write_json(root / "problem_classification.json", payload)


def _write_launchpad(root: Path, *, subdir: str | None, card_id: str) -> None:
    payload = {
        "schema_version": "candidate_launchpad_v1",
        "diagnostic_only": True,
        "cards": [{"card_id": card_id, "goal": "reduce_volatility", "method_id": "risk_parity"}],
    }
    if subdir:
        write_json(root / subdir / "candidate_launchpad.json", payload)
    else:
        write_json(root / "candidate_launchpad.json", payload)


def test_resolve_problem_classification_prefers_sidecar(tmp_path: Path) -> None:
    _write_problem(tmp_path, subdir="analysis_subject", problem_id="sidecar_problem")
    _write_problem(tmp_path, subdir=None, problem_id="root_problem")

    path = resolve_problem_classification_path(tmp_path)
    assert path is not None
    assert path.parent.name == "analysis_subject"
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["problems"][0]["problem_id"] == "sidecar_problem"


def test_resolve_problem_classification_falls_back_to_root(tmp_path: Path) -> None:
    _write_problem(tmp_path, subdir=None, problem_id="legacy_root")

    path = resolve_problem_classification_path(tmp_path)
    assert path == tmp_path / "problem_classification.json"


def test_resolve_candidate_launchpad_prefers_sidecar(tmp_path: Path) -> None:
    _write_launchpad(tmp_path, subdir="analysis_subject", card_id="sidecar_card")
    _write_launchpad(tmp_path, subdir=None, card_id="root_card")

    path = resolve_candidate_launchpad_path(tmp_path)
    assert path is not None
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["cards"][0]["card_id"] == "sidecar_card"


def test_load_diagnosis_bundle_docs_sidecar_only(tmp_path: Path) -> None:
    subject = tmp_path / "analysis_subject"
    seed_analysis_subject_diagnosis_bundle(subject)

    bundle = load_diagnosis_bundle_docs(tmp_path)
    assert bundle["problem_classification_resolution"] == "sidecar"
    assert bundle["candidate_launchpad_resolution"] == "sidecar"
    assert isinstance(bundle["problem_classification"], dict)
    assert isinstance(bundle["candidate_launchpad"], dict)
    assert (tmp_path / "problem_classification.json").is_file() is False


def test_product_bundle_generated_paths_for_manifest_sidecar(tmp_path: Path) -> None:
    subject = tmp_path / "analysis_subject"
    seed_analysis_subject_diagnosis_bundle(subject)
    (tmp_path / "current_vs_candidate.json").write_text("{}", encoding="utf-8")

    paths = product_bundle_generated_paths_for_manifest(tmp_path)
    assert set(paths.keys()) >= {
        "problem_classification_json",
        "candidate_launchpad_json",
        "current_vs_candidate_json",
    }
    assert "analysis_subject/problem_classification.json" in paths[
        "problem_classification_json"
    ]
    assert paths.keys() <= set(PRODUCT_BUNDLE_MANIFEST_KEYS)


def test_product_bundle_artifact_categories_lists_bundle_keys() -> None:
    categories = product_bundle_artifact_categories()
    assert categories["product_bundle"] == list(PRODUCT_BUNDLE_MANIFEST_KEYS)
    assert "candidate_comparison_json" in categories["technical_comparison"]
    assert "portfolio_health_score_json" in categories["advanced_evidence"]
    assert tuple(categories["advanced_evidence"]) == ADVANCED_EVIDENCE_MANIFEST_KEYS
    assert "run_result_json" in categories["legacy_compatibility"]
    assert tuple(categories["legacy_compatibility"]) == LEGACY_COMPATIBILITY_MANIFEST_KEYS
    assert categories["generated_export"] == ["*_csv", "*_txt", "*_html", "*_png", "*_pdf"]


def test_manifest_key_category_classifies_exports_and_legacy() -> None:
    assert manifest_key_category("decision_verdict_json") == "product_bundle"
    assert manifest_key_category("candidate_comparison_json") == "technical_comparison"
    assert manifest_key_category("portfolio_health_score_json") == "advanced_evidence"
    assert manifest_key_category("portfolio_comparison_json") == "legacy_compatibility"
    assert manifest_key_category("candidate_comparison_txt") == "generated_export"
    assert manifest_key_category("run_metadata") == "subject_diagnostics"


def test_build_generated_paths_by_category_buckets_paths() -> None:
    generated = {
        "problem_classification_json": "Main portfolio/analysis_subject/problem_classification.json",
        "candidate_comparison_json": "Main portfolio/candidate_comparison.json",
        "portfolio_health_score_json": "Main portfolio/portfolio_health_score.json",
        "portfolio_comparison_json": "Main portfolio/portfolio_comparison.json",
        "candidate_comparison_txt": "Main portfolio/candidate_comparison.txt",
        "run_metadata": "Main portfolio/run_metadata.json",
    }
    by_category = build_generated_paths_by_category(generated)
    assert set(by_category["product_bundle"]) == {"problem_classification_json"}
    assert "candidate_comparison_json" in by_category["technical_comparison"]
    assert "portfolio_health_score_json" in by_category["advanced_evidence"]
    assert "portfolio_comparison_json" in by_category["legacy_compatibility"]
    assert "candidate_comparison_txt" in by_category["generated_export"]
    assert "run_metadata" in by_category["subject_diagnostics"]


def test_build_output_manifest_discovery_extra_includes_product_discovery() -> None:
    generated = {
        "problem_classification_json": "Main portfolio/analysis_subject/problem_classification.json",
        "current_vs_candidate_json": "Main portfolio/current_vs_candidate.json",
        "candidate_comparison_json": "Main portfolio/candidate_comparison.json",
    }
    extra = build_output_manifest_discovery_extra(generated)
    discovery = extra["product_discovery"]
    assert discovery["primary_output_surface"] == "product_bundle"
    assert discovery["product_bundle_complete"] is False
    assert discovery["product_bundle_phase"] == "post_compare_partial"
    assert discovery["diagnosis_bundle_complete"] is False
    assert discovery["post_compare_bundle_complete"] is False
    assert discovery["product_bundle_paths"]["current_vs_candidate_json"].endswith(
        "current_vs_candidate.json"
    )
    assert "product_bundle" in extra["generated_paths_by_category"]
    assert "technical_comparison" in extra["generated_paths_by_category"]


def test_build_product_discovery_diagnosis_only_phase(tmp_path: Path) -> None:
    subject = tmp_path / "analysis_subject"
    seed_analysis_subject_diagnosis_bundle(subject)
    from src.product_bundle_paths import build_product_discovery_block

    discovery = build_product_discovery_block(
        product_bundle_generated_paths_for_manifest(tmp_path)
    )
    assert discovery["product_bundle_phase"] == "diagnosis_only"
    assert discovery["diagnosis_bundle_complete"] is True
    assert discovery["post_compare_bundle_complete"] is False
    assert discovery["product_bundle_complete"] is False
    assert set(discovery["diagnosis_bundle_paths"]) == set(PRODUCT_BUNDLE_DIAGNOSIS_MANIFEST_KEYS)
    assert discovery["post_compare_bundle_paths"] == {}


def test_build_product_discovery_complete_phase(tmp_path: Path) -> None:
    subject = tmp_path / "analysis_subject"
    seed_analysis_subject_diagnosis_bundle(subject)
    for name in ("current_vs_candidate.json", "decision_verdict.json", "ai_commentary_context.json", "what_changed_summary.json"):
        (tmp_path / name).write_text("{}", encoding="utf-8")
    from src.product_bundle_paths import build_product_discovery_block

    discovery = build_product_discovery_block(
        product_bundle_generated_paths_for_manifest(tmp_path)
    )
    assert discovery["product_bundle_phase"] == "complete"
    assert discovery["product_bundle_complete"] is True
    assert set(discovery["post_compare_bundle_paths"]) == set(
        PRODUCT_BUNDLE_POST_COMPARE_MANIFEST_KEYS
    )


def test_product_bundle_manifest_extra_declares_diagnosis_vs_post_compare() -> None:
    extra = product_bundle_manifest_extra()
    contract = extra["product_bundle_contract"]
    assert contract["diagnosis_artifact_keys"] == list(PRODUCT_BUNDLE_DIAGNOSIS_MANIFEST_KEYS)
    assert contract["post_compare_artifact_keys"] == list(
        PRODUCT_BUNDLE_POST_COMPARE_MANIFEST_KEYS
    )


def test_discover_product_bundle_paths_prefers_product_discovery_block() -> None:
    manifest = {
        "generated_paths": {
            "problem_classification_json": "legacy/generated_paths/should_not_win.json",
        },
        "product_discovery": {
            "product_bundle_paths": {
                "problem_classification_json": (
                    "Main portfolio/analysis_subject/problem_classification.json"
                ),
            },
        },
    }
    paths = discover_product_bundle_paths(manifest)
    assert paths["problem_classification_json"].endswith(
        "analysis_subject/problem_classification.json"
    )


def test_discover_paths_by_category_rebuilds_from_generated_paths() -> None:
    manifest = {
        "generated_paths": {
            "decision_verdict_json": "Main portfolio/decision_verdict.json",
            "selection_decision_json": "Main portfolio/selection_decision.json",
        },
    }
    by_category = discover_paths_by_category(manifest)
    assert by_category["product_bundle"]["decision_verdict_json"].endswith(
        "decision_verdict.json"
    )
    assert "selection_decision_json" in by_category["technical_comparison"]


def test_build_product_first_generated_paths_keeps_bundle_first(tmp_path: Path) -> None:
    subject = tmp_path / "analysis_subject"
    seed_analysis_subject_diagnosis_bundle(subject)
    (tmp_path / "current_vs_candidate.json").write_text("{}", encoding="utf-8")
    (tmp_path / "decision_verdict.json").write_text("{}", encoding="utf-8")

    paths = build_product_first_generated_paths(
        tmp_path,
        {
            "candidate_comparison_json": tmp_path / "candidate_comparison.json",
            "current_vs_candidate_json": tmp_path / "old_should_not_override.json",
        },
    )

    keys = list(paths)
    assert keys[:5] == [
        "problem_classification_json",
        "candidate_launchpad_json",
        "portfolio_alternatives_builder_json",
        "current_vs_candidate_json",
        "decision_verdict_json",
    ]
    assert keys[-1] == "candidate_comparison_json"
    assert "old_should_not_override" not in str(paths["current_vs_candidate_json"])


def test_product_bundle_manifest_extra_declares_primary_surface() -> None:
    extra = product_bundle_manifest_extra()
    assert extra["primary_output_surface"] == "product_bundle"
    assert extra["product_bundle_manifest_keys"] == list(PRODUCT_BUNDLE_MANIFEST_KEYS)
    assert extra["product_bundle_contract"]["merged_product_bundle_json"] is False
    assert extra["product_bundle_contract"]["advanced_artifacts_are_product_surface"] is False
    xray_note = extra["subject_diagnostics_contract"]["portfolio_xray_json"]
    assert xray_note["product_capital_structure_key"] == "block_2_1_asset_allocation"
    assert xray_note["product_portfolio_behavior_key"] == PORTFOLIO_XRAY_BLOCK_2_2_KEY
    assert xray_note["product_factor_exposure_key"] == PORTFOLIO_XRAY_BLOCK_2_3_KEY
    assert xray_note["product_hidden_exposure_key"] == PORTFOLIO_XRAY_BLOCK_2_4_KEY
    assert xray_note["product_risk_budget_key"] == PORTFOLIO_XRAY_BLOCK_2_5_KEY
    assert xray_note["product_weakness_map_key"] == PORTFOLIO_XRAY_BLOCK_2_6_KEY
    assert "portfolio_xray.json" in xray_note["note"]
    assert "Block 2.2" in xray_note["note"]
    assert "Block 2.3" in xray_note["note"]
    assert "Block 2.4" in xray_note["note"]
    assert "Block 2.5" in xray_note["note"]
    assert "Block 2.6" in xray_note["note"]


def test_portfolio_xray_has_block_2_2_detects_product_contract() -> None:
    assert not portfolio_xray_has_block_2_2(None)
    assert not portfolio_xray_has_block_2_2({})
    assert not portfolio_xray_has_block_2_2({PORTFOLIO_XRAY_BLOCK_2_2_KEY: {"block": "wrong"}})
    assert portfolio_xray_has_block_2_2(
        {PORTFOLIO_XRAY_BLOCK_2_2_KEY: {"block": BLOCK_2_2_ID}}
    )


def test_portfolio_xray_has_block_2_3_detects_product_contract() -> None:
    assert not portfolio_xray_has_block_2_3(None)
    assert not portfolio_xray_has_block_2_3({})
    assert not portfolio_xray_has_block_2_3({PORTFOLIO_XRAY_BLOCK_2_3_KEY: {"block": "wrong"}})
    assert portfolio_xray_has_block_2_3(
        {PORTFOLIO_XRAY_BLOCK_2_3_KEY: {"block": BLOCK_2_3_ID}}
    )


def test_portfolio_xray_has_block_2_4_detects_product_contract() -> None:
    assert not portfolio_xray_has_block_2_4(None)
    assert not portfolio_xray_has_block_2_4({})
    assert not portfolio_xray_has_block_2_4({PORTFOLIO_XRAY_BLOCK_2_4_KEY: {"block": "wrong"}})
    assert portfolio_xray_has_block_2_4(
        {PORTFOLIO_XRAY_BLOCK_2_4_KEY: {"block": BLOCK_2_4_ID}}
    )


def test_portfolio_xray_has_block_2_5_detects_product_contract() -> None:
    assert not portfolio_xray_has_block_2_5(None)
    assert not portfolio_xray_has_block_2_5({})
    assert not portfolio_xray_has_block_2_5({PORTFOLIO_XRAY_BLOCK_2_5_KEY: {"block": "wrong"}})
    assert portfolio_xray_has_block_2_5(
        {PORTFOLIO_XRAY_BLOCK_2_5_KEY: {"block": BLOCK_2_5_ID}}
    )


def test_portfolio_xray_has_block_2_6_detects_product_contract() -> None:
    assert not portfolio_xray_has_block_2_6(None)
    assert not portfolio_xray_has_block_2_6({})
    assert not portfolio_xray_has_block_2_6({PORTFOLIO_XRAY_BLOCK_2_6_KEY: {"block": "wrong"}})
    assert portfolio_xray_has_block_2_6(
        {PORTFOLIO_XRAY_BLOCK_2_6_KEY: {"block": BLOCK_2_6_ID}}
    )


def test_load_diagnosis_bundle_docs_legacy_root_only(tmp_path: Path) -> None:
    _write_problem(tmp_path, subdir=None, problem_id="legacy_only")
    _write_launchpad(tmp_path, subdir=None, card_id="legacy_card")

    bundle = load_diagnosis_bundle_docs(tmp_path)
    assert bundle["problem_classification_resolution"] == "root"
    assert bundle["candidate_launchpad_resolution"] == "root"
    assert bundle["problem_classification"]["problems"][0]["problem_id"] == "legacy_only"
