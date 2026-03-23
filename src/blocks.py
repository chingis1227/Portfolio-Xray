"""
Single source of truth for ticker → block mapping (RB and stress).

- get_ticker_to_block_for_rb(blocks): Growth, Duration, Inflation; Growth_HY and Growth_EM_debt → Growth.
- get_ticker_to_block_for_stress(blocks, tickers=None): Growth, Duration, Inflation, Liquidity, Tail; sub-blocks → Growth.
"""
from __future__ import annotations

# Keep in sync with config_schema for block names
RISK_BUDGET_BLOCKS = ("Growth", "Duration", "Inflation")
GROWTH_HY_KEY = "Growth_HY"
GROWTH_EM_DEBT_KEY = "Growth_EM_debt"
STRESS_BLOCK_NAMES = ("Growth", "Duration", "Inflation", "Liquidity", "Tail")


def get_ticker_to_block_for_rb(blocks: dict[str, list[str]]) -> dict[str, str]:
    """
    Map each ticker to one of Growth, Duration, Inflation for risk budget and RC.
    Growth_HY and Growth_EM_debt map to Growth.
    """
    out: dict[str, str] = {}
    for b in RISK_BUDGET_BLOCKS:
        for t in blocks.get(b, []):
            out[t] = b
    for b in (GROWTH_HY_KEY, GROWTH_EM_DEBT_KEY):
        for t in blocks.get(b, []):
            out[t] = "Growth"
    return out


def get_ticker_to_block_for_stress(
    blocks: dict[str, list[str]],
    tickers: list[str] | None = None,
) -> dict[str, str]:
    """
    Map each ticker to one of Growth, Duration, Inflation, Liquidity, Tail for stress.
    Growth_HY and Growth_EM_debt map to Growth. Unlisted tickers (if tickers given) → Growth.
    """
    out: dict[str, str] = {}
    for block_name in STRESS_BLOCK_NAMES:
        for t in blocks.get(block_name, []):
            out[t] = block_name
    for t in blocks.get(GROWTH_HY_KEY, []):
        out[t] = "Growth"
    for t in blocks.get(GROWTH_EM_DEBT_KEY, []):
        out[t] = "Growth"
    if tickers:
        for t in tickers:
            if t not in out:
                out[t] = "Growth"
    return out
