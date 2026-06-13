"""Fix module docstring placement in legacy/runners after migration."""

from __future__ import annotations

import re
from pathlib import Path

LEGACY = Path(__file__).resolve().parents[1] / "legacy" / "runners"
PATHS_LINE = "from legacy.runners._paths import REPO_ROOT\n"


def fix_file(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "REPO_ROOT" not in text and PATHS_LINE not in text:
        return
    text = text.replace(PATHS_LINE, "")
    lines = text.splitlines(keepends=True)
    # Drop leading blank lines
    while lines and lines[0].strip() == "":
        lines.pop(0)
    future_lines: list[str] = []
    while lines and lines[0].startswith("from __future__"):
        future_lines.append(lines.pop(0))
    body = "".join(lines)
    doc_match = re.search(r'("""[\s\S]*...""")', body)
    if not doc_match:
        text = "".join(future_lines) + PATHS_LINE + body
    else:
        doc = doc_match.group(1)
        doc_end = doc_match.end()
        after_doc = body[doc_end:].lstrip("\n")
        before_doc = body[: doc_match.start()]
        if before_doc.strip():
            # Docstring not at start of body; leave as-is with paths at top of after_doc
            text = "".join(future_lines) + before_doc + doc + "\n" + PATHS_LINE + "\n" + after_doc
        else:
            text = "".join(future_lines) + doc + "\n" + PATHS_LINE + "\n" + after_doc
    path.write_text(text, encoding="utf-8")
    print(f"fixed {path.name}")


def main() -> None:
    for path in sorted(LEGACY.glob("run_*.py")):
        fix_file(path)


if __name__ == "__main__":
    main()
