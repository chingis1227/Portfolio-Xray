#!/usr/bin/env python3
"""
Validate Core MVP Block 1 for fixture matrix runs (Step 3 only).

Reads:
  output/fixture_matrix_runs/<fixture_id>/analysis_subject/run_metadata.json
  tests/fixtures/mvp_portfolios/fixture_matrix_fx*.yml

Writes:
  output/fixture_matrix_runs/step3_block1_validation.json
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.etf_universe import REQUIRED_FIELDS as ETF_REQUIRED_FIELDS
from src.stock_universe import REQUIRED_FIELDS as STOCK_REQUIRED_FIELDS


REAL_CASH_LABELS = {"CASH", "CASH USD"}
EXPECTED_CORE_MVP_INPUT_GROUPS = ["tickers", "allocation", "investor_currency"]


def _load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _load_universe_map(path: Path) -> dict[str, dict[str, Any]]:
    data = _load_yaml(path) or []
    if not isinstance(data, list):
        raise ValueError(f"Universe YAML must be a list: {path}")
    out: dict[str, dict[str, Any]] = {}
    for row in data:
        if not isinstance(row, dict):
            continue
        ticker = str(row.get("ticker") or "").strip().upper()
        if ticker:
            out[ticker] = row
    return out


def _is_missing_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def _ticker_taxonomy_check(
    tickers: list[str],
    etf_map: dict[str, dict[str, Any]],
    stock_map: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    mapped: list[dict[str, Any]] = []
    unknown: list[str] = []
    missing_fields_rows: list[dict[str, Any]] = []
    for raw_ticker in tickers:
        ticker = str(raw_ticker or "").strip()
        upper = ticker.upper()
        if upper in REAL_CASH_LABELS:
            mapped.append({"ticker": ticker, "taxonomy_source": "real_cash_label"})
            continue
        if upper in etf_map:
            record = etf_map[upper]
            missing = [f for f in sorted(ETF_REQUIRED_FIELDS) if _is_missing_value(record.get(f))]
            mapped.append({"ticker": ticker, "taxonomy_source": "etf_universe"})
            if missing:
                missing_fields_rows.append(
                    {
                        "ticker": ticker,
                        "taxonomy_source": "etf_universe",
                        "missing_required_fields": missing,
                    }
                )
            continue
        if upper in stock_map:
            record = stock_map[upper]
            missing = [f for f in sorted(STOCK_REQUIRED_FIELDS) if _is_missing_value(record.get(f))]
            mapped.append({"ticker": ticker, "taxonomy_source": "stock_universe"})
            if missing:
                missing_fields_rows.append(
                    {
                        "ticker": ticker,
                        "taxonomy_source": "stock_universe",
                        "missing_required_fields": missing,
                    }
                )
            continue
        unknown.append(ticker)
    return {
        "mapped": mapped,
        "unknown_tickers": sorted(set(unknown)),
        "missing_taxonomy_required_fields": missing_fields_rows,
    }


def _safe_get(obj: dict[str, Any], *keys: str) -> Any:
    cur: Any = obj
    for key in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _check_real_cash_behavior(
    fixture_weights: dict[str, Any],
    run_metadata: dict[str, Any],
    run_log_path: Path | None,
) -> dict[str, Any]:
    fixture_real_cash = [
        t for t in fixture_weights.keys() if str(t).strip().upper() in REAL_CASH_LABELS and float(fixture_weights.get(t) or 0) > 0
    ]
    fixture_real_cash_upper = {str(t).strip().upper() for t in fixture_real_cash}

    cash_handling = _safe_get(run_metadata, "analysis_setup", "analysis_portfolio", "cash_handling") or {}
    rm_holdings = cash_handling.get("real_cash_holdings") or []
    rm_holding_tickers_upper = {str(row.get("ticker") or "").strip().upper() for row in rm_holdings}

    checks: dict[str, Any] = {
        "fixture_real_cash_tickers": fixture_real_cash,
        "run_metadata_real_cash_holdings": rm_holdings,
        "cash_proxy_ticker": cash_handling.get("cash_proxy_ticker"),
        "real_cash_return_assumption": cash_handling.get("real_cash_return_assumption"),
        "real_cash_distinct_from_cash_proxy": cash_handling.get("real_cash_distinct_from_cash_proxy"),
    }

    issues: list[str] = []

    if fixture_real_cash:
        if not fixture_real_cash_upper.issubset(rm_holding_tickers_upper):
            issues.append("REAL_CASH_MISSING_IN_RUN_METADATA")
        if cash_handling.get("real_cash_return_assumption") != "zero_return_zero_volatility_no_price_download":
            issues.append("REAL_CASH_RETURN_ASSUMPTION_INVALID")
        if cash_handling.get("real_cash_distinct_from_cash_proxy") is not True:
            issues.append("REAL_CASH_NOT_DISTINCT_FROM_CASH_PROXY")

        resolved_weights = _safe_get(run_metadata, "analysis_setup", "analysis_portfolio", "weights") or {}
        for raw_ticker in fixture_real_cash:
            fx_w = float(fixture_weights.get(raw_ticker) or 0.0)
            rm_w = float(resolved_weights.get(raw_ticker) or 0.0)
            if not math.isclose(fx_w, rm_w, rel_tol=0.0, abs_tol=1e-9):
                issues.append(f"REAL_CASH_WEIGHT_MISMATCH:{raw_ticker}")

        if run_log_path and run_log_path.is_file():
            text = run_log_path.read_text(encoding="utf-8", errors="ignore")
            if "Cash USD']: possibly delisted" in text or "$Cash USD:" in text:
                issues.append("REAL_CASH_MARKET_DOWNLOAD_DETECTED_IN_LOG")
            checks["run_log_checked"] = True
        else:
            checks["run_log_checked"] = False
            checks["run_log_note"] = "run log not found; download-proof check unavailable"

    return {"checks": checks, "issues": sorted(set(issues))}


def _validate_fixture(
    *,
    fixture_path: Path,
    output_root: Path,
    etf_map: dict[str, dict[str, Any]],
    stock_map: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    fixture = _load_yaml(fixture_path) or {}
    if not isinstance(fixture, dict):
        raise RuntimeError(f"Fixture is not an object: {fixture_path}")

    fixture_id = fixture_path.stem.replace("fixture_matrix_", "")
    run_dir = output_root / fixture_id / "analysis_subject"
    run_metadata_path = run_dir / "run_metadata.json"
    run_log_path = (output_root / fixture_id / "step2_materialize.log")

    row: dict[str, Any] = {
        "fixture_id": fixture_id,
        "fixture_file": str(fixture_path.relative_to(REPO_ROOT)),
        "output_dir": str(run_dir.relative_to(REPO_ROOT)),
        "status": "ok",
        "errors": [],
        "warnings": [],
    }

    if not run_metadata_path.is_file():
        row["status"] = "failed"
        row["errors"].append("MISSING_RUN_METADATA")
        return row

    run_metadata = json.loads(run_metadata_path.read_text(encoding="utf-8"))
    fixture_tickers = [str(t) for t in (fixture.get("tickers") or [])]
    fixture_weights = fixture.get("current_weights") or {}

    # Input accepted correctly
    core_ok = bool(_safe_get(run_metadata, "analysis_setup", "core_mvp_input_surface", "core_mvp_requirements_met"))
    validation_status = str(_safe_get(run_metadata, "analysis_setup", "validation_result", "status") or "")
    resolution_status = str(_safe_get(run_metadata, "analysis_setup", "analysis_subject", "resolution_status") or "")
    if not core_ok:
        row["errors"].append("CORE_MVP_REQUIREMENTS_NOT_MET")
    if validation_status.lower() != "valid":
        row["errors"].append(f"INPUT_VALIDATION_STATUS_{validation_status or 'UNKNOWN'}")
    if resolution_status.lower() != "resolved":
        row["errors"].append(f"ANALYSIS_SUBJECT_STATUS_{resolution_status or 'UNKNOWN'}")

    # weights sum / investor_currency
    weight_sum = _safe_get(run_metadata, "analysis_setup", "analysis_portfolio", "weight_status", "weight_sum")
    if weight_sum is None or not math.isclose(float(weight_sum), 1.0, rel_tol=0.0, abs_tol=1e-6):
        row["errors"].append("WEIGHT_SUM_NOT_100")
    investor_currency = _safe_get(run_metadata, "resolved_config", "investor_currency")
    if not investor_currency:
        row["errors"].append("INVESTOR_CURRENCY_MISSING")

    # old input fields unexpectedly required
    required_groups = _safe_get(run_metadata, "analysis_setup", "core_mvp_input_surface", "required_user_input_groups") or []
    if list(required_groups) != EXPECTED_CORE_MVP_INPUT_GROUPS:
        row["errors"].append("UNEXPECTED_REQUIRED_INPUT_GROUPS")

    # taxonomy mapping checks
    taxonomy = _ticker_taxonomy_check(fixture_tickers, etf_map=etf_map, stock_map=stock_map)
    row["taxonomy"] = taxonomy
    if taxonomy["unknown_tickers"]:
        row["errors"].append("UNKNOWN_TICKER_IN_TAXONOMY")
    if taxonomy["missing_taxonomy_required_fields"]:
        row["warnings"].append("MISSING_TAXONOMY_REQUIRED_FIELDS")

    # real cash behavior
    real_cash = _check_real_cash_behavior(fixture_weights, run_metadata, run_log_path)
    row["real_cash"] = real_cash["checks"]
    if real_cash["issues"]:
        row["errors"].extend(real_cash["issues"])

    if row["errors"]:
        row["status"] = "failed"
    elif row["warnings"]:
        row["status"] = "partial"

    return row


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Core MVP Block 1 for fixture matrix runs")
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=REPO_ROOT / "tests" / "fixtures" / "mvp_portfolios",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=REPO_ROOT / "output" / "fixture_matrix_runs",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    fixtures_dir = args.fixtures_dir.resolve()
    output_root = args.output_root.resolve()

    etf_map = _load_universe_map(REPO_ROOT / "config" / "etf_universe.yml")
    stock_map = _load_universe_map(REPO_ROOT / "config" / "stock_universe.yml")

    fixture_paths = sorted(fixtures_dir.glob("fixture_matrix_fx*.yml"))
    if len(fixture_paths) != 7:
        raise RuntimeError(f"Expected 7 fixture files, found {len(fixture_paths)}")

    results: list[dict[str, Any]] = []
    for path in fixture_paths:
        row = _validate_fixture(
            fixture_path=path,
            output_root=output_root,
            etf_map=etf_map,
            stock_map=stock_map,
        )
        results.append(row)
        print(f"[{row['status'].upper()}] {row['fixture_id']}")

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "step": "step_3_block_1_validation",
        "fixtures_dir": str(fixtures_dir),
        "output_root": str(output_root),
        "counts": {
            "ok": sum(1 for r in results if r["status"] == "ok"),
            "partial": sum(1 for r in results if r["status"] == "partial"),
            "failed": sum(1 for r in results if r["status"] == "failed"),
        },
        "results": results,
    }
    out_path = output_root / "step3_block1_validation.json"
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSummary: {out_path}")
    return 0 if summary["counts"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
