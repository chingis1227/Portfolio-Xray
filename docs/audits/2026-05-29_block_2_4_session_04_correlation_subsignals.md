# Block 2.4 Hidden Exposure — Session 04 Correlation Sub-signals

Date: 2026-05-29

Status: **CLOSED**

Prior: [Session 03 contributing assets](2026-05-29_block_2_4_session_03_contributing_assets.md)

## Scope delivered

| Item | Result |
| --- | --- |
| Block 2.2 `correlation_breakdown.avg_pairwise_correlation` | **PASS** |
| `correlation_concentration`: lowest-pair / avg / diversifying-flag evidence | **PASS** |
| `hidden_equity_beta`: `equity_like_high_correlation_pairs` | **PASS** |
| `avg_pairwise_correlation` removed from `blocked_upstream_fields` | **PASS** |
| Scores unchanged (`heuristic_v1` weights) | **PASS** — evidence-only |
| Tests | **PASS** — **32 passed** (Block 2.2 + Block 2.4 + contract) |
| Golden fixture regen | **PASS** |

## Matrix rows closed (Session 04)

- D1 `top equity-like corr pairs` → `equity_like_high_correlation_pairs` evidence ✅
- D4 `top low/negative pairs` → `top3_lowest_correlation_pairs` / `lowest_pair_correlation` ✅
- D4 `average pairwise correlation` → Block 2.2 export + `avg_pairwise_correlation` evidence ✅
- D4 `lack of diversifying pairs` → `lack_of_diversifying_pairs` derived evidence ✅

## Next

Session 05 — see [Session 05 factor concentration](2026-05-29_block_2_4_session_05_factor_concentration.md) (**CLOSED**).
