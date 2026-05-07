"""
Regime Factor Analytics v1 — diagnostic-only statistical foundation that
consumes the lagged monthly regime labels from ``macro_two_axis_v1`` and the
existing asset/factor return infrastructure to produce, per primary regime:

- asset covariance and correlation matrices (Ledoit–Wolf shrinkage when possible),
- factor covariance and correlation matrices (Ledoit–Wolf when possible; nine-factor model with oil),
- per-asset OLS factor betas with HAC Newey–West inference (monthly or weekly rows),
- bottom-up portfolio factor exposures (weighted sum of asset betas),
- factor variance contribution shares (β_pf' Σ_factor β_pf decomposition),
- average factor moves (mean / median),
- quality / confidence metadata based on sample size (gating 12 / 24 / 60 **month-equivalent**
  when ``frequency='weekly'``: weekly ``n_obs`` is mapped via ``round(n * 12 / 52)``).

The block is **diagnostic-only**: it does not change the macro classifier,
optimizer weights, mandate gates, stress pass/fail, or weight release. See
``docs/exec_plans/2026-05-07_regime_factor_analytics_v1.md`` and
``docs/docs/stress_testing_spec.md`` §8.8.3.
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from src.stress_factors import (
    FACTOR_COLUMN_ORDER,
    FACTOR_TO_BETA_KEY,
    _newey_west_covariance,
    _ols_with_inference,
)
from src.stress_factors_macro import (
    MACRO_PRIMARY_REGIME_NAMES,
    MACRO_REGIME_INSUFFICIENT_MAX_ROWS,
    MACRO_REGIME_RELIABLE_MIN_ROWS,
    MACRO_REGIME_USABLE_MIN_ROWS,
    macro_quality_status,
    macro_regime_obs_month_equivalent,
)

_LOG = logging.getLogger(__name__)

REGIME_FACTOR_ANALYTICS_VERSION = "regime_factor_analytics_v1"
REGIME_FACTOR_HAC_LAG_CAP_MONTHLY = 12
REGIME_FACTOR_HAC_LAG_CAP_WEEKLY = 15

# Portfolio-facing regime statistics use the same 10Y horizon as standard returns /
# metrics / covariance / factor analytics; macro labels may still be computed on
# longer macro history (`regime_label_history_span` in JSON/CSV).
REGIME_FACTOR_PORTFOLIO_WINDOW_NOTE = (
    "macro_two_axis_v1 may emit regime labels over a longer history "
    "(regime_label_history_span) than the portfolio analytics slice; "
    "portfolio_regime_analytics_window is 10Y ending at analysis_end "
    "(~520 weekly or 120 monthly periods), aligned with the standard "
    "return/metrics/covariance/factor horizons."
)


def _finalize_portfolio_regime_window(payload: dict[str, Any], *, freq_norm: str) -> None:
    """Attach actual overlap dates to ``portfolio_regime_analytics_window``."""

    win_in = payload.get("portfolio_regime_analytics_window")
    win: dict[str, Any] = dict(win_in) if isinstance(win_in, dict) else {}
    win["actual_data_start"] = payload.get("data_start")
    win["actual_data_end"] = payload.get("data_end")
    win["actual_n_periods"] = int(payload.get("n_obs_total") or 0)
    win["frequency"] = str(freq_norm)
    payload["portfolio_regime_analytics_window"] = win


def _payload_csv_window_columns(payload: dict[str, Any]) -> dict[str, Any]:
    """Flatten label-history vs portfolio-window metadata for CSV row replication."""

    span = payload.get("regime_label_history_span") or {}
    win = payload.get("portfolio_regime_analytics_window") or {}
    if not isinstance(span, dict):
        span = {}
    if not isinstance(win, dict):
        win = {}
    return {
        "regime_label_history_start": span.get("start"),
        "regime_label_history_end": span.get("end"),
        "regime_label_history_n_months": span.get("n_months"),
        "portfolio_regime_analytics_window_label": win.get("label"),
        "portfolio_regime_analytics_target_months": win.get("target_months"),
        "portfolio_regime_analytics_target_weeks": win.get("target_weeks"),
        "portfolio_regime_analytics_analysis_end": win.get("analysis_end"),
        "portfolio_regime_analytics_actual_start": win.get("actual_data_start"),
        "portfolio_regime_analytics_actual_end": win.get("actual_data_end"),
        "portfolio_regime_analytics_actual_n_periods": win.get("actual_n_periods"),
        "portfolio_regime_analytics_frequency": win.get("frequency"),
        "portfolio_regime_analytics_disclaimer": win.get("disclaimer"),
        "portfolio_regime_analytics_note": payload.get("portfolio_regime_analytics_note"),
    }


def _newey_west_max_lags(n: int, *, cap: int) -> int:
    """Newey–West lag length ``floor(4 * (n/100)^(2/9))``, at least 1, capped."""

    n = max(int(n), 1)
    L = int(np.floor(4.0 * (n / 100.0) ** (2.0 / 9.0)))
    L = max(1, L)
    return min(L, int(cap))


# ---------------------------------------------------------------------------
# Small numeric helpers (kept local so the module is self-contained and easy
# to test).
# ---------------------------------------------------------------------------


def _factor_columns() -> list[str]:
    """Full nine-factor model column order (production 8 + oil)."""

    return list(FACTOR_COLUMN_ORDER)


def _beta_keys_for(factors: list[str]) -> list[str]:
    return [FACTOR_TO_BETA_KEY.get(f, f"beta_{f}") for f in factors]


def _symmetrize(matrix: pd.DataFrame) -> pd.DataFrame:
    if matrix is None or matrix.empty:
        return matrix
    arr = matrix.values.astype(float)
    sym = 0.5 * (arr + arr.T)
    return pd.DataFrame(sym, index=matrix.index, columns=matrix.columns)


def _correlation_from_covariance(cov: pd.DataFrame) -> pd.DataFrame:
    if cov is None or cov.empty:
        return cov
    vals = cov.values.astype(float)
    diag = np.diag(vals).copy()
    diag = np.where(diag <= 0.0, 0.0, diag)
    vol = np.sqrt(diag)
    n = vals.shape[0]
    out = np.zeros_like(vals)
    for i in range(n):
        for j in range(n):
            den = vol[i] * vol[j]
            if den > 1e-20:
                out[i, j] = vals[i, j] / den
            elif i == j:
                out[i, j] = 1.0
            else:
                out[i, j] = 0.0
    out = np.clip(out, -1.0, 1.0)
    np.fill_diagonal(out, 1.0)
    return pd.DataFrame(out, index=cov.index, columns=cov.columns)


def _matrix_to_nested(df: pd.DataFrame) -> dict[str, dict[str, float]]:
    if df is None or df.empty:
        return {}
    return {
        str(i): {str(j): float(df.loc[i, j]) for j in df.columns}
        for i in df.index
    }


def _is_psd(matrix: pd.DataFrame, *, tol: float = -1e-9) -> bool:
    if matrix is None or matrix.empty:
        return True
    arr = matrix.values.astype(float)
    if not np.isfinite(arr).all():
        return False
    arr = 0.5 * (arr + arr.T)
    try:
        eig = np.linalg.eigvalsh(arr)
    except np.linalg.LinAlgError:
        return False
    return bool(np.min(eig) >= tol)


def _covariance_with_ledoit_wolf(
    df: pd.DataFrame,
    *,
    label: str,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Estimate covariance with Ledoit–Wolf on complete-case rows when possible.

    Uses :class:`sklearn.covariance.LedoitWolf` on ``df.dropna(how="any")`` when
    that frame has at least two rows. On failure or too little data, falls back to
    the pandas sample covariance of ``df`` (``ddof=1``, pairwise for missing).
    """

    from sklearn.covariance import LedoitWolf

    meta: dict[str, Any] = {
        "covariance_estimator": "sample_ddof1_pairwise",
        "covariance_rows_used": int(len(df)),
        "cov_complete_case_rows": 0,
        "ledoit_wolf_shrinkage": None,
    }

    if df is None or df.empty:
        raise ValueError("covariance input frame is empty")

    cols = list(df.columns)
    complete = df[cols].dropna(how="any")
    n_complete = int(len(complete))
    meta["cov_complete_case_rows"] = n_complete

    if n_complete >= 2:
        X = complete.to_numpy(dtype=float)
        try:
            lw = LedoitWolf(assume_centered=False).fit(X)
            cov = pd.DataFrame(lw.covariance_, index=cols, columns=cols)
            cov = _symmetrize(cov)
            corr = _correlation_from_covariance(cov)
            meta["covariance_estimator"] = "ledoit_wolf"
            meta["covariance_rows_used"] = n_complete
            meta["ledoit_wolf_shrinkage"] = float(lw.shrinkage_)
            return cov, corr, meta
        except Exception as exc:  # pragma: no cover - defensive
            _LOG.warning(
                "regime_factor_analytics: Ledoit-Wolf failed (%s, n_complete=%s, n_features=%s): %s",
                label,
                n_complete,
                len(cols),
                exc,
            )
            cov = _symmetrize(complete.cov(ddof=1))
            meta["covariance_estimator"] = "sample_ddof1_complete_case"
            meta["covariance_rows_used"] = n_complete
            corr = _correlation_from_covariance(cov)
            return cov, corr, meta

    cov = _symmetrize(df[cols].cov(ddof=1))
    corr = _correlation_from_covariance(cov)
    meta["covariance_rows_used"] = int(len(df))
    return cov, corr, meta


# ---------------------------------------------------------------------------
# Core per-regime estimators.
# ---------------------------------------------------------------------------


def _ols_with_hac_inference(
    y: np.ndarray,
    X: np.ndarray,
    *,
    max_lags: int,
    alpha: float = 0.05,
) -> dict[str, Any] | None:
    """OLS with HAC Newey–West inference (Bartlett kernel).

    Returns ``None`` when there are too few rows for stable inference.
    The output structure mirrors ``_ols_with_inference`` plus a ``hac_inference``
    sub-block with HAC SE, t, p, and CI for the intercept and every regressor.
    """

    base = _ols_with_inference(y, X, add_const=True, alpha=alpha)
    if not base:
        return None
    Xa = np.asarray(X, dtype=float)
    Z = np.column_stack([np.ones(len(Xa)), Xa])
    params = np.asarray(base["params"], dtype=float)
    resid = np.asarray(y, dtype=float).ravel() - Z @ params
    L = max(int(max_lags), 1)
    cov_hac = _newey_west_covariance(Z, resid, L)
    se_hac = np.sqrt(np.maximum(np.diag(cov_hac), 0.0))
    df_resid = int(base.get("df_resid", max(len(y) - Z.shape[1], 1)))
    with np.errstate(divide="ignore", invalid="ignore"):
        t_hac = np.where(se_hac > 0.0, params / se_hac, 0.0)
    p_hac = 2.0 * stats.t.sf(np.abs(t_hac), df=max(df_resid, 1))
    tcrit_hac = float(stats.t.ppf(1.0 - alpha / 2.0, df=max(df_resid, 1)))
    ci_low_hac = params - tcrit_hac * se_hac
    ci_high_hac = params + tcrit_hac * se_hac
    return {
        **base,
        "hac": {
            "se_type": "hac_newey_west",
            "kernel": "bartlett",
            "max_lags": int(L),
            "se": se_hac.astype(float),
            "t": t_hac.astype(float),
            "p": p_hac.astype(float),
            "ci_low": ci_low_hac.astype(float),
            "ci_high": ci_high_hac.astype(float),
        },
    }


def _asset_factor_beta_row(
    *,
    asset: str,
    y: pd.Series,
    X: pd.DataFrame,
    factor_cols: list[str],
    beta_keys: list[str],
    max_lags: int,
    frequency: str = "monthly",
) -> dict[str, Any] | None:
    """Run a single per-asset OLS with HAC inference inside one regime."""

    aligned = pd.concat([y.rename("__y__"), X.loc[:, factor_cols]], axis=1).dropna()
    n = int(len(aligned))
    n_gate = macro_regime_obs_month_equivalent(n, frequency=frequency)
    if n_gate < MACRO_REGIME_INSUFFICIENT_MAX_ROWS:
        return {
            "asset": asset,
            "n_obs": n,
            "quality_status": macro_quality_status(n, frequency=frequency),
            "available": False,
            "reason": "insufficient_data",
        }
    yv = aligned["__y__"].to_numpy(dtype=float)
    Xv = aligned.loc[:, factor_cols].to_numpy(dtype=float)
    out = _ols_with_hac_inference(yv, Xv, max_lags=max_lags)
    if out is None:
        return {
            "asset": asset,
            "n_obs": n,
            "quality_status": macro_quality_status(n, frequency=frequency),
            "available": False,
            "reason": "ols_failed",
        }
    params = out["params"]
    cls_t = out["t"]
    cls_p = out["p"]
    cls_ci_low = out["ci_low"]
    cls_ci_high = out["ci_high"]
    hac = out["hac"]
    quality = macro_quality_status(n, frequency=frequency)
    not_for_optimization = quality in {"insufficient_data", "low_confidence"}
    return {
        "asset": asset,
        "n_obs": n,
        "quality_status": quality,
        "available": True,
        "not_for_optimization": bool(not_for_optimization),
        "alpha": float(params[0]),
        "betas": {bk: float(v) for bk, v in zip(beta_keys, params[1:])},
        "se_classic": {bk: float(v) for bk, v in zip(["intercept", *beta_keys], out["se"])},
        "t_classic": {bk: float(v) for bk, v in zip(["intercept", *beta_keys], cls_t)},
        "p_classic": {bk: float(v) for bk, v in zip(["intercept", *beta_keys], cls_p)},
        "ci_low_classic": {bk: float(v) for bk, v in zip(["intercept", *beta_keys], cls_ci_low)},
        "ci_high_classic": {bk: float(v) for bk, v in zip(["intercept", *beta_keys], cls_ci_high)},
        "r2": float(out["r2"]),
        "adj_r2": float(out["adj_r2"]),
        "idiosyncratic_risk": float(out.get("idiosyncratic_risk", float("nan"))),
        "hac_inference": {
            "se_type": hac["se_type"],
            "kernel": hac["kernel"],
            "max_lags": int(hac["max_lags"]),
            "se": {bk: float(v) for bk, v in zip(["intercept", *beta_keys], hac["se"])},
            "t": {bk: float(v) for bk, v in zip(["intercept", *beta_keys], hac["t"])},
            "p": {bk: float(v) for bk, v in zip(["intercept", *beta_keys], hac["p"])},
            "ci_low": {bk: float(v) for bk, v in zip(["intercept", *beta_keys], hac["ci_low"])},
            "ci_high": {bk: float(v) for bk, v in zip(["intercept", *beta_keys], hac["ci_high"])},
        },
    }


def _asset_covariance_block(
    asset_returns: pd.DataFrame,
    *,
    regime: str,
    n_obs: int,
    frequency: str = "monthly",
) -> dict[str, Any]:
    n_gate = macro_regime_obs_month_equivalent(int(n_obs), frequency=frequency)
    if (
        asset_returns is None
        or asset_returns.empty
        or n_gate < MACRO_REGIME_INSUFFICIENT_MAX_ROWS
    ):
        return {"available": False, "n_obs": int(n_obs)}
    cleaned = asset_returns.dropna(axis=1, how="all")
    if cleaned.shape[1] < 2:
        return {
            "available": False,
            "n_obs": int(n_obs),
            "reason": "fewer_than_two_assets_with_data",
        }
    cov, corr, cov_meta = _covariance_with_ledoit_wolf(cleaned, label=f"asset:{regime}")
    out = {
        "available": True,
        "n_obs": int(n_obs),
        "assets": list(cleaned.columns),
        "covariance": _matrix_to_nested(cov),
        "correlation": _matrix_to_nested(corr),
        "psd_status": "psd" if _is_psd(cov) else "not_psd",
        "diagonal_max_abs_dev": float(
            np.max(np.abs(np.diag(corr.values) - 1.0)) if corr.size else 0.0
        ),
        **cov_meta,
    }
    return out


def _factor_covariance_block(
    factors: pd.DataFrame,
    *,
    regime: str,
    n_obs: int,
    factor_cols: list[str],
    frequency: str = "monthly",
) -> dict[str, Any]:
    n_gate = macro_regime_obs_month_equivalent(int(n_obs), frequency=frequency)
    if factors is None or factors.empty or n_gate < MACRO_REGIME_INSUFFICIENT_MAX_ROWS:
        return {"available": False, "n_obs": int(n_obs), "factors": list(factor_cols)}
    cleaned = factors.reindex(columns=factor_cols)
    cov, corr, cov_meta = _covariance_with_ledoit_wolf(cleaned, label=f"factor:{regime}")
    return {
        "available": True,
        "n_obs": int(n_obs),
        "factors": list(factor_cols),
        "covariance": _matrix_to_nested(cov),
        "correlation": _matrix_to_nested(corr),
        "psd_status": "psd" if _is_psd(cov) else "not_psd",
        **cov_meta,
    }


def _bottom_up_portfolio_betas(
    asset_betas: dict[str, dict[str, Any]],
    weights: dict[str, float] | None,
    *,
    beta_keys: list[str],
) -> tuple[dict[str, float], float]:
    """Return ``(beta_pf, weights_coverage)``.

    ``beta_pf`` keys follow ``beta_keys``; missing assets contribute zero. The
    coverage is the sum of weights across assets that produced a usable beta row.
    """

    weights = weights or {}
    pf = {bk: 0.0 for bk in beta_keys}
    coverage = 0.0
    for ticker, row in asset_betas.items():
        if not row.get("available"):
            continue
        w = float(weights.get(ticker, 0.0))
        if w == 0.0:
            continue
        coverage += w
        betas = row.get("betas") or {}
        for bk in beta_keys:
            pf[bk] += w * float(betas.get(bk, 0.0))
    return pf, float(coverage)


def _factor_variance_contribution(
    beta_pf: dict[str, float],
    factor_cov: pd.DataFrame,
    *,
    factor_cols: list[str],
    beta_keys: list[str],
) -> dict[str, Any]:
    """β_pf' · Σ · β_pf decomposed into per-factor mc / share / sign."""

    if factor_cov is None or factor_cov.empty:
        return {
            "available": False,
            "total_factor_variance": 0.0,
            "rows": [],
            "top_dominant_factor": None,
        }
    vec = np.array([float(beta_pf.get(bk, 0.0)) for bk in beta_keys], dtype=float)
    cov_mat = factor_cov.reindex(index=factor_cols, columns=factor_cols).fillna(0.0).values
    cov_mat = 0.5 * (cov_mat + cov_mat.T)
    total = float(vec @ cov_mat @ vec)
    total = max(total, 0.0)
    mc = vec * (cov_mat @ vec)
    rows: list[dict[str, Any]] = []
    abs_total = float(np.sum(np.abs(mc)))
    for i, factor in enumerate(factor_cols):
        contribution = float(mc[i])
        if total > 1e-20:
            share = float(contribution / total)
        elif abs_total > 1e-20:
            share = float(contribution / abs_total)
        else:
            share = 0.0
        if contribution > 1e-20:
            sign = "positive"
        elif contribution < -1e-20:
            sign = "negative"
        else:
            sign = "zero"
        rows.append(
            {
                "factor": str(factor),
                "beta_key": beta_keys[i],
                "factor_variance_contribution": contribution,
                "factor_risk_contribution_share": share,
                "factor_risk_contribution_sign": sign,
            }
        )
    top_factor = None
    if rows:
        top_factor = max(rows, key=lambda r: abs(r.get("factor_risk_contribution_share", 0.0)))[
            "factor"
        ]
    return {
        "available": True,
        "total_factor_variance": total,
        "rows": rows,
        "top_dominant_factor": top_factor,
    }


def _factor_average_moves(
    factors: pd.DataFrame,
    *,
    factor_cols: list[str],
) -> list[dict[str, Any]]:
    if factors is None or factors.empty:
        return []
    rows: list[dict[str, Any]] = []
    for f in factor_cols:
        if f not in factors.columns:
            continue
        col = factors[f].dropna()
        if col.empty:
            rows.append({"factor": f, "mean": float("nan"), "median": float("nan"), "n_obs": 0})
            continue
        rows.append(
            {
                "factor": f,
                "mean": float(col.mean()),
                "median": float(col.median()),
                "n_obs": int(len(col)),
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Top-level pipeline.
# ---------------------------------------------------------------------------


def _coerce_index_to_naive_timestamps(idx: pd.Index) -> pd.DatetimeIndex:
    return pd.to_datetime(idx).tz_localize(None) if getattr(idx, "tz", None) else pd.to_datetime(idx)


def _align_inputs(
    monthly_returns: pd.DataFrame,
    monthly_factor_returns: pd.DataFrame,
    regime_labels: pd.Series,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.DatetimeIndex]:
    if monthly_returns is None or monthly_returns.empty:
        raise ValueError("monthly_returns is empty")
    if monthly_factor_returns is None or monthly_factor_returns.empty:
        raise ValueError("monthly_factor_returns is empty")
    if regime_labels is None or len(regime_labels) == 0:
        raise ValueError("regime_labels is empty")

    asset_idx = pd.Index(_coerce_index_to_naive_timestamps(monthly_returns.index)).normalize()
    factor_idx = pd.Index(_coerce_index_to_naive_timestamps(monthly_factor_returns.index)).normalize()
    label_idx = pd.Index(_coerce_index_to_naive_timestamps(regime_labels.index)).normalize()

    asset_df = monthly_returns.copy()
    asset_df.index = asset_idx
    factor_df = monthly_factor_returns.copy()
    factor_df.index = factor_idx
    labels = pd.Series(regime_labels.values, index=label_idx, name="regime").dropna()
    labels = labels.astype(str)

    common = asset_df.index.intersection(factor_df.index).intersection(labels.index).sort_values()
    return asset_df.reindex(common), factor_df.reindex(common), labels.reindex(common), common


def _format_date(ts: Any) -> str | None:
    if ts is None:
        return None
    try:
        return pd.Timestamp(ts).strftime("%Y-%m-%d")
    except Exception:
        return None


def _empty_regime_block(regime: str) -> dict[str, Any]:
    return {
        "label": regime,
        "n_obs": 0,
        "quality_status": "no_observations",
        "not_for_optimization": True,
        "available": False,
        "asset_covariance_available": False,
        "factor_covariance_available": False,
        "asset_factor_betas_available": False,
        "factor_rc_available": False,
        "data_start": None,
        "data_end": None,
        "asset_covariance": {"available": False, "n_obs": 0},
        "factor_covariance": {"available": False, "n_obs": 0, "factors": _factor_columns()},
        "asset_factor_betas": {},
        "portfolio_factor_exposure": {
            "available": False,
            "betas": {bk: 0.0 for bk in _beta_keys_for(_factor_columns())},
            "weights_coverage": 0.0,
        },
        "factor_variance_contribution": {
            "available": False,
            "total_factor_variance": 0.0,
            "rows": [],
            "top_dominant_factor": None,
        },
        "factor_average_moves": [],
        "dominant_factors": [],
        "warnings": [],
        "transition_split": None,
        "confidence_split": None,
    }


def _compute_regime_block(
    regime: str,
    *,
    regime_dates: pd.DatetimeIndex,
    asset_returns: pd.DataFrame,
    factor_returns: pd.DataFrame,
    factor_cols: list[str],
    beta_keys: list[str],
    weights: dict[str, float] | None,
    hac_lag_cap: int,
    frequency: str = "monthly",
    transition_split: str | None = None,
    confidence_split: str | None = None,
) -> dict[str, Any]:
    n = int(len(regime_dates))
    quality = macro_quality_status(n, frequency=frequency)
    n_gate = macro_regime_obs_month_equivalent(n, frequency=frequency)
    block = _empty_regime_block(regime)
    block["transition_split"] = transition_split
    block["confidence_split"] = confidence_split
    block["not_for_optimization"] = quality in {"insufficient_data", "low_confidence", "no_observations"}
    if n <= 0:
        return block
    block["data_start"] = _format_date(regime_dates.min())
    block["data_end"] = _format_date(regime_dates.max())
    block["n_obs"] = n
    block["quality_status"] = quality
    max_lags = _newey_west_max_lags(n, cap=hac_lag_cap)
    block["hac_max_lags"] = int(max_lags)

    if n_gate < MACRO_REGIME_INSUFFICIENT_MAX_ROWS:
        block["warnings"].append(
            "Insufficient history for regime bucket (below ~12 month-equivalent observations; "
            "for weekly analytics, n_obs counts weeks). Estimates suppressed."
        )
        return block

    block["available"] = True
    not_for_optimization = quality in {"insufficient_data", "low_confidence"}
    block["not_for_optimization"] = bool(not_for_optimization)
    if quality == "low_confidence":
        block["warnings"].append(
            "Low confidence (~12–23 month-equivalent observations); regime estimates not for optimization."
        )

    a_slice = asset_returns.reindex(regime_dates)
    f_slice = factor_returns.reindex(regime_dates).loc[:, factor_cols]

    block["asset_covariance"] = _asset_covariance_block(
        a_slice, regime=regime, n_obs=n, frequency=frequency
    )
    block["asset_covariance_available"] = bool(block["asset_covariance"].get("available"))

    block["factor_covariance"] = _factor_covariance_block(
        f_slice, regime=regime, n_obs=n, factor_cols=factor_cols, frequency=frequency
    )
    block["factor_covariance_available"] = bool(block["factor_covariance"].get("available"))

    asset_betas: dict[str, dict[str, Any]] = {}
    for ticker in a_slice.columns:
        col = a_slice[ticker]
        if col.dropna().empty:
            continue
        row = _asset_factor_beta_row(
            asset=str(ticker),
            y=col,
            X=f_slice,
            factor_cols=factor_cols,
            beta_keys=beta_keys,
            max_lags=max_lags,
            frequency=frequency,
        )
        if row is not None:
            asset_betas[str(ticker)] = row

    block["asset_factor_betas"] = asset_betas
    block["asset_factor_betas_available"] = any(
        r.get("available") for r in asset_betas.values()
    )

    pf_betas, coverage = _bottom_up_portfolio_betas(asset_betas, weights, beta_keys=beta_keys)
    block["portfolio_factor_exposure"] = {
        "available": bool(block["asset_factor_betas_available"]),
        "betas": pf_betas,
        "weights_coverage": coverage,
    }

    factor_cov_df = pd.DataFrame()
    if block["factor_covariance_available"]:
        factor_cov_df = pd.DataFrame(
            block["factor_covariance"]["covariance"]
        ).reindex(index=factor_cols, columns=factor_cols).fillna(0.0)

    block["factor_variance_contribution"] = _factor_variance_contribution(
        pf_betas,
        factor_cov_df,
        factor_cols=factor_cols,
        beta_keys=beta_keys,
    )
    block["factor_rc_available"] = bool(
        block["factor_variance_contribution"].get("available")
        and block["factor_covariance_available"]
        and block["asset_factor_betas_available"]
    )

    block["factor_average_moves"] = _factor_average_moves(f_slice, factor_cols=factor_cols)

    if block["factor_variance_contribution"].get("rows"):
        ranked = sorted(
            block["factor_variance_contribution"]["rows"],
            key=lambda r: abs(r.get("factor_risk_contribution_share", 0.0)),
            reverse=True,
        )
        block["dominant_factors"] = [r["factor"] for r in ranked[:3]]

    return block


def regime_factor_analytics(
    *,
    monthly_returns: pd.DataFrame,
    monthly_factor_returns: pd.DataFrame,
    regime_labels: pd.Series,
    transition_flag: pd.Series | None = None,
    confidence_level: pd.Series | None = None,
    weights: dict[str, float] | None = None,
    enable_transition_split: bool = False,
    enable_confidence_split: bool = False,
    frequency: str = "monthly",
    weekly_alignment: str = "forward_fill_monthly_label",
    regime_label_history_span: dict[str, Any] | None = None,
    portfolio_regime_analytics_window: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute the full ``regime_factor_analytics_v1`` payload.

    Parameters
    ----------
    monthly_returns:
        DataFrame indexed by month-end timestamps. Columns are tickers; values
        are FX-converted simple returns (the same frame ``run_report.py`` uses).
        When ``frequency='weekly'`` the caller must pass a weekly DataFrame
        whose index is Friday week-end timestamps; the function does not
        auto-resample.
    monthly_factor_returns:
        DataFrame indexed by the same frequency as ``monthly_returns``. Columns
        must include the nine production factors plus oil; missing columns are
        filled with zeros to keep the matrix square.
    regime_labels:
        Series of primary regime strings indexed by the matching frequency.
        Labels must already be lagged (the macro pipeline applies a 1-month
        publication lag).
    transition_flag, confidence_level:
        Optional per-row Series for split analyses.
    weights:
        Current portfolio weights. Used only for the bottom-up portfolio factor
        exposure and the variance contribution decomposition.
    regime_label_history_span:
        Optional metadata for the **full** monthly regime label series (e.g. first/
        last scored month and count). Does not change alignment; for disclosure only.
    portfolio_regime_analytics_window:
        Optional metadata describing the fixed **10Y** portfolio analytics horizon
        (targets, ``analysis_end``, disclaimer). ``actual_*`` fields are filled
        from the realized overlap before return.
    """

    factor_cols = _factor_columns()
    beta_keys = _beta_keys_for(factor_cols)
    warnings: list[str] = []

    freq_norm = (frequency or "monthly").strip().lower()
    if freq_norm not in {"monthly", "weekly"}:
        raise ValueError(
            f"Unsupported frequency: {frequency!r}; expected 'monthly' or 'weekly'."
        )
    hac_lag_cap = (
        REGIME_FACTOR_HAC_LAG_CAP_WEEKLY
        if freq_norm == "weekly"
        else REGIME_FACTOR_HAC_LAG_CAP_MONTHLY
    )
    weekly_alignment_value = weekly_alignment if freq_norm == "weekly" else None

    if monthly_factor_returns is not None and not monthly_factor_returns.empty:
        ff = monthly_factor_returns.copy()
        for col in factor_cols:
            if col not in ff.columns:
                ff[col] = 0.0
                warnings.append(f"factor_column_missing:{col}")
        monthly_factor_returns = ff[factor_cols]

    if freq_norm == "weekly" and weekly_alignment_value == "forward_fill_monthly_label":
        # Forward-fill the most recent monthly regime label onto each weekly
        # timestamp present in monthly_returns / monthly_factor_returns.
        target_index = pd.Index(
            _coerce_index_to_naive_timestamps(monthly_returns.index)
        ).normalize().sort_values()
        labels_naive = pd.Series(
            regime_labels.values,
            index=pd.Index(_coerce_index_to_naive_timestamps(regime_labels.index)).normalize(),
            name="regime",
        ).dropna().astype(str).sort_index()
        regime_labels = labels_naive.reindex(target_index, method="ffill")
        if transition_flag is not None:
            tf_ff = pd.Series(
                transition_flag.values,
                index=pd.Index(
                    _coerce_index_to_naive_timestamps(transition_flag.index)
                ).normalize(),
                name="transition_flag",
            ).sort_index()
            transition_flag = tf_ff.reindex(target_index, method="ffill")
        if confidence_level is not None:
            cl_ff = pd.Series(
                confidence_level.values,
                index=pd.Index(
                    _coerce_index_to_naive_timestamps(confidence_level.index)
                ).normalize(),
                name="confidence_level",
            ).sort_index()
            confidence_level = cl_ff.reindex(target_index, method="ffill")

    asset_aligned, factor_aligned, label_aligned, common_index = _align_inputs(
        monthly_returns, monthly_factor_returns, regime_labels
    )

    weights_used = {str(k): float(v) for k, v in (weights or {}).items() if v}
    weights_total = float(sum(weights_used.values())) if weights_used else 0.0

    payload: dict[str, Any] = {
        "version": REGIME_FACTOR_ANALYTICS_VERSION,
        "frequency": freq_norm,
        "weekly_alignment": weekly_alignment_value,
        "factor_order": factor_cols,
        "beta_order": beta_keys,
        "data_start": _format_date(common_index.min()) if len(common_index) else None,
        "data_end": _format_date(common_index.max()) if len(common_index) else None,
        "n_obs_total": int(len(common_index)),
        "weights_used": weights_used,
        "weights_sum": weights_total,
        "weights_coverage": 0.0,
        "regimes": {},
        "splits": {"transition": {}, "confidence": {}},
        "warnings": warnings,
        "hac_lag_cap": int(hac_lag_cap),
    }
    if regime_label_history_span:
        payload["regime_label_history_span"] = {
            k: v for k, v in regime_label_history_span.items() if v is not None
        }
    if portfolio_regime_analytics_window:
        payload["portfolio_regime_analytics_window"] = dict(portfolio_regime_analytics_window)
    payload["portfolio_regime_analytics_note"] = REGIME_FACTOR_PORTFOLIO_WINDOW_NOTE

    if asset_aligned.empty or factor_aligned.empty or label_aligned.empty:
        for regime in MACRO_PRIMARY_REGIME_NAMES:
            payload["regimes"][regime] = _empty_regime_block(regime)
        payload["warnings"].append(
            "no_overlap_between_asset_returns_factor_returns_and_regime_labels"
        )
        _finalize_portfolio_regime_window(payload, freq_norm=freq_norm)
        return payload

    # Ensure transition / confidence series, when provided, are aligned to the
    # same common index.
    if transition_flag is not None:
        tf_naive = pd.Series(
            transition_flag.values,
            index=pd.Index(_coerce_index_to_naive_timestamps(transition_flag.index)).normalize(),
            name="transition_flag",
        ).reindex(common_index)
    else:
        tf_naive = None
    if confidence_level is not None:
        cl_naive = pd.Series(
            confidence_level.values,
            index=pd.Index(_coerce_index_to_naive_timestamps(confidence_level.index)).normalize(),
            name="confidence_level",
        ).reindex(common_index)
    else:
        cl_naive = None

    primary_coverage_total = 0.0
    primary_n_total = 0
    for regime in MACRO_PRIMARY_REGIME_NAMES:
        regime_dates = label_aligned.index[label_aligned.values == regime]
        block = _compute_regime_block(
            regime,
            regime_dates=regime_dates,
            asset_returns=asset_aligned,
            factor_returns=factor_aligned,
            factor_cols=factor_cols,
            beta_keys=beta_keys,
            weights=weights_used,
            hac_lag_cap=hac_lag_cap,
            frequency=freq_norm,
        )
        payload["regimes"][regime] = block
        primary_coverage_total += float(
            block.get("portfolio_factor_exposure", {}).get("weights_coverage", 0.0)
        )
        primary_n_total += int(block.get("n_obs", 0))

    if primary_n_total > 0:
        payload["weights_coverage"] = float(primary_coverage_total / 4.0)

    if enable_transition_split:
        if tf_naive is None:
            payload["warnings"].append(
                "transition_split_requested_without_per_month_transition_flag"
            )
        else:
            split_section: dict[str, dict[str, Any]] = {}
            for regime in MACRO_PRIMARY_REGIME_NAMES:
                for flag in (False, True):
                    mask = (label_aligned.values == regime) & (tf_naive.fillna(False).values == flag)
                    sub_dates = label_aligned.index[mask]
                    if len(sub_dates) == 0:
                        continue
                    key = f"{regime}__transition_{'true' if flag else 'false'}"
                    block = _compute_regime_block(
                        regime,
                        regime_dates=sub_dates,
                        asset_returns=asset_aligned,
                        factor_returns=factor_aligned,
                        factor_cols=factor_cols,
                        beta_keys=beta_keys,
                        weights=weights_used,
                        hac_lag_cap=hac_lag_cap,
                        frequency=freq_norm,
                        transition_split="transition" if flag else "non_transition",
                    )
                    split_section[key] = block
            payload["splits"]["transition"] = split_section

    if enable_confidence_split:
        if cl_naive is None:
            payload["warnings"].append(
                "confidence_split_requested_without_per_month_confidence_level"
            )
        else:
            split_section = {}
            for regime in MACRO_PRIMARY_REGIME_NAMES:
                for level in sorted({str(v) for v in cl_naive.dropna().unique() if str(v)}):
                    mask = (label_aligned.values == regime) & (cl_naive.fillna("").astype(str).values == level)
                    sub_dates = label_aligned.index[mask]
                    if len(sub_dates) == 0:
                        continue
                    key = f"{regime}__conf_{level}"
                    block = _compute_regime_block(
                        regime,
                        regime_dates=sub_dates,
                        asset_returns=asset_aligned,
                        factor_returns=factor_aligned,
                        factor_cols=factor_cols,
                        beta_keys=beta_keys,
                        weights=weights_used,
                        hac_lag_cap=hac_lag_cap,
                        frequency=freq_norm,
                        confidence_split=level,
                    )
                    split_section[key] = block
            payload["splits"]["confidence"] = split_section

    _finalize_portfolio_regime_window(payload, freq_norm=freq_norm)
    return payload


# ---------------------------------------------------------------------------
# CSV builders + summary JSON.
# ---------------------------------------------------------------------------


_REQUIRED_META_COLUMNS = (
    "regime",
    "n_obs",
    "quality_status",
    "transition_split",
    "confidence_split",
    "data_start",
    "data_end",
)


def _iter_blocks(payload: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Yield (regime_key, block) for the primary path and any splits."""

    out: list[tuple[str, dict[str, Any]]] = []
    for regime, block in (payload.get("regimes") or {}).items():
        if isinstance(block, dict):
            out.append((str(regime), block))
    for kind in ("transition", "confidence"):
        section = (payload.get("splits") or {}).get(kind) or {}
        for key, block in section.items():
            if isinstance(block, dict):
                out.append((str(key), block))
    return out


def _meta_row(block: dict[str, Any], regime_key: str) -> dict[str, Any]:
    label = str(block.get("label", regime_key))
    return {
        "regime": label if "__" not in regime_key else regime_key,
        "n_obs": int(block.get("n_obs", 0) or 0),
        "quality_status": str(block.get("quality_status", "no_observations")),
        "not_for_optimization": bool(block.get("not_for_optimization", True)),
        "transition_split": block.get("transition_split"),
        "confidence_split": block.get("confidence_split"),
        "data_start": block.get("data_start"),
        "data_end": block.get("data_end"),
        "hac_max_lags": block.get("hac_max_lags"),
    }


def _split_group_key(meta: dict[str, Any]) -> tuple[Any, Any, Any]:
    return (meta.get("regime"), meta.get("transition_split"), meta.get("confidence_split"))


def _covariance_csv_meta(block_cov: dict[str, Any] | None) -> dict[str, Any]:
    """Columns replicated on each long-form covariance / correlation CSV row."""

    if not isinstance(block_cov, dict):
        return {
            "covariance_estimator": None,
            "covariance_rows_used": None,
            "cov_complete_case_rows": None,
            "ledoit_wolf_shrinkage": None,
        }
    return {
        "covariance_estimator": block_cov.get("covariance_estimator"),
        "covariance_rows_used": block_cov.get("covariance_rows_used"),
        "cov_complete_case_rows": block_cov.get("cov_complete_case_rows"),
        "ledoit_wolf_shrinkage": block_cov.get("ledoit_wolf_shrinkage"),
    }


def _flatten_matrix(
    nested: dict[str, dict[str, float]],
    *,
    row_label: str,
    col_label: str,
    value_label: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for i, row in (nested or {}).items():
        for j, val in (row or {}).items():
            rows.append({row_label: str(i), col_label: str(j), value_label: float(val)})
    return rows


def regime_factor_analytics_csv_frames(
    payload: dict[str, Any],
) -> dict[str, pd.DataFrame]:
    """Flatten the payload into the eight CSV frames expected by the report."""

    if not isinstance(payload, dict) or not payload:
        return {}

    gmeta = _payload_csv_window_columns(payload)

    rows_asset_cov: list[dict[str, Any]] = []
    rows_asset_corr: list[dict[str, Any]] = []
    rows_factor_cov: list[dict[str, Any]] = []
    rows_factor_corr: list[dict[str, Any]] = []
    rows_betas: list[dict[str, Any]] = []
    rows_pf_exposure: list[dict[str, Any]] = []
    rows_var_contrib: list[dict[str, Any]] = []
    rows_avg_moves: list[dict[str, Any]] = []

    factor_order = list(payload.get("factor_order") or _factor_columns())
    beta_keys = list(payload.get("beta_order") or _beta_keys_for(factor_order))

    gk_asset_cov: set[tuple[Any, Any, Any]] = set()
    gk_asset_corr: set[tuple[Any, Any, Any]] = set()
    gk_factor_cov: set[tuple[Any, Any, Any]] = set()
    gk_factor_corr: set[tuple[Any, Any, Any]] = set()
    gk_betas: set[tuple[Any, Any, Any]] = set()
    gk_var: set[tuple[Any, Any, Any]] = set()
    gk_avg: set[tuple[Any, Any, Any]] = set()

    for regime_key, block in _iter_blocks(payload):
        meta = {**gmeta, **_meta_row(block, regime_key)}
        gk = _split_group_key(meta)
        a_cov = block.get("asset_covariance") or {}
        acm = _covariance_csv_meta(a_cov if a_cov.get("available") else None)
        if a_cov.get("available"):
            cov_mat = _flatten_matrix(
                a_cov.get("covariance", {}),
                row_label="asset_i",
                col_label="asset_j",
                value_label="covariance",
            )
            if cov_mat:
                gk_asset_cov.add(gk)
            for r in cov_mat:
                rows_asset_cov.append({**meta, **acm, **r})
            corr_mat = _flatten_matrix(
                a_cov.get("correlation", {}),
                row_label="asset_i",
                col_label="asset_j",
                value_label="correlation",
            )
            if corr_mat:
                gk_asset_corr.add(gk)
            for r in corr_mat:
                rows_asset_corr.append({**meta, **acm, **r})
        f_cov = block.get("factor_covariance") or {}
        fcm = _covariance_csv_meta(f_cov if f_cov.get("available") else None)
        if f_cov.get("available"):
            cov_mat = _flatten_matrix(
                f_cov.get("covariance", {}),
                row_label="factor_i",
                col_label="factor_j",
                value_label="covariance",
            )
            if cov_mat:
                gk_factor_cov.add(gk)
            for r in cov_mat:
                rows_factor_cov.append({**meta, **fcm, **r})
            corr_mat = _flatten_matrix(
                f_cov.get("correlation", {}),
                row_label="factor_i",
                col_label="factor_j",
                value_label="correlation",
            )
            if corr_mat:
                gk_factor_corr.add(gk)
            for r in corr_mat:
                rows_factor_corr.append({**meta, **fcm, **r})
        for ticker, beta_row in (block.get("asset_factor_betas") or {}).items():
            base = {**meta, "asset": str(ticker)}
            base["available"] = bool(beta_row.get("available"))
            base["asset_n_obs"] = int(beta_row.get("n_obs", 0) or 0)
            base["asset_quality_status"] = str(beta_row.get("quality_status", "no_observations"))
            base["not_for_optimization"] = bool(beta_row.get("not_for_optimization", False))
            base["alpha"] = float(beta_row.get("alpha", 0.0) or 0.0)
            base["r2"] = float(beta_row.get("r2", float("nan")))
            base["adj_r2"] = float(beta_row.get("adj_r2", float("nan")))
            betas = beta_row.get("betas") or {}
            hac = (beta_row.get("hac_inference") or {})
            for bk in beta_keys:
                base[bk] = float(betas.get(bk, 0.0))
                base[f"t_{bk}"] = float(hac.get("t", {}).get(bk, float("nan")))
                base[f"p_{bk}"] = float(hac.get("p", {}).get(bk, float("nan")))
                base[f"ci_low_{bk}"] = float(hac.get("ci_low", {}).get(bk, float("nan")))
                base[f"ci_high_{bk}"] = float(hac.get("ci_high", {}).get(bk, float("nan")))
            rows_betas.append(base)
            gk_betas.add(gk)
        pf = block.get("portfolio_factor_exposure") or {}
        pf_betas = pf.get("betas") or {}
        for f, bk in zip(factor_order, beta_keys):
            rows_pf_exposure.append(
                {
                    **meta,
                    "factor": str(f),
                    "beta_key": bk,
                    "portfolio_beta": float(pf_betas.get(bk, 0.0)),
                    "weights_coverage": float(pf.get("weights_coverage", 0.0)),
                    "exposure_available": bool(pf.get("available", False)),
                }
            )
        vc = block.get("factor_variance_contribution") or {}
        vc_rows = vc.get("rows") or []
        total = float(vc.get("total_factor_variance", 0.0) or 0.0)
        top = vc.get("top_dominant_factor")
        for r in vc_rows:
            rows_var_contrib.append(
                {
                    **meta,
                    "factor": r.get("factor"),
                    "beta_key": r.get("beta_key"),
                    "factor_variance_contribution": float(
                        r.get("factor_variance_contribution", 0.0) or 0.0
                    ),
                    "factor_risk_contribution_share": float(
                        r.get("factor_risk_contribution_share", 0.0) or 0.0
                    ),
                    "factor_risk_contribution_sign": str(
                        r.get("factor_risk_contribution_sign", "zero")
                    ),
                    "total_factor_variance": total,
                    "top_dominant_factor": top,
                }
            )
        if vc_rows:
            gk_var.add(gk)
        avg_list = block.get("factor_average_moves") or []
        for r in avg_list:
            rows_avg_moves.append(
                {
                    **meta,
                    "factor": r.get("factor"),
                    "mean": float(r.get("mean", float("nan"))),
                    "median": float(r.get("median", float("nan"))),
                    "factor_n_obs": int(r.get("n_obs", 0) or 0),
                }
            )
        if avg_list:
            gk_avg.add(gk)

    for regime_key, block in _iter_blocks(payload):
        meta = {**gmeta, **_meta_row(block, regime_key)}
        gk = _split_group_key(meta)
        a_cov_stub = block.get("asset_covariance") or {}
        f_cov_stub = block.get("factor_covariance") or {}
        acm0 = _covariance_csv_meta(a_cov_stub if a_cov_stub.get("available") else None)
        fcm0 = _covariance_csv_meta(f_cov_stub if f_cov_stub.get("available") else None)
        if gk not in gk_asset_cov:
            rows_asset_cov.append(
                {
                    **meta,
                    **acm0,
                    "asset_i": None,
                    "asset_j": None,
                    "covariance": None,
                    "estimate_suppressed": True,
                }
            )
        if gk not in gk_asset_corr:
            rows_asset_corr.append(
                {
                    **meta,
                    **acm0,
                    "asset_i": None,
                    "asset_j": None,
                    "correlation": None,
                    "estimate_suppressed": True,
                }
            )
        if gk not in gk_factor_cov:
            rows_factor_cov.append(
                {
                    **meta,
                    **fcm0,
                    "factor_i": None,
                    "factor_j": None,
                    "covariance": None,
                    "estimate_suppressed": True,
                }
            )
        if gk not in gk_factor_corr:
            rows_factor_corr.append(
                {
                    **meta,
                    **fcm0,
                    "factor_i": None,
                    "factor_j": None,
                    "correlation": None,
                    "estimate_suppressed": True,
                }
            )
        if gk not in gk_betas:
            stub = {
                **meta,
                "asset": None,
                "available": False,
                "asset_n_obs": int(block.get("n_obs", 0) or 0),
                "asset_quality_status": str(block.get("quality_status", "no_observations")),
                "not_for_optimization": bool(meta.get("not_for_optimization", True)),
                "alpha": float("nan"),
                "r2": float("nan"),
                "adj_r2": float("nan"),
                "estimate_suppressed": True,
            }
            for bk in beta_keys:
                stub[bk] = float("nan")
                stub[f"t_{bk}"] = float("nan")
                stub[f"p_{bk}"] = float("nan")
                stub[f"ci_low_{bk}"] = float("nan")
                stub[f"ci_high_{bk}"] = float("nan")
            rows_betas.append(stub)
        if gk not in gk_var:
            rows_var_contrib.append(
                {
                    **meta,
                    "factor": None,
                    "beta_key": None,
                    "factor_variance_contribution": float("nan"),
                    "factor_risk_contribution_share": float("nan"),
                    "factor_risk_contribution_sign": "na",
                    "total_factor_variance": float("nan"),
                    "top_dominant_factor": None,
                    "estimate_suppressed": True,
                }
            )
        if gk not in gk_avg:
            rows_avg_moves.append(
                {
                    **meta,
                    "factor": None,
                    "mean": float("nan"),
                    "median": float("nan"),
                    "factor_n_obs": 0,
                    "estimate_suppressed": True,
                }
            )

    frames: dict[str, pd.DataFrame] = {
        "regime_asset_covariance.csv": pd.DataFrame(rows_asset_cov),
        "regime_asset_correlation.csv": pd.DataFrame(rows_asset_corr),
        "regime_factor_covariance.csv": pd.DataFrame(rows_factor_cov),
        "regime_factor_correlation.csv": pd.DataFrame(rows_factor_corr),
        "regime_asset_factor_betas.csv": pd.DataFrame(rows_betas),
        "regime_portfolio_factor_exposures.csv": pd.DataFrame(rows_pf_exposure),
        "regime_factor_variance_contribution.csv": pd.DataFrame(rows_var_contrib),
        "regime_factor_average_moves.csv": pd.DataFrame(rows_avg_moves),
    }
    return frames


def regime_factor_analytics_for_stress_report(full: dict[str, Any]) -> dict[str, Any]:
    """Slim JSON-safe dict for ``stress_report.json`` (no large covariance nests)."""

    if not isinstance(full, dict) or not full:
        return {}
    strip_cov = ("covariance", "correlation")

    def _slim_cov_block(b: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(b, dict):
            return {}
        return {k: v for k, v in b.items() if k not in strip_cov}

    def _slim_block(block: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(block, dict):
            return {}
        vc = block.get("factor_variance_contribution") or {}
        out: dict[str, Any] = {
            "label": block.get("label"),
            "n_obs": int(block.get("n_obs", 0) or 0),
            "quality_status": block.get("quality_status"),
            "not_for_optimization": bool(block.get("not_for_optimization", True)),
            "data_start": block.get("data_start"),
            "data_end": block.get("data_end"),
            "hac_max_lags": block.get("hac_max_lags"),
            "asset_covariance_available": bool(block.get("asset_covariance_available", False)),
            "factor_covariance_available": bool(block.get("factor_covariance_available", False)),
            "asset_factor_betas_available": bool(block.get("asset_factor_betas_available", False)),
            "factor_rc_available": bool(block.get("factor_rc_available", False)),
            "dominant_factors": list(block.get("dominant_factors") or []),
            "warnings": list(block.get("warnings") or []),
            "asset_covariance": _slim_cov_block(block.get("asset_covariance") or {}),
            "factor_covariance": _slim_cov_block(block.get("factor_covariance") or {}),
            "portfolio_factor_exposure": block.get("portfolio_factor_exposure"),
            "factor_variance_contribution": {
                "available": bool(vc.get("available", False)),
                "total_factor_variance": vc.get("total_factor_variance"),
                "top_dominant_factor": vc.get("top_dominant_factor"),
                "rows": vc.get("rows"),
            },
            "factor_average_moves": block.get("factor_average_moves"),
            "n_asset_betas_tracked": len(block.get("asset_factor_betas") or {}),
            "transition_split": block.get("transition_split"),
            "confidence_split": block.get("confidence_split"),
        }
        return out

    slim_splits: dict[str, Any] = {"transition": {}, "confidence": {}}
    for kind in ("transition", "confidence"):
        section = (full.get("splits") or {}).get(kind) or {}
        if not isinstance(section, dict):
            continue
        for sk, blk in section.items():
            if isinstance(blk, dict):
                slim_splits[kind][str(sk)] = _slim_block(blk)

    return {
        "version": full.get("version", REGIME_FACTOR_ANALYTICS_VERSION),
        "frequency": full.get("frequency", "monthly"),
        "weekly_alignment": full.get("weekly_alignment"),
        "factor_order": full.get("factor_order"),
        "beta_order": full.get("beta_order"),
        "data_start": full.get("data_start"),
        "data_end": full.get("data_end"),
        "n_obs_total": full.get("n_obs_total"),
        "regime_label_history_span": full.get("regime_label_history_span"),
        "portfolio_regime_analytics_window": full.get("portfolio_regime_analytics_window"),
        "portfolio_regime_analytics_note": full.get("portfolio_regime_analytics_note"),
        "weights_used": full.get("weights_used"),
        "weights_sum": full.get("weights_sum"),
        "weights_coverage": full.get("weights_coverage"),
        "hac_lag_cap": full.get("hac_lag_cap"),
        "warnings": list(full.get("warnings") or []),
        "regimes": {r: _slim_block(b) for r, b in (full.get("regimes") or {}).items() if isinstance(b, dict)},
        "splits": slim_splits,
    }


def regime_factor_analytics_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Produce the JSON summary for ``regime_factor_analytics_summary.json``."""

    if not isinstance(payload, dict):
        return {}
    summary: dict[str, Any] = {
        "version": payload.get("version", REGIME_FACTOR_ANALYTICS_VERSION),
        "frequency": payload.get("frequency", "monthly"),
        "weekly_alignment": payload.get("weekly_alignment"),
        "regime_label_history_span": payload.get("regime_label_history_span"),
        "portfolio_regime_analytics_window": payload.get("portfolio_regime_analytics_window"),
        "portfolio_regime_analytics_note": payload.get("portfolio_regime_analytics_note"),
        "data_start": payload.get("data_start"),
        "data_end": payload.get("data_end"),
        "n_obs_total": payload.get("n_obs_total", 0),
        "factor_order": payload.get("factor_order", _factor_columns()),
        "beta_order": payload.get("beta_order", _beta_keys_for(_factor_columns())),
        "weights_used": payload.get("weights_used", {}),
        "weights_sum": payload.get("weights_sum", 0.0),
        "weights_coverage": payload.get("weights_coverage", 0.0),
        "warnings": list(payload.get("warnings") or []),
        "regimes": {},
        "splits_summary": {
            "transition": list((payload.get("splits") or {}).get("transition", {}).keys()),
            "confidence": list((payload.get("splits") or {}).get("confidence", {}).keys()),
        },
    }
    for regime, block in (payload.get("regimes") or {}).items():
        if not isinstance(block, dict):
            continue
        summary["regimes"][regime] = {
            "n_obs": int(block.get("n_obs", 0) or 0),
            "quality_status": block.get("quality_status", "no_observations"),
            "not_for_optimization": bool(block.get("not_for_optimization", True)),
            "asset_covariance_available": bool(block.get("asset_covariance_available", False)),
            "factor_covariance_available": bool(block.get("factor_covariance_available", False)),
            "asset_factor_betas_available": bool(block.get("asset_factor_betas_available", False)),
            "factor_rc_available": bool(block.get("factor_rc_available", False)),
            "dominant_factors": list(block.get("dominant_factors") or []),
            "data_start": block.get("data_start"),
            "data_end": block.get("data_end"),
            "warnings": list(block.get("warnings") or []),
            "weights_coverage": float(
                (block.get("portfolio_factor_exposure") or {}).get("weights_coverage", 0.0)
            ),
            "top_dominant_factor": (block.get("factor_variance_contribution") or {}).get(
                "top_dominant_factor"
            ),
            "total_factor_variance": float(
                (block.get("factor_variance_contribution") or {}).get(
                    "total_factor_variance", 0.0
                )
            ),
            "asset_covariance_estimator": (block.get("asset_covariance") or {}).get(
                "covariance_estimator"
            ),
            "factor_covariance_estimator": (block.get("factor_covariance") or {}).get(
                "covariance_estimator"
            ),
        }
    return summary


__all__ = [
    "REGIME_FACTOR_ANALYTICS_VERSION",
    "REGIME_FACTOR_PORTFOLIO_WINDOW_NOTE",
    "REGIME_FACTOR_HAC_LAG_CAP_MONTHLY",
    "REGIME_FACTOR_HAC_LAG_CAP_WEEKLY",
    "regime_factor_analytics",
    "regime_factor_analytics_csv_frames",
    "regime_factor_analytics_summary",
    "regime_factor_analytics_for_stress_report",
]
