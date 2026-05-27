#!/usr/bin/env python3
"""
Validate Core MVP Block 3 (Stress Lab) for fixture matrix runs (Step 5 only).

Reads:
  output/fixture_matrix_runs/<fixture_id>/analysis_subject/stress_report.json
  output/fixture_matrix_runs/<fixture_id>/analysis_subject/scenario_library.json (optional sidecar)

Writes:
  output/fixture_matrix_runs/step5_block3_validation.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.core_mvp_validation_contract import core_mvp_block3_fixture_status, core_mvp_block3_scenario_status

EXPECTED_HISTORICAL = ["dotcom", "2008", "2020", "2022", "banking_2023"]
EXPECTED_SYNTHETIC = [
    "equity_shock",
    "credit_shock",
    "rates_shock",
    "inflation_stagflation",
    "liquidity_shock",
    "usd_shock",
    "commodity_shock",
    "recession_severe",
]

REQUIRED_BLOCK3_KEYS = [
    "scenario_library_meta",
    "stress_results_v1",
    "hedge_gap_analysis_v1",
    "current_portfolio_stress_scorecard_v1",
]


def _is_missing(v: Any) -> bool:
    if v is None:
        return True
    if isinstance(v, str) and not v.strip():
        return True
    return False


def _scenario_status(
    *,
    scenario_type: str,
    scenario_id: str,
    v1_row: dict[str, Any] | None,
    raw_synthetic_row: dict[str, Any] | None,
    raw_historical_row: dict[str, Any] | None,
    hedge_row: dict[str, Any] | None,
) -> dict[str, Any]:
    v1_row = v1_row or {}
    raw_synthetic_row = raw_synthetic_row or {}
    raw_historical_row = raw_historical_row or {}
    hedge_row = hedge_row or {}

    availability = str(v1_row.get("availability") or "").strip().lower()

    if scenario_type == "synthetic":
        portfolio_pnl_pct = raw_synthetic_row.get("portfolio_pnl_pct")
        portfolio_loss_pct = v1_row.get("portfolio_loss_pct")
        loss_available = not _is_missing(portfolio_loss_pct) or not _is_missing(portfolio_pnl_pct)
        # Synthetic: portfolio_pnl_pct is mandatory in this audit contract.
        synthetic_pnl_required_present = not _is_missing(portfolio_pnl_pct)
        drawdown_available = not _is_missing(v1_row.get("drawdown_pct"))
    else:
        portfolio_loss_pct = v1_row.get("portfolio_loss_pct")
        max_dd = raw_historical_row.get("max_dd")
        pnl_real_episode = raw_historical_row.get("pnl_real_episode")
        # Historical: max_dd and/or pnl_real_episode required.
        historical_required_present = (not _is_missing(max_dd)) or (not _is_missing(pnl_real_episode))
        loss_available = not _is_missing(portfolio_loss_pct) or (not _is_missing(pnl_real_episode))
        drawdown_available = not _is_missing(v1_row.get("drawdown_pct")) or (not _is_missing(max_dd))

    loss_contribution = v1_row.get("loss_contribution") or {}
    factor_attr = v1_row.get("factor_attribution") or {}
    assets_helped = v1_row.get("assets_helped")
    assets_hurt = loss_contribution.get("assets_hurt")
    hedge_gap_available = not _is_missing(hedge_row.get("offset_coverage_ratio"))
    offset_ratio = hedge_row.get("offset_coverage_ratio")

    loss_contribution_available = (
        str(loss_contribution.get("availability") or "").lower() == "available"
        and bool(loss_contribution.get("pnl_by_asset_pct"))
    )
    factor_attr_available = (
        str(factor_attr.get("availability") or "").lower() == "available"
        and bool(factor_attr.get("pnl_by_factor_pct"))
    )
    helped_hurt_available = bool(assets_helped) or bool(assets_hurt)

    data_warnings: list[str] = []
    for source in (v1_row, raw_historical_row, hedge_row):
        if isinstance(source, dict):
            for key in ("reason_en", "data_quality", "data_availability_reason"):
                val = source.get(key)
                if isinstance(val, str) and val.strip():
                    data_warnings.append(val.strip())

    calculation_errors: list[str] = []
    # Treat explicit unavailability reasons as calculation/data issue signal.
    if availability == "unavailable":
        reason = str(v1_row.get("reason_en") or "").strip()
        if reason:
            calculation_errors.append(reason)
    if scenario_type == "synthetic" and not synthetic_pnl_required_present:
        calculation_errors.append("missing_portfolio_pnl_pct_required_for_synthetic")
    if scenario_type == "historical" and not historical_required_present:
        calculation_errors.append("missing_max_dd_and_pnl_real_episode_required_for_historical")

    # Status rules
    if scenario_type == "synthetic":
        if not synthetic_pnl_required_present:
            status = "failed"
        elif availability == "unavailable":
            status = "unavailable"
        elif all([loss_available, loss_contribution_available, factor_attr_available, hedge_gap_available]):
            status = "ok"
        else:
            status = "partial"
    else:
        if not historical_required_present:
            status = "failed" if availability != "unavailable" else "unavailable"
        elif availability == "unavailable":
            status = "unavailable"
        elif all([loss_available, drawdown_available, loss_contribution_available, factor_attr_available]):
            status = "ok"
        else:
            status = "partial"

    out = {
        "scenario_id": scenario_id,
        "scenario_type": scenario_type,
        "status": status,
        "availability": availability or None,
        "portfolio_loss_available": loss_available,
        "drawdown_available": drawdown_available,
        "asset_loss_contribution_available": loss_contribution_available,
        "factor_attribution_available": factor_attr_available,
        "assets_helped_hurt_available": helped_hurt_available,
        "hedge_gap_available": hedge_gap_available,
        "offset_coverage_ratio_available": not _is_missing(offset_ratio),
        "offset_coverage_ratio": offset_ratio,
        "data_warnings": sorted(set(data_warnings)),
        "calculation_errors": sorted(set(calculation_errors)),
    }
    if scenario_type == "synthetic":
        out["portfolio_pnl_pct_present"] = synthetic_pnl_required_present
        out["portfolio_pnl_pct"] = raw_synthetic_row.get("portfolio_pnl_pct")
    else:
        out["historical_required_max_dd_or_pnl_real_episode_present"] = historical_required_present
        out["max_dd"] = raw_historical_row.get("max_dd")
        out["pnl_real_episode"] = raw_historical_row.get("pnl_real_episode")
    return out


def _validate_fixture(stress_report_path: Path) -> dict[str, Any]:
    fixture_id = stress_report_path.parents[1].name
    base_dir = stress_report_path.parent
    report = json.loads(stress_report_path.read_text(encoding="utf-8"))

    row: dict[str, Any] = {
        "fixture_id": fixture_id,
        "stress_report_path": str(stress_report_path.relative_to(REPO_ROOT)),
        "status": "ok",
        "missing_block3_keys": [],
        "scenario_library": {},
        "scenario_coverage": {},
        "scenario_results": {"synthetic": [], "historical": []},
    }

    for key in REQUIRED_BLOCK3_KEYS:
        if key not in report:
            row["missing_block3_keys"].append(key)

    scenario_library_sidecar = base_dir / "scenario_library.json"
    scenario_library_meta = report.get("scenario_library_meta") or {}
    row["scenario_library"] = {
        "meta_present": "scenario_library_meta" in report,
        "sidecar_present": scenario_library_sidecar.is_file(),
        "meta_keys": list(scenario_library_meta.keys()) if isinstance(scenario_library_meta, dict) else [],
    }

    v1 = report.get("stress_results_v1") or {}
    synthetic_rows = v1.get("synthetic_scenarios") or []
    historical_rows = v1.get("historical_episodes") or []
    raw_synthetic_rows = report.get("scenario_results") or []
    raw_historical_rows = report.get("historical_results") or []
    hedge_rows = (report.get("hedge_gap_analysis_v1") or {}).get("by_risk_type") or []

    v1_syn_map = {str(r.get("scenario_id")): r for r in synthetic_rows if isinstance(r, dict)}
    v1_hist_map = {str(r.get("episode")): r for r in historical_rows if isinstance(r, dict)}
    raw_syn_map = {str(r.get("scenario_id")): r for r in raw_synthetic_rows if isinstance(r, dict)}
    raw_hist_map = {str(r.get("episode")): r for r in raw_historical_rows if isinstance(r, dict)}
    hedge_map = {str(r.get("linked_scenario_id")): r for r in hedge_rows if isinstance(r, dict)}

    present_syn_ids = sorted([k for k in v1_syn_map.keys() if k and k != "None"])
    present_hist_ids = sorted([k for k in v1_hist_map.keys() if k and k != "None"])
    missing_syn = sorted(set(EXPECTED_SYNTHETIC) - set(present_syn_ids))
    missing_hist = sorted(set(EXPECTED_HISTORICAL) - set(present_hist_ids))

    row["scenario_coverage"] = {
        "expected_synthetic": EXPECTED_SYNTHETIC,
        "expected_historical": EXPECTED_HISTORICAL,
        "present_synthetic": present_syn_ids,
        "present_historical": present_hist_ids,
        "missing_synthetic": missing_syn,
        "missing_historical": missing_hist,
    }

    for sid in EXPECTED_SYNTHETIC:
        row["scenario_results"]["synthetic"].append(
            _scenario_status(
                scenario_type="synthetic",
                scenario_id=sid,
                v1_row=v1_syn_map.get(sid),
                raw_synthetic_row=raw_syn_map.get(sid),
                raw_historical_row=None,
                hedge_row=hedge_map.get(sid),
            )
        )

    for sid in EXPECTED_HISTORICAL:
        row["scenario_results"]["historical"].append(
            _scenario_status(
                scenario_type="historical",
                scenario_id=sid,
                v1_row=v1_hist_map.get(sid),
                raw_synthetic_row=None,
                raw_historical_row=raw_hist_map.get(sid),
                hedge_row=hedge_map.get(sid),
            )
        )

    scenario_rows = row["scenario_results"]["synthetic"] + row["scenario_results"]["historical"]
    audit_statuses = [r["status"] for r in scenario_rows]
    core_statuses = [core_mvp_block3_scenario_status(r) for r in scenario_rows]
    row["core_mvp_scenario_statuses"] = {
        "audit": audit_statuses,
        "core_mvp": core_statuses,
    }
    row["status"] = core_mvp_block3_fixture_status(
        missing_block3_keys=row["missing_block3_keys"],
        missing_synthetic=missing_syn,
        missing_historical=missing_hist,
        scenario_rows=scenario_rows,
    )
    row["audit_status"] = (
        "failed"
        if row["missing_block3_keys"] or "failed" in audit_statuses
        else "partial"
        if missing_syn or missing_hist or "partial" in audit_statuses or "unavailable" in audit_statuses
        else "ok"
    )

    return row


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Block 3 fixture matrix outputs")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=REPO_ROOT / "output" / "fixture_matrix_runs",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    output_root = args.output_root.resolve()

    results: list[dict[str, Any]] = []
    for fixture_dir in sorted([p for p in output_root.glob("fx*") if p.is_dir()]):
        p = fixture_dir / "analysis_subject" / "stress_report.json"
        if not p.is_file():
            results.append(
                {
                    "fixture_id": fixture_dir.name,
                    "stress_report_path": str(p.relative_to(REPO_ROOT)),
                    "status": "failed",
                    "error": "MISSING_STRESS_REPORT_JSON",
                }
            )
            print(f"[FAILED] {fixture_dir.name} (missing stress_report.json)")
            continue

        row = _validate_fixture(p)
        results.append(row)
        print(f"[{row['status'].upper()}] {row['fixture_id']}")

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "step": "step_5_block_3_validation",
        "output_root": str(output_root),
        "validation_contract": "core_mvp_blocks_1_3_v2",
        "counts": {
            "ok": sum(1 for r in results if r["status"] == "ok"),
            "partial": sum(1 for r in results if r["status"] == "partial"),
            "failed": sum(1 for r in results if r["status"] == "failed"),
        },
        "audit_status_counts": {
            "ok": sum(1 for r in results if r.get("audit_status") == "ok"),
            "partial": sum(1 for r in results if r.get("audit_status") == "partial"),
            "failed": sum(1 for r in results if r.get("audit_status") == "failed"),
        },
        "results": results,
    }
    out_path = output_root / "step5_block3_validation.json"
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSummary: {out_path}")
    return 0 if summary["counts"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
