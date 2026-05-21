from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable

import numpy as np
import pandas as pd


OPTIMIZER_CONFIG_FINGERPRINT_FIELDS: tuple[str, ...] = (
    "investor_currency",
    "tickers",
    "cash_proxy_ticker",
    "min_single_security_weight_pct",
    "max_single_security_weight_pct",
    "coverage_threshold",
    "covariance_shrinkage",
    "young_etf_optimization_policy",
    "minimum_cvar_confidence_level",
    "minimum_variance_turnover_lambda",
    "minimum_variance_l1_experimental",
    "target_vol_annual",
    "robust_mv_lambda",
    "robust_mv_covariance_method",
    "robust_mv_mu_shrinkage_method",
    "optimization_soft_vol_penalty_lambda",
    "optimization_soft_return_penalty_lambda",
    "target_nominal_return_annual",
    "cash_policy",
)


def _normalizable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _normalizable(v) for k, v in sorted(value.items())}
    if isinstance(value, (list, tuple, set)):
        return [_normalizable(v) for v in value]
    if isinstance(value, pd.Timestamp):
        return value.normalize().date().isoformat()
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float):
        if not np.isfinite(value):
            return None
        return float(value)
    return value


def stable_json_fingerprint(payload: Any) -> str:
    canonical = json.dumps(
        _normalizable(payload),
        sort_keys=True,
        separators=(",", ":"),
        default=str,
        allow_nan=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def returns_panel_fingerprint(returns: pd.DataFrame | pd.Series | None) -> str | None:
    if returns is None:
        return None
    df = returns.to_frame() if isinstance(returns, pd.Series) else returns.copy()
    if df is None:
        return None
    df = df.sort_index()
    columns = [str(c) for c in df.columns]
    values: list[list[float | None]] = []
    for row in df.to_numpy(dtype=float, copy=False):
        values.append([float(x) if np.isfinite(x) else None for x in row])
    payload = {
        "columns": columns,
        "index": [pd.Timestamp(idx).normalize().date().isoformat() for idx in df.index],
        "values": values,
    }
    return stable_json_fingerprint(payload)


def universe_fingerprint(tickers: Iterable[str] | None) -> str:
    ordered = [str(t).strip().upper() for t in (tickers or []) if str(t).strip()]
    return stable_json_fingerprint({"ordered_tickers": ordered, "unique_sorted_tickers": sorted(set(ordered))})


def optimizer_config_fingerprint(
    cfg: Any,
    *,
    extra: dict[str, Any] | None = None,
    fields: Iterable[str] = OPTIMIZER_CONFIG_FINGERPRINT_FIELDS,
) -> str:
    payload = {str(field): getattr(cfg, str(field), None) for field in fields}
    if extra:
        payload["extra"] = extra
    return stable_json_fingerprint(payload)


def returns_panel_disclosure(
    returns: pd.DataFrame | pd.Series | None,
) -> dict[str, Any]:
    if returns is None:
        return {
            "returns_panel_fingerprint": None,
            "returns_panel_rows": 0,
            "returns_panel_start": None,
            "returns_panel_end": None,
        }
    df = returns.to_frame() if isinstance(returns, pd.Series) else returns
    if df.empty:
        return {
            "returns_panel_fingerprint": returns_panel_fingerprint(df),
            "returns_panel_rows": 0,
            "returns_panel_start": None,
            "returns_panel_end": None,
        }
    idx = pd.DatetimeIndex(df.index)
    return {
        "returns_panel_fingerprint": returns_panel_fingerprint(df),
        "returns_panel_rows": int(len(df)),
        "returns_panel_start": idx.min().normalize().date().isoformat(),
        "returns_panel_end": idx.max().normalize().date().isoformat(),
    }
