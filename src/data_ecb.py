"""
Fetch ECB €STR (Euro Short-Term Rate) for risk-free in EUR. Uses estr.dev API (ECB-sourced).
Returns Series with DatetimeIndex and annual percent (same convention as FRED).
"""
from __future__ import annotations

import urllib.parse
import urllib.request

import pandas as pd

ESTR_API = "https://api.estr.dev/historical"


def fetch_estr(start: str, end: str) -> pd.Series:
    """
    Fetch €STR historical rates. Returns Series with DatetimeIndex and annual percent (e.g. 3.9 for 3.9%).
    """
    params = urllib.parse.urlencode({"from": start, "to": end})
    url = f"{ESTR_API}...{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "PortfolioMetrics/1.0 (python)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read().decode("utf-8")
    import json

    rows = json.loads(data)
    if not rows:
        return pd.Series(dtype=float)
    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["date"])
    df = df.set_index("Date").sort_index()
    s = df["value"].astype(float)
    s.index = s.index.tz_localize(None)
    s = s.rename_axis("Date")
    return s
