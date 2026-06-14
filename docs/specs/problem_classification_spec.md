# Problem Classification Specification

This document owns the V1 deterministic Problem Classification artifact for the diagnosis-first Portfolio MRI migration.

**Current contract (V3):** [block_4_diagnosis_v3_spec.md](block_4_diagnosis_v3_spec.md) - primary schema `problem_classification_v3`; writer `src/block_4/diagnosis_builder.py`. V3 requires `next_diagnostic_step` so Block 4 always hands off a next test, monitoring/data-improvement step, or reference benchmark comparison without making a rebalance recommendation.

Implementation: `src/block_4/diagnosis_builder.py` (V3 canonical); `src/problem_classification.py` (legacy unit tests).

Canonical artifact: `problem_classification.json`.

Status: **legacy V1** — canonical contract is [block_4_diagnosis_v3_spec.md](block_4_diagnosis_v3_spec.md). Production writer: `src/block_4/diagnosis_builder.py`. The current product validator is v3; the old V1 artifact remains unit-test-only.

## Scope

Problem Classification converts existing deterministic evidence into a small set of user-understandable portfolio problems and reasonable paths to test.

It reads:

- `portfolio_xray.json`
- `stress_report.json`

It writes:

- `problem_classification.json`

It does not:

- calculate new metrics;
- change Portfolio Diagnosis or stress formulas;
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
  "warnings": [],
  "hedge_gap_source": "hedge_gap_analysis_v1",
  "stress_scorecard_source": "current_portfolio_stress_scorecard_v1"
}
```

`hedge_gap_source` is optional when neither v1 nor legacy hedge-gap evidence was evaluated (e.g. missing `stress_report.json`).

`stress_scorecard_source` records which stress scorecard path was used for worst-scenario problems:
`current_portfolio_stress_scorecard_v1` (primary) or `stress_scorecard_v1` / `stress_conclusions` (legacy fallback).

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

- Portfolio Diagnosis product block `block_2_6_portfolio_weakness_map` (canonical pre-stress weakness hypotheses; canonical `risk_type` → `problem_id` map in `src/problem_classification.py`);
- Portfolio Diagnosis `risk_diagnostics`;
- Portfolio Diagnosis `asset_allocation`;
- Portfolio Diagnosis `factor_exposure`;
- Block 3.4 `current_portfolio_stress_scorecard_v1` on `stress_report.json` (primary stress scorecard path), including `problem_classification_signals` and worst-scenario selectors;
- stress conclusions and legacy `stress_scorecard_v1` (fallback only when Block 3.4 is missing or `block_status = unavailable`);
- Block 3.3 `hedge_gap_analysis_v1` on `stress_report.json` (primary hedge-gap path).

### Hedge gap (Block 3.3 v1 primary)

When `stress_report.json` contains `hedge_gap_analysis_v1` with `version = hedge_gap_analysis_v1` and `block_status` is not `unavailable`, Problem Classification evaluates hedge weakness from v1 only:

- `summary.protection_profile` (`mostly_weak_protection`, mixed profile with weak `main_hedge_gap`, …);
- `summary.main_hedge_gap.protection_status` (`weak_protection`, `no_protection`, …);
- count of `by_risk_type[]` rows in weak/no-protection states.

Evidence for `weak_hedge_behavior` must cite `source_section: hedge_gap_analysis_v1` and include compact v1 summary fields (main gap scenario, offset ratio, protection status, `reason_codes`).

**Legacy fallback:** use `stress_conclusions.hedge_gap_status` only when v1 is missing or `block_status = unavailable`. Legacy path sets `evidence_path: legacy_fallback`.

Top-level `hedge_gap_source` on `problem_classification.json` records which path was used: `hedge_gap_analysis_v1` or `stress_conclusions.hedge_gap_status`.

### Stress scorecard (Block 3.4 v1 primary)

When `stress_report.json` contains `current_portfolio_stress_scorecard_v1` with `version = current_portfolio_stress_scorecard_v1` and `block_status` is not `unavailable`, Problem Classification evaluates `weak_crisis_resilience` and `high_drawdown_risk` from Block 3.4 worst selectors (and `problem_classification_signals` for compact hints). Evidence must cite `source_section: current_portfolio_stress_scorecard_v1`.

**Legacy fallback:** use `stress_conclusions.worst_synthetic_scenario` / `worst_historical_episode` and legacy mandate rollup on `stress_scorecard_v1.overall_status` only when Block 3.4 is missing or unavailable. Legacy stress paths set `evidence_path: legacy_fallback`.

Mandate-mode `overall_status` rollup still reads legacy `stress_scorecard_v1` even when Block 3.4 is primary (`evidence_path: legacy_mandate_rollup`).

Top-level `stress_scorecard_source` records which path was used: `current_portfolio_stress_scorecard_v1` or `stress_scorecard_v1`.

Every problem row must include at least one evidence reference. The classifier must expose source-missing warnings instead of implying full confidence.

Legacy `sections.weakness_map` is **not** a product source for Problem Classification after Block 2.6 v2 Session 07 (it remains stress-coupled for formatters/golden compatibility only). When present, `problem_classification.json` includes `weakness_map_source: "block_2_6_portfolio_weakness_map"`.

## Product Boundary

Problem Classification is diagnostic-only. It translates evidence into improvement directions for later Candidate Launchpad cards. It does not decide that a user should rebalance and does not select a candidate.

Reasonable paths such as "Reduce volatility" or "Improve diversification" are hypotheses to test, not recommendations or portfolios.

Current V3 `next_diagnostic_step` keeps this boundary explicit:

- actionable diagnoses use a targeted hypothesis test;
- mixed or acceptable outcomes use Equal Weight and Risk Parity only as reference benchmark tests;
- data-quality outcomes use a data-improvement step and do not emit unreliable benchmark comparisons.

## Workflow Integration

`run_report.py` writes `problem_classification.json` after `portfolio_xray.json` and `stress_report.json` are available. This applies to normal report outputs, `analysis_subject` materialization, and candidate report folders because all use the same report backend.

The artifact is included in the output manifest as `problem_classification`.

## Verification

Focused tests:

```text
python -m pytest tests/test_problem_classification.py tests/test_block_4_decision_entry_contract.py
```

Product contract (current v3): `problem_classification_v3_product_contract_violations` / `check_problem_classification_v3` in `scripts/core_mvp_validation_contract.py`; enforced on live diagnosis runs via `validate_live_core_artifacts` (`diagnosis_only`, `product_one_candidate`). V1 validators removed Session 14; current v3 also requires `next_diagnostic_step`.

Recommended adjacent regression checks:

```text
python -m pytest tests/test_problem_classification.py tests/test_candidate_launchpad.py tests/test_block_4_decision_entry_contract.py tests/test_live_core_e2e_validation.py -q
python run_portfolio_review.py
python scripts/verify_live_core_e2e.py --profile diagnosis_only
```
