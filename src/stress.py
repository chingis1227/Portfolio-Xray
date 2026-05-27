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

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.data_trust_signals import build_stress_data_trust_summary
from src.current_portfolio_stress_scorecard_block import (
    attach_current_portfolio_stress_scorecard_v1,
)
from src.hedge_gap_analysis_block import attach_hedge_gap_analysis_v1
from src.stress_results_block import attach_stress_results_v1, empty_stress_results_v1
from src.metrics_asset import time_to_recovery
from src.risk_contrib import cov_matrix_monthly, percentage_contributions_variance
from src.stress_factors import get_factor_display_name
from src.stress_covariance_taxonomy import (
    LAMBDA_BLEND,
    STRESS_COV_CALIBRATION_VERSION,
    VOL_MULT_BLOCK,
    key_rho_overrides_used_for_scenario,
    stress_covariance_taxonomy_blend,
)

FACTOR_TO_SHOCK_KEY = {
    "equity": "shock_eq",
    "real_rates": "shock_rr",
    "credit": "shock_credit",
    "inflation": "shock_inf",
    "usd": "shock_usd",
    "commodity": "shock_cmd",
}
PRODUCTION_FACTOR_BETA_KEYS = (
    "beta_eq",
    "beta_rr",
    "beta_inf",
    "beta_credit",
    "beta_usd",
    "beta_cmd",
    "beta_vix",
    "beta_us_growth",
)
RECESSION_CALIBRATION_EPISODES = ("2008", "2020")

# Used only when factor history is unavailable; normal report runs pass realized factors.
RECESSION_SEVERE_FALLBACK_SHOCK = {
    "shock_eq": -0.35,
    "shock_rr": -0.010,
    "shock_credit": 0.045,
    "shock_inf": -0.003,
    "shock_usd": 0.08,
    "shock_cmd": -0.15,
}

RECESSION_SEVERE_PARAMS = {
    "vol_mult": 1.60,
    "stress_cov": True,
    "risk_on_corr": 0.95,
}

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
        "stress_cov": True,
    },
    "inflation_stagflation": {
        "shock_eq": -0.20,
        "shock_rr": 0.005,
        "shock_credit": 0.0,
        "shock_inf": 0.005,
        "shock_usd": 0.0,
        "shock_cmd": 0.25,
        "vol_mult": 1.0,
        "stress_cov": True,
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
    "usd_shock": {
        "shock_eq": -0.05,
        "shock_rr": 0.0,
        "shock_credit": 0.0,
        "shock_inf": 0.0,
        "shock_usd": 0.10,
        "shock_cmd": -0.05,
        "vol_mult": 1.10,
        "stress_cov": True,
    },
    "commodity_shock": {
        "shock_eq": -0.05,
        "shock_rr": 0.0,
        "shock_credit": 0.0,
        "shock_inf": 0.005,
        "shock_usd": -0.03,
        "shock_cmd": 0.20,
        "vol_mult": 1.15,
        "stress_cov": True,
    },
}

HISTORICAL_EPISODES = [
    ("dotcom", "2000-03-01", "2002-10-31"),
    ("2008", "2007-10-01", "2009-03-31"),
    ("2020", "2020-02-01", "2020-04-30"),
    ("2022", "2021-11-01", "2022-10-31"),
    ("banking_2023", "2023-02-01", "2023-05-31"),
]

# Primary stress historical path: realized portfolio monthly returns only (no proxy waterfall).
HISTORICAL_PRIMARY_RETURN_METHOD = "realized_portfolio_monthly"
HISTORICAL_METHODOLOGY_VERSION = "historical_methodology_v1"

# Core MVP portfolio-first stress uses diagnostic-only statuses (no client mandate loss gate).
LOSS_GATE_MODE_MANDATE = "mandate"
LOSS_GATE_MODE_DIAGNOSTIC = "diagnostic"
STRESS_SUITE_STATUSES_MANDATE = frozenset({"DIAG_PASS", "DIAG_PASS_WITH_WARNING", "DIAG_ATTENTION"})
STRESS_SUITE_STATUSES_DIAGNOSTIC = frozenset({"ok", "warning", "insufficient_data"})

_SCENARIO_SUFFIX = {
    "equity_shock": "EQUITY_SHOCK",
    "credit_shock": "CREDIT_SHOCK",
    "rates_shock": "RATES_SHOCK",
    "liquidity_shock": "LIQUIDITY_SHOCK",
    "inflation_stagflation": "INFLATION_STAGFLATION",
    "recession_severe": "RECESSION_SEVERE",
    "usd_shock": "USD_SHOCK",
    "commodity_shock": "COMMODITY_SHOCK",
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
_FACTOR_SHORT_TO_BETA = {short: beta for beta, short in _BETA_TO_FACTOR_SHORT.items()}


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


def _portfolio_model_pnl_from_shock(
    shock: dict[str, float],
    portfolio_betas: dict[str, float],
) -> float:
    pnl = 0.0
    for sk, bk in _SHOCK_TO_BETA:
        try:
            pnl += float(shock.get(sk, 0.0)) * float(portfolio_betas.get(bk, 0.0))
        except (TypeError, ValueError):
            continue
    return float(pnl)


def _stress_score_from_shock(shock: dict[str, float]) -> float:
    """Fallback severity score when portfolio betas are unavailable."""
    return (
        max(0.0, -float(shock.get("shock_eq", 0.0)))
        + 5.0 * max(0.0, float(shock.get("shock_credit", 0.0)))
        + max(0.0, float(shock.get("shock_usd", 0.0)))
        + 0.5 * max(0.0, -float(shock.get("shock_cmd", 0.0)))
    )


def _episode_factor_shocks(
    factor_returns: pd.DataFrame | None,
    episodes: list[tuple[str, str, str]],
) -> dict[str, dict[str, float]]:
    """Sum weekly factor moves over the recession calibration episodes."""
    if factor_returns is None or factor_returns.empty:
        return {}
    factors = factor_returns.copy()
    try:
        dt_index = pd.to_datetime(factors.index, errors="coerce")
        valid = pd.notna(dt_index)
        if not bool(valid.all()):
            factors = factors.loc[valid].copy()
            dt_index = dt_index[valid]
        factors.index = dt_index
        factors = factors.sort_index()
    except Exception:
        return {}
    if factors.empty:
        return {}
    out: dict[str, dict[str, float]] = {}
    for ep_id, start, end in episodes:
        if ep_id not in RECESSION_CALIBRATION_EPISODES:
            continue
        sub = factors.loc[pd.Timestamp(start):pd.Timestamp(end)] if hasattr(factors.index, "slice_indexer") else factors
        if sub.empty:
            continue
        shock: dict[str, float] = {}
        for factor_col, shock_key in FACTOR_TO_SHOCK_KEY.items():
            if factor_col not in sub.columns:
                continue
            val = sub[factor_col].dropna().sum()
            if pd.notna(val):
                shock[shock_key] = float(val)
        if shock:
            for shock_key in FACTOR_TO_SHOCK_KEY.values():
                shock.setdefault(shock_key, 0.0)
            out[ep_id] = shock
    return out


def _calibrate_recession_severe(
    factor_returns: pd.DataFrame | None,
    portfolio_betas: dict[str, float],
) -> tuple[dict[str, Any], dict[str, float]]:
    episode_shocks = _episode_factor_shocks(factor_returns, HISTORICAL_EPISODES)
    if not episode_shocks:
        selected_shock = dict(RECESSION_SEVERE_FALLBACK_SHOCK)
        return {
            "method": "fallback_static_hard_landing",
            "status": "fallback_no_factor_history",
            "source_episodes": list(RECESSION_CALIBRATION_EPISODES),
            "selected_source_episode": None,
            "episode_shocks": {},
            "selected_shock": {k: round(float(v), 4) for k, v in selected_shock.items()},
            "model_pnl_by_episode": {},
            "vol_mult": RECESSION_SEVERE_PARAMS["vol_mult"],
            "risk_on_corr": RECESSION_SEVERE_PARAMS["risk_on_corr"],
            "stress_cov_method": "taxonomy_blend_v1",
            "stress_cov_lambda": round(float(LAMBDA_BLEND.get("recession_severe", 0.62)), 4),
            "stress_cov_calibration_version": STRESS_COV_CALIBRATION_VERSION,
            "vol_mult_by_block": {k: round(float(v), 4) for k, v in VOL_MULT_BLOCK.get("recession_severe", {}).items()},
            "key_rho_overrides_used": key_rho_overrides_used_for_scenario("recession_severe"),
        }, selected_shock

    has_betas = any(k in portfolio_betas for _, k in _SHOCK_TO_BETA)
    if has_betas:
        model_pnl_by_episode = {
            ep_id: _portfolio_model_pnl_from_shock(shock, portfolio_betas)
            for ep_id, shock in episode_shocks.items()
        }
        selected_episode = min(model_pnl_by_episode, key=model_pnl_by_episode.get)
    else:
        selected_episode = max(episode_shocks, key=lambda ep_id: _stress_score_from_shock(episode_shocks[ep_id]))
        model_pnl_by_episode = {ep_id: float("nan") for ep_id in episode_shocks}

    selected_shock = dict(episode_shocks[selected_episode])
    return {
        "method": "severe_from_realized_2008_2020_factor_moves",
        "status": "calibrated",
        "source_episodes": list(RECESSION_CALIBRATION_EPISODES),
        "selected_source_episode": selected_episode,
        "episode_shocks": {
            ep_id: {k: round(float(v), 4) for k, v in shock.items()}
            for ep_id, shock in episode_shocks.items()
        },
        "selected_shock": {k: round(float(v), 4) for k, v in selected_shock.items()},
        "model_pnl_by_episode": {
            ep_id: (round(float(v), 4) if np.isfinite(v) else None)
            for ep_id, v in model_pnl_by_episode.items()
        },
        "vol_mult": RECESSION_SEVERE_PARAMS["vol_mult"],
        "risk_on_corr": RECESSION_SEVERE_PARAMS["risk_on_corr"],
        "stress_cov_method": "taxonomy_blend_v1",
        "stress_cov_lambda": round(float(LAMBDA_BLEND.get("recession_severe", 0.62)), 4),
        "stress_cov_calibration_version": STRESS_COV_CALIBRATION_VERSION,
        "vol_mult_by_block": {k: round(float(v), 4) for k, v in VOL_MULT_BLOCK.get("recession_severe", {}).items()},
        "key_rho_overrides_used": key_rho_overrides_used_for_scenario("recession_severe"),
    }, selected_shock


def _attach_recession_validation(
    calibration: dict[str, Any],
    portfolio_betas: dict[str, float],
    historical_results: list[dict[str, Any]],
) -> dict[str, Any]:
    episode_shocks = calibration.get("episode_shocks") or {}
    realized_by_episode = {
        str(h.get("episode")): h.get("pnl_real_episode")
        for h in historical_results
        if h.get("episode") in RECESSION_CALIBRATION_EPISODES
    }
    rows: list[dict[str, Any]] = []
    for ep_id in RECESSION_CALIBRATION_EPISODES:
        shock = episode_shocks.get(ep_id)
        if not isinstance(shock, dict):
            continue
        model_pnl = _portfolio_model_pnl_from_shock({k: float(v) for k, v in shock.items()}, portfolio_betas)
        realized = realized_by_episode.get(ep_id)
        try:
            realized_float = float(realized) if realized is not None else None
        except (TypeError, ValueError):
            realized_float = None
        rows.append({
            "episode": ep_id,
            "model_pnl_pct": round(float(model_pnl), 4),
            "realized_pnl_pct": round(realized_float, 4) if realized_float is not None else None,
            "abs_error": round(abs(float(model_pnl) - realized_float), 4) if realized_float is not None else None,
        })
    out = dict(calibration)
    out["model_vs_realized"] = rows
    return out


PREPARED_SYNTHETIC_STRESS_SCHEMA = "prepared_synthetic_stress_v1"


@dataclass(frozen=True)
class PreparedSyntheticStressInputs:
    """
    Factory-invariant synthetic stress legs: per-scenario asset returns and stressed covariances.

    ``recession_severe`` is excluded (portfolio-beta calibration remains per candidate).
    """

    r_asset_by_scenario: dict[str, pd.Series]
    cov_stress_by_scenario: dict[str, pd.DataFrame]
    cov_meta_by_scenario: dict[str, dict[str, Any]]
    fallback_assets: tuple[str, ...]
    beta_coverage_ratio: float
    covered_assets: tuple[str, ...]
    universe_asset_cols: tuple[str, ...]
    stress_cov_method: str = "taxonomy_blend_v1"
    schema_version: str = PREPARED_SYNTHETIC_STRESS_SCHEMA


def prepared_synthetic_stress_usable(
    prepared: PreparedSyntheticStressInputs | None,
    *,
    asset_cols: list[str],
    stress_cov_method: str = "taxonomy_blend_v1",
) -> bool:
    """True when precomputed synthetic legs cover this candidate's assets and cov method."""
    if prepared is None or not prepared.r_asset_by_scenario:
        return False
    if str(stress_cov_method) != str(prepared.stress_cov_method):
        return False
    col_set = set(prepared.universe_asset_cols)
    return bool(col_set) and set(asset_cols).issubset(col_set)


def build_prepared_synthetic_stress_inputs(
    *,
    asset_cols: list[str],
    asset_betas: pd.DataFrame,
    cov_base: pd.DataFrame,
    cash_proxy_ticker: str | None = None,
    stress_cov_method: str = "taxonomy_blend_v1",
) -> PreparedSyntheticStressInputs | None:
    """
    Precompute static SCENARIOS ``r_asset`` vectors and stressed covariances for one factory run.
    """
    if not asset_cols or cov_base is None or cov_base.empty or asset_betas is None or asset_betas.empty:
        return None
    try:
        cov_aligned = cov_base.loc[asset_cols, asset_cols]
    except (KeyError, ValueError):
        return None
    if cov_aligned.empty or len(cov_aligned) < 2:
        return None

    cash_u = (cash_proxy_ticker or "").strip().upper()
    risk_on = [t for t in asset_cols if str(t).strip().upper() != cash_u]
    fallback_assets, beta_coverage_ratio = _beta_coverage_meta(asset_betas, asset_cols)
    covered_assets = tuple(t for t in asset_cols if t not in set(fallback_assets))

    r_asset_by_scenario: dict[str, pd.Series] = {}
    cov_stress_by_scenario: dict[str, pd.DataFrame] = {}
    cov_meta_by_scenario: dict[str, dict[str, Any]] = {}

    for scenario_id, params in SCENARIOS.items():
        shock = {
            k: v
            for k, v in params.items()
            if k.startswith("shock_") and isinstance(v, (int, float))
        }
        r_asset = _scenario_return_per_asset(shock, asset_betas, asset_cols)
        r_asset_by_scenario[scenario_id] = r_asset.reindex(asset_cols).fillna(0)

        use_stress_cov = bool(params.get("stress_cov", False))
        if not use_stress_cov:
            continue
        vol_mult = float(params.get("vol_mult", 1.0))
        risk_on_corr = float(params.get("risk_on_corr", 0.90))
        if stress_cov_method == "uniform_legacy":
            cov_s = _stress_covariance(cov_aligned, risk_on, vol_mult, risk_on_corr=risk_on_corr)
            cov_meta = {
                "stress_cov_method": "uniform_legacy",
                "stress_cov_lambda": None,
                "stress_cov_calibration_version": None,
                "taxonomy_coverage": {},
                "vol_mult_by_block": None,
                "key_rho_overrides_used": None,
            }
        else:
            cov_s, cov_diag = stress_covariance_taxonomy_blend(
                cov_aligned,
                asset_cols,
                scenario_id,
                cash_proxy_ticker=cash_proxy_ticker,
            )
            cov_meta = {
                "stress_cov_method": cov_diag.get("stress_cov_method", "taxonomy_blend_v1"),
                "stress_cov_lambda": cov_diag.get("stress_cov_lambda"),
                "stress_cov_calibration_version": cov_diag.get("stress_cov_calibration_version"),
                "taxonomy_coverage": cov_diag.get("taxonomy_coverage") or {},
                "vol_mult_by_block": cov_diag.get("vol_mult_by_block"),
                "key_rho_overrides_used": cov_diag.get("key_rho_overrides_used"),
            }
        cov_stress_by_scenario[scenario_id] = cov_s
        cov_meta_by_scenario[scenario_id] = cov_meta

    if not r_asset_by_scenario:
        return None

    return PreparedSyntheticStressInputs(
        r_asset_by_scenario=r_asset_by_scenario,
        cov_stress_by_scenario=cov_stress_by_scenario,
        cov_meta_by_scenario=cov_meta_by_scenario,
        fallback_assets=tuple(fallback_assets),
        beta_coverage_ratio=beta_coverage_ratio,
        covered_assets=covered_assets,
        universe_asset_cols=tuple(asset_cols),
        stress_cov_method=stress_cov_method,
    )


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


def _beta_coverage_meta(
    betas: pd.DataFrame,
    tickers: list[str],
) -> tuple[list[str], float]:
    """Return fallback tickers and coverage ratio for scenario simulation."""
    if betas is None or betas.empty:
        return list(tickers), 0.0
    fallback = [t for t in tickers if t not in betas.index]
    covered = max(0, len(tickers) - len(fallback))
    ratio = float(covered / len(tickers)) if tickers else 0.0
    return fallback, ratio


def _synthetic_assumptions_block(
    *,
    fallback_assets: list[str],
    beta_coverage_ratio: float,
    beta_data_source: str | None = None,
    covered_assets: list[str] | None = None,
    missing_assets: list[str] | None = None,
    fallback_reason: str | None = None,
) -> dict[str, Any]:
    ratio = float(beta_coverage_ratio)
    if ratio >= 0.95:
        confidence = "high"
    elif ratio >= 0.75:
        confidence = "medium"
    else:
        confidence = "low"
    fallback_used = bool(fallback_assets)
    return {
        "version": "synthetic_assumptions_v1",
        "beta_source": beta_data_source or "asset_factor_betas_weekly",
        "beta_data_source": beta_data_source or "asset_factor_betas_weekly",
        "beta_coverage_ratio": round(ratio, 4),
        "beta_confidence": confidence,
        "fallback_used": fallback_used,
        "fallback_reason": fallback_reason if fallback_used else None,
        "covered_assets": list(covered_assets or []),
        "missing_assets": list(missing_assets or fallback_assets),
        "fallback_asset_count": len(fallback_assets),
        "beta_fallback_assets": list(fallback_assets),
        "proxy_method_for_missing_betas": "equity_shock_proxy" if fallback_used else "none_required",
        "proxy_applied_to_assets": list(fallback_assets),
    }


def _historical_data_quality(n_obs: int, n_expected: int) -> tuple[float | None, str]:
    if n_expected <= 0:
        return None, "insufficient_data"
    coverage = float(n_obs / n_expected)
    if n_obs < 2:
        return coverage, "insufficient_data"
    if coverage < 0.50:
        return coverage, "low_confidence"
    if coverage < 0.75:
        return coverage, "usable_with_gaps"
    return coverage, "reliable"


def _historical_methodology_block() -> dict[str, Any]:
    """Report-level disclosure: primary stress is realized-only; proxies live in normalized library."""
    return {
        "version": HISTORICAL_METHODOLOGY_VERSION,
        "primary_stress_path": "realized_only",
        "return_method": HISTORICAL_PRIMARY_RETURN_METHOD,
        "proxy_used_in_primary_stress": False,
        "proxy_location": "scenario_library_normalized",
        "proxy_module": "historical_stress_fallback",
        "proxy_disclosure": (
            "Primary historical episodes in run_stress use aligned portfolio monthly returns only. "
            "Per-asset proxy waterfall (direct, ticker proxy, asset-class, factor replay) applies "
            "only when building scenario_library_normalized historical rows."
        ),
    }


def _historical_row_disclosure_fields() -> dict[str, Any]:
    return {
        "return_method": HISTORICAL_PRIMARY_RETURN_METHOD,
        "proxy_used": False,
    }


CRISIS_REPLAY_VERSION = "crisis_replay_v2"


def _episode_recovery_fields(port_ret: pd.Series) -> dict[str, Any]:
    """Max-drawdown recovery on episode portfolio monthly returns (metrics_spec §6.9)."""
    ttr, recovered = time_to_recovery(port_ret)
    return {
        "time_to_recovery_months": round(float(ttr), 3) if ttr is not None else None,
        "recovered": bool(recovered),
    }


def _episode_asset_pnl_contrib(
    sub: pd.DataFrame,
    asset_cols: list[str],
    w_vec: np.ndarray,
) -> dict[str, float]:
    """Additive static-weight monthly attribution; sums to sum(portfolio monthly returns)."""
    out: dict[str, float] = {}
    for i, ticker in enumerate(asset_cols):
        contrib = float((sub[ticker] * w_vec[i]).sum())
        out[str(ticker)] = round(contrib, 4)
    return out


def _top_loss_assets_from_contrib(asset_pnl_contrib: dict[str, float], n: int = 3) -> list[str]:
    if not asset_pnl_contrib:
        return []
    ranked = sorted(asset_pnl_contrib.items(), key=lambda kv: kv[1])
    return [t for t, _ in ranked[:n]]


def crisis_replay_summary_from_paths(
    historical_episode_paths: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Compact crisis replay for snapshot/comparison consumers (no daily ``rows``)."""
    summary: list[dict[str, Any]] = []
    for block in historical_episode_paths or []:
        if not isinstance(block, dict):
            continue
        summary.append(
            {
                "replay_version": block.get("replay_version"),
                "episode": block.get("episode"),
                "episode_start": block.get("episode_start"),
                "episode_end": block.get("episode_end"),
                "n_obs": block.get("n_obs"),
                "coverage_ratio": block.get("coverage_ratio"),
                "data_quality": block.get("data_quality"),
                "time_to_recovery_months": block.get("time_to_recovery_months"),
                "recovered": block.get("recovered"),
                "top_loss_assets_episode": list(block.get("top_loss_assets_episode") or []),
            }
        )
    return summary


def _build_historical_data_quality_warnings(historical_results: list[dict[str, Any]]) -> list[str]:
    """Methodology boundary plus per-episode quality flags for stress_conclusions."""
    warnings = [
        (
            "primary_historical_stress: realized_portfolio_monthly (no proxy in run_stress); "
            "per-asset proxy waterfall only in scenario_library_normalized "
            "(see scenario_library_spec Historical Stress Fallback)"
        ),
    ]
    for row in historical_results:
        quality = row.get("data_quality")
        if quality not in {"reliable", "usable_with_gaps"}:
            ep = row.get("episode", "unknown")
            method = row.get("return_method", HISTORICAL_PRIMARY_RETURN_METHOD)
            warnings.append(f"{ep}: {quality} (return_method={method})")
    return warnings


def _loss_severity_absolute(pnl_pct: float | None) -> str:
    """Magnitude-only severity for Core MVP (no client mandate threshold)."""
    if pnl_pct is None or not isinstance(pnl_pct, (int, float)):
        return "unknown"
    p = float(pnl_pct)
    if p <= -0.25:
        return "high"
    if p <= -0.10:
        return "moderate"
    return "low"


def _normalize_loss_gate_mode(loss_gate_mode: str | None) -> str:
    mode = str(loss_gate_mode or LOSS_GATE_MODE_MANDATE).strip().lower()
    if mode not in {LOSS_GATE_MODE_MANDATE, LOSS_GATE_MODE_DIAGNOSTIC}:
        return LOSS_GATE_MODE_MANDATE
    return mode


def _resolve_diagnostic_suite_status(
    historical_results: list[dict[str, Any]],
    *,
    hist_inconclusive: bool,
) -> tuple[str, str | None]:
    """Portfolio-first stress bundle status from data quality only."""
    bad_qualities = {"insufficient_data", "low_confidence"}
    n_bad = sum(1 for h in historical_results if str(h.get("data_quality") or "") in bad_qualities)
    n_hist = len(historical_results)
    if n_hist and n_bad >= max(1, (n_hist + 1) // 2):
        return "insufficient_data", _build_warning_code("DATA_INSUFFICIENT")
    if hist_inconclusive:
        return "warning", _build_warning_code("HIST_BORDERLINE")
    if n_bad > 0:
        return "warning", _build_warning_code("DATA_INSUFFICIENT")
    return "ok", None


def _loss_severity_vs_limit(pnl_pct: float | None, max_dd_limit: float, *, loss_ok: bool | None = None) -> str:
    """Diagnostic loss severity relative to mandate MaxDD (does not change pass/fail)."""
    if pnl_pct is None:
        return "unknown"
    if loss_ok is False or float(pnl_pct) < -float(max_dd_limit):
        return "high"
    if float(pnl_pct) <= -0.5 * float(max_dd_limit):
        return "moderate"
    return "low"


def _beta_coverage_confidence(ratio: float | None) -> str:
    if ratio is None:
        return "low"
    if float(ratio) >= 0.95:
        return "high"
    if float(ratio) >= 0.75:
        return "medium"
    return "low"


def _aggregate_stress_confidence(
    synthetic_rows: list[dict[str, Any]],
    historical_rows: list[dict[str, Any]],
) -> str:
    levels = {"low": 0, "medium": 1, "high": 2, "unknown": 0, "moderate": 1}
    worst = 2
    for row in synthetic_rows:
        for key in ("beta_confidence",):
            worst = min(worst, levels.get(str(row.get(key) or "high"), 2))
    for row in historical_rows:
        q = str(row.get("data_quality") or "")
        if q in {"insufficient_data", "low_confidence"}:
            worst = min(worst, 0)
        elif q == "usable_with_gaps":
            worst = min(worst, 1)
    inv = {0: "low", 1: "medium", 2: "high"}
    return inv.get(worst, "medium")


def _scorecard_synthetic_row(
    row: dict[str, Any],
    max_dd_limit: float | None,
    *,
    loss_gate_mode: str = LOSS_GATE_MODE_MANDATE,
) -> dict[str, Any]:
    pnl = row.get("portfolio_pnl_pct")
    loss_ok = row.get("loss_ok")
    beta_cov = row.get("beta_coverage_ratio")
    pnl_f = float(pnl) if isinstance(pnl, (int, float)) else None
    if loss_gate_mode == LOSS_GATE_MODE_DIAGNOSTIC:
        severity = _loss_severity_absolute(pnl_f)
    else:
        severity = _loss_severity_vs_limit(
            pnl_f,
            float(max_dd_limit or 0.25),
            loss_ok=loss_ok if isinstance(loss_ok, bool) else None,
        )
    return {
        "scenario_id": row.get("scenario_id"),
        "portfolio_pnl_pct": pnl,
        "pass": row.get("pass"),
        "loss_ok": loss_ok,
        "loss_severity": severity,
        "beta_coverage_ratio": beta_cov,
        "beta_confidence": _beta_coverage_confidence(
            float(beta_cov) if isinstance(beta_cov, (int, float)) else None
        ),
        "top3_loss_assets": row.get("top3_loss_assets") or [],
        "top1_rc_asset": row.get("top1_rc_asset"),
        "top1_rc_pct": row.get("top1_rc_pct"),
        "top3_rc_assets": row.get("top3_rc_assets") or [],
        "top3_rc_sum_pct": row.get("top3_rc_sum_pct"),
        "diagnostic_codes": list(row.get("diagnostic_codes") or []),
    }


def _scorecard_historical_row(
    row: dict[str, Any],
    max_dd_limit: float | None,
    *,
    loss_gate_mode: str = LOSS_GATE_MODE_MANDATE,
) -> dict[str, Any]:
    max_dd = row.get("max_dd")
    pnl = row.get("pnl_real_episode")
    passed = row.get("pass")
    severity = "unknown"
    if loss_gate_mode == LOSS_GATE_MODE_DIAGNOSTIC:
        if isinstance(max_dd, (int, float)):
            severity = _loss_severity_absolute(float(max_dd))
        elif isinstance(pnl, (int, float)):
            severity = _loss_severity_absolute(float(pnl))
    elif isinstance(max_dd, (int, float)):
        severity = _loss_severity_vs_limit(
            float(max_dd),
            float(max_dd_limit or 0.25),
            loss_ok=passed if isinstance(passed, bool) else None,
        )
    elif isinstance(pnl, (int, float)):
        severity = _loss_severity_vs_limit(float(pnl), float(max_dd_limit or 0.25))
    return {
        "episode": row.get("episode"),
        "pnl_real_episode": pnl,
        "max_dd": max_dd,
        "pass": passed,
        "loss_severity": severity,
        "data_quality": row.get("data_quality"),
        "coverage_ratio": row.get("coverage_ratio"),
        "n_obs": row.get("n_obs"),
        "diagnostic_code": row.get("diagnostic_code"),
        "return_method": row.get("return_method"),
        "proxy_used": row.get("proxy_used"),
    }


def _build_stress_scorecard_v1(
    *,
    status: str,
    primary_diagnostic_code: str | None,
    warning_code: str | None,
    max_dd_limit: float | None,
    scenario_results: list[dict[str, Any]],
    historical_results: list[dict[str, Any]],
    loss_gate_mode: str = LOSS_GATE_MODE_MANDATE,
) -> dict[str, Any]:
    synthetic = [
        _scorecard_synthetic_row(row, max_dd_limit, loss_gate_mode=loss_gate_mode)
        for row in scenario_results
    ]
    historical = [
        _scorecard_historical_row(row, max_dd_limit, loss_gate_mode=loss_gate_mode)
        for row in historical_results
    ]
    return {
        "version": "stress_scorecard_v1",
        "overall_status": status,
        "overall_reason": primary_diagnostic_code or warning_code,
        "overall_confidence": _aggregate_stress_confidence(synthetic, historical),
        "max_dd_limit": max_dd_limit,
        "n_synthetic_scenarios": len(synthetic),
        "n_historical_episodes": len(historical),
        "synthetic_scenarios": synthetic,
        "historical_episodes": historical,
    }


def _select_worst_historical_row(historical_results: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Episode with minimum max_dd (most severe drawdown), matching historical pass/fail."""
    hist_with_dd = [h for h in historical_results if h.get("max_dd") is not None]
    if not hist_with_dd:
        return None
    return min(hist_with_dd, key=lambda x: float(x.get("max_dd", 0.0)))


def _synthetic_factor_driver_row(factor_short: str, pnl_pct: float) -> dict[str, Any]:
    beta_key = _FACTOR_SHORT_TO_BETA.get(factor_short)
    return {
        "factor_short": factor_short,
        "beta_key": beta_key,
        "factor": get_factor_display_name(beta_key) if beta_key else factor_short,
        "pnl_pct": round(float(pnl_pct), 4),
        "abs_pnl_pct": round(abs(float(pnl_pct)), 4),
        "direction": "loss" if pnl_pct < 0 else "gain" if pnl_pct > 0 else "flat",
    }


def _worst_scenario_factor_drivers(
    worst_scenario_row: dict[str, Any] | None,
    *,
    limit: int = 3,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Top loss and helping factor channels from worst synthetic row pnl_by_factor_pct."""
    if not isinstance(worst_scenario_row, dict):
        return [], []
    pnl_by_factor = worst_scenario_row.get("pnl_by_factor_pct")
    if not isinstance(pnl_by_factor, dict) or not pnl_by_factor:
        return [], []

    negatives: list[dict[str, Any]] = []
    positives: list[dict[str, Any]] = []
    for factor_short, raw_pnl in pnl_by_factor.items():
        if not isinstance(raw_pnl, (int, float)):
            continue
        pnl = float(raw_pnl)
        row = _synthetic_factor_driver_row(str(factor_short), pnl)
        if pnl < 0:
            negatives.append(row)
        elif pnl > 0:
            positives.append(row)

    negatives.sort(key=lambda row: (float(row["pnl_pct"]), str(row["factor_short"])))
    positives.sort(key=lambda row: (-float(row["pnl_pct"]), str(row["factor_short"])))

    top_loss = negatives[:limit]
    helped = positives[:limit]
    for idx, row in enumerate(top_loss, start=1):
        row["rank"] = idx
    for idx, row in enumerate(helped, start=1):
        row["rank"] = idx
    return top_loss, helped


def _build_stress_conclusions(
    *,
    worst_scenario_row: dict[str, Any] | None,
    worst_historical_row: dict[str, Any] | None,
    helped_assets: list[dict[str, Any]],
    historical_results: list[dict[str, Any]],
    max_dd_limit: float | None,
    hedge_gap_analysis: dict[str, Any],
    overall_confidence: str,
    loss_gate_mode: str = LOSS_GATE_MODE_MANDATE,
) -> dict[str, Any]:
    ws_pnl = worst_scenario_row.get("portfolio_pnl_pct") if isinstance(worst_scenario_row, dict) else None
    ws_loss_ok = worst_scenario_row.get("loss_ok") if isinstance(worst_scenario_row, dict) else None
    wh_max_dd = worst_historical_row.get("max_dd") if isinstance(worst_historical_row, dict) else None
    top_factor_drivers, helped_factors = _worst_scenario_factor_drivers(worst_scenario_row)
    ws_pnl_f = float(ws_pnl) if isinstance(ws_pnl, (int, float)) else None
    if loss_gate_mode == LOSS_GATE_MODE_DIAGNOSTIC:
        ws_severity = _loss_severity_absolute(ws_pnl_f)
        wh_severity = (
            _loss_severity_absolute(float(wh_max_dd))
            if isinstance(wh_max_dd, (int, float))
            else "unknown"
        )
    else:
        ws_severity = _loss_severity_vs_limit(
            ws_pnl_f,
            float(max_dd_limit or 0.25),
            loss_ok=ws_loss_ok if isinstance(ws_loss_ok, bool) else None,
        )
        wh_severity = (
            _loss_severity_vs_limit(
                float(wh_max_dd),
                float(max_dd_limit or 0.25),
                loss_ok=worst_historical_row.get("pass")
                if isinstance(worst_historical_row, dict) and isinstance(worst_historical_row.get("pass"), bool)
                else None,
            )
            if isinstance(wh_max_dd, (int, float))
            else "unknown"
        )
    return {
        "version": "stress_conclusions_v1",
        "overall_confidence": overall_confidence,
        "worst_synthetic_scenario": {
            "scenario_id": worst_scenario_row.get("scenario_id") if isinstance(worst_scenario_row, dict) else None,
            "portfolio_pnl_pct": ws_pnl,
            "loss_severity": ws_severity,
            "pass": worst_scenario_row.get("pass") if isinstance(worst_scenario_row, dict) else None,
        },
        "worst_historical_episode": {
            "episode": worst_historical_row.get("episode") if isinstance(worst_historical_row, dict) else None,
            "pnl_real_episode": worst_historical_row.get("pnl_real_episode") if isinstance(worst_historical_row, dict) else None,
            "max_dd": wh_max_dd,
            "loss_severity": wh_severity,
            "data_quality": worst_historical_row.get("data_quality") if isinstance(worst_historical_row, dict) else None,
        },
        "top_loss_assets_worst_scenario": (worst_scenario_row or {}).get("top3_loss_assets")
        if isinstance(worst_scenario_row, dict)
        else [],
        "helped_assets_worst_scenario": helped_assets,
        "top_factor_drivers_worst_scenario": top_factor_drivers,
        "helped_factors_worst_scenario": helped_factors,
        "data_quality_warnings": _build_historical_data_quality_warnings(historical_results),
        "hedge_gap_status": hedge_gap_analysis.get("status"),
    }


# Universe taxonomy roles that qualify a holding as hedge-labeled (see hedge_gap_analysis_spec.md).
HEDGE_LABEL_RISK_ROLES: tuple[str, ...] = (
    "crisis_hedge",
    "defensive",
    "inflation_hedge",
    "tail_hedge",
)

# scenario_id -> weakness risk type; keep aligned with portfolio_xray.WEAKNESS_SCENARIO_MAP.
HEDGE_GAP_SCENARIO_BY_RISK: dict[str, str] = {
    "recession_severe": "recession",
    "inflation_stagflation": "inflation",
    "rates_shock": "rates",
    "credit_shock": "credit",
    "liquidity_shock": "liquidity",
    "equity_shock": "equity_crash",
    "usd_shock": "usd",
    "commodity_shock": "commodity_shock",
}

HEDGE_GAP_RISK_TYPE_ORDER: tuple[str, ...] = (
    "recession",
    "inflation",
    "rates",
    "credit",
    "liquidity",
    "usd",
    "equity_crash",
    "commodity_shock",
)


def _hedge_gap_scenarios_by_risk() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for scenario_id, risk_type in HEDGE_GAP_SCENARIO_BY_RISK.items():
        out.setdefault(risk_type, []).append(scenario_id)
    for risk_type in out:
        out[risk_type] = sorted(out[risk_type])
    return out


HEDGE_GAP_SCENARIOS_BY_RISK = _hedge_gap_scenarios_by_risk()

HEDGE_GAP_STATUS_REASON_EN: dict[str, str] = {
    "no_hedge_labels": (
        "No portfolio holdings carry hedge risk_role labels "
        f"({', '.join(HEDGE_LABEL_RISK_ROLES)}) in ETF/stock taxonomy."
    ),
    "no_synthetic_scenarios": "No synthetic stress scenarios available to evaluate hedge behavior.",
    "portfolio_pnl_unavailable": "Worst synthetic scenario portfolio PnL is unavailable.",
    "scenario_not_available": (
        "No mapped synthetic scenario for this risk type is present in scenario_results."
    ),
    "gap_evidence": (
        "At least one hedge-labeled holding had non-positive PnL while the portfolio lost "
        "in the mapped stress scenario for this risk type."
    ),
    "no_gap_evidence": (
        "Hedge-labeled holdings were not flagged as failing to offset loss in the mapped "
        "stress scenario for this risk type."
    ),
    "no_gap_evidence_global": (
        "Hedge-labeled holdings were not flagged as failing to offset loss in the worst synthetic scenario."
    ),
}


def _hedge_gap_status_reason_en(reason: str) -> str:
    return HEDGE_GAP_STATUS_REASON_EN.get(reason, reason)


def _hedge_gap_analysis_shell(
    *,
    method: str,
    considered: list[str],
    status: str,
    status_reason: str,
    worst_scenario_row: dict[str, Any] | None = None,
    hedge_negative: list[dict[str, Any]] | None = None,
    gap_detected: bool = False,
    by_risk_type: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    portfolio_pnl_out = None
    worst_id = None
    if isinstance(worst_scenario_row, dict):
        worst_id = worst_scenario_row.get("scenario_id")
        portfolio_pnl_raw = worst_scenario_row.get("portfolio_pnl_pct")
        if isinstance(portfolio_pnl_raw, (int, float)):
            portfolio_pnl_out = round(float(portfolio_pnl_raw), 4)
    rows = by_risk_type or []
    return {
        "method": method,
        "scenario_mapping": "HEDGE_GAP_SCENARIO_BY_RISK",
        "hedge_label_risk_roles": list(HEDGE_LABEL_RISK_ROLES),
        "hedge_assets_considered": considered,
        "n_hedge_assets_considered": len(considered),
        "worst_scenario_id": worst_id,
        "worst_scenario_portfolio_pnl_pct": portfolio_pnl_out,
        "hedge_assets_negative_in_worst_scenario": hedge_negative or [],
        "gap_detected": gap_detected,
        "status": status,
        "status_reason": status_reason,
        "status_reason_en": _hedge_gap_status_reason_en(status_reason),
        "by_risk_type": rows,
        "n_risk_types_evaluated": len(rows),
        "any_risk_type_gap_detected": any(bool(r.get("gap_detected")) for r in rows),
    }


def _hedge_assets_negative_in_scenario(
    scenario_row: dict[str, Any],
    hedge_assets: list[str],
) -> list[dict[str, Any]]:
    portfolio_pnl_raw = scenario_row.get("portfolio_pnl_pct")
    portfolio_pnl = float(portfolio_pnl_raw) if isinstance(portfolio_pnl_raw, (int, float)) else None
    if portfolio_pnl is None or portfolio_pnl >= 0:
        return []
    hedge_assets_u = {str(t).upper() for t in hedge_assets}
    hedge_negative: list[dict[str, Any]] = []
    by_asset = scenario_row.get("pnl_by_asset_pct") or {}
    if not isinstance(by_asset, dict):
        return []
    for t, v in by_asset.items():
        if str(t).upper() not in hedge_assets_u or not isinstance(v, (int, float)):
            continue
        asset_pnl = float(v)
        if asset_pnl <= 0:
            hedge_negative.append({"ticker": str(t), "pnl_pct": round(asset_pnl, 4)})
    return hedge_negative


def _worst_mapped_scenario_row(
    scenario_results: list[dict[str, Any]],
    mapped_ids: set[str],
) -> dict[str, Any] | None:
    candidates = [
        r
        for r in scenario_results
        if str(r.get("scenario_id") or "") in mapped_ids
    ]
    if not candidates:
        return None
    with_pnl = [r for r in candidates if isinstance(r.get("portfolio_pnl_pct"), (int, float))]
    if with_pnl:
        return min(with_pnl, key=lambda x: float(x["portfolio_pnl_pct"]))
    return candidates[0]


def _hedge_gap_row_for_scenario(
    *,
    risk_type: str,
    mapped_scenario_ids: list[str],
    scenario_row: dict[str, Any] | None,
    hedge_assets: list[str],
) -> dict[str, Any]:
    base: dict[str, Any] = {
        "risk_type": risk_type,
        "mapped_scenario_ids": mapped_scenario_ids,
        "scenario_mapping": "HEDGE_GAP_SCENARIO_BY_RISK",
        "evaluation_scenario_id": None,
        "evaluation_scenario_portfolio_pnl_pct": None,
        "hedge_assets_negative": [],
        "gap_detected": False,
        "status": "insufficient_data",
        "status_reason": "scenario_not_available",
        "status_reason_en": _hedge_gap_status_reason_en("scenario_not_available"),
    }
    if not isinstance(scenario_row, dict):
        return base

    scenario_id = scenario_row.get("scenario_id")
    portfolio_pnl_raw = scenario_row.get("portfolio_pnl_pct")
    portfolio_pnl = float(portfolio_pnl_raw) if isinstance(portfolio_pnl_raw, (int, float)) else None
    base["evaluation_scenario_id"] = scenario_id
    if portfolio_pnl is not None:
        base["evaluation_scenario_portfolio_pnl_pct"] = round(portfolio_pnl, 4)

    if portfolio_pnl is None:
        base["status_reason"] = "portfolio_pnl_unavailable"
        base["status_reason_en"] = _hedge_gap_status_reason_en("portfolio_pnl_unavailable")
        return base

    hedge_negative = _hedge_assets_negative_in_scenario(scenario_row, hedge_assets)
    base["hedge_assets_negative"] = hedge_negative
    if portfolio_pnl >= 0:
        base["status"] = "no_gap_detected"
        base["status_reason"] = "no_gap_evidence"
        base["status_reason_en"] = _hedge_gap_status_reason_en("no_gap_evidence")
        return base
    if hedge_negative:
        base["status"] = "gap_detected"
        base["status_reason"] = "gap_evidence"
        base["status_reason_en"] = _hedge_gap_status_reason_en("gap_evidence")
        base["gap_detected"] = True
        return base
    base["status"] = "no_gap_detected"
    base["status_reason"] = "no_gap_evidence"
    base["status_reason_en"] = _hedge_gap_status_reason_en("no_gap_evidence")
    return base


def _build_hedge_gap_by_risk_type(
    *,
    scenario_results: list[dict[str, Any]],
    hedge_assets: list[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for risk_type in HEDGE_GAP_RISK_TYPE_ORDER:
        mapped = HEDGE_GAP_SCENARIOS_BY_RISK.get(risk_type) or []
        if not mapped:
            continue
        scenario_row = _worst_mapped_scenario_row(scenario_results, set(mapped))
        rows.append(
            _hedge_gap_row_for_scenario(
                risk_type=risk_type,
                mapped_scenario_ids=mapped,
                scenario_row=scenario_row,
                hedge_assets=hedge_assets,
            )
        )
    return rows


def _build_hedge_gap_analysis(
    *,
    worst_scenario_row: dict[str, Any] | None,
    hedge_assets: list[str] | None,
    scenario_results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Stress-evidence hedge gap block (diagnostic only; see hedge_gap_analysis_spec.md).
    v1 aggregate: worst synthetic scenario globally. v2 by_risk_type: per weakness risk type,
    evaluate hedge assets in the worst mapped scenario for that type.
    """
    method = "stress_scenario_hedge_evidence_v2"
    considered = [str(t) for t in (hedge_assets or [])]
    n_hedge = len(considered)
    syn_rows = [r for r in (scenario_results or []) if isinstance(r, dict)]
    by_risk_type: list[dict[str, Any]] = []
    if n_hedge > 0 and syn_rows:
        by_risk_type = _build_hedge_gap_by_risk_type(scenario_results=syn_rows, hedge_assets=considered)

    if n_hedge == 0:
        return _hedge_gap_analysis_shell(
            method=method,
            considered=considered,
            status="not_applicable",
            status_reason="no_hedge_labels",
            by_risk_type=[],
        )

    if not isinstance(worst_scenario_row, dict):
        return _hedge_gap_analysis_shell(
            method=method,
            considered=considered,
            status="insufficient_data",
            status_reason="no_synthetic_scenarios",
            by_risk_type=by_risk_type,
        )

    portfolio_pnl_raw = worst_scenario_row.get("portfolio_pnl_pct")
    portfolio_pnl = float(portfolio_pnl_raw) if isinstance(portfolio_pnl_raw, (int, float)) else None
    hedge_negative = _hedge_assets_negative_in_scenario(worst_scenario_row, considered)

    if portfolio_pnl is None:
        return _hedge_gap_analysis_shell(
            method=method,
            considered=considered,
            status="insufficient_data",
            status_reason="portfolio_pnl_unavailable",
            worst_scenario_row=worst_scenario_row,
            by_risk_type=by_risk_type,
        )
    if portfolio_pnl >= 0:
        return _hedge_gap_analysis_shell(
            method=method,
            considered=considered,
            status="no_gap_detected",
            status_reason="no_gap_evidence_global",
            worst_scenario_row=worst_scenario_row,
            by_risk_type=by_risk_type,
        )
    if hedge_negative:
        return _hedge_gap_analysis_shell(
            method=method,
            considered=considered,
            status="gap_detected",
            status_reason="gap_evidence",
            worst_scenario_row=worst_scenario_row,
            hedge_negative=hedge_negative,
            gap_detected=True,
            by_risk_type=by_risk_type,
        )
    return _hedge_gap_analysis_shell(
        method=method,
        considered=considered,
        status="no_gap_detected",
        status_reason="no_gap_evidence_global",
        worst_scenario_row=worst_scenario_row,
        by_risk_type=by_risk_type,
    )


def _stress_covariance(
    cov_base: pd.DataFrame,
    risk_on_tickers: list[str],
    vol_mult: float,
    risk_on_corr: float = 0.90,
) -> pd.DataFrame:
    """Within risk-on: override correlation and vol multiplier. Other pairs keep base correlation."""
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
                corr[i, j] = risk_on_corr
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
    factor_returns: pd.DataFrame | None = None,
    stress_cov_method: str = "taxonomy_blend_v1",
    scenario_overrides: dict[str, dict[str, float]] | None = None,
    hedge_assets: list[str] | None = None,
    beta_data_source: str | None = None,
    cov_base: pd.DataFrame | None = None,
    prepared_synthetic: PreparedSyntheticStressInputs | None = None,
    loss_gate_mode: str = LOSS_GATE_MODE_MANDATE,
    **_: Any,
) -> dict[str, Any]:
    """
    Diagnostic stress suite (non-blocking).

    ``loss_gate_mode="mandate"`` (legacy): suite status DIAG_*; row pass/loss_ok vs client MaxDD.
    ``loss_gate_mode="diagnostic"`` (Core MVP portfolio-first): status ok/warning/insufficient_data;
    no mandate pass/fail on scenario rows.
    """
    gate_mode = _normalize_loss_gate_mode(loss_gate_mode)
    use_mandate_gate = gate_mode == LOSS_GATE_MODE_MANDATE
    cash_u = (cash_proxy_ticker or "").strip().upper()
    asset_cols = [t for t in tickers if t in monthly_returns.columns]
    if not asset_cols:
        return _empty_report("No return data for stress", loss_gate_mode=gate_mode)
    returns_sub = monthly_returns[asset_cols].dropna(how="all")
    if len(returns_sub) < 2:
        return _empty_report("Insufficient return history", loss_gate_mode=gate_mode)

    if use_mandate_gate:
        max_dd_limit = abs(target_max_drawdown_pct) if target_max_drawdown_pct is not None else 0.25
    else:
        max_dd_limit = None

    if cov_base is not None and not cov_base.empty:
        try:
            cov_base = cov_base.loc[asset_cols, asset_cols]
        except (KeyError, ValueError):
            cov_base = cov_matrix_monthly(returns_sub, ddof=1)
    else:
        cov_base = cov_matrix_monthly(returns_sub, ddof=1)
    risk_on = [t for t in asset_cols if str(t).strip().upper() != cash_u]

    w_vec = np.array([weights.get(t, 0.0) for t in asset_cols])
    w_vec = w_vec / w_vec.sum() if w_vec.sum() > 0 else w_vec

    use_prepared_synthetic = prepared_synthetic_stress_usable(
        prepared_synthetic,
        asset_cols=asset_cols,
        stress_cov_method=stress_cov_method,
    )

    scenario_results = []
    worst_loss = 0.0
    recession_calibration, recession_shock = _calibrate_recession_severe(factor_returns, portfolio_betas)
    scenario_defs: dict[str, dict[str, Any]] = {
        **SCENARIOS,
        "recession_severe": {
            **recession_shock,
            **RECESSION_SEVERE_PARAMS,
            "calibration_source_episode": recession_calibration.get("selected_source_episode"),
        },
    }
    if isinstance(scenario_overrides, dict):
        for sid, override in scenario_overrides.items():
            if sid in scenario_defs and isinstance(override, dict):
                merged = dict(scenario_defs[sid])
                for key, value in override.items():
                    if key.startswith("shock_") or key in {"vol_mult", "risk_on_corr"}:
                        try:
                            merged[key] = float(value)
                        except (TypeError, ValueError):
                            continue
                    elif key == "stress_cov":
                        merged[key] = bool(value)
                scenario_defs[sid] = merged

    for scenario_id, params in scenario_defs.items():
        shock = {k: v for k, v in params.items() if k.startswith("shock_") and isinstance(v, (int, float))}
        vol_mult = float(params.get("vol_mult", 1.0))
        use_stress_cov = bool(params.get("stress_cov", False))
        risk_on_corr = float(params.get("risk_on_corr", 0.90))

        prepared_row = (
            use_prepared_synthetic
            and scenario_id != "recession_severe"
            and prepared_synthetic is not None
            and scenario_id in prepared_synthetic.r_asset_by_scenario
        )
        if prepared_row:
            fallback_assets = list(prepared_synthetic.fallback_assets)
            beta_coverage_ratio = float(prepared_synthetic.beta_coverage_ratio)
            covered_assets = [t for t in asset_cols if t not in set(fallback_assets)]
            r_asset = prepared_synthetic.r_asset_by_scenario[scenario_id].reindex(asset_cols).fillna(0)
        else:
            fallback_assets, beta_coverage_ratio = _beta_coverage_meta(asset_betas, asset_cols)
            covered_assets = [t for t in asset_cols if t not in set(fallback_assets)]
            r_asset = _scenario_return_per_asset(shock, asset_betas, asset_cols)
            r_asset = r_asset.reindex(asset_cols).fillna(0)
        pnl_i = w_vec * r_asset.values
        portfolio_pnl_pct = float(np.sum(pnl_i))

        if use_stress_cov:
            if (
                prepared_row
                and prepared_synthetic is not None
                and scenario_id in prepared_synthetic.cov_stress_by_scenario
            ):
                cov_full = prepared_synthetic.cov_stress_by_scenario[scenario_id]
                cov_s = cov_full.loc[asset_cols, asset_cols]
                cov_meta = dict(prepared_synthetic.cov_meta_by_scenario.get(scenario_id) or {})
            elif stress_cov_method == "uniform_legacy":
                cov_s = _stress_covariance(cov_base, risk_on, vol_mult, risk_on_corr=risk_on_corr)
                cov_meta = {
                    "stress_cov_method": "uniform_legacy",
                    "stress_cov_lambda": None,
                    "stress_cov_calibration_version": None,
                    "taxonomy_coverage": {},
                    "vol_mult_by_block": None,
                    "key_rho_overrides_used": None,
                }
            else:
                cov_s, cov_diag = stress_covariance_taxonomy_blend(
                    cov_base,
                    asset_cols,
                    scenario_id,
                    cash_proxy_ticker=cash_proxy_ticker,
                )
                cov_meta = {
                    "stress_cov_method": cov_diag.get("stress_cov_method", "taxonomy_blend_v1"),
                    "stress_cov_lambda": cov_diag.get("stress_cov_lambda"),
                    "stress_cov_calibration_version": cov_diag.get("stress_cov_calibration_version"),
                    "taxonomy_coverage": cov_diag.get("taxonomy_coverage") or {},
                    "vol_mult_by_block": cov_diag.get("vol_mult_by_block"),
                    "key_rho_overrides_used": cov_diag.get("key_rho_overrides_used"),
                }
        else:
            cov_s = cov_base.copy()
            cov_meta = {
                "stress_cov_method": None,
                "stress_cov_lambda": None,
                "stress_cov_calibration_version": None,
                "taxonomy_coverage": {},
                "vol_mult_by_block": None,
                "key_rho_overrides_used": None,
            }

        pc = percentage_contributions_variance(w_vec, cov_s.values)
        pc_series = pd.Series(pc, index=asset_cols).sort_values(ascending=False)
        top1_asset = pc_series.index[0] if len(pc_series) else None
        top1_rc_pct = float(pc_series.iloc[0]) if len(pc_series) else 0.0
        top3_assets = list(pc_series.index[:3])
        top3_rc_sum_pct = float(pc_series.iloc[:3].sum())

        pnl_contrib = pd.Series(pnl_i, index=asset_cols)
        top3_loss_assets = list(pnl_contrib.sort_values().head(3).index)

        if use_mandate_gate:
            loss_ok = portfolio_pnl_pct >= -float(max_dd_limit)
            scenario_pass = loss_ok
            loss_diags: list[str] = []
            if not loss_ok:
                c = _build_diagnostic_code("Loss", scenario_id)
                if c:
                    loss_diags.append(c)
        else:
            loss_ok = None
            scenario_pass = None
            loss_diags = []

        if portfolio_pnl_pct < worst_loss:
            worst_loss = portfolio_pnl_pct

        pnl_by_asset_pct = {str(asset_cols[i]): round(float(pnl_i[i]), 4) for i in range(len(asset_cols))}
        pnl_by_factor_pct = _portfolio_factor_pnl_pct(shock, portfolio_betas)

        row = {
            "scenario_id": scenario_id,
            "portfolio_pnl_pct": round(portfolio_pnl_pct, 4),
            "shock_vector": {k: round(float(v), 4) for k, v in shock.items()},
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
            "stress_cov_method": cov_meta.get("stress_cov_method"),
            "stress_cov_lambda": cov_meta.get("stress_cov_lambda"),
            "stress_cov_calibration_version": cov_meta.get("stress_cov_calibration_version"),
            "taxonomy_coverage": cov_meta.get("taxonomy_coverage"),
            "vol_mult_by_block": cov_meta.get("vol_mult_by_block"),
            "key_rho_overrides_used": cov_meta.get("key_rho_overrides_used"),
            "beta_fallback_assets": fallback_assets,
            "beta_coverage_ratio": round(beta_coverage_ratio, 4),
            "synthetic_assumptions": _synthetic_assumptions_block(
                fallback_assets=fallback_assets,
                beta_coverage_ratio=beta_coverage_ratio,
                beta_data_source=beta_data_source,
                covered_assets=covered_assets,
                missing_assets=fallback_assets,
                fallback_reason="missing_asset_factor_betas" if fallback_assets else None,
            ),
        }
        if scenario_id == "recession_severe":
            row["calibration_source_episode"] = params.get("calibration_source_episode")
            row["vol_mult"] = round(vol_mult, 4)
            row["risk_on_corr"] = round(risk_on_corr, 4)
        scenario_results.append(row)

    factor_betas = {
        k: round(v, 4)
        for k, v in portfolio_betas.items()
        if str(k) in PRODUCTION_FACTOR_BETA_KEYS
    }

    historical_results = []
    historical_episode_paths: list[dict[str, Any]] = []
    for ep_id, start, end in HISTORICAL_EPISODES:
        try:
            full_ep = returns_sub.loc[start:end] if hasattr(returns_sub.index, "slice_indexer") else returns_sub
            n_expected_obs = int(len(full_ep))
            sub = full_ep.dropna(how="any")
            n_obs = int(len(sub))
            coverage_ratio, quality = _historical_data_quality(n_obs, n_expected_obs)
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
                    "n_obs": n_obs,
                    "n_expected_obs": n_expected_obs,
                    "coverage_ratio": round(coverage_ratio, 4) if coverage_ratio is not None else None,
                    "data_quality": quality,
                    **_historical_row_disclosure_fields(),
                })
                continue
            port_ret = sub.dot(w_vec)
            port_eq = (1 + port_ret).cumprod()
            port_dd = port_eq / port_eq.cummax() - 1
            max_dd = float(port_dd.min())
            pnl_real_episode = float(port_eq.iloc[-1] - 1.0) if len(port_eq) else None
            if use_mandate_gate:
                pass_dd = max_dd >= -float(max_dd_limit)
                hist_diag = _build_diagnostic_code("Historical", ep_id) if pass_dd is False else None
            else:
                pass_dd = None
                hist_diag = None

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
                "diagnostic_code": hist_diag,
                "n_obs": n_obs,
                "n_expected_obs": n_expected_obs,
                "coverage_ratio": round(coverage_ratio, 4) if coverage_ratio is not None else None,
                "data_quality": quality,
                **_historical_row_disclosure_fields(),
            })
            path_rows = []
            for dt in port_ret.index:
                idx = port_ret.index.get_loc(dt)
                path_rows.append(
                    {
                        "date": pd.Timestamp(dt).strftime("%Y-%m-%d"),
                        "portfolio_return": round(float(port_ret.iloc[idx]), 6),
                        "equity": round(float(port_eq.iloc[idx]), 6),
                        "drawdown": round(float(port_dd.iloc[idx]), 6),
                    }
                )
            asset_pnl_contrib = _episode_asset_pnl_contrib(sub, asset_cols, w_vec)
            historical_episode_paths.append(
                {
                    "replay_version": CRISIS_REPLAY_VERSION,
                    "episode": ep_id,
                    "episode_start": start,
                    "episode_end": end,
                    "n_obs": n_obs,
                    "n_expected_obs": n_expected_obs,
                    "coverage_ratio": round(coverage_ratio, 4) if coverage_ratio is not None else None,
                    "data_quality": quality,
                    **_episode_recovery_fields(port_ret),
                    "asset_pnl_contrib_episode": asset_pnl_contrib,
                    "top_loss_assets_episode": _top_loss_assets_from_contrib(asset_pnl_contrib),
                    "rows": path_rows,
                }
            )
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
                "n_obs": 0,
                "n_expected_obs": 0,
                "coverage_ratio": None,
                "data_quality": "insufficient_data",
                **_historical_row_disclosure_fields(),
            })

    recession_calibration = _attach_recession_validation(
        recession_calibration,
        portfolio_betas,
        historical_results,
    )

    diagnostic_codes: list[str] = []
    seen_codes: set[str] = set()

    def _push_diag(code: str | None) -> None:
        if code and code not in seen_codes:
            seen_codes.add(code)
            diagnostic_codes.append(code)

    if use_mandate_gate:
        for s in scenario_results:
            for c in s.get("diagnostic_codes") or []:
                _push_diag(c)
        for h in historical_results:
            if h.get("pass") is False:
                _push_diag(h.get("diagnostic_code") or _build_diagnostic_code("Historical", str(h.get("episode", ""))))

    hist_inconclusive = any(h.get("pass") is None and h.get("max_dd") is None for h in historical_results)

    primary_diagnostic_code: str | None = None
    failed_test: str | None = None
    failed_scenario: str | None = None
    warning_code: str | None = None
    fail_reason_code: str | None = None

    if use_mandate_gate:
        primary_diagnostic_code = diagnostic_codes[0] if diagnostic_codes else None
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
    else:
        status, warning_code = _resolve_diagnostic_suite_status(
            historical_results,
            hist_inconclusive=hist_inconclusive,
        )
        fail_reason_code = None
        primary_diagnostic_code = None
        failed_test = None
        failed_scenario = None

    worst_scenario_row = None
    if scenario_results:
        worst_scenario_row = min(
            scenario_results,
            key=lambda x: float(x.get("portfolio_pnl_pct", 0.0)),
        )
    worst_historical_row = _select_worst_historical_row(historical_results)
    helped_assets: list[dict[str, Any]] = []
    if isinstance(worst_scenario_row, dict):
        by_asset = worst_scenario_row.get("pnl_by_asset_pct") or {}
        if isinstance(by_asset, dict):
            positive = sorted(
                ((str(t), float(v)) for t, v in by_asset.items() if isinstance(v, (int, float)) and float(v) > 0),
                key=lambda x: (-x[1], x[0]),
            )[:3]
            helped_assets = [{"ticker": t, "pnl_pct": round(v, 4)} for t, v in positive]
    hedge_gap_analysis = _build_hedge_gap_analysis(
        worst_scenario_row=worst_scenario_row if isinstance(worst_scenario_row, dict) else None,
        hedge_assets=hedge_assets,
        scenario_results=scenario_results,
    )
    stress_scorecard_v1 = _build_stress_scorecard_v1(
        status=status,
        primary_diagnostic_code=primary_diagnostic_code,
        warning_code=warning_code,
        max_dd_limit=max_dd_limit,
        scenario_results=scenario_results,
        historical_results=historical_results,
        loss_gate_mode=gate_mode,
    )
    stress_conclusions = _build_stress_conclusions(
        worst_scenario_row=worst_scenario_row if isinstance(worst_scenario_row, dict) else None,
        worst_historical_row=worst_historical_row if isinstance(worst_historical_row, dict) else None,
        helped_assets=helped_assets,
        historical_results=historical_results,
        max_dd_limit=max_dd_limit,
        hedge_gap_analysis=hedge_gap_analysis,
        overall_confidence=stress_scorecard_v1.get("overall_confidence", "medium"),
        loss_gate_mode=gate_mode,
    )
    data_trust_summary = build_stress_data_trust_summary(
        historical_results=historical_results,
        stress_conclusions=stress_conclusions,
        stress_scorecard_v1=stress_scorecard_v1,
        historical_episode_paths=historical_episode_paths,
    )

    report: dict[str, Any] = {
        "status": status,
        "loss_gate_mode": gate_mode,
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
        "historical_methodology": _historical_methodology_block(),
        "historical_episode_paths": historical_episode_paths,
        "max_dd_limit": max_dd_limit,
        "recession_calibration": recession_calibration,
        "stress_scorecard_v1": stress_scorecard_v1,
        "stress_conclusions": stress_conclusions,
        "data_trust_summary": data_trust_summary,
        "hedge_gap_analysis": hedge_gap_analysis,
    }
    attach_stress_results_v1(report)
    attach_hedge_gap_analysis_v1(report)
    attach_current_portfolio_stress_scorecard_v1(report)
    return report


def _empty_report(reason: str, *, loss_gate_mode: str = LOSS_GATE_MODE_MANDATE) -> dict[str, Any]:
    gate_mode = _normalize_loss_gate_mode(loss_gate_mode)
    if gate_mode == LOSS_GATE_MODE_DIAGNOSTIC:
        empty_status = "insufficient_data"
        empty_warning = _build_warning_code("DATA_INSUFFICIENT")
    else:
        empty_status = "DIAG_PASS_WITH_WARNING"
        empty_warning = _build_warning_code("DATA_INSUFFICIENT")
    report: dict[str, Any] = {
        "status": empty_status,
        "loss_gate_mode": gate_mode,
        "diagnostic_codes": [],
        "primary_diagnostic_code": None,
        "fail_reason_code": None,
        "warning_code": empty_warning,
        "worst_scenario_loss_pct": None,
        "failed_scenario": None,
        "failed_test": None,
        "scenario_results": [],
        "factor_betas": {},
        "historical_results": [],
        "historical_methodology": _historical_methodology_block(),
        "historical_episode_paths": [],
        "max_dd_limit": None,
        "recession_calibration": {},
        "stress_scorecard_v1": {
            "version": "stress_scorecard_v1",
            "overall_status": empty_status,
            "overall_reason": empty_warning,
            "overall_confidence": "low",
            "max_dd_limit": None,
            "n_synthetic_scenarios": 0,
            "n_historical_episodes": 0,
            "synthetic_scenarios": [],
            "historical_episodes": [],
        },
        "stress_conclusions": {
            "version": "stress_conclusions_v1",
            "overall_confidence": "low",
            "worst_synthetic_scenario": {
                "scenario_id": None,
                "portfolio_pnl_pct": None,
                "loss_severity": "unknown",
                "pass": None,
            },
            "worst_historical_episode": {
                "episode": None,
                "pnl_real_episode": None,
                "max_dd": None,
                "loss_severity": "unknown",
                "data_quality": None,
            },
            "top_loss_assets_worst_scenario": [],
            "helped_assets_worst_scenario": [],
            "top_factor_drivers_worst_scenario": [],
            "helped_factors_worst_scenario": [],
            "data_quality_warnings": _build_historical_data_quality_warnings([]),
            "hedge_gap_status": "not_applicable",
        },
        "hedge_gap_analysis": _hedge_gap_analysis_shell(
            method="stress_scenario_hedge_evidence_v2",
            considered=[],
            status="not_applicable",
            status_reason="no_hedge_labels",
            by_risk_type=[],
        ),
        "data_trust_summary": build_stress_data_trust_summary(
            historical_results=[],
            stress_conclusions={
                "version": "stress_conclusions_v1",
                "overall_confidence": "low",
                "data_quality_warnings": _build_historical_data_quality_warnings([]),
            },
            stress_scorecard_v1={
                "version": "stress_scorecard_v1",
                "overall_confidence": "low",
            },
            historical_episode_paths=[],
        ),
        "stress_results_v1": empty_stress_results_v1(reason, loss_gate_mode=gate_mode),
        "skip_reason": reason,
    }
    attach_hedge_gap_analysis_v1(report)
    attach_current_portfolio_stress_scorecard_v1(report)
    return report


CUSTOM_SHOCK_SIMULATOR_VERSION = "custom_shock_simulator_v1"


def _normalize_shock_vector(shock_vector: dict[str, float] | None) -> dict[str, float]:
    """Canonical shock_* map with zeros for missing factors (same keys as synthetic scenarios)."""
    valid_keys = {k for k, _ in _SHOCK_TO_BETA}
    shock: dict[str, float] = {}
    for key, value in (shock_vector or {}).items():
        if key in valid_keys:
            try:
                shock[key] = float(value)
            except (TypeError, ValueError):
                continue
    for key in valid_keys:
        shock.setdefault(key, 0.0)
    return shock


def shock_vector_from_scenario(
    scenario_id: str,
    *,
    factor_returns: pd.DataFrame | None = None,
    portfolio_betas: dict[str, float] | None = None,
) -> dict[str, float]:
    """
    Return the shock_* vector for a built-in synthetic scenario id.
    Used to align custom simulation inputs with `run_stress` scenario definitions.
    """
    if scenario_id == "recession_severe":
        _, shock = _calibrate_recession_severe(factor_returns, portfolio_betas or {})
        return _normalize_shock_vector(shock)
    params = SCENARIOS.get(scenario_id)
    if not isinstance(params, dict):
        raise KeyError(f"Unknown synthetic scenario_id: {scenario_id}")
    return _normalize_shock_vector(
        {k: float(v) for k, v in params.items() if k.startswith("shock_")}
    )


def simulate_custom_shock(
    *,
    tickers: list[str],
    weights: dict[str, float],
    asset_betas: pd.DataFrame,
    portfolio_betas: dict[str, float],
    shock_vector: dict[str, float],
    scenario_id: str | None = None,
) -> dict[str, Any]:
    """
    Simulate a one-off custom stress shock with the same linear engine as synthetic scenarios.
    This helper is diagnostic-only and does not change run_stress pass/fail logic.

    Portfolio PnL and per-asset PnL match `run_stress` scenario rows when `shock_vector`
    equals the built-in scenario shock (RC / stress-cov fields are only in full `run_stress`).
    """
    shock = _normalize_shock_vector(shock_vector)
    asset_cols = list(tickers)
    w_vec = np.array([float(weights.get(t, 0.0)) for t in asset_cols], dtype=float)
    if w_vec.sum() > 0:
        w_vec = w_vec / w_vec.sum()
    fallback_assets, beta_coverage_ratio = _beta_coverage_meta(asset_betas, asset_cols)
    covered_assets = [t for t in asset_cols if t not in set(fallback_assets)]
    r_asset = _scenario_return_per_asset(shock, asset_betas, asset_cols).reindex(asset_cols).fillna(0.0)
    pnl_i = w_vec * r_asset.values
    portfolio_pnl_pct = round(float(np.sum(pnl_i)), 4)
    pnl_by_asset_pct = {asset_cols[i]: round(float(pnl_i[i]), 4) for i in range(len(asset_cols))}
    return {
        "version": CUSTOM_SHOCK_SIMULATOR_VERSION,
        "method": "linear_factor_shock_v1",
        "scenario_id": scenario_id or "custom_shock",
        "shock_vector": {k: round(float(v), 4) for k, v in shock.items()},
        "portfolio_pnl_pct": portfolio_pnl_pct,
        "model_pnl_pct": portfolio_pnl_pct,
        "pnl_by_asset_pct": pnl_by_asset_pct,
        "pnl_by_factor_pct": _portfolio_factor_pnl_pct(shock, portfolio_betas),
        "top3_loss_assets": list(pd.Series(pnl_i, index=asset_cols).sort_values().head(3).index),
        "beta_fallback_assets": fallback_assets,
        "beta_coverage_ratio": round(beta_coverage_ratio, 4),
        "synthetic_assumptions": _synthetic_assumptions_block(
            fallback_assets=fallback_assets,
            beta_coverage_ratio=beta_coverage_ratio,
            covered_assets=covered_assets,
            missing_assets=fallback_assets,
            fallback_reason="missing_asset_factor_betas" if fallback_assets else None,
        ),
    }


CUSTOM_SHOCK_RUNS_VERSION = "custom_shock_runs_v1"
CUSTOM_SHOCK_RUNS_FILENAME = "custom_shock_runs.json"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _round_json_export(obj: Any) -> Any:
    """Round floats for JSON export (same 4dp rule as stress_report export)."""
    if isinstance(obj, dict):
        return {k: _round_json_export(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round_json_export(x) for x in obj]
    if isinstance(obj, float) and obj is not None and not isinstance(obj, bool):
        return round(obj, 4)
    return obj


def empty_custom_shock_runs_document() -> dict[str, Any]:
    """Versioned shell for optional custom-shock audit trail (not written by run_stress)."""
    now = _utc_now_iso()
    return {
        "version": CUSTOM_SHOCK_RUNS_VERSION,
        "simulator_version": CUSTOM_SHOCK_SIMULATOR_VERSION,
        "created_at": now,
        "updated_at": now,
        "n_runs": 0,
        "runs": [],
    }


def load_custom_shock_runs(path: str | Path) -> dict[str, Any]:
    """
    Load ``custom_shock_runs.json`` or return an empty document when missing or invalid version.
    """
    p = Path(path)
    if not p.is_file():
        return empty_custom_shock_runs_document()
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return empty_custom_shock_runs_document()
    if not isinstance(data, dict) or data.get("version") != CUSTOM_SHOCK_RUNS_VERSION:
        return empty_custom_shock_runs_document()
    runs = data.get("runs")
    if not isinstance(runs, list):
        data["runs"] = []
    data.setdefault("simulator_version", CUSTOM_SHOCK_SIMULATOR_VERSION)
    data["n_runs"] = len(data["runs"])
    return data


def build_custom_shock_run_entry(
    simulation: dict[str, Any],
    *,
    tickers: list[str],
    portfolio_betas: dict[str, float] | None = None,
    run_id: str | None = None,
    notes: str | None = None,
    analysis_subject: str | None = None,
) -> dict[str, Any]:
    """One appendable run row referencing a ``simulate_custom_shock`` result."""
    entry: dict[str, Any] = {
        "run_id": run_id or str(uuid.uuid4()),
        "recorded_at": _utc_now_iso(),
        "scenario_id": simulation.get("scenario_id"),
        "shock_vector": simulation.get("shock_vector"),
        "simulation": simulation,
        "inputs_summary": {
            "tickers": sorted(str(t) for t in tickers),
            "n_assets": len(tickers),
        },
        "provenance": {
            "source": "simulate_custom_shock",
            "simulator_version": simulation.get("version", CUSTOM_SHOCK_SIMULATOR_VERSION),
            "method": simulation.get("method"),
        },
    }
    if portfolio_betas is not None:
        entry["inputs_summary"]["portfolio_betas"] = {
            k: round(float(v), 4) for k, v in portfolio_betas.items()
        }
    if notes:
        entry["notes"] = str(notes)
    if analysis_subject:
        entry["analysis_subject"] = str(analysis_subject)
    return entry


def append_custom_shock_run(
    document: dict[str, Any],
    simulation: dict[str, Any],
    *,
    tickers: list[str],
    portfolio_betas: dict[str, float] | None = None,
    notes: str | None = None,
    analysis_subject: str | None = None,
) -> dict[str, Any]:
    """Append one run to an in-memory ``custom_shock_runs`` document (mutates and returns it)."""
    if document.get("version") != CUSTOM_SHOCK_RUNS_VERSION:
        document.clear()
        document.update(empty_custom_shock_runs_document())
    runs = document.setdefault("runs", [])
    if not isinstance(runs, list):
        runs = []
        document["runs"] = runs
    runs.append(
        build_custom_shock_run_entry(
            simulation,
            tickers=tickers,
            portfolio_betas=portfolio_betas,
            notes=notes,
            analysis_subject=analysis_subject,
        )
    )
    document["updated_at"] = _utc_now_iso()
    document["simulator_version"] = CUSTOM_SHOCK_SIMULATOR_VERSION
    document["n_runs"] = len(runs)
    return document


def write_custom_shock_runs(path: str | Path, document: dict[str, Any]) -> Path:
    """Persist a versioned ``custom_shock_runs`` document (optional artifact; not part of run_stress)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    out = _round_json_export(document)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False, default=str)
    return p


def record_custom_shock_run(
    *,
    tickers: list[str],
    weights: dict[str, float],
    asset_betas: pd.DataFrame,
    portfolio_betas: dict[str, float],
    shock_vector: dict[str, float],
    scenario_id: str | None = None,
    output_dir: str | Path | None = None,
    persist: bool = True,
    merge_existing: bool = True,
    notes: str | None = None,
    analysis_subject: str | None = None,
) -> dict[str, Any]:
    """
    Run ``simulate_custom_shock`` and optionally append to ``custom_shock_runs.json`` under
    ``output_dir``. Does not alter ``run_stress`` pass/fail or mandate gates.
    """
    simulation = simulate_custom_shock(
        tickers=tickers,
        weights=weights,
        asset_betas=asset_betas,
        portfolio_betas=portfolio_betas,
        shock_vector=shock_vector,
        scenario_id=scenario_id,
    )
    result: dict[str, Any] = {"simulation": simulation, "document": None, "path": None}
    if not persist or output_dir is None:
        return result
    out_path = Path(output_dir) / CUSTOM_SHOCK_RUNS_FILENAME
    document = (
        load_custom_shock_runs(out_path)
        if merge_existing
        else empty_custom_shock_runs_document()
    )
    append_custom_shock_run(
        document,
        simulation,
        tickers=tickers,
        portfolio_betas=portfolio_betas,
        notes=notes,
        analysis_subject=analysis_subject,
    )
    write_custom_shock_runs(out_path, document)
    result["document"] = document
    result["path"] = out_path
    return result
