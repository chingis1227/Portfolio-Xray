"""
Central output policy for site/API versus explicit export/report modes.

This module only controls artifact routing. It must not change portfolio math,
optimizer behavior, stress logic, candidate weights, comparison ranking, or
selection logic.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

OUTPUT_PROFILE_SITE_API = "site_api"
OUTPUT_PROFILE_CORE_JSON = "core_json"
OUTPUT_PROFILE_LIGHTWEIGHT = "lightweight_comparison"
OUTPUT_PROFILE_FULL_REPORT = "full_report"
OUTPUT_PROFILE_LEGACY_EXPORT = "legacy_export"

OUTPUT_PROFILE_VALUES = frozenset(
    {
        OUTPUT_PROFILE_SITE_API,
        OUTPUT_PROFILE_CORE_JSON,
        OUTPUT_PROFILE_LIGHTWEIGHT,
        OUTPUT_PROFILE_FULL_REPORT,
        OUTPUT_PROFILE_LEGACY_EXPORT,
    }
)

OUTPUT_PROFILE_ALIASES = {
    "api": OUTPUT_PROFILE_SITE_API,
    "json": OUTPUT_PROFILE_SITE_API,
    "json_only": OUTPUT_PROFILE_SITE_API,
    "core": OUTPUT_PROFILE_CORE_JSON,
    "full": OUTPUT_PROFILE_FULL_REPORT,
    "report": OUTPUT_PROFILE_FULL_REPORT,
    "legacy": OUTPUT_PROFILE_LEGACY_EXPORT,
    "export": OUTPUT_PROFILE_LEGACY_EXPORT,
}

DEFAULT_OUTPUT_PROFILE = OUTPUT_PROFILE_SITE_API

PRESENTATION_SUFFIXES = {
    ".csv": "csv",
    ".txt": "txt",
    ".html": "html",
    ".png": "png",
    ".pdf": "pdf",
    ".css": "css_visual_assets",
}


@dataclass(frozen=True)
class OutputPolicy:
    """Boolean output contract for one execution profile."""

    profile: str
    write_json: bool = True
    write_cache: bool = True
    write_minimal_yaml: bool = True
    write_csv: bool = False
    write_txt: bool = False
    write_html: bool = False
    write_png: bool = False
    write_pdf: bool = False
    write_markdown_sidecars: bool = False
    write_css_visual_assets: bool = False
    write_legacy_comparison: bool = False
    lightweight_calculation_path: bool = True

    @property
    def disabled_artifact_classes(self) -> list[str]:
        disabled: list[str] = []
        if not self.write_csv:
            disabled.append("csv")
        if not self.write_txt:
            disabled.append("txt")
        if not self.write_html:
            disabled.append("html")
        if not self.write_png:
            disabled.append("png")
        if not self.write_pdf:
            disabled.append("pdf")
        if not self.write_markdown_sidecars:
            disabled.append("markdown_pdf_sidecars")
        if not self.write_css_visual_assets:
            disabled.append("css_visual_assets")
        return disabled


def normalize_output_profile(profile: str | None) -> str:
    normalized = (profile or DEFAULT_OUTPUT_PROFILE).strip().lower().replace("-", "_")
    normalized = OUTPUT_PROFILE_ALIASES.get(normalized, normalized)
    if normalized not in OUTPUT_PROFILE_VALUES:
        raise ValueError(
            f"Invalid output profile {profile!r}; expected one of: "
            f"{', '.join(sorted(OUTPUT_PROFILE_VALUES))}"
        )
    return normalized


def output_policy_for_profile(profile: str | None) -> OutputPolicy:
    normalized = normalize_output_profile(profile)
    if normalized in {
        OUTPUT_PROFILE_SITE_API,
        OUTPUT_PROFILE_CORE_JSON,
        OUTPUT_PROFILE_LIGHTWEIGHT,
    }:
        return OutputPolicy(profile=normalized)
    if normalized == OUTPUT_PROFILE_FULL_REPORT:
        return OutputPolicy(
            profile=normalized,
            write_csv=True,
            write_txt=True,
            write_html=True,
            write_png=True,
            write_legacy_comparison=True,
            lightweight_calculation_path=False,
        )
    if normalized == OUTPUT_PROFILE_LEGACY_EXPORT:
        return OutputPolicy(
            profile=normalized,
            write_csv=True,
            write_txt=True,
            write_html=True,
            write_png=True,
            write_pdf=True,
            write_markdown_sidecars=True,
            write_css_visual_assets=True,
            write_legacy_comparison=True,
            lightweight_calculation_path=False,
        )
    raise AssertionError(f"Unhandled output profile: {normalized}")


def profile_from_legacy_report_profile(report_profile: str | None) -> str | None:
    """Map the older report_profile argument to the central output profile."""
    if report_profile is None:
        return None
    normalized = report_profile.strip().lower().replace("-", "_")
    if normalized in {"full", "full_report"}:
        return OUTPUT_PROFILE_FULL_REPORT
    if normalized == OUTPUT_PROFILE_LIGHTWEIGHT:
        return OUTPUT_PROFILE_LIGHTWEIGHT
    return normalized


def artifact_counts_by_type(root: Path) -> dict[str, int]:
    counts = {
        "json": 0,
        "csv": 0,
        "txt": 0,
        "html": 0,
        "png": 0,
        "pdf": 0,
        "markdown_pdf_sidecars": 0,
        "css_visual_assets": 0,
    }
    if not root.exists():
        return counts
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix == ".json":
            counts["json"] += 1
        elif suffix in PRESENTATION_SUFFIXES:
            counts[PRESENTATION_SUFFIXES[suffix]] += 1
        if suffix == ".md" and "pdf_md_sources" in path.parts:
            counts["markdown_pdf_sidecars"] += 1
    return counts


def write_output_manifest(
    output_dir: Path,
    *,
    policy: OutputPolicy,
    run_kind: str,
    generated_paths: dict[str, str | Path | None] | None = None,
    cache_keys: dict[str, str | None] | None = None,
    extra: dict[str, Any] | None = None,
) -> Path:
    """Write a compact machine-readable manifest for UI/API consumers."""
    output_dir.mkdir(parents=True, exist_ok=True)
    clean_paths = {
        str(key): str(value).replace("\\", "/")
        for key, value in (generated_paths or {}).items()
        if value is not None
    }
    doc: dict[str, Any] = {
        "schema_version": "output_manifest_v1",
        "run_kind": run_kind,
        "output_profile": policy.profile,
        "json_is_default_contract": True,
        "cache_is_internal": True,
        "disabled_artifact_classes": policy.disabled_artifact_classes,
        "generated_paths": clean_paths,
        "cache_keys": {k: v for k, v in (cache_keys or {}).items() if v},
        "artifact_counts_by_type": artifact_counts_by_type(output_dir),
    }
    if extra:
        doc.update(extra)
    path = output_dir / "output_manifest.json"
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    return path

