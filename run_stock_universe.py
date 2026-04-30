"""CLI for validating, listing, and exporting the stock universe."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from src.etf_universe import RISK_FACTORS, STATUS_FAIL
from src.stock_universe import (
    ASSET_CLASSES,
    build_stock_universe_diagnostics,
    default_export_path,
    export_stock_universe,
    list_stock_universe,
    load_stock_universe,
    validate_stock_universe,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stock universe taxonomy utilities")
    parser.add_argument("--universe", default=None, help="Path to stock universe YAML")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate", help="Validate stock universe YAML")

    p_check = sub.add_parser("check-config", help="Validate universe and annotate config tickers")
    p_check.add_argument("--config", default="config.yml", help="Path to portfolio config YAML")

    p_export = sub.add_parser("export", help="Export stock universe to CSV or JSON")
    p_export.add_argument("--format", choices=("csv", "json"), required=True)
    p_export.add_argument("--output", default=None, help="Output path; defaults to results_csv/stock_universe.<format>")

    p_list = sub.add_parser("list", help="List stock universe rows by filters")
    p_list.add_argument("--asset-class", choices=sorted(ASSET_CLASSES), default=None)
    p_list.add_argument("--sector", default=None)
    p_list.add_argument("--industry", default=None)
    p_list.add_argument("--risk-factor", choices=sorted(RISK_FACTORS), default=None)

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


def main() -> None:
    args = parse_args()

    if args.command == "check-config":
        tickers = _load_config_tickers(args.config)
        diagnostics = build_stock_universe_diagnostics(tickers, args.universe)
        _print_diagnostics(diagnostics)
        raise SystemExit(_exit_for_status(diagnostics["status"]))

    records = load_stock_universe(args.universe)
    diagnostics = validate_stock_universe(records)
    if diagnostics["status"] == STATUS_FAIL and args.command != "validate":
        _print_diagnostics(diagnostics)
        raise SystemExit(1)

    if args.command == "validate":
        _print_diagnostics(diagnostics)
        raise SystemExit(_exit_for_status(diagnostics["status"]))

    if args.command == "export":
        output = Path(args.output) if args.output else default_export_path(args.format)
        path = export_stock_universe(records, output, args.format)
        print(path)
        return

    if args.command == "list":
        rows = list_stock_universe(records, sector=args.sector, industry=args.industry, risk_factor=args.risk_factor)
        if args.asset_class:
            rows = [row for row in rows if row.get("asset_class") == args.asset_class]
        for row in rows:
            print(
                "\t".join(
                    [
                        str(row.get("ticker", "")),
                        str(row.get("company_name", "")),
                        str(row.get("sector", "")),
                        str(row.get("industry", "")),
                        str(row.get("main_risk_factor", "")),
                    ]
                )
            )
        return

    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
