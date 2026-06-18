# Component State Matrix

Status: isolated UI workflow matrix for Portfolio MRI. This document defines the `/sandbox/components` coverage target for the foundation-first UX/UI implementation wave.

## Workflow decision

The official isolated UI workflow for this wave is the existing `/sandbox/components` route. Storybook is deferred until the sandbox proves which states and components need longer-term story coverage.

## Shared primitive coverage

| Component | Required examples |
| --- | --- |
| `Button` | primary, secondary, ghost, danger, disabled, long label, mobile-width action. |
| `StatusBadge` | blue active, amber watch/partial, red material issue/failure, slate neutral, long label. |
| `Surface` | default, glass, raised, subtle, warning, risk. |
| `EvidenceSummary` | no items, one item, four items, long text, amber/red/blue tones. |
| `MetricMatrix` | normal rows, unavailable rows, material rows, mobile stacking. |
| `VerdictHero` | no facts, three facts, long interpretation, boundary note, action row. |
| `States` | loading, empty, locked, partial evidence, stale lineage, read-only history, evidence insufficient, candidate unavailable, generation failed. |
| `ActiveDiagnosticTestContext` | selected test only, generated test candidate, evidence limitation, stale/partial tone. |

## Product component coverage

| Product area | Required states |
| --- | --- |
| Diagnosis | locked, running, failed/retry, complete, weak/partial evidence, advanced collapsed. |
| Hypothesis | blocked, ready to generate, generating, generation failed, generated, read-only history. |
| Comparison | candidate missing, candidate unavailable, comparison running, metrics unavailable, valid comparison, stale lineage. |
| Verdict | evidence insufficient, candidate failed, ready to generate, generated verdict, stale comparison. |
| Report | blocked, generating, preview created, warnings, read-only history. |

## State language rules

Empty and blocked states must say what is missing and what the user can do next. Partial and unavailable states must look like valid product states, not broken UI. Failed generation must explain recovery in setup language. Read-only history must explain that saved evidence can be read but cannot unlock new same-run actions. Stale lineage must say that previous results were ignored because they do not match the active diagnostic test.

## Acceptance

`/sandbox/components` is acceptable for this wave when it displays every shared state family above, uses only product-facing language, and can be reviewed without running a full review or using generated output folders.
