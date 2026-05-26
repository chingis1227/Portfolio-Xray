# Audit Register

This directory stores project audits as historical project memory. Audits are evidence and planning
inputs; they do not override `SPEC.md`, `RULES.md`, `OUTPUTS.md`, `TESTING.md`, detailed specs, or
current code behavior.

Portfolio MRI documentation alignment note: older audits may use prior product language such as
optimizer-first framing, recommendation wording, Macro Dashboard, Selection Engine, Portfolio Health
Score, or Robustness Scorecard emphasis. Preserve those files as snapshot-at-time evidence; do not
treat them as current product direction unless an active canonical doc or current spec confirms it.

Use this register to understand which audits exist, what each audit produced, and which plan followed
from it. When a new audit is created, add it here with its date, status, related plan, and short
outcome.

## Status Values

| Status | Meaning |
| --- | --- |
| Active input | Current audit evidence for the active plan. |
| Historical | Useful background, but not the active working baseline. |
| Superseded | Replaced by a later audit or plan, but retained for traceability. |

## Audit History

| Date | Audit | Status | Follow-up plan | Outcome |
| --- | --- | --- | --- | --- |
| 2026-05-26 | [Input Layer MVP Acceptance Audit](2026-05-26_input_layer_mvp_acceptance_audit.md) | **Historical** (closure) | [Input Layer MVP Migration](../exec_plans/2026-05-26_input_layer_mvp_migration.md) (**Completed**) | Session 10 closure: Core MVP input 10/10 PASS; dry-run + live materialize Block 1; `validate_one_candidate_demo.py` PASS; pytest **36 passed**. |
| 2026-05-25 | [Product-Flow Validation Audit](2026-05-25_product_flow_validation_audit.md) | **Historical** (closed) | [Product Flow MVP Backend Plan](../exec_plans/2026-05-25_product_flow_mvp_backend_plan.md) (**Completed**) | Original 2026-05-25 read-only findings; **Session 08 closure 2026-05-26:** demo-ready MVP backend, `RM-ARCH-011` Done, pytest 46 passed; residual: dirty tree, stale compare on disk, `RM-ARCH-010` deferred. |
| 2026-05-26 | [Product Flow Demo Baseline Snapshot](2026-05-25_product_flow_demo_baseline_snapshot.md) | **Historical** | [Product Flow MVP Backend Plan](../exec_plans/2026-05-25_product_flow_mvp_backend_plan.md) (Completed) | Live run `--candidates equal_weight`; six bundle JSON PASS; RM-ARCH-011 spot check PASS; caveats C1/C2 documented and accepted at audit closure. |
| 2026-05-25 | [Full Project Architecture Alignment Audit](2026-05-25_full_project_architecture_alignment_audit.md) | **Historical** (superseded by closure) | [Post-Audit Portfolio MRI Architecture Alignment Roadmap](../exec_plans/2026-05-25_post_architecture_alignment_roadmap.md) (**Completed**) | Deep source/code/output alignment audit for diagnosis-first architecture. Remediation closed Sessions 01–12; [Session 12 closure report](2026-05-25_post_architecture_alignment_session12_closure_report.md). |
| 2026-05-24 | [Blocks 1–5 E2E Timing Audit](2026-05-24_blocks_1_5_e2e_timing_audit.md) | **Active input** | [Performance Wave 2 ExecPlan](../exec_plans/2026-05-24_blocks_1_5_performance_wave2_plan.md) (`RM-983`) | Fresh `site_api` E2E: default core **542.5 s** (6 cand + subject + decision); full menu **973.1 s**; PDF **0 s**; factory `report_seconds` **853.2 s** vs Shared Evidence **857.7 s**; pytest **80 passed**. Session 0 baseline lock 2026-05-24. |
| 2026-05-23 | [Core / Full Artifact and Documentation Confusion Audit](2026-05-23_core_full_artifact_documentation_confusion_audit.md) | Historical | [Confusion remediation ExecPlan](../exec_plans/2026-05-23_core_full_artifact_documentation_confusion_plan.md) (Completed) | Read-only audit; remediation closed 2026-05-24 (Sessions 01–06): OUTPUTS/runbook/WORKFLOW, command matrix, agents, glossary — see audit § «Remediation status». |
| 2026-05-23 | [Site/API Default Output Session 07 Closure Report](2026-05-23_site_api_default_output_session07_closure_report.md) | Historical | [Site/API Default Output Refactor](../exec_plans/2026-05-23_site_api_default_output_refactor_plan.md) (Completed) | Sessions 0–7 closed; acceptance **10/10**; pytest **38 passed**; risks and next steps documented. |
| 2026-05-23 | [Site/API Default Output Session 06 Timing Audit](2026-05-23_site_api_default_output_session06_timing_audit.md) | Historical | [Site/API Default Output Refactor](../exec_plans/2026-05-23_site_api_default_output_refactor_plan.md) (Completed) | `core_benchmarks` × 2 `site_api` smoke: presentation artifacts **0** by count; decision JSON **14/14**; wall **171.6 s**; pytest **38 passed**. |
| 2026-05-23 | [Candidate Factory Shared Evidence Session 06 Timing Audit](2026-05-23_candidate_factory_shared_evidence_session06_timing_audit.md) | Historical | [Candidate Factory Shared Evidence ExecPlan](../exec_plans/2026-05-23_candidate_factory_shared_evidence_plan.md) (Completed) | Session 6 closure: **106** pytest passed; full-menu sequential `report_seconds` **857.7 s** vs baseline **1192.9 s** (−28.1%, below −35% target); RM-982 Done with documented blocker. |
| 2026-05-23 | [Candidate Factory Shared Evidence Audit](2026-05-23_candidate_factory_shared_evidence_audit.md) | Historical | [Candidate Factory Shared Evidence ExecPlan](../exec_plans/2026-05-23_candidate_factory_shared_evidence_plan.md) (Completed) | Pre-implementation map (R1–R5 ×16); superseded by Sessions 1–6 implementation + Session 06 timing audit. |
| 2026-05-22 | [Candidate Factory Parallel Reports Session 06 Timing Audit](2026-05-22_candidate_factory_parallel_reports_session06_timing_audit.md) | Historical | [Candidate Factory Parallel Lightweight Reports](../exec_plans/2026-05-22_candidate_factory_parallel_reports_plan.md) (Completed) | Session 6 closure: full `default_v1` sequential vs parallel smoke; 48 passed; 47.9% wall-clock improvement; identical run statuses; comparison-critical parity for 13 succeeded candidates; **keep parallel opt-in**. |
| 2026-05-22 | [Candidate Factory Parallel Reports Timing Audit](2026-05-22_candidate_factory_parallel_reports_timing_audit.md) | Historical | [Candidate Factory Parallel Lightweight Reports](../exec_plans/2026-05-22_candidate_factory_parallel_reports_plan.md) (Completed) | Session 5 verification: focused factory/manifest tests 48 passed; two-candidate sequential vs parallel smoke completed; comparison-critical artifacts matched; parallel wall clock improved by 35.4%. |
| 2026-05-22 | [Candidate Factory Timing Baseline](2026-05-22_candidate_factory_timing_baseline.md) | Historical | [Candidate Factory Runtime Refactor Plan](../exec_plans/2026-05-22_candidate_factory_runtime_refactor_plan.md) (Completed) | Session 9 closure: pre/post timing buckets, 2-candidate `standard` smoke, pytest 102 passed; `cli_lambda` run-context fix. |
| 2026-05-22 | [Blocks 1-5 Verification Report](2026-05-22_blocks_1_5_verification_report.md) | Active input | [Confusion remediation ExecPlan](../exec_plans/2026-05-23_core_full_artifact_documentation_confusion_plan.md) (Session 03 disk caveat applied) | 8-ticker YES/PARTIAL/NO checklist for Blocks 1-5; §20 qualified as snapshot-at-write-time — **verify `candidate_factory_run.json` → `factory_profile_id` on disk** before treating full-menu claims as current; decision layers excluded. |
| 2026-05-21 | [Blocks 1–5 Deep Audit Snapshot](2026-05-21_blocks_1_5_deep_audit_snapshot.md) | Active input | [Post-Deep-Audit Foundation Plan](../exec_plans/2026-05-21_post_deep_audit_foundation_plan.md) | Second-level audit after Phase 16; P0/P1 gaps P17-G1–G14; Sessions 02–10 remediation. |
| 2026-05-20 | [Optimization Engine Baseline Snapshot](2026-05-20_optimization_engine_baseline_snapshot.md) | Historical | [Optimization Engine Post-Audit Roadmap](../exec_plans/2026-05-20_optimization_engine_post_audit_roadmap.md) | Session 00 checklist; Phase 15 Sessions 01-12 closure; golden contracts; artifact fingerprints TBD until representative optimizer run. |
| 2026-05-20 | [Optimization Engine Methodology Map](2026-05-20_optimization_engine_methodology_map.md) | Historical | [Optimization Engine Post-Audit Roadmap](../exec_plans/2026-05-20_optimization_engine_post_audit_roadmap.md) | Block 5 map (5.1-5.11); Phase 15 governance wave closed Sessions 00-12 (G1-G8/G10 + golden/readiness). |
| 2026-05-20 | [Candidate Factory Baseline Snapshot](2026-05-20_candidate_factory_baseline_snapshot.md) | Historical | [Candidate Portfolio Factory Post-Audit Roadmap](../exec_plans/2026-05-20_candidate_factory_post_audit_roadmap.md) | Session 00 checklist; Phase 14 Sessions 01-11 closure; artifact fingerprints TBD until representative review run. |
| 2026-05-20 | [Candidate Factory Methodology Map](2026-05-20_candidate_factory_methodology_map.md) | Historical | [Candidate Portfolio Factory Post-Audit Roadmap](../exec_plans/2026-05-20_candidate_factory_post_audit_roadmap.md) | Block 4 map (4.1-4.9); Phase 14 governance wave closed Sessions 00-11 (G1-G10 + golden/resume/runbook). |
| 2026-05-20 | [Stress Lab Methodology Map](2026-05-20_stress_lab_methodology_map.md) | Historical | [Stress Lab Methodology Governance Plan](../exec_plans/2026-05-20_stress_lab_methodology_governance_plan.md) | Block 3 methodology map; Phase 13 governance wave closed Sessions 00-11 (G1-G10); Session 11 verification 90 passed. |
| 2026-05-20 | [Portfolio X-Ray Baseline Snapshot](2026-05-20_portfolio_xray_baseline_snapshot.md) | Historical | [Portfolio X-Ray Post-Audit Roadmap](../exec_plans/2026-05-20_portfolio_xray_post_audit_roadmap.md) | Artifact checklist and golden contract reference; Sessions 01-10 closed governance gaps G1-G6, G8-G11; Session 10 wave closure documented in the audit file. |
| 2026-05-20 | [Portfolio X-Ray Methodology Map](2026-05-20_portfolio_xray_methodology_map.md) | Historical | [Portfolio X-Ray Post-Audit Roadmap](../exec_plans/2026-05-20_portfolio_xray_post_audit_roadmap.md) | Block 2 methodology map (sub-blocks 2.1-2.7, provenance C/S/A/T/N, gaps G1-G11); Phase 12 governance wave closed 2026-05-20. |
| 2026-05-20 | [Stress Lab Baseline Snapshot](2026-05-20_stress_lab_baseline_snapshot.md) | Historical | [Stress Lab Methodology Governance Plan](../exec_plans/2026-05-20_stress_lab_methodology_governance_plan.md) | Session 00 fingerprints; post-audit Sessions 01-10 + Phase 13 Sessions 01-11 closure; checklist items 14-17; Session 11 governance verification documented. |
| 2026-05-19 | [Portfolio X-Ray Layer Audit](2026-05-19_portfolio_xray_layer_audit.md) | Historical | [Portfolio X-Ray Diagnostics Deepening Plan](../exec_plans/2026-05-19_portfolio_xray_diagnostics_deepening_plan.md) | Sessions 00-09 closed 2026-05-20 (`RM-930`-`RM-939`); X-Ray trust fixes and core/full review modes shipped. |
| 2026-05-19 | [Post-Portfolio-First State Audit](2026-05-19_post_portfolio_first_state_audit.md) | Historical | [Post-Portfolio-First Stabilization Plan](../exec_plans/2026-05-19_post_portfolio_first_stabilization_plan.md) | Phase 9 (`RM-900`-`RM-911`) closed 2026-05-19 after Sessions 00-11; audit findings addressed or explicitly deferred in the stabilization plan. |
| 2026-05-17 | [Diagnostic Product Concept Alignment Audit](2026-05-17_diagnostic_product_concept_alignment_audit.md) | Historical | [Project Development Session Plan](../exec_plans/2026-05-17_project_development_session_plan.md) | Quick concept-alignment audit supporting the first full project audit. |
| 2026-05-17 | [Full Project System Audit](2026-05-17_full_project_system_audit.md) | Historical | [Project Development Session Plan](../exec_plans/2026-05-17_project_development_session_plan.md) | Identified the missing ordered decision-support pipeline and led to Sessions 01-20. |
| 2026-05-17 | [Post-Session Deep System Audit](2026-05-17_post_session_deep_system_audit.md) | Historical | [Post-Audit Stabilization And Analytics Plan](../exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md) | Reviewed the project after Sessions 01-20 and set the stabilization/integration backlog. |
| 2026-05-17 | [Repeat Project MVP Readiness Audit](2026-05-17_repeat_project_mvp_readiness_audit.md) | Historical | [Post-Audit MVP Stabilization Plan](../exec_plans/2026-05-17_post_audit_mvp_stabilization_plan.md) | Drove Phase 7 (`RM-700`-`RM-710`); plan closed 2026-05-18 after Sessions 01-11. |

## Maintenance

- Keep audit files in this directory.
- Keep audit filenames date-prefixed with a short descriptive slug.
- Link each audit to the ExecPlan or roadmap work that followed from it.
- Do not edit generated outputs as audit source material; reference them only as evidence when needed.
