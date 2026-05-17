"""Fix common UTF-8 mojibake in source docs, Cursor rules/agents, and engineering Python files."""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

EM_DASH = "\u0432\u0402\u201d"
EN_DASH = "\u0432\u0402\u201c"
ARROW = "\u0432\u2020\u2019"
GE = "\u0432\u2030\u0490"
LE = "\u0432\u2030\u00a4"
NE = "\u0432\u2030\u00a0"
MINUS = "\u0432\u20ac\u2019"
TIMES = "\u0413\u2014"
SIGMA_SQ = "\u041f\u0453\u0412\u0406"
SIGMA = "\u041e\u0408"
W_T = "w_t\u0431\u00b5\u0402"
BETA = "\u041e\u0406"
DELTA = "\u041e\u201d"
RHO = "\u041f\u0403"
SECTION = "\u0412\u00a7"
R_SQ = "R\u0412\u0406"
CHI_SQ = "\u041f\u2021" + R_SQ
H0 = "H\u0432\u201a\u0406"
OPEN_QUOTE = "\u0432\u0402\u045a"
CLOSE_QUOTE = "\u0432\u0402\u045c"
ELLIPSIS = "\u0432\u0402\u00a6"
BULLET = "\u0432\u0402\u045e"
NDASH = "\u0432\u0402\u2013"  # variant en-dash in Durbin–Watson mojibake

REPLACEMENTS: list[tuple[str, str]] = [
    (f"Portfolio_PnL_% {GE} {MINUS}MaxDD_limit", "Portfolio_PnL_% >= -MaxDD_limit"),
    (f"(mean(r_simple {MINUS} rf_monthly) {TIMES} 12)", "(mean(r_simple - rf_monthly) * 12)"),
    (f"**{SIGMA_SQ}_t = {W_T} {SIGMA}_window w_t**", "**sigma_sq_t = w_t^T Sigma_window w_t**"),
    (f"**{SIGMA_SQ}_t**", "**sigma_sq_t**"),
    (SIGMA_SQ, "sigma_sq"),
    (W_T, "w_t^T"),
    (f"{SIGMA}_window", "Sigma_window"),
    (f"{SIGMA}_10Y", "Sigma_10Y"),
    (f"{SIGMA}_5Y", "Sigma_5Y"),
    (SIGMA, "Sigma"),
    (f"inner_join_months_used_for_risk ({SIGMA}/RC)", "inner_join_months_used_for_risk (Sigma/RC)"),
    (f"View After Optimization {EM_DASH}", "View After Optimization -"),
    (f"two types of beta {EM_DASH}", "two types of beta -"),
    (f"Not a portfolio metric** {EM_DASH}", "Not a portfolio metric** -"),
    (f"RC_vol {EM_DASH}", "RC_vol -"),
    (f"context only {EM_DASH}", "context only -"),
    (f"numeric diagnostics only** {EM_DASH}", "numeric diagnostics only** -"),
    (f"# Project Rules {EM_DASH}", "# Project Rules -"),
    (f"# Stress factor betas {EM_DASH}", "# Stress factor betas -"),
    (f"Portfolio Metrics Standard {EM_DASH}", "Portfolio Metrics Standard -"),
    (f"Durbin{EN_DASH}Watson", "Durbin-Watson"),
    (f"Durbin{NDASH}Watson", "Durbin-Watson"),
    (f"Breusch{EN_DASH}Godfrey", "Breusch-Godfrey"),
    (f"Breusch{NDASH}Godfrey", "Breusch-Godfrey"),
    (f"Newey{EN_DASH}West", "Newey-West"),
    (f"Newey{NDASH}West", "Newey-West"),
    (f"7{EN_DASH}10Y", "7-10Y"),
    (f"7{NDASH}10Y", "7-10Y"),
    ("`beta_eq`, `beta_rr`, " + ELLIPSIS, "`beta_eq`, `beta_rr`, ..."),
    ("scenario\u0432\u0402\u2122s", "scenario's"),
    (f"shock{TIMES}beta", "shock * beta"),
    (f"5% {ARROW} 2% {ARROW} 1%", "5% -> 2% -> 1%"),
    (f"2{EN_DASH}3", "2-3"),
    (f"2{NDASH}3", "2-3"),
    (f"2{EN_DASH}5", "2-5"),
    (f"2{NDASH}5", "2-5"),
    (f"2{EN_DASH}4", "2-4"),
    (f"2{NDASH}4", "2-4"),
    (f"3{EN_DASH}7", "3-7"),
    (f"3{NDASH}7", "3-7"),
    (f"20{EN_DASH}30%", "20-30%"),
    (f"20{NDASH}30%", "20-30%"),
    (f"+/-20{EN_DASH}30%", "+/-20-30%"),
    (f"+/-20{NDASH}30%", "+/-20-30%"),
    (f"2000-03-01 {ARROW} 2002-10-31", "2000-03-01 -> 2002-10-31"),
    (f"equity {MINUS}40%", "equity -40%"),
    (f"investor currency {NE} USD", "investor currency != USD"),
    (f"investor {NE} USD", "investor != USD"),
    (f"{NE} USD", "!= USD"),
    (OPEN_QUOTE, '"'),
    (CLOSE_QUOTE, '"'),
    (CHI_SQ, "chi^2"),
    (R_SQ, "R^2"),
    (H0, "H0"),
    (f"max |\\|{RHO}\\|", "max |rho|"),
    (f"max |{RHO}|", "max |rho|"),
    (f"{BETA} {TIMES} realized", "beta * realized"),
    (f"{BETA}_", "beta_"),
    (BETA, "beta"),
    (DELTA, "delta"),
    (f"(see {SECTION}10)", "(see Section 10)"),
    (f"(see {SECTION}9)", "(see Section 9)"),
    (f"(see {SECTION}8", "(see Section 8"),
    (SECTION, "Section"),
    ("\u0412\u00b1", "+/-"),
    ("\u0432\u2030\u20ac", "~="),
    (GE, ">="),
    (LE, "<="),
    (ARROW, "->"),
    (MINUS, "-"),
    (EM_DASH, " - "),
    (EN_DASH, "-"),
    (NDASH, "-"),
    (BULLET, "-"),
    (ELLIPSIS, "..."),
    (TIMES, "*"),
    (f" {TIMES} ", " * "),
]

# Exact placeholder token (not the broken quote above)
MOJIBAKE_EM = "\u0432\u0402\u201d"

SKIP_DIR_NAMES = {
    "pdf files",
    "pdf_md_sources",
    "cache",
    "output",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    ".git",
    "00_ВАЖНОЕ",
}

SKIP_PATH_PARTS = {
    "Main portfolio",
    "equal-weight portfolio",
    "risk parity portfolio",
    "minimum_cvar",
    "robust_mean_variance",
    "robust scenario portfolio",
}


def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    if parts & SKIP_DIR_NAMES:
        return True
    if any(p in parts for p in SKIP_PATH_PARTS):
        return True
    if path.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".pyc"}:
        return True
    return False


def iter_source_files() -> list[Path]:
    roots = [
        REPO / ".cursor",
        REPO / "docs",
        REPO / "src",
        REPO / "config_ui",
        REPO / "results_dashboard",
        REPO / "scripts",
        REPO / "tests",
    ]
    root_files = [
        REPO / "run_report.py",
        REPO / "run_optimization.py",
        REPO / "run_rebalance.py",
        REPO / "rebuild_pdf_reports.py",
        REPO / "AGENTS.md",
        REPO / "README.md",
        REPO / "SPEC.md",
        REPO / "RULES.md",
        REPO / "WORKFLOW.md",
        REPO / "OUTPUTS.md",
        REPO / "TESTING.md",
        REPO / "PRODUCT.md",
        REPO / "ARCHITECTURE.md",
        REPO / "DATA.md",
        REPO / "DESIGN.md",
        REPO / "KNOWN_ISSUES.md",
        REPO / "CHANGELOG.md",
        REPO / "DECISIONS.md",
        REPO / "GLOSSARY.md",
    ]
    out: list[Path] = []
    for r in roots:
        if not r.exists():
            continue
        if r.is_file():
            if not should_skip(r):
                out.append(r)
            continue
        for p in r.rglob("*"):
            if p.is_file() and not should_skip(p):
                if p.suffix.lower() in {".md", ".mdc", ".py", ".yml", ".yaml", ".txt"}:
                    if p.name.startswith("commentary") and "portfolio" in str(p):
                        continue
                    out.append(p)
    for p in root_files:
        if p.exists() and not should_skip(p):
            out.append(p)
    return sorted(set(out))


def apply_replacements(text: str) -> str:
    for old, new in REPLACEMENTS:
        if old == '"':
            continue
        text = text.replace(old, new)
    text = text.replace(MOJIBAKE_EM, "-")
    return text


def try_decode_mojibake_russian(text: str) -> str:
    """Fix UTF-8 misread as latin-1 in string literals (logger messages, docstrings)."""
    if "\u0420" not in text and "\u0432\u0402" not in text:
        return text

    def _decode_match(m: re.Match[str]) -> str:
        chunk = m.group(0)
        if not any(ord(c) > 127 for c in chunk):
            return chunk
        for enc in ("latin-1", "cp1252"):
            try:
                fixed = chunk.encode(enc).decode("utf-8")
                if fixed != chunk:
                    return fixed
            except (UnicodeDecodeError, UnicodeEncodeError):
                continue
        return chunk

    # Only rewrite likely-mojibake runs (Cyrillic-looking noise in Latin context)
    return re.sub(
        r"[\u0400-\u04ff\u0432\u0402\u201c\u201d\u2020\u2019\u2030\u20ac]+(?:\s*[\u0400-\u04ff\u0432\u0402\u201c\u201d\u2020\u2019\u2030\u20ac]+)*",
        _decode_match,
        text,
    )


def fix_file(path: Path) -> bool:
    try:
        original = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return False
    fixed = apply_replacements(original)
    if path.suffix == ".py":
        fixed = try_decode_mojibake_russian(fixed)
        fixed = apply_replacements(fixed)  # second pass after decode
    if fixed == original:
        return False
    path.write_text(fixed, encoding="utf-8", newline="\n")
    return True


def main() -> None:
    updated = 0
    for path in iter_source_files():
        if fix_file(path):
            print(f"updated {path.relative_to(REPO)}")
            updated += 1
    print(f"done: {updated} file(s) updated")


if __name__ == "__main__":
    main()
