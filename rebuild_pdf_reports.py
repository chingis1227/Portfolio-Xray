#!/usr/bin/env python3
"""
Regenerate the PDF report suite from latest run outputs (Markdown sources in pdf_md_sources/, PDFs in pdf files/).

Requires Pandoc + XeLaTeX. If missing, Markdown sidecars are still updated; PDF steps are skipped with warnings.

Usage:
  python rebuild_pdf_reports.py                    # rebuild full legacy PDF suite from current outputs
  python rebuild_pdf_reports.py --portfolio-first  # subject sidecar + decision package only
  python rebuild_pdf_reports.py --after-variant    # run run_compare_ew_rp.py first (after EW or RP)
  python rebuild_pdf_reports.py --after-main       # run run_compare_variants.py first (after Main / policy report)
"""
from __future__ import annotations

import argparse
import sys

from src.pdf_reports import (
    try_rebuild_pdfs_after_main_report,
    try_rebuild_pdfs_after_portfolio_review,
    try_rebuild_pdfs_after_variant,
    try_rebuild_pdfs_only,
)
from src.utils import logger, setup_logging


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild PDF reports (Pandoc + XeLaTeX)")
    parser.add_argument(
        "--after-variant",
        action="store_true",
        help="Run run_compare_ew_rp.py before PDF build (refresh EW vs RP comparison JSON)",
    )
    parser.add_argument(
        "--after-main",
        action="store_true",
        help="Run run_compare_variants.py before PDF build (refresh Policy vs EW vs RP summary)",
    )
    parser.add_argument(
        "--portfolio-first",
        action="store_true",
        help=(
            "Rebuild portfolio-first PDFs only (analysis_subject sidecar + decision package); "
            "does not refresh legacy EW/RP/baseline variant PDFs"
        ),
    )
    args = parser.parse_args()
    setup_logging()
    if sum(bool(x) for x in (args.after_main, args.after_variant, args.portfolio_first)) > 1:
        parser.error("Use only one of --after-main, --after-variant, or --portfolio-first")
    if args.after_main:
        try_rebuild_pdfs_after_main_report(logger=logger)
    elif args.after_variant:
        try_rebuild_pdfs_after_variant(logger=logger)
    elif args.portfolio_first:
        try_rebuild_pdfs_after_portfolio_review(logger=logger)
    else:
        try_rebuild_pdfs_only(logger=logger)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
