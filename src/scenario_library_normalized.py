"""
Scenario Library Normalized View v1.
Derived layer on top of Scenario Library v1 for future Monte Carlo / robust optimization
consumers. This module does not alter existing analytics, frequencies, optimizer logic,
mandate checks, or stress pass/fail logic.
Normalized classification intentionally overrides Scenario Library v1 labels where
upstream gates mix unrelated frequencies or conservative synthetic suitability flags.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd

from src.historical_stress_fallback import (
    build_historical_episode_asset_returns,
    episode_window_for_scenario,
    merge_proxy_config,
)
SCENARIO_LIBRARY_NORMALIZED_VERSION = "scenario_library_normalized_v1"
WEEKLY_TO_MONTHLY_VARIANCE_FACTOR = 12.0 / 52.0
ANNUAL_TO_MONTHLY_VARIANCE_FACTOR = 1.0 / 12.0
# Episodes ending before this date use the long weekly factor panel with partial rows
# for tier-4 shock sums (dotcom). Later episodes use the same strict 2007+ matrix as run_stress.
_FACTOR_SHOCK_LOOSE_EPISODE_END_BEFORE = pd.Timestamp("2007-01-01")
_QUALITY_ORDER = ("insufficient_data", "low_confidence", "usable", "reliable")
def _scale_nested_cov(nested: dict[str, dict[str, float]], factor: float) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for k, row in (nested or {}).items():
        out[str(k)] = {str(kk): float(vv) * factor for kk, vv in (row or {}).items()}
    return out
def _quality_tier(q: str | None) -> str:
    s = (q or "").strip().lower()
    if s in {"reliable", "usable", "low_confidence", "insufficient_data"}:
        return s
    return "insufficient_data"
def _worst_quality_tier(a: str, b: str) -> str:
    ia = _QUALITY_ORDER.index(a) if a in _QUALITY_ORDER else 0
    ib = _QUALITY_ORDER.index(b) if b in _QUALITY_ORDER else 0
    return _QUALITY_ORDER[min(ia, ib)]
def _confidence_for_classification(classification: str, warnings: list[str]) -> float:
    c = str(classification or "")
    if c == "ready_for_optimization":
        return 1.0
    if c == "usable_with_caution":
        return 0.5
    if c == "diagnostic_only":
        severe = any(
            x in w for w in (warnings or []) for x in ("critical_missing", "not_for_optimization", "frequency_conflict")
        )
        return 0.0 if severe else 0.1
    return 0.0
def _factor_betas_nonempty(s: dict[str, Any]) -> bool:
    fb = s.get("factor_betas")
    if not isinstance(fb, dict) or not fb:
        return False
    if "5y" in fb:
        inner = fb.get("5y")
        return isinstance(inner, dict) and len(inner) > 0
    return True
def _return_type_and_values(
    s: dict[str, Any],
) -> tuple[str, float | None, float | None, float | None, float | None, list[str]]:
    warnings: list[str] = []
    sid = str(s.get("scenario_id") or "")
    st = str(s.get("scenario_type") or "")
    raw = s.get("scenario_portfolio_return")
    try:
        raw_num = float(raw) if raw is not None else None
    except Exception:
        raw_num = None
        warnings.append("scenario_portfolio_return_not_numeric")
    if st == "historical_stress":
        return "historical_episode_loss", raw_num, None, raw_num, None, warnings
    if st == "synthetic_stress":
        return "synthetic_one_time_shock", raw_num, None, None, raw_num, warnings
    if st == "macro_regime":
        has_source = bool(s.get("scenario_asset_return") is not None or (s.get("scenario_factor_move") or []))
        if has_source and raw_num is not None:
            return "regime_average_return", raw_num, raw_num, None, None, warnings
        warnings.append(f"{sid}:regime_return_source_unavailable")
        return "unavailable", raw_num, None, None, None, warnings
    if st == "base":
        if raw_num is not None:
            return "monthly_expected_return", raw_num, raw_num, None, None, warnings
        warnings.append(f"{sid}:monthly_expected_return_unavailable")
        return "unavailable", raw_num, None, None, None, warnings
    warnings.append(f"{sid}:unknown_scenario_type")
    return "unavailable", raw_num, None, None, None, warnings
def _covariances_for_view(
    s: dict[str, Any], key: str
) -> tuple[dict[str, dict[str, float]] | None, dict[str, dict[str, float]] | None, list[str]]:
    warnings: list[str] = []
    block = s.get(key) if isinstance(s.get(key), dict) else {}
    if not block:
        return None, None, warnings
    mat = block.get("matrix")
    if not isinstance(mat, dict) or not mat:
        warnings.append(f"{key}_matrix_missing")
        return None, None, warnings
    original = dict(mat)
    native = str(block.get("native_frequency") or s.get("frequency") or "unknown").lower()
    normalized = str(block.get("normalized_frequency") or "").lower()
    if native == "weekly":
        monthly = _scale_nested_cov(original, WEEKLY_TO_MONTHLY_VARIANCE_FACTOR)
    elif native in {"annualized", "yearly"}:
        monthly = _scale_nested_cov(original, ANNUAL_TO_MONTHLY_VARIANCE_FACTOR)
    elif native == "daily" and "annual" in normalized:
        monthly = _scale_nested_cov(original, ANNUAL_TO_MONTHLY_VARIANCE_FACTOR)
    elif native in {"monthly", "episode"} or "monthly" in normalized:
        monthly = dict(original)
    else:
        monthly = None
        warnings.append(f"{key}_monthly_equivalent_undefined_for_native_frequency:{native}")
    return original, monthly, warnings
def _optimization_role(scenario_type: str, classification: str) -> str:
    if classification == "insufficient_data":
        return "excluded"
    if classification == "diagnostic_only":
        return "diagnostic_only"
    if scenario_type == "base":
        return "objective_input"
    if scenario_type in {"historical_stress", "synthetic_stress"}:
        return "hard_stress_constraint" if classification == "ready_for_optimization" else "soft_constraint"
    if scenario_type == "macro_regime":
        return "soft_constraint" if classification == "usable_with_caution" else "diagnostic_only"
    return "excluded"
def _reason_for_classification(classification: str, warnings: list[str], suffix: str | None = None) -> str:
    c = str(classification or "insufficient_data")
    parts = [c]
    if suffix:
        parts.append(suffix)
    ws = list(warnings or [])
    if ws:
        parts.append(";".join(str(w) for w in ws[:3]))
    return ":".join(parts)
def summarize_normalized_classifications(scenarios: list[dict[str, Any]]) -> dict[str, int]:
    out = {
        "n_ready_for_optimization": 0,
        "n_usable_with_caution": 0,
        "n_diagnostic_only": 0,
        "n_insufficient_data": 0,
    }
    for s in scenarios:
        c = str(s.get("classification") or "insufficient_data")
        if c == "ready_for_optimization":
            out["n_ready_for_optimization"] += 1
        elif c == "usable_with_caution":
            out["n_usable_with_caution"] += 1
        elif c == "diagnostic_only":
            out["n_diagnostic_only"] += 1
        else:
            out["n_insufficient_data"] += 1
    return out
def summarize_normalized_roles(scenarios: list[dict[str, Any]]) -> dict[str, list[str]]:
    roles: dict[str, list[str]] = {
        "objective_input": [],
        "hard_stress_constraint": [],
        "soft_constraint": [],
        "diagnostic_only": [],
        "excluded": [],
    }
    for s in scenarios:
        sid = str(s.get("scenario_id") or "unknown")
        role = str(s.get("optimization_role") or "excluded")
        if role in roles:
            roles[role].append(sid)
        else:
            roles["excluded"].append(sid)
    roles["objective_input"].sort()
    roles["hard_stress_constraint"].sort()
    roles["soft_constraint"].sort()
    roles["diagnostic_only"].sort()
    roles["excluded"].sort()
    return roles
def _weights_over_universe(weights: dict[str, float], universe: list[str]) -> np.ndarray:
    w = np.array([float(weights.get(t, 0.0)) for t in universe], dtype=float)
    s = float(w.sum())
    if s > 0:
        w = w / s
    return w
def _compute_base_monthly_mu(
    *,
    asset_cov_monthly: dict[str, dict[str, float]] | None,
    monthly_returns: pd.DataFrame | None,
    weights: dict[str, float] | None,
    tickers: list[str] | None,
    optimizer_mu_by_ticker: dict[str, float] | pd.Series | None,
) -> dict[str, Any]:
    """
    Monthly alignment only: μ vector shares asset keys with ``asset_covariance`` monthly matrix.
    """
    out: dict[str, Any] = {
        "expected_returns_by_asset": None,
        "portfolio_expected_return_monthly": None,
        "expected_return_method": None,
        "asset_universe_optimization": None,
        "base_mu_n_obs": None,
        "mu_warnings": [],
    }
    if not asset_cov_monthly:
        out["mu_warnings"].append("base_mu_skipped_no_asset_covariance_monthly")
        return out
    universe = sorted(asset_cov_monthly.keys())
    out["asset_universe_optimization"] = universe
    opt_mu = optimizer_mu_by_ticker
    if isinstance(opt_mu, pd.Series):
        opt_mu = {str(k): float(v) for k, v in opt_mu.items() if pd.notna(v)}
    elif isinstance(opt_mu, dict):
        opt_mu = {str(k): float(v) for k, v in opt_mu.items()}
    use_optimizer = (
        isinstance(opt_mu, dict)
        and len(opt_mu) > 0
        and all(t in opt_mu for t in universe)
    )
    if use_optimizer:
        mu_map = {t: float(opt_mu[t]) for t in universe}
        out["expected_returns_by_asset"] = mu_map
        out["expected_return_method"] = "optimizer_mu_precomputed"
        wvec = _weights_over_universe(weights or {}, universe)
        out["portfolio_expected_return_monthly"] = float(sum(wvec[i] * mu_map[universe[i]] for i in range(len(universe))))
        return out
    if monthly_returns is None or monthly_returns.empty:
        out["mu_warnings"].append("base_mu_skipped_no_monthly_returns_or_optimizer_mu")
        return out
    mr = monthly_returns.copy()
    mr.index = pd.to_datetime(mr.index).tz_localize(None)
    cols = [t for t in universe if t in mr.columns]
    if not cols:
        out["mu_warnings"].append("base_mu_skipped_no_overlap_monthly_returns_vs_covariance_universe")
        return out
    sub = mr[cols].dropna(how="all")
    n_obs = int(len(sub))
    out["base_mu_n_obs"] = n_obs
    if n_obs < 2:
        out["mu_warnings"].append("base_mu_insufficient_monthly_history_for_mean")
        return out
    mu_series = sub.astype(float).mean(axis=0, skipna=True)
    mu_map_full = {str(t): float(mu_series[t]) for t in cols if pd.notna(mu_series.get(t))}
    if len(mu_map_full) < len(universe):
        out["mu_warnings"].append("base_mu_partial_asset_coverage_mean_returns")
    mu_aligned = {t: float(mu_map_full[t]) if t in mu_map_full else float("nan") for t in universe}
    if any(np.isnan(v) for v in mu_aligned.values()):
        out["mu_warnings"].append("base_mu_contains_nan_for_some_assets")
        return out
    out["expected_returns_by_asset"] = mu_aligned
    out["expected_return_method"] = "historical_monthly_mean"
    wvec = _weights_over_universe(weights or {}, universe)
    out["portfolio_expected_return_monthly"] = float(
        sum(wvec[i] * mu_aligned[universe[i]] for i in range(len(universe)))
    )
    return out
def _cov_block_quality_status(block: Any) -> str:
    if not isinstance(block, dict):
        return "insufficient_data"
    raw_q = block.get("quality_status")
    if raw_q is not None and str(raw_q).strip() != "":
        return str(raw_q)
    mat = block.get("matrix")
    if isinstance(mat, dict) and mat:
        return "usable"
    return "insufficient_data"


def _normalized_classification(
    *,
    sid: str,
    st: str,
    s_raw: dict[str, Any],
    rt: str,
    shock_ret: float | None,
    ep_loss: float | None,
    a_monthly: dict[str, dict[str, float]] | None,
    f_monthly: dict[str, dict[str, float]] | None,
    base_mu_info: dict[str, Any] | None,
    pipeline_returns_frequency: str | None,
    historical_fallback_meta: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """
    Returns (classification, reason_suffix).
    """
    ac_q = _cov_block_quality_status(s_raw.get("asset_covariance"))
    fc_q = _cov_block_quality_status(s_raw.get("factor_covariance"))
    tier_a = _quality_tier(ac_q)
    tier_f = _quality_tier(fc_q)
    worst = _worst_quality_tier(tier_a, tier_f)
    ws = list(s_raw.get("warnings") or [])
    if st == "macro_regime":
        if a_monthly is None or f_monthly is None:
            return "diagnostic_only", "macro_regime_missing_monthly_equivalent_covariance"
        if rt == "unavailable":
            return "diagnostic_only", "macro_regime_no_valid_return_source"
        n_obs = int((s_raw.get("asset_covariance") or {}).get("n_obs") or 0)
        if n_obs < 24:
            return "diagnostic_only", "macro_regime_n_obs_below_24"
        if worst == "insufficient_data":
            return "diagnostic_only", "macro_regime_cov_quality_insufficient"
        if any("frequency_conflict" == str(w) for w in ws):
            return "diagnostic_only", "macro_regime_frequency_conflict"
        return "usable_with_caution", "macro_regime_monthly_compatible_strict_gate"
    if st == "base":
        if a_monthly is None or f_monthly is None:
            return "insufficient_data", "base_missing_asset_or_factor_covariance_monthly_view"
        if not _factor_betas_nonempty(s_raw):
            return "insufficient_data", "base_missing_factor_betas"
        mu_method = (base_mu_info or {}).get("expected_return_method")
        port_mu = (base_mu_info or {}).get("portfolio_expected_return_monthly")
        if mu_method is None or port_mu is None:
            return "diagnostic_only", "base_missing_mu_source_for_objective_slice"
        mu_ws = list((base_mu_info or {}).get("mu_warnings") or [])
        if mu_ws:
            return "usable_with_caution", f"base_mu_warnings:{mu_ws[0]}"
        if worst == "insufficient_data":
            return "usable_with_caution", "base_cov_quality_insufficient_factor_or_asset"
        if tier_a in {"reliable", "usable"} and tier_f in {"reliable", "usable"}:
            return "ready_for_optimization", "base_monthly_sigma_mu_betas_ready"
        if worst == "low_confidence":
            return "usable_with_caution", "base_cov_quality_low_confidence"
        return "usable_with_caution", "base_cov_quality_mixed"
    if st == "synthetic_stress":
        struct = (
            shock_ret is not None
            and np.isfinite(float(shock_ret))
            and a_monthly is not None
            and f_monthly is not None
            and _factor_betas_nonempty(s_raw)
        )
        if not struct:
            return "insufficient_data", "synthetic_missing_shock_return_covariance_or_betas"
        if tier_a == "insufficient_data" or tier_f == "insufficient_data":
            return "usable_with_caution", "synthetic_cov_quality_flagged_insufficient_but_structurally_present"
        if tier_a in {"reliable", "usable"} and tier_f in {"reliable", "usable"}:
            return "ready_for_optimization", "synthetic_hard_stress_inputs_present"
        if worst == "low_confidence":
            return "usable_with_caution", "synthetic_cov_quality_low_confidence"
        return "usable_with_caution", "synthetic_cov_quality_mixed"
    if st == "historical_stress":
        if historical_fallback_meta is None:
            if sid in {"dotcom", "2008"} and any(
                "historical_asset_cov_insufficient" in str(w) for w in ws
            ):
                return "insufficient_data", "historical_episode_asset_cov_insufficient_dotcom_2008"
        elif historical_fallback_meta.get("historical_stress_method") == "unavailable":
            return "insufficient_data", "historical_fallback_unavailable"
        struct = (
            ep_loss is not None
            and np.isfinite(float(ep_loss))
            and a_monthly is not None
            and f_monthly is not None
            and _factor_betas_nonempty(s_raw)
        )
        if not struct:
            miss = []
            if ep_loss is None:
                miss.append("episode_loss")
            if a_monthly is None:
                miss.append("asset_cov")
            if f_monthly is None:
                miss.append("factor_cov")
            if not _factor_betas_nonempty(s_raw):
                miss.append("betas")
            return "insufficient_data", f"historical_missing:{','.join(miss)}"
        if tier_a == "insufficient_data" or tier_f == "insufficient_data":
            return "diagnostic_only", "historical_cov_quality_insufficient"
        if tier_a in {"reliable", "usable"} and tier_f in {"reliable", "usable"}:
            cls_h = "ready_for_optimization"
            suf_h = "historical_episode_inputs_ready"
        else:
            cls_h = "usable_with_caution"
            suf_h = "historical_cov_quality_weak"
        if historical_fallback_meta is not None:
            sqfb = str(historical_fallback_meta.get("scenario_quality_status") or "usable")
            if sqfb == "insufficient_data":
                return "insufficient_data", "historical_fallback_quality_insufficient"
            if sqfb == "low_confidence":
                return "diagnostic_only", "historical_fallback_factor_replay_or_weak"
            if sqfb == "usable":
                if cls_h == "ready_for_optimization":
                    return "usable_with_caution", suf_h + ";historical_fallback_asset_class_mix"
                return cls_h, suf_h
            if sqfb == "reliable":
                return cls_h, suf_h
        return cls_h, suf_h
    return str(s_raw.get("classification") or "insufficient_data"), "passthrough_non_standard_type"


def build_scenario_library_normalized(
    scenario_library: dict[str, Any],
    *,
    output_dir_final: str | Path | None = None,
    output_dir_csv: str | Path | None = None,
    monthly_returns: pd.DataFrame | None = None,
    weights: dict[str, float] | None = None,
    tickers: list[str] | None = None,
    returns_frequency_pipeline: str | None = None,
    optimizer_mu_by_ticker: dict[str, float] | pd.Series | None = None,
    stress_report: dict[str, Any] | None = None,
    factor_returns_weekly: pd.DataFrame | None = None,
    factor_returns_weekly_episode_loose: pd.DataFrame | None = None,
    cash_proxy_ticker: str | None = None,
    historical_stress_proxy_config: dict[str, Any] | None = None,
    enable_historical_stress_fallback: bool = True,
) -> dict[str, Any]:
    scenarios_in = scenario_library.get("scenarios") if isinstance(scenario_library, dict) else None
    scenarios_in = scenarios_in if isinstance(scenarios_in, list) else []
    scenarios_out: list[dict[str, Any]] = []
    missing_rows: list[dict[str, str]] = []
    warning_rows: list[dict[str, str]] = []
    classification_rows: list[dict[str, Any]] = []
    global_warnings: list[str] = []
    for s in scenarios_in:
        if not isinstance(s, dict):
            continue
        sid = str(s.get("scenario_id") or "unknown")
        st = str(s.get("scenario_type") or "unknown")
        upstream_classification = str(s.get("classification") or "insufficient_data")
        rt, raw, monthly_eq, ep_loss, shock_ret, ret_warnings = _return_type_and_values(s)
        a_orig, a_monthly, a_warn = _covariances_for_view(s, "asset_covariance")
        f_orig, f_monthly, f_warn = _covariances_for_view(s, "factor_covariance")
        base_mu_info: dict[str, Any] | None = None
        optimization_frequency = "monthly_equivalent"
        pipeline_note = str(returns_frequency_pipeline or scenario_library.get("returns_frequency") or "")
        scaling_note = str(s.get("scaling_note") or "")
        if sid == "base_historical":
            base_mu_info = _compute_base_monthly_mu(
                asset_cov_monthly=a_monthly,
                monthly_returns=monthly_returns,
                weights=weights,
                tickers=tickers,
                optimizer_mu_by_ticker=optimizer_mu_by_ticker,
            )
            optimization_frequency = "monthly"
            if pipeline_note and pipeline_note != "monthly":
                scaling_note = (
                    f"{scaling_note}; normalized_optimization_slice_frequency=monthly; "
                    f"pipeline_returns_frequency_disclosure={pipeline_note} "
                    f"(weekly factor regression/shocks unchanged elsewhere)"
                )
            else:
                scaling_note = (
                    f"{scaling_note}; normalized_optimization_slice_frequency=monthly"
                )
            pm = base_mu_info.get("portfolio_expected_return_monthly")
            method = base_mu_info.get("expected_return_method")
            if pm is not None and method:
                rt = "monthly_expected_return"
                raw = float(pm)
                monthly_eq = float(pm)
                ret_warnings = [x for x in ret_warnings if "monthly_expected_return_unavailable" not in x]
        historical_fallback_meta: dict[str, Any] | None = None
        scenario_asset_returns_dict: dict[str, float] | None = None
        ep_loss_eff = ep_loss
        if (
            st == "historical_stress"
            and enable_historical_stress_fallback
            and monthly_returns is not None
            and not monthly_returns.empty
        ):
            win = episode_window_for_scenario(sid)
            rtickers = [str(t) for t in (tickers or [])]
            if cash_proxy_ticker:
                cpu = str(cash_proxy_ticker).strip().upper()
                rtickers = [t for t in rtickers if str(t).strip().upper() != cpu]
            if not rtickers and isinstance(a_monthly, dict) and a_monthly:
                rtickers = sorted({str(k) for k in a_monthly.keys()})
            if win and rtickers:
                cfg_m = merge_proxy_config(None, historical_stress_proxy_config)
                ep_end = pd.Timestamp(win[1])
                fr_for_hist = factor_returns_weekly
                if (
                    factor_returns_weekly_episode_loose is not None
                    and not factor_returns_weekly_episode_loose.empty
                    and ep_end < _FACTOR_SHOCK_LOOSE_EPISODE_END_BEFORE
                ):
                    fr_for_hist = factor_returns_weekly_episode_loose
                rd, historical_fallback_meta = build_historical_episode_asset_returns(
                    scenario_id=sid,
                    episode_start=win[0],
                    episode_end=win[1],
                    risk_tickers=rtickers,
                    monthly_returns=monthly_returns,
                    stress_report=stress_report,
                    proxy_config=cfg_m,
                    factor_returns_weekly=fr_for_hist,
                )
                scenario_asset_returns_dict = rd if rd else None
                if rd and weights:
                    ep_fb = sum(float(weights.get(t, 0.0)) * float(rd[t]) for t in rd if t in weights)
                    if ep_loss_eff is None or not np.isfinite(float(ep_loss_eff)):
                        ep_loss_eff = ep_fb
        if rt == "historical_episode_loss":
            scaling_note = f"{scaling_note}; historical stress kept as episode_loss (no synthetic monthly mu conversion)"
            optimization_frequency = "episode_plus_monthly_equivalent_covariances"
        elif rt == "synthetic_one_time_shock":
            scaling_note = f"{scaling_note}; synthetic stress kept as one_time_shock (no synthetic monthly mu conversion)"
            optimization_frequency = "one_time_shock_plus_monthly_equivalent_covariances"
        all_warnings = list(s.get("warnings") or []) + ret_warnings + a_warn + f_warn
        if historical_fallback_meta:
            all_warnings.extend([str(w) for w in (historical_fallback_meta.get("warnings") or [])])
        if sid == "base_historical" and pipeline_note and pipeline_note != "monthly":
            all_warnings.append(
                "normalized_view_pipeline_frequency_note_only_not_merged_into_monthly_sigma"
            )
        cls_norm, cls_suffix = _normalized_classification(
            sid=sid,
            st=st,
            s_raw=s,
            rt=rt,
            shock_ret=shock_ret,
            ep_loss=ep_loss_eff,
            a_monthly=a_monthly,
            f_monthly=f_monthly,
            base_mu_info=base_mu_info,
            pipeline_returns_frequency=pipeline_note or None,
            historical_fallback_meta=historical_fallback_meta,
        )
        classification = cls_norm
        beta_frequency = "weekly" if st in {"base", "synthetic_stress", "historical_stress"} else "daily_or_monthly"
        confidence_weight = _confidence_for_classification(classification, all_warnings)
        optimization_role = _optimization_role(st, classification)
        usable = classification in {"ready_for_optimization", "usable_with_caution"}
        reason = _reason_for_classification(classification, all_warnings, cls_suffix)
        if a_orig is None:
            missing_rows.append({"scenario_id": sid, "missing_field": "asset_covariance_original"})
        if f_orig is None:
            missing_rows.append({"scenario_id": sid, "missing_field": "factor_covariance_original"})
        if s.get("factor_betas") in (None, {}, []):
            missing_rows.append({"scenario_id": sid, "missing_field": "factor_betas_used"})
        if rt == "unavailable":
            missing_rows.append({"scenario_id": sid, "missing_field": "scenario_return_type_source"})
        for w in all_warnings:
            warning_rows.append({"scenario_id": sid, "warning": str(w)})
        row: dict[str, Any] = {
            "scenario_id": sid,
            "scenario_type": st,
            "upstream_classification": upstream_classification,
            "original_frequency": str(s.get("frequency") or "unknown"),
            "optimization_frequency": optimization_frequency,
            "pipeline_returns_frequency_note": pipeline_note or None,
            "normalized_frequency": optimization_frequency,
            "scaling_note": scaling_note,
            "scenario_return_type": rt,
            "scenario_return_raw": raw,
            "scenario_return_monthly_equivalent": monthly_eq,
            "scenario_episode_loss": ep_loss_eff,
            "scenario_shock_return": shock_ret,
            "asset_covariance_original": a_orig,
            "asset_covariance_monthly_equivalent": a_monthly,
            "factor_covariance_original": f_orig,
            "factor_covariance_monthly_equivalent": f_monthly,
            "factor_betas_used": s.get("factor_betas") or {},
            "beta_frequency": beta_frequency,
            "asset_rc": s.get("asset_rc"),
            "factor_rc": s.get("factor_rc"),
            "scenario_factor_move": s.get("scenario_factor_move"),
            "quality_status": s.get("quality_status"),
            "confidence_weight": confidence_weight,
            "optimization_role": optimization_role,
            "usable_for_optimization": bool(usable),
            "classification": classification,
            "reason_for_classification": reason,
            "warnings": all_warnings,
        }
        if scenario_asset_returns_dict:
            row["scenario_asset_return"] = dict(scenario_asset_returns_dict)
        if historical_fallback_meta is not None:
            row["historical_stress_metadata"] = dict(historical_fallback_meta)
        if sid == "base_historical":
            row["expected_return_method"] = (base_mu_info or {}).get("expected_return_method")
            row["expected_returns_by_asset"] = (base_mu_info or {}).get("expected_returns_by_asset")
            row["portfolio_expected_return_monthly"] = (base_mu_info or {}).get("portfolio_expected_return_monthly")
            row["asset_universe_optimization"] = (base_mu_info or {}).get("asset_universe_optimization")
            row["base_mu_n_obs"] = (base_mu_info or {}).get("base_mu_n_obs")
            row["scenario_risk_monthly"] = (s.get("scenario_risk") or {}).get("portfolio_sigma_monthly")
            row["scenario_risk_annual"] = (s.get("scenario_risk") or {}).get("portfolio_sigma_annual")
        scenarios_out.append(row)
        classification_rows.append(
            {
                "scenario_id": sid,
                "scenario_type": st,
                "upstream_classification": upstream_classification,
                "classification": classification,
                "confidence_weight": confidence_weight,
                "optimization_role": optimization_role,
                "usable_for_optimization": bool(usable),
                "reason_for_classification": reason,
            }
        )
    summary_rows = [
        {
            "scenario_id": s["scenario_id"],
            "scenario_type": s["scenario_type"],
            "original_frequency": s["original_frequency"],
            "optimization_frequency": s["optimization_frequency"],
            "normalized_frequency": s["normalized_frequency"],
            "scenario_return_type": s["scenario_return_type"],
            "quality_status": s["quality_status"],
            "upstream_classification": s.get("upstream_classification"),
            "classification": s["classification"],
            "confidence_weight": s["confidence_weight"],
            "optimization_role": s["optimization_role"],
            "usable_for_optimization": s["usable_for_optimization"],
        }
        for s in scenarios_out
    ]
    paths: dict[str, str] = {}
    readiness_roles = summarize_normalized_roles(scenarios_out)
    out = {
        "version": SCENARIO_LIBRARY_NORMALIZED_VERSION,
        "n_scenarios": len(scenarios_out),
        "scenarios": scenarios_out,
        "global_warnings": global_warnings,
        "readiness_roles": readiness_roles,
        "monte_carlo_feasibility_note": (
            "Monte Carlo feasibility requires sampling/model choices not implemented here; "
            "normalized layer supplies consistent monthly Σ and typed scenario shocks where classified usable."
        ),
        "robust_optimization_note": (
            "Robust optimization needs explicit uncertainty sets / constraint semantics beyond this export; "
            "use scenarios tagged hard_stress_constraint or soft_constraint plus objective_input base when ready."
        ),
    }
    if output_dir_final is not None:
        final_dir = Path(output_dir_final)
        final_dir.mkdir(parents=True, exist_ok=True)
        p = final_dir / "scenario_library_normalized.json"
        p.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        paths["scenario_library_normalized.json"] = str(p)
    if output_dir_csv is not None:
        csv_dir = Path(output_dir_csv)
        csv_dir.mkdir(parents=True, exist_ok=True)
        p1 = csv_dir / "scenario_library_normalized_summary.csv"
        pd.DataFrame(summary_rows).to_csv(p1, index=False)
        paths["scenario_library_normalized_summary.csv"] = str(p1)
        p2 = csv_dir / "scenario_library_normalized_missing_inputs.csv"
        pd.DataFrame(missing_rows).to_csv(p2, index=False)
        paths["scenario_library_normalized_missing_inputs.csv"] = str(p2)
        p3 = csv_dir / "scenario_library_normalized_warnings.csv"
        pd.DataFrame(warning_rows).to_csv(p3, index=False)
        paths["scenario_library_normalized_warnings.csv"] = str(p3)
        p4 = csv_dir / "scenario_library_normalized_classification.csv"
        pd.DataFrame(classification_rows).to_csv(p4, index=False)
        paths["scenario_library_normalized_classification.csv"] = str(p4)
    out["output_paths"] = paths
    return out


__all__ = [
    "SCENARIO_LIBRARY_NORMALIZED_VERSION",
    "build_scenario_library_normalized",
    "summarize_normalized_classifications",
    "summarize_normalized_roles",
]
