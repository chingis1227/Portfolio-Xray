#!/usr/bin/env python3
"""Re-enrich Stock Batch 1 draft rows (throttled Yahoo) and refresh review report."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.stock_batch_ingestion import (
    MIN_BATCH2_ACCEPTED,
    _assess_row,
    _merge_ready,
    _write_batch_artifacts,
)
from src.universe_ingestion import _upper_ticker, enrich_stock_sector_yahoo
from src.universe_merge import load_draft_universe_yaml
from src.stock_universe import load_stock_universe


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Throttled Yahoo enrichment for Stock Batch 1 draft")
    p.add_argument("--batch-dir", default=None, help="Override batch output directory")
    p.add_argument("--batch", type=int, choices=(1, 2), default=1, help="Stock batch number")
    p.add_argument("--stock-universe", default="config/stock_universe.yml")
    p.add_argument("--sleep-seconds", type=float, default=1.5, help="Delay between Yahoo calls")
    p.add_argument("--max-calls", type=int, default=None, help="Limit Yahoo calls this run")
    p.add_argument(
        "--checkpoint-every",
        type=int,
        default=25,
        help="Save draft + review report every N Yahoo calls (0 = only at end)",
    )
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def _rebuild_and_write(
    batch_dir: Path,
    batch_num: int,
    rows: list,
    prod_by: dict,
    *,
    yahoo_calls: int,
    sleep_seconds: float,
) -> tuple[int, int, bool]:
    from collections import Counter

    accepted, rejected, needs_review, in_production = [], [], [], []
    seen: set[str] = set()
    reject_reasons: Counter[str] = Counter()
    for row in rows:
        disp, reason = _assess_row(row, prod_by_ticker=prod_by, seen_tickers=seen)
        ticker = _upper_ticker(row.get("ticker"))
        seen.add(ticker)
        if disp == "accepted":
            accepted.append(row)
        elif disp == "in_production":
            in_production.append(row)
        elif disp == "needs_review":
            needs_review.append({**row, "review_reason": reason})
        else:
            reject_reasons[reason] += 1
            rejected.append({**row, "reject_reason": reason})

    report_path = batch_dir / f"stock_batch{batch_num}_review_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.is_file() else {}
    report.setdefault("summary", {})
    min_acc = MIN_BATCH2_ACCEPTED if batch_num == 2 else None
    merge_ready = _merge_ready(accepted, rejected, needs_review, min_accepted=min_acc)
    report["summary"].update(
        {
            "accepted_candidates": len(accepted),
            "rejected_candidates": len(rejected),
            "needs_review_candidates": len(needs_review),
            "already_in_production": len(in_production),
            "missing_sector_industry": sum(
                1
                for r in rows
                if str(r.get("sector")) in ("", "Unknown") or str(r.get("industry")) in ("", "Unknown")
            ),
            "merge_ready": merge_ready,
            "recommended_new_tickers": len(accepted),
        }
    )
    report["reject_reason_counts"] = dict(reject_reasons)
    report["accepted_tickers"] = sorted(_upper_ticker(r.get("ticker")) for r in accepted)
    report["enrichment_refresh"] = {
        "yahoo_calls_last_run": yahoo_calls,
        "sleep_seconds": sleep_seconds,
    }
    _write_batch_artifacts(
        batch_dir,
        batch_num,
        draft_rows=rows,
        accepted=accepted,
        rejected=rejected,
        needs_review=needs_review,
        review_report=report,
    )
    return len(accepted), len(rejected), merge_ready


def main() -> int:
    args = parse_args()
    batch_dir = Path(args.batch_dir) if args.batch_dir else Path(
        f"output/stock_batch{args.batch}_live"
    )
    draft_path = batch_dir / f"draft_stock_universe_batch{args.batch}.yml"
    if not draft_path.is_file():
        print(f"Missing {draft_path}", file=sys.stderr)
        return 1

    prod_by = {
        _upper_ticker(r["ticker"]): r
        for r in load_stock_universe(args.stock_universe)
        if r.get("ticker")
    }
    rows = load_draft_universe_yaml(draft_path)
    calls = 0
    for row in rows:
        t = _upper_ticker(row.get("ticker"))
        if t in prod_by:
            continue
        if str(row.get("industry") or "") not in ("", "Unknown"):
            continue
        if args.max_calls is not None and calls >= args.max_calls:
            break
        if args.dry_run:
            calls += 1
            continue
        time.sleep(max(0.0, args.sleep_seconds))
        meta = enrich_stock_sector_yahoo(t)
        calls += 1
        if meta.get("sector") not in ("", "Unknown"):
            row["sector"] = meta["sector"]
        if meta.get("industry") not in ("", "Unknown"):
            row["industry"] = meta["industry"]
        row["notes"] = (row.get("notes") or "") + f" Refresh enrichment: {meta.get('source')}."
        if args.checkpoint_every > 0 and calls % args.checkpoint_every == 0:
            n_acc, n_rej, _ = _rebuild_and_write(
                batch_dir,
                args.batch,
                rows,
                prod_by,
                yahoo_calls=calls,
                sleep_seconds=args.sleep_seconds,
            )
            print(f"Checkpoint @{calls}: accepted={n_acc} rejected={n_rej}", flush=True)

    if args.dry_run:
        print(f"Would call Yahoo for up to {calls} tickers")
        return 0

    n_acc, n_rej, merge_ready = _rebuild_and_write(
        batch_dir,
        args.batch,
        rows,
        prod_by,
        yahoo_calls=calls,
        sleep_seconds=args.sleep_seconds,
    )
    print(
        f"Yahoo calls: {calls}; accepted: {n_acc}; rejected: {n_rej}; merge_ready: {merge_ready}",
        flush=True,
    )
    return 0 if merge_ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
