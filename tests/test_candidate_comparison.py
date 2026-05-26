from __future__ import annotations

import json
from pathlib import Path

import yaml

from src.candidate_comparison import (
    COMPARISON_REBUILD_FACTORY_THEN_COMPARE,
    COMPARISON_REBUILD_STANDALONE,
    SCHEMA_VERSION,
    build_candidate_comparison,
    build_candidate_menu,
    build_candidate_menu_warnings,
    build_legacy_portfolio_comparison,
    candidate_registry_ids,
    product_candidate_ids_from_factory_run,
    scoped_product_comparison,
    write_candidate_comparison_outputs,
    write_candidate_comparison_txt,
)
from src.config_schema import validate_config
from src.snapshot import compute_candidate_config_fingerprint


def _write_yaml(path: Path, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def _snapshot_10y(
    metrics: dict,
    *,
    rc_asset: list | None = None,
    final_weights_total: dict | None = None,
    cfg: object | None = None,
    analysis_end: str = "2026-04-30",
) -> dict:
    snap = {
        "analysis_end": analysis_end,
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
    if cfg is not None:
        snap["candidate_config_fingerprint"] = compute_candidate_config_fingerprint(cfg)
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
    assert ids[0] == "analysis_subject"
    assert ids[1] == "policy"
    assert ids[2] == "current"
    assert len(ids) == 19
    assert ids[3:] == sorted(ids[3:])


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
    assert doc["comparison_baseline_candidate_id"] == "analysis_subject"
    assert len(doc["candidates"]) == 19
    assert doc["candidate_menu"]["factory_evidence_status"] == "missing"
    assert doc["candidate_menu"]["factory_steps_used"] is False
    assert "factory_summary_missing" in doc["warnings"]


def test_analysis_subject_row_reads_canonical_sidecar(tmp_path: Path) -> None:
    main = tmp_path / "Main portfolio"
    subject = main / "analysis_subject"
    subject.mkdir(parents=True)
    with open(subject / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(
            _snapshot_10y(
                {"cagr": 0.071, "vol_annual": 0.10, "max_drawdown": -0.18},
                final_weights_total={"VOO": 0.6, "BND": 0.4},
            ),
            f,
        )
    with open(subject / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "analysis_setup": {
                    "analysis_subject": {
                        "id": "starter",
                        "type": "model_portfolio",
                        "display_name": "Starter model",
                        "weight_source": "config.analysis_subject.weights",
                    },
                    "analysis_portfolio": {
                        "portfolio_role": "model_portfolio",
                        "recommendation_status": "diagnostic_model_portfolio_not_recommendation",
                    },
                }
            },
            f,
        )

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
            "analysis_subject": {
                "type": "model_portfolio",
                "weights": {"VOO": 0.6, "BND": 0.4},
            },
        }
    )
    doc = build_candidate_comparison(cfg, project_root=tmp_path)

    row = next(c for c in doc["candidates"] if c["candidate_id"] == "analysis_subject")
    assert row["status"] == "degraded"
    assert row["display_name"] == "Starter model"
    assert row["artifact_root"] == "Main portfolio/analysis_subject"
    assert row["portfolio_role"] == "model_portfolio"
    assert doc["analysis_end"] == "2026-04-30"


def test_comparison_warns_when_review_analysis_end_unknown(tmp_path: Path) -> None:
    eq = tmp_path / "equal-weight portfolio"
    eq.mkdir()
    with open(eq / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(_snapshot_10y({"cagr": 0.08, "vol_annual": 0.12}), f)

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    doc = build_candidate_comparison(cfg, project_root=tmp_path)

    assert doc["analysis_end"] == ""
    eq_row = next(c for c in doc["candidates"] if c["candidate_id"] == "equal_weight")
    assert eq_row["status"] in ("available", "degraded")
    assert (
        "candidate_freshness_unchecked_no_review_analysis_end:equal_weight"
        in eq_row["warnings"]
    )


def test_stale_candidate_snapshot_marked_unavailable(tmp_path: Path) -> None:
    main = tmp_path / "Main portfolio"
    subject = main / "analysis_subject"
    subject.mkdir(parents=True)
    subject_snapshot = _snapshot_10y({"cagr": 0.06, "vol_annual": 0.1})
    subject_snapshot["analysis_end"] = "2026-05-15"
    with open(subject / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(subject_snapshot, f)
    with open(subject / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(_run_metadata("user_current_portfolio"), f)

    eq = tmp_path / "equal-weight portfolio"
    eq.mkdir()
    with open(eq / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(_snapshot_10y({"cagr": 0.08, "vol_annual": 0.12}), f)

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    doc = build_candidate_comparison(cfg, project_root=tmp_path)

    assert doc["analysis_end"] == "2026-05-15"
    eq_row = next(c for c in doc["candidates"] if c["candidate_id"] == "equal_weight")
    assert eq_row["status"] == "unavailable"
    assert eq_row["unavailable_reason"] == "stale_snapshot_analysis_end"
    assert "stale_snapshot_analysis_end:2026-04-30!=2026-05-15" in eq_row["warnings"]


def test_stale_config_fingerprint_marked_unavailable(tmp_path: Path) -> None:
    main = tmp_path / "Main portfolio"
    subject = main / "analysis_subject"
    subject.mkdir(parents=True)
    subject_snapshot = _snapshot_10y({"cagr": 0.06, "vol_annual": 0.1})
    subject_snapshot["analysis_end"] = "2026-05-15"
    with open(subject / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(subject_snapshot, f)
    with open(subject / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(_run_metadata("user_current_portfolio"), f)

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    fp = compute_candidate_config_fingerprint(cfg)

    eq = tmp_path / "equal-weight portfolio"
    eq.mkdir()
    eq_snap = _snapshot_10y({"cagr": 0.08, "vol_annual": 0.12})
    eq_snap["analysis_end"] = "2026-05-15"
    eq_snap["candidate_config_fingerprint"] = "deadbeef" * 8
    with open(eq / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(eq_snap, f)

    doc = build_candidate_comparison(cfg, project_root=tmp_path)

    assert doc["config_fingerprint"] == fp
    eq_row = next(c for c in doc["candidates"] if c["candidate_id"] == "equal_weight")
    assert eq_row["status"] == "unavailable"
    assert eq_row["unavailable_reason"] == "stale_config_fingerprint"
    assert any(w.startswith("stale_config_fingerprint:") for w in eq_row["warnings"])


def test_analysis_setup_summary_prefers_analysis_subject_sidecar_metadata(
    tmp_path: Path,
) -> None:
    main = tmp_path / "Main portfolio"
    subject = main / "analysis_subject"
    subject.mkdir(parents=True)
    with open(main / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "analysis_setup": {
                    "portfolio_input": {"source_analysis_mode": "optimize_from_universe"},
                    "analysis_subject": {
                        "id": "legacy_root",
                        "type": "universe_baseline",
                        "display_name": "Universe Baseline",
                        "weight_source": "system.equal_weight_initial_baseline",
                    },
                    "analysis_portfolio": {
                        "portfolio_role": "equal_weight_initial_baseline",
                        "weight_source": "system.equal_weight_initial_baseline",
                        "recommendation_status": "baseline_not_recommendation",
                    },
                }
            },
            f,
        )
    with open(subject / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(
            _snapshot_10y(
                {"cagr": 0.061, "vol_annual": 0.11, "max_drawdown": -0.19},
                final_weights_total={"VOO": 0.55, "BND": 0.35, "GLD": 0.10},
            ),
            f,
        )
    with open(subject / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "analysis_setup": {
                    "portfolio_input": {"source_analysis_mode": "optimize_from_universe"},
                    "analysis_subject": {
                        "id": "client_current",
                        "type": "current_portfolio",
                        "display_name": "Client current portfolio",
                        "weight_source": "config.analysis_subject.weights",
                        "resolution_source": "config.analysis_subject",
                    },
                    "analysis_portfolio": {
                        "portfolio_role": "user_current_portfolio",
                        "weight_source": "config.analysis_subject.weights",
                        "recommendation_status": "diagnostic_current_portfolio_not_recommendation",
                    },
                }
            },
            f,
        )

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND", "GLD"],
            "analysis_subject": {
                "id": "client_current",
                "type": "current_portfolio",
                "display_name": "Client current portfolio",
                "weights": {"VOO": 0.55, "BND": 0.35, "GLD": 0.10},
            },
        }
    )
    doc = build_candidate_comparison(cfg, project_root=tmp_path)

    summary = doc["analysis_setup_summary"]
    assert summary["analysis_subject_id"] == "client_current"
    assert summary["analysis_subject_type"] == "current_portfolio"
    assert summary["analysis_subject_display_name"] == "Client current portfolio"
    assert summary["portfolio_role"] == "user_current_portfolio"
    bundle = doc["review_bundle_context"]
    assert bundle["version"] == "review_bundle_context_v1"
    assert bundle["review_bundle_fingerprint"]
    assert bundle["mode_subject_consistency"]["is_consistent"] is True
    assert bundle["mode_subject_consistency"]["informational_notices"]
    assert not any(
        w.startswith("review_bundle_mode_subject:") for w in doc.get("warnings", [])
    )


def test_policy_row_is_legacy_only_when_analysis_subject_exists(tmp_path: Path) -> None:
    main = tmp_path / "Main portfolio"
    subject = main / "analysis_subject"
    subject.mkdir(parents=True)
    with open(main / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(
            _snapshot_10y(
                {"cagr": 0.09, "vol_annual": 0.11},
                final_weights_total={"VOO": 0.7, "BND": 0.3},
            ),
            f,
        )
    with open(main / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(_run_metadata("generated_policy_portfolio"), f)
    with open(subject / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(
            _snapshot_10y(
                {"cagr": 0.06, "vol_annual": 0.12},
                final_weights_total={"VOO": 0.55, "BND": 0.45},
            ),
            f,
        )
    with open(subject / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "analysis_setup": {
                    "analysis_subject": {"type": "current_portfolio"},
                    "analysis_portfolio": {"portfolio_role": "user_current_portfolio"},
                }
            },
            f,
        )

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "analysis_mode": "optimize_from_universe",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
            "analysis_subject": {
                "type": "current_portfolio",
                "weights": {"VOO": 0.55, "BND": 0.45},
            },
        }
    )
    doc = build_candidate_comparison(cfg, project_root=tmp_path)

    subject_row = next(c for c in doc["candidates"] if c["candidate_id"] == "analysis_subject")
    policy_row = next(c for c in doc["candidates"] if c["candidate_id"] == "policy")
    assert subject_row["status"] in ("available", "degraded")
    assert policy_row["status"] == "unavailable"
    assert policy_row["unavailable_reason"] == "legacy_policy_not_default_portfolio_first_candidate"
    assert "legacy_policy_reference_optional_portfolio_first" in policy_row["warnings"]


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
    assert paths.get("tradeoff_explanation_json", Path()).is_file()
    assert paths.get("assumption_sensitivity_json", Path()).is_file()
    assert paths.get("pareto_dominance_json", Path()).is_file()
    assert paths.get("regret_analysis_json", Path()).is_file()
    assert paths.get("model_risk_diagnostics_json", Path()).is_file()
    with open(paths["candidate_comparison_json"], encoding="utf-8") as f:
        doc = json.load(f)
    legacy = build_legacy_portfolio_comparison(doc)
    assert set(legacy.keys()) == {"policy", "equal_weight", "risk_parity", "robust_scenario"}
    assert legacy["equal_weight"]["metrics"]["cagr"] == 0.08


def test_product_candidate_ids_from_explicit_factory_run() -> None:
    ids = product_candidate_ids_from_factory_run(
        {
            "factory_profile_id": "explicit_list",
            "steps": [
                {"candidate_id": "equal_weight"},
                {"candidate_id": "risk_parity"},
                {"candidate_id": "equal_weight"},
            ],
        }
    )

    assert ids == ("equal_weight", "risk_parity")


def test_product_candidate_ids_ignores_batch_factory_run() -> None:
    assert (
        product_candidate_ids_from_factory_run(
            {
                "factory_profile_id": "core_fast",
                "steps": [{"candidate_id": "equal_weight"}],
            }
        )
        == ()
    )


def test_scoped_product_comparison_filters_unselected_candidates() -> None:
    comparison = {
        "comparison_baseline_candidate_id": "analysis_subject",
        "warnings": [],
        "candidates": [
            {"candidate_id": "analysis_subject", "status": "available"},
            {"candidate_id": "equal_weight", "status": "available"},
            {"candidate_id": "risk_parity", "status": "available"},
        ],
    }

    scoped = scoped_product_comparison(comparison, ["equal_weight"])

    assert [row["candidate_id"] for row in scoped["candidates"]] == [
        "analysis_subject",
        "equal_weight",
    ]
    assert scoped["product_candidate_scope"]["candidate_ids"] == ["equal_weight"]
    assert "product_scope_explicit_candidates" in scoped["warnings"]


def test_write_outputs_scopes_product_adapters_to_explicit_factory_candidate(tmp_path: Path) -> None:
    main = tmp_path / "Main portfolio"
    subject = main / "analysis_subject"
    subject.mkdir(parents=True)
    with open(subject / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(
            _snapshot_10y({"cagr": 0.07, "vol_annual": 0.12, "max_drawdown": -0.2}),
            f,
        )
    with open(subject / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(_run_metadata("user_current_portfolio"), f)

    eq = tmp_path / "equal-weight portfolio"
    eq.mkdir()
    with open(eq / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(
            _snapshot_10y({"cagr": 0.075, "vol_annual": 0.10, "max_drawdown": -0.16}),
            f,
        )
    rp = tmp_path / "risk-parity portfolio"
    rp.mkdir()
    with open(rp / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(
            _snapshot_10y({"cagr": 0.09, "vol_annual": 0.08, "max_drawdown": -0.10}),
            f,
        )

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO"],
            "analysis_subject": {"type": "current_portfolio", "weights": {"VOO": 1.0}},
        }
    )
    factory_run = {
        "factory_profile_id": "explicit_list",
        "generated_at": "2026-05-26T10:00:00+00:00",
        "steps": [{"candidate_id": "equal_weight", "execution_action": "succeeded"}],
    }

    paths = write_candidate_comparison_outputs(
        cfg,
        project_root=tmp_path,
        factory_run=factory_run,
        write_txt=False,
    )

    with open(paths["candidate_comparison_json"], encoding="utf-8") as f:
        comparison = json.load(f)
    with open(paths["current_vs_candidate_json"], encoding="utf-8") as f:
        current_vs_candidate = json.load(f)
    with open(paths["decision_verdict_json"], encoding="utf-8") as f:
        decision_verdict = json.load(f)

    assert comparison["product_candidate_scope"]["candidate_ids"] == ["equal_weight"]
    assert any(row["candidate_id"] == "risk_parity" for row in comparison["candidates"])
    assert current_vs_candidate["selected_candidate_ids"] == ["equal_weight"]
    assert decision_verdict["selected_candidate_id"] == "equal_weight"
    assert decision_verdict["source_artifacts"]["selection_decision"] is None
    assert "selection_decision_json" not in paths
    assert "portfolio_health_score_json" not in paths
    assert "robustness_scorecard_json" not in paths
    assert "action_plan_json" not in paths
    assert "decision_journal_json" not in paths
    assert "monitoring_diff_json" not in paths
    with open(paths["output_manifest_json"], encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["advanced_package_generated"] is False
    by_category = manifest.get("generated_paths_by_category") or {}
    assert "portfolio_health_score_json" not in by_category.get("advanced_evidence", {})
    discovery = manifest.get("product_discovery") or {}
    assert discovery.get("product_bundle_paths", {}).get("current_vs_candidate_json")
    assert discovery.get("product_bundle_paths", {}).get("decision_verdict_json")


def test_build_candidate_menu_flags_reduced_core_scope() -> None:
    candidates = [
        {"candidate_id": "equal_weight", "status": "available"},
        {"candidate_id": "risk_parity", "status": "available"},
        {"candidate_id": "minimum_variance", "status": "unavailable", "unavailable_reason": "missing_artifact_folder"},
    ]
    menu = build_candidate_menu(
        candidates,
        factory_run={"factory_profile_id": "core_v1"},
        review_mode="core",
    )
    assert menu["intended_menu_profile_id"] == "core_v1"
    assert menu["product_menu_profile_id"] == "default_v1"
    assert menu["is_reduced_vs_product_menu"] is True
    assert menu["is_partial_menu"] is True
    assert menu["partial_menu_reason"] in (
        "reduced_menu_scope_vs_product_default_v1",
        "reduced_menu_scope_and_unavailable_intended_candidates",
    )


def test_build_candidate_menu_flags_incomplete_intended_menu() -> None:
    from src.candidate_factory import CORE_V1_CANDIDATE_ORDER

    candidates = [
        {"candidate_id": cid, "status": "available"}
        for cid in CORE_V1_CANDIDATE_ORDER[:2]
    ] + [
        {
            "candidate_id": CORE_V1_CANDIDATE_ORDER[2],
            "status": "unavailable",
            "unavailable_reason": "stale_snapshot_analysis_end",
        }
    ]
    menu = build_candidate_menu(
        candidates,
        factory_run={"factory_profile_id": "core_v1"},
    )
    assert menu["is_incomplete_intended_menu"] is True
    assert menu["is_partial_menu"] is True
    assert menu["unavailable_reasons_summary"]["stale_snapshot_analysis_end"] == 1


def test_comparison_includes_candidate_menu_and_warnings(tmp_path: Path) -> None:
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
    with open(main / "candidate_factory_run.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "factory_profile_id": "core_v1",
                "generated_at": "2026-05-21T10:00:00+00:00",
            },
            f,
        )

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO"],
        }
    )
    doc = build_candidate_comparison(cfg, project_root=tmp_path)
    assert "candidate_menu" in doc
    assert doc["candidate_menu"]["intended_menu_profile_id"] == "core_v1"
    warnings = build_candidate_menu_warnings(doc["candidate_menu"])
    assert any("reduced menu" in w.lower() for w in warnings)
    assert any(w in doc["warnings"] for w in warnings)

    txt_path = tmp_path / "candidate_comparison.txt"
    write_candidate_comparison_txt(doc, txt_path)
    text = txt_path.read_text(encoding="utf-8")
    assert "Partial menu" in text or "Menu:" in text


def test_decision_package_summary_mentions_partial_menu() -> None:
    from src.decision_package_reporting import build_decision_package_summary_lines

    comparison = {
        "analysis_end": "2026-04-30",
        "investor_currency": "USD",
        "candidate_menu": build_candidate_menu(
            [{"candidate_id": "equal_weight", "status": "available"}],
            factory_run={"factory_profile_id": "core_v1"},
        ),
        "candidates": [],
    }
    lines = build_decision_package_summary_lines(
        comparison=comparison,
        health=None,
        robustness=None,
        selection=None,
        action=None,
        monitoring_diff=None,
        decision_journal=None,
    )
    joined = "\n".join(lines)
    assert "Candidate menu" in joined
    assert "core_v1" in joined
    assert "Partial menu" in joined


def test_equal_weight_construction_disclosure_passthrough_baseline_metadata(
    tmp_path: Path,
) -> None:
    eq = tmp_path / "equal-weight portfolio"
    eq.mkdir()
    with open(eq / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(_snapshot_10y({"cagr": 0.08, "vol_annual": 0.12}), f)
    with open(eq / "baseline_weights_metadata.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "equal_weight_method": "equal_weight_by_assets",
                "universe_eligible": ["VOO", "BND"],
                "baseline_weights_note": "fixture",
            },
            f,
        )

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    doc = build_candidate_comparison(cfg, project_root=tmp_path)
    row = next(c for c in doc["candidates"] if c["candidate_id"] == "equal_weight")
    disc = row["construction_disclosure"]
    assert disc["disclosure_status"] == "available"
    assert "baseline_weights_metadata.json" in disc["source_files"]
    assert (
        disc["baseline_metadata"]["equal_weight_method"] == "equal_weight_by_assets"
    )


def test_optimizer_candidate_methodology_disclosure_from_baseline_metadata(
    tmp_path: Path,
) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    fp = compute_candidate_config_fingerprint(cfg)
    main = tmp_path / "Main portfolio"
    subject = main / "analysis_subject"
    subject.mkdir(parents=True)
    with open(subject / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(_snapshot_10y({"cagr": 0.06, "vol_annual": 0.1}, cfg=cfg), f)
    with open(subject / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(_run_metadata("model_portfolio"), f)

    mv = tmp_path / "minimum variance portfolio"
    mv.mkdir()
    with open(mv / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(
            _snapshot_10y(
                {"cagr": 0.05, "vol_annual": 0.08, "max_drawdown": -0.1},
                cfg=cfg,
            ),
            f,
        )
    with open(mv / "baseline_weights_metadata.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "optimizer_name": "minimum_variance_constrained",
                "optimizer_run_metadata": {
                    "schema_version": "candidate_optimizer_run_metadata_v1",
                    "optimizer_role": "candidate_only",
                    "candidate_only": True,
                    "method_id": "minimum_variance_constrained",
                    "objective": "0.5 * w.T @ covariance @ w",
                    "input_window": {
                        "analysis_end": "2026-04-30",
                        "window_months": 120,
                        "return_frequency": "monthly_simple",
                    },
                    "expected_return": {
                        "uses_expected_returns": False,
                        "method": "not_used",
                    },
                    "covariance": {
                        "method": "sample_covariance",
                        "methodology": {
                            "schema_version": "optimizer_covariance_methodology_v1",
                            "method": "sample_covariance",
                            "join_policy": "inner_join_complete_cases",
                            "shrinkage": {"enabled": False, "method": None},
                            "psd_repair": {"used": False, "status": None},
                            "young_etf": {
                                "schema_version": "optimizer_young_etf_methodology_v1",
                                "enabled": False,
                                "role": "covariance_and_per_ticker_caps",
                                "mode": None,
                                "per_ticker_caps": {},
                            },
                        },
                        "methodology_summary": "Covariance method=sample_covariance; join_policy=inner_join_complete_cases; shrinkage=False (none); psd_repair=False; young ETF policy off/not used.",
                    },
                    "young_etf_methodology": {
                        "schema_version": "optimizer_young_etf_methodology_v1",
                        "enabled": False,
                        "role": "covariance_and_per_ticker_caps",
                        "mode": None,
                        "per_ticker_caps": {},
                    },
                    "constraints": {
                        "active_constraints": ["long_only", "fully_invested", "box_bounds"],
                        "bounds_used": {"VOO": {"min": 0.02, "max": 0.35}},
                    },
                    "solver": {
                        "name": "SLSQP",
                        "success": True,
                        "status": "OK",
                        "fallback_used": False,
                        "fallback_reason": None,
                        "optimization_quality_status": "clean_solve",
                    },
                },
            },
            f,
        )
    with open(main / "candidate_factory_run.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "factory_profile_id": "default_v1",
                "generated_at": "2026-05-21T10:00:00+00:00",
                "analysis_end": "2026-04-30",
                "config_fingerprint": fp,
                "steps": [
                    {
                        "candidate_id": "minimum_variance",
                        "status": "succeeded",
                        "freshness_status": "fresh",
                        "snapshot_analysis_end": "2026-04-30",
                        "expected_analysis_end": "2026-04-30",
                        "expected_config_fingerprint": fp,
                        "snapshot_config_fingerprint": fp,
                    }
                ],
            },
            f,
        )

    doc = build_candidate_comparison(cfg, project_root=tmp_path)
    row = next(c for c in doc["candidates"] if c["candidate_id"] == "minimum_variance")
    methodology = row["construction_disclosure"]["optimizer_methodology"]
    assert methodology["source"] == "baseline_weights_metadata.json.optimizer_run_metadata"
    assert methodology["method_id"] == "minimum_variance_constrained"
    assert methodology["objective"] == "0.5 * w.T @ covariance @ w"
    assert methodology["candidate_only"] is True
    assert methodology["constraints"]["active_constraints"] == [
        "long_only",
        "fully_invested",
        "box_bounds",
    ]
    assert methodology["solver"]["optimization_quality_status"] == "clean_solve"
    assert methodology["solver"]["fallback_used"] is False
    assert methodology["covariance"]["methodology"]["join_policy"] == "inner_join_complete_cases"
    assert methodology["young_etf_methodology"]["enabled"] is False
    assert methodology["freshness"]["freshness_status"] == "fresh"
    assert methodology["freshness"]["expected_config_fingerprint"] == fp

    txt_path = tmp_path / "candidate_comparison.txt"
    write_candidate_comparison_txt(doc, txt_path)
    text = txt_path.read_text(encoding="utf-8")
    assert "Optimizer methodology notes" in text
    assert "Covariance method=sample_covariance" in text
    assert "Young ETF policy disabled or not used" in text


def test_optimizer_fallback_quality_degrades_comparison_row(tmp_path: Path) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    main = tmp_path / "Main portfolio"
    subject = main / "analysis_subject"
    subject.mkdir(parents=True)
    with open(subject / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(_snapshot_10y({"cagr": 0.06, "vol_annual": 0.1}, cfg=cfg), f)
    with open(subject / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(_run_metadata("model_portfolio"), f)

    mv = tmp_path / "minimum variance portfolio"
    mv.mkdir()
    with open(mv / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(
            _snapshot_10y(
                {"cagr": 0.05, "vol_annual": 0.08, "max_drawdown": -0.1},
                cfg=cfg,
            ),
            f,
        )
    with open(mv / "baseline_weights_metadata.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "optimizer_run_metadata": {
                    "schema_version": "candidate_optimizer_run_metadata_v1",
                    "optimizer_role": "candidate_only",
                    "method_id": "minimum_variance_constrained",
                    "solver": {
                        "success": True,
                        "status": "OK_FALLBACK",
                        "fallback_used": True,
                        "fallback_reason": "fixture_retry",
                        "optimization_quality_status": "approximate_fallback",
                    },
                },
            },
            f,
        )

    doc = build_candidate_comparison(cfg, project_root=tmp_path)
    row = next(c for c in doc["candidates"] if c["candidate_id"] == "minimum_variance")
    assert row["status"] == "degraded"
    assert "optimizer_quality_not_clean:approximate_fallback" in row["warnings"]
    quality = row["construction_disclosure"]["optimizer_quality"]
    assert quality["optimization_quality_status"] == "approximate_fallback"
    assert quality["optimization_quality_family"] == "approximate"
    assert quality["fallback_used"] is True


def test_failed_factory_step_blocks_comparison_row_even_with_snapshot(
    tmp_path: Path,
) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    main = tmp_path / "Main portfolio"
    subject = main / "analysis_subject"
    subject.mkdir(parents=True)
    with open(subject / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(_snapshot_10y({"cagr": 0.06, "vol_annual": 0.1}, cfg=cfg), f)
    with open(subject / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(_run_metadata("model_portfolio"), f)

    mv = tmp_path / "minimum variance portfolio"
    mv.mkdir()
    with open(mv / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(
            _snapshot_10y(
                {"cagr": 0.05, "vol_annual": 0.08, "max_drawdown": -0.1},
                cfg=cfg,
            ),
            f,
        )
    with open(main / "candidate_factory_run.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "factory_profile_id": "default_v1",
                "generated_at": "2026-05-21T10:00:00+00:00",
                "analysis_end": "2026-04-30",
                "config_fingerprint": compute_candidate_config_fingerprint(cfg),
                "steps": [
                    {
                        "candidate_id": "minimum_variance",
                        "status": "failed",
                        "reason_code": "builder_fail_numerical",
                    }
                ],
            },
            f,
        )

    doc = build_candidate_comparison(cfg, project_root=tmp_path)
    row = next(c for c in doc["candidates"] if c["candidate_id"] == "minimum_variance")
    assert row["status"] == "unavailable"
    assert row["unavailable_reason"] == "builder_fail_numerical"
    assert "factory_step_not_successful:builder_fail_numerical" in row["warnings"]


def test_stale_factory_summary_not_used_after_fresh_comparison_rebuild(
    tmp_path: Path,
) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    fp = compute_candidate_config_fingerprint(cfg)
    main = tmp_path / "Main portfolio"
    subject = main / "analysis_subject"
    subject.mkdir(parents=True)
    with open(subject / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(_snapshot_10y({"cagr": 0.06, "vol_annual": 0.1}, cfg=cfg), f)
    with open(subject / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(_run_metadata("model_portfolio"), f)

    eq = tmp_path / "equal-weight portfolio"
    eq.mkdir()
    with open(eq / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(
            _snapshot_10y(
                {"cagr": 0.08, "vol_annual": 0.12, "max_drawdown": -0.2},
                cfg=cfg,
            ),
            f,
        )

    with open(main / "candidate_factory_run.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "factory_profile_id": "core_v1",
                "generated_at": "2026-05-21T10:00:00+00:00",
                "analysis_end": "2026-04-30",
                "config_fingerprint": fp,
                "steps": [
                    {
                        "candidate_id": "equal_weight",
                        "status": "failed",
                        "reason_code": "builder_fail_numerical",
                    }
                ],
            },
            f,
        )
    with open(main / "candidate_comparison.json", "w", encoding="utf-8") as f:
        json.dump({"generated_at": "2026-05-21T11:00:00+00:00"}, f)

    doc = build_candidate_comparison(cfg, project_root=tmp_path)
    row = next(c for c in doc["candidates"] if c["candidate_id"] == "equal_weight")
    assert row["status"] == "degraded"
    assert row["unavailable_reason"] is None
    assert "factory_step" not in row["construction_disclosure"]
    assert "candidate_factory_run.json" not in row["construction_disclosure"]["source_files"]

    menu = doc["candidate_menu"]
    assert menu["factory_evidence_status"] == "stale"
    assert menu["factory_steps_used"] is False
    assert any(
        w.startswith("factory_summary_stale_vs_existing_comparison:")
        for w in menu["factory_evidence_warnings"]
    )
    assert any(
        w.startswith("factory_summary_stale_vs_existing_comparison:")
        for w in doc["warnings"]
    )


def test_factory_then_compare_same_review_context_not_stale_on_seconds_skew(
    tmp_path: Path,
) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    fp = compute_candidate_config_fingerprint(cfg)
    main = tmp_path / "Main portfolio"
    subject = main / "analysis_subject"
    subject.mkdir(parents=True)
    with open(subject / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(_snapshot_10y({"cagr": 0.06, "vol_annual": 0.1}, cfg=cfg), f)
    with open(subject / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(_run_metadata("model_portfolio"), f)

    eq = tmp_path / "equal-weight portfolio"
    eq.mkdir()
    with open(eq / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(
            _snapshot_10y(
                {"cagr": 0.08, "vol_annual": 0.12, "max_drawdown": -0.2},
                cfg=cfg,
            ),
            f,
        )

    factory_run = {
        "factory_profile_id": "core_v1",
        "generated_at": "2026-05-21T10:00:00+00:00",
        "analysis_end": "2026-04-30",
        "config_fingerprint": fp,
        "steps": [
            {
                "candidate_id": "equal_weight",
                "status": "succeeded",
                "reason_code": None,
            }
        ],
    }
    with open(main / "candidate_factory_run.json", "w", encoding="utf-8") as f:
        json.dump(factory_run, f)
    with open(main / "candidate_comparison.json", "w", encoding="utf-8") as f:
        json.dump({"generated_at": "2026-05-21T10:00:03+00:00"}, f)

    doc = build_candidate_comparison(
        cfg,
        project_root=tmp_path,
        factory_run=factory_run,
        comparison_rebuild_source=COMPARISON_REBUILD_FACTORY_THEN_COMPARE,
    )
    menu = doc["candidate_menu"]
    assert menu["factory_evidence_status"] == "current"
    assert menu["factory_steps_used"] is True
    assert not any(
        w.startswith("factory_summary_stale_vs_existing_comparison:")
        for w in menu["factory_evidence_warnings"]
    )


def test_standalone_comparison_accepts_timing_skew_within_tolerance(
    tmp_path: Path,
) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    fp = compute_candidate_config_fingerprint(cfg)
    main = tmp_path / "Main portfolio"
    subject = main / "analysis_subject"
    subject.mkdir(parents=True)
    with open(subject / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(_snapshot_10y({"cagr": 0.06, "vol_annual": 0.1}, cfg=cfg), f)
    with open(subject / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(_run_metadata("model_portfolio"), f)

    eq = tmp_path / "equal-weight portfolio"
    eq.mkdir()
    with open(eq / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(
            _snapshot_10y(
                {"cagr": 0.08, "vol_annual": 0.12, "max_drawdown": -0.2},
                cfg=cfg,
            ),
            f,
        )

    with open(main / "candidate_factory_run.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "factory_profile_id": "core_v1",
                "generated_at": "2026-05-21T10:00:00+00:00",
                "analysis_end": "2026-04-30",
                "config_fingerprint": fp,
                "steps": [
                    {
                        "candidate_id": "equal_weight",
                        "status": "succeeded",
                        "reason_code": None,
                    }
                ],
            },
            f,
        )
    with open(main / "candidate_comparison.json", "w", encoding="utf-8") as f:
        json.dump({"generated_at": "2026-05-21T10:00:45+00:00"}, f)

    doc = build_candidate_comparison(
        cfg,
        project_root=tmp_path,
        comparison_rebuild_source=COMPARISON_REBUILD_STANDALONE,
    )
    menu = doc["candidate_menu"]
    assert menu["factory_evidence_status"] == "current"
    assert menu["factory_steps_used"] is True
    assert any(
        w.startswith("factory_summary_timing_skew_accepted:")
        for w in menu["factory_evidence_warnings"]
    )


def test_policy_optimizer_methodology_disclosure_from_run_result(tmp_path: Path) -> None:
    main = tmp_path / "Main portfolio"
    main.mkdir()
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    with open(main / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(_snapshot_10y({"cagr": 0.07, "vol_annual": 0.11}, cfg=cfg), f)
    with open(main / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(_run_metadata("generated_policy_portfolio"), f)
    with open(main / "run_result.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "status": "APPROVED",
                "optimization_status": "OK",
                "optimizer_run_metadata": {
                    "schema_version": "legacy_policy_optimizer_run_metadata_v1",
                    "optimizer_role": "legacy_policy",
                    "method_id": "legacy_policy_max_return_v1",
                    "objective": {
                        "objective_mode": "max_return",
                        "expected_returns_used": True,
                    },
                    "input_window": {
                        "analysis_end": "2026-04-30",
                        "window_months": 120,
                    },
                    "constraints": {
                        "long_only": True,
                        "fully_invested_risk_portfolio": True,
                    },
                    "solver": {
                        "solver_success": True,
                        "solver_status": "OK",
                        "fallback_used": False,
                        "fallback_reason": None,
                        "optimization_quality_status": "clean_solve",
                    },
                },
            },
            f,
        )

    doc = build_candidate_comparison(cfg, project_root=tmp_path)
    row = next(c for c in doc["candidates"] if c["candidate_id"] == "policy")
    methodology = row["construction_disclosure"]["optimizer_methodology"]
    assert methodology["source"] == "run_result.json.optimizer_run_metadata"
    assert methodology["optimizer_role"] == "legacy_policy"
    assert methodology["candidate_only"] is False
    assert methodology["method_id"] == "legacy_policy_max_return_v1"
    assert methodology["solver"]["status"] == "OK"
    assert methodology["solver"]["optimization_quality_status"] == "clean_solve"


def test_risk_budget_construction_disclosure_includes_effective_targets(
    tmp_path: Path,
) -> None:
    rb = tmp_path / "risk budget by asset portfolio"
    rb.mkdir()
    with open(rb / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(_snapshot_10y({"cagr": 0.07, "vol_annual": 0.11}), f)
    with open(rb / "baseline_weights_metadata.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "risk_budgeting_method": "spinu_asset_level",
                "target_risk_budgets": {"VOO": 0.6, "BND": 0.4},
                "target_risk_budgets_effective": {"VOO": 0.6, "BND": 0.4},
            },
            f,
        )

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    doc = build_candidate_comparison(cfg, project_root=tmp_path)
    row = next(
        c for c in doc["candidates"] if c["candidate_id"] == "risk_budget_by_asset"
    )
    meta = row["construction_disclosure"]["baseline_metadata"]
    assert meta["target_risk_budgets_effective"]["VOO"] == 0.6


def test_construction_disclosure_partial_from_summary_when_metadata_missing(
    tmp_path: Path,
) -> None:
    rp = tmp_path / "risk parity portfolio"
    rp.mkdir()
    with open(rp / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(_snapshot_10y({"cagr": 0.07, "vol_annual": 0.1}), f)
    with open(rp / "summary.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "portfolio_type": "Risk Parity",
                "status": "OK",
                "solver_status": "APPROXIMATE",
                "max_rc_error": 0.02,
            },
            f,
        )

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO"],
        }
    )
    doc = build_candidate_comparison(cfg, project_root=tmp_path)
    row = next(c for c in doc["candidates"] if c["candidate_id"] == "risk_parity")
    disc = row["construction_disclosure"]
    assert disc["disclosure_status"] == "partial"
    assert disc["builder_summary"]["solver_status"] == "APPROXIMATE"
    assert "summary.json" in disc["source_files"]


def test_construction_disclosure_includes_factory_step_excerpt(tmp_path: Path) -> None:
    eq = tmp_path / "equal-weight portfolio"
    eq.mkdir()
    main = tmp_path / "Main portfolio"
    main.mkdir()
    with open(eq / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(_snapshot_10y({"cagr": 0.08, "vol_annual": 0.12}), f)
    with open(main / "candidate_factory_run.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "factory_profile_id": "core_v1",
                "generated_at": "2026-05-21T10:00:00+00:00",
                "steps": [
                    {
                        "candidate_id": "equal_weight",
                        "status": "failed",
                        "reason_code": "builder_infeasible",
                        "builder_status": "FAIL_INFEASIBLE",
                        "builder_reason": "empty universe",
                    }
                ],
            },
            f,
        )

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO"],
        }
    )
    doc = build_candidate_comparison(cfg, project_root=tmp_path)
    row = next(c for c in doc["candidates"] if c["candidate_id"] == "equal_weight")
    step = row["construction_disclosure"]["factory_step"]
    assert step["reason_code"] == "builder_infeasible"
    assert step["builder_status"] == "FAIL_INFEASIBLE"
    assert "candidate_factory_run.json" in row["construction_disclosure"]["source_files"]


def test_robust_scenario_construction_disclosure_main_prerequisites(tmp_path: Path) -> None:
    main = tmp_path / "Main portfolio"
    main.mkdir()
    with open(main / "candidate_factory_run.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "factory_profile_id": "default_v1",
                "generated_at": "2026-05-21T10:00:00+00:00",
                "steps": [
                    {
                        "candidate_id": "robust_scenario",
                        "status": "skipped_dependency",
                        "reason_code": "skipped_dependency",
                        "robust_paths_disclosure": {
                            "kind": "robust_scenario_main_prerequisites",
                            "shared_calibration_scope": "main_output_dir_final",
                            "prerequisites_met": False,
                            "missing_artifacts": [
                                "scenario_library_normalized.json",
                                "stress_report.json",
                            ],
                        },
                    }
                ],
            },
            f,
        )

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO"],
        }
    )
    doc = build_candidate_comparison(cfg, project_root=tmp_path)
    row = next(c for c in doc["candidates"] if c["candidate_id"] == "robust_scenario")
    rp = row["construction_disclosure"]["robust_paths"]
    assert rp["kind"] == "robust_scenario_main_prerequisites"
    assert rp["prerequisites_met"] is False
    assert rp["shared_calibration_scope"] == "main_output_dir_final"


def test_robust_scenario_optimizer_methodology_disclosure(tmp_path: Path) -> None:
    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO", "BND"],
        }
    )
    main = tmp_path / "Main portfolio"
    subject = main / "analysis_subject"
    subject.mkdir(parents=True)
    with open(subject / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(_snapshot_10y({"cagr": 0.06, "vol_annual": 0.1}, cfg=cfg), f)
    with open(subject / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(_run_metadata("model_portfolio"), f)

    robust = tmp_path / "robust scenario portfolio"
    robust.mkdir()
    with open(robust / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(
            _snapshot_10y(
                {"cagr": 0.055, "vol_annual": 0.09, "max_drawdown": -0.12},
                cfg=cfg,
            ),
            f,
        )
    with open(robust / "baseline_weights_metadata.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "variant": "robust_scenario_portfolio_v1",
                "optimizer_run_metadata": {
                    "schema_version": "robust_scenario_optimizer_run_metadata_v1",
                    "optimizer_role": "candidate_only",
                    "candidate_only": True,
                    "method_id": "robust_scenario_optimization_v1",
                    "objective": {
                        "objective_mode": "lower_half_mean",
                        "expected_returns_used": True,
                    },
                    "input_window": {
                        "analysis_end": None,
                        "scenario_count": 3,
                    },
                    "expected_return": {"used": True},
                    "covariance": {
                        "method": "base_historical.asset_covariance_monthly_equivalent",
                    },
                    "constraints": {
                        "active_constraints": [
                            "long_only",
                            "fully_invested",
                            "box_bounds",
                        ],
                    },
                    "solver": {
                        "name": "SLSQP",
                        "success": True,
                        "status": "OK",
                        "fallback_used": False,
                        "fallback_reason": None,
                        "optimization_quality_status": "clean_solve",
                    },
                },
            },
            f,
        )

    doc = build_candidate_comparison(cfg, project_root=tmp_path)
    row = next(c for c in doc["candidates"] if c["candidate_id"] == "robust_scenario")
    methodology = row["construction_disclosure"]["optimizer_methodology"]
    assert methodology["source"] == "baseline_weights_metadata.json.optimizer_run_metadata"
    assert methodology["source_schema_version"] == "robust_scenario_optimizer_run_metadata_v1"
    assert methodology["method_id"] == "robust_scenario_optimization_v1"
    assert methodology["objective"]["objective_mode"] == "lower_half_mean"
    assert methodology["solver"]["optimization_quality_status"] == "clean_solve"
    quality = row["construction_disclosure"]["optimizer_quality"]
    assert quality["optimization_quality_status"] == "clean_solve"
    assert quality["optimization_quality_family"] == "clean"


def test_robust_mv_construction_disclosure_lambda_without_factory_run(
    tmp_path: Path,
) -> None:
    cal = tmp_path / "analysis_robust_mv_lambda_calibration"
    cal.mkdir(parents=True)
    (cal / "selected_lambda.txt").write_text("0.3\n", encoding="utf-8")
    folder = tmp_path / "robust mean variance constrained portfolio"
    folder.mkdir()
    with open(folder / "snapshot_10y.json", "w", encoding="utf-8") as f:
        json.dump(_snapshot_10y({"cagr": 0.06, "vol_annual": 0.1}), f)
    with open(folder / "baseline_weights_metadata.json", "w", encoding="utf-8") as f:
        json.dump({"robust_mv_lambda": 0.3, "optimizer_name": "robust_mv"}, f)

    cfg = validate_config(
        {
            "investor_currency": "USD",
            "output_dir_final": "Main portfolio",
            "tickers": ["VOO"],
        }
    )
    doc = build_candidate_comparison(cfg, project_root=tmp_path)
    row = next(
        c for c in doc["candidates"] if c["candidate_id"] == "robust_mv_constrained"
    )
    rp = row["construction_disclosure"]["robust_paths"]
    assert rp["kind"] == "robust_mv_lambda"
    assert rp["robust_mv_lambda"] == 0.3
    assert rp["lambda_resolution_key"] == "calibration_file"
    assert rp["robust_mv_lambda_from_baseline_metadata"] == 0.3
