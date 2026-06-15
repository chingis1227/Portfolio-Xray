"""Verify the local staged Run Diagnosis route contract.

This guard is intentionally lightweight: it imports the local FastAPI app
instead of requiring a running server, then checks that the Next.js
compatibility route still targets the staged FastAPI endpoint.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(REPO_ROOT))

from src.api.app import app


STAGED_ROUTE = "/api/v1/reviews/staged"
DIAGNOSE_ROUTE = REPO_ROOT / "frontend" / "app" / "api" / "portfolio" / "diagnose" / "route.ts"
FASTAPI_BRIDGE = REPO_ROOT / "frontend" / "lib" / "server" / "fastapiBridge.ts"
MISMATCH_MESSAGE = (
    "Frontend/backend version mismatch: FastAPI OpenAPI does not expose "
    "POST /api/v1/reviews/staged. Restart the FastAPI backend and Next.js "
    "frontend so both use the same route contract."
)


def main() -> int:
    errors: list[str] = []
    openapi = app.openapi()
    staged_path = openapi.get("paths", {}).get(STAGED_ROUTE, {})
    if "post" not in staged_path:
        errors.append(MISMATCH_MESSAGE)

    diagnose_source = DIAGNOSE_ROUTE.read_text(encoding="utf-8")
    bridge_source = FASTAPI_BRIDGE.read_text(encoding="utf-8")
    if "diagnoseViaFastApi" not in diagnose_source:
        errors.append(
            "Frontend/backend version mismatch: /api/portfolio/diagnose no longer calls "
            "the FastAPI diagnosis bridge."
        )
    if f'"{STAGED_ROUTE}"' not in bridge_source:
        errors.append(
            "Frontend/backend version mismatch: the Next.js FastAPI bridge no longer calls "
            "POST /api/v1/reviews/staged."
        )
    if "Frontend/backend version mismatch" not in bridge_source:
        errors.append(
            "Frontend/backend version mismatch guard text is missing from the Next.js bridge."
        )

    if errors:
        print("Staged Run Diagnosis compatibility guard failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Staged Run Diagnosis compatibility guard passed: POST /api/v1/reviews/staged is present and /api/portfolio/diagnose targets it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
