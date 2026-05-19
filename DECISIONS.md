# DECISIONS.md

This file is the concise living decision log for Portfolio X-Ray & Optimization Terminal / Portfolio MRI.

It records important decisions, why they were made, what alternatives were rejected, and which assumptions existed at the time. It is not a changelog, roadmap, issue tracker, implementation spec, or ExecPlan.

Accepted project-level decisions are listed below. Add entries here only when a real decision is made.

## Purpose

- Preserve the reasoning behind important project choices.
- Prevent the same architectural, product, or methodology questions from being reopened without context.
- Make assumptions visible when a decision is made.
- Keep rationale separate from implementation details and change history.

## What Belongs Here

- Architecture decisions that affect module boundaries, workflows, interfaces, or source-of-truth ownership.
- Product boundary decisions, such as diagnostic-only vs production policy behavior.
- Financial methodology decisions, such as optimizer policy, stress governance, data assumptions, metrics behavior, or model-risk boundaries.
- Testing and quality decisions that affect verification strategy.
- Documentation governance decisions that affect how project knowledge is organized.

## What Does Not Belong Here

- Every code change; use [CHANGELOG.md](CHANGELOG.md) for concise completed-change history.
- Active bugs, weak spots, or technical debt; use [KNOWN_ISSUES.md](KNOWN_ISSUES.md).
- Long formulas or module contracts; use `SPEC.md`, `DATA.md`, and `docs/specs/*.md`.
- Step-by-step implementation plans; use [PLANS.md](PLANS.md) and `docs/exec_plans/`.
- Future product ideas without a decision; use `PRODUCT.md`, `BUSINESS_VISION.md`, or `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`.

## When To Add Or Update

- Add an entry when the project chooses one path among meaningful alternatives.
- Add an entry when a decision affects behavior, source-of-truth structure, methodology, API/UI boundaries, data policy, testing policy, or reporting contracts.
- Update an entry when the decision is superseded, narrowed, expanded, or its assumptions are no longer true.
- Do not rewrite history silently; mark old decisions as `superseded` and link the newer decision.
- If a decision changes current behavior, update the owning spec and add a short entry to [CHANGELOG.md](CHANGELOG.md).
- If a decision exposes an unresolved risk or debt item, add it to [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

## Entry Format

Keep entries short. Use this format:

```markdown
Decision ID: DEC-YYYY-MM-DD-NNN
Title: Short title

- Status: proposed | accepted | superseded
- Date: YYYY-MM-DD
- Decision: What was decided.
- Context: What problem or trade-off triggered the decision.
- Rationale: Why this option was chosen.
- Alternatives considered: What was rejected and why.
- Assumptions: What was believed to be true at the time.
- Consequences: What changes or constraints follow from the decision.
- Related documents: Links to specs, plans, code, tests, or docs.
- Review trigger: When this decision should be revisited.
```

## Decisions

Decision ID: DEC-2026-05-18-001
Title: Portfolio-first workflow and legacy policy engine boundary

- Status: accepted
- Date: 2026-05-18
- Decision: The main product workflow must start from `analysis_subject` diagnostics. Generated policy optimization must not be presented before `analysis_subject` is diagnosed and must not be a default candidate in the portfolio-first workflow. The old policy engine remains available as legacy, archived, or experimental infrastructure until a future canonical spec explicitly reactivates it.
- Context: The user identified that the project contract drifted toward a policy-first mental model: `run_optimization.py` generated policy weights first, then reports and comparisons treated that policy portfolio as the main starting point. This conflicts with the product vision that a user's current, model, or universe-baseline portfolio should be diagnosed first.
- Rationale: A portfolio review product must answer whether to keep, improve, rebalance, or rethink the portfolio the user started with. Showing optimized results before diagnosing that portfolio reverses the product logic and misleads agents and users.
- Alternatives considered: Keep policy as the default candidate; keep policy as the default starting portfolio but change wording; delete the old policy engine. These were rejected because they either preserve the source-of-truth conflict or discard potentially useful infrastructure.
- Assumptions: The transition remains file-first; UI work is not part of this decision; reintroducing policy as a candidate requires a future spec and explicit approval.
- Consequences: New specs, workflow orchestration, comparison, decision artifacts, reports, and docs must center on `analysis_subject`. `run_optimization.py` remains callable but is not part of the default portfolio-first path.
- Related documents: [Portfolio Review Workflow Specification](docs/specs/portfolio_review_workflow_spec.md), [Portfolio-First Transition Plan](docs/exec_plans/2026-05-18_portfolio_first_transition_plan.md), [docs/ROADMAP.md](docs/ROADMAP.md), [KNOWN_ISSUES.md](KNOWN_ISSUES.md), [PRODUCT.md](PRODUCT.md).
- Review trigger: Revisit only if a future accepted spec proposes reintroducing the policy engine as an optional candidate generator or production policy path.

Decision ID: DEC-2026-05-19-001
Title: Portfolio-first policy artifacts are compatibility-only

- Status: accepted
- Date: 2026-05-19
- Decision: When `analysis_subject` diagnostics are available, root `policy` artifacts remain readable for legacy compatibility but are not ranked or selected as normal portfolio-first candidate evidence. `current_vs_policy_status.json` may still be written, but it uses `workflow_profile: portfolio_first_review` and is hidden from the main decision-package summary story.
- Context: The post-portfolio-first audit found that policy rows, current-vs-policy status, and Health Score priority still made old policy optimizer artifacts look like the primary workflow in fresh portfolio-first outputs.
- Rationale: Keeping the artifacts avoids breaking legacy consumers, while gating and labeling them prevents users from treating generated policy output as the starting portfolio or default recommendation.
- Alternatives considered: Delete policy artifacts from comparison; leave them fully available with wording only. Deletion was too disruptive for compatibility, while wording-only cleanup would still let Selection and Health Score rank stale policy evidence.
- Assumptions: Reintroducing policy as an explicit portfolio-first candidate requires a future canonical spec.
- Consequences: Candidate Comparison gates `policy` as legacy-only when `analysis_subject` exists, Health Score priority starts with `analysis_subject`, and current-vs-policy status is compatibility metadata in portfolio-first runs.
- Related documents: [Portfolio Review Workflow Specification](docs/specs/portfolio_review_workflow_spec.md), [candidate comparison spec](docs/specs/candidate_comparison_spec.md), [current-vs-policy workflow spec](docs/specs/current_vs_policy_workflow_spec.md), [portfolio health score spec](docs/specs/portfolio_health_score_spec.md).
- Review trigger: Revisit if a future accepted spec adds an explicit opt-in policy-as-candidate mode for portfolio-first reviews.

Decision ID: DEC-2026-05-18-002
Title: Analysis subject is the decision baseline

- Status: accepted
- Date: 2026-05-18
- Decision: When `analysis_subject` diagnostics are materialized, candidate comparison and downstream decision artifacts use `analysis_subject` as the baseline. The legacy `current` baseline remains a fallback for current-vs-policy compatibility only.
- Context: Earlier Selection V1 behavior favored `policy` by default and evaluated No-Trade versus `current`. That was correct for the old current-vs-policy workflow but contradicted the portfolio-first transition once `analysis_subject` became the diagnosed starting portfolio.
- Rationale: Selection, No-Trade, Action, Monitoring, and Journal must answer whether to keep, improve, rebalance, or rethink the starting portfolio, not whether to move from current to generated policy.
- Alternatives considered: Keep policy as default even when `analysis_subject` exists; duplicate a separate subject-only decision artifact. These were rejected because they preserve old policy-first interpretation or split one decision workflow into parallel contracts.
- Assumptions: `current_vs_policy_status.json` remains compatibility-only; the policy engine is not deleted; report language cleanup continues in later transition sessions.
- Consequences: `candidate_comparison.json` includes `analysis_subject`; `selection_decision.json`, `action_plan.json`, monitoring snapshots, and `decision_journal.json` expose baseline fields and prefer `analysis_subject`.
- Related documents: [Portfolio Review Workflow Specification](docs/specs/portfolio_review_workflow_spec.md), [candidate comparison spec](docs/specs/candidate_comparison_spec.md), [selection engine spec](docs/specs/selection_engine_spec.md), [action engine spec](docs/specs/action_engine_spec.md), [monitoring spec](docs/specs/monitoring_spec.md), [decision journal spec](docs/specs/decision_journal_spec.md).
- Review trigger: Revisit if a future spec creates a multi-baseline comparison workflow or reintroduces policy as an explicit portfolio-first candidate.

Decision ID: DEC-2026-05-17-005
Title: Post-session next stage and optimizer-role boundary

- Status: accepted
- Date: 2026-05-17
- Decision: After Sessions 01-20, the next project stage is stabilization and integration of the new decision pipeline before major new analytics or UI. Main optimization remains the production policy path; robust MV and robust scenario optimization remain comparison/candidate paths unless a future accepted spec changes that boundary.
- Context: The post-session audit found that candidate comparison, robustness, health, selection, action, monitoring, and journal artifacts are implemented, while top-level docs, reporting surfaces, source text quality, and current-vs-policy workflow still need cleanup. It also reviewed Main optimizer inputs/objective/gates against robust optimizer paths and the product concept.
- Rationale: The project now has the V1 decision artifacts, but the user-facing and source-of-truth layers are not yet stable enough to safely build larger UI or advanced analytics on top. Keeping Main and robust optimizer roles explicit prevents silent changes to production policy behavior.
- Alternatives considered: Start UI work immediately; replace Main with robust optimization; add assumption sensitivity/Pareto/regret before syncing docs and reports. These were rejected as higher-risk sequencing because they would build on stale docs and incomplete user-facing surfaces.
- Assumptions: Sessions 01-20 remain the accepted V1 artifact baseline; generated outputs are not source of truth; any optimizer role change requires a new owning spec.
- Consequences: Near-term roadmap work should prioritize docs/status sync, decision-log integrity, report/PDF decision-package integration, mojibake cleanup, current-vs-policy workflow, and candidate factory orchestration before Sessions 21-22 or new analytics.
- Related documents: [post-session audit](docs/audits/2026-05-17_post_session_deep_system_audit.md), [docs/ROADMAP.md](docs/ROADMAP.md), [docs/specs/portfolio_construction_policy.md](docs/specs/portfolio_construction_policy.md), [docs/specs/robust_mv_spec.md](docs/specs/robust_mv_spec.md), [docs/specs/robust_scenario_optimization_spec.md](docs/specs/robust_scenario_optimization_spec.md).
- Review trigger: Revisit if robust optimization is proposed as the production policy optimizer, if a candidate factory becomes authoritative, or before implementing the first full product UI.

Decision ID: DEC-2026-05-17-002
Title: V1 candidate comparison contract (full registry, current row, Main output)

- Status: accepted
- Date: 2026-05-17
- Decision: The canonical comparison artifact is `candidate_comparison.json` under `output_dir_final` (default `Main portfolio/`). V1 lists the full candidate registry with `unavailable` when artifact folders are missing, and includes a `current` candidate when user-current portfolio artifacts exist (`analyze_current_weights` or `user_current_portfolio` tagging).
- Context: Legacy `portfolio_comparison.json` and `ew_rp_comparison.json` cover partial subsets with inconsistent schemas; audit AUD-010 requires one contract before scores and selection.
- Rationale: A single diagnostic-only table supports current vs policy vs benchmarks without implying a recommendation; Main placement keeps the comparison next to primary run outputs.
- Alternatives considered: Minimal four-candidate launch only; defer `current` to a later session; place the file in a root `comparison/` folder.
- Assumptions: Session 09 implements a read-only builder that does not recompute metrics; legacy comparison files remain until migration.
- Consequences: Robustness Scorecard, Health Score, and Selection Engine must consume `candidate_comparison.json` per [candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md).
- Related documents: [docs/specs/candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md), [OUTPUTS.md](OUTPUTS.md), [docs/ROADMAP.md](docs/ROADMAP.md).
- Review trigger: Revisit when comparison UI, cross-run history, or a dedicated comparison workspace is introduced.

Decision ID: DEC-2026-05-17-004
Title: Portfolio Health Score V1 scoring model

- Status: accepted
- Date: 2026-05-17
- Decision: The Portfolio Health Score uses ten reviewable components under profile `default_weights_reviewable`, within-run percentile normalization plus absolute mandate/liquidity checks, primary window 10y, optional `resilience_reference` (10%) from `robustness_scorecard.json` only, and weight concentration from a comparison `weight_concentration` block (not RC proxies). Output is diagnostic-only for all scored candidates; report surfaces prioritize `current` and `policy`.
- Context: Session 12 specifies holistic quality scoring after canonical comparison and robustness scorecard; product concept section 11 defines investor-facing health components distinct from resilience ranking.
- Rationale: Health answers balance, fit, and implementability; Robustness answers crisis resilience; ingesting robustness total avoids duplicating six robustness formulas while keeping a separate narrative.
- Alternatives considered: Health Score only for current/policy; full duplication of robustness stress/downside components; no cross-reference to robustness scorecard.
- Assumptions: Session 13 implements the health score module and comparison v1.2 `weight_concentration` together.
- Consequences: See [portfolio_health_score_spec.md](docs/specs/portfolio_health_score_spec.md).
- Related documents: [docs/specs/portfolio_health_score_spec.md](docs/specs/portfolio_health_score_spec.md), [docs/specs/robustness_scorecard_spec.md](docs/specs/robustness_scorecard_spec.md), [docs/specs/candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md), [docs/ROADMAP.md](docs/ROADMAP.md).
- Review trigger: Revisit after empirical validation of weights or when Selection Engine consumes health outputs.

Decision ID: DEC-2026-05-17-003
Title: Robustness Scorecard V1 scoring model

- Status: accepted
- Date: 2026-05-17
- Decision: The Robustness Scorecard uses relative within-run normalization for component sub-scores, product-concept weights under profile `default_weights_reviewable`, primary window 10y, RC-based diversification from a comparison `diversification` block (no vol/beta proxies), and absolute mandate checks only inside `mandate_fit`. Output is diagnostic-only until Selection Engine exists.
- Context: Session 10 specifies the scorecard after canonical `candidate_comparison.json`; the product concept defines six components and example weights.
- Rationale: Relative scoring answers "who is more resilient among these alternatives"; mandate limits stay explicit; RC concentration matches the project's RC_vol diagnostics.
- Alternatives considered: Absolute scoring against fixed thresholds for all components; temporary diversification proxies without RC in comparison.
- Assumptions: Session 11 implements the scorecard module and comparison v1.1 diversification fields together.
- Consequences: See [robustness_scorecard_spec.md](docs/specs/robustness_scorecard_spec.md); `src/robustness.py` remains optimizer weight stability only.
- Related documents: [docs/specs/robustness_scorecard_spec.md](docs/specs/robustness_scorecard_spec.md), [docs/specs/candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md), [docs/ROADMAP.md](docs/ROADMAP.md).
- Review trigger: Revisit after empirical validation of weights or when Selection Engine consumes score outputs.

Decision ID: DEC-2026-05-17-001
Title: Use docs/ROADMAP.md as the durable development roadmap

- Status: accepted
- Date: 2026-05-17
- Decision: The ordered product-development roadmap lives at `docs/ROADMAP.md`; it is a planning document and does not override canonical specs or current implementation contracts.
- Context: The 2026-05-17 audit found that the project had product concepts, implementation specs, and many analytical modules, but no single execution spine connecting concept layers to ordered development sessions.
- Rationale: `docs/ROADMAP.md` is clearer than `docs/product_backlog.md` for a durable cross-phase plan and matches the audit's first recommended filename.
- Alternatives considered: Use `docs/product_backlog.md`, which is also reasonable but narrower; keep only the ExecPlan, which would make the plan less discoverable from root documentation.
- Assumptions: Future major work continues to use checked-in ExecPlans when changes are large or risky; roadmap items remain non-binding until promoted into owning specs and code.
- Consequences: Future product modules should map to roadmap IDs, source-of-truth specs, artifacts, and verification before implementation. Current behavior remains governed by `SPEC.md` and detailed specs.
- Related documents: [docs/ROADMAP.md](docs/ROADMAP.md), [docs/exec_plans/2026-05-17_project_development_session_plan.md](docs/exec_plans/2026-05-17_project_development_session_plan.md), [docs/audits/2026-05-17_full_project_system_audit.md](docs/audits/2026-05-17_full_project_system_audit.md).
- Review trigger: Revisit if roadmap ownership moves, a separate backlog is introduced, or product planning becomes managed outside the repository.

Decision ID: DEC-2026-05-15-001
Title: Separate current weights from generated policy weights

- Status: accepted
- Date: 2026-05-15
- Decision: The Input and Assumptions Layer supports `analysis_mode=optimize_from_universe` for the default policy workflow and `analysis_mode=analyze_current_weights` for fixed current-portfolio diagnostics using `current_weights`.
- Context: The product concept allows existing-portfolio analysis with current weights, while the current policy rule says final production weights are generated by optimization.
- Rationale: Separating current diagnostic weights from generated policy weights lets users analyze existing portfolios without weakening the rule that policy weights come from the optimizer or approved post-optimization protocols.
- Alternatives considered: Continue using only `weights` for both cases, which keeps ambiguity; allow manual policy weights, which weakens production semantics.
- Assumptions: The first product layer remains CLI/file-driven and report-first; full UI, formal selection, and no-trade logic are still TBD.
- Consequences: `run_optimization.py` rejects `analyze_current_weights`; `run_report.py` can diagnose fixed current weights; artifacts expose an `input_assumptions` summary.
- Related documents: [docs/specs/input_assumptions_spec.md](docs/specs/input_assumptions_spec.md), [docs/exec_plans/2026-05-15_input_assumptions_layer_v1.md](docs/exec_plans/2026-05-15_input_assumptions_layer_v1.md), [docs/specs/portfolio_construction_policy.md](docs/specs/portfolio_construction_policy.md).
- Review trigger: Revisit when the project adds a UI input workflow, formal Selection Engine, or compare-current-to-policy workflow.

Decision ID: DEC-2026-05-15-002
Title: Make analysis_setup the input-layer runtime contract

- Status: accepted
- Date: 2026-05-15
- Decision: `analysis_setup` is the single resolved runtime contract for portfolio input, analysis portfolio, mandate, assumptions, and validation; `input_assumptions` is a report/export projection from it.
- Context: The product needs a clear analysis contract before diagnostics, stress testing, optimization, comparison, recommendation, or reporting, without adding UI or selection-engine scope.
- Rationale: A single resolved contract prevents `input_assumptions`, generated weights, current weights, and future UI inputs from becoming competing sources of truth.
- Alternatives considered: Keep only `input_assumptions` as the runtime summary, which blurs reporting metadata with business logic; immediately change universe-only report behavior, which would exceed the compatibility scope.
- Assumptions: Backward compatibility takes priority; target MVP conflicts are documented before behavior changes.
- Consequences: Run artifacts expose `analysis_setup`; `input_assumptions` is projected from it; Equal Weight Initial Portfolio is labeled as a baseline, not a recommendation.
- Related documents: [docs/specs/input_assumptions_spec.md](docs/specs/input_assumptions_spec.md), [OUTPUTS.md](OUTPUTS.md), [docs/specs/reporting_outputs_spec.md](docs/specs/reporting_outputs_spec.md).
- Review trigger: Revisit when SPEC authorizes taxonomy hard rejection in current repo mode or equal-weight universe-only diagnostics as executable report behavior.

Decision ID: DEC-2026-05-17-006
Title: Selection Engine V1 contract — composite score, policy default, No-Trade materiality

- Status: accepted
- Date: 2026-05-17
- Decision: Session 14 adopts [selection_engine_spec.md](docs/specs/selection_engine_spec.md) with neutral decision-support tone; favored target defaults to `policy` when mandate-clean; No-Trade compares `current` to favored target using reviewable health/robustness deltas, half-sum turnover, and optional drawdown improvement; Pareto/regret/assumption sensitivity remain out of V1; diagnostic scorecards stay non-binding inputs.
- Context: Comparison and diagnostic scores (Sessions 08–13) exist; the product needs a formal non-executing decision artifact before Action Engine and Decision Journal.
- Rationale: Separates evidence (comparison, health, robustness) from a single machine-readable decision status; No-Trade prevents implying trades when benefit is immaterial relative to turnover.
- Alternatives considered: Auto-select top health rank only (rejected — ignores policy role and robustness); merge Selection into Health Score (rejected — blurs diagnostic vs decision); include Pareto pruning in V1 (deferred — no owning spec).
- Assumptions: Session 15 will implement `selection_decision.json` without changing optimizer release or stress pass/fail.
- Consequences: `selection_decision_v1` is the target artifact; `src/selection_engine.py` and tests follow in Session 15; PDF/report surfaces reference decision rules when integrated.
- Related documents: [docs/specs/selection_engine_spec.md](docs/specs/selection_engine_spec.md), [docs/specs/candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md), [docs/specs/portfolio_health_score_spec.md](docs/specs/portfolio_health_score_spec.md), [docs/specs/robustness_scorecard_spec.md](docs/specs/robustness_scorecard_spec.md), [docs/ROADMAP.md](docs/ROADMAP.md) RM-300.
- Review trigger: Revisit when Pareto/dominance or regret modules are specified, or when transaction-cost-aware No-Trade is added in Action Engine.

Decision ID: DEC-2026-05-17-009
Title: Assumption Sensitivity V1 — selection-stability grid without optimizer re-run

- Status: accepted
- Date: 2026-05-17
- Decision: Adopt [assumption_sensitivity_spec.md](docs/specs/assumption_sensitivity_spec.md) with Tier A variants (composite weight stress, health/robust-only proxies, policy-default-off) and Tier B evidence variants (Sharpe rank by 3y/5y/10y, stress worst-loss rank). Stability is measured as `favored_stable_rate` on Tier A only; artifact is diagnostic-only and does not change `selection_decision.json`. Explicit V1 exclusions: optimizer re-run, expected-return shocks, covariance re-score, transaction-cost grids.
- Context: Post-audit Session 14 (RM-620 spec phase); product concept section 14 and audit PSA-012; Selection V1 defers sensitivity from binding logic.
- Rationale: Answers whether the favored profile is fragile to reviewable score-weight and policy-role assumptions using existing health/robustness totals; avoids expensive or formula-duplicating perturbations in V1.
- Alternatives considered: Full assumption grid with re-optimization (deferred — out of scope and high model risk); merge into model-risk artifact (rejected — different question); auto-downgrade selection when fragile (rejected — violates diagnostic boundary).
- Assumptions: Session 15 implements the assumption sensitivity builder, wires after trade-off in `write_candidate_comparison_outputs`, and extends decision-package reporting.
- Consequences: `assumption_sensitivity_v1` contract; journal/report may cite stability; Pareto/regret remain separate sessions.
- Related documents: [docs/specs/assumption_sensitivity_spec.md](docs/specs/assumption_sensitivity_spec.md), [docs/specs/selection_engine_spec.md](docs/specs/selection_engine_spec.md), [OUTPUTS.md](OUTPUTS.md), [docs/ROADMAP.md](docs/ROADMAP.md) RM-620.
- Review trigger: Revisit when Health/Robustness can be re-scored on alternate windows without full pipeline re-run, or when No-Trade threshold stress is added.

Decision ID: DEC-2026-05-17-010
Title: Pareto / Dominance Check V1 — strict metric-only dominance diagnostic

- Status: accepted
- Date: 2026-05-17
- Decision: Adopt [pareto_dominance_spec.md](docs/specs/pareto_dominance_spec.md) with strict Pareto dominance on primary-window `cagr`, `vol_annual`, `max_drawdown`, and `stress_worst_loss`, optional `es_95` and `turnover_vs_current_half_sum_pct` when present. Artifact is diagnostic-only, does not change `selection_decision.json`, and runs after assumption sensitivity in the comparison pipeline.
- Context: Post-audit Session 16 (RM-621 spec phase); product concept section 15 and audit PSA-012; Selection V1 defers dominance from binding logic.
- Rationale: Surfaces clearly weaker candidates using existing comparison exports without duplicating metric formulas or auto-pruning Selection output.
- Alternatives considered: Mandate-aware dominance (rejected for V1 — blurs binding gates with metric evidence); auto-remove dominated candidates from Selection (rejected — violates diagnostic boundary); Sharpe-only dominance (rejected — overlaps Assumption Sensitivity Tier B).
- Assumptions: Session 17 implements the Pareto/Dominance builder, wires into `write_candidate_comparison_outputs`, and extends decision-package reporting.
- Consequences: `pareto_dominance_v1` contract; journal/report may cite efficient set and `favored_is_dominated`; Regret Analysis spec in Session 18, implementation Session 19.
- Related documents: [docs/specs/pareto_dominance_spec.md](docs/specs/pareto_dominance_spec.md), [docs/specs/candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md), [OUTPUTS.md](OUTPUTS.md), [docs/ROADMAP.md](docs/ROADMAP.md) RM-621.
- Review trigger: Revisit when multi-window Pareto surfaces or mandate-aware dominance are product-required.

Decision ID: DEC-2026-05-17-011
Title: Regret Analysis V1 — stress-scenario opportunity-loss diagnostic

- Status: accepted
- Date: 2026-05-17
- Decision: Adopt [regret_analysis_spec.md](docs/specs/regret_analysis_spec.md) with stress-scenario regret `best_pnl - pnl_R` over the evaluable opportunity set, reference profiles `favored`, `current`, and `benchmark`, headline `mean_regret` / `worst_regret`, optional macro regime slice when comparison exports regime PnL, and informational primary-window CAGR regret (Tier B). Artifact is diagnostic-only, does not change `selection_decision.json`, and runs after Pareto dominance in the comparison pipeline.
- Context: Post-audit Session 18 (RM-622 spec phase); product concept section 16 and audit PSA-012; comparison-ranking agent regret guidance.
- Rationale: Surfaces opportunity cost of committing to a reference profile under named stress scenarios using existing comparison exports without duplicating stress engine runs or auto-overriding Selection.
- Alternatives considered: Regret vs Pareto-efficient set only (deferred to V2); auto-switch selection on high regret (rejected — violates diagnostic boundary); full macro regime regret without projected comparison fields (deferred — optional slice with `not_available` when data missing).
- Assumptions: Session 19 implements the Regret Analysis builder, wires into `write_candidate_comparison_outputs`, and extends decision-package reporting.
- Consequences: `regret_analysis_v1` contract; journal/report may cite `worst_regret` for favored reference; implementation remains Session 19.
- Related documents: [docs/specs/regret_analysis_spec.md](docs/specs/regret_analysis_spec.md), [docs/specs/candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md), [OUTPUTS.md](OUTPUTS.md), [docs/ROADMAP.md](docs/ROADMAP.md) RM-622.
- Review trigger: Revisit when regret-vs-Pareto-set or multi-window regret surfaces are product-required.

Decision ID: DEC-2026-05-17-008
Title: Trade-off Explanation and Model Risk Diagnostics V1 — separate diagnostic artifacts

- Status: accepted
- Date: 2026-05-17
- Decision: Adopt two file-first diagnostic artifacts under `output_dir_final`: `tradeoff_explanation_v1` (baseline `current` → favored target from selection, metric/stress deltas without new formulas, weight-based turnover at write time) and `model_risk_diagnostics_v1` (deduplicated warning catalog from comparison, scores, stress, and run metadata). Pipeline placement is after `selection_decision.json` and before `action_plan.json`. Layer is non-binding and does not change selection, mandate, or stress pass/fail.
- Context: Post-audit Session 12 (RM-616 spec phase); audit PSA-012 and product concept sections 17–18 flagged partial coverage via selection bullets and scattered warnings only.
- Rationale: Makes “price of improvement” and model self-criticism explicit for decision package and journal without conflating them with Health Score or Selection outcomes.
- Alternatives considered: Single combined JSON (rejected — reporting and tests are clearer with two files); compute trade-off after action for action turnover (deferred — V1 uses weight deltas at trade-off write time); auto-veto selection on high model risk (rejected — violates diagnostic boundary).
- Assumptions: Session 13 implements `src/tradeoff_and_model_risk.py`, wires into `write_candidate_comparison_outputs`, and extends decision-package reporting sections.
- Consequences: See [docs/specs/tradeoff_and_model_risk_spec.md](docs/specs/tradeoff_and_model_risk_spec.md); journal and reporting prefer trade-off artifact over selection `tradeoff_bullets` when present.
- Related documents: [docs/specs/tradeoff_and_model_risk_spec.md](docs/specs/tradeoff_and_model_risk_spec.md), [docs/specs/selection_engine_spec.md](docs/specs/selection_engine_spec.md), [docs/specs/decision_package_reporting_spec.md](docs/specs/decision_package_reporting_spec.md), [OUTPUTS.md](OUTPUTS.md), [docs/ROADMAP.md](docs/ROADMAP.md) RM-616.
- Review trigger: Revisit if trade-off should run after action for turnover parity, or if concentration thresholds should become mandate-binding.

Decision ID: DEC-2026-05-17-007
Title: Candidate Portfolio Factory V1 — orchestrate before compare

- Status: accepted
- Date: 2026-05-17
- Decision: Adopt a file-first Candidate Portfolio Factory that runs existing per-candidate `run_*.py` builders in defined profiles, writes `candidate_factory_run_v1` under `output_dir_final`, uses continue-on-error and skip-existing-by-default, and hands off to `run_compare_variants.py`. Policy (`run_optimization.py` + Main report) and optional current materialization stay outside factory profiles. Main remains the production policy path; robust MV/scenario stay candidate inputs only.
- Context: Post-audit Session 10 (PSA-008): comparison quality depended on which builders were run manually; the product concept expects a controlled comparison arena.
- Rationale: Makes the intended candidate set auditable without duplicating optimizer formulas or changing comparison/selection contracts.
- Alternatives considered: Require manual script runs only (rejected — opaque and error-prone); embed all builders in one mega-optimizer (rejected — violates Main vs candidate boundary); auto-run policy inside factory (rejected — blurs production release path).
- Assumptions: Registry stays aligned with `_REGISTRY_ROWS` in [src/candidate_comparison.py](src/candidate_comparison.py).
- Consequences: Implemented `run_candidate_factory.py` and [src/candidate_factory.py](src/candidate_factory.py); RM-615 done; factory run summary under `output_dir_final`.
- Related documents: [docs/specs/candidate_factory_spec.md](docs/specs/candidate_factory_spec.md), [docs/specs/candidate_portfolios_spec.md](docs/specs/candidate_portfolios_spec.md), [docs/specs/candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md), [docs/ROADMAP.md](docs/ROADMAP.md) RM-615.
- Review trigger: Revisit if factory should parallelize builders, change default profile, or include policy/current in automated batches.
