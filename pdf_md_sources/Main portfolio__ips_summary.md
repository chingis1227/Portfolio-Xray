---
title: "IPS Summary — Policy Run"
subtitle: "Main portfolio"
date: "2026-03-31 14:50 Центральная Европа (лето)"
documentclass: article
geometry: margin=1in
fontsize: 11pt
---
## Report scope / source context
- **Source:** `C:/Users/ShumeikoYe/OneDrive/Рабочий стол/Курсор Новый Изменения/Main portfolio/ips_summary.txt`
- **Generated:** 2026-03-31 14:50 Центральная Европа (лето)

## Executive summary
_See numbered sections below._

## Detailed results

### 1. Mandate parameters

- Target volatility (annual):  8.5%
- Max drawdown limit:          20.0%
- Horizon (years):             10.0
- Investor currency:           USD
- Client profile:              Balanced

### 2. Mandate check (blocking)

- Run status:                  CANDIDATE_RB_BREACH
- Historical MaxDD pass:       True
- Realized MaxDD (full hist.): -15.73%
- History window:              2018-07-31 00:00:00 .. 2026-03-31 00:00:00 (93 months)
- Note: Only this historical MaxDD vs mandate can block weight release.

### 3. Final portfolio weights

- BND: 0.360
- SCHP: 0.127
- BIL: 0.100
- GLD: 0.059
- VOO: 0.042
- VDC: 0.038
- BBJP: 0.029
- SCHD: 0.027
- VWO: 0.027
- CIBR: 0.026
- SLV: 0.023
- VT: 0.023
- QQQ: 0.021
- VGK: 0.021
- ITA: 0.020
- ROBO: 0.016
- URA: 0.015
- SMH: 0.014
- COPX: 0.010
- (sum: 0.998)

### 4. Risk contribution by block (actual | target)

- Growth: 62.18% | target 50.00% (+12.2 pp)
- Duration: 19.42% | target 38.89% (-19.5 pp)
- Inflation: 18.40% | target 11.11% (+7.3 pp)

### 5. RC breaches (asset above cap)

- VOO: RC=7.58%, cap=4.46%
- BBJP: RC=4.55%, cap=4.46%
- VWO: RC=4.49%, cap=4.46%
- VDC: RC=4.64%, cap=4.46%
- SLV: RC=5.35%, cap=4.63%
- GLD: RC=6.19%, cap=4.63%
- SCHP: RC=6.86%, cap=4.63%

### 6. Stress & scenario diagnostics (non-blocking for release)

- Diagnostic status:   DIAG_PASS_WITH_WARNING
- Primary code:        —
- Worst scenario loss: -10.24% (informational)
- Failed scenario:     —
- Note: Synthetic shocks & episode checks do not block weights; review with PM.

### 7. Violations

- RC_VIOLATION: iterations=200 | remaining_violators=['VOO', 'BBJP', 'VWO', 'VDC', 'SLV', 'GLD', 'SCHP'] | reason=max_iterations
- RB_BREACH: Growth=12.18 | Duration=-19.46 | Inflation=7.28
- VIOL_RC_ASSET_CAP: [{'ticker': 'VOO', 'rc_pct': 7.58, 'cap_pct': 4.46}, {'ticker': 'BBJP', 'rc_pct': 4.55, 'cap_pct': 4.46}, {'ticker': 'VWO', 'rc_pct': 4.49, 'cap_pct': 4.46}, {'ticker': 'VDC', 'rc_pct': 4.64, 'cap_pct': 4.46}, {'ticker': 'SLV', 'rc_pct': 5.35, 'cap_pct': 4.63}, {'ticker': 'GLD', 'rc_pct': 6.19, 'cap_pct': 4.63}, {'ticker': 'SCHP', 'rc_pct': 6.86, 'cap_pct': 4.63}]

### 8. Next actions (this run)

- Re-run with wider corridor (e.g., 7pp) OR relax secondary caps (weight caps) minimally.
- If still RB_BREACH: increase k_block (add instruments) in the offending block(s).
- If Growth capacity constraints prevent W_growth: add satellites or relax max_weight_sat/core caps.
- Consider adding assets to dilute RC or relax rc_asset_cap; review breached tickers.
- RC post-processing could not satisfy RC caps (strict mode: weights not written; permissive: violation flagged). Relax rc_asset_cap_pct, add assets, or set rc_policy_mode: permissive to write weights with violation.

### 9. Actions by status (reference)

APPROVED             Use weights as target; safe to execute.

CANDIDATE_RB_BREACH  Use with caution; consider re-run or accept and monitor.

OK_FALLBACK          Check rc_breaches above; use if acceptable for mandate.

FAIL_MANDATE         Historical MaxDD vs mandate failed or history insufficient; weights not written.

DIAG_* / FAIL_STRESS (violation)  Stress diagnostics only; does not block release (review PM).

FAIL_DATA/RC/FEAS    Weights not written. Follow next_actions above.


## Key takeaways
- Сводка отражает **последний прогон оптимизации** по policy; при смене конфигурации перезапустите пайплайн.
