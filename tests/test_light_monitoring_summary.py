from __future__ import annotations

import json
import re
from pathlib import Path

from src.light_monitoring_summary import (
    WHAT_CHANGED_SUMMARY_VERSION,
    build_what_changed_summary,
    write_what_changed_summary_outputs,
)

FORBIDDEN_PUBLIC_MESSAGE_RE = (
    r"\.json\b|field_path|source_refs|frontend_review_|Traceback|"
    r"\bbuy\b|\bsell\b|\btrade now\b|\bmust rebalance\b|\bbest portfolio\b|"
    r"\bsuitability approved\b|\bexecute trades\b"
)


def _line_messages(doc: dict) -> str:
    return "\n".join(str(line.get("message", "")) for line in doc.get("what_changed_lines", []))


def test_what_changed_summary_handles_no_prior_snapshot() -> None:
    doc = build_what_changed_summary(
        monitoring_diff={
            "schema_version": "monitoring_diff_v1",
            "diff_status": "no_prior_snapshot",
            "primary_profile_id": "analysis_subject",
            "current_analysis_end": "2026-05-25",
            "prior_analysis_end": None,
            "profile_changes": {},
            "decision_changes": {"decision_status_changed": False},
            "action_changes": {"action_status_changed": False},
            "rebalance_trigger": False,
            "summary_plain_en": "First snapshot.",
            "warnings": [],
        },
        decision_verdict={"verdict_id": "no_material_rebalance_recommended"},
    )

    assert doc["schema_version"] == WHAT_CHANGED_SUMMARY_VERSION
    assert doc["summary_status"] == "available"
    assert "baseline" in {line["category"] for line in doc["what_changed_lines"]}
    assert doc["retest_triggers"] == []
    assert doc["guardrails"]["does_not_change_monitoring_schema"] is True
    assert not re.search(FORBIDDEN_PUBLIC_MESSAGE_RE, _line_messages(doc), re.I)


def test_what_changed_summary_no_prior_ignores_change_flags() -> None:
    doc = build_what_changed_summary(
        monitoring_diff={
            "schema_version": "monitoring_diff_v1",
            "diff_status": "no_prior_snapshot",
            "primary_profile_id": "analysis_subject",
            "current_analysis_end": "2026-05-25",
            "prior_analysis_end": None,
            "profile_changes": {
                "analysis_subject": {
                    "available": True,
                    "top_risk_contributor_changed": True,
                    "worst_scenario_changed": True,
                }
            },
            "decision_changes": {"decision_status_changed": True},
            "action_changes": {"action_status_changed": True},
            "rebalance_trigger": True,
            "warnings": [],
        },
        decision_verdict={"verdict_id": "rebalance_to_selected_candidate"},
    )

    assert doc["summary_status"] == "available"
    assert [line["category"] for line in doc["what_changed_lines"]] == ["baseline"]
    assert doc["retest_triggers"] == []
    assert "changed since the prior snapshot" not in _line_messages(doc)
    assert "reviewed" not in _line_messages(doc).lower()


def test_what_changed_summary_flags_risk_and_stress_changes() -> None:
    doc = build_what_changed_summary(
        monitoring_diff={
            "diff_status": "diff_available",
            "primary_profile_id": "analysis_subject",
            "current_analysis_end": "2026-05-25",
            "prior_analysis_end": "2026-04-30",
            "profile_changes": {
                "analysis_subject": {
                    "available": True,
                    "top_risk_contributor_changed": True,
                    "worst_scenario_changed": True,
                    "macro_regime_changed": False,
                    "mandate_status_changed": False,
                }
            },
            "decision_changes": {"decision_status_changed": False},
            "action_changes": {"action_status_changed": False},
            "rebalance_trigger": False,
            "warnings": [],
        },
        problem_classification={"problems": [{"problem_id": "high_volatility"}]},
        current_vs_candidate={"view_mode": "one_candidate"},
    )

    categories = {line["category"] for line in doc["what_changed_lines"]}
    assert "risk_contributor" in categories
    assert "stress_behavior" in categories
    assert "top_risk_contributor_changed" in doc["retest_triggers"]
    assert "worst_scenario_changed" in doc["retest_triggers"]
    assert doc["problem_ids"] == ["high_volatility"]
    assert doc["current_vs_candidate_mode"] == "one_candidate"


def test_what_changed_summary_flags_decision_and_warning() -> None:
    doc = build_what_changed_summary(
        monitoring_diff={
            "diff_status": "diff_available",
            "primary_profile_id": "current",
            "profile_changes": {"current": {"available": True}},
            "decision_changes": {"decision_status_changed": True},
            "action_changes": {"action_status_changed": True},
            "rebalance_trigger": True,
            "warnings": ["primary_profile_diff_degraded"],
        },
        decision_verdict={"verdict_id": "rebalance_to_selected_candidate"},
    )

    categories = {line["category"] for line in doc["what_changed_lines"]}
    assert "decision" in categories
    assert "action" in categories
    assert "review_trigger" in categories
    assert "warning" in categories
    assert "monitoring_warning" in doc["retest_triggers"]
    assert "monitoring_diff:primary_profile_diff_degraded" in doc["warnings"]
    assert doc["decision_verdict_id"] == "rebalance_to_selected_candidate"
    assert not re.search(FORBIDDEN_PUBLIC_MESSAGE_RE, _line_messages(doc), re.I)


def test_what_changed_summary_handles_missing_monitoring() -> None:
    doc = build_what_changed_summary(
        monitoring_diff=None,
        decision_verdict={"verdict_id": "no_material_rebalance_recommended"},
        problem_classification={"problems": [{"problem_id": "high_concentration"}]},
        current_vs_candidate={"view_mode": "one_candidate"},
    )

    assert doc["summary_status"] == "missing_monitoring"
    assert "missing_required_source:monitoring_diff.json" in doc["warnings"]
    assert doc["source_artifacts"]["monitoring_diff"] is None
    assert doc["decision_verdict_id"] == "no_material_rebalance_recommended"
    assert doc["problem_ids"] == ["high_concentration"]
    assert doc["current_vs_candidate_mode"] == "one_candidate"
    assert doc["what_changed_lines"] == []


def test_write_what_changed_summary_outputs(tmp_path: Path) -> None:
    paths = write_what_changed_summary_outputs(
        output_dir=tmp_path,
        monitoring_diff={
            "diff_status": "no_prior_snapshot",
            "primary_profile_id": "analysis_subject",
            "rebalance_trigger": False,
        },
    )

    path = paths["what_changed_summary_json"]
    assert path == tmp_path / "what_changed_summary.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["schema_version"] == WHAT_CHANGED_SUMMARY_VERSION
    assert not (tmp_path / "monitoring").exists()


def test_what_changed_summary_public_lines_do_not_expose_artifact_or_advice_language() -> None:
    doc = build_what_changed_summary(
        monitoring_diff={
            "diff_status": "diff_degraded",
            "primary_profile_id": "analysis_subject",
            "current_analysis_end": "2026-05-25",
            "prior_analysis_end": "2026-04-30",
            "profile_changes": {"analysis_subject": {"available": False}},
            "decision_changes": {"decision_status_changed": True},
            "action_changes": {"action_status_changed": True},
            "rebalance_trigger": True,
            "warnings": ["source_refs field_path frontend_review_bad Traceback buy sell must rebalance"],
        },
        decision_verdict={"verdict_id": "rebalance_to_selected_candidate"},
    )

    messages = _line_messages(doc)
    assert "evidence_gap" in {line["category"] for line in doc["what_changed_lines"]}
    assert "review_trigger" in {line["category"] for line in doc["what_changed_lines"]}
    assert not re.search(FORBIDDEN_PUBLIC_MESSAGE_RE, messages, re.I)
    assert doc["guardrails"] == {
        "does_not_change_monitoring_schema": True,
        "does_not_write_monitoring_history": True,
        "does_not_calculate_metrics": True,
        "does_not_execute_trades": True,
    }
