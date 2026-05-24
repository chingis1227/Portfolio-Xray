# Blocks 1–5 End-to-End Timing Audit (Post PDF Removal / site_api Default)

Date: 2026-05-24

Purpose: Fresh measured runtime for the portfolio-first Blocks 1–5 path after per-candidate PDF removal and `site_api` default output policy. Identifies remaining bottlenecks and safe optimization boundaries without changing formulas, weights, comparison semantics, or JSON contracts.

Scope: `output_profile=site_api`, `pdf_mode=none`, `execution_mode=standard`, sequential factory (parallel **not** measured). Isolated project roots under `tmp/blocks_1_5_timing_audit/` — repository portfolio folders **not** refreshed.

Evidence:

- Script: `scripts/blocks_1_5_e2e_timing_audit.py`
- JSON: `tmp/blocks_1_5_timing_audit/combined_summary.json`
- Per-scenario: `default_core_summary.json`, `full_menu_reference_summary.json`

Environment: Windows, Python 3.13 (`.venv`), root `config.yml` (8 tickers), monthly/daily cache **warm** (`no_cache=False`). Network used for any cache miss during `analysis_subject` factor download.

---

## 1. Executive Summary

### Primary path — default Blocks 1–5 (`--mode core`, `core_v1`, 6 candidates)

| Metric | Measured |
| --- | ---: |
| **Total wall clock** | **542.5 s (~9.0 min)** |
| `analysis_subject` materialization | 114.1 s (21.0%) |
| Candidate factory (weights + lightweight reports) | 426.6 s (78.6%) |
| Comparison + decision package | 1.7 s (0.3%) |
| Per-candidate PDF time | **0.0 s** (confirmed) |
| Factory `run_status` | `full_success` (6/6) |

**PDF removal confirmed:** `pdf_seconds=0.0` at factory and per-candidate level; project-root artifact counts: `pdf=0`, `html=0`, `txt=0`, `csv=0`, `png=0`.

**Expected speedup vs legacy full report + per-candidate PDF:** **Yes.** Legacy baseline ~228 s/candidate × 16 ≈ 57 min ([2026-05-22 timing baseline](2026-05-22_candidate_factory_timing_baseline.md)). Current default core E2E is ~9 min for subject + 6 candidates + decision package — dominated by computation, not export.

**Biggest remaining bottleneck:** **Candidate factory lightweight reports** (78.6% of total). Within factory aggregate block timing (6 candidates), the top three named blocks are:

1. **`macro_regime`** — 60.0 s (38.2% of named report blocks)
2. **`daily_tail_risk`** — 34.7 s (22.1%)
3. **`snapshots`** — 33.2 s (21.1%) — includes snapshot JSON assembly tied to metrics/stress

Shared-evidence blocks (`asset_metrics`, `run_stress`, `factor_regression`, `factor_betas`) remain near-zero aggregate time — prior Shared Evidence work is holding.

### Reference path — full menu (`default_v1`, 16 candidates, sequential)

| Metric | Measured | Prior audit (Shared Evidence Session 06) |
| --- | ---: | ---: |
| Total wall clock (E2E incl. subject) | **973.1 s (~16.2 min)** | Factory-only wall **877.1 s** (no subject stage) |
| Factory `report_seconds` | **853.2 s** | **857.7 s** (−0.5%) |
| Factory `run_status` | `partial_success` (13/2/1) | Same status pattern |
| Per-candidate PDF | **0.0 s** | 0.0 s |

Full-menu factory timing is **essentially unchanged** vs Shared Evidence Session 06; E2E adds ~100 s for `analysis_subject`.

**Not measured this run:** parallel factory (`--parallel-lightweight-reports`), cold cache (`--no-cache`), subprocess-only CLI wall clock (audit uses in-process orchestration calling the same report/factory functions).

---

## 2. Runtime Breakdown

### 2.1 Default core (`core_v1`, 6 candidates) — primary product path

| Stage | Wall clock (s) | % of total | Notes |
| --- | ---: | ---: | --- |
| Input validation / config resolve | 0.0 | 0.0% | Negligible |
| `analysis_subject` materialization | 114.1 | 21.0% | Full report path (not lightweight); includes X-Ray, stress, factors |
| Candidate factory | 426.6 | 78.6% | Weights 3.0 s; reports 410.7 s |
| Comparison + decision package | 1.7 | 0.3% | Read-only aggregation |
| **Total** | **542.5** | 100% | |

**Within `analysis_subject` report blocks (single run):**

| Block | Seconds |
| --- | ---: |
| `factor_betas` | 19.6 |
| `macro_regime` | 13.6 |
| `factor_regression` | 11.0 |
| `factor_decomposition` | 9.2 |
| `daily_tail_risk` | 5.1 |
| `snapshots` | 4.9 |
| Other | < 2 each |

**Within factory aggregate report blocks (6 candidates, summed):**

| Block | Seconds | % of named aggregate (156.9 s) |
| --- | ---: | ---: |
| `macro_regime` | 60.0 | 38.2% |
| `daily_tail_risk` | 34.7 | 22.1% |
| `snapshots` | 33.2 | 21.1% |
| `portfolio_pca` | 21.7 | 13.9% |
| `scenario_library` | 2.6 | 1.7% |
| `factor_covariance` | 1.8 | 1.1% |
| `run_stress` | 0.3 | 0.2% |
| `factor_regression` | 0.8 | 0.5% |
| `factor_betas` | 0.1 | 0.1% |
| Other | < 1 each | — |

Per-candidate lightweight report mean: **~68.5 s** (range 65.8–74.9 s).

### 2.2 Full menu reference (`default_v1`, sequential)

| Stage | Wall clock (s) | % of total |
| --- | ---: | ---: |
| `analysis_subject` | 99.8 | 10.3% |
| Candidate factory | 870.9 | 89.5% |
| Comparison + decision package | 2.4 | 0.2% |
| **Total** | **973.1** | 100% |

**Factory aggregate report blocks (13 succeeded candidates, summed):**

| Block | Seconds | % of named aggregate (343.3 s) |
| --- | ---: | ---: |
| `macro_regime` | 133.8 | 39.0% |
| `daily_tail_risk` | 78.0 | 22.7% |
| `snapshots` | 72.6 | 21.1% |
| `portfolio_pca` | 40.1 | 11.7% |
| `scenario_library` | 6.8 | 2.0% |
| Shared/stress/factor base | < 5 total | ~1% |

Top three diagnostic blocks (`macro_regime` + `daily_tail_risk` + `portfolio_pca`) = **251.8 s / 343.3 s (73.4%)** of named factory report-block time on 13 succeeded candidates — consistent with [Shared Evidence Session 06](2026-05-23_candidate_factory_shared_evidence_session06_timing_audit.md) (~292 s / ~318 s pattern; snapshot block now separately visible in aggregate).

---

## 3. Bottleneck Diagnosis

| Rank | Bottleneck | Measured cost | Why slow | Required for comparison-critical output? |
| --- | --- | --- | --- | --- |
| 1 | **Lightweight comparison reports × N candidates** | ~410 s (core) / ~853 s (full factory report sum) | Each candidate still runs full diagnostic report pipeline under `lightweight_comparison` profile; weight-dependent portfolio metrics, stress PnL, snapshots recomputed per candidate | **Partially.** Weights, `snapshot_10y`, `stress_report.json` summary fields, and construction disclosure are comparison-critical per [candidate_comparison_spec.md](../specs/candidate_comparison_spec.md). Deep macro/PCA/tail blocks are **not** listed as required checks for `fair_comparison_ready`. |
| 2 | **`macro_regime` (per candidate)** | ~10 s/candidate; 60 s (core) / 134 s (13× full) | Regime label build, indicator panels, regime-factor analytics, CSV-equivalent JSON paths; **repeated per candidate** with no shared macro panel cache | **No** for comparison-critical readiness; **Yes** for health score macro component and optional comparison row fields when present |
| 3 | **`daily_tail_risk` (per candidate)** | ~5–6 s/candidate (core); ~6 s/candidate avg (full) | Daily return panel work for tail metrics; daily panel reused from context but tail computation still runs per candidate | **Partially.** Tail metrics may surface in stress/diagnostic paths; not a core `required_checks` gate |
| 4 | **`snapshots` block (per candidate)** | ~5–6 s/candidate | Snapshot JSON assembly across windows; weight-dependent portfolio metrics | **Yes** — `snapshot_10y.json` is comparison-critical |
| 5 | **`portfolio_pca` (per candidate)** | ~3–4 s/candidate (core); ~3 s/candidate avg (full) | Weekly return download/PCA diagnostics repeated per candidate | **No** for comparison-critical readiness |
| — | **Sequential orchestration** | Entire factory wall clock | 6 or 13 reports run one-after-another; parallel mode not used | N/A (orchestration only) |
| — | **Data loading / cache** | Low in factory after Shared Evidence; ~20 s `factor_betas` on cold `analysis_subject` | First subject run hit factor download; factory reused shared context | Shared monthly/daily/factor paths working |
| — | **Comparison / decision package** | 1.7–2.4 s | Read-only JSON aggregation | Required; already cheap |
| — | **PDF / presentation export** | **0 s** | Disabled by `site_api` | Not required on default path |

**Cause classification (factory phase):**

- **Repeated computation:** dominant — macro_regime, daily_tail_risk, portfolio_pca, snapshots per candidate
- **Unnecessary full-report work (hypothesis):** macro_regime + portfolio_pca on every lightweight candidate may exceed comparison-critical minimum — requires spec-backed defer/skip profile to implement safely
- **Data loading / cache misses:** minor in factory; subject-first factor beta download is one-time per E2E run
- **Sequential orchestration:** full factory wall clock would drop ~48% with 4-worker parallel per [Parallel Session 06 audit](2026-05-22_candidate_factory_parallel_reports_session06_timing_audit.md) — **not re-measured here**

---

## 4. Safe Optimization Plan

### Quick wins (orchestration / cache only — no formula changes)

| Item | Expected effect | Confidence |
| --- | --- | --- |
| **Shared macro panel cache** in `CandidateRunContext` (compute macro_regime inputs once per factory run) | **Hypothesis:** ~10–15% factory report time reduction on full menu (macro is ~39% of named blocks) | Medium — needs implementation + timing re-run |
| **Reuse prepared weekly frames for `portfolio_pca`** (avoid redundant price download/alignment) | **Hypothesis:** ~5–8% on full menu | Medium |
| **Trim `daily_tail_risk` horizons for `lightweight_comparison`** to comparison-critical minimum (likely 10Y-focused) | **Hypothesis:** ~5–10% | Medium — must verify stress/tail fields still present in `stress_report.json` where comparison reads them |
| **Opt-in `--parallel-lightweight-reports`** for full menu | **~48% factory wall-clock** per prior audit | **High** (already measured elsewhere; not re-run here) |
| **Keep default `--mode core`** for routine review | 6 candidates vs 16 — **542 s vs 973 s** measured E2E | High |

### Medium-risk backend refactors (spec / profile work required)

| Item | Notes |
| --- | --- |
| **Defer `macro_regime` + `portfolio_pca` on candidate lightweight profile** | Larger savings; requires explicit `skip_reason` / profile flag in spec + parity tests; health score macro component may need graceful `not_computed` |
| **Staged UI / fast-first response** | Return subject + partial comparison before deep diagnostics complete — product orchestration, not measured here |
| **Batch candidate evaluation API** | Deferred Session 7 in Shared Evidence ExecPlan |

### Do not touch (correctness / contract risk)

- Optimizer mathematics and candidate **weights**
- Stress scenario definitions, pass/fail semantics, and **`run_stress` PnL logic**
- **`snapshot_10y` / `stress_report.json` comparison-critical fields**
- **`candidate_comparison.json` ranking / `fair_comparison_ready` rules**
- Selection, health score, and decision-package **semantics**
- Silent removal of JSON fields from `site_api` contracts

---

## 5. No-Break Rules

All speedups must preserve:

- Financial formulas per `docs/specs/metrics_specification.md` and stress specs
- Optimizer behavior per `docs/specs/portfolio_construction_policy.md`
- Candidate weight generation paths (in-process builders unchanged)
- Comparison contract per `docs/specs/candidate_comparison_spec.md`
- JSON output contracts under `site_api` / `output_manifest.json`
- Explicit diagnostics when a block is deferred — no silent omission

---

## 6. Verification

### Tests run (2026-05-24)

```text
python -m pytest tests/test_report_profile.py tests/test_output_policy.py \
  tests/test_portfolio_review_workflow.py tests/test_candidate_factory.py \
  tests/test_report_timing.py -q --basetemp=tmp/pytest_blocks15_timing_audit
```

**Result:** **80 passed** in ~246 s.

### Parity / output checks (measured run)

| Check | Default core | Full menu reference |
| --- | --- | --- |
| Per-candidate `pdf_seconds` | 0.0 | 0.0 |
| Presentation artifacts absent | Yes | Yes |
| Decision package JSON present + schema | 14/14 | 14/14 |
| Candidate `lightweight_comparison` profile | 6/6 | 13/13 succeeded |
| Required candidate JSON (`snapshot_10y`, `stress_report`, `output_manifest`) | All succeeded | All succeeded |

### Comparison vs prior timing audits

| Baseline | Prior | This audit | Delta |
| --- | ---: | ---: | --- |
| Legacy 16× full report + PDF | ~57 min | — | Not re-run (historical) |
| Standard sequential factory `report_seconds` (16 menu, 13 ok) | 857.7 s (Shared Evidence 2026-05-23) | **853.2 s** | **−0.5%** |
| Standard sequential factory wall (factory only) | 877.1 s | 870.9 s (factory stage only) | ~−0.7% |
| Parallel 16-candidate wall | 631.1 s | **not measured** | — |
| site_api `core_benchmarks` × 2 wall | 171.6 s | **not measured** (different menu) | — |
| Default core E2E (subject + 6 + decision) | **not measured previously** | **542.5 s** | New baseline |

### Unverified areas

- Parallel factory wall clock on current codebase
- Cold-cache (`--no-cache`) E2E timing
- Subprocess-only `run_portfolio_review.py` CLI wall clock vs in-process audit harness
- Metric parity golden diff after any future optimization (required before shipping speedups)
- Full menu 16/16 success (robust suite prerequisites still produce 13/2/1 on isolated roots — same as prior audits)

---

## Re-run

```bash
python scripts/blocks_1_5_e2e_timing_audit.py
```

Expect ~9 min (`default_core` / `core_v1`) + ~16 min (`full_menu_reference`) on warm cache. Gate-only post-wave:

```bash
python scripts/blocks_1_5_e2e_timing_audit.py --skip-legacy
```

Expect ~3.5 min (`core_fast_parallel`) on warm cache with network available.

---

## 6. Post–Performance Wave 2 (`core_fast_parallel`, Session 8, 2026-05-24)

**Wave 2 closure:** `core_fast` E2E **meets** the **≤ 300 s** warm-cache acceptance gate.

| Metric | Session 0 baseline (`core_v1`) | Post-wave (`core_fast_parallel`) | Delta |
| --- | ---: | ---: | ---: |
| **Total wall clock** | 542.5 s | **210.7 s** | **−331.8 s (−61.2%)** |
| `prepare_review_run_context` | — (not measured) | 24.0 s | New stage |
| `analysis_subject` materialization | 114.1 s | **63.1 s** | −51.0 s |
| Candidate factory wall | 426.6 s | **122.8 s** | −303.8 s |
| Comparison + decision package | 1.7 s | 0.8 s | −0.9 s |
| Factory `report_seconds` (aggregate CPU) | 410.7 s | 365.0 s | −45.7 s |
| Per-candidate PDF | 0.0 s | **0.0 s** | — |
| Parallel Phase 2 | No | **Yes** (4 workers) | — |

**Factory aggregate report blocks (6 candidates, post-wave):**

| Block | Seconds | Session 0 (core_v1) |
| --- | ---: | ---: |
| `daily_tail_risk` | 62.2 | 34.7 |
| `snapshots` | 54.9 | 33.2 |
| `portfolio_pca` | 25.9 | 21.7 |
| `scenario_library` | 20.0 | 2.6 |
| `macro_regime` | 12.1 | 60.0 |
| Other | < 11 each | — |

**Acceptance checklist (Session 8):**

| Check | Result |
| --- | --- |
| `core_fast` E2E ≤ 300 s warm cache | **PASS** (210.7 s) |
| Parity bundle (`test_report_profile`, `test_report_timing`, `test_candidate_factory`, `test_candidate_comparison`, `test_portfolio_review_workflow`, `test_candidate_run_context`) | **138 passed** (2026-05-24) |
| `pdf_seconds == 0` | **PASS** |
| Decision package 14/14 JSON + schema | **PASS** |
| `python scripts/verify_docs.py` | **OK** |

**Residual notes (non-blocking):** `analysis_subject` wall **63.1 s** vs internal budget **60 s** (+3.1 s); total E2E still within gate. Harness: `scripts/blocks_1_5_e2e_timing_audit.py` scenario `core_fast_parallel` (or `--skip-legacy` for gate-only). JSON: `tmp/blocks_1_5_timing_audit/core_fast_parallel_summary.json`.
