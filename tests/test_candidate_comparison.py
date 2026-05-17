from __future__ import annotations

import json
from pathlib import Path

import yaml

from src.candidate_comparison import (
    SCHEMA_VERSION,
    build_candidate_comparison,
    build_legacy_portfolio_comparison,
    candidate_registry_ids,
    write_candidate_comparison_outputs,
)
from src.config_schema import validate_config


def _write_yaml(path: Path, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def _snapshot_10y(
    metrics: dict,
    *,
    rc_asset: list | None = None,
    final_weights_total: dict | None = None,
) -> dict:
    snap = {
        "analysis_end": "2026-04-30",
        "window_label": "10y",
        "metrics": metrics,
        "stress_suite_results": {
            "overall": "PASS",
            "fail_reason_code": None,
            "failed_scenario": None,
            "scenarios": [{"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.05, "pass": True}],
        },
        "constraints_status": {"target_vol": "PASS", "max_dd": "PASS"},
    }
    if rc_asset is not None:
        snap["RC_asset"] = rc_asset
    if final_weights_total is not None:
        snap["final_weights_total"] = final_weights_total
    return snap


def _run_metadata(portfolio_role: str) -> dict:
    return {
        "run_info": {"analysis_end_date": "2026-04-30"},
        "portfolio_valid": True,
        "analysis_setup": {
            "portfolio_input": {"source_analysis_mode": "optimize_from_universe"},
            "analysis_portfolio": {
                "portfolio_role": portfolio_role,
                "weight_source": "optimization_result_released",
                "recommendation_status": "generated_policy_output_released",
            },
        },
    }


def test_registry_length_and_order() -> None:
    ids = candidate_registry_ids()
    assert ids[0] == "policy"
    assert ids[1] == "current"
    assert len(ids) == 18
    assert ids[2:] == sorted(ids[2:])


def test_schema_required_top_level_keys(tmp_path: Path) -> None:
    main = tmp_path / "Main portfolio"
    main.mkdir()
    eq = tmp_path / "equal-weight portfolio"
    eq.mkdir()
    with open(eq / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(_snapshot_10y({"cagr": 0.08, "vol_annual": 0.12, "max_drawdown": -0.2, "sharpe": 0.5}), f)
    with open(main / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(
            _snapshot_10y({"cagr": 0.09, "vol_annual": 0.11, "max_drawdown": -0.15, "sharpe": 0.6}),
            f,
        )
    with open(main / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(_run_metadata("generated_policy_portfolio"), f)

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "tickers": ["VOO", "BND"],
            "output_dir_final": "Main portfolio",
        }
    )
    doc = build_candidate_comparison(cfg, project_root=tmp_path)

    assert doc["schema_version"] == SCHEMA_VERSION
    assert doc["diagnostic_only"] is True
    for key in (
        "generated_at",
        "analysis_end",
        "investor_currency",
        "output_dir_final",
        "analysis_setup_summary",
        "windows",
        "primary_window",
        "candidates",
        "legacy_artifacts",
        "warnings",
    ):
        assert key in doc
    assert len(doc["candidates"]) == 18


def test_unavailable_when_folder_missing(tmp_path: Path) -> None:
    main = tmp_path / "Main portfolio"
    main.mkdir()
    with open(main / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(_snapshot_10y({"cagr": 0.07}), f)
    with open(main / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(_run_metadata("generated_policy_portfolio"), f)

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO"],
        }
    )
    doc = build_candidate_comparison(cfg, project_root=tmp_path)
    rp = next(c for c in doc["candidates"] if c["candidate_id"] == "risk_parity")
    assert rp["status"] == "unavailable"
    assert rp["unavailable_reason"] == "missing_artifact_folder"


def test_degraded_when_only_summary_json(tmp_path: Path) -> None:
    folder = tmp_path / "risk parity portfolio"
    folder.mkdir()
    with open(folder / "summary.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "metrics_10y": {"cagr": 0.055, "vol_annual": 0.1, "max_drawdown": -0.12, "sharpe": 0.4},
                "stress_status": "DIAG_PASS",
                "portfolio_valid": True,
            },
            f,
        )

    cfg = validate_config({"investor_currency": "USD", "tickers": ["VOO"]})
    doc = build_candidate_comparison(cfg, project_root=tmp_path)
    rp = next(c for c in doc["candidates"] if c["candidate_id"] == "risk_parity")
    assert rp["status"] == "degraded"
    assert rp["metrics"]["10y"]["cagr"] == 0.055


def test_passthrough_metrics_from_snapshot(tmp_path: Path) -> None:
    folder = tmp_path / "equal-weight portfolio"
    folder.mkdir()
    metrics = {
        "cagr": 0.123456,
        "vol_annual": 0.098765,
        "max_drawdown": -0.111111,
        "sharpe": 0.555555,
        "sortino": 0.777777,
        "beta_portfolio": 0.333333,
    }
    with open(folder / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(_snapshot_10y(metrics), f)

    cfg = validate_config({"investor_currency": "USD", "tickers": ["VOO"]})
    doc = build_candidate_comparison(cfg, project_root=tmp_path)
    eq = next(c for c in doc["candidates"] if c["candidate_id"] == "equal_weight")
    m = eq["metrics"]["10y"]
    assert m["cagr"] == 0.123
    assert m["sharpe"] == 0.556
    assert m["beta_portfolio"] == 0.333


def test_current_unavailable_in_optimize_mode(tmp_path: Path) -> None:
    main = tmp_path / "Main portfolio"
    main.mkdir()
    with open(main / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(_snapshot_10y({"cagr": 0.07}), f)
    with open(main / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(_run_metadata("generated_policy_portfolio"), f)

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "current_weights": {"VOO": 0.6, "BND": 0.4},
            "tickers": ["VOO", "BND"],
        }
    )
    doc = build_candidate_comparison(cfg, project_root=tmp_path)
    cur = next(c for c in doc["candidates"] if c["candidate_id"] == "current")
    assert cur["status"] == "unavailable"
    assert cur["unavailable_reason"] == "missing_current_report"


def test_current_available_in_analyze_current_mode(tmp_path: Path) -> None:
    main = tmp_path / "Main portfolio"
    main.mkdir()
    rc = [{"ticker": "VOO", "rc_pct": 0.6}, {"ticker": "BND", "rc_pct": 0.4}]
    with open(main / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(
            _snapshot_10y(
                {"cagr": 0.065, "vol_annual": 0.09},
                rc_asset=rc,
                final_weights_total={"VOO": 0.6, "BND": 0.4},
            ),
            f,
        )
    with open(main / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(_run_metadata("user_current_portfolio"), f)

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "analyze_current_weights",
            "output_dir_final": "Main portfolio",
            "current_weights": {"VOO": 0.6, "BND": 0.4},
            "tickers": ["VOO", "BND"],
        }
    )
    doc = build_candidate_comparison(cfg, project_root=tmp_path)
    cur = next(c for c in doc["candidates"] if c["candidate_id"] == "current")
    pol = next(c for c in doc["candidates"] if c["candidate_id"] == "policy")
    assert cur["status"] == "available"
    assert pol["status"] == "degraded"
    assert "stale_policy_snapshot" in pol["warnings"]


def test_weight_concentration_from_final_weights(tmp_path: Path) -> None:
    folder = tmp_path / "equal-weight portfolio"
    folder.mkdir()
    weights = {"VOO": 0.35, "BND": 0.25, "GLD": 0.15, "TLT": 0.25}
    with open(folder / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(
            _snapshot_10y({"cagr": 0.08, "vol_annual": 0.12}, final_weights_total=weights),
            f,
        )

    cfg = validate_config({"investor_currency": "USD", "tickers": ["VOO"]})
    doc = build_candidate_comparison(cfg, project_root=tmp_path)
    eq = next(c for c in doc["candidates"] if c["candidate_id"] == "equal_weight")
    wc = eq["weight_concentration"]
    assert wc["top1_weight_asset"] == "VOO"
    assert wc["top1_weight_pct"] == 0.35
    assert wc["top3_weight_sum_pct"] == 0.85
    assert wc["source"] == "snapshot_10y.final_weights_total"


def test_diversification_from_rc_asset(tmp_path: Path) -> None:
    folder = tmp_path / "equal-weight portfolio"
    folder.mkdir()
    rc = [
        {"ticker": "VOO", "rc_pct": 0.35},
        {"ticker": "BND", "rc_pct": 0.25},
        {"ticker": "GLD", "rc_pct": 0.15},
    ]
    with open(folder / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(_snapshot_10y({"cagr": 0.08, "vol_annual": 0.12}, rc_asset=rc), f)

    cfg = validate_config({"investor_currency": "USD", "tickers": ["VOO"]})
    doc = build_candidate_comparison(cfg, project_root=tmp_path)
    eq = next(c for c in doc["candidates"] if c["candidate_id"] == "equal_weight")
    div = eq["diversification"]
    assert div["top1_rc_asset"] == "VOO"
    assert div["top1_rc_pct"] == 0.35
    assert div["top3_rc_sum_pct"] == 0.75
    assert div["source_window"] == "10y"


def test_write_outputs_and_legacy_subset(tmp_path: Path) -> None:
    main = tmp_path / "Main portfolio"
    main.mkdir()
    eq = tmp_path / "equal-weight portfolio"
    eq.mkdir()
    with open(main / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(_snapshot_10y({"cagr": 0.09, "vol_annual": 0.11}), f)
    with open(main / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(_run_metadata("generated_policy_portfolio"), f)
    with open(eq / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(_snapshot_10y({"cagr": 0.08, "vol_annual": 0.12}), f)

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO"],
        }
    )
    paths = write_candidate_comparison_outputs(cfg, project_root=tmp_path)
    assert paths["candidate_comparison_json"].is_file()
    assert paths.get("portfolio_health_score_json", Path()).is_file()
    assert paths.get("robustness_scorecard_json", Path()).is_file()
    with open(paths["candidate_comparison_json"], encoding="utf-8") as f:
        doc = json.load(f)
    legacy = build_legacy_portfolio_comparison(doc)
    assert set(legacy.keys()) == {"policy", "equal_weight", "risk_parity", "robust_scenario"}
    assert legacy["equal_weight"]["metrics"]["cagr"] == 0.08
