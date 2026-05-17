from __future__ import annotations

import json
from pathlib import Path

from src.portfolio_xray import (
    PORTFOLIO_XRAY_VERSION,
    XRAY_SECTION_KEYS,
    XRAY_THRESHOLDS,
    build_portfolio_xray_summary,
    build_portfolio_xray_v2,
    format_portfolio_xray_text,
)
from src.snapshot import write_report_html, write_report_txt


def _analysis_setup(role: str = "generated_policy_portfolio") -> dict:
    return {
        "version": "analysis_setup_v1",
        "portfolio_input": {
            "product_input_case": "universe_only",
            "investor_currency": "USD",
        },
        "analysis_portfolio": {
            "portfolio_role": role,
            "weight_source": "Main portfolio/portfolio_weights.yml",
            "recommendation_status": (
                "baseline_not_recommendation"
                if role == "equal_weight_initial_baseline"
                else "generated_policy_output_not_user_input"
            ),
            "weights": {"TLT": 0.3, "BND": 0.2, "SPY": 0.1, "BIL": 0.05},
            "cash_handling": {"cash_proxy_ticker": "BIL"},
        },
        "resolved_assumptions": {
            "base_benchmark_ticker": "SPY",
            "cash_proxy": {"ticker": "BIL"},
            "return_frequency": "monthly",
            "analysis_windows": [36, 60, 120],
        },
    }


def test_portfolio_xray_summary_answers_core_questions_without_score() -> None:
    summary = build_portfolio_xray_summary(
        analysis_setup=_analysis_setup(),
        weights={"TLT": 0.3, "BND": 0.2, "SPY": 0.1, "BIL": 0.05},
        rc_asset=[
            {"ticker": "SLV", "rc_pct": 0.4},
            {"ticker": "TLT", "rc_pct": 0.3},
            {"ticker": "GLD", "rc_pct": 0.2},
        ],
        stress_report={
            "status": "DIAG_PASS_WITH_WARNING",
            "scenario_results": [
                {"scenario_id": "rates_shock", "portfolio_pnl_pct": -0.12},
                {"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.04},
            ],
        },
        portfolio_valid=True,
        portfolio_metrics={"vol_annual": 0.07, "max_drawdown": -0.18},
    )
    text = format_portfolio_xray_text(summary)

    assert "role=generated_policy_portfolio" in text
    assert "weight_source=Main portfolio/portfolio_weights.yml" in text
    assert "Capital concentration: TLT 30.0%, BND 20.0%, SPY 10.0%" in text
    assert "Risk concentration by RC_vol: SLV 40.0%, TLT 30.0%, GLD 20.0%" in text
    assert "Main diagnostic concern: rates_shock sensitivity" in text
    assert "not a score, recommendation, selection decision, or trade instruction" in text
    assert "score" in text.lower()


def test_portfolio_xray_baseline_is_not_recommendation() -> None:
    summary = build_portfolio_xray_summary(
        analysis_setup=_analysis_setup("equal_weight_initial_baseline"),
        weights={"A": 0.5, "B": 0.5},
        rc_asset=[{"ticker": "A", "rc_pct": 0.7}, {"ticker": "B", "rc_pct": 0.3}],
        stress_report={"status": "DIAG_PASS"},
        portfolio_valid=True,
    )

    assert summary["analysis_setup_summary"]["portfolio_role"] == "equal_weight_initial_baseline"
    assert summary["analysis_setup_summary"]["recommendation_status"] == "baseline_not_recommendation"
    assert "baseline_not_recommendation" in format_portfolio_xray_text(summary)


def test_snapshot_reports_include_xray_summary(tmp_path: Path) -> None:
    out = tmp_path / "Main portfolio"
    out.mkdir(parents=True)
    (out / "run_metadata.json").write_text(
        json.dumps({"analysis_setup": _analysis_setup(), "portfolio_valid": True}),
        encoding="utf-8",
    )
    (out / "snapshot_10y.json").write_text(
        json.dumps(
            {
                "analysis_end": "2026-04-30",
                "final_weights_total": {"TLT": 0.3, "BND": 0.2, "SPY": 0.1, "BIL": 0.05},
                "RC_asset": [
                    {"ticker": "SLV", "rc_pct": 0.4},
                    {"ticker": "TLT", "rc_pct": 0.3},
                ],
                "metrics": {"vol_annual": 0.07, "max_drawdown": -0.18},
                "stress_suite_results": {"overall": "DIAG_PASS_WITH_WARNING"},
            }
        ),
        encoding="utf-8",
    )
    (out / "stress_report.json").write_text(
        json.dumps(
            {
                "status": "DIAG_PASS_WITH_WARNING",
                "scenario_results": [{"scenario_id": "rates_shock", "portfolio_pnl_pct": -0.12}],
            }
        ),
        encoding="utf-8",
    )

    txt = write_report_txt(out)
    html = write_report_html(out)
    xray_json = out / "portfolio_xray.json"

    txt_body = txt.read_text(encoding="utf-8")
    html_body = html.read_text(encoding="utf-8")
    xray_payload = json.loads(xray_json.read_text(encoding="utf-8"))
    assert "Portfolio X-Ray Summary" in txt_body
    assert "role=generated_policy_portfolio" in txt_body
    assert "main capital concentration" in txt_body
    assert "main RC_vol concentration" in txt_body
    assert "Portfolio Diagnostic Verdict" in txt_body
    assert "Portfolio X-Ray Summary" in html_body
    assert "Asset Allocation Summary" in html_body
    assert "Risk Contribution Summary" in html_body
    assert xray_payload["version"] == PORTFOLIO_XRAY_VERSION
    assert xray_payload["diagnostic_only"] is True
    assert set(XRAY_SECTION_KEYS).issubset(xray_payload["sections"])


def _taxonomy_rows() -> dict[str, dict]:
    return {
        "SPY": {
            "ticker": "SPY",
            "asset_class": "equity",
            "region": "US",
            "currency_exposure": "USD",
            "sector": "multi_sector",
            "risk_role": ["risk_on", "growth"],
            "main_risk_factor": "equity",
            "secondary_risk_factors": ["us_growth"],
            "duration_bucket": "none",
            "credit_quality": "none",
            "subtype": "broad_market",
        },
        "TLT": {
            "ticker": "TLT",
            "asset_class": "fixed_income",
            "region": "US",
            "currency_exposure": "USD",
            "sector": "none",
            "risk_role": ["defensive", "duration"],
            "main_risk_factor": "real_rates",
            "secondary_risk_factors": [],
            "duration_bucket": "long",
            "credit_quality": "Treasury",
            "subtype": "treasury",
        },
        "HYG": {
            "ticker": "HYG",
            "asset_class": "fixed_income",
            "region": "US",
            "currency_exposure": "USD",
            "sector": "none",
            "risk_role": ["carry", "risk_on", "income"],
            "main_risk_factor": "credit",
            "secondary_risk_factors": ["liquidity"],
            "duration_bucket": "intermediate",
            "credit_quality": "HY",
            "subtype": "high_yield",
        },
        "GLD": {
            "ticker": "GLD",
            "asset_class": "commodity",
            "region": "Global",
            "currency_exposure": "USD",
            "sector": "none",
            "risk_role": ["inflation_hedge", "crisis_hedge"],
            "main_risk_factor": "commodity",
            "secondary_risk_factors": ["usd"],
            "duration_bucket": "none",
            "credit_quality": "none",
            "subtype": "gold",
        },
    }


def _rich_stress_report() -> dict:
    return {
        "status": "DIAG_PASS_WITH_WARNING",
        "scenario_results": [
            {
                "scenario_id": "equity_shock",
                "portfolio_pnl_pct": -0.09,
                "top1_rc_asset": "SPY",
                "top1_rc_pct": 0.36,
                "top3_rc_sum_pct": 0.64,
                "pnl_by_asset_pct": {"SPY": -0.06, "TLT": -0.01, "HYG": -0.02, "GLD": 0.0},
            },
            {
                "scenario_id": "recession_severe",
                "portfolio_pnl_pct": -0.14,
                "top1_rc_asset": "HYG",
                "top1_rc_pct": 0.42,
                "top3_rc_sum_pct": 0.70,
                "pnl_by_asset_pct": {"SPY": -0.05, "TLT": 0.01, "HYG": -0.08, "GLD": -0.01},
            },
        ],
        "factor_betas_5y": {"beta_eq": 0.72, "beta_credit": 0.31, "beta_cmd": 0.18},
        "factor_betas_10y": {"beta_eq": 0.55, "beta_credit": 0.20, "beta_cmd": 0.12},
        "factor_variance_decomposition": {
            "status": "available",
            "residual_share": 0.70,
            "residual_severity": "high",
            "rows": [
                {
                    "factor": "equity",
                    "beta_key": "beta_eq",
                    "net_total_variance_share": 0.40,
                    "gross_total_variance_share": 0.40,
                    "direction": "risk_adder",
                },
                {
                    "factor": "credit",
                    "beta_key": "beta_credit",
                    "net_total_variance_share": 0.08,
                    "gross_total_variance_share": 0.08,
                    "direction": "risk_adder",
                },
            ],
        },
        "portfolio_pca": {
            "raw": {
                "covariance_pca": {
                    "pc1_explained_variance_ratio": 0.66,
                    "pc1_severity": "high",
                }
            }
        },
    }


def test_portfolio_xray_v2_contract_sections_and_disclaimer() -> None:
    xray = build_portfolio_xray_v2(
        analysis_setup=_analysis_setup(),
        weights={"SPY": 0.45, "TLT": 0.30, "HYG": 0.15, "GLD": 0.10},
        rc_asset=[
            {"ticker": "SPY", "rc_pct": 0.40},
            {"ticker": "HYG", "rc_pct": 0.30},
            {"ticker": "TLT", "rc_pct": 0.20},
            {"ticker": "GLD", "rc_pct": 0.10},
        ],
        stress_report=_rich_stress_report(),
        portfolio_valid=True,
        portfolio_metrics={"cagr": 0.08, "vol_annual": 0.10, "sharpe": 0.6, "sortino": 0.8, "max_drawdown": -0.22},
        portfolio_analytics={"var_95": -0.02, "es_95": -0.03},
        taxonomy_rows=_taxonomy_rows(),
        taxonomy_sources={ticker: "test_taxonomy" for ticker in _taxonomy_rows()},
    )

    assert xray["version"] == PORTFOLIO_XRAY_VERSION
    assert xray["diagnostic_only"] is True
    assert "does not optimize" in xray["diagnostic_only_disclaimer"]
    assert "top1_rc_high" in xray["thresholds"]
    assert xray["thresholds"]["top1_rc_high"] == XRAY_THRESHOLDS["top1_rc_high"]
    assert list(xray["sections"]) == list(XRAY_SECTION_KEYS)
    for section in xray["sections"].values():
        assert set(section) == {"status", "data_sources_used", "warnings", "items", "limitations"}
        assert section["status"] in {"available", "partial", "unavailable"}


def test_portfolio_xray_v2_taxonomy_breakdown_and_missing_taxonomy_partial() -> None:
    xray = build_portfolio_xray_v2(
        analysis_setup=_analysis_setup(),
        weights={"SPY": 0.50, "TLT": 0.25, "UNKNOWN": 0.25},
        rc_asset=[],
        stress_report={},
        portfolio_valid=True,
        taxonomy_rows=_taxonomy_rows(),
        taxonomy_sources={"SPY": "test_taxonomy", "TLT": "test_taxonomy"},
    )

    section = xray["sections"]["asset_allocation"]
    assert section["status"] == "partial"
    assert any("unknown taxonomy" in warning for warning in section["warnings"])
    asset_class = next(
        item for item in section["items"] if item.get("type") == "breakdown" and item.get("dimension") == "asset_class"
    )
    values = {row["name"]: row["weight"] for row in asset_class["values"]}
    assert values["equity"] == 0.50
    assert values["fixed_income"] == 0.25
    assert values["unknown"] == 0.25


def test_portfolio_xray_v2_risk_budget_hidden_flags_archetype_and_weakness() -> None:
    xray = build_portfolio_xray_v2(
        analysis_setup=_analysis_setup(),
        weights={"SPY": 0.45, "TLT": 0.30, "HYG": 0.15, "GLD": 0.10},
        rc_asset=[
            {"ticker": "SPY", "rc_pct": 0.40},
            {"ticker": "HYG", "rc_pct": 0.30},
            {"ticker": "TLT", "rc_pct": 0.20},
            {"ticker": "GLD", "rc_pct": 0.10},
        ],
        stress_report=_rich_stress_report(),
        portfolio_valid=True,
        portfolio_metrics={"max_drawdown": -0.22},
        portfolio_analytics={"es_95": -0.03},
        taxonomy_rows=_taxonomy_rows(),
    )

    risk_budget = xray["sections"]["risk_budget_view"]["items"]
    assert risk_budget[0]["ticker"] == "SPY"
    assert risk_budget[0]["risk_weight_gap"] == -0.04999999999999999
    hyg = next(item for item in risk_budget if item["ticker"] == "HYG")
    assert hyg["worst_stress_scenario"] == "recession_severe"
    assert hyg["worst_stress_loss_contribution_pct"] == -0.08

    flags = {item["name"]: item for item in xray["sections"]["hidden_risk_detector"]["items"]}
    assert flags["hidden_equity_beta"]["severity"] == "high"
    assert flags["single_asset_risk_concentration"]["severity"] == "high"
    assert flags["correlation_or_common_factor_concentration"]["severity"] == "high"
    assert flags["high_unexplained_factor_residual_risk"]["severity"] == "high"
    for flag in flags.values():
        assert {"severity", "fact", "interpretation", "next_test", "limitation"} <= set(flag)

    archetype = xray["sections"]["portfolio_archetype"]["items"][0]
    assert archetype["primary_archetype"] == "Equity Growth Portfolio"
    assert archetype["secondary_archetype"] is not None
    assert archetype["confidence"] in {"low", "medium", "high"}
    assert archetype["drivers"]
    assert "conflicting_signals" in archetype

    weakness = {item["risk"]: item for item in xray["sections"]["weakness_map"]["items"]}
    assert weakness["recession"]["severity"] == "high"
    assert weakness["equity_crash"]["severity"] == "high"
    assert weakness["liquidity"]["severity"] == "high"


def test_portfolio_xray_v2_degraded_inputs_are_not_overconfident() -> None:
    xray = build_portfolio_xray_v2(
        analysis_setup=None,
        weights={},
        rc_asset=[],
        stress_report=None,
        portfolio_valid=None,
    )

    assert xray["sections"]["asset_allocation"]["status"] == "unavailable"
    assert xray["sections"]["risk_diagnostics"]["status"] == "unavailable"
    assert xray["sections"]["factor_exposure"]["status"] == "unavailable"
    assert xray["sections"]["risk_budget_view"]["status"] == "unavailable"
    assert xray["sections"]["weakness_map"]["status"] == "partial"
