# Project Roadmap

This file is the durable roadmap and backlog for Portfolio X-Ray & Optimization Terminal /
Portfolio MRI. It turns the product concept, audit findings, and current implementation state into
an ordered development sequence.

This is a planning document. It does not override [SPEC.md](../SPEC.md), [RULES.md](../RULES.md),
[OUTPUTS.md](../OUTPUTS.md), [TESTING.md](../TESTING.md), or the detailed specs under
[docs/specs/](specs/README.md). Product ideas become binding only after the relevant source-of-truth
spec and implementation are updated.

## Current Development Rule

Do not add new major analytics until the current source-of-truth cleanup and the canonical candidate
comparison contract are done. The current project already has a strong report-first analytical base;
the next quality step is a controlled decision pipeline:

```text
concept -> source-of-truth spec -> canonical artifact -> tests -> report/UI surface -> decision record
```

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
| RM-500 | Planned | Session 21 | Decide the first real product UI surface: static report package, local dashboard, or web app. | Phases 1-4 enough for the chosen surface. | [DESIGN](../DESIGN.md), [PRODUCT](../PRODUCT.md), [ARCHITECTURE](../ARCHITECTURE.md), `config_ui/`, `results_dashboard/` | Decision record and updated product docs if direction changes | Documentation checks; no code unless explicitly requested. |
| RM-501 | Planned | Session 22 | Implement the first narrow UI slice. | RM-500 and stable artifact contracts. | Chosen UI code, stable artifact specs, [DESIGN](../DESIGN.md) | First UI surface around existing artifacts | UI tests if present; local browser inspection for significant frontend changes. |

## Phase 6: Post-Session Audit And Next Stage

Goal: reconcile the project after Sessions 01-20, then stabilize the new decision pipeline before
adding larger product surfaces or analytics.

Exit condition: stale status docs are synced, the decision package has a clear report/export surface,
source text is clean enough for user-facing reports, and the next analytical/UI work has accepted specs.

| ID | Status | Session | Work item | Prerequisites | Owning docs/code | Artifact or output | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RM-600 | Done | Post-closure 1-4 | Perform the post-session deep audit, including concept comparison, weak-block triage, mojibake triage, and Main-vs-robust optimizer review. | Sessions 01-20 complete. | [post-session audit](audits/2026-05-17_post_session_deep_system_audit.md), this roadmap, [known issues](../KNOWN_ISSUES.md), [decisions](../DECISIONS.md) | New audit and next-stage backlog | `python scripts/verify_docs.py`. |
| RM-601 | Done | Post-audit Session 01 | Create the post-audit stabilization and analytics ExecPlan. | RM-600. | [post-audit ExecPlan](exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md), this roadmap | Sessionized handoff plan for RM-610 through RM-622 | `python scripts/verify_docs.py`. |
| RM-610 | Done | Post-audit Session 02 | Sync top-level current-status docs after Sessions 01-20. | RM-601. | [README](../README.md), [AGENTS](../AGENTS.md), [SPEC](../SPEC.md), [PRODUCT](../PRODUCT.md), [ARCHITECTURE](../ARCHITECTURE.md), this roadmap, [post-audit ExecPlan](exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md) | Implemented file-first V1 decision artifacts no longer described as target/TBD in top-level docs | `python scripts/verify_docs.py`; targeted stale-reference search for Selection/Health/Monitoring/Journal TBD wording. |
| RM-611 | Done | Post-audit Session 03 | Fix decision-log and planning-doc integrity issues. | RM-601. | [DECISIONS](../DECISIONS.md), [post-audit ExecPlan](exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md), this roadmap | Unique decision IDs; handoff text now points to Session 04 | `python scripts/verify_docs.py`; targeted search for `DEC-2026-05-17-003` references. |
| RM-612 | Done | Post-audit Sessions 04, 06, 07 | Update detailed specs and report/PDF surfaces for the full decision package. | RM-610 recommended. | [decision package reporting spec](specs/decision_package_reporting_spec.md), [decision_package_reporting.py](../src/decision_package_reporting.py), [reporting outputs spec](specs/reporting_outputs_spec.md), [pdf_reports.py](../src/pdf_reports.py) | `decision_package_summary.txt` / `.json`, `report.txt` append, CLI paths, optional `Main portfolio_decision_package.pdf` | `tests/test_decision_package_reporting.py`; `python scripts/verify_docs.py`. |
| RM-613 | In progress | Post-audit Session 05 | Fix remaining source/generator mojibake, broken symbols, and English-language acceptance gaps. | RM-600. | `src/pdf_reports.py`, runner scripts, robust optimizer scripts/specs, [DESIGN](../DESIGN.md), affected docs | Source/generator text is cleaned; representative generated output refresh remains for report/PDF sessions | Targeted Cyrillic/mojibake source scans pass; `python scripts/verify_docs.py` passes. |
| RM-614 | Done | Post-audit Sessions 08, 09 | Define and harden current-vs-policy/no-trade workflow. | RM-301, RM-310, RM-601. | [current vs policy workflow spec](specs/current_vs_policy_workflow_spec.md), [current_vs_policy.py](../src/current_vs_policy.py), `run_report.py`, candidate comparison, runners | Sidecar materialization, status JSON, No-Trade actionability gating | `tests/test_current_vs_policy_workflow.py`; `python scripts/verify_docs.py`. |
| RM-615 | Done | Post-audit Sessions 10, 11 | Orchestrate candidate generation as a factory before comparison and implement the factory CLI. | RM-601. | [candidate factory spec](specs/candidate_factory_spec.md), [run_candidate_factory.py](../run_candidate_factory.py), [candidate_factory.py](../src/candidate_factory.py) | `candidate_factory_run.json` / `.txt` under `output_dir_final` | `tests/test_candidate_factory.py` |
| RM-616 | Done | Post-audit Sessions 12–13 | Specify and implement the trade-off explanation and model-risk diagnostics layer. | RM-612 recommended. | [tradeoff_and_model_risk.py](../src/tradeoff_and_model_risk.py), [candidate_comparison.py](../src/candidate_comparison.py), [decision_package_reporting.py](../src/decision_package_reporting.py) | `tradeoff_explanation.json` / `.txt`, `model_risk_diagnostics.json` / `.txt` under `output_dir_final` | `tests/test_tradeoff_and_model_risk.py`; wired in comparison pipeline. |
| RM-620 | In progress | Post-audit Sessions 14–15 | Specify and implement Assumption Sensitivity. Session 14 done (spec); Session 15 implements module. | RM-610 and RM-612 recommended. | [assumption_sensitivity_spec.md](specs/assumption_sensitivity_spec.md) | `assumption_sensitivity.json` / `.txt` and tests | `python scripts/verify_docs.py`; focused tests in Session 15. |
| RM-621 | Planned | Post-audit Sessions 16, 17 | Specify and implement Pareto/Dominance. | RM-620 recommended. | Selection/comparison specs and modules | Pareto/dominance artifact and tests | New focused tests. |
| RM-622 | Planned | Post-audit Sessions 18, 19 | Specify and implement Regret Analysis. | RM-620 recommended. | Selection/comparison/scenario specs and modules | Regret artifact and tests | New focused tests. |
| RM-623 | Planned | Post-audit Session 20 | Close the post-audit plan with broad verification and project-memory updates. | RM-610 through RM-622 complete or explicitly deferred. | [post-audit ExecPlan](exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md), [CHANGELOG](../CHANGELOG.md), [known issues](../KNOWN_ISSUES.md), [decisions](../DECISIONS.md) | Closure note and updated project registers | Docs verify, focused tests, relevant smoke run when data allows. |

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
| PSA-001 through PSA-013 | Registered in the [post-session audit](audits/2026-05-17_post_session_deep_system_audit.md); follow-up work starts at RM-610. |

## Session Boundary Rule

Use [the post-audit ExecPlan](exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md)
for RM-610 and later post-audit work. Complete one post-audit session per fresh chat unless the user
explicitly asks to combine sessions. Update that ExecPlan after each session with completed, partial,
or blocked status.

## Implemented Decision Artifacts

These artifacts now have accepted V1 specs and implementations:

- `candidate_comparison.json`
- `robustness_scorecard.json`
- `portfolio_health_score.json`
- `selection_decision.json`
- `action_plan.json`
- `monitoring_diff.json`
- `decision_journal.json`
