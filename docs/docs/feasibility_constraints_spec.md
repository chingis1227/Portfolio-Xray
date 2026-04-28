# Feasibility Constraints Spec (technical layer)

Defines **formulas** for derived **weight** caps used by the optimizer.  
**Per-asset RC_vol caps are not part of feasibility or optimization** (RC_vol remains a **reported diagnostic**; see `metrics_specification.md` and `docs/docs/stress_testing_spec.md`).

There is **no** risk-budget-by-block layer; achievability checks on Growth/Duration/Inflation shares are **removed**.

---

## Notation

- **N** — number of assets in the RiskPortfolio (excluding cash proxy, e.g. BIL).
- **min_weight** — minimum weight per held asset (from config or default 0.01 in code paths).

---

## 1. Max weight per asset (uniform)

Implemented as `resolve_max_weight_per_asset_cap(N)` in `policy_math/feasibility.py`. The same upper bound applies to **every** risk ticker (no core vs satellite split):

```
if N <= 0:
    cap = 0.0
elif N <= 3:
    cap = 0.40
else:
    cap = min(0.25, max(0.10, 2.5 / N))
```

Optional **max_single_security_weight_pct** in config tightens this cap for all names.

**Edge case:** for **N = 4**, the formula yields **M = 0.25** and **4M = 1.0**, so long-only full investment with all weights ≤ M admits **only** the equal-weight portfolio (0.25 each). With **N = 3**, **M = 0.40** and **3M > 1**, so the feasible set has positive volume.

---

## 2. Invariant

With uniform cap **M**, feasibility requires **N × M ≥ 1.0** (otherwise long-only full investment is impossible).

---

## 3. Stress / diagnostics

Stress scenarios report **Top1 / Top3 RC_vol** (share of portfolio variance under base or scenario covariance) for PM review only. **There are no RC breach flags or config thresholds** tied to suite status.

---

## Historical note (removed, pre-2026-04)

Older builds used a global **RC_asset_cap** formula by **N** plus optional `rc_asset_cap_pct` override, RC penalty in the objective, post-processing of weights, NaN-backtest gating on RC, and stress thresholds (`rc1_ok` / `rc3_ok`). That layer is **not** in the current pipeline; do not reintroduce it without a new product decision and spec revision.
