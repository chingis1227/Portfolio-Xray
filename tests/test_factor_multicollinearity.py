"""Unit tests for factor multicollinearity diagnostics (no network)."""
from __future__ import annotations

import numpy as np

from src.stress_factors import factor_multicollinearity_diagnostics


def test_factor_multicollinearity_orthogonal_low_severity() -> None:
    rng = np.random.default_rng(0)
    n = 200
    X = np.column_stack([rng.normal(size=n), rng.normal(size=n), rng.normal(size=n)])
    cols = ["a", "b", "c"]
    out = factor_multicollinearity_diagnostics(X, cols)
    assert out.get("error") is None
    assert out["severity"] == "low"
    assert out["n_obs_factors"] == n
    assert len(out["pairwise_correlations"]) == 3
    assert out["max_vif"] is not None and float(out["max_vif"]) < 5.0
    assert out["cond_correlation_matrix"] is not None and float(out["cond_correlation_matrix"]) < 30.0
    assert "assessment_en" in out
    assert isinstance(out["assessment_en"], str) and out["assessment_en"].startswith("Low:")
    assert "assessment_en_legacy" not in out


def test_factor_multicollinearity_duplicate_column_high_vif() -> None:
    rng = np.random.default_rng(1)
    n = 100
    z = rng.normal(size=n)
    # Exact duplication => auxiliary R² = 1 for duplicated column => infinite VIF
    X = np.column_stack([z, z, rng.normal(size=n)])
    out = factor_multicollinearity_diagnostics(X, ["x1", "x2", "x3"])
    assert out.get("error") is None
    assert out["severity"] == "high"
    assert out.get("max_vif_is_infinite") is True
    assert "assessment_en" in out
    assert "High:" in out["assessment_en"]
    assert "assessment_en_legacy" not in out


def test_multicollinearity_commentary_prefers_assessment_en_over_legacy_ru() -> None:
    from src.portfolio_commentary import _append_factor_multicollinearity_section

    lines: list[str] = []
    _append_factor_multicollinearity_section(
        lines,
        {
            "severity": "low",
            "assessment_en": "Primary English text.",
            "assessment_en_legacy": "Legacy Russian text.",
        },
    )
    text = "\n".join(lines)
    assert "Assessment: Primary English text." in text
    assert "Legacy Russian text." not in text


def test_multicollinearity_commentary_reads_legacy_assessment_ru() -> None:
    from src.portfolio_commentary import _append_factor_multicollinearity_section

    lines: list[str] = []
    _append_factor_multicollinearity_section(
        lines,
        {"severity": "low", "assessment_en_legacy": "Legacy-only assessment."},
    )
    assert "Assessment: Legacy-only assessment." in "\n".join(lines)
