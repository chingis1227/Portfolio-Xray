"""Factor beta stability diagnostics (no network)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src import stress_factors as sf


def _df(values: list[float]) -> pd.DataFrame:
    return pd.DataFrame({"beta_eq": values}, index=pd.date_range("2020-01-31", periods=len(values), freq="ME"))


def test_factor_beta_stability_low_for_stable_positive_beta() -> None:
    rolling = {
        "weekly": {"3y": _df([0.48, 0.50, 0.51, 0.49, 0.52])},
        "monthly": {"3y": _df([0.47, 0.50, 0.51, 0.49, 0.50])},
    }
    oos = {
        "by_beta": {
            "beta_eq": {
                "severity": "low",
                "n_tests": 4,
                "sign_match_share": 1.0,
                "relative_magnitude_degradation": 0.1,
            }
        }
    }

    out = sf.factor_beta_stability_diagnostics(rolling, oos_stability=oos)

    row = out["by_beta"]["beta_eq"]
    assert row["combined_severity"] == "low"
    assert row["sign_stability"]["severity"] == "low"
    assert row["magnitude_stability"]["severity"] == "low"
    assert row["specification_sensitivity"]["severity"] == "low"


def test_factor_beta_stability_high_for_frequent_sign_changes() -> None:
    rolling = {"weekly": {"3y": _df([0.5, -0.5, 0.45, -0.45, 0.4, -0.4])}}

    out = sf.factor_beta_stability_diagnostics(rolling)

    row = out["by_beta"]["beta_eq"]
    assert row["sign_stability"]["severity"] == "high"
    assert row["combined_severity"] == "high"


def test_factor_beta_stability_high_for_wide_magnitude_band() -> None:
    rolling = {"weekly": {"3y": _df([0.05, 0.20, 0.50, 0.80, 1.10, 1.40])}}

    out = sf.factor_beta_stability_diagnostics(rolling)

    row = out["by_beta"]["beta_eq"]
    assert row["magnitude_stability"]["severity"] in {"moderate", "high"}
    assert row["combined_severity"] in {"moderate", "high"}


def test_factor_beta_stability_high_for_specification_sign_disagreement() -> None:
    rolling = {
        "weekly": {"3y": _df([0.4, 0.5, 0.6])},
        "monthly": {"3y": _df([-0.4, -0.5, -0.6])},
    }

    out = sf.factor_beta_stability_diagnostics(rolling)

    row = out["by_beta"]["beta_eq"]
    assert row["specification_sensitivity"]["sign_disagreement"] is True
    assert row["specification_sensitivity"]["severity"] == "high"
    assert row["combined_severity"] == "high"


def test_oos_stability_high_for_sign_mismatch() -> None:
    records = pd.DataFrame(
        {
            "beta": ["beta_eq", "beta_eq", "beta_eq"],
            "sign_match": [False, False, True],
            "relative_magnitude_degradation": [0.2, 0.3, 0.1],
        }
    )

    out = sf.factor_beta_oos_stability_diagnostics({"weekly": {"3y": records}})

    row = out["by_beta"]["beta_eq"]
    assert row["severity"] == "high"
    assert np.isclose(row["sign_match_share"], 1.0 / 3.0)


def test_oos_stability_high_for_magnitude_degradation() -> None:
    records = pd.DataFrame(
        {
            "beta": ["beta_eq", "beta_eq", "beta_eq"],
            "sign_match": [True, True, True],
            "relative_magnitude_degradation": [2.5, 2.2, 2.1],
        }
    )

    out = sf.factor_beta_oos_stability_diagnostics({"weekly": {"3y": records}})

    row = out["by_beta"]["beta_eq"]
    assert row["severity"] == "high"
    assert row["relative_magnitude_degradation"] >= 2.0


def test_severity_distribution_warns_when_high_share_above_threshold() -> None:
    rolling = {
        "weekly": {
            "3y": pd.DataFrame(
                {
                    "beta_eq": [0.5, -0.5, 0.5, -0.5],
                    "beta_rr": [0.4, -0.4, 0.4, -0.4],
                    "beta_inf": [0.3, -0.3, 0.3, -0.3],
                    "beta_credit": [0.2, -0.2, 0.2, -0.2],
                }
            )
        }
    }

    out = sf.factor_beta_stability_diagnostics(rolling)

    assert out["severity_distribution"]["shares"]["high"] > 0.70
    assert out["severity_distribution_warning"] == "thresholds_may_be_too_strict_consider_relaxing_magnitude_to_1_5_2_5"


def test_severity_distribution_warns_when_low_share_above_threshold() -> None:
    rolling = {
        "weekly": {
            "3y": pd.DataFrame(
                {
                    "beta_eq": [0.50, 0.51, 0.49],
                    "beta_rr": [0.60, 0.61, 0.59],
                    "beta_inf": [0.70, 0.71, 0.69],
                    "beta_credit": [0.80, 0.81, 0.79],
                    "beta_usd": [0.90, 0.91, 0.89],
                }
            )
        }
    }

    out = sf.factor_beta_stability_diagnostics(rolling)

    assert out["severity_distribution"]["shares"]["low"] > 0.80
    assert out["severity_distribution_warning"] == "thresholds_may_be_too_soft"
