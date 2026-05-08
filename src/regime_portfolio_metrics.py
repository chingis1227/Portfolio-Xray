"""
Regime-level daily portfolio analytics v1 (diagnostic-only).

Mirrors base portfolio / asset metrics on daily returns sliced by primary macro regime.
See docs/docs/stress_testing_spec.md for contract.
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

from src.metrics_daily import (
    TRADING_DAYS_PER_YEAR,
    beta_base_daily,
    cagr_from_equity_daily,
    kurtosis_log_daily,
    max_drawdown_daily,
    sharpe_daily,
    skewness_log_daily,
    sortino_daily,
    treynor_daily,
    vol_annual_daily,
    time_to_recovery_daily,
    log_returns_from_simple_daily,
)
from src.portfolio_analytics import es_historical, var_historical
from src.regime_factor_analytics import (
    REGIME_ANALYTICS_ANNUALIZATION_FACTOR,
    regime_factor_quality_daily,
    _covariance_with_ledoit_wolf,
)
from src.risk_contrib import percentage_contributions_variance
from src.stress_factors_macro import MACRO_PRIMARY_REGIME_NAMES

_LOG = logging.getLogger(__name__)

REGIME_PORTFOLIO_METRICS_VERSION = "regime_portfolio_metrics_v1"

# Historical VaR/ES: require at least the daily regime Factor Analytics "usable" floor (>=60 days).
VAR_ES_MIN_OBS = 60


def expand_rf_monthly_to_daily(rf_monthly: pd.Series, daily_index: pd.DatetimeIndex) -> pd.Series:
    """Forward-fill month-end risk-free (monthly effective) to each trading day."""

    if rf_monthly is None or rf_monthly.empty:
        return pd.Series(dtype=float, index=daily_index)
    s = rf_monthly.copy()
    s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
    s = s.sort_index()
    idx = pd.DatetimeIndex(daily_index).tz_localize(None).normalize().sort_values()
    out = s.reindex(idx, method="ffill")
    # Days before the first month-end observation use the earliest published rate (no look-ahead).
    return out.bfill()


def _empty_metric_status() -> dict[str, Any]:
    return {
        "metric_available": False,
        "unavailable_reason": None,
        "value": None,
    }


def _ok_value(val: Any) -> bool:
    if val is None:
        return False
    if isinstance(val, float) and (np.isnan(val) or np.isinf(val)):
        return False
    return True


def _pack_portfolio_metrics(
    r_p: pd.Series,
    rf_d: pd.Series,
    bench_d: pd.Series,
    mar_daily: float | pd.Series | None,
    n_days: int,
) -> dict[str, Any]:
    """Compute portfolio metric dict with per-field availability."""

    out: dict[str, Any] = {
        "cagr_annual": _empty_metric_status(),
        "vol_annual": _empty_metric_status(),
        "sharpe": _empty_metric_status(),
        "sortino": _empty_metric_status(),
        "beta_portfolio": _empty_metric_status(),
        "treynor": _empty_metric_status(),
        "max_drawdown": _empty_metric_status(),
        "time_to_recovery_trading_days": _empty_metric_status(),
        "skewness_log": _empty_metric_status(),
        "kurtosis_log": _empty_metric_status(),
        "var_95": _empty_metric_status(),
        "var_99": _empty_metric_status(),
        "es_95": _empty_metric_status(),
        "es_99": _empty_metric_status(),
    }

    if n_days < 2:
        reason = "insufficient_days_lt_2"
        for k in out:
            out[k]["unavailable_reason"] = reason
        return out

    # CAGR
    cg = cagr_from_equity_daily(r_p)
    out["cagr_annual"]["metric_available"] = _ok_value(cg)
    out["cagr_annual"]["value"] = float(cg) if _ok_value(cg) else None
    if not out["cagr_annual"]["metric_available"]:
        out["cagr_annual"]["unavailable_reason"] = "cagr_undefined"

    # Vol
    vol = vol_annual_daily(r_p)
    out["vol_annual"]["metric_available"] = _ok_value(vol)
    out["vol_annual"]["value"] = float(vol) if _ok_value(vol) else None
    if not out["vol_annual"]["metric_available"]:
        out["vol_annual"]["unavailable_reason"] = "vol_undefined"

    # Sharpe / Sortino need rf alignment
    common_rf = r_p.dropna().index.intersection(rf_d.dropna().index)
    if len(common_rf) < 2:
        out["sharpe"]["unavailable_reason"] = "rf_alignment_lt_2"
        out["sortino"]["unavailable_reason"] = "rf_alignment_lt_2"
    else:
        sh = sharpe_daily(r_p, rf_d)
        out["sharpe"]["metric_available"] = _ok_value(sh)
        out["sharpe"]["value"] = float(sh) if _ok_value(sh) else None
        if not out["sharpe"]["metric_available"]:
            out["sharpe"]["unavailable_reason"] = "sharpe_undefined"
        so = sortino_daily(r_p, rf_d, mar_daily=mar_daily)
        out["sortino"]["metric_available"] = _ok_value(so)
        out["sortino"]["value"] = float(so) if _ok_value(so) else None
        if not out["sortino"]["metric_available"]:
            out["sortino"]["unavailable_reason"] = "sortino_undefined"

    common_b = r_p.dropna().index.intersection(bench_d.dropna().index)
    if len(common_b) < 2:
        out["beta_portfolio"]["unavailable_reason"] = "benchmark_alignment_lt_2"
        out["treynor"]["unavailable_reason"] = "benchmark_alignment_lt_2_or_beta_missing"
    else:
        b = beta_base_daily(r_p, bench_d)
        out["beta_portfolio"]["metric_available"] = _ok_value(b)
        out["beta_portfolio"]["value"] = float(b) if _ok_value(b) else None
        if not out["beta_portfolio"]["metric_available"]:
            out["beta_portfolio"]["unavailable_reason"] = "beta_undefined"
        tr = treynor_daily(r_p, rf_d, b) if out["beta_portfolio"]["metric_available"] else float("nan")
        out["treynor"]["metric_available"] = _ok_value(tr)
        out["treynor"]["value"] = float(tr) if _ok_value(tr) else None
        if not out["treynor"]["metric_available"]:
            out["treynor"]["unavailable_reason"] = "treynor_undefined"

    mdd, _ = max_drawdown_daily(r_p)
    out["max_drawdown"]["metric_available"] = _ok_value(mdd)
    out["max_drawdown"]["value"] = float(mdd) if _ok_value(mdd) else None
    if not out["max_drawdown"]["metric_available"]:
        out["max_drawdown"]["unavailable_reason"] = "mdd_undefined"

    ttr, rec, unit = time_to_recovery_daily(r_p)
    out["time_to_recovery_trading_days"]["metric_available"] = rec and ttr is not None
    out["time_to_recovery_trading_days"]["value"] = float(ttr) if ttr is not None else None
    out["time_to_recovery_trading_days"]["ttr_unit"] = unit
    out["time_to_recovery_trading_days"]["recovered"] = rec
    if not out["time_to_recovery_trading_days"]["metric_available"]:
        out["time_to_recovery_trading_days"]["unavailable_reason"] = "no_recovery_in_window"

    lr = log_returns_from_simple_daily(r_p)
    sk = skewness_log_daily(lr)
    kt = kurtosis_log_daily(lr)
    out["skewness_log"]["metric_available"] = _ok_value(sk)
    out["skewness_log"]["value"] = float(sk) if _ok_value(sk) else None
    if not out["skewness_log"]["metric_available"]:
        out["skewness_log"]["unavailable_reason"] = "skew_undefined"
    out["kurtosis_log"]["metric_available"] = _ok_value(kt)
    out["kurtosis_log"]["value"] = float(kt) if _ok_value(kt) else None
    if not out["kurtosis_log"]["metric_available"]:
        out["kurtosis_log"]["unavailable_reason"] = "kurtosis_undefined"

    if n_days < VAR_ES_MIN_OBS:
        vr = "historical_var_es_requires_n_ge_{}".format(VAR_ES_MIN_OBS)
        for k in ("var_95", "var_99", "es_95", "es_99"):
            out[k]["unavailable_reason"] = vr
    else:
        for conf, key in ((0.95, "var_95"), (0.99, "var_99")):
            v = var_historical(r_p, conf)
            out[key]["metric_available"] = _ok_value(v)
            out[key]["value"] = float(v) if _ok_value(v) else None
            if not out[key]["metric_available"]:
                out[key]["unavailable_reason"] = "var_undefined"
        for conf, key in ((0.95, "es_95"), (0.99, "es_99")):
            e = es_historical(r_p, conf)
            out[key]["metric_available"] = _ok_value(e)
            out[key]["value"] = float(e) if _ok_value(e) else None
            if not out[key]["metric_available"]:
                out[key]["unavailable_reason"] = "es_undefined"

    return out


def _pack_asset_metrics(
    ticker: str,
    r_a: pd.Series,
    rf_d: pd.Series,
    bench_d: pd.Series,
    local_d: pd.Series | None,
    mar_daily: float | pd.Series | None,
    n_days: int,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "ticker": ticker,
        "cagr_annual": _empty_metric_status(),
        "vol_annual": _empty_metric_status(),
        "sharpe": _empty_metric_status(),
        "sortino": _empty_metric_status(),
        "beta_base": _empty_metric_status(),
        "beta_local": _empty_metric_status(),
        "treynor": _empty_metric_status(),
        "max_drawdown": _empty_metric_status(),
        "skewness_log": _empty_metric_status(),
        "kurtosis_log": _empty_metric_status(),
    }
    if n_days < 2:
        reason = "insufficient_days_lt_2"
        for k in ("cagr_annual", "vol_annual", "sharpe", "sortino", "beta_base", "beta_local", "treynor", "max_drawdown", "skewness_log", "kurtosis_log"):
            out[k]["unavailable_reason"] = reason
        return out

    cg = cagr_from_equity_daily(r_a)
    out["cagr_annual"]["metric_available"] = _ok_value(cg)
    out["cagr_annual"]["value"] = float(cg) if _ok_value(cg) else None
    if not out["cagr_annual"]["metric_available"]:
        out["cagr_annual"]["unavailable_reason"] = "cagr_undefined"

    vol = vol_annual_daily(r_a)
    out["vol_annual"]["metric_available"] = _ok_value(vol)
    out["vol_annual"]["value"] = float(vol) if _ok_value(vol) else None
    if not out["vol_annual"]["metric_available"]:
        out["vol_annual"]["unavailable_reason"] = "vol_undefined"

    common_rf = r_a.dropna().index.intersection(rf_d.dropna().index)
    if len(common_rf) < 2:
        out["sharpe"]["unavailable_reason"] = "rf_alignment_lt_2"
        out["sortino"]["unavailable_reason"] = "rf_alignment_lt_2"
    else:
        sh = sharpe_daily(r_a, rf_d)
        out["sharpe"]["metric_available"] = _ok_value(sh)
        out["sharpe"]["value"] = float(sh) if _ok_value(sh) else None
        if not out["sharpe"]["metric_available"]:
            out["sharpe"]["unavailable_reason"] = "sharpe_undefined"
        so = sortino_daily(r_a, rf_d, mar_daily=mar_daily)
        out["sortino"]["metric_available"] = _ok_value(so)
        out["sortino"]["value"] = float(so) if _ok_value(so) else None
        if not out["sortino"]["metric_available"]:
            out["sortino"]["unavailable_reason"] = "sortino_undefined"

    common_b = r_a.dropna().index.intersection(bench_d.dropna().index)
    if len(common_b) < 2:
        out["beta_base"]["unavailable_reason"] = "benchmark_alignment_lt_2"
        out["beta_local"]["unavailable_reason"] = "benchmark_or_local_alignment_lt_2"
        out["treynor"]["unavailable_reason"] = "beta_missing"
    else:
        b = beta_base_daily(r_a, bench_d)
        out["beta_base"]["metric_available"] = _ok_value(b)
        out["beta_base"]["value"] = float(b) if _ok_value(b) else None
        if not out["beta_base"]["metric_available"]:
            out["beta_base"]["unavailable_reason"] = "beta_undefined"
        if local_d is not None and len(r_a.dropna().index.intersection(local_d.dropna().index)) >= 2:
            bl = beta_base_daily(r_a, local_d)
            out["beta_local"]["metric_available"] = _ok_value(bl)
            out["beta_local"]["value"] = float(bl) if _ok_value(bl) else None
        else:
            out["beta_local"]["metric_available"] = out["beta_base"]["metric_available"]
            out["beta_local"]["value"] = out["beta_base"]["value"]
            if not out["beta_local"]["metric_available"]:
                out["beta_local"]["unavailable_reason"] = "local_benchmark_unavailable_use_beta_base"
        tr = treynor_daily(r_a, rf_d, b) if out["beta_base"]["metric_available"] else float("nan")
        out["treynor"]["metric_available"] = _ok_value(tr)
        out["treynor"]["value"] = float(tr) if _ok_value(tr) else None
        if not out["treynor"]["metric_available"]:
            out["treynor"]["unavailable_reason"] = "treynor_undefined"

    mdd, _ = max_drawdown_daily(r_a)
    out["max_drawdown"]["metric_available"] = _ok_value(mdd)
    out["max_drawdown"]["value"] = float(mdd) if _ok_value(mdd) else None
    if not out["max_drawdown"]["metric_available"]:
        out["max_drawdown"]["unavailable_reason"] = "mdd_undefined"

    lr = log_returns_from_simple_daily(r_a)
    sk = skewness_log_daily(lr)
    kt = kurtosis_log_daily(lr)
    out["skewness_log"]["metric_available"] = _ok_value(sk)
    out["skewness_log"]["value"] = float(sk) if _ok_value(sk) else None
    if not out["skewness_log"]["metric_available"]:
        out["skewness_log"]["unavailable_reason"] = "skew_undefined"
    out["kurtosis_log"]["metric_available"] = _ok_value(kt)
    out["kurtosis_log"]["value"] = float(kt) if _ok_value(kt) else None
    if not out["kurtosis_log"]["metric_available"]:
        out["kurtosis_log"]["unavailable_reason"] = "kurtosis_undefined"

    return out


def _slim_factor_block(fa_block: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(fa_block, dict) or not fa_block:
        return {}
    strip = ("covariance", "correlation")
    ac = fa_block.get("asset_covariance") or {}
    fc = fa_block.get("factor_covariance") or {}
    return {
        "label": fa_block.get("label"),
        "n_obs": fa_block.get("n_obs"),
        "n_obs_daily": fa_block.get("n_obs_daily"),
        "quality_status": fa_block.get("quality_status"),
        "asset_covariance_available": bool(ac.get("available", False)),
        "factor_covariance_available": bool(fc.get("available", False)),
        "asset_factor_betas_available": bool(fa_block.get("asset_factor_betas_available", False)),
        "factor_rc_available": bool(fa_block.get("factor_rc_available", False)),
        "portfolio_factor_exposure": fa_block.get("portfolio_factor_exposure"),
        "factor_variance_contribution": fa_block.get("factor_variance_contribution"),
        "asset_factor_betas": fa_block.get("asset_factor_betas"),
        "dominant_factors": fa_block.get("dominant_factors"),
        "hac_max_lags": fa_block.get("hac_max_lags"),
        "warnings": list(fa_block.get("warnings") or []),
        "asset_covariance": {k: v for k, v in ac.items() if k not in strip},
        "factor_covariance": {k: v for k, v in fc.items() if k not in strip},
    }


def build_regime_portfolio_metrics(
    *,
    daily_asset_returns: pd.DataFrame,
    daily_regime_labels_ffill: pd.Series,
    weights: dict[str, float],
    rf_daily: pd.Series,
    benchmark_daily_returns: pd.Series,
    mar_daily: float | pd.Series | None = None,
    local_benchmark_daily_by_ticker: dict[str, pd.Series] | None = None,
    regime_factor_analytics_payload: dict[str, Any] | None = None,
    weight_handling_note: str | None = None,
) -> dict[str, Any]:
    """
    Build full ``regime_portfolio_metrics_v1`` payload.

    ``daily_regime_labels_ffill`` must be aligned to ``daily_asset_returns.index``
    (monthly primary regime forward-filled to each day).
    """

    local_benchmark_daily_by_ticker = local_benchmark_daily_by_ticker or {}

    assets = daily_asset_returns.copy()
    assets.index = pd.DatetimeIndex(assets.index).tz_localize(None).normalize()
    lab = pd.Series(daily_regime_labels_ffill)
    lab.index = pd.DatetimeIndex(lab.index).tz_localize(None).normalize()
    lab = lab.reindex(assets.index)

    combined = assets.copy()
    combined["_regime"] = lab.values
    combined = combined.dropna(subset=["_regime"])
    combined["_regime"] = combined["_regime"].astype(str)

    rf_d = pd.Series(rf_daily)
    rf_d.index = pd.DatetimeIndex(rf_d.index).tz_localize(None).normalize()
    rf_d = rf_d.reindex(combined.index, method="ffill")

    bench_d = pd.Series(benchmark_daily_returns)
    bench_d.index = pd.DatetimeIndex(bench_d.index).tz_localize(None).normalize()
    bench_d = bench_d.reindex(combined.index, method="ffill")

    fa_regimes = (regime_factor_analytics_payload or {}).get("regimes") or {}

    payload: dict[str, Any] = {
        "version": REGIME_PORTFOLIO_METRICS_VERSION,
        "frequency": "daily",
        "annualization_factor": int(REGIME_ANALYTICS_ANNUALIZATION_FACTOR),
        "regime_label_alignment": "monthly_label_forward_filled_to_daily",
        "trading_days_per_year": int(TRADING_DAYS_PER_YEAR),
        "covariance_scaled_to_annual": True,
        "weight_handling": weight_handling_note
        or "weights_renormalized_over_held_assets_present_in_daily_returns_columns",
        "regimes": {},
        "warnings": [],
    }

    for regime in MACRO_PRIMARY_REGIME_NAMES:
        block: dict[str, Any] = {
            "label": regime,
            "n_obs_days": 0,
            "data_start": None,
            "data_end": None,
            "quality_status": "no_observations",
            "portfolio_metrics_available": False,
            "asset_metrics_available": False,
            "covariance_available": False,
            "correlation_available": False,
            "rc_vol_available": False,
            "factor_betas_available": False,
            "factor_rc_available": False,
            "warnings": [],
            "portfolio_metrics": {},
            "asset_metrics": {},
            "asset_covariance": {"available": False},
            "asset_correlation": {"available": False},
            "rc_vol": {},
            "factor_analytics": _slim_factor_block(fa_regimes.get(regime) if isinstance(fa_regimes.get(regime), dict) else None),
        }

        sub = combined[combined["_regime"] == regime].drop(columns=["_regime"])
        held = [str(t) for t in sub.columns if float(weights.get(str(t), 0.0)) > 0.0]
        if not held:
            block["warnings"].append("no_assets_with_positive_weight_in_columns")
            payload["regimes"][regime] = block
            continue

        sub_h = sub[held].dropna(how="any")
        n = int(len(sub_h))
        block["n_obs_days"] = n
        if n == 0:
            block["warnings"].append("no_complete_rows_for_regime_and_held_assets")
            payload["regimes"][regime] = block
            continue

        block["data_start"] = sub_h.index.min().strftime("%Y-%m-%d")
        block["data_end"] = sub_h.index.max().strftime("%Y-%m-%d")
        block["quality_status"] = regime_factor_quality_daily(n)

        w_raw = pd.Series({h: float(weights.get(h, 0.0)) for h in held}, dtype=float)
        s_sum = float(w_raw.sum())
        if s_sum <= 0:
            block["warnings"].append("weight_sum_non_positive")
            payload["regimes"][regime] = block
            continue
        w_eff = w_raw / s_sum

        r_p = sub_h.dot(w_eff.reindex(sub_h.columns).fillna(0.0)).astype(float)
        block["portfolio_metrics"] = _pack_portfolio_metrics(
            r_p, rf_d.reindex(sub_h.index), bench_d.reindex(sub_h.index), mar_daily, n
        )
        block["portfolio_metrics_available"] = bool(n >= 2)

        asset_blocks: dict[str, Any] = {}
        for t in held:
            loc_ser = local_benchmark_daily_by_ticker.get(t)
            asset_blocks[t] = _pack_asset_metrics(
                t,
                sub_h[t].astype(float),
                rf_d.reindex(sub_h.index),
                bench_d.reindex(sub_h.index),
                loc_ser.reindex(sub_h.index) if loc_ser is not None else None,
                mar_daily,
                n,
            )
        block["asset_metrics"] = asset_blocks
        block["asset_metrics_available"] = bool(n >= 2)

        if n >= 2 and len(held) >= 2:
            try:
                cov_d, corr_d, cov_meta = _covariance_with_ledoit_wolf(
                    sub_h[held].astype(float),
                    label=f"regime_portfolio:{regime}",
                )
                cov_ann = cov_d.astype(float) * float(REGIME_ANALYTICS_ANNUALIZATION_FACTOR)
                cov_ann_dict = {
                    str(i): {str(j): float(cov_ann.loc[i, j]) for j in cov_ann.columns}
                    for i in cov_ann.index
                }
                corr_dict = {
                    str(i): {str(j): float(corr_d.loc[i, j]) for j in corr_d.columns}
                    for i in corr_d.index
                }
                block["asset_covariance"] = {
                    "available": True,
                    "covariance": cov_ann_dict,
                    "n_obs": n,
                    **{k: v for k, v in cov_meta.items() if k != "covariance_estimator"},
                    "covariance_estimator": cov_meta.get("covariance_estimator"),
                    "annualization_factor": int(REGIME_ANALYTICS_ANNUALIZATION_FACTOR),
                    "covariance_scaled_to_annual": True,
                }
                block["asset_correlation"] = {
                    "available": True,
                    "correlation": corr_dict,
                    "covariance_estimator": cov_meta.get("covariance_estimator"),
                }
                block["covariance_available"] = True
                block["correlation_available"] = True

                w_np = w_eff.reindex(held).fillna(0.0).to_numpy(dtype=float)
                cov_np = cov_d.reindex(index=held, columns=held).fillna(0.0).to_numpy(dtype=float)
                sigma2 = float(w_np @ cov_np @ w_np)
                if sigma2 > 1e-20 and np.all(np.isfinite(cov_np)):
                    pc = percentage_contributions_variance(w_np, cov_np)
                    block["rc_vol"] = {
                        "available": True,
                        "method": "percentage_contribution_to_variance_fixed_weights_regime_covariance_daily",
                        "sigma2_portfolio_daily": sigma2,
                        "rc_by_asset": {held[i]: float(pc[i]) for i in range(len(held))},
                    }
                    block["rc_vol_available"] = True
                else:
                    block["rc_vol"] = {
                        "available": False,
                        "unavailable_reason": "portfolio_variance_nonpositive_or_singular_covariance",
                    }
            except Exception as exc:
                _LOG.warning("regime_portfolio_metrics: covariance failed (%s): %s", regime, exc)
                block["warnings"].append(f"covariance_error:{exc}")
                block["asset_covariance"] = {"available": False, "unavailable_reason": str(exc)}
                block["asset_correlation"] = {"available": False}
        else:
            block["asset_covariance"] = {
                "available": False,
                "unavailable_reason": "need_n_ge_2_and_at_least_two_assets",
            }
            block["asset_correlation"] = {"available": False}
            block["rc_vol"] = {"available": False, "unavailable_reason": "covariance_unavailable"}

        fa_b = fa_regimes.get(regime)
        if isinstance(fa_b, dict):
            block["factor_betas_available"] = bool(fa_b.get("asset_factor_betas_available"))
            block["factor_rc_available"] = bool(fa_b.get("factor_rc_available"))
            block["factor_analytics"] = _slim_factor_block(fa_b)
        else:
            block["warnings"].append("regime_factor_analytics_block_missing_for_regime")

        payload["regimes"][regime] = block

    return payload


def regime_portfolio_metrics_for_stress_report(full: dict[str, Any]) -> dict[str, Any]:
    """Slim JSON-safe structure for ``stress_report.json`` (omit large nested cov)."""

    if not isinstance(full, dict) or not full:
        return {}

    def _slim_regime(b: dict[str, Any]) -> dict[str, Any]:
        ac = b.get("asset_covariance") or {}
        slim_cov = {k: v for k, v in ac.items() if k != "covariance"}
        ar = b.get("asset_correlation") or {}
        slim_corr = {k: v for k, v in ar.items() if k != "correlation"}
        return {
            "label": b.get("label"),
            "n_obs_days": b.get("n_obs_days"),
            "data_start": b.get("data_start"),
            "data_end": b.get("data_end"),
            "quality_status": b.get("quality_status"),
            "portfolio_metrics_available": b.get("portfolio_metrics_available"),
            "asset_metrics_available": b.get("asset_metrics_available"),
            "covariance_available": b.get("covariance_available"),
            "correlation_available": b.get("correlation_available"),
            "rc_vol_available": b.get("rc_vol_available"),
            "factor_betas_available": b.get("factor_betas_available"),
            "factor_rc_available": b.get("factor_rc_available"),
            "warnings": list(b.get("warnings") or []),
            "portfolio_metrics": b.get("portfolio_metrics"),
            "asset_metrics": b.get("asset_metrics"),
            "asset_covariance": slim_cov,
            "asset_correlation": slim_corr,
            "rc_vol": b.get("rc_vol"),
            "factor_analytics": b.get("factor_analytics"),
        }

    out = {
        "version": full.get("version", REGIME_PORTFOLIO_METRICS_VERSION),
        "frequency": full.get("frequency", "daily"),
        "annualization_factor": full.get("annualization_factor"),
        "regime_label_alignment": full.get("regime_label_alignment"),
        "trading_days_per_year": full.get("trading_days_per_year"),
        "covariance_scaled_to_annual": full.get("covariance_scaled_to_annual"),
        "weight_handling": full.get("weight_handling"),
        "warnings": list(full.get("warnings") or []),
        "regimes": {r: _slim_regime(b) for r, b in (full.get("regimes") or {}).items() if isinstance(b, dict)},
    }
    return out


def regime_portfolio_metrics_summary(full: dict[str, Any]) -> dict[str, Any]:
    """Summary JSON (one row per regime metadata)."""

    if not isinstance(full, dict):
        return {}
    regimes_out: dict[str, Any] = {}
    for r, b in (full.get("regimes") or {}).items():
        if not isinstance(b, dict):
            continue
        pm = b.get("portfolio_metrics") or {}
        cagr = (pm.get("cagr_annual") or {}).get("value")
        vol = (pm.get("vol_annual") or {}).get("value")
        sh = (pm.get("sharpe") or {}).get("value")
        regimes_out[r] = {
            "n_obs_days": b.get("n_obs_days"),
            "quality_status": b.get("quality_status"),
            "data_start": b.get("data_start"),
            "data_end": b.get("data_end"),
            "portfolio_metrics_available": b.get("portfolio_metrics_available"),
            "cagr_annual": cagr,
            "vol_annual": vol,
            "sharpe": sh,
            "covariance_available": b.get("covariance_available"),
            "factor_betas_available": b.get("factor_betas_available"),
            "factor_rc_available": b.get("factor_rc_available"),
            "warnings": list(b.get("warnings") or []),
        }
    return {
        "version": full.get("version", REGIME_PORTFOLIO_METRICS_VERSION),
        "frequency": full.get("frequency", "daily"),
        "annualization_factor": full.get("annualization_factor"),
        "regime_label_alignment": full.get("regime_label_alignment"),
        "regimes": regimes_out,
    }


def regime_portfolio_metrics_csv_frames(full: dict[str, Any]) -> dict[str, pd.DataFrame]:
    """Flatten key outputs to CSV."""

    if not isinstance(full, dict) or not full:
        return {}

    rows_pm: list[dict[str, Any]] = []
    rows_am: list[dict[str, Any]] = []
    rows_rc: list[dict[str, Any]] = []

    common_meta = {
        "rpm_version": full.get("version"),
        "frequency": full.get("frequency"),
        "annualization_factor": full.get("annualization_factor"),
        "regime_label_alignment": full.get("regime_label_alignment"),
        "covariance_scaled_to_annual": full.get("covariance_scaled_to_annual"),
    }

    for regime, b in (full.get("regimes") or {}).items():
        if not isinstance(b, dict):
            continue
        base = {
            **common_meta,
            "regime": regime,
            "n_obs_days": b.get("n_obs_days"),
            "quality_status": b.get("quality_status"),
            "data_start": b.get("data_start"),
            "data_end": b.get("data_end"),
        }
        pm = b.get("portfolio_metrics") or {}
        flat: dict[str, Any] = {**base}
        for mk, mv in pm.items():
            if isinstance(mv, dict):
                flat[f"portfolio_{mk}"] = mv.get("value")
                flat[f"portfolio_{mk}_available"] = mv.get("metric_available")
                flat[f"portfolio_{mk}_reason"] = mv.get("unavailable_reason")
        rows_pm.append(flat)

        for ticker, am in (b.get("asset_metrics") or {}).items():
            row = {**base, "ticker": ticker}
            for mk, mv in (am or {}).items():
                if mk == "ticker":
                    continue
                if isinstance(mv, dict):
                    row[f"asset_{mk}"] = mv.get("value")
                    row[f"asset_{mk}_available"] = mv.get("metric_available")
                    row[f"asset_{mk}_reason"] = mv.get("unavailable_reason")
            rows_am.append(row)

        rc = b.get("rc_vol") or {}
        if isinstance(rc, dict) and rc.get("available"):
            for asset, val in (rc.get("rc_by_asset") or {}).items():
                rows_rc.append({**base, "asset": asset, "rc_vol": val})

    return {
        "regime_portfolio_metrics_portfolio.csv": pd.DataFrame(rows_pm),
        "regime_portfolio_metrics_assets.csv": pd.DataFrame(rows_am),
        "regime_portfolio_metrics_rc_vol.csv": pd.DataFrame(rows_rc),
    }


__all__ = [
    "REGIME_PORTFOLIO_METRICS_VERSION",
    "VAR_ES_MIN_OBS",
    "build_regime_portfolio_metrics",
    "expand_rf_monthly_to_daily",
    "regime_portfolio_metrics_csv_frames",
    "regime_portfolio_metrics_for_stress_report",
    "regime_portfolio_metrics_summary",
]
