"""Smoke tests for Blocks 1–3 diagnostic journey view model."""

from __future__ import annotations

from pathlib import Path

from diagnostic_journey.view_model import build_diagnostic_journey_view_model

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUBJECT = PROJECT_ROOT / "Main portfolio" / "analysis_subject"


def test_build_view_model_from_live_subject_bundle():
    if not (SUBJECT / "portfolio_xray.json").is_file():
        return
    vm = build_diagnostic_journey_view_model(SUBJECT, project_root=PROJECT_ROOT)
    assert vm["has_data"] is True
    assert vm["has_xray"] is True
    assert vm["has_stress"] is True
    assert len(vm["block2_exec"]["findings"]) >= 5
    assert vm["block1"]["mode"] == "Current portfolio diagnosis"
    assert "pre-stress hypothesis" in vm["block2_weakness"]["pre_stress_note"].lower()
    assert "not recommendations" in vm["bridge"]["subtitle"].lower()
    assert "real_rates" not in vm["block2_exec"]["main_diagnosis"].lower()


def test_missing_bundle_is_safe():
    vm = build_diagnostic_journey_view_model(PROJECT_ROOT / "nonexistent_subject_dir")
    assert vm["has_data"] is False
