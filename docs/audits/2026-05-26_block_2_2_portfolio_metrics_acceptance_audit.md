# Block 2.2 Portfolio Metrics / Risk Diagnostics MVP — Acceptance Audit (Session 08)

Date: 2026-05-26

Purpose: Close [Block 2.2 Portfolio Metrics MVP ExecPlan](../exec_plans/2026-05-26_block_2_2_portfolio_metrics_plan.md) **Session 08** and record whether the product-facing `block_2_2_portfolio_metrics` contract is accepted on portfolio-first diagnosis and one-candidate runs.

Related:

- Canonical contract: [portfolio_xray_diagnostics_spec.md](../specs/portfolio_xray_diagnostics_spec.md) §2.2.1
- Decision: `DEC-2026-05-26-003`
- Implementation: `src/block_2_2_portfolio_metrics.py`, `build_portfolio_xray_v2` in `src/portfolio_xray.py`
- Real-cash regression fixture: `tests/fixtures/mvp_portfolios/demo_usd_asset_allocation_with_cash_5pct.yml`
- Operator guide: [product_flow_operator_guide.md](../product_flow_operator_guide.md) (step 2 — `analysis_subject/portfolio_xray.json`)

---

## 1. Executive Summary

| Question | Verdict |
| --- | --- |
| Is `block_2_2_portfolio_metrics` on live diagnosis path? | **Yes** — `run_portfolio_review.py --skip-candidates` refreshed `Main portfolio/analysis_subject/portfolio_xray.json` with populated Block 2.2. |
| Is Block 2.2 present after one-candidate demo? | **Yes** — same subject artifact after `--candidates equal_weight`; product validator **PASS** (8 checks). |
| Does real-cash fixture surface correct treatment? | **Yes** — offline pytest: `metadata.cash_treatment` = `real_cash_position_if_present`; real-cash warning present; see §4. |
| Does Block 2.1 remain unchanged alongside Block 2.2? | **Yes** — both top-level keys coexist on subject X-Ray (§5.1). |
| Is the full ExecPlan accepted (Sessions 01–08)? | **Yes — 8/8** sessions complete (see §3). |

**Bottom line:** Block 2.2 Portfolio Metrics MVP is **complete**. Operators read portfolio behavior from `block_2_2_portfolio_metrics` on `analysis_subject/portfolio_xray.json`; legacy `sections.risk_diagnostics` remains for formatters and golden contracts.

---

## 2. Session Rollup (01–08)

| Session | Objective | Status | Primary evidence |
| --- | --- | --- | --- |
| 01 | Audit & inventory | **Done** | ExecPlan inventories, gap list G1–G12 |
| 02 | Product contract in spec | **Done** | §2.2.1; `DEC-2026-05-26-003` |
| 03 | Builder module | **Done** | `src/block_2_2_portfolio_metrics.py` |
| 04 | Input Layer / real cash pass-through | **Done** | `cash_handling` + weight labels |
| 05 | Offline fixtures | **Done** | `mvp_offline_fixtures.py` Block 2.2 seeds |
| 06 | Unit/contract tests | **Done** | `tests/test_block_2_2_portfolio_metrics.py` |
| 07 | Pipeline integration | **Done** | manifest, E2E gates, pipeline tests |
| 08 | Live demo + closure | **Done** | This document; live runs §5 |

---

## 3. ExecPlan Acceptance Criteria

| # | Criterion | Result | Evidence |
| --- | --- | --- | --- |
| 1 | `block_2_2_portfolio_metrics` on diagnosis run | **PASS** | Live `--skip-candidates`; §5.1 |
| 2 | Block 2.2 on one-candidate run | **PASS** | Live `--candidates equal_weight`; subject X-Ray refreshed |
| 3 | Block 2.1 unchanged; Block 2.2 coexists | **PASS** | Both keys on `portfolio_xray.json` |
| 4 | Product demo validator unchanged scope | **PASS** | `validate_one_candidate_demo.py` **PASS** (8 checks) |
| 5 | Real-cash fixture contract | **PASS** | §4 (pytest-locked) |
| 6 | Pipeline / manifest disclosure | **PASS** | `product_portfolio_behavior_key` on `output_manifest.json` |
| 7 | Documentation matches implementation | **PASS** | `python scripts/verify_docs.py` **OK** (post-audit) |
| 8 | Closure pytest bundle | **PASS** | **48 passed** (Block 2.1 + 2.2 closure bundle); **16 passed** (bundle/runtime regression) |

**Block 2.2 Portfolio Metrics MVP: ACCEPTED.**

---

## 4. Fixture-Locked Block 2.2 Behavior (`demo_usd_asset_allocation_with_cash_5pct.yml`)

Source: `tests/test_block_2_2_portfolio_metrics.py` (`test_block_2_2_real_cash_treatment_surfaces_warning_and_metadata`); offline seeds in `tests/mvp_offline_fixtures.py`.

| Check | Expected |
| --- | --- |
| `metadata.cash_treatment` | `real_cash_position_if_present` |
| `metadata.cash_proxy_used_for_real_cash` | `false` |
| `data_quality_warnings` | Contains *"Real cash holdings contribute 0% return"* |
| `metric_quality` | **Not** exposed on product block (`metric_quality_internal_only`: true) |

Offline minimal metrics seed (unit tests, not live market data): CAGR **0.072**, vol **0.112**, Sharpe **0.52**, max drawdown **-0.21**, beta **0.80**, downside deviation **0.078**; top correlation pair from 3×3 CSV seed: BND–GLD **0.92** (highest), GLD–SPY **0.05** (lowest).

---

## 5. Live Verification (Session 08, root `config.yml`, no real cash)

Commands (repository root, warm cache):

```bash
python run_portfolio_review.py --skip-candidates
python run_portfolio_review.py --candidates equal_weight
python scripts/validate_one_candidate_demo.py
python -m pytest tests/test_block_2_1_asset_allocation.py tests/test_block_2_2_portfolio_metrics.py tests/test_block_2_2_pipeline_integration.py tests/test_portfolio_xray_contract.py tests/test_product_bundle_paths.py tests/test_blocks_1_5_mvp_smoke.py -q
python -m pytest tests/test_product_bundle_integration.py tests/test_runtime_mode_regression_boundaries.py -q
python scripts/verify_docs.py
```

| Check | Result |
| --- | --- |
| Diagnosis-only review | Exit **0**; `product_diagnosis_only`; `analysis_subject` materialized |
| One-candidate review | Exit **0**; `product_one_candidate`; factory `equal_weight` + compare |
| `validate_one_candidate_demo.py` | **PASS** (8 checks) |
| Closure pytest bundle | **48 passed** |
| Bundle/runtime regression | **16 passed** |
| Docs verification | **OK** (after this audit file exists) |

### 5.1 Live `block_2_2_portfolio_metrics` snapshot (demo `config.yml`, 8 market tickers)

Artifact: `Main portfolio/analysis_subject/portfolio_xray.json` (refreshed **2026-05-26** diagnosis materialize). Primary window: **10Y (120M)**. Values are export-rounded (3 decimals) per metrics spec.

| Section | Field | Observed |
| --- | --- | ---: |
| Identity | `block` | `2.2_portfolio_metrics` |
| Identity | `investor_currency` | USD |
| Metadata | `cash_treatment` | `market_tickers_only` |
| Metadata | `primary_window_label` | 10Y (120M) |
| Metadata | `vol_of_vol` / `rel_vol_of_vol` | **0.032** / **0.352** |
| Return/risk | `portfolio_cagr` | **0.099** |
| Return/risk | `vol_annual` | **0.096** |
| Return/risk | `sharpe` / `sortino` | **0.799** / **1.286** |
| Return/risk | `skewness` / `kurtosis` | **-0.352** / **0.170** |
| Drawdown | `max_drawdown` | **-0.198** |
| Drawdown | `ttr_months` / `recovered` | **27.0** / true |
| Tail | `var_95` / `es_95` | **-0.009** / **-0.014** |
| Tail | `downside_deviation` | **0.060** |
| Tail | `eee_10` | **39.068** |
| Benchmark | `benchmark_ticker` | SPY |
| Benchmark | `beta_portfolio` / `corr_base` | **0.513** / **0.813** |
| Rolling core | `rolling_sharpe_36m.latest` | **1.144** |
| Rolling core | `rolling_volatility_12m.latest` | **0.091** |
| Rolling core | `rolling_beta_or_correlation` | beta **0.512**, corr **0.735** |
| Correlation | highest pair | QQQ–SPY **0.918** |
| Correlation | lowest pair | SCHD–TLT **0.096** |
| Correlation | `full_matrix_available` | true (`correlation_matrix_10y.csv`) |
| Warnings | `data_quality_warnings` | *(empty)* |

**Coexistence (Block 2.1, same artifact):** `block_2_1_asset_allocation` present; SCHD top1 **17.0%**, top3 **46.0%** (unchanged from Block 2.1 acceptance audit).

**Manifest:** `output_manifest.json` → `subject_diagnostics_contract.portfolio_xray_json.product_portfolio_behavior_key` = `block_2_2_portfolio_metrics`.

---

## 6. Out of Scope / Deferred (documented)

| Item | Status |
| --- | --- |
| Extended drawdown episode fields on live `site_api` materialize | **Fixed 2026-05-26** — [drawdown wiring bugfix](2026-05-26_block_2_2_drawdown_wiring_bugfix.md): Block 2.2 reads `analytics.drawdown_structure`; live extended fields populated. |
| `metric_quality` on legacy `sections.risk_diagnostics` items (G3) | Post-MVP; product block uses `data_quality_warnings` only |
| HTML/PDF Block 2.2 product view | Post-MVP; legacy formatters use `sections.risk_diagnostics` |
| Root `config.yml` + 5% Cash USD | Optional operator change; fixture covers real-cash proof |

---

## 7. Operator Checklist

1. Run diagnosis: `python run_portfolio_review.py --skip-candidates`
2. Open `{output_dir_final}/analysis_subject/portfolio_xray.json` → `block_2_2_portfolio_metrics`
3. For one-hypothesis demo: `python run_portfolio_review.py --candidates equal_weight` then `python scripts/validate_one_candidate_demo.py`
4. For real-cash proof without changing root config: use fixture `tests/fixtures/mvp_portfolios/demo_usd_asset_allocation_with_cash_5pct.yml` in tests or a copied config.

---

**Closure:** ExecPlan [2026-05-26_block_2_2_portfolio_metrics_plan.md](../exec_plans/2026-05-26_block_2_2_portfolio_metrics_plan.md) marked **Completed** 2026-05-26.
