---
title: "IPS Summary — Policy Run"
subtitle: "Main portfolio"
date: "2026-03-23 23:38 Центральная Европа (зима)"
documentclass: article
geometry: margin=1in
fontsize: 11pt
---
## Report scope / source context
- **Source:** `C:/Users/ShumeikoYe/OneDrive/Рабочий стол/Cursor/Main portfolio/ips_summary.txt`
- **Generated:** 2026-03-23 23:38 Центральная Европа (зима)

## Executive summary
_See numbered sections below._

## Detailed results

### 1. Mandate parameters

- Target volatility (annual):  17.0%
- Max drawdown limit:          35.0%
- Horizon (years):             10.0
- Investor currency:           USD
- Client profile:              Aggressive

### 2. Run status: FAIL_MAX_DD


### 3. Final portfolio weights

(weights not written for this run)


### 4. Risk contribution by block (actual | target)

- Growth: 83.92% | target 90.00% (-6.1 pp)
- Duration: 0.16% | target 5.00% (-4.8 pp)
- Inflation: 15.92% | target 5.00% (+10.9 pp)

### 5. RC breaches: none


### 6. Stress summary

- Status:              FAIL_STRESS
- Fail reason:         FAIL_ROLE_EQUITY_SHOCK
- Worst scenario loss: -102.78%
- Failed scenario:     equity_shock

### 7. Violations

- RB_BREACH: Growth=-6.08 | Duration=-4.84 | Inflation=10.92
- FAIL_STRESS: fail_reason_code=FAIL_ROLE_EQUITY_SHOCK | worst_scenario_loss_pct=-1.0278 | failed_scenario=equity_shock
- MAX_DD_GATE: target_max_drawdown_pct=-0.35 | stress_worst_loss_pct=-1.0278 | stress_exceeds=True | realized_exceeds=False

### 8. Next actions (this run)

- Re-run with wider corridor (e.g., 7pp) OR relax secondary caps (weight caps) minimally.
- If still RB_BREACH: increase k_block (add instruments) in the offending block(s).
- If Growth capacity constraints prevent W_growth: add satellites or relax max_weight_sat/core caps.
- Consider: increase liquidity, shorten duration, reduce high growth/HY exposure.
- MaxDD gate (strict): stress or realized drawdown exceeds mandate; weights not written. Adjust target_max_drawdown_pct, rc_block_targets, or universe and re-run.

### 9. Actions by status (reference)

APPROVED             Use weights as target; safe to execute.

CANDIDATE_RB_BREACH  Use with caution; consider re-run or accept and monitor.

OK_FALLBACK          Check rc_breaches above; use if acceptable for mandate.

- FAIL_STRESS          If strict_stress_gate: weights not written. Review defensive blocks, liquidity.
FAIL_MAX_DD          Weights not written. Adjust target_max_drawdown_pct or risk budget.

FAIL_DATA/RC/FEAS    Weights not written. Follow next_actions above.


## Key takeaways
- Сводка отражает **последний прогон оптимизации** по policy; при смене конфигурации перезапустите пайплайн.
