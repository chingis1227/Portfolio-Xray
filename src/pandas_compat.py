from __future__ import annotations

import pandas as pd
from pandas.tseries.frequencies import to_offset


def _supports_freq(freq: str) -> bool:
    try:
        to_offset(freq)
        return True
    except ValueError:
        return False


def month_end_freq() -> str:
    if _supports_freq("ME"):
        return "ME"
    if _supports_freq("M"):
        return "M"
    return "ME"


MONTH_END_FREQ = month_end_freq()
