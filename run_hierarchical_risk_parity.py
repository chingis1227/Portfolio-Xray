"""LEGACY RUNNER WRAPPER — implementation lives in legacy/runners/run_hierarchical_risk_parity.py.

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
    target = root / "legacy" / "runners" / "run_hierarchical_risk_parity.py"
    cmd = [sys.executable, str(target), *sys.argv[1:]]
    return int(subprocess.call(cmd, cwd=str(root)))

if __name__ == "__main__":
    raise SystemExit(main())
