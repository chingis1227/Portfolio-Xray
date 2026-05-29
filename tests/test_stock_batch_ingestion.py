"""Tests for Stock Batch 1 index-based ingestion pipeline."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.stock_batch_ingestion import (
    IndexMember,
    merge_index_members,
    normalize_equity_ticker,
    primary_index_tag,
    run_stock_batch1_pipeline,
    select_batch1_candidates,
)
from src.stock_universe import validate_stock_universe
from src.universe_merge import build_merge_plan

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "tests" / "fixtures" / "stock_batch1"


def test_normalize_class_share_ticker() -> None:
    assert normalize_equity_ticker("BRK-B") == "BRK.B"
    assert normalize_equity_ticker("brk.b") == "BRK.B"


def test_primary_index_priority() -> None:
    assert primary_index_tag({"SP500", "R1000"}) == ["SP500"]
    assert primary_index_tag({"R1000", "R3000"}) == ["R1000"]
    assert primary_index_tag({"R3000"}) == ["R3000"]


def test_select_batch1_priority_and_cap() -> None:
    members = merge_index_members(
        [
            IndexMember("AAA", "A", index_tags={"SP500"}),
            IndexMember("BBB", "B", index_tags={"R1000"}),
            IndexMember("CCC", "C", index_tags={"R3000"}),
            IndexMember("DDD", "D", index_tags={"R1000", "R3000"}),
        ]
    )
    selected = select_batch1_candidates(members, max_tickers=3, include_r2000_liquid=False)
    tickers = [m.ticker for m in selected]
    assert tickers == ["AAA", "BBB", "DDD"]
    assert "CCC" not in tickers


def test_offline_pipeline_writes_artifacts(tmp_path: Path) -> None:
    out = tmp_path / "batch1"
    result = run_stock_batch1_pipeline(
        output_dir=out,
        production_stock_path=ROOT / "config" / "stock_universe.yml",
        offline=True,
        enrich_yahoo=False,
        max_tickers=50,
    )
    assert (out / "draft_stock_universe_batch1.yml").is_file()
    assert (out / "stock_batch1_review_report.json").is_file()
    assert (out / "needs_review_stocks.csv").is_file()
    report = result.review_report
    assert report["summary"]["total_candidates"] <= 50
    assert report["summary"]["already_in_production"] > 0


def test_r1000_csv_adds_new_accepted_candidates(tmp_path: Path) -> None:
    out = tmp_path / "batch1"
    result = run_stock_batch1_pipeline(
        output_dir=out,
        production_stock_path=ROOT / "config" / "stock_universe.yml",
        offline=True,
        enrich_yahoo=False,
        max_tickers=600,
        r1000_csv=FIX / "russell_1000_sample.csv",
        r3000_csv=FIX / "russell_3000_sample.csv",
        include_r2000_liquid=True,
    )
    accepted = {r["ticker"] for r in result.accepted}
    assert "NEW1" in accepted
    assert "NEW2" in accepted
    assert "NEW3" in accepted  # R3000-only band; requires --include-r2000-liquid
    for row in result.accepted:
        prod = {k: v for k, v in row.items() if k not in ("notes", "subtype", "stress_block", "data_source")}
        assert validate_stock_universe([prod])["status"] == "PASS"


def test_merge_plan_stock_batch_mode(tmp_path: Path) -> None:
    out = tmp_path / "batch1"
    run_stock_batch1_pipeline(
        output_dir=out,
        production_stock_path=ROOT / "config" / "stock_universe.yml",
        offline=True,
        enrich_yahoo=False,
        max_tickers=600,
        r1000_csv=FIX / "russell_1000_sample.csv",
    )
    report = json.loads((out / "stock_batch1_review_report.json").read_text(encoding="utf-8"))
    tickers = set(report["accepted_tickers"])
    plan, _ = build_merge_plan(
        draft_etf_path=out / "missing_etf.yml",
        draft_stock_path=out / "draft_stock_universe_batch1.yml",
        production_etf_path=ROOT / "config" / "etf_universe.yml",
        production_stock_path=ROOT / "config" / "stock_universe.yml",
        tickers_filter=tickers,
        include_etfs=False,
        include_stocks=True,
        stock_batch_mode=True,
    )
    add_tickers = {_upper(r["ticker"]) for r in plan.stock_to_add}
    assert "NEW1" in add_tickers


def _upper(t: str) -> str:
    return str(t).strip().upper()


def test_rejects_adr_name() -> None:
    from src.stock_batch_ingestion import is_excluded_instrument

    assert is_excluded_instrument("Toyota Motor ADR", "TM") == "adr_excluded"
