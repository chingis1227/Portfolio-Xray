# Candidate Factory Shared Evidence — ExecPlan

This ExecPlan is a living document. Maintain `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` per [PLANS.md](../../PLANS.md).

**Status:** Completed (Sessions 0–6 closed 2026-05-23; Session 7 deferred).

**Constraint (non-negotiable):** orchestration and caching only. Do not change financial formulas, optimizer mathematics, stress scenario definitions, candidate weights, comparison semantics, or `full` vs `lightweight_comparison` output meaning.

**Origin audit:** [docs/audits/2026-05-23_candidate_factory_shared_evidence_audit.md](../audits/2026-05-23_candidate_factory_shared_evidence_audit.md); timing evidence from Session 05/06 audits (~75–107 s/candidate Phase 2 report).

---

## Purpose / Big Picture

After Sessions 1–6, an operator running `python run_candidate_factory.py --profile default_v1 --execution-mode standard` should spend materially less wall-clock time in Phase 2 `lightweight_comparison` reports because invariant evidence (monthly panels, factor matrices, asset metrics, base covariance, asset factor betas) is computed **once per factory run** and reused across all 16 candidates.

The user-visible proof: `candidate_factory_run.json` → `timing_summary.report_seconds` drops (target: **−35% to −55%** sequential vs current ~75 s/candidate baseline on warm cache), while `weights.json`, `snapshot_10y.json` comparison-facing fields, and stress comparison-critical fields remain parity-equivalent to the pre-change baseline (Session 06 matrix).

Parallel mode (`--parallel-lightweight-reports`) stays opt-in; this plan attacks **duplicate work**, not product defaults.

---

## Current State (evidence)

**Already shipped (do not redo):**

- `src/candidate_run_context.py`: monthly panel, daily universe, asset betas 5Y/10Y, recession/scenario factor matrices
- `src/report_profile.py`: `lightweight_comparison` skips rolling/Kalman/regime-analytics HTML, commentary, snapshot_assets
- Parallel Phase 2 reports (completed ExecPlan 2026-05-22)

**Still repeated ×16 per candidate inside `run_portfolio_report_for_weights`:**

- `portfolio_factor_regression_weekly` ×4 + `factor_variance_decomposition_weekly` → `_portfolio_factor_weekly_ols_rows` → `download_all` + `build_factor_matrix`
- Diagnostic extended asset OLS (`run_report.py:741–761`) → `build_factor_matrix` per call
- Asset metrics loop, correlation matrices, `run_stress` → `cov_base`, second `load_daily_asset_returns_shared`, `save_inputs`, scenario library base layer

---

## General Roadmap (post-audit)

| Wave | Theme | Outcome |
| --- | --- | --- |
| **Wave A** (Sessions 0–1) | Measure | Per-block timers prove R1–R3 dominate |
| **Wave B** (Sessions 2–3) | Cache invariants in context | Asset metrics, corr, cov, daily dedup, extended betas |
| **Wave C** (Session 4) | Factor path dedup | Shared weekly R/X; eliminate 16×5 network+factor rebuilds |
| **Wave D** (Session 5) | Stress prepared inputs | Precomputed `r_asset` per scenario + shared `cov_base` |
| **Wave E** (Session 6) | Verify + docs | Timing audit, parity bundle, register closure |
| **Deferred** (Session 7+) | Batch evaluation API | Factory-only fast path; higher risk |

**Not in scope:** changing parallel default, optimizer cores, comparison ranking logic, new candidate families, UI.

---

## Session Order and Chat Boundaries

**Rule:** Start a **new chat** at the beginning of each session below. Carry only: this ExecPlan path, last session's audit/pytest evidence, and open items from `Progress`.

---

### Session 0 — ExecPlan bootstrap and audit formalization

**Goal:** Check in the ExecPlan, formalize the audit as project memory, wire doc pointers. **No runtime code changes.**

**Done when:** `python scripts/verify_docs.py` passes; no code behavior change.

---

### Session 1 — P0 Instrumentation (first implementation session)

**Start new chat when:** Session 0 complete.

**Goal:** Measure where Phase 2 time goes inside `run_portfolio_report_for_weights` before caching changes.

**Tasks:**

1. Add optional `report_timing: dict[str, float]` with named blocks: `save_inputs`, `asset_metrics`, `portfolio_metrics`, `rc_corr`, `factor_betas`, `run_stress`, `factor_regression`, `factor_covariance`, `macro_regime`, `factor_decomposition`, `portfolio_pca`, `scenario_library`, `daily_tail_risk`, `snapshots`, `export_stress`
2. Gate behind env `PORTFOLIO_REPORT_TIMING=1` or factory-only flag (default off)
3. Aggregate into `candidate_factory_run.json` when factory runs
4. Unit test: timing keys present when flag on; absent when off
5. Run 2-candidate smoke and append evidence to ExecPlan `Surprises & Discoveries`

**Files:** `run_report.py`, `src/candidate_factory.py`; new report-timing test module under `tests/` (Session 1)

**Done when:** pytest passes; 2-candidate timing breakdown; no snapshot/stress parity regression.

---

### Session 2 — P1a: Extend CandidateRunContext (invariant metrics and matrices)

**Goal:** Compute once per factory run: asset metrics (all windows), correlation matrices, monthly `cov_base` for stress.

**Files:** `src/candidate_run_context.py`, `run_report.py`, `src/stress.py`, `tests/test_candidate_run_context.py`

---

### Session 3 — P1b: Daily dedup, extended universe betas, lightweight I/O trim

**Goal:** Remove duplicate daily load and redundant extended OLS; trim lightweight-only I/O.

**Files:** `src/candidate_run_context.py`, `run_report.py`, `src/stress_factors.py`

---

### Session 4 — P2: Factor weekly frame dedup (highest ROI)

**Goal:** One shared weekly R and X per window; per candidate only `y = R @ w` and OLS inference.

**Files:** `src/stress_factors.py`, `src/candidate_run_context.py`, `run_report.py`

**Done when:** `factor_regression` block −50%+ vs Session 1 baseline; `test_report_profile.py` parity passes.

---

### Session 5 — P3: Prepared stress synthetic inputs

**Goal:** Precompute per-scenario `r_asset` vectors; candidate stress = dot product + RC/historical legs.

**Files:** `src/stress.py`, `src/candidate_run_context.py`, `run_report.py`; new prepared-stress test module under `tests/` (Session 5)

---

### Session 6 — Verification, timing audit, documentation closure

**Goal:** Prove end-to-end speedup; close ExecPlan; RM-982 Done.

**Verification bundle:**

    python -m pytest tests/test_candidate_factory.py tests/test_candidate_comparison.py \
      tests/test_report_profile.py tests/test_candidate_run_context.py -q
    python scripts/verify_docs.py

(Add Session 1 and Session 5 timing/prepared-stress test modules to the bundle when they exist.)

**Done when:** Sequential 16-candidate report sum improved ≥35% vs Session 06 baseline (1192.9 s) OR documented blocker; comparison-critical parity maintained.

---

### Session 7 — Deferred: Batch candidate evaluation API

Defer until Sessions 1–6 closed and operator still needs sub-10 min sequential runs.

---

## Progress

- [x] (2026-05-23) Session 0: ExecPlan + audit doc + register pointers + spec outline
- [x] (2026-05-23) Session 1: P0 instrumentation — `src/report_timing.py`, `run_report.py` block timers, factory aggregate in `timing_summary.report_timing_aggregate`; pytest `tests/test_report_timing.py` (4 passed); offline 2-candidate smoke (`equal_weight` + `risk_parity`, mocked data, ~18s wall)
- [x] (2026-05-23) Session 2: P1a — `FactoryInvariantMetrics` (asset metrics × windows, correlation matrices, `stress_cov_base`); wired in `run_report.py` / `run_stress(cov_base=...)`; pytest `tests/test_candidate_run_context.py`
- [x] (2026-05-23) Session 3: P1b — extended universe betas + `cash_returns_daily` in factory context; `daily_panel_for_candidate_report` dedup in tail-risk; lightweight skips `save_inputs`; pytest extended
- [x] (2026-05-23) Session 4: P2 — `PortfolioFactorWeeklyFrames` / `build_portfolio_factor_weekly_frames`; factory context v4 preloads weekly R+X once; `run_report.py` passes `shared_frames` to `portfolio_factor_regression_weekly` and `factor_variance_decomposition_weekly`; pytest extended (`tests/test_candidate_run_context.py`, 33 passed in factor/report bundle)
- [x] (2026-05-23) Session 5: P3 prepared stress inputs — `PreparedSyntheticStressInputs`, factory preload in `candidate_run_context_v5`, `run_stress(prepared_synthetic=...)`; pytest `tests/test_prepared_stress.py`
- [x] (2026-05-23) Session 6: Timing audit + docs closure — pytest bundle **106 passed**; `verify_docs` OK; full-menu smoke `report_seconds` 857.7 s vs baseline 1192.9 s (**−28.1%**, below −35% target — documented blocker); [Session 06 timing audit](../audits/2026-05-23_candidate_factory_shared_evidence_session06_timing_audit.md); RM-982 Done (partial timing target).
- [ ] Session 7: Deferred batch API

---

## Surprises & Discoveries

- (2026-05-23) **Session 1 smoke:** Offline factory run for `equal_weight` + `risk_parity` (`execution_mode=standard`, mocked returns/stress) writes per-step `report_timing` and `timing_summary.report_timing_aggregate` with non-empty `report_blocks_seconds_total`. Verification: `python -m pytest tests/test_report_timing.py -q` (4 passed, ~46s wall).
- (2026-05-23) **Instrumentation gap (expected):** Rolling/Kalman/regime-factor work between `factor_regression` and `factor_covariance`, plus OOS/overlay/stress-scenario analytics before `scenario_library`, are not separate buckets in Session 1 — wall time can exceed the sum of named blocks until Session 4+ caching or additional labels.
- (2026-05-23) **Enablement:** Factory Phase 2 passes `enable_report_timing=True`; operators can also set `PORTFOLIO_REPORT_TIMING=1` for non-factory `run_portfolio_report_for_weights` runs.
- (2026-05-23) **Session 2:** `prepare_candidate_run_context` preloads `FactoryInvariantMetrics` (`candidate_run_context_v2`). Phase 2 reports reuse asset metrics and correlation CSVs when `tickers ⊆ universe`; `run_stress` accepts optional precomputed `cov_base`. RC_vol and portfolio metrics remain per candidate.
- (2026-05-23) **Session 3:** `candidate_run_context_v3` precomputes extended-factor asset betas (5Y/10Y) and stores `cash_returns_daily`; Phase 2 reuses factory daily panel for tail-risk (no second `load_daily_asset_returns_shared` when context covers tickers); `lightweight_comparison` skips `save_inputs` CSV copies under `results_csv/inputs/`.
- (2026-05-23) **Session 4:** `candidate_run_context_v4` adds `weekly_factor_frames` (aligned weekly asset returns + factor matrix for 10Y+buffer). Per candidate, portfolio factor regression and variance decomposition only compute `y = R @ w` and OLS inference — no per-candidate `download_all` or `build_factor_matrix` when frames cover tickers. Weekly asset panel uses `asset_weekly_returns_from_daily_returns` on the factory daily panel (same resample as cached asset betas).
- (2026-05-23) **Session 5:** `candidate_run_context_v5` precomputes static `SCENARIOS` per-asset returns (`r_asset_by_scenario`) and stressed covariances once per factory run; `run_stress` reuses them when `prepared_synthetic_stress_usable` (recession_severe still calibrated per candidate). Verification: `python -m pytest tests/test_prepared_stress.py tests/test_candidate_run_context.py -q`.
- (2026-05-23) **Session 6:** Full `default_v1` sequential smoke (`scripts/shared_evidence_session06_timing_smoke.py`, isolated `tmp/candidate_shared_evidence_session06/sequential/`): `report_seconds` **857.7** vs parallel-plan baseline **1192.9** (−28.1%); wall **877.1** s vs **1210.6** s; run status 13/2/1 unchanged; aggregate blocks show near-zero `asset_metrics` / `factor_regression` / `run_stress` vs dominant `macro_regime` + `daily_tail_risk`. Verification bundle **106 passed** + `verify_docs` OK.

---

## Decision Log

- Decision: Split work into 7 bounded sessions (0–6 implement, 7 deferred).
  Rationale: Audit identified distinct risk layers; factor dedup (Session 4) must not ship before instrumentation (Session 1) and context extension (Sessions 2–3).
  Date: 2026-05-23.

- Decision: Keep `run_portfolio_report_for_weights` as the public facade; extend `CandidateRunContext` rather than new parallel report pipeline.
  Rationale: Preserves Main/EW/RP compatibility and existing `test_report_profile` parity contract.
  Date: 2026-05-23.

- Decision: Session 5 (prepared stress) after Session 4 (factor dedup).
  Rationale: Factor frames are prerequisite for consistent asset betas used in `r_asset` precompute.
  Date: 2026-05-23.

- Decision: Close Sessions 0–6 with **documented timing blocker** (−28.1% vs −35% goal); mark RM-982 Done; defer Session 7.
  Rationale: Invariant-cache targets met in aggregate timings; remaining per-candidate macro_regime / tail-risk / PCA dominate; pytest parity bundle green.
  Date: 2026-05-23.

---

## Outcomes & Retrospective

**Shipped:** Sessions 1–5 implementation (report block timing, `FactoryInvariantMetrics`, extended betas + daily dedup + lightweight `save_inputs` skip, weekly factor frame dedup, prepared synthetic stress). Session 6 verification: **106** pytest tests, docs link check, full-menu timing audit.

**Timing:** Sequential `report_seconds` sum improved **28.1%** (857.7 s vs 1192.9 s baseline) on warm network run — **below** the −35% ExecPlan target. Block aggregates confirm R1–R5-style duplication largely removed; **macro_regime**, **daily_tail_risk**, and **portfolio_pca** remain the next optimization frontier (Session 7+ / separate plan).

**Parity:** `test_report_profile` and factory/comparison suites pass; live full-menu comparison to pre-change bytes not attempted in isolated tmp (same caveat as parallel Session 06).

**Deferred:** Session 7 batch candidate evaluation API; optional follow-up for sub-10 min sequential runs without parallel workers.

---

## Handoff Prompts

**Session 1:**

> Implement Session 1 only from `docs/exec_plans/2026-05-23_candidate_factory_shared_evidence_plan.md`. Add report block instrumentation; no formula changes. Run pytest + 2-candidate smoke; update ExecPlan Progress.

**Session 2:**

> Implement Session 2 only from the Shared Evidence ExecPlan. Extend CandidateRunContext with invariant asset metrics, corr, cov_base. Wire run_report.py. Parity tests must pass.
