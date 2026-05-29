"""Investment-language presentation layer for diagnostic journey UI."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

_SCENARIO_LABEL: dict[str, str] = {
    "equity_shock": "Equity shock",
    "rates_shock": "Rates shock",
    "inflation_stagflation": "Inflation / stagflation",
    "liquidity_shock": "Liquidity shock",
    "usd_shock": "USD shock",
    "credit_shock": "Credit shock",
    "commodity_shock": "Commodity shock",
    "recession_severe": "Severe recession",
}

_ALERT_LABEL: dict[str, str] = {
    "hidden_equity_beta": "Hidden equity beta",
    "duration_concentration": "Duration concentration",
    "credit_liquidity_risk": "Credit / liquidity risk",
    "correlation_concentration": "Correlation concentration",
    "weak_hedge_behavior": "Weak hedge behavior",
    "tail_risk": "Tail risk",
}

_PROTECTION_LABEL: dict[str, str] = {
    "equity_crash_protection": "Equity crash protection",
    "rates_up_shock_protection": "Rates-up shock protection",
    "stagflation_protection": "Inflation / stagflation protection",
    "liquidity_shock_protection": "Liquidity shock protection",
    "usd_spike_protection": "USD spike protection",
    "credit_shock_protection": "Credit shock protection",
    "commodity_inflation_shock_protection": "Commodity inflation protection",
    "recession_severe_protection": "Severe recession protection",
}

_TOKEN_LABEL: dict[str, str] = {
    "fixed_income": "Fixed income",
    "equity": "Equity",
    "commodity": "Commodity",
    "cash": "Cash",
    "multi_asset": "Multi-asset",
    "unknown": "Other",
    "equity_like": "Equity-sensitive",
    "real_rates": "Real-rate sensitivity",
    "inflation": "Inflation sensitivity",
    "credit": "Credit sensitivity",
    "usd": "USD",
    "USD": "USD",
    "us": "US",
    "US": "US",
    "global": "Global",
    "defensive": "Defensive",
    "income": "Income",
    "growth": "Growth",
    "risk_on": "Risk-on",
    "cyclical": "Cyclical",
    "duration": "Duration",
    "crisis_hedge": "Crisis hedge",
    "inflation_hedge": "Inflation hedge",
    "diversifier": "Diversifier",
    "weak_protection": "Weak protection",
    "partial_protection": "Partial protection",
    "strong_protection": "Strong protection",
    "evidence_insufficient": "Evidence insufficient",
}

_FACTOR_LABEL: dict[str, str] = {
    "equity": "Equity risk",
    "real_rates": "Real-rate sensitivity",
    "inflation": "Inflation sensitivity",
    "credit": "Credit sensitivity",
    "USD": "USD exposure",
    "usd": "USD exposure",
    "commodity": "Commodity exposure",
    "VIX_volatility": "Volatility sensitivity",
    "us_growth": "US growth sensitivity",
}

_SCENARIO_HINT: dict[str, str] = {
    "recession_severe": "Largest portfolio loss in the synthetic suite",
    "equity_shock": "Equity-sensitive holdings drive most of the loss",
    "liquidity_shock": "Risk assets tend to decline together",
    "inflation_stagflation": "Rates and inflation sensitivity matter",
    "rates_shock": "Duration and rate-sensitive assets are pressured",
    "usd_shock": "USD and macro-sensitive exposures matter",
    "credit_shock": "Credit-sensitive exposures contribute modestly",
    "commodity_shock": "Relatively resilient in this scenario set",
}

_ASSET_CLASS_LABEL: dict[str, str] = {
    "equity": "Equity ETF",
    "fixed_income": "Bond ETF",
    "commodity": "Commodity ETF",
    "cash": "Cash",
    "alternative": "Alternative",
    "real_estate": "Real estate",
    "unknown": "Classification unavailable",
}


def fmt_pct(value: Any, *, decimals: int = 1, signed: bool = False) -> str | None:
    if value is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if abs(v) <= 1.5:
        v *= 100.0
    if signed and v > 0:
        return f"+{v:.{decimals}f}%"
    return f"{v:.{decimals}f}%"


def fmt_num(value: Any, *, decimals: int = 2) -> str | None:
    if value is None:
        return None
    try:
        return f"{float(value):.{decimals}f}"
    except (TypeError, ValueError):
        return None


def human_token(raw: Any) -> str:
    if raw is None:
        return "Classification unavailable"
    key = str(raw).strip()
    if not key:
        return "Classification unavailable"
    if key in _TOKEN_LABEL:
        return _TOKEN_LABEL[key]
    if key in _FACTOR_LABEL:
        return _FACTOR_LABEL[key]
    return key.replace("_", " ").strip().title()


def scenario_label(scenario_id: str | None) -> str:
    if not scenario_id:
        return "Unavailable"
    return _SCENARIO_LABEL.get(str(scenario_id), human_token(scenario_id))


def protection_label(risk_type: str | None) -> str:
    if not risk_type:
        return "Unavailable"
    return _PROTECTION_LABEL.get(str(risk_type), human_token(risk_type))


def factor_label(factor: str | None) -> str:
    if not factor:
        return "Unavailable"
    return _FACTOR_LABEL.get(str(factor), human_token(factor))


def severity_class(severity: str | None) -> str:
    s = (severity or "").lower()
    if s in {"high", "severe"}:
        return "high"
    if s in {"medium", "moderate"}:
        return "medium"
    if s in {"low"}:
        return "low"
    return "neutral"


def scenario_hint(scenario_id: str | None) -> str:
    if not scenario_id:
        return "Scenario interpretation unavailable"
    return _SCENARIO_HINT.get(str(scenario_id), "Defined stress assumptions; not a market forecast")


def protection_status_human(raw: str | None) -> str:
    if not raw:
        return "Unavailable"
    key = str(raw).lower()
    mapping = {
        "weak_protection": "Weak protection",
        "partial_protection": "Partial protection",
        "strong_protection": "Strong protection",
        "no_protection": "No meaningful protection",
        "evidence_insufficient": "Evidence insufficient",
    }
    return mapping.get(key, human_token(raw))


def confidence_human(raw: str | None) -> str:
    if not raw:
        return "Moderate confidence"
    key = str(raw).lower()
    mapping = {
        "significant": "Significant",
        "weak_evidence": "Visible but weaker",
        "unstable_low_confidence": "Low confidence",
        "high": "High confidence",
        "medium": "Moderate confidence",
        "low": "Low confidence",
    }
    return mapping.get(key, human_token(raw))


def load_ticker_taxonomy(project_root: Path, tickers: list[str]) -> dict[str, dict[str, str]]:
    """Best-effort ticker metadata from etf_universe.yml."""
    if yaml is None:
        return {}
    path = project_root / "config" / "etf_universe.yml"
    if not path.is_file():
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            rows = yaml.safe_load(f) or []
    except OSError:
        return {}
    want = {t.upper() for t in tickers}
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        ticker = str(row.get("ticker") or "").upper()
        if ticker not in want or ticker in out:
            continue
        ac = str(row.get("asset_class") or "unknown")
        roles = row.get("risk_role")
        role = roles[0] if isinstance(roles, list) and roles else "unknown"
        out[ticker] = {
            "asset_class": _ASSET_CLASS_LABEL.get(ac, human_token(ac)),
            "risk_role": human_token(role),
        }
    return out


def _metric_evidence(metric: str, value: Any, *, pct: bool = True) -> str | None:
    if value is None:
        return None
    label = human_token(metric.replace("_", " "))
    if pct:
        formatted = fmt_pct(value)
        return f"{label}: {formatted}" if formatted else None
    formatted = fmt_num(value)
    return f"{label}: {formatted}" if formatted else None


def build_hidden_alert_card(
    alert_id: str,
    alert: dict[str, Any],
    *,
    b21: dict[str, Any],
    b22: dict[str, Any],
    b23: dict[str, Any],
) -> dict[str, Any] | None:
    status = str(alert.get("status") or "")
    if status.lower() in {"low", "below_threshold", "unavailable"}:
        return None

    comp = b21.get("portfolio_composition_snapshot") if isinstance(b21.get("portfolio_composition_snapshot"), dict) else {}
    corr = (b22.get("correlation_breakdown") or {}) if isinstance(b22.get("correlation_breakdown"), dict) else {}
    top_pair = (corr.get("top3_highest_correlation_pairs") or [{}])[0]
    dom_ac = (comp.get("dominant_asset_class") or {}).get("name")
    dom_factor = (comp.get("dominant_main_risk_factor") or {}).get("name")
    bench = b22.get("benchmark_dependence") if isinstance(b22.get("benchmark_dependence"), dict) else {}
    metrics = b22.get("return_risk_metrics") if isinstance(b22.get("return_risk_metrics"), dict) else {}

    evidence: list[str] = []
    linked: list[str] = []
    for asset in (alert.get("contributing_assets") or [])[:3]:
        if isinstance(asset, dict) and asset.get("ticker"):
            linked.append(str(asset["ticker"]))

    title = _ALERT_LABEL.get(alert_id, human_token(alert_id))
    diagnosis = ""
    next_tests: list[str] = []

    if alert_id == "duration_concentration":
        diagnosis = "The portfolio has meaningful exposure to assets sensitive to real rates and duration."
        fi_pct = None
        for row in ((b21.get("capital_allocation_breakdown") or {}).get("by_asset_class") or []):
            if isinstance(row, dict) and row.get("name") == "fixed_income":
                fi_pct = row.get("weight_pct")
        if fi_pct is not None:
            evidence.append(f"Fixed income exposure is {fmt_pct(fi_pct / 100.0 if float(fi_pct) > 1.5 else fi_pct)}")
        evidence.append("Real-rate sensitivity is a top factor driver")
        if linked:
            evidence.append(f"Linked holdings include {', '.join(linked)}")
        next_tests = ["Rates shock", "Inflation / stagflation"]
    elif alert_id == "correlation_concentration":
        diagnosis = "Several holdings may move together, reducing real diversification."
        if isinstance(top_pair, dict):
            corr_val = top_pair.get("correlation")
            if corr_val is not None:
                evidence.append(f"Highest pairwise correlation is {fmt_num(corr_val, decimals=2)}")
        evidence.append("Multiple holdings share similar equity-sensitive behavior")
        dom_cur = (comp.get("dominant_currency") or {}).get("name")
        if dom_cur:
            evidence.append(f"{human_token(dom_cur)} exposure dominates the currency profile")
        next_tests = ["Equity shock", "Liquidity shock", "Severe recession"]
    elif alert_id == "weak_hedge_behavior":
        diagnosis = "Defensive or hedge-labeled sleeves may not offset losses in the worst stress scenario."
        evidence.append("Hedge-labeled weights did not materially offset the worst scenario loss")
        if linked:
            evidence.append(f"Linked holdings: {', '.join(linked[:3])}")
        evidence.append("Stress Lab should verify whether any sleeve actually helped")
        next_tests = ["Severe recession", "Equity shock"]
    elif alert_id == "hidden_equity_beta":
        diagnosis = "Equity market sensitivity may be higher than a simple holding count suggests."
        beta = bench.get("beta_portfolio")
        if beta is not None:
            evidence.append(f"Benchmark beta is {fmt_num(beta)}")
        if dom_ac:
            evidence.append(f"Dominant asset class: {human_token(dom_ac)}")
        next_tests = ["Equity shock", "Liquidity shock"]
    elif alert_id == "tail_risk":
        diagnosis = "Tail metrics suggest the portfolio should still be reviewed under severe scenarios."
        tail = b22.get("tail_risk_diagnostics") if isinstance(b22.get("tail_risk_diagnostics"), dict) else {}
        es = tail.get("es_95")
        if es is not None:
            evidence.append(f"Historical ES (95%) is about {fmt_pct(es)}")
        if metrics.get("portfolio_cagr") is not None:
            evidence.append(f"CAGR is {fmt_pct(metrics.get('portfolio_cagr'))} with meaningful drawdown risk")
        next_tests = ["Severe recession", "Equity shock"]
    elif alert_id == "credit_liquidity_risk":
        diagnosis = "Credit and liquidity-sensitive exposures should be reviewed if spread or funding stress appears."
        if dom_ac:
            evidence.append(f"Dominant asset class: {human_token(dom_ac)}")
        evidence.append("Credit remains a monitored factor in stress scenarios")
        next_tests = ["Credit shock", "Liquidity shock"]
    else:
        diagnosis = clean_technical_text((alert.get("explanation") or alert.get("why_it_matters") or "")[:280])
        if not diagnosis:
            diagnosis = "This exposure warrants review before relying on diversification alone."
        next_tests = [scenario_label(t) for t in (alert.get("next_tests") or [])[:3]]

    if not evidence:
        for item in (alert.get("evidence") or [])[:3]:
            if isinstance(item, dict):
                fact = item.get("fact") or item.get("interpretation")
                if fact and "Block " not in str(fact):
                    evidence.append(clean_technical_text(str(fact)[:200]))

    return {
        "id": alert_id,
        "title": title,
        "level": status.title() if status else "Unavailable",
        "level_class": severity_class(status),
        "diagnosis": diagnosis,
        "evidence": evidence[:3],
        "linked_assets": linked[:3],
        "next_tests": next_tests[:3],
    }


def build_weakness_card(row: dict[str, Any], *, b22: dict[str, Any], b23: dict[str, Any]) -> dict[str, Any]:
    risk_type = row.get("risk_type")
    label = row.get("risk_title") or scenario_label(risk_type)
    sev = str(row.get("severity") or "Low")
    bench = b22.get("benchmark_dependence") if isinstance(b22.get("benchmark_dependence"), dict) else {}
    factor_summary = b23.get("factor_exposure_summary") if isinstance(b23.get("factor_exposure_summary"), dict) else {}
    top_factors = [factor_label(f) for f in (factor_summary.get("top_3_factors") or [])[:2]]

    diagnosis = {
        "equity_shock": "The portfolio has meaningful equity-sensitive exposure and should be tested against an equity drawdown scenario.",
        "rates_shock": "Rate and duration sensitivity may pressure the portfolio when yields move abruptly.",
        "inflation_stagflation": "Inflation and stagflation scenarios remain relevant given macro-sensitive holdings.",
        "liquidity_shock": "A liquidity stress scenario is worth testing when risk assets correlate in risk-off markets.",
        "credit_shock": "Credit spread shocks should be reviewed if credit-sensitive exposure is present.",
        "usd_shock": "USD moves may matter given the portfolio's currency profile.",
        "commodity_shock": "Commodity-linked exposure should be checked under commodity stress assumptions.",
        "recession_severe": "A severe recession scenario is a priority test when macro-sensitive assets dominate losses.",
    }.get(str(risk_type), "This scenario should be verified under defined stress assumptions.")

    evidence: list[str] = []
    if top_factors:
        evidence.append(f"Top factor drivers include {top_factors[0]}")
    beta = bench.get("beta_portfolio")
    if beta is not None and str(risk_type) in {"equity_shock", "recession_severe", "liquidity_shock"}:
        evidence.append(f"Benchmark beta is {fmt_num(beta)}")
    if row.get("why_it_matters"):
        evidence.append(str(row["why_it_matters"])[:160])
    if not evidence:
        for line in (row.get("key_evidence") or [])[:2]:
            if isinstance(line, str) and "score" not in line.lower() and "present" not in line.lower():
                evidence.append(line[:160])

    next_test = scenario_label((row.get("next_tests") or [risk_type])[0])

    return {
        "label": label,
        "severity": sev,
        "severity_class": severity_class(sev),
        "diagnosis": diagnosis,
        "evidence": evidence[:3],
        "next_test": next_test,
        "score": row.get("score_0_100"),
    }


def build_executive_diagnosis(
    *,
    b21: dict[str, Any],
    b22: dict[str, Any],
    b23: dict[str, Any],
    b24: dict[str, Any],
    b25: dict[str, Any],
    b26: dict[str, Any],
) -> dict[str, Any]:
    comp = b21.get("portfolio_composition_snapshot") if isinstance(b21.get("portfolio_composition_snapshot"), dict) else {}
    dom_region = human_token((comp.get("dominant_region") or {}).get("name"))
    dom_ac = human_token((comp.get("dominant_asset_class") or {}).get("name"))
    dom_cur = human_token((comp.get("dominant_currency") or {}).get("name"))
    factor_summary = b23.get("factor_exposure_summary") if isinstance(b23.get("factor_exposure_summary"), dict) else {}
    factors = [factor_label(f) for f in (factor_summary.get("top_3_factors") or [])[:3]]
    top1_rc = b25.get("top1_rc_asset") if isinstance(b25.get("top1_rc_asset"), dict) else {}

    alerts = b24.get("alerts") if isinstance(b24.get("alerts"), dict) else {}
    hidden_names = []
    for key, alert in alerts.items():
        if not isinstance(alert, dict):
            continue
        if str(alert.get("status") or "").lower() in {"medium", "high"}:
            hidden_names.append(_ALERT_LABEL.get(key, human_token(key)))

    pre_high = [
        scenario_label(r.get("risk_type"))
        for r in (b26.get("risk_types") or [])
        if isinstance(r, dict) and str(r.get("severity", "")).lower() == "high"
    ]
    pre_medium = [
        scenario_label(r.get("risk_type"))
        for r in (b26.get("risk_types") or [])
        if isinstance(r, dict) and str(r.get("severity", "")).lower() == "medium"
    ][:3]

    main = (
        "The portfolio appears diversified by holdings, but its risk is mainly driven by "
        f"{', '.join(factors) if factors else 'macro factor exposure'}. "
        "Risk is also concentrated in a few holdings and should be verified through Stress Test Lab."
    )

    findings = [
        {
            "title": "Capital concentration",
            "body": f"{dom_region} / {dom_cur} exposure with meaningful {dom_ac} allocation.",
        },
        {
            "title": "Main factor drivers",
            "body": ", ".join(factors) if factors else "Factor evidence unavailable",
        },
        {
            "title": "Top risk contributor",
            "body": (
                f"{top1_rc.get('ticker')} contributes more risk than its capital weight suggests."
                if top1_rc.get("ticker")
                else "Risk contribution evidence unavailable."
            ),
        },
        {
            "title": "Hidden risks",
            "body": ", ".join(hidden_names) if hidden_names else "No elevated hidden-risk alerts in this run.",
        },
        {
            "title": "Pre-stress weaknesses",
            "body": (
                ", ".join(pre_high + pre_medium)
                if (pre_high or pre_medium)
                else "No high-severity pre-stress flags; Stress Lab may still find material losses."
            ),
        },
        {
            "title": "Next step",
            "body": "Verify these hypotheses in Stress Test Lab before testing any candidate.",
        },
    ]
    return {"main_diagnosis": main, "findings": findings}


def simplify_behavior_headline(headline: str | None, metrics: dict[str, Any], dd: dict[str, Any]) -> str:
    cagr = fmt_pct(metrics.get("portfolio_cagr"))
    mdd = fmt_pct(dd.get("max_drawdown"))
    uw = dd.get("longest_underwater")
    if cagr and mdd:
        uw_text = f"{int(uw)}-month" if uw is not None else "extended"
        return (
            f"The portfolio delivered a {cagr} CAGR with a {mdd} maximum drawdown over the diagnostic window. "
            f"Volatility is moderate, but the {uw_text} underwater period shows that downside recovery still matters."
        )
    return headline or "Historical behavior summary is unavailable for this run."


def behavior_label(b22: dict[str, Any]) -> str:
    snap = b22.get("portfolio_behavior_snapshot") if isinstance(b22.get("portfolio_behavior_snapshot"), dict) else {}
    label = str(snap.get("overall_behavior_label") or "moderate").replace("_", " ").title()
    return f"Behavior diagnosis: {label} risk, meaningful drawdown"


def ownership_diagnosis(b21: dict[str, Any]) -> str:
    comp = b21.get("portfolio_composition_snapshot") if isinstance(b21.get("portfolio_composition_snapshot"), dict) else {}
    dom_ac = human_token((comp.get("dominant_asset_class") or {}).get("name"))
    dom_region = human_token((comp.get("dominant_region") or {}).get("name"))
    dom_cur = human_token((comp.get("dominant_currency") or {}).get("name"))
    return (
        f"The portfolio is mainly allocated to {dom_ac.lower()} and equity-sensitive assets, "
        f"with strong {dom_region} / {dom_cur} exposure."
    )


def risk_contribution_diagnosis(b25: dict[str, Any]) -> str:
    top1 = b25.get("top1_rc_asset") if isinstance(b25.get("top1_rc_asset"), dict) else {}
    ticker = top1.get("ticker") or "the largest holding"
    top3_share = fmt_pct(b25.get("top3_rc_share"))
    return (
        f"{ticker} is the largest normal risk contributor. "
        f"The top three holdings create {top3_share or '—'} of total variance risk, "
        "meaning risk is more concentrated than the number of holdings suggests."
    )


def stress_main_diagnosis(
    *,
    worst_syn: dict[str, Any],
    main_gap: dict[str, Any],
    hg_row: dict[str, Any] | None,
) -> str:
    loss = fmt_pct(worst_syn.get("portfolio_loss_pct"))
    coverage = fmt_pct((main_gap or {}).get("offset_coverage_ratio") or (hg_row or {}).get("offset_coverage_ratio"))
    scenario = scenario_label(worst_syn.get("scenario_id"))
    return (
        f"The portfolio's largest stress weakness is {scenario.lower()}. "
        f"In this scenario, the portfolio loses about {loss}, while assets that helped offset only "
        f"{coverage} of losses from hurt assets. The issue is not only the loss itself, but weak "
        "internal protection when risk-sensitive assets decline together."
    )


def assets_hurt_helped_interpretation(hurt: list[dict[str, Any]], helped: list[dict[str, Any]]) -> str:
    hurt_names = ", ".join(h["ticker"] for h in hurt[:3] if h.get("ticker"))
    if helped and hurt_names:
        lead_help = helped[0].get("ticker")
        return f"{lead_help} helped, but not enough to offset losses from {hurt_names}."
    if hurt_names:
        return f"Losses were concentrated in {hurt_names}."
    return "Asset-level hurt/helped attribution is unavailable for this scenario."


def scorecard_confirmed_labels(scorecard: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    confirmed: list[str] = []
    partial: list[str] = []
    not_confirmed: list[str] = []
    psc = scorecard.get("pre_stress_confirmation_summary")
    if not isinstance(psc, dict):
        return confirmed, partial, not_confirmed
    hidden = psc.get("hidden_exposure")
    if isinstance(hidden, dict):
        for row in hidden.get("confirmation_rows") or []:
            if not isinstance(row, dict):
                continue
            name = _ALERT_LABEL.get(str(row.get("alert_id") or ""), human_token(row.get("alert_id")))
            status = str(row.get("confirmation_status") or "")
            if status == "confirmed":
                confirmed.append(name)
            elif status == "partially_confirmed":
                partial.append(f"{name} (partial)")
            elif status == "not_confirmed":
                not_confirmed.append(name)
    return confirmed, partial, not_confirmed


def hedge_gap_metrics(hg_summary: dict[str, Any], hedge_gap: dict[str, Any]) -> dict[str, Any]:
    main = hg_summary.get("main_hedge_gap") if isinstance(hg_summary.get("main_hedge_gap"), dict) else {}
    risk_type = main.get("risk_type")
    row = None
    for item in hedge_gap.get("by_risk_type") or []:
        if isinstance(item, dict) and item.get("risk_type") == risk_type:
            row = item
            break

    gross = None
    positive = None
    if isinstance(row, dict):
        gross = fmt_pct(row.get("gross_loss_from_assets_hurt"), signed=True)
        positive = fmt_pct(row.get("positive_contribution_from_assets_helped"), signed=True)

    return {
        "main_gap": protection_label(risk_type),
        "scenario": scenario_label(main.get("linked_scenario_id")),
        "portfolio_loss": fmt_pct(main.get("portfolio_loss_pct")),
        "gross_loss": gross,
        "gross_loss_label": gross if gross else "Unavailable in current summary output",
        "positive_help": positive,
        "positive_help_label": positive if positive else "Unavailable in current summary output",
        "offset_coverage": fmt_pct(main.get("offset_coverage_ratio")),
        "protection_status": protection_status_human(main.get("protection_status")),
        "interpretation": (
            "In the worst stress scenario, helped assets covered only "
            f"{fmt_pct(main.get('offset_coverage_ratio'))} of losses from hurt assets. "
            "This indicates weak internal protection."
        ),
    }


def clean_technical_text(text: str) -> str:
    """Strip obvious backend leakage from legacy strings."""
    if not text:
        return ""
    out = text
    for token, label in _TOKEN_LABEL.items():
        out = re.sub(rf"\b{re.escape(token)}\b", label, out, flags=re.IGNORECASE)
    out = re.sub(r"\bBlock 2\.\d\b", "", out)
    out = re.sub(r"\s+", " ", out).strip()
    return out
