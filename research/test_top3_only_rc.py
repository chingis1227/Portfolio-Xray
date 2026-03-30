"""
Experimental test:
- disable per-asset RC cap in optimization
- enforce only joint concentration cap: sum of top-3 RC <= 50%

This is a standalone research script and does NOT alter the main pipeline behavior.
"""
from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import load_validated_config
from src.optimization import (
    RB_CORRIDOR_PP,
    build_bounds,
    get_risk_portfolio_tickers,
    rc_by_asset_from_weights,
    rc_by_block_from_weights,
    run_risk_budget_optimization,
    ticker_to_block_map,
)
from src.risk_contrib import cov_matrix_monthly, variance_p


def _normalize_rb(rb: dict[str, float] | None) -> dict[str, float]:
    rb = rb or {}
    g = float(rb.get("Growth", 1.0 / 3))
    d = float(rb.get("Duration", 1.0 / 3))
    i = float(rb.get("Inflation", 1.0 / 3))
    s = g + d + i
    if s <= 1e-12:
        return {"Growth": 1.0 / 3, "Duration": 1.0 / 3, "Inflation": 1.0 / 3}
    return {"Growth": g / s, "Duration": d / s, "Inflation": i / s}


def _pc(w: np.ndarray, cov: np.ndarray) -> np.ndarray:
    vp = variance_p(w, cov)
    if vp <= 1e-16:
        return np.ones_like(w) / len(w)
    return (w * (cov @ w)) / vp


def _top3_sum(pc: np.ndarray) -> float:
    if pc.size <= 3:
        return float(np.sum(pc))
    return float(np.sum(np.sort(pc)[-3:]))


def optimize_top3_only(
    returns_window: pd.DataFrame,
    blocks: dict[str, list[str]],
    rc_block_targets: dict[str, float],
    growth_core_candidates: list[str],
    top3_cap: float = 0.50,
    min_weight: float = 0.01,
    max_single_security_weight_pct: float | None = None,
) -> tuple[dict[str, float], str, pd.DataFrame]:
    cols = list(returns_window.columns)
    n = len(cols)
    ttb = ticker_to_block_map(blocks)
    rb = _normalize_rb(rc_block_targets)
    rb_g, rb_d, rb_i = rb["Growth"], rb["Duration"], rb["Inflation"]

    cov_df = cov_matrix_monthly(returns_window, ddof=1)
    cov = cov_df.values
    mu = returns_window.mean().values

    bounds = build_bounds(
        cols,
        ttb,
        growth_core_candidates,
        n,
        min_weight=min_weight,
        max_single_security_weight_pct=max_single_security_weight_pct,
        rb_growth=rb_g,
    )

    def objective(w: np.ndarray) -> float:
        return -float(np.dot(mu, w))

    def c_sum(w: np.ndarray) -> float:
        return float(np.sum(w) - 1.0)

    def c_rb_lo(block: str, target: float):
        def fn(w: np.ndarray) -> float:
            pc = _pc(w, cov)
            rc_b = sum(pc[i] for i, t in enumerate(cols) if ttb.get(t) == block)
            return float(rc_b - (target - RB_CORRIDOR_PP))
        return fn

    def c_rb_hi(block: str, target: float):
        def fn(w: np.ndarray) -> float:
            pc = _pc(w, cov)
            rc_b = sum(pc[i] for i, t in enumerate(cols) if ttb.get(t) == block)
            return float((target + RB_CORRIDOR_PP) - rc_b)
        return fn

    def c_top3(w: np.ndarray) -> float:
        return float(top3_cap - _top3_sum(_pc(w, cov)))

    constraints = [
        {"type": "eq", "fun": c_sum},
        {"type": "ineq", "fun": c_rb_lo("Growth", rb_g)},
        {"type": "ineq", "fun": c_rb_hi("Growth", rb_g)},
        {"type": "ineq", "fun": c_rb_lo("Duration", rb_d)},
        {"type": "ineq", "fun": c_rb_hi("Duration", rb_d)},
        {"type": "ineq", "fun": c_rb_lo("Inflation", rb_i)},
        {"type": "ineq", "fun": c_rb_hi("Inflation", rb_i)},
        {"type": "ineq", "fun": c_top3},
    ]

    # Start from target split by block, then equal in-block.
    x0 = np.zeros(n)
    for b, target in (("Growth", rb_g), ("Duration", rb_d), ("Inflation", rb_i)):
        idx = [i for i, t in enumerate(cols) if ttb.get(t) == b]
        if idx:
            x0[idx] = target / len(idx)
    if abs(x0.sum() - 1.0) > 1e-6:
        x0 = np.ones(n) / n
    x0 = np.clip(x0, [b[0] for b in bounds], [b[1] for b in bounds])
    x0 = x0 / x0.sum()

    res = minimize(
        objective,
        x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 1500, "ftol": 1e-9},
    )
    if not res.success:
        # Fallback: keep RB constraints hard, enforce top3 via objective penalty.
        penalty_lambda = 200.0

        def objective_penalty(w: np.ndarray) -> float:
            pc = _pc(w, cov)
            t3 = _top3_sum(pc)
            viol = max(0.0, t3 - top3_cap)
            return -float(np.dot(mu, w)) + penalty_lambda * (viol * viol)

        constraints_no_top3 = [c for c in constraints if c.get("fun") is not c_top3]
        res2 = minimize(
            objective_penalty,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints_no_top3,
            options={"maxiter": 2000, "ftol": 1e-9},
        )
        if res2.x is None:
            return {}, f"FAIL: {res.message} | FALLBACK_FAIL: {res2.message}", cov_df
        w2 = res2.x
        pc2 = _pc(w2, cov)
        t3_2 = _top3_sum(pc2)
        out2 = {t: float(w2[i]) for i, t in enumerate(cols)}
        tag = "OK_FALLBACK_PENALTY" if res2.success else "APPROX_FALLBACK_PENALTY"
        return out2, f"{tag} top3={t3_2:.4f} | msg={res2.message}", cov_df

    w = res.x
    out = {t: float(w[i]) for i, t in enumerate(cols)}
    return out, "OK", cov_df


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    cfg = load_validated_config(root / "config.yml")
    returns = pd.read_csv(root / "results_csv" / "inputs" / "monthly_returns.csv", index_col=0, parse_dates=True)

    risk_tickers = [t for t in get_risk_portfolio_tickers(cfg.blocks) if t in returns.columns]
    wm = int(getattr(cfg, "primary_window_months", 120))
    ret_w = returns[risk_tickers].iloc[-wm:].dropna(axis=1, how="all").dropna(how="any")
    if ret_w.empty:
        raise SystemExit("No data for risk window.")

    w_base, st_base = run_risk_budget_optimization(
        returns,
        cfg.blocks,
        cfg.rc_block_targets or {},
        cfg.growth_core_candidates,
        rc_asset_cap_pct=cfg.rc_asset_cap_pct,
        min_single_security_weight_pct=cfg.min_single_security_weight_pct,
        max_single_security_weight_pct=cfg.max_single_security_weight_pct,
        window_months=wm,
        rb_search_enabled=False,
        rc_cap_mode=getattr(cfg, "rc_cap_mode", "global"),
        rc_cap_rb_k_multiplier=float(getattr(cfg, "rc_cap_rb_k_multiplier", 1.25)),
    )
    cov_base = cov_matrix_monthly(ret_w, ddof=1)

    w_t3, st_t3, cov_t3 = optimize_top3_only(
        ret_w,
        cfg.blocks,
        cfg.rc_block_targets or {},
        cfg.growth_core_candidates,
        top3_cap=0.50,
        min_weight=float(cfg.min_single_security_weight_pct) if (cfg.min_single_security_weight_pct or 0) > 0 else 0.01,
        max_single_security_weight_pct=cfg.max_single_security_weight_pct,
    )

    out_lines: list[str] = []
    out_lines.append("=== Top3-only RC test (no per-asset RC cap) ===")
    out_lines.append(f"profile={cfg.client_profile}")
    out_lines.append(f"window_months={wm}")
    out_lines.append("")

    if w_base:
        rc_a_base = rc_by_asset_from_weights(w_base, cov_base)
        top3_base = sum(sorted(rc_a_base.values(), reverse=True)[:3]) if rc_a_base else float("nan")
        out_lines.append(f"BASE status: {st_base}")
        out_lines.append(f"BASE top3_rc_sum: {top3_base:.4f}")
        out_lines.append(f"BASE rc_by_block: {rc_by_block_from_weights(w_base, cov_base, cfg.blocks)}")
    else:
        out_lines.append(f"BASE status: {st_base}")

    out_lines.append("")

    if w_t3:
        rc_a_t3 = rc_by_asset_from_weights(w_t3, cov_t3)
        top3_t3 = sum(sorted(rc_a_t3.values(), reverse=True)[:3]) if rc_a_t3 else float("nan")
        out_lines.append(f"TOP3_ONLY status: {st_t3}")
        out_lines.append(f"TOP3_ONLY top3_rc_sum: {top3_t3:.4f}")
        out_lines.append(f"TOP3_ONLY rc_by_block: {rc_by_block_from_weights(w_t3, cov_t3, cfg.blocks)}")
    else:
        out_lines.append(f"TOP3_ONLY status: {st_t3}")

    out_lines.append("")
    out_lines.append("Top 10 weight deltas (TOP3_ONLY - BASE):")
    if w_base and w_t3:
        deltas = []
        for t in sorted(set(w_base) | set(w_t3)):
            d = float(w_t3.get(t, 0.0) - w_base.get(t, 0.0))
            if abs(d) > 1e-4:
                deltas.append((t, w_base.get(t, 0.0), w_t3.get(t, 0.0), d))
        deltas.sort(key=lambda x: abs(x[3]), reverse=True)
        for t, b, n, d in deltas[:10]:
            out_lines.append(f"  {t}: {b:.4f} -> {n:.4f} (d={d:+.4f})")

    out_path = root / "research" / "top3_only_rc_test.txt"
    out_path.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"Written {out_path}")


if __name__ == "__main__":
    main()

