"""
Per-block wall-clock instrumentation for ``run_portfolio_report_for_weights``.

Orchestration only — no formula or report semantics changes. Enabled via
``PORTFOLIO_REPORT_TIMING=1`` or an explicit ``enable_report_timing`` argument
(candidate factory passes ``True`` for Phase 2 measurement).
"""

from __future__ import annotations

import os
import time
from contextlib import contextmanager
from contextlib import nullcontext
from typing import Any, Iterator

ENV_PORTFOLIO_REPORT_TIMING = "PORTFOLIO_REPORT_TIMING"

REPORT_TIMING_BLOCK_KEYS: tuple[str, ...] = (
    "save_inputs",
    "asset_metrics",
    "portfolio_metrics",
    "rc_corr",
    "factor_betas",
    "run_stress",
    "factor_regression",
    "factor_covariance",
    "factor_decomposition",
    "scenario_library",
    "daily_tail_risk",
    "snapshots",
    "export_stress",
    "export_stress_hedge_gap_bridge",
)


def portfolio_report_timing_enabled(*, enable_report_timing: bool | None = None) -> bool:
    """True when env or an explicit caller flag requests block timing."""
    if enable_report_timing is True:
        return True
    if enable_report_timing is False:
        return False
    return os.environ.get(ENV_PORTFOLIO_REPORT_TIMING, "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


class ReportTimingCollector:
    """Accumulates seconds per named report block (rounded to 3 decimals)."""

    def __init__(self, *, enabled: bool) -> None:
        self.enabled = enabled
        self.blocks: dict[str, float] = {k: 0.0 for k in REPORT_TIMING_BLOCK_KEYS}
        self._active: str | None = None
        self._active_start: float | None = None

    @classmethod
    def for_run(cls, *, enable_report_timing: bool | None = None) -> ReportTimingCollector:
        return cls(enabled=portfolio_report_timing_enabled(enable_report_timing=enable_report_timing))

    def _validate_block(self, name: str) -> None:
        if name not in self.blocks:
            raise KeyError(f"Unknown report timing block: {name}")

    def start_block(self, name: str) -> None:
        if not self.enabled:
            return
        self._validate_block(name)
        self._active = name
        self._active_start = time.perf_counter()

    def end_block(self, name: str) -> None:
        if not self.enabled:
            return
        if self._active != name or self._active_start is None:
            return
        self.blocks[name] = round(self.blocks[name] + time.perf_counter() - self._active_start, 3)
        self._active = None
        self._active_start = None

    @contextmanager
    def block(self, name: str) -> Iterator[None]:
        if not self.enabled:
            with nullcontext():
                yield
            return
        self._validate_block(name)
        t0 = time.perf_counter()
        try:
            yield
        finally:
            self.blocks[name] = round(self.blocks[name] + time.perf_counter() - t0, 3)

    def to_dict(self) -> dict[str, float]:
        return {k: self.blocks[k] for k in REPORT_TIMING_BLOCK_KEYS if self.blocks[k] > 0}


def aggregate_report_timing_from_steps(steps: list[dict[str, Any]]) -> dict[str, Any]:
    """Sum per-block seconds across factory steps that recorded ``report_timing``."""
    totals = {k: 0.0 for k in REPORT_TIMING_BLOCK_KEYS}
    measured = 0
    for step in steps:
        if not isinstance(step, dict):
            continue
        raw = step.get("report_timing")
        if not isinstance(raw, dict):
            continue
        measured += 1
        for key in REPORT_TIMING_BLOCK_KEYS:
            val = raw.get(key)
            if isinstance(val, (int, float)):
                totals[key] += float(val)
    return {
        "candidates_with_report_timing": measured,
        "report_blocks_seconds_total": {
            k: round(totals[k], 3) for k in REPORT_TIMING_BLOCK_KEYS if totals[k] > 0
        },
    }
