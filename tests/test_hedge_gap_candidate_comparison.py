"""Block 3.3 Session 08 — hedge_gap_comparison on candidate_comparison.json."""
from __future__ import annotations

import json
from pathlib import Path

from src.candidate_comparison import (
    HEDGE_GAP_COMPARISON_VERSION,
    HEDGE_GAP_V1_VERSION,
    _stress_from_artifacts,
    build_candidate_comparison,
)
from src.config_schema import validate_config
from src.current_portfolio_stress_scorecard_block import attach_current_portfolio_stress_scorecard_v1
from src.hedge_gap_analysis_block import attach_hedge_gap_analysis_v1
from src.snapshot import compute_candidate_config_fingerprint
from src.stress_results_block import build_stress_results_v1
from test_hedge_gap_analysis_v1_contract import _scenario_row


def _write_snapshot(path: Path, metrics: dict, *, stress_report: dict | None = None) -> None:
    snap: dict = {
        "analysis_end": "2026-04-30",
        "window_label": "10y",
        "metrics": metrics,
        "stress_suite_results": {
            "overall": "DIAG_PASS",
            "scenarios": [{"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.08, "pass": True}],
        },
    }
    if stress_report:
        from src.snapshot import _stress_suite_results_for_snapshot

        snap["stress_suite_results"] = _stress_suite_results_for_snapshot(
            stress_report,
            portfolio_params={},
        )
        snap["candidate_config_fingerprint"] = stress_report.get("_cfg_fp")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snap, f)


def _stress_report_with_v1(*, offset: float, loss: float) -> dict:
    rows = [
        _scenario_row(
            "equity_shock",
            portfolio_pnl_pct=loss,
            pnl_by_asset_pct={"A": loss * 0.9, "H": loss * 0.1 * offset},
        ),
    ]
    stress_results_v1 = build_stress_results_v1(
        scenario_results=rows,
        historical_results=[],
        historical_episode_paths=[],
        stress_conclusions={},
        loss_gate_mode="diagnostic",
    )
    report = {
        "scenario_results": rows,
        "stress_results_v1": stress_results_v1,
        "loss_gate_mode": "diagnostic",
        "status": "DIAG_PASS",
        "stress_conclusions": {"hedge_gap_status": "not_applicable"},
    }
    attach_hedge_gap_analysis_v1(report)
    attach_current_portfolio_stress_scorecard_v1(report)
    return report


def test_stress_from_artifacts_includes_hedge_gap_v1_compact(tmp_path: Path) -> None:
    folder = tmp_path / "peer"
    report = _stress_report_with_v1(offset=0.05, loss=-0.10)
    _write_snapshot(folder / "snapshot_10y.json", {"cagr": 0.07}, stress_report=report)
    with open(folder / "stress_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f)
    snap = json.loads((folder / "snapshot_10y.json").read_text(encoding="utf-8"))
    stress = _stress_from_artifacts(folder, snap)
    v1 = stress.get("hedge_gap_analysis_v1")
    assert isinstance(v1, dict)
    assert v1.get("main_hedge_gap_protection_status") in {
        "weak_protection",
        "no_protection",
        "partial_protection",
        "strong_protection",
    }


def test_build_candidate_comparison_emits_hedge_gap_comparison(tmp_path: Path) -> None:
    main = tmp_path / "Main portfolio"
    subject = main / "analysis_subject"
    eq = tmp_path / "equal-weight portfolio"
    metrics = {"cagr": 0.08, "vol_annual": 0.12, "max_drawdown": -0.2, "sharpe": 0.5}
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "tickers": ["VOO", "BND"],
            "output_dir_final": "Main portfolio",
        }
    )
    cfg_fp = compute_candidate_config_fingerprint(cfg)
    sub_report = _stress_report_with_v1(offset=0.0, loss=-0.12)
    sub_report["_cfg_fp"] = cfg_fp
    eq_report = _stress_report_with_v1(offset=0.45, loss=-0.10)
    eq_report["_cfg_fp"] = cfg_fp

    _write_snapshot(subject / "snapshot_10y.json", metrics, stress_report=sub_report)
    with open(subject / "stress_report.json", "w", encoding="utf-8") as f:
        json.dump(sub_report, f)
    with open(subject / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "run_info": {"analysis_end_date": "2026-04-30"},
                "analysis_setup": {
                    "analysis_subject": {"id": "starter", "type": "model_portfolio"},
                },
            },
            f,
        )

    _write_snapshot(eq / "snapshot_10y.json", metrics, stress_report=eq_report)
    with open(eq / "stress_report.json", "w", encoding="utf-8") as f:
        json.dump(eq_report, f)

    with open(main / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "analysis_end": "2026-04-30",
                "metrics": metrics,
                "candidate_config_fingerprint": cfg_fp,
            },
            f,
        )
    with open(main / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "run_info": {"analysis_end_date": "2026-04-30"},
                "analysis_setup": {
                    "portfolio_input": {"source_analysis_mode": "optimize_from_universe"},
                    "analysis_portfolio": {"portfolio_role": "generated_policy_portfolio"},
                },
            },
            f,
        )

    doc = build_candidate_comparison(cfg, project_root=tmp_path)
    hg = doc.get("hedge_gap_comparison")
    assert isinstance(hg, dict)
    assert hg.get("version") == HEDGE_GAP_COMPARISON_VERSION
    assert hg.get("status") == "ok"
    assert hg.get("hedge_gap_source") == HEDGE_GAP_V1_VERSION
    assert "analysis_subject" in (hg.get("candidates") or {})
    assert "equal_weight" in (hg.get("candidates") or {})
    pairwise = hg.get("pairwise") or []
    assert len(pairwise) >= 1
    row = next(p for p in pairwise if p.get("candidate_id") == "equal_weight")
    assert row.get("offset_coverage_ratio_delta") is not None
    assert isinstance(row.get("comparison_summary_en"), str)

    eq_cand = next(c for c in doc["candidates"] if c["candidate_id"] == "equal_weight")
    assert isinstance((eq_cand.get("stress") or {}).get("hedge_gap_analysis_v1"), dict)
