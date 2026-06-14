# DATA.md

This file is the living data-layer map for Portfolio MRI / Optimization Terminal.

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
- Interactive Brokers TWS / IB Gateway via `ib_insync` for optional read-only quote and
  historical-bar downloads through `market_data_provider`. `yfinance` remains available as the
  default provider and as the fallback in `ibkr_yfinance_fallback` mode.
- FRED through project data helpers for risk-free, macro, and selected factor inputs.
- ECB / FX helpers where configured by the project.
- Official CSV/API/keyed/manual macro sources where supported by the macro source resolver.
- Local YAML config and metadata files.
- Local cache files under `cache/` when cache is enabled.

Future quote-data candidates to evaluate: EODHD as first priority, Tiingo for personal usage only, and Alpaca. These are not default project data sources yet.

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
- IBKR latest quotes: per-symbol records with price, source (`mid`, `last`, `close`, or
  `marketPrice`), bid/ask/last/close fields, delayed/live mode disclosure, exchange, and currency.
- IBKR historical bars: Date-indexed DataFrames with a `Close` column. These are IBKR adjusted
  daily closes when `ADJUSTED_LAST` is available.
- FX series: time-indexed daily series in the orientation required by `src/fx.py`.
- Return panels: time-indexed DataFrames by ticker at the configured analysis frequency.
- Risk-free series: time-indexed series resampled to the required metric/reporting frequency.
- Factor and macro panels: time-indexed DataFrames with explicit frequency, source coverage, and quality metadata where implemented.
- Taxonomy records: structured config rows with canonical tickers, classes, and validation status.

Detailed field schemas are owned by the relevant config schema, taxonomy specs, and module-specific specs.

Provider selection:

- `market_data_provider: yfinance` keeps the legacy Yahoo pipeline.
- `market_data_provider: ibkr` uses IBKR only and returns missing tickers as unavailable.
- `market_data_provider: ibkr_yfinance_fallback` tries IBKR first and falls back to Yahoo per
  missing ticker.
- Daily and monthly cache keys include the resolved provider, so IBKR and Yahoo panels do not
  silently reuse each other's cache.
- yfinance's own SQLite metadata/cache files are pinned under `cache/yfinance/` by `src/data_yf.py`
  so Yahoo factor proxies do not fail because the operating-system default cache directory is
  unavailable.
- Diagnosis-only `analysis_subject` materialization may use an approved cached risk-free series
  when fresh FRED `DTB3` times out. This fallback is allowed only when cache is enabled and the
  cached series metadata matches the requested risk-free source, investor currency, return
  frequency, and covers the analysis-effective end date. It is never silent: `run_metadata.json`,
  `data_policy.json`, cache metadata, and logs expose `risk_free_fallback_used: true`,
  `risk_free_fallback_reason: fred_timeout_cached_rf`, and an operator warning.

## Core Data Rules

- Use adjusted close prices for market price inputs.
- Convert FX before computing returns.
- Do not interpolate asset returns.
- FX daily data may be forward-filled only where the detailed data/FX rules allow it.
- Monthly returns use effective month-end.
- `analysis_end` is the last completed effective period before today. Diagnostic runs use analysis-effective panels (rows `<= analysis_end`); raw cached panels may extend later and are exported separately when needed (`results_csv/inputs/monthly_returns_raw.csv`). See [docs/specs/data_policy_spec.md](docs/specs/data_policy_spec.md) §9.
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
- For diagnosis-only FRED `DTB3` timeouts, the approved cached risk-free fallback may keep the run
  operational only when the cache criteria above pass. If no approved cached series exists, or
  `--no-cache` is used, the command must fail clearly instead of fabricating a risk-free series.
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
- FRED `DTB3` timeout fallback is cache-only, diagnosis-only, and provenance-visible. The fallback
  reuses a previously cached risk-free series; it does not synthesize rates, change formulas, or
  make candidate generation automatic.
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

Factor proxy loaders attach diagnostics to factor matrices and stress beta outputs. When a proxy
such as FRED rates, credit, inflation, USD, VIX, WEI, oil, or Yahoo commodity data cannot be loaded,
`stress_report.json.factor_diagnostics_meta` records the available factors, missing factors, and
per-factor reason. If only the cached benchmark/equity proxy is available, the run is disclosed as
`factor_attribution_scope: equity_only` instead of being presented as a full multi-factor model.
Full factor-matrix FRED dependencies use a separate approved raw-series cache under
`cache/factors/v_<series_id>/`; this is not the monthly risk-free cache. Product/demo analysis is
cache-first: if the approved cache is complete, fresh, and covers the requested date range, the
factor path must not call live FRED. A cache entry is approved only when cache age is within
7 calendar days, metadata matches the FRED series, raw observations cover the requested date range,
and metadata declares daily raw, weekly `W-FRI`, and month-end reconstruction support.

Cache warm/update is API-first. `src.data_fred.fetch_fred_series` reads `FRED_API_KEY` from the
environment and uses the official FRED API when the key is present. Do not store the API key in
`config.yml` or checked-in files. In PowerShell:

```powershell
$env:FRED_API_KEY="your_key_here"
python scripts/warm_factor_cache.py --start 2007-01-01 --end 2026-06-05
python scripts/warm_factor_cache.py --check-only --start 2007-01-01 --end 2026-06-05
```

The public `fredgraph.csv` endpoint is allowed only as a disclosed fallback when no API key is set
or the API request fails. Diagnostics expose `source_used` (`fred_api`, `fred_csv_fallback`,
`cache_hit`, `cache_miss`, `cache_invalid`), `cache_status` (`valid`, `missing`, `partial`,
`expired`), `missing_series`, warnings, `full_factor_matrix_available`, and `demo_safe`.
Partial factor cache is not a full success by itself: every missing required series must refresh
successfully or fail clearly with the series named. The system must not present equity-only data,
fake values, or hidden missing factor series as a full factor matrix.

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
- `src/data_ibkr.py`
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
