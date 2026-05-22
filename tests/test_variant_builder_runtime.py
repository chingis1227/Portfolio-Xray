from __future__ import annotations

import os
from unittest.mock import patch

from src.variant_builder_runtime import (
    ENV_SKIP_VARIANT_PDF,
    BuilderStepTiming,
    maybe_rebuild_pdfs_after_variant,
    variant_pdf_skip_requested,
)


def test_variant_pdf_skip_requested_reads_env() -> None:
    with patch.dict(os.environ, {ENV_SKIP_VARIANT_PDF: "1"}, clear=False):
        assert variant_pdf_skip_requested() is True
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop(ENV_SKIP_VARIANT_PDF, None)
        assert variant_pdf_skip_requested() is False


def test_maybe_rebuild_pdfs_skips_when_env_set() -> None:
    timing = BuilderStepTiming()
    with patch.dict(os.environ, {ENV_SKIP_VARIANT_PDF: "1"}, clear=False):
        with patch(
            "src.pdf_reports.try_rebuild_pdfs_after_variant",
        ) as mocked:
            maybe_rebuild_pdfs_after_variant(timing=timing)
            mocked.assert_not_called()
    assert timing.pdf_seconds == 0.0
