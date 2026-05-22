# Downstream Decision Readiness Specification

Status: **implemented** (Phase 17 Session 08, `RM-1027`).

This document defines how **Blocks 6–7** and later decision modules consume
`candidate_comparison.json` without treating partial menus, degraded optimizer rows, or stale
artifacts as fair cross-candidate evidence.

It does not own metric formulas, stress scenarios, optimizer mathematics, selection ranking, or
package narrative. Those remain in [metrics_specification.md](metrics_specification.md),
[data_policy_spec.md](data_policy_spec.md), [stress_testing_spec.md](stress_testing_spec.md),
[candidate_comparison_spec.md](candidate_comparison_spec.md),
[portfolio_health_score_spec.md](portfolio_health_score_spec.md),
[robustness_scorecard_spec.md](robustness_scorecard_spec.md), and
[selection_engine_spec.md](selection_engine_spec.md).

Implementation: [src/downstream_decision_readiness.py](../../src/downstream_decision_readiness.py).

## Scope

| Block | Role in V1 | Primary evidence | This spec governs |
| --- | --- | --- | --- |
| 6 | Backtest / historical metrics | `snapshot_10y.json`, comparison `metrics` / `drawdown` | When metrics may be used for **fair** vs **diagnostic-only** comparison |
| 7 | Candidate stress evaluation | Comparison `stress` embed; optional `stress_report.json` | When full stress artifacts may be loaded beyond the comparison embed |
| 8–10 | Health, selection, action, package | Comparison + scorecards | Cross-reference favoring rules (`RM-1022`); package truthfulness in Session 09 |

## Inputs (authoritative)

Consumers must treat these comparison fields as the handoff contract:

| Field | Use |
| --- | --- |
| `comparison_baseline_candidate_id` | Baseline for regret/backtest narrative (typically `analysis_subject`) |
| `candidate_menu.review_mode` | `core` vs `full` — never infer full optimizer shootout from core |
| `candidate_menu.is_partial_menu` | When true, rankings are diagnostic only for the **intended** profile |
| `candidate_menu.intended_menu_profile_id` | e.g. `core_v1` vs `default_v1` |
| Row `status` | `available`, `degraded`, `unavailable` |
| `construction_disclosure.optimization_readiness.fair_comparison_ready` | Optimizer/robust fair-comparison gate |
| `review_bundle_context` (when present) | Review fingerprint and mode/subject alignment (Session 07) |

## Eligibility matrix

### Block 6 — backtest / metrics evidence

| Row condition | Diagnostic metrics (display / health partial) | Fair cross-candidate backtest compare |
| --- | --- | --- |
| `available`, non-optimizer-backed | Allowed | Allowed |
| `available`, optimizer-backed, `fair_comparison_ready: true` | Allowed | Allowed |
| `available`, optimizer-backed, `fair_comparison_ready: false` | Allowed | **Blocked** |
| `degraded`, optimizer-backed | Allowed with warning | **Blocked** |
| `degraded`, non-optimizer-backed | Allowed | Diagnostic only (no fair winner) |
| `unavailable` | **Blocked** | **Blocked** |

Dynamic NaN-safe backtest mechanics remain in [data_policy_spec.md](data_policy_spec.md). This spec
only gates **which comparison rows** may feed fair historical comparison.

### Block 7 — candidate stress evaluation

| Row condition | Comparison `stress` embed | Load `artifact_root/stress_report.json` |
| --- | --- | --- |
| `available` | Allowed | Allowed when file exists |
| `degraded`, non-optimizer-backed | Allowed | Allowed when file exists |
| `degraded`, optimizer-backed | Allowed (summary only) | **Blocked** — do not extend from file |
| `unavailable` | Empty / not scored | **Blocked** |

Loading a degraded optimizer's on-disk stress report would mix incomplete optimizer evidence with
full-file stress suites and mis-rank stress behavior. Consumers must use the comparison embed only.

### Blocks 8–10 — favoring and package truthfulness

Selection **favoring** uses the same optimizer fair-comparison rule via
`candidate_eligible_for_favoring` in [src/optimization_readiness.py](../../src/optimization_readiness.py)
(Session 03, `RM-1022`). Health and robustness scorecards may still score `degraded` rows for
diagnostics with warning `degraded_optimizer_diagnostic_only_not_favored`.

**Decision package** ([decision_package_reporting_spec.md](decision_package_reporting_spec.md),
Session 09 `RM-1028`) must surface partial-menu and degraded-optimizer boundaries in
`decision_package_summary` via [src/package_truthfulness.py](../../src/package_truthfulness.py).
Action plans emit `partial_candidate_menu_action_context` when `candidate_menu.is_partial_menu`
is true.

## Partial menu boundaries

When `candidate_menu.is_partial_menu` is `true`:

- Emit run-level warning `partial_candidate_menu` in health, selection, and decision package writers.
- Do not describe the run as a complete `default_v1` optimizer shootout.
- Fair backtest/stress comparison applies only among rows that pass the eligibility matrix **within
  the partial menu**; missing registry ids are not implicit failures.

## Machine helpers

| Function | Meaning |
| --- | --- |
| `candidate_eligible_for_diagnostic_backtest` | Row has `available` or `degraded` status |
| `candidate_eligible_for_fair_backtest_compare` | Fair Block 6 compare allowed |
| `may_load_candidate_stress_report` | Block 7 may open per-candidate `stress_report.json` |
| `build_downstream_readiness` | Optional per-row block with ineligibility reason codes |

Reason codes (stable strings):

- `unavailable_no_backtest_evidence`
- `degraded_backtest_diagnostic_only`
- `optimizer_not_fair_comparison_ready`
- `unavailable_no_stress_artifact`
- `degraded_optimizer_stress_comparison_embed_only`

## Consumer requirements

| Module | Requirement |
| --- | --- |
| [portfolio_health_score.py](../../src/portfolio_health_score.py) | Before loading `stress_report.json`, call `may_load_candidate_stress_report` |
| [robustness_scorecard.py](../../src/robustness_scorecard.py) | Same stress guard |
| Future backtest-on-candidates entrypoints | Call `candidate_eligible_for_fair_backtest_compare` before fair ranking |

## Non-goals

- New metrics, stress formulas, or optimizer constraints
- UI
- Changing comparison row `status` rules (owned by candidate comparison builder)
## Verification

Offline integration: `tests/test_blocks_6_7_downstream_integration.py`,
`tests/test_blocks_8_10_downstream_integration.py`.

Unit helpers: `tests/test_downstream_decision_readiness.py`, `tests/test_package_truthfulness.py`.
