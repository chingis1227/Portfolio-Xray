"""
Portfolio stress testing per docs/docs/stress_testing_spec.md.
Scenarios: Equity, Credit, Rates, Inflation/Stagflation, Liquidity.
Diagnostic suite: synthetic scenario PnL, Role/RC checks, historical episodes — non-blocking (DIAG_* codes).
Mandate MaxDD on full history is enforced in run_optimization (FAIL_MANDATE), not here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from src.blocks import STRESS_BLOCK_NAMES, get_ticker_to_block_for_stress
from src.config_schema import GROWTH_EM_DEBT_KEY, GROWTH_HY_KEY
from policy_math.feasibility import (
    DEFAULT_RC_CAP_RB_K_MULTIPLIER,
    RC_CAP_MODE_GLOBAL,
    RC_CAP_MODE_PER_BLOCK_RB_K,
)
from src.risk_contrib import (
    build_rc_cap_per_ticker,
    cov_matrix_monthly,
    percentage_contributions_variance,
    resolve_rc_asset_cap,
)


def _rc_cap_for_ticker_stress(
    ticker: str | None,
    blocks: dict[str, list[str]],
    rc_asset_cap_pct: float | None,
    rc_cap_mode: str,
    rc_cap_rb_k_multiplier: float,
    rc_block_targets: dict[str, float] | None,
    n_assets: int,
) -> float:
    if rc_asset_cap_pct is not None and rc_asset_cap_pct > 0:
        return float(rc_asset_cap_pct)
    if rc_cap_mode == RC_CAP_MODE_PER_BLOCK_RB_K and rc_block_targets:
        cmap = build_rc_cap_per_ticker(
            blocks,
            rc_block_targets,
            None,
            rc_cap_mode,
            rc_cap_rb_k_multiplier,
            max(n_assets, 1),
        )
        if ticker and ticker in cmap:
            return float(cmap[ticker])
        return float(next(iter(cmap.values()), 0.25)) if cmap else 0.25
    return resolve_rc_asset_cap(rc_asset_cap_pct, max(n_assets, 1), rb_growth=None)

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
    ("2008", "2007-10-01", "2009-03-31"),
    ("2020", "2020-02-15", "2020-04-30"),
    ("2022", "2021-11-01", "2022-10-31"),
]

# Equity shock — defensive bundle S = sum(Duration, Inflation, Tail) PnL; decimals like pnl_by_block_pct (stress_testing_spec §6)
EQUITY_DEFENSIVE_SUM_FAIL_BELOW = -0.01  # S < -0.01 → Role fail; −0.01 ≤ S < 0 → Role warn if Loss+RC pass

# Scenario id -> suffix for fail_reason_code (e.g. equity_shock -> EQUITY_SHOCK)
_SCENARIO_SUFFIX = {
    "equity_shock": "EQUITY_SHOCK",
    "credit_shock": "CREDIT_SHOCK",
    "rates_shock": "RATES_SHOCK",
    "liquidity_shock": "LIQUIDITY_SHOCK",
    "inflation_stagflation": "INFLATION_STAGFLATION",  # for Loss/RC; for Role use STAGFLATION
}


def _scenario_suffix(scenario_id: str, for_role: bool = False) -> str:
    """Scenario id to code suffix (e.g. EQUITY_SHOCK). For Role, inflation_stagflation -> STAGFLATION."""
    if for_role and scenario_id == "inflation_stagflation":
        return "STAGFLATION"
    return _SCENARIO_SUFFIX.get(scenario_id, scenario_id.upper().replace("-", "_"))


def _build_diagnostic_code(failed_test: str | None, failed_scenario: str | None) -> str | None:
    """
    Non-blocking diagnostic codes for PM reports: DIAG_<TEST>_<SUFFIX>.
    Examples: DIAG_LOSS_EQUITY_SHOCK, DIAG_ROLE_STAGFLATION, DIAG_RC_TOP1_LIQUIDITY_SHOCK,
    DIAG_HIST_2022.
    """
    if not failed_test or not failed_scenario:
        return None
    if failed_test == "Historical":
        return f"DIAG_HIST_{failed_scenario}"
    if failed_test == "Loss":
        return f"DIAG_LOSS_{_scenario_suffix(failed_scenario, for_role=False)}"
    if failed_test == "Role":
        return f"DIAG_ROLE_{_scenario_suffix(failed_scenario, for_role=True)}"
    if failed_test == "RC_Top1":
        return f"DIAG_RC_TOP1_{_scenario_suffix(failed_scenario, for_role=False)}"
    if failed_test == "RC_Top3":
        return f"DIAG_RC_TOP3_{_scenario_suffix(failed_scenario, for_role=False)}"
    if failed_test and failed_test.startswith("Beta"):
        factor = failed_scenario.replace("-", "_").upper() if failed_scenario else "UNKNOWN"
        return f"DIAG_BETA_{factor}"
    return None


def _build_fail_reason_code(failed_test: str | None, failed_scenario: str | None) -> str | None:
    """Alias of _build_diagnostic_code (legacy field name fail_reason_code in JSON)."""
    return _build_diagnostic_code(failed_test, failed_scenario)


def _build_warning_code(warning_reason: str | None) -> str | None:
    """Build warning_code for PASS_WITH_WARNING (e.g. WARN_BETA_NO_LIMITS, WARN_HIST_BORDERLINE)."""
    if not warning_reason:
        return None
    return f"WARN_{warning_reason}"


def _ticker_to_stress_block(blocks: dict[str, list[str]], tickers: list[str] | None = None) -> dict[str, str]:
    """Map each ticker to one of Growth, Duration, Inflation, Liquidity, Tail. Delegates to blocks.get_ticker_to_block_for_stress."""
    return get_ticker_to_block_for_stress(blocks, tickers)


def _scenario_return_per_asset(
    shock: dict[str, float],
    betas: pd.DataFrame,
    tickers: list[str],
    ticker_to_block: dict[str, str],
) -> pd.Series:
    """
    r_i = beta_eq*shock_eq + beta_rr*shock_rr + ... + beta_cmd*shock_cmd.
    If beta missing for asset, use block fallback: Growth->shock_eq, Duration->shock_rr, Inflation->shock_cmd, Liquidity->0, Tail->shock_eq (conservative).
    """
    r = {}
    for t in tickers:
        if t not in betas.index:
            block = ticker_to_block.get(t, "Growth")
            if block == "Growth":
                ri = shock["shock_eq"]
            elif block == "Duration":
                ri = shock["shock_rr"] * (-1)  # duration typically loses when rates up
            elif block == "Inflation":
                ri = shock["shock_cmd"]
            elif block == "Liquidity":
                ri = 0.0
            else:
                ri = shock["shock_eq"]
            r[t] = ri
            continue
        row = betas.loc[t]
        ri = 0.0
        for key, val in shock.items():
            if key in ("vol_mult", "stress_cov"):
                continue
            beta_col = f"beta_{key.replace('shock_', '')}"
            if beta_col in row.index and pd.notna(row[beta_col]):
                ri += row[beta_col] * val
        r[t] = ri
    return pd.Series(r)


def _stress_covariance(
    cov_base: pd.DataFrame,
    blocks: dict[str, list[str]],
    risk_on_tickers: list[str],
    vol_mult: float,
) -> pd.DataFrame:
    """
    Within risk-on (Growth + Growth_HY + Growth_EM_debt): corr = 0.90; vol *= vol_mult.
    Between risk-on and rest: keep base correlation; volatilities scaled for risk-on.
    """
    tickers = list(cov_base.columns)
    n = len(tickers)
    if n == 0:
        return cov_base
    risk_on_set = set(risk_on_tickers)
    vol_base = np.sqrt(np.maximum(np.diag(cov_base.values), 1e-12))
    # Correlation from cov: R_ij = cov_ij / (sigma_i * sigma_j)
    corr = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if vol_base[i] * vol_base[j] > 1e-12:
                corr[i, j] = cov_base.values[i, j] / (vol_base[i] * vol_base[j])
            else:
                corr[i, j] = 1.0 if i == j else 0.0
    np.fill_diagonal(corr, 1.0)
    # Override risk-on block to 0.90
    for i, ti in enumerate(tickers):
        for j, tj in enumerate(tickers):
            if ti in risk_on_set and tj in risk_on_set:
                corr[i, j] = 0.90
    # Scale vol for risk-on
    vol = vol_base.copy()
    for i, t in enumerate(tickers):
        if t in risk_on_set:
            vol[i] *= vol_mult
    # Cov_stress = D @ Corr @ D
    cov_stress = np.outer(vol, vol) * corr
    np.fill_diagonal(cov_stress, vol ** 2)
    return pd.DataFrame(cov_stress, index=tickers, columns=tickers)


def run_stress(
    tickers: list[str],
    weights: dict[str, float],
    blocks: dict[str, list[str]],
    monthly_returns: pd.DataFrame,
    asset_betas: pd.DataFrame,
    portfolio_betas: dict[str, float],
    target_max_drawdown_pct: float | None,
    rc_asset_cap_pct: float | None,
    stress_top3_rc_sum_cap_pct: float,
    rc_cap_mode: str = RC_CAP_MODE_GLOBAL,
    rc_cap_rb_k_multiplier: float = DEFAULT_RC_CAP_RB_K_MULTIPLIER,
    rc_block_targets: dict[str, float] | None = None,
) -> dict[str, Any]:
    """
    Run full diagnostic stress suite (non-blocking). Status is DIAG_PASS | DIAG_PASS_WITH_WARNING | DIAG_ATTENTION.
    """
    ticker_to_block = _ticker_to_stress_block(blocks, tickers)
    risk_on_tickers = (
        list(blocks.get("Growth", []))
        + list(blocks.get(GROWTH_HY_KEY, []))
        + list(blocks.get(GROWTH_EM_DEBT_KEY, []))
    )
    n_assets = len([t for t in tickers if t in weights and weights.get(t, 0) > 0])
    rc_cap = resolve_rc_asset_cap(rc_asset_cap_pct, max(n_assets, 1), rb_growth=None)
    max_dd_limit = abs(target_max_drawdown_pct) if target_max_drawdown_pct is not None else 0.25

    # Base covariance (RiskPortfolio assets only)
    asset_cols = [t for t in tickers if t in monthly_returns.columns]
    if not asset_cols:
        return _empty_report("No return data for stress")
    returns_sub = monthly_returns[asset_cols].dropna(how="all")
    if len(returns_sub) < 2:
        return _empty_report("Insufficient return history")
    cov_base = cov_matrix_monthly(returns_sub, ddof=1)

    w_vec = np.array([weights.get(t, 0.0) for t in asset_cols])
    w_vec = w_vec / w_vec.sum() if w_vec.sum() > 0 else w_vec

    scenario_results = []
    worst_loss = 0.0

    for scenario_id, params in SCENARIOS.items():
        shock = {k: v for k, v in params.items() if k.startswith("shock_") and isinstance(v, (int, float))}
        vol_mult = params.get("vol_mult", 1.0)
        use_stress_cov = params.get("stress_cov", False)

        r_asset = _scenario_return_per_asset(shock, asset_betas, asset_cols, ticker_to_block)
        r_asset = r_asset.reindex(asset_cols).fillna(0)
        pnl_i = w_vec * r_asset.values
        portfolio_pnl_pct = float(np.sum(pnl_i))

        pnl_by_block = {}
        for b in STRESS_BLOCK_NAMES:
            idx = [i for i, t in enumerate(asset_cols) if ticker_to_block.get(t) == b]
            pnl_by_block[b] = float(np.sum(pnl_i[idx])) if idx else 0.0

        if use_stress_cov:
            cov_s = _stress_covariance(cov_base, blocks, risk_on_tickers, vol_mult)
        else:
            cov_s = cov_base.copy()

        pc = percentage_contributions_variance(w_vec, cov_s.values)
        pc_series = pd.Series(pc, index=asset_cols)
        pc_series = pc_series.sort_values(ascending=False)
        top1_asset = pc_series.index[0] if len(pc_series) else None
        top1_rc_pct = float(pc_series.iloc[0]) if len(pc_series) else 0.0
        top3_assets = list(pc_series.index[:3])
        top3_rc_sum_pct = float(pc_series.iloc[:3].sum())

        # Top3 loss = assets with largest (negative) PnL contribution
        pnl_contrib = pd.Series(pnl_i, index=asset_cols)
        top3_loss_assets = list(pnl_contrib.sort_values().head(3).index)

        # Tests
        loss_ok = portfolio_pnl_pct >= -max_dd_limit
        equity_defensive_sum: float | None = None
        role_equity_shock_severity: str | None = None
        if scenario_id == "inflation_stagflation":
            role_ok = pnl_by_block.get("Inflation", 0) > 0
        elif scenario_id == "equity_shock":
            equity_defensive_sum = _equity_defensive_sum(pnl_by_block)
            role_equity_shock_severity = _equity_shock_role_severity(equity_defensive_sum)
            role_ok = role_equity_shock_severity != "fail"
        else:
            role_ok = True
        rc1_thr = _rc_cap_for_ticker_stress(
            str(top1_asset) if top1_asset is not None else None,
            blocks,
            rc_asset_cap_pct,
            rc_cap_mode,
            rc_cap_rb_k_multiplier,
            rc_block_targets,
            n_assets,
        )
        rc1_ok = top1_rc_pct <= rc1_thr
        rc3_ok = top3_rc_sum_pct <= stress_top3_rc_sum_cap_pct
        scenario_pass = loss_ok and role_ok and rc1_ok and rc3_ok

        row_diags: list[str] = []
        if not loss_ok:
            c = _build_diagnostic_code("Loss", scenario_id)
            if c:
                row_diags.append(c)
        if not role_ok:
            c = _build_diagnostic_code("Role", scenario_id)
            if c:
                row_diags.append(c)
        if not rc1_ok:
            c = _build_diagnostic_code("RC_Top1", scenario_id)
            if c:
                row_diags.append(c)
        if not rc3_ok:
            c = _build_diagnostic_code("RC_Top3", scenario_id)
            if c:
                row_diags.append(c)

        if portfolio_pnl_pct < worst_loss:
            worst_loss = portfolio_pnl_pct

        row: dict[str, Any] = {
            "scenario_id": scenario_id,
            "portfolio_pnl_pct": round(portfolio_pnl_pct, 4),
            "pnl_by_block_pct": {k: round(v, 4) for k, v in pnl_by_block.items()},
            "top1_rc_asset": top1_asset,
            "top1_rc_pct": round(top1_rc_pct, 4),
            "top3_rc_assets": top3_assets,
            "top3_rc_sum_pct": round(top3_rc_sum_pct, 4),
            "top3_loss_assets": top3_loss_assets,
            "loss_ok": loss_ok,
            "role_ok": role_ok,
            "rc1_ok": rc1_ok,
            "rc3_ok": rc3_ok,
            "top1_rc_cap_threshold": round(rc1_thr, 4),
            "pass": scenario_pass,
            "diagnostic_codes": row_diags,
        }
        if equity_defensive_sum is not None:
            row["defensive_pnl_sum"] = round(equity_defensive_sum, 4)
            row["role_equity_shock_severity"] = role_equity_shock_severity
        scenario_results.append(row)

    # Factor validation: output only (no limits for now)
    factor_betas = {k: round(v, 4) for k, v in portfolio_betas.items()}

    # Historical validation: max DD + volatility spike + stress correlations
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
                    "mean_monthly_return_by_block_pct": {},
                    "volatility_spike_ratio": None,
                    "stress_correlations": {},
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

            # Volatility spike: episode volatility vs same-length window immediately before episode.
            vol_ep = float(port_ret.std(ddof=1)) if len(port_ret) >= 2 else np.nan
            vol_annualized_episode = round(float(vol_ep * np.sqrt(12)), 4) if np.isfinite(vol_ep) else None

            mean_monthly_return_by_block_pct: dict[str, float | None] = {}
            for block in STRESS_BLOCK_NAMES:
                idx = [i for i, t in enumerate(asset_cols) if ticker_to_block.get(t) == block]
                if not idx:
                    mean_monthly_return_by_block_pct[block] = None
                    continue
                w_block = np.array([w_vec[i] for i in idx], dtype=float)
                s_block = w_block.sum()
                if s_block <= 1e-15:
                    mean_monthly_return_by_block_pct[block] = None
                    continue
                w_block = w_block / s_block
                block_ret = sub.iloc[:, idx].dot(w_block)
                mean_monthly_return_by_block_pct[block] = (
                    round(float(block_ret.mean()), 4) if block_ret.notna().any() else None
                )
            episode_start_ts = pd.Timestamp(start)
            pre = returns_sub.loc[returns_sub.index < episode_start_ts]
            pre_len = min(len(pre), len(port_ret))
            if pre_len >= 2 and np.isfinite(vol_ep):
                pre_port_ret = pre.tail(pre_len).dot(w_vec)
                vol_pre = float(pre_port_ret.std(ddof=1)) if len(pre_port_ret) >= 2 else np.nan
                vol_spike = (vol_ep / vol_pre) if np.isfinite(vol_pre) and vol_pre > 0 else np.nan
            else:
                vol_spike = np.nan

            # Stress correlations between key defensive/risk blocks over the episode.
            block_series: dict[str, pd.Series] = {}
            for block in STRESS_BLOCK_NAMES:
                idx = [i for i, t in enumerate(asset_cols) if ticker_to_block.get(t) == block]
                if not idx:
                    continue
                w_block = np.array([w_vec[i] for i in idx], dtype=float)
                block_ret = sub.iloc[:, idx].dot(w_block)
                if block_ret.notna().sum() >= 2:
                    block_series[block] = block_ret
            stress_corr: dict[str, float] = {}
            if block_series:
                block_df = pd.DataFrame(block_series).dropna(how="all")
                pairs = [("Growth", "Duration"), ("Growth", "Inflation"), ("Duration", "Inflation")]
                for b1, b2 in pairs:
                    if b1 in block_df.columns and b2 in block_df.columns:
                        pair_df = block_df[[b1, b2]].dropna()
                        if len(pair_df) >= 2:
                            c = float(pair_df[b1].corr(pair_df[b2]))
                            if np.isfinite(c):
                                stress_corr[f"{b1}_{b2}"] = round(c, 4)

            historical_results.append({
                "episode": ep_id,
                "episode_start": start,
                "episode_end": end,
                "max_dd": round(max_dd, 4),
                "pnl_real_episode": round(float(pnl_real_episode), 4) if pnl_real_episode is not None else None,
                "vol_annualized_episode": vol_annualized_episode,
                "mean_monthly_return_by_block_pct": mean_monthly_return_by_block_pct,
                "volatility_spike_ratio": round(float(vol_spike), 4) if np.isfinite(vol_spike) else None,
                "stress_correlations": stress_corr,
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
                "mean_monthly_return_by_block_pct": {},
                "volatility_spike_ratio": None,
                "stress_correlations": {},
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

    has_equity_role_warn = any(
        s.get("scenario_id") == "equity_shock" and s.get("role_equity_shock_severity") == "warn"
        for s in scenario_results
    )
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
        elif primary_diagnostic_code.startswith("DIAG_ROLE_"):
            failed_test = "Role"
            failed_scenario = next(
                (x["scenario_id"] for x in scenario_results if primary_diagnostic_code in (x.get("diagnostic_codes") or [])),
                None,
            )
        elif primary_diagnostic_code.startswith("DIAG_RC_TOP1_"):
            failed_test = "RC_Top1"
            failed_scenario = next(
                (x["scenario_id"] for x in scenario_results if primary_diagnostic_code in (x.get("diagnostic_codes") or [])),
                None,
            )
        elif primary_diagnostic_code.startswith("DIAG_RC_TOP3_"):
            failed_test = "RC_Top3"
            failed_scenario = next(
                (x["scenario_id"] for x in scenario_results if primary_diagnostic_code in (x.get("diagnostic_codes") or [])),
                None,
            )

    if diagnostic_codes:
        status = "DIAG_ATTENTION"
        fail_reason_code = primary_diagnostic_code
        warning_code = _build_warning_code("ROLE_EQUITY_DEFENSIVE_WEAK") if has_equity_role_warn else None
    elif has_equity_role_warn:
        status = "DIAG_PASS_WITH_WARNING"
        fail_reason_code = None
        warning_code = _build_warning_code("ROLE_EQUITY_DEFENSIVE_WEAK")
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
        "rc_asset_cap_used": rc_cap,
        "rc_cap_mode": rc_cap_mode,
        "stress_top3_rc_sum_cap": stress_top3_rc_sum_cap_pct,
        "max_dd_limit": max_dd_limit,
    }


def _equity_defensive_sum(pnl_by_block: dict[str, float]) -> float:
    """S = PnL_Duration + PnL_Inflation + PnL_Tail (decimal fractions)."""
    return (
        float(pnl_by_block.get("Duration", 0.0))
        + float(pnl_by_block.get("Inflation", 0.0))
        + float(pnl_by_block.get("Tail", 0.0))
    )


def _equity_shock_role_severity(defensive_sum: float) -> str:
    """
    Equity shock Role grades (stress_testing_spec §6):
    - ok: S >= 0
    - warn: -0.01 <= S < 0 (suite PASS_WITH_WARNING if Loss+RC pass); includes mild band [-0.005, 0)
    - fail: S < -0.01
    """
    if defensive_sum >= 0:
        return "ok"
    if defensive_sum < EQUITY_DEFENSIVE_SUM_FAIL_BELOW:
        return "fail"
    return "warn"


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
        "rc_asset_cap_used": None,
        "stress_top3_rc_sum_cap": None,
        "max_dd_limit": None,
        "skip_reason": reason,
    }
