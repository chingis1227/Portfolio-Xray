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

from src.portfolio_xray import build_portfolio_xray_v2

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


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
        "factor_regression_5y": _sample_factor_regression_block(n_obs=250, r2=0.50),
        "factor_regression_10y": _sample_factor_regression_block(
            n_obs=480, r2=0.55, betas={"beta_eq": 0.55, "beta_cmd": 0.12}
        ),
        "factor_betas_kalman": {
            "status": "available",
            "latest": {"beta_eq": 0.81, "beta_credit": 0.42},
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
                "es_95": -0.03,
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
