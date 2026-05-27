#!/usr/bin/env python3
"""
Run Core MVP Blocks 1-3 fixture matrix (Step 2 only).

Per fixture:
  - load YAML from tests/fixtures/mvp_portfolios/fixture_matrix_fx*.yml
  - validate taxonomy membership across active universe files
    (config/etf_universe.yml + config/stock_universe.yml)
  - validate config via src.config_schema.validate_config
  - materialize analysis_subject via run_materialize_analysis_subject_report
  - write outputs to output/fixture_matrix_runs/<fixture_id>/analysis_subject/

This runner intentionally avoids candidate generation, comparison, decision package,
and optimizer-first flows.
"""
from __future__ import annotations

import argparse
import contextlib
import inspect
import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from run_report import run_materialize_analysis_subject_report
from src.config_schema import validate_config


REAL_CASH_LABELS = {"CASH", "CASH USD"}
FORBIDDEN_ENTRYPOINT_TOKENS = (
    "run_candidate_factory",
    "run_compare_variants",
    "decision_verdict",
    "selection_decision",
    "run_optimization",
)


def _load_universe_tickers(path: Path) -> set[str]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    if not isinstance(raw, list):
        raise ValueError(f"Universe YAML must be a list: {path}")
    tickers: set[str] = set()
    for row in raw:
        if not isinstance(row, dict):
            continue
        token = str(row.get("ticker") or "").strip().upper()
        if token:
            tickers.add(token)
    return tickers


def _assert_entrypoint_preflight() -> None:
    source = inspect.getsource(run_materialize_analysis_subject_report)
    lowered = source.lower()
    violations = [token for token in FORBIDDEN_ENTRYPOINT_TOKENS if token.lower() in lowered]
    if violations:
        joined = ", ".join(sorted(violations))
        raise RuntimeError(
            "Preflight failed: run_materialize_analysis_subject_report contains forbidden references: "
            f"{joined}"
        )


def _validate_fixture_taxonomy(
    *,
    fixture_doc: dict[str, Any],
    etf_tickers: set[str],
    stock_tickers: set[str],
    fixture_id: str,
) -> None:
    unknown: list[str] = []
    for raw in fixture_doc.get("tickers") or []:
        t = str(raw or "").strip()
        if not t:
            continue
        up = t.upper()
        if up in REAL_CASH_LABELS:
            continue
        if up not in etf_tickers and up not in stock_tickers:
            unknown.append(t)
    if unknown:
        raise RuntimeError(
            f"Fixture {fixture_id} has taxonomy-missing tickers (no auto-replace allowed): "
            + ", ".join(sorted(set(unknown)))
        )


def _run_fixture(
    *,
    fixture_path: Path,
    output_root: Path,
    etf_tickers: set[str],
    stock_tickers: set[str],
    skip_existing: bool,
) -> dict[str, Any]:
    fixture_id = fixture_path.stem.replace("fixture_matrix_", "")
    raw = yaml.safe_load(fixture_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise RuntimeError(f"Fixture {fixture_path.name} must be a YAML object")
    _validate_fixture_taxonomy(
        fixture_doc=raw,
        etf_tickers=etf_tickers,
        stock_tickers=stock_tickers,
        fixture_id=fixture_id,
    )

    fixture_output_dir = output_root / fixture_id
    subject_dir = fixture_output_dir / "analysis_subject"
    existing_expected = (
        (subject_dir / "run_metadata.json").is_file()
        and (subject_dir / "portfolio_xray.json").is_file()
        and (subject_dir / "stress_report.json").is_file()
    )
    if skip_existing and existing_expected:
        return {
            "fixture_id": fixture_id,
            "fixture_file": str(fixture_path.relative_to(REPO_ROOT)),
            "output_dir": str(subject_dir.relative_to(REPO_ROOT)),
            "status": "skipped_existing",
        }

    payload = dict(raw)
    payload["output_dir_final"] = str(fixture_output_dir)

    cfg = validate_config(payload)
    run_timestamp = datetime.now(timezone.utc).isoformat()
    fixture_output_dir.mkdir(parents=True, exist_ok=True)
    run_log = fixture_output_dir / "step2_materialize.log"
    with open(run_log, "w", encoding="utf-8") as logf, contextlib.redirect_stdout(logf), contextlib.redirect_stderr(
        logf
    ):
        run_materialize_analysis_subject_report(
            cfg,
            run_timestamp=run_timestamp,
            backtest_mode="dynamic_nan_safe",
            no_cache=False,
            output_profile="site_api",
            review_mode="core",
            project_root=REPO_ROOT,
            use_review_run_context=True,
        )

    expected = {
        "run_metadata": subject_dir / "run_metadata.json",
        "portfolio_xray": subject_dir / "portfolio_xray.json",
        "stress_report": subject_dir / "stress_report.json",
    }
    exists = {k: v.is_file() for k, v in expected.items()}
    return {
        "fixture_id": fixture_id,
        "fixture_file": str(fixture_path.relative_to(REPO_ROOT)),
        "output_dir": str(subject_dir.relative_to(REPO_ROOT)),
        "status": "ok" if all(exists.values()) else "partial",
        "run_log": str(run_log.relative_to(REPO_ROOT)),
        "expected_files": {k: str(v.relative_to(REPO_ROOT)) for k, v in expected.items()},
        "expected_file_exists": exists,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Step 2 fixture matrix materialization (Blocks 1-3)")
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=REPO_ROOT / "tests" / "fixtures" / "mvp_portfolios",
        help="Directory containing fixture_matrix_fx*.yml files.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=REPO_ROOT / "output" / "fixture_matrix_runs",
        help="Root output directory for fixture runs.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue remaining fixtures after a fixture failure.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip fixtures that already have run_metadata/portfolio_xray/stress_report under analysis_subject.",
    )
    parser.add_argument(
        "--only",
        action="append",
        dest="only_fixtures",
        metavar="FIXTURE_ID",
        help="Run only selected fixture_id values (repeatable), e.g. fx7_mixed_10_holdings.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    fixtures_dir = args.fixtures_dir.resolve()
    output_root = args.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    _assert_entrypoint_preflight()

    etf_tickers = _load_universe_tickers(REPO_ROOT / "config" / "etf_universe.yml")
    stock_tickers = _load_universe_tickers(REPO_ROOT / "config" / "stock_universe.yml")

    fixture_paths = sorted(fixtures_dir.glob("fixture_matrix_fx*.yml"))
    if len(fixture_paths) != 7:
        raise RuntimeError(f"Expected 7 fixture files, found {len(fixture_paths)} in {fixtures_dir}")
    if args.only_fixtures:
        wanted = {str(x).strip() for x in args.only_fixtures if str(x).strip()}
        fixture_paths = [
            p
            for p in fixture_paths
            if p.stem.replace("fixture_matrix_", "") in wanted
        ]
        if not fixture_paths:
            raise RuntimeError("No fixtures selected after applying --only filter.")

    results: list[dict[str, Any]] = []
    exit_code = 0
    for path in fixture_paths:
        fixture_id = path.stem.replace("fixture_matrix_", "")
        print(f"\n=== Fixture: {fixture_id} ===", flush=True)
        try:
            row = _run_fixture(
                fixture_path=path,
                output_root=output_root,
                etf_tickers=etf_tickers,
                stock_tickers=stock_tickers,
                skip_existing=args.skip_existing,
            )
            results.append(row)
            print(f"[{row['status'].upper()}] {fixture_id} -> {row['output_dir']}", flush=True)
        except Exception as exc:  # noqa: BLE001
            exit_code = 1
            err = {
                "fixture_id": fixture_id,
                "fixture_file": str(path.relative_to(REPO_ROOT)),
                "status": "failed",
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }
            results.append(err)
            print(f"[FAILED] {fixture_id}: {exc}", flush=True)
            if not args.continue_on_error:
                break

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runner": "run_core_mvp_blocks_1_3_fixture_matrix.py",
        "step": "step_2_materialize_analysis_subject_only",
        "fixtures_dir": str(fixtures_dir),
        "output_root": str(output_root),
        "results": results,
    }
    summary_path = output_root / "step2_run_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSummary: {summary_path}", flush=True)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
