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

from src.config_schema import PortfolioConfig

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
) -> Path:
    """
    Export run metadata to JSON including:
    - Full resolved configuration
    - Derived assumptions used in the run
    - Pending config items (still need final user values)
    - Run timestamp and analysis period info
    - Comparison with targets (if specified)
    
    Returns path to exported file.
    """
    if run_timestamp is None:
        run_timestamp = datetime.now().isoformat()
    
    # Build metadata structure
    metadata = {
        "run_info": {
            "timestamp": run_timestamp,
            "analysis_end_date": analysis_end,
        },
        "resolved_config": portfolio_config.get_resolved_config(),
        "active_assumptions": portfolio_config.get_active_assumptions(),
        "derived_assumptions": derived_assumptions,
        "future_constraint_fields": {
            "description": "Constraints/reference inputs for current or future portfolio construction. "
                          "rc_asset_cap_pct, max_single_security_weight_pct, min_single_security_weight_pct "
                          "will receive final numeric values later from the user; the system already supports "
                          "them as config fields and passes them through all relevant layers.",
            "fields": portfolio_config.get_future_constraint_fields(),
        },
        "pending_user_input": {
            "description": "Config items that still need final user values (to be provided later by user)",
            "fields": portfolio_config.get_pending_config_items(),
        },
    }
    
    if stress_report:
        metadata["stress_test"] = {
            "status": stress_report.get("status"),
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
