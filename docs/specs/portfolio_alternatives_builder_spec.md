# Portfolio Alternatives Builder Specification

This document owns the V1 on-demand Portfolio Alternatives Builder wrapper for the diagnosis-first Portfolio MRI migration.

Implementation: `src/portfolio_alternatives_builder.py`.

Status: implemented as a pure Builder prefill and planning/delegation wrapper. It does not add a new CLI command and does not execute builders unless a caller explicitly runs a returned plan. The Launchpad-card-to-Builder-prefill conversion helper and product-contract validation are current.

## Scope

The Portfolio Alternatives Builder converts a selected Launchpad card or method
into either a pre-filled candidate setup or a one-candidate build plan using
existing candidate infrastructure. The setup step keeps the diagnosis,
hypothesis, success criteria, tradeoff, skip rule, and decision boundary visible
before any candidate is generated.

It reads:

- a selected Candidate Launchpad card or equivalent request;
- a selected `candidate_method_id`.

It returns:

- a `PortfolioAlternativeBuildPlan` containing one candidate id and a command delegating to `run_candidate_factory.py --candidates <candidate_id>`.

It does not:

- implement candidate formulas;
- run optimizers by default;
- build weights by default;
- write generated artifacts by default;
- recommend a rebalance;
- decide whether action is justified;
- change candidate factory profiles;
- change candidate comparison schema;
- change CLI behavior;
- apply advanced constraints in V1.

## V1 Method Mapping

V1 uses an explicit allowlist that maps product-facing method ids to existing candidate ids:

| Method id | Candidate id |
| --- | --- |
| `equal_weight` | `equal_weight` |
| `equal_weight_by_asset_class` | `equal_weight_by_asset_class` |
| `risk_parity` | `risk_parity` |
| `hierarchical_risk_parity` | `hierarchical_risk_parity` |
| `risk_budget_by_asset` | `risk_budget_by_asset` |
| `risk_budget_by_asset_class` | `risk_budget_by_asset_class` |
| `minimum_variance` | `minimum_variance` |
| `minimum_variance_uncapped` | `minimum_variance_uncapped` |
| `minimum_variance_advanced` | `minimum_variance_advanced` |
| `minimum_cvar_constrained` | `minimum_cvar_constrained` |
| `minimum_cvar_uncapped` | `minimum_cvar_uncapped` |
| `maximum_diversification` | `maximum_diversification` |
| `maximum_diversification_uncapped` | `maximum_diversification_uncapped` |
| `robust_mv_constrained` | `robust_mv_constrained` |
| `robust_mv_uncapped` | `robust_mv_uncapped` |
| `robust_scenario` | `robust_scenario` |

The wrapper delegates to current factory plumbing rather than importing optimizer internals. This preserves formulas and existing builder behavior.

The delegated factory is a backend implementation detail. The product-facing Alternatives Builder
surface is the one-candidate request/plan boundary in this spec, not the full batch factory menu.

## Request Contract

`PortfolioAlternativeRequest` contains:

- `candidate_method_id` (required);
- optional `goal`;
- optional `source_card_id`;
- optional simple-mode fields such as constraint preset, max/min asset weight, volatility target, rebalancing frequency, and transaction cost assumption.

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
build_builder_prefill_from_launchpad_card(card, *, next_diagnostic_step=None) -> dict
```

The prefill dictionary must contain these stable keys:

| Field | Required meaning |
| --- | --- |
| `builder_mode` | One of `guided_from_diagnosis`, `blocked_data_quality`, `monitor_only`, or `custom_builder_entry`. |
| `source` | Provenance string, normally `candidate_launchpad_v3`. |
| `source_diagnosis_id` | Diagnosis id copied from the Launchpad card. |
| `source_card_id` | Launchpad `card_id`. |
| `goal` | Builder goal copied from the card. |
| `hypothesis_to_test` | Diagnosis-linked hypothesis copied from the card. |
| `next_diagnostic_step` | Problem Classification next-step object when supplied by the caller; otherwise `null` or an equivalent empty value. |
| `suggested_method` | Default selected method id, using card `default_method` when present, otherwise the first `suggested_methods[].candidate_method_id`; `null` for blocked or monitor-only modes. |
| `alternative_methods` | Other method ids from `suggested_methods` after removing `suggested_method`. |
| `suggested_methods` | Method rows copied from the Launchpad card so role/rationale are not lost. |
| `constraint_preset` | Optional simple constraint preset for the Builder form; `null` when the card does not define one. |
| `max_asset_weight` | Optional max asset weight field for concentration-style setup; `null` when unavailable. |
| `min_asset_weight` | Optional min asset weight field; `null` when unavailable. |
| `volatility_target` | Optional volatility target field; `null` when unavailable. |
| `success_criteria` | Card success criteria copied without rewriting. |
| `tradeoff_to_watch` | Card tradeoff copied without rewriting. |
| `when_to_skip` | Card skip rule copied without rewriting. |
| `card_type` | Card type copied from Launchpad. |
| `launch_status` | Launch status copied from Launchpad. |
| `method_role` | Role of `suggested_method` in Builder terms: `targeted_candidate_method`, `reference_benchmark`, or `custom_user_selected`. Current Launchpad targeted rows may use `targeted_hypothesis`; the Builder prefill normalizes that to `targeted_candidate_method`. |
| `is_rebalance_recommendation` | Always preserved as `false` for Launchpad-derived prefill. |
| `decision_boundary` | Card decision boundary copied without weakening. |
| `candidate_generation_allowed` | `true` only when the Builder may show an explicit generate-candidate action; `false` for data-quality blockers and monitor-only cards. This flag never means auto-generation. |

Targeted diagnosis cards use `builder_mode: guided_from_diagnosis`, preserve the source diagnosis fields, and expose a targeted candidate method such as `minimum_cvar_constrained`, `robust_mv_constrained`, `maximum_diversification`, or another allowlisted method. Reference benchmark cards use `card_type: reference_benchmark_test`, keep Equal Weight and Risk Parity as reference methods, set `method_role: reference_benchmark`, and keep `is_rebalance_recommendation: false`. Monitor-only and data-quality cards use `builder_mode: monitor_only` or `blocked_data_quality`, set `candidate_generation_allowed: false`, and must not prepare an unreliable candidate factory plan.

`candidate_generation_allowed: true` means only that a user or caller may later request candidate generation. The prefill helper must not call `build_portfolio_alternative_plan()`, must not run subprocesses, and must not write generated artifacts.

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

Candidate Launchpad cards remain non-portfolio artifacts. Portfolio Alternatives Builder plans are candidate hypotheses, not recommendations. Decision support remains downstream of comparison and Selection/Decision Verdict layers.

The full batch candidate factory remains preserved as backend/advanced/research infrastructure. It
must not be removed or hidden because this wrapper exists, and it must not be treated as the default
product UX unless a later accepted session explicitly changes that boundary.

## Verification

Focused tests:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_portfolio_alternatives_builder.py
```

Recommended adjacent checks:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_portfolio_alternatives_builder.py tests\test_candidate_launchpad.py tests\test_portfolio_review_workflow.py
.\.venv\Scripts\python.exe run_portfolio_review.py --dry-run
```
