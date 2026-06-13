# Block 3.2 Stress Results MVP — Acceptance Audit (Session 08)

Date: 2026-05-27

Purpose: Close [Block 3.2 Stress Results MVP ExecPlan](../exec_plans/2026-05-27_block_3_2_stress_results_plan.md) **Session 08** and record whether the product-facing `stress_results_v1` contract is accepted on the portfolio-first diagnosis path.

Related:

- Canonical contract: [stress_testing_spec.md](../specs/stress_testing_spec.md) §12.1
- Stress Lab boundary: [stress_lab_layer_spec.md](../specs/stress_lab_layer_spec.md) §3.2
- Implementation: `src/stress_results_block.py`, wired from `src/stress.py`, `run_report.py`, `run_optimization.py`
- Operator guide: [product_flow_operator_guide.md](../product_flow_operator_guide.md) (step 3 — `analysis_subject/stress_report.json`)

---

## 1. Executive Summary

| Question | Verdict |
| --- | --- |
| Is `stress_results_v1` on live portfolio-first diagnosis... | **Yes** — `run_portfolio_review.py --skip-candidates` refreshed `Main portfolio/analysis_subject/stress_report.json`. |
| Are all 8 synthetic + 5 historical product rows present... | **Yes** — canonical ID order; counts match `SYNTHETIC_SCENARIO_IDS` / `HISTORICAL_SCENARIO_IDS`. |
| Do worst-case selectors match `stress_conclusions`... | **Yes** — worst synthetic `recession_severe` (-22.0%); worst historical `2022` (max drawdown -19.8%). |
| Is Core MVP in diagnostic mode without mandate fields on Block 3.2 rows... | **Yes** — `loss_gate_mode: diagnostic`; no `pass` / `loss_ok` / `diagnostic_code` on product rows. |
| Are English `diagnosis_summary_en` templates populated when data allows... | **Yes** — 8/8 synthetic; 3/5 historical (dotcom / 2008 omit narrative when loss contribution unavailable — §5.3). |
| Is the full ExecPlan accepted (Sessions 00–08)... | **Yes — 9/9** sessions complete (see §3). |

**Bottom line:** Block 3.2 Stress Results MVP is **complete**. Operators read per-scenario stress diagnosis from `stress_results_v1` on subject `stress_report.json`; `stress_conclusions` remains the compatibility worst-case rollup; snapshot carries a compact `stress_results` envelope mirror.

---

## 2. Session Rollup (00–08)

| Session | Objective | Status | Primary evidence |
| --- | --- | --- | --- |
| 00 | ExecPlan foundation + field audit | **Done** | ExecPlan sections A–H |
| 01 | Product contract in specs | **Done** | stress testing spec §12.1; PRODUCT §4.3.2 |
| 02 | Builder scaffold | **Done** | `src/stress_results_block.py` |
| 03 | Synthetic per-scenario rows + narratives | **Done** | 8 synthetic rows + templates |
| 04 | Historical rows (paths → loss contribution) | **Done** | 5 historical rows |
| 05 | Wire `run_stress` + `run_report` refresh | **Done** | `attach_stress_results_v1` |
| 06 | Commentary/snapshot mirror (minimal) | **Done** | `portfolio_commentary.py`, `snapshot.py` |
| 07 | Contract tests + regression bundle | **Done** | TESTING.md Block 3.2 bundle; CHANGELOG |
| 08 | Live proof + closure | **Done** | This document; live run §5 |

---

## 3. ExecPlan Acceptance Criteria

| # | Criterion | Result | Evidence |
| --- | --- | --- | --- |
| 1 | `stress_results_v1` on diagnosis run | **PASS** | Live `--skip-candidates`; §5.1 |
| 2 | 8 synthetic + 5 historical scenarios in canonical order | **PASS** | §5.2 |
| 3 | Worst synthetic = min `portfolio_loss_pct` | **PASS** | `recession_severe` **-0.2203** |
| 4 | Worst historical = min `max_dd` (drawdown) | **PASS** | `2022` drawdown **-0.1976** |
| 5 | `loss_gate_mode: diagnostic`; no mandate fields on Block 3.2 rows | **PASS** | §5.4 |
| 6 | `diagnosis_summary_en` when attribution/loss data allows | **PASS** | §5.3 |
| 7 | `stress_conclusions` worst IDs align with Block 3.2 envelope | **PASS** | §5.5 |
| 8 | Snapshot compact mirror | **PASS** | `snapshot_10y.json` → `stress_suite_results.stress_results` |
| 9 | Closure pytest bundle | **PASS** | **75 passed** (Block 3.2 bundle) |

**Block 3.2 Stress Results MVP: ACCEPTED.**

---

## 4. Fixture-Locked Behavior (pytest)

Source: `tests/test_stress_results_block_contract.py`, `tests/test_stress_diagnostic_mode.py`, `tests/test_stress_scenario_coverage_contract.py`, `tests/test_stress_downstream_integration.py`.

| Check | Expected |
| --- | --- |
| `version` | `stress_results_v1` |
| Builder attaches from `run_stress` / `attach_stress_results_v1` | Present on report dict |
| Diagnostic mode | No mandate keys on Block 3.2 product rows |
| Historical RC | `not_applicable` on historical rows |
| Factor on historical after enrichment | `available` when `pnl_by_factor_pct` present |

---

## 5. Live Verification (Session 08, root `config.yml`)

Commands (repository root, warm cache):

```bash
python run_portfolio_review.py --skip-candidates
python -m pytest tests/test_stress_results_block_contract.py tests/test_stress_diagnostic_mode.py tests/test_stress_scenario_coverage_contract.py tests/test_stress_downstream_integration.py -q
python scripts/verify_docs.py
```

| Check | Result |
| --- | --- |
| Diagnosis-only review | Exit **0**; `product_diagnosis_only`; `analysis_subject` materialized |
| Closure pytest bundle | **75 passed** |
| `verify_docs.py` | **OK** |

Artifact: `Main portfolio/analysis_subject/stress_report.json` (refreshed **2026-05-27**).

### 5.1 Block envelope (`stress_results_v1.envelope`)

| Field | Observed |
| --- | --- |
| `worst_synthetic.scenario_id` | `recession_severe` |
| `worst_synthetic.portfolio_loss_pct` | **-0.2203** |
| `worst_synthetic.top_factor_drivers` (top 3) | Equity, USD, Commodity |
| `worst_synthetic.helped_assets` | TLT, BND, SCHP (positive synthetic PnL on worst shock) |
| `worst_historical.episode` | `2022` |
| `worst_historical.portfolio_loss_pct` | **-0.1629** |
| `worst_historical.drawdown_pct` | **-0.1976** |
| `worst_historical.top3_loss_assets` | TLT, QQQ, BND |

### 5.2 Per-scenario synthetic (`synthetic_scenarios`)

| scenario_id | portfolio_loss_pct | diagnosis_summary_en |
| --- | ---: | --- |
| equity_shock | -0.1617 | Yes |
| credit_shock | -0.0295 | Yes |
| rates_shock | -0.0833 | Yes |
| inflation_stagflation | -0.0912 | Yes |
| liquidity_shock | -0.0929 | Yes |
| usd_shock | -0.0577 | Yes |
| commodity_shock | -0.0057 | Yes |
| recession_severe | -0.2203 | Yes |

### 5.3 Per-scenario historical (`historical_episodes`)

| episode | portfolio_loss_pct | drawdown_pct | loss_contribution | factor_attribution | diagnosis_summary_en |
| --- | ---: | ---: | --- | --- | --- |
| dotcom | — | — | unavailable | available | No (insufficient episode loss path) |
| 2008 | — | — | unavailable | available | No (insufficient episode loss path) |
| 2020 | -0.0078 | -0.0526 | available | available | Yes |
| 2022 | -0.1629 | -0.1976 | available | available | Yes |
| banking_2023 | 0.0072 | -0.0103 | available | available | Yes |

**Note:** Early episodes without usable static-weight loss contribution still expose factor attribution after `run_report` enrichment; narrative templates correctly omit when `loss_contribution` is unavailable (ExecPlan §B.3).

### 5.4 Diagnostic boundary

| Check | Result |
| --- | --- |
| `stress_report.json` `loss_gate_mode` | **diagnostic** |
| `stress_results_v1.loss_gate_mode` | **diagnostic** |
| Mandate keys on synthetic/historical Block 3.2 rows | **Absent** |
| Evidence row `pass` on synthetic scenarios (engine) | `null` (diagnostic — not copied to Block 3.2) |

### 5.5 Alignment with `stress_conclusions`

| Rollup field | `stress_conclusions` | Block 3.2 envelope |
| --- | --- | --- |
| Worst synthetic ID | `recession_severe` | `recession_severe` |
| Worst synthetic PnL | -0.2203 | -0.2203 |
| Worst historical episode | `2022` | `2022` |
| Worst historical max_dd | -0.1976 | -0.1976 (as `drawdown_pct`) |

### 5.6 Snapshot mirror

`Main portfolio/analysis_subject/snapshot_10y.json` → `stress_suite_results.stress_results` carries `version`, `loss_gate_mode`, and full `envelope` (worst synthetic / worst historical) for downstream comparison surfaces.

---

## 6. Out of Scope / Deferred (documented)

| Item | Status |
| --- | --- |
| PDF/HTML Block 3.2 product redesign | Post-MVP (ExecPlan non-goal) |
| Mandate-mode Block 3.2 pass/fail rows | Legacy policy path only; not Core MVP diagnostic |
| `portfolio_xray.json` Block 3.2 key | Deferred unless explicitly promoted |
| Full historical narratives for dotcom / 2008 on young-ETF-heavy books | Requires episode loss path data; degrade is by design |

---

## 7. Operator Checklist

1. Run diagnosis: `python run_portfolio_review.py --skip-candidates`
2. Open `{output_dir_final}/analysis_subject/stress_report.json` → `stress_results_v1`
3. Read `envelope.worst_synthetic` / `envelope.worst_historical` for headline stress; drill into `synthetic_scenarios` / `historical_episodes` for per-scenario `diagnosis_summary_en`
4. For comparison flows, use `snapshot_10y.json` → `stress_suite_results.stress_results` compact mirror
5. Regression after builder changes: TESTING.md Block 3.2 bundle (75 tests as of closure)

---

**Closure:** ExecPlan [2026-05-27_block_3_2_stress_results_plan.md](../exec_plans/2026-05-27_block_3_2_stress_results_plan.md) marked **Completed** 2026-05-27.
