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

Active: none.

Completed: [Post-Portfolio-First Stabilization Plan](2026-05-19_post_portfolio_first_stabilization_plan.md)
(Sessions 00-11, `RM-900`-`RM-911`, closed 2026-05-19).

Completed: [Portfolio-First Transition Plan](2026-05-18_portfolio_first_transition_plan.md) (Sessions 01-09, closed 2026-05-18).

Completed: [Post-Audit MVP Stabilization Plan](2026-05-17_post_audit_mvp_stabilization_plan.md) (Sessions 01-11, `RM-710`, closed 2026-05-18).

Also completed: [Post-Audit Stabilization And Analytics Plan](2026-05-17_post_audit_stabilization_and_analytics_plan.md) (Sessions 02-20, `RM-623`).

Default next work: choose the next roadmap item or create a new ExecPlan when the next task is large,
risky, or architectural (see [ROADMAP](../ROADMAP.md)).

## Major Plan History

| Date | Plan | Status | Origin audit | Current handoff |
| --- | --- | --- | --- | --- |
| 2026-05-19 | [Post-Portfolio-First Stabilization Plan](2026-05-19_post_portfolio_first_stabilization_plan.md) | Completed | [Post-Portfolio-First State Audit](../audits/2026-05-19_post_portfolio_first_state_audit.md) | Sessions 00-11 closed Phase 9 (`RM-900`-`RM-911`); representative review and pytest/docs verify passed 2026-05-19. |
| 2026-05-18 | [Portfolio-First Transition Plan](2026-05-18_portfolio_first_transition_plan.md) | Completed | User-approved source-of-truth correction | Sessions 01-09 closed the transition: default review starts from `analysis_subject`, policy optimization is legacy by default, and offline E2E coverage spans current, model, and universe-baseline subjects. |
| 2026-05-17 | [Project Development Session Plan](2026-05-17_project_development_session_plan.md) | Completed | [Full Project System Audit](../audits/2026-05-17_full_project_system_audit.md) | Sessions 01-20 and post-closure triage are complete; keep as historical project memory. |
| 2026-05-17 | [Post-Audit Stabilization And Analytics Plan](2026-05-17_post_audit_stabilization_and_analytics_plan.md) | Completed | [Post-Session Deep System Audit](../audits/2026-05-17_post_session_deep_system_audit.md) | Sessions 02-20 closed 2026-05-17; see plan closure note and [ROADMAP](../ROADMAP.md) RM-623. |
| 2026-05-17 | [Post-Audit MVP Stabilization Plan](2026-05-17_post_audit_mvp_stabilization_plan.md) | Completed | [Repeat Project MVP Readiness Audit](../audits/2026-05-17_repeat_project_mvp_readiness_audit.md) | Sessions 01-11 closed 2026-05-18; Phase 7 (`RM-700`–`RM-710`) complete. |

## Focused Historical ExecPlans

The remaining files in this directory are focused implementation plans for earlier scoped workstreams
such as factor analytics, stress diagnostics, taxonomy, optimization baselines, PDF output redesign,
and input-assumption layers. They remain useful as implementation history, but they are not the active
project-level plan unless explicitly referenced.

## Maintenance

- Add every new project-level plan to the Major Plan History table.
- Keep exactly one project-level plan marked `Active` unless the user explicitly starts parallel plans.
- When a plan closes, change its status to `Completed` or `Deferred` and update the Current Pointer.
- Keep detailed progress inside each ExecPlan; keep this file as the concise index.
