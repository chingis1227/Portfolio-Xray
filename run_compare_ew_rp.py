from __future__ import annotations

"""
Compare Equal-Weight vs Risk-Parity portfolios in dedicated files.

Outputs:
- <output_dir_final>/ew_rp_comparison.json
- <output_dir_final>/ew_rp_comparison.txt
"""

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from src.config import (
    load_assets_metadata,
    load_validated_config,
    resolve_cash_and_rf,
    resolve_local_benchmarks,
)
from src.data_loader import load_monthly_data_shared
from src.metrics_asset import time_to_recovery
from src.optimization import get_risk_portfolio_tickers
from src.portfolio_dynamic import portfolio_returns_nan_safe
from src.risk_contrib import cov_matrix_monthly
from src.utils import logger, setup_logging
from src.windows import slice_window


def _read_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _read_series_csv(path: Path) -> dict[str, float]:
    df = pd.read_csv(path, index_col=0)
    if df.empty:
        return {}
    s = df.iloc[:, 0]
    return {str(k): float(v) for k, v in s.items()}


def _read_one_row_csv(path: Path) -> dict[str, float]:
    df = pd.read_csv(path)
    if df.empty:
        return {}
    row = df.iloc[0].to_dict()
    out: dict[str, float] = {}
    for k, v in row.items():
        if pd.isna(v):
            continue
        out[str(k)] = float(v)
    return out


def _round_scalar(v: Any, ndigits: int = 3) -> Any:
    if v is None:
        return None
    try:
        f = float(v)
        if math.isnan(f):
            return None
        return round(f, ndigits)
    except Exception:
        return v


def _round_dict(obj: dict[str, Any], ndigits: int = 3) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in obj.items():
        if isinstance(v, dict):
            out[k] = _round_dict(v, ndigits)
        else:
            out[k] = _round_scalar(v, ndigits)
    return out


def _top_n_rc(rc_map: dict[str, float], n: int = 5) -> dict[str, float]:
    items = sorted(rc_map.items(), key=lambda kv: (-kv[1], kv[0]))
    return {k: v for k, v in items[:n]}


def _delta_nested_dict(
    left: dict[str, Any],
    right: dict[str, Any],
    ndigits: int = 3,
) -> dict[str, Any]:
    keys = sorted(set(left.keys()) | set(right.keys()))
    out: dict[str, Any] = {}
    for k in keys:
        lv = left.get(k)
        rv = right.get(k)
        if isinstance(lv, dict) or isinstance(rv, dict):
            out[k] = _delta_nested_dict(lv or {}, rv or {}, ndigits=ndigits)
        else:
            out[k] = _round_scalar(_safe_delta(lv, rv), ndigits=ndigits)
    return out


def _safe_delta(a: Any, b: Any) -> float | None:
    try:
        if a is None or b is None:
            return None
        af = float(a)
        bf = float(b)
        if np.isnan(af) or np.isnan(bf):
            return None
        return af - bf
    except Exception:
        return None


def _fmt(v: Any, pct: bool = False) -> str:
    if v is None:
        return " - "
    try:
        f = float(v)
        if np.isnan(f):
            return " - "
        if pct:
            return f"{f:.2%}"
        return f"{f:.3f}"
    except Exception:
        return str(v)


def _load_variant_payload(project_root: Path, folder_name: str) -> dict[str, Any]:
    base = project_root / folder_name
    summary_path = base / "summary.json"
    snapshot_path = base / "snapshot_10y.json"
    weights_path = base / "weights.json"
    rc_asset_csv = base / "results_csv" / "rc_vol_10y.csv"
    var_es_csv = base / "results_csv" / "var_es_10y.csv"
    eee_csv = base / "results_csv" / "eee_10y.csv"

    if not summary_path.exists() or not snapshot_path.exists() or not weights_path.exists():
        raise FileNotFoundError(
            f"Required files are missing in {base}. Run the EW and RP portfolio pipelines first."
        )

    summary = _read_json(summary_path)
    snapshot = _read_json(snapshot_path)
    weights = _read_json(weights_path)
    rc_asset = _read_series_csv(rc_asset_csv) if rc_asset_csv.exists() else {}
    var_es = _read_one_row_csv(var_es_csv) if var_es_csv.exists() else {}
    eee = _read_one_row_csv(eee_csv) if eee_csv.exists() else {}

    return {
        "label": summary.get("portfolio_type") or folder_name,
        "status": summary.get("status"),
        "stress_status": summary.get("stress_status"),
        "stress_fail_reason": summary.get("stress_fail_reason"),
        "portfolio_valid": summary.get("portfolio_valid"),
        "analysis_end": snapshot.get("analysis_end"),
        "window_months": snapshot.get("window_months"),
        "weights": {str(k): float(v) for k, v in weights.items()},
        "metrics": summary.get("metrics_10y") or {},
        "analytics": snapshot.get("analytics") or {},
        "rc_asset": rc_asset,
        "var_es": var_es,
        "eee": eee,
    }


def _compute_extra_metrics(
    cfg: Any,
    weights: dict[str, float],
    monthly_returns: pd.DataFrame,
    benchmark_returns: pd.Series,
    rf_monthly: pd.Series,
    cash_returns: pd.Series,
    analysis_end_str: str,
    window_months: int,
) -> dict[str, Any]:
    asset_returns_df = monthly_returns[[t for t in cfg.tickers if t in monthly_returns.columns]].copy()
    target_weights = {t: float(weights.get(t, 0.0)) for t in cfg.tickers}

    cov_df_nan_safe = None
    risk_rt = get_risk_portfolio_tickers(cfg.tickers, cfg.cash_proxy_ticker)
    if risk_rt and asset_returns_df.shape[0] >= 2:
        ret_inner = asset_returns_df.dropna(how="any").iloc[-720:]
        if len(ret_inner) >= 2:
            cov_df_nan_safe = cov_matrix_monthly(ret_inner, ddof=1)

    r_port, _w_used, _diag = portfolio_returns_nan_safe(
        asset_returns_df,
        target_weights,
        cash_returns.reindex(asset_returns_df.index).fillna(0.0),
        risk_tickers=risk_rt,
        return_diagnostics=True,
    )

    r_slice = slice_window(r_port, analysis_end_str, window_months).dropna()
    bench_slice = slice_window(benchmark_returns, analysis_end_str, window_months).reindex(r_slice.index)
    rf_slice = slice_window(rf_monthly, analysis_end_str, window_months).reindex(r_slice.index).fillna(0.0)
    common = pd.concat([r_slice, bench_slice, rf_slice], axis=1, join="inner").dropna()
    common.columns = ["r", "bench", "rf"]

    if common.shape[0] < 2:
        return {
            "corr_base": None,
            "downside_deviation_annual": None,
            "skewness": None,
            "kurtosis": None,
            "ttr_months": None,
            "recovered": False,
            "n_obs": int(common.shape[0]),
        }

    corr_base = float(common["r"].corr(common["bench"]))
    downside = np.minimum(0.0, common["r"].values - common["rf"].values)
    dd_monthly = float(np.sqrt(np.mean(np.square(downside))))
    dd_annual = float(dd_monthly * np.sqrt(12))
    lr = np.log1p(common["r"].values)
    skewness = float(stats.skew(lr))
    kurtosis = float(stats.kurtosis(lr))
    ttr_months, recovered = time_to_recovery(common["r"])

    return {
        "corr_base": corr_base,
        "downside_deviation_annual": dd_annual,
        "skewness": skewness,
        "kurtosis": kurtosis,
        "ttr_months": ttr_months if ttr_months is not None else None,
        "recovered": bool(recovered),
        "n_obs": int(common.shape[0]),
    }


def main() -> None:
    setup_logging()
    cfg = load_validated_config()
    project_root = Path(__file__).resolve().parent
    out_dir = Path(getattr(cfg, "output_dir_final", "Main portfolio"))
    out_dir.mkdir(parents=True, exist_ok=True)

    eq = _load_variant_payload(project_root, "equal-weight portfolio")
    rp = _load_variant_payload(project_root, "risk parity portfolio")

    assets_meta = load_assets_metadata()
    cash_proxy_ticker, rf_source = resolve_cash_and_rf(cfg)
    local_benchmark_map = resolve_local_benchmarks(
        cfg.tickers,
        cfg.local_benchmark_map or {},
        base_benchmark=cfg.benchmark_base_ticker,
    )
    data = load_monthly_data_shared(
        tickers=cfg.tickers,
        benchmark_base_ticker=cfg.benchmark_base_ticker,
        cash_proxy_ticker=cash_proxy_ticker,
        rf_source=rf_source,
        investor_currency=cfg.investor_currency,
        windows_months=cfg.windows_months,
        assets_meta=assets_meta,
        no_cache=False,
        local_benchmark_map=local_benchmark_map,
        returns_frequency=getattr(cfg, "returns_frequency", None),
    )
    analysis_end = data.analysis_end_str
    window_months = eq.get("window_months") or rp.get("window_months") or 120

    eq_extra = _compute_extra_metrics(
        cfg,
        eq["weights"],
        data.monthly_returns,
        data.benchmark_returns,
        data.rf_monthly,
        data.cash_returns,
        analysis_end,
        int(window_months),
    )
    rp_extra = _compute_extra_metrics(
        cfg,
        rp["weights"],
        data.monthly_returns,
        data.benchmark_returns,
        data.rf_monthly,
        data.cash_returns,
        analysis_end,
        int(window_months),
    )
    eq["extra_metrics"] = _round_dict(eq_extra)
    rp["extra_metrics"] = _round_dict(rp_extra)

    metric_keys = [
        "cagr",
        "vol_annual",
        "max_drawdown",
        "sharpe",
        "sortino",
        "beta_portfolio",
        "treynor",
        "corr_base",
        "downside_deviation_annual",
        "skewness",
        "kurtosis",
        "es_95",
        "es_99",
        "eee_10pct",
        "ttr_months",
    ]

    eq_flat = {
        **(eq.get("metrics") or {}),
        **(eq.get("extra_metrics") or {}),
        **(eq.get("var_es") or {}),
        **(eq.get("eee") or {}),
    }
    rp_flat = {
        **(rp.get("metrics") or {}),
        **(rp.get("extra_metrics") or {}),
        **(rp.get("var_es") or {}),
        **(rp.get("eee") or {}),
    }
    delta_metrics = {k: _round_scalar(_safe_delta(eq_flat.get(k), rp_flat.get(k))) for k in metric_keys}

    all_tickers = sorted(set(eq.get("rc_asset", {}).keys()) | set(rp.get("rc_asset", {}).keys()))
    delta_rc_asset = {
        t: _round_scalar(_safe_delta(eq.get("rc_asset", {}).get(t), rp.get("rc_asset", {}).get(t)))
        for t in all_tickers
    }

    eq_analytics = eq.get("analytics") or {}
    rp_analytics = rp.get("analytics") or {}

    rolling_keys = ("last", "mean", "p10", "p90")
    eq_roll_sharpe_36 = {k: (eq_analytics.get("rolling_sharpe_36m") or {}).get(k) for k in rolling_keys}
    rp_roll_sharpe_36 = {k: (rp_analytics.get("rolling_sharpe_36m") or {}).get(k) for k in rolling_keys}
    eq_roll_sharpe_12 = {k: (eq_analytics.get("rolling_sharpe_12m") or {}).get(k) for k in rolling_keys}
    rp_roll_sharpe_12 = {k: (rp_analytics.get("rolling_sharpe_12m") or {}).get(k) for k in rolling_keys}

    eq_roll_vol_12 = {k: (eq_analytics.get("rolling_vol_12m") or {}).get(k) for k in rolling_keys}
    rp_roll_vol_12 = {k: (rp_analytics.get("rolling_vol_12m") or {}).get(k) for k in rolling_keys}
    eq_vol_stability = {
        "vol_of_vol": eq_analytics.get("vol_of_vol"),
        "rel_vol_of_vol": eq_analytics.get("rel_vol_of_vol"),
    }
    rp_vol_stability = {
        "vol_of_vol": rp_analytics.get("vol_of_vol"),
        "rel_vol_of_vol": rp_analytics.get("rel_vol_of_vol"),
    }

    eq_rc_top5 = _top_n_rc(eq.get("rc_asset", {}), n=5)
    rp_rc_top5 = _top_n_rc(rp.get("rc_asset", {}), n=5)
    all_top5_tickers = sorted(set(eq_rc_top5.keys()) | set(rp_rc_top5.keys()))
    delta_rc_top5 = {
        t: _round_scalar(_safe_delta(eq_rc_top5.get(t), rp_rc_top5.get(t)))
        for t in all_top5_tickers
    }

    comparison = {
        "pair": "Equal-Weight vs Risk-Parity",
        "delta_definition": "delta = equal_weight - risk_parity",
        "period": {
            "analysis_end": analysis_end,
            "window_months": int(window_months),
            "window_label": "10y" if int(window_months) == 120 else f"{int(window_months)}m",
        },
        "equal_weight": {
            "label": eq.get("label"),
            "status": eq.get("status"),
            "stress_status": eq.get("stress_status"),
            "stress_fail_reason": eq.get("stress_fail_reason"),
            "portfolio_valid": eq.get("portfolio_valid"),
            "metrics": _round_dict(eq_flat),
            "rc_asset": _round_dict(eq.get("rc_asset") or {}),
        },
        "risk_parity": {
            "label": rp.get("label"),
            "status": rp.get("status"),
            "stress_status": rp.get("stress_status"),
            "stress_fail_reason": rp.get("stress_fail_reason"),
            "portfolio_valid": rp.get("portfolio_valid"),
            "metrics": _round_dict(rp_flat),
            "rc_asset": _round_dict(rp.get("rc_asset") or {}),
        },
        "delta": {
            "metrics": delta_metrics,
            "rc_asset": delta_rc_asset,
        },
        "rolling": {
            "sharpe_36m": {
                "equal_weight": _round_dict(eq_roll_sharpe_36),
                "risk_parity": _round_dict(rp_roll_sharpe_36),
                "delta": _delta_nested_dict(eq_roll_sharpe_36, rp_roll_sharpe_36),
            },
            "sharpe_12m": {
                "equal_weight": _round_dict(eq_roll_sharpe_12),
                "risk_parity": _round_dict(rp_roll_sharpe_12),
                "delta": _delta_nested_dict(eq_roll_sharpe_12, rp_roll_sharpe_12),
            },
            "vol_12m": {
                "equal_weight": _round_dict(eq_roll_vol_12),
                "risk_parity": _round_dict(rp_roll_vol_12),
                "delta": _delta_nested_dict(eq_roll_vol_12, rp_roll_vol_12),
            },
            "vol_stability": {
                "equal_weight": _round_dict(eq_vol_stability),
                "risk_parity": _round_dict(rp_vol_stability),
                "delta": _delta_nested_dict(eq_vol_stability, rp_vol_stability),
            },
        },
        "rc_vol_top5_asset": {
            "equal_weight": _round_dict(eq_rc_top5),
            "risk_parity": _round_dict(rp_rc_top5),
            "delta": delta_rc_top5,
        },
    }

    out_json = out_dir / "ew_rp_comparison.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(comparison, f, ensure_ascii=False, indent=2)

    lines = [
        "Equal-Weight vs Risk-Parity",
        "=" * 90,
        f"Analysis period: {comparison['period']['window_label']} (window_months={comparison['period']['window_months']}), analysis_end={comparison['period']['analysis_end']}",
        "Delta rule: EW - RP",
        "",
        f"{'Metric':<28} {'EW':>14} {'RP':>14} {'Delta':>14}",
        "-" * 90,
    ]

    pct_metrics = {"cagr", "vol_annual", "max_drawdown", "es_95", "es_99", "downside_deviation_annual"}
    for k in metric_keys:
        lines.append(
            f"{k:<28} {_fmt(eq_flat.get(k), pct=(k in pct_metrics)):>14} "
            f"{_fmt(rp_flat.get(k), pct=(k in pct_metrics)):>14} "
            f"{_fmt(delta_metrics.get(k), pct=(k in pct_metrics)):>14}"
        )

    lines.extend(
        [
            "",
            "Rolling Sharpe 36m (last/mean/p10/p90):",
            f"- EW: {_fmt(eq_roll_sharpe_36.get('last'))} / {_fmt(eq_roll_sharpe_36.get('mean'))} / {_fmt(eq_roll_sharpe_36.get('p10'))} / {_fmt(eq_roll_sharpe_36.get('p90'))}",
            f"- RP: {_fmt(rp_roll_sharpe_36.get('last'))} / {_fmt(rp_roll_sharpe_36.get('mean'))} / {_fmt(rp_roll_sharpe_36.get('p10'))} / {_fmt(rp_roll_sharpe_36.get('p90'))}",
            f"- Delta (EW-RP): {_fmt(_safe_delta(eq_roll_sharpe_36.get('last'), rp_roll_sharpe_36.get('last')))} / {_fmt(_safe_delta(eq_roll_sharpe_36.get('mean'), rp_roll_sharpe_36.get('mean')))} / {_fmt(_safe_delta(eq_roll_sharpe_36.get('p10'), rp_roll_sharpe_36.get('p10')))} / {_fmt(_safe_delta(eq_roll_sharpe_36.get('p90'), rp_roll_sharpe_36.get('p90')))}",
            "",
            "Rolling Sharpe 12m (last/mean/p10/p90):",
            f"- EW: {_fmt(eq_roll_sharpe_12.get('last'))} / {_fmt(eq_roll_sharpe_12.get('mean'))} / {_fmt(eq_roll_sharpe_12.get('p10'))} / {_fmt(eq_roll_sharpe_12.get('p90'))}",
            f"- RP: {_fmt(rp_roll_sharpe_12.get('last'))} / {_fmt(rp_roll_sharpe_12.get('mean'))} / {_fmt(rp_roll_sharpe_12.get('p10'))} / {_fmt(rp_roll_sharpe_12.get('p90'))}",
            f"- Delta (EW-RP): {_fmt(_safe_delta(eq_roll_sharpe_12.get('last'), rp_roll_sharpe_12.get('last')))} / {_fmt(_safe_delta(eq_roll_sharpe_12.get('mean'), rp_roll_sharpe_12.get('mean')))} / {_fmt(_safe_delta(eq_roll_sharpe_12.get('p10'), rp_roll_sharpe_12.get('p10')))} / {_fmt(_safe_delta(eq_roll_sharpe_12.get('p90'), rp_roll_sharpe_12.get('p90')))}",
            "",
            "Rolling Vol 12m (last/mean/p10/p90):",
            f"- EW: {_fmt(eq_roll_vol_12.get('last'), pct=True)} / {_fmt(eq_roll_vol_12.get('mean'), pct=True)} / {_fmt(eq_roll_vol_12.get('p10'), pct=True)} / {_fmt(eq_roll_vol_12.get('p90'), pct=True)}",
            f"- RP: {_fmt(rp_roll_vol_12.get('last'), pct=True)} / {_fmt(rp_roll_vol_12.get('mean'), pct=True)} / {_fmt(rp_roll_vol_12.get('p10'), pct=True)} / {_fmt(rp_roll_vol_12.get('p90'), pct=True)}",
            f"- Delta (EW-RP): {_fmt(_safe_delta(eq_roll_vol_12.get('last'), rp_roll_vol_12.get('last')), pct=True)} / {_fmt(_safe_delta(eq_roll_vol_12.get('mean'), rp_roll_vol_12.get('mean')), pct=True)} / {_fmt(_safe_delta(eq_roll_vol_12.get('p10'), rp_roll_vol_12.get('p10')), pct=True)} / {_fmt(_safe_delta(eq_roll_vol_12.get('p90'), rp_roll_vol_12.get('p90')), pct=True)}",
            "",
            "Vol stability:",
            f"- vol_of_vol: EW={_fmt(eq_vol_stability.get('vol_of_vol'))} | RP={_fmt(rp_vol_stability.get('vol_of_vol'))} | Delta={_fmt(_safe_delta(eq_vol_stability.get('vol_of_vol'), rp_vol_stability.get('vol_of_vol')))}",
            f"- rel_vol_of_vol: EW={_fmt(eq_vol_stability.get('rel_vol_of_vol'))} | RP={_fmt(rp_vol_stability.get('rel_vol_of_vol'))} | Delta={_fmt(_safe_delta(eq_vol_stability.get('rel_vol_of_vol'), rp_vol_stability.get('rel_vol_of_vol')))}",
            "",
            "RC_vol by asset (EW, RP, Delta):",
        ]
    )
    for t in all_tickers:
        ew_t = eq.get("rc_asset", {}).get(t)
        rp_t = rp.get("rc_asset", {}).get(t)
        d_t = delta_rc_asset.get(t)
        lines.append(f"- {t}: EW={_fmt(ew_t, pct=True)} | RP={_fmt(rp_t, pct=True)} | Delta={_fmt(d_t, pct=True)}")

    lines.extend(["", "RC_vol top-5 assets (EW, RP, Delta):"])
    for t in all_top5_tickers:
        lines.append(
            f"- {t}: EW={_fmt(eq_rc_top5.get(t), pct=True)} | RP={_fmt(rp_rc_top5.get(t), pct=True)} | Delta={_fmt(delta_rc_top5.get(t), pct=True)}"
        )

    lines.extend(
        [
            "",
            "Statuses:",
            f"- EW stress: {eq.get('stress_status')} ({eq.get('stress_fail_reason')}) | portfolio_valid={eq.get('portfolio_valid')}",
            f"- RP stress: {rp.get('stress_status')} ({rp.get('stress_fail_reason')}) | portfolio_valid={rp.get('portfolio_valid')}",
        ]
    )

    out_txt = out_dir / "ew_rp_comparison.txt"
    with open(out_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Comparison written to {out_json} and {out_txt}")

    try:
        from src.pdf_reports import try_rebuild_pdfs_only

        try_rebuild_pdfs_only(logger=logger)
    except Exception as e:
        logger.warning("PDF suite rebuild skipped: %s", e)


if __name__ == "__main__":
    main()

