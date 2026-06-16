"""Shared implementation for legacy root runner wrappers."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


LEGACY_RUNNER_WARNING = (
    "WARNING: legacy compatibility runner. This is not the Core MVP product path. "
    "Use run_core_diagnostics.py, run_portfolio_review.py, or "
    "scripts/run_blocks_5_to_9_vertical_flow.py for the current product flow.\n"
)


def run_legacy_runner(relative_runner_path: str) -> int:
    """Delegate a root legacy wrapper to its implementation under ``legacy/runners``."""
    root = Path(__file__).resolve().parents[1]
    target = root.joinpath(*relative_runner_path.split("/"))
    cmd = [sys.executable, str(target), *sys.argv[1:]]
    sys.stderr.write(LEGACY_RUNNER_WARNING)
    return int(subprocess.call(cmd, cwd=str(root)))
