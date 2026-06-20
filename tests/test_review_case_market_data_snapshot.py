from __future__ import annotations

import pytest

from src.review_case import (
    MARKET_DATA_SNAPSHOT_SCHEMA_VERSION,
    ReviewCaseMarketDataSnapshot,
    ReviewCaseMarketDataSnapshotError,
)


def test_market_data_snapshot_projects_demo_run_metadata_basis() -> None:
    snapshot = ReviewCaseMarketDataSnapshot.from_run_metadata(
        {
            "schema_version": "run_metadata_v1",
            "review_id": "frontend_review_demo",
            "mode": "demo_qa",
            "analysis_end": "2026-05-31",
            "analysis_setup": {
                "investor_currency": "USD",
                "analysis_window": "2026-05-31",
                "market_data_provider": "frozen_fixture",
                "provider_status": {
                    "source": "frozen_fixture",
                    "freshness": "fixed_demo_dataset",
                    "message": "Demo / QA mode uses deterministic fixture data.",
                },
            },
        },
        source_refs=("analysis_subject/run_metadata.json",),
    )

    serialized = snapshot.to_dict()

    assert serialized["schema_version"] == MARKET_DATA_SNAPSHOT_SCHEMA_VERSION
    assert serialized["review_id"] == "frontend_review_demo"
    assert serialized["mode"] == "demo_qa"
    assert serialized["analysis_end"] == "2026-05-31"
    assert serialized["market_data_provider"] == "frozen_fixture"
    assert serialized["provider_status"]["source"] == "frozen_fixture"
    assert serialized["source_refs"] == ["analysis_subject/run_metadata.json"]
    assert serialized["evidence_source_ref"].startswith("logical://market-data/")
    assert len(serialized["basis_key"]) == 64


def test_market_data_snapshot_uses_existing_live_provider_and_risk_free_metadata() -> None:
    run_metadata = {
        "schema_version": "run_metadata_v1",
        "review_id": "frontend_review_live",
        "mode": "live",
        "resolved_config": {
            "market_data_provider": "ibkr_yfinance_fallback",
            "investor_currency": "USD",
            "benchmark_base_ticker": "SPY",
            "cash_proxy_ticker": "BIL",
        },
        "analysis_setup": {
            "resolved_assumptions": {
                "analysis_end": "2026-04-30",
                "return_frequency": "monthly",
                "configured_return_frequency": "daily",
                "risk_free_rate": {"source": "FRED:DTB3"},
                "cash_proxy": {"ticker": "BIL"},
                "base_benchmark_ticker": "SPY",
            },
        },
        "derived_assumptions": {
            "risk_free_fallback_used": True,
            "risk_free_fallback_reason": "fred_timeout_cached_rf",
            "risk_free_data_provenance": {
                "risk_free_source_requested": "FRED:DTB3",
                "risk_free_source_used": "approved_cached_risk_free_series",
            },
        },
    }
    data_policy = {
        "risk_free_fallback_used": True,
        "risk_free_fallback_reason": "fred_timeout_cached_rf",
    }
    provider_status = {
        "source": "live_provider",
        "freshness": "pending",
        "message": "Live mode uses the normal market-data provider path.",
    }

    snapshot = ReviewCaseMarketDataSnapshot.from_run_metadata(
        run_metadata,
        provider_status=provider_status,
        data_policy=data_policy,
        source_refs=(
            "analysis_subject/run_metadata.json",
            "analysis_subject/data_policy.json",
        ),
    )
    same_basis_snapshot = ReviewCaseMarketDataSnapshot.from_run_metadata(
        run_metadata,
        provider_status=provider_status,
        data_policy=data_policy,
        source_refs=("analysis_subject/run_metadata.json",),
    )

    serialized = snapshot.to_dict()

    assert serialized["basis_key"] == same_basis_snapshot.basis_key
    assert serialized["market_data_provider"] == "ibkr_yfinance_fallback"
    assert serialized["investor_currency"] == "USD"
    assert serialized["returns_frequency"] == "monthly"
    assert serialized["configured_returns_frequency"] == "daily"
    assert serialized["risk_free"] == {
        "source_requested": "FRED:DTB3",
        "source_used": "approved_cached_risk_free_series",
        "fallback_used": True,
        "fallback_reason": "fred_timeout_cached_rf",
    }
    assert serialized["benchmark"] == {"base_ticker": "SPY"}
    assert serialized["cash_proxy"] == {"ticker": "BIL"}


def test_market_data_snapshot_rejects_unsafe_source_refs() -> None:
    with pytest.raises(ReviewCaseMarketDataSnapshotError):
        ReviewCaseMarketDataSnapshot.from_run_metadata(
            {"analysis_end": "2026-05-31"},
            source_refs=("C:/Users/example/run_metadata.json",),
        )
