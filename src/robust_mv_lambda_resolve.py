"""
Resolve Robust MV λ for baseline CLI scripts.

Production λ comes from ``run_robust_mv_lambda_calibration.py`` output under the default folder,
unless overridden explicitly via CLI.

YAML ``robust_mv_lambda`` is **not** used on baseline scripts — omit it from config or leave unset.
Tests and custom tooling may still pass λ programmatically (``replace(cfg, robust_mv_lambda=…)``).
"""
from __future__ import annotations

import logging
from pathlib import Path

_LOG = logging.getLogger(__name__)

DEFAULT_CALIBRATION_DIRNAME = "analysis_robust_mv_lambda_calibration"
SELECTED_LAMBDA_FILENAME = "selected_lambda.txt"


def read_selected_lambda_from_calibration_dir(calibration_dir: Path) -> float | None:
    """Return λ parsed from ``selected_lambda.txt`` if present and valid."""
    path = calibration_dir / SELECTED_LAMBDA_FILENAME
    if not path.is_file():
        return None
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        _LOG.warning("Invalid Robust MV calibration λ text in %s", path)
        return None


def resolve_robust_mv_lambda_for_baseline(
    *,
    project_root: Path,
    cli_lambda: float | None,
    calibration_dirname: str = DEFAULT_CALIBRATION_DIRNAME,
) -> tuple[float | None, str]:
    """
    Resolve λ for Robust MV baseline runners:

    1. explicit CLI λ (--robust-mv-lambda)
    2. last calibration artifact (``selected_lambda.txt`` under default folder)

    Returns ``(lambda_float_or_None, resolution_reason_key)``.
    """
    if cli_lambda is not None:
        return float(cli_lambda), "cli_override"

    cal_dir = project_root / calibration_dirname
    lam_file = read_selected_lambda_from_calibration_dir(cal_dir)
    if lam_file is not None and lam_file == lam_file and lam_file >= 0:
        return lam_file, "calibration_file"

    return None, "none"
