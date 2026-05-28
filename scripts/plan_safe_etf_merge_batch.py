"""Analyze live ingestion and propose safe ETF merge batch."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
ING = ROOT / "output" / "universe_ingestion_live"

from src.etf_universe import load_etf_universe
from src.universe_ingestion import _detect_hybrid_flags, classify_etf
from src.universe_merge import build_merge_plan, load_draft_universe_yaml, merge_plan_to_report
from src.taxonomy_stress_blocks import derive_stress_block_from_taxonomy_row, assess_classification

BLOCKED_NAME_FRAGMENTS = (
    "asset allocation",
    "multi-asset",
    "multi asset",
    "enhanced income",
    "weeklypay",
    "option income",
    "buywrite",
    "covered call",
    " 2x",
    " 3x",
    "ultrapro",
    "inverse",
    "bitcoin",
    "crypto",
    " vix",
    "volatility",
    "plus gold",
    "plus equity",
    "defined protection",
        "digital asset",
        "crypto",
        " max buffer",
        "buffer dec",
        "buffer etf",
    "bear 1x",
    "bear 2x",
    "bull 2x",
    "bull 3x",
    "cash cows",  # equity factor ETFs misclassified as cash
    "k-1 free",
    " k-1",
)


def _name_blocked(name: str) -> str | None:
    nl = name.lower()
    for frag in BLOCKED_NAME_FRAGMENTS:
        if frag in nl:
            return frag.strip()
    # Goldman Sachs *bond/equity* misclassified as gold commodity
    if "goldman" in nl and not any(
        k in nl for k in ("physical gold", "gold trust", "gold shares", "spdr gold", "gold etf", "gold fund")
    ):
        if any(k in nl for k in ("treasury", "bond", "aggregate", "equity", "municipal", "emerging", "international")):
            return "goldman_not_gold"
    return None


# Curated batch 1 — manually verified plain-vanilla sleeves (one per stress block where possible)
CURATED_BATCH_1 = [
    "BILS",  # CA t-bill
    "VBIL",  # CA t-bill
    "BBIB",  # ND treasury 3-10Y
    "IBIG",  # TI iBonds TIPS 2030
    "AHYB",  # CR high yield
    "PHYS",  # CO physical gold
    "AAUS",  # EQ broad US
    "GOVM",  # ND treasury 1-10Y (second duration sleeve; still plain treasury)
]
BLOCKED_HYBRID = frozenset(
    {
        "leveraged",
        "inverse",
        "crypto",
        "volatility",
        "covered_call",
        "option_income",
        "multi_asset",
        "managed_futures",
        "private_credit",
        "clo",
        "mortgage_reit",
        "preferred_share",
        "convertible",
    }
)
BLOCKED_SUBTYPES = frozenset(
    {
        "multi_asset",
        "covered_call",
        "managed_futures",
        "volatility_etf",
        "tail_risk",
        "preferred",
        "bitcoin_spot",
        "ether_spot",
    }
)
MEDIUM_RISK_SUBTYPES = frozenset({"aggregate_bond", "reit", "corporate_ig"})

# Plain-vanilla subtypes preferred for batch 2 scale-up
PREFERRED_SUBTYPES = frozenset(
    {
        "broad_market",
        "t_bill",
        "treasury",
        "tips",
        "high_yield",
        "gold",
        "sector_etf",
        "regional_etf",
        "country_etf",
        "dividend",
        "growth",
        "value",
        "small_cap",
        "large_cap",
        "mid_cap",
        "commodity_etf",
        "energy_commodity",
        "floating_rate",
        "bank_loan",
        "em_debt",
    }
)

# Stress-block quotas for scale-up batches
BATCH2_BLOCK_QUOTAS: dict[str, int] = {
    "EQ": 35,
    "ND": 12,
    "CA": 8,
    "CR": 10,
    "TI": 8,
    "CO": 7,
}
BATCH3_BLOCK_QUOTAS: dict[str, int] = {
    "EQ": 130,
    "ND": 45,
    "CA": 20,
    "CR": 45,
    "TI": 30,
    "CO": 30,
}

BATCH4_BLOCK_QUOTAS: dict[str, int] = {
    "EQ": 215,
    "ND": 75,
    "CA": 25,
    "CR": 75,
    "TI": 50,
    "CO": 60,
}

CURATED_BATCH_1_TICKERS = frozenset(CURATED_BATCH_1)
VALID_STRESS_BLOCKS = frozenset({"EQ", "ND", "CA", "CR", "TI", "CO"})


def _scale_batch_extra_blocked(name: str, entry: dict) -> str | None:
    """Stricter plain-vanilla rules for scale-up batches (2+)."""
    nl = name.lower()
    block = str(entry.get("stress_block") or "")
    subtype = str(entry.get("subtype") or "").lower()

    structured_markers = (
        "autocallable",
        "collared",
        "premium strategy",
        "yield premium",
        "enhanced yield",
        "income strategy",
        "distribution etf",
        "drawdown managed",
        "acktivist",
        "weeklypay",
        "monthly pay",
        "double long",
        "double short",
        " etn",
        "etn due",
        "stocks, bonds",
        "bonds & gold",
        "bond & gold",
        "flexible bond",
        "hypergrowth",
        "single-stock",
        "single stock",
        " allocation",
        "all weather",
        "80/20",
        "60/40",
        "40/60",
        "50/50",
        "infrastructure active",
        "infrastructure etf",
        "income etf",
        "target income",
        "flexible income",
        "high income etf",
        "high yield and income",
        "option income",
        " options ",
        "ft vest",
        "10% target",
        "target income",
        "buy-write",
        "buywrite",
        "enhanced high yield",
        "enhanced fallen",
        "blackstone high income",
        " buffer",
        "premium yield",
        "etracs",
    )
    if any(m in nl for m in structured_markers):
        return "income_structured"
    if (
        " active " in nl
        or nl.endswith(" active etf")
        or " active exchange-traded" in nl
        or "activebuilders" in nl
        or "activepassive" in nl
    ):
        return "active_non_plain"
    if block == "EQ" and "enhanced" in nl:
        return "enhanced_non_plain"

    if block == "CA" and subtype != "t_bill":
        return "ca_non_tbill"
    if block == "CA" and not any(k in nl for k in ("t-bill", "t bill", "treasury bill", "treasury bills")):
        return "ca_not_plain_tbill"
    if block == "CA" and "weekly" in nl:
        return "ca_weekly_structured"

    if block == "CO":
        if any(k in nl for k in ("miner", "miners", "exploration", "explorers", "producers")):
            return "commodity_miners"
        if "goldman" in nl or "golden dragon" in nl or "golden eagle" in nl:
            return "goldman_or_misclassified_gold"
        if subtype == "gold" and not any(
            k in nl for k in ("physical gold", "gold trust", "gold shares", "spdr gold", "gold fund", "gold etf", "merk gold")
        ):
            return "co_not_physical_gold"
        if subtype not in ("gold", "commodity_etf", "silver", "energy_commodity"):
            return "co_non_plain"

    if any(k in nl for k in ("alternative asset", "tactical", "dynamic hyper", "hedge industry")):
        return "non_plain_strategy"

    ac = str(entry.get("asset_class") or "").lower()
    fi_name_markers = (
        " bond",
        "bond etf",
        "municipal",
        "agency bond",
        " treasury",
        "treasury bond",
        " high yield",
        "floating rate",
        "bulletshares",
        " green bond",
        "core-plus bond",
        "total world bond",
        "international bond",
        "fixed income",
        "energy fund",
        " db energy",
    )
    if ac == "equity" and any(m in nl for m in fi_name_markers):
        return "misclassified_fi_as_equity"
    if block == "CO" and any(k in nl for k in ("equipment & services", "oil equipment", "exploration & production", "oil & gas services", "gas services")):
        return "equity_sector_misclassified_as_co"

    if subtype not in PREFERRED_SUBTYPES:
        return f"non_preferred_subtype:{subtype}"
    return None


def _scale_batch_quality_score(entry: dict) -> tuple:
    """Lower is better. Prefer major issuers and plain names."""
    name = str(entry.get("name") or "").lower()
    issuer_hints = ("ishares", "vanguard", "spdr", "state street", "jpmorgan", "schwab", "invesco", "franklin")
    major = 0 if any(h in name for h in issuer_hints) else 1
    suspicious = 1 if any(k in name for k in ("factor", "adaptive", "innovator", "aptus", "alpha architect", "abacus")) else 0
    subtype = str(entry.get("subtype") or "")
    core = 0 if subtype in ("broad_market", "treasury", "tips", "gold", "t_bill", "high_yield") else 1
    return (suspicious, core, major, entry.get("ticker", ""))


def select_scale_batch(
    safe: list[dict],
    *,
    target_size: int,
    block_quotas: dict[str, int],
    exclude_tickers: frozenset[str] | None = None,
) -> tuple[list[dict], list[dict]]:
    """Pick a scale-up batch with block quotas from remaining safe pool."""
    exclude = exclude_tickers or frozenset()
    candidates: list[dict] = []
    rejected: list[dict] = []
    for e in safe:
        if e["ticker"] in exclude:
            rejected.append({"ticker": e["ticker"], "reasons": ["prior_batch_merged"]})
            continue
        block = str(e.get("stress_block") or "")
        if block not in VALID_STRESS_BLOCKS:
            rejected.append({"ticker": e["ticker"], "reasons": [f"invalid_stress_block:{block or 'missing'}"]})
            continue
        reason = _scale_batch_extra_blocked(str(e.get("name") or ""), e)
        if reason:
            rejected.append({"ticker": e["ticker"], "reasons": [reason]})
            continue
        candidates.append(e)

    by_block: dict[str, list[dict]] = {b: [] for b in block_quotas}
    for e in candidates:
        b = str(e.get("stress_block") or "EQ")
        if b in by_block:
            by_block[b].append(e)
    for block in by_block:
        by_block[block].sort(key=_scale_batch_quality_score)

    selected: list[dict] = []
    selected_set: set[str] = set()
    for block, quota in block_quotas.items():
        for e in by_block.get(block, [])[:quota]:
            if e["ticker"] not in selected_set:
                selected.append(e)
                selected_set.add(e["ticker"])

    if len(selected) < target_size:
        fill_order = sorted(block_quotas.keys(), key=lambda b: (-block_quotas[b], b))
        for block in fill_order:
            for e in by_block.get(block, []):
                if e["ticker"] in selected_set:
                    continue
                selected.append(e)
                selected_set.add(e["ticker"])
                if len(selected) >= target_size:
                    break
            if len(selected) >= target_size:
                break

    return selected[:target_size], rejected


def _load_prior_batch_tickers(ing: Path, *, skip_tickers_file: str | None = None) -> frozenset[str]:
    tickers: set[str] = set(CURATED_BATCH_1_TICKERS)
    for fname in ("batch2_tickers.txt", "batch3_tickers.txt", "batch4_tickers.txt"):
        if skip_tickers_file and fname == skip_tickers_file:
            continue
        path = ing / fname
        if path.is_file():
            tickers.update(t.strip().upper() for t in path.read_text(encoding="utf-8").split(",") if t.strip())
    return frozenset(tickers)


SCALE_BATCH_SPECS: dict[int, dict[str, object]] = {
    2: {
        "target_size": lambda n: max(50, min(100, n)),
        "quotas": BATCH2_BLOCK_QUOTAS,
        "tickers_file": "batch2_tickers.txt",
        "plan_file": "safe_merge_batch2_plan.json",
        "out_prefix": "batch_2",
    },
    3: {
        "target_size": lambda n: max(50, n),
        "quotas": BATCH3_BLOCK_QUOTAS,
        "tickers_file": "batch3_tickers.txt",
        "plan_file": "safe_merge_batch3_plan.json",
        "out_prefix": "batch_3",
    },
    4: {
        "target_size": lambda n: max(50, n),
        "quotas": BATCH4_BLOCK_QUOTAS,
        "tickers_file": "batch4_tickers.txt",
        "plan_file": "safe_merge_batch4_plan.json",
        "out_prefix": "batch_4",
    },
}


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Plan safe ETF merge batches")
    p.add_argument("--batch", type=int, default=1, choices=(1, 2, 3, 4))
    p.add_argument("--target-size", type=int, default=80, help="Batch 2/3/4 target size")
    p.add_argument("--ingestion-dir", default=str(ING))
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    ing = Path(args.ingestion_dir)
    draft_path = ing / "draft_etf_universe.yml"
    needs_path = ing / "needs_review.csv"
    report_path = ing / "ingestion_report.json"

    draft = load_draft_universe_yaml(draft_path)
    prod = {_upper(r["ticker"]): r for r in load_etf_universe(ROOT / "config" / "etf_universe.yml") if r.get("ticker")}

    needs_review = set()
    if needs_path.is_file():
        ndf = pd.read_csv(needs_path)
        needs_review = {str(t).strip().upper() for t in ndf["ticker"] if str(t).strip()}

    readiness_by_ticker: dict[str, dict] = {}
    if report_path.is_file():
        rep = json.loads(report_path.read_text(encoding="utf-8"))
        for row in rep.get("readiness") or []:
            t = str(row.get("ticker") or "").upper()
            if t:
                readiness_by_ticker[t] = row

    plan, meta = build_merge_plan(
        draft_etf_path=draft_path,
        draft_stock_path=ING / "draft_stock_universe.yml",
        needs_review_path=needs_path,
        production_etf_path=ROOT / "config" / "etf_universe.yml",
        production_stock_path=ROOT / "config" / "stock_universe.yml",
        include_needs_review=False,
    )
    conflict_tickers = {c["ticker"] for c in plan.etf_conflicts}
    conflict_map = {c["ticker"]: c for c in plan.etf_conflicts}

    skipped: list[dict] = []
    safe: list[dict] = []

    for row in draft:
        t = str(row.get("ticker") or "").upper()
        if not t:
            continue
        name = str(row.get("name") or "")
        reasons: list[str] = []

        if t in prod:
            reasons.append("already_in_production")
        if t in needs_review:
            reasons.append("needs_review_csv")
        if t in conflict_tickers:
            reasons.append("production_conflict")
        nb = _name_blocked(name)
        if nb:
            reasons.append(f"name_blocked:{nb}")
        hybrid = _detect_hybrid_flags(name)
        blocked = [h for h in hybrid if h in BLOCKED_HYBRID]
        if blocked:
            reasons.append(f"hybrid:{','.join(blocked)}")
        subtype = str(row.get("subtype") or "").lower()
        if subtype in BLOCKED_SUBTYPES:
            reasons.append(f"blocked_subtype:{subtype}")
        if subtype in MEDIUM_RISK_SUBTYPES:
            reasons.append(f"medium_risk_subtype:{subtype}")
        if str(row.get("asset_class") or "").lower() == "alternative":
            reasons.append("alternative_asset_class")
        if str(row.get("asset_class") or "").lower() == "crypto":
            reasons.append("crypto_asset_class")

        rd = readiness_by_ticker.get(t, {})
        if rd.get("needs_review"):
            reasons.append("readiness_needs_review")
        if rd.get("classification_confidence") != "high":
            if rd:
                reasons.append(f"confidence:{rd.get('classification_confidence')}")
            else:
                # recompute
                clf = classify_etf(name, etf_flag=True)
                if clf.classification_confidence != "high":
                    reasons.append(f"confidence:{clf.classification_confidence}")
                if clf.needs_review:
                    reasons.append("classifier_needs_review")
        if rd and not rd.get("rc_ready"):
            reasons.append("rc_not_ready")
        if rd and rd.get("silent_default_eq"):
            reasons.append("silent_default_eq")

        resolution = derive_stress_block_from_taxonomy_row(row, universe_source="etf_universe")
        _, assess_needs, assess_warn = assess_classification(
            row=row,
            universe_source="etf_universe",
            resolution=resolution,
            taxonomy_summary={k: row.get(k) for k in ("asset_class", "subtype", "main_risk_factor", "credit_quality")},
        )
        if assess_needs:
            reasons.append("assess_needs_review")
        if any("expected" in str(w).lower() for w in assess_warn):
            reasons.append("block_mismatch_warning")

        entry = {
            "ticker": t,
            "name": name[:60],
            "stress_block": resolution.block,
            "asset_class": row.get("asset_class"),
            "subtype": row.get("subtype"),
            "main_risk_factor": row.get("main_risk_factor"),
        }
        if reasons:
            skipped.append({"ticker": t, "reasons": reasons})
        else:
            safe.append(entry)

    # Prioritize: core blocks, broad_market/treasury/tips/gold first
    def priority(e: dict) -> tuple:
        subtype = str(e.get("subtype") or "")
        block = str(e.get("stress_block") or "")
        core_sub = subtype in ("broad_market", "treasury", "tips", "gold", "t_bill", "high_yield", "corporate_ig")
        return (0 if core_sub else 1, block, e["ticker"])

    safe.sort(key=priority)

    safe_by_ticker = {e["ticker"]: e for e in safe}
    batch1 = [safe_by_ticker[t] for t in CURATED_BATCH_1 if t in safe_by_ticker]
    batch1_rejected = [
        {"ticker": t, "reasons": next((s["reasons"] for s in skipped if s["ticker"] == t), ["not_in_safe_pool"])}
        for t in CURATED_BATCH_1
        if t not in safe_by_ticker
    ]

    skip_reason_counts = Counter()
    for s in skipped:
        for r in s["reasons"]:
            skip_reason_counts[r.split(":")[0]] += 1

    scale_batch: list[dict] = []
    scale_rejected: list[dict] = []
    scale_reason_counts: Counter = Counter()
    scale_block_quotas: dict[str, int] = {}
    scale_target = 0
    tickers_filename = ""
    plan_filename = ""
    batch_prefix = ""

    spec = SCALE_BATCH_SPECS.get(args.batch)
    if spec:
        scale_target = spec["target_size"](args.target_size)  # type: ignore[operator]
        scale_block_quotas = dict(spec["quotas"])  # type: ignore[arg-type]
        tickers_filename = str(spec["tickers_file"])
        plan_filename = str(spec["plan_file"])
        batch_prefix = str(spec["out_prefix"])
        prior_batches = _load_prior_batch_tickers(ing, skip_tickers_file=tickers_filename)
        scale_batch, scale_rejected = select_scale_batch(
            safe,
            target_size=scale_target,
            block_quotas=scale_block_quotas,
            exclude_tickers=prior_batches,
        )
        for r in scale_rejected:
            for reason in r["reasons"]:
                scale_reason_counts[reason.split(":")[0]] += 1
        tickers_path = ing / tickers_filename
        tickers_path.write_text(",".join(e["ticker"] for e in scale_batch), encoding="utf-8")

    block_dist = Counter(e["stress_block"] for e in scale_batch)

    out: dict[str, object] = {
        "production_etf_count": len(prod),
        "draft_etf_count": len(draft),
        "safe_count": len(safe),
        "skipped_count": len(skipped),
        "needs_review_count": len(needs_review),
        "conflict_count": len(conflict_tickers),
        "skip_reason_summary": skip_reason_counts.most_common(25),
        "recommended_batch_1": batch1,
        "recommended_batch_1_tickers": [e["ticker"] for e in batch1],
        "batch_1_rejected": batch1_rejected,
        "conflict_tickers_sample": sorted(conflict_tickers)[:30],
    }
    if batch_prefix:
        out[f"recommended_{batch_prefix}"] = scale_batch
        out[f"recommended_{batch_prefix}_tickers"] = [e["ticker"] for e in scale_batch]
        out[f"{batch_prefix}_count"] = len(scale_batch)
        out[f"{batch_prefix}_target_size"] = scale_target
        out[f"{batch_prefix}_stress_block_distribution"] = dict(sorted(block_dist.items()))
        out[f"{batch_prefix}_block_quotas"] = scale_block_quotas
        out[f"{batch_prefix}_rejected_count"] = len(scale_rejected)
        out[f"{batch_prefix}_rejected_reason_summary"] = scale_reason_counts.most_common(20)
        out[f"{batch_prefix}_rejected_sample"] = scale_rejected[:50]

    out_path = ing / (plan_filename if plan_filename else "safe_merge_batch_plan.json")
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps({
        "batch": args.batch,
        "target_size": scale_target if spec else len(batch1),
        "selected_count": len(scale_batch) if spec else len(batch1),
        "stress_block_distribution": dict(sorted(block_dist.items())) if spec else {},
        "production_etf_count": len(prod),
        "safe_count": len(safe),
        "batch_rejected_count": len(scale_rejected) if spec else 0,
        "tickers_file": str(ing / tickers_filename) if tickers_filename else "",
        "plan_file": str(out_path),
    }, indent=2, ensure_ascii=False))


def _upper(x: str) -> str:
    return str(x or "").strip().upper()


if __name__ == "__main__":
    main()
