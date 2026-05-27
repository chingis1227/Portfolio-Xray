"""Block 3.4 Current Portfolio Stress Scorecard — current_portfolio_stress_scorecard_v1.

This is a diagnostic-only, product-facing summary layer that **reuses** existing Stress Lab
outputs on ``stress_report.json``:

- Block 3.1 evidence: ``scenario_results[]`` + ``historical_results[]``
- Block 3.2 product adapter: ``stress_results_v1``
- Block 3.3 product adapter: ``hedge_gap_analysis_v1``

It must not introduce mandate pass/fail, suitability logic, or DIAG_* language.
It must not create a new stress engine and must not add scenarios.
"""

from __future__ import annotations

from typing import Any

BLOCK_3_4_VERSION = "current_portfolio_stress_scorecard_v1"
_LOSS_GATE_MODE_DIAGNOSTIC = "diagnostic"
_LOSS_GATE_MODE_MANDATE = "mandate"


def attach_current_portfolio_stress_scorecard_v1(stress_report: dict[str, Any]) -> None:
    """Rebuild ``current_portfolio_stress_scorecard_v1`` on *stress_report* (in-place)."""
    stress_report[BLOCK_3_4_VERSION] = build_current_portfolio_stress_scorecard_v1(stress_report)


def empty_current_portfolio_stress_scorecard_v1(
    reason: str = "no_data",
    *,
    loss_gate_mode: str = _LOSS_GATE_MODE_DIAGNOSTIC,
) -> dict[str, Any]:
    gate_mode = _normalize_gate_mode(loss_gate_mode)
    return {
        "version": BLOCK_3_4_VERSION,
        "block": "3.4",
        "scenario_library": None,
        "loss_gate_mode": gate_mode,
        "worst_synthetic_scenario": {"availability": "unavailable", "reason_en": reason},
        "worst_historical_scenario": {"availability": "unavailable", "reason_en": reason},
        "portfolio_loss_summary": {"availability": "unavailable", "reason_en": reason},
        "historical_drawdown_summary": {"availability": "unavailable", "reason_en": reason},
        "top_loss_contributors": {"availability": "unavailable", "reason_en": reason},
        "top_risk_contributors": {"availability": "unavailable", "reason_en": reason},
        "factor_stress_attribution_summary": {"availability": "unavailable", "reason_en": reason},
        "assets_helped_hurt_summary": {"availability": "unavailable", "reason_en": reason},
        "offset_coverage_summary": {"availability": "unavailable", "reason_en": reason},
        "main_hedge_gap": {"availability": "unavailable", "reason_en": reason},
        "data_quality_warnings": [reason],
        "diagnosis_summary_en": None,
    }


def build_current_portfolio_stress_scorecard_v1(stress_report: dict[str, Any]) -> dict[str, Any]:
    """Build Block 3.4 summary from existing Stress Lab outputs on *stress_report*."""
    gate_mode = _normalize_gate_mode(str(stress_report.get("loss_gate_mode") or _LOSS_GATE_MODE_DIAGNOSTIC))

    stress_results = stress_report.get("stress_results_v1")
    stress_results = stress_results if isinstance(stress_results, dict) else {}

    hedge_gap = stress_report.get("hedge_gap_analysis_v1")
    hedge_gap = hedge_gap if isinstance(hedge_gap, dict) else {}

    conclusions = stress_report.get("stress_conclusions")
    conclusions = conclusions if isinstance(conclusions, dict) else {}

    trust = stress_report.get("data_trust_summary")
    trust = trust if isinstance(trust, dict) else {}

    scenario_library = stress_results.get("scenario_library")
    if not isinstance(scenario_library, dict):
        scenario_library = hedge_gap.get("scenario_library") if isinstance(hedge_gap.get("scenario_library"), dict) else None

    env = stress_results.get("envelope") if isinstance(stress_results.get("envelope"), dict) else {}
    worst_syn = env.get("worst_synthetic") if isinstance(env.get("worst_synthetic"), dict) else None
    worst_hist = env.get("worst_historical") if isinstance(env.get("worst_historical"), dict) else None

    synthetic_rows = stress_results.get("synthetic_scenarios") if isinstance(stress_results.get("synthetic_scenarios"), list) else []
    historical_rows = stress_results.get("historical_episodes") if isinstance(stress_results.get("historical_episodes"), list) else []

    worst_synthetic_scenario = _build_worst_synthetic_block(worst_syn)
    worst_historical_scenario = _build_worst_historical_block(worst_hist)

    top_loss_contributors = _build_top_loss_contributors(
        worst_syn=worst_syn,
        worst_hist=worst_hist,
    )
    top_risk_contributors = _build_top_risk_contributors(
        synthetic_rows=synthetic_rows,
        worst_synthetic_id=worst_syn.get("scenario_id") if isinstance(worst_syn, dict) else None,
    )
    factor_attr = _build_factor_stress_attribution_summary(
        worst_syn=worst_syn,
        conclusions=conclusions,
    )
    assets_helped_hurt = _build_assets_helped_hurt_summary(
        worst_syn=worst_syn,
        hedge_gap=hedge_gap,
    )
    offset_coverage, main_hedge_gap = _build_offset_and_main_gap(hedge_gap)

    portfolio_loss_summary = _build_portfolio_loss_summary(worst_syn=worst_syn, worst_hist=worst_hist)
    historical_drawdown_summary = _build_historical_drawdown_summary(worst_hist=worst_hist)

    warnings = _collect_data_quality_warnings(
        historical_rows=historical_rows,
        hedge_gap=hedge_gap,
        trust=trust,
        conclusions=conclusions,
    )

    diagnosis_summary_en = _format_diagnosis_summary_en(
        worst_synthetic=worst_synthetic_scenario,
        worst_historical=worst_historical_scenario,
        main_hedge_gap=main_hedge_gap,
        warnings=warnings,
    )

    return {
        "version": BLOCK_3_4_VERSION,
        "block": "3.4",
        "scenario_library": scenario_library,
        "loss_gate_mode": gate_mode,
        "worst_synthetic_scenario": worst_synthetic_scenario,
        "worst_historical_scenario": worst_historical_scenario,
        "portfolio_loss_summary": portfolio_loss_summary,
        "historical_drawdown_summary": historical_drawdown_summary,
        "top_loss_contributors": top_loss_contributors,
        "top_risk_contributors": top_risk_contributors,
        "factor_stress_attribution_summary": factor_attr,
        "assets_helped_hurt_summary": assets_helped_hurt,
        "offset_coverage_summary": offset_coverage,
        "main_hedge_gap": main_hedge_gap,
        "data_quality_warnings": warnings,
        "diagnosis_summary_en": diagnosis_summary_en,
    }


def _normalize_gate_mode(loss_gate_mode: str) -> str:
    mode = str(loss_gate_mode or "").strip().lower()
    if mode == _LOSS_GATE_MODE_DIAGNOSTIC:
        return _LOSS_GATE_MODE_DIAGNOSTIC
    return _LOSS_GATE_MODE_MANDATE


def _build_worst_synthetic_block(worst_syn: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(worst_syn, dict):
        return {"availability": "unavailable", "reason_en": "worst_synthetic_unavailable"}
    return {
        "availability": "available",
        "scenario_id": worst_syn.get("scenario_id"),
        "portfolio_loss_pct": worst_syn.get("portfolio_loss_pct"),
    }


def _build_worst_historical_block(worst_hist: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(worst_hist, dict):
        return {"availability": "unavailable", "reason_en": "worst_historical_unavailable"}
    return {
        "availability": "available",
        "episode": worst_hist.get("episode"),
        "portfolio_loss_pct": worst_hist.get("portfolio_loss_pct"),
        "drawdown_pct": worst_hist.get("drawdown_pct"),
    }


def _build_portfolio_loss_summary(
    *,
    worst_syn: dict[str, Any] | None,
    worst_hist: dict[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(worst_syn, dict) and not isinstance(worst_hist, dict):
        return {"availability": "unavailable", "reason_en": "loss_summary_unavailable"}
    return {
        "availability": "available",
        "synthetic": (
            {
                "scenario_id": worst_syn.get("scenario_id"),
                "portfolio_pnl_pct": worst_syn.get("portfolio_loss_pct"),
            }
            if isinstance(worst_syn, dict)
            else {"availability": "unavailable", "reason_en": "worst_synthetic_unavailable"}
        ),
        "historical": (
            {
                "episode": worst_hist.get("episode"),
                "pnl_real_episode": worst_hist.get("portfolio_loss_pct"),
            }
            if isinstance(worst_hist, dict)
            else {"availability": "unavailable", "reason_en": "worst_historical_unavailable"}
        ),
    }


def _build_historical_drawdown_summary(*, worst_hist: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(worst_hist, dict):
        return {"availability": "unavailable", "reason_en": "worst_historical_unavailable"}
    return {
        "availability": "available",
        "episode": worst_hist.get("episode"),
        "max_dd": worst_hist.get("drawdown_pct"),
    }


def _build_top_loss_contributors(
    *,
    worst_syn: dict[str, Any] | None,
    worst_hist: dict[str, Any] | None,
) -> dict[str, Any]:
    out: dict[str, Any] = {"availability": "available", "synthetic": None, "historical": None}
    if isinstance(worst_syn, dict):
        out["synthetic"] = {
            "scenario_id": worst_syn.get("scenario_id"),
            "top3_loss_assets": list(worst_syn.get("top3_loss_assets") or []),
        }
    else:
        out["synthetic"] = {"availability": "unavailable", "reason_en": "worst_synthetic_unavailable"}
    if isinstance(worst_hist, dict):
        out["historical"] = {
            "episode": worst_hist.get("episode"),
            "top3_loss_assets": list(worst_hist.get("top3_loss_assets") or []),
        }
    else:
        out["historical"] = {"availability": "unavailable", "reason_en": "worst_historical_unavailable"}
    if not isinstance(worst_syn, dict) and not isinstance(worst_hist, dict):
        out["availability"] = "unavailable"
        out["reason_en"] = "top_loss_contributors_unavailable"
    return out


def _build_top_risk_contributors(
    *,
    synthetic_rows: list[Any],
    worst_synthetic_id: str | None,
) -> dict[str, Any]:
    if not synthetic_rows or not worst_synthetic_id:
        return {"availability": "unavailable", "reason_en": "risk_contribution_unavailable"}
    worst_row: dict[str, Any] | None = None
    for row in synthetic_rows:
        if isinstance(row, dict) and row.get("scenario_id") == worst_synthetic_id:
            worst_row = row
            break
    if worst_row is None:
        return {"availability": "unavailable", "reason_en": "worst_synthetic_row_missing"}
    rc = worst_row.get("risk_contribution")
    if not isinstance(rc, dict) or rc.get("availability") != "available":
        reason = rc.get("reason_en") if isinstance(rc, dict) else "risk_contribution_unavailable"
        return {"availability": "unavailable", "reason_en": reason}
    return {
        "availability": "available",
        "scenario_id": worst_synthetic_id,
        "top1_rc_asset": rc.get("top1_rc_asset"),
        "top1_rc_pct": rc.get("top1_rc_pct"),
        "top3_rc_assets": list(rc.get("top3_rc_assets") or []),
        "top3_rc_sum_pct": rc.get("top3_rc_sum_pct"),
    }


def _build_factor_stress_attribution_summary(
    *,
    worst_syn: dict[str, Any] | None,
    conclusions: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(worst_syn, dict):
        return {"availability": "unavailable", "reason_en": "worst_synthetic_unavailable"}
    drivers = list(worst_syn.get("top_factor_drivers") or [])
    helped_factors = conclusions.get("helped_factors_worst_scenario")
    helped_factors_list = list(helped_factors) if isinstance(helped_factors, list) else []
    return {
        "availability": "available",
        "scenario_id": worst_syn.get("scenario_id"),
        "top_factor_drivers": drivers,
        "helped_factors": helped_factors_list,
    }


def _build_assets_helped_hurt_summary(
    *,
    worst_syn: dict[str, Any] | None,
    hedge_gap: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(worst_syn, dict):
        return {"availability": "unavailable", "reason_en": "worst_synthetic_unavailable"}
    helped = list(worst_syn.get("helped_assets") or [])
    hurt_top3 = list(worst_syn.get("top3_loss_assets") or [])

    # Hedge gap: contribution-based helped/hurt for the main hedge gap risk type (when available).
    main_assets: dict[str, Any] | None = None
    main_row = _resolve_main_hedge_gap_row(hedge_gap)
    if main_row is not None:
        main_assets = {
            "risk_type": main_row.get("risk_type"),
            "linked_scenario_id": main_row.get("linked_scenario_id"),
            "assets_hurt": list(main_row.get("assets_hurt") or []),
            "assets_helped": list(main_row.get("assets_helped") or []),
        }

    return {
        "availability": "available",
        "worst_synthetic": {
            "scenario_id": worst_syn.get("scenario_id"),
            "assets_helped": helped,
            "assets_hurt_top3": hurt_top3,
        },
        "hedge_gap_main_area": main_assets,
    }


def _resolve_main_hedge_gap_row(hedge_gap: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(hedge_gap, dict) or hedge_gap.get("version") != "hedge_gap_analysis_v1":
        return None
    summary = hedge_gap.get("summary") if isinstance(hedge_gap.get("summary"), dict) else {}
    main = summary.get("main_hedge_gap") if isinstance(summary.get("main_hedge_gap"), dict) else None
    if not isinstance(main, dict):
        return None
    risk_type = main.get("risk_type")
    linked_scenario_id = main.get("linked_scenario_id")
    if not risk_type or not linked_scenario_id:
        return None
    by_risk = hedge_gap.get("by_risk_type")
    if not isinstance(by_risk, list):
        return None
    for row in by_risk:
        if not isinstance(row, dict):
            continue
        if row.get("risk_type") == risk_type and row.get("linked_scenario_id") == linked_scenario_id:
            return row
    return None


def _build_offset_and_main_gap(hedge_gap: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(hedge_gap, dict) or hedge_gap.get("version") != "hedge_gap_analysis_v1":
        unavailable = {"availability": "unavailable", "reason_en": "hedge_gap_analysis_v1_unavailable"}
        return unavailable, unavailable

    summary = hedge_gap.get("summary") if isinstance(hedge_gap.get("summary"), dict) else {}
    main = summary.get("main_hedge_gap") if isinstance(summary.get("main_hedge_gap"), dict) else None
    if not isinstance(main, dict):
        unavailable = {"availability": "unavailable", "reason_en": "main_hedge_gap_unavailable"}
        return unavailable, unavailable

    main_row = _resolve_main_hedge_gap_row(hedge_gap)
    offset = {
        "availability": "available",
        "risk_type": main.get("risk_type"),
        "linked_scenario_id": main.get("linked_scenario_id"),
        "offset_coverage_ratio": main.get("offset_coverage_ratio"),
        "gross_loss_from_assets_hurt": main_row.get("gross_loss_from_assets_hurt") if isinstance(main_row, dict) else None,
        "positive_contribution_from_assets_helped": (
            main_row.get("positive_contribution_from_assets_helped") if isinstance(main_row, dict) else None
        ),
    }
    main_gap = {
        "availability": "available",
        "weakest_protection_area": summary.get("weakest_protection_area"),
        "strongest_protection_area": summary.get("strongest_protection_area"),
        "main_hedge_gap": dict(main),
        "diagnosis_summary_en": summary.get("diagnosis_summary_en"),
    }
    return offset, main_gap


def _collect_data_quality_warnings(
    *,
    historical_rows: list[Any],
    hedge_gap: dict[str, Any],
    trust: dict[str, Any],
    conclusions: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []

    # Prefer explicit, user-facing trust summary lines if present.
    trust_lines = trust.get("user_summary_lines")
    if isinstance(trust_lines, list):
        for line in trust_lines:
            if isinstance(line, str) and line.strip():
                warnings.append(line.strip())

    # Block 3.3 warnings.
    if isinstance(hedge_gap, dict) and hedge_gap.get("version") == "hedge_gap_analysis_v1":
        summary = hedge_gap.get("summary") if isinstance(hedge_gap.get("summary"), dict) else {}
        hg_warn = summary.get("data_quality_warnings")
        if isinstance(hg_warn, list):
            for w in hg_warn:
                if isinstance(w, str) and w.strip():
                    warnings.append(w.strip())

    # Block 3.2 conclusions warnings (historical methodology boundary + per-episode flags).
    conc_warn = conclusions.get("data_quality_warnings")
    if isinstance(conc_warn, list):
        for w in conc_warn:
            if isinstance(w, str) and w.strip():
                warnings.append(w.strip())

    # If historical episodes exist, but some are unavailable, add a compact warning.
    if historical_rows:
        unavailable_count = 0
        for row in historical_rows:
            if not isinstance(row, dict):
                continue
            avail = row.get("availability")
            if avail in {"unavailable", "insufficient_data"}:
                unavailable_count += 1
        if unavailable_count:
            warnings.append(f"historical_episodes_with_limited_data={unavailable_count}")

    # De-duplicate while preserving order.
    out: list[str] = []
    seen: set[str] = set()
    for w in warnings:
        if w in seen:
            continue
        seen.add(w)
        out.append(w)
    return out


def _format_diagnosis_summary_en(
    *,
    worst_synthetic: dict[str, Any],
    worst_historical: dict[str, Any],
    main_hedge_gap: dict[str, Any],
    warnings: list[str],
) -> str | None:
    if worst_synthetic.get("availability") != "available" and worst_historical.get("availability") != "available":
        return None

    parts: list[str] = []
    if worst_synthetic.get("availability") == "available":
        sid = worst_synthetic.get("scenario_id")
        loss = worst_synthetic.get("portfolio_loss_pct")
        if sid is not None and isinstance(loss, (int, float)):
            parts.append(f"Worst synthetic scenario is {sid} with portfolio loss {float(loss) * 100:.1f}%.")
    if worst_historical.get("availability") == "available":
        ep = worst_historical.get("episode")
        dd = worst_historical.get("drawdown_pct")
        if ep is not None and isinstance(dd, (int, float)):
            parts.append(f"Worst historical episode is {ep} with max drawdown {float(dd) * 100:.1f}%.")

    if main_hedge_gap.get("availability") == "available":
        mhg = main_hedge_gap.get("main_hedge_gap")
        if isinstance(mhg, dict):
            risk_type = mhg.get("risk_type")
            ratio = mhg.get("offset_coverage_ratio")
            if risk_type and isinstance(ratio, (int, float)):
                parts.append(
                    f"Main hedge gap is {risk_type}: helped assets offset about {float(ratio) * 100:.1f}% of gross losses in the mapped stress."
                )

    if warnings:
        parts.append("Data quality warnings are present; interpret historical episodes and attributions with caution where flagged.")

    return " ".join(parts) if parts else None

