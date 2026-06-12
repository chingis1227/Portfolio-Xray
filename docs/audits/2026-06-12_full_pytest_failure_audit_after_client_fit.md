# Full pytest failure audit after Client Fit V1 foundation

Date: 2026-06-12
Branch/commit baseline: `codex/client-fit-v1` at `75434571 Add Client Fit V1 foundation`
Source log: `output/pytest_full_2026-06-12_client_fit_session21.log` (generated log, not source)

## Scope

This audit triages the 13 failures from the post-Client-Fit full repository pytest run. It is an
investigation record only: no behavior was changed and no tests were re-baselined as part of this
audit.

The Client Fit acceptance surface is already verified separately. Focused Client Fit tests, docs
verification, FastAPI contract governance, frontend API tests, frontend typecheck, stale-reference
search, advice-language guardrail search, and staged diff check all passed before commit
`75434571`. The failures below are broad repository failures that block a clean merge/PR if the
policy is "full pytest must be green".

## Run result

Command:

    .\.venv\Scripts\python.exe -m pytest -q

Observed result:

    13 failed, 1898 passed, 3 skipped in 1603.45s (0:26:43)

Dirty working tree at audit time, not included in the Client Fit commit:

- deleted `.codex/skills/portfolio-mri-council/*` files;
- modified generated `minimum cvar constrained portfolio/*` artifacts.

These dirty files were not staged for the Client Fit commit. They should be cleaned or handled
separately before merge/PR, but they do not explain most pytest failures below.

## Executive summary

The 13 failures fall into 8 workstreams:

1. Current-vs-policy / candidate-comparison status and sidecar lineage drift: 3 failures, partly
   known before Client Fit.
2. Block 4 confidence / no-trade-gate golden fixture drift: 2 failures.
3. Universe seed-size expectation drift: 2 failures.
4. Pandas quarterly frequency compatibility: 2 failures.
5. Block 8-only output boundary now returns an extra site-explanation path: 1 failure.
6. Factor covariance empty-input guard regression: 1 failure, known before Client Fit.
7. MVP workflow materialize-current planning mismatch: 1 failure, known before Client Fit.
8. Portfolio X-Ray golden document drift: 1 failure.

At least these failures were already documented before Client Fit in
`docs/audits/2026-05-27_core_mvp_blocks_1_3_cleanup_acceptance_audit.md`: candidate comparison
current-row status, both current-vs-policy workflow failures, factor covariance empty-frame status,
and MVP workflow materialize-current planning. Client Fit did not introduce those known failures.

## Failure matrix

| # | Test | Observed failure | Likely class | Pre-existing evidence | Recommended next action |
| --- | --- | --- | --- | --- | --- |
| 1 | `tests/test_block8_current_vs_candidate_boundary.py::test_block8_only_writes_comparison_without_refreshing_stale_verdict` | Helper returned `site_explanation_bundle_json` in addition to `candidate_comparison_json` and `current_vs_candidate_json`. | Contract drift after site-explanation bundle integration. | Not in 2026-05-27 audit. | Decide whether `write_block8_current_vs_candidate_only_outputs` is still truly Block 8-only. If yes, stop returning/writing the site bundle there. If site bundle is intentionally post-compare support, update the test/spec name and expected path set. |
| 2 | `tests/test_block_4_no_trade_gate.py::test_golden_fixture_proceeds_to_launchpad` | Expected reason `Primary confidence is high`; actual reasons include `Primary problem materiality is high` and low-confidence/data-quality caveats. | Golden expectation drift in Block 4 confidence wording. | Not in 2026-05-27 audit. | Inspect `src/block_4/no_trade_gate.py`, `src/block_4/problem_scoring.py`, and golden X-Ray fixture partial statuses. Decide whether low confidence is now correct because X-Ray blocks are partial. Update fixture/test only if product accepts the lower confidence. |
| 3 | `tests/test_block_4_severity_confidence.py::test_golden_fixture_assigns_severity_and_confidence` | `weak_hedge_behavior.confidence` is `low`; test expected `high` or `medium`. | Same Block 4 confidence/golden drift as #2. | Not in 2026-05-27 audit. | Same as #2; fix scoring only if confirmed stress evidence should override partial-data confidence penalty. Otherwise re-baseline expectation to low confidence with rationale. |
| 4 | `tests/test_candidate_comparison.py::test_current_unavailable_in_optimize_mode` | `current.status` is `degraded`; test expects `unavailable`. | Current-row availability contract drift. | Present in 2026-05-27 audit and Client Fit ExecPlan surprises. | Reconcile `build_candidate_comparison()` with `current_vs_policy_workflow_spec.md`: in optimize mode without a current sidecar, either return unavailable/missing-current-report or intentionally accept degraded and update tests/specs. |
| 5 | `tests/test_current_vs_policy_workflow.py::test_combined_context_both_available` | `cur.artifact_root` is `Main portfolio`, not ending with `current_portfolio`. | Sidecar lineage/root resolution drift. | Present in 2026-05-27 audit. | Fix current sidecar discovery so current row points at `Main portfolio/current_portfolio` when sidecar exists, and `analysis_setup_summary.current_materialization_root` matches. |
| 6 | `tests/test_current_vs_policy_workflow.py::test_current_weights_without_sidecar` | `current.status` is `degraded`; test expects `unavailable`. | Same current-row status contract drift as #4. | Present in 2026-05-27 audit. | Same as #4. Treat #4-#6 as one focused fix session. |
| 7 | `tests/test_etf_universe.py::test_seed_universe_validates_and_has_target_size` | ETF universe length is 1105; test expects 150-250. | Seed fixture/spec expectation drift. | Not in 2026-05-27 audit. | Determine whether `config/etf_universe.yml` was intentionally expanded. If yes, update test bounds/docs. If no, restore seed universe to expected Core MVP size. |
| 8 | `tests/test_factor_covariance.py::test_factor_covariance_empty_factor_frame_returns_explicit_skip_reason` | Empty factor frame returns `status == available`; test expects `unavailable` with `insufficient_factor_history`. | Empty-input guard regression. | Present in 2026-05-27 audit. | Add an early guard in `src/stress_factors.py::factor_covariance_analytics` for empty `factor_returns` after loading, preserving diagnostics. This should be a small isolated fix. |
| 9 | `tests/test_macro_indicators.py::test_quarterly_ffill_monthly_three_m_change_for_gdpnow` | `pd.date_range(..., freq="QE")` raises `ValueError: Invalid frequency: QE`. | Pandas frequency compatibility gap in test harness. | Not in 2026-05-27 audit. | Extend root `conftest.py` `_compat_date_range` to translate unsupported `QE` to a supported quarterly-end alias such as `Q` / `Q-DEC`, similar to the existing `ME`/`M` compatibility shim. |
| 10 | `tests/test_macro_indicators.py::test_quarterly_ffill_monthly_yoy_for_eci` | Same `QE` compatibility failure. | Same as #9. | Not in 2026-05-27 audit. | Same as #9. |
| 11 | `tests/test_mvp_workflow.py::test_policy_current_adds_materialize_when_weights_set` | Planned command string did not include `--materialize-current`; observed command path involved `rebuild_pdf_reports.py`. | Workflow planning / config current-weights detection drift. | Present in 2026-05-27 audit. | Inspect `src/mvp_workflow.py::_has_current_weights`, `validate_config()`, and test tmp project script resolution. The source code appears to add `--materialize-current` when `_has_current_weights(cfg)` is true, so likely config normalization or wrapper path behavior is the real break. |
| 12 | `tests/test_portfolio_xray_contract.py::test_live_build_matches_golden_document` | Live golden document differs from checked fixture under `block_2_2_portfolio_metrics`; full log does not show exact diff. | Golden fixture drift. | Not in 2026-05-27 audit. | Run this single test with `-vv` or a small JSON diff script, then either fix the builder if unintended or refresh the golden fixture with a decision note if the new metrics surface is canonical. |
| 13 | `tests/test_stock_universe.py::test_seed_universe_validates_and_has_expected_size` | Stock universe length is 855; test expects exactly 503. | Seed fixture/spec expectation drift. | Not in 2026-05-27 audit. | Determine whether `config/stock_universe.yml` intentionally expanded beyond S&P 500 snapshot. If yes, update expected count/header/source docs. If no, restore seed universe to 503 records. |

## Recommended fix order

### 1. Quick isolated compatibility fixes

Start with failures that are likely small and low-risk:

1. `QE` pandas compatibility in `conftest.py` (#9-#10).
2. Empty factor covariance guard in `src/stress_factors.py` (#8).

These are independent of product flow and should be easy to verify with three focused tests.

### 2. Current-vs-policy / candidate-comparison contract fix

Handle #4-#6 together. This is the most important product-flow blocker because it affects current
portfolio lineage and no-trade actionability. Do not patch each assertion separately; decide the
canonical status rule first:

- If current weights exist but the current sidecar report is missing in optimize mode, should the
  current row be `unavailable` or `degraded`?
- If the current sidecar exists, should `artifact_root` always point to `Main portfolio/current_portfolio`?

The existing tests and older docs favor `unavailable` when the sidecar is missing and sidecar-root
lineage when it exists.

### 3. Block 4 confidence / golden fixture decision

Handle #2-#3 together. The current output says materiality is high but confidence is low because
some X-Ray blocks are partial. That may be a better diagnostic truth than the old high-confidence
expectation. This needs a product/spec decision before code changes.

### 4. Universe seed-size decision

Handle #7 and #13 together. These are likely fixture/spec drift rather than runtime bugs. The key
question is whether the expanded ETF/stock universes are intentional current data. If intentional,
change tests and docs; if accidental, restore the seed files.

### 5. Block 8 and X-Ray golden drift

Handle #1 and #12 last unless they block the intended PR policy. Both are contract/golden drift:
Block 8 needs a boundary decision around optional site-explanation output, and Portfolio X-Ray needs
a targeted diff before choosing fix vs fixture refresh.

## Focused verification commands for follow-up sessions

Run only the relevant subset for each fix before attempting full pytest again:

    .\.venv\Scripts\python.exe -m pytest tests\test_macro_indicators.py::test_quarterly_ffill_monthly_three_m_change_for_gdpnow tests\test_macro_indicators.py::test_quarterly_ffill_monthly_yoy_for_eci -q

    .\.venv\Scripts\python.exe -m pytest tests\test_factor_covariance.py::test_factor_covariance_empty_factor_frame_returns_explicit_skip_reason -q

    .\.venv\Scripts\python.exe -m pytest tests\test_candidate_comparison.py::test_current_unavailable_in_optimize_mode tests\test_current_vs_policy_workflow.py::test_combined_context_both_available tests\test_current_vs_policy_workflow.py::test_current_weights_without_sidecar tests\test_mvp_workflow.py::test_policy_current_adds_materialize_when_weights_set -q

    .\.venv\Scripts\python.exe -m pytest tests\test_block_4_no_trade_gate.py::test_golden_fixture_proceeds_to_launchpad tests\test_block_4_severity_confidence.py::test_golden_fixture_assigns_severity_and_confidence -q

    .\.venv\Scripts\python.exe -m pytest tests\test_etf_universe.py::test_seed_universe_validates_and_has_target_size tests\test_stock_universe.py::test_seed_universe_validates_and_has_expected_size -q

    .\.venv\Scripts\python.exe -m pytest tests\test_block8_current_vs_candidate_boundary.py::test_block8_only_writes_comparison_without_refreshing_stale_verdict tests\test_portfolio_xray_contract.py::test_live_build_matches_golden_document -q

Only after the focused groups are green should full repository pytest be rerun.

## Audit verdict

Client Fit V1 should not be rolled back to address these failures. The failures are either known
pre-existing repository issues, compatibility/test-harness drift, fixture/golden drift, or adjacent
product-flow contract drift. The cleanest next engineering move is a separate stabilization branch or
commit series focused on the groups above, starting with the small compatibility fixes and the
current-vs-policy lineage/status contract.
