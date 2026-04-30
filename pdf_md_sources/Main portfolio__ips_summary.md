---
title: "РџРѕР»РёС‚РёРєР° Рё РїРѕСЂС‚С„РµР»СЊ: СЃРІРѕРґРєР° СЂРµР°Р»РёР·Р°С†РёРё (IPS)"
date: "РС‚РѕРіРё Р°РЅР°Р»РёР·Р° РЅР° 10-Р»РµС‚РЅРµРј РѕРєРЅРµ, РїРѕ СЃРѕСЃС‚РѕСЏРЅРёСЋ РЅР° 2026-03-31"
documentclass: article
geometry: "left=18mm, right=18mm, top=24mm, bottom=20mm, head=20pt, foot=20pt, footskip=40pt"
fontsize: 10pt
---

## РљР»СЋС‡РµРІРѕР№ РІС‹РІРѕРґ

*(РЎСѓС‚СЊ РёР·Р»РѕР¶РµРЅР° РІ **РЅСѓРјРµСЂРѕРІР°РЅРЅС‹С…** РїСѓРЅРєС‚Р°С… РЅРёР¶Рµ.)*

## Р РµР°Р»РёР·Р°С†РёСЏ: РїРѕ С€Р°РіР°Рј РїР»Р°РЅР°


### 1. Mandate parameters

- Target volatility (annual): 8.5%
- Max drawdown limit: 20.0%
- Horizon (years): 10.0
- Investor currency: USD
- Client profile: Balanced
- Construction: single-stage max expected return; soft vol/return targets; RC_vol diagnostic-only (reports/stress).

### 2. Mandate check (blocking)

- Run status: APPROVED
- Historical MaxDD РІ РЅРѕСЂРјРµ РїРѕ РїСЂРѕРІРµСЂРєРµ: True
- Realized MaxDD (full hist.): -17.65%
- History window: 2014-05-31 00:00:00 .. 2026-04-30 00:00:00 (144 months)
- Note: Only this historical MaxDD vs mandate can prevent weight release.

### 3. Final portfolio weights

- TLT: 0.222
- BND: 0.174
- SCHP: 0.164
- BIL: 0.100
- SCHD: 0.088
- GLD: 0.086
- VOO: 0.072
- SLV: 0.062
- QQQ: 0.031
- (sum: 0.999)

### 4. Risk contribution (RC_vol)

RC_vol is reported in metrics and stress (Top1/Top3) for diagnostics; not used as a construction cap in this run.


### 5. Stress & scenario diagnostics (non-blocking for release)

- Diagnostic status:
- Primary code: вЂ”
- Worst scenario loss: -11.44% (informational)
- Failed scenario: вЂ”
- Note: Synthetic shocks & episode checks do not prevent weights; review with PM.

### 6. Violations: none


### 8. Actions by status (reference)

APPROVED Use weights as target; safe to execute.

OK_FALLBACK Optimizer used a numerical fallback; review optimization_status if needed.

Historical MaxDD vs mandate failed or history insufficient; weights not written.

DIAG_* / (violation) Stress diagnostics only; does not prevent release (review PM).

Weights not written. Follow next_actions above.

