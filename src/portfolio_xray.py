"""Portfolio X-Ray helpers built from existing report diagnostics only."""
from __future__ import annotations

import math
from typing import Any


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
    "archetype_equity_weight_high": 0.55,
    "archetype_fixed_income_weight_high": 0.45,
    "archetype_balanced_equity_min": 0.30,
    "archetype_balanced_equity_max": 0.70,
    "archetype_balanced_fixed_income_min": 0.20,
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
                "treynor": metrics.get("treynor"),
                "max_drawdown": metrics.get("max_drawdown"),
            }
        )
    tail_keys = ("var_95", "var_99", "es_95", "es_99", "eee_10pct")
    if any(k in analytics for k in tail_keys):
        items.append({"type": "tail_and_crisis_metrics", **{k: analytics.get(k) for k in tail_keys}})
    rolling_keys = (
        "rolling_sharpe_36m",
        "rolling_sharpe_12m",
        "rolling_sortino_36m",
        "rolling_sortino_12m",
        "rolling_vol_12m",
    )
    if any(k in analytics for k in rolling_keys):
        items.append({"type": "rolling_metrics", **{k: analytics.get(k) for k in rolling_keys}})
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
            "VaR and ES are historical tail metrics and should be checked against stress scenarios before action.",
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


def _factor_exposure_section(stress_report: dict[str, Any] | None) -> dict[str, Any]:
    betas_5y = _factor_betas(stress_report, "factor_betas_5y")
    betas_10y = _factor_betas(stress_report, "factor_betas_10y")
    if not betas_5y:
        betas_5y = _factor_betas(stress_report, "factor_betas")
    kalman = {}
    if isinstance(stress_report, dict) and isinstance(stress_report.get("factor_betas_kalman"), dict):
        kalman_raw = stress_report["factor_betas_kalman"].get("latest_betas_capped") or stress_report[
            "factor_betas_kalman"
        ].get("latest_betas")
        if isinstance(kalman_raw, dict):
            kalman = {str(k): v for k, v in kalman_raw.items()}
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
    return _section(
        items=items,
        data_sources_used=[
            "analyzed weights",
            "snapshot.RC_asset",
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


def _flag(
    *,
    name: str,
    severity: str,
    fact: str,
    interpretation: str,
    next_test: str,
    limitation: str,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    return {
        "type": "hidden_risk_flag",
        "name": name,
        "severity": severity,
        "fact": fact,
        "interpretation": interpretation,
        "next_test": next_test,
        "limitation": limitation,
        "evidence": evidence,
    }


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


def _hidden_risk_section(
    *,
    weights: dict[str, Any],
    rc_asset: Any,
    stress_report: dict[str, Any] | None,
    taxonomy_rows: dict[str, dict[str, Any]] | None,
) -> dict[str, Any]:
    flags: list[dict[str, Any]] = []
    warnings: list[str] = []
    betas = _factor_betas(stress_report, "factor_betas_5y") or _factor_betas(stress_report, "factor_betas")
    beta_eq = betas.get("beta_eq")
    sev = _severity_high(beta_eq, XRAY_THRESHOLDS["equity_beta_moderate_abs"], XRAY_THRESHOLDS["equity_beta_high_abs"])
    if sev:
        flags.append(
            _flag(
                name="hidden_equity_beta",
                severity=sev,
                fact=f"5Y equity beta is {_fmt_num(beta_eq)}.",
                interpretation="The portfolio has meaningful equity-market sensitivity even if holdings labels look diversified.",
                next_test="Check equity_shock, recession_severe, and downside equity behavior.",
                limitation="Beta is historical and can change when correlations or holdings change.",
                evidence={"beta_key": "beta_eq", "value": beta_eq, "thresholds": ["equity_beta_moderate_abs", "equity_beta_high_abs"]},
            )
        )

    top_rc = _rc_items(rc_asset, limit=1)
    top_rc_value = top_rc[0]["value"] if top_rc else None
    sev = _severity_share(
        top_rc_value,
        XRAY_THRESHOLDS["top1_rc_moderate"],
        XRAY_THRESHOLDS["top1_rc_high"],
    )
    if sev and top_rc:
        flags.append(
            _flag(
                name="single_asset_risk_concentration",
                severity=sev,
                fact=f"{top_rc[0]['ticker']} contributes {_fmt_pct(top_rc_value)} of RC_vol.",
                interpretation="Portfolio risk is more concentrated than capital weights alone imply.",
                next_test="Compare weight vs RC_vol and inspect stress Top1/Top3 RC concentration.",
                limitation="RC_vol depends on the selected covariance window and existing RC calculation.",
                evidence={"ticker": top_rc[0]["ticker"], "rc_vol": top_rc_value, "thresholds": ["top1_rc_moderate", "top1_rc_high"]},
            )
        )

    pca_cov = _pca_raw_covariance(stress_report)
    pc1 = _as_float(pca_cov.get("pc1_explained_variance_ratio"))
    sev = _severity_share(pc1, XRAY_THRESHOLDS["pca_pc1_moderate"], XRAY_THRESHOLDS["pca_pc1_high"])
    if sev:
        flags.append(
            _flag(
                name="correlation_or_common_factor_concentration",
                severity=sev,
                fact=f"Raw covariance PCA PC1 explains {_fmt_pct(pc1)} of asset-return variance.",
                interpretation="Several holdings may be driven by the same statistical risk direction.",
                next_test="Review PCA loadings, raw correlation PCA, and residual PCA after factor removal.",
                limitation="PCA is statistical and does not identify a tradable economic factor by itself.",
                evidence={"pc1_explained_variance_ratio": pc1, "thresholds": ["pca_pc1_moderate", "pca_pc1_high"]},
            )
        )

    worst = _scenario_by_worst_loss(stress_report)
    worst_top1 = _as_float(worst.get("top1_rc_pct")) if isinstance(worst, dict) else None
    sev = _severity_share(
        worst_top1,
        XRAY_THRESHOLDS["stress_top1_rc_moderate"],
        XRAY_THRESHOLDS["stress_top1_rc_high"],
    )
    if sev and isinstance(worst, dict):
        flags.append(
            _flag(
                name="stress_loss_contributor_concentration",
                severity=sev,
                fact=(
                    f"In worst scenario {worst.get('scenario_id')}, top stress RC asset "
                    f"{worst.get('top1_rc_asset')} is {_fmt_pct(worst_top1)}."
                ),
                interpretation="Stress losses may be dominated by a small number of assets.",
                next_test="Inspect pnl_by_asset_pct and Top3 RC for the worst stress scenario.",
                limitation="Synthetic stress RC uses scenario covariance diagnostics and is not a pass/fail gate.",
                evidence={"scenario_id": worst.get("scenario_id"), "top1_rc_pct": worst_top1},
            )
        )

    residual = _factor_residual_share(stress_report)
    sev = _severity_share(
        residual,
        XRAY_THRESHOLDS["factor_residual_moderate"],
        XRAY_THRESHOLDS["factor_residual_high"],
    )
    if sev:
        flags.append(
            _flag(
                name="high_unexplained_factor_residual_risk",
                severity=sev,
                fact=f"Factor residual risk share is {_fmt_pct(residual)}.",
                interpretation="Named factors explain only part of portfolio variance; omitted or idiosyncratic risks may matter.",
                next_test="Review factor regression R2, residual PCA, and asset-level contributors.",
                limitation="Residual risk is model-dependent and can reflect missing factors, nonlinear behavior, or asset-specific risk.",
                evidence={"residual_share": residual, "thresholds": ["factor_residual_moderate", "factor_residual_high"]},
            )
        )

    duration_weight = _taxonomy_weight_by_predicate(
        weights,
        taxonomy_rows,
        lambda row: str(row.get("duration_bucket") or "none").lower() not in {"", "none", "short"},
    )
    if duration_weight >= XRAY_THRESHOLDS["duration_weight_high"]:
        flags.append(
            _flag(
                name="duration_concentration",
                severity="medium",
                fact=f"Intermediate/long duration-labeled holdings are {_fmt_pct(duration_weight)} of capital.",
                interpretation="The portfolio may be sensitive to rates and duration shocks beyond broad asset labels.",
                next_test="Check rates_shock, real-rate beta, and stress RC contribution from bond holdings.",
                limitation="Duration bucket is taxonomy metadata, not a live duration estimate.",
                evidence={"duration_labeled_weight": duration_weight, "threshold": "duration_weight_high"},
            )
        )

    credit_weight = _taxonomy_weight_by_predicate(
        weights,
        taxonomy_rows,
        lambda row: _risk_budget_bucket(row) == "credit" or str(row.get("main_risk_factor") or "") == "credit",
    )
    if credit_weight >= XRAY_THRESHOLDS["credit_weight_high"]:
        flags.append(
            _flag(
                name="credit_concentration",
                severity="medium",
                fact=f"Credit-labeled exposure is {_fmt_pct(credit_weight)} of capital.",
                interpretation="Credit carry or spread risk may be a hidden driver of drawdown behavior.",
                next_test="Check credit_shock, recession_severe, and liquidity_shock scenario losses.",
                limitation="Credit taxonomy is a label-level diagnostic and not a full holdings look-through.",
                evidence={"credit_labeled_weight": credit_weight, "threshold": "credit_weight_high"},
            )
        )

    if not isinstance(stress_report, dict):
        warnings.append("stress_report is missing")
    if not top_rc:
        warnings.append("RC_vol is missing")
    if not flags and not warnings:
        flags.append(
            _flag(
                name="no_material_rule_flags",
                severity="low",
                fact="No hidden-risk rule crossed the configured thresholds.",
                interpretation="Available diagnostics did not identify a dominant hidden concentration under X-Ray v2 rules.",
                next_test="Still review stress tests and factor diagnostics before changing portfolio decisions.",
                limitation="Absence of a flag is not proof of absence of risk.",
                evidence={"thresholds": list(XRAY_THRESHOLDS.keys())},
            )
        )
    return _section(
        items=flags,
        data_sources_used=[
            "stress_report.factor_betas_5y",
            "snapshot.RC_asset",
            "stress_report.portfolio_pca",
            "stress_report.factor_variance_decomposition",
            "taxonomy metadata",
        ],
        warnings=warnings,
        limitations=[
            "Hidden risk flags are transparent threshold rules, not AI judgment and not portfolio recommendations.",
            "Flags summarize existing diagnostics and should be validated with stress testing and comparison.",
        ],
        unavailable_warning="No hidden-risk diagnostic inputs were available.",
    )


def _weight_by_dimension(section: dict[str, Any], dimension: str) -> dict[str, float]:
    for item in section.get("items") or []:
        if item.get("type") == "breakdown" and item.get("dimension") == dimension:
            return {str(row.get("name")): float(row.get("weight") or 0.0) for row in item.get("values") or []}
    return {}


def _portfolio_archetype_section(
    *,
    allocation_section: dict[str, Any],
    rc_asset: Any,
    stress_report: dict[str, Any] | None,
) -> dict[str, Any]:
    asset_class_weights = _weight_by_dimension(allocation_section, "asset_class")
    risk_bucket_weights = _weight_by_dimension(allocation_section, "risk_bucket")
    main_factor_weights = _weight_by_dimension(allocation_section, "main_risk_factor")
    betas = _factor_betas(stress_report, "factor_betas_5y") or _factor_betas(stress_report, "factor_betas")
    beta_eq = abs(betas.get("beta_eq", 0.0))
    beta_credit = abs(betas.get("beta_credit", 0.0))
    beta_inf = abs(betas.get("beta_inf", 0.0))
    beta_cmd = abs(betas.get("beta_cmd", 0.0))
    top_rc_value = (_rc_items(rc_asset, limit=1) or [{"value": 0.0}])[0]["value"]
    pc1 = _as_float(_pca_raw_covariance(stress_report).get("pc1_explained_variance_ratio")) or 0.0

    candidates: list[dict[str, Any]] = []

    def add_candidate(archetype: str, strength: float, drivers: list[str]) -> None:
        if strength <= 0:
            return
        candidates.append({"archetype": archetype, "strength": strength, "drivers": drivers})

    equity_weight = asset_class_weights.get("equity", 0.0)
    fixed_income_weight = asset_class_weights.get("fixed_income", 0.0)
    commodity_weight = asset_class_weights.get("commodity", 0.0)
    credit_weight = risk_bucket_weights.get("credit", 0.0) + main_factor_weights.get("credit", 0.0)
    inflation_weight = risk_bucket_weights.get("inflation_linked", 0.0) + main_factor_weights.get("inflation", 0.0)

    add_candidate(
        "Equity Growth Portfolio",
        max(equity_weight, beta_eq),
        [
            f"equity weight {_fmt_pct(equity_weight)}",
            f"equity beta {_fmt_num(beta_eq)}",
        ],
    )
    add_candidate(
        "Balanced 60/40-like",
        min(max(equity_weight, 0.0), 1.0) if fixed_income_weight >= XRAY_THRESHOLDS["archetype_balanced_fixed_income_min"] else 0.0,
        [
            f"equity weight {_fmt_pct(equity_weight)}",
            f"fixed income weight {_fmt_pct(fixed_income_weight)}",
        ],
    )
    add_candidate(
        "Credit Carry Portfolio",
        max(credit_weight, beta_credit),
        [f"credit-labeled weight {_fmt_pct(credit_weight)}", f"credit beta {_fmt_num(beta_credit)}"],
    )
    add_candidate(
        "Duration-heavy Defensive",
        fixed_income_weight if beta_eq <= XRAY_THRESHOLDS["equity_beta_moderate_abs"] else fixed_income_weight * 0.5,
        [f"fixed income weight {_fmt_pct(fixed_income_weight)}", f"equity beta {_fmt_num(beta_eq)}"],
    )
    add_candidate(
        "Inflation-sensitive",
        max(commodity_weight, inflation_weight, beta_inf, beta_cmd),
        [
            f"commodity weight {_fmt_pct(commodity_weight)}",
            f"inflation-linked weight {_fmt_pct(inflation_weight)}",
            f"commodity beta {_fmt_num(beta_cmd)}",
        ],
    )
    add_candidate(
        "Pseudo-diversified Portfolio",
        max(top_rc_value, pc1),
        [f"top RC_vol {_fmt_pct(top_rc_value)}", f"PCA PC1 {_fmt_pct(pc1)}"],
    )

    candidates.sort(key=lambda x: (-float(x["strength"]), str(x["archetype"])))
    if not candidates:
        return _section(
            items=[],
            data_sources_used=["asset allocation", "factor betas", "RC_vol", "PCA"],
            unavailable_warning="No archetype evidence was available.",
        )

    primary = candidates[0]
    secondary = candidates[1] if len(candidates) > 1 else None
    gap = float(primary["strength"]) - float(secondary["strength"] if secondary else 0.0)
    if float(primary["strength"]) < 0.25:
        confidence = "low"
    elif gap >= 0.20:
        confidence = "high"
    elif gap >= 0.10:
        confidence = "medium"
    else:
        confidence = "low"
    conflicting = [
        {
            "archetype": row["archetype"],
            "drivers": row["drivers"],
        }
        for row in candidates[1:4]
        if float(row["strength"]) >= max(0.20, float(primary["strength"]) - 0.15)
    ]
    item = {
        "type": "portfolio_archetype",
        "primary_archetype": primary["archetype"],
        "secondary_archetype": secondary["archetype"] if secondary else None,
        "confidence": confidence,
        "drivers": primary["drivers"],
        "conflicting_signals": conflicting,
    }
    return _section(
        items=[item],
        data_sources_used=["asset allocation", "factor betas", "RC_vol", "PCA"],
        limitations=[
            "Archetype is a rule-based behavior label with caveats, not a portfolio selection decision.",
            "A portfolio can have multiple simultaneous characteristics; confidence reflects signal clarity.",
        ],
    )


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


def _weakness_map_section(
    *,
    portfolio_metrics: dict[str, Any] | None,
    portfolio_analytics: dict[str, Any] | None,
    stress_report: dict[str, Any] | None,
    allocation_section: dict[str, Any],
) -> dict[str, Any]:
    evidence: dict[str, list[dict[str, Any]]] = {key: [] for key in WEAKNESS_KEYS}
    severities: dict[str, list[str]] = {key: [] for key in WEAKNESS_KEYS}

    for row in _stress_scenarios(stress_report):
        scenario_id = str(row.get("scenario_id") or "")
        weakness = WEAKNESS_SCENARIO_MAP.get(scenario_id)
        if not weakness:
            continue
        loss = _as_float(row.get("portfolio_pnl_pct"))
        severity = _loss_severity(loss)
        if severity:
            severities[weakness].append(severity)
            evidence[weakness].append(
                {"source": "stress_scenario", "scenario_id": scenario_id, "portfolio_pnl_pct": loss}
            )

    betas = _factor_betas(stress_report, "factor_betas_5y") or _factor_betas(stress_report, "factor_betas")
    for beta_key, value in betas.items():
        weakness = WEAKNESS_FACTOR_MAP.get(beta_key)
        if not weakness:
            continue
        severity = _severity_high(
            value,
            XRAY_THRESHOLDS["factor_beta_moderate_abs"],
            XRAY_THRESHOLDS["factor_beta_high_abs"],
        )
        if severity:
            severities[weakness].append(severity)
            evidence[weakness].append({"source": "factor_beta", "beta_key": beta_key, "value": value})

    metrics = portfolio_metrics or {}
    analytics = portfolio_analytics or {}
    mdd = _as_float(metrics.get("max_drawdown"))
    if mdd is not None and mdd <= XRAY_THRESHOLDS["max_drawdown_moderate"]:
        sev = "high" if mdd <= XRAY_THRESHOLDS["max_drawdown_high"] else "medium"
        for weakness in ("recession", "equity_crash"):
            severities[weakness].append(sev)
            evidence[weakness].append({"source": "max_drawdown", "max_drawdown": mdd})
    es95 = _as_float(analytics.get("es_95"))
    if es95 is not None and es95 <= XRAY_THRESHOLDS["es_95_moderate"]:
        sev = "high" if es95 <= XRAY_THRESHOLDS["es_95_high"] else "medium"
        for weakness in ("recession", "liquidity", "volatility_spike"):
            severities[weakness].append(sev)
            evidence[weakness].append({"source": "historical_es_95", "es_95": es95})

    main_factor_weights = _weight_by_dimension(allocation_section, "main_risk_factor")
    risk_bucket_weights = _weight_by_dimension(allocation_section, "risk_bucket")
    if main_factor_weights.get("liquidity", 0.0) >= XRAY_THRESHOLDS["liquidity_risk_weight_high"]:
        severities["liquidity"].append("medium")
        evidence["liquidity"].append(
            {"source": "taxonomy", "liquidity_main_risk_factor_weight": main_factor_weights.get("liquidity")}
        )
    if risk_bucket_weights.get("credit", 0.0) >= XRAY_THRESHOLDS["credit_weight_high"]:
        severities["credit"].append("medium")
        evidence["credit"].append({"source": "taxonomy", "credit_bucket_weight": risk_bucket_weights.get("credit")})

    items: list[dict[str, Any]] = []
    for weakness in WEAKNESS_KEYS:
        ev = evidence[weakness]
        items.append(
            {
                "type": "weakness",
                "risk": weakness,
                "severity": _max_severity(severities[weakness]) if ev else "low",
                "evidence": ev
                if ev
                else [{"source": "available_diagnostics", "note": "No adverse evidence crossed X-Ray thresholds."}],
                "interpretation": _weakness_interpretation(weakness),
            }
        )
    warnings = []
    if not _stress_scenarios(stress_report):
        warnings.append("stress scenario rows are missing")
    if not betas:
        warnings.append("factor betas are missing")
    return _section(
        items=items,
        data_sources_used=[
            "stress_report.scenario_results",
            "stress_report.factor_betas_5y",
            "snapshot.RC_asset",
            "snapshot metrics",
            "snapshot analytics",
            "taxonomy metadata",
        ],
        warnings=warnings,
        limitations=[
            "Weakness Map aggregates existing evidence only; it is not a forecasting or scoring model.",
            "Low severity means available evidence did not cross configured thresholds, not that the risk is impossible.",
        ],
    )


def _weakness_interpretation(weakness: str) -> str:
    return {
        "recession": "Potential sensitivity to hard-landing or recession-like market behavior.",
        "inflation": "Potential sensitivity to inflation or stagflation pressure.",
        "rates": "Potential sensitivity to real-rate or duration shocks.",
        "credit": "Potential sensitivity to credit spread, carry, or default-risk repricing.",
        "liquidity": "Potential sensitivity to liquidity shocks and crowded risk-off behavior.",
        "usd": "Potential sensitivity to USD moves through currency or global-risk channels.",
        "equity_crash": "Potential sensitivity to broad equity market drawdowns.",
        "commodity_shock": "Potential sensitivity to commodity shocks or commodity-linked assets.",
        "volatility_spike": "Potential sensitivity to volatility spikes and nonlinear risk-off moves.",
    }.get(weakness, "Potential portfolio weakness.")


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
) -> dict[str, Any]:
    """Build Portfolio X-Ray v2 from existing pipeline outputs and diagnostics.

    This function intentionally does not recompute canonical portfolio metrics,
    RC_vol, factor betas, VaR/ES, stress PnL, or stress pass/fail using alternate
    formulas. It only summarizes the inputs passed by the report pipeline.
    """
    legacy_summary = build_portfolio_xray_summary(
        analysis_setup=analysis_setup,
        weights=weights,
        rc_asset=rc_asset,
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
            rc_asset=rc_asset,
            stress_report=stress_report,
            taxonomy_rows=taxonomy_rows,
        ),
        "risk_budget_view": _risk_budget_section(
            weights=weight_map,
            rc_asset=rc_asset,
            stress_report=stress_report,
        ),
    }
    sections["portfolio_archetype"] = _portfolio_archetype_section(
        allocation_section=sections["asset_allocation"],
        rc_asset=rc_asset,
        stress_report=stress_report,
    )
    sections["weakness_map"] = _weakness_map_section(
        portfolio_metrics=portfolio_metrics,
        portfolio_analytics=portfolio_analytics,
        stress_report=stress_report,
        allocation_section=sections["asset_allocation"],
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
        return (
            f"CAGR {_fmt_pct(item.get('cagr'))}, vol {_fmt_pct(item.get('vol_annual'))}, "
            f"Sharpe {_fmt_num(item.get('sharpe'))}, Sortino {_fmt_num(item.get('sortino'))}, "
            f"MaxDD {_fmt_pct(item.get('max_drawdown'))}, beta {_fmt_num(item.get('beta_portfolio'))}"
        )
    if t == "tail_and_crisis_metrics":
        return (
            f"VaR95 {_fmt_pct(item.get('var_95'))}, ES95 {_fmt_pct(item.get('es_95'))}, "
            f"EEE10 {_fmt_num(item.get('eee_10pct'))}%"
        )
    if t == "rolling_metrics":
        return "rolling metrics available for Sharpe, Sortino, and volatility summaries"
    if t == "factor_exposure":
        return (
            f"{item.get('factor')}: beta_5y {_fmt_num(item.get('beta_5y'))}, "
            f"beta_10y {_fmt_num(item.get('beta_10y'))}, "
            f"variance share {_fmt_pct(item.get('net_total_variance_share'))}"
        )
    if t == "factor_residual_risk":
        return f"Residual factor risk: {_fmt_pct(item.get('residual_share'))}, severity={item.get('residual_severity')}"
    if t == "hidden_risk_flag":
        return (
            f"{item.get('severity')} {item.get('name')}: {item.get('fact')} "
            f"{item.get('interpretation')} Next test: {item.get('next_test')} "
            f"Limitation: {item.get('limitation')}"
        )
    if t == "portfolio_archetype":
        return (
            f"primary={item.get('primary_archetype')}, secondary={item.get('secondary_archetype')}, "
            f"confidence={item.get('confidence')}, drivers={'; '.join(item.get('drivers') or [])}"
        )
    if t == "asset_risk_budget":
        return (
            f"{item.get('ticker')}: weight {_fmt_pct(item.get('weight'))}, "
            f"RC_vol {_fmt_pct(item.get('rc_vol'))}, gap {_fmt_pp(item.get('risk_weight_gap'))}, "
            f"worst stress contribution {_fmt_pct(item.get('worst_stress_loss_contribution_pct'))} "
            f"({item.get('worst_stress_scenario') or 'n/a'})"
        )
    if t == "weakness":
        ev = item.get("evidence") or []
        ev_text = "; ".join(str(row.get("source")) for row in ev[:3])
        return f"{item.get('risk')}: {item.get('severity')} ({ev_text or 'no evidence'})"
    return str(item)


def _format_portfolio_xray_v2_text(xray: dict[str, Any]) -> str:
    setup = xray.get("analysis_setup_summary") or {}
    legacy = xray.get("legacy_summary") or {}
    alloc = legacy.get("asset_allocation_summary") or {}
    risk = legacy.get("risk_contribution_summary") or {}
    verdict = legacy.get("portfolio_diagnostic_verdict") or {}
    lines = [
        "Portfolio X-Ray Summary",
        f"Version: {xray.get('version')}; diagnostic_only={xray.get('diagnostic_only')}.",
        str(xray.get("diagnostic_only_disclaimer") or DIAGNOSTIC_ONLY_DISCLAIMER),
        f"Analyzed portfolio: role={setup.get('portfolio_role', 'unknown')}; weight_source={setup.get('weight_source', 'unknown')}; recommendation_status={setup.get('recommendation_status', 'unknown')}.",
        f"Setup: input_case={setup.get('product_input_case', 'unknown')}; currency={setup.get('investor_currency', 'n/a')}; benchmark={setup.get('base_benchmark_ticker', 'n/a')}; cash_proxy={setup.get('cash_proxy_ticker', 'n/a')}; frequency={setup.get('return_frequency', 'n/a')}.",
        f"Asset Allocation: main capital concentration is {_join_items(alloc.get('top_holdings') or [])}; cash={_fmt_pct(alloc.get('cash_weight'))}.",
        f"Risk Contribution Summary: main RC_vol concentration is {_join_items(risk.get('top_rc_contributors') or [])}. {risk.get('method_note', '')}",
        "Portfolio Diagnostic Verdict:",
    ]
    lines.extend(str(line) for line in verdict.get("lines") or [])
    sections = xray.get("sections") or {}
    for key in XRAY_SECTION_KEYS:
        section = sections.get(key) or {}
        title = XRAY_SECTION_TITLES.get(key, key)
        lines.append("")
        lines.append(title)
        lines.append(
            f"status={section.get('status', 'unavailable')}; sources={', '.join(section.get('data_sources_used') or []) or 'n/a'}."
        )
        for warning in section.get("warnings") or []:
            lines.append(f"warning: {warning}")
        items = section.get("items") or []
        for item in items[:12]:
            lines.append(f"- {_summarize_item(item)}")
        if len(items) > 12:
            lines.append(f"- ... {len(items) - 12} more items in portfolio_xray.json")
        for limitation in section.get("limitations") or []:
            lines.append(f"limitation: {limitation}")
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


__all__ = [
    "DIAGNOSTIC_ONLY_DISCLAIMER",
    "PORTFOLIO_XRAY_VERSION",
    "XRAY_SECTION_KEYS",
    "XRAY_THRESHOLDS",
    "build_portfolio_xray_summary",
    "build_portfolio_xray_v2",
    "format_portfolio_xray_text",
]
