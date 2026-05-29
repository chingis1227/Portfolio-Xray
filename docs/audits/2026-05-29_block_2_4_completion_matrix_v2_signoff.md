# Block 2.4 — Completion Matrix v2 Sign-Off (Session 13)

Date: 2026-05-29

Baseline matrix: [Session 00 §8](2026-05-29_block_2_4_session_00_baseline_audit.md#8-mandatory-completion-matrix--baseline-session-00)

Legend:

| Code | Meaning |
| --- | --- |
| **v2** | Implemented under `heuristic_v2` (evidence and/or score) |
| **DEF** | Deferred — listed in `diagnostics_meta.blocked_upstream_fields` and/or alert `limitations` |
| **XREF** | Wire-time cross-ref only (Block 3 stress or legacy PCA); scores unchanged |
| **N/A** | Not a separate product row by design |

Pytest lock: `tests/test_block_2_4_matrix_coverage.py` (**69** parametrized evidence rows + structural D12/D13/deferred tests).

---

## D1 — Equity → `hidden_equity_beta`

| Sub-dimension | Final | Session | Notes |
| --- | --- | --- | --- |
| equity allocation | **v2** | S02 | scored |
| risk_on exposure | **v2** | S02 | evidence |
| beta_portfolio | **v2** | S01+ | scored |
| downside_beta | **v2** | S01+ | scored |
| rolling benchmark correlation | **v2** | S01+ | scored |
| beta_eq | **v2** | S01+ | scored |
| beta_eq confidence | **v2** | S05–S06 | evidence |
| equity factor variance contribution | **v2** | S05 | evidence |
| equity-like non-equity assets | **v2** | S03 | `contributing_assets` |
| top equity-like corr pairs | **v2** | S04 | evidence |

## D2 — Rates / duration → `duration_concentration`

| Sub-dimension | Final | Session | Notes |
| --- | --- | --- | --- |
| fixed_income weight | **v2** | S01+ | scored |
| main_risk_factor rates/real_rates/duration | **v2** | S01+ | scored |
| beta_rr | **v2** | S01+ | scored |
| beta_inf | **v2** | S05 | evidence |
| duration_bucket | **DEF** | — | `blocked_upstream_fields.duration_bucket` |
| long/intermediate duration concentration | **DEF** | — | requires 2.1 duration buckets |
| rolling rates beta | **DEF** | — | `blocked_upstream_fields.rolling_rates_beta` |
| rates_shock / inflation_stagflation next_tests | **v2** | S01+ | next_tests |

## D3 — Credit / liquidity → `credit_liquidity_risk`

| Sub-dimension | Final | Session | Notes |
| --- | --- | --- | --- |
| beta_credit | **v2** | S01+ | scored |
| credit/liquidity main_risk_factor | **v2** | S01+ | scored |
| risk_role carry/risk_on/liquidity | **v2** | S01+ | scored |
| downside_beta | **v2** | S01+ | scored |
| subtype credit-sensitive weights | **DEF** | — | `blocked_upstream_fields.by_subtype` |
| credit_quality below IG | **DEF** | — | `blocked_upstream_fields.credit_quality` |
| credit-equity correlation per asset | **DEF** | — | overengineer registry entry |
| issuer/region concentration | **v2** | S02 | region via flags; issuer **DEF** |

## D4 — Correlation → `correlation_concentration`

| Sub-dimension | Final | Session | Notes |
| --- | --- | --- | --- |
| top high-correlation pairs | **v2** | S01+ | scored |
| top low/negative pairs | **v2** | S04 | evidence |
| average pairwise correlation | **v2** | S04 | evidence (2.2 export) |
| lack of diversifying pairs | **v2** | S04 | evidence |
| duplicate_group_id / canonical_ticker | **v2** | S01 | evidence |
| same main_risk_factor dominance | **v2** | S01+ | scored |
| PCA cluster concentration | **XREF** | S09 | legacy PCA evidence + limitations |
| rising/unstable correlation | **DEF** | — | `blocked_upstream_fields.rolling_correlation_instability` |

## D5 — Duplicate exposure

| Sub-dimension | Final | Session | Notes |
| --- | --- | --- | --- |
| combined_weight / combined_weight_pct | **v2** | S01 | bugfix |
| duplicate_exposure_flags | **v2** | S01 | evidence |
| same issuer/index/thematic | **DEF** | — | thematic/issuer registry |

## D6 — Currency / FX

| Sub-dimension | Final | Session | Notes |
| --- | --- | --- | --- |
| currency_exposure / dominant currency | **v2** | S02 | evidence |
| single_currency_dominance | **v2** | S02 | evidence |
| USD concentration | **v2** | S02 | evidence |
| investor_currency mismatch | **v2** | S02 | evidence |
| FX hidden behind non-local assets | **v2** | S05 | `beta_usd` on weak_hedge (evidence) |
| separate currency alert | **N/A** | — | six alerts sufficient |

## D7 — Factor concentration (distributed)

| Sub-dimension | Final | Session | Notes |
| --- | --- | --- | --- |
| factor_variance_contribution | **v2** | S05 | evidence |
| factor_risk_ranking / dominant factor | **v2** | S05 | evidence |
| all production betas | **v2** | S05 | evidence bundle |
| factor confidence all betas | **v2** | S05–S06 | confidence v2 |
| 5Y vs 10Y stability | **v2** | S05 | evidence |
| Kalman current beta | **v2** | S05 | evidence only |
| separate factor alert | **N/A** | — | distributed |

## D8 — Commodity / inflation

| Sub-dimension | Final | Session | Notes |
| --- | --- | --- | --- |
| beta_inf | **v2** | S05 | evidence |
| beta_cmd | **v2** | S05 | evidence |
| commodity shock (stress) | **XREF** | S08 | duration cross-ref evidence |
| inflation/stagflation next_tests | **v2** | S05+ | next_tests + cross-ref |
| commodity-sensitive assets | **v2** | S03 | contributors |
| inflation hedge role vs behavior | **v2** | S05–S08 | hedge + stress context |

## D9 — Weak hedge → `weak_hedge_behavior`

| Sub-dimension | Final | Session | Notes |
| --- | --- | --- | --- |
| hedge role weights | **v2** | S01+ | scored |
| downside_beta / rolling corr / eq\|credit beta | **v2** | S01+ | scored |
| offset factor betas (usd/cmd/vix/rr) | **v2** | S05 | evidence |
| stress helped/hurt / offset_coverage | **XREF** | S08 | wire-time enrichment |
| preliminary flag | **v2** | S01+ | data_quality_warnings |
| confirmation_status | **v2** | S08 | preliminary / confirmed |

## D10 — Tail / drawdown → `tail_risk`

| Sub-dimension | Final | Session | Notes |
| --- | --- | --- | --- |
| ES95/99, EEE10, skew, kurtosis | **v2** | S01+ | scored |
| downside_beta | **v2** | S01+ | scored |
| count DD >10/>20 | **v2** | S01+ | scored |
| VaR95/99, downside_deviation | **v2** | S07 | scored |
| max_drawdown, underwater, recovery, unrecovered | **v2** | S07 | scored |
| count DD >5 | **v2** | S07 | scored |

## D11 — Volatility instability

| Sub-dimension | Final | Session | Notes |
| --- | --- | --- | --- |
| vol_of_vol / rel_vol_of_vol | **v2** | S07 | evidence on tail_risk |
| rolling volatility latest | **v2** | S07 | evidence |
| Sharpe instability | **DEF** | — | limitation on tail_risk |
| separate alert | **N/A** | — | tail_risk evidence |

## D12 — Asset-level contributors

| Sub-dimension | Final | Session | Notes |
| --- | --- | --- | --- |
| by_asset + taxonomy → contributing_assets[] max 3 | **v2** | S03 | all alerts |
| no fake per-asset beta | **v2** | S03 | limitations |

## D13 — Data quality and confidence

| Sub-dimension | Final | Session | Notes |
| --- | --- | --- | --- |
| missing blocks/signals | **v2** | S01+ | unavailable handling |
| limitations / confidence_reason | **v2** | S01+ | mandatory |
| confidence v2 | **v2** | S06 | `confidence_model=v2` |
| preliminary vs confirmed | **v2** | S08 | confirmation_status |
| propagate 2.2 history warnings | **v2** | S06 | confidence penalties |

---

## Rollup (Session 13)

| Category | Count (approx.) |
| --- | ---: |
| **v2** implemented | ~72 |
| **DEF** documented (registry + limitations) | 9 registry fields |
| **XREF** wire-time only | 3 (PCA cluster, commodity shock, hedge offset) |
| **N/A** by design | 3 |

**Matrix sign-off: PASS** — all Session 00 sub-rows have a final code; implementable rows locked by pytest.
