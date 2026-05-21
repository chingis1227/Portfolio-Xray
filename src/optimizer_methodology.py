"""Shared optimizer methodology disclosure helpers.

These helpers describe estimator choices that already happened elsewhere. They
must not compute weights, rebuild covariance matrices, or change optimizer
inputs.
"""
from __future__ import annotations

from typing import Any


COVARIANCE_METHODOLOGY_SCHEMA_VERSION = "optimizer_covariance_methodology_v1"
YOUNG_ETF_METHODOLOGY_SCHEMA_VERSION = "optimizer_young_etf_methodology_v1"


def _copy_policy(policy: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(policy, dict):
        return {}
    keys = (
        "enabled",
        "eligible_months",
        "candidate_months_min",
        "new_shrinkage_alpha",
        "candidate_alpha_min",
        "candidate_alpha_at_eligible",
        "max_weight_candidate_or_new_pct",
        "aggregate_candidate_new_warn_pct",
    )
    return {k: policy.get(k) for k in keys if k in policy}


def young_etf_methodology_disclosure(
    *,
    enabled: bool,
    role: str,
    mode: str | None = None,
    policy: dict[str, Any] | None = None,
    diagnostics: dict[str, Any] | None = None,
    per_ticker_caps: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Return machine-readable young-ETF policy disclosure."""
    diag = diagnostics if isinstance(diagnostics, dict) else {}
    tickers = diag.get("tickers") if isinstance(diag.get("tickers"), dict) else {}
    eligible_tickers = diag.get("eligible_tickers")
    if not isinstance(eligible_tickers, list):
        eligible_tickers = []
    out = {
        "schema_version": YOUNG_ETF_METHODOLOGY_SCHEMA_VERSION,
        "enabled": bool(enabled),
        "role": role,
        "mode": mode,
        "policy": _copy_policy(policy),
        "eligible_tickers": eligible_tickers,
        "ticker_buckets": tickers,
        "per_ticker_caps": dict(per_ticker_caps or {}),
        "fallback_reason": diag.get("reason"),
        "core_effective_months": diag.get("core_effective_months"),
    }
    out["human_summary"] = young_etf_methodology_summary(out)
    return out


def covariance_methodology_disclosure(
    *,
    method: Any,
    source: str | None,
    analysis_end: Any,
    window_months: Any,
    returns_panel_fingerprint: Any = None,
    shrinkage_enabled: Any = None,
    shrinkage_method: str | None = None,
    psd_repair_used: Any = None,
    psd_status: Any = None,
    young_etf: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return machine-readable covariance methodology disclosure."""
    method_text = str(method or "")
    young = young_etf if isinstance(young_etf, dict) else {}
    young_mode = young.get("mode")
    young_enabled = bool(young.get("enabled"))
    if young_enabled and young_mode == "dual_core_median_anchor":
        estimator = "young_etf_dual_covariance_core_pairwise_shrinkage"
        join_policy = "eligible_core_inner_join_plus_pairwise_overlaps_for_young_assets"
    elif young_enabled and young_mode == "fallback_full_inner_join":
        estimator = "young_etf_policy_fallback_full_inner_join"
        join_policy = "full_inner_join_complete_cases"
    elif "ledoit" in method_text.lower():
        estimator = "ledoit_wolf_shrinkage_covariance"
        join_policy = "inner_join_complete_cases"
    elif "oas" in method_text.lower():
        estimator = "oas_shrinkage_covariance"
        join_policy = "inner_join_complete_cases"
    else:
        estimator = "sample_covariance"
        join_policy = "inner_join_complete_cases"

    shrink = {
        "enabled": bool(shrinkage_enabled) if shrinkage_enabled is not None else None,
        "method": shrinkage_method,
    }
    if shrink["method"] is None:
        if "ledoit" in method_text.lower():
            shrink["method"] = "ledoit_wolf"
        elif "oas" in method_text.lower():
            shrink["method"] = "oas"
        elif young_enabled and young_mode == "dual_core_median_anchor":
            shrink["method"] = "young_asset_pairwise_shrinkage_to_core_median_anchor"

    out = {
        "schema_version": COVARIANCE_METHODOLOGY_SCHEMA_VERSION,
        "method": method,
        "source": source,
        "estimator": estimator,
        "return_frequency": "monthly_simple",
        "analysis_end": analysis_end,
        "window_months": window_months,
        "join_policy": join_policy,
        "ddof": 1,
        "shrinkage": shrink,
        "psd_repair": {
            "used": psd_repair_used,
            "status": psd_status,
        },
        "young_etf": young,
        "returns_panel_fingerprint": returns_panel_fingerprint,
        "does_not_change_formula": True,
    }
    out["human_summary"] = covariance_methodology_summary(out)
    return out


def young_etf_methodology_summary(young: dict[str, Any] | None) -> str:
    if not isinstance(young, dict) or not young.get("enabled"):
        return "Young ETF policy disabled or not used for this optimizer."
    role = young.get("role") or "optimization disclosure"
    mode = young.get("mode") or "not reported"
    caps = young.get("per_ticker_caps") or {}
    cap_text = f"; capped tickers={len(caps)}" if caps else "; no per-ticker young caps"
    reason = young.get("fallback_reason")
    reason_text = f"; fallback_reason={reason}" if reason else ""
    return f"Young ETF policy role={role}; mode={mode}{cap_text}{reason_text}."


def covariance_methodology_summary(covariance: dict[str, Any] | None) -> str:
    if not isinstance(covariance, dict):
        return "Covariance methodology unavailable."
    method = covariance.get("method") or covariance.get("estimator") or "not reported"
    join_policy = covariance.get("join_policy") or "not reported"
    shrink = covariance.get("shrinkage") if isinstance(covariance.get("shrinkage"), dict) else {}
    shrink_enabled = shrink.get("enabled")
    shrink_method = shrink.get("method") or "none"
    psd = covariance.get("psd_repair") if isinstance(covariance.get("psd_repair"), dict) else {}
    psd_used = psd.get("used")
    young = covariance.get("young_etf") if isinstance(covariance.get("young_etf"), dict) else {}
    young_text = "young ETF policy on" if young.get("enabled") else "young ETF policy off/not used"
    return (
        f"Covariance method={method}; join_policy={join_policy}; "
        f"shrinkage={shrink_enabled} ({shrink_method}); "
        f"psd_repair={psd_used}; {young_text}."
    )
