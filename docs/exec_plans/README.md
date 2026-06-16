# ExecPlan Register

This directory stores implementation plans and historical work plans. Use this register as the
project-memory pointer for plan status. If a chat mentions "the plan", "current plan", or ongoing
plan work without naming a file, start from the single row marked `Active`.

Plans are documentation and workflow guidance only. They do not override `SPEC.md`, `RULES.md`,
`OUTPUTS.md`, `TESTING.md`, detailed specs, current code behavior, formulas, metrics, or generated
artifact contracts.

Portfolio MRI documentation alignment note: completed and historical ExecPlans may contain older
optimizer-first, recommendation, Selection Engine, scorecard, or advanced-module wording. Treat that
wording as planning memory at the time it was written, not as current product direction. Current
product positioning is governed by active canonical docs; current implementation truth remains
governed by `SPEC.md`, `OUTPUTS.md`, detailed specs, and code.

## Status Values

| Status | Meaning |
| --- | --- |
| Active | Current working plan. Resume here by default. |
| Completed | Implemented or closed; retained for history. |
| Historical | Older focused plan retained for traceability. |
| Deferred | Accepted but intentionally paused. |

## Current Pointer

**Active:** [Documentation 9/10 Maintenance Plan](2026-06-16_documentation_9_10_plan.md) - current
documentation cleanup plan. It keeps README short, clarifies owning-document routing, reduces
top-level duplication, and strengthens current-vs-historical boundaries without changing runtime
code, APIs, schemas, formulas, generated outputs, or frontend/backend behavior.

**Paused Active Context:** [Exhaustive QA System](2026-06-14_exhaustive_qa_system_plan.md) -
release-grade QA handoff. Sessions 01-03 delivered the baseline orchestrator, P0 Run Diagnosis
compatibility guard, local exhaustive gate, browser vertical/staging release-readiness hooks,
detailed findings, and `qa-release-readiness.*`. Current release readiness is **not ready** until
the blockers recorded in `KNOWN_ISSUES.md` are fixed, especially `KI-2026-06-14-001`.

**Completed:** [Repair the Builder to Report live review flow](2026-06-16_repair_builder_candidate_comparison_flow.md) -
completed 2026-06-16. Sessions 1-4 repaired backend candidate freshness, Comparison API evidence
transport, frontend Builder controls, downstream state cleanup, and final one-scenario browser
vertical QA through Report.

**Completed:** [Staged Review Pipeline Migration](2026-06-14_staged_review_pipeline_plan.md) -
completed 2026-06-14 and listed as completed history below.

**Deferred:** [Architecture Debt Roadmap for Staged Review Runtime, Frontend State, and Legacy
Runners](2026-06-15_architecture_debt_roadmap_plan.md) - created as a Session 6 handoff from the
Run Diagnostics stabilization work. It splits future architecture cleanup into API/subprocess,
frontend module, and legacy wrapper tracks without changing runtime behavior.

**Completed:** [Source-of-Truth Reconciliation Plan](2026-06-13_source_of_truth_reconciliation_plan.md) - completed 2026-06-13. Sessions 1-3 aligned AGENTS.md, root source-of-truth docs, runtime documentation, Client Fit status, product-bundle discovery, manifest/hygiene behavior, focused tests, and final verification around the implemented diagnosis-first/current-portfolio-first product.

**Completed:** [Current Frontend Design Documentation Synchronization](2026-06-13_current_frontend_design_docs_sync_plan.md) - 2026-06-13 docs/code sync that made the implemented frontend the source of truth for design tokens, route structure, landing/onboarding flow, 8-step platform shell, and local-only dev bypass.

**Previous Active:** [FastAPI Foundation and Contract-First Frontend Migration](2026-06-11_fastapi_foundation_plan.md) - current project-level plan for replacing the local Next.js-to-Python bridge with a FastAPI/OpenAPI/Pydantic/TypeScript contract foundation. Sessions 00-09 are complete; the next chat should begin with Session 10 (final acceptance, browser QA, and handoff).

**Previous Focused UI Plan:** [Landing and Onboarding Before Portfolio Input](2026-06-12_frontend_landing_onboarding_plan.md) - scoped frontend entry-experience plan that adds a public landing page, required email sign-in, onboarding, and a loading handoff before the existing Portfolio Input flow. It does not change Python analytics, FastAPI contracts, generated artifacts, or backend behavior.

**Completed:** [Dynamic Diagnosis Interpretation Foundation](2026-06-11_diagnosis_interpretation_foundation_plan.md) - Sessions 00-16 closed 2026-06-12. Final acceptance evidence is the live FastAPI + frontend vertical QA report `output/playwright/vertical-qa-2026-06-12T08-12-35-071Z/qa-report.json`, proving three distinct evidence-backed diagnosis flows, source-artifact-backed public claims, and stale selected-card rejection.

**Previous Active:** [Vertical Integration Post-Audit Hardening Plan](2026-06-08_vertical_integration_post_audit_hardening_plan.md) - prior frontend/backend vertical hardening plan after the 2026-06-08 full project audit. Keep as current-readiness context while the FastAPI foundation plan becomes the active architectural migration.

**Previous Active:** [Full Demo MVP Readiness Audit and Hardening](2026-06-05_full_demo_mvp_readiness_audit_and_hardening_plan.md) - prior readiness hardening plan. Keep as historical/current-readiness context.

**Completed:** [Blocks 5-9 Vertical Product Loop](2026-06-05_blocks_5_9_vertical_product_loop_plan.md) - Sessions 00-10 closed 2026-06-05. Live acceptance produced the required chain: `problem_classification.json`, `candidate_launchpad.json`, `portfolio_alternatives_builder.json`, `candidate_generation.json`, `current_vs_candidate.json`, `decision_verdict.json`, and `ai_commentary_context.json`. Final status: `BLOCK_6_READY BLOCK_7_READY BLOCK_8_READY BLOCK_9_READY READY_FOR_PRODUCT_DEMO`.

**Previous Active:** [Blocks 3-5 Product Handoff Integration Readiness Audit Plan](2026-06-04_blocks_3_5_integration_readiness_audit_plan.md) - unified 2026-06-04 around the canonical read-only audit question: Stress evidence -> Investment diagnosis -> Testable Launchpad card -> Builder prefill. Supporting evidence from the earlier one-candidate readiness plan and the Block 4 -> Builder handoff plan has been merged into the active plan.

**Completed:** [Block 4 v3 Investment Diagnosis Plan](2026-06-04_block_4_v3_investment_diagnosis_plan.md) ... implemented diagnosis-first v3 (`problem_classification_v3`, `candidate_launchpad_v3`), root-cause over symptoms, mixed evidence as no-action/note rather than normal primary verdict, and launchpad cards with success criteria. Closed 2026-06-04.

**Completed:** [Block 4 v2 Evidence-to-Problem Translation](2026-05-29_block_4_v2_evidence_to_problem_plan.md) - Sessions 00-14 closed 2026-05-29. Evidence: [Session 14 institutional closure](../audits/2026-05-29_block_4_v2_session_14_institutional_closure.md); pytest **109 passed** (closure bundle); decision `DEC-2026-05-29-013`.

**Previous (Phase A closed):** [Blocks 1-3 Post-Audit Development Plan](2026-05-29_blocks_1_3_post_audit_development_plan.md) - Phase A **closed** 2026-05-29 (Session 06); optional 07-08; Phase D Sessions 09-10 closed. Closure: [foundation closure audit](../audits/2026-05-29_blocks_1_3_foundation_closure_audit.md) (`READY_FOR_DECISION_WORKFLOW`). Operator contract: [runtime_artifact_contract.md](../runtime_artifact_contract.md).

**Previous closure:** Block 3.4 institutional upgrade **Completed** 2026-05-29.

**Most recent closure:** [Block 3.4 Current Portfolio Stress Scorecard Institutional Upgrade](2026-05-29_block_3_4_current_portfolio_stress_scorecard_institutional_upgrade_plan.md) (2026-05-29): v1.1 contract, `stress_diagnosis`, downstream v1-primary, live-output gates; pytest **67** (closure) / **142** (extended); fixture matrix **7/7**; evidence: [institutional upgrade acceptance audit](../audits/2026-05-29_block_3_4_institutional_upgrade_acceptance_audit.md).

**Previous closure:** [Block 3.3 Hedge Gap Analysis Institutional Upgrade](2026-05-29_block_3_3_hedge_gap_institutional_upgrade_plan.md) (2026-05-29): v1.1 contract, `hedge_gap_rules_v1_2` scoring, 2.4/2.6 bridges, v1-primary downstream; pytest **106 passed**; evidence: [institutional upgrade acceptance audit](../audits/2026-05-29_block_3_3_institutional_upgrade_acceptance_audit.md).

**Previous closure:** [Block 2.6 Portfolio Weakness Map heuristic_v2](2026-05-29_block_2_6_weakness_map_heuristic_v2_plan.md) (2026-05-29): `heuristic_v2`, eight canonical Stress Lab risk ids, narrative + stress boundary + downstream SSOT; pytest **68 passed**; evidence: [heuristic_v2 acceptance audit](../audits/2026-05-29_block_2_6_weakness_map_heuristic_v2_acceptance_audit.md).

**Previous closure:** [Final Architecture Consistency Audit Plan](final_architecture_consistency_audit_plan.md) (2026-05-27): Sessions 1-7 closed - diagnosis-only default aligned in docs/runbook, product-bundle clarity, AI grounding audit, `tests/test_architecture_consistency.py`, Session 7 live validation PASS.

Previous closure: [Core MVP Runtime Integration and Entrypoint Audit Plan](core_mvp_runtime_integration_and_entrypoint_audit_plan.md) (Sessions 1-7, closed 2026-05-27). Evidence: diagnosis-only default dry-run + one-candidate dry-run; boundary pytest bundle **25 passed**; live canonical E2E in `tmp/session07_live/Main portfolio/analysis_subject` (Blocks 2.1-2.6 + 3.1-3.4 present, no candidate zoo by default).

Previous closure: [Block 3.4 Current Portfolio Stress Scorecard MVP](2026-05-27_block_3_4_current_portfolio_stress_scorecard_plan.md) (product block `current_portfolio_stress_scorecard_v1` on subject `stress_report.json`; closed 2026-05-27). Evidence: [acceptance audit](../audits/2026-05-27_block_3_4_current_portfolio_stress_scorecard_acceptance_audit.md); Block 3.4 pytest bundle passed (including `tests/test_current_portfolio_stress_scorecard_v1_contract.py`); live subject stress_report with populated Block 3.4.

Previous closure: [Block 2.6 Portfolio Weakness Map MVP](2026-05-26_block_2_6_portfolio_weakness_map_plan.md) (product block `block_2_6_portfolio_weakness_map`; closed 2026-05-26). Evidence: [acceptance audit](../audits/2026-05-26_block_2_6_portfolio_weakness_map_acceptance_audit.md); closure pytest **35 passed**; live nine risk types on subject X-Ray (`rates_up` 65 Medium).

Previous closure: [Block 2.5 Risk Budget View MVP](2026-05-26_block_2_5_risk_budget_view_plan.md) (product block `block_2_5_risk_budget_view`; closed 2026-05-26). Evidence: [acceptance audit](../audits/2026-05-26_block_2_5_risk_budget_acceptance_audit.md); closure pytest **44 passed**; live `run_portfolio_review.py` on root `config.yml` with 8-ticker weight/RC/gap table.

Previous closure: [Block 2.4 Institutional Upgrade](2026-05-29_block_2_4_institutional_upgrade_plan.md) (Sessions 01-13, `heuristic_v2`; closed 2026-05-29). Evidence: [Session 13 audit](../audits/2026-05-29_block_2_4_session_13_institutional_closure.md); matrix [v2 signoff](../audits/2026-05-29_block_2_4_completion_matrix_v2_signoff.md); pytest **140 passed**.

Previous closure: [Block 2.4 Hidden Exposure / Hidden Risk Detector MVP](2026-05-26_block_2_4_hidden_exposure_plan.md) (six-alert product block `block_2_4_hidden_exposure`; closed 2026-05-26). Evidence: focused pytest **62 passed** on closure bundle; live `run_portfolio_review.py --candidates equal_weight` with Block 2.4 on subject X-Ray.

Previous closure: [Block 2.3 Factor Exposure / Factor Sensitivity MVP](2026-05-26_block_2_3_factor_exposure_plan.md) (adapter-only product block over `stress_report` factor diagnostics; closed 2026-05-26). Evidence: live diagnosis + one-candidate + `validate_one_candidate_demo.py` PASS; focused pytest bundles **9 + 6 + 56 + 46 + 31 passed**; docs verification OK.

Previous closure: [Block 2.2 Portfolio Metrics / Risk Diagnostics MVP](2026-05-26_block_2_2_portfolio_metrics_plan.md) (Sessions 01.........08, 2026-05-26). Evidence: [Block 2.2 acceptance audit](../audits/2026-05-26_block_2_2_portfolio_metrics_acceptance_audit.md); live diagnosis + one-candidate + `validate_one_candidate_demo.py` PASS; pytest closure bundle **48 passed**; bundle/runtime regression **16 passed**.

Previous closure: [Block 2.1 Asset Allocation MVP](2026-05-26_block_2_1_asset_allocation_plan.md) (Sessions 01-08, 2026-05-26). Evidence: [Block 2.1 acceptance audit](../audits/2026-05-26_block_2_1_asset_allocation_acceptance_audit.md); pytest closure bundle **44 passed**.

Previous closure: [Input Layer MVP Migration](2026-05-26_input_layer_mvp_migration.md) (Sessions 01-10, 2026-05-26). Evidence: [Input Layer MVP acceptance audit](../audits/2026-05-26_input_layer_mvp_acceptance_audit.md); pytest **36 passed**; dry-run + materialize + `validate_one_candidate_demo.py` PASS.

Previous closure: [Product Flow MVP Backend Plan](2026-05-25_product_flow_mvp_backend_plan.md) (Sessions 01-08, 2026-05-26). Origin audit: [Product-Flow Validation Audit](../audits/2026-05-25_product_flow_validation_audit.md) (Session 08 closure). Evidence: offline bundle gate + `RM-ARCH-011` Done; live [demo baseline snapshot](../audits/2026-05-25_product_flow_demo_baseline_snapshot.md); pytest **46 passed** (Session 08). Deferred: Session 09 / `RM-ARCH-010` LLM.

Previous closure: [Post-Audit Portfolio MRI Architecture Alignment Roadmap](2026-05-25_post_architecture_alignment_roadmap.md) (Sessions 01-12, 2026-05-25). Evidence: [Session 12 closure report](../audits/2026-05-25_post_architecture_alignment_session12_closure_report.md).

Previous closure: [Blocks 1-5 Performance Wave 2 (core_fast <= 5 min)](2026-05-24_blocks_1_5_performance_wave2_plan.md) (Sessions 0-8, 2026-05-24; `RM-983` **Done**). Session 8 gate: **`core_fast` E2E 210.7 s** (target <= 300 s). Evidence: [E2E timing audit Section6](../audits/2026-05-24_blocks_1_5_e2e_timing_audit.md).

Previous closure: [Core / Full Artifact and Documentation Confusion Remediation](2026-05-23_core_full_artifact_documentation_confusion_plan.md) (Sessions 00-06, 2026-05-24). Origin audit: [Core/full confusion audit](../audits/2026-05-23_core_full_artifact_documentation_confusion_audit.md).

Earlier: [Site/API Default Output Refactor](2026-05-23_site_api_default_output_refactor_plan.md) (Sessions 0-7, 2026-05-23).

Completed (2026-05-22): [Candidate Factory Parallel Lightweight Reports](2026-05-22_candidate_factory_parallel_reports_plan.md)
(Sessions 0-6 closed: opt-in parallel Phase 2 lightweight reports, fallback disclosure, operator docs,
Session 5 two-candidate timing audit, Session 6 full `default_v1` timing audit; **parallel remains opt-in**.)

Completed (2026-05-22): [Demo MVP Reliability Repair](2026-05-22_demo_mvp_reliability_plan.md)
(artifact-based proof for the 8-ticker core demo path; multi-factor stress attribution restored when
network factor proxies are available; generated-output QA passed).

Completed (2026-05-22): [Candidate Factory Runtime Refactor Plan](2026-05-22_candidate_factory_runtime_refactor_plan.md)
(Sessions 0-9; phased factory `standard` + timing baseline audit; handoff:
[Candidate Factory Timing Baseline](../audits/2026-05-22_candidate_factory_timing_baseline.md)).

Completed (2026-05-22): [Post-Deep-Audit Foundation & Downstream Readiness Plan](2026-05-21_post_deep_audit_foundation_plan.md)
(Sessions 01-10; Phase 17 `RM-1020`-`RM-1029` Done). Handoff: live core/full E2E gates,
selection/health/degraded guards, optimizer fairness offline gate, review bundle disclosure,
downstream readiness + package truthfulness; closure bundle **72 passed**; live full + resume
documented in Session 10.

Completed (2026-05-21): [Blocks 1-5 MVP Core Reliability Plan](2026-05-21_blocks_1_5_mvp_core_reliability_plan.md)
(Sessions 01-09; Phase 16 `RM-1010`-`RM-1018` Done). Handoff: hardened `analysis_subject` weight
validation, factory/comparison freshness, `--resume-candidates`, optimizer readiness degradation,
five-ticker offline smoke, data-trust signals, root docs/runbook, offline bundle **125 passed**.

Completed (2026-05-21): [Optimization Engine Post-Audit Roadmap](2026-05-20_optimization_engine_post_audit_roadmap.md)
(Sessions 00-12; Phase 15 `RM-990`-`RM-1002` Done). Handoff:
[Optimization Engine Methodology Map](../audits/2026-05-20_optimization_engine_methodology_map.md),
[Optimization Engine Baseline Snapshot](../audits/2026-05-20_optimization_engine_baseline_snapshot.md).

Completed (2026-05-20): [Candidate Portfolio Factory Post-Audit Roadmap](2026-05-20_candidate_factory_post_audit_roadmap.md)
(Sessions 00-11; Phase 14 `RM-970`-`RM-981` Done). Handoff:
[Candidate Factory Methodology Map](../audits/2026-05-20_candidate_factory_methodology_map.md),
[Candidate Factory Baseline Snapshot](../audits/2026-05-20_candidate_factory_baseline_snapshot.md).

Deferred post-wave: UI `RM-500+`; new `candidate_id` families only via spec + DEC (see DEC-2026-05-20-003 appendix).

Completed (2026-05-20): [Portfolio X-Ray Post-Audit Roadmap](2026-05-20_portfolio_xray_post_audit_roadmap.md)
(Sessions 00-10; baseline in
[Portfolio X-Ray Baseline Snapshot](../audits/2026-05-20_portfolio_xray_baseline_snapshot.md);
methodology map in
[Portfolio X-Ray Methodology Map](../audits/2026-05-20_portfolio_xray_methodology_map.md)).

Completed (2026-05-20): [Stress Lab Methodology Governance Plan](2026-05-20_stress_lab_methodology_governance_plan.md)
(Sessions 00-11; methodology map in
[Stress Lab Methodology Map](../audits/2026-05-20_stress_lab_methodology_map.md); baseline in
[Stress Lab Baseline Snapshot](../audits/2026-05-20_stress_lab_baseline_snapshot.md); Phase 13 `RM-951`-`RM-961` Done).

Completed (2026-05-20): [Stress Lab Post-Audit Roadmap](2026-05-20_stress_lab_post_audit_roadmap.md)
(Sessions 00-10; baseline in [Stress Lab Baseline Snapshot](../audits/2026-05-20_stress_lab_baseline_snapshot.md)).

Completed: [Portfolio X-Ray Diagnostics Deepening Plan](2026-05-19_portfolio_xray_diagnostics_deepening_plan.md)
(Sessions 00-09, `RM-930`-`RM-939`, closed 2026-05-20).

Completed: [Post-Portfolio-First Stabilization Plan](2026-05-19_post_portfolio_first_stabilization_plan.md)
(Sessions 00-11, `RM-900`-`RM-911`, closed 2026-05-19).

Completed: [Portfolio-First Transition Plan](2026-05-18_portfolio_first_transition_plan.md) (Sessions 01-09, closed 2026-05-18).

Completed: [Post-Audit MVP Stabilization Plan](2026-05-17_post_audit_mvp_stabilization_plan.md) (Sessions 01-11, `RM-710`, closed 2026-05-18).

Also completed: [Post-Audit Stabilization And Analytics Plan](2026-05-17_post_audit_stabilization_and_analytics_plan.md) (Sessions 02-20, `RM-623`).

Parallel or deferred backlog remains in [ROADMAP](../ROADMAP.md) (e.g. UI `RM-500+`).

## Major Plan History

| Date | Plan | Status | Origin audit | Current handoff |
| --- | --- | --- | --- | --- |
| 2026-06-16 | [Repair the Builder to Report live review flow](2026-06-16_repair_builder_candidate_comparison_flow.md) | **Completed** | User-requested repair of the live Builder -> Candidate -> Comparison -> Verdict -> Report path | Sessions 1-4 closed: live candidate generation forces fresh one-candidate factory evidence, stale/unavailable comparison rows are rejected, FastAPI Comparison returns `current_vs_candidate` display dimensions, `/hypothesis` exposes V1 Builder setup controls and clears downstream state on setup changes, and browser vertical QA passed through Report with stale-card 409 proof. |
| 2026-06-15 | [Architecture Debt Roadmap for Staged Review Runtime, Frontend State, and Legacy Runners](2026-06-15_architecture_debt_roadmap_plan.md) | Deferred | Session 6 of the Run Diagnostics stabilization plan | Future work is split into three safe tracks: replace staged API subprocess boundaries with direct service calls where proven, extract low-risk seams from `frontend/lib/server/fastapiBridge.ts` and `frontend/lib/reviewState.tsx`, and define root legacy wrapper retirement criteria. |
| 2026-06-14 | [Exhaustive QA System](2026-06-14_exhaustive_qa_system_plan.md) | **Active** | User-requested permanent maximum QA system after observing `Run Diagnosis` fail on the working site | Sessions 01-03 delivered: baseline `qa_exhaustive` orchestrator, P0 frontend/backend staged endpoint compatibility guard, full local exhaustive gate, browser vertical/staging release-readiness hooks, detailed findings, and release-readiness files. Current release status is not ready because blockers such as `KI-2026-06-14-001` remain. |
| 2026-06-14 | [Staged Review Pipeline Migration](2026-06-14_staged_review_pipeline_plan.md) | **Completed** | User-approved architecture remediation for long synchronous diagnosis, CLI/file-driven backend gap, run-local artifact truth risk, Supabase/privacy boundary, and frontend partial-result UX | Sessions 1-7 closed: `review_state_v1`, staged FastAPI start/status, diagnosis and downstream stage synchronization, deterministic Demo / QA fixtures, frontend polling/refresh recovery, compact Supabase persistence, and one-scenario vertical QA PASS. |
| 2026-06-13 | [Source-of-Truth Reconciliation Plan](2026-06-13_source_of_truth_reconciliation_plan.md) | **Completed** | [Current State Source-of-Truth Alignment Audit](../audits/2026-06-13_current_state_source_of_truth_alignment_audit.md) | Sessions 1-3 closed 2026-06-13: root truth reset, obsolete root historical file removal, contract/runtime alignment, product-bundle/manifest acceptance, and final verification. |
| 2026-06-11 | [Dynamic Diagnosis Interpretation Foundation](2026-06-11_diagnosis_interpretation_foundation_plan.md) | **Completed** | [Session 00 diagnosis interpretation baseline audit](../audits/2026-06-11_diagnosis_interpretation_session00_audit.md) | Sessions 00-16 closed 2026-06-12: deterministic evidence-to-diagnosis rulebook foundation, additive Block 4 interpretation chain, site/FastAPI/frontend display envelopes, source/provenance governance, multi-user lineage rejection, fixture matrix, and live vertical QA acceptance. Closure: [Session 16 closure](../audits/2026-06-12_diagnosis_interpretation_session16_closure.md). |
| 2026-06-08 | [Vertical Integration Post-Audit Hardening Plan](2026-06-08_vertical_integration_post_audit_hardening_plan.md) | Previous Active | [2026-06-08 vertical integration full project audit](../audits/2026-06-08_vertical_integration_full_project_audit.md) | Sessions 00-02 complete: plan registered, Builder prepare frontend/API handoff implemented, and operator docs synced. Superseded as active pointer by the staged review pipeline migration. |
| 2026-06-05 | [Full Demo MVP Readiness Audit and Hardening](2026-06-05_full_demo_mvp_readiness_audit_and_hardening_plan.md) | Previous Active | User-requested full demo MVP readiness audit and hardening plan after Blocks 5-9 vertical loop validation | Session 00 complete: plan created and registered; baseline dirty tree, existing vertical output chain, and FRED/factor runtime risk recorded. Next: Session 01 product-critical test inventory and smoke baseline. |
| 2026-06-05 | [Blocks 5-9 Vertical Product Loop](2026-06-05_blocks_5_9_vertical_product_loop_plan.md) | **Completed** | Product-loop implementation plan for `Diagnosis -> Hypothesis -> Candidate -> Comparison -> Verdict` | Sessions 00-10 closed 2026-06-05: one selected hypothesis/candidate path, Block 7 `candidate_generation_v1`, Block 8 scoped comparison, direct Block 9 verdict, AI grounding, live vertical demo PASS; final status `READY_FOR_PRODUCT_DEMO`. |
| 2026-05-29 | [Block 4 v2 Evidence-to-Problem Translation](2026-05-29_block_4_v2_evidence_to_problem_plan.md) | **Completed** | [Session 00 gap audit](../audits/2026-05-29_block_4_v2_session_00_gap_audit.md) | Sessions 00-14 closed; [Session 14 closure](../audits/2026-05-29_block_4_v2_session_14_institutional_closure.md); pytest **109 passed**. |
| 2026-05-29 | [Block 3.4 Current Portfolio Stress Scorecard Institutional Upgrade](2026-05-29_block_3_4_current_portfolio_stress_scorecard_institutional_upgrade_plan.md) | **Completed** | [Session 00 baseline](../audits/2026-05-29_block_3_4_session_00_baseline_audit.md); MVP prerequisite | Sessions 00-13 closed 2026-05-29: Phase 2 **ACCEPTED**; G1-G15 closed; pytest **142 passed** (extended); [acceptance audit](../audits/2026-05-29_block_3_4_institutional_upgrade_acceptance_audit.md). |
| 2026-05-28 | [Core MVP Historical Stress Replay](2026-05-28_core_mvp_historical_stress_replay_plan.md) | **Completed** | Stress Lab honest coverage for young books / partial history | Sessions 1-7 closed 2026-05-28: `historical_stress_replay_v1` direct-only; [acceptance audit](../audits/2026-05-28_core_mvp_historical_stress_replay_acceptance_audit.md); pytest **35 passed**; `scripts/verify_core_mvp_historical_stress_replay.py`. |
| 2026-05-27 | [Final Architecture Consistency Audit Plan](final_architecture_consistency_audit_plan.md) | **Completed** | Read-only architecture discrepancy map (2026-05-27) | Sessions 1-7 closed 2026-05-27: runbook/runtime alignment, JSON bundle rules, AI grounding, legacy labels, `test_architecture_consistency.py`, Session 7 acceptance (diagnosis + one-candidate demo PASS). |
| 2026-05-27 | [Core MVP Runtime Integration and Entrypoint Audit Plan](core_mvp_runtime_integration_and_entrypoint_audit_plan.md) | **Completed** | Runtime entrypoint confusion + factor/stress boundary audit | Sessions 1-7 closed 2026-05-27; diagnosis-only default + boundary pytest bundle **25 passed**. |
| 2026-05-27 | [Block 3.4 Current Portfolio Stress Scorecard MVP](2026-05-27_block_3_4_current_portfolio_stress_scorecard_plan.md) | **Completed** | Block 3.3 prerequisite; Stress Lab product brief Section3.4 | Sessions 00-06 closed 2026-05-27: `current_portfolio_stress_scorecard_v1` on subject `stress_report.json` summarizing Blocks 3.1-3.3; [acceptance audit](../audits/2026-05-27_block_3_4_current_portfolio_stress_scorecard_acceptance_audit.md); targeted pytest bundle (including `tests/test_current_portfolio_stress_scorecard_v1_contract.py`) and docs verification passed; live portfolio-first run with populated Block 3.4. |
| 2026-05-29 | [Block 3.3 Hedge Gap Analysis Institutional Upgrade](2026-05-29_block_3_3_hedge_gap_institutional_upgrade_plan.md) | **Completed** | [Session 00 baseline](../audits/2026-05-29_block_3_3_session_00_baseline_audit.md); MVP prerequisite | Sessions 01-12 closed 2026-05-29: v1.1 contract, `hedge_gap_rules_v1_2`, 2.4/2.6 bridges, v1-primary downstream; [acceptance audit](../audits/2026-05-29_block_3_3_institutional_upgrade_acceptance_audit.md); pytest **106 passed**. |
| 2026-05-27 | [Block 3.3 Hedge Gap Analysis MVP](2026-05-27_block_3_3_hedge_gap_analysis_plan.md) | **Completed** | Block 3.2 prerequisite; product brief Section3.3 | Sessions 00-08 closed 2026-05-27: `hedge_gap_analysis_v1` on subject `stress_report.json`; offset coverage MVP; [acceptance audit](../audits/2026-05-27_block_3_3_hedge_gap_acceptance_audit.md); superseded for product depth by institutional upgrade (2026-05-29). |
| 2026-05-27 | [Block 3.2 Stress Results MVP](2026-05-27_block_3_2_stress_results_plan.md) | **Completed** | Block 3.1 prerequisite; Stress Lab product brief Section3.2 | Sessions 00-08 closed 2026-05-27: `stress_results_v1` on subject `stress_report.json`; `stress_conclusions` preserved; [acceptance audit](../audits/2026-05-27_block_3_2_stress_results_acceptance_audit.md); pytest **75 passed**; live worst synthetic `recession_severe` / historical `2022`. |
| 2026-05-29 | [Block 2.6 Portfolio Weakness Map heuristic_v2](2026-05-29_block_2_6_weakness_map_heuristic_v2_plan.md) | **Completed** | v1 MVP + Stress Lab ID alignment + institutional scoring/narrative | Sessions 00-09 closed 2026-05-29: eight canonical risks, `heuristic_v2`; [acceptance audit](../audits/2026-05-29_block_2_6_weakness_map_heuristic_v2_acceptance_audit.md); pytest **68 passed**. |
| 2026-05-26 | [Block 2.6 Portfolio Weakness Map MVP](2026-05-26_block_2_6_portfolio_weakness_map_plan.md) | **Completed** | User brief Block 2.6 (9 risk types, rule-based scoring over Blocks 2.1-2.5; no mini Stress Lab) | Sessions 00-08 closed 2026-05-26: `block_2_6_portfolio_weakness_map` on portfolio-first X-Ray; [acceptance audit](../audits/2026-05-26_block_2_6_portfolio_weakness_map_acceptance_audit.md); pytest **35 passed**; live nine risk types. Superseded for product contract by heuristic_v2 plan (2026-05-29). |
| 2026-05-26 | [Block 2.5 Risk Budget View MVP](2026-05-26_block_2_5_risk_budget_view_plan.md) | **Completed** | User brief Block 2.5 (weight vs RC, buckets; no stress PnL); Blocks 2.1-2.4 prerequisite | Sessions 00-08 closed 2026-05-26: `block_2_5_risk_budget_view` on portfolio-first X-Ray; [acceptance audit](../audits/2026-05-26_block_2_5_risk_budget_acceptance_audit.md); pytest **44 passed**; live demo 8 tickers. |
| 2026-05-29 | [Block 2.4 Institutional Upgrade](2026-05-29_block_2_4_institutional_upgrade_plan.md) | **Completed** | [Session 00 baseline audit](../audits/2026-05-29_block_2_4_session_00_baseline_audit.md) | Sessions 01-13 closed 2026-05-29: `heuristic_v2`, confidence v2, matrix sign-off, Core MVP validator, live gate; [Session 13 audit](../audits/2026-05-29_block_2_4_session_13_institutional_closure.md); pytest **140 passed**. |
| 2026-05-26 | [Block 2.4 Hidden Exposure / Hidden Risk Detector MVP](2026-05-26_block_2_4_hidden_exposure_plan.md) | **Completed** | Product brief Block 2.4 | `block_2_4_hidden_exposure` on portfolio-first X-Ray; legacy `sections.hidden_risk_detector` preserved; closure pytest **62 passed**. |
| 2026-05-26 | [Block 2.3 Factor Exposure / Factor Sensitivity MVP](2026-05-26_block_2_3_factor_exposure_plan.md) | **Completed** | Product brief Block 2.3; Block 2.1/2.2 prerequisites | Adapter-only architecture (`DEC-2026-05-26-004`): top-level `block_2_3_factor_exposure` on portfolio-first X-Ray; missing fields degrade and are fixed upstream in `stress_report` generation; live diagnosis + one-candidate PASS; focused pytest bundles **9 + 6 + 56 + 46 + 31 passed**. |
| 2026-05-26 | [Block 2.2 Portfolio Metrics / Risk Diagnostics MVP](2026-05-26_block_2_2_portfolio_metrics_plan.md) | **Completed** | Product brief Block 2.2; Block 2.1 prerequisite | Sessions 01-08 closed 2026-05-26: `block_2_2_portfolio_metrics` on portfolio-first X-Ray; live demo + real-cash fixture; [acceptance audit](../audits/2026-05-26_block_2_2_portfolio_metrics_acceptance_audit.md); pytest **48+16 passed**. |
| 2026-05-26 | [Block 2.1 Asset Allocation MVP](2026-05-26_block_2_1_asset_allocation_plan.md) | **Completed** | Portfolio X-Ray Section2.1 product brief; Session 01 code/doc audit | Sessions 01-08 closed 2026-05-26: `block_2_1_asset_allocation` on portfolio-first X-Ray; live demo + fixture real-cash proof; [acceptance audit](../audits/2026-05-26_block_2_1_asset_allocation_acceptance_audit.md); pytest **44 passed**. |
| 2026-05-26 | [Input Layer MVP Migration](2026-05-26_input_layer_mvp_migration.md) | **Completed** (contract **frozen**) | User Input Layer redesign brief | Sessions 01-10 closed; live one-candidate PASS (audit Section5); `DEC-2026-05-26-001`; no input redesign unless bug. Next: Blocks 2-5 / product-flow layers. |
| 2026-05-25 | [Product Flow MVP Backend Plan](2026-05-25_product_flow_mvp_backend_plan.md) | **Completed** | [Product-Flow Validation Audit](../audits/2026-05-25_product_flow_validation_audit.md) | Sessions 01-08 closed 2026-05-26: demo-ready MVP backend (offline gate, `RM-ARCH-011` Done, operator guide, live bundle snapshot, audit closure). Session 09 / `RM-ARCH-010` deferred. |
| 2026-05-25 | [Post-Audit Portfolio MRI Architecture Alignment Roadmap](2026-05-25_post_architecture_alignment_roadmap.md) | **Completed** | [Full Project Architecture Alignment Audit](../audits/2026-05-25_full_project_architecture_alignment_audit.md) | Sessions 01-12 closed 2026-05-25: diagnosis-first docs alignment, output bundle policy, AI grounding lock, runtime filtering-first boundary; [Session 12 closure](../audits/2026-05-25_post_architecture_alignment_session12_closure_report.md). Deferred: dirty tree, generated refresh, `RM-ARCH-010`, `RM-ARCH-011`. |
| 2026-05-24 | [Blocks 1-5 Performance Wave 2 (core_fast <= 5 min)](2026-05-24_blocks_1_5_performance_wave2_plan.md) | **Completed** | [2026-05-24 E2E timing audit](../audits/2026-05-24_blocks_1_5_e2e_timing_audit.md) Section6 | Sessions 0-8 closed 2026-05-24 (`RM-983`): `core_fast` E2E **210.7 s** (gate <= 300 s); parity **138 passed**; timing harness `core_fast_parallel`. |
| 2026-05-23 | [Core / Full Artifact and Documentation Confusion Remediation](2026-05-23_core_full_artifact_documentation_confusion_plan.md) | Completed | [Core/full confusion audit](../audits/2026-05-23_core_full_artifact_documentation_confusion_audit.md) | Sessions 00-06 closed 2026-05-24 (`RM-1100`-`RM-1106`): docs-only remediation (OUTPUTS, WORKFLOW, runbook, audits, ARCHITECTURE, agents, glossary, audit remediation status); `verify_docs.py` OK each session. |
| 2026-05-23 | [Site/API Default Output Refactor](2026-05-23_site_api_default_output_refactor_plan.md) | Completed | Internal discovery (Session 0) | Sessions 0-7 closed: `site_api` default, `output_manifest.json`, explicit export/PDF paths; pytest **38 passed**; [Session 07 closure](../audits/2026-05-23_site_api_default_output_session07_closure_report.md). |
| 2026-05-23 | [Candidate Factory Shared Evidence](2026-05-23_candidate_factory_shared_evidence_plan.md) | Completed | [Shared evidence audit](../audits/2026-05-23_candidate_factory_shared_evidence_audit.md) | Sessions 0-6 closed: shared context v2-v5, report timing, pytest **106** passed; full-menu timing **-28.1%** `report_seconds` (below -35% goal - [Session 06 audit](../audits/2026-05-23_candidate_factory_shared_evidence_session06_timing_audit.md)); RM-982 Done; Session 7 deferred. |
| 2026-05-22 | [Candidate Factory Parallel Lightweight Reports](2026-05-22_candidate_factory_parallel_reports_plan.md) | Completed | Post-runtime-refactor audit of sequential `lightweight_comparison` bottleneck | Sessions 0-6 closed: opt-in parallel lightweight reports + fallback; Session 5/6 timing audits; **keep parallel opt-in** (see [Session 06 audit](../audits/2026-05-22_candidate_factory_parallel_reports_session06_timing_audit.md)). |
| 2026-05-22 | [Demo MVP Reliability Repair](2026-05-22_demo_mvp_reliability_plan.md) | Completed | User-requested demo reliability repair | Fresh `run_portfolio_review.py --mode core --skip-pdf` proof-run completed; artifact checklist passed; caveat is disclosed candidate snapshot reuse unless full rebuild command is used. |
| 2026-05-22 | [Candidate Factory Runtime Refactor Plan](2026-05-22_candidate_factory_runtime_refactor_plan.md) | Completed | Operator timing audit (report/PDF bottleneck, not optimizers) | Sessions 0-9 closed: `standard` factory path, timing baseline audit, pytest bundle 102 passed; `cli_lambda` fix in run context. |
| 2026-05-21 | [Post-Deep-Audit Foundation & Downstream Readiness Plan](2026-05-21_post_deep_audit_foundation_plan.md) | Completed | [Blocks 1-5 Deep Audit Snapshot](../audits/2026-05-21_blocks_1_5_deep_audit_snapshot.md) | Sessions 01-10 closed 2026-05-22: Phase 17 Done; live full + resume (`RM-1029`); closure bundle **72 passed**. |
| 2026-05-21 | [Blocks 1-5 MVP Core Reliability Plan](2026-05-21_blocks_1_5_mvp_core_reliability_plan.md) | Completed | User-requested operational audit of Blocks 1-5 | Sessions 01-09 closed 2026-05-21: Phase 16 Done; offline bundle **125 passed**; subject materialization live smoke; `tests/conftest.py` fixture import fix. |
| 2026-05-20 | [Optimization Engine Post-Audit Roadmap](2026-05-20_optimization_engine_post_audit_roadmap.md) | Completed | [Optimization Engine Methodology Map](../audits/2026-05-20_optimization_engine_methodology_map.md) | Sessions 00-12 closed 2026-05-21: G1-G8/G10 governance gaps; DEC-2026-05-21-001; golden contracts; Phase 15 Done. |
| 2026-05-20 | [Candidate Portfolio Factory Post-Audit Roadmap](2026-05-20_candidate_factory_post_audit_roadmap.md) | Completed | [Candidate Factory Methodology Map](../audits/2026-05-20_candidate_factory_methodology_map.md) | Sessions 00-11 closed 2026-05-20: G1-G10 governance gaps; DEC-2026-05-20-003 concept registry; Phase 14 Done. |
| 2026-05-20 | [Stress Lab Methodology Governance Plan](2026-05-20_stress_lab_methodology_governance_plan.md) | Completed | [Stress Lab Methodology Map](../audits/2026-05-20_stress_lab_methodology_map.md) | Sessions 00-11 closed 2026-05-20: G1-G10 governance gaps; 90-test bundle + verify_docs; Phase 13 Done. |
| 2026-05-20 | [Portfolio X-Ray Post-Audit Roadmap](2026-05-20_portfolio_xray_post_audit_roadmap.md) | Completed | [Portfolio X-Ray Baseline Snapshot](../audits/2026-05-20_portfolio_xray_baseline_snapshot.md) | Sessions 00-10 closed 2026-05-20: threshold registry, provenance, factor inference, multi-window/TTR, layer spec, concentration, vol-spike Option B, golden contract tests, baseline snapshot; Phase 12 (`RM-940`-`RM-950`) Done. |
| 2026-05-20 | [Stress Lab Post-Audit Roadmap](2026-05-20_stress_lab_post_audit_roadmap.md) | Completed | [Stress Lab Baseline Snapshot](../audits/2026-05-20_stress_lab_baseline_snapshot.md) | Sessions 00-10 closed 2026-05-20: scorecard, replay, hedge gap, scenario coverage, synthetic transparency, portfolio-first integration, commentary/IPS, simulator API; Session 10 regression bundle + docs sync. |
| 2026-05-19 | [Portfolio X-Ray Diagnostics Deepening Plan](2026-05-19_portfolio_xray_diagnostics_deepening_plan.md) | Completed | [Portfolio X-Ray Layer Audit](../audits/2026-05-19_portfolio_xray_layer_audit.md) | Sessions 00-09 closed (`RM-930`-`RM-939`); X-Ray trust fixes and operational core/full review modes shipped 2026-05-20. |
| 2026-05-19 | [Post-Portfolio-First Stabilization Plan](2026-05-19_post_portfolio_first_stabilization_plan.md) | Completed | [Post-Portfolio-First State Audit](../audits/2026-05-19_post_portfolio_first_state_audit.md) | Sessions 00-11 closed Phase 9 (`RM-900`-`RM-911`); representative review and pytest/docs verify passed 2026-05-19. |
| 2026-05-18 | [Portfolio-First Transition Plan](2026-05-18_portfolio_first_transition_plan.md) | Completed | User-approved source-of-truth correction | Sessions 01-09 closed the transition: default review starts from `analysis_subject`, policy optimization is legacy by default, and offline E2E coverage spans current, model, and universe-baseline subjects. |
| 2026-05-17 | [Project Development Session Plan](2026-05-17_project_development_session_plan.md) | Completed | [Full Project System Audit](../audits/2026-05-17_full_project_system_audit.md) | Sessions 01-20 and post-closure triage are complete; keep as historical project memory. |
| 2026-05-17 | [Post-Audit Stabilization And Analytics Plan](2026-05-17_post_audit_stabilization_and_analytics_plan.md) | Completed | [Post-Session Deep System Audit](../audits/2026-05-17_post_session_deep_system_audit.md) | Sessions 02-20 closed 2026-05-17; see plan closure note and [ROADMAP](../ROADMAP.md) RM-623. |
| 2026-05-17 | [Post-Audit MVP Stabilization Plan](2026-05-17_post_audit_mvp_stabilization_plan.md) | Completed | [Repeat Project MVP Readiness Audit](../audits/2026-05-17_repeat_project_mvp_readiness_audit.md) | Sessions 01-11 closed 2026-05-18; Phase 7 (`RM-700`-`RM-710`) complete. |

## Focused Historical ExecPlans

The remaining files in this directory are focused implementation plans for earlier scoped workstreams
such as factor analytics, stress diagnostics, taxonomy, optimization baselines, PDF output redesign,
and input-assumption layers. They remain useful as implementation history, but they are not the active
project-level plan unless explicitly referenced.

## Maintenance

- Add every new project-level plan to the Major Plan History table.
- Keep at most one project-level plan marked `Active` unless the user explicitly starts parallel plans.
- When a plan closes, change its status to `Completed` or `Deferred` and update the Current Pointer.
- Keep detailed progress inside each ExecPlan; keep this file as the concise index.
