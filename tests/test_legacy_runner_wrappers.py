"""Legacy root wrappers must identify themselves before delegation."""

from __future__ import annotations

from pathlib import Path


def test_legacy_root_wrappers_emit_runtime_warning() -> None:
    root = Path(__file__).resolve().parents[1]
    wrappers = [
        path
        for path in root.glob("run_*.py")
        if "LEGACY RUNNER WRAPPER" in path.read_text(encoding="utf-8")
    ]

    assert wrappers
    for path in wrappers:
        text = path.read_text(encoding="utf-8")
        assert "WARNING: legacy compatibility runner" in text, path.name
        assert "not the Core MVP product path" in text, path.name
        assert "scripts/run_blocks_5_to_9_vertical_flow.py" in text, path.name
