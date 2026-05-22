"""Tests for EW vs RP comparison CSV parsing (Session 7 PDF reliability)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from run_compare_ew_rp import _read_var_es_metrics_csv


def test_read_var_es_metrics_csv_skips_historical_method_column(tmp_path: Path) -> None:
    csv_path = tmp_path / "var_es_10y.csv"
    pd.DataFrame(
        [
            {
                "method": "historical",
                "frequency": "daily",
                "window_months": 120,
                "window_label": "10y",
                "n_obs": 2520,
                "var_95": -0.021,
                "var_99": -0.031,
                "es_95": -0.028,
                "es_99": -0.039,
                "metric_available": True,
            }
        ]
    ).to_csv(csv_path, index=False)

    metrics = _read_var_es_metrics_csv(csv_path)

    assert metrics == {
        "var_95": -0.021,
        "var_99": -0.031,
        "es_95": -0.028,
        "es_99": -0.039,
    }
    assert "method" not in metrics
    assert "frequency" not in metrics
