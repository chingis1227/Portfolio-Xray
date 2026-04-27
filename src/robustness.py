"""
Dual-horizon optimization robustness check (10Y primary + 5Y secondary validation).

Compares weights and per-asset RC from primary vs secondary optimization;
produces deterministic flags and diagnostics.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.optimization import portfolio_vol_annual, rc_by_asset_from_weights

FLAG_WEIGHT_INSTABILITY = "FLAG_WEIGHT_INSTABILITY"
FLAG_RC_INSTABILITY = "FLAG_RC_INSTABILITY"
FLAG_SHORT_SAMPLE = "FLAG_SHORT_SAMPLE"


def _expected_return_from_weights(weights: dict[str, float], mu_series: pd.Series) -> float:
    tickers = [t for t in weights if t in mu_series.index and weights.get(t, 0) != 0]
    if not tickers:
        return 0.0
    w = np.array([weights[t] for t in tickers])
    mu = mu_series.reindex(tickers).fillna(0).values
    return float(np.dot(w, mu))


def compute_robustness_diagnostics(
    weights_10y: dict[str, float],
    weights_5y: dict[str, float],
    cov_10y: pd.DataFrame,
    cov_5y: pd.DataFrame,
    mu_10y: pd.Series,
    mu_5y: pd.Series,
    effective_months_10y: int,
    effective_months_5y: int,
    **_: Any,
) -> dict[str, Any]:
    """Compare 10Y vs 5Y optimization results (same universe)."""
    all_tickers = sorted(set(weights_10y) | set(weights_5y))
    delta_w = {t: abs(weights_5y.get(t, 0.0) - weights_10y.get(t, 0.0)) for t in all_tickers}
    max_delta_w = max(delta_w.values()) if delta_w else 0.0
    top5_deltas = sorted([(t, delta_w[t]) for t in all_tickers], key=lambda x: (-x[1], x[0]))[:5]

    rc_asset_10y = rc_by_asset_from_weights(weights_10y, cov_10y)
    rc_asset_5y = rc_by_asset_from_weights(weights_5y, cov_5y)

    vol_10y_under_sigma10y = portfolio_vol_annual(weights_10y, cov_10y)
    vol_10y_under_sigma5y = portfolio_vol_annual(weights_10y, cov_5y)
    vol_5y_under_sigma5y = portfolio_vol_annual(weights_5y, cov_5y)
    vol_5y_under_sigma10y = portfolio_vol_annual(weights_5y, cov_10y)

    exp_ret_10y_under_mu10y = _expected_return_from_weights(weights_10y, mu_10y)
    exp_ret_10y_under_mu5y = _expected_return_from_weights(weights_10y, mu_5y)
    exp_ret_5y_under_mu10y = _expected_return_from_weights(weights_5y, mu_10y)
    exp_ret_5y_under_mu5y = _expected_return_from_weights(weights_5y, mu_5y)

    common_rc_tickers = sorted(set(rc_asset_10y) | set(rc_asset_5y))
    rc_asset_deltas = {
        t: abs(rc_asset_5y.get(t, 0.0) - rc_asset_10y.get(t, 0.0))
        for t in common_rc_tickers
    }
    max_rc_asset_delta = max(rc_asset_deltas.values()) if rc_asset_deltas else 0.0

    return {
        "effective_months_10y": effective_months_10y,
        "effective_months_5y": effective_months_5y,
        "weights_10y": dict(weights_10y),
        "weights_5y": dict(weights_5y),
        "delta_w": delta_w,
        "max_delta_w": max_delta_w,
        "top5_delta_w": top5_deltas,
        "rc_by_asset_10y": rc_asset_10y,
        "rc_by_asset_5y": rc_asset_5y,
        "rc_asset_deltas": rc_asset_deltas,
        "max_rc_asset_delta": max_rc_asset_delta,
        "vol_10y_under_sigma10y": vol_10y_under_sigma10y,
        "vol_10y_under_sigma5y": vol_10y_under_sigma5y,
        "vol_5y_under_sigma5y": vol_5y_under_sigma5y,
        "vol_5y_under_sigma10y": vol_5y_under_sigma10y,
        "exp_ret_10y_under_mu10y_annual": exp_ret_10y_under_mu10y * 12,
        "exp_ret_10y_under_mu5y_annual": exp_ret_10y_under_mu5y * 12,
        "exp_ret_5y_under_mu10y_annual": exp_ret_5y_under_mu10y * 12,
        "exp_ret_5y_under_mu5y_annual": exp_ret_5y_under_mu5y * 12,
    }


def compute_robustness_flags(
    diagnostics: dict[str, Any],
    policy: dict[str, Any],
) -> list[str]:
    flags: list[str] = []
    max_w = policy.get("max_weight_change_allowed", 0.10)
    max_rc_asset = policy.get("max_asset_rc_dev_allowed", 0.05)
    min_months = policy.get("min_effective_months", 36)

    if diagnostics.get("max_delta_w", 0) > max_w:
        flags.append(FLAG_WEIGHT_INSTABILITY)
    if diagnostics.get("effective_months_10y", 0) < min_months or diagnostics.get("effective_months_5y", 0) < min_months:
        flags.append(FLAG_SHORT_SAMPLE)
    if diagnostics.get("max_rc_asset_delta", 0) > max_rc_asset:
        flags.append(FLAG_RC_INSTABILITY)

    return list(dict.fromkeys(flags))
