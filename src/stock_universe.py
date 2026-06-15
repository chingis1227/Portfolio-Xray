"""Stock universe taxonomy loading, validation, diagnostics, and exports."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from src.yaml_cache import load_yaml_mtime_cached

from src.etf_universe import (
    FORBIDDEN_FIELDS,
    RISK_FACTORS,
    RISK_ROLES,
    STATUS_FAIL,
    STATUS_PASS,
    STATUS_PASS_WITH_WARNINGS,
    UniverseValidationError,
)

DEFAULT_UNIVERSE_PATH = Path(__file__).resolve().parent.parent / "config" / "stock_universe.yml"
ASSET_CLASSES = {"equity"}
INDEX_MEMBERSHIP_VALUES = {"SP500", "R1000", "R3000"}

REQUIRED_FIELDS = {
    "ticker",
    "company_name",
    "asset_class",
    "sector",
    "industry",
    "thematic_tags",
    "region",
    "currency_exposure",
    "main_risk_factor",
    "secondary_risk_factors",
    "risk_role",
    "index_membership",
}

EXPORT_COLUMNS = [
    "ticker",
    "company_name",
    "asset_class",
    "sector",
    "industry",
    "thematic_tags",
    "region",
    "currency_exposure",
    "main_risk_factor",
    "secondary_risk_factors",
    "risk_role",
    "index_membership",
]


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


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _upper_ticker(value: Any) -> str:
    return str(value or "").strip().upper()


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def load_stock_universe(path: str | Path | None = None) -> list[dict[str, Any]]:
    """Load stock universe YAML source as a list of mapping records."""
    universe_path = Path(path) if path is not None else DEFAULT_UNIVERSE_PATH
    try:
        data = load_yaml_mtime_cached(universe_path)
    except yaml.YAMLError as exc:
        raise UniverseValidationError(f"Malformed stock universe YAML: {universe_path}: {exc}") from exc
    except OSError as exc:
        raise UniverseValidationError(f"Stock universe not readable: {universe_path}: {exc}") from exc

    if data is None:
        return []
    if not isinstance(data, list):
        raise UniverseValidationError(f"Stock universe must be a YAML list: {universe_path}")

    records: list[dict[str, Any]] = []
    for idx, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise UniverseValidationError(f"Stock universe row {idx} must be a mapping")
        row = dict(item)
        if row.get("ticker"):
            row["ticker"] = _upper_ticker(row["ticker"])
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

    if errors:
        return errors, warnings

    asset_class = record.get("asset_class")
    if asset_class not in ASSET_CLASSES:
        errors.append(_issue("invalid_enum", f"Invalid asset_class: {asset_class!r}", ticker, field="asset_class", value=asset_class))

    for field in ("company_name", "sector", "industry", "region", "currency_exposure"):
        value = record.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(_issue("invalid_string", f"{field} must be a non-empty string", ticker, field=field))

    if record.get("region") != "US":
        errors.append(
            _issue(
                "invalid_region",
                "V1 stock universe requires region=US",
                ticker,
                field="region",
                value=record.get("region"),
            )
        )

    if record.get("currency_exposure") != "USD":
        errors.append(
            _issue(
                "invalid_currency_exposure",
                "V1 stock universe requires currency_exposure=USD",
                ticker,
                field="currency_exposure",
                value=record.get("currency_exposure"),
            )
        )

    main_risk_factor = record.get("main_risk_factor")
    if main_risk_factor not in RISK_FACTORS:
        errors.append(
            _issue(
                "invalid_enum",
                f"Invalid main_risk_factor: {main_risk_factor!r}",
                ticker,
                field="main_risk_factor",
                value=main_risk_factor,
            )
        )
    elif main_risk_factor != "equity":
        errors.append(
            _issue(
                "invalid_main_risk_factor",
                "V1 stock universe requires main_risk_factor=equity",
                ticker,
                field="main_risk_factor",
                value=main_risk_factor,
            )
        )

    for field in ("thematic_tags", "secondary_risk_factors", "risk_role", "index_membership"):
        value = record.get(field)
        if not isinstance(value, list):
            errors.append(_issue("invalid_list", f"{field} must be a list", ticker, field=field))

    risk_role = record.get("risk_role")
    if isinstance(risk_role, list):
        if not risk_role:
            errors.append(_issue("invalid_list", "risk_role must be a non-empty list", ticker, field="risk_role"))
        else:
            for value in risk_role:
                if value not in RISK_ROLES:
                    errors.append(
                        _issue("invalid_enum", f"Invalid risk_role: {value!r}", ticker, field="risk_role", value=value)
                    )

    secondary = record.get("secondary_risk_factors")
    if isinstance(secondary, list):
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
        if secondary != ["us_growth"]:
            errors.append(
                _issue(
                    "invalid_secondary_risk_factors",
                    "V1 stock universe requires secondary_risk_factors=[us_growth]",
                    ticker,
                    field="secondary_risk_factors",
                    value=secondary,
                )
            )

    membership = record.get("index_membership")
    if isinstance(membership, list):
        if not membership:
            errors.append(_issue("invalid_list", "index_membership must be a non-empty list", ticker, field="index_membership"))
        for value in membership:
            if value not in INDEX_MEMBERSHIP_VALUES:
                errors.append(
                    _issue("invalid_enum", f"Invalid index_membership value: {value!r}", ticker, field="index_membership", value=value)
                )
        if len(membership) != 1 or membership[0] not in INDEX_MEMBERSHIP_VALUES:
            errors.append(
                _issue(
                    "invalid_index_membership",
                    "Stock universe requires exactly one primary index_membership tag (SP500, R1000, or R3000)",
                    ticker,
                    field="index_membership",
                    value=membership,
                )
            )

    if risk_role == ["risk_on"]:
        pass
    elif isinstance(risk_role, list):
        errors.append(
            _issue(
                "invalid_risk_role",
                "V1 stock universe requires risk_role=[risk_on]",
                ticker,
                field="risk_role",
                value=risk_role,
            )
        )

    return errors, warnings


def validate_stock_universe(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate stock universe source records and return status, errors, warnings, and summary."""
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    tickers: dict[str, int] = {}

    for idx, record in enumerate(records, start=1):
        record_errors, record_warnings = _validate_record(record, idx)
        errors.extend(record_errors)
        warnings.extend(record_warnings)
        ticker = _upper_ticker(record.get("ticker"))
        if ticker:
            tickers[ticker] = tickers.get(ticker, 0) + 1

    for ticker, count in sorted(tickers.items()):
        if count > 1:
            errors.append(_issue("duplicate_ticker", f"Duplicate ticker in stock universe: {ticker}", ticker, count=count))

    return {
        "status": _status(errors, warnings),
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "record_count": len(records),
            "unique_ticker_count": len(tickers),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
    }


def check_config_tickers(config_tickers: list[str], records: list[dict[str, Any]]) -> dict[str, Any]:
    """Check a config ticker list against a structurally valid stock universe."""
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    by_ticker = {_upper_ticker(r.get("ticker")): r for r in records if _upper_ticker(r.get("ticker"))}
    normalized_tickers = [_upper_ticker(t) for t in config_tickers if _upper_ticker(t)]

    unknown = [t for t in normalized_tickers if t not in by_ticker]
    if unknown:
        warnings.append(
            _issue(
                "unknown_ticker",
                "Config contains tickers absent from stock universe",
                tickers=sorted(unknown),
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
        },
        "known_tickers": [t for t in normalized_tickers if t in by_ticker],
        "unknown_tickers": sorted(unknown),
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


def build_stock_universe_diagnostics(
    config_tickers: list[str] | None = None,
    universe_path: str | Path | None = None,
) -> dict[str, Any]:
    """Load and validate the stock universe, optionally checking a config ticker list."""
    path = Path(universe_path) if universe_path is not None else DEFAULT_UNIVERSE_PATH
    try:
        records = load_stock_universe(path)
    except UniverseValidationError as exc:
        return {
            "status": STATUS_FAIL,
            "errors": [_issue("malformed_yaml", str(exc))],
            "warnings": [],
            "summary": {"error_count": 1, "warning_count": 0, "record_count": 0},
            "universe_path": str(path),
        }

    validation = validate_stock_universe(records)
    validation["universe_path"] = str(path)
    if validation["status"] == STATUS_FAIL or config_tickers is None:
        return validation

    config_diag = check_config_tickers(config_tickers, records)
    merged = merge_diagnostics(validation, config_diag)
    merged["universe_path"] = str(path)
    return merged


def _exportable_record(record: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for col in EXPORT_COLUMNS:
        value = record.get(col)
        if isinstance(value, list):
            value = "|".join(str(v) for v in value)
        out[col] = value
    return out


def export_stock_universe(records: list[dict[str, Any]], output_path: str | Path, fmt: str) -> Path:
    """Export stock universe records as deterministic CSV or JSON."""
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


def list_stock_universe(
    records: list[dict[str, Any]],
    sector: str | None = None,
    industry: str | None = None,
    risk_factor: str | None = None,
) -> list[dict[str, Any]]:
    """Filter stock universe records by sector, industry, and/or main/secondary risk factor."""
    sector_filter = sector.strip().casefold() if sector else None
    industry_filter = industry.strip().casefold() if industry else None
    risk_factor_filter = risk_factor.strip() if risk_factor else None
    out: list[dict[str, Any]] = []
    for record in records:
        if sector_filter and str(record.get("sector", "")).strip().casefold() != sector_filter:
            continue
        if industry_filter and str(record.get("industry", "")).strip().casefold() != industry_filter:
            continue
        if risk_factor_filter:
            secondary = [str(v) for v in _as_list(record.get("secondary_risk_factors"))]
            if record.get("main_risk_factor") != risk_factor_filter and risk_factor_filter not in secondary:
                continue
        out.append(record)
    return sorted(out, key=lambda r: _upper_ticker(r.get("ticker")))


def default_export_path(fmt: str, output_dir: str | Path = "results_csv") -> Path:
    suffix = "csv" if fmt == "csv" else "json"
    return Path(output_dir) / f"stock_universe.{suffix}"
