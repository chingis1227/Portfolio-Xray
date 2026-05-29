"""
Controlled merge of draft universe YAML into production config files.

Never merges without explicit confirmation. Produces diff report before write.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml

from src.etf_universe import load_etf_universe, validate_etf_universe
from src.stock_universe import INDEX_MEMBERSHIP_VALUES, load_stock_universe, validate_stock_universe
from src.universe_ingestion import enrich_draft_stocks, load_production_stock_sector_lookup

MergeKind = Literal["etf", "stock"]


def _upper_ticker(value: Any) -> str:
    return str(value or "").strip().upper()


def load_draft_universe_yaml(path: Path) -> list[dict[str, Any]]:
    """Load draft YAML list (skips # comment lines)."""
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    lines = [ln for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    if not lines:
        return []
    data = yaml.safe_load("\n".join(lines))
    if not isinstance(data, list):
        raise ValueError(f"Draft universe must be a YAML list: {path}")
    return [dict(x) for x in data if isinstance(x, dict)]


def load_needs_review_tickers(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    import pandas as pd

    df = pd.read_csv(path)
    if "ticker" not in df.columns:
        return set()
    return {_upper_ticker(t) for t in df["ticker"].tolist() if _upper_ticker(t)}


@dataclass
class MergePlan:
    etf_to_add: list[dict[str, Any]] = field(default_factory=list)
    stock_to_add: list[dict[str, Any]] = field(default_factory=list)
    etf_skipped_existing: list[str] = field(default_factory=list)
    stock_skipped_existing: list[str] = field(default_factory=list)
    etf_skipped_needs_review: list[str] = field(default_factory=list)
    stock_skipped_needs_review: list[str] = field(default_factory=list)
    stock_skipped_not_sp500: list[str] = field(default_factory=list)
    stock_skipped_invalid_index: list[str] = field(default_factory=list)
    stock_skipped_unknown_sector: list[str] = field(default_factory=list)
    etf_conflicts: list[dict[str, Any]] = field(default_factory=list)
    stock_conflicts: list[dict[str, Any]] = field(default_factory=list)


def _row_diff(prod: dict[str, Any], draft: dict[str, Any]) -> dict[str, tuple[Any, Any]]:
    keys = sorted(set(prod) | set(draft))
    diff: dict[str, tuple[Any, Any]] = {}
    for k in keys:
        if k in ("notes",):
            continue
        if prod.get(k) != draft.get(k):
            diff[k] = (prod.get(k), draft.get(k))
    return diff


def build_merge_plan(
    *,
    draft_etf_path: Path,
    draft_stock_path: Path,
    needs_review_path: Path | None = None,
    production_etf_path: Path,
    production_stock_path: Path,
    tickers_filter: set[str] | None = None,
    include_needs_review: bool = False,
    include_etfs: bool = True,
    include_stocks: bool = False,
    enrich_stocks_yahoo: bool = False,
    enrich_stocks_yahoo_limit: int | None = None,
    stock_batch_mode: bool = False,
) -> tuple[MergePlan, dict[str, Any]]:
    """Compute merge plan without writing production files."""
    draft_etfs = load_draft_universe_yaml(draft_etf_path) if include_etfs else []
    draft_stocks = load_draft_universe_yaml(draft_stock_path) if include_stocks else []

    if include_stocks and enrich_stocks_yahoo:
        lookup = load_production_stock_sector_lookup(production_stock_path)
        draft_stocks, enrich_meta = enrich_draft_stocks(
            draft_stocks,
            production_lookup=lookup,
            use_yahoo=True,
            yahoo_limit=enrich_stocks_yahoo_limit,
        )
    else:
        enrich_meta = {}

    prod_etfs = { _upper_ticker(r["ticker"]): r for r in load_etf_universe(production_etf_path) if r.get("ticker") }
    prod_stocks = {
        _upper_ticker(r["ticker"]): r for r in load_stock_universe(production_stock_path) if r.get("ticker")
    }

    needs_review = load_needs_review_tickers(needs_review_path) if needs_review_path else set()
    plan = MergePlan()

    for row in draft_etfs:
        t = _upper_ticker(row.get("ticker"))
        if not t or (tickers_filter and t not in tickers_filter):
            continue
        if not include_needs_review and t in needs_review:
            plan.etf_skipped_needs_review.append(t)
            continue
        if t in prod_etfs:
            diff = _row_diff(prod_etfs[t], row)
            if diff:
                plan.etf_conflicts.append({"ticker": t, "field_diff": {k: list(v) for k, v in diff.items()}})
            else:
                plan.etf_skipped_existing.append(t)
            continue
        plan.etf_to_add.append(row)

    for row in draft_stocks:
        t = _upper_ticker(row.get("ticker"))
        if not t or (tickers_filter and t not in tickers_filter):
            continue
        if not include_needs_review and t in needs_review:
            plan.stock_skipped_needs_review.append(t)
            continue
        membership = row.get("index_membership") or []
        if stock_batch_mode:
            if (
                len(membership) != 1
                or membership[0] not in INDEX_MEMBERSHIP_VALUES
            ):
                plan.stock_skipped_invalid_index.append(t)
                continue
        elif membership != ["SP500"]:
            plan.stock_skipped_not_sp500.append(t)
            continue
        if str(row.get("sector") or "") in ("", "Unknown") or str(row.get("industry") or "") in ("", "Unknown"):
            plan.stock_skipped_unknown_sector.append(t)
            continue
        if t in prod_stocks:
            diff = _row_diff(prod_stocks[t], row)
            if diff:
                plan.stock_conflicts.append({"ticker": t, "field_diff": {k: list(v) for k, v in diff.items()}})
            else:
                plan.stock_skipped_existing.append(t)
            continue
        clean = {k: v for k, v in row.items() if k != "notes"}
        plan.stock_to_add.append(clean)

    meta = {
        "draft_etf_rows": len(draft_etfs),
        "draft_stock_rows": len(draft_stocks),
        "production_etf_count": len(prod_etfs),
        "production_stock_count": len(prod_stocks),
        "stock_enrichment": enrich_meta,
    }
    return plan, meta


def merge_plan_to_report(plan: MergePlan, meta: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": "universe_merge_plan_v1",
        "summary": {
            "etf_to_add": len(plan.etf_to_add),
            "stock_to_add": len(plan.stock_to_add),
            "etf_skipped_existing": len(plan.etf_skipped_existing),
            "stock_skipped_existing": len(plan.stock_skipped_existing),
            "etf_skipped_needs_review": len(plan.etf_skipped_needs_review),
            "stock_skipped_needs_review": len(plan.stock_skipped_needs_review),
            "stock_skipped_not_sp500": len(plan.stock_skipped_not_sp500),
            "stock_skipped_invalid_index": len(plan.stock_skipped_invalid_index),
            "stock_skipped_unknown_sector": len(plan.stock_skipped_unknown_sector),
            "etf_conflicts": len(plan.etf_conflicts),
            "stock_conflicts": len(plan.stock_conflicts),
        },
        "etf_to_add_tickers": sorted(_upper_ticker(r.get("ticker")) for r in plan.etf_to_add),
        "stock_to_add_tickers": sorted(_upper_ticker(r.get("ticker")) for r in plan.stock_to_add),
        "etf_skipped_needs_review": sorted(plan.etf_skipped_needs_review)[:100],
        "stock_skipped_needs_review": sorted(plan.stock_skipped_needs_review)[:100],
        "etf_conflicts": plan.etf_conflicts[:50],
        "stock_conflicts": plan.stock_conflicts[:50],
        "meta": meta,
    }


def _format_yaml_records(records: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for rec in records:
        lines.append("- " + yaml.dump(rec, default_flow_style=True, allow_unicode=True).strip())
    return lines


def _read_yaml_header_comments(path: Path) -> list[str]:
    if not path.is_file():
        return []
    header: list[str] = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        if ln.strip().startswith("#"):
            header.append(ln)
        elif not ln.strip():
            if header:
                header.append(ln)
        else:
            break
    return header


def apply_merge_plan(
    plan: MergePlan,
    *,
    production_etf_path: Path,
    production_stock_path: Path,
    backup_dir: Path | None = None,
) -> dict[str, Any]:
    """Append planned rows to production universe files (with optional backup)."""
    result: dict[str, Any] = {"etf_added": 0, "stock_added": 0, "backups": []}

    if backup_dir:
        backup_dir.mkdir(parents=True, exist_ok=True)
        for src in (production_etf_path, production_stock_path):
            if src.is_file():
                dest = backup_dir / src.name
                dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
                result["backups"].append(str(dest))

    if plan.etf_to_add:
        existing = load_etf_universe(production_etf_path)
        merged = existing + plan.etf_to_add
        val = validate_etf_universe(merged)
        if val.get("status") == "FAIL":
            raise RuntimeError(f"ETF merge validation failed: {val.get('errors', [])[:5]}")
        header = _read_yaml_header_comments(production_etf_path)
        body = _format_yaml_records(merged)
        production_etf_path.write_text("\n".join(header + body) + "\n", encoding="utf-8")
        result["etf_added"] = len(plan.etf_to_add)
        result["etf_validation"] = val.get("status")

    if plan.stock_to_add:
        existing = load_stock_universe(production_stock_path)
        merged = existing + plan.stock_to_add
        val = validate_stock_universe(merged)
        if val.get("status") == "FAIL":
            raise RuntimeError(f"Stock merge validation failed: {val.get('errors', [])[:5]}")
        header = _read_yaml_header_comments(production_stock_path)
        body = _format_yaml_records(merged)
        production_stock_path.write_text("\n".join(header + body) + "\n", encoding="utf-8")
        result["stock_added"] = len(plan.stock_to_add)
        result["stock_validation"] = val.get("status")

    return result


def format_merge_plan_text(report: dict[str, Any]) -> str:
    s = report.get("summary") or {}
    lines = [
        "Universe merge plan (dry-run unless --confirm)",
        "",
        f"  ETFs to add: {s.get('etf_to_add', 0)}",
        f"  Stocks to add: {s.get('stock_to_add', 0)}",
        f"  ETF skipped (needs_review): {s.get('etf_skipped_needs_review', 0)}",
        f"  ETF skipped (already exists): {s.get('etf_skipped_existing', 0)}",
        f"  ETF conflicts: {s.get('etf_conflicts', 0)}",
        f"  Stock skipped (not SP500): {s.get('stock_skipped_not_sp500', 0)}",
        f"  Stock skipped (invalid index): {s.get('stock_skipped_invalid_index', 0)}",
        f"  Stock skipped (unknown sector): {s.get('stock_skipped_unknown_sector', 0)}",
    ]
    sample = report.get("etf_to_add_tickers") or []
    if sample:
        lines.append("")
        lines.append(f"Sample ETF tickers to add ({min(20, len(sample))} of {len(sample)}):")
        lines.append("  " + ", ".join(sample[:20]))
    conflicts = report.get("etf_conflicts") or []
    if conflicts:
        lines.append("")
        lines.append("ETF conflicts (ticker exists with different fields):")
        for c in conflicts[:5]:
            lines.append(f"  {c.get('ticker')}: {list((c.get('field_diff') or {}).keys())}")
    return "\n".join(lines) + "\n"


__all__ = [
    "apply_merge_plan",
    "build_merge_plan",
    "format_merge_plan_text",
    "load_draft_universe_yaml",
    "merge_plan_to_report",
]
