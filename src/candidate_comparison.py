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

from src.candidate_robust_disclosure import (
    build_robust_paths_disclosure,
    is_robust_suite_candidate,
)
from src.config_schema import PortfolioConfig
from src.io_export import REPORT_DECIMALS
from src.optimization_readiness import build_optimization_readiness
from src.optimization_status import (
    optimizer_quality_from_solver_block,
    optimization_quality_family,
)
from src.optimizer_methodology import (
    covariance_methodology_summary,
    young_etf_methodology_summary,
)
from src.snapshot import compute_candidate_config_fingerprint, snapshot_config_fingerprint
from src.stress import crisis_replay_summary_from_paths

SCHEMA_VERSION = "candidate_comparison_v1"
WINDOWS = ("3y", "5y", "10y")
PRIMARY_WINDOW = "10y"
SNAPSHOT_FILES = {"3y": "snapshot_3y.json", "5y": "snapshot_5y.json", "10y": "snapshot_10y.json"}
CURRENT_SIDECAR_SUBDIR = "current_portfolio"
ANALYSIS_SUBJECT_SIDECAR_SUBDIR = "analysis_subject"
PORTFOLIO_FIRST_POLICY_LEGACY_REASON = "legacy_policy_not_default_portfolio_first_candidate"
PORTFOLIO_FIRST_POLICY_LEGACY_WARNING = "legacy_policy_reference_optional_portfolio_first"
MENU_BASELINE_IDS = frozenset({"analysis_subject", "policy", "current"})
PRODUCT_MENU_PROFILE_ID = "default_v1"
BASELINE_WEIGHTS_METADATA_FILE = "baseline_weights_metadata.json"
_SUMMARY_BUILDER_EXCERPT_KEYS = (
    "status",
    "reason",
    "solver_status",
    "max_rc_error",
    "portfolio_type",
)
_POLICY_RUN_RESULT_EXCERPT_KEYS = (
    "status",
    "optimization_status",
    "young_etf_dual_cov_enabled",
)
_FACTORY_STEP_EXCERPT_KEYS = (
    "status",
    "reason_code",
    "message",
    "builder_status",
    "builder_reason",
    "exit_code",
    "optimization_status_source",
    "optimization_quality_status",
    "optimization_quality_family",
    "optimizer_fallback_used",
    "optimizer_fallback_reason",
    "optimizer_solver_status",
    "freshness_status",
    "snapshot_analysis_end",
    "expected_analysis_end",
    "expected_config_fingerprint",
    "snapshot_config_fingerprint",
    "robust_paths_disclosure",
)

_REGISTRY_ROWS: list[dict[str, str]] = [
    {
        "candidate_id": "analysis_subject",
        "display_name": "Analysis Subject",
        "role": "analysis_subject",
        "construction_method": "analysis_subject_diagnostics",
        "weight_source": "analysis_subject.resolved_weights",
        "artifact_root": "{output_dir_final}/analysis_subject",
    },
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
        "es_95",
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
            scorecard = suite.get("scorecard")
            if isinstance(scorecard, dict) and scorecard:
                stress["scorecard"] = scorecard
            conclusions = suite.get("conclusions")
            if isinstance(conclusions, dict) and conclusions:
                stress["conclusions"] = conclusions
            hm = suite.get("historical_methodology")
            if isinstance(hm, dict) and hm:
                stress["historical_methodology"] = hm
            crs = suite.get("crisis_replay_summary")
            if isinstance(crs, list) and crs:
                stress["crisis_replay_summary"] = crs
            hg_suite = suite.get("hedge_gap_analysis")
            if isinstance(hg_suite, dict) and hg_suite:
                stress["hedge_gap_analysis"] = hg_suite

    summary = _load_json(folder / "summary.json")
    if stress.get("overall") is None and summary:
        stress["overall"] = summary.get("stress_status")

    stress_report = _load_json(folder / "stress_report.json")
    if stress_report:
        if stress.get("fail_reason_code") is None:
            stress["fail_reason_code"] = stress_report.get("fail_reason_code")
        if stress.get("failed_scenario") is None:
            stress["failed_scenario"] = stress_report.get("failed_scenario")
        if stress.get("analysis_end") is None:
            stress["analysis_end"] = stress_report.get("analysis_end")
        if stress.get("generated_at") is None:
            stress["generated_at"] = stress_report.get("generated_at")
        if "scorecard" not in stress and isinstance(stress_report.get("stress_scorecard_v1"), dict):
            stress["scorecard"] = stress_report.get("stress_scorecard_v1")
        if "conclusions" not in stress and isinstance(stress_report.get("stress_conclusions"), dict):
            stress["conclusions"] = stress_report.get("stress_conclusions")
        if isinstance(stress_report.get("hedge_gap_analysis"), dict):
            stress["hedge_gap_analysis"] = stress_report.get("hedge_gap_analysis")
        if "historical_methodology" not in stress:
            hm = stress_report.get("historical_methodology")
            if isinstance(hm, dict) and hm:
                stress["historical_methodology"] = hm
        if "crisis_replay_summary" not in stress:
            paths = stress_report.get("historical_episode_paths")
            if isinstance(paths, list) and paths:
                stress["crisis_replay_summary"] = crisis_replay_summary_from_paths(paths)
        stress["source_file"] = "stress_report.json"
    elif snap_10y:
        stress["source_file"] = SNAPSHOT_FILES[PRIMARY_WINDOW]

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


def _weight_concentration_from_snapshot(snap_10y: dict[str, Any] | None) -> dict[str, Any]:
    """Weight concentration block for comparison v1.2 (Portfolio Health Score input)."""
    if not snap_10y:
        return {}
    weights_raw = snap_10y.get("final_weights_total")
    if not isinstance(weights_raw, dict) or not weights_raw:
        return {}

    rows: list[tuple[str, float]] = []
    for ticker, pct in weights_raw.items():
        if ticker is None or pct is None:
            continue
        try:
            pct_f = float(pct)
        except (TypeError, ValueError):
            continue
        if math.isnan(pct_f) or math.isinf(pct_f) or pct_f <= 0:
            continue
        rows.append((str(ticker), pct_f))

    if not rows:
        return {}

    rows.sort(key=lambda x: (-x[1], x[0]))
    top1_ticker, top1_pct = rows[0]
    top3 = rows[:3]
    top3_sum = sum(p for _, p in top3)
    shares = [p for _, p in rows if p > 0]
    weight_hhi: float | None = None
    if len(shares) > 1:
        weight_hhi = round(sum(p * p for p in shares), REPORT_DECIMALS)

    return {
        "top1_weight_asset": top1_ticker,
        "top1_weight_pct": round(top1_pct, REPORT_DECIMALS),
        "top3_weight_assets": [t for t, _ in top3],
        "top3_weight_sum_pct": round(top3_sum, REPORT_DECIMALS),
        "weight_hhi": weight_hhi,
        "source": "snapshot_10y.final_weights_total",
    }


def _factory_step_excerpt(step: dict[str, Any] | None) -> dict[str, Any]:
    if not step:
        return {}
    return {k: step[k] for k in _FACTORY_STEP_EXCERPT_KEYS if k in step and step[k] is not None}


def _builder_summary_excerpt(summary: dict[str, Any]) -> dict[str, Any]:
    excerpt: dict[str, Any] = {}
    for key in _SUMMARY_BUILDER_EXCERPT_KEYS:
        if key in summary and summary[key] is not None:
            excerpt[key] = summary[key]
    for key, value in summary.items():
        if key.endswith("_metadata") and isinstance(value, dict) and value:
            excerpt[key] = value
    return excerpt


def _policy_construction_excerpt(folder: Path) -> tuple[dict[str, Any], list[str]]:
    source_files: list[str] = []
    excerpt: dict[str, Any] = {}
    run_result = _load_json(folder / "run_result.json")
    if run_result:
        source_files.append("run_result.json")
        for key in _POLICY_RUN_RESULT_EXCERPT_KEYS:
            if key in run_result and run_result[key] is not None:
                excerpt[key] = run_result[key]
        mandate = run_result.get("mandate_check")
        if isinstance(mandate, dict) and mandate:
            excerpt["mandate_check"] = {
                k: mandate[k]
                for k in ("passed", "fail_reason_code", "failed_scenario")
                if k in mandate
            }
    return excerpt, source_files


def _subject_construction_excerpt(folder: Path) -> tuple[dict[str, Any], list[str]]:
    source_files: list[str] = []
    excerpt: dict[str, Any] = {}
    run_meta = _load_json(folder / "run_metadata.json")
    if not run_meta:
        return excerpt, source_files
    source_files.append("run_metadata.json")
    setup = run_meta.get("analysis_setup") or {}
    if isinstance(setup, dict):
        subject = setup.get("analysis_subject")
        if isinstance(subject, dict) and subject:
            excerpt["analysis_subject"] = {
                k: subject[k]
                for k in (
                    "id",
                    "type",
                    "display_name",
                    "weight_source",
                    "resolution_source",
                )
                if k in subject
            }
        ap = setup.get("analysis_portfolio")
        if isinstance(ap, dict) and ap:
            excerpt["analysis_portfolio"] = {
                k: ap[k]
                for k in ("portfolio_role", "weight_source", "recommendation_status")
                if k in ap
            }
    return excerpt, source_files


def _construction_disclosure_status(
    *,
    baseline_metadata: dict[str, Any],
    builder_summary: dict[str, Any],
    main_row_excerpt: dict[str, Any],
    factory_step: dict[str, Any],
) -> str:
    if baseline_metadata:
        return "available"
    if builder_summary or main_row_excerpt:
        return "partial"
    if factory_step:
        return "partial"
    return "missing"


def _optimizer_methodology_from_metadata(
    optimizer_metadata: dict[str, Any],
    *,
    source: str,
    factory_step: dict[str, Any],
) -> dict[str, Any]:
    if not optimizer_metadata:
        return {}

    solver = optimizer_metadata.get("solver")
    if not isinstance(solver, dict):
        solver = {}
    input_window = optimizer_metadata.get("input_window")
    if not isinstance(input_window, dict):
        input_window = {}
    constraints = optimizer_metadata.get("constraints")
    if not isinstance(constraints, dict):
        constraints = {}

    freshness_keys = (
        "freshness_status",
        "snapshot_analysis_end",
        "expected_analysis_end",
        "expected_config_fingerprint",
        "snapshot_config_fingerprint",
    )
    freshness = {
        key: factory_step[key]
        for key in freshness_keys
        if key in factory_step and factory_step[key] is not None
    }
    if input_window.get("analysis_end") is not None:
        freshness["optimizer_analysis_end"] = input_window.get("analysis_end")

    methodology: dict[str, Any] = {
        "source": source,
        "source_schema_version": optimizer_metadata.get("schema_version"),
        "optimizer_role": optimizer_metadata.get("optimizer_role"),
        "candidate_only": bool(
            optimizer_metadata.get(
                "candidate_only",
                optimizer_metadata.get("optimizer_role") == "candidate_only",
            )
        ),
        "method_id": optimizer_metadata.get("method_id"),
        "objective": optimizer_metadata.get("objective"),
        "input_window": input_window,
        "expected_return": optimizer_metadata.get("expected_return")
        or optimizer_metadata.get("expected_returns"),
        "covariance": optimizer_metadata.get("covariance"),
        "young_etf_methodology": optimizer_metadata.get("young_etf_methodology"),
        "constraints": constraints,
        "solver": {
            "name": solver.get("name"),
            "success": solver.get("success")
            if "success" in solver
            else solver.get("solver_success"),
            "status": solver.get("status") or solver.get("solver_status"),
            "fallback_used": bool(solver.get("fallback_used", False)),
            "fallback_reason": solver.get("fallback_reason"),
            "optimization_quality_status": solver.get("optimization_quality_status"),
        },
    }
    if freshness:
        methodology["freshness"] = freshness
    return methodology


def _optimization_readiness_txt_line(cand: dict[str, Any]) -> str | None:
    disclosure = cand.get("construction_disclosure")
    if not isinstance(disclosure, dict):
        return None
    readiness = disclosure.get("optimization_readiness")
    if not isinstance(readiness, dict):
        return None
    gaps = readiness.get("gaps") or []
    gap_s = ", ".join(gaps) if gaps else "none"
    return (
        f"- {cand.get('display_name', cand.get('candidate_id', 'candidate'))}: "
        f"readiness={readiness.get('overall_status', 'unknown')}; "
        f"fair_comparison_ready={readiness.get('fair_comparison_ready')}; "
        f"gaps={gap_s}."
    )


def _optimizer_methodology_txt_line(cand: dict[str, Any]) -> str | None:
    disclosure = cand.get("construction_disclosure")
    if not isinstance(disclosure, dict):
        return None
    methodology = disclosure.get("optimizer_methodology")
    if not isinstance(methodology, dict):
        return None
    covariance = methodology.get("covariance")
    if isinstance(covariance, dict):
        covariance_methodology = (
            covariance.get("methodology")
            if isinstance(covariance.get("methodology"), dict)
            else covariance
        )
    else:
        covariance_methodology = {}
    young = methodology.get("young_etf_methodology")
    if not isinstance(young, dict) and isinstance(covariance_methodology, dict):
        young = covariance_methodology.get("young_etf")
    solver = methodology.get("solver") if isinstance(methodology.get("solver"), dict) else {}
    return (
        f"- {cand.get('display_name', cand.get('candidate_id', 'candidate'))}: "
        f"{covariance_methodology_summary(covariance_methodology)} "
        f"{young_etf_methodology_summary(young if isinstance(young, dict) else None)} "
        f"optimizer_quality={solver.get('optimization_quality_status') or 'unknown'}."
    )


def _optimizer_quality_from_disclosure(disclosure: dict[str, Any]) -> dict[str, Any]:
    """Project normalized optimizer quality from comparison construction disclosure."""
    factory_step = disclosure.get("factory_step")
    if isinstance(factory_step, dict) and factory_step.get("optimization_quality_status"):
        quality = str(factory_step["optimization_quality_status"])
        fallback_used = bool(factory_step.get("optimizer_fallback_used", False))
        return {
            "source": factory_step.get("optimization_status_source")
            or "candidate_factory_run.json.steps[]",
            "optimization_quality_status": quality,
            "optimization_quality_family": factory_step.get("optimization_quality_family")
            or optimization_quality_family(quality, fallback_used=fallback_used),
            "fallback_used": fallback_used,
            "fallback_reason": factory_step.get("optimizer_fallback_reason"),
            "solver_status": factory_step.get("optimizer_solver_status"),
        }

    methodology = disclosure.get("optimizer_methodology")
    if isinstance(methodology, dict):
        solver = methodology.get("solver")
        if isinstance(solver, dict):
            quality = optimizer_quality_from_solver_block(solver)
            fallback_used = bool(solver.get("fallback_used", False))
            return {
                "source": methodology.get("source"),
                "optimization_quality_status": quality,
                "optimization_quality_family": optimization_quality_family(
                    quality,
                    fallback_used=fallback_used,
                ),
                "fallback_used": fallback_used,
                "fallback_reason": solver.get("fallback_reason"),
                "solver_status": solver.get("status"),
            }
    return {}


def _apply_factory_and_optimizer_quality_policy(
    *,
    status: str,
    unavailable_reason: str | None,
    warnings: list[str],
    factory_step: dict[str, Any] | None,
    construction_disclosure: dict[str, Any],
) -> tuple[str, str | None, list[str]]:
    """Apply Session 06 comparison boundary without recomputing optimizer outputs."""
    out_status = status
    out_reason = unavailable_reason
    out_warnings = list(warnings)

    factory_status = str((factory_step or {}).get("status") or "")
    if factory_status in {"failed", "skipped_dependency"}:
        reason_code = (factory_step or {}).get("reason_code") or factory_status
        out_warnings.append(f"factory_step_not_successful:{reason_code}")
        return "unavailable", str(reason_code), out_warnings

    quality = _optimizer_quality_from_disclosure(construction_disclosure)
    if quality:
        construction_disclosure["optimizer_quality"] = quality
        family = quality.get("optimization_quality_family")
        q_status = quality.get("optimization_quality_status") or "unknown"
        if family == "failed":
            out_warnings.append(f"optimizer_quality_failed:{q_status}")
            return "unavailable", "optimizer_quality_failed", out_warnings
        if family == "approximate":
            out_warnings.append(f"optimizer_quality_not_clean:{q_status}")
            if out_status == "available":
                out_status = "degraded"
    return out_status, out_reason, out_warnings


def construction_disclosure_from_folder(
    folder: Path,
    *,
    candidate_id: str,
    factory_step: dict[str, Any] | None = None,
    project_root: Path | None = None,
    output_dir_final: str | None = None,
) -> dict[str, Any]:
    """
    Passthrough construction parameters from existing artifact metadata (no recomputation).

    See docs/specs/candidate_comparison_spec.md (construction_disclosure).
    """
    source_files: list[str] = []
    baseline_metadata: dict[str, Any] = {}
    builder_summary: dict[str, Any] = {}
    main_row_excerpt: dict[str, Any] = {}
    optimizer_metadata: dict[str, Any] = {}
    optimizer_metadata_source: str | None = None

    if folder.is_dir():
        meta = _load_json(folder / BASELINE_WEIGHTS_METADATA_FILE)
        if meta:
            baseline_metadata = dict(meta)
            source_files.append(BASELINE_WEIGHTS_METADATA_FILE)
            raw_optimizer_metadata = baseline_metadata.get("optimizer_run_metadata")
            if isinstance(raw_optimizer_metadata, dict):
                optimizer_metadata = raw_optimizer_metadata
                optimizer_metadata_source = (
                    f"{BASELINE_WEIGHTS_METADATA_FILE}.optimizer_run_metadata"
                )

        summary = _load_json(folder / "summary.json")
        if summary:
            builder_summary = _builder_summary_excerpt(summary)
            if builder_summary:
                source_files.append("summary.json")

        if candidate_id == "policy":
            main_row_excerpt, policy_sources = _policy_construction_excerpt(folder)
            source_files.extend(s for s in policy_sources if s not in source_files)
            run_result = _load_json(folder / "run_result.json")
            if run_result and isinstance(run_result.get("optimizer_run_metadata"), dict):
                optimizer_metadata = run_result["optimizer_run_metadata"]
                optimizer_metadata_source = "run_result.json.optimizer_run_metadata"
        elif candidate_id in ("analysis_subject", "current"):
            main_row_excerpt, subject_sources = _subject_construction_excerpt(folder)
            source_files.extend(s for s in subject_sources if s not in source_files)

    factory_excerpt = _factory_step_excerpt(factory_step)
    if factory_excerpt:
        source_files.append("candidate_factory_run.json")

    disclosure: dict[str, Any] = {
        "disclosure_status": _construction_disclosure_status(
            baseline_metadata=baseline_metadata,
            builder_summary=builder_summary,
            main_row_excerpt=main_row_excerpt,
            factory_step=factory_excerpt,
        ),
        "source_files": sorted(set(source_files)),
    }
    if baseline_metadata:
        disclosure["baseline_metadata"] = baseline_metadata
    if builder_summary:
        disclosure["builder_summary"] = builder_summary
    if main_row_excerpt:
        disclosure["main_row_excerpt"] = main_row_excerpt
    if factory_excerpt:
        disclosure["factory_step"] = factory_excerpt
    if optimizer_metadata and optimizer_metadata_source:
        disclosure["optimizer_methodology"] = _optimizer_methodology_from_metadata(
            optimizer_metadata,
            source=optimizer_metadata_source,
            factory_step=factory_excerpt,
        )

    robust_paths = factory_excerpt.get("robust_paths_disclosure")
    if robust_paths is None and is_robust_suite_candidate(candidate_id):
        if project_root is not None and output_dir_final:
            robust_paths = build_robust_paths_disclosure(
                candidate_id=candidate_id,
                project_root=project_root,
                output_dir_final=output_dir_final,
                baseline_metadata=baseline_metadata or None,
            )
    if robust_paths:
        disclosure["robust_paths"] = robust_paths

    return _round_export_value(disclosure)


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
    for meta_path in (
        analysis_subject_sidecar_dir(main_dir) / "run_metadata.json",
        main_dir / "run_metadata.json",
        main_dir / "run_result.json",
    ):
        meta = _load_json(meta_path)
        if not meta:
            continue
        setup = meta.get("analysis_setup") or meta.get("input_assumptions")
        if isinstance(setup, dict):
            ap = setup.get("analysis_portfolio") or {}
            pi = setup.get("portfolio_input") or {}
            subject = setup.get("analysis_subject") or {}
            return {
                "source_analysis_mode": pi.get("source_analysis_mode")
                or getattr(cfg, "analysis_mode", None),
                "product_input_case": pi.get("product_input_case"),
                "portfolio_role": ap.get("portfolio_role"),
                "weight_source": ap.get("weight_source"),
                "recommendation_status": ap.get("recommendation_status"),
                "analysis_subject_id": subject.get("id"),
                "analysis_subject_type": subject.get("type"),
                "analysis_subject_display_name": subject.get("display_name"),
                "analysis_subject_weight_source": subject.get("weight_source"),
                "analysis_subject_resolution_source": subject.get("resolution_source"),
            }
    cfg_subject = getattr(cfg, "analysis_subject", {}) or {}
    return {
        "source_analysis_mode": getattr(cfg, "analysis_mode", "optimize_from_universe"),
        "portfolio_role": None,
        "weight_source": getattr(cfg, "weights_source", None),
        "analysis_subject_id": cfg_subject.get("id"),
        "analysis_subject_type": cfg_subject.get("type"),
        "analysis_subject_display_name": cfg_subject.get("display_name"),
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
    subject_dir = analysis_subject_sidecar_dir(main_dir)
    for name in ("snapshot_10y.json", "snapshot_5y.json", "snapshot_3y.json"):
        snap = _load_json(subject_dir / name)
        if snap and snap.get("analysis_end"):
            return str(snap["analysis_end"])
    subject_meta = _load_json(subject_dir / "run_metadata.json")
    if subject_meta:
        run_info = subject_meta.get("run_info") or {}
        if run_info.get("analysis_end_date"):
            return str(run_info["analysis_end_date"])
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


def current_sidecar_dir(output_dir_final: Path) -> Path:
    return output_dir_final / CURRENT_SIDECAR_SUBDIR


def analysis_subject_sidecar_dir(output_dir_final: Path) -> Path:
    return output_dir_final / ANALYSIS_SUBJECT_SIDECAR_SUBDIR


def sidecar_meets_minimum(
    sidecar: Path,
    *,
    expected_portfolio_role: str | None = "user_current_portfolio",
    require_analysis_subject: bool = False,
) -> bool:
    if not (sidecar / SNAPSHOT_FILES[PRIMARY_WINDOW]).is_file():
        return False
    meta = _load_json(sidecar / "run_metadata.json")
    if not meta:
        return False
    setup = meta.get("analysis_setup") or {}
    ap = setup.get("analysis_portfolio") or {}
    if expected_portfolio_role is not None and ap.get("portfolio_role") != expected_portfolio_role:
        return False
    if require_analysis_subject and not isinstance(setup.get("analysis_subject"), dict):
        return False
    return True


def analysis_subject_meets_minimum(output_dir_final: Path) -> bool:
    return sidecar_meets_minimum(
        analysis_subject_sidecar_dir(output_dir_final),
        expected_portfolio_role=None,
        require_analysis_subject=True,
    )


def resolve_current_artifact_folder(
    *,
    output_dir_final: Path,
    output_dir_final_rel: str,
    analysis_mode: str,
) -> tuple[Path, str]:
    """Folder path and artifact_root string for the current candidate row."""
    if analysis_mode == "optimize_from_universe":
        sidecar = current_sidecar_dir(output_dir_final)
        if sidecar_meets_minimum(sidecar):
            return sidecar, f"{output_dir_final_rel}/{CURRENT_SIDECAR_SUBDIR}"
    return output_dir_final, output_dir_final_rel


def _artifact_folder(
    row: dict[str, str],
    *,
    output_dir_final: Path,
    project_root: Path,
    analysis_mode: str = "optimize_from_universe",
    output_dir_final_rel: str | None = None,
) -> Path:
    if row.get("candidate_id") == "analysis_subject":
        return analysis_subject_sidecar_dir(output_dir_final)
    if row.get("candidate_id") == "current":
        rel = output_dir_final_rel or str(
            getattr(output_dir_final, "name", output_dir_final)
        )
        folder, _ = resolve_current_artifact_folder(
            output_dir_final=output_dir_final,
            output_dir_final_rel=rel.replace("\\", "/"),
            analysis_mode=analysis_mode,
        )
        return folder
    root_tpl = row["artifact_root"]
    if root_tpl == "{output_dir_final}":
        return output_dir_final
    return project_root / root_tpl


def _evaluate_artifact_candidate(
    folder: Path,
    *,
    candidate_id: str,
    expected_analysis_end: str | None = None,
    expected_config_fingerprint: str | None = None,
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

    snap_10y = _load_json(folder / SNAPSHOT_FILES[PRIMARY_WINDOW])
    if snap_10y and not expected_analysis_end:
        warnings.append(
            f"candidate_freshness_unchecked_no_review_analysis_end:{candidate_id}"
        )
    if snap_10y and expected_analysis_end:
        snapshot_end = snap_10y.get("analysis_end")
        if str(snapshot_end) != str(expected_analysis_end):
            warnings.append(
                "stale_snapshot_analysis_end:"
                f"{snapshot_end or 'missing'}!={expected_analysis_end}"
            )
            return "unavailable", "stale_snapshot_analysis_end", {}, source_files, warnings
        snapshot_fp = snapshot_config_fingerprint(snap_10y)
        if expected_config_fingerprint:
            if snapshot_fp is None:
                warnings.append(f"candidate_config_fingerprint_missing:{candidate_id}")
            elif snapshot_fp != expected_config_fingerprint:
                warnings.append(
                    "stale_config_fingerprint:"
                    f"{snapshot_fp}!={expected_config_fingerprint}"
                )
                return "unavailable", "stale_config_fingerprint", {}, source_files, warnings

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

    weight_concentration = _weight_concentration_from_snapshot(snap_10y)
    if not weight_concentration:
        missing_fields.append("weight_concentration")

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
        "weight_concentration": weight_concentration,
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
    output_dir_final: Path,
    cfg: PortfolioConfig,
) -> tuple[str, str | None, list[str]]:
    warnings: list[str] = []
    if candidate_id not in ("policy", "current"):
        return status, unavailable_reason, warnings

    if candidate_id == "policy" and analysis_subject_meets_minimum(output_dir_final):
        warnings.append(PORTFOLIO_FIRST_POLICY_LEGACY_WARNING)
        return "unavailable", PORTFOLIO_FIRST_POLICY_LEGACY_REASON, warnings

    if analysis_mode == "optimize_from_universe":
        if candidate_id == "current":
            sidecar = current_sidecar_dir(output_dir_final)
            if folder.resolve() == sidecar.resolve() and status in ("available", "degraded"):
                return status, None, warnings
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


def _factory_steps_by_candidate_id(factory_run: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    if not factory_run:
        return by_id
    for step in factory_run.get("steps") or []:
        if not isinstance(step, dict):
            continue
        cid = step.get("candidate_id")
        if cid:
            by_id[str(cid)] = step
    return by_id


def _build_candidate_row(
    row: dict[str, str],
    *,
    cfg: PortfolioConfig,
    output_dir_final: Path,
    project_root: Path,
    analysis_mode: str,
    main_role: str | None,
    main_meta: dict[str, Any] | None,
    expected_analysis_end: str | None,
    factory_steps_by_id: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    out_rel = str(getattr(cfg, "output_dir_final", "Main portfolio")).replace("\\", "/")
    if row["candidate_id"] == "current":
        folder, artifact_root_str = resolve_current_artifact_folder(
            output_dir_final=output_dir_final,
            output_dir_final_rel=out_rel,
            analysis_mode=analysis_mode,
        )
        artifact_root_tpl = artifact_root_str
    elif row["candidate_id"] == "analysis_subject":
        folder = analysis_subject_sidecar_dir(output_dir_final)
        artifact_root_tpl = f"{out_rel}/{ANALYSIS_SUBJECT_SIDECAR_SUBDIR}"
    else:
        artifact_root_tpl = row["artifact_root"].replace("{output_dir_final}", out_rel)
        folder = _artifact_folder(
            row,
            output_dir_final=output_dir_final,
            project_root=project_root,
            analysis_mode=analysis_mode,
            output_dir_final_rel=out_rel,
        )

    status, unavailable_reason, payload, missing_fields, warnings = _evaluate_artifact_candidate(
        folder,
        candidate_id=row["candidate_id"],
        expected_analysis_end=expected_analysis_end,
        expected_config_fingerprint=compute_candidate_config_fingerprint(cfg),
    )
    status, unavailable_reason, gate_warnings = _apply_policy_current_gating(
        row["candidate_id"],
        status,
        unavailable_reason,
        analysis_mode=analysis_mode,
        main_role=main_role,
        folder=folder,
        output_dir_final=output_dir_final,
        cfg=cfg,
    )
    warnings = list(warnings) + gate_warnings

    portfolio_role = None
    recommendation_status = None
    display_name = row["display_name"]
    weight_source = row["weight_source"]
    if row["candidate_id"] in ("analysis_subject", "policy", "current"):
        row_meta = _load_json(folder / "run_metadata.json")
        if row_meta:
            setup = row_meta.get("analysis_setup") or {}
            ap = setup.get("analysis_portfolio") or {}
            subject = setup.get("analysis_subject") or {}
            portfolio_role = ap.get("portfolio_role")
            recommendation_status = ap.get("recommendation_status")
            if row["candidate_id"] == "analysis_subject":
                display_name = subject.get("display_name") or display_name
                weight_source = subject.get("weight_source") or ap.get("weight_source") or weight_source
        elif folder == output_dir_final.resolve() and main_meta:
            ap = (main_meta.get("analysis_setup") or {}).get("analysis_portfolio") or {}
            portfolio_role = ap.get("portfolio_role")
            recommendation_status = ap.get("recommendation_status")
        elif folder == output_dir_final.resolve() and main_role:
            portfolio_role = main_role

    factory_step = (factory_steps_by_id or {}).get(row["candidate_id"])
    construction_disclosure = construction_disclosure_from_folder(
        folder,
        candidate_id=row["candidate_id"],
        factory_step=factory_step,
        project_root=project_root,
        output_dir_final=out_rel,
    )
    status, unavailable_reason, warnings = _apply_factory_and_optimizer_quality_policy(
        status=status,
        unavailable_reason=unavailable_reason,
        warnings=warnings,
        factory_step=factory_step,
        construction_disclosure=construction_disclosure,
    )

    readiness = build_optimization_readiness(
        folder,
        role=row["role"],
        construction_disclosure=construction_disclosure,
        comparison_status=status,
        unavailable_reason=unavailable_reason,
        warnings=warnings,
        expected_analysis_end=expected_analysis_end,
        primary_snapshot_name=SNAPSHOT_FILES[PRIMARY_WINDOW],
    )
    if readiness:
        construction_disclosure["optimization_readiness"] = _round_export_value(readiness)

    candidate: dict[str, Any] = {
        "candidate_id": row["candidate_id"],
        "display_name": display_name,
        "role": row["role"],
        "construction_method": row["construction_method"],
        "weight_source": weight_source,
        "artifact_root": artifact_root_tpl.replace("\\", "/"),
        "status": status,
        "unavailable_reason": unavailable_reason,
        "portfolio_role": portfolio_role,
        "recommendation_status": recommendation_status,
        "construction_disclosure": construction_disclosure,
        "metrics": payload.get("metrics", {}) if status != "unavailable" else {},
        "stress": payload.get("stress", {}) if status != "unavailable" else {},
        "drawdown": payload.get("drawdown", {}) if status != "unavailable" else {},
        "factor_regime": payload.get("factor_regime", {}) if status != "unavailable" else {},
        "mandate": payload.get("mandate", {}) if status != "unavailable" else {},
        "diversification": payload.get("diversification", {}) if status != "unavailable" else {},
        "weight_concentration": payload.get("weight_concentration", {}) if status != "unavailable" else {},
        "missing_fields": missing_fields if status == "degraded" else [],
        "warnings": warnings,
        "source_files": payload.get("source_files", []) if status != "unavailable" else [],
    }
    return _round_export_value(candidate)


def _factory_menu_candidate_ids(profile_id: str) -> list[str]:
    from src.candidate_factory import resolve_profile_candidate_ids

    return resolve_profile_candidate_ids(profile_id=profile_id, explicit_candidates=None)


def _load_factory_run(main_dir: Path) -> dict[str, Any] | None:
    return _load_json(main_dir / "candidate_factory_run.json")


def build_candidate_menu(
    candidates: list[dict[str, Any]],
    *,
    factory_run: dict[str, Any] | None = None,
    review_mode: str | None = None,
) -> dict[str, Any]:
    """
    Summarize intended vs product candidate menus for comparison and decision outputs.

    See docs/specs/candidate_comparison_spec.md (candidate_menu block).
    """
    by_id = {c["candidate_id"]: c for c in candidates if c.get("candidate_id")}
    run_profile = (factory_run or {}).get("factory_profile_id") or review_mode
    if run_profile in ("core", "full"):
        from src.candidate_factory import REVIEW_MODE_PROFILES

        run_profile = REVIEW_MODE_PROFILES.get(str(run_profile), str(run_profile))
    if run_profile in (None, "", "explicit_list"):
        run_profile = PRODUCT_MENU_PROFILE_ID

    intended_ids = _factory_menu_candidate_ids(str(run_profile))
    product_ids = _factory_menu_candidate_ids(PRODUCT_MENU_PROFILE_ID)

    def _status_counts(ids: list[str]) -> dict[str, int]:
        counts: dict[str, int] = {
            "available": 0,
            "degraded": 0,
            "unavailable": 0,
            "missing_from_registry": 0,
        }
        for cid in ids:
            row = by_id.get(cid)
            if not row:
                counts["missing_from_registry"] += 1
                continue
            status = str(row.get("status") or "unavailable")
            if status in counts:
                counts[status] += 1
            else:
                counts["unavailable"] += 1
        return counts

    intended_counts = _status_counts(intended_ids)
    product_counts = _status_counts(product_ids)
    intended_scored = intended_counts["available"] + intended_counts["degraded"]
    product_scored = product_counts["available"] + product_counts["degraded"]

    unavailable_summary: dict[str, int] = {}
    for cid in intended_ids:
        row = by_id.get(cid) or {}
        if row.get("status") != "unavailable":
            continue
        reason = str(row.get("unavailable_reason") or "unknown")
        unavailable_summary[reason] = unavailable_summary.get(reason, 0) + 1

    is_reduced_vs_product = str(run_profile) != PRODUCT_MENU_PROFILE_ID
    is_incomplete_intended_menu = intended_scored < len(intended_ids)
    is_partial_menu = is_reduced_vs_product or is_incomplete_intended_menu

    if is_reduced_vs_product and is_incomplete_intended_menu:
        partial_reason = "reduced_menu_scope_and_unavailable_intended_candidates"
    elif is_reduced_vs_product:
        partial_reason = "reduced_menu_scope_vs_product_default_v1"
    elif is_incomplete_intended_menu:
        partial_reason = "unavailable_intended_candidates"
    else:
        partial_reason = None

    resolved_review_mode = review_mode
    if not resolved_review_mode:
        from src.candidate_factory import REVIEW_MODE_PROFILES

        for mode, profile in REVIEW_MODE_PROFILES.items():
            if profile == run_profile:
                resolved_review_mode = mode
                break

    refresh_core = "python run_portfolio_review.py --mode core"
    refresh_full = "python run_portfolio_review.py --mode full --no-skip-existing"
    menu: dict[str, Any] = {
        "product_menu_profile_id": PRODUCT_MENU_PROFILE_ID,
        "product_menu_size": len(product_ids),
        "intended_menu_profile_id": str(run_profile),
        "intended_menu_size": len(intended_ids),
        "review_mode": resolved_review_mode,
        "intended_menu_status_counts": intended_counts,
        "product_menu_status_counts": product_counts,
        "intended_menu_scored_count": intended_scored,
        "product_menu_scored_count": product_scored,
        "is_reduced_vs_product_menu": is_reduced_vs_product,
        "is_incomplete_intended_menu": is_incomplete_intended_menu,
        "is_partial_menu": is_partial_menu,
        "partial_menu_reason": partial_reason,
        "unavailable_reasons_summary": unavailable_summary,
        "refresh_command_core": refresh_core,
        "refresh_command_full": refresh_full,
    }
    if factory_run and factory_run.get("generated_at"):
        menu["factory_run_generated_at"] = factory_run["generated_at"]
    return _round_export_value(menu)


def build_candidate_menu_warnings(menu: dict[str, Any]) -> list[str]:
    """Run-level warnings derived from candidate_menu disclosure."""
    warnings: list[str] = []
    if not menu.get("is_partial_menu"):
        return warnings
    intended = menu.get("intended_menu_profile_id")
    product = menu.get("product_menu_profile_id")
    scored = menu.get("intended_menu_scored_count")
    size = menu.get("intended_menu_size")
    if menu.get("is_reduced_vs_product_menu"):
        warnings.append(
            f"Candidate comparison used reduced menu '{intended}' "
            f"(product menu '{product}' has {menu.get('product_menu_size')} script-backed candidates). "
            f"Selection and health ranks apply only to this menu unless a full refresh is run."
        )
    if menu.get("is_incomplete_intended_menu"):
        warnings.append(
            f"Intended menu '{intended}' is incomplete: {scored}/{size} candidates scored "
            f"(available or degraded). See unavailable_reasons_summary in candidate_menu."
        )
    return warnings


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

    analysis_end = _resolve_analysis_end(main_dir, cfg)
    factory_run = _load_factory_run(main_dir)
    factory_steps_by_id = _factory_steps_by_candidate_id(factory_run)
    candidates = [
        _build_candidate_row(
            row,
            cfg=cfg,
            output_dir_final=output_dir_final,
            project_root=project_root,
            analysis_mode=analysis_mode,
            main_role=main_role,
            main_meta=main_meta,
            expected_analysis_end=analysis_end or None,
            factory_steps_by_id=factory_steps_by_id,
        )
        for row in _REGISTRY_ROWS
    ]
    review_mode: str | None = None
    if factory_run:
        profile = str(factory_run.get("factory_profile_id") or "")
        from src.candidate_factory import REVIEW_MODE_PROFILES

        for mode, mapped in REVIEW_MODE_PROFILES.items():
            if mapped == profile:
                review_mode = mode
                break

    candidate_menu = build_candidate_menu(
        candidates,
        factory_run=factory_run,
        review_mode=review_mode,
    )
    menu_warnings = build_candidate_menu_warnings(candidate_menu)

    out_rel = str(getattr(cfg, "output_dir_final", "Main portfolio")).replace("\\", "/")
    setup_summary = _analysis_setup_summary_from_main(main_dir, cfg)
    sidecar = current_sidecar_dir(output_dir_final)
    if sidecar_meets_minimum(sidecar):
        setup_summary = dict(setup_summary)
        setup_summary["current_materialization_root"] = f"{out_rel}/{CURRENT_SIDECAR_SUBDIR}"

    doc: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "diagnostic_only": True,
        "comparison_baseline_candidate_id": "analysis_subject",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analysis_end": analysis_end,
        "config_fingerprint": (
            str(factory_run.get("config_fingerprint"))
            if factory_run and factory_run.get("config_fingerprint")
            else compute_candidate_config_fingerprint(cfg)
        ),
        "investor_currency": str(getattr(cfg, "investor_currency", "USD")),
        "output_dir_final": out_rel,
        "analysis_setup_summary": setup_summary,
        "windows": list(WINDOWS),
        "primary_window": PRIMARY_WINDOW,
        "candidates": candidates,
        "candidate_menu": candidate_menu,
        "legacy_artifacts": legacy,
        "warnings": run_warnings + menu_warnings,
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
    menu = comparison.get("candidate_menu") or {}
    lines = [
        "Candidate comparison (diagnostic only)",
        "=" * 72,
        "",
    ]
    if menu:
        intended = menu.get("intended_menu_profile_id", "—")
        product = menu.get("product_menu_profile_id", "—")
        scored = menu.get("intended_menu_scored_count")
        size = menu.get("intended_menu_size")
        lines.append(
            f"Menu: intended={intended} ({scored}/{size} scored); product reference={product} "
            f"({menu.get('product_menu_scored_count')}/{menu.get('product_menu_size')} scored)."
        )
        if menu.get("is_partial_menu"):
            lines.append(
                f"Partial menu: {menu.get('partial_menu_reason')}. "
                f"Full refresh: {menu.get('refresh_command_full')}."
            )
        lines.append("")

    lines.extend(
        [
            "Columns: CAGR | Vol | MaxDD | Sharpe | Stress | Client-fit",
            "",
        ]
    )

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

    methodology_lines = [
        line
        for line in (
            _optimizer_methodology_txt_line(cand)
            for cand in comparison.get("candidates", [])
        )
        if line
    ]
    if methodology_lines:
        lines.extend(
            [
                "",
                "Optimizer methodology notes",
                "-" * 72,
                *methodology_lines,
            ]
        )

    readiness_lines = [
        line
        for line in (
            _optimization_readiness_txt_line(cand)
            for cand in comparison.get("candidates", [])
        )
        if line
    ]
    if readiness_lines:
        lines.extend(
            [
                "",
                "Optimization readiness (optimizer-backed rows)",
                "-" * 72,
                *readiness_lines,
            ]
        )

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

    from src.portfolio_health_score import write_portfolio_health_score_outputs
    from src.robustness_scorecard import (
        build_robustness_scorecard,
        write_robustness_scorecard_outputs,
    )

    rob_paths = write_robustness_scorecard_outputs(
        cfg, project_root=project_root, comparison=comparison
    )
    paths.update(rob_paths)
    robustness_doc = build_robustness_scorecard(comparison, project_root=project_root)
    paths.update(
        write_portfolio_health_score_outputs(
            cfg,
            project_root=project_root,
            comparison=comparison,
            robustness_scorecard=robustness_doc,
        )
    )

    from src.selection_engine import write_selection_decision_outputs

    health_path = paths.get("portfolio_health_score_json")
    health_doc = None
    if health_path and health_path.is_file():
        health_doc = _load_json(health_path)
    sel_paths = write_selection_decision_outputs(
        cfg,
        project_root=project_root,
        comparison=comparison,
        health=health_doc,
        robustness=robustness_doc,
    )
    paths.update(sel_paths)

    selection_doc = None
    sel_json = paths.get("selection_decision_json")
    if sel_json and sel_json.is_file():
        selection_doc = _load_json(sel_json)

    from src.tradeoff_and_model_risk import write_tradeoff_and_model_risk_outputs

    paths.update(
        write_tradeoff_and_model_risk_outputs(
            cfg,
            project_root=project_root,
            comparison=comparison,
            selection=selection_doc,
            health=health_doc,
            robustness=robustness_doc,
        )
    )

    model_risk_doc = _load_json(
        paths.get("model_risk_diagnostics_json") or out_dir / "model_risk_diagnostics.json"
    )
    from src.assumption_sensitivity import write_assumption_sensitivity_outputs

    paths.update(
        write_assumption_sensitivity_outputs(
            cfg,
            project_root=project_root,
            comparison=comparison,
            selection=selection_doc,
            health=health_doc,
            robustness=robustness_doc,
            model_risk=model_risk_doc,
        )
    )

    from src.pareto_dominance import write_pareto_dominance_outputs

    paths.update(
        write_pareto_dominance_outputs(
            cfg,
            project_root=project_root,
            comparison=comparison,
            selection=selection_doc,
        )
    )

    pareto_doc = _load_json(
        paths.get("pareto_dominance_json") or out_dir / "pareto_dominance.json"
    )
    from src.regret_analysis import write_regret_analysis_outputs

    paths.update(
        write_regret_analysis_outputs(
            cfg,
            project_root=project_root,
            comparison=comparison,
            selection=selection_doc,
            pareto=pareto_doc,
        )
    )

    from src.current_vs_policy import write_current_vs_policy_status_outputs

    paths.update(
        write_current_vs_policy_status_outputs(
            cfg,
            comparison,
            project_root=project_root,
            selection=selection_doc,
        )
    )
    status_json = paths.get("current_vs_policy_status_json")
    workflow_status = _load_json(status_json) if status_json else None

    from src.action_engine import write_action_plan_outputs

    paths.update(
        write_action_plan_outputs(
            cfg,
            project_root=project_root,
            comparison=comparison,
            selection=selection_doc,
            workflow_status=workflow_status,
        )
    )

    from src.monitoring import write_monitoring_outputs

    action_doc = _load_json(paths.get("action_plan_json") or out_dir / "action_plan.json")
    paths.update(
        write_monitoring_outputs(
            cfg,
            project_root=project_root,
            comparison=comparison,
            health=health_doc,
            robustness=robustness_doc,
            selection=selection_doc,
            action=action_doc,
        )
    )

    from src.decision_journal import write_decision_journal_outputs

    monitoring_doc = _load_json(
        paths.get("monitoring_diff_json") or out_dir / "monitoring_diff.json"
    )
    journal_paths = write_decision_journal_outputs(
        cfg,
        project_root=project_root,
        comparison=comparison,
        selection=selection_doc,
        action=action_doc,
        monitoring_diff=monitoring_doc,
        health=health_doc,
        robustness=robustness_doc,
    )
    paths.update(journal_paths)

    from src.decision_package_reporting import write_decision_package_reporting_outputs

    journal_doc = _load_json(
        paths.get("decision_journal_json") or out_dir / "decision_journal.json"
    )
    tradeoff_doc = _load_json(
        paths.get("tradeoff_explanation_json") or out_dir / "tradeoff_explanation.json"
    )
    if model_risk_doc is None:
        model_risk_doc = _load_json(
            paths.get("model_risk_diagnostics_json") or out_dir / "model_risk_diagnostics.json"
        )
    assumption_doc = _load_json(
        paths.get("assumption_sensitivity_json") or out_dir / "assumption_sensitivity.json"
    )
    if pareto_doc is None:
        pareto_doc = _load_json(
            paths.get("pareto_dominance_json") or out_dir / "pareto_dominance.json"
        )
    regret_doc = _load_json(
        paths.get("regret_analysis_json") or out_dir / "regret_analysis.json"
    )
    paths.update(
        write_decision_package_reporting_outputs(
            cfg,
            project_root=project_root,
            comparison=comparison,
            health=health_doc,
            robustness=robustness_doc,
            selection=selection_doc,
            action=action_doc,
            monitoring_diff=monitoring_doc,
            decision_journal=journal_doc,
            workflow_status=workflow_status,
            tradeoff=tradeoff_doc,
            model_risk=model_risk_doc,
            assumption_sensitivity=assumption_doc,
            pareto_dominance=pareto_doc,
            regret_analysis=regret_doc,
        )
    )

    return paths


__all__ = [
    "SCHEMA_VERSION",
    "ANALYSIS_SUBJECT_SIDECAR_SUBDIR",
    "CURRENT_SIDECAR_SUBDIR",
    "analysis_subject_sidecar_dir",
    "build_candidate_comparison",
    "build_legacy_portfolio_comparison",
    "construction_disclosure_from_folder",
    "candidate_registry_ids",
    "current_sidecar_dir",
    "positive_current_weights",
    "resolve_current_artifact_folder",
    "sidecar_meets_minimum",
    "write_candidate_comparison_outputs",
    "write_candidate_comparison_txt",
]
