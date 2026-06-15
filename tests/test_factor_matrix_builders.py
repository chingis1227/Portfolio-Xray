"""Factor matrix construction and dynamic analytics output tests."""
from __future__ import annotations

from datetime import datetime, timedelta
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src import stress_factors as sf
from src import data_ecb, data_fred
from scripts.warm_factor_cache import warm_factor_cache
from run_report import (
    _factor_data_metadata_from_diagnostics,
    _merge_factor_data_policy_metadata,
    build_derived_assumptions,
)


def _test_output_dir(name: str) -> Path:
    root = Path.cwd() / "output" / "codex_test_artifacts" / name
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_build_factor_matrix_includes_vix_us_growth_oil_and_shifts_wei_to_friday(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(sf, "CACHE_DIR", tmp_path / "cache")
    daily_idx = pd.date_range("2024-01-01", "2024-01-19", freq="B")
    saturday_idx = pd.to_datetime(["2024-01-06", "2024-01-13", "2024-01-20"])

    daily_close_map = {
        "SPY": pd.Series(np.linspace(100.0, 109.0, len(daily_idx)), index=daily_idx),
        "DBC": pd.Series(np.linspace(20.0, 24.5, len(daily_idx)), index=daily_idx),
    }
    fred_map = {
        sf.FRED_REAL_10Y: pd.Series(np.linspace(1.00, 1.18, len(daily_idx)), index=daily_idx),
        sf.FRED_BREAKEVEN_10Y: pd.Series(np.linspace(2.00, 2.09, len(daily_idx)), index=daily_idx),
        sf.FRED_HY_SPREAD: pd.Series(np.linspace(4.00, 4.18, len(daily_idx)), index=daily_idx),
        sf.FRED_CREDIT_SPREAD_FALLBACK: pd.Series(np.linspace(1.50, 1.68, len(daily_idx)), index=daily_idx),
        sf.FRED_DXY: pd.Series(np.linspace(100.0, 101.8, len(daily_idx)), index=daily_idx),
        sf.FRED_VIX: pd.Series(np.linspace(14.0, 17.6, len(daily_idx)), index=daily_idx),
        sf.FRED_WTI_OIL: pd.Series(np.linspace(70.0, 75.4, len(daily_idx)), index=daily_idx),
        sf.FRED_US_GROWTH: pd.Series([1.0, 1.2, 1.5], index=saturday_idx),
    }

    monkeypatch.setattr(
        sf,
        "fetch_daily",
        lambda ticker, *_args, **_kwargs: pd.DataFrame({"Close": daily_close_map[ticker]}),
    )
    monkeypatch.setattr(sf, "fetch_fred_series", lambda series_id, *_args, **_kwargs: fred_map[series_id].copy())

    out = sf.build_factor_matrix("2024-01-01", "2024-01-20")

    assert list(out.columns) == [
        "equity",
        "real_rates",
        "inflation",
        "credit",
        "usd",
        "commodity",
        "vix",
        "us_growth",
        "oil",
    ]
    assert list(out.index) == [pd.Timestamp("2024-01-12"), pd.Timestamp("2024-01-19")]
    assert np.isclose(out.loc[pd.Timestamp("2024-01-12"), "us_growth"], 0.2)
    assert np.isclose(out.loc[pd.Timestamp("2024-01-19"), "us_growth"], 0.3)
    expected_vix = sf._week_end(fred_map[sf.FRED_VIX]).pct_change().dropna()
    expected_oil = sf._week_end(fred_map[sf.FRED_WTI_OIL]).pct_change().dropna()
    assert np.isclose(out.loc[pd.Timestamp("2024-01-12"), "vix"], expected_vix.loc[pd.Timestamp("2024-01-12")])
    assert np.isclose(out.loc[pd.Timestamp("2024-01-12"), "oil"], expected_oil.loc[pd.Timestamp("2024-01-12")])


def test_credit_factor_falls_back_to_baa10y_when_hy_oas_history_is_short(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(sf, "CACHE_DIR", tmp_path / "cache")
    daily_idx = pd.date_range("2020-01-01", "2024-12-31", freq="B")
    short_credit_idx = pd.date_range("2024-01-01", "2024-12-31", freq="B")

    daily_close_map = {
        "SPY": pd.Series(np.linspace(100.0, 180.0, len(daily_idx)), index=daily_idx),
        "DBC": pd.Series(np.linspace(20.0, 30.0, len(daily_idx)), index=daily_idx),
    }
    fred_map = {
        sf.FRED_REAL_10Y: pd.Series(np.linspace(1.00, 1.60, len(daily_idx)), index=daily_idx),
        sf.FRED_BREAKEVEN_10Y: pd.Series(np.linspace(2.00, 2.25, len(daily_idx)), index=daily_idx),
        sf.FRED_HY_SPREAD: pd.Series(np.linspace(4.00, 4.30, len(short_credit_idx)), index=short_credit_idx),
        sf.FRED_CREDIT_SPREAD_FALLBACK: pd.Series(np.linspace(1.50, 2.10, len(daily_idx)), index=daily_idx),
        sf.FRED_DXY: pd.Series(np.linspace(100.0, 105.0, len(daily_idx)), index=daily_idx),
        sf.FRED_VIX: pd.Series(np.linspace(14.0, 20.0, len(daily_idx)), index=daily_idx),
        sf.FRED_WTI_OIL: pd.Series(np.linspace(70.0, 80.0, len(daily_idx)), index=daily_idx),
        sf.FRED_US_GROWTH: pd.Series(
            np.linspace(1.0, 1.6, len(pd.date_range("2020-01-04", "2024-12-28", freq="W-SAT"))),
            index=pd.date_range("2020-01-04", "2024-12-28", freq="W-SAT"),
        ),
    }

    monkeypatch.setattr(
        sf,
        "fetch_daily",
        lambda ticker, *_args, **_kwargs: pd.DataFrame({"Close": daily_close_map[ticker]}),
    )
    monkeypatch.setattr(sf, "fetch_fred_series", lambda series_id, *_args, **_kwargs: fred_map[series_id].copy())

    out = sf.build_factor_matrix("2020-01-01", "2024-12-31")
    diag = out.attrs["factor_load_diagnostics"]["by_factor"]["credit"]

    assert "credit" in out.columns
    assert diag["status"] == "available"
    assert diag["source"] == f"FRED:{sf.FRED_CREDIT_SPREAD_FALLBACK}"
    assert diag["primary_source"] == f"FRED:{sf.FRED_HY_SPREAD}"
    assert diag["fallback_used"] is True
    assert "insufficient coverage" in diag["fallback_reason"]


def _factor_cache_test_maps(start: str = "2024-01-01", end: str = "2024-01-31"):
    daily_idx = pd.date_range(start, end, freq="B")
    saturday_idx = pd.date_range("2024-01-06", "2024-01-27", freq="W-SAT")
    daily_close_map = {
        "SPY": pd.Series(np.linspace(100.0, 115.0, len(daily_idx)), index=daily_idx),
        "DBC": pd.Series(np.linspace(20.0, 25.0, len(daily_idx)), index=daily_idx),
    }
    fred_map = {
        sf.FRED_REAL_10Y: pd.Series(np.linspace(1.00, 1.30, len(daily_idx)), index=daily_idx),
        sf.FRED_BREAKEVEN_10Y: pd.Series(np.linspace(2.00, 2.15, len(daily_idx)), index=daily_idx),
        sf.FRED_HY_SPREAD: pd.Series(np.linspace(4.00, 4.10, len(daily_idx)), index=daily_idx),
        sf.FRED_CREDIT_SPREAD_FALLBACK: pd.Series(np.linspace(1.50, 1.70, len(daily_idx)), index=daily_idx),
        sf.FRED_DXY: pd.Series(np.linspace(100.0, 102.0, len(daily_idx)), index=daily_idx),
        sf.FRED_VIX: pd.Series(np.linspace(14.0, 18.0, len(daily_idx)), index=daily_idx),
        sf.FRED_WTI_OIL: pd.Series(np.linspace(70.0, 76.0, len(daily_idx)), index=daily_idx),
        sf.FRED_US_GROWTH: pd.Series(np.linspace(1.0, 1.4, len(saturday_idx)), index=saturday_idx),
    }
    return daily_close_map, fred_map


def test_fred_real_rates_timeout_with_valid_factor_cache_succeeds_with_warning(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(sf, "CACHE_DIR", tmp_path / "cache")
    daily_close_map, fred_map = _factor_cache_test_maps()
    sf._save_fred_factor_series_cache(sf.FRED_REAL_10Y, fred_map[sf.FRED_REAL_10Y])

    monkeypatch.setattr(
        sf,
        "fetch_daily",
        lambda ticker, *_args, **_kwargs: pd.DataFrame({"Close": daily_close_map[ticker]}),
    )

    def fake_fred(series_id, *_args, **_kwargs):
        if series_id == sf.FRED_REAL_10Y:
            raise TimeoutError("simulated DFII10 timeout")
        return fred_map[series_id].copy()

    monkeypatch.setattr(sf, "fetch_fred_series", fake_fred)

    out = sf.build_factor_matrix("2024-01-01", "2024-01-31")
    diag = out.attrs["factor_load_diagnostics"]
    real_rates = diag["by_factor"]["real_rates"]

    assert not out.empty
    assert "real_rates" in out.columns
    assert "equity" in out.columns
    assert real_rates["source_used"] == "cache_hit"
    assert real_rates["cache_status"] == "valid"
    assert real_rates["factor_data_fallback_used"] is False
    assert real_rates["factor_data_cache_key"] == sf.FRED_REAL_10Y
    assert "cache_hit" in diag["source_used"]


def test_fred_timeout_without_valid_factor_cache_fails_clearly(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(sf, "CACHE_DIR", tmp_path / "cache")
    daily_close_map, fred_map = _factor_cache_test_maps()
    monkeypatch.setattr(
        sf,
        "fetch_daily",
        lambda ticker, *_args, **_kwargs: pd.DataFrame({"Close": daily_close_map[ticker]}),
    )

    def fake_fred(series_id, *_args, **_kwargs):
        if series_id == sf.FRED_REAL_10Y:
            raise TimeoutError("simulated DFII10 timeout")
        return fred_map[series_id].copy()

    monkeypatch.setattr(sf, "fetch_fred_series", fake_fred)

    with pytest.raises(sf.FactorDataUnavailableError, match="DFII10.*no valid approved factor cache"):
        sf.build_factor_matrix("2024-01-01", "2024-01-31")


def test_factor_cache_validity_rejects_expired_short_bad_frequency_and_partial_cache(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(sf, "CACHE_DIR", tmp_path / "cache")
    _daily_close_map, fred_map = _factor_cache_test_maps()

    sf._save_fred_factor_series_cache(sf.FRED_REAL_10Y, fred_map[sf.FRED_REAL_10Y])
    cache_path = sf._factor_cache_path(sf.FRED_REAL_10Y)
    meta_path = cache_path / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["created_at"] = (datetime.now() - timedelta(days=sf.FACTOR_CACHE_MAX_AGE_DAYS + 2)).isoformat()
    meta_path.write_text(json.dumps(meta), encoding="utf-8")
    with pytest.raises(sf.FactorCacheValidationError, match="expired"):
        sf._load_approved_cached_fred_factor_series(sf.FRED_REAL_10Y, "2024-01-01", "2024-01-31")

    shutil.rmtree(cache_path, ignore_errors=True)
    sf._save_fred_factor_series_cache(sf.FRED_REAL_10Y, fred_map[sf.FRED_REAL_10Y].loc["2024-01-10":])
    with pytest.raises(sf.FactorCacheValidationError, match="does not cover requested range"):
        sf._load_approved_cached_fred_factor_series(sf.FRED_REAL_10Y, "2024-01-01", "2024-01-31")

    sf._save_fred_factor_series_cache(sf.FRED_REAL_10Y, fred_map[sf.FRED_REAL_10Y])
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["config"]["supported_frequency_alignment"] = ["daily_raw"]
    meta_path.write_text(json.dumps(meta), encoding="utf-8")
    with pytest.raises(sf.FactorCacheValidationError, match="frequency alignment"):
        sf._load_approved_cached_fred_factor_series(sf.FRED_REAL_10Y, "2024-01-01", "2024-01-31")

    # Partial cache is not fake success: DFII10 is cached, but a second timed-out
    # required FRED factor without cache still fails and names that missing series.
    sf._save_fred_factor_series_cache(sf.FRED_REAL_10Y, fred_map[sf.FRED_REAL_10Y])
    daily_close_map, fred_map = _factor_cache_test_maps()
    monkeypatch.setattr(
        sf,
        "fetch_daily",
        lambda ticker, *_args, **_kwargs: pd.DataFrame({"Close": daily_close_map[ticker]}),
    )

    def fake_fred(series_id, *_args, **_kwargs):
        if series_id in {sf.FRED_REAL_10Y, sf.FRED_BREAKEVEN_10Y}:
            raise TimeoutError(f"simulated {series_id} timeout")
        return fred_map[series_id].copy()

    monkeypatch.setattr(sf, "fetch_fred_series", fake_fred)
    with pytest.raises(sf.FactorDataUnavailableError, match=sf.FRED_BREAKEVEN_10Y):
        sf.build_factor_matrix("2024-01-01", "2024-01-31")


def test_fred_fetch_timeout_retry_is_bounded(monkeypatch) -> None:
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    calls = {"urlopen": 0, "sleep": 0}

    def fake_urlopen(*_args, **_kwargs):
        calls["urlopen"] += 1
        raise TimeoutError("simulated urlopen timeout")

    def fake_sleep(_seconds):
        calls["sleep"] += 1

    monkeypatch.setattr(data_fred, "urlopen", fake_urlopen)
    monkeypatch.setattr(data_fred.time, "sleep", fake_sleep)

    with pytest.raises(RuntimeError, match="timed out"):
        data_fred.fetch_fred_series(
            "DFII10",
            "2024-01-01",
            "2024-01-31",
            timeout=0.01,
            retries=2,
            retry_sleep=0.0,
        )
    assert calls == {"urlopen": 3, "sleep": 2}


def test_fred_api_key_is_primary_when_configured(monkeypatch) -> None:
    captured: dict[str, str] = {}
    monkeypatch.setenv("FRED_API_KEY", "unit-test-key")

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return (
                b'{"observations":[{"date":"2024-01-05","value":"1.25"},'
                b'{"date":"2024-01-08","value":"1.30"}]}'
            )

    def fake_urlopen(url, **_kwargs):
        captured["url"] = str(url)
        return _Response()

    monkeypatch.setattr(data_fred, "urlopen", fake_urlopen)

    out = data_fred.fetch_fred_series("DFII10", "2024-01-01", "2024-01-31", retries=0)

    assert not out.empty
    assert data_fred.FRED_API_OBSERVATIONS_URL in captured["url"]
    assert captured["url"].startswith(f"{data_fred.FRED_API_OBSERVATIONS_URL}?")
    assert f"{data_fred.FRED_API_OBSERVATIONS_URL}..." not in captured["url"]
    assert "api_key=unit-test-key" in captured["url"]
    assert "observation_start=2024-01-01" in captured["url"]
    assert out.attrs["source_used"] == "fred_api"


def test_fred_csv_fallback_is_disclosed_when_api_key_missing(monkeypatch) -> None:
    captured: dict[str, str] = {}
    monkeypatch.delenv("FRED_API_KEY", raising=False)

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b"observation_date,DFII10\n2024-01-05,1.25\n"

    def fake_urlopen(url, **_kwargs):
        captured["url"] = str(url)
        return _Response()

    monkeypatch.setattr(data_fred, "urlopen", fake_urlopen)

    out = data_fred.fetch_fred_series("DFII10", "2024-01-01", "2024-01-31", retries=0)

    assert not out.empty
    assert data_fred.FRED_CSV_GRAPH_URL in captured["url"]
    assert captured["url"].startswith(f"{data_fred.FRED_CSV_GRAPH_URL}?")
    assert f"{data_fred.FRED_CSV_GRAPH_URL}..." not in captured["url"]
    assert out.attrs["source_used"] == "fred_csv_fallback"
    assert "fred_api_key_missing_csv_fallback" in out.attrs["warnings"]


def test_fred_csv_fallback_is_disclosed_when_api_fails(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setenv("FRED_API_KEY", "unit-test-key")

    class _CsvResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b"observation_date,DFII10\n2024-01-05,1.25\n"

    def fake_urlopen(url, **_kwargs):
        url = str(url)
        calls.append(url)
        if data_fred.FRED_API_OBSERVATIONS_URL in url:
            raise TimeoutError("simulated api timeout")
        return _CsvResponse()

    monkeypatch.setattr(data_fred, "urlopen", fake_urlopen)
    monkeypatch.setattr(data_fred.time, "sleep", lambda _seconds: None)

    out = data_fred.fetch_fred_series("DFII10", "2024-01-01", "2024-01-31", retries=0)

    assert len(calls) == 2
    assert data_fred.FRED_API_OBSERVATIONS_URL in calls[0]
    assert data_fred.FRED_CSV_GRAPH_URL in calls[1]
    assert out.attrs["source_used"] == "fred_csv_fallback"
    assert any(w.startswith("fred_api_failed_csv_fallback:") for w in out.attrs["warnings"])


def test_factor_cache_hit_does_not_call_live_fred(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(sf, "CACHE_DIR", tmp_path / "cache")
    _daily_close_map, fred_map = _factor_cache_test_maps()
    sf._save_fred_factor_series_cache(sf.FRED_REAL_10Y, fred_map[sf.FRED_REAL_10Y])

    def boom(*_args, **_kwargs):
        raise AssertionError("live FRED should not be called on approved cache hit")

    monkeypatch.setattr(sf, "fetch_fred_series", boom)

    out = sf._fetch_fred_factor_series(sf.FRED_REAL_10Y, "2024-01-01", "2024-01-31")

    assert not out.empty
    assert out.attrs["source_used"] == "cache_hit"
    assert out.attrs["cache_status"] == "valid"


def test_factor_series_live_fetch_uses_demo_safe_bounded_fred_budget(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(sf, "CACHE_DIR", tmp_path / "cache")
    captured: dict[str, object] = {}

    def fake_fetch(series_id, start, end, **kwargs):
        captured.update(
            {
                "series_id": series_id,
                "start": start,
                "end": end,
                **kwargs,
            }
        )
        raise TimeoutError("simulated bounded factor timeout")

    monkeypatch.setattr(sf, "fetch_fred_series", fake_fetch)

    with pytest.raises(sf.FactorDataUnavailableError, match="DFII10.*no valid approved factor cache"):
        sf._fetch_fred_factor_series(sf.FRED_REAL_10Y, "2024-01-01", "2024-01-31")

    assert captured["timeout"] == sf.FRED_FACTOR_FETCH_TIMEOUT_SECONDS
    assert captured["retries"] == sf.FRED_FACTOR_FETCH_RETRIES
    assert captured["retry_sleep"] == sf.FRED_FACTOR_FETCH_RETRY_SLEEP_SECONDS


def test_fred_csv_fetch_pushes_requested_date_range_into_url(monkeypatch) -> None:
    captured: dict[str, str] = {}
    monkeypatch.delenv("FRED_API_KEY", raising=False)

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b"observation_date,DFII10\n2024-01-05,1.25\n"

    def fake_urlopen(url, **_kwargs):
        captured["url"] = str(url)
        return _Response()

    monkeypatch.setattr(data_fred, "urlopen", fake_urlopen)

    out = data_fred.fetch_fred_series(
        "DFII10",
        "2024-01-01",
        "2024-01-31",
        timeout=0.01,
        retries=0,
    )

    assert not out.empty
    assert captured["url"].startswith(f"{data_fred.FRED_CSV_GRAPH_URL}?")
    assert f"{data_fred.FRED_CSV_GRAPH_URL}..." not in captured["url"]
    assert "id=DFII10" in captured["url"]
    assert "cosd=2024-01-01" in captured["url"]
    assert "coed=2024-01-31" in captured["url"]


def test_ecb_estr_fetch_pushes_requested_date_range_into_url(monkeypatch) -> None:
    captured: dict[str, str] = {}

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b'[{"date":"2024-01-05","value":"3.90"}]'

    def fake_urlopen(req, **_kwargs):
        captured["url"] = str(req.full_url)
        return _Response()

    monkeypatch.setattr(data_ecb.urllib.request, "urlopen", fake_urlopen)

    out = data_ecb.fetch_estr("2024-01-01", "2024-01-31")

    assert not out.empty
    assert captured["url"].startswith(f"{data_ecb.ESTR_API}?")
    assert f"{data_ecb.ESTR_API}..." not in captured["url"]
    assert "from=2024-01-01" in captured["url"]
    assert "to=2024-01-31" in captured["url"]


def test_warm_factor_cache_check_only_reports_not_ready_for_partial_cache(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(sf, "CACHE_DIR", tmp_path / "cache")
    _daily_close_map, fred_map = _factor_cache_test_maps()
    sf._save_fred_factor_series_cache(sf.FRED_REAL_10Y, fred_map[sf.FRED_REAL_10Y])

    summary = warm_factor_cache(
        start="2024-01-01",
        end="2024-01-31",
        series_ids=[sf.FRED_REAL_10Y, sf.FRED_BREAKEVEN_10Y],
        check_only=True,
    )

    assert summary["status"] == "failed"
    assert summary["cache_status"] == "partial"
    assert summary["full_factor_matrix_available"] is False
    assert summary["demo_safe"] is False
    assert summary["missing_series"] == [sf.FRED_BREAKEVEN_10Y]


def test_cached_factor_data_provenance_is_written_to_metadata_and_data_policy(tmp_path) -> None:
    factor_diag = {
        "factor_load_diagnostics": {
            "factor_data_fallback_used": True,
            "factor_data_fallback_reason": sf.FACTOR_DATA_FALLBACK_REASON_FRED_TIMEOUT_CACHED_FACTOR_DATA,
            "factor_data_source_used": "approved_cached_factor_series",
            "factor_data_provenance": {
                "real_rates": {"factor_data_cache_key": sf.FRED_REAL_10Y}
            },
            "cache_validity_policy": sf.factor_cache_validity_policy(),
            "warnings": [sf.FACTOR_DATA_FALLBACK_WARNING_CODE, sf.FACTOR_DATA_FALLBACK_WARNING],
        }
    }
    metadata, warnings = _factor_data_metadata_from_diagnostics(factor_diag)

    class _Cfg:
        weights = {"AAA": 1.0}
        min_acceptable_return = None
        liquidity_need_months = 0
        monthly_expenses = 0

    derived = build_derived_assumptions(
        _Cfg(),
        "BIL",
        "FRED:DTB3",
        {},
        "2024-01-31",
        [120],
        factor_data_metadata=metadata,
        factor_data_warnings=warnings,
    )
    assert derived["factor_data_fallback_used"] is True
    assert derived["factor_data_fallback_reason"] == sf.FACTOR_DATA_FALLBACK_REASON_FRED_TIMEOUT_CACHED_FACTOR_DATA
    assert derived["factor_data_provenance"]["factor_data_provenance"]["real_rates"]["factor_data_cache_key"] == sf.FRED_REAL_10Y

    policy_path = tmp_path / "data_policy.json"
    policy_path.write_text(json.dumps({"warnings": []}), encoding="utf-8")
    _merge_factor_data_policy_metadata(
        tmp_path,
        factor_data_metadata=metadata,
        factor_data_warnings=warnings,
    )
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    assert policy["factor_data_fallback_used"] is True
    assert policy["factor_data_provenance"]["factor_data_source_used"] == "approved_cached_factor_series"
    assert sf.FACTOR_DATA_FALLBACK_WARNING_CODE in policy["warnings"]


def test_base_factor_contract_excludes_oil_but_extended_registry_keeps_it() -> None:
    assert sf.BASE_FACTOR_COLUMN_ORDER == (
        "equity",
        "real_rates",
        "inflation",
        "credit",
        "usd",
        "commodity",
        "vix",
        "us_growth",
    )
    assert sf.BASE_BETA_ROW_ORDER == (
        "beta_eq",
        "beta_rr",
        "beta_inf",
        "beta_credit",
        "beta_usd",
        "beta_cmd",
        "beta_vix",
        "beta_us_growth",
    )
    assert "oil" not in sf.BASE_FACTOR_COLUMN_ORDER
    assert "beta_oil" not in sf.BASE_BETA_ROW_ORDER
    assert sf.FACTOR_COLUMN_ORDER[-1] == "oil"
    assert sf.BETA_ROW_ORDER[-1] == "beta_oil"


def test_portfolio_factor_regression_weekly_uses_base_by_default_and_extended_when_requested(monkeypatch) -> None:
    idx = pd.date_range("2024-01-05", periods=30, freq="W-FRI")
    rng = np.random.default_rng(123)
    factors = pd.DataFrame(
        rng.normal(scale=0.05, size=(len(idx), len(sf.FACTOR_COLUMN_ORDER))),
        index=idx,
        columns=list(sf.FACTOR_COLUMN_ORDER),
    )
    y = (
        0.4 * factors["equity"]
        - 0.3 * factors["credit"]
        + 0.2 * factors["vix"]
        + 0.1 * factors["us_growth"]
        - 0.15 * factors["oil"]
        + rng.normal(scale=0.01, size=len(idx))
    )
    asset_weekly = pd.DataFrame({"AAA": y}, index=idx)

    monkeypatch.setattr(sf, "asset_weekly_returns_from_daily", lambda *_args, **_kwargs: asset_weekly.copy())
    monkeypatch.setattr(sf, "build_factor_matrix", lambda *_args, **_kwargs: factors.copy())

    import src.data_yf as data_yf

    monkeypatch.setattr(
        data_yf,
        "download_all",
        lambda *_args, **_kwargs: {"AAA": pd.DataFrame({"Close": [1.0, 2.0]}, index=pd.to_datetime(["2024-01-01", "2024-01-02"]))},
    )

    out = sf.portfolio_factor_regression_weekly(
        weights={"AAA": 1.0},
        tickers=["AAA"],
        analysis_end_str="2024-08-30",
        window_weeks=30,
    )

    expected_beta_keys = [sf.FACTOR_TO_BETA_KEY[col] for col in sf.BASE_FACTOR_COLUMN_ORDER]
    assert list(out["betas"].keys()) == expected_beta_keys
    assert "beta_vix" in out["betas"]
    assert "beta_us_growth" in out["betas"]
    assert "beta_oil" not in out["betas"]
    assert np.isclose(out["idiosyncratic_risk"], 1.0 - out["r2"])
    assert len(out["hac_inference"]["t"]) == len(expected_beta_keys) + 1

    extended = sf.portfolio_factor_regression_weekly(
        weights={"AAA": 1.0},
        tickers=["AAA"],
        analysis_end_str="2024-08-30",
        window_weeks=30,
        factor_columns=sf.FACTOR_COLUMN_ORDER,
    )
    extended_beta_keys = [sf.FACTOR_TO_BETA_KEY[col] for col in sf.FACTOR_COLUMN_ORDER]
    assert list(extended["betas"].keys()) == extended_beta_keys
    assert "beta_oil" in extended["betas"]


def test_compute_portfolio_rolling_factor_betas_monthly_outputs_windows(monkeypatch) -> None:
    idx = pd.date_range("2010-01-31", periods=150, freq="ME")
    rng = np.random.default_rng(456)
    factors = pd.DataFrame(
        rng.normal(scale=0.03, size=(len(idx), len(sf.FACTOR_COLUMN_ORDER))),
        index=idx,
        columns=list(sf.FACTOR_COLUMN_ORDER),
    )
    y = (
        0.5 * factors["equity"]
        - 0.2 * factors["credit"]
        + 0.1 * factors["oil"]
        + rng.normal(scale=0.01, size=len(idx))
    )
    monthly_returns = pd.DataFrame({"AAA": y}, index=idx)

    monkeypatch.setattr(sf, "build_factor_matrix_monthly", lambda *_args, **_kwargs: factors.copy())

    out = sf.compute_portfolio_rolling_factor_betas_monthly(
        monthly_returns=monthly_returns,
        weights={"AAA": 1.0},
        analysis_end_str="2022-06-30",
        rolling_windows_months={"3y": sf.FACTOR_MONTHS_3Y, "5y": sf.FACTOR_MONTHS_5Y, "10y": sf.FACTOR_MONTHS_10Y},
    )

    assert set(out) == {"3y", "5y", "10y"}
    assert "beta_eq" in out["3y"].columns
    assert "beta_oil" not in out["5y"].columns
    assert not out["10y"].empty

    extended = sf.compute_portfolio_rolling_factor_betas_monthly(
        monthly_returns=monthly_returns,
        weights={"AAA": 1.0},
        analysis_end_str="2022-06-30",
        rolling_windows_months={"5y": sf.FACTOR_MONTHS_5Y},
        factor_columns=sf.FACTOR_COLUMN_ORDER,
    )
    assert "beta_oil" in extended["5y"].columns


def test_write_rolling_betas_plot_pngs_handles_nine_factors() -> None:
    idx = pd.date_range("2024-01-05", periods=15, freq="W-FRI")
    rolling_df = pd.DataFrame(
        {
            beta_key: np.linspace(-0.2 + i * 0.05, 0.2 + i * 0.05, len(idx))
            for i, beta_key in enumerate(sf.BETA_ROW_ORDER)
        },
        index=idx,
    )
    out_dir = _test_output_dir("factor_png")
    try:
        out = sf.write_rolling_betas_plot_pngs({"3y": rolling_df}, out_dir)
        assert out["3y"] == "rolling_factor_betas_3y.png"
        assert (out_dir / out["3y"]).is_file()
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)
