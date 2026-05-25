# Problem Classification Specification

This document owns the V1 deterministic Problem Classification artifact for the diagnosis-first Portfolio MRI migration.

Implementation: `src/problem_classification.py`.

Canonical artifact: `problem_classification.json`.

Status: implemented as an additive diagnostic artifact in code migration Session 04. It is a thin evidence translation layer over existing Portfolio X-Ray and Stress Test Lab artifacts.

## Scope

Problem Classification converts existing deterministic evidence into a small set of user-understandable portfolio problems and reasonable paths to test.

It reads:

- `portfolio_xray.json`
- `stress_report.json`

It writes:

- `problem_classification.json`

It does not:

- calculate new metrics;
- change Portfolio X-Ray or stress formulas;
- optimize weights;
- build candidate portfolios;
- change candidate factory behavior;
- rank candidates;
- produce Selection Engine decisions;
- rename existing schemas or JSON fields;
- issue trade instructions.

## Artifact Contract

Top-level shape:

```json
{
  "schema_version": "problem_classification_v1",
  "diagnostic_only": true,
  "generated_at": "ISO-8601 UTC timestamp",
  "analysis_end": "YYYY-MM-DD",
  "source_artifacts": {
    "portfolio_xray": "portfolio_xray.json",
    "stress_report": "stress_report.json"
  },
  "problems": [],
  "summary": {
    "n_problems": 1,
    "primary_problem_id": "high_volatility",
    "current_portfolio_acceptable": false
  },
  "warnings": []
}
```

Each `problems[]` row contains:

| Field | Meaning |
| --- | --- |
| `problem_id` | Stable machine id. |
| `label` | Client-understandable English label. |
| `severity` | `low`, `moderate`, `high`, or `unknown`. |
| `confidence` | `low`, `medium`, or `high`, derived from source evidence confidence where available. |
| `evidence` | Source artifact/section/field references and compact values or summaries. |
| `reasonable_paths_to_test` | Product hypotheses for Candidate Launchpad; these are not portfolios and contain no weights. |

## V1 Problem IDs

V1 supports these labels:

- `high_drawdown_risk`
- `high_volatility`
- `high_concentration`
- `poor_diversification`
- `weak_hedge_behavior`
- `weak_crisis_resilience`
- `high_equity_beta`
- `data_review_required`
- `current_portfolio_acceptable`

The artifact returns at most three problem rows. If no high-priority problem is detected by the deterministic rules, it emits `current_portfolio_acceptable` with low severity.

## Evidence Rules

Problem Classification may use existing evidence from:

- Portfolio X-Ray `weakness_map`;
- Portfolio X-Ray `risk_diagnostics`;
- Portfolio X-Ray `asset_allocation`;
- Portfolio X-Ray `factor_exposure`;
- stress conclusions;
- stress scorecard status and confidence.

Every problem row must include at least one evidence reference. The classifier must expose source-missing warnings instead of implying full confidence.

## Product Boundary

Problem Classification is diagnostic-only. It translates evidence into improvement directions for later Candidate Launchpad cards. It does not decide that a user should rebalance and does not select a candidate.

Reasonable paths such as "Reduce volatility" or "Improve diversification" are hypotheses to test, not recommendations or portfolios.

## Workflow Integration

`run_report.py` writes `problem_classification.json` after `portfolio_xray.json` and `stress_report.json` are available. This applies to normal report outputs, `analysis_subject` materialization, and candidate report folders because all use the same report backend.

The artifact is included in the output manifest as `problem_classification`.

## Verification

Focused tests:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_problem_classification.py
```

Recommended adjacent regression checks:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_problem_classification.py tests\test_portfolio_review_workflow.py
.\.venv\Scripts\python.exe run_portfolio_review.py --dry-run
```
