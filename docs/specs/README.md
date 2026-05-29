# Detailed Specifications

This directory contains the detailed source-of-truth documents for module-specific behavior.

These specs describe current implementation contracts. Product-facing Portfolio MRI language in `PRODUCT.md` or `ARCHITECTURE.md` may map these contracts into target UX concepts, but it does not rename schemas, output files, formulas, fields, statuses, or generated artifact contracts.

Output category boundary: the product-facing diagnosis-first bundle is
`problem_classification.json`, `candidate_launchpad.json`, `current_vs_candidate.json`,
`decision_verdict.json`, `ai_commentary_context.json`, and `what_changed_summary.json`.
`candidate_comparison.json`, `selection_decision.json`, factory manifests, and `output_manifest.json`
remain technical contracts. Health, robustness, assumption sensitivity, Pareto/dominance, regret,
trade-off, and model-risk artifacts are advanced/research evidence unless a later approved spec
promotes a specific surface. See [../../OUTPUTS.md](../../OUTPUTS.md) and
[reporting_outputs_spec.md](reporting_outputs_spec.md) for the full output bundle policy.

Top-level documents stay compact:

- [../../RULES.md](../../RULES.md) maps project principles and source-of-truth ownership.
- [../../AGENTS.md](../../AGENTS.md) defines agent operating rules.
- [../../WORKFLOW.md](../../WORKFLOW.md) defines the task workflow from request to implementation, verification, documentation sync, project memory, and commit.
- [../../SPEC.md](../../SPEC.md) defines the current implementation contract and indexes these detailed specs.
- [../../OUTPUTS.md](../../OUTPUTS.md) maps generated output folders, artifacts, formats, report packaging, and generated-vs-source boundaries.
- [../../GLOSSARY.md](../../GLOSSARY.md) defines shared project terminology and short definitions.
- [../../DATA.md](../../DATA.md) maps data sources, structures, pipeline, quality rules, and data documentation sync triggers.
- [../../TESTING.md](../../TESTING.md) defines the quality and verification framework.
- [../../KNOWN_ISSUES.md](../../KNOWN_ISSUES.md) tracks active known issues, model limitations, testing gaps, and technical debt.
- [../../DECISIONS.md](../../DECISIONS.md) records key project decisions, rationale, rejected alternatives, assumptions, and consequences.
- [../../CHANGELOG.md](../../CHANGELOG.md) records concise history of meaningful project changes.

## Spec Index

| Area | Spec |
| --- | --- |
| Portfolio-first review workflow, `analysis_subject` baseline, and `run_portfolio_review.py` orchestration | [portfolio_review_workflow_spec.md](portfolio_review_workflow_spec.md) |
| Diagnosis-first workflow state classification (`diagnosis_only`, `one_candidate`, `multiple_candidates`) | [workflow_state_spec.md](workflow_state_spec.md) |
| Problem Classification diagnostic artifact and evidence-to-problem mapping | [problem_classification_spec.md](problem_classification_spec.md) |
| Candidate Launchpad data artifact and problem-to-hypothesis card mapping | [candidate_launchpad_spec.md](candidate_launchpad_spec.md) |
| Portfolio Alternatives Builder one-candidate wrapper over existing candidate builders | [portfolio_alternatives_builder_spec.md](portfolio_alternatives_builder_spec.md) |
| Portfolio X-Ray diagnostics, seven-section current-portfolio diagnostic layer, and `portfolio_xray.json` contract | [portfolio_xray_diagnostics_spec.md](portfolio_xray_diagnostics_spec.md) |
| Block 2.4 Hidden Exposure UI Pareto cards (presentation layer over `block_2_4_hidden_exposure`) | [block_2_4_hidden_exposure_ui_pareto_spec.md](block_2_4_hidden_exposure_ui_pareto_spec.md) |
| Block 2.6 Portfolio Weakness Map UI Pareto cards (presentation layer over `block_2_6_portfolio_weakness_map`) | [block_2_6_weakness_map_ui_pareto_spec.md](block_2_6_weakness_map_ui_pareto_spec.md) |
| Portfolio X-Ray layer (Block 2.1-2.7) | [portfolio_xray_layer_spec.md](portfolio_xray_layer_spec.md) |
| Portfolio X-Ray methodology map (Block 2 audit baseline) | [../audits/2026-05-20_portfolio_xray_methodology_map.md](../audits/2026-05-20_portfolio_xray_methodology_map.md) |
| Metrics, estimators, windows, returns, FX, beta, drawdown, RC_vol, rounding | [metrics_specification.md](metrics_specification.md) |
| Analysis setup, input modes, current weights, mandate inputs, and calculation assumptions | [input_assumptions_spec.md](input_assumptions_spec.md) |
| Portfolio construction and main optimizer policy | [portfolio_construction_policy.md](portfolio_construction_policy.md) |
| Feasibility and weight constraints | [feasibility_constraints_spec.md](feasibility_constraints_spec.md) |
| Task workflow from request to implementation, verification, docs sync, project memory, and commit | [../../WORKFLOW.md](../../WORKFLOW.md) |
| Generated output folders, artifacts, formats, and generated-vs-source boundaries | [../../OUTPUTS.md](../../OUTPUTS.md) |
| Shared project terminology and short definitions | [../../GLOSSARY.md](../../GLOSSARY.md) |
| Data-layer map, sources, structures, pipeline, quality rules | [../../DATA.md](../../DATA.md) |
| Testing and verification framework | [../../TESTING.md](../../TESTING.md) |
| Known active issues, model limitations, testing gaps, and technical debt | [../../KNOWN_ISSUES.md](../../KNOWN_ISSUES.md) |
| Key project decisions and rationale | [../../DECISIONS.md](../../DECISIONS.md) |
| Concise history of meaningful project changes | [../../CHANGELOG.md](../../CHANGELOG.md) |
| Detailed data policy, NaN handling, young ETFs, return panels | [data_policy_spec.md](data_policy_spec.md) |
| Stress scenarios and stress diagnostics | [stress_testing_spec.md](stress_testing_spec.md) |
| Core MVP historical stress replay (direct history only; Stress Lab) | [core_mvp_historical_stress_replay_spec.md](core_mvp_historical_stress_replay_spec.md) |
| Deferred stress scenario proposals (governance) | [../proposals/README.md](../proposals/README.md) |
| Stress Lab layer (Block 3.1-3.6), provenance map, and handoff index | [stress_lab_layer_spec.md](stress_lab_layer_spec.md) |
| Stress Lab methodology map (Block 3 audit baseline) | [../audits/2026-05-20_stress_lab_methodology_map.md](../audits/2026-05-20_stress_lab_methodology_map.md) |
| Factor diagnostics and factor-risk outputs | [factor_diagnostics_spec.md](factor_diagnostics_spec.md) |
| Macro regime diagnostics | [macro_regime_spec.md](macro_regime_spec.md) |
| Scenario Library and normalized scenario view | [scenario_library_spec.md](scenario_library_spec.md) |
| Hedge gap analysis contract | [hedge_gap_analysis_spec.md](hedge_gap_analysis_spec.md) |
| Current Portfolio Stress Scorecard (Block 3.4) | [current_portfolio_stress_scorecard_spec.md](current_portfolio_stress_scorecard_spec.md) |
| Crisis replay path contract | [crisis_replay_spec.md](crisis_replay_spec.md) |
| Candidate and benchmark portfolios | [candidate_portfolios_spec.md](candidate_portfolios_spec.md) |
| Candidate portfolio factory orchestration | [candidate_factory_spec.md](candidate_factory_spec.md) |
| Candidate Factory layer mapping (Block 4.1–4.9) | [candidate_factory_layer_spec.md](candidate_factory_layer_spec.md) |
| Optimization Engine methodology map (Block 5 audit baseline) | [../audits/2026-05-20_optimization_engine_methodology_map.md](../audits/2026-05-20_optimization_engine_methodology_map.md) |
| Optimization Engine layer (Block 5.1-5.11), roles, objective/estimator/constraint/status/output matrices | [optimization_engine_layer_spec.md](optimization_engine_layer_spec.md) |
| Optimization Engine post-audit roadmap (Phase 15) | [../exec_plans/2026-05-20_optimization_engine_post_audit_roadmap.md](../exec_plans/2026-05-20_optimization_engine_post_audit_roadmap.md) |
| Canonical multi-candidate comparison artifact | [candidate_comparison_spec.md](candidate_comparison_spec.md) |
| Current-vs-candidate product comparison adapter | [current_vs_candidate_spec.md](current_vs_candidate_spec.md) |
| Downstream decision readiness (Blocks 6–7 handoff, eligibility guards) | [downstream_decision_readiness_spec.md](downstream_decision_readiness_spec.md) |
| Robustness Scorecard (diagnostic resilience scoring) | [robustness_scorecard_spec.md](robustness_scorecard_spec.md) |
| Portfolio Health Score (diagnostic holistic quality scoring) | [portfolio_health_score_spec.md](portfolio_health_score_spec.md) |
| Selection Engine and No-Trade Recommendation (formal decision contract) | [selection_engine_spec.md](selection_engine_spec.md) |
| Product-facing Decision Verdict mapping over Selection/No-Trade evidence | [decision_verdict_spec.md](decision_verdict_spec.md) |
| AI Commentary grounding context (current contract; not LLM prose) | [ai_commentary_grounding_spec.md](ai_commentary_grounding_spec.md) |
| Trade-off Explanation and Model Risk Diagnostics | [tradeoff_and_model_risk_spec.md](tradeoff_and_model_risk_spec.md) |
| Assumption Sensitivity (selection stability under perturbations) | [assumption_sensitivity_spec.md](assumption_sensitivity_spec.md) |
| Pareto / Dominance Check (multi-criteria candidate pruning) | [pareto_dominance_spec.md](pareto_dominance_spec.md) |
| Regret Analysis (scenario opportunity loss vs best available) | [regret_analysis_spec.md](regret_analysis_spec.md) |
| Current-vs-policy workflow and No-Trade actionability | [current_vs_policy_workflow_spec.md](current_vs_policy_workflow_spec.md) |
| Action Engine and Rebalancing Advisor (implementation plan) | [action_engine_spec.md](action_engine_spec.md) |
| Monitoring snapshots and What Changed diff | [monitoring_spec.md](monitoring_spec.md) |
| Light Monitoring / What Changed product summary | [light_monitoring_summary_spec.md](light_monitoring_summary_spec.md) |
| Decision Journal (generated decision record) | [decision_journal_spec.md](decision_journal_spec.md) |
| Robust Mean-Variance baselines and lambda calibration | [robust_mv_spec.md](robust_mv_spec.md) |
| Scenario-Based Robust Optimization | [robust_scenario_optimization_spec.md](robust_scenario_optimization_spec.md) |
| Reporting outputs and artifacts | [reporting_outputs_spec.md](reporting_outputs_spec.md) |
| Decision package report/PDF summary | [decision_package_reporting_spec.md](decision_package_reporting_spec.md) |
| ETF and stock taxonomy | [taxonomy_spec.md](taxonomy_spec.md) |
| Asset taxonomy onboarding (new tickers, stress blocks, report CLI) | [asset_taxonomy_onboarding_spec.md](asset_taxonomy_onboarding_spec.md) |
| US universe ingestion (public listings → draft taxonomy) | [universe_ingestion_spec.md](universe_ingestion_spec.md) |
| ETF taxonomy schema | [etf_universe_spec.md](etf_universe_spec.md) |
| Stock taxonomy schema | [stock_universe_spec.md](stock_universe_spec.md) |
| View After Optimization | [view_after_optimization_spec.md](view_after_optimization_spec.md) |
| Production workflow and release statuses | [production_workflow.md](production_workflow.md) |

When detailed behavior changes, update the owning spec here and keep top-level documents as indexes rather than copying long formulas or module contracts into them.
