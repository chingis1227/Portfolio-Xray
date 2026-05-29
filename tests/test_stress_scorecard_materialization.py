"""Block 3.4 Session 11 — snapshot mirror, validation contract, live E2E gates."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.core_mvp_validation_contract import (
    BLOCK34_RULESET_VERSION,
    assert_current_portfolio_stress_scorecard_v1_product_contract,
    check_current_portfolio_stress_scorecard_v1,
    current_portfolio_stress_scorecard_v1_product_contract_violations,
)
from src.candidate_comparison import write_candidate_comparison_outputs
from src.config_schema import validate_config
from src.current_portfolio_stress_scorecard_block import BLOCK_3_4_VERSION, RULESET_VERSION
from src.live_core_e2e import validate_live_core_artifacts
from src.snapshot import (
    _current_portfolio_stress_scorecard_v1_mirror_for_snapshot,
    _stress_suite_results_for_snapshot,
)
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


def test_snapshot_scorecard_v1_mirror_includes_institutional_fields() -> None:
    out = _minimal_run()
    mirror = _current_portfolio_stress_scorecard_v1_mirror_for_snapshot(out)
    assert mirror.get("version") == BLOCK_3_4_VERSION
    assert mirror.get("block_status") in {"ok", "partial", "unavailable"}
    assert mirror.get("ruleset_version") == RULESET_VERSION
    stress_diagnosis = mirror.get("stress_diagnosis") or {}
    assert "diagnosis_confidence" in stress_diagnosis

    section = _stress_suite_results_for_snapshot(out, portfolio_params={})
    suite_sc = section.get("current_portfolio_stress_scorecard_v1") or {}
    assert suite_sc.get("version") == BLOCK_3_4_VERSION
    assert suite_sc.get("ruleset_version") == RULESET_VERSION
    assert "block_status" in suite_sc


def test_check_current_portfolio_stress_scorecard_v1_passes_run_stress_block() -> None:
    out = _minimal_run()
    block = out[BLOCK_3_4_VERSION]
    assert_current_portfolio_stress_scorecard_v1_product_contract(block)
    checks = check_current_portfolio_stress_scorecard_v1(block)
    assert checks["product_contract_ok"] is True
    assert checks["ruleset_version"] == RULESET_VERSION
    if block.get("block_status") in {"ok", "partial"}:
        assert checks["headline_present"] is True
        assert (checks.get("next_decision_uses_count") or 0) > 0


def test_check_current_portfolio_stress_scorecard_v1_reports_violations_on_bad_version() -> None:
    violations = current_portfolio_stress_scorecard_v1_product_contract_violations(
        {"version": "wrong"}
    )
    assert violations
    assert any("version expected" in row for row in violations)


def test_live_core_e2e_validates_scorecard_contract_on_seeded_workspace(tmp_path: Path) -> None:
    cfg = validate_config(five_ticker_mvp_config_dict())
    seed_blocks_1_5_mvp_smoke_workspace(tmp_path, cfg)
    write_candidate_comparison_outputs(cfg, project_root=tmp_path)
    result = validate_live_core_artifacts(tmp_path / cfg.output_dir_final)
    assert result.ok, "\n".join(result.messages())
    assert result.evidence.get("block_3_4_ruleset_version") == RULESET_VERSION
    assert result.evidence.get("block_3_4_block_status") in {"ok", "partial", "unavailable"}
