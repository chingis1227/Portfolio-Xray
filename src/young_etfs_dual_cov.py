"""
Dual covariance + per-asset mean returns for optimization with young ETFs.

When some RiskPortfolio assets have short history, a full inner join collapses the
estimation window. This module builds:
- a long-window covariance on eligible (sufficient history) assets only;
- a pooled median anchor from that core matrix;
- pairwise sample cov on overlaps for young assets, shrunk toward the anchor;
- PSD repair if needed.

Policy parameters come from config key ``young_etf_optimization_policy`` (see config_schema).
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.risk_contrib import DDOF, cov_matrix_monthly, cov_matrix_monthly_robust
from src.windows import slice_calendar_window


def _core_covariance(
    ret: pd.DataFrame,
    *,
    use_shrinkage_on_core: bool,
    use_robust_on_core: bool,
) -> pd.DataFrame:
    """Covariance on the eligible core window (sample / Ledoit–Wolf / MCD)."""
    if use_robust_on_core:
        return cov_matrix_monthly_robust(ret, ddof=DDOF)
    return cov_matrix_monthly(ret, ddof=DDOF, use_shrinkage=use_shrinkage_on_core)


def _history_months_in_window(
    s: pd.Series,
    window: int,
    *,
    analysis_end: pd.Timestamp | None = None,
) -> int:
    """Non-NaN count in calendar ``window`` (months), or last ``window`` rows when analysis_end is None."""
    if s is None or len(s) == 0:
        return 0
    if analysis_end is None:
        tail = s.iloc[-window:] if len(s) >= window else s
        return int(tail.notna().sum())
    sl = slice_calendar_window(s, analysis_end, int(window))
    return int(sl.dropna().shape[0])


def maturity_bucket(history: int, candidate_min: int, eligible: int) -> str:
    if history >= eligible:
        return "eligible"
    if history >= candidate_min:
        return "candidate"
    return "new"


def shrinkage_alpha_for_history(history: int, policy: dict[str, Any]) -> float:
    """Piecewise: new -> new_shrinkage_alpha; candidate -> linear; eligible -> 1."""
    em = int(policy["eligible_months"])
    cm = int(policy["candidate_months_min"])
    a_new = float(policy["new_shrinkage_alpha"])
    a_lo = float(policy["candidate_alpha_min"])
    a_hi = float(policy["candidate_alpha_at_eligible"])
    if history >= em:
        return 1.0
    if history < cm:
        return a_new
    if em <= cm:
        return a_hi
    t = (history - cm) / (em - cm)
    return float(a_lo + t * (a_hi - a_lo))


def _pair_alpha(a_i: float, a_j: float) -> float:
    if a_i >= 1.0 - 1e-12 and a_j >= 1.0 - 1e-12:
        return 1.0
    return float((a_i + a_j) / 2.0)


def _pairwise_cov(s1: pd.Series, s2: pd.Series, ddof: int = DDOF) -> float:
    df = pd.concat([s1, s2], axis=1).dropna()
    if len(df) < 2:
        return float("nan")
    return float(df.iloc[:, 0].cov(df.iloc[:, 1], ddof=ddof))


def _pooled_core_median(sigma: pd.DataFrame) -> float:
    vals: list[float] = []
    for r in sigma.index:
        for c in sigma.columns:
            vals.append(float(sigma.loc[r, c]))
    if not vals:
        return float("nan")
    return float(np.median(vals))


def _repair_covariance_psd(cov: pd.DataFrame, eps: float = 1e-10) -> pd.DataFrame:
    vals = cov.values.astype(float)
    sym = (vals + vals.T) / 2.0
    w, v = np.linalg.eigh(sym)
    w_clip = np.maximum(w, eps)
    repaired = (v * w_clip) @ v.T
    out = pd.DataFrame(repaired, index=cov.index, columns=cov.columns)
    return (out + out.T) / 2.0


def build_dual_covariance_and_mu(
    monthly_returns: pd.DataFrame,
    tickers: list[str],
    window_months: int,
    policy: dict[str, Any],
    use_shrinkage_on_core: bool = False,
    use_robust_on_core: bool = False,
    analysis_end: pd.Timestamp | None = None,
) -> tuple[pd.DataFrame, pd.Series, dict[str, Any]]:
    """
    Build covariance matrix and mean monthly return vector for RiskPortfolio tickers.

    If ``use_robust_on_core`` is True, the eligible core set uses MinCovDet (MCD);
    ``use_shrinkage_on_core`` is then ignored for that core. Production default: both False.

    Returns:
      cov_df: square DataFrame indexed/columned by ``tickers`` (order preserved)
      mu: Series of mean monthly simple returns per ticker over last ``window_months`` (non-NaN mean)
      diagnostics: maturity buckets, alphas, mode
    """
    tickers = [t for t in tickers if t in monthly_returns.columns]
    if not tickers:
        raise ValueError("No tickers present in monthly_returns")
    ae = analysis_end if analysis_end is not None else pd.Timestamp(monthly_returns.index.max())

    eligible_m = int(policy["eligible_months"])
    cand_min = int(policy["candidate_months_min"])

    per_ticker: dict[str, dict[str, Any]] = {}
    hist: dict[str, int] = {}
    for t in tickers:
        h = _history_months_in_window(monthly_returns[t], window_months, analysis_end=ae)
        hist[t] = h
        bucket = maturity_bucket(h, cand_min, eligible_m)
        alpha = shrinkage_alpha_for_history(h, policy)
        per_ticker[t] = {
            "history_months": h,
            "bucket": bucket,
            "shrinkage_alpha": round(alpha, 4),
        }

    eligible = [t for t in tickers if per_ticker[t]["bucket"] == "eligible"]

    def _fallback_inner_join(reason: str) -> tuple[pd.DataFrame, pd.Series, dict[str, Any]]:
        win = slice_calendar_window(monthly_returns[tickers], ae, int(window_months))
        ret = win.dropna(axis=1, how="all").dropna(how="any")
        mu_local = win.mean().reindex(tickers).fillna(0.0)
        if len(ret) < 2 or ret.shape[1] == 0:
            cov_empty = pd.DataFrame(0.0, index=tickers, columns=tickers)
            for t in tickers:
                s = win[t].dropna()
                v = float(s.var(ddof=DDOF)) if len(s) >= 2 else 1e-6
                cov_empty.loc[t, t] = max(v, 1e-8)
            cov_empty = _repair_covariance_psd(cov_empty)
            diagnostics_local = {
                "mode": "fallback_full_inner_join",
                "reason": reason + "_insufficient_rows",
                "eligible_tickers": eligible,
                "tickers": per_ticker,
            }
            return cov_empty, mu_local, diagnostics_local
        cov_sub = _core_covariance(
            ret,
            use_shrinkage_on_core=use_shrinkage_on_core,
            use_robust_on_core=use_robust_on_core,
        )
        cov_full = pd.DataFrame(0.0, index=tickers, columns=tickers)
        for ti in cov_sub.index:
            for tj in cov_sub.columns:
                cov_full.loc[ti, tj] = float(cov_sub.loc[ti, tj])
        for t in tickers:
            if cov_full.loc[t, t] <= 0:
                s = win[t].dropna()
                v = float(s.var(ddof=DDOF)) if len(s) >= 2 else 1e-6
                cov_full.loc[t, t] = max(v, 1e-8)
        cov_full = _repair_covariance_psd(cov_full)
        diagnostics_local = {
            "mode": "fallback_full_inner_join",
            "reason": reason,
            "eligible_tickers": eligible,
            "tickers": per_ticker,
        }
        return cov_full, mu_local, diagnostics_local

    # --- Fallback: not enough eligible assets to anchor — full inner join (legacy) ---
    if len(eligible) < 2:
        return _fallback_inner_join("fewer_than_2_eligible_for_core")

    ret_core = slice_calendar_window(monthly_returns[eligible], ae, int(window_months)).dropna(how="any")
    if len(ret_core) < 2:
        return _fallback_inner_join("core_sample_too_short_after_join")

    sigma_core = _core_covariance(
        ret_core,
        use_shrinkage_on_core=use_shrinkage_on_core,
        use_robust_on_core=use_robust_on_core,
    )

    pooled_anchor = _pooled_core_median(sigma_core)

    n = len(tickers)
    cov_arr = np.zeros((n, n), dtype=float)
    idx_of = {t: i for i, t in enumerate(tickers)}

    # Fill eligible-eligible from core
    for ti in eligible:
        for tj in eligible:
            i, j = idx_of[ti], idx_of[tj]
            cov_arr[i, j] = float(sigma_core.loc[ti, tj])

    win_slice = slice_calendar_window(monthly_returns[tickers], ae, int(window_months))

    for i, ti in enumerate(tickers):
        for j in range(i, n):
            tj = tickers[j]
            ai = float(per_ticker[ti]["shrinkage_alpha"])
            aj = float(per_ticker[tj]["shrinkage_alpha"])
            a_pair = _pair_alpha(ai, aj)

            if ti in eligible and tj in eligible:
                c_ij = float(sigma_core.loc[ti, tj])
            else:
                raw_ij = _pairwise_cov(win_slice[ti], win_slice[tj], ddof=DDOF)
                if raw_ij == raw_ij and pooled_anchor == pooled_anchor:  # not NaN
                    c_ij = a_pair * raw_ij + (1.0 - a_pair) * pooled_anchor
                elif raw_ij == raw_ij:
                    c_ij = raw_ij
                elif pooled_anchor == pooled_anchor:
                    c_ij = pooled_anchor
                else:
                    c_ij = 0.0
            cov_arr[i, j] = c_ij
            cov_arr[j, i] = c_ij

    cov_df = pd.DataFrame(cov_arr, index=tickers, columns=tickers)
    cov_df = _repair_covariance_psd(cov_df)

    mu = win_slice.mean()
    mu = mu.reindex(tickers).fillna(0.0)

    diagnostics = {
        "mode": "dual_core_median_anchor",
        "eligible_tickers": eligible,
        "core_effective_months": len(ret_core),
        "tickers": per_ticker,
    }
    return cov_df, mu, diagnostics


def per_ticker_young_weight_caps(
    diagnostics_tickers: dict[str, dict[str, Any]],
    max_weight_pct: float,
) -> dict[str, float]:
    """Return {ticker: cap} for candidate + new buckets."""
    caps: dict[str, float] = {}
    for t, meta in diagnostics_tickers.items():
        if meta.get("bucket") in ("candidate", "new"):
            caps[t] = float(max_weight_pct)
    return caps
