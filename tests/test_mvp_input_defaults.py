"""Tests for Core MVP input normalization (apply_mvp_input_defaults)."""
from __future__ import annotations

import pytest

from src.config_schema import ConfigValidationError, validate_config
from src.mvp_input import apply_mvp_input_defaults


def test_current_weights_injects_current_portfolio_subject() -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "tickers": ["VOO", "BND"],
            "current_weights": {"VOO": 0.6, "BND": 0.4},
        }
    )

    assert cfg.analysis_mode == "analyze_current_weights"
    assert cfg.analysis_subject["type"] == "current_portfolio"
    assert cfg.weights == {"VOO": 0.6, "BND": 0.4}
    assert cfg.weights_source == "config.analysis_subject.weights"


def test_top_level_weights_injects_current_portfolio_subject() -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "tickers": ["VOO", "BND"],
            "weights": {"VOO": "50%", "BND": "50%"},
        }
    )

    assert cfg.analysis_mode == "analyze_current_weights"
    assert cfg.analysis_subject["type"] == "current_portfolio"
    assert cfg.weights == {"VOO": 0.5, "BND": 0.5}


def test_explicit_analysis_subject_is_not_overridden() -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "tickers": ["VOO", "BND"],
            "current_weights": {"VOO": 0.6, "BND": 0.4},
            "analysis_subject": {
                "type": "model_portfolio",
                "weights": {"VOO": 0.6, "BND": 0.4},
            },
        }
    )

    assert cfg.analysis_subject["type"] == "model_portfolio"


def test_no_weights_leaves_universe_baseline_path() -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "tickers": ["VOO", "BND"],
        }
    )

    assert cfg.analysis_subject == {}
    assert cfg.analysis_mode == "optimize_from_universe"


def test_generated_weights_source_skips_mvp_injection() -> None:
    raw = {
        "investor_currency": "USD",
        "tickers": ["VOO", "BND"],
        "weights": {"VOO": 0.7, "BND": 0.3},
        "_weights_source": "Main portfolio/portfolio_weights.yml",
    }
    apply_mvp_input_defaults(raw)

    assert not raw.get("analysis_subject")


def test_mvp_weights_preflight_rejects_unknown_ticker() -> None:
    with pytest.raises(ConfigValidationError, match="unknown="):
        validate_config(
            {
                "investor_currency": "USD",
                "tickers": ["VOO", "NOTAREALTICKER"],
                "weights": {"VOO": 0.5, "NOTAREALTICKER": 0.5},
            }
        )


def test_current_weights_take_precedence_over_top_level_weights() -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "tickers": ["VOO", "BND"],
            "current_weights": {"VOO": 0.7, "BND": 0.3},
            "weights": {"VOO": 0.5, "BND": 0.5},
        }
    )

    assert cfg.analysis_subject["type"] == "current_portfolio"
    assert cfg.weights == {"VOO": 0.7, "BND": 0.3}
