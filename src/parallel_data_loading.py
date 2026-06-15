"""Bounded helpers for independent data-loading tasks.

The helpers in this module are intentionally small and standard-library only.
They preserve the input order while allowing callers to overlap independent
I/O-bound provider calls.  Callers still own item-level error semantics.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import os
from typing import Callable, Generic, Iterable, TypeVar


T = TypeVar("T")
R = TypeVar("R")

MAX_DATA_LOAD_WORKERS = 16


@dataclass(frozen=True)
class ParallelLoadResult(Generic[T, R]):
    """Result for one bounded data-load item."""

    index: int
    item: T
    value: R | None = None
    exception: Exception | None = None


def parallel_data_load_disabled() -> bool:
    """Return True when operators request sequential data loading."""

    raw = os.environ.get("PMRI_DISABLE_PARALLEL_DATA_LOAD", "")
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def resolve_data_load_workers(env_name: str, default: int, item_count: int) -> int:
    """Resolve an effective worker count for a bounded data-load operation."""

    count = max(0, int(item_count or 0))
    if count <= 1 or parallel_data_load_disabled():
        return 1
    try:
        configured = int(str(os.environ.get(env_name, "")).strip())
    except (TypeError, ValueError):
        configured = int(default)
    if configured <= 0:
        configured = int(default)
    return max(1, min(count, configured, MAX_DATA_LOAD_WORKERS))


def bounded_parallel_map(
    items: Iterable[T],
    worker_fn: Callable[[T], R],
    *,
    env_name: str,
    default_workers: int,
) -> list[ParallelLoadResult[T, R]]:
    """Run ``worker_fn`` over ``items`` with bounded concurrency.

    The returned list always follows the original input order.  Exceptions are
    captured into ``ParallelLoadResult.exception`` so callers can preserve their
    existing per-item error handling rules.
    """

    ordered_items = list(items)
    workers = resolve_data_load_workers(env_name, default_workers, len(ordered_items))
    if workers <= 1:
        sequential: list[ParallelLoadResult[T, R]] = []
        for index, item in enumerate(ordered_items):
            try:
                sequential.append(ParallelLoadResult(index=index, item=item, value=worker_fn(item)))
            except Exception as exc:  # noqa: BLE001 - preserve caller-owned semantics.
                sequential.append(ParallelLoadResult(index=index, item=item, exception=exc))
        return sequential

    results: list[ParallelLoadResult[T, R] | None] = [None] * len(ordered_items)
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="pmri-data-load") as executor:
        future_to_item = {
            executor.submit(worker_fn, item): (index, item)
            for index, item in enumerate(ordered_items)
        }
        for future in as_completed(future_to_item):
            index, item = future_to_item[future]
            try:
                results[index] = ParallelLoadResult(index=index, item=item, value=future.result())
            except Exception as exc:  # noqa: BLE001 - preserve caller-owned semantics.
                results[index] = ParallelLoadResult(index=index, item=item, exception=exc)

    return [result for result in results if result is not None]
