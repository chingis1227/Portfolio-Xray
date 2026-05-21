# TESTING.md

This file is the quality and verification framework for Portfolio X-Ray & Optimization Terminal / Portfolio MRI.

It defines what to verify for different change types, which risks the checks cover, when focused `pytest` is enough, when CLI smoke runs are needed, and when generated artifacts or Markdown links must be inspected. It does not define formulas, scenarios, optimizer policy, or data rules; those remain in `SPEC.md`, `DATA.md`, and `docs/specs/`.

Update this file when test strategy, required checks, verification commands, regression coverage, or quality gates change.

## Core Rule

Verify the changed risk, not just the changed file.

Use the narrowest reliable check first. Broaden only when the change touches shared math, data alignment, optimizer behavior, config/schema, stress logic, report exports, or generated artifact contracts.

## Verification Levels

| Level | Use when | Commands or checks |
| --- | --- | --- |
| Focused unit/regression test | One module or behavior changed | `python -m pytest tests/test_name.py -q` |
| Adjacent focused suite | Change touches shared helpers or nearby behavior | Run multiple related `tests/test_*.py` files together |
| Full pytest | Shared math, optimizer, data, stress, config, or report contracts may regress | `python -m pytest` |
| CLI smoke run | Entrypoint behavior, generated outputs, or end-to-end flow changed | `python run_portfolio_review.py`, `python run_report.py`, legacy `python run_optimization.py`, or the affected `run_*.py` |
| Artifact inspection | JSON/CSV/HTML/TXT/PDF-style output shape or content changed | Inspect relevant files under `Main portfolio/`, `results_csv/`, variant folders, or `pdf files/` |
| Documentation verification | Docs, links, commands, renamed files, or source-of-truth maps changed | `python scripts/verify_docs.py` or `python -m pytest tests/test_docs_links.py -q`; add `rg` stale-reference searches when renaming removed fields |
| Generated-output language QA | Representative report/PDF text artifacts regenerated or language/story rules touched | `python scripts/scan_generated_outputs.py` and `python -m pytest tests/test_generated_output_language.py -q`; portfolio-first summaries must keep `Starting portfolio` and `Candidate alternatives` markers |
| Offline MVP pipeline smoke | File-first decision chain (comparison through decision package) or cross-module orchestration regressions | `python -m pytest tests/test_mvp_pipeline_offline.py -q` |
| Portfolio-first offline E2E smoke | Portfolio-first subject diagnostics, comparison, and decision package regressions across subject types | `python -m pytest tests/test_portfolio_first_e2e_offline.py -q` |
| Portfolio-first workflow orchestration | `run_portfolio_review.py` plan building or step ordering | `python -m pytest tests/test_portfolio_review_workflow.py -q` |
| MVP workflow orchestration | `run_mvp_workflow.py` plan building or step ordering | `python -m pytest tests/test_mvp_workflow.py -q` |

`pytest.ini` limits test discovery to `tests/`, so `python -m pytest` is the repository-level test command.

## Offline MVP Pipeline Smoke

Use this when touching `write_candidate_comparison_outputs`, selection/action/monitoring/journal writers, or any step in the file-first decision chain that feeds `decision_package_summary.json`.

The smoke test is fully offline:

- seeds synthetic `snapshot_10y.json` inputs for policy and legacy comparison variants;
- validates config input (in-memory and YAML);
- runs `write_candidate_comparison_outputs` through comparison, health/robustness, selection, action, monitoring, journal, and decision-package writers;
- blocks `src.data_yf.download_all` and `src.data_fred.fetch_fred_series` so live network access fails the test.

Command (prefer a workspace-local basetemp on Windows desktops):

```bash
python -m pytest tests/test_mvp_pipeline_offline.py -q --basetemp='tmp/pytest_mvp_offline'
```

Fixtures live in `tests/mvp_offline_fixtures.py`. This does not replace CLI smoke runs of
`run_portfolio_review.py`, `run_report.py`, or legacy `run_optimization.py` when data download,
stress, or full report exports change.

## Portfolio-First Offline E2E Smoke

Use this when touching `analysis_subject` resolution/materialization, `run_portfolio_review.py`
ordering, subject-centered candidate comparison, Selection/No-Trade, Action, Monitoring, Journal, or
decision-package reporting.

The smoke test is fully offline:

- seeds synthetic `{output_dir_final}/analysis_subject/` snapshots and metadata for
  `current_portfolio`, `model_portfolio`, and `universe_baseline`;
- seeds synthetic candidate snapshots for allowed non-policy alternatives;
- validates the `run_portfolio_review.py` plan materializes subject diagnostics before candidates and
  does not include `run_optimization.py`;
- runs `write_candidate_comparison_outputs` through comparison, scorecards, Selection, Action,
  Monitoring, Journal, and decision-package writers;
- blocks `src.data_yf.download_all` and `src.data_fred.fetch_fred_series` so live network access
  fails the test.

Command:

```bash
python -m pytest tests/test_portfolio_first_e2e_offline.py -q --basetemp='tmp/pytest_portfolio_first_e2e'
```

## Change-To-Check Matrix

| Change area | Primary risks | Minimum checks | Broaden when |
| --- | --- | --- | --- |
| Data layer | Wrong prices, FX timing, return frequency, NaN alignment, young ETF behavior, benchmark/risk-free gaps | `tests/test_backtest_nan_safe.py`, `tests/test_returns_frequency.py`, `tests/test_young_etfs_dual_cov.py`; add `tests/test_historical_stress_fallback.py` when historical fallback changes | Run `python run_report.py --backtest-mode dynamic_nan_safe` if data flow or generated report inputs change |
| Portfolio metrics | Formula drift, wrong annualization, bad windows, rounding too early, beta/covariance alignment errors | Relevant focused tests around affected outputs, commonly `tests/test_metrics_drawdown.py`, `tests/test_returns_frequency.py`, `tests/test_backtest_nan_safe.py`, `tests/test_regime_portfolio_metrics.py`, `tests/test_portfolio_pca.py`, `tests/test_portfolio_commentary.py` | Run full pytest when shared metric helpers, windows, covariance, risk-free, FX, or report metric exports change |
| Optimizer / constraints | Infeasible weights, wrong bounds, broken mandate gate, changed release semantics, baseline drift | `tests/test_optimization_fallback.py`, `tests/test_config_weights_sync.py`, `tests/test_resampled_optimization_helpers.py`, `tests/test_young_etfs_dual_cov.py`; add affected baseline tests such as `tests/test_minimum_variance_baseline.py`, `tests/test_maximum_diversification_baseline.py`, `tests/test_minimum_cvar_baseline.py`, `tests/test_risk_parity_baseline.py`, `tests/test_risk_budgeting.py`, `tests/test_hrp_weights.py`, `tests/test_robust_mean_variance.py`, or `tests/test_robust_mv_calibration.py` | Run `python run_optimization.py` when main policy optimization, release status, or output files change |
| Stress scenarios | Scenario PnL drift, mandate/stress boundary confusion, missing historical fields, bad covariance taxonomy, changed diagnostic-only behavior | Stress Lab wave bundle (see above): `tests/test_stress_mandate_pass.py`, `tests/test_stress_historical_fields.py`, `tests/test_stress_covariance_taxonomy.py`, `tests/test_stress_scenario_analytics.py`, plus scorecard/hedge-gap/coverage/synthetic/simulator/artifacts/commentary contract tests | Run `python run_report.py --materialize-analysis-subject` if `stress_report.json`, stress CSVs, or commentary output changes |
| Factor / macro analytics | Factor matrix drift, regression diagnostics broken, macro regime label instability, publication-lag mistakes, diagnostic blocks affecting policy | Factor tests: `tests/test_factor_matrix_builders.py`, `tests/test_factor_beta_stability.py`, `tests/test_factor_beta_adjusted_overlay.py`, `tests/test_factor_beta_kalman.py`, `tests/test_factor_covariance.py`, `tests/test_factor_oos_explainability.py`, `tests/test_factor_regression_hac.py`, `tests/test_factor_regression_heteroskedasticity.py`, `tests/test_factor_regression_serial.py`, `tests/test_factor_variance_decomposition.py`; macro tests: `tests/test_macro_regimes.py`, `tests/test_macro_primary_regime.py`, `tests/test_macro_indicators.py`, `tests/test_macro_scoring_modes.py`, `tests/test_macro_source_resolver.py`, `tests/test_macro_regime_label_quality.py`, `tests/test_macro_neutral_band_sensitivity.py`; regime tests: `tests/test_regime_factor_analytics.py`, `tests/test_regime_portfolio_metrics.py` | Run full pytest and `python run_report.py` when exported `stress_report.json` blocks or CSV artifacts change |
| Reports / outputs | Broken JSON/CSV schema, missing commentary, bad report rendering, stale generated files, changed user-facing artifacts | Portfolio X-Ray wave bundle (see below) when `portfolio_xray.json` or X-Ray report surfaces change; otherwise `tests/test_portfolio_commentary.py` plus affected output tests such as `tests/test_scenario_library.py`, `tests/test_scenario_library_normalized.py`, `tests/test_stress_scenario_analytics.py`, `tests/test_regime_portfolio_metrics.py`, `tests/test_portfolio_pca.py` | Run `python run_report.py`; run `python rebuild_pdf_reports.py` only when PDF rebuild behavior or PDF-style artifacts are the target |
| Config / schema | Invalid config accepted, valid config rejected, config/weights desync, taxonomy validation drift | `tests/test_config_weights_sync.py`, `tests/test_returns_frequency.py`; add `tests/test_etf_universe.py` or `tests/test_stock_universe.py` for taxonomy config changes | Run affected CLI such as `python run_etf_universe.py`, `python run_stock_universe.py`, `python run_optimization.py`, or `python run_report.py` when user-facing config workflows change |
| Documentation-only change | Broken links, stale source-of-truth maps, obsolete commands, copied concept text treated as binding | Markdown link check; stale-reference search with `rg`; no `pytest` required unless executable examples, commands, or documented behavior changed | Run relevant CLI/test command if docs change executable examples or acceptance criteria |

Focused drawdown and time-to-recovery coverage lives in `tests/test_metrics_drawdown.py`. Keep adding targeted regression coverage when changing formulas, windows, annualization, FX, risk-free handling, covariance, beta, drawdown, or rounding.

## CLI Smoke Runs

Run CLI smoke checks when the change affects orchestration, generated outputs, or user-facing workflow.

Common existing entrypoints:

```bash
python run_portfolio_review.py
python run_report.py
python run_optimization.py  # legacy policy compatibility
python run_report.py --backtest-mode dynamic_nan_safe
python run_view_after_optimization.py --asset VOO --delta 2
```

Candidate or robust portfolio changes should use the affected existing `run_*.py` script, for example:

```bash
python run_equal_weight.py
python run_risk_parity.py
python run_minimum_variance.py
python run_maximum_diversification.py
python run_minimum_cvar_constrained.py
python run_robust_mv_lambda_calibration.py
python run_robust_scenario_optimization.py
```

Do not run every candidate script by default. Run the affected entrypoint plus adjacent tests, then broaden only when shared candidate infrastructure changed.

## Stress Lab Wave Regression Bundle

Use this focused bundle after stress-layer contract changes (scorecard, hedge gap, scenario
coverage, synthetic assumptions, crisis replay paths, portfolio-first artifact resolution,
commentary/IPS stress narrative, or custom-shock simulator API). Baseline artifact fingerprints
live in [docs/audits/2026-05-20_stress_lab_baseline_snapshot.md](docs/audits/2026-05-20_stress_lab_baseline_snapshot.md).

## Stress Lab Governance Wave Bundle (Phase 13)

Governance wave (Phase 13, Sessions 01–11) **closed** 2026-05-20 per
[Stress Lab Methodology Governance Plan](docs/exec_plans/2026-05-20_stress_lab_methodology_governance_plan.md).
Methodology baseline (historical):
[docs/audits/2026-05-20_stress_lab_methodology_map.md](docs/audits/2026-05-20_stress_lab_methodology_map.md).
Re-run this bundle after Block 3 contract or downstream integration changes.

```bash
python -m pytest tests/test_stress_scorecard_contract.py tests/test_stress_hedge_gap_contract.py tests/test_stress_scenario_coverage_contract.py tests/test_stress_synthetic_assumptions_contract.py tests/test_stress_simulator_contract.py tests/test_stress_mandate_pass.py tests/test_stress_scenario_analytics.py tests/test_stress_historical_fields.py tests/test_stress_covariance_taxonomy.py tests/test_stress_artifacts_priority.py tests/test_stress_downstream_integration.py tests/test_portfolio_commentary.py tests/test_io_export_ips_summary.py -q
python scripts/verify_docs.py
```

When `stress_report.json` or sibling stress artifacts change intentionally, refresh the
representative subject run and update baseline hashes in the audit snapshot:

```bash
python run_report.py --materialize-analysis-subject
python run_stress_variant.py --variant main
```

## Portfolio X-Ray Wave Regression Bundle

Use this focused bundle after Portfolio X-Ray contract changes (seven-section JSON, risk budget RC
loading, factor/Kalman mapping, hidden-risk V2, weakness map V2, archetype scorecard, or structured
X-Ray report/commentary surfaces). Post-audit Sessions 09–10 (`RM-949`, `RM-950`) add golden JSON
contract tests and the baseline artifact checklist in
[docs/audits/2026-05-20_portfolio_xray_baseline_snapshot.md](docs/audits/2026-05-20_portfolio_xray_baseline_snapshot.md).

```bash
python -m pytest tests/test_portfolio_xray.py tests/test_portfolio_xray_threshold_registry.py tests/test_portfolio_xray_contract.py tests/test_portfolio_metrics_deepening.py tests/test_tail_risk.py tests/test_portfolio_commentary.py -q
python scripts/verify_docs.py
```

## Candidate Factory Governance Wave Bundle (Phase 14)

Governance wave (Phase 14, Sessions 00–11) **closed** 2026-05-20 per
[Candidate Portfolio Factory Post-Audit Roadmap](docs/exec_plans/2026-05-20_candidate_factory_post_audit_roadmap.md).
Methodology baseline:
[docs/audits/2026-05-20_candidate_factory_methodology_map.md](docs/audits/2026-05-20_candidate_factory_methodology_map.md).
Baseline checklist:
[docs/audits/2026-05-20_candidate_factory_baseline_snapshot.md](docs/audits/2026-05-20_candidate_factory_baseline_snapshot.md).

Re-run this bundle after Block 4 factory/comparison contract changes (reason codes, freshness,
`construction_disclosure`, config fingerprint, robust paths, resume manifest, or registry/menu schema):

```bash
python -m pytest tests/test_candidate_factory_contract.py tests/test_candidate_comparison_contract.py tests/test_candidate_factory.py tests/test_candidate_comparison.py tests/test_portfolio_review_workflow.py -q
python scripts/verify_docs.py
```

Golden fixtures (regenerate only after intentional `candidate_factory_run_v1` /
`candidate_comparison_v1` contract changes):

```bash
python tests/candidate_factory_golden_inputs.py
python -m pytest tests/test_candidate_factory_contract.py tests/test_candidate_comparison_contract.py -q
```

Committed fixtures:

- `tests/fixtures/candidate_factory_run_golden_v1.json`
- `tests/fixtures/candidate_comparison_golden_v1.json`

After Session 02+ builder reason mapping, confirm `test_builder_reason_mapping_contract` and
`test_factory_reason_from_builder_summary_mapping` pass in this bundle.

After Session 04+ `construction_disclosure`, confirm comparison disclosure passthrough tests and
`test_golden_comparison_post_audit_surface` (`equal_weight` available, `risk_parity` partial).

After Session 06+ config fingerprint, confirm `test_stale_config_fingerprint_*` and factory
`test_stale_config_fingerprint_rebuilds_same_analysis_end` pass in this bundle.

After Session 07+ robust paths, confirm factory robust disclosure tests and
`test_robust_scenario_construction_disclosure_main_prerequisites` pass in this bundle.

Session 11 wave closure (2026-05-20): governance bundle **77 passed**; family spot-check **19 passed**;
`verify_docs` OK. Phase 14 (`RM-970`–`RM-981`) complete.

When `candidate_factory_run.json` or `candidate_comparison.json` change intentionally on a live
run, refresh baseline fingerprints per
[docs/audits/2026-05-20_candidate_factory_baseline_snapshot.md](docs/audits/2026-05-20_candidate_factory_baseline_snapshot.md):

```bash
python run_portfolio_review.py --mode core
```

## Optimization Engine Governance Wave Bundle (Phase 15)

Governance wave (Phase 15, Sessions 00-12) is **closed** as of 2026-05-21 per
[Optimization Engine Post-Audit Roadmap](docs/exec_plans/2026-05-20_optimization_engine_post_audit_roadmap.md).
Methodology baseline:
[docs/audits/2026-05-20_optimization_engine_methodology_map.md](docs/audits/2026-05-20_optimization_engine_methodology_map.md).
Baseline checklist:
[docs/audits/2026-05-20_optimization_engine_baseline_snapshot.md](docs/audits/2026-05-20_optimization_engine_baseline_snapshot.md).

Session 00 is documentation-only:

```bash
python scripts/verify_docs.py
```

After code or output-contract sessions, run the focused Block 5 bundle:

```bash
python -m pytest tests/test_legacy_policy_optimizer_disclosure.py tests/test_optimization_fallback.py tests/test_config_weights_sync.py tests/test_young_etfs_dual_cov.py -q
python -m pytest tests/test_minimum_variance_baseline.py tests/test_maximum_diversification_baseline.py tests/test_minimum_cvar_baseline.py -q
python -m pytest tests/test_robust_mean_variance.py tests/test_robust_mv_calibration.py tests/test_robust_scenario_optimization.py -q
python -m pytest tests/test_optimization_readiness.py tests/test_optimization_engine_contract.py tests/test_candidate_factory.py tests/test_candidate_comparison.py tests/test_candidate_factory_contract.py tests/test_candidate_comparison_contract.py -q
python scripts/verify_docs.py
```

Golden contract fixtures (Session 11 / `RM-1001`):

```bash
python tests/optimization_engine_golden_inputs.py
python -m pytest tests/test_optimization_engine_contract.py -q
```

- `tests/fixtures/legacy_policy_optimizer_run_metadata_golden_v1.json`
- `tests/fixtures/candidate_optimizer_run_metadata_golden_v1.json`
- `tests/fixtures/optimization_comparison_block5_golden_v1.json`
- **Inputs:** `tests/optimization_engine_golden_inputs.py`
- **Tests:** `tests/test_optimization_engine_contract.py`

Run `python run_optimization.py` only when legacy policy outputs change. Run affected candidate or
robust scripts only when their wrapper/output contract changes. Do not refresh generated artifacts
for commit unless the session explicitly targets generated outputs.

Session 05 comparison-level optimizer disclosure: confirm
`test_optimizer_candidate_methodology_disclosure_from_baseline_metadata` and
`test_policy_optimizer_methodology_disclosure_from_run_result` in `tests/test_candidate_comparison.py`
pass after changes to `construction_disclosure.optimizer_methodology`.

Session 06 fallback/failure policy: confirm
`test_factory_step_surfaces_optimizer_fallback_quality` in `tests/test_candidate_factory.py`,
`test_optimizer_fallback_quality_degrades_comparison_row` and
`test_failed_factory_step_blocks_comparison_row_even_with_snapshot` in
`tests/test_candidate_comparison.py`, and
`test_selection_warns_when_favored_candidate_has_optimizer_fallback` in
`tests/test_selection_engine.py`.

Session 07 robust scenario solver disclosure: confirm
`test_build_inputs_and_optimize_round_trip` in `tests/test_robust_scenario_optimization.py`,
`test_robust_scenario_factory_step_surfaces_solver_quality` in `tests/test_candidate_factory.py`,
and `test_robust_scenario_optimizer_methodology_disclosure` in
`tests/test_candidate_comparison.py`.

Session 08 estimator date/fingerprint disclosure: confirm
`tests/test_legacy_policy_optimizer_disclosure.py`,
`tests/test_minimum_variance_baseline.py`, `tests/test_maximum_diversification_baseline.py`,
`tests/test_minimum_cvar_baseline.py`, and `tests/test_robust_mean_variance.py` cover
`input_fingerprints`, return-panel start/end/row fields, and estimator `analysis_end` propagation.

Session 09 covariance / Young ETF methodology disclosure: confirm
`tests/test_legacy_policy_optimizer_disclosure.py`, `tests/test_minimum_variance_baseline.py`,
`tests/test_robust_mean_variance.py`, `tests/test_candidate_comparison.py`, and
`tests/test_io_export_ips_summary.py` cover `optimizer_covariance_methodology_v1`,
`optimizer_young_etf_methodology_v1`, comparison-level passthrough, and human TXT summaries.

Session 10 optimization comparison readiness: confirm
`tests/test_optimization_readiness.py` and `test_block5_golden_post_audit_surface` in
`tests/test_optimization_engine_contract.py` cover `optimizer_comparison_readiness_v1`,
`fair_comparison_ready`, and Block 5 comparison disclosure keys.

Session 11 golden contracts and governance bundle closure (2026-05-21): Block 5 governance bundle
**159 passed** (`test_optimization_engine_contract.py` 9 tests included in comparison/factory line);
`verify_docs` OK. Regenerate optimizer golden JSON only after intentional disclosure contract changes.

Session 12 wave closure (2026-05-21): Phase 15 **Done** (`RM-990`–`RM-1002`); baseline snapshot,
ROADMAP, ExecPlan register, `KNOWN_ISSUES` Block 5 gap index, `CHANGELOG`; governance bundle
**159 passed**; `verify_docs` OK.

## Artifact Checks

Generated outputs are evidence, not source, unless the task explicitly targets generated artifacts.

Use [OUTPUTS.md](OUTPUTS.md) to identify which generated folders, artifacts, formats, and source-vs-generated boundaries apply.

Inspect artifacts when their schema, existence, naming, or user-facing content is part of the change:

- `portfolio_weights.yml` and `run_result.json` for optimizer release and weights.
- `stress_report.json` for stress, factor, macro, regime, PCA, and scenario diagnostics.
- `scenario_library.json` and `scenario_library_normalized.json` for scenario-library changes.
- CSV files under `results_csv/` for tabular diagnostics.
- `commentary.txt` and `stress_commentary.txt` for generated narrative output.
- Generated HTML and PDF-style outputs only when report rendering or PDF rebuild behavior changes.

If a CLI smoke run rewrites generated outputs, do not treat those files as source unless the user explicitly asked to update generated artifacts.

## Documentation Checks

Documentation changes require link and stale-reference verification when they rename files, move docs, add source-of-truth maps, or edit commands.

Minimum checks:

```bash
python scripts/verify_docs.py
python -m pytest tests/test_docs_links.py -q
```

- Search for stale names or removed paths with `rg` (for example `rc_asset_cap_pct` in editable UI surfaces after Session 03).
- Confirm changed command examples are real entrypoints or real test commands.

`scripts/verify_docs.py` scans source Markdown under the repo root, `docs/`, and `.cursor/` agents/rules. It checks local file links (repo-root and file-relative), forbidden stale canonical paths, and that `config_ui` does not reintroduce removed editable fields. Planned future spec filenames listed in `src/docs_verify.py` are allowed until those specs are created.
- Keep [docs/DIAGNOSTIC_PRODUCT_CONCEPT.md](docs/DIAGNOSTIC_PRODUCT_CONCEPT.md) non-binding: ideas from that document do not require code tests unless they are promoted into `SPEC.md`, `DATA.md`, `docs/specs/*.md`, or implementation work.

## Source-Of-Truth Links

- Use [RULES.md](RULES.md) for project-wide principles.
- Use [SPEC.md](SPEC.md) for the current implementation contract.
- Use [docs/specs/portfolio_review_workflow_spec.md](docs/specs/portfolio_review_workflow_spec.md) for
  the portfolio-first `analysis_subject` workflow and legacy policy boundary.
- Use [OUTPUTS.md](OUTPUTS.md) for generated output folders, artifacts, formats, report packaging, and generated-vs-source boundaries.
- Use [DATA.md](DATA.md) for data-layer expectations.
- Use [docs/specs/](docs/specs/README.md) for detailed module behavior.
- Use this file for verification strategy and test selection.
- Use [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for active testing gaps, model limitations, technical debt, and known weak spots.
- Use [AGENTS.md](AGENTS.md) only for agent operating rules and the requirement to follow this file.
