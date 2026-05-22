"""Offline full-menu fixtures for optimizer fair-comparison readiness (Phase 17 / RM-1023)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

from src.config_schema import PortfolioConfig, validate_config
from src.portfolio_variants import (
    BaselineWeightsResult,
    build_maximum_diversification_constrained,
    build_minimum_cvar_constrained,
    build_minimum_variance_constrained,
    build_robust_mean_variance_constrained,
    maximum_diversification_baseline_metadata_export,
    minimum_cvar_baseline_metadata_export,
    minimum_variance_baseline_metadata_export,
    robust_mean_variance_baseline_metadata_export,
)
from src.snapshot import compute_candidate_config_fingerprint

FIXTURE_ANALYSIS_END = "2026-04-30"
FIXTURE_WINDOW_MONTHS = 120

# Optimizer candidates seeded with builder-produced metadata (default_v1 classic + robust).
FULL_MENU_OPTIMIZER_SEED_SPECS: tuple[tuple[str, str, Callable[..., BaselineWeightsResult], Callable], ...] = (
    (
        "minimum_variance",
        "minimum variance portfolio",
        build_minimum_variance_constrained,
        minimum_variance_baseline_metadata_export,
    ),
    (
        "maximum_diversification",
        "maximum diversification portfolio",
        build_maximum_diversification_constrained,
        maximum_diversification_baseline_metadata_export,
    ),
    (
        "minimum_cvar_constrained",
        "minimum cvar constrained portfolio",
        build_minimum_cvar_constrained,
        minimum_cvar_baseline_metadata_export,
    ),
    (
        "robust_mv_constrained",
        "robust mean variance constrained portfolio",
        build_robust_mean_variance_constrained,
        robust_mean_variance_baseline_metadata_export,
    ),
)


def synthetic_monthly_returns(
    tickers: list[str],
    *,
    n_months: int = FIXTURE_WINDOW_MONTHS,
    seed: int = 42,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2015-05-31", periods=n_months, freq="ME")
    data = {t: rng.normal(0.003, 0.02 + 0.005 * i, n_months) for i, t in enumerate(tickers)}
    return pd.DataFrame(data, index=dates)


def fixture_portfolio_config(tickers: list[str] | None = None) -> PortfolioConfig:
    symbols = tickers or ["VOO", "BND", "GLD"]
    n = len(symbols)
    eq = 1.0 / n if n else 0.0
    return validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": symbols,
            "weights": {t: eq for t in symbols},
            "windows_months": [36, 60, 120],
            "max_single_security_weight_pct": 0.45,
            "min_single_security_weight_pct": 0.02,
            "robust_mv_lambda": 0.25,
            "young_etf_optimization_policy": {"enabled": False},
        }
    )


def _snapshot_10y(
    cfg: PortfolioConfig,
    weights: dict[str, float],
    *,
    analysis_end: str = FIXTURE_ANALYSIS_END,
) -> dict[str, Any]:
    rc_rows = []
    for ticker, weight in sorted(weights.items()):
        if float(weight) <= 0:
            continue
        rc_rows.append({"ticker": ticker, "rc_pct": round(float(weight), 3)})
    if not rc_rows and weights:
        eq = round(1.0 / len(weights), 3)
        rc_rows = [{"ticker": t, "rc_pct": eq} for t in sorted(weights)]

    return {
        "analysis_end": analysis_end,
        "window_label": "10y",
        "metrics": {
            "cagr": 0.05,
            "vol_annual": 0.08,
            "max_drawdown": -0.12,
            "sharpe": 0.55,
        },
        "stress_suite_results": {
            "overall": "PASS",
            "fail_reason_code": None,
            "failed_scenario": None,
        },
        "final_weights_total": dict(weights),
        "RC_asset": rc_rows,
        "candidate_config_fingerprint": compute_candidate_config_fingerprint(cfg),
    }


def _subject_sidecar(main: Path, cfg: PortfolioConfig) -> None:
    subject = main / "analysis_subject"
    subject.mkdir(parents=True, exist_ok=True)
    with open(subject / "snapshot_10y.json", "w", encoding="utf-8") as handle:
        json.dump(
            {
                "analysis_end": FIXTURE_ANALYSIS_END,
                "metrics": {"cagr": 0.06, "vol_annual": 0.1},
            },
            handle,
        )
    with open(subject / "run_metadata.json", "w", encoding="utf-8") as handle:
        json.dump(
            {
                "run_info": {"analysis_end_date": FIXTURE_ANALYSIS_END},
                "analysis_setup": {
                    "analysis_portfolio": {"portfolio_role": "model_portfolio"},
                },
            },
            handle,
        )


def seed_optimizer_candidate_folder(
    root: Path,
    candidate_id: str,
    folder_name: str,
    build_fn: Callable[..., BaselineWeightsResult],
    metadata_export: Callable[[dict[str, object]], dict[str, Any]],
    cfg: PortfolioConfig,
    monthly_returns: pd.DataFrame,
) -> dict[str, Any]:
    """Run builder, write weights + baseline metadata + snapshot/stress for comparison."""
    result = build_fn(cfg, monthly_returns, FIXTURE_ANALYSIS_END, FIXTURE_WINDOW_MONTHS)
    assert result.status in ("OK", "APPROXIMATE"), (
        f"{candidate_id} builder failed: {result.status} {result.diagnostics.get('reason')}"
    )
    meta_export = metadata_export(result.diagnostics)
    orm = meta_export.get("optimizer_run_metadata") or {}
    assert orm.get("schema_version") == "candidate_optimizer_run_metadata_v1"
    fingerprints = orm.get("input_fingerprints") or {}
    assert len(str(fingerprints.get("config_fingerprint") or "")) == 64
    assert len(str(fingerprints.get("returns_panel_fingerprint") or "")) == 64
    solver = orm.get("solver") or {}
    assert solver.get("optimization_quality_status") == "clean_solve"

    folder = root / folder_name
    folder.mkdir(parents=True, exist_ok=True)
    weights = {k: float(v) for k, v in result.weights.items() if float(v) > 1e-9}
    if not weights:
        weights = {t: 1.0 / len(cfg.tickers) for t in cfg.tickers}

    with open(folder / "weights.json", "w", encoding="utf-8") as handle:
        json.dump(weights, handle, indent=2)
    with open(folder / "baseline_weights_metadata.json", "w", encoding="utf-8") as handle:
        json.dump(meta_export, handle, indent=2)
    with open(folder / "snapshot_10y.json", "w", encoding="utf-8") as handle:
        json.dump(_snapshot_10y(cfg, weights), handle, indent=2)
    with open(folder / "stress_report.json", "w", encoding="utf-8") as handle:
        json.dump({"overall": "PASS", "status": "PASS"}, handle, indent=2)

    return {
        "candidate_id": candidate_id,
        "optimization_quality_status": solver.get("optimization_quality_status"),
        "method_id": orm.get("method_id"),
    }


def seed_full_menu_optimizer_artifacts(
    project_root: Path,
    cfg: PortfolioConfig | None = None,
) -> tuple[PortfolioConfig, str, list[dict[str, Any]]]:
    """Seed analysis_subject + four optimizer folders with live builder metadata."""
    cfg = cfg or fixture_portfolio_config()
    returns = synthetic_monthly_returns(list(cfg.tickers))
    main = project_root / "Main portfolio"
    main.mkdir(parents=True, exist_ok=True)
    _subject_sidecar(main, cfg)

    steps: list[dict[str, Any]] = []
    for candidate_id, folder_name, build_fn, export_fn in FULL_MENU_OPTIMIZER_SEED_SPECS:
        info = seed_optimizer_candidate_folder(
            project_root, candidate_id, folder_name, build_fn, export_fn, cfg, returns
        )
        fp = compute_candidate_config_fingerprint(cfg)
        steps.append(
            {
                "candidate_id": candidate_id,
                "status": "succeeded",
                "freshness_status": "fresh",
                "snapshot_analysis_end": FIXTURE_ANALYSIS_END,
                "expected_analysis_end": FIXTURE_ANALYSIS_END,
                "expected_config_fingerprint": fp,
                "snapshot_config_fingerprint": fp,
                "optimization_quality_status": info["optimization_quality_status"],
            }
        )

    fp = compute_candidate_config_fingerprint(cfg)
    with open(main / "candidate_factory_run.json", "w", encoding="utf-8") as handle:
        json.dump(
            {
                "factory_profile_id": "default_v1",
                "generated_at": "2026-05-22T12:00:00+00:00",
                "analysis_end": FIXTURE_ANALYSIS_END,
                "config_fingerprint": fp,
                "steps": steps,
            },
            handle,
        )
    return cfg, fp, steps


def fair_ready_optimizer_ids(comparison_doc: dict[str, Any]) -> list[str]:
    ready: list[str] = []
    for row in comparison_doc.get("candidates") or []:
        if row.get("role") != "optimizer_candidate":
            continue
        disclosure = row.get("construction_disclosure") or {}
        readiness = disclosure.get("optimization_readiness") or {}
        if readiness.get("fair_comparison_ready") is True:
            ready.append(str(row["candidate_id"]))
    return sorted(ready)


def full_menu_fair_ready_fingerprint(comparison_doc: dict[str, Any]) -> dict[str, Any]:
    ready = fair_ready_optimizer_ids(comparison_doc)
    return {
        "fair_ready_optimizer_ids": ready,
        "fair_ready_count": len(ready),
        "menu_profile": (comparison_doc.get("candidate_menu") or {}).get("factory_profile_id"),
    }
