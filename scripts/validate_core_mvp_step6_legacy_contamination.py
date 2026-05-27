#!/usr/bin/env python3
"""
Validate Core MVP fixture matrix Step 6 (absence of legacy contamination).

Reads per fixture (when present):
  output/fixture_matrix_runs/<fixture_id>/analysis_subject/run_metadata.json
  output/fixture_matrix_runs/<fixture_id>/analysis_subject/portfolio_xray.json
  output/fixture_matrix_runs/<fixture_id>/analysis_subject/stress_report.json
  output/fixture_matrix_runs/<fixture_id>/analysis_subject/output_manifest.json

Also runs entrypoint preflight safety audit against:
  run_report.run_materialize_analysis_subject_report

Writes:
  output/fixture_matrix_runs/step6_legacy_contamination_validation.json
"""
from __future__ import annotations

import argparse
import ast
import inspect
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from run_report import run_materialize_analysis_subject_report


FORBIDDEN_EXACT_KEYS = {
    "pass",
    "mandate_pass",
    "mandate_status",
    "pass_fail",
    "loss_ok",
    "max_dd_limit",
    "mandate",
    "suitability",
    "client_profile",
    "target_return",
    "target_volatility",
    "target_max_drawdown",
}

FORBIDDEN_EXACT_ARTIFACT_KEYS = {
    "candidate_launchpad_json",
    "candidate_comparison_json",
    "current_vs_candidate_json",
    "decision_verdict_json",
    "selection_decision_json",
    "what_changed_summary_json",
    "candidate_factory_run_json",
    "candidate_factory_manifest_json",
    "run_result_json",
    "portfolio_weights_yml",
    "portfolio_weights_yaml",
    "portfolio_comparison_json",
    "ew_rp_comparison_json",
}

PREFLIGHT_FORBIDDEN_CALLS = {
    "run_candidate_factory",
    "run_compare_variants",
    "run_compare_ew_rp",
    "run_optimization",
}

PREFLIGHT_FORBIDDEN_IDENTIFIERS = {
    "decision_verdict",
    "selection_decision",
    "mandate",
    "suitability",
    "loss_ok",
    "pass_fail",
    "mandate_pass",
    "mandate_status",
}

TARGET_FILES = (
    "run_metadata.json",
    "portfolio_xray.json",
    "stress_report.json",
    "output_manifest.json",
)


@dataclass
class Hit:
    file_name: str
    path: str
    key: str
    value: Any
    classification: str
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "file_name": self.file_name,
            "path": self.path,
            "key": self.key,
            "value": self.value,
            "classification": self.classification,
            "reason": self.reason,
        }


def _is_nullish(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def _json_path(base_path: str, key: str) -> str:
    if not base_path:
        return key
    return f"{base_path}.{key}"


def _index_path(base_path: str, idx: int) -> str:
    if not base_path:
        return f"[{idx}]"
    return f"{base_path}[{idx}]"


def _has_legacy_scope_false(ancestors: list[Any]) -> bool:
    for node in ancestors:
        if not isinstance(node, dict):
            continue
        scope = node.get("_scope")
        if isinstance(scope, dict) and scope.get("product_surface") is False:
            return True
    return False


def _walk_for_hits(
    *,
    obj: Any,
    file_name: str,
    path: str,
    ancestors: list[Any],
    hits: list[Hit],
) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_text = str(key)
            key_path = _json_path(path, key_text)
            if key_text in FORBIDDEN_EXACT_KEYS or key_text in FORBIDDEN_EXACT_ARTIFACT_KEYS:
                in_legacy_scope = _has_legacy_scope_false([*ancestors, obj])
                if in_legacy_scope:
                    hits.append(
                        Hit(
                            file_name=file_name,
                            path=key_path,
                            key=key_text,
                            value=value,
                            classification="legacy_compat_only",
                            reason="ancestor _scope.product_surface == false",
                        )
                    )
                elif _is_nullish(value):
                    hits.append(
                        Hit(
                            file_name=file_name,
                            path=key_path,
                            key=key_text,
                            value=value,
                            classification="harmless_null_legacy_field",
                            reason="value is null/empty with no active payload",
                        )
                    )
                else:
                    hits.append(
                        Hit(
                            file_name=file_name,
                            path=key_path,
                            key=key_text,
                            value=value,
                            classification="product_facing_active_contamination",
                            reason="exact forbidden key present with active value",
                        )
                    )

            _walk_for_hits(
                obj=value,
                file_name=file_name,
                path=key_path,
                ancestors=[*ancestors, obj],
                hits=hits,
            )
        return

    if isinstance(obj, list):
        for idx, item in enumerate(obj):
            _walk_for_hits(
                obj=item,
                file_name=file_name,
                path=_index_path(path, idx),
                ancestors=[*ancestors, obj],
                hits=hits,
            )


def _scan_json_file(path: Path) -> tuple[list[Hit], str | None]:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return [], f"JSON_PARSE_ERROR: {exc}"

    hits: list[Hit] = []
    _walk_for_hits(
        obj=doc,
        file_name=path.name,
        path="",
        ancestors=[],
        hits=hits,
    )
    return hits, None


def _collect_called_names(source: str) -> set[str]:
    tree = ast.parse(source)
    called: set[str] = set()
    identifiers: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Name):
                called.add(fn.id)
            elif isinstance(fn, ast.Attribute):
                called.add(fn.attr)
        elif isinstance(node, ast.Name):
            identifiers.add(node.id)
        elif isinstance(node, ast.Attribute):
            identifiers.add(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            identifiers.add(node.value)
    return called | identifiers


def _entrypoint_preflight() -> dict[str, Any]:
    source = inspect.getsource(run_materialize_analysis_subject_report)
    names = _collect_called_names(source)

    forbidden_calls_found = sorted(name for name in PREFLIGHT_FORBIDDEN_CALLS if name in names)
    forbidden_identifiers_found = sorted(name for name in PREFLIGHT_FORBIDDEN_IDENTIFIERS if name in names)
    status = "ok" if not forbidden_calls_found and not forbidden_identifiers_found else "failed"

    return {
        "status": status,
        "forbidden_calls_found": forbidden_calls_found,
        "forbidden_identifiers_found": forbidden_identifiers_found,
    }


def _fixture_status(classifications: list[str], file_errors: list[str], missing_files: list[str]) -> str:
    if file_errors:
        return "failed"
    if "product_facing_active_contamination" in classifications:
        return "failed"
    if missing_files:
        return "partial"
    if "harmless_null_legacy_field" in classifications or "legacy_compat_only" in classifications:
        return "partial"
    return "ok"


def _validate_fixture(fixture_dir: Path) -> dict[str, Any]:
    fixture_id = fixture_dir.name
    analysis_subject_dir = fixture_dir / "analysis_subject"

    hits: list[Hit] = []
    missing_files: list[str] = []
    file_errors: list[str] = []
    scanned_files: list[str] = []
    per_file_hit_counts: dict[str, int] = {}

    for file_name in TARGET_FILES:
        target = analysis_subject_dir / file_name
        if not target.is_file():
            missing_files.append(file_name)
            continue
        scanned_files.append(file_name)
        file_hits, err = _scan_json_file(target)
        if err:
            file_errors.append(f"{file_name}: {err}")
            continue
        hits.extend(file_hits)
        per_file_hit_counts[file_name] = len(file_hits)

    classifications = [h.classification for h in hits]
    status = _fixture_status(classifications, file_errors=file_errors, missing_files=missing_files)

    rollup = {
        "product_facing_active_contamination": sum(1 for h in hits if h.classification == "product_facing_active_contamination"),
        "legacy_compat_only": sum(1 for h in hits if h.classification == "legacy_compat_only"),
        "harmless_null_legacy_field": sum(1 for h in hits if h.classification == "harmless_null_legacy_field"),
    }

    return {
        "fixture_id": fixture_id,
        "analysis_subject_dir": str(analysis_subject_dir.relative_to(REPO_ROOT)),
        "status": status,
        "scanned_files": scanned_files,
        "missing_files": missing_files,
        "file_errors": file_errors,
        "classification_counts": rollup,
        "per_file_hit_counts": per_file_hit_counts,
        "findings": [h.as_dict() for h in hits],
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Step 6 legacy contamination for fixture matrix outputs")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=REPO_ROOT / "output" / "fixture_matrix_runs",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    output_root = args.output_root.resolve()
    fixture_dirs = sorted([p for p in output_root.glob("fx*") if p.is_dir()])
    if not fixture_dirs:
        raise RuntimeError(f"No fixture directories found in {output_root}")

    preflight = _entrypoint_preflight()
    results = []
    for fixture_dir in fixture_dirs:
        row = _validate_fixture(fixture_dir)
        results.append(row)
        print(f"[{row['status'].upper()}] {row['fixture_id']}")

    counts = {
        "ok": sum(1 for r in results if r["status"] == "ok"),
        "partial": sum(1 for r in results if r["status"] == "partial"),
        "failed": sum(1 for r in results if r["status"] == "failed"),
    }
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "step": "step_6_legacy_contamination_validation",
        "output_root": str(output_root),
        "entrypoint_preflight": preflight,
        "counts": counts,
        "results": results,
    }
    out_path = output_root / "step6_legacy_contamination_validation.json"
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSummary: {out_path}")

    failed = counts["failed"] > 0 or preflight["status"] != "ok"
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
