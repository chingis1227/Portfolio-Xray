#!/usr/bin/env python3
"""Session 07 gate: Core MVP historical_stress_replay_v1 on subject stress_report.json.

Validates live or CI-materialized ``analysis_subject/stress_report.json`` against
docs/specs/core_mvp_historical_stress_replay_spec.md (DEC-2026-05-28-001).

Exit 0 when all checks pass; exit 1 with a human-readable report otherwise.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.core_mvp_historical_stress_replay import CORE_MVP_HISTORICAL_SCENARIO_IDS  # noqa: E402
from src.scenario_library import HISTORICAL_SCENARIO_IDS  # noqa: E402

_FORBIDDEN_KEYS = frozenset(
    {
        "used_proxies",
        "proxy_coverage_weight_pct",
        "proxy_assisted_replay",
        "approved_etf_proxies",
    }
)
_REPLAY_MERGE_KEYS = (
    "replay_status",
    "direct_coverage_weight_pct",
    "unavailable_weight_pct",
    "portfolio_level_result_available",
    "user_note",
    "diagnosis_summary_en",
)


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    with open(path, encoding="utf-8") as handle:
        doc = json.load(handle)
    return doc if isinstance(doc, dict) else None


def verify_core_mvp_historical_stress_replay(
    stress_report: dict[str, Any],
) -> tuple[bool, list[str]]:
    messages: list[str] = []
    ok = True

    def fail(msg: str) -> None:
        nonlocal ok
        ok = False
        messages.append(f"FAIL: {msg}")

    def pass_(msg: str) -> None:
        messages.append(f"PASS: {msg}")

    if stress_report.get("historical_stress_replay_v1_error"):
        fail(
            f"historical_stress_replay_v1_error: {stress_report['historical_stress_replay_v1_error']}"
        )
        return ok, messages

    replay = stress_report.get("historical_stress_replay_v1")
    if not isinstance(replay, dict):
        fail("missing historical_stress_replay_v1 (diagnostic run expected)")
        return ok, messages

    if replay.get("version") != "core_mvp_historical_stress_replay_v1":
        fail(f"unexpected replay version: {replay.get('version')!r}")
    else:
        pass_("replay version core_mvp_historical_stress_replay_v1")

    if replay.get("policy") != "direct_history_only":
        fail(f"unexpected replay policy: {replay.get('policy')!r}")
    else:
        pass_("policy direct_history_only")

    episodes = replay.get("episodes")
    if not isinstance(episodes, list):
        fail("replay episodes is not a list")
        return ok, messages

    ids = [str(ep.get("scenario_id")) for ep in episodes if isinstance(ep, dict)]
    expected = list(HISTORICAL_SCENARIO_IDS)
    if ids != expected:
        fail(f"episode order mismatch: {ids} != {expected}")
    elif len(ids) != len(CORE_MVP_HISTORICAL_SCENARIO_IDS):
        fail(f"episode count {len(ids)} != {len(CORE_MVP_HISTORICAL_SCENARIO_IDS)}")
    else:
        pass_(f"five replay episodes in canonical order ({', '.join(ids)})")

    replay_by_id = {str(ep["scenario_id"]): ep for ep in episodes if isinstance(ep, dict)}

    for sid, ep in replay_by_id.items():
        for key in _FORBIDDEN_KEYS:
            if key in ep:
                fail(f"{sid}: forbidden key {key}")
        direct = float(ep.get("direct_coverage_weight_pct") or 0)
        unavail = float(ep.get("unavailable_weight_pct") or 0)
        if abs(direct + unavail - 100.0) > 0.05:
            fail(f"{sid}: coverage weights sum to {direct + unavail}, not 100")
        status = ep.get("replay_status")
        full = ep.get("portfolio_level_result_available") is True
        loss = ep.get("portfolio_loss_pct")
        dd = ep.get("drawdown_pct")
        if full:
            if status != "full_replay":
                fail(f"{sid}: portfolio_level_result_available but status={status!r}")
            if loss is None or dd is None:
                fail(f"{sid}: full replay missing portfolio_loss_pct or drawdown_pct")
        else:
            if loss is not None or dd is not None:
                fail(f"{sid}: partial/unavailable replay must not set portfolio metrics")
        if not isinstance(ep.get("user_note"), str) or not ep["user_note"].strip():
            fail(f"{sid}: missing user_note")
        if not isinstance(ep.get("diagnosis_summary_en"), str) or not ep["diagnosis_summary_en"].strip():
            fail(f"{sid}: missing diagnosis_summary_en")

    sr = stress_report.get("stress_results_v1")
    if not isinstance(sr, dict):
        fail("missing stress_results_v1 for Block 3.2 merge check")
    else:
        hist_rows = sr.get("historical_episodes")
        if not isinstance(hist_rows, list):
            fail("stress_results_v1.historical_episodes missing")
        else:
            for row in hist_rows:
                if not isinstance(row, dict):
                    continue
                sid = str(row.get("episode") or "")
                rep = replay_by_id.get(sid)
                if not rep:
                    continue
                for key in _REPLAY_MERGE_KEYS:
                    if key not in row:
                        fail(f"Block 3.2 row {sid} missing merged field {key}")
                if rep.get("portfolio_level_result_available"):
                    if row.get("portfolio_loss_pct") != rep.get("portfolio_loss_pct"):
                        fail(f"{sid}: Block 3.2 loss != replay loss on full replay")
                    if row.get("replay_status") != rep.get("replay_status"):
                        fail(f"{sid}: Block 3.2 replay_status mismatch")
                else:
                    if row.get("portfolio_loss_pct") is not None or row.get("drawdown_pct") is not None:
                        fail(f"{sid}: Block 3.2 must clear portfolio metrics when replay not full")
                    if row.get("diagnosis_summary_en") != rep.get("diagnosis_summary_en"):
                        fail(f"{sid}: Block 3.2 diagnosis must match replay on non-full replay")
            pass_("Block 3.2 historical_episodes merge replay fields")

    if stress_report.get("loss_gate_mode") != "diagnostic":
        fail(f"expected loss_gate_mode diagnostic, got {stress_report.get('loss_gate_mode')!r}")
    else:
        pass_("loss_gate_mode diagnostic")

    return ok, messages


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stress-report",
        type=Path,
        default=REPO_ROOT / "Main portfolio" / "analysis_subject" / "stress_report.json",
        help="Path to subject stress_report.json",
    )
    args = parser.parse_args()
    report = _load_json(args.stress_report)
    if report is None:
        print(f"FAIL: cannot read {args.stress_report}", file=sys.stderr)
        return 1
    ok, messages = verify_core_mvp_historical_stress_replay(report)
    for line in messages:
        print(line)
    if ok:
        print(f"OK: Core MVP historical stress replay verified ({args.stress_report})")
        return 0
    print(f"FAILED: {args.stress_report}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
