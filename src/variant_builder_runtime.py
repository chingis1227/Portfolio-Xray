"""
Variant builder runtime helpers: PDF skip policy and per-step timing buckets.

Used by per-candidate ``run_*.py`` scripts and read by ``src/candidate_factory.py``.
Orchestration only — no formula or report semantics changes.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ENV_SKIP_VARIANT_PDF = "PORTFOLIO_SKIP_VARIANT_PDF"
BUILDER_RUNTIME_TIMING_FILENAME = "builder_runtime_timing.json"

PDF_MODE_VALUES = frozenset({"none", "final_only", "per_candidate"})


def normalize_pdf_mode(pdf_mode: str) -> str:
    mode = (pdf_mode or "none").strip().lower()
    if mode not in PDF_MODE_VALUES:
        raise ValueError(
            f"Invalid pdf_mode {pdf_mode!r}; expected one of: {', '.join(sorted(PDF_MODE_VALUES))}"
        )
    return mode


def variant_pdf_skip_requested() -> bool:
    """True when factory (or operator) requested skipping per-variant Pandoc rebuild."""
    return os.environ.get(ENV_SKIP_VARIANT_PDF, "").strip() in ("1", "true", "yes", "on")


def subprocess_env_for_pdf_mode(
    pdf_mode: str,
    *,
    base_env: dict[str, str] | None = None,
) -> dict[str, str]:
    """Build environment for factory subprocess builders."""
    env = dict(base_env if base_env is not None else os.environ)
    mode = normalize_pdf_mode(pdf_mode)
    if mode == "per_candidate":
        env.pop(ENV_SKIP_VARIANT_PDF, None)
    else:
        env[ENV_SKIP_VARIANT_PDF] = "1"
    return env


@dataclass
class BuilderStepTiming:
    """Wall-clock buckets for one candidate builder invocation."""

    builder_core_seconds: float = 0.0
    report_seconds: float = 0.0
    pdf_seconds: float = 0.0
    _core_start: float | None = field(default=None, repr=False)
    _report_start: float | None = field(default=None, repr=False)

    def start_core(self) -> None:
        self._core_start = time.perf_counter()

    def end_core(self) -> None:
        if self._core_start is not None:
            self.builder_core_seconds += time.perf_counter() - self._core_start
            self._core_start = None

    def start_report(self) -> None:
        self._report_start = time.perf_counter()

    def end_report(self) -> None:
        if self._report_start is not None:
            self.report_seconds += time.perf_counter() - self._report_start
            self._report_start = None

    @property
    def total_seconds(self) -> float:
        return round(
            self.builder_core_seconds + self.report_seconds + self.pdf_seconds,
            3,
        )

    def to_dict(self) -> dict[str, float]:
        return {
            "builder_core_seconds": round(self.builder_core_seconds, 3),
            "report_seconds": round(self.report_seconds, 3),
            "pdf_seconds": round(self.pdf_seconds, 3),
            "total_seconds": self.total_seconds,
        }


def persist_builder_runtime_timing(out_dir: Path, timing: BuilderStepTiming) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / BUILDER_RUNTIME_TIMING_FILENAME
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(timing.to_dict(), handle, indent=2)
        handle.write("\n")
    return path


def load_builder_runtime_timing(artifact_dir: Path) -> dict[str, float] | None:
    path = artifact_dir / BUILDER_RUNTIME_TIMING_FILENAME
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict):
        return None
    out: dict[str, float] = {}
    for key in (
        "builder_core_seconds",
        "report_seconds",
        "pdf_seconds",
        "total_seconds",
    ):
        val = raw.get(key)
        if isinstance(val, (int, float)):
            out[key] = round(float(val), 3)
    return out or None


def merge_timing_into_step(step: dict[str, Any], timing: dict[str, float] | None) -> None:
    """Attach timing buckets to a factory step dict (in place)."""
    if timing:
        step["builder_core_seconds"] = timing.get("builder_core_seconds")
        step["report_seconds"] = timing.get("report_seconds")
        step["pdf_seconds"] = timing.get("pdf_seconds")
        step["total_seconds"] = timing.get("total_seconds")
        return
    duration = step.get("duration_seconds")
    if isinstance(duration, (int, float)):
        step["total_seconds"] = round(float(duration), 3)
    step["builder_core_seconds"] = None
    step["report_seconds"] = None
    step["pdf_seconds"] = None


def build_timing_summary(steps: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate timing across factory steps for operator dashboards."""
    bucket_keys = (
        "builder_core_seconds",
        "report_seconds",
        "pdf_seconds",
        "total_seconds",
    )
    totals = {k: 0.0 for k in bucket_keys}
    measured_steps = 0
    for step in steps:
        if not isinstance(step, dict):
            continue
        if step.get("execution_action") not in (
            "builder_invoked",
            "builder_invoked_failed",
            "lightweight_report_built",
            "lightweight_report_reused_weights",
            "lightweight_report_failed",
            "weights_built",
        ):
            continue
        has_bucket = False
        for key in bucket_keys:
            val = step.get(key)
            if isinstance(val, (int, float)):
                totals[key] += float(val)
                has_bucket = True
        if has_bucket:
            measured_steps += 1
        elif isinstance(step.get("duration_seconds"), (int, float)):
            totals["total_seconds"] += float(step["duration_seconds"])
            measured_steps += 1
    return {
        "steps_with_timing": measured_steps,
        "builder_core_seconds": round(totals["builder_core_seconds"], 3),
        "report_seconds": round(totals["report_seconds"], 3),
        "pdf_seconds": round(totals["pdf_seconds"], 3),
        "total_seconds": round(totals["total_seconds"], 3),
    }


def maybe_rebuild_pdfs_after_variant(
    *,
    logger: Any = None,
    timing: BuilderStepTiming | None = None,
) -> None:
    """Rebuild EW/RP compare + variant PDFs unless factory skip env is set."""
    if variant_pdf_skip_requested():
        if timing is not None:
            timing.pdf_seconds = 0.0
        if logger is not None:
            logger.info(
                "Skipping variant PDF rebuild (%s set by factory or operator).",
                ENV_SKIP_VARIANT_PDF,
            )
        return
    t0 = time.perf_counter()
    try:
        from src.pdf_reports import try_rebuild_pdfs_after_variant as _rebuild

        _rebuild(logger=logger)
    except Exception as exc:  # noqa: BLE001 — match legacy builder scripts
        if logger is not None:
            logger.warning("PDF suite rebuild skipped: %s", exc)
    finally:
        if timing is not None:
            timing.pdf_seconds = round(time.perf_counter() - t0, 3)


def maybe_rebuild_pdfs_only(
    *,
    logger: Any = None,
    timing: BuilderStepTiming | None = None,
) -> None:
    """Rebuild variant PDFs without EW/RP compare (robust scenario report path)."""
    if variant_pdf_skip_requested():
        if timing is not None:
            timing.pdf_seconds = 0.0
        if logger is not None:
            logger.info(
                "Skipping variant PDF-only rebuild (%s set).",
                ENV_SKIP_VARIANT_PDF,
            )
        return
    t0 = time.perf_counter()
    try:
        from src.pdf_reports import try_rebuild_pdfs_only as _rebuild

        _rebuild(logger=logger)
    except Exception as exc:  # noqa: BLE001
        if logger is not None:
            logger.warning("PDF-only rebuild skipped: %s", exc)
    finally:
        if timing is not None:
            timing.pdf_seconds = round(time.perf_counter() - t0, 3)
