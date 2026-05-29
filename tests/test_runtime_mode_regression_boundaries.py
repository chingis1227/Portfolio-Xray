"""Session 08 — runtime mode regression boundaries (product vs research).

Enforces separate contracts for product_one_candidate / product_shortlist / diagnosis-only
versus research_batch compare outputs. Research batch must keep the advanced package;
product explicit-list runs must not let stale folders or Selection Engine drive verdicts.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mvp_offline_fixtures import (
    PRODUCT_BUNDLE_ARTIFACTS,
    seed_analysis_subject_diagnosis_bundle,
)
from run_portfolio_review import resolve_candidate_execution_flags
from src.candidate_comparison import write_candidate_comparison_outputs
from src.config_schema import validate_config
from src.portfolio_review_workflow import (
    RUNTIME_MODE_PRODUCT_DIAGNOSIS_ONLY,
    RUNTIME_MODE_PRODUCT_ONE_CANDIDATE,
    RUNTIME_MODE_PRODUCT_SHORTLIST,
    RUNTIME_MODE_RESEARCH_BATCH,
    build_portfolio_review_plan,
    resolve_portfolio_review_runtime_mode,
)
from src.product_bundle_paths import PRODUCT_BUNDLE_MANIFEST_KEYS
from src.workflow_state import WORKFLOW_STATE_ONE_CANDIDATE

ADVANCED_PACKAGE_PATH_KEYS: frozenset[str] = frozenset(
    {
        "portfolio_health_score_json",
        "robustness_scorecard_json",
        "selection_decision_json",
        "action_plan_json",
        "monitoring_diff_json",
        "decision_journal_json",
        "tradeoff_explanation_json",
        "model_risk_diagnostics_json",
        "assumption_sensitivity_json",
        "pareto_dominance_json",
        "regret_analysis_json",
    }
)


def _snapshot_10y(metrics: dict) -> dict:
    return {
        "schema_version": "snapshot_10y_v1",
        "analysis_end": "2026-04-30",
        "window_label": "10y",
        "metrics": metrics,
        "stress_suite_results": {
            "overall": "PASS",
            "fail_reason_code": None,
            "scenarios": [{"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.05, "pass": True}],
        },
        "constraints_status": {"target_vol": "PASS", "max_dd": "PASS"},
    }


def _run_metadata(portfolio_role: str) -> dict:
    return {
        "run_info": {"analysis_end_date": "2026-04-30"},
        "portfolio_valid": True,
        "analysis_setup": {
            "portfolio_input": {"source_analysis_mode": "optimize_from_universe"},
            "analysis_portfolio": {
                "portfolio_role": portfolio_role,
                "weight_source": "optimization_result_released",
            },
        },
    }


def _seed_compare_workspace(
    root: Path,
    *,
    extra_candidates: tuple[tuple[str, dict], ...] = (),
) -> tuple[Path, dict]:
    """Subject + equal_weight + optional stale/high-rank candidates."""
    main = root / "Main portfolio"
    subject = main / "analysis_subject"
    subject.mkdir(parents=True)
    seed_analysis_subject_diagnosis_bundle(subject)
    with open(subject / "snapshot_10y.json", "w", encoding="utf-8") as handle:
        json.dump(
            _snapshot_10y({"cagr": 0.07, "vol_annual": 0.12, "max_drawdown": -0.2}),
            handle,
        )
    with open(subject / "run_metadata.json", "w", encoding="utf-8") as handle:
        json.dump(_run_metadata("user_current_portfolio"), handle)

    candidates = [
        ("equal-weight portfolio", {"cagr": 0.075, "vol_annual": 0.10, "max_drawdown": -0.16}),
        *extra_candidates,
    ]
    for folder, metrics in candidates:
        candidate_dir = root / folder
        candidate_dir.mkdir(parents=True, exist_ok=True)
        with open(candidate_dir / "snapshot_10y.json", "w", encoding="utf-8") as handle:
            json.dump(_snapshot_10y(metrics), handle)

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO"],
            "analysis_subject": {"type": "current_portfolio", "weights": {"VOO": 1.0}},
        }
    )
    return main, cfg


def _explicit_factory_run(*candidate_ids: str) -> dict:
    return {
        "factory_profile_id": "explicit_list",
        "generated_at": "2026-05-26T14:00:00+00:00",
        "steps": [{"candidate_id": cid, "execution_action": "succeeded"} for cid in candidate_ids],
    }


def _load_manifest(paths: dict[str, Path]) -> dict:
    with open(paths["output_manifest_json"], encoding="utf-8") as handle:
        return json.load(handle)


@pytest.mark.parametrize(
    ("kwargs", "expected_mode"),
    [
        ({}, RUNTIME_MODE_RESEARCH_BATCH),
        ({"skip_candidates": True, "skip_compare": True}, RUNTIME_MODE_PRODUCT_DIAGNOSIS_ONLY),
        ({"candidate_ids": "equal_weight"}, RUNTIME_MODE_PRODUCT_ONE_CANDIDATE),
        ({"candidate_ids": "equal_weight,risk_parity"}, RUNTIME_MODE_PRODUCT_SHORTLIST),
        ({"review_mode": "full"}, RUNTIME_MODE_RESEARCH_BATCH),
        ({"candidate_profile": "default_v1"}, RUNTIME_MODE_RESEARCH_BATCH),
    ],
)
def test_runtime_mode_resolution_matrix(kwargs: dict, expected_mode: str) -> None:
    assert resolve_portfolio_review_runtime_mode(**kwargs) == expected_mode


def test_regression_cli_default_is_product_diagnosis_only() -> None:
    skip_candidates, skip_compare, run_candidates = resolve_candidate_execution_flags()
    assert run_candidates is False
    assert skip_candidates is True
    assert skip_compare is True
    assert (
        resolve_portfolio_review_runtime_mode(
            skip_candidates=skip_candidates, skip_compare=skip_compare
        )
        == RUNTIME_MODE_PRODUCT_DIAGNOSIS_ONLY
    )


def test_regression_with_candidates_cli_is_research_batch() -> None:
    skip_candidates, skip_compare, run_candidates = resolve_candidate_execution_flags(
        with_candidates=True
    )
    assert run_candidates is True
    assert (
        resolve_portfolio_review_runtime_mode(
            skip_candidates=skip_candidates,
            skip_compare=skip_compare,
        )
        == RUNTIME_MODE_RESEARCH_BATCH
    )


def test_product_one_candidate_compare_contract_excludes_advanced_package(
    tmp_path: Path,
) -> None:
    main, cfg = _seed_compare_workspace(
        tmp_path,
        extra_candidates=(
            ("risk-parity portfolio", {"cagr": 0.09, "vol_annual": 0.08, "max_drawdown": -0.10}),
        ),
    )
    with open(main / "candidate_factory_run.json", "w", encoding="utf-8") as handle:
        json.dump(_explicit_factory_run("equal_weight"), handle)

    paths = write_candidate_comparison_outputs(
        cfg,
        project_root=tmp_path,
        factory_run=_explicit_factory_run("equal_weight"),
        write_txt=False,
    )

    assert ADVANCED_PACKAGE_PATH_KEYS.isdisjoint(paths.keys())

    with open(paths["current_vs_candidate_json"], encoding="utf-8") as handle:
        current_vs = json.load(handle)
    with open(paths["decision_verdict_json"], encoding="utf-8") as handle:
        verdict = json.load(handle)

    assert current_vs["selected_candidate_ids"] == ["equal_weight"]
    assert verdict["selected_candidate_id"] == "equal_weight"
    assert verdict["source_artifacts"].get("selection_decision") is None

    manifest = _load_manifest(paths)
    assert manifest["advanced_package_generated"] is False
    assert manifest["primary_output_surface"] == "product_bundle"
    discovery = manifest.get("product_discovery") or {}
    assert discovery.get("product_bundle_complete") is True
    assert set(discovery.get("product_bundle_paths") or {}) == set(PRODUCT_BUNDLE_MANIFEST_KEYS)

    with open(paths["candidate_comparison_json"], encoding="utf-8") as handle:
        comparison = json.load(handle)
    assert comparison["product_candidate_scope"]["candidate_ids"] == ["equal_weight"]
    product_ids = {row["candidate_id"] for row in comparison["candidates"]}
    assert product_ids >= {"analysis_subject", "equal_weight"}
    assert "risk_parity" not in product_ids
    with open(paths["candidate_comparison_registry_json"], encoding="utf-8") as handle:
        registry = json.load(handle)
    assert any(row["candidate_id"] == "risk_parity" for row in registry["candidates"])


def test_research_batch_compare_contract_preserves_advanced_package(tmp_path: Path) -> None:
    main, cfg = _seed_compare_workspace(
        tmp_path,
        extra_candidates=(
            ("risk-parity portfolio", {"cagr": 0.09, "vol_annual": 0.08, "max_drawdown": -0.10}),
        ),
    )

    paths = write_candidate_comparison_outputs(
        cfg,
        project_root=tmp_path,
        factory_run=None,
        advanced_package=True,
        write_txt=False,
    )

    assert ADVANCED_PACKAGE_PATH_KEYS.issubset(paths.keys())

    with open(paths["selection_decision_json"], encoding="utf-8") as handle:
        selection = json.load(handle)
    assert selection.get("schema_version") == "selection_decision_v1"
    assert isinstance(selection.get("composite_ranking"), list)
    assert len(selection["composite_ranking"]) >= 1

    manifest = _load_manifest(paths)
    assert manifest["advanced_package_generated"] is True
    by_category = manifest.get("generated_paths_by_category") or {}
    assert by_category.get("advanced_evidence")

    with open(paths["decision_verdict_json"], encoding="utf-8") as handle:
        verdict = json.load(handle)
    assert verdict.get("source_artifacts", {}).get("selection_decision") == (
        "selection_decision.json"
    )


def test_product_shortlist_scopes_both_explicit_candidates(tmp_path: Path) -> None:
    _, cfg = _seed_compare_workspace(
        tmp_path,
        extra_candidates=(
            ("risk-parity portfolio", {"cagr": 0.09, "vol_annual": 0.08, "max_drawdown": -0.10}),
            ("minimum-variance portfolio", {"cagr": 0.05, "vol_annual": 0.07, "max_drawdown": -0.12}),
        ),
    )
    factory_run = _explicit_factory_run("equal_weight", "risk_parity")

    paths = write_candidate_comparison_outputs(
        cfg,
        project_root=tmp_path,
        factory_run=factory_run,
        write_txt=False,
    )

    with open(paths["current_vs_candidate_json"], encoding="utf-8") as handle:
        current_vs = json.load(handle)
    assert set(current_vs["selected_candidate_ids"]) == {"equal_weight", "risk_parity"}
    assert current_vs["view_mode"] == "shortlist"
    assert "selection_decision_json" not in paths

    with open(paths["candidate_comparison_json"], encoding="utf-8") as handle:
        comparison = json.load(handle)
    assert set(comparison["product_candidate_scope"]["candidate_ids"]) == {
        "equal_weight",
        "risk_parity",
    }
    product_ids = {row["candidate_id"] for row in comparison["candidates"]}
    assert product_ids >= {"analysis_subject", "equal_weight", "risk_parity"}
    assert "minimum_variance" not in product_ids
    assert paths["candidate_comparison_registry_json"].is_file()


def test_product_bundle_schema_versions_in_product_mode(tmp_path: Path) -> None:
    main, cfg = _seed_compare_workspace(tmp_path)
    write_candidate_comparison_outputs(
        cfg,
        project_root=tmp_path,
        factory_run=_explicit_factory_run("equal_weight"),
        write_txt=False,
    )
    missing: list[str] = []
    for rel_path, schema_version in PRODUCT_BUNDLE_ARTIFACTS:
        artifact_path = main / rel_path
        if not artifact_path.is_file():
            missing.append(rel_path)
            continue
        with open(artifact_path, encoding="utf-8") as handle:
            doc = json.load(handle)
        if doc.get("schema_version") != schema_version:
            missing.append(f"{rel_path} (schema {doc.get('schema_version')!r})")
    assert not missing, "product bundle schema mismatch: " + ", ".join(missing)


def test_stale_higher_rank_candidate_does_not_override_product_verdict(tmp_path: Path) -> None:
    """Full comparison may rank risk_parity higher; product verdict must stay on explicit id."""
    _, cfg = _seed_compare_workspace(
        tmp_path,
        extra_candidates=(
            ("risk-parity portfolio", {"cagr": 0.15, "vol_annual": 0.05, "max_drawdown": -0.05}),
        ),
    )
    paths = write_candidate_comparison_outputs(
        cfg,
        project_root=tmp_path,
        factory_run=_explicit_factory_run("equal_weight"),
        write_txt=False,
    )
    with open(paths["candidate_comparison_registry_json"], encoding="utf-8") as handle:
        registry = json.load(handle)
    rp_rows = [r for r in registry["candidates"] if r["candidate_id"] == "risk_parity"]
    assert rp_rows, "fixture must include risk_parity in full registry comparison"

    with open(paths["candidate_comparison_json"], encoding="utf-8") as handle:
        comparison = json.load(handle)
    assert "risk_parity" not in {row["candidate_id"] for row in comparison["candidates"]}

    with open(paths["decision_verdict_json"], encoding="utf-8") as handle:
        verdict = json.load(handle)
    assert verdict["selected_candidate_id"] == "equal_weight"


def test_plan_with_candidates_is_research_batch_not_product(tmp_path: Path) -> None:
    cfg = validate_config(
        {
            "tickers": ["VOO", "BND"],
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "analysis_subject": {
                "type": "current_portfolio",
                "weights": {"VOO": 0.6, "BND": 0.4},
            },
        }
    )
    plan = build_portfolio_review_plan(cfg, project_root=tmp_path, skip_pdf=True)
    assert plan.runtime_mode == RUNTIME_MODE_RESEARCH_BATCH
    factory_argv = plan.steps[1].argv
    assert "--profile" in factory_argv
    assert "--candidates" not in factory_argv


def test_plan_explicit_candidate_is_product_one_candidate(tmp_path: Path) -> None:
    cfg = validate_config(
        {
            "tickers": ["VOO"],
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "analysis_subject": {"type": "current_portfolio", "weights": {"VOO": 1.0}},
        }
    )
    plan = build_portfolio_review_plan(
        cfg,
        project_root=tmp_path,
        candidate_ids="equal_weight",
        skip_pdf=True,
    )
    assert plan.runtime_mode == RUNTIME_MODE_PRODUCT_ONE_CANDIDATE
    assert plan.workflow_state.state == WORKFLOW_STATE_ONE_CANDIDATE
    assert "equal_weight" in plan.steps[1].argv
