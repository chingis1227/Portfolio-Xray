from __future__ import annotations

"""
Candidate Portfolio Factory CLI.

Orchestrates existing per-candidate builder scripts without reimplementing formulas.
See docs/specs/candidate_factory_spec.md.
"""

import argparse
from pathlib import Path

from src.candidate_factory import (
    FactoryValidationError,
    build_factory_run_txt,
    factory_exit_code,
    run_candidate_factory,
    run_then_compare,
    write_candidate_factory_outputs,
)
from src.config import load_validated_config
from src.config_schema import ConfigValidationError
from src.utils import logger, setup_logging


def _parse_candidates(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    return [part.strip() for part in raw.split(",") if part.strip()]


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    parser = argparse.ArgumentParser(
        description="Run candidate portfolio builders in a controlled factory profile."
    )
    parser.add_argument(
        "--profile",
        type=str,
        default="default_v1",
        help="Factory profile id (default: default_v1).",
    )
    parser.add_argument(
        "--candidates",
        type=str,
        default=None,
        help="Comma-separated candidate ids; overrides --profile.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        default=True,
        help="Skip builders when snapshot_10y.json exists (default: on).",
    )
    parser.add_argument(
        "--no-skip-existing",
        action="store_false",
        dest="skip_existing",
        help="Always attempt builders unless other skip rules apply.",
    )
    parser.add_argument("--force", action="store_true", help="Rerun even when snapshot exists.")
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop factory on first failed step.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help=(
            "Resume from candidate_factory_manifest.json: skip succeeded and "
            "fresh skipped_existing steps when run checksum matches."
        ),
    )
    parser.add_argument(
        "--then-compare",
        action="store_true",
        help="Run comparison and decision package after factory completes.",
    )
    parser.add_argument(
        "--pdf-mode",
        type=str,
        default="none",
        choices=["none", "final_only", "per_candidate"],
        help=(
            "Per-candidate PDF rebuild policy for factory subprocess builders "
            "(default: none — sets PORTFOLIO_SKIP_VARIANT_PDF=1). "
            "Standalone run_*.py scripts are unchanged unless this env is set."
        ),
    )
    parser.add_argument(
        "--execution-mode",
        type=str,
        default="legacy_full",
        choices=["fast", "standard", "legacy_full"],
        help=(
            "fast: in-process weights only. standard: weights + lightweight_comparison "
            "report (snapshots for compare, no per-candidate PDF). legacy_full: full "
            "subprocess run_*.py chain (default)."
        ),
    )
    parser.add_argument(
        "--full-candidate-reports",
        action="store_true",
        help=(
            "After the main factory phases, export full report_profile artifacts "
            "(HTML, commentary, rolling betas) for all candidates in this run."
        ),
    )
    parser.add_argument(
        "--selected-candidates-for-full-report",
        type=str,
        default=None,
        help=(
            "Comma-separated candidate ids for Phase 3 full report export. "
            "Implies --full-candidate-reports when set."
        ),
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to config.yml (default: project root config.yml).",
    )
    args = parser.parse_args(argv)

    project_root = Path(__file__).resolve().parent
    config_path = Path(args.config) if args.config else project_root / "config.yml"

    try:
        cfg = load_validated_config(config_path)
    except (ConfigValidationError, FileNotFoundError) as exc:
        logger.error("Configuration error: %s", exc)
        return 2

    explicit = _parse_candidates(args.candidates)
    profile_id = "explicit_list" if explicit is not None else args.profile
    selected_full = _parse_candidates(args.selected_candidates_for_full_report)
    full_reports = bool(args.full_candidate_reports or selected_full)

    try:
        doc = run_candidate_factory(
            cfg,
            project_root=project_root,
            profile_id=profile_id,
            explicit_candidates=explicit,
            skip_existing=args.skip_existing,
            force=args.force,
            fail_fast=args.fail_fast,
            resume=args.resume,
            config_path=config_path if config_path.is_file() else None,
            pdf_mode=args.pdf_mode,
            execution_mode=args.execution_mode,
            full_candidate_reports=full_reports,
            selected_candidates_for_full_report=selected_full,
        )
    except FactoryValidationError as exc:
        logger.error("%s", exc)
        return 2

    doc["options"]["then_compare"] = args.then_compare

    out_dir = project_root / cfg.output_dir_final
    written = write_candidate_factory_outputs(doc, output_dir=out_dir)

    if args.then_compare:
        paths, err = run_then_compare(
            cfg,
            project_root=project_root,
            factory_run=doc,
        )
        if err:
            doc.setdefault("warnings", []).append(f"comparison_failed: {err}")
        elif paths:
            doc["comparison_outputs"] = {k: str(v) for k, v in paths.items()}
            write_candidate_factory_outputs(doc, output_dir=out_dir)
    logger.info("Factory run summary: %s", written["candidate_factory_run_json"])

    code = factory_exit_code(doc)
    print(build_factory_run_txt(doc))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
