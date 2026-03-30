"""
Офлайн-эксперимент по той же двухэтапной логике, что и production `run_optimization.py` (по умолчанию).
Спецификация: docs/two_stage_optimization.md.

Этап 1 — risk_skeleton (RC penalty + минимизация HHI по RC_vol); этап 2 — max return со стартом от этапа 1,
привязкой к скелету (SKEL_TRACK_LAMBDA) и мягким выравниванием под IPS/профиль:
target_vol_annual и target_nominal_return_annual из конфига (после apply_profile_override),
штрафы λ_vol / λ_ret — из optimization_soft_*_penalty_lambda или дефолты эксперимента ниже.

Пишет research/two_stage_optimization_experiment.txt. Не меняет portfolio_weights.yml и config.yml.

Запуск из корня репозитория:
  python research/two_stage_optimization_experiment.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.block_selection import apply_block_selection  # noqa: E402
from src.config import apply_profile_override, load_assets_metadata, load_validated_config, resolve_cash_and_rf  # noqa: E402
from src.data_loader import load_monthly_data_shared  # noqa: E402
from src.optimization import (  # noqa: E402
    OBJECTIVE_MODE_MAX_RETURN,
    OBJECTIVE_MODE_RISK_SKELETON,
    get_risk_portfolio_tickers,
    rc_by_asset_from_weights,
    rc_by_block_from_weights,
    run_risk_budget_optimization,
    ticker_to_block_map,
)
from src.risk_contrib import build_rc_cap_per_ticker, cov_matrix_monthly  # noqa: E402
from src.young_etfs_dual_cov import build_dual_covariance_and_mu  # noqa: E402
from policy_math.feasibility import DEFAULT_RC_CAP_RB_K_MULTIPLIER  # noqa: E402

# Привязка к скелету на этапе 2 (можно поменять и перезапустить скрипт)
STAGE2_TRACKING_LAMBDA = 10.0
# Если в config optimization_soft_*_penalty_lambda = 0 или отсутствует — используются эти значения для этапа 2
DEFAULT_EXPERIMENT_SOFT_VOL_LAMBDA = 12.0
DEFAULT_EXPERIMENT_SOFT_RET_LAMBDA = 8.0


def _risk_skeleton_conc_from_cfg(cfg) -> float:
    """Concentration lambda: 0 = только RC-штраф; иначе Herfindahl(RC)."""
    v = getattr(cfg, "risk_skeleton_concentration_lambda", None)
    if v is None:
        return 10.0
    return float(v)


def _resolved_soft_lambdas(cfg) -> tuple[float, float]:
    vl = float(getattr(cfg, "optimization_soft_vol_penalty_lambda", 0.0) or 0.0)
    rl = float(getattr(cfg, "optimization_soft_return_penalty_lambda", 0.0) or 0.0)
    if vl <= 0:
        vl = DEFAULT_EXPERIMENT_SOFT_VOL_LAMBDA
    if rl <= 0:
        rl = DEFAULT_EXPERIMENT_SOFT_RET_LAMBDA
    return vl, rl


def _run_single(
    *,
    cfg,
    monthly_returns: pd.DataFrame,
    blocks: dict,
    duration_internal_weights,
    inflation_internal_weights,
    window_months: int,
    objective_mode: str,
    warm_start_weights: dict[str, float] | None,
    skeleton_tracking_lambda: float,
    soft_target_vol_annual: float | None = None,
    soft_vol_penalty_lambda: float = 0.0,
    soft_target_return_annual: float | None = None,
    soft_return_penalty_lambda: float = 0.0,
) -> tuple[dict[str, float], str, pd.DataFrame, pd.Series]:
    risk_tickers = get_risk_portfolio_tickers(blocks)
    cols_primary = [t for t in risk_tickers if t in monthly_returns.columns]
    young_pol = getattr(cfg, "young_etf_optimization_policy", None) or {}
    dual_enabled = bool(young_pol.get("enabled", True))
    use_shrinkage = getattr(cfg, "covariance_shrinkage", False)
    cap_mode = getattr(cfg, "rc_cap_mode", "global")
    cap_mult = float(getattr(cfg, "rc_cap_rb_k_multiplier", DEFAULT_RC_CAP_RB_K_MULTIPLIER))
    pen_lam = float(getattr(cfg, "rc_cap_penalty_lambda", 25.0))

    common_kw = dict(
        rc_asset_cap_pct=cfg.rc_asset_cap_pct,
        min_single_security_weight_pct=cfg.min_single_security_weight_pct,
        max_single_security_weight_pct=cfg.max_single_security_weight_pct,
        window_months=window_months,
        duration_internal_weights=duration_internal_weights,
        inflation_internal_weights=inflation_internal_weights,
        use_shrinkage=use_shrinkage,
        rb_target_ranges=getattr(cfg, "rc_block_target_ranges", None),
        rb_search_enabled=False,
        rc_cap_mode=cap_mode,
        rc_cap_rb_k_multiplier=cap_mult,
        rc_cap_penalty_lambda=pen_lam,
        objective_mode=objective_mode,
        warm_start_weights=warm_start_weights,
        skeleton_tracking_lambda=skeleton_tracking_lambda,
        soft_target_vol_annual=soft_target_vol_annual,
        soft_vol_penalty_lambda=soft_vol_penalty_lambda,
        soft_target_return_annual=soft_target_return_annual,
        soft_return_penalty_lambda=soft_return_penalty_lambda,
        risk_skeleton_concentration_lambda=_risk_skeleton_conc_from_cfg(cfg),
    )

    if dual_enabled:
        ticker_to_rb = ticker_to_block_map(blocks)
        cov_df, mu_series, _diag = build_dual_covariance_and_mu(
            monthly_returns,
            cols_primary,
            ticker_to_rb,
            window_months,
            young_pol,
            use_shrinkage_on_core=use_shrinkage,
        )
        w, status = run_risk_budget_optimization(
            monthly_returns,
            blocks,
            cfg.rc_block_targets,
            cfg.growth_core_candidates,
            returns_window=None,
            cov_precomputed=cov_df,
            mu_precomputed=mu_series,
            **common_kw,
        )
        return w, status, cov_df, mu_series

    ret_primary = monthly_returns[cols_primary].iloc[-window_months:].dropna(axis=1, how="all").dropna(how="any")
    cov_df = cov_matrix_monthly(ret_primary, ddof=1, use_shrinkage=use_shrinkage)
    mu_series = ret_primary.mean()
    w, status = run_risk_budget_optimization(
        monthly_returns,
        blocks,
        cfg.rc_block_targets,
        cfg.growth_core_candidates,
        returns_window=ret_primary,
        **common_kw,
    )
    return w, status, cov_df, mu_series


def _portfolio_mu_var(
    w: dict[str, float],
    mu: pd.Series,
    cov_df: pd.DataFrame,
    cols: list[str],
) -> tuple[float, float]:
    v = np.array([float(w.get(t, 0.0)) for t in cols])
    mu_v = np.array([float(mu.reindex(cols).fillna(0.0).loc[t]) for t in cols])
    c = cov_df.reindex(index=cols, columns=cols).fillna(0.0).values
    mu_p = float(np.dot(mu_v, v))
    var_p = float(v @ c @ v)
    return mu_p, var_p


def _violations(w: dict[str, float], cov_df: pd.DataFrame, cap_map: dict[str, float], cols: list[str]) -> list[str]:
    rc = rc_by_asset_from_weights(w, cov_df)
    bad = []
    for t in cols:
        cap = float(cap_map.get(t, 1.0))
        rv = float(rc.get(t, 0.0))
        if rv > cap + 1e-9:
            bad.append(f"{t}: RC={rv:.4f} > cap={cap:.4f}")
    return bad


def main() -> None:
    cfg = load_validated_config("config.yml")
    prof = getattr(cfg, "client_profile", None)
    if prof:
        apply_profile_override(cfg, prof)
    window_months = int(getattr(cfg, "primary_window_months", 120))

    cash_proxy_ticker, rf_source = resolve_cash_and_rf(cfg)
    assets_meta = load_assets_metadata()
    data = load_monthly_data_shared(
        tickers=cfg.tickers,
        benchmark_base_ticker=cfg.benchmark_base_ticker,
        cash_proxy_ticker=cash_proxy_ticker,
        rf_source=rf_source,
        investor_currency=cfg.investor_currency,
        windows_months=cfg.windows_months,
        assets_meta=assets_meta,
        no_cache=False,
        local_benchmark_map=None,
    )
    monthly_returns = data.monthly_returns

    block_result = apply_block_selection(
        cfg.blocks,
        config=cfg,
        monthly_returns=monthly_returns,
        window_months=window_months,
        rc_block_targets=cfg.rc_block_targets,
    )
    blocks = block_result.get("blocks", cfg.blocks)
    duration_internal_weights = block_result.get("duration_internal_weights") if block_result.get("status") == "OK" else None
    inflation_internal_weights = block_result.get("inflation_internal_weights") if block_result.get("status") == "OK" else None

    w_base, st_base, cov_df, mu_s = _run_single(
        cfg=cfg,
        monthly_returns=monthly_returns,
        blocks=blocks,
        duration_internal_weights=duration_internal_weights,
        inflation_internal_weights=inflation_internal_weights,
        window_months=window_months,
        objective_mode=OBJECTIVE_MODE_MAX_RETURN,
        warm_start_weights=None,
        skeleton_tracking_lambda=0.0,
    )

    w1, st1, _, _ = _run_single(
        cfg=cfg,
        monthly_returns=monthly_returns,
        blocks=blocks,
        duration_internal_weights=duration_internal_weights,
        inflation_internal_weights=inflation_internal_weights,
        window_months=window_months,
        objective_mode=OBJECTIVE_MODE_RISK_SKELETON,
        warm_start_weights=None,
        skeleton_tracking_lambda=0.0,
    )

    vol_lam, ret_lam = _resolved_soft_lambdas(cfg)
    tgt_vol = getattr(cfg, "target_vol_annual", None)
    tgt_ret = getattr(cfg, "target_nominal_return_annual", None)

    w2, st2, _, _ = _run_single(
        cfg=cfg,
        monthly_returns=monthly_returns,
        blocks=blocks,
        duration_internal_weights=duration_internal_weights,
        inflation_internal_weights=inflation_internal_weights,
        window_months=window_months,
        objective_mode=OBJECTIVE_MODE_MAX_RETURN,
        warm_start_weights=w1,
        skeleton_tracking_lambda=STAGE2_TRACKING_LAMBDA,
        soft_target_vol_annual=float(tgt_vol) if tgt_vol is not None else None,
        soft_vol_penalty_lambda=vol_lam,
        soft_target_return_annual=float(tgt_ret) if tgt_ret is not None else None,
        soft_return_penalty_lambda=ret_lam,
    )

    risk_tickers = get_risk_portfolio_tickers(blocks)
    cols = [t for t in risk_tickers if t in cov_df.index and t in cov_df.columns]

    n_risk = max(len([t for t in risk_tickers if t in monthly_returns.columns]), 1)
    cap_map = build_rc_cap_per_ticker(
        blocks,
        cfg.rc_block_targets,
        cfg.rc_asset_cap_pct,
        getattr(cfg, "rc_cap_mode", "global"),
        float(getattr(cfg, "rc_cap_rb_k_multiplier", DEFAULT_RC_CAP_RB_K_MULTIPLIER)),
        n_risk,
    )

    def pack(label: str, w: dict, st: str) -> list[str]:
        mu_p, var_p = _portfolio_mu_var(w, mu_s, cov_df, cols)
        vol_m = var_p ** 0.5
        viol = _violations(w, cov_df, cap_map, cols)
        rb = rc_by_block_from_weights(w, cov_df, blocks)
        out_lines = [
            f"--- {label} ---",
            f"status: {st}",
            f"mu_monthly (blend): {mu_p:.6f}  vol_monthly: {vol_m:.6f}  vol_annual~: {vol_m * (12 ** 0.5):.6f}",
            f"RC blocks: {rb}",
            f"RC cap violations ({len(viol)}):",
        ]
        out_lines.extend(f"  {x}" for x in (viol[:15] if viol else ["(none)"]))
        return out_lines

    profile_label = getattr(cfg, "client_profile", None) or "(нет)"
    lines = [
        "=== Двухэтапная оптимизация (эксперимент) vs одноэтапный baseline ===",
        f"Профиль клиента: {profile_label}",
        f"IPS/конфиг: target_vol_annual={tgt_vol!r}  target_nominal_return_annual={tgt_ret!r}",
        f"Этап 2: мягкие штрафы λ_vol={vol_lam} λ_ret={ret_lam} (из config или дефолт эксперимента)",
        f"Окно: {window_months} мес.  stage2 SKEL_TRACK_LAMBDA={STAGE2_TRACKING_LAMBDA}",
        "rb_search_enabled=False (фиксированные rc_block_targets из конфига/профиля)",
        "",
    ]
    lines.extend(pack("Baseline (max_return, один этап)", w_base, st_base))
    lines.append("")
    lines.extend(pack("Stage 1 (risk_skeleton: RC penalty + min HHI(RC_vol))", w1, st1))
    lines.append("")
    lines.extend(pack("Stage 2 (max_return + warm_start + скелет + soft vol/return под профиль)", w2, st2))
    lines.append("")
    lines.append("--- Max |delta weight| vs baseline (stage2 - baseline) ---")
    all_t = sorted(set(w_base) | set(w2))
    diffs = [(t, float(w2.get(t, 0) - w_base.get(t, 0))) for t in all_t]
    diffs.sort(key=lambda x: -abs(x[1]))
    for t, d in diffs[:25]:
        if abs(d) > 1e-5:
            lines.append(f"  {t}: {d:+.4f}")
    lines.append("")
    lines.append("--- RC по активам (baseline / stage2), первые 12 имён ---")
    if w_base:
        ra_b = rc_by_asset_from_weights(w_base, cov_df)
        ra2 = rc_by_asset_from_weights(w2, cov_df)
        for t in cols[:12]:
            lines.append(f"  {t}: {float(ra_b.get(t, 0)):.4f} / {float(ra2.get(t, 0)):.4f}")

    out_path = ROOT / "research" / "two_stage_optimization_experiment.txt"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Written {out_path}")


if __name__ == "__main__":
    main()
