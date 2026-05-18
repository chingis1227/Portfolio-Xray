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

## 2026-05-18

### Added

- Closed [post-audit MVP stabilization plan](docs/exec_plans/2026-05-17_post_audit_mvp_stabilization_plan.md) Session 11: Phase 7 (`RM-700`–`RM-710`) complete; broad verification (`462` pytest passes, docs verify, generated-output QA scan).
- Added file-first MVP workflow orchestration ([run_mvp_workflow.py](run_mvp_workflow.py), [src/mvp_workflow.py](src/mvp_workflow.py), [tests/test_mvp_workflow.py](tests/test_mvp_workflow.py)): thin wrapper for `input -> diagnosis -> comparison -> action`; documented in [docs/operational_runbook.md](docs/operational_runbook.md) (MVP stabilization Session 10).
- Added offline MVP pipeline smoke test ([tests/test_mvp_pipeline_offline.py](tests/test_mvp_pipeline_offline.py), [tests/mvp_offline_fixtures.py](tests/mvp_offline_fixtures.py)): synthetic snapshots, network guards, and decision-package JSON chain verification; documented in [TESTING.md](TESTING.md) (MVP stabilization Session 09).

### Changed

- Updated [README](README.md) and [ARCHITECTURE](ARCHITECTURE.md) to document supported partial utility UIs (`config_ui/`, `results_dashboard/`) vs full product workspace TBD.

### Fixed

- Removed active issue `KI-2026-05-17-004` after partial utility UI status was synced in top-level docs (MVP stabilization Session 11).
- Removed active issue `KI-2026-05-17-020` after the offline MVP smoke test landed.

## 2026-05-17

### Added

- Added [repeat project MVP readiness audit](docs/audits/2026-05-17_repeat_project_mvp_readiness_audit.md) and active [post-audit MVP stabilization plan](docs/exec_plans/2026-05-17_post_audit_mvp_stabilization_plan.md), with roadmap/register/known-issue handoff for Sessions 01-11.
- Implemented [src/regret_analysis.py](src/regret_analysis.py): `regret_analysis_v1` JSON/TXT, stress-scenario regret vs best available, reference profiles favored/current/benchmark, Tier B CAGR slice, wired after Pareto in `write_candidate_comparison_outputs`, decision-package Regret section; [tests/test_regret_analysis.py](tests/test_regret_analysis.py) (post-audit Session 19).
- Added [regret analysis spec](docs/specs/regret_analysis_spec.md): `regret_analysis_v1` contract, stress-scenario regret vs best available, reference profiles favored/current/benchmark, pipeline placement after Pareto (post-audit Session 18); decision `DEC-2026-05-17-011`.
- Implemented [src/pareto_dominance.py](src/pareto_dominance.py): `pareto_dominance_v1` JSON/TXT, strict Pareto dominance on comparison metrics, wired after assumption sensitivity in `write_candidate_comparison_outputs`, decision-package section; optional `es_95` in comparison metrics; [tests/test_pareto_dominance.py](tests/test_pareto_dominance.py) (post-audit Session 17).
- Added [pareto dominance spec](docs/specs/pareto_dominance_spec.md): `pareto_dominance_v1` contract, strict Pareto objectives, pairwise dominance rules, pipeline placement after assumption sensitivity (post-audit Session 16); decision `DEC-2026-05-17-010`.
- Implemented [src/assumption_sensitivity.py](src/assumption_sensitivity.py): `assumption_sensitivity_v1` JSON/TXT, Tier A/B variant grid, wired after trade-off in `write_candidate_comparison_outputs`, decision-package summary section; [tests/test_assumption_sensitivity.py](tests/test_assumption_sensitivity.py) (post-audit Session 15).
- Added [assumption sensitivity spec](docs/specs/assumption_sensitivity_spec.md): `assumption_sensitivity_v1` contract, Tier A selection-weight variants, Tier B evidence ranks, stability bands, pipeline placement after trade-off (post-audit Session 14); decision `DEC-2026-05-17-009`.
- Implemented [src/tradeoff_and_model_risk.py](src/tradeoff_and_model_risk.py): `tradeoff_explanation_v1` and `model_risk_diagnostics_v1` after selection in `write_candidate_comparison_outputs`; decision package and journal integration; [tests/test_tradeoff_and_model_risk.py](tests/test_tradeoff_and_model_risk.py) (post-audit Session 13).
- Added [trade-off and model risk spec](docs/specs/tradeoff_and_model_risk_spec.md): `tradeoff_explanation_v1` and `model_risk_diagnostics_v1` contracts, warning catalog, pipeline placement after selection (post-audit Session 12); decision `DEC-2026-05-17-008`.
- Implemented candidate factory (post-audit Session 11): [run_candidate_factory.py](run_candidate_factory.py), [src/candidate_factory.py](src/candidate_factory.py), profiles and skip-existing orchestration, `candidate_factory_run.json` / `.txt`, optional `--then-compare`; [tests/test_candidate_factory.py](tests/test_candidate_factory.py).
- Added [candidate factory spec](docs/specs/candidate_factory_spec.md): V1 orchestration profiles, registry-to-script table, `candidate_factory_run_v1` contract, and planned `run_candidate_factory.py` CLI (post-audit Session 10; implementation Session 11); decision `DEC-2026-05-17-007`.
- Implemented current-vs-policy workflow (post-audit Session 09): `run_report.py --materialize-current`, sidecar resolution in [src/candidate_comparison.py](src/candidate_comparison.py), [src/current_vs_policy.py](src/current_vs_policy.py) status artifacts, reporting/selection/action gating; [tests/test_current_vs_policy_workflow.py](tests/test_current_vs_policy_workflow.py).
- Added [current vs policy workflow spec](docs/specs/current_vs_policy_workflow_spec.md): V1 combined workflow (policy on Main + `current_portfolio/` sidecar), No-Trade actionability matrix, skip reason codes, and `current_vs_policy_status_v1` contract (post-audit Session 08).
- Added [audit register](docs/audits/README.md) and [ExecPlan register](docs/exec_plans/README.md) to keep audit history, plan history, and the active plan pointer in concise documentation indexes.
- Added [post-audit stabilization and analytics ExecPlan](docs/exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md) to guide separate future sessions for docs sync, report integration, workflow hardening, candidate factory, and new analytics.
- Added the post-session deep system audit after Sessions 01-20, covering concept alignment, docs/code drift, Post-closure triage, and Main-vs-robust optimizer boundaries.
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
- Added [decision package reporting spec](docs/specs/decision_package_reporting_spec.md) and [src/decision_package_reporting.py](src/decision_package_reporting.py): compact `decision_package_summary` TXT/JSON, `report.txt` append, comparison CLI paths, optional decision-package PDF; [tests/test_decision_package_reporting.py](tests/test_decision_package_reporting.py).

### Changed

- Completed MVP stabilization Session 08 (`RM-707`): regenerated representative Main/EW/RP outputs, added generated-output QA scan/test, English EW/RP comparison labels, and FRED CSV fallback when `pandas_datareader` is unavailable.
- Completed MVP stabilization Session 06 (`RM-705`): time-to-recovery now follows the max-drawdown peak/trough path, counts monthly/trading observations by index position, and treats no-drawdown windows as recovered with `ttr = 0`.
- Completed MVP stabilization Session 07 (`RM-706`): factor multicollinearity diagnostics now emit `assessment_en`; stress commentary prefers `assessment_en` and legacy-reads `assessment_ru` from older reports only.
- Completed MVP stabilization Session 05 (`RM-704`): NaN-safe data policy docs now define when `n_months_cash_fallback` is counted after risk-weight redistribution.
- Completed MVP stabilization Session 04 (`RM-703`): monthly return-panel cache keys now include resolved asset-currency metadata so FX-adjusted cached panels invalidate after `assets.yml` currency changes.
- Completed MVP stabilization Session 03 (`RM-702`): synced risk-free and cash policy docs/tests so USD/EUR defaults are explicit and unsupported non-USD currencies require configured cash and risk-free sources.
- Completed MVP stabilization Session 02 (`RM-701`): synced `README.md`, `ARCHITECTURE.md`, and `PRODUCT.md` so implemented file-first factory, current-vs-policy, trade-off/model-risk, assumption sensitivity, Pareto, regret, and decision-package outputs are not described as target/TBD work.
- Closed post-audit stabilization plan (Session 20, `RM-623`): marked [post-audit ExecPlan](docs/exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md) completed, updated [docs/ROADMAP.md](docs/ROADMAP.md) and [exec plan register](docs/exec_plans/README.md), synced [PRODUCT.md](PRODUCT.md) comparison targets with implemented factory/current-vs-policy/Pareto/regret file-first artifacts.
- Cross-linked current-vs-policy workflow spec from candidate comparison, input assumptions, selection, action, reporting outputs, OUTPUTS, and spec index (post-audit Session 08).
- Cleaned source/generator text defaults across optimization/report/PDF/config/docs paths so project artifacts use English and common mojibake markers are removed from source.
- Synced detailed decision-package specs so reporting, comparison, selection, action, monitoring, and journal contracts describe the implemented V1 artifact chain instead of stale future/TBD neighbors.
- Synced top-level docs after the post-session audit: `README.md`, `AGENTS.md`, `SPEC.md`, `PRODUCT.md`, and `ARCHITECTURE.md` now treat the V1 decision pipeline as implemented file-first artifacts while keeping full UI/workspace and advanced analytics as future work.
- Updated [docs/ROADMAP.md](docs/ROADMAP.md), [DECISIONS.md](DECISIONS.md), and [KNOWN_ISSUES.md](KNOWN_ISSUES.md) with post-session next-stage priorities and unresolved stabilization issues.
- Extended [src/candidate_comparison.py](src/candidate_comparison.py) and [run_compare_variants.py](run_compare_variants.py) to export robustness scorecard and portfolio health score after each comparison run.
- Refactored [run_compare_variants.py](run_compare_variants.py) to call the shared candidate comparison builder (canonical JSON + legacy `portfolio_comparison.*`).
- Updated [DECISIONS.md](DECISIONS.md) to remove the stale empty-log wording and record the roadmap ownership decision.

### Fixed

- Closed `KI-2026-05-17-019` by emitting `assessment_en` from factor multicollinearity diagnostics and keeping `assessment_ru` as legacy-read compatibility in stress commentary only.
- Closed `KI-2026-05-17-007` after representative output regeneration and automated QA scan passed; opened `KI-2026-05-18-001` for the residual decision-package PDF Pandoc failure.
- Closed `KI-2026-05-17-018` by adding focused recovered/unrecovered/no-drawdown TTR regressions and correcting monthly/daily recovery semantics.
- Closed `KI-2026-05-17-017` by counting actual NaN-safe cash fallback months and adding focused regressions for missing-risk residual cash usage.
- Closed `KI-2026-05-17-016` by adding an asset-currency metadata fingerprint to monthly cache keys and focused regression coverage for currency-metadata invalidation.
- Closed `KI-2026-05-17-015` by aligning risk-free/cash policy wording with config resolver behavior and adding focused regressions for EUR defaults and unsupported-currency explicit configuration.
- Closed `KI-2026-05-17-014` by removing top-level implemented-as-TBD wording for the file-first V1 decision artifact chain.
- Closed `KI-2026-05-17-006` by assigning Selection Engine V1 the unique decision ID `DEC-2026-05-17-006` and updating the session handoff references.
- Closed `KI-2026-05-17-005` by removing stale top-level wording that described implemented Health Score, Selection/No-Trade, Monitoring, and Decision Journal artifacts as target/TBD.
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
