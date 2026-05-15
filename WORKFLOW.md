# WORKFLOW.md

This file defines the practical task workflow for Portfolio X-Ray & Optimization Terminal / Portfolio MRI.

It explains how work moves from request to implementation, verification, documentation sync, project-memory updates, and commit. It does not replace `RULES.md`, `SPEC.md`, `TESTING.md`, `PLANS.md`, or detailed specs; it connects them into one operating process.

Update this file when the working process changes: task intake, planning thresholds, implementation discipline, verification routing, documentation sync, project-memory updates, commit practice, or final reporting.

## Core Workflow

Use this sequence for meaningful work:

1. Understand the request.
2. Classify the change area.
3. Check the source of truth.
4. Decide whether a plan is required.
5. Implement scoped changes.
6. Sync documentation.
7. Verify with the right checks.
8. Update project memory if needed.
9. Review the diff and stale references.
10. Commit only the intended files when asked.
11. Report what changed and what was verified.

## 1. Task Intake

Clarify what the user is asking for:

- code behavior change
- documentation change
- data/config change
- formula or metric change
- optimizer or constraint change
- stress/factor/macro/reporting change
- generated-output refresh
- investigation or explanation only

If the request is ambiguous and a wrong assumption could change behavior, ask a concise question. Otherwise make a reasonable assumption, state it when useful, and proceed.

## 2. Source-Of-Truth Check

Before changing behavior, check the owning source of truth:

- [RULES.md](RULES.md) for high-level principles and source-of-truth ownership.
- [SPEC.md](SPEC.md) for the current implementation contract.
- [OUTPUTS.md](OUTPUTS.md) for generated output folders, artifacts, formats, report packaging, and generated-vs-source boundaries.
- [GLOSSARY.md](GLOSSARY.md) for shared terminology and short definitions.
- [DATA.md](DATA.md) for data sources, data pipeline, structures, quality rules, and data sync triggers.
- [TESTING.md](TESTING.md) for verification strategy and test selection.
- [docs/specs/](docs/specs/README.md) for detailed module behavior.
- [ARCHITECTURE.md](ARCHITECTURE.md) for module boundaries and execution flow.
- [DESIGN.md](DESIGN.md) for UI, dashboard, HTML report, or visual work.
- [docs/DIAGNOSTIC_PRODUCT_CONCEPT.md](docs/DIAGNOSTIC_PRODUCT_CONCEPT.md) for non-binding product direction only.

Do not invent formulas, estimators, scenarios, constraints, statuses, or data rules when a spec exists.

## 3. Planning

Use [PLANS.md](PLANS.md) and a checked-in ExecPlan under `docs/exec_plans/` when work is large, risky, multi-step, or architectural.

Plan usually required:

- broad refactors
- new modules or major feature areas
- changes to optimizer policy, stress logic, data pipeline, or output contracts
- changes that require multiple coordinated code and documentation updates
- work where progress, decisions, or surprises must be tracked over time

Plan usually not required:

- small docs updates
- localized bug fixes
- narrow tests
- simple reference updates
- direct answers or investigations with no code change

## 4. Implementation Discipline

Keep the change scoped to the requested behavior and the owning files.

Rules:

- Prefer existing helpers and repo patterns over parallel implementations.
- Do not change formulas, scenarios, optimizer logic, outputs, or tests unless the task requires it.
- Do not treat generated outputs as source unless the task explicitly targets them.
- Do not revert unrelated user changes or dirty working-tree files.
- Preserve diagnostic-only boundaries unless a canonical spec changes them.
- Keep assumptions explicit in code, configs, reports, or docs.

## 5. Documentation Sync

Documentation sync is part of done for meaningful changes.

Update the owning docs when behavior changes:

- [SPEC.md](SPEC.md): general implementation contract, workflows, inputs/outputs, behavior rules, edge cases, status matrix.
- [OUTPUTS.md](OUTPUTS.md): output folders, artifact names, formats, report sections, visual/report packaging, and generated-vs-source boundaries.
- [GLOSSARY.md](GLOSSARY.md): recurring terminology, acronyms, names, and definitions.
- [DATA.md](DATA.md): sources, structures, data pipeline, NaN handling, FX, benchmark, risk-free, factor/macro inputs, data validation.
- `docs/specs/*.md`: detailed behavior of a specific module.
- [README.md](README.md): user-facing commands, setup, structure, workflows, outputs.
- [ARCHITECTURE.md](ARCHITECTURE.md): module boundaries, flows, layers.
- [AGENTS.md](AGENTS.md): agent operating instructions.
- [TESTING.md](TESTING.md): verification strategy or required checks.
- [WORKFLOW.md](WORKFLOW.md): task process itself.

Do not duplicate long formulas or implementation details in top-level docs when an owning spec exists.

## 6. Verification

Use [TESTING.md](TESTING.md) to select checks.

Default order:

1. Run the narrowest reliable focused test or check.
2. Broaden to adjacent tests when shared helpers may be affected.
3. Run full `python -m pytest` when portfolio math, optimizer behavior, data alignment, config schema, stress logic, or report contracts may regress.
4. Run CLI smoke commands when entrypoints or generated outputs are affected.
5. Run Markdown link and stale-reference checks for documentation structure changes.

Documentation-only changes usually do not require `pytest` unless they change executable examples, commands, or behavior expectations.

## 7. Project Memory Updates

Update project-memory documents only when relevant:

- [KNOWN_ISSUES.md](KNOWN_ISSUES.md): add active bugs, model limitations, testing gaps, weak spots, or technical debt that are not fixed immediately; remove them after verified fix.
- [DECISIONS.md](DECISIONS.md): record key decisions, rationale, rejected alternatives, assumptions, consequences, and review triggers.
- [CHANGELOG.md](CHANGELOG.md): record meaningful completed changes in short bullets; do not log every minor edit.
- [GLOSSARY.md](GLOSSARY.md): add, update, rename, or remove terms when project vocabulary changes.
- ExecPlans under `docs/exec_plans/`: update progress, surprises, decision log, and outcomes for large planned work.

Project memory must stay concise. If an entry becomes long, move detail into the owning spec or ExecPlan and keep only a short pointer.

## 8. Diff Review

Before finishing:

- Check which files changed.
- Confirm generated files were not changed unless intentionally targeted.
- Search for stale references after renames, moves, or removed concepts.
- Verify Markdown links after doc moves or new docs.
- Confirm docs and code do not contradict each other.
- Report any unverified area, blocker, or assumption.

## 9. Commit Workflow

Commit only when the user asks or when the agreed workflow requires it.

Before commit:

- Stage only intended files.
- Exclude unrelated dirty files, generated artifacts, caches, and user changes.
- Run `git diff --cached --check`.
- Review `git diff --cached --name-only`.
- Use a concise commit message describing the project-level change.

After commit, report the commit hash and mention any remaining uncommitted files that were intentionally left out.

## 10. Final Response

Final response should be short and evidence-based:

- what changed
- where it changed
- what verification ran
- what was not run and why
- any remaining risk or uncommitted unrelated changes when relevant

Do not claim work is done without proof through tests, link checks, CLI output, or a clear explanation of why verification was not required.

## Workflow Summary

```text
Request
-> classify change
-> check source of truth
-> plan if needed
-> implement scoped change
-> sync docs
-> verify
-> update known issues / decisions / changelog if needed
-> review diff and stale references
-> commit when asked
-> report outcome
```
