#!/usr/bin/env python3
"""Run the Blocks 5-9 vertical product loop with one selected candidate.

The script is intentionally not a candidate-factory menu.  It runs the
diagnosis-only portfolio review, rebuilds one Block 6 Builder setup for the
selected Launchpad card, generates one Block 7 candidate attempt, writes the
Block 8 current-vs-candidate comparison, builds the direct Block 9 verdict, and
writes deterministic AI Commentary grounding.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.generate_candidate_from_builder_setup import (  # noqa: E402
    generate_candidate_from_builder_setup,
)
from src.ai_commentary_context import write_ai_commentary_context_outputs  # noqa: E402
from src.candidate_comparison import write_block8_current_vs_candidate_only_outputs  # noqa: E402
from src.candidate_generation import CANDIDATE_GENERATION_FILENAME  # noqa: E402
from src.config import load_validated_config  # noqa: E402
from src.current_vs_candidate import CURRENT_VS_CANDIDATE_FILENAME  # noqa: E402
from src.decision_verdict import DECISION_VERDICT_FILENAME, write_decision_verdict_outputs  # noqa: E402
from src.product_bundle_hygiene import attach_product_run_metadata, product_run_id  # noqa: E402
from src.portfolio_alternatives_builder import (  # noqa: E402
    PORTFOLIO_ALTERNATIVES_BUILDER_FILENAME,
    PortfolioAlternativesBuilderError,
    build_portfolio_alternatives_builder_document,
    build_simple_builder_parameters,
    builder_prefill_to_candidate_setup,
    launchpad_card_to_builder_prefill,
    validate_builder_setup,
)
from src.product_bundle_paths import (  # noqa: E402
    load_diagnosis_bundle_docs,
    resolve_portfolio_alternatives_builder_path,
)


DEFAULT_DEMO_METHOD = "equal_weight"
STALE_VERTICAL_FILENAMES: tuple[str, ...] = (
    CANDIDATE_GENERATION_FILENAME,
    "candidate_factory_run.json",
    "candidate_comparison.json",
    CURRENT_VS_CANDIDATE_FILENAME,
    DECISION_VERDICT_FILENAME,
    "ai_commentary_context.json",
)


class VerticalFlowError(RuntimeError):
    """Raised when the vertical demo cannot safely continue."""


def run_blocks_5_to_9_vertical_flow(
    *,
    project_root: str | Path = REPO_ROOT,
    config_path: str | Path | None = None,
    method: str = DEFAULT_DEMO_METHOD,
    constraint_preset: str | None = None,
    mode: str | None = None,
    card_id: str | None = None,
    no_cache: bool = False,
    force_candidate: bool = False,
    run_factory: bool = True,
    factory_execution_mode: str = "fast",
    output_profile: str = "site_api",
    python_executable: str | None = None,
    runner: Any = subprocess.run,
) -> dict[str, Any]:
    """Run diagnosis -> one candidate -> compare -> verdict -> AI grounding.

    ``runner`` is injectable so tests can prove orchestration without running
    the full data pipeline.  In normal CLI use it is ``subprocess.run``.
    """

    root = Path(project_root)
    py = python_executable or sys.executable
    cfg = load_validated_config(config_path) if config_path is not None else load_validated_config()
    output_dir = root / str(getattr(cfg, "output_dir_final", "Main portfolio"))

    product_run = f"blocks_5_9:{uuid.uuid4()}"
    diagnosis = _run_diagnosis_only_review(
        root=root,
        config_path=config_path,
        python_executable=py,
        output_profile=output_profile,
        no_cache=no_cache,
        runner=runner,
    )
    removed_stale = _remove_stale_vertical_artifacts(output_dir)

    diagnosis_docs = load_diagnosis_bundle_docs(output_dir)
    builder_path, builder_doc = build_selected_builder_document(
        output_dir=output_dir,
        diagnosis_docs=diagnosis_docs,
        method=method,
        constraint_preset=constraint_preset,
        mode=mode,
        card_id=card_id,
    )
    builder_doc = attach_product_run_metadata(
        builder_doc,
        run_id=product_run,
        artifact_role=PORTFOLIO_ALTERNATIVES_BUILDER_FILENAME,
        workflow_state="blocks_5_9_vertical",
    )
    _write_json(builder_path, builder_doc)

    candidate_generation = generate_candidate_from_builder_setup(
        builder_input=builder_path,
        output_path=output_dir / CANDIDATE_GENERATION_FILENAME,
        project_root=root,
        run_factory=run_factory,
        force=force_candidate,
        config_path=config_path,
        factory_execution_mode=factory_execution_mode,
        python_executable=py,
    )
    candidate_generation = attach_product_run_metadata(
        candidate_generation,
        run_id=product_run,
        artifact_role=CANDIDATE_GENERATION_FILENAME,
        workflow_state="blocks_5_9_vertical",
        upstream_run_ids={"portfolio_alternatives_builder": product_run},
    )
    _write_json(output_dir / CANDIDATE_GENERATION_FILENAME, candidate_generation)
    candidate = candidate_generation.get("candidate") if isinstance(candidate_generation, dict) else {}
    candidate_id = str((candidate or {}).get("candidate_id") or "")
    if not candidate_id:
        raise VerticalFlowError("candidate_generation_missing_candidate_id")

    block8_paths = write_block8_current_vs_candidate_only_outputs(
        cfg,
        project_root=root,
        candidate_ids=[candidate_id],
        candidate_generation=candidate_generation,
    )
    comparison = _read_json_object(block8_paths["candidate_comparison_json"])
    current_vs_candidate = _read_json_object(block8_paths["current_vs_candidate_json"])
    comparison = attach_product_run_metadata(
        comparison or {},
        run_id=product_run,
        artifact_role="candidate_comparison.json",
        workflow_state="blocks_5_9_vertical",
        upstream_run_ids={"candidate_generation": product_run},
    )
    current_vs_candidate = attach_product_run_metadata(
        current_vs_candidate or {},
        run_id=product_run,
        artifact_role=CURRENT_VS_CANDIDATE_FILENAME,
        workflow_state="blocks_5_9_vertical",
        upstream_run_ids={"candidate_generation": product_run, "candidate_comparison": product_run},
    )
    _write_json(block8_paths["candidate_comparison_json"], comparison)
    _write_json(block8_paths["current_vs_candidate_json"], current_vs_candidate)

    verdict_paths = write_decision_verdict_outputs(
        output_dir=output_dir,
        candidate_generation=candidate_generation,
        current_vs_candidate=current_vs_candidate,
        client_fit_check=diagnosis_docs.get("client_fit_check")
        if isinstance(diagnosis_docs.get("client_fit_check"), Mapping)
        else None,
        problem_classification=diagnosis_docs.get("problem_classification")
        if isinstance(diagnosis_docs.get("problem_classification"), Mapping)
        else None,
    )
    decision_verdict = _read_json_object(verdict_paths["decision_verdict_json"])
    decision_verdict = attach_product_run_metadata(
        decision_verdict or {},
        run_id=product_run,
        artifact_role=DECISION_VERDICT_FILENAME,
        workflow_state="blocks_5_9_vertical",
        upstream_run_ids={"candidate_generation": product_run, "current_vs_candidate": product_run},
    )
    _write_json(verdict_paths["decision_verdict_json"], decision_verdict)

    ai_paths = write_ai_commentary_context_outputs(
        output_dir=output_dir,
        comparison=comparison,
        current_vs_candidate=current_vs_candidate,
        selection=None,
        decision_verdict=decision_verdict,
        action=None,
        problem_classification=diagnosis_docs.get("problem_classification"),
        candidate_launchpad=diagnosis_docs.get("candidate_launchpad"),
        portfolio_alternatives_builder=builder_doc,
        candidate_generation=candidate_generation,
        monitoring_diff=None,
        portfolio_xray=diagnosis_docs.get("portfolio_xray"),
        stress_report=diagnosis_docs.get("stress_report"),
    )
    ai_context = _read_json_object(ai_paths["ai_commentary_context_json"])
    ai_context = attach_product_run_metadata(
        ai_context or {},
        run_id=product_run,
        artifact_role="ai_commentary_context.json",
        workflow_state="blocks_5_9_vertical",
        upstream_run_ids={
            "candidate_generation": product_run_id(candidate_generation),
            "candidate_comparison": product_run_id(comparison),
            "current_vs_candidate": product_run_id(current_vs_candidate),
            "decision_verdict": product_run_id(decision_verdict),
        },
    )
    _write_json(ai_paths["ai_commentary_context_json"], ai_context)

    return {
        "status": "completed",
        "product_run_id": product_run,
        "diagnosis_command": diagnosis["command"],
        "removed_stale_artifacts": removed_stale,
        "selected_card": builder_doc.get("selected_card_id"),
        "selected_method": (builder_doc.get("candidate_setup") or {}).get("selected_method"),
        "candidate_id": candidate_id,
        "artifact_paths": {
            "problem_classification_json": diagnosis_docs.get("problem_classification_path"),
            "candidate_launchpad_json": diagnosis_docs.get("candidate_launchpad_path"),
            "portfolio_alternatives_builder_json": builder_path,
            "candidate_generation_json": output_dir / CANDIDATE_GENERATION_FILENAME,
            "candidate_comparison_json": block8_paths["candidate_comparison_json"],
            "current_vs_candidate_json": block8_paths["current_vs_candidate_json"],
            "decision_verdict_json": verdict_paths["decision_verdict_json"],
            "ai_commentary_context_json": ai_paths["ai_commentary_context_json"],
        },
    }


def build_selected_builder_document(
    *,
    output_dir: str | Path,
    diagnosis_docs: Mapping[str, Any],
    method: str = DEFAULT_DEMO_METHOD,
    constraint_preset: str | None = None,
    mode: str | None = None,
    card_id: str | None = None,
) -> tuple[Path, dict[str, Any]]:
    """Select one Launchpad card, build one valid Builder document, and write it."""

    out = Path(output_dir)
    problem = diagnosis_docs.get("problem_classification")
    launchpad = diagnosis_docs.get("candidate_launchpad")
    existing_builder_path = resolve_portfolio_alternatives_builder_path(out)
    existing_builder = _read_json_object(existing_builder_path) if existing_builder_path else None

    card = select_demo_launchpad_card(launchpad, preferred_method=method, card_id=card_id)
    next_step = problem.get("next_diagnostic_step") if isinstance(problem, Mapping) else None
    next_step = next_step if isinstance(next_step, Mapping) else None
    client_fit_check = diagnosis_docs.get("client_fit_check")
    client_fit_check = client_fit_check if isinstance(client_fit_check, Mapping) else None

    if isinstance(card, Mapping):
        prefill = launchpad_card_to_builder_prefill(
            card,
            next_diagnostic_step=next_step,
            client_fit_check=client_fit_check,
        )
    elif isinstance(existing_builder, Mapping) and isinstance(
        existing_builder.get("builder_prefill"), Mapping
    ):
        prefill = existing_builder["builder_prefill"]
    else:
        raise VerticalFlowError("launchpad_card_or_builder_prefill_missing")

    overrides: dict[str, Any] = {"method": method}
    if constraint_preset is not None:
        overrides["constraint_preset"] = constraint_preset
    elif method in {"equal_weight", "risk_parity"}:
        overrides["constraint_preset"] = "basic_reference"
    if mode is not None:
        overrides["mode"] = mode

    setup = build_simple_builder_parameters(prefill, overrides=overrides)
    validation = validate_builder_setup(setup)
    candidate_setup = builder_prefill_to_candidate_setup(prefill, edits=overrides)
    if candidate_setup is None:
        reason = validation.get("validation_status") or "builder_validation_failed"
        errors = ",".join(str(row) for row in validation.get("validation_errors") or [])
        raise VerticalFlowError(f"builder_setup_not_generatable:{reason}:{errors}")

    builder_doc = build_portfolio_alternatives_builder_document(
        prefill,
        candidate_setup,
        validation,
    )
    builder_path = existing_builder_path or out / "analysis_subject" / PORTFOLIO_ALTERNATIVES_BUILDER_FILENAME
    builder_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(builder_path, builder_doc)
    return builder_path, builder_doc


def select_demo_launchpad_card(
    candidate_launchpad: Mapping[str, Any] | None,
    *,
    preferred_method: str = DEFAULT_DEMO_METHOD,
    card_id: str | None = None,
) -> Mapping[str, Any] | None:
    """Return one demo card, preferring reference/mixed-evidence cards.

    The default demo is a simple Equal Weight reference test when possible.
    If no reference/mixed card exists, the first generatable targeted card is
    used.  Monitor/data-quality cards are not selected.
    """

    if not isinstance(candidate_launchpad, Mapping):
        return None
    cards = candidate_launchpad.get("cards")
    if not isinstance(cards, Sequence) or isinstance(cards, (str, bytes)):
        return None
    rows = [card for card in cards if isinstance(card, Mapping)]
    if card_id:
        for card in rows:
            if str(card.get("card_id") or "") == card_id:
                return card
        raise VerticalFlowError(f"launchpad_card_not_found:{card_id}")

    generatable = [
        card
        for card in rows
        if _card_has_method(card, preferred_method)
        and str(card.get("card_type") or "") != "monitor_or_data_step"
    ]
    reference_or_mixed = [
        card for card in generatable if _card_is_reference_or_mixed(card)
    ]
    if reference_or_mixed:
        return reference_or_mixed[0]
    if generatable:
        return generatable[0]
    for card in rows:
        if _card_has_any_method(card) and str(card.get("card_type") or "") != "monitor_or_data_step":
            return card
    return None


def _run_diagnosis_only_review(
    *,
    root: Path,
    config_path: str | Path | None,
    python_executable: str,
    output_profile: str,
    no_cache: bool,
    runner: Any,
) -> dict[str, Any]:
    command = [
        python_executable,
        str(root / "run_portfolio_review.py"),
        "--skip-candidates",
        "--skip-compare",
        "--output-profile",
        output_profile,
    ]
    if config_path is not None:
        command.extend(["--config", str(config_path)])
    if no_cache:
        command.append("--no-cache")
    completed = runner(
        command,
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if int(getattr(completed, "returncode", 1)) != 0:
        stderr = str(getattr(completed, "stderr", "") or "")
        raise VerticalFlowError(f"diagnosis_only_review_failed:{stderr[-500:]}")
    return {"command": command, "returncode": int(getattr(completed, "returncode", 0))}


def _remove_stale_vertical_artifacts(output_dir: Path) -> list[str]:
    removed: list[str] = []
    for filename in STALE_VERTICAL_FILENAMES:
        path = output_dir / filename
        if path.is_file():
            path.unlink()
            removed.append(filename)
    return removed


def _card_has_method(card: Mapping[str, Any], method: str) -> bool:
    normalized = str(method or "").strip()
    for row in card.get("suggested_methods") or []:
        if isinstance(row, Mapping) and str(row.get("candidate_method_id") or "").strip() == normalized:
            return True
    return str(card.get("default_method") or "").strip() == normalized


def _card_has_any_method(card: Mapping[str, Any]) -> bool:
    rows = card.get("suggested_methods")
    return isinstance(rows, Sequence) and not isinstance(rows, (str, bytes)) and bool(rows)


def _card_is_reference_or_mixed(card: Mapping[str, Any]) -> bool:
    values = [
        card.get("card_type"),
        card.get("launch_status"),
        card.get("source_diagnosis_id"),
        card.get("source_problem_id"),
        card.get("goal"),
    ]
    text = " ".join(str(value or "").lower() for value in values)
    return (
        "reference" in text
        or "mixed_evidence" in text
        or "mixed evidence" in text
        or str(card.get("card_type") or "") == "reference_benchmark_test"
    )


def _read_json_object(path: str | Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else None


def _write_json(path: str | Path, data: Mapping[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run Blocks 5-9 as one diagnosis-first, one-candidate vertical product demo."
    )
    parser.add_argument(
        "--method",
        default=DEFAULT_DEMO_METHOD,
        help="Guided Builder method to test (default: equal_weight).",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to demo config.yml (default: project root config.yml).",
    )
    parser.add_argument(
        "--preset",
        dest="constraint_preset",
        default=None,
        help="Optional Block 6 constraint preset override.",
    )
    parser.add_argument("--mode", default=None, help="Optional capped/uncapped mode override.")
    parser.add_argument("--card-id", default=None, help="Optional Launchpad card id override.")
    parser.add_argument("--no-cache", action="store_true", help="Pass --no-cache to diagnosis-only review.")
    parser.add_argument("--force-candidate", action="store_true", help="Force the one candidate factory step.")
    parser.add_argument(
        "--factory-execution-mode",
        choices=["fast", "standard", "legacy_full"],
        default="fast",
        help=(
            "Backend factory mode for the selected candidate (default: fast). "
            "Use standard to attempt fresh comparison snapshots; may be slow until factor/FRED "
            "runtime is hardened."
        ),
    )
    parser.add_argument(
        "--skip-factory",
        action="store_true",
        help="Testing/debug only: write a non-comparable candidate attempt without backend weights.",
    )
    parser.add_argument(
        "--output-profile",
        default="site_api",
        help="Output profile for diagnosis-only review (default: site_api).",
    )
    args = parser.parse_args(argv)

    try:
        result = run_blocks_5_to_9_vertical_flow(
            config_path=args.config,
            method=args.method,
            constraint_preset=args.constraint_preset,
            mode=args.mode,
            card_id=args.card_id,
            no_cache=bool(args.no_cache),
            force_candidate=bool(args.force_candidate),
            run_factory=not args.skip_factory,
            factory_execution_mode=args.factory_execution_mode,
            output_profile=args.output_profile,
        )
    except (VerticalFlowError, PortfolioAlternativesBuilderError) as exc:
        print(f"Blocks 5-9 vertical flow failed: {exc}", file=sys.stderr)
        return 2

    print("Blocks 5-9 vertical flow completed.")
    print(f"selected_card={result.get('selected_card')}")
    print(f"selected_method={result.get('selected_method')}")
    print(f"candidate_id={result.get('candidate_id')}")
    for key, value in (result.get("artifact_paths") or {}).items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
