"""LEGACY RUNNER WRAPPER — implementation lives in legacy/runners/run_compare_ew_rp.py.

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
    target = root / "legacy" / "runners" / "run_compare_ew_rp.py"
    cmd = [sys.executable, str(target), *sys.argv[1:]]
    sys.stderr.write(
        "WARNING: legacy compatibility runner. This is not the Core MVP product path. "
        "Use run_core_diagnostics.py, run_portfolio_review.py, or "
        "scripts/run_blocks_5_to_9_vertical_flow.py for the current product flow.\n"
    )
    return int(subprocess.call(cmd, cwd=str(root)))

if __name__ == "__main__":
    raise SystemExit(main())
