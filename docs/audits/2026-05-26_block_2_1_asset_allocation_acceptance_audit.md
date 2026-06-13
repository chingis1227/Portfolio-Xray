# Block 2.1 Asset Allocation MVP — Acceptance Audit (Session 08)

Date: 2026-05-26

Purpose: Close [Block 2.1 Asset Allocation MVP ExecPlan](../exec_plans/2026-05-26_block_2_1_asset_allocation_plan.md) **Session 08** and record whether the product-facing `block_2_1_asset_allocation` contract is accepted on portfolio-first diagnosis and one-candidate runs.

Related:

- Canonical contract: [portfolio_xray_diagnostics_spec.md](../specs/portfolio_xray_diagnostics_spec.md) §2.1.1–§2.1.2
- Decision: `DEC-2026-05-26-002`
- Implementation: `src/block_2_1_asset_allocation.py`, `build_portfolio_xray_v2` in `src/portfolio_xray.py`
- Real-cash regression fixture: `tests/fixtures/mvp_portfolios/demo_usd_asset_allocation_with_cash_5pct.yml`
- Operator guide: [product_flow_operator_guide.md](../product_flow_operator_guide.md) (step 2 — `analysis_subject/portfolio_xray.json`)

---

## 1. Executive Summary

| Question | Verdict |
| --- | --- |
| Is `block_2_1_asset_allocation` on live diagnosis path... | **Yes** — `run_portfolio_review.py --skip-candidates` refreshed `Main portfolio/analysis_subject/portfolio_xray.json` with populated Block 2.1. |
| Is Block 2.1 present after one-candidate demo... | **Yes** — same subject artifact after `--candidates equal_weight`; product validator **PASS** (8 checks). |
| Does real-cash fixture match §2.1.1 golden numbers... | **Yes** — offline pytest (fixture ×0.95 + 5% `Cash USD`); see §4. |
| Is the full ExecPlan accepted (Sessions 01–08)... | **Yes — 8/8** sessions complete (see §3). |

**Bottom line:** Block 2.1 Asset Allocation MVP is **complete**. Operators read capital structure from `block_2_1_asset_allocation` on `analysis_subject/portfolio_xray.json`; legacy `sections.asset_allocation` remains for formatters and golden contracts.

---

## 2. Session Rollup (01–08)

| Session | Objective | Status | Primary evidence |
| --- | --- | --- | --- |
| 01 | Audit & inventory | **Done** | ExecPlan inventories, gap list G1–G11 |
| 02 | Product contract in spec | **Done** | §2.1.1–§2.1.2; `DEC-2026-05-26-002` |
| 03 | Builder module | **Done** | `src/block_2_1_asset_allocation.py` |
| 04 | Input Layer weights / real cash | **Done** | `resolved_analysis_weights`; legacy `cash_weight` |
| 05 | 5% cash demo fixture | **Done** | `demo_usd_asset_allocation_with_cash_5pct.yml` |
| 06 | Unit/contract tests | **Done** | `tests/test_block_2_1_asset_allocation.py` |
| 07 | Pipeline integration | **Done** | materialize path, manifest, live E2E gates |
| 08 | Live demo + closure | **Done** | This document; live runs §5 |

---

## 3. ExecPlan Acceptance Criteria

| # | Criterion | Result | Evidence |
| --- | --- | --- | --- |
| 1 | `block_2_1_asset_allocation` on diagnosis run | **PASS** | Live `--skip-candidates`; §5.1 |
| 2 | Block 2.1 on one-candidate run | **PASS** | Live `--candidates equal_weight`; subject X-Ray refreshed |
| 3 | Product demo validator unchanged scope | **PASS** | `validate_one_candidate_demo.py` **PASS** (8 checks) |
| 4 | Real-cash fixture exact numbers | **PASS** | §4 (pytest-locked) |
| 5 | Threshold registry drift guard | **PASS** | `tests/test_block_2_1_threshold_registry.py` |
| 6 | Pipeline / manifest disclosure | **PASS** | `subject_diagnostics_contract` on `output_manifest.json` |
| 7 | Documentation matches implementation | **PASS** | `python scripts/verify_docs.py` **OK** |
| 8 | Closure pytest bundle | **PASS** | **44 passed** (Session 08 bundle) |

**Block 2.1 Asset Allocation MVP: ACCEPTED.**

---

## 4. Fixture-Locked Block 2.1 Numbers (`demo_usd_asset_allocation_with_cash_5pct.yml`)

Source: `tests/test_block_2_1_asset_allocation.py` (Session 06). Weights = root `config.yml` tickers × **0.95** + **`Cash USD: 0.05`**.

| Field | Expected (export `weight_pct`) |
| --- | ---: |
| `total_holdings` | 9 |
| `top1_holding` | SCHD **16.15** |
| `top3_holdings` | SCHD 16.15, BND 15.2, QQQ 12.35 |
| `top3_weight_pct` | **43.7** |
| `dominant_asset_class` | fixed_income **39.9** |
| `by_asset` Cash USD | **5.0** |
| `by_asset_class` cash | **5.0** |
| `legacy_summary.cash_weight` (fraction) | **0.05** |
| `metadata.cash_treatment` | `real_cash_position_if_present` |

**Concentration flags (fixture):** `single_region_dominance` medium; `single_currency_dominance` medium + high; `duplicate_exposure_flags` empty.

**Economic summary (fixture):** headline mentions `fixed_income`; key points reference SCHD and bank cash.

---

## 5. Live Verification (Session 08, root `config.yml`, no real cash)

Commands (repository root, warm cache):

```bash
python run_portfolio_review.py --skip-candidates
python run_portfolio_review.py --candidates equal_weight
python scripts/validate_one_candidate_demo.py
python -m pytest tests/test_block_2_1_asset_allocation.py tests/test_block_2_1_threshold_registry.py tests/test_block_2_1_pipeline_integration.py tests/test_portfolio_xray_contract.py tests/test_product_bundle_paths.py tests/test_blocks_1_5_mvp_smoke.py -q
python scripts/verify_docs.py
```

| Check | Result |
| --- | --- |
| Diagnosis-only review | Exit **0**; `product_diagnosis_only`; `analysis_subject` materialized |
| One-candidate review | Exit **0**; `product_one_candidate`; factory `equal_weight` + compare |
| `validate_one_candidate_demo.py` | **PASS** (8 checks) |
| Closure pytest bundle | **44 passed** |
| Docs verification | **OK** |

### 5.1 Live `block_2_1_asset_allocation` snapshot (demo `config.yml`, 8 market tickers)

Artifact: `Main portfolio/analysis_subject/portfolio_xray.json` (refreshed **2026-05-26** diagnosis materialize).

| Field | Observed |
| --- | ---: |
| `block` | `2.1_asset_allocation` |
| `total_holdings` | 8 |
| `top1_holding` | SCHD **17.0** |
| `top3_holdings` | SCHD 17.0, BND 16.0, QQQ 13.0 |
| `top3_weight_pct` | **46.0** |
| `dominant_asset_class` | fixed_income **42.0** |
| `dominant_region` | US **82.0** |
| `dominant_currency` | USD **100.0** |
| `metadata.cash_treatment` | `market_tickers_only` |
| `metadata.cash_proxy_used_for_real_cash` | `false` |

**Concentration flags (live demo):** `single_region_dominance` medium (US 82%); `single_currency_dominance` medium + high (USD 100%).

**Manifest:** `output_manifest.json` → `subject_diagnostics_contract.portfolio_xray_json.product_capital_structure_key` = `block_2_1_asset_allocation`.

---

## 6. Out of Scope / Deferred (documented)

| Item | Status |
| --- | --- |
| HTML/PDF Block 2.1 product view (G11) | Post-MVP; legacy formatters use `sections.asset_allocation` |
| `problem_classification` reads structured Block 2.1 flags (G10) | Post-MVP |
| Sector/subtype in product contract | Advanced; excluded per ExecPlan |
| Root `config.yml` + 5% Cash USD | Optional operator change; fixture covers real-cash proof |

---

## 7. Operator Checklist

1. Run diagnosis: `python run_portfolio_review.py --skip-candidates`
2. Open `{output_dir_final}/analysis_subject/portfolio_xray.json` → `block_2_1_asset_allocation`
3. For one-hypothesis demo: `python run_portfolio_review.py --candidates equal_weight` then `python scripts/validate_one_candidate_demo.py`
4. For real-cash proof without changing root config: use fixture `tests/fixtures/mvp_portfolios/demo_usd_asset_allocation_with_cash_5pct.yml` in tests or a copied config.

---

**Closure:** ExecPlan [2026-05-26_block_2_1_asset_allocation_plan.md](../exec_plans/2026-05-26_block_2_1_asset_allocation_plan.md) marked **Completed** 2026-05-26.
