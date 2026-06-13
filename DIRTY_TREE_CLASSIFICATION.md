# Dirty Working Tree Classification

Date: 2026-05-25

## Executive Summary

The working tree is heavily dirty after the Portfolio MRI code-migration sessions. No files are staged (`git diff --cached --name-only` returned no paths). The dirty tree contains a clear migration set, supporting docs/tests, many generated portfolio/report artifacts, config/environment changes, and unrelated pre-existing data-provider/cache/source changes.

Recommended action: do **not** use `git add -A`. First review and stage only the explicit migration code/docs/tests listed below. Keep generated outputs, config/environment changes, provider work, logs, and pycache out of the migration commit unless a human explicitly approves a separate commit.

## Commands Run

- `git status --short`
- `git diff --stat`
- `git diff --name-only`
- `git diff --cached --name-only`

## Command Output Summary

- Dirty tracked/untracked entries: 352
- Staged files: 0
- `git diff --cached --name-only`: empty

### git diff --stat

```text
OUTPUTS.md                                         |    23 +-
 SPEC.md                                            |    16 +-
 config.yml                                         |     1 +
 config.yml.example                                 |     1 +
 docs/audits/README.md                              |     5 +
 docs/exec_plans/README.md                          |     6 +
 docs/specs/README.md                               |     8 +
 docs/specs/candidate_factory_spec.md               |    28 +
 docs/specs/portfolio_review_workflow_spec.md       |    25 +
 .../baseline_weights_metadata.json                 |    20 +-
 hierarchical risk parity portfolio/commentary.txt  |   121 +-
 .../data_policy.json                               |     2 +-
 .../drawdown_structure_3y.json                     |     8 +-
 .../portfolio_xray.json                            |  1329 +-
 .../regime_factor_analytics_summary.json           |    34 +-
 .../regime_label_quality_summary.json              |    22 +-
 .../regime_portfolio_metrics_summary.json          |    24 +-
 hierarchical risk parity portfolio/report.html     |   201 +-
 hierarchical risk parity portfolio/report.txt      |   316 +-
 .../rolling_factor_betas.html                      |     2 +-
 .../rolling_factor_betas_10y.png                   |   Bin 206225 -> 207956 bytes
 .../rolling_factor_betas_3y.png                    |   Bin 231551 -> 232473 bytes
 .../rolling_factor_betas_5y.png                    |   Bin 206710 -> 207364 bytes
 .../run_metadata.json                              |    50 +-
 .../scenario_library.json                          |  5375 +-
 .../scenario_library_normalized.json               |  8910 ++-
 .../snapshot_10y.json                              |  1580 +-
 .../snapshot_3y.json                               |  1600 +-
 .../snapshot_5y.json                               |  1584 +-
 .../snapshot_assets.json                           |     2 +-
 .../snapshot_index.json                            |     2 +-
 .../stress_commentary.txt                          |   351 +-
 .../stress_report.json                             | 74148 +------------------
 hierarchical risk parity portfolio/summary.json    |    49 +-
 hierarchical risk parity portfolio/summary.txt     |     2 +-
 hierarchical risk parity portfolio/weights.json    |    16 +-
 hierarchical risk parity portfolio/weights.txt     |     8 +-
 .../baseline_weights_metadata.json                 |   380 +-
 .../commentary.txt                                 |   124 +-
 .../data_policy.json                               |     2 +-
 .../drawdown_structure_10y.json                    |     6 +-
 .../drawdown_structure_5y.json                     |     2 +-
 .../portfolio_xray.json                            |  1375 +-
 .../regime_factor_analytics_summary.json           |    31 +-
 .../regime_label_quality_summary.json              |    22 +-
 .../regime_portfolio_metrics_summary.json          |    24 +-
 .../report.html                                    |   201 +-
 .../report.txt                                     |   321 +-
 .../rolling_factor_betas.html                      |     2 +-
 .../rolling_factor_betas_10y.png                   |   Bin 210993 -> 211537 bytes
 .../rolling_factor_betas_3y.png                    |   Bin 221217 -> 221668 bytes
 .../rolling_factor_betas_5y.png                    |   Bin 213402 -> 213593 bytes
 .../run_metadata.json                              |    59 +-
 .../scenario_library.json                          |  5381 +-
 .../scenario_library_normalized.json               |  8842 ++-
 .../snapshot_10y.json                              |  1666 +-
 .../snapshot_3y.json                               |  1656 +-
 .../snapshot_5y.json                               |  1666 +-
 .../snapshot_assets.json                           |     2 +-
 .../snapshot_index.json                            |     2 +-
 .../stress_commentary.txt                          |   355 +-
 .../stress_report.json                             | 73730 +-----------------
 .../summary.json                                   |   411 +-
 .../summary.txt                                    |     8 +-
 .../weights.json                                   |    14 +-
 .../weights.txt                                    |     8 +-
 .../baseline_weights_metadata.json                 |   336 +-
 minimum cvar constrained portfolio/commentary.txt  |   115 +-
 .../data_policy.json                               |     2 +-
 .../portfolio_xray.json                            |  1264 +-
 .../regime_factor_analytics_summary.json           |    18 +-
 .../regime_label_quality_summary.json              |    22 +-
 .../regime_portfolio_metrics_summary.json          |    24 +-
 minimum cvar constrained portfolio/report.html     |   183 +-
 minimum cvar constrained portfolio/report.txt      |   238 +-
 .../rolling_factor_betas.html                      |     2 +-
 .../rolling_factor_betas_10y.png                   |   Bin 206236 -> 206232 bytes
 .../rolling_factor_betas_3y.png                    |   Bin 240387 -> 240516 bytes
 .../rolling_factor_betas_5y.png                    |   Bin 213741 -> 213804 bytes
 .../run_metadata.json                              |    46 +-
 .../scenario_library.json                          |  5329 +-
 .../scenario_library_normalized.json               |  8796 ++-
 .../snapshot_10y.json                              |  1508 +-
 .../snapshot_3y.json                               |  1508 +-
 .../snapshot_5y.json                               |  1508 +-
 .../snapshot_assets.json                           |     2 +-
 .../snapshot_index.json                            |     2 +-
 .../stress_commentary.txt                          |   354 +-
 .../stress_report.json                             | 74044 +-----------------
 minimum cvar constrained portfolio/summary.json    |   351 +-
 minimum cvar constrained portfolio/summary.txt     |     2 +-
 .../baseline_weights_metadata.json                 |   371 +-
 minimum cvar uncapped portfolio/commentary.txt     |   115 +-
 minimum cvar uncapped portfolio/data_policy.json   |     2 +-
 .../portfolio_xray.json                            |  1154 +-
 .../regime_factor_analytics_summary.json           |    18 +-
 .../regime_label_quality_summary.json              |    22 +-
 .../regime_portfolio_metrics_summary.json          |    24 +-
 minimum cvar uncapped portfolio/report.html        |   181 +-
 minimum cvar uncapped portfolio/report.txt         |   235 +-
 .../rolling_factor_betas.html                      |     2 +-
 .../rolling_factor_betas_10y.png                   |   Bin 207821 -> 207987 bytes
 .../rolling_factor_betas_3y.png                    |   Bin 223633 -> 223655 bytes
 .../rolling_factor_betas_5y.png                    |   Bin 215908 -> 215923 bytes
 minimum cvar uncapped portfolio/run_metadata.json  |    46 +-
 .../scenario_library.json                          |  5293 +-
 .../scenario_library_normalized.json               |  8888 ++-
 minimum cvar uncapped portfolio/snapshot_10y.json  |  1596 +-
 minimum cvar uncapped portfolio/snapshot_3y.json   |  1596 +-
 minimum cvar uncapped portfolio/snapshot_5y.json   |  1596 +-
 .../snapshot_assets.json                           |     2 +-
 .../snapshot_index.json                            |     2 +-
 .../stress_commentary.txt                          |   355 +-
 minimum cvar uncapped portfolio/stress_report.json | 72281 +-----------------
 minimum cvar uncapped portfolio/summary.json       |   386 +-
 minimum cvar uncapped portfolio/summary.txt        |     2 +-
 pdf files/Main portfolio_commentary.pdf            |   Bin 40094 -> 39863 bytes
 pdf files/Main portfolio_decision_package.pdf      |   Bin 37627 -> 37830 bytes
 pdf files/Main portfolio_ew_rp_comparison.pdf      |   Bin 36386 -> 36385 bytes
 pdf files/Main portfolio_ips_summary.pdf           |   Bin 36864 -> 36857 bytes
 pdf files/Main portfolio_stress_commentary.pdf     |   Bin 40022 -> 39791 bytes
 pdf files/Main portfolio_weights.pdf               |   Bin 36373 -> 36529 bytes
 pdf files/equal-weight_portfolio_commentary.pdf    |   Bin 39965 -> 40038 bytes
 .../equal-weight_portfolio_stress_commentary.pdf   |   Bin 39934 -> 40019 bytes
 pdf files/equal-weight_portfolio_weights.pdf       |   Bin 36002 -> 36158 bytes
 ...aximum_diversification_portfolio_commentary.pdf |   Bin 39798 -> 40015 bytes
 ...diversification_portfolio_stress_commentary.pdf |   Bin 39611 -> 39839 bytes
 .../maximum_diversification_portfolio_weights.pdf  |   Bin 36477 -> 36530 bytes
 ...nimum_cvar_constrained_portfolio_commentary.pdf |   Bin 39607 -> 39637 bytes
 ...var_constrained_portfolio_stress_commentary.pdf |   Bin 39438 -> 39459 bytes
 .../minimum_cvar_constrained_portfolio_weights.pdf |   Bin 36228 -> 36231 bytes
 .../minimum_cvar_uncapped_portfolio_commentary.pdf |   Bin 39576 -> 39590 bytes
 ...m_cvar_uncapped_portfolio_stress_commentary.pdf |   Bin 39403 -> 39419 bytes
 .../minimum_cvar_uncapped_portfolio_weights.pdf    |   Bin 36306 -> 36311 bytes
 ...imum_variance_advanced_portfolio_commentary.pdf |   Bin 39877 -> 40035 bytes
 ...riance_advanced_portfolio_stress_commentary.pdf |   Bin 39694 -> 39860 bytes
 ...minimum_variance_advanced_portfolio_weights.pdf |   Bin 36636 -> 36783 bytes
 .../minimum_variance_portfolio_commentary.pdf      |   Bin 40270 -> 40223 bytes
 ...inimum_variance_portfolio_stress_commentary.pdf |   Bin 40090 -> 40048 bytes
 pdf files/minimum_variance_portfolio_weights.pdf   |   Bin 36755 -> 36815 bytes
 ...imum_variance_uncapped_portfolio_commentary.pdf |   Bin 39369 -> 39623 bytes
 ...riance_uncapped_portfolio_stress_commentary.pdf |   Bin 39340 -> 39593 bytes
 ...minimum_variance_uncapped_portfolio_weights.pdf |   Bin 36219 -> 36118 bytes
 pdf files/risk_parity_portfolio_commentary.pdf     |   Bin 39713 -> 39768 bytes
 .../risk_parity_portfolio_stress_commentary.pdf    |   Bin 39693 -> 39747 bytes
 pdf files/risk_parity_portfolio_weights.pdf        |   Bin 36950 -> 36954 bytes
 ...n_variance_constrained_portfolio_commentary.pdf |   Bin 40334 -> 40390 bytes
 ...nce_constrained_portfolio_stress_commentary.pdf |   Bin 40329 -> 40384 bytes
 ...mean_variance_constrained_portfolio_weights.pdf |   Bin 37310 -> 37374 bytes
 ...mean_variance_uncapped_portfolio_commentary.pdf |   Bin 40065 -> 40110 bytes
 ...riance_uncapped_portfolio_stress_commentary.pdf |   Bin 40043 -> 40095 bytes
 ...st_mean_variance_uncapped_portfolio_weights.pdf |   Bin 36932 -> 36930 bytes
 pdf_md_sources/Main portfolio__commentary.md       |    20 +-
 pdf_md_sources/Main portfolio__decision_package.md |    44 +-
 pdf_md_sources/Main portfolio__ips_summary.md      |     4 +-
 .../Main portfolio__stress_commentary.md           |    20 +-
 .../equal-weight portfolio__commentary.md          |    18 +-
 .../equal-weight portfolio__stress_commentary.md   |    18 +-
 ...aximum diversification portfolio__commentary.md |    20 +-
 ...diversification portfolio__stress_commentary.md |    20 +-
 .../maximum diversification portfolio__weights.md  |    16 +-
 ...nimum cvar constrained portfolio__commentary.md |    18 +-
 ...var constrained portfolio__stress_commentary.md |    18 +-
 .../minimum cvar uncapped portfolio__commentary.md |    18 +-
 ...m cvar uncapped portfolio__stress_commentary.md |    18 +-
 ...imum variance advanced portfolio__commentary.md |    20 +-
 ...riance advanced portfolio__stress_commentary.md |    20 +-
 ...minimum variance advanced portfolio__weights.md |    14 +-
 .../minimum variance portfolio__commentary.md      |    20 +-
 ...inimum variance portfolio__stress_commentary.md |    20 +-
 .../minimum variance portfolio__weights.md         |    12 +-
 ...imum variance uncapped portfolio__commentary.md |    20 +-
 ...riance uncapped portfolio__stress_commentary.md |    20 +-
 ...minimum variance uncapped portfolio__weights.md |    14 +-
 .../risk parity portfolio__commentary.md           |    18 +-
 .../risk parity portfolio__stress_commentary.md    |    18 +-
 ...n variance constrained portfolio__commentary.md |    18 +-
 ...nce constrained portfolio__stress_commentary.md |    18 +-
 ...mean variance uncapped portfolio__commentary.md |    18 +-
 ...riance uncapped portfolio__stress_commentary.md |    18 +-
 requirements.txt                                   |     1 +
 risk budget by asset portfolio/commentary.txt      |   113 +-
 risk budget by asset portfolio/data_policy.json    |     2 +-
 risk budget by asset portfolio/portfolio_xray.json |  1263 +-
 .../regime_factor_analytics_summary.json           |    18 +-
 .../regime_label_quality_summary.json              |    22 +-
 .../regime_portfolio_metrics_summary.json          |    24 +-
 risk budget by asset portfolio/report.html         |   181 +-
 risk budget by asset portfolio/report.txt          |   236 +-
 .../rolling_factor_betas.html                      |     2 +-
 .../rolling_factor_betas_10y.png                   |   Bin 215105 -> 215082 bytes
 .../rolling_factor_betas_3y.png                    |   Bin 217718 -> 217646 bytes
 .../rolling_factor_betas_5y.png                    |   Bin 211732 -> 211797 bytes
 risk budget by asset portfolio/run_metadata.json   |    46 +-
 .../scenario_library.json                          |  5209 +-
 .../scenario_library_normalized.json               |  8866 ++-
 risk budget by asset portfolio/snapshot_10y.json   |  1508 +-
 risk budget by asset portfolio/snapshot_3y.json    |  1508 +-
 risk budget by asset portfolio/snapshot_5y.json    |  1508 +-
 .../snapshot_assets.json                           |     2 +-
 risk budget by asset portfolio/snapshot_index.json |     2 +-
 .../stress_commentary.txt                          |   352 +-
 risk budget by asset portfolio/stress_report.json  | 74028 +-----------------
 risk budget by asset portfolio/summary.json        |    15 +-
 risk budget by asset portfolio/summary.txt         |     2 +-
 .../commentary.txt                                 |   113 +-
 .../data_policy.json                               |     2 +-
 .../portfolio_xray.json                            |  1258 +-
 .../regime_factor_analytics_summary.json           |    18 +-
 .../regime_label_quality_summary.json              |    22 +-
 .../regime_portfolio_metrics_summary.json          |    24 +-
 risk budget by asset-class portfolio/report.html   |   181 +-
 risk budget by asset-class portfolio/report.txt    |   236 +-
 .../rolling_factor_betas.html                      |     2 +-
 .../rolling_factor_betas_10y.png                   |   Bin 219032 -> 218948 bytes
 .../rolling_factor_betas_3y.png                    |   Bin 219997 -> 219985 bytes
 .../rolling_factor_betas_5y.png                    |   Bin 208005 -> 208025 bytes
 .../run_metadata.json                              |    46 +-
 .../scenario_library.json                          |  5313 +-
 .../scenario_library_normalized.json               |  9648 ++-
 .../snapshot_10y.json                              |  1505 +-
 .../snapshot_3y.json                               |  1505 +-
 .../snapshot_5y.json                               |  1505 +-
 .../snapshot_assets.json                           |     2 +-
 .../snapshot_index.json                            |     2 +-
 .../stress_commentary.txt                          |   355 +-
 .../stress_report.json                             | 74059 +-----------------
 risk budget by asset-class portfolio/summary.json  |    15 +-
 risk budget by asset-class portfolio/summary.txt   |     2 +-
 .../baseline_weights_metadata.json                 |   318 +-
 .../commentary.txt                                 |   116 +-
 .../data_policy.json                               |     2 +-
 .../portfolio_xray.json                            |  1248 +-
 .../regime_factor_analytics_summary.json           |    18 +-
 .../regime_label_quality_summary.json              |    22 +-
 .../regime_portfolio_metrics_summary.json          |    24 +-
 .../report.html                                    |   183 +-
 .../report.txt                                     |   236 +-
 .../rolling_factor_betas.html                      |     2 +-
 .../rolling_factor_betas_10y.png                   |   Bin 209138 -> 209250 bytes
 .../rolling_factor_betas_3y.png                    |   Bin 229370 -> 229235 bytes
 .../rolling_factor_betas_5y.png                    |   Bin 210229 -> 210189 bytes
 .../run_metadata.json                              |    46 +-
 .../scenario_library.json                          |  5219 +-
 .../scenario_library_normalized.json               |  8848 ++-
 .../snapshot_10y.json                              |  1512 +-
 .../snapshot_3y.json                               |  1512 +-
 .../snapshot_5y.json                               |  1512 +-
 .../snapshot_assets.json                           |     2 +-
 .../snapshot_index.json                            |     2 +-
 .../stress_commentary.txt                          |   356 +-
 .../stress_report.json                             | 74103 +-----------------
 .../summary.json                                   |   333 +-
 .../summary.txt                                    |     2 +-
 .../baseline_weights_metadata.json                 |   167 +-
 .../commentary.txt                                 |   116 +-
 .../data_policy.json                               |     2 +-
 .../portfolio_xray.json                            |  1248 +-
 .../regime_factor_analytics_summary.json           |    18 +-
 .../regime_label_quality_summary.json              |    22 +-
 .../regime_portfolio_metrics_summary.json          |    24 +-
 .../report.html                                    |   179 +-
 robust mean variance uncapped portfolio/report.txt |   234 +-
 .../rolling_factor_betas.html                      |     2 +-
 .../rolling_factor_betas_10y.png                   |   Bin 203669 -> 203692 bytes
 .../rolling_factor_betas_3y.png                    |   Bin 220372 -> 220369 bytes
 .../rolling_factor_betas_5y.png                    |   Bin 202230 -> 202063 bytes
 .../run_metadata.json                              |    47 +-
 .../scenario_library.json                          |  5435 +-
 .../scenario_library_normalized.json               |  8828 ++-
 .../snapshot_10y.json                              |  1572 +-
 .../snapshot_3y.json                               |  1572 +-
 .../snapshot_5y.json                               |  1572 +-
 .../snapshot_assets.json                           |     2 +-
 .../snapshot_index.json                            |     2 +-
 .../stress_commentary.txt                          |   363 +-
 .../stress_report.json                             | 73224 +-----------------
 .../summary.json                                   |   182 +-
 .../summary.txt                                    |     2 +-
 run_report.py                                      |    29 +-
 src/__pycache__/__init__.cpython-313.pyc           |   Bin 174 -> 187 bytes
 src/__pycache__/cache.cpython-313.pyc              |   Bin 14041 -> 15297 bytes
 src/__pycache__/client_profiles.cpython-313.pyc    |   Bin 4701 -> 4714 bytes
 src/__pycache__/config.cpython-313.pyc             |   Bin 16231 -> 17126 bytes
 src/__pycache__/config_schema.cpython-313.pyc      |   Bin 43575 -> 54936 bytes
 src/__pycache__/data_ecb.cpython-313.pyc           |   Bin 2237 -> 2250 bytes
 src/__pycache__/data_fred.cpython-313.pyc          |   Bin 2868 -> 4715 bytes
 src/__pycache__/data_yf.cpython-313.pyc            |   Bin 3782 -> 4814 bytes
 src/__pycache__/fx.cpython-313.pyc                 |   Bin 4542 -> 4576 bytes
 src/__pycache__/io_export.cpython-313.pyc          |   Bin 20206 -> 27693 bytes
 src/__pycache__/metrics_asset.cpython-313.pyc      |   Bin 14373 -> 16913 bytes
 src/__pycache__/metrics_portfolio.cpython-313.pyc  |   Bin 3210 -> 5999 bytes
 src/__pycache__/portfolio_dynamic.cpython-313.pyc  |   Bin 7113 -> 8310 bytes
 src/__pycache__/resample.cpython-313.pyc           |   Bin 1317 -> 1330 bytes
 src/__pycache__/returns.cpython-313.pyc            |   Bin 2011 -> 2024 bytes
 src/__pycache__/risk_contrib.cpython-313.pyc       |   Bin 5728 -> 5803 bytes
 src/__pycache__/stress.cpython-313.pyc             |   Bin 29117 -> 83588 bytes
 src/__pycache__/utils.cpython-313.pyc              |   Bin 5076 -> 4961 bytes
 src/__pycache__/windows.cpython-313.pyc            |   Bin 3118 -> 4056 bytes
 src/cache.py                                       |     4 +
 src/candidate_comparison.py                        |    70 +-
 src/candidate_factory.py                           |    35 +
 src/config_schema.py                               |    19 +
 src/data_loader.py                                 |    36 +-
 src/live_core_e2e.py                               |     2 +-
 src/portfolio_review_workflow.py                   |    17 +-
 tests/test_candidate_factory.py                    |    30 +
 tests/test_data_cache_key.py                       |    30 +-
 tests/test_portfolio_review_workflow.py            |    28 +
 309 files changed, 107646 insertions(+), 656304 deletions(-)
```

## File Classification Table

Every changed or untracked path reported by `git status --short` is listed below.

### 1. Migration code changes to keep

| Status | Path | Recommendation | Notes |
| --- | --- | --- | --- |
| `M` | `run_report.py` | keep; stage later with migration code | Belongs to diagnosis-first Portfolio MRI code migration. |
| `......` | `src/ai_commentary_context.py` | keep; stage later with migration code | Belongs to diagnosis-first Portfolio MRI code migration. |
| `M` | `src/candidate_comparison.py` | keep; stage later with migration code | Belongs to diagnosis-first Portfolio MRI code migration. |
| `M` | `src/candidate_factory.py` | keep; stage later with migration code | Belongs to diagnosis-first Portfolio MRI code migration. |
| `......` | `src/candidate_launchpad.py` | keep; stage later with migration code | Belongs to diagnosis-first Portfolio MRI code migration. |
| `......` | `src/current_vs_candidate.py` | keep; stage later with migration code | Belongs to diagnosis-first Portfolio MRI code migration. |
| `......` | `src/decision_verdict.py` | keep; stage later with migration code | Belongs to diagnosis-first Portfolio MRI code migration. |
| `......` | `src/light_monitoring_summary.py` | keep; stage later with migration code | Belongs to diagnosis-first Portfolio MRI code migration. |
| `......` | `src/portfolio_alternatives_builder.py` | keep; stage later with migration code | Belongs to diagnosis-first Portfolio MRI code migration. |
| `M` | `src/portfolio_review_workflow.py` | keep; stage later with migration code | Belongs to diagnosis-first Portfolio MRI code migration. |
| `......` | `src/problem_classification.py` | keep; stage later with migration code | Belongs to diagnosis-first Portfolio MRI code migration. |
| `......` | `src/workflow_state.py` | keep; stage later with migration code | Belongs to diagnosis-first Portfolio MRI code migration. |

### 2. Documentation/ExecPlan changes to keep

| Status | Path | Recommendation | Notes |
| --- | --- | --- | --- |
| `......` | `CODE_MIGRATION_PLAN.md` | keep; stage later as docs/planning commit or with matching code | Migration documentation/spec/output-contract update. |
| `......` | `docs/audits/2026-05-25_code_migration_session01_runtime_inventory.md` | keep; stage later as docs/planning commit or with matching code | Migration documentation/spec/output-contract update. |
| `......` | `docs/exec_plans/2026-05-25_code_migration_to_diagnosis_first_portfolio_mri.md` | keep; stage later as docs/planning commit or with matching code | Migration documentation/spec/output-contract update. |
| `......` | `docs/specs/ai_commentary_grounding_spec.md` | keep; stage later as docs/planning commit or with matching code | Migration documentation/spec/output-contract update. |
| `M` | `docs/specs/candidate_factory_spec.md` | keep; stage later as docs/planning commit or with matching code | Migration documentation/spec/output-contract update. |
| `......` | `docs/specs/candidate_launchpad_spec.md` | keep; stage later as docs/planning commit or with matching code | Migration documentation/spec/output-contract update. |
| `......` | `docs/specs/current_vs_candidate_spec.md` | keep; stage later as docs/planning commit or with matching code | Migration documentation/spec/output-contract update. |
| `......` | `docs/specs/decision_verdict_spec.md` | keep; stage later as docs/planning commit or with matching code | Migration documentation/spec/output-contract update. |
| `......` | `docs/specs/light_monitoring_summary_spec.md` | keep; stage later as docs/planning commit or with matching code | Migration documentation/spec/output-contract update. |
| `......` | `docs/specs/portfolio_alternatives_builder_spec.md` | keep; stage later as docs/planning commit or with matching code | Migration documentation/spec/output-contract update. |
| `M` | `docs/specs/portfolio_review_workflow_spec.md` | keep; stage later as docs/planning commit or with matching code | Migration documentation/spec/output-contract update. |
| `......` | `docs/specs/problem_classification_spec.md` | keep; stage later as docs/planning commit or with matching code | Migration documentation/spec/output-contract update. |
| `M` | `docs/specs/README.md` | keep; stage later as docs/planning commit or with matching code | Migration documentation/spec/output-contract update. |
| `......` | `docs/specs/workflow_state_spec.md` | keep; stage later as docs/planning commit or with matching code | Migration documentation/spec/output-contract update. |
| `M` | `OUTPUTS.md` | keep; stage later as docs/planning commit or with matching code | Migration documentation/spec/output-contract update. |
| `M` | `SPEC.md` | keep; stage later as docs/planning commit or with matching code | Migration documentation/spec/output-contract update. |

### 5. Test changes

| Status | Path | Recommendation | Notes |
| --- | --- | --- | --- |
| `......` | `tests/test_ai_commentary_context.py` | keep; stage later with related migration code | Supports migration behavior or regression coverage. |
| `M` | `tests/test_candidate_factory.py` | keep; stage later with related migration code | Supports migration behavior or regression coverage. |
| `......` | `tests/test_candidate_launchpad.py` | keep; stage later with related migration code | Supports migration behavior or regression coverage. |
| `......` | `tests/test_current_vs_candidate.py` | keep; stage later with related migration code | Supports migration behavior or regression coverage. |
| `......` | `tests/test_decision_verdict.py` | keep; stage later with related migration code | Supports migration behavior or regression coverage. |
| `......` | `tests/test_light_monitoring_summary.py` | keep; stage later with related migration code | Supports migration behavior or regression coverage. |
| `......` | `tests/test_portfolio_alternatives_builder.py` | keep; stage later with related migration code | Supports migration behavior or regression coverage. |
| `M` | `tests/test_portfolio_review_workflow.py` | keep; stage later with related migration code | Supports migration behavior or regression coverage. |
| `......` | `tests/test_problem_classification.py` | keep; stage later with related migration code | Supports migration behavior or regression coverage. |
| `......` | `tests/test_workflow_state.py` | keep; stage later with related migration code | Supports migration behavior or regression coverage. |

### 3. Generated outputs / artifacts

| Status | Path | Recommendation | Notes |
| --- | --- | --- | --- |
| `......` | `candidate_factory_session9_smoke.log` | do not commit unless explicitly requested | Generated report/cache/artifact/log output. |
| `......` | `candidate_factory_stderr.log` | do not commit unless explicitly requested | Generated report/cache/artifact/log output. |
| `......` | `candidate_factory_stdout.log` | do not commit unless explicitly requested | Generated report/cache/artifact/log output. |
| `......` | `portfolio_review_stderr.log` | do not commit unless explicitly requested | Generated report/cache/artifact/log output. |
| `......` | `portfolio_review_stdout.log` | do not commit unless explicitly requested | Generated report/cache/artifact/log output. |
| `M` | `src/__pycache__/__init__.cpython-313.pyc` | do not commit unless explicitly requested | Generated report/cache/artifact/log output. |
| `M` | `src/__pycache__/cache.cpython-313.pyc` | do not commit unless explicitly requested | Generated report/cache/artifact/log output. |
| `M` | `src/__pycache__/client_profiles.cpython-313.pyc` | do not commit unless explicitly requested | Generated report/cache/artifact/log output. |
| `M` | `src/__pycache__/config.cpython-313.pyc` | do not commit unless explicitly requested | Generated report/cache/artifact/log output. |
| `M` | `src/__pycache__/config_schema.cpython-313.pyc` | do not commit unless explicitly requested | Generated report/cache/artifact/log output. |
| `M` | `src/__pycache__/data_ecb.cpython-313.pyc` | do not commit unless explicitly requested | Generated report/cache/artifact/log output. |
| `M` | `src/__pycache__/data_fred.cpython-313.pyc` | do not commit unless explicitly requested | Generated report/cache/artifact/log output. |
| `M` | `src/__pycache__/data_yf.cpython-313.pyc` | do not commit unless explicitly requested | Generated report/cache/artifact/log output. |
| `M` | `src/__pycache__/fx.cpython-313.pyc` | do not commit unless explicitly requested | Generated report/cache/artifact/log output. |
| `M` | `src/__pycache__/io_export.cpython-313.pyc` | do not commit unless explicitly requested | Generated report/cache/artifact/log output. |
| `M` | `src/__pycache__/metrics_asset.cpython-313.pyc` | do not commit unless explicitly requested | Generated report/cache/artifact/log output. |
| `M` | `src/__pycache__/metrics_portfolio.cpython-313.pyc` | do not commit unless explicitly requested | Generated report/cache/artifact/log output. |
| `M` | `src/__pycache__/portfolio_dynamic.cpython-313.pyc` | do not commit unless explicitly requested | Generated report/cache/artifact/log output. |
| `M` | `src/__pycache__/resample.cpython-313.pyc` | do not commit unless explicitly requested | Generated report/cache/artifact/log output. |
| `M` | `src/__pycache__/returns.cpython-313.pyc` | do not commit unless explicitly requested | Generated report/cache/artifact/log output. |
| `M` | `src/__pycache__/risk_contrib.cpython-313.pyc` | do not commit unless explicitly requested | Generated report/cache/artifact/log output. |
| `M` | `src/__pycache__/stress.cpython-313.pyc` | do not commit unless explicitly requested | Generated report/cache/artifact/log output. |
| `M` | `src/__pycache__/utils.cpython-313.pyc` | do not commit unless explicitly requested | Generated report/cache/artifact/log output. |
| `M` | `src/__pycache__/windows.cpython-313.pyc` | do not commit unless explicitly requested | Generated report/cache/artifact/log output. |

### 4. Config/environment changes

| Status | Path | Recommendation | Notes |
| --- | --- | --- | --- |
| `M` | `config.yml` | human review before keep/revert | Config/environment/dependency surface; do not stage with migration without review. |
| `M` | `config.yml.example` | human review before keep/revert | Config/environment/dependency surface; do not stage with migration without review. |
| `M` | `requirements.txt` | human review before keep/revert | Config/environment/dependency surface; do not stage with migration without review. |

### 6. Unrelated pre-existing dirty files

| Status | Path | Recommendation | Notes |
| --- | --- | --- | --- |
| `M` | `docs/audits/README.md` | do not stage with migration; review separately | Known unrelated/pre-existing dirty source/docs/test/provider work. |
| `M` | `docs/exec_plans/README.md` | do not stage with migration; review separately | Known unrelated/pre-existing dirty source/docs/test/provider work. |
| `......` | `run_ibkr_market_data.py` | do not stage with migration; review separately | Known unrelated/pre-existing dirty source/docs/test/provider work. |
| `M` | `src/action_engine.py` | do not stage with migration; review separately | Known unrelated/pre-existing dirty source/docs/test/provider work. |
| `M` | `src/cache.py` | do not stage with migration; review separately | Known unrelated/pre-existing dirty source/docs/test/provider work. |
| `M` | `src/config_schema.py` | do not stage with migration; review separately | Known unrelated/pre-existing dirty source/docs/test/provider work. |
| `......` | `src/data_ibkr.py` | do not stage with migration; review separately | Known unrelated/pre-existing dirty source/docs/test/provider work. |
| `M` | `src/data_loader.py` | do not stage with migration; review separately | Known unrelated/pre-existing dirty source/docs/test/provider work. |
| `......` | `src/data_provider.py` | do not stage with migration; review separately | Known unrelated/pre-existing dirty source/docs/test/provider work. |
| `M` | `src/data_trust_signals.py` | do not stage with migration; review separately | Known unrelated/pre-existing dirty source/docs/test/provider work. |
| `M` | `src/live_core_e2e.py` | do not stage with migration; review separately | Known unrelated/pre-existing dirty source/docs/test/provider work. |
| `M` | `src/selection_engine.py` | do not stage with migration; review separately | Known unrelated/pre-existing dirty source/docs/test/provider work. |
| `M` | `tests/test_data_cache_key.py` | do not stage with migration; review separately | Known unrelated/pre-existing dirty source/docs/test/provider work. |
| `......` | `tests/test_data_ibkr.py` | do not stage with migration; review separately | Known unrelated/pre-existing dirty source/docs/test/provider work. |
| `......` | `tests/test_data_provider.py` | do not stage with migration; review separately | Known unrelated/pre-existing dirty source/docs/test/provider work. |

### 7. Unknown / requires human review

| Status | Path | Recommendation | Notes |
| --- | --- | --- | --- |
| `M` | `"hierarchical risk parity portfolio/baseline_weights_metadata.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `......` | `"hierarchical risk parity portfolio/candidate_manifest.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"hierarchical risk parity portfolio/commentary.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"hierarchical risk parity portfolio/data_policy.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"hierarchical risk parity portfolio/drawdown_structure_3y.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"hierarchical risk parity portfolio/portfolio_xray.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"hierarchical risk parity portfolio/regime_factor_analytics_summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"hierarchical risk parity portfolio/regime_label_quality_summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"hierarchical risk parity portfolio/regime_portfolio_metrics_summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"hierarchical risk parity portfolio/report.html"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"hierarchical risk parity portfolio/report.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"hierarchical risk parity portfolio/rolling_factor_betas.html"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"hierarchical risk parity portfolio/rolling_factor_betas_10y.png"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"hierarchical risk parity portfolio/rolling_factor_betas_3y.png"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"hierarchical risk parity portfolio/rolling_factor_betas_5y.png"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"hierarchical risk parity portfolio/run_metadata.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"hierarchical risk parity portfolio/scenario_library.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"hierarchical risk parity portfolio/scenario_library_normalized.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"hierarchical risk parity portfolio/snapshot_10y.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"hierarchical risk parity portfolio/snapshot_3y.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"hierarchical risk parity portfolio/snapshot_5y.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"hierarchical risk parity portfolio/snapshot_assets.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"hierarchical risk parity portfolio/snapshot_index.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"hierarchical risk parity portfolio/stress_commentary.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"hierarchical risk parity portfolio/stress_report.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"hierarchical risk parity portfolio/summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"hierarchical risk parity portfolio/summary.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"hierarchical risk parity portfolio/weights.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"hierarchical risk parity portfolio/weights.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"maximum diversification unconstrained portfolio/baseline_weights_metadata.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"maximum diversification unconstrained portfolio/commentary.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"maximum diversification unconstrained portfolio/data_policy.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"maximum diversification unconstrained portfolio/drawdown_structure_10y.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"maximum diversification unconstrained portfolio/drawdown_structure_5y.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"maximum diversification unconstrained portfolio/portfolio_xray.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"maximum diversification unconstrained portfolio/regime_factor_analytics_summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"maximum diversification unconstrained portfolio/regime_label_quality_summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"maximum diversification unconstrained portfolio/regime_portfolio_metrics_summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"maximum diversification unconstrained portfolio/report.html"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"maximum diversification unconstrained portfolio/report.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"maximum diversification unconstrained portfolio/rolling_factor_betas.html"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"maximum diversification unconstrained portfolio/rolling_factor_betas_10y.png"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"maximum diversification unconstrained portfolio/rolling_factor_betas_3y.png"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"maximum diversification unconstrained portfolio/rolling_factor_betas_5y.png"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"maximum diversification unconstrained portfolio/run_metadata.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"maximum diversification unconstrained portfolio/scenario_library.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"maximum diversification unconstrained portfolio/scenario_library_normalized.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"maximum diversification unconstrained portfolio/snapshot_10y.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"maximum diversification unconstrained portfolio/snapshot_3y.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"maximum diversification unconstrained portfolio/snapshot_5y.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"maximum diversification unconstrained portfolio/snapshot_assets.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"maximum diversification unconstrained portfolio/snapshot_index.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"maximum diversification unconstrained portfolio/stress_commentary.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"maximum diversification unconstrained portfolio/stress_report.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"maximum diversification unconstrained portfolio/summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"maximum diversification unconstrained portfolio/summary.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"maximum diversification unconstrained portfolio/weights.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"maximum diversification unconstrained portfolio/weights.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar constrained portfolio/baseline_weights_metadata.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar constrained portfolio/commentary.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar constrained portfolio/data_policy.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar constrained portfolio/portfolio_xray.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar constrained portfolio/regime_factor_analytics_summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar constrained portfolio/regime_label_quality_summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar constrained portfolio/regime_portfolio_metrics_summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar constrained portfolio/report.html"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar constrained portfolio/report.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar constrained portfolio/rolling_factor_betas.html"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar constrained portfolio/rolling_factor_betas_10y.png"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar constrained portfolio/rolling_factor_betas_3y.png"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar constrained portfolio/rolling_factor_betas_5y.png"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar constrained portfolio/run_metadata.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar constrained portfolio/scenario_library.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar constrained portfolio/scenario_library_normalized.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar constrained portfolio/snapshot_10y.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar constrained portfolio/snapshot_3y.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar constrained portfolio/snapshot_5y.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar constrained portfolio/snapshot_assets.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar constrained portfolio/snapshot_index.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar constrained portfolio/stress_commentary.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar constrained portfolio/stress_report.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar constrained portfolio/summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar constrained portfolio/summary.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar uncapped portfolio/baseline_weights_metadata.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar uncapped portfolio/commentary.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar uncapped portfolio/data_policy.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar uncapped portfolio/portfolio_xray.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar uncapped portfolio/regime_factor_analytics_summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar uncapped portfolio/regime_label_quality_summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar uncapped portfolio/regime_portfolio_metrics_summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar uncapped portfolio/report.html"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar uncapped portfolio/report.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar uncapped portfolio/rolling_factor_betas.html"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar uncapped portfolio/rolling_factor_betas_10y.png"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar uncapped portfolio/rolling_factor_betas_3y.png"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar uncapped portfolio/rolling_factor_betas_5y.png"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar uncapped portfolio/run_metadata.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar uncapped portfolio/scenario_library.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar uncapped portfolio/scenario_library_normalized.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar uncapped portfolio/snapshot_10y.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar uncapped portfolio/snapshot_3y.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar uncapped portfolio/snapshot_5y.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar uncapped portfolio/snapshot_assets.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar uncapped portfolio/snapshot_index.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar uncapped portfolio/stress_commentary.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar uncapped portfolio/stress_report.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar uncapped portfolio/summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"minimum cvar uncapped portfolio/summary.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/equal-weight_portfolio_commentary.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/equal-weight_portfolio_stress_commentary.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/equal-weight_portfolio_weights.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/Main portfolio_commentary.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/Main portfolio_decision_package.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/Main portfolio_ew_rp_comparison.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/Main portfolio_ips_summary.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/Main portfolio_stress_commentary.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/Main portfolio_weights.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/maximum_diversification_portfolio_commentary.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/maximum_diversification_portfolio_stress_commentary.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/maximum_diversification_portfolio_weights.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/minimum_cvar_constrained_portfolio_commentary.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/minimum_cvar_constrained_portfolio_stress_commentary.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/minimum_cvar_constrained_portfolio_weights.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/minimum_cvar_uncapped_portfolio_commentary.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/minimum_cvar_uncapped_portfolio_stress_commentary.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/minimum_cvar_uncapped_portfolio_weights.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/minimum_variance_advanced_portfolio_commentary.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/minimum_variance_advanced_portfolio_stress_commentary.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/minimum_variance_advanced_portfolio_weights.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/minimum_variance_portfolio_commentary.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/minimum_variance_portfolio_stress_commentary.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/minimum_variance_portfolio_weights.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/minimum_variance_uncapped_portfolio_commentary.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/minimum_variance_uncapped_portfolio_stress_commentary.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/minimum_variance_uncapped_portfolio_weights.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/risk_parity_portfolio_commentary.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/risk_parity_portfolio_stress_commentary.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/risk_parity_portfolio_weights.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/robust_mean_variance_constrained_portfolio_commentary.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/robust_mean_variance_constrained_portfolio_stress_commentary.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/robust_mean_variance_constrained_portfolio_weights.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/robust_mean_variance_uncapped_portfolio_commentary.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/robust_mean_variance_uncapped_portfolio_stress_commentary.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf files/robust_mean_variance_uncapped_portfolio_weights.pdf"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf_md_sources/equal-weight portfolio__commentary.md"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf_md_sources/equal-weight portfolio__stress_commentary.md"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf_md_sources/Main portfolio__commentary.md"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf_md_sources/Main portfolio__decision_package.md"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf_md_sources/Main portfolio__ips_summary.md"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf_md_sources/Main portfolio__stress_commentary.md"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf_md_sources/maximum diversification portfolio__commentary.md"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf_md_sources/maximum diversification portfolio__stress_commentary.md"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf_md_sources/maximum diversification portfolio__weights.md"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf_md_sources/minimum cvar constrained portfolio__commentary.md"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf_md_sources/minimum cvar constrained portfolio__stress_commentary.md"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf_md_sources/minimum cvar uncapped portfolio__commentary.md"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf_md_sources/minimum cvar uncapped portfolio__stress_commentary.md"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf_md_sources/minimum variance advanced portfolio__commentary.md"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf_md_sources/minimum variance advanced portfolio__stress_commentary.md"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf_md_sources/minimum variance advanced portfolio__weights.md"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf_md_sources/minimum variance portfolio__commentary.md"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf_md_sources/minimum variance portfolio__stress_commentary.md"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf_md_sources/minimum variance portfolio__weights.md"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf_md_sources/minimum variance uncapped portfolio__commentary.md"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf_md_sources/minimum variance uncapped portfolio__stress_commentary.md"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf_md_sources/minimum variance uncapped portfolio__weights.md"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf_md_sources/risk parity portfolio__commentary.md"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf_md_sources/risk parity portfolio__stress_commentary.md"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf_md_sources/robust mean variance constrained portfolio__commentary.md"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf_md_sources/robust mean variance constrained portfolio__stress_commentary.md"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf_md_sources/robust mean variance uncapped portfolio__commentary.md"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"pdf_md_sources/robust mean variance uncapped portfolio__stress_commentary.md"` | review before staging | Path does not match known migration/generated/config buckets. |
| `......` | `"risk budget by asset portfolio/candidate_manifest.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset portfolio/commentary.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset portfolio/data_policy.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset portfolio/portfolio_xray.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset portfolio/regime_factor_analytics_summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset portfolio/regime_label_quality_summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset portfolio/regime_portfolio_metrics_summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset portfolio/report.html"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset portfolio/report.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset portfolio/rolling_factor_betas.html"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset portfolio/rolling_factor_betas_10y.png"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset portfolio/rolling_factor_betas_3y.png"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset portfolio/rolling_factor_betas_5y.png"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset portfolio/run_metadata.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset portfolio/scenario_library.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset portfolio/scenario_library_normalized.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset portfolio/snapshot_10y.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset portfolio/snapshot_3y.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset portfolio/snapshot_5y.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset portfolio/snapshot_assets.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset portfolio/snapshot_index.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset portfolio/stress_commentary.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset portfolio/stress_report.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset portfolio/summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset portfolio/summary.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `......` | `"risk budget by asset-class portfolio/candidate_manifest.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset-class portfolio/commentary.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset-class portfolio/data_policy.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset-class portfolio/portfolio_xray.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset-class portfolio/regime_factor_analytics_summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset-class portfolio/regime_label_quality_summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset-class portfolio/regime_portfolio_metrics_summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset-class portfolio/report.html"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset-class portfolio/report.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset-class portfolio/rolling_factor_betas.html"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset-class portfolio/rolling_factor_betas_10y.png"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset-class portfolio/rolling_factor_betas_3y.png"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset-class portfolio/rolling_factor_betas_5y.png"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset-class portfolio/run_metadata.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset-class portfolio/scenario_library.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset-class portfolio/scenario_library_normalized.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset-class portfolio/snapshot_10y.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset-class portfolio/snapshot_3y.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset-class portfolio/snapshot_5y.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset-class portfolio/snapshot_assets.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset-class portfolio/snapshot_index.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset-class portfolio/stress_commentary.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset-class portfolio/stress_report.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset-class portfolio/summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"risk budget by asset-class portfolio/summary.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance constrained portfolio/baseline_weights_metadata.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance constrained portfolio/commentary.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance constrained portfolio/data_policy.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance constrained portfolio/portfolio_xray.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance constrained portfolio/regime_factor_analytics_summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance constrained portfolio/regime_label_quality_summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance constrained portfolio/regime_portfolio_metrics_summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance constrained portfolio/report.html"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance constrained portfolio/report.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance constrained portfolio/rolling_factor_betas.html"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance constrained portfolio/rolling_factor_betas_10y.png"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance constrained portfolio/rolling_factor_betas_3y.png"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance constrained portfolio/rolling_factor_betas_5y.png"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance constrained portfolio/run_metadata.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance constrained portfolio/scenario_library.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance constrained portfolio/scenario_library_normalized.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance constrained portfolio/snapshot_10y.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance constrained portfolio/snapshot_3y.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance constrained portfolio/snapshot_5y.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance constrained portfolio/snapshot_assets.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance constrained portfolio/snapshot_index.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance constrained portfolio/stress_commentary.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance constrained portfolio/stress_report.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance constrained portfolio/summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance constrained portfolio/summary.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance uncapped portfolio/baseline_weights_metadata.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance uncapped portfolio/commentary.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance uncapped portfolio/data_policy.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance uncapped portfolio/portfolio_xray.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance uncapped portfolio/regime_factor_analytics_summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance uncapped portfolio/regime_label_quality_summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance uncapped portfolio/regime_portfolio_metrics_summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance uncapped portfolio/report.html"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance uncapped portfolio/report.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance uncapped portfolio/rolling_factor_betas.html"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance uncapped portfolio/rolling_factor_betas_10y.png"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance uncapped portfolio/rolling_factor_betas_3y.png"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance uncapped portfolio/rolling_factor_betas_5y.png"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance uncapped portfolio/run_metadata.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance uncapped portfolio/scenario_library.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance uncapped portfolio/scenario_library_normalized.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance uncapped portfolio/snapshot_10y.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance uncapped portfolio/snapshot_3y.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance uncapped portfolio/snapshot_5y.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance uncapped portfolio/snapshot_assets.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance uncapped portfolio/snapshot_index.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance uncapped portfolio/stress_commentary.txt"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance uncapped portfolio/stress_report.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance uncapped portfolio/summary.json"` | review before staging | Path does not match known migration/generated/config buckets. |
| `M` | `"robust mean variance uncapped portfolio/summary.txt"` | review before staging | Path does not match known migration/generated/config buckets. |

## Recommended Cleanup Order

1. **Do not stage anything yet.** Confirm this classification with a human first.
2. Review config/environment changes (`config.yml`, `config.yml.example`, `requirements.txt`) separately; decide keep/revert/commit separately.
3. Review unrelated pre-existing source/provider changes separately, especially IBKR/data-provider/cache files.
4. Exclude generated artifacts/logs/pycache from migration commits. Do not delete them in this audit task.
5. Stage migration code files only after review.
6. Stage migration tests with the code commit, or as a paired test commit.
7. Stage migration docs/specs/ExecPlan either with the related code or as a separate documentation commit.
8. Fix the three remaining blockers in separate focused sessions.
9. Only after blockers are resolved/accepted, run the fuller smoke command and inspect generated-output changes before any commit.

## Exact Files Safe to Stage Later

These are safe to stage later **only after human review** and without using `git add -A`.

### Migration code changes to keep

- `run_report.py`
- `src/ai_commentary_context.py`
- `src/candidate_comparison.py`
- `src/candidate_factory.py`
- `src/candidate_launchpad.py`
- `src/current_vs_candidate.py`
- `src/decision_verdict.py`
- `src/light_monitoring_summary.py`
- `src/portfolio_alternatives_builder.py`
- `src/portfolio_review_workflow.py`
- `src/problem_classification.py`
- `src/workflow_state.py`

### Documentation / ExecPlan changes to keep

- `CODE_MIGRATION_PLAN.md`
- `docs/audits/2026-05-25_code_migration_session01_runtime_inventory.md`
- `docs/exec_plans/2026-05-25_code_migration_to_diagnosis_first_portfolio_mri.md`
- `docs/specs/ai_commentary_grounding_spec.md`
- `docs/specs/candidate_factory_spec.md`
- `docs/specs/candidate_launchpad_spec.md`
- `docs/specs/current_vs_candidate_spec.md`
- `docs/specs/decision_verdict_spec.md`
- `docs/specs/light_monitoring_summary_spec.md`
- `docs/specs/portfolio_alternatives_builder_spec.md`
- `docs/specs/portfolio_review_workflow_spec.md`
- `docs/specs/problem_classification_spec.md`
- `docs/specs/README.md`
- `docs/specs/workflow_state_spec.md`
- `OUTPUTS.md`
- `SPEC.md`

### Migration test changes to keep

- `tests/test_ai_commentary_context.py`
- `tests/test_candidate_factory.py`
- `tests/test_candidate_launchpad.py`
- `tests/test_current_vs_candidate.py`
- `tests/test_decision_verdict.py`
- `tests/test_light_monitoring_summary.py`
- `tests/test_portfolio_alternatives_builder.py`
- `tests/test_portfolio_review_workflow.py`
- `tests/test_problem_classification.py`
- `tests/test_workflow_state.py`

## Exact Files That Should Not Be Committed With Migration

These paths should not be staged with the migration commit. Some may be kept in separate work, but they require human review or are generated artifacts.

- `"hierarchical risk parity portfolio/baseline_weights_metadata.json"`
- `"hierarchical risk parity portfolio/candidate_manifest.json"`
- `"hierarchical risk parity portfolio/commentary.txt"`
- `"hierarchical risk parity portfolio/data_policy.json"`
- `"hierarchical risk parity portfolio/drawdown_structure_3y.json"`
- `"hierarchical risk parity portfolio/portfolio_xray.json"`
- `"hierarchical risk parity portfolio/regime_factor_analytics_summary.json"`
- `"hierarchical risk parity portfolio/regime_label_quality_summary.json"`
- `"hierarchical risk parity portfolio/regime_portfolio_metrics_summary.json"`
- `"hierarchical risk parity portfolio/report.html"`
- `"hierarchical risk parity portfolio/report.txt"`
- `"hierarchical risk parity portfolio/rolling_factor_betas.html"`
- `"hierarchical risk parity portfolio/rolling_factor_betas_10y.png"`
- `"hierarchical risk parity portfolio/rolling_factor_betas_3y.png"`
- `"hierarchical risk parity portfolio/rolling_factor_betas_5y.png"`
- `"hierarchical risk parity portfolio/run_metadata.json"`
- `"hierarchical risk parity portfolio/scenario_library.json"`
- `"hierarchical risk parity portfolio/scenario_library_normalized.json"`
- `"hierarchical risk parity portfolio/snapshot_10y.json"`
- `"hierarchical risk parity portfolio/snapshot_3y.json"`
- `"hierarchical risk parity portfolio/snapshot_5y.json"`
- `"hierarchical risk parity portfolio/snapshot_assets.json"`
- `"hierarchical risk parity portfolio/snapshot_index.json"`
- `"hierarchical risk parity portfolio/stress_commentary.txt"`
- `"hierarchical risk parity portfolio/stress_report.json"`
- `"hierarchical risk parity portfolio/summary.json"`
- `"hierarchical risk parity portfolio/summary.txt"`
- `"hierarchical risk parity portfolio/weights.json"`
- `"hierarchical risk parity portfolio/weights.txt"`
- `"maximum diversification unconstrained portfolio/baseline_weights_metadata.json"`
- `"maximum diversification unconstrained portfolio/commentary.txt"`
- `"maximum diversification unconstrained portfolio/data_policy.json"`
- `"maximum diversification unconstrained portfolio/drawdown_structure_10y.json"`
- `"maximum diversification unconstrained portfolio/drawdown_structure_5y.json"`
- `"maximum diversification unconstrained portfolio/portfolio_xray.json"`
- `"maximum diversification unconstrained portfolio/regime_factor_analytics_summary.json"`
- `"maximum diversification unconstrained portfolio/regime_label_quality_summary.json"`
- `"maximum diversification unconstrained portfolio/regime_portfolio_metrics_summary.json"`
- `"maximum diversification unconstrained portfolio/report.html"`
- `"maximum diversification unconstrained portfolio/report.txt"`
- `"maximum diversification unconstrained portfolio/rolling_factor_betas.html"`
- `"maximum diversification unconstrained portfolio/rolling_factor_betas_10y.png"`
- `"maximum diversification unconstrained portfolio/rolling_factor_betas_3y.png"`
- `"maximum diversification unconstrained portfolio/rolling_factor_betas_5y.png"`
- `"maximum diversification unconstrained portfolio/run_metadata.json"`
- `"maximum diversification unconstrained portfolio/scenario_library.json"`
- `"maximum diversification unconstrained portfolio/scenario_library_normalized.json"`
- `"maximum diversification unconstrained portfolio/snapshot_10y.json"`
- `"maximum diversification unconstrained portfolio/snapshot_3y.json"`
- `"maximum diversification unconstrained portfolio/snapshot_5y.json"`
- `"maximum diversification unconstrained portfolio/snapshot_assets.json"`
- `"maximum diversification unconstrained portfolio/snapshot_index.json"`
- `"maximum diversification unconstrained portfolio/stress_commentary.txt"`
- `"maximum diversification unconstrained portfolio/stress_report.json"`
- `"maximum diversification unconstrained portfolio/summary.json"`
- `"maximum diversification unconstrained portfolio/summary.txt"`
- `"maximum diversification unconstrained portfolio/weights.json"`
- `"maximum diversification unconstrained portfolio/weights.txt"`
- `"minimum cvar constrained portfolio/baseline_weights_metadata.json"`
- `"minimum cvar constrained portfolio/commentary.txt"`
- `"minimum cvar constrained portfolio/data_policy.json"`
- `"minimum cvar constrained portfolio/portfolio_xray.json"`
- `"minimum cvar constrained portfolio/regime_factor_analytics_summary.json"`
- `"minimum cvar constrained portfolio/regime_label_quality_summary.json"`
- `"minimum cvar constrained portfolio/regime_portfolio_metrics_summary.json"`
- `"minimum cvar constrained portfolio/report.html"`
- `"minimum cvar constrained portfolio/report.txt"`
- `"minimum cvar constrained portfolio/rolling_factor_betas.html"`
- `"minimum cvar constrained portfolio/rolling_factor_betas_10y.png"`
- `"minimum cvar constrained portfolio/rolling_factor_betas_3y.png"`
- `"minimum cvar constrained portfolio/rolling_factor_betas_5y.png"`
- `"minimum cvar constrained portfolio/run_metadata.json"`
- `"minimum cvar constrained portfolio/scenario_library.json"`
- `"minimum cvar constrained portfolio/scenario_library_normalized.json"`
- `"minimum cvar constrained portfolio/snapshot_10y.json"`
- `"minimum cvar constrained portfolio/snapshot_3y.json"`
- `"minimum cvar constrained portfolio/snapshot_5y.json"`
- `"minimum cvar constrained portfolio/snapshot_assets.json"`
- `"minimum cvar constrained portfolio/snapshot_index.json"`
- `"minimum cvar constrained portfolio/stress_commentary.txt"`
- `"minimum cvar constrained portfolio/stress_report.json"`
- `"minimum cvar constrained portfolio/summary.json"`
- `"minimum cvar constrained portfolio/summary.txt"`
- `"minimum cvar uncapped portfolio/baseline_weights_metadata.json"`
- `"minimum cvar uncapped portfolio/commentary.txt"`
- `"minimum cvar uncapped portfolio/data_policy.json"`
- `"minimum cvar uncapped portfolio/portfolio_xray.json"`
- `"minimum cvar uncapped portfolio/regime_factor_analytics_summary.json"`
- `"minimum cvar uncapped portfolio/regime_label_quality_summary.json"`
- `"minimum cvar uncapped portfolio/regime_portfolio_metrics_summary.json"`
- `"minimum cvar uncapped portfolio/report.html"`
- `"minimum cvar uncapped portfolio/report.txt"`
- `"minimum cvar uncapped portfolio/rolling_factor_betas.html"`
- `"minimum cvar uncapped portfolio/rolling_factor_betas_10y.png"`
- `"minimum cvar uncapped portfolio/rolling_factor_betas_3y.png"`
- `"minimum cvar uncapped portfolio/rolling_factor_betas_5y.png"`
- `"minimum cvar uncapped portfolio/run_metadata.json"`
- `"minimum cvar uncapped portfolio/scenario_library.json"`
- `"minimum cvar uncapped portfolio/scenario_library_normalized.json"`
- `"minimum cvar uncapped portfolio/snapshot_10y.json"`
- `"minimum cvar uncapped portfolio/snapshot_3y.json"`
- `"minimum cvar uncapped portfolio/snapshot_5y.json"`
- `"minimum cvar uncapped portfolio/snapshot_assets.json"`
- `"minimum cvar uncapped portfolio/snapshot_index.json"`
- `"minimum cvar uncapped portfolio/stress_commentary.txt"`
- `"minimum cvar uncapped portfolio/stress_report.json"`
- `"minimum cvar uncapped portfolio/summary.json"`
- `"minimum cvar uncapped portfolio/summary.txt"`
- `"pdf files/equal-weight_portfolio_commentary.pdf"`
- `"pdf files/equal-weight_portfolio_stress_commentary.pdf"`
- `"pdf files/equal-weight_portfolio_weights.pdf"`
- `"pdf files/Main portfolio_commentary.pdf"`
- `"pdf files/Main portfolio_decision_package.pdf"`
- `"pdf files/Main portfolio_ew_rp_comparison.pdf"`
- `"pdf files/Main portfolio_ips_summary.pdf"`
- `"pdf files/Main portfolio_stress_commentary.pdf"`
- `"pdf files/Main portfolio_weights.pdf"`
- `"pdf files/maximum_diversification_portfolio_commentary.pdf"`
- `"pdf files/maximum_diversification_portfolio_stress_commentary.pdf"`
- `"pdf files/maximum_diversification_portfolio_weights.pdf"`
- `"pdf files/minimum_cvar_constrained_portfolio_commentary.pdf"`
- `"pdf files/minimum_cvar_constrained_portfolio_stress_commentary.pdf"`
- `"pdf files/minimum_cvar_constrained_portfolio_weights.pdf"`
- `"pdf files/minimum_cvar_uncapped_portfolio_commentary.pdf"`
- `"pdf files/minimum_cvar_uncapped_portfolio_stress_commentary.pdf"`
- `"pdf files/minimum_cvar_uncapped_portfolio_weights.pdf"`
- `"pdf files/minimum_variance_advanced_portfolio_commentary.pdf"`
- `"pdf files/minimum_variance_advanced_portfolio_stress_commentary.pdf"`
- `"pdf files/minimum_variance_advanced_portfolio_weights.pdf"`
- `"pdf files/minimum_variance_portfolio_commentary.pdf"`
- `"pdf files/minimum_variance_portfolio_stress_commentary.pdf"`
- `"pdf files/minimum_variance_portfolio_weights.pdf"`
- `"pdf files/minimum_variance_uncapped_portfolio_commentary.pdf"`
- `"pdf files/minimum_variance_uncapped_portfolio_stress_commentary.pdf"`
- `"pdf files/minimum_variance_uncapped_portfolio_weights.pdf"`
- `"pdf files/risk_parity_portfolio_commentary.pdf"`
- `"pdf files/risk_parity_portfolio_stress_commentary.pdf"`
- `"pdf files/risk_parity_portfolio_weights.pdf"`
- `"pdf files/robust_mean_variance_constrained_portfolio_commentary.pdf"`
- `"pdf files/robust_mean_variance_constrained_portfolio_stress_commentary.pdf"`
- `"pdf files/robust_mean_variance_constrained_portfolio_weights.pdf"`
- `"pdf files/robust_mean_variance_uncapped_portfolio_commentary.pdf"`
- `"pdf files/robust_mean_variance_uncapped_portfolio_stress_commentary.pdf"`
- `"pdf files/robust_mean_variance_uncapped_portfolio_weights.pdf"`
- `"pdf_md_sources/equal-weight portfolio__commentary.md"`
- `"pdf_md_sources/equal-weight portfolio__stress_commentary.md"`
- `"pdf_md_sources/Main portfolio__commentary.md"`
- `"pdf_md_sources/Main portfolio__decision_package.md"`
- `"pdf_md_sources/Main portfolio__ips_summary.md"`
- `"pdf_md_sources/Main portfolio__stress_commentary.md"`
- `"pdf_md_sources/maximum diversification portfolio__commentary.md"`
- `"pdf_md_sources/maximum diversification portfolio__stress_commentary.md"`
- `"pdf_md_sources/maximum diversification portfolio__weights.md"`
- `"pdf_md_sources/minimum cvar constrained portfolio__commentary.md"`
- `"pdf_md_sources/minimum cvar constrained portfolio__stress_commentary.md"`
- `"pdf_md_sources/minimum cvar uncapped portfolio__commentary.md"`
- `"pdf_md_sources/minimum cvar uncapped portfolio__stress_commentary.md"`
- `"pdf_md_sources/minimum variance advanced portfolio__commentary.md"`
- `"pdf_md_sources/minimum variance advanced portfolio__stress_commentary.md"`
- `"pdf_md_sources/minimum variance advanced portfolio__weights.md"`
- `"pdf_md_sources/minimum variance portfolio__commentary.md"`
- `"pdf_md_sources/minimum variance portfolio__stress_commentary.md"`
- `"pdf_md_sources/minimum variance portfolio__weights.md"`
- `"pdf_md_sources/minimum variance uncapped portfolio__commentary.md"`
- `"pdf_md_sources/minimum variance uncapped portfolio__stress_commentary.md"`
- `"pdf_md_sources/minimum variance uncapped portfolio__weights.md"`
- `"pdf_md_sources/risk parity portfolio__commentary.md"`
- `"pdf_md_sources/risk parity portfolio__stress_commentary.md"`
- `"pdf_md_sources/robust mean variance constrained portfolio__commentary.md"`
- `"pdf_md_sources/robust mean variance constrained portfolio__stress_commentary.md"`
- `"pdf_md_sources/robust mean variance uncapped portfolio__commentary.md"`
- `"pdf_md_sources/robust mean variance uncapped portfolio__stress_commentary.md"`
- `"risk budget by asset portfolio/candidate_manifest.json"`
- `"risk budget by asset portfolio/commentary.txt"`
- `"risk budget by asset portfolio/data_policy.json"`
- `"risk budget by asset portfolio/portfolio_xray.json"`
- `"risk budget by asset portfolio/regime_factor_analytics_summary.json"`
- `"risk budget by asset portfolio/regime_label_quality_summary.json"`
- `"risk budget by asset portfolio/regime_portfolio_metrics_summary.json"`
- `"risk budget by asset portfolio/report.html"`
- `"risk budget by asset portfolio/report.txt"`
- `"risk budget by asset portfolio/rolling_factor_betas.html"`
- `"risk budget by asset portfolio/rolling_factor_betas_10y.png"`
- `"risk budget by asset portfolio/rolling_factor_betas_3y.png"`
- `"risk budget by asset portfolio/rolling_factor_betas_5y.png"`
- `"risk budget by asset portfolio/run_metadata.json"`
- `"risk budget by asset portfolio/scenario_library.json"`
- `"risk budget by asset portfolio/scenario_library_normalized.json"`
- `"risk budget by asset portfolio/snapshot_10y.json"`
- `"risk budget by asset portfolio/snapshot_3y.json"`
- `"risk budget by asset portfolio/snapshot_5y.json"`
- `"risk budget by asset portfolio/snapshot_assets.json"`
- `"risk budget by asset portfolio/snapshot_index.json"`
- `"risk budget by asset portfolio/stress_commentary.txt"`
- `"risk budget by asset portfolio/stress_report.json"`
- `"risk budget by asset portfolio/summary.json"`
- `"risk budget by asset portfolio/summary.txt"`
- `"risk budget by asset-class portfolio/candidate_manifest.json"`
- `"risk budget by asset-class portfolio/commentary.txt"`
- `"risk budget by asset-class portfolio/data_policy.json"`
- `"risk budget by asset-class portfolio/portfolio_xray.json"`
- `"risk budget by asset-class portfolio/regime_factor_analytics_summary.json"`
- `"risk budget by asset-class portfolio/regime_label_quality_summary.json"`
- `"risk budget by asset-class portfolio/regime_portfolio_metrics_summary.json"`
- `"risk budget by asset-class portfolio/report.html"`
- `"risk budget by asset-class portfolio/report.txt"`
- `"risk budget by asset-class portfolio/rolling_factor_betas.html"`
- `"risk budget by asset-class portfolio/rolling_factor_betas_10y.png"`
- `"risk budget by asset-class portfolio/rolling_factor_betas_3y.png"`
- `"risk budget by asset-class portfolio/rolling_factor_betas_5y.png"`
- `"risk budget by asset-class portfolio/run_metadata.json"`
- `"risk budget by asset-class portfolio/scenario_library.json"`
- `"risk budget by asset-class portfolio/scenario_library_normalized.json"`
- `"risk budget by asset-class portfolio/snapshot_10y.json"`
- `"risk budget by asset-class portfolio/snapshot_3y.json"`
- `"risk budget by asset-class portfolio/snapshot_5y.json"`
- `"risk budget by asset-class portfolio/snapshot_assets.json"`
- `"risk budget by asset-class portfolio/snapshot_index.json"`
- `"risk budget by asset-class portfolio/stress_commentary.txt"`
- `"risk budget by asset-class portfolio/stress_report.json"`
- `"risk budget by asset-class portfolio/summary.json"`
- `"risk budget by asset-class portfolio/summary.txt"`
- `"robust mean variance constrained portfolio/baseline_weights_metadata.json"`
- `"robust mean variance constrained portfolio/commentary.txt"`
- `"robust mean variance constrained portfolio/data_policy.json"`
- `"robust mean variance constrained portfolio/portfolio_xray.json"`
- `"robust mean variance constrained portfolio/regime_factor_analytics_summary.json"`
- `"robust mean variance constrained portfolio/regime_label_quality_summary.json"`
- `"robust mean variance constrained portfolio/regime_portfolio_metrics_summary.json"`
- `"robust mean variance constrained portfolio/report.html"`
- `"robust mean variance constrained portfolio/report.txt"`
- `"robust mean variance constrained portfolio/rolling_factor_betas.html"`
- `"robust mean variance constrained portfolio/rolling_factor_betas_10y.png"`
- `"robust mean variance constrained portfolio/rolling_factor_betas_3y.png"`
- `"robust mean variance constrained portfolio/rolling_factor_betas_5y.png"`
- `"robust mean variance constrained portfolio/run_metadata.json"`
- `"robust mean variance constrained portfolio/scenario_library.json"`
- `"robust mean variance constrained portfolio/scenario_library_normalized.json"`
- `"robust mean variance constrained portfolio/snapshot_10y.json"`
- `"robust mean variance constrained portfolio/snapshot_3y.json"`
- `"robust mean variance constrained portfolio/snapshot_5y.json"`
- `"robust mean variance constrained portfolio/snapshot_assets.json"`
- `"robust mean variance constrained portfolio/snapshot_index.json"`
- `"robust mean variance constrained portfolio/stress_commentary.txt"`
- `"robust mean variance constrained portfolio/stress_report.json"`
- `"robust mean variance constrained portfolio/summary.json"`
- `"robust mean variance constrained portfolio/summary.txt"`
- `"robust mean variance uncapped portfolio/baseline_weights_metadata.json"`
- `"robust mean variance uncapped portfolio/commentary.txt"`
- `"robust mean variance uncapped portfolio/data_policy.json"`
- `"robust mean variance uncapped portfolio/portfolio_xray.json"`
- `"robust mean variance uncapped portfolio/regime_factor_analytics_summary.json"`
- `"robust mean variance uncapped portfolio/regime_label_quality_summary.json"`
- `"robust mean variance uncapped portfolio/regime_portfolio_metrics_summary.json"`
- `"robust mean variance uncapped portfolio/report.html"`
- `"robust mean variance uncapped portfolio/report.txt"`
- `"robust mean variance uncapped portfolio/rolling_factor_betas.html"`
- `"robust mean variance uncapped portfolio/rolling_factor_betas_10y.png"`
- `"robust mean variance uncapped portfolio/rolling_factor_betas_3y.png"`
- `"robust mean variance uncapped portfolio/rolling_factor_betas_5y.png"`
- `"robust mean variance uncapped portfolio/run_metadata.json"`
- `"robust mean variance uncapped portfolio/scenario_library.json"`
- `"robust mean variance uncapped portfolio/scenario_library_normalized.json"`
- `"robust mean variance uncapped portfolio/snapshot_10y.json"`
- `"robust mean variance uncapped portfolio/snapshot_3y.json"`
- `"robust mean variance uncapped portfolio/snapshot_5y.json"`
- `"robust mean variance uncapped portfolio/snapshot_assets.json"`
- `"robust mean variance uncapped portfolio/snapshot_index.json"`
- `"robust mean variance uncapped portfolio/stress_commentary.txt"`
- `"robust mean variance uncapped portfolio/stress_report.json"`
- `"robust mean variance uncapped portfolio/summary.json"`
- `"robust mean variance uncapped portfolio/summary.txt"`
- `candidate_factory_session9_smoke.log`
- `candidate_factory_stderr.log`
- `candidate_factory_stdout.log`
- `config.yml`
- `config.yml.example`
- `docs/audits/README.md`
- `docs/exec_plans/README.md`
- `portfolio_review_stderr.log`
- `portfolio_review_stdout.log`
- `requirements.txt`
- `run_ibkr_market_data.py`
- `src/__pycache__/__init__.cpython-313.pyc`
- `src/__pycache__/cache.cpython-313.pyc`
- `src/__pycache__/client_profiles.cpython-313.pyc`
- `src/__pycache__/config.cpython-313.pyc`
- `src/__pycache__/config_schema.cpython-313.pyc`
- `src/__pycache__/data_ecb.cpython-313.pyc`
- `src/__pycache__/data_fred.cpython-313.pyc`
- `src/__pycache__/data_yf.cpython-313.pyc`
- `src/__pycache__/fx.cpython-313.pyc`
- `src/__pycache__/io_export.cpython-313.pyc`
- `src/__pycache__/metrics_asset.cpython-313.pyc`
- `src/__pycache__/metrics_portfolio.cpython-313.pyc`
- `src/__pycache__/portfolio_dynamic.cpython-313.pyc`
- `src/__pycache__/resample.cpython-313.pyc`
- `src/__pycache__/returns.cpython-313.pyc`
- `src/__pycache__/risk_contrib.cpython-313.pyc`
- `src/__pycache__/stress.cpython-313.pyc`
- `src/__pycache__/utils.cpython-313.pyc`
- `src/__pycache__/windows.cpython-313.pyc`
- `src/action_engine.py`
- `src/cache.py`
- `src/config_schema.py`
- `src/data_ibkr.py`
- `src/data_loader.py`
- `src/data_provider.py`
- `src/data_trust_signals.py`
- `src/live_core_e2e.py`
- `src/selection_engine.py`
- `tests/test_data_cache_key.py`
- `tests/test_data_ibkr.py`
- `tests/test_data_provider.py`

## Config / Environment Review Notes

| Path | Classification | Recommendation |
| --- | --- | --- |
| `config.yml` | Config/environment changes | Local runtime config; do not commit unless intentionally changing project defaults and secrets/local values are reviewed. |
| `config.yml.example` | Config/environment changes | Example config can be committed only if the change is intentional and documented; otherwise revert or split. |
| `requirements.txt` | Config/environment changes | Review dependency diff separately; likely related to data-provider/IBKR or environment work, not the Portfolio MRI migration core. |

## Remaining Blocker Fix Plan

### 1. `scripts/verify_docs.py` fails on archive links

- Likely cause: archived legacy file `docs/archive/documentation_migration_2026_05_25/LEGACY_DIAGNOSTIC_PRODUCT_CONCEPT.md` contains relative links that no longer resolve from the archive location.
- Safest fix direction: separate archive-link cleanup session. Either adjust archive-relative links, mark archive docs as exempt in the verifier, or replace links with explicit archive notes according to project documentation policy.
- Files likely affected: `docs/archive/documentation_migration_2026_05_25/LEGACY_DIAGNOSTIC_PRODUCT_CONCEPT.md`, possibly `scripts/verify_docs.py` only if the accepted policy is to ignore archived legacy docs.
- What not to touch: active product docs, formulas, specs unrelated to archive links, generated outputs.
- Verification command: `./.venv/Scripts/python.exe scripts/verify_docs.py` (PowerShell: `& '.\.venv\Scripts\python.exe' scripts\verify_docs.py`).

### 2. `test_analysis_subject_materialization` tries to pull FRED/yfinance in sandbox

- Likely cause: `run_materialize_analysis_subject_report()` now prepares or reaches `ReviewRunContext` / shared data loading before the test monkeypatch fully isolates network-backed data loaders. In the sandbox, FRED/yfinance socket access is blocked, and `pandas_datareader` also has a Python 3.12 `distutils` issue.
- Safest fix direction: separate test-stabilization session. Mock `prepare_review_run_context` / data loading in `tests/test_analysis_subject_materialization.py`, or add a test-only no-network path around the materialization helper without changing production formulas.
- Files likely affected: `tests/test_analysis_subject_materialization.py`; possibly a tiny injectable seam in `run_report.py` only if test monkeypatching cannot isolate the dependency.
- What not to touch: `src/data_fred.py`, `src/data_yf.py`, metric formulas, cache semantics, production provider behavior.
- Verification command: `& '.\.venv\Scripts\python.exe' -m pytest tests\test_analysis_subject_materialization.py -q --basetemp='tmp\pytest_analysis_subject_materialization_fix'`.

### 3. `test_candidate_factory_contract` has golden `options_keys` drift

- Likely cause: candidate factory runtime added option keys such as `output_profile`, `parallel_lightweight_reports`, and `lightweight_report_workers`, while the committed golden fixture or normalization expectation still reflects an older options surface.
- Safest fix direction: separate golden-contract session. Inspect whether the current options keys are intentional; if yes, update the golden fixture and contract expectation deliberately. If not, restore the intended factory output contract without changing runtime behavior casually.
- Files likely affected: `tests/fixtures/candidate_factory_run_golden_v1.json`, `tests/candidate_factory_golden_inputs.py`, `tests/test_candidate_factory_contract.py`; possibly `src/candidate_factory.py` only if the output keys are not intended.
- What not to touch: candidate builder formulas, optimizer math, candidate output folders, generated report artifacts.
- Verification command: `& '.\.venv\Scripts\python.exe' -m pytest tests\test_candidate_factory_contract.py -q --basetemp='tmp\pytest_candidate_factory_contract_fix'`.

## Next Recommended Session

Run a focused **dirty-tree cleanup staging-prep session** after human review of this report. The first practical step should be to split the migration changes from generated/config/unrelated changes using explicit path lists, not `git add -A`. After that, run separate blocker-fix sessions for archive links, no-network materialization tests, and candidate-factory golden drift.

## Raw `git diff --name-only`

```text
OUTPUTS.md
SPEC.md
config.yml
config.yml.example
docs/audits/README.md
docs/exec_plans/README.md
docs/specs/README.md
docs/specs/candidate_factory_spec.md
docs/specs/portfolio_review_workflow_spec.md
hierarchical risk parity portfolio/baseline_weights_metadata.json
hierarchical risk parity portfolio/commentary.txt
hierarchical risk parity portfolio/data_policy.json
hierarchical risk parity portfolio/drawdown_structure_3y.json
hierarchical risk parity portfolio/portfolio_xray.json
hierarchical risk parity portfolio/regime_factor_analytics_summary.json
hierarchical risk parity portfolio/regime_label_quality_summary.json
hierarchical risk parity portfolio/regime_portfolio_metrics_summary.json
hierarchical risk parity portfolio/report.html
hierarchical risk parity portfolio/report.txt
hierarchical risk parity portfolio/rolling_factor_betas.html
hierarchical risk parity portfolio/rolling_factor_betas_10y.png
hierarchical risk parity portfolio/rolling_factor_betas_3y.png
hierarchical risk parity portfolio/rolling_factor_betas_5y.png
hierarchical risk parity portfolio/run_metadata.json
hierarchical risk parity portfolio/scenario_library.json
hierarchical risk parity portfolio/scenario_library_normalized.json
hierarchical risk parity portfolio/snapshot_10y.json
hierarchical risk parity portfolio/snapshot_3y.json
hierarchical risk parity portfolio/snapshot_5y.json
hierarchical risk parity portfolio/snapshot_assets.json
hierarchical risk parity portfolio/snapshot_index.json
hierarchical risk parity portfolio/stress_commentary.txt
hierarchical risk parity portfolio/stress_report.json
hierarchical risk parity portfolio/summary.json
hierarchical risk parity portfolio/summary.txt
hierarchical risk parity portfolio/weights.json
hierarchical risk parity portfolio/weights.txt
maximum diversification unconstrained portfolio/baseline_weights_metadata.json
maximum diversification unconstrained portfolio/commentary.txt
maximum diversification unconstrained portfolio/data_policy.json
maximum diversification unconstrained portfolio/drawdown_structure_10y.json
maximum diversification unconstrained portfolio/drawdown_structure_5y.json
maximum diversification unconstrained portfolio/portfolio_xray.json
maximum diversification unconstrained portfolio/regime_factor_analytics_summary.json
maximum diversification unconstrained portfolio/regime_label_quality_summary.json
maximum diversification unconstrained portfolio/regime_portfolio_metrics_summary.json
maximum diversification unconstrained portfolio/report.html
maximum diversification unconstrained portfolio/report.txt
maximum diversification unconstrained portfolio/rolling_factor_betas.html
maximum diversification unconstrained portfolio/rolling_factor_betas_10y.png
maximum diversification unconstrained portfolio/rolling_factor_betas_3y.png
maximum diversification unconstrained portfolio/rolling_factor_betas_5y.png
maximum diversification unconstrained portfolio/run_metadata.json
maximum diversification unconstrained portfolio/scenario_library.json
maximum diversification unconstrained portfolio/scenario_library_normalized.json
maximum diversification unconstrained portfolio/snapshot_10y.json
maximum diversification unconstrained portfolio/snapshot_3y.json
maximum diversification unconstrained portfolio/snapshot_5y.json
maximum diversification unconstrained portfolio/snapshot_assets.json
maximum diversification unconstrained portfolio/snapshot_index.json
maximum diversification unconstrained portfolio/stress_commentary.txt
maximum diversification unconstrained portfolio/stress_report.json
maximum diversification unconstrained portfolio/summary.json
maximum diversification unconstrained portfolio/summary.txt
maximum diversification unconstrained portfolio/weights.json
maximum diversification unconstrained portfolio/weights.txt
minimum cvar constrained portfolio/baseline_weights_metadata.json
minimum cvar constrained portfolio/commentary.txt
minimum cvar constrained portfolio/data_policy.json
minimum cvar constrained portfolio/portfolio_xray.json
minimum cvar constrained portfolio/regime_factor_analytics_summary.json
minimum cvar constrained portfolio/regime_label_quality_summary.json
minimum cvar constrained portfolio/regime_portfolio_metrics_summary.json
minimum cvar constrained portfolio/report.html
minimum cvar constrained portfolio/report.txt
minimum cvar constrained portfolio/rolling_factor_betas.html
minimum cvar constrained portfolio/rolling_factor_betas_10y.png
minimum cvar constrained portfolio/rolling_factor_betas_3y.png
minimum cvar constrained portfolio/rolling_factor_betas_5y.png
minimum cvar constrained portfolio/run_metadata.json
minimum cvar constrained portfolio/scenario_library.json
minimum cvar constrained portfolio/scenario_library_normalized.json
minimum cvar constrained portfolio/snapshot_10y.json
minimum cvar constrained portfolio/snapshot_3y.json
minimum cvar constrained portfolio/snapshot_5y.json
minimum cvar constrained portfolio/snapshot_assets.json
minimum cvar constrained portfolio/snapshot_index.json
minimum cvar constrained portfolio/stress_commentary.txt
minimum cvar constrained portfolio/stress_report.json
minimum cvar constrained portfolio/summary.json
minimum cvar constrained portfolio/summary.txt
minimum cvar uncapped portfolio/baseline_weights_metadata.json
minimum cvar uncapped portfolio/commentary.txt
minimum cvar uncapped portfolio/data_policy.json
minimum cvar uncapped portfolio/portfolio_xray.json
minimum cvar uncapped portfolio/regime_factor_analytics_summary.json
minimum cvar uncapped portfolio/regime_label_quality_summary.json
minimum cvar uncapped portfolio/regime_portfolio_metrics_summary.json
minimum cvar uncapped portfolio/report.html
minimum cvar uncapped portfolio/report.txt
minimum cvar uncapped portfolio/rolling_factor_betas.html
minimum cvar uncapped portfolio/rolling_factor_betas_10y.png
minimum cvar uncapped portfolio/rolling_factor_betas_3y.png
minimum cvar uncapped portfolio/rolling_factor_betas_5y.png
minimum cvar uncapped portfolio/run_metadata.json
minimum cvar uncapped portfolio/scenario_library.json
minimum cvar uncapped portfolio/scenario_library_normalized.json
minimum cvar uncapped portfolio/snapshot_10y.json
minimum cvar uncapped portfolio/snapshot_3y.json
minimum cvar uncapped portfolio/snapshot_5y.json
minimum cvar uncapped portfolio/snapshot_assets.json
minimum cvar uncapped portfolio/snapshot_index.json
minimum cvar uncapped portfolio/stress_commentary.txt
minimum cvar uncapped portfolio/stress_report.json
minimum cvar uncapped portfolio/summary.json
minimum cvar uncapped portfolio/summary.txt
pdf files/Main portfolio_commentary.pdf
pdf files/Main portfolio_decision_package.pdf
pdf files/Main portfolio_ew_rp_comparison.pdf
pdf files/Main portfolio_ips_summary.pdf
pdf files/Main portfolio_stress_commentary.pdf
pdf files/Main portfolio_weights.pdf
pdf files/equal-weight_portfolio_commentary.pdf
pdf files/equal-weight_portfolio_stress_commentary.pdf
pdf files/equal-weight_portfolio_weights.pdf
pdf files/maximum_diversification_portfolio_commentary.pdf
pdf files/maximum_diversification_portfolio_stress_commentary.pdf
pdf files/maximum_diversification_portfolio_weights.pdf
pdf files/minimum_cvar_constrained_portfolio_commentary.pdf
pdf files/minimum_cvar_constrained_portfolio_stress_commentary.pdf
pdf files/minimum_cvar_constrained_portfolio_weights.pdf
pdf files/minimum_cvar_uncapped_portfolio_commentary.pdf
pdf files/minimum_cvar_uncapped_portfolio_stress_commentary.pdf
pdf files/minimum_cvar_uncapped_portfolio_weights.pdf
pdf files/minimum_variance_advanced_portfolio_commentary.pdf
pdf files/minimum_variance_advanced_portfolio_stress_commentary.pdf
pdf files/minimum_variance_advanced_portfolio_weights.pdf
pdf files/minimum_variance_portfolio_commentary.pdf
pdf files/minimum_variance_portfolio_stress_commentary.pdf
pdf files/minimum_variance_portfolio_weights.pdf
pdf files/minimum_variance_uncapped_portfolio_commentary.pdf
pdf files/minimum_variance_uncapped_portfolio_stress_commentary.pdf
pdf files/minimum_variance_uncapped_portfolio_weights.pdf
pdf files/risk_parity_portfolio_commentary.pdf
pdf files/risk_parity_portfolio_stress_commentary.pdf
pdf files/risk_parity_portfolio_weights.pdf
pdf files/robust_mean_variance_constrained_portfolio_commentary.pdf
pdf files/robust_mean_variance_constrained_portfolio_stress_commentary.pdf
pdf files/robust_mean_variance_constrained_portfolio_weights.pdf
pdf files/robust_mean_variance_uncapped_portfolio_commentary.pdf
pdf files/robust_mean_variance_uncapped_portfolio_stress_commentary.pdf
pdf files/robust_mean_variance_uncapped_portfolio_weights.pdf
pdf_md_sources/Main portfolio__commentary.md
pdf_md_sources/Main portfolio__decision_package.md
pdf_md_sources/Main portfolio__ips_summary.md
pdf_md_sources/Main portfolio__stress_commentary.md
pdf_md_sources/equal-weight portfolio__commentary.md
pdf_md_sources/equal-weight portfolio__stress_commentary.md
pdf_md_sources/maximum diversification portfolio__commentary.md
pdf_md_sources/maximum diversification portfolio__stress_commentary.md
pdf_md_sources/maximum diversification portfolio__weights.md
pdf_md_sources/minimum cvar constrained portfolio__commentary.md
pdf_md_sources/minimum cvar constrained portfolio__stress_commentary.md
pdf_md_sources/minimum cvar uncapped portfolio__commentary.md
pdf_md_sources/minimum cvar uncapped portfolio__stress_commentary.md
pdf_md_sources/minimum variance advanced portfolio__commentary.md
pdf_md_sources/minimum variance advanced portfolio__stress_commentary.md
pdf_md_sources/minimum variance advanced portfolio__weights.md
pdf_md_sources/minimum variance portfolio__commentary.md
pdf_md_sources/minimum variance portfolio__stress_commentary.md
pdf_md_sources/minimum variance portfolio__weights.md
pdf_md_sources/minimum variance uncapped portfolio__commentary.md
pdf_md_sources/minimum variance uncapped portfolio__stress_commentary.md
pdf_md_sources/minimum variance uncapped portfolio__weights.md
pdf_md_sources/risk parity portfolio__commentary.md
pdf_md_sources/risk parity portfolio__stress_commentary.md
pdf_md_sources/robust mean variance constrained portfolio__commentary.md
pdf_md_sources/robust mean variance constrained portfolio__stress_commentary.md
pdf_md_sources/robust mean variance uncapped portfolio__commentary.md
pdf_md_sources/robust mean variance uncapped portfolio__stress_commentary.md
requirements.txt
risk budget by asset portfolio/commentary.txt
risk budget by asset portfolio/data_policy.json
risk budget by asset portfolio/portfolio_xray.json
risk budget by asset portfolio/regime_factor_analytics_summary.json
risk budget by asset portfolio/regime_label_quality_summary.json
risk budget by asset portfolio/regime_portfolio_metrics_summary.json
risk budget by asset portfolio/report.html
risk budget by asset portfolio/report.txt
risk budget by asset portfolio/rolling_factor_betas.html
risk budget by asset portfolio/rolling_factor_betas_10y.png
risk budget by asset portfolio/rolling_factor_betas_3y.png
risk budget by asset portfolio/rolling_factor_betas_5y.png
risk budget by asset portfolio/run_metadata.json
risk budget by asset portfolio/scenario_library.json
risk budget by asset portfolio/scenario_library_normalized.json
risk budget by asset portfolio/snapshot_10y.json
risk budget by asset portfolio/snapshot_3y.json
risk budget by asset portfolio/snapshot_5y.json
risk budget by asset portfolio/snapshot_assets.json
risk budget by asset portfolio/snapshot_index.json
risk budget by asset portfolio/stress_commentary.txt
risk budget by asset portfolio/stress_report.json
risk budget by asset portfolio/summary.json
risk budget by asset portfolio/summary.txt
risk budget by asset-class portfolio/commentary.txt
risk budget by asset-class portfolio/data_policy.json
risk budget by asset-class portfolio/portfolio_xray.json
risk budget by asset-class portfolio/regime_factor_analytics_summary.json
risk budget by asset-class portfolio/regime_label_quality_summary.json
risk budget by asset-class portfolio/regime_portfolio_metrics_summary.json
risk budget by asset-class portfolio/report.html
risk budget by asset-class portfolio/report.txt
risk budget by asset-class portfolio/rolling_factor_betas.html
risk budget by asset-class portfolio/rolling_factor_betas_10y.png
risk budget by asset-class portfolio/rolling_factor_betas_3y.png
risk budget by asset-class portfolio/rolling_factor_betas_5y.png
risk budget by asset-class portfolio/run_metadata.json
risk budget by asset-class portfolio/scenario_library.json
risk budget by asset-class portfolio/scenario_library_normalized.json
risk budget by asset-class portfolio/snapshot_10y.json
risk budget by asset-class portfolio/snapshot_3y.json
risk budget by asset-class portfolio/snapshot_5y.json
risk budget by asset-class portfolio/snapshot_assets.json
risk budget by asset-class portfolio/snapshot_index.json
risk budget by asset-class portfolio/stress_commentary.txt
risk budget by asset-class portfolio/stress_report.json
risk budget by asset-class portfolio/summary.json
risk budget by asset-class portfolio/summary.txt
robust mean variance constrained portfolio/baseline_weights_metadata.json
robust mean variance constrained portfolio/commentary.txt
robust mean variance constrained portfolio/data_policy.json
robust mean variance constrained portfolio/portfolio_xray.json
robust mean variance constrained portfolio/regime_factor_analytics_summary.json
robust mean variance constrained portfolio/regime_label_quality_summary.json
robust mean variance constrained portfolio/regime_portfolio_metrics_summary.json
robust mean variance constrained portfolio/report.html
robust mean variance constrained portfolio/report.txt
robust mean variance constrained portfolio/rolling_factor_betas.html
robust mean variance constrained portfolio/rolling_factor_betas_10y.png
robust mean variance constrained portfolio/rolling_factor_betas_3y.png
robust mean variance constrained portfolio/rolling_factor_betas_5y.png
robust mean variance constrained portfolio/run_metadata.json
robust mean variance constrained portfolio/scenario_library.json
robust mean variance constrained portfolio/scenario_library_normalized.json
robust mean variance constrained portfolio/snapshot_10y.json
robust mean variance constrained portfolio/snapshot_3y.json
robust mean variance constrained portfolio/snapshot_5y.json
robust mean variance constrained portfolio/snapshot_assets.json
robust mean variance constrained portfolio/snapshot_index.json
robust mean variance constrained portfolio/stress_commentary.txt
robust mean variance constrained portfolio/stress_report.json
robust mean variance constrained portfolio/summary.json
robust mean variance constrained portfolio/summary.txt
robust mean variance uncapped portfolio/baseline_weights_metadata.json
robust mean variance uncapped portfolio/commentary.txt
robust mean variance uncapped portfolio/data_policy.json
robust mean variance uncapped portfolio/portfolio_xray.json
robust mean variance uncapped portfolio/regime_factor_analytics_summary.json
robust mean variance uncapped portfolio/regime_label_quality_summary.json
robust mean variance uncapped portfolio/regime_portfolio_metrics_summary.json
robust mean variance uncapped portfolio/report.html
robust mean variance uncapped portfolio/report.txt
robust mean variance uncapped portfolio/rolling_factor_betas.html
robust mean variance uncapped portfolio/rolling_factor_betas_10y.png
robust mean variance uncapped portfolio/rolling_factor_betas_3y.png
robust mean variance uncapped portfolio/rolling_factor_betas_5y.png
robust mean variance uncapped portfolio/run_metadata.json
robust mean variance uncapped portfolio/scenario_library.json
robust mean variance uncapped portfolio/scenario_library_normalized.json
robust mean variance uncapped portfolio/snapshot_10y.json
robust mean variance uncapped portfolio/snapshot_3y.json
robust mean variance uncapped portfolio/snapshot_5y.json
robust mean variance uncapped portfolio/snapshot_assets.json
robust mean variance uncapped portfolio/snapshot_index.json
robust mean variance uncapped portfolio/stress_commentary.txt
robust mean variance uncapped portfolio/stress_report.json
robust mean variance uncapped portfolio/summary.json
robust mean variance uncapped portfolio/summary.txt
run_report.py
src/__pycache__/__init__.cpython-313.pyc
src/__pycache__/cache.cpython-313.pyc
src/__pycache__/client_profiles.cpython-313.pyc
src/__pycache__/config.cpython-313.pyc
src/__pycache__/config_schema.cpython-313.pyc
src/__pycache__/data_ecb.cpython-313.pyc
src/__pycache__/data_fred.cpython-313.pyc
src/__pycache__/data_yf.cpython-313.pyc
src/__pycache__/fx.cpython-313.pyc
src/__pycache__/io_export.cpython-313.pyc
src/__pycache__/metrics_asset.cpython-313.pyc
src/__pycache__/metrics_portfolio.cpython-313.pyc
src/__pycache__/portfolio_dynamic.cpython-313.pyc
src/__pycache__/resample.cpython-313.pyc
src/__pycache__/returns.cpython-313.pyc
src/__pycache__/risk_contrib.cpython-313.pyc
src/__pycache__/stress.cpython-313.pyc
src/__pycache__/utils.cpython-313.pyc
src/__pycache__/windows.cpython-313.pyc
src/cache.py
src/candidate_comparison.py
src/candidate_factory.py
src/config_schema.py
src/data_loader.py
src/live_core_e2e.py
src/portfolio_review_workflow.py
tests/test_candidate_factory.py
tests/test_data_cache_key.py
tests/test_portfolio_review_workflow.py
```

## Raw `git diff --cached --name-only`

```text
(empty)
```
