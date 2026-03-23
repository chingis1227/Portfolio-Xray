"""Smoke tests for auto-generated commentary.txt."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.portfolio_commentary import write_portfolio_commentary


def test_write_portfolio_commentary_creates_file(tmp_path: Path) -> None:
    final = tmp_path / "risk parity portfolio"
    csv_dir = final / "results_csv"
    csv_dir.mkdir(parents=True)
    pd.DataFrame(
        [{"window_months": 120, "cagr": 0.08, "vol_annual": 0.07, "sharpe": 0.9, "sortino": 1.2,
          "beta_portfolio": 0.5, "max_drawdown": -0.1, "corr_base": 0.3, "treynor": 0.1}]
    ).to_csv(csv_dir / "portfolio_metrics_10y.csv", index=False)
    s = pd.Series({"A": 0.2, "B": 0.2, "C": 0.2, "D": 0.2, "E": 0.2})
    s.round(3).to_csv(csv_dir / "rc_vol_10y.csv", header=True)

    stress = {
        "status": "FAIL_STRESS",
        "fail_reason_code": "FAIL_X",
        "failed_scenario": "credit_shock",
        "failed_test": "Loss",
        "worst_scenario_loss_pct": -0.2,
        "scenario_results": [
            {"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.05, "pass": True},
        ],
    }
    pm = {
        "cagr": 0.08,
        "vol_annual": 0.07,
        "max_drawdown": -0.1,
        "sharpe": 0.9,
        "sortino": 1.2,
        "beta_portfolio": 0.5,
        "corr_base": 0.3,
        "treynor": 0.1,
    }
    out = write_portfolio_commentary(
        final,
        output_dir_csv=csv_dir,
        portfolio_metrics_10y=pm,
        stress_report=stress,
        portfolio_valid=True,
        analysis_end="2026-02-28",
    )
    assert out is not None
    assert out.is_file()
    text = out.read_text(encoding="utf-8")
    assert "Executive Summary" in text
    assert "FAIL_STRESS" in text
    assert "credit_shock" in text
    assert "Risk-Parity baseline" in text or "Risk-Parity" in text
