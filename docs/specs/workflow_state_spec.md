# Workflow State Specification

This document owns the V1 workflow-state classification used by the Portfolio MRI code migration from CLI/file/report-first runtime toward a diagnosis-first product architecture.

Implementation: `src/workflow_state.py`.

Status: Session 02 migration support. The helper is pure and additive. It does not change CLI behavior, run workflows, read or write generated artifacts, change schemas, change formulas, or replace current orchestration.

## Scope

The workflow-state helper classifies known review intent into one of three target product states:

| State | Meaning |
| --- | --- |
| `diagnosis_only` | The input portfolio / `analysis_subject` is diagnosed and no candidate scope is known for this view. |
| `one_candidate` | Exactly one candidate hypothesis is in scope for comparison against the diagnosed portfolio. |
| `multiple_candidates` | Two or more candidate hypotheses are in scope. This includes current factory profiles such as `core_fast`, `core_v1`, and `default_v1`. |

This is a product workflow-state classification, not an investment decision and not an output contract for generated reports.

## Non-Goals

The workflow-state helper does not:

- validate candidate ids;
- build candidate weights;
- run the candidate factory;
- run comparison;
- read generated artifacts from disk;
- change `run_portfolio_review.py` behavior;
- change `candidate_comparison.json`;
- change `selection_decision.json`;
- change any optimizer, stress, metric, or score formula.

Validation remains owned by candidate factory and comparison modules. Generated output ownership remains in `OUTPUTS.md` and detailed artifact specs.

## Classification Inputs

`resolve_workflow_state()` accepts already-known intent:

- explicit `candidate_count`;
- explicit `candidate_ids`;
- known `factory_profile`;
- existing artifact candidate ids supplied by a caller;
- `skip_candidates`;
- `skip_compare`.

Precedence is:

1. explicit `candidate_count`;
2. explicit `candidate_ids`;
3. supplied existing artifact candidate ids;
4. known factory profile count;
5. diagnosis-only with a warning when candidate scope is unresolved.

The helper keeps a local static map of known factory profile counts so it does not import or execute candidate factory code.

## Current Factory Profile Classification

At Session 02 time, the helper classifies current factory profiles as:

| Factory profile | Candidate count | Workflow state |
| --- | ---: | --- |
| `core_benchmarks` | 3 | `multiple_candidates` |
| `risk_budgets` | 3 | `multiple_candidates` |
| `classic_optimizers` | 7 | `multiple_candidates` |
| `robust_suite` | 3 | `multiple_candidates` |
| `core_v1` | 6 | `multiple_candidates` |
| `core_fast` | 6 | `multiple_candidates` |
| `default_v1` | 16 | `multiple_candidates` |

If factory profiles change, update this spec and the local helper count map in the same focused change.

## Review Plan Adapter

`classify_review_plan()` can inspect an existing `PortfolioReviewPlan` without executing it. It uses duck typing over plan steps and argv so `src.workflow_state` does not depend on `src.portfolio_review_workflow`.

Beginning with code migration Session 03, `PortfolioReviewPlan` also stores a `workflow_state`
assessment directly when built by `build_portfolio_review_plan()`. This keeps the diagnosis-first
state explicit in orchestration without changing the existing CLI command sequence.

The direct plan metadata and `classify_review_plan()` should agree for plans with a candidate
factory step. For `--skip-candidates`, direct plan metadata reports the requested command state
(`diagnosis_only`); a separate caller can pass artifact candidate ids to `resolve_workflow_state()`
when it wants to classify already-existing comparison artifacts.

Expected interpretations:

- default `run_portfolio_review.py` core plan with `core_fast` factory profile -> `multiple_candidates`;
- explicit `--candidates equal_weight` plan -> `one_candidate`;
- explicit comma-separated candidate list with more than one id -> `multiple_candidates`;
- `--skip-candidates` plan that only compares existing artifacts -> `diagnosis_only` with warning `comparison_candidate_scope_unknown`, unless a caller separately supplies artifact candidate ids to `resolve_workflow_state()`.

## Migration Boundary

Session 02 only adds classification. Later sessions may wire this state into orchestration metadata or product artifacts, but they must do so without changing current CLI behavior unless a focused session explicitly updates and tests that behavior.

Target later uses:

- diagnosis-only state after `analysis_subject` materialization;
- one-candidate state for Portfolio Alternatives Builder output;
- multiple-candidate state for shortlist or advanced factory runs;
- product-facing summaries that avoid showing the full research table as the default MVP experience.

## Verification

Focused tests live in `tests/test_workflow_state.py`.

Recommended checks for changes to this helper:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_workflow_state.py tests\test_portfolio_review_workflow.py
.\.venv\Scripts\python.exe scripts\verify_docs.py
```

The docs verifier may still report unrelated archived legacy documentation links. Do not repair archived documentation in a workflow-state session unless that cleanup is explicitly in scope.
