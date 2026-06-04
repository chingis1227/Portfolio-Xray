from __future__ import annotations

import json

import pandas as pd
import pytest

from src import data_loader
from src.cache import compute_asset_metadata_fingerprint, compute_daily_cache_key, compute_monthly_cache_key
from src.io_export import export_data_policy


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


def _daily_price_cache() -> dict[str, pd.DataFrame]:
    idx = pd.date_range("2024-01-01", "2024-03-31", freq="D")
    base = pd.Series(range(len(idx)), index=idx, dtype=float)
    return {
        "ABC": pd.DataFrame({"Close": 100.0 + base * 0.10}, index=idx),
        "SPY": pd.DataFrame({"Close": 400.0 + base * 0.20}, index=idx),
        "BIL": pd.DataFrame({"Close": 91.0 + base * 0.01}, index=idx),
    }


def _write_cached_rf(cache_dir, *, rf_source: str = "FRED:DTB3", currency: str = "USD") -> None:
    cache_dir.mkdir(parents=True)
    (cache_dir / "meta.json").write_text(
        json.dumps(
            {
                "created_at": "2024-04-01T00:00:00",
                "config": {
                    "rf_source": rf_source,
                    "investor_currency": currency,
                    "returns_frequency": "monthly",
                    "data_month": "2024-03",
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    idx = pd.to_datetime(["2024-01-31", "2024-02-29", "2024-03-31"])
    pd.Series([0.001, 0.0011, 0.0012], index=idx, name="rf").to_frame("rf").to_parquet(
        cache_dir / "rf_monthly.parquet"
    )


def _install_rf_fallback_loader_mocks(monkeypatch, tmp_path):
    daily_path = tmp_path / "daily_current"
    monthly_path = tmp_path / "monthly_current"
    cache_root = tmp_path / "cache"

    monkeypatch.setattr(data_loader, "CACHE_DIR", cache_root)
    monkeypatch.setattr(data_loader, "get_daily_cache_path", lambda _key: daily_path)
    monkeypatch.setattr(data_loader, "get_monthly_cache_path", lambda _key: monthly_path)
    monkeypatch.setattr(data_loader, "cache_exists", lambda path: path == daily_path)
    monkeypatch.setattr(data_loader, "load_daily_prices", lambda _path: _daily_price_cache())
    monkeypatch.setattr(
        data_loader,
        "fetch_fred_series",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(TimeoutError("FRED timed out")),
    )
    return cache_root


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


def test_cache_keys_change_when_market_data_provider_changes() -> None:
    daily_yf = compute_daily_cache_key(["SPY"], "2026-01-01", "2026-05-22", "2026-05-22")
    daily_ibkr = compute_daily_cache_key(
        ["SPY"],
        "2026-01-01",
        "2026-05-22",
        "2026-05-22",
        data_provider="ibkr_yfinance_fallback",
    )
    monthly_args = {
        "tickers": ["SPY"],
        "investor_currency": "USD",
        "benchmark": "SPY",
        "cash_proxy": "BIL",
        "rf_source": "FRED:DTB3",
        "windows_months": [36],
        "data_month": "2026-04",
        "asset_metadata_fingerprint": compute_asset_metadata_fingerprint({"SPY": "USD", "BIL": "USD"}),
    }
    monthly_yf = compute_monthly_cache_key(**monthly_args)
    monthly_ibkr = compute_monthly_cache_key(**monthly_args, data_provider="ibkr_yfinance_fallback")

    assert daily_yf != daily_ibkr
    assert monthly_yf != monthly_ibkr


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
        data_provider="ibkr_yfinance_fallback",
    )

    expected_fingerprint = compute_asset_metadata_fingerprint(
        {
            "ABC": "EUR",
            "SPY": "USD",
            "BIL": "USD",
        }
    )
    assert captured["asset_metadata_fingerprint"] == expected_fingerprint
    assert captured["data_provider"] == "ibkr_yfinance_fallback"
    assert result.monthly_cache_key == "captured-monthly-key"


def test_load_monthly_data_shared_uses_approved_cached_rf_on_fred_timeout(
    monkeypatch,
    tmp_path,
) -> None:
    cache_root = _install_rf_fallback_loader_mocks(monkeypatch, tmp_path)
    _write_cached_rf(cache_root / "monthly" / "v_cachedrf")

    result = data_loader.load_monthly_data_shared(
        tickers=["ABC"],
        benchmark_base_ticker="SPY",
        cash_proxy_ticker="BIL",
        rf_source="FRED:DTB3",
        investor_currency="USD",
        windows_months=[36],
        assets_meta={},
        allow_risk_free_cached_fallback=True,
    )

    meta = result.risk_free_metadata or {}
    assert meta["risk_free_fallback_used"] is True
    assert meta["risk_free_fallback_reason"] == "fred_timeout_cached_rf"
    assert meta["risk_free_source_requested"] == "FRED:DTB3"
    assert meta["risk_free_source_used"] == "approved_cached_risk_free_series"
    assert meta["risk_free_cache_key"] == "cachedrf"
    assert "risk_free_fallback_used:fred_timeout_cached_rf" in result.risk_free_warnings
    assert result.rf_monthly.reindex(result.monthly_returns.index).ffill().notna().all()


def test_load_monthly_data_shared_fails_clearly_when_fred_timeout_has_no_approved_rf_cache(
    monkeypatch,
    tmp_path,
) -> None:
    _install_rf_fallback_loader_mocks(monkeypatch, tmp_path)

    with pytest.raises(RuntimeError, match="no approved cached risk-free series"):
        data_loader.load_monthly_data_shared(
            tickers=["ABC"],
            benchmark_base_ticker="SPY",
            cash_proxy_ticker="BIL",
            rf_source="FRED:DTB3",
            investor_currency="USD",
            windows_months=[36],
            assets_meta={},
            allow_risk_free_cached_fallback=True,
        )


def test_export_data_policy_surfaces_risk_free_fallback_metadata(tmp_path) -> None:
    meta = {
        "risk_free_fallback_used": True,
        "risk_free_fallback_reason": "fred_timeout_cached_rf",
        "risk_free_cache_key": "cachedrf",
    }
    warning = "Risk-free FRED source timed out; using approved cached risk-free series."

    path = export_data_policy(
        tmp_path,
        backtest_mode="dynamic_nan_safe",
        first_available_month={"ABC": "2024-02"},
        risk_free_metadata=meta,
        risk_free_warnings=["risk_free_fallback_used:fred_timeout_cached_rf", warning],
    )

    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["risk_free_fallback_used"] is True
    assert doc["risk_free_fallback_reason"] == "fred_timeout_cached_rf"
    assert doc["risk_free_data_provenance"]["risk_free_cache_key"] == "cachedrf"
    assert "risk_free_fallback_used:fred_timeout_cached_rf" in doc["warnings"]
