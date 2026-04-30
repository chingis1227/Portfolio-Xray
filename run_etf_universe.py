"""CLI for validating, listing, exporting, and enriching the ETF universe."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from src.etf_universe import (
    ASSET_CLASSES,
    RISK_FACTORS,
    STATUS_FAIL,
    build_universe_diagnostics,
    default_export_path,
    export_universe,
    list_universe,
    load_etf_universe,
    validate_etf_universe,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ETF universe taxonomy utilities")
    parser.add_argument("--universe", default=None, help="Path to ETF universe YAML")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate", help="Validate ETF universe YAML")

    p_check = sub.add_parser("check-config", help="Validate universe and annotate config tickers")
    p_check.add_argument("--config", default="config.yml", help="Path to portfolio config YAML")

    p_export = sub.add_parser("export", help="Export universe to CSV or JSON")
    p_export.add_argument("--format", choices=("csv", "json"), required=True)
    p_export.add_argument("--output", default=None, help="Output path; defaults to results_csv/etf_universe.<format>")

    p_list = sub.add_parser("list", help="List universe tickers by filters")
    p_list.add_argument("--asset-class", choices=sorted(ASSET_CLASSES), default=None)
    p_list.add_argument("--risk-factor", choices=sorted(RISK_FACTORS), default=None)

    p_enrich = sub.add_parser("enrich-yahoo", help="Write generated yfinance history/volume coverage artifact")
    p_enrich.add_argument("--output", default="results_csv/etf_universe_yahoo_enrichment.csv")
    p_enrich.add_argument("--period", default="3mo", help="yfinance period for recent volume checks")

    return parser.parse_args()


def _load_config_tickers(config_path: str | Path) -> list[str]:
    path = Path(config_path)
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    tickers = data.get("tickers") or []
    if not isinstance(tickers, list):
        raise ValueError(f"{path}: tickers must be a YAML list")
    return [str(t).strip().upper() for t in tickers if str(t).strip()]


def _print_diagnostics(diagnostics: dict[str, Any]) -> None:
    print(json.dumps(diagnostics, indent=2, ensure_ascii=False))


def _exit_for_status(status: str) -> int:
    return 1 if status == STATUS_FAIL else 0


def _write_yahoo_enrichment(records: list[dict[str, Any]], output: str | Path, period: str) -> Path:
    try:
        import yfinance as yf
    except ImportError as exc:
        raise RuntimeError("yfinance is required for enrich-yahoo") from exc

    rows: list[dict[str, Any]] = []
    for record in sorted(records, key=lambda r: str(r.get("ticker", ""))):
        ticker = str(record.get("ticker", "")).strip().upper()
        if not ticker:
            continue
        row: dict[str, Any] = {
            "ticker": ticker,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "period": period,
            "history_start": None,
            "history_end": None,
            "rows": 0,
            "avg_volume": None,
            "status": "ERROR",
            "error": None,
        }
        try:
            df = yf.download(
                ticker,
                period=period,
                interval="1d",
                auto_adjust=False,
                progress=False,
                threads=False,
            )
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.dropna(how="all")
            row["rows"] = int(len(df))
            if len(df):
                row["history_start"] = str(pd.to_datetime(df.index.min()).date())
                row["history_end"] = str(pd.to_datetime(df.index.max()).date())
                if "Volume" in df.columns:
                    row["avg_volume"] = float(df["Volume"].dropna().tail(30).mean())
                row["status"] = "OK"
            else:
                row["status"] = "NO_DATA"
        except Exception as exc:  # pragma: no cover - network/provider dependent
            row["error"] = str(exc)
        rows.append(row)

    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def main() -> None:
    args = parse_args()

    if args.command == "check-config":
        tickers = _load_config_tickers(args.config)
        diagnostics = build_universe_diagnostics(tickers, args.universe)
        _print_diagnostics(diagnostics)
        raise SystemExit(_exit_for_status(diagnostics["status"]))

    records = load_etf_universe(args.universe)
    diagnostics = validate_etf_universe(records)
    if diagnostics["status"] == STATUS_FAIL and args.command != "validate":
        _print_diagnostics(diagnostics)
        raise SystemExit(1)

    if args.command == "validate":
        _print_diagnostics(diagnostics)
        raise SystemExit(_exit_for_status(diagnostics["status"]))

    if args.command == "export":
        output = Path(args.output) if args.output else default_export_path(args.format)
        path = export_universe(records, output, args.format)
        print(path)
        return

    if args.command == "list":
        rows = list_universe(records, asset_class=args.asset_class, risk_factor=args.risk_factor)
        for row in rows:
            print(
                "\t".join(
                    [
                        str(row.get("ticker", "")),
                        str(row.get("name", "")),
                        str(row.get("asset_class", "")),
                        str(row.get("main_risk_factor", "")),
                    ]
                )
            )
        return

    if args.command == "enrich-yahoo":
        path = _write_yahoo_enrichment(records, args.output, args.period)
        print(path)
        return

    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
