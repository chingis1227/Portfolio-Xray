"""LEGACY RUNNER WRAPPER - implementation lives in legacy/runners/run_minimum_cvar_constrained.py.

Prefer Core MVP entrypoints:
  python run_core_diagnostics.py
  python run_portfolio_review.py
See docs/runtime_entrypoints.md.

Emits "WARNING: legacy compatibility runner" and reminds callers this is
"not the Core MVP product path"; the shared helper also points to
"scripts/run_blocks_5_to_9_vertical_flow.py" for the current product flow.
"""
from __future__ import annotations

from src.legacy_runner_wrapper import run_legacy_runner

LEGACY_RUNNER = "legacy/runners/run_minimum_cvar_constrained.py"


def main() -> int:
    return run_legacy_runner(LEGACY_RUNNER)


if __name__ == "__main__":
    raise SystemExit(main())
