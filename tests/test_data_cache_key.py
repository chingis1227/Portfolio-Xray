from __future__ import annotations

import pandas as pd

from src import data_loader
from src.cache import compute_asset_metadata_fingerprint, compute_monthly_cache_key


def _cached_monthly_data() -> dict:
    idx = pd.to_datetime(["2024-01-31", "2024-02-29"])
    prices = pd.DataFrame(
        {
            "ABC": [100.0, 101.0],
            "SPY": [400.0, 404.0],
            "BIL": [91.0, 91.1],
        },
        index=idx,
    )
    returns = prices.pct_change().fillna(0.0)
    rf = pd.Series([0.001, 0.001], index=idx, name="rf")
    return {
        "monthly_prices": prices,
        "monthly_returns": returns,
        "monthly_log_returns": returns,
        "rf_monthly": rf,
        "benchmark_returns": returns["SPY"],
        "cash_returns": returns["BIL"],
        "fx_series": {},
    }


def test_asset_metadata_fingerprint_is_stable_for_order_and_currency_case() -> None:
    first = compute_asset_metadata_fingerprint({"ABC": "eur", "SPY": "USD"})
    second = compute_asset_metadata_fingerprint({"SPY": "usd", "ABC": "EUR"})

    assert first == second


def test_monthly_cache_key_changes_when_asset_currency_metadata_changes() -> None:
    base_args = {
        "tickers": ["ABC"],
        "investor_currency": "USD",
        "benchmark": "SPY",
        "cash_proxy": "BIL",
        "rf_source": "FRED:DTB3",
        "windows_months": [36, 60, 120],
        "data_month": "2026-04",
        "returns_frequency": "monthly",
    }
    usd_metadata = compute_asset_metadata_fingerprint({"ABC": "USD", "SPY": "USD", "BIL": "USD"})
    eur_metadata = compute_asset_metadata_fingerprint({"ABC": "EUR", "SPY": "USD", "BIL": "USD"})

    usd_key = compute_monthly_cache_key(**base_args, asset_metadata_fingerprint=usd_metadata)
    eur_key = compute_monthly_cache_key(**base_args, asset_metadata_fingerprint=eur_metadata)

    assert usd_metadata != eur_metadata
    assert usd_key != eur_key


def test_load_monthly_data_shared_threads_asset_metadata_fingerprint(monkeypatch, tmp_path) -> None:
    captured: dict = {}

    def fake_compute_monthly_cache_key(**kwargs):
        captured.update(kwargs)
        return "captured-monthly-key"

    monkeypatch.setattr(data_loader, "compute_monthly_cache_key", fake_compute_monthly_cache_key)
    monkeypatch.setattr(data_loader, "get_monthly_cache_path", lambda cache_key: tmp_path / cache_key)
    monkeypatch.setattr(data_loader, "cache_exists", lambda cache_path: True)
    monkeypatch.setattr(data_loader, "load_monthly_data", lambda cache_path: _cached_monthly_data())

    result = data_loader.load_monthly_data_shared(
        tickers=["ABC"],
        benchmark_base_ticker="SPY",
        cash_proxy_ticker="BIL",
        rf_source="FRED:DTB3",
        investor_currency="USD",
        windows_months=[36],
        assets_meta={"ABC": {"currency": "EUR"}},
    )

    expected_fingerprint = compute_asset_metadata_fingerprint(
        {
            "ABC": "EUR",
            "SPY": "USD",
            "BIL": "USD",
        }
    )
    assert captured["asset_metadata_fingerprint"] == expected_fingerprint
    assert result.monthly_cache_key == "captured-monthly-key"
