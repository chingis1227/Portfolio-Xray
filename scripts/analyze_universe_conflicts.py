#!/usr/bin/env python3
"""Analyze production vs draft ETF taxonomy conflicts (read-only plan generator)."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.etf_universe import load_etf_universe
from src.taxonomy_stress_blocks import (
    assess_classification,
    derive_stress_block_from_taxonomy_row,
)
from src.universe_ingestion import classify_etf, _detect_hybrid_flags
from src.universe_merge import build_merge_plan, load_draft_universe_yaml, load_needs_review_tickers

TAXONOMY_FIELDS = (
    "asset_class",
    "subtype",
    "main_risk_factor",
    "credit_quality",
    "duration_bucket",
    "region",
    "sector",
    "issuer",
    "currency_exposure",
    "risk_role",
    "secondary_risk_factors",
    "thematic_primary",
    "thematic_tags",
    "name",
    "canonical_ticker",
)

INGESTION_ONLY_FIELDS = frozenset(
    {
        "data_source",
        "duplicate_group_id",
        "notes",
    }
)

PRIORITY_TICKERS = frozenset(
    {
        "SPY", "VOO", "IVV", "VTI", "QQQ", "DIA", "IWM",
        "EFA", "VEA", "IEFA", "EEM", "VWO", "IEMG", "VXUS", "IXUS",
        "BND", "AGG", "BIV", "BSV", "BLV", "TLT", "IEF", "SHY", "SHV", "GOVT", "VGIT", "VGLT",
        "BIL", "SGOV", "SHV", "TFLO", "USFR",
        "TIP", "SCHP", "VTIP", "STIP",
        "HYG", "JNK", "LQD", "VCIT", "VCSH", "IGSB", "MUB", "VTEB",
        "GLD", "IAU", "SLV", "GLDM", "PDBC", "DBC",
        "ARKK", "ARKG", "ARKX", "BOTZ", "CIBR", "CLOU", "DRIV",
        "AAXJ", "ASHR", "BBJP", "BATT", "BNO", "COPX", "CPER", "DBA", "DBB", "DBC",
        "DGRO", "EDV", "ELD", "ANGL", "BKLN", "AIQ", "AIA", "ARMY",
    }
)

BLOCK_PRIORITY = frozenset({"asset_class", "subtype", "main_risk_factor", "credit_quality", "duration_bucket"})


def _upper(value: Any) -> str:
    return str(value or "").strip().upper()


def _taxonomy_slice(row: dict[str, Any]) -> dict[str, Any]:
    return {k: row.get(k) for k in TAXONOMY_FIELDS if k in row}


def _field_diff(prod: dict[str, Any], draft: dict[str, Any]) -> dict[str, list[Any]]:
    diff: dict[str, list[Any]] = {}
    keys = sorted(set(prod) | set(draft))
    for k in keys:
        if k in INGESTION_ONLY_FIELDS:
            continue
        if prod.get(k) != draft.get(k):
            diff[k] = [prod.get(k), draft.get(k)]
    return diff


def _readiness(row: dict[str, Any] | None, *, universe_source: str) -> dict[str, Any]:
    if row is None:
        return {
            "stress_block": "EQ",
            "stress_block_source": "unknown",
            "silent_default_eq": True,
            "classification_confidence": "low",
            "needs_review": True,
            "xray_ready": False,
            "rc_ready": False,
            "warnings": ["missing row"],
        }
    resolution = derive_stress_block_from_taxonomy_row(row, universe_source="etf_universe")
    taxonomy_summary = {k: row.get(k) for k in TAXONOMY_FIELDS if k in row}
    confidence, needs_review, warnings = assess_classification(
        row=row,
        universe_source="etf_universe",
        resolution=resolution,
        taxonomy_summary=taxonomy_summary,
    )
    silent_default_eq = resolution.source == "unknown"
    rc_ready = not silent_default_eq and confidence != "low"
    xray_ready = row is not None and universe_source == "etf_universe"
    return {
        "stress_block": resolution.block,
        "stress_block_source": resolution.source,
        "silent_default_eq": silent_default_eq,
        "classification_confidence": confidence,
        "needs_review": needs_review,
        "xray_ready": xray_ready,
        "rc_ready": rc_ready,
        "warnings": warnings,
    }


def _draft_quality_flags(name: str, draft: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    nl = str(name or "").lower()
    clf = classify_etf(name, etf_flag=True)
    if clf.needs_review:
        flags.append("classifier_needs_review")
    if clf.classification_confidence != "high":
        flags.append(f"classifier_confidence:{clf.classification_confidence}")
    hybrid = [h for h in _detect_hybrid_flags(name) if h in {
        "leveraged", "inverse", "crypto", "volatility", "covered_call", "multi_asset",
    }]
    if hybrid:
        flags.append(f"hybrid:{','.join(hybrid)}")
    if draft.get("issuer") in (None, "", "unknown"):
        flags.append("unknown_issuer")
    if any(k in nl for k in ("2x", "3x", "inverse", "buffer", "covered call", "bitcoin", "crypto")):
        flags.append("risky_name_pattern")
    return flags


def _core_taxonomy_diff(taxonomy_diff: dict[str, list[Any]]) -> dict[str, list[Any]]:
    return {k: v for k, v in taxonomy_diff.items() if k in BLOCK_PRIORITY or k == "asset_class"}


def _draft_clearly_worse(
    *,
    prod: dict[str, Any],
    draft: dict[str, Any],
    prod_ready: dict[str, Any],
    draft_ready: dict[str, Any],
) -> bool:
    """True when draft classification is objectively lower quality than production."""
    if draft_ready["silent_default_eq"] and not prod_ready["silent_default_eq"]:
        return True
    ac_p = str(prod.get("asset_class") or "").lower()
    ac_d = str(draft.get("asset_class") or "").lower()
    if ac_p == "fixed_income" and ac_d == "equity":
        return True
    if ac_p == "commodity" and ac_d == "equity":
        return True
    if ac_p == "cash" and ac_d in {"fixed_income", "equity"}:
        return True
    if ac_p == "equity" and ac_d == "commodity" and str(draft.get("subtype") or "") != "gold":
        return True
    if prod_ready["rc_ready"] and not draft_ready["rc_ready"]:
        return True
    if prod_ready["classification_confidence"] == "high" and draft_ready["classification_confidence"] == "low":
        return True
    return False


def _recommend(
    *,
    ticker: str,
    prod: dict[str, Any],
    draft: dict[str, Any],
    diff: dict[str, list[Any]],
    prod_ready: dict[str, Any],
    draft_ready: dict[str, Any],
    draft_flags: list[str],
    in_needs_review: bool,
) -> tuple[str, str, list[str], bool]:
    """Return (action, reason, safe_field_updates, manual_review_required)."""
    taxonomy_diff = {k: v for k, v in diff.items() if k in TAXONOMY_FIELDS}
    core_diff = _core_taxonomy_diff(taxonomy_diff)
    metadata_diff = {k: v for k, v in diff.items() if k not in TAXONOMY_FIELDS and k not in INGESTION_ONLY_FIELDS}

    block_prod = prod_ready["stress_block"]
    block_draft = draft_ready["stress_block"]
    block_changed = block_prod != block_draft
    draft_worse = _draft_clearly_worse(prod=prod, draft=draft, prod_ready=prod_ready, draft_ready=draft_ready)

    manual_review_required = bool(
        block_changed
        or (ticker in PRIORITY_TICKERS and core_diff)
        or (ticker in PRIORITY_TICKERS and taxonomy_diff and not block_changed)
        or draft_flags
    )

    if in_needs_review:
        return "skip", "Ticker is in needs_review.csv; draft classification not trusted.", [], True

    if draft_flags:
        return (
            "keep_production",
            f"Draft has quality flags: {', '.join(draft_flags[:4])}.",
            [],
            manual_review_required,
        )

    if block_changed:
        if draft_worse:
            return (
                "keep_production",
                f"Draft stress block {block_draft} is worse than production {block_prod} "
                f"(misclassification / RC degradation).",
                [],
                True,
            )
        return (
            "manual_review",
            f"Stress block would change {block_prod} -> {block_draft}; requires human sign-off.",
            [],
            True,
        )

    if not taxonomy_diff and (metadata_diff or diff.keys() & INGESTION_ONLY_FIELDS):
        return (
            "keep_production",
            "Only ingestion metadata differs; production taxonomy unchanged.",
            [],
            ticker in PRIORITY_TICKERS,
        )

    if not taxonomy_diff:
        return "keep_production", "No taxonomy difference.", [], False

    # Same block — optional cosmetic name refresh
    if set(taxonomy_diff) == {"name"} and draft.get("name") and prod.get("name"):
        if len(str(draft.get("name"))) > len(str(prod.get("name"))) + 5:
            return (
                "update_from_draft",
                "Same stress block; draft has fuller official listing name only.",
                ["name"],
                True,
            )

    if core_diff and prod_ready["rc_ready"] and prod_ready["classification_confidence"] == "high":
        if ticker in PRIORITY_TICKERS:
            return (
                "keep_production",
                f"Priority ticker: production core taxonomy preferred over draft on {sorted(core_diff)}.",
                [],
                True,
            )
        return (
            "manual_review",
            f"Core taxonomy differs on {sorted(core_diff)} with unchanged block; case-by-case review.",
            [],
            True,
        )

    low_impact = set(taxonomy_diff) <= {
        "canonical_ticker", "name", "thematic_primary", "thematic_tags",
        "secondary_risk_factors", "risk_role", "issuer",
    }
    if low_impact and prod_ready["rc_ready"] and not block_changed:
        return (
            "keep_production",
            f"Low RC impact diffs only ({sorted(taxonomy_diff)}); production taxonomy retained.",
            [],
            ticker in PRIORITY_TICKERS,
        )

    cosmetic = set(taxonomy_diff) <= {
        "region", "sector", "thematic_primary", "thematic_tags",
        "secondary_risk_factors", "risk_role", "currency_exposure", "name", "issuer",
    }
    if cosmetic and prod_ready["rc_ready"]:
        if set(taxonomy_diff) == {"name"} and len(str(draft.get("name") or "")) > len(str(prod.get("name") or "")):
            return "update_from_draft", "Cosmetic name refresh only; block unchanged.", ["name"], True
        return (
            "keep_production",
            f"Production RC-ready; draft changes are X-Ray tags only ({sorted(taxonomy_diff)}).",
            [],
            ticker in PRIORITY_TICKERS,
        )

    return "manual_review", "Unresolved taxonomy difference.", [], True


def _priority_score(ticker: str, action: str, prod_ready: dict[str, Any], draft_ready: dict[str, Any], diff: dict[str, list[Any]]) -> tuple:
    block_changed = prod_ready["stress_block"] != draft_ready["stress_block"]
    core_diff = any(k in BLOCK_PRIORITY for k in diff)
    action_rank = {"manual_review": 0, "update_from_draft": 1, "keep_production": 2, "skip": 3}[action]
    priority_ticker = 0 if ticker in PRIORITY_TICKERS else 1
    return (priority_ticker, action_rank, 0 if block_changed else 1, 0 if core_diff else 1, ticker)


def analyze_conflicts(
    *,
    ingestion_dir: Path,
    etf_universe: Path,
    stock_universe: Path,
) -> dict[str, Any]:
    needs_path = ingestion_dir / "needs_review.csv"
    needs_review = load_needs_review_tickers(needs_path)

    plan, meta = build_merge_plan(
        draft_etf_path=ingestion_dir / "draft_etf_universe.yml",
        draft_stock_path=ingestion_dir / "draft_stock_universe.yml",
        needs_review_path=needs_path if needs_path.is_file() else None,
        production_etf_path=etf_universe,
        production_stock_path=stock_universe,
        include_stocks=False,
    )

    prod_by = {_upper(r["ticker"]): r for r in load_etf_universe(etf_universe) if r.get("ticker")}
    draft_by = {_upper(r["ticker"]): r for r in load_draft_universe_yaml(ingestion_dir / "draft_etf_universe.yml")}

    rows: list[dict[str, Any]] = []
    for conflict in plan.etf_conflicts:
        ticker = _upper(conflict["ticker"])
        prod = prod_by[ticker]
        draft = draft_by[ticker]
        diff = _field_diff(prod, draft)
        prod_ready = _readiness(prod, universe_source="etf_universe")
        draft_ready = _readiness(draft, universe_source="etf_universe")
        draft_flags = _draft_quality_flags(str(draft.get("name") or ""), draft)
        action, reason, safe_updates, manual_review_required = _recommend(
            ticker=ticker,
            prod=prod,
            draft=draft,
            diff=diff,
            prod_ready=prod_ready,
            draft_ready=draft_ready,
            draft_flags=draft_flags,
            in_needs_review=ticker in needs_review,
        )
        rows.append(
            {
                "ticker": ticker,
                "priority": ticker in PRIORITY_TICKERS,
                "production_fields": _taxonomy_slice(prod),
                "draft_fields": _taxonomy_slice(draft),
                "field_differences": diff,
                "taxonomy_field_differences": {k: v for k, v in diff.items() if k in TAXONOMY_FIELDS},
                "core_field_differences": _core_taxonomy_diff({k: v for k, v in diff.items() if k in TAXONOMY_FIELDS}),
                "recommended_action": action,
                "manual_review_required": manual_review_required,
                "reason": reason,
                "safe_field_updates": safe_updates,
                "production_readiness": prod_ready,
                "draft_readiness": draft_ready,
                "stress_block_impact": {
                    "production_block": prod_ready["stress_block"],
                    "draft_block": draft_ready["stress_block"],
                    "block_changed": prod_ready["stress_block"] != draft_ready["stress_block"],
                },
                "rc_xray_impact": {
                    "production_rc_ready": prod_ready["rc_ready"],
                    "draft_rc_ready": draft_ready["rc_ready"],
                    "production_xray_ready": prod_ready["xray_ready"],
                    "draft_xray_ready": draft_ready["xray_ready"],
                    "production_needs_review": prod_ready["needs_review"],
                    "draft_needs_review": draft_ready["needs_review"],
                    "production_silent_default_eq": prod_ready["silent_default_eq"],
                    "draft_silent_default_eq": draft_ready["silent_default_eq"],
                },
                "draft_quality_flags": draft_flags,
            }
        )

    rows.sort(key=lambda r: _priority_score(
        r["ticker"], r["recommended_action"], r["production_readiness"], r["draft_readiness"], r["field_differences"]
    ))

    action_counts = Counter(r["recommended_action"] for r in rows)
    safe_updates = [r for r in rows if r["recommended_action"] == "update_from_draft"]
    manual = [r for r in rows if r["recommended_action"] == "manual_review"]
    manual_queue = [r for r in rows if r.get("manual_review_required")]
    priority = [r for r in rows if r["priority"] or r["stress_block_impact"]["block_changed"]]

    return {
        "version": "universe_conflict_resolution_plan_v1",
        "summary": {
            "conflict_count": len(rows),
            "action_counts": dict(action_counts),
            "priority_conflict_count": sum(1 for r in rows if r["priority"]),
            "block_change_count": sum(1 for r in rows if r["stress_block_impact"]["block_changed"]),
            "safe_update_count": len(safe_updates),
            "manual_review_action_count": len(manual),
            "manual_review_queue_count": len(manual_queue),
            "production_etf_count": meta.get("production_etf_count"),
        },
        "priority_review_list": [
            {
                "ticker": r["ticker"],
                "action": r["recommended_action"],
                "reason": r["reason"],
                "production_block": r["stress_block_impact"]["production_block"],
                "draft_block": r["stress_block_impact"]["draft_block"],
                "taxonomy_diff_keys": sorted(r["taxonomy_field_differences"]),
            }
            for r in priority[:40]
        ],
        "safe_update_plan": [
            {
                "ticker": r["ticker"],
                "fields": r["safe_field_updates"],
                "reason": r["reason"],
                "production_block": r["stress_block_impact"]["production_block"],
            }
            for r in safe_updates
        ],
        "manual_review_list": [
            {
                "ticker": r["ticker"],
                "recommended_action": r["recommended_action"],
                "reason": r["reason"],
                "production_block": r["stress_block_impact"]["production_block"],
                "draft_block": r["stress_block_impact"]["draft_block"],
                "block_changed": r["stress_block_impact"]["block_changed"],
                "taxonomy_diff_keys": sorted(r["taxonomy_field_differences"]),
                "core_diff_keys": sorted(r["core_field_differences"]),
            }
            for r in manual_queue
        ],
        "conflicts": rows,
    }


def _format_text(report: dict[str, Any]) -> str:
    s = report["summary"]
    lines = [
        "Universe conflict resolution plan (read-only)",
        "",
        f"Conflicts: {s['conflict_count']}",
        f"Priority tickers in conflict set: {s['priority_conflict_count']}",
        f"Block changes: {s['block_change_count']}",
        f"Safe high-confidence updates: {s['safe_update_count']}",
        f"Manual review queue: {s.get('manual_review_queue_count', 0)}",
        f"Manual review action: {s.get('manual_review_action_count', 0)}",
        "",
        "Action summary:",
    ]
    for action, count in sorted((s.get("action_counts") or {}).items()):
        lines.append(f"  {action}: {count}")
    lines.extend(["", "Priority review (top 25):"])
    for item in report.get("priority_review_list", [])[:25]:
        lines.append(
            f"  {item['ticker']:6} {item['action']:18} prod={item['production_block']} draft={item['draft_block']} "
            f"diff={item['taxonomy_diff_keys']}"
        )
    lines.extend(["", "Safe update plan:"])
    safe = report.get("safe_update_plan") or []
    if not safe:
        lines.append("  (none — do not apply field updates without manual sign-off)")
    for item in safe[:30]:
        lines.append(f"  {item['ticker']:6} fields={item['fields']} block={item['production_block']} — {item['reason']}")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Analyze ETF production vs draft conflicts")
    p.add_argument("--ingestion-dir", default="output/universe_ingestion_live")
    p.add_argument("--etf-universe", default="config/etf_universe.yml")
    p.add_argument("--stock-universe", default="config/stock_universe.yml")
    p.add_argument("--format", choices=("json", "text"), default="text")
    p.add_argument("--out", default=None, help="Write JSON plan path")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    ingestion_dir = Path(args.ingestion_dir)
    report = analyze_conflicts(
        ingestion_dir=ingestion_dir,
        etf_universe=Path(args.etf_universe),
        stock_universe=Path(args.stock_universe),
    )
    out_path = Path(args.out) if args.out else ingestion_dir / "conflict_resolution_plan.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(_format_text(report), end="")
        print(f"Full plan: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
