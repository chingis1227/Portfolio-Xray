"""Real cash holdings: labels, validation, data panel, and analysis_setup disclosure."""
from __future__ import annotations

from unittest.mock import MagicMock

import pandas as pd
import pytest

from src.analysis_setup import build_analysis_setup, preflight_explicit_analysis_subject_tickers
from src.config import resolve_cash_and_rf
from src.config_schema import ConfigValidationError, validate_config
from src.data_loader import load_monthly_data_shared
from src.optimization import get_risk_portfolio_tickers
from src.real_cash import (
    collect_real_cash_tickers,
    inject_real_cash_return_panels,
    is_real_cash_ticker,
    partition_market_data_tickers,
)


def test_is_real_cash_ticker_labels() -> None:
    assert is_real_cash_ticker("Cash USD")
    assert is_real_cash_ticker("Cash EUR")
    assert is_real_cash_ticker("CASH")
    assert is_real_cash_ticker("CASH USD")
    assert not is_real_cash_ticker("BIL")
    assert not is_real_cash_ticker("VOO")


def test_validate_config_keeps_cash_usd_not_bil() -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "tickers": ["VOO", "BND", "Cash USD"],
            "weights": {"VOO": 0.45, "BND": 0.45, "Cash USD": 0.1},
        }
    )

    assert "Cash USD" in cfg.weights
    assert cfg.weights["Cash USD"] == pytest.approx(0.1)
    assert cfg.weights.get("BIL") is None
    cash_proxy, _ = resolve_cash_and_rf(cfg)
    assert cash_proxy == "BIL"


def test_preflight_allows_cash_usd_without_taxonomy() -> None:
    preflight_explicit_analysis_subject_tickers(["VOO", "Cash USD"])


def test_get_risk_portfolio_tickers_excludes_cash_usd_and_bil() -> None:
    tickers = ["VOO", "BND", "Cash USD", "BIL"]
    risk = get_risk_portfolio_tickers(tickers, "BIL")
    assert risk == ["VOO", "BND"]


def test_inject_zero_return_columns() -> None:
    import numpy as np

    index = pd.date_range("2020-01-31", periods=6, freq="ME")
    simple = pd.DataFrame({"VOO": [0.01, -0.02, 0.0, 0.03, -0.01, 0.02]}, index=index)
    log = pd.DataFrame(np.log1p(simple.to_numpy()), index=index, columns=["VOO"])
    prices = (1 + simple).cumprod()

    prices2, simple2, log2 = inject_real_cash_return_panels(
        prices,
        simple,
        log,
        ["Cash USD"],
    )

    assert "Cash USD" in simple2.columns
    assert (simple2["Cash USD"] == 0.0).all()
    assert (log2["Cash USD"] == 0.0).all()
    assert (prices2["Cash USD"] == 1.0).all()


def test_build_analysis_setup_real_cash_handling() -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "tickers": ["VOO", "Cash USD"],
            "weights": {"VOO": 0.9, "Cash USD": 0.1},
        }
    )
    setup = build_analysis_setup(
        cfg,
        portfolio_weights=cfg.weights,
        weights_source="config.analysis_subject.weights",
        cash_proxy_ticker="BIL",
    )
    cash = setup["analysis_portfolio"]["cash_handling"]
    assert cash["cash_proxy_ticker"] == "BIL"
    assert cash["real_cash_distinct_from_cash_proxy"] is True
    holdings = cash["real_cash_holdings"]
    assert len(holdings) == 1
    assert holdings[0]["ticker"] == "Cash USD"
    assert holdings[0]["weight"] == 0.1


def test_load_monthly_data_skips_download_for_cash_usd(monkeypatch: pytest.MonkeyPatch) -> None:
    downloaded: list[list[str]] = []

    def _fake_download(tickers, start, end, currency_by_ticker, *, provider=None):
        downloaded.append(list(tickers))
        idx = pd.bdate_range("2020-01-02", periods=800)
        prices: dict[str, pd.DataFrame] = {}
        for t in tickers:
            if t == "Cash USD":
                continue
            series = 100.0 + pd.Series(range(len(idx)), dtype=float, index=idx) * 0.05
            prices[t] = pd.DataFrame({"Close": series})
        return MagicMock(
            prices=prices,
            provider_by_ticker={t: "yfinance" for t in prices},
        )

    monkeypatch.setattr("src.data_loader.download_all_prices", _fake_download)
    monkeypatch.setattr("src.data_loader.cache_exists", lambda _path: False)
    monkeypatch.setattr("src.data_loader.load_daily_prices", lambda _path: None)
    monkeypatch.setattr("src.data_loader.save_daily_prices", lambda *_a, **_k: None)
    monkeypatch.setattr("src.data_loader.save_cache_meta", lambda *_a, **_k: None)
    monkeypatch.setattr("src.data_loader.save_monthly_data", lambda *_a, **_k: None)
    monkeypatch.setattr(
        "src.data_loader.fetch_fred_series",
        lambda *_a, **_k: pd.Series(2.0, index=pd.date_range("2018-01-31", periods=80, freq="ME")),
    )
    monkeypatch.setattr(
        "src.data_loader.convert_prices_to_investor_currency",
        lambda prices, *_a, **_k: prices,
    )
    monkeypatch.setattr(
        "src.data_loader.get_analysis_end",
        lambda monthly_index, today: pd.Timestamp("2025-12-31"),
    )

    result = load_monthly_data_shared(
        tickers=["VOO", "Cash USD"],
        benchmark_base_ticker="SPY",
        cash_proxy_ticker="BIL",
        rf_source="FRED:DTB3",
        investor_currency="USD",
        windows_months=[36],
        assets_meta={},
        no_cache=True,
    )

    assert downloaded
    assert "Cash USD" not in downloaded[0]
    assert "Cash USD" in result.monthly_returns.columns
    assert (result.monthly_returns["Cash USD"] == 0.0).all()


def test_partition_market_data_tickers() -> None:
    download, real = partition_market_data_tickers(["VOO", "Cash USD", "BIL"])
    assert download == ["VOO", "BIL"]
    assert real == ["Cash USD"]


def test_collect_real_cash_from_weights() -> None:
    labels = collect_real_cash_tickers(weights={"VOO": 0.9, "Cash USD": 0.1, "BIL": 0.0})
    assert labels == ["Cash USD"]


def test_mvp_preflight_rejects_only_non_cash_unknown() -> None:
    with pytest.raises(ConfigValidationError, match="unknown="):
        validate_config(
            {
                "investor_currency": "USD",
                "tickers": ["VOO", "NOTAREALTICKER"],
                "weights": {"VOO": 0.5, "NOTAREALTICKER": 0.5},
            }
        )
