# ExecPlan Register

This directory stores implementation plans and historical work plans. Use this register as the
project-memory pointer for plan status. If a chat mentions "the plan", "current plan", or ongoing
plan work without naming a file, start from the single row marked `Active`.

Plans are documentation and workflow guidance only. They do not override `SPEC.md`, `RULES.md`,
`OUTPUTS.md`, `TESTING.md`, detailed specs, current code behavior, formulas, metrics, or generated
artifact contracts.

## Status Values

| Status | Meaning |
| --- | --- |
| Active | Current working plan. Resume here by default. |
| Completed | Implemented or closed; retained for history. |
| Historical | Older focused plan retained for traceability. |
| Deferred | Accepted but intentionally paused. |

## Current Pointer

**Active:** None (resume from [ROADMAP](../ROADMAP.md) for the next backlog row).

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
