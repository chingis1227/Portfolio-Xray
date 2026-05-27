"""
Final optimization/report snapshot: one object, same print and save.
Used by run_optimization.py and run_report.py.

Production workflow (single source of truth with run_result.json):
  - Only hard stop: FAIL_DATA (invalid config, missing/NaN data, covariance not computable). Weights are always written otherwise.
  - Stress suite: diagnostic-only (DIAG_*); mandate MaxDD on full overlapping history in run_optimization (FAIL_MANDATE).
  - RC_vol: diagnostic in metrics/stress only; not a cap gate in snapshot constraints.
  - Soft/diagnostic: Baseline coverage, constraints_status (target_vol, max_dd, rc_caps legacy slot, weight_caps) for transparency.
  - Report-only: target_nominal_return_annual (comparison with realized CAGR only; not an optimization constraint).
"""
from __future__ import annotations

import hashlib
import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.config_schema import PortfolioConfig

from src.portfolio_xray import (
    build_portfolio_xray_v2,
    format_portfolio_xray_html,
    format_portfolio_xray_text,
    load_portfolio_windows_from_dir,
)
from src.risk_contrib import rc_vol_window
from src.stress import crisis_replay_summary_from_paths
from src.windows import slice_window

REPORT_DECIMALS = 3
TOP_RC_N = 5
CANDIDATE_CONFIG_FINGERPRINT_KEY = "candidate_config_fingerprint"


def _normalize_fingerprint_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _normalize_fingerprint_value(v) for k, v in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_normalize_fingerprint_value(v) for v in value]
    if isinstance(value, float):
        return round(value, 12)
    return value


def build_candidate_config_fingerprint_payload(cfg: PortfolioConfig) -> dict[str, Any]:
    """
    Canonical inputs for candidate freshness beyond analysis_end (RM-976 / G2).

    Hashes investor currency, ticker universe, risk budgeting, and weight bound fields only.
    """
    tickers = sorted(
        {str(t).strip().upper() for t in (cfg.tickers or []) if isinstance(t, str) and str(t).strip()}
    )
    return _normalize_fingerprint_value(
        {
            "investor_currency": str(cfg.investor_currency or "").strip().upper(),
            "tickers": tickers,
            "risk_budgeting": dict(cfg.risk_budgeting or {}),
            "min_single_security_weight_pct": cfg.min_single_security_weight_pct,
            "max_single_security_weight_pct": cfg.max_single_security_weight_pct,
        }
    )


def compute_candidate_config_fingerprint(cfg: PortfolioConfig) -> str:
    """SHA-256 of canonical JSON fingerprint payload."""
    payload = build_candidate_config_fingerprint_payload(cfg)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def snapshot_config_fingerprint(snapshot: dict[str, Any] | None) -> str | None:
    if not snapshot:
        return None
    fp = snapshot.get(CANDIDATE_CONFIG_FINGERPRINT_KEY)
    return str(fp) if fp else None


def attach_candidate_config_fingerprint(
    snapshot: dict[str, Any],
    fingerprint: str,
) -> dict[str, Any]:
    out = dict(snapshot)
    out[CANDIDATE_CONFIG_FINGERPRINT_KEY] = fingerprint
    return out


def _rc_asset_top(rc_series: pd.Series, top_n: int = TOP_RC_N) -> list[dict[str, Any]]:
    """Top N assets by RC (percentage)."""
    if rc_series is None or rc_series.empty:
        return []
    s = rc_series.dropna().sort_values(ascending=False).head(top_n)
    return [{"ticker": str(t), "rc_pct": round(float(v), REPORT_DECIMALS)} for t, v in s.items()]


def rc_asset_rows_from_series(rc_series: pd.Series | None) -> list[dict[str, Any]]:
    """Full per-asset RC_vol rows for JSON contracts (snapshot / site_api consumers)."""
    if rc_series is None or rc_series.empty:
        return []
    s = rc_series.dropna().sort_values(ascending=False)
    return [{"ticker": str(t), "rc_pct": round(float(v), REPORT_DECIMALS)} for t, v in s.items()]


def _constraints_status(
    *,
    target_vol_annual: float | None,
    current_vol_annual: float | None,
    max_dd_ok: bool | None,
    rc_caps_ok: bool | None,
    weight_caps_ok: bool | None,
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


def _stress_results_mirror_for_snapshot(stress_report: dict[str, Any]) -> dict[str, Any]:
    """Compact Block 3.2 mirror (envelope + gate mode) for snapshot and comparison consumers."""
    block = stress_report.get("stress_results_v1")
    if not isinstance(block, dict):
        return {}
    envelope = block.get("envelope")
    return {
        "version": block.get("version"),
        "loss_gate_mode": block.get("loss_gate_mode"),
        "envelope": envelope if isinstance(envelope, dict) else {},
    }


def _hedge_gap_analysis_v1_mirror_for_snapshot(stress_report: dict[str, Any]) -> dict[str, Any]:
    """
    Compact Block 3.3 mirror for snapshot consumers.

    Keep it small: summary + linkage fields only (avoid large per-asset lists).
    """
    block = stress_report.get("hedge_gap_analysis_v1")
    if not isinstance(block, dict) or block.get("version") != "hedge_gap_analysis_v1":
        return {}
    summary = block.get("summary") if isinstance(block.get("summary"), dict) else {}
    main = summary.get("main_hedge_gap") if isinstance(summary.get("main_hedge_gap"), dict) else None
    out: dict[str, Any] = {
        "version": block.get("version"),
        "loss_gate_mode": block.get("loss_gate_mode"),
        "diagnosis_method": block.get("diagnosis_method"),
        "n_risk_types": block.get("n_risk_types"),
        "summary": {
            "weakest_protection_area": summary.get("weakest_protection_area"),
            "strongest_protection_area": summary.get("strongest_protection_area"),
            "main_hedge_gap": (
                {
                    "risk_type": main.get("risk_type"),
                    "linked_scenario_id": main.get("linked_scenario_id"),
                    "offset_coverage_ratio": main.get("offset_coverage_ratio"),
                    "portfolio_loss_pct": main.get("portfolio_loss_pct"),
                }
                if isinstance(main, dict)
                else None
            ),
            "data_quality_warnings": summary.get("data_quality_warnings")
            if isinstance(summary.get("data_quality_warnings"), list)
            else [],
        },
    }
    diag = summary.get("diagnosis_summary_en")
    if isinstance(diag, str) and diag.strip():
        out["summary"]["diagnosis_summary_en"] = diag.strip()
    return out


def _stress_suite_results_for_snapshot(stress_report: dict[str, Any], portfolio_params: dict[str, Any] | None) -> dict[str, Any]:
    """Format stress_suite_results section; include per-scenario violations and portfolio_params."""
    overall = stress_report.get("status", "N/A")
    fail_reason = stress_report.get("fail_reason_code") or stress_report.get("skip_reason")

    scenarios_out = []
    for s in stress_report.get("scenario_results", []):
        # Mandate stress gate for synthetics: portfolio loss vs MaxDD only (RC is diagnostic).
        violations = []
        if not s.get("loss_ok", True):
            violations.append("loss")
        rc_flags: list[str] = []
        scenarios_out.append({
            "scenario_id": s.get("scenario_id"),
            "portfolio_pnl_pct": round(s.get("portfolio_pnl_pct", 0), 4),
            "violations": violations,
            "rc_flags": rc_flags,
            "pass": s.get("pass", True),
            "synthetic_assumptions": dict(s.get("synthetic_assumptions") or {})
            if isinstance(s.get("synthetic_assumptions"), dict)
            else {},
        })

    episode_paths = stress_report.get("historical_episode_paths")
    crisis_summary = crisis_replay_summary_from_paths(
        episode_paths if isinstance(episode_paths, list) else None
    )
    historical_methodology = stress_report.get("historical_methodology")
    return {
        "overall": overall,
        "fail_reason_code": fail_reason,
        "failed_scenario": stress_report.get("failed_scenario"),
        "scenarios": scenarios_out,
        "historical": stress_report.get("historical_results", []),
        "portfolio_params": portfolio_params or {},
        "scorecard": stress_report.get("stress_scorecard_v1") or {},
        "conclusions": stress_report.get("stress_conclusions") or {},
        "hedge_gap_analysis": stress_report.get("hedge_gap_analysis") or {},
        "hedge_gap_analysis_v1": _hedge_gap_analysis_v1_mirror_for_snapshot(stress_report),
        "historical_methodology": historical_methodology
        if isinstance(historical_methodology, dict)
        else {},
        "crisis_replay_summary": crisis_summary,
        "stress_results": _stress_results_mirror_for_snapshot(stress_report),
    }


def build_snapshot(
    final_weights_total: dict[str, float],
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
    rc_caps_ok: bool | None = True,
    weight_caps_ok: bool | None = None,
    min_single_security_weight_pct: float | None = None,
    max_single_security_weight_pct: float | None = None,
    portfolio_metrics_summary: dict[str, Any] | None = None,
    run_timestamp: str | None = None,
    # Optional per-window portfolio metrics and RC/correlation outputs (3Y/5Y/10Y), per metrics_specification.md Section11
    portfolio_windows: dict[str, dict[str, Any]] | None = None,
    rc_by_window: dict[str, pd.Series] | None = None,
    rc_csv_by_window: dict[str, str] | None = None,
    corr_csv_by_window: dict[str, str] | None = None,
    resolved_config: dict[str, Any] | None = None,
    candidate_config_fingerprint: str | None = None,
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
        rc_caps_ok=rc_caps_ok,
        weight_caps_ok=weight_caps_ok,
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
        "RC_asset": rc_asset_top,
        "constraints_status": constraints_status,
        "stress_suite_results": _stress_suite_results_for_snapshot(stress_report, portfolio_params),
    }
    if windows:
        snapshot["windows"] = windows
    if resolved_config is not None:
        snapshot["resolved_config"] = resolved_config
    if candidate_config_fingerprint:
        snapshot[CANDIDATE_CONFIG_FINGERPRINT_KEY] = candidate_config_fingerprint
    return snapshot


def print_snapshot(snapshot: dict[str, Any]) -> None:
    """Print snapshot in a fixed, always identical format."""
    print("\n" + "=" * 60)
    print("SNAPSHOT")
    print("=" * 60)
    print("timestamp:", snapshot.get("timestamp", ""))
    print("analysis_end:", snapshot.get("analysis_end", ""))

    print("\n--- final_weights_total (including cash and tail) ---")
    for t in sorted(snapshot.get("final_weights_total", {}).keys(), key=lambda x: (-snapshot["final_weights_total"].get(x, 0), x)):
        print(f"  {t}: {snapshot['final_weights_total'][t]:.3f}")

    print("\n--- final_weights_risk_portfolio (ex cash) ---")
    for t in sorted(snapshot.get("final_weights_risk_portfolio", {}).keys(), key=lambda x: (-snapshot["final_weights_risk_portfolio"].get(x, 0), x)):
        print(f"  {t}: {snapshot['final_weights_risk_portfolio'][t]:.3f}")

    print("\n--- RC_asset (top-%d risk contributors) ---" % TOP_RC_N)
    for x in snapshot.get("RC_asset", []):
        print(f"  {x.get('ticker', '')}: {x.get('rc_pct', 0):.3f}")

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
    candidate_config_fingerprint: str | None = None,
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
    rc_asset_all = rc_asset_rows_from_series(rc_series) if rc_series is not None else []
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
        "RC_asset": rc_asset_top,
        "constraints_status": constraints_status or {},
        "stress_suite_results": stress_section,
        "metrics": metrics,
        "rc_vol_csv": rc_vol_csv,
        "correlation_matrix_csv": correlation_matrix_csv,
    }
    if rc_asset_all:
        snapshot["RC_asset_all"] = rc_asset_all
    if analytics:
        snapshot["analytics"] = analytics
    if candidate_config_fingerprint:
        snapshot[CANDIDATE_CONFIG_FINGERPRINT_KEY] = candidate_config_fingerprint
    return snapshot


def _fmt_val(v: Any) -> str:
    """Format a value for text report (handle NaN, floats, dicts)."""
    if v is None:
        return " - "
    if isinstance(v, float) and v != v:  # NaN
        return " - "
    if isinstance(v, str) and v.upper() == "NAN":
        return " - "
    if isinstance(v, (int, float)):
        return f"{v:.3f}" if isinstance(v, float) else str(v)
    if isinstance(v, dict):
        return ", ".join(f"{k}: {_fmt_val(x)}" for k, x in v.items())
    return str(v)


def _fmt_ratio(v: Any) -> str:
    """Format fractional value as percentage for human-readable reports."""
    if v is None:
        return " - "
    if isinstance(v, float) and v != v:
        return " - "
    try:
        return f"{float(v):.1%}"
    except Exception:
        return _fmt_val(v)


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
        lines.append(f"  {t}: {_fmt_ratio(w_total[t])}")
    lines.extend(["", "--- RC_asset (top 5) ---"])
    for x in data.get("RC_asset") or []:
        lines.append(f"  {x.get('ticker', '')}: {_fmt_ratio(x.get('rc_pct'))}")
    lines.extend(["", "--- constraints_status ---"])
    for k, v in (data.get("constraints_status") or {}).items():
        lines.append(f"  {k}: {v}")
    metrics = data.get("metrics") or {}
    if metrics:
        lines.extend(["", "--- metrics ---"])
        for k in (
            "cagr",
            "vol_annual",
            "sharpe",
            "sortino",
            "beta_portfolio",
            "corr_base",
            "downside_beta",
            "upside_beta",
            "skewness",
            "kurtosis",
            "treynor",
            "max_drawdown",
            "ttr_months",
        ):
            if k in metrics:
                if k in ("cagr", "vol_annual", "max_drawdown"):
                    lines.append(f"  {k}: {_fmt_ratio(metrics[k])}")
                else:
                    lines.append(f"  {k}: {_fmt_val(metrics[k])}")
        mq = metrics.get("metric_quality")
        if isinstance(mq, dict) and mq:
            lines.append(
                f"  metric_quality: n_obs={mq.get('n_obs')}, freq={mq.get('frequency')}, "
                f"bench={mq.get('benchmark_ticker')}, rf={mq.get('risk_free_source')}"
            )
    stress = data.get("stress_suite_results") or {}
    lines.extend(["", "--- stress ---"])
    lines.append(f"  overall: {stress.get('overall', ' - ')}")
    analytics = data.get("analytics") or {}
    if analytics:
        lines.extend(["", "--- analytics (summary) ---"])
        tail_risk = analytics.get("tail_risk")
        if isinstance(tail_risk, dict) and tail_risk.get("metric_available"):
            lines.append(
                f"  tail_risk: daily historical VaR/ES, window {tail_risk.get('window_label')}, "
                f"n_obs={tail_risk.get('n_obs')}"
            )
            for k in ("var_95", "var_99", "es_95", "es_99"):
                if tail_risk.get(k) is not None:
                    lines.append(f"  {k}: {_fmt_ratio(tail_risk[k])}")
        else:
            for k in ("var_95", "es_95"):
                if k in analytics and analytics[k] is not None:
                    lines.append(f"  {k}: {_fmt_ratio(analytics[k])}")
        if analytics.get("eee_10pct") is not None:
            lines.append(f"  eee_10pct: {_fmt_val(analytics['eee_10pct'])}%")
        for k in (
            "rolling_sharpe_36m",
            "rolling_sortino_36m",
            "rolling_beta_36m",
            "rolling_beta_12m",
            "rolling_correlation_36m",
            "rolling_correlation_12m",
        ):
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
                vals = []
                for k in keys:
                    if k in ("cagr", "vol_annual", "max_drawdown"):
                        vals.append(_fmt_ratio(r.get(k)))
                    elif k in ("skewness", "kurtosis", "sharpe", "sortino", "beta_base", "beta_local", "treynor", "window_months", "ttr_months"):
                        vals.append(_fmt_val(r.get(k)))
                    else:
                        vals.append(_fmt_val(r.get(k)))
                vals = "\t".join(vals)
                lines.append(f"{ticker}\t{vals}")
    return "\n".join(lines)


def _load_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _correlation_matrix_from_snapshot(out: Path, snapshot: dict[str, Any]) -> tuple[pd.DataFrame | None, str | None]:
    """
    Load the primary-window correlation matrix referenced by snapshot JSON.

    `site_api` / JSON-only runs may not write CSV, so this is best-effort only;
    runtime callers can pass an in-memory matrix directly to `build_portfolio_xray_v2`.
    """
    ref = snapshot.get("correlation_matrix_csv") if isinstance(snapshot, dict) else None
    if not ref:
        return None, None
    path = out / "results_csv" / str(ref)
    if not path.is_file():
        return None, str(ref)
    try:
        frame = pd.read_csv(path, index_col=0)
    except Exception:
        return None, str(ref)
    if frame.empty:
        return None, str(ref)
    return frame, str(ref)


def _xray_summary_from_output_dir(out: Path) -> dict[str, Any] | None:
    metadata = _load_json_if_exists(out / "run_metadata.json") or {}
    snapshot = _load_json_if_exists(out / "snapshot_10y.json") or _load_json_if_exists(out / "snapshot_5y.json") or {}
    stress_report = _load_json_if_exists(out / "stress_report.json")
    analysis_setup = metadata.get("analysis_setup")
    if not isinstance(analysis_setup, dict) and not snapshot:
        return None
    csv_dir = out / "results_csv"
    portfolio_windows = load_portfolio_windows_from_dir(out)
    corr_matrix, corr_ref = _correlation_matrix_from_snapshot(out, snapshot)
    xray = build_portfolio_xray_v2(
        analysis_setup=analysis_setup if isinstance(analysis_setup, dict) else None,
        weights=snapshot.get("final_weights_total") if isinstance(snapshot, dict) else None,
        rc_asset=snapshot.get("RC_asset") if isinstance(snapshot, dict) else None,
        stress_report=stress_report,
        portfolio_valid=metadata.get("portfolio_valid") if isinstance(metadata, dict) else None,
        portfolio_metrics=snapshot.get("metrics") if isinstance(snapshot, dict) else None,
        portfolio_windows=portfolio_windows or None,
        portfolio_analytics=snapshot.get("analytics") if isinstance(snapshot, dict) else None,
        drawdown_structure=snapshot.get("drawdown_structure") if isinstance(snapshot, dict) else None,
        correlation_matrix=corr_matrix,
        correlation_matrix_ref=corr_ref,
        output_dir_final=out,
        output_dir_csv=csv_dir if csv_dir.is_dir() else None,
    )
    try:
        with open(out / "portfolio_xray.json", "w", encoding="utf-8") as f:
            json.dump(xray, f, indent=2, ensure_ascii=False, default=str)
    except Exception:
        pass
    return xray


def _format_xray_summary_html(summary: dict[str, Any]) -> str:
    if summary.get("version") == "portfolio_xray_v2":
        return format_portfolio_xray_html(summary)

    setup = summary.get("analysis_setup_summary") or {}
    alloc = summary.get("asset_allocation_summary") or {}
    risk = summary.get("risk_contribution_summary") or {}
    verdict = summary.get("portfolio_diagnostic_verdict") or {}

    def _item_rows(items: list[dict[str, Any]]) -> str:
        return "".join(
            "<tr><td>"
            + html.escape(str(row.get("ticker", "")))
            + "</td><td>"
            + html.escape(_fmt_ratio(row.get("value")))
            + "</td></tr>"
            for row in items
        )

    parts = [
        '<section class="xray-summary-section" id="xray-summary">',
        "<h2>Portfolio X-Ray Summary</h2>",
        "<p><strong>Analyzed portfolio:</strong> role="
        + html.escape(str(setup.get("portfolio_role", "unknown")))
        + "; weight_source="
        + html.escape(str(setup.get("weight_source", "unknown")))
        + "; recommendation_status="
        + html.escape(str(setup.get("recommendation_status", "unknown")))
        + ".</p>",
        "<p><strong>Setup:</strong> input_case="
        + html.escape(str(setup.get("product_input_case", "unknown")))
        + "; currency="
        + html.escape(str(setup.get("investor_currency", "n/a")))
        + "; benchmark="
        + html.escape(str(setup.get("base_benchmark_ticker", "n/a")))
        + "; cash_proxy="
        + html.escape(str(setup.get("cash_proxy_ticker", "n/a")))
        + "; frequency="
        + html.escape(str(setup.get("return_frequency", "n/a")))
        + ".</p>",
    ]
    alloc_rows = _item_rows(alloc.get("top_holdings") or [])
    if alloc_rows:
        parts.append(
            _html_table_section(
                "<table><caption>Asset Allocation Summary</caption><thead><tr><th>Ticker</th><th>Weight</th></tr></thead><tbody>"
                + alloc_rows
                + "</tbody></table>"
            )
        )
    risk_rows = _item_rows(risk.get("top_rc_contributors") or [])
    if risk_rows:
        parts.append(
            _html_table_section(
                "<table><caption>Risk Contribution Summary</caption><thead><tr><th>Ticker</th><th>RC_vol</th></tr></thead><tbody>"
                + risk_rows
                + "</tbody></table>"
            )
        )
    parts.append("<h3>Portfolio Diagnostic Verdict</h3>")
    parts.append("<ul>")
    for line in verdict.get("lines") or []:
        parts.append("<li>" + html.escape(str(line)) + "</li>")
    parts.append("</ul>")
    parts.append("</section>")
    return "\n".join(parts)


def _format_data_policy_text(data: dict[str, Any]) -> str:
    """Format Data Policy / Backtest Mode section for text report."""
    lines = [
        "============================================================",
        "DATA POLICY / BACKTEST MODE",
        "============================================================",
        "",
        "backtest_mode: " + str(data.get("backtest_mode", " - ")),
        "join_policy (for cov/RC/beta): " + str(data.get("join_policy_cov_rc", "inner join")),
        "",
    ]
    inner = data.get("inner_join_months_used_for_risk")
    if inner is not None:
        lines.append("inner_join_months_used_for_risk (Sigma/RC): " + str(inner))
        if inner < 36:
            lines.append("  (warning: < 36 months; risk estimates may be noisy)")
        lines.append("")
    n_redist = data.get("n_months_redistributed")
    n_cash = data.get("n_months_cash_fallback")
    if n_redist is not None:
        lines.append("months with NaN redistribution (among risk assets): " + str(n_redist))
    if n_cash is not None:
        lines.append("months with excess weight to cash (RC caps / gating): " + str(n_cash))
    if n_redist is not None or n_cash is not None:
        lines.append("")
    fam = data.get("first_available_month") or {}
    if fam:
        lines.append("first_available_month (per ticker, young ETF inclusion):")
        for t in sorted(fam.keys()):
            lines.append("  " + t + ": " + str(fam[t]))
        lines.append("")
    lines.append("")
    return "\n".join(lines)


def _format_robustness_text(data: dict[str, Any]) -> str:
    """Format Dual-Horizon Robustness section for text report."""
    lines = [
        "============================================================",
        "DUAL-HORIZON ROBUSTNESS (10Y primary + 5Y secondary validation)",
        "============================================================",
        "",
    ]
    eff_10 = data.get("effective_months_10y")
    eff_5 = data.get("effective_months_5y")
    if eff_10 is not None:
        lines.append("effective_months_10y (after join): " + str(eff_10))
    if eff_5 is not None:
        lines.append("effective_months_5y (after join): " + str(eff_5))
    lines.append("")
    max_dw = data.get("max_delta_w")
    if max_dw is not None:
        lines.append("max |weight_5Y - weight_10Y|: " + str(round(max_dw, 3)))
    top5 = data.get("top5_delta_w") or []
    if top5:
        lines.append("top 5 weight deltas (ticker, delta): " + ", ".join(f"{t}={d}" for t, d in top5))
    lines.append("")
    mrc = data.get("max_rc_asset_delta")
    if mrc is not None:
        lines.append("max |RC_asset(5Y) - RC_asset(10Y)|: " + str(round(float(mrc), 4)))
    rc_deltas = data.get("rc_asset_deltas") or {}
    if isinstance(rc_deltas, dict) and rc_deltas:
        top_rc = sorted(rc_deltas.items(), key=lambda x: (-float(x[1] or 0), x[0]))[:5]
        lines.append("top 5 per-asset RC deltas (ticker, |delta|): " + ", ".join(f"{t}={round(float(d), 4)}" for t, d in top_rc))
    lines.append("")
    vol10 = data.get("vol_10y_under_sigma10y")
    vol10_5 = data.get("vol_10y_under_sigma5y")
    if vol10 is not None:
        lines.append("Portfolio vol (10Y weights) under Sigma_10Y: " + str(vol10) + "%")
    if vol10_5 is not None:
        lines.append("Portfolio vol (10Y weights) under Sigma_5Y: " + str(vol10_5) + "%")
    lines.append("")
    flags = data.get("flags") or []
    lines.append("Robustness flags: " + (", ".join(flags) if flags else "none (10Y solution consistent with 5Y)"))
    actions = data.get("stabilization_actions") or []
    if actions:
        lines.append("Stabilization actions applied: " + ", ".join(actions))
    lines.append("Final portfolio: " + ("10Y weights (primary)" if data.get("final_portfolio_is_10y", True) else " - "))
    lines.append("Robust vs 5Y: " + ("yes" if data.get("robust_vs_5y", False) else "no" + (f" ({', '.join(flags)})" if flags else "")))
    lines.append("")
    return "\n".join(lines)


def _format_robustness_html(data: dict[str, Any]) -> str:
    """Format Dual-Horizon Robustness section for HTML report."""
    parts = [
        '<section class="robustness-section" id="robustness">',
        "<h2>Dual-Horizon Robustness (10Y primary + 5Y secondary validation)</h2>",
    ]
    eff_10 = data.get("effective_months_10y")
    eff_5 = data.get("effective_months_5y")
    parts.append("<p><strong>Effective sample length (after inner join):</strong> ")
    parts.append(f"10Y = {eff_10} months, 5Y = {eff_5} months</p>")
    max_dw = data.get("max_delta_w")
    if max_dw is not None:
        parts.append(f"<p><strong>Max |weight_5Y - weight_10Y|:</strong> {html.escape(_fmt_ratio(max_dw))}</p>")
    top5 = data.get("top5_delta_w") or []
    if top5:
        rows = "".join(f"<tr><td>{html.escape(str(t))}</td><td>{html.escape(_fmt_ratio(d))}</td></tr>" for t, d in top5)
        parts.append(
            _html_table_section(
                '<table><caption>Top 5 weight deltas</caption><thead><tr><th>Ticker</th><th>Delta</th></tr></thead><tbody>'
                + rows
                + "</tbody></table>"
            )
        )
    mrc = data.get("max_rc_asset_delta")
    if mrc is not None:
        parts.append(f"<p><strong>Max |RC_asset(5Y) - RC_asset(10Y)|:</strong> {html.escape(_fmt_val(mrc))}</p>")
    rc_deltas = data.get("rc_asset_deltas") or {}
    if isinstance(rc_deltas, dict) and rc_deltas:
        top_rc = sorted(rc_deltas.items(), key=lambda x: (-float(x[1] or 0), x[0]))[:5]
        drows = "".join(
            f"<tr><td>{html.escape(str(t))}</td><td>{html.escape(_fmt_val(d))}</td></tr>" for t, d in top_rc
        )
        parts.append(
            _html_table_section(
                '<table><caption>Top per-asset RC deltas (|5Y - 10Y|)</caption><thead><tr><th>Ticker</th><th>|delta|</th></tr></thead><tbody>'
                + drows
                + "</tbody></table>"
            )
        )
    vol10 = data.get("vol_10y_under_sigma10y")
    vol10_5 = data.get("vol_10y_under_sigma5y")
    if vol10 is not None or vol10_5 is not None:
        parts.append("<p><strong>Portfolio vol (10Y weights):</strong> under Sigma_10Y = " + html.escape(_fmt_ratio(vol10)) + "; under Sigma_5Y = " + html.escape(_fmt_ratio(vol10_5)) + "</p>")
    flags = data.get("flags") or []
    flag_class = "status-fail" if flags else "status-pass"
    parts.append(f'<p><strong>Robustness flags:</strong> <span class="{flag_class}">' + (", ".join(html.escape(f) for f in flags) if flags else "none (10Y consistent with 5Y)") + "</span></p>")
    if data.get("stabilization_actions"):
        parts.append("<p><strong>Stabilization actions:</strong> " + html.escape(", ".join(data["stabilization_actions"])) + "</p>")
    parts.append("<p><strong>Final portfolio:</strong> 10Y weights (primary). <strong>Robust vs 5Y:</strong> " + ("yes" if data.get("robust_vs_5y", False) else "no") + "</p>")
    parts.append("</section>")
    return "\n".join(parts)


def write_report_txt(output_dir: str | Path) -> Path:
    """
    Load snapshot_3y, 5y, 10y and snapshot_assets from output_dir,
    format into a single text report, and write output_dir/report.txt.
    Includes Data Policy / Backtest Mode section from data_policy.json when present.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    report_lines = [
        "Portfolio Snapshot Report",
        "Generated from snapshot_3y.json, snapshot_5y.json, snapshot_10y.json, snapshot_assets.json",
        "",
    ]
    xray_summary = _xray_summary_from_output_dir(out)
    if xray_summary:
        report_lines.append(format_portfolio_xray_text(xray_summary))
        report_lines.append("")
    data_policy_path = out / "data_policy.json"
    if data_policy_path.exists():
        try:
            with open(data_policy_path, encoding="utf-8") as f:
                data_policy = json.load(f)
            report_lines.append(_format_data_policy_text(data_policy))
        except Exception:
            pass
    robustness_path = out / "robustness_report.json"
    if robustness_path.exists():
        try:
            with open(robustness_path, encoding="utf-8") as f:
                robustness_data = json.load(f)
            report_lines.append(_format_robustness_text(robustness_data))
        except Exception:
            pass
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
            f"<tr><td>{html.escape(t)}</td><td>{html.escape(_fmt_ratio(w_total[t]))}</td></tr>"
            for t in sorted(w_total.keys(), key=lambda x: (-w_total.get(x, 0), x))
        )
        parts.append(
            _html_table_section(
                '<table><caption>Final weights (total)</caption><thead><tr><th>Ticker</th><th>Weight</th></tr></thead><tbody>'
                + rows
                + "</tbody></table>"
            )
        )
    # RC asset
    rc_asset = data.get("RC_asset") or []
    if rc_asset:
        rows = "".join(f"<tr><td>{html.escape(str(x.get('ticker', '')))}</td><td>{html.escape(_fmt_ratio(x.get('rc_pct')))}</td></tr>" for x in rc_asset)
        parts.append(
            _html_table_section(
                '<table><caption>RC by asset (top)</caption><thead><tr><th>Ticker</th><th>RC %</th></tr></thead><tbody>'
                + rows
                + "</tbody></table>"
            )
        )
    # Constraints
    constraints = data.get("constraints_status") or {}
    if constraints:
        rows = "".join(f"<tr><td>{html.escape(k)}</td><td class=\"status-{html.escape(v.lower())}\">{html.escape(v)}</td></tr>" for k, v in constraints.items())
        parts.append(
            _html_table_section(
                '<table><caption>Constraints</caption><thead><tr><th>Constraint</th><th>Status</th></tr></thead><tbody>'
                + rows
                + "</tbody></table>"
            )
        )
    # Metrics
    metrics = data.get("metrics") or {}
    if metrics:
        metric_keys = ("cagr", "vol_annual", "sharpe", "sortino", "beta_portfolio", "treynor", "max_drawdown", "ttr_months")
        def _fmt_metric_for_html(key: str, value: Any) -> str:
            if key in ("cagr", "vol_annual", "max_drawdown"):
                return html.escape(_fmt_ratio(value))
            return _fmt_val_html(value)
        rows = "".join(f"<tr><td>{html.escape(k)}</td><td>{_fmt_metric_for_html(k, metrics.get(k))}</td></tr>" for k in metric_keys if k in metrics)
        parts.append(
            _html_table_section(
                '<table><caption>Portfolio metrics</caption><thead><tr><th>Metric</th><th>Value</th></tr></thead><tbody>'
                + rows
                + "</tbody></table>"
            )
        )
    # Stress
    stress = data.get("stress_suite_results") or {}
    overall = stress.get("overall", " - ")
    parts.append(f'<p class="stress-overall"><strong>Stress:</strong> <span class="status-{html.escape(str(overall).lower())}">{_fmt_val_html(overall)}</span></p>')
    # Analytics summary
    analytics = data.get("analytics") or {}
    if analytics:
        rows = []
        tail_risk = analytics.get("tail_risk")
        if isinstance(tail_risk, dict) and tail_risk.get("metric_available"):
            rows.append(
                "<tr><td>tail_risk</td><td>"
                + html.escape(
                    f"daily historical, window {tail_risk.get('window_label')}, n_obs={tail_risk.get('n_obs')}"
                )
                + "</td></tr>"
            )
            for k in ("var_95", "var_99", "es_95", "es_99"):
                if tail_risk.get(k) is not None:
                    rows.append(
                        f"<tr><td>{html.escape(k)}</td><td>{html.escape(_fmt_ratio(tail_risk[k]))}</td></tr>"
                    )
        else:
            for k in ("var_95", "es_95"):
                if k in analytics and analytics[k] is not None:
                    rows.append(
                        f"<tr><td>{html.escape(k)}</td><td>{html.escape(_fmt_ratio(analytics[k]))}</td></tr>"
                    )
        if analytics.get("eee_10pct") is not None:
            rows.append(
                f"<tr><td>eee_10pct</td><td>{_fmt_val_html(analytics['eee_10pct'])}%</td></tr>"
            )
        for k in ("rolling_sharpe_36m", "rolling_sortino_36m"):
            if k in analytics:
                rows.append(
                    f"<tr><td>{html.escape(k)}</td><td>{_fmt_val_html(analytics[k])}</td></tr>"
                )
        if rows:
            parts.append(
                _html_table_section(
                    '<table><caption>Analytics</caption><thead><tr><th>Metric</th><th>Value</th></tr></thead><tbody>'
                    + "".join(rows)
                    + "</tbody></table>"
                )
            )
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
            formatted_cells = []
            for k in keys:
                if k in ("cagr", "vol_annual", "max_drawdown"):
                    formatted_cells.append(f"<td>{html.escape(_fmt_ratio(r.get(k)))}</td>")
                else:
                    formatted_cells.append(f"<td>{_fmt_val_html(r.get(k))}</td>")
            cells = "".join(formatted_cells)
            body_rows.append(f"<tr><td>{ticker}</td>{cells}</tr>")
        parts.append(
            _html_table_section(
                f'<table class="assets-table"><caption>Window {html.escape(label)}</caption>'
                f"<thead><tr>{header_cells}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"
            )
        )
    parts.append("</section>")
    return "\n".join(parts)


HTML_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Portfolio Snapshot Report</title>
<!-- Aligned with DESIGN.md + config_ui/static/design.css: Inter/DM Sans, RUI tokens, flat, pill nav. -->
<style>
@import url("https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@9..40,400;500&family=Inter:ital,opsz,wght@0,14..32,400;500;600&display=swap");
:root {
  --rui-dark: #191c1f;
  --rui-white: #ffffff;
  --rui-surface: #f4f4f4;
  --rui-border: #c9c9cd;
  --rui-mid: #505a63;
  --rui-muted: #8d969e;
  --rui-blue: #376cd5;
  --rui-blue-brand: #494fdf;
  --rui-pass: #00a87e;
  --rui-fail: #e23b4a;
  --rui-warn: #ec7e00;
  --rui-pass-bg: #e6f7f2;
  --rui-fail-bg: #fdeced;
  --rui-warn-bg: #fff3e6;
  --font-d: "DM Sans", "Inter", system-ui, sans-serif;
  --font-b: "Inter", system-ui, -apple-system, sans-serif;
  --radius-card: 20px;
  --radius-pill: 9999px;
  --space-8: 8px;
  --space-16: 16px;
  --space-24: 24px;
  --space-32: 32px;
  --space-40: 40px;
}
* { box-sizing: border-box; }
body { font-family: var(--font-b); font-size: 16px; line-height: 1.5; letter-spacing: 0.02em; background: var(--rui-white); color: var(--rui-dark); margin: 0; padding: var(--space-32) var(--space-16) 48px; -webkit-font-smoothing: antialiased; }
.report-root { max-width: 1200px; margin: 0 auto; }
.report-header { margin-bottom: var(--space-32); padding-bottom: var(--space-24); border-bottom: 1px solid var(--rui-border); }
.report-header h1 { font-family: var(--font-d); font-size: clamp(1.75rem, 4vw, 2.5rem); font-weight: 500; line-height: 1.15; letter-spacing: -0.02em; margin: 0 0 var(--space-8); color: var(--rui-dark); }
.subtitle { color: var(--rui-mid); font-size: 0.95rem; margin: 0 0 var(--space-24); letter-spacing: 0.02em; line-height: 1.5; max-width: 48rem; }
.report-nav { display: flex; flex-wrap: wrap; gap: var(--space-8); align-items: center; }
.report-nav a {
  display: inline-flex;
  align-items: center;
  font-family: var(--font-d);
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--rui-dark);
  text-decoration: none;
  padding: 8px 16px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--rui-border);
  background: var(--rui-white);
  transition: border-color 0.15s, background 0.15s, opacity 0.15s;
}
.report-nav a:hover { border-color: var(--rui-dark); background: var(--rui-surface); opacity: 0.9; }
section {
  background: var(--rui-surface);
  border: 1px solid var(--rui-border);
  border-radius: var(--radius-card);
  padding: var(--space-24) var(--space-24);
  margin-bottom: var(--space-24);
  break-inside: avoid;
  box-shadow: none;
}
section h2 { font-family: var(--font-d); font-size: 1.25rem; font-weight: 500; line-height: 1.3; margin: 0 0 var(--space-16); border-bottom: 1px solid var(--rui-border); padding-bottom: var(--space-8); letter-spacing: -0.01em; }
section h2 .meta { font-weight: 400; color: var(--rui-mid); font-size: 0.88rem; }
section p { margin: 0 0 0.75rem; color: var(--rui-dark); }
section p:last-child { margin-bottom: 0; }
section p strong { color: var(--rui-mid); font-weight: 600; }
.table-wrap { width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; margin-bottom: var(--space-16); }
.table-wrap table { margin-bottom: 0; }
table { width: 100%; max-width: 100%; border-collapse: collapse; margin-bottom: var(--space-16); font-size: 0.94rem; }
section > table:last-child { margin-bottom: 0; }
table caption { text-align: left; font-weight: 500; font-family: var(--font-d); margin: 0 0 var(--space-8); font-size: 0.9rem; color: var(--rui-dark); }
th, td { border: 1px solid var(--rui-border); padding: 10px 12px; text-align: left; vertical-align: top; }
th { background: var(--rui-white); font-weight: 500; color: var(--rui-dark); }
tbody tr:nth-child(even) { background: rgba(25, 28, 31, 0.03); }
.assets-table th, .assets-table td { font-size: 0.88rem; }
.stress-overall { margin-bottom: 0.75rem; }
.stress-overall strong { color: var(--rui-mid); }
/* Status: text + optional pill in stress line */
.stress-overall .status-pass, .stress-overall .status-fail, .stress-overall .status-diag_attention,
.stress-overall [class^="status-"] {
  display: inline-block;
  margin-left: 4px;
  padding: 4px 12px;
  border-radius: var(--radius-pill);
  font-size: 0.85rem;
  font-weight: 500;
  font-family: var(--font-d);
}
.stress-overall [class^="status-"] { background: var(--rui-surface); color: var(--rui-mid); }
.stress-overall .status-pass { background: var(--rui-pass-bg); color: #006400; }
.stress-overall .status-fail, .stress-overall [class^="status-fail"] { background: var(--rui-fail-bg); color: #8b0000; }
.stress-overall .status-diag_attention { background: var(--rui-warn-bg); color: #b06a00; }
/* Prose status pills (e.g. robustness flags) */
.robustness-section p > span[class^="status-"] {
  display: inline-block; margin-left: 6px; padding: 4px 12px; border-radius: var(--radius-pill);
  font-size: 0.85rem; font-weight: 500; font-family: var(--font-d);
  background: var(--rui-surface); color: var(--rui-mid);
}
.robustness-section p > span.status-pass { background: var(--rui-pass-bg); color: #006400; }
.robustness-section p > span.status-fail, .robustness-section p > span[class^="status-fail"] { background: var(--rui-fail-bg); color: #8b0000; }
.robustness-section p > span.status-diag_attention { background: var(--rui-warn-bg); color: #b06a00; }
/* Table cells: constraint / generic status (no pill) */
td.status-pass { color: var(--rui-pass); font-weight: 500; }
td.status-fail, td[class^="status-fail"] { color: var(--rui-fail); font-weight: 500; }
td.status-diag_attention { color: var(--rui-warn); font-weight: 500; }
.data-policy-section table { max-width: 100%; }
.table-wrap + .table-wrap, section > .table-wrap { margin-top: 0; }
.data-policy-section .table-wrap, .robustness-section .table-wrap { margin-bottom: var(--space-16); }
.data-policy-section .table-wrap:last-child, .robustness-section .table-wrap:last-child { margin-bottom: 0; }
.xray-summary-section .xray-disclaimer { color: var(--rui-mid); font-size: 0.92rem; }
.xray-section-nav { display: flex; flex-wrap: wrap; gap: var(--space-8); margin: var(--space-16) 0; }
.xray-section-nav a { font-size: 0.82rem; padding: 6px 12px; border-radius: var(--radius-pill); border: 1px solid var(--rui-border); text-decoration: none; color: var(--rui-dark); }
.xray-section { margin-top: var(--space-16); padding-top: var(--space-16); border-top: 1px solid var(--rui-border); }
.xray-section h3 { font-family: var(--font-d); font-size: 1.05rem; margin: 0 0 var(--space-8); }
.xray-meta, .xray-warning, .xray-limitation, .xray-source-note { font-size: 0.9rem; color: var(--rui-mid); }
.xray-bullets { margin: 0 0 var(--space-16); padding-left: 1.25rem; }
@media (max-width: 720px) {
  body { padding: var(--space-24) 12px 40px; }
  .report-header h1 { font-size: 1.5rem; }
  section { padding: var(--space-16); }
}
@media print {
  body { background: #fff; padding: 0.5rem; }
  .report-nav { display: none; }
  section { break-inside: avoid; }
}
</style>
</head>
<body>
<div class="report-root">
"""

HTML_TAIL = """
</div>
</body>
</html>
"""


def _html_table_section(table_html: str) -> str:
    """Wrap a <table> in a scroll container (DESIGN.md  -  wide tables on small viewports)."""
    return f'<div class="table-wrap">{table_html}</div>'


def _format_data_policy_html(data: dict[str, Any]) -> str:
    """Format Data Policy / Backtest Mode section for HTML report."""
    parts = [
        '<section class="data-policy-section" id="data-policy">',
        "<h2>Data Policy / Backtest Mode</h2>",
    ]
    trows: list[str] = [
        "<tr><td>backtest_mode</td><td>" + html.escape(str(data.get("backtest_mode", " - "))) + "</td></tr>",
        "<tr><td>join_policy (cov/RC/beta)</td><td>" + html.escape(str(data.get("join_policy_cov_rc", "inner join"))) + "</td></tr>",
    ]
    inner = data.get("inner_join_months_used_for_risk")
    if inner is not None:
        trows.append(
            "<tr><td>inner_join_months_used_for_risk</td><td>"
            + html.escape(str(inner))
            + (" (warning: &lt;36 months)" if inner < 36 else "")
            + "</td></tr>"
        )
    n_redist = data.get("n_months_redistributed")
    n_cash = data.get("n_months_cash_fallback")
    if n_redist is not None:
        trows.append("<tr><td>months with NaN redistribution</td><td>" + html.escape(str(n_redist)) + "</td></tr>")
    if n_cash is not None:
        trows.append(
            "<tr><td>months with excess to cash (RC/RB gating)</td><td>" + html.escape(str(n_cash)) + "</td></tr>"
        )
    table1 = "<table><caption>Backtest and join policy</caption><tbody>" + "".join(trows) + "</tbody></table>"
    parts.append(_html_table_section(table1))
    fam = data.get("first_available_month") or {}
    if fam:
        fam_rows: list[str] = [
            "<table><caption>First available month (per ticker)</caption><thead><tr><th>Ticker</th><th>First month</th></tr></thead><tbody>"
        ]
        for t in sorted(fam.keys()):
            fam_rows.append("<tr><td>" + html.escape(t) + "</td><td>" + html.escape(str(fam[t])) + "</td></tr>")
        fam_rows.append("</tbody></table>")
        parts.append(_html_table_section("".join(fam_rows)))
    parts.append("</section>")
    return "\n".join(parts)


def write_report_html(output_dir: str | Path) -> Path:
    """
    Load snapshot_3y, 5y, 10y and snapshot_assets from output_dir,
    format into a single HTML report (board), and write output_dir/report.html.
    Includes Data Policy / Backtest Mode section from data_policy.json when present.
    Open in browser; use Print -> Save as PDF for PDF.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    chunks = [HTML_HEAD]
    chunks.append("<header class=\"report-header\">")
    chunks.append("<h1>Portfolio Snapshot Report</h1>")
    chunks.append(
        '<p class="subtitle">Generated from snapshot_3y.json, snapshot_5y.json, snapshot_10y.json, snapshot_assets.json</p>'
    )
    chunks.append(
        '<nav class="report-nav" aria-label="Report sections">'
        '<a href="#xray-summary">X-Ray Summary</a>'
        '<a href="#data-policy">Data Policy</a>'
        '<a href="#robustness">Dual-Horizon</a>'
        '<a href="#win-3y">3Y</a>'
        '<a href="#win-5y">5Y</a>'
        '<a href="#win-10y">10Y</a>'
        '<a href="#assets">Assets</a>'
        "</nav>"
    )
    chunks.append("</header>")
    xray_summary = _xray_summary_from_output_dir(out)
    if xray_summary:
        chunks.append(_format_xray_summary_html(xray_summary))
    data_policy_path = out / "data_policy.json"
    if data_policy_path.exists():
        try:
            with open(data_policy_path, encoding="utf-8") as f:
                data_policy = json.load(f)
            chunks.append(_format_data_policy_html(data_policy))
        except Exception:
            pass
    robustness_path = out / "robustness_report.json"
    if robustness_path.exists():
        try:
            with open(robustness_path, encoding="utf-8") as f:
                robustness_data = json.load(f)
            chunks.append(_format_robustness_html(robustness_data))
        except Exception:
            pass
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
