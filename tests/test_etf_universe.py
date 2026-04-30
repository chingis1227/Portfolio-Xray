from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

from src.etf_universe import (
    STATUS_FAIL,
    STATUS_PASS,
    STATUS_PASS_WITH_WARNINGS,
    check_config_tickers,
    export_universe,
    list_universe,
    load_etf_universe,
    validate_etf_universe,
)


ROOT = Path(__file__).resolve().parent.parent


def _smh_record() -> dict:
    return {
        "ticker": "SMH",
        "name": "VanEck Semiconductor ETF",
        "issuer": "VanEck",
        "asset_class": "equity",
        "subtype": "thematic_etf",
        "sector": "technology",
        "thematic_primary": "semiconductors",
        "thematic_tags": ["AI", "data_centers", "chips", "hardware_cycle"],
        "risk_role": ["risk_on", "growth", "cyclical"],
        "main_risk_factor": "equity",
        "secondary_risk_factors": ["us_growth", "real_rates"],
        "region": "Global",
        "currency_exposure": "mixed",
        "duration_bucket": "none",
        "credit_quality": "none",
        "duplicate_group_id": "semiconductors",
        "canonical_ticker": "SMH",
        "data_source": ["manual_seed", "issuer", "yahoo", "inferred"],
        "notes": "Semiconductor cycle and AI capex exposure.",
    }


def _tlt_record() -> dict:
    return {
        "ticker": "TLT",
        "name": "iShares 20 Plus Year Treasury Bond ETF",
        "issuer": "iShares",
        "asset_class": "fixed_income",
        "subtype": "treasury",
        "sector": "none",
        "thematic_primary": "none",
        "thematic_tags": [],
        "risk_role": ["duration", "defensive"],
        "main_risk_factor": "real_rates",
        "secondary_risk_factors": [],
        "region": "US",
        "currency_exposure": "USD",
        "duration_bucket": "long",
        "credit_quality": "Treasury",
        "duplicate_group_id": "us_treasury_long",
        "canonical_ticker": "TLT",
        "data_source": ["manual_seed"],
        "notes": "Long US Treasury duration exposure.",
    }


def _write_yaml(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(records, f, sort_keys=False)


def _case_dir(name: str) -> Path:
    path = ROOT / "tmp" / "etf_universe_tests" / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_valid_smh_record_passes() -> None:
    diag = validate_etf_universe([_smh_record()])
    assert diag["status"] == STATUS_PASS
    assert diag["errors"] == []


def test_missing_required_field_fails() -> None:
    record = _smh_record()
    del record["data_source"]
    diag = validate_etf_universe([record])
    assert diag["status"] == STATUS_FAIL
    assert any(e["code"] == "missing_required_field" for e in diag["errors"])


def test_forbidden_optimizer_fields_fail() -> None:
    record = _smh_record()
    record["optimization_rule"] = "allow"
    record["eligibility_bucket"] = "core"
    diag = validate_etf_universe([record])
    assert diag["status"] == STATUS_FAIL
    assert {e["details"]["field"] for e in diag["errors"] if e["code"] == "forbidden_field"} == {
        "optimization_rule",
        "eligibility_bucket",
    }


def test_invalid_enum_fails() -> None:
    record = _smh_record()
    record["asset_class"] = "equities"
    diag = validate_etf_universe([record])
    assert diag["status"] == STATUS_FAIL
    assert any(e["code"] == "invalid_enum" and e["details"]["field"] == "asset_class" for e in diag["errors"])


def test_data_source_is_required_and_validated() -> None:
    record = _smh_record()
    record["data_source"] = ["manual_seed", "vendor_x"]
    diag = validate_etf_universe([record])
    assert diag["status"] == STATUS_FAIL
    assert any(e["code"] == "invalid_enum" and e["details"]["field"] == "data_source" for e in diag["errors"])


def test_missing_canonical_ticker_fails() -> None:
    record = _smh_record()
    record["ticker"] = "SOXX"
    record["canonical_ticker"] = "SMH"
    diag = validate_etf_universe([record])
    assert diag["status"] == STATUS_FAIL
    assert any(e["code"] == "broken_canonical_reference" for e in diag["errors"])


def test_fixed_income_requires_duration_and_credit() -> None:
    record = _tlt_record()
    record["duration_bucket"] = "none"
    diag = validate_etf_universe([record])
    assert diag["status"] == STATUS_FAIL
    assert any(e["code"] == "fixed_income_fields_missing" for e in diag["errors"])


def test_non_fixed_income_bond_fields_fail_without_hybrid_exception() -> None:
    record = _smh_record()
    record["duration_bucket"] = "long"
    record["credit_quality"] = "Mixed"
    diag = validate_etf_universe([record])
    assert diag["status"] == STATUS_FAIL
    assert any(e["code"] == "non_fixed_income_fields_present" for e in diag["errors"])


def test_hybrid_exception_requires_flag_and_notes() -> None:
    record = _smh_record()
    record["asset_class"] = "alternative"
    record["subtype"] = "multi_asset"
    record["sector"] = "multi_sector"
    record["duration_bucket"] = "long"
    record["credit_quality"] = "Mixed"
    record["hybrid_fixed_income_fields_allowed"] = True
    record["notes"] = "Explicit hybrid allocation with bond sleeve."
    diag = validate_etf_universe([record])
    assert diag["status"] == STATUS_PASS


def test_duplicate_group_in_config_warns() -> None:
    smh = _smh_record()
    soxx = dict(smh, ticker="SOXX", canonical_ticker="SMH")
    records = [smh, soxx]
    assert validate_etf_universe(records)["status"] == STATUS_PASS
    diag = check_config_tickers(["SMH", "SOXX"], records)
    assert diag["status"] == STATUS_PASS_WITH_WARNINGS
    assert "semiconductors" in diag["duplicate_groups_in_config"]


def test_unknown_config_ticker_warns_but_does_not_fail() -> None:
    diag = check_config_tickers(["SMH", "UNKNOWN"], [_smh_record()])
    assert diag["status"] == STATUS_PASS_WITH_WARNINGS
    assert diag["unknown_tickers"] == ["UNKNOWN"]


def test_clean_universe_and_config_pass() -> None:
    validation = validate_etf_universe([_smh_record(), _tlt_record()])
    config_diag = check_config_tickers(["SMH", "TLT"], [_smh_record(), _tlt_record()])
    assert validation["status"] == STATUS_PASS
    assert config_diag["status"] == STATUS_PASS


def test_seed_universe_validates_and_has_target_size() -> None:
    records = load_etf_universe(ROOT / "config" / "etf_universe.yml")
    diag = validate_etf_universe(records)
    assert diag["status"] == STATUS_PASS
    assert 150 <= len(records) <= 250


def test_export_universe_csv_and_json() -> None:
    records = [_smh_record(), _tlt_record()]
    tmp_path = _case_dir("export")
    csv_path = export_universe(records, tmp_path / "etf_universe.csv", "csv")
    json_path = export_universe(records, tmp_path / "etf_universe.json", "json")
    assert csv_path.read_text(encoding="utf-8").splitlines()[0].startswith("ticker,name,issuer")
    assert json.loads(json_path.read_text(encoding="utf-8"))[0]["ticker"] == "SMH"


def test_list_universe_filters_by_asset_class_and_risk_factor() -> None:
    records = [_smh_record(), _tlt_record()]
    assert [r["ticker"] for r in list_universe(records, asset_class="equity")] == ["SMH"]
    assert [r["ticker"] for r in list_universe(records, risk_factor="real_rates")] == ["SMH", "TLT"]


def test_cli_validate_export_and_list() -> None:
    tmp_path = _case_dir("cli")
    universe_path = tmp_path / "universe.yml"
    _write_yaml(universe_path, [_smh_record(), _tlt_record()])

    validate = subprocess.run(
        [sys.executable, "run_etf_universe.py", "--universe", str(universe_path), "validate"],
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
            "run_etf_universe.py",
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

    listed = subprocess.run(
        [
            sys.executable,
            "run_etf_universe.py",
            "--universe",
            str(universe_path),
            "list",
            "--risk-factor",
            "real_rates",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert listed.returncode == 0
    assert "SMH" in listed.stdout
    assert "TLT" in listed.stdout
