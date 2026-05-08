"""
Tests for Equal-Weight baselines (per-asset and class-balanced).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from src.config_schema import PortfolioConfig
from src.portfolio_variants import (
    EQUAL_WEIGHT_METHOD_BY_ASSET_CLASS,
    EQUAL_WEIGHT_METHOD_BY_ASSETS,
    build_equal_weight_baseline,
    build_equal_weight_by_asset_class_baseline,
    load_ticker_asset_class_map,
)


def _minimal_portfolio_config(tickers: list[str]) -> PortfolioConfig:
    n = len(tickers)
    eq = 1.0 / n if n else 0.0
    return PortfolioConfig(
        investor_currency="USD",
        initial_investable_amount=100_000.0,
        liquidity_need=0.0,
        liquidity_need_months=6.0,
        monthly_expenses=0.0,
        portfolio_value=100_000.0,
        cash_policy="allowed_for_scaling",
        tickers=list(tickers),
        weights={t: eq for t in tickers},
        benchmark_base_ticker="VOO",
        rf_source="FRED:DTB3",
        cash_proxy_ticker="BIL",
        local_benchmark_map=None,
        allow_leverage=False,
        allow_short_selling=False,
        min_acceptable_return=None,
        target_nominal_return_annual=None,
        target_vol_annual=None,
        target_max_drawdown_pct=None,
        horizon_years=None,
        client_profile=None,
        max_single_security_weight_pct=None,
        min_single_security_weight_pct=None,
        N_rc=5,
        donor_shift_mode="proportional",
        windows_months=[36, 60, 120],
        coverage_threshold=0.90,
        output_dir="results_csv",
        output_dir_final="Main portfolio",
    )


def _dense_monthly_returns(
    tickers: list[str],
    *,
    rng_seed: int = 7,
    n_months: int = 80,
    start: str = "2015-01-31",
) -> pd.DataFrame:
    rng = np.random.default_rng(rng_seed)
    dates = pd.date_range(start, periods=n_months, freq="ME")
    data = {t: rng.normal(0.005, 0.02, len(dates)) for t in tickers}
    return pd.DataFrame(data, index=dates)


def test_equal_weight_by_assets_weights_and_metadata() -> None:
    ts = ["VOO", "BND", "GLD"]
    ret = _dense_monthly_returns(ts)
    end = ret.index[-1].strftime("%Y-%m-%d")
    cfg = _minimal_portfolio_config(ts)
    res = build_equal_weight_baseline(cfg, ret, end, len(ret))

    assert res.status == "OK"
    pos = [res.weights[t] for t in ts]
    assert abs(sum(pos) - 1.0) < 1e-9
    assert all(abs(w - 1.0 / 3.0) < 1e-9 for w in pos)
    assert res.diagnostics["equal_weight_method"] == EQUAL_WEIGHT_METHOD_BY_ASSETS


def test_equal_weight_by_assets_unchanged_without_taxonomy_rollout() -> None:
    ts = ["A", "B", "C"]
    ret = _dense_monthly_returns(ts)
    end = ret.index[-1].strftime("%Y-%m-%d")
    cfg = _minimal_portfolio_config(ts)
    res = build_equal_weight_baseline(cfg, ret, end, len(ret))

    weights = {t: res.weights[t] for t in ts}
    assert weights == {"A": 1.0 / 3.0, "B": 1.0 / 3.0, "C": 1.0 / 3.0}


def test_equal_weight_by_asset_class_four_classes_example_structure() -> None:
    """4 classes × 25% budget; nested equal weights inside each class."""
    ts = ["E1", "E2", "E3", "E4", "E5", "C1", "C2", "F1", "CA1"]
    lookup = {
        **{f"E{k}": "equity" for k in range(1, 6)},
        "C1": "commodity",
        "C2": "commodity",
        "F1": "fixed_income",
        "CA1": "cash",
    }
    ret = _dense_monthly_returns(ts)
    end = ret.index[-1].strftime("%Y-%m-%d")
    cfg = _minimal_portfolio_config(ts)

    res = build_equal_weight_by_asset_class_baseline(
        cfg, ret, end, len(ret), asset_class_lookup=lookup
    )
    assert res.status == "OK"
    pos_w = [(t, res.weights[t]) for t in cfg.tickers if res.weights[t] > 1e-12]
    assert abs(sum(w for _, w in pos_w) - 1.0) < 1e-9

    cw = res.diagnostics["class_weights"]
    assert set(cw.keys()) == {"cash", "commodity", "equity", "fixed_income"}
    for bw in cw.values():
        assert abs(bw - 0.25) < 1e-9

    eq_ws = sorted(res.weights[f"E{k}"] for k in range(1, 6))
    assert abs(eq_ws[0] - 0.25 / 5.0) < 1e-9 and len(set(eq_ws)) == 1

    for c_sym in ("C1", "C2"):
        assert abs(res.weights[c_sym] - 0.25 / 2.0) < 1e-9
    assert abs(res.weights["F1"] - 0.25) < 1e-9
    assert abs(res.weights["CA1"] - 0.25) < 1e-9


def test_equal_weight_by_asset_class_excludes_missing_asset_class_warns() -> None:
    ts = ["A", "B", "BAD"]
    lookup = {"A": "equity", "B": "equity"}
    ret = _dense_monthly_returns(ts)
    end = ret.index[-1].strftime("%Y-%m-%d")
    cfg = _minimal_portfolio_config(ts)

    res = build_equal_weight_by_asset_class_baseline(
        cfg, ret, end, len(ret), asset_class_lookup=lookup
    )
    assert res.status == "OK"
    assert "BAD" in res.diagnostics["excluded_missing_asset_class"]
    assert res.weights["BAD"] == 0.0
    assert "warnings" in res.diagnostics
    assert sum(res.weights.values()) >= 1.0 - 1e-9
    ws = sorted([res.weights[t] for t in ("A", "B")])
    assert abs(ws[0] - 0.5) < 1e-9


def test_load_taxonomy_yaml_merge(tmp_path: Path) -> None:
    etf_yaml = "- {ticker: ZETF , asset_class: commodity}\n"
    stock_yaml = "- {ticker: ZEQ, asset_class: equity}\n"

    ef = tmp_path / "etf.yml"
    sf = tmp_path / "stock.yml"
    ef.write_text(etf_yaml, encoding="utf-8")
    sf.write_text(stock_yaml, encoding="utf-8")

    m = load_ticker_asset_class_map(etf_universe_path=ef, stock_universe_path=sf)
    assert m["ZETF"] == "commodity"
    assert m["ZEQ"] == "equity"


def test_equal_weight_methods_distinct_constants() -> None:
    assert EQUAL_WEIGHT_METHOD_BY_ASSETS != EQUAL_WEIGHT_METHOD_BY_ASSET_CLASS
