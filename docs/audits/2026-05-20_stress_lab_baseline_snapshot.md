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
14. `snapshot_10y.stress_suite_results`: `historical_methodology`, `crisis_replay_summary` (no daily rows), `failed_scenario`, full `hedge_gap_analysis` / `conclusions` mirrors.
15. `candidate_comparison` per-candidate `stress`: `historical_methodology`, `crisis_replay_summary`, `hedge_gap_analysis`, `conclusions` from snapshot and/or `stress_report.json`.
16. `stress_commentary.txt`: methodology line, per-episode `return_method`, crisis replay v2 recovery/top-loss lines, hedge `by_risk_type` summary.
17. Downstream integration tests: `tests/test_stress_downstream_integration.py`.

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

## Post-audit wave closure (Sessions 00–10, 2026-05-20)

Scope: [Stress Lab Post-Audit Roadmap](../exec_plans/2026-05-20_stress_lab_post_audit_roadmap.md) — scorecard, replay, hedge gap, coverage, simulator API.

- Post-audit regression bundle: **70 passed** (see that ExecPlan Concrete Steps).
- Known gaps (items 9–13 in checklist above): closed in Sessions 01–10 of the post-audit wave.

## Phase 13 governance closure (Session 11, 2026-05-20)

Scope: [Stress Lab Methodology Governance Plan](../exec_plans/2026-05-20_stress_lab_methodology_governance_plan.md) Sessions 00–11 — verification and documentation only (no new stress logic).

### Verification commands (passed)

- Stress Lab governance bundle ([TESTING.md](../../TESTING.md) § Stress Lab Governance Wave Bundle): **90 passed**
  (`--basetemp=tmp/pytest_gov_s11`).
- `python scripts/verify_docs.py`: **OK**

### Governance gap closure (G1–G10)

| Gap ID | Topic | Status after Sessions 01–11 |
| --- | --- | --- |
| G1 | Worst historical by pnl vs max_dd | **Closed** Session 01 (`RM-952`) |
| G2 | Historical realized vs proxy boundary | **Closed** Session 02 (`RM-953`) |
| G3 | Hedge N/A when no labels | **Closed** Session 03 (`RM-954`) |
| G4 | Factor drivers in conclusions | **Closed** Session 04 (`RM-955`) |
| G5 | Hedge gap by risk type | **Closed** Session 05 (`RM-956`) |
| G6 | Crisis replay v2 | **Closed** Session 06 (`RM-957`) |
| G7 | stress_lab_layer_spec handoff | **Closed** Session 07 (`RM-958`) |
| G8 | crypto/vol synthetic in run_stress | **Deferred** Session 08 (`RM-959`, DEC-2026-05-20-002) |
| G9 | custom_shock_runs artifact | **Closed** Session 09 (`RM-960`) |
| G10 | Downstream integration | **Closed** Session 10 (`RM-961` part 1) |

Checklist items **14–17** (downstream mirrors, comparison `stress`, commentary lines, integration tests) verified via governance pytest bundle and Session 10 implementation.

### Baseline hash note

Session 11 did **not** re-run `run_report.py` (no `Main portfolio/analysis_subject/` on disk). Session 00
fingerprints in **Baseline snapshot fingerprints** remain the regression reference until the next
representative materialization; after refresh, update hashes using **Compare command template**.

### Documentation pack

- This file: Phase 13 closure section and G1–G10 table.
- [TESTING.md](../../TESTING.md): governance wave bundle (Sessions 01–11).
- [docs/exec_plans/README.md](../exec_plans/README.md): governance plan **Completed**; active pointer updated.
- [docs/ROADMAP.md](../ROADMAP.md): Phase 13 **Done** (`RM-951`–`RM-961`).
- [CHANGELOG.md](../../CHANGELOG.md): Session 11 closure entry.

### Wave status

Stress Lab methodology governance **Sessions 00–11: complete**. Block 3 is audit-grade for handoff per
[methodology map](2026-05-20_stress_lab_methodology_map.md) final verdict.
