#!/usr/bin/env python3
"""Apply field-level conflict resolutions from conflict_resolution_plan.json (never full-row overwrite)."""
from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.etf_universe import load_etf_universe, validate_etf_universe
from src.universe_merge import _format_yaml_records, _read_yaml_header_comments


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Apply safe field-level ETF conflict updates")
    p.add_argument(
        "--plan",
        default="output/universe_ingestion_live/conflict_resolution_plan.json",
        help="Conflict resolution plan JSON",
    )
    p.add_argument("--etf-universe", default="config/etf_universe.yml")
    p.add_argument("--ingestion-dir", default="output/universe_ingestion_live")
    p.add_argument(
        "--tickers",
        default=None,
        help="Optional comma-separated subset; default: all update_from_draft in plan",
    )
    p.add_argument("--confirm", action="store_true", help="Write production YAML after preview")
    p.add_argument("--backup-dir", default=None)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    plan_path = Path(args.plan)
    if not plan_path.is_file():
        print(f"Plan not found: {plan_path}", file=sys.stderr)
        return 1

    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    safe = [c for c in plan.get("conflicts", []) if c.get("recommended_action") == "update_from_draft"]
    if args.tickers:
        allow = {t.strip().upper() for t in args.tickers.split(",") if t.strip()}
        safe = [c for c in safe if c["ticker"] in allow]

    if not safe:
        print("No safe update_from_draft entries to apply.", file=sys.stderr)
        return 0

    draft_path = Path(args.ingestion_dir) / "draft_etf_universe.yml"
    from src.universe_merge import load_draft_universe_yaml

    draft_by = {str(r["ticker"]).upper(): r for r in load_draft_universe_yaml(draft_path)}
    etf_path = Path(args.etf_universe)
    records = load_etf_universe(etf_path)
    by_ticker = {str(r["ticker"]).upper(): r for r in records}

    preview: list[dict] = []
    for item in safe:
        t = item["ticker"]
        fields = item.get("safe_field_updates") or []
        if t not in by_ticker:
            print(f"Skip {t}: not in production", file=sys.stderr)
            continue
        if t not in draft_by:
            print(f"Skip {t}: not in draft", file=sys.stderr)
            continue
        if not fields:
            print(f"Skip {t}: no safe_field_updates listed", file=sys.stderr)
            continue
        prod = by_ticker[t]
        draft = draft_by[t]
        changes = {}
        for field in fields:
            if prod.get(field) == draft.get(field):
                continue
            changes[field] = [prod.get(field), draft.get(field)]
            prod[field] = draft.get(field)
        if changes:
            preview.append({"ticker": t, "fields": changes, "reason": item.get("reason")})

    print(json.dumps({"updates": preview, "count": len(preview)}, indent=2, ensure_ascii=False))
    if not preview:
        print("Nothing to change after field comparison.", file=sys.stderr)
        return 0

    if not args.confirm:
        print("\nDry-run only. Re-run with --confirm to apply field-level updates.", file=sys.stderr)
        return 0

    val = validate_etf_universe(records)
    if val.get("status") != "PASS" or val.get("warnings"):
        print(f"Validation blocked: {val}", file=sys.stderr)
        return 1

    backup_dir = Path(args.backup_dir) if args.backup_dir else Path(args.ingestion_dir) / "merge_backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / etf_path.name
    backup.write_text(etf_path.read_text(encoding="utf-8"), encoding="utf-8")

    header = _read_yaml_header_comments(etf_path)
    body = _format_yaml_records(records)
    etf_path.write_text("\n".join(header + body) + "\n", encoding="utf-8")
    print(f"Applied {len(preview)} field-level updates. Backup: {backup}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
