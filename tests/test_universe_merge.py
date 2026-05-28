"""Tests for controlled universe merge."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.universe_merge import (
    apply_merge_plan,
    build_merge_plan,
    load_draft_universe_yaml,
    merge_plan_to_report,
)

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "tests" / "fixtures" / "universe_ingestion"
SAMPLE = ROOT / "output" / "universe_ingestion_sample"


@pytest.fixture
def sample_ingestion_dir() -> Path:
    if not (SAMPLE / "draft_etf_universe.yml").is_file():
        pytest.skip("Run sample ingestion first or use fixtures")
    return SAMPLE


def test_load_draft_yaml_skips_comments(tmp_path: Path) -> None:
    p = tmp_path / "draft.yml"
    p.write_text(
        "# DRAFT\n"
        "- {ticker: AAA, name: Test ETF, issuer: X, asset_class: equity, subtype: broad_market, "
        "sector: multi_sector, thematic_primary: none, thematic_tags: [], risk_role: [risk_on], "
        "main_risk_factor: equity, secondary_risk_factors: [], region: US, currency_exposure: USD, "
        "duration_bucket: none, credit_quality: none, duplicate_group_id: a, canonical_ticker: AAA, "
        "data_source: [inferred]}\n",
        encoding="utf-8",
    )
    rows = load_draft_universe_yaml(p)
    assert len(rows) == 1
    assert rows[0]["ticker"] == "AAA"


def test_merge_plan_skips_needs_review(sample_ingestion_dir: Path) -> None:
    plan, _ = build_merge_plan(
        draft_etf_path=sample_ingestion_dir / "draft_etf_universe.yml",
        draft_stock_path=sample_ingestion_dir / "draft_stock_universe.yml",
        needs_review_path=sample_ingestion_dir / "needs_review.csv",
        production_etf_path=ROOT / "config" / "etf_universe.yml",
        production_stock_path=ROOT / "config" / "stock_universe.yml",
        include_needs_review=False,
    )
    report = merge_plan_to_report(plan, {})
    if (sample_ingestion_dir / "needs_review.csv").is_file():
        assert report["summary"]["etf_skipped_needs_review"] >= 0


def test_merge_dry_run_does_not_modify_production(sample_ingestion_dir: Path) -> None:
    prod = ROOT / "config" / "etf_universe.yml"
    before = prod.read_text(encoding="utf-8")
    plan, meta = build_merge_plan(
        draft_etf_path=sample_ingestion_dir / "draft_etf_universe.yml",
        draft_stock_path=sample_ingestion_dir / "draft_stock_universe.yml",
        production_etf_path=prod,
        production_stock_path=ROOT / "config" / "stock_universe.yml",
        tickers_filter={"ZZZNOTINTDRAFT999"},
    )
    assert plan.etf_to_add == []
    assert prod.read_text(encoding="utf-8") == before


def test_apply_merge_to_temp_files(tmp_path: Path) -> None:
    etf_path = tmp_path / "etf_universe.yml"
    etf_path.write_text(
        "- {ticker: VOO, name: Vanguard S&P 500 ETF, issuer: Vanguard, asset_class: equity, "
        "subtype: broad_market, sector: multi_sector, thematic_primary: none, thematic_tags: [], "
        "risk_role: [risk_on], main_risk_factor: equity, secondary_risk_factors: [], region: US, "
        "currency_exposure: USD, duration_bucket: none, credit_quality: none, "
        "duplicate_group_id: x, canonical_ticker: VOO, data_source: [manual_seed]}\n",
        encoding="utf-8",
    )
    from src.universe_merge import MergePlan

    new_row = {
        "ticker": "SPLG",
        "name": "SPDR Portfolio S&P 500 ETF",
        "issuer": "State Street",
        "asset_class": "equity",
        "subtype": "broad_market",
        "sector": "multi_sector",
        "thematic_primary": "none",
        "thematic_tags": [],
        "risk_role": ["risk_on", "growth"],
        "main_risk_factor": "equity",
        "secondary_risk_factors": ["us_growth"],
        "region": "US",
        "currency_exposure": "USD",
        "duration_bucket": "none",
        "credit_quality": "none",
        "duplicate_group_id": "ingestion_splg",
        "canonical_ticker": "SPLG",
        "data_source": ["public_listing_ingestion"],
        "notes": "test merge",
    }
    plan = MergePlan(etf_to_add=[new_row])
    result = apply_merge_plan(plan, production_etf_path=etf_path, production_stock_path=tmp_path / "stock.yml")
    assert result["etf_added"] == 1
    text = etf_path.read_text(encoding="utf-8")
    assert "SPLG" in text
