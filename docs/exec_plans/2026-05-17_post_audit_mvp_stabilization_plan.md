# Post-Audit MVP Stabilization Plan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.
This document follows `PLANS.md` at the repository root.

## Purpose / Big Picture

The project already emits the main file-first decision-support artifacts. A user can run the
analysis and receive comparison, scoring, selection, action, monitoring, and decision-package files.
The next useful improvement is to make that MVP reliable enough that another developer or agent can
trust the documents, data behavior, diagnostics, generated outputs, tests, and command flow.

When this plan is complete, the project should have a coherent file-first path from input to action:
`input -> diagnosis -> comparison -> action`. Full UI/workspace work is intentionally outside this
plan and should return only after stabilization is closed.

## Progress

- [x] (2026-05-17) Session 01 started from the user's accepted roadmap and read `PLANS.md`,
  `RULES.md`, `WORKFLOW.md`, audit/ExecPlan registers, roadmap, changelog, and known issues.
- [x] (2026-05-17) Session 01 created the repeat MVP readiness audit handoff and this active
  ExecPlan.
- [x] (2026-05-17) Session 01 updated the audit register, ExecPlan register, roadmap, known issues,
  and changelog to point to this plan.
- [x] (2026-05-17) Session 01 verification passed: `.venv\Scripts\python.exe scripts\verify_docs.py`
  returned `docs verification: OK`.
- [x] (2026-05-17) Session 02 synchronized top-level source-of-truth status wording in
  `README.md`, `ARCHITECTURE.md`, and `PRODUCT.md` so implemented file-first V1 artifacts are no
  longer presented as target/TBD work.
- [x] (2026-05-17) Session 02 verification passed: `.\.venv\Scripts\python.exe scripts\verify_docs.py`,
  `.\.venv\Scripts\python.exe -m pytest tests\test_docs_links.py -q --basetemp='tmp\pytest_mvp_session_02_docs'`,
  and targeted stale-reference search returned no matches in source-of-truth docs/specs.
- [x] (2026-05-17) Session 03 synchronized risk-free and cash policy wording in `DATA.md`,
  `docs/specs/input_assumptions_spec.md`, and `docs/specs/metrics_specification.md`.
- [x] (2026-05-17) Session 03 added focused config regressions proving EUR default cash/risk-free
  resolution and explicit cash/risk-free requirements for unsupported non-USD currencies.
- [x] (2026-05-17) Session 03 verification passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_config_weights_sync.py tests\test_input_assumptions.py -q --basetemp='tmp\pytest_mvp_session_03_policy'`,
  `.\.venv\Scripts\python.exe scripts\verify_docs.py`, and stale-policy search returned no matches
  in the updated source-of-truth docs.
- [x] (2026-05-17) Session 04 added resolved asset-currency metadata fingerprints to monthly
  return-panel cache keys and monthly cache metadata.
- [x] (2026-05-17) Session 04 added focused cache regressions proving stable fingerprints, key
  invalidation after asset currency changes, and `load_monthly_data_shared` fingerprint threading.
- [x] (2026-05-17) Session 04 verification passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_data_cache_key.py -q --basetemp='tmp\pytest_mvp_session_04_cache'`
  and `.\.venv\Scripts\python.exe scripts\verify_docs.py`.
- [x] (2026-05-17) Session 05 fixed NaN-safe cash fallback diagnostics so
  `n_months_cash_fallback` counts months where missing positive risk-sleeve weight remains after
  redistribution and is applied to the cash proxy.
- [x] (2026-05-17) Session 05 added focused regressions proving all-risk-missing residual cash is
  counted, peer redistribution is not counted as cash fallback, and planned cash exposure without
  missing returns is not counted as fallback.
- [x] (2026-05-17) Session 05 verification passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_backtest_nan_safe.py -k 'not test_run_report_default_mode_uses_dynamic_engine' -q --basetemp='tmp\pytest_mvp_session_05_cash'`
  and `.\.venv\Scripts\python.exe scripts\verify_docs.py`.
- [x] (2026-05-17) Session 06 fixed monthly and daily time-to-recovery so the recovery path is
  anchored to the peak and trough of the maximum drawdown, not the last or global equity peak.
- [x] (2026-05-17) Session 06 added focused regressions for recovered max-drawdown paths,
  unrecovered paths, no-drawdown `ttr = 0`, and the daily diagnostic analog.
- [x] (2026-05-17) Session 06 verification passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_metrics_drawdown.py -q --basetemp='tmp\pytest_mvp_session_06_ttr'`,
  `.\.venv\Scripts\python.exe -m pytest tests\test_metrics_drawdown.py tests\test_regime_portfolio_metrics.py tests\test_returns_frequency.py tests\test_portfolio_commentary.py tests\test_candidate_comparison.py -q --basetemp='tmp\pytest_mvp_session_06_adjacent'`,
  and `.\.venv\Scripts\python.exe scripts\verify_docs.py`.
- [x] (2026-05-17) Session 06 broad verification ran:
  `.\.venv\Scripts\python.exe -m pytest -q --basetemp='tmp\pytest_mvp_session_06_full'`
  reported 449 passed and 2 permission-only failures creating `output/codex_test_artifacts/*`;
  the two failed tests passed on an approved rerun outside the sandbox.
- [x] (2026-05-17) Session 07 completed: `factor_multicollinearity` now emits `assessment_en` as the
  primary field; `portfolio_commentary` reads `assessment_en` first and falls back to legacy
  `assessment_ru` only for older artifacts; updated stress spec, cursor rule, and focused tests.
- [x] (2026-05-17) Session 07 verification passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_factor_multicollinearity.py tests\test_portfolio_commentary.py -q --basetemp='tmp\pytest_mvp_session_07_schema'`
  (`6 passed`) and `.\.venv\Scripts\python.exe scripts\verify_docs.py`.
- [x] (2026-05-18) Session 08 completed: regenerated Main, Equal-Weight, and Risk-Parity
  representative outputs; fixed EW/RP comparison generator English labels and ASCII null
  formatting; added FRED CSV fallback for environments without pandas_datareader/distutils;
  added `scripts/scan_generated_outputs.py` and `tests/test_generated_output_language.py`.
- [x] (2026-05-18) Session 08 verification passed:
  `.\.venv\Scripts\python.exe scripts\scan_generated_outputs.py` (77 files),
  `.\.venv\Scripts\python.exe -m pytest tests\test_generated_output_language.py -q --basetemp='tmp\pytest_mvp_session_08_qa'`,
  `.\.venv\Scripts\python.exe scripts\verify_docs.py`; CLI regen via `run_equal_weight.py`,
  `run_risk_parity.py`, and `run_report.py`.
- [x] (2026-05-18) Session 09 completed: offline MVP pipeline smoke test
  (`tests/test_mvp_pipeline_offline.py`, `tests/mvp_offline_fixtures.py`) with network guards;
  documented in `TESTING.md`.
- [x] (2026-05-18) Session 09 verification passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_mvp_pipeline_offline.py -q --basetemp='tmp\pytest_mvp_session_09'`
  (`2 passed`) and `.\.venv\Scripts\python.exe scripts\verify_docs.py`.
- [x] (2026-05-18) Session 10 completed: documented file-first MVP stages in
  `docs/operational_runbook.md`; added thin orchestrator `run_mvp_workflow.py` /
  `src/mvp_workflow.py` with workflow profiles (`policy-only`, `policy-current`,
  `full-decision`, `diagnosis-only`); updated README, SPEC, AGENTS, TESTING; added
  `tests/test_mvp_workflow.py`.
- [x] (2026-05-18) Session 10 verification passed:
  `.\.venv\Scripts\python.exe -m pytest tests\test_mvp_workflow.py -q --basetemp='tmp\pytest_mvp_session_10'`
  and `.\.venv\Scripts\python.exe scripts\verify_docs.py`.
- [x] (2026-05-18) Session 11 completed: broad verification (`462 passed` full pytest with
  `--basetemp=tmp/pytest_mvp_session_11`), `scripts/verify_docs.py`, `scripts/scan_generated_outputs.py`
  (77 files); synced partial utility UI wording in `README.md` and `ARCHITECTURE.md`; removed
  `KI-2026-05-17-004`; closed Phase 7 (`RM-710`) and this ExecPlan.

## Surprises & Discoveries

- Observation: The prior project-level plan is closed and the ExecPlan register said there was no
  active plan.
  Evidence: `docs/exec_plans/README.md` pointed to no active project-level ExecPlan and listed the
  prior post-audit plan as completed.

- Observation: The new stabilization plan should not make UI the default next work.
  Evidence: The user explicitly corrected the planning draft so UI decision stays outside this plan
  and only returns after stabilization.

- Observation: Generated-output QA should happen after source-level schema and language cleanup.
  Evidence: The user explicitly corrected the ordering to avoid regenerating outputs twice.

- Observation: The remaining status drift was concentrated in top-level orientation text, not in
  the canonical artifact specs.
  Evidence: `SPEC.md`, `OUTPUTS.md`, `docs/ROADMAP.md`, and detailed specs already listed the factory,
  current-vs-policy, trade-off/model-risk, assumption sensitivity, Pareto, regret, and decision
  package outputs as implemented, while `README.md`, `ARCHITECTURE.md`, and `PRODUCT.md` still had
  stale or under-specific target/TBD wording.

- Observation: Risk-free/cash runtime behavior already matched the intended policy; the mismatch was
  documentation and missing focused regression coverage.
  Evidence: `src/config.py` `DEFAULT_CASH_AND_RF` resolves USD to `BIL` / `FRED:DTB3`, EUR to `PEU`
  / `ECB:€STR`, and raises `ConfigValidationError` for unsupported currencies without explicit
  `cash_proxy_ticker` and `risk_free_source`.

- Observation: The monthly cache stores FX-adjusted panels, so the key must depend on the resolved
  asset currency map, not only on run settings.
  Evidence: `src/data_loader.py` builds `currency_by_ticker` before calling
  `convert_prices_to_investor_currency`, and `src/cache.py` writes `prices_monthly.parquet` /
  `returns_monthly.parquet` after FX conversion.

- Observation: The cash fallback diagnostic was structurally unable to increment.
  Evidence: before Session 05, `src/portfolio_dynamic.py` initialized `used_fallback = False` inside
  the monthly loop but never set it to `True`; the focused regression with both risk assets missing
  would therefore return `n_months_cash_fallback == 0` before the fix.

- Observation: The time-to-recovery helper measured recovery from the final/global equity peak rather
  than from the peak immediately before the maximum drawdown trough.
  Evidence: before Session 06, the synthetic path `[0.0, -0.20, -0.125, 2 / 7, 1 / 9, 0.10]`
  returned `(None, False)` even though the -30% max drawdown recovered after four monthly
  observations.

- Observation: Full pytest has two tests that can hit a sandbox/permission boundary when creating
  `output/codex_test_artifacts/*` on this desktop workspace.
  Evidence: the Session 06 full run reported 449 passed and permission-only failures in
  `test_attach_kalman_factor_betas_preserves_raw_ols_fields` and
  `test_write_rolling_betas_plot_pngs_handles_nine_factors`; both passed when rerun outside the
  sandbox.

## Decision Log

- Decision: Treat this as a new active project-level plan, not as a reopening of the completed
  post-audit stabilization and analytics plan.
  Rationale: The previous plan is closed, and the repeat audit found a new MVP stabilization backlog.
  Date/Author: 2026-05-17 / Codex.

- Decision: Keep full UI/workspace outside this plan.
  Rationale: The user asked to leave UI as "after stabilization", and the current MVP risk is file-first
  reliability rather than UI surface design.
  Date/Author: 2026-05-17 / Codex.

- Decision: Run generated-output QA after schema/language drift cleanup.
  Rationale: Regenerating before source/schema fixes can require a second regeneration pass and makes
  output QA less meaningful.
  Date/Author: 2026-05-17 / Codex.

- Decision: Unless the user gives a different instruction, keep the current USD/EUR default behavior
  for risk-free and cash sources and document unsupported non-USD currencies as requiring explicit
  config.
  Rationale: This matches current code behavior and avoids changing portfolio semantics before the
  policy sync session has tests.
  Date/Author: 2026-05-17 / Codex.

- Decision: Treat Candidate Portfolio Factory, current-vs-policy, trade-off/model-risk, Assumption
  Sensitivity, Pareto / Dominance, Regret Analysis, and decision package summary as implemented
  file-first V1 artifacts, while keeping full UI/workspace flows and polished client-facing packaging
  as future scope.
  Rationale: This matches `SPEC.md`, `OUTPUTS.md`, detailed specs, and the completed Phase 6 roadmap
  items without expanding runtime behavior in this documentation-only session.
  Date/Author: 2026-05-17 / Codex.

- Decision: Fingerprint the resolved per-ticker currency map instead of raw `assets.yml` contents.
  Rationale: FX-adjusted panels change when the effective asset currency changes; unrelated metadata
  fields in `assets.yml` should not force unnecessary cache invalidation.
  Date/Author: 2026-05-17 / Codex.

- Decision: Count `n_months_cash_fallback` only when missing positive risk-sleeve weight remains
  after redistribution and positive `w_miss` is applied to available cash returns.
  Rationale: The diagnostic should report data fallback usage, not ordinary explicit or implicit cash
  exposure when all risk returns are observed.
  Date/Author: 2026-05-17 / Codex.

- Decision: Define time-to-recovery as the number of monthly or trading-day observations from the
  peak immediately before the maximum drawdown trough to the first post-trough observation where
  equity reaches or exceeds that peak.
  Rationale: This matches the canonical max-drawdown recovery interpretation and avoids false
  unrecovered readings when a portfolio makes a later high near the end of the window.
  Date/Author: 2026-05-17 / Codex.

- Decision: Treat windows with no drawdown as `ttr = 0` and `recovered = True`.
  Rationale: No recovery is required when equity never falls below its running peak; reporting such
  paths as unrecovered would penalize monotonic positive windows.
  Date/Author: 2026-05-17 / Codex.

## Outcomes & Retrospective

Session 01 outcome: project memory now has an active repeat-audit stabilization handoff. The audit
register points to the repeat MVP readiness audit, the ExecPlan register points to this active plan,
the roadmap has Phase 7 (`RM-700` through `RM-710`), active known issues capture the unresolved audit
risks, and documentation verification passed. At that point, the next chat was Session 02, using this
file as the single working plan.

Session 02 outcome: top-level docs now agree that the file-first V1 comparison and decision package
chain is implemented, including factory orchestration, current-vs-policy status, trade-off/model-risk,
Assumption Sensitivity, Pareto / Dominance, Regret Analysis, Action Plan, Monitoring, Decision
Journal, and decision package summary outputs. Future scope is now framed as UI/workspace UX,
polished report packaging, and user-maintained workflows rather than the underlying file-first
artifacts.

Session 03 outcome: risk-free and cash policy is now explicit and consistent. USD and EUR have
built-in defaults; unsupported investor currencies must configure both `cash_proxy_ticker` and
`risk_free_source`. Focused config/input tests and documentation verification passed.

Session 04 outcome: monthly return-panel caches now include an asset-currency metadata fingerprint.
Changing a ticker's resolved currency, including via `assets.yml`, produces a different monthly cache
key before FX-adjusted prices and returns are reused. Focused cache tests passed.

Session 05 outcome: NaN-safe return behavior is unchanged, but its data-policy audit trail is now
accurate. `data_policy.json.n_months_cash_fallback` counts months where missing positive risk-sleeve
weight cannot be redistributed to observed risk peers and is therefore applied to the cash proxy.
Focused NaN-safe tests and documentation verification passed. The live `run_report.py` smoke inside
`tests/test_backtest_nan_safe.py` was intentionally deselected for this session to avoid live data
dependency; Session 09 will add the offline end-to-end smoke test.

Session 06 outcome: TTR now matches the max-drawdown recovery definition for monthly portfolio/asset
metrics and the daily regime diagnostic analog. Recovered paths report the observation count from
the max-drawdown peak to the first post-trough recovery, unrecovered paths report `None`/`False`,
and no-drawdown windows preserve `0.0` instead of being converted to `NaN`. Focused and adjacent
metric/report tests passed. Full pytest passed functionally after rerunning two permission-only
artifact-output failures outside the sandbox. The active known issue `KI-2026-05-17-018` was removed.

Session 07 outcome: stress multicollinearity diagnostics now write `assessment_en` instead of the
misnamed `assessment_ru` field (content was already English). Commentary prefers `assessment_en` and
still reads legacy `assessment_ru` when present in older `stress_report.json` files. Focused
multicollinearity and commentary tests passed, and documentation verification passed. The active
known issue `KI-2026-05-17-019` was removed. Next step: Session 09 offline end-to-end smoke test.

Session 08 outcome: representative folders (`Main portfolio/`, `equal-weight portfolio/`,
`risk parity portfolio/`, `pdf_md_sources/`, `pdf files/`) were regenerated from cleaned generators
after Sessions 06-07. Stale Russian/mojibake commentary and `assessment_ru`-only stress blocks were
replaced on fresh runs. `run_compare_ew_rp.py` now emits English comparison text and uses ASCII ` - `
for missing metrics. Automated QA scan and regression test guard the representative text artifacts.
`KI-2026-05-17-007` was removed. Residual: `Main portfolio_decision_package.pdf` Pandoc/LaTeX build
still fails on some analysis-end dates (other representative PDFs rebuild successfully).

Session 10 outcome: the file-first MVP path is documented as four stages
(`input -> diagnosis -> comparison -> action`) in `docs/operational_runbook.md`. Operators can run
steps manually or use `run_mvp_workflow.py` (`policy-only`, `policy-current`, `full-decision`,
`diagnosis-only`) which chains existing CLIs only. Focused orchestration tests and documentation
verification passed. Next step: Session 11 MVP readiness pass and plan closure.

Session 11 outcome: MVP stabilization is closed. Full pytest (`462 passed`), documentation
verification, and generated-output QA scan passed. Partial utility UI status is documented in
top-level docs; `KI-2026-05-17-004` removed. Phase 7 (`RM-700`–`RM-710`) and this ExecPlan are
marked complete in project memory. Residual accepted issue: `KI-2026-05-18-001` (decision-package
PDF Pandoc edge case). Default next backlog: deferred UI/workspace work unless the user starts a
new plan.

## Context and Orientation

This repository is a Python portfolio decision-support and reporting system. It is currently
CLI/file-driven. The main production flow is `python run_optimization.py` followed by
`python run_report.py`, with comparison and decision artifacts written through the candidate
comparison pipeline. Generated outputs are not source of truth; source docs and specs define expected
behavior.

The key documents for this plan are:

- `docs/audits/2026-05-17_repeat_project_mvp_readiness_audit.md`, the audit evidence for this plan.
- `docs/ROADMAP.md`, the durable roadmap and phase register.
- `KNOWN_ISSUES.md`, the active issue register.
- `DATA.md`, `OUTPUTS.md`, `TESTING.md`, and the specs under `docs/specs/`, the owning documents for
  data, generated artifacts, verification, and detailed behavior.

Definitions used here:

- "File-first MVP" means the product experience is delivered through CLI commands and generated JSON,
  TXT, HTML, Markdown, and PDF-facing files, not through a full interactive workspace.
- "Generated outputs" means files under output folders such as `Main portfolio/`, `pdf_md_sources/`,
  and `pdf files/`. They can be regenerated and should not be hand-edited as source.
- "Schema drift" means two parts of the project disagree on a field name or meaning, for example
  `assessment_ru` versus `assessment_en`.

## Plan of Work

Session 01 creates project memory for this stabilization stage. It writes the repeat audit handoff,
creates this active ExecPlan, updates the audit and ExecPlan registers, adds a new roadmap phase, and
records the active known issues. It does not change runtime behavior.

Session 02 synchronizes source-of-truth status wording. Update `README.md`, `ARCHITECTURE.md`, and any
adjacent root docs that still describe implemented file-first artifacts as target/TBD. Keep full
UI/workspace marked as future scope.

Session 03 resolved risk-free and cash policy wording. It preserved the current practical behavior:
USD and EUR have defaults; unsupported non-USD currencies require explicit cash and risk-free
configuration. The session synced `DATA.md`, input assumptions spec, metrics spec, and focused tests.

Session 04 hardens monthly data cache invalidation. Add an asset metadata fingerprint to the monthly
cache key so changes in asset currency metadata invalidate FX-adjusted cached panels. Add focused
tests and update data docs.

Session 05 fixes NaN-safe cash fallback diagnostics. The backtest behavior should continue to move
missing risk-asset residual weight to cash, but `n_months_cash_fallback` must count the months where
that fallback actually happened.

Session 06 hardened time-to-recovery metrics. The implementation now measures recovery from the
peak before the maximum drawdown trough, adds regression tests for recovered and unrecovered paths,
and documents that no-drawdown windows are recovered with `ttr = 0`.

Session 07 fixes source-level schema and language drift. Make `assessment_en` the primary stress
assessment field and keep `assessment_ru` only as legacy-read compatibility. Clean source/generator
names or text that can leak confusing language into reports.

Session 08 performs generated-output QA after source/schema fixes. Regenerate representative outputs
from the cleaned source and inspect them for mojibake, broken symbols, and non-English default text.
Do not hand-edit generated files.

Session 09 adds a synthetic offline end-to-end test. The test should prove the MVP flow can produce
key decision-package JSON artifacts without live network data.

Session 10 clarifies user flow. Update operational docs and, if still needed, add a thin CLI
orchestration wrapper that calls existing steps without adding formulas or changing optimizer logic.

Session 11 closes the stabilization stage. Run docs checks, focused or full pytest with a
workspace-local `--basetemp`, representative CLI smoke checks, and update roadmap/issues/changelog.

## Concrete Steps

Run commands from the repository root:

    C:\Users\ShumeikoYe\OneDrive\Desktop\CURSOR TULA DIAGNOSTICS

For Session 01, run:

    python scripts\verify_docs.py

If `python` is unavailable in PATH, use the project virtual environment:

    .\.venv\Scripts\python.exe scripts\verify_docs.py

For later code sessions, use workspace-local pytest temp directories to avoid shared-cache cleanup
permission errors:

    .\.venv\Scripts\python.exe -m pytest <focused tests> -q --basetemp='tmp\pytest_mvp_session_<NN>'

For Session 05, run:

    .\.venv\Scripts\python.exe -m pytest tests\test_backtest_nan_safe.py -k 'not test_run_report_default_mode_uses_dynamic_engine' -q --basetemp='tmp\pytest_mvp_session_05_cash'
    .\.venv\Scripts\python.exe scripts\verify_docs.py

For Session 06, run:

    .\.venv\Scripts\python.exe -m pytest tests\test_metrics_drawdown.py -q --basetemp='tmp\pytest_mvp_session_06_ttr'
    .\.venv\Scripts\python.exe -m pytest tests\test_metrics_drawdown.py tests\test_regime_portfolio_metrics.py tests\test_returns_frequency.py tests\test_portfolio_commentary.py tests\test_candidate_comparison.py -q --basetemp='tmp\pytest_mvp_session_06_adjacent'
    .\.venv\Scripts\python.exe scripts\verify_docs.py

Each numbered session should update this file before stopping. Do not start the next numbered session
in the same chat unless the user explicitly overrides the session boundary rule.

## Validation and Acceptance

Session 01 is accepted when:

- `docs/audits/2026-05-17_repeat_project_mvp_readiness_audit.md` exists.
- This ExecPlan exists and is marked active in `docs/exec_plans/README.md`.
- `docs/audits/README.md` marks the repeat audit as the active input.
- `docs/ROADMAP.md` has a stabilization phase that points to this plan and keeps UI outside this
  active work.
- `KNOWN_ISSUES.md` has active issues for the unresolved audit findings.
- `CHANGELOG.md` records the planning/project-memory update.
- `scripts/verify_docs.py` passes.

Session 05 is accepted when:

- `portfolio_returns_nan_safe(..., return_diagnostics=True)` reports one cash fallback month when all
  positive risk-sleeve assets are missing and the residual earns the cash proxy return.
- A month where one missing risk asset is fully redistributed to other observed risk peers increments
  `n_months_redistributed` but not `n_months_cash_fallback`.
- Planned cash exposure without missing risk returns does not increment `n_months_cash_fallback`.
- The focused NaN-safe pytest command and documentation verification pass.

Session 06 is accepted when:

- `time_to_recovery(...)` reports recovery for a max-drawdown path even when a later all-time high
  occurs near the end of the window.
- `time_to_recovery(...)` reports `None, False` when the max-drawdown path does not recover.
- Portfolio metrics preserve no-drawdown recovery as `ttr_months = 0.0` and `recovered = True`.
- The daily diagnostic analog follows the same max-drawdown peak/trough path using trading-day
  index positions.
- Focused and adjacent metric tests plus documentation verification pass.

The full plan is accepted when Session 11 closes with no open high-severity MVP issues except items
explicitly accepted or deferred in `KNOWN_ISSUES.md`.

## Idempotence and Recovery

Documentation edits in this plan are safe to repeat if links and registers remain consistent. Do not
delete or rewrite generated output folders unless the session explicitly targets generated-output QA.
Do not revert unrelated dirty files. If a verification command fails because of temp directory
permissions, rerun with `--basetemp` under `tmp/` inside the workspace.

## Artifacts and Notes

The repeat audit found these stabilization risks; completed sessions above mark which ones are now
resolved:

- Source-of-truth status drift in top-level docs.
- Generated-output language and encoding quality risk.
- Monthly cache key missing asset metadata fingerprint, resolved in Session 04.
- Risk-free/cash policy wording conflict, resolved in Session 03.
- NaN-safe cash fallback diagnostic counter underreporting fallback months, resolved in Session 05.
- Time-to-recovery semantics needing regression coverage, resolved in Session 06.
- Stress assessment language/schema naming drift, resolved in Session 07.
- Missing offline MVP end-to-end smoke test, resolved in Session 09.

## Interfaces and Dependencies

Expected public interface changes during this plan:

- Monthly cache keys include an asset metadata fingerprint.
- `data_policy.json.n_months_cash_fallback` keeps the same name but reports correct fallback counts.
- `ttr_months` remains the monthly recovery metric name, but now uses the max-drawdown peak/trough
  path and preserves no-drawdown windows as `0.0` / recovered.
- Stress diagnostics use `assessment_en` as the primary field, with `assessment_ru` only for legacy
  compatibility where needed.
- Risk-free/cash policy is documented and tested as USD/EUR defaults plus explicit config for other
  non-USD investor currencies.
- Any new CLI wrapper must be a thin orchestration command only; it must call existing commands or
  helpers and must not introduce new formulas or optimizer behavior.

Revision note, 2026-05-17: Initial active plan created from the user's accepted Post-Audit MVP
Stabilization Roadmap and repeat audit findings.

Revision note, 2026-05-17: Session 02 completed the source-of-truth status sync and updated this
living plan with the observed stale-doc pattern and file-first-vs-UI boundary decision.

Revision note, 2026-05-17: Session 03 completed the risk-free/cash policy sync, added focused
regressions for EUR defaults and unsupported-currency explicit configuration, and recorded passing
verification.

Revision note, 2026-05-17: Session 04 completed the cache and FX metadata correctness work, added
focused cache-key regressions, and recorded passing focused verification.

Revision note, 2026-05-17: Session 05 completed the NaN-safe cash fallback diagnostic fix, added
focused fallback-count regressions, updated data policy docs and project memory, and recorded passing
focused verification.

Revision note, 2026-05-17: Session 06 completed time-to-recovery formula hardening, added focused
monthly/daily drawdown regressions, updated the metrics spec and testing guidance, and recorded
passing focused and adjacent verification.

Revision note, 2026-05-17: Session 07 completed stress assessment schema cleanup (`assessment_en`
primary, legacy `assessment_ru` read-only in commentary), updated the stress spec and tests, and
recorded passing focused verification.

Revision note, 2026-05-18: Session 08 regenerated representative outputs, added generated-output
QA scan/test, fixed EW/RP comparison English labels, and added FRED CSV fallback in `data_fred.py`.

Revision note, 2026-05-18: Session 09 added the offline MVP pipeline smoke test
(`tests/test_mvp_pipeline_offline.py`), shared fixtures, `TESTING.md` guidance, and closed known issue
`KI-2026-05-17-020`.

Revision note, 2026-05-18: Session 10 added MVP user-flow documentation and
`run_mvp_workflow.py` orchestration (`src/mvp_workflow.py`, `tests/test_mvp_workflow.py`);
closed roadmap item RM-709.

Revision note, 2026-05-18: Session 11 closed MVP stabilization (RM-710): full verification,
partial utility UI doc sync, plan/register/roadmap closure. No active project-level ExecPlan.
