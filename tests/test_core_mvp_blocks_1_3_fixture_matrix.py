from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
import yaml

from run_report import run_materialize_analysis_subject_report
from src.config_schema import validate_config
from src.real_cash import partition_market_data_tickers


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures" / "mvp_portfolios"

REAL_CASH_LABELS = {"CASH", "CASH USD"}
REQUIRED_BLOCK2_KEYS = {
    "block_2_1_asset_allocation",
    "block_2_2_portfolio_metrics",
    "block_2_3_factor_exposure",
    "block_2_4_hidden_exposure",
    "block_2_5_risk_budget_view",
    "block_2_6_portfolio_weakness_map",
}
REQUIRED_BLOCK3_KEYS = {
    "scenario_library_meta",
    "stress_results_v1",
    "hedge_gap_analysis_v1",
    "current_portfolio_stress_scorecard_v1",
}
EXPECTED_SYNTHETIC_IDS = {
    "equity_shock",
    "credit_shock",
    "rates_shock",
    "inflation_stagflation",
    "liquidity_shock",
    "usd_shock",
    "commodity_shock",
    "recession_severe",
}
EXPECTED_HISTORICAL_IDS = {"dotcom", "2008", "2020", "2022", "banking_2023"}

FORBIDDEN_EXACT_KEYS = {
    "pass",
    "mandate_pass",
    "mandate_status",
    "pass_fail",
    "loss_ok",
    "max_dd_limit",
    "mandate",
    "suitability",
    "client_profile",
    "target_return",
    "target_volatility",
    "target_max_drawdown",
}
FORBIDDEN_EXACT_ARTIFACT_KEYS = {
    "candidate_launchpad_json",
    "candidate_comparison_json",
    "current_vs_candidate_json",
    "decision_verdict_json",
    "selection_decision_json",
    "what_changed_summary_json",
    "candidate_factory_run_json",
    "candidate_factory_manifest_json",
    "run_result_json",
    "portfolio_weights_yml",
    "portfolio_weights_yaml",
    "portfolio_comparison_json",
    "ew_rp_comparison_json",
}


def _load_yaml(path: Path) -> dict[str, Any]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(doc, dict):
        raise AssertionError(f"Fixture is not a YAML object: {path}")
    return doc


def _json_load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _has_legacy_scope_false(ancestors: list[Any]) -> bool:
    for node in ancestors:
        if not isinstance(node, dict):
            continue
        scope = node.get("_scope")
        if isinstance(scope, dict) and scope.get("product_surface") is False:
            return True
    return False


def _is_nullish(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def _has_active_forbidden_hits(obj: Any, ancestors: list[Any] | None = None) -> bool:
    if ancestors is None:
        ancestors = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_text = str(key)
            if key_text in FORBIDDEN_EXACT_KEYS or key_text in FORBIDDEN_EXACT_ARTIFACT_KEYS:
                if not _has_legacy_scope_false([*ancestors, obj]) and not _is_nullish(value):
                    return True
            if _has_active_forbidden_hits(value, [*ancestors, obj]):
                return True
    elif isinstance(obj, list):
        for row in obj:
            if _has_active_forbidden_hits(row, [*ancestors, obj]):
                return True
    return False


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.live_core
def test_core_mvp_blocks_1_3_fixture_matrix_materialize_and_validate(tmp_path: Path) -> None:
    fixture_paths = sorted(FIXTURES_DIR.glob("fixture_matrix_fx*.yml"))
    assert len(fixture_paths) == 7, "Expected exactly 7 fixture matrix YAML files"

    for fixture_path in fixture_paths:
        fixture_id = fixture_path.stem.replace("fixture_matrix_", "")
        fixture = _load_yaml(fixture_path)

        payload = dict(fixture)
        payload["output_dir_final"] = str(tmp_path / fixture_id)
        cfg = validate_config(payload)

        run_materialize_analysis_subject_report(
            cfg,
            run_timestamp=datetime.now(timezone.utc).isoformat(),
            backtest_mode="dynamic_nan_safe",
            no_cache=False,
            output_profile="site_api",
            review_mode="core",
            project_root=REPO_ROOT,
            use_review_run_context=True,
        )

        out_dir = Path(cfg.output_dir_final) / "analysis_subject"
        run_metadata_path = out_dir / "run_metadata.json"
        portfolio_xray_path = out_dir / "portfolio_xray.json"
        stress_report_path = out_dir / "stress_report.json"

        assert run_metadata_path.is_file(), f"{fixture_id}: missing run_metadata.json"
        assert portfolio_xray_path.is_file(), f"{fixture_id}: missing portfolio_xray.json"
        assert stress_report_path.is_file(), f"{fixture_id}: missing stress_report.json"

        run_metadata = _json_load(run_metadata_path)
        portfolio_xray = _json_load(portfolio_xray_path)
        stress_report = _json_load(stress_report_path)
        output_manifest_path = out_dir / "output_manifest.json"
        output_manifest = _json_load(output_manifest_path) if output_manifest_path.is_file() else {}

        # Block 1: basic contract and real-cash behavior.
        assert run_metadata.get("resolved_config", {}).get("investor_currency") == "USD", f"{fixture_id}: missing investor_currency"

        fixture_tickers = [str(t) for t in (fixture.get("tickers") or [])]
        download_tickers, real_cash_tickers = partition_market_data_tickers(fixture_tickers)
        for t in fixture_tickers:
            if str(t).strip().upper() in REAL_CASH_LABELS:
                assert t not in download_tickers, f"{fixture_id}: real cash ticker appeared in download set"
                assert t in real_cash_tickers, f"{fixture_id}: real cash ticker missing in real-cash partition"

        fixture_weights = fixture.get("current_weights") or {}
        fixture_real_cash = [t for t in fixture_weights.keys() if str(t).strip().upper() in REAL_CASH_LABELS and float(fixture_weights[t]) > 0]
        cash_handling = (
            run_metadata.get("analysis_setup", {})
            .get("analysis_portfolio", {})
            .get("cash_handling", {})
        )
        rm_real_cash = {str(row.get("ticker") or "") for row in (cash_handling.get("real_cash_holdings") or [])}
        for t in fixture_real_cash:
            assert t in rm_real_cash, f"{fixture_id}: real cash ticker missing in run_metadata real_cash_holdings"
        if fixture_real_cash:
            assert cash_handling.get("real_cash_return_assumption") == "zero_return_zero_volatility_no_price_download"

        # Block 2: required X-Ray keys.
        assert REQUIRED_BLOCK2_KEYS <= set(portfolio_xray.keys()), f"{fixture_id}: missing Block 2 keys"

        # Block 3: required Stress keys and canonical scenario IDs.
        assert REQUIRED_BLOCK3_KEYS <= set(stress_report.keys()), f"{fixture_id}: missing Block 3 keys"

        v1 = stress_report.get("stress_results_v1") or {}
        synthetic_ids = {str(row.get("scenario_id") or "") for row in (v1.get("synthetic_scenarios") or []) if isinstance(row, dict)}
        historical_ids = {str(row.get("episode") or "") for row in (v1.get("historical_episodes") or []) if isinstance(row, dict)}
        assert EXPECTED_SYNTHETIC_IDS <= synthetic_ids, f"{fixture_id}: missing synthetic scenario IDs"
        assert EXPECTED_HISTORICAL_IDS <= historical_ids, f"{fixture_id}: missing historical scenario IDs"

        # Step 6 boundary: no active forbidden keys/artifacts on product-facing surfaces.
        assert not _has_active_forbidden_hits(run_metadata), f"{fixture_id}: active forbidden key in run_metadata"
        assert not _has_active_forbidden_hits(portfolio_xray), f"{fixture_id}: active forbidden key in portfolio_xray"
        assert not _has_active_forbidden_hits(stress_report), f"{fixture_id}: active forbidden key in stress_report"
        assert not _has_active_forbidden_hits(output_manifest), f"{fixture_id}: active forbidden key in output_manifest"
