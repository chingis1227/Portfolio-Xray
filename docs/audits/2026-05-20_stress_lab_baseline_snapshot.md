# Stress Lab Baseline Snapshot

Date: 2026-05-20

Purpose: fixed baseline for Stress Test Lab changes in the post-audit roadmap wave.
Session: 00 (Scope Freeze & Baseline Snapshot).
Policy for this chat: no stress-logic refactor, baseline only.

## Baseline commands

- `python run_report.py --materialize-analysis-subject`
- `python run_stress_variant.py --variant main`
- `python -m pytest tests/test_stress_scorecard_contract.py tests/test_stress_hedge_gap_contract.py tests/test_stress_scenario_coverage_contract.py tests/test_stress_synthetic_assumptions_contract.py tests/test_stress_simulator_contract.py tests/test_stress_mandate_pass.py tests/test_stress_scenario_analytics.py tests/test_stress_historical_fields.py tests/test_stress_covariance_taxonomy.py -q`
- `python scripts/verify_docs.py`

## Baseline artifacts to compare after each session

- `{output_dir_final}/analysis_subject/stress_report.json`
- `{output_dir_final}/analysis_subject/stress_commentary.txt`
- `{output_dir_final}/analysis_subject/results_csv/stress_scenario_analytics_summary.csv`
- `{output_dir_final}/analysis_subject/scenario_library.json`
- `{output_dir_final}/analysis_subject/scenario_library_normalized.json`
- `{output_dir_final}/analysis_subject/snapshot_10y.json`

Current output_dir_final in this baseline run: `Main portfolio/analysis_subject`.

## Baseline snapshot fingerprints (Session 00)

- `stress_report.json`: size `2040157`, sha256 `afeea2b75d3feba06215679b05f37135ebebc15eab255861a2f28edf6dfd62fd`
- `stress_commentary.txt`: size `26875`, sha256 `26ba597000e87effcf582dfa9c5bdbb5f24db60c01bd5fbb71f7d63ebf95ae13`
- `results_csv/stress_scenario_analytics_summary.csv`: size `3201`, sha256 `d8c8a2f00da009c7b3502dd145b6cb9ae73efd664de08af8fa91f4a25d85a3cf`
- `scenario_library.json`: size `183286`, sha256 `7330d8dc804e56a54d32590ba1568ede2ee7298d44008344f314d16d2b54c5c5`
- `scenario_library_normalized.json`: size `295064`, sha256 `1f7be322810e021a8d59f0d4fe9580f81bbc333606edb7a55790ab2a3c34e423`
- `snapshot_10y.json`: size `54125`, sha256 `7d81d7f8dbdba1d0d80b0844d9c1688a75d3edebfab70f89d226f7cdb7bcbe1b`

## Baseline contract checklist

1. `stress_report.status`, `diagnostic_codes`, `fail_reason_code`, `failed_scenario`.
2. `scenario_results[*]` contains:
   - `portfolio_pnl_pct`, `pnl_by_asset_pct`, `pnl_by_factor_pct`
   - `top3_loss_assets`
   - `top1_rc_asset`, `top3_rc_sum_pct`
3. `historical_results[*]` exists for all canonical episodes in `src/stress.py`.
4. `factor_betas_5y`, `factor_betas_10y`, `factor_regression_5y`, `factor_regression_10y`.
5. `factor_betas_rolling_summary`, `factor_betas_stability`, `factor_beta_shock_oos`.
6. `stress_scenario_analytics` block and CSV exports.
7. `scenario_library_meta` and `scenario_library_normalized_meta`.
8. `snapshot_10y.stress_suite_results` mirrors stress status and scenarios.
9. `stress_scorecard_v1`: `overall_confidence`, `synthetic_scenarios[]` with `loss_severity` and `beta_confidence`.
10. `stress_conclusions`: `overall_confidence`, worst outcomes with `loss_severity`, `hedge_gap_status`.
11. `historical_episode_paths`: path-level replay rows with quality metadata; CSV export `results_csv/crisis_replay_{episode}.csv`.
12. `hedge_gap_analysis`: `status`, `gap_detected`, `worst_scenario_portfolio_pnl_pct`, `hedge_assets_negative_in_worst_scenario`.
13. Simulator API (no UI): `simulate_custom_shock` / `shock_vector_from_scenario` in `src/stress.py`; contract in `stress_testing_spec.md` §12.3; tests in `tests/test_stress_simulator_contract.py`.

## Session 00 checklist result (captured)

- `stress_report.status = DIAG_ATTENTION`
- `factor_regression_5y`: present
- `factor_regression_10y`: present
- `factor_betas_rolling_summary`: present
- `factor_betas_stability`: present
- `factor_beta_shock_oos`: present
- `stress_scenario_analytics`: present
- `scenario_results` length: `8`
- `historical_results` length: `5`
- `scenario_library_meta`: present
- `scenario_library_normalized_meta`: present

## Compare command template (next sessions)

Use this single command after each completed session to compare baseline integrity quickly:

`python -c "from pathlib import Path; import hashlib; base=Path('Main portfolio/analysis_subject'); files=['stress_report.json','stress_commentary.txt','results_csv/stress_scenario_analytics_summary.csv','scenario_library.json','scenario_library_normalized.json','snapshot_10y.json']; print('\\n'.join(f'{f}|{hashlib.sha256((base/f).read_bytes()).hexdigest()}' for f in files if (base/f).exists()))"`

## Known gaps at baseline

- ~~No unified `stress_scorecard_v1` / `stress_conclusions` contract in downstream consumers.~~ Addressed in Session 02 (spec §12.1, builders in `src/stress.py`, commentary/scorecard tests).
- ~~Historical stress was aggregate-focused; no canonical path-level replay artifact.~~ Addressed in Session 03 (`historical_episode_paths` in `src/stress.py`, CSV export in `run_report.py`, `tests/test_stress_historical_fields.py`).
- ~~Hedge gap logic was indirect in X-Ray, not explicit in stress contract.~~ Addressed in Session 04 (`_build_hedge_gap_analysis` in `src/stress.py`, evidence fields in `hedge_gap_analysis`, `tests/test_stress_hedge_gap_contract.py`).
- ~~Scenario coverage did not include 2023 banking historical episode or dedicated USD/commodity synthetic rows.~~ Addressed in Session 05 (dedicated taxonomy calibration for `usd_shock` / `commodity_shock` in `src/stress_covariance_taxonomy.py`, canonical id contract in `tests/test_stress_scenario_coverage_contract.py`, X-Ray `WEAKNESS_SCENARIO_MAP` wiring).
- ~~No programmatic What Happens If / custom-shock simulator API.~~ Addressed in Session 09 (`simulate_custom_shock`, `shock_vector_from_scenario`, `tests/test_stress_simulator_contract.py`, spec §12.3).

## Session 10 wave closure (2026-05-20)

Scope: final verification and documentation pack only (no new stress logic).

### Verification commands (passed)

- Stress Lab regression bundle: **70 passed** (see `docs/exec_plans/2026-05-20_stress_lab_post_audit_roadmap.md` Concrete Steps for the exact `pytest` file list).
- `python scripts/verify_docs.py`: **OK**

### Documentation pack

- `TESTING.md`: Stress Lab wave regression bundle and artifact refresh commands.
- `docs/exec_plans/README.md`: plan marked **Completed**; active pointer moved off this wave.
- `CHANGELOG.md`: Stress Lab Sessions 01-10 summary entry.
- Stale test fix: `tests/test_portfolio_commentary.py` X-Ray heading/disclaimer assertions match `format_portfolio_xray_commentary`.

### Baseline hash note

Session 10 did **not** re-run `run_report.py` in this closure chat (no `Main portfolio/analysis_subject/` artifacts on disk). Session 00 fingerprints remain the regression reference until the next representative materialization run; after refresh, update the hash table in this file using the compare command in **Compare command template**.

### Wave status

Stress Lab post-audit roadmap **Sessions 00-10: complete**. All baseline known gaps (items 9-13) are closed in code/spec/tests per session notes above.
