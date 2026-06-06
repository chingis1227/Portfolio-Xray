from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from scripts.generate_candidate_from_builder_setup import (
    generate_candidate_from_builder_setup,
    generation_kwargs_from_factory_result,
)
from src.candidate_generation import build_candidate_generation_document
from src.portfolio_alternatives_builder import (
    builder_prefill_to_candidate_setup,
    launchpad_card_to_builder_prefill,
)


def _candidate_setup(method: str = "minimum_cvar") -> dict[str, object]:
    prefill = launchpad_card_to_builder_prefill(
        {
            "card_id": f"launchpad_01_{method}",
            "goal": "Improve crisis resilience",
            "source_problem_id": "weak_crisis_resilience",
            "source_diagnosis_id": "weak_crisis_resilience",
            "hypothesis_to_test": "Test whether the selected method improves the diagnosis.",
            "default_method": method,
            "suggested_methods": [
                {"candidate_method_id": method, "method_role": "targeted_hypothesis"}
            ],
            "success_criteria": ["Improve the diagnosed weakness."],
            "tradeoff_to_watch": "Risk improvement versus concentration and turnover.",
            "when_to_skip": "Skip if diagnosis no longer applies.",
            "card_type": "targeted_hypothesis_test",
            "launch_status": "hypothesis_test",
            "is_rebalance_recommendation": False,
            "decision_boundary": "This is not a rebalance recommendation.",
        }
    )
    setup = builder_prefill_to_candidate_setup(prefill)
    assert setup is not None
    return setup


def _factory_doc(candidate_id: str, step: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": "candidate_factory_run_v1",
        "factory_profile_id": "explicit_list",
        "steps": [{"candidate_id": candidate_id, **step}],
        "warnings": [],
    }


def test_failed_factory_attempt_ignores_stale_weights_and_cannot_compare(tmp_path: Path) -> None:
    stale_dir = tmp_path / "minimum cvar constrained portfolio"
    stale_dir.mkdir()
    (stale_dir / "weights.json").write_text(
        json.dumps({"VOO": 1.0}),
        encoding="utf-8",
    )
    setup = _candidate_setup("minimum_cvar")

    kwargs = generation_kwargs_from_factory_result(
        project_root=tmp_path,
        candidate_id="minimum_cvar_constrained",
        factory_doc=_factory_doc(
            "minimum_cvar_constrained",
            {
                "status": "failed",
                "artifact_root": "minimum cvar constrained portfolio",
                "reason_code": "builder_fail_numerical",
                "message": "Builder reported FAIL_NUMERICAL.",
            },
        ),
        returncode=1,
    )
    document = build_candidate_generation_document(setup, **kwargs)

    assert document["generation_status"] == "failed"
    assert document["candidate"]["weights"] is None
    assert document["candidate"]["failure_reason"]
    assert document["candidate"]["is_rebalance_recommendation"] is False
    assert document["handoff_to_comparison"]["can_compare"] is False
    assert document["handoff_to_comparison"]["blocked_reason"] == "candidate_generation_failed"


def test_infeasible_factory_attempt_is_preserved_as_infeasible(tmp_path: Path) -> None:
    setup = _candidate_setup("minimum_variance")

    kwargs = generation_kwargs_from_factory_result(
        project_root=tmp_path,
        candidate_id="minimum_variance",
        factory_doc=_factory_doc(
            "minimum_variance",
            {
                "status": "failed",
                "artifact_root": "minimum variance portfolio",
                "reason_code": "builder_infeasible_bounds",
                "builder_status": "FAIL_INFEASIBLE_BOUNDS",
                "builder_reason": "max weight too low for asset count",
                "message": "Builder reported FAIL_INFEASIBLE_BOUNDS.",
            },
        ),
        returncode=1,
    )
    document = build_candidate_generation_document(setup, **kwargs)

    assert document["generation_status"] == "infeasible"
    assert document["candidate"]["failure_reason"] is None
    assert "builder_infeasible_bounds" in document["candidate"]["infeasibility_reason"]
    assert document["candidate"]["weights"] is None
    assert document["candidate"]["is_rebalance_recommendation"] is False
    assert document["handoff_to_comparison"]["can_compare"] is False
    assert document["handoff_to_comparison"]["blocked_reason"] == "candidate_generation_infeasible"


def test_runtime_script_writes_generated_candidate_from_factory_weights(tmp_path: Path) -> None:
    setup = _candidate_setup("equal_weight")
    builder_doc = {
        "can_generate_candidate": True,
        "candidate_setup": setup,
    }
    builder_path = tmp_path / "Main portfolio" / "analysis_subject" / "portfolio_alternatives_builder.json"
    builder_path.parent.mkdir(parents=True)
    builder_path.write_text(json.dumps(builder_doc), encoding="utf-8")

    artifact_dir = tmp_path / "equal-weight portfolio"
    artifact_dir.mkdir()
    (artifact_dir / "weights.json").write_text(
        json.dumps({"VOO": 0.5, "TLT": 0.5}),
        encoding="utf-8",
    )
    factory_path = tmp_path / "Main portfolio" / "candidate_factory_run.json"
    factory_path.write_text(
        json.dumps(
            _factory_doc(
                "equal_weight",
                {
                    "status": "succeeded",
                    "artifact_root": "equal-weight portfolio",
                    "reason_code": None,
                    "message": None,
                },
            )
        ),
        encoding="utf-8",
    )

    calls: list[list[str]] = []

    def fake_runner(command: list[str], **_: object) -> SimpleNamespace:
        calls.append(command)
        return SimpleNamespace(returncode=0, stderr="")

    output = tmp_path / "Main portfolio" / "candidate_generation.json"
    document = generate_candidate_from_builder_setup(
        builder_input=builder_path,
        output_path=output,
        project_root=tmp_path,
        factory_run_json=factory_path,
        runner=fake_runner,
    )

    assert calls
    assert "--then-compare" not in calls[0]
    assert document["generation_status"] == "generated"
    assert document["candidate"]["weights"] == {"VOO": 0.5, "TLT": 0.5}
    assert document["candidate"]["is_rebalance_recommendation"] is False
    assert document["handoff_to_comparison"]["can_compare"] is True
    assert json.loads(output.read_text(encoding="utf-8"))["candidate"]["candidate_id"] == "equal_weight"
