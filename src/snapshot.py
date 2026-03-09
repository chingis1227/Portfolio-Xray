"""
Final optimization/report snapshot: one object, same print and save.
Used by run_optimization.py and run_report.py.
"""
from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.config_schema import STRESS_BLOCK_NAMES
from src.risk_contrib import rc_vol_window
from src.stress import _ticker_to_stress_block
from src.windows import slice_window

RB_CORRIDOR_DEFAULT_PP = 0.05  # target ± 5pp for RB corridor
REPORT_DECIMALS = 3
TOP_RC_N = 5


def _ticker_to_display_block(blocks: dict[str, list[str]]) -> dict[str, str]:
    """Map each ticker to one of Growth, Duration, Inflation, Liquidity, Tail."""
    return _ticker_to_stress_block(blocks, None)


def _block_weights_from_total(
    weights_total: dict[str, float],
    blocks: dict[str, list[str]],
) -> dict[str, float]:
    """Sum weights by display block (Growth, Duration, Inflation, Liquidity, Tail)."""
    t2b = _ticker_to_display_block(blocks)
    out = {b: 0.0 for b in STRESS_BLOCK_NAMES}
    for t, w in weights_total.items():
        b = t2b.get(t)
        if b is not None:
            out[b] = out.get(b, 0.0) + w
    return {b: round(out[b], REPORT_DECIMALS) for b in STRESS_BLOCK_NAMES}


def _rc_asset_top(rc_series: pd.Series, top_n: int = TOP_RC_N) -> list[dict[str, Any]]:
    """Top N assets by RC (percentage)."""
    if rc_series is None or rc_series.empty:
        return []
    s = rc_series.dropna().sort_values(ascending=False).head(top_n)
    return [{"ticker": str(t), "rc_pct": round(float(v), REPORT_DECIMALS)} for t, v in s.items()]


def _rc_block_from_asset(
    rc_series: pd.Series,
    blocks: dict[str, list[str]],
) -> list[dict[str, Any]]:
    """Aggregate RC by display block (Growth = Growth + Growth_HY + Growth_EM_debt)."""
    if rc_series is None or rc_series.empty:
        return []
    t2b = _ticker_to_display_block(blocks)
    agg: dict[str, float] = {b: 0.0 for b in STRESS_BLOCK_NAMES}
    for t, v in rc_series.items():
        b = t2b.get(t)
        if b is not None and not (v != v):
            agg[b] = agg.get(b, 0.0) + float(v)
    return [{"block": b, "rc_pct": round(agg[b], REPORT_DECIMALS)} for b in STRESS_BLOCK_NAMES if agg.get(b, 0) != 0]


def _constraints_status(
    *,
    target_vol_annual: float | None,
    current_vol_annual: float | None,
    max_dd_ok: bool | None,
    rc_block_targets: dict[str, float] | None,
    actual_rc_block: dict[str, float] | None,
    rc_caps_ok: bool | None,
    weight_caps_ok: bool | None,
    rb_corridor_pp: float = RB_CORRIDOR_DEFAULT_PP,
) -> dict[str, str]:
    """Build constraints_status dict (PASS / FAIL / NOT_CHECKED)."""
    status: dict[str, str] = {}

    if target_vol_annual is not None and current_vol_annual is not None:
        status["target_vol"] = "PASS" if current_vol_annual <= target_vol_annual + 1e-6 else "FAIL"
    else:
        status["target_vol"] = "NOT_CHECKED"

    if max_dd_ok is True:
        status["max_dd"] = "PASS"
    elif max_dd_ok is False:
        status["max_dd"] = "FAIL"
    else:
        status["max_dd"] = "NOT_CHECKED"

    if rc_block_targets and actual_rc_block:
        # RB corridor: actual within target ± rb_corridor_pp for Growth, Duration, Inflation
        inside = True
        for block in ("Growth", "Duration", "Inflation"):
            target = rc_block_targets.get(block)
            actual = actual_rc_block.get(block, 0.0)
            if target is not None:
                if abs(actual - target) > rb_corridor_pp:
                    inside = False
                    break
        status["rb_corridor"] = "PASS" if inside else "FAIL"
    else:
        status["rb_corridor"] = "NOT_CHECKED"

    if rc_caps_ok is True:
        status["rc_caps"] = "PASS"
    elif rc_caps_ok is False:
        status["rc_caps"] = "FAIL"
    else:
        status["rc_caps"] = "NOT_CHECKED"

    if weight_caps_ok is True:
        status["weight_caps"] = "PASS"
    elif weight_caps_ok is False:
        status["weight_caps"] = "FAIL"
    else:
        status["weight_caps"] = "NOT_CHECKED"

    return status


def _stress_suite_results_for_snapshot(stress_report: dict[str, Any], portfolio_params: dict[str, Any] | None) -> dict[str, Any]:
    """Format stress_suite_results section; include per-scenario violations and portfolio_params."""
    overall = stress_report.get("status", "N/A")
    fail_reason = stress_report.get("fail_reason_code") or stress_report.get("skip_reason")

    scenarios_out = []
    for s in stress_report.get("scenario_results", []):
        violations = []
        if not s.get("loss_ok", True):
            violations.append("loss")
        if not s.get("role_ok", True):
            violations.append("role")
        if not s.get("rc1_ok", True):
            violations.append("rc_top1")
        if not s.get("rc3_ok", True):
            violations.append("rc_top3")
        scenarios_out.append({
            "scenario_id": s.get("scenario_id"),
            "portfolio_pnl_pct": round(s.get("portfolio_pnl_pct", 0), 4),
            "pnl_by_block_pct": {k: round(v, 4) for k, v in (s.get("pnl_by_block_pct") or {}).items()},
            "violations": violations,
            "pass": s.get("pass", True),
        })

    return {
        "overall": overall,
        "fail_reason_code": fail_reason,
        "scenarios": scenarios_out,
        "historical": stress_report.get("historical_results", []),
        "portfolio_params": portfolio_params or {},
    }


def build_snapshot(
    final_weights_total: dict[str, float],
    blocks: dict[str, list[str]],
    cash_proxy_ticker: str,
    analysis_end: str,
    stress_report: dict[str, Any],
    *,
    final_weights_risk_portfolio: dict[str, float] | None = None,
    rc_series: pd.Series | None = None,
    monthly_returns: pd.DataFrame | None = None,
    window_months: int = 60,
    target_vol_annual: float | None = None,
    current_vol_annual: float | None = None,
    max_dd_ok: bool | None = None,
    rc_block_targets: dict[str, float] | None = None,
    rc_caps_ok: bool | None = True,
    weight_caps_ok: bool | None = None,
    min_single_security_weight_pct: float | None = None,
    max_single_security_weight_pct: float | None = None,
    portfolio_metrics_summary: dict[str, Any] | None = None,
    run_timestamp: str | None = None,
    rb_corridor_pp: float = RB_CORRIDOR_DEFAULT_PP,
    # Optional per-window portfolio metrics and RC/correlation outputs (3Y/5Y/10Y), per metrics_specification.md §11
    portfolio_windows: dict[str, dict[str, Any]] | None = None,
    rc_by_window: dict[str, pd.Series] | None = None,
    rc_csv_by_window: dict[str, str] | None = None,
    corr_csv_by_window: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Build the single final snapshot dict.
    If final_weights_risk_portfolio is None, derive from total (exclude cash, renormalize).
    If rc_series is None but monthly_returns and window_months are provided, RC is computed from full portfolio weights.
    """
    if run_timestamp is None:
        run_timestamp = datetime.now().isoformat()

    # Risk portfolio weights (no cash)
    if final_weights_risk_portfolio is not None:
        risk_weights = dict(final_weights_risk_portfolio)
    else:
        risk_weights = {t: w for t, w in final_weights_total.items() if t != cash_proxy_ticker and w > 0}
        total_risk = sum(risk_weights.values())
        if total_risk > 0:
            risk_weights = {t: w / total_risk for t, w in risk_weights.items()}
    risk_weights = {t: round(w, REPORT_DECIMALS) for t, w in risk_weights.items() if w > 0}

    # RC: compute if not provided
    if rc_series is None and monthly_returns is not None and window_months and not monthly_returns.empty:
        asset_cols = [t for t in final_weights_total if t in monthly_returns.columns and final_weights_total.get(t, 0) > 0]
        if asset_cols:
            try:
                ret_slice = slice_window(monthly_returns[asset_cols], pd.Timestamp(analysis_end), window_months)
                ret_slice = ret_slice.dropna(how="all")
                if len(ret_slice) >= 2:
                    weights_df = pd.DataFrame(
                        index=ret_slice.index,
                        data={t: final_weights_total.get(t, 0.0) for t in asset_cols},
                    )
                    rc_series = rc_vol_window(ret_slice, weights_df, ddof=1)
            except Exception:
                rc_series = pd.Series(dtype=float)
        else:
            rc_series = pd.Series(dtype=float)

    rc_asset_top = _rc_asset_top(rc_series) if rc_series is not None else []
    rc_block_list = _rc_block_from_asset(rc_series, blocks) if rc_series is not None else []
    actual_rc_block = {x["block"]: x["rc_pct"] for x in rc_block_list} if rc_block_list else None

    # Weight caps check (optional)
    if weight_caps_ok is None and (min_single_security_weight_pct is not None or max_single_security_weight_pct is not None):
        min_w = (min_single_security_weight_pct or 0) / 100.0
        max_w = (max_single_security_weight_pct or 100) / 100.0
        weight_caps_ok = True
        for t, w in final_weights_total.items():
            if w <= 0:
                continue
            if w < min_w - 1e-9 or w > max_w + 1e-9:
                weight_caps_ok = False
                break

    constraints_status = _constraints_status(
        target_vol_annual=target_vol_annual,
        current_vol_annual=current_vol_annual,
        max_dd_ok=max_dd_ok,
        rc_block_targets=rc_block_targets,
        actual_rc_block=actual_rc_block,
        rc_caps_ok=rc_caps_ok,
        weight_caps_ok=weight_caps_ok,
        rb_corridor_pp=rb_corridor_pp,
    )

    portfolio_params = None
    if portfolio_metrics_summary:
        portfolio_params = {
            "cagr": round(portfolio_metrics_summary.get("cagr"), REPORT_DECIMALS) if portfolio_metrics_summary.get("cagr") is not None else None,
            "vol_annual": round(portfolio_metrics_summary.get("vol_annual"), REPORT_DECIMALS) if portfolio_metrics_summary.get("vol_annual") is not None else None,
            "max_drawdown": round(portfolio_metrics_summary.get("max_drawdown"), REPORT_DECIMALS) if portfolio_metrics_summary.get("max_drawdown") is not None else None,
            "sharpe": round(portfolio_metrics_summary.get("sharpe"), REPORT_DECIMALS) if portfolio_metrics_summary.get("sharpe") is not None else None,
            "beta_base": round(portfolio_metrics_summary.get("beta_portfolio"), REPORT_DECIMALS) if portfolio_metrics_summary.get("beta_portfolio") is not None else None,
        }
        if stress_report.get("factor_betas"):
            portfolio_params["factor_betas"] = {k: round(v, 4) for k, v in stress_report["factor_betas"].items()}

    # Per-window metrics section (3Y / 5Y / 10Y and others if present)
    windows: dict[str, Any] = {}
    if portfolio_windows:
        for label, pm in portfolio_windows.items():
            # pm already follows metrics_specification.md for portfolio (CAGR, vol_annual, Sharpe, Sortino, beta, Treynor, MaxDD, TTR)
            w_entry: dict[str, Any] = {
                "window_months": pm.get("window_months"),
                "cagr": pm.get("cagr"),
                "vol_annual": pm.get("vol_annual"),
                "sharpe": pm.get("sharpe"),
                "sortino": pm.get("sortino"),
                "beta_portfolio": pm.get("beta_portfolio"),
                "treynor": pm.get("treynor"),
                "max_drawdown": pm.get("max_drawdown"),
                "ttr_months": pm.get("ttr_months"),
                "recovered": pm.get("recovered"),
            }
            # Attach RC_vol by block summary if RC series for this window is available
            if rc_by_window and label in rc_by_window:
                rc_win = rc_by_window[label]
                rc_blocks = _rc_block_from_asset(rc_win, blocks)
                w_entry["RC_block"] = rc_blocks
            # Attach CSV filenames (relative to output_dir) for RC_vol and correlation matrix
            if rc_csv_by_window and label in rc_csv_by_window:
                w_entry["rc_vol_csv"] = rc_csv_by_window[label]
            if corr_csv_by_window and label in corr_csv_by_window:
                w_entry["correlation_matrix_csv"] = corr_csv_by_window[label]
            windows[label] = w_entry

    snapshot = {
        "timestamp": run_timestamp,
        "analysis_end": analysis_end,
        "final_weights_total": {t: round(w, REPORT_DECIMALS) for t, w in final_weights_total.items() if w > 0},
        "final_weights_risk_portfolio": risk_weights,
        "block_weights": _block_weights_from_total(final_weights_total, blocks),
        "RC_asset": rc_asset_top,
        "RC_block": rc_block_list,
        "constraints_status": constraints_status,
        "stress_suite_results": _stress_suite_results_for_snapshot(stress_report, portfolio_params),
    }
    if windows:
        snapshot["windows"] = windows
    return snapshot


def print_snapshot(snapshot: dict[str, Any]) -> None:
    """Print snapshot in a fixed, always identical format."""
    print("\n" + "=" * 60)
    print("SNAPSHOT")
    print("=" * 60)
    print("timestamp:", snapshot.get("timestamp", ""))
    print("analysis_end:", snapshot.get("analysis_end", ""))

    print("\n--- final_weights_total (включая кэш и tail) ---")
    for t in sorted(snapshot.get("final_weights_total", {}).keys(), key=lambda x: (-snapshot["final_weights_total"].get(x, 0), x)):
        print(f"  {t}: {snapshot['final_weights_total'][t]:.3f}")

    print("\n--- final_weights_risk_portfolio (без кэша) ---")
    for t in sorted(snapshot.get("final_weights_risk_portfolio", {}).keys(), key=lambda x: (-snapshot["final_weights_risk_portfolio"].get(x, 0), x)):
        print(f"  {t}: {snapshot['final_weights_risk_portfolio'][t]:.3f}")

    print("\n--- block_weights (Growth/Duration/Inflation/Liquidity/Tail) ---")
    for b in STRESS_BLOCK_NAMES:
        w = snapshot.get("block_weights", {}).get(b, 0)
        print(f"  {b}: {w:.3f}")

    print("\n--- RC_asset (топ-%d доноров риска) ---" % TOP_RC_N)
    for x in snapshot.get("RC_asset", []):
        print(f"  {x.get('ticker', '')}: {x.get('rc_pct', 0):.3f}")

    print("\n--- RC_block ---")
    for x in snapshot.get("RC_block", []):
        print(f"  {x.get('block', '')}: {x.get('rc_pct', 0):.3f}")

    print("\n--- constraints_status ---")
    for k, v in snapshot.get("constraints_status", {}).items():
        print(f"  {k}: {v}")

    stress = snapshot.get("stress_suite_results", {})
    print("\n--- stress_suite_results ---")
    print("  overall:", stress.get("overall", "N/A"))
    if stress.get("fail_reason_code"):
        print("  fail_reason_code:", stress["fail_reason_code"])
    print("  scenarios:")
    for s in stress.get("scenarios", []):
        viol = s.get("violations", [])
        pnl = s.get("portfolio_pnl_pct")
        pnl_str = f"{pnl:.4f}" if pnl is not None else "N/A"
        print(f"    {s.get('scenario_id', '')}: PnL={pnl_str} pass={s.get('pass')} violations={viol}")
    print("  portfolio_params:", stress.get("portfolio_params", {}))
    print("=" * 60)


def save_snapshot(snapshot: dict[str, Any], path: str | Path) -> Path:
    """Save snapshot to JSON. path can be file (e.g. snapshot_3y.json) or directory (then snapshot.json)."""
    p = Path(path)
    if p.suffix != ".json":
        p = p / "snapshot.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False, default=str)
    return p


def build_snapshot_assets(
    asset_metrics_by_window: dict[str, list[dict[str, Any]]],
    run_timestamp: str | None = None,
) -> dict[str, Any]:
    """
    Build snapshot for assets only (per-asset metrics, not in portfolio).
    asset_metrics_by_window: {"3y": [row per asset], "5y": [...], "10y": [...]}.
    """
    if run_timestamp is None:
        run_timestamp = datetime.now().isoformat()
    out: dict[str, Any] = {
        "timestamp": run_timestamp,
        "description": "Per-asset metrics by window (standalone, not in portfolio)",
    }
    for label, rows in asset_metrics_by_window.items():
        rounded = []
        for r in rows:
            row = {}
            for k, v in r.items():
                if isinstance(v, (int, float)) and not (v != v):
                    row[k] = round(float(v), REPORT_DECIMALS)
                else:
                    row[k] = v
            rounded.append(row)
        out[label] = rounded
    return out


def build_snapshot_for_window(
    window_label: str,
    window_months: int,
    final_weights_total: dict[str, float],
    blocks: dict[str, list[str]],
    cash_proxy_ticker: str,
    analysis_end: str,
    stress_report: dict[str, Any],
    *,
    final_weights_risk_portfolio: dict[str, float] | None = None,
    rc_series: pd.Series | None = None,
    portfolio_metrics: dict[str, Any] | None = None,
    rc_vol_csv: str | None = None,
    correlation_matrix_csv: str | None = None,
    constraints_status: dict[str, str] | None = None,
    run_timestamp: str | None = None,
    stress_portfolio_params: dict[str, Any] | None = None,
    analytics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build a single snapshot for one window (3y, 5y, or 10y). Contains everything for that horizon.
    """
    if run_timestamp is None:
        run_timestamp = datetime.now().isoformat()
    if final_weights_risk_portfolio is None:
        risk_weights = {t: w for t, w in final_weights_total.items() if t != cash_proxy_ticker and w > 0}
        total_risk = sum(risk_weights.values())
        if total_risk > 0:
            risk_weights = {t: w / total_risk for t, w in risk_weights.items()}
        risk_weights = {t: round(w, REPORT_DECIMALS) for t, w in risk_weights.items() if w > 0}
    else:
        risk_weights = {t: round(w, REPORT_DECIMALS) for t, w in final_weights_risk_portfolio.items() if w > 0}
    rc_asset_top = _rc_asset_top(rc_series) if rc_series is not None else []
    rc_block_list = _rc_block_from_asset(rc_series, blocks) if rc_series is not None else []
    metrics = None
    if portfolio_metrics:
        metrics = {
            k: round(v, REPORT_DECIMALS) if isinstance(v, (int, float)) and not (v != v) else v
            for k, v in portfolio_metrics.items()
        }
    stress_section = _stress_suite_results_for_snapshot(stress_report, stress_portfolio_params or metrics)
    snapshot = {
        "timestamp": run_timestamp,
        "analysis_end": analysis_end,
        "window_label": window_label,
        "window_months": window_months,
        "final_weights_total": {t: round(w, REPORT_DECIMALS) for t, w in final_weights_total.items() if w > 0},
        "final_weights_risk_portfolio": risk_weights,
        "block_weights": _block_weights_from_total(final_weights_total, blocks),
        "RC_asset": rc_asset_top,
        "RC_block": rc_block_list,
        "constraints_status": constraints_status or {},
        "stress_suite_results": stress_section,
        "metrics": metrics,
        "rc_vol_csv": rc_vol_csv,
        "correlation_matrix_csv": correlation_matrix_csv,
    }
    if analytics:
        snapshot["analytics"] = analytics
    return snapshot


def _fmt_val(v: Any) -> str:
    """Format a value for text report (handle NaN, floats, dicts)."""
    if v is None:
        return "—"
    if isinstance(v, float) and v != v:  # NaN
        return "—"
    if isinstance(v, str) and v.upper() == "NAN":
        return "—"
    if isinstance(v, (int, float)):
        return f"{v:.3f}" if isinstance(v, float) else str(v)
    if isinstance(v, dict):
        return ", ".join(f"{k}: {_fmt_val(x)}" for k, x in v.items())
    return str(v)


def _format_window_snapshot_text(label: str, data: dict[str, Any]) -> str:
    """Format one window snapshot (3y/5y/10y) as text."""
    lines = [
        "",
        "=" * 60,
        f"WINDOW {label.upper()} (analysis_end: {data.get('analysis_end', '')})",
        "=" * 60,
        "",
        "--- final_weights_total ---",
    ]
    w_total = data.get("final_weights_total") or {}
    for t in sorted(w_total.keys(), key=lambda x: (-w_total.get(x, 0), x)):
        lines.append(f"  {t}: {_fmt_val(w_total[t])}")
    lines.extend(["", "--- block_weights ---"])
    for b, w in (data.get("block_weights") or {}).items():
        lines.append(f"  {b}: {_fmt_val(w)}")
    lines.extend(["", "--- RC_asset (top 5) ---"])
    for x in data.get("RC_asset") or []:
        lines.append(f"  {x.get('ticker', '')}: {_fmt_val(x.get('rc_pct'))}")
    lines.extend(["", "--- RC_block ---"])
    for x in data.get("RC_block") or []:
        lines.append(f"  {x.get('block', '')}: {_fmt_val(x.get('rc_pct'))}")
    lines.extend(["", "--- constraints_status ---"])
    for k, v in (data.get("constraints_status") or {}).items():
        lines.append(f"  {k}: {v}")
    metrics = data.get("metrics") or {}
    if metrics:
        lines.extend(["", "--- metrics ---"])
        for k in ("cagr", "vol_annual", "sharpe", "sortino", "beta_portfolio", "treynor", "max_drawdown", "ttr_months"):
            if k in metrics:
                lines.append(f"  {k}: {_fmt_val(metrics[k])}")
    stress = data.get("stress_suite_results") or {}
    lines.extend(["", "--- stress ---"])
    lines.append(f"  overall: {stress.get('overall', '—')}")
    analytics = data.get("analytics") or {}
    if analytics:
        lines.extend(["", "--- analytics (summary) ---"])
        for k in ("rolling_sharpe_36m", "rolling_sortino_36m", "var_95", "es_95", "eee_10pct"):
            if k in analytics:
                lines.append(f"  {k}: {_fmt_val(analytics[k])}")
    return "\n".join(lines)


def _format_assets_snapshot_text(data: dict[str, Any]) -> str:
    """Format snapshot_assets as text (per-window tables)."""
    lines = [
        "",
        "=" * 60,
        "ASSETS (per-asset metrics by window, standalone)",
        "=" * 60,
    ]
    for label in ("3y", "5y", "10y"):
        rows = data.get(label)
        if not rows:
            continue
        lines.extend(["", f"--- Window {label} ---", ""])
        # Header
        if rows:
            keys = [k for k in rows[0].keys() if k != "ticker"]
            lines.append("ticker\t" + "\t".join(keys))
            for r in rows:
                ticker = r.get("ticker", "")
                vals = "\t".join(_fmt_val(r.get(k)) for k in keys)
                lines.append(f"{ticker}\t{vals}")
    return "\n".join(lines)


def write_report_txt(output_dir: str | Path) -> Path:
    """
    Load snapshot_3y, 5y, 10y and snapshot_assets from output_dir,
    format into a single text report, and write output_dir/report.txt.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    report_lines = [
        "Portfolio Snapshot Report",
        "Generated from snapshot_3y.json, snapshot_5y.json, snapshot_10y.json, snapshot_assets.json",
        "",
    ]
    for label, fname in [("3y", "snapshot_3y.json"), ("5y", "snapshot_5y.json"), ("10y", "snapshot_10y.json")]:
        path = out / fname
        if path.exists():
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                report_lines.append(_format_window_snapshot_text(label, data))
            except Exception:
                report_lines.append(f"\n[Could not load {fname}]\n")
    assets_path = out / "snapshot_assets.json"
    if assets_path.exists():
        try:
            with open(assets_path, encoding="utf-8") as f:
                data = json.load(f)
            report_lines.append(_format_assets_snapshot_text(data))
        except Exception:
            report_lines.append("\n[Could not load snapshot_assets.json]\n")
    report_path = out / "report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    return report_path


def _fmt_val_html(v: Any) -> str:
    """Format value for HTML (escape and handle NaN)."""
    s = _fmt_val(v)
    return html.escape(s)


def _format_window_snapshot_html(label: str, data: dict[str, Any]) -> str:
    """Format one window snapshot as HTML section with tables."""
    analysis_end = data.get("analysis_end", "")
    parts = [
        f'<section class="window-section" id="win-{html.escape(label)}">',
        f'<h2>Window {html.escape(label).upper()} <span class="meta">(analysis_end: {_fmt_val_html(analysis_end)})</span></h2>',
    ]
    # Weights table
    w_total = data.get("final_weights_total") or {}
    if w_total:
        rows = "".join(
            f"<tr><td>{html.escape(t)}</td><td>{_fmt_val_html(w_total[t])}</td></tr>"
            for t in sorted(w_total.keys(), key=lambda x: (-w_total.get(x, 0), x))
        )
        parts.append(
            '<table><caption>Final weights (total)</caption><thead><tr><th>Ticker</th><th>Weight</th></tr></thead><tbody>' + rows + "</tbody></table>"
        )
    # Block weights
    block_weights = data.get("block_weights") or {}
    if block_weights:
        rows = "".join(f"<tr><td>{html.escape(b)}</td><td>{_fmt_val_html(w)}</td></tr>" for b, w in block_weights.items())
        parts.append('<table><caption>Block weights</caption><thead><tr><th>Block</th><th>Weight</th></tr></thead><tbody>' + rows + "</tbody></table>")
    # RC asset
    rc_asset = data.get("RC_asset") or []
    if rc_asset:
        rows = "".join(f"<tr><td>{html.escape(str(x.get('ticker', '')))}</td><td>{_fmt_val_html(x.get('rc_pct'))}</td></tr>" for x in rc_asset)
        parts.append('<table><caption>RC by asset (top)</caption><thead><tr><th>Ticker</th><th>RC %</th></tr></thead><tbody>' + rows + "</tbody></table>")
    # RC block
    rc_block = data.get("RC_block") or []
    if rc_block:
        rows = "".join(f"<tr><td>{html.escape(str(x.get('block', '')))}</td><td>{_fmt_val_html(x.get('rc_pct'))}</td></tr>" for x in rc_block)
        parts.append('<table><caption>RC by block</caption><thead><tr><th>Block</th><th>RC %</th></tr></thead><tbody>' + rows + "</tbody></table>")
    # Constraints
    constraints = data.get("constraints_status") or {}
    if constraints:
        rows = "".join(f"<tr><td>{html.escape(k)}</td><td class=\"status-{html.escape(v.lower())}\">{html.escape(v)}</td></tr>" for k, v in constraints.items())
        parts.append('<table><caption>Constraints</caption><thead><tr><th>Constraint</th><th>Status</th></tr></thead><tbody>' + rows + "</tbody></table>")
    # Metrics
    metrics = data.get("metrics") or {}
    if metrics:
        metric_keys = ("cagr", "vol_annual", "sharpe", "sortino", "beta_portfolio", "treynor", "max_drawdown", "ttr_months")
        rows = "".join(f"<tr><td>{html.escape(k)}</td><td>{_fmt_val_html(metrics.get(k))}</td></tr>" for k in metric_keys if k in metrics)
        parts.append('<table><caption>Portfolio metrics</caption><thead><tr><th>Metric</th><th>Value</th></tr></thead><tbody>' + rows + "</tbody></table>")
    # Stress
    stress = data.get("stress_suite_results") or {}
    overall = stress.get("overall", "—")
    parts.append(f'<p class="stress-overall"><strong>Stress:</strong> <span class="status-{html.escape(str(overall).lower())}">{_fmt_val_html(overall)}</span></p>')
    # Analytics summary
    analytics = data.get("analytics") or {}
    if analytics:
        rows = []
        for k in ("rolling_sharpe_36m", "rolling_sortino_36m", "var_95", "es_95", "eee_10pct"):
            if k in analytics:
                rows.append(f"<tr><td>{html.escape(k)}</td><td>{_fmt_val_html(analytics[k])}</td></tr>")
        if rows:
            parts.append('<table><caption>Analytics</caption><thead><tr><th>Metric</th><th>Value</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table>")
    parts.append("</section>")
    return "\n".join(parts)


def _format_assets_snapshot_html(data: dict[str, Any]) -> str:
    """Format snapshot_assets as HTML section with tables per window."""
    parts = [
        '<section class="assets-section" id="assets">',
        "<h2>Assets (per-asset metrics by window)</h2>",
    ]
    for label in ("3y", "5y", "10y"):
        rows_data = data.get(label)
        if not rows_data:
            continue
        keys = [k for k in rows_data[0].keys() if k != "ticker"]
        header_cells = "".join(f"<th>{html.escape(k)}</th>" for k in ["ticker"] + keys)
        body_rows = []
        for r in rows_data:
            ticker = html.escape(str(r.get("ticker", "")))
            cells = "".join(f"<td>{_fmt_val_html(r.get(k))}</td>" for k in keys)
            body_rows.append(f"<tr><td>{ticker}</td>{cells}</tr>")
        parts.append(
            f'<table class="assets-table"><caption>Window {html.escape(label)}</caption>'
            f"<thead><tr>{header_cells}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"
        )
    parts.append("</section>")
    return "\n".join(parts)


HTML_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Portfolio Snapshot Report</title>
<style>
:root { --bg: #f8f9fa; --card: #fff; --border: #dee2e6; --text: #212529; --muted: #6c757d; --pass: #198754; --fail: #dc3545; }
* { box-sizing: border-box; }
body { font-family: system-ui, -apple-system, Segoe UI, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 1rem 2rem 2rem; line-height: 1.5; }
h1 { font-size: 1.5rem; margin-bottom: 0.25rem; }
.subtitle { color: var(--muted); font-size: 0.9rem; margin-bottom: 1.5rem; }
nav { margin-bottom: 1.5rem; }
nav a { margin-right: 1rem; color: #0d6efd; text-decoration: none; }
nav a:hover { text-decoration: underline; }
section { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 1rem 1.5rem; margin-bottom: 1.5rem; break-inside: avoid; }
section h2 { font-size: 1.2rem; margin-top: 0; margin-bottom: 1rem; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; }
section h2 .meta { font-weight: normal; color: var(--muted); font-size: 0.9rem; }
table { width: 100%; max-width: 32rem; border-collapse: collapse; margin-bottom: 1rem; }
table caption { text-align: left; font-weight: 600; margin-bottom: 0.25rem; font-size: 0.9rem; }
th, td { border: 1px solid var(--border); padding: 0.35rem 0.6rem; text-align: left; }
th { background: var(--bg); font-weight: 600; }
.status-pass { color: var(--pass); }
.status-fail, [class^="status-fail"] { color: var(--fail); }
.stress-overall { margin-bottom: 0.5rem; }
.assets-table { max-width: none; }
@media print { body { background: #fff; padding: 0.5rem; } section { break-inside: avoid; box-shadow: none; } nav { display: none; } }
</style>
</head>
<body>
"""

HTML_TAIL = """
</body>
</html>
"""


def write_report_html(output_dir: str | Path) -> Path:
    """
    Load snapshot_3y, 5y, 10y and snapshot_assets from output_dir,
    format into a single HTML report (board), and write output_dir/report.html.
    Open in browser; use Print → Save as PDF for PDF.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    chunks = [HTML_HEAD]
    chunks.append("<h1>Portfolio Snapshot Report</h1>")
    chunks.append('<p class="subtitle">Generated from snapshot_3y.json, snapshot_5y.json, snapshot_10y.json, snapshot_assets.json</p>')
    chunks.append('<nav><a href="#win-3y">3Y</a> <a href="#win-5y">5Y</a> <a href="#win-10y">10Y</a> <a href="#assets">Assets</a></nav>')
    for label, fname in [("3y", "snapshot_3y.json"), ("5y", "snapshot_5y.json"), ("10y", "snapshot_10y.json")]:
        path = out / fname
        if path.exists():
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                chunks.append(_format_window_snapshot_html(label, data))
            except Exception:
                chunks.append(f'<section><p>Could not load {html.escape(fname)}</p></section>')
    assets_path = out / "snapshot_assets.json"
    if assets_path.exists():
        try:
            with open(assets_path, encoding="utf-8") as f:
                data = json.load(f)
            chunks.append(_format_assets_snapshot_html(data))
        except Exception:
            chunks.append("<section><p>Could not load snapshot_assets.json</p></section>")
    chunks.append(HTML_TAIL)
    report_path = out / "report.html"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(chunks))
    return report_path
