"""Block 3.4 Session 09 — stress_scorecard_comparison on candidate_comparison.json."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.candidate_comparison import (
    SCORECARD_V1_BLOCK,
    SCORECARD_V1_VERSION,
    STRESS_SCORECARD_COMPARISON_VERSION,
    STRESS_SCORECARD_SOURCE_LEGACY,
    _stress_from_artifacts,
    build_candidate_comparison,
)
from src.config_schema import validate_config
from src.snapshot import compute_candidate_config_fingerprint
from src.stress import run_stress
from test_hedge_gap_candidate_comparison import (
    _stress_report_with_v1,
    _write_snapshot,
)


def _minimal_stress_report(**kwargs: object) -> dict:
    idx = pd.date_range("2015-01-31", periods=120, freq="ME")
    monthly_returns = pd.DataFrame({"AAA": [0.01] * len(idx), "BBB": [0.01] * len(idx)}, index=idx)
    defaults = dict(
        tickers=["AAA", "BBB"],
        weights={"AAA": 0.8, "BBB": 0.2},
        monthly_returns=monthly_returns,
        asset_betas=pd.DataFrame(
            columns=["beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd"]
        ),
        portfolio_betas={k: 0.0 for k in ("beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd")},
        target_max_drawdown_pct=0.2,
        cash_proxy_ticker="",
        hedge_assets=["AAA"],
        loss_gate_mode="diagnostic",
    )
    defaults.update(kwargs)
    return run_stress(**defaults)  # type: ignore[arg-type]


def test_stress_from_artifacts_includes_scorecard_v1_compact(tmp_path: Path) -> None:
    folder = tmp_path / "peer"
    report = _minimal_stress_report()
    _write_snapshot(folder / "snapshot_10y.json", {"cagr": 0.07}, stress_report=report)
    with open(folder / "stress_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f)
    snap = json.loads((folder / "snapshot_10y.json").read_text(encoding="utf-8"))
    stress = _stress_from_artifacts(folder, snap)
    v1 = stress.get(SCORECARD_V1_BLOCK)
    assert isinstance(v1, dict)
    assert stress.get("stress_scorecard_source") == SCORECARD_V1_BLOCK
    assert v1.get("worst_synthetic_scenario_id") is not None
    assert v1.get("block_status") in {"ok", "partial"}


def test_stress_from_artifacts_legacy_scorecard_when_v1_missing(tmp_path: Path) -> None:
    folder = tmp_path / "peer"
    folder.mkdir(parents=True)
    report = {
        "loss_gate_mode": "diagnostic",
        "status": "DIAG_PASS",
        "stress_scorecard_v1": {"overall_status": "DIAG_PASS", "overall_confidence": "medium"},
        "stress_conclusions": {"version": "stress_conclusions_v1"},
    }
    with open(folder / "stress_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f)
    stress = _stress_from_artifacts(folder, None)
    assert SCORECARD_V1_BLOCK not in stress
    assert isinstance(stress.get("scorecard"), dict)
    assert stress.get("stress_scorecard_source") == STRESS_SCORECARD_SOURCE_LEGACY


def test_build_candidate_comparison_emits_stress_scorecard_comparison(tmp_path: Path) -> None:
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
    eq_report = _stress_report_with_v1(offset=0.45, loss=-0.08)
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
    comparison = doc.get("stress_scorecard_comparison") or {}
    assert comparison.get("version") == STRESS_SCORECARD_COMPARISON_VERSION
    assert comparison.get("status") == "ok"
    assert comparison.get("stress_scorecard_source") == SCORECARD_V1_BLOCK
    assert "equal_weight" in (comparison.get("comparison_candidate_ids") or [])
    pairwise = comparison.get("pairwise") or []
    assert pairwise
    assert pairwise[0].get("worst_synthetic_loss_pct_delta") is not None

    by_id = {row["candidate_id"]: row for row in doc.get("candidates") or []}
    subject_stress = (by_id.get("analysis_subject") or {}).get("stress") or {}
    assert isinstance(subject_stress.get(SCORECARD_V1_BLOCK), dict)
    assert subject_stress.get("stress_scorecard_source") == SCORECARD_V1_BLOCK
