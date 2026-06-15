"""Small mtime-aware YAML cache for hot runtime metadata files."""

from __future__ import annotations

import copy
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


def _yaml_cache_key(path: str | Path) -> tuple[str, int, int]:
    resolved = Path(path).resolve()
    stat = resolved.stat()
    return str(resolved), int(stat.st_mtime_ns), int(stat.st_size)


@lru_cache(maxsize=32)
def _load_yaml_cached(resolved_path: str, _mtime_ns: int, _size: int) -> Any:
    with open(resolved_path, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_yaml_mtime_cached(path: str | Path) -> Any:
    """Load YAML and invalidate automatically when file mtime or size changes.

    A deep copy is returned so callers can mutate the result without changing the
    process-level cached value.
    """

    resolved_path, mtime_ns, size = _yaml_cache_key(path)
    return copy.deepcopy(_load_yaml_cached(resolved_path, mtime_ns, size))


def clear_yaml_mtime_cache() -> None:
    """Clear the process-local YAML cache; primarily useful for tests."""

    _load_yaml_cached.cache_clear()
