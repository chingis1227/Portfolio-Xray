# Block 2.4 Hidden Exposure — Session 00 Baseline Audit

Date: 2026-05-29

Purpose: Establish the institutional-upgrade baseline for `block_2_4_hidden_exposure` before Session 01. Read-only audit: inventory files, verify JSON contract, confirm tests, reproduce known bugs, and sign the §10 completion matrix at **v1 baseline** (what exists today vs planned v2).

Related:

- Product contract: [portfolio_xray_diagnostics_spec.md](../specs/portfolio_xray_diagnostics_spec.md) §2.4.1
- v1 closure: [2026-05-26_block_2_4_hidden_exposure_plan.md](../exec_plans/2026-05-26_block_2_4_hidden_exposure_plan.md) (**Completed**)
- Institutional upgrade roadmap: Cursor plan `block_2.4_institutional_upgrade` (Sessions 01–13)
- Implementation: `src/block_2_4_hidden_exposure.py` → `build_block_2_4_hidden_exposure`, wired in `src/portfolio_xray.py`

---

## 1. Executive Summary

| Question | Verdict |
| --- | --- |
| Is Block 2.4 implemented as Core MVP product block... | **Yes** — `block_2_4_hidden_exposure` on `portfolio_xray.json`; 6 alerts; `heuristic_v1`. |
| Does it read only Blocks 2.1–2.3... | **Yes** — module docstring + `diagnostics_meta.does_not_run_stress_lab: true`. |
| Is legacy `sections.hidden_risk_detector` preserved... | **Yes** — parallel 11-category legacy section in `portfolio_xray.py`. |
| Are focused tests green... | **Yes** — **13 passed** (`test_block_2_4_hidden_exposure.py` + contract subset). |
| Critical schema bug... | **Yes — confirmed** — duplicate exposure reads wrong keys; `combined_weight=0.18` → score `0.0`. |
| Institutional v2 complete... | **No** — ~35% matrix rows at v1; Session 01+ required. |

**Bottom line:** Block 2.4 v1 scaffold is sound and test-covered, but **not institutional-grade**. Session 00 closes with a signed baseline matrix; **Session 01** starts with duplicate bugfix + contract fields.

---

## 2. Files Inventoried

| Role | Path |
| --- | --- |
| Implementation | `src/block_2_4_hidden_exposure.py` |
| Wiring | `src/portfolio_xray.py` (`build_portfolio_xray_v2`, legacy `_hidden_risk_section`) |
| Upstream inputs | `src/block_2_1_asset_allocation.py`, `src/block_2_2_portfolio_metrics.py`, `src/block_2_3_factor_exposure.py` |
| Downstream consumer | `src/block_2_6_portfolio_weakness_map.py` (5 alert scores; excludes `weak_hedge_behavior`) |
| Product bundle | `src/product_bundle_paths.py` (`PORTFOLIO_XRAY_BLOCK_2_4_KEY`) |
| Spec | `docs/specs/portfolio_xray_diagnostics_spec.md` §2.4.1 |
| v1 ExecPlan | `docs/exec_plans/2026-05-26_block_2_4_hidden_exposure_plan.md` |
| Tests | `tests/test_block_2_4_hidden_exposure.py` (6 tests) |
| Contract | `tests/test_portfolio_xray_contract.py`, `tests/test_core_mvp_blocks_1_3_boundaries.py`, `scripts/core_mvp_validation_contract.py`, `scripts/validate_core_mvp_block2_fixture_matrix.py` |
| Golden | `tests/fixtures/portfolio_xray_golden_v2.json` |
| E2E gates | `src/live_core_e2e.py`, `src/live_full_e2e.py` |

No separate `hidden_exposure.json` in the six-file product bundle (correct per spec).

---

## 3. Current JSON Contract (verified)

### Top-level `block_2_4_hidden_exposure`

| Field | Present v1 | Notes |
| --- | --- | --- |
| `block` | Yes | `"2.4_hidden_exposure"` |
| `block_id`, `block_name` | Yes | |
| `status` | Yes | `ok` / `partial` / `unavailable` |
| `summary` | Yes | |
| `alerts` | Yes | exactly 6 keys |
| `top_hidden_risks` | Yes | top 3 by score |
| `data_quality_warnings` | Yes | missing input blocks |
| `diagnostics_meta` | Yes | `ruleset=heuristic_v1`, signal_weights, boundary flags |
| `limitations` | **No** | planned Session 01 (per alert) |
| `contributing_assets` | **No** | planned Session 03 |
| `blocked_upstream_fields` | **No** | planned Session 04b |
| `confidence_reason` | **No** | planned Session 01/06 |

### Per-alert (all 6)

| Field | Present v1 |
| --- | --- |
| `status`, `score`, `evidence`, `explanation`, `why_it_matters`, `next_tests` | Yes |
| `confidence`, `data_quality_warnings`, `insufficient_evidence_reasons`, `calculation_notes` | Yes |
| `limitations`, `confidence_reason`, `contributing_assets`, `confirmation_status` | **No** |

### Alert IDs and v1 signal counts

| alert_id | Score signals | Extra evidence only |
| --- | --- | --- |
| `hidden_equity_beta` | 4 | `beta_eq_confidence` |
| `duration_concentration` | 3 | duration_bucket warning in calculation_notes |
| `credit_liquidity_risk` | 4 | — |
| `correlation_concentration` | 3 | — |
| `weak_hedge_behavior` | 4 | `preliminary_without_stress_lab` warning |
| `tail_risk` | 8 | — |

Golden fixture excerpt: `tests/fixtures/portfolio_xray_golden_v2.json` L888+; all six alerts populated; `ruleset=heuristic_v1`.

---

## 4. Baseline Tests

```text
pytest tests/test_block_2_4_hidden_exposure.py tests/test_portfolio_xray_contract.py -q
13 passed in 20.31s
```

Existing Block 2.4 tests cover: contract shape, evidence schema, missing-data Unavailable, status boundaries (hidden_equity_beta), weak_hedge preliminary flag, input immutability, X-Ray integration.

**Gap:** no test for duplicate `combined_weight` bug; no per-dimension matrix tests; contract tests only check block presence/status fingerprint.

---

## 5. Critical Bug — Duplicate Exposure Schema Mismatch

**Block 2.1 exports** (`src/block_2_1_asset_allocation.py`):

```python
"combined_weight": round(combined, REPORT_DECIMALS),
"combined_weight_pct": pct,
```

**Block 2.4 reads** (`src/block_2_4_hidden_exposure.py` L206):

```python
for key in ("observed", "group_weight", "weight", "duplicate_weight"):
```

**Reproduction (Session 00):**

```python
b21 = {"duplicate_exposure_flags": [{"combined_weight": 0.18, ...}]}
→ duplicate_exposure_weight evidence value = 0.0  # BUG
```

**Impact:** `correlation_concentration.duplicate_exposure_weight` stuck at 0.0 whenever flags exist but use Block 2.1 field names. Golden has empty `duplicate_exposure_flags` so bug is masked in fixture.

**Fix owner:** Session 01 — read `combined_weight` / `combined_weight_pct` first.

---

## 6. Upstream Surface Available but Not Consumed by Block 2.4 v1

### Block 2.1 (not read by 2.4 v1)

- `concentration_flags[]` (top1/top3, asset class, main risk factor, region, **currency**)
- `capital_allocation_breakdown.by_asset`, `by_region`, `by_currency`
- `duplicate_exposure_flags` detail: `duplicate_group_id`, `tickers`, `canonical_ticker`, `severity`, `message`
- **Not in product surface:** `duration_bucket`, `credit_quality`, `subtype`, `sector`, `issuer`, `thematic_*`

### Block 2.2 (not read by 2.4 v1)

- `drawdown_diagnostics`: `pct_time_underwater`, `longest_underwater`, `max_drawdown`, `recovered`, `count_drawdowns_gt_5`, `recovery_months`
- `tail_risk_diagnostics`: `var_95`, `var_99`, `downside_deviation`
- `benchmark_dependence.upside_beta`
- `correlation_breakdown.top3_lowest_correlation_pairs`
- **Not exported:** `avg_pairwise_correlation` (matrix loaded internally; field absent)
- `metadata.vol_of_vol`, `metadata.rel_vol_of_vol`
- `rolling_diagnostics` panels beyond `latest_correlation`

### Block 2.3 (not read by 2.4 v1)

- `factor_variance_contribution`, `factor_risk_ranking`, `factor_exposure_summary`
- `factor_beta_stability`, `kalman_current_beta`, `factor_kalman_uncertainty`
- Betas: `beta_inf`, `beta_usd`, `beta_cmd`, `beta_vix`, `beta_us_growth`
- Factor confidence for all betas except `beta_eq` extra evidence row

---

## 7. Stress Lab Boundary (verified)

| Component | Reads stress... | Role |
| --- | --- | --- |
| `block_2_4_hidden_exposure` core | **No** | Pre-stress hypotheses from 2.1–2.3 |
| `sections.hidden_risk_detector` | **Yes** | Legacy 11 categories, PCA, stress PnL |
| `hedge_gap_analysis_v1` (Block 3.3) | **Yes** | Hedge confirmation: helped/hurt, offset_coverage_ratio |
| `block_2_6_portfolio_weakness_map` | **No** | Uses 2.4 integer scores only |

Weak hedge v1: always `preliminary_without_stress_lab`; never claims hedge failure.

---

## 8. Mandatory Completion Matrix — Baseline (Session 00)

Legend: **v1** = implemented today | **v2** = scheduled Sessions 01–13 | **DEF** = deferred with documented reason

### D1 — Equity hidden risk → `hidden_equity_beta`

| Sub-dimension | Placement | v1 | Target session | Deferred reason |
| --- | --- | --- | --- | --- |
| equity allocation | score | — | S02 | — |
| risk_on exposure | sub-signal | — | S02 | — |
| beta_portfolio | score | v1 | — | — |
| downside_beta | score | v1 | — | — |
| rolling benchmark correlation | score | v1 | — | — |
| beta_eq | score | v1 | — | — |
| beta_eq confidence | evidence/confidence | partial | S05–S06 | not in score/confidence v1 |
| equity factor variance contribution | sub-signal | — | S05 | — |
| equity-like non-equity assets | contributing_assets | — | S03 | — |
| top equity-like corr pairs | evidence | — | S04 | — |

### D2 — Rates / duration → `duration_concentration`

| Sub-dimension | v1 | Target | Deferred reason |
| --- | --- | --- | --- |
| fixed_income weight | v1 | — | — |
| main_risk_factor rates/real_rates/duration | v1 | — | — |
| beta_rr | v1 | — | — |
| beta_inf | — | S05 | — |
| duration_bucket | DEF | S04b | **Requires Block 2.1** `by_duration_bucket` |
| long/intermediate duration concentration | DEF | S04b | **Requires Block 2.1** |
| rolling rates beta | DEF | S04b | **Requires Block 2.2/2.3** export |
| rates_shock / inflation_stagflation next_tests | v1 | — | — |

### D3 — Credit / liquidity → `credit_liquidity_risk`

| Sub-dimension | v1 | Target | Deferred reason |
| --- | --- | --- | --- |
| beta_credit | v1 | — | — |
| credit/liquidity main_risk_factor | v1 | — | — |
| risk_role carry/risk_on/liquidity | v1 | — | — |
| downside_beta | v1 | — | — |
| subtype credit-sensitive weights | DEF | S04b | **Requires Block 2.1** `by_subtype` |
| credit_quality below IG | DEF | S04b | **Requires Block 2.1** `by_credit_quality` |
| credit-equity correlation per asset | DEF | S04b | **Overengineer Core MVP** / Asset X-Ray |
| issuer/region concentration | partial | S02 | region via flags; **issuer N/A** — not aggregated in 2.1 |

### D4 — Correlation → `correlation_concentration`

| Sub-dimension | v1 | Target | Deferred reason |
| --- | --- | --- | --- |
| top high-correlation pairs | v1 | — | — |
| top low/negative pairs | — | S04 | — |
| average pairwise correlation | — | S04 | **Requires Block 2.2 add** |
| lack of diversifying pairs | — | S04 | derived after above |
| duplicate_group_id / canonical_ticker | — | S01 | — |
| same main_risk_factor dominance | v1 | — | — |
| PCA cluster concentration | DEF | S09 cross-ref | **Legacy / Block 3** — not in product 2.1–2.3 |
| rising/unstable correlation | DEF | S04b | **Requires Block 2.2** instability summary |

### D5 — Duplicate exposure → sub-signal `correlation_concentration`

| Sub-dimension | v1 | Target | Deferred reason |
| --- | --- | --- | --- |
| combined_weight / combined_weight_pct | **BUG** | S01 | reads wrong keys |
| duplicate_exposure_flags | broken | S01 | — |
| same issuer/index/thematic | DEF | S04b | **Requires Block 2.1** aggregation |

### D6 — Currency / FX

| Sub-dimension | v1 | Target | Deferred reason |
| --- | --- | --- | --- |
| currency_exposure / dominant currency | — | S02 | — |
| single_currency_dominance | — | S02 | via concentration_flags |
| USD concentration | — | S02 | via by_currency |
| investor_currency mismatch | — | S02 | 2.2 investor_currency vs 2.1 dominant |
| FX hidden behind non-local assets | DEF | S05 | **Overengineer** — beta_usd evidence in weak_hedge |
| separate currency alert | N/A | — | 6 alerts sufficient |

### D7 — Factor concentration (distributed)

| Sub-dimension | v1 | Target | Deferred reason |
| --- | --- | --- | --- |
| factor_variance_contribution | — | S05 | — |
| factor_risk_ranking / dominant factor | — | S05 | — |
| all production betas | partial | S05 | only eq/rr/credit in v1 |
| factor confidence all betas | partial | S05–S06 | eq evidence only |
| 5Y vs 10Y stability | — | S05 | — |
| Kalman current beta | — | S05 | evidence only |
| separate factor alert | N/A | — | distributed sub-signals |

### D8 — Commodity / inflation

| Sub-dimension | v1 | Target | Deferred reason |
| --- | --- | --- | --- |
| beta_inf | — | S05 | — |
| beta_cmd | — | S05 | — |
| commodity shock (stress) | DEF | S08 cross-ref | **Block 3** |
| inflation/stagflation next_tests | v1 partial | S05 | duration only in v1 |
| commodity-sensitive assets | — | S03/S04b | taxonomy contributors |
| inflation hedge role vs behavior | partial | S05–S08 | hedge weight v1; stress S08 |

### D9 — Weak hedge → `weak_hedge_behavior`

| Sub-dimension | v1 | Target | Deferred reason |
| --- | --- | --- | --- |
| hedge role weights | v1 | — | — |
| downside_beta / rolling corr / eq|credit beta | v1 | — | — |
| offset factor betas (usd/cmd/vix/rr) | — | S05 | — |
| stress helped/hurt / offset_coverage | DEF | S08 | **Block 3 summary** wire-time only |
| preliminary flag | v1 | — | — |
| confirmation_status | — | S08 | — |

### D10 — Tail / drawdown → `tail_risk`

| Sub-dimension | v1 | Target | Deferred reason |
| --- | --- | --- | --- |
| ES95/99, EEE10, skew, kurtosis | v1 | — | — |
| downside_beta | v1 | — | — |
| count DD >10/>20 | v1 | — | — |
| VaR95/99, downside_deviation | — | S07 | in 2.2, not wired |
| max_drawdown, underwater, recovery, unrecovered | — | S07 | in 2.2, not wired |
| count DD >5 | — | S07 | in 2.2, not wired |

### D11 — Volatility instability

| Sub-dimension | v1 | Target | Deferred reason |
| --- | --- | --- | --- |
| vol_of_vol / rel_vol_of_vol | — | S07 | in 2.2 metadata |
| rolling volatility latest | — | S07 | 2.2 panel |
| Sharpe instability | DEF | S04b | **Requires Block 2.2** export |
| separate alert | N/A | — | tail_risk evidence |

### D12 — Asset-level contributors

| Sub-dimension | v1 | Target |
| --- | --- | --- |
| by_asset + taxonomy → contributing_assets[] max 3 | — | S03 |
| no fake per-asset beta | — | S03 limitations |

### D13 — Data quality and confidence

| Sub-dimension | v1 | Target |
| --- | --- | --- |
| missing blocks/signals | v1 | — |
| limitations / confidence_reason | — | S01/S06 |
| confidence v2 (factor, agreement, conflict) | — | S06 |
| preliminary vs confirmed | partial | S08 |
| propagate 2.2 history warnings | — | S06 |

---

## 9. Matrix Rollup (Session 00)

| Status | Sub-rows (approx.) |
| --- | --- |
| v1 implemented | ~38 |
| v1 partial / bug | ~8 |
| Scheduled v2 (Sessions 01–08) | ~52 |
| Deferred upstream (documented) | ~12 |
| Deferred Block 3 / legacy cross-ref | ~4 |
| Deferred overengineer / N/A | ~6 |

**No dimension omitted.** Every sub-row above has placement + status + owner session or defer reason.

---

## 10. Session 00 Acceptance

| Criterion | Result |
| --- | --- |
| All Block 2.4 files inventoried | **PASS** |
| JSON contract documented | **PASS** |
| Baseline tests run | **PASS** — 13 passed |
| Duplicate bug reproduced | **PASS** |
| §10 matrix signed at baseline | **PASS** |
| Code changes | **None** (audit only) |

**Session 00: CLOSED.**

**Next:** Session 01 — Contract stabilization + duplicate bugfix (`combined_weight` / `combined_weight_pct`, `limitations[]`, `confidence_reason`, `blocked_upstream_fields` scaffold).

---

## 11. V2 closure (Session 13)

Institutional upgrade closed 2026-05-29. Final matrix sign-off: [completion matrix v2](2026-05-29_block_2_4_completion_matrix_v2_signoff.md). Program closure: [Session 13 institutional closure](2026-05-29_block_2_4_session_13_institutional_closure.md); ExecPlan: [institutional upgrade plan](../exec_plans/2026-05-29_block_2_4_institutional_upgrade_plan.md) (**Completed**).
