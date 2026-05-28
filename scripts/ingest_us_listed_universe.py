#!/usr/bin/env python3
"""Ingest US-listed stocks and ETFs from public sources into draft taxonomy files."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.universe_ingestion import (
    DEFAULT_NASDAQ_LISTED_URL,
    DEFAULT_OTHER_LISTED_URL,
    DEFAULT_SEC_TICKERS_URL,
    run_ingestion_pipeline,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Stage US listing sources into draft ETF/stock universe YAML (never overwrites production)",
    )
    p.add_argument(
        "--nasdaq-listed-url",
        default=DEFAULT_NASDAQ_LISTED_URL,
        help="URL or local path to nasdaqlisted.txt",
    )
    p.add_argument(
        "--other-listed-url",
        default=DEFAULT_OTHER_LISTED_URL,
        help="URL or local path to otherlisted.txt",
    )
    p.add_argument(
        "--sec-company-tickers-url",
        default=DEFAULT_SEC_TICKERS_URL,
        help="URL or local path to company_tickers_exchange.json",
    )
    p.add_argument(
        "--output-dir",
        default="output/universe_ingestion",
        help="Directory for draft CSV/YAML/JSON outputs",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute report only; do not write output files",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of kept/flagged candidates processed (for testing)",
    )
    p.add_argument(
        "--enrich-sectors-yahoo",
        action="store_true",
        help="Enrich Unknown stock sector/industry via yfinance after draft build",
    )
    p.add_argument(
        "--enrich-sectors-yahoo-limit",
        type=int,
        default=None,
        help="Max yfinance calls when --enrich-sectors-yahoo is set",
    )
    p.add_argument(
        "--format",
        choices=("json", "text"),
        default="text",
        help="Stdout summary format",
    )
    return p.parse_args()


def _format_text(report: dict) -> str:
    c = report.get("counts") or {}
    v = report.get("validation") or {}
    lines = [
        f"Universe ingestion report ({report.get('version')})",
        f"dry_run={report.get('dry_run')}",
        "",
        "Counts:",
        f"  downloaded rows: {c.get('total_rows_downloaded')}",
        f"  unique tickers (raw): {c.get('unique_tickers_raw')}",
        f"  kept: {c.get('rows_kept')} | removed: {c.get('rows_removed')} | flagged: {c.get('rows_flagged')}",
        f"  draft ETFs: {c.get('draft_etfs')} | draft stocks: {c.get('draft_stocks')}",
        f"  needs_review: {c.get('needs_review_count')} | low confidence: {c.get('low_confidence_count')}",
        f"  silent default EQ: {c.get('silent_default_eq_count')}",
        "",
        "Validation:",
        f"  draft ETF: {v.get('draft_etf_universe', {}).get('status')}",
        f"  draft stock: {v.get('draft_stock_universe', {}).get('status')}",
        f"  production modified: {v.get('production_files_modified')}",
        "",
        report.get("pnl_readiness_note", ""),
        report.get("rc_readiness_note", ""),
    ]
    top = report.get("top_warning_categories") or []
    if top:
        lines.append("")
        lines.append("Top warning categories:")
        for cat, n in top[:10]:
            lines.append(f"  {cat}: {n}")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    out_dir = Path(args.output_dir)
    try:
        report = run_ingestion_pipeline(
            nasdaq_listed_source=args.nasdaq_listed_url,
            other_listed_source=args.other_listed_url,
            sec_tickers_source=args.sec_company_tickers_url,
            output_dir=out_dir,
            dry_run=args.dry_run,
            limit=args.limit,
            enrich_sectors_yahoo=args.enrich_sectors_yahoo,
            enrich_sectors_yahoo_limit=args.enrich_sectors_yahoo_limit,
        )
    except Exception as exc:
        print(f"Ingestion failed: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(_format_text(report), end="")

    val = report.get("validation") or {}
    if val.get("draft_etf_universe", {}).get("status") == "FAIL":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
