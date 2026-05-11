"""
Historical stress fallback v1 — per-asset episode returns for robust optimization consumers.

Waterfall: direct ETF → ticker proxy → asset-class proxy → factor replay.
Does not mutate upstream stress_report or mandate outputs.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from src.stress import FACTOR_TO_SHOCK_KEY, _scenario_return_per_asset

_HIST_METHOD_RANK = {
    "direct_etf_history": 1,
    "ticker_proxy": 2,
    "asset_class_proxy": 3,
    "factor_replay": 4,
    "unavailable": 5,
}


def default_historical_stress_proxy_config() -> dict[str, Any]:
    """Load packaged defaults from config/historical_stress_proxy_map.yml."""
    root = Path(__file__).resolve().parents[1]
    p = root / "config" / "historical_stress_proxy_map.yml"
    if not p.is_file():
        return {
            "min_coverage_ratio": 0.45,
            "ticker_proxies": {},
            "ticker_asset_class": {},
            "asset_class_proxies": {},
        }
    with p.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data if isinstance(data, dict) else {}


def merge_proxy_config(base: dict[str, Any] | None, override: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(default_historical_stress_proxy_config())
    if base:
        for k, v in base.items():
            if isinstance(v, dict) and isinstance(out.get(k), dict):
                merged = dict(out[k])
                merged.update(v)
                out[k] = merged
            else:
                out[k] = v
    if override:
        for k, v in override.items():
            if isinstance(v, dict) and isinstance(out.get(k), dict):
                merged = dict(out[k])
                merged.update(v)
                out[k] = merged
            else:
                out[k] = v
    return out


def _month_slice_returns(
    monthly_returns: pd.DataFrame,
    ticker: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> tuple[pd.Series, int, int]:
    """Returns (simple return series aligned to months in window, n_valid, n_total)."""
    if ticker not in monthly_returns.columns:
        return pd.Series(dtype=float), 0, 0
    mr = monthly_returns.copy()
    mr.index = pd.to_datetime(mr.index).tz_localize(None)
    sub = mr.loc[start:end, ticker].astype(float)
    sub = sub.dropna()
    if len(sub) < 2:
        return sub, int(sub.notna().sum()), int(len(mr.loc[start:end, ticker]))
    # compound over episode
    tot = len(mr.loc[start:end, ticker])
    valid = int(monthly_returns.loc[start:end, ticker].notna().sum())
    return sub, valid, max(tot, 1)


def compound_episode_simple_return(series: pd.Series) -> float | None:
    if series is None or len(series) < 2:
        return None
    r = series.astype(float).values
    return float(np.prod(1.0 + r) - 1.0)


def episode_factor_shocks_sum(
    factor_returns: pd.DataFrame | None,
    start: str,
    end: str,
) -> dict[str, float]:
    """Sum weekly (or any bar) factor moves in [start,end] into shock_* keys."""
    if factor_returns is None or factor_returns.empty:
        return {}
    fr = factor_returns.copy()
    fr.index = pd.to_datetime(fr.index).tz_localize(None)
    s = pd.Timestamp(start)
    e = pd.Timestamp(end)
    try:
        sub = fr.loc[s:e]
    except Exception:
        sub = fr
    if sub.empty:
        return {}
    shock: dict[str, float] = {}
    for factor_col, shock_key in FACTOR_TO_SHOCK_KEY.items():
        if factor_col not in sub.columns:
            continue
        val = sub[factor_col].dropna().sum()
        if pd.notna(val):
            shock[shock_key] = float(val)
    for shock_key in FACTOR_TO_SHOCK_KEY.values():
        shock.setdefault(shock_key, 0.0)
    return shock


def asset_betas_from_stress_report(stress_report: dict[str, Any] | None, tickers: list[str]) -> pd.DataFrame:
    """Best-effort asset beta DataFrame for _scenario_return_per_asset."""
    empty = pd.DataFrame(index=list(tickers))
    if not stress_report:
        return empty
    raw = (
        stress_report.get("asset_factor_betas")
        or stress_report.get("asset_factor_betas_weekly")
        or stress_report.get("asset_factor_betas_weekly_5y")
    )
    if not isinstance(raw, dict):
        return empty
    rows = []
    idx = []
    for t in tickers:
        key_candidates = [t, str(t).upper()]
        br = None
        for k in key_candidates:
            if k in raw and isinstance(raw[k], dict):
                br = raw[k]
                break
        if br is None:
            continue
        flat = {}
        inner = br.get("betas") if isinstance(br.get("betas"), dict) else br
        if not isinstance(inner, dict):
            continue
        for bk, bv in inner.items():
            if str(bk).startswith("beta_") and isinstance(bv, (int, float)):
                flat[str(bk)] = float(bv)
        if flat:
            idx.append(t)
            rows.append(flat)
    if not rows:
        return empty
    df = pd.DataFrame(rows, index=idx)
    return df.reindex(tickers).fillna(0.0)


def dominant_historical_stress_method(per_asset: dict[str, str]) -> str:
    """Worst tier across assets defines portfolio-level method tag."""
    worst_rank = 0
    worst_name = "direct_etf_history"
    for m in per_asset.values():
        r = _HIST_METHOD_RANK.get(m, 5)
        if r >= worst_rank:
            worst_rank = r
            worst_name = m
    return worst_name


def build_historical_episode_asset_returns(
    *,
    scenario_id: str,
    episode_start: str,
    episode_end: str,
    risk_tickers: list[str],
    monthly_returns: pd.DataFrame | None,
    stress_report: dict[str, Any] | None,
    proxy_config: dict[str, Any] | None = None,
    factor_returns_weekly: pd.DataFrame | None = None,
) -> tuple[dict[str, float], dict[str, Any]]:
    """
    Returns (returns_by_ticker, metadata). Missing tickers omitted or nan → unavailable.
    """
    cfg = merge_proxy_config(None, proxy_config)
    min_cov = float(cfg.get("min_coverage_ratio") or 0.45)
    ticker_proxies: dict[str, str] = {
        str(k).upper(): str(v).upper() for k, v in (cfg.get("ticker_proxies") or {}).items()
    }
    ticker_class: dict[str, str] = {str(k).upper(): str(v) for k, v in (cfg.get("ticker_asset_class") or {}).items()}
    class_proxy: dict[str, str] = {str(k): str(v).upper() for k, v in (cfg.get("asset_class_proxies") or {}).items()}

    start = pd.Timestamp(episode_start)
    end = pd.Timestamp(episode_end)

    per_asset_method: dict[str, str] = {}
    returns_out: dict[str, float] = {}
    warnings: list[str] = []
    coverages: list[float] = []

    asset_betas_df = asset_betas_from_stress_report(stress_report, risk_tickers)

    fr_weekly = factor_returns_weekly
    if fr_weekly is None and stress_report:
        fr_block = stress_report.get("factor_returns_weekly")
        if isinstance(fr_block, dict) and fr_block.get("index") and fr_block.get("data"):
            try:
                fr_weekly = pd.DataFrame(
                    fr_block["data"],
                    index=pd.to_datetime(fr_block["index"]),
                    columns=fr_block.get("columns"),
                )
            except Exception:
                fr_weekly = None

    shock_vec = episode_factor_shocks_sum(fr_weekly, episode_start, episode_end)

    for t in risk_tickers:
        tu = str(t).upper()
        method_used = "unavailable"
        r_val: float | None = None
        cov_ratio = 0.0

        if monthly_returns is not None and not monthly_returns.empty:
            series, nv, nt = _month_slice_returns(monthly_returns, t, start, end)
            cov_ratio = float(nv / nt) if nt else 0.0
            if cov_ratio >= min_cov and len(series) >= 2:
                r_val = compound_episode_simple_return(series)
                if r_val is not None and np.isfinite(r_val):
                    method_used = "direct_etf_history"

            if r_val is None or not np.isfinite(float(r_val)):
                px = ticker_proxies.get(tu)
                if px and px in monthly_returns.columns:
                    series_p, nv_p, nt_p = _month_slice_returns(monthly_returns, px, start, end)
                    cr = float(nv_p / nt_p) if nt_p else 0.0
                    if cr >= min_cov and len(series_p) >= 2:
                        r_val = compound_episode_simple_return(series_p)
                        if r_val is not None and np.isfinite(r_val):
                            method_used = "ticker_proxy"
                            cov_ratio = cr
                            warnings.append(f"{tu}:ticker_proxy->{px}")

            if r_val is None or not np.isfinite(float(r_val)):
                acl = ticker_class.get(tu)
                rep = class_proxy.get(acl or "") if acl else None
                if rep and rep in monthly_returns.columns:
                    series_c, nv_c, nt_c = _month_slice_returns(monthly_returns, rep, start, end)
                    cr = float(nv_c / nt_c) if nt_c else 0.0
                    if cr >= min_cov and len(series_c) >= 2:
                        r_val = compound_episode_simple_return(series_c)
                        if r_val is not None and np.isfinite(r_val):
                            method_used = "asset_class_proxy"
                            cov_ratio = cr
                            warnings.append(f"{tu}:asset_class_proxy:{acl}->{rep}")

        if r_val is None or not np.isfinite(float(r_val)):
            if shock_vec:
                r_series = _scenario_return_per_asset(shock_vec, asset_betas_df, [t])
                rv = float(r_series.reindex([t]).fillna(0.0).iloc[0])
                if np.isfinite(rv):
                    r_val = rv
                    method_used = "factor_replay"
                    cov_ratio = max(cov_ratio, 1.0)
                    warnings.append(f"{tu}:factor_replay")

        if r_val is None or not np.isfinite(float(r_val)):
            method_used = "unavailable"
            warnings.append(f"{tu}:historical_episode_return_unavailable")
        else:
            returns_out[t] = float(r_val)
            coverages.append(float(cov_ratio))

        per_asset_method[t] = method_used

    dom = dominant_historical_stress_method(per_asset_method)
    proxy_coverage_ratio = float(np.mean(coverages)) if coverages else 0.0

    assets_direct = [k for k, v in per_asset_method.items() if v == "direct_etf_history"]
    assets_proxy = [k for k, v in per_asset_method.items() if v == "ticker_proxy"]
    assets_ac = [k for k, v in per_asset_method.items() if v == "asset_class_proxy"]
    assets_fr = [k for k, v in per_asset_method.items() if v == "factor_replay"]
    assets_un = [k for k, v in per_asset_method.items() if v == "unavailable"]

    if assets_un:
        sq = "insufficient_data"
    elif dom == "factor_replay" or len(assets_fr) == len(risk_tickers):
        sq = "low_confidence"
    elif dom == "asset_class_proxy" or assets_ac:
        sq = "usable"
    elif dom == "ticker_proxy" and not assets_ac and not assets_fr:
        sq = "reliable"
    elif dom == "direct_etf_history":
        sq = "reliable"
    else:
        sq = "usable"

    meta: dict[str, Any] = {
        "historical_stress_method": dom,
        "historical_stress_method_per_asset": per_asset_method,
        "proxy_coverage_ratio": round(proxy_coverage_ratio, 6),
        "assets_with_direct_history": assets_direct,
        "assets_with_proxy_history": assets_proxy,
        "assets_using_asset_class_proxy": assets_ac,
        "assets_using_factor_replay": assets_fr,
        "assets_unavailable": assets_un,
        "scenario_quality_status": sq,
        "warnings": warnings,
        "scenario_id": scenario_id,
        "episode_start": episode_start,
        "episode_end": episode_end,
    }
    return returns_out, meta


def episode_window_for_scenario(scenario_id: str) -> tuple[str, str] | None:
    """Resolve episode dates from src.stress.HISTORICAL_EPISODES."""
    from src.stress import HISTORICAL_EPISODES

    for ep_id, start, end in HISTORICAL_EPISODES:
        if ep_id == scenario_id:
            return start, end
    return None


__all__ = [
    "build_historical_episode_asset_returns",
    "default_historical_stress_proxy_config",
    "dominant_historical_stress_method",
    "episode_window_for_scenario",
    "merge_proxy_config",
]
