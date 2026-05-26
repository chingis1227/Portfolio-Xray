"""Session 07 — one-candidate demo validation (runtime truth reset).

Offline acceptance for ``run_portfolio_review.py --candidates equal_weight``:
workflow plans one factory id; compare/verdict stay scoped when stale folders exist.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.validate_one_candidate_demo import validate_one_candidate_demo
from src.candidate_comparison import write_candidate_comparison_outputs
from src.config_schema import validate_config
from src.portfolio_review_workflow import (
    RUNTIME_MODE_PRODUCT_ONE_CANDIDATE,
    build_portfolio_review_plan,
)
from src.workflow_state import WORKFLOW_STATE_ONE_CANDIDATE

from mvp_offline_fixtures import seed_analysis_subject_diagnosis_bundle

REPO_ROOT = Path(__file__).resolve().parents[1]


def _snapshot_10y(metrics: dict) -> dict:
    return {
        "schema_version": "snapshot_10y_v1",
        "metrics": metrics,
        "risk_contribution": {"by_asset": []},
    }


def _run_metadata(portfolio_role: str) -> dict:
    return {
        "portfolio_role": portfolio_role,
        "config_fingerprint": "fp-test",
        "weights_source": "user_current_portfolio",
    }


def test_session07_dry_run_cli_equal_weight() -> None:
    """Canonical dry-run: runtime mode + factory argv + --then-compare."""
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "run_portfolio_review.py"),
            "--dry-run",
            "--candidates",
            "equal_weight",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    out = proc.stdout
    assert "Runtime mode: product_one_candidate" in out
    assert "equal_weight" in out
    assert "--then-compare" in out
    assert "run_optimization.py" not in out


def test_session07_workflow_plans_single_equal_weight_candidate(tmp_path: Path) -> None:
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
    plan = build_portfolio_review_plan(
        cfg,
        project_root=tmp_path,
        candidate_ids="equal_weight",
        skip_pdf=True,
    )
    factory_argv = plan.steps[1].argv
    assert plan.runtime_mode == RUNTIME_MODE_PRODUCT_ONE_CANDIDATE
    assert plan.workflow_state.state == WORKFLOW_STATE_ONE_CANDIDATE
    assert plan.workflow_state.candidate_ids == ("equal_weight",)
    assert "--candidates" in factory_argv and "equal_weight" in factory_argv
    assert "--then-compare" in factory_argv


def test_session07_product_scoping_with_stale_risk_parity_folder(tmp_path: Path) -> None:
    """Stale risk_parity on disk must not hijack product verdict for equal_weight."""
    main = tmp_path / "Main portfolio"
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

    for folder, metrics in (
        ("equal-weight portfolio", {"cagr": 0.075, "vol_annual": 0.10, "max_drawdown": -0.16}),
        ("risk-parity portfolio", {"cagr": 0.09, "vol_annual": 0.08, "max_drawdown": -0.10}),
    ):
        candidate_dir = tmp_path / folder
        candidate_dir.mkdir()
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
    factory_run = {
        "factory_profile_id": "explicit_list",
        "generated_at": "2026-05-26T12:00:00+00:00",
        "steps": [{"candidate_id": "equal_weight", "execution_action": "succeeded"}],
    }
    with open(main / "candidate_factory_run.json", "w", encoding="utf-8") as handle:
        json.dump(factory_run, handle)
    paths = write_candidate_comparison_outputs(
        cfg,
        project_root=tmp_path,
        factory_run=factory_run,
        write_txt=False,
    )

    ok, messages = validate_one_candidate_demo(main, expected_candidate_id="equal_weight")
    assert ok, "\n".join(messages)

    with open(paths["ai_commentary_context_json"], encoding="utf-8") as handle:
        ai_ctx = json.load(handle)
    assert ai_ctx.get("selected_candidate_id") in (None, "equal_weight") or (
        ai_ctx.get("decision_verdict", {}).get("selected_candidate_id") == "equal_weight"
    )

    manifest = json.loads(paths["output_manifest_json"].read_text(encoding="utf-8"))
    discovery = manifest.get("product_discovery") or {}
    assert set(discovery.get("product_bundle_paths") or {}) >= {
        "current_vs_candidate_json",
        "decision_verdict_json",
    }
    assert manifest.get("generated_paths_by_category", {}).get("product_bundle")


def test_session07_validator_detects_stale_verdict(tmp_path: Path) -> None:
    main = tmp_path / "Main portfolio"
    main.mkdir()
    (main / "candidate_factory_run.json").write_text(
        json.dumps({"steps": [{"candidate_id": "equal_weight"}]}),
        encoding="utf-8",
    )
    (main / "current_vs_candidate.json").write_text(
        json.dumps({"selected_candidate_ids": ["risk_parity"]}),
        encoding="utf-8",
    )
    (main / "decision_verdict.json").write_text(
        json.dumps({"selected_candidate_id": "risk_parity", "verdict_id": "rebalance"}),
        encoding="utf-8",
    )
    for name in ("ai_commentary_context.json", "what_changed_summary.json"):
        (main / name).write_text("{}", encoding="utf-8")

    ok, messages = validate_one_candidate_demo(main)
    assert not ok
    assert any("risk_parity" in message for message in messages)
