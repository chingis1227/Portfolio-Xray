"""Block 2.2 Portfolio Metrics — product-facing risk/return behavior diagnostics."""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pandas as pd

from src.analysis_setup import resolved_analysis_weights
from src.io_export import REPORT_DECIMALS
from src.real_cash import collect_real_cash_tickers

BLOCK_2_2_ID = "2.2_portfolio_metrics"

_PRIMARY_WINDOW_ORDER: tuple[tuple[str, str, int], ...] = (
    ("10y", "10Y (120M)", 120),
    ("5y", "5Y (60M)", 60),
    ("3y", "3Y (36M)", 36),
)

_WINDOW_SUFFIX_BY_MONTHS: dict[int, tuple[str, str]] = {
    120: ("10y", "10Y (120M)"),
    60: ("5y", "5Y (60M)"),
    36: ("3y", "3Y (36M)"),
}

_ADVANCED_ROLLING_KEYS = (
    "rolling_sharpe_12m",
    "rolling_sortino_36m",
    "rolling_sortino_12m",
    "rolling_beta_36m",
    "rolling_beta_12m",
    "rolling_correlation_36m",
    "rolling_correlation_12m",
)


def _as_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        out = float(value)
        if math.isnan(out):
            return None
        return out
    except (TypeError, ValueError):
        return None


def _round_metric(value: Any) -> float | None:
    number = _as_float(value)
    if number is None:
        return None
    return round(number, REPORT_DECIMALS)


def _setup_context(analysis_setup: dict[str, Any] | None) -> tuple[str, str, str]:
    if not isinstance(analysis_setup, dict):
        return "unknown", "unknown", "unknown"
    portfolio_input = analysis_setup.get("portfolio_input")
    if not isinstance(portfolio_input, dict):
        portfolio_input = {}
    subject = analysis_setup.get("analysis_subject")
    subject_type = "unknown"
    if isinstance(subject, dict) and subject.get("type"):
        subject_type = str(subject["type"])
    elif portfolio_input.get("analysis_subject_type"):
        subject_type = str(portfolio_input["analysis_subject_type"])
    analysis_mode = str(
        portfolio_input.get("source_analysis_mode")
        or analysis_setup.get("analysis_mode")
        or "unknown"
    )
    investor_currency = str(portfolio_input.get("investor_currency") or "unknown")
    return subject_type, analysis_mode, investor_currency


def _real_cash_labels(
    analysis_setup: dict[str, Any] | None, *, weight_map: dict[str, float]
) -> list[str]:
    labels = collect_real_cash_tickers(weights=weight_map)
    if not isinstance(analysis_setup, dict):
        return labels
    ap = analysis_setup.get("analysis_portfolio")
    if not isinstance(ap, dict):
        return labels
    cash_handling = ap.get("cash_handling")
    if not isinstance(cash_handling, dict):
        return labels
    holdings = cash_handling.get("real_cash_holdings")
    if not isinstance(holdings, list) or not holdings:
        return labels
    for row in holdings:
        if not isinstance(row, dict):
            continue
        ticker = str(row.get("ticker") or "").strip()
        if not ticker:
            continue
        labels = collect_real_cash_tickers(tickers=[*labels, ticker])
    return labels


def _resolve_primary_metrics(
    portfolio_windows: dict[str, dict[str, Any]] | None,
    portfolio_metrics: dict[str, Any] | None,
) -> tuple[dict[str, Any], str, str, int]:
    windows_in = portfolio_windows if isinstance(portfolio_windows, dict) else {}
    for window_key, window_label, window_months in _PRIMARY_WINDOW_ORDER:
        metrics = windows_in.get(window_key)
        if isinstance(metrics, dict) and metrics:
            return metrics, window_key, window_label, window_months
    if isinstance(portfolio_metrics, dict) and portfolio_metrics:
        wm = int(portfolio_metrics.get("window_months") or 0)
        suffix_label = _WINDOW_SUFFIX_BY_MONTHS.get(wm)
        if suffix_label:
            return portfolio_metrics, suffix_label[0], suffix_label[1], wm
        return portfolio_metrics, "10y", "10Y (120M)", wm or 120
    return {}, "10y", "10Y (120M)", 120


def _metric_quality_n_obs(metrics: dict[str, Any]) -> int | None:
    mq = metrics.get("metric_quality")
    if not isinstance(mq, dict):
        return None
    n_obs = mq.get("n_obs")
    try:
        return int(n_obs) if n_obs is not None else None
    except (TypeError, ValueError):
        return None


def _benchmark_ticker(metrics: dict[str, Any]) -> str | None:
    mq = metrics.get("metric_quality")
    if isinstance(mq, dict) and mq.get("benchmark_ticker"):
        return str(mq["benchmark_ticker"])
    return None


def _metrics_mostly_missing(metrics: dict[str, Any]) -> bool:
    keys = ("cagr", "vol_annual", "sharpe", "max_drawdown")
    present = [_as_float(metrics.get(k)) for k in keys]
    if not present:
        return True
    return all(v is None for v in present)


def _deepest_drawdown_episode(
    drawdown_structure: dict[str, Any] | None,
) -> tuple[float | None, int | None, int | None]:
    if not isinstance(drawdown_structure, dict):
        return None, None, None
    drawdowns = drawdown_structure.get("drawdowns")
    if not isinstance(drawdowns, list) or not drawdowns:
        return None, None, None
    valid = [d for d in drawdowns if isinstance(d, dict) and d.get("depth") is not None]
    if not valid:
        return None, None, None
    deepest = min(valid, key=lambda d: float(d["depth"]))
    depth = _round_metric(deepest.get("depth"))
    length = deepest.get("length_months")
    recovery = deepest.get("recovery_months")
    try:
        length_i = int(length) if length is not None else None
    except (TypeError, ValueError):
        length_i = None
    try:
        recovery_i = int(recovery) if recovery is not None else None
    except (TypeError, ValueError):
        recovery_i = None
    return depth, length_i, recovery_i


def _drawdown_summary_field(drawdown_structure: dict[str, Any] | None, key: str) -> Any:
    if not isinstance(drawdown_structure, dict):
        return None
    summary = drawdown_structure.get("summary")
    if not isinstance(summary, dict):
        return None
    return summary.get(key)


def _threshold_count(drawdown_structure: dict[str, Any] | None, threshold_label: str) -> int | None:
    if not isinstance(drawdown_structure, dict):
        return None
    by_threshold = drawdown_structure.get("by_threshold")
    if not isinstance(by_threshold, dict):
        return None
    entry = by_threshold.get(threshold_label)
    if not isinstance(entry, dict):
        return None
    count = entry.get("count")
    try:
        return int(count) if count is not None else None
    except (TypeError, ValueError):
        return None


def _tail_risk_fields(analytics: dict[str, Any]) -> tuple[dict[str, Any], bool, dict[str, Any] | None]:
    tail = analytics.get("tail_risk")
    if isinstance(tail, dict):
        values = {
            "var_95": _round_metric(tail.get("var_95")),
            "var_99": _round_metric(tail.get("var_99")),
            "es_95": _round_metric(tail.get("es_95")),
            "es_99": _round_metric(tail.get("es_99")),
        }
        explicit = tail.get("metric_available")
        has_values = any(v is not None for v in values.values())
        if explicit is False:
            return values, False, tail
        if explicit is True and has_values:
            return values, True, tail
        if has_values:
            return values, True, tail
        return values, False, tail
    flat = {
        "var_95": _round_metric(analytics.get("var_95")),
        "var_99": _round_metric(analytics.get("var_99")),
        "es_95": _round_metric(analytics.get("es_95")),
        "es_99": _round_metric(analytics.get("es_99")),
    }
    has_any = any(v is not None for v in flat.values())
    return flat, has_any, None


def _build_tail_risk_diagnostics(
    analytics: dict[str, Any],
    metrics: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    tail_values, tail_available, tail_meta = _tail_risk_fields(analytics)
    diag: dict[str, Any] = {
        **tail_values,
        "downside_deviation": _round_metric(metrics.get("downside_deviation")),
        "eee_10": _round_metric(analytics.get("eee_10pct")),
        "metric_available": tail_available,
        "method": tail_meta.get("method") if isinstance(tail_meta, dict) else None,
        "frequency": tail_meta.get("frequency") if isinstance(tail_meta, dict) else None,
        "window": tail_meta.get("window_label") if isinstance(tail_meta, dict) else None,
        "window_months": tail_meta.get("window_months") if isinstance(tail_meta, dict) else None,
        "n_obs": tail_meta.get("n_obs") if isinstance(tail_meta, dict) else None,
    }
    limitations: list[str] = []
    if isinstance(tail_meta, dict) and tail_meta.get("unavailable_reason"):
        limitations.append(str(tail_meta["unavailable_reason"]))
    if limitations:
        diag["limitations"] = limitations
    return diag, tail_available


def _rolling_panel(
    summary: dict[str, Any] | None,
    *,
    series_ref: str | None,
    latest_key: str = "last",
) -> dict[str, Any]:
    latest = None
    if isinstance(summary, dict):
        latest = _round_metric(summary.get(latest_key))
    return {
        "available": latest is not None,
        "latest": latest,
        "series_ref": series_ref,
    }


def _rolling_beta_or_correlation_panel(
    analytics: dict[str, Any],
    *,
    window_suffix: str,
) -> dict[str, Any]:
    beta_summary = analytics.get("rolling_beta_36m")
    corr_summary = analytics.get("rolling_correlation_36m")
    beta_ref = f"rolling_beta_36m_{window_suffix}.csv"
    corr_ref = f"rolling_correlation_36m_{window_suffix}.csv"
    latest_beta = None
    latest_correlation = None
    series_ref: str | None = None
    if isinstance(beta_summary, dict) and beta_summary.get("last") is not None:
        latest_beta = _round_metric(beta_summary.get("last"))
        series_ref = beta_ref
    if isinstance(corr_summary, dict) and corr_summary.get("last") is not None:
        latest_correlation = _round_metric(corr_summary.get("last"))
        if series_ref is None:
            series_ref = corr_ref
    available = latest_beta is not None or latest_correlation is not None
    return {
        "available": available,
        "latest": None,
        "latest_beta": latest_beta,
        "latest_correlation": latest_correlation,
        "series_ref": series_ref,
    }


def _load_correlation_matrix(
    *,
    output_dir_csv: Path | str | None,
    correlation_matrix: pd.DataFrame | None,
    correlation_matrix_ref: str | None,
    window_suffix: str,
) -> tuple[pd.DataFrame | None, str | None]:
    if correlation_matrix is not None and not correlation_matrix.empty:
        ref = correlation_matrix_ref or f"correlation_matrix_{window_suffix}.csv"
        return correlation_matrix, ref
    if output_dir_csv is None:
        return None, None
    ref = f"correlation_matrix_{window_suffix}.csv"
    path = Path(output_dir_csv) / ref
    if not path.is_file():
        return None, None
    try:
        frame = pd.read_csv(path, index_col=0)
    except Exception:
        return None, None
    if frame.empty:
        return None, None
    return frame, ref


def top_correlation_pairs(
    corr: pd.DataFrame,
    *,
    n: int = 3,
    exclude_tickers: set[str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return up to n highest- and lowest-correlation off-diagonal pairs (upper triangle)."""
    exclude = {str(t).upper() for t in (exclude_tickers or set())}
    columns = [str(c) for c in corr.columns]
    pairs: list[dict[str, Any]] = []
    for i, ticker_a in enumerate(columns):
        for j in range(i + 1, len(columns)):
            ticker_b = columns[j]
            if ticker_a.upper() in exclude or ticker_b.upper() in exclude:
                continue
            try:
                value = float(corr.iloc[i, j])
            except (TypeError, ValueError):
                continue
            if math.isnan(value):
                continue
            a, b = (ticker_a, ticker_b) if ticker_a <= ticker_b else (ticker_b, ticker_a)
            pairs.append(
                {
                    "ticker_a": a,
                    "ticker_b": b,
                    "correlation": round(value, REPORT_DECIMALS),
                }
            )
    if not pairs:
        return [], []
    highest = sorted(pairs, key=lambda p: p["correlation"], reverse=True)[:n]
    lowest = sorted(pairs, key=lambda p: p["correlation"])[:n]
    return highest, lowest


def avg_pairwise_correlation(corr: pd.DataFrame) -> float | None:
    """Mean off-diagonal Pearson correlation (upper triangle, ddof=0)."""
    columns = [str(c) for c in corr.columns]
    values: list[float] = []
    for i in range(len(columns)):
        for j in range(i + 1, len(columns)):
            try:
                value = float(corr.iloc[i, j])
            except (TypeError, ValueError):
                continue
            if math.isnan(value):
                continue
            values.append(value)
    if not values:
        return None
    return round(sum(values) / len(values), REPORT_DECIMALS)


def _behavior_snapshot(
    *,
    metrics: dict[str, Any],
    drawdown: dict[str, Any],
    tail_available: bool,
    warnings: list[str],
) -> dict[str, Any]:
    cagr = _as_float(metrics.get("cagr"))
    vol = _as_float(metrics.get("vol_annual"))
    sharpe = _as_float(metrics.get("sharpe"))
    sortino = _as_float(metrics.get("sortino"))
    mdd = _as_float(drawdown.get("max_drawdown"))
    beta = _as_float(metrics.get("beta_portfolio"))
    recovered = drawdown.get("recovered")

    key_points: list[str] = []
    if cagr is not None and vol is not None:
        key_points.append(
            f"Realized CAGR {_round_metric(cagr):.3f} with annualized volatility {_round_metric(vol):.3f} "
            f"over the primary window."
        )
    if sharpe is not None:
        sortino_txt = f"{_round_metric(sortino):.3f}" if sortino is not None else "n/a"
        key_points.append(f"Sharpe ratio {_round_metric(sharpe):.3f}; Sortino {sortino_txt}.")
    if mdd is not None:
        rec_phrase = "recovered within sample" if recovered else "not yet recovered in window"
        key_points.append(f"Maximum drawdown {_round_metric(mdd):.3f}; deepest episode {rec_phrase}.")
    if tail_available:
        key_points.append("Daily historical VaR/ES tail metrics are available for this run.")
    else:
        key_points.append("Daily tail risk metrics were not available for this run.")
    if beta is not None:
        key_points.append(f"Base-benchmark beta {_round_metric(beta):.3f} on monthly aligned returns.")
    for warning in warnings[:2]:
        if warning not in key_points:
            key_points.append(warning)

    headline: str | None = None
    if cagr is not None and mdd is not None:
        headline = (
            f"The portfolio delivered {_round_metric(cagr):.3f} CAGR with a "
            f"{_round_metric(mdd):.3f} maximum drawdown over the primary diagnostic window."
        )
    elif warnings:
        headline = warnings[0]
    else:
        headline = "Portfolio behavior diagnostics are limited because primary metrics are incomplete."

    label: str | None = None
    if sharpe is not None and mdd is not None:
        if sharpe >= 0.6 and mdd > -0.15:
            label = "balanced"
        elif mdd <= -0.25:
            label = "drawdown_sensitive"
        elif vol is not None and vol >= 0.14:
            label = "volatile"
        else:
            label = "moderate"

    return {
        "headline": headline,
        "key_points": key_points[:5],
        "overall_behavior_label": label,
    }


def build_block_2_2_portfolio_metrics(
    *,
    analysis_setup: dict[str, Any] | None,
    portfolio_metrics: dict[str, Any] | None,
    portfolio_analytics: dict[str, Any] | None,
    drawdown_structure: dict[str, Any] | None,
    portfolio_windows: dict[str, dict[str, Any]] | None = None,
    correlation_matrix: pd.DataFrame | None = None,
    correlation_matrix_ref: str | None = None,
    output_dir_csv: Path | str | None = None,
    primary_window_months: int = 120,
    weights: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Map snapshot/report metrics into the Block 2.2 product contract (no formula recompute)."""
    subject_type, analysis_mode, investor_currency = _setup_context(analysis_setup)
    metrics, window_suffix, window_label, resolved_months = _resolve_primary_metrics(
        portfolio_windows, portfolio_metrics
    )
    if primary_window_months and resolved_months != primary_window_months:
        override = _WINDOW_SUFFIX_BY_MONTHS.get(int(primary_window_months))
        if override and not portfolio_windows:
            window_suffix, window_label = override
            resolved_months = int(primary_window_months)

    analytics = portfolio_analytics if isinstance(portfolio_analytics, dict) else {}
    if isinstance(drawdown_structure, dict) and drawdown_structure:
        dd_struct = drawdown_structure
    else:
        nested = analytics.get("drawdown_structure")
        dd_struct = nested if isinstance(nested, dict) else {}
    depth, length_months, recovery_months = _deepest_drawdown_episode(dd_struct)

    tail_diag, tail_available = _build_tail_risk_diagnostics(analytics, metrics)
    data_quality_warnings: list[str] = []
    informational_disclosures: list[str] = []

    weight_map = resolved_analysis_weights(analysis_setup, weights=weights)
    real_cash_labels = _real_cash_labels(analysis_setup, weight_map=weight_map)
    if real_cash_labels:
        informational_disclosures.append(
            "Cash holdings are handled as real cash positions (zero return/volatility, no market price download) and remain distinct from cash proxy ETFs."
        )

    n_obs = _metric_quality_n_obs(metrics)
    if not metrics or _metrics_mostly_missing(metrics):
        data_quality_warnings.append(
            "Analysis is limited because of short history / incomplete data."
        )
    elif n_obs is not None and n_obs < max(12, int(resolved_months * 0.8)):
        data_quality_warnings.append(
            "Analysis is limited because of short history / incomplete data."
        )

    if not tail_available:
        data_quality_warnings.append(
            "Daily historical tail risk (VaR/ES) is unavailable for this run."
        )

    corr_frame, matrix_ref = _load_correlation_matrix(
        output_dir_csv=output_dir_csv,
        correlation_matrix=correlation_matrix,
        correlation_matrix_ref=correlation_matrix_ref,
        window_suffix=window_suffix,
    )
    highest_pairs: list[dict[str, Any]] = []
    lowest_pairs: list[dict[str, Any]] = []
    avg_pairwise: float | None = None
    if corr_frame is not None:
        highest_pairs, lowest_pairs = top_correlation_pairs(corr_frame, n=3)
        avg_pairwise = avg_pairwise_correlation(corr_frame)
    else:
        data_quality_warnings.append(
            "Correlation breakdown is limited because the primary-window correlation matrix is missing."
        )

    return_risk = {
        "portfolio_cagr": _round_metric(metrics.get("cagr")),
        "vol_annual": _round_metric(metrics.get("vol_annual")),
        "sharpe": _round_metric(metrics.get("sharpe")),
        "sortino": _round_metric(metrics.get("sortino")),
        "treynor": _round_metric(metrics.get("treynor")),
        "skewness": _round_metric(metrics.get("skewness")),
        "kurtosis": _round_metric(metrics.get("kurtosis")),
    }
    beta_portfolio = _round_metric(metrics.get("beta_portfolio"))
    drawdown_diag = {
        "max_drawdown": _round_metric(metrics.get("max_drawdown")),
        "ttr_months": _round_metric(metrics.get("ttr_months")),
        "recovered": bool(metrics.get("recovered")) if metrics.get("recovered") is not None else None,
        "drawdown_depth": depth,
        "drawdown_length": length_months,
        "recovery_months": recovery_months,
        "recovery_median": _round_metric(_drawdown_summary_field(dd_struct, "recovery_median_months")),
        "recovery_p90": _round_metric(_drawdown_summary_field(dd_struct, "recovery_p90_months")),
        "pct_time_underwater": _round_metric(_drawdown_summary_field(dd_struct, "pct_time_underwater")),
        "longest_underwater": _drawdown_summary_field(dd_struct, "longest_underwater_months"),
        "count_drawdowns_gt_5": _threshold_count(dd_struct, ">5%"),
        "count_drawdowns_gt_10": _threshold_count(dd_struct, ">10%"),
        "count_drawdowns_gt_20": _threshold_count(dd_struct, ">20%"),
    }
    benchmark_dep = {
        "benchmark_ticker": _benchmark_ticker(metrics),
        "beta_portfolio": beta_portfolio,
        "beta_base": beta_portfolio,
        "corr_base": _round_metric(metrics.get("corr_base")),
        "downside_beta": _round_metric(metrics.get("downside_beta")),
        "upside_beta": _round_metric(metrics.get("upside_beta")),
    }
    rolling_core = {
        "rolling_sharpe_36m": _rolling_panel(
            analytics.get("rolling_sharpe_36m") if isinstance(analytics.get("rolling_sharpe_36m"), dict) else None,
            series_ref=f"rolling_sharpe_36m_{window_suffix}.csv",
        ),
        "rolling_volatility_12m": _rolling_panel(
            analytics.get("rolling_vol_12m") if isinstance(analytics.get("rolling_vol_12m"), dict) else None,
            series_ref=f"rolling_vol_12m_{window_suffix}.csv",
        ),
        "rolling_beta_or_correlation": _rolling_beta_or_correlation_panel(
            analytics, window_suffix=window_suffix
        ),
    }
    advanced_available = {
        key: isinstance(analytics.get(key), dict) and analytics.get(key) is not None
        for key in _ADVANCED_ROLLING_KEYS
    }
    metadata: dict[str, Any] = {
        "source": "core_mvp_input",
        "cash_treatment": "real_cash_position_if_present" if real_cash_labels else "market_tickers_only",
        "cash_proxy_used_for_real_cash": False,
        "metric_quality_internal_only": True,
        "primary_window_months": int(resolved_months),
        "primary_window_label": window_label,
    }
    vol_of_vol = _round_metric(analytics.get("vol_of_vol"))
    rel_vol_of_vol = _round_metric(analytics.get("rel_vol_of_vol"))
    if vol_of_vol is not None:
        metadata["vol_of_vol"] = vol_of_vol
    if rel_vol_of_vol is not None:
        metadata["rel_vol_of_vol"] = rel_vol_of_vol

    behavior = _behavior_snapshot(
        metrics=metrics,
        drawdown=drawdown_diag,
        tail_available=tail_available,
        warnings=data_quality_warnings,
    )

    return {
        "block": BLOCK_2_2_ID,
        "analysis_subject": subject_type,
        "analysis_mode": analysis_mode,
        "investor_currency": investor_currency,
        "portfolio_behavior_snapshot": behavior,
        "return_risk_metrics": return_risk,
        "drawdown_diagnostics": drawdown_diag,
        "tail_risk_diagnostics": tail_diag,
        "benchmark_dependence": benchmark_dep,
        "rolling_diagnostics": {
            "core_view": rolling_core,
            "advanced_available": advanced_available,
        },
        "correlation_breakdown": {
            "top3_highest_correlation_pairs": highest_pairs,
            "top3_lowest_correlation_pairs": lowest_pairs,
            "avg_pairwise_correlation": avg_pairwise,
            "full_matrix_available": corr_frame is not None,
            "full_matrix_ref": matrix_ref,
        },
        "data_quality_warnings": data_quality_warnings,
        "informational_disclosures": informational_disclosures,
        "metadata": metadata,
    }


__all__ = [
    "BLOCK_2_2_ID",
    "avg_pairwise_correlation",
    "build_block_2_2_portfolio_metrics",
    "top_correlation_pairs",
]
