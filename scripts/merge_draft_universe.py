#!/usr/bin/env python3
"""Controlled merge of draft universe YAML into production config (requires --confirm)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.universe_merge import (
    apply_merge_plan,
    build_merge_plan,
    format_merge_plan_text,
    merge_plan_to_report,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Merge draft ETF/stock universe into production YAML with diff preview",
    )
    p.add_argument(
        "--ingestion-dir",
        default="output/universe_ingestion",
        help="Folder with draft_etf_universe.yml, draft_stock_universe.yml, needs_review.csv",
    )
    p.add_argument("--etf-universe", default="config/etf_universe.yml")
    p.add_argument("--stock-universe", default="config/stock_universe.yml")
    p.add_argument(
        "--tickers",
        default=None,
        help="Comma-separated tickers to merge (default: all eligible in draft)",
    )
    p.add_argument("--include-etfs", action="store_true", default=True)
    p.add_argument("--no-etfs", action="store_false", dest="include_etfs")
    p.add_argument("--include-stocks", action="store_true", help="Merge SP500-validated stocks only")
    p.add_argument(
        "--include-needs-review",
        action="store_true",
        help="Allow tickers listed in needs_review.csv (default: skip)",
    )
    p.add_argument(
        "--enrich-stocks-yahoo",
        action="store_true",
        help="Enrich stock sector/industry via yfinance before merge",
    )
    p.add_argument("--enrich-stocks-yahoo-limit", type=int, default=None)
    p.add_argument(
        "--confirm",
        action="store_true",
        help="Apply merge after preview (writes production YAML; creates backup)",
    )
    p.add_argument(
        "--backup-dir",
        default=None,
        help="Backup production YAML here before merge (default: <ingestion-dir>/merge_backup)",
    )
    p.add_argument("--format", choices=("text", "json"), default="text")
    p.add_argument(
        "--report-out",
        default=None,
        help="Write merge plan JSON to this path (default: <ingestion-dir>/merge_plan.json)",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    ingestion_dir = Path(args.ingestion_dir)
    draft_etf = ingestion_dir / "draft_etf_universe.yml"
    draft_stock = ingestion_dir / "draft_stock_universe.yml"
    needs_review = ingestion_dir / "needs_review.csv"

    tickers_filter = None
    if args.tickers:
        tickers_filter = {t.strip().upper() for t in args.tickers.split(",") if t.strip()}

    plan, meta = build_merge_plan(
        draft_etf_path=draft_etf,
        draft_stock_path=draft_stock,
        needs_review_path=needs_review if needs_review.is_file() else None,
        production_etf_path=Path(args.etf_universe),
        production_stock_path=Path(args.stock_universe),
        tickers_filter=tickers_filter,
        include_needs_review=args.include_needs_review,
        include_etfs=args.include_etfs,
        include_stocks=args.include_stocks,
        enrich_stocks_yahoo=args.enrich_stocks_yahoo,
        enrich_stocks_yahoo_limit=args.enrich_stocks_yahoo_limit,
    )
    report = merge_plan_to_report(plan, meta)
    report["confirmed"] = args.confirm

    report_path = Path(args.report_out) if args.report_out else ingestion_dir / "merge_plan.json"
    if not args.confirm:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(format_merge_plan_text(report), end="")
        print(f"Full plan: {report_path}")

    if not args.confirm:
        print("\nDry-run only. Re-run with --confirm to apply merge.", file=sys.stderr)
        return 0

    if not plan.etf_to_add and not plan.stock_to_add:
        print("Nothing to merge.", file=sys.stderr)
        return 0

    backup_dir = Path(args.backup_dir) if args.backup_dir else ingestion_dir / "merge_backup"
    try:
        result = apply_merge_plan(
            plan,
            production_etf_path=Path(args.etf_universe),
            production_stock_path=Path(args.stock_universe),
            backup_dir=backup_dir,
        )
    except RuntimeError as exc:
        print(f"Merge failed: {exc}", file=sys.stderr)
        return 1

    report["merge_result"] = result
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        f"Merged: ETF +{result.get('etf_added', 0)}, Stock +{result.get('stock_added', 0)}. "
        f"Backups: {result.get('backups')}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
