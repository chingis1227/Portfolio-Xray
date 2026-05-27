#!/usr/bin/env python3
"""
Validate Core MVP Block 2 (Portfolio X-Ray) for fixture matrix runs (Step 4 only).

Reads:
  output/fixture_matrix_runs/<fixture_id>/analysis_subject/portfolio_xray.json

Writes:
  output/fixture_matrix_runs/step4_block2_validation.json
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

BLOCK_KEYS = [
    "block_2_1_asset_allocation",
    "block_2_2_portfolio_metrics",
    "block_2_3_factor_exposure",
    "block_2_4_hidden_exposure",
    "block_2_5_risk_budget_view",
    "block_2_6_portfolio_weakness_map",
]

DERIVED_REQUIRED_FIELDS = {
    "block_2_1_asset_allocation": [
        "portfolio_composition_snapshot",
        "capital_allocation_breakdown",
        "actual_economic_exposure_summary",
    ],
    "block_2_2_portfolio_metrics": [
        "portfolio_behavior_snapshot",
        "return_risk_metrics",
        "drawdown_diagnostics",
    ],
}

BLOCK_23_REQUIRED_FIELDS = [
    "factor_universe",
    "factor_betas_5y",
    "factor_betas_10y",
    "kalman_current_beta",
    "factor_significance_confidence",
    "factor_variance_contribution",
    "stress_lab_separation",
]

STRESS_LEAKAGE_PATTERNS = [
    re.compile(r"scenario", re.IGNORECASE),
    re.compile(r"stress_results", re.IGNORECASE),
    re.compile(r"historical_results", re.IGNORECASE),
    re.compile(r"pnl", re.IGNORECASE),
    re.compile(r"drawdown", re.IGNORECASE),
]


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def _block_status(block: dict[str, Any], block_key: str) -> str:
    explicit = str(block.get("status") or "").strip().lower()
    if explicit in {"ok", "partial", "unavailable", "failed"}:
        return explicit

    required = DERIVED_REQUIRED_FIELDS.get(block_key, [])
    missing = [field for field in required if _is_missing(block.get(field))]
    if missing:
        return "partial"
    return "ok"


def _block_missing_fields(block: dict[str, Any], block_key: str) -> list[str]:
    required = list(DERIVED_REQUIRED_FIELDS.get(block_key, []))
    if block_key == "block_2_3_factor_exposure":
        required.extend(BLOCK_23_REQUIRED_FIELDS)
    return [field for field in required if _is_missing(block.get(field))]


def _to_warning_texts(raw: Any) -> list[str]:
    out: list[str] = []
    if isinstance(raw, list):
        for row in raw:
            if isinstance(row, dict):
                msg = row.get("message") or row.get("warning") or row.get("code")
                if msg:
                    out.append(str(msg))
            elif row is not None:
                out.append(str(row))
    elif isinstance(raw, dict):
        msg = raw.get("message") or raw.get("warning") or raw.get("code")
        if msg:
            out.append(str(msg))
    elif raw is not None:
        out.append(str(raw))
    return out


def _classify_warning_domains(warnings: list[str]) -> dict[str, int]:
    domains = {
        "taxonomy": 0,
        "factor": 0,
        "metrics": 0,
        "risk_budget": 0,
        "hidden_exposure": 0,
        "weakness_map": 0,
        "data_quality": 0,
    }
    for w in warnings:
        lw = w.lower()
        if "taxonom" in lw:
            domains["taxonomy"] += 1
        if "factor" in lw or "beta" in lw:
            domains["factor"] += 1
        if "metric" in lw or "vol" in lw or "sharpe" in lw:
            domains["metrics"] += 1
        if "risk budget" in lw or "rc_" in lw:
            domains["risk_budget"] += 1
        if "hidden" in lw or "concentration" in lw:
            domains["hidden_exposure"] += 1
        if "weakness" in lw:
            domains["weakness_map"] += 1
        if "data" in lw or "missing" in lw or "unavailable" in lw:
            domains["data_quality"] += 1
    return domains


def _check_block_23(block: dict[str, Any]) -> dict[str, Any]:
    b5 = block.get("factor_betas_5y") or {}
    b10 = block.get("factor_betas_10y") or {}
    kalman = block.get("kalman_current_beta") or {}
    signif = block.get("factor_significance_confidence") or {}
    variance = block.get("factor_variance_contribution") or {}
    stress_sep = block.get("stress_lab_separation") or {}

    significance_present = False
    if isinstance(signif, dict) and signif:
        # at least one factor entry has explicit significance diagnostics
        for _, payload in signif.items():
            if isinstance(payload, dict) and any(
                key in payload for key in ("status", "t_stat", "p_value", "hac_used", "comment")
            ):
                significance_present = True
                break

    # Ensure Block 2.3 does not contain raw stress/scenario payloads.
    leakage_hits: list[str] = []
    for key in block.keys():
        lk = str(key)
        if lk in {"stress_lab_separation"}:
            continue
        for pattern in STRESS_LEAKAGE_PATTERNS:
            if pattern.search(lk):
                leakage_hits.append(lk)
                break

    return {
        "factor_betas_available_5y": b5.get("status"),
        "factor_betas_available_10y": b10.get("status"),
        "missing_factors_5y": b5.get("missing_beta_keys") or [],
        "missing_factors_10y": b10.get("missing_beta_keys") or [],
        "kalman_available": kalman.get("available"),
        "kalman_reason": kalman.get("reason"),
        "significance_outputs_present": significance_present,
        "variance_contribution_status": variance.get("status"),
        "variance_contribution_method": variance.get("method"),
        "stress_separation_flag": stress_sep.get("no_scenario_shocks_in_this_block"),
        "stress_leakage_keys": sorted(set(leakage_hits)),
    }


def _validate_fixture(portfolio_xray_path: Path) -> dict[str, Any]:
    fixture_id = portfolio_xray_path.parents[1].name
    xray = json.loads(portfolio_xray_path.read_text(encoding="utf-8"))

    result: dict[str, Any] = {
        "fixture_id": fixture_id,
        "portfolio_xray_path": str(portfolio_xray_path.relative_to(REPO_ROOT)),
        "status": "ok",
        "missing_blocks": [],
        "block_results": {},
    }

    for block_key in BLOCK_KEYS:
        block = xray.get(block_key)
        if not isinstance(block, dict):
            result["missing_blocks"].append(block_key)
            result["block_results"][block_key] = {
                "status": "failed",
                "missing_fields": [],
                "warnings": ["BLOCK_MISSING"],
                "warning_domains": {},
            }
            continue

        status = _block_status(block, block_key)
        missing_fields = _block_missing_fields(block, block_key)
        warnings = _to_warning_texts(block.get("data_quality_warnings"))
        warning_domains = _classify_warning_domains(warnings)

        block_row: dict[str, Any] = {
            "status": status,
            "missing_fields": missing_fields,
            "warnings": warnings,
            "warning_domains": warning_domains,
        }
        if block_key == "block_2_3_factor_exposure":
            block_row["special_checks"] = _check_block_23(block)
            if block_row["special_checks"]["stress_leakage_keys"]:
                # leakage in Block 2.3 is a hard failure
                block_row["status"] = "failed"

        result["block_results"][block_key] = block_row

    # Fixture rollup status
    statuses = [v["status"] for v in result["block_results"].values()]
    if "failed" in statuses:
        result["status"] = "failed"
    elif any(s in {"partial", "unavailable"} for s in statuses):
        result["status"] = "partial"
    else:
        result["status"] = "ok"

    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Block 2 fixture matrix outputs")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=REPO_ROOT / "output" / "fixture_matrix_runs",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    output_root = args.output_root.resolve()
    fixture_dirs = sorted([p for p in output_root.glob("fx*") if p.is_dir()])

    results: list[dict[str, Any]] = []
    for fixture_dir in fixture_dirs:
        p = fixture_dir / "analysis_subject" / "portfolio_xray.json"
        if not p.is_file():
            results.append(
                {
                    "fixture_id": fixture_dir.name,
                    "portfolio_xray_path": str(p.relative_to(REPO_ROOT)),
                    "status": "failed",
                    "missing_blocks": BLOCK_KEYS,
                    "block_results": {},
                    "error": "MISSING_PORTFOLIO_XRAY_JSON",
                }
            )
            print(f"[FAILED] {fixture_dir.name} (missing portfolio_xray.json)")
            continue

        row = _validate_fixture(p)
        results.append(row)
        print(f"[{row['status'].upper()}] {row['fixture_id']}")

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "step": "step_4_block_2_validation",
        "output_root": str(output_root),
        "counts": {
            "ok": sum(1 for r in results if r["status"] == "ok"),
            "partial": sum(1 for r in results if r["status"] == "partial"),
            "failed": sum(1 for r in results if r["status"] == "failed"),
        },
        "results": results,
    }
    out_path = output_root / "step4_block2_validation.json"
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSummary: {out_path}")
    return 0 if summary["counts"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
