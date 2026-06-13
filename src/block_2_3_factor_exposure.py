"""Block 2.3 Factor Exposure — product adapter over stress_report diagnostics.

This module intentionally does not calculate factor models.  It only adapts
existing ``stress_report`` factor diagnostics into a stable product-facing
Portfolio X-Ray contract.
"""
from __future__ import annotations

import math
from typing import Any

from src.analysis_setup import resolved_analysis_weights
from src.io_export import REPORT_DECIMALS
from src.real_cash import collect_real_cash_tickers

BLOCK_2_3_ID = "2.3_factor_exposure"
BLOCK_2_3_NAME = "Factor Exposure / Factor Sensitivity"
FACTOR_BETAS_3Y_WINDOW_MONTHS = 36
FACTOR_BETAS_3Y_UNAVAILABLE_REASON = (
    "No point-in-time 3Y OLS portfolio factor betas in stress_report "
    "(factor_betas_3y missing). Rolling beta summaries are not used as a 3Y snapshot substitute."
)

PRODUCTION_FACTOR_UNIVERSE: tuple[str, ...] = (
    "equity",
    "real_rates",
    "inflation",
    "credit",
    "USD",
    "commodity",
    "VIX_volatility",
    "us_growth",
)

PRODUCTION_BETA_KEYS: tuple[str, ...] = (
    "beta_eq",
    "beta_rr",
    "beta_inf",
    "beta_credit",
    "beta_usd",
    "beta_cmd",
    "beta_vix",
    "beta_us_growth",
)

BETA_TO_PRODUCT_FACTOR: dict[str, str] = dict(zip(PRODUCTION_BETA_KEYS, PRODUCTION_FACTOR_UNIVERSE))
PRODUCT_FACTOR_TO_BETA: dict[str, str] = {v: k for k, v in BETA_TO_PRODUCT_FACTOR.items()}

_INTERNAL_FACTOR_TO_PRODUCT: dict[str, str] = {
    "equity": "equity",
    "real_rates": "real_rates",
    "inflation": "inflation",
    "credit": "credit",
    "usd": "USD",
    "USD": "USD",
    "commodity": "commodity",
    "cmd": "commodity",
    "vix": "VIX_volatility",
    "VIX": "VIX_volatility",
    "volatility": "VIX_volatility",
    "VIX_volatility": "VIX_volatility",
    "us_growth": "us_growth",
    "growth": "us_growth",
}

_KALMAN_UNCERTAINTY_LABELS: frozenset[str] = frozenset({"low", "moderate", "high"})

_KALMAN_UNCERTAINTY_NOTES: dict[str, str] = {
    "low": "Current beta estimate appears relatively stable.",
    "moderate": "Current beta is useful but should be read together with 5Y/10Y beta.",
    "high": "Current beta is noisy and should be interpreted cautiously.",
    "unavailable": "Kalman beta is unavailable or skipped for this factor.",
}

# Beta stability across 3Y / 5Y / 10Y point-in-time OLS snapshots (adapter-only; not rolling summary).
_BETA_STABILITY_NEAR_ZERO = 0.03
_BETA_STABILITY_MODERATE_ABS_GAP = 0.12
_BETA_STABILITY_MODERATE_REL_GAP = 0.35
_BETA_STABILITY_UNSTABLE_ABS_GAP = 0.25
_BETA_STABILITY_UNSTABLE_REL_GAP = 0.75

# Kalman vs 5Y/10Y alignment (adapter-only; mirrors stress_factors divergence thresholds).
_KALMAN_ALIGN_ABS_GAP = 0.25
_KALMAN_ALIGN_REL_GAP = 0.75
_KALMAN_ALIGN_MIN_DENOM = 0.05

_PRODUCT_FACTOR_INTERPRETATIONS: dict[str, str] = {
    "equity": (
        "The portfolio shows sensitivity to equity risk. In risk-off markets, its behavior "
        "may be driven more by equity beta than by the number of holdings."
    ),
    "real_rates": (
        "The portfolio shows sensitivity to real rates. Rising real yields may pressure "
        "duration-sensitive assets."
    ),
    "inflation": (
        "The portfolio shows sensitivity to inflation-linked market moves. This should be "
        "checked later in the inflation or stagflation Stress Lab scenario."
    ),
    "credit": (
        "The portfolio may carry credit or liquidity-sensitive risk, especially if income "
        "assets behave like risk-on exposure during market stress."
    ),
    "USD": (
        "The portfolio has currency sensitivity to USD moves. This may matter if investor "
        "currency is not USD or if assets have strong USD exposure."
    ),
    "commodity": (
        "Commodity sensitivity may provide inflation linkage or introduce cyclical exposure "
        "depending on sign and stability."
    ),
    "VIX_volatility": (
        "Sensitivity to volatility indicates how the portfolio behaves when market risk "
        "aversion rises."
    ),
    "us_growth": (
        "US growth sensitivity indicates whether the portfolio is tied to the US economic cycle."
    ),
}


def _as_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        out = float(value)
        if math.isnan(out) or math.isinf(out):
            return None
        return out
    except (TypeError, ValueError):
        return None


def _round(value: Any) -> float | None:
    number = _as_float(value)
    if number is None:
        return None
    return round(number, REPORT_DECIMALS)


def _beta_map(raw: Any) -> dict[str, float | None]:
    out = {key: None for key in PRODUCTION_BETA_KEYS}
    if not isinstance(raw, dict):
        return out
    for key in PRODUCTION_BETA_KEYS:
        out[key] = _round(raw.get(key))
    return out


def _present_beta_keys(raw: Any) -> set[str]:
    if not isinstance(raw, dict):
        return set()
    return {str(k) for k, v in raw.items() if _as_float(v) is not None}


def _extra_beta_keys(raw: Any) -> list[str]:
    if not isinstance(raw, dict):
        return []
    return sorted(str(k) for k in raw if str(k) not in PRODUCTION_BETA_KEYS)


def _window_status(raw: Any) -> str:
    present = _present_beta_keys(raw)
    if not present:
        return "unavailable"
    if present >= set(PRODUCTION_BETA_KEYS):
        return "available"
    return "partial"


def _window_block(raw: Any, *, window_months: int, observations_used: int | None) -> dict[str, Any]:
    status = _window_status(raw)
    return {
        "status": status,
        "window_months": int(window_months),
        "frequency": "weekly",
        "betas": _beta_map(raw),
        "observations_used": observations_used,
        "missing_beta_keys": [key for key in PRODUCTION_BETA_KEYS if key not in _present_beta_keys(raw)],
        "extra_beta_keys": _extra_beta_keys(raw),
    }


def _regression_beta_order(reg: dict[str, Any]) -> list[str]:
    betas = reg.get("betas") if isinstance(reg.get("betas"), dict) else {}
    ordered = [key for key in PRODUCTION_BETA_KEYS if key in betas]
    ordered.extend(sorted(str(k) for k in betas if str(k) not in ordered))
    return ordered


def _hac_value(reg: dict[str, Any], beta_key: str, field: str) -> float | None:
    hac = reg.get("hac_inference") if isinstance(reg.get("hac_inference"), dict) else {}
    raw = hac.get(field)
    if isinstance(raw, dict):
        return _as_float(raw.get(beta_key))
    if isinstance(raw, list):
        order = _regression_beta_order(reg)
        if beta_key in order:
            idx = order.index(beta_key) + 1  # HAC arrays include intercept at position 0.
            if idx < len(raw):
                return _as_float(raw[idx])
    return None


def _ols_value(reg: dict[str, Any], beta_key: str, field: str) -> float | None:
    raw = reg.get(field)
    if isinstance(raw, dict):
        return _as_float(raw.get(beta_key))
    return None


def _confidence_status(
    *,
    beta_value: float | None,
    t_stat: float | None,
    p_value: float | None,
    n_obs: int | None,
    r_squared: float | None,
) -> str:
    if beta_value is None:
        return "unavailable"
    if n_obs is not None and n_obs < 30:
        return "unstable_low_confidence"
    if p_value is not None:
        if p_value <= 0.05:
            return "significant"
        if p_value <= 0.15:
            return "weak_evidence"
        return "unstable_low_confidence"
    if t_stat is not None:
        abs_t = abs(t_stat)
        if abs_t >= 2.0:
            return "significant"
        if abs_t >= 1.4:
            return "weak_evidence"
    if r_squared is not None and r_squared < 0.10:
        return "unstable_low_confidence"
    return "weak_evidence"


def _inference_source(hac_t: float | None, hac_p: float | None, ols_t: float | None, ols_p: float | None) -> str:
    if hac_t is not None or hac_p is not None:
        return "hac_newey_west"
    if ols_t is not None or ols_p is not None:
        return "ols_classic"
    return "unavailable"


def _inference_label(inference_source: str) -> str:
    if inference_source == "hac_newey_west":
        return "HAC"
    if inference_source == "ols_classic":
        return "OLS"
    return "regression"


def _beta_window_phrase(
    *,
    betas_3y: float | None,
    betas_5y: float | None,
    betas_10y: float | None,
) -> str:
    windows: list[str] = []
    if betas_3y is not None:
        windows.append("3Y")
    if betas_5y is not None:
        windows.append("5Y")
    if betas_10y is not None:
        windows.append("10Y")
    if len(windows) >= 2:
        return f" across {'/'.join(windows)} windows"
    if len(windows) == 1:
        return f" in the {windows[0]} window"
    return ""


def _confidence_reason(
    *,
    signal_confidence: str,
    beta_key: str,
    inference_source: str,
    p_value: float | None,
    t_stat: float | None,
    n_obs: int | None,
    r_squared: float | None,
    betas_3y: float | None,
    betas_5y: float | None,
    betas_10y: float | None,
) -> str:
    factor = BETA_TO_PRODUCT_FACTOR.get(beta_key, beta_key)
    infer = _inference_label(inference_source)
    window_phrase = _beta_window_phrase(betas_3y=betas_3y, betas_5y=betas_5y, betas_10y=betas_10y)

    if signal_confidence == "unavailable":
        return f"Unavailable because the factor beta is missing for the 5Y snapshot ({factor})."

    if signal_confidence == "significant":
        if p_value is not None:
            return f"{infer} p-value below 0.05 and beta is available{window_phrase}."
        return f"{infer} t-stat meets the strong-significance threshold and beta is available{window_phrase}."

    if signal_confidence == "weak_evidence":
        if p_value is not None:
            return f"Signal is visible but {infer} p-value is above the strong-significance threshold."
        return f"Signal is visible but {infer} t-stat is below the strong-significance threshold."

    reasons: list[str] = []
    if n_obs is not None and n_obs < 30:
        reasons.append("sample size is small")
    if p_value is not None and p_value > 0.15:
        reasons.append(f"{infer} p-value is high")
    elif t_stat is not None and abs(t_stat) < 1.4:
        reasons.append(f"{infer} t-stat is weak")
    if r_squared is not None and r_squared < 0.10:
        reasons.append("factor model explanatory power is weak")
    if reasons:
        return "Low confidence because " + " or ".join(reasons) + "."
    return f"Low confidence in the available {infer} factor signal for {factor}."


def _factor_signal_confidence(
    stress_report: dict[str, Any],
    *,
    betas_3y: dict[str, float | None],
    betas_5y: dict[str, float | None],
    betas_10y: dict[str, float | None],
) -> dict[str, dict[str, Any]]:
    """Product-facing OLS/HAC signal confidence (not Kalman uncertainty)."""
    reg = stress_report.get("factor_regression_5y")
    regression_window = "5y"
    if not isinstance(reg, dict) or not reg:
        reg = stress_report.get("factor_regression_10y") if isinstance(stress_report.get("factor_regression_10y"), dict) else {}
        regression_window = "10y"
    n_obs = None
    if isinstance(reg, dict) and reg.get("n_obs") is not None:
        try:
            n_obs = int(reg.get("n_obs"))
        except (TypeError, ValueError):
            n_obs = None
    r_squared = _as_float(reg.get("r2")) if isinstance(reg, dict) else None
    out: dict[str, dict[str, Any]] = {}
    for beta_key in PRODUCTION_BETA_KEYS:
        beta_value = betas_5y.get(beta_key)
        hac_t = _hac_value(reg, beta_key, "t") if isinstance(reg, dict) else None
        hac_p = _hac_value(reg, beta_key, "p") if isinstance(reg, dict) else None
        ols_t = _ols_value(reg, beta_key, "t") if isinstance(reg, dict) else None
        ols_p = _ols_value(reg, beta_key, "p") if isinstance(reg, dict) else None
        t_stat = hac_t if hac_t is not None else ols_t
        p_value = hac_p if hac_p is not None else ols_p
        inference_source = _inference_source(hac_t, hac_p, ols_t, ols_p)
        signal_confidence = _confidence_status(
            beta_value=beta_value,
            t_stat=t_stat,
            p_value=p_value,
            n_obs=n_obs,
            r_squared=r_squared,
        )
        out[beta_key] = {
            "signal_confidence": signal_confidence,
            "confidence_reason": _confidence_reason(
                signal_confidence=signal_confidence,
                beta_key=beta_key,
                inference_source=inference_source,
                p_value=p_value,
                t_stat=t_stat,
                n_obs=n_obs,
                r_squared=r_squared,
                betas_3y=betas_3y.get(beta_key),
                betas_5y=betas_5y.get(beta_key),
                betas_10y=betas_10y.get(beta_key),
            ),
            "inference_source": inference_source,
            "regression_window": regression_window,
        }
    return out


def _beta_sign(value: float, *, near_zero: float = _BETA_STABILITY_NEAR_ZERO) -> int:
    if abs(value) <= near_zero:
        return 0
    return 1 if value > 0 else -1


def _pairwise_beta_gaps(values: list[float]) -> tuple[float, float]:
    max_abs_gap = 0.0
    max_rel_gap = 0.0
    for i, left in enumerate(values):
        for right in values[i + 1 :]:
            abs_gap = abs(left - right)
            scale = max(abs(left), abs(right), _BETA_STABILITY_NEAR_ZERO)
            rel_gap = abs_gap / scale
            max_abs_gap = max(max_abs_gap, abs_gap)
            max_rel_gap = max(max_rel_gap, rel_gap)
    return max_abs_gap, max_rel_gap


def _classify_beta_stability(values: list[float]) -> tuple[str, str | None]:
    """Classify 3Y/5Y/10Y point betas: stable | moderately_changed | unstable | unavailable."""
    if len(values) < 2:
        return "unavailable", "insufficient_beta_windows"

    material = [v for v in values if abs(v) > _BETA_STABILITY_NEAR_ZERO]
    signs = {_beta_sign(v) for v in material}
    nonzero_signs = {s for s in signs if s != 0}
    if len(nonzero_signs) > 1:
        return "unstable", None

    max_abs_gap, max_rel_gap = _pairwise_beta_gaps(values)
    if max_abs_gap >= _BETA_STABILITY_UNSTABLE_ABS_GAP or max_rel_gap >= _BETA_STABILITY_UNSTABLE_REL_GAP:
        return "unstable", None
    if max_abs_gap >= _BETA_STABILITY_MODERATE_ABS_GAP or max_rel_gap >= _BETA_STABILITY_MODERATE_REL_GAP:
        return "moderately_changed", None
    return "stable", None


def _factor_beta_stability(
    *,
    betas_3y: dict[str, float | None],
    betas_5y: dict[str, float | None],
    betas_10y: dict[str, float | None],
) -> dict[str, dict[str, Any]]:
    """Per-beta stability across point-in-time 3Y/5Y/10Y OLS betas (not rolling summaries)."""
    out: dict[str, dict[str, Any]] = {}
    for beta_key in PRODUCTION_BETA_KEYS:
        window_values = [
            _as_float(betas_3y.get(beta_key)),
            _as_float(betas_5y.get(beta_key)),
            _as_float(betas_10y.get(beta_key)),
        ]
        available = [v for v in window_values if v is not None]
        label, unavailable_reason = _classify_beta_stability(available)
        out[beta_key] = {
            "beta_stability_label": label,
            "unavailable_reason": unavailable_reason,
            "windows_available": len(available),
        }
    return out


def _legacy_significance_confidence(signal_by_beta: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Backward-compatible map for Block 2.4 (status alias only; no raw inference stats)."""
    legacy: dict[str, Any] = {}
    for beta_key, row in signal_by_beta.items():
        legacy[beta_key] = {
            "status": row.get("signal_confidence"),
            "confidence_reason": row.get("confidence_reason"),
        }
    return legacy


def _product_factor_name(value: Any, beta_key: str | None = None) -> str | None:
    if beta_key and beta_key in BETA_TO_PRODUCT_FACTOR:
        return BETA_TO_PRODUCT_FACTOR[beta_key]
    raw = str(value or "").strip()
    return _INTERNAL_FACTOR_TO_PRODUCT.get(raw)


def _decomp_rows_by_beta(decomp: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = decomp.get("rows") if isinstance(decomp, dict) else []
    out: dict[str, dict[str, Any]] = {}
    if not isinstance(rows, list):
        return out
    for row in rows:
        if not isinstance(row, dict):
            continue
        beta_key = row.get("beta_key")
        if beta_key is None:
            continue
        beta_str = str(beta_key)
        if beta_str in PRODUCTION_BETA_KEYS:
            out[beta_str] = row
    return out


def _factor_variance_contribution(stress_report: dict[str, Any]) -> dict[str, Any]:
    decomp = stress_report.get("factor_variance_decomposition")
    if not isinstance(decomp, dict):
        return {
            "status": "unavailable",
            "method": "stress_report.factor_variance_decomposition",
            "r_squared": None,
            "contributions": {factor: None for factor in PRODUCTION_FACTOR_UNIVERSE},
            "reason": "factor_variance_decomposition_missing",
            "method_notes": [
                "Block 2.3 does not calculate variance contribution; missing decomposition must be fixed upstream."
            ],
        }
    rows_by_beta = _decomp_rows_by_beta(decomp)
    raw: dict[str, float | None] = {}
    for beta_key in PRODUCTION_BETA_KEYS:
        row = rows_by_beta.get(beta_key) or {}
        value = _as_float(row.get("gross_total_variance_share"))
        if value is None:
            value = _as_float(row.get("net_total_variance_share"))
            value = abs(value) if value is not None else None
        raw[BETA_TO_PRODUCT_FACTOR[beta_key]] = value
    numeric = {k: v for k, v in raw.items() if v is not None}
    denom = sum(abs(v) for v in numeric.values())
    if decomp.get("status") != "available" or not numeric or denom <= 0.0:
        return {
            "status": "unavailable",
            "method": str(decomp.get("method") or "stress_report.factor_variance_decomposition"),
            "r_squared": _round(decomp.get("r2")),
            "contributions": {factor: None for factor in PRODUCTION_FACTOR_UNIVERSE},
            "reason": decomp.get("reason") or "factor_variance_decomposition_unavailable",
            "method_notes": [
                "Variance contribution is unavailable in stress_report; Block 2.3 does not recompute it."
            ],
        }
    contributions = {
        factor: (_round(abs(value) / denom) if value is not None else None)
        for factor, value in raw.items()
    }
    return {
        "status": "available",
        "method": str(decomp.get("method") or "stress_report.factor_variance_decomposition"),
        "r_squared": _round(decomp.get("r2")),
        "contributions": contributions,
        "raw_contributions": {factor: _round(value) for factor, value in raw.items()},
        "reason": None,
        "method_notes": [
            "Contributions are adapted from stress_report.factor_variance_decomposition, using gross total variance share when available.",
            "Values are normalized across production factors for product ranking; residual risk is not included in this normalized factor list.",
        ],
    }


def _confidence_weight(status: str) -> float:
    if status == "significant":
        return 1.0
    if status == "weak_evidence":
        return 0.65
    if status == "unstable_low_confidence":
        return 0.35
    return 0.0


def _risk_ranking(
    *,
    betas_5y: dict[str, float | None],
    confidence: dict[str, Any],
    variance_contribution: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    contribs = variance_contribution.get("contributions") if isinstance(variance_contribution, dict) else {}
    use_contrib = variance_contribution.get("status") == "available" and isinstance(contribs, dict)
    for beta_key in PRODUCTION_BETA_KEYS:
        factor = BETA_TO_PRODUCT_FACTOR[beta_key]
        conf_row = confidence.get(beta_key) if isinstance(confidence.get(beta_key), dict) else {}
        conf_status = str(
            conf_row.get("signal_confidence") or conf_row.get("status") or "unavailable"
        )
        contribution = _as_float(contribs.get(factor)) if use_contrib else None
        beta = betas_5y.get(beta_key)
        score = contribution if contribution is not None else (abs(beta or 0.0) * _confidence_weight(conf_status))
        if score is None or score <= 0.0:
            continue
        rows.append(
            {
                "factor": factor,
                "beta_name": beta_key,
                "beta": beta,
                "contribution": _round(contribution),
                "confidence": conf_status if conf_status != "unavailable" else "unstable_low_confidence",
                "_score": float(score),
            }
        )
    rows.sort(key=lambda row: (-float(row["_score"]), str(row["factor"])))
    out: list[dict[str, Any]] = []
    for idx, row in enumerate(rows[:3], start=1):
        factor = row.pop("factor")
        score = row.pop("_score")
        out.append(
            {
                "rank": idx,
                "factor": factor,
                **row,
                "ranking_metric": "variance_contribution" if row.get("contribution") is not None else "absolute_beta_adjusted_by_confidence",
                "ranking_score": _round(score),
                "interpretation": _PRODUCT_FACTOR_INTERPRETATIONS.get(factor, "This factor may influence portfolio behavior."),
            }
        )
    return out


def _normalize_kalman_uncertainty_label(raw: Any) -> str | None:
    if raw is None:
        return None
    label = str(raw).strip().lower()
    if label in _KALMAN_UNCERTAINTY_LABELS:
        return label
    return None


def _kalman_block_unavailable_reason(stress_report: dict[str, Any], kalman_block: dict[str, Any]) -> str:
    if kalman_block.get("available"):
        return ""
    reason = str(kalman_block.get("reason") or "").strip()
    if reason:
        return reason
    kalman_error = str(stress_report.get("factor_betas_kalman_error") or "").strip()
    if kalman_error:
        return "kalman_computation_failed"
    skip_reason = str(stress_report.get("factor_betas_kalman_skip_reason") or "").strip()
    if skip_reason:
        return "kalman_skipped_by_profile"
    if not isinstance(stress_report.get("factor_betas_kalman"), dict):
        return "kalman_not_in_stress_report"
    return "kalman_unavailable"


def _kalman_factor_uncertainty(
    stress_report: dict[str, Any],
    *,
    kalman_block: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Per-beta Kalman uncertainty adapter (not OLS/HAC signal_confidence)."""
    kalman_raw = stress_report.get("factor_betas_kalman")
    uncertainty_by_beta: dict[str, str] = {}
    if isinstance(kalman_raw, dict):
        raw_unc = kalman_raw.get("uncertainty_by_beta")
        if isinstance(raw_unc, dict):
            uncertainty_by_beta = {str(k): str(v).strip().lower() for k, v in raw_unc.items()}

    kalman_betas = kalman_block.get("betas") if isinstance(kalman_block.get("betas"), dict) else {}
    block_available = bool(kalman_block.get("available"))
    block_reason = _kalman_block_unavailable_reason(stress_report, kalman_block)

    out: dict[str, dict[str, Any]] = {}
    for beta_key in PRODUCTION_BETA_KEYS:
        if not block_available:
            out[beta_key] = {
                "kalman_uncertainty_label": "unavailable",
                "kalman_note": _KALMAN_UNCERTAINTY_NOTES["unavailable"],
                "unavailable_reason": block_reason,
            }
            continue

        upstream_label = _normalize_kalman_uncertainty_label(uncertainty_by_beta.get(beta_key))
        beta_value = kalman_betas.get(beta_key) if isinstance(kalman_betas, dict) else None

        if upstream_label is not None:
            out[beta_key] = {
                "kalman_uncertainty_label": upstream_label,
                "kalman_note": _KALMAN_UNCERTAINTY_NOTES[upstream_label],
                "unavailable_reason": None,
            }
            continue

        if beta_value is None:
            out[beta_key] = {
                "kalman_uncertainty_label": "unavailable",
                "kalman_note": _KALMAN_UNCERTAINTY_NOTES["unavailable"],
                "unavailable_reason": "kalman_beta_missing_for_factor",
            }
            continue

        raw_unc = uncertainty_by_beta.get(beta_key)
        if raw_unc is not None and str(raw_unc).strip().lower() == "unknown":
            unavailable_reason = "kalman_uncertainty_unknown"
        else:
            unavailable_reason = "kalman_uncertainty_missing"

        out[beta_key] = {
            "kalman_uncertainty_label": "unavailable",
            "kalman_note": _KALMAN_UNCERTAINTY_NOTES["unavailable"],
            "unavailable_reason": unavailable_reason,
        }
    return out


def _kalman_current_beta(stress_report: dict[str, Any]) -> dict[str, Any]:
    kalman = stress_report.get("factor_betas_kalman")
    if not isinstance(kalman, dict):
        kalman_error = str(stress_report.get("factor_betas_kalman_error") or "").strip()
        skip_reason = str(stress_report.get("factor_betas_kalman_skip_reason") or "").strip()
        if skip_reason:
            reason = "kalman_skipped_by_profile"
            notes = [f"Kalman skipped: {skip_reason}."]
        elif kalman_error:
            reason = "kalman_computation_failed"
            notes = [f"Kalman computation failed upstream: {kalman_error}"]
        else:
            reason = "kalman_not_in_stress_report"
            notes = ["Kalman beta diagnostics are missing from stress_report; Block 2.3 does not calculate them."]
        return {
            "available": False,
            "reason": reason,
            "betas": {key: None for key in PRODUCTION_BETA_KEYS},
            "method": "kalman_dynamic_beta",
            "notes": notes,
        }
    raw = kalman.get("latest")
    if not isinstance(raw, dict) or not raw:
        raw = kalman.get("latest_betas_capped") if isinstance(kalman.get("latest_betas_capped"), dict) else kalman.get("latest_betas")
    available = kalman.get("status") == "available" and isinstance(raw, dict) and bool(raw)
    notes = []
    if not available:
        diagnostics = kalman.get("diagnostics") if isinstance(kalman.get("diagnostics"), dict) else {}
        warning_codes = diagnostics.get("warning_codes") if isinstance(diagnostics, dict) else []
        if warning_codes:
            notes.append("Kalman unavailable warning codes: " + ", ".join(str(x) for x in warning_codes))
        else:
            notes.append("Kalman beta diagnostics are unavailable in stress_report.")
    return {
        "available": bool(available),
        "reason": None if available else kalman.get("reason") or kalman.get("status") or "kalman_unavailable",
        "betas": _beta_map(raw if isinstance(raw, dict) else {}),
        "method": str(kalman.get("method") or "kalman_dynamic_beta"),
        "latest_date": kalman.get("latest_date"),
        "notes": notes,
    }


def _display_factor_name(factor: str) -> str:
    if factor == "USD":
        return "USD"
    if factor == "VIX_volatility":
        return "VIX volatility"
    return str(factor).replace("_", " ")


def _signal_confidence_phrase(signal_confidence: str) -> str:
    if signal_confidence == "significant":
        return "the factor signal is statistically significant"
    if signal_confidence == "weak_evidence":
        return "exposure is visible but the factor signal is statistically weak"
    if signal_confidence == "unstable_low_confidence":
        return "the factor signal has low statistical confidence"
    return "the factor beta is unavailable for this window"


def _beta_stability_phrase(beta_stability_label: str) -> str | None:
    if beta_stability_label == "stable":
        return "beta is stable across 3Y/5Y/10Y windows"
    if beta_stability_label == "moderately_changed":
        return "beta moves materially across 3Y/5Y/10Y windows"
    if beta_stability_label == "unstable":
        return "beta is unstable across 3Y/5Y/10Y windows"
    return None


def _kalman_alignment_label(
    *,
    beta_key: str,
    kalman_block: dict[str, Any],
    betas_5y: dict[str, float | None],
    betas_10y: dict[str, float | None],
) -> str:
    if not kalman_block.get("available"):
        return "kalman_unavailable"
    kalman_betas = kalman_block.get("betas") if isinstance(kalman_block.get("betas"), dict) else {}
    kalman_value = _as_float(kalman_betas.get(beta_key))
    if kalman_value is None:
        return "kalman_unavailable"
    benchmarks = [_as_float(betas_5y.get(beta_key)), _as_float(betas_10y.get(beta_key))]
    benchmarks = [v for v in benchmarks if v is not None]
    if not benchmarks:
        return "long_window_unavailable"
    for benchmark in benchmarks:
        gap = abs(kalman_value - benchmark)
        rel_gap = gap / max(abs(benchmark), _KALMAN_ALIGN_MIN_DENOM)
        sign_diff = (kalman_value * benchmark) < 0.0 and abs(kalman_value) > _BETA_STABILITY_NEAR_ZERO and abs(benchmark) > _BETA_STABILITY_NEAR_ZERO
        if sign_diff or gap >= _KALMAN_ALIGN_ABS_GAP or rel_gap >= _KALMAN_ALIGN_REL_GAP:
            return "differs_from_5y_10y"
    return "aligned_with_5y_10y"


def _kalman_alignment_phrase(alignment: str, *, uncertainty_label: str) -> str | None:
    if alignment == "aligned_with_5y_10y":
        if uncertainty_label in {"moderate", "high"}:
            return "current Kalman beta is broadly in line with the 5Y/10Y baseline, but Kalman uncertainty is elevated"
        return "current Kalman beta is broadly in line with the 5Y/10Y baseline"
    if alignment == "differs_from_5y_10y":
        if uncertainty_label in {"moderate", "high"}:
            return "current Kalman beta differs from the 5Y/10Y baseline and Kalman uncertainty is elevated"
        return "current Kalman beta differs from the 5Y/10Y baseline"
    return None


def _factor_highlight_row(
    *,
    factor: str,
    beta_key: str,
    signal_confidence: dict[str, dict[str, Any]],
    beta_stability: dict[str, dict[str, Any]],
    kalman_uncertainty: dict[str, dict[str, Any]],
    kalman_block: dict[str, Any],
    betas_5y: dict[str, float | None],
    betas_10y: dict[str, float | None],
) -> dict[str, Any]:
    signal_row = signal_confidence.get(beta_key) if isinstance(signal_confidence.get(beta_key), dict) else {}
    stability_row = beta_stability.get(beta_key) if isinstance(beta_stability.get(beta_key), dict) else {}
    kalman_row = kalman_uncertainty.get(beta_key) if isinstance(kalman_uncertainty.get(beta_key), dict) else {}
    signal_status = str(signal_row.get("signal_confidence") or "unavailable")
    stability_label = str(stability_row.get("beta_stability_label") or "unavailable")
    uncertainty_label = str(kalman_row.get("kalman_uncertainty_label") or "unavailable")
    alignment = _kalman_alignment_label(
        beta_key=beta_key,
        kalman_block=kalman_block,
        betas_5y=betas_5y,
        betas_10y=betas_10y,
    )
    return {
        "factor": factor,
        "beta_name": beta_key,
        "signal_confidence": signal_status,
        "beta_stability_label": stability_label,
        "kalman_uncertainty_label": uncertainty_label,
        "kalman_alignment": alignment,
    }


def _factor_highlight_sentence(highlight: dict[str, Any]) -> str:
    factor_label = _display_factor_name(str(highlight.get("factor") or ""))
    parts = [_signal_confidence_phrase(str(highlight.get("signal_confidence") or "unavailable"))]
    stability_phrase = _beta_stability_phrase(str(highlight.get("beta_stability_label") or "unavailable"))
    if stability_phrase:
        parts.append(stability_phrase)
    kalman_phrase = _kalman_alignment_phrase(
        str(highlight.get("kalman_alignment") or "kalman_unavailable"),
        uncertainty_label=str(highlight.get("kalman_uncertainty_label") or "unavailable"),
    )
    if kalman_phrase:
        parts.append(kalman_phrase)
    return f"{factor_label.capitalize()}: " + "; ".join(parts) + "."


def _main_caveat_from_highlights(highlights: list[dict[str, Any]]) -> str | None:
    caveats: list[str] = []
    for row in highlights:
        factor_label = _display_factor_name(str(row.get("factor") or ""))
        uncertainty = str(row.get("kalman_uncertainty_label") or "unavailable")
        if uncertainty == "high":
            caveats.append(f"Kalman uncertainty is high for {factor_label}")
        signal = str(row.get("signal_confidence") or "unavailable")
        if signal in {"weak_evidence", "unstable_low_confidence"}:
            caveats.append(f"the {factor_label} factor signal is not statistically strong")
        stability = str(row.get("beta_stability_label") or "unavailable")
        if stability == "unstable":
            caveats.append(f"{factor_label} beta is unstable across 3Y/5Y/10Y windows")
        alignment = str(row.get("kalman_alignment") or "")
        if alignment == "differs_from_5y_10y" and uncertainty == "moderate":
            caveats.append(f"current Kalman beta for {factor_label} differs from longer windows with only moderate reliability")
    if not caveats:
        return None
    # Prefer the first distinct caveat; cap length for product surface.
    return "Main caveat: " + caveats[0] + "."


def _factor_exposure_summary(
    *,
    ranking: list[dict[str, Any]],
    status: str,
    signal_confidence: dict[str, dict[str, Any]],
    beta_stability: dict[str, dict[str, Any]],
    kalman_uncertainty: dict[str, dict[str, Any]],
    kalman_block: dict[str, Any],
    betas_5y: dict[str, float | None],
    betas_10y: dict[str, float | None],
) -> dict[str, Any]:
    top = [row["factor"] for row in ranking[:3]]
    dominant = top[0] if top else None
    diagnostic = (
        "This is a diagnostic read from existing factor evidence. It indicates sensitivity, "
        "not a recommendation; related shocks should be checked separately in Stress Lab."
    )

    if status == "unavailable" or not top:
        if status == "unavailable":
            client_summary = (
                "Factor exposure diagnostics are unavailable because required stress_report factor evidence is missing."
            )
            diagnostic = "Fix missing factor diagnostics upstream before interpreting market-factor drivers."
        else:
            client_summary = (
                "Factor exposure diagnostics are limited; no dominant factor can be identified with the available evidence."
            )
            diagnostic = "Use this block as a data-quality signal and review upstream stress_report factor diagnostics."
        return {
            "dominant_factor": dominant,
            "top_3_factors": top,
            "factor_highlights": [],
            "main_caveat": None,
            "client_summary": client_summary,
            "diagnostic_interpretation": diagnostic,
        }

    highlights: list[dict[str, Any]] = []
    for row in ranking[:3]:
        factor = str(row.get("factor") or "")
        beta_key = str(row.get("beta_name") or PRODUCT_FACTOR_TO_BETA.get(factor, ""))
        if not beta_key:
            continue
        highlights.append(
            _factor_highlight_row(
                factor=factor,
                beta_key=beta_key,
                signal_confidence=signal_confidence,
                beta_stability=beta_stability,
                kalman_uncertainty=kalman_uncertainty,
                kalman_block=kalman_block,
                betas_5y=betas_5y,
                betas_10y=betas_10y,
            )
        )

    display_top = [_display_factor_name(f) for f in top]
    if len(display_top) == 1:
        driver_phrase = display_top[0]
    elif len(display_top) == 2:
        driver_phrase = f"{display_top[0]} and {display_top[1]}"
    else:
        driver_phrase = f"{display_top[0]}, {display_top[1]}, and {display_top[2]}"

    sentences = [f"The portfolio appears most driven by {driver_phrase} exposure."]
    sentences.extend(_factor_highlight_sentence(row) for row in highlights)
    main_caveat = _main_caveat_from_highlights(highlights)
    if main_caveat:
        sentences.append(main_caveat)

    client_summary = " ".join(sentences)
    return {
        "dominant_factor": dominant,
        "top_3_factors": top,
        "factor_highlights": highlights,
        "main_caveat": main_caveat,
        "client_summary": client_summary,
        "diagnostic_interpretation": diagnostic,
    }


def _setup_context(analysis_setup: dict[str, Any] | None) -> tuple[str, str, str]:
    if not isinstance(analysis_setup, dict):
        return "unknown", "unknown", "unknown"
    portfolio_input = analysis_setup.get("portfolio_input") if isinstance(analysis_setup.get("portfolio_input"), dict) else {}
    subject = analysis_setup.get("analysis_subject") if isinstance(analysis_setup.get("analysis_subject"), dict) else {}
    return (
        str(subject.get("type") or portfolio_input.get("analysis_subject_type") or "unknown"),
        str(portfolio_input.get("source_analysis_mode") or analysis_setup.get("analysis_mode") or "unknown"),
        str(portfolio_input.get("investor_currency") or "unknown"),
    )


def _n_obs(stress_report: dict[str, Any], key: str) -> int | None:
    reg = stress_report.get(key)
    if isinstance(reg, dict) and reg.get("n_obs") is not None:
        try:
            return int(reg.get("n_obs"))
        except (TypeError, ValueError):
            return None
    return None


def _naming_warnings(stress_report: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    for field in ("factor_betas_3y", "factor_betas_5y", "factor_betas_10y", "factor_betas"):
        raw = stress_report.get(field)
        if not isinstance(raw, dict):
            continue
        extra = _extra_beta_keys(raw)
        if extra:
            warnings.append(f"{field} contains non-production beta keys: {', '.join(extra)}.")
        missing = [key for key in PRODUCTION_BETA_KEYS if key not in _present_beta_keys(raw)]
        if missing and field in {"factor_betas_3y", "factor_betas_5y", "factor_betas_10y"}:
            warnings.append(f"{field} is missing production beta keys: {', '.join(missing)}.")
    decomp = stress_report.get("factor_variance_decomposition")
    rows = decomp.get("rows") if isinstance(decomp, dict) else []
    if isinstance(rows, list):
        normalized: list[str] = []
        unknown: list[str] = []
        for row in rows:
            if not isinstance(row, dict) or row.get("beta_key") is None:
                continue
            beta_key = str(row.get("beta_key"))
            factor_raw = row.get("factor")
            product = _product_factor_name(factor_raw, beta_key=beta_key)
            if product is None:
                unknown.append(str(factor_raw))
            elif str(factor_raw) != product:
                normalized.append(f"{factor_raw}->{product}")
        if normalized:
            warnings.append("factor_variance_decomposition factor names normalized for product contract: " + ", ".join(sorted(set(normalized))) + ".")
        if unknown:
            warnings.append("factor_variance_decomposition contains unknown factor names: " + ", ".join(sorted(set(unknown))) + ".")
    meta = stress_report.get("factor_diagnostics_meta")
    if isinstance(meta, dict):
        meta_keys = [str(k) for k in meta.get("factor_beta_keys") or []]
        extra_meta = sorted(k for k in meta_keys if k not in PRODUCTION_BETA_KEYS)
        if extra_meta:
            warnings.append("factor_diagnostics_meta.factor_beta_keys contains non-production beta keys: " + ", ".join(extra_meta) + ".")
    return warnings


def build_block_2_3_factor_exposure(
    *,
    stress_report: dict[str, Any] | None,
    analysis_setup: dict[str, Any] | None = None,
    weights: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build Block 2.3 from existing ``stress_report`` factor diagnostics only."""
    subject_type, analysis_mode, investor_currency = _setup_context(analysis_setup)
    stress = stress_report if isinstance(stress_report, dict) else {}
    data_quality_warnings: list[str] = []
    informational_disclosures: list[str] = []
    if not isinstance(stress_report, dict):
        data_quality_warnings.append("stress_report is missing; Block 2.3 cannot calculate factor diagnostics.")

    raw_3y = stress.get("factor_betas_3y")
    raw_5y = stress.get("factor_betas_5y")
    raw_10y = stress.get("factor_betas_10y")
    if not isinstance(raw_3y, dict):
        data_quality_warnings.append(FACTOR_BETAS_3Y_UNAVAILABLE_REASON)
    if not isinstance(raw_5y, dict) and isinstance(stress.get("factor_betas"), dict):
        raw_5y = stress.get("factor_betas")
        data_quality_warnings.append("factor_betas_5y missing; legacy factor_betas used only as existing stress_report evidence.")
    if not isinstance(stress.get("factor_betas_5y"), dict):
        data_quality_warnings.append("factor_betas_5y missing; fix upstream stress_report factor diagnostics.")
    if not isinstance(raw_10y, dict):
        data_quality_warnings.append("factor_betas_10y missing; 10Y factor exposure is unavailable until fixed upstream.")

    data_quality_warnings.extend(_naming_warnings(stress))

    weight_map = resolved_analysis_weights(analysis_setup, weights=weights)
    real_cash_labels = collect_real_cash_tickers(weights=weight_map)
    if real_cash_labels:
        informational_disclosures.append(
            "Cash holdings are treated as real cash positions with zero return/volatility and no price download; this is an expected input policy, not missing data."
        )

    betas_3y = _beta_map(raw_3y)
    betas_5y = _beta_map(raw_5y)
    betas_10y = _beta_map(raw_10y)
    beta_stability = _factor_beta_stability(betas_3y=betas_3y, betas_5y=betas_5y, betas_10y=betas_10y)
    signal_confidence = _factor_signal_confidence(
        stress,
        betas_3y=betas_3y,
        betas_5y=betas_5y,
        betas_10y=betas_10y,
    )
    variance_contribution = _factor_variance_contribution(stress)
    if variance_contribution.get("status") != "available":
        reason = variance_contribution.get("reason") or "unknown"
        data_quality_warnings.append(f"Factor variance contribution unavailable: {reason}.")
    kalman = _kalman_current_beta(stress)
    kalman_uncertainty = _kalman_factor_uncertainty(stress, kalman_block=kalman)
    if not kalman.get("available"):
        informational_disclosures.append(
            f"Kalman current beta unavailable (optional diagnostic): {kalman.get('reason')}."
        )

    ranking = _risk_ranking(
        betas_5y=betas_5y,
        confidence=signal_confidence,
        variance_contribution=variance_contribution,
    )

    has_any_evidence = any(
        [
            _present_beta_keys(raw_3y),
            _present_beta_keys(raw_5y),
            _present_beta_keys(raw_10y),
            isinstance(stress.get("factor_regression_5y"), dict) and bool(stress.get("factor_regression_5y")),
            isinstance(stress.get("factor_regression_10y"), dict) and bool(stress.get("factor_regression_10y")),
            variance_contribution.get("status") == "available",
            kalman.get("available"),
        ]
    )
    if not has_any_evidence:
        status = "unavailable"
    elif _window_status(raw_5y) == "available" and _window_status(raw_10y) == "available":
        status = "available" if variance_contribution.get("status") == "available" else "partial"
    else:
        status = "partial"

    factor_meta = stress.get("factor_diagnostics_meta") if isinstance(stress.get("factor_diagnostics_meta"), dict) else {}
    meta = {
        "min_observations_required": 30,
        "observations_used_5y": _n_obs(stress, "factor_regression_5y") or factor_meta.get("aligned_weekly_observations"),
        "observations_used_10y": _n_obs(stress, "factor_regression_10y"),
        "missing_factor_data": list(factor_meta.get("missing_factors") or []),
        "missing_portfolio_return_data": not has_any_evidence,
        "cash_handling": "real_cash_has_zero_return_and_no_price_series",
        "frequency": "weekly",
        "method_notes": [
            "Block 2.3 adapts existing stress_report factor diagnostics and does not trigger calculations.",
            "Missing factor diagnostics must be fixed upstream in stress_report generation or src/stress_factors.py.",
            "Block 2.3 is separate from Stress Lab: it reports sensitivity, not shocked outcomes.",
            "signal_confidence reflects OLS/HAC weekly regression evidence only; Kalman uncertainty is reported separately in factor_kalman_uncertainty.",
            "factor_kalman_uncertainty reads stress_report.factor_betas_kalman.uncertainty_by_beta only; Block 2.3 does not compute Kalman posteriors.",
            "factor_beta_stability compares point-in-time factor_betas_3y/5y/10y only; rolling summaries are not used.",
            "Full regression diagnostics (SE, CI, VIF, residual tests) remain in stress_report.json only.",
        ],
        "observations_used_3y": _n_obs(stress, "factor_regression_3y"),
        "source_fields": [
            "stress_report.factor_betas_3y",
            "stress_report.factor_betas_5y",
            "stress_report.factor_betas_10y",
            "stress_report.factor_regression_3y",
            "stress_report.factor_regression_5y",
            "stress_report.factor_regression_10y",
            "stress_report.factor_betas_kalman",
            "stress_report.factor_variance_decomposition",
            "stress_report.factor_diagnostics_meta",
        ],
    }

    factor_betas_3y_block = _window_block(
        raw_3y,
        window_months=FACTOR_BETAS_3Y_WINDOW_MONTHS,
        observations_used=_n_obs(stress, "factor_regression_3y"),
    )
    if factor_betas_3y_block.get("status") == "unavailable":
        factor_betas_3y_block["unavailable_reason"] = FACTOR_BETAS_3Y_UNAVAILABLE_REASON

    return {
        "block": BLOCK_2_3_ID,
        "block_id": "2.3",
        "block_name": BLOCK_2_3_NAME,
        "analysis_subject": subject_type,
        "analysis_mode": analysis_mode,
        "investor_currency": investor_currency,
        "status": status,
        "factor_universe": list(PRODUCTION_FACTOR_UNIVERSE),
        "factor_beta_snapshot": betas_5y,
        "factor_betas_3y": factor_betas_3y_block,
        "factor_betas_5y": _window_block(raw_5y, window_months=60, observations_used=_n_obs(stress, "factor_regression_5y")),
        "factor_betas_10y": _window_block(raw_10y, window_months=120, observations_used=_n_obs(stress, "factor_regression_10y")),
        "kalman_current_beta": kalman,
        "factor_kalman_uncertainty": kalman_uncertainty,
        "factor_beta_stability": beta_stability,
        "factor_signal_confidence": signal_confidence,
        "factor_significance_confidence": _legacy_significance_confidence(signal_confidence),
        "factor_variance_contribution": variance_contribution,
        "factor_risk_ranking": ranking,
        "factor_exposure_summary": _factor_exposure_summary(
            ranking=ranking,
            status=status,
            signal_confidence=signal_confidence,
            beta_stability=beta_stability,
            kalman_uncertainty=kalman_uncertainty,
            kalman_block=kalman,
            betas_5y=betas_5y,
            betas_10y=betas_10y,
        ),
        "data_quality_warnings": list(dict.fromkeys(data_quality_warnings)),
        "informational_disclosures": list(dict.fromkeys(informational_disclosures)),
        "factor_diagnostics_meta": meta,
        "naming_validation": {
            "expected_factor_universe": list(PRODUCTION_FACTOR_UNIVERSE),
            "expected_beta_keys": list(PRODUCTION_BETA_KEYS),
            "status": "passed" if not _naming_warnings(stress) else "warnings",
            "warnings": _naming_warnings(stress),
        },
        "stress_lab_separation": {
            "block_2_3_answers": "What factors is the portfolio sensitive to...",
            "stress_lab_answers": "What happens if those factors receive a stress shock...",
            "no_scenario_shocks_in_this_block": True,
            "no_rebalance_recommendations": True,
        },
    }


__all__ = [
    "BLOCK_2_3_ID",
    "FACTOR_BETAS_3Y_UNAVAILABLE_REASON",
    "FACTOR_BETAS_3Y_WINDOW_MONTHS",
    "PRODUCTION_BETA_KEYS",
    "PRODUCTION_FACTOR_UNIVERSE",
    "build_block_2_3_factor_exposure",
]
