#!/usr/bin/env python3
"""Verify source Markdown links and stale documentation references."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.docs_verify import verify_docs  # noqa: E402


def main() -> int:
    result = verify_docs()
    messages = result.messages()
    if not messages:
        print("docs verification: OK")
        return 0
    print("docs verification: FAILED", file=sys.stderr)
    for line in messages:
        print(line, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
