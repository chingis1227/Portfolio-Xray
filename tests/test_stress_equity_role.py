"""Equity shock Role: defensive sum S and severity tiers (stress_testing_spec §6)."""

import pytest

from src.stress import (
    EQUITY_DEFENSIVE_SUM_FAIL_BELOW,
    _equity_defensive_sum,
    _equity_shock_role_severity,
)


@pytest.mark.parametrize(
    "S,expected",
    [
        (0.0, "ok"),
        (0.001, "ok"),
        (-0.001, "warn"),
        (-0.005, "warn"),
        (-0.01, "warn"),
        (-0.0100001, "fail"),
        (-0.05, "fail"),
    ],
)
def test_equity_shock_role_severity(S: float, expected: str) -> None:
    assert _equity_shock_role_severity(S) == expected
    assert EQUITY_DEFENSIVE_SUM_FAIL_BELOW == -0.01


def test_equity_defensive_sum() -> None:
    pnl = {"Duration": -0.02, "Inflation": 0.015, "Tail": 0.0, "Growth": -0.1}
    assert _equity_defensive_sum(pnl) == pytest.approx(-0.005)
