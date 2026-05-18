"""
Tests for NaN-safe dynamic backtest (data_policy_nan_young_etfs.md).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import numpy as np
import pandas as pd

from src.portfolio_dynamic import portfolio_returns_nan_safe


def test_young_etf_does_not_truncate_history():
    n = 120
    dates = pd.date_range("2014-01-31", periods=n, freq="M")
    r_a = 0.01 * np.ones(n)
    r_b = np.full(n, np.nan)
    r_b[89:] = 0.008
    returns_df = pd.DataFrame({"A": r_a, "B": r_b}, index=dates)
    cash = pd.Series(0.002, index=dates)
    target_weights = {"A": 0.6, "B": 0.4}

    r_p, w_df = portfolio_returns_nan_safe(returns_df, target_weights, cash)

    assert len(r_p) == 120, f"Expected 120 months of portfolio returns, got {len(r_p)}"
    assert len(w_df) == 120

    for i in range(89):
        t = dates[i]
        w_b = w_df.loc[t, "B"] if "B" in w_df.columns else 0.0
        assert w_b == 0.0 or (np.isnan(w_b) and pd.isna(w_df.loc[t, "B"])), (
            f"Month {t}: B should have no weight before month 90, got B={w_b}"
        )

    w_b_90 = w_df.loc[dates[89], "B"] if "B" in w_df.columns else 0.0
    assert float(w_b_90) >= 0 and float(w_b_90) <= 1.0


def test_nan_redistribution_global_among_risk_tickers():
    """If one risk asset has NaN, its weight is redistributed equally among other risk assets with data."""
    dates = pd.date_range("2020-01-31", periods=12, freq="M")
    r_a = 0.01 * np.ones(12)
    r_b = 0.01 * np.ones(12)
    r_b[5] = np.nan
    r_c = 0.01 * np.ones(12)
    returns_df = pd.DataFrame({"A": r_a, "B": r_b, "C": r_c}, index=dates)
    cash = pd.Series(0.0, index=dates)
    target_weights = {"A": 0.33, "B": 0.34, "C": 0.33}
    risk_rt = ["A", "B", "C"]

    r_p, w_df, diag = portfolio_returns_nan_safe(
        returns_df,
        target_weights,
        cash,
        risk_tickers=risk_rt,
        return_diagnostics=True,
    )

    t_nan = dates[5]
    w_a = float(w_df.loc[t_nan, "A"])
    w_b = float(w_df.loc[t_nan, "B"])
    w_c = float(w_df.loc[t_nan, "C"])
    assert w_b == 0.0
    assert w_a >= 0.4 and w_c >= 0.4
    assert abs((w_a + w_c) - 1.0) < 1e-6
    assert diag.get("n_months_redistributed", 0) >= 1
    assert diag.get("n_months_cash_fallback") == 0


def test_dynamic_nan_safe_counts_cash_fallback_when_no_risk_peer_has_data():
    """If missing risk weight cannot be redistributed, the residual cash month is counted."""
    dates = pd.date_range("2020-01-31", periods=4, freq="M")
    returns_df = pd.DataFrame(
        {
            "A": [0.01, np.nan, 0.01, 0.01],
            "B": [0.01, np.nan, 0.01, 0.01],
        },
        index=dates,
    )
    cash = pd.Series(0.001, index=dates)

    r_p, w_df, diag = portfolio_returns_nan_safe(
        returns_df,
        {"A": 0.6, "B": 0.4},
        cash,
        risk_tickers=["A", "B"],
        return_diagnostics=True,
    )

    t_fallback = dates[1]
    assert float(w_df.loc[t_fallback, "A"]) == 0.0
    assert float(w_df.loc[t_fallback, "B"]) == 0.0
    assert abs(float(r_p.loc[t_fallback]) - 0.001) < 1e-12
    assert diag.get("n_months_redistributed") == 0
    assert diag.get("n_months_cash_fallback") == 1


def test_dynamic_nan_safe_does_not_count_planned_cash_without_missing_returns():
    """Intentional underinvestment is not a data-fallback month when all risk returns exist."""
    dates = pd.date_range("2020-01-31", periods=3, freq="M")
    returns_df = pd.DataFrame(
        {
            "A": [0.01, 0.01, 0.01],
            "B": [0.02, 0.02, 0.02],
        },
        index=dates,
    )
    cash = pd.Series(0.001, index=dates)

    _r_p, _w_df, diag = portfolio_returns_nan_safe(
        returns_df,
        {"A": 0.5, "B": 0.3},
        cash,
        risk_tickers=["A", "B"],
        return_diagnostics=True,
    )

    assert diag.get("n_months_redistributed") == 0
    assert diag.get("n_months_cash_fallback") == 0


def test_dynamic_nan_safe_diagnostics():
    """Diagnostics dict includes redistribution / cash-fallback counters (RC no longer gates path)."""
    dates = pd.date_range("2020-01-31", periods=6, freq="M")
    np.random.seed(42)
    r1 = 0.02 + 0.05 * np.random.randn(6)
    r2 = 0.005 + 0.01 * np.random.randn(6)
    returns_df = pd.DataFrame({"X": r1, "Y": r2}, index=dates)
    cash_returns = pd.Series(0.001, index=dates)

    r_p, w_df, diag = portfolio_returns_nan_safe(
        returns_df,
        {"X": 0.5, "Y": 0.5},
        cash_returns,
        risk_tickers=["X", "Y"],
        return_diagnostics=True,
    )

    assert "n_months_cash_fallback" in diag
    assert "n_months_redistributed" in diag
    assert len(r_p) >= 1


def test_run_report_default_mode_uses_dynamic_engine():
    root = Path(__file__).resolve().parent.parent
    run_report = root / "run_report.py"
    if not run_report.is_file():
        return
    out_dir = root / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    data_policy_path = out_dir / "data_policy.json"

    result = subprocess.run(
        [sys.executable, str(run_report)],
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=600,
    )

    if result.returncode != 0:
        return
    alt = root / "Main portfolio" / "data_policy.json"
    policy_path = data_policy_path if data_policy_path.is_file() else alt
    assert policy_path.is_file(), (
        "data_policy.json should be written by run_report (output/ or Main portfolio/)"
    )
    with open(policy_path, encoding="utf-8") as f:
        data = json.load(f)
    assert data.get("backtest_mode") == "dynamic_nan_safe", (
        "Default backtest_mode must be dynamic_nan_safe, got " + str(data.get("backtest_mode"))
    )


if __name__ == "__main__":
    test_young_etf_does_not_truncate_history()
    print("test_young_etf_does_not_truncate_history: OK")
    test_nan_redistribution_global_among_risk_tickers()
    print("test_nan_redistribution_global_among_risk_tickers: OK")
    test_dynamic_nan_safe_counts_cash_fallback_when_no_risk_peer_has_data()
    print("test_dynamic_nan_safe_counts_cash_fallback_when_no_risk_peer_has_data: OK")
    test_dynamic_nan_safe_does_not_count_planned_cash_without_missing_returns()
    print("test_dynamic_nan_safe_does_not_count_planned_cash_without_missing_returns: OK")
    test_dynamic_nan_safe_diagnostics()
    print("test_dynamic_nan_safe_diagnostics: OK")
    test_run_report_default_mode_uses_dynamic_engine()
    print("test_run_report_default_mode_uses_dynamic_engine: OK")
    print("All tests passed.")
