"""P0: diagnostic consumers must not use or disclose data after analysis_end."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.io_export import save_inputs
from src.scenario_library import build_scenario_library
from src.stress_factors import FACTOR_COLUMN_ORDER, FACTOR_TO_BETA_KEY
from src.stress_scenario_analytics import build_stress_scenario_analytics
from src.windows import truncate_to_analysis_end

ANALYSIS_END = "2026-04-30"


def _beta_map(val: float = 0.1) -> dict[str, float]:
    return {FACTOR_TO_BETA_KEY[f]: float(val) for f in FACTOR_COLUMN_ORDER if f in FACTOR_TO_BETA_KEY}


def _factor_cov_nested(scale: float = 1e-4) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for f in FACTOR_COLUMN_ORDER:
        row: dict[str, float] = {}
        for g in FACTOR_COLUMN_ORDER:
            row[str(g)] = float(scale) if f == g else 0.0
        out[str(f)] = row
    return out


def _minimal_stress_report() -> dict:
    betas = _beta_map(0.05)
    return {
        "scenario_results": [
            {
                "scenario_id": "equity_shock",
                "shock_vector": {
                    "shock_eq": -0.10,
                    "shock_rr": 0.0,
                    "shock_credit": 0.0,
                    "shock_inf": 0.0,
                    "shock_usd": 0.0,
                    "shock_cmd": 0.0,
                },
                "portfolio_pnl_pct": -1.25,
            }
        ],
        "historical_results": [],
        "factor_betas_5y": betas,
        "factor_betas_10y": betas,
        "factor_regression_5y": {"betas": betas, "n_obs": 200, "r2": 0.2, "adj_r2": 0.15},
        "factor_regression_10y": {"betas": betas, "n_obs": 400, "r2": 0.22, "adj_r2": 0.16},
        "factor_covariance": {
            "base": {
                "matrix": _factor_cov_nested(1e-4),
                "n_obs": 260,
                "window": {"analysis_end": ANALYSIS_END},
            },
        },
        "factor_betas_adjusted": {"adjusted": {k: v * 0.95 for k, v in betas.items()}},
        "synthetic_factor_pnl_adjusted": {
            "scenarios": [
                {
                    "scenario_id": "equity_shock",
                    "pnl_model_raw": -1.2,
                    "pnl_model_adjusted": -1.0,
                }
            ]
        },
    }


def _returns_with_future_tail() -> pd.DataFrame:
    idx = pd.date_range("2024-01-31", "2026-05-31", freq="ME")
    rng = np.random.default_rng(1)
    return pd.DataFrame(
        {"VOO": rng.normal(0.005, 0.02, len(idx)), "BND": rng.normal(0.002, 0.01, len(idx))},
        index=idx,
    )


def test_truncate_to_analysis_end_drops_later_rows():
    r = _returns_with_future_tail()
    eff = truncate_to_analysis_end(r, ANALYSIS_END)
    assert eff.index.max().strftime("%Y-%m-%d") == ANALYSIS_END
    assert len(eff) < len(r)


def test_stress_scenario_analytics_data_end_respects_analysis_end():
    monthly_returns = _returns_with_future_tail()
    rep = _minimal_stress_report()
    out = build_stress_scenario_analytics(
        stress_report=rep,
        weights={"VOO": 0.6, "BND": 0.4},
        tickers=["VOO", "BND"],
        monthly_returns=monthly_returns,
        factor_returns_weekly=None,
        cash_proxy_ticker="BIL",
        analysis_end_str=ANALYSIS_END,
    )
    scen = out["scenarios"]["equity_shock"]
    data_end = scen["asset_covariance"]["data_end"]
    assert data_end is not None
    assert pd.Timestamp(data_end) <= pd.Timestamp(ANALYSIS_END)


def test_scenario_library_base_layer_data_end_respects_analysis_end():
    monthly_returns = _returns_with_future_tail()
    rep = _minimal_stress_report()
    rep["stress_scenario_analytics"] = build_stress_scenario_analytics(
        stress_report=rep,
        weights={"VOO": 0.6, "BND": 0.4},
        tickers=["VOO", "BND"],
        monthly_returns=monthly_returns,
        factor_returns_weekly=None,
        cash_proxy_ticker="BIL",
        analysis_end_str=ANALYSIS_END,
    )
    out = build_scenario_library(
        rep,
        weights={"VOO": 0.6, "BND": 0.4},
        tickers=["VOO", "BND"],
        monthly_returns=monthly_returns,
        analysis_end_str=ANALYSIS_END,
        cash_proxy_ticker="BIL",
    )
    syn = next(s for s in out["scenarios"] if s.get("scenario_id") == "equity_shock")
    ac = syn.get("asset_covariance") or {}
    data_end = ac.get("data_end")
    if data_end:
        assert pd.Timestamp(data_end) <= pd.Timestamp(ANALYSIS_END)


def test_save_inputs_writes_effective_returns_and_optional_raw(tmp_path: Path):
    raw = _returns_with_future_tail()
    eff = truncate_to_analysis_end(raw, ANALYSIS_END)
    prices = eff.copy()
    rf = pd.Series(0.0001, index=eff.index)
    bench = eff["VOO"]
    cash = pd.Series(0.0, index=eff.index)

    save_inputs(
        tmp_path,
        prices,
        eff,
        rf,
        bench,
        cash,
        monthly_returns_raw=raw,
        analysis_end=ANALYSIS_END,
    )

    eff_csv = pd.read_csv(tmp_path / "inputs" / "monthly_returns.csv", index_col=0, parse_dates=True)
    assert eff_csv.index.max().strftime("%Y-%m-%d") == ANALYSIS_END

    raw_path = tmp_path / "inputs" / "monthly_returns_raw.csv"
    assert raw_path.is_file()
    raw_csv = pd.read_csv(raw_path, index_col=0, parse_dates=True)
    assert raw_csv.index.max().strftime("%Y-%m-%d") == "2026-05-31"

    manifest = json.loads((tmp_path / "inputs" / "inputs_manifest.json").read_text(encoding="utf-8"))
    assert manifest["analysis_end"] == ANALYSIS_END
    assert manifest["monthly_returns_effective"] == "monthly_returns.csv"
    assert manifest["monthly_returns_raw"] == "monthly_returns_raw.csv"
