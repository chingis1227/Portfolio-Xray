"""
Export asset/portfolio metrics to CSV and persist all input series.
All metric outputs are rounded to 3 decimal places at export only (Output Formatting Standard).

Also exports run_metadata.json with resolved configuration, derived assumptions,
and pending config items.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from src.analysis_setup import build_analysis_setup
from src.config_schema import PortfolioConfig
from src.input_assumptions import build_input_assumptions_from_analysis_setup

REPORT_DECIMALS = 3


def ensure_output_dir(output_dir: str | Path) -> Path:
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def export_asset_metrics_csv(
    metrics_list: list[dict],
    window_months: int,
    output_dir: Path,
    suffix: str | None = None,
) -> Path:
    """
    Write flat asset metrics to CSV. Filename: asset_metrics_3y.csv, _5y.csv, _10y.csv.
    Numeric columns rounded to 3 decimal places at export only.
    """
    suffix = suffix or f"{window_months}y"
    if window_months == 36:
        suffix = "3y"
    elif window_months == 60:
        suffix = "5y"
    elif window_months == 120:
        suffix = "10y"
    path = output_dir / f"asset_metrics_{suffix}.csv"
    df = pd.DataFrame(metrics_list)
    df = df.round(REPORT_DECIMALS)
    df.to_csv(path, index=False)
    return path


def export_portfolio_metrics_csv(metrics_list: list[dict], output_dir: Path) -> list[Path]:
    """Write portfolio metrics per window to CSV(s). Numeric values rounded to 3 decimal places at export only."""
    paths = []
    for m in metrics_list:
        w = m.get("window_months", 0)
        suffix = "3y" if w == 36 else "5y" if w == 60 else "10y"
        path = output_dir / f"portfolio_metrics_{suffix}.csv"
        df = pd.DataFrame([m])
        df = df.round(REPORT_DECIMALS)
        df.to_csv(path, index=False)
        paths.append(path)
    return paths


def export_rc_vol_csv(rc_series: pd.Series, path: Path) -> None:
    """Save RC_vol (percentage contribution to variance) to CSV. Values rounded to 3 decimal places at export only."""
    rc_series.round(REPORT_DECIMALS).to_csv(path, header=True)


def persist_series(series: pd.Series, path: Path) -> None:
    """Save a single Series to CSV (index as first column)."""
    series.to_csv(path, header=True)


def persist_df(df: pd.DataFrame, path: Path) -> None:
    """Save DataFrame to CSV."""
    df.to_csv(path)


def save_inputs(
    output_dir: Path,
    monthly_prices: pd.DataFrame,
    monthly_returns: pd.DataFrame,
    rf_monthly: pd.Series,
    benchmark_returns: pd.Series,
    cash_returns: pd.Series,
    fx_series_used: dict[str, pd.Series] | None = None,
) -> None:
    """Persist all input series used for reproducibility."""
    sub = output_dir / "inputs"
    sub.mkdir(parents=True, exist_ok=True)
    persist_df(monthly_prices, sub / "monthly_prices.csv")
    persist_df(monthly_returns, sub / "monthly_returns.csv")
    persist_series(rf_monthly, sub / "rf_monthly.csv")
    persist_series(benchmark_returns, sub / "benchmark_returns.csv")
    persist_series(cash_returns, sub / "cash_proxy_returns.csv")
    if fx_series_used:
        for name, s in fx_series_used.items():
            persist_series(s, sub / f"fx_{name}.csv")


def export_run_metadata(
    output_dir: Path,
    portfolio_config: PortfolioConfig,
    derived_assumptions: dict[str, Any],
    analysis_end: str,
    run_timestamp: str | None = None,
    portfolio_metrics_summary: dict[str, Any] | None = None,
    stress_report: dict[str, Any] | None = None,
    portfolio_valid: bool | None = None,
    portfolio_weights: dict[str, float] | None = None,
    weights_source: str | None = None,
    analysis_setup: dict[str, Any] | None = None,
) -> Path:
    """
    Export run metadata to JSON including:
    - Full resolved configuration
    - Derived assumptions used in the run
    - Pending config items (still need final user values)
    - Run timestamp and analysis period info
    - Comparison with targets (if specified)
    - portfolio_valid: False when MaxDD or Stress Judge fails (gatekeeper)

    Returns path to exported file.
    """
    if run_timestamp is None:
        run_timestamp = datetime.now().isoformat()

    if analysis_setup is None:
        analysis_setup = build_analysis_setup(
            portfolio_config,
            portfolio_weights=portfolio_weights,
            weights_source=weights_source,
            cash_proxy_ticker=derived_assumptions.get("resolved_cash_proxy_ticker"),
            rf_source=derived_assumptions.get("resolved_rf_source"),
            local_benchmark_map=derived_assumptions.get("resolved_local_benchmark_map"),
            analysis_end=analysis_end,
            windows_months=derived_assumptions.get("windows_months"),
            returns_frequency=derived_assumptions.get("returns_frequency"),
            periods_per_year=derived_assumptions.get("periods_per_year"),
            run_context="report",
        )

    # Build metadata structure
    metadata = {
        "run_info": {
            "timestamp": run_timestamp,
            "analysis_end_date": analysis_end,
        },
        "resolved_config": portfolio_config.get_resolved_config(),
        "analysis_setup": analysis_setup,
        "input_assumptions": build_input_assumptions_from_analysis_setup(analysis_setup),
        "active_assumptions": portfolio_config.get_active_assumptions(),
        "derived_assumptions": derived_assumptions,
        "future_constraint_fields": {
            "description": "Constraints/reference inputs for current or future portfolio construction. "
                          "max_single_security_weight_pct, min_single_security_weight_pct "
                          "may receive final numeric values from the user; the system passes them through relevant layers.",
            "fields": portfolio_config.get_future_constraint_fields(),
        },
        "pending_user_input": {
            "description": "Config items that still need final user values (to be provided later by user)",
            "fields": portfolio_config.get_pending_config_items(),
        },
    }
    if portfolio_valid is not None:
        metadata["portfolio_valid"] = portfolio_valid

    if isinstance(stress_report, dict):
        fd = stress_report.get("frequency_disclosure")
        if isinstance(fd, dict):
            metadata["frequency_disclosure"] = fd
        pp = stress_report.get("periods_per_year")
        if isinstance(pp, (int, float)) and not isinstance(pp, bool):
            metadata["periods_per_year"] = int(pp)

    if stress_report:
        metadata["stress_test"] = {
            "status": stress_report.get("status"),
            "diagnostic_codes": stress_report.get("diagnostic_codes"),
            "primary_diagnostic_code": stress_report.get("primary_diagnostic_code"),
            "fail_reason_code": stress_report.get("fail_reason_code"),
            "warning_code": stress_report.get("warning_code"),
            "worst_scenario_loss_pct": stress_report.get("worst_scenario_loss_pct"),
            "failed_scenario": stress_report.get("failed_scenario"),
            "failed_test": stress_report.get("failed_test"),
        }

    # Add target comparison if target was specified and portfolio metrics available
    if portfolio_config.target_nominal_return_annual is not None and portfolio_metrics_summary:
        realized_cagr = portfolio_metrics_summary.get("cagr")
        target = portfolio_config.target_nominal_return_annual
        metadata["target_comparison"] = {
            "target_nominal_return_annual": target,
            "realized_cagr": realized_cagr,
            "difference": (realized_cagr - target) if realized_cagr is not None else None,
            "target_achieved": (realized_cagr >= target) if realized_cagr is not None else None,
        }

    # Export
    path = output_dir / "run_metadata.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)

    return path


def export_correlation_matrix_csv(
    corr_matrix: pd.DataFrame,
    window_months: int,
    output_dir: Path,
) -> Path:
    """
    Export correlation matrix to CSV.
    Filename: correlation_matrix_3y.csv, _5y.csv, _10y.csv.
    Values rounded to 3 decimal places at export only.
    """
    suffix = "3y" if window_months == 36 else "5y" if window_months == 60 else "10y"
    path = output_dir / f"correlation_matrix_{suffix}.csv"
    corr_matrix.round(REPORT_DECIMALS).to_csv(path)
    return path


def export_data_policy(
    output_dir: Path,
    backtest_mode: str,
    first_available_month: dict[str, str],
    inner_join_months_used: int | None = None,
    n_months_redistributed: int | None = None,
    n_months_cash_fallback: int | None = None,
) -> Path:
    """
    Export data policy / backtest mode section for reports.
    Used by run_report to persist backtest_mode, join policy, per-ticker first month, and NaN/cash counts.
    """
    data = {
        "backtest_mode": backtest_mode,
        "join_policy_cov_rc": "inner join (intersection of dates across assets)",
        "first_available_month": first_available_month,
        "inner_join_months_used_for_risk": inner_join_months_used,
        "n_months_redistributed": n_months_redistributed,
        "n_months_cash_fallback": n_months_cash_fallback,
    }
    path = output_dir / "data_policy.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


def export_stress_report(stress_report: dict, output_dir: Path) -> Path:
    """
    Export stress test report to JSON. Per docs/docs/stress_testing_spec.md.
    """
    path = output_dir / "stress_report.json"
    # Ensure serializable (round floats, no numpy)
    def _round_obj(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: _round_obj(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_round_obj(x) for x in obj]
        if isinstance(obj, (int, float)) and obj is not None and not isinstance(obj, bool):
            return round(obj, 4) if isinstance(obj, float) else obj
        return obj
    out = _round_obj(stress_report)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False, default=str)
    return path


def _cfg_val(cfg: Any, key: str, default: Any = None) -> Any:
    """Get config value from PortfolioConfig or dict."""
    if hasattr(cfg, key):
        return getattr(cfg, key, default)
    if isinstance(cfg, dict):
        return cfg.get(key, default)
    return default


def generate_ips_summary(cfg: Any, run_result: dict[str, Any], output_path: Path) -> Path:
    """
    Generate IPS summary with full run results: mandate, status, weights,
    stress summary, violations, and actions. Single reference for risk and execution.
    """
    target_vol = _cfg_val(cfg, "target_vol_annual")
    target_vol_pct = round(float(target_vol) * 100, 1) if target_vol is not None else None
    max_dd = _cfg_val(cfg, "target_max_drawdown_pct")
    max_dd_pct = round(abs(float(max_dd)) * 100, 1) if max_dd is not None else None
    horizon = _cfg_val(cfg, "horizon_years")
    currency = _cfg_val(cfg, "investor_currency", "USD")
    profile = _cfg_val(cfg, "client_profile") or " - "
    status = run_result.get("status", " - ")
    next_actions = run_result.get("next_actions") or []
    weights = run_result.get("weights") or {}
    stress_summary = run_result.get("stress_summary") or {}
    violations = run_result.get("violations") or []
    mandate_check = run_result.get("mandate_check") or {}

    lines = [
        "IPS Summary  -  Full Run Results",
        "=" * 50,
        "",
        "1. Mandate parameters",
        "-" * 30,
        "  Target volatility (annual):  %s%%" % (target_vol_pct if target_vol_pct is not None else " - "),
        "  Max drawdown limit:          %s%%" % (max_dd_pct if max_dd_pct is not None else " - "),
        "  Horizon (years):             %s" % (horizon if horizon is not None else " - "),
        "  Investor currency:           %s" % currency,
        "  Client profile:              %s" % profile,
        "  Construction:                single-stage max expected return; soft vol/return targets; RC_vol diagnostic-only (reports/stress).",
        "",
        "2. Mandate check (blocking)",
        "-" * 30,
        "  Run status:                  %s" % status,
        "  Historical MaxDD pass:       %s"
        % (
            mandate_check.get("pass")
            if mandate_check.get("pass") is not None
            else ("N/A" if max_dd_pct is None else "NOT_CHECKED")
        ),
        "  Realized MaxDD (full hist.): %s"
        % (
            ("%.2f%%" % (float(mandate_check["max_drawdown_realized"]) * 100))
            if mandate_check.get("max_drawdown_realized") is not None
            else " - "
        ),
        "  History window:              %s .. %s (%s months)"
        % (
            mandate_check.get("history_start") or " - ",
            mandate_check.get("history_end") or " - ",
            mandate_check.get("months_used") or 0,
        ),
        "  Note: Only this historical MaxDD vs mandate can prevent weight release.",
        "",
        "3. Final portfolio weights",
        "-" * 30,
    ]
    if weights:
        for t in sorted(weights.keys(), key=lambda x: (-(weights.get(x) or 0), x)):
            w = weights[t]
            if isinstance(w, (int, float)):
                lines.append("  %s: %.3f" % (t, float(w)))
            else:
                lines.append("  %s: %s" % (t, w))
        lines.append("  (sum: %.3f)" % sum(weights.values()))
    else:
        lines.append("  (weights not written for this run)")
    lines.append("")

    lines.append("4. Risk contribution (RC_vol)")
    lines.append("-" * 30)
    lines.append("  RC_vol is reported in metrics and stress (Top1/Top3) for diagnostics; not used as a construction cap in this run.")
    lines.append("")

    lines.append("5. Stress & scenario diagnostics (non-blocking for release)")
    lines.append("-" * 30)
    lines.append("  Diagnostic status:   %s" % stress_summary.get("diagnostic_status", stress_summary.get("status", " - ")))
    dcodes = stress_summary.get("diagnostic_codes") or []
    if dcodes:
        lines.append("  Diagnostic codes:    %s" % ", ".join(str(c) for c in dcodes))
    lines.append(
        "  Primary code:        %s" % (stress_summary.get("primary_diagnostic_code") or stress_summary.get("fail_reason_code") or " - ")
    )
    worst = stress_summary.get("worst_scenario_loss_pct")
    if worst is not None:
        lines.append("  Worst scenario loss: %.2f%% (informational)" % (float(worst) * 100))
    lines.append("  Failed scenario:     %s" % (stress_summary.get("failed_scenario") or " - "))
    lines.append("  Note: Synthetic shocks & episode checks do not prevent weights; review with PM.")
    lines.append("")

    if violations:
        lines.append("6. Violations")
        lines.append("-" * 30)
        for v in violations:
            code = v.get("code", "?")
            details = v.get("details", "")
            if isinstance(details, dict):
                details = " | ".join("%s=%s" % (k, v) for k, v in details.items())
            lines.append("  %s: %s" % (code, details))
        lines.append("")
    else:
        lines.append("6. Violations: none")
        lines.append("")

    if next_actions:
        lines.append("7. Next actions (this run)")
        lines.append("-" * 30)
        for a in next_actions:
            lines.append("  - %s" % a)
        lines.append("")

    lines.append("8. Actions by status (reference)")
    lines.append("-" * 30)
    lines.append("  APPROVED             Use weights as target; safe to execute.")
    lines.append("  OK_FALLBACK          Optimizer used a numerical fallback; review optimization_status if needed.")
    lines.append("  FAIL_MANDATE         Historical MaxDD vs mandate failed or history insufficient; weights not written.")
    lines.append("  DIAG_* / FAIL_STRESS (violation)  Stress diagnostics only; does not prevent release (review PM).")
    lines.append("  FAIL_DATA            Weights not written. Follow next_actions above.")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path
