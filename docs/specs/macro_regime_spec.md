# Macro Regime Diagnostics Specification

This document owns the high-level contract for macro regime diagnostics. The detailed formulas, labels, gating, artifacts, and historical notes live in [stress_testing_spec.md](stress_testing_spec.md).

## Scope

`stress_report.json.macro_regime_diagnostics` is diagnostic-only. It does not affect optimizer weights, mandate gates, stress pass/fail, raw 5Y/10Y beta outputs, or weight release.

## Method

The current method is `macro_two_axis_v1`, a monthly two-axis classifier:

- `growth_score`
- `inflation_score`
- primary regime label
- transition flags and transition reasons
- coverage and confidence metadata

Primary regime labels are:

- `goldilocks`
- `reflation`
- `stagflation`
- `recession_disinflation`

Legacy labels and counts may be preserved for backward compatibility where implemented.

## Data Sources And Look-Ahead Protection

Indicators flow through a layered source resolver:

- FRED
- Yahoo
- official CSV
- official API
- keyed API
- manual CSV

Missing sources degrade `coverage_tier` and `confidence_level` without crashing the report path. The classifier applies a 1-month publication lag for look-ahead protection.

## Regime Analytics

Per-regime analytics are gated by observation count and remain diagnostic-only. The regime label history may be longer than the portfolio-facing analytics window; portfolio-facing regime statistics use the documented overlap ending at `analysis_end`.

Detailed gating thresholds, shrinkage behavior, labels, CSV exports, JSON fields, quality checks, and commentary requirements are governed by [stress_testing_spec.md](stress_testing_spec.md).
