"""One-off helper: move legacy run_* scripts and install root wrappers."""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LEGACY_DIR = REPO_ROOT / "legacy" / "runners"

LEGACY_SCRIPT_NAMES = [
    "run_optimization.py",
    "run_mvp_workflow.py",
    "run_equal_weight.py",
    "run_risk_parity.py",
    "run_equal_weight_by_asset_class.py",
    "run_minimum_variance.py",
    "run_minimum_variance_advanced.py",
    "run_minimum_variance_uncapped.py",
    "run_minimum_cvar_constrained.py",
    "run_minimum_cvar_uncapped.py",
    "run_maximum_diversification.py",
    "run_maximum_diversification_unconstrained.py",
    "run_hierarchical_risk_parity.py",
    "run_risk_budget_by_asset.py",
    "run_risk_budget_by_asset_class.py",
    "run_robust_mean_variance_constrained.py",
    "run_robust_mean_variance_uncapped.py",
    "run_robust_scenario_optimization.py",
    "run_robust_scenario_portfolio_report.py",
    "run_robust_mv_lambda_calibration.py",
    "run_stress_variant.py",
    "run_rebalance.py",
    "run_view_after_optimization.py",
    "run_compare_ew_rp.py",
    "run_advanced_mv_lambda_sensitivity.py",
]

PATHS_IMPORT = "from legacy.runners._paths import REPO_ROOT\n"
PATHS_IMPORT_ALT = "from legacy.runners._paths import REPO_ROOT, RUNNERS_DIR\n"

WRAPPER_TEMPLATE = '''\
"""LEGACY RUNNER WRAPPER — implementation lives in legacy/runners/{name}.

Prefer Core MVP entrypoints:
  python run_core_diagnostics.py
  python run_portfolio_review.py
See docs/runtime_entrypoints.md.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

def main() -> int:
    root = Path(__file__).resolve().parent
    target = root / "legacy" / "runners" / "{name}"
    cmd = [sys.executable, str(target), *sys.argv[1:]]
    return int(subprocess.call(cmd, cwd=str(root)))

if __name__ == "__main__":
    raise SystemExit(main())
'''


def _patch_legacy_source(text: str) -> str:
    if "from legacy.runners._paths import REPO_ROOT" not in text:
        # Insert after module docstring / future import block
        lines = text.splitlines(keepends=True)
        insert_at = 0
        if lines and lines[0].startswith('"""'):
            for i, line in enumerate(lines[1:], 1):
                if line.strip().endswith('"""'):
                    insert_at = i + 1
                    break
        if insert_at < len(lines) and "from __future__" in lines[insert_at]:
            insert_at += 1
        lines.insert(insert_at, PATHS_IMPORT)
        text = "".join(lines)
    text = text.replace("Path(__file__).resolve().parent", "REPO_ROOT")
    text = text.replace("_SCRIPT_ROOT = REPO_ROOT", "_SCRIPT_ROOT = REPO_ROOT")
    return text


def migrate(dry_run: bool = False) -> None:
    LEGACY_DIR.mkdir(parents=True, exist_ok=True)
    for name in LEGACY_SCRIPT_NAMES:
        src = REPO_ROOT / name
        dst = LEGACY_DIR / name
        if not src.is_file():
            print(f"skip missing: {name}")
            continue
        if dst.is_file() and not src.is_file():
            print(f"already migrated: {name}")
            continue
        body = src.read_text(encoding="utf-8")
        patched = _patch_legacy_source(body)
        wrapper = WRAPPER_TEMPLATE.format(name=name)
        print(f"migrate {name}")
        if dry_run:
            continue
        if not dst.is_file():
            dst.write_text(patched, encoding="utf-8")
            src.unlink()
        src.write_text(wrapper, encoding="utf-8")


if __name__ == "__main__":
    migrate(dry_run="--dry-run" in sys.argv)
