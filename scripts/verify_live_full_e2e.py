#!/usr/bin/env python3
"""Run or verify the Phase 17 live full + resume E2E gate (RM-1029)."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.config import load_validated_config  # noqa: E402
from src.live_full_e2e import validate_live_full_artifacts  # noqa: E402


def _run_live_full(*, resume_candidates: bool = False, skip_pdf: bool = True) -> int:
    argv = [sys.executable, "run_portfolio_review.py", "--mode", "full"]
    if resume_candidates:
        argv.append("--resume-candidates")
    if skip_pdf:
        argv.append("--skip-pdf")
    print("Running:", " ".join(argv))
    completed = subprocess.run(argv, cwd=REPO_ROOT, check=False)
    return int(completed.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify live full portfolio-first E2E artifacts (RM-1029)."
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run python run_portfolio_review.py --mode full [--skip-pdf] before validation.",
    )
    parser.add_argument(
        "--resume-candidates",
        action="store_true",
        help="When using --run, pass --resume-candidates to the orchestrator.",
    )
    parser.add_argument(
        "--with-pdf",
        action="store_true",
        help="When using --run, do not pass --skip-pdf to the orchestrator.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Override output_dir_final (default: from config.yml).",
    )
    args = parser.parse_args()

    if args.run:
        rc = _run_live_full(
            resume_candidates=args.resume_candidates,
            skip_pdf=not args.with_pdf,
        )
        if rc != 0:
            print(f"live full orchestrator exited {rc}", file=sys.stderr)
            return rc

    cfg = load_validated_config(REPO_ROOT / "config.yml")
    output_dir = args.output_dir or (REPO_ROOT / cfg.output_dir_final)
    result = validate_live_full_artifacts(
        output_dir,
        expect_resume_evidence=args.resume_candidates,
    )
    for line in result.messages():
        print(line)
    if result.ok:
        print("live full E2E validation: OK")
        return 0
    print("live full E2E validation: FAILED", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
