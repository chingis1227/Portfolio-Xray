# Portfolio Alternatives Builder Specification

This document owns the V1 on-demand Portfolio Alternatives Builder wrapper for the diagnosis-first Portfolio MRI migration.

Implementation: `src/portfolio_alternatives_builder.py`.

Status: implemented as Block 6 setup: strict `BuilderPrefill`, public Launchpad-card mapper, guided Strategy Selector, Simple Mode parameter builder, validation layer, `CandidateSetup` handoff, and runtime `portfolio_alternatives_builder.json` writing after Launchpad. It does not add a new CLI command, does not generate candidates automatically, and does not execute builders unless a caller explicitly uses the separate Block 7/back-end delegation path.

## Scope

The Portfolio Alternatives Builder converts a selected Launchpad card into editable, validated setup state. The setup step keeps the diagnosis, hypothesis, success criteria, optional Client Fit display/test criteria, tradeoff, skip rule, and decision boundary visible before any candidate is generated. A separate legacy/explicit delegation helper can still prepare one-candidate factory commands, but that helper is not the canonical Block 6 output.

It reads:

- a selected Candidate Launchpad card or equivalent request;
- a selected `candidate_method_id`.

It returns:

- a `BuilderPrefill` setup object copied from one selected Launchpad card;
- optional `client_fit_test_criteria` copied from `client_fit_check.json` as display/test rows only;
- a Strategy Selector object that maps the Builder goal to a guided default method and preserves user method changes;
- a Simple Mode parameter setup containing only the editable setup choices `goal`, `method`, `mode`, and `constraint_preset`, plus the only user-adjustable optimization fields `min_asset_weight` and `max_asset_weight`;
- validation output with one explicit setup status and `can_generate_candidate`;
- a validated `CandidateSetup` handoff when validation passes;
- a runtime Builder document at `{output_dir_final}/analysis_subject/portfolio_alternatives_builder.json` when Block 4 writes a primary Launchpad card;
- for the legacy explicit generation path only, a `PortfolioAlternativeBuildPlan` containing one candidate id and a command delegating to `run_candidate_factory.py --candidates <candidate_id>`.

It does not:

- implement candidate formulas;
- run optimizers by default;
- build weights by default;
- write candidate, comparison, verdict, or report artifacts by default;
- recommend a rebalance;
- decide whether action is justified;
- change candidate factory profiles;
- convert Client Fit target return, volatility, drawdown, or horizon into optimizer objectives,
  constraints, mandate gates, factory command changes, analysis-window changes, or weights;
- change candidate comparison schema;
- change CLI behavior;
- apply advanced constraints in V1.

Dedicated contract specs: [builder_prefill_spec.md](builder_prefill_spec.md) and [candidate_setup_spec.md](candidate_setup_spec.md).

## V1 Guided Method Mapping

V1 uses an explicit guided allowlist that maps product-facing method ids and mode to existing candidate ids. The guided product path exposes only Equal Weight, Risk Parity, Hierarchical Risk Parity, Minimum Variance, Minimum CVaR, and Maximum Diversification.

| Method id | Capped candidate id | Uncapped candidate id |
| --- | --- | --- |
| `equal_weight` | `equal_weight` | `equal_weight` |
| `risk_parity` | `risk_parity` | `risk_parity` |
| `hierarchical_risk_parity` | `hierarchical_risk_parity` | `hierarchical_risk_parity` |
| `minimum_variance` | `minimum_variance` | `minimum_variance_uncapped` |
| `minimum_cvar` | `minimum_cvar_constrained` | `minimum_cvar_uncapped` |
| `maximum_diversification` | `maximum_diversification` | `maximum_diversification_uncapped` |

The wrapper delegates to current factory plumbing rather than importing optimizer internals. This preserves formulas and existing builder behavior.

The delegated factory is a backend implementation detail. The product-facing Alternatives Builder
surface is the one-candidate request/plan boundary in this spec, not the full batch factory menu.

Hidden backend methods remain supported outside the guided product path as advanced or legacy infrastructure: Equal Weight by Asset Class, Risk Budget by Asset, Risk Budget by Asset Class, Minimum Variance Advanced Controls, Robust Mean-Variance, Scenario-Based Robust Optimization, and Legacy Policy Optimizer. They must not appear in guided Builder method options.

Supported modes are `capped` and `uncapped`. Uncapped mode always carries this warning:

```text
Uncapped mode may create concentrated portfolios. Use only for diagnostic comparison, not as an automatic rebalance recommendation.
```

Constraint presets:

| Preset | `min_asset_weight` | `max_asset_weight` | Mode |
| --- | ---: | ---: | --- |
| `conservative` | 0% | 15% | capped |
| `balanced` | 0% | 20% | capped |
| `aggressive` | 0% | 30% | capped |
| `basic_reference` | null | null | capped; Equal Weight / Risk Parity diagnostic reference tests only |
| `custom` | user field | user field | capped |
| `uncapped` | 0% | null | uncapped |

Frontend simple mode starts from the neutral default Builder preset unless the user explicitly edits
the setup. The saved Client Fit profile family must not choose the initial constraint preset, max
asset weight, min asset weight, method, mode, optimizer objective, or hidden mandate. Client Fit
targets remain visible only as non-binding context and comparison success criteria.

## Request Contract

`PortfolioAlternativeRequest` contains:

- `candidate_method_id` (required);
- optional `goal`;
- optional `source_card_id`;
- optional simple-mode fields such as mode, constraint preset, and max/min asset weight.

In V1, optional simple-mode fields are recorded as request context but are not applied to existing builders. When such fields are present, the plan emits warning `request_parameters_recorded_not_applied_v1`.

## Builder Prefill Contract

Builder prefill is the product handoff object that opens Portfolio Alternatives Builder from one selected Candidate Launchpad v3 card. It is a setup object only. It does not execute `run_candidate_factory.py`, does not write weights, and does not imply that the user should rebalance. Candidate generation remains possible only after a separate explicit user action.

In the canonical product flow, Block 4 identifies the diagnosis and
`next_diagnostic_step`, Candidate Launchpad exposes a testable card, Builder
pre-fills the candidate setup from that card, Candidate Generation runs only
after explicit user action, Current vs Candidate Comparison evaluates the
result, and Decision Verdict is the only layer that decides whether action is
justified.

The helper lives in `src/portfolio_alternatives_builder.py` and returns a plain dictionary:

```text
launchpad_card_to_builder_prefill(card, *, next_diagnostic_step=None, client_fit_check=None) -> dict
```

`build_builder_prefill_from_launchpad_card(card, *, next_diagnostic_step=None, client_fit_check=None)` remains as a backward-compatible wrapper for existing callers.

The strict Block 6 `BuilderPrefill` contract is Launchpad-derived prefill only. It is not the final user-confirmed `CandidateSetup`, and it is not a candidate portfolio. It must contain these fields:

| Field | Required meaning |
| --- | --- |
| `builder_prefill_id` | Stable prefill id derived from the selected card id or diagnosis id. |
| `source_card_id` | Launchpad `card_id`. |
| `source_diagnosis_id` | Diagnosis id copied from the Launchpad card. |
| `source_problem_id` | Problem id copied from the Launchpad card, falling back to diagnosis id when needed. |
| `card_type` | Card type copied from Launchpad. |
| `launch_status` | Launch status copied from Launchpad. |
| `method_role` | Role of `suggested_method`: `targeted_candidate_method`, `reference_benchmark`, or `custom_user_selected`; may be `null` for blocked/monitor setups. |
| `hypothesis_to_test` | Diagnosis-linked hypothesis copied from the card. |
| `next_diagnostic_step` | Problem Classification next-step object when supplied by the caller; otherwise `null` or an equivalent empty value. |
| `goal` | Builder goal copied from the card. |
| `suggested_method` | Default method id for the Builder form; `null` for blocked or monitor-only modes. |
| `alternative_methods` | Other method ids from `suggested_methods` after removing `suggested_method`. |
| `constraint_preset` | Optional simple constraint preset for the Builder form; `null` when the card does not define one. |
| `max_asset_weight` | Optional max asset weight field for concentration-style setup; `null` when unavailable. |
| `min_asset_weight` | Optional min asset weight field; `null` when unavailable. |
| `volatility_target` | Optional volatility target field; `null` when unavailable. |
| `rebalancing_frequency` | Optional simple-mode rebalancing frequency; `null` when unavailable. |
| `transaction_cost_bps` | Optional transaction-cost assumption in basis points; `null` when unavailable. |
| `success_criteria` | Card success criteria copied without rewriting. |
| `tradeoff_to_watch` | Card tradeoff copied without rewriting. |
| `when_to_skip` | Card skip rule copied without rewriting. |
| `decision_boundary` | Card decision boundary copied without weakening. |
| `is_rebalance_recommendation` | Always preserved as `false` for Launchpad-derived prefill. |
| `created_from` | Provenance marker, currently `candidate_launchpad_v3`. |
| `status` | Prefill state: `ready_for_user_confirmation`, `blocked`, `monitor_only`, or `custom_draft`. |
| `warnings` | List of setup warnings; empty when no warning applies. |

When a valid `client_fit_check.json` is supplied, `success_criteria` is extended with plain-English
Client Fit test criteria such as comparing return, volatility, historical drawdown, and worst stress
loss against the stated profile. These entries are hypothesis-test criteria for later comparison,
not optimization rules.

The strict `BuilderPrefill` contract must never contain `candidate_id`, `weights`, `candidate_status`, or `comparison_status`. Those fields belong to downstream candidate generation, candidate artifacts, or comparison layers, not Block 6 prefill.

For compatibility with the current handoff and validators, the prefill dictionary also contains these stable helper keys:

| Field | Required meaning |
| --- | --- |
| `builder_mode` | One of `guided_from_diagnosis`, `blocked_data_quality`, `monitor_only`, or `custom_builder_entry`. |
| `source` | Provenance string, normally `candidate_launchpad_v3`. |
| `suggested_methods` | Method rows copied from the Launchpad card so role/rationale are not lost. |
| `candidate_generation_allowed` | `true` only when the Builder may show an explicit generate-candidate action; `false` for data-quality blockers and monitor-only cards. This flag never means auto-generation. |
| `client_fit_context` | Optional compact Client Fit status context copied from Launchpad. |
| `client_fit_relevance_en` | Optional plain-English relevance boundary copied from Launchpad. |
| `client_fit_test_criteria` | Optional structured target rows derived from `client_fit_check.json`; rows use `display_test_criterion` or `display_context_only`. |
| `client_fit_optimizer_boundary` | Plain-English guardrail stating that Client Fit targets do not change optimizer objectives, constraints, mandate gates, analysis windows, candidate weights, or factory commands. |

Targeted diagnosis cards use `builder_mode: guided_from_diagnosis`, preserve the source diagnosis fields, and expose a guided MVP method such as `minimum_cvar`, `minimum_variance`, `maximum_diversification`, `risk_parity`, or `equal_weight`. Reference benchmark cards use `card_type: reference_benchmark_test`, keep Equal Weight and Risk Parity as reference methods, set `method_role: reference_benchmark`, and keep `is_rebalance_recommendation: false`. Monitor-only and data-quality cards use `builder_mode: monitor_only` or `blocked_data_quality`, set `candidate_generation_allowed: false`, and must not prepare an unreliable candidate factory plan.

`candidate_generation_allowed: true` means only that a user or caller may later request candidate generation. The prefill helper must not call `build_portfolio_alternative_plan()`, must not run subprocesses, and must not write generated artifacts.

## Strategy Selector Contract

The Strategy Selector is the Block 6 guided method-picking layer. It maps a Builder goal to a small product-facing method set instead of exposing the raw optimizer menu. The public helper lives in `src/portfolio_alternatives_builder.py` and returns a plain dictionary:

```text
select_builder_strategy(goal, *, card_type=None, method_role=None, selected_method=None) -> dict
```

Current goal defaults:

| Goal id | Original suggested method | Guided alternatives |
| --- | --- | --- |
| `improve_crisis_resilience` | `minimum_cvar` | `maximum_diversification`, `minimum_variance` |
| `improve_diversification` | `risk_parity` | `hierarchical_risk_parity`, `maximum_diversification` |
| `reduce_concentration` | `equal_weight` | `risk_parity`, `maximum_diversification` |
| `reduce_volatility` | `minimum_variance` | `risk_parity`, `equal_weight` |
| `compare_simple_benchmark` | `equal_weight` | `risk_parity` |

The selector accepts both canonical ids, such as `improve_crisis_resilience`, and plain labels, such as `Improve crisis resilience`. `compare_against_simple_benchmark`, `Compare against simple benchmark`, and `Compare against simple references` normalize to `compare_simple_benchmark`.

The returned object preserves `original_suggested_method`, `selected_method`, and `method_changed_by_user`. When `selected_method` differs from the guided default, `method_changed_by_user` is `true`. If a user-selected method is outside the guided methods, the selector records warning `selected_method_outside_guided_goal_methods`; `validate_builder_setup()` later blocks unsupported methods before Block 7. Unknown or data-quality goals return no method, keep `shows_raw_optimizer_menu: false`, and record `unknown_goal_no_guided_method`.

For concentration goals, the selector adds a simple max-weight hint (`constraint_preset: custom`, `max_asset_weight: 0.15`, `min_asset_weight: 0.0`). For reference benchmark goals/cards, it preserves `method_role: reference_benchmark`, uses `constraint_preset: basic_reference`, and keeps `is_rebalance_recommendation: false`. These hints are setup fields only; they are not applied to any optimizer in Block 6.

## Simple Mode Parameter Builder Contract

Simple Mode is the small editable setup surface between `BuilderPrefill` and `CandidateSetup`. The public helper lives in `src/portfolio_alternatives_builder.py` and returns a plain dictionary:

```text
build_simple_builder_parameters(prefill, *, overrides=None) -> dict
```

The editable setup fields are `goal`, `method`, `mode`, `constraint_preset`, `max_asset_weight`, and `min_asset_weight`. The only user-adjustable optimization fields are `min_asset_weight` and `max_asset_weight`. The allowed presets are `conservative`, `balanced`, `aggressive`, `custom`, `basic_reference`, and `uncapped`. Numeric fields are copied from preset defaults, Launchpad/Strategy Selector hints, or user overrides; preset labels are visible setup labels and do not secretly apply optimizer formulas. User-entered numeric overrides may be captured with `constraint_preset: custom` even when a preset originally filled the fields.

The Simple Mode object preserves `builder_prefill_id`, source card/diagnosis/problem ids, `method_role`, `original_suggested_method`, `selected_method`, `method_changed_by_user`, hypothesis, success criteria, optional Client Fit context/test criteria, tradeoff, skip rule, decision boundary, and `is_rebalance_recommendation: false`. It also exposes `parameters` and `constraints` sub-objects for UI/API convenience.

Client Fit target rows must not appear in `parameters` or `constraints`. They are displayed beside
the setup as success criteria and passed downstream so Current vs Candidate can evaluate them as
evidence. They must not alter the selected method, constraint preset, min/max weight, mode,
analysis window, candidate id, or generated weights.

Simple Mode must not expose advanced settings such as tax-aware optimization, turnover-aware objective, asset-class bounds, custom risk budgets, Robust MV lambda, advanced CVaR settings, covariance selector, expected-return model selector, volatility target, rebalancing frequency, transaction-cost controls, leverage, or shorting. If these appear in overrides, the helper raises `PortfolioAlternativesBuilderError` instead of silently accepting them.

Simple Mode must not contain `candidate_id`, `weights`, comparison output, or verdict output. It prepares setup state only and does not call candidate factory or optimizer code.

## Builder Validation Contract

Validation is the Block 6 guard before any Block 7 candidate generation. The public helper lives in `src/portfolio_alternatives_builder.py` and returns a plain dictionary:

```text
validate_builder_setup(setup) -> dict
```

For frontend/run-local generation, validation may receive non-editable `asset_count` / `n_assets`
metadata from the current input portfolio. If `max_asset_weight * asset_count < 1.0` or
`min_asset_weight * asset_count > 1.0`, validation returns `infeasible_constraints_risk` and
`can_generate_candidate: false`. The UI must show this as an actionable cap/holding-count problem
and must not unlock Candidate Generation or Comparison.

The result contains `validation_status`, `can_generate_candidate`, `validation_errors`, and `validation_warnings`. The status is exactly one of:

- `valid`
- `blocked_by_data_quality`
- `invalid_method`
- `missing_goal`
- `missing_method`
- `invalid_constraints`
- `infeasible_constraints_risk`
- `reference_benchmark_boundary_violation`

Data-quality setups are blocked first with `blocked_by_data_quality` and `can_generate_candidate: false`. Missing goal or method are explicit failures. Unsupported methods are rejected against the current guided method allowlist before Block 7. Constraint sanity rejects max weight below min weight, negative min weight, non-positive max weight, weights above 1.0, unsupported modes or presets, invalid uncapped shape, and any advanced fields that Simple Mode must not expose. When an optional `asset_count` or `n_assets` is available, validation flags obvious feasibility risk, such as a max weight too low to allocate 100% across the assets.

Reference benchmark setups must preserve `method_role: reference_benchmark`, `is_rebalance_recommendation: false`, and a decision boundary that blocks rebalance interpretation. Targeted setups must preserve `hypothesis_to_test`, non-empty `success_criteria`, and `tradeoff_to_watch`. Validation is the gate used before creating `CandidateSetup`.

## CandidateSetup Contract

`CandidateSetup` is the validated setup object that Block 7 may consume after an explicit Generate Candidate action. It is not a candidate portfolio and does not contain candidate ids, weights, metrics, stress results, comparison, or verdict fields.

The public helper is:

```text
builder_prefill_to_candidate_setup(prefill, *, edits=None) -> dict | None
```

The setup contains `candidate_setup_id`, `builder_prefill_id`, source card/diagnosis ids, source Launchpad card type, `goal`, `hypothesis_to_test`, `selected_method`, `original_suggested_method`, `method_changed_by_user`, `parameters`, `constraints`, success criteria, optional Client Fit test criteria, tradeoff, skip rule, decision boundary, `is_rebalance_recommendation: false`, `can_generate_candidate`, validation status/warnings, and `created_at`.

`CandidateSetup` is emitted only when validation is `valid`. Blocked data quality, unsupported methods, missing setup, invalid constraints, feasibility risk, and reference-boundary violations leave `candidate_setup: null`.

## Runtime Builder Artifact

When `write_block_4_diagnosis_outputs()` writes `candidate_launchpad.json`, it also calls `write_portfolio_alternatives_builder_outputs()` for the primary Launchpad card. The generated file is:

```text
{output_dir_final}/analysis_subject/portfolio_alternatives_builder.json
```

Valid targeted or reference cards produce `status: ok`, `can_generate_candidate: true`, `builder_prefill`, and `candidate_setup`. Data-quality cards produce `status: blocked`, `can_generate_candidate: false`, `reason: data_quality_blocker`, and `candidate_setup: null`.

The runtime writer does not call `run_candidate_factory.py`, does not call optimizers, and does not write `current_vs_candidate.json` or `decision_verdict.json`.

## Build Plan Contract

`PortfolioAlternativeBuildPlan` contains:

- `candidate_method_id`;
- `candidate_id`;
- `command`;
- `artifact_contract`;
- `provenance`;
- `warnings`.

The default command shape is:

```text
<python> run_candidate_factory.py --candidates <candidate_id> --execution-mode standard --output-profile site_api --then-compare
```

The returned command is a plan. It is not executed by `build_portfolio_alternative_plan()`.

## Product Boundary

This wrapper is the first backend step toward user-triggered candidate generation. It is not a full UI, saved workspace, custom optimizer configuration layer, or advanced constraints engine.

Candidate Launchpad cards remain non-portfolio artifacts. Portfolio Alternatives Builder setup is a candidate hypothesis setup, not a recommendation. Candidate generation is Block 7 and requires explicit action. Decision support remains downstream of comparison and Selection/Decision Verdict layers.

The full batch candidate factory remains preserved as backend/advanced/research infrastructure. It
must not be removed or hidden because this wrapper exists, and it must not be treated as the default
product UX unless a later accepted session explicitly changes that boundary.

## Verification

Focused tests:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_block_6_parameter_builder_simple_mode.py tests\test_block_6_builder_validation.py tests\test_portfolio_alternatives_builder.py
```

Recommended adjacent checks:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_block_6_builder_prefill_contract.py tests\test_block_6_launchpad_to_builder_prefill.py tests\test_block_6_strategy_selector.py tests\test_block_6_parameter_builder_simple_mode.py tests\test_block_6_builder_validation.py tests\test_portfolio_alternatives_builder.py tests\test_candidate_launchpad.py tests\test_portfolio_review_workflow.py
.\.venv\Scripts\python.exe run_portfolio_review.py --dry-run
```
