#!/usr/bin/env python3
"""Session 07 validator: one-candidate product demo (--candidates equal_weight).

Reads on-disk artifacts under output_dir_final and checks product scoping contracts.
Exit 0 when all checks pass; exit 1 with a human-readable report otherwise.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.product_bundle_paths import (  # noqa: E402
    PRODUCT_BUNDLE_MANIFEST_KEYS,
    discover_product_bundle_paths,
)

NO_TRADE_VERDICT_IDS = frozenset(
    {
        "no_trade",
        "evidence_insufficient",
        "no_trade_evidence_insufficient",
        "hold_current",
    }
)


def _load_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    with open(path, encoding="utf-8") as handle:
        doc = json.load(handle)
    return doc if isinstance(doc, dict) else None


def validate_one_candidate_demo(
    output_dir: Path,
    *,
    expected_candidate_id: str = "equal_weight",
) -> tuple[bool, list[str]]:
    """Return (ok, messages) for Session 07 acceptance checks."""
    messages: list[str] = []
    ok = True

    def fail(msg: str) -> None:
        nonlocal ok
        ok = False
        messages.append(f"FAIL: {msg}")

    def pass_(msg: str) -> None:
        messages.append(f"PASS: {msg}")

    factory_run = _load_json(output_dir / "candidate_factory_run.json")
    if factory_run is None:
        fail("candidate_factory_run.json missing")
    else:
        step_ids = [
            str(step.get("candidate_id"))
            for step in factory_run.get("steps") or []
            if step.get("candidate_id")
        ]
        if step_ids != [expected_candidate_id]:
            fail(
                f"factory steps {step_ids!r} != [{expected_candidate_id!r}] "
                "(factory must touch only the selected hypothesis)"
            )
        else:
            pass_(f"factory_run steps == [{expected_candidate_id}]")

    current_vs = _load_json(output_dir / "current_vs_candidate.json")
    if current_vs is None:
        fail("current_vs_candidate.json missing")
    else:
        selected = list(current_vs.get("selected_candidate_ids") or [])
        if selected != [expected_candidate_id]:
            fail(
                f"current_vs_candidate.selected_candidate_ids={selected!r} "
                f"expected [{expected_candidate_id!r}]"
            )
        else:
            pass_(f"current_vs_candidate scopes to {expected_candidate_id}")

    verdict = _load_json(output_dir / "decision_verdict.json")
    if verdict is None:
        fail("decision_verdict.json missing")
    else:
        selected_id = verdict.get("selected_candidate_id")
        verdict_id = str(verdict.get("verdict_id") or "")
        if selected_id == expected_candidate_id:
            pass_(f"decision_verdict.selected_candidate_id == {expected_candidate_id}")
        elif selected_id is None and verdict_id in NO_TRADE_VERDICT_IDS:
            pass_(f"decision_verdict is no-trade/evidence-insufficient for run ({verdict_id})")
        else:
            fail(
                f"decision_verdict.selected_candidate_id={selected_id!r} "
                f"(verdict_id={verdict_id!r}); stale candidate must not control verdict"
            )

    for rel in (
        "ai_commentary_context.json",
        "what_changed_summary.json",
    ):
        if not (output_dir / rel).is_file():
            fail(f"{rel} missing")
        else:
            pass_(f"{rel} present")

    manifest = _load_json(output_dir / "output_manifest.json")
    if manifest is None:
        fail("output_manifest.json missing")
    else:
        discovery_paths = discover_product_bundle_paths(manifest)
        missing = [k for k in PRODUCT_BUNDLE_MANIFEST_KEYS if k not in discovery_paths]
        if missing:
            fail(f"output_manifest missing product bundle keys: {missing}")
        else:
            pass_("output_manifest product_discovery lists six bundle paths")
        if manifest.get("primary_output_surface") != "product_bundle":
            fail(
                "output_manifest.primary_output_surface != product_bundle "
                f"(got {manifest.get('primary_output_surface')!r})"
            )
        else:
            pass_("output_manifest.primary_output_surface == product_bundle")

    comparison = _load_json(output_dir / "candidate_comparison.json")
    if comparison is None:
        fail("candidate_comparison.json missing (technical evidence)")
    else:
        scope = comparison.get("product_candidate_scope") or {}
        scope_ids = list(scope.get("candidate_ids") or [])
        if scope_ids != [expected_candidate_id]:
            fail(f"product_candidate_scope.candidate_ids={scope_ids!r}")
        else:
            pass_("candidate_comparison.product_candidate_scope matches CLI hypothesis")

    return ok, messages


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "Main portfolio",
        help="output_dir_final folder to validate (default: Main portfolio/)",
    )
    parser.add_argument(
        "--candidate-id",
        default="equal_weight",
        help="expected selected candidate id (default: equal_weight)",
    )
    args = parser.parse_args(argv)
    output_dir = args.output_dir.resolve()
    if not output_dir.is_dir():
        print(f"ERROR: output directory not found: {output_dir}", file=sys.stderr)
        return 2

    ok, messages = validate_one_candidate_demo(
        output_dir, expected_candidate_id=args.candidate_id
    )
    for line in messages:
        print(line)
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
