"""Pytest hooks for the repository test suite."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_TESTS_DIR = Path(__file__).resolve().parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--live-core",
        action="store_true",
        default=False,
        help="Enable live core E2E artifact validation (networked run done separately)",
    )
    parser.addoption(
        "--live-full",
        action="store_true",
        default=False,
        help="Enable live full E2E artifact validation (networked run done separately)",
    )


def _live_core_enabled(config: pytest.Config) -> bool:
    if config.getoption("--live-core", default=False):
        return True
    return os.environ.get("PORTFOLIO_LIVE_CORE_E2E", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _live_full_enabled(config: pytest.Config) -> bool:
    if config.getoption("--live-full", default=False):
        return True
    return os.environ.get("PORTFOLIO_LIVE_FULL_E2E", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "live_core: live core E2E artifact gate (RM-1021); requires prior --mode core run",
    )
    config.addinivalue_line(
        "markers",
        "live_full: live full E2E artifact gate (RM-1029); requires prior --mode full run",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if not _live_core_enabled(config):
        skip_core = pytest.mark.skip(
            reason="live core E2E disabled (pytest --live-core or PORTFOLIO_LIVE_CORE_E2E=1)"
        )
        for item in items:
            if "live_core" in item.keywords:
                item.add_marker(skip_core)
    if not _live_full_enabled(config):
        skip_full = pytest.mark.skip(
            reason="live full E2E disabled (pytest --live-full or PORTFOLIO_LIVE_FULL_E2E=1)"
        )
        for item in items:
            if "live_full" in item.keywords:
                item.add_marker(skip_full)
