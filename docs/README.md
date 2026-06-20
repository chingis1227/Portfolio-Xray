# Portfolio MRI Documentation

This is the main navigation page for Portfolio MRI documentation. It tells contributors what to
read first, which documents are current source of truth, and which folders are historical memory.

## Start Here

Read these first when joining the project or before changing behavior:

1. [../README.md](../README.md) - short product orientation.
2. [../PRODUCT.md](../PRODUCT.md) - product direction, Core MVP boundaries, and non-goals.
3. [../SPEC.md](../SPEC.md) - current implementation contract and detailed source-of-truth index.
4. [../RULES.md](../RULES.md) and [../WORKFLOW.md](../WORKFLOW.md) - operating rules and change workflow.
5. [../TESTING.md](../TESTING.md) - how to choose and run the right verification.

Portfolio MRI is diagnosis-first and current-portfolio-first. It is not optimizer-first. Candidate
portfolios are hypotheses to test, not trade recommendations.

## Current Source Of Truth

Use this order when documents disagree:

1. Agent and contributor rules: [../AGENTS.md](../AGENTS.md), [../RULES.md](../RULES.md),
   [../WORKFLOW.md](../WORKFLOW.md).
2. Current implementation: [../SPEC.md](../SPEC.md).
3. Product flow and boundaries:
   [contracts/PRODUCT_FLOW_CONTRACT.md](contracts/PRODUCT_FLOW_CONTRACT.md),
   [../PRODUCT.md](../PRODUCT.md).
4. Screen flow and route responsibilities:
   [contracts/SCREEN_CONTRACTS.md](contracts/SCREEN_CONTRACTS.md),
   [specs/frontend_screen_contracts.md](specs/frontend_screen_contracts.md),
   [../frontend/README.md](../frontend/README.md).
5. Staged review state and persistence boundary:
   [contracts/STAGED_REVIEW_STATE_CONTRACT.md](contracts/STAGED_REVIEW_STATE_CONTRACT.md).
6. Artifacts and generated-output routing:
   [contracts/ARTIFACT_TO_SCREEN_MAP.md](contracts/ARTIFACT_TO_SCREEN_MAP.md),
   [../OUTPUTS.md](../OUTPUTS.md).
7. Data rules: [../DATA.md](../DATA.md) and owning files in [specs/](specs/).
8. Testing and QA: [../TESTING.md](../TESTING.md) and
   [contracts/QA_CONTRACT.md](contracts/QA_CONTRACT.md).

Detailed module behavior belongs in [specs/README.md](specs/README.md) and the owning spec files,
not in top-level indexes.

## Product vs Implementation

Current product truth is the diagnosis journey:

```text
Input Portfolio
-> Portfolio Diagnosis
-> Stress Test Lab
-> Client Fit Check
-> Problem Classification
-> Candidate Launchpad
-> Portfolio Alternatives Builder
-> Candidate Generation
-> Current vs Candidate Comparison
-> Decision Verdict
-> AI Commentary / grounding
-> Monitoring / What Changed
```

The implementation still includes older optimizer/report/scorecard-heavy infrastructure. Treat those
areas as support code, advanced evidence, legacy compatibility, or future/backlog unless a current
contract or spec promotes them into the product journey.

## Specs And Contracts

Use contracts for cross-cutting product and runtime boundaries:

- [contracts/PRODUCT_FLOW_CONTRACT.md](contracts/PRODUCT_FLOW_CONTRACT.md)
- [contracts/SCREEN_CONTRACTS.md](contracts/SCREEN_CONTRACTS.md)
- [contracts/STAGED_REVIEW_STATE_CONTRACT.md](contracts/STAGED_REVIEW_STATE_CONTRACT.md)
- [contracts/ARTIFACT_TO_SCREEN_MAP.md](contracts/ARTIFACT_TO_SCREEN_MAP.md)
- [contracts/INFORMATION_ARCHITECTURE_COPY_CONTRACT.md](contracts/INFORMATION_ARCHITECTURE_COPY_CONTRACT.md)
- [contracts/DOC_SYNC_CONTRACT.md](contracts/DOC_SYNC_CONTRACT.md)
- [contracts/QA_CONTRACT.md](contracts/QA_CONTRACT.md)

Use [specs/README.md](specs/README.md) for module-specific behavior, formulas, data rules,
artifacts, APIs, and workflow details.

## Historical Memory

These folders are traceability and project memory, not current product truth:

- [audits/](audits/) - snapshots, findings, closure evidence, and historical acceptance notes.
- [exec_plans/](exec_plans/) - active and completed work plans.
- [archive/](archive/) - intentionally retired or superseded material.

Read historical files through the current canonical docs above. Historical wording can mention older
optimizer-first, scorecard, recommendation, or advanced-module framing that is no longer current.

## How To Update Docs

Before editing, follow [../WORKFLOW.md](../WORKFLOW.md) and the documentation sync contract:

1. Update the narrowest owning document.
2. Keep indexes short; link to source-of-truth files instead of duplicating formulas or schemas.
3. Keep repository files in English.
4. Do not edit generated outputs unless the task explicitly targets them.
5. Run the fast docs-only gate from [../TESTING.md](../TESTING.md):

```powershell
.\.venv\Scripts\python.exe scripts\verify_docs.py
git diff --check
git status --short
```

