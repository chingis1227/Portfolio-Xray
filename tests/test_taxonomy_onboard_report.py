"""Tests for taxonomy onboarding report and stress block derivation."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.taxonomy_stress_blocks import (
    build_onboard_report,
    derive_stress_block_for_ticker,
)

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize(
    "ticker,expected_block",
    [
        ("VOO", "EQ"),
        ("HYG", "CR"),
        ("TIP", "TI"),
        ("IEF", "ND"),
        ("GLD", "CO"),
        ("BIL", "CA"),
    ],
)
def test_known_etf_stress_blocks(ticker: str, expected_block: str) -> None:
    out = derive_stress_block_for_ticker(ticker, cash_proxy_ticker="BIL")
    assert out["stress_block"] == expected_block
    assert out["universe_source"] == "etf_universe"
    assert out["silent_default_eq"] is False


def test_unknown_ticker_silent_default_eq() -> None:
    out = derive_stress_block_for_ticker("ZZZNOTAREALTICKER999", cash_proxy_ticker="BIL")
    assert out["stress_block"] == "EQ"
    assert out["stress_block_source"] == "unknown"
    assert out["universe_source"] == "missing"
    assert out["silent_default_eq"] is True
    assert out["classification_confidence"] == "low"
    assert out["needs_review"] is True
    assert out["rc_ready"] is False


def test_build_onboard_report_schema() -> None:
    report = build_onboard_report(["VOO", "ZZZNOTAREALTICKER999"], cash_proxy_ticker="BIL")
    assert report["version"] == "taxonomy_onboard_report_v1"
    assert len(report["per_ticker"]) == 2
    assert "validators" in report
    assert report["summary"]["silent_default_eq_count"] == 1
    assert report["validators"]["etf_universe"]["status"] in ("PASS", "PASS_WITH_WARNINGS", "FAIL")


def test_cli_json_exit_code() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "taxonomy_onboard_report.py"),
            "--tickers",
            "ZZZNOTAREALTICKER999",
            "--format",
            "json",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 1
    data = json.loads(proc.stdout)
    assert data["per_ticker"][0]["silent_default_eq"] is True


def test_cli_known_ticker_exit_zero() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "taxonomy_onboard_report.py"),
            "--tickers",
            "VOO",
            "--format",
            "json",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    assert data["per_ticker"][0]["rc_ready"] is True
