from __future__ import annotations

import numpy as np

from src import stress_factors as sf


def _orthogonal_residual(X: np.ndarray, seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    z = rng.normal(size=X.shape[0])
    design = np.column_stack([np.ones(X.shape[0]), X])
    projection = design @ np.linalg.lstsq(design, z, rcond=None)[0]
    return z - projection


def _fixture(target_r2: float = 0.8) -> tuple[np.ndarray, np.ndarray, list[str]]:
    rng = np.random.default_rng(42)
    X = rng.normal(size=(180, 3))
    beta = np.array([0.5, -0.3, 0.0])
    signal = X @ beta
    e = _orthogonal_residual(X)
    scale = np.sqrt(np.var(signal, ddof=1) * (1.0 - target_r2) / (target_r2 * np.var(e, ddof=1)))
    y = signal + scale * e
    return y, X, ["equity", "credit", "usd"]


def test_factor_variance_decomposition_formula_and_weekly_scale() -> None:
    y, X, cols = _fixture(target_r2=0.8)
    out = sf._factor_variance_decomposition_from_rows(y, X, cols)

    assert out["status"] == "available"
    assert out["variance_scale"] == "weekly"
    assert out["ddof"] == 1
    factor_rows = [r for r in out["rows"] if r["direction"] != "residual"]
    assert np.isclose(sum(r["factor_rc_share"] for r in factor_rows), 1.0)
    assert np.isclose(sum(r["net_total_variance_share"] for r in factor_rows), out["r2"])
    assert np.isclose(out["residual_share"], 1.0 - out["r2"])
    assert np.isclose(sum(r["gross_total_variance_share"] for r in factor_rows), out["r2"])
    assert out["cross_check"]["status"] == "pass"


def test_factor_variance_decomposition_net_gross_and_neutral_classification() -> None:
    y, X, cols = _fixture(target_r2=0.8)
    out = sf._factor_variance_decomposition_from_rows(y, X, cols)

    factor_rows = {r["factor"]: r for r in out["rows"] if r["direction"] != "residual"}
    assert factor_rows["usd"]["direction"] == "neutral"
    assert factor_rows["usd"]["gross_total_variance_share"] < 1e-8
    assert any(r["direction"] == "risk_adder" for r in out["risk_adders"])
    assert isinstance(out["hedgers"], list)
    assert all(r["gross_total_variance_share"] >= 0.0 for r in factor_rows.values())


def test_factor_variance_decomposition_degeneracy_and_dimension_guards() -> None:
    y, X, cols = _fixture(target_r2=0.8)
    short = sf._factor_variance_decomposition_from_rows(y[:20], X[:20], cols)
    assert short["status"] == "unavailable"
    assert short["reason"] == "insufficient_observations"

    flat = sf._factor_variance_decomposition_from_rows(np.ones_like(y), X, cols)
    assert flat["status"] == "unavailable"
    assert flat["reason"] in {"ols_failed", "degenerate_portfolio_variance"}

    y_orth = _orthogonal_residual(X, seed=21)
    degenerate_factor = sf._factor_variance_decomposition_from_rows(y_orth, X, cols)
    assert degenerate_factor["status"] == "unavailable"
    assert degenerate_factor["reason"] == "degenerate_factor_variance"

    mismatch = sf._factor_variance_decomposition_from_rows(y, X, ["equity", "credit"])
    assert mismatch["status"] == "unavailable"
    assert mismatch["reason"] == "factor_dimension_mismatch"


def test_factor_variance_decomposition_cross_check_thresholds() -> None:
    assert sf._factor_decomp_cross_check(factor_variance=0.8, portfolio_total_variance=1.0, r2=0.802)["status"] == "pass"
    warning = sf._factor_decomp_cross_check(factor_variance=0.8, portfolio_total_variance=1.0, r2=0.79)
    assert warning["status"] == "warning"
    assert warning["warning_code"] == "WARN_FACTOR_VARIANCE_DECOMP_MISMATCH"
    high = sf._factor_decomp_cross_check(factor_variance=0.8, portfolio_total_variance=1.0, r2=0.75)
    assert high["status"] == "high_warning"
    assert high["warning_code"] == "WARN_FACTOR_VARIANCE_DECOMP_HIGH_MISMATCH"
    unavailable = sf._factor_decomp_cross_check(factor_variance=None, portfolio_total_variance=1.0, r2=0.8)
    assert unavailable["status"] == "unavailable"


def test_factor_variance_decomposition_residual_severity() -> None:
    assert sf._residual_diagnostics(0.20)["residual_severity"] == "low"
    assert sf._residual_diagnostics(0.40)["residual_severity"] == "moderate"
    assert sf._residual_diagnostics(0.70)["residual_severity"] == "high"


def test_factor_variance_decomposition_stability_v1() -> None:
    y, X, cols = _fixture(target_r2=0.8)
    snap1 = sf._factor_variance_decomposition_from_rows(y, X, cols, include_stability=False)
    snap2 = sf._factor_variance_decomposition_from_rows(y * 1.01, X, cols, include_stability=False)
    out = sf._factor_variance_decomposition_from_rows(y, X, cols, stability_snapshots=[snap1, snap2])

    assert out["stability"]["status"] == "available"
    assert out["stability"]["overall_severity"] == "low"
    assert out["stability"]["r2"]["severity"] == "low"

    unknown = sf._factor_variance_decomposition_from_rows(y, X, cols)
    assert unknown["stability"]["status"] == "unknown"
