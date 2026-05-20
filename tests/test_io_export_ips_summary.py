from __future__ import annotations

from pathlib import Path

from src.io_export import generate_ips_summary


def test_generate_ips_summary_adds_stress_decision_context(tmp_path: Path) -> None:
    out_path = tmp_path / "ips_summary.txt"
    cfg = {
        "target_vol_annual": 0.12,
        "target_max_drawdown_pct": 0.35,
        "horizon_years": 10,
        "investor_currency": "USD",
        "client_profile": "balanced",
    }
    run_result = {
        "status": "DIAG_ATTENTION",
        "weights": {"VOO": 0.6, "TLT": 0.4},
        "violations": [],
        "next_actions": [],
        "mandate_check": {
            "pass": True,
            "max_drawdown_realized": -0.22,
            "history_start": "2016-01-31",
            "history_end": "2026-01-31",
            "months_used": 120,
        },
        "stress_summary": {
            "diagnostic_status": "DIAG_ATTENTION",
            "diagnostic_codes": ["DIAG_LOSS_EQUITY_SHOCK"],
            "primary_diagnostic_code": "DIAG_LOSS_EQUITY_SHOCK",
            "worst_scenario_loss_pct": -0.31,
            "failed_scenario": "equity_shock",
        },
        "stress_diagnostic_report": {
            "stress_conclusions": {
                "overall_confidence": "medium",
                "worst_synthetic_scenario": {
                    "scenario_id": "equity_shock",
                    "portfolio_pnl_pct": -0.31,
                    "loss_severity": "high",
                },
                "worst_historical_episode": {
                    "episode": "covid_2020",
                    "pnl_real_episode": -0.18,
                    "loss_severity": "moderate",
                },
                "top_loss_assets_worst_scenario": [
                    {"ticker": "VOO", "pnl_pct": -0.19},
                    {"ticker": "HYG", "pnl_pct": -0.08},
                ],
            },
            "hedge_gap_analysis": {
                "status": "gap_detected",
                "worst_scenario_id": "equity_shock",
                "worst_scenario_portfolio_pnl_pct": -0.31,
            },
        },
    }

    path = generate_ips_summary(cfg, run_result, out_path)
    text = path.read_text(encoding="utf-8")

    assert path == out_path
    assert "Worst synthetic:" in text
    assert "equity_shock" in text
    assert "Main loss drivers:" in text
    assert "VOO" in text
    assert "Stress confidence:" in text
    assert "Hedge gap:" in text
    assert "gap_detected" in text
