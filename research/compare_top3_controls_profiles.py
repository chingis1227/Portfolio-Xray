"""
Research experiment:
1) Baseline: current optimizer (per-asset RC cap only).
2) Soft top3 control: keep per-asset RC cap + try to reduce top3 RC sum to soft target.
3) Hard top3 control: keep per-asset RC cap + try to reduce top3 RC sum to hard target.

Runs on cached monthly returns and compares profiles:
- balanced
- growth
- aggressive
"""
from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import apply_profile_override, load_validated_config
from src.block_selection import apply_block_selection
from src.optimization import (
    build_bounds,
    get_risk_portfolio_tickers,
    rc_by_asset_from_weights,
    rc_by_block_from_weights,
    run_risk_budget_optimization,
    ticker_to_block_map,
)
from src.risk_contrib import build_rc_cap_per_ticker, cov_matrix_monthly, variance_p
from policy_math.feasibility import DEFAULT_RC_CAP_RB_K_MULTIPLIER, RC_CAP_MODE_GLOBAL


PROFILES = ("balanced", "growth", "aggressive")
SOFT_TOP3_TARGET = 0.55
HARD_TOP3_TARGET = 0.50
ITER_MAX = 600
STEP = 0.0025


def _pc(cols: list[str], w_dict: dict[str, float], cov_df: pd.DataFrame) -> np.ndarray:
    w = np.array([float(w_dict.get(t, 0.0)) for t in cols], dtype=float)
    cov = cov_df.reindex(index=cols, columns=cols).fillna(0.0).values
    vp = variance_p(w, cov)
    if vp <= 1e-16:
        return np.ones(len(cols)) / len(cols)
    return (w * (cov @ w)) / vp


def _top3_sum(pc: np.ndarray) -> float:
    if pc.size <= 3:
        return float(pc.sum())
    return float(np.sort(pc)[-3:].sum())


def _enforce_top3_control(
    w_dict: dict[str, float],
    cov_df: pd.DataFrame,
    blocks: dict[str, list[str]],
    growth_core_candidates: list[str],
    rc_cap_map: dict[str, float],
    rb_growth: float,
    target_top3: float,
) -> tuple[dict[str, float], bool, dict]:
    cols = [t for t in w_dict if t in cov_df.columns and t in cov_df.index and w_dict.get(t, 0.0) > 0]
    if len(cols) < 3:
        return dict(w_dict), True, {"reason": "lt3_assets"}

    ttb = ticker_to_block_map(blocks)
    min_w = 0.01
    bounds = build_bounds(
        cols,
        ttb,
        growth_core_candidates,
        n_total=len(cols),
        min_weight=min_w,
        max_single_security_weight_pct=None,
        rb_growth=rb_growth,
    )
    lo = np.array([b[0] for b in bounds], dtype=float)
    hi = np.array([b[1] for b in bounds], dtype=float)
    w = np.array([float(w_dict.get(t, 0.0)) for t in cols], dtype=float)
    cov = cov_df.reindex(index=cols, columns=cols).fillna(0.0).values
    cap_row = np.array([float(rc_cap_map.get(t, 1.0)) for t in cols], dtype=float)

    # recipients: core eq then defensive low-vol
    vol = np.sqrt(np.maximum(np.diag(cov), 1e-20))
    defensive = [(t, vol[i]) for i, t in enumerate(cols) if ttb.get(t) in ("Duration", "Inflation")]
    defensive.sort(key=lambda x: (x[1], x[0]))
    rec_order = [t for t in ("VOO", "VT", "VTI") if t in cols] + [t for t, _ in defensive]
    if not rec_order:
        rec_order = sorted(cols)
    rec_idx = [cols.index(t) for t in rec_order]

    def _pc_np(wv: np.ndarray) -> np.ndarray:
        vp = float(wv @ cov @ wv)
        if vp <= 1e-16:
            return np.ones_like(wv) / len(wv)
        return (wv * (cov @ wv)) / vp

    for it in range(ITER_MAX):
        pc = _pc_np(w)
        t3 = _top3_sum(pc)
        if t3 <= target_top3 + 1e-9:
            out = {t: float(w[i]) for i, t in enumerate(cols)}
            for t in w_dict:
                if t not in out:
                    out[t] = float(w_dict[t])
            return out, True, {"iterations": it, "top3": t3}

        donor = int(np.argmax(pc))
        room_down = float(w[donor] - lo[donor])
        if room_down <= 1e-12:
            break
        shift = min(STEP, room_down)
        # fill recipients with available capacity and keep per-asset RC cap
        remaining = shift
        w_new = w.copy()
        w_new[donor] -= shift
        for j in rec_idx:
            if remaining <= 1e-12:
                break
            cap_space = float(hi[j] - w_new[j])
            if cap_space <= 1e-12:
                continue
            add = min(remaining, cap_space)
            w_try = w_new.copy()
            w_try[j] += add
            pc_try = _pc_np(w_try)
            if np.all(pc_try <= cap_row + 1e-9):
                w_new = w_try
                remaining -= add
        # if couldn't place transfer safely, try next iteration with smaller shift
        if remaining > 1e-8:
            shift2 = shift * 0.4
            if shift2 <= 1e-6:
                break
            w_new = w.copy()
            w_new[donor] -= shift2
            remaining = shift2
            for j in rec_idx:
                if remaining <= 1e-12:
                    break
                cap_space = float(hi[j] - w_new[j])
                if cap_space <= 1e-12:
                    continue
                add = min(remaining, cap_space)
                w_try = w_new.copy()
                w_try[j] += add
                pc_try = _pc_np(w_try)
                if np.all(pc_try <= cap_row + 1e-9):
                    w_new = w_try
                    remaining -= add
            if remaining > 1e-8:
                break
        w = w_new

    pc_final = _pc_np(w)
    out = {t: float(w[i]) for i, t in enumerate(cols)}
    for t in w_dict:
        if t not in out:
            out[t] = float(w_dict[t])
    return out, False, {"iterations": ITER_MAX, "top3": _top3_sum(pc_final)}


def _viol_count_by_cap(w: dict[str, float], cov_df: pd.DataFrame, cap_map: dict[str, float]) -> int:
    rc = rc_by_asset_from_weights(w, cov_df)
    return sum(1 for t, v in rc.items() if v > float(cap_map.get(t, 1.0)) + 1e-9)


def run_profile(profile_id: str, returns_df: pd.DataFrame) -> list[str]:
    cfg = load_validated_config(ROOT / "config.yml")
    apply_profile_override(cfg, profile_id)

    wm = int(getattr(cfg, "primary_window_months", 120))
    br = apply_block_selection(
        cfg.blocks,
        config=cfg,
        monthly_returns=returns_df,
        window_months=wm,
        rc_block_targets=cfg.rc_block_targets,
    )
    blocks = br.get("blocks", cfg.blocks)
    dur = br.get("duration_internal_weights") if br.get("status") == "OK" else None
    inf = br.get("inflation_internal_weights") if br.get("status") == "OK" else None

    risk_tickers = [t for t in get_risk_portfolio_tickers(blocks) if t in returns_df.columns]
    ret_w = returns_df[risk_tickers].iloc[-wm:].dropna(axis=1, how="all").dropna(how="any")
    cov_df = cov_matrix_monthly(ret_w, ddof=1)
    rb_g = float((cfg.rc_block_targets or {}).get("Growth", 1.0 / 3))

    base_w, base_st = run_risk_budget_optimization(
        returns_df,
        blocks,
        cfg.rc_block_targets or {},
        cfg.growth_core_candidates,
        rc_asset_cap_pct=cfg.rc_asset_cap_pct,
        min_single_security_weight_pct=cfg.min_single_security_weight_pct,
        max_single_security_weight_pct=cfg.max_single_security_weight_pct,
        window_months=wm,
        duration_internal_weights=dur,
        inflation_internal_weights=inf,
        rb_target_ranges=getattr(cfg, "rc_block_target_ranges", None),
        rb_search_enabled=False,
        rc_cap_mode=getattr(cfg, "rc_cap_mode", RC_CAP_MODE_GLOBAL),
        rc_cap_rb_k_multiplier=float(
            getattr(cfg, "rc_cap_rb_k_multiplier", DEFAULT_RC_CAP_RB_K_MULTIPLIER)
        ),
    )
    if not base_w:
        return [f"[{profile_id}] baseline FAIL: {base_st}"]

    cap_map = build_rc_cap_per_ticker(
        blocks=blocks,
        rc_block_targets=cfg.rc_block_targets,
        rc_asset_cap_pct=cfg.rc_asset_cap_pct,
        rc_cap_mode=getattr(cfg, "rc_cap_mode", RC_CAP_MODE_GLOBAL),
        rc_cap_rb_k_multiplier=float(
            getattr(cfg, "rc_cap_rb_k_multiplier", DEFAULT_RC_CAP_RB_K_MULTIPLIER)
        ),
        n_total_for_global=max(len(risk_tickers), 1),
    )

    cols_eval = [t for t in base_w if t in cov_df.columns and t in cov_df.index and base_w.get(t, 0) > 0]
    base_top3 = _top3_sum(_pc(cols_eval, base_w, cov_df))
    base_viol = _viol_count_by_cap(base_w, cov_df, cap_map)
    base_rb = rc_by_block_from_weights(base_w, cov_df, blocks)

    soft_w, soft_ok, soft_diag = _enforce_top3_control(
        base_w,
        cov_df,
        blocks,
        cfg.growth_core_candidates,
        cap_map,
        rb_growth=rb_g,
        target_top3=SOFT_TOP3_TARGET,
    )
    hard_w, hard_ok, hard_diag = _enforce_top3_control(
        base_w,
        cov_df,
        blocks,
        cfg.growth_core_candidates,
        cap_map,
        rb_growth=rb_g,
        target_top3=HARD_TOP3_TARGET,
    )

    def _line(name: str, w: dict[str, float], ok: bool, diag: dict) -> str:
        cols = [t for t in w if t in cov_df.columns and t in cov_df.index and w.get(t, 0) > 0]
        t3 = _top3_sum(_pc(cols, w, cov_df))
        viol = _viol_count_by_cap(w, cov_df, cap_map)
        rb = rc_by_block_from_weights(w, cov_df, blocks)
        mx = max([v for v in w.values() if v > 1e-9], default=0.0)
        return (
            f"  {name}: top3={t3:.4f}, viol={viol}, max_w={mx:.3f}, "
            f"rb={rb}, ok={ok}, diag={diag}"
        )

    out = []
    out.append(f"[{profile_id}]")
    out.append(
        f"  baseline: status={base_st}, top3={base_top3:.4f}, viol={base_viol}, rb={base_rb}"
    )
    out.append(_line("soft_top3", soft_w, soft_ok, soft_diag))
    out.append(_line("hard_top3", hard_w, hard_ok, hard_diag))
    return out


def main() -> None:
    ret = pd.read_csv(ROOT / "results_csv" / "inputs" / "monthly_returns.csv", index_col=0, parse_dates=True)
    lines: list[str] = []
    lines.append("=== Compare additional top3 controls (with per-asset RC cap kept) ===")
    lines.append(f"soft_target={SOFT_TOP3_TARGET:.2f}, hard_target={HARD_TOP3_TARGET:.2f}")
    lines.append("")
    for p in PROFILES:
        lines.extend(run_profile(p, ret))
        lines.append("")
    out_path = ROOT / "research" / "top3_controls_profiles_comparison.txt"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Written {out_path}")


if __name__ == "__main__":
    main()

