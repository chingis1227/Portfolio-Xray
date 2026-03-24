from __future__ import annotations

"""
Run one portfolio variant pipeline and print only stress results.

Usage:
  python run_stress_variant.py --variant equal-weight
  python run_stress_variant.py --variant risk-parity
  python run_stress_variant.py --variant main
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run selected portfolio pipeline and print compact stress results only."
    )
    parser.add_argument(
        "--variant",
        required=True,
        choices=("equal-weight", "risk-parity", "main"),
        help="Portfolio variant to run.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Pass --no-cache to the underlying pipeline script.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show full underlying pipeline stdout/stderr.",
    )
    return parser.parse_args()


def _variant_to_script(variant: str) -> tuple[Path, Path]:
    if variant == "equal-weight":
        return PROJECT_ROOT / "run_equal_weight.py", PROJECT_ROOT / "equal-weight portfolio" / "stress_report.json"
    if variant == "risk-parity":
        return PROJECT_ROOT / "run_risk_parity.py", PROJECT_ROOT / "risk parity portfolio" / "stress_report.json"
    # variant == "main"
    return PROJECT_ROOT / "run_optimization.py", PROJECT_ROOT / "Main portfolio" / "stress_report.json"


def _print_compact_stress(stress_report: dict) -> None:
    status = stress_report.get("status", "N/A")
    fail_reason = stress_report.get("fail_reason_code") or stress_report.get("warning_code") or "—"
    worst_loss = stress_report.get("worst_scenario_loss_pct")
    failed_scenario = stress_report.get("failed_scenario") or "—"
    failed_test = stress_report.get("failed_test") or "—"

    print("\n=== Stress Result ===")
    print(f"status: {status}")
    print(f"reason: {fail_reason}")
    print(f"worst_scenario_loss_pct: {worst_loss}")
    print(f"failed_scenario: {failed_scenario}")
    print(f"failed_test: {failed_test}")

    factor_betas_5y = stress_report.get("factor_betas_5y") or {}
    factor_betas_10y = stress_report.get("factor_betas_10y") or {}
    if factor_betas_5y:
        print(f"factor_betas_5y: {json.dumps(factor_betas_5y, ensure_ascii=False)}")
    if factor_betas_10y:
        print(f"factor_betas_10y: {json.dumps(factor_betas_10y, ensure_ascii=False)}")

    scenario_rows = stress_report.get("scenario_results") or []
    if scenario_rows:
        print("\nscenarios:")
        for row in scenario_rows:
            sid = row.get("scenario_id", "unknown")
            pnl = row.get("portfolio_pnl_pct")
            p = row.get("pass")
            top1 = row.get("top1_rc_pct")
            top3 = row.get("top3_rc_sum_pct")
            print(
                f"- {sid}: pnl={pnl}, pass={p}, top1_rc={top1}, top3_rc_sum={top3}"
            )


def run_stress_for_variant(variant: str, *, no_cache: bool = False, verbose: bool = False) -> int:
    """
    Run one official pipeline script for the selected variant,
    then print only the stress section from the produced stress_report.json.
    """
    script_path, stress_report_path = _variant_to_script(variant)
    cmd = [sys.executable, str(script_path)]
    if no_cache:
        cmd.append("--no-cache")

    print(f"Running: {' '.join(cmd)}")
    completed = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=not verbose,
        text=True,
    )
    if completed.returncode != 0:
        print(f"\nPipeline failed with exit code {completed.returncode}.")
        if not verbose:
            if completed.stdout:
                print("\n--- pipeline stdout (tail) ---")
                print("\n".join(completed.stdout.splitlines()[-30:]))
            if completed.stderr:
                print("\n--- pipeline stderr (tail) ---")
                print("\n".join(completed.stderr.splitlines()[-30:]))
        return completed.returncode

    if not stress_report_path.exists():
        print(f"\nStress report not found: {stress_report_path}")
        return 1

    with open(stress_report_path, encoding="utf-8") as f:
        stress_report = json.load(f)
    _print_compact_stress(stress_report)
    return 0


def main() -> None:
    args = parse_args()
    exit_code = run_stress_for_variant(args.variant, no_cache=args.no_cache, verbose=args.verbose)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()

