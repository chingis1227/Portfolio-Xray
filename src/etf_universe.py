"""ETF universe taxonomy loading, validation, diagnostics, and exports."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

STATUS_PASS = "PASS"
STATUS_PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
STATUS_FAIL = "FAIL"

DEFAULT_UNIVERSE_PATH = Path(__file__).resolve().parent.parent / "config" / "etf_universe.yml"

ASSET_CLASSES = {"equity", "fixed_income", "commodity", "cash", "alternative", "crypto"}
SUBTYPES = {
    "broad_market",
    "large_cap",
    "mid_cap",
    "small_cap",
    "regional_etf",
    "country_etf",
    "sector_etf",
    "thematic_etf",
    "factor_etf",
    "dividend",
    "growth",
    "value",
    "quality",
    "momentum",
    "low_volatility",
    "equal_weight",
    "treasury",
    "tips",
    "aggregate_bond",
    "corporate_ig",
    "high_yield",
    "em_debt",
    "floating_rate",
    "bank_loan",
    "preferred",
    "t_bill",
    "ultra_short_bond",
    "commodity_etf",
    "gold",
    "silver",
    "energy_commodity",
    "agriculture",
    "industrial_metals",
    "currency_etf",
    "reit",
    "infrastructure",
    "managed_futures",
    "volatility_etf",
    "tail_risk",
    "covered_call",
    "multi_asset",
    "bitcoin_spot",
    "ether_spot",
}
SECTORS = {
    "technology",
    "healthcare",
    "financials",
    "energy",
    "industrials",
    "utilities",
    "consumer_discretionary",
    "consumer_staples",
    "communication_services",
    "real_estate",
    "materials",
    "multi_sector",
    "none",
}
RISK_ROLES = {
    "risk_on",
    "defensive",
    "inflation_hedge",
    "duration",
    "liquidity",
    "cash_like",
    "crisis_hedge",
    "diversifier",
    "carry",
    "growth",
    "cyclical",
    "income",
    "volatility_hedge",
    "tail_hedge",
    "unknown",
}
RISK_FACTORS = {
    "equity",
    "real_rates",
    "inflation",
    "credit",
    "usd",
    "commodity",
    "vix",
    "us_growth",
    "short_rates",
    "liquidity",
    "crypto_beta",
}
REGIONS = {
    "US",
    "Europe",
    "EM",
    "Global",
    "China",
    "Japan",
    "Developed_ex_US",
    "Asia_ex_Japan",
    "LatAm",
    "Frontier",
    "Single_Country",
    "Canada",
    "Australia",
    "UK",
    "India",
}
CURRENCY_EXPOSURES = {"USD", "EUR", "JPY", "GBP", "CNY", "CAD", "AUD", "CHF", "local_EM", "hedged", "mixed"}
DURATION_BUCKETS = {"cash", "short", "intermediate", "long", "ultra_long", "floating", "none"}
CREDIT_QUALITIES = {"Treasury", "Agency", "IG", "HY", "EM_debt", "Mixed", "Unrated", "none"}
DATA_SOURCES = {"manual_seed", "issuer", "yahoo", "inferred"}

REQUIRED_FIELDS = {
    "ticker",
    "name",
    "issuer",
    "asset_class",
    "subtype",
    "sector",
    "thematic_primary",
    "thematic_tags",
    "risk_role",
    "main_risk_factor",
    "secondary_risk_factors",
    "region",
    "currency_exposure",
    "duration_bucket",
    "credit_quality",
    "duplicate_group_id",
    "canonical_ticker",
    "data_source",
}

OPTIONAL_METADATA_FIELDS = {"notes"}

FORBIDDEN_FIELDS = {
    "optimization_rule",
    "eligibility_bucket",
    "optimizer_rule",
    "allow_in_optimization",
    "block_in_optimization",
    "optimization_allowed",
    "eligible_for_optimization",
}

EXPORT_COLUMNS = [
    "ticker",
    "name",
    "issuer",
    "asset_class",
    "subtype",
    "sector",
    "thematic_primary",
    "thematic_tags",
    "risk_role",
    "main_risk_factor",
    "secondary_risk_factors",
    "region",
    "currency_exposure",
    "duration_bucket",
    "credit_quality",
    "duplicate_group_id",
    "canonical_ticker",
    "data_source",
    "hybrid_fixed_income_fields_allowed",
    "notes",
]


class UniverseValidationError(Exception):
    """Raised when an ETF universe source file cannot be parsed or validated."""


def _status(errors: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> str:
    if errors:
        return STATUS_FAIL
    if warnings:
        return STATUS_PASS_WITH_WARNINGS
    return STATUS_PASS


def _issue(code: str, message: str, ticker: str | None = None, **details: Any) -> dict[str, Any]:
    out: dict[str, Any] = {"code": code, "message": message}
    if ticker:
        out["ticker"] = ticker
    if details:
        out["details"] = details
    return out


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _upper_ticker(value: Any) -> str:
    return str(value or "").strip().upper()


def load_etf_universe(path: str | Path | None = None) -> list[dict[str, Any]]:
    """Load ETF universe YAML source as a list of mapping records."""
    universe_path = Path(path) if path is not None else DEFAULT_UNIVERSE_PATH
    try:
        with open(universe_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise UniverseValidationError(f"Malformed ETF universe YAML: {universe_path}: {exc}") from exc
    except OSError as exc:
        raise UniverseValidationError(f"ETF universe not readable: {universe_path}: {exc}") from exc

    if data is None:
        return []
    if not isinstance(data, list):
        raise UniverseValidationError(f"ETF universe must be a YAML list: {universe_path}")
    records: list[dict[str, Any]] = []
    for idx, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise UniverseValidationError(f"ETF universe row {idx} must be a mapping")
        row = dict(item)
        if row.get("ticker"):
            row["ticker"] = _upper_ticker(row["ticker"])
        if row.get("canonical_ticker"):
            row["canonical_ticker"] = _upper_ticker(row["canonical_ticker"])
        records.append(row)
    return records


def _validate_record(record: dict[str, Any], idx: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    ticker = _upper_ticker(record.get("ticker")) or f"row_{idx}"

    for field in sorted(FORBIDDEN_FIELDS & set(record)):
        errors.append(_issue("forbidden_field", f"Forbidden optimizer-specific field: {field}", ticker, field=field))

    for field in sorted(REQUIRED_FIELDS):
        if field not in record or _is_blank(record.get(field)):
            errors.append(_issue("missing_required_field", f"Missing required field: {field}", ticker, field=field))

    for field in sorted(OPTIONAL_METADATA_FIELDS):
        if field not in record or _is_blank(record.get(field)):
            warnings.append(_issue("missing_optional_metadata", f"Missing optional metadata: {field}", ticker, field=field))

    if errors:
        return errors, warnings

    enum_checks = [
        ("asset_class", ASSET_CLASSES),
        ("subtype", SUBTYPES),
        ("sector", SECTORS),
        ("main_risk_factor", RISK_FACTORS),
        ("region", REGIONS),
        ("currency_exposure", CURRENCY_EXPOSURES),
        ("duration_bucket", DURATION_BUCKETS),
        ("credit_quality", CREDIT_QUALITIES),
    ]
    for field, allowed in enum_checks:
        value = record.get(field)
        if value not in allowed:
            errors.append(_issue("invalid_enum", f"Invalid {field}: {value!r}", ticker, field=field, value=value))

    risk_role = record.get("risk_role")
    if not isinstance(risk_role, list) or not risk_role:
        errors.append(_issue("invalid_list", "risk_role must be a non-empty list", ticker, field="risk_role"))
    else:
        for value in risk_role:
            if value not in RISK_ROLES:
                errors.append(_issue("invalid_enum", f"Invalid risk_role: {value!r}", ticker, field="risk_role", value=value))

    thematic_tags = record.get("thematic_tags")
    if not isinstance(thematic_tags, list):
        errors.append(_issue("invalid_list", "thematic_tags must be a list", ticker, field="thematic_tags"))

    secondary = record.get("secondary_risk_factors")
    if not isinstance(secondary, list):
        errors.append(
            _issue("invalid_list", "secondary_risk_factors must be a list", ticker, field="secondary_risk_factors")
        )
    else:
        for value in secondary:
            if value in RISK_FACTORS:
                continue
            if isinstance(value, str) and value.startswith("tag:") and len(value) > 4:
                continue
            errors.append(
                _issue(
                    "invalid_enum",
                    f"Invalid secondary_risk_factors value: {value!r}",
                    ticker,
                    field="secondary_risk_factors",
                    value=value,
                )
            )

    sources = record.get("data_source")
    if not isinstance(sources, list) or not sources:
        errors.append(_issue("invalid_list", "data_source must be a non-empty list", ticker, field="data_source"))
    else:
        for value in sources:
            if value not in DATA_SOURCES:
                errors.append(_issue("invalid_enum", f"Invalid data_source: {value!r}", ticker, field="data_source", value=value))

    asset_class = record.get("asset_class")
    duration_bucket = record.get("duration_bucket")
    credit_quality = record.get("credit_quality")
    hybrid_allowed = bool(record.get("hybrid_fixed_income_fields_allowed", False))
    if asset_class == "fixed_income":
        if duration_bucket == "none" or credit_quality == "none":
            errors.append(
                _issue(
                    "fixed_income_fields_missing",
                    "fixed_income records require non-none duration_bucket and credit_quality",
                    ticker,
                )
            )
    elif duration_bucket != "none" or credit_quality != "none":
        if hybrid_allowed and not _is_blank(record.get("notes")):
            pass
        else:
            errors.append(
                _issue(
                    "non_fixed_income_fields_present",
                    "non-fixed-income records require duration_bucket=none and credit_quality=none unless hybrid exception is explicit",
                    ticker,
                )
            )

    if record.get("main_risk_factor") == "oil":
        errors.append(_issue("invalid_main_risk_factor", "oil is not allowed as a production main_risk_factor", ticker))

    return errors, warnings


def validate_etf_universe(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate ETF universe source records and return status, errors, warnings, and summary."""
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    tickers: dict[str, int] = {}
    canonical_refs: list[tuple[str, str]] = []

    for idx, record in enumerate(records, start=1):
        record_errors, record_warnings = _validate_record(record, idx)
        errors.extend(record_errors)
        warnings.extend(record_warnings)
        ticker = _upper_ticker(record.get("ticker"))
        if ticker:
            tickers[ticker] = tickers.get(ticker, 0) + 1
            canonical = _upper_ticker(record.get("canonical_ticker"))
            if canonical:
                canonical_refs.append((ticker, canonical))

    for ticker, count in sorted(tickers.items()):
        if count > 1:
            errors.append(_issue("duplicate_ticker", f"Duplicate ticker in ETF universe: {ticker}", ticker, count=count))

    ticker_set = set(tickers)
    for ticker, canonical in canonical_refs:
        if ticker != canonical and canonical not in ticker_set:
            errors.append(
                _issue(
                    "broken_canonical_reference",
                    f"canonical_ticker {canonical!r} is not present in universe",
                    ticker,
                    canonical_ticker=canonical,
                )
            )

    return {
        "status": _status(errors, warnings),
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "record_count": len(records),
            "unique_ticker_count": len(ticker_set),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
    }


def check_config_tickers(config_tickers: list[str], records: list[dict[str, Any]]) -> dict[str, Any]:
    """Check active config tickers against a structurally valid universe."""
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    by_ticker = {_upper_ticker(r.get("ticker")): r for r in records if _upper_ticker(r.get("ticker"))}
    normalized_tickers = [_upper_ticker(t) for t in config_tickers if _upper_ticker(t)]

    unknown = [t for t in normalized_tickers if t not in by_ticker]
    if unknown:
        warnings.append(
            _issue(
                "unknown_ticker",
                "Config contains tickers absent from ETF universe",
                tickers=sorted(unknown),
            )
        )

    duplicate_groups: dict[str, list[str]] = {}
    non_canonical: list[dict[str, str]] = []
    for ticker in normalized_tickers:
        record = by_ticker.get(ticker)
        if not record:
            continue
        group = str(record.get("duplicate_group_id") or "").strip()
        if group and group != "none":
            duplicate_groups.setdefault(group, []).append(ticker)
        canonical = _upper_ticker(record.get("canonical_ticker"))
        if canonical and ticker != canonical:
            non_canonical.append({"ticker": ticker, "canonical_ticker": canonical})

    duplicate_groups_in_config = {
        group: sorted(set(tickers))
        for group, tickers in duplicate_groups.items()
        if len(set(tickers)) > 1
    }
    if duplicate_groups_in_config:
        warnings.append(
            _issue(
                "duplicate_group_in_config",
                "Config contains multiple ETF tickers from the same duplicate exposure group",
                duplicate_groups=duplicate_groups_in_config,
            )
        )

    if non_canonical:
        warnings.append(
            _issue(
                "non_canonical_selection",
                "Config uses non-canonical ETF selections",
                selections=non_canonical,
            )
        )

    return {
        "status": _status(errors, warnings),
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "config_ticker_count": len(normalized_tickers),
            "known_ticker_count": len([t for t in normalized_tickers if t in by_ticker]),
            "unknown_ticker_count": len(unknown),
            "duplicate_group_count": len(duplicate_groups_in_config),
            "non_canonical_count": len(non_canonical),
        },
        "known_tickers": [t for t in normalized_tickers if t in by_ticker],
        "unknown_tickers": sorted(unknown),
        "duplicate_groups_in_config": duplicate_groups_in_config,
        "non_canonical_selections": non_canonical,
    }


def merge_diagnostics(*diagnostics: dict[str, Any]) -> dict[str, Any]:
    """Merge validation/check diagnostics into one status object."""
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    out: dict[str, Any] = {"components": []}
    for diag in diagnostics:
        if not diag:
            continue
        errors.extend(diag.get("errors") or [])
        warnings.extend(diag.get("warnings") or [])
        out["components"].append(diag)
    out["status"] = _status(errors, warnings)
    out["errors"] = errors
    out["warnings"] = warnings
    out["summary"] = {
        "error_count": len(errors),
        "warning_count": len(warnings),
    }
    return out


def build_universe_diagnostics(
    config_tickers: list[str] | None = None,
    universe_path: str | Path | None = None,
) -> dict[str, Any]:
    """Load and validate the universe, optionally checking a config ticker list."""
    path = Path(universe_path) if universe_path is not None else DEFAULT_UNIVERSE_PATH
    try:
        records = load_etf_universe(path)
    except UniverseValidationError as exc:
        return {
            "status": STATUS_FAIL,
            "errors": [_issue("malformed_yaml", str(exc))],
            "warnings": [],
            "summary": {"error_count": 1, "warning_count": 0, "record_count": 0},
            "universe_path": str(path),
        }

    validation = validate_etf_universe(records)
    validation["universe_path"] = str(path)
    if validation["status"] == STATUS_FAIL or config_tickers is None:
        return validation

    config_diag = check_config_tickers(config_tickers, records)
    merged = merge_diagnostics(validation, config_diag)
    merged["universe_path"] = str(path)
    return merged


def write_universe_diagnostics(
    output_dir: str | Path,
    config_tickers: list[str],
    universe_path: str | Path | None = None,
) -> Path | None:
    """Write `etf_universe_validation.json` when the source universe file exists."""
    path = Path(universe_path) if universe_path is not None else DEFAULT_UNIVERSE_PATH
    if not path.is_file():
        return None
    diagnostics = build_universe_diagnostics(config_tickers=config_tickers, universe_path=path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "etf_universe_validation.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(diagnostics, f, indent=2, ensure_ascii=False)
    if diagnostics.get("status") == STATUS_FAIL:
        raise UniverseValidationError(f"ETF universe validation failed; see {out_path}")
    return out_path


def _exportable_record(record: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for col in EXPORT_COLUMNS:
        value = record.get(col)
        if isinstance(value, list):
            value = "|".join(str(v) for v in value)
        out[col] = value
    return out


def export_universe(records: list[dict[str, Any]], output_path: str | Path, fmt: str) -> Path:
    """Export universe records as deterministic CSV or JSON."""
    fmt = fmt.lower()
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(records, key=lambda r: _upper_ticker(r.get("ticker")))
    if fmt == "csv":
        pd.DataFrame([_exportable_record(r) for r in ordered], columns=EXPORT_COLUMNS).to_csv(path, index=False)
    elif fmt == "json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(ordered, f, indent=2, ensure_ascii=False)
    else:
        raise ValueError("fmt must be 'csv' or 'json'")
    return path


def list_universe(
    records: list[dict[str, Any]],
    asset_class: str | None = None,
    risk_factor: str | None = None,
) -> list[dict[str, Any]]:
    """Filter universe records by asset class and/or main/secondary risk factor."""
    asset_class_filter = asset_class.strip() if asset_class else None
    risk_factor_filter = risk_factor.strip() if risk_factor else None
    out: list[dict[str, Any]] = []
    for record in records:
        if asset_class_filter and record.get("asset_class") != asset_class_filter:
            continue
        if risk_factor_filter:
            secondary = [str(v) for v in _as_list(record.get("secondary_risk_factors"))]
            if record.get("main_risk_factor") != risk_factor_filter and risk_factor_filter not in secondary:
                continue
        out.append(record)
    return sorted(out, key=lambda r: _upper_ticker(r.get("ticker")))


def default_export_path(fmt: str, output_dir: str | Path = "results_csv") -> Path:
    suffix = "csv" if fmt == "csv" else "json"
    return Path(output_dir) / f"etf_universe.{suffix}"
