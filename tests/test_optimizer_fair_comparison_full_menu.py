"""Phase 17 Session 04 (RM-1023): full-menu optimizer fair-comparison readiness offline gate."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.candidate_comparison import build_candidate_comparison
from src.optimization_readiness import SCHEMA_VERSION
from optimizer_fair_comparison_fixtures import (
    FULL_MENU_OPTIMIZER_SEED_SPECS,
    fair_ready_optimizer_ids,
    fixture_portfolio_config,
    full_menu_fair_ready_fingerprint,
    seed_full_menu_optimizer_artifacts,
)

_FIXTURES = Path(__file__).resolve().parent / "fixtures"
FULL_MENU_FAIR_READY_GOLDEN_PATH = (
    _FIXTURES / "optimization_comparison_full_menu_fair_ready_golden_v1.json"
)

MINIMUM_FAIR_READY_OPTIMIZERS = 3


@pytest.fixture
def full_menu_project(tmp_path: Path) -> Path:
    seed_full_menu_optimizer_artifacts(tmp_path)
    return tmp_path


def test_full_menu_at_least_three_optimizers_fair_comparison_ready(
    full_menu_project: Path,
) -> None:
    cfg = fixture_portfolio_config()
    doc = build_candidate_comparison(cfg, project_root=full_menu_project)
    ready = fair_ready_optimizer_ids(doc)
    assert len(ready) >= MINIMUM_FAIR_READY_OPTIMIZERS, (
        f"expected >={MINIMUM_FAIR_READY_OPTIMIZERS} fair-ready optimizers, got {ready}"
    )
    seeded_ids = {spec[0] for spec in FULL_MENU_OPTIMIZER_SEED_SPECS}
    assert seeded_ids.issubset(set(ready))

    for candidate_id in ready:
        row = next(c for c in doc["candidates"] if c["candidate_id"] == candidate_id)
        assert row["status"] == "available"
        readiness = row["construction_disclosure"]["optimization_readiness"]
        assert readiness["schema_version"] == SCHEMA_VERSION
        assert readiness["overall_status"] == "ready"
        assert readiness["gaps"] == []
        snap_fp = row["construction_disclosure"]["optimizer_methodology"]["freshness"][
            "snapshot_config_fingerprint"
        ]
        assert len(str(snap_fp)) == 64


def test_full_menu_snapshot_and_metadata_config_fingerprints_match(
    full_menu_project: Path,
) -> None:
    from src.snapshot import compute_candidate_config_fingerprint

    cfg = fixture_portfolio_config()
    expected_fp = compute_candidate_config_fingerprint(cfg)
    for _cid, folder_name, _build, _export in FULL_MENU_OPTIMIZER_SEED_SPECS:
        folder = full_menu_project / folder_name
        snap = json.loads((folder / "snapshot_10y.json").read_text(encoding="utf-8"))
        meta = json.loads((folder / "baseline_weights_metadata.json").read_text(encoding="utf-8"))
        assert snap["candidate_config_fingerprint"] == expected_fp
        orm = meta["optimizer_run_metadata"]
        fingerprints = orm["input_fingerprints"]
        assert len(str(fingerprints["config_fingerprint"])) == 64
        assert len(str(fingerprints["returns_panel_fingerprint"])) == 64
        assert len(str(fingerprints["universe_fingerprint"])) == 64


def test_full_menu_fair_ready_golden_fingerprint(full_menu_project: Path) -> None:
    assert FULL_MENU_FAIR_READY_GOLDEN_PATH.is_file(), (
        f"Missing golden fixture: {FULL_MENU_FAIR_READY_GOLDEN_PATH}"
    )
    cfg = fixture_portfolio_config()
    live = full_menu_fair_ready_fingerprint(
        build_candidate_comparison(cfg, project_root=full_menu_project)
    )
    golden = json.loads(FULL_MENU_FAIR_READY_GOLDEN_PATH.read_text(encoding="utf-8"))
    assert live == golden
    assert live["fair_ready_count"] >= MINIMUM_FAIR_READY_OPTIMIZERS
