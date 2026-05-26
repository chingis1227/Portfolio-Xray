# Block 2.6 Portfolio Weakness Map MVP — Acceptance Audit (Session 08)

Date: 2026-05-26

Purpose: Close [Block 2.6 Portfolio Weakness Map MVP ExecPlan](../exec_plans/2026-05-26_block_2_6_portfolio_weakness_map_plan.md) **Session 08** and record whether the product-facing `block_2_6_portfolio_weakness_map` contract is accepted on portfolio-first diagnosis and one-candidate runs.

Related:

- Canonical contract: [portfolio_xray_diagnostics_spec.md](../specs/portfolio_xray_diagnostics_spec.md) §2.6.1
- Decision: `DEC-2026-05-26-006`
- Implementation: `src/block_2_6_portfolio_weakness_map.py`, `build_portfolio_xray_v2` in `src/portfolio_xray.py`
- Operator guide: [product_flow_operator_guide.md](../product_flow_operator_guide.md) (step 2 — `analysis_subject/portfolio_xray.json`)

---

## 1. Executive Summary

| Question | Verdict |
| --- | --- |
| Is `block_2_6_portfolio_weakness_map` on live diagnosis path? | **Yes** — `run_portfolio_review.py --skip-candidates` refreshed `Main portfolio/analysis_subject/portfolio_xray.json` with Block 2.6 (`status` **partial**, nine risk rows). |
| Is Block 2.6 present after one-candidate demo? | **Yes** — subject X-Ray refreshed after `--candidates equal_weight`; product validator **PASS** (8 checks). |
| Does the product block exclude Stress Lab PnL fields? | **Yes** — no `stress_report`, `scenario_results`, `pnl_by_asset_pct`, or `worst_stress` keys in the block envelope (§5.2). |
| Are nine MVP risk types emitted? | **Yes** — eight scored + `usd_shock` **Unavailable** (insufficient evidence; contract-allowed). |
| Does legacy `sections.weakness_map` remain? | **Yes** — legacy section present on full X-Ray build (§5.3). |
| Is the full ExecPlan accepted (Sessions 00–08)? | **Yes — 9/9** sessions complete (see §3). |

**Bottom line:** Block 2.6 Portfolio Weakness Map MVP is **complete**. Operators read pre-stress vulnerability hypotheses and `next_tests` from `block_2_6_portfolio_weakness_map` on `analysis_subject/portfolio_xray.json`; Stress Lab continues to own scenario losses and pass/fail.

---

## 2. Session Rollup (00–08)

| Session | Objective | Status | Primary evidence |
| --- | --- | --- | --- |
| 00 | ExecPlan foundation + stress boundary | **Done** | ExecPlan, `DEC-2026-05-26-006` |
| 01 | Product contract in spec | **Done** | §2.6.1; Core MVP 2.1–2.6 docs |
| 02 | Module scaffold | **Done** | `src/block_2_6_portfolio_weakness_map.py` |
| 03 | Metric extraction from Blocks 2.1–2.5 | **Done** | adapter helpers in module |
| 04 | Rule tables + scoring engine | **Done** | `RISK_RULE_TABLES`, `heuristic_v1` |
| 05 | Wire `build_portfolio_xray_v2` | **Done** | top-level `block_2_6_portfolio_weakness_map` |
| 06 | Unit/contract tests + golden | **Done** | `tests/test_block_2_6_portfolio_weakness_map.py`, golden v2 |
| 07 | Pipeline integration | **Done** | `product_bundle_paths`, `live_full_e2e`, MVP smoke |
| 08 | Live demo + closure | **Done** | This document; live runs §5 |

---

## 3. ExecPlan Acceptance Criteria

| # | Criterion | Result | Evidence |
| --- | --- | --- | --- |
| 1 | `block_2_6_portfolio_weakness_map` on diagnosis run | **PASS** | Live `--skip-candidates`; §5.1 |
| 2 | Block 2.6 on one-candidate run | **PASS** | Live `--candidates equal_weight`; subject X-Ray refreshed |
| 3 | Nine MVP risk types with score/severity/evidence/`next_tests` | **PASS** | §5.1 (8 scored + 1 unavailable) |
| 4 | No stress PnL or attribution in product block | **PASS** | §5.2 |
| 5 | Inputs limited to Blocks 2.1–2.5 metadata | **PASS** | `metadata.inputs` = block_2_1 … block_2_5 |
| 6 | Legacy `sections.weakness_map` preserved | **PASS** | §5.3 |
| 7 | Product demo validator unchanged scope | **PASS** | `validate_one_candidate_demo.py` **PASS** (8 checks) |
| 8 | Pipeline / manifest disclosure | **PASS** | `product_weakness_map_key` on `output_manifest.json` |
| 9 | Closure pytest bundle | **PASS** | **35 passed** (Block 2.6 closure bundle) |

**Block 2.6 Portfolio Weakness Map MVP: ACCEPTED.**

---

## 4. Fixture-Locked Block 2.6 Behavior (golden / unit tests)

Source: `tests/fixtures/portfolio_xray_golden_v2.json`; `tests/test_block_2_6_portfolio_weakness_map.py`.

| Check | Expected (golden fixture) |
| --- | --- |
| `block_id` | `2.6_portfolio_weakness_map` |
| Risk type count | **9** |
| `metadata.rule_version` | `heuristic_v1` |
| `metadata.stress_lab_separation` | `no_stress_pnl_or_attribution` |
| Stress keys in block JSON | **Absent** |

---

## 5. Live Verification (Session 08, root `config.yml`)

Commands (repository root, warm cache):

```bash
python run_portfolio_review.py --skip-candidates
python run_portfolio_review.py --candidates equal_weight
python scripts/validate_one_candidate_demo.py
python -m pytest tests/test_block_2_6_portfolio_weakness_map.py tests/test_portfolio_xray_contract.py tests/test_product_bundle_paths.py tests/test_blocks_1_5_mvp_smoke.py -q
python scripts/verify_docs.py
```

| Check | Result |
| --- | --- |
| Diagnosis-only review | Exit **0**; `product_diagnosis_only`; `analysis_subject` materialized |
| One-candidate review | Exit **0**; `product_one_candidate`; factory `equal_weight` reused + compare |
| `validate_one_candidate_demo.py` | **PASS** (8 checks) |
| Closure pytest bundle | **35 passed** |
| `verify_docs.py` | **OK** |

### 5.1 Live nine risk types (`block_2_6_portfolio_weakness_map.risk_types`)

Artifact: `Main portfolio/analysis_subject/portfolio_xray.json` (refreshed **2026-05-26**).

| Risk type | Score (0–100) | Severity | Confidence | Sample `next_tests` |
| --- | ---: | --- | --- | --- |
| `equity_crash` | 36 | Low | high | equity_shock, recession_severe |
| `rates_up` | 65 | Medium | high | rates_shock, inflation_stagflation |
| `inflation_shock` | 41 | Medium | medium | inflation_stagflation, commodity_shock |
| `credit_spreads` | 5 | Low | high | credit_shock, liquidity_shock |
| `liquidity_shock` | 20 | Low | medium | liquidity_shock, credit_shock |
| `usd_shock` | — | Unavailable | unavailable | usd_shock |
| `commodity_shock` | 28 | Low | high | commodity_shock, inflation_stagflation |
| `volatility_spike` | 32 | Low | medium | volatility_spike, liquidity_shock |
| `recession` | 12 | Low | medium | recession_severe, credit_shock |

**Block envelope (same artifact):**

| Field | Observed |
| --- | --- |
| `status` | **partial** (some signals missing; map still evaluable) |
| `metadata.rule_version` | **heuristic_v1** |
| `metadata.forbidden_stress_keys_detected` | **[]** |
| `metadata.inputs` | block_2_1, block_2_2, block_2_3, block_2_4, block_2_5 |

**Coexistence:** `block_2_1` through `block_2_5` present on the same artifact.

**Manifest:** `output_manifest.json` → `subject_diagnostics_contract.portfolio_xray_json.product_weakness_map_key` = `block_2_6_portfolio_weakness_map`.

### 5.2 Stress boundary (product block)

| Check | Result |
| --- | --- |
| `stress_report` in block JSON | **Absent** |
| `scenario_results` in block JSON | **Absent** |
| `pnl_by_asset_pct` in block JSON | **Absent** |
| `worst_stress_*` in block JSON | **Absent** |
| `failed_scenario` / `failed_test` in block JSON | **Absent** |

### 5.3 Legacy section

| Check | Result |
| --- | --- |
| `sections.weakness_map` on subject X-Ray | **Present** (formatters / Problem Classification compatibility) |

---

## 6. Out of Scope / Deferred (documented)

| Item | Status |
| --- | --- |
| HTML/PDF Block 2.6 product view | Post-MVP; legacy formatters may use `sections.weakness_map` |
| Problem Classification consuming Block 2.6 | Post-MVP (ExecPlan non-goal) |
| `usd_shock` unavailable on live 8-ticker book | Accepted when USD-factor evidence below minimum evaluable weight; re-check if factor panel expands |
| `crypto_shock` in product Block 2.6 | Out of MVP scope per `DEC-2026-05-26-006` (legacy/advanced only) |

---

## 7. Operator Checklist

1. Run diagnosis: `python run_portfolio_review.py --skip-candidates`
2. Open `{output_dir_final}/analysis_subject/portfolio_xray.json` → `block_2_6_portfolio_weakness_map`
3. For one-hypothesis demo: `python run_portfolio_review.py --candidates equal_weight` then `python scripts/validate_one_candidate_demo.py`
4. Use `risk_types[].next_tests` as Stress Lab scenario hints; read losses only from `stress_report.json`, not from Block 2.6.

---

**Closure:** ExecPlan [2026-05-26_block_2_6_portfolio_weakness_map_plan.md](../exec_plans/2026-05-26_block_2_6_portfolio_weakness_map_plan.md) marked **Completed** 2026-05-26.
