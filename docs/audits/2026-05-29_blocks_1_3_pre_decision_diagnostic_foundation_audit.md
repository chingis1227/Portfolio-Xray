# Blocks 1–3 Pre-Decision Diagnostic Foundation Audit

**Status: Superseded** (2026-05-29) — Phase A remediation closed; current verdict and evidence: [Blocks 1–3 foundation closure audit](2026-05-29_blocks_1_3_foundation_closure_audit.md) (`READY_FOR_DECISION_WORKFLOW`).

Date: 2026-05-29  
Scope: Input Layer (Block 1), Portfolio X-Ray (Block 2.1–2.6), Stress Test Lab (Block 3.1–3.4), three canonical runtime modes, JSON contracts, documentation alignment, legacy leakage, semantic diagnosis, downstream readiness.  
Method: live CLI runs on repo `config.yml` demo portfolio, JSON inspection under `Main portfolio/analysis_subject/`, focused pytest bundle, `validate_live_core_artifacts`, comparison with canonical specs and prior audits.  
Out of scope: Blocks 4+ implementation changes, PDF product, optimizer zoo policy beyond artifact isolation.

Related: [runtime_entrypoints.md](../runtime_entrypoints.md), [Block 3.4 institutional upgrade acceptance](2026-05-29_block_3_4_institutional_upgrade_acceptance_audit.md), [core/full artifact confusion audit](2026-05-23_core_full_artifact_documentation_confusion_audit.md).

---

## 1. Executive verdict

| Question | Answer |
| --- | --- |
| Can the system answer the 15 diagnostic questions (portfolio identity, composition, behavior, factors, hidden risks, normal risk owners, pre-stress weaknesses, stress losses, hedge gaps, executive stress diagnosis)... | **Mostly yes** on live `analysis_subject` JSON for the demo portfolio; gaps are data-window limits (dotcom/2008), partial block statuses, and pre-stress vs post-stress framing. |
| Are three canonical runtime modes operational... | **Yes**, after one blocking fix (`export_stress_hedge_gap_bridge` timing registry). |
| Is artifact scope clean per mode (no stale compare / no Blocks 4+ leakage in core-only)... | **No** — stale comparison menu and subject-side product JSON can remain on disk; one-candidate compare still aggregates **19** on-disk candidates in `candidate_comparison.json`. |
| Do tests support readiness... | **Yes** — **232 passed**, 1 skipped in focused bundle. |
| Ready for Decision Workflow... | **No** — use verdict **`NOT_READY_RUNTIME_CONTRACT_MISMATCH`**. |

**Bottom line:** Blocks **1–3 analytical content** on `portfolio_xray.json` and `stress_report.json` is materially present, institutionally upgraded (3.3 `hedge_gap_rules_v1_2`, 3.4 `current_portfolio_stress_scorecard_rules_v1_1`), and test-backed. **Runtime artifact contracts** for core-only, diagnosis-only, and one-candidate paths do not yet guarantee operators and downstream consumers see only the intended surface (stale comparison zoo, subject folder not pruned on core-only, live E2E gate fails on a real workspace). Fix artifact hygiene and re-run this audit before freezing the foundation.

---

## 2. Run mode verification

### 2.1 Commands executed

| # | Command | Exit | Console mode label | Notes |
| --- | --- | ---: | --- | --- |
| 1 | `python run_core_diagnostics.py` | **1** (first) | `core_diagnostics_only` | Failed: `KeyError: Unknown report timing block: export_stress_hedge_gap_bridge` when `enable_report_timing=True` via review context. |
| 1b | `python run_core_diagnostics.py` (after fix) | **0** | `core_diagnostics_only` | Completed; artifacts under `Main portfolio/analysis_subject/`. |
| 2 | `python run_portfolio_review.py` | **0** | `product_diagnosis_workflow` / `diagnosis_only` | `candidate_count=0`, factory not invoked. |
| 3 | `python run_portfolio_review.py --candidates equal_weight` | **0** | `product_one_candidate` | Factory `explicit_list`, `skipped_existing` for EW; `--then-compare` ran. |

**Fix applied during audit (required to complete runs):** added `export_stress_hedge_gap_bridge` to `REPORT_TIMING_BLOCK_KEYS` in `src/report_timing.py`.

### 2.2 Mode expectations vs observed

| Mode | Expected | Observed |
| --- | --- | --- |
| Core diagnostics | Input → X-Ray → Stress only; no candidates / verdict / PDF | **Pass** after timing fix. Does **not** delete stale `problem_classification.json`, `candidate_launchpad.json`, or `ai_commentary_context.json` if left from prior runs (manifest blocks keys but files may remain). |
| Full review (no candidates) | Diagnosis + Problem Classification + Launchpad; no compare/verdict | **Pass** orchestration (`run_candidate_factory` absent). **Fail** hygiene: root `current_vs_candidate.json` / `decision_verdict.json` from prior runs remain unless manually removed. |
| One candidate (`equal_weight`) | Exactly one selected candidate in compare/verdict | **Partial pass:** `current_vs_candidate.json` has `selected_candidate_ids: ["equal_weight"]`, `view_mode: one_candidate`. **Fail:** `candidate_comparison.json` lists **19** candidates (all folders on disk). Factory profile `explicit_list`, not `core_fast` (live E2E expects `core_fast`). |

---

## 3. Block 1 — Input Layer

| Check | Result | Evidence |
| --- | --- | --- |
| Minimal input (currency, tickers, weights) | **Pass** | `config.yml`: USD, 8 ETFs, weights sum 1.00. |
| `analysis_subject` = `current_portfolio` | **Pass** | `run_metadata.json` → `analysis_subject.type`, `portfolio_role: user_current_portfolio`. |
| `analysis_mode` = `analyze_current_weights` | **Pass** | `portfolio_xray.json` Block 2.1; `run_metadata` resolved config. |
| Weights normalization | **Pass** | Snapshot `final_weights_*` match config (SCHD 17%, BND 16%, …). |
| Real cash vs cash proxy | **Pass** (no real cash in demo) | Demo has no `CASH` ticker; `cash_proxy_ticker: BIL` in analysis setup only. Fixture matrix + `partition_market_data_tickers` tests cover real cash. |
| No forced mandate/client fields in first input | **Pass** | `config.yml` Core MVP demo shape; pending_fields logged for weight caps only. |
| Core run does not trigger candidate zoo | **Pass** | Plan has single `run_report.py --core-diagnostics-only` step. |

**Diagnostic Q1–Q2:** Correct current portfolio, USD, weights — **yes**.

---

## 4. Block 2 — Portfolio X-Ray

### 4.1 Block 2.1 Asset Allocation — **Pass**

- Present: `block_2_1_asset_allocation` (12 top-level fields).
- `total_holdings: 8`; top1 SCHD 17%; top3 46%; breakdowns by asset, class, risk factor, role, region, currency.
- Concentration / duplicate flags and data-quality warnings present in structure (live demo: US 82%, fixed income 42% dominant).

### 4.2 Block 2.2 Portfolio Metrics — **Pass** (shape differs from flat 3Y/5Y/10Y table)

- Present: `block_2_2_portfolio_metrics` with `return_risk_metrics` (CAGR 9.9%, vol 9.6%, Sharpe 0.799, Sortino, Treynor, skew/kurtosis), `drawdown_diagnostics`, `tail_risk_diagnostics`, `benchmark_dependence`, `rolling_diagnostics`, `correlation_breakdown`.
- Rolling/advanced under `rolling_diagnostics.core_view`; correlation pairs in `correlation_breakdown`.
- `metric_quality` not exposed as user-facing metric (warnings in `data_quality_warnings` only) — **aligned**.

### 4.3 Block 2.3 Factor Exposure — **Pass**

- Eight production factors in `factor_beta_snapshot`: `beta_eq` 0.404, `beta_rr` -4.163, `beta_inf` -3.448, `beta_credit` 0.272, `beta_usd` -0.32, `beta_cmd` 0.111, `beta_vix` -0.002, `beta_us_growth` 0.001.
- Windows: `factor_betas_3y` / `5y` / `10y`; Kalman, confidence, variance contribution, top-3 risk ranking, `factor_diagnostics_meta`.
- `status: available`; diagnostic-only disclaimer on X-Ray root — **no rebalance language**.

### 4.4 Block 2.4 Hidden Exposure — **Partial pass**

- `ruleset: heuristic_v2`, `status: partial`, six alerts present.
- Live scores: hidden_equity Low 33; duration Medium 66; credit Low 19; correlation Medium 40; **weak_hedge Medium 51**; tail_risk Unavailable.
- Alert contract fields (status, score, evidence, confidence, confidence_reason, limitations, contributing_assets, next_tests, diagnostics_meta) — **present** (contract tests).
- Rule-based only — **no AI-generated alerts**.

### 4.5 Block 2.5 Risk Budget View — **Pass**

- `status: ok`; top1 risk contributor SCHD; RC_vol / risk_contribution_pct / weight_vs_risk_gap; bucket contributions.
- No stress PnL fields in product block — **aligned**.

### 4.6 Block 2.6 Portfolio Weakness Map — **Partial pass**

- `heuristic_v2`, eight canonical `risk_types` (equity_shock … recession_severe).
- Pre-stress only (no stress PnL / hedge gap in block) — **aligned**.
- **Gap:** `recession_severe` scored **Unavailable** in 2.6 while Block 3.2 worst synthetic is `recession_severe` (-21.2%) — boundary/availability mismatch (see §9).

**Diagnostic Q3–Q9:** Composition, concentration, behavior, factors, hidden risks, risk owners, pre-stress weaknesses — **answered** with noted partial statuses.

---

## 5. Block 3 — Stress Test Lab

### 5.1 Block 3.1 Scenario Library — **Pass** (data-limited history)

- `scenario_library_meta` on `stress_report.json`; separate `scenario_library.json` / normalized copy on disk.
- Synthetic eight IDs align with 2.6.
- Historical: five episodes; **dotcom / 2008** without portfolio loss (panel starts 2014-06); **2020 / 2022 / banking_2023** populated — expected per data policy.

### 5.2 Block 3.2 Stress Results — **Pass**

- `stress_results_v1` with eight synthetic scenarios; losses e.g. equity_shock -16.2%, recession_severe -21.2%.
- Per-scenario `pnl_by_asset_pct`, factor attribution, top loss assets, helped/hurt where enabled.
- Legacy `scenario_results` retained for compatibility.

### 5.3 Block 3.3 Hedge Gap Analysis — **Pass**

- `hedge_gap_analysis_v1`, `ruleset_version: hedge_gap_rules_v1_2`, `block_status: ok`.
- Main gap (v2 scoring): **recession_severe_protection**, offset coverage **11.5%**, `protection_status: weak_protection`, `main_gap_score: 0.221`.
- Eight protection types in `by_risk_type`; contribution-based helped/hurt; legacy `hedge_gap_analysis` secondary on `stress_report.json`.

### 5.4 Block 3.4 Current Portfolio Stress Scorecard — **Partial pass**

- `current_portfolio_stress_scorecard_v1`, `ruleset_version: current_portfolio_stress_scorecard_rules_v1_1`.
- `block_status: partial`; `legacy_fallback_used: false`.
- `stress_diagnosis.headline` non-empty; `diagnosis_confidence: low`.
- Summaries: worst synthetic/historical, loss/risk, hedge gap, pre-stress confirmation bridges, `problem_classification_signals`, `next_decision_uses`.
- **No mandate pass/fail** inside 3.4 product block — **aligned**.

**Diagnostic Q10–Q13:** Stress losses, hedge gap, executive stress diagnosis — **yes**; headline matches recession_severe + weak offset story.

---

## 6. JSON output audit (live `Main portfolio/`)

### 6.1 By mode (after sequential runs on same workspace)

| Artifact | Core (intended) | Review no candidate | Review + EW |
| --- | --- | --- | --- |
| `analysis_subject/portfolio_xray.json` | Required | Required | Required |
| `analysis_subject/stress_report.json` | Required | Required | Required |
| `analysis_subject/problem_classification.json` | Should be absent / not authoritative | Present | Present |
| `analysis_subject/candidate_launchpad.json` | Should be absent / not authoritative | Present | Present |
| `analysis_subject/ai_commentary_context.json` | Should be absent / not authoritative | Present (diagnosis phase) | Present |
| `current_vs_candidate.json` (root) | Absent | Should be absent | Present (`equal_weight` only) |
| `decision_verdict.json` (root) | Absent | Should be absent | Present |
| `candidate_comparison.json` | Absent | Stale risk | **19 candidates** |
| `candidate_factory_run.json` | Absent | Absent | Present (`explicit_list`) |

### 6.2 Contract highlights (live subject)

- `portfolio_xray.json`: `version: portfolio_xray_v2`, `diagnostic_only: true`, Blocks 2.1–2.6 nested.
- `stress_report.json`: `stress_results_v1`, `hedge_gap_analysis_v1`, `current_portfolio_stress_scorecard_v1`, legacy `stress_scorecard_v1` still present (secondary).
- `output_manifest.json`: documents product bundle keys; core-only should block PC/launchpad keys from manifest — **files may still exist on disk**.

---

## 7. Documentation alignment audit

| Source | Blocks 1–3 accuracy | Notes |
| --- | --- | --- |
| `docs/runtime_entrypoints.md` | **Aligned** | Three active commands documented. |
| `README.md` / `SPEC.md` | **Aligned** | Diagnosis-first; Health/Robustness/Macro not Core MVP. |
| `OUTPUTS.md` / Block 3.3–3.4 specs | **Aligned** | v1 product keys documented post institutional upgrade. |
| `AGENTS.md` | **Aligned** | `run_core_diagnostics.py` + `run_portfolio_review.py` matrix. |
| Comparison vs factory scope | **Documented but easy to misread** | SPEC/2026-05-23 audit: `candidate_comparison.json` aggregates **on-disk** menu, not last factory scope. Operators can misinterpret one-candidate CLI as a one-row comparison file. |

No material claim found that Block 3.3/3.4 are still Target-only. Legacy optimizers correctly under `legacy/runners/`.

---

## 8. Legacy vs product-facing audit

| Item | Location | Status | Leaks into Core MVP... |
| --- | --- | --- | --- |
| `stress_scorecard_v1` | `stress_report.json` | Legacy / mandate rollup | Secondary; 3.4 `legacy_fallback_used: false` |
| `hedge_gap_analysis` (legacy) | `stress_report.json` | Legacy | Secondary to `hedge_gap_analysis_v1` |
| `scenario_results` (flat) | `stress_report.json` | Legacy compatibility | Coexists with `stress_results_v1` |
| Policy / EW / RP / robust folders | `Main portfolio/*` | Legacy / research | Comparison menu ingests if on disk — **yes, leakage** |
| Portfolio Health / Robustness | decision package | Advanced | Not written in default `site_api` review |
| PDF suite | `pdf files/` | Legacy export | Not run (default `site_api`) — **pass** |
| `stress_commentary.txt` / rolling PNG | `analysis_subject/` | Technical / export-adjacent | Present under `site_api` (not PDF); acceptable as backend evidence |

---

## 9. Semantic diagnosis review (demo portfolio)

| Review | Assessment |
| --- | --- |
| 2.1 composition | Plausible: income/dividend + bonds + metals + growth (SCHD, BND, QQQ, GLD/SLV, TLT). |
| Concentration | Top3 46% moderate; US 82% — flags reasonable. |
| 2.2 behavior | CAGR ~9.9%, vol ~9.6%, MDD ~-19.8% — coherent multi-asset profile. |
| 2.3 factors | Positive equity beta, large negative real-rate/inflation betas — consistent with bonds/gold mix. |
| 2.4 vs 3.3 weak hedge | **Explainable:** 2.4 weak_hedge **Medium** (pre-stress heuristics); 3.3/PC **high** weak protection (11.5% offset on recession_severe). Problem Classification bridges both — **not a silent contradiction**. |
| 2.6 vs 3.2 | inflation_stagflation Medium (41) vs loss -9.1%; recession_severe **Unavailable** in 2.6 but worst in stress — **needs explicit “unavailable pre-stress / confirmed in Stress Lab” UX** (partially via 3.4 pre_stress_confirmation). |
| 3.4 headline | Matches worst synthetic recession_severe and weak hedge — **coherent**. |
| Problem Classification | Primary: weak hedge behavior; secondary concentration and drawdown — **aligned** with 3.3/3.4. |
| Candidate Launchpad | Suggests crisis resilience / diversification paths — **reasonable** given problems. |
| EW compare | Slightly higher CAGR/Sharpe, similar vol/MDD — verdict low confidence, no trade execution — **appropriately cautious**. |
| Limitations | `diagnosis_confidence: low`, factor beta overlay warnings, historical panel 2014+ — **visible**. |

**No critical silent contradiction** found; **moderate** 2.6 recession_severe availability vs 3.2 severity should be tightened in copy or scoring rules.

---

## 10. Downstream readiness (Blocks 4–7 consumption)

| Consumer | Can use current foundation... | Blocker |
| --- | --- | --- |
| Problem Classification | **Yes** | Uses v1 hedge gap + scorecard; live output sensible. |
| Candidate Launchpad | **Yes** | Driven from PC. |
| Current vs Candidate | **Partial** | `current_vs_candidate` OK for EW; **`candidate_comparison.json` over-broad**. |
| Decision Verdict | **Partial** | EW-only verdict OK; confidence low by design. |
| AI Commentary | **Yes** | `ai_commentary_context.json` diagnosis grounding; v1 stress context. |
| Monitoring / What Changed | **Not verified** | `what_changed_summary.json` present after compare run only. |

---

## 11. Test results

**Command:**

```bash
python -m pytest tests/test_mvp_input_defaults.py tests/test_input_assumptions.py \
  tests/test_portfolio_xray_contract.py tests/test_block_2_4_hidden_exposure.py \
  tests/test_block_2_6_portfolio_weakness_map.py tests/test_hedge_gap_analysis_v1_contract.py \
  tests/test_current_portfolio_stress_scorecard_v1_contract.py tests/test_problem_classification.py \
  tests/test_ai_commentary_context.py tests/test_live_core_e2e_validation.py \
  tests/test_core_mvp_blocks_1_3_fixture_matrix.py tests/test_core_diagnostics_entrypoint.py -q
```

**Result:** **232 passed**, **1 skipped**, 0 failed (~41s).

**Note:** `test_input_layer_mvp.py` does not exist; used `test_mvp_input_defaults.py` + `test_input_assumptions.py`.

**Live E2E validator** (`validate_live_core_artifacts(Main portfolio)`): **FAIL**

- `candidate_menu.review_mode` expected `core`, got `full`
- `factory_profile_id` expected `core_fast`, got `explicit_list`
- `comparison_candidate_count: 19`

---

## 12. Gaps and fixes required

| Priority | ID | Gap | Fix |
| --- | --- | --- | --- |
| **P0** | R1 | Core diagnostics crashed on timing registry | **Fixed in audit:** `export_stress_hedge_gap_bridge` in `src/report_timing.py`. Add regression test for timing block registry parity. |
| **P0** | R2 | One-candidate path leaves **19-row** `candidate_comparison.json` | Scope comparison write to `selected_candidate_ids` + baseline only, or mark menu `factory_evidence_status: not_authoritative` and filter rows; align with operator guide. |
| **P0** | R3 | Stale root decision artifacts after diagnosis-only | On `diagnosis_only` workflow, remove or tombstone `current_vs_candidate.json`, `decision_verdict.json`, or write explicit `no_candidate` sentinels. |
| **P1** | R4 | Core-only does not prune subject PC/launchpad/AI files | Delete or move aside stale product JSON when `product_bundle_scope=core_blocks_1_3`. |
| **P1** | R5 | `validate_live_core_artifacts` fails on real workspace | Re-run after R2–R4; or split validator profiles for `explicit_list` one-candidate vs `core_fast` batch. |
| **P2** | R6 | 2.6 `recession_severe` Unavailable vs 3.2 worst case | Score or mark “stress-confirmed” when 3.2 available; improve 3.4 bridge text. |
| **P2** | R7 | Scorecard `block_status: partial` | Document required fields for `ok` on demo portfolio; fix data gaps if any. |
| **P3** | R8 | Historical dotcom/2008 empty | Data policy / disclosure only (2014+ panel). |

---

## 13. Acceptance criteria scorecard

| # | Criterion | Result |
| --- | --- | --- |
| 1 | Three runtime modes execute | **Pass** (after R1 fix) |
| 2 | Core mode = Blocks 1–3 only | **Pass** orchestration; **Fail** stale file hygiene (R4) |
| 3 | No-candidate review = no zoo | **Pass** orchestration; **Fail** stale compare/verdict (R3) |
| 4 | EW = one selected candidate | **Partial** — CVC/verdict yes; comparison menu no (R2) |
| 5 | `portfolio_xray` 2.1–2.6 | **Pass** |
| 6 | `stress_report` 3.2–3.4 v1 | **Pass** |
| 7 | Block 1 cash | **Pass** (demo); fixtures cover real cash |
| 8 | Block 2 consistent | **Pass** / partial statuses |
| 9 | Block 3 consistent | **Pass** / partial 3.4 |
| 10 | 3.3/3.4 v1 primary | **Pass** |
| 11 | PC without stale legacy | **Pass** content; comparison file **Fail** (R2) |
| 12 | AI context grounded | **Pass** |
| 13 | No stale candidates by default | **Pass** factory; **Fail** comparison aggregate (R2) |
| 14 | Documentation matches runtime | **Pass** with known comparison caveat |
| 15 | Advanced not Core MVP | **Pass** |
| 16 | Semantic contradictions | **Pass** with moderate 2.6/3.2 note |
| 17 | Tests pass | **Pass** |
| 18 | Clear final verdict | **This document** |

---

## 14. Final readiness verdict

### `NOT_READY_RUNTIME_CONTRACT_MISMATCH`

**Rationale:** Analytical Blocks 1–3 are implementated and test-green, but **runtime artifact scope** does not yet meet the pre-decision contract: first core run was blocked by a timing registry bug (fixed), **one-candidate compare still surfaces a 19-candidate menu from disk**, diagnosis-only does not clear prior verdict/compare files, and **live core E2E validation fails** on the operator workspace.

### Recommended next step

1. Land **R2–R4** (comparison scoping, stale artifact hygiene, core-only prune).  
2. Re-run the three CLI modes on a **clean** `Main portfolio/` (or fresh output dir).  
3. Confirm `validate_live_core_artifacts` → `ok`.  
4. Re-run this audit checklist; target verdict **`READY_FOR_DECISION_WORKFLOW`** when R2–R5 are closed.

**Safe to build next (with caveats):** Problem Classification and Candidate Launchpad logic against `portfolio_xray.json` / `stress_report.json` content; **not safe** to treat `candidate_comparison.json` as authoritative for one-candidate product UX until R2 is fixed.

---

## 15. Session evidence log

| Category | Detail |
| --- | --- |
| **Audited** | Blocks 1–3 product contracts, three runtime entrypoints, downstream JSON, docs, legacy boundaries, semantic story for demo portfolio. |
| **Files inspected** | `config.yml`, `Main portfolio/analysis_subject/{portfolio_xray,stress_report,problem_classification,candidate_launchpad,ai_commentary_context,output_manifest,run_metadata}.json`, `Main portfolio/{current_vs_candidate,decision_verdict,candidate_comparison,candidate_factory_run}.json`, `src/report_timing.py`, `src/live_core_e2e.py`, canonical specs/README/SPEC/OUTPUTS. |
| **Outputs generated** | Refreshed subject diagnostics and decision package from live runs (2026-05-29). |
| **Fixes made** | `src/report_timing.py` — register `export_stress_hedge_gap_bridge`. |
| **Key JSON paths** | `portfolio_xray.json` → `block_2_1_*` … `block_2_6_*`; `stress_report.json` → `stress_results_v1`, `hedge_gap_analysis_v1`, `current_portfolio_stress_scorecard_v1`. |

---

## 16. Audit register

| Date | Audit | Status |
| --- | --- | --- |
| 2026-05-29 | Blocks 1–3 Pre-Decision Diagnostic Foundation (this document) | **Superseded** → [foundation closure](2026-05-29_blocks_1_3_foundation_closure_audit.md) |
