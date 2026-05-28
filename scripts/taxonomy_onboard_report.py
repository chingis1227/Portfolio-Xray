#!/usr/bin/env python3
"""Print taxonomy + stress-block onboarding report for tickers (read-only)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.taxonomy_stress_blocks import build_onboard_report


def _load_cash_proxy_from_config(config_path: Path) -> str | None:
    import yaml

    if not config_path.is_file():
        return None
    with config_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    raw = data.get("cash_proxy_ticker") or data.get("cash_proxy")
    if raw is None:
        return None
    s = str(raw).strip().upper()
    return s or None


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Taxonomy and stress-block onboarding report (RC vs PnL readiness hints)",
    )
    p.add_argument(
        "--tickers",
        required=True,
        help="Comma-separated tickers, e.g. VOO,HYG,UNKNOWN",
    )
    p.add_argument("--config", default="config.yml", help="Portfolio config for unknown-ticker cross-check")
    p.add_argument("--etf-universe", default=None, help="Path to etf_universe.yml")
    p.add_argument("--stock-universe", default=None, help="Path to stock_universe.yml")
    p.add_argument("--cash-proxy", default=None, help="Cash proxy ticker (default: read from config if present)")
    p.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format",
    )
    return p.parse_args()


def _format_text(report: dict) -> str:
    lines: list[str] = []
    lines.append(f"Taxonomy onboard report ({report.get('version')})")
    lines.append("")
    summary = report.get("summary") or {}
    lines.append(
        f"Summary: {summary.get('count', 0)} tickers | "
        f"RC-ready: {summary.get('rc_ready_count', 0)} | "
        f"X-Ray-ready: {summary.get('xray_ready_count', 0)} | "
        f"needs_review: {summary.get('needs_review_count', 0)} | "
        f"silent_default_EQ: {summary.get('silent_default_eq_count', 0)}"
    )
    val = report.get("validators") or {}
    lines.append(
        f"Validators: ETF={val.get('etf_universe', {}).get('status')} | "
        f"Stock={val.get('stock_universe', {}).get('status')}"
    )
    if val.get("config_unknown_among_input"):
        lines.append(f"Config unknown among input: {', '.join(val['config_unknown_among_input'])}")
    lines.append("")
    for row in report.get("per_ticker") or []:
        lines.append(f"--- {row.get('ticker')} ---")
        lines.append(f"  universe: {row.get('universe_source')}")
        lines.append(f"  stress_block: {row.get('stress_block')} (source={row.get('stress_block_source')})")
        lines.append(f"  silent_default_eq: {row.get('silent_default_eq')}")
        lines.append(f"  confidence: {row.get('classification_confidence')} | needs_review: {row.get('needs_review')}")
        lines.append(f"  xray_ready: {row.get('xray_ready')} | rc_ready: {row.get('rc_ready')}")
        tax = row.get("taxonomy") or {}
        if tax.get("asset_class"):
            lines.append(
                f"  taxonomy: asset_class={tax.get('asset_class')} subtype={tax.get('subtype')} "
                f"main_risk_factor={tax.get('main_risk_factor')}"
            )
        for w in row.get("warnings") or []:
            lines.append(f"  WARNING: {w}")
        lines.append(f"  pnl_hint: {row.get('pnl_ready_hint')}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    tickers = [t.strip() for t in args.tickers.split(",") if t.strip()]
    if not tickers:
        print("No tickers provided.", file=sys.stderr)
        return 1

    cash_proxy = args.cash_proxy
    if cash_proxy:
        cash_proxy = str(cash_proxy).strip().upper() or None
    elif args.config:
        cash_proxy = _load_cash_proxy_from_config(Path(args.config))

    report = build_onboard_report(
        tickers,
        cash_proxy_ticker=cash_proxy,
        config_path=args.config,
        etf_path=args.etf_universe,
        stock_path=args.stock_universe,
    )

    if args.format == "text":
        sys.stdout.write(_format_text(report))
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))

    any_not_rc = any(not r.get("rc_ready") for r in report.get("per_ticker") or [])
    return 1 if any_not_rc else 0


if __name__ == "__main__":
    raise SystemExit(main())
