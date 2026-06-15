from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_review_from_payload import DEFAULT_TIMEOUT_SECONDS, MODE_DIAGNOSIS_PLUS_PROBLEM, run_from_payload


BLOCKER_TOKENS = (
    "DATA_PROVIDER_FAILED",
    "market data produced no usable prices",
    "market data produced an empty panel",
    "FRED fetch timed out",
    "FRED download failed",
    "yfinance",
)


def _run_once(payload: Path, timeout_seconds: int) -> tuple[int, Path, float, dict]:
    started = time.perf_counter()
    code, result_path = run_from_payload(
        payload,
        mode=MODE_DIAGNOSIS_PLUS_PROBLEM,
        timeout_seconds=timeout_seconds,
    )
    elapsed = time.perf_counter() - started
    try:
        result = json.loads(result_path.read_text(encoding="utf-8"))
    except Exception:
        result = {}
    return code, result_path, elapsed, result if isinstance(result, dict) else {}


def _blocker_from_result(result: dict) -> str | None:
    text = json.dumps(result, ensure_ascii=False)
    for token in BLOCKER_TOKENS:
        if token.lower() in text.lower():
            return token
    return None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Measure staged diagnosis cold-ish and warm runtime.")
    parser.add_argument("--payload", type=Path, required=True, help="Frontend portfolio payload JSON.")
    parser.add_argument("--warm-threshold-seconds", type=float, default=30.0)
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = args.payload
    if not payload.is_file():
        print(f"status=failed\nmessage=Payload not found: {payload}", file=sys.stderr)
        return 2

    cold_code, cold_path, cold_seconds, cold_result = _run_once(payload, args.timeout_seconds)
    if cold_code != 0:
        blocker = _blocker_from_result(cold_result)
        print(f"cold_seconds={cold_seconds:.3f}")
        print(f"cold_result={cold_path}")
        if blocker:
            print("status=blocked")
            print(f"blocker={blocker}")
            print(f"message={cold_result.get('error') or cold_result.get('details') or 'External data provider blocked diagnosis.'}")
            return 3
        print("status=failed")
        print(f"message={cold_result.get('error') or 'Cold diagnosis run failed.'}")
        return 1

    warm_code, warm_path, warm_seconds, warm_result = _run_once(payload, args.timeout_seconds)
    print(f"cold_seconds={cold_seconds:.3f}")
    print(f"warm_seconds={warm_seconds:.3f}")
    print(f"warm_threshold_seconds={float(args.warm_threshold_seconds):.3f}")
    print(f"cold_result={cold_path}")
    print(f"warm_result={warm_path}")

    if warm_code != 0:
        blocker = _blocker_from_result(warm_result)
        if blocker:
            print("status=blocked")
            print(f"blocker={blocker}")
            print(f"message={warm_result.get('error') or warm_result.get('details') or 'External data provider blocked diagnosis.'}")
            return 3
        print("status=failed")
        print(f"message={warm_result.get('error') or 'Warm diagnosis run failed.'}")
        return 1

    if warm_seconds > float(args.warm_threshold_seconds):
        print("status=failed")
        print("message=Warm diagnosis runtime exceeded threshold.")
        return 1

    print("status=passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
