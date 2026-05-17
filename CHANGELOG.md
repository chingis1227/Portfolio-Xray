# CHANGELOG.md

This file is the concise living history of meaningful project changes.

It records what was added, changed, removed, fixed, or deprecated at a project level. It is not a full git log, not a roadmap, and not a replacement for specs, tests, or ExecPlans.

## How To Use

- Add entries only for meaningful project changes: behavior, formulas, data flow, configs, commands, outputs, docs structure, source-of-truth rules, or user-facing workflows.
- Keep each bullet short: one change, one sentence, no implementation essay.
- Do not log every typo, formatting edit, generated-output refresh, or internal refactor with no project-facing effect.
- Link the owning document or module when it helps.
- When an item from [KNOWN_ISSUES.md](KNOWN_ISSUES.md) is fixed, remove it from active issues and add one short `Fixed` entry here if the fix is meaningful.
- For large changes, use this file as the summary and keep detailed rationale in an ExecPlan under `docs/exec_plans/`.

## Entry Format

Use date-based sections unless formal releases are introduced later.

```markdown
Date: YYYY-MM-DD

Category: Added

- Short change summary.

Category: Changed

- Short change summary.

Category: Fixed

- Short change summary.

Category: Removed

- Short change summary.
```

Omit empty categories.

## 2026-05-17

### Added

- Implemented [src/decision_journal.py](src/decision_journal.py): generated-only `decision_journal_v1` JSON/TXT projecting selection, action, monitoring, and comparison; `journal/latest/` and `journal/history/` copies; wired after monitoring in `write_candidate_comparison_outputs`; [tests/test_decision_journal.py](tests/test_decision_journal.py).
- Added [decision journal spec](docs/specs/decision_journal_spec.md) (`decision_journal_v1`): generated-only decision record, journal latest/history layout, pipeline placement after monitoring.
- Implemented [src/monitoring.py](src/monitoring.py): `analysis_snapshot_v1` under `monitoring/latest/` and `history/`, `monitoring_diff_v1` JSON/TXT vs prior snapshot; wired in `write_candidate_comparison_outputs`; [tests/test_monitoring.py](tests/test_monitoring.py).
- Added [monitoring spec](docs/specs/monitoring_spec.md) (`analysis_snapshot_v1`, `monitoring_diff_v1`): What Changed contract, profile projection for current/policy, pipeline placement.
- Implemented [src/action_engine.py](src/action_engine.py): non-executing `action_plan.json` / `.txt` from selection and comparison (weight deltas, trades when `selected_candidate`, 10 bps transaction-cost estimate on turnover half-sum, always written after selection); wired in `write_candidate_comparison_outputs`; [tests/test_action_engine.py](tests/test_action_engine.py).
- Added [action engine spec](docs/specs/action_engine_spec.md) (`action_plan_v1`): Rebalancing Advisor contract, action statuses, transaction-cost model, pipeline placement.
- Implemented [src/selection_engine.py](src/selection_engine.py): formal non-executing `selection_decision.json` / `.txt` from comparison and score artifacts (policy default, composite fallback, No-Trade materiality, five decision statuses); wired in `write_candidate_comparison_outputs`; [tests/test_selection_engine.py](tests/test_selection_engine.py).
- Added [selection engine spec](docs/specs/selection_engine_spec.md) (`selection_decision_v1`): formal decision outcomes, composite selection from health and robustness scores, No-Trade materiality thresholds, neutral decision-support wording.
- Implemented [src/portfolio_health_score.py](src/portfolio_health_score.py): diagnostic `portfolio_health_score.json` / `.txt` from `candidate_comparison.json` (ten components, optional robustness `resilience_reference`); comparison `weight_concentration` from `snapshot_10y.final_weights_total`; [tests/test_portfolio_health_score.py](tests/test_portfolio_health_score.py).
- Added [portfolio health score spec](docs/specs/portfolio_health_score_spec.md) (`portfolio_health_score_v1`): ten weighted components, within-run ranks plus absolute mandate/liquidity checks, optional `resilience_reference` from robustness scorecard, comparison `weight_concentration` prerequisite for Session 13.
- Implemented [src/robustness_scorecard.py](src/robustness_scorecard.py): diagnostic `robustness_scorecard.json` / `.txt` from `candidate_comparison.json` (six components, within-run ranks, mandate cap, stress_report fallback).
- Extended [src/candidate_comparison.py](src/candidate_comparison.py) with per-candidate `diversification` (RC from `snapshot_10y.json`) and automatic scorecard export; [tests/test_robustness_scorecard.py](tests/test_robustness_scorecard.py).
- Added [robustness scorecard spec](docs/specs/robustness_scorecard_spec.md) (`robustness_scorecard_v1`): six weighted components, relative within-run scoring, mandate absolute checks, RC via comparison `diversification` block.
- Added [src/candidate_comparison.py](src/candidate_comparison.py) read-only builder for canonical `candidate_comparison.json` (18-candidate registry, policy/current gating, legacy subset export) and [tests/test_candidate_comparison.py](tests/test_candidate_comparison.py).
- Added [candidate comparison spec](docs/specs/candidate_comparison_spec.md) defining canonical `candidate_comparison.json` under `output_dir_final` (full candidate registry, `current` row, diagnostic-only boundary).
- Added [docs/ROADMAP.md](docs/ROADMAP.md) as the durable phased development roadmap and audit-to-session backlog.
- Added active audit-derived issues to [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for unresolved source-of-truth, config UI, rebalance, encoding, and docs-verification gaps.
- Added [scripts/verify_docs.py](scripts/verify_docs.py), [src/docs_verify.py](src/docs_verify.py), and [tests/test_docs_links.py](tests/test_docs_links.py) for repeatable Markdown link and stale-reference checks.

### Changed

- Extended [src/candidate_comparison.py](src/candidate_comparison.py) and [run_compare_variants.py](run_compare_variants.py) to export robustness scorecard and portfolio health score after each comparison run.
- Refactored [run_compare_variants.py](run_compare_variants.py) to call the shared candidate comparison builder (canonical JSON + legacy `portfolio_comparison.*`).
- Updated [DECISIONS.md](DECISIONS.md) to remove the stale empty-log wording and record the roadmap ownership decision.

### Fixed

- Project-wide documentation hygiene: fixed punctuation/math mojibake in `.cursor/` agents and rules, `docs/`, and engineering Python (`run_report.py`, `src/snapshot.py`, `results_dashboard/app.py`, `src/pdf_reports.py`, `src/config.py`); restored cp1251-mojibake logger text in `run_report.py`.
- Cleaned source-document mojibake in [production_workflow.md](docs/specs/production_workflow.md), [stress_testing_spec.md](docs/specs/stress_testing_spec.md), [metrics_specification.md](docs/specs/metrics_specification.md), and [view_after_optimization_spec.md](docs/specs/view_after_optimization_spec.md).
- Clarified [rebalance.py](src/rebalance.py) threshold docstrings: `threshold_pct` gates on max absolute per-ticker weight drift only; added focused regression tests.
- Rewrote the [stress testing spec](docs/specs/stress_testing_spec.md) stress covariance section so `taxonomy_blend_v1` is the current default and `uniform_legacy` is clearly legacy-only.
- Removed the stale editable `rc_asset_cap_pct` field from the config UI and added focused regression coverage.
- Updated the config UI to separate `analysis_mode`, user-entered `current_weights`, and read-only generated `portfolio_weights.yml` output.

## 2026-05-15

### Added

- Added Portfolio X-Ray v2 with generated `portfolio_xray.json`, common section schema, rule-based hidden-risk flags, archetype caveats, weakness map, and diagnostic-only report wiring.
- Added `analysis_setup_v1` as the resolved Input and Assumptions runtime contract and exported it in run artifacts alongside projected `input_assumptions`.
- Added Portfolio X-Ray summary helpers for report/commentary surfaces, including setup, allocation, risk-contribution, and explanatory diagnostic verdict sections.
- Added Input and Assumptions Layer V1 with `analysis_mode`, `current_weights`, an `input_assumptions` artifact summary, and the canonical [input assumptions spec](docs/specs/input_assumptions_spec.md).
- Added [GLOSSARY.md](GLOSSARY.md) as a living glossary for shared project terminology.
- Added [OUTPUTS.md](OUTPUTS.md) as the root map for generated outputs, report artifacts, output folders, formats, and generated-vs-source boundaries.
- Added [WORKFLOW.md](WORKFLOW.md) as the explicit task workflow from request to implementation, verification, docs sync, project memory, and commit.
- Added [DECISIONS.md](DECISIONS.md) as the concise living decision log for key project decisions and rationale.
- Added [CHANGELOG.md](CHANGELOG.md) as the concise living history for meaningful project changes.
- Added [KNOWN_ISSUES.md](KNOWN_ISSUES.md) as the living register for active issues, model limitations, testing gaps, and technical debt.

### Changed

- Populated [GLOSSARY.md](GLOSSARY.md) with the initial 80 shared project terms.
- Linked decision-log, changelog, and known-issues governance from the top-level documentation maps.
- Simplified top-level documentation routing and clarified source-of-truth links across root docs.

## 2026-05-14

### Added

- Added [DATA.md](DATA.md) as the living data-layer map.
- Added [TESTING.md](TESTING.md) as the project verification framework.

### Changed

- Reorganized project documentation around compact top-level maps and detailed specs under [docs/specs/](docs/specs/README.md).
- Clarified that [docs/DIAGNOSTIC_PRODUCT_CONCEPT.md](docs/DIAGNOSTIC_PRODUCT_CONCEPT.md) is a living product blueprint, not a binding implementation spec.
