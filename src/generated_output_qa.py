"""Scan representative generated outputs for mojibake and non-English prose issues."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

# Common UTF-8 read as cp1251 artifacts (em dash, quotes, bullets).
MOJIBAKE_SUBSTRINGS: tuple[str, ...] = (
    "\u0432\u0402",
    "\u0432\u0402",
    "\u00e2\u20ac",
    "\u0432\u0402",
    "\u041e\u201d",
    "\u00e2\u20ac\u201d",
    "\u00ce",
    "\u00d0",
    "\ufffd",
)

# Cyrillic letters in prose (exclude path-only lines).
_CYRILLIC_RE = re.compile(r"[\u0400-\u04ff]")
_PATH_LIKE_RE = re.compile(
    r"(...:^[A-Za-z]:\\)|(...:^Source:\s)|(...:weight_source=)|(...:[/\\][\w.\- ]+[/\\])|(...:OneDrive\\)|(...:\\\\)",
    re.IGNORECASE,
)

TEXT_SUFFIXES: frozenset[str] = frozenset({".txt", ".md", ".html"})

STRESS_REPORT_NAME = "stress_report.json"
JSON_SCAN_NAMES: frozenset[str] = frozenset({STRESS_REPORT_NAME})
PORTFOLIO_FIRST_SUMMARY_REQUIRED_MARKERS: tuple[str, ...] = (
    "Starting portfolio",
    "Candidate alternatives",
)
PORTFOLIO_FIRST_SUMMARY_FORBIDDEN_MARKERS: tuple[str, ...] = (
    "Current vs policy workflow",
    "Top candidates by health rank",
    "Versus current:",
)

PORTFOLIO_XRAY_REPORT_REQUIRED_MARKERS: tuple[str, ...] = (
    "PORTFOLIO X-RAY SUMMARY",
    "diagnostic-only",
    "Portfolio Metrics / Risk Diagnostics",
    "Hidden Exposure / Hidden Risk Detector",
    "Portfolio Weakness Map",
    "portfolio_xray.json",
)

PORTFOLIO_XRAY_HTML_REQUIRED_MARKERS: tuple[str, ...] = (
    'class="xray-summary-section"',
    'class="xray-section"',
    "Portfolio X-Ray Summary",
    "Portfolio Weakness Map",
)

PORTFOLIO_XRAY_COMMENTARY_REQUIRED_MARKERS: tuple[str, ...] = (
    "Portfolio X-Ray (diagnostic-only)",
    "portfolio_xray.json",
    "report.html",
)

PORTFOLIO_XRAY_FORBIDDEN_MARKERS: tuple[str, ...] = (
    "status=partial; sources=",
    "more items in portfolio_xray.json",
    "<pre>",
)

REPRESENTATIVE_REL_DIRS: tuple[str, ...] = (
    "Main portfolio",
    "equal-weight portfolio",
    "risk parity portfolio",
    "pdf_md_sources",
    "pdf files",
)


@dataclass
class ScanFinding:
    path: str
    kind: str
    detail: str
    line_no: int | None = None


@dataclass
class ScanResult:
    scanned_files: int = 0
    findings: list[ScanFinding] = field(default_factory=list)

    def ok(self) -> bool:
        return not self.findings

    def messages(self) -> list[str]:
        out: list[str] = []
        for f in self.findings:
            loc = f"{f.path}:{f.line_no}" if f.line_no else f.path
            out.append(f"{loc}: [{f.kind}] {f.detail}")
        return out


def _line_has_cyrillic_prose(line: str) -> bool:
    if not _CYRILLIC_RE.search(line):
        return False
    if _PATH_LIKE_RE.search(line):
        return False
    # Allow ticker-like tokens only when the line is otherwise Latin.
    stripped = _CYRILLIC_RE.sub("", line).strip()
    if not stripped:
        return True
    return bool(_CYRILLIC_RE.search(line))


def _scan_text_lines(rel_path: str, text: str) -> list[ScanFinding]:
    findings: list[ScanFinding] = []
    for idx, line in enumerate(text.splitlines(), start=1):
        for marker in MOJIBAKE_SUBSTRINGS:
            if marker in line:
                findings.append(
                    ScanFinding(rel_path, "mojibake", f"contains marker {marker!r}", idx)
                )
                break
        if _line_has_cyrillic_prose(line):
            findings.append(
                ScanFinding(rel_path, "cyrillic_prose", "Cyrillic outside path-like context", idx)
            )
    return findings


def _scan_stress_report(rel_path: str, data: object) -> list[ScanFinding]:
    findings: list[ScanFinding] = []
    if not isinstance(data, dict):
        return findings

    def walk(obj: object, prefix: str) -> None:
        if isinstance(obj, dict):
            if "assessment_en_legacy" in obj and "assessment_en" not in obj:
                findings.append(
                    ScanFinding(
                        rel_path,
                        "schema_drift",
                        f"{prefix}: assessment_ru without assessment_en",
                    )
                )
            for key, val in obj.items():
                walk(val, f"{prefix}.{key}" if prefix else key)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                walk(item, f"{prefix}[{i}]")

    walk(data, "")
    return findings


def iter_representative_files(repo_root: Path) -> Iterable[Path]:
    for rel in REPRESENTATIVE_REL_DIRS:
        root = repo_root / rel
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            suffix = path.suffix.lower()
            if suffix in TEXT_SUFFIXES or path.name in JSON_SCAN_NAMES:
                yield path


def scan_representative_outputs(repo_root: Path | None = None) -> ScanResult:
    root = repo_root or Path(__file__).resolve().parents[1]
    result = ScanResult()
    for path in iter_representative_files(root):
        rel = path.relative_to(root).as_posix()
        result.scanned_files += 1
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            result.findings.append(
                ScanFinding(rel, "encoding", "file is not valid UTF-8")
            )
            continue
        result.findings.extend(_scan_text_lines(rel, text))
        if path.name == STRESS_REPORT_NAME:
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                result.findings.append(
                    ScanFinding(rel, "json", "invalid JSON")
                )
            else:
                result.findings.extend(_scan_stress_report(rel, payload))
    return result


def scan_portfolio_xray_report_text(
    text: str,
    *,
    rel_path: str = "report.txt",
    required_markers: tuple[str, ...] = PORTFOLIO_XRAY_REPORT_REQUIRED_MARKERS,
) -> ScanResult:
    """Check report/commentary surfaces for structured X-Ray wording (Session 08)."""
    result = ScanResult(scanned_files=1)
    result.findings.extend(_scan_text_lines(rel_path, text))
    for marker in required_markers:
        if marker not in text:
            result.findings.append(
                ScanFinding(rel_path, "xray_marker_missing", f"missing {marker!r}")
            )
    for marker in PORTFOLIO_XRAY_FORBIDDEN_MARKERS:
        if marker in text:
            result.findings.append(
                ScanFinding(rel_path, "xray_raw_dump", f"contains forbidden {marker!r}")
            )
    return result


def scan_portfolio_xray_html_text(
    text: str,
    *,
    rel_path: str = "report.html",
) -> ScanResult:
    result = ScanResult(scanned_files=1)
    result.findings.extend(_scan_text_lines(rel_path, text))
    for marker in PORTFOLIO_XRAY_HTML_REQUIRED_MARKERS:
        if marker not in text:
            result.findings.append(
                ScanFinding(rel_path, "xray_html_marker_missing", f"missing {marker!r}")
            )
    if "<pre>" in text.lower() and "xray-summary" in text.lower():
        result.findings.append(
            ScanFinding(rel_path, "xray_raw_dump", "X-Ray HTML uses preformatted dump")
        )
    return result


def scan_portfolio_first_summary_text(
    text: str,
    *,
    rel_path: str = "decision_package_summary.txt",
) -> ScanResult:
    """Check the portfolio-first report story for an analysis_subject decision summary."""
    result = ScanResult(scanned_files=1)
    result.findings.extend(_scan_text_lines(rel_path, text))
    for marker in PORTFOLIO_FIRST_SUMMARY_REQUIRED_MARKERS:
        if marker not in text:
            result.findings.append(
                ScanFinding(rel_path, "story_marker_missing", f"missing {marker!r}")
            )
    for marker in PORTFOLIO_FIRST_SUMMARY_FORBIDDEN_MARKERS:
        if marker in text:
            result.findings.append(
                ScanFinding(rel_path, "stale_story_marker", f"contains {marker!r}")
            )
    return result
