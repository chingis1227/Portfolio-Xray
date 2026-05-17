# Full Project System Audit

Date: 2026-05-17

Primary reference concept: `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`

Related quick audit: `docs/audits/2026-05-17_diagnostic_product_concept_alignment_audit.md`

## Purpose

This audit exists because the project has three parallel layers:

1. A broad product concept in `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`.
2. Many source-of-truth Markdown documents and detailed specs.
3. A large amount of already implemented Python/reporting/UI utility code.

The main question is not whether the concept is valuable. The main question is whether the repository now has a clear system for deciding what is current behavior, what is future product direction, what is stale, and what should be built next.

## Executive Conclusion

The project is directionally coherent, but operationally under-systematized.

The core analytical engine is already substantial: CLI optimization, report generation, Input and Assumptions V1, Portfolio X-Ray diagnostics, stress diagnostics, factor/macro diagnostics, candidate portfolio builders, robust variants, comparison scripts, report artifacts, and partial utility UIs exist.

The missing part is the product decision layer: a unified comparison arena, formal robustness/health scoring, formal selection, no-trade logic, monitoring, and decision journal. These are correctly marked as target/TBD in the strongest source-of-truth docs, but there is no single working roadmap that turns the concept into ordered implementation slices.

The most urgent work is not adding another analytics module. The most urgent work is:

- clean stale or contradictory docs/UI surfaces;
- make source-of-truth ownership explicit;
- create one implementation roadmap/backlog from the concept;
- standardize candidate comparison before building scores or selection.

## Audit Method

Reviewed as source-of-truth or evidence:

- Product concept: `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`.
- Root docs: `AGENTS.md`, `RULES.md`, `WORKFLOW.md`, `SPEC.md`, `README.md`, `PRODUCT.md`, `BUSINESS_VISION.md`, `ARCHITECTURE.md`, `DATA.md`, `OUTPUTS.md`, `TESTING.md`, `DESIGN.md`, `DECISIONS.md`, `KNOWN_ISSUES.md`, `CHANGELOG.md`, `PLANS.md`, `GLOSSARY.md`.
- Detailed specs under `docs/specs/`.
- ExecPlans under `docs/exec_plans/`.
- Representative code entry points: `run_optimization.py`, `run_report.py`, `run_view_after_optimization.py`, `run_rebalance.py`, `run_compare_variants.py`, `run_compare_ew_rp.py`, candidate scripts, `config_ui/`, `results_dashboard/`.
- Representative implementation modules: `src/analysis_setup.py`, `src/input_assumptions.py`, `src/portfolio_xray.py`, `src/stress.py`, `src/stress_covariance_taxonomy.py`, `src/portfolio_variants.py`, `src/portfolio_commentary.py`, `src/rebalance.py`, `src/config.py`.
- Focused tests referenced by specs, especially input assumptions, Portfolio X-Ray/reporting, stress covariance taxonomy, factor/stress/reporting tests, and candidate portfolio tests.

Generated output folders were treated as evidence/deliverables, not as source, following `OUTPUTS.md`.

## Status Labels

| Label | Meaning |
| --- | --- |
| Done | Implemented and broadly covered by current source docs/specs. |
| Partial | Some code or reports exist, but the product layer, unified contract, or UX is incomplete. |
| Not done | Target/TBD in docs or no formal implementation found. |
| Stale/Risk | Source docs or UI can mislead future work. |

## Source-Of-Truth Map

| Document | Current role | Audit finding |
| --- | --- | --- |
| `AGENTS.md` | Agent operating rules and source-of-truth routing. | Consistent with report-first, CLI/file-driven current state. |
| `RULES.md` | Highest-level project rules before behavior changes. | Correctly says concept docs do not override canonical specs and code contracts. |
| `WORKFLOW.md` | How to make changes and update docs/tests. | Correctly protects docs/code sync, but does not itself create a product roadmap. |
| `SPEC.md` | Current implementation contract. | Strongest current-state document. Correctly marks full UI, Selection Engine, Health Score, Monitoring, Decision Journal as TBD. |
| `PRODUCT.md` | Product direction and feature inventory. | Good bridge from concept to product backlog, but still broad and not yet an execution plan. |
| `BUSINESS_VISION.md` | Business positioning and target users. | Aligned with concept; not a behavior spec. |
| `ARCHITECTURE.md` | System structure and current/target architecture. | Mostly aligned; should mention partial utility UIs more explicitly. |
| `DESIGN.md` | UI/dashboard/generated visual-interface guidance. | Correctly owns `config_ui/` and `results_dashboard/`, but these partial UIs are under-mentioned elsewhere. |
| `DATA.md` | Data sources, pipeline, structures, quality rules. | Aligned with current implementation; future data vendors are not active. |
| `OUTPUTS.md` | Generated output boundaries and artifacts. | Important and aligned. Should continue to be used to avoid treating generated reports as source. |
| `TESTING.md` | Verification strategy. | Aligned. Notes that there is no dedicated Markdown link checker. |
| `DECISIONS.md` | Decision log. | Contains real accepted decisions, but its intro still says no project-level decisions are recorded. |
| `KNOWN_ISSUES.md` | Active issue register. | Says no active issues, but this audit found concrete stale docs/UI issues. |
| `docs/specs/*` | Module-level behavior contracts. | Mostly strong, with specific stale sections noted below. |
| `docs/exec_plans/*` | Large-change execution records. | Useful. Input Assumptions and RC diagnostic-only plans are important anchors. |

## Concept Alignment Summary

`docs/DIAGNOSTIC_PRODUCT_CONCEPT.md` is best understood as a long-term product blueprint. Current repository docs correctly avoid treating it as a direct implementation contract.

The concept and current docs agree on the target direction:

- diagnose current portfolio;
- stress test it;
- create candidate portfolios;
- compare candidates;
- explain trade-offs;
- eventually select or recommend an action/no-trade outcome;
- monitor changes over time;
- record decisions.

The codebase has implemented much of the analytical/reporting backbone. It has not yet implemented the formal decision product.

## Current Implementation Map

### Main Flow

| Area | Status | Evidence |
| --- | --- | --- |
| Optimization run | Done | `run_optimization.py`, `src/optimization.py`, `portfolio_weights.yml`, `run_result.json`. |
| Report run | Done | `run_report.py`, report JSON/CSV/HTML/TXT/PDF-style artifacts. |
| File-driven workflow | Done | `README.md`, `SPEC.md`, `ARCHITECTURE.md`, `OUTPUTS.md`. |
| Full product workspace UI | Not done | Marked TBD in `SPEC.md`, `PRODUCT.md`, `ARCHITECTURE.md`. |
| Partial config/results utility UI | Partial | `config_ui/`, `results_dashboard/`, `DESIGN.md`. |

### Data And Inputs

| Area | Status | Evidence |
| --- | --- | --- |
| Config validation | Done | `src/config.py`, `src/config_schema.py`, `docs/specs/input_assumptions_spec.md`. |
| Client profile target resolution | Done | `config/client_profiles.yml`, profile docs/specs. |
| Input and Assumptions Layer V1 | Done | `src/analysis_setup.py`, `src/input_assumptions.py`, `docs/specs/input_assumptions_spec.md`. |
| Existing portfolio diagnostic mode | Done in CLI/report path | `analysis_mode=analyze_current_weights`, `current_weights`, `run_report.py`. |
| Transaction costs | Not done/formal TBD | Concept target; not a full implemented product layer. |
| Horizon/liquidity/tax as full assumption engine | Partial | Some config/profile fields exist; not the full concept assumption engine. |

### Diagnostics And Reporting

| Area | Status | Evidence |
| --- | --- | --- |
| Portfolio metrics/backtests | Done | Report pipeline, snapshots, metric specs. |
| Portfolio X-Ray v2 | Done as diagnostic report | `src/portfolio_xray.py`, `portfolio_xray.json`, `docs/specs/reporting_outputs_spec.md`. |
| Hidden risk flags | Done as transparent diagnostics | `src/portfolio_xray.py`. |
| Portfolio archetype | Partial | X-Ray has an explanatory section, while some docs still mark formal archetype/UI as TBD. |
| Portfolio Weakness Map | Partial | X-Ray/report artifact exists; formal UI remains TBD. |
| AI commentary | Done as report/commentary | `src/portfolio_commentary.py`, `commentary.txt`, `stress_commentary.txt`. |
| Formal recommendation | Not done | X-Ray/report specs explicitly prohibit recommendations/selection decisions. |

### Stress, Factors, Macro

| Area | Status | Evidence |
| --- | --- | --- |
| Synthetic stress testing | Done as diagnostics | `src/stress.py`, `docs/specs/stress_testing_spec.md`. |
| Historical stress episodes | Done as diagnostics | Stress/report pipeline. |
| Stress RC diagnostics | Done | `taxonomy_blend_v1` path in `src/stress.py`, `src/stress_covariance_taxonomy.py`. |
| Factor diagnostics | Done/large partial | Factor betas, rolling/Kalman, covariance, attribution, variance decomposition. |
| PCA diagnostics | Done/large partial | Report/stress artifacts. |
| Macro/regime diagnostics | Done as diagnostics | Macro/regime modules and reports. |
| Interactive What Happens If simulator | Not done | Concept target; docs mark UI/workspace TBD. |
| Product macro dashboard UI | Not done | Diagnostics exist, product UI TBD. |

### Candidate Portfolios And Robust Variants

| Area | Status | Evidence |
| --- | --- | --- |
| Equal Weight | Done as candidate script | `run_equal_weight.py`, candidate specs. |
| Equal Weight by asset class | Done as candidate script | Candidate specs/scripts. |
| Risk Parity | Done as candidate script | `src/portfolio_variants.py`, candidate specs. |
| Risk budget variants | Done/partial as candidate scripts | `src/portfolio_variants.py`. |
| HRP | Done/partial as candidate script | `src/portfolio_variants.py`. |
| Minimum variance | Done as candidate script family | Candidate specs/scripts. |
| Maximum diversification | Done as candidate script family | Candidate specs/scripts. |
| Minimum CVaR | Done as candidate script family | Candidate specs/scripts. |
| Robust Mean-Variance | Done as benchmark/candidate | `docs/specs/robust_mv_spec.md`, robust MV scripts. |
| Scenario-Based Robust Optimization | Done as additive candidate builder | `docs/specs/robust_scenario_optimization_spec.md`. |
| Unified Candidate Portfolio Factory UX | Partial/not done | Scripts exist; unified product surface does not. |

### Comparison And Decision Layer

| Area | Status | Evidence |
| --- | --- | --- |
| EW vs RP comparison | Partial | `run_compare_ew_rp.py`. |
| Policy vs EW/RP/Robust Scenario comparison | Partial | `run_compare_variants.py`, `portfolio_comparison.json/txt`. |
| Unified comparison arena | Not done | Current comparison scripts are useful but not canonical product arena. |
| Robustness Scorecard | Partial/conceptual | Robust diagnostics exist; no formal scorecard contract. |
| Portfolio Health Score | Not done | Explicitly target/TBD. |
| Selection Engine | Not done | Explicitly target/TBD. |
| Assumption Sensitivity | Not done as formal module | Some calibration/sensitivity-like scripts exist, but not general assumption sensitivity. |
| Pareto/Dominance | Not done as formal module | Product target. |
| Regret Analysis | Not done as formal module | Product target. |
| Formal trade-off explanation across candidates | Partial | Commentary exists; candidate-level trade-off contract is missing. |

### Action, Monitoring, Journal

| Area | Status | Evidence |
| --- | --- | --- |
| View After Optimization | Done as tactical tilt tool | `run_view_after_optimization.py`, `docs/specs/view_after_optimization_spec.md`. |
| Rebalance utility | Partial | `run_rebalance.py`, `src/rebalance.py`. |
| Full Action Engine | Not done | Needs target/current delta, turnover, costs, benefit scoring, and recommendation rules. |
| No-Trade Recommendation | Not done formally | Current threshold output is utility behavior, not product no-trade logic. |
| Monitoring / What Changed | Not done | Explicitly target/TBD. |
| Decision Journal | Not done | Explicitly target/TBD. |

## 24-Layer Concept Matrix

| # | Concept layer | Current status | Main gap |
| --- | --- | --- | --- |
| 1 | Input & Assumptions Layer | Done V1 | UI still lags behind config semantics. |
| 2 | Portfolio X-Ray / Diagnostics | Done as report diagnostics | Formal product UI remains TBD. |
| 3 | Stress Test Lab | Done as report diagnostics | Interactive simulator/crisis replay UI not done. |
| 4 | Candidate Portfolio Factory | Partial/done scripts | Unified factory UX and registry missing. |
| 5 | Optimization Engine | Done for current policy plus benchmarks | Not the full target optimizer menu/workspace. |
| 6 | Strategy Backtest | Done in report pipeline | Product backtest UX/walk-forward screen missing. |
| 7 | Scenario & Stress Evaluation For Candidates | Partial | Needs unified candidate comparison contract. |
| 8 | Macro Dashboard | Partial diagnostics | Product dashboard UI and regime-fit score not formal. |
| 9 | Candidate Comparison Layer | Partial | Existing scripts are not a canonical comparison layer. |
| 10 | Portfolio Comparison Arena | Partial/not done | Needs product spec and canonical artifact. |
| 11 | Portfolio Health Score | Not done | Needs formula/spec before code. |
| 12 | Robustness Scorecard | Partial/conceptual | Existing robust diagnostics are not a formal scorecard. |
| 13 | Selection Engine | Not done | Needs scoring prerequisites and decision spec. |
| 14 | Assumption Sensitivity | Not done formal | Needs dimensions, artifacts, and tests. |
| 15 | Pareto Frontier / Dominance | Not done | Needs dominance rules. |
| 16 | Regret Analysis | Not done | Needs scenario/regime regret definitions. |
| 17 | Trade-off Explanation | Partial | Commentary exists; candidate trade-off artifact missing. |
| 18 | Model Risk Diagnostics | Partial | Diagnostics exist in fragments; no unified product layer. |
| 19 | Action Engine | Partial | Rebalance/tilt tools exist; action recommendation logic missing. |
| 20 | Rebalancing Advisor | Partial | Utility exists; formal product advisor missing. |
| 21 | No-Trade Recommendation | Not done | Needs explicit no-trade rules and tests. |
| 22 | AI Portfolio Commentary | Done report form | Must stay non-binding until recommendation layer exists. |
| 23 | Monitoring / What Changed | Not done | Needs persistent snapshot/workspace model. |
| 24 | Decision Journal | Not done | Needs journal schema and lifecycle. |

## Contradiction And Risk Register

### AUD-001: No single implementation roadmap connects concept to execution

Severity: High

Evidence:

- `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md` defines a 24-layer product.
- `PRODUCT.md` lists broad feature inventory and statuses.
- `SPEC.md` states current behavior.
- `PLANS.md` defines how to write ExecPlans for large changes.
- There is no single ordered roadmap/backlog that says which concept layers will be built next, in what order, and what each requires.

Impact:

- The repository has many good documents, but no central execution spine.
- Future work can jump between analytics, UI, scoring, and commentary without prerequisites.

Recommended fix:

- Add `docs/ROADMAP.md` or `docs/product_backlog.md`.
- Structure it around phases:
  1. Stabilize current source-of-truth and UI semantics.
  2. Standardize candidate comparison.
  3. Build Robustness Scorecard.
  4. Build Health Score.
  5. Build Selection/No-Trade.
  6. Build monitoring and journal.

### AUD-002: Stress covariance spec has a stale legacy section

Severity: High

Evidence:

- `docs/specs/stress_testing_spec.md` early sections describe current `taxonomy_blend_v1` stress covariance.
- The same file later has a section "Stress covariance (for RC in stress)" that still describes older `_stress_covariance` behavior with uniform risk-on correlation and scalar `vol_mult`.
- `src/stress.py` uses `_stress_covariance` only under `stress_cov_method == "uniform_legacy"`.
- `tests/test_stress_covariance_taxonomy.py` asserts `taxonomy_blend_v1`.

Impact:

- Future changes could accidentally reimplement legacy stress covariance behavior as current behavior.

Recommended fix:

- Rewrite the stale section so `taxonomy_blend_v1` is the current default.
- Move the older `_stress_covariance` behavior under a clearly labeled `uniform_legacy` subsection.
- Keep scenario rows for `equity_shock`, `credit_shock`, `liquidity_shock`, `recession_severe`, `rates_shock`, and `inflation_stagflation` consistent.

### AUD-003: Config UI exposes an RC cap that policy removed

Severity: High

Evidence:

- `config_ui/templates/config_form.html` shows "Max RC per Asset" and `rc_asset_cap_pct`.
- `docs/specs/feasibility_constraints_spec.md` says the old RC asset cap layer is not in the current pipeline.
- `docs/exec_plans/2026-04-28_rc_diagnostic_only.md` says RC caps were removed and RC_vol is diagnostic-only.
- `config_ui/app.py` does not parse/write this field, so it is silently ignored.

Impact:

- A user can believe they configured a real risk-contribution constraint when they did not.
- This conflicts with the project's explicit-assumption style.

Recommended fix:

- Remove the field from the UI, or relabel it as non-editable diagnostic context.
- Do not reintroduce RC caps without a new decision record and spec update.

### AUD-004: Config UI can blur generated policy weights and manual input weights

Severity: High

Evidence:

- `config_ui/app.py` loads `portfolio_weights.yml` into editable `weights` when config has no weights.
- Current docs distinguish `weights`, `current_weights`, generated `portfolio_weights.yml`, and `analysis_mode`.
- `docs/specs/input_assumptions_spec.md` makes this distinction explicit.

Impact:

- Generated optimizer output can become editable source config.
- A user may confuse "current portfolio" with "generated policy target".

Recommended fix:

- Add explicit `analysis_mode` controls to `config_ui`.
- Add `current_weights` entry for `analyze_current_weights`.
- Show generated `portfolio_weights.yml` only as read-only generated output.
- Avoid writing generated weights back into `config.yml` as manual `weights` by default.

### AUD-005: Partial UIs exist, but top-level docs mostly say UI is TBD

Severity: Medium

Evidence:

- `config_ui/` and `results_dashboard/` exist.
- `DESIGN.md` discusses UI/dashboard work.
- `README.md`, `SPEC.md`, `PRODUCT.md`, and `ARCHITECTURE.md` mostly describe full interactive UI/product workspace as TBD.

Impact:

- New contributors may not know whether partial UIs are supported utilities or abandoned experiments.

Recommended fix:

- Add one consistent sentence to top-level docs:
  "Partial utility UIs exist for config editing and read-only result viewing; the full product workspace remains TBD."

### AUD-006: Rebalance threshold documentation overstates turnover logic

Severity: Medium

Evidence:

- `src/rebalance.py::rebalance_needed` docstring says max drift or turnover can trigger rebalance.
- `compute_trades` currently checks only maximum absolute per-ticker weight deviation when `threshold_pct` is set.
- `run_rebalance.py` help text correctly describes max absolute weight drift.

Impact:

- If this utility becomes the basis for No-Trade Recommendation, the product could inherit incorrect semantics.

Recommended fix:

- Either update the docstring to say max absolute ticker drift only, or implement explicit turnover threshold logic with tests.

### AUD-007: `DECISIONS.md` intro is stale

Severity: Low

Evidence:

- `DECISIONS.md` says no project-level decisions are recorded.
- The same file contains accepted decisions `DEC-2026-05-15-001` and `DEC-2026-05-15-002`.

Impact:

- Small trust issue in the decision log.

Recommended fix:

- Replace the stale intro sentence with a short note that accepted decisions are listed below.

### AUD-008: `KNOWN_ISSUES.md` is empty despite known issues

Severity: Medium

Evidence:

- `KNOWN_ISSUES.md` says no active issues are currently recorded.
- This audit identifies active stale docs/UI issues.

Impact:

- If issues are not fixed immediately, the known-issues register is inaccurate.

Recommended fix:

- Either fix all issues immediately, or add concise entries for AUD-002 through AUD-006 and AUD-009.

### AUD-009: Source text encoding/mojibake debt exists

Severity: Medium

Evidence:

- Source docs and code comments contain mojibake patterns such as `вЂ`, `Sigma`, `delta`, `beta`, `*`, and unreadable Russian text in at least `docs/specs/production_workflow.md` and parts of other source docs/specs.
- Generated outputs also contain encoding artifacts, but generated outputs are not source and should not drive source edits.

Impact:

- Specs become hard to read.
- Search and future doc updates become unreliable.
- Mathematical symbols and Russian text can be misunderstood.

Recommended fix:

- Restore affected source docs as clean UTF-8.
- Prioritize source docs/specs before generated outputs.
- Do this as a separate docs hygiene task to avoid mixing with behavior changes.

### AUD-010: Candidate comparison exists, but is not yet a canonical arena

Severity: Medium

Evidence:

- `run_compare_ew_rp.py` compares EW vs RP.
- `run_compare_variants.py` compares Policy vs Equal-Weight vs Risk-Parity vs Robust Scenario.
- `PRODUCT.md` still marks Candidate Comparison Arena as partial.

Impact:

- Selection/Health Score cannot safely build on ad hoc comparison artifacts.

Recommended fix:

- Define one canonical `candidate_comparison.json` contract.
- Every candidate should expose construction method, role, constraints, metric block, stress block, drawdown block, regime/factor block, and warnings.
- Only after this should scoring/selection be implemented.

### AUD-011: Current commentary and X-Ray are diagnostic, but concept asks for recommendation

Severity: Medium

Evidence:

- `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md` targets recommendations, no-trade decisions, and action explanations.
- `docs/specs/reporting_outputs_spec.md` and `src/portfolio_xray.py` explicitly forbid scores, selection, recommendation, no-trade decisions, or trade instructions in Portfolio X-Ray.

Impact:

- This is not a contradiction if understood correctly, but it is a product boundary that must stay explicit.

Recommended fix:

- Keep current diagnostics non-binding.
- Create a separate Selection/Action spec before any recommendation language is added.

### AUD-012: Product status is clear, but not test-gated as documentation

Severity: Low/Medium

Evidence:

- `TESTING.md` notes no dedicated Markdown link checker.
- Many docs cross-link specs, source files, and generated-output policy.

Impact:

- Stale references can survive after renames or module moves.

Recommended fix:

- Add a lightweight docs verification task later:
  - check Markdown links;
  - check references to removed fields such as `rc_asset_cap_pct`;
  - check generated-output paths are not treated as source.

## What Is Already Done

The project already has a strong analytical base:

- Main optimization flow.
- Main reporting flow.
- Config validation and client profile target resolution.
- Input and Assumptions Layer V1.
- Existing-portfolio diagnostic mode using `analysis_mode=analyze_current_weights`.
- Report-first portfolio diagnostics.
- Portfolio X-Ray v2.
- Stress testing and stress commentary.
- Synthetic stress covariance taxonomy engine.
- Historical stress diagnostics.
- Factor diagnostics and rolling/Kalman beta work.
- Factor covariance and factor variance decomposition.
- PCA diagnostics.
- Macro/regime diagnostics.
- Scenario library and normalized scenario library artifacts.
- Candidate portfolios: EW, EW by class, RP, risk-budget variants, HRP, min variance, max diversification, min CVaR, Robust MV, Scenario-Based Robust Optimization.
- Robust MV lambda calibration tooling.
- View After Optimization.
- Rebalance utility.
- Report outputs in JSON/CSV/HTML/TXT/PDF-style forms.
- Partial config editor UI.
- Partial read-only results dashboard.
- ETF/stock taxonomy as annotation-only V1.

## What Is Not Done Yet

The main product gaps are:

- Full product workspace UI.
- Saved analysis workspace/state model.
- Unified Candidate Portfolio Factory UX.
- Unified Candidate Comparison Arena.
- Formal Robustness Scorecard.
- Formal Portfolio Health Score.
- Formal Selection Engine.
- General Assumption Sensitivity.
- Pareto/Dominance module.
- Regret Analysis module.
- Candidate-level trade-off explanation artifact.
- Unified Model Risk Diagnostics product layer.
- Full Action Engine.
- Formal Rebalancing Advisor with turnover/cost/benefit logic.
- Formal No-Trade Recommendation.
- Transaction cost model.
- Monitoring / What Changed.
- Decision Journal.
- Interactive What Happens If simulator.
- Product macro dashboard.
- Walk-forward/out-of-sample product UX.

## Recommended System Plan

### Phase 0: Stabilize the current source of truth

Goal: make the current repository harder to misunderstand.

Tasks:

- Fix `docs/specs/stress_testing_spec.md` stale stress covariance section.
- Fix or remove stale `config_ui` RC cap.
- Update `config_ui` for `analysis_mode` and `current_weights`.
- Clarify partial utility UI status in top-level docs.
- Fix `src/rebalance.py` threshold docstring or implement turnover threshold.
- Update `DECISIONS.md` stale intro.
- Add known issue entries for unresolved audit items.
- Clean source-doc mojibake in a focused docs hygiene pass.

Exit condition:

- A new developer can read root docs and not confuse current behavior with future product goals.

### Phase 1: Create the execution spine

Goal: turn the product concept into an ordered implementation backlog.

Tasks:

- Create `docs/ROADMAP.md` or `docs/product_backlog.md`.
- Give each target module an ID, status, owner doc, prerequisites, output artifact, and tests.
- Split concept layers into implementation slices.
- Use ExecPlans only for large/risky slices, not for every small task.

Exit condition:

- Every future feature can be mapped to one roadmap item and one owning spec.

### Phase 2: Standardize candidate comparison

Goal: create the foundation for any score or selection.

Tasks:

- Define canonical `candidate_comparison.json`.
- Normalize candidate metadata across policy, EW, RP, robust, MinVar, MaxDiv, MinCVaR, etc.
- Include metrics, stress, drawdown, factor/regime, warnings, and construction method.
- Update comparison scripts to produce the canonical artifact.

Exit condition:

- Every candidate can be compared in one table without special-case interpretation.

### Phase 3: Build scoring carefully

Goal: add scores only after comparison inputs are stable.

Recommended order:

1. Robustness Scorecard.
2. Portfolio Health Score.
3. Selection Engine.
4. No-Trade Recommendation.

Rules:

- Each score needs a spec before code.
- Each score must state inputs, formulas, missing-data behavior, thresholds, and output contract.
- No scoring output should silently override mandate gates or diagnostics.

Exit condition:

- Scores are transparent enough that a user can see why a portfolio was favored or rejected.

### Phase 4: Productize action, monitoring, and journal

Goal: turn one-time analysis into an ongoing decision workflow.

Tasks:

- Define saved analysis snapshot schema.
- Define monitoring diff artifact.
- Define journal schema.
- Connect selected candidate, no-trade/action decision, and rationale into the journal.
- Add UI only after data contracts are stable.

Exit condition:

- The system can answer: what changed, what did we decide, why, and what happened after.

## Suggested Immediate Backlog

| ID | Task | Type | Priority |
| --- | --- | --- | --- |
| AUD-FIX-001 | Rewrite stale stress covariance section in `docs/specs/stress_testing_spec.md`. | Docs/spec | P0 |
| AUD-FIX-002 | Remove or correct stale RC cap field in `config_ui`. | UI/code | P0 |
| AUD-FIX-003 | Add `analysis_mode`/`current_weights` semantics to `config_ui`. | UI/code | P0 |
| AUD-FIX-004 | Clarify partial utility UI status in root docs. | Docs | P1 |
| AUD-FIX-005 | Fix `src/rebalance.py` threshold docstring or add turnover logic/tests. | Code/docs | P1 |
| AUD-FIX-006 | Update `DECISIONS.md` intro. | Docs | P2 |
| AUD-FIX-007 | Add unresolved audit items to `KNOWN_ISSUES.md`. | Docs | P1 |
| AUD-FIX-008 | Clean source-doc mojibake in a dedicated pass. | Docs hygiene | P1 |
| AUD-PLAN-001 | Create `docs/ROADMAP.md` or `docs/product_backlog.md`. | Planning | P0 |
| AUD-PLAN-002 | Define canonical candidate comparison artifact. | Spec | P0 |
| AUD-PLAN-003 | Draft Robustness Scorecard spec. | Spec/product | P1 |
| AUD-PLAN-004 | Draft Portfolio Health Score spec. | Spec/product | P2 |
| AUD-PLAN-005 | Draft Selection Engine and No-Trade Recommendation spec after scores exist. | Spec/product | P2 |

## Recommended Operating Rule Going Forward

Do not add new major analytics until the current source-of-truth cleanup and candidate comparison contract are done.

The project already has many analytical components. The next quality jump will come from systematizing the decision pipeline:

concept -> source-of-truth spec -> canonical artifact -> tests -> report/UI surface -> decision record

## Verification Notes

This audit changed documentation only.

Recommended verification for this audit file:

- Confirm Markdown file exists under `docs/audits/`.
- Search the audit for all `AUD-` IDs.
- No pytest run is required for this audit alone because no executable behavior changed.

