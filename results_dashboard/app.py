"""
Results dashboard — key optimization / report metrics in the browser.

Usage:
    pip install flask pyyaml
    python results_dashboard/app.py

Open http://localhost:5005

Reads output_dir_final from project config.yml (default Main portfolio), then
run_result.json and snapshot_10y.json. Styling: DESIGN.md (shared design.css).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

# Project root
DASH_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = DASH_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import yaml
from flask import Flask, render_template, send_file

from src.client_profiles import apply_profile_to_config

app = Flask(
    __name__,
    static_folder=str(DASH_DIR / "static"),
    template_folder=str(DASH_DIR / "templates"),
)

CONFIG_PATH = PROJECT_ROOT / "config.yml"
DESIGN_CSS = PROJECT_ROOT / "config_ui" / "static" / "design.css"


def _read_yaml_config() -> dict[str, Any]:
    if not CONFIG_PATH.is_file():
        return {}
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _output_dir() -> Path:
    raw = _read_yaml_config()
    merged = apply_profile_to_config(dict(raw))
    name = merged.get("output_dir_final") or "Main portfolio"
    return (PROJECT_ROOT / str(name)).resolve()


def _fmt_pct(x: Any, *, signed: bool = False, decimals: int = 2) -> str:
    if x is None:
        return "—"
    try:
        v = float(x) * 100.0
    except (TypeError, ValueError):
        return "—"
    if signed and v > 0:
        return f"+{v:.{decimals}f}%"
    return f"{v:.{decimals}f}%"


def _top_weights(weights: dict[str, Any], n: int = 12) -> list[tuple[str, float]]:
    if not isinstance(weights, dict):
        return []
    items = [(str(k), float(v)) for k, v in weights.items() if isinstance(v, (int, float))]
    items.sort(key=lambda t: -t[1])
    return items[:n]


def _rc_block_list_to_dict(rc_block: Any) -> dict[str, float]:
    if not rc_block:
        return {}
    out: dict[str, float] = {}
    if isinstance(rc_block, list):
        for x in rc_block:
            if isinstance(x, dict) and x.get("block") is not None:
                out[str(x["block"])] = float(x.get("rc_pct", 0) or 0)
    return out


def _infer_targets(
    actual: dict[str, float],
    rb_deltas_pp: dict[str, Any] | None,
) -> dict[str, float | None]:
    """target RC ≈ actual − (delta_pp / 100) for Growth/Duration/Inflation."""
    out: dict[str, float | None] = {}
    if not rb_deltas_pp:
        for b in ("Growth", "Duration", "Inflation"):
            out[b] = None
        return out
    for b in ("Growth", "Duration", "Inflation"):
        a = actual.get(b)
        d = rb_deltas_pp.get(b)
        if a is not None and d is not None:
            try:
                out[b] = float(a) - float(d) / 100.0
            except (TypeError, ValueError):
                out[b] = None
        else:
            out[b] = None
    return out


def build_view_model() -> dict[str, Any]:
    out: dict[str, Any] = {
        "project_root": str(PROJECT_ROOT),
        "output_dir": None,
        "config_path": str(CONFIG_PATH),
        "error": None,
        "has_data": False,
    }
    out_dir = _output_dir()
    out["output_dir"] = str(out_dir)

    rr_path = out_dir / "run_result.json"
    snap_path = out_dir / "snapshot_10y.json"
    report_path = out_dir / "report.html"

    if not rr_path.is_file():
        out["error"] = f"Нет {rr_path.name}. Сначала выполните оптимизацию и отчёт (run_optimization / run_report)."
        return out

    with open(rr_path, encoding="utf-8") as f:
        run_result: dict[str, Any] = json.load(f)

    snap: dict[str, Any] = {}
    if snap_path.is_file():
        with open(snap_path, encoding="utf-8") as f:
            snap = json.load(f)

    cfg = apply_profile_to_config(dict(_read_yaml_config()))
    rc_targets_cfg = cfg.get("rc_block_targets")
    if not isinstance(rc_targets_cfg, dict):
        rc_targets_cfg = {}

    weights = run_result.get("weights") or {}
    status = str(run_result.get("status", "—"))
    mandate = run_result.get("mandate_check") or {}
    stress = run_result.get("stress_summary") or {}
    rb_deltas = run_result.get("rb_deltas_pp") or {}
    violations = run_result.get("violations") or []
    rc_breaches = run_result.get("rc_breaches") or []

    actual_rc = _rc_block_list_to_dict(snap.get("RC_block"))
    if not actual_rc and isinstance(run_result.get("rc_by_block_10y"), dict):
        actual_rc = {k: float(v) for k, v in run_result["rc_by_block_10y"].items()}

    targets: dict[str, float | None] = {}
    for b in ("Growth", "Duration", "Inflation"):
        if b in rc_targets_cfg and rc_targets_cfg[b] is not None:
            try:
                targets[b] = float(rc_targets_cfg[b])
            except (TypeError, ValueError):
                targets[b] = None
        else:
            targets[b] = _infer_targets(actual_rc, rb_deltas).get(b)

    rc_rows = []
    for b in ("Growth", "Duration", "Inflation"):
        ar = actual_rc.get(b)
        tr = targets.get(b)
        dpp = rb_deltas.get(b)
        if isinstance(dpp, (int, float)):
            dpp_fmt = f"{float(dpp):+.2f}"
        else:
            dpp_fmt = "—"
        row = {
            "block": b,
            "actual": ar,
            "target": tr,
            "actual_pct": _fmt_pct(ar) if ar is not None else "—",
            "target_pct": _fmt_pct(tr) if tr is not None else "—",
            "delta_pp": dpp,
            "delta_pp_fmt": dpp_fmt,
        }
        if tr is not None and ar is not None:
            row["gap_pp"] = (ar - tr) * 100.0
        else:
            row["gap_pp"] = None
        rc_rows.append(row)

    metrics = snap.get("metrics") or {}
    block_weights = snap.get("block_weights") or {}

    v_lines = _summarize_violations(violations)
    tw = _top_weights(weights, 12)
    max_w = max((w for _, w in tw), default=0.0) or 1.0

    out.update(
        {
            "has_data": True,
            "client_profile": cfg.get("client_profile"),
            "status": status,
            "status_kind": _status_kind(status, mandate.get("pass"), stress.get("status")),
            "weights": weights,
            "top_weights": tw,
            "max_weight": max_w,
            "violation_lines": v_lines,
            "analysis_end": snap.get("analysis_end") or "—",
            "mandate": mandate,
            "mandate_max_dd_pct": _fmt_pct(mandate.get("max_drawdown_realized")),
            "mandate_dd_limit_pct": _fmt_pct(mandate.get("limit_pct")),
            "stress": stress,
            "stress_worst_pct": _fmt_pct(stress.get("worst_scenario_loss_pct")),
            "rb_deltas": rb_deltas,
            "violations": violations,
            "rc_breaches": rc_breaches[:16],
            "rc_rows": rc_rows,
            "block_weights": block_weights,
            "metrics_cagr": _fmt_pct(metrics.get("cagr")) if metrics.get("cagr") is not None else "—",
            "metrics_vol": _fmt_pct(metrics.get("vol_annual")) if metrics.get("vol_annual") is not None else "—",
            "metrics_mdd": _fmt_pct(metrics.get("max_drawdown")) if metrics.get("max_drawdown") is not None else "—",
            "metrics_sharpe": f"{float(metrics.get('sharpe')):.3f}" if metrics.get("sharpe") is not None else "—",
            "report_url": "/report" if report_path.is_file() else None,
        }
    )
    return out


def _summarize_violations(violations: list[Any]) -> list[str]:
    lines: list[str] = []
    for v in violations or []:
        if not isinstance(v, dict):
            continue
        code = str(v.get("code", ""))
        d = v.get("details")
        if code == "RC_VIOLATION" and isinstance(d, dict):
            viol = d.get("remaining_violators") or []
            lines.append(
                f"RC post-process: {d.get('reason', '—')}; остались: {', '.join(str(t) for t in viol[:12])}"
                f"{'…' if len(viol) > 12 else ''}"
            )
        elif code == "RB_BREACH" and isinstance(d, dict):
            parts = [f"{bk} {float(dv):+.1f} п.п." for bk, dv in d.items() if isinstance(dv, (int, float))]
            lines.append("RB коридор: " + (", ".join(parts) if parts else str(d)))
        elif code == "VIOL_RC_ASSET_CAP" and isinstance(d, list):
            for item in d[:6]:
                if isinstance(item, dict) and "ticker" in item:
                    lines.append(
                        f"RC cap: {item.get('ticker')} RC={item.get('rc_pct')}% / cap {item.get('cap_pct')}%"
                    )
        elif code == "FAIL_STRESS" and isinstance(d, dict):
            lines.append(
                f"Stress (диаг.): {d.get('primary_diagnostic_code', '—')}; "
                f"сценарий: {d.get('failed_scenario', '—')}"
            )
        else:
            lines.append(f"{code}: {d}"[:180])
    return lines[:20]


def _status_kind(status: str, mandate_pass: Any, stress_st: Any) -> str:
    s = (status or "").upper()
    if "FAIL" in s or s.startswith("FAIL"):
        return "bad"
    if mandate_pass is False:
        return "bad"
    if s in ("APPROVED", "OK", "OK_FALLBACK", ""):
        return "ok"
    if "CANDIDATE" in s or "ATTENTION" in str(stress_st).upper() or "DIAG" in str(stress_st).upper():
        return "warn"
    return "neutral"


@app.route("/")
def index():
    return render_template("dashboard.html", vm=build_view_model(), design_css_href="/design-assets/design.css")


@app.route("/report")
def report_html():
    out_dir = _output_dir()
    p = out_dir / "report.html"
    if not p.is_file():
        return f"Нет {p}", 404
    return send_file(p, mimetype="text/html; charset=utf-8", max_age=0)


@app.route("/design-assets/<path:subpath>")
def design_assets(subpath: str):
    """Serve shared DESIGN.md stylesheet from config_ui/static."""
    base = PROJECT_ROOT / "config_ui" / "static"
    target = (base / subpath).resolve()
    if not str(target).startswith(str(base.resolve())) or not target.is_file():
        return "Not found", 404
    return send_file(target, max_age=3600)


def main() -> None:
    port = int(os.environ.get("RESULTS_DASHBOARD_PORT", "5005"))
    if not DESIGN_CSS.is_file():
        print("Warning: design.css not at", DESIGN_CSS, file=sys.stderr)
    app.run(host="127.0.0.1", port=port, debug=False)


if __name__ == "__main__":
    main()
