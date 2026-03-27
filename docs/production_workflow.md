# Production Workflow: What Blocks, What Does Not

This document is the single source of truth for **what prevents writing portfolio weights** and **how to interpret run status** when using the system in production. It aligns with **portfolio_construction_policy.md** § Production workflow (implementation).

---

## 1. Hard gate (weights NOT written)

Weights are **not** written when any of the following holds:

| Gate | Condition | Result |
|------|-----------|--------|
| **FAIL_MANDATE** | Mandate `target_max_drawdown_pct` is set and **realized portfolio max drawdown on the full overlapping monthly history** (all months where every held asset has a return) is **worse** than the limit, **or** the check is **inconclusive** (insufficient overlapping history) | Weights are **not** written. `run_result.json` has `status: FAIL_MANDATE`, `mandate_check` with period and depth, empty `weights`, and `next_actions`. |

**Stress / scenarios:** Synthetic scenario losses (equity −40%, etc.), historical **episodes** (2008 / 2020 / 2022 windows), Role/RC concentration flags, and **`DIAG_*` codes** are **diagnostic only**. They **never** block weight release. Config `strict_stress_gate` is **deprecated** (logged warning only).

All other checks (RB corridor, RC caps, feasibility) either cause an early exit without optimization (FAIL_FEASIBILITY, FAIL_DATA, FAIL_RC) or are recorded as **violations** while weights **are still written**.

RB target search order used by optimization:

1. midpoint target from `rc_block_targets`;
2. profile `min/max` range search (if `rc_block_target_ranges` is available);
3. expanded range search (`min - 5 pp`, `max + 5 pp`, clipped to `[0, 1]`).

The RB corridor validator is applied to each tested target and still uses target ± 5 pp by default.

`run_result.json` includes `rb_target_selection` with:
- `stage`: `midpoint` | `range` | `expanded`
- `target`: selected RC target for `Growth/Duration/Inflation`

---

## 2. Early exits (no optimization or no weights)

| Status | When | Weights written? |
|--------|------|------------------|
| **FAIL_DATA** | Invalid config, missing data, or insufficient history after inner join | No |
| **FAIL_FEASIBILITY** | Structural RB achievability check fails (e.g. not enough instruments in a block to meet risk budget) | No |
| **FAIL_RC** | RC post-processing cannot satisfy RC caps and `rc_policy_mode` is strict | No |
| **FAIL_MANDATE** | Historical max drawdown vs mandate failed or inconclusive (see §1) | No |

**Legacy:** Older runs may show `FAIL_MAX_DD` / `FAIL_STRESS` in archived `run_result.json`; current `run_optimization.py` emits **`FAIL_MANDATE`** for the mandate gate and does **not** block on stress status.

In all **blocking** cases, `run_result.json` is written with the corresponding status, empty or no weights, and `next_actions` for remediation.

---

## 3. Successful write with status and violations

When the **mandate** gate passes, weights are written. Status and violations indicate quality:

| Status | Meaning | Use weights for execution? |
|--------|---------|-----------------------------|
| **APPROVED** | RB within corridor, no RC breach, no solver fallback | Yes. Safe to use as target weights. |
| **CANDIDATE_RB_BREACH** | Realized block RC (Growth/Duration/Inflation) is outside target ± corridor (e.g. ±5 pp) | Use with caution. Consider re-running with wider corridor or more instruments; or accept and monitor. |
| **OK_FALLBACK** | Solver used fallback and/or per-asset RC cap is violated (see `rc_breaches` in run_result) | Check `run_result.json` violations and `rc_breaches`. If acceptable for mandate, can use; otherwise re-run or relax constraints. |

**Stress diagnostics:** If `stress_diagnostic_report.status == DIAG_ATTENTION`, a violation with code **`FAIL_STRESS`** may be listed with `details.note = diagnostic_only` — **informational**, not a block. Use `stress_summary.diagnostic_codes` and `stress_diagnostic_report` for PM review.

---

## 4. Summary

- **Only FAIL_MANDATE** (historical MaxDD on full overlapping sample vs limit) is the stress/mandate **hard** gate for `run_optimization.py`.
- **FAIL_DATA, FAIL_FEASIBILITY, FAIL_RC** are other early exits: no weights file.
- **APPROVED / CANDIDATE_RB_BREACH / OK_FALLBACK** mean weights were written; use status and `violations` to decide execution and re-runs.
- **Scenario and episode stress** outputs are for **reports and PM diagnostics** only.

See **portfolio_construction_policy.md** §2 (Rule hierarchy) and § Production workflow (implementation) for the full policy context.
