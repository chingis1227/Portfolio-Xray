#!/usr/bin/env python3
"""Generate one Block 7 candidate attempt from a Block 6 Builder setup.

Default input:
    Main portfolio/analysis_subject/portfolio_alternatives_builder.json

Default output:
    Main portfolio/candidate_generation.json

The script delegates weights generation to the existing one-candidate factory
plumbing, then adapts the result into the product-facing Block 7 artifact.  It
does not compare candidates, does not write a verdict, and does not silently
fall back to another method when the selected candidate fails.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.candidate_generation import (  # noqa: E402
    CandidateGenerationError,
    build_candidate_generation_document,
    candidate_setup_from_builder_document,
)
from src.config import ConfigValidationError, load_validated_config  # noqa: E402

DEFAULT_BUILDER_INPUT = Path("Main portfolio") / "analysis_subject" / "portfolio_alternatives_builder.json"
DEFAULT_OUTPUT = Path("Main portfolio") / "candidate_generation.json"
DEFAULT_FACTORY_RUN = Path("Main portfolio") / "candidate_factory_run.json"

SUCCESS_FACTORY_STATUSES = frozenset({"succeeded", "skipped_existing"})


def generate_candidate_from_builder_setup(
    *,
    builder_input: str | Path,
    output_path: str | Path,
    project_root: str | Path = REPO_ROOT,
    run_factory: bool = True,
    force: bool = False,
    factory_run_json: str | Path | None = None,
    config_path: str | Path | None = None,
    factory_execution_mode: str = "fast",
    python_executable: str | None = None,
    runner: Any = subprocess.run,
) -> dict[str, Any]:
    """Read Builder setup, optionally run the backend factory, and write Block 7 JSON."""

    root = Path(project_root)
    builder_path = _resolve_path(builder_input, root)
    output = _resolve_path(output_path, root)
    builder_document = _read_json_object(builder_path)
    candidate_setup = candidate_setup_from_builder_document(builder_document)

    initial_document = build_candidate_generation_document(candidate_setup)
    candidate_id = str(initial_document["candidate"]["candidate_id"])
    warnings: list[str] = []
    kwargs: dict[str, Any] = {}

    if run_factory:
        completed = _run_one_candidate_factory(
            candidate_id,
            project_root=root,
            force=force,
            config_path=config_path,
            execution_mode=factory_execution_mode,
            python_executable=python_executable,
            runner=runner,
        )
        factory_path = (
            _resolve_path(factory_run_json, root)
            if factory_run_json is not None
            else _default_factory_run_path(root, config_path)
        )
        factory_doc = _read_json_object(factory_path) if factory_path.is_file() else None
        kwargs = generation_kwargs_from_factory_result(
            project_root=root,
            candidate_id=candidate_id,
            factory_doc=factory_doc,
            returncode=int(getattr(completed, "returncode", 1)),
            stderr=str(getattr(completed, "stderr", "") or ""),
        )
        warnings.extend(_factory_warnings(factory_doc))
    else:
        warnings.append("factory_not_run_candidate_weights_not_available")

    runtime_warnings = list(kwargs.pop("warnings", []))
    runtime_warnings.extend(warnings)
    document = build_candidate_generation_document(
        candidate_setup,
        warnings=runtime_warnings,
        **kwargs,
    )
    _write_json(output, document)
    return document


def generation_kwargs_from_factory_result(
    *,
    project_root: str | Path,
    candidate_id: str,
    factory_doc: Mapping[str, Any] | None,
    returncode: int,
    stderr: str | None = None,
) -> dict[str, Any]:
    """Translate backend factory evidence into Candidate Generation builder kwargs.

    Failure and infeasibility statuses deliberately win over any existing
    ``weights.json`` on disk.  This prevents a stale artifact from converting a
    failed attempt into a comparable or recommended candidate.
    """

    if not isinstance(factory_doc, Mapping):
        reason = f"factory_run_json_missing_or_invalid; returncode={returncode}"
        if stderr:
            reason = f"{reason}; stderr_tail={stderr[-500:]}"
        return {"status": "failed", "failure_reason": reason}

    step = _factory_step_for_candidate(factory_doc, candidate_id)
    if step is None:
        return {
            "status": "failed",
            "failure_reason": f"factory_step_missing:{candidate_id}",
        }

    status = str(step.get("status") or "").strip()
    if status in SUCCESS_FACTORY_STATUSES:
        weights_path = _weights_path_for_step(project_root, step)
        weights = _read_weights(weights_path) if weights_path is not None else None
        if weights:
            return {
                "weights": weights,
                "status": "generated",
                "warnings": [f"factory_step_status:{status}"],
            }
        return {
            "status": "failed",
            "failure_reason": _step_reason(
                step,
                fallback=f"candidate_weights_missing_after_factory_{status}",
            ),
        }

    reason = _step_reason(step, fallback=f"candidate_factory_status:{status or 'unknown'}")
    if _step_is_infeasible(step):
        return {"status": "infeasible", "infeasibility_reason": reason}
    return {"status": "failed", "failure_reason": reason}


def _run_one_candidate_factory(
    candidate_id: str,
    *,
    project_root: Path,
    force: bool,
    config_path: str | Path | None,
    execution_mode: str,
    python_executable: str | None,
    runner: Any,
) -> Any:
    py = python_executable or sys.executable
    command = [
        py,
        str(project_root / "run_candidate_factory.py"),
        "--candidates",
        candidate_id,
        "--execution-mode",
        execution_mode,
        "--output-profile",
        "site_api",
        "--fail-fast",
    ]
    if config_path is not None:
        command.extend(["--config", str(config_path)])
    if force:
        command.append("--force")
    env = os.environ.copy()
    for name in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
    ):
        env.setdefault(name, "1")
    return runner(
        command,
        cwd=str(project_root),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _factory_step_for_candidate(
    factory_doc: Mapping[str, Any],
    candidate_id: str,
) -> Mapping[str, Any] | None:
    for step in factory_doc.get("steps") or []:
        if isinstance(step, Mapping) and str(step.get("candidate_id") or "") == candidate_id:
            return step
    return None


def _weights_path_for_step(project_root: str | Path, step: Mapping[str, Any]) -> Path | None:
    artifact_root = str(step.get("artifact_root") or "").strip()
    if not artifact_root:
        return None
    return Path(project_root) / artifact_root / "weights.json"


def _default_factory_run_path(project_root: Path, config_path: str | Path | None) -> Path:
    """Return the factory summary path for the same config used by the factory.

    Demo configs use config-isolated ``output_dir_final`` folders.  Reading the
    legacy ``Main portfolio/candidate_factory_run.json`` path here makes Block 7
    miss fresh factory output while Block 8 can still find it from the config
    output directory.
    """

    if config_path is not None:
        try:
            cfg = load_validated_config(config_path)
            return project_root / str(getattr(cfg, "output_dir_final", "Main portfolio")) / "candidate_factory_run.json"
        except (ConfigValidationError, FileNotFoundError, OSError):
            pass
    return project_root / DEFAULT_FACTORY_RUN


def _read_weights(path: Path | None) -> dict[str, float] | None:
    if path is None or not path.is_file():
        return None
    data = _read_json_object(path)
    weights: dict[str, float] = {}
    for ticker, value in data.items():
        if isinstance(value, bool):
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if numeric > 0:
            weights[str(ticker)] = numeric
    return weights or None


def _step_is_infeasible(step: Mapping[str, Any]) -> bool:
    values = (
        step.get("reason_code"),
        step.get("builder_status"),
        step.get("builder_reason"),
        step.get("message"),
    )
    text = " ".join(str(value or "").lower() for value in values)
    return "infeasible" in text


def _step_reason(step: Mapping[str, Any], *, fallback: str) -> str:
    parts = [
        str(step.get("reason_code") or "").strip(),
        str(step.get("builder_status") or "").strip(),
        str(step.get("builder_reason") or "").strip(),
        str(step.get("message") or "").strip(),
    ]
    reason = "; ".join(part for part in parts if part)
    return reason or fallback


def _factory_warnings(factory_doc: Mapping[str, Any] | None) -> list[str]:
    if not isinstance(factory_doc, Mapping):
        return []
    warnings = [str(warning) for warning in factory_doc.get("warnings") or []]
    profile = factory_doc.get("factory_profile_id")
    if profile:
        warnings.append(f"factory_profile_id:{profile}")
    return warnings


def _resolve_path(path: str | Path, project_root: Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return project_root / candidate


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CandidateGenerationError(f"json_file_missing:{path}") from exc
    except json.JSONDecodeError as exc:
        raise CandidateGenerationError(f"json_file_invalid:{path}") from exc
    if not isinstance(data, dict):
        raise CandidateGenerationError(f"json_file_not_object:{path}")
    return data


def _write_json(path: Path, data: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate one candidate_generation.json artifact from one validated "
            "portfolio_alternatives_builder.json setup."
        )
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_BUILDER_INPUT),
        help="Builder artifact path (default: Main portfolio/analysis_subject/portfolio_alternatives_builder.json).",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Candidate Generation artifact path (default: Main portfolio/candidate_generation.json).",
    )
    parser.add_argument(
        "--project-root",
        default=str(REPO_ROOT),
        help="Repository root used for relative paths.",
    )
    parser.add_argument(
        "--factory-run-json",
        default=None,
        help="Optional candidate_factory_run.json path to inspect after factory execution.",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to config.yml for backend candidate factory (default: project root config.yml).",
    )
    parser.add_argument(
        "--factory-execution-mode",
        choices=["fast", "standard", "legacy_full"],
        default="fast",
        help=(
            "Backend candidate factory execution mode (default: fast). "
            "Use standard when Block 8 needs fresh lightweight comparison snapshots."
        ),
    )
    parser.add_argument(
        "--skip-factory",
        action="store_true",
        help="Write an attempt_created artifact without running backend candidate plumbing.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Pass --force to run_candidate_factory.py when running backend plumbing.",
    )
    args = parser.parse_args(argv)

    try:
        document = generate_candidate_from_builder_setup(
            builder_input=args.input,
            output_path=args.output,
            project_root=args.project_root,
            run_factory=not args.skip_factory,
            force=bool(args.force),
            factory_run_json=args.factory_run_json,
            config_path=args.config,
            factory_execution_mode=args.factory_execution_mode,
        )
    except CandidateGenerationError as exc:
        print(f"Candidate generation failed before runtime artifact could be written: {exc}", file=sys.stderr)
        return 2

    output = _resolve_path(args.output, Path(args.project_root))
    print(f"Wrote {output}")
    print(f"generation_status={document.get('generation_status')}")
    print(f"can_compare={(document.get('handoff_to_comparison') or {}).get('can_compare')}")
    return 0 if document.get("generation_status") in {"generated", "attempt_created"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
