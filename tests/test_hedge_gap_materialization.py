"""Block 3.3 Session 10 — snapshot mirror, scorecard linkage, validation contract."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from scripts.core_mvp_validation_contract import (
    assert_hedge_gap_analysis_v1_product_contract,
    check_hedge_gap_analysis_v1,
    hedge_gap_analysis_v1_product_contract_violations,
)
from src.candidate_comparison import write_candidate_comparison_outputs
from src.config_schema import validate_config
from src.current_portfolio_stress_scorecard_block import BLOCK_3_4_VERSION
from src.hedge_gap_analysis_block import RULESET_VERSION, attach_hedge_gap_analysis_v1
from test_hedge_gap_analysis_v1_contract import _scenario_row
from src.live_core_e2e import validate_live_core_artifacts
from src.snapshot import _hedge_gap_analysis_v1_mirror_for_snapshot, _stress_suite_results_for_snapshot
from src.stress import run_stress
from mvp_offline_fixtures import five_ticker_mvp_config_dict, seed_blocks_1_5_mvp_smoke_workspace


def _minimal_run(**kwargs: object) -> dict:
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


def test_snapshot_hedge_gap_v1_mirror_includes_institutional_fields() -> None:
    out = _minimal_run()
    mirror = _hedge_gap_analysis_v1_mirror_for_snapshot(out)
    assert mirror.get("version") == "hedge_gap_analysis_v1"
    assert mirror.get("block_status") in {"ok", "partial", "unavailable"}
    assert mirror.get("ruleset_version") == RULESET_VERSION
    summary = mirror.get("summary") or {}
    assert "protection_profile" in summary
    main = summary.get("main_hedge_gap")
    if isinstance(main, dict):
        assert "protection_status" in main

    section = _stress_suite_results_for_snapshot(out, portfolio_params={})
    suite_v1 = section.get("hedge_gap_analysis_v1") or {}
    assert suite_v1.get("version") == "hedge_gap_analysis_v1"
    assert suite_v1.get("ruleset_version") == RULESET_VERSION
    assert "block_status" in suite_v1


def test_check_hedge_gap_analysis_v1_passes_run_stress_block() -> None:
    out = _minimal_run()
    block = out["hedge_gap_analysis_v1"]
    assert_hedge_gap_analysis_v1_product_contract(block)
    checks = check_hedge_gap_analysis_v1(block)
    assert checks["product_contract_ok"] is True
    assert checks["ruleset_version"] == RULESET_VERSION


def test_check_hedge_gap_analysis_v1_reports_violations_on_bad_version() -> None:
    violations = hedge_gap_analysis_v1_product_contract_violations({"version": "wrong"})
    assert violations
    assert any("version expected" in row for row in violations)


def test_scorecard_exposes_hedge_gap_linkage_metadata() -> None:
    out = _minimal_run()
    scorecard = out[BLOCK_3_4_VERSION]
    assert scorecard.get("hedge_gap_ruleset_version") == RULESET_VERSION
    assert scorecard.get("hedge_gap_block_status") in {"ok", "partial", "unavailable"}


def test_live_core_e2e_validates_hedge_gap_contract_on_seeded_workspace(tmp_path: Path) -> None:
    cfg = validate_config(five_ticker_mvp_config_dict())
    seed_blocks_1_5_mvp_smoke_workspace(tmp_path, cfg)
    write_candidate_comparison_outputs(cfg, project_root=tmp_path)
    result = validate_live_core_artifacts(tmp_path / cfg.output_dir_final)
    assert result.ok, "\n".join(result.messages())
    assert result.evidence.get("hedge_gap_ruleset_version") == RULESET_VERSION
    assert result.evidence.get("hedge_gap_block_status") == "unavailable"


def test_attach_without_upstream_leaves_bridge_lists_absent_until_xray() -> None:
    report: dict = {
        "loss_gate_mode": "diagnostic",
        "stress_results_v1": {"version": "stress_results_v1", "synthetic_scenarios": []},
        "scenario_results": [
            _scenario_row(
                "equity_shock",
                portfolio_pnl_pct=-0.08,
                pnl_by_asset_pct={"AAA": -0.07, "BBB": -0.01},
            ),
        ],
    }
    attach_hedge_gap_analysis_v1(report)
    checks = check_hedge_gap_analysis_v1(report["hedge_gap_analysis_v1"])
    assert checks["product_contract_ok"] is True
    assert checks["has_hidden_exposure_confirmation"] is False
    assert checks["has_weakness_map_confirmation"] is False
