"""Block 2.5 pipeline integration — analysis_subject portfolio_xray on product review paths."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import run_report
from mvp_offline_fixtures import (
    refresh_analysis_subject_portfolio_xray,
    seed_block_2_5_subject_dir,
    validate_mvp_fixture,
    write_json,
)
from src.analysis_setup import build_analysis_setup
from src.config import resolve_cash_and_rf
from src.output_policy import output_policy_for_profile, write_output_manifest
from src.product_bundle_paths import (
    PORTFOLIO_XRAY_BLOCK_2_5_KEY,
    build_output_manifest_discovery_extra,
    portfolio_xray_has_block_2_5,
    product_bundle_manifest_extra,
)
from src.snapshot import _xray_summary_from_output_dir
from test_block_2_5_risk_budget import assert_block_2_5_product_contract


def _analysis_setup_for_fixture(fixture_name: str) -> dict:
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


def test_block_2_5_product_bundle_manifest_note() -> None:
    note = product_bundle_manifest_extra()["subject_diagnostics_contract"]["portfolio_xray_json"]

    assert note["product_risk_budget_key"] == PORTFOLIO_XRAY_BLOCK_2_5_KEY
    assert "Block 2.5 risk budget view" in note["note"]


def test_xray_summary_from_output_dir_writes_block_2_5_offline_fixture(tmp_path: Path) -> None:
    subject = tmp_path / "analysis_subject"
    setup = _analysis_setup_for_fixture("minimal_usd_no_cash.yml")
    weights = {str(k): float(v) for k, v in (setup["analysis_portfolio"]["weights"] or {}).items()}
    seed_block_2_5_subject_dir(
        subject,
        tickers=list(weights),
        analysis_setup=setup,
        weights=weights,
    )
    write_json(subject / "stress_report.json", {"stress_scorecard_v1": {}})

    xray = _xray_summary_from_output_dir(subject)
    assert xray is not None
    assert portfolio_xray_has_block_2_5(xray)
    assert (subject / "portfolio_xray.json").is_file()

    block = xray[PORTFOLIO_XRAY_BLOCK_2_5_KEY]
    assert_block_2_5_product_contract(block)
    assert block["status"] in {"ok", "partial"}
    assert len(block["assets"]) == len(weights)
    assert block["top1_rc_asset"]["ticker"] in weights


def test_portfolio_xray_has_block_2_5_helper_rejects_legacy_section_only() -> None:
    assert not portfolio_xray_has_block_2_5({"sections": {"risk_budget_view": {}}})


def test_materialize_analysis_subject_writes_block_2_5_on_disk(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = validate_mvp_fixture("minimal_usd_with_cash.yml")
    cfg.output_dir_final = str(tmp_path / "Main portfolio")
    setup = _analysis_setup_for_fixture("minimal_usd_with_cash.yml")
    weights = {str(k): float(v) for k, v in (cfg.weights or {}).items()}
    expected_tickers = {t for t, w in weights.items() if w > 0}

    def fake_run_portfolio_report_for_weights(_cfg, weights_arg, **kwargs):
        out = Path(kwargs["output_dir_final"])
        seed_block_2_5_subject_dir(
            out,
            tickers=[t for t in weights_arg if t != "Cash USD"],
            analysis_setup=setup,
            weights=weights_arg,
        )
        write_json(out / "stress_report.json", {"stress_scorecard_v1": {}})
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
    assert portfolio_xray_has_block_2_5(xray)
    block = xray[PORTFOLIO_XRAY_BLOCK_2_5_KEY]
    assert_block_2_5_product_contract(block)
    assert block["status"] in {"ok", "partial"}
    assert {row["ticker"] for row in block["assets"]} == expected_tickers


def test_output_manifest_subject_diagnostics_notes_block_2_5_nested(tmp_path: Path) -> None:
    subject = tmp_path / "analysis_subject"
    setup = _analysis_setup_for_fixture("minimal_usd_no_cash.yml")
    weights = {str(k): float(v) for k, v in (setup["analysis_portfolio"]["weights"] or {}).items()}
    seed_block_2_5_subject_dir(
        subject,
        tickers=list(weights),
        analysis_setup=setup,
        weights=weights,
    )
    write_json(subject / "stress_report.json", {"stress_scorecard_v1": {}})
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
    assert note["product_risk_budget_key"] == PORTFOLIO_XRAY_BLOCK_2_5_KEY
    assert "Block 2.5" in note["note"]
    assert product_bundle_manifest_extra()["subject_diagnostics_contract"] == manifest[
        "subject_diagnostics_contract"
    ]
