"""Portfolio review integration for Core MVP input (Input Layer Session 07)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

import run_report
from mvp_offline_fixtures import (
    FIVE_TICKER_MVP_TICKERS,
    five_ticker_mvp_core_input_dict,
    seed_product_bundle_offline_workspace,
    validate_mvp_fixture,
)
from src.config_schema import validate_config
from src.portfolio_review_workflow import (
    RUNTIME_MODE_PRODUCT_DIAGNOSIS_ONLY,
    build_portfolio_review_plan,
)
from src.real_cash import collect_real_cash_tickers
from src.stress import LOSS_GATE_MODE_DIAGNOSTIC, run_stress


@pytest.mark.parametrize(
    "fixture_name",
    ["minimal_usd_no_cash.yml", "minimal_usd_with_cash.yml"],
)
def test_mvp_fixture_materialization_resolves_current_portfolio(fixture_name: str) -> None:
    cfg = validate_mvp_fixture(fixture_name)
    mat = run_report.resolve_analysis_subject_materialization(cfg)

    assert mat["status"] == "resolved"
    assert mat["subject"]["type"] == "current_portfolio"
    assert mat["subject"]["portfolio_role"] == "user_current_portfolio"
    assert mat["weights_source"] == "config.analysis_subject.weights"
    assert sum(mat["weights"].values()) == pytest.approx(1.0, abs=1e-6)


def test_mvp_fixture_with_cash_materialization_keeps_cash_usd() -> None:
    cfg = validate_mvp_fixture("minimal_usd_with_cash.yml")
    mat = run_report.resolve_analysis_subject_materialization(cfg)

    assert "Cash USD" in mat["weights"]
    assert mat["weights"]["Cash USD"] == pytest.approx(0.10)
    assert collect_real_cash_tickers(tickers=cfg.tickers, weights=cfg.weights) == ["Cash USD"]


def test_five_ticker_current_weights_materializes_without_explicit_subject() -> None:
    cfg = validate_config(five_ticker_mvp_core_input_dict())
    mat = run_report.resolve_analysis_subject_materialization(cfg)

    assert cfg.analysis_mode == "analyze_current_weights"
    assert cfg.analysis_subject["type"] == "current_portfolio"
    assert mat["status"] == "resolved"
    assert set(mat["weights"]) == set(FIVE_TICKER_MVP_TICKERS)
    assert sum(mat["weights"].values()) == pytest.approx(1.0, abs=1e-6)


def test_mvp_fixture_portfolio_review_plan_materializes_subject_first(tmp_path: Path) -> None:
    cfg = validate_mvp_fixture("minimal_usd_no_cash.yml")
    plan = build_portfolio_review_plan(
        cfg,
        project_root=tmp_path,
        skip_candidates=True,
        skip_compare=True,
        skip_pdf=True,
    )

    assert [step.stage for step in plan.steps] == ["diagnosis"]
    assert plan.runtime_mode == RUNTIME_MODE_PRODUCT_DIAGNOSIS_ONLY
    subject_argv = " ".join(plan.steps[0].argv)
    assert "run_report.py" in subject_argv
    assert "--materialize-analysis-subject" in subject_argv
    assert "--review-mode" in subject_argv
    assert "core" in subject_argv
    assert "run_optimization.py" not in subject_argv


def test_mvp_fixture_one_candidate_product_path(tmp_path: Path) -> None:
    cfg = validate_mvp_fixture("minimal_usd_no_cash.yml")
    plan = build_portfolio_review_plan(
        cfg,
        project_root=tmp_path,
        candidate_ids="equal_weight",
        skip_pdf=True,
    )

    assert [step.stage for step in plan.steps] == ["diagnosis", "candidates"]
    factory_argv = plan.steps[1].argv
    assert "--candidates" in factory_argv
    assert "equal_weight" in factory_argv
    assert "--then-compare" in factory_argv
    assert "run_optimization.py" not in " ".join(" ".join(step.argv) for step in plan.steps)


def test_run_materialize_mvp_fixture_passes_resolved_weights(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = validate_mvp_fixture("minimal_usd_no_cash.yml")
    cfg.output_dir_final = str(tmp_path / "Main portfolio")
    expected_weights = {str(k): float(v) for k, v in (cfg.weights or {}).items()}
    calls: list[dict[str, Any]] = []

    def fake_run_portfolio_report_for_weights(_cfg, weights, **kwargs):
        calls.append({"weights": weights, "kwargs": kwargs})
        out = Path(kwargs["output_dir_final"])
        out.mkdir(parents=True, exist_ok=True)
        (out / "run_metadata.json").write_text("{}", encoding="utf-8")
        (out / "snapshot_10y.json").write_text(
            json.dumps({"metrics": {"cagr": 0.06}, "final_weights_total": weights}),
            encoding="utf-8",
        )
        (out / "stress_report.json").write_text("{}", encoding="utf-8")
        return {}, {"portfolio_valid": True}

    monkeypatch.setattr(
        run_report,
        "run_portfolio_report_for_weights",
        fake_run_portfolio_report_for_weights,
    )
    monkeypatch.setattr(
        run_report,
        "prepare_review_run_context",
        lambda *a, **k: None,
    )

    run_report.run_materialize_analysis_subject_report(
        cfg,
        run_timestamp="2026-05-26T12:00:00",
        backtest_mode="dynamic_nan_safe",
        no_cache=True,
        review_mode="core",
        project_root=tmp_path,
    )

    assert len(calls) == 1
    assert calls[0]["weights"] == expected_weights
    assert calls[0]["kwargs"]["weights_source"] == "config.analysis_subject.weights"
    assert calls[0]["kwargs"]["portfolio_role_override"] == "analysis_subject"
    sidecar = tmp_path / "Main portfolio" / "analysis_subject"
    assert sidecar.is_dir()


def test_offline_product_bundle_seed_run_metadata_core_mvp_profile(
    tmp_path: Path,
) -> None:
    cfg = validate_mvp_fixture("minimal_usd_no_cash.yml")
    seeded = seed_product_bundle_offline_workspace(tmp_path, cfg)
    run_metadata = json.loads(
        (seeded["analysis_subject_dir"] / "run_metadata.json").read_text(encoding="utf-8")
    )
    assumptions = run_metadata["input_assumptions"]

    assert assumptions["input_surface"]["profile"] == "core_mvp"
    assert assumptions["input_surface"]["core_mvp_requirements_met"] is True
    assert assumptions["field_tiers"]["run_disclosure"]["core_mvp"]["requirements_met"] is True
    assert run_metadata["analysis_setup"]["analysis_subject"]["type"] == "current_portfolio"


CORE_MVP_FORBIDDEN_KEYS = {
    "client_profile",
    "mandate",
    "mandate_gate",
    "suitability",
    "fail_reason_code",
    "failed_scenario",
    "failed_test",
    "pass",
    "loss_ok",
}


def _find_forbidden_keys(obj: Any, forbidden: set[str] = CORE_MVP_FORBIDDEN_KEYS) -> list[str]:
    found: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if str(key) in forbidden:
                found.append(str(key))
            found.extend(_find_forbidden_keys(value, forbidden))
    elif isinstance(obj, list):
        for item in obj:
            found.extend(_find_forbidden_keys(item, forbidden))
    return found


def test_core_mvp_materialize_subject_writes_blocks_2_and_3_to_temp_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Session 03: temp-output E2E wiring check for Core MVP Block 1 -> 2 -> 3 path.

    We run the real materialization entrypoint but stub heavy calculation to keep the test
    deterministic and offline, while still validating:
    - real cash survives
    - analysis_subject output path is stable
    - Blocks 2.1-2.6 exist in portfolio_xray.json
    - Blocks 3.1-3.4 exist in stress_report.json
    - no optimizer/candidate/mandate leakage in product-facing outputs
    """
    cfg = validate_mvp_fixture("minimal_usd_with_cash.yml")
    cfg.output_dir_final = str(tmp_path / "Main portfolio")
    expected_weights = {str(k): float(v) for k, v in (cfg.weights or {}).items()}
    assert "Cash USD" in expected_weights

    def fake_run_portfolio_report_for_weights(_cfg, weights, **kwargs):
        out = Path(kwargs["output_dir_final"])
        out.mkdir(parents=True, exist_ok=True)

        # Minimal-but-shaped portfolio_xray.json with Blocks 2.1-2.6 present.
        xray = {
            "version": "offline_test_fixture",
            "diagnostic_only": True,
            "block_2_1_asset_allocation": {"block": "2.1_asset_allocation", "status": "available"},
            "block_2_2_portfolio_metrics": {"block": "2.2_portfolio_metrics", "status": "available"},
            "block_2_3_factor_exposure": {"block": "2.3_factor_exposure", "status": "available"},
            "block_2_4_hidden_exposure": {"block": "2.4_hidden_exposure", "status": "available"},
            "block_2_5_risk_budget_view": {"block": "2.5_risk_budget_view", "status": "available"},
            "block_2_6_portfolio_weakness_map": {
                "block": "2.6_portfolio_weakness_map",
                "status": "available",
            },
        }

        # Deterministic stress run that already includes product adapters 3.2-3.4.
        idx = pd.date_range("2016-01-31", periods=120, freq="ME")
        monthly_returns = pd.DataFrame(
            {"AAA": [0.01] * len(idx), "BBB": [0.005] * len(idx)},
            index=idx,
        )
        factor_cols = ["beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd"]
        stress = run_stress(
            tickers=["AAA", "BBB"],
            weights={"AAA": 0.8, "BBB": 0.2},
            monthly_returns=monthly_returns,
            asset_betas=pd.DataFrame(columns=factor_cols),
            portfolio_betas={key: 0.0 for key in factor_cols},
            target_max_drawdown_pct=0.05,
            cash_proxy_ticker="",
            hedge_assets=["AAA"],
            loss_gate_mode=LOSS_GATE_MODE_DIAGNOSTIC,
        )
        # Block 3.1 is an adapter/metadata wrapper in the exported stress_report.json.
        # `run_stress` does not own it, so we seed a minimal deterministic stub here.
        stress["scenario_library_meta"] = {
            "schema_version": "scenario_library_meta_v1",
            "status": "available",
            "library_source": "offline_test_fixture",
            "scenario_count": len(stress.get("scenario_results") or []),
        }

        (out / "run_metadata.json").write_text("{}", encoding="utf-8")
        (out / "portfolio_xray.json").write_text(json.dumps(xray), encoding="utf-8")
        (out / "stress_report.json").write_text(json.dumps(stress), encoding="utf-8")
        (out / "snapshot_10y.json").write_text(
            json.dumps({"metrics": {"cagr": 0.06}, "final_weights_total": weights}),
            encoding="utf-8",
        )
        return {}, {"portfolio_valid": True}

    monkeypatch.setattr(
        run_report,
        "run_portfolio_report_for_weights",
        fake_run_portfolio_report_for_weights,
    )
    monkeypatch.setattr(
        run_report,
        "prepare_review_run_context",
        lambda *a, **k: None,
    )

    run_report.run_materialize_analysis_subject_report(
        cfg,
        run_timestamp="2026-05-26T12:00:00",
        backtest_mode="dynamic_nan_safe",
        no_cache=True,
        review_mode="core",
        project_root=tmp_path,
    )

    sidecar = tmp_path / "Main portfolio" / "analysis_subject"
    assert sidecar.is_dir()
    assert (sidecar / "run_metadata.json").is_file()
    assert (sidecar / "portfolio_xray.json").is_file()
    assert (sidecar / "stress_report.json").is_file()

    # Cash should stay real (in config materialization + weights passed through).
    assert collect_real_cash_tickers(tickers=cfg.tickers, weights=cfg.weights) == ["Cash USD"]
    assert expected_weights["Cash USD"] == pytest.approx(0.10)

    xray = json.loads((sidecar / "portfolio_xray.json").read_text(encoding="utf-8"))
    for key in (
        "block_2_1_asset_allocation",
        "block_2_2_portfolio_metrics",
        "block_2_3_factor_exposure",
        "block_2_4_hidden_exposure",
        "block_2_5_risk_budget_view",
        "block_2_6_portfolio_weakness_map",
    ):
        assert key in xray
        assert xray[key].get("status") == "available"
        found = sorted(set(_find_forbidden_keys(xray[key])))
        assert not found, f"{key} contains forbidden keys: {found}"

    stress = json.loads((sidecar / "stress_report.json").read_text(encoding="utf-8"))
    for key in ("scenario_library_meta", "stress_results_v1", "hedge_gap_analysis_v1", "current_portfolio_stress_scorecard_v1"):
        assert key in stress, f"Missing stress_report product key: {key}"
        found = sorted(set(_find_forbidden_keys(stress[key])))
        assert not found, f"{key} contains forbidden keys: {found}"
