"""
Canonical candidate comparison builder (read-only aggregation).

See docs/specs/candidate_comparison_spec.md.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config_schema import PortfolioConfig
from src.io_export import REPORT_DECIMALS

SCHEMA_VERSION = "candidate_comparison_v1"
WINDOWS = ("3y", "5y", "10y")
PRIMARY_WINDOW = "10y"
SNAPSHOT_FILES = {"3y": "snapshot_3y.json", "5y": "snapshot_5y.json", "10y": "snapshot_10y.json"}

_REGISTRY_ROWS: list[dict[str, str]] = [
    {
        "candidate_id": "policy",
        "display_name": "Policy Portfolio",
        "role": "policy",
        "construction_method": "policy_optimizer",
        "weight_source": "optimization_result_released",
        "artifact_root": "{output_dir_final}",
    },
    {
        "candidate_id": "current",
        "display_name": "Current Portfolio",
        "role": "user_current",
        "construction_method": "user_supplied_weights",
        "weight_source": "config.current_weights",
        "artifact_root": "{output_dir_final}",
    },
    {
        "candidate_id": "equal_weight",
        "display_name": "Equal-Weight Portfolio",
        "role": "benchmark",
        "construction_method": "equal_weight_by_asset",
        "weight_source": "candidate_script.fixed_weights",
        "artifact_root": "equal-weight portfolio",
    },
    {
        "candidate_id": "equal_weight_by_asset_class",
        "display_name": "Equal-Weight by Asset-Class Portfolio",
        "role": "benchmark",
        "construction_method": "equal_weight_by_asset_class",
        "weight_source": "candidate_script.fixed_weights",
        "artifact_root": "equal-weight by asset-class portfolio",
    },
    {
        "candidate_id": "hierarchical_risk_parity",
        "display_name": "Hierarchical Risk Parity Portfolio",
        "role": "benchmark",
        "construction_method": "hierarchical_risk_parity",
        "weight_source": "candidate_script.fixed_weights",
        "artifact_root": "hierarchical risk parity portfolio",
    },
    {
        "candidate_id": "maximum_diversification",
        "display_name": "Maximum Diversification Portfolio",
        "role": "optimizer_candidate",
        "construction_method": "maximum_diversification_constrained",
        "weight_source": "candidate_script.fixed_weights",
        "artifact_root": "maximum diversification portfolio",
    },
    {
        "candidate_id": "maximum_diversification_uncapped",
        "display_name": "Maximum Diversification (Unconstrained) Portfolio",
        "role": "optimizer_candidate",
        "construction_method": "maximum_diversification_unconstrained",
        "weight_source": "candidate_script.fixed_weights",
        "artifact_root": "maximum diversification unconstrained portfolio",
    },
    {
        "candidate_id": "minimum_cvar_constrained",
        "display_name": "Minimum CVaR (Constrained) Portfolio",
        "role": "optimizer_candidate",
        "construction_method": "minimum_cvar_constrained",
        "weight_source": "candidate_script.fixed_weights",
        "artifact_root": "minimum cvar constrained portfolio",
    },
    {
        "candidate_id": "minimum_cvar_uncapped",
        "display_name": "Minimum CVaR (Uncapped) Portfolio",
        "role": "optimizer_candidate",
        "construction_method": "minimum_cvar_uncapped",
        "weight_source": "candidate_script.fixed_weights",
        "artifact_root": "minimum cvar uncapped portfolio",
    },
    {
        "candidate_id": "minimum_variance",
        "display_name": "Minimum Variance Portfolio",
        "role": "optimizer_candidate",
        "construction_method": "minimum_variance_constrained",
        "weight_source": "candidate_script.fixed_weights",
        "artifact_root": "minimum variance portfolio",
    },
    {
        "candidate_id": "minimum_variance_advanced",
        "display_name": "Minimum Variance (Advanced Controls) Portfolio",
        "role": "optimizer_candidate",
        "construction_method": "minimum_variance_advanced",
        "weight_source": "candidate_script.fixed_weights",
        "artifact_root": "minimum variance advanced portfolio",
    },
    {
        "candidate_id": "minimum_variance_uncapped",
        "display_name": "Minimum Variance (Uncapped) Portfolio",
        "role": "optimizer_candidate",
        "construction_method": "minimum_variance_uncapped",
        "weight_source": "candidate_script.fixed_weights",
        "artifact_root": "minimum variance uncapped portfolio",
    },
    {
        "candidate_id": "risk_budget_by_asset",
        "display_name": "Risk Budget by Asset Portfolio",
        "role": "benchmark",
        "construction_method": "risk_budget_by_asset",
        "weight_source": "candidate_script.fixed_weights",
        "artifact_root": "risk budget by asset portfolio",
    },
    {
        "candidate_id": "risk_budget_by_asset_class",
        "display_name": "Risk Budget by Asset-Class Portfolio",
        "role": "benchmark",
        "construction_method": "risk_budget_by_asset_class",
        "weight_source": "candidate_script.fixed_weights",
        "artifact_root": "risk budget by asset-class portfolio",
    },
    {
        "candidate_id": "risk_parity",
        "display_name": "Risk Parity Portfolio",
        "role": "benchmark",
        "construction_method": "risk_parity",
        "weight_source": "candidate_script.fixed_weights",
        "artifact_root": "risk parity portfolio",
    },
    {
        "candidate_id": "robust_mv_constrained",
        "display_name": "Robust Mean-Variance (Constrained) Portfolio",
        "role": "optimizer_candidate",
        "construction_method": "robust_mean_variance_constrained",
        "weight_source": "candidate_script.fixed_weights",
        "artifact_root": "robust mean variance constrained portfolio",
    },
    {
        "candidate_id": "robust_mv_uncapped",
        "display_name": "Robust Mean-Variance (Uncapped) Portfolio",
        "role": "optimizer_candidate",
        "construction_method": "robust_mean_variance_uncapped",
        "weight_source": "candidate_script.fixed_weights",
        "artifact_root": "robust mean variance uncapped portfolio",
    },
    {
        "candidate_id": "robust_scenario",
        "display_name": "Robust Scenario Portfolio",
        "role": "robust_candidate",
        "construction_method": "scenario_robust_optimization",
        "weight_source": "candidate_script.fixed_weights",
        "artifact_root": "robust scenario portfolio",
    },
]

LEGACY_VARIANT_IDS = ("policy", "equal_weight", "risk_parity", "robust_scenario")


def candidate_registry_ids() -> list[str]:
    return [row["candidate_id"] for row in _REGISTRY_ROWS]


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _round_export_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return round(value, REPORT_DECIMALS)
    if isinstance(value, int):
        return value
    if isinstance(value, dict):
        return {k: _round_export_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_round_export_value(v) for v in value]
    return value


def _rel_path(path: Path, project_root: Path) -> str:
    try:
        return str(path.relative_to(project_root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _metric_fields_from_snapshot(metrics: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "cagr",
        "vol_annual",
        "max_drawdown",
        "sharpe",
        "sortino",
        "beta_portfolio",
        "correlation_benchmark",
    )
    out: dict[str, Any] = {}
    for key in keys:
        if key in metrics and metrics[key] is not None:
            out[key] = metrics[key]
    return out


def _metric_fields_from_summary(metrics: dict[str, Any]) -> dict[str, Any]:
    return _metric_fields_from_snapshot(metrics)


def _load_window_metrics(
    folder: Path,
    window: str,
) -> tuple[dict[str, Any] | None, list[str], str | None]:
    """Return (metrics_dict, source_files, source_kind). source_kind: snapshot|summary|None."""
    snap_name = SNAPSHOT_FILES[window]
    snap = _load_json(folder / snap_name)
    if snap and isinstance(snap.get("metrics"), dict):
        return _metric_fields_from_snapshot(snap["metrics"]), [snap_name], "snapshot"

    summary = _load_json(folder / "summary.json")
    if summary:
        key = f"metrics_{window}"
        block = summary.get(key)
        if isinstance(block, dict):
            return _metric_fields_from_summary(block), ["summary.json"], "summary"
    return None, [], None


def _stress_from_artifacts(folder: Path, snap_10y: dict[str, Any] | None) -> dict[str, Any]:
    stress: dict[str, Any] = {}
    if snap_10y:
        suite = snap_10y.get("stress_suite_results") or {}
        if suite:
            stress["overall"] = suite.get("overall")
            stress["fail_reason_code"] = suite.get("fail_reason_code")
            stress["failed_scenario"] = suite.get("failed_scenario")
            scenarios = suite.get("scenarios")
            if isinstance(scenarios, list) and scenarios:
                stress["scenarios"] = [
                    {
                        "scenario_id": s.get("scenario_id"),
                        "portfolio_pnl_pct": s.get("portfolio_pnl_pct"),
                        "pass": s.get("pass"),
                    }
                    for s in scenarios[:8]
                    if isinstance(s, dict)
                ]

    summary = _load_json(folder / "summary.json")
    if stress.get("overall") is None and summary:
        stress["overall"] = summary.get("stress_status")

    stress_report = _load_json(folder / "stress_report.json")
    if stress_report:
        if stress.get("fail_reason_code") is None:
            stress["fail_reason_code"] = stress_report.get("fail_reason_code")
        if stress.get("failed_scenario") is None:
            stress["failed_scenario"] = stress_report.get("failed_scenario")

    return stress


def _drawdown_from_metrics(metrics_by_window: dict[str, dict[str, Any]]) -> dict[str, Any]:
    primary = metrics_by_window.get(PRIMARY_WINDOW) or {}
    dd: dict[str, Any] = {}
    if "max_drawdown" in primary:
        dd["max_drawdown"] = primary["max_drawdown"]
    for field in ("recovered", "time_to_recovery_months", "ttr_months"):
        if field in primary:
            dd[field if field != "ttr_months" else "time_to_recovery_months"] = primary[field]
    return dd


def _factor_regime_from_stress(folder: Path) -> dict[str, Any]:
    stress_report = _load_json(folder / "stress_report.json")
    if not stress_report:
        return {}
    block: dict[str, Any] = {}
    for key in ("factor_regression_5y", "factor_regression_10y"):
        if key in stress_report:
            block[key] = stress_report[key]
    macro = stress_report.get("macro_regime")
    if macro is not None:
        block["macro_regime"] = macro
    return block


def _diversification_from_snapshot(snap_10y: dict[str, Any] | None) -> dict[str, Any]:
    """RC concentration block for comparison v1.1 (Robustness Scorecard input)."""
    if not snap_10y:
        return {}
    rc_raw = snap_10y.get("RC_asset") or snap_10y.get("rc_asset")
    if not isinstance(rc_raw, list) or not rc_raw:
        return {}

    rows: list[tuple[str, float]] = []
    for item in rc_raw:
        if not isinstance(item, dict):
            continue
        ticker = item.get("ticker")
        pct = item.get("rc_pct")
        if ticker is None or pct is None:
            continue
        try:
            pct_f = float(pct)
        except (TypeError, ValueError):
            continue
        if math.isnan(pct_f) or math.isinf(pct_f):
            continue
        rows.append((str(ticker), pct_f))

    if not rows:
        return {}

    rows.sort(key=lambda x: (-x[1], x[0]))
    top1_ticker, top1_pct = rows[0]
    top3 = rows[:3]
    top3_sum = sum(p for _, p in top3)
    shares = [p for _, p in rows if p > 0]
    rc_hhi: float | None = None
    if len(shares) > 1:
        rc_hhi = round(sum(p * p for p in shares), REPORT_DECIMALS)

    return {
        "top1_rc_asset": top1_ticker,
        "top1_rc_pct": round(top1_pct, REPORT_DECIMALS),
        "top3_rc_assets": [t for t, _ in top3],
        "top3_rc_sum_pct": round(top3_sum, REPORT_DECIMALS),
        "rc_hhi": rc_hhi,
        "source_window": PRIMARY_WINDOW,
    }


def _mandate_from_artifacts(
    folder: Path,
    snap_10y: dict[str, Any] | None,
    run_meta: dict[str, Any] | None,
) -> dict[str, Any]:
    mandate: dict[str, Any] = {}
    if run_meta and "portfolio_valid" in run_meta:
        mandate["portfolio_valid"] = bool(run_meta["portfolio_valid"])
        mandate["client_fit"] = bool(run_meta["portfolio_valid"])

    summary = _load_json(folder / "summary.json")
    if summary:
        if "portfolio_valid" in summary and "portfolio_valid" not in mandate:
            mandate["portfolio_valid"] = bool(summary["portfolio_valid"])
            mandate["client_fit"] = bool(summary["portfolio_valid"])

    if snap_10y:
        constraints = snap_10y.get("constraints_status")
        if isinstance(constraints, dict):
            mandate["constraints_status"] = constraints
    return mandate


def _analysis_setup_summary_from_main(main_dir: Path, cfg: PortfolioConfig) -> dict[str, Any]:
    meta = _load_json(main_dir / "run_metadata.json")
    if meta:
        setup = meta.get("analysis_setup") or meta.get("input_assumptions")
        if isinstance(setup, dict):
            ap = setup.get("analysis_portfolio") or {}
            pi = setup.get("portfolio_input") or {}
            return {
                "source_analysis_mode": pi.get("source_analysis_mode")
                or getattr(cfg, "analysis_mode", None),
                "product_input_case": pi.get("product_input_case"),
                "portfolio_role": ap.get("portfolio_role"),
                "weight_source": ap.get("weight_source"),
                "recommendation_status": ap.get("recommendation_status"),
            }
    return {
        "source_analysis_mode": getattr(cfg, "analysis_mode", "optimize_from_universe"),
        "portfolio_role": None,
        "weight_source": getattr(cfg, "weights_source", None),
    }


def _main_portfolio_role(main_dir: Path) -> str | None:
    meta = _load_json(main_dir / "run_metadata.json")
    if meta:
        setup = meta.get("analysis_setup") or {}
        ap = setup.get("analysis_portfolio") or {}
        role = ap.get("portfolio_role")
        if role:
            return str(role)
    result = _load_json(main_dir / "run_result.json")
    if result:
        setup = result.get("analysis_setup") or {}
        ap = setup.get("analysis_portfolio") or {}
        role = ap.get("portfolio_role")
        if role:
            return str(role)
    return None


def _resolve_analysis_end(main_dir: Path, cfg: PortfolioConfig) -> str:
    for name in ("snapshot_10y.json", "snapshot_5y.json", "snapshot_3y.json"):
        snap = _load_json(main_dir / name)
        if snap and snap.get("analysis_end"):
            return str(snap["analysis_end"])
    meta = _load_json(main_dir / "run_metadata.json")
    if meta:
        run_info = meta.get("run_info") or {}
        if run_info.get("analysis_end_date"):
            return str(run_info["analysis_end_date"])
    return str(getattr(cfg, "analysis_end", "") or "")


def _artifact_folder(
    row: dict[str, str],
    *,
    output_dir_final: Path,
    project_root: Path,
) -> Path:
    root_tpl = row["artifact_root"]
    if root_tpl == "{output_dir_final}":
        return output_dir_final
    return project_root / root_tpl


def _evaluate_artifact_candidate(
    folder: Path,
    *,
    candidate_id: str,
) -> tuple[str, str | None, dict[str, Any], list[str], list[str]]:
    """
    Returns (status, unavailable_reason, payload_blocks, missing_fields, warnings).
    payload_blocks keys: metrics, stress, drawdown, factor_regime, mandate, source_files.
    """
    missing_fields: list[str] = []
    warnings: list[str] = []
    source_files: list[str] = []

    if not folder.is_dir():
        return "unavailable", "missing_artifact_folder", {}, source_files, warnings

    metrics_by_window: dict[str, dict[str, Any]] = {}
    has_primary_metrics = False
    used_summary_only = False

    for window in WINDOWS:
        m, files, kind = _load_window_metrics(folder, window)
        if m:
            metrics_by_window[window] = m
            source_files.extend(files)
            if window == PRIMARY_WINDOW:
                has_primary_metrics = True
                if kind == "summary":
                    used_summary_only = True

    if not has_primary_metrics:
        return "unavailable", "missing_snapshot", {}, source_files, warnings

    snap_10y = _load_json(folder / SNAPSHOT_FILES[PRIMARY_WINDOW])
    if snap_10y:
        source_files.append(SNAPSHOT_FILES[PRIMARY_WINDOW])
    run_meta = _load_json(folder / "run_metadata.json")
    if run_meta:
        source_files.append("run_metadata.json")
    if (folder / "stress_report.json").is_file():
        source_files.append("stress_report.json")
    if (folder / "summary.json").is_file() and "summary.json" not in source_files:
        source_files.append("summary.json")

    stress = _stress_from_artifacts(folder, snap_10y)
    if not stress.get("overall"):
        missing_fields.append("stress.overall")
        warnings.append("stress_summary_missing")

    diversification = _diversification_from_snapshot(snap_10y)
    if not diversification:
        missing_fields.append("diversification")

    status = "available"
    if used_summary_only or missing_fields:
        status = "degraded"

    payload = {
        "metrics": metrics_by_window,
        "stress": stress,
        "drawdown": _drawdown_from_metrics(metrics_by_window),
        "factor_regime": _factor_regime_from_stress(folder),
        "mandate": _mandate_from_artifacts(folder, snap_10y, run_meta),
        "diversification": diversification,
        "source_files": sorted(set(source_files)),
    }
    return status, None, payload, missing_fields, warnings


def _apply_policy_current_gating(
    candidate_id: str,
    status: str,
    unavailable_reason: str | None,
    *,
    analysis_mode: str,
    main_role: str | None,
    folder: Path,
    cfg: PortfolioConfig,
) -> tuple[str, str | None, list[str]]:
    warnings: list[str] = []
    if candidate_id not in ("policy", "current"):
        return status, unavailable_reason, warnings

    if analysis_mode == "optimize_from_universe":
        if candidate_id == "current":
            if main_role == "user_current_portfolio" and status in ("available", "degraded"):
                return status, None, warnings
            if positive_current_weights(cfg):
                return "unavailable", "missing_current_report", warnings
            if status in ("available", "degraded"):
                return "unavailable", "not_applicable_for_analysis_mode", warnings
            return "unavailable", unavailable_reason or "not_applicable_for_analysis_mode", warnings

        if candidate_id == "policy":
            return status, unavailable_reason, warnings

    if analysis_mode == "analyze_current_weights":
        if candidate_id == "current":
            return status, unavailable_reason, warnings
        if candidate_id == "policy":
            if status == "unavailable":
                return "unavailable", "not_applicable_for_analysis_mode", warnings
            if status in ("available", "degraded") and _load_json(folder / SNAPSHOT_FILES[PRIMARY_WINDOW]):
                warnings.append("stale_policy_snapshot")
                return "degraded", None, warnings
            return "unavailable", "not_applicable_for_analysis_mode", warnings

    return status, unavailable_reason, warnings


def positive_current_weights(cfg: PortfolioConfig) -> bool:
    current = getattr(cfg, "current_weights", None) or {}
    return bool(current) and sum(float(v) for v in current.values() if v) > 0


def _build_candidate_row(
    row: dict[str, str],
    *,
    cfg: PortfolioConfig,
    output_dir_final: Path,
    project_root: Path,
    analysis_mode: str,
    main_role: str | None,
    main_meta: dict[str, Any] | None,
) -> dict[str, Any]:
    artifact_root_tpl = row["artifact_root"].replace("{output_dir_final}", str(output_dir_final))
    folder = _artifact_folder(row, output_dir_final=output_dir_final, project_root=project_root)

    status, unavailable_reason, payload, missing_fields, warnings = _evaluate_artifact_candidate(
        folder, candidate_id=row["candidate_id"]
    )
    status, unavailable_reason, gate_warnings = _apply_policy_current_gating(
        row["candidate_id"],
        status,
        unavailable_reason,
        analysis_mode=analysis_mode,
        main_role=main_role,
        folder=folder,
        cfg=cfg,
    )
    warnings = list(warnings) + gate_warnings

    portfolio_role = None
    recommendation_status = None
    if row["candidate_id"] in ("policy", "current") and folder == output_dir_final.resolve():
        if main_meta:
            ap = (main_meta.get("analysis_setup") or {}).get("analysis_portfolio") or {}
            portfolio_role = ap.get("portfolio_role")
            recommendation_status = ap.get("recommendation_status")
        elif main_role:
            portfolio_role = main_role

    candidate: dict[str, Any] = {
        "candidate_id": row["candidate_id"],
        "display_name": row["display_name"],
        "role": row["role"],
        "construction_method": row["construction_method"],
        "weight_source": row["weight_source"],
        "artifact_root": artifact_root_tpl.replace("\\", "/"),
        "status": status,
        "unavailable_reason": unavailable_reason,
        "portfolio_role": portfolio_role,
        "recommendation_status": recommendation_status,
        "metrics": payload.get("metrics", {}) if status != "unavailable" else {},
        "stress": payload.get("stress", {}) if status != "unavailable" else {},
        "drawdown": payload.get("drawdown", {}) if status != "unavailable" else {},
        "factor_regime": payload.get("factor_regime", {}) if status != "unavailable" else {},
        "mandate": payload.get("mandate", {}) if status != "unavailable" else {},
        "diversification": payload.get("diversification", {}) if status != "unavailable" else {},
        "missing_fields": missing_fields if status == "degraded" else [],
        "warnings": warnings,
        "source_files": payload.get("source_files", []) if status != "unavailable" else [],
    }
    return _round_export_value(candidate)


def build_candidate_comparison(
    cfg: PortfolioConfig,
    *,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Assemble the canonical comparison document (does not write files)."""
    project_root = project_root or Path.cwd()
    output_dir_final = project_root / str(getattr(cfg, "output_dir_final", "Main portfolio"))
    main_dir = output_dir_final.resolve()
    analysis_mode = str(getattr(cfg, "analysis_mode", "optimize_from_universe"))
    main_meta = _load_json(main_dir / "run_metadata.json")
    main_role = _main_portfolio_role(main_dir)

    run_warnings: list[str] = []
    legacy: dict[str, str | None] = {
        "portfolio_comparison_json": None,
        "ew_rp_comparison_json": None,
    }
    pc = output_dir_final / "portfolio_comparison.json"
    ew = output_dir_final / "ew_rp_comparison.json"
    if pc.is_file():
        legacy["portfolio_comparison_json"] = "portfolio_comparison.json"
    if ew.is_file():
        legacy["ew_rp_comparison_json"] = "ew_rp_comparison.json"

    candidates = [
        _build_candidate_row(
            row,
            cfg=cfg,
            output_dir_final=output_dir_final,
            project_root=project_root,
            analysis_mode=analysis_mode,
            main_role=main_role,
            main_meta=main_meta,
        )
        for row in _REGISTRY_ROWS
    ]

    doc: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "diagnostic_only": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analysis_end": _resolve_analysis_end(main_dir, cfg),
        "investor_currency": str(getattr(cfg, "investor_currency", "USD")),
        "output_dir_final": str(getattr(cfg, "output_dir_final", "Main portfolio")).replace("\\", "/"),
        "analysis_setup_summary": _analysis_setup_summary_from_main(main_dir, cfg),
        "windows": list(WINDOWS),
        "primary_window": PRIMARY_WINDOW,
        "candidates": candidates,
        "legacy_artifacts": legacy,
        "warnings": run_warnings,
    }
    return _round_export_value(doc)


def build_legacy_portfolio_comparison(
    comparison: dict[str, Any],
) -> dict[str, Any]:
    """Subset compatible with legacy portfolio_comparison.json consumers."""
    legacy: dict[str, Any] = {}
    by_id = {c["candidate_id"]: c for c in comparison.get("candidates", [])}
    label_map = {
        "policy": "Policy Portfolio",
        "equal_weight": "Equal-Weight Portfolio",
        "risk_parity": "Risk Parity Portfolio",
        "robust_scenario": "Robust Scenario Portfolio",
    }
    for cid in LEGACY_VARIANT_IDS:
        cand = by_id.get(cid) or {}
        metrics = (cand.get("metrics") or {}).get(PRIMARY_WINDOW) or {}
        stress = cand.get("stress") or {}
        mandate = cand.get("mandate") or {}
        legacy[cid] = {
            "label": label_map.get(cid, cand.get("display_name", cid)),
            "metrics": metrics,
            "stress_status": stress.get("overall"),
            "client_fit": mandate.get("client_fit"),
        }
    return _round_export_value(legacy)


def write_candidate_comparison_txt(
    comparison: dict[str, Any],
    path: Path,
) -> None:
    """Optional human-readable summary table (English)."""
    lines = [
        "Candidate comparison (diagnostic only)",
        "=" * 72,
        "",
        "Columns: CAGR | Vol | MaxDD | Sharpe | Stress | Client-fit",
        "",
    ]

    def _fmt(v: Any, pct: bool = False) -> str:
        if v is None:
            return "—"
        try:
            if pct:
                return f"{float(v):.1%}"
            return f"{float(v):.3f}"
        except (TypeError, ValueError):
            return str(v)

    for cand in comparison.get("candidates", []):
        if cand.get("status") == "unavailable":
            lines.append(
                f"{cand.get('display_name', ''):<36} UNAVAILABLE ({cand.get('unavailable_reason', '')})"
            )
            continue
        m = (cand.get("metrics") or {}).get(PRIMARY_WINDOW) or {}
        mandate = cand.get("mandate") or {}
        client_fit = mandate.get("client_fit")
        fit_s = (
            "PASS"
            if client_fit is True
            else "FAIL"
            if client_fit is False
            else "—"
        )
        stress = (cand.get("stress") or {}).get("overall") or "N/A"
        line = (
            f"{cand.get('display_name', ''):<36} "
            f"{_fmt(m.get('cagr'), pct=True):>8}  "
            f"{_fmt(m.get('vol_annual'), pct=True):>8}  "
            f"{_fmt(m.get('max_drawdown'), pct=True):>8}  "
            f"{_fmt(m.get('sharpe')):>7}  "
            f"{str(stress):>12}  "
            f"{fit_s:>6}"
        )
        lines.append(line)

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def write_candidate_comparison_outputs(
    cfg: PortfolioConfig,
    *,
    project_root: Path | None = None,
    write_legacy: bool = True,
    write_txt: bool = True,
) -> dict[str, Path]:
    """Build and write canonical (and optional legacy) comparison artifacts."""
    project_root = project_root or Path.cwd()
    comparison = build_candidate_comparison(cfg, project_root=project_root)
    out_dir = project_root / str(getattr(cfg, "output_dir_final", "Main portfolio"))
    out_dir.mkdir(parents=True, exist_ok=True)

    paths: dict[str, Path] = {}
    json_path = out_dir / "candidate_comparison.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)
    paths["candidate_comparison_json"] = json_path

    if write_txt:
        txt_path = out_dir / "candidate_comparison.txt"
        write_candidate_comparison_txt(comparison, txt_path)
        paths["candidate_comparison_txt"] = txt_path

    if write_legacy:
        legacy = build_legacy_portfolio_comparison(comparison)
        legacy_json = out_dir / "portfolio_comparison.json"
        with open(legacy_json, "w", encoding="utf-8") as f:
            json.dump(legacy, f, indent=2, ensure_ascii=False)
        paths["portfolio_comparison_json"] = legacy_json

        lines = [
            "Policy vs Equal-Weight vs Risk-Parity vs Robust Scenario",
            "=" * 70,
            "",
            "Columns:   CAGR | Vol | MaxDD | Sharpe | Sortino | Beta | Stress | Client-fit",
            "",
        ]

        def _fmt(v: Any, pct: bool = False) -> str:
            if v is None:
                return "—"
            try:
                if pct:
                    return f"{float(v):.1%}"
                return f"{float(v):.3f}"
            except (TypeError, ValueError):
                return str(v)

        for cid in LEGACY_VARIANT_IDS:
            item = legacy.get(cid, {})
            m = item.get("metrics") or {}
            line = (
                f"{item.get('label', cid):<22} "
                f"{_fmt(m.get('cagr'), pct=True):>8}  "
                f"{_fmt(m.get('vol_annual'), pct=True):>8}  "
                f"{_fmt(m.get('max_drawdown'), pct=True):>8}  "
                f"{_fmt(m.get('sharpe')):>7}  "
                f"{_fmt(m.get('sortino')):>7}  "
                f"{_fmt(m.get('beta_portfolio')):>7}  "
                f"{(item.get('stress_status') or 'N/A'):>8}  "
                f"{('PASS' if item.get('client_fit') else 'FAIL') if item.get('client_fit') is not None else '—':>6}"
            )
            lines.append(line)

        legacy_txt = out_dir / "portfolio_comparison.txt"
        with open(legacy_txt, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        paths["portfolio_comparison_txt"] = legacy_txt

    from src.robustness_scorecard import write_robustness_scorecard_outputs

    paths.update(
        write_robustness_scorecard_outputs(
            cfg, project_root=project_root, comparison=comparison
        )
    )

    return paths


__all__ = [
    "SCHEMA_VERSION",
    "build_candidate_comparison",
    "build_legacy_portfolio_comparison",
    "candidate_registry_ids",
    "write_candidate_comparison_outputs",
    "write_candidate_comparison_txt",
]
