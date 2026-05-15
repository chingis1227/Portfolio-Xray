# DECISIONS.md

This file is the concise living decision log for Portfolio X-Ray & Optimization Terminal / Portfolio MRI.

It records important decisions, why they were made, what alternatives were rejected, and which assumptions existed at the time. It is not a changelog, roadmap, issue tracker, implementation spec, or ExecPlan.

No project-level decisions are recorded yet. Add entries here only when a real decision is made.

## Purpose

- Preserve the reasoning behind important project choices.
- Prevent the same architectural, product, or methodology questions from being reopened without context.
- Make assumptions visible when a decision is made.
- Keep rationale separate from implementation details and change history.

## What Belongs Here

- Architecture decisions that affect module boundaries, workflows, interfaces, or source-of-truth ownership.
- Product boundary decisions, such as diagnostic-only vs production policy behavior.
- Financial methodology decisions, such as optimizer policy, stress governance, data assumptions, metrics behavior, or model-risk boundaries.
- Testing and quality decisions that affect verification strategy.
- Documentation governance decisions that affect how project knowledge is organized.

## What Does Not Belong Here

- Every code change; use [CHANGELOG.md](CHANGELOG.md) for concise completed-change history.
- Active bugs, weak spots, or technical debt; use [KNOWN_ISSUES.md](KNOWN_ISSUES.md).
- Long formulas or module contracts; use `SPEC.md`, `DATA.md`, and `docs/specs/*.md`.
- Step-by-step implementation plans; use [PLANS.md](PLANS.md) and `docs/exec_plans/`.
- Future product ideas without a decision; use `PRODUCT.md`, `BUSINESS_VISION.md`, or `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`.

## When To Add Or Update

- Add an entry when the project chooses one path among meaningful alternatives.
- Add an entry when a decision affects behavior, source-of-truth structure, methodology, API/UI boundaries, data policy, testing policy, or reporting contracts.
- Update an entry when the decision is superseded, narrowed, expanded, or its assumptions are no longer true.
- Do not rewrite history silently; mark old decisions as `superseded` and link the newer decision.
- If a decision changes current behavior, update the owning spec and add a short entry to [CHANGELOG.md](CHANGELOG.md).
- If a decision exposes an unresolved risk or debt item, add it to [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

## Entry Format

Keep entries short. Use this format:

```markdown
Decision ID: DEC-YYYY-MM-DD-NNN
Title: Short title

- Status: proposed | accepted | superseded
- Date: YYYY-MM-DD
- Decision: What was decided.
- Context: What problem or trade-off triggered the decision.
- Rationale: Why this option was chosen.
- Alternatives considered: What was rejected and why.
- Assumptions: What was believed to be true at the time.
- Consequences: What changes or constraints follow from the decision.
- Related documents: Links to specs, plans, code, tests, or docs.
- Review trigger: When this decision should be revisited.
```

## Decisions

No project-level decisions are currently recorded.
