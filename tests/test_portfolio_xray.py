from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.generated_output_qa import (
    scan_portfolio_xray_html_text,
    scan_portfolio_xray_report_text,
)
from src.portfolio_xray import (
    PORTFOLIO_XRAY_VERSION,
    XRAY_SECTION_KEYS,
    XRAY_THRESHOLDS,
    build_portfolio_xray_summary,
    build_portfolio_xray_v2,
    format_portfolio_xray_commentary,
    format_portfolio_xray_html,
    format_portfolio_xray_text,
    load_rc_vol_map_from_csv,
    resolve_rc_asset_for_xray,
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
    assert scan_portfolio_xray_report_text(txt_body, rel_path="report.txt").ok()
    assert scan_portfolio_xray_html_text(html_body, rel_path="report.html").ok()
    assert "PORTFOLIO X-RAY SUMMARY" in txt_body
    assert "Capital concentration" in txt_body
    assert "Portfolio Metrics / Risk Diagnostics" in txt_body
    assert 'class="xray-section"' in html_body
    assert "Asset Allocation Summary" in html_body
    assert "<pre>" not in html_body.lower() or "xray-summary" not in html_body.lower()
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
                "pnl_by_factor_pct": {"eq": -0.07, "credit": -0.02},
            },
            {
                "scenario_id": "recession_severe",
                "portfolio_pnl_pct": -0.14,
                "top1_rc_asset": "HYG",
                "top1_rc_pct": 0.42,
                "top3_rc_sum_pct": 0.70,
                "pnl_by_asset_pct": {"SPY": -0.05, "TLT": 0.01, "HYG": -0.08, "GLD": -0.01},
                "pnl_by_factor_pct": {"eq": -0.10, "credit": -0.04},
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
            },
            "residual": {
                "covariance_pca": {
                    "pc1_explained_variance_ratio": 0.52,
                }
            },
        },
        "factor_beta_shock_oos": {
            "summary": {
                "mean_abs_error_5y": 0.03,
                "n_episodes_with_real_pnl": 4,
            }
        },
    }


def test_portfolio_xray_v2_tail_risk_disclosure_in_risk_diagnostics() -> None:
    xray = build_portfolio_xray_v2(
        analysis_setup=_analysis_setup(),
        weights={"SPY": 1.0},
        rc_asset=[],
        stress_report={},
        portfolio_valid=True,
        portfolio_metrics={"cagr": 0.08, "max_drawdown": -0.15},
        portfolio_analytics={
            "tail_risk": {
                "method": "historical",
                "frequency": "daily",
                "window_months": 120,
                "window_label": "10y",
                "n_obs": 2520,
                "metric_available": True,
                "var_95": -0.012,
                "es_95": -0.015,
                "var_99": -0.018,
                "es_99": -0.022,
            },
            "eee_10pct": 85.0,
        },
    )
    section = xray["sections"]["risk_diagnostics"]
    types = [item.get("type") for item in section["items"]]
    assert "tail_risk" in types
    tail = next(i for i in section["items"] if i.get("type") == "tail_risk")
    assert tail.get("frequency") == "daily"
    assert tail.get("method") == "historical"
    assert tail.get("window_label") == "10y"


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
        portfolio_analytics={
            "tail_risk": {
                "method": "historical",
                "frequency": "daily",
                "window_label": "10y",
                "metric_available": True,
                "var_95": -0.02,
                "es_95": -0.03,
            },
        },
        taxonomy_rows=_taxonomy_rows(),
        taxonomy_sources={ticker: "test_taxonomy" for ticker in _taxonomy_rows()},
    )

    assert xray["version"] == PORTFOLIO_XRAY_VERSION
    assert xray["diagnostic_only"] is True
    assert "does not optimize" in xray["diagnostic_only_disclaimer"]
    assert "top1_rc_high" in xray["thresholds"]
    assert xray["thresholds"]["top1_rc_high"] == XRAY_THRESHOLDS["top1_rc_high"]
    assert list(xray["sections"]) == list(XRAY_SECTION_KEYS)
    required_section_keys = {"status", "data_sources_used", "warnings", "items", "limitations"}
    for section in xray["sections"].values():
        assert required_section_keys <= set(section)
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
        portfolio_analytics={
            "es_95": -0.03,
            "tail_risk": {
                "method": "historical",
                "frequency": "daily",
                "window_label": "10y",
                "metric_available": True,
                "var_95": -0.012,
                "es_95": -0.028,
            },
        },
        taxonomy_rows=_taxonomy_rows(),
    )

    risk_budget = xray["sections"]["risk_budget_view"]["items"]
    assert risk_budget[0]["ticker"] == "SPY"
    assert risk_budget[0]["risk_weight_gap"] == -0.04999999999999999
    hyg = next(item for item in risk_budget if item["ticker"] == "HYG")
    assert hyg["worst_stress_scenario"] == "recession_severe"
    assert hyg["worst_stress_loss_contribution_pct"] == -0.08

    hidden = xray["sections"]["hidden_risk_detector"]
    assert hidden["confidence"] in {"low", "medium", "high"}
    assert hidden["evidence_count"] >= 8
    assert hidden["flagged_count"] >= 4
    assert hidden["below_threshold_count"] >= 1

    assessments = {item["name"]: item for item in hidden["items"]}
    assert len(assessments) == 11
    assert assessments["hidden_equity_beta"]["flagged"] is True
    assert assessments["hidden_equity_beta"]["severity"] == "high"
    assert assessments["single_asset_risk_concentration"]["severity"] == "high"
    assert assessments["correlation_or_common_factor_concentration"]["severity"] == "high"
    assert assessments["macro_factor_dependency"]["flagged"] is True
    assert assessments["tail_risk"]["flagged"] is True
    assert assessments["credit_concentration"]["assessment_status"] == "below_threshold"
    assert assessments["credit_concentration"]["flagged"] is False
    for row in assessments.values():
        assert {"severity", "fact", "interpretation", "next_test", "limitation", "flagged", "assessment_status"} <= set(
            row
        )

    archetype = xray["sections"]["portfolio_archetype"]["items"][0]
    assert archetype["primary_archetype"] == "Equity Growth Portfolio"
    assert archetype["secondary_archetype"] is not None
    assert archetype["confidence"] in {"low", "medium", "high"}
    assert archetype["positive_evidence"]
    assert archetype["drivers"] == archetype["positive_evidence"]
    assert "negative_evidence" in archetype
    assert "archetype_scorecard" in archetype
    assert len(archetype["archetype_scorecard"]) >= 8
    assert any(row.get("fit") == "primary" for row in archetype["archetype_scorecard"])
    assert "conflicting_signals" in archetype

    weakness = {item["risk"]: item for item in xray["sections"]["weakness_map"]["items"]}
    assert weakness["recession"]["severity"] == "high"
    assert weakness["equity_crash"]["severity"] == "high"
    assert weakness["liquidity"]["severity"] == "high"
    recession = weakness["recession"]
    assert recession["exposure_present"] is True
    assert recession["adverse_evidence"] is True
    assert "recession_severe" in recession["scenario_coverage"]["scenarios_present"]
    assert recession["top_asset_loss_drivers"][0]["ticker"] == "HYG"

    equity = weakness["equity_crash"]
    assert equity["exposure_present"] is True
    assert "equity_shock" in equity["scenario_coverage"]["scenarios_present"]
    assert equity["top_factor_drivers"]

    liquidity = weakness["liquidity"]
    assert liquidity["adverse_evidence"] is True
    assert liquidity["exposure_present"] is True
    assert "liquidity_shock" in liquidity["scenario_coverage"]["scenarios_missing"]
    assert "crypto_shock" not in weakness


def test_hidden_risk_detector_v2_low_risk_portfolio_mostly_below_threshold() -> None:
    xray = build_portfolio_xray_v2(
        analysis_setup=_analysis_setup(),
        weights={"BIL": 0.55, "SHY": 0.45},
        rc_asset=[
            {"ticker": "BIL", "rc_pct": 0.18},
            {"ticker": "SHY", "rc_pct": 0.17},
        ],
        stress_report={
            "factor_betas_5y": {"beta_eq": 0.10, "beta_rr": 0.05},
            "portfolio_pca": {
                "raw": {"covariance_pca": {"pc1_explained_variance_ratio": 0.25}},
                "residual": {"covariance_pca": {"pc1_explained_variance_ratio": 0.20}},
            },
            "scenario_results": [
                {
                    "scenario_id": "equity_shock",
                    "portfolio_pnl_pct": -0.02,
                    "top1_rc_asset": "SHY",
                    "top1_rc_pct": 0.18,
                }
            ],
        },
        portfolio_valid=True,
        portfolio_analytics={
            "tail_risk": {
                "metric_available": True,
                "method": "historical",
                "frequency": "daily",
                "es_95": -0.008,
            }
        },
        taxonomy_rows={
            "BIL": {
                "ticker": "BIL",
                "asset_class": "fixed_income",
                "main_risk_factor": "cash",
                "duration_bucket": "short",
                "risk_role": ["cash"],
            },
            "SHY": {
                "ticker": "SHY",
                "asset_class": "fixed_income",
                "main_risk_factor": "real_rates",
                "duration_bucket": "short",
                "risk_role": ["defensive"],
            },
        },
    )
    hidden = xray["sections"]["hidden_risk_detector"]
    assessments = {row["name"]: row for row in hidden["items"]}
    assert assessments["hidden_equity_beta"]["assessment_status"] == "below_threshold"
    assert assessments["hidden_equity_beta"]["flagged"] is False
    assert assessments["correlation_or_common_factor_concentration"]["assessment_status"] == "below_threshold"
    assert assessments["tail_risk"]["assessment_status"] == "below_threshold"
    assert hidden["flagged_count"] == 0


def test_resolve_rc_asset_prefers_full_csv_over_snapshot_top5(tmp_path: Path) -> None:
    csv_dir = tmp_path / "results_csv"
    csv_dir.mkdir()
    pd.DataFrame(
        {
            "rc_vol": {
                "SPY": 0.22,
                "TLT": 0.18,
                "HYG": 0.16,
                "GLD": 0.14,
                "BND": 0.12,
                "BIL": 0.08,
            }
        }
    ).to_csv(csv_dir / "rc_vol_10y.csv")

    rows, sources = resolve_rc_asset_for_xray(
        [{"ticker": "SPY", "rc_pct": 0.9}],
        output_dir_csv=csv_dir,
    )
    by_ticker = {row["ticker"]: row["rc_pct"] for row in rows}

    assert len(by_ticker) == 6
    assert by_ticker["SPY"] == 0.22
    assert any("rc_vol_10y.csv" in source for source in sources)


def test_portfolio_xray_v2_risk_budget_covers_all_positive_weights_from_csv(
    tmp_path: Path,
) -> None:
    csv_dir = tmp_path / "results_csv"
    csv_dir.mkdir()
    pd.DataFrame(
        {
            "rc_vol": {
                "SPY": 0.30,
                "TLT": 0.25,
                "HYG": 0.20,
                "GLD": 0.15,
                "BND": 0.10,
            }
        }
    ).to_csv(csv_dir / "rc_vol_10y.csv")

    weights = {"SPY": 0.30, "TLT": 0.25, "HYG": 0.20, "GLD": 0.15, "BND": 0.10}
    xray = build_portfolio_xray_v2(
        analysis_setup=_analysis_setup(),
        weights=weights,
        rc_asset=[{"ticker": "SPY", "rc_pct": 0.9}],
        stress_report=_rich_stress_report(),
        portfolio_valid=True,
        output_dir_csv=csv_dir,
    )

    risk_budget = {
        item["ticker"]: item["rc_vol"]
        for item in xray["sections"]["risk_budget_view"]["items"]
        if item.get("type") == "asset_risk_budget"
    }
    assert set(risk_budget) == set(weights)
    assert all(value is not None for value in risk_budget.values())
    assert any("rc_vol_10y.csv" in src for src in xray["sections"]["risk_budget_view"]["data_sources_used"])


def test_portfolio_xray_v2_kalman_reads_factor_betas_kalman_latest() -> None:
    stress = _rich_stress_report()
    stress["factor_betas_kalman"] = {
        "status": "available",
        "latest": {"beta_eq": 0.81, "beta_credit": 0.42},
        "latest_raw": {"beta_eq": 0.95, "beta_credit": 0.50},
    }
    xray = build_portfolio_xray_v2(
        analysis_setup=_analysis_setup(),
        weights={"SPY": 1.0},
        rc_asset=[],
        stress_report=stress,
        portfolio_valid=True,
    )
    exposure = {
        item["beta_key"]: item.get("kalman_current_beta")
        for item in xray["sections"]["factor_exposure"]["items"]
        if item.get("type") == "factor_exposure"
    }
    assert exposure["beta_eq"] == 0.81
    assert exposure["beta_credit"] == 0.42


def test_load_rc_vol_map_from_csv_fallback_window(tmp_path: Path) -> None:
    csv_dir = tmp_path / "results_csv"
    csv_dir.mkdir()
    pd.DataFrame({"rc_vol": {"AAA": 0.5, "BBB": 0.5}}).to_csv(csv_dir / "rc_vol_5y.csv")

    loaded = load_rc_vol_map_from_csv(csv_dir)
    assert loaded == {"AAA": 0.5, "BBB": 0.5}


def test_weakness_map_v2_low_risk_portfolio_not_overstated() -> None:
    xray = build_portfolio_xray_v2(
        analysis_setup=_analysis_setup(),
        weights={"BIL": 0.55, "SHY": 0.45},
        rc_asset=[],
        stress_report={
            "factor_betas_5y": {"beta_eq": 0.08, "beta_rr": 0.04},
            "scenario_results": [
                {
                    "scenario_id": "equity_shock",
                    "portfolio_pnl_pct": -0.02,
                    "pnl_by_asset_pct": {"BIL": -0.005, "SHY": -0.015},
                    "pnl_by_factor_pct": {"eq": -0.01},
                }
            ],
        },
        portfolio_valid=True,
        portfolio_analytics={
            "tail_risk": {
                "metric_available": True,
                "method": "historical",
                "frequency": "daily",
                "es_95": -0.006,
            }
        },
        taxonomy_rows={
            "BIL": {
                "ticker": "BIL",
                "asset_class": "fixed_income",
                "main_risk_factor": "cash",
                "risk_bucket": "cash",
            },
            "SHY": {
                "ticker": "SHY",
                "asset_class": "fixed_income",
                "main_risk_factor": "real_rates",
                "risk_bucket": "rates",
            },
        },
    )
    weakness = {item["risk"]: item for item in xray["sections"]["weakness_map"]["items"]}
    equity = weakness["equity_crash"]
    assert equity["severity"] == "low"
    assert equity["adverse_evidence"] is False
    assert equity["exposure_present"] is False
    rates = weakness["rates"]
    assert rates["exposure_present"] is True
    assert rates["adverse_evidence"] is False
    assert rates["severity"] == "low"
    assert "crypto_shock" not in weakness


def test_weakness_map_v2_crypto_row_only_with_crypto_exposure() -> None:
    crypto_taxonomy = {
        "IBIT": {
            "ticker": "IBIT",
            "asset_class": "crypto",
            "main_risk_factor": "crypto_beta",
            "risk_bucket": "crypto",
        }
    }
    xray = build_portfolio_xray_v2(
        analysis_setup=_analysis_setup(),
        weights={"IBIT": 0.10, "SPY": 0.90},
        rc_asset=[],
        stress_report={
            "factor_betas_5y": {"beta_eq": 0.85},
            "scenario_results": [
                {
                    "scenario_id": "equity_shock",
                    "portfolio_pnl_pct": -0.08,
                    "pnl_by_asset_pct": {"IBIT": -0.03, "SPY": -0.05},
                }
            ],
        },
        portfolio_valid=True,
        taxonomy_rows={**_taxonomy_rows(), **crypto_taxonomy},
    )
    weakness = {item["risk"]: item for item in xray["sections"]["weakness_map"]["items"]}
    assert "crypto_shock" in weakness
    assert weakness["crypto_shock"]["exposure_present"] is True

    xray_no_crypto = build_portfolio_xray_v2(
        analysis_setup=_analysis_setup(),
        weights={"SPY": 1.0},
        rc_asset=[],
        stress_report={"factor_betas_5y": {"beta_eq": 0.85}, "scenario_results": []},
        portfolio_valid=True,
        taxonomy_rows=_taxonomy_rows(),
    )
    assert "crypto_shock" not in {
        item["risk"] for item in xray_no_crypto["sections"]["weakness_map"]["items"]
    }


def test_weakness_map_v2_missing_mapped_scenarios_surface_warnings() -> None:
    xray = build_portfolio_xray_v2(
        analysis_setup=_analysis_setup(),
        weights={"SPY": 1.0},
        rc_asset=[],
        stress_report={
            "factor_betas_5y": {"beta_eq": 0.70},
            "scenario_results": [
                {
                    "scenario_id": "equity_shock",
                    "portfolio_pnl_pct": -0.09,
                    "pnl_by_asset_pct": {"SPY": -0.09},
                }
            ],
        },
        portfolio_valid=True,
        taxonomy_rows=_taxonomy_rows(),
    )
    recession = next(
        item for item in xray["sections"]["weakness_map"]["items"] if item["risk"] == "recession"
    )
    assert "recession_severe" in recession["scenario_coverage"]["scenarios_missing"]
    assert recession["missing_inputs"]
    assert any("missing stress scenarios" in msg for msg in recession["missing_inputs"])


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


def _archetype_item(xray: dict) -> dict:
    items = xray["sections"]["portfolio_archetype"]["items"]
    assert items
    return items[0]


def test_archetype_v2_balanced_scorecard() -> None:
    xray = build_portfolio_xray_v2(
        analysis_setup=_analysis_setup(),
        weights={"SPY": 0.40, "TLT": 0.35, "BND": 0.25},
        rc_asset=[
            {"ticker": "SPY", "rc_pct": 0.34},
            {"ticker": "TLT", "rc_pct": 0.33},
            {"ticker": "BND", "rc_pct": 0.33},
        ],
        stress_report={"factor_betas_5y": {"beta_eq": 0.45, "beta_rr": 0.35}},
        portfolio_valid=True,
        taxonomy_rows=_taxonomy_rows(),
    )
    archetype = _archetype_item(xray)
    assert archetype["primary_archetype"] == "Balanced 60/40-like"
    assert archetype["positive_evidence"]
    assert any("balanced capital mix" in line for line in archetype["positive_evidence"])
    balanced = next(
        row for row in archetype["archetype_scorecard"] if row["archetype"] == "Balanced 60/40-like"
    )
    assert balanced["fit"] == "primary"


def test_archetype_v2_duration_heavy_defensive() -> None:
    rows = {
        **_taxonomy_rows(),
        "BND": {
            "ticker": "BND",
            "asset_class": "fixed_income",
            "region": "US",
            "currency_exposure": "USD",
            "sector": "none",
            "risk_role": ["defensive"],
            "main_risk_factor": "credit",
            "secondary_risk_factors": [],
            "duration_bucket": "intermediate",
            "credit_quality": "IG",
            "subtype": "aggregate",
        },
        "BIL": {
            "ticker": "BIL",
            "asset_class": "fixed_income",
            "region": "US",
            "currency_exposure": "USD",
            "sector": "none",
            "risk_role": ["cash"],
            "main_risk_factor": "cash",
            "secondary_risk_factors": [],
            "duration_bucket": "short",
            "credit_quality": "Treasury",
            "subtype": "t_bills",
        },
    }
    xray = build_portfolio_xray_v2(
        analysis_setup=_analysis_setup(),
        weights={"TLT": 0.50, "BND": 0.35, "BIL": 0.15},
        rc_asset=[
            {"ticker": "TLT", "rc_pct": 0.45},
            {"ticker": "BND", "rc_pct": 0.35},
            {"ticker": "BIL", "rc_pct": 0.20},
        ],
        stress_report={"factor_betas_5y": {"beta_eq": 0.12, "beta_rr": 0.55}},
        portfolio_valid=True,
        taxonomy_rows=rows,
    )
    archetype = _archetype_item(xray)
    assert archetype["primary_archetype"] == "Duration-heavy Defensive"
    assert any("fixed income" in line for line in archetype["positive_evidence"])


def test_archetype_v2_inflation_sensitive_with_regime_conflict() -> None:
    tip_row = {
        "ticker": "TIP",
        "asset_class": "fixed_income",
        "region": "US",
        "currency_exposure": "USD",
        "sector": "none",
        "risk_role": ["inflation_hedge"],
        "main_risk_factor": "inflation",
        "secondary_risk_factors": [],
        "duration_bucket": "intermediate",
        "credit_quality": "Treasury",
        "subtype": "tips",
    }
    xray = build_portfolio_xray_v2(
        analysis_setup=_analysis_setup(),
        weights={"TIP": 0.70, "SPY": 0.30},
        rc_asset=[{"ticker": "TIP", "rc_pct": 0.55}, {"ticker": "SPY", "rc_pct": 0.45}],
        stress_report={
            "factor_betas_5y": {"beta_eq": 0.25, "beta_inf": 0.42, "beta_cmd": 0.15, "beta_rr": 0.40},
            "scenario_results": [
                {
                    "scenario_id": "inflation_stagflation",
                    "portfolio_pnl_pct": -0.13,
                    "pnl_by_asset_pct": {"TIP": -0.09, "SPY": -0.04},
                    "pnl_by_factor_pct": {"inf": -0.10},
                },
                {
                    "scenario_id": "rates_shock",
                    "portfolio_pnl_pct": -0.11,
                    "pnl_by_asset_pct": {"TIP": -0.08, "SPY": -0.03},
                    "pnl_by_factor_pct": {"rr": -0.09},
                },
            ],
        },
        portfolio_valid=True,
        taxonomy_rows={**_taxonomy_rows(), "TIP": tip_row},
    )
    archetype = _archetype_item(xray)
    assert archetype["primary_archetype"] == "Inflation-sensitive"
    assert archetype["negative_evidence"]
    assert any("weakness map" in line for line in archetype["negative_evidence"])
    assert archetype["conflict_summary"]
    regime_conflicts = [row for row in archetype["conflicting_signals"] if row.get("related_weakness")]
    assert regime_conflicts
    assert any(row.get("related_weakness") in {"inflation", "rates"} for row in regime_conflicts)


def test_archetype_v2_pseudo_diversified_concentration() -> None:
    xray = build_portfolio_xray_v2(
        analysis_setup=_analysis_setup(),
        weights={"SPY": 0.20, "TLT": 0.20, "HYG": 0.20, "GLD": 0.20, "BND": 0.20},
        rc_asset=[{"ticker": "SPY", "rc_pct": 0.52}],
        stress_report={
            "factor_betas_5y": {"beta_eq": 0.40},
            "portfolio_pca": {
                "raw": {"covariance_pca": {"pc1_explained_variance_ratio": 0.72, "pc1_severity": "high"}}
            },
            "scenario_results": [],
        },
        portfolio_valid=True,
        taxonomy_rows=_taxonomy_rows(),
    )
    archetype = _archetype_item(xray)
    assert archetype["primary_archetype"] == "Pseudo-diversified Portfolio"
    assert any("RC_vol" in line or "PCA" in line for line in archetype["positive_evidence"])


def test_archetype_v2_equity_growth_and_competing_label_conflicts() -> None:
    xray = build_portfolio_xray_v2(
        analysis_setup=_analysis_setup(),
        weights={"SPY": 0.75, "HYG": 0.15, "GLD": 0.10},
        rc_asset=[{"ticker": "SPY", "rc_pct": 0.62}],
        stress_report=_rich_stress_report(),
        portfolio_valid=True,
        portfolio_metrics={"max_drawdown": -0.22},
        taxonomy_rows=_taxonomy_rows(),
    )
    archetype = _archetype_item(xray)
    assert archetype["primary_archetype"] == "Equity Growth Portfolio"
    competing = [row for row in archetype["conflicting_signals"] if row.get("tension") == "competing_label"]
    assert competing
    assert all(row.get("explanation") for row in competing)


def test_format_portfolio_xray_v2_structured_surfaces() -> None:
    xray = build_portfolio_xray_v2(
        analysis_setup=_analysis_setup(),
        weights={"SPY": 0.45, "TLT": 0.30, "HYG": 0.15, "GLD": 0.10},
        rc_asset=[{"ticker": "SPY", "rc_pct": 0.40}],
        stress_report=_rich_stress_report(),
        portfolio_valid=True,
        portfolio_metrics={"max_drawdown": -0.22},
        taxonomy_rows=_taxonomy_rows(),
    )
    text = format_portfolio_xray_text(xray)
    html = format_portfolio_xray_html(xray)
    commentary = format_portfolio_xray_commentary(xray)

    assert scan_portfolio_xray_report_text(text).ok()
    assert scan_portfolio_xray_html_text(html).ok()
    assert "Ticker" in text and "Weight" in text
    assert 'class="xray-section"' in html
    assert "Portfolio X-Ray (diagnostic-only)" in commentary
    assert "status=partial" not in commentary
    assert len(commentary) < len(text)
