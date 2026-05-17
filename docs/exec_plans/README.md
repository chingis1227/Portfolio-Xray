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

Active plan: [Post-Audit Stabilization And Analytics Plan](2026-05-17_post_audit_stabilization_and_analytics_plan.md)

Next default work item: continue the first incomplete session in the active plan unless the user names
another session or plan.

## Major Plan History

| Date | Plan | Status | Origin audit | Current handoff |
| --- | --- | --- | --- | --- |
| 2026-05-17 | [Project Development Session Plan](2026-05-17_project_development_session_plan.md) | Completed | [Full Project System Audit](../audits/2026-05-17_full_project_system_audit.md) | Sessions 01-20 and post-closure triage are complete; keep as historical project memory. |
| 2026-05-17 | [Post-Audit Stabilization And Analytics Plan](2026-05-17_post_audit_stabilization_and_analytics_plan.md) | Active | [Post-Session Deep System Audit](../audits/2026-05-17_post_session_deep_system_audit.md) | Resume from the first incomplete session in this plan. |

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
