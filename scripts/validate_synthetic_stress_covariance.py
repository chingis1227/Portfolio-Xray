"""
Offline validation / calibration report for synthetic stress covariance (taxonomy_blend_v1).

Run from repo root: python scripts/validate_synthetic_stress_covariance.py

Does not change configs or optimization. Prints JSON-ish tables to stdout.
"""
from __future__ import annotations

import copy
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.risk_contrib import cov_matrix_monthly, percentage_contributions_variance
from src.stress import run_stress
import src.stress_covariance_taxonomy as tax
from src.stress_covariance_taxonomy import resolve_stress_asset_block, stress_covariance_taxonomy_blend

SCENARIOS = [
    "equity_shock",
    "credit_shock",
    "liquidity_shock",
    "recession_severe",
    "rates_shock",
    "inflation_stagflation",
]

# Diversified sleeves: labels match etf_universe taxonomy
TICKERS = ["VOO", "IEF", "HYG", "GLD", "TIP", "BIL"]
CASH = "BIL"


def _build_synthetic_monthly_returns(seed: int = 42) -> pd.DataFrame:
    """Correlated monthly simple returns ~120 months, block-roughly realistic."""
    rng = np.random.default_rng(seed)
    n = 120
    idx = pd.date_range("2015-01-31", periods=n, freq="ME")
    # latent factors: equity, rates, credit, commodity, inflation
    f_eq = rng.normal(0, 0.045, n)
    f_rr = rng.normal(0, 0.025, n)
    f_cr = 0.55 * f_eq + rng.normal(0, 0.02, n)
    f_cmd = 0.35 * f_eq + rng.normal(0, 0.035, n)
    f_inf = 0.12 * f_cmd + rng.normal(0, 0.015, n)

    voo = 0.95 * f_eq + rng.normal(0, 0.012, n)
    ief = -0.75 * f_rr + 0.12 * f_eq + rng.normal(0, 0.008, n)
    hyg = 0.45 * f_cr + 0.25 * f_eq - 0.35 * f_rr + rng.normal(0, 0.01, n)
    gld = -0.15 * f_rr + 0.22 * f_cmd + rng.normal(0, 0.018, n)
    tip = -0.55 * f_rr + 0.45 * f_inf + rng.normal(0, 0.009, n)
    bil = 0.05 * f_rr + rng.normal(0, 0.0015, n)

    df = pd.DataFrame({"VOO": voo, "IEF": ief, "HYG": hyg, "GLD": gld, "TIP": tip, "BIL": bil}, index=idx)
    return df


def _weights() -> dict[str, float]:
    return {"VOO": 0.35, "IEF": 0.20, "HYG": 0.12, "GLD": 0.10, "TIP": 0.13, "BIL": 0.10}


def _asset_betas() -> pd.DataFrame:
    """Rough factor loadings for stress PnL (same columns as stress engine)."""
    cols = ["beta_eq", "beta_rr", "beta_inf", "beta_credit", "beta_usd", "beta_cmd"]
    data = {
        "VOO": [1.0, 0.05, 0.02, 0.08, -0.05, 0.10],
        "IEF": [0.05, -6.0, 0.15, 0.02, 0.10, -0.02],
        "HYG": [0.35, -2.0, 0.05, 0.85, 0.05, 0.08],
        "GLD": [0.02, -0.4, 0.08, 0.05, -0.2, 0.65],
        "TIP": [0.08, -3.0, 0.55, 0.12, 0.02, 0.15],
        "BIL": [0.0, -0.1, 0.0, 0.0, 0.0, 0.0],
    }
    df = pd.DataFrame(data, index=cols).T
    return df.reindex(TICKERS)


def _portfolio_betas(w: dict[str, float], betas: pd.DataFrame) -> dict[str, float]:
    out = {}
    for c in betas.columns:
        out[c] = float(sum(w.get(t, 0) * betas.loc[t, c] for t in TICKERS))
    return out


def _annualized_vol(cov: np.ndarray, w: np.ndarray) -> float:
    v = float(w @ cov @ w)
    return float(math.sqrt(max(v, 0.0)) * math.sqrt(12))


def _corr_from_cov(cov: np.ndarray) -> np.ndarray:
    d = np.sqrt(np.clip(np.diag(cov), 1e-18, None))
    outer = np.outer(d, d)
    return cov / outer


def _mean_offdiag(corr: np.ndarray) -> float:
    n = corr.shape[0]
    if n < 2:
        return 0.0
    m = np.triu(corr, k=1)
    c = n * (n - 1) / 2
    return float(m.sum() / c)


def _hhi(rc: np.ndarray) -> float:
    return float(np.sum(np.square(rc)))


def _dominant_factor(pbf: dict) -> str | None:
    if not pbf:
        return None
    return max(pbf.keys(), key=lambda k: abs(float(pbf[k])))


def _backup_tax_params():
    return {
        "LAMBDA_BLEND": copy.deepcopy(tax.LAMBDA_BLEND),
        "RHO_WITHIN": copy.deepcopy(tax.RHO_WITHIN),
        "RHO_PAIR_OVERRIDES": copy.deepcopy(tax.RHO_PAIR_OVERRIDES),
        "RHO_DEFAULT_BETWEEN": copy.deepcopy(tax.RHO_DEFAULT_BETWEEN),
        "VOL_MULT_BLOCK": copy.deepcopy(tax.VOL_MULT_BLOCK),
    }


def _restore_tax_params(b: dict):
    tax.LAMBDA_BLEND = b["LAMBDA_BLEND"]
    tax.RHO_WITHIN = b["RHO_WITHIN"]
    tax.RHO_PAIR_OVERRIDES = b["RHO_PAIR_OVERRIDES"]
    tax.RHO_DEFAULT_BETWEEN = b["RHO_DEFAULT_BETWEEN"]
    tax.VOL_MULT_BLOCK = b["VOL_MULT_BLOCK"]
    tax._load_combined_universe.cache_clear()


def scenario_metrics(
    scenario_id: str,
    cov_base: pd.DataFrame,
    w_arr: np.ndarray,
    *,
    cash_proxy: str,
) -> dict:
    cov_s, diag = stress_covariance_taxonomy_blend(
        cov_base, TICKERS, scenario_id, cash_proxy_ticker=cash_proxy
    )
    rc_b = percentage_contributions_variance(w_arr, cov_base.values)
    rc_s = percentage_contributions_variance(w_arr, cov_s.values)
    ix = int(np.argmax(rc_s))
    blocks = {t: resolve_stress_asset_block(t, cash_proxy_ticker=cash_proxy).block for t in TICKERS}
    block_rc: dict[str, float] = defaultdict(float)
    for i, t in enumerate(TICKERS):
        block_rc[blocks[t]] += float(rc_s[i])
    dom_block = max(block_rc, key=lambda k: block_rc[k])
    corr_s = _corr_from_cov(cov_s.values)
    return {
        "sigma_base_ann": round(_annualized_vol(cov_base.values, w_arr), 4),
        "sigma_stress_ann": round(_annualized_vol(cov_s.values, w_arr), 4),
        "sigma_ratio": round(_annualized_vol(cov_s.values, w_arr) / max(_annualized_vol(cov_base.values, w_arr), 1e-12), 4),
        "top1_asset": TICKERS[ix],
        "top1_rc": round(float(rc_s[ix]), 4),
        "top3_rc_sum": round(float(np.sort(rc_s)[-3:].sum()), 4),
        "hhi_rc": round(_hhi(rc_s), 4),
        "mean_offdiag_corr_stress": round(_mean_offdiag(corr_s), 4),
        "dominant_block": dom_block,
        "block_rc_shares": {k: round(v, 4) for k, v in sorted(block_rc.items(), key=lambda x: -x[1])},
        "lambda": diag.get("stress_cov_lambda"),
        "missing_taxonomy": diag.get("taxonomy_coverage", {}).get("missing_tickers", []),
    }


def main() -> None:
    monthly = _build_synthetic_monthly_returns()
    w = _weights()
    w_arr = np.array([w[t] for t in TICKERS])
    betas = _asset_betas()
    pb = _portfolio_betas(w, betas)

    cov_base = cov_matrix_monthly(monthly[TICKERS], ddof=1)
    base = _backup_tax_params()

    stress_out = run_stress(
        TICKERS,
        w,
        monthly,
        betas,
        pb,
        0.25,
        cash_proxy_ticker=CASH,
        factor_returns=None,
    )

    hist = {h["episode"]: h for h in stress_out.get("historical_results") or []}

    rows = []
    factor_rows = []
    pnl_rows = []

    for sid in SCENARIOS:
        m = scenario_metrics(sid, cov_base, w_arr, cash_proxy=CASH)
        row = stress_out["scenario_results"]
        sr = next(x for x in row if x["scenario_id"] == sid)
        m["portfolio_pnl_pct"] = sr["portfolio_pnl_pct"]
        m["dominant_factor"] = _dominant_factor(sr.get("pnl_by_factor_pct") or {})
        m["pnl_by_factor"] = sr.get("pnl_by_factor_pct") or {}
        rows.append({"scenario": sid, **m})
        factor_rows.append({"scenario": sid, "dominant_factor": m["dominant_factor"], **(sr.get("pnl_by_factor_pct") or {})})
        pnl_rows.append({"scenario": sid, "pnl_pct": sr["portfolio_pnl_pct"]})

    # Differentiation: Euclidean distance on normalized feature vector
    feats = []
    for r in rows:
        feats.append(
            [
                r["top1_rc"],
                r["top3_rc_sum"],
                r["hhi_rc"],
                r["mean_offdiag_corr_stress"],
                r["sigma_ratio"],
            ]
        )
    X = np.array(feats, dtype=float)
    if X.size:
        Xn = (X - X.mean(0)) / (X.std(0) + 1e-12)
        dist = np.linalg.norm(Xn[:, None, :] - Xn[None, :, :], axis=-1)

    # Sensitivity (lambda ±0.1, vol ±10%, rho_within ±0.1, pairs ±0.1)
    sens_summary = {}
    for sid in SCENARIOS:
        baseline = scenario_metrics(sid, cov_base, w_arr, cash_proxy=CASH)
        variants = []
        for label, patch_fn in [
            ("lam_m10", lambda: _patch_lambda(sid, -0.10)),
            ("lam_p10", lambda: _patch_lambda(sid, +0.10)),
            ("vol_m10", lambda: _patch_vol_scale(sid, 0.9)),
            ("vol_p10", lambda: _patch_vol_scale(sid, 1.1)),
            ("rho_in_m10", lambda: _patch_rho_within(sid, -0.10)),
            ("rho_in_p10", lambda: _patch_rho_within(sid, +0.10)),
            ("rho_pair_m10", lambda: _patch_rho_pairs(sid, -0.10)),
            ("rho_pair_p10", lambda: _patch_rho_pairs(sid, +0.10)),
        ]:
            b = _backup_tax_params()
            try:
                patch_fn()
                mv = scenario_metrics(sid, cov_base, w_arr, cash_proxy=CASH)
                variants.append(
                    {
                        "label": label,
                        "top1": mv["top1_asset"],
                        "top1_rc": mv["top1_rc"],
                        "sigma_ratio": mv["sigma_ratio"],
                        "hhi": mv["hhi_rc"],
                    }
                )
            finally:
                _restore_tax_params(b)
        stable_top1 = len({baseline["top1_asset"]} | {v["top1"] for v in variants}) == 1
        sens_summary[sid] = {"baseline_top1": baseline["top1_asset"], "stable_top1_asset": stable_top1, "variants": variants}

    out = {
        "portfolio_tickers": TICKERS,
        "weights": w,
        "scenario_table": rows,
        "pairwise_scenario_dist": dist.tolist() if X.size else [],
        "scenario_labels": SCENARIOS,
        "historical_annual_vol_episode": {
            k: hist[k].get("vol_annualized_episode")
            for k in ("dotcom", "2008", "2020", "2022")
            if k in hist
        },
        "historical_max_dd": {k: hist[k].get("max_dd") for k in hist},
        "sensitivity": sens_summary,
    }
    print(json.dumps(out, indent=2))


def _patch_lambda(sid: str, delta: float):
    v = float(tax.LAMBDA_BLEND[sid]) + delta
    tax.LAMBDA_BLEND[sid] = max(0.05, min(0.85, v))


def _patch_vol_scale(sid: str, scale: float):
    d = tax.VOL_MULT_BLOCK[sid]
    tax.VOL_MULT_BLOCK[sid] = {k: min(2.5, float(v) * scale) for k, v in d.items()}


def _patch_rho_within(sid: str, delta: float):
    d = tax.RHO_WITHIN[sid]
    tax.RHO_WITHIN[sid] = {k: max(0.05, min(0.95, float(v) + delta)) for k, v in d.items()}


def _patch_rho_pairs(sid: str, delta: float):
    pairs = tax.RHO_PAIR_OVERRIDES.get(sid) or {}
    tax.RHO_PAIR_OVERRIDES[sid] = {k: max(-0.95, min(0.95, float(v) + delta)) for k, v in pairs.items()}


if __name__ == "__main__":
    main()
