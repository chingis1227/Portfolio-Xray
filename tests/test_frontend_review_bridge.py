from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest
import yaml


def load_bridge_module() -> ModuleType:
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "run_review_from_payload.py"
    spec = importlib.util.spec_from_file_location("run_review_from_payload", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bridge = load_bridge_module()


def sample_payload() -> dict:
    return {
        "investor_currency": "USD",
        "holdings": [
            {"ticker": "SPY", "weight": 40, "type": "instrument"},
            {"ticker": "QQQ", "weight": 20, "type": "instrument"},
            {"ticker": "TLT", "weight": 20, "type": "instrument"},
            {"ticker": "GLD", "weight": 10, "type": "instrument"},
            {"type": "cash", "currency": "USD", "weight": 10},
        ],
    }


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _method(method_id: str, *, role: str = "targeted_hypothesis") -> dict:
    return {"candidate_method_id": method_id, "method_role": role}


def _launchpad_card(card_id: str, *, methods: list[dict] | None = None) -> dict:
    methods = methods or [_method("minimum_variance")]
    return {
        "card_id": card_id,
        "source_diagnosis_id": "weak_crisis_resilience",
        "source_problem_id": "weak_crisis_resilience",
        "goal": "Reduce volatility",
        "hypothesis_to_test": "Test whether volatility can be reduced without hiding trade-offs.",
        "suggested_methods": methods,
        "default_method": methods[0]["candidate_method_id"] if methods else None,
        "success_criteria": ["Lower volatility while preserving diagnostic transparency."],
        "tradeoff_to_watch": "Return drag and concentration.",
        "when_to_skip": "Skip if the diagnosis no longer applies.",
        "card_type": "targeted_hypothesis_test",
        "launch_status": "hypothesis_test",
        "is_rebalance_recommendation": False,
        "decision_boundary": "This is not a rebalance recommendation; Decision Verdict decides.",
    }


def _review_dir_with_launchpad(tmp_path: Path, launchpad: dict) -> tuple[str, Path]:
    review_id = "frontend_review_unit"
    run_dir = tmp_path / review_id
    subject = run_dir / "analysis_subject"
    _write_json(subject / "candidate_launchpad.json", launchpad)
    _write_json(subject / "problem_classification.json", {"next_diagnostic_step": {}})
    return review_id, run_dir


def test_normalize_payload_maps_frontend_percent_and_preserves_real_cash() -> None:
    normalized = bridge.normalize_payload(sample_payload())

    assert normalized["investor_currency"] == "USD"
    assert normalized["tickers"] == ["SPY", "QQQ", "TLT", "GLD", "Cash USD"]
    assert normalized["current_weights"] == {
        "SPY": 0.40,
        "QQQ": 0.20,
        "TLT": 0.20,
        "GLD": 0.10,
        "Cash USD": 0.10,
    }
    assert normalized["holdings"][-1]["type"] == "cash"
    assert normalized["holdings"][-1]["ticker"] == "Cash USD"
    assert normalized["client_fit"] is None


def test_client_fit_payload_is_preserved_and_mapped_to_input_config(tmp_path: Path) -> None:
    payload = sample_payload()
    payload["client_fit"] = {
        "preset_id": "growth",
        "source": "manual_override",
        "source_quality": "high",
        "source_quality_reason": "User supplied complete manual targets.",
        "horizon_years": 8,
        "target_return_range": {"min": 0.07, "max": 0.10},
        "target_vol_range": {"min": 0.10, "max": 0.14},
        "target_max_drawdown_pct": -0.275,
    }

    normalized = bridge.normalize_payload(payload)
    config = bridge.build_input_config(normalized, bridge.PROJECT_ROOT / "runs" / "frontend_review_client_fit")

    assert normalized["client_fit"] == payload["client_fit"]
    assert config["client_fit"] == payload["client_fit"]
    assert config["client_profile"] == "growth"
    assert config["horizon_years"] == 8.0
    assert config["target_nominal_return_annual"] == pytest.approx(0.085)
    assert config["target_vol_annual"] == pytest.approx(0.12)
    assert config["target_max_drawdown_pct"] == -0.275


def test_client_fit_payload_rejects_invalid_range() -> None:
    payload = sample_payload()
    payload["client_fit"] = {
        "preset_id": "balanced",
        "source": "questionnaire",
        "source_quality": "medium",
        "target_return_range": {"min": 0.08, "max": 0.05},
    }

    with pytest.raises(bridge.PayloadValidationError, match="target_return_range"):
        bridge.normalize_payload(payload)


def test_create_run_dir_creates_unique_frontend_review_dirs_for_100_users(tmp_path: Path) -> None:
    created = [bridge.create_run_dir(base_dir=tmp_path) for _ in range(100)]

    review_ids = [review_id for review_id, _run_dir in created]
    run_dirs = [run_dir for _review_id, run_dir in created]

    assert len(set(review_ids)) == 100
    assert len(set(run_dirs)) == 100
    assert all(review_id.startswith("frontend_review_") for review_id in review_ids)
    assert all(run_dir.parent == tmp_path for run_dir in run_dirs)
    assert all(run_dir.is_dir() for run_dir in run_dirs)


def test_normalize_payload_rejects_duplicate_tickers() -> None:
    payload = sample_payload()
    payload["holdings"] = [
        {"ticker": "SPY", "weight": 50, "type": "instrument"},
        {"ticker": "spy", "weight": 50, "type": "instrument"},
    ]

    with pytest.raises(bridge.PayloadValidationError, match="Duplicate holding label 'SPY'"):
        bridge.normalize_payload(payload)


@pytest.mark.parametrize(
    ("payload_update", "message"),
    [
        ({"investor_currency": ""}, "investor_currency is required"),
        ({"holdings": [{"ticker": "SPY", "weight": 100, "type": "instrument"}]}, "at least 2"),
        (
            {
                "holdings": [
                    {"ticker": "SPY", "weight": 60, "type": "instrument"},
                    {"ticker": "QQQ", "weight": 30, "type": "instrument"},
                ]
            },
            "Total weights must equal 100",
        ),
        (
            {
                "holdings": [
                    {"ticker": "SPY", "weight": 50, "type": "instrument"},
                    {"weight": 50, "type": "instrument"},
                ]
            },
            "requires ticker",
        ),
        (
            {
                "holdings": [
                    {"ticker": "SPY", "weight": 50, "type": "instrument"},
                    {"weight": 50, "type": "cash"},
                ]
            },
            "requires currency",
        ),
        (
            {
                "holdings": [
                    {"ticker": "SPY", "weight": 50, "type": "instrument"},
                    {"ticker": "QQQ", "weight": 50, "type": "crypto"},
                ]
            },
            "Unsupported holding type",
        ),
        (
            {
                "holdings": [
                    {"ticker": "SPY", "weight": 0, "type": "instrument"},
                    {"ticker": "QQQ", "weight": 100, "type": "instrument"},
                ]
            },
            "greater than 0",
        ),
    ],
)
def test_normalize_payload_validation_errors(payload_update: dict, message: str) -> None:
    payload = sample_payload()
    payload.update(payload_update)

    with pytest.raises(bridge.PayloadValidationError, match=message):
        bridge.normalize_payload(payload)


def test_build_input_config_contains_bridge_only_review_settings(tmp_path: Path) -> None:
    normalized = bridge.normalize_payload(sample_payload())
    run_dir = bridge.PROJECT_ROOT / "runs" / "frontend_review_test"

    config = bridge.build_input_config(normalized, run_dir)

    assert config == {
        "investor_currency": "USD",
        "tickers": ["SPY", "QQQ", "TLT", "GLD", "Cash USD"],
        "current_weights": {
            "SPY": 0.40,
            "QQQ": 0.20,
            "TLT": 0.20,
            "GLD": 0.10,
            "Cash USD": 0.10,
        },
        "output_dir": "runs/frontend_review_test/csv",
        "output_dir_final": "runs/frontend_review_test",
        "returns_frequency": "monthly",
        "market_data_provider": "ibkr_yfinance_fallback",
    }

    dumped = yaml.safe_dump(config, sort_keys=False, allow_unicode=True)
    assert "Cash USD: 0.1" in dumped


def test_core_only_backend_command_is_core_diagnostics_only(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, "kwargs": kwargs})

        class Completed:
            returncode = 0
            stdout = ""
            stderr = ""

        return Completed()

    monkeypatch.setattr(bridge.subprocess, "run", fake_run)

    bridge.run_backend(
        Path("runs/frontend_review_test/input.yml"),
        mode=bridge.MODE_CORE_ONLY,
        timeout_seconds=123,
    )

    assert calls
    cmd = calls[0]["cmd"]
    assert cmd[0] == bridge.sys.executable
    assert cmd[1:] == [
        "run_report.py",
        "--materialize-analysis-subject",
        "--core-diagnostics-only",
        "--output-profile",
        "site_api",
        "--review-mode",
        "core",
        "--config",
        "runs/frontend_review_test/input.yml",
        "--no-review-run-context",
    ]
    assert calls[0]["kwargs"]["cwd"] == bridge.PROJECT_ROOT
    assert calls[0]["kwargs"]["capture_output"] is True
    assert calls[0]["kwargs"]["timeout"] == 123


def test_diagnosis_plus_problem_backend_command_skips_candidates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict] = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, "kwargs": kwargs})

        class Completed:
            returncode = 0
            stdout = ""
            stderr = ""

        return Completed()

    monkeypatch.setattr(bridge.subprocess, "run", fake_run)

    bridge.run_backend(
        Path("runs/frontend_review_test/input.yml"),
        mode=bridge.MODE_DIAGNOSIS_PLUS_PROBLEM,
        timeout_seconds=123,
    )

    assert calls
    cmd = calls[0]["cmd"]
    assert cmd[0] == bridge.sys.executable
    assert cmd[1:] == [
        "run_portfolio_review.py",
        "--config",
        "runs/frontend_review_test/input.yml",
        "--skip-candidates",
        "--output-profile",
        "site_api",
    ]
    assert "--skip-candidates" in cmd
    assert "--candidates" not in cmd
    assert "--with-candidates" not in cmd
    assert "--then-compare" not in cmd


def test_diagnosis_plus_problem_expected_outputs_extend_problem_bundle() -> None:
    paths = bridge.expected_output_paths(
        bridge.PROJECT_ROOT / "runs" / "frontend_review_test",
        mode=bridge.MODE_DIAGNOSIS_PLUS_PROBLEM,
    )

    assert paths["problem_classification"].as_posix().endswith(
        "analysis_subject/problem_classification.json"
    )
    assert paths["candidate_launchpad"].as_posix().endswith(
        "analysis_subject/candidate_launchpad.json"
    )
    assert paths["portfolio_alternatives_builder"].as_posix().endswith(
        "analysis_subject/portfolio_alternatives_builder.json"
    )
    assert "candidate_comparison" not in paths
    assert "current_vs_candidate" not in paths
    assert "decision_verdict" not in paths


def test_run_from_payload_writes_failed_result_for_validation_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload_path = tmp_path / "payload.json"
    payload_path.write_text(json.dumps({"investor_currency": "USD", "holdings": []}), encoding="utf-8")
    run_dir = tmp_path / "runs" / "frontend_review_validation"
    run_dir.mkdir(parents=True)

    monkeypatch.setattr(bridge, "create_run_dir", lambda: ("frontend_review_validation", run_dir))

    code, result_path = bridge.run_from_payload(payload_path, timeout_seconds=1)

    assert code == 1
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert result["status"] == "failed"
    assert "at least 2" in result["error"]
    assert result["details"] == "input_validation_error"


def test_scrub_failure_text_hides_tracebacks_and_absolute_paths() -> None:
    raw = (
        'Traceback (most recent call last):\n'
        '  File "D:\\Рабочий стол\\КУРСОР ТУЛА ДИАГНОСТИКА\\src\\internal.py", line 12, in run\n'
        "ValueError: failed while reading D:\\secret\\portfolio\\config.yml"
    )

    safe = bridge.scrub_failure_text(raw)

    assert "Traceback" not in safe
    assert "D:\\" not in safe
    assert "config.yml" not in safe
    assert safe == "Backend failure details were captured safely."


def test_build_failure_result_sanitizes_backend_log_tails() -> None:
    result = bridge.build_failure_result(
        review_id="frontend_review_unit",
        error="Expected output file was not created: D:\\private\\run\\analysis_subject\\portfolio_xray.json",
        details="FileNotFoundError",
        stdout="ok\nD:\\private\\run\\review_result.json",
        stderr='Traceback (most recent call last):\n  File "C:\\tmp\\bridge.py", line 1, in <module>\nRuntimeError',
    )

    rendered = json.dumps(result, ensure_ascii=False)
    assert "D:\\" not in rendered
    assert "C:\\" not in rendered
    assert "Traceback" not in rendered
    assert result["status"] == "failed"
    assert result["error"].startswith("Expected output file was not created:")
    assert result["stderr_tail"] == "Backend failure details were captured safely."


def test_run_from_payload_missing_outputs_writes_safe_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload_path = tmp_path / "payload.json"
    payload_path.write_text(json.dumps(sample_payload()), encoding="utf-8")
    run_dir = tmp_path / "runs" / "frontend_review_missing_outputs"
    run_dir.mkdir(parents=True)

    class Completed:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr(bridge, "create_run_dir", lambda: ("frontend_review_missing_outputs", run_dir))
    monkeypatch.setattr(bridge, "run_backend", lambda *args, **kwargs: Completed())

    code, result_path = bridge.run_from_payload(
        payload_path,
        mode=bridge.MODE_DIAGNOSIS_PLUS_PROBLEM,
        timeout_seconds=1,
    )

    assert code == 1
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert result["status"] == "failed"
    assert result["details"] == "missing_backend_output"
    assert "Expected output file was not created:" in result["error"]
    assert str(run_dir) not in result["error"]


def test_prepare_selected_builder_setup_rebuilds_matching_builder_for_selected_card(
    tmp_path: Path,
) -> None:
    review_id, run_dir = _review_dir_with_launchpad(
        tmp_path,
        {
            "schema_version": "candidate_launchpad_v3",
            "cards": [
                _launchpad_card("card_a", methods=[_method("minimum_variance")]),
                _launchpad_card("card_b", methods=[_method("risk_parity")]),
            ],
        },
    )
    stale_builder_path = run_dir / "analysis_subject" / "portfolio_alternatives_builder.json"
    _write_json(
        stale_builder_path,
        {
            "selected_card_id": "card_a",
            "builder_prefill": {"source_card_id": "card_a"},
            "candidate_setup": {"source_card_id": "card_a"},
        },
    )

    result = bridge.prepare_selected_builder_setup(
        review_id=review_id,
        selected_card_id="card_b",
        base_dir=tmp_path,
    )

    assert result["status"] == "completed"
    assert result["stage"] == "builder_setup"
    assert result["selected_card_id"] == "card_b"
    builder = json.loads(stale_builder_path.read_text(encoding="utf-8"))
    assert builder["selected_card_id"] == "card_b"
    assert builder["builder_prefill"]["source_card_id"] == "card_b"
    assert builder["candidate_setup"]["source_card_id"] == "card_b"
    assert builder["candidate_setup"]["selected_method"] == "risk_parity"
    assert builder["guardrails"]["does_not_generate_candidate"] is True
    assert not (run_dir / "candidate_generation.json").exists()


def test_prepare_selected_builder_setup_rejects_missing_selected_card(tmp_path: Path) -> None:
    review_id, _run_dir = _review_dir_with_launchpad(
        tmp_path,
        {"schema_version": "candidate_launchpad_v3", "cards": [_launchpad_card("card_a")]},
    )

    with pytest.raises(bridge.BuilderSelectionError, match="Selected Launchpad card was not found"):
        bridge.prepare_selected_builder_setup(
            review_id=review_id,
            selected_card_id="card_b",
            base_dir=tmp_path,
        )


def test_selected_builder_lineage_guard_rejects_mismatched_candidate_setup() -> None:
    with pytest.raises(bridge.BuilderSelectionError, match="does not match"):
        bridge._assert_selected_builder_lineage(
            {
                "selected_card_id": "card_b",
                "can_generate_candidate": True,
                "builder_prefill": {"source_card_id": "card_b"},
                "candidate_setup": {"source_card_id": "card_a"},
            },
            "card_b",
        )


def test_prepare_selected_builder_setup_rejects_path_traversal_review_id(tmp_path: Path) -> None:
    with pytest.raises(bridge.BuilderSelectionError, match="path separators"):
        bridge.prepare_selected_builder_setup(
            review_id="frontend_review_../escape",
            selected_card_id="card_a",
            base_dir=tmp_path,
        )


def _candidate_generation_document(
    *,
    card_id: str = "card_a",
    candidate_id: str = "minimum_variance",
    status: str = "generated",
) -> dict:
    return {
        "schema_version": "candidate_generation_v1",
        "diagnostic_only": True,
        "candidate": {
            "candidate_id": candidate_id,
            "source_card_id": card_id,
            "is_rebalance_recommendation": False,
            "status": status,
            "weights": {"SPY": 0.5, "TLT": 0.5} if status == "generated" else None,
        },
        "generation_status": status,
        "source_builder_setup": {"source_card_id": card_id},
        "method_availability": {"backend_candidate_id": candidate_id},
        "warnings": [],
        "handoff_to_comparison": {
            "can_compare": status == "generated",
            "candidate_id": candidate_id,
            "does_not_create_verdict": True,
        },
        "guardrails": {
            "creates_exactly_one_candidate_attempt": True,
            "is_rebalance_recommendation": False,
            "does_not_compare_candidates": True,
            "does_not_create_decision_verdict": True,
        },
    }


def _review_dir_with_selected_builder(tmp_path: Path) -> tuple[str, Path]:
    review_id, run_dir = _review_dir_with_launchpad(
        tmp_path,
        {"schema_version": "candidate_launchpad_v3", "cards": [_launchpad_card("card_a")]},
    )
    (run_dir / "input.yml").write_text("output_dir_final: ignored\n", encoding="utf-8")
    bridge.prepare_selected_builder_setup(
        review_id=review_id,
        selected_card_id="card_a",
        base_dir=tmp_path,
    )
    return review_id, run_dir


def test_generate_selected_candidate_uses_run_local_paths_and_one_candidate(
    tmp_path: Path,
) -> None:
    review_id, run_dir = _review_dir_with_selected_builder(tmp_path)
    calls: list[dict] = []

    def fake_generator(**kwargs):
        calls.append(kwargs)
        document = _candidate_generation_document()
        kwargs["output_path"].write_text(json.dumps(document), encoding="utf-8")
        _write_json(
            run_dir / "candidate_factory_run.json",
            {"steps": [{"candidate_id": "minimum_variance", "status": "succeeded"}]},
        )
        return document

    result = bridge.generate_selected_candidate(
        review_id=review_id,
        selected_card_id="card_a",
        base_dir=tmp_path,
        generator=fake_generator,
    )

    assert result["status"] == "completed"
    assert result["stage"] == "candidate_generation"
    assert result["candidate_id"] == "minimum_variance"
    assert result["can_compare"] is True
    assert (run_dir / "candidate_generation.json").is_file()
    assert calls
    call = calls[0]
    assert call["builder_input"] == run_dir / "analysis_subject" / "portfolio_alternatives_builder.json"
    assert call["output_path"] == run_dir / "candidate_generation.json"
    assert call["factory_run_json"] == run_dir / "candidate_factory_run.json"
    assert call["config_path"] == run_dir / "input.yml"
    assert call["run_factory"] is True
    assert call["factory_execution_mode"] == "fast"
    assert not (run_dir / "current_vs_candidate.json").exists()
    assert not (run_dir / "decision_verdict.json").exists()


def test_generate_selected_candidate_rejects_mismatched_builder_lineage(tmp_path: Path) -> None:
    review_id, run_dir = _review_dir_with_selected_builder(tmp_path)
    builder_path = run_dir / "analysis_subject" / "portfolio_alternatives_builder.json"
    builder = json.loads(builder_path.read_text(encoding="utf-8"))
    builder["candidate_setup"]["source_card_id"] = "other_card"
    _write_json(builder_path, builder)

    with pytest.raises(bridge.BuilderSelectionError, match="does not match"):
        bridge.generate_selected_candidate(
            review_id=review_id,
            selected_card_id="card_a",
            base_dir=tmp_path,
            generator=lambda **kwargs: _candidate_generation_document(),
        )


def test_mismatched_builder_blocks_generation_until_prepare_rebuilds_selected_card(
    tmp_path: Path,
) -> None:
    review_id, run_dir = _review_dir_with_launchpad(
        tmp_path,
        {
            "schema_version": "candidate_launchpad_v3",
            "cards": [
                _launchpad_card("card_a", methods=[_method("minimum_variance")]),
                _launchpad_card("card_b", methods=[_method("risk_parity")]),
            ],
        },
    )
    (run_dir / "input.yml").write_text("output_dir_final: ignored\n", encoding="utf-8")
    bridge.prepare_selected_builder_setup(
        review_id=review_id,
        selected_card_id="card_a",
        base_dir=tmp_path,
    )

    with pytest.raises(bridge.BuilderSelectionError, match="does not match"):
        bridge.generate_selected_candidate(
            review_id=review_id,
            selected_card_id="card_b",
            base_dir=tmp_path,
            generator=lambda **kwargs: _candidate_generation_document(card_id="card_b", candidate_id="risk_parity"),
        )

    prepare_result = bridge.prepare_selected_builder_setup(
        review_id=review_id,
        selected_card_id="card_b",
        base_dir=tmp_path,
    )
    assert prepare_result["status"] == "completed"
    assert prepare_result["selected_card_id"] == "card_b"

    def fake_generator(**kwargs):
        document = _candidate_generation_document(card_id="card_b", candidate_id="risk_parity")
        kwargs["output_path"].write_text(json.dumps(document), encoding="utf-8")
        _write_json(
            run_dir / "candidate_factory_run.json",
            {"steps": [{"candidate_id": "risk_parity", "status": "succeeded"}]},
        )
        return document

    generation_result = bridge.generate_selected_candidate(
        review_id=review_id,
        selected_card_id="card_b",
        base_dir=tmp_path,
        generator=fake_generator,
    )

    assert generation_result["status"] == "completed"
    assert generation_result["candidate_id"] == "risk_parity"
    assert generation_result["can_compare"] is True


def test_generate_selected_candidate_rejects_mismatched_candidate_generation_lineage(
    tmp_path: Path,
) -> None:
    review_id, _run_dir = _review_dir_with_selected_builder(tmp_path)

    with pytest.raises(bridge.CandidateBridgeError, match="does not match"):
        bridge.generate_selected_candidate(
            review_id=review_id,
            selected_card_id="card_a",
            base_dir=tmp_path,
            generator=lambda **kwargs: _candidate_generation_document(card_id="other_card"),
        )


def test_generate_selected_candidate_rejects_factory_summary_with_multiple_candidates(
    tmp_path: Path,
) -> None:
    review_id, run_dir = _review_dir_with_selected_builder(tmp_path)

    def fake_generator(**kwargs):
        document = _candidate_generation_document(candidate_id="minimum_variance")
        _write_json(
            run_dir / "candidate_factory_run.json",
            {
                "steps": [
                    {"candidate_id": "minimum_variance", "status": "succeeded"},
                    {"candidate_id": "risk_parity", "status": "succeeded"},
                ]
            },
        )
        return document

    with pytest.raises(bridge.CandidateBridgeError, match="exactly one selected candidate"):
        bridge.generate_selected_candidate(
            review_id=review_id,
            selected_card_id="card_a",
            base_dir=tmp_path,
            generator=fake_generator,
        )


def test_compare_selected_candidate_writes_run_local_block8_outputs(
    tmp_path: Path,
) -> None:
    review_id, run_dir = _review_dir_with_selected_builder(tmp_path)
    _write_json(run_dir / "candidate_generation.json", _candidate_generation_document())
    _write_json(
        run_dir / "candidate_factory_run.json",
        {"steps": [{"candidate_id": "minimum_variance", "status": "succeeded"}]},
    )
    calls: list[dict] = []

    def fake_config_loader(path: Path):
        assert path == run_dir / "input.yml"
        return SimpleNamespace(output_dir_final=run_dir.as_posix())

    def fake_comparison_writer(cfg, *, project_root, candidate_ids, candidate_generation, factory_run, **kwargs):
        calls.append(
            {
                "cfg": cfg,
                "project_root": project_root,
                "candidate_ids": candidate_ids,
                "candidate_generation": candidate_generation,
                "factory_run": factory_run,
            }
        )
        _write_json(
            run_dir / "candidate_comparison.json",
            {
                "schema_version": "candidate_comparison_v1",
                "product_candidate_scope": {"candidate_ids": ["minimum_variance"]},
                "candidates": [
                    {"candidate_id": "analysis_subject"},
                    {"candidate_id": "minimum_variance"},
                ],
            },
        )
        _write_json(
            run_dir / "current_vs_candidate.json",
            {
                "schema_version": "current_vs_candidate_v1",
                "comparison_status": "available",
                "view_mode": "one_candidate",
                "selected_candidate_ids": ["minimum_variance"],
                "requested_candidate_ids": ["minimum_variance"],
                "comparisons": [{"candidate_id": "minimum_variance"}],
                "warnings": [],
            },
        )
        return {
            "candidate_comparison_json": run_dir / "candidate_comparison.json",
            "current_vs_candidate_json": run_dir / "current_vs_candidate.json",
        }

    result = bridge.compare_selected_candidate(
        review_id=review_id,
        selected_card_id="card_a",
        base_dir=tmp_path,
        config_loader=fake_config_loader,
        comparison_writer=fake_comparison_writer,
    )

    assert result["status"] == "completed"
    assert result["stage"] == "current_vs_candidate"
    assert result["candidate_id"] == "minimum_variance"
    assert result["comparison_status"] == "available"
    assert result["view_mode"] == "one_candidate"
    assert result["paths"]["candidate_comparison"].endswith("candidate_comparison.json")
    assert result["paths"]["current_vs_candidate"].endswith("current_vs_candidate.json")
    assert calls
    call = calls[0]
    assert call["project_root"] == bridge.PROJECT_ROOT
    assert call["candidate_ids"] == ["minimum_variance"]
    assert call["candidate_generation"]["candidate"]["candidate_id"] == "minimum_variance"
    assert call["factory_run"]["steps"][0]["candidate_id"] == "minimum_variance"
    assert not (run_dir / "decision_verdict.json").exists()


def test_compare_selected_candidate_rejects_mismatched_candidate_generation_lineage(
    tmp_path: Path,
) -> None:
    review_id, run_dir = _review_dir_with_selected_builder(tmp_path)
    _write_json(
        run_dir / "candidate_generation.json",
        _candidate_generation_document(card_id="other_card"),
    )

    with pytest.raises(bridge.CandidateBridgeError, match="does not match"):
        bridge.compare_selected_candidate(
            review_id=review_id,
            selected_card_id="card_a",
            base_dir=tmp_path,
            config_loader=lambda path: SimpleNamespace(output_dir_final="ignored"),
            comparison_writer=lambda *args, **kwargs: {},
        )


def test_compare_selected_candidate_rejects_factory_summary_with_multiple_candidates(
    tmp_path: Path,
) -> None:
    review_id, run_dir = _review_dir_with_selected_builder(tmp_path)
    _write_json(run_dir / "candidate_generation.json", _candidate_generation_document())
    _write_json(
        run_dir / "candidate_factory_run.json",
        {
            "steps": [
                {"candidate_id": "minimum_variance", "status": "succeeded"},
                {"candidate_id": "risk_parity", "status": "succeeded"},
            ]
        },
    )

    with pytest.raises(bridge.CandidateBridgeError, match="exactly one selected candidate"):
        bridge.compare_selected_candidate(
            review_id=review_id,
            selected_card_id="card_a",
            base_dir=tmp_path,
            config_loader=lambda path: SimpleNamespace(output_dir_final="ignored"),
            comparison_writer=lambda *args, **kwargs: {},
        )


def _current_vs_candidate_document(*, candidate_id: str = "minimum_variance") -> dict:
    return {
        "schema_version": "current_vs_candidate_v1",
        "diagnostic_only": True,
        "comparison_status": "available",
        "view_mode": "one_candidate",
        "baseline": {"candidate_id": "analysis_subject", "status": "available"},
        "selected_candidate_ids": [candidate_id],
        "requested_candidate_ids": [candidate_id],
        "comparisons": [
            {
                "candidate_id": candidate_id,
                "status": "available",
                "dimensions": [{"field": "vol_annual", "status": "available"}],
                "risk_reduced": [{"field": "vol_annual", "is_material": True}],
                "risk_added": [],
                "what_improved": [{"field": "vol_annual", "is_material": True}],
                "what_worsened": [],
                "practicality": {
                    "turnover_required": {
                        "status": "available",
                        "turnover_half_sum_pct": 0.10,
                    },
                    "estimated_transaction_cost_pct": 0.0001,
                },
                "success_criteria_result": {"overall_status": "met", "criteria": []},
                "materiality_for_decision_review": {
                    "status": "review_candidate",
                    "is_material_enough": True,
                    "reason": "at_least_one_material_improvement_available",
                },
                "data_quality": {
                    "missing_fields": [],
                    "warnings": [],
                    "construction_disclosure_status": "available",
                },
            }
        ],
        "warnings": [],
    }


def test_write_selected_candidate_verdict_writes_run_local_block9_output(
    tmp_path: Path,
) -> None:
    review_id, run_dir = _review_dir_with_selected_builder(tmp_path)
    _write_json(run_dir / "candidate_generation.json", _candidate_generation_document())
    _write_json(
        run_dir / "candidate_factory_run.json",
        {"steps": [{"candidate_id": "minimum_variance", "status": "succeeded"}]},
    )
    _write_json(run_dir / "current_vs_candidate.json", _current_vs_candidate_document())

    result = bridge.write_selected_candidate_verdict(
        review_id=review_id,
        selected_card_id="card_a",
        base_dir=tmp_path,
    )

    assert result["status"] == "completed"
    assert result["stage"] == "decision_verdict"
    assert result["candidate_id"] == "minimum_variance"
    assert result["verdict_id"] == "rebalance_to_selected_candidate"
    assert result["selection_decision_status"] == "selected_candidate"
    assert result["path"].endswith("decision_verdict.json")
    verdict = json.loads((run_dir / "decision_verdict.json").read_text(encoding="utf-8"))
    assert verdict["reviewed_candidate_id"] == "minimum_variance"
    assert verdict["source_artifacts"]["candidate_generation"] == "candidate_generation.json"
    assert verdict["source_artifacts"]["current_vs_candidate"] == "current_vs_candidate.json"
    assert verdict["guardrails"]["does_not_execute_trades"] is True


def test_write_selected_candidate_verdict_rejects_stale_comparison_candidate(
    tmp_path: Path,
) -> None:
    review_id, run_dir = _review_dir_with_selected_builder(tmp_path)
    _write_json(run_dir / "candidate_generation.json", _candidate_generation_document())
    _write_json(
        run_dir / "candidate_factory_run.json",
        {"steps": [{"candidate_id": "minimum_variance", "status": "succeeded"}]},
    )
    _write_json(
        run_dir / "current_vs_candidate.json",
        _current_vs_candidate_document(candidate_id="risk_parity"),
    )

    with pytest.raises(bridge.VerdictBridgeError, match="does not match"):
        bridge.write_selected_candidate_verdict(
            review_id=review_id,
            selected_card_id="card_a",
            base_dir=tmp_path,
        )


def test_write_selected_candidate_verdict_allows_failed_candidate_without_rebalance(
    tmp_path: Path,
) -> None:
    review_id, run_dir = _review_dir_with_selected_builder(tmp_path)
    failed = _candidate_generation_document(status="failed")
    failed["candidate"]["failure_reason"] = "optimizer_solver_failed"
    failed["candidate"]["weights"] = None
    failed["handoff_to_comparison"]["can_compare"] = False
    failed["handoff_to_comparison"]["blocked_reason"] = "candidate_generation_failed"
    _write_json(run_dir / "candidate_generation.json", failed)
    _write_json(
        run_dir / "candidate_factory_run.json",
        {"steps": [{"candidate_id": "minimum_variance", "status": "failed"}]},
    )

    result = bridge.write_selected_candidate_verdict(
        review_id=review_id,
        selected_card_id="card_a",
        base_dir=tmp_path,
    )

    assert result["status"] == "completed"
    assert result["verdict_id"] == "candidate_failed_or_infeasible"
    verdict = result["decision_verdict"]
    assert verdict["selected_candidate_id"] is None
    assert verdict["reviewed_candidate_id"] == "minimum_variance"
    assert verdict["no_trade"]["evaluated"] is False


def test_write_selected_report_context_writes_grounded_post_compare_context(
    tmp_path: Path,
) -> None:
    review_id, run_dir = _review_dir_with_selected_builder(tmp_path)
    subject = run_dir / "analysis_subject"
    _write_json(
        subject / "problem_classification.json",
        {
            "primary_diagnosis": {
                "thesis_en": "The current portfolio has a volatility problem worth testing."
            }
        },
    )
    _write_json(subject / "portfolio_xray.json", {"status": "ok"})
    _write_json(subject / "stress_report.json", {"status": "ok", "worst_scenario_loss_pct": -0.25})
    _write_json(run_dir / "candidate_generation.json", _candidate_generation_document())
    _write_json(
        run_dir / "candidate_factory_run.json",
        {"steps": [{"candidate_id": "minimum_variance", "status": "succeeded"}]},
    )
    _write_json(run_dir / "current_vs_candidate.json", _current_vs_candidate_document())
    bridge.write_selected_candidate_verdict(
        review_id=review_id,
        selected_card_id="card_a",
        base_dir=tmp_path,
    )

    result = bridge.write_selected_report_context(
        review_id=review_id,
        selected_card_id="card_a",
        base_dir=tmp_path,
    )

    assert result["status"] == "completed"
    assert result["stage"] == "report_commentary"
    assert result["candidate_id"] == "minimum_variance"
    assert result["path"].endswith("ai_commentary_context.json")
    context = result["ai_commentary_context"]
    assert context["grounding_phase"] == "post_compare"
    assert context["guardrails"]["does_not_execute_trades"] is True
    assert context["source_artifacts"]["decision_verdict"] == "decision_verdict.json"
    assert context["source_artifacts"]["current_vs_candidate"] == "current_vs_candidate.json"
    assert context["client_explanation_draft"]["sentences"]


def test_write_selected_report_context_rejects_stale_verdict_candidate(
    tmp_path: Path,
) -> None:
    review_id, run_dir = _review_dir_with_selected_builder(tmp_path)
    _write_json(run_dir / "candidate_generation.json", _candidate_generation_document())
    _write_json(
        run_dir / "candidate_factory_run.json",
        {"steps": [{"candidate_id": "minimum_variance", "status": "succeeded"}]},
    )
    _write_json(run_dir / "current_vs_candidate.json", _current_vs_candidate_document())
    _write_json(
        run_dir / "decision_verdict.json",
        {
            "reviewed_candidate_id": "risk_parity",
            "selected_candidate_id": "risk_parity",
            "guardrails": {"does_not_execute_trades": True},
        },
    )

    with pytest.raises(bridge.ReportBridgeError, match="does not match"):
        bridge.write_selected_report_context(
            review_id=review_id,
            selected_card_id="card_a",
            base_dir=tmp_path,
        )
