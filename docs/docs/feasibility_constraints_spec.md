# Feasibility Constraints Spec (technical layer)

Defines **formulas** for derived caps used by the optimizer and RC post-processing.  
There is **no** risk-budget-by-block layer; achievability checks on Growth/Duration/Inflation shares are **removed**.

---

## Notation

- **N** — number of assets in the RiskPortfolio (excluding cash proxy, e.g. BIL).
- **min_weight** — minimum weight per held asset (from config or default 0.01 in code paths).

---

## 1. Global RC cap (per asset, share of portfolio variance)

```
if N < 4:
    rc_asset_cap = 0.40
else:
    rc_asset_cap = min(0.25, max(0.10, 1.5 / N))
```

If `rc_asset_cap_pct` in `config.yml` is set to a **positive** number, it **overrides** the formula and applies **uniformly** to every risk ticker.

---

## 2. Max weight per asset (uniform)

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

## 3. Invariant

With uniform cap **M**, feasibility requires **N × M ≥ 1.0** (otherwise long-only full investment is impossible).

---

## 4. Stress / diagnostics

Stress RC thresholds reuse **§1** (or explicit override) for Top1 RC checks; see `docs/docs/stress_testing_spec.md`.
