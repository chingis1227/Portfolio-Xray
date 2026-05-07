from __future__ import annotations

import pandas as pd

from src.stress_factors_macro import build_regime_label_quality_check
from src.pandas_compat import MONTH_END_FREQ


def _labels_frame(seq: list[str], start: str = "2000-01-31") -> pd.DataFrame:
    idx = pd.date_range(start=start, periods=len(seq), freq=MONTH_END_FREQ)
    return pd.DataFrame(
        {
            "regime": seq,
            "growth_score": [0.8 if x in {"goldilocks", "reflation"} else -0.8 for x in seq],
            "inflation_score": [0.8 if x in {"reflation", "stagflation"} else -0.8 for x in seq],
            "growth_block_growth_labor_level": [1.0] * len(seq),
            "inflation_block_core_inflation_level": [1.0] * len(seq),
        },
        index=idx,
    )


def test_regime_label_quality_thresholds_and_episodes() -> None:
    seq = (
        ["goldilocks"] * 10
        + ["reflation"] * 12
        + ["stagflation"] * 24
        + ["recession_disinflation"] * 60
        + ["neutral_transition"] * 2
    )
    frame = _labels_frame(seq)
    out = build_regime_label_quality_check(
        labels_with_regime=frame,
        coverage_tier="full",
        optional_blocks_missing=set(),
        available_blocks={"growth_labor", "core_inflation"},
        missing_blocks=set(),
        neutral_band=0.25,
    )

    by = out["by_regime"]
    assert by["goldilocks"]["quality_status"] == "insufficient_data"
    assert by["reflation"]["quality_status"] == "low_confidence"
    assert by["stagflation"]["quality_status"] == "usable"
    assert by["recession_disinflation"]["quality_status"] == "reliable"
    assert by["recession_disinflation"]["n_episodes"] == 1
    assert out["stability_summary"]["n_switches"] == 4
    assert out["metadata_quality"]["coverage_tier_distribution"]["full"] == len(seq)
    assert "2020_covid_shock" in {x["window"] for x in out["macro_sanity_checks"]["episodes"]}


def test_regime_label_quality_switch_noise_warning() -> None:
    seq = ["goldilocks" if i % 2 == 0 else "reflation" for i in range(36)]
    frame = _labels_frame(seq, start="2018-01-31")
    out = build_regime_label_quality_check(
        labels_with_regime=frame,
        coverage_tier="reduced",
        optional_blocks_missing={"growth_nowcast"},
        available_blocks={"growth_labor"},
        missing_blocks={"growth_nowcast"},
        neutral_band=0.25,
    )

    stable = out["stability_summary"]
    assert stable["n_switches"] == 35
    assert stable["too_frequent_switches"] is True
    assert stable["too_many_one_month_regimes"] is True
    assert out["overall_assessment"]["classifier_noise_warning"] is True
