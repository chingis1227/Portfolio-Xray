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
| ETF universe taxonomy, closed enums, duplicate groups, canonical tickers, diagnostics statuses | [docs/etf_universe_spec.md](docs/etf_universe_spec.md) |
| Stock universe taxonomy for current S&P 500 constituents | [docs/stock_universe_spec.md](docs/stock_universe_spec.md) |

## Expected Product Behavior

- `run_optimization.py` reads `config.yml`, applies `config/client_profiles.yml` when needed, downloads/uses market data, runs the optimizer, applies ProLiquidity, and writes portfolio weights only if the mandate gate allows it.
- `run_report.py` reads optimized weights, computes reports and metrics over the configured windows, and writes CSV/JSON/HTML/text outputs.
- Final weights must come from optimization plus approved post-processing protocols; manual final weights in config are not the normal workflow.
- `config/etf_universe.yml` validates and annotates ETF taxonomy for the active config ticker list. V1 diagnostics do not select tickers, do not replace existing optimizer eligibility/data rules, and do not change weights.
- `config/stock_universe.yml` is a separate stock taxonomy source for the current S&P 500 constituent set. V1 is CLI-only, validates and annotates stock metadata, and does not integrate into optimizer/report flows or change weights.

## Output Contract

- Optimized weights and run status are written under `output_dir_final`, usually `Main portfolio/`.
- Tabular metric outputs are written under `output_dir`, usually `results_csv/`.
- Reports and diagnostics must follow the definitions in the linked canonical specs.
- When `config/etf_universe.yml` exists, optimization and report runs write `etf_universe_validation.json` under `output_dir_final` with status `PASS`, `PASS_WITH_WARNINGS`, or `FAIL`.
- `stress_report.json` factor regression diagnostics follow [docs/docs/stress_testing_spec.md](docs/docs/stress_testing_spec.md), including `idiosyncratic_risk = 1 - r2`, rolling beta stability diagnostics, and Breusch-Pagan heteroskedasticity checks for portfolio factor betas.
- Production factor outputs use base factors only: `equity`, `real_rates`, `inflation`, `credit`, `usd`, `commodity`, `vix`, and `us_growth`. `commodity` is the production сырьевой factor.
- Extended diagnostic/stress outputs use base factors plus `oil`. `beta_oil` is deprecated and removed from new production beta outputs; Oil exposure is read from `diagnostic_oil_beta` or stress-layer metrics.
- `stress_report.json.factor_betas_kalman` follows [docs/docs/stress_testing_spec.md](docs/docs/stress_testing_spec.md): it adds diagnostic-only time-varying weekly Kalman betas with capped reported values, uncapped latest values, Kalman-vs-5Y divergence flags, state uncertainty classes, and CSV exports `kalman_factor_betas_weekly.csv` / `kalman_factor_betas_latest.csv`.
- `stress_report.json` includes a diagnostic-only stability-adjusted beta overlay (`factor_betas_adjusted`, `synthetic_factor_pnl_adjusted`, `factor_beta_shock_oos_adjusted`, `raw_vs_adjusted_pnl_signal`) that shrinks unstable 5Y betas toward 10Y anchors, flags strong 5Y-vs-10Y divergence, and reports material raw-vs-adjusted factor-model PnL deltas without changing the primary raw stress path. Production adjusted beta maps exclude Oil.
- `stress_report.json.historical_results` includes model-based historical factor attribution when factor history is available, using 5Y betas as the primary attribution source. The same rows may carry parallel adjusted attribution fields with `_adjusted` suffixes. The report must label both as beta times realized factor shock, not a pure realized causal decomposition.
- `stress_report.json.factor_covariance` follows [docs/docs/stress_testing_spec.md](docs/docs/stress_testing_spec.md): it keeps `base`, `stress_empirical`, and `stress_overlay` separate, labels data-driven versus hypothetical metrics, zero-fills missing betas explicitly, and exports factor covariance/correlation, factor RC, overlay delta, beta sensitivity, RC stability, covariance stability, and covariance forecast-quality diagnostics.
- `stress_report.json.factor_variance_decomposition` follows [docs/docs/stress_testing_spec.md](docs/docs/stress_testing_spec.md): it uses 5Y weekly base-factor OLS rows only, fixes `variance_scale=weekly`, normalizes factor RC against `b' Sigma_f b` before R2 scaling, preserves net and gross views, splits risk adders from hedgers, reports residual severity, performs a mandatory R2 cross-check, and exports `factor_variance_decomposition_5y.csv`.
- `stress_report.json.portfolio_pca` follows [docs/docs/stress_testing_spec.md](docs/docs/stress_testing_spec.md): it uses 5Y weekly adjusted-close returns for current positive-weight portfolio assets, reports raw and factor-residual PCA, separates covariance PCA (`risk_dominance`) from correlation PCA (`structure`), reports PC1 stability, effective number of bets, and PC1 factor correlations, and exports PCA summary/component/rolling/correlation CSV artifacts.
