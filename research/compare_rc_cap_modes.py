"""
Сравнение весов RiskPortfolio: rc_cap_mode=global vs per_block_rb_k (вариант B).
Пишет research/rc_cap_mode_comparison.txt. Не меняет portfolio_weights.yml и config.yml.

Запуск из корня репозитория:
  python research/compare_rc_cap_modes.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from policy_math.feasibility import (  # noqa: E402
    DEFAULT_RC_CAP_RB_K_MULTIPLIER,
    RC_CAP_MODE_GLOBAL,
    RC_CAP_MODE_PER_BLOCK_RB_K,
)
from src.block_selection import apply_block_selection  # noqa: E402
from src.config import apply_profile_override, load_assets_metadata, load_validated_config, resolve_cash_and_rf  # noqa: E402
from src.data_loader import load_monthly_data_shared  # noqa: E402
from src.optimization import (  # noqa: E402
    get_risk_portfolio_tickers,
    rc_by_asset_from_weights,
    rc_by_block_from_weights,
    run_risk_budget_optimization,
    ticker_to_block_map,
)
from src.risk_contrib import build_rc_cap_per_ticker, cov_matrix_monthly  # noqa: E402
from src.young_etfs_dual_cov import build_dual_covariance_and_mu  # noqa: E402


def _run_branch(
    *,
    cfg,
    monthly_returns: pd.DataFrame,
    blocks,
    duration_internal_weights,
    inflation_internal_weights,
    window_months: int,
    rc_cap_mode: str,
) -> tuple[dict[str, float], str, pd.DataFrame]:
    risk_tickers = get_risk_portfolio_tickers(blocks)
    cols_primary = [t for t in risk_tickers if t in monthly_returns.columns]
    young_pol = getattr(cfg, "young_etf_optimization_policy", None) or {}
    dual_enabled = bool(young_pol.get("enabled", True))
    use_shrinkage = getattr(cfg, "covariance_shrinkage", False)

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
        ret_primary = monthly_returns[list(cov_df.columns)].iloc[-window_months:]
        w, status = run_risk_budget_optimization(
            monthly_returns,
            blocks,
            cfg.rc_block_targets,
            cfg.growth_core_candidates,
            rc_asset_cap_pct=cfg.rc_asset_cap_pct,
            min_single_security_weight_pct=cfg.min_single_security_weight_pct,
            max_single_security_weight_pct=cfg.max_single_security_weight_pct,
            window_months=window_months,
            duration_internal_weights=duration_internal_weights,
            inflation_internal_weights=inflation_internal_weights,
            returns_window=None,
            use_shrinkage=use_shrinkage,
            rb_target_ranges=getattr(cfg, "rc_block_target_ranges", None),
            cov_precomputed=cov_df,
            mu_precomputed=mu_series,
            rc_cap_mode=rc_cap_mode,
            rc_cap_rb_k_multiplier=float(
                getattr(cfg, "rc_cap_rb_k_multiplier", DEFAULT_RC_CAP_RB_K_MULTIPLIER)
            ),
        )
        return w, status, cov_df

    ret_primary = monthly_returns[cols_primary].iloc[-window_months:].dropna(axis=1, how="all").dropna(how="any")
    cols_primary = list(ret_primary.columns)
    cov_df = cov_matrix_monthly(ret_primary, ddof=1, use_shrinkage=use_shrinkage)
    w, status = run_risk_budget_optimization(
        monthly_returns,
        blocks,
        cfg.rc_block_targets,
        cfg.growth_core_candidates,
        rc_asset_cap_pct=cfg.rc_asset_cap_pct,
        min_single_security_weight_pct=cfg.min_single_security_weight_pct,
        max_single_security_weight_pct=cfg.max_single_security_weight_pct,
        window_months=window_months,
        duration_internal_weights=duration_internal_weights,
        inflation_internal_weights=inflation_internal_weights,
        returns_window=ret_primary,
        use_shrinkage=use_shrinkage,
        rb_target_ranges=getattr(cfg, "rc_block_target_ranges", None),
        rc_cap_mode=rc_cap_mode,
        rc_cap_rb_k_multiplier=float(
            getattr(cfg, "rc_cap_rb_k_multiplier", DEFAULT_RC_CAP_RB_K_MULTIPLIER)
        ),
    )
    return w, status, cov_df


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

    w_g, st_g, cov_g = _run_branch(
        cfg=cfg,
        monthly_returns=monthly_returns,
        blocks=blocks,
        duration_internal_weights=duration_internal_weights,
        inflation_internal_weights=inflation_internal_weights,
        window_months=window_months,
        rc_cap_mode=RC_CAP_MODE_GLOBAL,
    )
    w_b, st_b, cov_b = _run_branch(
        cfg=cfg,
        monthly_returns=monthly_returns,
        blocks=blocks,
        duration_internal_weights=duration_internal_weights,
        inflation_internal_weights=inflation_internal_weights,
        window_months=window_months,
        rc_cap_mode=RC_CAP_MODE_PER_BLOCK_RB_K,
    )

    risk_tickers = get_risk_portfolio_tickers(blocks)
    n_risk = max(len([t for t in risk_tickers if t in monthly_returns.columns]), 1)
    cap_glob = build_rc_cap_per_ticker(
        blocks,
        cfg.rc_block_targets,
        cfg.rc_asset_cap_pct,
        RC_CAP_MODE_GLOBAL,
        float(getattr(cfg, "rc_cap_rb_k_multiplier", DEFAULT_RC_CAP_RB_K_MULTIPLIER)),
        n_risk,
    )
    cap_b = build_rc_cap_per_ticker(
        blocks,
        cfg.rc_block_targets,
        cfg.rc_asset_cap_pct,
        RC_CAP_MODE_PER_BLOCK_RB_K,
        float(getattr(cfg, "rc_cap_rb_k_multiplier", DEFAULT_RC_CAP_RB_K_MULTIPLIER)),
        n_risk,
    )

    rb_g = (cfg.rc_block_targets or {}).get("Growth", 1 / 3)
    lines = [
        "=== Сравнение RC cap: global (§1) vs per_block_rb_k (вариант B) ===",
        f"Окно оптимизации: {window_months} мес.",
        f"Статус global: {st_g}",
        f"Статус per_block_rb_k: {st_b}",
        "",
        "--- RC по блокам (global / variant B) ---",
    ]
    if w_g:
        lines.append(str(rc_by_block_from_weights(w_g, cov_g, blocks)))
    if w_b:
        lines.append(str(rc_by_block_from_weights(w_b, cov_b, blocks)))
    lines.append("")
    lines.append("--- Примеры лимитов RC (доля дисперсии) global vs per_block ---")
    sample = sorted(set(cap_glob.keys()) & set(cap_b.keys()))[:12]
    for t in sample:
        lines.append(f"  {t}: global_cap={cap_glob[t]:.4f}  per_block_cap={cap_b[t]:.4f}")
    lines.append("")
    lines.append("--- Дельта весов (variant B − global), только |delta|>1e-4 ---")
    all_t = sorted(set(w_g or []) | set(w_b or []))
    for t in all_t:
        a = float((w_g or {}).get(t, 0.0))
        b = float((w_b or {}).get(t, 0.0))
        d = b - a
        if abs(d) > 1e-4:
            lines.append(f"  {t}: {a:.4f} -> {b:.4f}  (d={d:+.4f})")
    lines.append("")
    lines.append("--- RC по активам (variant B решение) ---")
    if w_b:
        lines.append(str(rc_by_asset_from_weights(w_b, cov_b)))

    out_path = ROOT / "research" / "rc_cap_mode_comparison.txt"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Written {out_path}")


if __name__ == "__main__":
    main()
