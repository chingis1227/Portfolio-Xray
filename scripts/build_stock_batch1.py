#!/usr/bin/env python3
"""Build Stock Batch 1 draft universe from index-based sources (no production writes)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.stock_batch_ingestion import (
    MAX_BATCH1_SIZE,
    build_batch1_merge_preview,
    run_stock_batch1_pipeline,
)
from src.universe_merge import format_merge_plan_text, merge_plan_to_report


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build Stock Batch 1 draft + review artifacts")
    p.add_argument(
        "--output-dir",
        default="output/stock_batch1",
        help="Output folder for draft YAML, review JSON, needs_review_stocks.csv",
    )
    p.add_argument("--stock-universe", default="config/stock_universe.yml")
    p.add_argument("--max-tickers", type=int, default=MAX_BATCH1_SIZE)
    p.add_argument("--dry-run", action="store_true", help="Compute report only; do not write files")
    p.add_argument(
        "--offline",
        action="store_true",
        help="Use production SP500 only (no network); for tests/air-gapped",
    )
    p.add_argument("--no-enrich-yahoo", action="store_true")
    p.add_argument(
        "--no-r1000-market-cap",
        action="store_true",
        help="Skip Yahoo market-cap ranking; tag R1000 as SP500 plus next non-SP500 R3000 names",
    )
    p.add_argument("--enrich-yahoo-limit", type=int, default=500)
    p.add_argument(
        "--include-r2000-liquid",
        action="store_true",
        help="Include large/liquid Russell 3000 names outside R1000 (market-cap filtered)",
    )
    p.add_argument("--sp500-url", default=None)
    p.add_argument("--r1000-url", default=None)
    p.add_argument("--r3000-url", default=None)
    p.add_argument("--r1000-csv", default=None, help="Local Russell 1000 constituents CSV")
    p.add_argument("--r3000-csv", default=None, help="Local Russell 3000 constituents CSV")
    p.add_argument(
        "--merge-preview",
        action="store_true",
        help="After build, print controlled merge preview for accepted new tickers",
    )
    p.add_argument("--format", choices=("text", "json"), default="text")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    kwargs: dict = {
        "output_dir": output_dir,
        "production_stock_path": Path(args.stock_universe),
        "max_tickers": args.max_tickers,
        "include_r2000_liquid": args.include_r2000_liquid,
        "enrich_yahoo": not args.no_enrich_yahoo,
        "yahoo_limit": args.enrich_yahoo_limit,
        "dry_run": args.dry_run,
        "offline": args.offline,
        "skip_r1000_market_cap": args.no_r1000_market_cap,
    }
    if args.sp500_url:
        kwargs["sp500_source"] = args.sp500_url
    if args.r1000_url:
        kwargs["r1000_source"] = args.r1000_url
    if args.r3000_url:
        kwargs["r3000_source"] = args.r3000_url
    if args.r1000_csv:
        kwargs["r1000_csv"] = Path(args.r1000_csv)
    if args.r3000_csv:
        kwargs["r3000_csv"] = Path(args.r3000_csv)

    result = run_stock_batch1_pipeline(**kwargs)
    report = result.review_report

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        s = report.get("summary") or {}
        print("Stock Batch 1 review")
        print(f"  Candidates: {s.get('total_candidates')}")
        print(f"  Accepted (new, merge-eligible): {s.get('accepted_candidates')}")
        print(f"  Already in production: {s.get('already_in_production')}")
        print(f"  Rejected: {s.get('rejected_candidates')}")
        print(f"  Needs review: {s.get('needs_review_candidates')}")
        print(f"  Merge ready: {s.get('merge_ready')}")
        if not args.dry_run:
            print(f"  Artifacts: {output_dir}")

    if args.merge_preview and not args.dry_run:
        plan, meta = build_batch1_merge_preview(
            output_dir=output_dir,
            production_stock_path=Path(args.stock_universe),
        )
        mreport = merge_plan_to_report(plan, meta)
        print(format_merge_plan_text(mreport), end="")
        preview_path = output_dir / "stock_batch1_merge_plan.json"
        preview_path.write_text(json.dumps(mreport, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Merge preview: {preview_path}")

    if not result.merge_ready:
        print(
            "\nStop: merge blocked until review report is clean (no needs_review, no blocking rejects).",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
