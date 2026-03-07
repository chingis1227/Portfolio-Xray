"""
Portfolio stress testing per docs/docs/stress_testing_spec.md.
Scenarios: Equity, Credit, Rates, Inflation/Stagflation, Liquidity.
Loss test (MaxDD), Role test, RC test (Top1/Top3), factor validation, historical validation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from src.config_schema import GROWTH_EM_DEBT_KEY, GROWTH_HY_KEY, STRESS_BLOCK_NAMES
from src.risk_contrib import percentage_contributions_variance, cov_matrix_monthly

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


def _build_fail_reason_code(failed_test: str | None, failed_scenario: str | None) -> str | None:
    """
    Build fail_reason_code: FAIL_<TEST>_<SUFFIX>.
    Examples: FAIL_LOSS_EQUITY_SHOCK, FAIL_ROLE_STAGFLATION, FAIL_RC_TOP1_LIQUIDITY_SHOCK,
    FAIL_RC_TOP3_CREDIT_SHOCK, FAIL_BETA_REAL_RATES, FAIL_HIST_2022.
    """
    if not failed_test or not failed_scenario:
        return None
    if failed_test == "Historical":
        return f"FAIL_HIST_{failed_scenario}"
    if failed_test == "Loss":
        return f"FAIL_LOSS_{_scenario_suffix(failed_scenario, for_role=False)}"
    if failed_test == "Role":
        return f"FAIL_ROLE_{_scenario_suffix(failed_scenario, for_role=True)}"
    if failed_test == "RC_Top1":
        return f"FAIL_RC_TOP1_{_scenario_suffix(failed_scenario, for_role=False)}"
    if failed_test == "RC_Top3":
        return f"FAIL_RC_TOP3_{_scenario_suffix(failed_scenario, for_role=False)}"
    if failed_test and failed_test.startswith("Beta"):
        # FAIL_BETA_<FACTOR> e.g. FAIL_BETA_REAL_RATES
        factor = failed_scenario.replace("-", "_").upper() if failed_scenario else "UNKNOWN"
        return f"FAIL_BETA_{factor}"
    return None


def _build_warning_code(warning_reason: str | None) -> str | None:
    """Build warning_code for PASS_WITH_WARNING (e.g. WARN_BETA_NO_LIMITS, WARN_HIST_BORDERLINE)."""
    if not warning_reason:
        return None
    return f"WARN_{warning_reason}"


def _ticker_to_stress_block(blocks: dict[str, list[str]], tickers: list[str] | None = None) -> dict[str, str]:
    """Map each ticker to one of Growth, Duration, Inflation, Liquidity, Tail. Growth_HY, Growth_EM_debt -> Growth. Unlisted tickers -> Growth."""
    out = {}
    for block_name in STRESS_BLOCK_NAMES:
        for t in blocks.get(block_name, []):
            out[t] = block_name
    for t in blocks.get(GROWTH_HY_KEY, []):
        out[t] = "Growth"
    for t in blocks.get(GROWTH_EM_DEBT_KEY, []):
        out[t] = "Growth"
    if tickers:
        for t in tickers:
            if t not in out:
                out[t] = "Growth"
    return out


def _resolve_rc_asset_cap(rc_asset_cap_pct: float | None, n_assets: int) -> float:
    """From feasibility_constraints_spec: if N < 4 then 0.40 else min(0.25, max(0.10, 1.5/N))."""
    if rc_asset_cap_pct is not None and rc_asset_cap_pct > 0:
        return float(rc_asset_cap_pct)
    if n_assets < 4:
        return 0.40
    return min(0.25, max(0.10, 1.5 / n_assets))


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
) -> dict[str, Any]:
    """
    Run full stress suite. Returns report dict with status, per-scenario results, factor betas, historical.
    """
    ticker_to_block = _ticker_to_stress_block(blocks, tickers)
    risk_on_tickers = (
        list(blocks.get("Growth", []))
        + list(blocks.get(GROWTH_HY_KEY, []))
        + list(blocks.get(GROWTH_EM_DEBT_KEY, []))
    )
    n_assets = len([t for t in tickers if t in weights and weights.get(t, 0) > 0])
    rc_cap = _resolve_rc_asset_cap(rc_asset_cap_pct, max(n_assets, 1))
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
    failed_scenario: str | None = None
    failed_test: str | None = None

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
        role_ok = _role_test_ok(scenario_id, pnl_by_block)
        rc1_ok = top1_rc_pct <= rc_cap
        rc3_ok = top3_rc_sum_pct <= stress_top3_rc_sum_cap_pct
        scenario_pass = loss_ok and role_ok and rc1_ok and rc3_ok

        if not loss_ok and failed_test is None:
            failed_test = "Loss"
            failed_scenario = scenario_id
        if not role_ok and failed_test is None:
            failed_test = "Role"
            failed_scenario = scenario_id
        if not rc1_ok and failed_test is None:
            failed_test = "RC_Top1"
            failed_scenario = scenario_id
        if not rc3_ok and failed_test is None:
            failed_test = "RC_Top3"
            failed_scenario = scenario_id

        if portfolio_pnl_pct < worst_loss:
            worst_loss = portfolio_pnl_pct

        scenario_results.append({
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
            "pass": scenario_pass,
        })

    # Factor validation: output only (no limits for now)
    factor_betas = {k: round(v, 4) for k, v in portfolio_betas.items()}

    # Historical validation (simplified: run portfolio through episodes, max DD)
    historical_results = []
    for ep_id, start, end in HISTORICAL_EPISODES:
        try:
            sub = returns_sub.loc[start:end] if hasattr(returns_sub.index, "slice_indexer") else returns_sub
            if sub.empty or len(sub) < 2:
                historical_results.append({"episode": ep_id, "max_dd": None, "pass": None})
                continue
            eq = (1 + sub).cumprod()
            dd = eq / eq.cummax() - 1
            port_eq = (1 + sub.dot(w_vec)).cumprod()
            port_dd = port_eq / port_eq.cummax() - 1
            max_dd = float(port_dd.min())
            historical_results.append({"episode": ep_id, "max_dd": round(max_dd, 4), "pass": max_dd >= -max_dd_limit})
        except Exception:
            historical_results.append({"episode": ep_id, "max_dd": None, "pass": None})

    hist_fail = any(h.get("pass") is False for h in historical_results)
    if hist_fail and failed_test is None:
        failed_test = "Historical"
        failed_scenario = next((h["episode"] for h in historical_results if h.get("pass") is False), None)

    all_scenario_pass = all(s["pass"] for s in scenario_results)
    if not all_scenario_pass and failed_test is None:
        failed_scenario = next((s["scenario_id"] for s in scenario_results if not s["pass"]), None)
        failed_test = "Loss"
        for s in scenario_results:
            if not s["pass"]:
                if not s["loss_ok"]:
                    failed_test = "Loss"
                elif not s["role_ok"]:
                    failed_test = "Role"
                elif not s["rc1_ok"]:
                    failed_test = "RC_Top1"
                elif not s["rc3_ok"]:
                    failed_test = "RC_Top3"
                break

    if all_scenario_pass and not hist_fail:
        status = "PASS"
        fail_reason_code = None
        warning_code = None
    elif failed_test:
        status = "FAIL_STRESS"
        fail_reason_code = _build_fail_reason_code(failed_test, failed_scenario)
        warning_code = None
    else:
        status = "PASS_WITH_WARNING"
        fail_reason_code = None
        warning_code = _build_warning_code("HIST_BORDERLINE")  # or other reason when we have multiple warning types

    return {
        "status": status,
        "fail_reason_code": fail_reason_code,
        "warning_code": warning_code,
        "worst_scenario_loss_pct": round(worst_loss, 4),
        "failed_scenario": failed_scenario,
        "failed_test": failed_test,
        "scenario_results": scenario_results,
        "factor_betas": factor_betas,
        "historical_results": historical_results,
        "rc_asset_cap_used": rc_cap,
        "stress_top3_rc_sum_cap": stress_top3_rc_sum_cap_pct,
        "max_dd_limit": max_dd_limit,
    }


def _role_test_ok(scenario_id: str, pnl_by_block: dict[str, float]) -> bool:
    """Stagflation: PnL_Inflation > 0. Equity shock: not (PnL_Duration < 0 and PnL_Inflation < 0 and PnL_Tail <= 0)."""
    if scenario_id == "inflation_stagflation":
        return pnl_by_block.get("Inflation", 0) > 0
    if scenario_id == "equity_shock":
        dur = pnl_by_block.get("Duration", 0)
        inf = pnl_by_block.get("Inflation", 0)
        tail = pnl_by_block.get("Tail", 0)
        if dur < 0 and inf < 0 and tail <= 0:
            return False
    return True


def _empty_report(reason: str) -> dict[str, Any]:
    return {
        "status": "PASS_WITH_WARNING",
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
