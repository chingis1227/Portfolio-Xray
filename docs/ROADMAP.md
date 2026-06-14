# Project Roadmap

This file is the durable roadmap and backlog for Portfolio MRI / Optimization Terminal /
Portfolio MRI. It turns the product concept, audit findings, and current implementation state into
an ordered development sequence.

This is a planning document. It does not override [SPEC.md](../SPEC.md), [RULES.md](../RULES.md),
[OUTPUTS.md](../OUTPUTS.md), [TESTING.md](../TESTING.md), or the detailed specs under
[docs/specs/](specs/README.md). Product ideas become binding only after the relevant source-of-truth
spec and implementation are updated.

## Current Development Rule

Current product direction is diagnosis-first and decision-support oriented: Input Portfolio ->
Portfolio Diagnosis -> Stress Test Lab -> Problem Classification -> Candidate Launchpad -> Portfolio
Alternatives Builder -> Current vs Candidate Comparison -> Decision Verdict -> AI Commentary
grounding -> Monitoring / What Changed. Optimizers, candidate factories, scorecards, and full
multi-candidate research remain implementation/advanced evidence unless an active canonical spec
explicitly promotes a surface to Core MVP.

**Active (2026-05-29):** [Blocks 1–3 post-audit development plan](exec_plans/2026-05-29_blocks_1_3_post_audit_development_plan.md) — Phase D in progress: Session 10 **done** (Block 5 Current vs Candidate + Decision Verdict contracts + live E2E). Phase A closed (`READY_FOR_DECISION_WORKFLOW`). Next: Sessions 11–12 (AI commentary / decision package). Operator contract: [runtime_artifact_contract.md](runtime_artifact_contract.md).

Active alignment work: **closed** 2026-05-25 — [Post-Audit Portfolio MRI Architecture Alignment Roadmap](exec_plans/2026-05-25_post_architecture_alignment_roadmap.md) (Sessions 01–12), based on the [Full Project Architecture Alignment Audit](audits/2026-05-25_full_project_architecture_alignment_audit.md). Closure: [Session 12 closure report](audits/2026-05-25_post_architecture_alignment_session12_closure_report.md). Older phases below are retained as historical project memory and implementation traceability; they do not override the current diagnosis-first product direction.

Architecture-alignment backlog (diagnosis-first docs; not a code milestone until approved):

| ID | Status | Scope | Notes |
| --- | --- | --- | --- |
| RM-ARCH-010 | Backlog | Natural-language AI Commentary generation spec | Requires separate spec (provider, prompts, output schema, citation rules, guardrail tests). Current implementation stops at `ai_commentary_context.json` per [ai_commentary_grounding_spec.md](specs/ai_commentary_grounding_spec.md). Do not add LLM calls until this row is accepted and implemented. |
| RM-ARCH-011 | **Done** (2026-05-26) | Product bundle runtime wiring (no merged bundle file) | Closed via [Product Flow MVP Backend ExecPlan](exec_plans/2026-05-25_product_flow_mvp_backend_plan.md) Sessions 02–03: `src/product_bundle_paths.py`, compare sidecar for AI commentary / What Changed, manifest `product_bundle_*` keys, offline + path tests. Evidence: [Product-Flow Validation Audit closure](audits/2026-05-25_product_flow_validation_audit.md) § Session 08; [demo baseline snapshot](audits/2026-05-25_product_flow_demo_baseline_snapshot.md). Do **not** add a merged `product_bundle.json` unless a later spec approves it. |

Post-audit stabilization (RM-610 through RM-623, Sessions 02–20) is **complete** as of 2026-05-17.
The file-first V1 decision pipeline is implemented end-to-end through `write_candidate_comparison_outputs`.
Do not add new major analytics without an accepted spec and roadmap row. Current active backlog:

```text
Post-portfolio-first stabilization (RM-900 -> RM-911) closed as of 2026-05-19
Portfolio Diagnosis evidence deepening (RM-930 -> RM-939): **closed** as of 2026-05-20 (Session 09).
Portfolio Diagnosis post-audit governance (RM-940 -> RM-950): **closed** as of 2026-05-20 (Session 10).
Baseline: [Portfolio Diagnosis Baseline Snapshot](audits/2026-05-20_portfolio_xray_baseline_snapshot.md).
Stress Lab methodology governance (RM-951 -> RM-961): **closed** as of 2026-05-20 (Sessions 00-11).
Plan: [Stress Lab Methodology Governance Plan](exec_plans/2026-05-20_stress_lab_methodology_governance_plan.md).
Methodology map: [Stress Lab Methodology Map](audits/2026-05-20_stress_lab_methodology_map.md).
Baseline: [Stress Lab Baseline Snapshot](audits/2026-05-20_stress_lab_baseline_snapshot.md).
Candidate Portfolio Factory governance (RM-970 -> RM-981): **closed** as of 2026-05-20 (Sessions 00-11).
Plan: [Candidate Portfolio Factory Post-Audit Roadmap](exec_plans/2026-05-20_candidate_factory_post_audit_roadmap.md).
Methodology map: [Candidate Factory Methodology Map](audits/2026-05-20_candidate_factory_methodology_map.md).
Baseline: [Candidate Factory Baseline Snapshot](audits/2026-05-20_candidate_factory_baseline_snapshot.md).
Note: RM-921 resumable factory is scheduled in Phase 14 Session 09 (RM-979), not deferred indefinitely.
Optimization Engine governance (RM-990 -> RM-1002): **closed** as of 2026-05-21 (Sessions 00-12 complete).
Plan: [Optimization Engine Post-Audit Roadmap](exec_plans/2026-05-20_optimization_engine_post_audit_roadmap.md).
Methodology map: [Optimization Engine Methodology Map](audits/2026-05-20_optimization_engine_methodology_map.md).
Baseline: [Optimization Engine Baseline Snapshot](audits/2026-05-20_optimization_engine_baseline_snapshot.md).
Blocks 1-5 MVP core reliability (RM-1010 -> RM-1018): **closed** as of 2026-05-21 (Session 09 complete).
Plan: [Blocks 1-5 MVP Core Reliability Plan](exec_plans/2026-05-21_blocks_1_5_mvp_core_reliability_plan.md).
Scope: harden the existing portfolio-first MVP core without adding UI, new optimizer methodology,
new stress methodology, new constraints, or new candidate behavior.
Post-deep-audit foundation (RM-1020 -> RM-1029): **closed** as of 2026-05-22 (Session 10 complete).
Plan: [Post-Deep-Audit Foundation Plan](exec_plans/2026-05-21_post_deep_audit_foundation_plan.md).
Audit: [Blocks 1-5 Deep Audit Snapshot](audits/2026-05-21_blocks_1_5_deep_audit_snapshot.md).
Scope: live E2E, selection/health guards, optimizer fairness backfill, preflight, freshness, downstream readiness; no formula/UI changes.
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

Completed plan: [Portfolio Diagnosis Diagnostics Deepening Plan](exec_plans/2026-05-19_portfolio_xray_diagnostics_deepening_plan.md)
(Sessions 00-09, closed 2026-05-20). Deepened the current-portfolio diagnostic layer: data cutoff,
diagnosis evidence completeness, VaR / ES, portfolio metrics, hidden risk, weakness map, archetype,
report productization, and operational portfolio-first review modes.

Completed plan: [Portfolio Diagnosis Post-Audit Roadmap](exec_plans/2026-05-20_portfolio_xray_post_audit_roadmap.md)
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
| RM-920 | Done | Diagnosis Session 09 | Split portfolio-first review into **core-run** and **full-run** CLI modes/profiles (`core_v1` vs `default_v1`). | RM-911. | [run_portfolio_review.py](../run_portfolio_review.py), [portfolio_review_workflow.py](../src/portfolio_review_workflow.py), [candidate_factory.py](../src/candidate_factory.py), [operational_runbook.md](operational_runbook.md) | `--mode core` (default) and `--mode full` | `tests/test_portfolio_review_workflow.py`; operational runbook. |
| RM-921 | Done (resumable scope; parallel report scope shipped opt-in) | Session 09 (`RM-979`); 2026-05-22 parallel report plan Sessions 1-4 | Improve factory orchestration operations: resumable steps via manifest + `--resume`; opt-in parallel Phase 2 `lightweight_comparison` reports for eligible `standard` runs. Remaining: parallel candidate builders are still out of scope. | RM-902 freshness contract; RM-979. | [candidate_factory.py](../src/candidate_factory.py), [candidate_factory_spec.md](specs/candidate_factory_spec.md), [operational_runbook.md](operational_runbook.md) | Operators can resume long runs without redoing succeeded steps and can opt into parallel lightweight report generation without changing weights/formulas | `tests/test_candidate_factory.py` resume + parallel lightweight report tests; `python scripts/verify_docs.py`. |
| RM-982 | Done | Shared Evidence Sessions 0–6 (2026-05-23) | Eliminate 16× invariant recomputation in Phase 2 `lightweight_comparison` via `CandidateRunContext` v2–v5 (metrics/corr/cov, factor weekly frames, prepared stress). Orchestration/caching only. | RM-921; [shared evidence ExecPlan](exec_plans/2026-05-23_candidate_factory_shared_evidence_plan.md) | [candidate_run_context.py](../src/candidate_run_context.py), [run_report.py](../run_report.py), [stress.py](../src/stress.py), [stress_factors.py](../src/stress_factors.py) | Measured **−28.1%** sequential `report_seconds` vs 1192.9 s baseline (below −35% goal — [Session 06 timing audit](audits/2026-05-23_candidate_factory_shared_evidence_session06_timing_audit.md)); pytest parity bundle **106** passed | Session 7 batch API deferred; further speedup needs macro_regime/tail-risk/PCA scope |
| RM-983 | Done | Performance Wave 2 Sessions 0–8 (2026-05-24) | **`core_fast` E2E ≤ 300 s** warm cache via `ReviewRunContext`, parallel lightweight factory, fast `analysis_subject`, shared macro/PCA caches, lightweight 10Y trims. Orchestration only. | RM-982; [performance wave 2 ExecPlan](exec_plans/2026-05-24_blocks_1_5_performance_wave2_plan.md); [E2E timing audit](audits/2026-05-24_blocks_1_5_e2e_timing_audit.md) | [portfolio_review_workflow.py](../src/portfolio_review_workflow.py), [candidate_run_context.py](../src/candidate_run_context.py), [candidate_factory.py](../src/candidate_factory.py), [run_report.py](../run_report.py), [blocks_1_5_e2e_timing_audit.py](../scripts/blocks_1_5_e2e_timing_audit.py) | **210.7 s** measured `core_fast_parallel` (Session 8); baseline **542.5 s** core_v1 | Session 8: E2E gate **PASS**; parity **138 passed**; `verify_docs.py` OK |
| RM-922 | Done | Diagnosis Session 09 | Add explicit **partial candidate menu** disclosure in comparison and decision-package outputs. | RM-920. | [candidate_comparison.py](../src/candidate_comparison.py), [decision_package_reporting.py](../src/decision_package_reporting.py), [candidate_comparison_spec.md](specs/candidate_comparison_spec.md) | `candidate_menu` block + decision summary | `tests/test_candidate_comparison.py`. |

**Direction (not yet implemented):** cache/reuse candidates only when `analysis_end`, config fingerprint,
universe, weights, and material assumptions match; do not default to rebuilding every expensive
optimizer on every `run_portfolio_review.py` invocation.

## Phase 11: Portfolio Diagnosis Diagnostics Deepening

Goal: make the current-portfolio diagnostic layer trustworthy and decision-useful before UI,
advanced optimization, or heavier product surfaces. This phase follows the 2026-05-19 Portfolio
Portfolio Diagnosis Technical Layer Audit and is governed by the active
[Portfolio Diagnosis Diagnostics Deepening Plan](exec_plans/2026-05-19_portfolio_xray_diagnostics_deepening_plan.md).

Exit condition: `analysis_subject` diagnostics use analysis-effective data, expose complete risk
budget and factor evidence, align tail-risk methodology with the metrics spec, include richer
portfolio metrics, and present hidden risk, weakness, and archetype evidence with confidence and
caveats. Report surfaces should be readable without inspecting raw JSON.

| ID | Status | Session | Work item | Prerequisites | Owning docs/code | Artifact or output | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RM-930 | Done | Diagnosis Session 00 | Create Portfolio Diagnosis audit memory, active ExecPlan, dedicated diagnostics spec scaffold, roadmap rows, known issues, and registers. | User-approved Diagnosis roadmap. | [Portfolio Diagnosis audit](audits/2026-05-19_portfolio_xray_layer_audit.md), [Diagnosis ExecPlan](exec_plans/2026-05-19_portfolio_xray_diagnostics_deepening_plan.md), [Diagnosis spec](specs/portfolio_xray_diagnostics_spec.md), [known issues](../KNOWN_ISSUES.md), this roadmap | Active plan and source-of-truth scaffold for Sessions 01-09 | `python scripts/verify_docs.py`. |
| RM-931 | Done | Diagnosis Session 01 | Fix P0 data cutoff and `analysis_end` integrity across diagnostic consumers. | RM-930. | [windows.py](../src/windows.py), [run_report.py](../run_report.py), [io_export.py](../src/io_export.py), [stress_scenario_analytics.py](../src/stress_scenario_analytics.py), [scenario_library.py](../src/scenario_library.py), [data policy spec](specs/data_policy_spec.md), [DATA](../DATA.md) | Diagnostics use rows `<= analysis_end`; raw cache vs analysis-effective panels documented | `tests/test_analysis_end_cutoff.py`; fresh subject run should show no diagnostic `data_end` after `analysis_end`. |
| RM-932 | Done | Diagnosis Session 02 | Fix P0 diagnosis evidence completeness: full risk contribution data and Kalman factor beta mapping. | RM-931 recommended. | [portfolio_xray.py](../src/portfolio_xray.py), [snapshot.py](../src/snapshot.py), [portfolio_commentary.py](../src/portfolio_commentary.py), [Diagnosis spec](specs/portfolio_xray_diagnostics_spec.md), [OUTPUTS](../OUTPUTS.md) | Risk budget includes all positive-weight holdings with RC evidence; Kalman betas surface when available | `tests/test_portfolio_xray.py` (`test_resolve_rc_asset_prefers_full_csv_over_snapshot_top5`, `test_portfolio_xray_v2_kalman_reads_factor_betas_kalman_latest`). |
| RM-933 | Done | Diagnosis Session 03 | Align VaR / ES methodology with canonical metrics spec or explicitly revise the spec. | RM-932. | [portfolio_analytics.py](../src/portfolio_analytics.py), [data_loader.py](../src/data_loader.py), [run_report.py](../run_report.py), [metrics spec](specs/metrics_specification.md) | Tail metrics disclose method, frequency, and window; docs and generated output agree | `tests/test_tail_risk.py`, `tests/test_portfolio_xray.py`. |
| RM-934 | Done | Diagnosis Session 04 | Add missing portfolio metrics and quality metadata. | RM-933. | `src/metrics_*`, [portfolio_analytics.py](../src/portfolio_analytics.py), [run_report.py](../run_report.py), [Diagnosis spec](specs/portfolio_xray_diagnostics_spec.md) | Diagnosis risk diagnostics include skew/kurtosis, downside/upside beta, rolling beta/correlation, and quality metadata | `tests/test_portfolio_metrics_deepening.py`. |
| RM-935 | Done | Diagnosis Session 05 | Build Hidden Risk Detector V2 with explicit flags, non-flags, evidence counts, and confidence. | RM-934. | [portfolio_xray.py](../src/portfolio_xray.py), [Diagnosis spec](specs/portfolio_xray_diagnostics_spec.md) | Per-category flagged/below-threshold/unavailable assessments; section confidence and counts | `python -m pytest tests/test_portfolio_xray.py -q` (hidden-risk tests). |
| RM-936 | Done | Diagnosis Session 06 | Build Weakness Map V2 with exposure, adverse evidence, severity, confidence, and drivers. | RM-935. | [portfolio_xray.py](../src/portfolio_xray.py), [portfolio_xray diagnostics spec](specs/portfolio_xray_diagnostics_spec.md), tests | Weakness rows separate exposure vs adverse evidence; top asset/factor drivers; conditional crypto_shock | `tests/test_portfolio_xray.py` weakness V2 tests; `python scripts/verify_docs.py`. |
| RM-937 | Done | Diagnosis Session 07 | Rework Portfolio Archetype as an evidence scorecard with conflicts and caveats. | RM-936. | [portfolio_xray.py](../src/portfolio_xray.py), [Diagnosis spec](specs/portfolio_xray_diagnostics_spec.md), [PRODUCT](../PRODUCT.md) | Legacy `sections.portfolio_archetype` includes positive/negative evidence, confidence, conflicting signals (**not** Core MVP product surface; see spec §2.5) | `python -m pytest tests/test_portfolio_xray.py -q` (archetype V2 tests). |
| RM-938 | Done | Diagnosis Session 08 | Productize diagnosis report/HTML/PDF presentation. | RM-931 through RM-937 stable. | [snapshot.py](../src/snapshot.py), [portfolio_xray.py](../src/portfolio_xray.py), [portfolio_commentary.py](../src/portfolio_commentary.py), [generated_output_qa.py](../src/generated_output_qa.py), [DESIGN](../DESIGN.md), [OUTPUTS](../OUTPUTS.md) | Reports show structured Diagnosis sections instead of raw JSON-style dumps | `format_portfolio_xray_html` / `format_portfolio_xray_commentary`; QA scans; `tests/test_portfolio_xray.py`. |
| RM-939 | Done | Diagnosis Session 09 | Implement operational portfolio-first review modes after Diagnosis trust fixes. | RM-938. | [run_portfolio_review.py](../run_portfolio_review.py), [portfolio_review_workflow.py](../src/portfolio_review_workflow.py), [candidate_factory.py](../src/candidate_factory.py), [candidate_comparison.py](../src/candidate_comparison.py), [decision_package_reporting.py](../src/decision_package_reporting.py), [operational runbook](operational_runbook.md) | Core/full modes + partial menu disclosure | Focused workflow, factory, comparison, reporting tests. |

## Phase 12: Portfolio Diagnosis Post-Audit Governance

Goal: make Block 2 (Portfolio Diagnosis) **audit-grade** — transparent thresholds, provenance metadata,
factor inference surfacing, multi-window metrics, layer spec, contract tests, and baseline snapshot.

Exit condition: methodology map and layer navigation exist in repo; spec owns thresholds; sections
disclose frequency/window where applicable; contract tests prevent schema drift; documentation registers
match runtime.

Governed by the completed
[Portfolio Diagnosis Post-Audit Roadmap](exec_plans/2026-05-20_portfolio_xray_post_audit_roadmap.md)
(Sessions 00–10 closed 2026-05-20).
Methodology baseline:
[Portfolio Diagnosis Methodology Map](audits/2026-05-20_portfolio_xray_methodology_map.md).

| ID | Status | Session | Work item | Prerequisites | Owning docs/code | Artifact or output | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RM-940 | Done | Diagnosis Post-Audit Session 00 | Project memory: methodology map, ExecPlan, registers, ROADMAP Phase 12. | 2026-05-20 methodology audit. | [methodology map](audits/2026-05-20_portfolio_xray_methodology_map.md), [post-audit ExecPlan](exec_plans/2026-05-20_portfolio_xray_post_audit_roadmap.md), [audits/README](audits/README.md), [exec_plans/README](exec_plans/README.md) | Active handoff for Sessions 01-10 | `python scripts/verify_docs.py`. |
| RM-941 | Done | Session 01 | Doc sync: close stale KNOWN_ISSUES (RC/Kalman); mark RM-932 Done; CHANGELOG; TESTING bundle stub. | RM-940. | [KNOWN_ISSUES](../KNOWN_ISSUES.md), [ROADMAP](ROADMAP.md), [CHANGELOG](../CHANGELOG.md), [TESTING](../TESTING.md) | Registers match deepening wave runtime | `python scripts/verify_docs.py`; Portfolio Diagnosis regression bundle stub in TESTING.md. |
| RM-942 | Done | Session 02 | Canonical threshold registry in spec + validation tests. | RM-941. | [portfolio_xray_diagnostics_spec.md](specs/portfolio_xray_diagnostics_spec.md) §8, [portfolio_xray.py](../src/portfolio_xray.py), [test_portfolio_xray_threshold_registry.py](../tests/test_portfolio_xray_threshold_registry.py) | Spec-owned `XRAY_THRESHOLDS`; drift tests | `python -m pytest tests/test_portfolio_xray_threshold_registry.py -q`. |
| RM-943 | Done | Session 03 | Section provenance metadata (frequency/window/n_obs/benchmark). | RM-942. | [portfolio_xray.py](../src/portfolio_xray.py), Diagnosis spec §2.2–2.7 | Sections 2.2/2.3/2.6/2.7 disclose provenance | `tests/test_portfolio_xray.py` (`test_portfolio_xray_section_provenance_metadata`). |
| RM-944 | Done | Session 04 | Factor regression inference panel (read-only from stress_report). | RM-943. | [portfolio_xray.py](../src/portfolio_xray.py), [stress_testing_spec.md](specs/stress_testing_spec.md) | Inference visible when stress provides it | `test_portfolio_xray_factor_regression_inference_panel`. |
| RM-945 | Done | Session 05 | Multi-window metrics + TTR in risk diagnostics. | RM-944. | [snapshot.py](../src/snapshot.py), [portfolio_xray.py](../src/portfolio_xray.py) | `multi_window_metrics` panel; `ttr_months`/`recovered` on primary metrics | `test_portfolio_xray_multi_window_metrics_panel`, `test_portfolio_xray_ttr_in_primary_risk_metrics`, `test_load_portfolio_windows_from_dir`. |
| RM-946 | Done | Session 06 | Create `portfolio_xray_layer_spec.md`. | RM-945. | [portfolio_xray_layer_spec.md](specs/portfolio_xray_layer_spec.md), [SPEC.md](../SPEC.md) | Block 2 layer map 2.1–2.7 | `python scripts/verify_docs.py`. |
| RM-947 | Done | Session 07 | Allocation concentration (HHI, top-N). | RM-946. | [portfolio_xray.py](../src/portfolio_xray.py), Diagnosis spec §2.1 | `weight_concentration` item in asset_allocation | `test_portfolio_xray_weight_concentration_in_asset_allocation`. |
| RM-948 | Done | Session 08 | `volatility_spike` methodology: Option B factor-only (`beta_vix`, ES_95); spec + `scenario_coverage` contract. | RM-947. | [portfolio_xray_diagnostics_spec.md](specs/portfolio_xray_diagnostics_spec.md) §2.7, [portfolio_xray.py](../src/portfolio_xray.py) | Documented vol-spike rule; no new stress scenario | `test_volatility_spike_weakness_factor_only_methodology`. |
| RM-949 | Done | Session 09 | Golden contract tests + TESTING bundle. | RM-948. | [tests/fixtures/portfolio_xray_golden_v2.json](../tests/fixtures/portfolio_xray_golden_v2.json), [test_portfolio_xray_contract.py](../tests/test_portfolio_xray_contract.py), [TESTING.md](../TESTING.md) | Golden JSON + schema drift tests | `python -m pytest tests/test_portfolio_xray_contract.py tests/test_portfolio_xray.py tests/test_portfolio_xray_threshold_registry.py -q`. |
| RM-950 | Done | Session 10 | Baseline snapshot + wave closure. | RM-949. | [baseline snapshot](audits/2026-05-20_portfolio_xray_baseline_snapshot.md), ExecPlan, ROADMAP | `2026-05-20_portfolio_xray_baseline_snapshot.md`; Phase 12 closed | verify_docs + Diagnosis bundle (40 tests). |

Note: `RM-932` (full RC + Kalman in Diagnosis) was implemented in the deepening Session 02; post-audit
Session 01 marked it **Done** in Phase 11 and removed stale `KI-2026-05-19-007` / `KI-2026-05-19-008`
from active KNOWN_ISSUES.

## Phase 13: Stress Lab Methodology Governance

Goal: make Block 3 (Stress Test Lab) **audit-grade** — transparent methodology boundary, conclusions
integrity, hedge/replay/factor decision context, layer spec handoff, spec-only proposals for new scenarios.

Exit condition: methodology map and governance ExecPlan exist in repo; gaps G1–G3 closed; G4–G7
implemented per plan; verification bundle and baseline snapshot updated; documentation registers match runtime.

Governed by the active
[Stress Lab Methodology Governance Plan](exec_plans/2026-05-20_stress_lab_methodology_governance_plan.md)
(Sessions 00–11). Methodology baseline:
[Stress Lab Methodology Map](audits/2026-05-20_stress_lab_methodology_map.md).

| ID | Status | Session | Work item | Prerequisites | Owning docs/code | Artifact or output | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RM-951 | Done | Session 00 | Project memory: methodology map, ExecPlan, registers, ROADMAP Phase 13, TESTING stub. | 2026-05-20 methodology audit. | [methodology map](audits/2026-05-20_stress_lab_methodology_map.md), [governance ExecPlan](exec_plans/2026-05-20_stress_lab_methodology_governance_plan.md) | Active handoff for Sessions 01–11 | `python scripts/verify_docs.py`. |
| RM-952 | Done | Session 01 | Worst historical episode by max_dd in stress_conclusions. | RM-951. | [stress.py](../src/stress.py), [stress_testing_spec.md](specs/stress_testing_spec.md) §12.1 | Consistent worst_historical_episode | `tests/test_stress_scorecard_contract.py`. |
| RM-953 | Done | Session 02 | Historical realized-vs-proxy boundary + disclosure on historical_results. | RM-952. | [stress.py](../src/stress.py), [DECISIONS.md](../DECISIONS.md), stress spec §9 | `return_method` / `historical_methodology` | `tests/test_stress_historical_fields.py`. |
| RM-954 | Done | Session 03 | Hedge analysis N/A transparency (status_reason, commentary). | RM-953. | [hedge_gap_analysis_spec.md](specs/hedge_gap_analysis_spec.md), [portfolio_commentary.py](../src/portfolio_commentary.py) | `not_applicable` + `no_hedge_labels` when no taxonomy hedge roles | `tests/test_stress_hedge_gap_contract.py`. |
| RM-955 | Done | Session 04 | Factor drivers in stress_conclusions. | RM-954. | [stress.py](../src/stress.py), stress spec §12.1 | top_factor_drivers on worst synthetic | scorecard/conclusions contract tests. |
| RM-956 | Done | Session 05 | Hedge gap v2 by risk type (`by_risk_type[]`, `HEDGE_GAP_SCENARIO_BY_RISK`). | RM-955. | [hedge_gap_analysis_spec.md](specs/hedge_gap_analysis_spec.md), [stress.py](../src/stress.py) | `by_risk_type[]` on hedge_gap_analysis | `tests/test_stress_hedge_gap_contract.py`. |
| RM-957 | Done | Session 06 | Crisis replay v2 (recovery + asset episode contrib). | RM-956. | [crisis_replay_spec.md](specs/crisis_replay_spec.md), [run_report.py](../run_report.py) | `crisis_replay_v2` path fields + `_asset_contrib.csv` | `tests/test_stress_historical_fields.py`. |
| RM-958 | Done | Session 07 | Deepen stress_lab_layer_spec.md (handoff-grade 3.1–3.6). | RM-957. | [stress_lab_layer_spec.md](specs/stress_lab_layer_spec.md) | Layer navigation without chat | `python scripts/verify_docs.py`. |
| RM-959 | Done | Session 08 | crypto/vol synthetic scenarios — spec-only + DECISIONS. | RM-958. | [proposal](proposals/2026-05-20_crypto_vol_stress_scenarios_proposal.md), [DECISIONS.md](../DECISIONS.md) | DEC-2026-05-20-002 defer; stress spec §2.3; G8 closed | `python scripts/verify_docs.py`. |
| RM-960 | Done | Session 09 | Optional custom_shock run artifact. | RM-959. | [stress.py](../src/stress.py), stress spec §12.3 | `custom_shock_runs.json` opt-in | `tests/test_stress_simulator_contract.py`. |
| RM-961 | Done | Session 11 | Downstream integration + verification closure. | RM-960. | [snapshot.py](../src/snapshot.py), [candidate_comparison.py](../src/candidate_comparison.py), [portfolio_commentary.py](../src/portfolio_commentary.py), [TESTING.md](../TESTING.md), baseline snapshot | Session 10: mirrors; Session 11: 90-test bundle + baseline closure | `tests/test_stress_downstream_integration.py` + governance pytest bundle (90 passed) + verify_docs. |

## Phase 14: Candidate Portfolio Factory Governance

Goal: make Block 4 (Candidate Portfolio Factory / Portfolio Menu) **audit-grade** — explicit factory
failure reasons, config-aware freshness, construction disclosure in comparison, layer spec handoff,
resumable long runs, and a regression bundle—without new candidate types, UI, or optimizer changes.

Exit condition: methodology map and governance ExecPlan in repo; gaps G1, G3, G6, G8, G10 addressed;
P1–P4 implemented per accepted specs; P5 documented; verification bundle and baseline snapshot updated.

Governed by the active
[Candidate Portfolio Factory Post-Audit Roadmap](exec_plans/2026-05-20_candidate_factory_post_audit_roadmap.md)
(Sessions 00–11). Methodology baseline:
[Candidate Factory Methodology Map](audits/2026-05-20_candidate_factory_methodology_map.md).

| ID | Status | Session | Work item | Prerequisites | Owning docs/code | Artifact or output | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RM-970 | Done | Session 00 | Project memory: methodology map link, ExecPlan, registers, ROADMAP Phase 14, baseline snapshot, TESTING stub. | 2026-05-20 methodology audit. | [methodology map](audits/2026-05-20_candidate_factory_methodology_map.md), [baseline snapshot](audits/2026-05-20_candidate_factory_baseline_snapshot.md), [governance ExecPlan](exec_plans/2026-05-20_candidate_factory_post_audit_roadmap.md) | Active handoff for Sessions 01–11 | `python scripts/verify_docs.py`; factory/comparison/workflow pytest stub. |
| RM-971 | Done | Session 01 | Documentation sync (CHANGELOG, KNOWN_ISSUES, SPEC links). | RM-970. | [CHANGELOG](../CHANGELOG.md), [KNOWN_ISSUES](../KNOWN_ISSUES.md), [SPEC.md](../SPEC.md), [OUTPUTS.md](../OUTPUTS.md) | Registers match audit G1–G10 | `python scripts/verify_docs.py`. |
| RM-972 | Done | Session 02 | Builder FAIL_* → factory `reason_code` (G1, P1). | RM-971. | [candidate_factory.py](../src/candidate_factory.py), [candidate_factory_spec.md](specs/candidate_factory_spec.md) | Explicit infeasible/config reasons in run JSON | `tests/test_candidate_factory.py` (16 passed). |
| RM-973 | Done | Session 03 | Freshness when `analysis_end` missing (G3). | RM-972. | [candidate_factory.py](../src/candidate_factory.py), [candidate_comparison_spec.md](specs/candidate_comparison_spec.md) | No silent unchecked skip | `tests/test_candidate_factory.py` + `tests/test_candidate_comparison.py` (36 passed). |
| RM-974 | Done | Session 04 | `construction_disclosure` in comparison (G6, P3). | RM-971. | [candidate_comparison.py](../src/candidate_comparison.py), [candidate_comparison_spec.md](specs/candidate_comparison_spec.md) | Metadata passthrough on rows | `tests/test_candidate_comparison.py` (40 passed). |
| RM-975 | Done | Session 05 | `candidate_factory_layer_spec.md`. | RM-974. | [candidate_factory_layer_spec.md](specs/candidate_factory_layer_spec.md) | Block 4.1–4.9 handoff doc | `verify_docs`. |
| RM-976 | Done | Session 06 | Config fingerprint freshness (G2, P2). | RM-975. | [candidate_factory.py](../src/candidate_factory.py), [snapshot.py](../src/snapshot.py), comparison spec | `stale_config_fingerprint` when mismatch | new + existing tests. |
| RM-977 | Done | Session 07 | Robust MV λ + robust_scenario Main deps (G8, G10). | RM-975. | [candidate_robust_disclosure.py](../src/candidate_robust_disclosure.py), [operational_runbook.md](operational_runbook.md) | `robust_paths_disclosure` + runbook | factory/comparison robust tests. |
| RM-978 | Done | Session 08 | Golden contract tests + TESTING bundle finalize. | RM-972–RM-977 stable. | [tests/fixtures/candidate_factory_run_golden_v1.json](../tests/fixtures/candidate_factory_run_golden_v1.json), [tests/fixtures/candidate_comparison_golden_v1.json](../tests/fixtures/candidate_comparison_golden_v1.json), [TESTING.md](../TESTING.md) | Golden JSON + bundle command | `python -m pytest tests/test_candidate_factory_contract.py tests/test_candidate_comparison_contract.py tests/test_candidate_factory.py tests/test_candidate_comparison.py tests/test_portfolio_review_workflow.py -q` (71 passed Session 08). |
| RM-979 | Done | Session 09 | Resumable factory (P4, closes RM-921 resumable scope). | RM-978. | [candidate_factory.py](../src/candidate_factory.py), [run_candidate_factory.py](../run_candidate_factory.py) | `--resume` + `candidate_factory_manifest.json` | factory resume tests (Session 09). |
| RM-980 | Done | Session 10 | Operational runbook factory UX. | RM-979. | [operational_runbook.md](operational_runbook.md), [candidate_factory.py](../src/candidate_factory.py) | §8 playbooks; contextual `next_recommended_command`; richer `candidate_factory_run.txt` | doc review + factory tests. |
| RM-981 | Done | Session 11 | Concept registry DEC + wave closure (P5). | RM-980. | [DECISIONS.md](../DECISIONS.md), [candidate_portfolios_spec.md](specs/candidate_portfolios_spec.md), baseline snapshot | Phase 14 closed; DEC-2026-05-20-003; G9 closed | full governance bundle + `verify_docs`. |

## Phase 15: Optimization Engine Governance

Goal: make Block 5 (Optimization Engine) **audit-grade** by separating optimizer roles, objective
formulas, estimators, constraints, failure handling, reproducibility metadata, and comparison
readiness without adding new optimizers or changing formulas silently.

Exit condition: methodology map and governance ExecPlan in repo; canonical Optimization Engine
layer spec accepted; target-only objectives documented; policy and candidate optimizer disclosures
are machine-readable; fallback and solver quality are explicit; comparison rows disclose optimizer
methodology; verification bundle and baseline snapshot updated.

Governed by the active
[Optimization Engine Post-Audit Roadmap](exec_plans/2026-05-20_optimization_engine_post_audit_roadmap.md)
(Sessions 00-12). Methodology baseline:
[Optimization Engine Methodology Map](audits/2026-05-20_optimization_engine_methodology_map.md).

| ID | Status | Session | Work item | Prerequisites | Owning docs/code | Artifact or output | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RM-990 | Done | Session 00 | Project memory: methodology map link, ExecPlan, registers, ROADMAP Phase 15, baseline snapshot, TESTING stub. | 2026-05-20 methodology audit. | [methodology map](audits/2026-05-20_optimization_engine_methodology_map.md), [baseline snapshot](audits/2026-05-20_optimization_engine_baseline_snapshot.md), [governance ExecPlan](exec_plans/2026-05-20_optimization_engine_post_audit_roadmap.md) | Active handoff for Sessions 01-12 | `python scripts/verify_docs.py`. |
| RM-991 | Done | Session 01 | Canonical `optimization_engine_layer_spec.md`. | RM-990. | docs/specs, `SPEC.md`, `OUTPUTS.md` | Block 5.1-5.11 source-of-truth spec | `python scripts/verify_docs.py`. |
| RM-992 | Done | Session 02 | Target-only objective decision log. | RM-991. | `DECISIONS.md`, optimization spec appendix | Max Sharpe/drawdown/macro/tax-turnover concepts cannot drift into code silently | `python scripts/verify_docs.py`; target-name search. |
| RM-993 | Done | Session 03 | Legacy policy optimizer disclosure. | RM-991. | `run_optimization.py`, `src/optimization.py`, policy spec | `run_result.json.optimizer_run_metadata` policy methodology block | focused legacy optimizer tests, Block 5 bundle, `verify_docs`. |
| RM-994 | Done | Session 04 | Candidate optimizer reproducibility envelope. | RM-991. | `src/portfolio_variants.py`, candidate specs | `baseline_weights_metadata.json.optimizer_run_metadata` on MinVar/MaxDiv/CVaR/Robust MV optimizer candidates | MinVar/MaxDiv/CVaR/Robust MV tests; Block 5 bundle; `verify_docs`. |
| RM-995 | Done | Session 05 | Comparison-level optimizer disclosure. | RM-994. | `src/candidate_comparison.py`, comparison spec | `construction_disclosure.optimizer_methodology` | `tests/test_candidate_comparison.py -q --basetemp=tmp\\pytest_session05_candidate_comparison`; `verify_docs`. |
| RM-996 | Done | Session 06 | Formal fallback and failure policy. | RM-995. | optimizer, factory, comparison modules/specs | normalized fallback/failure quality fields now propagate through factory steps, comparison readiness, and Selection warnings | Block 5 focused bundles; `verify_docs`. |
| RM-997 | Done | Session 07 | Robust scenario solver status contract. | RM-996. | `src/robust_scenario_optimization.py`, `run_robust_scenario_portfolio_report.py`, robust scenario/factory/comparison specs | normalized SLSQP solver quality is emitted in robust scenario summary and propagated through candidate metadata, factory evidence, and comparison disclosure | robust scenario, factory, comparison tests; `verify_docs`. |
| RM-998 | Done | Session 08 | Explicit `analysis_end` and input fingerprints. | RM-994. | `run_optimization.py`, `src/portfolio_variants.py`, optimizer input fingerprint helper, specs/tests | legacy/candidate optimizer metadata includes estimator input fingerprints and candidate young-ETF covariance receives explicit `analysis_end` | focused legacy/candidate optimizer metadata tests; `verify_docs`. |
| RM-999 | Done | Session 09 | Covariance and young ETF disclosure. | RM-998. | `run_optimization.py`, `src/portfolio_variants.py`, `src/candidate_comparison.py`, `src/io_export.py`, specs/tests | `optimizer_covariance_methodology_v1`, `optimizer_young_etf_methodology_v1`, comparison/IPS TXT notes | focused optimizer disclosure, comparison, IPS tests; `verify_docs`. |
| RM-1000 | Done | Session 10 | Optimization readiness for candidate comparison. | RM-999. | [optimization_readiness.py](../src/optimization_readiness.py), [candidate_comparison.py](../src/candidate_comparison.py), comparison/layer specs | `construction_disclosure.optimization_readiness` + `fair_comparison_ready` for optimizer-backed rows | `tests/test_optimization_readiness.py` + comparison bundle; `verify_docs`. |
| RM-1001 | Done | Session 11 | Golden contracts and Optimization governance bundle. | RM-993-RM-1000 stable. | [tests/fixtures](../tests/fixtures/), [optimization_engine_golden_inputs.py](../tests/optimization_engine_golden_inputs.py), [test_optimization_engine_contract.py](../tests/test_optimization_engine_contract.py), `TESTING.md` | Block 5 golden JSON + governance bundle (159 passed) | focused bundle + `verify_docs`. |
| RM-1002 | Done | Session 12 | Wave closure and documentation sync. | RM-1001. | root docs, roadmap, ExecPlan, baseline | Phase 15 **Done** (`RM-990`–`RM-1002`); G1–G8/G10 closed; G9 accepted | governance bundle **159 passed** + `verify_docs`. |

## Phase 16: Blocks 1-5 MVP Core Reliability

Goal: make the first five blocks work as a trustworthy file-first MVP core. A user should be able
to provide `analysis_subject` tickers and weights, materialize diagnostics, stress-test the subject,
generate candidate alternatives, run optimizer-backed candidates, and compare only fresh or clearly
degraded artifacts.

Exit condition: the project has strict enough input validation to prevent misleading starting
weights, comparison does not rely on stale factory evidence, full candidate generation can be
resumed through the portfolio-first orchestrator, optimizer-backed rows disclose readiness
consistently, a five-ticker smoke gate covers the MVP core, and the operator runbook/docs can hand
the work to a new session without chat memory.

Governed by the active
[Blocks 1-5 MVP Core Reliability Plan](exec_plans/2026-05-21_blocks_1_5_mvp_core_reliability_plan.md)
(Sessions 01-09).

| ID | Status | Session | Work item | Prerequisites | Owning docs/code | Artifact or output | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RM-1010 | Done | Session 01 | Create active ExecPlan and registers. | User-approved post-audit plan. | [Blocks 1-5 MVP Core Reliability Plan](exec_plans/2026-05-21_blocks_1_5_mvp_core_reliability_plan.md), ExecPlan register, this roadmap, `KNOWN_ISSUES.md`, `CHANGELOG.md` | Active handoff plan for Sessions 02-09 | `python scripts/verify_docs.py`. |
| RM-1011 | Done | Session 02 | Harden input and weight validation for `analysis_subject`. | RM-1010. | `src/config_schema.py`, `src/analysis_setup.py`, input assumptions spec/tests | Weighted current/model subjects hard-fail on material overallocations; partial weights remain explicit cash-remainder diagnostics | `test_input_assumptions.py` (19 passed); `test_config_weights_sync.py` (6 passed); `verify_docs` OK. |
| RM-1012 | Done | Session 03 | Fix factory/comparison freshness coherence. | RM-1010. | `src/candidate_comparison.py`, candidate factory/comparison specs/tests | `candidate_comparison.json.candidate_menu` reports missing/stale factory evidence and does not treat stale step evidence as authoritative | Candidate factory governance bundle (85 passed); `verify_docs` OK. |
| RM-1013 | Done | Session 04 | Make portfolio-first full factory resumable from `run_portfolio_review.py`. | RM-1012 recommended. | `run_portfolio_review.py`, `src/portfolio_review_workflow.py`, `docs/operational_runbook.md`, workflow tests | `--resume-candidates` passes factory `--resume`; dry-run exposes it | `test_portfolio_review_workflow.py`; dry-run smoke; `verify_docs` OK. |
| RM-1014 | Done | Session 05 | Normalize optimizer readiness disclosure. | RM-1012. | `src/candidate_comparison.py`, `src/optimization_readiness.py`, Block 5 tests/specs | Optimizer-backed rows with missing methodology/quality or `unknown` quality now degrade instead of looking like ordinary available evidence | Readiness, comparison, and golden contract tests; `verify_docs` OK. |
| RM-1015 | Done | Session 06 | Add real five-ticker MVP smoke gate. | RM-1011-RM-1014. | `tests/test_blocks_1_5_mvp_smoke.py`, `tests/mvp_offline_fixtures.py`, `TESTING.md` | Offline executable smoke test for five tickers plus explicit weights through subject diagnostics, Diagnosis, stress, current factory evidence, and comparison baseline | `test_blocks_1_5_mvp_smoke.py` (4 passed); `verify_docs` OK. |
| RM-1016 | Done | Session 07 | Improve data-quality and young-ETF trust signals. | RM-1015 recommended. | `src/data_trust_signals.py`, stress/input/Diagnosis/commentary surfaces, specs/tests | `data_trust_summary` and `data_trust_signals` expose episode quality, taxonomy, and young-ETF policy in user-readable summaries | `test_data_trust_signals.py`, stress historical tests, input/Diagnosis tests; `verify_docs` OK. |
| RM-1017 | Done | Session 08 | Documentation handoff and operator runbook cleanup. | RM-1013-RM-1016. | `README.md`, `SPEC.md`, `OUTPUTS.md`, `TESTING.md`, `docs/operational_runbook.md` | Root docs explain Blocks 1-5 MVP core, core/full/resume paths, trust artifacts, factory-evidence boundaries, and offline acceptance without chat context | `python scripts/verify_docs.py` OK. |
| RM-1018 | Done | Session 09 | Representative run and closure. | RM-1011-RM-1017. | tests, `tests/conftest.py`, roadmap, known issues, changelog, ExecPlan | Phase 16 **Done**; closure verdict: MVP core reliability objectives met under plan scope | Offline bundle **125 passed**; `verify_docs` OK; dry-run core/full resume OK; live core subject materialization OK. |

## Phase 17: Post-Deep-Audit Foundation & Downstream Readiness

Goal: after the second-level Blocks 1–5 audit, close trust gaps that can mislead Blocks 6–10:
live core proof, selection/health eligibility for `degraded` rows and partial menus, optimizer
fair-comparison metadata on disk, ticker preflight, factory/comparison timestamp semantics, review
bundle disclosure, and guarded downstream integration.

Exit condition: operators can run core review with documented live acceptance; decision artifacts
do not favor `degraded` optimizers; full-menu refresh yields multiple fair-ready optimizer rows;
Blocks 6–10 consume comparison under documented eligibility rules; Phase 17 closed in ExecPlan and
roadmap.

Governed by the active
[Post-Deep-Audit Foundation Plan](exec_plans/2026-05-21_post_deep_audit_foundation_plan.md)
(Sessions 01–10). Audit input:
[Blocks 1–5 Deep Audit Snapshot](audits/2026-05-21_blocks_1_5_deep_audit_snapshot.md).

| ID | Status | Session | Work item | Prerequisites | Owning docs/code | Artifact or output | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RM-1020 | Done | Session 01 | ExecPlan, audit snapshot, registers. | Phase 16 closed; deep audit complete. | This ExecPlan, audit snapshot, ExecPlan register, ROADMAP, `KNOWN_ISSUES.md`, `CHANGELOG.md` | Active handoff for Sessions 02–10 | `python scripts/verify_docs.py`. |
| RM-1021 | Done | Session 02 | Live core E2E gate. | RM-1020. | `src/live_core_e2e.py`, `scripts/verify_live_core_e2e.py`, `TESTING.md`, `docs/operational_runbook.md`, live marker test | Documented live core acceptance + validator | `verify_live_core_e2e.py --run` OK; offline smoke 6 passed; `--live-core` pytest 1 passed. |
| RM-1022 | Done | Session 03 | Selection/health partial menu + degraded guards. | RM-1020. | `selection_engine.py`, `portfolio_health_score.py`, specs, tests | No favored `degraded` optimizer; partial menu warnings | selection/health pytest; MVP + portfolio-first E2E. |
| RM-1023 | Done | Session 04 | Optimizer fairness metadata backfill. | RM-1022 recommended. | Optimizer builders, `portfolio_variants.py`, golden fixtures, runbook | ≥3 fair-ready optimizer rows on fresh full run or golden | `test_optimizer_fair_comparison_full_menu.py` (3 passed); Block 5 bundle. |
| RM-1024 | Done | Session 05 | Block 1 ticker/universe preflight. | RM-1020. | `config_schema.py`, `analysis_setup.py`, input spec | Bad ticker fails before report | `test_input_assumptions.py` + MVP smoke **26 passed**. |
| RM-1025 | Done | Session 06 | Factory vs comparison timestamp semantics. | RM-1020. | `candidate_comparison.py`, `run_candidate_factory.py`, `candidate_factory.py`, workflow, tests | Same-run review → `factory_evidence_status: current` when context matches | `test_candidate_comparison.py` (skew + stale); `verify_docs`. |
| RM-1026 | Done | Session 07 | Review bundle disclosure. | RM-1025 recommended. | `review_bundle_context.py`, `candidate_comparison.py`, `input_assumptions.py`, specs, tests | `review_bundle_context` + input trust lines | `test_review_bundle_context.py` + comparison contract; `verify_docs`. |
| RM-1027 | Done | Session 08 | Blocks 6–7 guarded integration. | RM-1022, RM-1026. | `downstream_decision_readiness_spec.md`, `downstream_decision_readiness.py`, health/robustness stress guards, tests | Offline integration test for guarded stress handoff | `test_blocks_6_7_downstream_integration.py` + `verify_docs`. |
| RM-1028 | Done | Session 09 | Blocks 8–10 package truthfulness. | RM-1022, RM-1027. | `package_truthfulness.py`, `decision_package_reporting.py`, `action_engine.py`, tests | Package cannot imply full-menu optimizer winner after core-only | `test_blocks_8_10_downstream_integration.py` + package truthfulness bundle; `verify_docs`. |
| RM-1029 | Done | Session 10 | Live full resume + Phase 17 closure. | RM-1021–RM-1028. | `live_full_e2e.py`, `verify_live_full_e2e.py`, ExecPlan, ROADMAP, CHANGELOG, KNOWN_ISSUES | Phase 17 **Done** | `verify_live_full_e2e.py --run` OK; resume `resumed_from_manifest=16`; closure **72 passed**; `verify_docs` OK. |

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
(`RM-940` through `RM-950`) is **closed** as of 2026-05-20. Phase 13 (`RM-951` through `RM-961`) is
**closed** as of 2026-05-20 (Sessions 00-11 complete). Phase 14 (`RM-970` through `RM-981`) is
**closed** as of 2026-05-20 (Session 11 complete). Phase 15 (`RM-990` through `RM-1002`) is
**closed** as of 2026-05-21 (Session 12 complete). Phase 16 (`RM-1010` through `RM-1018`) is
**closed** as of 2026-05-21 (Session 09 complete). Phase 17 (`RM-1020` through `RM-1029`) is
**closed** as of 2026-05-22 (Session 10 complete) — see
[Post-Deep-Audit Foundation Plan](exec_plans/2026-05-21_post_deep_audit_foundation_plan.md).
Keep each future project-level session in a separate chat unless the user explicitly changes that
rule. Do not reopen closed MVP, post-audit, portfolio-first, Phase 9, Phase 11, Phase 12, Phase 16,
or Phase 17 sessions unless the user explicitly requests plan amendments.

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
