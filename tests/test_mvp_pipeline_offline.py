"""Offline end-to-end smoke test for the file-first MVP decision pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from src.candidate_comparison import write_candidate_comparison_outputs
from mvp_offline_fixtures import (
    MVP_DECISION_PACKAGE_ARTIFACTS,
    load_mvp_config,
    seed_minimal_mvp_workspace,
    write_minimal_config_yaml,
)


def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*_args, **_kwargs):
        raise AssertionError("MVP offline smoke test must not use live network data")

    import src.data_fred as data_fred
    import src.data_yf as data_yf

    monkeypatch.setattr(data_yf, "download_all", _boom)
    monkeypatch.setattr(data_fred, "fetch_fred_series", _boom, raising=False)


def _assert_decision_package_chain(out_dir: Path) -> None:
    for filename, schema_version in MVP_DECISION_PACKAGE_ARTIFACTS:
        path = out_dir / filename
        assert path.is_file(), f"missing {filename}"
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
        assert doc.get("schema_version") == schema_version, filename

    snapshot_latest = out_dir / "monitoring" / "latest" / "analysis_snapshot.json"
    assert snapshot_latest.is_file()
    with open(snapshot_latest, encoding="utf-8") as f:
        snap = json.load(f)
    assert snap.get("schema_version") == "analysis_snapshot_v1"

    with open(out_dir / "selection_decision.json", encoding="utf-8") as f:
        selection = json.load(f)
    favored = selection.get("favored_candidate_id") or selection.get("selected_candidate_id")
    status = selection.get("decision_status")
    assert status
    if favored:
        assert status in ("selected_candidate", "no_material_rebalance")
    else:
        assert status == "inconclusive"
        assert "no_favor_eligible_candidates" in (selection.get("warnings") or [])

    with open(out_dir / "decision_package_summary.json", encoding="utf-8") as f:
        package = json.load(f)
    assert package.get("summary_plain_en")
    assert package.get("sections", {}).get("selection", {}).get("availability") == "available"


def test_mvp_offline_decision_package_pipeline(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Config + synthetic snapshots -> comparison -> action -> decision package (no network)."""
    _block_network(monkeypatch)
    seed_minimal_mvp_workspace(tmp_path)
    cfg = load_mvp_config(tmp_path)

    paths = write_candidate_comparison_outputs(cfg, project_root=tmp_path)
    out_dir = tmp_path / "Main portfolio"

    assert paths["candidate_comparison_json"] == out_dir / "candidate_comparison.json"
    _assert_decision_package_chain(out_dir)


def test_mvp_offline_config_yaml_entry(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Prove the pipeline starts from on-disk config input, not only in-memory dicts."""
    _block_network(monkeypatch)
    seed_minimal_mvp_workspace(tmp_path)
    config_path = write_minimal_config_yaml(tmp_path)

    with open(config_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    from src.config_schema import validate_config

    cfg = validate_config(raw)
    write_candidate_comparison_outputs(cfg, project_root=tmp_path)
    _assert_decision_package_chain(tmp_path / "Main portfolio")
