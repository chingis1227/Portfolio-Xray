# Portfolio Alternatives Builder Specification

This document owns the V1 on-demand Portfolio Alternatives Builder wrapper for the diagnosis-first Portfolio MRI migration.

Implementation: `src/portfolio_alternatives_builder.py`.

Status: implemented as a pure planning/delegation wrapper in code migration Session 06. It does not add a new CLI command and does not execute builders unless a caller explicitly runs a returned plan.

## Scope

The Portfolio Alternatives Builder converts a selected Launchpad method into a one-candidate build plan using existing candidate infrastructure.

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
