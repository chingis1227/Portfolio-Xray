#!/usr/bin/env python3
"""Build Stock Batch 2 draft (remaining R1000 / liquid R3000, excluding production)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.stock_batch_ingestion import MAX_BATCH2_SIZE, MIN_BATCH2_ACCEPTED, run_stock_batch2_pipeline


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build Stock Batch 2 draft + review artifacts")
    p.add_argument("--output-dir", default="output/stock_batch2_live")
    p.add_argument("--stock-universe", default="config/stock_universe.yml")
    p.add_argument("--max-tickers", type=int, default=MAX_BATCH2_SIZE)
    p.add_argument("--min-accepted", type=int, default=MIN_BATCH2_ACCEPTED)
    p.add_argument(
        "--prefill-r3000-caps",
        type=int,
        default=0,
        metavar="N",
        help="Fetch Yahoo market cap for up to N R3000-band tickers before selection (slow)",
    )
    p.add_argument("--dry-run", action="store_true")
    p.add_argument(
        "--with-r2000-liquid",
        action="store_true",
        default=True,
        help="Include large/liquid Russell 3000 names outside R1000 (default: on)",
    )
    p.add_argument(
        "--no-r2000-liquid",
        action="store_false",
        dest="with_r2000_liquid",
        help="R1000-only expansion (no R3000 liquid band)",
    )
    p.add_argument(
        "--with-r1000-market-cap",
        action="store_true",
        help="Use Yahoo market-cap ranking for R1000 tags (slow; risks rate limits)",
    )
    p.add_argument("--format", choices=("text", "json"), default="text")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    result = run_stock_batch2_pipeline(
        output_dir=Path(args.output_dir),
        production_stock_path=Path(args.stock_universe),
        max_tickers=args.max_tickers,
        min_accepted=args.min_accepted,
        include_r2000_liquid=args.with_r2000_liquid,
        dry_run=args.dry_run,
        skip_r1000_market_cap=not args.with_r1000_market_cap,
        prefill_r3000_caps=args.prefill_r3000_caps,
    )
    report = result.review_report
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        s = report.get("summary") or {}
        print("Stock Batch 2 review")
        print(f"  Production before: {report.get('production_count_before')}")
        print(f"  Candidates screened: {s.get('total_candidates_screened')}")
        print(f"  Accepted (new): {s.get('accepted_candidates')}")
        print(f"  Rejected: {s.get('rejected_candidates')}")
        print(f"  Already in production: {s.get('already_in_production')}")
        print(f"  Missing sector/industry: {s.get('missing_sector_industry')}")
        print(f"  Merge ready: {s.get('merge_ready')}")
        if not args.dry_run:
            print(f"  Artifacts: {args.output_dir}")
    return 0 if result.merge_ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
