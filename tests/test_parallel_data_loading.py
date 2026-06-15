from __future__ import annotations

import threading
import time

import pandas as pd
import pytest


class _OverlapProbe:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.active = 0
        self.max_active = 0
        self.calls: list[str] = []

    def run(self, key: str, *, sleep_seconds: float = 0.03) -> None:
        with self._lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
            self.calls.append(str(key))
        try:
            time.sleep(sleep_seconds)
        finally:
            with self._lock:
                self.active -= 1


def test_yfinance_download_all_overlaps_preserves_order_and_currency(monkeypatch) -> None:
    import src.data_yf as data_yf

    monkeypatch.delenv("PMRI_DISABLE_PARALLEL_DATA_LOAD", raising=False)
    monkeypatch.setenv("PMRI_YF_MAX_WORKERS", "3")
    probe = _OverlapProbe()

    def fake_fetch(ticker: str, start: str, end: str, currency_override: str | None = None) -> pd.DataFrame:
        probe.run(ticker)
        frame = pd.DataFrame(
            {"Close": [float(len(ticker))]},
            index=pd.to_datetime(["2026-01-02"]),
        ).rename_axis("Date")
        frame.attrs["currency"] = currency_override
        return frame

    monkeypatch.setattr(data_yf, "fetch_daily", fake_fetch)

    out = data_yf.download_all(
        ["CCC", "A", "BBBB"],
        "2026-01-01",
        "2026-02-01",
        currency_by_ticker={"A": "EUR"},
    )

    assert list(out.keys()) == ["CCC", "A", "BBBB"]
    assert probe.max_active > 1
    assert out["A"].attrs["currency"] == "EUR"
    assert out["CCC"].attrs["currency"] == "USD"


def test_yfinance_download_all_rollback_mode_is_sequential(monkeypatch) -> None:
    import src.data_yf as data_yf

    monkeypatch.setenv("PMRI_DISABLE_PARALLEL_DATA_LOAD", "1")
    monkeypatch.setenv("PMRI_YF_MAX_WORKERS", "4")
    probe = _OverlapProbe()

    def fake_fetch(ticker: str, *_args, **_kwargs) -> pd.DataFrame:
        probe.run(ticker, sleep_seconds=0.01)
        return pd.DataFrame({"Close": [1.0]}, index=pd.to_datetime(["2026-01-02"]))

    monkeypatch.setattr(data_yf, "fetch_daily", fake_fetch)

    out = data_yf.download_all(["A", "B", "C"], "2026-01-01", "2026-02-01")

    assert list(out.keys()) == ["A", "B", "C"]
    assert probe.max_active == 1
    assert probe.calls == ["A", "B", "C"]


def test_factor_matrix_loaders_overlap_keep_column_order_and_error_semantics(monkeypatch) -> None:
    import src.stress_factors as sf

    monkeypatch.delenv("PMRI_DISABLE_PARALLEL_DATA_LOAD", raising=False)
    monkeypatch.setenv("PMRI_FACTOR_MAX_WORKERS", "3")
    probe = _OverlapProbe()
    index = pd.to_datetime(["2026-01-02", "2026-01-09"])

    def loader_for(column: str):
        def _loader(_start: str, _end: str) -> pd.Series:
            probe.run(column)
            if column == "credit":
                raise RuntimeError("simulated provider error")
            return pd.Series([0.01, 0.02], index=index)

        return _loader

    definitions = tuple(
        sf.FactorDefinition(
            column=column,
            beta_key=f"beta_{column}",
            display_name=column.title(),
            source_label=f"fake:{column}",
            weekly_loader=loader_for(column),
            monthly_loader=loader_for(column),
        )
        for column in ("equity", "credit", "usd")
    )
    monkeypatch.setattr(sf, "FACTOR_DEFINITIONS", definitions)

    out = sf._build_factor_frame("2026-01-01", "2026-02-01", monthly=True, require_complete_rows=False)

    assert list(out.columns) == ["equity", "credit", "usd"]
    assert probe.max_active > 1
    diagnostics = out.attrs["factor_load_diagnostics"]["by_factor"]
    assert diagnostics["credit"]["status"] == "missing"
    assert diagnostics["credit"]["reason"].startswith("RuntimeError:simulated provider error")


def test_factor_matrix_hard_unavailable_error_still_propagates(monkeypatch) -> None:
    import src.stress_factors as sf

    monkeypatch.setenv("PMRI_FACTOR_MAX_WORKERS", "2")

    def hard_fail(_start: str, _end: str) -> pd.Series:
        raise sf.FactorDataUnavailableError("hard factor failure")

    definitions = (
        sf.FactorDefinition(
            column="equity",
            beta_key="beta_equity",
            display_name="Equity",
            source_label="fake:equity",
            weekly_loader=hard_fail,
            monthly_loader=hard_fail,
        ),
    )
    monkeypatch.setattr(sf, "FACTOR_DEFINITIONS", definitions)

    with pytest.raises(sf.FactorDataUnavailableError, match="hard factor failure"):
        sf._build_factor_frame("2026-01-01", "2026-02-01", monthly=False)


def test_macro_indicator_resolution_overlaps_but_preserves_spec_order(monkeypatch) -> None:
    import src.stress_factors_macro as macro

    monkeypatch.delenv("PMRI_DISABLE_PARALLEL_DATA_LOAD", raising=False)
    monkeypatch.setenv("PMRI_MACRO_MAX_WORKERS", "3")
    probe = _OverlapProbe()

    specs = tuple(
        macro.IndicatorSpec(
            key=key,
            block=macro.GROWTH_BLOCK_LABOR,
            axis="growth",
            role="required",
            sign="+",
            frequency="M",
            transform="level_and_three_m_change",
            source_chain=(macro.SourceSpec(kind="fred", locator=key),),
        )
        for key in ("z_indicator", "a_indicator", "m_indicator")
    )

    def resolver(spec, _start: str, _end: str):
        probe.run(spec.key)
        series = pd.Series(
            [1.0, 2.0, 3.0, 4.0],
            index=pd.date_range("2026-01-31", periods=4, freq="ME"),
        )
        return series, {"available": True, "source_used": f"fake:{spec.key}", "frequency_native": "M"}

    panel, meta = macro.fetch_macro_indicators(
        "2026-01-01",
        "2026-05-01",
        indicators=specs,
        resolver=resolver,
    )

    assert list(panel.columns) == [
        "z_indicator__level",
        "z_indicator__momentum",
        "a_indicator__level",
        "a_indicator__momentum",
        "m_indicator__level",
        "m_indicator__momentum",
    ]
    assert probe.max_active > 1
    assert meta["available_indicators"] == ["a_indicator", "m_indicator", "z_indicator"]
    assert list(meta["data_sources_used"].keys()) == ["z_indicator", "a_indicator", "m_indicator"]
