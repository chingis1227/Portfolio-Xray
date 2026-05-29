from __future__ import annotations

import copy

from src.block_2_4_hidden_exposure import (
    ALERT_IDS,
    ALERT_RULES,
    BLOCK_2_4_ID,
    BLOCKED_UPSTREAM_FIELDS,
    CONFIRMATION_STATUSES,
    EVIDENCE_DIRECTIONS,
    EVIDENCE_SOURCES,
    MAX_CONTRIBUTING_ASSETS,
    LEGACY_PCA_RAW_SECTION,
    build_block_2_4_hidden_exposure,
    build_block_2_4_legacy_enrichment,
    build_block_2_4_stress_enrichment,
)
from src.hedge_gap_analysis_block import build_hedge_gap_analysis_v1
from src.portfolio_xray import build_portfolio_xray_v2
from src.stress_results_block import build_stress_results_v1


def _block_2_1() -> dict:
    return {
        "block": "2.1_asset_allocation",
        "capital_allocation_breakdown": {
            "by_asset_class": [
                {"name": "equity", "weight_pct": 45.0},
                {"name": "fixed_income", "weight_pct": 40.0},
            ],
            "by_main_risk_factor": [
                {"name": "equity", "weight_pct": 45.0},
                {"name": "real_rates", "weight_pct": 40.0},
            ],
            "by_risk_role": [
                {"name": "risk_on", "weight_pct": 45.0},
                {"name": "defensive", "weight_pct": 40.0},
            ],
            "by_region": [{"name": "US", "weight_pct": 90.0}],
            "by_currency": [{"name": "USD", "weight_pct": 100.0}],
            "by_asset": [
                {"name": "SPY", "weight_pct": 45.0},
                {"name": "BND", "weight_pct": 40.0},
                {"name": "HYG", "weight_pct": 15.0},
            ],
        },
        "concentration_flags": [
            {
                "flag_id": "single_region_dominance",
                "severity": "high",
                "metric": "region_weight",
                "dimension": "region",
                "label": "US",
                "threshold": 0.85,
                "observed": 0.9,
                "message": "US region concentration is high.",
            },
            {
                "flag_id": "single_currency_dominance",
                "severity": "high",
                "metric": "currency_exposure_weight",
                "dimension": "currency_exposure",
                "label": "USD",
                "threshold": 0.85,
                "observed": 1.0,
                "message": "USD currency exposure concentration is high.",
            },
        ],
        "duplicate_exposure_flags": [
            {
                "duplicate_group_id": "us_large_cap_blend",
                "tickers": ["SPY", "VOO"],
                "combined_weight": 0.12,
                "combined_weight_pct": 12.0,
                "canonical_ticker": "SPY",
                "severity": "medium",
            }
        ],
    }


def _block_2_2() -> dict:
    return {
        "block": "2.2_portfolio_metrics",
        "investor_currency": "USD",
        "return_risk_metrics": {"skewness": -0.7, "kurtosis": 5.0},
        "drawdown_diagnostics": {
            "max_drawdown": -0.22,
            "recovered": False,
            "recovery_months": 18.0,
            "pct_time_underwater": 0.35,
            "longest_underwater": 14,
            "count_drawdowns_gt_5": 3,
            "count_drawdowns_gt_10": 2,
            "count_drawdowns_gt_20": 1,
        },
        "tail_risk_diagnostics": {
            "es_95": -0.02,
            "es_99": -0.03,
            "var_95": -0.018,
            "var_99": -0.028,
            "eee_10": -0.035,
            "downside_deviation": 0.09,
        },
        "metadata": {"vol_of_vol": 0.18, "rel_vol_of_vol": 1.2},
        "rolling_diagnostics": {
            "core_view": {
                "rolling_beta_or_correlation": {
                    "available": True,
                    "latest_correlation": 0.78,
                },
                "rolling_volatility_12m": {
                    "available": True,
                    "latest": 0.14,
                    "series_ref": "rolling_vol_12m_10y.csv",
                },
            }
        },
        "benchmark_dependence": {
            "beta_portfolio": 0.8,
            "downside_beta": 1.0,
            "corr_base": 0.78,
        },
        "correlation_breakdown": {
            "top3_highest_correlation_pairs": [
                {"ticker_a": "SPY", "ticker_b": "SCHD", "correlation": 0.82}
            ]
        },
    }


def _taxonomy() -> dict:
    return {
        "SPY": {
            "asset_class": "equity",
            "main_risk_factor": "equity",
            "risk_role": ["risk_on"],
        },
        "BND": {
            "asset_class": "fixed_income",
            "main_risk_factor": "real_rates",
            "risk_role": ["defensive"],
        },
        "HYG": {
            "asset_class": "fixed_income",
            "main_risk_factor": "credit",
            "risk_role": ["carry"],
        },
    }


def _block_2_3() -> dict:
    return {
        "block": "2.3_factor_exposure",
        "factor_beta_snapshot": {
            "beta_eq": 0.5,
            "beta_rr": 0.4,
            "beta_credit": 0.35,
        },
        "factor_significance_confidence": {
            "beta_eq": {"status": "significant"},
            "beta_rr": {"status": "weak_evidence"},
            "beta_credit": {"status": "weak_evidence"},
        },
    }


def _block_2_3_rich() -> dict:
    return {
        **_block_2_3(),
        "factor_beta_snapshot": {
            "beta_eq": 0.5,
            "beta_rr": 0.4,
            "beta_inf": 0.42,
            "beta_credit": 0.35,
            "beta_usd": 0.28,
            "beta_cmd": 0.31,
            "beta_vix": 0.55,
            "beta_us_growth": 0.38,
        },
        "factor_significance_confidence": {
            "beta_eq": {"status": "significant"},
            "beta_rr": {"status": "weak_evidence"},
            "beta_inf": {"status": "significant"},
            "beta_credit": {"status": "weak_evidence"},
            "beta_usd": {"status": "weak_evidence"},
            "beta_cmd": {"status": "unstable_low_confidence"},
            "beta_vix": {"status": "significant"},
            "beta_us_growth": {"status": "weak_evidence"},
        },
        "factor_variance_contribution": {
            "status": "available",
            "r_squared": 0.72,
            "contributions": {
                "equity": 0.35,
                "real_rates": 0.25,
                "inflation": 0.15,
                "credit": 0.1,
                "USD": 0.05,
                "commodity": 0.05,
                "VIX_volatility": 0.05,
                "us_growth": 0.0,
            },
        },
        "factor_risk_ranking": [
            {
                "rank": 1,
                "factor": "equity",
                "beta_name": "beta_eq",
                "beta": 0.5,
                "contribution": 0.35,
                "confidence": "significant",
                "ranking_metric": "variance_contribution",
                "ranking_score": 0.35,
                "interpretation": "Equity factor dominates variance share.",
            }
        ],
        "factor_beta_stability": {
            "beta_eq": {"beta_stability_label": "stable", "windows_available": 3},
            "beta_rr": {"beta_stability_label": "moderately_changed", "windows_available": 3},
            "beta_inf": {"beta_stability_label": "unstable", "windows_available": 2},
            "beta_vix": {"beta_stability_label": "stable", "windows_available": 3},
        },
        "kalman_current_beta": {
            "available": True,
            "betas": {
                "beta_eq": 0.48,
                "beta_rr": 0.37,
                "beta_usd": 0.22,
                "beta_cmd": 0.29,
                "beta_vix": 0.52,
            },
        },
    }


def _assert_evidence_schema(item: dict) -> None:
    assert set(item) == {"metric", "value", "threshold", "direction", "source", "interpretation"}
    assert item["direction"] in EVIDENCE_DIRECTIONS
    assert item["source"] in EVIDENCE_SOURCES
    assert isinstance(item["metric"], str) and item["metric"]
    assert isinstance(item["interpretation"], str) and item["interpretation"]


def test_block_2_4_contract_and_structured_evidence() -> None:
    block = build_block_2_4_hidden_exposure(
        _block_2_1(),
        _block_2_2(),
        _block_2_3(),
        taxonomy_rows=_taxonomy(),
    )

    assert block["block"] == BLOCK_2_4_ID
    assert block["status"] in {"ok", "partial", "unavailable"}
    assert tuple(block["alerts"]) == ALERT_IDS
    assert block["diagnostics_meta"]["threshold_policy"] == "heuristic_v2"
    assert block["diagnostics_meta"]["confidence_model"] == "v2"
    assert block["diagnostics_meta"]["ruleset"] == "heuristic_v2"
    assert block["diagnostics_meta"]["does_not_optimize"] is True
    assert block["diagnostics_meta"]["does_not_generate_candidates"] is True
    assert block["diagnostics_meta"]["does_not_run_stress_lab"] is True
    blocked = block["diagnostics_meta"]["blocked_upstream_fields"]
    assert isinstance(blocked, list) and len(blocked) == len(BLOCKED_UPSTREAM_FIELDS)
    for row in blocked:
        assert {"field", "reason", "owner_block", "target_session"} <= set(row)

    for alert in block["alerts"].values():
        assert {
            "status",
            "score",
            "evidence",
            "explanation",
            "why_it_matters",
            "next_tests",
            "confidence",
            "confidence_reason",
            "confirmation_status",
            "limitations",
            "contributing_assets",
            "data_quality_warnings",
            "insufficient_evidence_reasons",
            "calculation_notes",
        } <= set(alert)
        assert isinstance(alert["limitations"], list)
        assert isinstance(alert["contributing_assets"], list)
        assert len(alert["contributing_assets"]) <= MAX_CONTRIBUTING_ASSETS
        assert alert["confidence_reason"] is None or isinstance(alert["confidence_reason"], str)
        assert alert["confirmation_status"] in CONFIRMATION_STATUSES
        for asset in alert["contributing_assets"]:
            assert set(asset) == {
                "ticker",
                "weight_pct",
                "expected_role",
                "behavior_flag",
                "source",
            }
            assert asset["source"] == "block_2_1"
        assert any("Per-asset factor betas are not computed" in lim for lim in alert["limitations"])
        assert alert["status"] in {"Low", "Medium", "High", "Unavailable"}
        for item in alert["evidence"]:
            _assert_evidence_schema(item)


def test_block_2_4_missing_data_returns_unavailable_or_low_confidence() -> None:
    block = build_block_2_4_hidden_exposure(None, None, None)

    assert block["status"] == "unavailable"
    for alert in block["alerts"].values():
        assert alert["status"] == "Unavailable"
        assert alert["score"] is None
        assert alert["confidence"] == "unavailable"
        assert alert["insufficient_evidence_reasons"]


def test_block_2_4_status_boundaries() -> None:
    low = build_block_2_4_hidden_exposure(
        _block_2_1(),
        {
            **_block_2_2(),
            "benchmark_dependence": {"beta_portfolio": 0.0, "downside_beta": 0.0},
            "rolling_diagnostics": {"core_view": {"rolling_beta_or_correlation": {"latest_correlation": 0.0}}},
        },
        {"factor_beta_snapshot": {"beta_eq": 0.0}, "factor_significance_confidence": {}},
    )["alerts"]["hidden_equity_beta"]
    assert low["status"] == "Low"
    assert 0 <= low["score"] <= 39

    medium = build_block_2_4_hidden_exposure(
        _block_2_1(),
        {
            **_block_2_2(),
            "benchmark_dependence": {"beta_portfolio": 0.70, "downside_beta": 0.90},
            "rolling_diagnostics": {"core_view": {"rolling_beta_or_correlation": {"latest_correlation": 0.70}}},
        },
        {"factor_beta_snapshot": {"beta_eq": 0.35}, "factor_significance_confidence": {}},
    )["alerts"]["hidden_equity_beta"]
    assert medium["status"] == "Medium"
    assert 40 <= medium["score"] <= 69

    high = build_block_2_4_hidden_exposure(
        _block_2_1(),
        {
            **_block_2_2(),
            "benchmark_dependence": {"beta_portfolio": 1.0, "downside_beta": 1.2},
            "rolling_diagnostics": {"core_view": {"rolling_beta_or_correlation": {"latest_correlation": 0.85}}},
        },
        {"factor_beta_snapshot": {"beta_eq": 0.65}, "factor_significance_confidence": {}},
    )["alerts"]["hidden_equity_beta"]
    assert high["status"] == "High"
    assert 70 <= high["score"] <= 100


def test_block_2_4_duplicate_exposure_reads_combined_weight_from_block_2_1() -> None:
    block_21 = {
        "duplicate_exposure_flags": [
            {
                "duplicate_group_id": "us_equity_core",
                "tickers": ["SPY", "IVV"],
                "combined_weight": 0.18,
                "combined_weight_pct": 18.0,
                "canonical_ticker": "SPY",
            }
        ]
    }
    alert = build_block_2_4_hidden_exposure(block_21, _block_2_2(), _block_2_3())["alerts"][
        "correlation_concentration"
    ]
    duplicate_metric = next(
        row for row in alert["evidence"] if row["metric"] == "duplicate_exposure_weight"
    )
    assert duplicate_metric["value"] == 0.18
    assert duplicate_metric["direction"] == "above_threshold"
    group_evidence = next(
        row for row in alert["evidence"] if row["metric"] == "duplicate_exposure_groups"
    )
    assert group_evidence["direction"] == "present"
    assert group_evidence["value"][0]["duplicate_group_id"] == "us_equity_core"
    assert group_evidence["value"][0]["canonical_ticker"] == "SPY"


def test_block_2_4_duplicate_exposure_falls_back_to_legacy_weight_keys() -> None:
    block_21 = {"duplicate_exposure_flags": [{"observed": 0.12}]}
    alert = build_block_2_4_hidden_exposure(block_21, _block_2_2(), _block_2_3())["alerts"][
        "correlation_concentration"
    ]
    duplicate_metric = next(
        row for row in alert["evidence"] if row["metric"] == "duplicate_exposure_weight"
    )
    assert duplicate_metric["value"] == 0.12


def test_block_2_4_contributing_assets_equity_like_non_equity_label() -> None:
    block_21 = {
        **_block_2_1(),
        "capital_allocation_breakdown": {
            **_block_2_1()["capital_allocation_breakdown"],
            "by_asset": [
                {"name": "SPY", "weight_pct": 30.0},
                {"name": "GLD", "weight_pct": 20.0},
            ],
        },
    }
    taxonomy = {
        "SPY": {"asset_class": "equity", "main_risk_factor": "equity", "risk_role": ["risk_on"]},
        "GLD": {"asset_class": "commodity", "main_risk_factor": "equity", "risk_role": ["risk_on"]},
    }
    contributors = build_block_2_4_hidden_exposure(
        block_21, _block_2_2(), _block_2_3(), taxonomy_rows=taxonomy
    )["alerts"]["hidden_equity_beta"]["contributing_assets"]
    assert len(contributors) <= MAX_CONTRIBUTING_ASSETS
    gld = next(row for row in contributors if row["ticker"] == "GLD")
    assert gld["behavior_flag"] == "equity_like_non_equity_label"
    assert contributors[0]["ticker"] == "GLD"


def test_block_2_4_contributing_assets_correlation_prefers_duplicate_tickers() -> None:
    block_21 = {
        **_block_2_1(),
        "duplicate_exposure_flags": [
            {
                "duplicate_group_id": "us_equity",
                "tickers": ["SPY", "VOO"],
                "combined_weight": 0.55,
                "canonical_ticker": "SPY",
            }
        ],
        "capital_allocation_breakdown": {
            **_block_2_1()["capital_allocation_breakdown"],
            "by_asset": [
                {"name": "SPY", "weight_pct": 30.0},
                {"name": "VOO", "weight_pct": 25.0},
                {"name": "BND", "weight_pct": 45.0},
            ],
        },
    }
    contributors = build_block_2_4_hidden_exposure(
        block_21,
        {
            **_block_2_2(),
            "correlation_breakdown": {
                "top3_highest_correlation_pairs": [
                    {"ticker_a": "BND", "ticker_b": "TLT", "correlation": 0.91}
                ]
            },
        },
        _block_2_3(),
        taxonomy_rows=_taxonomy(),
    )["alerts"]["correlation_concentration"]["contributing_assets"]
    tickers = [row["ticker"] for row in contributors]
    assert "SPY" in tickers
    assert "VOO" in tickers
    assert contributors[0]["behavior_flag"] == "duplicate_exposure_group_member"


def test_block_2_4_contributing_assets_without_taxonomy_adds_limitation() -> None:
    block = build_block_2_4_hidden_exposure(_block_2_1(), _block_2_2(), _block_2_3())
    equity_alert = block["alerts"]["hidden_equity_beta"]
    tail_alert = block["alerts"]["tail_risk"]
    assert equity_alert["contributing_assets"] == []
    assert tail_alert["contributing_assets"]
    assert any("taxonomy_rows were not available" in lim for lim in equity_alert["limitations"])


def test_block_2_4_hidden_equity_beta_includes_taxonomy_sub_signals() -> None:
    alert = build_block_2_4_hidden_exposure(
        _block_2_1(), _block_2_2(), _block_2_3(), taxonomy_rows=_taxonomy()
    )["alerts"][
        "hidden_equity_beta"
    ]
    metrics = {row["metric"] for row in alert["evidence"]}
    assert "equity_weight" in metrics
    assert "risk_on_weight" in metrics
    equity = next(row for row in alert["evidence"] if row["metric"] == "equity_weight")
    assert equity["value"] == 0.45
    assert equity["source"] == "block_2_1"


def test_block_2_4_correlation_concentration_includes_correlation_subsignals() -> None:
    block_22 = {
        **_block_2_2(),
        "correlation_breakdown": {
            "top3_highest_correlation_pairs": [
                {"ticker_a": "SPY", "ticker_b": "SCHD", "correlation": 0.82}
            ],
            "top3_lowest_correlation_pairs": [
                {"ticker_a": "SPY", "ticker_b": "BND", "correlation": 0.35}
            ],
            "avg_pairwise_correlation": 0.61,
            "full_matrix_available": True,
            "full_matrix_ref": "correlation_matrix_10y.csv",
        },
    }
    alert = build_block_2_4_hidden_exposure(_block_2_1(), block_22, _block_2_3())["alerts"][
        "correlation_concentration"
    ]
    metrics = {row["metric"] for row in alert["evidence"]}
    assert "top3_lowest_correlation_pairs" in metrics
    assert "lowest_pair_correlation" in metrics
    assert "avg_pairwise_correlation" in metrics
    assert "lack_of_diversifying_pairs" in metrics
    lack = next(row for row in alert["evidence"] if row["metric"] == "lack_of_diversifying_pairs")
    assert lack["value"] is True
    assert lack["direction"] == "present"
    lowest = next(row for row in alert["evidence"] if row["metric"] == "lowest_pair_correlation")
    assert lowest["value"] == 0.35
    assert lowest["direction"] == "above_threshold"
    blocked_fields = {
        row["field"]
        for row in build_block_2_4_hidden_exposure(_block_2_1(), block_22, _block_2_3())[
            "diagnostics_meta"
        ]["blocked_upstream_fields"]
    }
    assert "avg_pairwise_correlation" not in blocked_fields


def test_block_2_4_hidden_equity_beta_includes_equity_like_correlation_pairs() -> None:
    block_21 = {
        **_block_2_1(),
        "capital_allocation_breakdown": {
            **_block_2_1()["capital_allocation_breakdown"],
            "by_asset": [
                {"name": "SPY", "weight_pct": 40.0},
                {"name": "GLD", "weight_pct": 35.0},
                {"name": "BND", "weight_pct": 25.0},
            ],
        },
    }
    block_22 = {
        **_block_2_2(),
        "correlation_breakdown": {
            "top3_highest_correlation_pairs": [
                {"ticker_a": "GLD", "ticker_b": "SPY", "correlation": 0.78}
            ],
            "top3_lowest_correlation_pairs": [
                {"ticker_a": "BND", "ticker_b": "GLD", "correlation": 0.15}
            ],
            "avg_pairwise_correlation": 0.52,
            "full_matrix_available": True,
            "full_matrix_ref": "correlation_matrix_10y.csv",
        },
    }
    taxonomy = {
        "SPY": {"asset_class": "equity", "main_risk_factor": "equity", "risk_role": ["risk_on"]},
        "GLD": {"asset_class": "commodity", "main_risk_factor": "equity", "risk_role": ["risk_on"]},
        "BND": {
            "asset_class": "fixed_income",
            "main_risk_factor": "real_rates",
            "risk_role": ["defensive"],
        },
    }
    alert = build_block_2_4_hidden_exposure(
        block_21, block_22, _block_2_3(), taxonomy_rows=taxonomy
    )["alerts"]["hidden_equity_beta"]
    metrics = {row["metric"] for row in alert["evidence"]}
    assert "equity_like_high_correlation_pairs" in metrics
    pairs = next(
        row for row in alert["evidence"] if row["metric"] == "equity_like_high_correlation_pairs"
    )
    assert pairs["value"][0]["ticker_a"] in {"GLD", "SPY"}
    assert pairs["direction"] == "present"


def test_block_2_4_correlation_concentration_includes_currency_evidence() -> None:
    alert = build_block_2_4_hidden_exposure(_block_2_1(), _block_2_2(), _block_2_3())["alerts"][
        "correlation_concentration"
    ]
    metrics = {row["metric"] for row in alert["evidence"]}
    assert "dominant_currency_weight" in metrics
    assert "usd_exposure_weight" in metrics
    assert "single_currency_dominance_flags" in metrics
    assert "investor_currency_mismatch" in metrics
    mismatch = next(row for row in alert["evidence"] if row["metric"] == "investor_currency_mismatch")
    assert mismatch["value"] is False
    assert mismatch["direction"] == "below_threshold"
    assert any("FX factor decomposition" in lim for lim in alert["limitations"])


def test_block_2_4_investor_currency_mismatch_when_dominant_currency_differs() -> None:
    block_21 = {
        **_block_2_1(),
        "capital_allocation_breakdown": {
            **_block_2_1()["capital_allocation_breakdown"],
            "by_currency": [{"name": "EUR", "weight_pct": 80.0}],
        },
    }
    block_22 = {**_block_2_2(), "investor_currency": "USD"}
    alert = build_block_2_4_hidden_exposure(block_21, block_22, _block_2_3())["alerts"][
        "correlation_concentration"
    ]
    mismatch = next(row for row in alert["evidence"] if row["metric"] == "investor_currency_mismatch")
    assert mismatch["value"] is True
    assert mismatch["direction"] == "present"


def test_block_2_4_credit_liquidity_includes_region_concentration_flags() -> None:
    alert = build_block_2_4_hidden_exposure(_block_2_1(), _block_2_2(), _block_2_3())["alerts"][
        "credit_liquidity_risk"
    ]
    metrics = {row["metric"] for row in alert["evidence"]}
    assert "region_concentration_flags" in metrics
    region = next(row for row in alert["evidence"] if row["metric"] == "region_concentration_flags")
    assert region["value"][0]["flag_id"] == "single_region_dominance"


def test_block_2_4_session_05_factor_subsignals_on_hidden_equity_beta() -> None:
    alert = build_block_2_4_hidden_exposure(_block_2_1(), _block_2_2(), _block_2_3_rich())["alerts"][
        "hidden_equity_beta"
    ]
    metrics = {row["metric"] for row in alert["evidence"]}
    assert "production_factor_betas_5y" in metrics
    assert "production_factor_confidence" in metrics
    assert "factor_variance_contribution" in metrics
    assert "factor_risk_ranking" in metrics
    assert "factor_beta_stability" in metrics
    assert "kalman_current_betas" in metrics
    conf = next(row for row in alert["evidence"] if row["metric"] == "production_factor_confidence")
    assert "beta_vix" in conf["value"]
    assert len(conf["value"]) >= 8


def test_block_2_4_session_05_duration_includes_beta_inf() -> None:
    alert = build_block_2_4_hidden_exposure(_block_2_1(), _block_2_2(), _block_2_3_rich())["alerts"][
        "duration_concentration"
    ]
    metrics = {row["metric"] for row in alert["evidence"]}
    assert "beta_inf" in metrics
    beta_inf = next(row for row in alert["evidence"] if row["metric"] == "beta_inf")
    assert beta_inf["value"] == 0.42
    assert "factor_beta_stability" in metrics


def test_block_2_4_session_05_weak_hedge_offset_factor_betas() -> None:
    alert = build_block_2_4_hidden_exposure(_block_2_1(), _block_2_2(), _block_2_3_rich())["alerts"][
        "weak_hedge_behavior"
    ]
    metrics = {row["metric"] for row in alert["evidence"]}
    for key in ("beta_usd", "beta_cmd", "beta_vix", "beta_rr"):
        assert key in metrics
    kalman = next(row for row in alert["evidence"] if row["metric"] == "kalman_current_betas")
    assert "beta_usd" in kalman["value"]


def test_block_2_4_session_05_tail_risk_includes_beta_vix() -> None:
    alert = build_block_2_4_hidden_exposure(_block_2_1(), _block_2_2(), _block_2_3_rich())["alerts"]["tail_risk"]
    metrics = {row["metric"] for row in alert["evidence"]}
    assert "beta_vix" in metrics
    assert "factor_variance_contribution" in metrics


def test_block_2_4_session_05_scores_unchanged_with_factor_evidence() -> None:
    minimal = build_block_2_4_hidden_exposure(_block_2_1(), _block_2_2(), _block_2_3())["alerts"]
    rich = build_block_2_4_hidden_exposure(_block_2_1(), _block_2_2(), _block_2_3_rich())["alerts"]
    for alert_id in (
        "hidden_equity_beta",
        "duration_concentration",
        "credit_liquidity_risk",
        "correlation_concentration",
        "weak_hedge_behavior",
        "tail_risk",
    ):
        assert minimal[alert_id]["score"] == rich[alert_id]["score"]
        assert minimal[alert_id]["status"] == rich[alert_id]["status"]


def test_block_2_4_session_06_propagates_block_2_2_history_warnings() -> None:
    block_22 = {
        **_block_2_2(),
        "data_quality_warnings": [
            "Analysis is limited because of short history / incomplete data.",
            "Correlation breakdown is limited because the primary-window correlation matrix is missing.",
        ],
    }
    alerts = build_block_2_4_hidden_exposure(_block_2_1(), block_22, _block_2_3())["alerts"]
    short_history = "short history"
    for alert_id in (
        "hidden_equity_beta",
        "credit_liquidity_risk",
        "correlation_concentration",
        "weak_hedge_behavior",
        "tail_risk",
    ):
        joined = " ".join(alerts[alert_id]["data_quality_warnings"]).lower()
        assert short_history in joined, alert_id
    corr_alert = alerts["correlation_concentration"]
    assert any("correlation breakdown" in w.lower() for w in corr_alert["data_quality_warnings"])
    block = build_block_2_4_hidden_exposure(_block_2_1(), block_22, _block_2_3())
    assert any("short history" in w.lower() for w in block["data_quality_warnings"])


def test_block_2_4_session_06_confidence_v2_and_status_cap() -> None:
    block_23 = {
        **_block_2_3(),
        "factor_significance_confidence": {
            "beta_eq": {"status": "unstable_low_confidence"},
            "beta_rr": {"status": "unstable_low_confidence"},
            "beta_credit": {"status": "unstable_low_confidence"},
        },
    }
    alert = build_block_2_4_hidden_exposure(
        _block_2_1(),
        {
            **_block_2_2(),
            "benchmark_dependence": {"beta_portfolio": 1.0, "downside_beta": 1.2},
            "rolling_diagnostics": {
                "core_view": {"rolling_beta_or_correlation": {"latest_correlation": 0.85}}
            },
        },
        {
            **block_23,
            "factor_beta_snapshot": {"beta_eq": 0.65, "beta_rr": 0.4, "beta_credit": 0.35},
        },
        taxonomy_rows=_taxonomy(),
    )["alerts"]["hidden_equity_beta"]
    assert alert["confidence"] == "low"
    assert "cross-signal agreement" in (alert["confidence_reason"] or "").lower()
    assert "model v2" in (alert["confidence_reason"] or "").lower()
    if alert.get("score") is not None and alert["score"] >= 70:
        assert alert["status"] != "High"
        assert alert["status"] == "Medium"
        assert alert["score"] <= 69
        assert any("capped" in note.lower() for note in alert["calculation_notes"])


def test_block_2_4_session_07_tail_risk_scored_var_and_underwater() -> None:
    alert = build_block_2_4_hidden_exposure(_block_2_1(), _block_2_2(), _block_2_3())["alerts"]["tail_risk"]
    scored_metrics = {row["metric"] for row in alert["evidence"] if row["metric"] in ALERT_RULES["tail_risk"]["signals"]}
    for key in (
        "var_95",
        "var_99",
        "downside_deviation",
        "max_drawdown",
        "pct_time_underwater",
        "longest_underwater_months",
        "unrecovered_drawdown",
        "count_drawdowns_gt_5",
    ):
        assert key in scored_metrics, key
    unrec = next(row for row in alert["evidence"] if row["metric"] == "unrecovered_drawdown")
    assert unrec["value"] == 1.0
    assert alert["score"] is not None


def test_block_2_4_session_07_tail_risk_vol_and_recovery_evidence() -> None:
    alert = build_block_2_4_hidden_exposure(_block_2_1(), _block_2_2(), _block_2_3())["alerts"]["tail_risk"]
    metrics = {row["metric"] for row in alert["evidence"]}
    assert "vol_of_vol" in metrics
    assert "rel_vol_of_vol" in metrics
    assert "rolling_volatility_12m_latest" in metrics
    assert "recovery_months" in metrics
    assert "drawdown_recovered" in metrics
    assert any("Sharpe instability" in lim for lim in alert["limitations"])


def test_block_2_4_session_07_tail_risk_partial_when_drawdown_missing() -> None:
    block_22 = {
        **_block_2_2(),
        "drawdown_diagnostics": {},
        "tail_risk_diagnostics": {"es_95": -0.02},
    }
    alert = build_block_2_4_hidden_exposure(_block_2_1(), block_22, _block_2_3())["alerts"]["tail_risk"]
    assert "max_drawdown missing" in " ".join(alert["insufficient_evidence_reasons"]).lower() or alert[
        "status"
    ] in {"Low", "Medium", "High", "Unavailable"}


def test_block_2_4_session_06_weak_hedge_confidence_capped_at_medium() -> None:
    alert = build_block_2_4_hidden_exposure(_block_2_1(), _block_2_2(), _block_2_3())["alerts"][
        "weak_hedge_behavior"
    ]
    assert alert["confidence"] in {"low", "medium"}
    assert "preliminary" in (alert["confidence_reason"] or "").lower()


def test_block_2_4_weak_hedge_is_preliminary_without_stress_lab() -> None:
    alert = build_block_2_4_hidden_exposure(_block_2_1(), _block_2_2(), _block_2_3())["alerts"][
        "weak_hedge_behavior"
    ]

    assert "preliminary_without_stress_lab" in alert["data_quality_warnings"]
    assert any("does not claim actual hedge failure" in note for note in alert["calculation_notes"])
    assert any("preliminary without Stress Lab" in lim for lim in alert["limitations"])
    assert alert["confidence_reason"]
    assert "equity_shock" in alert["next_tests"]


def test_block_2_4_does_not_mutate_input_blocks() -> None:
    block_21 = _block_2_1()
    block_22 = _block_2_2()
    block_23 = _block_2_3()
    before = (copy.deepcopy(block_21), copy.deepcopy(block_22), copy.deepcopy(block_23))

    build_block_2_4_hidden_exposure(block_21, block_22, block_23)

    assert (block_21, block_22, block_23) == before


def test_portfolio_xray_v2_includes_block_2_4_without_removing_legacy_section() -> None:
    xray = build_portfolio_xray_v2(
        analysis_setup={"analysis_portfolio": {"portfolio_role": "test"}},
        weights={"SPY": 0.6, "BND": 0.4},
        rc_asset=[],
        stress_report={"factor_betas_5y": {"beta_eq": 0.4, "beta_rr": 0.3}},
        portfolio_valid=True,
        portfolio_metrics={"beta_portfolio": 0.8, "downside_beta": 1.0},
        taxonomy_rows={
            "SPY": {"asset_class": "equity", "main_risk_factor": "equity", "risk_role": ["risk_on"]},
            "BND": {
                "asset_class": "fixed_income",
                "main_risk_factor": "real_rates",
                "risk_role": ["defensive"],
            },
        },
    )

    assert xray["block_2_4_hidden_exposure"]["block"] == BLOCK_2_4_ID
    assert tuple(xray["block_2_4_hidden_exposure"]["alerts"]) == ALERT_IDS
    assert "hidden_risk_detector" in xray["sections"]
    assert xray["block_2_1_asset_allocation"]["block"] == "2.1_asset_allocation"
    assert xray["block_2_2_portfolio_metrics"]["block"] == "2.2_portfolio_metrics"
    assert xray["block_2_3_factor_exposure"]["block"] == "2.3_factor_exposure"


def _stress_report_with_hedge_gap() -> dict:
    scenario_rows = [
        {
            "scenario_id": "equity_shock",
            "portfolio_pnl_pct": -0.10,
            "pnl_by_asset_pct": {"SPY": -0.08, "BND": -0.02},
        },
        {
            "scenario_id": "inflation_stagflation",
            "portfolio_pnl_pct": -0.08,
            "pnl_by_asset_pct": {"SPY": -0.05, "BND": 0.01},
        },
        {
            "scenario_id": "commodity_shock",
            "portfolio_pnl_pct": -0.06,
            "pnl_by_asset_pct": {"SPY": -0.04, "BND": 0.005},
        },
    ]
    stress_results_v1 = build_stress_results_v1(
        scenario_results=scenario_rows,
        historical_results=[],
        historical_episode_paths=[],
        stress_conclusions={},
        loss_gate_mode="diagnostic",
    )
    hedge_gap = build_hedge_gap_analysis_v1(
        stress_results_v1=stress_results_v1,
        scenario_results=scenario_rows,
        loss_gate_mode="diagnostic",
    )
    return {
        "scenario_results": scenario_rows,
        "stress_results_v1": stress_results_v1,
        "hedge_gap_analysis_v1": hedge_gap,
        "factor_beta_shock_oos": {"summary": {"mean_abs_error_5y": 0.03}},
    }


def test_block_2_4_session_08_stress_enrichment_builder() -> None:
    enrichment = build_block_2_4_stress_enrichment(
        _stress_report_with_hedge_gap(),
        block_2_1=_block_2_1(),
        taxonomy_rows=_taxonomy(),
    )
    assert enrichment is not None
    assert enrichment["available"] is True
    assert "hedge_gap_analysis_v1" in enrichment["sources"]
    assert "BND" in enrichment["hedge_tickers"]
    assert enrichment["hedge_gap_by_risk_type"]["stagflation_protection"]["linked_scenario_id"] == (
        "inflation_stagflation"
    )


def test_block_2_4_session_08_weak_hedge_confirmed_with_stress_context() -> None:
    enrichment = build_block_2_4_stress_enrichment(
        _stress_report_with_hedge_gap(),
        block_2_1=_block_2_1(),
        taxonomy_rows=_taxonomy(),
    )
    alert = build_block_2_4_hidden_exposure(
        _block_2_1(),
        _block_2_2(),
        _block_2_3(),
        taxonomy_rows=_taxonomy(),
        stress_enrichment=enrichment,
    )["alerts"]["weak_hedge_behavior"]
    assert alert["confirmation_status"] == "confirmed"
    assert "preliminary_without_stress_lab" not in alert["data_quality_warnings"]
    metrics = {row["metric"] for row in alert["evidence"]}
    assert "hedge_gap_summary" in metrics
    assert "worst_scenario_hedge_offset_check" in metrics
    assert "factor_oos_mae_5y" in metrics
    assert any(row["source"] == "block_3_stress" for row in alert["evidence"])


def test_block_2_4_session_08_duration_commodity_stagflation_cross_ref() -> None:
    enrichment = build_block_2_4_stress_enrichment(
        _stress_report_with_hedge_gap(),
        block_2_1=_block_2_1(),
        taxonomy_rows=_taxonomy(),
    )
    alert = build_block_2_4_hidden_exposure(
        _block_2_1(),
        _block_2_2(),
        _block_2_3(),
        stress_enrichment=enrichment,
    )["alerts"]["duration_concentration"]
    metrics = {row["metric"] for row in alert["evidence"]}
    assert "stagflation_offset_coverage" in metrics
    assert "commodity_shock_offset_coverage" in metrics


def test_block_2_4_session_08_scores_unchanged_with_stress_enrichment() -> None:
    base = build_block_2_4_hidden_exposure(_block_2_1(), _block_2_2(), _block_2_3(), taxonomy_rows=_taxonomy())[
        "alerts"
    ]
    enrichment = build_block_2_4_stress_enrichment(
        _stress_report_with_hedge_gap(),
        block_2_1=_block_2_1(),
        taxonomy_rows=_taxonomy(),
    )
    enriched = build_block_2_4_hidden_exposure(
        _block_2_1(),
        _block_2_2(),
        _block_2_3(),
        taxonomy_rows=_taxonomy(),
        stress_enrichment=enrichment,
    )["alerts"]
    for alert_id in ALERT_IDS:
        assert base[alert_id]["score"] == enriched[alert_id]["score"]
        assert base[alert_id]["status"] == enriched[alert_id]["status"]


def _stress_report_with_portfolio_pca() -> dict:
    return {
        "portfolio_pca": {
            "raw": {
                "covariance_pca": {
                    "pc1_explained_variance_ratio": 0.65,
                }
            },
            "residual": {
                "covariance_pca": {
                    "pc1_explained_variance_ratio": 0.48,
                }
            },
        },
        "factor_variance_decomposition": {"residual_share": 0.35},
    }


def test_block_2_4_session_09_legacy_enrichment_builder() -> None:
    enrichment = build_block_2_4_legacy_enrichment(_stress_report_with_portfolio_pca())
    assert enrichment is not None
    assert enrichment["available"] is True
    assert enrichment["raw_pc1_explained_variance_ratio"] == 0.65
    assert enrichment["residual_pc1_explained_variance_ratio"] == 0.48
    assert enrichment["factor_residual_share"] == 0.35
    assert "portfolio_pca.raw" in enrichment["sources"]
    assert enrichment["legacy_section_refs"]["raw_pca"] == LEGACY_PCA_RAW_SECTION


def test_block_2_4_session_09_correlation_pca_cross_ref_evidence() -> None:
    enrichment = build_block_2_4_legacy_enrichment(_stress_report_with_portfolio_pca())
    alert = build_block_2_4_hidden_exposure(
        _block_2_1(),
        _block_2_2(),
        _block_2_3(),
        legacy_enrichment=enrichment,
    )["alerts"]["correlation_concentration"]
    metrics = {row["metric"] for row in alert["evidence"]}
    assert "legacy_pca_pc1_raw" in metrics
    assert "legacy_pca_pc1_residual" in metrics
    assert "legacy_factor_residual_share" in metrics
    raw_row = next(row for row in alert["evidence"] if row["metric"] == "legacy_pca_pc1_raw")
    assert raw_row["source"] == "portfolio_analytics"
    assert raw_row["value"]["legacy_section"] == LEGACY_PCA_RAW_SECTION
    assert raw_row["direction"] == "above_threshold"
    assert any("PCA common-factor" in lim for lim in alert["limitations"])
    assert any(
        "legacy_pca_cross_ref" in note for note in alert["calculation_notes"]
    )


def test_block_2_4_session_09_scores_unchanged_with_legacy_enrichment() -> None:
    base = build_block_2_4_hidden_exposure(_block_2_1(), _block_2_2(), _block_2_3())["alerts"]
    enrichment = build_block_2_4_legacy_enrichment(_stress_report_with_portfolio_pca())
    enriched = build_block_2_4_hidden_exposure(
        _block_2_1(),
        _block_2_2(),
        _block_2_3(),
        legacy_enrichment=enrichment,
    )["alerts"]
    for alert_id in ALERT_IDS:
        assert base[alert_id]["score"] == enriched[alert_id]["score"]
        assert base[alert_id]["status"] == enriched[alert_id]["status"]


def test_block_2_4_session_09_xray_wires_legacy_enrichment_meta() -> None:
    xray = build_portfolio_xray_v2(
        analysis_setup={"analysis_portfolio": {"portfolio_role": "test"}},
        weights={"SPY": 0.45, "BND": 0.4, "HYG": 0.15},
        rc_asset=[],
        stress_report=_stress_report_with_portfolio_pca(),
        portfolio_valid=True,
        portfolio_metrics={"beta_portfolio": 0.8, "downside_beta": 1.0},
        taxonomy_rows=_taxonomy(),
    )
    meta = xray["block_2_4_hidden_exposure"]["diagnostics_meta"]
    assert meta["legacy_enrichment_wire_time"] is True
    assert "portfolio_pca.raw" in meta["legacy_enrichment_sources"]
    metrics = {
        row["metric"]
        for row in xray["block_2_4_hidden_exposure"]["alerts"]["correlation_concentration"]["evidence"]
    }
    assert "legacy_pca_pc1_raw" in metrics


def test_block_2_4_session_08_xray_wires_stress_enrichment_meta() -> None:
    stress_report = _stress_report_with_hedge_gap()
    xray = build_portfolio_xray_v2(
        analysis_setup={"analysis_portfolio": {"portfolio_role": "test"}},
        weights={"SPY": 0.45, "BND": 0.4, "HYG": 0.15},
        rc_asset=[],
        stress_report=stress_report,
        portfolio_valid=True,
        portfolio_metrics={"beta_portfolio": 0.8, "downside_beta": 1.0},
        taxonomy_rows=_taxonomy(),
    )
    meta = xray["block_2_4_hidden_exposure"]["diagnostics_meta"]
    assert meta["stress_enrichment_wire_time"] is True
    assert "hedge_gap_analysis_v1" in meta["stress_enrichment_sources"]
    assert meta["hedge_gap_bridge_wire_time"] is True
    weak = xray["block_2_4_hidden_exposure"]["alerts"]["weak_hedge_behavior"]
    assert weak["confirmation_status"] in {"confirmed", "partially_confirmed"}
    assert isinstance(weak.get("hedge_gap_bridge"), dict)
    hedge_gap = stress_report.get("hedge_gap_analysis_v1") or {}
    assert isinstance(hedge_gap.get("hidden_exposure_confirmation"), list)
    assert isinstance(hedge_gap.get("weakness_map_confirmation"), list)
    assert len(hedge_gap.get("weakness_map_confirmation") or []) == 8
    bridge_meta = hedge_gap.get("bridge_meta") or {}
    assert bridge_meta.get("block_2_6_portfolio_weakness_map") is True
