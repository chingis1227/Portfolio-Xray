"""Tests for US universe ingestion pipeline."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.universe_ingestion import (
    classify_etf,
    clean_raw_universe,
    parse_nasdaqlisted_text,
    parse_otherlisted_text,
    parse_sec_company_tickers_json,
    run_ingestion_pipeline,
    _merge_raw_rows,
    build_draft_etf_row,
    build_draft_stock_row,
)

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "tests" / "fixtures" / "universe_ingestion"


def test_parse_nasdaqlisted_sample() -> None:
    text = (FIX / "nasdaqlisted.txt").read_text(encoding="utf-8")
    rows = parse_nasdaqlisted_text(text)
    tickers = {r["ticker"] for r in rows}
    assert "AAPL" in tickers
    assert "VOO" in tickers
    voo = next(r for r in rows if r["ticker"] == "VOO")
    assert voo["etf_flag"] is True
    assert voo["test_issue"] is False


def test_parse_otherlisted_sample() -> None:
    text = (FIX / "otherlisted.txt").read_text(encoding="utf-8")
    rows = parse_otherlisted_text(text)
    assert any(r["ticker"] == "MSFT" for r in rows)
    spy = next(r for r in rows if r["ticker"] == "SPY")
    assert spy["etf_flag"] is True


def test_parse_sec_company_tickers_sample() -> None:
    text = (FIX / "company_tickers_exchange.json").read_text(encoding="utf-8")
    rows = parse_sec_company_tickers_json(text)
    assert len(rows) == 3
    assert rows[0]["ticker"] == "AAPL"
    assert rows[0]["exchange"] == "Nasdaq"


@pytest.mark.parametrize(
    "name,expected_block",
    [
        ("Vanguard S&P 500 ETF", "EQ"),
        ("iShares iBoxx $ High Yield Corporate Bond ETF", "CR"),
        ("iShares TIPS Bond ETF", "TI"),
        ("iShares 7-10 Year Treasury Bond ETF", "ND"),
        ("SPDR Gold Shares", "CO"),
        ("SPDR Bloomberg 1-3 Month T-Bill ETF", "CA"),
    ],
)
def test_etf_stress_block_mapping(name: str, expected_block: str) -> None:
    clf = classify_etf(name, etf_flag=True)
    assert clf.stress_block == expected_block


def test_complex_etf_flagged_needs_review() -> None:
    clf = classify_etf("ProShares UltraPro QQQ", etf_flag=True)
    assert clf.needs_review is True
    assert clf.classification_confidence == "low"
    assert "leveraged" in clf.hybrid_flags


def test_stock_routed_to_draft_stock_universe() -> None:
    raw = {"ticker": "AAPL", "name": "Apple Inc.", "sources": ["nasdaqlisted"], "etf_flag": False}
    row = build_draft_stock_row(raw)
    assert row["ticker"] == "AAPL"
    assert row["asset_class"] == "equity"
    assert row["main_risk_factor"] == "equity"
    assert row["region"] == "US"


def test_etf_routed_to_draft_etf_universe() -> None:
    raw = {"ticker": "VOO", "name": "Vanguard S&P 500 ETF", "sources": ["nasdaqlisted"], "etf_flag": True}
    clf = classify_etf(raw["name"], etf_flag=True)
    row = build_draft_etf_row(raw, clf)
    assert row["ticker"] == "VOO"
    assert row["asset_class"] == "equity"
    assert "public_listing_ingestion" in row["data_source"]


def test_cleaning_removes_test_and_warrants() -> None:
    text = (FIX / "nasdaqlisted.txt").read_text(encoding="utf-8")
    merged = _merge_raw_rows(parse_nasdaqlisted_text(text))
    clean = clean_raw_universe(merged)
    removed_tickers = {r["ticker"] for r in clean.removed}
    assert "TEST" in removed_tickers
    assert "WARR" in removed_tickers
    kept_tickers = {r["ticker"] for r in clean.kept}
    assert "AAPL" in kept_tickers
    assert "VOO" in kept_tickers


def test_pipeline_dry_run_does_not_write_outputs(tmp_path: Path) -> None:
    prod_etf = ROOT / "config" / "etf_universe.yml"
    prod_stock = ROOT / "config" / "stock_universe.yml"
    etf_before = prod_etf.read_text(encoding="utf-8")
    stock_before = prod_stock.read_text(encoding="utf-8")

    report = run_ingestion_pipeline(
        nasdaq_listed_source=str(FIX / "nasdaqlisted.txt"),
        other_listed_source=str(FIX / "otherlisted.txt"),
        sec_tickers_source=str(FIX / "company_tickers_exchange.json"),
        output_dir=tmp_path / "out",
        dry_run=True,
    )
    assert report["dry_run"] is True
    assert not (tmp_path / "out" / "draft_etf_universe.yml").exists()
    assert prod_etf.read_text(encoding="utf-8") == etf_before
    assert prod_stock.read_text(encoding="utf-8") == stock_before
    assert report["validation"]["production_files_modified"] is False


def test_pipeline_writes_draft_artifacts(tmp_path: Path) -> None:
    out = tmp_path / "universe_ingestion"
    report = run_ingestion_pipeline(
        nasdaq_listed_source=str(FIX / "nasdaqlisted.txt"),
        other_listed_source=str(FIX / "otherlisted.txt"),
        sec_tickers_source=str(FIX / "company_tickers_exchange.json"),
        output_dir=out,
        dry_run=False,
    )
    assert (out / "raw_us_universe.csv").is_file()
    assert (out / "clean_us_universe.csv").is_file()
    assert (out / "draft_etf_universe.yml").is_file()
    assert (out / "draft_stock_universe.yml").is_file()
    assert (out / "ingestion_report.json").is_file()
    assert report["counts"]["draft_etfs"] >= 1
    assert report["counts"]["draft_stocks"] >= 1


def test_cli_dry_run_exit_zero() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "ingest_us_listed_universe.py"),
            "--nasdaq-listed-url",
            str(FIX / "nasdaqlisted.txt"),
            "--other-listed-url",
            str(FIX / "otherlisted.txt"),
            "--sec-company-tickers-url",
            str(FIX / "company_tickers_exchange.json"),
            "--dry-run",
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
    assert data["validation"]["production_files_modified"] is False
