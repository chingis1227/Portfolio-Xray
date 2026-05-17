"""Rebalance threshold uses max absolute per-ticker drift, not portfolio turnover."""

from __future__ import annotations

from src.rebalance import compute_trades, rebalance_needed


def _half_turnover_pct(current: dict[str, float], target: dict[str, float]) -> float:
    tickers = set(current) | set(target)
    deltas = [target.get(t, 0.0) - current.get(t, 0.0) for t in tickers]
    return 0.5 * sum(abs(d) for d in deltas) * 100.0


def test_threshold_uses_max_per_ticker_drift_not_turnover() -> None:
    """High half-sum turnover with low max |Δw| must not trigger rebalance alone."""
    n = 10
    w = 1.0 / n
    shift = 0.008
    current = {f"T{i}": w for i in range(n)}
    target = dict(current)
    for i in range(5):
        target[f"T{i}"] = w - shift
    for i in range(5, n):
        target[f"T{i}"] = w + shift

    max_drift_pct = max(abs(target[t] - current[t]) for t in current) * 100.0
    turnover_pct = _half_turnover_pct(current, target)
    assert max_drift_pct < 1.0
    assert turnover_pct > 3.5

    _, needed = compute_trades(current, target, threshold_pct=2.5)
    assert needed is False
    assert rebalance_needed(current, target, threshold_pct=2.5) is False


def test_threshold_triggers_when_max_drift_exceeds_gate() -> None:
    current = {"A": 0.5, "B": 0.5}
    target = {"A": 0.53, "B": 0.47}
    assert rebalance_needed(current, target, threshold_pct=2.0) is True
    trades, needed = compute_trades(current, target, threshold_pct=2.0)
    assert needed is True
    assert trades
