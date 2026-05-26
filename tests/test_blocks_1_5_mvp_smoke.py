"""Executable five-ticker smoke gate for Blocks 1-5 MVP reliability."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from src.candidate_comparison import write_candidate_comparison_outputs
from src.config_schema import ConfigValidationError, validate_config
from src.portfolio_review_workflow import build_portfolio_review_plan
from src.portfolio_xray import XRAY_SECTION_KEYS
from src.product_bundle_paths import portfolio_xray_has_block_2_1, portfolio_xray_has_block_2_2
from mvp_offline_fixtures import (
    DEFAULT_ANALYSIS_END,
    FIVE_TICKER_MVP_TICKERS,
    FIVE_TICKER_MVP_WEIGHTS,
    five_ticker_mvp_config_dict,
    seed_blocks_1_5_mvp_smoke_workspace,
)


def _load_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*_args, **_kwargs):
        raise AssertionError("Blocks 1-5 smoke gate must stay offline")

    import src.data_fred as data_fred
    import src.data_yf as data_yf

    monkeypatch.setattr(data_yf, "download_all", _boom)
    monkeypatch.setattr(data_fred, "fetch_fred_series", _boom, raising=False)


def test_five_ticker_blocks_1_5_mvp_smoke_gate(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _block_network(monkeypatch)
    cfg = validate_config(five_ticker_mvp_config_dict())
    seeded = seed_blocks_1_5_mvp_smoke_workspace(tmp_path, cfg)

    assert list(cfg.tickers) == FIVE_TICKER_MVP_TICKERS
    assert sum((cfg.weights or {}).values()) == pytest.approx(1.0)
    assert cfg.weights_source == "config.analysis_subject.weights"

    plan = build_portfolio_review_plan(
        cfg,
        project_root=tmp_path,
        review_mode="core",
        skip_pdf=True,
    )
    assert [step.stage for step in plan.steps] == ["diagnosis", "candidates"]
    assert "--materialize-analysis-subject" in plan.steps[0].argv
    assert "--profile" in plan.steps[1].argv
    assert "core_fast" in plan.steps[1].argv

    subject_dir = seeded["analysis_subject_dir"]
    run_metadata = _load_json(subject_dir / "run_metadata.json")
    assert run_metadata["analysis_setup"]["analysis_subject"]["ticker_count"] == 5
    assert run_metadata["analysis_setup"]["analysis_subject"]["weight_status"]["status"] == "fully_invested"
    assert run_metadata["input_assumptions"]["analysis_subject"]["type"] == "current_portfolio"

    xray = _load_json(subject_dir / "portfolio_xray.json")
    assert set(xray["sections"]) == set(XRAY_SECTION_KEYS)
    assert portfolio_xray_has_block_2_1(xray)
    assert portfolio_xray_has_block_2_2(xray)
    assert (xray["block_2_1_asset_allocation"]["portfolio_composition_snapshot"]["total_holdings"]) == 5
    assert (xray["block_2_2_portfolio_metrics"]["metadata"]["primary_window_months"]) == 120

    stress = _load_json(subject_dir / "stress_report.json")
    for key in (
        "stress_scorecard_v1",
        "stress_conclusions",
        "historical_methodology",
        "hedge_gap_analysis",
    ):
        assert key in stress

    factory = _load_json(seeded["main_dir"] / "candidate_factory_run.json")
    assert factory["factory_profile_id"] == "core_fast"
    assert factory["analysis_end"] == DEFAULT_ANALYSIS_END
    assert factory["config_fingerprint"] == seeded["config_fingerprint"]
    assert [step["candidate_id"] for step in factory["steps"]] == seeded["core_candidate_ids"]
    assert all(step["freshness_status"] == "fresh" for step in factory["steps"])

    paths = write_candidate_comparison_outputs(cfg, project_root=tmp_path)
    comparison = _load_json(paths["candidate_comparison_json"])
    assert comparison["comparison_baseline_candidate_id"] == "analysis_subject"
    assert comparison["analysis_end"] == DEFAULT_ANALYSIS_END
    assert comparison["candidate_menu"]["factory_evidence_status"] == "current"
    assert comparison["candidate_menu"]["factory_steps_used"] is True
    assert comparison["candidate_menu"]["review_mode"] == "core"
    assert comparison["candidate_menu"]["intended_menu_status_counts"]["available"] == 6

    subject_row = next(c for c in comparison["candidates"] if c["candidate_id"] == "analysis_subject")
    assert subject_row["status"] == "available"
    assert subject_row["portfolio_role"] == "user_current_portfolio"
    assert subject_row["weight_concentration"]["top3_weight_sum_pct"] == pytest.approx(0.75)

    equal_weight = next(c for c in comparison["candidates"] if c["candidate_id"] == "equal_weight")
    assert equal_weight["status"] == "available"
    assert equal_weight["construction_disclosure"]["factory_step"]["freshness_status"] == "fresh"
    assert "candidate_factory_run.json" in equal_weight["construction_disclosure"]["source_files"]


@pytest.mark.parametrize(
    ("analysis_subject", "message"),
    [
        (
            {"type": "current_portfolio"},
            "requires non-empty analysis_subject.weights",
        ),
        (
            {
                "type": "current_portfolio",
                "weights": {**FIVE_TICKER_MVP_WEIGHTS, "GLD": "-5%"},
            },
            "must be non-negative",
        ),
        (
            {
                "type": "current_portfolio",
                "weights": {
                    "VOO": "50%",
                    "BND": "30%",
                    "GLD": "25%",
                    "QQQ": "20%",
                    "VNQ": "10%",
                },
            },
            "must not sum above 1\\.0",
        ),
    ],
)
def test_five_ticker_blocks_1_5_smoke_gate_rejects_missing_or_invalid_weights(
    analysis_subject: dict[str, Any],
    message: str,
) -> None:
    config = five_ticker_mvp_config_dict()
    config["analysis_subject"] = analysis_subject

    with pytest.raises(ConfigValidationError, match=message):
        validate_config(config)
