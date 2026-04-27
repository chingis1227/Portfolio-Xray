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

- Run status: OK_FALLBACK
- Historical MaxDD в норме по проверке: True
- Realized MaxDD (full hist.): -12.72%
- History window: 2018-07-31 00:00:00 .. 2026-04-30 00:00:00 (94 months)
- Note: Only this historical MaxDD vs mandate can block weight release.

### 3. Final portfolio weights

- BIL: 0.256
- GLD: 0.074
- SCHP: 0.074
- VDC: 0.074
- BBJP: 0.064
- VWO: 0.062
- VOO: 0.061
- SCHD: 0.060
- VT: 0.055
- VGK: 0.050
- ITA: 0.046
- SLV: 0.025
- COPX: 0.007
- QQQ: 0.007
- URA: 0.007
- (sum: 0.922)

### 4. Per-asset RC vs cap (if any breaches)

- VOO: RC=10.66%, cap=10.00%
- VT: RC=10.01%, cap=10.00%
- VWO: RC=10.00%, cap=10.00%
- SCHD: RC=10.01%, cap=10.00%

### 5. Stress & scenario diagnostics (non-blocking for release)

- Diagnostic status:
- Diagnostic codes: сильный обвал на рынке акций, стресс на рынке кредита, , ,
- Primary code: сильный обвал на рынке акций
- Worst scenario loss: -14.00% (informational)
- Failed scenario: сильный обвал на рынке акций
- Note: Synthetic shocks & episode checks do not block weights; review with PM.

### 6. Violations

- VIOL_RC_VIOLATION: iterations=200 | remaining_violators=['VOO', 'VT', 'VWO', 'SCHD'] | reason=max_iterations
- VIOL_RC_ASSET_CAP: [{'ticker': 'VOO', 'rc_pct': 10.66, 'cap_pct': 10.0}, {'ticker': 'VT', 'rc_pct': 10.01, 'cap_pct': 10.0}, {'ticker': 'VWO', 'rc_pct': 10.0, 'cap_pct': 10.0}, {'ticker': 'SCHD', 'rc_pct': 10.01, 'cap_pct': 10.0}]
- VIOL_ : note=diagnostic_only | diagnostic_codes=[' сильный обвал на рынке акций', ' стресс на рынке кредита', ' ', ' ', ' '] | primary_diagnostic_code= сильный обвал на рынке акций

### 7. Next actions (this run)

- Consider adding assets to dilute RC or relax rc_asset_cap; review breached tickers.
- Stress diagnostic (DIAG_*): informational only; review scenario loss and RC concentration.

### 8. Actions by status (reference)

APPROVED Use weights as target; safe to execute.

OK_FALLBACK Check rc_breaches above; use if acceptable for mandate.

Historical MaxDD vs mandate failed or history insufficient; weights not written.

DIAG_* / (violation) Stress diagnostics only; does not block release (review PM).

/RC/FEAS Weights not written. Follow next_actions above.

