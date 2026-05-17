from __future__ import annotations

import json
from pathlib import Path

import yaml

from src.analysis_setup import build_analysis_setup
from src.config import load_validated_config
from src.config_schema import validate_config
from src.input_assumptions import (
    build_input_assumptions_from_analysis_setup,
    build_input_assumptions_summary,
)
from src.io_export import export_run_metadata


def _write_yaml(path: Path, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def test_analyze_current_weights_maps_current_weights_to_report_weights() -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "analyze_current_weights",
            "tickers": ["VOO", "BND"],
            "current_weights": {"VOO": "60%", "BND": "40%"},
        }
    )

    assert cfg.analysis_mode == "analyze_current_weights"
    assert cfg.current_weights == {"VOO": 0.6, "BND": 0.4}
    assert cfg.weights == {"VOO": 0.6, "BND": 0.4}
    assert cfg.weights_source == "config.current_weights"


def test_analyze_current_weights_does_not_merge_stale_generated_weights(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yml"
    weights_dir = tmp_path / "Main portfolio"
    weights_dir.mkdir(parents=True)
    _write_yaml(
        config_path,
        {
            "investor_currency": "USD",
            "analysis_mode": "analyze_current_weights",
            "tickers": ["VOO", "BND"],
            "output_dir_final": "Main portfolio",
            "current_weights": {"VOO": 0.7, "BND": 0.3},
        },
    )
    _write_yaml(weights_dir / "portfolio_weights.yml", {"VOO": 0.1, "BND": 0.9})

    cfg = load_validated_config(config_path)

    assert cfg.weights == {"VOO": 0.7, "BND": 0.3}
    assert cfg.weights_source == "config.current_weights"


def test_input_assumptions_summary_contains_input_mode_and_known_gap() -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "tickers": ["VOO", "BND"],
            "weights": {"VOO": 0.5, "BND": 0.5},
            "returns_frequency": "weekly",
            "horizon_years": 10,
        }
    )

    summary = build_input_assumptions_summary(
        cfg,
        portfolio_weights=cfg.weights,
        weights_source="config.weights",
        cash_proxy_ticker="BIL",
        rf_source="FRED:DTB3",
        analysis_end="2026-04-30",
        windows_months=[36, 60, 120],
        returns_frequency="weekly",
        periods_per_year=52,
        run_context="report",
    )

    assert summary["portfolio_input"]["analysis_mode"] == "optimize_from_universe"
    assert summary["source_analysis_setup_version"] == "analysis_setup_v1"
    assert summary["portfolio_input"]["reported_weights"]["status"] == "fully_invested"
    assert summary["currency_and_market"]["cash_proxy_ticker"] == "BIL"
    assert summary["mandate_and_constraints"]["horizon_role"] == "report_context_only_not_optimizer_constraint"
    assert summary["calculation_assumptions"]["returns_frequency"] == "weekly"
    assert summary["current_v1_gaps"]["transaction_costs"] == "not_implemented"


def test_export_run_metadata_includes_input_assumptions(tmp_path: Path) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "tickers": ["VOO", "BND"],
            "weights": {"VOO": 0.6, "BND": 0.4},
        }
    )
    derived = {
        "resolved_cash_proxy_ticker": "BIL",
        "resolved_rf_source": "FRED:DTB3",
        "resolved_local_benchmark_map": {"VOO": "SPY", "BND": "BND"},
        "windows_months": [36, 60, 120],
        "returns_frequency": "monthly",
        "periods_per_year": 12,
    }

    path = export_run_metadata(
        tmp_path,
        cfg,
        derived,
        analysis_end="2026-04-30",
        run_timestamp="2026-05-15T18:16:00",
        portfolio_weights=cfg.weights,
        weights_source="config.weights",
    )

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["analysis_setup"]["version"] == "analysis_setup_v1"
    assert data["input_assumptions"]["version"] == "input_assumptions_v1"
    assert data["input_assumptions"]["source_analysis_setup_version"] == "analysis_setup_v1"
    assert data["input_assumptions"]["portfolio_input"]["reported_weights_source"] == "config.weights"


def test_analysis_setup_contract_shape_and_projection() -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "analyze_current_weights",
            "tickers": ["VOO", "BND"],
            "current_weights": {"VOO": 0.6, "BND": 0.4},
            "horizon_years": 5,
        }
    )

    setup = build_analysis_setup(
        cfg,
        cash_proxy_ticker="BIL",
        rf_source="FRED:DTB3",
        analysis_end="2026-04-30",
        windows_months=[36, 60, 120],
        returns_frequency="monthly",
        periods_per_year=12,
        run_context="report",
    )

    assert setup["version"] == "analysis_setup_v1"
    assert set(
        [
            "portfolio_input",
            "analysis_portfolio",
            "resolved_mandate",
            "resolved_assumptions",
            "validation_result",
        ]
    ).issubset(setup)
    assert setup["portfolio_input"]["product_input_case"] == "user_current"
    assert setup["analysis_portfolio"]["portfolio_role"] == "user_current_portfolio"
    assert setup["analysis_portfolio"]["recommendation_status"] == "diagnostic_current_portfolio_not_recommendation"
    assert setup["portfolio_input"]["investment_horizon_years"]["affects_calculations"] is False

    projection = build_input_assumptions_from_analysis_setup(setup)
    assert projection["version"] == "input_assumptions_v1"
    assert projection["source_analysis_setup_version"] == "analysis_setup_v1"
    assert projection["portfolio_input"]["analysis_portfolio_role"] == "user_current_portfolio"


def test_universe_only_analysis_setup_creates_equal_weight_baseline_not_recommendation() -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "tickers": ["VOO", "BND", "GLD"],
        }
    )

    setup = build_analysis_setup(cfg, cash_proxy_ticker="BIL", rf_source="FRED:DTB3")

    assert setup["portfolio_input"]["product_input_case"] == "universe_only"
    assert setup["analysis_portfolio"]["portfolio_role"] == "equal_weight_initial_baseline"
    assert setup["analysis_portfolio"]["recommendation_status"] == "baseline_not_recommendation"
    assert setup["analysis_portfolio"]["weight_source"] == "system.equal_weight_initial_baseline"
    assert setup["analysis_portfolio"]["weight_status"]["status"] == "fully_invested"
    assert setup["validation_result"]["no_silent_behavior_change"] is True


def test_optimize_from_universe_with_generated_weights_preserves_current_repo_behavior() -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "tickers": ["VOO", "BND"],
        }
    )

    setup = build_analysis_setup(
        cfg,
        portfolio_weights={"VOO": 0.7, "BND": 0.3},
        weights_source="optimization_result_released",
        cash_proxy_ticker="BIL",
        rf_source="FRED:DTB3",
    )

    assert setup["portfolio_input"]["product_input_case"] == "universe_only"
    assert setup["analysis_portfolio"]["portfolio_role"] == "generated_policy_portfolio"
    assert setup["analysis_portfolio"]["weight_source"] == "optimization_result_released"
    assert setup["analysis_portfolio"]["recommendation_status"] == "generated_policy_output_released"


def test_input_assumptions_spec_documents_unknown_ticker_policy_conflict() -> None:
    text = Path("docs/specs/input_assumptions_spec.md").read_text(encoding="utf-8")

    assert "analysis_setup" in text
    assert "MVP product mode rejects unknown tickers" in text
    assert "current repo mode" in text
