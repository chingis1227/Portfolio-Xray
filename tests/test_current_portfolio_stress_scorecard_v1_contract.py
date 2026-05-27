"""Contract tests for Block 3.4 current_portfolio_stress_scorecard_v1."""

from __future__ import annotations

import pandas as pd

from src.current_portfolio_stress_scorecard_block import BLOCK_3_4_VERSION
from src.stress import run_stress


def _minimal_run(**kwargs: object) -> dict:
    idx = pd.date_range("2015-01-31", periods=120, freq="ME")
    monthly_returns = pd.DataFrame({"AAA": [0.01] * len(idx), "BBB": [0.01] * len(idx)}, index=idx)
    tickers = ["AAA", "BBB"]
    weights = {"AAA": 0.8, "BBB": 0.2}
    asset_betas = pd.DataFrame(columns=["beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd"])
    portfolio_betas = {k: 0.0 for k in ("beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd")}
    defaults = dict(
        tickers=tickers,
        weights=weights,
        monthly_returns=monthly_returns,
        asset_betas=asset_betas,
        portfolio_betas=portfolio_betas,
        target_max_drawdown_pct=0.2,
        cash_proxy_ticker="",
        hedge_assets=["AAA"],
        loss_gate_mode="diagnostic",
    )
    defaults.update(kwargs)
    return run_stress(**defaults)  # type: ignore[arg-type]


def test_block_exists_and_has_required_keys() -> None:
    out = _minimal_run()
    block = out.get(BLOCK_3_4_VERSION)
    assert isinstance(block, dict)
    assert block["version"] == BLOCK_3_4_VERSION
    assert block["block"] == "3.4"
    assert block["loss_gate_mode"] in {"diagnostic", "mandate"}
    for key in (
        "scenario_library",
        "worst_synthetic_scenario",
        "worst_historical_scenario",
        "portfolio_loss_summary",
        "historical_drawdown_summary",
        "top_loss_contributors",
        "top_risk_contributors",
        "factor_stress_attribution_summary",
        "assets_helped_hurt_summary",
        "offset_coverage_summary",
        "main_hedge_gap",
        "data_quality_warnings",
        "diagnosis_summary_en",
    ):
        assert key in block, f"Missing key: {key}"


def test_linkage_to_block_3_2_and_3_3() -> None:
    out = _minimal_run()
    assert out["stress_results_v1"]["version"] == "stress_results_v1"
    assert out["hedge_gap_analysis_v1"]["version"] == "hedge_gap_analysis_v1"
    block = out[BLOCK_3_4_VERSION]
    assert isinstance(block.get("scenario_library"), dict)
    assert block["scenario_library"]["version"] == out["stress_results_v1"]["scenario_library"]["version"]


def test_worst_selectors_use_required_rules() -> None:
    out = _minimal_run()
    block = out[BLOCK_3_4_VERSION]
    ws = block["worst_synthetic_scenario"]
    assert ws["availability"] == "available"
    worst_id = ws["scenario_id"]
    # required: min portfolio_pnl_pct (same as Block 3.2 envelope.worst_synthetic)
    assert worst_id == out["stress_results_v1"]["envelope"]["worst_synthetic"]["scenario_id"]

    wh = block["worst_historical_scenario"]
    assert wh["availability"] == "available"
    # required: min max_dd (same as Block 3.2 envelope.worst_historical)
    assert wh["episode"] == out["stress_results_v1"]["envelope"]["worst_historical"]["episode"]


def test_no_mandate_pass_fail_language_inside_block() -> None:
    out = _minimal_run()
    block = out[BLOCK_3_4_VERSION]

    forbidden_keys = {
        "pass",
        "loss_ok",
        "max_dd_limit",
        "diagnostic_codes",
        "primary_diagnostic_code",
        "fail_reason_code",
        "failed_scenario",
        "failed_test",
    }

    def _walk(obj: object) -> list[str]:
        found: list[str] = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in forbidden_keys:
                    found.append(k)
                found.extend(_walk(v))
        elif isinstance(obj, list):
            for item in obj:
                found.extend(_walk(item))
        return found

    found = set(_walk(block))
    assert not found, f"Forbidden mandate keys found in Block 3.4: {sorted(found)}"

