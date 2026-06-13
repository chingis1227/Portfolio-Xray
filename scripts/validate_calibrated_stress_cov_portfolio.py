"""
One-off validation: Main portfolio weights + results_csv monthly returns.
Computes base vs stressed annualized vol, RC HHI, dominant risk block per synthetic scenario.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.risk_contrib import cov_matrix_monthly, percentage_contributions_variance  # noqa: E402
from src.stress_covariance_taxonomy import stress_covariance_taxonomy_blend  # noqa: E402

SYNTH = (
    "equity_shock",
    "credit_shock",
    "rates_shock",
    "inflation_stagflation",
    "liquidity_shock",
    "recession_severe",
)


def main() -> None:
    with (ROOT / "Main portfolio" / "portfolio_weights.yml").open(encoding="utf-8") as f:
        weights = yaml.safe_load(f)
    tickers = list(weights.keys())

    ret = pd.read_csv(ROOT / "results_csv" / "inputs" / "monthly_returns.csv")
    ret["Date"] = pd.to_datetime(ret["Date"])
    ret = ret.set_index("Date")

    asset_cols = [t for t in tickers if t in ret.columns]
    w = np.array([float(weights[t]) for t in asset_cols])
    w = w / w.sum()
    returns_sub = ret[asset_cols].dropna(how="all")
    cov_base = cov_matrix_monthly(returns_sub, ddof=1)
    vol_base_ann = float(np.sqrt(max(float(w @ cov_base.values @ w), 0.0)) * np.sqrt(12.0))

    out: dict = {
        "vol_base_annualized": round(vol_base_ann, 4),
        "scenarios": [],
    }

    for sid in SYNTH:
        cov_s, diag = stress_covariance_taxonomy_blend(
            cov_base, asset_cols, sid, cash_proxy_ticker="BIL"
        )
        vol_s_ann = float(np.sqrt(max(float(w @ cov_s.values @ w), 0.0)) * np.sqrt(12.0))
        pc = percentage_contributions_variance(w, cov_s.values)
        s = pd.Series(pc, index=asset_cols).sort_values(ascending=False)
        hhi = float((s**2).sum())
        blocks = (diag.get("taxonomy_coverage") or {}).get("blocks_by_ticker") or {}
        by_block: dict[str, float] = defaultdict(float)
        for t, p in s.items():
            by_block[str(blocks.get(t, "..."))] += float(p)
        dom = max(by_block, key=lambda k: by_block[k]) if by_block else None
        top3 = list(s.head(3).index)
        out["scenarios"].append(
            {
                "scenario_id": sid,
                "vol_stress_annualized": round(vol_s_ann, 4),
                "vol_ratio_stress_to_base": round(vol_s_ann / vol_base_ann, 4) if vol_base_ann > 0 else None,
                "top1_rc_asset": s.index[0],
                "top1_rc_pct": round(float(s.iloc[0]), 4),
                "top3_rc_assets": top3,
                "top3_rc_sum_pct": round(float(s.head(3).sum()), 4),
                "rc_hhi": round(hhi, 4),
                "dominant_block": dom,
                "rc_by_block": {k: round(v, 4) for k, v in sorted(by_block.items(), key=lambda x: -x[1])},
                "stress_cov_lambda": diag.get("stress_cov_lambda"),
                "stress_cov_calibration_version": diag.get("stress_cov_calibration_version"),
                "key_rho_overrides_used": diag.get("key_rho_overrides_used"),
            }
        )

    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
