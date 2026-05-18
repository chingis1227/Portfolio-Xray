"""Regression: representative generated outputs stay English and mojibake-free."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.generated_output_qa import (
    REPRESENTATIVE_REL_DIRS,
    scan_representative_outputs,
)


def test_representative_output_dirs_exist() -> None:
    repo = Path(__file__).resolve().parents[1]
    missing = [rel for rel in REPRESENTATIVE_REL_DIRS if not (repo / rel).is_dir()]
    assert not missing, f"missing representative output dirs: {missing}"


def test_representative_generated_outputs_language_qa() -> None:
    repo = Path(__file__).resolve().parents[1]
    result = scan_representative_outputs(repo)
    assert result.scanned_files > 0, "expected at least one representative text artifact"
    assert result.ok(), "\n".join(result.messages())
