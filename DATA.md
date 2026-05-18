# DATA.md

This file is the living data-layer map for Portfolio X-Ray & Optimization Terminal / Portfolio MRI.

It explains what data the project uses, where it comes from, what shapes and quality rules are expected, and which files own the detailed behavior. It does not replace detailed specs such as [docs/specs/data_policy_spec.md](docs/specs/data_policy_spec.md), [docs/specs/metrics_specification.md](docs/specs/metrics_specification.md), or [docs/specs/stress_testing_spec.md](docs/specs/stress_testing_spec.md).

Update this file whenever data sources, data structures, the data pipeline, NaN handling, FX logic, benchmark handling, risk-free source, factor/macro inputs, config fields, or data validation rules change.

## Data Layer Purpose

The data layer turns user configuration and external market/macro inputs into consistent analysis panels for optimization, reporting, stress diagnostics, candidate portfolios, and exports.

Analysis setup, input mode, current-weight semantics, mandate inputs, and technical calculation settings are governed by [docs/specs/input_assumptions_spec.md](docs/specs/input_assumptions_spec.md).

The core pipeline is:

```text
config and metadata
-> prices and external series
-> FX-adjusted prices
-> return panels
-> aligned analysis windows
-> optimizer / metrics / stress / reporting inputs
```

The data layer must make data gaps and assumptions visible. It must not silently fabricate returns, rewrite history, or hide degraded input quality.

## Data Used By The Project

Primary data categories:

- Asset prices for portfolio tickers, benchmark tickers, local benchmark proxies, cash proxies, ETFs, stocks, commodities, and other supported instruments.
- FX rates used to convert asset prices into `investor_currency`.
- Risk-free rates used for Sharpe, Sortino, Treynor, excess returns, cash assumptions, and related metrics.
- Benchmark series used for `Beta_base`, local beta diagnostics, correlation, and market exposure diagnostics.
- Factor data used for stress testing, factor betas, factor covariance, factor attribution, PCA-related context, scenario analytics, and regime analytics.
- Macro data used for `macro_regime_diagnostics`.
- Config and metadata files used to define tickers, profiles, taxonomy, cash proxies, risk-free settings, and optional asset metadata.
- Generated report artifacts and cache files, which are outputs, not source data.

## Data Sources

Current external and local source families:

- `yfinance` for adjusted close price data and Yahoo FX tickers.
- FRED through project data helpers for risk-free, macro, and selected factor inputs.
- ECB / FX helpers where configured by the project.
- Official CSV/API/keyed/manual macro sources where supported by the macro source resolver.
- Local YAML config and metadata files.
- Local cache files under `cache/` when cache is enabled.

Future quote-data candidates to evaluate: EODHD as first priority, Tiingo for personal usage only, and Alpaca. These are not active project data sources yet.

Source-specific behavior belongs in the relevant implementation modules and detailed specs. Any new source must document its expected format, frequency, failure mode, and fallback behavior.

## Expected Inputs And Formats

Primary source files:

- `config.yml`: active local analysis config.
- `config.yml.example`: reference config and documented defaults.
- `config/client_profiles.yml`: client profile targets.
- `assets.yml`: optional asset metadata.
- `config/etf_universe.yml`: ETF taxonomy metadata.
- `config/stock_universe.yml`: stock taxonomy metadata.
- `config/historical_stress_proxy_map.yml`: historical stress fallback proxy map and coverage thresholds where used.

Expected runtime structures:

- Prices: time-indexed series or DataFrames by ticker, using adjusted close prices.
- FX series: time-indexed daily series in the orientation required by `src/fx.py`.
- Return panels: time-indexed DataFrames by ticker at the configured analysis frequency.
- Risk-free series: time-indexed series resampled to the required metric/reporting frequency.
- Factor and macro panels: time-indexed DataFrames with explicit frequency, source coverage, and quality metadata where implemented.
- Taxonomy records: structured config rows with canonical tickers, classes, and validation status.

Detailed field schemas are owned by the relevant config schema, taxonomy specs, and module-specific specs.

## Core Data Rules

- Use adjusted close prices for market price inputs.
- Convert FX before computing returns.
- Do not interpolate asset returns.
- FX daily data may be forward-filled only where the detailed data/FX rules allow it.
- Monthly returns use effective month-end.
- `analysis_end` is the last completed effective period before today.
- Monthly return-panel cache keys must include the resolved per-ticker asset-currency fingerprint;
  changing an asset currency in `assets.yml` must invalidate FX-adjusted cached panels.
- Use inner joins for covariance, correlation, beta, excess-return metrics, and RC_vol unless the owning spec says otherwise.
- Preserve full precision through calculations; round only at final export/report stage.
- Missing returns are missing data, not zero returns.
- Generated outputs are not source data unless a task explicitly targets generated artifacts.

Detailed metric rules live in [docs/specs/metrics_specification.md](docs/specs/metrics_specification.md). Detailed NaN and young ETF rules live in [docs/specs/data_policy_spec.md](docs/specs/data_policy_spec.md).

## Missing Data And Errors

Missing data must be handled explicitly:

- Missing asset returns remain NaN until the owning pipeline applies a documented policy.
- Dynamic NaN-safe backtests use the documented `w_miss` to cash-proxy behavior.
- `data_policy.json.n_months_cash_fallback` counts periods where missing positive risk-asset weight
  could not be placed on observed risk returns after redistribution and therefore used the cash proxy.
- Young ETFs must not truncate the entire portfolio history to the youngest inception date.
- Insufficient data should produce clear errors, warnings, fallback metadata, or quality flags.
- Failed data source calls should not silently produce misleading complete outputs.
- If investor-currency risk-free data is required and neither an explicit source nor a supported
  currency default exists, the pipeline must fail fast rather than guess.

Detailed fallback and reporting behavior is governed by [docs/specs/data_policy_spec.md](docs/specs/data_policy_spec.md), [docs/specs/production_workflow.md](docs/specs/production_workflow.md), and the module-specific specs.

## FX, Benchmark, And Risk-Free Data

FX:

- FX conversion is handled before returns.
- Yahoo-style FX tickers such as `EURUSD=X` mean one unit of the base currency in quote currency.
- If a required orientation is unavailable and an inverse pair is supported, the implementation may invert explicitly.
- FX calendars may be aligned by forward fill where allowed; asset returns must not be interpolated.

Benchmarks:

- `Beta_base` uses a single investor-currency base benchmark for a unified market-risk scale.
- `Beta_local` is a per-asset diagnostic and is not a portfolio metric.
- Local benchmark mappings and hard special rules are governed by [docs/specs/metrics_specification.md](docs/specs/metrics_specification.md).

Risk-free:

- Supported built-in risk-free defaults are USD -> FRED `DTB3` and EUR -> ECB `€STR`, where
  configured by the metrics spec.
- Risk-free series must be converted/resampled to the relevant metric frequency.
- If investor currency is not covered by a built-in default and no explicit risk-free source exists,
  the pipeline must not guess.

Cash proxies:

- Supported built-in cash-proxy defaults are USD -> `BIL` and EUR -> `PEU`.
- If investor currency is not covered by a built-in cash-proxy default, `cash_proxy_ticker` must be
  set explicitly.

## Factor And Macro Data

Factor and macro inputs are diagnostic inputs unless a canonical spec says otherwise.

Factor data supports:

- stress factor betas
- factor covariance analytics
- factor attribution
- factor variance decomposition
- scenario analytics
- regime factor analytics

Macro data supports:

- `macro_regime_diagnostics`
- regime labels
- regime quality checks
- regime-specific analytics

Production factor definitions, extended diagnostic factors, macro source resolution, frequency rules, coverage tiers, and diagnostic-only boundaries are governed by [docs/specs/stress_testing_spec.md](docs/specs/stress_testing_spec.md), [docs/specs/factor_diagnostics_spec.md](docs/specs/factor_diagnostics_spec.md), and [docs/specs/macro_regime_spec.md](docs/specs/macro_regime_spec.md).

## Data Quality Rules

Every data-layer change should preserve these standards:

- Inputs must be traceable to a source, config, cache, or generated artifact.
- Frequency conversions must be explicit.
- Calendar alignment must be explicit.
- Missing data treatment must be documented.
- Fallbacks must be visible in metadata, warnings, or report fields.
- Diagnostics must report confidence, coverage, or usability flags where the owning spec requires them.
- Cache use must not hide stale or failed source behavior.
- Cache metadata must expose cache-relevant config such as the asset-currency fingerprint when cached panels are written.
- Generated outputs must not be treated as source-of-truth data.
- Tests or reproducible checks should cover new parsing, validation, fallback, or alignment behavior.

## Data-Layer Files And Modules

Core data/config files:

- `config.yml`
- `config.yml.example`
- `assets.yml`
- `config/client_profiles.yml`
- `config/etf_universe.yml`
- `config/stock_universe.yml`
- `config/historical_stress_proxy_map.yml`

Core data modules:

- `src/config.py`
- `src/config_schema.py`
- `src/client_profiles.py`
- `src/data_loader.py`
- `src/data_yf.py`
- `src/data_fred.py`
- `src/data_ecb.py`
- `src/data_macro_sources.py`
- `src/fx.py`
- `src/returns_frequency.py`
- `src/resample.py`
- `src/returns.py`
- `src/portfolio_dynamic.py`
- `src/historical_stress_fallback.py`

Data consumers:

- `src/optimization.py`
- `src/metrics_asset.py`
- `src/metrics_portfolio.py`
- `src/metrics_daily.py`
- `src/risk_contrib.py`
- `src/stress.py`
- `src/stress_factors.py`
- `src/stress_scenario_analytics.py`
- `src/regime_factor_analytics.py`
- `src/regime_portfolio_metrics.py`
- `src/scenario_library.py`
- `src/scenario_library_normalized.py`
- `run_optimization.py`
- `run_report.py`
- candidate portfolio runner scripts

## Documentation Sync Rule

If an agent or developer changes code related to data, they must check whether these documents need updates:

- [DATA.md](DATA.md)
- [SPEC.md](SPEC.md)
- [README.md](README.md)
- [AGENTS.md](AGENTS.md)
- [RULES.md](RULES.md)
- [docs/specs/data_policy_spec.md](docs/specs/data_policy_spec.md)
- [docs/specs/metrics_specification.md](docs/specs/metrics_specification.md)
- [docs/specs/stress_testing_spec.md](docs/specs/stress_testing_spec.md)
- [docs/specs/factor_diagnostics_spec.md](docs/specs/factor_diagnostics_spec.md)
- [docs/specs/macro_regime_spec.md](docs/specs/macro_regime_spec.md)
- [docs/specs/scenario_library_spec.md](docs/specs/scenario_library_spec.md)
- [docs/specs/taxonomy_spec.md](docs/specs/taxonomy_spec.md)

Update [DATA.md](DATA.md) when the change affects data sources, expected structures, data pipeline, NaN handling, FX logic, benchmark logic, risk-free inputs, factor/macro inputs, config fields, validation rules, fallback behavior, or data quality expectations.

Update [SPEC.md](SPEC.md) when the general implementation contract, workflows, inputs/outputs, behavior rules, edge cases, or status matrix change.

Update [AGENTS.md](AGENTS.md) only when agent operating rules, verification rules, source-of-truth order, or documentation sync rules change.

Update detailed `docs/specs/*.md` files when detailed behavior of a specific data path changes.
