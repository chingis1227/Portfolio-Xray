"""Deterministic inputs for Portfolio X-Ray golden contract tests (RM-949).

Regenerate the committed golden JSON after intentional contract changes:

    python tests/portfolio_xray_golden_inputs.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.portfolio_xray import build_portfolio_xray_v2


def _load_xray_test_helpers():
    path = _REPO_ROOT / "tests" / "test_portfolio_xray.py"
    spec = importlib.util.spec_from_file_location("portfolio_xray_test_helpers", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load test helpers from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_tx = _load_xray_test_helpers()
_analysis_setup = _tx._analysis_setup
_rich_stress_report = _tx._rich_stress_report
_sample_factor_regression_block = _tx._sample_factor_regression_block
_taxonomy_rows = _tx._taxonomy_rows
_window_metrics = _tx._window_metrics

GOLDEN_FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "portfolio_xray_golden_v2.json"


def golden_build_kwargs() -> dict[str, Any]:
    """Keyword arguments for ``build_portfolio_xray_v2`` that exercise the post-audit contract."""
    stress = {
        **_rich_stress_report(),
        "factor_betas_3y": {"beta_eq": 0.68, "beta_credit": 0.28, "beta_cmd": 0.16},
        "factor_regression_3y": _sample_factor_regression_block(n_obs=150, r2=0.48),
        "factor_regression_5y": _sample_factor_regression_block(n_obs=250, r2=0.50),
        "factor_regression_10y": _sample_factor_regression_block(
            n_obs=480, r2=0.55, betas={"beta_eq": 0.55, "beta_cmd": 0.12}
        ),
        "factor_betas_kalman": {
            "status": "available",
            "latest": {"beta_eq": 0.81, "beta_credit": 0.42},
            "uncertainty_by_beta": {"beta_eq": "low", "beta_credit": "moderate"},
        },
    }
    metrics = _window_metrics(
        120,
        cagr=0.08,
        vol=0.10,
        sharpe=0.6,
        mdd=-0.22,
        ttr_months=2.0,
        recovered=True,
    )
    metrics["downside_deviation"] = 0.065
    metrics["corr_base"] = 0.72
    metrics["downside_beta"] = 0.9
    metrics["upside_beta"] = 0.75
    metrics["skewness"] = -0.2
    metrics["kurtosis"] = 1.1
    metrics["metric_quality"] = {
        "n_obs": 118,
        "frequency": "monthly",
        "benchmark_ticker": "SPY",
        "risk_free_source": "FRED:DTB3",
        "window_months": 120,
        "analysis_end": "2026-04-30",
    }
    portfolio_windows = {
        "3y": _window_metrics(36, cagr=0.05, vol=0.08, sharpe=0.4, mdd=-0.10, ttr_months=3.0),
        "5y": _window_metrics(60, cagr=0.07, vol=0.09, sharpe=0.55, mdd=-0.15, ttr_months=4.0),
        "10y": metrics,
    }
    return {
        "analysis_setup": _analysis_setup(),
        "weights": {"SPY": 0.45, "TLT": 0.30, "HYG": 0.15, "GLD": 0.10},
        "rc_asset": [
            {"ticker": "SPY", "rc_pct": 0.40},
            {"ticker": "HYG", "rc_pct": 0.30},
            {"ticker": "TLT", "rc_pct": 0.20},
            {"ticker": "GLD", "rc_pct": 0.10},
        ],
        "stress_report": stress,
        "portfolio_valid": True,
        "portfolio_metrics": metrics,
        "portfolio_windows": portfolio_windows,
        "portfolio_analytics": {
            "tail_risk": {
                "method": "historical",
                "frequency": "daily",
                "window_label": "10y",
                "metric_available": True,
                "var_95": -0.02,
                "var_99": -0.03,
                "es_95": -0.03,
                "es_99": -0.04,
            },
            "rolling_sharpe_36m": {"last": 0.55, "mean": 0.5, "p10": 0.3, "p90": 0.7},
            "rolling_vol_12m": {"last": 0.11, "mean": 0.1, "p10": 0.08, "p90": 0.13},
            "rolling_beta_36m": {"last": 0.82, "mean": 0.8, "p10": 0.6, "p90": 0.95},
            "rolling_sharpe_12m": {"last": 0.48, "mean": 0.45, "p10": 0.2, "p90": 0.65},
            "eee_10pct": 42.5,
            "vol_of_vol": 0.04,
            "rel_vol_of_vol": 0.35,
        },
        "drawdown_structure": {
            "drawdowns": [
                {"depth": -0.22, "length_months": 8, "recovery_months": 4},
                {"depth": -0.08, "length_months": 3, "recovery_months": 2},
            ],
            "summary": {
                "recovery_median_months": 3.0,
                "recovery_p90_months": 4.0,
                "pct_time_underwater": 0.12,
                "longest_underwater_months": 10,
            },
            "by_threshold": {
                ">5%": {"count": 2, "recovery_median": 3.0, "recovery_p90": 4.0},
                ">10%": {"count": 1, "recovery_median": 4.0, "recovery_p90": 4.0},
                ">20%": {"count": 1, "recovery_median": 4.0, "recovery_p90": 4.0},
            },
        },
        "taxonomy_rows": _taxonomy_rows(),
        "taxonomy_sources": {ticker: "test_taxonomy" for ticker in _taxonomy_rows()},
    }


def build_golden_document() -> dict[str, Any]:
    return build_portfolio_xray_v2(**golden_build_kwargs())


def write_golden_fixture(path: Path | None = None) -> Path:
    from src.portfolio_xray import XRAY_SECTION_KEYS

    target = path or GOLDEN_FIXTURE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    doc = build_golden_document()
    ordered = dict(doc)
    ordered["sections"] = {key: doc["sections"][key] for key in XRAY_SECTION_KEYS}
    target.write_text(json.dumps(ordered, indent=2) + "\n", encoding="utf-8")
    return target


if __name__ == "__main__":
    out = write_golden_fixture()
    print(f"Wrote {out} ({out.stat().st_size} bytes)")
