"""
Scenario Library v1 — unified, normalized scenario inputs for future robust optimization.

Collects base / macro-regime / stress layers from ``stress_report`` and related payloads.
Does **not** run optimization, change mandate gates, or alter stress pass/fail. See
``build_scenario_library`` docstring for normalization rules.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.risk_contrib import cov_matrix_monthly
from src.stress_covariance_taxonomy import stress_covariance_taxonomy_blend
from src.stress_factors_macro import MACRO_PRIMARY_REGIME_NAMES
import src.stress_scenario_analytics as _ssa

SCENARIO_LIBRARY_VERSION = "scenario_library_v1"

WEEKLY_TO_MONTHLY_VARIANCE_FACTOR = 12.0 / 52.0
DAILY_ANNUAL_TO_MONTHLY_COV_FACTOR = 1.0 / 12.0

# Block 3.1.2 — fixed active synthetic scenario IDs (Stress Test Lab Scenario Library).
# Must match SCENARIOS + recession_severe in src/stress.py run_stress. Do not extend without
# docs/specs/stress_lab_layer_spec.md §3.1 and DECISIONS.md.
SYNTHETIC_SCENARIO_IDS: tuple[str, ...] = (
    "equity_shock",
    "credit_shock",
    "rates_shock",
    "inflation_stagflation",
    "liquidity_shock",
    "usd_shock",
    "commodity_shock",
    "recession_severe",
)
# Block 3.1.1 — fixed active historical scenario IDs (Stress Test Lab Scenario Library).
# Must match HISTORICAL_EPISODES in src/stress.py. Do not extend without
# docs/specs/stress_lab_layer_spec.md §3.1 and DECISIONS.md.
HISTORICAL_SCENARIO_IDS: tuple[str, ...] = ("dotcom", "2008", "2020", "2022", "banking_2023")


def _nested_cov_from_df(cov: pd.DataFrame) -> dict[str, dict[str, float]]:
    cov = cov.fillna(0.0)
    out: dict[str, dict[str, float]] = {}
    for ri in cov.index:
        row: dict[str, float] = {}
        for cj in cov.columns:
            row[str(cj)] = float(cov.loc[ri, cj])
        out[str(ri)] = row
    return out


def _scale_nested_cov(nested: dict[str, dict[str, float]], factor: float) -> dict[str, dict[str, float]]:
    scaled: dict[str, dict[str, float]] = {}
    for ki, row in nested.items():
        scaled[ki] = {kj: float(v) * factor for kj, v in (row or {}).items()}
    return scaled


def _beta_map_for_library(stress_report: dict[str, Any]) -> dict[str, Any]:
    return dict(stress_report.get("factor_betas_5y") or stress_report.get("factor_betas") or {})


def _portfolio_sigma_monthly(w: np.ndarray, cov: pd.DataFrame, assets: list[str]) -> float | None:
    if cov is None or cov.empty:
        return None
    c = cov.reindex(index=assets, columns=assets).fillna(0.0).values.astype(float)
    if c.size == 0 or len(w) != c.shape[0]:
        return None
    v = float(w.T @ c @ w)
    if v < 0 and v > -1e-12:
        v = 0.0
    return float(np.sqrt(max(v, 0.0)))


def _weights_vector(weights: dict[str, float], assets: list[str]) -> np.ndarray:
    w = np.array([float(weights.get(t, 0.0)) for t in assets], dtype=float)
    s = float(w.sum())
    if s > 0:
        w = w / s
    return w


def _quality_tier(q: str | None) -> str:
    s = (q or "").strip().lower()
    if s in {"reliable", "usable", "low_confidence", "insufficient_data"}:
        return s
    if s in {"no_observations"}:
        return "insufficient_data"
    return "insufficient_data"


def _confidence_weight_for_quality(tier: str) -> float:
    return {"reliable": 1.0, "usable": 0.75, "low_confidence": 0.25, "insufficient_data": 0.0}.get(
        tier, 0.0
    )


def _classify_scenario(
    *,
    tier: str,
    not_for_optimization: bool,
    suitable_robust: bool | None,
    has_asset_cov: bool,
    has_factor_cov: bool,
    frequency_conflict: bool,
    critical_missing: bool,
) -> str:
    if critical_missing or tier == "insufficient_data":
        return "insufficient_data"
    if frequency_conflict or not_for_optimization:
        return "diagnostic_only"
    if tier == "low_confidence":
        return "diagnostic_only"
    if suitable_robust is True and tier in {"reliable", "usable"} and has_asset_cov and has_factor_cov:
        return "ready_for_optimization"
    if tier in {"reliable", "usable"}:
        return "usable_with_caution"
    return "diagnostic_only"


def _usable_for_opt_flag(classification: str) -> bool:
    return classification == "ready_for_optimization"


_QUALITY_ORDER = ("insufficient_data", "low_confidence", "usable", "reliable")


def _worst_quality_tier(a: str, b: str) -> str:
    ia = _QUALITY_ORDER.index(a) if a in _QUALITY_ORDER else 0
    ib = _QUALITY_ORDER.index(b) if b in _QUALITY_ORDER else 0
    return _QUALITY_ORDER[min(ia, ib)]


def build_scenario_library(
    stress_report: dict[str, Any],
    *,
    weights: dict[str, float],
    tickers: list[str],
    monthly_returns: pd.DataFrame,
    returns_frequency: str = "monthly",
    analysis_end_str: str | None = None,
    regime_factor_analytics_full: dict[str, Any] | None = None,
    factor_returns_weekly: pd.DataFrame | None = None,
    cash_proxy_ticker: str | None = None,
    shock_scale_alpha: float = _ssa.SHOCK_SCALE_ALPHA_DEFAULT,
    output_dir_final: str | Path | None = None,
    output_dir_csv: str | Path | None = None,
) -> dict[str, Any]:
    """
    Assemble Scenario Library v1 from existing report payloads.

    Normalization (v1):
    - **Monthly** asset covariance for the base layer from overlapping monthly returns.
    - **Weekly** factor covariance from ``factor_covariance.base`` scaled to a **monthly-equivalent**
      covariance via ``Σ_m ≈ Σ_w * (12/52)`` (variance scaling for i.i.d.-style approximation;
      documented in ``scaling_note``).
    - **Regime (daily)** asset/factor covariances stored as annualized daily covariance are converted
      to monthly-equivalent via ``Σ_m ≈ Σ_annual / 12`` when ``covariance_scaled_to_annual`` is true.
    - If full regime payload is missing (stress_report stores slim regime blocks without matrices),
      regime scenarios are retained with **insufficient_data** / **diagnostic_only** and warnings.
    - Stress scenario dense matrices are recomputed using the same helpers as
      ``build_stress_scenario_analytics`` (taxonomy blend asset Σ, shock-scale factor Σ).
    """
    from src.windows import truncate_to_analysis_end

    warnings_global: list[str] = []
    scenarios: list[dict[str, Any]] = []
    missing_rows: list[dict[str, str]] = []
    warn_rows: list[dict[str, str]] = []

    ae = analysis_end_str
    if ae is None:
        fc_block_ae = stress_report.get("factor_covariance") or {}
        base_win_ae = ((fc_block_ae.get("base") or {}).get("window")) if isinstance(fc_block_ae, dict) else None
        if isinstance(base_win_ae, dict) and base_win_ae.get("analysis_end"):
            ae = str(base_win_ae["analysis_end"])

    monthly_eff = monthly_returns
    if ae:
        monthly_eff = truncate_to_analysis_end(monthly_returns, ae)
    factor_weekly_eff = factor_returns_weekly
    if ae and factor_returns_weekly is not None and not factor_returns_weekly.empty:
        factor_weekly_eff = truncate_to_analysis_end(factor_returns_weekly, ae)

    asset_cols = [t for t in tickers if t in monthly_eff.columns]
    returns_all = monthly_eff[asset_cols].copy()
    returns_all.index = pd.to_datetime(returns_all.index).tz_localize(None)
    w_vec = _weights_vector(weights, asset_cols)

    fc_block = stress_report.get("factor_covariance") or {}
    base_nested = ((fc_block.get("base") or {}).get("matrix")) if isinstance(fc_block, dict) else None
    factor_cov_weekly_df = _ssa._nested_cov_to_df(base_nested if isinstance(base_nested, dict) else None)
    factor_cov_monthly_nested = _scale_nested_cov(
        _nested_cov_from_df(factor_cov_weekly_df),
        WEEKLY_TO_MONTHLY_VARIANCE_FACTOR,
    )

    base_cov_m = cov_matrix_monthly(returns_all.dropna(how="all"), ddof=1)
    base_cov_m = base_cov_m.reindex(index=asset_cols, columns=asset_cols).fillna(0.0)
    n_m_base = int(len(returns_all.dropna(how="all")))
    q_base_asset = _ssa.quality_status_from_n_months(float(n_m_base))

    pf_rc_base = ((fc_block.get("portfolio_factor_rc") or {}).get("base")) or []

    base_sig = _portfolio_sigma_monthly(w_vec, base_cov_m, asset_cols)
    base_scen: dict[str, Any] = {
        "scenario_id": "base_historical",
        "scenario_type": "base",
        "frequency": "monthly",
        "scaling_note": (
            "asset_covariance: monthly simple returns ddof=1; "
            "factor_covariance: weekly factor window scaled to monthly-equivalent via Σ_m≈Σ_w*(12/52)"
        ),
        "asset_covariance": {
            "native_frequency": "monthly",
            "normalized_frequency": "monthly",
            "matrix": _nested_cov_from_df(base_cov_m),
            "n_obs": n_m_base,
            "quality_status": q_base_asset,
        },
        "factor_covariance": {
            "native_frequency": "weekly",
            "normalized_frequency": "monthly_equivalent",
            "matrix": factor_cov_monthly_nested,
            "n_obs": int((fc_block.get("base") or {}).get("n_obs") or 0),
            "quality_status": _ssa.quality_status_from_n_months(
                _ssa._month_equiv_from_weekly(int((fc_block.get("base") or {}).get("n_obs") or 0))
            )
            if (fc_block.get("base") or {}).get("n_obs")
            else "insufficient_data",
        },
        "factor_betas": _beta_map_for_library(stress_report),
        "scenario_factor_move": None,
        "scenario_asset_return": None,
        "scenario_portfolio_return": None,
        "scenario_risk": {
            "portfolio_sigma_monthly": base_sig,
            "portfolio_sigma_annual": float(base_sig * np.sqrt(12)) if base_sig is not None else None,
            "basis": "monthly_return_std_of_buy_hold_weights",
        },
        "scenario_drawdown_proxy": None,
        "asset_rc": None,
        "factor_rc": pf_rc_base,
        "quality_status": q_base_asset,
        "confidence_weight": _confidence_weight_for_quality(_quality_tier(q_base_asset)),
        "usable_for_optimization": False,
        "warnings": [],
        "classification": "usable_with_caution",
        "raw_vs_shrinkage": None,
    }
    base_tier = _quality_tier(q_base_asset)
    base_class = _classify_scenario(
        tier=base_tier,
        not_for_optimization=False,
        suitable_robust=None,
        has_asset_cov=True,
        has_factor_cov=bool((fc_block.get("base") or {}).get("matrix")),
        frequency_conflict=returns_frequency != "monthly",
        critical_missing=not bool((fc_block.get("base") or {}).get("matrix")),
    )
    if returns_frequency != "monthly":
        base_scen["warnings"].append(
            f"returns_frequency={returns_frequency}_mixed_cadence_with_weekly_factor_pipeline"
        )
        warnings_global.append("base_layer_frequency_not_monthly")
    if not (fc_block.get("base") or {}).get("matrix"):
        missing_rows.append({"scenario_id": "base_historical", "missing_field": "factor_covariance.base.matrix"})
    base_scen["classification"] = base_class
    base_scen["usable_for_optimization"] = _usable_for_opt_flag(base_class)
    scenarios.append(base_scen)

    # --- Macro regimes (require full payload for matrices) ---
    rfa = regime_factor_analytics_full if isinstance(regime_factor_analytics_full, dict) else None
    if rfa is None:
        warnings_global.append("macro_regime_covariance_payload_unavailable_for_scenario_library")
    regimes_payload = (rfa or {}).get("regimes") or {}
    rfa_freq = str((rfa or {}).get("frequency") or "unknown")

    for regime in MACRO_PRIMARY_REGIME_NAMES:
        block = regimes_payload.get(regime) if isinstance(regimes_payload, dict) else None
        if not isinstance(block, dict):
            block = {}
        qc = block.get("quality_status") or "no_observations"
        tier = _quality_tier(str(qc))
        nfo = bool(block.get("not_for_optimization", True))
        asset_cb = block.get("asset_covariance") if isinstance(block.get("asset_covariance"), dict) else {}
        factor_cb = block.get("factor_covariance") if isinstance(block.get("factor_covariance"), dict) else {}
        asset_nested_raw = asset_cb.get("covariance")
        factor_nested_raw = factor_cb.get("covariance")
        ann = bool(block.get("covariance_scaled_to_annual"))
        freq_conflict = rfa_freq == "daily" and ann

        asset_nested_norm: dict[str, dict[str, float]] | None = None
        factor_nested_norm: dict[str, dict[str, float]] | None = None
        scaling_note = f"regime analytics_frequency={rfa_freq}; regime labels monthly"

        if rfa is None or not asset_nested_raw:
            scaling_note += "; full regime payload missing — covariance not populated"
        elif isinstance(asset_nested_raw, dict):
            asset_nested_norm = dict(asset_nested_raw)  # copy
            if ann and rfa_freq == "daily":
                asset_nested_norm = _scale_nested_cov(asset_nested_norm, DAILY_ANNUAL_TO_MONTHLY_COV_FACTOR)
                scaling_note += (
                    "; asset covariance converted from daily-annualized to monthly-equivalent via Σ_m≈Σ_ann/12"
                )
            elif rfa_freq == "weekly":
                asset_nested_norm = _scale_nested_cov(asset_nested_norm, WEEKLY_TO_MONTHLY_VARIANCE_FACTOR)
                scaling_note += "; asset covariance weekly→monthly-equivalent via Σ_m≈Σ_w*(12/52)"
            else:
                scaling_note += "; asset covariance left native (monthly regime path)"

        if rfa is None or not factor_nested_raw:
            pass
        elif isinstance(factor_nested_raw, dict):
            factor_nested_norm = dict(factor_nested_raw)
            if ann and rfa_freq == "daily":
                factor_nested_norm = _scale_nested_cov(factor_nested_norm, DAILY_ANNUAL_TO_MONTHLY_COV_FACTOR)
                scaling_note += (
                    "; factor covariance converted from daily-annualized to monthly-equivalent via Σ_m≈Σ_ann/12"
                )
            elif rfa_freq == "weekly":
                factor_nested_norm = _scale_nested_cov(factor_nested_norm, WEEKLY_TO_MONTHLY_VARIANCE_FACTOR)
                scaling_note += "; factor covariance weekly→monthly-equivalent"

        pexp = block.get("portfolio_factor_exposure") or {}
        betas_reg = (pexp.get("betas") if isinstance(pexp, dict) else None) or {}

        fac_moves = block.get("factor_average_moves") or []

        scen_risk = None
        acv = block.get("asset_covariance") or {}
        if isinstance(acv, dict) and asset_nested_norm:
            try:
                assets_order = list(acv.get("assets") or [])
                if assets_order:
                    cov_df = pd.DataFrame(asset_nested_norm).reindex(index=assets_order, columns=assets_order).astype(float)
                    wr = np.array([float(weights.get(a, 0.0)) for a in assets_order], dtype=float)
                    swr = float(wr.sum())
                    if swr > 0:
                        wr = wr / swr
                    sm = _portfolio_sigma_monthly(wr, cov_df, assets_order)
                    scen_risk = {
                        "portfolio_sigma_monthly": sm,
                        "portfolio_sigma_annual": float(sm * np.sqrt(12)) if sm is not None else None,
                        "basis": "regime_slice_asset_covariance",
                    }
            except Exception as exc:
                warn_rows.append({"scenario_id": regime, "warning_code": "regime_sigma_failed", "message": str(exc)})

        reg_scen = {
            "scenario_id": regime,
            "scenario_type": "macro_regime",
            "frequency": rfa_freq if rfa else "unknown",
            "scaling_note": scaling_note,
            "asset_covariance": (
                {
                    "native_frequency": rfa_freq,
                    "normalized_frequency": "monthly_equivalent" if asset_nested_norm else None,
                    "matrix": asset_nested_norm,
                    "n_obs": int(block.get("n_obs", 0) or 0),
                    "quality_status": str(qc),
                }
                if asset_nested_norm
                else None
            ),
            "factor_covariance": (
                {
                    "native_frequency": rfa_freq,
                    "normalized_frequency": "monthly_equivalent" if factor_nested_norm else None,
                    "matrix": factor_nested_norm,
                    "n_obs": int(block.get("n_obs", 0) or 0),
                    "quality_status": str(qc),
                }
                if factor_nested_norm
                else None
            ),
            "factor_betas": betas_reg,
            "scenario_factor_move": fac_moves,
            "scenario_asset_return": None,
            "scenario_portfolio_return": None,
            "scenario_risk": scen_risk,
            "scenario_drawdown_proxy": (block.get("portfolio_daily_risk_metrics") or {}).get("max_drawdown")
            if isinstance(block.get("portfolio_daily_risk_metrics"), dict)
            else None,
            "asset_rc": None,
            "factor_rc": block.get("factor_variance_contribution"),
            "quality_status": str(qc),
            "confidence_weight": _confidence_weight_for_quality(tier),
            "usable_for_optimization": False,
            "warnings": list(block.get("warnings") or []),
            "classification": "diagnostic_only",
            "raw_vs_shrinkage": None,
        }
        if rfa is None:
            missing_rows.append({"scenario_id": regime, "missing_field": "macro_regime_covariance_payload"})
        if not asset_nested_raw:
            missing_rows.append({"scenario_id": regime, "missing_field": "asset_covariance.matrix"})
        if not factor_nested_raw:
            missing_rows.append({"scenario_id": regime, "missing_field": "factor_covariance.matrix"})

        cl = _classify_scenario(
            tier=tier,
            not_for_optimization=nfo or rfa is None,
            suitable_robust=None,
            has_asset_cov=bool(asset_nested_norm),
            has_factor_cov=bool(factor_nested_norm),
            frequency_conflict=freq_conflict,
            critical_missing=rfa is None,
        )
        if nfo:
            reg_scen["warnings"].append("not_for_optimization_true_in_regime_analytics")
        reg_scen["classification"] = cl
        reg_scen["usable_for_optimization"] = _usable_for_opt_flag(cl)
        scenarios.append(reg_scen)

    # --- Stress layer: reuse SSA helpers for dense matrices ---
    by_sid = {str(r.get("scenario_id")): r for r in (stress_report.get("scenario_results") or []) if isinstance(r, dict)}
    hist_by = {str(h.get("episode")): h for h in (stress_report.get("historical_results") or []) if isinstance(h, dict)}
    ssa_block = stress_report.get("stress_scenario_analytics") or {}
    ssa_scenarios = (ssa_block.get("scenarios") or {}) if isinstance(ssa_block, dict) else {}

    adj_overlay = stress_report.get("synthetic_factor_pnl_adjusted") or {}
    adj_by_sid = {
        str(r.get("scenario_id")): r
        for r in (adj_overlay.get("scenarios") or [])
        if isinstance(r, dict) and r.get("scenario_id")
    }

    betas_5y = stress_report.get("factor_betas_5y") or stress_report.get("factor_betas") or {}
    fb_adj = (stress_report.get("factor_betas_adjusted") or {}).get("adjusted") or {}

    def _append_stress_row(
        sid: str,
        stype: str,
        *,
        shock: dict[str, Any],
        pnl_raw: float | None,
        pnl_adj: float | None,
        actual_pnl: float | None,
        model_pnl: float | None,
        meta_ssa: dict[str, Any],
    ) -> None:
        sub_m_hist: pd.DataFrame | None = None
        try:
            if stype == "synthetic":
                cov_stress, _ = stress_covariance_taxonomy_blend(
                    base_cov_m, asset_cols, sid, cash_proxy_ticker=cash_proxy_ticker
                )
            else:
                sub_m_hist = returns_all.loc[str(meta_ssa.get("data_start", "")) : str(meta_ssa.get("data_end", ""))]
                sub_m_hist = sub_m_hist.dropna(how="all")
                cov_stress, _, _ = _ssa._cov_from_returns_sample(sub_m_hist, shrinkage=False)
                cov_stress = cov_stress.reindex(index=asset_cols, columns=asset_cols).fillna(0.0)
        except Exception as exc:
            warn_rows.append({"scenario_id": sid, "warning_code": "stress_asset_cov_rebuild_failed", "message": str(exc)})
            cov_stress = base_cov_m.copy()

        if stype == "synthetic":
            fac_w_m, fac_meta = _ssa._shock_scale_factor_cov(
                factor_cov_weekly_df, shock, alpha=shock_scale_alpha
            )
        else:
            start = str(meta_ssa.get("data_start", ""))
            end = str(meta_ssa.get("data_end", ""))
            fac_w_m, fac_meta = _ssa._factor_cov_episode(
                factor_weekly_eff,
                start,
                end,
                fallback_base=factor_cov_weekly_df,
                use_shrinkage=True,
            )
        fac_w_m_norm = _scale_nested_cov(_nested_cov_from_df(fac_w_m), WEEKLY_TO_MONTHLY_VARIANCE_FACTOR)

        ac_meta = meta_ssa.get("asset_covariance") if isinstance(meta_ssa.get("asset_covariance"), dict) else {}
        if stype == "historical" and sub_m_hist is not None:
            n_obs_a = int(len(sub_m_hist))
            q_ast = _ssa.quality_status_from_n_months(float(n_obs_a))
        elif isinstance(ac_meta, dict) and ac_meta.get("n_obs") is not None:
            q_ast = str(
                ac_meta.get("quality_status")
                or _ssa.quality_status_from_n_months(float(ac_meta.get("n_obs", 0)))
            )
            n_obs_a = int(ac_meta.get("n_obs") or 0)
        else:
            n_obs_a = int(n_m_base)
            q_ast = str(meta_ssa.get("quality_status") or _ssa.quality_status_from_n_months(float(n_obs_a)))
        tier_a = _quality_tier(q_ast)

        fac_q = str(fac_meta.get("quality_status") or "insufficient_data")
        tier_fac = _quality_tier(fac_q)
        tier_effective = _worst_quality_tier(tier_a, tier_fac)

        suitable = meta_ssa.get("suitable_robust_optimization_input")

        scen_sigma = _portfolio_sigma_monthly(w_vec, cov_stress, asset_cols)
        port_ret = pnl_raw if stype == "synthetic" else actual_pnl

        raw_vs = {
            "pnl_raw": pnl_raw,
            "pnl_shrinkage_adjusted": pnl_adj,
            "actual_realized_historical": actual_pnl,
            "model_explained": model_pnl,
            "note": "historical PnL is realized and not shrinkage-adjusted per stress spec"
            if stype == "historical"
            else "synthetic PnL is factor model; optional adjusted overlay separate",
        }

        wlist = list(meta_ssa.get("warnings") or [])

        has_fac_cov = tier_fac != "insufficient_data" and bool(fac_w_m_norm)

        cl = _classify_scenario(
            tier=tier_effective,
            not_for_optimization=False,
            suitable_robust=bool(suitable) if suitable is not None else False,
            has_asset_cov=True,
            has_factor_cov=has_fac_cov,
            frequency_conflict=False,
            critical_missing=tier_effective == "insufficient_data",
        )

        scen: dict[str, Any] = {
            "scenario_id": sid,
            "scenario_type": "synthetic_stress" if stype == "synthetic" else "historical_stress",
            "frequency": "monthly" if stype == "synthetic" else "episode",
            "scaling_note": (
                f"synthetic: asset Σ monthly (taxonomy_blend); factor Σ weekly shock-scaled then monthly-equivalent; "
                if stype == "synthetic"
                else "historical: asset Σ from episode monthly returns; factor Σ from weekly episode sample "
                "scaled to monthly-equivalent"
            ),
            "asset_covariance": {
                "native_frequency": "monthly",
                "normalized_frequency": "monthly",
                "matrix": _nested_cov_from_df(cov_stress),
                "n_obs": n_obs_a,
                "quality_status": q_ast,
            },
            "factor_covariance": {
                "native_frequency": "weekly",
                "normalized_frequency": "monthly_equivalent",
                "matrix": fac_w_m_norm,
                "factor_covariance_method": fac_meta.get("factor_covariance_method"),
                "n_obs": int(fac_meta.get("n_obs", 0) or 0),
                "quality_status": fac_q,
            },
            "factor_betas": {"5y": betas_5y, "10y": stress_report.get("factor_betas_10y") or {}, "adjusted": fb_adj},
            "scenario_factor_move": shock if stype == "synthetic" else None,
            "scenario_asset_return": None,
            "scenario_portfolio_return": port_ret,
            "scenario_risk": {
                "portfolio_sigma_monthly": scen_sigma,
                "portfolio_sigma_annual": float(scen_sigma * np.sqrt(12)) if scen_sigma is not None else None,
                "basis": "stress_scenario_asset_covariance",
            },
            "scenario_drawdown_proxy": port_ret,
            "asset_rc": meta_ssa.get("top_asset_risk_contributors"),
            "factor_rc": meta_ssa.get("top_factor_risk_contributors"),
            "quality_status": tier_effective,
            "confidence_weight": _confidence_weight_for_quality(tier_effective),
            "usable_for_optimization": False,
            "warnings": wlist,
            "classification": cl,
            "raw_vs_shrinkage": raw_vs,
        }
        if stype == "synthetic":
            src_row = by_sid.get(sid) or {}
            if isinstance(src_row.get("synthetic_assumptions"), dict):
                scen["synthetic_assumptions"] = dict(src_row.get("synthetic_assumptions") or {})
        scen["usable_for_optimization"] = _usable_for_opt_flag(cl)
        scenarios.append(scen)

        for w in wlist:
            warn_rows.append({"scenario_id": sid, "warning_code": "from_stress_scenario_analytics", "message": str(w)})

    for sid in SYNTHETIC_SCENARIO_IDS:
        srow = by_sid.get(sid)
        if not isinstance(srow, dict):
            missing_rows.append({"scenario_id": sid, "missing_field": "scenario_results row"})
            continue
        shock = srow.get("shock_vector") or {}
        adj_row = adj_by_sid.get(sid, {})
        pnl_reported = srow.get("portfolio_pnl_pct")
        pnl_raw_model = adj_row.get("pnl_model_raw")
        pnl_adj_model = adj_row.get("pnl_model_adjusted")
        pnl_raw: float | None = None
        if pnl_reported is not None:
            pnl_raw = float(pnl_reported)
        elif pnl_raw_model is not None:
            pnl_raw = float(pnl_raw_model)
        pnl_adj: float | None = float(pnl_adj_model) if pnl_adj_model is not None else None

        meta_ssa = ssa_scenarios.get(sid, {})
        if not meta_ssa:
            meta_ssa = {}
        _append_stress_row(
            sid,
            "synthetic",
            shock=dict(shock),
            pnl_raw=pnl_raw,
            pnl_adj=pnl_adj,
            actual_pnl=None,
            model_pnl=None,
            meta_ssa=meta_ssa if isinstance(meta_ssa, dict) else {},
        )

    for ep in HISTORICAL_SCENARIO_IDS:
        hrow = hist_by.get(ep)
        if not isinstance(hrow, dict):
            missing_rows.append({"scenario_id": ep, "missing_field": "historical_results episode"})
            continue
        meta_ssa = ssa_scenarios.get(ep, {})
        if not isinstance(meta_ssa, dict):
            meta_ssa = {}
        meta_ssa.setdefault("data_start", hrow.get("episode_start"))
        meta_ssa.setdefault("data_end", hrow.get("episode_end"))
        act = hrow.get("pnl_real_episode")
        mod = hrow.get("factor_model_pnl_pct")
        _append_stress_row(
            ep,
            "historical",
            shock={},
            pnl_raw=None,
            pnl_adj=None,
            actual_pnl=float(act) if act is not None and np.isfinite(float(act)) else None,
            model_pnl=float(mod) if mod is not None and np.isfinite(float(mod)) else None,
            meta_ssa=meta_ssa,
        )

    out: dict[str, Any] = {
        "version": SCENARIO_LIBRARY_VERSION,
        "returns_frequency": returns_frequency,
        "factor_stress_native_frequency": "weekly",
        "n_scenarios": len(scenarios),
        "scenarios": scenarios,
        "warnings_global": warnings_global,
    }

    summary_rows: list[dict[str, Any]] = []
    for s in scenarios:
        summary_rows.append(
            {
                "scenario_id": s.get("scenario_id"),
                "scenario_type": s.get("scenario_type"),
                "frequency": s.get("frequency"),
                "classification": s.get("classification"),
                "quality_status": s.get("quality_status"),
                "confidence_weight": s.get("confidence_weight"),
                "usable_for_optimization": s.get("usable_for_optimization"),
                "has_asset_cov_matrix": bool(s.get("asset_covariance") and (s.get("asset_covariance") or {}).get("matrix")),
                "has_factor_cov_matrix": bool(
                    s.get("factor_covariance") and (s.get("factor_covariance") or {}).get("matrix")
                ),
                "scenario_portfolio_return": s.get("scenario_portfolio_return"),
                "scenario_risk_annual": (s.get("scenario_risk") or {}).get("portfolio_sigma_annual")
                if isinstance(s.get("scenario_risk"), dict)
                else None,
                "scaling_note": (s.get("scaling_note") or "")[:500],
            }
        )

    paths: dict[str, str] = {}
    if output_dir_final is not None:
        p = Path(output_dir_final) / "scenario_library.json"
        p.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        paths["scenario_library.json"] = str(p)
    if output_dir_csv is not None:
        csv_dir = Path(output_dir_csv)
        csv_dir.mkdir(parents=True, exist_ok=True)
        sum_path = csv_dir / "scenario_library_summary.csv"
        pd.DataFrame(summary_rows).round(6).to_csv(sum_path, index=False)
        paths["scenario_library_summary.csv"] = str(sum_path)
        miss_path = csv_dir / "scenario_library_missing_inputs.csv"
        pd.DataFrame(missing_rows).to_csv(miss_path, index=False)
        paths["scenario_library_missing_inputs.csv"] = str(miss_path)
        wpath = csv_dir / "scenario_library_warnings.csv"
        pd.DataFrame(warn_rows).to_csv(wpath, index=False)
        paths["scenario_library_warnings.csv"] = str(wpath)

    out["output_paths"] = paths
    return out


def summarize_scenario_classifications(scenarios: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "ready_for_optimization": 0,
        "usable_with_caution": 0,
        "diagnostic_only": 0,
        "insufficient_data": 0,
    }
    for s in scenarios:
        c = str(s.get("classification") or "insufficient_data")
        if c in counts:
            counts[c] += 1
        else:
            counts["insufficient_data"] += 1
    return counts


__all__ = [
    "SCENARIO_LIBRARY_VERSION",
    "SYNTHETIC_SCENARIO_IDS",
    "HISTORICAL_SCENARIO_IDS",
    "build_scenario_library",
    "summarize_scenario_classifications",
]
