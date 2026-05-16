from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_SOURCES = [
    REPO_ROOT / ".cursor" / "agents",
    REPO_ROOT / ".cursor" / "rules",
]
EXTRA_FILES = [REPO_ROOT / "AGENTS.md"]

FORBIDDEN_REFERENCES = [
    "docs/metrics_specification.md",
    "docs/docs/stress_testing_spec.md",
    "docs/portfolio_construction_policy.md",
    "docs/data_policy_nan_young_etfs.md",
    "ROADMAP.md",
]

LOCAL_REF_RE = re.compile(
    r"`([^`\n]+\.(?:md|mdc|py|yml|yaml|json|csv|txt))`"
    r"|\]\((?!https?://|mailto:)([^)#]+)"
)


def _source_files() -> list[Path]:
    files: list[Path] = []
    for directory in DOC_SOURCES:
        files.extend(sorted(directory.glob("*.md")))
        files.extend(sorted(directory.glob("*.mdc")))
    files.extend(path for path in EXTRA_FILES if path.exists())
    return files


def _normalize_ref(raw_ref: str) -> str | None:
    ref = raw_ref.strip().strip("<>").replace("\\", "/")
    if not ref or ref.startswith("#"):
        return None
    if ref.startswith(("http://", "https://", "mailto:", "app://")):
        return None
    if any(token in ref for token in ("*", "...", "<", ">", "{", "}", "[", "]")):
        return None
    if ref.startswith(("python ", "pytest ", "pip ", "git ")):
        return None
    if "/" not in ref and not ref.startswith((".cursor/", "docs/", "src/", "tests/")):
        return None
    if ref.startswith(("output/", "cache/", "results_csv/", "pdf files/", "pdf_md_sources/")):
        return None
    if ref.endswith((".json", ".csv", ".txt", ".yml", ".yaml")) and not ref.startswith(
        (".cursor/", "docs/", "src/", "tests/", "config/")
    ):
        return None
    if ref.startswith(("/", "\\")):
        ref = ref.lstrip("/\\")
    return ref.split("#", 1)[0]


def test_cursor_agent_docs_do_not_reference_removed_canonical_paths() -> None:
    failures: list[str] = []

    for path in _source_files():
        text = path.read_text(encoding="utf-8")
        for stale_ref in FORBIDDEN_REFERENCES:
            if stale_ref in text:
                failures.append(f"{path.relative_to(REPO_ROOT)} contains stale reference {stale_ref}")

    assert not failures, "\n".join(failures)


def test_cursor_agent_local_file_references_exist() -> None:
    failures: list[str] = []

    for path in _source_files():
        text = path.read_text(encoding="utf-8")
        for match in LOCAL_REF_RE.finditer(text):
            raw_ref = match.group(1) or match.group(2)
            ref = _normalize_ref(raw_ref)
            if ref is None:
                continue

            target = (REPO_ROOT / ref).resolve()
            try:
                target.relative_to(REPO_ROOT)
            except ValueError:
                continue

            if not target.exists():
                failures.append(f"{path.relative_to(REPO_ROOT)} references missing file {ref}")

    assert not failures, "\n".join(failures)
