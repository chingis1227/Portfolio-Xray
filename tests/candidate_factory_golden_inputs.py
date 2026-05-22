"""Deterministic inputs for Candidate Factory / Comparison golden contract tests (RM-978).

Regenerate committed golden JSON after intentional contract changes:

    python tests/candidate_factory_golden_inputs.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.candidate_comparison import build_candidate_comparison
from src.candidate_factory import run_candidate_factory
from src.config_schema import validate_config
from src.snapshot import compute_candidate_config_fingerprint

_FIXTURES = Path(__file__).resolve().parent / "fixtures"
FACTORY_GOLDEN_PATH = _FIXTURES / "candidate_factory_run_golden_v1.json"
COMPARISON_GOLDEN_PATH = _FIXTURES / "candidate_comparison_golden_v1.json"

GOLDEN_GENERATED_AT = "2026-05-20T12:00:00+00:00"
GOLDEN_ANALYSIS_END = "2026-04-30"
GOLDEN_PROJECT_ROOT = "/golden/candidate_factory_project"

_GOLDEN_CFG_DICT = {
    "investor_currency": "USD",
    "analysis_mode": "optimize_from_universe",
    "output_dir_final": "Main portfolio",
    "tickers": ["VOO", "BND"],
    "risk_budgeting": {
        "targets": {"equity": 0.6, "fixed_income": 0.4},
    },
    "min_weight_per_security": 0.02,
    "max_weight_per_security": 0.35,
}


def _snapshot_10y(
    metrics: dict[str, float],
    *,
    analysis_end: str = GOLDEN_ANALYSIS_END,
    cfg: object,
) -> dict[str, Any]:
    return {
        "analysis_end": analysis_end,
        "window_label": "10y",
        "metrics": metrics,
        "stress_suite_results": {
            "overall": "PASS",
            "fail_reason_code": None,
            "failed_scenario": None,
            "scenarios": [
                {"scenario_id": "equity_shock", "portfolio_pnl_pct": -0.05, "pass": True}
            ],
        },
        "constraints_status": {"target_vol": "PASS", "max_dd": "PASS"},
        "candidate_config_fingerprint": compute_candidate_config_fingerprint(cfg),
    }


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _golden_runner(cfg: object) -> Any:
    fp = compute_candidate_config_fingerprint(cfg)
    script_to_folder = {
        "run_equal_weight.py": "equal-weight portfolio",
        "run_risk_parity.py": "risk parity portfolio",
    }

    def runner(cmd: list[str], cwd: str | Path) -> int:
        script = Path(cmd[1]).name
        folder = script_to_folder.get(script)
        if folder:
            art = Path(cwd) / folder
            art.mkdir(parents=True, exist_ok=True)
            _write_json(
                art / "snapshot_10y.json",
                {
                    "analysis_end": GOLDEN_ANALYSIS_END,
                    "window_label": "10y",
                    "candidate_config_fingerprint": fp,
                    "metrics": {"cagr": 0.07, "vol_annual": 0.1},
                },
            )
        return 0

    return runner


def normalize_factory_run(doc: dict[str, Any]) -> dict[str, Any]:
    out = json.loads(json.dumps(doc))
    out["generated_at"] = GOLDEN_GENERATED_AT
    out["project_root"] = GOLDEN_PROJECT_ROOT
    out["analysis_end"] = GOLDEN_ANALYSIS_END
    if isinstance(out.get("manifest"), dict):
        out["manifest"]["path"] = (
            f"{GOLDEN_PROJECT_ROOT}/Main portfolio/candidate_factory_manifest.json"
        )
    options = out.get("options")
    if "run_status" not in out:
        out["run_status"] = "full_success"
    if isinstance(options, dict):
        if "resume" not in options:
            options["resume"] = False
        if "pdf_mode" not in options:
            options["pdf_mode"] = "none"
        if "execution_mode" not in options:
            options["execution_mode"] = "legacy_full"
    for index, step in enumerate(out.get("steps", [])):
        step["duration_seconds"] = round(1.0 + index * 0.01, 3)
        commands = []
        for raw in step.get("entry_commands") or []:
            token = str(raw).replace("\\", "/")
            script = Path(token.split()[-1]).name if token else ""
            commands.append(f"python {script}" if script else token)
        step["entry_commands"] = commands
    return out


def normalize_comparison(doc: dict[str, Any]) -> dict[str, Any]:
    out = json.loads(json.dumps(doc))
    out["generated_at"] = GOLDEN_GENERATED_AT
    out["analysis_end"] = GOLDEN_ANALYSIS_END
    return out


def golden_factory_build_kwargs() -> dict[str, Any]:
    """Keyword arguments for ``run_candidate_factory`` in golden contract tests."""
    return {
        "explicit_candidates": ["equal_weight", "risk_parity"],
        "skip_existing": False,
        "force": False,
        "fail_fast": False,
    }


def _materialize_golden_project(root: Path) -> tuple[Any, dict[str, Any]]:
    cfg = validate_config(dict(_GOLDEN_CFG_DICT))
    subject = root / "Main portfolio" / "analysis_subject"
    subject.mkdir(parents=True)
    _write_json(
        subject / "run_metadata.json",
        {
            "run_info": {"analysis_end_date": GOLDEN_ANALYSIS_END},
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
            },
        },
    )
    _write_json(
        subject / "snapshot_10y.json",
        _snapshot_10y(
            {"cagr": 0.071, "vol_annual": 0.1, "max_drawdown": -0.18, "sharpe": 0.55},
            cfg=cfg,
        ),
    )
    return cfg, {"runner": _golden_runner(cfg)}


def build_golden_factory_run(*, root: Path | None = None) -> dict[str, Any]:
    if root is not None:
        cfg, runner_kwargs = _materialize_golden_project(root)
        doc = run_candidate_factory(
            cfg,
            project_root=root,
            runner=runner_kwargs["runner"],
            **golden_factory_build_kwargs(),
        )
        return normalize_factory_run(doc)
    with tempfile.TemporaryDirectory(prefix="cf_golden_") as tmp:
        return build_golden_factory_run(root=Path(tmp))


def build_golden_comparison() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="cc_golden_") as tmp:
        root = Path(tmp)
        cfg, runner_kwargs = _materialize_golden_project(root)
        fp = compute_candidate_config_fingerprint(cfg)

        factory_run = run_candidate_factory(
            cfg,
            project_root=root,
            runner=runner_kwargs["runner"],
            **golden_factory_build_kwargs(),
        )
        factory_run = normalize_factory_run(factory_run)
        factory_run["config_fingerprint"] = fp

        ew = root / "equal-weight portfolio"
        ew.mkdir(parents=True, exist_ok=True)
        _write_json(
            ew / "snapshot_10y.json",
            _snapshot_10y(
                {"cagr": 0.08, "vol_annual": 0.12, "max_drawdown": -0.2, "sharpe": 0.5},
                cfg=cfg,
            ),
        )
        _write_json(
            ew / "baseline_weights_metadata.json",
            {
                "equal_weight_method": "equal_weight_by_assets",
                "universe_eligible": ["VOO", "BND"],
                "baseline_weights_note": "golden_fixture",
            },
        )

        rp = root / "risk parity portfolio"
        rp.mkdir(parents=True, exist_ok=True)
        _write_json(
            rp / "snapshot_10y.json",
            _snapshot_10y(
                {"cagr": 0.07, "vol_annual": 0.1, "max_drawdown": -0.17, "sharpe": 0.48},
                cfg=cfg,
            ),
        )
        _write_json(
            rp / "summary.json",
            {
                "portfolio_type": "Risk Parity",
                "status": "OK",
                "solver_status": "APPROXIMATE",
                "max_rc_error": 0.02,
            },
        )

        _write_json(root / "Main portfolio" / "candidate_factory_run.json", factory_run)

        doc = build_candidate_comparison(cfg, project_root=root)
        return normalize_comparison(doc)


def write_golden_fixtures() -> tuple[Path, Path]:
    _FIXTURES.mkdir(parents=True, exist_ok=True)
    factory_doc = build_golden_factory_run()
    comparison_doc = build_golden_comparison()
    FACTORY_GOLDEN_PATH.write_text(
        json.dumps(factory_doc, indent=2) + "\n", encoding="utf-8"
    )
    COMPARISON_GOLDEN_PATH.write_text(
        json.dumps(comparison_doc, indent=2) + "\n", encoding="utf-8"
    )
    return FACTORY_GOLDEN_PATH, COMPARISON_GOLDEN_PATH


if __name__ == "__main__":
    factory_path, comparison_path = write_golden_fixtures()
    print(f"Wrote {factory_path} ({factory_path.stat().st_size} bytes)")
    print(f"Wrote {comparison_path} ({comparison_path.stat().st_size} bytes)")
