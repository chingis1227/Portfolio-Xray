from __future__ import annotations

import json
from pathlib import Path

from src.decision_package_reporting import (
    REPORT_TXT_MARKER,
    SCHEMA_VERSION,
    build_decision_package_report,
    build_decision_package_report_md,
    write_decision_package_reporting_outputs,
)
from src.selection_engine import rationale_text_is_client_safe


def _comparison() -> dict:
    return {
        "schema_version": "candidate_comparison_v1",
        "analysis_end": "2025-12-31",
        "investor_currency": "USD",
        "output_dir_final": "Main portfolio",
        "candidates": [
            {
                "candidate_id": "policy",
                "display_name": "Policy (Optimized)",
                "role": "policy",
                "status": "available",
                "metrics": {
                    "10y": {
                        "cagr": 0.08,
                        "vol_annual": 0.12,
                        "max_drawdown": -0.2,
                    }
                },
                "stress": {"overall": "DIAG_PASS"},
                "mandate": {"portfolio_valid": True},
            },
            {
                "candidate_id": "current",
                "display_name": "Current Portfolio",
                "role": "user_current",
                "status": "available",
                "metrics": {
                    "10y": {
                        "cagr": 0.07,
                        "vol_annual": 0.14,
                        "max_drawdown": -0.24,
                    }
                },
                "stress": {"overall": "DIAG_PASS"},
                "mandate": {"portfolio_valid": True},
            },
        ],
    }


def _portfolio_first_comparison() -> dict:
    comp = _comparison()
    comp["comparison_baseline_candidate_id"] = "analysis_subject"
    comp["candidates"] = [
        {
            "candidate_id": "analysis_subject",
            "display_name": "Starter model",
            "role": "analysis_subject",
            "status": "available",
            "metrics": {
                "10y": {
                    "cagr": 0.06,
                    "vol_annual": 0.11,
                    "max_drawdown": -0.18,
                }
            },
            "stress": {"overall": "DIAG_PASS"},
            "mandate": {"portfolio_valid": True},
        },
        {
            "candidate_id": "equal_weight",
            "display_name": "Equal-Weight Portfolio",
            "role": "benchmark",
            "status": "available",
            "metrics": {
                "10y": {
                    "cagr": 0.065,
                    "vol_annual": 0.10,
                    "max_drawdown": -0.16,
                }
            },
            "stress": {"overall": "DIAG_PASS"},
            "mandate": {"portfolio_valid": True},
        },
    ]
    return comp


def _health_robust() -> tuple[dict, dict]:
    rows = [
        {
            "candidate_id": "policy",
            "total_score": 72,
            "score_status": "scored",
            "health_rank": 1,
            "robustness_rank": 1,
        },
        {
            "candidate_id": "current",
            "total_score": 65,
            "score_status": "scored",
            "health_rank": 2,
            "robustness_rank": 2,
        },
    ]
    health = {
        "schema_version": "portfolio_health_score_v1",
        "candidates": [
            {k: v for k, v in r.items() if k != "robustness_rank"} for r in rows
        ],
    }
    robust = {
        "schema_version": "robustness_scorecard_v1",
        "candidates": [
            {k: v for k, v in r.items() if k != "health_rank"} for r in rows
        ],
    }
    return health, robust


def _portfolio_first_health_robust() -> tuple[dict, dict]:
    rows = [
        {
            "candidate_id": "analysis_subject",
            "total_score": 64,
            "score_status": "scored",
            "health_rank": 2,
            "robustness_rank": 2,
        },
        {
            "candidate_id": "equal_weight",
            "total_score": 71,
            "score_status": "scored",
            "health_rank": 1,
            "robustness_rank": 1,
        },
    ]
    health = {
        "schema_version": "portfolio_health_score_v1",
        "candidates": [
            {k: v for k, v in r.items() if k != "robustness_rank"} for r in rows
        ],
    }
    robust = {
        "schema_version": "robustness_scorecard_v1",
        "candidates": [
            {k: v for k, v in r.items() if k != "health_rank"} for r in rows
        ],
    }
    return health, robust


def _selection() -> dict:
    return {
        "schema_version": "selection_decision_v1",
        "decision_status": "no_material_rebalance",
        "favored_candidate_id": "policy",
        "favored_display_name": "Policy (Optimized)",
        "rationale": {
            "summary": "Policy profile is favored; move from current is below review thresholds."
        },
        "no_trade": {
            "evaluated": True,
            "summary": "Health and robustness deltas are below thresholds.",
        },
        "warnings": [],
    }


def _portfolio_first_selection() -> dict:
    return {
        "schema_version": "selection_decision_v1",
        "baseline_candidate_id": "analysis_subject",
        "baseline_display_name": "Starter model",
        "decision_status": "selected_candidate",
        "favored_candidate_id": "equal_weight",
        "favored_display_name": "Equal-Weight Portfolio",
        "rationale": {
            "summary": "Equal-Weight Portfolio is favored for review versus the diagnosed subject."
        },
        "no_trade": {
            "evaluated": True,
            "baseline_candidate_id": "analysis_subject",
            "summary": "Material improvement versus the starting portfolio may warrant review.",
        },
        "warnings": [],
    }


def _mandate_blocked_selection() -> dict:
    return {
        "schema_version": "selection_decision_v1",
        "baseline_candidate_id": "analysis_subject",
        "baseline_display_name": "Starter model",
        "decision_status": "mandate_risk_reduction",
        "favored_candidate_id": None,
        "favored_display_name": None,
        "rationale": {
            "summary": "Mandate constraints require risk reduction; allocation change is not advised until resolved.",
            "selection_bullets": [
                "Starter model does not meet mandate fit; risk reduction is required before allocation changes."
            ],
            "data_quality_notes": [
                "Starter model does not meet mandate fit; risk reduction is required before allocation changes."
            ],
        },
        "no_trade": None,
        "warnings": ["mandate_risk_reduction"],
    }


def _action() -> dict:
    return {
        "schema_version": "action_plan_v1",
        "action_status": "no_trades_no_material_rebalance",
        "no_trades_reason": "No trades: no material rebalance versus current weights.",
        "turnover_half_sum_pct": 2.5,
        "trades": [],
    }


def _monitoring() -> dict:
    return {
        "schema_version": "monitoring_diff_v1",
        "diff_status": "no_prior_snapshot",
        "summary_plain_en": "First analysis snapshot stored for future comparison.",
    }


def _journal() -> dict:
    return {
        "schema_version": "decision_journal_v1",
        "analysis_end": "2025-12-31",
    }


def test_build_decision_package_report_sections() -> None:
    health, robust = _health_robust()
    doc = build_decision_package_report(
        comparison=_comparison(),
        health=health,
        robustness=robust,
        selection=_selection(),
        action=_action(),
        monitoring_diff=_monitoring(),
        decision_journal=_journal(),
    )
    assert doc["schema_version"] == SCHEMA_VERSION
    assert doc["sections"]["comparison"]["availability"] == "available"
    text = doc["summary_plain_en"]
    assert "Policy (Optimized)" in text
    assert "No material rebalance" in text
    assert "First analysis snapshot" in text
    assert rationale_text_is_client_safe(text)


def test_portfolio_first_summary_names_subject_before_alternatives() -> None:
    health, robust = _portfolio_first_health_robust()
    doc = build_decision_package_report(
        comparison=_portfolio_first_comparison(),
        health=health,
        robustness=robust,
        selection=_portfolio_first_selection(),
        action=_action(),
        monitoring_diff=_monitoring(),
        decision_journal=_journal(),
        workflow_status={
            "schema_version": "current_vs_policy_status_v1",
            "workflow_profile": "portfolio_first_review",
            "user_message_en": "Portfolio-first review uses analysis_subject as the baseline.",
        },
    )
    text = doc["summary_plain_en"]
    assert "Starting portfolio: Starter model" in text
    assert "Candidate alternatives by health rank" in text
    assert "Equal-Weight Portfolio" in text
    assert "Versus starting portfolio" in text
    assert "Current vs policy workflow" not in text
    assert rationale_text_is_client_safe(text)


def test_mandate_block_selection_explains_missing_favored_profile() -> None:
    health, robust = _portfolio_first_health_robust()
    doc = build_decision_package_report(
        comparison=_portfolio_first_comparison(),
        health=health,
        robustness=robust,
        selection=_mandate_blocked_selection(),
        action={"schema_version": "action_plan_v1", "action_status": "no_trades_other"},
        monitoring_diff=_monitoring(),
        decision_journal=_journal(),
    )
    text = doc["summary_plain_en"]
    assert "Favored profile: —" in text
    assert "mandate risk-reduction gates blocked selection" in text
    assert "Mandate note: Starter model does not meet mandate fit" in text
    assert "Warning: mandate_risk_reduction" not in text
    assert rationale_text_is_client_safe(text)


def _truth_test_optimizer(
    cid: str,
    *,
    status: str = "degraded",
    fair_ready: bool = False,
) -> dict:
    return {
        "candidate_id": cid,
        "display_name": cid.replace("_", " ").title(),
        "role": "optimizer_candidate",
        "status": status,
        "metrics": {"10y": {"cagr": 0.08, "vol_annual": 0.11, "max_drawdown": -0.2}},
        "stress": {"overall": "DIAG_PASS"},
        "mandate": {"portfolio_valid": True},
        "construction_disclosure": {
            "optimization_readiness": {"fair_comparison_ready": fair_ready},
        },
    }


def test_partial_menu_and_degraded_optimizer_prominent_in_summary() -> None:
    from src.selection_engine import build_selection_decision

    comparison = {
        "analysis_end": "2026-04-30",
        "investor_currency": "USD",
        "comparison_baseline_candidate_id": "analysis_subject",
        "candidate_menu": {
            "review_mode": "core",
            "is_partial_menu": True,
            "partial_menu_reason": "reduced_vs_product_menu",
            "intended_menu_profile_id": "core_v1",
            "product_menu_profile_id": "default_v1",
            "factory_execution_summary": {
                "build_steps_executed": 4,
                "in_process_build_steps": 0,
                "builder_invoked": 4,
                "reused_existing": 1,
                "reused_existing_snapshot": 1,
                "resumed_from_manifest": 1,
            },
        },
        "candidates": [
            {
                "candidate_id": "analysis_subject",
                "display_name": "Starter",
                "role": "analysis_subject",
                "status": "available",
                "metrics": {"10y": {"cagr": 0.06, "vol_annual": 0.12, "max_drawdown": -0.2}},
                "stress": {"overall": "DIAG_PASS"},
                "mandate": {"portfolio_valid": True},
            },
            _truth_test_optimizer("degraded_opt"),
            _truth_test_optimizer("fair_opt", status="available", fair_ready=True),
        ],
    }
    health = {
        "schema_version": "portfolio_health_score_v1",
        "candidates": [
            {"candidate_id": "degraded_opt", "total_score": 90, "score_status": "scored", "health_rank": 1},
            {"candidate_id": "fair_opt", "total_score": 75, "score_status": "scored", "health_rank": 2},
            {"candidate_id": "analysis_subject", "total_score": 60, "score_status": "scored", "health_rank": 3},
        ],
    }
    robust = {
        "schema_version": "robustness_scorecard_v1",
        "candidates": [
            {"candidate_id": "degraded_opt", "total_score": 88, "score_status": "scored", "robustness_rank": 1},
            {"candidate_id": "fair_opt", "total_score": 72, "score_status": "scored", "robustness_rank": 2},
            {"candidate_id": "analysis_subject", "total_score": 58, "score_status": "scored", "robustness_rank": 3},
        ],
    }
    selection = build_selection_decision(comparison, health=health, robustness=robust)
    doc = build_decision_package_report(
        comparison=comparison,
        health=health,
        robustness=robust,
        selection=selection,
        action=_action(),
        monitoring_diff=_monitoring(),
        decision_journal=_journal(),
    )
    text = doc["summary_plain_en"]
    assert "Review scope (read first)" in text
    assert "optimizer shootout" in text.lower()
    assert (
        "Factory evidence: 4 build step(s) executed (4 builder(s) invoked, "
        "0 in-process), 1 existing artifact step(s) reused"
    ) in text
    assert doc["package_truthfulness"]["is_partial_menu"] is True
    assert doc["package_truthfulness"]["degraded_optimizer_count"] == 1


def test_missing_artifacts_marked_not_available() -> None:
    doc = build_decision_package_report(
        comparison=None,
        health=None,
        robustness=None,
        selection=None,
        action=None,
        monitoring_diff=None,
        decision_journal=None,
    )
    assert all(
        s["availability"] == "not_available" for s in doc["sections"].values()
    )
    assert "Not available" in doc["summary_plain_en"]


def test_write_outputs_and_append_report_txt(tmp_path: Path) -> None:
    from src.config_schema import validate_config

    out = tmp_path / "Main portfolio"
    out.mkdir()
    (out / "report.txt").write_text("Existing report body\n", encoding="utf-8")

    health, robust = _health_robust()
    comp = _comparison()
    for name, data in (
        ("candidate_comparison.json", comp),
        ("portfolio_health_score.json", health),
        ("robustness_scorecard.json", robust),
        ("selection_decision.json", _selection()),
        ("action_plan.json", _action()),
        ("monitoring_diff.json", _monitoring()),
        ("decision_journal.json", _journal()),
    ):
        (out / name).write_text(json.dumps(data), encoding="utf-8")

    cfg = validate_config(
        {
            "output_dir_final": out.name,
            "investor_currency": "USD",
            "tickers": ["VOO"],
        }
    )
    paths = write_decision_package_reporting_outputs(
        cfg, project_root=tmp_path, comparison=comp
    )
    assert paths["decision_package_summary_txt"].is_file()
    assert paths["decision_package_summary_json"].is_file()
    report = (out / "report.txt").read_text(encoding="utf-8")
    assert REPORT_TXT_MARKER in report
    assert "Decision package summary" in report

    md = build_decision_package_report_md(
        paths["decision_package_summary_txt"].read_text(encoding="utf-8"),
        analysis_end="2025-12-31",
    )
    assert 'title: "Decision Package Summary"' in md
    assert "2025-12-31" in md
    assert "# Decision Package Summary" not in md


def test_decision_package_pdf_md_avoids_broken_latex_section_title() -> None:
    from src.pdf_reports import build_decision_package_pdf_md

    summary = (
        "Decision package summary (non-executing)\n"
        "========================================================================\n"
        "Analysis end: 2026-05-15   Investor currency: USD\n\n"
        "Comparison highlights\n"
        "----------------------------------------\n"
        "  Starting portfolio: CAGR 10.4%, vol 9.6%, max DD -20.2%.\n"
    )
    md = build_decision_package_pdf_md(summary, analysis_end="2026-05-15")
    assert md.startswith("---\n")
    assert 'title: "Decision Package Summary"' in md
    assert "Decision package summary as of 2026-05-15" in md
    assert "# Decision Package Summary" not in md
    assert "analysis end 2026-05-15" not in md


def test_decision_package_pdf_builds_when_pandoc_available(tmp_path: Path) -> None:
    from src.pdf_reports import _find_pandoc, _find_xelatex, build_decision_package_pdf_md, write_md_and_pdf

    import pytest

    try:
        has_pdf_toolchain = bool(_find_pandoc() and _find_xelatex())
    except PermissionError as exc:
        pytest.skip(f"pdf toolchain probe blocked by OS permissions: {exc}")
    if not has_pdf_toolchain:
        pytest.skip("pandoc/xelatex not available")

    summary = (
        "Analysis end: 2026-05-15   Investor currency: USD\n\n"
        "Selection\n"
        "----------------------------------------\n"
        "  Status: Mandate constraints require risk reduction.\n"
        "  Starting portfolio: CAGR 10.4%, vol 9.6%.\n"
    )
    md = build_decision_package_pdf_md(summary, analysis_end="2026-05-15")
    ok = write_md_and_pdf(
        md,
        md_out=tmp_path / "decision_package.md",
        pdf_out=tmp_path / "decision_package.pdf",
    )
    assert ok
    assert (tmp_path / "decision_package.pdf").is_file()


def test_favored_partial_scores_are_displayed_not_reported_unscored() -> None:
    comp = _comparison()
    comp["candidates"].append(
        {
            "candidate_id": "risk_parity",
            "display_name": "Risk Parity",
            "role": "optimizer",
            "status": "available",
            "metrics": {"10y": {"cagr": 0.07, "vol_annual": 0.10, "max_drawdown": -0.16}},
            "stress": {"overall": "DIAG_PASS"},
            "mandate": {"portfolio_valid": True},
        }
    )
    selection = {
        **_selection(),
        "favored_candidate_id": "risk_parity",
        "favored_display_name": "Risk Parity",
    }
    health = {
        "schema_version": "portfolio_health_score_v1",
        "candidates": [
            {
                "candidate_id": "risk_parity",
                "score_status": "partial",
                "total_score": 66,
                "health_rank": 1,
            }
        ],
    }
    robust = {
        "schema_version": "robustness_scorecard_v1",
        "candidates": [
            {
                "candidate_id": "risk_parity",
                "score_status": "partial",
                "total_score": 63,
                "robustness_rank": 1,
            }
        ],
    }
    doc = build_decision_package_report(
        comparison=comp,
        health=health,
        robustness=robust,
        selection=selection,
        action=None,
        monitoring_diff=None,
        decision_journal=None,
    )
    text = doc["summary_plain_en"]
    assert "not scored" not in text.lower()
    assert "Favored profile: total 63.0, rank 1 (partial score)" in text
    assert "Favored profile: total 66.0, rank 1 (partial score)" in text


def test_missing_favored_score_reports_candidate_id_and_artifact() -> None:
    comp = _comparison()
    selection = {
        **_selection(),
        "favored_candidate_id": "risk_parity",
        "favored_display_name": "Risk Parity",
    }
    doc = build_decision_package_report(
        comparison=comp,
        health={"schema_version": "portfolio_health_score_v1", "candidates": []},
        robustness={"schema_version": "robustness_scorecard_v1", "candidates": []},
        selection=selection,
        action=None,
        monitoring_diff=None,
        decision_journal=None,
    )
    text = doc["summary_plain_en"]
    assert "Favored profile risk_parity missing from robustness_scorecard.json." in text
    assert "Favored profile risk_parity missing from portfolio_health_score.json." in text
