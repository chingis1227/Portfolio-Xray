"""Input Layer MVP regression gate (ExecPlan Session 08).

Cross-cutting acceptance for Core MVP input: three-field config, USD system defaults,
real cash, disclosure export, portfolio-review runtime modes, and six-file product bundle
after one-candidate compare. Offline only; no live market data.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import run_report
from mvp_offline_fixtures import (
    MVP_FIXTURE_DIR,
    PRODUCT_BUNDLE_ARTIFACTS,
    load_mvp_fixture_yaml,
    seed_product_bundle_offline_workspace,
    validate_mvp_fixture,
)
from src.analysis_setup import build_analysis_setup
from src.candidate_comparison import write_candidate_comparison_outputs
from src.config import resolve_cash_and_rf
from src.config_schema import validate_config
from src.input_assumptions import build_input_assumptions_from_analysis_setup
from src.portfolio_review_workflow import (
    RUNTIME_MODE_PRODUCT_DIAGNOSIS_ONLY,
    RUNTIME_MODE_PRODUCT_ONE_CANDIDATE,
    build_portfolio_review_plan,
)
from src.real_cash import collect_real_cash_tickers, partition_market_data_tickers
from src.workflow_state import WORKFLOW_STATE_ONE_CANDIDATE

MVP_FIXTURE_NAMES = ("minimal_usd_no_cash.yml", "minimal_usd_with_cash.yml")

DEFERRED_CONFIG_KEYS = frozenset(
    {
        "client_profile",
        "portfolio_value",
        "initial_investable_amount",
        "liquidity_need_months",
        "monthly_expenses",
        "liquidity_need",
        "target_nominal_return_annual",
        "target_vol_annual",
        "target_max_drawdown_pct",
        "min_acceptable_return",
        "horizon_years",
        "cash_policy",
        "max_single_security_weight_pct",
        "min_single_security_weight_pct",
    }
)


def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*_args, **_kwargs):
        raise AssertionError("Input Layer MVP regression must stay offline")

    import src.data_fred as data_fred
    import src.data_yf as data_yf

    monkeypatch.setattr(data_yf, "download_all", _boom)
    monkeypatch.setattr(data_fred, "fetch_fred_series", _boom, raising=False)


def _explicit_factory_run(*candidate_ids: str) -> dict[str, Any]:
    return {
        "factory_profile_id": "explicit_list",
        "generated_at": "2026-05-26T18:00:00+00:00",
        "steps": [
            {"candidate_id": cid, "execution_action": "succeeded"} for cid in candidate_ids
        ],
    }


def _load_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


@pytest.mark.parametrize("fixture_name", MVP_FIXTURE_NAMES)
def test_mvp_fixture_yaml_has_only_core_user_keys(fixture_name: str) -> None:
    raw = load_mvp_fixture_yaml(fixture_name)
    assert set(raw.keys()) <= {"investor_currency", "tickers", "current_weights"}
    for key in DEFERRED_CONFIG_KEYS:
        assert key not in raw


@pytest.mark.parametrize("fixture_name", MVP_FIXTURE_NAMES)
def test_mvp_fixture_validates_without_deferred_fields(fixture_name: str) -> None:
    cfg = validate_mvp_fixture(fixture_name)

    assert cfg.investor_currency == "USD"
    assert cfg.analysis_mode == "analyze_current_weights"
    assert cfg.analysis_subject["type"] == "current_portfolio"
    assert sum(cfg.weights.values()) == pytest.approx(1.0, abs=1e-6)
    for key in DEFERRED_CONFIG_KEYS:
        value = getattr(cfg, key, None)
        if key in ("liquidity_need_months", "monthly_expenses", "portfolio_value"):
            assert value is None or float(value or 0) == 0.0
        elif key == "client_profile":
            assert value in (None, "", "balanced_growth")


@pytest.mark.parametrize("fixture_name", MVP_FIXTURE_NAMES)
def test_mvp_usd_system_defaults_when_omitted_from_yaml(fixture_name: str) -> None:
    cfg = validate_mvp_fixture(fixture_name)
    cash_proxy, rf_source = resolve_cash_and_rf(cfg)

    assert cash_proxy == "BIL"
    assert rf_source == "FRED:DTB3"
    assert cfg.benchmark_base_ticker == "SPY"
    # Cash proxy / RF resolve at runtime when omitted from YAML (not stored on PortfolioConfig).
    assert cfg.cash_proxy_ticker in (None, "")
    assert cfg.rf_source in (None, "")


@pytest.mark.parametrize("fixture_name", MVP_FIXTURE_NAMES)
def test_mvp_disclosure_chain_core_mvp_requirements_met(fixture_name: str) -> None:
    cfg = validate_mvp_fixture(fixture_name)
    weights = {str(k): float(v) for k, v in (cfg.weights or {}).items()}
    cash_proxy, rf_source = resolve_cash_and_rf(cfg)
    setup = build_analysis_setup(
        cfg,
        portfolio_weights=weights,
        weights_source=cfg.weights_source,
        portfolio_role_override="analysis_subject",
        cash_proxy_ticker=cash_proxy,
        rf_source=rf_source,
        analysis_end="2026-04-30",
        windows_months=[36, 60, 120],
        returns_frequency="monthly",
        periods_per_year=12,
        run_context="report",
    )
    assumptions = build_input_assumptions_from_analysis_setup(setup)

    assert assumptions["input_surface"]["profile"] == "core_mvp"
    assert assumptions["input_surface"]["core_mvp_requirements_met"] is True
    assert assumptions["field_tiers"]["run_disclosure"]["core_mvp"]["requirements_met"] is True
    assert assumptions["analysis_subject"]["type"] == "current_portfolio"
    assert assumptions["analysis_subject"]["resolution_source"] == "config.analysis_subject"


def test_mvp_with_cash_real_cash_partition_and_handling() -> None:
    cfg = validate_mvp_fixture("minimal_usd_with_cash.yml")
    download, real_cash = partition_market_data_tickers(list(cfg.tickers))

    assert "Cash USD" in real_cash
    assert "Cash USD" not in download
    assert collect_real_cash_tickers(tickers=cfg.tickers, weights=cfg.weights) == ["Cash USD"]

    setup = build_analysis_setup(
        cfg,
        portfolio_weights=dict(cfg.weights or {}),
        weights_source=cfg.weights_source,
        cash_proxy_ticker="BIL",
        rf_source="FRED:DTB3",
        analysis_end="2026-04-30",
        windows_months=[36, 60, 120],
        returns_frequency="monthly",
        periods_per_year=12,
        run_context="report",
    )
    handling = setup["analysis_portfolio"]["cash_handling"]
    assert handling["cash_proxy_ticker"] == "BIL"
    assert handling["real_cash_distinct_from_cash_proxy"] is True
    holdings = handling["real_cash_holdings"]
    assert len(holdings) == 1
    assert holdings[0]["ticker"] == "Cash USD"
    assert holdings[0]["weight"] == pytest.approx(0.10)
    assert cfg.weights.get("BIL") is None


@pytest.mark.parametrize("fixture_name", MVP_FIXTURE_NAMES)
def test_mvp_materialization_resolves_current_portfolio(fixture_name: str) -> None:
    cfg = validate_mvp_fixture(fixture_name)
    mat = run_report.resolve_analysis_subject_materialization(cfg)

    assert mat["status"] == "resolved"
    assert mat["subject"]["type"] == "current_portfolio"
    assert sum(mat["weights"].values()) == pytest.approx(1.0, abs=1e-6)


def test_mvp_portfolio_review_product_runtime_modes(tmp_path: Path) -> None:
    cfg = validate_mvp_fixture("minimal_usd_no_cash.yml")

    diagnosis_plan = build_portfolio_review_plan(
        cfg,
        project_root=tmp_path,
        skip_candidates=True,
        skip_compare=True,
        skip_pdf=True,
    )
    assert diagnosis_plan.runtime_mode == RUNTIME_MODE_PRODUCT_DIAGNOSIS_ONLY
    assert [step.stage for step in diagnosis_plan.steps] == ["diagnosis"]
    assert "run_optimization.py" not in " ".join(diagnosis_plan.steps[0].argv)

    one_candidate_plan = build_portfolio_review_plan(
        cfg,
        project_root=tmp_path,
        candidate_ids="equal_weight",
        skip_pdf=True,
    )
    assert one_candidate_plan.runtime_mode == RUNTIME_MODE_PRODUCT_ONE_CANDIDATE
    assert one_candidate_plan.workflow_state.state == WORKFLOW_STATE_ONE_CANDIDATE
    assert [step.stage for step in one_candidate_plan.steps] == ["diagnosis", "candidates"]
    factory_argv = " ".join(one_candidate_plan.steps[1].argv)
    assert "equal_weight" in factory_argv
    assert "--then-compare" in factory_argv
    assert "run_optimization.py" not in factory_argv


def test_universe_only_config_remains_legacy_advanced_profile() -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "tickers": ["VOO", "BND"],
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
    assumptions = build_input_assumptions_from_analysis_setup(setup)

    assert cfg.analysis_subject == {}
    assert assumptions["input_surface"]["profile"] == "legacy_advanced"
    assert assumptions["input_surface"]["core_mvp_requirements_met"] is False


def test_mvp_product_bundle_one_candidate_compare_regression(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Eight-ticker MVP fixture + explicit equal_weight -> six product bundle JSON files."""
    _block_network(monkeypatch)
    raw = dict(load_mvp_fixture_yaml("minimal_usd_no_cash.yml"))
    raw["output_dir_final"] = str(tmp_path / "Main portfolio")
    cfg = validate_config(raw)
    seeded = seed_product_bundle_offline_workspace(tmp_path, cfg)
    main_dir = seeded["main_dir"]

    paths = write_candidate_comparison_outputs(
        cfg,
        project_root=tmp_path,
        factory_run=_explicit_factory_run("equal_weight"),
        write_txt=False,
    )

    missing: list[str] = []
    for rel_path, schema_version in PRODUCT_BUNDLE_ARTIFACTS:
        artifact_path = main_dir / rel_path
        if not artifact_path.is_file():
            missing.append(rel_path)
            continue
        doc = _load_json(artifact_path)
        assert doc.get("schema_version") == schema_version, rel_path
    assert not missing

    run_metadata = _load_json(seeded["analysis_subject_dir"] / "run_metadata.json")
    assumptions = run_metadata["input_assumptions"]
    assert assumptions["input_surface"]["profile"] == "core_mvp"
    assert assumptions["input_surface"]["core_mvp_requirements_met"] is True

    current_vs = _load_json(main_dir / "current_vs_candidate.json")
    verdict = _load_json(main_dir / "decision_verdict.json")
    manifest = _load_json(main_dir / "output_manifest.json")

    assert current_vs["view_mode"] == "one_candidate"
    assert current_vs["selected_candidate_ids"] == ["equal_weight"]
    assert verdict["selected_candidate_id"] == "equal_weight"
    assert verdict.get("source_artifacts", {}).get("selection_decision") is None
    assert manifest.get("advanced_package_generated") is False
    assert manifest.get("primary_output_surface") == "product_bundle"
    assert paths.get("selection_decision_json") is None

    discovery = manifest.get("product_discovery") or {}
    assert discovery.get("product_bundle_complete") is True


def test_mvp_fixture_files_live_under_fixtures_dir() -> None:
    for name in MVP_FIXTURE_NAMES:
        path = MVP_FIXTURE_DIR / name
        assert path.is_file(), f"missing MVP fixture: {path}"
