"""Regression: representative generated outputs stay English and mojibake-free."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.generated_output_qa import (
    MOJIBAKE_SUBSTRINGS,
    PORTFOLIO_XRAY_COMMENTARY_REQUIRED_MARKERS,
    REPRESENTATIVE_REL_DIRS,
    scan_portfolio_first_summary_text,
    scan_portfolio_xray_report_text,
    scan_representative_outputs,
)
from src.text_sanitizer import ascii_safe_text


def test_representative_output_dirs_exist() -> None:
    repo = Path(__file__).resolve().parents[1]
    missing = [rel for rel in REPRESENTATIVE_REL_DIRS if not (repo / rel).is_dir()]
    assert not missing, f"missing representative output dirs: {missing}"


def test_representative_generated_outputs_language_qa() -> None:
    repo = Path(__file__).resolve().parents[1]
    result = scan_representative_outputs(repo)
    assert result.scanned_files > 0, "expected at least one representative text artifact"
    assert result.ok(), "\n".join(result.messages())


def test_portfolio_first_summary_story_qa() -> None:
    text = "\n".join(
        [
            "Decision package summary (non-executing)",
            "Comparison highlights",
            "  Starting portfolio: Starter model: CAGR 6.0%, vol 11.0%, max DD -18.0%, stress Diagnostic pass",
            "  Candidate alternatives by health rank:",
            "    Equal-Weight Portfolio: health 71.0 (rank 1)",
            "Selection",
            "  Versus starting portfolio: Material improvement may warrant review.",
        ]
    )
    result = scan_portfolio_first_summary_text(text)
    assert result.ok(), "\n".join(result.messages())


def test_portfolio_xray_commentary_story_qa() -> None:
    text = "\n".join(
        [
            "Portfolio X-Ray (diagnostic-only)",
            "Diagnostic summary only.",
            "Archetype lens: Balanced (confidence medium); secondary none.",
            "Full seven-section tables and evidence: portfolio_xray.json, report.html, report.txt.",
        ]
    )
    result = scan_portfolio_xray_report_text(
        text,
        rel_path="commentary.txt",
        required_markers=PORTFOLIO_XRAY_COMMENTARY_REQUIRED_MARKERS,
    )
    assert result.ok(), "\n".join(result.messages())


def test_portfolio_first_summary_story_qa_rejects_legacy_markers() -> None:
    text = "\n".join(
        [
            "Decision package summary (non-executing)",
            "Comparison highlights",
            "  Starting portfolio: Starter model: CAGR 6.0%, vol 11.0%, max DD -18.0%, stress Diagnostic pass",
            "  Top candidates by health rank:",
            "    Equal-Weight Portfolio: health 71.0 (rank 1)",
            "  Versus current: old wording",
        ]
    )
    result = scan_portfolio_first_summary_text(text)
    assert not result.ok()
    assert any(f.kind == "story_marker_missing" for f in result.findings)
    assert any(f.kind == "stale_story_marker" for f in result.findings)


def test_mojibake_markers_cover_common_windows_corruption() -> None:
    for marker in ("\u0432\u0402", "\u041e\u201d", "\u00e2\u20ac\u201d", "\u00ce", "\u00d0", "\ufffd"):
        assert marker in MOJIBAKE_SUBSTRINGS


def test_ascii_safe_text_replaces_fragile_symbols_and_mojibake() -> None:
    text = "Monitoring \u2014 What Changed; \u0394w \u2265 1\u00d7; \u041e\u201dw=0.01; \u00e2\u20ac\u201d; \u00ce\u00b2"
    safe = ascii_safe_text(text)
    assert "Monitoring - What Changed" in safe
    assert "delta w=0.01" in safe
    assert ">=" in safe
    assert "x" in safe
    assert "\u00e2\u20ac\u201d" not in safe
    assert "\u00ce" not in safe
