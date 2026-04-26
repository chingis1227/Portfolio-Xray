---
title: "Политика и портфель: сводка реализации (IPS)"
date: "Итоги анализа на 10-летнем окне, по состоянию на 2026-03-31"
documentclass: article
geometry: "left=18mm, right=18mm, top=24mm, bottom=20mm, head=20pt, foot=20pt, footskip=40pt"
fontsize: 10pt
---

## Ключевой вывод

*(Суть изложена в **нумерованных** пунктах ниже.)*

## Реализация: по шагам плана


### 1. Mandate parameters

- Target volatility (annual): 8.5%
- Max drawdown limit: 20.0%
- Horizon (years): 10.0
- Investor currency: USD
- Client profile: Balanced

### 2. Mandate check (blocking)

- Run status: CANDIDATE_RB_BREACH
- Historical MaxDD в норме по проверке: True
- Realized MaxDD (full hist.): -15.63%
- History window: 2018-07-31 00:00:00 .. 2026-04-30 00:00:00 (94 months)
- Note: Only this historical MaxDD vs mandate can block weight release.

### 3. Final portfolio weights

- BND: 0.360
- SCHP: 0.127
- BIL: 0.100
- GLD: 0.062
- VOO: 0.041
- VDC: 0.039
- BBJP: 0.030
- SCHD: 0.028
- VWO: 0.027
- CIBR: 0.025
- SLV: 0.024
- VT: 0.023
- VGK: 0.021
- ITA: 0.020
- QQQ: 0.020
- ROBO: 0.015
- URA: 0.015
- SMH: 0.013
- COPX: 0.011
- (sum: 1.001)

### 4. Risk contribution by block (actual | target)

- Growth: 62.15% | target 50.00% (+12.2 pp)
- Duration: 19.43% | target 38.89% (-19.5 pp)
- Inflation: 18.42% | target 11.11% (+7.3 pp)

### 5. RC breaches (asset above cap)

- VOO: RC=7.65%, cap=4.46%
- BBJP: RC=4.59%, cap=4.46%
- VWO: RC=4.49%, cap=4.46%
- VDC: RC=4.68%, cap=4.46%
- SLV: RC=5.33%, cap=4.63%
- GLD: RC=6.23%, cap=4.63%
- SCHP: RC=6.87%, cap=4.63%

### 6. Stress & scenario diagnostics (non-blocking for release)

- Diagnostic status:
- Diagnostic codes: сильный обвал на рынке акций
- Primary code: сильный обвал на рынке акций
- Worst scenario loss: -11.40% (informational)
- Failed scenario: сильный обвал на рынке акций
- Note: Synthetic shocks & episode checks do not block weights; review with PM.

### 7. Violations

- RC_VIOLATION: iterations=200 | remaining_violators=['VOO', 'BBJP', 'VWO', 'VDC', 'SLV', 'GLD', 'SCHP'] | reason=max_iterations
- RB_BREACH: Growth=12.15 | Duration=-19.46 | Inflation=7.31
- VIOL_RC_ASSET_CAP: [{'ticker': 'VOO', 'rc_pct': 7.65, 'cap_pct': 4.46}, {'ticker': 'BBJP', 'rc_pct': 4.59, 'cap_pct': 4.46}, {'ticker': 'VWO', 'rc_pct': 4.49, 'cap_pct': 4.46}, {'ticker': 'VDC', 'rc_pct': 4.68, 'cap_pct': 4.46}, {'ticker': 'SLV', 'rc_pct': 5.33, 'cap_pct': 4.63}, {'ticker': 'GLD', 'rc_pct': 6.23, 'cap_pct': 4.63}, {'ticker': 'SCHP', 'rc_pct': 6.87, 'cap_pct': 4.63}]
- : note=diagnostic_only | diagnostic_codes=[' сильный обвал на рынке акций'] | primary_diagnostic_code= сильный обвал на рынке акций | worst_scenario_loss_pct=-0.114 | failed_scenario=сильный обвал на рынке акций

### 8. Next actions (this run)

- Re-run with wider corridor (e.g., 7pp) OR relax secondary caps (weight caps) minimally.
- If still RB_BREACH: increase k_block (add instruments) in the offending block(s).
- If Growth capacity constraints prevent W_growth: add satellites or relax max_weight_sat/core caps.
- Consider adding assets to dilute RC or relax rc_asset_cap; review breached tickers.
- Stress diagnostic (DIAG_*): review liquidity, duration, growth/HY — informational only.
- RC post-processing could not satisfy RC caps (strict mode: weights not written; permissive: violation flagged). Relax rc_asset_cap_pct, add assets, or set rc_policy_mode: permissive to write weights with violation.

### 9. Actions by status (reference)

APPROVED Use weights as target; safe to execute.

CANDIDATE_RB_BREACH Use with caution; consider re-run or accept and monitor.

OK_FALLBACK Check rc_breaches above; use if acceptable for mandate.

Historical MaxDD vs mandate failed or history insufficient; weights not written.

DIAG_* / (violation) Stress diagnostics only; does not block release (review PM).

/RC/FEAS Weights not written. Follow next_actions above.

