# BuilderPrefill Specification

This document owns the Block 6 `BuilderPrefill` contract for Portfolio MRI.

Implementation: `src/portfolio_alternatives_builder.py`.

`BuilderPrefill` is the Launchpad-derived setup state that opens Portfolio Alternatives Builder from one selected `candidate_launchpad_v3` card. It is not a portfolio, not a candidate, not a rebalance recommendation, and not a factory execution plan.

## Product Boundary

The current product flow is:

```text
Candidate Launchpad
-> Portfolio Alternatives Builder
-> Candidate Generation
```

Block 5 ends at `candidate_launchpad.json`. Block 6 starts when a selected Launchpad card is copied into Builder setup state. Block 7 starts only after an explicit Generate Candidate action consumes a valid `CandidateSetup`.

`BuilderPrefill` must preserve the card's diagnosis context, hypothesis, success criteria, optional Client Fit display/test criteria, tradeoff, skip rule, method role, and decision boundary. It must keep `is_rebalance_recommendation: false`.

## Public Helpers

The public mapper is:

```text
launchpad_card_to_builder_prefill(card, *, next_diagnostic_step=None) -> dict
```

`build_builder_prefill_from_launchpad_card(card, *, next_diagnostic_step=None)` remains as a backward-compatible wrapper.

Both helpers also accept optional `client_fit_check=None`. When supplied, Client Fit target return,
volatility, maximum drawdown, and horizon are copied only into display/test criteria and must not
alter Builder parameters, constraints, optimizer objectives, factory commands, analysis windows, or
weights.

The strict validator is:

```text
builder_prefill_contract_violations(prefill) -> list[str]
```

## Required Fields

A valid `BuilderPrefill` contains:

- `builder_prefill_id`
- `source_card_id`
- `source_diagnosis_id`
- `source_problem_id`
- `card_type`
- `launch_status`
- `method_role`
- `hypothesis_to_test`
- `next_diagnostic_step`
- `goal`
- `suggested_method`
- `alternative_methods`
- `constraint_preset`
- `max_asset_weight`
- `min_asset_weight`
- `volatility_target`
- `rebalancing_frequency`
- `transaction_cost_bps`
- `success_criteria`
- `tradeoff_to_watch`
- `when_to_skip`
- `decision_boundary`
- `is_rebalance_recommendation`
- `created_from`
- `status`
- `warnings`

Compatibility helper fields such as `builder_mode`, `source`, `suggested_methods`, `strategy_selector`, `selected_method`, `original_suggested_method`, `method_changed_by_user`, and `candidate_generation_allowed` may also be present. `candidate_generation_allowed` means only that the Builder may show an explicit generate action later; it never means automatic candidate generation.

Optional Client Fit helper fields are `client_fit_context`, `client_fit_relevance_en`,
`client_fit_test_criteria`, and `client_fit_optimizer_boundary`. These are allowed only as
hypothesis-test/display context.

## Prohibited Fields

`BuilderPrefill` must not contain:

- `candidate_id`
- `weights`
- `candidate_status`
- `comparison_status`

Candidate identifiers, weights, portfolio metrics, stress results, comparisons, and verdicts belong downstream of Block 6.

## Statuses

Allowed `status` values are:

- `ready_for_user_confirmation`
- `blocked`
- `monitor_only`
- `custom_draft`

Data-quality Launchpad cards may create blocked prefill state, but they must not expose a ready candidate setup.

## Reference And Targeted Boundaries

Guided Builder method options are limited to `equal_weight`, `risk_parity`, `hierarchical_risk_parity`, `minimum_variance`, `minimum_cvar`, and `maximum_diversification`. Advanced or legacy backend methods such as Equal Weight by Asset Class, Risk Budget methods, Robust Mean-Variance, Scenario-Based Robust Optimization, Minimum Variance Advanced Controls, and Legacy Policy Optimizer are not shown by guided prefill.

Reference benchmark cards keep `method_role: reference_benchmark`, use Equal Weight or Risk Parity only as transparent benchmark tests, preserve the decision boundary, and keep `is_rebalance_recommendation: false`.

Targeted hypothesis cards preserve `hypothesis_to_test`, non-empty `success_criteria`, and `tradeoff_to_watch` so the Builder remains tied to the diagnosis instead of becoming a raw optimizer menu.

## Verification

Focused checks:

```text
.\.venv\Scripts\python.exe -m pytest tests	est_block_6_builder_prefill_contract.py tests	est_block_6_launchpad_to_builder_prefill.py -q
```

Adjacent contract checks:

```text
.\.venv\Scripts\python.exe -m pytest tests	est_portfolio_alternatives_builder.py tests	est_candidate_launchpad_builder_handoff.py -q
```
