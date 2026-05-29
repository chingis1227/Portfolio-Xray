# Block 2.4 Hidden Exposure — Session 06 Confidence v2

Date: 2026-05-29

Status: **CLOSED**

Prior: [Session 05 factor concentration](2026-05-29_block_2_4_session_05_factor_concentration.md)

## Scope delivered

| Item | Result |
| --- | --- |
| `diagnostics_meta.ruleset` / `threshold_policy` = `heuristic_v2` | **PASS** |
| `diagnostics_meta.confidence_model` = `v2` | **PASS** |
| Confidence v2 (factor penalty, cross-signal agreement, evaluable weight) | **PASS** |
| High status cap when `confidence=low` (score ≤ 69, status Medium) | **PASS** |
| Propagate Block 2.2 `data_quality_warnings` to affected alerts + block level | **PASS** |
| `weak_hedge_behavior` preliminary confidence cap at medium | **PASS** |
| Per-alert `confidence_reason` documents model v2 inputs | **PASS** |
| Tests | **PASS** — **32 passed** (Block 2.4 + contract) |
| Golden fixture regen | **PASS** |

## Matrix rows closed (Session 06)

- D13 `confidence v2` (factor, agreement, conflict) → ✅
- D13 propagate Block 2.2 history warnings → ✅
- D13 `limitations` / `confidence_reason` → complete with v2 narrative ✅

## Next

Session 07 — closed; see [Session 07 tail / vol](2026-05-29_block_2_4_session_07_tail_vol.md).
