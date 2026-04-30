from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

from src.etf_universe import STATUS_FAIL, STATUS_PASS, STATUS_PASS_WITH_WARNINGS
from src.stock_universe import (
    check_config_tickers,
    export_stock_universe,
    list_stock_universe,
    load_stock_universe,
    validate_stock_universe,
)


ROOT = Path(__file__).resolve().parent.parent


def _stock_record() -> dict:
    return {
        "ticker": "AAPL",
        "company_name": "Apple Inc.",
        "asset_class": "equity",
        "sector": "Information Technology",
        "industry": "Technology Hardware, Storage & Peripherals",
        "thematic_tags": [],
        "region": "US",
        "currency_exposure": "USD",
        "main_risk_factor": "equity",
        "secondary_risk_factors": ["us_growth"],
        "risk_role": ["risk_on"],
        "index_membership": ["SP500"],
    }


def _write_yaml(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(records, f, sort_keys=False)


def _write_config(path: Path, tickers: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump({"tickers": tickers}, f, sort_keys=False)


def _case_dir(name: str) -> Path:
    path = ROOT / "tmp" / "stock_universe_tests" / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_valid_stock_record_passes() -> None:
    diag = validate_stock_universe([_stock_record()])
    assert diag["status"] == STATUS_PASS
    assert diag["errors"] == []


def test_missing_required_field_fails() -> None:
    record = _stock_record()
    del record["company_name"]
    diag = validate_stock_universe([record])
    assert diag["status"] == STATUS_FAIL
    assert any(e["code"] == "missing_required_field" for e in diag["errors"])


def test_invalid_asset_class_fails() -> None:
    record = _stock_record()
    record["asset_class"] = "alternative"
    diag = validate_stock_universe([record])
    assert diag["status"] == STATUS_FAIL
    assert any(e["code"] == "invalid_enum" and e["details"]["field"] == "asset_class" for e in diag["errors"])


def test_blank_company_sector_or_industry_fails() -> None:
    record = _stock_record()
    record["industry"] = ""
    diag = validate_stock_universe([record])
    assert diag["status"] == STATUS_FAIL
    assert any(e["details"]["field"] == "industry" for e in diag["errors"])


def test_list_fields_must_be_lists() -> None:
    record = _stock_record()
    record["thematic_tags"] = "ai"
    record["secondary_risk_factors"] = "us_growth"
    record["risk_role"] = "risk_on"
    record["index_membership"] = "SP500"
    diag = validate_stock_universe([record])
    assert diag["status"] == STATUS_FAIL
    bad_fields = {e["details"]["field"] for e in diag["errors"] if e["code"] == "invalid_list"}
    assert {"thematic_tags", "secondary_risk_factors", "risk_role", "index_membership"} <= bad_fields


def test_unknown_config_ticker_warns() -> None:
    diag = check_config_tickers(["AAPL", "UNKNOWN"], [_stock_record()])
    assert diag["status"] == STATUS_PASS_WITH_WARNINGS
    assert diag["unknown_tickers"] == ["UNKNOWN"]


def test_clean_universe_and_config_pass() -> None:
    validation = validate_stock_universe([_stock_record()])
    config_diag = check_config_tickers(["AAPL"], [_stock_record()])
    assert validation["status"] == STATUS_PASS
    assert config_diag["status"] == STATUS_PASS


def test_seed_universe_validates_and_has_expected_size() -> None:
    records = load_stock_universe(ROOT / "config" / "stock_universe.yml")
    diag = validate_stock_universe(records)
    assert diag["status"] == STATUS_PASS
    assert len(records) == 503


def test_seed_header_contains_snapshot_date() -> None:
    text = (ROOT / "config" / "stock_universe.yml").read_text(encoding="utf-8")
    lines = text.splitlines()[:3]
    assert lines[0] == "# snapshot_date: 2026-04-30"
    assert lines[1] == "# snapshot_source: current public S&P 500 constituents list"


def test_export_stock_universe_csv_and_json() -> None:
    records = [_stock_record()]
    tmp_path = _case_dir("export")
    csv_path = export_stock_universe(records, tmp_path / "stock_universe.csv", "csv")
    json_path = export_stock_universe(records, tmp_path / "stock_universe.json", "json")
    assert csv_path.read_text(encoding="utf-8").splitlines()[0].startswith("ticker,company_name,asset_class")
    assert json.loads(json_path.read_text(encoding="utf-8"))[0]["ticker"] == "AAPL"


def test_list_stock_universe_filters_by_sector_industry_and_risk_factor() -> None:
    records = [_stock_record()]
    assert [r["ticker"] for r in list_stock_universe(records, sector="Information Technology")] == ["AAPL"]
    assert [
        r["ticker"]
        for r in list_stock_universe(records, industry="Technology Hardware, Storage & Peripherals")
    ] == ["AAPL"]
    assert [r["ticker"] for r in list_stock_universe(records, risk_factor="us_growth")] == ["AAPL"]


def test_cli_validate_export_and_list() -> None:
    tmp_path = _case_dir("cli")
    universe_path = tmp_path / "universe.yml"
    config_path = tmp_path / "config.yml"
    _write_yaml(universe_path, [_stock_record()])
    _write_config(config_path, ["AAPL"])

    validate = subprocess.run(
        [sys.executable, "run_stock_universe.py", "--universe", str(universe_path), "validate"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert validate.returncode == 0
    assert '"status": "PASS"' in validate.stdout

    out_csv = tmp_path / "export.csv"
    export = subprocess.run(
        [
            sys.executable,
            "run_stock_universe.py",
            "--universe",
            str(universe_path),
            "export",
            "--format",
            "csv",
            "--output",
            str(out_csv),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert export.returncode == 0
    assert out_csv.is_file()

    checked = subprocess.run(
        [
            sys.executable,
            "run_stock_universe.py",
            "--universe",
            str(universe_path),
            "check-config",
            "--config",
            str(config_path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert checked.returncode == 0
    assert '"status": "PASS"' in checked.stdout

    listed = subprocess.run(
        [
            sys.executable,
            "run_stock_universe.py",
            "--universe",
            str(universe_path),
            "list",
            "--sector",
            "Information Technology",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert listed.returncode == 0
    assert "AAPL" in listed.stdout
