"""Offline end-to-end smoke tests for the portfolio-first review chain."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from src.analysis_setup import build_analysis_setup
from src.candidate_comparison import write_candidate_comparison_outputs
from src.config_schema import PortfolioConfig, validate_config
from src.portfolio_review_workflow import build_portfolio_review_plan
from mvp_offline_fixtures import (
    MVP_DECISION_PACKAGE_ARTIFACTS,
    DEFAULT_ANALYSIS_END,
    snapshot_10y,
    write_json,
)


def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*_args, **_kwargs):
        raise AssertionError("portfolio-first offline E2E test must not use live network data")

    import src.data_fred as data_fred
    import src.data_yf as data_yf

    monkeypatch.setattr(data_yf, "download_all", _boom)
    monkeypatch.setattr(data_fred, "fetch_fred_series", _boom, raising=False)


def _rc_rows(weights: dict[str, float]) -> list[dict[str, Any]]:
    return [{"ticker": ticker, "rc_pct": weight} for ticker, weight in weights.items()]


def _seed_snapshot(folder: Path, metrics: dict[str, Any], weights: dict[str, float]) -> None:
    write_json(
        folder / "snapshot_10y.json",
        snapshot_10y(
            metrics,
            rc_asset=_rc_rows(weights),
            final_weights_total=weights,
        ),
    )


def _seed_candidate_artifacts(root: Path) -> None:
    eq_weights = {"VOO": 0.3333333333, "BND": 0.3333333333, "GLD": 0.3333333334}
    rp_weights = {"VOO": 0.45, "BND": 0.4, "GLD": 0.15}
    _seed_snapshot(
        root / "equal-weight portfolio",
        {"cagr": 0.075, "vol_annual": 0.105, "max_drawdown": -0.16, "sharpe": 0.55},
        eq_weights,
    )
    _seed_snapshot(
        root / "risk parity portfolio",
        {"cagr": 0.071, "vol_annual": 0.09, "max_drawdown": -0.13, "sharpe": 0.62},
        rp_weights,
    )


def _seed_analysis_subject_sidecar(root: Path, cfg: PortfolioConfig) -> dict[str, Any]:
    out_dir = root / str(cfg.output_dir_final) / "analysis_subject"
    weights = {str(k): float(v) for k, v in (cfg.weights or {}).items()}
    setup = build_analysis_setup(
        cfg,
        portfolio_weights=weights,
        weights_source=cfg.weights_source,
        portfolio_role_override="analysis_subject",
    )
    write_json(
        out_dir / "run_metadata.json",
        {
            "run_info": {"analysis_end_date": DEFAULT_ANALYSIS_END},
            "portfolio_valid": True,
            "analysis_setup": setup,
        },
    )
    _seed_snapshot(
        out_dir,
        {"cagr": 0.058, "vol_annual": 0.13, "max_drawdown": -0.24, "sharpe": 0.34},
        weights,
    )
    return setup


def _cfg(subject: dict[str, Any]) -> PortfolioConfig:
    return validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND", "GLD"],
            "analysis_subject": subject,
        }
    )


def _load(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize(
    ("subject", "expected_type", "expected_role", "expected_recommendation"),
    [
        (
            {
                "type": "current_portfolio",
                "display_name": "Client current portfolio",
                "weights": {"VOO": 0.55, "BND": 0.35, "GLD": 0.10},
            },
            "current_portfolio",
            "user_current_portfolio",
            "diagnostic_current_portfolio_not_recommendation",
        ),
        (
            {
                "id": "income_model",
                "type": "model_portfolio",
                "display_name": "Income model portfolio",
                "weights": {"VOO": 0.45, "BND": 0.4, "GLD": 0.15},
            },
            "model_portfolio",
            "model_portfolio",
            "diagnostic_model_portfolio_not_recommendation",
        ),
        (
            {
                "type": "universe_baseline",
                "display_name": "Starter universe baseline",
            },
            "universe_baseline",
            "equal_weight_initial_baseline",
            "baseline_not_recommendation",
        ),
    ],
)
def test_portfolio_first_offline_e2e_subject_to_decision_package(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    subject: dict[str, Any],
    expected_type: str,
    expected_role: str,
    expected_recommendation: str,
) -> None:
    """Synthetic subject diagnostics + candidates -> comparison -> decision package."""
    _block_network(monkeypatch)
    cfg = _cfg(subject)
    setup = _seed_analysis_subject_sidecar(tmp_path, cfg)
    _seed_candidate_artifacts(tmp_path)

    plan = build_portfolio_review_plan(cfg, project_root=tmp_path, skip_pdf=True)
    stage_text = " ".join(" ".join(step.argv) for step in plan.steps)
    assert [step.stage for step in plan.steps] == ["diagnosis", "candidates"]
    assert "--materialize-analysis-subject" in plan.steps[0].argv
    assert "run_optimization.py" not in stage_text

    paths = write_candidate_comparison_outputs(cfg, project_root=tmp_path)
    out_dir = tmp_path / "Main portfolio"

    for filename, schema_version in MVP_DECISION_PACKAGE_ARTIFACTS:
        doc = _load(out_dir / filename)
        assert doc.get("schema_version") == schema_version, filename

    comparison = _load(paths["candidate_comparison_json"])
    assert comparison["comparison_baseline_candidate_id"] == "analysis_subject"
    assert comparison["analysis_setup_summary"]["analysis_subject_type"] == expected_type
    assert setup["analysis_subject"]["type"] == expected_type
    subject_row = next(c for c in comparison["candidates"] if c["candidate_id"] == "analysis_subject")
    assert subject_row["status"] == "available"
    assert subject_row["portfolio_role"] == expected_role
    assert subject_row["recommendation_status"] == expected_recommendation
    assert subject_row["artifact_root"] == "Main portfolio/analysis_subject"

    if expected_type == "universe_baseline":
        assert subject_row["weight_source"] == "system.analysis_subject.equal_weight_baseline"
        assert subject_row["weight_concentration"]["top3_weight_sum_pct"] == pytest.approx(1.0)
    else:
        assert subject_row["weight_concentration"]["top1_weight_asset"] == "VOO"

    selection = _load(out_dir / "selection_decision.json")
    assert selection["baseline_candidate_id"] == "analysis_subject"
    assert selection.get("favored_candidate_id") != "policy"
    favored_display = selection["favored_display_name"]

    policy_row = next(c for c in comparison["candidates"] if c["candidate_id"] == "policy")
    assert policy_row["unavailable_reason"] == "legacy_policy_not_default_portfolio_first_candidate"

    current_vs_policy = _load(out_dir / "current_vs_policy_status.json")
    assert current_vs_policy["workflow_profile"] == "portfolio_first_review"
    assert current_vs_policy["skip_reason"] == "portfolio_first_review"

    action = _load(out_dir / "action_plan.json")
    assert action["baseline_candidate_id"] == "analysis_subject"
    assert action["baseline_weights"]

    monitoring = _load(out_dir / "monitoring_diff.json")
    assert monitoring["primary_profile_id"] == "analysis_subject"

    journal = _load(out_dir / "decision_journal.json")
    assert journal["diagnosed_subject"]["candidate_id"] == "analysis_subject"
    assert journal["assumptions"]["analysis_subject_type"] == expected_type
    assert journal["expected_improvement"]["baseline_candidate_id"] == "analysis_subject"

    package = _load(out_dir / "decision_package_summary.json")
    summary_text = package.get("summary_plain_en") or ""
    assert "Starting portfolio:" in summary_text
    assert favored_display in summary_text
    assert not (out_dir / "decision_package_summary.txt").is_file()
