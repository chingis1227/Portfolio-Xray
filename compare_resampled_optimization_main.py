"""
Resampled (bootstrap) оптимизация vs одна обычная на config.yml.

На каждой репликации: bootstrap строк ret_primary с возвращением, заново
cov_matrix_monthly(ret_boot), затем run_max_return_optimization с precomputed Σ.
Веса усредняются по успешным прогонам (до RC), затем один раз enforce_rc_caps_postprocess
на той же Sigma, что и у baseline (cov_optim из обычного прогона).

Не пишет portfolio_weights.yml.

  python compare_resampled_optimization_main.py
  python compare_resampled_optimization_main.py -B 200 --seed 42
"""
from __future__ import annotations

import argparse
import sys
from types import SimpleNamespace

import numpy as np

from compare_covariance_shrinkage_main import _primary_optimization_branch
from run_optimization import load_monthly_returns
from src.config import load_validated_config
from src.config_schema import ConfigValidationError
from src.optimization import (
    enforce_rc_caps_postprocess,
    portfolio_vol_annual,
    rc_by_asset_from_weights,
    run_max_return_optimization,
)
from src.risk_contrib import build_rc_cap_per_ticker, cov_matrix_monthly, resolve_rc_asset_cap
from src.utils import setup_logging, logger


def _average_weights(weight_dicts: list[dict[str, float]]) -> dict[str, float]:
    if not weight_dicts:
        return {}
    tickers: set[str] = set()
    for w in weight_dicts:
        tickers |= {t for t, x in w.items() if x and x > 1e-15}
    out = {t: float(np.mean([wd.get(t, 0.0) for wd in weight_dicts])) for t in tickers}
    s = sum(out.values())
    if s <= 1e-15:
        return {}
    return {t: out[t] / s for t in out}


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Bootstrap resampled optimization vs single run")
    parser.add_argument("--config", type=str, default=None)
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("-B", "--bootstrap-replications", type=int, default=100, help="Число bootstrap-прогонов")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    setup_logging()

    if args.bootstrap_replications < 1:
        logger.error("-B must be >= 1")
        raise SystemExit(1)

    try:
        cfg_path = __import__("pathlib").Path(args.config).resolve() if args.config else None
        cfg = load_validated_config(cfg_path)
    except ConfigValidationError as e:
        logger.error("Конфиг: %s", e)
        raise SystemExit(1)

    ns = SimpleNamespace(no_cache=args.no_cache)
    monthly_returns, analysis_end_str, _ = load_monthly_returns(cfg, ns)
    window_months = getattr(cfg, "primary_window_months", 120) or 120

    common_kw = dict(
        cfg=cfg,
        monthly_returns=monthly_returns,
        window_months=window_months,
    )
    r_single = _primary_optimization_branch(**common_kw, cov_mode="sample")
    if r_single.get("error"):
        print("Baseline ОШИБКА:", r_single["error"])
        raise SystemExit(1)

    ret_primary = r_single["ret_primary"]
    cov_ref = r_single["cov_optim"]
    cols_primary = r_single["cols_primary"]
    cash_proxy = getattr(cfg, "cash_proxy_ticker", None) or "BIL"

    per_ticker_young_caps = None
    yd = r_single.get("young_diagnostics") or {}
    if yd.get("tickers"):
        from src.young_etfs_dual_cov import per_ticker_young_weight_caps

        young_pol = getattr(cfg, "young_etf_optimization_policy", None) or {}
        per_ticker_young_caps = per_ticker_young_weight_caps(
            yd["tickers"],
            float(young_pol.get("max_weight_candidate_or_new_pct", 0.02)),
        )
        if not per_ticker_young_caps:
            per_ticker_young_caps = None

    n = len(ret_primary)
    rng = np.random.default_rng(args.seed)
    pre_rc_list: list[dict[str, float]] = []
    n_fail = 0

    rc_pen_lam = float(getattr(cfg, "rc_cap_penalty_lambda", 25.0))
    vol_lam = float(getattr(cfg, "optimization_soft_vol_penalty_lambda", 0.0) or 0.0)
    ret_lam = float(getattr(cfg, "optimization_soft_return_penalty_lambda", 0.0) or 0.0)
    if vol_lam <= 0:
        vol_lam = 12.0
    if ret_lam <= 0:
        ret_lam = 8.0
    tv = getattr(cfg, "target_vol_annual", None)
    tr = getattr(cfg, "target_nominal_return_annual", None)

    for _ in range(args.bootstrap_replications):
        idx = rng.integers(0, n, size=n)
        ret_boot = ret_primary.iloc[idx]
        cov_b = cov_matrix_monthly(ret_boot, ddof=1, use_shrinkage=False)
        mu_b = ret_boot.mean()
        w_try, st = run_max_return_optimization(
            monthly_returns,
            cols_primary,
            rc_asset_cap_pct=cfg.rc_asset_cap_pct,
            min_single_security_weight_pct=cfg.min_single_security_weight_pct,
            max_single_security_weight_pct=cfg.max_single_security_weight_pct,
            window_months=window_months,
            cash_proxy_ticker=cash_proxy,
            returns_window=None,
            use_shrinkage=False,
            cov_precomputed=cov_b,
            mu_precomputed=mu_b,
            per_ticker_max_weight=per_ticker_young_caps,
            rc_cap_penalty_lambda=rc_pen_lam,
            soft_target_vol_annual=float(tv) if tv is not None else None,
            soft_vol_penalty_lambda=vol_lam,
            soft_target_return_annual=float(tr) if tr is not None else None,
            soft_return_penalty_lambda=ret_lam,
        )
        if w_try:
            pre_rc_list.append(w_try)
        else:
            n_fail += 1

    if not pre_rc_list:
        logger.error("Все bootstrap-прогоны вернули пустые веса")
        raise SystemExit(1)

    w_avg_pre = _average_weights(pre_rc_list)
    n_risk = len([t for t in cols_primary if w_avg_pre.get(t, 0) > 0])
    rc_cap_resolved = resolve_rc_asset_cap(cfg.rc_asset_cap_pct, max(n_risk, 1))
    cap_by_ticker = build_rc_cap_per_ticker(cols_primary, cfg.rc_asset_cap_pct, max(n_risk, 1))
    min_weight_rc = (
        float(cfg.min_single_security_weight_pct)
        if (cfg.min_single_security_weight_pct is not None and cfg.min_single_security_weight_pct > 0)
        else 0.01
    )
    risk_keys = [t for t in cols_primary if w_avg_pre.get(t, 0) > 0]
    w_res_final, rc_ok_res, rc_diag_res = enforce_rc_caps_postprocess(
        w_avg_pre,
        cov_ref,
        rc_cap_resolved,
        min_weight_rc,
        cfg.max_single_security_weight_pct,
        risk_keys or cols_primary,
        per_ticker_max_weight=per_ticker_young_caps,
        rc_cap_by_ticker=cap_by_ticker,
    )

    w_base = r_single["weights"]
    tickers = sorted(set(w_base) | set(w_res_final))
    l1 = sum(abs(w_base.get(t, 0.0) - w_res_final.get(t, 0.0)) for t in tickers)
    mx = max(abs(w_base.get(t, 0.0) - w_res_final.get(t, 0.0)) for t in tickers)

    vol_b = portfolio_vol_annual(w_base, cov_ref)
    vol_r = portfolio_vol_annual(w_res_final, cov_ref)

    print("=== Resampled optimization (bootstrap rows, fresh Sigma each step) ===")
    print(f"analysis_end={analysis_end_str}, окно={window_months}, B={args.bootstrap_replications}, seed={args.seed}")
    print(f"успешных прогонов: {len(pre_rc_list)}, пустых/ошибок: {n_fail}")
    print(f"dual_cov (baseline path): {r_single['dual_enabled']}")
    print("Примечание: внутри bootstrap используется выборочная Sigma по ret_boot; dual-cov не пересобирается.")
    print()
    print(f"L1 |w_baseline - w_resampled| = {l1:.6f}, max |dw| = {mx:.6f}")
    print(f"Вола на Sigma baseline (cov_optim): baseline={vol_b:.4f}, resampled={vol_r:.4f}")
    print()
    print("RC по активам (Sigma baseline): baseline ", rc_by_asset_from_weights(w_base, cov_ref))
    print("RC по активам (Sigma baseline): resampled", rc_by_asset_from_weights(w_res_final, cov_ref))
    print()
    print("RC post baseline:", r_single["rc_postprocess_ok"], " resampled:", rc_ok_res)
    print()
    hdr = f"{'ticker':<8} {'baseline':>10} {'resampled':>10} {'diff':>10}"
    print(hdr)
    print("-" * len(hdr))
    for t in tickers:
        a, b = w_base.get(t, 0.0), w_res_final.get(t, 0.0)
        if abs(a) < 1e-8 and abs(b) < 1e-8:
            continue
        print(f"{t:<8} {a:10.4f} {b:10.4f} {b - a:10.4f}")


if __name__ == "__main__":
    main()
