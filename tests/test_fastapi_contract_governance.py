from __future__ import annotations

from pathlib import Path

from scripts.verify_fastapi_contract_governance import (
    _validate_mapping_notes,
    _validate_response_sourcing,
    _validate_text_governance,
    verify_fastapi_contract_governance,
)
from src.api.app import app


def test_fastapi_contract_governance_is_current() -> None:
    assert verify_fastapi_contract_governance() == []


def test_sourced_claim_governance_rejects_missing_source_fields() -> None:
    schema = app.openapi()
    diagnosis_schema = schema["components"]["schemas"]["DiagnosisEvidenceItem"]
    removed = diagnosis_schema["properties"].pop("source_field_path")
    try:
        errors = _validate_response_sourcing(schema)
    finally:
        diagnosis_schema["properties"]["source_field_path"] = removed

    assert any("DiagnosisEvidenceItem" in error and "source_field_path" in error for error in errors)


def test_mapping_note_governance_requires_recommendation_boundary() -> None:
    mapping = {
        "operations": [
            {
                "operation_id": "generateCandidate",
                "mapping_note": "One diagnostic candidate attempt only.",
            }
        ]
    }

    errors = _validate_mapping_notes(mapping)

    assert any("generateCandidate" in error and "not a recommendation" in error for error in errors)


def test_text_governance_allows_boundary_language_but_rejects_advice_like_claims(tmp_path: Path) -> None:
    bad = tmp_path / "bad.tsx"
    bad.write_text('const hero = "This is the best portfolio for you.";', encoding="utf-8")
    safe = tmp_path / "safe.tsx"
    safe.write_text(
        'const boundary = "This is not the best portfolio and not a trade instruction.";',
        encoding="utf-8",
    )

    errors = _validate_text_governance([bad, safe])

    assert any("bad.tsx" in error and "best portfolio" in error for error in errors)
    assert all("safe.tsx" not in error for error in errors)
