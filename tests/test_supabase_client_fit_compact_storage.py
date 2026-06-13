from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PERSISTENCE_TSX = PROJECT_ROOT / "frontend" / "lib" / "supabase" / "persistence.tsx"


def test_supabase_client_fit_storage_uses_compact_display_summary_only() -> None:
    source = PERSISTENCE_TSX.read_text(encoding="utf-8")

    assert "compactClientFitForCloud" in source
    assert "clientFitFromCloud" in source
    assert "clientFit: compactClientFitForCloud" in source

    client_fit_block = source[
        source.index("function compactClientFitForCloud"):
        source.index("type ComparisonResultSummaryClientFit")
    ]
    assert "statusLabel" in client_fit_block
    assert "targetRows" in client_fit_block
    assert "client_fit_check" not in client_fit_block
    assert "source_artifacts" not in client_fit_block
    assert "schema_version" not in client_fit_block
    assert "artifact" not in client_fit_block.lower()
    assert "json" not in client_fit_block.lower()


def test_supabase_client_fit_recovery_reads_compact_cloud_fields_only() -> None:
    source = PERSISTENCE_TSX.read_text(encoding="utf-8")
    recovery_block = source[
        source.index("function clientFitFromCloud"):
        source.index("function compactClientFitForCloud")
    ]

    assert "statusLabel" in recovery_block
    assert "targetRows" in recovery_block
    assert "client_fit_check" not in recovery_block
    assert "source_artifacts" not in recovery_block
    assert "schema_version" not in recovery_block
    assert "artifact" not in recovery_block.lower()
    assert "json" not in recovery_block.lower()
