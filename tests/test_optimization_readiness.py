"""Block 5 Session 10: optimization comparison readiness checklist."""

from __future__ import annotations

import json
from pathlib import Path

from src.candidate_comparison import build_candidate_comparison, write_candidate_comparison_txt
from src.config_schema import validate_config
from src.optimization_readiness import (
    SCHEMA_VERSION,
    build_optimization_readiness,
)
from src.snapshot import compute_candidate_config_fingerprint


def _snapshot_10y(
    metrics: dict,
    *,
    rc_asset: list | None = None,
    final_weights_total: dict | None = None,
    cfg: object | None = None,
    analysis_end: str = "2026-04-30",
) -> dict:
    snap = {
        "analysis_end": analysis_end,
        "window_label": "10y",
        "metrics": metrics,
        "stress_suite_results": {
            "overall": "PASS",
            "fail_reason_code": None,
            "failed_scenario": None,
        },
    }
    if rc_asset is not None:
        snap["RC_asset"] = rc_asset
    if final_weights_total is not None:
        snap["final_weights_total"] = final_weights_total
    if cfg is not None:
        snap["candidate_config_fingerprint"] = compute_candidate_config_fingerprint(cfg)
    return snap


def _run_metadata(portfolio_role: str) -> dict:
    return {
        "run_info": {"analysis_end_date": "2026-04-30"},
        "portfolio_valid": True,
        "analysis_setup": {
            "portfolio_input": {"source_analysis_mode": "optimize_from_universe"},
            "analysis_portfolio": {
                "portfolio_role": portfolio_role,
                "weight_source": "optimization_result_released",
                "recommendation_status": "generated_policy_output_released",
            },
        },
    }


def _mv_folder(tmp_path: Path, cfg, *, metadata: dict | None = None) -> Path:
    folder = tmp_path / "minimum variance portfolio"
    folder.mkdir()
    with open(folder / "snapshot_10y.json", "w", encoding="utf-8") as handle:
        json.dump(
            _snapshot_10y(
                {"cagr": 0.05, "vol_annual": 0.08, "max_drawdown": -0.1},
                cfg=cfg,
                final_weights_total={"VOO": 0.6, "BND": 0.4},
                rc_asset=[
                    {"ticker": "VOO", "rc_pct": 0.55},
                    {"ticker": "BND", "rc_pct": 0.45},
                ],
            ),
            handle,
        )
    with open(folder / "weights.json", "w", encoding="utf-8") as handle:
        json.dump({"VOO": 0.6, "BND": 0.4}, handle)
    with open(folder / "stress_report.json", "w", encoding="utf-8") as handle:
        json.dump({"overall": "PASS"}, handle)
    meta = metadata or {
        "optimizer_run_metadata": {
            "schema_version": "candidate_optimizer_run_metadata_v1",
            "optimizer_role": "candidate_only",
            "method_id": "minimum_variance_constrained",
            "solver": {
                "success": True,
                "status": "OK",
                "fallback_used": False,
                "optimization_quality_status": "clean_solve",
            },
        },
    }
    with open(folder / "baseline_weights_metadata.json", "w", encoding="utf-8") as handle:
        json.dump(meta, handle)
    return folder


def _subject_sidecar(main: Path, cfg) -> None:
    subject = main / "analysis_subject"
    subject.mkdir(parents=True)
    with open(subject / "snapshot_10y.json", "w", encoding="utf-8") as handle:
        json.dump(_snapshot_10y({"cagr": 0.06, "vol_annual": 0.1}, cfg=cfg), handle)
    with open(subject / "run_metadata.json", "w", encoding="utf-8") as handle:
        json.dump(_run_metadata("model_portfolio"), handle)


def test_build_readiness_ready_for_clean_optimizer_row(tmp_path: Path) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    main = tmp_path / "Main portfolio"
    main.mkdir()
    _subject_sidecar(main, cfg)
    fp = compute_candidate_config_fingerprint(cfg)
    _mv_folder(tmp_path, cfg)
    with open(main / "candidate_factory_run.json", "w", encoding="utf-8") as handle:
        json.dump(
            {
                "factory_profile_id": "default_v1",
                "steps": [
                    {
                        "candidate_id": "minimum_variance",
                        "status": "succeeded",
                        "freshness_status": "fresh",
                        "snapshot_analysis_end": "2026-04-30",
                        "expected_analysis_end": "2026-04-30",
                        "expected_config_fingerprint": fp,
                        "snapshot_config_fingerprint": fp,
                        "optimization_quality_status": "clean_solve",
                    }
                ],
            },
            handle,
        )

    doc = build_candidate_comparison(cfg, project_root=tmp_path)
    row = next(c for c in doc["candidates"] if c["candidate_id"] == "minimum_variance")
    readiness = row["construction_disclosure"]["optimization_readiness"]
    assert readiness["schema_version"] == SCHEMA_VERSION
    assert readiness["overall_status"] == "ready"
    assert readiness["fair_comparison_ready"] is True
    assert readiness["gaps"] == []
    assert readiness["required_checks"]["weights"]["present"] is True
    assert readiness["required_checks"]["optimizer_methodology"]["present"] is True


def test_build_readiness_degraded_quality_on_approximate_solver(tmp_path: Path) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    main = tmp_path / "Main portfolio"
    main.mkdir()
    _subject_sidecar(main, cfg)
    _mv_folder(
        tmp_path,
        cfg,
        metadata={
            "optimizer_run_metadata": {
                "schema_version": "candidate_optimizer_run_metadata_v1",
                "method_id": "minimum_variance_constrained",
                "solver": {
                    "success": True,
                    "status": "OK_FALLBACK",
                    "fallback_used": True,
                    "fallback_reason": "fixture",
                    "optimization_quality_status": "approximate_fallback",
                },
            },
        },
    )

    doc = build_candidate_comparison(cfg, project_root=tmp_path)
    row = next(c for c in doc["candidates"] if c["candidate_id"] == "minimum_variance")
    readiness = row["construction_disclosure"]["optimization_readiness"]
    assert row["status"] == "degraded"
    assert readiness["overall_status"] == "degraded_quality"
    assert readiness["fair_comparison_ready"] is False
    assert readiness["optimization_quality_family"] == "approximate"


def test_build_readiness_failed_when_row_unavailable(tmp_path: Path) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    main = tmp_path / "Main portfolio"
    main.mkdir()
    _subject_sidecar(main, cfg)
    _mv_folder(tmp_path, cfg)
    with open(main / "candidate_factory_run.json", "w", encoding="utf-8") as handle:
        json.dump(
            {
                "steps": [
                    {
                        "candidate_id": "minimum_variance",
                        "status": "failed",
                        "reason_code": "builder_fail_numerical",
                    }
                ]
            },
            handle,
        )

    doc = build_candidate_comparison(cfg, project_root=tmp_path)
    row = next(c for c in doc["candidates"] if c["candidate_id"] == "minimum_variance")
    readiness = row["construction_disclosure"]["optimization_readiness"]
    assert row["status"] == "unavailable"
    assert readiness["overall_status"] == "failed"
    assert readiness["fair_comparison_ready"] is False


def test_benchmark_row_has_no_optimization_readiness(tmp_path: Path) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    main = tmp_path / "Main portfolio"
    main.mkdir()
    _subject_sidecar(main, cfg)
    ew = tmp_path / "equal-weight portfolio"
    ew.mkdir()
    with open(ew / "snapshot_10y.json", "w", encoding="utf-8") as handle:
        json.dump(
            _snapshot_10y(
                {"cagr": 0.05, "vol_annual": 0.09},
                cfg=cfg,
                final_weights_total={"VOO": 0.5, "BND": 0.5},
            ),
            handle,
        )
    with open(ew / "baseline_weights_metadata.json", "w", encoding="utf-8") as handle:
        json.dump({"equal_weight_method": "by_asset"}, handle)

    doc = build_candidate_comparison(cfg, project_root=tmp_path)
    row = next(c for c in doc["candidates"] if c["candidate_id"] == "equal_weight")
    assert "optimization_readiness" not in row["construction_disclosure"]


def test_partial_readiness_when_stress_missing(tmp_path: Path) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    main = tmp_path / "Main portfolio"
    main.mkdir()
    _subject_sidecar(main, cfg)
    folder = _mv_folder(tmp_path, cfg)
    (folder / "stress_report.json").unlink()
    snap = _snapshot_10y(
        {"cagr": 0.05, "vol_annual": 0.08},
        cfg=cfg,
        final_weights_total={"VOO": 0.6, "BND": 0.4},
    )
    snap.pop("stress_suite_results", None)
    with open(folder / "snapshot_10y.json", "w", encoding="utf-8") as handle:
        json.dump(snap, handle)

    disclosure = {
        "disclosure_status": "available",
        "optimizer_methodology": {"source": "fixture", "solver": {}},
        "optimizer_quality": {
            "optimization_quality_status": "clean_solve",
            "optimization_quality_family": "clean",
        },
        "baseline_metadata": {},
    }
    readiness = build_optimization_readiness(
        folder,
        role="optimizer_candidate",
        construction_disclosure=disclosure,
        comparison_status="degraded",
        unavailable_reason=None,
        warnings=["stress_summary_missing"],
        expected_analysis_end="2026-04-30",
    )
    assert readiness is not None
    assert "stress_summary" in readiness["gaps"]
    assert readiness["fair_comparison_ready"] is False
    assert readiness["overall_status"] in {"partial", "degraded_quality"}


def test_comparison_txt_includes_readiness_section(tmp_path: Path) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    main = tmp_path / "Main portfolio"
    main.mkdir()
    _subject_sidecar(main, cfg)
    _mv_folder(tmp_path, cfg)

    doc = build_candidate_comparison(cfg, project_root=tmp_path)
    txt_path = tmp_path / "candidate_comparison.txt"
    write_candidate_comparison_txt(doc, txt_path)
    text = txt_path.read_text(encoding="utf-8")
    assert "Optimization readiness (optimizer-backed rows)" in text
    assert "fair_comparison_ready=" in text
