"""Portfolio X-Ray helpers built from existing report diagnostics only."""
from __future__ import annotations

import html
import math
from pathlib import Path
from typing import Any

import pandas as pd


PORTFOLIO_XRAY_VERSION = "portfolio_xray_v2"
DIAGNOSTIC_ONLY_DISCLAIMER = (
    "Portfolio X-Ray v2 is diagnostic-only. It summarizes existing report pipeline "
    "outputs and in-memory diagnostics; it does not optimize, change weights, change "
    "mandate gates, change stress pass/fail status, score portfolios, select portfolios, "
    "or provide trade instructions."
)

XRAY_SECTION_KEYS = (
    "asset_allocation",
    "risk_diagnostics",
    "factor_exposure",
    "hidden_risk_detector",
    "portfolio_archetype",
    "risk_budget_view",
    "weakness_map",
)

XRAY_SECTION_TITLES = {
    "asset_allocation": "Asset Allocation Summary",
    "risk_diagnostics": "Portfolio Metrics / Risk Diagnostics",
    "factor_exposure": "Factor Exposure / Factor Sensitivity",
    "hidden_risk_detector": "Hidden Exposure / Hidden Risk Detector",
    "portfolio_archetype": "Portfolio Archetype Classification",
    "risk_budget_view": "Risk Budget View",
    "weakness_map": "Portfolio Weakness Map",
}

# Named thresholds for transparent diagnostic rules. These thresholds classify
# existing diagnostics; they do not create optimizer constraints or portfolio gates.
XRAY_THRESHOLDS: dict[str, float] = {
    "equity_beta_moderate_abs": 0.35,
    "equity_beta_high_abs": 0.65,
    "factor_beta_moderate_abs": 0.25,
    "factor_beta_high_abs": 0.50,
    "top1_rc_moderate": 0.25,
    "top1_rc_high": 0.35,
    "top3_rc_high": 0.60,
    "pca_pc1_moderate": 0.40,
    "pca_pc1_high": 0.60,
    "stress_top1_rc_moderate": 0.25,
    "stress_top1_rc_high": 0.35,
    "factor_residual_moderate": 0.50,
    "factor_residual_high": 0.65,
    "duration_weight_high": 0.30,
    "credit_weight_high": 0.25,
    "liquidity_risk_weight_high": 0.20,
    "weak_hedge_oos_mae_moderate": 0.05,
    "weak_hedge_oos_mae_high": 0.10,
    "macro_dominant_variance_share_moderate": 0.35,
    "macro_dominant_variance_share_high": 0.50,
    "archetype_equity_weight_high": 0.55,
    "archetype_fixed_income_weight_high": 0.45,
    "archetype_balanced_equity_min": 0.30,
    "archetype_balanced_equity_max": 0.70,
    "archetype_balanced_fixed_income_min": 0.20,
    "archetype_cash_weight_high": 0.35,
    "archetype_defensive_equity_max": 0.30,
    "archetype_concentrated_rc_min": 0.35,
    "stress_loss_moderate": -0.06,
    "stress_loss_high": -0.12,
    "max_drawdown_moderate": -0.10,
    "max_drawdown_high": -0.20,
    "es_95_moderate": -0.015,
    "es_95_high": -0.025,
}

FACTOR_DISPLAY_NAMES = {
    "beta_eq": "equity",
    "beta_rr": "rates",
    "beta_inf": "inflation",
    "beta_credit": "credit",
    "beta_usd": "USD",
    "beta_cmd": "commodity",
    "beta_vix": "volatility/VIX",
    "beta_us_growth": "growth",
}

WEAKNESS_SCENARIO_MAP = {
    "recession_severe": "recession",
    "inflation_stagflation": "inflation",
    "rates_shock": "rates",
    "credit_shock": "credit",
    "liquidity_shock": "liquidity",
    "equity_shock": "equity_crash",
}

WEAKNESS_FACTOR_MAP = {
    "beta_eq": "equity_crash",
    "beta_rr": "rates",
    "beta_inf": "inflation",
    "beta_credit": "credit",
    "beta_usd": "usd",
    "beta_cmd": "commodity_shock",
    "beta_vix": "volatility_spike",
    "beta_us_growth": "equity_crash",
}

WEAKNESS_KEYS = (
    "recession",
    "inflation",
    "rates",
    "credit",
    "liquidity",
    "usd",
    "equity_crash",
    "commodity_shock",
    "volatility_spike",
)

WEAKNESS_CRYPTO_KEY = "crypto_shock"

WEAKNESS_EXPOSURE_WEIGHT_MIN = 0.05

_FACTOR_SHORT_TO_BETA_KEY = {
    "eq": "beta_eq",
    "rr": "beta_rr",
    "credit": "beta_credit",
    "inf": "beta_inf",
    "usd": "beta_usd",
    "cmd": "beta_cmd",
}

WEAKNESS_FACTOR_SHORTS: dict[str, tuple[str, ...]] = {
    "recession": ("eq", "credit"),
    "inflation": ("inf", "cmd"),
    "rates": ("rr",),
    "credit": ("credit",),
    "liquidity": ("eq", "credit"),
    "usd": ("usd",),
    "equity_crash": ("eq",),
    "commodity_shock": ("cmd",),
    "volatility_spike": (),
    WEAKNESS_CRYPTO_KEY: (),
}

WEAKNESS_EXPOSURE_HINTS: dict[str, dict[str, tuple[str, ...]]] = {
    "recession": {
        "asset_class": ("equity",),
        "risk_bucket": ("credit", "equity"),
        "main_risk_factor": ("equity", "credit", "us_growth"),
        "factor_beta": ("beta_eq", "beta_credit", "beta_us_growth"),
    },
    "inflation": {
        "asset_class": ("commodity",),
        "risk_bucket": ("inflation_linked",),
        "main_risk_factor": ("inflation", "commodity"),
        "factor_beta": ("beta_inf", "beta_cmd"),
    },
    "rates": {
        "asset_class": ("fixed_income",),
        "main_risk_factor": ("real_rates", "short_rates"),
        "factor_beta": ("beta_rr",),
    },
    "credit": {
        "risk_bucket": ("credit",),
        "main_risk_factor": ("credit",),
        "factor_beta": ("beta_credit",),
    },
    "liquidity": {
        "main_risk_factor": ("liquidity",),
        "secondary_risk_factor": ("liquidity",),
        "risk_role": ("carry",),
    },
    "usd": {
        "main_risk_factor": ("usd",),
        "factor_beta": ("beta_usd",),
    },
    "equity_crash": {
        "asset_class": ("equity",),
        "main_risk_factor": ("equity", "us_growth"),
        "factor_beta": ("beta_eq", "beta_us_growth"),
    },
    "commodity_shock": {
        "asset_class": ("commodity",),
        "main_risk_factor": ("commodity",),
        "factor_beta": ("beta_cmd",),
    },
    "volatility_spike": {
        "factor_beta": ("beta_vix",),
    },
    WEAKNESS_CRYPTO_KEY: {
        "asset_class": ("crypto",),
        "main_risk_factor": ("crypto_beta",),
    },
}

ARCHETYPE_WEAKNESS_TENSIONS: dict[str, tuple[str, ...]] = {
    "Inflation-sensitive": ("inflation", "rates"),
    "Duration-heavy Defensive": ("rates", "inflation"),
    "Equity Growth Portfolio": ("equity_crash", "recession"),
    "Credit Carry Portfolio": ("credit", "liquidity"),
    "Balanced 60/40-like": ("recession", "rates", "inflation"),
    "Defensive Portfolio": ("rates", "inflation"),
    "Concentrated-risk Portfolio": ("equity_crash", "recession", "liquidity"),
    "Tail-risk Exposed Portfolio": ("volatility_spike", "liquidity"),
    "Pseudo-diversified Portfolio": ("recession", "equity_crash"),
    "Cash-heavy Low-Risk": ("rates", "inflation"),
}


def _as_float(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(out) or math.isinf(out):
        return None
    return out


def _fmt_pct(value: Any, digits: int = 1) -> str:
    number = _as_float(value)
    if number is None:
        return "n/a"
    return f"{number * 100:.{digits}f}%"


def _fmt_pp(value: Any, digits: int = 1) -> str:
    number = _as_float(value)
    if number is None:
        return "n/a"
    sign = "+" if number >= 0 else ""
    return f"{sign}{number * 100:.{digits}f}pp"


def _fmt_num(value: Any, digits: int = 3) -> str:
    number = _as_float(value)
    if number is None:
        return "n/a"
    return f"{number:.{digits}f}"


def _clean_sources(values: list[str] | tuple[str, ...] | None) -> list[str]:
    out: list[str] = []
    for value in values or []:
        if not value:
            continue
        s = str(value)
        if s not in out:
            out.append(s)
    return out


def _section(
    *,
    items: list[dict[str, Any]] | None = None,
    data_sources_used: list[str] | tuple[str, ...] | None = None,
    warnings: list[str] | tuple[str, ...] | None = None,
    limitations: list[str] | tuple[str, ...] | None = None,
    unavailable_warning: str | None = None,
) -> dict[str, Any]:
    item_list = list(items or [])
    warning_list = [str(w) for w in warnings or [] if str(w).strip()]
    if not item_list and unavailable_warning:
        warning_list.append(unavailable_warning)
    if not item_list:
        status = "unavailable"
    elif warning_list:
        status = "partial"
    else:
        status = "available"
    return {
        "status": status,
        "data_sources_used": _clean_sources(data_sources_used),
        "warnings": warning_list,
        "items": item_list,
        "limitations": [str(x) for x in limitations or [] if str(x).strip()],
    }


def _top_items(values: dict[str, Any], limit: int = 3) -> list[dict[str, Any]]:
    rows = []
    for ticker, value in values.items():
        number = _as_float(value)
        if number is None or number <= 0:
            continue
        rows.append({"ticker": str(ticker), "value": number})
    return sorted(rows, key=lambda x: (-x["value"], x["ticker"]))[:limit]


def _rc_items(rc_asset: Any, limit: int = 3) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in rc_asset or []:
        if isinstance(item, dict):
            ticker = item.get("ticker")
            value = item.get("rc_pct")
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            ticker, value = item[0], item[1]
        else:
            continue
        number = _as_float(value)
        if ticker is None or number is None:
            continue
        rows.append({"ticker": str(ticker), "value": number})
    return sorted(rows, key=lambda x: (-x["value"], x["ticker"]))[:limit]


def _join_items(items: list[dict[str, Any]]) -> str:
    if not items:
        return "n/a"
    return ", ".join(f"{row['ticker']} {_fmt_pct(row['value'])}" for row in items)


def _analysis_portfolio(analysis_setup: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(analysis_setup, dict):
        return {}
    value = analysis_setup.get("analysis_portfolio")
    return value if isinstance(value, dict) else {}


def _portfolio_input(analysis_setup: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(analysis_setup, dict):
        return {}
    value = analysis_setup.get("portfolio_input")
    return value if isinstance(value, dict) else {}


def _resolved_assumptions(analysis_setup: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(analysis_setup, dict):
        return {}
    value = analysis_setup.get("resolved_assumptions")
    return value if isinstance(value, dict) else {}


def _stress_status(stress_report: dict[str, Any] | None) -> str:
    if not isinstance(stress_report, dict):
        return "n/a"
    return str(stress_report.get("status") or "n/a")


def _main_concern(
    *,
    stress_report: dict[str, Any] | None,
    portfolio_valid: bool | None,
    top_rc: dict[str, Any] | None,
) -> str:
    if portfolio_valid is False:
        return "mandate MaxDD gate did not pass"
    if isinstance(stress_report, dict):
        failed_scenario = stress_report.get("failed_scenario")
        primary_code = stress_report.get("primary_diagnostic_code") or stress_report.get("fail_reason_code")
        if failed_scenario:
            return f"stress scenario {failed_scenario}"
        if primary_code:
            return str(primary_code)
        scenarios = stress_report.get("scenario_results") or []
        worst = None
        for row in scenarios:
            if not isinstance(row, dict):
                continue
            pnl = _as_float(row.get("portfolio_pnl_pct"))
            if pnl is None:
                continue
            if worst is None or pnl < worst[1]:
                worst = (str(row.get("scenario_id") or "unknown"), pnl)
        if worst is not None:
            return f"{worst[0]} sensitivity"
    if top_rc:
        return f"risk concentration in {top_rc['ticker']}"
    return "no single diagnostic concern identified from available artifacts"


def build_portfolio_xray_summary(
    *,
    analysis_setup: dict[str, Any] | None,
    weights: dict[str, Any] | None,
    rc_asset: Any,
    stress_report: dict[str, Any] | None,
    portfolio_valid: bool | None,
    portfolio_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the legacy explanatory X-Ray summary without scores or recommendations."""
    ap = _analysis_portfolio(analysis_setup)
    pi = _portfolio_input(analysis_setup)
    ra = _resolved_assumptions(analysis_setup)
    weight_map = dict(weights or ap.get("weights") or {})
    top_weight = _top_items(weight_map, limit=3)
    top_rc = _rc_items(rc_asset, limit=3)
    cash_proxy = None
    cash_proxy_block = ra.get("cash_proxy")
    if isinstance(cash_proxy_block, dict):
        cash_proxy = cash_proxy_block.get("ticker")
    if cash_proxy is None:
        cash_handling = ap.get("cash_handling")
        if isinstance(cash_handling, dict):
            cash_proxy = cash_handling.get("cash_proxy_ticker")
    cash_weight = _as_float(weight_map.get(str(cash_proxy))) if cash_proxy else None
    top_weight_first = top_weight[0] if top_weight else None
    top_rc_first = top_rc[0] if top_rc else None
    top3_weight_sum = sum(row["value"] for row in top_weight)
    top3_rc_sum = sum(row["value"] for row in top_rc)
    concern = _main_concern(
        stress_report=stress_report,
        portfolio_valid=portfolio_valid,
        top_rc=top_rc_first,
    )
    role = str(ap.get("portfolio_role") or "unknown")
    weight_source = str(ap.get("weight_source") or "unknown")
    recommendation_status = str(ap.get("recommendation_status") or "not_recommendation")
    stress = _stress_status(stress_report)
    metric_mdd = (portfolio_metrics or {}).get("max_drawdown") if isinstance(portfolio_metrics, dict) else None
    metric_vol = (portfolio_metrics or {}).get("vol_annual") if isinstance(portfolio_metrics, dict) else None

    verdict_lines = [
        f"Analyzed portfolio role: {role}; weight source: {weight_source}.",
        f"Capital concentration: {_join_items(top_weight)}.",
        f"Risk concentration by RC_vol: {_join_items(top_rc)}.",
        f"Main diagnostic concern: {concern}.",
        f"Mandate gate: {'PASS' if portfolio_valid is True else 'FAIL' if portfolio_valid is False else 'n/a'}; stress status: {stress}.",
        "This is an explanatory diagnostic summary, not a score, recommendation, selection decision, or trade instruction.",
    ]

    return {
        "analysis_setup_summary": {
            "portfolio_role": role,
            "weight_source": weight_source,
            "recommendation_status": recommendation_status,
            "product_input_case": pi.get("product_input_case"),
            "investor_currency": pi.get("investor_currency"),
            "base_benchmark_ticker": ra.get("base_benchmark_ticker") or pi.get("base_benchmark_ticker"),
            "cash_proxy_ticker": cash_proxy,
            "return_frequency": ra.get("return_frequency"),
            "analysis_windows": ra.get("analysis_windows"),
        },
        "asset_allocation_summary": {
            "top_holdings": top_weight,
            "top3_weight_sum": top3_weight_sum,
            "cash_proxy_ticker": cash_proxy,
            "cash_weight": cash_weight,
            "largest_holding": top_weight_first,
        },
        "risk_contribution_summary": {
            "top_rc_contributors": top_rc,
            "top3_rc_sum": top3_rc_sum,
            "largest_risk_contributor": top_rc_first,
            "largest_weight_vs_largest_risk_match": (
                bool(top_weight_first and top_rc_first and top_weight_first["ticker"] == top_rc_first["ticker"])
            ),
            "method_note": "RC_vol is diagnostic-only and does not act as an optimizer gate or recommendation rule.",
        },
        "portfolio_diagnostic_verdict": {
            "main_diagnostic_concern": concern,
            "mandate_gate": "PASS" if portfolio_valid is True else "FAIL" if portfolio_valid is False else "n/a",
            "stress_status": stress,
            "vol_annual": metric_vol,
            "max_drawdown": metric_mdd,
            "lines": verdict_lines,
        },
    }


def _load_default_taxonomy() -> tuple[dict[str, dict[str, Any]], dict[str, str], list[str]]:
    try:
        from src.risk_budgeting import load_merged_universe_rows

        rows, sources = load_merged_universe_rows()
        return rows, sources, []
    except Exception as exc:
        return {}, {}, [f"taxonomy load failed: {exc}"]


def _risk_budget_bucket(row: dict[str, Any] | None) -> str:
    try:
        from src.risk_budgeting import risk_budget_bucket_from_row

        return risk_budget_bucket_from_row(row)
    except Exception:
        return "unknown"


def _taxonomy_lookup(
    taxonomy_rows: dict[str, dict[str, Any]] | None,
    taxonomy_sources: dict[str, str] | None,
) -> tuple[dict[str, dict[str, Any]], dict[str, str], list[str]]:
    if taxonomy_rows is None:
        return _load_default_taxonomy()
    rows = {str(k).upper(): v for k, v in taxonomy_rows.items() if isinstance(v, dict)}
    sources = {str(k).upper(): str(v) for k, v in (taxonomy_sources or {}).items()}
    return rows, sources, []


def _row_for_ticker(ticker: str, rows: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    return rows.get(str(ticker).upper()) or rows.get(str(ticker))


def _positive_weights(weights: dict[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    for ticker, value in weights.items():
        number = _as_float(value)
        if number is not None and number > 0:
            out[str(ticker)] = number
    return out


def _as_rc_map(rc_asset: Any) -> dict[str, float]:
    return {row["ticker"]: row["value"] for row in _rc_items(rc_asset, limit=10_000)}


def load_rc_vol_map_from_csv(output_dir_csv: Path | str | None) -> dict[str, float]:
    """Load full per-asset RC_vol from results_csv (10Y preferred, then 5Y/3Y)."""
    if output_dir_csv is None:
        return {}
    base = Path(output_dir_csv)
    for suffix in ("10y", "5y", "3y"):
        path = base / f"rc_vol_{suffix}.csv"
        if not path.is_file():
            continue
        try:
            df = pd.read_csv(path, index_col=0)
            if df.empty or df.shape[1] < 1:
                continue
            series = df.iloc[:, 0].dropna()
            out: dict[str, float] = {}
            for ticker, value in series.items():
                number = _as_float(value)
                ticker_s = str(ticker).strip()
                if number is None or not ticker_s:
                    continue
                out[ticker_s] = number
            if out:
                return out
        except Exception:
            continue
    return {}


def resolve_rc_asset_for_xray(
    rc_asset: Any,
    *,
    rc_vol_map: dict[str, float] | None = None,
    output_dir_csv: Path | str | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    """
    Prefer full RC_vol CSV evidence; use snapshot RC_asset rows only to fill gaps.

    Returns (rc_asset rows for X-Ray builders, data_sources_used additions).
    """
    merged: dict[str, float] = {}
    sources: list[str] = []
    if rc_vol_map:
        merged = {str(k): float(v) for k, v in rc_vol_map.items() if _as_float(v) is not None}
        sources.append("rc_vol_map")
    elif output_dir_csv is not None:
        merged = load_rc_vol_map_from_csv(output_dir_csv)
        if merged:
            sources.append(f"{Path(output_dir_csv)}/rc_vol_10y.csv")
    for row in _rc_items(rc_asset, limit=10_000):
        merged.setdefault(row["ticker"], row["value"])
    if not sources and rc_asset:
        sources.append("snapshot.RC_asset")
    rows = [{"ticker": ticker, "rc_pct": value} for ticker, value in merged.items()]
    rows.sort(key=lambda x: (-x["rc_pct"], x["ticker"]))
    return rows, sources


def _aggregate_values(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    totals: dict[str, float] = {}
    for row in rows:
        value = row.get(key)
        if isinstance(value, list):
            values = [str(v).strip() for v in value if str(v).strip()]
            split_weight = row["weight"] / max(len(values), 1)
            for item in values or ["unknown"]:
                totals[item] = totals.get(item, 0.0) + split_weight
        else:
            label = str(value or "unknown").strip() or "unknown"
            totals[label] = totals.get(label, 0.0) + row["weight"]
    return [
        {"name": name, "weight": value}
        for name, value in sorted(totals.items(), key=lambda x: (-x[1], x[0]))
    ]


def _allocation_section(
    *,
    weights: dict[str, Any],
    taxonomy_rows: dict[str, dict[str, Any]] | None,
    taxonomy_sources: dict[str, str] | None,
) -> tuple[dict[str, Any], dict[str, float]]:
    weight_map = _positive_weights(weights)
    rows, sources, warnings = _taxonomy_lookup(taxonomy_rows, taxonomy_sources)
    holding_items: list[dict[str, Any]] = []
    unknown_weight = 0.0
    if not weight_map:
        return _section(
            items=[],
            data_sources_used=["analyzed weights", "config/etf_universe.yml", "config/stock_universe.yml"],
            warnings=warnings,
            limitations=[
                "Taxonomy is annotation-only in V1 and does not select assets or change weights.",
                "ETF sector and currency fields can describe broad economic exposure rather than exact look-through holdings.",
            ],
            unavailable_warning="No positive analyzed weights were available for allocation diagnostics.",
        ), {}

    for ticker, weight in sorted(weight_map.items(), key=lambda x: (-x[1], x[0])):
        tax = _row_for_ticker(ticker, rows) or {}
        if not tax:
            unknown_weight += weight
        source = sources.get(ticker.upper(), "unknown")
        item = {
            "type": "holding",
            "ticker": ticker,
            "weight": weight,
            "taxonomy_source": source,
            "asset_class": tax.get("asset_class", "unknown"),
            "region": tax.get("region", "unknown"),
            "currency_exposure": tax.get("currency_exposure", "unknown"),
            "sector": tax.get("sector", "unknown"),
            "risk_role": tax.get("risk_role") if isinstance(tax.get("risk_role"), list) else ["unknown"],
            "main_risk_factor": tax.get("main_risk_factor", "unknown"),
            "secondary_risk_factors": (
                tax.get("secondary_risk_factors")
                if isinstance(tax.get("secondary_risk_factors"), list)
                else []
            ),
            "duration_bucket": tax.get("duration_bucket", "unknown"),
            "credit_quality": tax.get("credit_quality", "unknown"),
            "risk_bucket": _risk_budget_bucket(tax),
        }
        holding_items.append(item)

    if unknown_weight > 0:
        warnings.append(f"{_fmt_pct(unknown_weight)} of portfolio weight has unknown taxonomy")

    breakdowns = []
    for dimension in (
        "asset_class",
        "region",
        "currency_exposure",
        "sector",
        "risk_role",
        "main_risk_factor",
        "risk_bucket",
    ):
        breakdowns.append(
            {
                "type": "breakdown",
                "dimension": dimension,
                "values": _aggregate_values(holding_items, dimension),
            }
        )

    items = holding_items + breakdowns
    return _section(
        items=items,
        data_sources_used=["analyzed weights", "config/etf_universe.yml", "config/stock_universe.yml"],
        warnings=warnings,
        limitations=[
            "Taxonomy is annotation-only in V1 and does not select assets or change weights.",
            "ETF sector and currency fields can describe broad economic exposure rather than exact look-through holdings.",
        ],
        unavailable_warning="No positive analyzed weights were available for allocation diagnostics.",
    ), {}


def _risk_diagnostics_section(
    *,
    portfolio_metrics: dict[str, Any] | None,
    portfolio_analytics: dict[str, Any] | None,
    drawdown_structure: dict[str, Any] | None,
) -> dict[str, Any]:
    metrics = portfolio_metrics if isinstance(portfolio_metrics, dict) else {}
    analytics = portfolio_analytics if isinstance(portfolio_analytics, dict) else {}
    items: list[dict[str, Any]] = []
    if metrics:
        items.append(
            {
                "type": "portfolio_metrics",
                "cagr": metrics.get("cagr"),
                "vol_annual": metrics.get("vol_annual"),
                "sharpe": metrics.get("sharpe"),
                "sortino": metrics.get("sortino"),
                "beta_portfolio": metrics.get("beta_portfolio"),
                "corr_base": metrics.get("corr_base"),
                "downside_beta": metrics.get("downside_beta"),
                "upside_beta": metrics.get("upside_beta"),
                "skewness": metrics.get("skewness"),
                "kurtosis": metrics.get("kurtosis"),
                "treynor": metrics.get("treynor"),
                "max_drawdown": metrics.get("max_drawdown"),
                "metric_quality": metrics.get("metric_quality"),
            }
        )
    tail_risk = analytics.get("tail_risk")
    if isinstance(tail_risk, dict):
        items.append({"type": "tail_risk", **tail_risk})
    else:
        tail_keys = ("var_95", "var_99", "es_95", "es_99")
        flat_tail = {k: analytics.get(k) for k in tail_keys if k in analytics}
        if flat_tail:
            items.append({"type": "tail_and_crisis_metrics", **flat_tail})
    if analytics.get("eee_10pct") is not None:
        items.append({"type": "crisis_equity_exposure", "eee_10pct": analytics.get("eee_10pct")})
    rolling_keys = (
        "rolling_sharpe_36m",
        "rolling_sharpe_12m",
        "rolling_sortino_36m",
        "rolling_sortino_12m",
        "rolling_vol_12m",
        "rolling_beta_36m",
        "rolling_beta_12m",
        "rolling_correlation_36m",
        "rolling_correlation_12m",
    )
    if any(k in analytics for k in rolling_keys):
        items.append({"type": "rolling_metrics", **{k: analytics.get(k) for k in rolling_keys if k in analytics}})
    if isinstance(drawdown_structure, dict) and drawdown_structure:
        items.append(
            {
                "type": "drawdown_structure",
                "summary": drawdown_structure.get("summary") or drawdown_structure,
            }
        )
    warnings: list[str] = []
    if not metrics:
        warnings.append("portfolio metrics are missing")
    if not analytics:
        warnings.append("portfolio analytics summary is missing")
    return _section(
        items=items,
        data_sources_used=["snapshot metrics", "snapshot analytics", "drawdown_structure"],
        warnings=warnings,
        limitations=[
            "Historical metrics describe realized behavior in the selected window, not expected future returns.",
            "VaR and ES use historical daily simple returns (not Monte Carlo); check against stress scenarios before action.",
            "When tail_risk.metric_available is false, flat var/es fields may be absent or stale.",
        ],
        unavailable_warning="No portfolio metrics or analytics were available.",
    )


def _factor_betas(stress_report: dict[str, Any] | None, key: str) -> dict[str, float]:
    if not isinstance(stress_report, dict):
        return {}
    raw = stress_report.get(key)
    if not isinstance(raw, dict):
        return {}
    out: dict[str, float] = {}
    for beta_key, value in raw.items():
        number = _as_float(value)
        if number is not None:
            out[str(beta_key)] = number
    return out


def _factor_decomp_rows(stress_report: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(stress_report, dict):
        return []
    decomp = stress_report.get("factor_variance_decomposition")
    if not isinstance(decomp, dict):
        return []
    rows = decomp.get("rows")
    return [row for row in rows or [] if isinstance(row, dict)]


def _kalman_beta_map(stress_report: dict[str, Any] | None) -> dict[str, float]:
    if not isinstance(stress_report, dict):
        return {}
    block = stress_report.get("factor_betas_kalman")
    if not isinstance(block, dict):
        return {}
    kalman_raw = block.get("latest")
    if not isinstance(kalman_raw, dict) or not kalman_raw:
        kalman_raw = block.get("latest_betas_capped") or block.get("latest_betas")
    if not isinstance(kalman_raw, dict):
        return {}
    out: dict[str, float] = {}
    for beta_key, value in kalman_raw.items():
        number = _as_float(value)
        if number is not None:
            out[str(beta_key)] = number
    return out


def _factor_exposure_section(stress_report: dict[str, Any] | None) -> dict[str, Any]:
    betas_5y = _factor_betas(stress_report, "factor_betas_5y")
    betas_10y = _factor_betas(stress_report, "factor_betas_10y")
    if not betas_5y:
        betas_5y = _factor_betas(stress_report, "factor_betas")
    kalman = _kalman_beta_map(stress_report)
    decomp_by_beta = {
        str(row.get("beta_key")): row for row in _factor_decomp_rows(stress_report) if row.get("beta_key")
    }
    factor_keys = sorted(set(betas_5y) | set(betas_10y) | set(kalman) | set(decomp_by_beta))
    items = []
    for beta_key in factor_keys:
        row = decomp_by_beta.get(beta_key) or {}
        items.append(
            {
                "type": "factor_exposure",
                "beta_key": beta_key,
                "factor": row.get("factor") or FACTOR_DISPLAY_NAMES.get(beta_key, beta_key),
                "beta_5y": betas_5y.get(beta_key),
                "beta_10y": betas_10y.get(beta_key),
                "kalman_current_beta": kalman.get(beta_key),
                "net_total_variance_share": row.get("net_total_variance_share"),
                "gross_total_variance_share": row.get("gross_total_variance_share"),
                "direction": row.get("direction"),
            }
        )
    items.sort(
        key=lambda x: (
            -abs(
                _as_float(x.get("net_total_variance_share"))
                or _as_float(x.get("beta_5y"))
                or _as_float(x.get("beta_10y"))
                or 0.0
            ),
            str(x.get("beta_key")),
        )
    )
    residual = None
    if isinstance(stress_report, dict) and isinstance(stress_report.get("factor_variance_decomposition"), dict):
        residual = stress_report["factor_variance_decomposition"].get("residual_share")
        residual_severity = stress_report["factor_variance_decomposition"].get("residual_severity")
        if residual is not None:
            items.append(
                {
                    "type": "factor_residual_risk",
                    "residual_share": residual,
                    "residual_severity": residual_severity,
                    "interpretation": stress_report["factor_variance_decomposition"].get(
                        "residual_interpretation"
                    ),
                }
            )
    warnings = []
    if not items:
        warnings.append("factor betas and factor variance decomposition are missing")
    return _section(
        items=items,
        data_sources_used=[
            "stress_report.factor_betas_5y",
            "stress_report.factor_betas_10y",
            "stress_report.factor_betas_kalman",
            "stress_report.factor_variance_decomposition",
        ],
        warnings=warnings,
        limitations=[
            "Factor exposures are diagnostics from the existing factor pipeline and do not replace raw holdings.",
            "Kalman betas are current-regime diagnostics and do not replace raw 5Y/10Y OLS betas.",
        ],
        unavailable_warning="No factor diagnostics were available.",
    )


def _stress_scenarios(stress_report: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(stress_report, dict):
        return []
    return [row for row in stress_report.get("scenario_results") or [] if isinstance(row, dict)]


def _scenario_by_worst_loss(stress_report: dict[str, Any] | None) -> dict[str, Any] | None:
    worst = None
    for row in _stress_scenarios(stress_report):
        pnl = _as_float(row.get("portfolio_pnl_pct"))
        if pnl is None:
            continue
        if worst is None or pnl < worst[0]:
            worst = (pnl, row)
    return worst[1] if worst else None


def _worst_asset_stress_contrib(stress_report: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in _stress_scenarios(stress_report):
        scenario_id = str(row.get("scenario_id") or "unknown")
        pnl_by_asset = row.get("pnl_by_asset_pct")
        if not isinstance(pnl_by_asset, dict):
            continue
        for ticker, value in pnl_by_asset.items():
            number = _as_float(value)
            if number is None:
                continue
            current = out.get(str(ticker))
            if current is None or number < float(current["pnl_pct"]):
                out[str(ticker)] = {"scenario_id": scenario_id, "pnl_pct": number}
    return out


def _risk_budget_section(
    *,
    weights: dict[str, Any],
    rc_asset: Any,
    stress_report: dict[str, Any] | None,
    rc_data_sources: list[str] | None = None,
) -> dict[str, Any]:
    weight_map = _positive_weights(weights)
    rc_map = _as_rc_map(rc_asset)
    stress_map = _worst_asset_stress_contrib(stress_report)
    tickers = sorted(set(weight_map) | set(rc_map) | set(stress_map))
    items: list[dict[str, Any]] = []
    for ticker in tickers:
        weight = weight_map.get(ticker)
        rc = rc_map.get(ticker)
        stress = stress_map.get(ticker) or {}
        gap = (rc - weight) if rc is not None and weight is not None else None
        items.append(
            {
                "type": "asset_risk_budget",
                "ticker": ticker,
                "weight": weight,
                "rc_vol": rc,
                "risk_weight_gap": gap,
                "worst_stress_loss_contribution_pct": stress.get("pnl_pct"),
                "worst_stress_scenario": stress.get("scenario_id"),
            }
        )
    items.sort(
        key=lambda x: (
            -(_as_float(x.get("rc_vol")) or 0.0),
            -abs(_as_float(x.get("risk_weight_gap")) or 0.0),
            str(x.get("ticker")),
        )
    )
    warnings = []
    if not rc_map:
        warnings.append("RC_vol diagnostics are missing")
    if not stress_map:
        warnings.append("per-asset stress PnL contributions are missing")
    rc_sources = list(rc_data_sources or [])
    if not rc_sources:
        rc_sources = ["snapshot.RC_asset"]
    return _section(
        items=items,
        data_sources_used=[
            "analyzed weights",
            *rc_sources,
            "stress_report.scenario_results.pnl_by_asset_pct",
        ],
        warnings=warnings,
        limitations=[
            "RC_vol is contribution to portfolio variance from the existing pipeline and is diagnostic-only.",
            "Stress loss contribution is scenario-specific and should not be read as expected loss.",
        ],
        unavailable_warning="No weight, RC_vol, or stress contribution rows were available.",
    )


def _severity_high(value: float | None, moderate: float, high: float) -> str | None:
    if value is None:
        return None
    av = abs(value)
    if av >= high:
        return "high"
    if av >= moderate:
        return "medium"
    return None


def _severity_share(value: float | None, moderate: float, high: float) -> str | None:
    if value is None:
        return None
    if value >= high:
        return "high"
    if value >= moderate:
        return "medium"
    return None


HIDDEN_RISK_CATEGORY_ORDER = (
    "hidden_equity_beta",
    "duration_concentration",
    "credit_concentration",
    "liquidity_concentration",
    "correlation_or_common_factor_concentration",
    "residual_pca_concentration",
    "weak_hedge_behavior",
    "tail_risk",
    "stress_loss_contributor_concentration",
    "macro_factor_dependency",
    "single_asset_risk_concentration",
)


def _hidden_risk_assessment(
    *,
    category: str,
    flagged: bool,
    assessment_status: str,
    severity: str | None,
    fact: str,
    interpretation: str,
    next_test: str,
    limitation: str,
    evidence: dict[str, Any],
    thresholds: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "type": "hidden_risk_flag" if flagged else "hidden_risk_assessment",
        "name": category,
        "category": category,
        "flagged": flagged,
        "assessment_status": assessment_status,
        "severity": severity,
        "fact": fact,
        "interpretation": interpretation,
        "next_test": next_test,
        "limitation": limitation,
        "evidence": evidence,
        "thresholds": list(thresholds or []),
    }


def _hidden_risk_section_confidence(*, evaluable: int, unavailable: int) -> str:
    total = len(HIDDEN_RISK_CATEGORY_ORDER)
    if evaluable <= 0:
        return "unavailable"
    if evaluable >= 8 and unavailable <= max(2, total // 4):
        return "high"
    if evaluable >= 5:
        return "medium"
    return "low"


def _pca_raw_covariance(stress_report: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(stress_report, dict):
        return {}
    pca = stress_report.get("portfolio_pca")
    if not isinstance(pca, dict):
        return {}
    raw = pca.get("raw")
    if not isinstance(raw, dict):
        return {}
    cov = raw.get("covariance_pca")
    return cov if isinstance(cov, dict) else {}


def _pca_residual_covariance(stress_report: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(stress_report, dict):
        return {}
    pca = stress_report.get("portfolio_pca")
    if not isinstance(pca, dict):
        return {}
    residual = pca.get("residual")
    if not isinstance(residual, dict):
        return {}
    cov = residual.get("covariance_pca")
    return cov if isinstance(cov, dict) else {}


def _factor_residual_share(stress_report: dict[str, Any] | None) -> float | None:
    if not isinstance(stress_report, dict):
        return None
    decomp = stress_report.get("factor_variance_decomposition")
    if not isinstance(decomp, dict):
        return None
    return _as_float(decomp.get("residual_share"))


def _taxonomy_weight_by_predicate(
    weights: dict[str, Any],
    taxonomy_rows: dict[str, dict[str, Any]] | None,
    predicate: Any,
) -> float:
    rows, _, _ = _taxonomy_lookup(taxonomy_rows, None)
    total = 0.0
    for ticker, weight in _positive_weights(weights).items():
        row = _row_for_ticker(ticker, rows)
        if row and predicate(row):
            total += weight
    return total


def _liquidity_labeled_weight(
    weights: dict[str, Any],
    taxonomy_rows: dict[str, dict[str, Any]] | None,
) -> float:
    def _is_liquidity(row: dict[str, Any]) -> bool:
        if str(row.get("main_risk_factor") or "").lower() == "liquidity":
            return True
        roles = row.get("risk_role") or []
        if isinstance(roles, str):
            roles = [roles]
        return any(str(role).lower() == "liquidity" for role in roles)

    return _taxonomy_weight_by_predicate(weights, taxonomy_rows, _is_liquidity)


def _hedge_labeled_weight_and_tickers(
    weights: dict[str, Any],
    taxonomy_rows: dict[str, dict[str, Any]] | None,
) -> tuple[float, list[str]]:
    rows, _, _ = _taxonomy_lookup(taxonomy_rows, None)
    hedge_roles = {"crisis_hedge", "defensive", "inflation_hedge"}
    tickers: list[str] = []
    total = 0.0
    for ticker, weight in _positive_weights(weights).items():
        row = _row_for_ticker(ticker, rows)
        if not row:
            continue
        roles = row.get("risk_role") or []
        if isinstance(roles, str):
            roles = [roles]
        if any(str(role).lower() in hedge_roles for role in roles):
            tickers.append(ticker)
            total += weight
    return total, tickers


def _dominant_factor_variance_share(stress_report: dict[str, Any] | None) -> tuple[str | None, float | None]:
    if not isinstance(stress_report, dict):
        return None, None
    decomp = stress_report.get("factor_variance_decomposition")
    if not isinstance(decomp, dict):
        return None, None
    best_name: str | None = None
    best_share: float | None = None
    for row in decomp.get("rows") or []:
        if not isinstance(row, dict):
            continue
        share = _as_float(row.get("net_total_variance_share"))
        if share is None:
            continue
        factor = str(row.get("factor") or row.get("beta_key") or "unknown")
        if best_share is None or share > best_share:
            best_share = share
            best_name = factor
    return best_name, best_share


def _max_abs_factor_beta(betas: dict[str, Any]) -> tuple[str | None, float | None]:
    best_key: str | None = None
    best_abs: float | None = None
    for key, value in betas.items():
        if not str(key).startswith("beta_"):
            continue
        number = _as_float(value)
        if number is None:
            continue
        av = abs(number)
        if best_abs is None or av > best_abs:
            best_abs = av
            best_key = str(key)
    return best_key, best_abs


def _weak_hedge_stress_evidence(
    stress_report: dict[str, Any] | None,
    hedge_tickers: list[str],
) -> dict[str, Any]:
    out: dict[str, Any] = {"hedge_tickers": hedge_tickers}
    worst = _scenario_by_worst_loss(stress_report)
    if not isinstance(worst, dict) or not hedge_tickers:
        return out
    pnl_by_asset = worst.get("pnl_by_asset_pct")
    if not isinstance(pnl_by_asset, dict):
        return out
    portfolio_pnl = _as_float(worst.get("portfolio_pnl_pct"))
    failing: list[dict[str, Any]] = []
    for ticker in hedge_tickers:
        asset_pnl = _as_float(pnl_by_asset.get(ticker))
        if asset_pnl is None:
            continue
        if portfolio_pnl is not None and portfolio_pnl < 0 and asset_pnl <= 0:
            failing.append({"ticker": ticker, "pnl_pct": asset_pnl})
    out["worst_scenario_id"] = worst.get("scenario_id")
    out["portfolio_pnl_pct"] = portfolio_pnl
    out["hedge_assets_negative_with_portfolio_loss"] = failing
    return out


def _hidden_risk_section(
    *,
    weights: dict[str, Any],
    rc_asset: Any,
    stress_report: dict[str, Any] | None,
    taxonomy_rows: dict[str, dict[str, Any]] | None,
    portfolio_analytics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    warnings: list[str] = []
    betas = _factor_betas(stress_report, "factor_betas_5y") or _factor_betas(stress_report, "factor_betas")
    beta_eq = betas.get("beta_eq")
    eq_thresh = ["equity_beta_moderate_abs", "equity_beta_high_abs"]
    eq_sev = _severity_high(
        beta_eq,
        XRAY_THRESHOLDS["equity_beta_moderate_abs"],
        XRAY_THRESHOLDS["equity_beta_high_abs"],
    )
    if beta_eq is None:
        items.append(
            _hidden_risk_assessment(
                category="hidden_equity_beta",
                flagged=False,
                assessment_status="unavailable",
                severity=None,
                fact="5Y equity beta is not available.",
                interpretation="Hidden equity beta cannot be assessed without factor beta evidence.",
                next_test="Regenerate stress_report with factor_betas_5y.",
                limitation="Beta is historical and can change when correlations or holdings change.",
                evidence={},
                thresholds=eq_thresh,
            )
        )
    elif eq_sev:
        items.append(
            _hidden_risk_assessment(
                category="hidden_equity_beta",
                flagged=True,
                assessment_status="flagged",
                severity=eq_sev,
                fact=f"5Y equity beta is {_fmt_num(beta_eq)} (above {_fmt_num(XRAY_THRESHOLDS['equity_beta_moderate_abs'])} moderate threshold).",
                interpretation="The portfolio has meaningful equity-market sensitivity even if holdings labels look diversified.",
                next_test="Check equity_shock, recession_severe, and downside equity behavior.",
                limitation="Beta is historical and can change when correlations or holdings change.",
                evidence={"beta_key": "beta_eq", "value": beta_eq},
                thresholds=eq_thresh,
            )
        )
    else:
        items.append(
            _hidden_risk_assessment(
                category="hidden_equity_beta",
                flagged=False,
                assessment_status="below_threshold",
                severity=None,
                fact=f"5Y equity beta is {_fmt_num(beta_eq)}; below moderate threshold {_fmt_num(XRAY_THRESHOLDS['equity_beta_moderate_abs'])}.",
                interpretation="Equity beta is present but does not cross hidden-equity-beta concentration rules.",
                next_test="Still review equity stress scenarios if allocation looks defensive.",
                limitation="Below-threshold beta does not eliminate equity drawdown risk.",
                evidence={"beta_key": "beta_eq", "value": beta_eq},
                thresholds=eq_thresh,
            )
        )

    duration_weight = _taxonomy_weight_by_predicate(
        weights,
        taxonomy_rows,
        lambda row: str(row.get("duration_bucket") or "none").lower() not in {"", "none", "short"},
    )
    dur_thresh = ["duration_weight_high"]
    if duration_weight >= XRAY_THRESHOLDS["duration_weight_high"]:
        items.append(
            _hidden_risk_assessment(
                category="duration_concentration",
                flagged=True,
                assessment_status="flagged",
                severity="medium",
                fact=f"Intermediate/long duration-labeled holdings are {_fmt_pct(duration_weight)} of capital.",
                interpretation="The portfolio may be sensitive to rates and duration shocks beyond broad asset labels.",
                next_test="Check rates_shock, real-rate beta, and stress RC contribution from bond holdings.",
                limitation="Duration bucket is taxonomy metadata, not a live duration estimate.",
                evidence={"duration_labeled_weight": duration_weight},
                thresholds=dur_thresh,
            )
        )
    else:
        items.append(
            _hidden_risk_assessment(
                category="duration_concentration",
                flagged=False,
                assessment_status="below_threshold",
                severity=None,
                fact=f"Duration-labeled weight is {_fmt_pct(duration_weight)}; below {_fmt_pct(XRAY_THRESHOLDS['duration_weight_high'])} threshold.",
                interpretation="Taxonomy does not show heavy intermediate/long duration concentration.",
                next_test="Confirm live duration if fixed income is material.",
                limitation="Taxonomy duration buckets are not live duration estimates.",
                evidence={"duration_labeled_weight": duration_weight},
                thresholds=dur_thresh,
            )
        )

    credit_weight = _taxonomy_weight_by_predicate(
        weights,
        taxonomy_rows,
        lambda row: _risk_budget_bucket(row) == "credit" or str(row.get("main_risk_factor") or "") == "credit",
    )
    credit_thresh = ["credit_weight_high"]
    if credit_weight >= XRAY_THRESHOLDS["credit_weight_high"]:
        items.append(
            _hidden_risk_assessment(
                category="credit_concentration",
                flagged=True,
                assessment_status="flagged",
                severity="medium",
                fact=f"Credit-labeled exposure is {_fmt_pct(credit_weight)} of capital.",
                interpretation="Credit carry or spread risk may be a hidden driver of drawdown behavior.",
                next_test="Check credit_shock, recession_severe, and liquidity_shock scenario losses.",
                limitation="Credit taxonomy is a label-level diagnostic and not a full holdings look-through.",
                evidence={"credit_labeled_weight": credit_weight},
                thresholds=credit_thresh,
            )
        )
    else:
        items.append(
            _hidden_risk_assessment(
                category="credit_concentration",
                flagged=False,
                assessment_status="below_threshold",
                severity=None,
                fact=f"Credit-labeled weight is {_fmt_pct(credit_weight)}; below {_fmt_pct(XRAY_THRESHOLDS['credit_weight_high'])} threshold.",
                interpretation="Credit-labeled capital concentration is not elevated under X-Ray rules.",
                next_test="Review credit factor beta and credit stress scenarios if HY/IG holdings exist.",
                limitation="Low labeled credit weight does not remove spread or default risk.",
                evidence={"credit_labeled_weight": credit_weight},
                thresholds=credit_thresh,
            )
        )

    liquidity_weight = _liquidity_labeled_weight(weights, taxonomy_rows)
    liq_thresh = ["liquidity_risk_weight_high"]
    if liquidity_weight >= XRAY_THRESHOLDS["liquidity_risk_weight_high"]:
        items.append(
            _hidden_risk_assessment(
                category="liquidity_concentration",
                flagged=True,
                assessment_status="flagged",
                severity="medium",
                fact=f"Liquidity-labeled holdings are {_fmt_pct(liquidity_weight)} of capital.",
                interpretation="Liquidity-sensitive holdings may amplify stress in risk-off episodes.",
                next_test="Review liquidity_shock scenario loss and holding-level liquidity metadata.",
                limitation="Liquidity labels are taxonomy-based, not live market liquidity scores.",
                evidence={"liquidity_labeled_weight": liquidity_weight},
                thresholds=liq_thresh,
            )
        )
    else:
        items.append(
            _hidden_risk_assessment(
                category="liquidity_concentration",
                flagged=False,
                assessment_status="below_threshold",
                severity=None,
                fact=f"Liquidity-labeled weight is {_fmt_pct(liquidity_weight)}; below {_fmt_pct(XRAY_THRESHOLDS['liquidity_risk_weight_high'])} threshold.",
                interpretation="Liquidity-labeled concentration is not elevated under taxonomy rules.",
                next_test="Still review liquidity_shock if holdings are illiquid in practice.",
                limitation="Absence of a liquidity label does not guarantee market liquidity.",
                evidence={"liquidity_labeled_weight": liquidity_weight},
                thresholds=liq_thresh,
            )
        )

    pca_cov = _pca_raw_covariance(stress_report)
    pc1 = _as_float(pca_cov.get("pc1_explained_variance_ratio"))
    pca_thresh = ["pca_pc1_moderate", "pca_pc1_high"]
    pc1_sev = _severity_share(pc1, XRAY_THRESHOLDS["pca_pc1_moderate"], XRAY_THRESHOLDS["pca_pc1_high"])
    if pc1 is None:
        items.append(
            _hidden_risk_assessment(
                category="correlation_or_common_factor_concentration",
                flagged=False,
                assessment_status="unavailable",
                severity=None,
                fact="Raw covariance PCA PC1 is not available.",
                interpretation="Common-factor concentration cannot be assessed from raw PCA.",
                next_test="Regenerate stress_report.portfolio_pca.raw.",
                limitation="PCA requires sufficient aligned weekly return history.",
                evidence={},
                thresholds=pca_thresh,
            )
        )
    elif pc1_sev:
        items.append(
            _hidden_risk_assessment(
                category="correlation_or_common_factor_concentration",
                flagged=True,
                assessment_status="flagged",
                severity=pc1_sev,
                fact=f"Raw covariance PCA PC1 explains {_fmt_pct(pc1)} of asset-return variance.",
                interpretation="Several holdings may be driven by the same statistical risk direction.",
                next_test="Review PCA loadings, raw correlation PCA, and residual PCA after factor removal.",
                limitation="PCA is statistical and does not identify a tradable economic factor by itself.",
                evidence={"pca_layer": "raw", "pc1_explained_variance_ratio": pc1},
                thresholds=pca_thresh,
            )
        )
    else:
        items.append(
            _hidden_risk_assessment(
                category="correlation_or_common_factor_concentration",
                flagged=False,
                assessment_status="below_threshold",
                severity=None,
                fact=f"Raw PCA PC1 explains {_fmt_pct(pc1)}; below moderate threshold {_fmt_pct(XRAY_THRESHOLDS['pca_pc1_moderate'])}.",
                interpretation="Raw return co-movement is not dominated by a single statistical direction.",
                next_test="Compare with residual PCA after named factors are removed.",
                limitation="Low raw PC1 does not guarantee diversification in stress regimes.",
                evidence={"pca_layer": "raw", "pc1_explained_variance_ratio": pc1},
                thresholds=pca_thresh,
            )
        )

    residual_pca = _pca_residual_covariance(stress_report)
    residual_pc1 = _as_float(residual_pca.get("pc1_explained_variance_ratio"))
    res_pca_thresh = ["pca_pc1_moderate", "pca_pc1_high"]
    res_pc1_sev = _severity_share(
        residual_pc1,
        XRAY_THRESHOLDS["pca_pc1_moderate"],
        XRAY_THRESHOLDS["pca_pc1_high"],
    )
    if residual_pc1 is None:
        items.append(
            _hidden_risk_assessment(
                category="residual_pca_concentration",
                flagged=False,
                assessment_status="unavailable",
                severity=None,
                fact="Residual PCA PC1 is not available (factor-adjusted returns missing or insufficient).",
                interpretation="Idiosyncratic co-movement after factors cannot be assessed.",
                next_test="Ensure portfolio_pca.residual is populated in stress_report.",
                limitation="Residual PCA depends on factor return history and asset coverage.",
                evidence={},
                thresholds=res_pca_thresh,
            )
        )
    elif res_pc1_sev:
        items.append(
            _hidden_risk_assessment(
                category="residual_pca_concentration",
                flagged=True,
                assessment_status="flagged",
                severity=res_pc1_sev,
                fact=f"Residual PCA PC1 explains {_fmt_pct(residual_pc1)} of factor-adjusted return variance.",
                interpretation="After named factors, holdings may still share a common residual direction.",
                next_test="Review residual PCA loadings and unexplained factor residual share.",
                limitation="Residual PCA is model-dependent on the factor set used.",
                evidence={"pca_layer": "residual", "pc1_explained_variance_ratio": residual_pc1},
                thresholds=res_pca_thresh,
            )
        )
    else:
        items.append(
            _hidden_risk_assessment(
                category="residual_pca_concentration",
                flagged=False,
                assessment_status="below_threshold",
                severity=None,
                fact=f"Residual PCA PC1 explains {_fmt_pct(residual_pc1)}; below moderate threshold.",
                interpretation="Factor-adjusted returns do not show a dominant residual common direction.",
                next_test="Cross-check factor_variance_decomposition residual share.",
                limitation="Low residual PC1 does not eliminate asset-specific risk.",
                evidence={"pca_layer": "residual", "pc1_explained_variance_ratio": residual_pc1},
                thresholds=res_pca_thresh,
            )
        )

    hedge_weight, hedge_tickers = _hedge_labeled_weight_and_tickers(weights, taxonomy_rows)
    hedge_stress = _weak_hedge_stress_evidence(stress_report, hedge_tickers)
    oos = (stress_report or {}).get("factor_beta_shock_oos") if isinstance(stress_report, dict) else None
    oos_summary = oos.get("summary") if isinstance(oos, dict) else {}
    oos_mae = _as_float((oos_summary or {}).get("mean_abs_error_5y")) if isinstance(oos_summary, dict) else None
    failing_hedges = hedge_stress.get("hedge_assets_negative_with_portfolio_loss") or []
    weak_hedge_thresh = ["weak_hedge_oos_mae_moderate", "weak_hedge_oos_mae_high"]
    weak_hedge_flag = False
    weak_sev: str | None = None
    if oos_mae is not None:
        weak_sev = _severity_share(
            oos_mae,
            XRAY_THRESHOLDS["weak_hedge_oos_mae_moderate"],
            XRAY_THRESHOLDS["weak_hedge_oos_mae_high"],
        )
        if weak_sev:
            weak_hedge_flag = True
    if failing_hedges and hedge_weight >= 0.10:
        weak_hedge_flag = True
        weak_sev = weak_sev or "medium"
    if hedge_weight <= 0 and oos_mae is None:
        items.append(
            _hidden_risk_assessment(
                category="weak_hedge_behavior",
                flagged=False,
                assessment_status="unavailable",
                severity=None,
                fact="No hedge-labeled holdings and no factor OOS explainability summary.",
                interpretation="Weak hedge behavior cannot be assessed without hedge labels or OOS episodes.",
                next_test="Tag defensive/crisis holdings in taxonomy or regenerate factor_beta_shock_oos.",
                limitation="Hedge behavior is scenario-specific and label-dependent.",
                evidence={"hedge_labeled_weight": hedge_weight},
                thresholds=weak_hedge_thresh,
            )
        )
    elif weak_hedge_flag:
        fact_parts = []
        if failing_hedges:
            names = ", ".join(row["ticker"] for row in failing_hedges[:3])
            fact_parts.append(
                f"hedge-labeled assets ({names}) did not offset portfolio loss in worst scenario "
                f"{hedge_stress.get('worst_scenario_id', 'n/a')}"
            )
        if oos_mae is not None:
            fact_parts.append(f"factor OOS mean absolute error (5Y beta) is {_fmt_pct(oos_mae)}")
        items.append(
            _hidden_risk_assessment(
                category="weak_hedge_behavior",
                flagged=True,
                assessment_status="flagged",
                severity=weak_sev or "medium",
                fact="; ".join(fact_parts) + "." if fact_parts else "Weak hedge behavior detected.",
                interpretation="Defensive or hedge-labeled sleeves may not provide expected crisis offset.",
                next_test="Review historical episodes, hedge asset stress PnL, and crisis_hedge role coverage.",
                limitation="Hedge labels and factor OOS tests are approximations, not live hedge effectiveness.",
                evidence={
                    "hedge_labeled_weight": hedge_weight,
                    "hedge_tickers": hedge_tickers,
                    **hedge_stress,
                    "mean_abs_error_5y": oos_mae,
                },
                thresholds=weak_hedge_thresh,
            )
        )
    else:
        items.append(
            _hidden_risk_assessment(
                category="weak_hedge_behavior",
                flagged=False,
                assessment_status="below_threshold",
                severity=None,
                fact=(
                    f"Hedge-labeled weight {_fmt_pct(hedge_weight)}; "
                    f"OOS MAE {_fmt_pct(oos_mae) if oos_mae is not None else 'n/a'}; "
                    "no hedge-labeled asset failed to offset worst-scenario portfolio loss."
                ),
                interpretation="Available hedge and OOS evidence does not show weak hedge behavior under rules.",
                next_test="Stress-test recession and equity crash scenarios for hedge sleeves.",
                limitation="Historical OOS fit does not guarantee future hedge performance.",
                evidence={
                    "hedge_labeled_weight": hedge_weight,
                    "hedge_tickers": hedge_tickers,
                    "mean_abs_error_5y": oos_mae,
                    **hedge_stress,
                },
                thresholds=weak_hedge_thresh,
            )
        )

    tail = portfolio_analytics.get("tail_risk") if isinstance(portfolio_analytics, dict) else None
    tail = tail if isinstance(tail, dict) else {}
    es95 = _as_float(tail.get("es_95"))
    tail_avail = bool(tail.get("metric_available"))
    tail_thresh = ["es_95_moderate", "es_95_high"]
    tail_sev = None
    if es95 is not None:
        tail_sev = "high" if es95 <= XRAY_THRESHOLDS["es_95_high"] else (
            "medium" if es95 <= XRAY_THRESHOLDS["es_95_moderate"] else None
        )
    if not tail_avail and es95 is None:
        items.append(
            _hidden_risk_assessment(
                category="tail_risk",
                flagged=False,
                assessment_status="unavailable",
                severity=None,
                fact="Daily historical tail risk (VaR/ES) is not available.",
                interpretation="Tail risk concentration cannot be assessed without tail_risk analytics.",
                next_test="Run report pipeline with daily return panel for portfolio_analytics.tail_risk.",
                limitation="Tail metrics depend on return frequency and window disclosure.",
                evidence={},
                thresholds=tail_thresh,
            )
        )
    elif tail_sev:
        items.append(
            _hidden_risk_assessment(
                category="tail_risk",
                flagged=True,
                assessment_status="flagged",
                severity=tail_sev,
                fact=(
                    f"Daily historical ES95 is {_fmt_pct(es95)} "
                    f"({tail.get('method', 'historical')}, {tail.get('frequency', 'daily')}, "
                    f"window {tail.get('window_label') or tail.get('window_months') or 'n/a'})."
                ),
                interpretation="Left-tail loss magnitude is elevated relative to configured ES thresholds.",
                next_test="Review tail_risk block, stress worst-case loss, and drawdown metrics together.",
                limitation="Historical VaR/ES is backward-looking and not a forecast.",
                evidence={
                    "es_95": es95,
                    "var_95": tail.get("var_95"),
                    "method": tail.get("method"),
                    "frequency": tail.get("frequency"),
                    "window_label": tail.get("window_label"),
                    "n_obs": tail.get("n_obs"),
                },
                thresholds=tail_thresh,
            )
        )
    else:
        items.append(
            _hidden_risk_assessment(
                category="tail_risk",
                flagged=False,
                assessment_status="below_threshold",
                severity=None,
                fact=(
                    f"Daily historical ES95 is {_fmt_pct(es95)}; "
                    f"above moderate tail threshold {_fmt_pct(XRAY_THRESHOLDS['es_95_moderate'])}."
                ),
                interpretation="Configured daily ES thresholds are not crossed.",
                next_test="Still review stress tail scenarios and max drawdown.",
                limitation="Below-threshold ES does not eliminate crisis tail risk.",
                evidence={"es_95": es95, "metric_available": tail_avail},
                thresholds=tail_thresh,
            )
        )

    worst = _scenario_by_worst_loss(stress_report)
    worst_top1 = _as_float(worst.get("top1_rc_pct")) if isinstance(worst, dict) else None
    stress_rc_thresh = ["stress_top1_rc_moderate", "stress_top1_rc_high"]
    stress_rc_sev = _severity_share(
        worst_top1,
        XRAY_THRESHOLDS["stress_top1_rc_moderate"],
        XRAY_THRESHOLDS["stress_top1_rc_high"],
    )
    if worst_top1 is None or not isinstance(worst, dict):
        items.append(
            _hidden_risk_assessment(
                category="stress_loss_contributor_concentration",
                flagged=False,
                assessment_status="unavailable",
                severity=None,
                fact="Worst-scenario stress RC concentration is not available.",
                interpretation="Stress loss contributor concentration cannot be assessed.",
                next_test="Regenerate stress_report scenario_results with top1_rc fields.",
                limitation="Stress RC is scenario-specific diagnostics.",
                evidence={},
                thresholds=stress_rc_thresh,
            )
        )
    elif stress_rc_sev:
        items.append(
            _hidden_risk_assessment(
                category="stress_loss_contributor_concentration",
                flagged=True,
                assessment_status="flagged",
                severity=stress_rc_sev,
                fact=(
                    f"In worst scenario {worst.get('scenario_id')}, top stress RC asset "
                    f"{worst.get('top1_rc_asset')} is {_fmt_pct(worst_top1)}."
                ),
                interpretation="Stress losses may be dominated by a small number of assets.",
                next_test="Inspect pnl_by_asset_pct and Top3 RC for the worst stress scenario.",
                limitation="Synthetic stress RC uses scenario covariance diagnostics and is not a pass/fail gate.",
                evidence={
                    "scenario_id": worst.get("scenario_id"),
                    "top1_rc_asset": worst.get("top1_rc_asset"),
                    "top1_rc_pct": worst_top1,
                },
                thresholds=stress_rc_thresh,
            )
        )
    else:
        items.append(
            _hidden_risk_assessment(
                category="stress_loss_contributor_concentration",
                flagged=False,
                assessment_status="below_threshold",
                severity=None,
                fact=(
                    f"Worst-scenario top1 stress RC is {_fmt_pct(worst_top1)} "
                    f"({worst.get('scenario_id')}); below moderate threshold."
                ),
                interpretation="Stress loss contribution is not highly concentrated in one asset.",
                next_test="Review Top3 RC and asset PnL vectors in severe scenarios.",
                limitation="Low concentration in one scenario does not rule out joint stress.",
                evidence={"scenario_id": worst.get("scenario_id"), "top1_rc_pct": worst_top1},
                thresholds=stress_rc_thresh,
            )
        )

    dom_factor, dom_share = _dominant_factor_variance_share(stress_report)
    max_beta_key, max_beta_abs = _max_abs_factor_beta(betas)
    macro_thresh = [
        "factor_beta_moderate_abs",
        "factor_beta_high_abs",
        "macro_dominant_variance_share_moderate",
        "macro_dominant_variance_share_high",
    ]
    macro_flag = False
    macro_sev: str | None = None
    if max_beta_abs is not None:
        macro_sev = _severity_high(
            max_beta_abs,
            XRAY_THRESHOLDS["factor_beta_moderate_abs"],
            XRAY_THRESHOLDS["factor_beta_high_abs"],
        )
        if macro_sev:
            macro_flag = True
    if dom_share is not None:
        share_sev = _severity_share(
            dom_share,
            XRAY_THRESHOLDS["macro_dominant_variance_share_moderate"],
            XRAY_THRESHOLDS["macro_dominant_variance_share_high"],
        )
        if share_sev:
            macro_flag = True
            macro_sev = macro_sev or share_sev
    residual_share = _factor_residual_share(stress_report)
    if not betas and dom_share is None:
        items.append(
            _hidden_risk_assessment(
                category="macro_factor_dependency",
                flagged=False,
                assessment_status="unavailable",
                severity=None,
                fact="Factor betas and variance decomposition are not available.",
                interpretation="Macro/factor dependency cannot be assessed.",
                next_test="Regenerate factor_betas_5y and factor_variance_decomposition.",
                limitation="Factor dependency is model- and window-dependent.",
                evidence={},
                thresholds=macro_thresh,
            )
        )
    elif macro_flag:
        items.append(
            _hidden_risk_assessment(
                category="macro_factor_dependency",
                flagged=True,
                assessment_status="flagged",
                severity=macro_sev or "medium",
                fact=(
                    f"Largest |beta| is {max_beta_key}={_fmt_num(max_beta_abs)}; "
                    f"dominant variance share {dom_factor or 'n/a'}={_fmt_pct(dom_share)}; "
                    f"residual share {_fmt_pct(residual_share)}."
                ),
                interpretation="Portfolio behavior may be driven by a small set of macro/factor exposures.",
                next_test="Review factor exposure section, factor stress history, and residual risk.",
                limitation="Factor maps are linear approximations and may miss regime shifts.",
                evidence={
                    "max_abs_beta_key": max_beta_key,
                    "max_abs_beta": max_beta_abs,
                    "dominant_factor": dom_factor,
                    "dominant_variance_share": dom_share,
                    "residual_share": residual_share,
                },
                thresholds=macro_thresh,
            )
        )
    else:
        items.append(
            _hidden_risk_assessment(
                category="macro_factor_dependency",
                flagged=False,
                assessment_status="below_threshold",
                severity=None,
                fact=(
                    f"Max |beta| {max_beta_key}={_fmt_num(max_beta_abs)}; "
                    f"dominant variance share {_fmt_pct(dom_share)} below moderate thresholds."
                ),
                interpretation="Named macro factors do not dominate under current beta/variance rules.",
                next_test="Still review factor stress scenarios and residual PCA.",
                limitation="Low measured dependency does not remove macro regime risk.",
                evidence={
                    "max_abs_beta_key": max_beta_key,
                    "max_abs_beta": max_beta_abs,
                    "dominant_factor": dom_factor,
                    "dominant_variance_share": dom_share,
                    "residual_share": residual_share,
                },
                thresholds=macro_thresh,
            )
        )

    top_rc = _rc_items(rc_asset, limit=1)
    top_rc_value = top_rc[0]["value"] if top_rc else None
    rc_thresh = ["top1_rc_moderate", "top1_rc_high"]
    rc_sev = _severity_share(
        top_rc_value,
        XRAY_THRESHOLDS["top1_rc_moderate"],
        XRAY_THRESHOLDS["top1_rc_high"],
    )
    if top_rc_value is None or not top_rc:
        items.append(
            _hidden_risk_assessment(
                category="single_asset_risk_concentration",
                flagged=False,
                assessment_status="unavailable",
                severity=None,
                fact="Top1 RC_vol is not available.",
                interpretation="Single-asset risk concentration cannot be assessed.",
                next_test="Provide rc_vol CSV or snapshot RC_asset evidence.",
                limitation="RC_vol depends on covariance window and weighting.",
                evidence={},
                thresholds=rc_thresh,
            )
        )
    elif rc_sev:
        items.append(
            _hidden_risk_assessment(
                category="single_asset_risk_concentration",
                flagged=True,
                assessment_status="flagged",
                severity=rc_sev,
                fact=f"{top_rc[0]['ticker']} contributes {_fmt_pct(top_rc_value)} of RC_vol.",
                interpretation="Portfolio risk is more concentrated than capital weights alone imply.",
                next_test="Compare weight vs RC_vol and inspect stress Top1/Top3 RC concentration.",
                limitation="RC_vol depends on the selected covariance window and existing RC calculation.",
                evidence={"ticker": top_rc[0]["ticker"], "rc_vol": top_rc_value},
                thresholds=rc_thresh,
            )
        )
    else:
        items.append(
            _hidden_risk_assessment(
                category="single_asset_risk_concentration",
                flagged=False,
                assessment_status="below_threshold",
                severity=None,
                fact=(
                    f"Top1 RC_vol is {_fmt_pct(top_rc_value)} ({top_rc[0]['ticker']}); "
                    f"below moderate threshold {_fmt_pct(XRAY_THRESHOLDS['top1_rc_moderate'])}."
                ),
                interpretation="Volatility risk is not dominated by a single asset under RC rules.",
                next_test="Review risk budget view for multi-asset gaps.",
                limitation="Low Top1 RC does not guarantee balanced stress behavior.",
                evidence={"ticker": top_rc[0]["ticker"], "rc_vol": top_rc_value},
                thresholds=rc_thresh,
            )
        )

    if not isinstance(stress_report, dict):
        warnings.append("stress_report is missing")
    if not top_rc:
        warnings.append("RC_vol is missing")

    evaluable = sum(1 for row in items if row.get("assessment_status") != "unavailable")
    unavailable_count = sum(1 for row in items if row.get("assessment_status") == "unavailable")
    flagged_count = sum(1 for row in items if row.get("flagged"))
    below_threshold_count = sum(1 for row in items if row.get("assessment_status") == "below_threshold")

    section = _section(
        items=items,
        data_sources_used=[
            "stress_report.factor_betas_5y",
            "stress_report.portfolio_pca",
            "stress_report.factor_variance_decomposition",
            "stress_report.factor_beta_shock_oos",
            "stress_report.scenario_results",
            "portfolio_analytics.tail_risk",
            "RC_vol evidence",
            "taxonomy metadata",
        ],
        warnings=warnings,
        limitations=[
            "Hidden risk flags are transparent threshold rules, not AI judgment and not portfolio recommendations.",
            "Each category reports flagged, below-threshold, or unavailable evidence; absence of a flag is not proof of safety.",
        ],
        unavailable_warning="No hidden-risk diagnostic inputs were available.",
    )
    section["confidence"] = _hidden_risk_section_confidence(
        evaluable=evaluable,
        unavailable=unavailable_count,
    )
    section["evidence_count"] = evaluable
    section["flagged_count"] = flagged_count
    section["below_threshold_count"] = below_threshold_count
    section["unavailable_count"] = unavailable_count
    return section


def _weight_by_dimension(section: dict[str, Any], dimension: str) -> dict[str, float]:
    for item in section.get("items") or []:
        if item.get("type") == "breakdown" and item.get("dimension") == dimension:
            return {str(row.get("name")): float(row.get("weight") or 0.0) for row in item.get("values") or []}
    return {}


def _weakness_rows_by_risk(weakness_map_section: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for item in (weakness_map_section or {}).get("items") or []:
        if item.get("type") != "weakness":
            continue
        risk = str(item.get("risk") or "").strip()
        if risk:
            rows[risk] = item
    return rows


def _build_archetype_scorecard(
    *,
    allocation_section: dict[str, Any],
    rc_asset: Any,
    stress_report: dict[str, Any] | None,
    weakness_map_section: dict[str, Any] | None,
    portfolio_metrics: dict[str, Any] | None,
    portfolio_analytics: dict[str, Any] | None,
    hidden_risk_section: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    asset_class_weights = _weight_by_dimension(allocation_section, "asset_class")
    risk_bucket_weights = _weight_by_dimension(allocation_section, "risk_bucket")
    main_factor_weights = _weight_by_dimension(allocation_section, "main_risk_factor")
    betas = _factor_betas(stress_report, "factor_betas_5y") or _factor_betas(stress_report, "factor_betas")
    beta_eq = abs(betas.get("beta_eq", 0.0) or 0.0)
    beta_rr = abs(betas.get("beta_rr", 0.0) or 0.0)
    beta_credit = abs(betas.get("beta_credit", 0.0) or 0.0)
    beta_inf = abs(betas.get("beta_inf", 0.0) or 0.0)
    beta_cmd = abs(betas.get("beta_cmd", 0.0) or 0.0)
    top_rc_value = float((_rc_items(rc_asset, limit=1) or [{"value": 0.0}])[0]["value"])
    pc1 = _as_float(_pca_raw_covariance(stress_report).get("pc1_explained_variance_ratio")) or 0.0
    equity_weight = float(asset_class_weights.get("equity", 0.0))
    fixed_income_weight = float(asset_class_weights.get("fixed_income", 0.0))
    commodity_weight = float(asset_class_weights.get("commodity", 0.0))
    cash_weight = float(asset_class_weights.get("cash", 0.0))
    credit_weight = float(risk_bucket_weights.get("credit", 0.0) + main_factor_weights.get("credit", 0.0))
    inflation_weight = float(
        risk_bucket_weights.get("inflation_linked", 0.0) + main_factor_weights.get("inflation", 0.0)
    )
    weakness_by_risk = _weakness_rows_by_risk(weakness_map_section)
    tail = (portfolio_analytics or {}).get("tail_risk") if isinstance(portfolio_analytics, dict) else {}
    es_95 = _as_float((portfolio_analytics or {}).get("es_95"))
    if es_95 is None and isinstance(tail, dict):
        es_95 = _as_float(tail.get("es_95"))
    max_drawdown = _as_float((portfolio_metrics or {}).get("max_drawdown"))
    hidden_flagged = {
        str(row.get("name"))
        for row in (hidden_risk_section or {}).get("items") or []
        if row.get("flagged") is True and row.get("name")
    }

    def weakness_tension_lines(archetype: str) -> list[str]:
        lines: list[str] = []
        for risk in ARCHETYPE_WEAKNESS_TENSIONS.get(archetype, ()):
            row = weakness_by_risk.get(risk)
            if not row:
                continue
            if not row.get("adverse_evidence"):
                continue
            severity = str(row.get("severity") or "low")
            if severity not in {"medium", "high"}:
                continue
            lines.append(
                f"weakness map flags {severity} {risk.replace('_', ' ')} vulnerability "
                f"despite {archetype.lower()} characteristics"
            )
        return lines

    def row(archetype: str, strength: float, positive: list[str], negative: list[str]) -> dict[str, Any]:
        negative = list(negative) + weakness_tension_lines(archetype)
        if strength <= 0 and not positive and not negative:
            return {
                "archetype": archetype,
                "strength": 0.0,
                "positive_evidence": [],
                "negative_evidence": negative,
            }
        return {
            "archetype": archetype,
            "strength": round(float(strength), 4),
            "positive_evidence": positive,
            "negative_evidence": negative,
        }

    scorecard: list[dict[str, Any]] = []

    eq_pos: list[str] = []
    eq_neg: list[str] = []
    eq_strength = 0.0
    if equity_weight >= XRAY_THRESHOLDS["archetype_equity_weight_high"]:
        eq_pos.append(
            f"equity capital weight {_fmt_pct(equity_weight)} is at or above "
            f"{_fmt_pct(XRAY_THRESHOLDS['archetype_equity_weight_high'])}"
        )
        eq_strength = max(eq_strength, equity_weight)
    if beta_eq >= XRAY_THRESHOLDS["equity_beta_high_abs"]:
        eq_pos.append(
            f"equity factor beta {_fmt_num(beta_eq)} is at or above "
            f"{_fmt_num(XRAY_THRESHOLDS['equity_beta_high_abs'])}"
        )
        eq_strength = max(eq_strength, beta_eq)
    if fixed_income_weight >= XRAY_THRESHOLDS["archetype_fixed_income_weight_high"]:
        eq_neg.append(f"high fixed income weight {_fmt_pct(fixed_income_weight)} dilutes pure equity-growth profile")
    if beta_eq < XRAY_THRESHOLDS["equity_beta_moderate_abs"]:
        eq_neg.append(f"equity beta {_fmt_num(beta_eq)} is below moderate equity sensitivity")
    scorecard.append(row("Equity Growth Portfolio", eq_strength, eq_pos, eq_neg))

    bal_pos: list[str] = []
    bal_neg: list[str] = []
    bal_strength = 0.0
    eq_min = XRAY_THRESHOLDS["archetype_balanced_equity_min"]
    eq_max = XRAY_THRESHOLDS["archetype_balanced_equity_max"]
    fi_min = XRAY_THRESHOLDS["archetype_balanced_fixed_income_min"]
    if eq_min <= equity_weight <= eq_max and fixed_income_weight >= fi_min:
        bal_pos.append(
            f"equity {_fmt_pct(equity_weight)} and fixed income {_fmt_pct(fixed_income_weight)} "
            "sit in a balanced capital mix band"
        )
        bal_strength = min(equity_weight, fixed_income_weight) + 0.15
    else:
        if equity_weight < eq_min:
            bal_neg.append(f"equity weight {_fmt_pct(equity_weight)} is below balanced lower bound {_fmt_pct(eq_min)}")
        if equity_weight > eq_max:
            bal_neg.append(f"equity weight {_fmt_pct(equity_weight)} exceeds balanced upper bound {_fmt_pct(eq_max)}")
        if fixed_income_weight < fi_min:
            bal_neg.append(
                f"fixed income weight {_fmt_pct(fixed_income_weight)} is below balanced minimum {_fmt_pct(fi_min)}"
            )
    scorecard.append(row("Balanced 60/40-like", bal_strength, bal_pos, bal_neg))

    dur_pos: list[str] = []
    dur_neg: list[str] = []
    dur_strength = 0.0
    if fixed_income_weight >= XRAY_THRESHOLDS["archetype_fixed_income_weight_high"]:
        dur_pos.append(
            f"fixed income weight {_fmt_pct(fixed_income_weight)} is duration-heavy "
            f"(>= {_fmt_pct(XRAY_THRESHOLDS['archetype_fixed_income_weight_high'])})"
        )
        dur_strength = max(dur_strength, fixed_income_weight + 0.05)
    if beta_eq <= XRAY_THRESHOLDS["equity_beta_moderate_abs"]:
        dur_pos.append(f"equity beta {_fmt_num(beta_eq)} is low, consistent with defensive duration profile")
        dur_strength = max(dur_strength, fixed_income_weight if fixed_income_weight else beta_rr)
    else:
        dur_neg.append(f"equity beta {_fmt_num(beta_eq)} is not low enough for a defensive duration read")
    if equity_weight >= XRAY_THRESHOLDS["archetype_equity_weight_high"]:
        dur_neg.append(f"equity weight {_fmt_pct(equity_weight)} is high for a duration-defensive label")
    scorecard.append(row("Duration-heavy Defensive", dur_strength, dur_pos, dur_neg))

    cred_pos: list[str] = []
    cred_neg: list[str] = []
    cred_strength = 0.0
    if credit_weight >= XRAY_THRESHOLDS["credit_weight_high"]:
        cred_pos.append(f"credit-labeled capital weight {_fmt_pct(credit_weight)} is elevated")
        cred_strength = max(cred_strength, credit_weight)
    if beta_credit >= XRAY_THRESHOLDS["factor_beta_moderate_abs"]:
        cred_pos.append(f"credit factor beta {_fmt_num(beta_credit)} is material")
        cred_strength = max(cred_strength, beta_credit)
    if credit_weight < XRAY_THRESHOLDS["credit_weight_high"] * 0.5 and beta_credit < XRAY_THRESHOLDS["factor_beta_moderate_abs"]:
        cred_neg.append("credit capital and factor beta are both modest")
    scorecard.append(row("Credit Carry Portfolio", cred_strength, cred_pos, cred_neg))

    inf_pos: list[str] = []
    inf_neg: list[str] = []
    inf_strength = 0.0
    if commodity_weight >= WEAKNESS_EXPOSURE_WEIGHT_MIN:
        inf_pos.append(f"commodity capital weight {_fmt_pct(commodity_weight)}")
        inf_strength = max(inf_strength, commodity_weight)
    if inflation_weight >= WEAKNESS_EXPOSURE_WEIGHT_MIN:
        inf_pos.append(f"inflation-linked capital weight {_fmt_pct(inflation_weight)}")
        inf_strength = max(inf_strength, inflation_weight)
    if beta_inf >= XRAY_THRESHOLDS["factor_beta_moderate_abs"]:
        inf_pos.append(f"inflation factor beta {_fmt_num(beta_inf)}")
        inf_strength = max(inf_strength, beta_inf)
    if beta_cmd >= XRAY_THRESHOLDS["factor_beta_moderate_abs"]:
        inf_pos.append(f"commodity factor beta {_fmt_num(beta_cmd)}")
        inf_strength = max(inf_strength, beta_cmd)
    if not inf_pos:
        inf_neg.append("no material inflation-linked allocation or inflation/commodity factor beta")
    scorecard.append(row("Inflation-sensitive", inf_strength, inf_pos, inf_neg))

    pseudo_pos: list[str] = []
    pseudo_neg: list[str] = []
    pseudo_strength = 0.0
    if top_rc_value >= XRAY_THRESHOLDS["top1_rc_high"]:
        pseudo_pos.append(f"top RC_vol {_fmt_pct(top_rc_value)} indicates concentration despite many holdings")
        pseudo_strength = max(pseudo_strength, top_rc_value)
    if pc1 >= XRAY_THRESHOLDS["pca_pc1_high"]:
        pseudo_pos.append(f"raw PCA PC1 {_fmt_pct(pc1)} shows common-factor concentration")
        pseudo_strength = max(pseudo_strength, pc1)
    if top_rc_value < XRAY_THRESHOLDS["top1_rc_moderate"] and pc1 < XRAY_THRESHOLDS["pca_pc1_moderate"]:
        pseudo_neg.append("risk is not unusually concentrated in RC_vol or PCA PC1")
    scorecard.append(row("Pseudo-diversified Portfolio", pseudo_strength, pseudo_pos, pseudo_neg))

    def_pos: list[str] = []
    def_neg: list[str] = []
    def_strength = 0.0
    if equity_weight <= XRAY_THRESHOLDS["archetype_defensive_equity_max"]:
        def_pos.append(f"equity weight {_fmt_pct(equity_weight)} is defensive")
        def_strength = max(def_strength, min(0.55, 1.0 - equity_weight))
    if beta_eq <= XRAY_THRESHOLDS["equity_beta_moderate_abs"]:
        def_pos.append(f"equity beta {_fmt_num(beta_eq)} is low")
        def_strength = max(def_strength, 0.5)
    if (
        fixed_income_weight >= XRAY_THRESHOLDS["archetype_balanced_fixed_income_min"]
        and fixed_income_weight < XRAY_THRESHOLDS["archetype_fixed_income_weight_high"]
    ):
        def_pos.append(f"fixed income weight {_fmt_pct(fixed_income_weight)} supports defensive posture")
        def_strength = max(def_strength, fixed_income_weight * 0.8)
    elif fixed_income_weight >= XRAY_THRESHOLDS["archetype_fixed_income_weight_high"]:
        def_neg.append("very high fixed income is better captured by Duration-heavy Defensive than generic Defensive")
    if equity_weight > XRAY_THRESHOLDS["archetype_equity_weight_high"]:
        def_neg.append(f"equity weight {_fmt_pct(equity_weight)} is too high for a defensive read")
    scorecard.append(row("Defensive Portfolio", def_strength, def_pos, def_neg))

    conc_pos: list[str] = []
    conc_neg: list[str] = []
    conc_strength = 0.0
    if top_rc_value >= XRAY_THRESHOLDS["archetype_concentrated_rc_min"]:
        conc_pos.append(f"top RC_vol {_fmt_pct(top_rc_value)} shows concentrated risk budget")
        conc_strength = max(conc_strength, top_rc_value)
    if "single_asset_risk_concentration" in hidden_flagged:
        conc_pos.append("hidden risk detector flags single-asset risk concentration")
        conc_strength = max(conc_strength, top_rc_value)
    if beta_eq >= XRAY_THRESHOLDS["equity_beta_moderate_abs"]:
        conc_pos.append(f"equity beta {_fmt_num(beta_eq)} adds market-beta concentration")
        conc_strength = max(conc_strength, beta_eq * 0.5)
    if top_rc_value < XRAY_THRESHOLDS["top1_rc_moderate"]:
        conc_neg.append(f"top RC_vol {_fmt_pct(top_rc_value)} is not concentrated")
    scorecard.append(row("Concentrated-risk Portfolio", conc_strength, conc_pos, conc_neg))

    tail_pos: list[str] = []
    tail_neg: list[str] = []
    tail_strength = 0.0
    if es_95 is not None and es_95 <= XRAY_THRESHOLDS["es_95_high"]:
        tail_pos.append(f"daily historical ES95 {_fmt_pct(es_95)} is in the high tail-risk band")
        tail_strength = abs(es_95)
    if "tail_risk" in hidden_flagged:
        tail_pos.append("hidden risk detector flags elevated tail risk")
        tail_strength = max(tail_strength, abs(es_95 or XRAY_THRESHOLDS["es_95_high"]))
    if max_drawdown is not None and max_drawdown <= XRAY_THRESHOLDS["max_drawdown_high"]:
        tail_pos.append(f"max drawdown {_fmt_pct(max_drawdown)} is severe")
        tail_strength = max(tail_strength, abs(max_drawdown))
    if es_95 is None and "tail_risk" not in hidden_flagged:
        tail_neg.append("tail ES95 evidence is unavailable")
    scorecard.append(row("Tail-risk Exposed Portfolio", tail_strength, tail_pos, tail_neg))

    cash_pos: list[str] = []
    cash_neg: list[str] = []
    cash_strength = 0.0
    if cash_weight >= XRAY_THRESHOLDS["archetype_cash_weight_high"]:
        cash_pos.append(f"cash capital weight {_fmt_pct(cash_weight)} is high")
        cash_strength = cash_weight
    if (
        cash_weight >= WEAKNESS_EXPOSURE_WEIGHT_MIN
        and beta_eq <= XRAY_THRESHOLDS["equity_beta_moderate_abs"] * 0.5
        and equity_weight <= XRAY_THRESHOLDS["archetype_defensive_equity_max"]
    ):
        cash_pos.append("low equity beta with explicit cash allocation supports a cash-heavy low-risk read")
        cash_strength = max(cash_strength, cash_weight)
    if cash_weight < WEAKNESS_EXPOSURE_WEIGHT_MIN:
        cash_neg.append(f"cash weight {_fmt_pct(cash_weight)} is not material")
    scorecard.append(row("Cash-heavy Low-Risk", cash_strength, cash_pos, cash_neg))

    scorecard.sort(key=lambda x: (-float(x["strength"]), str(x["archetype"])))
    return scorecard


def _archetype_conflicting_signals(
    *,
    primary: dict[str, Any],
    scorecard: list[dict[str, Any]],
    weakness_by_risk: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], str | None]:
    primary_name = str(primary["archetype"])
    primary_strength = float(primary["strength"])
    conflicts: list[dict[str, Any]] = []

    for candidate in scorecard[1:5]:
        name = str(candidate["archetype"])
        strength = float(candidate["strength"])
        if strength < max(0.20, primary_strength - 0.15):
            continue
        conflicts.append(
            {
                "archetype": name,
                "tension": "competing_label",
                "explanation": (
                    f"{name} also scores {_fmt_num(strength)} versus primary {primary_name} "
                    f"at {_fmt_num(primary_strength)}; multiple behavior labels may apply."
                ),
                "positive_evidence": list(candidate.get("positive_evidence") or []),
                "negative_evidence": list(candidate.get("negative_evidence") or []),
            }
        )

    for risk in ARCHETYPE_WEAKNESS_TENSIONS.get(primary_name, ()):
        row = weakness_by_risk.get(risk)
        if not row or not row.get("adverse_evidence"):
            continue
        severity = str(row.get("severity") or "low")
        if severity not in {"medium", "high"}:
            continue
        tension = f"{primary_name.lower().replace(' ', '_')}_vs_{risk}_weakness"
        conflicts.append(
            {
                "archetype": primary_name,
                "tension": tension,
                "explanation": (
                    f"{primary_name} is supported by allocation/factor evidence, but the weakness map "
                    f"shows {severity} {risk.replace('_', ' ')} vulnerability — review both together."
                ),
                "positive_evidence": list(primary.get("positive_evidence") or []),
                "negative_evidence": list(primary.get("negative_evidence") or []),
                "related_weakness": risk,
                "weakness_severity": severity,
            }
        )

    for candidate in scorecard:
        name = str(candidate["archetype"])
        if name == primary_name:
            continue
        neg = candidate.get("negative_evidence") or []
        weakness_lines = [line for line in neg if str(line).startswith("weakness map flags")]
        if not weakness_lines:
            continue
        if float(candidate["strength"]) < max(0.15, primary_strength - 0.25):
            continue
        conflicts.append(
            {
                "archetype": name,
                "tension": "label_vs_regime_tension",
                "explanation": (
                    f"{name} has supporting evidence but simultaneous regime weakness: "
                    f"{weakness_lines[0]}"
                ),
                "positive_evidence": list(candidate.get("positive_evidence") or []),
                "negative_evidence": list(neg),
            }
        )

    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for row in conflicts:
        key = (str(row.get("archetype")), str(row.get("tension")))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)

    summary = None
    if deduped:
        regime = next((r for r in deduped if r.get("related_weakness")), None)
        if regime:
            summary = (
                f"Primary label {primary_name} coexists with {regime.get('weakness_severity')} "
                f"{str(regime.get('related_weakness')).replace('_', ' ')} weakness — "
                "the label describes holdings, not immunity to that regime."
            )
        else:
            summary = (
                f"Primary label {primary_name} has competing archetype signals; "
                "use the scorecard and weakness map together."
            )
    return deduped, summary


def _portfolio_archetype_section(
    *,
    allocation_section: dict[str, Any],
    rc_asset: Any,
    stress_report: dict[str, Any] | None,
    weakness_map_section: dict[str, Any] | None = None,
    portfolio_metrics: dict[str, Any] | None = None,
    portfolio_analytics: dict[str, Any] | None = None,
    hidden_risk_section: dict[str, Any] | None = None,
) -> dict[str, Any]:
    scorecard = _build_archetype_scorecard(
        allocation_section=allocation_section,
        rc_asset=rc_asset,
        stress_report=stress_report,
        weakness_map_section=weakness_map_section,
        portfolio_metrics=portfolio_metrics,
        portfolio_analytics=portfolio_analytics,
        hidden_risk_section=hidden_risk_section,
    )
    ranked = [row for row in scorecard if float(row.get("strength") or 0.0) > 0]
    if not ranked:
        return _section(
            items=[],
            data_sources_used=[
                "asset allocation",
                "factor betas",
                "RC_vol",
                "PCA",
                "weakness map",
                "tail risk",
            ],
            unavailable_warning="No archetype evidence was available.",
        )

    primary = ranked[0]
    secondary = ranked[1] if len(ranked) > 1 else None
    gap = float(primary["strength"]) - float(secondary["strength"] if secondary else 0.0)
    weakness_by_risk = _weakness_rows_by_risk(weakness_map_section)
    conflicting, conflict_summary = _archetype_conflicting_signals(
        primary=primary,
        scorecard=ranked,
        weakness_by_risk=weakness_by_risk,
    )
    tension_count = sum(1 for row in conflicting if row.get("related_weakness"))
    if float(primary["strength"]) < 0.25:
        confidence = "low"
    elif gap >= 0.20 and tension_count == 0:
        confidence = "high"
    elif gap >= 0.10 and tension_count <= 1:
        confidence = "medium"
    else:
        confidence = "low"

    threshold_strength = 0.20
    for row in scorecard:
        strength = float(row.get("strength") or 0.0)
        if row["archetype"] == primary["archetype"]:
            row["fit"] = "primary"
        elif secondary and row["archetype"] == secondary["archetype"]:
            row["fit"] = "secondary"
        elif strength >= threshold_strength:
            row["fit"] = "secondary"
        else:
            row["fit"] = "below_threshold"

    positive_evidence = list(primary.get("positive_evidence") or [])
    negative_evidence = list(primary.get("negative_evidence") or [])
    item = {
        "type": "portfolio_archetype",
        "primary_archetype": primary["archetype"],
        "secondary_archetype": secondary["archetype"] if secondary else None,
        "confidence": confidence,
        "positive_evidence": positive_evidence,
        "negative_evidence": negative_evidence,
        "drivers": positive_evidence,
        "archetype_scorecard": scorecard,
        "conflicting_signals": conflicting,
        "conflict_summary": conflict_summary,
    }
    section = _section(
        items=[item],
        data_sources_used=[
            "asset allocation",
            "factor betas",
            "RC_vol",
            "PCA",
            "weakness map",
            "hidden risk detector",
            "tail risk",
        ],
        limitations=[
            "Archetype is a rule-based behavior label with caveats, not a portfolio selection decision.",
            "A portfolio can have multiple simultaneous characteristics; confidence reflects signal clarity and regime tensions.",
            "Negative evidence and conflicting signals can apply even when a primary label is shown.",
        ],
    )
    section["confidence"] = confidence
    return section


def _loss_severity(loss: float | None) -> str | None:
    if loss is None:
        return None
    if loss <= XRAY_THRESHOLDS["stress_loss_high"]:
        return "high"
    if loss <= XRAY_THRESHOLDS["stress_loss_moderate"]:
        return "medium"
    return "low"


def _max_severity(values: list[str]) -> str:
    order = {"low": 0, "medium": 1, "high": 2}
    best = "low"
    for value in values:
        if order.get(value, 0) > order[best]:
            best = value
    return best


def _invert_string_map(mapping: dict[str, str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for source_key, target in mapping.items():
        out.setdefault(target, []).append(source_key)
    return out


WEAKNESS_SCENARIOS_BY_RISK = _invert_string_map(WEAKNESS_SCENARIO_MAP)
WEAKNESS_FACTOR_KEYS_BY_RISK = _invert_string_map(WEAKNESS_FACTOR_MAP)


def _weakness_keys_for_portfolio(
    *,
    allocation_section: dict[str, Any],
    taxonomy_rows: dict[str, dict[str, Any]] | None,
    weights: dict[str, Any] | None,
) -> tuple[str, ...]:
    keys = list(WEAKNESS_KEYS)
    if _portfolio_has_crypto_exposure(
        allocation_section=allocation_section,
        taxonomy_rows=taxonomy_rows,
        weights=weights,
    ):
        keys.append(WEAKNESS_CRYPTO_KEY)
    return tuple(keys)


def _portfolio_has_crypto_exposure(
    *,
    allocation_section: dict[str, Any],
    taxonomy_rows: dict[str, dict[str, Any]] | None,
    weights: dict[str, Any] | None,
) -> bool:
    crypto_weight = _weight_by_dimension(allocation_section, "asset_class").get("crypto", 0.0)
    if crypto_weight >= WEAKNESS_EXPOSURE_WEIGHT_MIN:
        return True
    crypto_factor_weight = _weight_by_dimension(allocation_section, "main_risk_factor").get("crypto_beta", 0.0)
    if crypto_factor_weight >= WEAKNESS_EXPOSURE_WEIGHT_MIN:
        return True
    weight_map = _positive_weights(weights or {})
    rows = taxonomy_rows or {}
    for ticker in weight_map:
        row = _row_for_ticker(ticker, rows)
        if not row:
            continue
        asset_class = str(row.get("asset_class") or "").strip().lower()
        main_factor = str(row.get("main_risk_factor") or "").strip().lower()
        if asset_class == "crypto" or main_factor == "crypto_beta":
            return True
    return False


def _weakness_exposure_present(
    weakness: str,
    *,
    allocation_section: dict[str, Any],
    betas: dict[str, float],
) -> bool:
    hints = WEAKNESS_EXPOSURE_HINTS.get(weakness) or {}
    asset_class_weights = _weight_by_dimension(allocation_section, "asset_class")
    risk_bucket_weights = _weight_by_dimension(allocation_section, "risk_bucket")
    main_factor_weights = _weight_by_dimension(allocation_section, "main_risk_factor")
    for name in hints.get("asset_class") or ():
        if asset_class_weights.get(name, 0.0) >= WEAKNESS_EXPOSURE_WEIGHT_MIN:
            return True
    for name in hints.get("risk_bucket") or ():
        if risk_bucket_weights.get(name, 0.0) >= WEAKNESS_EXPOSURE_WEIGHT_MIN:
            return True
    for name in hints.get("main_risk_factor") or ():
        if main_factor_weights.get(name, 0.0) >= WEAKNESS_EXPOSURE_WEIGHT_MIN:
            return True
    beta_floor = XRAY_THRESHOLDS["factor_beta_moderate_abs"] * 0.5
    for beta_key in hints.get("factor_beta") or ():
        value = betas.get(beta_key)
        if value is not None and abs(value) >= beta_floor:
            return True
    for item in allocation_section.get("items") or []:
        if item.get("type") != "holding":
            continue
        if str(item.get("asset_class") or "") in (hints.get("asset_class") or ()):
            return True
        if str(item.get("main_risk_factor") or "") in (hints.get("main_risk_factor") or ()):
            return True
        roles = [str(v) for v in (item.get("risk_role") or [])]
        if any(role in (hints.get("risk_role") or ()) for role in roles):
            return True
        secondary = [str(v) for v in (item.get("secondary_risk_factors") or [])]
        if any(tag in (hints.get("secondary_risk_factor") or ()) for tag in secondary):
            return True
    return False


def _weakness_scenario_coverage(
    weakness: str,
    *,
    stress_report: dict[str, Any] | None,
) -> dict[str, Any]:
    mapped = sorted(WEAKNESS_SCENARIOS_BY_RISK.get(weakness) or [])
    present = sorted(
        {
            str(row.get("scenario_id"))
            for row in _stress_scenarios(stress_report)
            if str(row.get("scenario_id") or "") in mapped
        }
    )
    missing = [sid for sid in mapped if sid not in present]
    return {
        "mapped_scenarios": mapped,
        "scenarios_present": present,
        "scenarios_missing": missing,
    }


def _weakness_top_asset_loss_drivers(
    weakness: str,
    *,
    stress_report: dict[str, Any] | None,
    limit: int = 3,
) -> list[dict[str, Any]]:
    mapped = set(WEAKNESS_SCENARIOS_BY_RISK.get(weakness) or [])
    worst_by_ticker: dict[str, dict[str, Any]] = {}
    for row in _stress_scenarios(stress_report):
        scenario_id = str(row.get("scenario_id") or "")
        if scenario_id not in mapped:
            continue
        pnl_by_asset = row.get("pnl_by_asset_pct")
        if not isinstance(pnl_by_asset, dict):
            continue
        for ticker, value in pnl_by_asset.items():
            pnl = _as_float(value)
            if pnl is None:
                continue
            current = worst_by_ticker.get(str(ticker))
            if current is None or pnl < float(current["pnl_pct"]):
                worst_by_ticker[str(ticker)] = {
                    "ticker": str(ticker),
                    "pnl_pct": pnl,
                    "scenario_id": scenario_id,
                    "evidence_type": "stress_asset_pnl",
                }
    drivers = sorted(worst_by_ticker.values(), key=lambda x: (float(x["pnl_pct"]), str(x["ticker"])))
    return drivers[:limit]


def _weakness_top_factor_drivers(
    weakness: str,
    *,
    stress_report: dict[str, Any] | None,
    betas: dict[str, float],
    limit: int = 3,
) -> list[dict[str, Any]]:
    mapped = set(WEAKNESS_SCENARIOS_BY_RISK.get(weakness) or [])
    factor_shorts = set(WEAKNESS_FACTOR_SHORTS.get(weakness) or ())
    for beta_key in WEAKNESS_FACTOR_KEYS_BY_RISK.get(weakness) or ():
        for short_key, bk in _FACTOR_SHORT_TO_BETA_KEY.items():
            if bk == beta_key:
                factor_shorts.add(short_key)
    drivers: dict[str, dict[str, Any]] = {}
    for row in _stress_scenarios(stress_report):
        scenario_id = str(row.get("scenario_id") or "")
        if scenario_id not in mapped:
            continue
        pnl_by_factor = row.get("pnl_by_factor_pct")
        if not isinstance(pnl_by_factor, dict):
            continue
        for factor_short, pnl in pnl_by_factor.items():
            if factor_shorts and str(factor_short) not in factor_shorts:
                continue
            number = _as_float(pnl)
            if number is None:
                continue
            beta_key = _FACTOR_SHORT_TO_BETA_KEY.get(str(factor_short))
            current = drivers.get(str(factor_short))
            if current is None or number < float(current.get("scenario_pnl_pct") or 0.0):
                drivers[str(factor_short)] = {
                    "factor_short": str(factor_short),
                    "beta_key": beta_key,
                    "beta_5y": betas.get(beta_key) if beta_key else None,
                    "scenario_pnl_pct": number,
                    "scenario_id": scenario_id,
                    "evidence_type": "stress_factor_pnl",
                }
    for beta_key in WEAKNESS_FACTOR_KEYS_BY_RISK.get(weakness) or ():
        value = betas.get(beta_key)
        if value is None:
            continue
        short = None
        for short_key, bk in _FACTOR_SHORT_TO_BETA_KEY.items():
            if bk == beta_key:
                short = short_key
                break
        key = short or beta_key
        if key not in drivers:
            drivers[key] = {
                "factor_short": short,
                "beta_key": beta_key,
                "beta_5y": value,
                "scenario_pnl_pct": None,
                "scenario_id": None,
                "evidence_type": "factor_beta_5y",
            }
    def _factor_driver_rank(row: dict[str, Any]) -> tuple[float, float]:
        pnl = _as_float(row.get("scenario_pnl_pct"))
        if pnl is not None:
            return (pnl, 0.0)
        return (0.0, -abs(_as_float(row.get("beta_5y")) or 0.0))

    ranked = sorted(drivers.values(), key=_factor_driver_rank)
    return ranked[:limit]


def _weakness_row_confidence(
    *,
    exposure_present: bool,
    adverse_evidence: bool,
    evidence_count: int,
    missing_inputs: list[str],
) -> str:
    if not exposure_present and not adverse_evidence and evidence_count == 0:
        return "low"
    critical_missing = any(
        "scenario_results" in item or "factor betas" in item for item in missing_inputs
    )
    if adverse_evidence and evidence_count >= 2 and exposure_present and not critical_missing:
        return "high"
    if adverse_evidence and evidence_count >= 1 and exposure_present:
        return "medium"
    if exposure_present or evidence_count >= 1:
        return "medium"
    return "low"


def _collect_weakness_adverse_evidence(
    weakness: str,
    *,
    portfolio_metrics: dict[str, Any] | None,
    portfolio_analytics: dict[str, Any] | None,
    stress_report: dict[str, Any] | None,
    allocation_section: dict[str, Any],
    betas: dict[str, float],
) -> tuple[list[str], list[dict[str, Any]]]:
    severities: list[str] = []
    evidence: list[dict[str, Any]] = []

    for row in _stress_scenarios(stress_report):
        scenario_id = str(row.get("scenario_id") or "")
        if weakness != WEAKNESS_SCENARIO_MAP.get(scenario_id):
            continue
        loss = _as_float(row.get("portfolio_pnl_pct"))
        severity = _loss_severity(loss)
        if severity in ("medium", "high"):
            severities.append(severity)
            evidence.append(
                {
                    "source": "stress_scenario",
                    "evidence_type": "stress_scenario",
                    "scenario_id": scenario_id,
                    "portfolio_pnl_pct": loss,
                    "severity": severity,
                }
            )

    for beta_key in WEAKNESS_FACTOR_KEYS_BY_RISK.get(weakness) or ():
        value = betas.get(beta_key)
        severity = _severity_high(
            value,
            XRAY_THRESHOLDS["factor_beta_moderate_abs"],
            XRAY_THRESHOLDS["factor_beta_high_abs"],
        )
        if severity:
            severities.append(severity)
            evidence.append(
                {
                    "source": "factor_beta",
                    "evidence_type": "factor_beta",
                    "beta_key": beta_key,
                    "value": value,
                    "severity": severity,
                }
            )

    metrics = portfolio_metrics or {}
    analytics = portfolio_analytics or {}
    mdd = _as_float(metrics.get("max_drawdown"))
    if weakness in ("recession", "equity_crash") and mdd is not None and mdd <= XRAY_THRESHOLDS["max_drawdown_moderate"]:
        sev = "high" if mdd <= XRAY_THRESHOLDS["max_drawdown_high"] else "medium"
        severities.append(sev)
        evidence.append(
            {"source": "max_drawdown", "evidence_type": "max_drawdown", "max_drawdown": mdd, "severity": sev}
        )

    tail_es = analytics.get("tail_risk") if isinstance(analytics.get("tail_risk"), dict) else {}
    es95 = _as_float(tail_es.get("es_95") if tail_es else analytics.get("es_95"))
    if (
        weakness in ("recession", "liquidity", "volatility_spike")
        and es95 is not None
        and es95 <= XRAY_THRESHOLDS["es_95_moderate"]
    ):
        sev = "high" if es95 <= XRAY_THRESHOLDS["es_95_high"] else "medium"
        severities.append(sev)
        evidence.append(
            {"source": "historical_es_95", "evidence_type": "historical_tail", "es_95": es95, "severity": sev}
        )

    main_factor_weights = _weight_by_dimension(allocation_section, "main_risk_factor")
    risk_bucket_weights = _weight_by_dimension(allocation_section, "risk_bucket")
    if (
        weakness == "liquidity"
        and main_factor_weights.get("liquidity", 0.0) >= XRAY_THRESHOLDS["liquidity_risk_weight_high"]
    ):
        severities.append("medium")
        evidence.append(
            {
                "source": "taxonomy",
                "evidence_type": "taxonomy_exposure",
                "liquidity_main_risk_factor_weight": main_factor_weights.get("liquidity"),
                "severity": "medium",
            }
        )
    if weakness == "credit" and risk_bucket_weights.get("credit", 0.0) >= XRAY_THRESHOLDS["credit_weight_high"]:
        severities.append("medium")
        evidence.append(
            {
                "source": "taxonomy",
                "evidence_type": "taxonomy_exposure",
                "credit_bucket_weight": risk_bucket_weights.get("credit"),
                "severity": "medium",
            }
        )

    return severities, evidence


def _weakness_map_section(
    *,
    portfolio_metrics: dict[str, Any] | None,
    portfolio_analytics: dict[str, Any] | None,
    stress_report: dict[str, Any] | None,
    allocation_section: dict[str, Any],
    weights: dict[str, Any] | None = None,
    taxonomy_rows: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    betas = _factor_betas(stress_report, "factor_betas_5y") or _factor_betas(stress_report, "factor_betas")
    weakness_keys = _weakness_keys_for_portfolio(
        allocation_section=allocation_section,
        taxonomy_rows=taxonomy_rows,
        weights=weights,
    )
    items: list[dict[str, Any]] = []
    section_missing: list[str] = []

    for weakness in weakness_keys:
        severities, evidence = _collect_weakness_adverse_evidence(
            weakness,
            portfolio_metrics=portfolio_metrics,
            portfolio_analytics=portfolio_analytics,
            stress_report=stress_report,
            allocation_section=allocation_section,
            betas=betas,
        )
        exposure_present = _weakness_exposure_present(
            weakness,
            allocation_section=allocation_section,
            betas=betas,
        )
        adverse_evidence = bool(severities)
        severity = _max_severity(severities) if adverse_evidence else "low"
        scenario_coverage = _weakness_scenario_coverage(weakness, stress_report=stress_report)
        missing_inputs: list[str] = []
        if scenario_coverage["mapped_scenarios"] and scenario_coverage["scenarios_missing"]:
            missing_inputs.append(
                "missing stress scenarios: " + ", ".join(scenario_coverage["scenarios_missing"])
            )
        if not betas and (WEAKNESS_FACTOR_KEYS_BY_RISK.get(weakness) or WEAKNESS_EXPOSURE_HINTS.get(weakness, {}).get("factor_beta")):
            missing_inputs.append("factor betas unavailable for factor-channel checks")
        top_asset_loss_drivers = _weakness_top_asset_loss_drivers(weakness, stress_report=stress_report)
        if scenario_coverage["mapped_scenarios"] and not top_asset_loss_drivers:
            missing_inputs.append("pnl_by_asset_pct missing for mapped stress scenarios")
        top_factor_drivers = _weakness_top_factor_drivers(weakness, stress_report=stress_report, betas=betas)
        confidence = _weakness_row_confidence(
            exposure_present=exposure_present,
            adverse_evidence=adverse_evidence,
            evidence_count=len(evidence),
            missing_inputs=missing_inputs,
        )
        items.append(
            {
                "type": "weakness",
                "risk": weakness,
                "exposure_present": exposure_present,
                "adverse_evidence": adverse_evidence,
                "severity": severity,
                "confidence": confidence,
                "scenario_coverage": scenario_coverage,
                "top_asset_loss_drivers": top_asset_loss_drivers,
                "top_factor_drivers": top_factor_drivers,
                "evidence": evidence
                if evidence
                else [
                    {
                        "source": "available_diagnostics",
                        "evidence_type": "below_threshold",
                        "note": "No adverse evidence crossed configured X-Ray thresholds.",
                    }
                ],
                "missing_inputs": missing_inputs,
                "interpretation": _weakness_interpretation(
                    weakness,
                    exposure_present=exposure_present,
                    adverse_evidence=adverse_evidence,
                    severity=severity,
                ),
            }
        )

    warnings: list[str] = []
    if not _stress_scenarios(stress_report):
        warnings.append("stress scenario rows are missing")
        section_missing.append("stress_report.scenario_results")
    if not betas:
        warnings.append("factor betas are missing")
        section_missing.append("stress_report.factor_betas_5y")
    section = _section(
        items=items,
        data_sources_used=[
            "stress_report.scenario_results",
            "stress_report.factor_betas_5y",
            "snapshot metrics",
            "snapshot analytics",
            "taxonomy metadata",
            "config/etf_universe.yml",
        ],
        warnings=warnings,
        limitations=[
            "Weakness Map aggregates existing evidence only; it is not a forecasting or scoring model.",
            "Low severity with adverse_evidence=false means thresholds were not crossed, not that the risk is absent.",
            "crypto_shock appears only when crypto exposure is present in taxonomy or weights.",
        ],
    )
    if section_missing:
        section["missing_input_warnings"] = section_missing
    return section


def _weakness_interpretation(
    weakness: str,
    *,
    exposure_present: bool,
    adverse_evidence: bool,
    severity: str,
) -> str:
    base = {
        "recession": "recession or hard-landing channels",
        "inflation": "inflation or stagflation pressure",
        "rates": "real-rate or duration shocks",
        "credit": "credit spread or default-risk repricing",
        "liquidity": "liquidity shocks and crowded risk-off behavior",
        "usd": "USD moves through currency or global-risk channels",
        "equity_crash": "broad equity market drawdowns",
        "commodity_shock": "commodity shocks or commodity-linked assets",
        "volatility_spike": "volatility spikes and nonlinear risk-off moves",
        WEAKNESS_CRYPTO_KEY: "crypto market shocks",
    }.get(weakness, "this risk channel")
    if not exposure_present and not adverse_evidence:
        return f"Limited mapped exposure to {base}; available diagnostics did not cross thresholds."
    if exposure_present and not adverse_evidence:
        return (
            f"Exposure to {base} is present, but available stress/factor/tail diagnostics "
            "did not cross adverse-evidence thresholds in this run."
        )
    if adverse_evidence:
        return (
            f"Adverse evidence for {base} ({severity} severity); review scenario coverage, "
            "asset loss drivers, and factor drivers before action."
        )
    return f"Potential sensitivity to {base}."


def build_portfolio_xray_v2(
    *,
    analysis_setup: dict[str, Any] | None,
    weights: dict[str, Any] | None,
    rc_asset: Any,
    stress_report: dict[str, Any] | None,
    portfolio_valid: bool | None,
    portfolio_metrics: dict[str, Any] | None = None,
    portfolio_analytics: dict[str, Any] | None = None,
    drawdown_structure: dict[str, Any] | None = None,
    taxonomy_rows: dict[str, dict[str, Any]] | None = None,
    taxonomy_sources: dict[str, str] | None = None,
    rc_vol_map: dict[str, float] | None = None,
    output_dir_csv: Path | str | None = None,
) -> dict[str, Any]:
    """Build Portfolio X-Ray v2 from existing pipeline outputs and diagnostics.

    This function intentionally does not recompute canonical portfolio metrics,
    RC_vol, factor betas, VaR/ES, stress PnL, or stress pass/fail using alternate
    formulas. It only summarizes the inputs passed by the report pipeline.

    Risk Budget View prefers full ``rc_vol_*`` CSV evidence (via ``rc_vol_map`` or
    ``output_dir_csv``) over display-oriented ``snapshot.RC_asset`` top-N rows.
    """
    rc_asset_resolved, rc_sources = resolve_rc_asset_for_xray(
        rc_asset,
        rc_vol_map=rc_vol_map,
        output_dir_csv=output_dir_csv,
    )
    legacy_summary = build_portfolio_xray_summary(
        analysis_setup=analysis_setup,
        weights=weights,
        rc_asset=rc_asset_resolved,
        stress_report=stress_report,
        portfolio_valid=portfolio_valid,
        portfolio_metrics=portfolio_metrics,
    )
    ap = _analysis_portfolio(analysis_setup)
    weight_map = dict(weights or ap.get("weights") or {})
    allocation, _ = _allocation_section(
        weights=weight_map,
        taxonomy_rows=taxonomy_rows,
        taxonomy_sources=taxonomy_sources,
    )
    sections = {
        "asset_allocation": allocation,
        "risk_diagnostics": _risk_diagnostics_section(
            portfolio_metrics=portfolio_metrics,
            portfolio_analytics=portfolio_analytics,
            drawdown_structure=drawdown_structure,
        ),
        "factor_exposure": _factor_exposure_section(stress_report),
        "hidden_risk_detector": _hidden_risk_section(
            weights=weight_map,
            rc_asset=rc_asset_resolved,
            stress_report=stress_report,
            taxonomy_rows=taxonomy_rows,
            portfolio_analytics=portfolio_analytics,
        ),
        "risk_budget_view": _risk_budget_section(
            weights=weight_map,
            rc_asset=rc_asset_resolved,
            stress_report=stress_report,
            rc_data_sources=rc_sources,
        ),
    }
    sections["weakness_map"] = _weakness_map_section(
        portfolio_metrics=portfolio_metrics,
        portfolio_analytics=portfolio_analytics,
        stress_report=stress_report,
        allocation_section=sections["asset_allocation"],
        weights=weight_map,
        taxonomy_rows=taxonomy_rows,
    )
    sections["portfolio_archetype"] = _portfolio_archetype_section(
        allocation_section=sections["asset_allocation"],
        rc_asset=rc_asset_resolved,
        stress_report=stress_report,
        weakness_map_section=sections["weakness_map"],
        portfolio_metrics=portfolio_metrics,
        portfolio_analytics=portfolio_analytics,
        hidden_risk_section=sections["hidden_risk_detector"],
    )
    return {
        "version": PORTFOLIO_XRAY_VERSION,
        "diagnostic_only": True,
        "diagnostic_only_disclaimer": DIAGNOSTIC_ONLY_DISCLAIMER,
        "analysis_setup_summary": legacy_summary["analysis_setup_summary"],
        "thresholds": dict(XRAY_THRESHOLDS),
        "sections": {key: sections[key] for key in XRAY_SECTION_KEYS},
        "legacy_summary": legacy_summary,
    }


def _summarize_item(item: dict[str, Any]) -> str:
    t = item.get("type")
    if t == "holding":
        return (
            f"{item.get('ticker')}: weight {_fmt_pct(item.get('weight'))}, "
            f"asset_class={item.get('asset_class')}, region={item.get('region')}, "
            f"risk_bucket={item.get('risk_bucket')}"
        )
    if t == "breakdown":
        values = item.get("values") or []
        top = ", ".join(f"{row.get('name')} {_fmt_pct(row.get('weight'))}" for row in values[:4])
        return f"{item.get('dimension')}: {top or 'n/a'}"
    if t == "portfolio_metrics":
        mq = item.get("metric_quality") if isinstance(item.get("metric_quality"), dict) else {}
        n_obs = mq.get("n_obs")
        bench = mq.get("benchmark_ticker")
        return (
            f"CAGR {_fmt_pct(item.get('cagr'))}, vol {_fmt_pct(item.get('vol_annual'))}, "
            f"Sharpe {_fmt_num(item.get('sharpe'))}, Sortino {_fmt_num(item.get('sortino'))}, "
            f"MaxDD {_fmt_pct(item.get('max_drawdown'))}, beta {_fmt_num(item.get('beta_portfolio'))}, "
            f"down/up beta {_fmt_num(item.get('downside_beta'))}/{_fmt_num(item.get('upside_beta'))}, "
            f"skew/kurt {_fmt_num(item.get('skewness'))}/{_fmt_num(item.get('kurtosis'))}"
            + (f" (n_obs={n_obs}, bench={bench})" if n_obs is not None else "")
        )
    if t == "tail_risk":
        freq = item.get("frequency") or "daily"
        window = item.get("window_label") or item.get("window_months")
        n_obs = item.get("n_obs")
        return (
            f"Historical VaR/ES on {freq} returns, window {window}, n_obs={n_obs}: "
            f"VaR95 {_fmt_pct(item.get('var_95'))}, ES95 {_fmt_pct(item.get('es_95'))}, "
            f"VaR99 {_fmt_pct(item.get('var_99'))}, ES99 {_fmt_pct(item.get('es_99'))}"
        )
    if t == "tail_and_crisis_metrics":
        return (
            f"VaR95 {_fmt_pct(item.get('var_95'))}, ES95 {_fmt_pct(item.get('es_95'))}, "
            f"EEE10 {_fmt_num(item.get('eee_10pct'))}%"
        )
    if t == "crisis_equity_exposure":
        return f"EEE (crisis beta x100) {_fmt_num(item.get('eee_10pct'))}%"
    if t == "rolling_metrics":
        parts = [k for k in item if k != "type" and item.get(k)]
        return "rolling summaries: " + (", ".join(parts) if parts else "Sharpe, Sortino, vol, beta, correlation")
    if t == "factor_exposure":
        return (
            f"{item.get('factor')}: beta_5y {_fmt_num(item.get('beta_5y'))}, "
            f"beta_10y {_fmt_num(item.get('beta_10y'))}, "
            f"variance share {_fmt_pct(item.get('net_total_variance_share'))}"
        )
    if t == "factor_residual_risk":
        return f"Residual factor risk: {_fmt_pct(item.get('residual_share'))}, severity={item.get('residual_severity')}"
    if t in {"hidden_risk_flag", "hidden_risk_assessment"}:
        status = item.get("assessment_status") or ("flagged" if t == "hidden_risk_flag" else "n/a")
        sev = item.get("severity") or "n/a"
        return (
            f"[{status}] {sev} {item.get('name')}: {item.get('fact')} "
            f"{item.get('interpretation')} Next test: {item.get('next_test')} "
            f"Limitation: {item.get('limitation')}"
        )
    if t == "portfolio_archetype":
        pos = "; ".join(item.get("positive_evidence") or item.get("drivers") or [])
        neg = "; ".join(item.get("negative_evidence") or [])
        conflict = item.get("conflict_summary") or ""
        return (
            f"primary={item.get('primary_archetype')}, secondary={item.get('secondary_archetype')}, "
            f"confidence={item.get('confidence')}, positive={pos}"
            + (f", negative={neg}" if neg else "")
            + (f", tension={conflict}" if conflict else "")
        )
    if t == "asset_risk_budget":
        return (
            f"{item.get('ticker')}: weight {_fmt_pct(item.get('weight'))}, "
            f"RC_vol {_fmt_pct(item.get('rc_vol'))}, gap {_fmt_pp(item.get('risk_weight_gap'))}, "
            f"worst stress contribution {_fmt_pct(item.get('worst_stress_loss_contribution_pct'))} "
            f"({item.get('worst_stress_scenario') or 'n/a'})"
        )
    if t == "weakness":
        drivers = item.get("top_asset_loss_drivers") or []
        driver_tickers = ", ".join(str(row.get("ticker")) for row in drivers[:2] if row.get("ticker"))
        return (
            f"{item.get('risk')}: severity={item.get('severity')}, "
            f"exposure={item.get('exposure_present')}, adverse={item.get('adverse_evidence')}, "
            f"confidence={item.get('confidence')}"
            + (f", top assets={driver_tickers}" if driver_tickers else "")
        )
    return str(item)


def _xray_section_id(section_key: str) -> str:
    return f"xray-{section_key.replace('_', '-')}"


def _html_esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def _xray_section_meta_phrase(section: dict[str, Any]) -> str:
    parts: list[str] = []
    status = section.get("status")
    if status:
        parts.append(f"Status: {status}")
    confidence = section.get("confidence")
    if confidence:
        parts.append(f"Confidence: {confidence}")
    frequency = section.get("frequency")
    if frequency and frequency != "n/a":
        parts.append(f"Frequency: {frequency}")
    window = section.get("window")
    if window and window != "n/a":
        parts.append(f"Window: {window}")
    n_obs = section.get("n_obs")
    if n_obs is not None:
        parts.append(f"n_obs: {n_obs}")
    sources = section.get("data_sources_used") or []
    if sources:
        parts.append(f"Sources: {', '.join(str(s) for s in sources)}")
    return "; ".join(parts) if parts else "Evidence metadata not available."


def _xray_legacy_overview_lines(xray: dict[str, Any]) -> list[str]:
    setup = xray.get("analysis_setup_summary") or {}
    legacy = xray.get("legacy_summary") or {}
    alloc = legacy.get("asset_allocation_summary") or {}
    risk = legacy.get("risk_contribution_summary") or {}
    verdict = legacy.get("portfolio_diagnostic_verdict") or {}
    lines = [
        str(xray.get("diagnostic_only_disclaimer") or DIAGNOSTIC_ONLY_DISCLAIMER),
        (
            f"Analyzed portfolio role: {setup.get('portfolio_role', 'unknown')}; "
            f"weight source: {setup.get('weight_source', 'unknown')}; "
            f"recommendation status: {setup.get('recommendation_status', 'unknown')}."
        ),
        (
            f"Setup: currency {setup.get('investor_currency', 'n/a')}; "
            f"base benchmark {setup.get('base_benchmark_ticker', 'n/a')}; "
            f"cash proxy {setup.get('cash_proxy_ticker', 'n/a')}; "
            f"return frequency {setup.get('return_frequency', 'n/a')}."
        ),
        (
            f"Capital concentration (top weights): {_join_items(alloc.get('top_holdings') or [])}; "
            f"cash weight {_fmt_pct(alloc.get('cash_weight'))}."
        ),
        (
            f"Risk concentration (top RC_vol): {_join_items(risk.get('top_rc_contributors') or [])}. "
            f"{risk.get('method_note', '')}"
        ),
        "Diagnostic verdict:",
    ]
    lines.extend(str(line) for line in verdict.get("lines") or [])
    return lines


def _xray_text_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    if not rows:
        return []
    widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))
    fmt = "  ".join(f"{{:{w}}}" for w in widths)
    lines = [fmt.format(*headers), fmt.format(*("-" * w for w in widths))]
    lines.extend(fmt.format(*row) for row in rows)
    return lines


def _xray_section_text_block(section_key: str, section: dict[str, Any]) -> list[str]:
    title = XRAY_SECTION_TITLES.get(section_key, section_key)
    lines = ["", title, _xray_section_meta_phrase(section)]
    for warning in section.get("warnings") or []:
        lines.append(f"Warning: {warning}")
    items = section.get("items") or []
    table_rows = _xray_section_table_rows(section_key, items)
    if table_rows:
        headers, rows = table_rows
        lines.extend(_xray_text_table(headers, rows))
    else:
        for item in items[:16]:
            lines.append(f"  - {_summarize_item(item)}")
        if len(items) > 16:
            lines.append(f"  - ({len(items) - 16} additional rows in portfolio_xray.json)")
    for limitation in section.get("limitations") or []:
        lines.append(f"Limitation: {limitation}")
    return lines


def _xray_section_table_rows(
    section_key: str, items: list[dict[str, Any]]
) -> tuple[list[str], list[list[str]]] | None:
    if not items:
        return None
    if section_key == "asset_allocation":
        holdings = [item for item in items if item.get("type") == "holding"]
        if holdings:
            return (
                ["Ticker", "Weight", "Asset class", "Region", "Risk bucket"],
                [
                    [
                        str(item.get("ticker", "")),
                        _fmt_pct(item.get("weight")),
                        str(item.get("asset_class") or "n/a"),
                        str(item.get("region") or "n/a"),
                        str(item.get("risk_bucket") or "n/a"),
                    ]
                    for item in holdings[:20]
                ],
            )
        breakdowns = [item for item in items if item.get("type") == "breakdown"]
        if breakdowns:
            rows: list[list[str]] = []
            for item in breakdowns:
                for row in item.get("values") or []:
                    rows.append(
                        [
                            str(item.get("dimension") or ""),
                            str(row.get("name") or ""),
                            _fmt_pct(row.get("weight")),
                        ]
                    )
            return (["Dimension", "Bucket", "Weight"], rows[:24])
    if section_key == "risk_diagnostics":
        metrics = [item for item in items if item.get("type") == "portfolio_metrics"]
        if metrics:
            m = metrics[0]
            return (
                ["Metric", "Value"],
                [
                    ["CAGR", _fmt_pct(m.get("cagr"))],
                    ["Volatility (annual)", _fmt_pct(m.get("vol_annual"))],
                    ["Sharpe", _fmt_num(m.get("sharpe"))],
                    ["Sortino", _fmt_num(m.get("sortino"))],
                    ["Max drawdown", _fmt_pct(m.get("max_drawdown"))],
                    ["Beta (base)", _fmt_num(m.get("beta_portfolio"))],
                    ["Downside / upside beta", f"{_fmt_num(m.get('downside_beta'))} / {_fmt_num(m.get('upside_beta'))}"],
                    ["Skew / kurtosis", f"{_fmt_num(m.get('skewness'))} / {_fmt_num(m.get('kurtosis'))}"],
                ],
            )
        tail = [item for item in items if item.get("type") == "tail_risk"]
        if tail:
            t = tail[0]
            return (
                ["Tail metric", "Value"],
                [
                    ["Method", str(t.get("method") or "historical")],
                    ["Frequency", str(t.get("frequency") or "n/a")],
                    ["Window", str(t.get("window_label") or t.get("window_months") or "n/a")],
                    ["VaR 95%", _fmt_pct(t.get("var_95"))],
                    ["ES 95%", _fmt_pct(t.get("es_95"))],
                ],
            )
    if section_key == "factor_exposure":
        factors = [item for item in items if item.get("type") == "factor_exposure"]
        if factors:
            return (
                ["Factor", "Beta 5Y", "Beta 10Y", "Variance share"],
                [
                    [
                        str(item.get("factor") or ""),
                        _fmt_num(item.get("beta_5y")),
                        _fmt_num(item.get("beta_10y")),
                        _fmt_pct(item.get("net_total_variance_share")),
                    ]
                    for item in factors
                ],
            )
    if section_key == "hidden_risk_detector":
        assessments = [
            item
            for item in items
            if item.get("type") in {"hidden_risk_assessment", "hidden_risk_flag"}
        ]
        if assessments:
            return (
                ["Category", "Status", "Severity", "Finding"],
                [
                    [
                        str(item.get("name") or ""),
                        str(item.get("assessment_status") or ("flagged" if item.get("flagged") else "n/a")),
                        str(item.get("severity") or "n/a"),
                        str(item.get("fact") or item.get("interpretation") or "")[:120],
                    ]
                    for item in assessments
                ],
            )
    if section_key == "portfolio_archetype":
        archetypes = [item for item in items if item.get("type") == "portfolio_archetype"]
        if archetypes:
            a = archetypes[0]
            rows = [
                ["Primary archetype", str(a.get("primary_archetype") or "n/a")],
                ["Secondary archetype", str(a.get("secondary_archetype") or "none")],
                ["Confidence", str(a.get("confidence") or "n/a")],
            ]
            if a.get("conflict_summary"):
                rows.append(["Tension", str(a.get("conflict_summary"))[:160]])
            scorecard = a.get("archetype_scorecard") or []
            for row in scorecard[:8]:
                if isinstance(row, dict):
                    rows.append(
                        [
                            str(row.get("archetype") or ""),
                            f"fit={row.get('fit')}, score={_fmt_num(row.get('score'))}",
                        ]
                    )
            return (["Archetype lens", "Detail"], rows)
    if section_key == "risk_budget_view":
        budget = [item for item in items if item.get("type") == "asset_risk_budget"]
        if budget:
            return (
                ["Ticker", "Weight", "RC_vol", "Risk gap", "Worst stress"],
                [
                    [
                        str(item.get("ticker") or ""),
                        _fmt_pct(item.get("weight")),
                        _fmt_pct(item.get("rc_vol")),
                        _fmt_pp(item.get("risk_weight_gap")),
                        f"{_fmt_pct(item.get('worst_stress_loss_contribution_pct'))} ({item.get('worst_stress_scenario') or 'n/a'})",
                    ]
                    for item in budget[:20]
                ],
            )
    if section_key == "weakness_map":
        weaknesses = [item for item in items if item.get("type") == "weakness"]
        if weaknesses:
            return (
                ["Risk", "Severity", "Exposure", "Adverse", "Confidence", "Interpretation"],
                [
                    [
                        str(item.get("risk") or ""),
                        str(item.get("severity") or "n/a"),
                        "yes" if item.get("exposure_present") else "no",
                        "yes" if item.get("adverse_evidence") else "no",
                        str(item.get("confidence") or "n/a"),
                        str(item.get("interpretation") or "")[:100],
                    ]
                    for item in weaknesses
                ],
            )
    return None


def _xray_html_table_wrapped(caption: str, headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return ""
    head = "".join(f"<th>{_html_esc(h)}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{_html_esc(cell)}</td>" for cell in row) + "</tr>" for row in rows
    )
    table = (
        f"<table><caption>{_html_esc(caption)}</caption>"
        f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"
    )
    return '<div class="table-wrap">' + table + '</div>'


def _xray_section_html_block(section_key: str, section: dict[str, Any]) -> list[str]:
    title = XRAY_SECTION_TITLES.get(section_key, section_key)
    section_id = _xray_section_id(section_key)
    parts = [
        f'<section class="xray-section" id="{section_id}">',
        f"<h3>{_html_esc(title)}</h3>",
        f'<p class="xray-meta">{_html_esc(_xray_section_meta_phrase(section))}</p>',
    ]
    for warning in section.get("warnings") or []:
        parts.append(f'<p class="xray-warning"><strong>Warning:</strong> {_html_esc(warning)}</p>')
    items = section.get("items") or []
    table_rows = _xray_section_table_rows(section_key, items)
    if table_rows:
        headers, rows = table_rows
        parts.append(_xray_html_table_wrapped(title, headers, rows))
    elif items:
        parts.append("<ul class=\"xray-bullets\">")
        for item in items[:16]:
            parts.append(f"<li>{_html_esc(_summarize_item(item))}</li>")
        parts.append("</ul>")
        if len(items) > 16:
            parts.append(
                f"<p class=\"xray-more\">{_html_esc(f'{len(items) - 16} additional rows in portfolio_xray.json.')}</p>"
            )
    for limitation in section.get("limitations") or []:
        parts.append(f'<p class="xray-limitation"><strong>Limitation:</strong> {_html_esc(limitation)}</p>')
    parts.append("</section>")
    return parts


def _format_portfolio_xray_v2_text(xray: dict[str, Any]) -> str:
    lines = [
        "============================================================",
        "PORTFOLIO X-RAY SUMMARY (diagnostic-only)",
        "============================================================",
    ]
    lines.extend(_xray_legacy_overview_lines(xray))
    sections = xray.get("sections") or {}
    for key in XRAY_SECTION_KEYS:
        section = sections.get(key) or {}
        lines.extend(_xray_section_text_block(key, section))
    lines.append("")
    lines.append("Machine-readable source: portfolio_xray.json")
    return "\n".join(lines)


def format_portfolio_xray_text(summary: dict[str, Any]) -> str:
    """Format X-Ray summary as a plain-text diagnostic section."""
    if summary.get("version") == PORTFOLIO_XRAY_VERSION:
        return _format_portfolio_xray_v2_text(summary)

    setup = summary.get("analysis_setup_summary") or {}
    alloc = summary.get("asset_allocation_summary") or {}
    risk = summary.get("risk_contribution_summary") or {}
    verdict = summary.get("portfolio_diagnostic_verdict") or {}
    lines = [
        "Portfolio X-Ray Summary",
        f"Analyzed portfolio: role={setup.get('portfolio_role', 'unknown')}; weight_source={setup.get('weight_source', 'unknown')}; recommendation_status={setup.get('recommendation_status', 'unknown')}.",
        f"Setup: input_case={setup.get('product_input_case', 'unknown')}; currency={setup.get('investor_currency', 'n/a')}; benchmark={setup.get('base_benchmark_ticker', 'n/a')}; cash_proxy={setup.get('cash_proxy_ticker', 'n/a')}; frequency={setup.get('return_frequency', 'n/a')}.",
        f"Asset Allocation: main capital concentration is {_join_items(alloc.get('top_holdings') or [])}; cash={_fmt_pct(alloc.get('cash_weight'))}.",
        f"Risk Contribution: main RC_vol concentration is {_join_items(risk.get('top_rc_contributors') or [])}. {risk.get('method_note', '')}",
        "Portfolio Diagnostic Verdict:",
    ]
    lines.extend(str(line) for line in verdict.get("lines") or [])
    return "\n".join(lines)


def format_portfolio_xray_html(xray: dict[str, Any]) -> str:
    """Structured HTML for report.html (v2 only; legacy callers use snapshot legacy HTML)."""
    if xray.get("version") != PORTFOLIO_XRAY_VERSION:
        return ""

    legacy = xray.get("legacy_summary") or {}
    alloc = legacy.get("asset_allocation_summary") or {}
    risk = legacy.get("risk_contribution_summary") or {}

    def _legacy_rows(items: list[dict[str, Any]]) -> list[list[str]]:
        return [
            [str(row.get("ticker", "")), _fmt_ratio_html(row.get("value"))]
            for row in items
        ]

    def _fmt_ratio_html(value: Any) -> str:
        number = _as_float(value)
        if number is None:
            return "n/a"
        return f"{number * 100:.1f}%"

    parts = [
        '<section class="xray-summary-section" id="xray-summary">',
        "<h2>Portfolio X-Ray Summary</h2>",
        f'<p class="xray-disclaimer">{_html_esc(xray.get("diagnostic_only_disclaimer") or DIAGNOSTIC_ONLY_DISCLAIMER)}</p>',
    ]
    for line in _xray_legacy_overview_lines(xray):
        parts.append(f"<p>{_html_esc(line)}</p>")

    alloc_rows = _legacy_rows(alloc.get("top_holdings") or [])
    if alloc_rows:
        parts.append(
            _xray_html_table_wrapped(
                "Top holdings (capital weight)",
                ["Ticker", "Weight"],
                alloc_rows,
            )
        )
    risk_rows = _legacy_rows(risk.get("top_rc_contributors") or [])
    if risk_rows:
        parts.append(
            _xray_html_table_wrapped(
                "Top RC_vol contributors",
                ["Ticker", "RC_vol"],
                risk_rows,
            )
        )

    nav_links = "".join(
        f'<a href="#{_xray_section_id(key)}">{_html_esc(XRAY_SECTION_TITLES.get(key, key))}</a>'
        for key in XRAY_SECTION_KEYS
    )
    parts.append(f'<nav class="xray-section-nav" aria-label="X-Ray sections">{nav_links}</nav>')

    sections = xray.get("sections") or {}
    for key in XRAY_SECTION_KEYS:
        section = sections.get(key) or {}
        parts.extend(_xray_section_html_block(key, section))

    parts.append(
        '<p class="xray-source-note">Machine-readable source: <code>portfolio_xray.json</code>.</p>'
    )
    parts.append("</section>")
    return "\n".join(parts)


def format_portfolio_xray_commentary(xray: dict[str, Any]) -> str:
    """Compact X-Ray block for commentary.txt (not a full section dump)."""
    if xray.get("version") != PORTFOLIO_XRAY_VERSION:
        return format_portfolio_xray_text(xray)

    lines = [
        "Portfolio X-Ray (diagnostic-only)",
        str(xray.get("diagnostic_only_disclaimer") or DIAGNOSTIC_ONLY_DISCLAIMER),
        "",
    ]
    legacy = xray.get("legacy_summary") or {}
    verdict = legacy.get("portfolio_diagnostic_verdict") or {}
    for line in verdict.get("lines") or []:
        lines.append(str(line))

    sections = xray.get("sections") or {}
    archetype_items = (sections.get("portfolio_archetype") or {}).get("items") or []
    if archetype_items:
        a = archetype_items[0]
        lines.append(
            f"Archetype lens: {a.get('primary_archetype')} "
            f"(confidence {a.get('confidence')}); "
            f"secondary {a.get('secondary_archetype') or 'none'}."
        )
        if a.get("conflict_summary"):
            lines.append(f"Archetype tension: {a.get('conflict_summary')}")

    hidden = sections.get("hidden_risk_detector") or {}
    flagged = [
        str(item.get("name"))
        for item in hidden.get("items") or []
        if item.get("flagged") or item.get("assessment_status") == "flagged"
    ]
    if flagged:
        preview = ", ".join(flagged[:6])
        if len(flagged) > 6:
            preview += f", +{len(flagged) - 6} more"
        lines.append(f"Hidden risks flagged: {preview}.")

    weaknesses = [
        item
        for item in (sections.get("weakness_map") or {}).get("items") or []
        if item.get("severity") in {"high", "medium"} and item.get("adverse_evidence")
    ]
    if weaknesses:
        preview = ", ".join(
            f"{item.get('risk')} ({item.get('severity')})" for item in weaknesses[:5]
        )
        lines.append(f"Elevated scenario vulnerabilities: {preview}.")

    lines.append(
        "Full seven-section tables and evidence: portfolio_xray.json, report.html, report.txt."
    )
    return "\n".join(lines)


__all__ = [
    "DIAGNOSTIC_ONLY_DISCLAIMER",
    "PORTFOLIO_XRAY_VERSION",
    "XRAY_SECTION_KEYS",
    "XRAY_THRESHOLDS",
    "build_portfolio_xray_summary",
    "build_portfolio_xray_v2",
    "format_portfolio_xray_commentary",
    "format_portfolio_xray_html",
    "format_portfolio_xray_text",
    "load_rc_vol_map_from_csv",
    "resolve_rc_asset_for_xray",
]
