# Block 2.4 Hidden Exposure — Session 05 Factor Concentration

Date: 2026-05-29

Status: **CLOSED**

Prior: [Session 04 correlation sub-signals](2026-05-29_block_2_4_session_04_correlation_subsignals.md)

## Scope delivered

| Item | Result |
| --- | --- |
| `factor_variance_contribution` + `dominant_factor_variance_share` evidence | **PASS** |
| `factor_risk_ranking` evidence | **PASS** |
| `production_factor_confidence` (all production betas) | **PASS** |
| `production_factor_betas_5y` full snapshot on `hidden_equity_beta` | **PASS** |
| `factor_beta_stability` (3Y/5Y/10Y labels) | **PASS** |
| `kalman_current_betas` (evidence only) | **PASS** |
| Supplemental betas: `beta_inf`, offset `beta_usd/cmd/vix/rr`, `beta_vix` tail | **PASS** |
| Scores unchanged (`heuristic_v1` weights) | **PASS** |
| Tests | **PASS** — **29 passed** (Block 2.4 + contract) |
| Golden fixture regen | **PASS** |

## Matrix rows closed (Session 05)

- D7 `factor_variance_contribution`, `factor_risk_ranking` / dominant factor → evidence ✅
- D7 all production betas → `production_factor_betas_5y` ✅ (scores still subset)
- D7 factor confidence all betas → `production_factor_confidence` ✅ (confidence v2 deferred Session 06)
- D7 5Y vs 10Y stability → `factor_beta_stability` ✅
- D7 Kalman current beta → `kalman_current_betas` ✅
- D8 `beta_inf`, `beta_cmd` → evidence on duration / weak_hedge ✅
- D9 offset factor betas (`usd/cmd/vix/rr`) → weak_hedge evidence ✅

## Next

Session 06 — Confidence v2 + propagate Block 2.2 history warnings.
