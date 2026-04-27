"""
Portfolio optimization: max expected return with per-asset RC caps, weight bounds, ProLiquidity.
No structural blocks (Growth/Duration/Inflation) or risk-budget targets.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from policy_math.feasibility import resolve_weight_caps
from src.risk_contrib import (
    build_rc_cap_per_ticker,
    cov_matrix_monthly,
    percentage_contributions_variance,
    resolve_rc_asset_cap,
    variance_p,
)

MIN_WEIGHT_DEFAULT = 0.01
RC_CAP_PENALTY_LAMBDA_DEFAULT = 25.0

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
    growth_core_candidates: list[str],
    max_single_security_weight_pct: float | None,
    per_ticker_max_weight: dict[str, float] | None,
) -> list[tuple[float, float]]:
    n_core = sum(1 for t in cols if t in growth_core_candidates)
    n_sat = len(cols) - n_core
    caps = resolve_weight_caps(n_total=n, n_core=n_core, n_sat=n_sat, equity_only=False)
    max_core = float(caps["max_weight_core"] or 0.0)
    max_sat = float(caps["max_weight_sat"] or 0.0)
    global_cap: float | None = None
    if max_single_security_weight_pct is not None and max_single_security_weight_pct > 0:
        global_cap = float(max_single_security_weight_pct)
    ptm = per_ticker_max_weight or {}
    bounds: list[tuple[float, float]] = []
    for t in cols:
        cap = max_core if t in growth_core_candidates else max_sat
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


def run_risk_budget_optimization(
    returns_df: pd.DataFrame,
    risk_tickers: list[str],
    growth_core_candidates: list[str],
    rc_asset_cap_pct: float | None = None,
    min_single_security_weight_pct: float | None = None,
    max_single_security_weight_pct: float | None = None,
    window_months: int = 60,
    cash_proxy_ticker: str | None = None,
    returns_window: pd.DataFrame | None = None,
    use_shrinkage: bool = False,
    cov_precomputed: pd.DataFrame | None = None,
    mu_precomputed: pd.Series | None = None,
    per_ticker_max_weight: dict[str, float] | None = None,
    rc_cap_penalty_lambda: float = RC_CAP_PENALTY_LAMBDA_DEFAULT,
    objective_mode: str = OBJECTIVE_MODE_MAX_RETURN,
    warm_start_weights: dict[str, float] | None = None,
    skeleton_tracking_lambda: float = 0.0,
    soft_target_vol_annual: float | None = None,
    soft_vol_penalty_lambda: float = 0.0,
    soft_target_return_annual: float | None = None,
    soft_return_penalty_lambda: float = 0.0,
    **_: Any,
) -> tuple[dict[str, float], str]:
    """
    Optimize weights on ``risk_tickers`` (excluding cash). Sum(weights)=1, long-only.
    Objective: max_return (minimize -mu'w) + RC-cap penalty; optional risk_parity mode.
    Optional soft penalties vs target vol / nominal return (annual decimals).
    Returns (weights_dict, status_message).
    """
    del cash_proxy_ticker  # reserved for callers documenting intent
    risk_list = list(risk_tickers)
    if not risk_list:
        return {}, "FAIL: no risk tickers"

    MIN_FULL_JOIN_MONTHS = 11
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
        if len(ret) < MIN_FULL_JOIN_MONTHS:
            return {}, (
                f"FAIL_DATA: returns_window has only {len(ret)} months. "
                f"Need at least {MIN_FULL_JOIN_MONTHS} months."
            )
        n = len(cols)
        mu = ret.mean().values
        cov = cov_matrix_monthly(ret, ddof=1, use_shrinkage=use_shrinkage).values
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
        ret = returns_df[cols].iloc[-window_months:]
        ret = ret.dropna(axis=1, how="all").dropna(how="any")
        if len(ret) < MIN_FULL_JOIN_MONTHS:
            lookback = min(returns_df.shape[0], max(window_months * 2, 120))
            ret = returns_df[cols].iloc[-lookback:]
            ret = ret.dropna(axis=1, how="all").dropna(how="any")
            if len(ret) >= MIN_FULL_JOIN_MONTHS:
                ret = ret.iloc[-min(window_months, len(ret)):]
            else:
                return {}, (
                    f"FAIL_DATA: insufficient history after inner join ({len(ret)} months). "
                    f"Need at least {MIN_FULL_JOIN_MONTHS} months where every risk ticker has data."
                )
        else:
            ret = ret.iloc[-min(window_months, len(ret)):]
        cols = list(ret.columns)
        if not cols:
            return {}, "FAIL_DATA: no assets with returns in window"
        n = len(cols)
        mu = ret.mean().values
        cov = cov_matrix_monthly(ret, ddof=1, use_shrinkage=use_shrinkage).values

    rc_cap_map = build_rc_cap_per_ticker(cols, rc_asset_cap_pct, max(n, 1))
    rc_cap_arr = np.array([float(rc_cap_map.get(t, 0.25)) for t in cols], dtype=float)

    min_weight = (
        float(min_single_security_weight_pct)
        if min_single_security_weight_pct is not None and min_single_security_weight_pct > 0
        else MIN_WEIGHT_DEFAULT
    )
    bounds = _build_bounds(
        cols, n, min_weight, growth_core_candidates,
        max_single_security_weight_pct, per_ticker_max_weight,
    )

    penalty_lambda = float(rc_cap_penalty_lambda) if rc_cap_penalty_lambda > 0 else RC_CAP_PENALTY_LAMBDA_DEFAULT
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

    def objective(w: np.ndarray) -> float:
        pc = _pc_from_w(w, cov)
        rc_viol = np.maximum(0.0, pc - rc_cap_arr)
        rc_pen = float(np.sum(rc_viol * rc_viol))
        base = penalty_lambda * rc_pen
        if obj_mode == OBJECTIVE_MODE_RISK_PARITY:
            target = 1.0 / float(n)
            rp_dev = float(np.sum((pc - target) ** 2))
            return rp_dev + base
        track = 0.0
        if w_ref_vec is not None:
            d = w - w_ref_vec
            track = track_lam * float(np.dot(d, d))
        soft_ips = 0.0
        if lam_sv > 0 and stv is not None:
            var_p = float(w @ cov @ w)
            sigma_m = math.sqrt(max(var_p, 0.0))
            sigma_ann = sigma_m * math.sqrt(12.0)
            dv = sigma_ann - stv
            soft_ips += lam_sv * (dv * dv)
        if lam_sr > 0 and st_ret is not None:
            mu_m = float(np.dot(mu, w))
            ret_ann_lin = 12.0 * mu_m
            dr = ret_ann_lin - st_ret
            soft_ips += lam_sr * (dr * dr)
        return -float(np.dot(mu, w)) + base + track + soft_ips

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
    pc = _pc_from_w(w, cov)
    viol_idx = [i for i in range(n) if pc[i] > rc_cap_arr[i]]
    rc_cap_viol_tickers = [cols[i] for i in viol_idx] if viol_idx else []

    w_dict = {t: float(w[i]) for i, t in enumerate(cols)}
    for t in risk_list:
        if t not in w_dict:
            w_dict[t] = 0.0

    status_parts = []
    status_parts.append("OK_FALLBACK" if used_fallback else "OK")
    if rc_cap_viol_tickers:
        status_parts.append(f"VIOL_RC_ASSET_CAP: {rc_cap_viol_tickers}")
    status_parts.append(f"RC_CAP_PENALTY_LAMBDA={penalty_lambda:.2f}")
    status_parts.append(f"OBJECTIVE_MODE={obj_mode}")
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


RC_POSTPROCESS_MAX_ITER = 200
RC_POSTPROCESS_STEP_PCT = 0.005


def enforce_rc_caps_postprocess(
    weights_risk: dict[str, float],
    cov_df: pd.DataFrame,
    growth_core_candidates: list[str],
    rc_asset_cap: float | list[float],
    min_weight: float,
    max_single_security_weight_pct: float | None,
    risk_tickers: list[str],
    max_iterations: int = RC_POSTPROCESS_MAX_ITER,
    step_pct: float = RC_POSTPROCESS_STEP_PCT,
    per_ticker_max_weight: dict[str, float] | None = None,
    rc_cap_by_ticker: dict[str, float] | None = None,
) -> tuple[dict[str, float], bool, dict]:
    """
    Iteratively reduce weight from assets above RC cap; reallocate to VOO/VT/VTI then lowest-vol names.
    """
    cols = [
        t for t in risk_tickers
        if t in weights_risk and t in cov_df.columns and t in cov_df.index and weights_risk.get(t, 0) > 0
    ]
    if not cols:
        return dict(weights_risk), True, {}
    n = len(cols)
    bounds = _build_bounds(
        cols, n, min_weight, growth_core_candidates,
        max_single_security_weight_pct, per_ticker_max_weight,
    )
    cov = cov_df.reindex(index=cols, columns=cols).fillna(0).values
    w = np.array([weights_risk[t] for t in cols], dtype=float)

    if rc_cap_by_ticker is not None:
        cap_row = [float(rc_cap_by_ticker.get(t, 1.0)) for t in cols]
    elif isinstance(rc_asset_cap, (int, float)):
        cap_row = [float(rc_asset_cap)] * n
    else:
        cap_row = [float(x) for x in rc_asset_cap]
        if len(cap_row) != n:
            return dict(weights_risk), False, {"reason": "rc_cap_len_mismatch", "n": n, "caps": len(cap_row)}

    vol_per = np.sqrt(np.maximum(np.diag(cov), 1e-20))
    hedge_vol = [(t, vol_per[cols.index(t)]) for t in cols]
    hedge_vol.sort(key=lambda x: (x[1], x[0]))
    recipient_order = [t for t in ("VOO", "VT", "VTI") if t in cols]
    recipient_order += [t for t, _ in hedge_vol if t not in recipient_order]

    for it in range(max_iterations):
        var_p = variance_p(w, cov)
        if var_p <= 1e-16:
            break
        pc = (w * (cov @ w)) / var_p
        violators = [i for i in range(n) if pc[i] > cap_row[i] + 1e-9]
        if not violators:
            s = float(w.sum())
            if s > 1e-12:
                w = w / s
            out = {t: float(w[j]) for j, t in enumerate(cols)}
            for t in risk_tickers:
                if t not in out:
                    out[t] = 0.0
            return out, True, {"iterations": it, "rc_cap": cap_row}

        violators.sort(key=lambda i: (-pc[i], cols[i]))
        donor_idx = violators[0]
        lo, hi = bounds[donor_idx]
        delta_max = float(w[donor_idx] - lo)
        if delta_max <= 1e-9:
            out = {t: float(w[j]) for j, t in enumerate(cols)}
            for t in risk_tickers:
                if t not in out:
                    out[t] = 0.0
            return out, False, {
                "iterations": it,
                "remaining_violators": [cols[i] for i in violators],
                "reason": "donor_at_min",
            }
        delta = min(step_pct, delta_max)

        total_recipient_space = 0.0
        for rec_ticker in recipient_order:
            j = cols.index(rec_ticker)
            rec_hi = bounds[j][1]
            total_recipient_space += max(0.0, rec_hi - w[j])
        transfer = min(delta, total_recipient_space)
        if transfer <= 1e-12:
            out = {t: float(w[j]) for j, t in enumerate(cols)}
            for t in risk_tickers:
                if t not in out:
                    out[t] = 0.0
            return out, False, {"iterations": it, "reason": "recipient_caps_full"}

        w[donor_idx] -= transfer
        remaining = transfer
        for rec_ticker in recipient_order:
            if remaining <= 1e-12:
                break
            j = cols.index(rec_ticker)
            rec_hi = bounds[j][1]
            space = max(0.0, rec_hi - w[j])
            if space <= 1e-12:
                continue
            add = min(remaining, space)
            w[j] += add
            remaining -= add
        w = np.clip(w, [b[0] for b in bounds], [b[1] for b in bounds])

    var_p = variance_p(w, cov)
    pc = (w * (cov @ w)) / var_p if var_p > 1e-16 else np.ones(n) / n
    violators = [i for i in range(n) if pc[i] > cap_row[i] + 1e-9]
    out = {t: float(w[j]) for j, t in enumerate(cols)}
    for t in risk_tickers:
        if t not in out:
            out[t] = 0.0
    return out, False, {
        "iterations": max_iterations,
        "remaining_violators": [cols[i] for i in violators],
        "reason": "max_iterations",
    }


def _alpha_shift_to_target_vol(
    weights_risk: dict[str, float],
    cov_df: pd.DataFrame,
    target_vol_annual: float,
    n_rc: int,
    donor_shift_mode: str,
    growth_core_candidates: list[str],
) -> tuple[dict[str, float], str | None]:
    tickers = [t for t in weights_risk if t in cov_df.columns and t in cov_df.index]
    if not tickers:
        return dict(weights_risk), "No risk assets in covariance for alpha shift."
    cov = cov_df.reindex(index=tickers, columns=tickers).fillna(0).values
    w = np.array([weights_risk[t] for t in tickers])
    current_vol = float(np.sqrt(variance_p(w, cov) * 12)) if variance_p(w, cov) > 0 else 0.0
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
            if t in growth_core_candidates:
                continue
            idx = tickers.index(t)
            vol_t = float(np.sqrt(cov[idx, idx] * 12)) if cov[idx, idx] > 0 else 0.0
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
        vol_new = float(np.sqrt(var_p * 12)) if var_p > 0 else 0.0
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
    vol_final = float(np.sqrt(variance_p(w_final, cov) * 12)) if variance_p(w_final, cov) > 0 else 0.0
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
    growth_core_candidates: list[str] | None = None,
) -> tuple[dict[str, float], str | None]:
    if cash_policy == "prohibited":
        if (
            current_vol_annual > target_vol_annual
            and cov_df is not None
            and growth_core_candidates is not None
        ):
            shifted, err = _alpha_shift_to_target_vol(
                weights_risk,
                cov_df,
                target_vol_annual,
                n_rc,
                donor_shift_mode,
                growth_core_candidates,
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


def portfolio_vol_annual(weights: dict[str, float], cov_df: pd.DataFrame) -> float:
    tickers = [t for t in weights if t in cov_df.columns and t in cov_df.index]
    if not tickers:
        return 0.0
    w = np.array([weights[t] for t in tickers])
    cov = cov_df.reindex(index=tickers, columns=tickers).fillna(0).values
    var = variance_p(w, cov)
    return float(np.sqrt(var * 12)) if var > 0 else 0.0


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
