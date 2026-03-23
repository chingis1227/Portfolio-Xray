#!/usr/bin/env python3
"""
Regenerate the PDF report suite from latest run outputs (Markdown sources in pdf_md_sources/, PDFs in pdf files/).

Requires Pandoc + XeLaTeX. If missing, Markdown sidecars are still updated; PDF steps are skipped with warnings.

Usage:
  python rebuild_pdf_reports.py                    # rebuild from current JSON/txt/yml
  python rebuild_pdf_reports.py --after-variant    # run run_compare_ew_rp.py first (after EW or RP)
  python rebuild_pdf_reports.py --after-main       # run run_compare_variants.py first (after Main / policy report)
"""
from __future__ import annotations

import argparse
import sys

from src.pdf_reports import (
    try_rebuild_pdfs_after_main_report,
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
    args = parser.parse_args()
    setup_logging()
    if args.after_main:
        try_rebuild_pdfs_after_main_report(logger=logger)
    elif args.after_variant:
        try_rebuild_pdfs_after_variant(logger=logger)
    else:
        try_rebuild_pdfs_only(logger=logger)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
