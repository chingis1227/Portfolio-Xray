#!/usr/bin/env python3
"""QA scan for representative generated outputs (language / mojibake)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.generated_output_qa import scan_representative_outputs  # noqa: E402


def main() -> int:
    result = scan_representative_outputs(REPO_ROOT)
    if result.ok():
        print(
            f"generated-output QA: OK ({result.scanned_files} text files scanned)"
        )
        return 0
    print("generated-output QA: FAILED", file=sys.stderr)
    for line in result.messages():
        print(line, file=sys.stderr)
    print(
        f"scanned {result.scanned_files} files; {len(result.findings)} finding(s)",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
