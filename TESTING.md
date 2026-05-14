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
| CLI smoke run | Entrypoint behavior, generated outputs, or end-to-end flow changed | `python run_optimization.py`, `python run_report.py`, or the affected `run_*.py` |
| Artifact inspection | JSON/CSV/HTML/TXT/PDF-style output shape or content changed | Inspect relevant files under `Main portfolio/`, `results_csv/`, variant folders, or `pdf files/` |
| Documentation verification | Docs, links, commands, renamed files, or source-of-truth maps changed | Markdown link check plus stale-reference search with `rg` |

`pytest.ini` limits test discovery to `tests/`, so `python -m pytest` is the repository-level test command.

## Change-To-Check Matrix

| Change area | Primary risks | Minimum checks | Broaden when |
| --- | --- | --- | --- |
| Data layer | Wrong prices, FX timing, return frequency, NaN alignment, young ETF behavior, benchmark/risk-free gaps | `tests/test_backtest_nan_safe.py`, `tests/test_returns_frequency.py`, `tests/test_young_etfs_dual_cov.py`; add `tests/test_historical_stress_fallback.py` when historical fallback changes | Run `python run_report.py --backtest-mode dynamic_nan_safe` if data flow or generated report inputs change |
| Portfolio metrics | Formula drift, wrong annualization, bad windows, rounding too early, beta/covariance alignment errors | Relevant focused tests around affected outputs, commonly `tests/test_returns_frequency.py`, `tests/test_backtest_nan_safe.py`, `tests/test_regime_portfolio_metrics.py`, `tests/test_portfolio_pca.py`, `tests/test_portfolio_commentary.py` | Run full pytest when shared metric helpers, windows, covariance, risk-free, FX, or report metric exports change |
| Optimizer / constraints | Infeasible weights, wrong bounds, broken mandate gate, changed release semantics, baseline drift | `tests/test_optimization_fallback.py`, `tests/test_config_weights_sync.py`, `tests/test_resampled_optimization_helpers.py`, `tests/test_young_etfs_dual_cov.py`; add affected baseline tests such as `tests/test_minimum_variance_baseline.py`, `tests/test_maximum_diversification_baseline.py`, `tests/test_minimum_cvar_baseline.py`, `tests/test_risk_parity_baseline.py`, `tests/test_risk_budgeting.py`, `tests/test_hrp_weights.py`, `tests/test_robust_mean_variance.py`, or `tests/test_robust_mv_calibration.py` | Run `python run_optimization.py` when main policy optimization, release status, or output files change |
| Stress scenarios | Scenario PnL drift, mandate/stress boundary confusion, missing historical fields, bad covariance taxonomy, changed diagnostic-only behavior | `tests/test_stress_mandate_pass.py`, `tests/test_stress_historical_fields.py`, `tests/test_stress_covariance_taxonomy.py`, `tests/test_stress_scenario_analytics.py` | Run `python run_report.py` if `stress_report.json`, stress CSVs, or commentary output changes |
| Factor / macro analytics | Factor matrix drift, regression diagnostics broken, macro regime label instability, publication-lag mistakes, diagnostic blocks affecting policy | Factor tests: `tests/test_factor_matrix_builders.py`, `tests/test_factor_beta_stability.py`, `tests/test_factor_beta_adjusted_overlay.py`, `tests/test_factor_beta_kalman.py`, `tests/test_factor_covariance.py`, `tests/test_factor_oos_explainability.py`, `tests/test_factor_regression_hac.py`, `tests/test_factor_regression_heteroskedasticity.py`, `tests/test_factor_regression_serial.py`, `tests/test_factor_variance_decomposition.py`; macro tests: `tests/test_macro_regimes.py`, `tests/test_macro_primary_regime.py`, `tests/test_macro_indicators.py`, `tests/test_macro_scoring_modes.py`, `tests/test_macro_source_resolver.py`, `tests/test_macro_regime_label_quality.py`, `tests/test_macro_neutral_band_sensitivity.py`; regime tests: `tests/test_regime_factor_analytics.py`, `tests/test_regime_portfolio_metrics.py` | Run full pytest and `python run_report.py` when exported `stress_report.json` blocks or CSV artifacts change |
| Reports / outputs | Broken JSON/CSV schema, missing commentary, bad report rendering, stale generated files, changed user-facing artifacts | `tests/test_portfolio_commentary.py`, plus affected output tests such as `tests/test_scenario_library.py`, `tests/test_scenario_library_normalized.py`, `tests/test_stress_scenario_analytics.py`, `tests/test_regime_portfolio_metrics.py`, `tests/test_portfolio_pca.py` | Run `python run_report.py`; run `python rebuild_pdf_reports.py` only when PDF rebuild behavior or PDF-style artifacts are the target |
| Config / schema | Invalid config accepted, valid config rejected, config/weights desync, taxonomy validation drift | `tests/test_config_weights_sync.py`, `tests/test_returns_frequency.py`; add `tests/test_etf_universe.py` or `tests/test_stock_universe.py` for taxonomy config changes | Run affected CLI such as `python run_etf_universe.py`, `python run_stock_universe.py`, `python run_optimization.py`, or `python run_report.py` when user-facing config workflows change |
| Documentation-only change | Broken links, stale source-of-truth maps, obsolete commands, copied concept text treated as binding | Markdown link check; stale-reference search with `rg`; no `pytest` required unless executable examples, commands, or documented behavior changed | Run relevant CLI/test command if docs change executable examples or acceptance criteria |

TBD: there is no dedicated repository Markdown link-check command checked in yet. Until one exists, use an equivalent local Markdown link checker and report the exact result.

TBD: portfolio metrics do not have one single named golden-scenario test file. Use the affected focused tests above and add targeted regression coverage when changing formulas, windows, annualization, FX, risk-free handling, covariance, beta, drawdown, or rounding.

## CLI Smoke Runs

Run CLI smoke checks when the change affects orchestration, generated outputs, or user-facing workflow.

Common existing entrypoints:

```bash
python run_optimization.py
python run_report.py
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

## Artifact Checks

Generated outputs are evidence, not source, unless the task explicitly targets generated artifacts.

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

- Search for stale names or removed paths with `rg`.
- Validate relative Markdown links.
- Confirm changed command examples are real entrypoints or real test commands.
- Keep [docs/DIAGNOSTIC_PRODUCT_CONCEPT.md](docs/DIAGNOSTIC_PRODUCT_CONCEPT.md) non-binding: ideas from that document do not require code tests unless they are promoted into `SPEC.md`, `DATA.md`, `docs/specs/*.md`, or implementation work.

## Source-Of-Truth Links

- Use [RULES.md](RULES.md) for project-wide principles.
- Use [SPEC.md](SPEC.md) for the current implementation contract.
- Use [DATA.md](DATA.md) for data-layer expectations.
- Use [docs/specs/](docs/specs/README.md) for detailed module behavior.
- Use this file for verification strategy and test selection.
- Use [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for active testing gaps, model limitations, technical debt, and known weak spots.
- Use [AGENTS.md](AGENTS.md) only for agent operating rules and the requirement to follow this file.
