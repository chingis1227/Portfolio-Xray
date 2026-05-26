"""Core MVP stress: diagnostic loss_gate_mode without client mandate pass/fail."""
from __future__ import annotations

import pandas as pd

from src.stress import LOSS_GATE_MODE_DIAGNOSTIC, LOSS_GATE_MODE_MANDATE, run_stress


def _long_history_run(**kwargs: object) -> dict:
    idx = pd.date_range("1995-01-31", periods=360, freq="ME")
    monthly_returns = pd.DataFrame(
        {"AAA": [0.008] * len(idx), "BBB": [0.006] * len(idx)},
        index=idx,
    )
    tickers = ["AAA", "BBB"]
    weights = {"AAA": 0.99, "BBB": 0.01}
    asset_betas = pd.DataFrame(columns=["beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd"])
    portfolio_betas = {k: 0.05 for k in ("beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd")}
    defaults = dict(
        tickers=tickers,
        weights=weights,
        monthly_returns=monthly_returns,
        asset_betas=asset_betas,
        portfolio_betas=portfolio_betas,
        target_max_drawdown_pct=0.05,
        cash_proxy_ticker="",
        loss_gate_mode=LOSS_GATE_MODE_DIAGNOSTIC,
    )
    defaults.update(kwargs)
    return run_stress(**defaults)  # type: ignore[arg-type]


def test_diagnostic_mode_skips_mandate_pass_fail() -> None:
    out = _long_history_run()
    assert out["loss_gate_mode"] == LOSS_GATE_MODE_DIAGNOSTIC
    assert out["max_dd_limit"] is None
    assert out["status"] in {"ok", "warning", "insufficient_data"}
    assert out["status"] not in {"DIAG_PASS", "DIAG_ATTENTION", "DIAG_PASS_WITH_WARNING"}
    assert not out.get("fail_reason_code")
    for row in out["scenario_results"]:
        assert row.get("pass") is None
        assert row.get("loss_ok") is None
        assert not row.get("diagnostic_codes")


def test_mandate_mode_still_applies_loss_gate() -> None:
    idx = pd.date_range("1995-01-31", periods=360, freq="ME")
    monthly_returns = pd.DataFrame({"AAA": [0.008] * len(idx), "BBB": [0.006] * len(idx)}, index=idx)
    out = run_stress(
        tickers=["AAA", "BBB"],
        weights={"AAA": 0.99, "BBB": 0.01},
        monthly_returns=monthly_returns,
        asset_betas=pd.DataFrame(columns=["beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd"]),
        portfolio_betas={k: 0.05 for k in ("beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd")},
        target_max_drawdown_pct=0.05,
        cash_proxy_ticker="",
        loss_gate_mode=LOSS_GATE_MODE_MANDATE,
    )
    assert out["loss_gate_mode"] == LOSS_GATE_MODE_MANDATE
    assert out["max_dd_limit"] == 0.05
    assert out["status"] in {"DIAG_PASS", "DIAG_PASS_WITH_WARNING", "DIAG_ATTENTION"}
    assert any(row.get("loss_ok") is not None for row in out["scenario_results"])
