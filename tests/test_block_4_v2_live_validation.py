"""Block 4 v3 Session 12 — live validation script and E2E v2 gate."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.core_mvp_validation_contract import (
    check_block_4_v3_diagnosis_handoff,
    check_candidate_launchpad_v3,
    check_problem_classification_v3,
)
from scripts.validate_block_4_live import validate_block_4_live
from src.config_schema import validate_config
from src.live_core_e2e import (
    LIVE_CORE_E2E_PROFILE_DIAGNOSIS_ONLY,
    detect_live_core_e2e_profile,
    validate_live_core_artifacts,
)
from src.product_bundle_hygiene import apply_diagnosis_only_product_bundle_hygiene
from mvp_offline_fixtures import (
    DEFAULT_ANALYSIS_END,
    five_ticker_mvp_config_dict,
    seed_analysis_subject_diagnosis_bundle,
    seed_blocks_1_5_mvp_smoke_workspace,
)


def test_validate_block_4_live_accepts_v2_seed_bundle(tmp_path: Path) -> None:
    cfg = validate_config(five_ticker_mvp_config_dict())
    main = tmp_path / cfg.output_dir_final
    subject = main / "analysis_subject"
    seed_blocks_1_5_mvp_smoke_workspace(tmp_path, cfg)
    seed_analysis_subject_diagnosis_bundle(subject)

    result = validate_block_4_live(subject)
    assert result["ok"] is True
    pc = json.loads((subject / "problem_classification.json").read_text(encoding="utf-8"))
    lp = json.loads((subject / "candidate_launchpad.json").read_text(encoding="utf-8"))
    assert pc["schema_version"] == "problem_classification_v3"
    assert lp["schema_version"] == "candidate_launchpad_v3"
    assert check_problem_classification_v3(pc)["product_contract_ok"] is True
    assert check_candidate_launchpad_v3(lp)["product_contract_ok"] is True
    assert check_block_4_v3_diagnosis_handoff(pc, lp)["handoff_ok"] is True


def test_validate_block_4_live_cli_refresh_diagnosis(tmp_path: Path) -> None:
    cfg = validate_config(five_ticker_mvp_config_dict())
    main = tmp_path / cfg.output_dir_final
    subject = main / "analysis_subject"
    seed_blocks_1_5_mvp_smoke_workspace(tmp_path, cfg)
    (subject / "problem_classification.json").unlink(missing_ok=True)
    (subject / "candidate_launchpad.json").unlink(missing_ok=True)

    repo_root = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "validate_block_4_live.py"),
            "--subject-dir",
            str(subject),
            "--refresh-diagnosis",
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert (subject / "problem_classification.json").is_file()
    assert (subject / "candidate_launchpad.json").is_file()


def test_live_e2e_diagnosis_only_uses_block_4_v3_contract(tmp_path: Path) -> None:
    cfg = validate_config(five_ticker_mvp_config_dict())
    main = tmp_path / cfg.output_dir_final
    subject = main / "analysis_subject"
    seed_blocks_1_5_mvp_smoke_workspace(tmp_path, cfg)
    seed_analysis_subject_diagnosis_bundle(subject)
    apply_diagnosis_only_product_bundle_hygiene(
        main,
        analysis_end=DEFAULT_ANALYSIS_END,
        investor_currency="USD",
    )

    assert detect_live_core_e2e_profile(main) == LIVE_CORE_E2E_PROFILE_DIAGNOSIS_ONLY
    result = validate_live_core_artifacts(main)
    assert result.ok, "\n".join(result.messages())
    assert result.evidence.get("block_4_schema_version") == "problem_classification_v3"
    assert result.evidence.get("block_4_primary_problem_id")
    assert result.evidence.get("block_4_n_cards", 0) >= 0
