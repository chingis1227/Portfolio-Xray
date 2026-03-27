---
title: "IPS Summary — Policy Run"
subtitle: "Main portfolio"
date: "2026-03-28 00:24 Центральная Европа (зима)"
documentclass: article
geometry: margin=1in
fontsize: 11pt
---
## Report scope / source context
- **Source:** `C:/Users/ShumeikoYe/OneDrive/Рабочий стол/Курсор Новый Изменения/Main portfolio/ips_summary.txt`
- **Generated:** 2026-03-28 00:24 Центральная Европа (зима)

## Executive summary
_See numbered sections below._

## Detailed results

### 1. Mandate parameters

- Target volatility (annual):  17.0%
- Max drawdown limit:          35.0%
- Horizon (years):             10.0
- Investor currency:           USD
- Client profile:              Aggressive

### 2. Mandate check (blocking)

- Run status:                  OK_FALLBACK
- Historical MaxDD pass:       True
- Realized MaxDD (full hist.): -22.46%
- History window:              2018-07-31 00:00:00 .. 2026-03-31 00:00:00 (93 months)
- Note: Only this historical MaxDD vs mandate can block weight release.

### 3. Final portfolio weights

- VOO: 0.170
- QQQ: 0.146
- SMH: 0.107
- URA: 0.097
- COPX: 0.083
- ITA: 0.068
- GLD: 0.057
- SCHP: 0.044
- BIL: 0.029
- SLV: 0.025
- BBJP: 0.019
- BND: 0.019
- CIBR: 0.019
- ROBO: 0.019
- SCHD: 0.019
- VDC: 0.019
- VGK: 0.019
- VT: 0.019
- VWO: 0.019
- (sum: 0.997)

### 4. Risk contribution by block (actual | target)

- Growth: 94.63% | target 90.00% (+4.6 pp)
- Duration: 0.33% | target 5.00% (-4.7 pp)
- Inflation: 5.04% | target 5.00% (+0.0 pp)

### 5. RC breaches (asset above cap)

- VOO: RC=15.31%, cap=15.00%
- SMH: RC=15.30%, cap=15.00%

### 6. Stress & scenario diagnostics (non-blocking for release)

- Diagnostic status:   DIAG_ATTENTION
- Diagnostic codes:    DIAG_RC_TOP1_EQUITY_SHOCK, DIAG_RC_TOP1_CREDIT_SHOCK, DIAG_RC_TOP1_RATES_SHOCK, DIAG_RC_TOP1_INFLATION_STAGFLATION, DIAG_RC_TOP1_LIQUIDITY_SHOCK
- Primary code:        DIAG_RC_TOP1_EQUITY_SHOCK
- Worst scenario loss: -31.08% (informational)
- Failed scenario:     equity_shock
- Note: Synthetic shocks & episode checks do not block weights; review with PM.

### 7. Violations

- RC_VIOLATION: iterations=200 | remaining_violators=['VOO', 'SMH'] | reason=max_iterations
- VIOL_RC_ASSET_CAP: [{'ticker': 'VOO', 'rc_pct': 15.31, 'cap_pct': 15.0}, {'ticker': 'SMH', 'rc_pct': 15.3, 'cap_pct': 15.0}]
- FAIL_STRESS: note=diagnostic_only | diagnostic_codes=['DIAG_RC_TOP1_EQUITY_SHOCK', 'DIAG_RC_TOP1_CREDIT_SHOCK', 'DIAG_RC_TOP1_RATES_SHOCK', 'DIAG_RC_TOP1_INFLATION_STAGFLATION', 'DIAG_RC_TOP1_LIQUIDITY_SHOCK'] | primary_diagnostic_code=DIAG_RC_TOP1_EQUITY_SHOCK | worst_scenario_loss_pct=-0.3108 | failed_scenario=equity_shock

### 8. Next actions (this run)

- Consider adding assets to dilute RC or relax rc_asset_cap; review breached tickers.
- Stress diagnostic (DIAG_*): review liquidity, duration, growth/HY — informational only.
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
