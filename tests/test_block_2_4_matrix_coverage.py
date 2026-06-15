"""Block 2.4 institutional upgrade — Session 10 matrix row coverage (§10 plan).

Each parametrized row maps to one implementable ✅ v2 sub-dimension from the completion
matrix in docs/audits/2026-05-29_block_2_4_session_00_baseline_audit.md.
"""
from __future__ import annotations

import pytest

from src.block_2_4_hidden_exposure import ALERT_IDS, BLOCKED_UPSTREAM_FIELDS, BLOCK_2_4_ID

from test_block_2_4_hidden_exposure import (
    _block_2_1,
    _block_2_2,
    _block_2_3_rich,
    _stress_report_with_hedge_gap,
    _taxonomy,
    build_block_2_4_hidden_exposure,
    build_block_2_4_stress_enrichment,
)

# (matrix_row_id, alert_id, expected evidence metric name)
MATRIX_V2_EVIDENCE_ROWS: tuple[tuple[str, str, str], ...] = (
    # D1 — Equity hidden risk
    ("D1.equity_allocation", "hidden_equity_beta", "equity_weight"),
    ("D1.risk_on_exposure", "hidden_equity_beta", "risk_on_weight"),
    ("D1.beta_portfolio", "hidden_equity_beta", "beta_portfolio"),
    ("D1.downside_beta_equity", "hidden_equity_beta", "downside_beta"),
    ("D1.rolling_benchmark_correlation", "hidden_equity_beta", "rolling_correlation"),
    ("D1.beta_eq", "hidden_equity_beta", "beta_eq"),
    ("D1.beta_eq_confidence", "hidden_equity_beta", "beta_eq_confidence"),
    ("D1.equity_variance_share", "hidden_equity_beta", "factor_variance_contribution"),
    ("D1.equity_like_corr_pairs", "hidden_equity_beta", "equity_like_high_correlation_pairs"),
    # D2 — Rates / duration
    ("D2.fixed_income_weight", "duration_concentration", "fixed_income_weight"),
    ("D2.rates_or_duration_weight", "duration_concentration", "rates_or_duration_weight"),
    ("D2.beta_rr", "duration_concentration", "beta_rr"),
    ("D2.beta_inf", "duration_concentration", "beta_inf"),
    # D3 — Credit / liquidity
    ("D3.beta_credit", "credit_liquidity_risk", "beta_credit"),
    ("D3.credit_liquidity_weight", "credit_liquidity_risk", "credit_liquidity_weight"),
    ("D3.risk_on_or_carry", "credit_liquidity_risk", "risk_on_or_carry_weight"),
    ("D3.downside_beta_credit", "credit_liquidity_risk", "downside_beta"),
    ("D3.region_concentration_flags", "credit_liquidity_risk", "region_concentration_flags"),
    # D4 — Correlation
    ("D4.highest_pair_correlation", "correlation_concentration", "highest_pair_correlation"),
    ("D4.lowest_pair_correlation", "correlation_concentration", "lowest_pair_correlation"),
    ("D4.avg_pairwise_correlation", "correlation_concentration", "avg_pairwise_correlation"),
    ("D4.lack_of_diversifying_pairs", "correlation_concentration", "lack_of_diversifying_pairs"),
    ("D4.duplicate_exposure_groups", "correlation_concentration", "duplicate_exposure_groups"),
    ("D4.dominant_main_risk_factor", "correlation_concentration", "dominant_main_risk_factor_weight"),
    # D5 — Duplicate exposure (sub-signal)
    ("D5.duplicate_exposure_weight", "correlation_concentration", "duplicate_exposure_weight"),
    # D6 — Currency / FX
    ("D6.dominant_currency_weight", "correlation_concentration", "dominant_currency_weight"),
    ("D6.usd_exposure_weight", "correlation_concentration", "usd_exposure_weight"),
    ("D6.single_currency_dominance", "correlation_concentration", "single_currency_dominance_flags"),
    ("D6.investor_currency_mismatch", "correlation_concentration", "investor_currency_mismatch"),
    # D7 — Factor concentration (distributed)
    ("D7.factor_risk_ranking", "hidden_equity_beta", "factor_risk_ranking"),
    ("D7.dominant_factor_share", "hidden_equity_beta", "dominant_factor_variance_share"),
    ("D7.production_factor_confidence", "hidden_equity_beta", "production_factor_confidence"),
    ("D7.production_factor_betas", "hidden_equity_beta", "production_factor_betas_5y"),
    ("D7.factor_beta_stability", "hidden_equity_beta", "factor_beta_stability"),
    ("D7.kalman_current_betas", "hidden_equity_beta", "kalman_current_betas"),
    # D8 — Commodity / inflation
    ("D8.beta_cmd_weak_hedge", "weak_hedge_behavior", "beta_cmd"),
    ("D8.stagflation_cross_ref", "duration_concentration", "stagflation_offset_coverage"),
    ("D8.commodity_shock_cross_ref", "duration_concentration", "commodity_shock_offset_coverage"),
    # D9 — Weak hedge
    ("D9.hedge_labeled_weight", "weak_hedge_behavior", "hedge_labeled_weight"),
    ("D9.equity_or_credit_beta", "weak_hedge_behavior", "equity_or_credit_beta"),
    ("D9.offset_beta_usd", "weak_hedge_behavior", "beta_usd"),
    ("D9.offset_beta_vix", "weak_hedge_behavior", "beta_vix"),
    ("D9.hedge_gap_summary", "weak_hedge_behavior", "hedge_gap_summary"),
    ("D9.worst_scenario_hedge_offset", "weak_hedge_behavior", "worst_scenario_hedge_offset_check"),
    ("D9.factor_oos_mae", "weak_hedge_behavior", "factor_oos_mae_5y"),
    # D10 — Tail / drawdown
    ("D10.es_95", "tail_risk", "es_95"),
    ("D10.es_99", "tail_risk", "es_99"),
    ("D10.var_95", "tail_risk", "var_95"),
    ("D10.var_99", "tail_risk", "var_99"),
    ("D10.eee_10", "tail_risk", "eee_10"),
    ("D10.skewness", "tail_risk", "skewness"),
    ("D10.kurtosis", "tail_risk", "kurtosis"),
    ("D10.downside_deviation", "tail_risk", "downside_deviation"),
    ("D10.max_drawdown", "tail_risk", "max_drawdown"),
    ("D10.pct_time_underwater", "tail_risk", "pct_time_underwater"),
    ("D10.longest_underwater", "tail_risk", "longest_underwater_months"),
    ("D10.unrecovered_drawdown", "tail_risk", "unrecovered_drawdown"),
    ("D10.count_drawdowns_gt_5", "tail_risk", "count_drawdowns_gt_5"),
    ("D10.recovery_months", "tail_risk", "recovery_months"),
    ("D10.drawdown_recovered", "tail_risk", "drawdown_recovered"),
    # D11 — Vol instability (evidence on tail_risk)
    ("D11.vol_of_vol", "tail_risk", "vol_of_vol"),
    ("D11.rel_vol_of_vol", "tail_risk", "rel_vol_of_vol"),
    ("D11.rolling_volatility", "tail_risk", "rolling_volatility_12m_latest"),
)

DEFERRED_REGISTRY_FIELDS: tuple[str, ...] = tuple(row["field"] for row in BLOCKED_UPSTREAM_FIELDS)

DEFERRED_LIMITATION_SNIPPETS: tuple[tuple[str, str], ...] = (
    ("duration_concentration", "duration_bucket"),
    ("credit_liquidity_risk", "credit_quality"),
    ("credit_liquidity_risk", "subtype weights"),
    ("tail_risk", "Sharpe instability"),
)


def _rich_block_22() -> dict:
    return {
        **_block_2_2(),
        "correlation_breakdown": {
            "top3_highest_correlation_pairs": [
                {"ticker_a": "GLD", "ticker_b": "SPY", "correlation": 0.78}
            ],
            "top3_lowest_correlation_pairs": [
                {"ticker_a": "SPY", "ticker_b": "BND", "correlation": 0.35}
            ],
            "avg_pairwise_correlation": 0.61,
            "full_matrix_available": True,
            "full_matrix_ref": "correlation_matrix_10y.csv",
        },
    }


def _rich_block_21_equity_like_pair() -> dict:
    return {
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


def _equity_like_taxonomy() -> dict:
    return {
        **_taxonomy(),
        "GLD": {
            "asset_class": "commodity",
            "main_risk_factor": "equity",
            "risk_role": ["risk_on"],
        },
    }


def _build_v2_matrix_block() -> dict:
    block_21 = _rich_block_21_equity_like_pair()
    taxonomy = _equity_like_taxonomy()
    stress_enrichment = build_block_2_4_stress_enrichment(
        _stress_report_with_hedge_gap(),
        block_2_1=block_21,
        taxonomy_rows=taxonomy,
    )
    return build_block_2_4_hidden_exposure(
        block_21,
        _rich_block_22(),
        _block_2_3_rich(),
        taxonomy_rows=taxonomy,
        stress_enrichment=stress_enrichment,
    )


@pytest.fixture(scope="module")
def v2_matrix_block() -> dict:
    return _build_v2_matrix_block()


@pytest.mark.parametrize("row_id,alert_id,metric", MATRIX_V2_EVIDENCE_ROWS)
def test_matrix_v2_row_has_evidence(
    v2_matrix_block: dict, row_id: str, alert_id: str, metric: str
) -> None:
    alert = v2_matrix_block["alerts"][alert_id]
    metrics = {row["metric"] for row in alert["evidence"]}
    assert metric in metrics, f"{row_id}: {metric} missing on {alert_id}"


def test_matrix_d1_equity_like_contributing_asset(v2_matrix_block: dict) -> None:
    contributors = v2_matrix_block["alerts"]["hidden_equity_beta"]["contributing_assets"]
    assert contributors
    assert any(row.get("behavior_flag") == "equity_like_non_equity_label" for row in contributors)


def test_matrix_d2_rates_next_tests(v2_matrix_block: dict) -> None:
    next_tests = v2_matrix_block["alerts"]["duration_concentration"]["next_tests"]
    assert "rates_shock" in next_tests
    assert "inflation_stagflation" in next_tests


def test_matrix_d4_correlation_concentration_is_non_pca(v2_matrix_block: dict) -> None:
    metrics = {
        row["metric"] for row in v2_matrix_block["alerts"]["correlation_concentration"]["evidence"]
    }
    assert "legacy_pca_pc1_raw" not in metrics
    assert "legacy_pca_pc1_residual" not in metrics
    assert "highest_pair_correlation" in metrics
    assert "avg_pairwise_correlation" in metrics
    assert any("PCA is not read or scored" in lim for lim in v2_matrix_block["alerts"]["correlation_concentration"]["limitations"])


def test_matrix_d9_confirmation_status_with_stress(v2_matrix_block: dict) -> None:
    weak = v2_matrix_block["alerts"]["weak_hedge_behavior"]
    assert weak["confirmation_status"] == "confirmed"
    assert "preliminary_without_stress_lab" not in weak["data_quality_warnings"]


def test_matrix_d12_contributing_assets_on_all_alerts(v2_matrix_block: dict) -> None:
    for alert_id in ALERT_IDS:
        assets = v2_matrix_block["alerts"][alert_id]["contributing_assets"]
        assert isinstance(assets, list)
        assert len(assets) <= 3


def test_matrix_d13_mandatory_alert_fields(v2_matrix_block: dict) -> None:
    for alert_id in ALERT_IDS:
        alert = v2_matrix_block["alerts"][alert_id]
        assert isinstance(alert["limitations"], list)
        assert alert["confidence_reason"]
        assert alert["confirmation_status"] in {
            "preliminary",
            "confirmed",
            "unavailable",
            "not_applicable",
        }


def test_matrix_d13_heuristic_v2_metadata(v2_matrix_block: dict) -> None:
    meta = v2_matrix_block["diagnostics_meta"]
    assert meta["ruleset"] == "heuristic_v2"
    assert meta["confidence_model"] == "v2"
    assert meta["stress_enrichment_wire_time"] is True
    assert meta["legacy_enrichment_wire_time"] is False
    assert meta["legacy_enrichment_sources"] == []
    assert meta["pca_used_for_correlation_concentration"] is False


@pytest.mark.parametrize("field", DEFERRED_REGISTRY_FIELDS)
def test_matrix_deferred_field_in_blocked_registry(v2_matrix_block: dict, field: str) -> None:
    blocked = {row["field"] for row in v2_matrix_block["diagnostics_meta"]["blocked_upstream_fields"]}
    assert field in blocked


@pytest.mark.parametrize("alert_id,snippet", DEFERRED_LIMITATION_SNIPPETS)
def test_matrix_deferred_upstream_limitation_documented(
    v2_matrix_block: dict, alert_id: str, snippet: str
) -> None:
    limitations = " ".join(v2_matrix_block["alerts"][alert_id]["limitations"]).lower()
    assert snippet.lower() in limitations


def test_matrix_block_top_level_contract(v2_matrix_block: dict) -> None:
    assert v2_matrix_block["block"] == BLOCK_2_4_ID
    assert v2_matrix_block["status"] in {"ok", "partial", "unavailable"}
    assert tuple(v2_matrix_block["alerts"]) == ALERT_IDS
    assert len(v2_matrix_block["top_hidden_risks"]) <= 3
