"""
Сравнение Main-оптимизации: выборочная Sigma vs Ledoit–Wolf vs робастная (MinCovDet) на config.yml.

Не пишет portfolio_weights.yml и run_result.json. Запуск из корня:
  python compare_covariance_shrinkage_main.py
  python compare_covariance_shrinkage_main.py --variants sample,lw
  python compare_covariance_shrinkage_main.py --no-cache

Только sample vs MCD: python compare_robust_cov_main.py
"""
from __future__ import annotations

import argparse
import sys
from types import SimpleNamespace

import numpy as np
import pandas as pd

from run_optimization import load_monthly_returns
from src.config import load_validated_config
from src.config_schema import ConfigValidationError
from src.optimization import (
    get_risk_portfolio_tickers,
    portfolio_vol_annual,
    rc_by_asset_from_weights,
    run_max_return_optimization,
)
from src.risk_contrib import cov_matrix_monthly, cov_matrix_monthly_robust
from src.utils import setup_logging, logger
from src.young_etfs_dual_cov import build_dual_covariance_and_mu, per_ticker_young_weight_caps


def _frobenius(a: pd.DataFrame, b: pd.DataFrame) -> float:
    d = (a.values - b.values).ravel()
    return float(np.sqrt(np.dot(d, d)))


def _primary_optimization_branch(
    *,
    cfg,
    monthly_returns: pd.DataFrame,
    window_months: int,
    cov_mode: str = "sample",
) -> dict:
    """
    Тот же путь cov + run_max_return_optimization, что в run_optimization.py (без RC-постобработки).

    cov_mode: "sample" | "lw" | "robust" (MinCovDet на ядре dual или на full join).
    """
    if cov_mode not in ("sample", "lw", "robust"):
        return {"error": f"unknown cov_mode: {cov_mode}"}

    use_shrinkage = cov_mode == "lw"
    use_robust = cov_mode == "robust"
    cash_proxy = getattr(cfg, "cash_proxy_ticker", None) or "BIL"
    risk_tickers_all = get_risk_portfolio_tickers(list(cfg.tickers), cfg.cash_proxy_ticker)
    cols_primary = [t for t in risk_tickers_all if t in monthly_returns.columns]
    if not cols_primary:
        return {"error": "FAIL_DATA: нет доходностей по risk-тикерам"}

    young_pol = getattr(cfg, "young_etf_optimization_policy", None) or {}
    dual_enabled = bool(young_pol.get("enabled", True))
    mu_series_primary: pd.Series | None = None
    per_ticker_young_caps: dict[str, float] | None = None
    young_diagnostics: dict | None = None
    cov_df: pd.DataFrame
    fake_block_map = {t: "Risk" for t in cols_primary}

    if dual_enabled:
        cov_df, mu_series_primary, young_diagnostics = build_dual_covariance_and_mu(
            monthly_returns,
            cols_primary,
            fake_block_map,
            window_months,
            young_pol,
            use_shrinkage_on_core=use_shrinkage,
            use_robust_on_core=use_robust,
        )
        cols_primary = list(cov_df.columns)
        per_ticker_young_caps = per_ticker_young_weight_caps(
            young_diagnostics["tickers"],
            float(young_pol.get("max_weight_candidate_or_new_pct", 0.02)),
        )
        if not per_ticker_young_caps:
            per_ticker_young_caps = None
        ret_primary = monthly_returns[cols_primary].iloc[-window_months:]
    else:
        MIN_FULL_JOIN_MONTHS = 11
        ret_primary = (
            monthly_returns[cols_primary]
            .iloc[-window_months:]
            .dropna(axis=1, how="all")
            .dropna(how="any")
        )
        if len(ret_primary) < MIN_FULL_JOIN_MONTHS:
            lookback = min(monthly_returns.shape[0], max(window_months * 2, 120))
            ret_primary = (
                monthly_returns[cols_primary]
                .iloc[-lookback:]
                .dropna(axis=1, how="all")
                .dropna(how="any")
            )
            if len(ret_primary) >= MIN_FULL_JOIN_MONTHS:
                ret_primary = ret_primary.iloc[-min(window_months, len(ret_primary)) :]
        cols_primary = list(ret_primary.columns)
        if not cols_primary:
            return {"error": "FAIL_DATA: пустое окно после inner join"}
        if use_robust:
            cov_df = cov_matrix_monthly_robust(ret_primary, ddof=1)
        else:
            cov_df = cov_matrix_monthly(ret_primary, ddof=1, use_shrinkage=use_shrinkage)

    use_precomputed_cov = dual_enabled or (not dual_enabled and use_robust)
    returns_window_arg = None if use_precomputed_cov else ret_primary
    mu_precomputed_arg = mu_series_primary if dual_enabled else (ret_primary.mean() if use_robust else None)
    cov_precomputed_arg = cov_df if use_precomputed_cov else None

    vol_lam = float(getattr(cfg, "optimization_soft_vol_penalty_lambda", 0.0) or 0.0)
    ret_lam = float(getattr(cfg, "optimization_soft_return_penalty_lambda", 0.0) or 0.0)
    if vol_lam <= 0:
        vol_lam = 12.0
    if ret_lam <= 0:
        ret_lam = 8.0
    tv = getattr(cfg, "target_vol_annual", None)
    tr = getattr(cfg, "target_nominal_return_annual", None)

    weights_risk, status = run_max_return_optimization(
        monthly_returns,
        cols_primary,
        min_single_security_weight_pct=cfg.min_single_security_weight_pct,
        max_single_security_weight_pct=cfg.max_single_security_weight_pct,
        window_months=window_months,
        cash_proxy_ticker=cash_proxy,
        returns_window=returns_window_arg,
        use_shrinkage=use_shrinkage and not use_robust,
        cov_precomputed=cov_precomputed_arg,
        mu_precomputed=mu_precomputed_arg,
        per_ticker_max_weight=per_ticker_young_caps,
        soft_target_vol_annual=float(tv) if tv is not None else None,
        soft_vol_penalty_lambda=vol_lam,
        soft_target_return_annual=float(tr) if tr is not None else None,
        soft_return_penalty_lambda=ret_lam,
    )
    if not weights_risk:
        return {"error": f"optimization failed: {status}"}

    adjusted = weights_risk

    cov_sample_eval = cov_matrix_monthly(ret_primary, ddof=1, use_shrinkage=False)

    return {
        "cov_mode": cov_mode,
        "weights": adjusted,
        "weights_pre_rc": weights_risk,
        "cov_optim": cov_df,
        "cov_sample_eval": cov_sample_eval,
        "ret_primary": ret_primary,
        "status": status,
        "dual_enabled": dual_enabled,
        "young_diagnostics": young_diagnostics,
        "cols_primary": cols_primary,
        "rc_postprocess_ok": True,
        "rc_postprocess_diag": {},
        "vol_on_optim_cov": portfolio_vol_annual(adjusted, cov_df),
        "vol_on_sample_cov": portfolio_vol_annual(adjusted, cov_sample_eval),
        "rc_asset_on_optim_cov": rc_by_asset_from_weights(adjusted, cov_df),
        "rc_asset_on_sample_cov": rc_by_asset_from_weights(adjusted, cov_sample_eval),
    }


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Sample vs LW vs robust (MCD) covariance — Main path")
    parser.add_argument("--config", type=str, default=None, help="Путь к config.yml")
    parser.add_argument("--no-cache", action="store_true", help="Без кэша данных")
    parser.add_argument(
        "--variants",
        type=str,
        default="sample,lw,robust",
        help="Через запятую: sample, lw, robust (подмножество)",
    )
    args = parser.parse_args()
    setup_logging()

    try:
        cfg_path = __import__("pathlib").Path(args.config).resolve() if args.config else None
        cfg = load_validated_config(cfg_path)
    except ConfigValidationError as e:
        logger.error("Конфиг: %s", e)
        raise SystemExit(1)

    ns = SimpleNamespace(no_cache=args.no_cache)
    monthly_returns, analysis_end_str, _ = load_monthly_returns(cfg, ns)
    window_months = getattr(cfg, "primary_window_months", 120) or 120

    want = [x.strip().lower() for x in args.variants.split(",") if x.strip()]
    allowed = {"sample", "lw", "robust"}
    bad = set(want) - allowed
    if bad or not want:
        logger.error("--variants: ожидаются sample, lw, robust; получено %s", args.variants)
        raise SystemExit(1)

    common_kw = dict(
        cfg=cfg,
        monthly_returns=monthly_returns,
        window_months=window_months,
    )
    results: dict[str, dict] = {}
    for mode in want:
        results[mode] = _primary_optimization_branch(**common_kw, cov_mode=mode)

    labels = {"sample": "sample", "lw": "LW", "robust": "MCD"}
    for mode in want:
        r = results[mode]
        if r.get("error"):
            print(f"[{labels.get(mode, mode)}] ОШИБКА: {r['error']}")
            raise SystemExit(1)

    base = results[want[0]]
    print("=== Сравнение ковариации (оптимизационная Sigma) ===")
    print(f"analysis_end={analysis_end_str}, окно={window_months} мес., dual_cov={base['dual_enabled']}")
    print(f"variants={want}")
    for i, a in enumerate(want):
        for b in want[i + 1 :]:
            f = _frobenius(results[a]["cov_optim"], results[b]["cov_optim"])
            print(f"Frobenius ||Sigma_{a} - Sigma_{b}|| = {f:.6e}")
    print()

    tickers = set()
    for mode in want:
        tickers |= set(results[mode]["weights"].keys())
    tickers = sorted(tickers)

    if len(want) == 2:
        a, b = want[0], want[1]
        w0, w1 = results[a]["weights"], results[b]["weights"]
        l1 = sum(abs(w0.get(t, 0.0) - w1.get(t, 0.0)) for t in tickers)
        max_abs = max(abs(w0.get(t, 0.0) - w1.get(t, 0.0)) for t in tickers)
        print("=== Веса после RC post-process (как в Main) ===")
        print(f"L1 |dw| ({a} vs {b}) = {l1:.6f}, max |dw_i| = {max_abs:.6f}")
        print()

    col_w = max(10, max(len(labels.get(m, m)) for m in want) + 2)
    hdr_parts = [f"{'ticker':<8}"] + [f"{labels.get(m, m):>{col_w}}" for m in want]
    hdr = " ".join(hdr_parts)
    print(hdr)
    print("-" * len(hdr))
    for t in tickers:
        row = [f"{t:<8}"]
        ws = [results[m]["weights"].get(t, 0.0) for m in want]
        if all(abs(x) < 1e-8 for x in ws):
            continue
        for x in ws:
            row.append(f"{x:>{col_w}.4f}")
        print(" ".join(row))
    print()

    print("=== Вола (месячная cov -> год), Sigma_opt ===")
    parts = [f"{labels.get(m, m)}={results[m]['vol_on_optim_cov']:.4f}" for m in want]
    print("  " + "  |  ".join(parts))
    print("=== Вола на Sigma_hist (выборочная), по весам каждого варианта ===")
    for m in want:
        print(f"  {labels.get(m, m)}: {results[m]['vol_on_sample_cov']:.4f}")
    print()

    print("=== RC по активам на Sigma_opt (доля дисперсии) ===")
    for m in want:
        print(f"  {labels.get(m, m)}: ", results[m]["rc_asset_on_optim_cov"])
    print("=== RC по активам на Sigma_hist ===")
    for m in want:
        print(f"  {labels.get(m, m)}: ", results[m]["rc_asset_on_sample_cov"])
    print()

    print("=== Статусы оптимизатора ===")
    for m in want:
        st = results[m]["status"]
        print(f"{labels.get(m, m)}:", st[:220] + ("..." if len(st) > 220 else ""))
    print()
    rc_bits = "  ".join(f"{labels.get(m, m)}={results[m]['rc_postprocess_ok']}" for m in want)
    print("RC post-process OK:", rc_bits)


if __name__ == "__main__":
    main()
