# Block 2.4 Hidden Exposure — Session 02 Taxonomy / Currency Sub-signals

Date: 2026-05-29

Status: **CLOSED**

Prior: [Session 01 contract stabilization](2026-05-29_block_2_4_session_01_contract_stabilization.md)

## Scope delivered

| Item | Result |
| --- | --- |
| `hidden_equity_beta`: `equity_weight`, `risk_on_weight` evidence | **PASS** |
| `duration_concentration`: `main_risk_factor_dominance_flags` | **PASS** |
| `credit_liquidity_risk`: region + asset-class concentration flags | **PASS** |
| `correlation_concentration`: currency bundle + `investor_currency_mismatch` | **PASS** |
| FX limitation on `correlation_concentration` | **PASS** |
| Scores unchanged (`heuristic_v1` weights) | **PASS** — evidence-only |
| Tests | **PASS** — 19 passed |
| Golden fixture regen | **PASS** |

## Matrix rows closed (Session 02)

- D1 equity allocation, risk_on exposure → evidence ✅
- D3 issuer/region via `region_concentration_flags` → evidence ✅ (issuer still blocked upstream)
- D6 dominant currency, USD, single_currency_dominance, investor_currency_mismatch → evidence ✅

## Next

Session 03 — Mandatory `contributing_assets[]` (max 3 per alert) via `by_asset` + taxonomy at wire time.
