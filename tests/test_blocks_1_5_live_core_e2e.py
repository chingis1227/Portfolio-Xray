"""Live networked core review acceptance gate (Phase 17 RM-1021).

Skipped by default. Enable with ``pytest --live-core`` or env ``PORTFOLIO_LIVE_CORE_E2E=1``.
Run the orchestrator first (or use ``scripts/verify_live_core_e2e.py --run``), then validate
artifacts with this test or the script.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.config import load_validated_config
from src.live_core_e2e import validate_live_core_artifacts

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.live_core
def test_live_core_e2e_artifacts_match_acceptance() -> None:
    cfg = load_validated_config(REPO_ROOT / "config.yml")
    output_dir = REPO_ROOT / cfg.output_dir_final
    result = validate_live_core_artifacts(output_dir)
    if not result.ok:
        pytest.fail("\n".join(result.messages()))
