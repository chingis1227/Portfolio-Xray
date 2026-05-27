# Core MVP Blocks 1–3 Fixture Matrix Audit

Date: 2026-05-27

Scope: Validate Core MVP Blocks 1–3 (Input, Portfolio X-Ray, Stress Lab) across seven realistic fixture portfolios using materialized `analysis_subject` outputs under `output/fixture_matrix_runs/<fixture_id>/analysis_subject/`.

Evidence sources:
- `output/fixture_matrix_runs/step2_run_summary.json`
- `output/fixture_matrix_runs/step3_block1_validation.json`
- `output/fixture_matrix_runs/step4_block2_validation.json`
- `output/fixture_matrix_runs/step5_block3_validation.json`
- `output/fixture_matrix_runs/step6_legacy_contamination_validation.json`

---

## A. Executive Summary

Final product verdict for the requested question:

**Can Blocks 1–3 be trusted as the Core MVP diagnostic foundation across realistic portfolios?**  
**Yes, with limitations**

Rationale:
- Block 1 validation passes on all fixtures (7/7), including taxonomy validation and real-cash handling checks.
- Block 2 and Block 3 are consistently present, but remain partial on all fixtures (7/7 partial for each block), mainly due to known incompleteness in factor/episode subcomponents.
- Step 6 no longer reports product-facing active contamination (`product_facing_active_contamination = 0` on all fixtures after fix); remaining findings are legacy-compat scoped or harmless null fields.
- Entry-point safety preflight remains `ok` (no forbidden optimizer/candidate/mandate invocation patterns detected in `run_materialize_analysis_subject_report`).

---

## B. Run Scope, Inputs, and Output Folders

Fixture run roots (all under `analysis_subject/`):
- `output/fixture_matrix_runs/fx1_diversified_balanced/analysis_subject/`
- `output/fixture_matrix_runs/fx2_equity_growth_heavy/analysis_subject/`
- `output/fixture_matrix_runs/fx3_duration_defensive/analysis_subject/`
- `output/fixture_matrix_runs/fx4_inflation_sensitive/analysis_subject/`
- `output/fixture_matrix_runs/fx5_cash_heavy_conservative/analysis_subject/`
- `output/fixture_matrix_runs/fx6_pseudo_diversified_risk_on/analysis_subject/`
- `output/fixture_matrix_runs/fx7_mixed_10_holdings/analysis_subject/`

Step 2 run mode summary:
- All seven fixtures were present and recognized.
- Current materialization run used `skipped_existing` for all fixtures (existing outputs reused).

---

## C. Fixture Matrix (Blocks 1–3 + Step 6 Rollup)

| Fixture | Block 1 (Step 3) | Block 2 (Step 4) | Block 3 (Step 5) | Step 6 contamination | Overall |
| --- | --- | --- | --- | --- | --- |
| fx1_diversified_balanced | ok | partial | partial | partial | partial |
| fx2_equity_growth_heavy | ok | partial | partial | partial | partial |
| fx3_duration_defensive | ok | partial | partial | partial | partial |
| fx4_inflation_sensitive | ok | partial | partial | partial | partial |
| fx5_cash_heavy_conservative | ok | partial | partial | partial | partial |
| fx6_pseudo_diversified_risk_on | ok | partial | partial | partial | partial |
| fx7_mixed_10_holdings | ok | partial | partial | partial | partial |

Aggregate counts:
- Step 3: `ok=7`, `partial=0`, `failed=0`
- Step 4: `ok=0`, `partial=7`, `failed=0`
- Step 5: `ok=0`, `partial=7`, `failed=0`
- Step 6 (post-fix rerun): `ok=0`, `partial=7`, `failed=0`

---

## D. Block 1 Findings (Input Layer)

Observed status:
- All fixtures passed Core MVP input checks with no hard errors.
- Ticker taxonomy mapping succeeded for all non-cash instruments.
- Real-cash behavior (`Cash USD`) is correctly represented in fixtures that include it (`fx1`, `fx5`, `fx7`):
  - appears in `real_cash_holdings`
  - uses `real_cash_return_assumption="zero_return_zero_volatility_no_price_download"`
  - remains distinct from cash proxy ticker.

Limitations:
- Download-proof confirmation via run logs is incomplete for several fixtures (`run_log_checked=false`), so direct log-based exclusion evidence is uneven.
- In `fx6`, fixture ticker drift is visible vs original plan intent (`XLK` observed in validation mapping), but taxonomy validity remains intact.

---

## E. Block 2 Findings (Portfolio X-Ray)

Contract presence:
- All required Block 2 keys are present across all fixtures:
  - `block_2_1_asset_allocation`
  - `block_2_2_portfolio_metrics`
  - `block_2_3_factor_exposure`
  - `block_2_4_hidden_exposure`
  - `block_2_5_risk_budget_view`
  - `block_2_6_portfolio_weakness_map`

Common partial drivers:
- `block_2_3_factor_exposure` partial on all fixtures:
  - `factor_betas_10y` missing `beta_credit` (5Y available, 10Y partial).
  - Kalman current beta unavailable (`kalman_module_not_available`).
- `block_2_6_portfolio_weakness_map` partial on all fixtures.

Separation check:
- No scenario-loss leakage detected inside Block 2.3 (`stress_leakage_keys=[]`, separation flag true).

---

## F. Factor Diagnostics (Block 2.3)

Cross-fixture factor diagnostics rollup:
- 5Y factor betas: available across fixtures.
- 10Y factor betas: partial across fixtures due to missing `beta_credit`.
- Significance/inference metadata: present (`significance_outputs_present=true`) in all fixtures.
- Variance contribution block: available and method reported (`r2_scaled_factor_rc_plus_residual`).
- Kalman module: unavailable in all fixtures (`kalman_module_not_available`).

Interpretation:
- Factor exposure diagnostics are usable but incomplete for long-horizon credit sensitivity and live-drift beta tracking.
- This prevents full acceptance of Block 2 factor diagnostics as fully production-complete.

---

## G. Block 3 Findings (Stress Lab)

Contract presence:
- Required stress keys are present in all fixtures:
  - `scenario_library_meta`
  - `stress_results_v1`
  - `hedge_gap_analysis_v1`
  - `current_portfolio_stress_scorecard_v1`
- `scenario_library` sidecar presence is confirmed for all fixtures.

Scenario coverage:
- Synthetic IDs: full coverage (8/8) on all fixtures.
- Historical IDs: full presence (5/5) on all fixtures, but availability differs by episode maturity/history.

Common partial drivers:
- `recession_severe` synthetic often partial due to missing hedge-gap coverage ratio fields.
- Historical `dotcom` and `2008` frequently unavailable with explicit insufficient-history diagnostics.
- Historical factor attribution availability is mixed by fixture/episode.

Interpretation:
- Stress block behaves as expected for heterogeneous history depth, but not all scenario outputs are decision-complete across all fixtures.

---

## H. Legacy Contamination Scan and Entrypoint Preflight

Entrypoint preflight:
- Status: `ok`
- No forbidden candidate/compare/optimizer call tokens detected in `run_materialize_analysis_subject_report`.
- No mandate/suitability/pass-fail identifiers detected by preflight rule set.

Contamination scan (exact-key only) summary:
- All fixtures: `partial` (no active contamination; legacy/null findings only).
- Per fixture classification counts are identical:
  - `product_facing_active_contamination = 0`
  - `legacy_compat_only = 2`
  - `harmless_null_legacy_field = 27`

Post-fix contamination classification patterns:
- `run_metadata.json`
  - `input_assumptions.field_tiers.registry.client_profile` remains present but is now under explicit non-product scope and classified as `legacy_compat_only`.
- `output_manifest.json`
  - candidate/comparison/decision artifact keys are not published as active paths in product-facing generated/discovery sections for analysis_subject site_api runs.

Interpretation:
- FXM-001 and FXM-002 are resolved for Core MVP Blocks 1–3 diagnosis-only/site_api surface.
- Remaining partial status is driven by documented P1/P2/P3 limitations, not by active product-facing contamination.

---

## I. Prioritized Issue Register (P0–P3)

| priority | issue_id | fixture_id | block | path | symptom | likely cause | next action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P0 | FXM-001 | all | Step6 / Output surface | `output/fixture_matrix_runs/<fixture_id>/analysis_subject/output_manifest.json` | Active `candidate_launchpad_json` appeared in product-facing manifest paths for a Blocks 1–3 run (pre-fix). | `site_api` manifest contract exported product bundle candidate key paths for diagnosis outputs. | **Resolved (2026-05-27):** strict analysis_subject site_api/core_json manifest gating suppresses candidate/comparison/decision artifact keys from product-facing active paths. |
| P0 | FXM-002 | all | Step6 / Block1 disclosure | `output/fixture_matrix_runs/<fixture_id>/analysis_subject/run_metadata.json` (`input_assumptions.field_tiers.registry.client_profile`) | Active `client_profile` registry value was detected as product-facing contamination (pre-fix). | Field-tier registry was treated as product-facing payload by contamination contract. | **Resolved (2026-05-27):** deferred registry is now explicitly scoped non-product (`_scope.product_surface=false`) for Core MVP profile. |
| P1 | FXM-003 | all | Block2.3 | `output/fixture_matrix_runs/<fixture_id>/analysis_subject/portfolio_xray.json` (`block_2_3_factor_exposure`) | `factor_betas_10y` partial due to missing `beta_credit`; Kalman beta unavailable. | Incomplete long-window factor diagnostics and unavailable Kalman dependency/module path. | Complete 10Y factor key coverage for `beta_credit`; gate or implement Kalman module with explicit availability policy. |
| P1 | FXM-004 | all | Block3 synthetic stress | `output/fixture_matrix_runs/<fixture_id>/analysis_subject/stress_report.json` (`stress_results_v1.synthetic_scenarios.recession_severe`) | `recession_severe` often partial due to missing hedge-gap coverage fields. | Hedge gap linkage not fully populated for severe synthetic scenario mapping. | Ensure `hedge_gap_analysis_v1` linkage and coverage ratio computation are emitted for all synthetic scenarios, including `recession_severe`. |
| P2 | FXM-005 | fx1,fx5,fx7 | Block2 with real cash | `output/fixture_matrix_runs/<fixture_id>/analysis_subject/portfolio_xray.json` warnings | Real cash appears as 0% return contribution with synthetic taxonomy warnings. | Current real-cash policy intentionally excludes proxy substitution; warnings are expected but noisy for product UX. | Keep model behavior unchanged; improve warning wording/classification to separate expected policy behavior from degradations. |
| P2 | FXM-006 | all | Block3 historical episodes | `output/fixture_matrix_runs/<fixture_id>/analysis_subject/stress_report.json` (`dotcom`,`2008`) | Historical scenarios present but often unavailable due to insufficient history (`episode_metrics_missing`). | Young ETF history and episode data depth constraints. | Preserve explicit unavailable diagnostics; optionally add portfolio-age gating metadata in report layer to pre-announce expected unavailability. |
| P3 | FXM-007 | fx1,fx5 | Block1 evidence trace | `output/fixture_matrix_runs/step3_block1_validation.json` (`run_log_checked=false`) | Download-exclusion evidence via run logs is incomplete in some fixtures. | Runs reused existing outputs (`skipped_existing`), so per-fixture materialize logs were absent. | Re-run fixture matrix without `--skip-existing` when collecting final acceptance evidence pack. |

---

Conclusion:
- Blocks 1–3 show strong structural coverage and useful diagnostics across realistic fixtures.
- P0 blockers (`FXM-001`, `FXM-002`) are resolved and Step 6 no longer reports active contamination.
- Final verdict can be upgraded to **Yes, with limitations**; remaining limitations are P1/P2/P3 and remain documented unchanged.
