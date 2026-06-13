"""
Controlled Stock Batch 1 pipeline: index-based US equity expansion (draft only).

Never writes production config/stock_universe.yml. See docs/specs/universe_ingestion_spec.md.
"""
from __future__ import annotations

import io
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Literal

import pandas as pd
import yaml

from src.stock_universe import (
    INDEX_MEMBERSHIP_VALUES,
    load_stock_universe,
    validate_stock_universe,
)
from src.universe_ingestion import (
    _clean_reason,
    _upper_ticker,
    enrich_draft_stocks,
    enrich_stock_sector_yahoo,
    fetch_source,
    load_production_stock_sector_lookup,
)
from src.universe_merge import MergePlan, _row_diff, build_merge_plan, load_draft_universe_yaml

IndexTag = Literal["SP500", "R1000", "R3000"]
INDEX_PRIORITY: tuple[IndexTag, ...] = ("SP500", "R1000", "R3000")
MAX_BATCH1_SIZE = 1000
MAX_BATCH2_SIZE = 700
MIN_BATCH2_ACCEPTED = 500

DEFAULT_SP500_WIKIPEDIA_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
DEFAULT_ISHARES_IWB_HOLDINGS_URL = (
    "https://www.ishares.com/us/products/239710/ishares-russell-1000-etf/"
    "1467271812596.ajax...fileType=csv&fileName=IWB_holdings&dataType=fund"
)
DEFAULT_ISHARES_IWV_HOLDINGS_URL = (
    "https://www.ishares.com/us/products/239714/ishares-russell-3000-etf/"
    "1467271812596.ajax...fileType=csv&fileName=IWV_holdings&dataType=fund"
)
DEFAULT_BATCH_USER_AGENT = "PortfolioMRI/1.0 (research; stock-batch-ingestion@local)"
DEFAULT_R3000_GITHUB_URL = (
    "https://raw.githubusercontent.com/yya518/peer-firms/main/russell3000_ticker_GIC.csv"
)

# GICS sector code (peer-firms gsector column) → sector label
_GSECTOR_TO_GICS: dict[str, str] = {
    "10": "Energy",
    "15": "Materials",
    "20": "Industrials",
    "25": "Consumer Discretionary",
    "30": "Consumer Staples",
    "35": "Health Care",
    "40": "Financials",
    "45": "Information Technology",
    "50": "Communication Services",
    "55": "Utilities",
    "60": "Real Estate",
}

_ADR_NAME = re.compile(
    r"\b(adr|american depositary|depositary share|sponsored adr|unsponsored adr)\b",
    re.IGNORECASE,
)
_SPAC_NAME = re.compile(r"\b(spac|acquisition corp|blank check)\b", re.IGNORECASE)
_FUND_NAME = re.compile(
    r"\b(etf|etn|mutual fund|fund shares|closed[- ]end|trust shares)\b",
    re.IGNORECASE,
)
_CLASS_SHARE_DASH = re.compile(r"^([A-Z]{1,5})-([A-Z])$")


@dataclass
class IndexMember:
    ticker: str
    name: str
    sector: str = ""
    industry: str = ""
    index_tags: set[str] = field(default_factory=set)
    market_cap_usd: float | None = None
    source: str = ""


@dataclass
class StockBatch1Result:
    draft_rows: list[dict[str, Any]]
    accepted: list[dict[str, Any]]
    rejected: list[dict[str, Any]]
    needs_review: list[dict[str, Any]]
    review_report: dict[str, Any]
    merge_ready: bool


def normalize_equity_ticker(symbol: str) -> str:
    """Normalize index/vendor symbols to Nasdaq-style tickers (e.g. BRK-B -> BRK.B)."""
    s = str(symbol or "").strip().upper()
    if not s:
        return ""
    m = _CLASS_SHARE_DASH.match(s)
    if m:
        return f"{m.group(1)}.{m.group(2)}"
    return s.replace(" ", "")


def primary_index_tag(tags: set[str]) -> list[str]:
    for tag in INDEX_PRIORITY:
        if tag in tags:
            return [tag]
    return []


def fetch_sp500_wikipedia(url: str = DEFAULT_SP500_WIKIPEDIA_URL) -> list[IndexMember]:
    """Load S&P 500 constituents from Wikipedia (GICS sector/industry)."""
    html = fetch_source(url, user_agent=DEFAULT_BATCH_USER_AGENT)
    tables = pd.read_html(io.StringIO(html))
    if not tables:
        raise ValueError("No tables found on S&P 500 Wikipedia page")
    df = tables[0]
    sym_col = "Symbol" if "Symbol" in df.columns else df.columns[0]
    name_col = "Security" if "Security" in df.columns else None
    sector_col = "GICS Sector" if "GICS Sector" in df.columns else None
    industry_col = "GICS Sub-Industry" if "GICS Sub-Industry" in df.columns else None
    out: list[IndexMember] = []
    for _, row in df.iterrows():
        ticker = normalize_equity_ticker(str(row[sym_col]))
        if not ticker:
            continue
        out.append(
            IndexMember(
                ticker=ticker,
                name=str(row[name_col]).strip() if name_col else ticker,
                sector=str(row[sector_col]).strip() if sector_col and pd.notna(row[sector_col]) else "",
                industry=str(row[industry_col]).strip() if industry_col and pd.notna(row[industry_col]) else "",
                index_tags={"SP500"},
                source="wikipedia_sp500",
            )
        )
    return out


def parse_peer_firms_r3000_csv(text: str) -> list[IndexMember]:
    """Parse yya518/peer-firms russell3000_ticker_GIC.csv (Symbol, Description, gsector)."""
    df = pd.read_csv(io.StringIO(text))
    cols = {c.lower().strip(): c for c in df.columns}
    sym = cols.get("symbol") or cols.get("ticker")
    name = cols.get("description") or cols.get("name")
    gsec = cols.get("gsector") or cols.get("sector")
    if not sym:
        raise ValueError("Russell 3000 GitHub CSV missing Symbol column")
    out: list[IndexMember] = []
    for _, row in df.iterrows():
        ticker = normalize_equity_ticker(str(row[sym]))
        if not ticker:
            continue
        sector = ""
        if gsec and pd.notna(row.get(gsec)):
            try:
                code = str(int(float(row[gsec])))
            except (TypeError, ValueError):
                code = str(row[gsec]).strip().split(".")[0]
            sector = _GSECTOR_TO_GICS.get(code, "")
        out.append(
            IndexMember(
                ticker=ticker,
                name=str(row[name]).strip() if name and pd.notna(row.get(name)) else ticker,
                sector=sector,
                industry="",
                index_tags={"R3000"},
                source="github_peer_firms_r3000",
            )
        )
    return out


def fetch_ishares_holdings(url: str, *, index_tag: IndexTag) -> list[IndexMember] | None:
    """Return holdings or None when iShares serves HTML / invalid CSV."""
    text = fetch_source(url, user_agent=DEFAULT_BATCH_USER_AGENT)
    if text.lstrip().startswith("<"):
        return None
    try:
        return parse_ishares_holdings_csv(text, index_tag=index_tag)
    except ValueError:
        return None


def fetch_market_caps_yahoo(tickers: list[str], *, chunk_size: int = 80) -> dict[str, float]:
    """Best-effort market cap (USD) for ranking Russell 1000 within R3000."""
    try:
        import yfinance as yf
    except ImportError:
        return {t: 0.0 for t in tickers}
    caps: dict[str, float] = {}
    unique = sorted({t for t in tickers if t})
    import time

    for i in range(0, len(unique), chunk_size):
        batch = unique[i : i + chunk_size]
        if i > 0:
            time.sleep(2.0)
        try:
            bundle = yf.Tickers(" ".join(batch))
        except Exception:
            for t in batch:
                caps[t] = 0.0
            continue
        for t in batch:
            try:
                cap = bundle.tickers[t].fast_info.get("marketCap") or 0.0
            except Exception:
                cap = 0.0
            caps[t] = float(cap) if cap else 0.0
    return caps


def apply_r1000_tags_by_market_cap(by_ticker: dict[str, IndexMember], *, top_n: int = 1000) -> int:
    """Tag top-N by market cap with R1000 (when official R1000 file unavailable).

    S&P 500 ⊆ Russell 1000: all SP500 names receive R1000. Remaining R1000 slots are
    filled from Russell 3000 \\ SP500 by market cap (Yahoo), capped to ~700 API calls.
    """
    for member in by_ticker.values():
        if "SP500" in member.index_tags:
            member.index_tags.add("R1000")
    non_sp500 = [
        t
        for t, m in by_ticker.items()
        if "SP500" not in m.index_tags and "R3000" in m.index_tags
    ]
    caps = fetch_market_caps_yahoo(non_sp500[:700])
    for ticker, cap in caps.items():
        if ticker in by_ticker:
            by_ticker[ticker].market_cap_usd = cap or by_ticker[ticker].market_cap_usd
    ranked = sorted(non_sp500, key=lambda t: caps.get(t, 0.0), reverse=True)
    slots = max(0, top_n - sum(1 for m in by_ticker.values() if "R1000" in m.index_tags))
    for ticker in ranked[:slots]:
        by_ticker[ticker].index_tags.add("R1000")
    return sum(1 for m in by_ticker.values() if "R1000" in m.index_tags)


def parse_ishares_holdings_csv(text: str, *, index_tag: IndexTag) -> list[IndexMember]:
    """Parse iShares ETF holdings CSV (Russell 1000 / 3000 proxies)."""
    lines = text.splitlines()
    start = 0
    for i, ln in enumerate(lines):
        if ln.strip().startswith("Ticker") or ln.strip().lower().startswith("ticker,"):
            start = i
            break
    df = pd.read_csv(io.StringIO("\n".join(lines[start:])), on_bad_lines="skip")
    cols = {c.lower().strip(): c for c in df.columns}
    ticker_col = cols.get("ticker") or cols.get("symbol")
    name_col = cols.get("name") or cols.get("issuer")
    sector_col = cols.get("sector")
    industry_col = cols.get("industry") or cols.get("asset class")
    mcap_col = cols.get("market value") or cols.get("market cap") or cols.get("market_value")
    if not ticker_col:
        raise ValueError("Holdings CSV missing Ticker column")
    out: list[IndexMember] = []
    for _, row in df.iterrows():
        raw = str(row[ticker_col]).strip()
        if not raw or raw in ("-", "—", "Cash", "USD", "nan"):
            continue
        ticker = normalize_equity_ticker(raw)
        if not ticker or len(ticker) > 8:
            continue
        mcap: float | None = None
        if mcap_col and pd.notna(row.get(mcap_col)):
            try:
                mcap = float(str(row[mcap_col]).replace(",", "").replace("$", ""))
            except ValueError:
                mcap = None
        out.append(
            IndexMember(
                ticker=ticker,
                name=str(row[name_col]).strip() if name_col and pd.notna(row.get(name_col)) else ticker,
                sector=str(row[sector_col]).strip() if sector_col and pd.notna(row.get(sector_col)) else "",
                industry=str(row[industry_col]).strip() if industry_col and pd.notna(row.get(industry_col)) else "",
                index_tags={index_tag},
                market_cap_usd=mcap,
                source=f"ishares_{index_tag.lower()}",
            )
        )
    return out


def load_index_csv(path: Path, *, index_tag: IndexTag) -> list[IndexMember]:
    """Load ticker,name[,sector,industry][,market_cap] CSV for index constituents."""
    df = pd.read_csv(path)
    cols = {c.lower().strip(): c for c in df.columns}
    ticker_col = cols.get("ticker") or cols.get("symbol")
    if not ticker_col:
        raise ValueError(f"Index CSV {path} missing ticker/symbol column")
    name_col = cols.get("name") or cols.get("company_name") or cols.get("security")
    sector_col = cols.get("sector") or cols.get("gics sector")
    industry_col = cols.get("industry") or cols.get("gics sub-industry") or cols.get("gics_sub_industry")
    mcap_col = cols.get("market_cap") or cols.get("market_cap_usd")
    out: list[IndexMember] = []
    for _, row in df.iterrows():
        ticker = normalize_equity_ticker(str(row[ticker_col]))
        if not ticker:
            continue
        mcap: float | None = None
        if mcap_col and pd.notna(row.get(mcap_col)):
            try:
                mcap = float(row[mcap_col])
            except (TypeError, ValueError):
                mcap = None
        out.append(
            IndexMember(
                ticker=ticker,
                name=str(row[name_col]).strip() if name_col and pd.notna(row.get(name_col)) else ticker,
                sector=str(row[sector_col]).strip() if sector_col and pd.notna(row.get(sector_col)) else "",
                industry=str(row[industry_col]).strip() if industry_col and pd.notna(row.get(industry_col)) else "",
                index_tags={index_tag},
                market_cap_usd=mcap,
                source=f"file_{index_tag.lower()}",
            )
        )
    return out


def merge_index_members(members: list[IndexMember]) -> dict[str, IndexMember]:
    """Merge index member rows by ticker; union index tags; prefer richer sector/industry."""
    by_ticker: dict[str, IndexMember] = {}
    for m in members:
        t = m.ticker
        if t not in by_ticker:
            by_ticker[t] = IndexMember(
                ticker=t,
                name=m.name,
                sector=m.sector,
                industry=m.industry,
                index_tags=set(m.index_tags),
                market_cap_usd=m.market_cap_usd,
                source=m.source,
            )
            continue
        cur = by_ticker[t]
        cur.index_tags |= m.index_tags
        if not cur.sector and m.sector:
            cur.sector = m.sector
        if not cur.industry and m.industry:
            cur.industry = m.industry
        if m.market_cap_usd and (cur.market_cap_usd is None or m.market_cap_usd > cur.market_cap_usd):
            cur.market_cap_usd = m.market_cap_usd
        if len(m.name) > len(cur.name):
            cur.name = m.name
    return by_ticker


def russell_2000_only_tickers(by_ticker: dict[str, IndexMember]) -> set[str]:
    """Tickers in Russell 3000 but not in Russell 1000 or S&P 500 (approx. R2000 band)."""
    r3000 = {t for t, m in by_ticker.items() if "R3000" in m.index_tags}
    r1000_or_sp = {t for t, m in by_ticker.items() if "R1000" in m.index_tags or "SP500" in m.index_tags}
    return r3000 - r1000_or_sp


def select_batch1_candidates(
    by_ticker: dict[str, IndexMember],
    *,
    max_tickers: int = MAX_BATCH1_SIZE,
    include_r2000_liquid: bool = False,
    r2000_min_market_cap_usd: float = 5e9,
) -> list[IndexMember]:
    """Priority fill: SP500 → R1000 \\ SP500 → liquid R3000 \\ R1000 (optional R2000 band)."""
    buckets: list[list[str]] = []
    sp500 = sorted(t for t, m in by_ticker.items() if "SP500" in m.index_tags)
    r1000_only = sorted(
        t for t, m in by_ticker.items() if "R1000" in m.index_tags and "SP500" not in m.index_tags
    )
    r3000_extra = sorted(
        t
        for t, m in by_ticker.items()
        if "R3000" in m.index_tags and "R1000" not in m.index_tags and "SP500" not in m.index_tags
    )
    if include_r2000_liquid and r3000_extra:
        r3000_extra = sorted(
            r3000_extra,
            key=lambda t: by_ticker[t].market_cap_usd or 0.0,
            reverse=True,
        )
        r3000_extra = [
            t
            for t in r3000_extra
            if (by_ticker[t].market_cap_usd or 0.0) >= r2000_min_market_cap_usd
        ]
    else:
        r3000_extra = []

    buckets.append(sp500)
    buckets.append(r1000_only)
    buckets.append(r3000_extra)

    selected: list[str] = []
    seen: set[str] = set()
    for bucket in buckets:
        for t in bucket:
            if t in seen:
                continue
            selected.append(t)
            seen.add(t)
            if len(selected) >= max_tickers:
                break
        if len(selected) >= max_tickers:
            break
    return [by_ticker[t] for t in selected[:max_tickers]]


def prepare_batch2_index_tags(
    by_ticker: dict[str, IndexMember],
    production_tickers: set[str],
    *,
    max_new: int = MAX_BATCH2_SIZE,
    r1000_target_total: int = 1000,
    r2000_min_market_cap_usd: float = 5e9,
    cap_fetch_limit: int = 900,
) -> int:
    """Rank non-production names by market cap; assign R1000 then liquid R3000 slots."""
    non_prod = sorted(t for t in by_ticker if t not in production_tickers)
    caps = fetch_market_caps_yahoo(non_prod[:cap_fetch_limit])
    for ticker, cap in caps.items():
        if ticker in by_ticker:
            by_ticker[ticker].market_cap_usd = cap or 0.0
    # Only use names with a valid Yahoo market cap for ranking/slot assignment.
    ranked = [t for t in sorted(non_prod, key=lambda t: caps.get(t, 0.0), reverse=True) if (caps.get(t, 0.0) or 0.0) > 0]
    r1000_slots = max(0, r1000_target_total - len(production_tickers))
    assigned = 0
    for ticker in ranked:
        if assigned >= max_new:
            break
        member = by_ticker[ticker]
        if assigned < r1000_slots:
            member.index_tags.add("R1000")
            assigned += 1
            continue
        if (caps.get(ticker, 0.0) or 0.0) >= r2000_min_market_cap_usd and "R3000" in member.index_tags:
            member.index_tags.discard("R1000")
            member.index_tags.add("R3000")
            assigned += 1
    return assigned


def select_batch2_candidates(
    by_ticker: dict[str, IndexMember],
    *,
    production_tickers: set[str],
    max_tickers: int = MAX_BATCH2_SIZE,
    include_r2000_liquid: bool = True,
    r2000_min_market_cap_usd: float = 5e9,
) -> list[IndexMember]:
    """Batch 2: names not in production — R1000 \\ prod, then liquid R3000 \\ R1000 \\ prod."""
    pool = {t: m for t, m in by_ticker.items() if t not in production_tickers}
    r1000_new = sorted(
        t for t, m in pool.items() if "R1000" in m.index_tags and "SP500" not in m.index_tags
    )
    r3000_band = sorted(
        t
        for t, m in pool.items()
        if "R3000" in m.index_tags and "R1000" not in m.index_tags and "SP500" not in m.index_tags
    )
    if include_r2000_liquid and r3000_band:
        caps_present = any((pool[t].market_cap_usd or 0.0) > 0 for t in r3000_band)
        if caps_present:
            r3000_band = sorted(r3000_band, key=lambda t: pool[t].market_cap_usd or 0.0, reverse=True)
            r3000_band = [t for t in r3000_band if (pool[t].market_cap_usd or 0.0) >= r2000_min_market_cap_usd]
        else:
            r3000_band = []

    selected: list[str] = []
    seen: set[str] = set()
    for bucket in (r1000_new, r3000_band):
        for t in bucket:
            if t in seen:
                continue
            selected.append(t)
            seen.add(t)
            if len(selected) >= max_tickers:
                break
        if len(selected) >= max_tickers:
            break
    return [pool[t] for t in selected[:max_tickers]]


def load_index_membership_pool(
    *,
    production_stock_path: Path,
    offline: bool = False,
    sp500_source: str = DEFAULT_SP500_WIKIPEDIA_URL,
    r1000_source: str | None = DEFAULT_ISHARES_IWB_HOLDINGS_URL,
    r3000_source: str | None = DEFAULT_ISHARES_IWV_HOLDINGS_URL,
    r1000_csv: Path | None = None,
    r3000_csv: Path | None = None,
    skip_r1000_market_cap: bool = False,
) -> tuple[dict[str, IndexMember], list[str]]:
    """Load merged index members and list of data source labels."""
    data_sources: list[str] = []
    all_members: list[IndexMember] = []

    if offline:
        for row in load_stock_universe(production_stock_path):
            t = _upper_ticker(row.get("ticker"))
            if t:
                all_members.append(
                    IndexMember(
                        ticker=t,
                        name=str(row.get("company_name") or t),
                        sector=str(row.get("sector") or ""),
                        industry=str(row.get("industry") or ""),
                        index_tags={"SP500"},
                        source="production_offline",
                    )
                )
        data_sources.append("production_offline")
    else:
        try:
            all_members.extend(fetch_sp500_wikipedia(sp500_source))
            data_sources.append("wikipedia_sp500")
        except Exception as exc:
            for row in load_stock_universe(production_stock_path):
                t = _upper_ticker(row.get("ticker"))
                if t:
                    all_members.append(
                        IndexMember(
                            ticker=t,
                            name=str(row.get("company_name") or t),
                            sector=str(row.get("sector") or ""),
                            industry=str(row.get("industry") or ""),
                            index_tags={"SP500"},
                            source="production_sp500_fallback",
                        )
                    )
            data_sources.append(f"production_sp500_fallback:{exc!s}")

        r1000_loaded = False
        if r1000_csv and r1000_csv.is_file():
            all_members.extend(load_index_csv(r1000_csv, index_tag="R1000"))
            data_sources.append(f"file:{r1000_csv.name}")
            r1000_loaded = True
        elif r1000_source:
            ishares_r1000 = fetch_ishares_holdings(r1000_source, index_tag="R1000")
            if ishares_r1000:
                all_members.extend(ishares_r1000)
                data_sources.append("ishares_iwb_holdings")
                r1000_loaded = True

        if r3000_csv and r3000_csv.is_file():
            all_members.extend(load_index_csv(r3000_csv, index_tag="R3000"))
            data_sources.append(f"file:{r3000_csv.name}")
        else:
            ishares_r3000 = fetch_ishares_holdings(r3000_source or "", index_tag="R3000") if r3000_source else None
            if ishares_r3000:
                all_members.extend(ishares_r3000)
                data_sources.append("ishares_iwv_holdings")
            else:
                r3000_text = fetch_source(DEFAULT_R3000_GITHUB_URL, user_agent=DEFAULT_BATCH_USER_AGENT)
                all_members.extend(parse_peer_firms_r3000_csv(r3000_text))
                data_sources.append("github_peer_firms_r3000")

        by_ticker = merge_index_members(all_members)
        if not r1000_loaded:
            if skip_r1000_market_cap:
                for member in by_ticker.values():
                    if "SP500" in member.index_tags:
                        member.index_tags.add("R1000")
                non_sp500 = sorted(
                    t
                    for t, m in by_ticker.items()
                    if "SP500" not in m.index_tags and "R3000" in m.index_tags
                )
                slots = max(0, 1000 - sum(1 for m in by_ticker.values() if "R1000" in m.index_tags))
                for ticker in non_sp500[:slots]:
                    by_ticker[ticker].index_tags.add("R1000")
                data_sources.append("r1000_derived_sp500_plus_r3000_fill_no_market_cap")
            else:
                apply_r1000_tags_by_market_cap(by_ticker, top_n=1000)
                data_sources.append("r1000_derived_top1000_market_cap_within_r3000")
        return by_ticker, data_sources

    return merge_index_members(all_members), data_sources


def is_excluded_instrument(name: str, ticker: str) -> str | None:
    """Return rejection reason for non-common-stock instruments."""
    if _ADR_NAME.search(name):
        return "adr_excluded"
    if _SPAC_NAME.search(name):
        return "spac_excluded"
    if _FUND_NAME.search(name):
        return "fund_or_etf_name"
    raw = {"ticker": ticker, "name": name, "test_issue": False, "financial_status": ""}
    clean = _clean_reason(raw)
    if clean:
        return clean
    return None


def build_batch_stock_row(
    member: IndexMember,
    *,
    batch_label: str,
    production_lookup: dict[str, dict[str, str]],
    data_sources: list[str],
    uncertain_notes: str = "",
) -> dict[str, Any]:
    """Build production-schema stock row plus draft-only annotation fields."""
    ticker = member.ticker
    sector = member.sector or "Unknown"
    industry = member.industry or "Unknown"
    if ticker in production_lookup:
        sector = production_lookup[ticker].get("sector") or sector
        industry = production_lookup[ticker].get("industry") or industry
    membership = primary_index_tag(member.index_tags)
    notes_parts = [
        f"Stock {batch_label}; index sources: {', '.join(sorted(data_sources))}.",
        f"Primary index_membership: {membership[0] if membership else 'none'}.",
    ]
    if uncertain_notes:
        notes_parts.append(uncertain_notes)
    row: dict[str, Any] = {
        "ticker": ticker,
        "company_name": member.name,
        "asset_class": "equity",
        "sector": sector,
        "industry": industry,
        "thematic_tags": [],
        "region": "US",
        "currency_exposure": "USD",
        "main_risk_factor": "equity",
        "secondary_risk_factors": ["us_growth"],
        "risk_role": ["risk_on"],
        "index_membership": membership,
        "notes": " ".join(notes_parts),
        # Draft/review annotations (stripped before production merge)
        "subtype": "stock",
        "stress_block": "EQ",
        "data_source": list(data_sources),
    }
    return row


def build_batch1_stock_row(
    member: IndexMember,
    *,
    production_lookup: dict[str, dict[str, str]],
    data_sources: list[str],
    uncertain_notes: str = "",
) -> dict[str, Any]:
    return build_batch_stock_row(
        member,
        batch_label="Batch 1",
        production_lookup=production_lookup,
        data_sources=data_sources,
        uncertain_notes=uncertain_notes,
    )


def _merge_ready(
    accepted: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
    needs_review: list[dict[str, Any]],
    *,
    min_accepted: int | None = None,
) -> bool:
    """True when accepted rows are merge-safe; rejected rows do not block merge."""
    del rejected  # screened out; merge uses accepted_tickers only
    if needs_review:
        return False
    for row in accepted:
        if str(row.get("sector") or "") in ("", "Unknown"):
            return False
        if str(row.get("industry") or "") in ("", "Unknown"):
            return False
        if not row.get("index_membership"):
            return False
    if min_accepted is not None and len(accepted) < min_accepted:
        return False
    return True


def _assess_row(
    row: dict[str, Any],
    *,
    prod_by_ticker: dict[str, dict[str, Any]],
    seen_tickers: set[str],
) -> tuple[str, str]:
    """Return (disposition, reason): accepted|rejected|needs_review|in_production."""
    ticker = _upper_ticker(row.get("ticker"))
    name = str(row.get("company_name") or "")
    if ticker in seen_tickers:
        return "rejected", "duplicate_in_batch"
    excl = is_excluded_instrument(name, ticker)
    if excl:
        return "rejected", excl
    if not row.get("index_membership"):
        return "rejected", "missing_index_membership"
    if str(row.get("sector") or "") in ("", "Unknown"):
        return "rejected", "missing_sector"
    if str(row.get("industry") or "") in ("", "Unknown"):
        return "rejected", "missing_industry"
    membership = row.get("index_membership") or []
    if any(m not in INDEX_MEMBERSHIP_VALUES for m in membership):
        return "rejected", "invalid_index_membership"
    prod_row = production_row_from_draft(row)
    if ticker in prod_by_ticker:
        diff = _row_diff(prod_by_ticker[ticker], prod_row)
        if diff:
            # Production wins for merge; field drift vs index source is not a merge blocker.
            return "in_production", "production_field_diff"
        return "in_production", "already_in_production"
    val = validate_stock_universe([prod_row])
    if val.get("status") == "FAIL":
        return "rejected", "invalid_schema"
    return "accepted", ""


def production_row_from_draft(row: dict[str, Any]) -> dict[str, Any]:
    skip = {"notes", "subtype", "stress_block", "data_source"}
    return {k: v for k, v in row.items() if k not in skip}


def run_stock_batch1_pipeline(
    *,
    output_dir: Path,
    production_stock_path: Path,
    sp500_source: str = DEFAULT_SP500_WIKIPEDIA_URL,
    r1000_source: str | None = DEFAULT_ISHARES_IWB_HOLDINGS_URL,
    r3000_source: str | None = DEFAULT_ISHARES_IWV_HOLDINGS_URL,
    r1000_csv: Path | None = None,
    r3000_csv: Path | None = None,
    max_tickers: int = MAX_BATCH1_SIZE,
    include_r2000_liquid: bool = False,
    enrich_yahoo: bool = True,
    yahoo_limit: int | None = 500,
    dry_run: bool = False,
    offline: bool = False,
    skip_r1000_market_cap: bool = False,
) -> StockBatch1Result:
    """Build Stock Batch 1 draft artifacts and review report."""
    output_dir.mkdir(parents=True, exist_ok=True)
    data_sources: list[str] = []
    all_members: list[IndexMember] = []

    if offline:
        # Offline mode is used for deterministic tests. If explicit index CSV inputs are
        # provided, do not seed the pool with the full production universe (it can crowd
        # out the intended "new" sample tickers under small max_tickers limits).
        if not (r1000_csv or r3000_csv):
            prod = load_stock_universe(production_stock_path)
            for row in prod:
                t = _upper_ticker(row.get("ticker"))
                if not t:
                    continue
                all_members.append(
                    IndexMember(
                        ticker=t,
                        name=str(row.get("company_name") or t),
                        sector=str(row.get("sector") or ""),
                        industry=str(row.get("industry") or ""),
                        index_tags={"SP500"},
                        source="production_offline",
                    )
                )
            data_sources.append("production_offline")
    else:
        try:
            sp500 = fetch_sp500_wikipedia(sp500_source)
            all_members.extend(sp500)
            data_sources.append("wikipedia_sp500")
        except Exception as exc:
            prod = load_stock_universe(production_stock_path)
            for row in prod:
                t = _upper_ticker(row.get("ticker"))
                if not t:
                    continue
                all_members.append(
                    IndexMember(
                        ticker=t,
                        name=str(row.get("company_name") or t),
                        sector=str(row.get("sector") or ""),
                        industry=str(row.get("industry") or ""),
                        index_tags={"SP500"},
                        source="production_sp500_fallback",
                    )
                )
            data_sources.append(f"production_sp500_fallback:{exc!s}")

    r1000_loaded = False
    if r1000_csv and r1000_csv.is_file():
        all_members.extend(load_index_csv(r1000_csv, index_tag="R1000"))
        data_sources.append(f"file:{r1000_csv.name}")
        r1000_loaded = True
    elif not offline and r1000_source:
        ishares_r1000 = fetch_ishares_holdings(r1000_source, index_tag="R1000")
        if ishares_r1000:
            all_members.extend(ishares_r1000)
            data_sources.append("ishares_iwb_holdings")
            r1000_loaded = True

    if r3000_csv and r3000_csv.is_file():
        all_members.extend(load_index_csv(r3000_csv, index_tag="R3000"))
        data_sources.append(f"file:{r3000_csv.name}")
    elif not offline:
        ishares_r3000 = fetch_ishares_holdings(r3000_source or "", index_tag="R3000") if r3000_source else None
        if ishares_r3000:
            all_members.extend(ishares_r3000)
            data_sources.append("ishares_iwv_holdings")
        else:
            r3000_text = fetch_source(DEFAULT_R3000_GITHUB_URL, user_agent=DEFAULT_BATCH_USER_AGENT)
            all_members.extend(parse_peer_firms_r3000_csv(r3000_text))
            data_sources.append("github_peer_firms_r3000")

    by_ticker = merge_index_members(all_members)
    if not offline and not r1000_loaded:
        if skip_r1000_market_cap:
            for member in by_ticker.values():
                if "SP500" in member.index_tags:
                    member.index_tags.add("R1000")
            non_sp500 = sorted(
                t
                for t, m in by_ticker.items()
                if "SP500" not in m.index_tags and "R3000" in m.index_tags
            )
            slots = max(0, 1000 - sum(1 for m in by_ticker.values() if "R1000" in m.index_tags))
            for ticker in non_sp500[:slots]:
                by_ticker[ticker].index_tags.add("R1000")
            data_sources.append("r1000_derived_sp500_plus_r3000_fill_no_market_cap")
        else:
            apply_r1000_tags_by_market_cap(by_ticker, top_n=1000)
            data_sources.append("r1000_derived_top1000_market_cap_within_r3000")
    candidates = select_batch1_candidates(
        by_ticker,
        max_tickers=max_tickers,
        include_r2000_liquid=include_r2000_liquid,
    )

    production_lookup = load_production_stock_sector_lookup(production_stock_path)
    prod_by_ticker = {
        _upper_ticker(r.get("ticker")): r
        for r in load_stock_universe(production_stock_path)
        if _upper_ticker(r.get("ticker"))
    }

    draft_rows: list[dict[str, Any]] = []
    for member in candidates:
        draft_rows.append(
            build_batch1_stock_row(
                member,
                production_lookup=production_lookup,
                data_sources=data_sources,
            )
        )

    if enrich_yahoo:
        enriched, enrich_meta = enrich_draft_stocks(
            draft_rows,
            production_lookup=production_lookup,
            use_yahoo=True,
            yahoo_limit=yahoo_limit,
        )
        draft_rows = enriched
        # Second pass for rows still missing industry (R3000 GitHub has sector only).
        still_unknown = [
            r
            for r in draft_rows
            if str(r.get("industry")) in ("", "Unknown") and _upper_ticker(r.get("ticker")) not in prod_by_ticker
        ]
        if still_unknown and yahoo_limit is not None:
            extra_limit = max(yahoo_limit, len(still_unknown))
            enriched2, _ = enrich_draft_stocks(
                still_unknown,
                production_lookup=production_lookup,
                use_yahoo=True,
                yahoo_limit=extra_limit,
            )
            by_t = {_upper_ticker(r["ticker"]): r for r in enriched2}
            draft_rows = [by_t.get(_upper_ticker(r.get("ticker")), r) for r in draft_rows]
        elif still_unknown:
            enriched2, _ = enrich_draft_stocks(
                still_unknown,
                production_lookup=production_lookup,
                use_yahoo=True,
                yahoo_limit=None,
            )
            by_t = {_upper_ticker(r["ticker"]): r for r in enriched2}
            draft_rows = [by_t.get(_upper_ticker(r.get("ticker")), r) for r in draft_rows]

    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    needs_review: list[dict[str, Any]] = []
    in_production: list[dict[str, Any]] = []
    seen: set[str] = set()
    reject_reasons: Counter[str] = Counter()
    for row in draft_rows:
        disp, reason = _assess_row(row, prod_by_ticker=prod_by_ticker, seen_tickers=seen)
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

    prod_accept_rows = [production_row_from_draft(r) for r in accepted]
    merge_ready = not needs_review and not any(
        str(r.get("reject_reason"))
        in ("missing_sector", "missing_industry", "missing_index_membership", "duplicate_in_batch", "invalid_schema")
        for r in rejected
    )

    r2000_only = russell_2000_only_tickers(by_ticker)
    review_report: dict[str, Any] = {
        "version": "stock_batch1_review_v1",
        "snapshot_date": date.today().isoformat(),
        "index_membership_source": {
            "SP500": "wikipedia_gics" if not offline else "production_offline",
            "R1000": r1000_source or (str(r1000_csv) if r1000_csv else None),
            "R3000": r3000_source or (str(r3000_csv) if r3000_csv else None),
        },
        "sector_industry_source": "index_file_or_wikipedia_gics; production_lookup; optional_yahoo_finance",
        "data_sources": data_sources,
        "summary": {
            "total_candidates": len(candidates),
            "draft_rows": len(draft_rows),
            "accepted_candidates": len(accepted),
            "rejected_candidates": len(rejected),
            "needs_review_candidates": len(needs_review),
            "missing_sector_industry": sum(
                1
                for r in draft_rows
                if str(r.get("sector")) in ("", "Unknown") or str(r.get("industry")) in ("", "Unknown")
            ),
            "missing_index_membership": sum(1 for r in draft_rows if not r.get("index_membership")),
            "duplicates_in_batch": len(draft_rows) - len({ _upper_ticker(r.get("ticker")) for r in draft_rows }),
            "production_conflicts": sum(1 for r in needs_review if r.get("review_reason") == "production_conflict"),
            "already_in_production": len(in_production),
            "russell_2000_only_pool_size": len(r2000_only),
            "r2000_included": include_r2000_liquid,
            "merge_ready": merge_ready,
            "recommended_new_tickers": len(accepted),
        },
        "reject_reason_counts": dict(reject_reasons),
        "accepted_tickers": sorted(_upper_ticker(r.get("ticker")) for r in accepted),
        "data_quality_warnings": [],
    }
    if include_r2000_liquid:
        review_report["data_quality_warnings"].append(
            "Russell 2000 band names included with market-cap filter; verify liquidity manually."
        )
    if not merge_ready:
        review_report["data_quality_warnings"].append(
            "Merge blocked: resolve needs_review, unknown sector/industry, or schema errors before --confirm."
        )

    if not dry_run:
        _write_batch1_artifacts(
            output_dir,
            draft_rows=draft_rows,
            accepted=accepted,
            rejected=rejected,
            needs_review=needs_review,
            review_report=review_report,
        )

    return StockBatch1Result(
        draft_rows=draft_rows,
        accepted=accepted,
        rejected=rejected,
        needs_review=needs_review,
        review_report=review_report,
        merge_ready=merge_ready,
    )


@dataclass
class StockBatch2Result:
    draft_rows: list[dict[str, Any]]
    accepted: list[dict[str, Any]]
    rejected: list[dict[str, Any]]
    needs_review: list[dict[str, Any]]
    review_report: dict[str, Any]
    merge_ready: bool


def run_stock_batch2_pipeline(
    *,
    output_dir: Path,
    production_stock_path: Path,
    max_tickers: int = MAX_BATCH2_SIZE,
    min_accepted: int = MIN_BATCH2_ACCEPTED,
    include_r2000_liquid: bool = True,
    enrich_yahoo: bool = False,
    dry_run: bool = False,
    skip_r1000_market_cap: bool = True,
    r2000_min_market_cap_usd: float = 5e9,
    prefill_r3000_caps: int = 0,
) -> StockBatch2Result:
    """Build Stock Batch 2 from index pool excluding current production tickers."""
    output_dir.mkdir(parents=True, exist_ok=True)
    prod_records = load_stock_universe(production_stock_path)
    production_tickers = {_upper_ticker(r.get("ticker")) for r in prod_records if _upper_ticker(r.get("ticker"))}
    production_count_before = len(production_tickers)

    by_ticker, data_sources = load_index_membership_pool(
        production_stock_path=production_stock_path,
        skip_r1000_market_cap=True,
    )
    data_sources.append("batch2_market_cap_rank_tags")
    tag_slots = max(max_tickers, min(max_tickers + 400, 1100))
    prepare_batch2_index_tags(
        by_ticker,
        production_tickers,
        max_new=tag_slots,
        r2000_min_market_cap_usd=r2000_min_market_cap_usd,
        cap_fetch_limit=max(1200, prefill_r3000_caps or 0, tag_slots + 300),
    )

    candidates = select_batch2_candidates(
        by_ticker,
        production_tickers=production_tickers,
        max_tickers=max_tickers,
        include_r2000_liquid=include_r2000_liquid,
        r2000_min_market_cap_usd=r2000_min_market_cap_usd,
    )

    production_lookup = load_production_stock_sector_lookup(production_stock_path)
    prod_by_ticker = {_upper_ticker(r.get("ticker")): r for r in prod_records if _upper_ticker(r.get("ticker"))}

    draft_rows = [
        build_batch_stock_row(
            m,
            batch_label="Batch 2",
            production_lookup=production_lookup,
            data_sources=data_sources,
        )
        for m in candidates
    ]

    if enrich_yahoo:
        draft_rows, _ = enrich_draft_stocks(
            draft_rows, production_lookup=production_lookup, use_yahoo=True, yahoo_limit=50
        )

    accepted, rejected, needs_review, in_production = [], [], [], []
    seen: set[str] = set()
    reject_reasons: Counter[str] = Counter()
    for row in draft_rows:
        disp, reason = _assess_row(row, prod_by_ticker=prod_by_ticker, seen_tickers=seen)
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

    merge_ready = _merge_ready(
        accepted, rejected, needs_review, min_accepted=min_accepted
    )
    r2000_only = russell_2000_only_tickers(by_ticker)
    review_report: dict[str, Any] = {
        "version": "stock_batch2_review_v1",
        "snapshot_date": date.today().isoformat(),
        "batch": 2,
        "production_count_before": production_count_before,
        "index_membership_source": {
            "SP500": "wikipedia_gics",
            "R1000": "derived_or_ishares",
            "R3000": DEFAULT_R3000_GITHUB_URL,
        },
        "sector_industry_source": "index_gics_code; yahoo_finance_enrichment",
        "data_sources": data_sources,
        "summary": {
            "total_candidates_screened": len(candidates),
            "draft_rows": len(draft_rows),
            "accepted_candidates": len(accepted),
            "rejected_candidates": len(rejected),
            "needs_review_candidates": len(needs_review),
            "already_in_production": len(in_production),
            "missing_sector_industry": sum(
                1
                for r in draft_rows
                if str(r.get("sector")) in ("", "Unknown") or str(r.get("industry")) in ("", "Unknown")
            ),
            "missing_index_membership": sum(1 for r in draft_rows if not r.get("index_membership")),
            "duplicates_in_batch": len(draft_rows) - len({_upper_ticker(r.get("ticker")) for r in draft_rows}),
            "production_conflicts": sum(1 for r in needs_review if r.get("review_reason") == "production_conflict"),
            "russell_2000_only_pool_size": len(r2000_only),
            "r2000_included": include_r2000_liquid,
            "merge_ready": merge_ready,
            "recommended_new_tickers": len(accepted),
            "production_count_after_merge_planned": production_count_before + len(accepted),
        },
        "reject_reason_counts": dict(reject_reasons),
        "accepted_tickers": sorted(_upper_ticker(r.get("ticker")) for r in accepted),
        "data_quality_warnings": [],
    }
    if len(accepted) < min_accepted:
        review_report["data_quality_warnings"].append(
            f"Accepted count {len(accepted)} below target minimum {min_accepted}."
        )
    if not merge_ready:
        review_report["data_quality_warnings"].append(
            "Merge blocked: needs_review, missing fields on accepted rows, blocking rejects, or below min accepted."
        )

    if not dry_run:
        _write_batch_artifacts(
            output_dir,
            2,
            draft_rows=draft_rows,
            accepted=accepted,
            rejected=rejected,
            needs_review=needs_review,
            review_report=review_report,
        )

    return StockBatch2Result(
        draft_rows=draft_rows,
        accepted=accepted,
        rejected=rejected,
        needs_review=needs_review,
        review_report=review_report,
        merge_ready=merge_ready,
    )


def _write_batch_artifacts(
    output_dir: Path,
    batch_num: int,
    *,
    draft_rows: list[dict[str, Any]],
    accepted: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
    needs_review: list[dict[str, Any]],
    review_report: dict[str, Any],
) -> None:
    draft_path = output_dir / f"draft_stock_universe_batch{batch_num}.yml"
    header = [
        f"# snapshot_date: {review_report.get('snapshot_date')}",
        f"# snapshot_source: Stock Batch {batch_num} index-based pipeline (draft only)",
        f"# verification_note: Do not merge without clean stock_batch{batch_num}_review_report.json",
        "",
    ]
    body = []
    for rec in draft_rows:
        body.append("- " + yaml.dump(rec, default_flow_style=True, allow_unicode=True).strip())
    draft_path.write_text("\n".join(header + body) + "\n", encoding="utf-8")

    (output_dir / f"stock_batch{batch_num}_review_report.json").write_text(
        json.dumps(review_report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    import pandas as pd

    nr_cols = [
        "ticker",
        "company_name",
        "sector",
        "industry",
        "index_membership",
        "review_reason",
        "reject_reason",
        "notes",
    ]
    nr_rows: list[dict[str, Any]] = []
    for r in needs_review:
        nr_rows.append({c: r.get(c, "") for c in nr_cols})
        nr_rows[-1]["review_reason"] = r.get("review_reason", "")
    for r in rejected:
        if r.get("reject_reason") in (
            "missing_sector",
            "missing_industry",
            "missing_index_membership",
            "production_conflict",
        ):
            nr_rows.append({c: r.get(c, "") for c in nr_cols})
            nr_rows[-1]["reject_reason"] = r.get("reject_reason", "")
    nr_name = "needs_review_stocks.csv" if batch_num == 1 else f"needs_review_stocks_batch{batch_num}.csv"
    pd.DataFrame(nr_rows).to_csv(output_dir / nr_name, index=False)

    tickers_path = output_dir / f"stock_batch{batch_num}_accepted_tickers.txt"
    tickers_path.write_text(
        "\n".join(review_report.get("accepted_tickers") or []) + "\n",
        encoding="utf-8",
    )


def _write_batch1_artifacts(
    output_dir: Path,
    *,
    draft_rows: list[dict[str, Any]],
    accepted: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
    needs_review: list[dict[str, Any]],
    review_report: dict[str, Any],
) -> None:
    _write_batch_artifacts(
        output_dir, 1, draft_rows=draft_rows, accepted=accepted, rejected=rejected,
        needs_review=needs_review, review_report=review_report,
    )


def build_batch1_merge_preview(
    *,
    output_dir: Path,
    production_stock_path: Path,
    draft_path: Path | None = None,
) -> tuple[MergePlan, dict[str, Any]]:
    """Preview merge for accepted production rows only."""
    draft_file = draft_path or (output_dir / "draft_stock_universe_batch1.yml")
    report_path = output_dir / "stock_batch1_review_report.json"
    if report_path.is_file():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        tickers = set(report.get("accepted_tickers") or [])
    else:
        tickers = None
    accepted_rows = [
        production_row_from_draft(r)
        for r in load_draft_universe_yaml(draft_file)
        if not tickers or _upper_ticker(r.get("ticker")) in tickers
    ]
    tmp = output_dir / "_merge_preview_accepted.yml"
    tmp.write_text(
        "\n".join("- " + yaml.dump(r, default_flow_style=True).strip() for r in accepted_rows) + "\n",
        encoding="utf-8",
    )
    return build_merge_plan(
        draft_etf_path=output_dir / "_nonexistent_etf.yml",
        draft_stock_path=tmp,
        production_etf_path=production_stock_path.parent / "etf_universe.yml",
        production_stock_path=production_stock_path,
        include_etfs=False,
        include_stocks=True,
        stock_batch_mode=True,
    )


__all__ = [
    "MAX_BATCH1_SIZE",
    "MAX_BATCH2_SIZE",
    "MIN_BATCH2_ACCEPTED",
    "IndexMember",
    "StockBatch1Result",
    "StockBatch2Result",
    "build_batch1_stock_row",
    "build_batch_stock_row",
    "fetch_sp500_wikipedia",
    "load_index_membership_pool",
    "merge_index_members",
    "normalize_equity_ticker",
    "parse_ishares_holdings_csv",
    "production_row_from_draft",
    "build_batch1_merge_preview",
    "run_stock_batch1_pipeline",
    "run_stock_batch2_pipeline",
    "select_batch1_candidates",
    "select_batch2_candidates",
]
