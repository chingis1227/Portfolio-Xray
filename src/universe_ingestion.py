"""
US listed universe ingestion: parse public sources, clean, classify, draft taxonomy.

Staged pipeline only — never writes production config/etf_universe.yml or stock_universe.yml.
See docs/specs/universe_ingestion_spec.md.
"""
from __future__ import annotations

import csv
import io
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal
from urllib.error import URLError
from urllib.request import Request, urlopen

import pandas as pd
import yaml

from src.etf_universe import validate_etf_universe
from src.stock_universe import validate_stock_universe
from src.taxonomy_stress_blocks import (
    assess_classification,
    derive_stress_block_from_taxonomy_row,
)

SecurityKind = Literal["stock", "etf", "unknown"]
ClassificationMethod = Literal["rule_based", "source_metadata", "inferred", "manual_required"]
ClassificationConfidence = Literal["high", "medium", "low"]
Disposition = Literal["kept", "removed", "flagged"]

DEFAULT_NASDAQ_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
DEFAULT_OTHER_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"
DEFAULT_SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers_exchange.json"

# Conservative suffix / name patterns for non-core instruments
# Warrant/right/unit suffixes — conservative (avoid false positives like TIP, IEF)
_WARRANT_SUFFIXES = re.compile(r"(WS|WT|\+W|-W)$", re.IGNORECASE)
_PREFERRED_NAME = re.compile(r"\bpreferred\b|\bpfd\b|\bpr\s", re.IGNORECASE)
_RIGHTS_NAME = re.compile(r"\b(right|rights)\b", re.IGNORECASE)
_UNIT_NAME = re.compile(r"\bunit(s)...\b", re.IGNORECASE)
_WARRANT_NAME = re.compile(r"\bwarrant(s)...\b", re.IGNORECASE)
_TEST_NAME = re.compile(r"\btest\b", re.IGNORECASE)
_UNSUPPORTED_SYMBOL = re.compile(r"[^A-Z0-9.\-]")

_HYBRID_NAME_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("preferred_share", _PREFERRED_NAME),
    ("convertible", re.compile(r"\bconvertible\b", re.IGNORECASE)),
    ("covered_call", re.compile(r"covered call|buywrite|option income", re.IGNORECASE)),
    ("option_income", re.compile(r"option income|premium income", re.IGNORECASE)),
    ("leveraged", re.compile(r"\b(2x|3x|ultra|ultrapro|leveraged)\b", re.IGNORECASE)),
    ("inverse", re.compile(r"\binverse\b|\bshort\b|\b(-1x|-2x|-3x)\b", re.IGNORECASE)),
    ("crypto", re.compile(r"\b(bitcoin|btc|ether|ethereum|crypto)\b", re.IGNORECASE)),
    ("volatility", re.compile(r"\b(vix|volatility|vol)\b", re.IGNORECASE)),
    ("multi_asset", re.compile(r"multi-asset|multi asset|balanced fund|target allocation", re.IGNORECASE)),
    ("managed_futures", re.compile(r"managed futures|cta\b", re.IGNORECASE)),
    ("private_credit", re.compile(r"private credit|direct lending", re.IGNORECASE)),
    ("clo", re.compile(r"\bclo\b|collateralized loan", re.IGNORECASE)),
    ("mortgage_reit", re.compile(r"mortgage reit|mreit", re.IGNORECASE)),
]

_ISSUER_KEYWORDS: list[tuple[str, str]] = [
    ("Vanguard", "Vanguard"),
    ("iShares", "iShares"),
    ("SPDR", "State Street"),
    ("Invesco", "Invesco"),
    ("Schwab", "Schwab"),
    ("First Trust", "First Trust"),
    ("Global X", "Global X"),
    ("VanEck", "VanEck"),
    ("ProShares", "ProShares"),
    ("Direxion", "Direxion"),
    ("KraneShares", "KraneShares"),
    ("Franklin", "Franklin"),
    ("Pacer", "Pacer"),
    ("State Street", "State Street"),
    ("JPMorgan", "JPMorgan"),
    ("Fidelity", "Fidelity"),
    ("BlackRock", "BlackRock"),
    ("WisdomTree", "WisdomTree"),
]


def _upper_ticker(value: Any) -> str:
    return str(value or "").strip().upper()


def _norm_yes(value: Any) -> bool:
    return str(value or "").strip().upper() in {"Y", "YES", "TRUE", "1"}


DEFAULT_SEC_USER_AGENT = "PortfolioMRI/1.0 (research; universe-ingestion@local)"

# Yahoo Finance sector labels → GICS-style labels used in stock_universe.yml
_YAHOO_SECTOR_TO_GICS: dict[str, str] = {
    "Technology": "Information Technology",
    "Healthcare": "Health Care",
    "Financial Services": "Financials",
    "Financial": "Financials",
    "Consumer Cyclical": "Consumer Discretionary",
    "Consumer Defensive": "Consumer Staples",
    "Industrials": "Industrials",
    "Energy": "Energy",
    "Utilities": "Utilities",
    "Basic Materials": "Materials",
    "Materials": "Materials",
    "Real Estate": "Real Estate",
    "Communication Services": "Communication Services",
}


def fetch_source(url_or_path: str, *, timeout: int = 60, user_agent: str | None = None) -> str:
    """Load text from HTTP(S) URL or local file path."""
    p = Path(url_or_path)
    if p.exists() and p.is_file():
        return p.read_text(encoding="utf-8", errors="replace")
    headers = {}
    if user_agent:
        headers["User-Agent"] = user_agent
    elif "sec.gov" in url_or_path.lower():
        headers["User-Agent"] = DEFAULT_SEC_USER_AGENT
        headers["Accept"] = "application/json"
    req = Request(url_or_path, headers=headers)
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return raw.decode("utf-8", errors="replace")
    except URLError as exc:
        raise RuntimeError(f"Failed to fetch source {url_or_path!r}: {exc}") from exc


def parse_nasdaqlisted_text(text: str) -> list[dict[str, Any]]:
    """Parse Nasdaq Trader nasdaqlisted.txt pipe-delimited file."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return []
    reader = csv.DictReader(lines, delimiter="|")
    rows: list[dict[str, Any]] = []
    for raw in reader:
        symbol = _upper_ticker(raw.get("Symbol"))
        if not symbol or symbol.startswith("FILE"):
            continue
        rows.append(
            {
                "ticker": symbol,
                "name": str(raw.get("Security Name") or "").strip(),
                "source": "nasdaqlisted",
                "exchange": "NASDAQ",
                "market_category": str(raw.get("Market Category") or "").strip(),
                "test_issue": _norm_yes(raw.get("Test Issue")),
                "financial_status": str(raw.get("Financial Status") or "").strip().upper(),
                "etf_flag": _norm_yes(raw.get("ETF")),
                "next_shares": _norm_yes(raw.get("NextShares")),
            }
        )
    return rows


def parse_otherlisted_text(text: str) -> list[dict[str, Any]]:
    """Parse Nasdaq Trader otherlisted.txt pipe-delimited file."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return []
    reader = csv.DictReader(lines, delimiter="|")
    rows: list[dict[str, Any]] = []
    for raw in reader:
        symbol = _upper_ticker(raw.get("ACT Symbol"))
        if not symbol or symbol.startswith("FILE"):
            continue
        rows.append(
            {
                "ticker": symbol,
                "name": str(raw.get("Security Name") or "").strip(),
                "source": "otherlisted",
                "exchange": str(raw.get("Exchange") or "").strip(),
                "cqs_symbol": str(raw.get("CQS Symbol") or "").strip(),
                "etf_flag": _norm_yes(raw.get("ETF")),
                "test_issue": _norm_yes(raw.get("Test Issue")),
                "nasdaq_symbol": str(raw.get("NASDAQ Symbol") or "").strip(),
            }
        )
    return rows


def parse_sec_company_tickers_json(text: str) -> list[dict[str, Any]]:
    """Parse SEC company_tickers_exchange.json."""
    payload = json.loads(text)
    fields = payload.get("fields") or []
    data = payload.get("data") or []
    idx = {str(f).lower(): i for i, f in enumerate(fields)}
    rows: list[dict[str, Any]] = []
    for item in data:
        if not isinstance(item, list):
            continue
        ticker = _upper_ticker(item[idx.get("ticker", 2)] if "ticker" in idx else item[2])
        if not ticker:
            continue
        rows.append(
            {
                "ticker": ticker,
                "name": str(item[idx.get("name", 1)] if "name" in idx else item[1]).strip(),
                "source": "sec_company_tickers",
                "cik": str(item[idx.get("cik", 0)] if "cik" in idx else item[0]).strip(),
                "exchange": str(item[idx.get("exchange", 3)] if "exchange" in idx else item[3]).strip(),
            }
        )
    return rows


def _merge_raw_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Deduplicate by ticker; merge metadata from multiple sources."""
    by_ticker: dict[str, dict[str, Any]] = {}
    for row in rows:
        t = _upper_ticker(row.get("ticker"))
        if not t:
            continue
        if t not in by_ticker:
            by_ticker[t] = {
                "ticker": t,
                "name": row.get("name") or "",
                "sources": [],
                "etf_flag": False,
                "test_issue": False,
                "exchange": "",
                "financial_status": "",
                "sec_name": "",
                "sec_exchange": "",
                "sec_cik": "",
            }
        rec = by_ticker[t]
        src = str(row.get("source") or "")
        if src and src not in rec["sources"]:
            rec["sources"].append(src)
        if row.get("name") and (not rec["name"] or len(str(row["name"])) > len(str(rec["name"]))):
            rec["name"] = row["name"]
        if row.get("etf_flag"):
            rec["etf_flag"] = True
        if row.get("test_issue"):
            rec["test_issue"] = True
        if row.get("exchange"):
            rec["exchange"] = row["exchange"]
        if row.get("financial_status"):
            rec["financial_status"] = row["financial_status"]
        if src == "sec_company_tickers":
            rec["sec_name"] = row.get("name") or rec["sec_name"]
            rec["sec_exchange"] = row.get("exchange") or rec["sec_exchange"]
            rec["sec_cik"] = row.get("cik") or rec["sec_cik"]
    return by_ticker


@dataclass
class CleanResult:
    kept: list[dict[str, Any]] = field(default_factory=list)
    removed: list[dict[str, Any]] = field(default_factory=list)
    flagged: list[dict[str, Any]] = field(default_factory=list)


def _clean_reason(row: dict[str, Any]) -> str | None:
    ticker = _upper_ticker(row.get("ticker"))
    name = str(row.get("name") or "")
    if row.get("test_issue"):
        return "test_issue"
    if row.get("financial_status") == "D":
        return "delisted_financial_status_D"
    if _TEST_NAME.search(name):
        return "test_issue_name"
    if _WARRANT_NAME.search(name) or _WARRANT_SUFFIXES.search(ticker):
        return "warrant"
    if _RIGHTS_NAME.search(name):
        return "rights"
    if _UNIT_NAME.search(name) and " ETF" not in name.upper():
        return "units"
    if _PREFERRED_NAME.search(name):
        return "preferred_share"
    if ticker and _UNSUPPORTED_SYMBOL.search(ticker.replace(".", "").replace("-", "")):
        return "unsupported_symbol_characters"
    return None


def detect_security_kind(row: dict[str, Any]) -> SecurityKind:
    if row.get("etf_flag"):
        return "etf"
    name_u = str(row.get("name") or "").upper()
    if " ETF" in name_u or "EXCHANGE TRADED FUND" in name_u or " ETN" in name_u:
        return "etf"
    if row.get("next_shares"):
        return "etf"
    if row.get("sources") == ["sec_company_tickers"]:
        return "stock"
    if any(s in (row.get("sources") or []) for s in ("nasdaqlisted", "otherlisted")):
        if row.get("etf_flag") is False and " ETF" not in name_u:
            return "stock"
    if row.get("sec_cik"):
        return "stock"
    return "unknown"


def clean_raw_universe(raw_by_ticker: dict[str, dict[str, Any]]) -> CleanResult:
    result = CleanResult()
    for ticker, row in sorted(raw_by_ticker.items()):
        row = dict(row)
        row["security_kind_guess"] = detect_security_kind(row)
        reason = _clean_reason(row)
        if reason:
            row["disposition"] = "removed"
            row["disposition_reason"] = reason
            result.removed.append(row)
            continue
        if row["security_kind_guess"] == "unknown":
            row["disposition"] = "flagged"
            row["disposition_reason"] = "unclear_security_type"
            result.flagged.append(row)
            continue
        row["disposition"] = "kept"
        row["disposition_reason"] = ""
        result.kept.append(row)
    return result


def _infer_issuer(name: str) -> str:
    for keyword, issuer in _ISSUER_KEYWORDS:
        if keyword.lower() in name.lower():
            return issuer
    return "unknown"


def _detect_hybrid_flags(name: str) -> list[str]:
    flags: list[str] = []
    for label, pattern in _HYBRID_NAME_PATTERNS:
        if pattern.search(name):
            flags.append(label)
    return flags


def _match_keywords(name: str, keywords: list[str]) -> bool:
    name_l = name.lower()
    return any(kw.lower() in name_l for kw in keywords)


@dataclass
class EtfClassification:
    asset_class: str
    subtype: str
    sector: str
    main_risk_factor: str
    secondary_risk_factors: list[str]
    region: str
    currency_exposure: str
    duration_bucket: str
    credit_quality: str
    risk_role: list[str]
    thematic_primary: str
    thematic_tags: list[str]
    stress_block: str
    classification_method: ClassificationMethod
    classification_confidence: ClassificationConfidence
    needs_review: bool
    warnings: list[str]
    hybrid_flags: list[str]


def classify_etf(name: str, *, etf_flag: bool = True) -> EtfClassification:
    """Rule-based ETF taxonomy classifier."""
    hybrid_flags = _detect_hybrid_flags(name)
    warnings: list[str] = []
    needs_review = bool(hybrid_flags)
    confidence: ClassificationConfidence = "high"
    method: ClassificationMethod = "source_metadata" if etf_flag else "rule_based"

    name_l = name.lower()

    # Order: cash-like → TIPS → credit → commodity → treasury/duration → equity default
    if _match_keywords(
        name,
        ["T-Bill", "Treasury Bills", "0-3 Month", "Ultra Short Treasury", "Money Market", "Cash", "UltraShort"],
    ):
        return EtfClassification(
            asset_class="cash",
            subtype="t_bill" if "bill" in name_l else "ultra_short_bond",
            sector="none",
            main_risk_factor="short_rates",
            secondary_risk_factors=[],
            region="US",
            currency_exposure="USD",
            duration_bucket="none",
            credit_quality="none",
            risk_role=["cash_like", "liquidity"],
            thematic_primary="none",
            thematic_tags=[],
            stress_block="CA",
            classification_method=method,
            classification_confidence="medium" if hybrid_flags else "high",
            needs_review=needs_review,
            warnings=warnings + hybrid_flags,
            hybrid_flags=hybrid_flags,
        )

    if _match_keywords(name, ["TIPS", "Inflation Protected", "Inflation-Linked", "Inflation Protected Bond"]):
        return EtfClassification(
            asset_class="fixed_income",
            subtype="tips",
            sector="none",
            main_risk_factor="inflation",
            secondary_risk_factors=["real_rates"],
            region="US",
            currency_exposure="USD",
            duration_bucket="intermediate",
            credit_quality="Treasury",
            risk_role=["inflation_hedge", "duration"],
            thematic_primary="none",
            thematic_tags=[],
            stress_block="TI",
            classification_method=method,
            classification_confidence="medium" if hybrid_flags else "high",
            needs_review=needs_review,
            warnings=warnings + hybrid_flags,
            hybrid_flags=hybrid_flags,
        )

    if _match_keywords(
        name,
        [
            "High Yield",
            " HY ",
            "Junk",
            "Corporate Bond",
            "Investment Grade Corporate",
            "Bank Loan",
            "Senior Loan",
            "Floating Rate",
            "EM Debt",
            "Emerging Markets Bond",
            "High-Yield",
        ],
    ):
        cq = "HY" if _match_keywords(name, ["High Yield", "Junk", " HY", "High-Yield"]) else "IG"
        if _match_keywords(name, ["EM Debt", "Emerging Markets Bond"]):
            cq = "EM_debt"
        if _match_keywords(name, ["Bank Loan", "Senior Loan", "Floating Rate"]):
            subtype = "bank_loan" if "bank loan" in name_l or "senior loan" in name_l else "floating_rate"
        elif _match_keywords(name, ["High Yield", "Junk", " HY", "High-Yield"]):
            subtype = "high_yield"
        else:
            subtype = "corporate_ig"
        return EtfClassification(
            asset_class="fixed_income",
            subtype=subtype,
            sector="none",
            main_risk_factor="credit",
            secondary_risk_factors=["usd"],
            region="US" if "EM" not in name.upper() else "EM",
            currency_exposure="USD",
            duration_bucket="intermediate",
            credit_quality=cq,
            risk_role=["carry", "income"],
            thematic_primary="none",
            thematic_tags=[],
            stress_block="CR",
            classification_method=method,
            classification_confidence="medium" if hybrid_flags or subtype == "corporate_ig" else "high",
            needs_review=needs_review or subtype == "corporate_ig",
            warnings=warnings + hybrid_flags,
            hybrid_flags=hybrid_flags,
        )

    if _match_keywords(
        name,
        ["Gold", "Silver", "Commodity", "Commodities", "Oil", "Natural Gas", "Energy Futures", "Precious Metals", "Agriculture"],
    ):
        subtype = "gold" if "gold" in name_l else "commodity_etf"
        if "silver" in name_l:
            subtype = "silver"
        if _match_keywords(name, ["Oil", "Natural Gas", "Energy"]):
            subtype = "energy_commodity"
        return EtfClassification(
            asset_class="commodity",
            subtype=subtype,
            sector="none",
            main_risk_factor="commodity",
            secondary_risk_factors=["usd"],
            region="Global",
            currency_exposure="USD",
            duration_bucket="none",
            credit_quality="none",
            risk_role=["inflation_hedge", "diversifier"],
            thematic_primary="commodity_beta" if "energy" in name_l else "none",
            thematic_tags=["commodity"],
            stress_block="CO",
            classification_method=method,
            classification_confidence="medium" if hybrid_flags else "high",
            needs_review=needs_review,
            warnings=warnings + hybrid_flags,
            hybrid_flags=hybrid_flags,
        )

    if _match_keywords(
        name,
        ["Treasury", "Government Bond", "Aggregate Bond", "Core Bond", "Intermediate Treasury", "Long Treasury", "Short Treasury", "Aggregate"],
    ):
        subtype = "treasury" if "treasury" in name_l else "aggregate_bond"
        dur = "long" if "long" in name_l else ("short" if "short" in name_l else "intermediate")
        conf: ClassificationConfidence = "medium" if subtype == "aggregate_bond" or hybrid_flags else "high"
        return EtfClassification(
            asset_class="fixed_income",
            subtype=subtype,
            sector="none",
            main_risk_factor="real_rates",
            secondary_risk_factors=["inflation"],
            region="US",
            currency_exposure="USD",
            duration_bucket=dur,
            credit_quality="Treasury" if subtype == "treasury" else "Mixed",
            risk_role=["duration", "defensive"],
            thematic_primary="none",
            thematic_tags=[],
            stress_block="ND",
            classification_method=method,
            classification_confidence=conf,
            needs_review=needs_review or subtype == "aggregate_bond",
            warnings=warnings + hybrid_flags + (["Aggregate bond may blend credit and duration"] if subtype == "aggregate_bond" else []),
            hybrid_flags=hybrid_flags,
        )

    if _match_keywords(name, ["REIT", "Real Estate"]):
        return EtfClassification(
            asset_class="alternative",
            subtype="reit",
            sector="real_estate",
            main_risk_factor="real_rates",
            secondary_risk_factors=["equity"],
            region="US",
            currency_exposure="USD",
            duration_bucket="none",
            credit_quality="none",
            risk_role=["income", "diversifier"],
            thematic_primary="real_estate",
            thematic_tags=["reit"],
            stress_block="EQ",
            classification_method=method,
            classification_confidence="medium",
            needs_review=True,
            warnings=warnings + hybrid_flags + ["REIT: mapped to EQ for stress RC; verify manually"],
            hybrid_flags=hybrid_flags + (["mortgage_reit"] if "mortgage" in name_l else []),
        )

    # Equity ETFs (default bucket for ETF flag)
    subtype = "broad_market"
    sector = "multi_sector"
    thematic_primary = "none"
    thematic_tags: list[str] = []
    if _match_keywords(name, ["S&P 500", "SP 500", "S&P500"]):
        subtype = "broad_market"
    elif _match_keywords(name, ["Nasdaq", "NASDAQ-100", "QQQ"]):
        subtype = "growth"
    elif _match_keywords(name, ["Russell 2000", "Small Cap", "Small-Cap"]):
        subtype = "small_cap"
    elif _match_keywords(name, ["Russell", "Total Market", "Total Stock"]):
        subtype = "broad_market"
    elif _match_keywords(name, ["Sector", "Select Sector"]):
        subtype = "sector_etf"
    elif _match_keywords(name, ["Dividend"]):
        subtype = "dividend"
    elif _match_keywords(name, ["Growth"]):
        subtype = "growth"
    elif _match_keywords(name, ["Value"]):
        subtype = "value"
    elif _match_keywords(name, ["Semiconductor", "Cyber", "AI", "Robotics", "Cloud"]):
        subtype = "thematic_etf"
        thematic_primary = "technology"
        thematic_tags = ["thematic"]

    if hybrid_flags:
        confidence = "low" if any(f in hybrid_flags for f in ("leveraged", "inverse", "crypto", "volatility")) else "medium"
        needs_review = True
    else:
        confidence = "high"

    return EtfClassification(
        asset_class="equity",
        subtype=subtype,
        sector=sector,
        main_risk_factor="equity",
        secondary_risk_factors=["us_growth"],
        region="US",
        currency_exposure="USD",
        duration_bucket="none",
        credit_quality="none",
        risk_role=["risk_on", "growth"],
        thematic_primary=thematic_primary,
        thematic_tags=thematic_tags,
        stress_block="EQ",
        classification_method=method,
        classification_confidence=confidence,
        needs_review=needs_review,
        warnings=warnings + hybrid_flags,
        hybrid_flags=hybrid_flags,
    )


def build_draft_etf_row(raw: dict[str, Any], clf: EtfClassification) -> dict[str, Any]:
    ticker = _upper_ticker(raw["ticker"])
    name = str(raw.get("name") or ticker)
    issuer = _infer_issuer(name)
    sources = ",".join(raw.get("sources") or [])
    notes = (
        f"Ingested from public listing sources ({sources}). "
        f"Rule-based classification; review before merge to production."
    )
    if clf.hybrid_flags:
        notes += f" Hybrid flags: {', '.join(clf.hybrid_flags)}."

    return {
        "ticker": ticker,
        "name": name,
        "issuer": issuer,
        "asset_class": clf.asset_class,
        "subtype": clf.subtype,
        "sector": clf.sector,
        "thematic_primary": clf.thematic_primary,
        "thematic_tags": clf.thematic_tags,
        "risk_role": clf.risk_role,
        "main_risk_factor": clf.main_risk_factor,
        "secondary_risk_factors": clf.secondary_risk_factors,
        "region": clf.region,
        "currency_exposure": clf.currency_exposure,
        "duration_bucket": clf.duration_bucket,
        "credit_quality": clf.credit_quality,
        "duplicate_group_id": f"ingestion_{ticker.lower()}",
        "canonical_ticker": ticker,
        "data_source": ["public_listing_ingestion"],
        "notes": notes,
    }


def build_draft_stock_row(
    raw: dict[str, Any],
    *,
    sector_lookup: dict[str, dict[str, str]] | None = None,
) -> dict[str, Any]:
    ticker = _upper_ticker(raw["ticker"])
    name = str(raw.get("sec_name") or raw.get("name") or ticker)
    sources = ",".join(raw.get("sources") or [])
    sector = "Unknown"
    industry = "Unknown"
    enrichment_source = ""
    index_membership: list[str] = []
    if sector_lookup and ticker in sector_lookup:
        sector = sector_lookup[ticker].get("sector") or sector
        industry = sector_lookup[ticker].get("industry") or industry
        enrichment_source = sector_lookup[ticker].get("source") or "production_universe"
        index_membership = list(sector_lookup[ticker].get("index_membership_list") or [])
    notes = f"Ingested from public listing sources ({sources})."
    if enrichment_source:
        notes += f" Sector/industry from {enrichment_source}."
    else:
        notes += " Sector/industry require enrichment (production lookup or --enrich-sectors-yahoo)."
    return {
        "ticker": ticker,
        "company_name": name,
        "asset_class": "equity",
        "sector": sector,
        "industry": industry,
        "thematic_tags": [],
        "region": "US",
        "currency_exposure": "USD",
        "main_risk_factor": "equity",
        "secondary_risk_factors": ["us_growth"],
        "risk_role": ["risk_on"],
        "index_membership": index_membership,
        "notes": notes,
    }


def load_production_stock_sector_lookup(
    stock_path: str | Path | None = None,
) -> dict[str, dict[str, str]]:
    """Build ticker → sector/industry map from production stock_universe.yml."""
    from src.stock_universe import load_stock_universe

    root = Path(__file__).resolve().parent.parent
    path = Path(stock_path) if stock_path else root / "config" / "stock_universe.yml"
    lookup: dict[str, dict[str, str]] = {}
    for row in load_stock_universe(path):
        t = _upper_ticker(row.get("ticker"))
        if not t:
            continue
        membership = row.get("index_membership")
        lookup[t] = {
            "sector": str(row.get("sector") or ""),
            "industry": str(row.get("industry") or ""),
            "index_membership_list": list(membership) if isinstance(membership, list) else [],
            "source": "production_universe",
        }
    return lookup


def _normalize_yahoo_sector(sector: str | None) -> str:
    if not sector or not str(sector).strip():
        return "Unknown"
    s = str(sector).strip()
    return _YAHOO_SECTOR_TO_GICS.get(s, s)


def enrich_stock_sector_yahoo(ticker: str, *, max_retries: int = 3) -> dict[str, str]:
    """Fetch sector/industry for one ticker via yfinance (best-effort)."""
    import time

    try:
        import yfinance as yf
    except ImportError:
        return {"sector": "Unknown", "industry": "Unknown", "source": "yahoo_unavailable"}
    info: dict = {}
    for attempt in range(max_retries):
        try:
            info = yf.Ticker(ticker).info or {}
            break
        except Exception as exc:
            msg = str(exc).lower()
            if "too many requests" in msg or "rate limit" in msg:
                time.sleep(min(60.0, 5.0 * (2**attempt)))
                continue
            return {"sector": "Unknown", "industry": "Unknown", "source": "yahoo_error"}
    else:
        return {"sector": "Unknown", "industry": "Unknown", "source": "yahoo_rate_limited"}
    sector = _normalize_yahoo_sector(info.get("sector"))
    industry = str(info.get("industry") or "Unknown").strip() or "Unknown"
    if sector == "Unknown" and industry == "Unknown":
        return {"sector": "Unknown", "industry": "Unknown", "source": "yahoo_empty"}
    return {"sector": sector, "industry": industry, "source": "yahoo_finance"}


def enrich_draft_stocks(
    stocks: list[dict[str, Any]],
    *,
    production_lookup: dict[str, dict[str, str]] | None = None,
    use_yahoo: bool = False,
    yahoo_limit: int | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Enrich draft stock rows: production lookup first, optional yfinance for Unknown rows.
    """
    lookup = production_lookup or load_production_stock_sector_lookup()
    enriched: list[dict[str, Any]] = []
    stats = Counter()
    yahoo_calls = 0

    for row in stocks:
        rec = dict(row)
        t = _upper_ticker(rec.get("ticker"))
        if t in lookup:
            rec["sector"] = lookup[t].get("sector") or rec.get("sector")
            rec["industry"] = lookup[t].get("industry") or rec.get("industry")
            if lookup[t].get("index_membership_list"):
                rec["index_membership"] = list(lookup[t]["index_membership_list"])
            stats["from_production"] += 1
        elif str(rec.get("sector") or "") in ("", "Unknown") and use_yahoo:
            if yahoo_limit is not None and yahoo_calls >= yahoo_limit:
                stats["yahoo_skipped_limit"] += 1
            else:
                yahoo_calls += 1
                meta = enrich_stock_sector_yahoo(t)
                if meta.get("sector") not in ("", "Unknown"):
                    rec["sector"] = meta["sector"]
                if meta.get("industry") not in ("", "Unknown"):
                    rec["industry"] = meta["industry"]
                rec["notes"] = (rec.get("notes") or "") + f" Yahoo enrichment: {meta.get('source')}."
                stats[meta.get("source", "yahoo")] += 1
        if str(rec.get("sector") or "") in ("", "Unknown"):
            stats["still_unknown_sector"] += 1
        enriched.append(rec)

    return enriched, {
        "enriched_count": len(enriched),
        "stats": dict(stats),
        "yahoo_calls": yahoo_calls,
    }


def validate_draft_etf_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate draft ETF rows using production validator."""
    return validate_etf_universe(records)


def validate_draft_stock_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Validate draft stock rows with production rules except index_membership
    (empty list allowed for non-SP500 ingested names).
    """
    sp500_only = [r for r in records if r.get("index_membership") == ["SP500"]]
    if sp500_only:
        prod = validate_stock_universe(sp500_only)
    else:
        prod = {"status": "PASS", "errors": [], "warnings": [], "summary": {"error_count": 0, "warning_count": 0}}

    structural_errors: list[dict[str, Any]] = []
    for rec in records:
        t = _upper_ticker(rec.get("ticker"))
        for fld in ("ticker", "company_name", "asset_class", "region", "currency_exposure", "main_risk_factor"):
            if not rec.get(fld):
                structural_errors.append({"code": "missing_field", "ticker": t, "field": fld})
        if rec.get("index_membership") is not None and not isinstance(rec.get("index_membership"), list):
            structural_errors.append({"code": "invalid_list", "ticker": t, "field": "index_membership"})

    status = prod.get("status", "PASS")
    if structural_errors:
        status = "FAIL"
    elif records and all(not r.get("index_membership") for r in records):
        status = "PASS_WITH_WARNINGS" if status == "PASS" else status

    warnings = list(prod.get("warnings") or [])
    if any(not r.get("index_membership") for r in records):
        warnings.append(
            {
                "code": "draft_index_membership_empty",
                "message": "Draft ingested stocks have empty index_membership; production requires SP500",
            }
        )

    return {
        "status": status,
        "errors": list(prod.get("errors") or []) + structural_errors,
        "warnings": warnings,
        "summary": {
            "error_count": len(prod.get("errors") or []) + len(structural_errors),
            "warning_count": len(warnings),
            "draft_mode": True,
        },
    }


def _readiness_for_row(
    draft_row: dict[str, Any],
    *,
    universe_source: Literal["etf_universe", "stock_universe"],
    meta: dict[str, Any],
) -> dict[str, Any]:
    resolution = derive_stress_block_from_taxonomy_row(draft_row, universe_source=universe_source)
    conf, needs_review, warnings = assess_classification(
        row=draft_row,
        universe_source=universe_source,
        resolution=resolution,
        taxonomy_summary={
            k: draft_row.get(k)
            for k in (
                "asset_class",
                "subtype",
                "main_risk_factor",
                "credit_quality",
                "region",
                "currency_exposure",
            )
            if k in draft_row
        },
    )
    if meta.get("classification_confidence"):
        conf = meta["classification_confidence"]
    if meta.get("needs_review"):
        needs_review = True
    silent_default = resolution.source == "unknown"
    return {
        "ticker": draft_row.get("ticker"),
        "stress_block": resolution.block,
        "stress_block_source": resolution.source,
        "silent_default_eq": silent_default,
        "classification_method": meta.get("classification_method"),
        "classification_confidence": conf,
        "needs_review": needs_review,
        "warnings": list(set((meta.get("warnings") or []) + warnings)),
        "xray_ready_hint": "Validate draft row against etf/stock universe schema",
        "rc_ready": not silent_default and conf != "low" and not needs_review,
        "pnl_ready_hint": "Requires price history and factor beta estimation during portfolio review",
    }


def run_ingestion_pipeline(
    *,
    nasdaq_listed_source: str,
    other_listed_source: str,
    sec_tickers_source: str,
    output_dir: Path | None = None,
    dry_run: bool = False,
    limit: int | None = None,
    enrich_sectors_yahoo: bool = False,
    enrich_sectors_yahoo_limit: int | None = None,
    production_stock_path: str | Path | None = None,
) -> dict[str, Any]:
    """Full staged ingestion pipeline."""
    sector_lookup = load_production_stock_sector_lookup(production_stock_path)
    nasdaq_text = fetch_source(nasdaq_listed_source)
    other_text = fetch_source(other_listed_source)
    sec_text = fetch_source(sec_tickers_source)

    nasdaq_rows = parse_nasdaqlisted_text(nasdaq_text)
    other_rows = parse_otherlisted_text(other_text)
    sec_rows = parse_sec_company_tickers_json(sec_text)

    total_downloaded = len(nasdaq_rows) + len(other_rows) + len(sec_rows)
    raw_by = _merge_raw_rows(nasdaq_rows + other_rows + sec_rows)
    clean = clean_raw_universe(raw_by)

    all_candidates = clean.kept + clean.flagged
    if limit is not None:
        all_candidates = all_candidates[:limit]

    draft_etfs: list[dict[str, Any]] = []
    draft_stocks: list[dict[str, Any]] = []
    per_ticker_meta: dict[str, dict[str, Any]] = {}
    needs_review_rows: list[dict[str, Any]] = []

    for raw in all_candidates:
        kind = raw.get("security_kind_guess")
        if kind == "etf":
            clf = classify_etf(str(raw.get("name") or ""), etf_flag=bool(raw.get("etf_flag")))
            draft = build_draft_etf_row(raw, clf)
            draft_etfs.append(draft)
            meta = {
                "classification_method": clf.classification_method,
                "classification_confidence": clf.classification_confidence,
                "needs_review": clf.needs_review,
                "warnings": clf.warnings,
                "security_kind": "etf",
            }
            per_ticker_meta[draft["ticker"]] = meta
        elif kind == "stock":
            draft = build_draft_stock_row(raw, sector_lookup=sector_lookup)
            draft_stocks.append(draft)
            hybrid = _detect_hybrid_flags(str(raw.get("name") or ""))
            meta = {
                "classification_method": "source_metadata",
                "classification_confidence": "low" if hybrid else "high",
                "needs_review": bool(hybrid),
                "warnings": hybrid,
                "security_kind": "stock",
            }
            per_ticker_meta[draft["ticker"]] = meta
        else:
            meta = {
                "classification_method": "manual_required",
                "classification_confidence": "low",
                "needs_review": True,
                "warnings": ["unclear_security_type"],
                "security_kind": "unknown",
            }
            per_ticker_meta[_upper_ticker(raw["ticker"])] = meta

    enrichment_summary: dict[str, Any] = {}
    if draft_stocks and enrich_sectors_yahoo:
        draft_stocks, enrichment_summary = enrich_draft_stocks(
            draft_stocks,
            production_lookup=sector_lookup,
            use_yahoo=True,
            yahoo_limit=enrich_sectors_yahoo_limit,
        )

    readiness: list[dict[str, Any]] = []
    for rec in draft_etfs:
        meta = per_ticker_meta.get(rec["ticker"], {})
        rd = _readiness_for_row(rec, universe_source="etf_universe", meta=meta)
        readiness.append(rd)
        if rd["needs_review"]:
            needs_review_rows.append({**rec, **meta, **rd, "universe": "etf"})
    for rec in draft_stocks:
        meta = per_ticker_meta.get(rec["ticker"], {})
        rd = _readiness_for_row(rec, universe_source="stock_universe", meta=meta)
        readiness.append(rd)
        if rd["needs_review"]:
            needs_review_rows.append({**rec, **meta, **rd, "universe": "stock"})

    etf_val = validate_draft_etf_records(draft_etfs) if draft_etfs else {"status": "PASS", "errors": [], "warnings": []}
    stock_val = validate_draft_stock_records(draft_stocks) if draft_stocks else {"status": "PASS", "errors": [], "warnings": []}

    warning_categories = Counter()
    for r in readiness:
        for w in r.get("warnings") or []:
            warning_categories[str(w)] += 1
    for row in clean.removed:
        warning_categories[row.get("disposition_reason", "removed")] += 1

    silent_default_eq_count = sum(1 for r in readiness if r.get("silent_default_eq"))
    low_confidence_count = sum(1 for r in readiness if r.get("classification_confidence") == "low")

    report: dict[str, Any] = {
        "version": "universe_ingestion_v1",
        "dry_run": dry_run,
        "sources": {
            "nasdaq_listed": nasdaq_listed_source,
            "other_listed": other_listed_source,
            "sec_company_tickers": sec_tickers_source,
        },
        "counts": {
            "total_rows_downloaded": total_downloaded,
            "unique_tickers_raw": len(raw_by),
            "rows_kept": len(clean.kept),
            "rows_removed": len(clean.removed),
            "rows_flagged": len(clean.flagged),
            "draft_etfs": len(draft_etfs),
            "draft_stocks": len(draft_stocks),
            "unknown_security_types": sum(1 for r in all_candidates if r.get("security_kind_guess") == "unknown"),
            "duplicates_merged": total_downloaded - len(raw_by),
            "needs_review_count": len(needs_review_rows),
            "low_confidence_count": low_confidence_count,
            "silent_default_eq_count": silent_default_eq_count,
        },
        "validation": {
            "draft_etf_universe": {"status": etf_val.get("status"), "error_count": len(etf_val.get("errors") or [])},
            "draft_stock_universe": {"status": stock_val.get("status"), "error_count": len(stock_val.get("errors") or [])},
            "production_files_modified": False,
        },
        "top_warning_categories": warning_categories.most_common(20),
        "removed_sample": clean.removed[:50],
        "readiness": readiness,
        "pnl_readiness_note": "Synthetic PnL requires price history and factor beta estimation during portfolio review; not confirmed by ingestion alone.",
        "rc_readiness_note": "Synthetic RC requires valid stress block, non-low confidence, and needs_review=false.",
        "stock_enrichment": enrichment_summary,
    }

    if output_dir is not None and not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        raw_df = pd.DataFrame(list(raw_by.values()))
        raw_df.to_csv(output_dir / "raw_us_universe.csv", index=False)

        clean_rows = clean.kept + clean.flagged + clean.removed
        pd.DataFrame(clean_rows).to_csv(output_dir / "clean_us_universe.csv", index=False)

        _write_draft_yaml(draft_stocks, output_dir / "draft_stock_universe.yml")
        _write_draft_yaml(draft_etfs, output_dir / "draft_etf_universe.yml")

        if needs_review_rows:
            pd.DataFrame(needs_review_rows).to_csv(output_dir / "needs_review.csv", index=False)
        else:
            pd.DataFrame(columns=["ticker"]).to_csv(output_dir / "needs_review.csv", index=False)

        with (output_dir / "ingestion_report.json").open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    return report


def _write_draft_yaml(records: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write("# DRAFT — do not merge without manual review\n")
        f.write("# Generated by scripts/ingest_us_listed_universe.py\n")
        for rec in records:
            row = {k: v for k, v in rec.items() if k != "notes" or v}
            f.write("- ")
            f.write(yaml.dump(row, default_flow_style=True, allow_unicode=True).strip())
            f.write("\n")


__all__ = [
    "DEFAULT_NASDAQ_LISTED_URL",
    "DEFAULT_OTHER_LISTED_URL",
    "DEFAULT_SEC_TICKERS_URL",
    "DEFAULT_SEC_USER_AGENT",
    "classify_etf",
    "clean_raw_universe",
    "enrich_draft_stocks",
    "enrich_stock_sector_yahoo",
    "fetch_source",
    "load_production_stock_sector_lookup",
    "parse_nasdaqlisted_text",
    "parse_otherlisted_text",
    "parse_sec_company_tickers_json",
    "run_ingestion_pipeline",
    "validate_draft_etf_records",
    "validate_draft_stock_records",
]
