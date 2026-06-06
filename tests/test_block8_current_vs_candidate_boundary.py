from __future__ import annotations

import json
from pathlib import Path

from src.candidate_comparison import write_block8_current_vs_candidate_only_outputs
from src.config_schema import validate_config
from src.snapshot import compute_candidate_config_fingerprint


def _snapshot(metrics: dict, *, cfg: object, analysis_end: str = "2026-04-30") -> dict:
    return {
        "analysis_end": analysis_end,
        "window_label": "10y",
        "candidate_config_fingerprint": compute_candidate_config_fingerprint(cfg),
        "metrics": metrics,
        "stress_suite_results": {
            "overall": "PASS",
            "scenarios": [{"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.08}],
        },
    }


def _run_metadata() -> dict:
    return {
        "run_info": {"analysis_end_date": "2026-04-30"},
        "analysis_setup": {
            "analysis_subject": {
                "id": "current_portfolio",
                "type": "current_portfolio",
                "display_name": "Current Portfolio",
            },
            "analysis_portfolio": {
                "portfolio_role": "user_current_portfolio",
                "recommendation_status": "diagnostic_current_portfolio_not_recommendation",
            },
        },
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_block8_only_writes_comparison_without_refreshing_stale_verdict(
    tmp_path: Path,
) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    main = tmp_path / "Main portfolio"
    subject = main / "analysis_subject"
    equal_weight = tmp_path / "equal-weight portfolio"

    _write_json(
        subject / "snapshot_10y.json",
        _snapshot(
            {"cagr": 0.07, "vol_annual": 0.12, "max_drawdown": -0.25, "sharpe": 0.58},
            cfg=cfg,
        ),
    )
    _write_json(subject / "run_metadata.json", _run_metadata())
    _write_json(
        equal_weight / "snapshot_10y.json",
        _snapshot(
            {"cagr": 0.065, "vol_annual": 0.10, "max_drawdown": -0.18, "sharpe": 0.65},
            cfg=cfg,
        ),
    )

    stale_verdict = {
        "schema_version": "decision_verdict_v1",
        "generated_at": "2000-01-01T00:00:00Z",
        "verdict_id": "stale_should_not_be_current",
    }
    _write_json(main / "decision_verdict.json", stale_verdict)

    paths = write_block8_current_vs_candidate_only_outputs(
        cfg,
        project_root=tmp_path,
        candidate_ids=["equal_weight"],
    )

    assert set(paths) == {"candidate_comparison_json", "current_vs_candidate_json"}
    assert (main / "action_plan.json").exists() is False
    assert (main / "decision_journal.json").exists() is False
    assert (main / "ai_commentary_context.json").exists() is False
    assert json.loads((main / "decision_verdict.json").read_text(encoding="utf-8")) == stale_verdict

    comparison = json.loads((main / "candidate_comparison.json").read_text(encoding="utf-8"))
    assert comparison["product_candidate_scope"]["candidate_ids"] == ["equal_weight"]
    emitted_ids = {row["candidate_id"] for row in comparison["candidates"]}
    assert "equal_weight" in emitted_ids
    assert "risk_parity" not in emitted_ids
    assert comparison["block_8_vertical_scope"]["writes_verdict"] is False

    current_vs = json.loads((main / "current_vs_candidate.json").read_text(encoding="utf-8"))
    assert current_vs["view_mode"] == "one_candidate"
    assert current_vs["selected_candidate_ids"] == ["equal_weight"]
    assert current_vs["block_boundary"]["writes_decision_verdict"] is False
    assert current_vs["block_boundary"]["stale_downstream_artifacts_are_not_current"] is True
    assert current_vs["block_boundary"]["ignored_downstream_artifacts"] == [
        "decision_verdict.json"
    ]
    assert (
        "stale_downstream_artifact_ignored:decision_verdict.json"
        in current_vs["warnings"]
    )
    assert current_vs["source_artifacts"]["decision_verdict"] is None
