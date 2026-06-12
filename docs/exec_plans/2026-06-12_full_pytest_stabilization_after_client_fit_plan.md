# Full pytest stabilization after Client Fit V1

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows `PLANS.md` from the repository root. It is self-contained for implementing a
single stabilization pass that turns the full backend `pytest -q` suite green after Client Fit V1.

## Purpose / Big Picture

Client Fit V1 was implemented and committed at baseline commit `75434571 Add Client Fit V1
foundation`. Focused Client Fit, docs, FastAPI, frontend API, and frontend type checks passed, but a
full repository backend test run still reported 13 failures. This plan records how to fix those
failures in one implementation session without rolling back Client Fit and without mixing in
unrelated dirty generated or local Codex files.

After this plan is implemented, a developer should be able to run:

    .\.venv\Scripts\python.exe -m pytest -q

from the repository root and observe zero failures.

## Progress

- [x] (2026-06-12) Session 01 created this plan-only ExecPlan in
  `docs/exec_plans/2026-06-12_full_pytest_stabilization_after_client_fit_plan.md`. No production
  code, tests, configs, generated artifacts, or Client Fit behavior were changed in Session 01.
- [x] (2026-06-12) Session 02 implemented the isolated compatibility fixes: pandas `freq="QE"`
  date-range compatibility in `conftest.py`, explicit-empty factor covariance handling in
  `src/stress_factors.py`, and verified them with the first focused pytest group.
- [x] (2026-06-12) Session 02 restored the current-vs-policy compatibility contract:
  `src/candidate_comparison.py` now treats policy-root plus `current_weights` as the combined
  current-vs-policy context even after config normalization; `src/current_vs_policy.py` applies the
  same effective-mode rule; `src/mvp_workflow.py` keeps `--materialize-current` in the
  policy-current plan.
- [x] (2026-06-12) Session 02 restored the Block 8-only boundary by keeping
  `write_block8_current_vs_candidate_only_outputs` limited to `candidate_comparison.json` and
  `current_vs_candidate.json`; site explanation bundle output remains outside this helper.
- [x] (2026-06-12) Session 02 re-baselined intentional contract drift: Block 4 golden tests now
  accept low confidence when partial X-Ray evidence is present, ETF/stock universe tests validate
  expanded structurally valid universes, and the Portfolio X-Ray golden fixture was refreshed for
  additive tail-risk methodology metadata.
- [x] (2026-06-12) Session 02 final acceptance passed: `scripts/verify_docs.py` returned OK,
  `git diff --check` returned 0 with only line-ending warnings, and full
  `.\.venv\Scripts\python.exe -m pytest -q` completed with 1911 passed and 3 skipped.

## Surprises & Discoveries

- Observation: The working tree contains unrelated dirty files that must not be included in this
  stabilization work.
  Evidence: `git status --short` shows deleted `.codex/skills/portfolio-mri-council/*` files and
  modified generated `minimum cvar constrained portfolio/*` artifacts. These are outside this plan.

- Observation: The full pytest failure audit already exists as a repo-local audit file but is not
  committed in the current working tree.
  Evidence: `docs/audits/2026-06-12_full_pytest_failure_audit_after_client_fit.md` exists and
  contains the 13-failure triage used by this plan.

- Observation: `validate_config()` normalizes top-level `current_weights` into
  `analysis_mode = analyze_current_weights`, even when the on-disk `Main portfolio/run_metadata.json`
  is a generated policy root from an optimize workflow.
  Evidence: the focused current-vs-policy group initially still returned a degraded current row and
  `current_only_diagnostic` status until comparison/status code derived an effective combined mode
  from the policy-root run metadata.

- Observation: The Portfolio X-Ray golden mismatch was additive tail-risk metadata, not a numeric
  formula drift.
  Evidence: the focused JSON diff showed only `frequency`, `method`, `metric_available`, `n_obs`,
  `window`, and `window_months` added under `block_2_2_portfolio_metrics.tail_risk_diagnostics`.

- Observation: The checked-in universe files are intentionally larger than the stale tests assumed.
  Evidence: `config/etf_universe.yml` validates with 1105 rows including
  `public_listing_ingestion`; `config/stock_universe.yml` validates with 855 rows, currently at
  least 500 `SP500` and at least 300 `R1000` records.

## Decision Log

- Decision: Do not roll back or weaken Client Fit V1 while fixing the full pytest failures.
  Rationale: The focused Client Fit acceptance surface passed, and the audit classifies the 13
  failures as broad repository failures, known pre-existing issues, compatibility drift, fixture
  drift, or adjacent product-flow contract drift.
  Date/Author: 2026-06-12 / Codex.

- Decision: Treat `unavailable` without a current sidecar and `Main portfolio/current_portfolio`
  lineage with a sidecar as the canonical current-vs-policy behavior for this stabilization pass.
  Rationale: Existing tests and older workflow docs favor this contract, and it preserves clear
  no-trade actionability semantics.
  Date/Author: 2026-06-12 / Codex.

- Decision: Treat Block 4 low confidence under partial X-Ray evidence as acceptable unless a focused
  inspection proves the confidence penalty is incorrect.
  Rationale: Low confidence with high materiality is more honest than overclaiming high confidence
  when one or more X-Ray blocks are partial.
  Date/Author: 2026-06-12 / Codex.

- Decision: Treat expanded ETF/stock universes as intentional unless validation or current docs prove
  they are accidental.
  Rationale: The failing universe tests assert stale fixed-size expectations; the correct product
  invariant is valid records and documented source/snapshot, not an old hard-coded count.
  Date/Author: 2026-06-12 / Codex.

- Decision: In current-vs-policy artifacts, treat a policy-root `Main portfolio/run_metadata.json`
  plus configured `current_weights` as the combined current-vs-policy workflow even when the
  normalized config object says `analyze_current_weights`.
  Rationale: Config normalization is useful for current-only diagnostics, but the combined workflow
  is identified by on-disk policy-root lineage plus a materialized or expected current sidecar.
  Date/Author: 2026-06-12 / Codex.

- Decision: Keep the site explanation bundle outside
  `write_block8_current_vs_candidate_only_outputs`.
  Rationale: The helper name and Block 8 boundary contract are narrower than the post-compare/report
  presentation path; returning the site bundle made stale downstream-output hygiene ambiguous.
  Date/Author: 2026-06-12 / Codex.

- Decision: Refresh the Portfolio X-Ray golden fixture for additive tail-risk methodology metadata.
  Rationale: The live builder exposes useful provenance fields without changing shared numeric
  metrics; the fixture, not the builder, was stale.
  Date/Author: 2026-06-12 / Codex.

## Outcomes & Retrospective

Session 01 outcome: the plan is now written in the repository as a Markdown ExecPlan. Implementation
has intentionally not started.

Session 02 final outcome: the stabilization pass is complete. All focused verification groups listed
in this plan passed, documentation verification passed, whitespace diff checking passed, and full
repository backend pytest completed with 1911 passed and 3 skipped in 23 minutes 35 seconds. No
Client Fit V1 behavior, public Client Fit API, frontend route, Supabase persistence model, or Client
Fit artifact schema was changed.

## Context and Orientation

The baseline Client Fit commit is:

    75434571 Add Client Fit V1 foundation

The failure audit that this plan implements is:

    docs/audits/2026-06-12_full_pytest_failure_audit_after_client_fit.md

The full pytest result from that audit was:

    13 failed, 1898 passed, 3 skipped in 1603.45s (0:26:43)

The 13 failures are grouped into these eight workstreams:

1. Current-vs-policy / candidate-comparison status and sidecar lineage drift: 3 failures.
2. Block 4 confidence / no-trade-gate golden fixture drift: 2 failures.
3. Universe seed-size expectation drift: 2 failures.
4. Pandas quarterly frequency compatibility: 2 failures.
5. Block 8-only output boundary now returns an extra site-explanation path: 1 failure.
6. Factor covariance empty-input guard regression: 1 failure.
7. MVP workflow materialize-current planning mismatch: 1 failure.
8. Portfolio X-Ray golden document drift: 1 failure.

Do not include unrelated dirty files in this work:

    .codex/skills/portfolio-mri-council/*
    minimum cvar constrained portfolio/*

Do not modify Client Fit V1 behavior unless a failing test directly proves a Client Fit regression,
which the audit does not currently show.

## Plan of Work

Session 02 must implement the fixes in this order.

First, apply the isolated compatibility fixes. In `conftest.py`, extend the existing pandas date
range compatibility shim so unsupported `freq="QE"` maps to a supported quarter-end alias such as
`Q` or `Q-DEC`. In `src/stress_factors.py::factor_covariance_analytics`, distinguish an omitted
`factor_returns` argument from an explicitly supplied empty DataFrame: `None` may load factor data,
but an explicit empty frame must return the existing unavailable response with
`insufficient_factor_history` and `no_factor_rows_after_loading`.

Second, fix current-vs-policy and MVP workflow contracts. In `src/candidate_comparison.py`, make the
`current` row unavailable when optimize mode has current weights but no valid `current_portfolio`
sidecar, and make it point to `Main portfolio/current_portfolio` when the sidecar exists. Preserve
`analysis_setup_summary.current_materialization_root` when the sidecar is valid. In
`src/mvp_workflow.py`, make `WORKFLOW_POLICY_CURRENT` add `run_report.py --materialize-current` when
current weights are supplied instead of being swallowed by an analyze-current early return.

Third, handle contract and fixture drift. Update the Block 4 tests to accept low confidence when the
golden fixture has partial X-Ray evidence while preserving high materiality and stress confirmation.
Update ETF/stock universe tests and any owning docs to validate the expanded universe rather than old
hard-coded sizes, unless inspection proves the expanded files are accidental. Keep
`write_block8_current_vs_candidate_only_outputs` as a Block 8-only helper that returns only
`candidate_comparison_json` and `current_vs_candidate_json`; any site explanation bundle belongs to a
separate post-compare/report path. For the Portfolio X-Ray golden mismatch, run a focused diff first;
if the live output is canonical, refresh the golden fixture with a note, otherwise fix the builder.

Fourth, synchronize documentation. Update this ExecPlan `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` as Session 02 proceeds. If universe, Block 8, or
Portfolio X-Ray contracts change, update the owning specs or changelog so tests and docs agree.

## Concrete Steps

Work from repository root:

    D:\Рабочий стол\КУРСОР ТУЛА ДИАГНОСТИКА

Use Windows PowerShell and the project virtual environment:

    .\.venv\Scripts\python.exe

Session 01 commands:

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check -- docs/exec_plans/2026-06-12_full_pytest_stabilization_after_client_fit_plan.md

Session 02 focused verification commands:

    .\.venv\Scripts\python.exe -m pytest tests\test_macro_indicators.py::test_quarterly_ffill_monthly_three_m_change_for_gdpnow tests\test_macro_indicators.py::test_quarterly_ffill_monthly_yoy_for_eci tests\test_factor_covariance.py::test_factor_covariance_empty_factor_frame_returns_explicit_skip_reason -q

    .\.venv\Scripts\python.exe -m pytest tests\test_candidate_comparison.py::test_current_unavailable_in_optimize_mode tests\test_current_vs_policy_workflow.py::test_combined_context_both_available tests\test_current_vs_policy_workflow.py::test_current_weights_without_sidecar tests\test_mvp_workflow.py::test_policy_current_adds_materialize_when_weights_set -q

    .\.venv\Scripts\python.exe -m pytest tests\test_block_4_no_trade_gate.py::test_golden_fixture_proceeds_to_launchpad tests\test_block_4_severity_confidence.py::test_golden_fixture_assigns_severity_and_confidence tests\test_etf_universe.py::test_seed_universe_validates_and_has_target_size tests\test_stock_universe.py::test_seed_universe_validates_and_has_expected_size tests\test_block8_current_vs_candidate_boundary.py::test_block8_only_writes_comparison_without_refreshing_stale_verdict tests\test_portfolio_xray_contract.py::test_live_build_matches_golden_document -q

Session 02 final acceptance commands:

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check
    .\.venv\Scripts\python.exe -m pytest -q

## Validation and Acceptance

Session 01 is accepted when this plan file exists, docs verification passes, the plan file has no
whitespace errors, and no code/test/config fix has been made.

Session 02 is accepted only when all focused verification groups pass, `scripts/verify_docs.py`
passes, `git diff --check` passes, and full repository backend `pytest -q` completes with zero
failures. If full pytest still fails, Session 02 must record the remaining failures in this plan and
must not claim completion.

## Idempotence and Recovery

All fixes should be small and independently verifiable. If a focused group fails after a change,
revert only the owning change for that group or record the blocker before continuing. Do not delete
or regenerate broad output folders to hide failures. Do not stage or commit the unrelated dirty
`.codex/skills/portfolio-mri-council/*` deletions or `minimum cvar constrained portfolio/*` generated
artifact changes.

## Artifacts and Notes

Audit source:

    docs/audits/2026-06-12_full_pytest_failure_audit_after_client_fit.md

Client Fit baseline commit:

    75434571 Add Client Fit V1 foundation

Known unrelated dirty paths at Session 01 start:

    .codex/skills/portfolio-mri-council/SKILL.md
    .codex/skills/portfolio-mri-council/agents/openai.yaml
    .codex/skills/portfolio-mri-council/references/project-canon.md
    minimum cvar constrained portfolio/baseline_weights_metadata.json
    minimum cvar constrained portfolio/summary.json
    minimum cvar constrained portfolio/weights.json

## Interfaces and Dependencies

The stabilization should preserve these existing interfaces:

    current row status in optimize mode without current sidecar = unavailable
    current row artifact_root with valid sidecar = Main portfolio/current_portfolio
    factor_covariance_analytics(empty explicit factor_returns) = unavailable / insufficient_factor_history
    Block 8-only writer returns candidate_comparison_json and current_vs_candidate_json only

No public Client Fit API, frontend route, Supabase persistence model, or Client Fit artifact schema
should change in this stabilization plan.

Revision note, 2026-06-12 Session 02: this plan was updated from implementation-pending to
implementation-complete after the focused fixes, documentation synchronization, and full pytest
acceptance run. The update records the effective combined current-vs-policy mode decision, the
Block 8 boundary decision, the universe/golden fixture re-baselines, and the final verification
evidence so a future reader can restart from this file without needing chat context.
