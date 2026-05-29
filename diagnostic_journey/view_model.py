"""View model for Blocks 1–3 diagnostic journey UI (reads analysis_subject JSON only)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from diagnostic_journey import presentation as P

_UNAVAILABLE = "Unavailable"
_CLASS_UNAVAILABLE = "Classification unavailable"


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else None


def _pct(value: Any, **kwargs: Any) -> str:
    return P.fmt_pct(value, **kwargs) or _UNAVAILABLE


def build_diagnostic_journey_view_model(
    subject_dir: Path,
    *,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Build template context from ``{output_dir_final}/analysis_subject/`` artifacts."""
    subject_dir = subject_dir.resolve()
    root = project_root or subject_dir.parent.parent

    run_meta = _load_json(subject_dir / "run_metadata.json") or {}
    xray = _load_json(subject_dir / "portfolio_xray.json") or {}
    stress = _load_json(subject_dir / "stress_report.json") or {}
    problem = _load_json(subject_dir / "problem_classification.json")
    launchpad = _load_json(subject_dir / "candidate_launchpad.json")

    setup = run_meta.get("analysis_setup") if isinstance(run_meta.get("analysis_setup"), dict) else {}
    subject = setup.get("analysis_subject") if isinstance(setup.get("analysis_subject"), dict) else {}
    weights_map = subject.get("weights") if isinstance(subject.get("weights"), dict) else {}
    input_assumptions = (
        run_meta.get("input_assumptions") if isinstance(run_meta.get("input_assumptions"), dict) else {}
    )
    core_input = (
        input_assumptions.get("core_mvp_input_contract")
        if isinstance(input_assumptions.get("core_mvp_input_contract"), dict)
        else {}
    )
    currency_block = (
        input_assumptions.get("currency_and_market")
        if isinstance(input_assumptions.get("currency_and_market"), dict)
        else {}
    )

    b21 = xray.get("block_2_1_asset_allocation") if isinstance(xray.get("block_2_1_asset_allocation"), dict) else {}
    b22 = xray.get("block_2_2_portfolio_metrics") if isinstance(xray.get("block_2_2_portfolio_metrics"), dict) else {}
    b23 = xray.get("block_2_3_factor_exposure") if isinstance(xray.get("block_2_3_factor_exposure"), dict) else {}
    b24 = xray.get("block_2_4_hidden_exposure") if isinstance(xray.get("block_2_4_hidden_exposure"), dict) else {}
    b25 = xray.get("block_2_5_risk_budget_view") if isinstance(xray.get("block_2_5_risk_budget_view"), dict) else {}
    b26 = xray.get("block_2_6_portfolio_weakness_map") if isinstance(xray.get("block_2_6_portfolio_weakness_map"), dict) else {}
    xray_summary = xray.get("analysis_setup_summary") if isinstance(xray.get("analysis_setup_summary"), dict) else {}

    has_xray = bool(xray)
    has_stress = bool(stress)
    comp = b21.get("portfolio_composition_snapshot") if isinstance(b21.get("portfolio_composition_snapshot"), dict) else {}

    # —— Block 1 ——
    weight_sum = subject.get("weight_sum")
    if weight_sum is None and isinstance(setup.get("portfolio_input"), dict):
        cw = setup["portfolio_input"].get("current_weights")
        if isinstance(cw, dict):
            weight_sum = cw.get("weight_sum")

    taxonomy = P.load_ticker_taxonomy(root, list(weights_map.keys()))
    holdings_rows: list[dict[str, Any]] = []
    for ticker, w in sorted(weights_map.items(), key=lambda kv: (-float(kv[1] or 0), kv[0])):
        try:
            wt = float(w)
        except (TypeError, ValueError):
            continue
        meta = taxonomy.get(str(ticker).upper(), {})
        holdings_rows.append(
            {
                "ticker": ticker,
                "weight_pct": _pct(wt),
                "asset_class": meta.get("asset_class") or _CLASS_UNAVAILABLE,
                "risk_role": meta.get("risk_role") or _CLASS_UNAVAILABLE,
                "status": "OK",
            }
        )

    validation = run_meta.get("validation_result") if isinstance(run_meta.get("validation_result"), dict) else {}
    val_raw = str(validation.get("status") or ("valid" if run_meta.get("portfolio_valid") else "review"))
    val_label = "Passed" if val_raw.lower() in {"valid", "passed", "ok"} else val_raw.title()

    cash_remainder = None
    if isinstance(setup.get("portfolio_input"), dict):
        cw = setup["portfolio_input"].get("current_weights")
        if isinstance(cw, dict):
            cash_remainder = cw.get("cash_remainder")

    investor_ccy = (
        core_input.get("investor_currency")
        or currency_block.get("investor_currency")
        or xray_summary.get("investor_currency")
        or "USD"
    )

    block1 = {
        "title": "Portfolio ready for diagnosis",
        "lead": (
            "Your current portfolio has been loaded. The system will first diagnose the portfolio as it is. "
            "No candidate, rebalance, or recommendation has been generated yet."
        ),
        "holdings_count": len(holdings_rows) or subject.get("ticker_count") or len(weights_map),
        "weight_total": _pct(weight_sum if weight_sum is not None else 1.0),
        "investor_currency": investor_ccy,
        "cash_position": _pct(cash_remainder) if cash_remainder and float(cash_remainder) > 0.001 else "Not included",
        "mode": "Current portfolio diagnosis",
        "validation_status": val_label,
        "holdings": holdings_rows,
        "no_reco_note": "No recommendation yet. This step only defines the portfolio to be diagnosed.",
        "next_steps": [
            "Diagnose the current portfolio structure.",
            "Identify hidden exposures and concentration.",
            "Stress-test the main weaknesses.",
            "Suggest testable improvement paths only after diagnosis.",
        ],
        "assumptions": {
            "benchmark": xray_summary.get("base_benchmark_ticker") or currency_block.get("base_benchmark_ticker") or _UNAVAILABLE,
            "risk_free": "US Treasury bills (FRED proxy)" if investor_ccy == "USD" else _UNAVAILABLE,
            "return_frequency": "Monthly returns",
            "analysis_window": "3Y, 5Y, and 10Y diagnostic windows",
            "cash_treatment": "Market tickers only; cash proxy not held separately" if not cash_remainder else "Cash remainder tracked separately",
            "fx": "No FX conversion required" if investor_ccy == "USD" else "FX conversion per investor currency policy",
            "data_provider": "Market data via configured provider",
            "warnings": [P.clean_technical_text(str(w)) for w in (b21.get("data_quality_warnings") or [])[:5]],
        },
        "analysis_end": (run_meta.get("run_info") or {}).get("analysis_end_date") if isinstance(run_meta.get("run_info"), dict) else None,
    }

    # —— Block 2 ——
    block2_exec = P.build_executive_diagnosis(b21=b21, b22=b22, b23=b23, b24=b24, b25=b25, b26=b26)
    block2_exec["title"] = "Portfolio X-Ray diagnosis"
    block2_exec["subtitle"] = "What the portfolio really owns, what drives its behavior, and what should be stress-tested next."

    top1 = comp.get("top1_holding") if isinstance(comp.get("top1_holding"), dict) else {}
    block2_own = {
        "diagnosis": P.ownership_diagnosis(b21),
        "interpretation": (
            "The portfolio is diversified by ticker count, but capital remains meaningfully concentrated "
            "in a few holdings and one currency regime."
        ),
        "total_holdings": comp.get("total_holdings"),
        "top_holding": f"{top1.get('ticker', '—')} · {_pct(top1.get('weight_pct'))}" if top1.get("ticker") else _UNAVAILABLE,
        "top3_weight": _pct(comp.get("top3_weight_pct")),
        "dominant_asset_class": P.human_token((comp.get("dominant_asset_class") or {}).get("name")),
        "dominant_region": P.human_token((comp.get("dominant_region") or {}).get("name")),
        "dominant_currency": P.human_token((comp.get("dominant_currency") or {}).get("name")),
        "dominant_risk_role": P.human_token((comp.get("dominant_risk_role") or {}).get("name")),
        "drilldown": {
            "by_asset_class": [
                {"name": P.human_token(r.get("name")), "weight": _pct(r.get("weight_pct"))}
                for r in ((b21.get("capital_allocation_breakdown") or {}).get("by_asset_class") or [])
                if isinstance(r, dict)
            ],
        },
    }

    metrics = b22.get("return_risk_metrics") if isinstance(b22.get("return_risk_metrics"), dict) else {}
    dd = b22.get("drawdown_diagnostics") if isinstance(b22.get("drawdown_diagnostics"), dict) else {}
    bench = b22.get("benchmark_dependence") if isinstance(b22.get("benchmark_dependence"), dict) else {}
    block2_behave = {
        "behavior_label": P.behavior_label(b22),
        "diagnosis": P.simplify_behavior_headline(None, metrics, dd),
        "cagr": _pct(metrics.get("portfolio_cagr")),
        "vol": _pct(metrics.get("vol_annual")),
        "sharpe": P.fmt_num(metrics.get("sharpe")) or _UNAVAILABLE,
        "max_drawdown": _pct(dd.get("max_drawdown")),
        "beta": P.fmt_num(bench.get("beta_portfolio")) or _UNAVAILABLE,
        "longest_underwater": f"{int(dd['longest_underwater'])} months" if dd.get("longest_underwater") is not None else _UNAVAILABLE,
    }

    ranking = b23.get("factor_risk_ranking") if isinstance(b23.get("factor_risk_ranking"), list) else []
    drivers = []
    for row in ranking[:3]:
        if not isinstance(row, dict):
            continue
        contrib = float(row.get("contribution") or 0)
        exposure = "High" if contrib >= 0.35 else "Medium" if contrib >= 0.15 else "Low"
        conf_raw = str(row.get("confidence") or "")
        conf = (
            "Significant but less stable"
            if row.get("factor") == "real_rates"
            else P.confidence_human(conf_raw)
        )
        interp = row.get("interpretation") or ""
        if row.get("factor") == "equity":
            interp = "The portfolio remains meaningfully exposed to equity-market behavior."
        elif row.get("factor") == "real_rates":
            interp = "Interest-rate and duration sensitivity matter, but the signal is less stable across windows."
        elif row.get("factor") in {"USD", "usd"}:
            interp = "Currency exposure is a relevant portfolio driver."
        drivers.append(
            {
                "name": P.factor_label(row.get("factor")),
                "exposure": exposure,
                "confidence": conf,
                "interpretation": P.clean_technical_text(interp)[:220],
            }
        )

    factor_summary = b23.get("factor_exposure_summary") if isinstance(b23.get("factor_exposure_summary"), dict) else {}
    block2_factors = {
        "diagnosis": (
            "Portfolio behavior is mostly explained by three factor exposures: "
            + ", ".join(P.factor_label(f) for f in (factor_summary.get("top_3_factors") or [])[:3])
            + "."
            if factor_summary.get("top_3_factors")
            else "Factor driver evidence is unavailable."
        ),
        "confidence_note": (
            "Factor evidence is strongest for equity and USD. Real-rate sensitivity is meaningful, "
            "but less stable across model windows."
        ),
        "drivers": drivers,
    }

    alert_cards = []
    alerts = b24.get("alerts") if isinstance(b24.get("alerts"), dict) else {}
    for alert_id, alert in alerts.items():
        if not isinstance(alert, dict):
            continue
        card = P.build_hidden_alert_card(alert_id, alert, b21=b21, b22=b22, b23=b23)
        if card:
            alert_cards.append(card)
    block2_hidden = {
        "alerts": alert_cards,
        "note": (
            "These are diagnostic hypotheses before stress testing. Stress Lab will verify "
            "which risks actually matter under stress."
        ),
    }

    top1_rc = b25.get("top1_rc_asset") if isinstance(b25.get("top1_rc_asset"), dict) else {}
    gap_assets = b25.get("top_risk_overweight_assets") if isinstance(b25.get("top_risk_overweight_assets"), list) else []
    largest_gap = gap_assets[0] if gap_assets and isinstance(gap_assets[0], dict) else {}
    block2_risk = {
        "diagnosis": P.risk_contribution_diagnosis(b25),
        "top_contributor": top1_rc.get("ticker") or _UNAVAILABLE,
        "top3_share": _pct(b25.get("top3_rc_share")),
        "largest_gap": largest_gap.get("ticker") or _UNAVAILABLE,
        "disclaimer": "Risk contribution shows normal portfolio variance risk, not losses in a stress scenario.",
    }

    weakness_groups: dict[str, list[dict[str, Any]]] = {"High": [], "Medium": [], "Low": []}
    for row in b26.get("risk_types") or []:
        if not isinstance(row, dict):
            continue
        card = P.build_weakness_card(row, b22=b22, b23=b23)
        bucket = card["severity"] if card["severity"] in weakness_groups else "Low"
        weakness_groups[bucket].append(card)

    block2_weakness = {
        "title": "Pre-stress weakness map",
        "subtitle": "Which market shocks should be tested next.",
        "groups": weakness_groups,
        "no_high_note": (
            "No High pre-stress weakness was detected by rule score. "
            "Stress Lab may still identify material losses under specific scenarios."
        ),
        "pre_stress_note": (
            "This is a pre-stress hypothesis. Stress Lab will verify whether the portfolio "
            "actually breaks in these scenarios."
        ),
        "has_high": bool(weakness_groups["High"]),
    }

    # —— Block 3 ——
    stress_results = stress.get("stress_results_v1") if isinstance(stress.get("stress_results_v1"), dict) else {}
    envelope = stress_results.get("envelope") if isinstance(stress_results.get("envelope"), dict) else {}
    worst_syn = envelope.get("worst_synthetic") if isinstance(envelope.get("worst_synthetic"), dict) else {}
    worst_hist = envelope.get("worst_historical") if isinstance(envelope.get("worst_historical"), dict) else {}
    hedge_gap = stress.get("hedge_gap_analysis_v1") if isinstance(stress.get("hedge_gap_analysis_v1"), dict) else {}
    hg_summary = hedge_gap.get("summary") if isinstance(hedge_gap.get("summary"), dict) else {}
    main_gap = hg_summary.get("main_hedge_gap") if isinstance(hg_summary.get("main_hedge_gap"), dict) else {}
    scorecard = stress.get("current_portfolio_stress_scorecard_v1") if isinstance(stress.get("current_portfolio_stress_scorecard_v1"), dict) else {}

    hurt = [
        {"ticker": h.get("ticker"), "contribution": _pct(h.get("pnl_pct"), signed=True)}
        for h in (worst_syn.get("top3_loss_assets") or worst_syn.get("assets_hurt") or [])[:3]
        if isinstance(h, dict)
    ]
    helped = [
        {"ticker": h.get("ticker"), "contribution": _pct(h.get("pnl_pct"), signed=True)}
        for h in (worst_syn.get("helped_assets") or [])[:3]
        if isinstance(h, dict)
    ]

    block3_summary = {
        "title": "Current portfolio stress diagnosis",
        "diagnosis": P.stress_main_diagnosis(worst_syn=worst_syn, main_gap=main_gap, hg_row=None),
        "worst_synthetic": P.scenario_label(worst_syn.get("scenario_id")),
        "portfolio_loss": _pct(worst_syn.get("portfolio_loss_pct")),
        "offset_coverage": _pct(main_gap.get("offset_coverage_ratio")),
        "main_hedge_gap": P.protection_label(main_gap.get("risk_type")),
        "worst_historical": (
            f"{worst_hist.get('episode')} · {_pct(worst_hist.get('drawdown_pct'))}"
            if worst_hist.get("episode")
            else None
        ),
        "hurt": hurt,
        "helped": helped,
        "interpretation": P.assets_hurt_helped_interpretation(hurt, helped),
    }

    scenarios_sorted: list[dict[str, Any]] = []
    for row in stress.get("scenario_results") or []:
        if not isinstance(row, dict):
            continue
        sid = row.get("scenario_id")
        scenarios_sorted.append(
            {
                "label": P.scenario_label(sid),
                "loss": _pct(row.get("portfolio_pnl_pct")),
                "loss_raw": row.get("portfolio_pnl_pct"),
                "hint": P.scenario_hint(sid),
            }
        )
    scenarios_sorted.sort(key=lambda r: float(r.get("loss_raw") or 0))
    mid = max(1, len(scenarios_sorted) // 2)
    block3_scenarios = {
        "most_damaging": scenarios_sorted[:mid],
        "less_damaging": scenarios_sorted[mid:],
    }

    block3_assets = {
        "title": "Assets hurt / helped in the worst scenario",
        "subtitle": "Labels are based on actual scenario contribution, not asset names.",
        "scenario": P.scenario_label(worst_syn.get("scenario_id")),
        "hurt": hurt,
        "helped": helped,
        "interpretation": (
            "Losses were concentrated in equity-sensitive and macro-sensitive holdings. "
            "Defensive contributors helped, but only partially."
        ),
    }

    block3_hedge = P.hedge_gap_metrics(hg_summary, hedge_gap)

    confirmed, partial, not_confirmed = P.scorecard_confirmed_labels(scorecard)
    all_confirmed = confirmed + [p for p in partial if p]
    failure = (
        "Risk-sensitive assets decline together, while helped assets offset only a small share of losses."
    )
    hedge_gap_line = (
        f"{P.protection_label(main_gap.get('risk_type'))} is weak because helped assets offset only "
        f"{_pct(main_gap.get('offset_coverage_ratio'))} of losses from hurt assets."
    )
    next_uses = scorecard.get("next_decision_uses") if isinstance(scorecard.get("next_decision_uses"), list) else []
    next_use_human = (
        "Any candidate should be judged by whether it reduces severe recession loss, lowers loss concentration, "
        "or improves offset coverage without excessive turnover."
        if not next_uses or "problem_classification" in str(next_uses[0])
        else P.clean_technical_text(str(next_uses[0]))
    )

    block3_scorecard = {
        "main_weakness": P.scenario_label(
            (scorecard.get("worst_synthetic_scenario") or {}).get("scenario_id")
            if isinstance(scorecard.get("worst_synthetic_scenario"), dict)
            else worst_syn.get("scenario_id")
        ),
        "confirmed": all_confirmed or ["See Stress Lab evidence in drill-down"],
        "not_confirmed": not_confirmed,
        "failure_mode": failure,
        "hedge_gap_line": hedge_gap_line,
        "next_use": next_use_human,
    }

    bridge_cards = _bridge_cards(launchpad, problem, block3_hedge, block2_risk, block2_weakness)

    return {
        "project_root": str(root),
        "subject_dir": str(subject_dir),
        "has_data": bool(weights_map or has_xray),
        "has_xray": has_xray,
        "has_stress": has_stress,
        "analysis_end": block1.get("analysis_end"),
        "block1": block1,
        "block2_exec": block2_exec,
        "block2_own": block2_own,
        "block2_behave": block2_behave,
        "block2_factors": block2_factors,
        "block2_hidden": block2_hidden,
        "block2_risk": block2_risk,
        "block2_weakness": block2_weakness,
        "block3_summary": block3_summary,
        "block3_scenarios": block3_scenarios,
        "block3_assets": block3_assets,
        "block3_hedge": block3_hedge,
        "block3_scorecard": block3_scorecard,
        "bridge": {
            "title": "Diagnosis complete — suggested next paths",
            "subtitle": "No candidate generated yet. These are testable hypotheses, not recommendations.",
            "optional_note": "You can stop here. Diagnosis-only output is already valid. Candidate testing is optional.",
            "cards": bridge_cards[:3],
            "no_trade_note": "No-trade and keep current portfolio remain valid outcomes.",
        },
    }


def _bridge_cards(
    launchpad: dict[str, Any] | None,
    problem: dict[str, Any] | None,
    hedge: dict[str, Any],
    risk: dict[str, Any],
    weakness: dict[str, Any],
) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    if isinstance(launchpad, dict):
        for card in launchpad.get("cards") or []:
            if not isinstance(card, dict) or len(cards) >= 3:
                break
            cards.append(_bridge_card_from_launchpad(card))
    if isinstance(problem, dict) and len(cards) < 3:
        for path in problem.get("improvement_paths") or problem.get("paths") or []:
            if not isinstance(path, dict) or len(cards) >= 3:
                break
            cards.append(
                {
                    "title": path.get("path_label") or path.get("goal") or "Improvement hypothesis",
                    "why": P.clean_technical_text(str(path.get("why") or "")),
                    "suggested_test": P.clean_technical_text(str(path.get("suggested_candidate_family") or "Candidate family TBD")),
                    "goal": P.clean_technical_text(str(path.get("goal") or "")),
                }
            )
    if not cards:
        if hedge.get("main_gap") and hedge.get("main_gap") != _UNAVAILABLE:
            cards.append(
                {
                    "title": "Improve crisis resilience",
                    "why": f"Main hedge gap detected in {hedge.get('main_gap', 'stress')}.",
                    "suggested_test": "Minimum CVaR (constrained) or robust scenario candidate",
                    "goal": "Reduce tail losses and improve offset coverage in severe stress scenarios.",
                }
            )
        if weakness.get("has_high"):
            cards.append(
                {
                    "title": "Reduce drawdown risk",
                    "why": "Worst stress scenario creates a material portfolio loss.",
                    "suggested_test": "Minimum variance or minimum CVaR",
                    "goal": "Lower drawdown and reduce severe recession loss.",
                }
            )
        elif not weakness.get("has_high"):
            cards.append(
                {
                    "title": "Reduce drawdown risk",
                    "why": "Stress testing shows meaningful loss in the worst synthetic scenario.",
                    "suggested_test": "Minimum variance or minimum CVaR",
                    "goal": "Lower drawdown and reduce severe recession loss.",
                }
            )
        top = risk.get("top_contributor")
        if top and top != _UNAVAILABLE:
            cards.append(
                {
                    "title": "Improve diversification",
                    "why": f"Risk is concentrated in {top} and other top contributors relative to capital weights.",
                    "suggested_test": "Risk parity or equal weight by asset class",
                    "goal": "Reduce dependence on top variance risk contributors.",
                }
            )
    for card in cards:
        card.setdefault("cta", "Open in Builder")
    return cards


def _bridge_card_from_launchpad(card: dict[str, Any]) -> dict[str, Any]:
    methods = card.get("candidate_methods") or card.get("methods") or []
    method_labels = {
        "minimum_cvar_constrained": "Minimum CVaR (constrained)",
        "robust_scenario": "Robust scenario candidate",
        "minimum_variance": "Minimum variance",
        "risk_parity": "Risk parity",
        "equal_weight_by_asset_class": "Equal weight by asset class",
        "equal_weight": "Equal weight",
    }
    tests = ", ".join(method_labels.get(str(m), P.human_token(m)) for m in methods[:2]) or "See launchpad"
    return {
        "title": card.get("goal") or card.get("title") or "Improvement hypothesis",
        "why": P.clean_technical_text(str(card.get("why") or card.get("rationale") or "")),
        "suggested_test": tests,
        "goal": P.clean_technical_text(str(card.get("goal_description") or card.get("description") or "")),
        "cta": "Open in Builder",
    }
