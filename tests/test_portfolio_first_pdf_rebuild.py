"""Tests for portfolio-first PDF rebuild scope (Session 10 / RM-910)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.pdf_reports import rebuild_portfolio_first_pdfs


def test_rebuild_portfolio_first_pdfs_scope(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Portfolio-first rebuild targets decision package and subject sidecar only."""
    out_final = tmp_path / "Main portfolio"
    subject = out_final / "analysis_subject"
    subject.mkdir(parents=True)
    (out_final / "decision_package_summary.txt").write_text(
        "Decision Package Summary\n\nStarting portfolio: analysis_subject\n",
        encoding="utf-8",
    )
    (subject / "commentary.txt").write_text(
        "Executive Summary\n\nSubject diagnostics.\n",
        encoding="utf-8",
    )
    (subject / "stress_commentary.txt").write_text(
        "Executive Summary\n\nSubject stress view.\n",
        encoding="utf-8",
    )
    (subject / "weights.json").write_text(
        json.dumps({"VOO": 0.6, "BND": 0.4}),
        encoding="utf-8",
    )

    written: list[str] = []

    def _fake_write_md_and_pdf(
        _md: str, *, md_out: Path, pdf_out: Path, logger=None
    ) -> bool:
        written.append(pdf_out.name)
        md_out.parent.mkdir(parents=True, exist_ok=True)
        md_out.write_text(_md, encoding="utf-8")
        pdf_out.parent.mkdir(parents=True, exist_ok=True)
        pdf_out.write_bytes(b"%PDF-1.4\n")
        return True

    class _Cfg:
        output_dir_final = str(out_final)

    monkeypatch.setattr("src.pdf_reports.load_validated_config", lambda: _Cfg())
    monkeypatch.setattr("src.pdf_reports._ROOT", tmp_path)
    monkeypatch.setattr("src.pdf_reports._PDF_OUT", tmp_path / "pdf files")
    monkeypatch.setattr("src.pdf_reports._PDF_MD_SOURCES", tmp_path / "pdf_md_sources")
    monkeypatch.setattr("src.pdf_reports.write_md_and_pdf", _fake_write_md_and_pdf)
    monkeypatch.setattr("src.pdf_reports._copy_pdf_to_archive", lambda *_a, **_k: None)

    results = rebuild_portfolio_first_pdfs()

    assert set(written) == {
        "Main portfolio_decision_package.pdf",
        "analysis_subject_commentary.pdf",
        "analysis_subject_stress_commentary.pdf",
        "analysis_subject_weights.pdf",
    }
    assert results["Main portfolio_decision_package.pdf"] is True
    assert "equal-weight_portfolio_commentary.pdf" not in results
    assert "Main portfolio_commentary.pdf" not in results
