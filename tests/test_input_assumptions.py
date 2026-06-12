from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from src.analysis_setup import build_analysis_setup
from src.config import load_validated_config
from src.config_schema import ConfigValidationError, validate_config
from src.input_assumptions import (
    FIELD_TIER_REGISTRY,
    build_field_tiers,
    build_input_assumptions_from_analysis_setup,
    build_input_assumptions_summary,
    build_input_surface,
)
from src.io_export import export_run_metadata


FIVE_TICKERS = ["VOO", "BND", "GLD", "QQQ", "VNQ"]


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
    assert cfg.weights_source == "config.analysis_subject.weights"


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
    assert cfg.weights_source == "config.analysis_subject.weights"


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

    assert summary["portfolio_input"]["analysis_mode"] == "analyze_current_weights"
    assert summary["source_analysis_setup_version"] == "analysis_setup_v1"
    assert summary["analysis_subject"]["type"] == "current_portfolio"
    assert summary["analysis_subject"]["resolution_source"] == "config.analysis_subject"
    assert summary["portfolio_input"]["reported_weights"]["status"] == "fully_invested"
    assert summary["currency_and_market"]["cash_proxy_ticker"] == "BIL"
    assert summary["core_mvp_input_contract"]["product_surface"] is True
    assert summary["core_mvp_input_contract"]["required_user_input_groups"] == [
        "tickers",
        "allocation",
        "investor_currency",
    ]
    assert "client_profile" in summary["core_mvp_input_contract"]["excluded_legacy_advanced_fields"]
    assert summary["mandate_and_constraints"]["_scope"]["product_surface"] is False
    assert summary["mandate_and_constraints"]["_scope"]["not_required_for_core_mvp"] is True
    assert summary["mandate_and_constraints"]["horizon_role"] == "report_context_only_not_optimizer_constraint"
    assert summary["calculation_assumptions"]["returns_frequency"] == "monthly"
    assert summary["calculation_assumptions"]["configured_returns_frequency"] == "weekly"
    assert summary["calculation_assumptions"]["main_metrics_returns_frequency_forced"] is True
    assert summary["current_v1_gaps"]["transaction_costs"] == "not_implemented"
    assert summary["input_surface"]["version"] == "input_surface_v1"
    assert summary["input_surface"]["profile"] == "core_mvp"
    assert summary["input_surface"]["core_mvp_requirements_met"] is True
    assert summary["field_tiers"]["version"] == "field_tiers_v1"
    assert "tickers" in summary["field_tiers"]["registry"]
    assert summary["field_tiers"]["run_disclosure"]["core_mvp"]["requirements_met"] is True


def test_input_surface_core_mvp_from_mvp_fixture() -> None:
    fixture_path = (
        Path(__file__).resolve().parent / "fixtures" / "mvp_portfolios" / "minimal_usd_no_cash.yml"
    )
    with open(fixture_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    cfg = validate_config(raw)
    setup = build_analysis_setup(cfg, cash_proxy_ticker="BIL", rf_source="FRED:DTB3")
    surface = build_input_surface(setup)

    assert setup["core_mvp_input_surface"]["required_user_input_groups"] == [
        "tickers",
        "allocation",
        "investor_currency",
    ]
    assert setup["core_mvp_input_surface"]["core_mvp_requirements_met"] is True
    assert "target_max_drawdown_pct" in setup["core_mvp_input_surface"]["excluded_legacy_advanced_fields"]
    assert setup["resolved_mandate"]["_scope"]["core_mvp_product_surface"] is False
    assert surface["profile"] == "core_mvp"
    assert surface["product_path"] == "portfolio_first_diagnosis"
    assert surface["first_screen"]["tickers"]["supplied"] is True
    assert surface["first_screen"]["allocation"]["supplied"] is True
    assert surface["first_screen"]["investor_currency"]["value"] == "USD"


def test_input_surface_legacy_universe_only() -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "tickers": ["VOO", "BND", "GLD"],
        }
    )
    setup = build_analysis_setup(cfg, cash_proxy_ticker="BIL", rf_source="FRED:DTB3")
    surface = build_input_surface(setup)

    assert surface["profile"] == "legacy_advanced"
    assert surface["first_screen"]["allocation"]["supplied"] is False


def test_field_tiers_registry_covers_core_mvp_keys() -> None:
    for key in ("tickers", "current_weights", "investor_currency"):
        assert FIELD_TIER_REGISTRY[key] == "core_mvp"


def test_field_tiers_marks_deferred_client_fit_when_profile_set() -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "tickers": ["VOO", "BND"],
            "weights": {"VOO": 0.5, "BND": 0.5},
            "client_profile": "balanced",
            "horizon_years": 10,
        }
    )
    setup = build_analysis_setup(cfg, cash_proxy_ticker="BIL", rf_source="FRED:DTB3")
    tiers = build_field_tiers(setup)

    assert "client_fit_v1" in tiers["run_disclosure"]["deferred_tiers_with_values"]
    assert "client_profile" in tiers["run_disclosure"]["populated_by_tier"]["client_fit_v1"]
    assert "horizon_years" in tiers["run_disclosure"]["user_configured_fields"]


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
    assert data["input_assumptions"]["input_surface"]["profile"] == "core_mvp"
    assert data["input_assumptions"]["field_tiers"]["version"] == "field_tiers_v1"


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
            "analysis_subject",
            "analysis_portfolio",
            "resolved_mandate",
            "resolved_assumptions",
            "validation_result",
        ]
    ).issubset(setup)
    assert setup["portfolio_input"]["product_input_case"] == "user_current"
    assert setup["analysis_subject"]["type"] == "current_portfolio"
    assert setup["analysis_portfolio"]["portfolio_role"] == "user_current_portfolio"
    assert setup["analysis_portfolio"]["recommendation_status"] == "diagnostic_current_portfolio_not_recommendation"
    assert setup["portfolio_input"]["investment_horizon_years"]["affects_calculations"] is False

    projection = build_input_assumptions_from_analysis_setup(setup)
    assert projection["version"] == "input_assumptions_v1"
    assert projection["source_analysis_setup_version"] == "analysis_setup_v1"
    assert projection["analysis_subject"]["type"] == "current_portfolio"
    assert projection["portfolio_input"]["analysis_portfolio_role"] == "user_current_portfolio"
    assert projection["input_surface"]["profile"] == "core_mvp"
    assert projection["field_tiers"]["run_disclosure"]["input_surface_profile"] == "core_mvp"


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
    assert setup["analysis_subject"]["type"] == "universe_baseline"
    assert setup["analysis_subject"]["weight_source"] == "system.equal_weight_universe_baseline"
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
    assert setup["analysis_subject"]["type"] == "universe_baseline"
    assert setup["analysis_subject"]["warnings"][0]["code"] == "GENERATED_POLICY_WEIGHTS_NOT_ANALYSIS_SUBJECT"
    assert setup["analysis_portfolio"]["portfolio_role"] == "generated_policy_portfolio"
    assert setup["analysis_portfolio"]["weight_source"] == "optimization_result_released"
    assert setup["analysis_portfolio"]["recommendation_status"] == "generated_policy_output_released"


def test_explicit_current_analysis_subject_sets_report_weights_and_metadata() -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "tickers": ["VOO", "BND"],
            "analysis_subject": {
                "type": "current_portfolio",
                "display_name": "Client current portfolio",
                "weights": {"VOO": "60%", "BND": "40%"},
            },
        }
    )

    setup = build_analysis_setup(cfg, cash_proxy_ticker="BIL", rf_source="FRED:DTB3")

    assert cfg.weights == {"VOO": 0.6, "BND": 0.4}
    assert cfg.weights_source == "config.analysis_subject.weights"
    assert setup["analysis_subject"]["type"] == "current_portfolio"
    assert setup["analysis_subject"]["display_name"] == "Client current portfolio"
    assert setup["analysis_subject"]["weight_status"]["status"] == "fully_invested"
    assert setup["analysis_portfolio"]["portfolio_role"] == "user_current_portfolio"


def test_explicit_analysis_subject_rejects_unknown_ticker() -> None:
    with pytest.raises(ConfigValidationError, match="unknown="):
        validate_config(
            {
                "investor_currency": "USD",
                "tickers": ["VOO", "NOTAREALTICKER"],
                "analysis_subject": {
                    "type": "current_portfolio",
                    "weights": {"VOO": "50%", "NOTAREALTICKER": "50%"},
                },
            }
        )


def test_explicit_analysis_subject_accepts_stock_universe_ticker() -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "tickers": ["AAPL"],
            "analysis_subject": {
                "type": "model_portfolio",
                "weights": {"AAPL": "100%"},
            },
        }
    )
    assert cfg.analysis_subject["type"] == "model_portfolio"


def test_mvp_weights_without_analysis_subject_preflights_unknown_ticker() -> None:
    with pytest.raises(ConfigValidationError, match="unknown="):
        validate_config(
            {
                "investor_currency": "USD",
                "tickers": ["VOO", "NOTAREALTICKER"],
                "weights": {"VOO": 0.5, "NOTAREALTICKER": 0.5},
            }
        )


def test_five_ticker_current_analysis_subject_accepts_valid_weights() -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "tickers": FIVE_TICKERS,
            "analysis_subject": {
                "type": "current_portfolio",
                "weights": {
                    "VOO": "35%",
                    "BND": "25%",
                    "GLD": "15%",
                    "QQQ": "15%",
                    "VNQ": "10%",
                },
            },
        }
    )

    setup = build_analysis_setup(cfg, cash_proxy_ticker="BIL", rf_source="FRED:DTB3")

    assert cfg.weights_source == "config.analysis_subject.weights"
    assert setup["analysis_subject"]["ticker_count"] == 5
    assert setup["analysis_subject"]["weight_status"]["status"] == "fully_invested"
    assert setup["validation_result"]["status"] == "valid"


def test_five_ticker_current_analysis_subject_partial_weights_show_cash_remainder() -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "tickers": FIVE_TICKERS,
            "analysis_subject": {
                "type": "current_portfolio",
                "weights": {
                    "VOO": "30%",
                    "BND": "20%",
                    "GLD": "10%",
                    "QQQ": "10%",
                    "VNQ": "5%",
                },
            },
        }
    )

    setup = build_analysis_setup(cfg, cash_proxy_ticker="BIL", rf_source="FRED:DTB3")
    projection = build_input_assumptions_from_analysis_setup(setup)

    assert setup["analysis_subject"]["weight_status"]["status"] == "partial_with_cash_remainder"
    assert setup["analysis_subject"]["weight_status"]["cash_remainder"] == pytest.approx(0.25)
    assert setup["validation_result"]["status"] == "valid_with_action_required_warnings"
    assert projection["analysis_subject"]["weight_status"]["status"] == "partial_with_cash_remainder"
    assert projection["analysis_subject"]["weight_status"]["cash_remainder"] == pytest.approx(0.25)
    assert projection["portfolio_input"]["reported_weights"]["status"] == "partial_with_cash_remainder"


def test_five_ticker_current_analysis_subject_rejects_overallocated_weights() -> None:
    with pytest.raises(ConfigValidationError, match="must not sum above 1\\.0"):
        validate_config(
            {
                "investor_currency": "USD",
                "tickers": FIVE_TICKERS,
                "analysis_subject": {
                    "type": "current_portfolio",
                    "weights": {
                        "VOO": "50%",
                        "BND": "30%",
                        "GLD": "25%",
                        "QQQ": "20%",
                        "VNQ": "10%",
                    },
                },
            }
        )


def test_five_ticker_model_analysis_subject_rejects_overallocated_weights() -> None:
    with pytest.raises(ConfigValidationError, match="must not sum above 1\\.0"):
        validate_config(
            {
                "investor_currency": "USD",
                "tickers": FIVE_TICKERS,
                "analysis_subject": {
                    "type": "model_portfolio",
                    "weights": {
                        "VOO": "40%",
                        "BND": "30%",
                        "GLD": "20%",
                        "QQQ": "15%",
                        "VNQ": "5%",
                    },
                },
            }
        )


def test_five_ticker_current_analysis_subject_rejects_negative_weight() -> None:
    with pytest.raises(ConfigValidationError, match="must be non-negative"):
        validate_config(
            {
                "investor_currency": "USD",
                "tickers": FIVE_TICKERS,
                "analysis_subject": {
                    "type": "current_portfolio",
                    "weights": {
                        "VOO": "40%",
                        "BND": "30%",
                        "GLD": "-5%",
                        "QQQ": "20%",
                        "VNQ": "15%",
                    },
                },
            }
        )


def test_explicit_model_analysis_subject_resolves_as_model_portfolio() -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "tickers": ["VOO", "BND", "GLD"],
            "analysis_subject": {
                "type": "model_portfolio",
                "id": "income_model",
                "tickers": ["VOO", "BND", "GLD"],
                "weights": {"VOO": 0.4, "BND": 0.4, "GLD": 0.2},
            },
        }
    )

    setup = build_analysis_setup(cfg, cash_proxy_ticker="BIL", rf_source="FRED:DTB3")

    assert setup["portfolio_input"]["product_input_case"] == "model_portfolio"
    assert setup["analysis_subject"]["id"] == "income_model"
    assert setup["analysis_subject"]["type"] == "model_portfolio"
    assert setup["analysis_subject"]["portfolio_role"] == "model_portfolio"
    assert setup["analysis_subject"]["recommendation_status"] == "diagnostic_model_portfolio_not_recommendation"
    assert setup["analysis_portfolio"]["portfolio_role"] == "model_portfolio"


def test_explicit_universe_baseline_analysis_subject_creates_equal_weights() -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "tickers": ["VOO", "BND", "GLD"],
            "analysis_subject": {
                "type": "universe_baseline",
                "display_name": "Starter universe",
            },
        }
    )

    setup = build_analysis_setup(cfg, cash_proxy_ticker="BIL", rf_source="FRED:DTB3")

    assert cfg.weights_source == "system.analysis_subject.equal_weight_baseline"
    assert sum(cfg.weights.values()) == pytest.approx(1.0)
    assert setup["analysis_subject"]["type"] == "universe_baseline"
    assert setup["analysis_subject"]["display_name"] == "Starter universe"
    assert setup["analysis_subject"]["weight_status"]["status"] == "fully_invested"
    assert setup["analysis_portfolio"]["portfolio_role"] == "equal_weight_initial_baseline"


def test_explicit_analysis_subject_blocks_generated_weights_merge(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yml"
    weights_dir = tmp_path / "Main portfolio"
    weights_dir.mkdir(parents=True)
    _write_yaml(
        config_path,
        {
            "investor_currency": "USD",
            "tickers": ["VOO", "BND"],
            "output_dir_final": "Main portfolio",
            "analysis_subject": {"type": "universe_baseline"},
        },
    )
    _write_yaml(weights_dir / "portfolio_weights.yml", {"VOO": 0.1, "BND": 0.9})

    cfg = load_validated_config(config_path)

    assert cfg.weights == {"VOO": pytest.approx(0.5), "BND": pytest.approx(0.5)}
    assert cfg.weights_source == "system.analysis_subject.equal_weight_baseline"


@pytest.mark.parametrize("subject_type", ["current_portfolio", "model_portfolio"])
def test_invalid_weighted_analysis_subject_requires_weights(subject_type: str) -> None:
    with pytest.raises(ConfigValidationError, match="requires non-empty analysis_subject.weights"):
        validate_config(
            {
                "investor_currency": "USD",
                "tickers": FIVE_TICKERS,
                "analysis_subject": {"type": subject_type},
            }
        )


def test_input_assumptions_spec_documents_ticker_preflight_policy() -> None:
    text = Path("docs/specs/input_assumptions_spec.md").read_text(encoding="utf-8")

    assert "analysis_setup" in text
    assert "preflight_explicit_analysis_subject_tickers" in text
    assert "Explicit `analysis_subject`" in text
    assert "Legacy compatibility paths" in text
