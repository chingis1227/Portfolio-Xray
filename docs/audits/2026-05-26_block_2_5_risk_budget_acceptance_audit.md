# Block 2.5 Risk Budget View MVP — Acceptance Audit (Session 08)

Date: 2026-05-26

Purpose: Close [Block 2.5 Risk Budget View MVP ExecPlan](../exec_plans/2026-05-26_block_2_5_risk_budget_view_plan.md) **Session 08** and record whether the product-facing `block_2_5_risk_budget_view` contract is accepted on portfolio-first diagnosis and one-candidate runs.

Related:

- Canonical contract: [portfolio_xray_diagnostics_spec.md](../specs/portfolio_xray_diagnostics_spec.md) §2.5.1
- Decision: `DEC-2026-05-26-005`
- Implementation: `src/block_2_5_risk_budget_view.py`, `build_portfolio_xray_v2` in `src/portfolio_xray.py`
- Operator guide: [product_flow_operator_guide.md](../product_flow_operator_guide.md) (step 2 — `analysis_subject/portfolio_xray.json`)

---

## 1. Executive Summary

| Question | Verdict |
| --- | --- |
| Is `block_2_5_risk_budget_view` on live diagnosis path? | **Yes** — `run_portfolio_review.py --skip-candidates` refreshed `Main portfolio/analysis_subject/portfolio_xray.json` with populated Block 2.5 (`status` **ok**). |
| Is Block 2.5 present after one-candidate demo? | **Yes** — same subject artifact after `--candidates equal_weight`; product validator **PASS** (8 checks). |
| Does the product block exclude stress PnL fields? | **Yes** — no `worst_stress_*` keys on `assets[]` or block envelope (§5.2). |
| Does legacy `sections.risk_budget_view` remain? | **Yes** — legacy section present on full X-Ray build (§5.3). |
| Is the full ExecPlan accepted (Sessions 00–08)? | **Yes — 9/9** sessions complete (see §3). |

**Bottom line:** Block 2.5 Risk Budget View MVP is **complete**. Operators read capital vs variance-risk contribution from `block_2_5_risk_budget_view` on `analysis_subject/portfolio_xray.json`; legacy `sections.risk_budget_view` remains for formatters and golden contracts.

---

## 2. Session Rollup (00–08)

| Session | Objective | Status | Primary evidence |
| --- | --- | --- | --- |
| 00 | ExecPlan foundation + audit | **Done** | ExecPlan inventories, gap list |
| 01 | Product contract in spec | **Done** | §2.5.1; `DEC-2026-05-26-005` |
| 02 | Module scaffold + asset rows | **Done** | `src/block_2_5_risk_budget_view.py` |
| 03 | Portfolio aggregates | **Done** | top1/top3, overweight/underweight |
| 04 | Risk-budget bucket contribution | **Done** | taxonomy wire-time aggregation |
| 05 | Wire `build_portfolio_xray_v2` | **Done** | top-level `block_2_5_risk_budget_view` |
| 06 | Unit/contract tests + golden | **Done** | `tests/test_block_2_5_risk_budget.py`, golden v2 |
| 07 | Pipeline integration | **Done** | manifest, E2E gates, pipeline tests |
| 08 | Live demo + closure | **Done** | This document; live runs §5 |

---

## 3. ExecPlan Acceptance Criteria

| # | Criterion | Result | Evidence |
| --- | --- | --- | --- |
| 1 | `block_2_5_risk_budget_view` on diagnosis run | **PASS** | Live `--skip-candidates`; §5.1 |
| 2 | Block 2.5 on one-candidate run | **PASS** | Live `--candidates equal_weight`; subject X-Ray refreshed |
| 3 | Per-asset rows for all positive-weight holdings when RC exists | **PASS** | 8/8 tickers with weight %, RC %, gap pp |
| 4 | Portfolio summary fields present | **PASS** | top1, top3, top3 share, overweight/underweight, buckets |
| 5 | No stress PnL in product block | **PASS** | §5.2 |
| 6 | Legacy `sections.risk_budget_view` preserved | **PASS** | §5.3 |
| 7 | Product demo validator unchanged scope | **PASS** | `validate_one_candidate_demo.py` **PASS** (8 checks) |
| 8 | Pipeline / manifest disclosure | **PASS** | `product_risk_budget_key` on `output_manifest.json` |
| 9 | Closure pytest bundle | **PASS** | **44 passed** (Block 2.5 closure bundle) |

**Block 2.5 Risk Budget View MVP: ACCEPTED.**

---

## 4. Fixture-Locked Block 2.5 Behavior (golden / unit tests)

Source: `tests/fixtures/portfolio_xray_golden_v2.json`; `tests/test_block_2_5_risk_budget.py` (`assert_block_2_5_product_contract`).

| Check | Expected (golden fixture) |
| --- | --- |
| `block_id` | `2.5_risk_budget_view` |
| `top1_rc_asset.ticker` | SPY |
| Risk-overweight example | HYG **+15.0** pp gap |
| Stress fields on `assets[]` | **Absent** |
| `risk_budget_bucket_contribution` | Four buckets populated |

---

## 5. Live Verification (Session 08, root `config.yml`)

Commands (repository root, warm cache):

```bash
python run_portfolio_review.py --skip-candidates
python run_portfolio_review.py --candidates equal_weight
python scripts/validate_one_candidate_demo.py
python -m pytest tests/test_block_2_5_risk_budget.py tests/test_block_2_5_pipeline_integration.py tests/test_portfolio_xray_contract.py tests/test_product_bundle_paths.py tests/test_blocks_1_5_mvp_smoke.py -q
python scripts/verify_docs.py
```

| Check | Result |
| --- | --- |
| Diagnosis-only review | Exit **0**; `product_diagnosis_only`; `analysis_subject` materialized |
| One-candidate review | Exit **0**; `product_one_candidate`; factory `equal_weight` reused + compare |
| `validate_one_candidate_demo.py` | **PASS** (8 checks) |
| Closure pytest bundle | **44 passed** |

### 5.1 Live per-ticker Block 2.5 (`block_2_5_risk_budget_view.assets`)

Artifact: `Main portfolio/analysis_subject/portfolio_xray.json` (refreshed **2026-05-26**). Values are export-rounded (3 decimals) per metrics spec. RC source on this run: `snapshot_10y.json` (`metadata.rc_sources`).

| Ticker | Weight % | RC % | Gap (pp) |
| --- | ---: | ---: | ---: |
| SPY | 10.0 | 12.9 | +2.9 |
| QQQ | 13.0 | 19.3 | +6.3 |
| GLD | 9.0 | 8.1 | -0.9 |
| SLV | 9.0 | 18.5 | +9.5 |
| BND | 16.0 | 6.4 | -9.6 |
| SCHD | 17.0 | 19.5 | +2.5 |
| SCHP | 13.0 | 5.2 | -7.8 |
| TLT | 13.0 | 10.1 | -2.9 |

**Portfolio summary (same artifact):**

| Field | Observed |
| --- | --- |
| `status` | **ok** |
| `top1_rc_asset` | SCHD — weight **17.0%**, RC **19.5%**, gap **+2.5** pp |
| `top3_rc_share` | **57.3%** (SCHD, QQQ, SLV) |
| Largest risk-overweight | SLV **+9.5** pp; QQQ **+6.3** pp |
| Largest risk-underweight | BND **-9.6** pp; SCHP **-7.8** pp |
| Dominant risk bucket (RC) | **equity** — weight **40.0%**, RC **51.7%**, gap **+11.7** pp |
| Fixed income bucket | weight **29.0%**, RC **16.5%**, gap **-12.5** pp |

**Coexistence:** `block_2_1` through `block_2_4` present on the same artifact; Blocks 2.1–2.4 acceptance audits unchanged.

**Manifest:** `output_manifest.json` → `subject_diagnostics_contract.portfolio_xray_json.product_risk_budget_key` = `block_2_5_risk_budget_view`.

### 5.2 Stress boundary (product block)

| Check | Result |
| --- | --- |
| `worst_stress_loss_contribution_pct` on `assets[]` | **Absent** (all 8 tickers) |
| `worst_stress_scenario` on `assets[]` | **Absent** |
| Stress-named keys on block envelope | **Absent** |

### 5.3 Legacy section

| Check | Result |
| --- | --- |
| `sections.risk_budget_view` on subject X-Ray | **Present** (formatters / golden compatibility) |

---

## 6. Out of Scope / Deferred (documented)

| Item | Status |
| --- | --- |
| HTML/PDF Block 2.5 product view | Post-MVP; legacy formatters use `sections.risk_budget_view` |
| Problem Classification consuming Block 2.5 | Post-MVP (ExecPlan non-goal) |
| Prefer full `rc_vol_10y.csv` over snapshot top-N on lightweight materialize | Operational follow-up; live run used snapshot RC map with full 8-ticker coverage |

---

## 7. Operator Checklist

1. Run diagnosis: `python run_portfolio_review.py --skip-candidates`
2. Open `{output_dir_final}/analysis_subject/portfolio_xray.json` → `block_2_5_risk_budget_view`
3. For one-hypothesis demo: `python run_portfolio_review.py --candidates equal_weight` then `python scripts/validate_one_candidate_demo.py`
4. Compare capital weight % vs `risk_contribution_pct` and `weight_vs_risk_gap_pp` per holding; use `risk_budget_bucket_contribution` for bucket-level RC.

---

**Closure:** ExecPlan [2026-05-26_block_2_5_risk_budget_view_plan.md](../exec_plans/2026-05-26_block_2_5_risk_budget_view_plan.md) marked **Completed** 2026-05-26.
