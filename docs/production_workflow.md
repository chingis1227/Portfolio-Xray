# Production Workflow: What Blocks, What Does Not

This document is the single source of truth for **what prevents writing portfolio weights** and **how to interpret run status** when using the system in production. It aligns with **portfolio_construction_policy.md** § Production workflow (implementation).

---

## 1. Hard gate (weights NOT written)

Weights are **not** written when any of the following holds:

| Gate | Condition | Result |
|------|-----------|--------|
| **MaxDD** | Mandate `target_max_drawdown_pct` is set and either (a) worst stress scenario loss exceeds it, or (b) realized historical max drawdown on the primary window exceeds it | Weights are **not** written. `run_result.json` has `status: FAIL_MAX_DD`, empty `weights`, and `next_actions`. |
| **Stress** | Config `strict_stress_gate: true` and Stress Judge returns **FAIL_STRESS** | Weights are **not** written. `run_result.json` has `status: FAIL_STRESS`, empty `weights`, and `next_actions`. |

When `strict_stress_gate` is false (default), Stress Judge failure is only recorded as a violation and weights **are** still written.

All other checks (RB corridor, RC caps, feasibility) either cause an early exit without optimization (FAIL_FEASIBILITY, FAIL_DATA, FAIL_RC) or are recorded as **violations** while weights **are still written**.

RB target search order used by optimization:

1. midpoint target from `rc_block_targets`;
2. profile `min/max` range search (if `rc_block_target_ranges` is available);
3. expanded range search (`min - 5 pp`, `max + 5 pp`, clipped to `[0, 1]`).

The RB corridor validator is applied to each tested target and still uses target ± 5 pp by default.

---

## 2. Early exits (no optimization or no weights)

| Status | When | Weights written? |
|--------|------|------------------|
| **FAIL_DATA** | Invalid config, missing data, or insufficient history after inner join | No |
| **FAIL_FEASIBILITY** | Structural RB achievability check fails (e.g. not enough instruments in a block to meet risk budget) | No |
| **FAIL_RC** | RC post-processing cannot satisfy RC caps and `rc_policy_mode` is strict | No |
| **FAIL_MAX_DD** | MaxDD gate failed (see above) | No |
| **FAIL_STRESS** | `strict_stress_gate: true` and Stress Judge returned FAIL_STRESS | No |

In all these cases, `run_result.json` is written with the corresponding status, empty or no weights, and `next_actions` for remediation.

---

## 3. Successful write with status and violations

When the MaxDD gate passes, weights are always written. Status and violations indicate quality:

| Status | Meaning | Use weights for execution? |
|--------|---------|-----------------------------|
| **APPROVED** | RB within corridor, no RC breach, no stress failure, no fallback | Yes. Safe to use as target weights. |
| **CANDIDATE_RB_BREACH** | Realized block RC (Growth/Duration/Inflation) is outside target ± corridor (e.g. ±5 pp) | Use with caution. Consider re-running with wider corridor or more instruments; or accept and monitor. |
| **OK_FALLBACK** | Solver used fallback and/or per-asset RC cap is violated (see `rc_breaches` in run_result) | Check `run_result.json` violations and `rc_breaches`. If acceptable for mandate, can use; otherwise re-run or relax constraints. |

**Stress Judge:** If stress validation fails, a **FAIL_STRESS** violation is added to `run_result.violations` and `stress_summary` is set; weights are still written. The policy is to treat this as a signal to review architecture (e.g. liquidity, duration, growth share), not to block execution automatically.

---

## 4. Summary

- **Only MaxDD** is a hard gate: if it fails, weights are not written.
- **FAIL_DATA, FAIL_FEASIBILITY, FAIL_RC** are early exits: no weights file.
- **APPROVED / CANDIDATE_RB_BREACH / OK_FALLBACK** all mean weights were written; use status and `violations` to decide whether to use them for trading and whether to re-run.

See **portfolio_construction_policy.md** §2 (Rule hierarchy) and § Production workflow (implementation) for the full policy context.
