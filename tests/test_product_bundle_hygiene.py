"""Tests for diagnosis-only product bundle hygiene (Session 03 / R3)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import run_report
from mvp_offline_fixtures import validate_mvp_fixture
from src.config_schema import validate_config
from src.output_policy import OUTPUT_PROFILE_SITE_API
from src.product_bundle_hygiene import (
    CORE_BLOCKS_SUBJECT_BLOCK4_FILENAMES,
    NO_CANDIDATE_TOMBSTONE,
    apply_core_blocks_product_bundle_hygiene,
    apply_diagnosis_only_product_bundle_hygiene,
    build_no_candidate_current_vs_candidate,
    build_no_candidate_decision_verdict,
)
POST_COMPARE_ROOT_ARTIFACTS = (
    "decision_verdict.json",
    "current_vs_candidate.json",
    "candidate_comparison.json",
)


def test_tombstone_builders_use_no_candidate_v1() -> None:
    current_vs = build_no_candidate_current_vs_candidate(analysis_end="2026-04-30")
    verdict = build_no_candidate_decision_verdict(analysis_end="2026-04-30")
    assert current_vs["tombstone"] == NO_CANDIDATE_TOMBSTONE
    assert current_vs["view_mode"] == "diagnosis_only"
    assert current_vs["selected_candidate_ids"] == []
    assert verdict["tombstone"] == NO_CANDIDATE_TOMBSTONE
    assert verdict["selected_candidate_id"] is None
    assert verdict["verdict_id"] == "no_candidate_selected"


def test_apply_hygiene_replaces_stale_compare_and_verdict(tmp_path: Path) -> None:
    out = tmp_path / "Main portfolio"
    out.mkdir()
    stale_comparison = {
        "schema_version": "candidate_comparison_v1",
        "candidates": [{"candidate_id": "equal_weight", "status": "available"}] * 19,
    }
    with open(out / "candidate_comparison.json", "w", encoding="utf-8") as f:
        json.dump(stale_comparison, f)
    with open(out / "current_vs_candidate.json", "w", encoding="utf-8") as f:
        json.dump({"selected_candidate_ids": ["equal_weight"]}, f)
    with open(out / "decision_verdict.json", "w", encoding="utf-8") as f:
        json.dump({"selected_candidate_id": "equal_weight"}, f)
    with open(out / "selection_decision.json", "w", encoding="utf-8") as f:
        json.dump({"decision_status": "selected_candidate"}, f)
    with open(out / "candidate_comparison_registry.json", "w", encoding="utf-8") as f:
        json.dump({"candidates": []}, f)

    result = apply_diagnosis_only_product_bundle_hygiene(
        out,
        analysis_end="2026-04-30",
        investor_currency="USD",
    )

    assert result["tombstone"] == NO_CANDIDATE_TOMBSTONE
    assert "selection_decision.json" in result["removed_stale"]
    assert "candidate_comparison_registry.json" in result["removed_stale"]

    with open(out / "current_vs_candidate.json", encoding="utf-8") as f:
        current_vs = json.load(f)
    with open(out / "decision_verdict.json", encoding="utf-8") as f:
        verdict = json.load(f)
    with open(out / "candidate_comparison.json", encoding="utf-8") as f:
        comparison = json.load(f)

    assert current_vs["tombstone"] == NO_CANDIDATE_TOMBSTONE
    assert verdict["tombstone"] == NO_CANDIDATE_TOMBSTONE
    assert comparison["tombstone"] == NO_CANDIDATE_TOMBSTONE
    assert len(comparison.get("candidates") or []) == 0
    assert not (out / "selection_decision.json").exists()
    assert not (out / "candidate_comparison_registry.json").exists()


def test_diagnosis_only_materialize_writes_root_tombstones(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = validate_mvp_fixture("minimal_usd_no_cash.yml")
    cfg.output_dir_final = str(tmp_path / "Main portfolio")
    variant_root = tmp_path / "Main portfolio"
    expected_weights = {str(k): float(v) for k, v in (cfg.weights or {}).items()}

    stale = variant_root / "decision_verdict.json"
    variant_root.mkdir(parents=True, exist_ok=True)
    stale.write_text('{"selected_candidate_id": "equal_weight"}', encoding="utf-8")

    def fake_run_portfolio_report_for_weights(_cfg, weights, **kwargs):
        out = Path(kwargs["output_dir_final"])
        out.mkdir(parents=True, exist_ok=True)
        (out / "run_metadata.json").write_text(
            json.dumps({"analysis_end": "2026-04-30"}),
            encoding="utf-8",
        )
        (out / "portfolio_xray.json").write_text(
            json.dumps({"block_2_1_asset_allocation": {"status": "available"}}),
            encoding="utf-8",
        )
        (out / "stress_report.json").write_text(
            json.dumps({"stress_results_v1": {"status": "available"}}),
            encoding="utf-8",
        )
        (out / "snapshot_10y.json").write_text(
            json.dumps({"metrics": {"cagr": 0.06}, "final_weights_total": weights}),
            encoding="utf-8",
        )
        return {}, {"portfolio_valid": True}

    monkeypatch.setattr(
        run_report,
        "run_portfolio_report_for_weights",
        fake_run_portfolio_report_for_weights,
    )
    monkeypatch.setattr(run_report, "prepare_review_run_context", lambda *a, **k: None)

    run_report.run_materialize_analysis_subject_report(
        cfg,
        run_timestamp="2026-05-29T12:00:00",
        backtest_mode="dynamic_nan_safe",
        no_cache=True,
        review_mode="core",
        output_profile=OUTPUT_PROFILE_SITE_API,
        project_root=tmp_path,
    )

    assert expected_weights
    for name in POST_COMPARE_ROOT_ARTIFACTS:
        path = variant_root / name
        assert path.is_file(), f"expected tombstone artifact {name}"
        doc = json.loads(path.read_text(encoding="utf-8"))
        assert doc.get("tombstone") == NO_CANDIDATE_TOMBSTONE, name
        assert doc.get("artifact_status") == "not_authoritative", name

    with open(variant_root / "decision_verdict.json", encoding="utf-8") as f:
        verdict = json.load(f)
    assert verdict.get("selected_candidate_id") is None


def test_apply_core_blocks_prune_removes_stale_subject_and_root(tmp_path: Path) -> None:
    out = tmp_path / "Main portfolio"
    subject = out / "analysis_subject"
    subject.mkdir(parents=True)
    for name in CORE_BLOCKS_SUBJECT_BLOCK4_FILENAMES:
        (subject / name).write_text("{}", encoding="utf-8")
    (subject / "portfolio_xray.json").write_text("{}", encoding="utf-8")
    (out / "decision_verdict.json").write_text('{"selected_candidate_id": "equal_weight"}', encoding="utf-8")
    (out / "candidate_comparison.json").write_text("{}", encoding="utf-8")

    result = apply_core_blocks_product_bundle_hygiene(out, subject_dir=subject)

    assert result["product_bundle_scope"] == "core_blocks_1_3"
    assert set(result["removed_subject_block4"]) == set(CORE_BLOCKS_SUBJECT_BLOCK4_FILENAMES)
    assert "decision_verdict.json" in result["removed_root_post_compare"]
    assert "candidate_comparison.json" in result["removed_root_post_compare"]
    for name in CORE_BLOCKS_SUBJECT_BLOCK4_FILENAMES:
        assert not (subject / name).exists()
    assert (subject / "portfolio_xray.json").is_file()
    assert not (out / "decision_verdict.json").exists()
    assert not (out / "candidate_comparison.json").exists()


def test_core_diagnostics_materialize_prunes_stale_subject_and_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = validate_config(
        {
            "tickers": ["VOO", "BND"],
            "investor_currency": "USD",
            "analysis_subject": {
                "type": "current_portfolio",
                "weights": {"VOO": 0.6, "BND": 0.4},
            },
            "output_dir_final": str(tmp_path / "Main portfolio"),
        }
    )
    variant_root = tmp_path / "Main portfolio"
    subject = variant_root / "analysis_subject"
    subject.mkdir(parents=True)
    (subject / "problem_classification.json").write_text("{}", encoding="utf-8")
    (subject / "candidate_launchpad.json").write_text("{}", encoding="utf-8")
    (subject / "ai_commentary_context.json").write_text("{}", encoding="utf-8")
    (variant_root / "decision_verdict.json").write_text(
        '{"selected_candidate_id": "equal_weight"}',
        encoding="utf-8",
    )

    def fake_run_portfolio_report_for_weights(_cfg, weights, **kwargs):
        out = Path(kwargs["output_dir_final"])
        out.mkdir(parents=True, exist_ok=True)
        (out / "run_metadata.json").write_text("{}", encoding="utf-8")
        (out / "portfolio_xray.json").write_text("{}", encoding="utf-8")
        (out / "stress_report.json").write_text("{}", encoding="utf-8")
        (out / "snapshot_10y.json").write_text(
            json.dumps({"final_weights_total": weights}),
            encoding="utf-8",
        )
        return {}, {"portfolio_valid": True}

    monkeypatch.setattr(
        run_report,
        "run_portfolio_report_for_weights",
        fake_run_portfolio_report_for_weights,
    )
    monkeypatch.setattr(run_report, "prepare_review_run_context", lambda *a, **k: None)

    run_report.run_materialize_analysis_subject_report(
        cfg,
        run_timestamp="2026-05-29T12:00:00",
        backtest_mode="dynamic_nan_safe",
        no_cache=True,
        review_mode="core",
        output_profile=OUTPUT_PROFILE_SITE_API,
        project_root=tmp_path,
        core_diagnostics_only=True,
    )

    # Core-only removes stale Block 4+ subject files and root compare/decision JSON.
    for name in CORE_BLOCKS_SUBJECT_BLOCK4_FILENAMES:
        assert not (subject / name).exists(), name
    assert not (variant_root / "decision_verdict.json").exists()
    assert not (variant_root / "candidate_comparison.json").exists()
