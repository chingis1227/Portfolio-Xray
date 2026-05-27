# Core MVP Runtime Integration and Entrypoint Audit Plan

## 1. Executive Summary

Read-only audit completed. No code or runtime behavior was changed.

Current state is **partly clear in code, but confusing in docs and entrypoints**.

- `run_portfolio_review.py` currently dry-runs as **diagnosis-only by default**:
  `run_report.py --materialize-analysis-subject --output-profile site_api --review-mode core --use-review-run-context`.
- Primary product truth lives under `{output_dir_final}/analysis_subject/`.
- Product-facing Block 2.3 and Block 3 outputs are mostly separated correctly:
  - `portfolio_xray.json.block_2_3_factor_exposure` is an adapter over existing factor diagnostics.
  - `stress_report.json` owns `stress_results_v1`, `hedge_gap_analysis_v1`, and `current_portfolio_stress_scorecard_v1`.
- Main confusion: factor calculations are not represented as a clear named raw layer; `run_report.py` and legacy `run_optimization.py` duplicate substantial factor/stress enrichment orchestration.
- Runtime script surface is crowded: many `run_*.py` scripts are advanced, research, legacy, or test utilities but still look like product entrypoints.

Top 3 risks:

1. Stale docs still imply `--mode core` / default review runs a candidate batch, while current code default is diagnosis-only.
2. Factor diagnostics are shared in practice but not cleanly named as `factor_diagnostics_raw`, causing adapter-boundary ambiguity.
3. Legacy surfaces (`sections.*`, `stress_scorecard_v1`, `stress_conclusions`, root artifacts, old scripts) can be mistaken for Core MVP product outputs.

Audit evidence:

- `python run_portfolio_review.py --dry-run` confirms diagnosis-only default.
- `python run_portfolio_review.py --candidates equal_weight --dry-run` confirms one-candidate path.
- `python run_portfolio_review.py --with-candidates --dry-run` and `--mode full --dry-run` confirm research/batch paths.
- Canonical input `VOO/QQQ/TLT/GLD/Cash USD` validates as `analysis_mode=analyze_current_weights`; real cash is not downloaded and is not replaced by `BIL`.
- Targeted tests passed: `33 passed`.

## 2. Factor Pipeline Audit

### Finding F1 — Shared factor calculation infrastructure exists but is implicit

- File path: `src/stress_factors.py`
- Functions/modules: `build_factor_matrix`, `compute_asset_factor_betas_weekly`, `compute_asset_factor_betas_from_daily_returns`, `portfolio_factor_regression_weekly`, `attach_kalman_factor_betas_to_stress_report`, `factor_variance_decomposition_weekly`, `factor_covariance_analytics`
- Current behavior: owns most raw factor data loading, beta estimation, regression diagnostics, Kalman, covariance, and variance decomposition.
- Classification: correct shared calculation boundary, but needs clearer raw contract.
- Why it matters: Block 2.3 and Block 3 share evidence, but no single `factor_diagnostics_raw` object makes the boundary obvious.
- Recommended action: introduce a documented shared raw diagnostics contract or helper wrapper, without changing formulas.
- Tests needed: factor diagnostics golden/contract tests ensuring existing stress fields remain populated.

### Finding F2 — `run_report.py` mixes orchestration, raw factor calculation, Stress Lab assembly, and adapter refresh

- File path: `run_report.py`
- Functions/modules: `run_portfolio_report_for_weights`
- Current behavior: computes factor betas, calls `run_stress`, mutates `stress_report` with factor diagnostics, then reattaches Block 3 product adapters.
- Classification: legacy coupling / mixed adapter boundary.
- Why it matters: product adapters are clean, but the raw calculation layer is hidden inside a large runtime function.
- Recommended action: extract factor/stress enrichment into a shared internal helper while preserving output fields.
- Tests needed: before/after JSON contract tests for `stress_report.json` factor keys and Block 3 product keys.

### Finding F3 — Block 2.3 is correctly adapter-only

- File path: `src/block_2_3_factor_exposure.py`
- Function/module: `build_block_2_3_factor_exposure`
- Current behavior: reads existing `stress_report` fields; does not run regressions, Kalman, data loading, or Stress Lab.
- Classification: correct shared calculation boundary / acceptable adapter dependency.
- Why it matters: this matches the product boundary: sensitivity in X-Ray, shocks in Stress Lab.
- Recommended action: preserve; add regression tests that forbid scenario/stress-loss fields in Block 2.3.
- Tests needed: extend `tests/test_block_2_3_factor_exposure.py`.

### Finding F4 — Legacy X-Ray factor section duplicates part of Block 2.3 adapter logic

- File path: `src/portfolio_xray.py`
- Function/module: `_factor_exposure_section`
- Current behavior: builds legacy `sections.factor_exposure` directly from `stress_report`.
- Classification: duplicated logic / legacy coupling.
- Why it matters: product and legacy factor surfaces can drift.
- Recommended action: keep for compatibility, but mark non-product and eventually derive from `block_2_3_factor_exposure`.
- Tests needed: product block contract tests; optional legacy drift test.

### Finding F5 — Legacy X-Ray sections still read Stress Lab evidence

- File path: `src/portfolio_xray.py`
- Functions/modules: `_hidden_risk_section`, `_risk_budget_section`, `_weakness_map_section`, `sections.*`
- Current behavior: legacy sections can include stress/scenario evidence, while top-level product blocks 2.4–2.6 are clean.
- Classification: product boundary leak if consumed as product; acceptable only as legacy section coupling.
- Why it matters: UI/API must not treat `sections.*` as Core MVP product truth.
- Recommended action: document and test that Core MVP consumers use top-level `block_2_*` keys only.
- Tests needed: product-block forbidden-key tests.

### Finding F6 — Block 3 product adapters are correctly separated

- File paths:
  - `src/stress_results_block.py`
  - `src/hedge_gap_analysis_block.py`
  - `src/current_portfolio_stress_scorecard_block.py`
- Current behavior: adapt existing stress evidence into `stress_results_v1`, `hedge_gap_analysis_v1`, and `current_portfolio_stress_scorecard_v1`.
- Classification: correct product adapter boundary.
- Recommended action: preserve; keep legacy `stress_scorecard_v1` separate.
- Tests needed: Block 3 contract tests for no mandate/pass-fail fields in product keys.

### Finding F7 — `run_optimization.py` duplicates stress/factor enrichment

- File path: `run_optimization.py`
- Current behavior: legacy policy optimizer computes factor/stress diagnostics and writes `stress_report.json`.
- Classification: duplicated logic / legacy coupling.
- Why it matters: factor fixes may need to be made twice.
- Recommended action: move shared enrichment behind a helper used by both report and legacy optimizer, or explicitly freeze optimizer path as legacy.
- Tests needed: legacy policy compatibility stress report test.

### Finding F8 — Duplicate `build_factor_matrix_monthly` definition needs verification

- File path: `src/stress_factors.py`
- Function/module: `build_factor_matrix_monthly`
- Current behavior: function appears defined twice with equivalent intent.
- Classification: duplicated logic / needs verification.
- Recommended action: remove duplication only after focused tests prove no behavior change.
- Tests needed: factor matrix monthly regression tests.

## 3. End-to-End Runtime Audit

### Product runtime

- Command / entrypoint: `python run_portfolio_review.py`
- Expected input: `investor_currency`, `tickers`, `current_weights` or `weights`.
- Canonical test input: `VOO 45%, QQQ 20%, TLT 15%, GLD 10%, Cash USD 10%, investor_currency USD`.
- Actual validation result: resolves to `analysis_mode=analyze_current_weights`, `analysis_subject.type=current_portfolio`, `Cash USD` preserved as real cash.
- Expected output files:
  - `{output_dir_final}/analysis_subject/run_metadata.json`
  - `{output_dir_final}/analysis_subject/portfolio_xray.json`
  - `{output_dir_final}/analysis_subject/stress_report.json`
  - `{output_dir_final}/analysis_subject/scenario_library.json`
  - `{output_dir_final}/analysis_subject/output_manifest.json`
- Actual dry-run behavior: only diagnosis stage; no candidate factory, no optimizer.
- Blocks 2.1–2.6: present in existing subject artifact.
- Blocks 3.1–3.4: present via `scenario_library_meta` / sidecars, `stress_results_v1`, `hedge_gap_analysis_v1`, `current_portfolio_stress_scorecard_v1`.
- Real cash: validation/tests say yes; exact live canonical run not executed because it would mutate generated outputs.
- Candidate/optimizer/mandate/suitability triggered: no in default dry-run.
- Gaps:
  - standalone `input_assumptions.json` missing in existing subject folder; input assumptions are embedded in `run_metadata.json`.
  - generated artifacts may be stale and should not be used as source truth.
  - docs still conflict about default candidate behavior.
- Recommended action: add a temp-output E2E smoke using canonical cash example.

### One-candidate product runtime

- Command: `python run_portfolio_review.py --candidates equal_weight`
- Actual dry-run behavior: diagnosis + candidate factory explicit list + compare.
- Classification: Product one-candidate runtime.
- Recommended action: keep as official demo path.

### Research / batch runtime

- Commands:
  - `python run_portfolio_review.py --with-candidates`
  - `python run_portfolio_review.py --mode full`
  - `python run_candidate_factory.py --profile core_fast|default_v1`
- Actual dry-run behavior: candidate batch.
- Classification: Research / advanced runtime.
- Recommended action: keep, but document as backend/research, not default Core MVP.

## 4. Runtime Entrypoint Inventory

| Script / command | Flags / modes | Outputs | Current purpose | Classification | Recommended status |
| --- | --- | --- | --- | --- | --- |
| `run_portfolio_review.py` | default, `--skip-candidates` | `analysis_subject/` JSON | Portfolio-first diagnosis | Core MVP product runtime | keep as primary |
| `run_portfolio_review.py --candidates ID` | explicit IDs | subject + selected candidate + compare | one-hypothesis demo | Product one-candidate | keep documented |
| `run_portfolio_review.py --with-candidates` | batch core | subject + candidate batch | backend candidate batch | Research / advanced | keep advanced |
| `run_portfolio_review.py --mode full` | full 16 menu | full candidate evidence | full research batch | Research / advanced | keep advanced |
| `run_report.py --materialize-analysis-subject` | review mode/profile | `analysis_subject/` | internal subject materializer | Product diagnostic-only | keep as internal |
| `run_report.py` bare | report/export profiles | root output folder | legacy/root report | Legacy | keep but namespace |
| `run_report.py --materialize-current` | current sidecar | `current_portfolio/` | current-vs-policy support | Legacy | keep documented as legacy |
| `run_candidate_factory.py` | profiles, `--then-compare`, execution modes | candidate folders, factory JSON | backend candidate factory | Research / advanced | keep advanced |
| `run_compare_variants.py` | `--output-profile` | comparison/verdict JSON | compare existing artifacts | Advanced/product utility | keep documented |
| `run_optimization.py` | profile/config/report flags | `portfolio_weights.yml`, root reports | legacy policy optimizer | Legacy | keep legacy |
| `run_mvp_workflow.py` | policy workflows | policy/current/factory/PDF chain | old wrapper | Legacy | move docs to legacy |
| `run_equal_weight.py` | none | equal-weight folder | candidate builder | Research / advanced | keep advanced |
| `run_equal_weight_by_asset_class.py` | none | candidate folder | candidate builder | Research / advanced | keep advanced |
| `run_risk_parity.py` | none | candidate folder | candidate builder | Research / advanced | keep advanced |
| `run_risk_budget_by_asset.py` | none | candidate folder | candidate builder | Research / advanced | keep advanced |
| `run_risk_budget_by_asset_class.py` | none | candidate folder | candidate builder | Research / advanced | keep advanced |
| `run_hierarchical_risk_parity.py` | none | candidate folder | candidate builder | Research / advanced | keep advanced |
| `run_minimum_variance.py` | none | candidate folder | optimizer candidate | Research / advanced | keep advanced |
| `run_minimum_variance_uncapped.py` | none | candidate folder | optimizer candidate | Research / advanced | keep advanced |
| `run_minimum_variance_advanced.py` | none | candidate folder | advanced optimizer candidate | Research / advanced | keep advanced |
| `run_maximum_diversification.py` | none | candidate folder | optimizer candidate | Research / advanced | keep advanced |
| `run_maximum_diversification_unconstrained.py` | none | candidate folder | optimizer candidate | Research / advanced | keep advanced |
| `run_minimum_cvar_constrained.py` | none | candidate folder | optimizer candidate | Research / advanced | keep advanced |
| `run_minimum_cvar_uncapped.py` | none | candidate folder | optimizer candidate | Research / advanced | keep advanced |
| `run_robust_mean_variance_constrained.py` | config/lambda | candidate folder | robust optimizer | Research / advanced | keep advanced |
| `run_robust_mean_variance_uncapped.py` | config/lambda | candidate folder | robust optimizer | Research / advanced | keep advanced |
| `run_robust_scenario_optimization.py` | config/objective/output | robust scenario artifacts | robust research | Research / advanced | keep advanced |
| `run_robust_scenario_portfolio_report.py` | weights/no-cache | robust scenario folder | robust candidate report | Research / advanced | keep advanced |
| `run_robust_mv_lambda_calibration.py` | calibration/grid | calibration artifacts | MV lambda calibration sweep | Research / advanced | keep advanced |
| `run_advanced_mv_lambda_sensitivity.py` | grid constants | lambda sensitivity CSV/JSON | analysis sweep | Research / advanced | keep advanced |
| `run_compare_ew_rp.py` | none | legacy comparison | old comparison | Deprecated / archive candidate | move to legacy |
| `run_stress_variant.py` | variant/no-cache | variant stress print/report | stress validation | Test/research utility | keep under scripts or legacy |
| `run_rebalance.py` | target/current/nav | trade list | rebalancing utility | Legacy / advanced | remove from main product docs |
| `run_view_after_optimization.py` | asset/delta | view report | post-optimization tilt | Legacy | keep legacy |
| `run_etf_universe.py` | validation/export | universe reports | data maintenance | Test/maintenance | keep utility |
| `run_stock_universe.py` | validation/export | universe reports | data maintenance | Test/maintenance | keep utility |
| `run_ibkr_market_data.py` | market data flags | smoke output | market data smoke | Test-only utility | keep utility |
| `rebuild_pdf_reports.py` | portfolio/legacy PDF modes | PDFs/MD sidecars | explicit PDF export | Legacy/export utility | keep explicit only |
| `scripts/run_one_candidate_from_method.py` | method/goal/run | command mapping | Launchpad helper | Product utility | keep documented |
| `scripts/validate_one_candidate_demo.py` | output/candidate | validation report | demo validator | Test-only utility | keep |
| `scripts/validate_calibrated_stress_cov_portfolio.py` | none | stdout | one-off validation | Test-only utility | keep or archive |
| `scripts/validate_synthetic_stress_covariance.py` | none | stdout | stress covariance validation | Test-only utility | keep |

### Scripts folder utilities (non-entrypoint helpers)

These are not product entrypoints; they are repo maintenance / verification / timing helpers.

| Script | Purpose | Classification | Recommended status |
| --- | --- | --- | --- |
| `scripts/verify_docs.py` | docs verification / link & structure checks | Test/maintenance | keep utility |
| `scripts/scan_generated_outputs.py` | scan generated artifacts for drift / inconsistencies | Test/maintenance | keep utility |
| `scripts/verify_live_core_e2e.py` | live core E2E verification harness | Test/maintenance | keep utility |
| `scripts/verify_live_full_e2e.py` | live full E2E verification harness | Test/maintenance | keep utility |
| `scripts/blocks_1_5_e2e_timing_audit.py` | timing audit harness | Test/maintenance | keep utility |
| `scripts/shared_evidence_session06_timing_smoke.py` | timing smoke (shared evidence) | Test/maintenance | keep utility |
| `scripts/site_api_session06_benchmark_smoke.py` | site/api benchmark smoke | Test/maintenance | keep utility |
| `scripts/fix_doc_mojibake.py` | fix doc encoding mojibake | Maintenance | keep utility |
| `scripts/fix_cp1251_mojibake.py` | fix cp1251 mojibake | Maintenance | keep utility |

## 5. Proposed Target Runtime Contract

Primary product command:

- `python run_portfolio_review.py`

Default behavior:

- Diagnosis-only Core MVP run.
- No candidate factory.
- No optimizer.
- No full PDF/report export.
- Output profile defaults to `site_api`.
- Source of truth: `{output_dir_final}/analysis_subject/`.

Candidate behavior:

- `python run_portfolio_review.py --candidates equal_weight` is the official one-candidate demo.
- More than one explicit candidate is a product shortlist, not a candidate zoo.
- `--with-candidates`, `--mode full`, and factory profiles are research/advanced.

Product output source of truth:

- Portfolio X-Ray: `{output_dir_final}/analysis_subject/portfolio_xray.json`
  - product keys: `block_2_1_asset_allocation` through `block_2_6_portfolio_weakness_map`
  - legacy `sections.*` and `legacy_summary` are compatibility only
- Stress Lab: `{output_dir_final}/analysis_subject/stress_report.json`
  - Block 3.1: `scenario_library_meta` plus sidecar `scenario_library.json`
  - Block 3.2: `stress_results_v1`
  - Block 3.3: `hedge_gap_analysis_v1`
  - Block 3.4: `current_portfolio_stress_scorecard_v1`
  - `stress_scorecard_v1`, `stress_conclusions`, and `hedge_gap_analysis` are legacy/compatibility.

Default Core MVP diagnostic run must never:

- call `run_optimization.py`;
- read root policy artifacts as product truth;
- run candidate zoo/batch factory;
- emit client mandate, suitability, pass/fail, or optimizer-first behavior in product-facing blocks;
- substitute real cash with `cash_proxy_ticker`;
- refresh PDFs or legacy report bundles unless explicitly requested.

## 6. Session-Based Implementation Plan

### Session 1 — Runtime Entrypoint Inventory and Classification

Objective: create the checked-in audit/plan file and lock all script classifications.

Files likely touched:

- `docs/exec_plans/core_mvp_runtime_integration_and_entrypoint_audit_plan.md`
- optionally `docs/exec_plans/README.md`

Exact tasks:

- Add this audit as the session plan file.
- Re-run script inventory.
- Confirm no scripts were missed.
- Mark default product, one-candidate, research, legacy, deprecated, and test-only paths.

Tests to add/update:

- none unless inventory helpers already exist.

Commands to run:

- `git status --short`
- `Get-ChildItem -File -Filter 'run_*.py'`
- `Get-ChildItem scripts -Recurse -File`
- `python run_portfolio_review.py --dry-run`
- `python run_portfolio_review.py --candidates equal_weight --dry-run`

Acceptance criteria:

- Every discovered runtime script is classified.
- Primary product command is unambiguous.
- No runtime behavior changed.

Rollback / safety notes:

- Revert only the new markdown file if needed.
- Do not move, rename, or delete scripts.

What must NOT be changed:

- runtime code;
- command names;
- generated artifacts.

### Session 2 — Factor Pipeline Boundary Audit and Plan

Objective: document and plan the clean boundary between raw factor diagnostics, Block 2.3, and Block 3.

Files likely touched:

- `docs/exec_plans/core_mvp_runtime_integration_and_entrypoint_audit_plan.md`
- maybe `docs/specs/factor_diagnostics_spec.md` in later implementation

Exact tasks:

- Inventory factor fields written to `stress_report.json`.
- Decide whether to introduce `factor_diagnostics_raw`.
- Plan how `run_report.py` and `run_optimization.py` should share helper code.
- Preserve Block 2.3 adapter-only behavior.

Session 2 notes (implementation intent: **docs + tests only**, no formula or runtime refactor):

- Factor evidence lives in **two places** today:
  - **Stress Lab engine output** (`src/stress.py::run_stress`) carries scenario and historical results, plus a small factor-related surface (`factor_betas` for scenario pnl_by_factor attribution).
  - **Factor diagnostics enrichment** (weekly regressions, Kalman, variance decomposition) is computed in `src/stress_factors.py` and then attached into the exported `stress_report.json` by report/optimizer orchestration (`run_report.py` / `run_optimization.py`), not by `run_stress` itself.

- Inventory: factor-related keys expected in exported `stress_report.json` (and read by Block 2.3 and other diagnostics):
  - Portfolio-level point betas:
    - `factor_betas_5y` (required; weekly OLS over ~260 weeks)
    - `factor_betas_10y` (required; weekly OLS over ~520 weeks)
    - `factor_betas` (legacy alias for `factor_betas_5y`; keep for backward compatibility)
  - Regression inference (must include HAC/Newey-West inference blocks per stress rules):
    - `factor_regression_5y`
    - `factor_regression_10y`
  - Dynamic beta diagnostics:
    - `factor_betas_kalman` (latest betas + status/diagnostics)
  - Variance contribution diagnostics:
    - `factor_variance_decomposition`
  - Data-quality / provenance:
    - `factor_diagnostics_meta` (status/source/missing_factors/aligned observations; minimal structured provenance)
  - Stress engine attribution (scenario-only; produced inside `run_stress`):
    - `factor_betas` (filtered map used by synthetic scenario `pnl_by_factor_pct` attribution)

- Decision: introduce `factor_diagnostics_raw` as a **documented internal contract first**, not a runtime JSON-breaking change.
  - Rationale: it clarifies the shared raw boundary (stress + x-ray both read it), but adding a new top-level object immediately risks subtle drift in legacy exports and tests.
  - Plan: in a later implementation session, define a stable internal dict (e.g. `factor_diagnostics_raw_v1`) that is assembled once and then:
    - exported into `stress_report.json` (while preserving all existing legacy keys listed above),
    - consumed by Block 2.3 adapter without triggering calculations,
    - shared by `run_report.py` and `run_optimization.py` via a helper function (single orchestration point).

- Safe remediation order (future sessions; no code extraction in Session 2):
  - Step A: add `factor_diagnostics_raw_v1` (internal, parallel to legacy keys; contract tests first).
  - Step B: refactor orchestration to a shared helper used by `run_report.py` and `run_optimization.py` (no formula changes; JSON contract preserved).
  - Step C: optionally derive legacy `src/portfolio_xray.py` `sections.factor_exposure` from Block 2.3 adapter to prevent drift (keep legacy surface, but avoid duplicate mapping logic).

Tests to add/update:

- Block 2.3 adapter does not call factor calculation functions.
- Stress Report still contains factor diagnostics.
- Legacy optimizer compatibility remains gated.

Commands to run:

- `python -m pytest tests/test_block_2_3_factor_exposure.py tests/test_factor_diagnostics_wiring.py -q`

Acceptance criteria:

- Shared calculation vs product adapter boundary is written down.
- Duplicated logic is listed with safe remediation order.

Rollback / safety notes:

- Do not extract code in this session unless explicitly asked.

What must NOT be changed:

- factor formulas;
- beta names;
- stress scenario shocks.

### Session 3 — Core MVP Block 1 → 2 → 3 End-to-End Runtime Verification

Objective: verify the canonical portfolio-first diagnostic path with the VOO/QQQ/TLT/GLD/Cash USD example.

Files likely touched:

- tests only, if adding an offline/temporary-output smoke
- audit plan progress notes

Exact tasks:

- Use a temp config/output folder, not root generated artifacts.
- Verify minimal input resolves.
- Verify real cash persists.
- Verify `portfolio_xray.json` Blocks 2.1–2.6.
- Verify `stress_report.json` Blocks 3.1–3.4.
- Verify no optimizer/candidate/default mandate leakage.

Tests to add/update:

- canonical cash E2E smoke with temp output.
- output path stability test.

Commands to run:

- `python -m pytest tests/test_mvp_portfolio_review_materialization.py tests/test_core_mvp_blocks_1_3_boundaries.py -q`
- optional live temp-output run if approved.

Acceptance criteria:

- Canonical example works end-to-end or gaps are explicitly listed.
- Real cash survives full path.

Rollback / safety notes:

- Use temp output only.
- Do not overwrite `config.yml` or root `Main portfolio` manually.

What must NOT be changed:

- generated root artifacts;
- real cash implementation.

### Session 4 — Primary Runtime Contract Cleanup Plan

Objective: align code comments, docs, and tests around the official product runtime.

Files likely touched:

- `docs/product_flow_operator_guide.md`
- `OUTPUTS.md`
- `docs/specs/portfolio_review_workflow_spec.md`
- `README.md`
- runtime mode tests if needed

Exact tasks:

- Correct stale docs saying default/core runs candidate batch.
- State default = diagnosis-only.
- State `--candidates ID` = one selected candidate.
- State `--with-candidates` / `--mode full` = advanced/research.
- Ensure docs point to `analysis_subject/`.

Tests to add/update:

- runtime mode regression tests for default, one candidate, with-candidates, full.

Commands to run:

- `python -m pytest tests/test_runtime_mode_regression_boundaries.py -q`

Acceptance criteria:

- Docs and code agree on default runtime.
- No user-facing doc promotes candidate zoo as Core MVP default.

Rollback / safety notes:

- Docs-only changes; revert docs if wording is wrong.

What must NOT be changed:

- runtime command semantics.

### Session 5 — Legacy Runtime Isolation Plan

Objective: plan how old optimizer/profile/mandate/full report flows are namespaced.

Files likely touched:

- `README.md`
- `OUTPUTS.md`
- `docs/product_flow_operator_guide.md`
- maybe `docs/specs/portfolio_review_workflow_spec.md`

Exact tasks:

- Mark `run_optimization.py`, `run_mvp_workflow.py`, bare `run_report.py`, and root artifacts as legacy.
- Decide whether scripts move later to `scripts/legacy/` or stay with stronger docs.
- Preserve recoverability.
- Remove legacy flows from main quickstart if present.

Tests to add/update:

- docs search regression for forbidden “default optimizer” wording if feasible.

Commands to run:

- `rg -n "run_optimization.py|run_mvp_workflow.py|client_profile|mandate|suitability|core_fast|default" README.md OUTPUTS.md docs`

Acceptance criteria:

- Legacy runtime remains callable but not confused with Core MVP product runtime.

Rollback / safety notes:

- Do not move files in this session unless explicitly approved.

What must NOT be changed:

- optimizer behavior;
- legacy output contracts.

Session 5 implementation status (2026-05-27):

- Completed as documentation isolation only (no runtime/code behavior changes).
- `README.md` command matrix split into primary product runtime vs legacy compatibility runtime.
- `OUTPUTS.md` legacy command matrix now explicitly marks `run_report.py`, `run_optimization.py`, and `run_mvp_workflow.py` as legacy compatibility entrypoints.
- `docs/product_flow_operator_guide.md` now includes an explicit legacy-runtime command row and anti-pattern guidance to avoid starting Core MVP demos from legacy entrypoints.

### Session 6 — Test and Documentation Alignment Plan

Objective: define regression tests and docs updates that keep the runtime clean.

Files likely touched:

- `tests/test_runtime_mode_regression_boundaries.py`
- `tests/test_core_mvp_blocks_1_3_boundaries.py`
- `tests/test_block_2_3_factor_exposure.py`
- docs listed in Session 4/5

Exact tasks:

- Add tests for default no candidates.
- Add tests for Block 2.3 no stress scenario output.
- Add tests for Block 3 no X-Ray contamination.
- Add tests for real cash in canonical input.
- Add docs verification command if the repo has one.

Commands to run:

- `python -m pytest tests/test_block_2_3_factor_exposure.py tests/test_core_mvp_blocks_1_3_boundaries.py tests/test_runtime_mode_regression_boundaries.py -q`

Acceptance criteria:

- Runtime boundary tests fail if default reverts to optimizer/candidate-first behavior.

Rollback / safety notes:

- Keep tests focused; avoid live network dependence.

What must NOT be changed:

- formulas;
- generated artifacts.

Session 6 implementation status (2026-05-27):

- Completed as regression verification + docs verification (no runtime/formula changes).
- Boundary pytest bundle passed:
  - `tests/test_block_2_3_factor_exposure.py`
  - `tests/test_core_mvp_blocks_1_3_boundaries.py`
  - `tests/test_runtime_mode_regression_boundaries.py`
- Documentation verification command executed and passed:
  - `python scripts/verify_docs.py` -> `docs verification: OK`
- Session 6 acceptance retained: default/runtime boundary regressions are now continuously gated by the existing test bundle.

### Session 7 — Final Live Acceptance Plan

Objective: prove the product runtime behaves like clean Core MVP diagnostics.

Files likely touched:

- final audit note under `docs/audits/` if requested
- plan progress/outcomes

Exact tasks:

- Run default product runtime in a controlled output folder.
- Run one-candidate demo.
- Inspect product JSON keys.
- Confirm no candidate zoo by default.
- Confirm no optimizer-first or mandate/suitability leakage.
- Record any remaining legacy exceptions.

Commands to run:

- `python run_portfolio_review.py --dry-run`
- `python run_portfolio_review.py --candidates equal_weight --dry-run`
- targeted pytest bundle from Session 6
- live run only if explicitly approved because it mutates generated outputs.

Acceptance criteria:

- Core MVP E2E path verified or every gap is documented.
- Plan can be closed with evidence.

Rollback / safety notes:

- Prefer temp output folder.
- If live root artifacts are regenerated, report that clearly.

What must NOT be changed:

- runtime behavior without explicit implementation approval.

Session 7 implementation status (2026-05-27):

- Completed as controlled acceptance verification without live artifact mutation.
- Default dry-run verified diagnosis-only runtime and no candidate zoo:
  - `python run_portfolio_review.py --dry-run`
  - observed `Runtime mode: product_diagnosis_only`, `Workflow state: diagnosis_only (candidate_count=0, source=skip_candidates)`.
- One-candidate dry-run verified explicit candidate behavior only:
  - `python run_portfolio_review.py --candidates equal_weight --dry-run`
  - observed `Runtime mode: product_one_candidate`, `Workflow state: one_candidate (candidate_count=1, source=candidate_ids)`.
- Session 6 boundary regression bundle re-run and passed:
  - `python -m pytest tests/test_block_2_3_factor_exposure.py tests/test_core_mvp_blocks_1_3_boundaries.py tests/test_runtime_mode_regression_boundaries.py -q`
  - result: `25 passed`.
- Live canonical E2E executed after explicit approval, isolated to temp output:
  - temporary runtime input: `VOO/QQQ/TLT/GLD/Cash USD` with weights `45/20/15/10/10`.
  - command: `python run_portfolio_review.py` (non-dry-run).
  - isolated output root: `tmp/session07_live/Main portfolio/analysis_subject`.
  - runtime evidence: `Runtime mode: product_diagnosis_only`, `Workflow state: diagnosis_only (candidate_count=0, source=skip_candidates)`.
- Product block verification on live temp artifacts:
  - Block 2 presence in `portfolio_xray.json`: `block_2_1` through `block_2_6` all present.
  - Block 3 presence in `stress_report.json`: `scenario_library_meta`, `stress_results_v1`, `hedge_gap_analysis_v1`, `current_portfolio_stress_scorecard_v1` all present.
  - no candidate-zoo side effects in subject folder (`candidate_factory_manifest.json` absent).
  - forbidden-key leakage check in product blocks returned empty findings for both Block 2 and Block 3.
- Recorded residual warnings from live run (non-blocking for this acceptance, but visible):
  - `Macro regime diagnostics failed: name 'logger' is not defined`.
  - `Factor beta*shock OOS diagnostics failed: Length mismatch`.
  - repeated historical yfinance availability warnings for early ranges (`VOO/TLT/GLD/USD/DBC`).

## 7. Test Strategy

Tests must prove:

- minimal input is enough for Block 1 → 2 → 3;
- real cash works end-to-end and is not replaced by `cash_proxy_ticker`;
- Block 2.3 receives factor diagnostics without becoming Stress Lab;
- Block 3 uses stress outputs without contaminating Portfolio X-Ray product blocks;
- no candidate zoo runs by default;
- no optimizer-first behavior runs by default;
- no client mandate / pass-fail / suitability logic leaks into product-facing default runtime;
- primary runtime output paths are stable;
- legacy runtimes are gated and documented as legacy/advanced.

Core commands:

- `python -m pytest tests/test_block_2_3_factor_exposure.py`
- `python -m pytest tests/test_core_mvp_blocks_1_3_boundaries.py`
- `python -m pytest tests/test_runtime_mode_regression_boundaries.py`
- `python -m pytest tests/test_mvp_portfolio_review_materialization.py`

## 8. Acceptance Checklist

- [x] Factor pipeline boundary understood.
- [x] Block 2.3 / Block 3 product separation audited.
- [x] Primary runtime command identified.
- [x] Runtime scripts inventoried.
- [x] Legacy runtimes classified.
- [x] Core MVP E2E path dry-run verified.
- [x] Canonical cash input validated without live mutation.
- [x] Tests planned.
- [x] Docs plan created.
- [x] No code implemented yet.
- [x] Markdown audit file written to repository after Plan Mode ends.
- [x] Live canonical E2E run performed in temp output or approved generated-output folder.

## 9. Implementation Protocol

When implementation begins, execute this plan session by session. If the user says "start the runtime plan" or "begin the runtime plan", perform only Session 1 unless explicitly instructed otherwise. After each session, stop, summarize changes, report tests, and wait for the next instruction. Do not jump to the next session automatically.

