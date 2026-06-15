from __future__ import annotations

import contextlib
import io
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from src.cache import cleanup_old_cache
from src.config import load_validated_config


def run_staged_diagnosis_service(
    config_path: Path,
    *,
    mode: str,
    project_root: Path,
) -> subprocess.CompletedProcess[str]:
    """Materialize staged diagnosis artifacts without launching a Python subprocess.

    The service intentionally reuses ``run_report.run_materialize_analysis_subject_report``.
    It does not copy formulas or artifact builders; it only replaces the normal FastAPI
    adapter boundary that used to shell out to ``run_report.py`` or ``run_portfolio_review.py``.
    """

    from run_report import run_materialize_analysis_subject_report

    core_diagnostics_only = mode == "core_only"
    stdout = io.StringIO()
    stderr = io.StringIO()
    args = ["direct_staged_diagnosis_service", mode, "--config", str(config_path)]
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            cfg = load_validated_config(config_path)
            run_materialize_analysis_subject_report(
                cfg,
                run_timestamp=datetime.now(timezone.utc).isoformat(),
                backtest_mode="dynamic_nan_safe",
                no_cache=False,
                output_profile="site_api",
                review_mode="core",
                project_root=project_root,
                use_review_run_context=False,
                core_diagnostics_only=core_diagnostics_only,
            )
            cleanup_old_cache(keep_versions=3)
    except SystemExit as exc:
        code = int(exc.code) if isinstance(exc.code, int) else 1
        return subprocess.CompletedProcess(
            args=args,
            returncode=code,
            stdout=stdout.getvalue(),
            stderr=stderr.getvalue(),
        )
    except Exception as exc:
        stderr.write(f"{type(exc).__name__}: {exc}")
        return subprocess.CompletedProcess(
            args=args,
            returncode=1,
            stdout=stdout.getvalue(),
            stderr=stderr.getvalue(),
        )

    return subprocess.CompletedProcess(
        args=args,
        returncode=0,
        stdout=stdout.getvalue(),
        stderr=stderr.getvalue(),
    )
