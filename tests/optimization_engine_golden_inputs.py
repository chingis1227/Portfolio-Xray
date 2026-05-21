"""Deterministic inputs for Optimization Engine golden contract tests (RM-1001).

Regenerate committed golden JSON after intentional contract changes:

    python tests/optimization_engine_golden_inputs.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from run_optimization import _build_legacy_policy_optimizer_run_metadata
from src.candidate_comparison import build_candidate_comparison
from src.config_schema import validate_config
from src.portfolio_variants import _candidate_optimizer_run_metadata
from src.snapshot import compute_candidate_config_fingerprint

_FIXTURES = Path(__file__).resolve().parent / "fixtures"
LEGACY_METADATA_GOLDEN_PATH = _FIXTURES / "legacy_policy_optimizer_run_metadata_golden_v1.json"
CANDIDATE_METADATA_GOLDEN_PATH = _FIXTURES / "candidate_optimizer_run_metadata_golden_v1.json"
COMPARISON_BLOCK5_GOLDEN_PATH = _FIXTURES / "optimization_comparison_block5_golden_v1.json"

GOLDEN_ANALYSIS_END = "2026-04-30"
GOLDEN_RETURNS_PANEL_FINGERPRINT = (
    "a1b2c3d4e5f6789012345678abcdef0123456789abcdef0123456789abcdef01"
)
GOLDEN_CONFIG_FINGERPRINT = (
    "fedcba0987654321fedcba0987654321fedcba0987654321fedcba0987654321"
)
GOLDEN_UNIVERSE_FINGERPRINT = (
    "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
)


def _golden_cfg() -> SimpleNamespace:
    return SimpleNamespace(
        tickers=["VOO", "BND", "GLD"],
        min_single_security_weight_pct=0.02,
        max_single_security_weight_pct=0.35,
        young_etf_optimization_policy={"enabled": True},
    )


def _golden_returns_window() -> pd.DataFrame:
    return pd.DataFrame(
        {"VOO": [0.01, 0.02, 0.015], "BND": [0.003, 0.004, 0.002], "GLD": [0.0, 0.01, 0.005]},
        index=pd.to_datetime(["2026-02-28", "2026-03-31", "2026-04-30"]),
    )


def normalize_legacy_metadata(meta: dict[str, Any]) -> dict[str, Any]:
    """Normalize volatile hashes for committed golden comparison."""
    out = json.loads(json.dumps(meta))
    for key in ("returns_panel_fingerprint", "config_fingerprint", "universe_fingerprint"):
        if isinstance(out.get("input_fingerprints"), dict):
            out["input_fingerprints"][key] = (
                GOLDEN_RETURNS_PANEL_FINGERPRINT
                if key == "returns_panel_fingerprint"
                else GOLDEN_CONFIG_FINGERPRINT
                if key == "config_fingerprint"
                else GOLDEN_UNIVERSE_FINGERPRINT
            )
    for block in ("expected_returns", "covariance"):
        if isinstance(out.get(block), dict):
            if "returns_panel_fingerprint" in out[block]:
                out[block]["returns_panel_fingerprint"] = GOLDEN_RETURNS_PANEL_FINGERPRINT
            cov = out[block].get("methodology")
            if isinstance(cov, dict) and "returns_panel_fingerprint" in cov:
                cov["returns_panel_fingerprint"] = GOLDEN_RETURNS_PANEL_FINGERPRINT
    if isinstance(out.get("universe"), dict):
        out["universe"]["universe_fingerprint"] = GOLDEN_UNIVERSE_FINGERPRINT
    return out


def normalize_candidate_metadata(meta: dict[str, Any]) -> dict[str, Any]:
    return normalize_legacy_metadata(meta)


def build_golden_legacy_policy_metadata() -> dict[str, Any]:
    meta = _build_legacy_policy_optimizer_run_metadata(
        _golden_cfg(),
        optimization_status="OK | OBJECTIVE_MODE=max_return | SOFT_VOL_TARGET=0.1200 LAMBDA=12",
        production_status="APPROVED",
        analysis_end=GOLDEN_ANALYSIS_END,
        returns_frequency="monthly",
        periods_per_year=12,
        window_months=120,
        secondary_window_months=60,
        risk_tickers_all=["VOO", "BND", "GLD"],
        eligible_universe=["VOO", "BND", "GLD"],
        cash_proxy_ticker="BIL",
        covariance_shrinkage=True,
        dual_covariance_enabled=False,
        young_diagnostics=None,
        per_ticker_young_caps=None,
        soft_target_vol_annual=0.12,
        soft_vol_penalty_lambda=12.0,
        soft_target_return_annual=0.06,
        soft_return_penalty_lambda=8.0,
        liquidity_floor_pct=0.05,
        current_vol_annual=0.11,
        target_vol_annual=0.12,
        cash_policy="allowed",
        mandate_gate_passed=True,
        weights_written=True,
        estimator_returns_window=_golden_returns_window(),
    )
    return normalize_legacy_metadata(meta)


def _golden_candidate_diagnostics() -> dict[str, object]:
    return {
        "optimizer_name": "minimum_variance_constrained",
        "objective": "minimize portfolio variance (monthly)",
        "analysis_end": GOLDEN_ANALYSIS_END,
        "window_months": 120,
        "returns_panel_start": "2016-05-31",
        "returns_panel_end": GOLDEN_ANALYSIS_END,
        "returns_panel_rows": 120,
        "returns_panel_fingerprint": GOLDEN_RETURNS_PANEL_FINGERPRINT,
        "config_fingerprint": GOLDEN_CONFIG_FINGERPRINT,
        "universe_fingerprint": GOLDEN_UNIVERSE_FINGERPRINT,
        "estimator_input_columns": ["VOO", "BND"],
        "eligible_universe": ["VOO", "BND"],
        "covariance_method": "ledoit_wolf",
        "covariance_source": "monthly_return_panel",
        "shrinkage_used": True,
        "shrinkage_applied": True,
        "psd_repair_used": False,
        "psd_status": "already_psd",
        "young_etf_policy_enabled": False,
        "young_etf_policy_role": "not_used",
        "solver": "SLSQP",
        "solver_success": True,
        "solver_status": "OK",
        "solver_message": "golden_fixture",
        "fallback_used": False,
        "active_constraints": ["long_only", "fully_invested", "box_bounds"],
        "constraints_used": ["long_only", "fully_invested", "box_bounds"],
        "constraints_not_used": ["volatility_target"],
        "bounds_used": True,
        "constraint_summary": "long-only fully invested with box bounds",
        "final_weights": {"VOO": 0.55, "BND": 0.45},
        "portfolio_variance": 0.00042,
        "annualized_volatility": 0.08,
        "objective_value": 0.00042,
    }


def build_golden_candidate_optimizer_metadata() -> dict[str, Any]:
    return normalize_candidate_metadata(
        _candidate_optimizer_run_metadata(_golden_candidate_diagnostics())
    )


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _snapshot_10y(cfg: object) -> dict[str, Any]:
    return {
        "analysis_end": GOLDEN_ANALYSIS_END,
        "window_label": "10y",
        "metrics": {"cagr": 0.05, "vol_annual": 0.08, "max_drawdown": -0.1},
        "stress_suite_results": {
            "overall": "PASS",
            "fail_reason_code": None,
            "failed_scenario": None,
        },
        "final_weights_total": {"VOO": 0.55, "BND": 0.45},
        "candidate_config_fingerprint": compute_candidate_config_fingerprint(cfg),
    }


def build_golden_comparison_block5() -> dict[str, Any]:
    """Minimal comparison row construction_disclosure for Block 5 post-audit surface."""
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    with tempfile.TemporaryDirectory(prefix="oe_golden_") as tmp:
        root = Path(tmp)
        main = root / "Main portfolio"
        main.mkdir()
        subject = main / "analysis_subject"
        subject.mkdir()
        _write_json(
            subject / "snapshot_10y.json",
            {"analysis_end": GOLDEN_ANALYSIS_END, "metrics": {"cagr": 0.06}},
        )
        _write_json(
            subject / "run_metadata.json",
            {
                "run_info": {"analysis_end_date": GOLDEN_ANALYSIS_END},
                "analysis_setup": {
                    "analysis_portfolio": {"portfolio_role": "model_portfolio"},
                },
            },
        )

        mv = root / "minimum variance portfolio"
        mv.mkdir()
        _write_json(mv / "snapshot_10y.json", _snapshot_10y(cfg))
        _write_json(mv / "weights.json", {"VOO": 0.55, "BND": 0.45})
        _write_json(mv / "stress_report.json", {"overall": "PASS"})
        _write_json(
            mv / "baseline_weights_metadata.json",
            {"optimizer_run_metadata": build_golden_candidate_optimizer_metadata()},
        )

        fp = compute_candidate_config_fingerprint(cfg)
        _write_json(
            main / "candidate_factory_run.json",
            {
                "factory_profile_id": "default_v1",
                "steps": [
                    {
                        "candidate_id": "minimum_variance",
                        "status": "succeeded",
                        "freshness_status": "fresh",
                        "snapshot_analysis_end": GOLDEN_ANALYSIS_END,
                        "expected_analysis_end": GOLDEN_ANALYSIS_END,
                        "expected_config_fingerprint": fp,
                        "snapshot_config_fingerprint": fp,
                        "optimization_quality_status": "clean_solve",
                    }
                ],
            },
        )

        doc = build_candidate_comparison(cfg, project_root=root)
        row = next(c for c in doc["candidates"] if c["candidate_id"] == "minimum_variance")
        disclosure = row["construction_disclosure"]
        return {
            "candidate_id": "minimum_variance",
            "role": row["role"],
            "status": row["status"],
            "construction_disclosure": {
                "disclosure_status": disclosure.get("disclosure_status"),
                "optimizer_methodology": disclosure.get("optimizer_methodology"),
                "optimizer_quality": disclosure.get("optimizer_quality"),
                "optimization_readiness": disclosure.get("optimization_readiness"),
            },
        }


def write_golden_fixtures() -> tuple[Path, Path, Path]:
    _FIXTURES.mkdir(parents=True, exist_ok=True)
    legacy_path = LEGACY_METADATA_GOLDEN_PATH
    candidate_path = CANDIDATE_METADATA_GOLDEN_PATH
    block5_path = COMPARISON_BLOCK5_GOLDEN_PATH
    _write_json(legacy_path, build_golden_legacy_policy_metadata())
    _write_json(candidate_path, build_golden_candidate_optimizer_metadata())
    _write_json(block5_path, build_golden_comparison_block5())
    return legacy_path, candidate_path, block5_path


if __name__ == "__main__":
    paths = write_golden_fixtures()
    for path in paths:
        print(f"Wrote {path} ({path.stat().st_size} bytes)")
