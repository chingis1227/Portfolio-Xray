"""
Stress scenario analytics v1 — diagnostic-only per-scenario risk and covariance stats.

Produces ``stress_report["stress_scenario_analytics"]`` and CSV exports under ``results_csv/``.
Does not change optimizer, mandate gates, or stress pass/fail. See docs/docs/stress_testing_spec.md §2.3.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.risk_contrib import cov_matrix_monthly, percentage_contributions_variance
from src.stress_factors import (
    BASE_BETA_ROW_ORDER,
    FACTOR_BETA_TO_SYNTHETIC_SHOCK_KEY,
    FACTOR_COLUMN_ORDER,
    FACTOR_TO_BETA_KEY,
    _correlation_from_covariance,
    _repair_covariance_psd,
)
from src.stress_covariance_taxonomy import stress_covariance_taxonomy_blend

STRESS_SCENARIO_ANALYTICS_VERSION = "stress_scenario_analytics_v1"

# Default matches stress_testing_spec §2.3
SHOCK_SCALE_ALPHA_DEFAULT = 2.0


def _month_equiv_from_weekly(n_weeks: int) -> float:
    return float(n_weeks) * 12.0 / 52.0


def quality_status_from_n_months(n_m: float) -> str:
    """Map month-equivalent count to quality label (spec gates)."""
    n = float(n_m)
    if n <= 0:
        return "insufficient_data"
    if n < 12:
        return "insufficient_data"
    if n < 24:
        return "low_confidence"
    if n < 60:
        return "usable"
    return "reliable"


def _nested_cov_to_df(nested: dict[str, dict[str, float]] | None) -> pd.DataFrame:
    order = list(FACTOR_COLUMN_ORDER)
    if not nested:
        return pd.DataFrame(0.0, index=order, columns=order)
    out = np.zeros((len(order), len(order)), dtype=float)
    for i, fi in enumerate(order):
        row = nested.get(fi) or nested.get(str(fi)) or {}
        for j, fj in enumerate(order):
            v = row.get(fj)
            if v is None:
                v = row.get(str(fj))
            out[i, j] = float(v) if v is not None else 0.0
    return pd.DataFrame(out, index=order, columns=order)


def _psd_status(cov: pd.DataFrame) -> str:
    arr = cov.values.astype(float)
    arr = (arr + arr.T) / 2.0
    if not np.isfinite(arr).all():
        return "invalid"
    try:
        ev = np.linalg.eigvalsh(arr)
    except np.linalg.LinAlgError:
        return "unknown"
    if float(np.min(ev)) >= -1e-8:
        return "psd"
    return "not_psd"


def _symmetry_max_abs_diff(cov: pd.DataFrame) -> float:
    arr = cov.values.astype(float)
    return float(np.max(np.abs(arr - arr.T))) if arr.size else 0.0


def _beta_vector_portfolio(beta_map: dict[str, Any] | None) -> np.ndarray:
    beta_map = beta_map or {}
    vec: list[float] = []
    for f in FACTOR_COLUMN_ORDER:
        bk = FACTOR_TO_BETA_KEY.get(str(f), f"beta_{f}")
        try:
            vec.append(float(beta_map.get(bk, 0.0)))
        except (TypeError, ValueError):
            vec.append(0.0)
    return np.asarray(vec, dtype=float)


def _factor_risk_contrib_rows(cov: pd.DataFrame, beta_map: dict[str, Any] | None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    vec = _beta_vector_portfolio(beta_map)
    order = list(FACTOR_COLUMN_ORDER)
    vals = cov.reindex(index=order, columns=order).fillna(0.0).values.astype(float)
    variance = float(vec.T @ vals @ vec)
    variance = max(variance, 0.0)
    marginal = vals @ vec
    rows: list[dict[str, Any]] = []
    for idx, factor in enumerate(order):
        contribution = float(vec[idx] * marginal[idx])
        rc = float(contribution / variance) if variance > 1e-20 else 0.0
        rows.append(
            {
                "factor": str(factor),
                "beta_key": FACTOR_TO_BETA_KEY.get(str(factor), f"beta_{factor}"),
                "marginal_contribution_to_variance": contribution,
                "rc_share": rc,
            }
        )
    sorted_rc = sorted(rows, key=lambda r: abs(float(r["rc_share"])), reverse=True)
    top1 = sorted_rc[0] if sorted_rc else None
    top3 = sorted_rc[:3]
    hhi = float(sum(float(r["rc_share"]) ** 2 for r in rows))
    summary = {
        "total_factor_variance": variance,
        "top1_factor": (top1 or {}).get("factor"),
        "top1_rc_share": round(float((top1 or {}).get("rc_share", 0.0)), 6),
        "top3_factors": [str(r.get("factor")) for r in top3],
        "top3_rc_sum": round(float(sum(float(r["rc_share"]) for r in top3)), 6),
        "factor_rc_hhi": round(hhi, 6),
    }
    return rows, summary


def _asset_risk_summary(w: np.ndarray, cov: pd.DataFrame, tickers: list[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    cov_np = cov.reindex(index=tickers, columns=tickers).fillna(0.0).values.astype(float)
    pc = percentage_contributions_variance(w, cov_np)
    rows = [
        {
            "asset": tickers[i],
            "marginal_contribution_to_variance": float((cov_np @ w)[i] * w[i])
            if len(w) == len(tickers)
            else float("nan"),
            "rc_share": float(pc[i]) if i < len(pc) else float("nan"),
        }
        for i in range(len(tickers))
    ]
    srt = sorted(rows, key=lambda r: float(r["rc_share"]), reverse=True)
    top1 = srt[0] if srt else None
    top3 = srt[:3]
    hhi = float(sum(float(r["rc_share"]) ** 2 for r in rows))
    summ = {
        "top1_asset": (top1 or {}).get("asset"),
        "top1_rc_share": round(float((top1 or {}).get("rc_share", 0.0)), 6),
        "top3_assets": [str(r.get("asset")) for r in top3],
        "top3_rc_sum": round(float(sum(float(r["rc_share"]) for r in top3)), 6),
        "asset_rc_hhi": round(hhi, 6),
    }
    return rows, summ


def _cov_from_returns_sample(
    df: pd.DataFrame,
    *,
    shrinkage: bool,
) -> tuple[pd.DataFrame, int, str]:
    if df is None or df.empty or len(df) < 2:
        empty_idx = list(df.columns) if df is not None and len(df.columns) else []
        return pd.DataFrame(index=empty_idx, columns=empty_idx, dtype=float), int(len(df) if df is not None else 0), "insufficient_data"
    cov = cov_matrix_monthly(df, use_shrinkage=shrinkage)
    return cov, int(len(df)), "sample_ddof1_ledoit_wolf" if shrinkage else "sample_ddof1"


def _factor_cov_episode(
    factor_weekly: pd.DataFrame | None,
    start: str,
    end: str,
    *,
    fallback_base: pd.DataFrame,
    use_shrinkage: bool,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    meta: dict[str, Any] = {
        "factor_covariance_method": "weekly_episode_sample",
        "shrinkage_applied": bool(use_shrinkage),
        "n_obs": 0,
        "data_start": start,
        "data_end": end,
        "quality_status": "insufficient_data",
        "warnings": [],
    }
    if factor_weekly is None or factor_weekly.empty:
        meta["warnings"].append("factor_returns_missing_fallback_base")
        meta["factor_covariance_method"] = "fallback_factor_covariance_base"
        return fallback_base.copy(), meta
    sub = factor_weekly.loc[str(start) : str(end)]
    sub = sub.dropna(how="all")
    n = int(len(sub))
    meta["n_obs"] = n
    n_m = _month_equiv_from_weekly(n)
    meta["quality_status"] = quality_status_from_n_months(n_m)
    if meta["quality_status"] == "insufficient_data" or n < 2:
        meta["warnings"].append("factor_cov_fallback_full_sample")
        meta["factor_covariance_method"] = "fallback_factor_covariance_base"
        return fallback_base.copy(), meta
    if use_shrinkage:
        try:
            from sklearn.covariance import LedoitWolf

            cols = [c for c in FACTOR_COLUMN_ORDER if c in sub.columns]
            if not cols:
                meta["warnings"].append("factor_cov_fallback_full_sample")
                meta["factor_covariance_method"] = "fallback_factor_covariance_base"
                return fallback_base.copy(), meta
            x = sub.loc[:, cols].dropna(how="any")
            if len(x) < 2:
                meta["warnings"].append("factor_cov_fallback_full_sample")
                meta["factor_covariance_method"] = "fallback_factor_covariance_base"
                return fallback_base.copy(), meta
            lw = LedoitWolf().fit(x.values.astype(float))
            cov = pd.DataFrame(lw.covariance_, index=cols, columns=cols)
            cov = cov.reindex(index=list(FACTOR_COLUMN_ORDER), columns=list(FACTOR_COLUMN_ORDER)).fillna(0.0)
            meta["factor_covariance_method"] = "weekly_episode_ledoit_wolf"
        except Exception:
            cov = sub.reindex(columns=list(FACTOR_COLUMN_ORDER), fill_value=0.0).cov(ddof=1)
            cov = cov.reindex(index=list(FACTOR_COLUMN_ORDER), columns=list(FACTOR_COLUMN_ORDER)).fillna(0.0)
            meta["factor_covariance_method"] = "weekly_episode_sample"
    else:
        cov = sub.reindex(columns=list(FACTOR_COLUMN_ORDER), fill_value=0.0).cov(ddof=1)
        cov = cov.reindex(index=list(FACTOR_COLUMN_ORDER), columns=list(FACTOR_COLUMN_ORDER)).fillna(0.0)
    repaired, was_rep = _repair_covariance_psd(cov)
    if was_rep:
        meta["warnings"].append("factor_cov_psd_repair")
    return repaired, meta


def _shock_scale_factor_cov(
    base_cov: pd.DataFrame,
    shock_vector: dict[str, float],
    *,
    alpha: float,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    order = list(FACTOR_COLUMN_ORDER)
    cov0 = base_cov.reindex(index=order, columns=order).fillna(0.0)
    vol = np.sqrt(np.maximum(np.diag(cov0.values.astype(float)), 0.0))
    corr = _correlation_from_covariance(cov0)
    m = np.ones(len(order), dtype=float)
    mult_meta: dict[str, float] = {}
    for idx, col in enumerate(order):
        bk = FACTOR_TO_BETA_KEY.get(str(col))
        if not bk:
            continue
        sk = FACTOR_BETA_TO_SYNTHETIC_SHOCK_KEY.get(str(bk))
        if sk is None:
            continue
        try:
            shock_val = float(shock_vector.get(sk, 0.0) or 0.0)
        except (TypeError, ValueError):
            shock_val = 0.0
        mult = 1.0 + float(alpha) * abs(shock_val)
        m[idx] = mult
        mult_meta[str(col)] = float(mult)
    new_vol = vol * m
    cvals = corr.values.astype(float)
    new_cov = np.outer(new_vol, new_vol) * cvals
    np.fill_diagonal(new_cov, new_vol**2)
    df = pd.DataFrame(new_cov, index=order, columns=order)
    repaired, was_rep = _repair_covariance_psd(df)
    meta = {
        "factor_covariance_method": "base_weekly_corr_shock_vol_scale_v1",
        "shock_scale_alpha": float(alpha),
        "shock_scale_multipliers": {k: round(v, 6) for k, v in mult_meta.items()},
        "psd_repaired": bool(was_rep),
    }
    return repaired, meta


def _matrix_long_rows(
    cov: pd.DataFrame,
    *,
    scenario_id: str,
    scenario_type: str,
    kind: str,
    n_obs: int,
    quality_status: str,
    covariance_method: str,
    shrinkage_applied: bool,
    data_start: str | None,
    data_end: str | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cols = list(cov.columns)
    is_asset = kind.startswith("asset")
    for i, ai in enumerate(cols):
        for j, aj in enumerate(cols):
            if i > j:
                continue
            val = float(cov.loc[ai, aj])
            base: dict[str, Any] = {
                "scenario_id": scenario_id,
                "scenario_type": scenario_type,
                "kind": kind,
                "n_obs": n_obs,
                "quality_status": quality_status,
                "covariance_method": covariance_method,
                "shrinkage_applied": shrinkage_applied,
                "data_start": data_start,
                "data_end": data_end,
            }
            if is_asset:
                base["asset_i"] = ai
                base["asset_j"] = aj
                base["covariance"] = val
            else:
                base["factor_i"] = ai
                base["factor_j"] = aj
                base["covariance"] = val
            rows.append(base)
    return rows


def _corr_long_from_cov(
    cov: pd.DataFrame,
    *,
    scenario_id: str,
    scenario_type: str,
    prefix: str,
    n_obs: int,
    quality_status: str,
    covariance_method: str,
    shrinkage_applied: bool,
    data_start: str | None,
    data_end: str | None,
) -> list[dict[str, Any]]:
    c = _correlation_from_covariance(cov)
    rows: list[dict[str, Any]] = []
    cols = list(c.columns)
    for i, ai in enumerate(cols):
        for j, aj in enumerate(cols):
            if i > j:
                continue
            row: dict[str, Any] = {
                "scenario_id": scenario_id,
                "scenario_type": scenario_type,
                "n_obs": n_obs,
                "quality_status": quality_status,
                "covariance_method": covariance_method,
                "shrinkage_applied": shrinkage_applied,
                "data_start": data_start,
                "data_end": data_end,
                "correlation": float(c.loc[ai, aj]),
            }
            if prefix == "asset":
                row["asset_i"] = ai
                row["asset_j"] = aj
            else:
                row["factor_i"] = ai
                row["factor_j"] = aj
            rows.append(row)
    return rows


def _parse_regression_betas(stress_report: dict[str, Any], *, window: str) -> dict[str, Any]:
    key = "factor_regression_5y" if window == "5y" else "factor_regression_10y"
    block = stress_report.get(key) or {}
    # Weekly regression payload has ``betas`` / ``n_obs``; it does not use ``status``.
    has_betas = isinstance(block.get("betas"), dict) and len(block.get("betas") or {}) > 0
    out: dict[str, Any] = {
        "window": window,
        "available": bool(has_betas or str(block.get("status")) == "available"),
    }
    if not out["available"]:
        return out
    betas = block.get("betas") or {}
    t = block.get("t") or {}
    p = block.get("p") or {}
    ci_low = block.get("ci_low") or {}
    ci_high = block.get("ci_high") or {}
    per_factor: dict[str, Any] = {}
    for bk in BASE_BETA_ROW_ORDER:
        per_factor[bk] = {
            "beta": betas.get(bk),
            "t": t.get(bk),
            "p": p.get(bk),
            "ci_low": ci_low.get(bk),
            "ci_high": ci_high.get(bk),
        }
    out["r2"] = block.get("r2")
    out["adj_r2"] = block.get("adj_r2")
    out["n_obs"] = block.get("n_obs")
    out["hac"] = block.get("hac_inference")
    out["per_factor"] = per_factor
    return out


def export_stress_scenario_analytics_csv(payload: dict[str, Any], output_dir_csv: str | Path) -> dict[str, str]:
    """Write CSV artifacts; returns map name -> filename."""
    out_dir = Path(output_dir_csv)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}
    bundle = payload.get("csv_frames") or {}
    if not isinstance(bundle, dict):
        return written
    for name, df in bundle.items():
        if isinstance(df, pd.DataFrame) and not df.empty:
            num_cols = df.select_dtypes(include=[np.number]).columns
            if len(num_cols):
                df = df.copy()
                df[num_cols] = df[num_cols].round(3)
            path = out_dir / name
            df.to_csv(path, index=False)
            written[name] = path.name
    return written


def build_stress_scenario_analytics(
    *,
    stress_report: dict[str, Any],
    weights: dict[str, float],
    tickers: list[str],
    monthly_returns: pd.DataFrame,
    factor_returns_weekly: pd.DataFrame | None,
    cash_proxy_ticker: str | None,
    output_dir_csv: str | Path | None = None,
    shock_scale_alpha: float = SHOCK_SCALE_ALPHA_DEFAULT,
) -> dict[str, Any]:
    """
    Build the full ``stress_scenario_analytics`` payload and optional CSV bundle.

    Caller must pass a ``stress_report`` already containing ``scenario_results``,
    ``historical_results``, ``factor_covariance`` (optional), ``factor_betas_5y`` / ``10y``,
    ``factor_regression_*``, ``factor_betas_adjusted``, ``synthetic_factor_pnl_adjusted``.
    """
    asset_cols = [t for t in tickers if t in monthly_returns.columns]
    w = np.array([float(weights.get(t, 0.0)) for t in asset_cols], dtype=float)
    if w.sum() > 0:
        w = w / w.sum()

    returns_all = monthly_returns[asset_cols].copy()
    returns_all.index = pd.to_datetime(returns_all.index).tz_localize(None)
    cov_base_monthly = cov_matrix_monthly(returns_all.dropna(how="all"), ddof=1)

    fc_block = stress_report.get("factor_covariance") or {}
    base_nested = ((fc_block.get("base") or {}).get("matrix")) if isinstance(fc_block, dict) else None
    factor_cov_base = _nested_cov_to_df(base_nested if isinstance(base_nested, dict) else None)

    adj_overlay = stress_report.get("synthetic_factor_pnl_adjusted") or {}
    adj_by_sid = {
        str(r.get("scenario_id")): r
        for r in (adj_overlay.get("scenarios") or [])
        if isinstance(r, dict) and r.get("scenario_id")
    }

    betas_5y = stress_report.get("factor_betas_5y") or stress_report.get("factor_betas") or {}
    betas_10y = stress_report.get("factor_betas_10y") or {}
    fb_adj_block = stress_report.get("factor_betas_adjusted") or {}
    betas_adj = (fb_adj_block.get("adjusted") if isinstance(fb_adj_block, dict) else None) or {}

    reg_5y = _parse_regression_betas(stress_report, window="5y")
    reg_10y = _parse_regression_betas(stress_report, window="10y")

    def beta_quality() -> str:
        if reg_5y.get("available") and int(reg_5y.get("n_obs") or 0) >= 30:
            return "reliable"
        if reg_5y.get("available"):
            return "usable"
        return "insufficient_data"

    scenarios_out: dict[str, Any] = {}
    errors: list[str] = []

    rows_asset_cov: list[dict[str, Any]] = []
    rows_asset_corr: list[dict[str, Any]] = []
    rows_fac_cov: list[dict[str, Any]] = []
    rows_fac_corr: list[dict[str, Any]] = []
    rows_fac_betas: list[dict[str, Any]] = []
    rows_asset_rc: list[dict[str, Any]] = []
    rows_fac_rc: list[dict[str, Any]] = []
    rows_raw_vs: list[dict[str, Any]] = []
    rows_summary: list[dict[str, Any]] = []

    # --- Synthetic scenarios ---
    by_sid = {str(r.get("scenario_id")): r for r in stress_report.get("scenario_results") or [] if isinstance(r, dict)}
    for sid, srow in by_sid.items():
        if not isinstance(srow, dict):
            continue
        shock = srow.get("shock_vector") or {}
        pnl_reported = srow.get("portfolio_pnl_pct")
        adj_row = adj_by_sid.get(sid, {})
        pnl_raw_model = adj_row.get("pnl_model_raw")
        pnl_adj_model = adj_row.get("pnl_model_adjusted")
        pnl_raw_effective = float(pnl_reported) if pnl_reported is not None else float(pnl_raw_model or 0.0)
        pnl_adj_effective = float(pnl_adj_model) if pnl_adj_model is not None else None
        conservative = None
        if pnl_adj_effective is not None:
            conservative = float(min(pnl_raw_effective, pnl_adj_effective))

        scen: dict[str, Any] = {
            "scenario_type": "synthetic",
            "pnl_raw": round(pnl_raw_effective, 6),
            "pnl_shrinkage_adjusted": round(float(pnl_adj_effective), 6) if pnl_adj_effective is not None else None,
            "conservative_pnl": round(float(conservative), 6) if conservative is not None else None,
            "actual_pnl": None,
            "model_explained_pnl": None,
            "warnings": [],
        }

        # Asset stress cov
        try:
            cov_stress, cov_diag_tax = stress_covariance_taxonomy_blend(
                cov_base_monthly, asset_cols, sid, cash_proxy_ticker=cash_proxy_ticker
            )
        except Exception as exc:
            errors.append(f"{sid}_asset_cov:{exc}")
            cov_stress = cov_base_monthly.reindex(index=asset_cols, columns=asset_cols).fillna(0.0)
            cov_diag_tax = {"error": str(exc)}
            scen["warnings"].append("taxonomy_asset_cov_failed")

        n_m_asset = int(len(returns_all.dropna(how="all")))
        q_asset = quality_status_from_n_months(float(n_m_asset))
        sym_asset = _symmetry_max_abs_diff(cov_stress) < 1e-9
        psd_asset = _psd_status(cov_stress)
        scen["asset_covariance"] = {
            "covariance_method": str(cov_diag_tax.get("stress_cov_method", "taxonomy_blend_v1")),
            "shrinkage_applied": False,
            "taxonomy_metadata": {k: cov_diag_tax.get(k) for k in ("stress_cov_lambda", "stress_cov_calibration_version", "taxonomy_coverage", "vol_mult_by_block", "key_rho_overrides_used") if cov_diag_tax.get(k) is not None},
            "n_obs": n_m_asset,
            "quality_status": q_asset,
            "psd_status": psd_asset,
            "symmetric": sym_asset,
            "data_start": returns_all.index.min().strftime("%Y-%m-%d") if len(returns_all) else None,
            "data_end": returns_all.index.max().strftime("%Y-%m-%d") if len(returns_all) else None,
        }
        rows_asset_cov.extend(
            _matrix_long_rows(
                cov_stress,
                scenario_id=sid,
                scenario_type="synthetic",
                kind="asset_covariance",
                n_obs=n_m_asset,
                quality_status=q_asset,
                covariance_method=str(scen["asset_covariance"]["covariance_method"]),
                shrinkage_applied=False,
                data_start=scen["asset_covariance"]["data_start"],
                data_end=scen["asset_covariance"]["data_end"],
            )
        )
        rows_asset_corr.extend(
            _corr_long_from_cov(
                cov_stress,
                scenario_id=sid,
                scenario_type="synthetic",
                prefix="asset",
                n_obs=n_m_asset,
                quality_status=q_asset,
                covariance_method=str(scen["asset_covariance"]["covariance_method"]),
                shrinkage_applied=False,
                data_start=scen["asset_covariance"]["data_start"],
                data_end=scen["asset_covariance"]["data_end"],
            )
        )

        # Factor shock-scale cov
        fac_cov, fac_meta = _shock_scale_factor_cov(factor_cov_base, shock if isinstance(shock, dict) else {}, alpha=shock_scale_alpha)
        fac_psd = _psd_status(fac_cov)
        n_fac_base = int((fc_block.get("base") or {}).get("n_obs") or 0)
        q_fac = quality_status_from_n_months(_month_equiv_from_weekly(n_fac_base)) if n_fac_base else "insufficient_data"
        if not base_nested:
            scen["warnings"].append("factor_cov_base_missing")
            q_fac = "insufficient_data"
        base_win = (fc_block.get("base") or {}).get("window") if isinstance(fc_block.get("base"), dict) else None
        data_end_fc = base_win.get("analysis_end") if isinstance(base_win, dict) else None
        scen["factor_covariance"] = {
            **fac_meta,
            "n_obs": n_fac_base,
            "quality_status": q_fac,
            "psd_status": fac_psd,
            "data_start": None,
            "data_end": data_end_fc,
        }
        rows_fac_cov.extend(
            _matrix_long_rows(
                fac_cov,
                scenario_id=sid,
                scenario_type="synthetic",
                kind="factor_covariance",
                n_obs=n_fac_base,
                quality_status=q_fac,
                covariance_method=str(fac_meta.get("factor_covariance_method", "")),
                shrinkage_applied=False,
                data_start=None,
                data_end=scen["factor_covariance"].get("data_end"),
            )
        )
        rows_fac_corr.extend(
            _corr_long_from_cov(
                fac_cov,
                scenario_id=sid,
                scenario_type="synthetic",
                prefix="factor",
                n_obs=n_fac_base,
                quality_status=q_fac,
                covariance_method=str(fac_meta.get("factor_covariance_method", "")),
                shrinkage_applied=False,
                data_start=None,
                data_end=scen["factor_covariance"].get("data_end"),
            )
        )

        for src_name, beta_src in ("5y", betas_5y), ("10y", betas_10y), ("adjusted", betas_adj):
            reg_ref = reg_5y if src_name == "5y" else reg_10y if src_name == "10y" else {}
            for bk in BASE_BETA_ROW_ORDER:
                row_fb = {
                    "scenario_id": sid,
                    "scenario_type": "synthetic",
                    "beta_source": src_name,
                    "beta_key": bk,
                    "beta_value": round(float(beta_src.get(bk, 0.0)), 6) if beta_src else None,
                    "n_obs": reg_ref.get("n_obs") if isinstance(reg_ref, dict) else None,
                    "quality_status": beta_quality(),
                    "covariance_method": "n/a",
                    "shrinkage_applied": src_name == "adjusted",
                    "data_start": None,
                    "data_end": None,
                    "r2": reg_ref.get("r2") if src_name != "adjusted" else None,
                    "adj_r2": reg_ref.get("adj_r2") if src_name != "adjusted" else None,
                }
                pf = (reg_ref.get("per_factor") or {}).get(bk) if isinstance(reg_ref, dict) else None
                if isinstance(pf, dict):
                    row_fb["t_stat"] = pf.get("t")
                    row_fb["p_value"] = pf.get("p")
                    row_fb["ci_low"] = pf.get("ci_low")
                    row_fb["ci_high"] = pf.get("ci_high")
                rows_fac_betas.append(row_fb)

        arc_rows, arc_summ = _asset_risk_summary(w, cov_stress, asset_cols)
        for r in arc_rows:
            rows_asset_rc.append(
                {
                    "scenario_id": sid,
                    "scenario_type": "synthetic",
                    "n_obs": n_m_asset,
                    "quality_status": q_asset,
                    "covariance_method": scen["asset_covariance"]["covariance_method"],
                    "shrinkage_applied": False,
                    "data_start": scen["asset_covariance"]["data_start"],
                    "data_end": scen["asset_covariance"]["data_end"],
                    **r,
                }
            )
        frc_raw, frc_summ_raw = _factor_risk_contrib_rows(fac_cov, betas_5y)
        frc_adj, frc_summ_adj = _factor_risk_contrib_rows(fac_cov, betas_adj) if betas_adj else ([], {})
        for r in frc_raw:
            rows_fac_rc.append(
                {
                    "scenario_id": sid,
                    "scenario_type": "synthetic",
                    "beta_side": "raw_5y",
                    "n_obs": n_fac_base,
                    "quality_status": q_fac,
                    "covariance_method": fac_meta.get("factor_covariance_method"),
                    "shrinkage_applied": False,
                    "data_start": None,
                    "data_end": scen["factor_covariance"].get("data_end"),
                    **r,
                }
            )
        if betas_adj:
            for r in frc_adj:
                rows_fac_rc.append(
                    {
                        "scenario_id": sid,
                        "scenario_type": "synthetic",
                        "beta_side": "adjusted",
                        "n_obs": n_fac_base,
                        "quality_status": q_fac,
                        "covariance_method": fac_meta.get("factor_covariance_method"),
                        "shrinkage_applied": True,
                        "data_start": None,
                        "data_end": scen["factor_covariance"].get("data_end"),
                        **r,
                    }
                )

        mat_delta = None
        if pnl_adj_effective is not None:
            mat_delta = bool(
                abs(pnl_adj_effective - pnl_raw_effective) >= 0.01
                or abs(pnl_adj_effective - pnl_raw_effective) / max(abs(pnl_raw_effective), 0.01) >= 0.25
            )
        rows_raw_vs.append({
            "scenario_id": sid,
            "scenario_type": "synthetic",
            "pnl_layer": "factor_model",
            "pnl_raw": round(pnl_raw_effective, 6),
            "pnl_shrinkage_adjusted": round(float(pnl_adj_effective), 6) if pnl_adj_effective is not None else None,
            "material_difference": mat_delta,
            "top1_asset_raw": arc_summ.get("top1_asset"),
            "top1_rc_share_raw": arc_summ.get("top1_rc_share"),
            "top1_factor_raw": frc_summ_raw.get("top1_factor"),
            "top1_factor_rc_share_raw": frc_summ_raw.get("top1_rc_share"),
            "top1_factor_adjusted": frc_summ_adj.get("top1_factor") if betas_adj else None,
            "top1_factor_rc_share_adjusted": frc_summ_adj.get("top1_rc_share") if betas_adj else None,
            "n_obs": n_m_asset,
            "quality_status": q_asset,
            "covariance_method": scen["asset_covariance"]["covariance_method"],
            "shrinkage_applied": False,
            "data_start": scen["asset_covariance"]["data_start"],
            "data_end": scen["asset_covariance"]["data_end"],
        })

        fac_b_usable = beta_quality() in {"usable", "reliable", "low_confidence"}
        asset_usable = psd_asset == "psd" and q_asset in {"usable", "reliable", "low_confidence"}
        factor_usable = fac_psd == "psd" and q_fac in {"usable", "reliable", "low_confidence"}
        suitable = bool(
            asset_usable and factor_usable and fac_b_usable and q_asset in {"usable", "reliable"} and q_fac in {"usable", "reliable"}
        )

        scen["asset_covariance_available"] = asset_usable
        scen["factor_covariance_available"] = factor_usable
        scen["factor_betas_available"] = fac_b_usable
        scen["asset_rc_available"] = asset_usable and float(arc_summ.get("top3_rc_sum") or 0) <= 1.001
        scen["factor_rc_available"] = factor_usable
        scen["suitable_robust_optimization_input"] = suitable
        scen["top_asset_risk_contributors"] = arc_summ
        scen["top_factor_risk_contributors"] = {"raw_5y": frc_summ_raw, "adjusted": frc_summ_adj if betas_adj else None}
        scen["raw_vs_shrinkage"] = {
            "pnl_material_difference": mat_delta,
            "asset_rc_hhi": arc_summ.get("asset_rc_hhi"),
            "factor_rc_hhi_raw": frc_summ_raw.get("factor_rc_hhi"),
            "factor_rc_hhi_adjusted": frc_summ_adj.get("factor_rc_hhi") if betas_adj else None,
        }
        scenarios_out[sid] = scen

        rows_summary.append(
            {
                "scenario_id": sid,
                "scenario_type": "synthetic",
                "asset_covariance_usable": asset_usable,
                "factor_covariance_usable": factor_usable,
                "factor_betas_usable": fac_b_usable,
                "asset_rc_usable": scen["asset_rc_available"],
                "factor_rc_usable": scen["factor_rc_available"],
                "suitable_robust_optimization_input": suitable,
                "asset_quality": q_asset,
                "factor_quality": q_fac,
                "asset_psd": psd_asset,
                "factor_psd": fac_psd,
                "top1_asset": arc_summ.get("top1_asset"),
                "top1_asset_rc": arc_summ.get("top1_rc_share"),
                "top1_factor_raw": frc_summ_raw.get("top1_factor"),
                "top1_factor_rc_raw": frc_summ_raw.get("top1_rc_share"),
                "asset_rc_hhi": arc_summ.get("asset_rc_hhi"),
                "factor_rc_hhi_raw": frc_summ_raw.get("factor_rc_hhi"),
                "n_obs_assets": n_m_asset,
                "n_obs_factors": n_fac_base,
                "covariance_method_asset": scen["asset_covariance"]["covariance_method"],
                "covariance_method_factor": fac_meta.get("factor_covariance_method"),
                "shrinkage_applied_asset": False,
                "shrinkage_applied_factor": False,
                "data_start": scen["asset_covariance"]["data_start"],
                "data_end": scen["asset_covariance"]["data_end"],
            }
        )

    # --- Historical episodes ---
    hist_by_ep = {str(h.get("episode")): h for h in stress_report.get("historical_results") or [] if isinstance(h, dict)}
    for ep_id, hrow in hist_by_ep.items():
        if not isinstance(hrow, dict):
            continue
        start = str(hrow.get("episode_start", ""))
        end = str(hrow.get("episode_end", ""))
        actual = hrow.get("pnl_real_episode")
        model_pnl = hrow.get("factor_model_pnl_pct")

        scen: dict[str, Any] = {
            "scenario_type": "historical",
            "actual_pnl": round(float(actual), 6) if actual is not None and np.isfinite(float(actual)) else None,
            "model_explained_pnl": round(float(model_pnl), 6) if model_pnl is not None and np.isfinite(float(model_pnl)) else None,
            "attribution_source": "historical_factor_attribution" if hrow.get("historical_factor_attribution") else None,
            "pnl_raw": None,
            "pnl_shrinkage_adjusted": None,
            "conservative_pnl": None,
            "warnings": [],
        }

        sub_m = returns_all.loc[start:end]
        sub_m = sub_m.dropna(how="all")
        n_m = int(len(sub_m))
        q_m = quality_status_from_n_months(float(n_m))

        cov_hist, _, m_eth = _cov_from_returns_sample(sub_m, shrinkage=False)
        cov_lw, _, _ = _cov_from_returns_sample(sub_m, shrinkage=True)
        cov_hist = cov_hist.reindex(index=asset_cols, columns=asset_cols).fillna(0.0)
        cov_lw = cov_lw.reindex(index=asset_cols, columns=asset_cols).fillna(0.0)
        psd_h = _psd_status(cov_hist)

        scen["asset_covariance"] = {
            "covariance_method": m_eth,
            "shrinkage_applied": False,
            "covariance_method_shrunk_parallel": "sample_ddof1_ledoit_wolf",
            "n_obs": n_m,
            "quality_status": q_m,
            "psd_status": psd_h,
            "data_start": start,
            "data_end": end,
        }
        if n_m < 2:
            scen["warnings"].append("historical_asset_cov_insufficient")

        rows_asset_cov.extend(
            _matrix_long_rows(
                cov_hist,
                scenario_id=ep_id,
                scenario_type="historical",
                kind="asset_covariance",
                n_obs=n_m,
                quality_status=q_m,
                covariance_method=m_eth,
                shrinkage_applied=False,
                data_start=start,
                data_end=end,
            )
        )
        rows_asset_corr.extend(
            _corr_long_from_cov(
                cov_hist,
                scenario_id=ep_id,
                scenario_type="historical",
                prefix="asset",
                n_obs=n_m,
                quality_status=q_m,
                covariance_method=m_eth,
                shrinkage_applied=False,
                data_start=start,
                data_end=end,
            )
        )

        m_eth_lw = "sample_ddof1_ledoit_wolf"
        psd_lw = _psd_status(cov_lw)
        scen["asset_covariance"]["parallel_shrinkage"] = {
            "covariance_method": m_eth_lw,
            "shrinkage_applied": True,
            "psd_status": psd_lw,
        }
        rows_asset_cov.extend(
            _matrix_long_rows(
                cov_lw,
                scenario_id=ep_id,
                scenario_type="historical",
                kind="asset_covariance",
                n_obs=n_m,
                quality_status=q_m,
                covariance_method=m_eth_lw,
                shrinkage_applied=True,
                data_start=start,
                data_end=end,
            )
        )
        rows_asset_corr.extend(
            _corr_long_from_cov(
                cov_lw,
                scenario_id=ep_id,
                scenario_type="historical",
                prefix="asset",
                n_obs=n_m,
                quality_status=q_m,
                covariance_method=m_eth_lw,
                shrinkage_applied=True,
                data_start=start,
                data_end=end,
            )
        )

        fac_cov_ep, fac_meta_ep = _factor_cov_episode(
            factor_returns_weekly,
            start,
            end,
            fallback_base=factor_cov_base,
            use_shrinkage=True,
        )
        fac_psd_ep = _psd_status(fac_cov_ep)
        scen["factor_covariance"] = {**fac_meta_ep, "psd_status": fac_psd_ep}
        n_f = int(fac_meta_ep.get("n_obs") or 0)
        q_f = str(fac_meta_ep.get("quality_status") or "insufficient_data")

        rows_fac_cov.extend(
            _matrix_long_rows(
                fac_cov_ep,
                scenario_id=ep_id,
                scenario_type="historical",
                kind="factor_covariance",
                n_obs=n_f,
                quality_status=q_f,
                covariance_method=str(fac_meta_ep.get("factor_covariance_method")),
                shrinkage_applied=bool(fac_meta_ep.get("shrinkage_applied")),
                data_start=start,
                data_end=end,
            )
        )
        rows_fac_corr.extend(
            _corr_long_from_cov(
                fac_cov_ep,
                scenario_id=ep_id,
                scenario_type="historical",
                prefix="factor",
                n_obs=n_f,
                quality_status=q_f,
                covariance_method=str(fac_meta_ep.get("factor_covariance_method")),
                shrinkage_applied=bool(fac_meta_ep.get("shrinkage_applied")),
                data_start=start,
                data_end=end,
            )
        )

        for src_name, beta_src in ("5y", betas_5y), ("10y", betas_10y), ("adjusted", betas_adj):
            reg_ref = reg_5y if src_name == "5y" else reg_10y if src_name == "10y" else {}
            for bk in BASE_BETA_ROW_ORDER:
                row_fb = {
                    "scenario_id": ep_id,
                    "scenario_type": "historical",
                    "beta_source": src_name,
                    "beta_key": bk,
                    "beta_value": round(float(beta_src.get(bk, 0.0)), 6) if beta_src else None,
                    "n_obs": n_m,
                    "quality_status": q_m,
                    "covariance_method": "historical_episode",
                    "shrinkage_applied": src_name == "adjusted",
                    "data_start": start,
                    "data_end": end,
                    "r2": reg_ref.get("r2") if src_name != "adjusted" else None,
                    "adj_r2": reg_ref.get("adj_r2") if src_name != "adjusted" else None,
                }
                pf = (reg_ref.get("per_factor") or {}).get(bk) if isinstance(reg_ref, dict) else None
                if isinstance(pf, dict):
                    row_fb["t_stat"] = pf.get("t")
                    row_fb["p_value"] = pf.get("p")
                    row_fb["ci_low"] = pf.get("ci_low")
                    row_fb["ci_high"] = pf.get("ci_high")
                rows_fac_betas.append(row_fb)

        arc_rows, arc_summ = _asset_risk_summary(w, cov_hist, asset_cols)
        for r in arc_rows:
            rows_asset_rc.append(
                {
                    "scenario_id": ep_id,
                    "scenario_type": "historical",
                    "n_obs": n_m,
                    "quality_status": q_m,
                    "covariance_method": m_eth,
                    "shrinkage_applied": False,
                    "data_start": start,
                    "data_end": end,
                    **r,
                }
            )
        frc_raw, frc_summ_raw = _factor_risk_contrib_rows(fac_cov_ep, betas_5y)
        frc_adj, frc_summ_adj = _factor_risk_contrib_rows(fac_cov_ep, betas_adj) if betas_adj else ([], {})
        for r in frc_raw:
            rows_fac_rc.append(
                {
                    "scenario_id": ep_id,
                    "scenario_type": "historical",
                    "beta_side": "raw_5y",
                    "n_obs": n_f,
                    "quality_status": q_f,
                    "covariance_method": fac_meta_ep.get("factor_covariance_method"),
                    "shrinkage_applied": bool(fac_meta_ep.get("shrinkage_applied")),
                    "data_start": start,
                    "data_end": end,
                    **r,
                }
            )
        if betas_adj:
            for r in frc_adj:
                rows_fac_rc.append(
                    {
                        "scenario_id": ep_id,
                        "scenario_type": "historical",
                        "beta_side": "adjusted",
                        "n_obs": n_f,
                        "quality_status": q_f,
                        "covariance_method": fac_meta_ep.get("factor_covariance_method"),
                        "shrinkage_applied": True,
                        "data_start": start,
                        "data_end": end,
                        **r,
                    }
                )

        rows_raw_vs.append({
            "scenario_id": ep_id,
            "scenario_type": "historical",
            "pnl_layer": "realized",
            "pnl_raw": scen["actual_pnl"],
            "pnl_shrinkage_adjusted": None,
            "material_difference": None,
            "note": "historical_pnl_not_shrunk",
            "top1_asset_raw": arc_summ.get("top1_asset"),
            "top1_rc_share_raw": arc_summ.get("top1_rc_share"),
            "top1_factor_raw": frc_summ_raw.get("top1_factor"),
            "top1_factor_rc_share_raw": frc_summ_raw.get("top1_rc_share"),
            "n_obs": n_m,
            "quality_status": q_m,
            "covariance_method": m_eth,
            "shrinkage_applied": False,
            "data_start": start,
            "data_end": end,
        })

        fac_b_usable = beta_quality() in {"usable", "reliable", "low_confidence"}
        asset_usable = psd_h == "psd" and q_m in {"usable", "reliable", "low_confidence"}
        factor_usable = fac_psd_ep == "psd" and q_f in {"usable", "reliable", "low_confidence"}
        suitable = bool(
            asset_usable and factor_usable and fac_b_usable and q_m in {"usable", "reliable"} and q_f in {"usable", "reliable"}
        )

        scen["asset_covariance_available"] = asset_usable
        scen["factor_covariance_available"] = factor_usable
        scen["factor_betas_available"] = fac_b_usable
        scen["asset_rc_available"] = asset_usable
        scen["factor_rc_available"] = factor_usable
        scen["suitable_robust_optimization_input"] = suitable
        scen["top_asset_risk_contributors"] = arc_summ
        scen["top_factor_risk_contributors"] = {"raw_5y": frc_summ_raw, "adjusted": frc_summ_adj if betas_adj else None}
        scen["raw_vs_shrinkage"] = {"note": "historical_realized_pnl_and_cov_only"}
        scenarios_out[ep_id] = scen

        rows_summary.append(
            {
                "scenario_id": ep_id,
                "scenario_type": "historical",
                "asset_covariance_usable": asset_usable,
                "factor_covariance_usable": factor_usable,
                "factor_betas_usable": fac_b_usable,
                "asset_rc_usable": scen["asset_rc_available"],
                "factor_rc_usable": scen["factor_rc_available"],
                "suitable_robust_optimization_input": suitable,
                "asset_quality": q_m,
                "factor_quality": q_f,
                "asset_psd": psd_h,
                "factor_psd": fac_psd_ep,
                "top1_asset": arc_summ.get("top1_asset"),
                "top1_asset_rc": arc_summ.get("top1_rc_share"),
                "top1_factor_raw": frc_summ_raw.get("top1_factor"),
                "top1_factor_rc_raw": frc_summ_raw.get("top1_rc_share"),
                "asset_rc_hhi": arc_summ.get("asset_rc_hhi"),
                "factor_rc_hhi_raw": frc_summ_raw.get("factor_rc_hhi"),
                "n_obs_assets": n_m,
                "n_obs_factors": n_f,
                "covariance_method_asset": m_eth,
                "covariance_method_factor": fac_meta_ep.get("factor_covariance_method"),
                "shrinkage_applied_asset": False,
                "shrinkage_applied_factor": bool(fac_meta_ep.get("shrinkage_applied")),
                "data_start": start,
                "data_end": end,
            }
        )

    csv_frames = {
            "stress_scenario_asset_covariance.csv": pd.DataFrame(rows_asset_cov),
            "stress_scenario_asset_correlation.csv": pd.DataFrame(rows_asset_corr),
            "stress_scenario_factor_covariance.csv": pd.DataFrame(rows_fac_cov),
            "stress_scenario_factor_correlation.csv": pd.DataFrame(rows_fac_corr),
            "stress_scenario_factor_betas_used.csv": pd.DataFrame(rows_fac_betas),
            "stress_scenario_asset_risk_contribution.csv": pd.DataFrame(rows_asset_rc),
            "stress_scenario_factor_risk_contribution.csv": pd.DataFrame(rows_fac_rc),
            "stress_scenario_raw_vs_shrinkage_summary.csv": pd.DataFrame(rows_raw_vs),
            "stress_scenario_analytics_summary.csv": pd.DataFrame(rows_summary),
        }

    out: dict[str, Any] = {
        "version": STRESS_SCENARIO_ANALYTICS_VERSION,
        "scenarios": scenarios_out,
        "errors": errors,
        "shock_scale_alpha_default": shock_scale_alpha,
    }

    if output_dir_csv is not None:
        out["csv_export"] = export_stress_scenario_analytics_csv({"csv_frames": csv_frames}, output_dir_csv)

    return out


__all__ = [
    "STRESS_SCENARIO_ANALYTICS_VERSION",
    "SHOCK_SCALE_ALPHA_DEFAULT",
    "build_stress_scenario_analytics",
    "export_stress_scenario_analytics_csv",
    "quality_status_from_n_months",
]
