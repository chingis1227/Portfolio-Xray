# Post-Deep-Audit Foundation & Downstream Readiness Plan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan must be maintained in accordance with [PLANS.md](../../PLANS.md).

## Purpose / Big Picture

Phase 16 made Blocks 1–5 **operationally reliable** for portfolio-first review: strict weight
validation, factory/comparison freshness, resume, optimizer readiness degradation, offline
five-ticker smoke, and trust signals. The **second-level audit** (2026-05-21) found the next risks
are methodological and downstream: selection can rank `degraded` optimizer rows, core vs full menu
confusion, missing live E2E proof, ticker preflight gaps, and Blocks 6–10 consuming comparison
without eligibility guards.

After this plan completes, a new session can resume from repo files only, run core review with
network proof, trust decision artifacts only on **fair-comparison-ready** optimizer rows, and
extend backtest/stress-on-candidates without treating a partial menu as a full optimizer shootout.

**Non-goals:** UI; new optimizer/stress formulas; new constraints; new candidate families.

**Chat rule:** one session = one new chat unless the user explicitly asks for a tiny follow-up in
the same thread. Session 01 is documentation-only. Start Session 02 in a new chat.

**Source audit:** [Blocks 1–5 Deep Audit Snapshot](../audits/2026-05-21_blocks_1_5_deep_audit_snapshot.md).

**Prior wave:** [Blocks 1-5 MVP Core Reliability Plan](2026-05-21_blocks_1_5_mvp_core_reliability_plan.md) (Phase 16, closed).

## Progress

- [x] (2026-05-21) Session 01 (`RM-1020`): ExecPlan persisted; audit snapshot checked in;
  ExecPlan register Active; ROADMAP Phase 17 added; Phase 17 gap index in `KNOWN_ISSUES.md`;
  changelog entry added. No runtime code changed.
- [x] (2026-05-22) Session 02 (`RM-1021`): Live core E2E gate.
- [x] (2026-05-22) Session 03 (`RM-1022`): Selection/health partial menu + degraded guards.
- [x] (2026-05-22) Session 04 (`RM-1023`): Optimizer fairness metadata backfill.
- [x] (2026-05-22) Session 05 (`RM-1024`): Block 1 ticker/universe preflight.
- [x] (2026-05-22) Session 06 (`RM-1025`): Factory vs comparison timestamp semantics.
- [x] (2026-05-22) Session 07 (`RM-1026`): Review bundle disclosure.
- [x] (2026-05-22) Session 08 (`RM-1027`): Blocks 6–7 integration spec + tests.
- [x] (2026-05-22) Session 09 (`RM-1028`): Blocks 8–10 package truthfulness.
- [x] (2026-05-22) Session 10 (`RM-1029`): Live full resume E2E + Phase 17 closure.

## Surprises & Discoveries

- Observation: Phase 16 closed with strong offline proof but without mandatory live factory+compare
  completion in the closure session.
  Evidence: Phase 16 ExecPlan Session 09 outcome; audit P17-G4.

- Observation: `degraded` comparison rows remain eligible in selection and health score modules
  despite Phase 16 degrading optimizer rows for disclosure.
  Evidence: `src/selection_engine.py` `ELIGIBLE_STATUSES`; audit snapshot P17-G1.

- Observation: Same orchestrated review can set `factory_evidence_status: stale` when factory
  JSON is seconds older than comparison `generated_at`.
  Evidence: `Main portfolio/candidate_comparison.json` `candidate_menu` block; audit P17-G6.

## Decision Log

- Decision: Phase 17 follows Phase 16 without reopening formulas or Phase 16 scope.
  Rationale: User audit request was trust, reproducibility, and downstream readiness only.
  Date/Author: 2026-05-21 / Agent.

- Decision: Serial order — Session 03 (selection guards) before Session 04 (optimizer backfill).
  Rationale: Ranking rules must exist before expanding fair-comparison-ready optimizer rows.
  Date/Author: 2026-05-21 / Agent.

- Decision: Live full E2E deferred to Session 10.
  Rationale: Avoid blocking mid-wave sessions on multi-hour factory runs.
  Date/Author: 2026-05-21 / Agent.

- Decision: Session 01 documentation-only; implementation starts Session 02 in a new chat.
  Rationale: User instruction and PLANS.md handoff pattern from Phase 16.
  Date/Author: 2026-05-21 / Agent.

## Outcomes & Retrospective

Session 01 outcome: project memory for Phase 17 is checked in. The audit snapshot, active ExecPlan,
ROADMAP rows `RM-1020`–`RM-1029`, and gap index allow Session 02 to start without prior chat context.
Runtime behavior unchanged.

Session 02 outcome (`RM-1021`): live core acceptance gate documented and implemented.
`src/live_core_e2e.py`, `scripts/verify_live_core_e2e.py`, `tests/test_blocks_1_5_live_core_e2e.py`
(marker, skipped by default), and `tests/test_live_core_e2e_validation.py` (offline). Updated
`TESTING.md`, `docs/operational_runbook.md`, `pytest.ini`, `tests/conftest.py`. Evidence:
`python scripts/verify_live_core_e2e.py --run` exit 0 (~190s); validation OK with
`candidate_menu.review_mode == core`, `factory_profile_id == core_v1`, subject artifacts present;
`factory_evidence_status: stale` warned (P17-G6, Session 06). Offline:
`test_blocks_1_5_mvp_smoke.py` + `test_live_core_e2e_validation.py` **6 passed**;
`pytest tests/test_blocks_1_5_live_core_e2e.py --live-core` **1 passed**; `verify_docs` OK.

Session 03 outcome (`RM-1022`): selection favoring guards and partial-menu warnings.
`src/optimization_readiness.py` (`candidate_eligible_for_favoring`, `favoring_ineligibility_reason`);
`src/selection_engine.py` (degraded and non-fair-ready optimizers excluded from favoring;
`partial_candidate_menu` warning); `src/portfolio_health_score.py` (partial menu + degraded
optimizer diagnostic warnings); `src/decision_package_reporting.py` (client warning labels).
Specs: `selection_engine_spec.md`, `portfolio_health_score_spec.md`. Tests:
`test_selection_engine.py`, `test_portfolio_health_score.py`, `test_optimization_readiness.py`
(**30 passed** in focused bundle).

Session 04 outcome (`RM-1023`): optimizer fairness metadata offline gate and operator rebuild path.
Builders already emit `optimizer_run_metadata` + fingerprints via `portfolio_variants.py`; snapshots
stamp `candidate_config_fingerprint` via `run_portfolio_report_for_weights`. Added
`tests/optimizer_fair_comparison_fixtures.py`, `tests/test_optimizer_fair_comparison_full_menu.py`,
golden `optimization_comparison_full_menu_fair_ready_golden_v1.json` (4 fair-ready optimizers on
synthetic full-menu seed). Runbook §8.6 documents `--no-skip-existing` refresh. Tests:
`test_optimizer_fair_comparison_full_menu.py` **3 passed**; `verify_docs` OK.

Session 06 outcome (`RM-1025`): factory/compare timestamp semantics and CLI ordering.
`run_candidate_factory.py` writes `candidate_factory_run.json` before `--then-compare`;
`run_then_compare` passes in-memory factory doc with `comparison_rebuild_source=factory_then_compare`.
`_assess_factory_run_context` accepts same-review clock skew (standalone: ≤120s with matching
`analysis_end` + fingerprint). Spec/runbook/workflow notes updated. Tests:
`test_factory_then_compare_same_review_context_not_stale_on_seconds_skew`,
`test_standalone_comparison_accepts_timing_skew_within_tolerance`; existing stale-hour test retained.
Focused: `test_candidate_comparison.py` (new tests) + `test_blocks_1_5_mvp_smoke.py`; `verify_docs` OK.

Session 07 outcome (`RM-1026`): review bundle disclosure and mode/subject interpretation.
`src/review_bundle_context.py`; `candidate_comparison.json` includes `review_bundle_context`
(fingerprint, alignment, `mode_subject_consistency`, `user_summary_lines`);
`input_assumptions` adds `review_bundle_disclosure` and merges trust lines. Closed P17-G7/G8.
Specs: `candidate_comparison_spec.md`, `input_assumptions_spec.md`. Tests:
`test_review_bundle_context.py`, comparison contract + sidecar test; `verify_docs` OK.

Session 08 outcome (`RM-1027`): Blocks 6–7 guarded downstream handoff.
`docs/specs/downstream_decision_readiness_spec.md`; `src/downstream_decision_readiness.py`
(backtest fair vs diagnostic, stress_report load guards); `portfolio_health_score.py` and
`robustness_scorecard.py` honor `may_load_candidate_stress_report` for degraded optimizers.
Tests: `test_downstream_decision_readiness.py`, `test_blocks_6_7_downstream_integration.py`;
`verify_docs` OK. Closed P17-G9.

Session 09 outcome (`RM-1028`): Blocks 8–10 package truthfulness.
`src/package_truthfulness.py`; `decision_package_reporting.py` review-scope banner + JSON
`package_truthfulness`; `action_engine.py` partial-menu action warning. Specs:
`decision_package_reporting_spec.md`, `downstream_decision_readiness_spec.md`. Tests:
`test_package_truthfulness.py`, `test_blocks_8_10_downstream_integration.py`,
`test_decision_package_reporting.py` (partial/degraded banner). Closed P17-G2 (package leg),
P17-G10. `verify_docs` OK.

Session 05 outcome (`RM-1024`): Block 1 ticker preflight for explicit `analysis_subject`.
`preflight_explicit_analysis_subject_tickers` in `src/analysis_setup.py` (ETF ∪ stock taxonomy);
called from `_validate_analysis_subject` in `config_schema.py`. Removed stale
`UNKNOWN_TICKER_POLICY` legacy conflict from `build_analysis_setup` validation output. Spec:
`input_assumptions_spec.md` Ticker Validation Policy. Tests: `test_input_assumptions.py` **22 passed**
(including unknown-ticker reject, stock-universe accept, legacy warn-only path); MVP smoke **4 passed**;
`verify_docs` OK.

Session 10 outcome (`RM-1029`): live full + resume E2E gate and Phase 17 closure.
`src/live_full_e2e.py`, `scripts/verify_live_full_e2e.py`, `tests/test_blocks_1_5_live_full_e2e.py`,
`tests/test_live_full_e2e_validation.py`; `pytest.ini`, `tests/conftest.py`, `TESTING.md` Phase 17
closure bundle, `docs/operational_runbook.md` § live full. Live evidence:
`python scripts/verify_live_full_e2e.py --run` OK (~44 min; 16 factory steps, `review_mode: full`,
`factory_evidence_status: current`, `is_partial_menu: false`); `--run --resume-candidates` OK
(~2 min; `resumed_from_manifest: 16`, manifest present). Offline closure bundle **72 passed**;
`verify_docs` OK. Phase 17 **Done**; ExecPlan register Active cleared.

**Phase 17 closure verdict:** Post-deep-audit foundation objectives are **met** under plan scope:
live core/full proof, selection/health/degraded guards, optimizer fairness offline gate, ticker
preflight, factory/compare freshness, review bundle disclosure, Blocks 6–10 guarded consumption and
package truthfulness. Residual accepted: full `default_v1` factory remains operationally heavy
(P17-G11); live gates remain operator/CI optional, not default pytest.

## Context and Orientation

Portfolio X-Ray / Portfolio MRI is a Python, CLI/file-driven decision-support system. The default
workflow is portfolio-first: diagnose `analysis_subject`, then build/compare candidates.

**Blocks 1–5** (foundation):

| Block | Role |
| --- | --- |
| 1 | Input & assumptions — `analysis_subject`, `analysis_setup`, `input_assumptions` |
| 2 | Portfolio X-Ray — `portfolio_xray.json` (7 sections, diagnostic only) |
| 3 | Stress Lab — `stress_report.json` (DIAG suite vs mandate in policy path) |
| 4 | Candidate factory — `candidate_factory_run.json`, profiles `core_v1` / `default_v1` |
| 5 | Optimization engine — candidate builders + readiness disclosure |

**Blocks 6–10** (this plan prepares, does not fully implement): backtest, candidate stress,
comparison (exists), health/robustness, selection/action/package/monitoring.

Key commands:

    python run_portfolio_review.py
    python run_portfolio_review.py --mode full --resume-candidates

Offline gate:

    python -m pytest tests/test_blocks_1_5_mvp_smoke.py -q

## Plan of Work

### Session 01 — Project memory (`RM-1020`) — DONE

Persist this ExecPlan, audit snapshot, registers. Run `python scripts/verify_docs.py`.

### Session 02 — Live core E2E (`RM-1021`)

Add live acceptance checklist or marker test; document in `TESTING.md` and
`docs/operational_runbook.md`. Run live core once; record evidence in Progress.

**Acceptance:** subject + comparison artifacts; `candidate_menu.review_mode == core`; offline smoke
still passes.

### Session 03 — Selection/health guards (`RM-1022`)

Specs + code: favored candidates require `available` and optimizer
`fair_comparison_ready`; `degraded` excluded from favoring; `is_partial_menu` warnings in
selection/health/decision package.

**Files:** `src/selection_engine.py`, `src/portfolio_health_score.py`, selection/health specs,
tests.

### Session 04 — Optimizer fairness backfill (`RM-1023`)

Ensure optimizer builders emit full `optimizer_run_metadata` and snapshot
`config_fingerprint`. Golden/offline test: ≥3 optimizer rows fair-ready after full-menu fixture.

**Files:** `src/portfolio_variants.py`, `run_minimum_*.py`, golden fixtures, runbook.

### Session 05 — Ticker preflight (`RM-1024`)

Reject unknown tickers for explicit `analysis_subject` before report (spec decision).
**Files:** `src/config_schema.py` and/or `src/analysis_setup.py`, `input_assumptions_spec.md`.

### Session 06 — Factory/compare timestamps (`RM-1025`)

Reduce false stale when factory and comparison share review context.
**Files:** `src/candidate_comparison.py`, `src/portfolio_review_workflow.py`, tests.

### Session 07 — Review bundle disclosure (`RM-1026`)

`review_bundle_context_v1` or extended `candidate_menu`; mode/subject mismatch in
`user_summary_lines`.

### Session 08 — Blocks 6–7 (`RM-1027`)

New `docs/specs/downstream_decision_readiness_spec.md`; offline integration test for guarded
backtest/stress-on-candidates path.

### Session 09 — Blocks 8–10 truthfulness (`RM-1028`)

Audit decision chain writers; partial menu + degraded prominent in package summary; extend
offline E2E tests.

### Session 10 — Closure (`RM-1029`)

Live full + resume; Phase 17 Done; register Active → None; closure bundle.

## Concrete Steps

Session 01 steps (completed):

1. Create `docs/exec_plans/2026-05-21_post_deep_audit_foundation_plan.md`.
2. Create `docs/audits/2026-05-21_blocks_1_5_deep_audit_snapshot.md`.
3. Update `docs/exec_plans/README.md`, `docs/audits/README.md`, `docs/ROADMAP.md`, `KNOWN_ISSUES.md`,
   `CHANGELOG.md`.
4. Run:

    python scripts/verify_docs.py

Expected: `docs verification: OK`.

Session 02 starter (next chat):

1. Read this ExecPlan and audit snapshot.
2. Read `TESTING.md` Blocks 1-5 section and `docs/operational_runbook.md`.
3. Implement live core gate per Session 02 acceptance above.

## Validation and Acceptance

**Session 01:**

- Audit snapshot and ExecPlan exist and cross-link.
- `docs/exec_plans/README.md` Active = this plan.
- Phase 17 in `docs/ROADMAP.md` with `RM-1020`–`RM-1029` Pending (except RM-1020 Done).
- `python scripts/verify_docs.py` passes.

**Wave closure (Session 10):**

- Live core and live full (or accepted partial + resume) documented.
- Selection does not favor `degraded` optimizers; partial menu explicit in decision package.
- ≥3 fair-ready optimizer rows after full refresh (maintainer or golden).
- Offline: `test_blocks_1_5_mvp_smoke.py`, portfolio-first E2E, MVP pipeline pass.
- `verify_docs` OK.

## Idempotence and Recovery

Documentation updates are safe to repeat. Code sessions should use focused pytest before broad
runs. Interrupted full factory: `python run_portfolio_review.py --mode full --resume-candidates`.
Do not delete generated folders to force freshness unless the user asks.

## Artifacts and Notes

Audit motivation: Phase 16 fixed operational trust; deep audit found downstream eligibility,
live proof, optimizer fairness on disk, and Block 1 preflight as the next layer.

Phase 17 roadmap IDs: `RM-1020` (Session 01) through `RM-1029` (Session 10).
