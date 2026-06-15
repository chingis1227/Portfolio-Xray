from __future__ import annotations

from pathlib import Path

import pandas as pd


def test_yaml_mtime_cache_returns_copy_and_reloads_on_file_change(tmp_path: Path) -> None:
    from src.yaml_cache import clear_yaml_mtime_cache, load_yaml_mtime_cached

    clear_yaml_mtime_cache()
    path = tmp_path / "sample.yml"
    path.write_text("items:\n  - ticker: SPY\n", encoding="utf-8")

    first = load_yaml_mtime_cached(path)
    first["items"][0]["ticker"] = "MUTATED"
    second = load_yaml_mtime_cached(path)

    assert second["items"][0]["ticker"] == "SPY"

    path.write_text("items:\n  - ticker: QQQX\n", encoding="utf-8")
    third = load_yaml_mtime_cached(path)
    assert third["items"][0]["ticker"] == "QQQX"


def test_fetch_fred_series_memory_cache_returns_copy(monkeypatch) -> None:
    import src.data_fred as data_fred

    data_fred.clear_fred_series_memory_cache()
    calls = {"count": 0}

    def fake_csv(series_id: str, start: str, end: str, *, timeout: float):
        calls["count"] += 1
        return pd.Series([1.0, 2.0], index=pd.to_datetime(["2026-01-01", "2026-01-02"]), name=series_id)

    monkeypatch.setattr(data_fred, "_fred_api_key", lambda api_key=None: None)
    monkeypatch.setattr(data_fred, "_fetch_fred_series_csv", fake_csv)

    first = data_fred.fetch_fred_series("DTB3", "2026-01-01", "2026-01-31", retries=0)
    first.iloc[0] = 99.0
    second = data_fred.fetch_fred_series("DTB3", "2026-01-01", "2026-01-31", retries=0)

    assert calls["count"] == 1
    assert float(second.iloc[0]) == 1.0
    assert second.attrs["source_used"] == "fred_csv_fallback"


def test_fetch_daily_memory_cache_returns_copy(monkeypatch) -> None:
    import src.data_yf as data_yf

    data_yf.clear_fetch_daily_memory_cache()
    calls = {"count": 0}

    def fake_download(*args, **kwargs):
        calls["count"] += 1
        return pd.DataFrame(
            {"Adj Close": [100.0, 101.0]},
            index=pd.to_datetime(["2026-01-01", "2026-01-02"]),
        )

    monkeypatch.setattr(data_yf.yf, "download", fake_download)

    first = data_yf.fetch_daily("SPY", "2026-01-01", "2026-01-31", currency_override="USD")
    first.iloc[0, 0] = 1.0
    second = data_yf.fetch_daily("SPY", "2026-01-01", "2026-01-31", currency_override="USD")

    assert calls["count"] == 1
    assert float(second.iloc[0]["Close"]) == 100.0
    assert second.attrs["currency"] == "USD"


def test_factor_matrix_memory_cache_returns_copy(monkeypatch) -> None:
    import src.stress_factors as stress_factors

    stress_factors.clear_factor_matrix_memory_cache()
    calls = {"count": 0}

    def fake_build(start: str, end: str, *, monthly: bool, require_complete_rows: bool = True):
        calls["count"] += 1
        frame = pd.DataFrame({"equity": [0.01, 0.02]}, index=pd.to_datetime(["2026-01-02", "2026-01-09"]))
        frame.attrs["source"] = "fake"
        return frame

    monkeypatch.setattr(stress_factors, "_build_factor_frame", fake_build)

    first = stress_factors.build_factor_matrix("2026-01-01", "2026-02-01")
    first.iloc[0, 0] = 9.0
    second = stress_factors.build_factor_matrix("2026-01-01", "2026-02-01")

    assert calls["count"] == 1
    assert float(second.iloc[0]["equity"]) == 0.01
    assert second.attrs["source"] == "fake"


def test_review_macro_panel_memory_cache_returns_copy(monkeypatch) -> None:
    import src.candidate_run_context as context
    import src.stress_factors_macro as macro

    context.clear_review_macro_panel_memory_cache()
    calls = {"count": 0}

    def fake_fetch(start: str, end: str):
        calls["count"] += 1
        return pd.DataFrame({"indicator": [1.0]}, index=pd.to_datetime(["2026-01-31"])), {"start": start, "end": end}

    monkeypatch.setattr(macro, "fetch_macro_indicators", fake_fetch)

    first, _meta = context.load_review_macro_panel("2026-05-31")
    first.iloc[0, 0] = 99.0
    second, meta = context.load_review_macro_panel("2026-05-31")

    assert calls["count"] == 1
    assert float(second.iloc[0]["indicator"]) == 1.0
    assert "start" in meta and "end" in meta
