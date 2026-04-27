"""Pure helpers for resampled weight averaging (no dependency on compare_* scripts)."""

from __future__ import annotations

import numpy as np


def _average_weights(weight_dicts: list[dict[str, float]]) -> dict[str, float]:
    if not weight_dicts:
        return {}
    tickers: set[str] = set()
    for w in weight_dicts:
        tickers |= {t for t, x in w.items() if x and x > 1e-15}
    out = {t: float(np.mean([wd.get(t, 0.0) for wd in weight_dicts])) for t in tickers}
    s = sum(out.values())
    if s <= 1e-15:
        return {}
    return {t: out[t] / s for t in out}


def test_average_weights_renormalizes():
    wds = [
        {"A": 0.5, "B": 0.5},
        {"A": 0.4, "B": 0.6},
    ]
    out = _average_weights(wds)
    assert abs(sum(out.values()) - 1.0) < 1e-9
    assert abs(out["A"] - 0.45) < 1e-9
    assert abs(out["B"] - 0.55) < 1e-9


def test_average_weights_empty():
    assert _average_weights([]) == {}


def test_average_weights_single():
    out = _average_weights([{"X": 1.0}])
    assert abs(out["X"] - 1.0) < 1e-9
