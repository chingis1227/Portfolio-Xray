"""Synthetic workspace fixtures for offline MVP pipeline smoke tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from src.analysis_setup import build_analysis_setup
from src.config_schema import PortfolioConfig, validate_config
from src.input_assumptions import build_input_assumptions_from_analysis_setup
from src.block_2_1_asset_allocation import build_block_2_1_asset_allocation
from src.portfolio_xray import PORTFOLIO_XRAY_VERSION, XRAY_SECTION_KEYS
from src.snapshot import compute_candidate_config_fingerprint
from src.current_portfolio_stress_scorecard_block import build_current_portfolio_stress_scorecard_v1
from src.hedge_gap_analysis_block import empty_hedge_gap_analysis_v1
from src.stress_results_block import empty_stress_results_v1

MVP_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "mvp_portfolios"

DEFAULT_ANALYSIS_END = "2026-04-30"
FIVE_TICKER_MVP_TICKERS = ["VOO", "BND", "GLD", "QQQ", "VNQ"]
FIVE_TICKER_MVP_WEIGHTS = {
    "VOO": "35%",
    "BND": "25%",
    "GLD": "15%",
    "QQQ": "15%",
    "VNQ": "10%",
}


def snapshot_10y(
    metrics: dict[str, Any],
    *,
    rc_asset: list[dict[str, Any]] | None = None,
    final_weights_total: dict[str, float] | None = None,
    stress_overall: str = "PASS",
    candidate_config_fingerprint: str | None = None,
) -> dict[str, Any]:
    snap: dict[str, Any] = {
        "analysis_end": DEFAULT_ANALYSIS_END,
        "window_label": "10y",
        "metrics": metrics,
        "stress_suite_results": {
            "overall": stress_overall,
            "fail_reason_code": None,
            "failed_scenario": None,
            "scenarios": [
                {"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.05, "pass": True}
            ],
        },
        "constraints_status": {"target_vol": "PASS", "max_dd": "PASS"},
    }
    if rc_asset is not None:
        snap["RC_asset"] = rc_asset
    if final_weights_total is not None:
        snap["final_weights_total"] = final_weights_total
    if candidate_config_fingerprint is not None:
        snap["candidate_config_fingerprint"] = candidate_config_fingerprint
    return snap


def load_mvp_fixture_yaml(name: str) -> dict[str, Any]:
    """Load a Core MVP portfolio YAML fixture from ``tests/fixtures/mvp_portfolios/``."""
    path = MVP_FIXTURE_DIR / name
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if not isinstance(raw, dict):
        raise TypeError(f"fixture {name!r} must be a mapping")
    return raw


def validate_mvp_fixture(name: str) -> PortfolioConfig:
    """Validate a Core MVP fixture through ``validate_config`` (includes MVP defaults)."""
    return validate_config(load_mvp_fixture_yaml(name))


def eight_ticker_demo_mvp_config_dict(*, output_dir_final: str = "Main portfolio") -> dict[str, Any]:
    """Eight-ticker USD demo config (``minimal_usd_no_cash.yml``) for offline integration tests."""
    raw = load_mvp_fixture_yaml("minimal_usd_no_cash.yml")
    raw = dict(raw)
    raw["output_dir_final"] = output_dir_final
    return raw


def five_ticker_mvp_core_input_dict(*, output_dir_final: str = "Main portfolio") -> dict[str, Any]:
    """Five-ticker Core MVP input using ``current_weights`` only (no explicit ``analysis_subject``)."""
    return {
        "investor_currency": "USD",
        "output_dir_final": output_dir_final,
        "tickers": list(FIVE_TICKER_MVP_TICKERS),
        "current_weights": dict(FIVE_TICKER_MVP_WEIGHTS),
    }


def run_metadata(
    portfolio_role: str = "generated_policy_portfolio",
    *,
    analysis_setup: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if analysis_setup is not None:
        return build_offline_run_metadata(analysis_setup)
    return {
        "run_info": {"analysis_end_date": DEFAULT_ANALYSIS_END},
        "portfolio_valid": True,
        "analysis_setup": {
            "portfolio_input": {"source_analysis_mode": "optimize_from_universe"},
            "analysis_portfolio": {
                "portfolio_role": portfolio_role,
                "weight_source": "optimization_result_released",
                "recommendation_status": "generated_policy_output_released",
            },
        },
    }


def build_offline_run_metadata(analysis_setup: dict[str, Any]) -> dict[str, Any]:
    """``run_metadata.json`` payload with ``input_assumptions`` for portfolio-first sidecars."""
    return {
        "run_info": {"analysis_end_date": DEFAULT_ANALYSIS_END},
        "portfolio_valid": True,
        "analysis_setup": analysis_setup,
        "input_assumptions": build_input_assumptions_from_analysis_setup(analysis_setup),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def seed_variant_snapshot(
    root: Path,
    folder_name: str,
    metrics: dict[str, Any],
    *,
    with_run_metadata: bool = False,
    portfolio_role: str = "generated_policy_portfolio",
    final_weights_total: dict[str, float] | None = None,
) -> Path:
    folder = root / folder_name
    folder.mkdir(parents=True, exist_ok=True)
    weights = final_weights_total or {"VOO": 0.5, "BND": 0.5}
    write_json(
        folder / "snapshot_10y.json",
        snapshot_10y(
            metrics,
            rc_asset=_rc_rows(weights),
            final_weights_total=weights,
        ),
    )
    if with_run_metadata:
        write_json(folder / "run_metadata.json", run_metadata(portfolio_role))
    return folder


def seed_minimal_mvp_workspace(root: Path) -> Path:
    """Seed current-portfolio Main + EW/RP variant snapshots for offline comparison tests."""
    cfg = validate_config(minimal_mvp_config_dict())
    weights = {str(k): float(v) for k, v in (cfg.weights or {}).items()}
    main = seed_variant_snapshot(
        root,
        "Main portfolio",
        {"cagr": 0.09, "vol_annual": 0.11, "max_drawdown": -0.15, "sharpe": 0.6},
        final_weights_total=weights,
    )
    setup = build_analysis_setup(
        cfg,
        portfolio_weights=weights,
        weights_source=cfg.weights_source,
        portfolio_role_override="analysis_subject",
        cash_proxy_ticker="BIL",
        rf_source="FRED:DTB3",
        analysis_end=DEFAULT_ANALYSIS_END,
        windows_months=[36, 60, 120],
        returns_frequency="monthly",
        periods_per_year=12,
        run_context="report",
    )
    write_json(main / "run_metadata.json", build_offline_run_metadata(setup))
    seed_variant_snapshot(
        root,
        "equal-weight portfolio",
        {"cagr": 0.08, "vol_annual": 0.12, "max_drawdown": -0.2, "sharpe": 0.5},
        final_weights_total=weights,
    )
    seed_variant_snapshot(
        root,
        "risk parity portfolio",
        {"cagr": 0.075, "vol_annual": 0.105, "max_drawdown": -0.18, "sharpe": 0.55},
        final_weights_total=weights,
    )
    return main


def minimal_mvp_config_dict(*, output_dir_final: str = "Main portfolio") -> dict[str, Any]:
    """Two-ticker Core MVP config (``current_weights`` only) for fast offline comparison tests."""
    return {
        "investor_currency": "USD",
        "output_dir_final": output_dir_final,
        "tickers": ["VOO", "BND"],
        "current_weights": {"VOO": 0.5, "BND": 0.5},
    }


def write_minimal_config_yaml(root: Path, name: str = "config_mvp_offline.yml") -> Path:
    path = root / name
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(minimal_mvp_config_dict(), f, allow_unicode=True, sort_keys=False)
    return path


def load_mvp_config(root: Path) -> Any:
    return validate_config(minimal_mvp_config_dict())


def five_ticker_mvp_config_dict(*, output_dir_final: str = "Main portfolio") -> dict[str, Any]:
    return {
        "investor_currency": "USD",
        "analysis_mode": "optimize_from_universe",
        "output_dir_final": output_dir_final,
        "tickers": list(FIVE_TICKER_MVP_TICKERS),
        "analysis_subject": {
            "type": "current_portfolio",
            "display_name": "Five ticker current portfolio",
            "weights": dict(FIVE_TICKER_MVP_WEIGHTS),
        },
    }


def minimal_blocks_1_5_stress_report() -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema_version": "stress_report_v1",
        "status": "ok",
        "analysis_end": DEFAULT_ANALYSIS_END,
        "loss_gate_mode": "diagnostic",
        "stress_results_v1": empty_stress_results_v1(
            "offline_fixture",
            loss_gate_mode="diagnostic",
        ),
        "stress_scorecard_v1": {
            "overall_status": "PASS",
            "score": 82,
            "worst_scenario_id": "equity_shock",
        },
        "stress_conclusions": {
            "hedge_gap_status": "not_applicable",
            "overall_confidence": "medium",
            "version": "stress_conclusions_v1",
        },
        "historical_methodology": {
            "version": "historical_methodology_v1",
            "method": "offline_fixture",
            "episodes_evaluated": 1,
            "proxy_used_in_primary_stress": False,
        },
        "hedge_gap_analysis": {
            "status": "not_applicable",
            "status_reason": "no_hedge_labels",
            "by_risk_type": [],
        },
        "scenario_results": [
            {"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.05},
        ],
        "historical_results": [],
    }
    report["hedge_gap_analysis_v1"] = empty_hedge_gap_analysis_v1("offline_fixture")
    report["current_portfolio_stress_scorecard_v1"] = build_current_portfolio_stress_scorecard_v1(
        report
    )
    return report


def minimal_blocks_1_5_portfolio_xray() -> dict[str, Any]:
    """Offline stub when ``run_metadata`` / snapshot are not seeded for X-Ray rebuild."""
    return {
        "version": PORTFOLIO_XRAY_VERSION,
        "diagnostic_only": True,
        "block_2_1_asset_allocation": build_block_2_1_asset_allocation(
            analysis_setup=None,
            weights={},
            taxonomy_rows={},
            taxonomy_sources={},
        ),
        "block_2_2_portfolio_metrics": {
            "block": "2.2_portfolio_metrics",
            "status": "unavailable",
            "metadata": {},
        },
        "block_2_3_factor_exposure": {"block": "2.3_factor_exposure", "status": "unavailable"},
        "block_2_4_hidden_exposure": {"block": "2.4_hidden_exposure", "status": "unavailable"},
        "block_2_5_risk_budget_view": {"block": "2.5_risk_budget_view", "status": "unavailable"},
        "block_2_6_portfolio_weakness_map": {
            "block": "2.6_portfolio_weakness_map",
            "status": "unavailable",
        },
        "sections": {
            key: {"status": "available", "data_sources_used": ["offline_smoke_fixture"]}
            for key in XRAY_SECTION_KEYS
        },
    }


def refresh_analysis_subject_portfolio_xray(subject_dir: Path) -> dict[str, Any]:
    """Rebuild ``portfolio_xray.json`` the same way ``run_report`` does after snapshots."""
    from src.snapshot import _xray_summary_from_output_dir

    subject_dir.mkdir(parents=True, exist_ok=True)
    xray = _xray_summary_from_output_dir(subject_dir)
    if isinstance(xray, dict) and xray.get("version") == PORTFOLIO_XRAY_VERSION:
        return xray
    write_json(subject_dir / "portfolio_xray.json", minimal_blocks_1_5_portfolio_xray())
    return json.loads((subject_dir / "portfolio_xray.json").read_text(encoding="utf-8"))


def _rc_rows(weights: dict[str, float]) -> list[dict[str, Any]]:
    return [{"ticker": ticker, "rc_pct": weight} for ticker, weight in weights.items()]


def _decimal_five_ticker_weights() -> dict[str, float]:
    cfg = validate_config(five_ticker_mvp_config_dict())
    return {str(k): float(v) for k, v in (cfg.weights or {}).items()}


def _seed_candidate_snapshot(
    root: Path,
    folder_name: str,
    *,
    metrics: dict[str, Any],
    weights: dict[str, float],
    config_fingerprint: str,
) -> None:
    folder = root / folder_name
    folder.mkdir(parents=True, exist_ok=True)
    write_json(
        folder / "snapshot_10y.json",
        snapshot_10y(
            metrics,
            rc_asset=_rc_rows(weights),
            final_weights_total=weights,
            candidate_config_fingerprint=config_fingerprint,
        ),
    )


def seed_blocks_1_5_mvp_smoke_workspace(root: Path, cfg: Any) -> dict[str, Any]:
    """Seed an offline five-ticker Blocks 1-5 workspace with current factory evidence."""
    from src.candidate_factory import CORE_V1_CANDIDATE_ORDER, registry_row

    output_dir_final = str(getattr(cfg, "output_dir_final", "Main portfolio"))
    main = root / output_dir_final
    subject = main / "analysis_subject"
    weights = {str(k): float(v) for k, v in (cfg.weights or {}).items()}
    config_fingerprint = compute_candidate_config_fingerprint(cfg)
    setup = build_analysis_setup(
        cfg,
        portfolio_weights=weights,
        weights_source=cfg.weights_source,
        portfolio_role_override="analysis_subject",
        cash_proxy_ticker="BIL",
        rf_source="FRED:DTB3",
        analysis_end=DEFAULT_ANALYSIS_END,
        windows_months=[36, 60, 120],
        returns_frequency="monthly",
        periods_per_year=12,
        run_context="report",
    )

    write_json(subject / "run_metadata.json", build_offline_run_metadata(setup))
    write_json(
        subject / "snapshot_10y.json",
        snapshot_10y(
            {"cagr": 0.062, "vol_annual": 0.128, "max_drawdown": -0.22, "sharpe": 0.39},
            rc_asset=_rc_rows(weights),
            final_weights_total=weights,
            candidate_config_fingerprint=config_fingerprint,
        ),
    )
    write_json(subject / "stress_report.json", minimal_blocks_1_5_stress_report())
    refresh_analysis_subject_portfolio_xray(subject)

    candidate_weights = _decimal_five_ticker_weights()
    candidate_metrics = {
        "equal_weight": {"cagr": 0.071, "vol_annual": 0.116, "max_drawdown": -0.18, "sharpe": 0.48},
        "risk_parity": {"cagr": 0.069, "vol_annual": 0.101, "max_drawdown": -0.15, "sharpe": 0.55},
        "equal_weight_by_asset_class": {"cagr": 0.068, "vol_annual": 0.112, "max_drawdown": -0.17, "sharpe": 0.47},
        "risk_budget_by_asset": {"cagr": 0.073, "vol_annual": 0.109, "max_drawdown": -0.16, "sharpe": 0.57},
        "risk_budget_by_asset_class": {"cagr": 0.072, "vol_annual": 0.107, "max_drawdown": -0.155, "sharpe": 0.56},
        "hierarchical_risk_parity": {"cagr": 0.07, "vol_annual": 0.104, "max_drawdown": -0.152, "sharpe": 0.54},
    }
    steps: list[dict[str, Any]] = []
    for candidate_id in CORE_V1_CANDIDATE_ORDER:
        row = registry_row(candidate_id) or {}
        artifact_root = str(row.get("artifact_root") or candidate_id)
        _seed_candidate_snapshot(
            root,
            artifact_root,
            metrics=candidate_metrics[candidate_id],
            weights=candidate_weights,
            config_fingerprint=config_fingerprint,
        )
        steps.append(
            {
                "candidate_id": candidate_id,
                "display_name": row.get("display_name"),
                "role": row.get("role"),
                "artifact_root": artifact_root,
                "status": "succeeded",
                "entry_commands": [f"python {candidate_id}.py"],
                "exit_code": 0,
                "duration_seconds": 0.01,
                "reason_code": None,
                "message": None,
                "expected_analysis_end": DEFAULT_ANALYSIS_END,
                "snapshot_analysis_end": DEFAULT_ANALYSIS_END,
                "expected_config_fingerprint": config_fingerprint,
                "snapshot_config_fingerprint": config_fingerprint,
                "freshness_status": "fresh",
            }
        )

    write_json(
        main / "candidate_factory_run.json",
        {
            "schema_version": "candidate_factory_run_v1",
            "diagnostic_only": True,
            "generated_at": "2026-05-21T12:00:00+00:00",
            "factory_profile_id": "core_fast",
            "project_root": ".",
            "output_dir_final": output_dir_final,
            "config_path": "config.yml",
            "analysis_end": DEFAULT_ANALYSIS_END,
            "config_fingerprint": config_fingerprint,
            "options": {
                "skip_existing": True,
                "force": False,
                "fail_fast": False,
                "resume": False,
                "then_compare": True,
            },
            "steps": steps,
            "summary": {
                "total": len(steps),
                "succeeded": len(steps),
                "failed": 0,
                "skipped_existing": 0,
                "skipped_dependency": 0,
            },
            "warnings": [],
            "next_recommended_command": "python run_compare_variants.py",
        },
    )
    return {
        "main_dir": main,
        "analysis_subject_dir": subject,
        "analysis_setup": setup,
        "config_fingerprint": config_fingerprint,
        "core_candidate_ids": list(CORE_V1_CANDIDATE_ORDER),
    }


def seed_analysis_subject_diagnosis_bundle(subject_dir: Path) -> None:
    """Write Portfolio X-Ray, stress, Block 4 v3 diagnosis under analysis_subject/."""
    from src.block_4.diagnosis_builder import write_block_4_diagnosis_outputs

    subject_dir.mkdir(parents=True, exist_ok=True)
    if not (subject_dir / "stress_report.json").is_file():
        write_json(subject_dir / "stress_report.json", minimal_blocks_1_5_stress_report())
    stress = json.loads((subject_dir / "stress_report.json").read_text(encoding="utf-8"))
    xray = refresh_analysis_subject_portfolio_xray(subject_dir)
    write_block_4_diagnosis_outputs(
        output_dir=subject_dir,
        portfolio_xray=xray,
        stress_report=stress,
        analysis_end=DEFAULT_ANALYSIS_END,
    )


def seed_product_bundle_offline_workspace(root: Path, cfg: Any) -> dict[str, Any]:
    """Offline workspace: materialized analysis_subject + diagnosis bundle + one candidate."""
    from src.candidate_factory import registry_row

    output_dir_final = str(getattr(cfg, "output_dir_final", "Main portfolio"))
    main = root / output_dir_final
    subject = main / "analysis_subject"
    weights = {str(k): float(v) for k, v in (cfg.weights or {}).items()}
    config_fingerprint = compute_candidate_config_fingerprint(cfg)
    setup = build_analysis_setup(
        cfg,
        portfolio_weights=weights,
        weights_source=cfg.weights_source,
        portfolio_role_override="analysis_subject",
        cash_proxy_ticker="BIL",
        rf_source="FRED:DTB3",
        analysis_end=DEFAULT_ANALYSIS_END,
        windows_months=[36, 60, 120],
        returns_frequency="monthly",
        periods_per_year=12,
        run_context="report",
    )
    write_json(subject / "run_metadata.json", build_offline_run_metadata(setup))
    write_json(
        subject / "snapshot_10y.json",
        snapshot_10y(
            {"cagr": 0.058, "vol_annual": 0.13, "max_drawdown": -0.24, "sharpe": 0.34},
            rc_asset=_rc_rows(weights),
            final_weights_total=weights,
            candidate_config_fingerprint=config_fingerprint,
        ),
    )
    seed_analysis_subject_diagnosis_bundle(subject)

    candidate_id = "equal_weight"
    row = registry_row(candidate_id) or {}
    artifact_root = str(row.get("artifact_root") or "equal-weight portfolio")
    _seed_candidate_snapshot(
        root,
        artifact_root,
        metrics={"cagr": 0.075, "vol_annual": 0.105, "max_drawdown": -0.16, "sharpe": 0.55},
        weights=weights,
        config_fingerprint=config_fingerprint,
    )
    return {
        "main_dir": main,
        "analysis_subject_dir": subject,
        "analysis_setup": setup,
        "config_fingerprint": config_fingerprint,
        "candidate_id": candidate_id,
    }


# ---------------------------------------------------------------------------
# Block 2.2 offline seed helpers
# ---------------------------------------------------------------------------


def minimal_block_2_2_metrics(
    window_months: int = 120,
    *,
    cagr: float = 0.072,
    vol: float = 0.112,
    sharpe: float = 0.52,
    sortino: float = 0.58,
    mdd: float = -0.21,
    ttr_months: float = 6.0,
    recovered: bool = True,
    beta_portfolio: float = 0.80,
    downside_deviation: float = 0.078,
    corr_base: float = 0.75,
    downside_beta: float = 0.88,
    upside_beta: float = 0.71,
    skewness: float = -0.15,
    kurtosis: float = 1.05,
    benchmark_ticker: str = "SPY",
) -> dict[str, Any]:
    """Minimal realistic Block 2.2 window metrics dict for offline unit tests."""
    return {
        "window_months": window_months,
        "cagr": cagr,
        "vol_annual": vol,
        "sharpe": sharpe,
        "sortino": sortino,
        "treynor": round(sharpe * 0.12, 4),
        "beta_portfolio": beta_portfolio,
        "max_drawdown": mdd,
        "ttr_months": ttr_months,
        "recovered": recovered,
        "downside_deviation": downside_deviation,
        "corr_base": corr_base,
        "downside_beta": downside_beta,
        "upside_beta": upside_beta,
        "skewness": skewness,
        "kurtosis": kurtosis,
        "metric_quality": {
            "n_obs": window_months,
            "frequency": "monthly",
            "benchmark_ticker": benchmark_ticker,
            "risk_free_source": "FRED:DTB3",
            "window_months": window_months,
            "analysis_end": DEFAULT_ANALYSIS_END,
        },
    }


def minimal_block_2_2_analytics() -> dict[str, Any]:
    """Minimal portfolio analytics dict for Block 2.2 offline unit tests.

    Covers: tail_risk, rolling_sharpe_36m, rolling_vol_12m, rolling_beta_36m,
    advanced rolling summaries, eee_10pct, vol_of_vol, rel_vol_of_vol.
    """
    return {
        "tail_risk": {
            "method": "historical",
            "frequency": "daily",
            "window_label": "10y",
            "window_months": 120,
            "n_obs": 520,
            "metric_available": True,
            "var_95": -0.019,
            "var_99": -0.029,
            "es_95": -0.028,
            "es_99": -0.038,
        },
        "rolling_sharpe_36m": {"last": 0.50, "mean": 0.47, "p10": 0.28, "p90": 0.68},
        "rolling_vol_12m": {"last": 0.108, "mean": 0.11, "p10": 0.082, "p90": 0.136},
        "rolling_beta_36m": {"last": 0.78, "mean": 0.77, "p10": 0.58, "p90": 0.93},
        "rolling_correlation_36m": {"last": 0.74, "mean": 0.72, "p10": 0.55, "p90": 0.87},
        "rolling_sharpe_12m": {"last": 0.44, "mean": 0.42, "p10": 0.19, "p90": 0.62},
        "rolling_sortino_36m": {"last": 0.55, "mean": 0.52, "p10": 0.31, "p90": 0.74},
        "rolling_sortino_12m": {"last": 0.49, "mean": 0.47, "p10": 0.22, "p90": 0.66},
        "rolling_beta_12m": {"last": 0.81, "mean": 0.79, "p10": 0.60, "p90": 0.96},
        "rolling_correlation_12m": {"last": 0.76, "mean": 0.74, "p10": 0.57, "p90": 0.89},
        "eee_10pct": 38.0,
        "vol_of_vol": 0.038,
        "rel_vol_of_vol": 0.32,
    }


def minimal_block_2_2_drawdown_structure() -> dict[str, Any]:
    """Minimal drawdown_structure dict for Block 2.2 offline unit tests."""
    return {
        "drawdowns": [
            {"depth": -0.21, "length_months": 9, "recovery_months": 5},
            {"depth": -0.09, "length_months": 4, "recovery_months": 3},
            {"depth": -0.06, "length_months": 2, "recovery_months": 2},
        ],
        "summary": {
            "recovery_median_months": 3.0,
            "recovery_p90_months": 5.0,
            "pct_time_underwater": 0.14,
            "longest_underwater_months": 11,
        },
        "by_threshold": {
            ">5%": {"count": 3, "recovery_median": 3.0, "recovery_p90": 5.0},
            ">10%": {"count": 1, "recovery_median": 5.0, "recovery_p90": 5.0},
            ">20%": {"count": 1, "recovery_median": 5.0, "recovery_p90": 5.0},
        },
    }


def minimal_block_2_2_correlation_matrix(tickers: list[str] | None = None) -> dict[str, Any]:
    """Minimal 3×3 (or n×n) correlation matrix as a nested dict.

    The default three-ticker matrix is tuned for deterministic top-pair tests:
    highest pair = (BND, TLT) at 0.92; lowest pair = (GLD, SPY) at 0.05.
    """
    t = tickers or ["SPY", "BND", "GLD"]
    n = len(t)
    # Identity diagonal; off-diagonal rounded plausible values
    _off: dict[tuple[int, int], float] = {
        (0, 1): 0.55,
        (0, 2): 0.05,
        (1, 2): 0.92,
    }
    mat: list[list[float]] = []
    for i in range(n):
        row: list[float] = []
        for j in range(n):
            if i == j:
                row.append(1.0)
            else:
                lo, hi = (i, j) if i < j else (j, i)
                row.append(_off.get((lo, hi), 0.30))
        mat.append(row)
    return {"tickers": t, "matrix": mat}


def snapshot_10y_with_block_2_2(
    *,
    metrics: dict[str, Any] | None = None,
    analytics: dict[str, Any] | None = None,
    drawdown: dict[str, Any] | None = None,
    rc_asset: list[dict[str, Any]] | None = None,
    final_weights_total: dict[str, float] | None = None,
    stress_overall: str = "PASS",
) -> dict[str, Any]:
    """``snapshot_10y`` extended with Block 2.2 analytics/drawdown seeds.

    Drop-in replacement for ``snapshot_10y`` when Block 2.2 unit tests need
    ``analytics`` and ``drawdown_structure`` embedded in the snapshot payload.
    """
    m = metrics if metrics is not None else minimal_block_2_2_metrics()
    snap = snapshot_10y(
        m,
        rc_asset=rc_asset,
        final_weights_total=final_weights_total,
        stress_overall=stress_overall,
    )
    snap["analytics"] = analytics if analytics is not None else minimal_block_2_2_analytics()
    snap["drawdown_structure"] = drawdown if drawdown is not None else minimal_block_2_2_drawdown_structure()
    return snap


def seed_block_2_2_subject_dir(
    subject_dir: Path,
    *,
    tickers: list[str] | None = None,
    analysis_setup: dict[str, Any] | None = None,
    weights: dict[str, float] | None = None,
    metrics: dict[str, Any] | None = None,
    analytics: dict[str, Any] | None = None,
    drawdown: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Seed an offline ``analysis_subject/`` directory for Block 2.2 unit tests.

    Writes:
    - ``snapshot_10y.json`` (extended with analytics + drawdown_structure)
    - ``run_metadata.json`` (if *analysis_setup* is provided)
    - ``correlation_matrix_10y.csv`` (deterministic 3×4-ticker matrix)

    Returns the seed payloads for inspection in tests.
    """
    import pandas as pd

    subject_dir.mkdir(parents=True, exist_ok=True)
    t = tickers or ["SPY", "BND", "GLD"]
    w = weights or {tick: round(1.0 / len(t), 4) for tick in t}
    m = metrics if metrics is not None else minimal_block_2_2_metrics()
    a = analytics if analytics is not None else minimal_block_2_2_analytics()
    d = drawdown if drawdown is not None else minimal_block_2_2_drawdown_structure()

    snap = snapshot_10y_with_block_2_2(
        metrics=m,
        analytics=a,
        drawdown=d,
        rc_asset=_rc_rows(w),
        final_weights_total=w,
    )
    write_json(subject_dir / "snapshot_10y.json", snap)

    if analysis_setup is not None:
        write_json(subject_dir / "run_metadata.json", build_offline_run_metadata(analysis_setup))

    # Write deterministic correlation CSV for top-pair tests
    corr_info = minimal_block_2_2_correlation_matrix(t)
    corr_df = pd.DataFrame(
        corr_info["matrix"],
        index=corr_info["tickers"],
        columns=corr_info["tickers"],
    )
    # results_csv lives alongside subject_dir (sibling of analysis_subject/)
    results_csv_dir = subject_dir.parent / "results_csv"
    results_csv_dir.mkdir(parents=True, exist_ok=True)
    corr_df.to_csv(results_csv_dir / "correlation_matrix_10y.csv")

    return {"snapshot": snap, "analytics": a, "drawdown": d, "metrics": m, "correlation_tickers": t}


def seed_block_2_5_subject_dir(
    subject_dir: Path,
    *,
    tickers: list[str] | None = None,
    analysis_setup: dict[str, Any] | None = None,
    weights: dict[str, float] | None = None,
    metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Seed offline ``analysis_subject/`` inputs for Block 2.5 pipeline tests.

    Reuses Block 2.2 snapshot seeding (includes ``RC_asset`` rows aligned to weights).
    """
    return seed_block_2_2_subject_dir(
        subject_dir,
        tickers=tickers,
        analysis_setup=analysis_setup,
        weights=weights,
        metrics=metrics,
    )


def seed_cash5pct_block_2_2_subject_dir(
    subject_dir: Path,
) -> dict[str, Any]:
    """Seed a Block 2.2 offline workspace from the 5%-Cash-USD fixture.

    Uses ``demo_usd_asset_allocation_with_cash_5pct.yml`` tickers and weights;
    seeds ``snapshot_10y.json`` with Block 2.2 analytics/drawdown and
    ``run_metadata.json`` with full ``analysis_setup`` including ``cash_handling``.
    """
    raw = load_mvp_fixture_yaml("demo_usd_asset_allocation_with_cash_5pct.yml")
    cfg = validate_mvp_fixture("demo_usd_asset_allocation_with_cash_5pct.yml")
    weights = {str(k): float(v) for k, v in (cfg.weights or {}).items()}
    market_tickers = [t for t in weights if t != "Cash USD"]
    setup = build_analysis_setup(
        cfg,
        portfolio_weights=weights,
        weights_source=cfg.weights_source,
        portfolio_role_override="analysis_subject",
        cash_proxy_ticker="BIL",
        rf_source="FRED:DTB3",
        analysis_end=DEFAULT_ANALYSIS_END,
        windows_months=[36, 60, 120],
        returns_frequency="monthly",
        periods_per_year=12,
        run_context="report",
    )
    # Cash USD earns 0% — metrics are realistic for the 8-market-ticker basket
    m = minimal_block_2_2_metrics(cagr=0.068, vol=0.105, sharpe=0.49, mdd=-0.19)
    return seed_block_2_2_subject_dir(
        subject_dir,
        tickers=market_tickers,
        analysis_setup=setup,
        weights=weights,
        metrics=m,
    )


# (relative path under output_dir_final, expected schema_version)
PRODUCT_BUNDLE_ARTIFACTS: tuple[tuple[str, str], ...] = (
    ("analysis_subject/problem_classification.json", "problem_classification_v3"),
    ("analysis_subject/candidate_launchpad.json", "candidate_launchpad_v3"),
    ("current_vs_candidate.json", "current_vs_candidate_v1"),
    ("decision_verdict.json", "decision_verdict_v1"),
    ("ai_commentary_context.json", "ai_commentary_context_v1"),
    ("what_changed_summary.json", "what_changed_summary_v1"),
)


# (filename, expected schema_version)
MVP_DECISION_PACKAGE_ARTIFACTS: tuple[tuple[str, str], ...] = (
    ("candidate_comparison.json", "candidate_comparison_v1"),
    ("portfolio_health_score.json", "portfolio_health_score_v1"),
    ("robustness_scorecard.json", "robustness_scorecard_v1"),
    ("selection_decision.json", "selection_decision_v1"),
    ("current_vs_policy_status.json", "current_vs_policy_status_v1"),
    ("action_plan.json", "action_plan_v1"),
    ("monitoring_diff.json", "monitoring_diff_v1"),
    ("decision_journal.json", "decision_journal_v1"),
    ("decision_package_summary.json", "decision_package_report_v1"),
    ("tradeoff_explanation.json", "tradeoff_explanation_v1"),
    ("model_risk_diagnostics.json", "model_risk_diagnostics_v1"),
    ("assumption_sensitivity.json", "assumption_sensitivity_v1"),
    ("pareto_dominance.json", "pareto_dominance_v1"),
    ("regret_analysis.json", "regret_analysis_v1"),
)
