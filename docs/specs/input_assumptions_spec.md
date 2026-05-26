# Input And Assumptions Specification

This document owns the current contract for the product's first layer: portfolio input, mandate inputs, and calculation assumptions. It promotes the first layer from the non-binding product concept into an implementation-facing specification without changing metric formulas, stress scenarios, or optimizer policy.

The resolved runtime contract is `analysis_setup` (`analysis_setup_v1`). `input_assumptions` is the exported/reporting representation of `analysis_setup`; it is not a separate source object for business logic.

## Contract freeze (2026-05-26)

The **Input Layer MVP** contract in this spec (Core MVP three-field surface, real-cash holdings,
`input_surface` / `field_tiers` export, MVP normalization) is **frozen** as of ExecPlan closure
[Input Layer MVP Migration](../exec_plans/2026-05-26_input_layer_mvp_migration.md) Session 10.

- **Do not** reopen input-layer redesign, new first-screen fields, or tier reclassification unless a
  **documented bug** breaks acceptance (regression in `tests/test_input_layer_mvp_regression.py`,
  `tests/test_real_cash.py`, or live Block 1 disclosure).
- **Allowed without reopening:** bug fixes, clarifications that match implemented behavior, EUR or
  non-USD parity work explicitly scoped in a new ExecPlan.
- **Next product work** belongs to downstream layers (Portfolio X-Ray, Stress Lab, Problem
  Classification, Candidate Launchpad, compare/verdict adapters) — see
  [product_flow_operator_guide.md](../product_flow_operator_guide.md).

Evidence: [Input Layer MVP acceptance audit](../audits/2026-05-26_input_layer_mvp_acceptance_audit.md);
live one-candidate verification 2026-05-26 in audit §5.

## Scope

The Input and Assumptions Layer defines what the user or system must know before optimization, reporting, stress diagnostics, candidate generation, or recommendation logic runs.

It covers:

- portfolio input mode
- canonical `analysis_subject` input object
- configured ticker universe
- optional current portfolio weights
- investor currency, benchmark, cash proxy, and risk-free source
- client profile, targets, constraints, and cash policy
- calculation windows, return frequency, coverage, backtest mode, and output folders
- the structured `analysis_setup` runtime contract
- the structured `input_assumptions` summary exported from `analysis_setup` in run artifacts

It does not own metric formulas, risk-free conversion formulas, NaN handling formulas, feasibility formulas, stress scenario definitions, candidate construction methods, or production release statuses. Those remain in their dedicated specs.

## Core MVP Input Surface

The **Core MVP** portfolio-first product path (`run_portfolio_review.py`, diagnosis and optional
one-candidate compare) requires **only** these user-supplied inputs:

| User input | Config keys | Required for Core MVP |
| --- | --- | --- |
| Instruments | `tickers` | Yes |
| Allocation | `weights`, `current_weights`, or `analysis_subject.weights` | Yes (at least one positive weight map) |
| Reporting currency | `investor_currency` | Yes |

Everything else in this document is either **system-resolved**, **legacy/advanced config**, or a
**later product layer** (Client-Fit Check, Risk Guardrail, Candidate Builder, Assumption Testing).
Core MVP must not fail config validation when optional later-layer fields are omitted.

**Config UI (`config_ui/`):** the web form exposes the three Core MVP groups on the first screen
(currency, tickers, weights). Legacy optimizer, mandate, and liquidity fields live under
**Advanced settings** (collapsed by default). Saving in Core MVP mode writes compact YAML aligned
with `config.yml.example` Section 1 plus preserved technical run settings.

**Internal defaults (not first-screen user fields):** for Core MVP the system assumes
`analysis_subject.type = current_portfolio` and `analysis_mode = analyze_current_weights` when
the user supplies a current allocation (implementation: Session 02+ in
[Input Layer MVP Migration ExecPlan](../exec_plans/2026-05-26_input_layer_mvp_migration.md)).
Users may still set these keys explicitly in YAML for clarity or legacy tooling.

**Export-only artifact:** `input_assumptions` remains a reporting projection of `analysis_setup`.
Downstream calculation, stress, and comparison logic must consume `analysis_setup` or canonical
runtime inputs (`PortfolioConfig`, resolved weights), not treat `input_assumptions` as a second
source of truth.

## Input Layer Structure (canonical product)

The Input and Assumptions Layer is organized into six logical blocks. Only **§1.1** and **§1.2**
(partly) are required for Core MVP user-facing input; the rest are deferred or backend-only.

### 1.1 Portfolio Input

**Purpose:** Capture the factual portfolio under diagnosis — which instruments, what weights, and
in which currency results are shown.

**Core MVP user fields:**

- `tickers` — instrument list (risk assets and explicit cash labels; see Real Cash Holdings).
- `weights` / `current_weights` / `analysis_subject.weights` — allocation; percent strings allowed.
- `investor_currency` — USD, EUR, JPY, CHF (non-USD/EUR may require explicit cash proxy and RF in config until broader defaults exist).

**Not on first screen (deferred or internal):**

| Field | Tier | Notes |
| --- | --- | --- |
| `analysis_subject` (`type`, `id`, `display_name`) | `system_default` / internal | Injected for Core MVP when weights supplied |
| `analysis_mode` | `system_default` / internal | `analyze_current_weights` for Core MVP |
| `portfolio_value` | `client_fit_later` | Liquidity / action / rebalancing |
| `initial_investable_amount` | `client_fit_later` | Same |
| `beta_local_mapping` | `assumption_testing` | Asset-level diagnostic override |

**Example (Core MVP):** VOO 45%, QQQ 20%, TLT 15%, GLD 10%, Cash USD 10%, `investor_currency: USD`.

#### Real Cash Holdings (normative)

If the user enters **real cash** as a portfolio holding (for example `Cash USD`, `Cash EUR`,
`CASH`, or equivalent labels accepted by the implementation), the system **must**:

- treat it as an explicit portfolio position in weights;
- use **0%** return, **0%** volatility, and **0** drawdown for that position;
- **not** download a price series for that label;
- include it in reported allocation and diagnostics as actual cash;
- **not** replace it with `cash_proxy_ticker` (for example BIL or PEU).

`cash_proxy_ticker` is a **technical** setting only: risk-free rate for Sharpe/excess metrics,
NaN-safe backtest miss fill, and alternative candidate modeling. It is **not** the same as user-entered
bank cash. If both an ETF cash proxy (e.g. BIL) and `Cash USD` appear, they are distinct positions.

Implementation status: enforced in `src/real_cash.py` (Session 03,
[Input Layer MVP Migration ExecPlan](../exec_plans/2026-05-26_input_layer_mvp_migration.md)).

### 1.2 System Defaults / Market and Calculation Base

**Purpose:** Provide a consistent market and calculation base for X-Ray, metrics, stress, and
reports after the user chooses `investor_currency`.

**System-resolved (user not asked on first screen for USD/EUR Core MVP):**

- `risk_free_source` / `rf_source`
- `cash_proxy_ticker`
- `base_benchmark_ticker` / `benchmark_base_ticker`
- FX and local-currency conversion rules per [metrics_specification.md](metrics_specification.md) and [DATA.md](../../DATA.md)
- `market_data_provider` (config default)

Resolution is implemented in `src/config.py` (`resolve_cash_and_rf`, benchmark defaults by currency).
Unsupported currencies must still set cash proxy and risk-free explicitly.

### 1.3 Liquidity and Cash Context (later — not Core MVP input)

**Purpose (future):** Cash adequacy and practical suitability — life floor, expense coverage,
whether a candidate violates liquidity needs.

**Fields (optional / later layers):** `liquidity_need` (legacy derived flag), `liquidity_need_months`,
`monthly_expenses`, `cash_policy`.

**Core MVP:** not required. If the user already holds cash in the portfolio (§1.1 Real Cash), that
position is diagnosed as-is. `cash_policy` (vol scaling via cash, required floor, prohibited) applies
to **Candidate Builder / optimization** later, not to mandatory first-screen input.

**Future placement:** optional Risk Guardrail / Client-Fit Check before or after Candidate Builder.

### 1.4 Client Profile and Objectives (later — not Core MVP input)

**Purpose (future):** Compare realized portfolio behavior to stated goals (drawdown tolerance,
vol target, return objective) — interpretive, not auto-trading.

**Fields:** `client_profile`, `target_nominal_return_annual`, `target_vol_annual`,
`target_max_drawdown_pct`, `min_acceptable_return`, `horizon_years`.

**Core MVP:** not required for `run_portfolio_review` diagnosis. `horizon_years` remains report/context
only in V1 (does not change optimizer or stress gates).

**Future placement:** Client-Fit Check / Client Sheet; may prefill Candidate Builder constraints.

### 1.5 Mandate / Constraints (later — Candidate Builder; Core MVP defaults only)

**Purpose (future):** Limit how **alternative** portfolios are generated (caps, leverage, shorts).

**Fields:** `allow_leverage`, `allow_short_selling`, `max_single_security_weight_pct`,
`min_single_security_weight_pct`, asset-class bounds, turnover/CVaR limits (where configured).

**Core MVP defaults (no user prompt):** `allow_leverage = false`, `allow_short_selling = false`.
Current portfolio is diagnosed **as-is**; concentration is an X-Ray finding, not a first-input block.

**Future placement:** Portfolio Alternatives Builder parameters.

### 1.6 Technical Assumptions (backend / config defaults)

**Purpose:** Define run windows, data quality, backtest mode, robustness checks, and output folders.

**Fields:** `windows_months`, `returns_frequency`, `coverage_threshold`, `backtest_mode`,
`optimization_windows_months`, `primary_window_months`, `secondary_window_months`, `robustness_policy`,
`covariance_shrinkage`, `young_etf_optimization_policy`, `output_dir`, `output_dir_final`,
`market_data_provider`.

**Core MVP:** not user-required on first screen; values come from config defaults and
`validate_config` injection. Non-monthly `returns_frequency` is disclosure-only for the main metrics
panel per [metrics_specification.md](metrics_specification.md).

**Future placement:** Assumption Testing / Sensitivity Mode (advanced).

## Field Classification Reference

| Tier | Meaning | Examples |
| --- | --- | --- |
| `core_mvp` | Required user input for portfolio-first Core MVP | `tickers`, weights, `investor_currency` |
| `system_default` | Resolved from currency/config; may be injected | `analysis_subject`, `analysis_mode`, RF, benchmark, cash proxy |
| `client_fit_later` | Client-Fit Check / Client Sheet | `client_profile`, targets, `horizon_years`, `portfolio_value` |
| `risk_guardrail_later` | Liquidity suitability after diagnosis | `liquidity_need_months`, `monthly_expenses` |
| `candidate_builder` | Alternative portfolio construction | `max_single_security_weight_pct`, `cash_policy` for scaling |
| `assumption_testing` | Sensitivity / advanced | `beta_local_mapping`, window overrides |
| `legacy_advanced` | Legacy policy optimizer / full config UI | full mandate + liquidity + `optimize_from_universe` batch |

## Resolved Analysis Setup Contract

`analysis_setup` is the single resolved runtime contract consumed by downstream modules. User/config inputs may be simple or incomplete; the first layer resolves them into a complete analysis setup before diagnostics, stress tests, optimization artifacts, candidate comparison, or reporting logic use them.

`analysis_setup_v1` contains:

- `analysis_subject`: the resolved portfolio-first subject diagnosed before candidates, including
  type, id, display name, tickers, resolved weights, weight source, role, recommendation status,
  resolution source, and validation status.
- `portfolio_input`: raw user/config intent, selected tickers, optional current weights, currency, benchmark request, profile, and horizon metadata.
- `analysis_portfolio`: the resolved portfolio used as the diagnostic base, including role, weight source, weights, cash handling, and recommendation status.
- `resolved_mandate`: profile/default/override values with source, enforcement type, and downstream applicability.
- `resolved_assumptions`: windows, return frequency, expected-return method, covariance method, risk-free source, cash proxy, missing-data policy, and placeholders for transaction-cost/rebalance assumptions.
- `validation_result`: blocking errors, action-required warnings, informational notices, and explicit current-repo-vs-target-MVP policy notes.

The exported `input_assumptions` block is a projection from `analysis_setup`. Reports may display it for reproducibility, but calculation or policy modules must use `analysis_setup` or their existing canonical runtime inputs, not infer business logic from `input_assumptions`.

### `data_trust_signals` (RM-1016)

`input_assumptions_v1` may include `data_trust_signals` (`input_data_trust_signals_v1`): a
read-only trust panel for young-ETF optimization policy and input-validation/taxonomy notices.
It does not change data policy, NaN handling, or optimizer formulas.

| Field | Description |
| --- | --- |
| `young_etf_policy_enabled` | Copy of `calculation_assumptions.young_etf_optimization_policy.enabled`. |
| `young_etf_policy_summary` | Plain-English summary of young-ETF policy scope for optimizer runs. |
| `signals[]` | Structured rows (`category`, `severity`, `code`, `plain_english`). |
| `user_summary_lines[]` | Short lines for run metadata and commentary handoff. |
| `does_not_change_data_policy` | Always `true`. |

### `review_bundle_disclosure` (RM-1026)

`input_assumptions_v1` may include `review_bundle_disclosure` with
`mode_subject_consistency` projected from the same resolver as
`candidate_comparison.json` → `review_bundle_context`. When present,
`data_trust_signals.user_summary_lines` merges review-bundle notices (for example
legacy `analysis_mode=optimize_from_universe` while diagnosing an explicit
`current_portfolio` subject) ahead of generic trust lines.

### `input_surface` (Input Layer MVP Session 06)

`input_assumptions_v1` includes `input_surface` (`input_surface_v1`): export-only disclosure of
which product input surface applies and whether Core MVP first-screen requirements are met.

| Field | Description |
| --- | --- |
| `profile` | `core_mvp` when diagnosing a user-supplied allocation (`analyze_current_weights` or explicit current/model subject); otherwise `legacy_advanced`. |
| `product_path` | `portfolio_first_diagnosis` vs `legacy_policy_or_universe_baseline`. |
| `first_screen` | Per-group status for tickers, allocation, and `investor_currency` (required/supplied/source). |
| `core_mvp_requirements_met` | `true` when all three first-screen groups are supplied. |
| `system_injected` | Resolved `analysis_mode`, `analysis_subject` type, `resolution_source`, and whether a `compat.*` resolver applied. |
| `real_cash` | Holdings summary from `analysis_portfolio.cash_handling` (distinct from `cash_proxy_ticker`). |
| `notes` | Plain-English disclosure lines for operators and Block 1 acceptance. |

### `field_tiers` (Input Layer MVP Session 06)

`input_assumptions_v1` includes `field_tiers` (`field_tiers_v1`): the static tier registry from
**Field Classification Reference** plus a per-run `run_disclosure` block.

| Field | Description |
| --- | --- |
| `tier_definitions` | Short meaning of each tier (`core_mvp`, `system_default`, `client_fit_later`, …). |
| `registry` | Config field → tier map (canonical classification; not a second source of truth for logic). |
| `run_disclosure.core_mvp` | Which first-screen groups were user-supplied and whether requirements are met. |
| `run_disclosure.populated_by_tier` | Fields with values on this run, grouped by tier. |
| `run_disclosure.user_configured_fields` | Fields with user or profile preset sources (deferred layers). |
| `run_disclosure.deferred_tiers_with_values` | Later-layer tiers that still have values on this run. |

Implementation: `build_input_surface` and `build_field_tiers` in `src/input_assumptions.py`.

## `analysis_subject` Config Object

`analysis_subject` is the canonical portfolio-first input object. When it is present and valid, it
takes priority over compatibility inference from `analysis_mode`, legacy `weights`, and generated
`portfolio_weights.yml`.

Supported explicit values:

- `analysis_subject.type: current_portfolio` requires `analysis_subject.weights` and represents the
  user's real current allocation.
- `analysis_subject.type: model_portfolio` requires `analysis_subject.weights` and represents a
  user-specified model or proposed allocation to diagnose before alternatives.
- `analysis_subject.type: universe_baseline` requires tickers only; the resolver creates equal
  weights for diagnostic baseline use.

Optional fields:

- `id`: stable subject id; defaults to `analysis_subject`.
- `display_name`: report-friendly label; defaults from the subject type.
- `tickers`: subject ticker list; defaults to top-level `tickers` and must be a subset of them.
- `weights`: required only for current/model subjects; percent strings such as `"60%"` are accepted.

Runtime behavior:

- explicit current/model subjects become fixed report weights with
  `weights_source = config.analysis_subject.weights`;
- explicit current/model subject weights must be numeric, non-negative, include at least one
  positive weight, and have a positive-weight sum no greater than `1.0` plus a small floating-point
  tolerance;
- explicit current/model subject weights with a positive-weight sum below `1.0` remain valid as a
  partial allocation with the remainder disclosed as `cash_remainder` in `analysis_setup` and
  `input_assumptions`;
- explicit current/model subject weights with a material positive-weight sum above `1.0` fail config
  validation before report generation, rather than continuing as warning-only diagnostics;
- explicit universe-baseline subjects become equal-weight diagnostic weights with
  `weights_source = system.analysis_subject.equal_weight_baseline`;
- explicit `analysis_subject` prevents stale generated `portfolio_weights.yml` from being merged as
  the report weights for that run;
- generated policy weights remain legacy outputs and are not the default `analysis_subject`.

## Supported Compatibility Modes

`analysis_mode` is the current config compatibility mode.

Supported V1 values:

- `optimize_from_universe`
- `analyze_current_weights`

When omitted, `analysis_mode` defaults to `optimize_from_universe`.

### optimize_from_universe

This is the legacy compatibility policy workflow. The config default remains
`optimize_from_universe` for backward compatibility, but the portfolio-first product workflow should
use explicit `analysis_subject` and `run_portfolio_review.py`.

The user supplies a ticker list in `tickers`. The configured tickers define the risk-asset universe after cash proxy exclusion. `run_optimization.py` builds policy weights from the universe, applies the current construction policy, and writes generated weights to `portfolio_weights.yml` under `output_dir_final`.

In this mode, `run_report.py` expects fixed weights from either legacy `weights` or the generated
`portfolio_weights.yml`. If neither exists, the normal report command must fail clearly and point to
portfolio-first subject materialization or deliberate legacy policy optimization.

Lifecycle mapping:

- In portfolio-first semantics, explicit `analysis_subject.type: universe_baseline` resolves the
  ticker universe to equal diagnostic weights before candidates are generated.
- In current repo compatibility mode without explicit `analysis_subject`, `optimize_from_universe`
  remains optimizer-first. Reporting without generated or fixed weights still fails unless the user
  materializes the resolved subject through `run_report.py --materialize-analysis-subject` or uses
  `run_portfolio_review.py`.

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

Legacy production policy weights still come from `run_optimization.py` and approved
post-optimization protocols. Users must not manually edit generated final weights as if they were
policy optimizer output.

`current_weights` may be entered manually only for existing-portfolio diagnostics. In `analyze_current_weights` mode, current weights become fixed report weights. In `optimize_from_universe` mode, current weights are preserved as input context but do not replace generated policy weights.

For the **combined current-vs-policy workflow** (policy optimize + report on Main, current materialized to `{output_dir_final}/current_portfolio/`, then comparison), see [current_vs_policy_workflow_spec.md](current_vs_policy_workflow_spec.md). Users should not toggle the whole config to `analyze_current_weights` to answer "should I move to policy?"

When the user wants **current-vs-policy No-Trade** in the same comparison run, keep `analysis_mode: optimize_from_universe`, set `current_weights`, run the policy path, then **materialize current** into `{output_dir_final}/current_portfolio/` without overwriting Main policy artifacts. See [current_vs_policy_workflow_spec.md](current_vs_policy_workflow_spec.md).

Equal Weight Initial Portfolio is a baseline, not a recommendation. It must be excluded from recommendation language unless it later becomes an explicit candidate and wins comparison under documented selection logic.

## Lifecycle Mapping

The target product lifecycle maps user intent into `analysis_setup`:

- `current_portfolio`: tickers plus subject weights create
  `analysis_subject.type = current_portfolio` and
  `analysis_portfolio.portfolio_role = user_current_portfolio` when the run diagnoses that subject.
- `model_portfolio`: tickers plus subject weights create
  `analysis_subject.type = model_portfolio` and
  `analysis_portfolio.portfolio_role = model_portfolio` when the run diagnoses that subject.
- `universe_baseline`: tickers without subject weights create
  `analysis_subject.type = universe_baseline` and equal-weight diagnostic baseline weights.

Current repo compatibility:

- `analysis_mode=analyze_current_weights` maps to `user_current`.
- `analysis_mode=optimize_from_universe` without explicit `analysis_subject` maps to the existing construction workflow and resolves a universe-baseline subject for metadata.
- legacy `weights` remains supported for fixed-report compatibility and resolves as a model-portfolio subject when not generated from `portfolio_weights.yml`.

## User Inputs (compatibility index)

For **Core MVP**, see **§ Core MVP Input Surface** and **§1.1 Portfolio Input**. The list below
indexes all config keys historically grouped as “user inputs”; tier labels refer to
**Field Classification Reference**.

| Field | Tier (Core MVP) |
| --- | --- |
| `tickers` | `core_mvp` |
| `weights`, `current_weights`, `analysis_subject.weights` | `core_mvp` |
| `investor_currency` | `core_mvp` |
| `analysis_mode`, `analysis_subject` | `system_default` (may be injected) |
| `initial_investable_amount`, `portfolio_value` | `client_fit_later` |
| `liquidity_need_months`, `monthly_expenses`, `liquidity_need` | `risk_guardrail_later` |
| `cash_policy` | `candidate_builder` |
| `client_profile`, target overrides, `horizon_years` | `client_fit_later` |
| `allow_leverage`, `allow_short_selling`, position caps/floors | `candidate_builder` / defaults |
| `risk_free_source`, `cash_proxy_ticker`, `base_benchmark_ticker` | `system_default` |
| `windows_months`, `returns_frequency`, … | `assumption_testing` / backend defaults |

`horizon_years` is report/context only in V1: validated and exported, but does not change optimizer
objective, constraints, windows, stress tests, or release status.

## System-Resolved Inputs

See **§1.2 System Defaults**. Implementation summary:

- cash proxy ticker from `cash_proxy_ticker`, otherwise currency defaults (USD → `BIL`, EUR → `PEU`)
- risk-free source from `risk_free_source`, otherwise currency defaults (USD → `FRED:DTB3`, EUR → ECB €STR)
- base benchmark from `base_benchmark_ticker` or currency defaults
- local benchmark map from config overrides plus defaults
- profile-derived targets from `config/client_profiles.yml` when `client_profile` is set (not required for Core MVP)

Unsupported investor currencies may still use benchmark defaults, but must set both
`cash_proxy_ticker` and `risk_free_source` explicitly. Risk-free and benchmark behavior remains
governed by [metrics_specification.md](metrics_specification.md), [DATA.md](../../DATA.md), and `src/config.py`.

## Ticker Validation Policy

Users should select tickers only from the supported taxonomy universe so the system can avoid missing asset classes, missing stress classifications, and broken reports.

### Explicit `analysis_subject` (Block 1 preflight)

When `analysis_subject` is present with a supported `type`, config validation **must fail before**
report or portfolio-review runs if any subject ticker is absent from both `config/etf_universe.yml`
and `config/stock_universe.yml`. The cash proxy ticker resolved for the run (for example `BIL` for
USD) is treated as allowed even when it is not part of the subject ticker list.

Failure mode: `ConfigValidationError` with `unknown=[...]` listing tickers not found in either
taxonomy file. This is enforced in `validate_config` via `preflight_explicit_analysis_subject_tickers`
in `src/analysis_setup.py`.

### Legacy compatibility paths

Configs without explicit `analysis_subject` keep warning-based taxonomy checks during
optimization/report (`etf_universe_validation.json`). ETF and stock taxonomy remain
annotation/diagnostics infrastructure and do not silently rewrite the configured ticker universe.

## Mandate And Constraint Inputs

See **§1.5 Mandate / Constraints**. `client_profile` fills targets only when set. Profile values may set:

- `target_nominal_return_annual`
- `target_vol_annual`
- `target_max_drawdown_pct`
- `liquidity_floor_pct`
- optional `min_single_security_weight_pct`

Manual target and constraint values are allowed through config. Config values may use decimals such as `0.15` or percent strings such as `"15%"` where the schema supports percent fields.

Feasibility formulas for weight caps and floors are owned by `feasibility_constraints_spec.md`. Portfolio construction behavior is owned by `portfolio_construction_policy.md`.

## Technical Calculation Assumptions

See **§1.6 Technical Assumptions**. Technical analysis settings include:

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

`returns_frequency` in config may be `monthly`, `weekly`, or `daily`, but the **main investor return panel** for metrics, optimizer covariance and expected returns, correlation, RC_vol, and backtest is always **monthly** per `metrics_specification.md`. Non-monthly config values are recorded as `configured_returns_frequency` / `configured_return_frequency` in runtime metadata and `frequency_disclosure`; they do not resample the main panel. Factor stress, primary factor regression diagnostics, macro regime labels, and regime factor analytics may use their own canonical frequencies and must disclose mismatches as defined in the stress and metrics specs.

NaN and young-ETF behavior remains governed by `data_policy_spec.md`.

## Runtime Artifact Contract

Runs must expose structured `analysis_setup` and `input_assumptions` objects where metadata artifacts are produced.

`run_result.json` from `run_optimization.py` includes `analysis_setup` and projected `input_assumptions`.

`run_metadata.json` from `run_report.py` includes `analysis_setup` and projected `input_assumptions`.

`analysis_setup` must identify:

- schema version
- run context
- resolved `analysis_subject` with type, id, display name, tickers, weights, weight source,
  resolution source, and validation status
- portfolio input and product input case
- analysis portfolio role, weight source, weights, cash handling, and recommendation status
- resolved mandate values with source, enforcement, and applicability
- resolved assumptions for currency, benchmark, cash proxy, risk-free source, local benchmark map, windows, frequency, covariance, missing data, and current placeholders
- validation result, including current repo conflicts with target MVP semantics

`input_assumptions` must identify the reporting-friendly subset:

- source `analysis_setup` version
- run context
- resolved `analysis_subject` summary
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

The following remain open relative to this spec and the
[Input Layer MVP Migration ExecPlan](../exec_plans/2026-05-26_input_layer_mvp_migration.md):

- **Real cash holdings** in metrics and data pipeline (Session 03; rule is normative in §1.1) — implemented; see §1.1
- **Field tier metadata** on exported `input_assumptions` (Session 06) — implemented; see `input_surface` and `field_tiers`
- interactive UI range pickers for every target and technical setting
- transaction cost / rebalance cost model
- investment horizon effects on optimizer policy
- formal assumption sensitivity module ([assumption_sensitivity_spec.md](assumption_sensitivity_spec.md))
- Client-Fit Check and Risk Guardrail product surfaces (§1.3–1.4)
- formal selection engine or no-trade logic beyond existing product adapters

These items require implementation work in their owning sessions before they become fully binding in code.
