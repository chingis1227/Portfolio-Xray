# Production Workflow: Release Gates

Single orientation: **when weights may be written** and **how to read status** after `run_optimization.py`. Aligned with **`portfolio_construction_policy.md`** (production workflow).

---

## 1. Hard stops (weights not written or run aborted)

Typical cases (exact list in `run_optimization.py` and log messages):

| Gate | Meaning |
|------|--------|
| **FAIL_MANDATE** | `target_max_drawdown_pct` is set and **realized** portfolio max drawdown on the **full overlapping** monthly history is worse than the limit, or the check is **not possible** (insufficient data). In `run_result.json`: `status`, `mandate_check`, empty or non-final weights per policy. |
| **FAIL_DATA** | Invalid config, missing data, FX conversion failure, etc. |

**Stress (`run_stress`):** synthetic scenarios, historical windows 2008/2020/2022, codes **DIAG_*** — **diagnostics only**. They **do not** block weight release when the mandate passes. Parameter `strict_stress_gate` is **not used as a hard stop** (legacy name may still appear in logs).

---

## 2. Successful weight write and statuses

When the mandate and other hard checks pass, weights are written. In `run_result.json`:

| Status | Meaning |
|--------|--------|
| **APPROVED** | Optimizer did not return **OK_FALLBACK** (see `optimization_status` in `run_result.json`). |
| **OK_FALLBACK** | Optimizer returned **OK_FALLBACK** (alternative solution branch); field **`rc_breaches`** remains in JSON for compatibility and is currently **empty** — RC is not a release constraint. |

`violations` may also contain stress diagnostics (**`FAIL_STRESS`** / `diagnostic_only` flag) for the PM — **not** a ban on using weights unless **FAIL_MANDATE** is present.

---

## 3. Summary

- **Blocks weight release:** first and foremost **FAIL_MANDATE**, plus **FAIL_DATA** and analogous data/config errors.
- **Does not block:** scenario stress and **DIAG_*** codes.
- Portfolio construction rules — **`portfolio_construction_policy.md`**.
