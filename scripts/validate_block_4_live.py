#!/usr/bin/env python3
"""Validate Block 4 v2 diagnosis on materialized ``analysis_subject/`` artifacts.

Session 12 operator helper: inspect live ``problem_classification.json`` and
``candidate_launchpad.json`` after ``run_portfolio_review.py`` or
``run_report.py`` (non core-blocks-only), or refresh from existing X-Ray + stress.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.core_mvp_validation_contract import (  # noqa: E402
    check_block_4_v2_diagnosis_handoff,
    check_candidate_launchpad_v2,
    check_problem_classification_v2,
)
from src.block_4.diagnosis_builder import write_block_4_diagnosis_outputs  # noqa: E402
from src.candidate_launchpad import CANDIDATE_LAUNCHPAD_FILENAME  # noqa: E402
from src.config import load_validated_config  # noqa: E402
from src.problem_classification import PROBLEM_CLASSIFICATION_FILENAME  # noqa: E402
from src.snapshot import _xray_summary_from_output_dir  # noqa: E402


def _default_subject_dir() -> Path:
    cfg = load_validated_config(REPO_ROOT / "config.yml")
    return (REPO_ROOT / cfg.output_dir_final / "analysis_subject").resolve()


def _resolve_analysis_end(subject_dir: Path) -> str | None:
    for name in ("snapshot_10y.json", "snapshot_5y.json", "snapshot_3y.json", "run_metadata.json"):
        path = subject_dir / name
        if not path.is_file():
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(doc, dict):
            continue
        for key in ("analysis_end",):
            value = doc.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        run_info = doc.get("run_info")
        if isinstance(run_info, dict):
            value = run_info.get("analysis_end_date") or run_info.get("analysis_end")
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    doc = json.loads(path.read_text(encoding="utf-8"))
    return doc if isinstance(doc, dict) else None


def _refresh_block_4_diagnosis(subject_dir: Path) -> None:
    xray_path = subject_dir / "portfolio_xray.json"
    stress_path = subject_dir / "stress_report.json"
    if xray_path.is_file():
        portfolio_xray = _load_json(xray_path)
    else:
        print(f"Refreshing portfolio_xray.json under {subject_dir} ...")
        portfolio_xray = _xray_summary_from_output_dir(subject_dir)
    stress_report = _load_json(stress_path)
    if portfolio_xray is None:
        raise FileNotFoundError(f"missing portfolio_xray.json: {xray_path}")
    if stress_report is None:
        raise FileNotFoundError(f"missing stress_report.json: {stress_path}")

    analysis_end = _resolve_analysis_end(subject_dir)
    print(f"Writing Block 4 v2 diagnosis to {subject_dir} (analysis_end={analysis_end!r}) ...")
    write_block_4_diagnosis_outputs(
        output_dir=subject_dir,
        portfolio_xray=portfolio_xray,
        stress_report=stress_report,
        analysis_end=analysis_end,
    )


def validate_block_4_live(subject_dir: Path) -> dict[str, Any]:
    pc_path = subject_dir / PROBLEM_CLASSIFICATION_FILENAME
    lp_path = subject_dir / CANDIDATE_LAUNCHPAD_FILENAME
    pc = _load_json(pc_path)
    lp = _load_json(lp_path)
    if pc is None:
        raise FileNotFoundError(f"missing {PROBLEM_CLASSIFICATION_FILENAME}: {pc_path}")
    if lp is None:
        raise FileNotFoundError(f"missing {CANDIDATE_LAUNCHPAD_FILENAME}: {lp_path}")

    pc_checks = check_problem_classification_v2(pc)
    lp_checks = check_candidate_launchpad_v2(lp)
    handoff = check_block_4_v2_diagnosis_handoff(pc, lp)
    ok = (
        bool(pc_checks.get("product_contract_ok"))
        and bool(lp_checks.get("product_contract_ok"))
        and bool(handoff.get("handoff_ok"))
    )
    return {
        "ok": ok,
        "subject_dir": str(subject_dir),
        "problem_classification": pc_checks,
        "candidate_launchpad": lp_checks,
        "handoff": handoff,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Block 4 v2 Problem Classification + Launchpad on analysis_subject/."
    )
    parser.add_argument(
        "--subject-dir",
        type=Path,
        default=None,
        help="Path to analysis_subject/ (default: config output_dir_final/analysis_subject/).",
    )
    parser.add_argument(
        "--refresh-diagnosis",
        action="store_true",
        help=(
            "Rebuild problem_classification.json and candidate_launchpad.json from "
            "portfolio_xray.json + stress_report.json before validation."
        ),
    )
    args = parser.parse_args()

    subject_dir = (args.subject_dir or _default_subject_dir()).resolve()
    if not subject_dir.is_dir():
        print(f"ERROR: missing analysis_subject directory: {subject_dir}", file=sys.stderr)
        return 1

    if args.refresh_diagnosis:
        try:
            _refresh_block_4_diagnosis(subject_dir)
        except FileNotFoundError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

    try:
        result = validate_block_4_live(subject_dir)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    pc = result["problem_classification"]
    lp = result["candidate_launchpad"]
    handoff = result["handoff"]

    print(f"subject_dir={subject_dir}")
    print(f"primary_problem_id={pc.get('primary_problem_id')}")
    print(f"no_trade_outcome={pc.get('no_trade_outcome')}")
    print(f"n_secondary={pc.get('n_secondary')}")
    print(f"n_rejected={pc.get('n_rejected')}")
    print(f"n_cards={lp.get('n_cards')}")
    print(f"launchpad_outcome={lp.get('launchpad_outcome')}")
    print(f"primary_card_id={lp.get('primary_card_id')}")
    print(f"product_contract_ok={pc.get('product_contract_ok') and lp.get('product_contract_ok')}")
    print(f"handoff_ok={handoff.get('handoff_ok')}")

    for label, checks in (("problem_classification_v2", pc), ("candidate_launchpad_v2", lp)):
        violations = checks.get("contract_violations") or []
        if violations:
            print(f"{label} contract_violations:")
            for row in violations:
                print(f"  - {row}")

    handoff_violations = handoff.get("contract_violations") or []
    if handoff_violations:
        print("block_4_v2_handoff violations:")
        for row in handoff_violations:
            print(f"  - {row}")

    if result["ok"]:
        print("Block 4 v2 live validation: OK")
        return 0

    print("Block 4 v2 live validation: FAILED", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
