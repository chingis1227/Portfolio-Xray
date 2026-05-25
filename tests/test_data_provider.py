from __future__ import annotations

import pandas as pd

from src import data_provider


def _frame(value: float = 100.0) -> pd.DataFrame:
    return pd.DataFrame({"Close": [value]}, index=pd.to_datetime(["2026-05-22"])).rename_axis("Date")


def test_download_all_prices_uses_yfinance_provider(monkeypatch):
    monkeypatch.setattr(data_provider, "_download_all_yfinance", lambda tickers, start, end, cur: {"SPY": _frame()})

    result = data_provider.download_all_prices(["SPY"], "2026-05-01", "2026-05-22", provider="yfinance")

    assert list(result.prices) == ["SPY"]
    assert result.provider_by_ticker == {"SPY": "yfinance"}


def test_download_all_prices_falls_back_per_missing_ibkr_ticker(monkeypatch):
    def fake_import(name, *args, **kwargs):
        if name == "src.data_ibkr":
            class FakeIbkrModule:
                @staticmethod
                def download_all(tickers, start, end, currency_by_ticker):
                    return {"SPY": _frame(101.0), "QQQ": pd.DataFrame(columns=["Close"]).rename_axis("Date")}

            return FakeIbkrModule
        return real_import(name, *args, **kwargs)

    real_import = __import__
    monkeypatch.setattr("builtins.__import__", fake_import)
    monkeypatch.setattr(data_provider, "_download_all_yfinance", lambda tickers, start, end, cur: {"QQQ": _frame(202.0)})

    result = data_provider.download_all_prices(
        ["SPY", "QQQ"],
        "2026-05-01",
        "2026-05-22",
        provider="ibkr_yfinance_fallback",
    )

    assert result.prices["SPY"]["Close"].iloc[-1] == 101.0
    assert result.prices["QQQ"]["Close"].iloc[-1] == 202.0
    assert result.provider_by_ticker == {"SPY": "ibkr", "QQQ": "yfinance_fallback"}
