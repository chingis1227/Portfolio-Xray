from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from pandas.tseries.frequencies import to_offset


def _supports_freq(freq: str) -> bool:
    try:
        to_offset(freq)
        return True
    except ValueError:
        return False


_DATE_RANGE = pd.date_range


def _compat_date_range(*args, **kwargs):
    freq = kwargs.get("freq")
    if freq == "ME" and not _supports_freq("ME"):
        kwargs["freq"] = "M"
    elif freq == "M" and not _supports_freq("M"):
        kwargs["freq"] = "ME"
    return _DATE_RANGE(*args, **kwargs)


pd.date_range = _compat_date_range


def pytest_configure(config) -> None:
    if not getattr(config.option, "basetemp", None):
        user_profile = Path(os.environ.get("USERPROFILE", str(Path.home())))
        base = user_profile / ".cache" / "codex-pytest-temp"
        base.mkdir(parents=True, exist_ok=True)
        config.option.basetemp = str(base)
