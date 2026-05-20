# Audit Register

This directory stores project audits as historical project memory. Audits are evidence and planning
inputs; they do not override `SPEC.md`, `RULES.md`, `OUTPUTS.md`, `TESTING.md`, detailed specs, or
current code behavior.

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
| 2026-05-20 | [Candidate Factory Baseline Snapshot](2026-05-20_candidate_factory_baseline_snapshot.md) | Historical | [Candidate Portfolio Factory Post-Audit Roadmap](../exec_plans/2026-05-20_candidate_factory_post_audit_roadmap.md) | Session 00 checklist; Phase 14 Sessions 01–11 closure; artifact fingerprints TBD until representative review run. |
| 2026-05-20 | [Candidate Factory Methodology Map](2026-05-20_candidate_factory_methodology_map.md) | Historical | [Candidate Portfolio Factory Post-Audit Roadmap](../exec_plans/2026-05-20_candidate_factory_post_audit_roadmap.md) | Block 4 map (4.1–4.9); Phase 14 governance wave closed Sessions 00–11 (G1–G10 + golden/resume/runbook). |
| 2026-05-20 | [Stress Lab Methodology Map](2026-05-20_stress_lab_methodology_map.md) | Historical | [Stress Lab Methodology Governance Plan](../exec_plans/2026-05-20_stress_lab_methodology_governance_plan.md) | Block 3 methodology map; Phase 13 governance wave closed Sessions 00–11 (G1–G10); Session 11 verification 90 passed. |
| 2026-05-20 | [Portfolio X-Ray Baseline Snapshot](2026-05-20_portfolio_xray_baseline_snapshot.md) | Historical | [Portfolio X-Ray Post-Audit Roadmap](../exec_plans/2026-05-20_portfolio_xray_post_audit_roadmap.md) | Artifact checklist and golden contract reference; Sessions 01–10 closed governance gaps G1–G6, G8–G11; Session 10 wave closure documented in the audit file. |
| 2026-05-20 | [Portfolio X-Ray Methodology Map](2026-05-20_portfolio_xray_methodology_map.md) | Historical | [Portfolio X-Ray Post-Audit Roadmap](../exec_plans/2026-05-20_portfolio_xray_post_audit_roadmap.md) | Block 2 methodology map (sub-blocks 2.1–2.7, provenance C/S/A/T/N, gaps G1–G11); Phase 12 governance wave closed 2026-05-20. |
| 2026-05-20 | [Stress Lab Baseline Snapshot](2026-05-20_stress_lab_baseline_snapshot.md) | Historical | [Stress Lab Methodology Governance Plan](../exec_plans/2026-05-20_stress_lab_methodology_governance_plan.md) | Session 00 fingerprints; post-audit Sessions 01–10 + Phase 13 Sessions 01–11 closure; checklist items 14–17; Session 11 governance verification documented. |
| 2026-05-19 | [Portfolio X-Ray Layer Audit](2026-05-19_portfolio_xray_layer_audit.md) | Historical | [Portfolio X-Ray Diagnostics Deepening Plan](../exec_plans/2026-05-19_portfolio_xray_diagnostics_deepening_plan.md) | Sessions 00-09 closed 2026-05-20 (`RM-930`-`RM-939`); X-Ray trust fixes and core/full review modes shipped. |
| 2026-05-19 | [Post-Portfolio-First State Audit](2026-05-19_post_portfolio_first_state_audit.md) | Historical | [Post-Portfolio-First Stabilization Plan](../exec_plans/2026-05-19_post_portfolio_first_stabilization_plan.md) | Phase 9 (`RM-900`-`RM-911`) closed 2026-05-19 after Sessions 00-11; audit findings addressed or explicitly deferred in the stabilization plan. |
| 2026-05-17 | [Diagnostic Product Concept Alignment Audit](2026-05-17_diagnostic_product_concept_alignment_audit.md) | Historical | [Project Development Session Plan](../exec_plans/2026-05-17_project_development_session_plan.md) | Quick concept-alignment audit supporting the first full project audit. |
| 2026-05-17 | [Full Project System Audit](2026-05-17_full_project_system_audit.md) | Historical | [Project Development Session Plan](../exec_plans/2026-05-17_project_development_session_plan.md) | Identified the missing ordered decision-support pipeline and led to Sessions 01-20. |
| 2026-05-17 | [Post-Session Deep System Audit](2026-05-17_post_session_deep_system_audit.md) | Historical | [Post-Audit Stabilization And Analytics Plan](../exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md) | Reviewed the project after Sessions 01-20 and set the stabilization/integration backlog. |
| 2026-05-17 | [Repeat Project MVP Readiness Audit](2026-05-17_repeat_project_mvp_readiness_audit.md) | Historical | [Post-Audit MVP Stabilization Plan](../exec_plans/2026-05-17_post_audit_mvp_stabilization_plan.md) | Drove Phase 7 (`RM-700`–`RM-710`); plan closed 2026-05-18 after Sessions 01-11. |

## Maintenance

- Keep audit files in this directory.
- Keep audit filenames date-prefixed with a short descriptive slug.
- Link each audit to the ExecPlan or roadmap work that followed from it.
- Do not edit generated outputs as audit source material; reference them only as evidence when needed.
