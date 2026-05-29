from __future__ import annotations

from typing import Any

import pandas as pd

from mvp_offline_fixtures import (
    minimal_block_2_2_analytics,
    minimal_block_2_2_drawdown_structure,
    minimal_block_2_2_metrics,
    refresh_analysis_subject_portfolio_xray,
    seed_cash5pct_block_2_2_subject_dir,
    snapshot_10y,
    write_json,
)
from src.block_2_2_portfolio_metrics import (
    BLOCK_2_2_ID,
    avg_pairwise_correlation,
    build_block_2_2_portfolio_metrics,
)


BLOCK_2_2_TOP_LEVEL_KEYS = frozenset(
    {
        "block",
        "analysis_subject",
        "analysis_mode",
        "investor_currency",
        "portfolio_behavior_snapshot",
        "return_risk_metrics",
        "drawdown_diagnostics",
        "tail_risk_diagnostics",
        "benchmark_dependence",
        "rolling_diagnostics",
        "correlation_breakdown",
        "data_quality_warnings",
        "informational_disclosures",
        "metadata",
    }
)


def assert_block_2_2_product_contract(block: dict[str, Any]) -> None:
    """Normative shape guard (portfolio_xray_diagnostics_spec.md §2.2.1)."""
    assert set(block) >= BLOCK_2_2_TOP_LEVEL_KEYS
    assert block["block"] == BLOCK_2_2_ID
    assert isinstance(block["data_quality_warnings"], list)
    assert isinstance(block["informational_disclosures"], list)

    behavior = block["portfolio_behavior_snapshot"]
    assert set(behavior) >= {"headline", "key_points", "overall_behavior_label"}
    assert isinstance(behavior["key_points"], list)

    rr = block["return_risk_metrics"]
    assert set(rr) >= {
        "portfolio_cagr",
        "vol_annual",
        "sharpe",
        "sortino",
        "treynor",
        "skewness",
        "kurtosis",
    }

    dd = block["drawdown_diagnostics"]
    assert set(dd) >= {
        "max_drawdown",
        "ttr_months",
        "recovered",
        "drawdown_depth",
        "drawdown_length",
        "recovery_months",
        "recovery_median",
        "recovery_p90",
        "pct_time_underwater",
        "longest_underwater",
        "count_drawdowns_gt_5",
        "count_drawdowns_gt_10",
        "count_drawdowns_gt_20",
    }

    tail = block["tail_risk_diagnostics"]
    assert set(tail) >= {"var_95", "var_99", "es_95", "es_99", "downside_deviation", "eee_10"}

    bench = block["benchmark_dependence"]
    assert set(bench) >= {
        "benchmark_ticker",
        "beta_portfolio",
        "beta_base",
        "corr_base",
        "downside_beta",
        "upside_beta",
    }

    rolling = block["rolling_diagnostics"]
    assert set(rolling) >= {"core_view", "advanced_available"}
    core = rolling["core_view"]
    assert set(core) == {"rolling_sharpe_36m", "rolling_volatility_12m", "rolling_beta_or_correlation"}
    assert isinstance(core["rolling_sharpe_36m"], dict)
    assert isinstance(core["rolling_volatility_12m"], dict)
    assert isinstance(core["rolling_beta_or_correlation"], dict)
    advanced = rolling["advanced_available"]
    assert isinstance(advanced, dict)
    assert set(advanced) >= {
        "rolling_sharpe_12m",
        "rolling_sortino_36m",
        "rolling_sortino_12m",
        "rolling_beta_36m",
        "rolling_beta_12m",
        "rolling_correlation_36m",
        "rolling_correlation_12m",
    }

    corr = block["correlation_breakdown"]
    assert set(corr) >= {
        "top3_highest_correlation_pairs",
        "top3_lowest_correlation_pairs",
        "avg_pairwise_correlation",
        "full_matrix_available",
        "full_matrix_ref",
    }
    assert isinstance(corr["top3_highest_correlation_pairs"], list)
    assert isinstance(corr["top3_lowest_correlation_pairs"], list)
    assert len(corr["top3_highest_correlation_pairs"]) <= 3
    assert len(corr["top3_lowest_correlation_pairs"]) <= 3

    metadata = block["metadata"]
    assert metadata.get("source") == "core_mvp_input"
    assert metadata.get("cash_proxy_used_for_real_cash") is False
    assert metadata.get("metric_quality_internal_only") is True


def _mvp_analysis_setup() -> dict[str, Any]:
    return {
        "version": "analysis_setup_v1",
        "portfolio_input": {
            "source_analysis_mode": "analyze_current_weights",
            "investor_currency": "USD",
            "analysis_subject_type": "current_portfolio",
        },
        "analysis_subject": {"type": "current_portfolio"},
        "analysis_portfolio": {"weights": {"SPY": 0.5, "BND": 0.5}},
    }


def test_build_block_2_2_contract_and_top_correlation_pairs_from_csv(tmp_path: Any) -> None:
    # Use output_dir_csv loading path, mirroring build_portfolio_xray_v2 integration.
    out_csv = tmp_path / "results_csv"
    out_csv.mkdir(parents=True, exist_ok=True)
    corr = pd.DataFrame(
        [[1.0, 0.55, 0.05], [0.55, 1.0, 0.92], [0.05, 0.92, 1.0]],
        index=["SPY", "BND", "GLD"],
        columns=["SPY", "BND", "GLD"],
    )
    corr.to_csv(out_csv / "correlation_matrix_10y.csv")

    metrics = minimal_block_2_2_metrics()
    analytics = minimal_block_2_2_analytics()
    dd = minimal_block_2_2_drawdown_structure()
    doc = build_block_2_2_portfolio_metrics(
        analysis_setup=_mvp_analysis_setup(),
        portfolio_metrics=metrics,
        portfolio_analytics=analytics,
        drawdown_structure=dd,
        output_dir_csv=out_csv,
        weights={"SPY": 0.5, "BND": 0.5},
    )

    assert_block_2_2_product_contract(doc)
    assert doc["metadata"]["primary_window_months"] == 120
    assert doc["correlation_breakdown"]["full_matrix_available"] is True
    assert doc["correlation_breakdown"]["full_matrix_ref"] == "correlation_matrix_10y.csv"

    highest = doc["correlation_breakdown"]["top3_highest_correlation_pairs"]
    lowest = doc["correlation_breakdown"]["top3_lowest_correlation_pairs"]
    assert highest[0] == {"ticker_a": "BND", "ticker_b": "GLD", "correlation": 0.92}
    assert lowest[0] == {"ticker_a": "GLD", "ticker_b": "SPY", "correlation": 0.05}
    assert doc["correlation_breakdown"]["avg_pairwise_correlation"] == 0.507


def test_avg_pairwise_correlation_helper() -> None:
    corr = pd.DataFrame(
        [[1.0, 0.55, 0.05], [0.55, 1.0, 0.92], [0.05, 0.92, 1.0]],
        index=["SPY", "BND", "GLD"],
        columns=["SPY", "BND", "GLD"],
    )
    assert avg_pairwise_correlation(corr) == 0.507


def test_build_block_2_2_top_correlation_pairs_from_in_memory_matrix() -> None:
    corr = pd.DataFrame(
        [[1.0, 0.55, 0.05], [0.55, 1.0, 0.92], [0.05, 0.92, 1.0]],
        index=["SPY", "BND", "GLD"],
        columns=["SPY", "BND", "GLD"],
    )

    doc = build_block_2_2_portfolio_metrics(
        analysis_setup=_mvp_analysis_setup(),
        portfolio_metrics=minimal_block_2_2_metrics(),
        portfolio_analytics=minimal_block_2_2_analytics(),
        drawdown_structure=minimal_block_2_2_drawdown_structure(),
        output_dir_csv=None,
        correlation_matrix=corr,
        correlation_matrix_ref="runtime:correlation_matrix_10y",
        weights={"SPY": 0.5, "BND": 0.5},
    )

    assert doc["correlation_breakdown"]["full_matrix_available"] is True
    assert doc["correlation_breakdown"]["full_matrix_ref"] == "runtime:correlation_matrix_10y"
    assert doc["correlation_breakdown"]["top3_highest_correlation_pairs"][0] == {
        "ticker_a": "BND",
        "ticker_b": "GLD",
        "correlation": 0.92,
    }
    assert doc["correlation_breakdown"]["avg_pairwise_correlation"] == 0.507
    assert not any("correlation matrix is missing" in w.lower() for w in doc["data_quality_warnings"])


def test_build_block_2_2_missing_correlation_matrix_adds_warning() -> None:
    doc = build_block_2_2_portfolio_metrics(
        analysis_setup=_mvp_analysis_setup(),
        portfolio_metrics=minimal_block_2_2_metrics(),
        portfolio_analytics=minimal_block_2_2_analytics(),
        drawdown_structure=minimal_block_2_2_drawdown_structure(),
        output_dir_csv=None,
        weights={"SPY": 0.5, "BND": 0.5},
    )
    assert_block_2_2_product_contract(doc)
    assert doc["correlation_breakdown"]["full_matrix_available"] is False
    assert doc["correlation_breakdown"]["top3_highest_correlation_pairs"] == []
    assert doc["correlation_breakdown"]["top3_lowest_correlation_pairs"] == []
    assert any("correlation matrix is missing" in w.lower() for w in doc["data_quality_warnings"])


def _assert_extended_drawdown_populated(dd_diag: dict[str, Any]) -> None:
    assert dd_diag["pct_time_underwater"] is not None
    assert dd_diag["count_drawdowns_gt_5"] is not None
    assert dd_diag["count_drawdowns_gt_10"] is not None
    assert dd_diag["count_drawdowns_gt_20"] is not None
    assert dd_diag["recovery_median"] is not None
    assert dd_diag["recovery_p90"] is not None
    assert dd_diag["longest_underwater"] is not None


def test_block_2_2_drawdown_from_analytics_when_top_level_missing() -> None:
    dd = minimal_block_2_2_drawdown_structure()
    analytics = minimal_block_2_2_analytics()
    analytics["drawdown_structure"] = dd
    doc = build_block_2_2_portfolio_metrics(
        analysis_setup=_mvp_analysis_setup(),
        portfolio_metrics=minimal_block_2_2_metrics(),
        portfolio_analytics=analytics,
        drawdown_structure=None,
        weights={"SPY": 0.5, "BND": 0.5},
    )
    _assert_extended_drawdown_populated(doc["drawdown_diagnostics"])
    assert doc["drawdown_diagnostics"]["pct_time_underwater"] == 0.14
    assert doc["drawdown_diagnostics"]["count_drawdowns_gt_5"] == 3
    assert doc["drawdown_diagnostics"]["drawdown_depth"] == -0.21


def test_block_2_2_top_level_drawdown_structure_takes_precedence() -> None:
    top_level = minimal_block_2_2_drawdown_structure()
    top_level["summary"]["pct_time_underwater"] = 0.99
    analytics = minimal_block_2_2_analytics()
    analytics["drawdown_structure"] = minimal_block_2_2_drawdown_structure()
    doc = build_block_2_2_portfolio_metrics(
        analysis_setup=_mvp_analysis_setup(),
        portfolio_metrics=minimal_block_2_2_metrics(),
        portfolio_analytics=analytics,
        drawdown_structure=top_level,
        weights={"SPY": 0.5, "BND": 0.5},
    )
    assert doc["drawdown_diagnostics"]["pct_time_underwater"] == 0.99


def test_block_2_2_xray_from_snapshot_with_nested_drawdown_only(tmp_path: Any) -> None:
    """Live path: drawdown_structure only under snapshot analytics, not top-level."""
    subject_dir = tmp_path / "analysis_subject"
    subject_dir.mkdir(parents=True, exist_ok=True)
    dd = minimal_block_2_2_drawdown_structure()
    analytics = minimal_block_2_2_analytics()
    analytics["drawdown_structure"] = dd
    snap = snapshot_10y(minimal_block_2_2_metrics())
    snap["analytics"] = analytics
    write_json(subject_dir / "snapshot_10y.json", snap)
    xray = refresh_analysis_subject_portfolio_xray(subject_dir)
    block = xray.get("block_2_2_portfolio_metrics")
    assert isinstance(block, dict)
    _assert_extended_drawdown_populated(block["drawdown_diagnostics"])


def test_block_2_2_real_cash_treatment_surfaces_informational_disclosure_and_metadata(tmp_path: Any) -> None:
    payload = seed_cash5pct_block_2_2_subject_dir(tmp_path / "analysis_subject")
    # Re-read analysis_setup from written run_metadata.json to avoid relying on helper internals.
    import json

    run_meta = json.loads((tmp_path / "analysis_subject" / "run_metadata.json").read_text(encoding="utf-8"))
    analysis_setup = run_meta["analysis_setup"]

    doc = build_block_2_2_portfolio_metrics(
        analysis_setup=analysis_setup,
        portfolio_metrics=payload["metrics"],
        portfolio_analytics=payload["analytics"],
        drawdown_structure=payload["drawdown"],
        output_dir_csv=tmp_path / "results_csv",
        weights=None,
    )
    assert_block_2_2_product_contract(doc)
    assert doc["metadata"]["cash_treatment"] == "real_cash_position_if_present"
    assert any("real cash positions" in w.lower() for w in doc["informational_disclosures"])

