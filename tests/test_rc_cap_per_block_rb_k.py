"""Unit tests for variant B RC caps (RB_block / k_block × multiplier)."""
from __future__ import annotations

from policy_math.feasibility import (
    RC_CAP_MODE_GLOBAL,
    RC_CAP_MODE_PER_BLOCK_RB_K,
    build_rc_cap_per_ticker,
    compute_rc_caps_by_block_from_targets,
    resolve_rc_cap_block_rb_k,
)


def test_resolve_rc_cap_block_rb_k_equal_split_multiplier():
    # RB=0.20, k=4, mult=1.25 → fair=0.05, cap=min(0.25, 0.0625)=0.0625
    c = resolve_rc_cap_block_rb_k(0.20, 4, 1.25, equity_only_growth=False)
    assert abs(c - 0.0625) < 1e-9

    c2 = resolve_rc_cap_block_rb_k(0.65, 20, 1.25, equity_only_growth=False)
    fair = 0.65 / 20
    assert abs(c2 - min(0.25, fair * 1.25)) < 1e-9


def test_resolve_rc_cap_block_rb_k_single_asset():
    c = resolve_rc_cap_block_rb_k(0.35, 1, 1.25, equity_only_growth=False)
    assert abs(c - 0.25) < 1e-9
    c2 = resolve_rc_cap_block_rb_k(0.50, 1, 1.25, equity_only_growth=False)
    assert abs(c2 - 0.25) < 1e-9


def test_equity_only_floor_growth():
    c = resolve_rc_cap_block_rb_k(0.10, 10, 1.0, equity_only_growth=True)
    assert c >= 0.15


def test_build_rc_cap_per_ticker_global_matches_scalar():
    blocks = {
        "Growth": ["A", "B"],
        "Duration": ["C"],
        "Inflation": ["D"],
    }
    rb = {"Growth": 0.5, "Duration": 0.25, "Inflation": 0.25}
    m = build_rc_cap_per_ticker(
        blocks,
        rb,
        None,
        RC_CAP_MODE_GLOBAL,
        1.25,
        n_total_for_global=4,
    )
    assert len(m) == 4
    assert len(set(m.values())) == 1


def test_build_rc_cap_per_ticker_variant_b_distinct_blocks():
    blocks = {
        "Growth": [f"G{i}" for i in range(20)],
        "Duration": ["D1", "D2", "D3", "D4"],
        "Inflation": ["I1", "I2"],
    }
    rb = {"Growth": 0.65, "Duration": 0.20, "Inflation": 0.15}
    caps_b = compute_rc_caps_by_block_from_targets(blocks, 0.65, 0.20, 0.15, 1.25, equity_only=False)
    assert caps_b["Duration"] > caps_b["Growth"]  # fewer names in Duration → higher fair share / cap

    m = build_rc_cap_per_ticker(
        blocks,
        rb,
        None,
        RC_CAP_MODE_PER_BLOCK_RB_K,
        1.25,
        n_total_for_global=26,
    )
    assert m["G0"] == caps_b["Growth"]
    assert m["D1"] == caps_b["Duration"]


def test_explicit_rc_asset_cap_pct_overrides_mode():
    blocks = {"Growth": ["A"], "Duration": ["B"], "Inflation": ["C"]}
    rb = {"Growth": 1 / 3, "Duration": 1 / 3, "Inflation": 1 / 3}
    m = build_rc_cap_per_ticker(
        blocks,
        rb,
        0.12,
        RC_CAP_MODE_PER_BLOCK_RB_K,
        1.25,
        n_total_for_global=3,
    )
    assert all(v == 0.12 for v in m.values())
