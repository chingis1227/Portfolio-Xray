#!/usr/bin/env python3
"""Validate Block 2.4 institutional v2 on a materialized subject portfolio_xray.json.

Session 12 operator helper: inspect live ``analysis_subject/portfolio_xray.json`` after
``run_portfolio_review.py`` or ``run_report.py --materialize-analysis-subject``.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.core_mvp_validation_contract import check_block_2_4_hidden_exposure
from src.config import load_validated_config
from src.snapshot import _xray_summary_from_output_dir


def _default_xray_path() -> Path:
    cfg = load_validated_config(REPO_ROOT / "config.yml")
    return REPO_ROOT / cfg.output_dir_final / "analysis_subject" / "portfolio_xray.json"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Block 2.4 hidden exposure v2 on materialized portfolio_xray.json."
    )
    parser.add_argument(
        "--xray-path",
        type=Path,
        default=None,
        help="Path to portfolio_xray.json (default: config output_dir_final/analysis_subject/).",
    )
    parser.add_argument(
        "--refresh-xray",
        action="store_true",
        help=(
            "Rebuild portfolio_xray.json from existing analysis_subject artifacts "
            "(snapshot, stress_report, run_metadata) before validation."
        ),
    )
    args = parser.parse_args()

    if args.refresh_xray:
        cfg = load_validated_config(REPO_ROOT / "config.yml")
        subject_dir = (REPO_ROOT / cfg.output_dir_final / "analysis_subject").resolve()
        print(f"Refreshing portfolio_xray.json under {subject_dir} ...")
        _xray_summary_from_output_dir(subject_dir)

    xray_path = (args.xray_path or _default_xray_path()).resolve()
    if not xray_path.is_file():
        print(f"ERROR: missing portfolio_xray.json: {xray_path}", file=sys.stderr)
        return 1

    doc = json.loads(xray_path.read_text(encoding="utf-8"))
    block = doc.get("block_2_4_hidden_exposure")
    if not isinstance(block, dict):
        print("ERROR: block_2_4_hidden_exposure missing or not an object", file=sys.stderr)
        return 1

    checks = check_block_2_4_hidden_exposure(block)
    print(f"xray_path={xray_path}")
    print(f"block_status={block.get('status')}")
    print(f"summary={block.get('summary')}")
    for key in (
        "institutional_v2_surface_ok",
        "stress_boundary_ok",
        "ruleset",
        "confidence_model",
        "alert_count",
        "unavailable_alert_count",
        "blocked_upstream_registry_count",
    ):
        print(f"{key}={checks.get(key)}")

    violations = checks.get("contract_violations") or []
    if violations:
        print("contract_violations:")
        for row in violations:
            print(f"  - {row}")

    top = block.get("top_hidden_risks") or []
    if isinstance(top, list) and top:
        print("top_hidden_risks:")
        for row in top[:3]:
            if isinstance(row, dict):
                print(
                    "  - "
                    f"{row.get('alert_id')}: status={row.get('status')} "
                    f"score={row.get('score')} confidence={row.get('confidence')}"
                )

    if checks.get("institutional_v2_surface_ok") and checks.get("stress_boundary_ok"):
        print("Block 2.4 live validation: OK")
        return 0

    print("Block 2.4 live validation: FAILED", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
