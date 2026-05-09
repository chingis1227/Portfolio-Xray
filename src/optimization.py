"""
Portfolio optimization: max expected return with weight bounds, ProLiquidity.
RC_vol is diagnostic-only and is not enforced in the objective.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from policy_math.feasibility import resolve_max_weight_per_asset_cap
from src.risk_contrib import cov_matrix_monthly, cov_matrix_returns, percentage_contributions_variance, variance_p
from src.returns_frequency import ReturnsFrequency, calendar_window_to_n_periods
from src.risk_parity_spinu import repair_covariance_psd, spinu_ccd_equal_budget

MIN_WEIGHT_DEFAULT = 0.01

OBJECTIVE_MODE_MAX_RETURN = "max_return"
OBJECTIVE_MODE_RISK_PARITY = "risk_parity"
OBJECTIVE_MODES = (OBJECTIVE_MODE_MAX_RETURN, OBJECTIVE_MODE_RISK_PARITY)


def get_risk_portfolio_tickers(tickers: list[str], cash_proxy_ticker: str | None = None) -> list[str]:
    """Return tickers excluding the cash proxy (e.g. BIL). All remaining tickers are in the optimization universe."""
    if not cash_proxy_ticker:
        return list(tickers)
    c = str(cash_proxy_ticker).strip().upper()
    return [t for t in tickers if str(t).strip().upper() != c]


def _build_bounds(
    cols: list[str],
    n: int,
    min_weight: float,
    max_single_security_weight_pct: float | None,
    per_ticker_max_weight: dict[str, float] | None,
) -> list[tuple[float, float]]:
    max_w = float(resolve_max_weight_per_asset_cap(n))
    global_cap: float | None = None
    if max_single_security_weight_pct is not None and max_single_security_weight_pct > 0:
        global_cap = float(max_single_security_weight_pct)
    ptm = per_ticker_max_weight or {}
    bounds: list[tuple[float, float]] = []
    for t in cols:
        cap = max_w
        if global_cap is not None:
            cap = min(cap, global_cap)
        if t in ptm:
            cap = min(cap, float(ptm[t]))
        bounds.append((min_weight, min(cap, 1.0)))
    return bounds


def _pc_from_w(w: np.ndarray, cov: np.ndarray) -> np.ndarray:
    var_p = variance_p(w, cov)
    if var_p <= 1e-16:
        return np.full_like(w, 1.0 / len(w))
    m = cov @ w
    return (w * m) / var_p


def run_max_return_optimization(
    returns_df: pd.DataFrame,
    risk_tickers: list[str],
    min_single_security_weight_pct: float | None = None,
    max_single_security_weight_pct: float | None = None,
    window_months: int = 60,
    cash_proxy_ticker: str | None = None,
    returns_window: pd.DataFrame | None = None,
    use_shrinkage: bool = False,
    cov_precomputed: pd.DataFrame | None = None,
    mu_precomputed: pd.Series | None = None,
    per_ticker_max_weight: dict[str, float] | None = None,
    objective_mode: str = OBJECTIVE_MODE_MAX_RETURN,
    warm_start_weights: dict[str, float] | None = None,
    skeleton_tracking_lambda: float = 0.0,
    soft_target_vol_annual: float | None = None,
    soft_vol_penalty_lambda: float = 0.0,
    soft_target_return_annual: float | None = None,
    soft_return_penalty_lambda: float = 0.0,
    periods_per_year: int = 12,
    returns_frequency: ReturnsFrequency = "monthly",
    **_: Any,
) -> tuple[dict[str, float], str]:
    """
    Optimize weights on ``risk_tickers`` (excluding cash). Sum(weights)=1, long-only.
    Objective: max_return (minimize -mu'w) or risk_parity: Spinu CCD on 0.5 x'Σx - (1/N)Σ log(x_i)
    with PSD-repaired Σ and equal budgets b_i=1/N, then normalize x to weights; if convergence/bounds fail,
    minimize squared deviation of RC from 1/n via SLSQP. Optional soft penalties apply only to max_return.
    Returns (weights_dict, status_message).
    """
    del cash_proxy_ticker  # reserved for callers documenting intent
    risk_list = list(risk_tickers)
    if not risk_list:
        return {}, "FAIL: no risk tickers"

    rf_key = returns_frequency if returns_frequency in ("monthly", "weekly", "daily") else "monthly"
    min_periods = max(2, calendar_window_to_n_periods(11, rf_key))
    ppy = int(periods_per_year)
    use_precomputed_cov = (
        cov_precomputed is not None and mu_precomputed is not None and not cov_precomputed.empty
    )

    if use_precomputed_cov:
        cols = [t for t in risk_list if t in cov_precomputed.index and t in cov_precomputed.columns]
        if not cols:
            return {}, "FAIL_DATA: cov_precomputed missing overlap with risk tickers"
        n = len(cols)
        cov = cov_precomputed.reindex(index=cols, columns=cols).fillna(0.0).values
        mu = mu_precomputed.reindex(cols).fillna(0.0).values
    elif returns_window is not None and not returns_window.empty:
        ret = returns_window
        cols = list(ret.columns)
        if len(ret) < min_periods:
            return {}, (
                f"FAIL_DATA: returns_window has only {len(ret)} periods (need ≥{min_periods} "
                f"aligned bars for calendar ~11m history)."
            )
        n = len(cols)
        mu = ret.mean().values
        cov = cov_matrix_returns(ret, ddof=1, use_shrinkage=use_shrinkage).values
    else:
        cols = [t for t in risk_list if t in returns_df.columns]
        missing = set(risk_list) - set(cols)
        if missing:
            import logging

            logging.getLogger(__name__).warning(
                "Тикеры без данных (исключены из оптимизации, вес = 0): %s", sorted(missing)
            )
        if not cols:
            return {}, f"FAIL_DATA: no risk tickers with returns (missing: {risk_list})"

        from src.windows import slice_calendar_window

        ret_full = returns_df[cols].dropna(axis=1, how="all")
        ae_panel = pd.Timestamp(ret_full.index.max()).normalize()
        ret = slice_calendar_window(ret_full, ae_panel, window_months).dropna(how="any")
        if len(ret) < min_periods:
            span = max(
                calendar_window_to_n_periods(int(window_months) * 4, rf_key),
                min_periods * 6,
            )
            tail = ret_full.iloc[-min(len(ret_full), span) :]
            ae_panel = pd.Timestamp(tail.index.max()).normalize()
            ret = slice_calendar_window(tail, ae_panel, window_months).dropna(how="any")
        if len(ret) < min_periods:
            return {}, (
                f"FAIL_DATA: insufficient history after inner join ({len(ret)} periods). "
                f"Need at least {min_periods} overlapping bars (~11 calendar months)."
            )
        cols = list(ret.columns)
        if not cols:
            return {}, "FAIL_DATA: no assets with returns in window"
        n = len(cols)
        mu = ret.mean().values
        cov = cov_matrix_returns(ret, ddof=1, use_shrinkage=use_shrinkage).values

    min_weight = (
        float(min_single_security_weight_pct)
        if min_single_security_weight_pct is not None and min_single_security_weight_pct > 0
        else MIN_WEIGHT_DEFAULT
    )
    bounds = _build_bounds(
        cols, n, min_weight,
        max_single_security_weight_pct, per_ticker_max_weight,
    )

    obj_mode = objective_mode if objective_mode in OBJECTIVE_MODES else OBJECTIVE_MODE_MAX_RETURN
    obj_mode_invalid = objective_mode not in OBJECTIVE_MODES
    track_lam = float(skeleton_tracking_lambda) if skeleton_tracking_lambda > 0 else 0.0
    w_ref_vec: np.ndarray | None = None
    if track_lam > 0 and obj_mode == OBJECTIVE_MODE_MAX_RETURN and warm_start_weights:
        w_ref_vec = np.array([float(warm_start_weights.get(t, 0.0)) for t in cols], dtype=float)
        sr = float(w_ref_vec.sum())
        if sr > 1e-12:
            w_ref_vec = w_ref_vec / sr
        else:
            w_ref_vec = None

    stv = float(soft_target_vol_annual) if soft_target_vol_annual is not None else None
    lam_sv = float(soft_vol_penalty_lambda) if soft_vol_penalty_lambda and soft_vol_penalty_lambda > 0 else 0.0
    st_ret = float(soft_target_return_annual) if soft_target_return_annual is not None else None
    lam_sr = float(soft_return_penalty_lambda) if soft_return_penalty_lambda and soft_return_penalty_lambda > 0 else 0.0

    # Risk parity: Spinu cyclical coordinate descent on 0.5 x'Σx - (1/N)Σ log(x_i); Σ PSD-repaired.
    if obj_mode == OBJECTIVE_MODE_RISK_PARITY:
        cov, _cov_psd_flag = repair_covariance_psd(cov)
        w_spinu, spinu_diag = spinu_ccd_equal_budget(
            cov,
            eps_floor=1e-12,
            max_iter=50_000,
            tol=1e-10,
            init="inv_vol",
        )
        bounds_lo = np.array([float(b[0]) for b in bounds])
        bounds_hi = np.array([float(b[1]) for b in bounds])
        tol_b = 1e-10
        in_bounds = bool(
            np.all(w_spinu >= bounds_lo - tol_b) and np.all(w_spinu <= bounds_hi + tol_b)
        )
        spinu_quality = (
            bool(spinu_diag.get("converged"))
            and float(spinu_diag.get("max_rc_error", 1.0)) <= 1e-2
            and np.all(np.isfinite(w_spinu))
            and abs(float(np.sum(w_spinu)) - 1.0) < 1e-8
            and np.all(w_spinu > 0)
        )
        if spinu_quality and in_bounds:
            w_dict = {t: float(w_spinu[i]) for i, t in enumerate(cols)}
            for t in risk_list:
                if t not in w_dict:
                    w_dict[t] = 0.0
            status_parts = [
                "OK",
                f"OBJECTIVE_MODE={obj_mode}",
                "RP_SOLVER=spinu_ccd",
            ]
            if obj_mode_invalid:
                status_parts.append(f"OBJECTIVE_MODE_INVALID: {objective_mode!r} -> max_return")
            if warm_start_weights:
                status_parts.append("WARM_START=on")
            return w_dict, " | ".join(status_parts)

    def objective(w: np.ndarray) -> float:
        pc = _pc_from_w(w, cov)
        if obj_mode == OBJECTIVE_MODE_RISK_PARITY:
            target = 1.0 / float(n)
            rp_dev = float(np.sum((pc - target) ** 2))
            return rp_dev
        track = 0.0
        if w_ref_vec is not None:
            d = w - w_ref_vec
            track = track_lam * float(np.dot(d, d))
        soft_ips = 0.0
        if lam_sv > 0 and stv is not None:
            var_p = float(w @ cov @ w)
            sigma_m = math.sqrt(max(var_p, 0.0))
            k = float(ppy)
            sigma_ann = sigma_m * math.sqrt(k)
            dv = sigma_ann - stv
            soft_ips += lam_sv * (dv * dv)
        if lam_sr > 0 and st_ret is not None:
            mu_m = float(np.dot(mu, w))
            k = float(ppy)
            ret_ann_lin = k * mu_m
            dr = ret_ann_lin - st_ret
            soft_ips += lam_sr * (dr * dr)
        return -float(np.dot(mu, w)) + track + soft_ips

    def constraint_sum(w: np.ndarray) -> float:
        return float(np.sum(w) - 1.0)

    constraints_full = [{"type": "eq", "fun": constraint_sum}]

    def penalty_feas(w: np.ndarray) -> float:
        s = float(np.sum(w) - 1.0)
        return s * s

    bounds_hi = np.array([b[1] for b in bounds])
    x0_from_warm: np.ndarray | None = None
    if warm_start_weights:
        xw = np.array([float(warm_start_weights.get(t, 0.0)) for t in cols], dtype=float)
        xw = np.clip(xw, min_weight, bounds_hi - 1e-6)
        sw = float(xw.sum())
        if sw > 1e-12:
            x0_from_warm = xw / sw

    x0 = np.ones(n) / n
    x0 = np.clip(x0, min_weight, bounds_hi - 1e-6)
    x0 = x0 / x0.sum()

    feas = minimize(penalty_feas, x0, method="L-BFGS-B", bounds=bounds, options={"maxiter": 300})
    if x0_from_warm is not None:
        x0_slsqp = x0_from_warm.copy()
    elif feas.fun < 1e-6:
        x0_slsqp = feas.x
    else:
        x0_slsqp = feas.x / max(feas.x.sum(), 1e-12)

    res = minimize(
        objective,
        x0_slsqp.copy(),
        method="SLSQP",
        bounds=bounds,
        constraints=constraints_full,
        options={"maxiter": 1000, "ftol": 1e-9},
    )
    used_fallback = False
    if not res.success:
        res = minimize(
            objective,
            x0_slsqp.copy(),
            method="SLSQP",
            bounds=bounds,
            constraints=constraints_full,
            options={"maxiter": 1000, "ftol": 1e-9},
        )
        if not res.success:
            w_fallback = np.clip(feas.x, min_weight, np.array([b[1] for b in bounds]) - 1e-8)
            w_fallback = w_fallback / w_fallback.sum()
            res = type("Res", (), {"success": True, "x": w_fallback})()
        used_fallback = True

    w = res.x

    w_dict = {t: float(w[i]) for i, t in enumerate(cols)}
    for t in risk_list:
        if t not in w_dict:
            w_dict[t] = 0.0

    status_parts = []
    status_parts.append("OK_FALLBACK" if used_fallback else "OK")
    status_parts.append(f"OBJECTIVE_MODE={obj_mode}")
    if obj_mode == OBJECTIVE_MODE_RISK_PARITY:
        status_parts.append("RP_SOLVER=slsqp_fallback")
    if obj_mode_invalid:
        status_parts.append(f"OBJECTIVE_MODE_INVALID: {objective_mode!r} -> max_return")
    if warm_start_weights:
        status_parts.append("WARM_START=on")
    if track_lam > 0 and w_ref_vec is not None:
        status_parts.append(f"SKEL_TRACK_LAMBDA={track_lam:.4g}")
    if lam_sv > 0 and stv is not None:
        status_parts.append(f"SOFT_VOL_TARGET={stv:.4f} LAMBDA={lam_sv:.4g}")
    if lam_sr > 0 and st_ret is not None:
        status_parts.append(f"SOFT_RET_TARGET={st_ret:.4f} LAMBDA={lam_sr:.4g}")
    return w_dict, " | ".join(status_parts)


def _alpha_shift_to_target_vol(
    weights_risk: dict[str, float],
    cov_df: pd.DataFrame,
    target_vol_annual: float,
    n_rc: int,
    donor_shift_mode: str,
    *,
    periods_per_year: int = 12,
) -> tuple[dict[str, float], str | None]:
    tickers = [t for t in weights_risk if t in cov_df.columns and t in cov_df.index]
    if not tickers:
        return dict(weights_risk), "No risk assets in covariance for alpha shift."
    cov = cov_df.reindex(index=tickers, columns=tickers).fillna(0).values
    w = np.array([weights_risk[t] for t in tickers])
    k_scale = float(periods_per_year)
    current_vol = float(np.sqrt(variance_p(w, cov) * k_scale)) if variance_p(w, cov) > 0 else 0.0
    if current_vol <= target_vol_annual:
        return dict(weights_risk), None

    pc = percentage_contributions_variance(w, cov)
    rc_by_ticker = [(tickers[i], float(pc[i])) for i in range(len(tickers)) if w[i] > 0]
    rc_by_ticker.sort(key=lambda x: (-x[1], x[0]))
    donors = [x[0] for x in rc_by_ticker[: min(n_rc, len(rc_by_ticker))]]
    donors = [t for t in donors if weights_risk.get(t, 0) > 0]
    if not donors:
        return dict(weights_risk), "Donor set empty for alpha shift."

    recipient = None
    for candidate in ("VOO", "VT", "VTI"):
        if candidate in weights_risk and candidate in tickers:
            recipient = candidate
            break
    if recipient is None:
        vol_by_ticker = []
        for t in tickers:
            idx = tickers.index(t)
            vol_t = float(np.sqrt(cov[idx, idx] * k_scale)) if cov[idx, idx] > 0 else 0.0
            vol_by_ticker.append((t, vol_t))
        vol_by_ticker.sort(key=lambda x: (x[1], x[0]))
        recipient = vol_by_ticker[0][0] if vol_by_ticker else tickers[0]

    donor_weights = np.array([weights_risk[t] for t in donors])
    alpha_max = float(donor_weights.sum())
    if alpha_max <= 0:
        return dict(weights_risk), "Total donor weight is zero."

    tol_vol = 1e-6
    alpha_lo, alpha_hi = 0.0, alpha_max
    for _ in range(80):
        alpha = (alpha_lo + alpha_hi) / 2.0
        if donor_shift_mode == "equal":
            take_per_donor = alpha / len(donors) if donors else 0.0
            new_weights = dict(weights_risk)
            for t in donors:
                new_weights[t] = max(0.0, weights_risk[t] - take_per_donor)
            add_to_recipient = min(alpha, sum(weights_risk[t] for t in donors) - sum(new_weights[t] for t in donors))
        else:
            new_weights = dict(weights_risk)
            for t in donors:
                frac = weights_risk[t] / alpha_max if alpha_max > 0 else 0.0
                new_weights[t] = max(0.0, weights_risk[t] - alpha * frac)
            add_to_recipient = sum(weights_risk[t] for t in donors) - sum(new_weights[t] for t in donors)
        new_weights[recipient] = weights_risk.get(recipient, 0.0) + add_to_recipient
        w_new = np.array([new_weights.get(t, 0.0) for t in tickers])
        var_p = variance_p(w_new, cov)
        vol_new = float(np.sqrt(var_p * k_scale)) if var_p > 0 else 0.0
        if vol_new <= target_vol_annual + tol_vol:
            alpha_hi = alpha
        else:
            alpha_lo = alpha
        if alpha_hi - alpha_lo < 1e-8:
            break

    alpha_final = alpha_hi
    if donor_shift_mode == "equal":
        take_per_donor = alpha_final / len(donors) if donors else 0.0
        out = dict(weights_risk)
        for t in donors:
            out[t] = max(0.0, weights_risk[t] - take_per_donor)
        add_to_recipient = sum(weights_risk[t] for t in donors) - sum(out[t] for t in donors)
    else:
        out = dict(weights_risk)
        for t in donors:
            frac = weights_risk[t] / alpha_max if alpha_max > 0 else 0.0
            out[t] = max(0.0, weights_risk[t] - alpha_final * frac)
        add_to_recipient = sum(weights_risk[t] for t in donors) - sum(out[t] for t in donors)
    out[recipient] = out.get(recipient, 0.0) + add_to_recipient
    w_final = np.array([out.get(t, 0.0) for t in tickers])
    vol_final = float(np.sqrt(variance_p(w_final, cov) * k_scale)) if variance_p(w_final, cov) > 0 else 0.0
    if vol_final > target_vol_annual + 1e-4:
        return dict(weights_risk), (
            "TargetVol cannot be achieved with cash_policy='prohibited' "
            "given the current universe and constraints."
        )
    return out, None


def proliquidity(
    weights_risk: dict[str, float],
    cash_proxy_ticker: str,
    current_vol_annual: float,
    target_vol_annual: float,
    liquidity_floor_pct: float,
    cash_policy: str,
    cov_df: pd.DataFrame | None = None,
    n_rc: int = 3,
    donor_shift_mode: str = "proportional",
    *,
    periods_per_year: int = 12,
) -> tuple[dict[str, float], str | None]:
    if cash_policy == "prohibited":
        if current_vol_annual > target_vol_annual and cov_df is not None:
            shifted, err = _alpha_shift_to_target_vol(
                weights_risk,
                cov_df,
                target_vol_annual,
                n_rc,
                donor_shift_mode,
                periods_per_year=periods_per_year,
            )
            if err:
                return shifted, err
            return shifted, None
        return dict(weights_risk), None

    if current_vol_annual <= 0:
        vol_scaling_cash = 0.0
    else:
        scaler = target_vol_annual / current_vol_annual
        vol_scaling_cash = max(0.0, 1.0 - scaler)
    cash_weight = max(liquidity_floor_pct, vol_scaling_cash)
    cash_weight = max(0.0, min(1.0, cash_weight))
    risky_weight = 1.0 - cash_weight

    out = {t: risky_weight * w for t, w in weights_risk.items()}
    out[cash_proxy_ticker] = cash_weight
    return out, None


def portfolio_vol_annual(weights: dict[str, float], cov_df: pd.DataFrame, *, periods_per_year: int = 12) -> float:
    tickers = [t for t in weights if t in cov_df.columns and t in cov_df.index]
    if not tickers:
        return 0.0
    w = np.array([weights[t] for t in tickers])
    cov = cov_df.reindex(index=tickers, columns=tickers).fillna(0).values
    var = variance_p(w, cov)
    return float(np.sqrt(var * float(periods_per_year))) if var > 0 else 0.0


def rc_by_asset_from_weights(
    weights_risk: dict[str, float],
    cov_df: pd.DataFrame,
) -> dict[str, float]:
    cols = [t for t in weights_risk if t in cov_df.columns and t in cov_df.index and weights_risk.get(t, 0) > 0]
    if not cols:
        return {}
    w = np.array([weights_risk[t] for t in cols])
    cov = cov_df.reindex(index=cols, columns=cols).fillna(0).values
    pc = _pc_from_w(w, cov)
    return {t: float(pc[i]) for i, t in enumerate(cols)}
