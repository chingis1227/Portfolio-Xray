"""Fix UTF-8 text mis-decoded via cp1251 and saved as UTF-8 again (whole-file heuristic)."""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

SKIP_PARTS = {
    "pdf files",
    "pdf_md_sources",
    "cache",
    "output",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    ".git",
    "Main portfolio",
    "equal-weight portfolio",
    "risk parity portfolio",
}


def iter_targets() -> list[Path]:
    roots = [REPO / "src", REPO / "docs", REPO / ".cursor", REPO / "config_ui", REPO / "tests"]
    root_files = [REPO / "run_report.py", REPO / "run_optimization.py", REPO / "results_dashboard"]
    out: list[Path] = []
    for r in roots:
        if not r.exists():
            continue
        if r.is_file():
            out.append(r)
            continue
        for p in r.rglob("*"):
            if not p.is_file():
                continue
            if any(s in p.parts for s in SKIP_PARTS):
                continue
            if p.suffix.lower() in {".py", ".md", ".mdc"}:
                out.append(p)
    for p in [REPO / "run_report.py", REPO / "run_optimization.py"]:
        if p.exists():
            out.append(p)
    if (REPO / "results_dashboard" / "app.py").exists():
        out.append(REPO / "results_dashboard" / "app.py")
    return sorted(set(out))


def cp1251_score(text: str) -> int:
    """Lower is better: count suspicious mojibake lead bytes."""
    return len(re.findall(r"\u0420.", text))


def try_fix_file(text: str) -> str | None:
    if cp1251_score(text) < 3:
        return None
    try:
        fixed = text.encode("cp1251").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return None
    if cp1251_score(fixed) < cp1251_score(text):
        return fixed
    return None


def main() -> None:
    updated = 0
    for path in iter_targets():
        try:
            original = path.read_text(encoding="utf-8-sig")
        except (UnicodeDecodeError, OSError):
            continue
        fixed = try_fix_file(original)
        if fixed is None or fixed == original:
            continue
        path.write_text(fixed, encoding="utf-8", newline="\n")
        print(f"updated {path.relative_to(REPO)}")
        updated += 1
    print(f"done: {updated} file(s)")


if __name__ == "__main__":
    main()
