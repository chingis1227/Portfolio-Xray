"""Block 2.1 pipeline integration — analysis_subject portfolio_xray on product review paths."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import run_report
from mvp_offline_fixtures import (
    build_offline_run_metadata,
    refresh_analysis_subject_portfolio_xray,
    snapshot_10y,
    validate_mvp_fixture,
    write_json,
)
from src.analysis_setup import build_analysis_setup
from src.config import resolve_cash_and_rf
from src.output_policy import output_policy_for_profile, write_output_manifest
from src.portfolio_review_workflow import (
    RUNTIME_MODE_PRODUCT_DIAGNOSIS_ONLY,
    RUNTIME_MODE_PRODUCT_ONE_CANDIDATE,
    build_portfolio_review_plan,
)
from src.product_bundle_paths import (
    build_output_manifest_discovery_extra,
    portfolio_xray_has_block_2_1,
    product_bundle_manifest_extra,
)
from src.snapshot import _xray_summary_from_output_dir
from test_block_2_1_asset_allocation import assert_block_2_1_product_contract


def _analysis_setup_for_fixture(fixture_name: str) -> dict[str, Any]:
    cfg = validate_mvp_fixture(fixture_name)
    cash_proxy, rf_source = resolve_cash_and_rf(cfg)
    return build_analysis_setup(
        cfg,
        portfolio_weights=dict(cfg.weights or {}),
        weights_source=cfg.weights_source,
        cash_proxy_ticker=cash_proxy,
        rf_source=rf_source,
        analysis_end="2026-04-30",
        windows_months=[36, 60, 120],
        returns_frequency="monthly",
        periods_per_year=12,
        run_context="report",
    )


def _seed_subject_report_inputs(
    subject_dir: Path,
    *,
    setup: dict[str, Any],
    weights: dict[str, float],
) -> None:
    subject_dir.mkdir(parents=True, exist_ok=True)
    write_json(subject_dir / "run_metadata.json", build_offline_run_metadata(setup))
    write_json(
        subject_dir / "snapshot_10y.json",
        snapshot_10y(
            {"cagr": 0.06, "vol_annual": 0.12, "max_drawdown": -0.2, "sharpe": 0.4},
            final_weights_total=weights,
        ),
    )
    write_json(subject_dir / "stress_report.json", {"stress_scorecard_v1": {}})


def test_xray_summary_from_output_dir_writes_block_2_1_demo_fixture(tmp_path: Path) -> None:
    fixture = "demo_usd_asset_allocation_with_cash_5pct.yml"
    setup = _analysis_setup_for_fixture(fixture)
    weights = {str(k): float(v) for k, v in (setup["analysis_portfolio"]["weights"] or {}).items()}
    subject = tmp_path / "analysis_subject"
    _seed_subject_report_inputs(subject, setup=setup, weights=weights)

    xray = _xray_summary_from_output_dir(subject)
    assert xray is not None
    assert portfolio_xray_has_block_2_1(xray)
    assert (subject / "portfolio_xray.json").is_file()

    block = xray["block_2_1_asset_allocation"]
    assert_block_2_1_product_contract(block)
    assert block["portfolio_composition_snapshot"]["total_holdings"] == 9
    assert block["portfolio_composition_snapshot"]["top1_holding"] == {
        "ticker": "SCHD",
        "weight_pct": 16.15,
    }


@pytest.mark.parametrize(
    "skip_candidates,candidate_ids,expected_mode",
    [
        (True, None, RUNTIME_MODE_PRODUCT_DIAGNOSIS_ONLY),
        (False, "equal_weight", RUNTIME_MODE_PRODUCT_ONE_CANDIDATE),
    ],
)
def test_portfolio_review_plan_product_modes_materialize_subject_first(
    tmp_path: Path,
    skip_candidates: bool,
    candidate_ids: str | None,
    expected_mode: str,
) -> None:
    cfg = validate_mvp_fixture("minimal_usd_no_cash.yml")
    plan = build_portfolio_review_plan(
        cfg,
        project_root=tmp_path,
        skip_candidates=skip_candidates,
        skip_compare=skip_candidates,
        candidate_ids=candidate_ids,
        skip_pdf=True,
    )
    assert plan.runtime_mode == expected_mode
    assert plan.steps[0].stage == "diagnosis"
    subject_argv = " ".join(plan.steps[0].argv)
    assert "--materialize-analysis-subject" in subject_argv
    if candidate_ids:
        assert len(plan.steps) == 2
        assert plan.steps[1].stage == "candidates"
    else:
        assert [step.stage for step in plan.steps] == ["diagnosis"]


def test_materialize_analysis_subject_writes_block_2_1_on_disk(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = validate_mvp_fixture("minimal_usd_with_cash.yml")
    cfg.output_dir_final = str(tmp_path / "Main portfolio")
    setup = _analysis_setup_for_fixture("minimal_usd_with_cash.yml")
    expected_weights = {str(k): float(v) for k, v in (cfg.weights or {}).items()}

    def fake_run_portfolio_report_for_weights(_cfg, weights, **kwargs):
        out = Path(kwargs["output_dir_final"])
        _seed_subject_report_inputs(out, setup=setup, weights=weights)
        refresh_analysis_subject_portfolio_xray(out)
        return {}, {"portfolio_valid": True}

    monkeypatch.setattr(
        run_report,
        "run_portfolio_report_for_weights",
        fake_run_portfolio_report_for_weights,
    )
    monkeypatch.setattr(run_report, "prepare_review_run_context", lambda *a, **k: None)

    run_report.run_materialize_analysis_subject_report(
        cfg,
        run_timestamp="2026-05-26T12:00:00",
        backtest_mode="dynamic_nan_safe",
        no_cache=True,
        review_mode="core",
        project_root=tmp_path,
    )

    sidecar = tmp_path / "Main portfolio" / "analysis_subject"
    xray = json.loads((sidecar / "portfolio_xray.json").read_text(encoding="utf-8"))
    assert portfolio_xray_has_block_2_1(xray)
    block = xray["block_2_1_asset_allocation"]
    by_asset = {r["name"]: r["weight_pct"] for r in block["capital_allocation_breakdown"]["by_asset"]}
    assert by_asset["Cash USD"] == pytest.approx(10.0)
    assert expected_weights["Cash USD"] == pytest.approx(0.10)


def test_output_manifest_subject_diagnostics_notes_block_2_1_nested(tmp_path: Path) -> None:
    subject = tmp_path / "analysis_subject"
    setup = _analysis_setup_for_fixture("minimal_usd_no_cash.yml")
    weights = {str(k): float(v) for k, v in (setup["analysis_portfolio"]["weights"] or {}).items()}
    _seed_subject_report_inputs(subject, setup=setup, weights=weights)
    refresh_analysis_subject_portfolio_xray(subject)

    policy = output_policy_for_profile("site_api")
    manifest_path = write_output_manifest(
        subject,
        policy=policy,
        run_kind="analysis_subject",
        generated_paths={"portfolio_xray": subject / "portfolio_xray.json"},
        extra=build_output_manifest_discovery_extra(
            {"portfolio_xray": str(subject / "portfolio_xray.json")}
        ),
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    note = manifest["subject_diagnostics_contract"]["portfolio_xray_json"]
    assert note["product_capital_structure_key"] == "block_2_1_asset_allocation"
    assert product_bundle_manifest_extra()["subject_diagnostics_contract"] == manifest[
        "subject_diagnostics_contract"
    ]
