"""Repository paths for scripts under legacy/runners/."""

from __future__ import annotations

from pathlib import Path

# legacy/runners/_paths.py -> repo root is two levels up
REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNERS_DIR = Path(__file__).resolve().parent
