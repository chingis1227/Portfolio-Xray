# Block 2.4 Hidden Exposure — Session 07 Tail / Vol Instability

Date: 2026-05-29

Status: **CLOSED**

Prior: [Session 06 confidence v2](2026-05-29_block_2_4_session_06_confidence_v2.md)

## Scope delivered

| Item | Result |
| --- | --- |
| `tail_risk` scored: `var_95`, `var_99` | **PASS** |
| `tail_risk` scored: `downside_deviation`, `max_drawdown` | **PASS** |
| `tail_risk` scored: `pct_time_underwater`, `longest_underwater_months` | **PASS** |
| `tail_risk` scored: `unrecovered_drawdown`, `count_drawdowns_gt_5` | **PASS** |
| Evidence: `recovery_months`, `drawdown_recovered` | **PASS** |
| Evidence: `vol_of_vol`, `rel_vol_of_vol`, `rolling_volatility_12m_latest` | **PASS** |
| Vol/Sharpe limitations on `tail_risk` | **PASS** |
| Tests | **PASS** — **35 passed** (Block 2.4 + contract) |
| Golden fixture regen | **PASS** |

## Matrix rows closed (Session 07)

- D10 VaR, downside_deviation, max_drawdown, underwater, recovery, unrecovered → ✅
- D11 vol_of_vol, rel_vol_of_vol, rolling vol latest → ✅ (evidence)
- D11 Sharpe instability / regime detector → ⏸ documented in `limitations[]`

## Next

Session 08 — closed; see [Session 08 weak hedge stress](2026-05-29_block_2_4_session_08_weak_hedge_stress.md).
