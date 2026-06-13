"""Plain-text output sanitizers for client-facing generated reports."""
from __future__ import annotations

from typing import Any


ASCII_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("\u0394w", "delta w"),
    ("\u2014", "-"),
    ("\u2013", "-"),
    ("\u2212", "-"),
    ("\u0394", "delta"),
    ("\u00d7", "x"),
    ("\u2265", ">="),
    ("\u2264", "<="),
    ("\u201c", '"'),
    ("\u201d", '"'),
    ("\u2018", "'"),
    ("\u2019", "'"),
    ("\u2026", "..."),
    ("\u00a0", " "),
)


MOJIBAKE_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("\u041e\u201dw", "delta w"),
    ('\u041e\"w', "delta w"),
    ("—", "-"),
    ("–", "-"),
    ("≥", ">="),
    ("≤", "<="),
    ("\u041e\u201d", "delta"),
    ("\u041e\u0406", "beta"),
    ("\u0413\u2014", "x"),
    ("\u00e2\u20ac\u201d", "-"),
    ('\u00e2\u20ac"', "-"),
    ("\u00e2\u20ac\u201c", "-"),
    ("\u00ce\u201d", "delta"),
    ("\u00ce\u00b2", "beta"),
    ("\u00d0", ""),
    ("\ufffd", ""),
)


def ascii_safe_text(text: Any) -> str:
    """Return text safe for plain .txt outputs across Windows consoles/viewers."""

    out = "" if text is None else str(text)
    for src, dst in ASCII_REPLACEMENTS:
        out = out.replace(src, dst)
    for src, dst in MOJIBAKE_REPLACEMENTS:
        out = out.replace(src, dst)
    return out
