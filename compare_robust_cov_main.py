"""
Отдельное сравнение: выборочная Sigma vs робастная (MinCovDet / MCD) на config.yml.

Не трогает production run_optimization и portfolio_weights.
Запуск: python compare_robust_cov_main.py
        python compare_robust_cov_main.py --no-cache
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
from src.utils import setup_logging, logger


def _frobenius(a, b) -> float:
    d = (a.values - b.values).ravel()
    return float(np.sqrt(np.dot(d, d)))


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Sample vs MinCovDet (robust) — Main path")
    parser.add_argument("--config", type=str, default=None)
    parser.add_argument("--no-cache", action="store_true")
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

    common = dict(
        cfg=cfg,
        monthly_returns=monthly_returns,
        window_months=window_months,
    )
    r_sample = _primary_optimization_branch(**common, cov_mode="sample")
    r_robust = _primary_optimization_branch(**common, cov_mode="robust")

    for label, r in [("sample", r_sample), ("MCD", r_robust)]:
        if r.get("error"):
            print(f"[{label}] ОШИБКА: {r['error']}")
            raise SystemExit(1)

    frob = _frobenius(r_sample["cov_optim"], r_robust["cov_optim"])
    w0, w1 = r_sample["weights"], r_robust["weights"]
    tickers = sorted(set(w0) | set(w1))
    l1 = sum(abs(w0.get(t, 0.0) - w1.get(t, 0.0)) for t in tickers)
    max_abs = max(abs(w0.get(t, 0.0) - w1.get(t, 0.0)) for t in tickers)

    print("=== Sample vs robust (MinCovDet) — оптимизационная Sigma ===")
    print(f"analysis_end={analysis_end_str}, окно={window_months} мес., dual_cov={r_sample['dual_enabled']}")
    print(f"Frobenius ||Sigma_sample - Sigma_MCD|| = {frob:.6e}")
    print()
    print("=== Веса после RC post-process ===")
    print(f"L1 sum |dw| = {l1:.6f}, max |dw_i| = {max_abs:.6f}")
    print()
    hdr = f"{'ticker':<8} {'w_sample':>10} {'w_MCD':>10} {'diff':>10}"
    print(hdr)
    print("-" * len(hdr))
    for t in tickers:
        a, b = w0.get(t, 0.0), w1.get(t, 0.0)
        if abs(a) < 1e-8 and abs(b) < 1e-8:
            continue
        print(f"{t:<8} {a:10.4f} {b:10.4f} {b - a:10.4f}")
    print()
    print("=== Вола (месячная cov -> год) ===")
    print(f"Sigma_opt sample: {r_sample['vol_on_optim_cov']:.4f}  |  Sigma_opt MCD: {r_robust['vol_on_optim_cov']:.4f}")
    print(f"Sigma_hist sample веса: {r_sample['vol_on_sample_cov']:.4f}  |  Sigma_hist MCD веса: {r_robust['vol_on_sample_cov']:.4f}")
    print()
    print("RC по активам Sigma_opt: sample ", r_sample["rc_asset_on_optim_cov"])
    print("RC по активам Sigma_opt: MCD    ", r_robust["rc_asset_on_optim_cov"])
    print()
    print("status sample:", r_sample["status"][:220])
    print("status MCD:   ", r_robust["status"][:220])
    print("RC post OK: sample=%s MCD=%s" % (r_sample["rc_postprocess_ok"], r_robust["rc_postprocess_ok"]))


if __name__ == "__main__":
    main()
