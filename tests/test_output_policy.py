"""Focused tests for site/API output policy and presentation artifact absence."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from mvp_offline_fixtures import (
    MVP_DECISION_PACKAGE_ARTIFACTS,
    load_mvp_config,
    seed_minimal_mvp_workspace,
)
from run_optimization import parse_args as parse_optimization_args
from src.candidate_comparison import write_candidate_comparison_outputs
from src.config_schema import validate_config
from src.output_policy import (
    OUTPUT_PROFILE_FULL_REPORT,
    OUTPUT_PROFILE_LEGACY_EXPORT,
    OUTPUT_PROFILE_SITE_API,
    artifact_counts_by_type,
    normalize_output_profile,
    output_policy_for_profile,
    write_output_manifest,
)


def test_normalize_output_profile_aliases() -> None:
    assert normalize_output_profile(None) == OUTPUT_PROFILE_SITE_API
    assert normalize_output_profile("api") == OUTPUT_PROFILE_SITE_API
    assert normalize_output_profile("json_only") == OUTPUT_PROFILE_SITE_API
    assert normalize_output_profile("full") == OUTPUT_PROFILE_FULL_REPORT
    assert normalize_output_profile("legacy") == OUTPUT_PROFILE_LEGACY_EXPORT


def test_normalize_output_profile_rejects_unknown() -> None:
    with pytest.raises(ValueError, match="Invalid output profile"):
        normalize_output_profile("turbo_export")


def test_full_report_policy_enables_presentation_exports() -> None:
    policy = output_policy_for_profile(OUTPUT_PROFILE_FULL_REPORT)
    assert policy.write_csv is True
    assert policy.write_txt is True
    assert policy.write_html is True
    assert policy.write_png is True
    assert policy.write_pdf is False
    assert policy.write_legacy_comparison is True
    assert "csv" not in policy.disabled_artifact_classes


def test_legacy_export_policy_enables_pdf_and_sidecars() -> None:
    policy = output_policy_for_profile(OUTPUT_PROFILE_LEGACY_EXPORT)
    assert policy.write_pdf is True
    assert policy.write_markdown_sidecars is True
    assert policy.write_css_visual_assets is True


def test_artifact_counts_classifies_markdown_pdf_sidecars(tmp_path: Path) -> None:
    sidecar_dir = tmp_path / "pdf_md_sources"
    sidecar_dir.mkdir()
    (sidecar_dir / "Main portfolio__commentary.md").write_text("# Title\n", encoding="utf-8")
    (tmp_path / "snapshot_10y.json").write_text("{}", encoding="utf-8")
    (tmp_path / "commentary.txt").write_text("txt\n", encoding="utf-8")

    counts = artifact_counts_by_type(tmp_path)
    assert counts["json"] == 1
    assert counts["txt"] == 1
    assert counts["markdown_pdf_sidecars"] == 1


def test_write_output_manifest_records_policy_and_counts(tmp_path: Path) -> None:
    (tmp_path / "candidate_comparison.json").write_text("{}", encoding="utf-8")
    policy = output_policy_for_profile(OUTPUT_PROFILE_SITE_API)
    path = write_output_manifest(
        tmp_path,
        policy=policy,
        run_kind="unit_test",
        generated_paths={"candidate_comparison_json": tmp_path / "candidate_comparison.json"},
    )
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["schema_version"] == "output_manifest_v1"
    assert doc["output_profile"] == OUTPUT_PROFILE_SITE_API
    assert doc["json_is_default_contract"] is True
    assert "txt" in doc["disabled_artifact_classes"]
    assert doc["artifact_counts_by_type"]["json"] == 1
    assert doc["artifact_counts_by_type"]["txt"] == 0


def test_site_api_comparison_pipeline_has_no_presentation_artifacts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def _boom(*_args, **_kwargs):
        raise AssertionError("site_api comparison test must not use live network data")

    import src.data_fred as data_fred
    import src.data_yf as data_yf

    monkeypatch.setattr(data_yf, "download_all", _boom)
    monkeypatch.setattr(data_fred, "fetch_fred_series", _boom, raising=False)

    seed_minimal_mvp_workspace(tmp_path)
    cfg = load_mvp_config(tmp_path)
    paths = write_candidate_comparison_outputs(cfg, project_root=tmp_path, output_profile="site_api")
    out_dir = tmp_path / "Main portfolio"

    for filename, schema_version in MVP_DECISION_PACKAGE_ARTIFACTS:
        doc = json.loads((out_dir / filename).read_text(encoding="utf-8"))
        assert doc.get("schema_version") == schema_version, filename

    assert paths["candidate_comparison_json"].is_file()
    assert "candidate_comparison_txt" not in paths
    assert "portfolio_comparison_json" not in paths
    assert not (out_dir / "candidate_comparison.txt").is_file()
    assert not (out_dir / "decision_package_summary.txt").is_file()

    manifest = json.loads((out_dir / "output_manifest.json").read_text(encoding="utf-8"))
    assert manifest["output_profile"] == OUTPUT_PROFILE_SITE_API
    counts = artifact_counts_by_type(out_dir)
    for key in ("csv", "txt", "html", "png", "pdf", "markdown_pdf_sidecars", "css_visual_assets"):
        assert counts[key] == 0, key
    assert counts["json"] > 0


def test_full_report_comparison_writes_txt_sidecars(tmp_path: Path) -> None:
    main = tmp_path / "Main portfolio"
    main.mkdir()
    eq = tmp_path / "equal-weight portfolio"
    eq.mkdir()
    snap = {"metrics": {"cagr": 0.08, "vol_annual": 0.12, "max_drawdown": -0.2}}
    (main / "snapshot_10y.json").write_text(json.dumps(snap), encoding="utf-8")
    (main / "run_metadata.json").write_text(
        json.dumps({"config_fingerprint": "fp", "weights_source": "generated_policy_portfolio"}),
        encoding="utf-8",
    )
    (eq / "snapshot_10y.json").write_text(json.dumps(snap), encoding="utf-8")

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO"],
        }
    )
    paths = write_candidate_comparison_outputs(
        cfg,
        project_root=tmp_path,
        output_profile=OUTPUT_PROFILE_FULL_REPORT,
    )
    assert paths.get("candidate_comparison_txt", Path()).is_file()
    assert (main / "portfolio_comparison.json").is_file()


def test_run_optimization_skips_report_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["run_optimization.py"])
    args = parse_optimization_args()
    assert args.with_report is False
    assert args.output_profile == OUTPUT_PROFILE_SITE_API


def test_run_optimization_with_report_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["run_optimization.py", "--with-report"])
    args = parse_optimization_args()
    assert args.with_report is True
