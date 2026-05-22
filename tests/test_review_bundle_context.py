"""Tests for review bundle disclosure (RM-1026 / Session 07)."""
from __future__ import annotations

import json
from pathlib import Path

from src.analysis_setup import build_analysis_setup
from src.candidate_comparison import build_candidate_comparison
from src.config_schema import validate_config
from src.input_assumptions import build_input_assumptions_from_analysis_setup
from src.review_bundle_context import (
    REVIEW_BUNDLE_CONTEXT_VERSION,
    assess_mode_subject_consistency,
    build_review_bundle_context_v1,
    compute_review_bundle_fingerprint,
    input_assumptions_review_summary_lines,
)


def test_optimize_from_universe_with_current_subject_is_informational_not_mismatch() -> None:
    ms = assess_mode_subject_consistency(
        source_analysis_mode="optimize_from_universe",
        analysis_subject_type="current_portfolio",
        portfolio_role="user_current_portfolio",
        product_input_case="user_current",
    )
    assert ms["is_consistent"] is True
    assert ms["mismatch_codes"] == []
    assert ms["informational_notices"]


def test_analyze_current_vs_model_subject_is_mismatch() -> None:
    ms = assess_mode_subject_consistency(
        source_analysis_mode="analyze_current_weights",
        analysis_subject_type="model_portfolio",
        portfolio_role="model_portfolio",
    )
    assert ms["is_consistent"] is False
    assert "MODE_SUBJECT_ANALYZE_CURRENT_VS_MODEL" in ms["mismatch_codes"]


def test_review_bundle_fingerprint_stable_for_same_inputs() -> None:
    parts = {
        "analysis_end": "2026-04-30",
        "comparison_config_fingerprint": "abc",
        "analysis_subject_id": "client",
        "analysis_subject_type": "current_portfolio",
        "subject_snapshot_fingerprint": "def",
        "factory_profile_id": "core_v1",
        "factory_config_fingerprint": "abc",
        "review_mode": "core",
    }
    assert compute_review_bundle_fingerprint(parts) == compute_review_bundle_fingerprint(parts)


def test_input_assumptions_trust_lines_include_mode_subject_notice() -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "tickers": ["VOO", "BND"],
            "analysis_subject": {
                "type": "current_portfolio",
                "weights": {"VOO": 0.6, "BND": 0.4},
            },
        }
    )
    setup = build_analysis_setup(cfg)
    lines = input_assumptions_review_summary_lines(setup)
    assert any("optimize_from_universe" in line for line in lines)
    exported = build_input_assumptions_from_analysis_setup(setup)
    trust_lines = exported["data_trust_signals"]["user_summary_lines"]
    assert any("optimize_from_universe" in line for line in trust_lines)
    assert exported["review_bundle_disclosure"]["mode_subject_consistency"]["is_consistent"]


def test_comparison_includes_review_bundle_context(tmp_path: Path) -> None:
    main = tmp_path / "Main portfolio"
    subject = main / "analysis_subject"
    subject.mkdir(parents=True)
    snap = {
        "analysis_end": "2026-04-30",
        "window_label": "10y",
        "metrics": {"cagr": 0.07, "vol_annual": 0.1, "max_drawdown": -0.2, "sharpe": 0.5},
        "candidate_config_fingerprint": "fp_subject_1234567890abcdef",
    }
    with open(subject / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(snap, f)
    with open(subject / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "analysis_setup": {
                    "portfolio_input": {"source_analysis_mode": "optimize_from_universe"},
                    "analysis_subject": {
                        "id": "client_current",
                        "type": "current_portfolio",
                        "display_name": "Client current",
                        "weight_source": "config.analysis_subject.weights",
                    },
                    "analysis_portfolio": {
                        "portfolio_role": "user_current_portfolio",
                        "weight_source": "config.analysis_subject.weights",
                    },
                }
            },
            f,
        )

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
            "analysis_subject": {
                "id": "client_current",
                "type": "current_portfolio",
                "weights": {"VOO": 0.6, "BND": 0.4},
            },
        }
    )
    doc = build_candidate_comparison(cfg, project_root=tmp_path)
    bundle = doc["review_bundle_context"]
    assert bundle["version"] == REVIEW_BUNDLE_CONTEXT_VERSION
    assert len(bundle["review_bundle_fingerprint"]) == 64
    assert bundle["bundle_parts"]["analysis_subject"]["analysis_subject_type"] == "current_portfolio"
    assert bundle["mode_subject_consistency"]["is_consistent"] is True
    assert bundle["user_summary_lines"]
    assert any(
        "review_bundle_context" in line or "fingerprint" in line.lower()
        for line in bundle["user_summary_lines"]
    )

    ctx = build_review_bundle_context_v1(
        analysis_end="2026-04-30",
        comparison_config_fingerprint="fp_subject_1234567890abcdef",
        comparison_generated_at="2026-05-22T00:00:00+00:00",
        comparison_rebuild_source="standalone",
        setup_summary=doc["analysis_setup_summary"],
        candidate_menu=doc["candidate_menu"],
        subject_artifacts={
            "sidecar_present": True,
            "snapshot_config_fingerprint": "fp_subject_1234567890abcdef",
        },
        factory_run=None,
        factory_context={},
    )
    assert ctx["fingerprint_alignment"]["subject_vs_comparison_config"] == "match"
