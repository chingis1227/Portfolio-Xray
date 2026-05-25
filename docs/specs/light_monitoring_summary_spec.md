# Light Monitoring / What Changed Summary Spec

This spec owns the additive product-facing Monitoring / What Changed projection
for the diagnosis-first Portfolio MRI flow.

The implemented artifact is `what_changed_summary.json`, written by
`src/light_monitoring_summary.py` after `monitoring_diff.json` is available in
the candidate comparison / decision-package pipeline.

## Status

Implemented as an additive projection:

- module: `src/light_monitoring_summary.py`
- artifact: `{output_dir_final}/what_changed_summary.json`
- schema version: `what_changed_summary_v1`
- tests: `tests/test_light_monitoring_summary.py`

This artifact does not replace `monitoring_diff.json`, monitoring snapshots, or
monitoring history. It is a compact product layer over existing monitoring
evidence.

## Product role

Target product architecture ends with:

```text
AI Commentary -> Monitoring / What Changed
```

In the current implementation, `what_changed_summary.json` gives a small
diagnosis-first product summary backed by `monitoring_diff.json`. It can mention
whether there is a first snapshot, changed risk contributor, changed worst
scenario, changed macro regime, changed mandate status, decision/action changes,
warnings, and review/retest triggers.

## Inputs

Required:

- `monitoring_diff.json`

Optional context:

- `decision_verdict.json`
- `problem_classification.json`
- `current_vs_candidate.json`

Optional context is copied or referenced only. Missing optional context must not
block writing the summary.

## Artifact shape

Top-level fields:

- `schema_version`: `what_changed_summary_v1`
- `diagnostic_only`: `true`
- `generated_at`: UTC timestamp
- `summary_status`: `available` or `missing_monitoring`
- `headline`: compact product-facing summary sentence
- `primary_profile_id`: copied from monitoring diff when available
- `current_analysis_end`: copied from monitoring diff
- `prior_analysis_end`: copied from monitoring diff
- `problem_ids`: compact problem ids from Problem Classification, if available
- `decision_verdict_id`: current product-facing verdict id, if available
- `current_vs_candidate_mode`: current-vs-candidate view mode, if available
- `what_changed_lines`: product-level change lines
- `retest_triggers`: stable trigger ids derived from existing monitoring fields
- `source_artifacts`: source presence map
- `guardrails`: booleans proving this layer does not change monitoring schema,
  write history, calculate metrics, or execute trades
- `warnings`: propagated missing-source or monitoring warnings

## What changed lines

Each `what_changed_lines[]` item contains:

- `category`
- `message`
- `evidence_refs`
- `retest_trigger`

Evidence references must point to existing source artifacts and field paths.

Implemented categories include:

- `baseline`
- `risk_contributor`
- `stress_behavior`
- `market_context`
- `mandate`
- `decision`
- `action`
- `review_trigger`
- `warning`
- `evidence_gap`
- `decision_verdict`
- `no_material_change`

## Retest triggers

Retest triggers are product-level hints for what a user or future workflow may
review next. They are not trades, alerts, or scheduler jobs.

Implemented trigger ids:

- `top_risk_contributor_changed`
- `worst_scenario_changed`
- `macro_regime_changed`
- `mandate_status_changed`
- `decision_status_changed`
- `action_status_changed`
- `rebalance_trigger`
- `monitoring_warning`
- `monitoring_evidence_degraded`

## Integration

`src.candidate_comparison.write_candidate_comparison_outputs()` writes
`what_changed_summary.json` after `monitoring_diff.json` has been written and
loaded, before Decision Journal and decision-package summary generation.

The existing monitoring writer still owns:

- `monitoring/latest/analysis_snapshot.json`
- `monitoring/history/analysis_snapshot_{analysis_end}.json`
- `monitoring_diff.json`
- optional `monitoring_diff.txt`

This projection does not write to monitoring history.

## Non-goals

- no change to `monitoring_diff_v1`
- no change to snapshot retention semantics
- no scheduler, email, or notification system
- no new metric formulas or thresholds
- no broker/trade execution
- no generated-output cleanup

## Verification

Required focused checks:

```bash
python -m pytest tests/test_light_monitoring_summary.py tests/test_monitoring.py
python -m pytest tests/test_candidate_comparison_contract.py
python run_portfolio_review.py --dry-run
```

Use `scripts/verify_docs.py` for documentation link checks. If archived legacy
documentation has stale links, record the failure as unrelated unless the task
explicitly targets archive repair.
