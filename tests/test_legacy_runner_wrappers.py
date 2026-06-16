"""Legacy root wrappers must identify themselves before delegation."""

from __future__ import annotations

import sys
from pathlib import Path

from src.legacy_runner_wrapper import LEGACY_RUNNER_WARNING, run_legacy_runner


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


def test_legacy_wrapper_helper_warns_and_delegates(monkeypatch, capsys) -> None:
    calls: list[tuple[list[str], str]] = []

    def fake_call(cmd: list[str], cwd: str) -> int:
        calls.append((cmd, cwd))
        return 7

    monkeypatch.setattr(sys, "argv", ["run_equal_weight.py", "--dry-run"])
    monkeypatch.setattr("src.legacy_runner_wrapper.subprocess.call", fake_call)

    exit_code = run_legacy_runner("legacy/runners/run_equal_weight.py")

    assert exit_code == 7
    assert len(calls) == 1
    cmd, cwd = calls[0]
    assert cmd[0] == sys.executable
    assert cmd[-1] == "--dry-run"
    assert Path(cmd[1]).as_posix().endswith("legacy/runners/run_equal_weight.py")
    assert Path(cwd).is_dir()
    assert LEGACY_RUNNER_WARNING in capsys.readouterr().err
