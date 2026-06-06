"""Warm or validate the approved FRED factor-series cache.

This is an operator smoke tool for demo readiness. It does not calculate
portfolio weights, does not run candidate generation, and does not replace the
full factor matrix. It only exercises the same raw FRED factor cache policy that
``src.stress_factors`` uses before Block 2.3 / Stress Lab diagnostics.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import stress_factors as sf  # noqa: E402


DEFAULT_START = "2007-01-01"


def _date_arg(value: str) -> str:
    return str(pd.Timestamp(value).date())


def _series_ids(raw: str | None) -> list[str]:
    if not raw or raw.strip().lower() == "all":
        return list(sf.FRED_FACTOR_SERIES_IDS)
    return [item.strip().upper() for item in raw.split(",") if item.strip()]


def _summarize_series(series_id: str, series: pd.Series, elapsed: float, *, status: str) -> dict[str, Any]:
    attrs = dict(getattr(series, "attrs", {}) or {})
    return {
        "series_id": series_id,
        "status": status,
        "source_used": attrs.get("source_used") or attrs.get("factor_data_source_used"),
        "cache_status": attrs.get("cache_status") or ("valid" if status == "valid_cached" else None),
        "elapsed_seconds": round(float(elapsed), 3),
        "observations": int(series.dropna().shape[0]) if isinstance(series, pd.Series) else 0,
        "first_observation": str(pd.Timestamp(series.index.min()).date()) if not series.empty else None,
        "last_observation": str(pd.Timestamp(series.index.max()).date()) if not series.empty else None,
        "factor_data_fallback_used": bool(attrs.get("factor_data_fallback_used") or False),
        "factor_data_source_used": attrs.get("factor_data_source_used"),
        "warnings": list(attrs.get("factor_data_warnings") or attrs.get("warnings") or []),
        "factor_data_cache_key": attrs.get("factor_data_cache_key"),
    }


def warm_factor_cache(
    *,
    start: str,
    end: str,
    series_ids: list[str],
    check_only: bool,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    t0 = time.perf_counter()

    for series_id in series_ids:
        t_series = time.perf_counter()
        try:
            if check_only:
                series = sf._load_approved_cached_fred_factor_series(series_id, start, end)
                status = "valid_cached"
            else:
                series = sf._fetch_fred_factor_series(series_id, start, end, force_refresh=True)
                status = "updated"
            rows.append(
                _summarize_series(
                    series_id,
                    series,
                    time.perf_counter() - t_series,
                    status=status,
                )
            )
        except Exception as exc:  # noqa: BLE001 - operator tool must report all series failures.
            failures.append(
                {
                    "series_id": series_id,
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                }
            )
            rows.append(
                {
                    "series_id": series_id,
                    "status": "failed",
                    **sf.factor_cache_status(series_id, start, end),
                    "elapsed_seconds": round(time.perf_counter() - t_series, 3),
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                }
            )

    missing_series = [row["series_id"] for row in rows if row.get("status") == "failed"]
    cache_statuses = {str(row.get("cache_status")) for row in rows if row.get("cache_status")}
    source_used = sorted({str(row.get("source_used")) for row in rows if row.get("source_used")})
    full_factor_matrix_available = not failures
    demo_safe = check_only and full_factor_matrix_available and cache_statuses == {"valid"}
    return {
        "schema_version": "factor_cache_warmup_v1",
        "mode": "check_only" if check_only else "warm",
        "start": start,
        "end": end,
        "cache_root": str(sf._factor_cache_root()),
        "cache_validity_policy": sf.factor_cache_validity_policy(),
        "source_used": source_used[0] if len(source_used) == 1 else source_used,
        "cache_status": (
            "valid"
            if full_factor_matrix_available and cache_statuses == {"valid"}
            else "missing"
            if not cache_statuses
            else "partial"
        ),
        "missing_series": missing_series,
        "full_factor_matrix_available": full_factor_matrix_available,
        "demo_safe": demo_safe,
        "elapsed_seconds": round(time.perf_counter() - t0, 3),
        "series": rows,
        "status": "ok" if not failures else "failed",
        "failures": failures,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Warm or validate approved FRED factor-series cache for demo-safe factor diagnostics."
    )
    parser.add_argument("--start", default=DEFAULT_START, type=_date_arg, help="Required raw factor coverage start.")
    parser.add_argument(
        "--end",
        default=str(pd.Timestamp.today().normalize().date()),
        type=_date_arg,
        help="Required raw factor coverage end.",
    )
    parser.add_argument(
        "--series",
        default="all",
        help="Comma-separated FRED series ids to check/warm, or 'all' for the full factor set.",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Validate approved cache only; do not call live FRED.",
    )
    args = parser.parse_args(argv)

    summary = warm_factor_cache(
        start=args.start,
        end=args.end,
        series_ids=_series_ids(args.series),
        check_only=bool(args.check_only),
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
