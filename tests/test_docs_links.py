from __future__ import annotations

from src.docs_verify import (
    collect_cursor_markdown_files,
    collect_source_markdown_files,
    find_broken_local_links,
    find_forbidden_references,
    find_removed_config_ui_fields,
    verify_docs,
)


def test_source_markdown_local_file_references_exist() -> None:
    failures = find_broken_local_links(collect_source_markdown_files())
    assert not failures, "\n".join(failures)


def test_source_markdown_has_no_forbidden_canonical_paths() -> None:
    failures = find_forbidden_references(collect_source_markdown_files())
    assert not failures, "\n".join(failures)


def test_config_ui_does_not_expose_removed_rc_asset_cap_field() -> None:
    failures = find_removed_config_ui_fields()
    assert not failures, "\n".join(failures)


def test_cursor_agent_docs_do_not_reference_removed_canonical_paths() -> None:
    failures = find_forbidden_references(collect_cursor_markdown_files())
    assert not failures, "\n".join(failures)


def test_cursor_agent_local_file_references_exist() -> None:
    failures = find_broken_local_links(collect_cursor_markdown_files())
    assert not failures, "\n".join(failures)


def test_verify_docs_aggregate_passes() -> None:
    assert verify_docs().ok
