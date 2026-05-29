"""Session 06 — architecture consistency regression guards.

Automated checks against doc/runtime drift and commentary boundary regressions
from docs/exec_plans/final_architecture_consistency_audit_plan.md Session 6.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

import run_report
from mvp_offline_fixtures import validate_mvp_fixture
from src.output_policy import OUTPUT_PROFILE_SITE_API, output_policy_for_profile
from src.portfolio_review_workflow import (
    RUNTIME_MODE_PRODUCT_DIAGNOSIS_ONLY,
    RUNTIME_MODE_PRODUCT_ONE_CANDIDATE,
    RUNTIME_MODE_RESEARCH_BATCH,
    build_portfolio_review_plan,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

POST_COMPARE_ROOT_ARTIFACTS = (
    "decision_verdict.json",
    "current_vs_candidate.json",
    "candidate_comparison.json",
)


def _run_portfolio_review_dry_run(*extra_argv: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "run_portfolio_review.py"),
            "--dry-run",
            *extra_argv,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize(
    ("extra_argv", "expected_runtime_mode", "expected_stages", "must_contain", "must_not_contain"),
    [
        (
            (),
            "product_diagnosis_only",
            "input -> diagnosis",
            ("factory profile: none", "Workflow state: diagnosis_only"),
            ("run_candidate_factory.py",),
        ),
        (
            ("--candidates", "equal_weight"),
            "product_one_candidate",
            "input -> diagnosis -> candidates",
            ("equal_weight", "--then-compare"),
            (),
        ),
        (
            ("--with-candidates",),
            "research_batch",
            "input -> diagnosis -> candidates",
            ("core_fast", "multiple_candidates"),
            (),
        ),
    ],
)
def test_dry_run_plan_stages_match_architecture_contract(
    extra_argv: tuple[str, ...],
    expected_runtime_mode: str,
    expected_stages: str,
    must_contain: tuple[str, ...],
    must_not_contain: tuple[str, ...],
) -> None:
    proc = _run_portfolio_review_dry_run(*extra_argv)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    out = proc.stdout
    assert f"Runtime mode: {expected_runtime_mode}" in out
    assert f"Stages: {expected_stages}" in out
    for token in must_contain:
        assert token in out
    for token in must_not_contain:
        assert token not in out


def test_site_api_output_policy_disables_txt_artifacts() -> None:
    policy = output_policy_for_profile(OUTPUT_PROFILE_SITE_API)
    assert policy.write_txt is False
    assert "txt" in policy.disabled_artifact_classes


def test_diagnosis_only_materialize_site_api_writes_no_commentary_or_root_verdict(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Default site_api materialize must not emit rule-based TXT; root compare is tombstoned."""
    from src.product_bundle_hygiene import NO_CANDIDATE_TOMBSTONE

    cfg = validate_mvp_fixture("minimal_usd_no_cash.yml")
    cfg.output_dir_final = str(tmp_path / "Main portfolio")
    variant_root = tmp_path / "Main portfolio"
    expected_weights = {str(k): float(v) for k, v in (cfg.weights or {}).items()}

    def fake_run_portfolio_report_for_weights(_cfg, weights, **kwargs):
        out = Path(kwargs["output_dir_final"])
        out.mkdir(parents=True, exist_ok=True)
        (out / "run_metadata.json").write_text("{}", encoding="utf-8")
        (out / "portfolio_xray.json").write_text(
            json.dumps({"block_2_1_asset_allocation": {"status": "available"}}),
            encoding="utf-8",
        )
        (out / "stress_report.json").write_text(
            json.dumps({"stress_results_v1": {"status": "available"}}),
            encoding="utf-8",
        )
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
    monkeypatch.setattr(run_report, "prepare_review_run_context", lambda *a, **k: None)

    run_report.run_materialize_analysis_subject_report(
        cfg,
        run_timestamp="2026-05-27T12:00:00",
        backtest_mode="dynamic_nan_safe",
        no_cache=True,
        review_mode="core",
        output_profile=OUTPUT_PROFILE_SITE_API,
        project_root=tmp_path,
    )

    subject_dir = variant_root / "analysis_subject"
    assert subject_dir.is_dir()
    assert expected_weights  # fixture sanity

    for name in ("commentary.txt", "stress_commentary.txt", "report.txt"):
        assert not (subject_dir / name).exists(), f"site_api must not write {name}"

    for name in POST_COMPARE_ROOT_ARTIFACTS:
        path = variant_root / name
        assert path.is_file(), f"diagnosis-only materialize must write tombstone {name}"
        doc = json.loads(path.read_text(encoding="utf-8"))
        assert doc.get("tombstone") == NO_CANDIDATE_TOMBSTONE, name
        assert doc.get("artifact_status") == "not_authoritative", name


def test_diagnosis_only_plan_matches_cli_default_flags(tmp_path: Path) -> None:
    cfg = validate_mvp_fixture("minimal_usd_no_cash.yml")
    plan = build_portfolio_review_plan(
        cfg,
        project_root=tmp_path,
        skip_candidates=True,
        skip_compare=True,
        skip_pdf=True,
    )
    assert plan.runtime_mode == RUNTIME_MODE_PRODUCT_DIAGNOSIS_ONLY
    assert [step.stage for step in plan.steps] == ["diagnosis"]


def test_one_candidate_plan_matches_demo_contract(tmp_path: Path) -> None:
    cfg = validate_mvp_fixture("minimal_usd_no_cash.yml")
    plan = build_portfolio_review_plan(
        cfg,
        project_root=tmp_path,
        candidate_ids="equal_weight",
        skip_pdf=True,
    )
    assert plan.runtime_mode == RUNTIME_MODE_PRODUCT_ONE_CANDIDATE
    assert [step.stage for step in plan.steps] == ["diagnosis", "candidates"]
    factory_argv = " ".join(plan.steps[1].argv)
    assert "equal_weight" in factory_argv
    assert "--then-compare" in factory_argv


def test_with_candidates_plan_is_research_batch(tmp_path: Path) -> None:
    cfg = validate_mvp_fixture("minimal_usd_no_cash.yml")
    plan = build_portfolio_review_plan(
        cfg,
        project_root=tmp_path,
        skip_pdf=True,
    )
    assert plan.runtime_mode == RUNTIME_MODE_RESEARCH_BATCH
    assert [step.stage for step in plan.steps] == ["diagnosis", "candidates"]
    factory_argv = " ".join(plan.steps[1].argv)
    assert "core_fast" in factory_argv
