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
    p.add_argument(
        "--stock-batch-dir",
        default=None,
        help="Stock batch folder (draft_stock_universe_batchN.yml + accepted tickers filter)",
    )
    p.add_argument(
        "--stock-batch",
        type=int,
        choices=(1, 2),
        default=None,
        help="Stock batch number (sets default dir to output/stock_batchN_live)",
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
    stock_batch_num = args.stock_batch
    stock_batch_dir = Path(args.stock_batch_dir) if args.stock_batch_dir else None
    if stock_batch_dir is None and stock_batch_num is not None:
        stock_batch_dir = Path(f"output/stock_batch{stock_batch_num}_live")
    draft_etf = ingestion_dir / "draft_etf_universe.yml"
    draft_stock = ingestion_dir / "draft_stock_universe.yml"
    needs_review = ingestion_dir / "needs_review.csv"
    stock_batch_mode = False
    report_path: Path | None = None
    batch_label = "Stock Batch"
    if stock_batch_dir:
        bn = stock_batch_num
        if bn is None:
            for n in (2, 1):
                if (stock_batch_dir / f"stock_batch{n}_review_report.json").is_file():
                    bn = n
                    break
            bn = bn or 1
        batch_label = f"Stock Batch {bn}"
        draft_stock = stock_batch_dir / f"draft_stock_universe_batch{bn}.yml"
        nr_csv = stock_batch_dir / (
            "needs_review_stocks.csv" if bn == 1 else f"needs_review_stocks_batch{bn}.csv"
        )
        needs_review = nr_csv
        stock_batch_mode = True
        report_path = stock_batch_dir / f"stock_batch{bn}_review_report.json"
        if report_path.is_file():
            import json as _json

            batch_report = _json.loads(report_path.read_text(encoding="utf-8"))
            summary = batch_report.get("summary") or {}
            if not summary.get("merge_ready"):
                print(f"{batch_label} merge blocked: merge_ready=false.", file=sys.stderr)
                if summary.get("needs_review_candidates", 0) > 0:
                    print("  Reason: needs_review > 0", file=sys.stderr)
                if summary.get("missing_sector_industry", 0) > 0:
                    print(
                        f"  Reason: missing sector/industry on draft rows ({summary.get('missing_sector_industry')})",
                        file=sys.stderr,
                    )
                return 2

    tickers_filter = None
    if args.tickers:
        tickers_filter = {t.strip().upper() for t in args.tickers.split(",") if t.strip()}

    if stock_batch_dir and not args.include_stocks:
        args.include_stocks = True

    if stock_batch_dir and tickers_filter is None and report_path and report_path.is_file():
        import json as _json

        batch_report = _json.loads(report_path.read_text(encoding="utf-8"))
        tickers_filter = {t.upper() for t in batch_report.get("accepted_tickers") or []}

    plan, meta = build_merge_plan(
        draft_etf_path=draft_etf,
        draft_stock_path=draft_stock,
        needs_review_path=needs_review if needs_review.is_file() else None,
        production_etf_path=Path(args.etf_universe),
        production_stock_path=Path(args.stock_universe),
        tickers_filter=tickers_filter,
        include_needs_review=args.include_needs_review,
        include_etfs=args.include_etfs and not stock_batch_mode,
        include_stocks=args.include_stocks or bool(stock_batch_dir),
        enrich_stocks_yahoo=args.enrich_stocks_yahoo,
        enrich_stocks_yahoo_limit=args.enrich_stocks_yahoo_limit,
        stock_batch_mode=stock_batch_mode,
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
