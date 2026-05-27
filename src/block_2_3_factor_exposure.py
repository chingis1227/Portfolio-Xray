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


def _confidence_comment(status: str, beta_key: str) -> str:
    factor = BETA_TO_PRODUCT_FACTOR.get(beta_key, beta_key)
    if status == "significant":
        return f"{factor} sensitivity has stronger statistical evidence in the available weekly regression."
    if status == "weak_evidence":
        return f"{factor} sensitivity is present but evidence is marginal; interpret as diagnostic, not as an action signal."
    if status == "unstable_low_confidence":
        return f"{factor} sensitivity has low or unstable evidence in the available data."
    return f"{factor} sensitivity is unavailable because the required regression evidence is missing."


def _factor_confidence(stress_report: dict[str, Any], betas_5y: dict[str, float | None]) -> dict[str, Any]:
    reg = stress_report.get("factor_regression_5y")
    if not isinstance(reg, dict) or not reg:
        reg = stress_report.get("factor_regression_10y") if isinstance(stress_report.get("factor_regression_10y"), dict) else {}
    n_obs = None
    if isinstance(reg, dict) and reg.get("n_obs") is not None:
        try:
            n_obs = int(reg.get("n_obs"))
        except (TypeError, ValueError):
            n_obs = None
    r_squared = _as_float(reg.get("r2")) if isinstance(reg, dict) else None
    out: dict[str, Any] = {}
    for beta_key in PRODUCTION_BETA_KEYS:
        beta_value = betas_5y.get(beta_key)
        hac_t = _hac_value(reg, beta_key, "t") if isinstance(reg, dict) else None
        hac_p = _hac_value(reg, beta_key, "p") if isinstance(reg, dict) else None
        ols_t = _ols_value(reg, beta_key, "t") if isinstance(reg, dict) else None
        ols_p = _ols_value(reg, beta_key, "p") if isinstance(reg, dict) else None
        t_stat = hac_t if hac_t is not None else ols_t
        p_value = hac_p if hac_p is not None else ols_p
        status = _confidence_status(
            beta_value=beta_value,
            t_stat=t_stat,
            p_value=p_value,
            n_obs=n_obs,
            r_squared=r_squared,
        )
        out[beta_key] = {
            "status": status,
            "t_stat": _round(t_stat),
            "p_value": _round(p_value),
            "hac_used": hac_t is not None or hac_p is not None,
            "comment": _confidence_comment(status, beta_key),
        }
    return out


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
        conf_status = str((confidence.get(beta_key) or {}).get("status") or "unavailable")
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


def _kalman_current_beta(stress_report: dict[str, Any]) -> dict[str, Any]:
    kalman = stress_report.get("factor_betas_kalman")
    if not isinstance(kalman, dict):
        return {
            "available": False,
            "reason": "kalman_module_not_available",
            "betas": {key: None for key in PRODUCTION_BETA_KEYS},
            "method": "kalman_dynamic_beta",
            "notes": ["Kalman beta diagnostics are missing from stress_report; Block 2.3 does not calculate them."],
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


def _summary(ranking: list[dict[str, Any]], status: str) -> dict[str, Any]:
    top = [row["factor"] for row in ranking[:3]]
    dominant = top[0] if top else None
    if dominant:
        client_summary = (
            f"The strongest available factor signal is {dominant}. "
            f"{_PRODUCT_FACTOR_INTERPRETATIONS.get(dominant, 'This factor may influence portfolio behavior.')}"
        )
        diagnostic = (
            "This is a diagnostic read from existing factor evidence. It indicates sensitivity, "
            "not a recommendation; related shocks should be checked separately in Stress Lab."
        )
    elif status == "unavailable":
        client_summary = "Factor exposure diagnostics are unavailable because required stress_report factor evidence is missing."
        diagnostic = "Fix missing factor diagnostics upstream before interpreting market-factor drivers."
    else:
        client_summary = "Factor exposure diagnostics are limited; no dominant factor can be identified with the available evidence."
        diagnostic = "Use this block as a data-quality signal and review upstream stress_report factor diagnostics."
    return {
        "dominant_factor": dominant,
        "top_3_factors": top,
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
    for field in ("factor_betas_5y", "factor_betas_10y", "factor_betas"):
        raw = stress_report.get(field)
        if not isinstance(raw, dict):
            continue
        extra = _extra_beta_keys(raw)
        if extra:
            warnings.append(f"{field} contains non-production beta keys: {', '.join(extra)}.")
        missing = [key for key in PRODUCTION_BETA_KEYS if key not in _present_beta_keys(raw)]
        if missing and field in {"factor_betas_5y", "factor_betas_10y"}:
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

    raw_5y = stress.get("factor_betas_5y")
    raw_10y = stress.get("factor_betas_10y")
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

    betas_5y = _beta_map(raw_5y)
    betas_10y = _beta_map(raw_10y)
    confidence = _factor_confidence(stress, betas_5y)
    variance_contribution = _factor_variance_contribution(stress)
    if variance_contribution.get("status") != "available":
        reason = variance_contribution.get("reason") or "unknown"
        data_quality_warnings.append(f"Factor variance contribution unavailable: {reason}.")
    kalman = _kalman_current_beta(stress)
    if not kalman.get("available"):
        data_quality_warnings.append(f"Kalman current beta unavailable: {kalman.get('reason')}.")

    ranking = _risk_ranking(
        betas_5y=betas_5y,
        confidence=confidence,
        variance_contribution=variance_contribution,
    )

    has_any_evidence = any(
        [
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
        ],
        "source_fields": [
            "stress_report.factor_betas_5y",
            "stress_report.factor_betas_10y",
            "stress_report.factor_regression_5y",
            "stress_report.factor_regression_10y",
            "stress_report.factor_betas_kalman",
            "stress_report.factor_variance_decomposition",
            "stress_report.factor_diagnostics_meta",
        ],
    }

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
        "factor_betas_5y": _window_block(raw_5y, window_months=60, observations_used=_n_obs(stress, "factor_regression_5y")),
        "factor_betas_10y": _window_block(raw_10y, window_months=120, observations_used=_n_obs(stress, "factor_regression_10y")),
        "kalman_current_beta": kalman,
        "factor_significance_confidence": confidence,
        "factor_variance_contribution": variance_contribution,
        "factor_risk_ranking": ranking,
        "factor_exposure_summary": _summary(ranking, status),
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
            "block_2_3_answers": "What factors is the portfolio sensitive to?",
            "stress_lab_answers": "What happens if those factors receive a stress shock?",
            "no_scenario_shocks_in_this_block": True,
            "no_rebalance_recommendations": True,
        },
    }


__all__ = [
    "BLOCK_2_3_ID",
    "PRODUCTION_BETA_KEYS",
    "PRODUCTION_FACTOR_UNIVERSE",
    "build_block_2_3_factor_exposure",
]
