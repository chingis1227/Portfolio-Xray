# SPEC.md

This file is a short index for product behavior and implementation specs. Do not duplicate formulas or detailed rules here; update the linked source document instead.

## Canonical Specs

| Area | Source |
| --- | --- |
| Portfolio construction, optimizer behavior, ProLiquidity, mandate gate, RC_vol role | [docs/portfolio_construction_policy.md](docs/portfolio_construction_policy.md) |
| Metrics formulas, dates, windows, returns, FX, covariance, RC_vol, beta, stress metrics | [metrics_specification.md](metrics_specification.md) |
| Feasibility and weight constraints | [docs/docs/feasibility_constraints_spec.md](docs/docs/feasibility_constraints_spec.md) |
| Stress testing scenarios, diagnostics, failure/warning codes | [docs/docs/stress_testing_spec.md](docs/docs/stress_testing_spec.md) |
| View After Optimization tactical tilt protocol | [docs/docs/view_after_optimization_spec.md](docs/docs/view_after_optimization_spec.md) |
| Data policy for NaN, young ETFs, and backtest handling | [docs/data_policy_nan_young_etfs.md](docs/data_policy_nan_young_etfs.md) |
| Production workflow and release statuses | [docs/production_workflow.md](docs/production_workflow.md) |

## Expected Product Behavior

- `run_optimization.py` reads `config.yml`, applies `config/client_profiles.yml` when needed, downloads/uses market data, runs the optimizer, applies ProLiquidity, and writes portfolio weights only if the mandate gate allows it.
- `run_report.py` reads optimized weights, computes reports and metrics over the configured windows, and writes CSV/JSON/HTML/text outputs.
- Final weights must come from optimization plus approved post-processing protocols; manual final weights in config are not the normal workflow.

## Output Contract

- Optimized weights and run status are written under `output_dir_final`, usually `Main portfolio/`.
- Tabular metric outputs are written under `output_dir`, usually `results_csv/`.
- Reports and diagnostics must follow the definitions in the linked canonical specs.
- `stress_report.json` factor regression diagnostics follow [docs/docs/stress_testing_spec.md](docs/docs/stress_testing_spec.md), including `idiosyncratic_risk = 1 - r2`, rolling beta stability diagnostics, and Breusch-Pagan heteroskedasticity checks for portfolio factor betas.
- `stress_report.json` factor analytics now include the additional beta keys `beta_vix`, `beta_us_growth`, and `beta_oil` alongside the legacy factor betas. Synthetic stress scenarios remain six-shock diagnostics even though factor analytics now use a nine-factor registry.
- `stress_report.json.historical_results` includes model-based historical factor attribution when factor history is available, using 5Y betas as the primary attribution source. The report must label this as beta times realized factor shock, not a pure realized causal decomposition.
- `stress_report.json.factor_covariance` follows [docs/docs/stress_testing_spec.md](docs/docs/stress_testing_spec.md): it keeps `base`, `stress_empirical`, and `stress_overlay` separate, labels data-driven versus hypothetical metrics, zero-fills missing betas explicitly, and exports factor covariance/correlation, factor RC, overlay delta, beta sensitivity, RC stability, and covariance stability diagnostics.
- `stress_report.json.factor_variance_decomposition` follows [docs/docs/stress_testing_spec.md](docs/docs/stress_testing_spec.md): it uses 5Y weekly OLS rows only, fixes `variance_scale=weekly`, normalizes factor RC against `b' Sigma_f b` before R2 scaling, preserves net and gross views, splits risk adders from hedgers, reports residual severity, performs a mandatory R2 cross-check, and exports `factor_variance_decomposition_5y.csv`.
