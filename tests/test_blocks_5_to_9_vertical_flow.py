from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from scripts import run_blocks_5_to_9_vertical_flow as flow


class _Completed:
    returncode = 0
    stdout = ""
    stderr = ""


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _method(method_id: str, *, role: str = "targeted_hypothesis") -> dict:
    return {"candidate_method_id": method_id, "method_role": role}


def _card(
    card_id: str,
    *,
    source_diagnosis_id: str,
    goal: str,
    methods: list[dict],
    card_type: str = "targeted_hypothesis_test",
    launch_status: str = "hypothesis_test",
) -> dict:
    return {
        "card_id": card_id,
        "source_diagnosis_id": source_diagnosis_id,
        "source_problem_id": source_diagnosis_id,
        "goal": goal,
        "hypothesis_to_test": f"Test {source_diagnosis_id}.",
        "suggested_methods": methods,
        "default_method": methods[0]["candidate_method_id"] if methods else None,
        "success_criteria": ["Improve the diagnosed issue without hiding trade-offs."],
        "tradeoff_to_watch": "Turnover and cost.",
        "when_to_skip": "Skip if diagnosis no longer applies.",
        "card_type": card_type,
        "launch_status": launch_status,
        "is_rebalance_recommendation": False,
        "decision_boundary": "This is not a rebalance recommendation; Decision Verdict decides.",
    }


def _diagnosis_runner(output_dir: Path, launchpad: dict, commands: list[list[str]]):
    def runner(command, **kwargs):
        commands.append(list(command))
        assert "--skip-candidates" in command
        assert "--skip-compare" in command
        subject = output_dir / "analysis_subject"
        _write_json(subject / "problem_classification.json", {"next_diagnostic_step": {}})
        _write_json(subject / "candidate_launchpad.json", launchpad)
        _write_json(subject / "portfolio_xray.json", {"schema_version": "portfolio_xray_v1"})
        _write_json(subject / "stress_report.json", {"schema_version": "stress_report_v1"})
        return _Completed()

    return runner


def test_vertical_flow_runs_one_candidate_and_writes_direct_artifacts(
    tmp_path: Path,
    monkeypatch,
) -> None:
    output_dir = tmp_path / "Main portfolio"
    launchpad = {
        "schema_version": "candidate_launchpad_v3",
        "cards": [
            _card(
                "targeted_minvar",
                source_diagnosis_id="weak_crisis_resilience",
                goal="Reduce volatility",
                methods=[_method("minimum_variance"), _method("risk_parity")],
            ),
            _card(
                "reference_equal_weight",
                source_diagnosis_id="mixed_evidence_no_action",
                goal="Compare against simple references",
                methods=[
                    _method("equal_weight", role="reference_benchmark"),
                    _method("risk_parity", role="reference_benchmark"),
                ],
                card_type="reference_benchmark_test",
                launch_status="reference_test",
            ),
        ],
    }
    stale = output_dir / "decision_verdict.json"
    _write_json(stale, {"stale": True})
    _write_json(output_dir / "candidate_factory_run.json", {"factory_profile_id": "default_v1"})

    monkeypatch.setattr(
        flow,
        "load_validated_config",
        lambda: SimpleNamespace(output_dir_final="Main portfolio"),
    )

    def fake_generate(**kwargs):
        assert Path(kwargs["builder_input"]).name == "portfolio_alternatives_builder.json"
        assert kwargs["run_factory"] is True
        builder = json.loads(Path(kwargs["builder_input"]).read_text(encoding="utf-8"))
        setup = builder["candidate_setup"]
        assert setup["source_card_id"] == "reference_equal_weight"
        assert setup["selected_method"] == "equal_weight"
        assert setup["constraints"]["constraint_preset"] == "basic_reference"
        doc = {
            "schema_version": "candidate_generation_v1",
            "generation_status": "generated",
            "candidate": {
                "candidate_id": "equal_weight",
                "method": "equal_weight",
                "weights": {"A": 0.5, "B": 0.5},
                "is_rebalance_recommendation": False,
            },
            "method_availability": {"available": True},
            "handoff_to_comparison": {"can_compare": True, "candidate_id": "equal_weight"},
            "warnings": [],
        }
        _write_json(Path(kwargs["output_path"]), doc)
        return doc

    def fake_block8(cfg, *, project_root, candidate_ids, candidate_generation, **kwargs):
        assert candidate_ids == ["equal_weight"]
        assert candidate_generation["candidate"]["candidate_id"] == "equal_weight"
        comparison = {
            "schema_version": "candidate_comparison_v1",
            "candidates": [{"candidate_id": "analysis_subject"}, {"candidate_id": "equal_weight"}],
            "block_8_vertical_scope": {"candidate_ids": ["equal_weight"]},
        }
        current_vs = {
            "schema_version": "current_vs_candidate_v1",
            "baseline": {"candidate_id": "analysis_subject"},
            "selected_candidate_ids": ["equal_weight"],
            "comparisons": [
                {
                    "candidate_id": "equal_weight",
                    "materiality_for_decision_review": {"is_material_enough": False},
                    "success_criteria_result": {"overall_status": "not_met"},
                    "risk_reduced": [],
                    "what_improved": [],
                    "what_worsened": [],
                    "practicality": {},
                }
            ],
            "warnings": [],
        }
        _write_json(output_dir / "candidate_comparison.json", comparison)
        _write_json(output_dir / "current_vs_candidate.json", current_vs)
        return {
            "candidate_comparison_json": output_dir / "candidate_comparison.json",
            "current_vs_candidate_json": output_dir / "current_vs_candidate.json",
        }

    monkeypatch.setattr(flow, "generate_candidate_from_builder_setup", fake_generate)
    monkeypatch.setattr(flow, "write_block8_current_vs_candidate_only_outputs", fake_block8)
    commands: list[list[str]] = []

    result = flow.run_blocks_5_to_9_vertical_flow(
        project_root=tmp_path,
        runner=_diagnosis_runner(output_dir, launchpad, commands),
        python_executable="python-test",
    )

    assert result["status"] == "completed"
    assert result["candidate_id"] == "equal_weight"
    assert result["selected_card"] == "reference_equal_weight"
    assert "candidate_factory_run.json" in result["removed_stale_artifacts"]
    assert json.loads((output_dir / "decision_verdict.json").read_text(encoding="utf-8"))["schema_version"] == "decision_verdict_v1"
    ai_context = json.loads((output_dir / "ai_commentary_context.json").read_text(encoding="utf-8"))
    assert ai_context["purpose"] == "grounded_ai_commentary_context"
    assert commands[0][1].endswith("run_portfolio_review.py")
