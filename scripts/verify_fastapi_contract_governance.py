"""Verify FastAPI contract governance for frontend consumption.

This guard makes four contract-drift checks explicit:

1. The generated frontend TypeScript API file must match the live FastAPI
   OpenAPI schema.
2. Every public FastAPI v1 operation and every top-level response ``data``
   field must be listed in the machine-readable screen mapping contract.
3. Public display schemas that carry diagnosis, comparison, verdict, or report
   claims must also expose source/provenance fields.
4. Public frontend/API copy must preserve the diagnostic-test and
   decision-support-only boundary instead of drifting into advice-like wording.

The screen mapping is intentionally separate from generated types. New backend
fields can be generated mechanically, but they do not become visible UI until
the mapping contract, adapters, and screen tests opt in.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
MAPPING_PATH = REPO_ROOT / "docs" / "contracts" / "FASTAPI_SCREEN_MAPPING.json"

REQUIRED_SCHEMA_FIELDS: dict[str, set[str]] = {
    "ArtifactRef": {"kind", "ref", "scope", "raw_path_exposed"},
    "DiagnosisSummary": {
        "diagnosis_evidence_items",
        "metric_to_diagnosis_trace",
        "professional_rationale_refs",
        "recommendation_boundary",
        "source_artifacts",
    },
    "DiagnosisEvidenceItem": {"source_artifact", "source_block", "source_field_path"},
    "DiagnosisRootCauseNarrative": {"source_refs"},
    "DiagnosisMetricTrace": {"evidence_item_id", "source_artifact", "source_block", "source_field_path"},
    "DiagnosisRationaleRef": {"source"},
    "DownstreamEvidenceChainContext": {
        "candidate_boundary",
        "recommendation_boundary",
        "source_artifacts",
    },
    "ReportGrounding": {"source_refs", "unavailable_sections"},
    "VerdictSummary": {"decision_support_only", "evidence_used", "limitations", "what_would_change_verdict"},
}

DATA_SCHEMA_FIELD_DEPENDENCIES: dict[str, dict[str, set[str]]] = {
    "ReviewCreatedData": {
        "diagnosis": {"artifact_refs"},
    },
    "ReviewRecoveryData": {
        "diagnosis": {"artifact_refs"},
    },
    "ComparisonData": {
        "comparison": {"evidence_chain_context"},
    },
    "VerdictData": {
        "verdict": {"evidence_chain_context"},
    },
    "ReportData": {
        "report_preview": {"evidence_chain_context", "grounding", "llm_generated"},
    },
}

OPERATION_NOTE_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "generateCandidate": ("not a recommendation",),
    "runComparison": ("trade-off evidence", "must not", "advice"),
    "generateVerdict": ("non-binding", "evidence"),
    "generateReport": ("grounded", "unsupported"),
}

GOVERNED_TEXT_PATHS = (
    REPO_ROOT / "frontend" / "app",
    REPO_ROOT / "frontend" / "components",
    REPO_ROOT / "frontend" / "lib",
    REPO_ROOT / "src" / "api",
    MAPPING_PATH,
)

GOVERNED_FILE_SUFFIXES = {".json", ".md", ".py", ".ts", ".tsx", ".js", ".cjs"}

ADVICE_LIKE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("recommended portfolio", re.compile(r"\brecommended\s+portfolio\b", re.IGNORECASE)),
    ("best portfolio", re.compile(r"\bbest\s+portfolio\b", re.IGNORECASE)),
    ("winner", re.compile(r"\bwinner\b", re.IGNORECASE)),
    ("must rebalance", re.compile(r"\bmust\s+rebalance\b", re.IGNORECASE)),
    ("trade now", re.compile(r"\btrade\s+now\b", re.IGNORECASE)),
    ("execute trade", re.compile(r"\bexecute\s+(...:a\s+)...trade\b", re.IGNORECASE)),
    ("guaranteed improvement", re.compile(r"\bguaranteed\s+improvement\b", re.IGNORECASE)),
    ("suitability approved", re.compile(r"\bsuitability\s+approved\b", re.IGNORECASE)),
    ("client suitability approved", re.compile(r"\bclient\s+suitability\s+approved\b", re.IGNORECASE)),
)

BOUNDARY_CONTEXT_PATTERN = re.compile(
    r"\b(...:not|no|never|must\s+not|does\s+not|do\s+not|is\s+not|without|instead\s+of)\b",
    re.IGNORECASE,
)

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.generate_fastapi_api_types import OUTPUT_PATH, render_types  # noqa: E402
from src.api.app import app  # noqa: E402


def _ref_name(schema: Any) -> str | None:
    if not isinstance(schema, dict):
        return None
    ref = schema.get("$ref")
    if isinstance(ref, str):
        return ref.rsplit("/", 1)[-1]
    return None


def _schema_properties(openapi_schema: dict[str, Any], schema_name: str | None) -> list[str]:
    if not schema_name:
        return []
    schema = openapi_schema.get("components", {}).get("schemas", {}).get(schema_name, {})
    properties = schema.get("properties") if isinstance(schema, dict) else None
    if not isinstance(properties, dict):
        return []
    return sorted(str(name) for name in properties)


def _request_schema_name(operation: dict[str, Any]) -> str | None:
    return _ref_name(
        operation.get("requestBody", {})
        .get("content", {})
        .get("application/json", {})
        .get("schema")
    )


def _response_schema_name(operation: dict[str, Any], status: str = "200") -> str | None:
    return _ref_name(
        operation.get("responses", {})
        .get(status, {})
        .get("content", {})
        .get("application/json", {})
        .get("schema")
    )


def _data_schema_name(openapi_schema: dict[str, Any], response_schema_name: str | None) -> str | None:
    if not response_schema_name:
        return None
    response_schema = (
        openapi_schema.get("components", {})
        .get("schemas", {})
        .get(response_schema_name, {})
    )
    if not isinstance(response_schema, dict):
        return None
    return _ref_name(response_schema.get("properties", {}).get("data"))


def _openapi_operations(openapi_schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    operations: dict[str, dict[str, Any]] = {}
    for path, path_item in sorted((openapi_schema.get("paths") or {}).items()):
        if not isinstance(path_item, dict):
            continue
        for method, operation in sorted(path_item.items()):
            if not isinstance(operation, dict):
                continue
            operation_id = operation.get("operationId")
            if not isinstance(operation_id, str) or not operation_id:
                continue
            response_schema = _response_schema_name(operation)
            data_schema = _data_schema_name(openapi_schema, response_schema)
            operations[operation_id] = {
                "operation_id": operation_id,
                "method": method.upper(),
                "path": path,
                "request_schema": _request_schema_name(operation),
                "success_status": "200",
                "response_schema": response_schema,
                "data_schema": data_schema,
                "public_data_fields": _schema_properties(openapi_schema, data_schema),
            }
    return operations


def _schema_property_set(openapi_schema: dict[str, Any], schema_name: str) -> set[str]:
    return set(_schema_properties(openapi_schema, schema_name))


def _load_mapping() -> dict[str, Any]:
    return json.loads(MAPPING_PATH.read_text(encoding="utf-8"))


def _validate_response_sourcing(openapi_schema: dict[str, Any]) -> list[str]:
    """Verify display claim schemas keep source/provenance companions."""

    errors: list[str] = []
    schemas = openapi_schema.get("components", {}).get("schemas", {})
    for schema_name, required_fields in sorted(REQUIRED_SCHEMA_FIELDS.items()):
        if schema_name not in schemas:
            errors.append(f"OpenAPI schema {schema_name} is missing; sourced-claim governance cannot run.")
            continue
        actual_fields = _schema_property_set(openapi_schema, schema_name)
        missing_fields = sorted(required_fields - actual_fields)
        if missing_fields:
            errors.append(
                f"{schema_name}: sourced-claim governance requires fields {missing_fields}, "
                f"but schema exposes {sorted(actual_fields)}."
            )

    for schema_name, dependencies in sorted(DATA_SCHEMA_FIELD_DEPENDENCIES.items()):
        actual_fields = _schema_property_set(openapi_schema, schema_name)
        if not actual_fields:
            errors.append(f"OpenAPI data schema {schema_name} is missing or has no public fields.")
            continue
        for claim_field, required_companions in sorted(dependencies.items()):
            if claim_field not in actual_fields:
                continue
            missing_companions = sorted(required_companions - actual_fields)
            if missing_companions:
                errors.append(
                    f"{schema_name}: public claim field {claim_field!r} requires provenance/boundary "
                    f"companions {missing_companions}."
                )
    return errors


def _iter_governed_text_files() -> list[Path]:
    files: list[Path] = []
    for path in GOVERNED_TEXT_PATHS:
        if not path.exists():
            continue
        if path.is_file():
            candidates = [path]
        else:
            candidates = [candidate for candidate in path.rglob("*") if candidate.is_file()]
        files.extend(
            candidate
            for candidate in candidates
            if candidate.suffix.lower() in GOVERNED_FILE_SUFFIXES
            and "generated" not in candidate.parts
            and ".next" not in candidate.parts
        )
    return sorted(set(files))


def _is_boundary_or_guardrail_line(line: str) -> bool:
    return bool(BOUNDARY_CONTEXT_PATTERN.search(line))


def _validate_text_governance(files: list[Path] | None = None) -> list[str]:
    """Scan public display/API copy for unqualified advice-like wording."""

    errors: list[str] = []
    for path in files if files is not None else _iter_governed_text_files():
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for lineno, line in enumerate(lines, start=1):
            for label, pattern in ADVICE_LIKE_PATTERNS:
                if not pattern.search(line):
                    continue
                if _is_boundary_or_guardrail_line(line):
                    continue
                rel = path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path
                errors.append(
                    f"{rel}:{lineno}: advice-like phrase {label!r} is not framed as a boundary/guardrail."
                )
    return errors


def _validate_mapping_notes(mapping: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    operations = {
        row.get("operation_id"): row
        for row in mapping.get("operations", [])
        if isinstance(row, dict) and isinstance(row.get("operation_id"), str)
    }
    for operation_id, required_terms in sorted(OPERATION_NOTE_REQUIREMENTS.items()):
        note = str(operations.get(operation_id, {}).get("mapping_note") or "").lower()
        missing_terms = [term for term in required_terms if term not in note]
        if missing_terms:
            errors.append(
                f"{operation_id}: mapping_note must include governance terms {missing_terms} "
                "so the screen contract preserves the evidence/recommendation boundary."
            )
    return errors


def verify_fastapi_contract_governance() -> list[str]:
    """Return governance errors. An empty list means the guard passes."""

    errors: list[str] = []
    openapi_schema = app.openapi()
    expected_types = render_types(openapi_schema)
    generated_types = OUTPUT_PATH.read_text(encoding="utf-8")
    if generated_types != expected_types:
        errors.append(
            "frontend/lib/generated/api-types.ts is stale. "
            "Regenerate it with .\\.venv\\Scripts\\python.exe scripts\\generate_fastapi_api_types.py."
        )

    mapping = _load_mapping()
    if mapping.get("schema_version") != "fastapi_screen_mapping_v1":
        errors.append("FASTAPI_SCREEN_MAPPING.json schema_version must be fastapi_screen_mapping_v1.")

    for doc in mapping.get("contract_docs", []):
        if not isinstance(doc, str) or not (REPO_ROOT / doc).exists():
            errors.append(f"Mapped contract doc is missing: {doc!r}.")

    errors.extend(_validate_mapping_notes(mapping))
    errors.extend(_validate_response_sourcing(openapi_schema))
    errors.extend(_validate_text_governance())

    allowed_routes = set(mapping.get("allowed_screen_routes") or [])
    mapped_operations = {
        row.get("operation_id"): row
        for row in mapping.get("operations", [])
        if isinstance(row, dict) and isinstance(row.get("operation_id"), str)
    }
    openapi_operations = _openapi_operations(openapi_schema)

    missing = sorted(set(openapi_operations) - set(mapped_operations))
    extra = sorted(set(mapped_operations) - set(openapi_operations))
    if missing:
        errors.append(f"OpenAPI operations missing from FASTAPI_SCREEN_MAPPING.json: {missing}.")
    if extra:
        errors.append(f"FASTAPI_SCREEN_MAPPING.json lists operations not present in OpenAPI: {extra}.")

    for operation_id, expected in sorted(openapi_operations.items()):
        mapped = mapped_operations.get(operation_id)
        if not mapped:
            continue
        for key in (
            "method",
            "path",
            "request_schema",
            "success_status",
            "response_schema",
            "data_schema",
        ):
            if mapped.get(key) != expected.get(key):
                errors.append(
                    f"{operation_id}: mapped {key}={mapped.get(key)!r} does not match "
                    f"OpenAPI {expected.get(key)!r}."
                )
        mapped_fields = sorted(str(field) for field in (mapped.get("public_data_fields") or []))
        if mapped_fields != expected["public_data_fields"]:
            errors.append(
                f"{operation_id}: public_data_fields are {mapped_fields}, "
                f"but OpenAPI data schema {expected['data_schema']} has {expected['public_data_fields']}."
            )

        routes = mapped.get("screen_routes")
        if not isinstance(routes, list):
            errors.append(f"{operation_id}: screen_routes must be a list.")
            continue
        unknown_routes = sorted(str(route) for route in routes if route not in allowed_routes)
        if unknown_routes:
            errors.append(f"{operation_id}: screen_routes include unknown MVP routes {unknown_routes}.")
        if operation_id != "getHealth" and not routes:
            errors.append(f"{operation_id}: non-health operation must map to at least one screen route.")
        if not isinstance(mapped.get("mapping_note"), str) or not mapped["mapping_note"].strip():
            errors.append(f"{operation_id}: mapping_note is required.")

    return errors


def main() -> int:
    errors = verify_fastapi_contract_governance()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("FastAPI contract governance OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
