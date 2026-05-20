# Project Roadmap

This file is the durable roadmap and backlog for Portfolio X-Ray & Optimization Terminal /
Portfolio MRI. It turns the product concept, audit findings, and current implementation state into
an ordered development sequence.

This is a planning document. It does not override [SPEC.md](../SPEC.md), [RULES.md](../RULES.md),
[OUTPUTS.md](../OUTPUTS.md), [TESTING.md](../TESTING.md), or the detailed specs under
[docs/specs/](specs/README.md). Product ideas become binding only after the relevant source-of-truth
spec and implementation are updated.

## Current Development Rule

Post-audit stabilization (RM-610 through RM-623, Sessions 02–20) is **complete** as of 2026-05-17.
The file-first V1 decision pipeline is implemented end-to-end through `write_candidate_comparison_outputs`.
Do not add new major analytics without an accepted spec and roadmap row. Current active backlog:

```text
Post-portfolio-first stabilization (RM-900 -> RM-911) closed as of 2026-05-19
Portfolio X-Ray diagnostics deepening (RM-930 -> RM-939): **closed** as of 2026-05-20 (Session 09).
Portfolio X-Ray post-audit governance (RM-940 -> RM-950): **closed** as of 2026-05-20 (Session 10).
Baseline: [Portfolio X-Ray Baseline Snapshot](audits/2026-05-20_portfolio_xray_baseline_snapshot.md).
Deferred follow-up: factory resumability / progress logging (RM-921).
```

New diagnostic layers must remain non-binding unless a canonical spec explicitly changes Selection or
policy release behavior.

**Not a logic blocker:** the file-first MVP core is usable when partial vs full candidate coverage
is read from `candidate_factory_run.json` and comparison row `status`. Address RM-920+ before serious
UI/productization so the product does not depend on one heavy command finishing every time.

Completed plan: [Portfolio-First Transition Plan](exec_plans/2026-05-18_portfolio_first_transition_plan.md)
(Sessions 01-09). Its source-of-truth correction is that the main product flow starts from
`analysis_subject` diagnostics, not generated policy optimization. The old policy engine is preserved
as legacy or archived infrastructure and is excluded from the default portfolio-first path unless a
future canonical spec reactivates it.

Completed plan: [Post-Portfolio-First Stabilization Plan](exec_plans/2026-05-19_post_portfolio_first_stabilization_plan.md)
(Sessions 00-11, closed 2026-05-19). Stabilized the portfolio-first path: subject metadata, candidate
freshness, decision reliability, methodology alignment, regime metrics, monitoring honesty, and
portfolio-first PDF scope.

Completed plan: [Portfolio X-Ray Diagnostics Deepening Plan](exec_plans/2026-05-19_portfolio_xray_diagnostics_deepening_plan.md)
(Sessions 00-09, closed 2026-05-20). Deepened the current-portfolio diagnostic layer: data cutoff,
X-Ray evidence completeness, VaR / ES, portfolio metrics, hidden risk, weakness map, archetype,
report productization, and operational portfolio-first review modes.

Completed plan: [Portfolio X-Ray Post-Audit Roadmap](exec_plans/2026-05-20_portfolio_xray_post_audit_roadmap.md)
(Sessions 00-10, closed 2026-05-20). Made Block 2 audit-grade for governance scope: spec-owned thresholds,
section provenance, factor inference surfacing, multi-window metrics, layer spec, concentration, golden
contract tests, and baseline snapshot. Methodology map and baseline:
[2026-05-20_portfolio_xray_methodology_map.md](audits/2026-05-20_portfolio_xray_methodology_map.md),
[2026-05-20_portfolio_xray_baseline_snapshot.md](audits/2026-05-20_portfolio_xray_baseline_snapshot.md).

## Status Values

Use these statuses for roadmap items:

| Status | Meaning |
| --- | --- |
| Done | Implemented or documented, with the relevant verification recorded. |
| In progress | Work has started and must be resumed before starting dependent items. |
| Planned | Accepted as future work, but not started in source. |
| Blocked | Cannot proceed until a user decision, dependency, or contradiction is resolved. |
| Deferred | Intentionally postponed; not part of the near-term sequence. |
| TBD | Needs a spec or decision before implementation can be planned. |

## Phase 0: Stabilize Current Source Of Truth

Goal: make the current repository harder to misunderstand before adding scores,
recommendations, monitoring, or a full product UI.

Exit condition: a new developer can read root docs, specs, and utility UI descriptions without
confusing current behavior with future product goals.

| ID | Status | Session | Work item | Prerequisites | Owning docs/code | Artifact or output | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RM-000 | Done | Session 01 | Create this durable roadmap and register unresolved audit issues. | 2026-05-17 audit completed. | [Session plan](exec_plans/2026-05-17_project_development_session_plan.md), [full audit](audits/2026-05-17_full_project_system_audit.md), [known issues](../KNOWN_ISSUES.md), [decisions](../DECISIONS.md) | `docs/ROADMAP.md`, updated issue and decision registers | Search all `AUD-` IDs and confirm each is fixed, registered, or deferred here. |
| RM-001 | Done | Session 02 | Fix stale stress covariance documentation so `taxonomy_blend_v1` is clearly current default and `uniform_legacy` is legacy. | RM-000. | [stress testing spec](specs/stress_testing_spec.md), [stress.py](../src/stress.py), [stress covariance taxonomy](../src/stress_covariance_taxonomy.py) | Updated stress spec; no runtime code change required | `tests/test_stress_covariance_taxonomy.py -q` passed; stale-reference search confirms legacy scalars are only in legacy context. |
| RM-002 | Done | Session 03 | Remove or correct the stale `rc_asset_cap_pct` config UI surface. | RM-000. | [config form](../config_ui/templates/config_form.html), [config UI app](../config_ui/app.py), [feasibility constraints spec](specs/feasibility_constraints_spec.md), [portfolio construction policy](specs/portfolio_construction_policy.md) | Removed editable config UI field and added focused regression coverage. | Search `rc_asset_cap_pct`; focused config UI tests passed. |
| RM-003 | Done | Session 04 | Fix config UI `analysis_mode`, `current_weights`, and generated-weight semantics. | RM-002 recommended first. | [config UI app](../config_ui/app.py), [config form](../config_ui/templates/config_form.html), [input assumptions spec](specs/input_assumptions_spec.md), [config schema](../src/config_schema.py) | Config UI distinguishes current weights from generated policy weights and shows generated policy weights as read-only output. | `tests/test_config_ui_input_modes.py`, `tests/test_config_ui_rc_cap_removed.py`, `tests/test_input_assumptions.py`, and `tests/test_config_weights_sync.py` passed. |
| RM-004 | Planned | Session 01 or later docs cleanup | Clarify that partial utility UIs exist for config editing and read-only result viewing, while full product workspace remains TBD. | RM-000. | [README](../README.md), [SPEC](../SPEC.md), [PRODUCT](../PRODUCT.md), [ARCHITECTURE](../ARCHITECTURE.md), [DESIGN](../DESIGN.md) | Consistent top-level wording | Stale-reference search for UI status wording. |
| RM-005 | Done | Session 05 | Fix rebalance threshold semantics or implement explicit turnover logic. | RM-000. | [rebalance.py](../src/rebalance.py), [run_rebalance.py](../run_rebalance.py), [test_rebalance_threshold.py](../tests/test_rebalance_threshold.py) | Docstrings state max per-ticker drift gate only; turnover threshold deferred to Action/No-Trade sessions | `tests/test_rebalance_threshold.py -q` passed (2 tests); stale-reference search for turnover-threshold overstatement in `src/rebalance.py`. |
| RM-006 | Done | Session 06 | Clean source-document mojibake in a focused documentation hygiene pass. | RM-000. | Source docs/specs, especially [production workflow spec](specs/production_workflow.md) | Rewrote `production_workflow.md` in English; normalized encoding artifacts in stress, metrics, and view-after-optimization specs | Targeted mojibake codepoint scan on `docs/specs/*.md` passed. |
| RM-007 | Done | Session 07 | Add lightweight Markdown link and stale-reference verification. | RM-000. | [TESTING](../TESTING.md), [verify_docs.py](../scripts/verify_docs.py), [docs_verify.py](../src/docs_verify.py), [test_docs_links.py](../tests/test_docs_links.py) | `scripts/verify_docs.py` plus pytest coverage for source Markdown links, forbidden stale paths, and removed config UI fields | `python scripts/verify_docs.py` and `python -m pytest tests/test_docs_links.py -q` passed. |

## Phase 1: Standardize Candidate Comparison

Goal: create the canonical comparison artifact that later scores, selection, action, monitoring, and
UI can consume without special-case interpretation.

Exit condition: every supported candidate can be represented in one comparison table with clear
metadata, metrics, diagnostics, warnings, and construction method.

| ID | Status | Session | Work item | Prerequisites | Owning docs/code | Artifact or output | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RM-100 | Done | Session 08 | Specify the canonical candidate comparison artifact. | Phase 0 complete. | [candidate_comparison_spec.md](specs/candidate_comparison_spec.md), [candidate portfolios spec](specs/candidate_portfolios_spec.md), [reporting outputs spec](specs/reporting_outputs_spec.md), [OUTPUTS](../OUTPUTS.md) | Accepted spec for `candidate_comparison.json` (full registry, `current` row, Main output path) | `rg candidate_comparison` shows single contract; docs verify passes. |
| RM-101 | Done | Session 09 | Implement canonical candidate comparison output. | RM-100. | [candidate_comparison.py](../src/candidate_comparison.py), `run_compare_variants.py`, [candidate_comparison_spec.md](specs/candidate_comparison_spec.md) | `candidate_comparison.json` (+ optional `.txt`, legacy `portfolio_comparison.*`) under `output_dir_final` | `tests/test_candidate_comparison.py -q`; `python run_compare_variants.py` smoke when Main artifacts exist. |

## Phase 2: Build Scoring Carefully

Goal: add transparent scores only after candidate comparison inputs are stable.

Exit condition: scores are explainable, testable, and non-binding until the Selection Engine exists.

| ID | Status | Session | Work item | Prerequisites | Owning docs/code | Artifact or output | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RM-200 | Done | Session 10 | Specify the Robustness Scorecard. | RM-100. | [robustness_scorecard_spec.md](specs/robustness_scorecard_spec.md), [candidate_comparison_spec.md](specs/candidate_comparison_spec.md), [stress testing spec](specs/stress_testing_spec.md) | Accepted spec: relative within-run scoring, RC via comparison v1.1, 10y primary | `python scripts/verify_docs.py`; no recommendation wording in spec |
| RM-201 | Done | Session 11 | Implement the Robustness Scorecard. | RM-200 and RM-101. | [robustness_scorecard.py](../src/robustness_scorecard.py), [candidate_comparison.py](../src/candidate_comparison.py), [run_compare_variants.py](../run_compare_variants.py) | `robustness_scorecard.json` / `.txt` under `output_dir_final` | `tests/test_robustness_scorecard.py`, `tests/test_candidate_comparison.py` |
| RM-210 | Done | Session 12 | Specify the Portfolio Health Score. | RM-200 recommended; RM-100 required. | [portfolio_health_score_spec.md](specs/portfolio_health_score_spec.md), metrics/stress/reporting specs, [PRODUCT](../PRODUCT.md) | Accepted Health Score spec (`portfolio_health_score_v1`, ten components, optional robustness reference) | `python scripts/verify_docs.py`; confirm score remains explanatory and non-binding. |
| RM-211 | Done | Session 13 | Implement the Portfolio Health Score. | RM-210 and RM-101. | [portfolio_health_score.py](../src/portfolio_health_score.py), [candidate_comparison.py](../src/candidate_comparison.py), [run_compare_variants.py](../run_compare_variants.py) | `portfolio_health_score.json` / `.txt` under `output_dir_final` | `tests/test_portfolio_health_score.py`, `tests/test_candidate_comparison.py` |

## Phase 3: Add Selection, No-Trade, And Action

Goal: create the first formal decision artifact only after comparison and scores exist.

Exit condition: the system can produce a selected candidate, no-trade conclusion, inconclusive status,
or data-review status with rationale and warnings, without mixing diagnostics and decisions.

| ID | Status | Session | Work item | Prerequisites | Owning docs/code | Artifact or output | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RM-300 | Done | Session 14 | Specify Selection Engine and No-Trade Recommendation boundaries. | RM-201 and RM-211. | [selection_engine_spec.md](specs/selection_engine_spec.md), comparison and score specs, [production workflow spec](specs/production_workflow.md) | Accepted selection/no-trade spec (`selection_decision_v1`) | `python scripts/verify_docs.py`; confirm diagnostic scorecards remain non-binding. |
| RM-301 | Done | Session 15 | Implement Selection Engine and No-Trade Recommendation. | RM-300. | [selection_engine.py](../src/selection_engine.py), [candidate_comparison.py](../src/candidate_comparison.py), score outputs | `selection_decision.json` / `.txt` under `output_dir_final` | `tests/test_selection_engine.py`; wired in `write_candidate_comparison_outputs`. |
| RM-310 | Done | Session 16 | Extend Action Engine and Rebalancing Advisor around selected candidates. | RM-301. | [action_engine_spec.md](specs/action_engine_spec.md), [action_engine.py](../src/action_engine.py), [rebalance.py](../src/rebalance.py), selection outputs | `action_plan.json` / `.txt` under `output_dir_final` (always when selection exists; 10 bps on turnover) | `tests/test_action_engine.py`; wired in `write_candidate_comparison_outputs`. |

## Phase 4: Add Monitoring And Decision Records

Goal: turn one-time analysis into a repeatable process that can explain what changed and what was
decided.

Exit condition: the system can compare an analysis with a prior snapshot and emit a generated decision
record.

| ID | Status | Session | Work item | Prerequisites | Owning docs/code | Artifact or output | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RM-400 | Done | Session 17 | Specify monitoring snapshots and What Changed artifacts. | RM-301 recommended. | [monitoring_spec.md](specs/monitoring_spec.md), [OUTPUTS](../OUTPUTS.md), [PRODUCT](../PRODUCT.md) | Accepted monitoring spec (`analysis_snapshot_v1`, `monitoring_diff_v1`) | `python scripts/verify_docs.py`; generated-vs-source boundary in spec. |
| RM-401 | Done | Session 18 | Implement monitoring diff outputs. | RM-400. | [monitoring.py](../src/monitoring.py), [candidate_comparison.py](../src/candidate_comparison.py) | `monitoring_diff.json` / `.txt`, `monitoring/latest/` and `history/` snapshots | `tests/test_monitoring.py -q`; wired in `write_candidate_comparison_outputs`. |
| RM-410 | Done | Session 19 | Specify Decision Journal schema and lifecycle. | RM-300 required; RM-310 and RM-400 preferred. | [decision_journal_spec.md](specs/decision_journal_spec.md), [OUTPUTS](../OUTPUTS.md), selection/action/monitoring specs | Accepted journal spec (`decision_journal_v1`) | `python scripts/verify_docs.py`; generated-only V1 boundary confirmed. |
| RM-411 | Done | Session 20 | Implement generated Decision Journal output. | RM-410. | [decision_journal.py](../src/decision_journal.py), selection/action/monitoring modules | `decision_journal.json` / `.txt`, `journal/latest/` and `history/` | `tests/test_decision_journal.py`; wired in `write_candidate_comparison_outputs`. |

## Phase 5: Product UI Only After Stable Contracts

Goal: display stable artifacts without moving formulas or product decisions into the UI layer.

Exit condition: the first UI slice consumes existing stable artifacts and does not invent its own
portfolio logic.

| ID | Status | Session | Work item | Prerequisites | Owning docs/code | Artifact or output | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RM-500 | Deferred | After MVP stabilization | Decide the first real product UI surface: static report package, local dashboard, or web app. | Active MVP stabilization plan closed. | [DESIGN](../DESIGN.md), [PRODUCT](../PRODUCT.md), [ARCHITECTURE](../ARCHITECTURE.md), `config_ui/`, `results_dashboard/` | Decision record and updated product docs if direction changes | Documentation checks; no code unless explicitly requested. |
| RM-501 | Deferred | After RM-500 | Implement the first narrow UI slice. | RM-500 and stable artifact contracts. | Chosen UI code, stable artifact specs, [DESIGN](../DESIGN.md) | First UI surface around existing artifacts | UI tests if present; local browser inspection for significant frontend changes. |

## Phase 6: Post-Session Audit And Next Stage

Goal: reconcile the project after Sessions 01-20, then stabilize the new decision pipeline before
adding larger product surfaces or analytics.

Exit condition (**met 2026-05-17**): stale status docs synced; V1 decision package has report/export
surface; post-audit analytics implemented; `RM-623` closed. Residual: regenerated-output language QA
(`KI-2026-05-17-007`); Phase 5 UI (`RM-500+`) is deferred until MVP stabilization closes.

| ID | Status | Session | Work item | Prerequisites | Owning docs/code | Artifact or output | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RM-600 | Done | Post-closure 1-4 | Perform the post-session deep audit, including concept comparison, weak-block triage, mojibake triage, and Main-vs-robust optimizer review. | Sessions 01-20 complete. | [post-session audit](audits/2026-05-17_post_session_deep_system_audit.md), this roadmap, [known issues](../KNOWN_ISSUES.md), [decisions](../DECISIONS.md) | New audit and next-stage backlog | `python scripts/verify_docs.py`. |
| RM-601 | Done | Post-audit Session 01 | Create the post-audit stabilization and analytics ExecPlan. | RM-600. | [post-audit ExecPlan](exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md), this roadmap | Sessionized handoff plan for RM-610 through RM-622 | `python scripts/verify_docs.py`. |
| RM-610 | Done | Post-audit Session 02 | Sync top-level current-status docs after Sessions 01-20. | RM-601. | [README](../README.md), [AGENTS](../AGENTS.md), [SPEC](../SPEC.md), [PRODUCT](../PRODUCT.md), [ARCHITECTURE](../ARCHITECTURE.md), this roadmap, [post-audit ExecPlan](exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md) | Implemented file-first V1 decision artifacts no longer described as target/TBD in top-level docs | `python scripts/verify_docs.py`; targeted stale-reference search for Selection/Health/Monitoring/Journal TBD wording. |
| RM-611 | Done | Post-audit Session 03 | Fix decision-log and planning-doc integrity issues. | RM-601. | [DECISIONS](../DECISIONS.md), [post-audit ExecPlan](exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md), this roadmap | Unique decision IDs; handoff text now points to Session 04 | `python scripts/verify_docs.py`; targeted search for `DEC-2026-05-17-003` references. |
| RM-612 | Done | Post-audit Sessions 04, 06, 07 | Update detailed specs and report/PDF surfaces for the full decision package. | RM-610 recommended. | [decision package reporting spec](specs/decision_package_reporting_spec.md), [decision_package_reporting.py](../src/decision_package_reporting.py), [reporting outputs spec](specs/reporting_outputs_spec.md), [pdf_reports.py](../src/pdf_reports.py) | `decision_package_summary.txt` / `.json`, `report.txt` append, CLI paths, optional `Main portfolio_decision_package.pdf` | `tests/test_decision_package_reporting.py`; `python scripts/verify_docs.py`. |
| RM-613 | Done | Post-audit Session 05 | Fix remaining source/generator mojibake, broken symbols, and English-language acceptance gaps. | RM-600. | `src/pdf_reports.py`, runner scripts, robust optimizer scripts/specs, [DESIGN](../DESIGN.md), affected docs | Source/generator text cleaned; regenerated-output QA tracked under `KI-2026-05-17-007` | Targeted Cyrillic/mojibake source scans pass; `python scripts/verify_docs.py` passes. |
| RM-614 | Done | Post-audit Sessions 08, 09 | Define and harden current-vs-policy/no-trade workflow. | RM-301, RM-310, RM-601. | [current vs policy workflow spec](specs/current_vs_policy_workflow_spec.md), [current_vs_policy.py](../src/current_vs_policy.py), `run_report.py`, candidate comparison, runners | Sidecar materialization, status JSON, No-Trade actionability gating | `tests/test_current_vs_policy_workflow.py`; `python scripts/verify_docs.py`. |
| RM-615 | Done | Post-audit Sessions 10, 11 | Orchestrate candidate generation as a factory before comparison and implement the factory CLI. | RM-601. | [candidate factory spec](specs/candidate_factory_spec.md), [run_candidate_factory.py](../run_candidate_factory.py), [candidate_factory.py](../src/candidate_factory.py) | `candidate_factory_run.json` / `.txt` under `output_dir_final` | `tests/test_candidate_factory.py` |
| RM-616 | Done | Post-audit Sessions 12–13 | Specify and implement the trade-off explanation and model-risk diagnostics layer. | RM-612 recommended. | [tradeoff_and_model_risk.py](../src/tradeoff_and_model_risk.py), [candidate_comparison.py](../src/candidate_comparison.py), [decision_package_reporting.py](../src/decision_package_reporting.py) | `tradeoff_explanation.json` / `.txt`, `model_risk_diagnostics.json` / `.txt` under `output_dir_final` | `tests/test_tradeoff_and_model_risk.py`; wired in comparison pipeline. |
| RM-620 | Done | Post-audit Sessions 14–15 | Specify and implement Assumption Sensitivity. | RM-610 and RM-612 recommended. | [assumption_sensitivity_spec.md](specs/assumption_sensitivity_spec.md), [assumption_sensitivity.py](../src/assumption_sensitivity.py), [candidate_comparison.py](../src/candidate_comparison.py) | `assumption_sensitivity.json` / `.txt` under `output_dir_final` | `tests/test_assumption_sensitivity.py`; wired in `write_candidate_comparison_outputs`. |
| RM-621 | Done | Post-audit Sessions 16, 17 | Specify and implement Pareto/Dominance. | RM-620 recommended. | [pareto_dominance.py](../src/pareto_dominance.py), [pareto_dominance_spec.md](specs/pareto_dominance_spec.md) | `pareto_dominance.json` / `.txt` under `output_dir_final` | `tests/test_pareto_dominance.py`; wired after assumption sensitivity. |
| RM-622 | Done | Post-audit Sessions 18, 19 | Specify and implement Regret Analysis. | RM-620 recommended. | [regret_analysis_spec.md](specs/regret_analysis_spec.md), `src/regret_analysis.py` | `regret_analysis.json` / `.txt` | Session 19: wired after Pareto; `tests/test_regret_analysis.py`. |
| RM-623 | Done | Post-audit Session 20 | Close the post-audit plan with broad verification and project-memory updates. | RM-610 through RM-622 complete or explicitly deferred. | [post-audit ExecPlan](exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md), [CHANGELOG](../CHANGELOG.md), [known issues](../KNOWN_ISSUES.md), [decisions](../DECISIONS.md) | Plan marked completed; exec plan register updated; smoke compare refreshed Main portfolio artifacts | `python scripts/verify_docs.py`; 112 focused pipeline tests; `python run_compare_variants.py` smoke. |

## Phase 7: MVP Stabilization After Repeat Audit

Goal: stabilize the file-first MVP before UI/workspace work. This phase keeps existing analytics
intact and focuses on source-of-truth coherence, data-policy correctness, schema/language cleanup,
generated-output QA, offline end-to-end verification, and a clearer user flow.

Exit condition: a user or new agent can run the file-first project path and trust the docs, data
behavior, diagnostics, generated outputs, and tests. UI/workspace decisions stay deferred until this
phase is closed.

| ID | Status | Session | Work item | Prerequisites | Owning docs/code | Artifact or output | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RM-700 | Done | MVP Session 01 | Create repeat audit handoff and active MVP stabilization ExecPlan. | User-approved roadmap. | [repeat audit](audits/2026-05-17_repeat_project_mvp_readiness_audit.md), [MVP stabilization ExecPlan](exec_plans/2026-05-17_post_audit_mvp_stabilization_plan.md), audit and plan registers, this roadmap, [known issues](../KNOWN_ISSUES.md), [CHANGELOG](../CHANGELOG.md) | Active plan and registered audit evidence | `python scripts/verify_docs.py`. |
| RM-701 | Done | MVP Session 02 | Sync source-of-truth status docs and remove implemented-as-TBD wording. | RM-700. | [README](../README.md), [ARCHITECTURE](../ARCHITECTURE.md), [SPEC](../SPEC.md), [PRODUCT](../PRODUCT.md), [OUTPUTS](../OUTPUTS.md), spec index | Top-level docs agree on file-first V1 vs future UI/workspace | `python scripts/verify_docs.py`; stale-reference search. |
| RM-702 | Done | MVP Session 03 | Sync risk-free and cash policy across docs/code/tests. | RM-701 recommended. | [config.py](../src/config.py), [DATA](../DATA.md), input assumptions and metrics specs, tests | USD/EUR defaults documented and tested; unsupported non-USD requires explicit config | `tests/test_config_weights_sync.py` and `tests/test_input_assumptions.py`; `python scripts/verify_docs.py`; stale-policy search. |
| RM-703 | Done | MVP Session 04 | Add asset metadata fingerprint to monthly data cache key. | RM-702 recommended. | [data_loader.py](../src/data_loader.py), cache/data docs, data tests | Cache invalidates when asset currency metadata changes | `tests/test_data_cache_key.py`; `python scripts/verify_docs.py`. |
| RM-704 | Done | MVP Session 05 | Fix NaN-safe cash fallback diagnostics. | RM-700. | [portfolio_dynamic.py](../src/portfolio_dynamic.py), data policy docs, NaN-safe tests | `n_months_cash_fallback` counts actual fallback months after redistribution | Focused backtest NaN-safe regression passed. |
| RM-705 | Done | MVP Session 06 | Harden time-to-recovery metric semantics. | RM-700. | [metrics_asset.py](../src/metrics_asset.py), [metrics_daily.py](../src/metrics_daily.py), [metrics spec](specs/metrics_specification.md), [TESTING](../TESTING.md), tests | TTR uses the peak/trough path of maximum drawdown, preserves no-drawdown `0` recovery, and has focused monthly/daily regressions | `tests/test_metrics_drawdown.py`; adjacent metric/report tests; `python scripts/verify_docs.py`. |
| RM-706 | Done | MVP Session 07 | Clean source-level schema and language drift. | RM-700. | [stress_factors.py](../src/stress_factors.py), [portfolio_commentary.py](../src/portfolio_commentary.py), [stress testing spec](specs/stress_testing_spec.md), tests | `assessment_en` primary in new multicollinearity outputs; commentary legacy-reads `assessment_ru` | `tests/test_factor_multicollinearity.py`, `tests/test_portfolio_commentary.py`; `python scripts/verify_docs.py`. |
| RM-707 | Done | MVP Session 08 | Regenerate and QA representative generated outputs after source/schema fixes. | RM-706. | Report runners, `Main portfolio/`, `pdf_md_sources/`, `pdf files/`, `scripts/scan_generated_outputs.py`, tests | Representative outputs regenerated; QA scan passes on text artifacts | `scripts/scan_generated_outputs.py`; `tests/test_generated_output_language.py`; CLI regen. |
| RM-708 | Done | MVP Session 09 | Add offline end-to-end MVP pipeline smoke test. | RM-703 through RM-706 recommended. | [test_mvp_pipeline_offline.py](../tests/test_mvp_pipeline_offline.py), [mvp_offline_fixtures.py](../tests/mvp_offline_fixtures.py), [TESTING](../TESTING.md) | Synthetic offline test proves key decision-package JSON outputs | `python -m pytest tests/test_mvp_pipeline_offline.py -q`. |
| RM-709 | Done | MVP Session 10 | Clarify and optionally orchestrate the user flow. | RM-708 recommended. | [operational runbook](operational_runbook.md), [mvp_workflow.py](../src/mvp_workflow.py), [run_mvp_workflow.py](../run_mvp_workflow.py), production workflow spec | Documented `input -> diagnosis -> comparison -> action` path and `run_mvp_workflow.py` wrapper | `tests/test_mvp_workflow.py`; `python scripts/verify_docs.py`. |
| RM-710 | Done | MVP Session 11 | Close MVP stabilization with broad verification and project-memory cleanup. | RM-701 through RM-709 complete or accepted/deferred. | Whole repo, roadmap, known issues, changelog, active ExecPlan | MVP stabilization plan closed; Phase 7 exit met | `scripts/verify_docs.py`; `scripts/scan_generated_outputs.py`; full pytest (`462 passed`, `--basetemp=tmp/pytest_mvp_session_11`). |

## Phase 8: Portfolio-First Workflow Transition

Goal: correct the main workflow contract so the project starts from the user-selected
`analysis_subject`, diagnoses that portfolio first, and only then generates alternatives for
comparison. The old policy optimizer remains available as legacy or archived infrastructure, but it
is not the default starting portfolio and is not a default candidate in this phase.

Exit condition: the main file-first workflow can resolve `analysis_subject`, materialize its
diagnostics before any candidate generation, compare that subject against allowed candidates, and emit
decision artifacts that answer whether to keep, improve, rebalance, or rethink the starting
portfolio.

| ID | Status | Session | Work item | Prerequisites | Owning docs/code | Artifact or output | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RM-800 | Done | Portfolio-first Session 01 | Create active ExecPlan and record the policy-first architecture conflict. | User-approved portfolio-first transition plan. | [Portfolio-first ExecPlan](exec_plans/2026-05-18_portfolio_first_transition_plan.md), this roadmap, [known issues](../KNOWN_ISSUES.md), [CHANGELOG](../CHANGELOG.md), [ExecPlan register](exec_plans/README.md) | Active handoff plan; old mental model (`policy first`) and new mental model (`analysis_subject first`) recorded | `python scripts/verify_docs.py`. |
| RM-801 | Done | Portfolio-first Session 02 | Create canonical portfolio review workflow spec. | RM-800. | [portfolio_review_workflow_spec.md](specs/portfolio_review_workflow_spec.md), [SPEC](../SPEC.md), [ARCHITECTURE](../ARCHITECTURE.md), [PRODUCT](../PRODUCT.md), [OUTPUTS](../OUTPUTS.md) | Binding workflow contract: diagnostics before candidate generation; policy engine legacy by default | `python scripts/verify_docs.py`; stale policy-first wording search. |
| RM-802 | Done | Portfolio-first Session 03 | Add `analysis_subject` input contract and resolver. | RM-801. | Config schema/loading, [analysis_setup.py](../src/analysis_setup.py), [input_assumptions.py](../src/input_assumptions.py), [input assumptions spec](specs/input_assumptions_spec.md), [config example](../config.yml.example) | Runtime resolves `current_portfolio`, `model_portfolio`, and `universe_baseline`; explicit subject blocks stale generated-weight merge | `python -m pytest tests/test_input_assumptions.py tests/test_config_weights_sync.py -q --basetemp='tmp/pytest_portfolio_first_session_03'`. |
| RM-803 | Done | Portfolio-first Session 04 | Materialize diagnostics for `analysis_subject` before candidates. | RM-802. | [run_report.py](../run_report.py), report helpers, snapshots, metadata tests | `run_report.py --materialize-analysis-subject` writes `{output_dir_final}/analysis_subject/` diagnostics for current/model/universe baseline without overwriting candidate outputs | `python -m pytest tests/test_analysis_subject_materialization.py tests/test_input_assumptions.py -q --basetemp='tmp/pytest_portfolio_first_session_04'`. |
| RM-804 | Done | Portfolio-first Session 05 | Add portfolio-first orchestrator. | RM-803. | [run_portfolio_review.py](../run_portfolio_review.py), [portfolio_review_workflow.py](../src/portfolio_review_workflow.py), candidate factory integration, [operational runbook](operational_runbook.md), workflow tests | Default command materializes and diagnoses `analysis_subject`, then runs allowed non-policy candidates and comparison outputs without calling `run_optimization.py` | `python -m pytest tests/test_portfolio_review_workflow.py -q --basetemp='tmp/pytest_portfolio_first_session_05_workflow'`. |
| RM-805 | Done | Portfolio-first Session 06 | Center comparison and decision logic on `analysis_subject` versus candidates. | RM-804. | Candidate comparison, selection, action, decision package, status artifacts | New comparison/status contract where baseline is `analysis_subject`; old `current_vs_policy_status.json` remains compatibility-only | Focused comparison/selection/action tests. |
| RM-806 | Done | Portfolio-first Session 07 | Isolate the old policy engine as legacy infrastructure. | RM-805. | [README](../README.md), [SPEC](../SPEC.md), [ARCHITECTURE](../ARCHITECTURE.md), [AGENTS](../AGENTS.md), [operational runbook](operational_runbook.md), [portfolio construction policy](specs/portfolio_construction_policy.md) | User-facing docs and CLI help route the normal path through `run_portfolio_review.py`; `run_optimization.py` is labeled legacy compatibility | `python scripts/verify_docs.py`; stale wording search; help text smoke checks. |
| RM-807 | Done | Portfolio-first Session 08 | Update report language, examples, and generated-output QA. | RM-806. | [decision package reporting](../src/decision_package_reporting.py), [generated output QA](../src/generated_output_qa.py), [config example](../config.yml.example), reporting specs | Decision package summaries name `analysis_subject` as the starting portfolio and candidates as alternatives; generated-output QA checks the story markers | `python -m pytest tests/test_decision_package_reporting.py tests/test_generated_output_language.py -q`; `python scripts/verify_docs.py`. |
| RM-808 | Done | Portfolio-first Session 09 | Add offline end-to-end coverage and close the transition. | RM-801 through RM-807 complete. | [test_portfolio_first_e2e_offline.py](../tests/test_portfolio_first_e2e_offline.py), [TESTING](../TESTING.md), roadmap, changelog, known issues, ExecPlan register | Portfolio-first transition closed; default workflow has offline coverage across current, model, and universe-baseline subjects | `python -m pytest tests/test_portfolio_first_e2e_offline.py -q`; adjacent portfolio-first tests; `python scripts/verify_docs.py`. |

## Phase 9: Post-Portfolio-First Stabilization

Goal: make the implemented portfolio-first pipeline trustworthy before adding UI, saved workspaces, or
new product surfaces. This phase follows the 2026-05-19 post-portfolio-first audit and prioritizes
comparison trust before report polish.

Exit condition: a fresh `run_portfolio_review.py` run correctly identifies `analysis_subject`, compares
it against fresh or explicitly stale-labeled candidates, produces explainable selection/no-trade
artifacts, avoids known first-run monitoring contradictions, restores regime metrics, and builds the
decision package outputs needed for advisor/client review.

| ID | Status | Session | Work item | Prerequisites | Owning docs/code | Artifact or output | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RM-900 | Done | Stabilization Session 00 | Create post-portfolio-first stabilization handoff. | 2026-05-19 audit completed and user-approved priority order. | [stabilization ExecPlan](exec_plans/2026-05-19_post_portfolio_first_stabilization_plan.md), this roadmap, [audit register](audits/README.md), [known issues](../KNOWN_ISSUES.md), [ExecPlan register](exec_plans/README.md) | Active plan; Phase 9 roadmap; audit findings mapped to sessions and known issues | `python scripts/verify_docs.py`. |
| RM-901 | Done | Stabilization Session 01 | Fix comparison metadata precedence so subject sidecar metadata beats legacy root metadata. | RM-900. | [candidate_comparison.py](../src/candidate_comparison.py), [candidate comparison spec](specs/candidate_comparison_spec.md), comparison tests | `candidate_comparison.json.analysis_setup_summary` reflects the actual `analysis_subject` such as `current_portfolio` | Focused candidate comparison tests and portfolio-first comparison regression. |
| RM-902 | Done | Stabilization Session 02 | Add candidate freshness contract. | RM-901. | [candidate_factory.py](../src/candidate_factory.py), [run_candidate_factory.py](../run_candidate_factory.py), [run_portfolio_review.py](../run_portfolio_review.py), [candidate factory spec](specs/candidate_factory_spec.md) | Factory/review output distinguishes fresh, reused, stale, failed, and skipped candidates; stale snapshots are not silently used | Candidate factory tests plus a stale `analysis_end` regression. |
| RM-903 | Done | Stabilization Session 03 | Perform quick `returns_frequency` methodology check. | RM-902. | [run_report.py](../run_report.py), metrics/config flow, [metrics spec](specs/metrics_specification.md), config examples | ExecPlan finding records whether `returns_frequency: daily` affects main metrics or only daily/regime diagnostics | Focused inspection/test; promote a fix before RM-904 if main metrics are affected. |
| RM-904 | Done | Stabilization Session 04 | Improve selection and mandate/no-trade reliability after comparison trust is fixed. | RM-901, RM-902, RM-903 finding. | Selection, trade-off/model-risk, assumption sensitivity, regret modules and specs | No-favored mandate blocks explain the evidence and use `analysis_subject` as baseline | Focused selection/trade-off/sensitivity/regret tests. |
| RM-905 | Done | Stabilization Session 05 | Clean portfolio-first legacy policy boundary. | RM-904. | Candidate comparison, current-vs-policy, decision package reporting, related specs | Policy appears only as optional legacy reference in portfolio-first outputs | Focused output text/schema tests and stale wording search. |
| RM-906 | Done | Stabilization Session 06 | Fix regime portfolio metrics `mar_monthly` failure. | RM-903 finding. | [run_report.py](../run_report.py), [regime_portfolio_metrics.py](../src/regime_portfolio_metrics.py), [stress testing spec](specs/stress_testing_spec.md) | Subject `stress_report.json` includes `regime_portfolio_metrics` without `regime_portfolio_metrics_error` | Focused regime metrics tests and syntax parsing of the touched report path. |
| RM-907 | Done | Stabilization Session 07 | Apply methodology consistency follow-up. | RM-903; required only if docs/runtime need alignment. | [returns_frequency.py](../src/returns_frequency.py), [data_loader.py](../src/data_loader.py), metrics/input/stress specs, config examples | Main metrics/optimizer always monthly; non-monthly config is disclosure-only | `tests/test_returns_frequency.py`, `tests/test_input_assumptions.py`; `python scripts/verify_docs.py`. |
| RM-908 | Done | Stabilization Session 08 | Fix first-run monitoring honesty. | RM-904 recommended. | [monitoring.py](../src/monitoring.py), [monitoring spec](specs/monitoring_spec.md), monitoring tests | `no_prior_snapshot` does not show fake deltas or identical prior/current paths as a real comparison | Focused monitoring tests. |
| RM-909 | Done | Stabilization Session 09 | Repair decision package PDF build. | RM-901 and RM-902; after core trust blockers. | [decision_package_reporting.py](../src/decision_package_reporting.py), [pdf_reports.py](../src/pdf_reports.py), [decision package reporting spec](specs/decision_package_reporting_spec.md) | `Main portfolio_decision_package.pdf` builds via YAML front matter (`build_decision_package_pdf_md`) | `tests/test_decision_package_reporting.py`; PDF rebuild smoke. |
| RM-910 | Done | Stabilization Session 10 | Reduce portfolio-first report/PDF rebuild noise. | RM-909 recommended. | [run_portfolio_review.py](../run_portfolio_review.py), [rebuild_pdf_reports.py](../rebuild_pdf_reports.py), [pdf_reports.py](../src/pdf_reports.py), [OUTPUTS](../OUTPUTS.md) | Portfolio-first review focuses on subject/decision outputs; full legacy variant PDF rebuild is explicit | `tests/test_portfolio_review_workflow.py`, `tests/test_portfolio_first_pdf_rebuild.py`; `python scripts/verify_docs.py`. |
| RM-911 | Done | Stabilization Session 11 | Run fresh representative review and close the stabilization plan. | RM-901 through RM-910 complete or explicitly deferred. | Whole pipeline, roadmap, known issues, changelog, ExecPlan | Stabilization plan closed or remaining issues explicitly deferred | Fresh subject materialization; compare/PDF refresh; `504` pytest passes; `python scripts/verify_docs.py`. |

## Phase 10: Operational Portfolio-First Review (Deferred)

Goal: make the portfolio-first pipeline practical for routine runs without weakening freshness gating
or reintroducing silent stale reuse.

Exit condition: a documented **core-run** completes subject → lightweight candidates → compare →
decision package within normal session limits; **full-run** remains explicit for all optimizer/robust
builders; partial menus are visible in factory, comparison, and decision outputs.

| ID | Status | When | Work item | Prerequisites | Owning docs/code | Artifact or output | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RM-920 | Done | X-Ray Session 09 | Split portfolio-first review into **core-run** and **full-run** CLI modes/profiles (`core_v1` vs `default_v1`). | RM-911. | [run_portfolio_review.py](../run_portfolio_review.py), [portfolio_review_workflow.py](../src/portfolio_review_workflow.py), [candidate_factory.py](../src/candidate_factory.py), [operational_runbook.md](operational_runbook.md) | `--mode core` (default) and `--mode full` | `tests/test_portfolio_review_workflow.py`; operational runbook. |
| RM-921 | Deferred | After RM-920 or in parallel | Improve factory orchestration operations: progress logging, resumable steps, clearer per-candidate duration in `candidate_factory_run.json`, optional parallel execution only with isolation guarantees. | RM-902 freshness contract. | [candidate_factory.py](../src/candidate_factory.py), [candidate_factory_spec.md](specs/candidate_factory_spec.md) | Operators can resume or monitor long runs without guessing state | Manual long-run smoke; focused factory tests for resume/status fields. |
| RM-922 | Done | X-Ray Session 09 | Add explicit **partial candidate menu** disclosure in comparison and decision-package outputs. | RM-920. | [candidate_comparison.py](../src/candidate_comparison.py), [decision_package_reporting.py](../src/decision_package_reporting.py), [candidate_comparison_spec.md](specs/candidate_comparison_spec.md) | `candidate_menu` block + decision summary | `tests/test_candidate_comparison.py`. |

**Direction (not yet implemented):** cache/reuse candidates only when `analysis_end`, config fingerprint,
universe, weights, and material assumptions match; do not default to rebuilding every expensive
optimizer on every `run_portfolio_review.py` invocation.

## Phase 11: Portfolio X-Ray Diagnostics Deepening

Goal: make the current-portfolio diagnostic layer trustworthy and decision-useful before UI,
advanced optimization, or heavier product surfaces. This phase follows the 2026-05-19 Portfolio
X-Ray Layer Audit and is governed by the active
[Portfolio X-Ray Diagnostics Deepening Plan](exec_plans/2026-05-19_portfolio_xray_diagnostics_deepening_plan.md).

Exit condition: `analysis_subject` diagnostics use analysis-effective data, expose complete risk
budget and factor evidence, align tail-risk methodology with the metrics spec, include richer
portfolio metrics, and present hidden risk, weakness, and archetype evidence with confidence and
caveats. Report surfaces should be readable without inspecting raw JSON.

| ID | Status | Session | Work item | Prerequisites | Owning docs/code | Artifact or output | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RM-930 | Done | X-Ray Session 00 | Create Portfolio X-Ray audit memory, active ExecPlan, dedicated diagnostics spec scaffold, roadmap rows, known issues, and registers. | User-approved X-Ray roadmap. | [Portfolio X-Ray audit](audits/2026-05-19_portfolio_xray_layer_audit.md), [X-Ray ExecPlan](exec_plans/2026-05-19_portfolio_xray_diagnostics_deepening_plan.md), [X-Ray spec](specs/portfolio_xray_diagnostics_spec.md), [known issues](../KNOWN_ISSUES.md), this roadmap | Active plan and source-of-truth scaffold for Sessions 01-09 | `python scripts/verify_docs.py`. |
| RM-931 | Done | X-Ray Session 01 | Fix P0 data cutoff and `analysis_end` integrity across diagnostic consumers. | RM-930. | [windows.py](../src/windows.py), [run_report.py](../run_report.py), [io_export.py](../src/io_export.py), [stress_scenario_analytics.py](../src/stress_scenario_analytics.py), [scenario_library.py](../src/scenario_library.py), [data policy spec](specs/data_policy_spec.md), [DATA](../DATA.md) | Diagnostics use rows `<= analysis_end`; raw cache vs analysis-effective panels documented | `tests/test_analysis_end_cutoff.py`; fresh subject run should show no diagnostic `data_end` after `analysis_end`. |
| RM-932 | Done | X-Ray Session 02 | Fix P0 X-Ray evidence completeness: full risk contribution data and Kalman factor beta mapping. | RM-931 recommended. | [portfolio_xray.py](../src/portfolio_xray.py), [snapshot.py](../src/snapshot.py), [portfolio_commentary.py](../src/portfolio_commentary.py), [X-Ray spec](specs/portfolio_xray_diagnostics_spec.md), [OUTPUTS](../OUTPUTS.md) | Risk budget includes all positive-weight holdings with RC evidence; Kalman betas surface when available | `tests/test_portfolio_xray.py` (`test_resolve_rc_asset_prefers_full_csv_over_snapshot_top5`, `test_portfolio_xray_v2_kalman_reads_factor_betas_kalman_latest`). |
| RM-933 | Done | X-Ray Session 03 | Align VaR / ES methodology with canonical metrics spec or explicitly revise the spec. | RM-932. | [portfolio_analytics.py](../src/portfolio_analytics.py), [data_loader.py](../src/data_loader.py), [run_report.py](../run_report.py), [metrics spec](specs/metrics_specification.md) | Tail metrics disclose method, frequency, and window; docs and generated output agree | `tests/test_tail_risk.py`, `tests/test_portfolio_xray.py`. |
| RM-934 | Done | X-Ray Session 04 | Add missing portfolio metrics and quality metadata. | RM-933. | `src/metrics_*`, [portfolio_analytics.py](../src/portfolio_analytics.py), [run_report.py](../run_report.py), [X-Ray spec](specs/portfolio_xray_diagnostics_spec.md) | X-Ray risk diagnostics include skew/kurtosis, downside/upside beta, rolling beta/correlation, and quality metadata | `tests/test_portfolio_metrics_deepening.py`. |
| RM-935 | Done | X-Ray Session 05 | Build Hidden Risk Detector V2 with explicit flags, non-flags, evidence counts, and confidence. | RM-934. | [portfolio_xray.py](../src/portfolio_xray.py), [X-Ray spec](specs/portfolio_xray_diagnostics_spec.md) | Per-category flagged/below-threshold/unavailable assessments; section confidence and counts | `python -m pytest tests/test_portfolio_xray.py -q` (hidden-risk tests). |
| RM-936 | Done | X-Ray Session 06 | Build Weakness Map V2 with exposure, adverse evidence, severity, confidence, and drivers. | RM-935. | [portfolio_xray.py](../src/portfolio_xray.py), [portfolio_xray diagnostics spec](specs/portfolio_xray_diagnostics_spec.md), tests | Weakness rows separate exposure vs adverse evidence; top asset/factor drivers; conditional crypto_shock | `tests/test_portfolio_xray.py` weakness V2 tests; `python scripts/verify_docs.py`. |
| RM-937 | Done | X-Ray Session 07 | Rework Portfolio Archetype as an evidence scorecard with conflicts and caveats. | RM-936. | [portfolio_xray.py](../src/portfolio_xray.py), [X-Ray spec](specs/portfolio_xray_diagnostics_spec.md), [PRODUCT](../PRODUCT.md) | Archetype output includes positive evidence, negative evidence, confidence, and conflicting signals | `python -m pytest tests/test_portfolio_xray.py -q` (archetype V2 tests). |
| RM-938 | Done | X-Ray Session 08 | Productize X-Ray report/HTML/PDF presentation. | RM-931 through RM-937 stable. | [snapshot.py](../src/snapshot.py), [portfolio_xray.py](../src/portfolio_xray.py), [portfolio_commentary.py](../src/portfolio_commentary.py), [generated_output_qa.py](../src/generated_output_qa.py), [DESIGN](../DESIGN.md), [OUTPUTS](../OUTPUTS.md) | Reports show structured X-Ray sections instead of raw JSON-style dumps | `format_portfolio_xray_html` / `format_portfolio_xray_commentary`; QA scans; `tests/test_portfolio_xray.py`. |
| RM-939 | Done | X-Ray Session 09 | Implement operational portfolio-first review modes after X-Ray trust fixes. | RM-938. | [run_portfolio_review.py](../run_portfolio_review.py), [portfolio_review_workflow.py](../src/portfolio_review_workflow.py), [candidate_factory.py](../src/candidate_factory.py), [candidate_comparison.py](../src/candidate_comparison.py), [decision_package_reporting.py](../src/decision_package_reporting.py), [operational runbook](operational_runbook.md) | Core/full modes + partial menu disclosure | Focused workflow, factory, comparison, reporting tests. |

## Phase 12: Portfolio X-Ray Post-Audit Governance

Goal: make Block 2 (Portfolio X-Ray) **audit-grade** — transparent thresholds, provenance metadata,
factor inference surfacing, multi-window metrics, layer spec, contract tests, and baseline snapshot.

Exit condition: methodology map and layer navigation exist in repo; spec owns thresholds; sections
disclose frequency/window where applicable; contract tests prevent schema drift; documentation registers
match runtime.

Governed by the completed
[Portfolio X-Ray Post-Audit Roadmap](exec_plans/2026-05-20_portfolio_xray_post_audit_roadmap.md)
(Sessions 00–10 closed 2026-05-20).
Methodology baseline:
[Portfolio X-Ray Methodology Map](audits/2026-05-20_portfolio_xray_methodology_map.md).

| ID | Status | Session | Work item | Prerequisites | Owning docs/code | Artifact or output | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RM-940 | Done | X-Ray Post-Audit Session 00 | Project memory: methodology map, ExecPlan, registers, ROADMAP Phase 12. | 2026-05-20 methodology audit. | [methodology map](audits/2026-05-20_portfolio_xray_methodology_map.md), [post-audit ExecPlan](exec_plans/2026-05-20_portfolio_xray_post_audit_roadmap.md), [audits/README](audits/README.md), [exec_plans/README](exec_plans/README.md) | Active handoff for Sessions 01-10 | `python scripts/verify_docs.py`. |
| RM-941 | Done | Session 01 | Doc sync: close stale KNOWN_ISSUES (RC/Kalman); mark RM-932 Done; CHANGELOG; TESTING bundle stub. | RM-940. | [KNOWN_ISSUES](../KNOWN_ISSUES.md), [ROADMAP](ROADMAP.md), [CHANGELOG](../CHANGELOG.md), [TESTING](../TESTING.md) | Registers match deepening wave runtime | `python scripts/verify_docs.py`; Portfolio X-Ray regression bundle stub in TESTING.md. |
| RM-942 | Done | Session 02 | Canonical threshold registry in spec + validation tests. | RM-941. | [portfolio_xray_diagnostics_spec.md](specs/portfolio_xray_diagnostics_spec.md) §8, [portfolio_xray.py](../src/portfolio_xray.py), [test_portfolio_xray_threshold_registry.py](../tests/test_portfolio_xray_threshold_registry.py) | Spec-owned `XRAY_THRESHOLDS`; drift tests | `python -m pytest tests/test_portfolio_xray_threshold_registry.py -q`. |
| RM-943 | Done | Session 03 | Section provenance metadata (frequency/window/n_obs/benchmark). | RM-942. | [portfolio_xray.py](../src/portfolio_xray.py), X-Ray spec §2.2–2.7 | Sections 2.2/2.3/2.6/2.7 disclose provenance | `tests/test_portfolio_xray.py` (`test_portfolio_xray_section_provenance_metadata`). |
| RM-944 | Done | Session 04 | Factor regression inference panel (read-only from stress_report). | RM-943. | [portfolio_xray.py](../src/portfolio_xray.py), [stress_testing_spec.md](specs/stress_testing_spec.md) | Inference visible when stress provides it | `test_portfolio_xray_factor_regression_inference_panel`. |
| RM-945 | Done | Session 05 | Multi-window metrics + TTR in risk diagnostics. | RM-944. | [snapshot.py](../src/snapshot.py), [portfolio_xray.py](../src/portfolio_xray.py) | `multi_window_metrics` panel; `ttr_months`/`recovered` on primary metrics | `test_portfolio_xray_multi_window_metrics_panel`, `test_portfolio_xray_ttr_in_primary_risk_metrics`, `test_load_portfolio_windows_from_dir`. |
| RM-946 | Done | Session 06 | Create `portfolio_xray_layer_spec.md`. | RM-945. | [portfolio_xray_layer_spec.md](specs/portfolio_xray_layer_spec.md), [SPEC.md](../SPEC.md) | Block 2 layer map 2.1–2.7 | `python scripts/verify_docs.py`. |
| RM-947 | Done | Session 07 | Allocation concentration (HHI, top-N). | RM-946. | [portfolio_xray.py](../src/portfolio_xray.py), X-Ray spec §2.1 | `weight_concentration` item in asset_allocation | `test_portfolio_xray_weight_concentration_in_asset_allocation`. |
| RM-948 | Done | Session 08 | `volatility_spike` methodology: Option B factor-only (`beta_vix`, ES_95); spec + `scenario_coverage` contract. | RM-947. | [portfolio_xray_diagnostics_spec.md](specs/portfolio_xray_diagnostics_spec.md) §2.7, [portfolio_xray.py](../src/portfolio_xray.py) | Documented vol-spike rule; no new stress scenario | `test_volatility_spike_weakness_factor_only_methodology`. |
| RM-949 | Done | Session 09 | Golden contract tests + TESTING bundle. | RM-948. | [tests/fixtures/portfolio_xray_golden_v2.json](../tests/fixtures/portfolio_xray_golden_v2.json), [test_portfolio_xray_contract.py](../tests/test_portfolio_xray_contract.py), [TESTING.md](../TESTING.md) | Golden JSON + schema drift tests | `python -m pytest tests/test_portfolio_xray_contract.py tests/test_portfolio_xray.py tests/test_portfolio_xray_threshold_registry.py -q`. |
| RM-950 | Done | Session 10 | Baseline snapshot + wave closure. | RM-949. | [baseline snapshot](audits/2026-05-20_portfolio_xray_baseline_snapshot.md), ExecPlan, ROADMAP | `2026-05-20_portfolio_xray_baseline_snapshot.md`; Phase 12 closed | verify_docs + X-Ray bundle (40 tests). |

Note: `RM-932` (full RC + Kalman in X-Ray) was implemented in the deepening Session 02; post-audit
Session 01 marked it **Done** in Phase 11 and removed stale `KI-2026-05-19-007` / `KI-2026-05-19-008`
from active KNOWN_ISSUES.

## Audit Mapping

| Audit ID | Roadmap handling |
| --- | --- |
| AUD-001 | Fixed by RM-000 and this roadmap. |
| AUD-002 | Fixed by RM-001 in Session 02; resolved issue removed from [KNOWN_ISSUES](../KNOWN_ISSUES.md). |
| AUD-003 | Fixed by RM-002 in Session 03; resolved issue removed from [KNOWN_ISSUES](../KNOWN_ISSUES.md). |
| AUD-004 | Fixed by RM-003 in Session 04; resolved issue removed from [KNOWN_ISSUES](../KNOWN_ISSUES.md). |
| AUD-005 | Registered in [KNOWN_ISSUES](../KNOWN_ISSUES.md); planned as RM-004. |
| AUD-006 | Resolved in Session 05 via RM-005 (docstrings + focused tests). |
| AUD-007 | Fixed by updating [DECISIONS](../DECISIONS.md). |
| AUD-008 | Fixed by registering unresolved issues in [KNOWN_ISSUES](../KNOWN_ISSUES.md). |
| AUD-009 | Fixed by RM-006 in Session 06; resolved issue removed from [KNOWN_ISSUES](../KNOWN_ISSUES.md). |
| AUD-010 | Resolved at artifact level by RM-100 and RM-101; UI/workspace follow-up continues under RM-612, RM-614, and RM-615. |
| AUD-011 | Resolved at V1 decision-artifact level by RM-200 through RM-301; report/UI integration continues under RM-612. |
| AUD-012 | Resolved via RM-007 (Session 07): `scripts/verify_docs.py` and `tests/test_docs_links.py`. |
| PSA-001 through PSA-013 | Addressed by RM-610 through RM-623 (post-audit plan closed 2026-05-17); residual items in [KNOWN_ISSUES](../KNOWN_ISSUES.md). |
| RMA-001 through RMA-008 | Addressed by RM-700 through RM-710; handoff closed in [Post-Audit MVP Stabilization Plan](exec_plans/2026-05-17_post_audit_mvp_stabilization_plan.md) (2026-05-18). |
| PFT-001 | Fixed by RM-800 through RM-808: default workflow starts from `analysis_subject`, not generated policy optimization. |
| PPF-001 | Fixed by RM-906: regime portfolio metrics no longer reference undefined `mar_monthly`; default MAR is aligned daily risk-free. |
| PPF-002 | Fixed by RM-901: comparison setup summary now prefers `analysis_subject` sidecar metadata. |
| PPF-003 | Done (RM-909): decision package PDF uses YAML front matter; Pandoc/XeLaTeX build verified. |
| PPF-004 | Fixed by RM-902: candidate freshness contract for review runs. |
| PPF-005 | Fixed by RM-905: legacy policy artifacts are optional/compatibility-only in portfolio-first outputs. |
| PPF-006 | Fixed by RM-904: mandate/no-favored downstream artifacts include blocked-decision narrative. |
| PPF-007 | Done (RM-908): monitoring first run no longer shows contradictory deltas on `no_prior_snapshot`. |
| PXL-001 through PXL-010 | Addressed by RM-930 through RM-939 (deepening plan closed 2026-05-20). Governance gaps G1–G11 closed in Phase 12 RM-940–RM-950 except deferred G7 (factor/drawdown/ES risk budget). |
| PXF-001 | Closed: methodology map and post-audit governance wave completed (RM-940–RM-950, Sessions 00–10, 2026-05-20). |
| PPF-008 | Mitigated (RM-920, RM-922, RM-939): core default path + partial-menu disclosure; full refresh remains explicit via `--mode full`. |

## Session Boundary Rule

Post-audit Sessions 02–20 are **closed** (see completed [post-audit ExecPlan](exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md)).
Phase 7 (`RM-700` through `RM-710`) is **closed** as of 2026-05-18. Phase 8 (`RM-800` through
`RM-808`) is **closed** as of 2026-05-18. Phase 9 (`RM-900` through `RM-911`) is **closed** as of
2026-05-19. Phase 11 (`RM-930` through `RM-939`) is **closed** as of 2026-05-20. Phase 12
(`RM-940` through `RM-950`) is **closed** as of 2026-05-20. Keep each future project-level session
in a separate chat unless the user explicitly changes that rule. Do not reopen closed MVP,
post-audit, portfolio-first, Phase 9, or Phase 11 sessions unless the user explicitly requests plan
amendments.

## Implemented Decision Artifacts

These artifacts now have accepted V1 specs and implementations (emitted from `write_candidate_comparison_outputs` unless noted):

- `candidate_comparison.json`
- `robustness_scorecard.json`
- `portfolio_health_score.json`
- `selection_decision.json`
- `tradeoff_explanation.json` and `model_risk_diagnostics.json`
- `assumption_sensitivity.json`
- `pareto_dominance.json`
- `regret_analysis.json`
- `action_plan.json`
- `monitoring_diff.json`
- `decision_journal.json`
- `decision_package_summary.json` / `.txt` (reporting; [decision_package_reporting.py](../src/decision_package_reporting.py))
- `current_vs_policy_status.json` (when current weights are supplied)
- `candidate_factory_run.json` (orchestration; [run_candidate_factory.py](../run_candidate_factory.py))
