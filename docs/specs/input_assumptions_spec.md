# Input And Assumptions Specification

This document owns the current contract for the product's first layer: portfolio input, mandate inputs, and calculation assumptions. It promotes the first layer from the non-binding product concept into an implementation-facing specification without changing metric formulas, stress scenarios, or optimizer policy.

The resolved runtime contract is `analysis_setup` (`analysis_setup_v1`). `input_assumptions` is the exported/reporting representation of `analysis_setup`; it is not a separate source object for business logic.

## Scope

The Input and Assumptions Layer defines what the user or system must know before optimization, reporting, stress diagnostics, candidate generation, or recommendation logic runs.

It covers:

- portfolio input mode
- configured ticker universe
- optional current portfolio weights
- investor currency, benchmark, cash proxy, and risk-free source
- client profile, targets, constraints, and cash policy
- calculation windows, return frequency, coverage, backtest mode, and output folders
- the structured `analysis_setup` runtime contract
- the structured `input_assumptions` summary exported from `analysis_setup` in run artifacts

It does not own metric formulas, risk-free conversion formulas, NaN handling formulas, feasibility formulas, stress scenario definitions, candidate construction methods, or production release statuses. Those remain in their dedicated specs.

## Resolved Analysis Setup Contract

`analysis_setup` is the single resolved runtime contract consumed by downstream modules. User/config inputs may be simple or incomplete; the first layer resolves them into a complete analysis setup before diagnostics, stress tests, optimization artifacts, candidate comparison, or reporting logic use them.

`analysis_setup_v1` contains:

- `portfolio_input`: raw user/config intent, selected tickers, optional current weights, currency, benchmark request, profile, and horizon metadata.
- `analysis_portfolio`: the resolved portfolio used as the diagnostic base, including role, weight source, weights, cash handling, and recommendation status.
- `resolved_mandate`: profile/default/override values with source, enforcement type, and downstream applicability.
- `resolved_assumptions`: windows, return frequency, expected-return method, covariance method, risk-free source, cash proxy, missing-data policy, and placeholders for transaction-cost/rebalance assumptions.
- `validation_result`: blocking errors, action-required warnings, informational notices, and explicit current-repo-vs-target-MVP policy notes.

The exported `input_assumptions` block is a projection from `analysis_setup`. Reports may display it for reproducibility, but calculation or policy modules must use `analysis_setup` or their existing canonical runtime inputs, not infer business logic from `input_assumptions`.

## Supported Config Modes

`analysis_mode` is the current config compatibility mode.

Supported V1 values:

- `optimize_from_universe`
- `analyze_current_weights`

When omitted, `analysis_mode` defaults to `optimize_from_universe`.

### optimize_from_universe

This is the default policy workflow.

The user supplies a ticker list in `tickers`. The configured tickers define the risk-asset universe after cash proxy exclusion. `run_optimization.py` builds policy weights from the universe, applies the current construction policy, and writes generated weights to `portfolio_weights.yml` under `output_dir_final`.

In this mode, `run_report.py` expects fixed weights from either legacy `weights` or the generated `portfolio_weights.yml`. If neither exists, reporting must fail clearly and tell the user to run optimization first.

Lifecycle mapping:

- In target MVP product semantics, tickers without weights represent `universe_only` and resolve to an `Equal Weight Initial Portfolio` baseline before diagnostics.
- In current repo compatibility mode, `optimize_from_universe` remains optimizer-first. Reporting without generated or fixed weights still fails unless SPEC and code are updated to make equal-weight universe-only diagnostics binding behavior.

### analyze_current_weights

This is the existing-portfolio diagnostic workflow.

The user supplies `tickers` and `current_weights`. When legacy `weights` is absent, `current_weights` becomes the fixed report weight map consumed by `run_report.py`.

This mode is for diagnostics and reporting only. `run_optimization.py` must not optimize in this mode; the user must switch back to `optimize_from_universe` to build a policy portfolio.

Weights in this mode are current portfolio weights, not final policy weights. They may later be compared against optimized or candidate portfolios, but they do not replace the policy optimizer.

## Weight Semantics

There are four distinct weight concepts:

- `current_weights`: user-supplied weights for an existing portfolio being diagnosed.
- initial baseline weights: system-created weights for universe-only setup, such as Equal Weight Initial Portfolio.
- `weights`: legacy fixed report weights and backward-compatible fixed-weight input.
- `portfolio_weights.yml`: generated policy weights produced by `run_optimization.py`.
- selected/target weights: weights selected after explicit comparison or policy release logic.

Final production policy weights still come from `run_optimization.py` and approved post-optimization protocols. Users must not manually edit generated final weights as if they were policy optimizer output.

`current_weights` may be entered manually only for existing-portfolio diagnostics. In `analyze_current_weights` mode, current weights become fixed report weights. In `optimize_from_universe` mode, current weights are preserved as input context but do not replace generated policy weights.

Equal Weight Initial Portfolio is a baseline, not a recommendation. It must be excluded from recommendation language unless it later becomes an explicit candidate and wins comparison under documented selection logic.

## Lifecycle Mapping

The target product lifecycle maps user intent into `analysis_setup`:

- `user_current`: tickers plus current weights create `analysis_portfolio.portfolio_role = user_current_portfolio`.
- `universe_only`: tickers without current weights create `analysis_portfolio.portfolio_role = equal_weight_initial_baseline`.
- `custom_model_later`: manual model-portfolio creation and comparison is out of scope for this MVP decision area.

Current repo compatibility:

- `analysis_mode=analyze_current_weights` maps to `user_current`.
- `analysis_mode=optimize_from_universe` maps to the existing construction workflow.
- legacy `weights` remains supported for fixed-report compatibility and must be distinguished from `current_weights` and generated `portfolio_weights.yml`.

## User Inputs

Core user-controlled inputs include:

- `analysis_mode`
- `tickers`
- `current_weights`, when analyzing an existing portfolio
- `investor_currency`
- `initial_investable_amount`
- `portfolio_value`
- `liquidity_need_months`
- `monthly_expenses`
- `cash_policy`
- `client_profile`
- manual target overrides
- `allow_leverage`
- `allow_short_selling`
- position caps and floors
- `horizon_years`

`horizon_years` is currently report/context only. It is validated and exported, but it does not change optimizer objective, constraints, windows, stress tests, or release status in V1.

## System-Resolved Inputs

The system resolves:

- cash proxy ticker from `cash_proxy_ticker` or currency defaults
- risk-free source from `risk_free_source` or currency defaults where supported
- base benchmark from `base_benchmark_ticker` or currency defaults
- local benchmark map from config overrides plus defaults
- profile-derived target values from `config/client_profiles.yml`

Risk-free and benchmark behavior remains governed by `metrics_specification.md`, `DATA.md`, and config resolution code.

## Ticker Validation Policy

MVP product mode rejects unknown tickers. Users should select tickers only from the supported taxonomy universe so the system can avoid missing asset classes, missing stress classifications, and broken reports.

In current repo mode, existing taxonomy behavior remains warning-based unless SPEC is updated. ETF and stock taxonomy validation may report unknown tickers, but taxonomy remains annotation/diagnostics infrastructure and does not silently rewrite the configured ticker universe.

## Mandate And Constraint Inputs

`client_profile` fills targets only. Profile values may set:

- `target_nominal_return_annual`
- `target_vol_annual`
- `target_max_drawdown_pct`
- `liquidity_floor_pct`
- optional `min_single_security_weight_pct`

Manual target and constraint values are allowed through config. Config values may use decimals such as `0.15` or percent strings such as `"15%"` where the schema supports percent fields.

Feasibility formulas for weight caps and floors are owned by `feasibility_constraints_spec.md`. Portfolio construction behavior is owned by `portfolio_construction_policy.md`.

## Technical Calculation Assumptions

Technical analysis settings include:

- `windows_months`
- `returns_frequency`: `monthly`, `weekly`, or `daily`
- `coverage_threshold`
- `backtest_mode`: `dynamic_nan_safe` or `simple`
- `primary_window_months`
- `secondary_window_months`
- `optimization_windows_months`
- `robustness_policy`
- `covariance_shrinkage`
- `young_etf_optimization_policy`
- `output_dir`
- `output_dir_final`

`returns_frequency` controls the main investor return panel for metrics, optimizer covariance and expected returns, correlation, RC_vol, and backtest. Factor stress, primary factor regression diagnostics, and macro regime labels may use their own canonical frequencies and must disclose mismatches as defined in the stress and metrics specs.

NaN and young-ETF behavior remains governed by `data_policy_spec.md`.

## Runtime Artifact Contract

Runs must expose structured `analysis_setup` and `input_assumptions` objects where metadata artifacts are produced.

`run_result.json` from `run_optimization.py` includes `analysis_setup` and projected `input_assumptions`.

`run_metadata.json` from `run_report.py` includes `analysis_setup` and projected `input_assumptions`.

`analysis_setup` must identify:

- schema version
- run context
- portfolio input and product input case
- analysis portfolio role, weight source, weights, cash handling, and recommendation status
- resolved mandate values with source, enforcement, and applicability
- resolved assumptions for currency, benchmark, cash proxy, risk-free source, local benchmark map, windows, frequency, covariance, missing data, and current placeholders
- validation result, including current repo conflicts with target MVP semantics

`input_assumptions` must identify the reporting-friendly subset:

- source `analysis_setup` version
- run context
- analysis mode and product input case
- configured tickers and ticker count
- current-weight status
- reported/fixed-weight status and source
- analysis portfolio role and recommendation status
- currency, benchmark, cash proxy, risk-free source, and local benchmark map
- profile, targets, constraints, cash policy, liquidity inputs, and horizon role
- analysis end, windows, return frequency, periods per year, coverage threshold, backtest mode, covariance settings, young-ETF policy, and known V1 gaps

The `input_assumptions` artifact is explanatory and reproducibility-oriented. It must not change optimizer inputs, mandate gates, or report calculations by itself.

## Current V1 Gaps

The following product concept items are not implemented in this layer yet:

- interactive UI input controls
- user-facing range pickers for every target and technical setting
- transaction cost / rebalance cost model
- investment horizon effects on optimizer policy
- formal assumption sensitivity module
- formal selection engine or no-trade logic

These items require separate specs and implementation work before they become binding.
