"""
Portfolio stress testing per docs/docs/stress_testing_spec.md (asset-level suite).

Synthetic scenarios are factor shocks applied to the whole portfolio. Outputs:
portfolio PnL, per-asset PnL, optional per-factor portfolio PnL from betas, and
RC concentration as diagnostics only.

Synthetic **pass** = portfolio PnL vs client mandate max drawdown (same threshold as loss_ok).
RC Top1/Top3 (share of variance) are reported per scenario for diagnostics only; they do not affect status.
Mandate MaxDD on full history is enforced in run_optimization (FAIL_MANDATE), not here.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.risk_contrib import cov_matrix_monthly, percentage_contributions_variance

# Scenario ids and shock vectors (shock_eq, shock_rr, shock_credit, shock_inf, shock_usd, shock_cmd)
SCENARIOS = {
    "equity_shock": {
        "shock_eq": -0.40,
        "shock_rr": 0.0,
        "shock_credit": 0.0,
        "shock_inf": 0.0,
        "shock_usd": 0.0,
        "shock_cmd": 0.0,
        "vol_mult": 1.25,
        "stress_cov": True,
    },
    "credit_shock": {
        "shock_eq": -0.10,
        "shock_rr": 0.0,
        "shock_credit": 0.04,
        "shock_inf": 0.0,
        "shock_usd": 0.0,
        "shock_cmd": 0.0,
        "vol_mult": 1.25,
        "stress_cov": True,
    },
    "rates_shock": {
        "shock_eq": 0.0,
        "shock_rr": 0.02,
        "shock_credit": 0.0,
        "shock_inf": 0.0,
        "shock_usd": 0.0,
        "shock_cmd": 0.0,
        "vol_mult": 1.0,
        "stress_cov": False,
    },
    "inflation_stagflation": {
        "shock_eq": -0.20,
        "shock_rr": 0.005,
        "shock_credit": 0.0,
        "shock_inf": 0.0,
        "shock_usd": 0.0,
        "shock_cmd": 0.25,
        "vol_mult": 1.0,
        "stress_cov": False,
    },
    "liquidity_shock": {
        "shock_eq": -0.25,
        "shock_rr": 0.0,
        "shock_credit": 0.03,
        "shock_inf": 0.0,
        "shock_usd": 0.0,
        "shock_cmd": 0.0,
        "vol_mult": 1.50,
        "stress_cov": True,
    },
}

HISTORICAL_EPISODES = [
    ("dotcom", "2000-03-01", "2002-10-31"),
    ("2008", "2007-10-01", "2009-03-31"),
    ("2020", "2020-02-01", "2020-04-30"),
    ("2022", "2021-11-01", "2022-10-31"),
]

_SCENARIO_SUFFIX = {
    "equity_shock": "EQUITY_SHOCK",
    "credit_shock": "CREDIT_SHOCK",
    "rates_shock": "RATES_SHOCK",
    "liquidity_shock": "LIQUIDITY_SHOCK",
    "inflation_stagflation": "INFLATION_STAGFLATION",
}


def _scenario_suffix(scenario_id: str) -> str:
    return _SCENARIO_SUFFIX.get(scenario_id, scenario_id.upper().replace("-", "_"))


def _build_diagnostic_code(failed_test: str | None, failed_scenario: str | None) -> str | None:
    if not failed_test or not failed_scenario:
        return None
    if failed_test == "Historical":
        return f"DIAG_HIST_{failed_scenario}"
    if failed_test == "Loss":
        return f"DIAG_LOSS_{_scenario_suffix(failed_scenario)}"
    return None


def _build_fail_reason_code(failed_test: str | None, failed_scenario: str | None) -> str | None:
    return _build_diagnostic_code(failed_test, failed_scenario)


def _build_warning_code(warning_reason: str | None) -> str | None:
    if not warning_reason:
        return None
    return f"WARN_{warning_reason}"


_SHOCK_TO_BETA = (
    ("shock_eq", "beta_eq"),
    ("shock_rr", "beta_rr"),
    ("shock_credit", "beta_credit"),
    ("shock_inf", "beta_inf"),
    ("shock_usd", "beta_usd"),
    ("shock_cmd", "beta_cmd"),
)
_BETA_TO_FACTOR_SHORT = {
    "beta_eq": "eq",
    "beta_rr": "rr",
    "beta_credit": "credit",
    "beta_inf": "inf",
    "beta_usd": "usd",
    "beta_cmd": "cmd",
}


def _portfolio_factor_pnl_pct(
    shock: dict[str, float],
    portfolio_betas: dict[str, float],
) -> dict[str, float]:
    """Portfolio-level PnL contribution per factor: shock_k * beta_port_k (linear factor map)."""
    out: dict[str, float] = {}
    for sk, bk in _SHOCK_TO_BETA:
        if sk not in shock or bk not in portfolio_betas:
            continue
        try:
            bpv = float(portfolio_betas[bk])
            sv = float(shock[sk])
        except (TypeError, ValueError):
            continue
        short = _BETA_TO_FACTOR_SHORT.get(bk)
        if short is None:
            continue
        prod = round(sv * bpv, 4)
        if prod != 0.0:
            out[short] = prod
    return out


def _scenario_return_per_asset(
    shock: dict[str, float],
    betas: pd.DataFrame,
    tickers: list[str],
) -> pd.Series:
    """r_i from factor betas when available; else conservative equity shock proxy."""
    r: dict[str, float] = {}
    for t in tickers:
        if t in betas.index:
            row = betas.loc[t]
            ri = 0.0
            for key, val in shock.items():
                if key in ("vol_mult", "stress_cov"):
                    continue
                beta_col = f"beta_{key.replace('shock_', '')}"
                if beta_col in row.index and pd.notna(row[beta_col]):
                    ri += float(row[beta_col]) * float(val)
            r[t] = ri
        else:
            r[t] = float(shock.get("shock_eq", 0.0))
    return pd.Series(r)


def _stress_covariance(
    cov_base: pd.DataFrame,
    risk_on_tickers: list[str],
    vol_mult: float,
) -> pd.DataFrame:
    """Within risk-on: corr ≈ 0.90; vol *= vol_mult. Other pairs keep base correlation."""
    tickers = list(cov_base.columns)
    n = len(tickers)
    if n == 0:
        return cov_base
    risk_on_set = set(risk_on_tickers)
    vol_base = np.sqrt(np.maximum(np.diag(cov_base.values), 1e-12))
    corr = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if vol_base[i] * vol_base[j] > 1e-12:
                corr[i, j] = cov_base.values[i, j] / (vol_base[i] * vol_base[j])
            else:
                corr[i, j] = 1.0 if i == j else 0.0
    np.fill_diagonal(corr, 1.0)
    for i, ti in enumerate(tickers):
        for j, tj in enumerate(tickers):
            if ti in risk_on_set and tj in risk_on_set:
                corr[i, j] = 0.90
    vol = vol_base.copy()
    for i, t in enumerate(tickers):
        if t in risk_on_set:
            vol[i] *= vol_mult
    cov_stress = np.outer(vol, vol) * corr
    np.fill_diagonal(cov_stress, vol**2)
    return pd.DataFrame(cov_stress, index=tickers, columns=tickers)


def run_stress(
    tickers: list[str],
    weights: dict[str, float],
    monthly_returns: pd.DataFrame,
    asset_betas: pd.DataFrame,
    portfolio_betas: dict[str, float],
    target_max_drawdown_pct: float | None,
    cash_proxy_ticker: str | None = None,
    **_: Any,
) -> dict[str, Any]:
    """
    Diagnostic stress suite (non-blocking). Status: DIAG_PASS | DIAG_PASS_WITH_WARNING | DIAG_ATTENTION.

    Synthetic scenarios: factor shocks to the **whole portfolio**; **pass** = portfolio PnL ≥ −mandate MaxDD
    (same as loss_ok). Top1/Top3 RC (variance shares) are informational fields on each scenario row.

    Historical episodes: same row fields; pass = episode max drawdown vs mandate (see spec).
    """
    cash_u = (cash_proxy_ticker or "").strip().upper()
    asset_cols = [t for t in tickers if t in monthly_returns.columns]
    if not asset_cols:
        return _empty_report("No return data for stress")
    returns_sub = monthly_returns[asset_cols].dropna(how="all")
    if len(returns_sub) < 2:
        return _empty_report("Insufficient return history")

    max_dd_limit = abs(target_max_drawdown_pct) if target_max_drawdown_pct is not None else 0.25

    cov_base = cov_matrix_monthly(returns_sub, ddof=1)
    risk_on = [t for t in asset_cols if str(t).strip().upper() != cash_u]

    w_vec = np.array([weights.get(t, 0.0) for t in asset_cols])
    w_vec = w_vec / w_vec.sum() if w_vec.sum() > 0 else w_vec

    scenario_results = []
    worst_loss = 0.0

    for scenario_id, params in SCENARIOS.items():
        shock = {k: v for k, v in params.items() if k.startswith("shock_") and isinstance(v, (int, float))}
        vol_mult = float(params.get("vol_mult", 1.0))
        use_stress_cov = bool(params.get("stress_cov", False))

        r_asset = _scenario_return_per_asset(shock, asset_betas, asset_cols)
        r_asset = r_asset.reindex(asset_cols).fillna(0)
        pnl_i = w_vec * r_asset.values
        portfolio_pnl_pct = float(np.sum(pnl_i))

        if use_stress_cov:
            cov_s = _stress_covariance(cov_base, risk_on, vol_mult)
        else:
            cov_s = cov_base.copy()

        pc = percentage_contributions_variance(w_vec, cov_s.values)
        pc_series = pd.Series(pc, index=asset_cols).sort_values(ascending=False)
        top1_asset = pc_series.index[0] if len(pc_series) else None
        top1_rc_pct = float(pc_series.iloc[0]) if len(pc_series) else 0.0
        top3_assets = list(pc_series.index[:3])
        top3_rc_sum_pct = float(pc_series.iloc[:3].sum())

        pnl_contrib = pd.Series(pnl_i, index=asset_cols)
        top3_loss_assets = list(pnl_contrib.sort_values().head(3).index)

        loss_ok = portfolio_pnl_pct >= -max_dd_limit
        scenario_pass = loss_ok

        loss_diags: list[str] = []
        if not loss_ok:
            c = _build_diagnostic_code("Loss", scenario_id)
            if c:
                loss_diags.append(c)

        if portfolio_pnl_pct < worst_loss:
            worst_loss = portfolio_pnl_pct

        pnl_by_asset_pct = {str(asset_cols[i]): round(float(pnl_i[i]), 4) for i in range(len(asset_cols))}
        pnl_by_factor_pct = _portfolio_factor_pnl_pct(shock, portfolio_betas)

        scenario_results.append({
            "scenario_id": scenario_id,
            "portfolio_pnl_pct": round(portfolio_pnl_pct, 4),
            "pnl_by_asset_pct": pnl_by_asset_pct,
            "pnl_by_factor_pct": pnl_by_factor_pct,
            "top1_rc_asset": top1_asset,
            "top1_rc_pct": round(top1_rc_pct, 4),
            "top3_rc_assets": top3_assets,
            "top3_rc_sum_pct": round(top3_rc_sum_pct, 4),
            "top3_loss_assets": top3_loss_assets,
            "loss_ok": loss_ok,
            "pass": scenario_pass,
            "diagnostic_codes": loss_diags,
        })

    factor_betas = {k: round(v, 4) for k, v in portfolio_betas.items()}

    historical_results = []
    for ep_id, start, end in HISTORICAL_EPISODES:
        try:
            sub = returns_sub.loc[start:end] if hasattr(returns_sub.index, "slice_indexer") else returns_sub
            if sub.empty or len(sub) < 2:
                historical_results.append({
                    "episode": ep_id,
                    "episode_start": start,
                    "episode_end": end,
                    "max_dd": None,
                    "pnl_real_episode": None,
                    "vol_annualized_episode": None,
                    "volatility_spike_ratio": None,
                    "pass": None,
                    "diagnostic_code": None,
                })
                continue
            port_ret = sub.dot(w_vec)
            port_eq = (1 + port_ret).cumprod()
            port_dd = port_eq / port_eq.cummax() - 1
            max_dd = float(port_dd.min())
            pnl_real_episode = float(port_eq.iloc[-1] - 1.0) if len(port_eq) else None
            pass_dd = max_dd >= -max_dd_limit

            vol_ep = float(port_ret.std(ddof=1)) if len(port_ret) >= 2 else np.nan
            vol_annualized_episode = round(float(vol_ep * np.sqrt(12)), 4) if np.isfinite(vol_ep) else None

            episode_start_ts = pd.Timestamp(start)
            pre = returns_sub.loc[returns_sub.index < episode_start_ts]
            pre_len = min(len(pre), len(port_ret))
            if pre_len >= 2 and np.isfinite(vol_ep):
                pre_port_ret = pre.tail(pre_len).dot(w_vec)
                vol_pre = float(pre_port_ret.std(ddof=1)) if len(pre_port_ret) >= 2 else np.nan
                vol_spike = (vol_ep / vol_pre) if np.isfinite(vol_pre) and vol_pre > 0 else np.nan
            else:
                vol_spike = np.nan

            historical_results.append({
                "episode": ep_id,
                "episode_start": start,
                "episode_end": end,
                "max_dd": round(max_dd, 4),
                "pnl_real_episode": round(float(pnl_real_episode), 4) if pnl_real_episode is not None else None,
                "vol_annualized_episode": vol_annualized_episode,
                "volatility_spike_ratio": round(float(vol_spike), 4) if np.isfinite(vol_spike) else None,
                "pass": pass_dd,
                "diagnostic_code": _build_diagnostic_code("Historical", ep_id) if pass_dd is False else None,
            })
        except Exception:
            historical_results.append({
                "episode": ep_id,
                "episode_start": start,
                "episode_end": end,
                "max_dd": None,
                "pnl_real_episode": None,
                "vol_annualized_episode": None,
                "volatility_spike_ratio": None,
                "pass": None,
                "diagnostic_code": None,
            })

    diagnostic_codes: list[str] = []
    seen_codes: set[str] = set()

    def _push_diag(code: str | None) -> None:
        if code and code not in seen_codes:
            seen_codes.add(code)
            diagnostic_codes.append(code)

    for s in scenario_results:
        for c in s.get("diagnostic_codes") or []:
            _push_diag(c)
    for h in historical_results:
        if h.get("pass") is False:
            _push_diag(h.get("diagnostic_code") or _build_diagnostic_code("Historical", str(h.get("episode", ""))))

    hist_inconclusive = any(h.get("pass") is None and h.get("max_dd") is None for h in historical_results)

    primary_diagnostic_code = diagnostic_codes[0] if diagnostic_codes else None
    failed_test: str | None = None
    failed_scenario: str | None = None
    if primary_diagnostic_code:
        if primary_diagnostic_code.startswith("DIAG_HIST_"):
            failed_test = "Historical"
            failed_scenario = primary_diagnostic_code.replace("DIAG_HIST_", "", 1)
        elif primary_diagnostic_code.startswith("DIAG_LOSS_"):
            failed_test = "Loss"
            failed_scenario = next(
                (x["scenario_id"] for x in scenario_results if primary_diagnostic_code in (x.get("diagnostic_codes") or [])),
                None,
            )

    if diagnostic_codes:
        status = "DIAG_ATTENTION"
        fail_reason_code = primary_diagnostic_code
        warning_code = None
    elif hist_inconclusive:
        status = "DIAG_PASS_WITH_WARNING"
        fail_reason_code = None
        warning_code = _build_warning_code("HIST_BORDERLINE")
    else:
        status = "DIAG_PASS"
        fail_reason_code = None
        warning_code = None

    return {
        "status": status,
        "diagnostic_codes": diagnostic_codes,
        "primary_diagnostic_code": primary_diagnostic_code,
        "fail_reason_code": fail_reason_code,
        "warning_code": warning_code,
        "worst_scenario_loss_pct": round(worst_loss, 4),
        "failed_scenario": failed_scenario,
        "failed_test": failed_test,
        "scenario_results": scenario_results,
        "factor_betas": factor_betas,
        "historical_results": historical_results,
        "max_dd_limit": max_dd_limit,
    }


def _empty_report(reason: str) -> dict[str, Any]:
    return {
        "status": "DIAG_PASS_WITH_WARNING",
        "diagnostic_codes": [],
        "primary_diagnostic_code": None,
        "fail_reason_code": None,
        "warning_code": _build_warning_code("DATA_INSUFFICIENT"),
        "worst_scenario_loss_pct": None,
        "failed_scenario": None,
        "failed_test": None,
        "scenario_results": [],
        "factor_betas": {},
        "historical_results": [],
        "max_dd_limit": None,
        "skip_reason": reason,
    }
