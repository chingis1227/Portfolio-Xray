"""
In-process candidate weight construction for the Candidate Portfolio Factory.

Orchestration only: delegates to ``src.portfolio_variants`` and robust-scenario helpers.
Does not change optimizer mathematics or weight semantics.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

from src.candidate_run_context import CandidateRunContext, prepare_candidate_run_context
from src.config_schema import PortfolioConfig
from src.optimization import MIN_WEIGHT_DEFAULT, _build_bounds, get_risk_portfolio_tickers
from src.portfolio_variants import (
    BASELINE_EQ_BY_CLASS_LABEL,
    BASELINE_EQ_LABEL,
    BASELINE_HRP_LABEL,
    BASELINE_MD_LABEL,
    BASELINE_MD_UNCONSTRAINED_LABEL,
    BASELINE_MCVAR_CONSTRAINED_LABEL,
    BASELINE_MCVAR_UNCAPPED_LABEL,
    BASELINE_MV_ADVANCED_LABEL,
    BASELINE_MV_LABEL,
    BASELINE_MV_UNCAPPED_LABEL,
    BASELINE_RISK_BUDGET_BY_ASSET_CLASS_LABEL,
    BASELINE_RISK_BUDGET_BY_ASSET_LABEL,
    BASELINE_ROBUST_MV_CONSTRAINED_LABEL,
    BASELINE_ROBUST_MV_UNCAPPED_LABEL,
    BASELINE_RP_LABEL,
    BaselineWeightsResult,
    build_equal_weight_baseline,
    build_equal_weight_by_asset_class_baseline,
    build_hierarchical_risk_parity_baseline,
    build_maximum_diversification_constrained,
    build_maximum_diversification_unconstrained,
    build_minimum_cvar_constrained,
    build_minimum_cvar_uncapped,
    build_minimum_variance_advanced_controls,
    build_minimum_variance_baseline,
    build_minimum_variance_uncapped_long_only,
    build_risk_budget_by_asset_baseline,
    build_risk_budget_by_asset_class_baseline,
    build_risk_parity_baseline,
    build_robust_mean_variance_constrained,
    build_robust_mean_variance_uncapped,
    equal_weight_baseline_metadata_export,
    export_baseline_weights_txt,
    hierarchical_risk_parity_baseline_metadata_export,
    maximum_diversification_baseline_metadata_export,
    minimum_cvar_baseline_metadata_export,
    minimum_variance_advanced_metadata_export,
    minimum_variance_baseline_metadata_export,
    minimum_variance_uncapped_metadata_export,
    risk_budgeting_baseline_metadata_export,
    robust_mean_variance_baseline_metadata_export,
)
from src.robust_scenario_optimization import (
    OBJECTIVE_LOWER_HALF_MEAN,
    build_robust_optimization_inputs,
    export_robust_optimization_outputs,
    lower_half_mean,
    run_robust_scenario_optimization,
)
from src.config import load_weights_file
from src.risk_contrib import rc_vol_window
from src.variant_builder_runtime import BuilderStepTiming, persist_builder_runtime_timing
from src.windows import slice_window

EXECUTION_MODES = frozenset({"fast", "standard", "legacy_full"})
WEIGHTS_ONLY_EXECUTION_MODES = frozenset({"fast", "standard"})
DEFAULT_EXECUTION_MODE = "legacy_full"

CANDIDATE_WEIGHTS_BUILD_FILENAME = "candidate_weights_build.json"
WEIGHTS_BUILD_SCHEMA = "candidate_weights_build_v1"

SUCCESS_STATUSES_OK_ONLY = frozenset({"OK"})
SUCCESS_STATUSES_WITH_APPROXIMATE = frozenset({"OK", "APPROXIMATE"})


def normalize_execution_mode(mode: str) -> str:
    normalized = (mode or DEFAULT_EXECUTION_MODE).strip().lower()
    if normalized not in EXECUTION_MODES:
        raise ValueError(
            f"Invalid execution_mode {mode!r}; expected one of: "
            f"{', '.join(sorted(EXECUTION_MODES))}"
        )
    return normalized


def uses_weights_only_phase(execution_mode: str) -> bool:
    return normalize_execution_mode(execution_mode) in WEIGHTS_ONLY_EXECUTION_MODES


def uses_lightweight_report_phase(execution_mode: str) -> bool:
    """Phase 2: comparison-ready snapshots via lightweight report profile."""
    return normalize_execution_mode(execution_mode) == "standard"


# Backward-compatible alias; factory uses CandidateRunContext (Session 4).
CandidateWeightsContext = CandidateRunContext


@dataclass(frozen=True)
class _WeightFamilySpec:
    portfolio_label: str
    build_fn: Callable[..., BaselineWeightsResult]
    success_statuses: frozenset[str]
    metadata_exporter: Callable[[dict[str, object]], dict[str, Any]] | None
    summary_metadata_key: str | None
    rc_from_diagnostics: bool = False


def prepare_candidate_weights_context(
    cfg: PortfolioConfig,
    *,
    project_root: Path,
    no_cache: bool = False,
) -> CandidateRunContext:
    """Deprecated name; delegates to ``prepare_candidate_run_context``."""
    return prepare_candidate_run_context(
        cfg,
        project_root=project_root,
        no_cache=no_cache,
        preload_factor_stress=True,
    )


def _family_specs() -> dict[str, _WeightFamilySpec]:
    return {
        "equal_weight": _WeightFamilySpec(
            portfolio_label=BASELINE_EQ_LABEL,
            build_fn=build_equal_weight_baseline,
            success_statuses=SUCCESS_STATUSES_OK_ONLY,
            metadata_exporter=equal_weight_baseline_metadata_export,
            summary_metadata_key="equal_weight_baseline_metadata",
        ),
        "equal_weight_by_asset_class": _WeightFamilySpec(
            portfolio_label=BASELINE_EQ_BY_CLASS_LABEL,
            build_fn=build_equal_weight_by_asset_class_baseline,
            success_statuses=SUCCESS_STATUSES_OK_ONLY,
            metadata_exporter=equal_weight_baseline_metadata_export,
            summary_metadata_key="equal_weight_baseline_metadata",
        ),
        "risk_parity": _WeightFamilySpec(
            portfolio_label=BASELINE_RP_LABEL,
            build_fn=build_risk_parity_baseline,
            success_statuses=SUCCESS_STATUSES_WITH_APPROXIMATE,
            metadata_exporter=None,
            summary_metadata_key=None,
            rc_from_diagnostics=True,
        ),
        "risk_budget_by_asset": _WeightFamilySpec(
            portfolio_label=BASELINE_RISK_BUDGET_BY_ASSET_LABEL,
            build_fn=build_risk_budget_by_asset_baseline,
            success_statuses=SUCCESS_STATUSES_WITH_APPROXIMATE,
            metadata_exporter=risk_budgeting_baseline_metadata_export,
            summary_metadata_key="risk_budgeting_metadata",
        ),
        "risk_budget_by_asset_class": _WeightFamilySpec(
            portfolio_label=BASELINE_RISK_BUDGET_BY_ASSET_CLASS_LABEL,
            build_fn=build_risk_budget_by_asset_class_baseline,
            success_statuses=SUCCESS_STATUSES_WITH_APPROXIMATE,
            metadata_exporter=risk_budgeting_baseline_metadata_export,
            summary_metadata_key="risk_budgeting_metadata",
        ),
        "hierarchical_risk_parity": _WeightFamilySpec(
            portfolio_label=BASELINE_HRP_LABEL,
            build_fn=build_hierarchical_risk_parity_baseline,
            success_statuses=SUCCESS_STATUSES_WITH_APPROXIMATE,
            metadata_exporter=hierarchical_risk_parity_baseline_metadata_export,
            summary_metadata_key="hierarchical_risk_parity_metadata",
        ),
        "minimum_variance": _WeightFamilySpec(
            portfolio_label=BASELINE_MV_LABEL,
            build_fn=build_minimum_variance_baseline,
            success_statuses=SUCCESS_STATUSES_WITH_APPROXIMATE,
            metadata_exporter=minimum_variance_baseline_metadata_export,
            summary_metadata_key="minimum_variance_metadata",
        ),
        "minimum_variance_uncapped": _WeightFamilySpec(
            portfolio_label=BASELINE_MV_UNCAPPED_LABEL,
            build_fn=build_minimum_variance_uncapped_long_only,
            success_statuses=SUCCESS_STATUSES_WITH_APPROXIMATE,
            metadata_exporter=minimum_variance_uncapped_metadata_export,
            summary_metadata_key="minimum_variance_metadata",
        ),
        "minimum_variance_advanced": _WeightFamilySpec(
            portfolio_label=BASELINE_MV_ADVANCED_LABEL,
            build_fn=build_minimum_variance_advanced_controls,
            success_statuses=SUCCESS_STATUSES_WITH_APPROXIMATE,
            metadata_exporter=minimum_variance_advanced_metadata_export,
            summary_metadata_key="minimum_variance_metadata",
        ),
        "maximum_diversification": _WeightFamilySpec(
            portfolio_label=BASELINE_MD_LABEL,
            build_fn=build_maximum_diversification_constrained,
            success_statuses=SUCCESS_STATUSES_WITH_APPROXIMATE,
            metadata_exporter=maximum_diversification_baseline_metadata_export,
            summary_metadata_key="maximum_diversification_metadata",
        ),
        "maximum_diversification_uncapped": _WeightFamilySpec(
            portfolio_label=BASELINE_MD_UNCONSTRAINED_LABEL,
            build_fn=build_maximum_diversification_unconstrained,
            success_statuses=SUCCESS_STATUSES_WITH_APPROXIMATE,
            metadata_exporter=maximum_diversification_baseline_metadata_export,
            summary_metadata_key="maximum_diversification_metadata",
        ),
        "minimum_cvar_constrained": _WeightFamilySpec(
            portfolio_label=BASELINE_MCVAR_CONSTRAINED_LABEL,
            build_fn=build_minimum_cvar_constrained,
            success_statuses=SUCCESS_STATUSES_WITH_APPROXIMATE,
            metadata_exporter=minimum_cvar_baseline_metadata_export,
            summary_metadata_key="minimum_cvar_metadata",
        ),
        "minimum_cvar_uncapped": _WeightFamilySpec(
            portfolio_label=BASELINE_MCVAR_UNCAPPED_LABEL,
            build_fn=build_minimum_cvar_uncapped,
            success_statuses=SUCCESS_STATUSES_WITH_APPROXIMATE,
            metadata_exporter=minimum_cvar_baseline_metadata_export,
            summary_metadata_key="minimum_cvar_metadata",
        ),
        "robust_mv_constrained": _WeightFamilySpec(
            portfolio_label=BASELINE_ROBUST_MV_CONSTRAINED_LABEL,
            build_fn=build_robust_mean_variance_constrained,
            success_statuses=SUCCESS_STATUSES_WITH_APPROXIMATE,
            metadata_exporter=robust_mean_variance_baseline_metadata_export,
            summary_metadata_key="robust_mean_variance_metadata",
        ),
        "robust_mv_uncapped": _WeightFamilySpec(
            portfolio_label=BASELINE_ROBUST_MV_UNCAPPED_LABEL,
            build_fn=build_robust_mean_variance_uncapped,
            success_statuses=SUCCESS_STATUSES_WITH_APPROXIMATE,
            metadata_exporter=robust_mean_variance_baseline_metadata_export,
            summary_metadata_key="robust_mean_variance_metadata",
        ),
    }


def _effective_cfg_for_candidate(
    context: CandidateWeightsContext,
    candidate_id: str,
) -> PortfolioConfig | None:
    if candidate_id not in ("robust_mv_constrained", "robust_mv_uncapped"):
        return context.cfg
    if context.robust_mv_lambda is None:
        return None
    return replace(context.cfg, robust_mv_lambda=float(context.robust_mv_lambda))


def build_candidate_weights(
    context: CandidateWeightsContext,
    candidate_id: str,
) -> BaselineWeightsResult:
    """
    Build weights for one registry candidate in-process (no report pipeline).
    """
    if candidate_id == "robust_scenario":
        return _build_robust_scenario_weights(context)

    spec = _family_specs().get(candidate_id)
    if spec is None:
        return BaselineWeightsResult(
            weights={},
            status="FAIL_CONFIG",
            diagnostics={"reason": f"No in-process weight builder for {candidate_id}"},
        )

    cfg_eff = _effective_cfg_for_candidate(context, candidate_id)
    if cfg_eff is None:
        return BaselineWeightsResult(
            weights={},
            status="FAIL_CONFIG",
            diagnostics={
                "reason": (
                    "Robust MV λ not resolved; run run_robust_mv_lambda_calibration.py "
                    "or pass --robust-mv-lambda on legacy builder."
                ),
                "lambda_resolution": context.robust_mv_lambda_resolution,
            },
        )

    return spec.build_fn(
        cfg_eff,
        context.monthly_returns,
        context.analysis_end_str,
        context.primary_window,
    )


def _build_robust_scenario_weights(context: CandidateWeightsContext) -> BaselineWeightsResult:
    cfg = context.cfg
    rob = getattr(cfg, "robust_scenario_optimization", None) or {}
    final_dir = context.project_root / cfg.output_dir_final
    norm_path = final_dir / "scenario_library_normalized.json"
    if not norm_path.is_file():
        return BaselineWeightsResult(
            weights={},
            status="FAIL_CONFIG",
            diagnostics={
                "reason": f"Missing {norm_path.name} under {cfg.output_dir_final}",
            },
        )

    stress_path = final_dir / "stress_report.json"
    stress_report = None
    if stress_path.is_file():
        stress_report = json.loads(stress_path.read_text(encoding="utf-8"))

    normalized = json.loads(norm_path.read_text(encoding="utf-8"))
    cash_proxy, _rf = resolve_cash_and_rf(cfg)
    risk_tickers = get_risk_portfolio_tickers(list(cfg.tickers), cash_proxy)
    lam = dict(rob.get("lambdas") or {})
    try:
        inputs = build_robust_optimization_inputs(
            scenario_library_normalized=normalized,
            stress_report=stress_report,
            risk_tickers=risk_tickers,
            objective_mode=OBJECTIVE_LOWER_HALF_MEAN,
            lambdas=lam,
        )
    except Exception as exc:
        return BaselineWeightsResult(
            weights={},
            status="FAIL_CONFIG",
            diagnostics={"reason": str(exc)},
        )

    min_w = (
        float(cfg.min_single_security_weight_pct)
        if cfg.min_single_security_weight_pct is not None
        and cfg.min_single_security_weight_pct > 0
        else MIN_WEIGHT_DEFAULT
    )
    bounds = _build_bounds(
        inputs.ticker_order,
        len(inputs.ticker_order),
        min_w,
        cfg.max_single_security_weight_pct,
        None,
    )
    warm: list[np.ndarray] = []
    wpol = load_weights_file()
    if wpol:
        v = np.array([float(wpol.get(t, 0.0)) for t in inputs.ticker_order], dtype=float)
        s = float(v.sum())
        if s > 1e-12:
            warm.append(v / s)
    warm.append(np.ones(len(inputs.ticker_order)) / len(inputs.ticker_order))

    result = run_robust_scenario_optimization(inputs, bounds=bounds, warm_starts=warm)
    export_robust_optimization_outputs(
        result,
        inputs,
        output_dir=final_dir,
        comparisons={},
        write_export_artifacts=False,
    )

    weights_vec = result.get("weights_vec")
    if weights_vec is None:
        return BaselineWeightsResult(
            weights={},
            status="FAIL_NUMERICAL",
            diagnostics={"reason": "Robust scenario optimization returned no weights"},
        )
    weights = {
        t: float(weights_vec[i])
        for i, t in enumerate(inputs.ticker_order)
        if float(weights_vec[i]) > 1e-12
    }
    solver = result.get("solver") if isinstance(result.get("solver"), dict) else {}
    status = "OK" if solver.get("success") else "APPROXIMATE"
    return BaselineWeightsResult(
        weights=weights,
        status=status,
        diagnostics={
            "method_id": "robust_scenario_optimization_v1",
            "objective_mode": OBJECTIVE_LOWER_HALF_MEAN,
            "analysis_end": context.analysis_end_str,
            "solver": solver,
        },
    )


def _compute_rc_series(
    context: CandidateWeightsContext,
    weights: dict[str, float],
    *,
    diagnostics: dict[str, object],
    prefer_diagnostics_rc: bool,
) -> pd.Series | None:
    if prefer_diagnostics_rc:
        rc_diag = diagnostics.get("rc_by_asset")
        if isinstance(rc_diag, dict) and rc_diag:
            return pd.Series({str(k): float(v) for k, v in rc_diag.items()})
    try:
        cols = [t for t in context.cfg.tickers if t in context.monthly_returns.columns]
        ret_slice = slice_window(
            context.monthly_returns[cols],
            context.analysis_end_str,
            context.primary_window,
        ).dropna(how="all")
        if len(ret_slice) < 2:
            return None
        weights_df = pd.DataFrame(
            index=ret_slice.index,
            data={t: float(weights.get(t, 0.0)) for t in cols},
        )
        return rc_vol_window(ret_slice, weights_df, ddof=1)
    except Exception:
        return None


def write_candidate_weights(
    context: CandidateWeightsContext,
    candidate_id: str,
    result: BaselineWeightsResult,
    *,
    artifact_dir: Path,
    config_fingerprint: str | None = None,
    write_txt: bool = False,
) -> dict[str, Any]:
    """
    Persist weights artifacts under ``artifact_dir`` (same contract as ``run_*.py`` builders).
    """
    spec = _family_specs().get(candidate_id)
    portfolio_label = (
        spec.portfolio_label if spec else "Robust Scenario Portfolio (scenario optimization v1)"
    )
    artifact_dir.mkdir(parents=True, exist_ok=True)

    meta_export: dict[str, Any] | None = None
    if spec and spec.metadata_exporter is not None:
        meta_export = spec.metadata_exporter(result.diagnostics)
        with open(artifact_dir / "baseline_weights_metadata.json", "w", encoding="utf-8") as handle:
            json.dump(meta_export, handle, indent=2, ensure_ascii=False)
    elif candidate_id == "robust_scenario" and result.status in SUCCESS_STATUSES_WITH_APPROXIMATE:
        final_dir = context.project_root / context.cfg.output_dir_final
        weights_src = final_dir / "robust_optimization_weights.json"
        meta_export = {
            "variant": "robust_scenario_portfolio_v1",
            "label": portfolio_label,
            "weights_source": str(weights_src.resolve()),
            "analysis_end": context.analysis_end_str,
        }
        with open(artifact_dir / "baseline_weights_metadata.json", "w", encoding="utf-8") as handle:
            json.dump(meta_export, handle, indent=2, ensure_ascii=False)

    with open(artifact_dir / "weights.json", "w", encoding="utf-8") as handle:
        json.dump(result.weights, handle, indent=2, ensure_ascii=False)

    if candidate_id == "robust_scenario":
        with open(artifact_dir / "robust_scenario_weights.json", "w", encoding="utf-8") as handle:
            json.dump(result.weights, handle, indent=2, ensure_ascii=False)

    rc_series = None
    if spec and result.status in spec.success_statuses:
        rc_series = _compute_rc_series(
            context,
            result.weights,
            diagnostics=result.diagnostics,
            prefer_diagnostics_rc=spec.rc_from_diagnostics,
        )
    if write_txt:
        export_baseline_weights_txt(
            result.weights,
            rc_series=rc_series,
            label=portfolio_label,
            output_dir=artifact_dir,
        )

    summary: dict[str, Any] = {
        "portfolio_type": portfolio_label,
        "status": result.status,
    }
    reason = result.diagnostics.get("reason")
    if reason:
        summary["reason"] = reason
    if spec and spec.summary_metadata_key and meta_export is not None:
        summary[spec.summary_metadata_key] = meta_export
    if candidate_id == "robust_scenario" and meta_export is not None:
        summary["robust_scenario_metadata"] = meta_export

    with open(artifact_dir / "summary.json", "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)

    success = spec is None or result.status in (
        spec.success_statuses if spec else SUCCESS_STATUSES_WITH_APPROXIMATE
    )
    if candidate_id == "robust_scenario":
        success = result.status in SUCCESS_STATUSES_WITH_APPROXIMATE

    if write_txt and not success:
        with open(artifact_dir / "summary.txt", "w", encoding="utf-8") as handle:
            handle.write(f"{portfolio_label} — infeasible or failed baseline\n")
            handle.write(f"Status: {result.status}\n")
            if reason:
                handle.write(f"Reason: {reason}\n")

    manifest = {
        "schema_version": WEIGHTS_BUILD_SCHEMA,
        "candidate_id": candidate_id,
        "analysis_end": context.analysis_end_str,
        "config_fingerprint": config_fingerprint,
        "status": result.status,
        "built_at": datetime.now(timezone.utc).isoformat(),
        "weights_path": "weights.json",
        "phases_completed": ["weights"],
    }
    manifest_path = artifact_dir / CANDIDATE_WEIGHTS_BUILD_FILENAME
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)

    return {
        "weights_json": str(artifact_dir / "weights.json"),
        "weights_build_manifest": str(manifest_path),
        "summary_json": str(artifact_dir / "summary.json"),
        "success": success,
    }


def weights_build_freshness(
    artifact_dir: Path,
    *,
    expected_analysis_end: str | None,
    expected_config_fingerprint: str | None,
) -> tuple[str, str | None, str | None]:
    """Freshness of Phase-1 weights relative to review ``analysis_end`` / config fingerprint."""
    manifest_path = artifact_dir / CANDIDATE_WEIGHTS_BUILD_FILENAME
    if not manifest_path.is_file():
        weights_path = artifact_dir / "weights.json"
        if not weights_path.is_file():
            return "missing", None, None
        return "unchecked", None, None

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "missing", None, None
    if not isinstance(manifest, dict):
        return "missing", None, None

    build_end = manifest.get("analysis_end")
    build_end_str = str(build_end) if build_end else None
    build_fp = manifest.get("config_fingerprint")
    build_fp_str = str(build_fp) if build_fp else None
    status = manifest.get("status")
    if status not in SUCCESS_STATUSES_OK_ONLY and status not in SUCCESS_STATUSES_WITH_APPROXIMATE:
        return "stale", build_end_str, build_fp_str

    if not expected_analysis_end:
        return "unchecked", build_end_str, build_fp_str
    if build_end_str != expected_analysis_end:
        return "stale", build_end_str, build_fp_str
    if expected_config_fingerprint and build_fp_str != expected_config_fingerprint:
        return "stale_config", build_end_str, build_fp_str
    return "fresh", build_end_str, build_fp_str


def candidate_weights_success(result: BaselineWeightsResult, candidate_id: str) -> bool:
    if candidate_id == "robust_scenario":
        return result.status in SUCCESS_STATUSES_WITH_APPROXIMATE
    spec = _family_specs().get(candidate_id)
    if spec is None:
        return False
    return result.status in spec.success_statuses
