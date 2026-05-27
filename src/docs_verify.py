"""Lightweight Markdown link and stale-reference checks for source documentation."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

LOCAL_REF_RE = re.compile(
    r"`([^`\n]+\.(?:md|mdc|py|yml|yaml|json|csv|txt))`"
    r"|\]\((?!https?://|mailto:)([^)#]+)"
)

# Paths that were removed or moved; presence in source docs is a stale reference.
FORBIDDEN_REFERENCES: tuple[str, ...] = (
    "docs/metrics_specification.md",
    "docs/docs/stress_testing_spec.md",
    "docs/portfolio_construction_policy.md",
    "docs/data_policy_nan_young_etfs.md",
)

# Optional or not-yet-created paths that may appear in roadmap/exec-plan prose.
ALLOW_MISSING_PATHS: frozenset[str] = frozenset(
    {
        "docs/product_backlog.md",
        "src/portfolio_health_score.py",
        "src/selection_engine.py",
        "docs/specs/action_engine_spec.md",
        "docs/specs/monitoring_spec.md",
        "docs/specs/decision_journal_spec.md",
        # Input Layer MVP migration (ExecPlan 2026-05-26; created in Sessions 02–08)
        "src/mvp_input.py",
        "tests/test_mvp_input_defaults.py",
        "tests/test_mvp_portfolio_fixtures.py",
        "tests/test_input_layer_mvp_regression.py",
        "tests/fixtures/mvp_portfolios/minimal_usd_no_cash.yml",
        "tests/fixtures/mvp_portfolios/minimal_usd_with_cash.yml",
        # Block 2.5 Risk Budget View MVP (ExecPlan 2026-05-26; Sessions 07–08)
        "tests/test_block_2_5_pipeline_integration.py",
        "docs/audits/2026-05-26_block_2_5_risk_budget_acceptance_audit.md",
        # Block 3.3 Hedge Gap Analysis MVP (ExecPlan 2026-05-27; Sessions 02–08)
        "src/hedge_gap_analysis_block.py",
        "tests/test_hedge_gap_analysis_v1_contract.py",
        "docs/audits/2026-05-27_block_3_3_hedge_gap_acceptance_audit.md",
    }
)

# Directory names skipped when collecting source Markdown (generated or non-source trees).
EXCLUDE_DIR_NAMES: frozenset[str] = frozenset(
    {
        "__pycache__",
        ".pytest_cache",
        ".git",
        "cache",
        "output",
        "pdf files",
        "pdf_md_sources",
        "node_modules",
        "Main portfolio",
        "equal-weight portfolio",
        "risk parity portfolio",
        "robust scenario portfolio",
        "minimum_cvar_constrained portfolio",
        "minimum_cvar_uncapped portfolio",
        "robust_mean_variance_constrained portfolio",
        "robust_mean_variance_uncapped portfolio",
        "00_IMPORTANT",
    }
)

CURSOR_DOC_DIRS: tuple[Path, ...] = (
    REPO_ROOT / ".cursor" / "agents",
    REPO_ROOT / ".cursor" / "rules",
)

SOURCE_DOC_DIRS: tuple[Path, ...] = (
    REPO_ROOT / "docs",
    REPO_ROOT / ".cursor" / "agents",
    REPO_ROOT / ".cursor" / "rules",
)

ROOT_DOC_FILES: tuple[Path, ...] = tuple(
    path
    for name in (
        "AGENTS.md",
        "ARCHITECTURE.md",
        "BUSINESS_VISION.md",
        "CHANGELOG.md",
        "DATA.md",
        "DECISIONS.md",
        "DESIGN.md",
        "GLOSSARY.md",
        "KNOWN_ISSUES.md",
        "OUTPUTS.md",
        "PLANS.md",
        "PRODUCT.md",
        "README.md",
        "RULES.md",
        "SPEC.md",
        "TESTING.md",
        "WORKFLOW.md",
    )
    for path in (REPO_ROOT / name,)
    if path.exists()
)


OPERATIONAL_RUNBOOK_PATH = REPO_ROOT / "docs" / "operational_runbook.md"

# Positive anchors: default portfolio review must stay diagnosis-only in the runbook.
OPERATIONAL_RUNBOOK_REQUIRED_SNIPPETS: tuple[str, ...] = (
    "**Diagnosis-only** (default)",
    "runtime_mode=product_diagnosis_only",
    "input -> diagnosis",
    "| none | no factory stage |",
)

# Stale batch-default wording that must not reappear in the operator runbook.
OPERATIONAL_RUNBOOK_FORBIDDEN_PATTERNS: tuple[tuple[str, str], ...] = (
    (
        r"\*\*Core\s*\(default\)\*\*.*run_portfolio_review\.py.*core_fast",
        "runbook must not label plain run_portfolio_review.py as Core (default) with core_fast",
    ),
    (
        r"run_portfolio_review\.py`\s*\|\s*`core_fast`\s*\|.*\(default\)",
        "runbook must not map default command to core_fast factory profile",
    ),
    (
        r"run_portfolio_review\.py(?:[^\n]*)\(default\)(?:[^\n]*)(?:six|6)\s+candidates",
        "runbook must not describe default review as a six-candidate batch",
    ),
)


@dataclass
class DocsVerifyResult:
    broken_links: list[str] = field(default_factory=list)
    forbidden_refs: list[str] = field(default_factory=list)
    removed_fields: list[str] = field(default_factory=list)
    architecture_doc_violations: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not (
            self.broken_links
            or self.forbidden_refs
            or self.removed_fields
            or self.architecture_doc_violations
        )

    def messages(self) -> list[str]:
        return [
            *self.broken_links,
            *self.forbidden_refs,
            *self.removed_fields,
            *self.architecture_doc_violations,
        ]


def _normalize_ref(raw_ref: str) -> str | None:
    ref = raw_ref.strip().strip("<>").replace("\\", "/")
    if not ref or ref.startswith("#"):
        return None
    if any(ch.isspace() for ch in ref):
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


def collect_source_markdown_files() -> list[Path]:
    files: list[Path] = list(ROOT_DOC_FILES)
    for directory in SOURCE_DOC_DIRS:
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".md", ".mdc"}:
                continue
            if any(part in EXCLUDE_DIR_NAMES for part in path.parts):
                continue
            files.append(path)
    # De-duplicate while preserving order.
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in files:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(path)
    return unique


def collect_cursor_markdown_files() -> list[Path]:
    files: list[Path] = []
    for directory in CURSOR_DOC_DIRS:
        if not directory.is_dir():
            continue
        files.extend(sorted(directory.glob("*.md")))
        files.extend(sorted(directory.glob("*.mdc")))
    extra = REPO_ROOT / "AGENTS.md"
    if extra.exists():
        files.append(extra)
    return files


REPO_RELATIVE_PREFIXES: tuple[str, ...] = (
    "docs/",
    "src/",
    "tests/",
    "config/",
    "config_ui/",
    "scripts/",
    "policy_math/",
    ".cursor/",
)


def _resolve_local_ref(source_file: Path, ref: str) -> Path:
    ref_path = Path(ref)
    if ref_path.is_absolute():
        return ref_path.resolve()
    norm = ref.replace("\\", "/")
    if norm.startswith(REPO_RELATIVE_PREFIXES):
        return (REPO_ROOT / ref_path).resolve()
    return (source_file.parent / ref_path).resolve()


def find_broken_local_links(
    paths: list[Path],
    *,
    allow_missing: frozenset[str] = ALLOW_MISSING_PATHS,
) -> list[str]:
    failures: list[str] = []
    repo_root = REPO_ROOT.resolve()
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for match in LOCAL_REF_RE.finditer(text):
            raw_ref = match.group(1) or match.group(2)
            ref = _normalize_ref(raw_ref)
            if ref is None:
                continue
            norm_ref = ref.replace("\\", "/")
            if norm_ref in allow_missing:
                continue
            target = _resolve_local_ref(path, ref)
            try:
                target.relative_to(repo_root)
            except ValueError:
                continue
            if not target.exists():
                rel = path.relative_to(REPO_ROOT)
                failures.append(f"{rel} references missing file {ref}")
    return failures


def find_forbidden_references(
    paths: list[Path],
    forbidden: tuple[str, ...] = FORBIDDEN_REFERENCES,
) -> list[str]:
    failures: list[str] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(REPO_ROOT)
        for stale_ref in forbidden:
            if stale_ref in text:
                failures.append(f"{rel} contains stale reference {stale_ref}")
    return failures


def find_operational_runbook_architecture_violations(
    runbook_path: Path = OPERATIONAL_RUNBOOK_PATH,
) -> list[str]:
    """Guard against reintroducing batch-default portfolio review wording in the runbook."""
    if not runbook_path.is_file():
        return [f"missing operational runbook at {runbook_path.relative_to(REPO_ROOT)}"]
    text = runbook_path.read_text(encoding="utf-8")
    rel = runbook_path.relative_to(REPO_ROOT)
    failures: list[str] = []
    for snippet in OPERATIONAL_RUNBOOK_REQUIRED_SNIPPETS:
        if snippet not in text:
            failures.append(f"{rel} missing required architecture snippet: {snippet!r}")
    for pattern, message in OPERATIONAL_RUNBOOK_FORBIDDEN_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            failures.append(f"{rel}: {message}")
    return failures


def find_removed_config_ui_fields() -> list[str]:
    form = REPO_ROOT / "config_ui" / "templates" / "config_form.html"
    if not form.exists():
        return []
    text = form.read_text(encoding="utf-8")
    if 'name="rc_asset_cap_pct"' in text:
        return [f"{form.relative_to(REPO_ROOT)} still exposes editable rc_asset_cap_pct"]
    return []


def verify_docs(
    *,
    include_cursor_only: bool = False,
) -> DocsVerifyResult:
    if include_cursor_only:
        paths = collect_cursor_markdown_files()
    else:
        paths = collect_source_markdown_files()
    return DocsVerifyResult(
        broken_links=find_broken_local_links(paths),
        forbidden_refs=find_forbidden_references(paths),
        removed_fields=find_removed_config_ui_fields() if not include_cursor_only else [],
        architecture_doc_violations=(
            find_operational_runbook_architecture_violations()
            if not include_cursor_only
            else []
        ),
    )
