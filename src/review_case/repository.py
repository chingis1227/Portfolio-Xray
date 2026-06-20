"""Run-local persistence for Portfolio MRI Review Cases.

The repository is a small storage seam around the existing ``review_state.json``
file. It stores the same public ``review_state_v1`` JSON shape that the FastAPI
staged review routes already use, but exposes typed ``ReviewCase`` load/save
operations for architecture migration work. It intentionally does not introduce
new public routes, envelopes, CLI commands, or generated artifact schemas.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .domain import ReviewCase


class ReviewCaseRepositoryError(ValueError):
    """Raised when a run-local Review Case cannot be loaded or saved safely."""


class RunLocalReviewCaseRepository:
    """Load and save one Review Case in a run-local folder."""

    def __init__(self, run_dir: Path, *, schema_version: str) -> None:
        self.run_dir = Path(run_dir)
        self.schema_version = schema_version

    @property
    def state_path(self) -> Path:
        return self.run_dir / "review_state.json"

    @property
    def temporary_state_path(self) -> Path:
        return self.run_dir / "review_state.json.tmp"

    def exists(self) -> bool:
        return self.state_path.is_file()

    def save(self, review_case: ReviewCase) -> None:
        """Atomically save ``review_case`` as the existing staged-state JSON."""

        self.run_dir.mkdir(parents=True, exist_ok=True)
        state = review_case.to_staged_state_dict(schema_version=self.schema_version)
        self.temporary_state_path.write_text(
            json.dumps(state, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self.temporary_state_path.replace(self.state_path)

    def load(self) -> ReviewCase:
        """Load and validate a Review Case from ``review_state.json``."""

        try:
            raw_state = json.loads(self.state_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise
        except json.JSONDecodeError as exc:
            raise ReviewCaseRepositoryError("Run-local review_state.json is not valid JSON.") from exc
        if not isinstance(raw_state, dict):
            raise ReviewCaseRepositoryError("Run-local review_state.json must contain a JSON object.")
        return ReviewCase.from_staged_state_dict(
            raw_state,
            expected_schema_version=self.schema_version,
        )

    def load_optional(self) -> ReviewCase | None:
        """Return ``None`` when ``review_state.json`` does not exist."""

        if not self.exists():
            return None
        return self.load()


def staged_state_path(run_dir: Path) -> Path:
    """Return the existing run-local staged-state file path."""

    return Path(run_dir) / "review_state.json"


def staged_state_dict_from_case(review_case: ReviewCase, *, schema_version: str) -> dict[str, Any]:
    """Serialize a Review Case to the current public staged-state dictionary."""

    return review_case.to_staged_state_dict(schema_version=schema_version)
