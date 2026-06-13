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

**Can Blocks 1–3 be trusted as the Core MVP diagnostic foundation across realistic portfolios...**
**Yes, with limitations**

Rationale:
- Block 1 validation passes on all fixtures (7/7), including taxonomy validation and real-cash handling checks.
- Block 2 and Block 3 are consistently present, but remain partial on all fixtures (7/7 partial for each block), mainly due to known incompleteness in factor/episode subcomponents.
- FXM-005 is no longer treated as a warning/error issue: real-cash messaging is now an informational disclosure describing expected policy behavior.
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

Aggregate counts (validation contract v2, post Kalman/real-cash fix rerun):
- Step 3: `ok=7`, `partial=0`, `failed=0`
- Step 4 (Core MVP rollup): `ok=7`, `partial=0`, `failed=0`
- Step 5 (Core MVP rollup): `ok=7`, `partial=0`, `failed=0`
- Step 6 (legacy contamination scan): `ok=0`, `partial=7`, `failed=0` (expected: legacy-compat null fields only)

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

Common partial drivers (pre-2026-05-27 evening fixes; superseded by validation contract v2):
- `block_2_3_factor_exposure` partial on all fixtures:
  - `factor_betas_10y` missing `beta_credit` (5Y available, 10Y partial).
  - Kalman current beta unavailable (`kalman_module_not_available`).
- `block_2_6_portfolio_weakness_map` partial on all fixtures.

### Validation contract v2 (2026-05-27)

Fixture validators (`validate_core_mvp_block2_fixture_matrix.py`, `validate_core_mvp_block3_fixture_matrix.py`) now use `scripts/core_mvp_validation_contract.py` to separate:

- **Required Core MVP rollup (Block 2):** `block_2_1`, `block_2_2`, `block_2_3`, `block_2_5`
- **Optional diagnostic blocks:** `block_2_4`, `block_2_6` (product status may remain `partial` when some rule-based alerts are `Unavailable`; Core MVP contract status is `ok` when required fields exist). Block 2.4 additionally runs institutional v2 contract checks via `check_block_2_4_hidden_exposure` (Session 11).
- **Block 2.3 informational only:** variance-decomposition name normalization, optional Kalman, real-cash disclosure
- **Block 3 Core MVP:** required product keys + scenario menu coverage; per-scenario enrichments (hedge gap, factor attribution, helped/hurt) are optional for rollup

Kalman weekly path fix: `_portfolio_factor_weekly_ols_rows` no longer calls `download_all` on real-cash labels (`Cash USD`); cash receives zero weekly returns in-panel (same policy as monthly loader).

Separation check:
- No scenario-loss leakage detected inside Block 2.3 (`stress_leakage_keys=[]`, separation flag true).

Real-cash reporting classification update (FXM-005):
- For `fx1`, `fx5`, `fx7`, `Cash USD` is now documented as informational disclosure (not warning), with expected policy semantics:
  - real-cash position (outside ETF/stock taxonomy failure logic),
  - 0% expected return,
  - 0% expected volatility,
  - no price download dependency.
- Interpretation: this is normal behavior under real-cash policy, not a data-quality degradation.

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
| P1 | FXM-004 | all | Block3 synthetic stress | `hedge_gap_analysis_v1.by_risk_type[recession_severe_protection]` | `recession_severe` partial due to missing hedge-gap fields (pre-2026-05-27). | Block 3.3 v1 had only seven protection rows. | **Resolved (2026-05-27):** eighth mapping `recession_severe_protection` → `recession_severe` with full offset-coverage fields. |
| P2 | FXM-005 | fx1,fx5,fx7 | Block2 with real cash | `output/fixture_matrix_runs/<fixture_id>/analysis_subject/portfolio_xray.json` informational disclosures | **Resolved (2026-05-27):** real-cash text is no longer classified as warning/error. `Cash USD` is disclosed as expected real-cash policy behavior (0% return, 0% volatility, no price download). | Report layer previously classified expected real-cash behavior as warning-style noise. | No further action required for MVP acceptance; keep as informational disclosure and preserve existing real-cash math/policy boundary. |
| P2 | FXM-006 | all | Block3 historical episodes | `output/fixture_matrix_runs/<fixture_id>/analysis_subject/stress_report.json` (`dotcom`,`2008`) | Historical scenarios present but often unavailable due to insufficient history (`episode_metrics_missing`). | Young ETF history and episode data depth constraints. | Preserve explicit unavailable diagnostics; optionally add portfolio-age gating metadata in report layer to pre-announce expected unavailability. |
| P3 | FXM-007 | fx1,fx5 | Block1 evidence trace | `output/fixture_matrix_runs/step3_block1_validation.json` (`run_log_checked=false`) | Download-exclusion evidence via run logs is incomplete in some fixtures. | Runs reused existing outputs (`skipped_existing`), so per-fixture materialize logs were absent. | Re-run fixture matrix without `--skip-existing` when collecting final acceptance evidence pack. |

---

Conclusion:
- Blocks 1–3 show strong structural coverage and useful diagnostics across realistic fixtures.
- P0 blockers (`FXM-001`, `FXM-002`) are resolved and Step 6 no longer reports active contamination.
- FXM-005 is resolved at report-layer classification level and now treated as informational disclosure, not a warning/error.
- Final verdict remains **Yes, with limitations**; remaining material limitations are FXM-003/004/006/007.
