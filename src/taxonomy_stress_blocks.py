"""
Taxonomy onboarding helpers: stress block derivation and readiness reports.

See docs/specs/asset_taxonomy_onboarding_spec.md.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from src.etf_universe import (
    check_config_tickers,
    load_etf_universe,
    validate_etf_universe,
)
from src.stock_universe import load_stock_universe, validate_stock_universe
from src.stress_covariance_taxonomy import (
    BLOCK_CA,
    BLOCK_CO,
    BLOCK_CR,
    BLOCK_EQ,
    BLOCK_ND,
    BLOCK_TI,
    TaxonomyResolution,
    _block_from_etf_row,
    resolve_stress_asset_block,
)

ClassificationConfidence = Literal["high", "medium", "low"]
UniverseSource = Literal["etf_universe", "stock_universe", "missing"]

HYBRID_SUBTYPES = frozenset(
    {
        "multi_asset",
        "covered_call",
        "managed_futures",
        "volatility_etf",
        "tail_risk",
        "preferred",
        "infrastructure",
    }
)
LOW_CONFIDENCE_SUBTYPES = frozenset(
    {
        "bitcoin_spot",
        "ether_spot",
    }
)


def _upper_ticker(t: str | None) -> str:
    return str(t or "").strip().upper()


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_universe_maps(
    *,
    etf_path: str | Path | None = None,
    stock_path: str | Path | None = None,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    root = _project_root()
    ep = Path(etf_path) if etf_path else root / "config" / "etf_universe.yml"
    sp = Path(stock_path) if stock_path else root / "config" / "stock_universe.yml"
    etf_records = load_etf_universe(ep)
    stock_records = load_stock_universe(sp)
    etf_by = {_upper_ticker(r.get("ticker")): r for r in etf_records if _upper_ticker(r.get("ticker"))}
    stock_by = {_upper_ticker(r.get("ticker")): r for r in stock_records if _upper_ticker(r.get("ticker"))}
    return etf_by, stock_by


def lookup_universe_row(
    ticker: str,
    etf_by: dict[str, dict[str, Any]],
    stock_by: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any] | None, UniverseSource]:
    t = _upper_ticker(ticker)
    if t in etf_by:
        return etf_by[t], "etf_universe"
    if t in stock_by:
        return stock_by[t], "stock_universe"
    return None, "missing"


def derive_stress_block_from_taxonomy_row(
    row: dict[str, Any],
    *,
    universe_source: UniverseSource,
    ticker: str | None = None,
    cash_proxy_ticker: str | None = None,
) -> TaxonomyResolution:
    """
    Resolve stress RC block from an in-memory taxonomy row (draft or production).
    """
    t = _upper_ticker(ticker or row.get("ticker"))
    cash_u = (cash_proxy_ticker or "").strip().upper()
    if cash_u and t == cash_u:
        return TaxonomyResolution(ticker=t, block=BLOCK_CA, source="cash_proxy")
    if universe_source == "stock_universe":
        return TaxonomyResolution(ticker=t, block=BLOCK_EQ, source="stock_universe")
    if universe_source == "etf_universe":
        return TaxonomyResolution(ticker=t, block=_block_from_etf_row(row, t), source="etf_universe")
    return TaxonomyResolution(ticker=t, block=BLOCK_EQ, source="unknown")


def derive_stress_block_for_ticker(
    ticker: str,
    *,
    cash_proxy_ticker: str | None = None,
    etf_path: str | Path | None = None,
    stock_path: str | Path | None = None,
    etf_by: dict[str, dict[str, Any]] | None = None,
    stock_by: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Resolve stress RC block (EQ/CR/ND/TI/CO/CA) and taxonomy provenance for one ticker.
    """
    if etf_by is None or stock_by is None:
        etf_by, stock_by = load_universe_maps(etf_path=etf_path, stock_path=stock_path)

    row, universe_source = lookup_universe_row(ticker, etf_by, stock_by)
    resolution: TaxonomyResolution = resolve_stress_asset_block(
        ticker,
        cash_proxy_ticker=cash_proxy_ticker,
        etf_path=str(etf_path) if etf_path else None,
        stock_path=str(stock_path) if stock_path else None,
    )

    silent_default_eq = resolution.source == "unknown"
    stress_block_source = resolution.source

    taxonomy_summary: dict[str, Any] = {}
    if row:
        for key in (
            "asset_class",
            "subtype",
            "sector",
            "main_risk_factor",
            "secondary_risk_factors",
            "risk_role",
            "credit_quality",
            "duration_bucket",
            "region",
            "currency_exposure",
        ):
            if key in row:
                taxonomy_summary[key] = row.get(key)

    confidence, needs_review, warnings = assess_classification(
        row=row,
        universe_source=universe_source,
        resolution=resolution,
        taxonomy_summary=taxonomy_summary,
    )

    xray_ready = _xray_ready(row, universe_source, etf_by, stock_by, ticker)
    rc_ready = not silent_default_eq and confidence != "low"
    pnl_ready_hint = (
        "Run portfolio review or stress report and confirm weekly factor betas / "
        "synthetic_assumptions in stress_report.json (not checked by this CLI)."
    )

    return {
        "ticker": _upper_ticker(ticker),
        "universe_source": universe_source,
        "taxonomy_row_present": row is not None,
        "taxonomy": taxonomy_summary,
        "stress_block": resolution.block,
        "stress_block_source": stress_block_source,
        "silent_default_eq": silent_default_eq,
        "classification_confidence": confidence,
        "needs_review": needs_review,
        "warnings": warnings,
        "xray_ready": xray_ready,
        "rc_ready": rc_ready,
        "pnl_ready_hint": pnl_ready_hint,
    }


def assess_classification(
    *,
    row: dict[str, Any] | None,
    universe_source: UniverseSource,
    resolution: TaxonomyResolution,
    taxonomy_summary: dict[str, Any],
) -> tuple[ClassificationConfidence, bool, list[str]]:
    warnings: list[str] = []

    if universe_source == "missing":
        warnings.append("Ticker absent from etf_universe.yml and stock_universe.yml; stress RC uses default EQ.")
        return "low", True, warnings

    if row is None:
        return "low", True, warnings

    asset_class = str(row.get("asset_class") or "").strip().lower()
    subtype = str(row.get("subtype") or "").strip().lower()
    main_rf = str(row.get("main_risk_factor") or "").strip().lower()
    block = resolution.block

    warnings.extend(_taxonomy_block_consistency_warnings(row, block))

    if subtype in LOW_CONFIDENCE_SUBTYPES or asset_class == "crypto":
        warnings.append("Crypto-related product: verify factor beta coverage and stress block manually.")
        return "low", True, warnings

    if "leveraged" in subtype or "inverse" in subtype:
        warnings.append("Leveraged/inverse product: low confidence for taxonomy and factor betas.")
        return "low", True, warnings

    if asset_class == "alternative" or subtype in HYBRID_SUBTYPES:
        warnings.append("Hybrid/alternative product: document secondary risks in notes.")
        return "medium", True, warnings

    if asset_class == "fixed_income" and subtype == "aggregate_bond":
        warnings.append("Aggregate bond fund may blend duration and credit; confirm CR vs ND mapping.")
        return "medium", True, warnings

    if subtype == "reit":
        warnings.append("REIT: mapped to EQ for stress RC; rates sensitivity may remain in factor betas.")

    if warnings and any("default EQ" in w for w in warnings):
        return "low", True, warnings

    if warnings:
        return "medium", True, warnings

    return "high", False, warnings


def _taxonomy_block_consistency_warnings(row: dict[str, Any], block: str) -> list[str]:
    """Flag obvious mismatches between YAML tags and derived stress block."""
    warnings: list[str] = []
    ac = str(row.get("asset_class") or "").strip().lower()
    st = str(row.get("subtype") or "").strip().lower()
    main_rf = str(row.get("main_risk_factor") or "").strip().lower()
    cq = str(row.get("credit_quality") or "").strip()

    if ac == "commodity" and block != BLOCK_CO:
        warnings.append(f"asset_class=commodity but stress block is {block}; expected CO.")
    if ac == "cash" and block != BLOCK_CA:
        warnings.append(f"asset_class=cash but stress block is {block}; expected CA.")
    if ac == "equity" and block not in (BLOCK_EQ,):
        warnings.append(f"asset_class=equity but stress block is {block}; expected EQ.")
    if st == "tips" and block != BLOCK_TI:
        warnings.append(f"subtype=tips but stress block is {block}; expected TI.")
    if st in ("high_yield", "corporate_ig", "em_debt", "bank_loan") and block != BLOCK_CR:
        warnings.append(f"Credit-sensitive subtype={st} but stress block is {block}; expected CR.")
    if main_rf == "credit" and block != BLOCK_CR:
        warnings.append(f"main_risk_factor=credit but stress block is {block}; expected CR.")
    if main_rf == "inflation" and block != BLOCK_TI:
        warnings.append(f"main_risk_factor=inflation but stress block is {block}; expected TI.")
    if cq in ("HY", "Junk", "EM_debt") and block != BLOCK_CR:
        warnings.append(f"credit_quality={cq} but stress block is {block}; expected CR.")
    if ac == "fixed_income" and st == "aggregate_bond" and block == BLOCK_CR:
        warnings.append("Aggregate bond mapped to CR; confirm credit vs duration dominance.")
    return warnings


def _xray_ready(
    row: dict[str, Any] | None,
    universe_source: UniverseSource,
    etf_by: dict[str, dict[str, Any]],
    stock_by: dict[str, dict[str, Any]],
    ticker: str,
) -> bool:
    if row is None:
        return False
    t = _upper_ticker(ticker)
    if universe_source == "etf_universe":
        recs = [row]
        val = validate_etf_universe(recs)
        ticker_errors = [e for e in val.get("errors", []) if e.get("ticker") == t or t in (e.get("tickers") or [])]
        return val.get("status") != "FAIL" and not ticker_errors
    if universe_source == "stock_universe":
        val = validate_stock_universe([row])
        return val.get("status") != "FAIL" and not val.get("errors")
    return False


def build_onboard_report(
    tickers: list[str],
    *,
    cash_proxy_ticker: str | None = None,
    config_path: str | Path | None = None,
    etf_path: str | Path | None = None,
    stock_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build full onboarding report for one or more tickers."""
    etf_by, stock_by = load_universe_maps(etf_path=etf_path, stock_path=stock_path)
    normalized = [_upper_ticker(t) for t in tickers if _upper_ticker(t)]

    per_ticker = [
        derive_stress_block_for_ticker(
            t,
            cash_proxy_ticker=cash_proxy_ticker,
            etf_path=etf_path,
            stock_path=stock_path,
            etf_by=etf_by,
            stock_by=stock_by,
        )
        for t in normalized
    ]

    etf_records = list(etf_by.values())
    stock_records = list(stock_by.values())
    etf_val = validate_etf_universe(etf_records)
    stock_val = validate_stock_universe(stock_records)

    config_unknown: list[str] = []
    if config_path:
        import yaml

        cfg_path = Path(config_path)
        if cfg_path.is_file():
            with cfg_path.open(encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            cfg_tickers = [_upper_ticker(t) for t in (data.get("tickers") or []) if _upper_ticker(t)]
            chk = check_config_tickers(cfg_tickers, etf_records)
            config_unknown = sorted(set(chk.get("unknown_tickers") or []) & set(normalized))

    return {
        "version": "taxonomy_onboard_report_v1",
        "tickers": normalized,
        "cash_proxy_ticker": cash_proxy_ticker,
        "per_ticker": per_ticker,
        "validators": {
            "etf_universe": {
                "status": etf_val.get("status"),
                "error_count": etf_val.get("summary", {}).get("error_count"),
                "warning_count": etf_val.get("summary", {}).get("warning_count"),
            },
            "stock_universe": {
                "status": stock_val.get("status"),
                "error_count": stock_val.get("summary", {}).get("error_count"),
                "warning_count": stock_val.get("summary", {}).get("warning_count"),
            },
            "config_unknown_among_input": config_unknown,
        },
        "summary": {
            "count": len(per_ticker),
            "rc_ready_count": sum(1 for r in per_ticker if r.get("rc_ready")),
            "xray_ready_count": sum(1 for r in per_ticker if r.get("xray_ready")),
            "needs_review_count": sum(1 for r in per_ticker if r.get("needs_review")),
            "silent_default_eq_count": sum(1 for r in per_ticker if r.get("silent_default_eq")),
        },
    }


__all__ = [
    "assess_classification",
    "build_onboard_report",
    "derive_stress_block_for_ticker",
    "derive_stress_block_from_taxonomy_row",
    "load_universe_maps",
    "lookup_universe_row",
]
