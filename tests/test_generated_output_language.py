"""Regression: representative generated outputs stay English and mojibake-free."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.generated_output_qa import (
    REPRESENTATIVE_REL_DIRS,
    scan_portfolio_first_summary_text,
    scan_representative_outputs,
)


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
