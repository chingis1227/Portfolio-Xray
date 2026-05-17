# Diagnostic Product Concept Alignment Audit

Date: 2026-05-17

Scope:

- Compared `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md` against the current top-level documentation, detailed specs, and representative code entry points.
- Treated the product concept as non-binding direction, as required by `RULES.md`, `SPEC.md`, `WORKFLOW.md`, and the concept document itself.
- Reviewed the current dirty worktree as-is. No existing user changes were reverted.

## Executive Summary

The project documentation is broadly aligned with `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`.

The main alignment pattern is correct:

- The concept document defines the long-term product chain.
- `PRODUCT.md`, `BUSINESS_VISION.md`, and `ARCHITECTURE.md` translate that concept into target product and architecture language.
- `SPEC.md` and `docs/specs/*` correctly limit current behavior to the implemented CLI/file-driven, report-first system.
- Current code supports a large part of the diagnostic/reporting engine, candidate portfolio generation, stress/factor/macro diagnostics, and generated artifacts.

The biggest gap is not conceptual disagreement. It is product maturity: the project has many analytical pieces, but the full decision workflow is not yet unified into a product surface with formal scoring, formal selection, monitoring, and a journal.

## Current Implementation Status Against Product Chain

| Concept layer | Current status | Evidence | Recommended action |
| --- | --- | --- | --- |
| 1. Input & Assumptions Layer | Implemented V1, CLI/file-driven | `src/analysis_setup.py`, `src/input_assumptions.py`, `docs/specs/input_assumptions_spec.md`, tests | Keep; fix stale `config_ui` behavior around modes and weights. |
| 2. Portfolio X-Ray / Diagnostics | Substantially implemented in report form | `src/portfolio_xray.py`, `portfolio_xray.json`, `docs/specs/reporting_outputs_spec.md`, tests | Keep diagnostic-only boundary; productize UI later. |
| 3. Stress Test Lab | Implemented as report diagnostics | `src/stress.py`, `docs/specs/stress_testing_spec.md`, `stress_report.json` | Fix stale stress covariance section in spec. Interactive simulator remains future work. |
| 4. Candidate Portfolio Factory | Implemented through scripts | `run_equal_weight.py`, `run_risk_parity.py`, `run_minimum_cvar_*.py`, `run_robust_*.py`, `docs/specs/candidate_portfolios_spec.md` | Standardize candidate registry/comparison metadata before UI. |
| 5. Optimization Engine | Implemented as main policy optimizer plus benchmark candidates | `run_optimization.py`, `src/optimization.py`, `docs/specs/portfolio_construction_policy.md` | Current engine is not the full target menu from concept; document this as intentional. |
| 6. Strategy Backtest | Implemented in reporting pipeline, no full UX | `run_report.py`, `src/portfolio_dynamic.py`, snapshots/report artifacts | Product backtest screen and walk-forward UX remain TBD. |
| 7. Scenario & Stress Evaluation For Candidates | Mostly implemented via common report pipeline after fixed candidate weights | Candidate scripts and variant output folders | Add a unified comparison contract when productizing the arena. |
| 8. Macro Highlight / Macro Risk Dashboard | Diagnostics implemented, product UI TBD | `src/stress_factors.py`, `src/regime_factor_analytics.py`, `src/regime_portfolio_metrics.py` | Keep diagnostic-only; decide future dashboard scope. |
| 9. Candidate Comparison Layer | Partially implemented | `run_compare_variants.py`, `run_compare_ew_rp.py`, candidate folders | Needs canonical comparison artifact and UX. |
| 10. Portfolio Comparison Arena | Partial scripts only | Comparison scripts, `PRODUCT.md` status | Needs formal product spec. |
| 11. Portfolio Health Score | Not implemented | `SPEC.md` Target/TBD, `PRODUCT.md` Target/TBD | Define formulas/spec before code. |
| 12. Robustness Scorecard | Partially conceptual; related robust diagnostics exist | Robust MV/scenario docs and scripts | Do not call existing diagnostics a formal score until specified. |
| 13. Selection Engine | Not implemented | `SPEC.md` Target/TBD | Needs separate spec and decision log entry before implementation. |
| 14. Assumption Sensitivity | Not implemented as formal product module | Some lambda calibration/sensitivity scripts exist, but not general assumption sensitivity | Decide first sensitivity dimensions and output contract. |
| 15. Pareto Frontier / Dominance Check | Not implemented as formal module | `PRODUCT.md` Target/TBD | Define dominance rules before implementation. |
| 16. Regret Analysis | Not implemented as formal module | `PRODUCT.md` Target/TBD | Define scenario/regime regret metrics before implementation. |
| 17. Trade-off Explanation | Partially covered by commentary/reporting | `src/portfolio_commentary.py`, report artifacts | Needs standardized candidate-vs-current trade-off output. |
| 18. Model Risk Diagnostics | Partially implemented as diagnostic fragments | Factor stability, covariance quality, PCA, regime quality | Needs unified model-risk section if promoted to product layer. |
| 19. Action Engine | Partially covered by rebalance tooling and View After Optimization | `run_rebalance.py`, `src/rebalance.py`, `run_view_after_optimization.py` | Needs formal target/current delta artifact and cost/benefit logic. |
| 20. Rebalancing Advisor | Partially implemented | `run_rebalance.py`, `docs/operational_runbook.md` | Clarify threshold/turnover semantics. |
| 21. No-Trade Recommendation | Not formally implemented | `PRODUCT.md` Target/TBD | Current threshold output is utility behavior, not product no-trade logic. |
| 22. AI Portfolio Commentary | Implemented in report/commentary form | `src/portfolio_commentary.py`, `commentary.txt`, `stress_commentary.txt` | Keep disclaimers: not score, recommendation, or selection. |
| 23. Monitoring / What Changed | Not implemented | `SPEC.md` Target/TBD | Needs persistent analysis snapshots/workspace first. |
| 24. Decision Journal | Not implemented | `SPEC.md` Target/TBD | Needs saved analysis model and journal schema. |

## Documentation Alignment

The top-level documentation mostly agrees with the concept:

- `RULES.md`, `WORKFLOW.md`, `SPEC.md`, `AGENTS.md`, `README.md`, `PRODUCT.md`, and `ARCHITECTURE.md` consistently say the current implementation is report-first and CLI/file-driven.
- They consistently say product concept documents do not override specs, formulas, stress scenarios, data policy, optimizer policy, output contracts, or current code behavior.
- `PRODUCT.md` correctly lists many concept modules as partial or TBD.
- `BUSINESS_VISION.md` correctly frames the long-term business direction without making it binding.

The main documentation weakness is that some partial implemented utilities are under-described:

- `config_ui/` and `results_dashboard/` exist, but top-level docs mainly say "full UI TBD". This is not strictly wrong, but it can confuse readers because partial utility UIs do exist.
- The recommended wording is: "Partial utility UIs exist for config editing and read-only results viewing; the full product workspace/UI remains TBD."

## Confirmed Contradictions Or Stale Areas

### 1. Stress covariance spec contains an outdated section

Problem:

- `docs/specs/stress_testing_spec.md` early sections and code say current synthetic RC diagnostics use `taxonomy_blend_v1`.
- The same spec later has a stale "Stress covariance (for RC in stress)" section that describes the older `_stress_covariance` behavior for only Equity/Credit/Liquidity scenarios with simple vol scaling.
- Code shows `_stress_covariance` is now the `uniform_legacy` branch, while normal production uses `stress_covariance_taxonomy_blend`.

Impact:

- A future agent or developer could implement against the stale section and accidentally reintroduce old stress covariance behavior.

Action:

- Update the stale section to describe `taxonomy_blend_v1` as current default.
- Move the old `_stress_covariance` text under a clearly labeled legacy `uniform_legacy` subsection.
- Confirm the scenario list includes `equity_shock`, `credit_shock`, `liquidity_shock`, `recession_severe`, `rates_shock`, and `inflation_stagflation`.

### 2. Config UI still exposes an RC cap that current policy removed

Problem:

- `config_ui/templates/config_form.html` shows "Max RC per Asset" as a weight constraint.
- Current policy says `RC_vol` is diagnostic-only and the old `rc_asset_cap_pct` layer is not in the current pipeline.
- `config_ui/app.py` also does not parse or write `rc_asset_cap_pct`, so the UI field is silently ignored.

Impact:

- A user can believe they set a risk-contribution constraint, but the system ignores it.
- This conflicts with the project rule that assumptions and constraints must be explicit.

Action:

- Remove the RC cap field from `config_ui`, or relabel it as diagnostic-only and do not present it as a constraint.
- If RC caps are desired again, create a new product/spec decision before reintroducing code.

### 3. Config UI can blur generated policy weights and manual weights

Problem:

- `config_ui/app.py` loads generated `portfolio_weights.yml` into `weights` when `config.yml` has no weights.
- Saving the UI can then write those generated weights back into `config.yml` as fixed `weights`.
- Current rules separate generated policy weights, legacy fixed report weights, and `current_weights`.

Impact:

- This can make generated optimizer output look like manual/source config input.
- It weakens the recently added Input & Assumptions Layer V1 distinction.

Action:

- Add explicit `analysis_mode` support to the config UI.
- Add `current_weights` support only for `analysis_mode=analyze_current_weights`.
- Stop copying generated `portfolio_weights.yml` into editable `weights` by default.
- If showing generated weights in the UI, show them read-only and label them as generated output.

### 4. Partial UI exists, but product docs only say "full UI TBD"

Problem:

- `DESIGN.md`, `config_ui/`, and `results_dashboard/` show that partial utility UIs exist.
- `README.md`, `SPEC.md`, `PRODUCT.md`, and `ARCHITECTURE.md` mostly say "full interactive UI" or "product UI/workspace" is TBD.

Impact:

- New contributors may not know whether to maintain the existing UI utilities or treat all UI as future-only.

Action:

- Add a short line to `README.md`, `SPEC.md`, `PRODUCT.md`, and `ARCHITECTURE.md`: partial config/results utility UIs exist, but they are not the full product workspace.

### 5. Rebalance utility documentation overstates threshold semantics

Problem:

- `src/rebalance.py` says `rebalance_needed` returns true if max weight delta or turnover is above threshold.
- The implementation checks only max absolute per-ticker weight deviation.

Impact:

- This is small, but it matters if it is used as the basis for No-Trade Recommendation later.

Action:

- Either update the docstring to say max absolute ticker drift only, or add explicit turnover threshold logic and tests.

### 6. Known issues register is empty despite newly observed issues

Problem:

- `KNOWN_ISSUES.md` currently says no active issues are recorded.
- This audit found several concrete stale documentation/code issues.

Impact:

- If these issues are not fixed immediately, the known-issues register is no longer accurate.

Action:

- Either fix the issues now, or add concise entries to `KNOWN_ISSUES.md` until they are fixed and verified.

## What Is Already Done

Implemented or substantially implemented:

- CLI/file-driven main optimization and report pipeline.
- Config validation, client profile target resolution, and profile-derived targets.
- Input and Assumptions Layer V1 with `analysis_setup` and `input_assumptions`.
- Existing-portfolio diagnostic mode through `analysis_mode=analyze_current_weights`.
- Portfolio X-Ray v2 diagnostic summary with allocation, risk diagnostics, factor exposure, hidden-risk flags, archetype section, risk budget view, and weakness map.
- Portfolio metrics, dynamic NaN-safe backtesting, snapshots, risk contribution diagnostics.
- Stress testing with synthetic and historical scenarios, stress commentary, and diagnostic statuses.
- Factor diagnostics, Kalman/rolling beta diagnostics, factor covariance, factor variance decomposition, PCA, macro/regime diagnostics, regime analytics.
- Scenario library and normalized scenario library artifacts.
- Candidate portfolio scripts for equal weight, equal weight by asset class, risk parity, risk budgeting, HRP, minimum variance, maximum diversification, minimum CVaR, Robust MV, and Scenario-Based Robust Optimization.
- Robust MV lambda calibration and robust scenario candidate generation.
- View After Optimization tactical tilt protocol.
- Rebalance utility for current-to-target trade deltas.
- CSV, JSON, HTML, TXT, and PDF-style generated artifacts.
- ETF and stock taxonomy validation as annotation-only V1.
- Partial utility UIs: config editor and read-only results dashboard.

## What Is Not Done Yet

Not implemented as formal product modules:

- Full interactive product UI / saved workspace.
- Unified Candidate Comparison Arena.
- Formal Portfolio Health Score.
- Formal Robustness Scorecard.
- Formal Selection Engine.
- General Assumption Sensitivity module.
- Pareto Frontier / Dominance Check.
- Regret Analysis.
- Formal trade-off explanation across candidates.
- Unified Model Risk Diagnostics product layer.
- Full Action Engine with risk improvement per turnover and cost model.
- Productized No-Trade Recommendation.
- Monitoring / What Changed.
- Decision Journal.
- Transaction cost model.
- Full user-facing crisis replay and What Happens If simulator.
- Walk-forward / out-of-sample UX.

## Suggested Priority Order

1. Fix stale/contradictory documentation that could mislead code changes:
   - stress covariance section in `docs/specs/stress_testing_spec.md`
   - UI/current-weight boundary docs
   - rebalance docstring threshold semantics

2. Fix `config_ui` before treating it as a real product input surface:
   - add `analysis_mode`
   - separate `current_weights` from generated policy weights
   - remove or relabel ignored RC cap

3. Add known-issue entries for anything not fixed immediately.

4. Standardize candidate comparison output before building a full Selection Engine:
   - one comparison artifact
   - same metric/stress fields for every candidate
   - explicit candidate role and construction method

5. Only then formalize scoring:
   - Robustness Scorecard first
   - Portfolio Health Score second
   - Selection Engine after both are specified

## Bottom Line

The project is directionally consistent with the Diagnostic Product Concept. It already implements the analytical backbone of the product. The missing part is the unified decision product layer: comparison, scoring, selection, action/no-trade, monitoring, and decision record.

The main immediate work is not to add more analytics. It is to clean up stale specs/UI seams so the current system cannot be misunderstood as already having formal constraints, formal selection, or a full product UI.
