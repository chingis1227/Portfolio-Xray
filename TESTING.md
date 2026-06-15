# TESTING.md

This file is the quality and verification framework for Portfolio MRI / Optimization Terminal.

It defines what to verify for different change types, which risks the checks cover, when focused `pytest` is enough, when CLI smoke runs are needed, and when generated artifacts or Markdown links must be inspected. It does not define formulas, scenarios, optimizer policy, or data rules; those remain in `SPEC.md`, `DATA.md`, and `docs/specs/`.

Update this file when test strategy, required checks, verification commands, regression coverage, or quality gates change.

## Core Rule

Verify the changed risk, not just the changed file.

Use the narrowest reliable check first. Broaden only when the change touches shared math, data alignment, optimizer behavior, config/schema, stress logic, report exports, or generated artifact contracts.

## Verification Levels

| Level | Use when | Commands or checks |
| --- | --- | --- |
| Focused unit/regression test | One module or behavior changed | `python -m pytest tests/test_name.py -q` |
| Adjacent focused suite | Change touches shared helpers or nearby behavior | Run multiple related `tests/test_*.py` files together |
| Full pytest | Shared math, optimizer, data, stress, config, or report contracts may regress | `python -m pytest` |
| CLI smoke run | Entrypoint behavior, generated outputs, or end-to-end flow changed | `python run_portfolio_review.py`, `python run_report.py`, legacy `python run_optimization.py`, or the affected `run_*.py` |
| Artifact inspection | JSON/CSV/HTML/TXT/PDF-style output shape or content changed | Inspect relevant files under `Main portfolio/`, `results_csv/`, variant folders, or `pdf files/` |
| Documentation verification | Docs, links, commands, renamed files, or source-of-truth maps changed | `python scripts/verify_docs.py` or `python -m pytest tests/test_docs_links.py -q`; add `rg` stale-reference searches when renaming removed fields |
| Generated-output language QA | Representative report/PDF text artifacts regenerated or language/story rules touched | `python scripts/scan_generated_outputs.py` and `python -m pytest tests/test_generated_output_language.py -q`; portfolio-first summaries must keep `Starting portfolio` and `Candidate alternatives` markers |
| Offline MVP pipeline smoke | File-first decision chain (comparison through decision package) or cross-module orchestration regressions | `python -m pytest tests/test_mvp_pipeline_offline.py -q` |
| Portfolio-first offline E2E smoke | Portfolio-first subject diagnostics, comparison, and decision package regressions across subject types | `python -m pytest tests/test_portfolio_first_e2e_offline.py -q` |
| Blocks 1-5 five-ticker MVP smoke | First-five-block contract from explicit weighted subject input through diagnostics, Diagnosis, stress, current factory evidence, and comparison baseline | `python -m pytest tests/test_blocks_1_5_mvp_smoke.py -q` |
| Blocks 1-5 live core E2E (networked) | Operator or CI proof that `run_portfolio_review.py --with-candidates` materializes subject + `core_fast` factory + comparison with `candidate_menu.review_mode == core` | Run orchestrator, then `python scripts/verify_live_core_e2e.py` or `python -m pytest tests/test_blocks_1_5_live_core_e2e.py --live-core -q` |
| Blocks 1-5 live full + resume E2E (networked) | Operator proof that `--mode full` (and optional `--resume-candidates`) completes `default_v1` factory + comparison | `python scripts/verify_live_full_e2e.py --run` or `--run --resume-candidates`; then `pytest tests/test_blocks_1_5_live_full_e2e.py --live-full -q` |
| Staged diagnosis performance smoke (network/cache sensitive) | Run Diagnostics perceived/runtime performance, shared context, or cache behavior changes | `python scripts/diagnosis_performance_smoke.py --payload runs\<frontend_review_id>\payload.json --warm-threshold-seconds 30`; pass requires warm runtime at or below threshold, while external provider/cache outages must be reported as blockers rather than silent passes |
| Bounded parallel data loading | yfinance ticker loading, factor proxy loading, macro indicator loading, worker-limit environment variables, or rollback behavior changes | `python -m pytest tests/test_parallel_data_loading.py tests/test_runtime_memory_caches.py tests/test_factor_matrix_builders.py tests/test_macro_source_resolver.py -q`; pass requires deterministic output order, sequential behavior under `PMRI_DISABLE_PARALLEL_DATA_LOAD=1`, preserved item-level error semantics, and unchanged macro source-chain precedence |
| FRED factor cache smoke (networked) | Before live demos or after changing full factor-matrix FRED/cache behavior | Set API key in the shell, not config: `$env:FRED_API_KEY="your_key_here"`. Check readiness without network: `python scripts/warm_factor_cache.py --check-only --start 2007-01-01 --end YYYY-MM-DD`. If cache is missing/partial/expired, refresh API-first: `python scripts/warm_factor_cache.py --start 2007-01-01 --end YYYY-MM-DD`, then repeat `--check-only`. Focused regression: `python -m pytest tests/test_factor_matrix_builders.py tests/test_data_cache_key.py tests/test_factor_diagnostics_wiring.py tests/test_product_bundle_integration.py -q`. Pass requires `cache_status=valid`, empty `missing_series`, `full_factor_matrix_available=true`, and `demo_safe=true` on check-only. |
| Blocks 6-7 downstream integration (offline) | Guarded backtest/stress handoff from `candidate_comparison.json` (degraded optimizer stress embed-only) | `python -m pytest tests/test_blocks_6_7_downstream_integration.py tests/test_downstream_decision_readiness.py -q` |
| Blocks 8-10 package truthfulness (offline) | Partial menu + degraded optimizer disclosure in selection/action/decision package | `python -m pytest tests/test_blocks_8_10_downstream_integration.py tests/test_package_truthfulness.py tests/test_decision_package_reporting.py -q` |
| Blocks 1-5 data trust signals | Stress/input/Diagnosis trust summaries for episode quality, taxonomy warnings, and young-ETF policy disclosure | `python -m pytest tests/test_data_trust_signals.py -q` |
| Core diagnostics entrypoint (Blocks 1-3) | `run_core_diagnostics.py`, `--core-diagnostics-only`, or `product_bundle_scope` | `python -m pytest tests/test_core_diagnostics_entrypoint.py -q` |
| Local utility UI security | `config_ui/` or `results_dashboard/` local-only behavior, CSRF protection, command-trigger endpoints, or generated-output path resolution | `python -m pytest tests/test_config_ui_input_modes.py tests/test_config_ui_mvp_first_screen.py tests/test_config_ui_rc_cap_removed.py tests/test_config_ui_security.py tests/test_results_dashboard_security.py -q` |
| FastAPI foundation contracts | Local FastAPI app, health endpoint, diagnosis/recovery/Builder/Candidate/runtime adapters, Pydantic API models, OpenAPI surface, generated frontend API types, FastAPI screen-mapping governance, sourced-claim/advice-language governance, frontend display-model adapters, signed Next.js-to-FastAPI compatibility proxy routes, or active-review lineage/isolation behavior | `python -m pytest tests/test_fastapi_app.py tests/test_fastapi_contract_governance.py -q`; after schema/type/screen-map changes also run `python scripts/verify_fastapi_contract_governance.py` and `cd frontend && npm.cmd run typecheck`; when Next.js proxy routes are touched also run `cd frontend && npm.cmd run test:api`; when legacy/debug script helpers or run-local review isolation are touched also run `python -m pytest tests/test_frontend_review_bridge.py -q` |
| Live FastAPI + frontend vertical QA | Explicit operator proof that fresh FastAPI, fresh Next.js, clean Playwright browser state, frontend compatibility routes, run-local lineage, and stale-card rejection work together across multiple portfolio scenarios | `cd frontend && npm.cmd run qa:vertical -- --scenario-limit 3`; inspect `output/playwright/**/qa-report.json`, screenshots, DOM fallbacks, `next.log`, and `fastapi.log`. This is a live/network-sensitive acceptance check, not a default fast gate. |
| Portfolio-first workflow orchestration | `run_portfolio_review.py` plan building or step ordering | `python -m pytest tests/test_portfolio_review_workflow.py -q` |
| One-candidate product demo | After `scripts/run_blocks_5_to_9_vertical_flow.py --method equal_weight` or runtime-truth scoping changes | `python -m pytest tests/test_one_candidate_demo_validation.py -q`; live disk gate: `python scripts/validate_one_candidate_demo.py` |
| Runtime truth product vs research boundaries (Session 08) | Runtime mode routing, `advanced_package` gating, or compare/verdict scoping changes | `python -m pytest tests/test_runtime_mode_regression_boundaries.py tests/test_portfolio_review_workflow.py tests/test_candidate_comparison.py tests/test_one_candidate_demo_validation.py -q` |
| Architecture consistency guards (Session 06) | Default diagnosis-only CLI, dry-run stage contracts, `site_api` TXT boundary, runbook batch-default doc drift | `python -m pytest tests/test_architecture_consistency.py tests/test_runtime_mode_regression_boundaries.py tests/test_docs_links.py -q`; `python scripts/verify_docs.py` |
| MVP workflow orchestration | `run_mvp_workflow.py` plan building or step ordering | `python -m pytest tests/test_mvp_workflow.py -q` |

`pytest.ini` limits test discovery to `tests/`, so `python -m pytest` is the repository-level test command.

## Fast QA gates

Use these PowerShell shortcuts for routine local verification when a full test suite would be too slow for the active task:

| Gate | Command | Use when | Excludes |
| --- | --- | --- | --- |
| Fast daily QA | `.\scripts\qa_fast.ps1` (`.\scripts\qa_fast.cmd` if PowerShell policy blocks scripts) | Default local gate for docs consistency, staged Run Diagnosis route compatibility, core offline workflow smoke, product-bundle adapters, frontend typecheck, and frontend API routes. Target runtime is roughly 3 minutes on the Windows desktop setup. | Full `python -m pytest`, live E2E, frontend build, frontend smoke, Playwright/browser visual QA. |
| Contract QA | `.\scripts\qa_contracts.ps1` (`.\scripts\qa_contracts.cmd` if PowerShell policy blocks scripts) | Runtime contract, candidate factory, comparison JSON, or golden fixture changes. It runs the candidate factory/comparison suites while excluding the still-open KI-2026-05-26-001 drift test. | Networked/live checks and full `python -m pytest`. |
| Exhaustive local QA | `.\scripts\qa_exhaustive.cmd -LocalOnly -SkipLive` | Release-candidate local static gate. It writes `output/qa_runs/<timestamp>/qa-summary.*`, per-step logs, `qa-findings.*`, and `qa-release-readiness.*`; runs environment readiness, the staged Run Diagnosis OpenAPI guard, fast QA, contract QA, FastAPI governance, full pytest, frontend typecheck/build/API/smoke, docs verification, and Supabase compact/privacy checks. | Browser vertical QA and staging readiness are skipped by `-SkipLive` / `-LocalOnly`; use the release commands below before declaring release readiness. Known baseline failures are classified as `known_failure`; unexpected failures are `new_failure`. |
| Exhaustive local + browser vertical QA | `.\scripts\qa_exhaustive.cmd -LocalOnly` | Local release-readiness gate that adds `npm.cmd run qa:vertical -- --scenario-limit 5` after the local static gate. It records active `reviewId` lineage, selected Launchpad card, Builder/Candidate/Comparison/Verdict/Report ids, screenshots or DOM fallbacks, and stale selected-card HTTP 409 evidence in `qa-findings.*`. | Staging readiness is skipped because `-LocalOnly` is supplied. |
| Exhaustive staging release readiness | `.\scripts\qa_exhaustive.cmd -Staging` with `PMRI_QA_ALLOW_STAGING=1`, `PMRI_QA_FRONTEND_URL`, and `PMRI_QA_FASTAPI_URL` | Full release-readiness gate. It runs the local checks, local browser vertical QA, staging Run Diagnosis compatibility, and staging route-chain journey checks through Report. | Requires configured staging URLs and may create a normal demo QA staged review in staging. External provider outages may be classified as `blocked_external`. |

Keep full `python -m pytest` as a manual/nightly or risk-based check, not the everyday fast gate. Run live core/full E2E only for demo, release, or explicit operator proof.

Current exhaustive baseline note: the 2026-06-14 Session 02 run completed as
`passed_with_known_failures`. `KNOWN_ISSUES.md` tracks the current full-pytest count and
`KI-2026-06-14-001`, where `npm.cmd run build` can return exit `-1` inside the long exhaustive
runner even though the same build passes standalone. Session 03 upgrades the same runner to
`qa_exhaustive_session03_v1` and adds `qa-release-readiness.*`; known P0/P1/P2 failures remain
release blockers in the readiness summary even when they are classified as known baselines.
The previous browser vertical blocker `KI-2026-06-14-002` is resolved: downstream frontend bridge
routes must stay deployment-safe by consuming FastAPI response payloads plus explicit lineage ids
from frontend state, not by reading run-local files from Next.js route handlers. Demo QA mode uses
fixed fixture diagnosis text across scenarios, so the vertical helper records that as a warning
rather than a route-chain failure; release evidence is the same-run lineage and stale-card 409 proof.

### Known full-suite status

As of the latest recorded full-suite audit on **2026-06-14**, `python -m pytest` reported
**34 failed, 1887 passed, 3 skipped**. Treat this as the current full-suite status until a newer
full run is recorded. The previous structured grouping came from
[docs/audits/2026-06-12_full_pytest_failure_audit_after_client_fit.md](docs/audits/2026-06-12_full_pytest_failure_audit_after_client_fit.md);
the current count and active drift index are summarized in [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

Until the remaining rows are closed: use focused pytest for the changed layer and the fast QA gates
above; do not claim full-suite green or make it a release gate without rerunning and reconciling the
full suite.

### Block 2.4 Hidden Exposure institutional upgrade (Sessions 01-13, **closed**)

After Block 2.4 contract, scoring, enrichment, or golden changes:

```bash
python -m pytest tests/test_block_2_4_hidden_exposure.py tests/test_block_2_4_matrix_coverage.py tests/test_portfolio_xray_contract.py -q
```

Regenerate golden when `portfolio_xray.json` contract changes intentionally:

```bash
python tests/portfolio_xray_golden_inputs.py
python -m pytest tests/test_portfolio_xray_contract.py -q
```

Session 10 closure (2026-05-29): **129 passed** in the bundle above; matrix coverage in
`tests/test_block_2_4_matrix_coverage.py` maps implementable implemented v2 rows from the Session 00
completion matrix. Evidence: [Session 10 audit](docs/audits/2026-05-29_block_2_4_session_10_tests_golden.md).

After Session 11 Core MVP contract wiring, also run:

```bash
python -m pytest tests/test_core_mvp_block2_4_contract.py tests/test_core_mvp_blocks_1_3_boundaries.py -q
python scripts/validate_core_mvp_block2_fixture_matrix.py
```

Session 11 closure (2026-05-29): shared Block 2.4 v2 validator in
`scripts/core_mvp_validation_contract.py`; fixture-matrix Block 2 script reports
`special_checks.contract_violations`. Evidence:
[Session 11 audit](docs/audits/2026-05-29_block_2_4_session_11_core_mvp_validation.md).

After Session 12 live demo, validate materialized subject Block 2.4:

```bash
python run_portfolio_review.py --skip-candidates
python scripts/validate_block_2_4_live.py --refresh-xray
```

If `portfolio_xray.json` predates the institutional upgrade, `--refresh-xray` rebuilds it
from existing `snapshot_10y.json` / `stress_report.json` / `run_metadata.json` via
`build_portfolio_xray_v2` (same builder as materialization). Evidence:
[Session 12 audit](docs/audits/2026-05-29_block_2_4_session_12_live_demo_regression.md).

Session 13 closure (2026-05-29): institutional upgrade **complete** - matrix v2 sign-off
([completion matrix](docs/audits/2026-05-29_block_2_4_completion_matrix_v2_signoff.md)),
ExecPlan [2026-05-29_block_2_4_institutional_upgrade_plan.md](docs/exec_plans/2026-05-29_block_2_4_institutional_upgrade_plan.md)
(**Completed**). Canonical closure bundle:

```bash
python -m pytest tests/test_core_mvp_block2_4_contract.py tests/test_block_2_4_hidden_exposure.py tests/test_block_2_4_matrix_coverage.py tests/test_portfolio_xray_contract.py tests/test_core_mvp_blocks_1_3_boundaries.py -q
python scripts/validate_block_2_4_live.py --refresh-xray
```

Evidence: [Session 13 audit](docs/audits/2026-05-29_block_2_4_session_13_institutional_closure.md).

## Block 4 v3 Diagnosis-First Contract

Primary contract: [block_4_diagnosis_v3_spec.md](docs/specs/block_4_diagnosis_v3_spec.md). Block 4 should be tested as investment diagnosis, not as a scoring dashboard.

Session 02 next-step regression focus:

- `problem_classification_v3.next_diagnostic_step` is always present and keeps the rebalance decision boundary explicit.
- Mixed/acceptable outcomes expose Equal Weight / Risk Parity only as `reference_benchmark_test` Launchpad cards.
- Data-quality blockers do not emit unreliable Equal Weight / Risk Parity reference comparisons.
- Actionable diagnoses keep the targeted hypothesis card before any reference benchmark tests.
- Launchpad-to-Builder handoff preserves diagnosis, success criteria, tradeoff, skip rule, decision boundary, and `is_rebalance_recommendation: false`.
- Builder prefill never generates candidates automatically; data-quality and monitor cards keep `candidate_generation_allowed: false`.

Regression bundle:

```bash
python -m pytest tests/test_block_4_diagnosis_builder.py \
  tests/test_block_4_no_trade_gate.py \
  tests/test_block_4_launchpad_cards.py \
  tests/test_block_4_action_path_mapping.py \
  tests/test_block_4_problem_prioritization.py \
  tests/test_block_4_severity_confidence.py \
  tests/test_block_4_problem_scoring.py \
  tests/test_block_4_evidence_extraction.py \
  tests/test_block_4_problem_taxonomy.py \
  tests/test_block_4_v2_contract.py \
  tests/test_block_4_v2_archetype_fixtures.py \
  tests/test_block_4_v2_live_validation.py \
  tests/test_block_4_decision_entry_contract.py \
  tests/test_diagnostic_journey_view_model.py -q
```

Dynamic interpretation-chain matrix (Diagnosis Interpretation Foundation Session 11):

```bash
python -m pytest tests/test_diagnosis_interpretation_fixture_matrix.py tests/test_block_4_v2_archetype_fixtures.py -q
```

This matrix uses ten deterministic portfolio archetypes and checks that different source evidence
produces different primary diagnoses, root-cause narratives, leading evidence signals, and FastAPI
diagnosis summaries without refreshing generated review artifacts.

Live product validation (Session 12+):

```bash
python scripts/validate_block_4_live.py --refresh-diagnosis
```

Launchpad-to-Builder handoff checks:

```bash
python -m pytest tests/test_portfolio_alternatives_builder.py tests/test_candidate_launchpad_builder_handoff.py -q
```

Diagnostic journey bridge: `tests/test_diagnostic_journey_view_model.py` asserts v3
`primary_diagnosis`, no-trade outcome, and Launchpad card mapping in `diagnostic_journey/view_model.py`.

Evidence: [Session 12 live validation](docs/audits/2026-05-29_block_4_v2_session_12_live_product_validation.md),
[Session 13 documentation sync](docs/audits/2026-05-29_block_4_v2_session_13_documentation_sync.md),
[Session 14 institutional closure](docs/audits/2026-05-29_block_4_v2_session_14_institutional_closure.md).

## Post-Architecture Alignment Checks

Use this matrix for diagnosis-first / decision-support architecture work after the 2026-05-25
alignment audit. The goal is to choose the narrowest reliable check for the changed layer without
refreshing generated outputs unless the session explicitly targets generated artifacts.

### Change-type verification

| Change type | Use when | Minimum checks | Do not do by default |
| --- | --- | --- | --- |
| Docs-only wording / source-of-truth cleanup | Editing product, architecture, output, workflow, or spec wording without changing executable examples or schemas | Targeted `rg` searches for the old/conflicting terms; optional `python -m pytest tests/test_docs_links.py -q` when links changed | Do not run portfolio refresh commands or rewrite generated outputs |
| AI Commentary contract wording | Locking grounding-only vs generated AI prose in active docs | `rg -n -i "generates... AI Commentary|implemented AI Commentary|LLM" README.md PRODUCT.md ARCHITECTURE.md SPEC.md OUTPUTS.md docs/DIAGNOSTIC_PRODUCT_CONCEPT.md docs/specs/ai_commentary_grounding_spec.md docs/specs/reporting_outputs_spec.md GLOSSARY.md`; confirm hits are negated, refer to grounding context, or point to `RM-ARCH-010` backlog | Do not treat `commentary.txt` presence as proof of LLM AI Commentary |
| Command matrix / CLI documentation | Editing documented commands, profiles, or examples | Targeted `rg` over owning docs; add the focused CLI/workflow tests only if behavior claims changed: `tests/test_portfolio_review_workflow.py`, `tests/test_candidate_factory_contract.py` | Do not change CLI defaults or schemas in a docs-only session |
| Output-contract wording | Reclassifying outputs or editing generated-vs-source policy without changing JSON fields | Targeted `rg` over `OUTPUTS.md`, `docs/specs/README.md`, and owning specs; add owning contract tests only if schema text changed | Do not regenerate `Main portfolio/` or candidate folders unless the session is a generated-output refresh |
| Product adapter code | Changing a diagnosis-first adapter module or its JSON shape | Run the focused adapter tests listed below, plus adjacent comparison/manifest tests when the adapter reads those artifacts | Do not rename existing lower-level contracts unless a separate migration plan exists |
| Runtime orchestration | Changing `run_portfolio_review.py`, `src/portfolio_review_workflow.py`, candidate factory invocation, or compare sequencing | `python -m pytest tests/test_portfolio_review_workflow.py tests/test_candidate_factory_contract.py tests/test_candidate_comparison_contract.py -q`; add offline E2E smoke when subject/comparison flow can regress | Do not run live networked E2E unless explicitly needed and approved |
| Generated-output refresh | Session explicitly approves refreshing generated files | Run the approved narrow CLI command, then inspect `output_manifest.json`, product-bundle JSON presence, and `candidate_menu` scope; classify generated diffs separately | Do not mix generated-output diffs with docs/code migration commits |

### Diagnosis-first adapter test map

| Layer / artifact | Owning tests | Add adjacent tests when |
| --- | --- | --- |
| Problem Classification / `problem_classification.json` | `python -m pytest tests/test_problem_classification.py -q` | Add `tests/test_portfolio_xray.py` or stress tests if evidence extraction from Diagnosis/stress changes |
| Candidate Launchpad / `candidate_launchpad.json` | `python -m pytest tests/test_candidate_launchpad.py -q` | Add Problem Classification tests if problem-to-card mapping inputs change |
| Portfolio Alternatives Builder / Launchpad prefill and one-candidate delegation plan | `python -m pytest tests/test_portfolio_alternatives_builder.py tests/test_candidate_launchpad_builder_handoff.py -q` | Add candidate factory contract tests if delegated command/profile/candidate IDs change |
| Candidate Generation / `candidate_generation.json` | `python -m pytest tests/test_candidate_generation_from_builder_setup.py tests/test_candidate_generation_method_mapping.py tests/test_candidate_generation_no_recommendation_boundary.py -q` | Add Portfolio Alternatives Builder tests if `CandidateSetup` fields or method mapping change |
| Current vs Candidate / `current_vs_candidate.json` | `python -m pytest tests/test_current_vs_candidate.py tests/test_block8_current_vs_candidate_boundary.py tests/test_no_stale_candidate_generation.py -q` | Add `tests/test_candidate_comparison.py tests/test_candidate_comparison_contract.py` if comparison row semantics change |
| Decision Verdict / `decision_verdict.json` | `python -m pytest tests/test_decision_verdict.py -q` | Add `tests/test_selection_engine.py` and action tests if Selection/No-Trade or action-plan evidence changes |
| AI Commentary grounding / `ai_commentary_context.json` | `python -m pytest tests/test_ai_commentary_context.py tests/test_no_stale_verdict_in_ai_context.py -q` | Add Decision Verdict and Current-vs-Candidate tests if grounding inputs change |
| Light Monitoring / `what_changed_summary.json` | `python -m pytest tests/test_light_monitoring_summary.py -q` | Add monitoring tests if `monitoring_diff.json` snapshots/diff logic changes |
| Product bundle integration after compare | `python -m pytest tests/test_product_bundle_paths.py tests/test_product_bundle_integration.py tests/test_runtime_entrypoint_labels.py tests/test_product_bundle_hygiene.py -q` | Extend when manifest keys, sidecar paths, hygiene, compare ordering, or bundle schemas change; add adapter unit tests below when artifact payloads change |
| Product bundle adapter unit tests | `python -m pytest tests/test_problem_classification.py tests/test_candidate_launchpad.py tests/test_portfolio_alternatives_builder.py tests/test_current_vs_candidate.py tests/test_decision_verdict.py tests/test_ai_commentary_context.py tests/test_light_monitoring_summary.py -q` | Add offline portfolio-first E2E if runtime flow or generated artifact ordering changes |

### Output-bundle acceptance checks

For a generated-output refresh session only, inspect the refreshed `output_dir_final` and confirm:

- product-facing bundle: `client_fit_check.json`, `problem_classification.json`,
  `candidate_launchpad.json`, `portfolio_alternatives_builder.json`, `candidate_generation.json`
  when explicitly generated, `current_vs_candidate.json`, `decision_verdict.json`,
  `ai_commentary_context.json`, and `what_changed_summary.json`;
- technical contracts: `candidate_comparison.json`, `selection_decision.json`,
  `candidate_factory_run.json` when candidates ran, and `output_manifest.json`;
- product surfaces do not present `portfolio_health_score.json`, `robustness_scorecard.json`,
  `assumption_sensitivity.json`, `pareto_dominance.json`, or `regret_analysis.json` as the main
  answer unless a later approved spec changes that boundary.

If any artifact is absent, report whether it is expected for the workflow state
(`diagnosis_only`, `one_candidate`, `multiple_candidates`) or whether it requires code/spec
verification. Do not infer success from stale generated files.

## Offline MVP Pipeline Smoke

Use this when touching `write_candidate_comparison_outputs`, selection/action/monitoring/journal writers, or any step in the file-first decision chain that feeds `decision_package_summary.json`.

The smoke test is fully offline:

- seeds synthetic `snapshot_10y.json` inputs for policy and legacy comparison variants;
- validates config input (in-memory and YAML);
- runs `write_candidate_comparison_outputs` through comparison, health/robustness, selection, action, monitoring, journal, and decision-package writers;
- blocks `src.data_yf.download_all` and `src.data_fred.fetch_fred_series` so live network access fails the test.

Command (prefer a workspace-local basetemp on Windows desktops):

```bash
python -m pytest tests/test_mvp_pipeline_offline.py -q --basetemp='tmp/pytest_mvp_offline'
```

Fixtures live in `tests/mvp_offline_fixtures.py`. This does not replace CLI smoke runs of
`run_portfolio_review.py`, `run_report.py`, or legacy `run_optimization.py` when data download,
stress, or full report exports change.

## Portfolio-First Offline E2E Smoke

Use this when touching `analysis_subject` resolution/materialization, `run_portfolio_review.py`
ordering, subject-centered candidate comparison, Selection/No-Trade, Action, Monitoring, Journal, or
decision-package reporting.

The smoke test is fully offline:

- seeds synthetic `{output_dir_final}/analysis_subject/` snapshots and metadata for
  `current_portfolio`, `model_portfolio`, and `universe_baseline`;
- seeds synthetic candidate snapshots for allowed non-policy alternatives;
- validates the `run_portfolio_review.py` plan materializes subject diagnostics before candidates and
  does not include `run_optimization.py`;
- runs `write_candidate_comparison_outputs` through comparison, scorecards, Selection, Action,
  Monitoring, Journal, and decision-package writers;
- blocks `src.data_yf.download_all` and `src.data_fred.fetch_fred_series` so live network access
  fails the test.

Command:

```bash
python -m pytest tests/test_portfolio_first_e2e_offline.py -q --basetemp='tmp/pytest_portfolio_first_e2e'
```

## Blocks 1-5 Five-Ticker MVP Smoke

Use this as the focused executable gate for Blocks 1-5 MVP reliability. The smoke test is fully
offline:

- validates a five-ticker `current_portfolio` `analysis_subject` with explicit weights;
- rejects missing, negative, and overallocated explicit subject weights before report generation;
- seeds synthetic `analysis_subject` diagnostics with `run_metadata.json`, `input_assumptions`,
  `snapshot_10y.json`, `portfolio_xray.json`, and `stress_report.json`;
- seeds offline `core_v1` `candidate_factory_run.json` evidence (plan argv uses `core_fast`; fixture profile unchanged);
- runs `write_candidate_comparison_outputs` and confirms `analysis_subject` is the baseline and
  current factory steps are used for candidate construction disclosure;
- blocks live Yahoo/FRED calls so the gate cannot silently depend on network data.

Command (workspace-local basetemp, Windows-safe):

```bash
python -m pytest tests/test_blocks_1_5_mvp_smoke.py -q --basetemp='tmp\pytest_rm1015_blocks_1_5_smoke'
python -m pytest tests/test_data_trust_signals.py -q --basetemp='tmp\pytest_rm1016_data_trust'
```

## Blocks 1-5 MVP Core Reliability (Phase 16)

Use this section when handing off or verifying the first-five-block MVP core without prior chat
context. Governed by
[Blocks 1-5 MVP Core Reliability Plan](docs/exec_plans/2026-05-21_blocks_1_5_mvp_core_reliability_plan.md).

**Routine CLI (representative live run, Session 09):**

```bash
python run_portfolio_review.py
python run_portfolio_review.py --with-candidates --skip-pdf
python run_portfolio_review.py --candidates equal_weight --skip-pdf
python run_portfolio_review.py --dry-run --mode full --resume-candidates --skip-pdf
```

**Note:** `tests/conftest.py` prepends the repository `tests/` directory so
`mvp_offline_fixtures` imports are not shadowed by a third-party `tests` package in
site-packages.

**Offline acceptance bundle (Sessions 02-08 focused gates; Session 09 closure):**

```bash
python -m pytest tests/test_input_assumptions.py -q --basetemp='tmp\pytest_rm1011_input'
python -m pytest tests/test_candidate_comparison.py tests/test_candidate_comparison_contract.py -q --basetemp='tmp\pytest_rm1012_comparison'
python -m pytest tests/test_portfolio_review_workflow.py -q --basetemp='tmp\pytest_rm1013_portfolio_review'
python -m pytest tests/test_optimization_readiness.py -q --basetemp='tmp\pytest_rm1014_readiness'
python -m pytest tests/test_blocks_1_5_mvp_smoke.py -q --basetemp='tmp\pytest_rm1015_blocks_1_5_smoke'
python -m pytest tests/test_data_trust_signals.py tests/test_stress_historical_fields.py tests/test_input_assumptions.py tests/test_portfolio_xray.py -q --basetemp='tmp\pytest_rm1016_trust_bundle'
python scripts/verify_docs.py
```

Session 09 closure (2026-05-21): single-command bundle above reported **125 passed**;
`verify_docs` OK.

**What the offline smoke proves:** five-ticker explicit weighted `analysis_subject`; config rejects
missing, negative, and overallocated weights; subject `run_metadata`, `input_assumptions`,
`portfolio_xray.json`, and `stress_report.json` exist; current `core_fast` factory evidence is
authoritative; `candidate_comparison.json` uses `analysis_subject` as baseline with
`candidate_menu.factory_evidence_status: current`. Output acceptance checklist:
[OUTPUTS.md](OUTPUTS.md) Blocks 1-5 section; operator commands:
[docs/operational_runbook.md](docs/operational_runbook.md) section 0.

## Blocks 1-5 Live Core E2E (Phase 17, RM-1021)

Governed by [Post-Deep-Audit Foundation Plan](docs/exec_plans/2026-05-21_post_deep_audit_foundation_plan.md)
Session 02. This gate is **networked** and **not** part of default `python -m pytest`; offline
`test_blocks_1_5_mvp_smoke.py` remains the executable closure gate for routine CI.

**Operator sequence:**

```bash
python run_portfolio_review.py --with-candidates --skip-pdf
python scripts/verify_live_core_e2e.py
python -m pytest tests/test_blocks_1_5_mvp_smoke.py -q --basetemp='tmp\pytest_blocks_1_5_smoke'
```

Or run and verify in one step:

```bash
python scripts/verify_live_core_e2e.py --run
```

**Pass criteria (artifact validation):**

| Check | Location |
| --- | --- |
| Subject diagnosis | `{output_dir_final}/analysis_subject/run_metadata.json`, `portfolio_xray.json`, `stress_report.json` |
| Diagnosis sections | All seven `XRAY_SECTION_KEYS` in `portfolio_xray.json` |
| Stress blocks | `stress_results_v1`, `hedge_gap_analysis_v1`, `current_portfolio_stress_scorecard_v1`, `stress_scorecard_v1`, `stress_conclusions`, `historical_methodology`, legacy `hedge_gap_analysis` |
| Comparison | `{output_dir_final}/candidate_comparison.json` present |
| Core menu | `candidate_menu.review_mode == "core"` |
| Factory profile | `candidate_factory_run.json` -> `factory_profile_id == "core_fast"` |

`factory_evidence_status: current` is expected after `run_portfolio_review.py` or
`run_candidate_factory.py --then-compare` (RM-1025). Validator warnings surface non-`current`
factory evidence when factory and comparison contexts diverge.

**Pytest marker (after a live run):**

```bash
python -m pytest tests/test_blocks_1_5_live_core_e2e.py --live-core -q
```

Enable via env: `PORTFOLIO_LIVE_CORE_E2E=1`. Offline validator unit test:
`tests/test_live_core_e2e_validation.py`.

Implementation: `src/live_core_e2e.py`, `scripts/verify_live_core_e2e.py`.

## Blocks 1-5 Live Full + Resume E2E (Phase 17, RM-1029)

Governed by [Post-Deep-Audit Foundation Plan](docs/exec_plans/2026-05-21_post_deep_audit_foundation_plan.md)
Session 10. Networked; not part of default `python -m pytest`. Use after Sessions 02-09 gates pass.

**Operator sequence (full menu):**

```bash
python run_portfolio_review.py --mode full --skip-pdf
python scripts/verify_live_full_e2e.py
```

**Recovery after interrupt:**

```bash
python run_portfolio_review.py --mode full --resume-candidates --skip-pdf
python scripts/verify_live_full_e2e.py --resume-candidates
```

Combined run + verify:

```bash
python scripts/verify_live_full_e2e.py --run
python scripts/verify_live_full_e2e.py --run --resume-candidates
```

**Pass criteria (artifact validation):**

| Check | Location |
| --- | --- |
| Subject diagnosis | Same as live core table above |
| Comparison | `candidate_comparison.json` present |
| Full menu | `candidate_menu.review_mode == "full"` |
| Factory profile | `candidate_factory_run.json` -> `factory_profile_id == "default_v1"` |
| Full menu scope | Factory `steps` length should match `default_v1` menu (16); warnings if partial |
| Resume (when flagged) | `candidate_factory_manifest.json` present; factory summary may show `resumed_from_manifest` |

`is_partial_menu: true` is a **warning**, not a hard failure - decision package must disclose scope
(`package_truthfulness`, RM-1028).

**Pytest marker (after a live run):**

```bash
python -m pytest tests/test_blocks_1_5_live_full_e2e.py --live-full -q
```

Enable via env: `PORTFOLIO_LIVE_FULL_E2E=1`. Offline validator unit tests:
`tests/test_live_full_e2e_validation.py`.

Implementation: `src/live_full_e2e.py`, `scripts/verify_live_full_e2e.py`.

## Phase 17 Post-Deep-Audit Closure Bundle (RM-1029)

Run when closing Session 10 / Phase 17 without prior chat context. Combines Blocks 1-5 smoke,
portfolio-first offline E2E, downstream 6-10 guards, and doc verification.

```bash
python -m pytest tests/test_blocks_1_5_mvp_smoke.py tests/test_live_core_e2e_validation.py tests/test_live_full_e2e_validation.py -q --basetemp='tmp\pytest_phase17_blocks_1_5'
python -m pytest tests/test_portfolio_first_e2e_offline.py tests/test_mvp_pipeline_offline.py -q --basetemp='tmp\pytest_phase17_portfolio_first'
python -m pytest tests/test_selection_engine.py tests/test_portfolio_health_score.py tests/test_optimization_readiness.py -q --basetemp='tmp\pytest_phase17_selection'
python -m pytest tests/test_optimizer_fair_comparison_full_menu.py tests/test_downstream_decision_readiness.py tests/test_blocks_6_7_downstream_integration.py -q --basetemp='tmp\pytest_phase17_downstream_67'
python -m pytest tests/test_package_truthfulness.py tests/test_blocks_8_10_downstream_integration.py tests/test_decision_package_reporting.py -q --basetemp='tmp\pytest_phase17_downstream_810'
python scripts/verify_docs.py
```

Live proof (operator, not CI default): `python scripts/verify_live_core_e2e.py --run` and
`python scripts/verify_live_full_e2e.py --run` (or `--run --resume-candidates` after interrupt).

## Change-To-Check Matrix

| Change area | Primary risks | Minimum checks | Broaden when |
| --- | --- | --- | --- |
| Data layer | Wrong prices, FX timing, return frequency, NaN alignment, young ETF behavior, benchmark/risk-free gaps | `tests/test_backtest_nan_safe.py`, `tests/test_returns_frequency.py`, `tests/test_young_etfs_dual_cov.py`; add `tests/test_historical_stress_fallback.py` when historical fallback changes | Run `python run_report.py --backtest-mode dynamic_nan_safe` if data flow or generated report inputs change |
| Portfolio metrics | Formula drift, wrong annualization, bad windows, rounding too early, beta/covariance alignment errors | Relevant focused tests around affected outputs, commonly `tests/test_metrics_drawdown.py`, `tests/test_returns_frequency.py`, `tests/test_backtest_nan_safe.py`, `tests/test_regime_portfolio_metrics.py`, `tests/test_portfolio_pca.py`, `tests/test_portfolio_commentary.py` | Run full pytest when shared metric helpers, windows, covariance, risk-free, FX, or report metric exports change |
| Optimizer / constraints | Infeasible weights, wrong bounds, broken mandate gate, changed release semantics, baseline drift | `tests/test_optimization_fallback.py`, `tests/test_config_weights_sync.py`, `tests/test_resampled_optimization_helpers.py`, `tests/test_young_etfs_dual_cov.py`; add affected baseline tests such as `tests/test_minimum_variance_baseline.py`, `tests/test_maximum_diversification_baseline.py`, `tests/test_minimum_cvar_baseline.py`, `tests/test_risk_parity_baseline.py`, `tests/test_risk_budgeting.py`, `tests/test_hrp_weights.py`, `tests/test_robust_mean_variance.py`, or `tests/test_robust_mv_calibration.py` | Run `python run_optimization.py` when main policy optimization, release status, or output files change |
| Stress scenarios | Scenario PnL drift, mandate/stress boundary confusion, missing historical fields, bad covariance taxonomy, changed diagnostic-only behavior | Stress Lab wave bundle (see above): `tests/test_stress_mandate_pass.py`, `tests/test_stress_historical_fields.py`, `tests/test_stress_covariance_taxonomy.py`, `tests/test_stress_scenario_analytics.py`, plus scorecard/hedge-gap/coverage/synthetic/simulator/artifacts/commentary contract tests; Core MVP historical replay: `tests/test_core_mvp_historical_stress_replay_config.py` (Session 1+), `tests/test_core_mvp_historical_stress_replay.py` (Sessions 2-4), `tests/test_core_mvp_historical_stress_replay_contract.py` (Session 5 cases A-D + Block 3.2), `tests/test_stress_results_historical_replay_contract.py` (Sessions 3-5). Normative contract: [core_mvp_historical_stress_replay_spec.md](docs/specs/core_mvp_historical_stress_replay_spec.md); decision DEC-2026-05-28-001; layer map [stress_lab_layer_spec.md](docs/specs/stress_lab_layer_spec.md) Section3.1.1/Section3.2; live gate after subject refresh: `python scripts/verify_core_mvp_historical_stress_replay.py` ([acceptance audit](docs/audits/2026-05-28_core_mvp_historical_stress_replay_acceptance_audit.md)) | Run `python run_portfolio_review.py --skip-candidates` (or `run_report.py --materialize-analysis-subject`) if `stress_report.json` changes; closure bundle: `python -m pytest tests/test_core_mvp_historical_stress_replay_config.py tests/test_core_mvp_historical_stress_replay.py tests/test_core_mvp_historical_stress_replay_contract.py tests/test_stress_results_historical_replay_contract.py -q` |
| Factor / macro analytics | Factor matrix drift, regression diagnostics broken, macro regime label instability, publication-lag mistakes, diagnostic blocks affecting policy | Factor tests: `tests/test_factor_matrix_builders.py`, `tests/test_factor_beta_stability.py`, `tests/test_factor_beta_adjusted_overlay.py`, `tests/test_factor_beta_kalman.py`, `tests/test_factor_covariance.py`, `tests/test_factor_oos_explainability.py`, `tests/test_factor_regression_hac.py`, `tests/test_factor_regression_heteroskedasticity.py`, `tests/test_factor_regression_serial.py`, `tests/test_factor_variance_decomposition.py`; macro tests: `tests/test_macro_regimes.py`, `tests/test_macro_primary_regime.py`, `tests/test_macro_indicators.py`, `tests/test_macro_scoring_modes.py`, `tests/test_macro_source_resolver.py`, `tests/test_macro_regime_label_quality.py`, `tests/test_macro_neutral_band_sensitivity.py`; regime tests: `tests/test_regime_factor_analytics.py`, `tests/test_regime_portfolio_metrics.py` | Run full pytest and `python run_report.py` when exported `stress_report.json` blocks or CSV artifacts change |
| Reports / outputs | Broken JSON/CSV schema, missing commentary, bad report rendering, stale generated files, changed user-facing artifacts | Portfolio Diagnosis wave bundle (see below) when `portfolio_xray.json` or diagnosis report surfaces change; otherwise `tests/test_portfolio_commentary.py` plus affected output tests such as `tests/test_scenario_library.py`, `tests/test_scenario_library_normalized.py`, `tests/test_stress_scenario_analytics.py`, `tests/test_regime_portfolio_metrics.py`, `tests/test_portfolio_pca.py` | Run `python run_report.py`; run `python rebuild_pdf_reports.py` only when PDF rebuild behavior or PDF-style artifacts are the target |
| Diagnosis-first product adapters | Broken product-bundle JSON, stale mapping from deterministic evidence, AI/commentary accidentally treated as calculator, technical artifacts promoted as product answer | Use the Post-Architecture Alignment adapter map above: focused tests for Problem Classification, Candidate Launchpad, Alternatives Builder, Current-vs-Candidate, Decision Verdict, AI grounding, and Light Monitoring | Add candidate comparison, selection, monitoring, or offline E2E tests when adapter inputs or runtime ordering change |
| Config / schema | Invalid config accepted, valid config rejected, config/weights desync, taxonomy validation drift | `tests/test_config_weights_sync.py`, `tests/test_returns_frequency.py`; add `tests/test_etf_universe.py` or `tests/test_stock_universe.py` for taxonomy config changes | Run affected CLI such as `python run_etf_universe.py`, `python run_stock_universe.py`, `python run_optimization.py`, or `python run_report.py` when user-facing config workflows change |
| Taxonomy onboarding (new tickers, stress blocks) | New rows in `etf_universe.yml` / `stock_universe.yml`, stress RC block mapping, onboarding report CLI | `tests/test_taxonomy_onboard_report.py`; adjacent `tests/test_stress_covariance_taxonomy.py` when block rules change | `python run_etf_universe.py validate`; `python run_stock_universe.py validate`; `python scripts/taxonomy_onboard_report.py --tickers TICK1,TICK2` |
| US universe ingestion (draft scale-up) | New/changed parsing, cleaning, ETF classifier, draft YAML, ingestion report | `python -m pytest tests/test_universe_ingestion.py tests/test_universe_merge.py -q` | Live: `python scripts/ingest_us_listed_universe.py --output-dir output/universe_ingestion_live`; merge preview: `python scripts/merge_draft_universe.py --ingestion-dir output/universe_ingestion_live`; confirm merge only after review: `--confirm` |
| Stock Batch 1 (index-based stock expansion) | New/changed `src/stock_batch_ingestion.py`, stock merge gates, `scripts/build_stock_batch1.py` | `python -m pytest tests/test_stock_batch_ingestion.py tests/test_stock_universe.py -q` | Offline build: `python scripts/build_stock_batch1.py --offline --output-dir output/stock_batch1`; live: omit `--offline`; merge preview: `python scripts/merge_draft_universe.py --stock-batch-dir output/stock_batch1`; confirm only when `merge_ready` in `stock_batch1_review_report.json` |
| Documentation-only change | Broken links, stale source-of-truth maps, obsolete commands, copied concept text treated as binding | Markdown link check; stale-reference search with `rg`; no `pytest` required unless executable examples, commands, or documented behavior changed | Run relevant CLI/test command if docs change executable examples or acceptance criteria |

For explicit `analysis_subject` weight validation changes, use the focused input assumptions check
first. It covers five-ticker current/model subjects with valid, missing, negative, partial, and
overallocated weights:

```bash
python -m pytest tests/test_input_assumptions.py -q --basetemp='tmp/pytest_rm1011_input'
```

For Blocks 1-5 reliability Session 04 (`RM-1013`) or later changes to portfolio-first candidate
resume wiring, use the focused workflow check and a dry-run smoke:

```bash
python -m pytest tests/test_portfolio_review_workflow.py -q --basetemp='tmp/pytest_rm1013_portfolio_review'
python run_portfolio_review.py --dry-run --mode full --resume-candidates --skip-pdf
```

Focused drawdown and time-to-recovery coverage lives in `tests/test_metrics_drawdown.py`. Keep adding targeted regression coverage when changing formulas, windows, annualization, FX, risk-free handling, covariance, beta, drawdown, or rounding.

## CLI Smoke Runs

Run CLI smoke checks when the change affects orchestration, generated outputs, or user-facing workflow.

Common existing entrypoints:

```bash
python run_portfolio_review.py
python run_portfolio_review.py --candidates equal_weight --skip-pdf
python run_portfolio_review.py --with-candidates --skip-pdf
python run_portfolio_review.py --mode full --resume-candidates --skip-pdf
python run_report.py
python run_optimization.py  # legacy policy compatibility
python run_report.py --backtest-mode dynamic_nan_safe
python run_view_after_optimization.py --asset VOO --delta 2
```

Candidate or robust portfolio changes should use the affected existing `run_*.py` script, for example:

```bash
python run_equal_weight.py
python run_risk_parity.py
python run_minimum_variance.py
python run_maximum_diversification.py
python run_minimum_cvar_constrained.py
python run_robust_mv_lambda_calibration.py
python run_robust_scenario_optimization.py
```

Do not run every candidate script by default. Run the affected entrypoint plus adjacent tests, then broaden only when shared candidate infrastructure changed.

## Stress Lab Wave Regression Bundle

Use this focused bundle after stress-layer contract changes (scorecard, hedge gap, scenario
coverage, synthetic assumptions, crisis replay paths, portfolio-first artifact resolution,
commentary/IPS stress narrative, or custom-shock simulator API). Baseline artifact fingerprints
live in [docs/audits/2026-05-20_stress_lab_baseline_snapshot.md](docs/audits/2026-05-20_stress_lab_baseline_snapshot.md).

## Stress Lab Governance Wave Bundle (Phase 13)

Governance wave (Phase 13, Sessions 01-11) **closed** 2026-05-20 per
[Stress Lab Methodology Governance Plan](docs/exec_plans/2026-05-20_stress_lab_methodology_governance_plan.md).
Methodology baseline (historical):
[docs/audits/2026-05-20_stress_lab_methodology_map.md](docs/audits/2026-05-20_stress_lab_methodology_map.md).
Re-run this bundle after Block 3 contract or downstream integration changes.

```bash
python -m pytest tests/test_current_portfolio_stress_scorecard_v1_contract.py tests/test_stress_scorecard_materialization.py tests/test_stress_results_block_contract.py tests/test_stress_diagnostic_mode.py tests/test_stress_scorecard_contract.py tests/test_stress_hedge_gap_contract.py tests/test_stress_scenario_coverage_contract.py tests/test_stress_synthetic_assumptions_contract.py tests/test_stress_simulator_contract.py tests/test_stress_mandate_pass.py tests/test_stress_scenario_analytics.py tests/test_stress_historical_fields.py tests/test_stress_covariance_taxonomy.py tests/test_stress_artifacts_priority.py tests/test_stress_downstream_integration.py tests/test_problem_classification.py tests/test_ai_commentary_context.py tests/test_portfolio_commentary.py tests/test_io_export_ips_summary.py -q
python scripts/verify_docs.py
```

## Block 3.4 Current Portfolio Stress Scorecard regression bundle

Governed by [Block 3.4 MVP](docs/exec_plans/2026-05-27_block_3_4_current_portfolio_stress_scorecard_plan.md) (**Completed**)
and [Block 3.4 Institutional Upgrade](docs/exec_plans/2026-05-29_block_3_4_current_portfolio_stress_scorecard_institutional_upgrade_plan.md) (Sessions 02-11 implementation; Session 12 docs).

Re-run after `current_portfolio_stress_scorecard_v1` builder, pre-stress bridges, snapshot mirror, Core MVP validator (`check_current_portfolio_stress_scorecard_v1`), or downstream consumers (`problem_classification`, `candidate_comparison`, `ai_commentary_context`, `portfolio_commentary` stress commentary) change.

```bash
python -m pytest tests/test_current_portfolio_stress_scorecard_v1_contract.py tests/test_stress_scorecard_materialization.py tests/test_problem_classification.py tests/test_ai_commentary_context.py tests/test_stress_downstream_integration.py tests/test_live_core_e2e_validation.py tests/test_portfolio_commentary.py -q
python scripts/verify_docs.py
```

Closure bundle (matches ExecPlan Sessions 10-13 verification):

```bash
python -m pytest tests/test_current_portfolio_stress_scorecard_v1_contract.py tests/test_problem_classification.py tests/test_ai_commentary_context.py tests/test_stress_downstream_integration.py tests/test_live_core_e2e_validation.py -q
```

## Block 3.2 Stress Results regression bundle

Governed by [Block 3.2 Stress Results ExecPlan](docs/exec_plans/2026-05-27_block_3_2_stress_results_plan.md)
(Session 07 closure). Re-run after `stress_results_v1` builder, diagnostic-mode, or downstream
commentary/snapshot mirror changes.

```bash
python -m pytest tests/test_stress_results_block_contract.py tests/test_stress_diagnostic_mode.py tests/test_stress_scenario_coverage_contract.py tests/test_stress_downstream_integration.py -q
python -m pytest tests/test_stress_scorecard_contract.py tests/test_stress_hedge_gap_contract.py -q
python scripts/verify_docs.py
```

## Block 3.3 Hedge Gap Analysis regression bundle

Governed by [Block 3.3 Hedge Gap Analysis MVP](docs/exec_plans/2026-05-27_block_3_3_hedge_gap_analysis_plan.md) (**Completed**)
and [Block 3.3 Institutional Upgrade](docs/exec_plans/2026-05-29_block_3_3_hedge_gap_institutional_upgrade_plan.md) (Sessions 02-10 implementation; Session 11 docs).

Re-run after `hedge_gap_analysis_v1` builder, scoring/bridge logic, snapshot or scorecard mirrors, Core MVP validator, or downstream consumers (`problem_classification`, `candidate_comparison`, `ai_commentary_context`) change.

```bash
python -m pytest tests/test_hedge_gap_analysis_v1_contract.py tests/test_hedge_gap_materialization.py tests/test_hedge_gap_candidate_comparison.py tests/test_problem_classification.py tests/test_ai_commentary_context.py tests/test_stress_results_block_contract.py tests/test_stress_scenario_coverage_contract.py tests/test_stress_diagnostic_mode.py tests/test_stress_hedge_gap_contract.py tests/test_stress_downstream_integration.py tests/test_live_core_e2e_validation.py -q
python scripts/verify_docs.py
```

When `stress_report.json` or sibling stress artifacts change intentionally, refresh the
representative subject run and update baseline hashes in the audit snapshot:

```bash
python run_report.py --materialize-analysis-subject
python run_stress_variant.py --variant main
```

## Portfolio Diagnosis Wave Regression Bundle

Use this focused bundle after Portfolio Diagnosis contract changes (seven-section JSON, risk budget RC
loading, factor/Kalman mapping, hidden-risk V2, weakness map V2, archetype scorecard, or structured
diagnosis report/commentary surfaces). Post-audit Sessions 09-10 (`RM-949`, `RM-950`) add golden JSON
contract tests and the baseline artifact checklist in
[docs/audits/2026-05-20_portfolio_xray_baseline_snapshot.md](docs/audits/2026-05-20_portfolio_xray_baseline_snapshot.md).

```bash
python -m pytest tests/test_portfolio_xray.py tests/test_portfolio_xray_threshold_registry.py tests/test_portfolio_xray_contract.py tests/test_portfolio_metrics_deepening.py tests/test_tail_risk.py tests/test_portfolio_commentary.py -q
python scripts/verify_docs.py
```

## Candidate Factory Governance Wave Bundle (Phase 14)

Governance wave (Phase 14, Sessions 00-11) **closed** 2026-05-20 per
[Candidate Portfolio Factory Post-Audit Roadmap](docs/exec_plans/2026-05-20_candidate_factory_post_audit_roadmap.md).
Methodology baseline:
[docs/audits/2026-05-20_candidate_factory_methodology_map.md](docs/audits/2026-05-20_candidate_factory_methodology_map.md).
Baseline checklist:
[docs/audits/2026-05-20_candidate_factory_baseline_snapshot.md](docs/audits/2026-05-20_candidate_factory_baseline_snapshot.md).

Re-run this bundle after Block 4 factory/comparison contract changes (reason codes, freshness,
`construction_disclosure`, config fingerprint, robust paths, resume manifest, or registry/menu schema):

```bash
python -m pytest tests/test_candidate_factory_contract.py tests/test_candidate_comparison_contract.py tests/test_candidate_factory.py tests/test_candidate_comparison.py tests/test_portfolio_review_workflow.py -q
python scripts/verify_docs.py
```

Golden fixtures (regenerate only after intentional `candidate_factory_run_v1` /
`candidate_comparison_v1` contract changes):

```bash
python tests/candidate_factory_golden_inputs.py
python -m pytest tests/test_candidate_factory_contract.py tests/test_candidate_comparison_contract.py -q
```

Committed fixtures:

- `tests/fixtures/candidate_factory_run_golden_v1.json`
- `tests/fixtures/candidate_comparison_golden_v1.json`

After Session 02+ builder reason mapping, confirm `test_builder_reason_mapping_contract` and
`test_factory_reason_from_builder_summary_mapping` pass in this bundle.

After Session 04+ `construction_disclosure`, confirm comparison disclosure passthrough tests and
`test_golden_comparison_post_audit_surface` (`equal_weight` available, `risk_parity` partial).

After Session 06+ config fingerprint, confirm `test_stale_config_fingerprint_*` and factory
`test_stale_config_fingerprint_rebuilds_same_analysis_end` pass in this bundle.

After Session 07+ robust paths, confirm factory robust disclosure tests and
`test_robust_scenario_construction_disclosure_main_prerequisites` pass in this bundle.

After Blocks 1-5 reliability Session 03 (`RM-1012`), confirm
`test_stale_factory_summary_not_used_after_fresh_comparison_rebuild` passes so stale
`candidate_factory_run.json` steps are reported in `candidate_menu` but not treated as current row
evidence.

After Candidate Factory parallel lightweight report changes, confirm
`test_parallel_lightweight_reports_overlap_and_keep_menu_order`,
`test_parallel_lightweight_report_failure_continues_without_fail_fast`, and
`test_parallel_lightweight_reports_requested_fail_fast_uses_sequential_fallback` in
`tests/test_candidate_factory.py`. The focused command is:

```bash
python -m pytest tests/test_candidate_factory.py tests/test_candidate_manifest.py -q --basetemp='tmp\pytest_candidate_parallel'
```

Session 11 wave closure (2026-05-20): governance bundle **77 passed**; family spot-check **19 passed**;
`verify_docs` OK. Phase 14 (`RM-970`-`RM-981`) complete.

When `candidate_factory_run.json` or `candidate_comparison.json` change intentionally on a live
run, refresh baseline fingerprints per
[docs/audits/2026-05-20_candidate_factory_baseline_snapshot.md](docs/audits/2026-05-20_candidate_factory_baseline_snapshot.md):

```bash
python run_portfolio_review.py --with-candidates
```

## Optimization Engine Governance Wave Bundle (Phase 15)

Governance wave (Phase 15, Sessions 00-12) is **closed** as of 2026-05-21 per
[Optimization Engine Post-Audit Roadmap](docs/exec_plans/2026-05-20_optimization_engine_post_audit_roadmap.md).
Methodology baseline:
[docs/audits/2026-05-20_optimization_engine_methodology_map.md](docs/audits/2026-05-20_optimization_engine_methodology_map.md).
Baseline checklist:
[docs/audits/2026-05-20_optimization_engine_baseline_snapshot.md](docs/audits/2026-05-20_optimization_engine_baseline_snapshot.md).

Session 00 is documentation-only:

```bash
python scripts/verify_docs.py
```

After code or output-contract sessions, run the focused Block 5 bundle:

```bash
python -m pytest tests/test_legacy_policy_optimizer_disclosure.py tests/test_optimization_fallback.py tests/test_config_weights_sync.py tests/test_young_etfs_dual_cov.py -q
python -m pytest tests/test_minimum_variance_baseline.py tests/test_maximum_diversification_baseline.py tests/test_minimum_cvar_baseline.py -q
python -m pytest tests/test_robust_mean_variance.py tests/test_robust_mv_calibration.py tests/test_robust_scenario_optimization.py -q
python -m pytest tests/test_optimization_readiness.py tests/test_optimizer_fair_comparison_full_menu.py tests/test_optimization_engine_contract.py tests/test_candidate_factory.py tests/test_candidate_comparison.py tests/test_candidate_factory_contract.py tests/test_candidate_comparison_contract.py -q
python scripts/verify_docs.py
```

Phase 17 Session 04 (`RM-1023`) - full-menu optimizer fair-comparison offline gate (builder metadata +
snapshot `candidate_config_fingerprint`; expects ≥3 `fair_comparison_ready` optimizer rows):

```bash
python -m pytest tests/test_optimizer_fair_comparison_full_menu.py -q
```

Golden contract fixtures (Session 11 / `RM-1001`):

```bash
python tests/optimization_engine_golden_inputs.py
python -m pytest tests/test_optimization_engine_contract.py -q
```

- `tests/fixtures/legacy_policy_optimizer_run_metadata_golden_v1.json`
- `tests/fixtures/candidate_optimizer_run_metadata_golden_v1.json`
- `tests/fixtures/optimization_comparison_block5_golden_v1.json`
- `tests/fixtures/optimization_comparison_full_menu_fair_ready_golden_v1.json` (RM-1023)
- **Inputs:** `tests/optimization_engine_golden_inputs.py`
- **Tests:** `tests/test_optimization_engine_contract.py`, `tests/test_optimizer_fair_comparison_full_menu.py`

Run `python run_optimization.py` only when legacy policy outputs change. Run affected candidate or
robust scripts only when their wrapper/output contract changes. Do not refresh generated artifacts
for commit unless the session explicitly targets generated outputs.

Session 05 comparison-level optimizer disclosure: confirm
`test_optimizer_candidate_methodology_disclosure_from_baseline_metadata` and
`test_policy_optimizer_methodology_disclosure_from_run_result` in `tests/test_candidate_comparison.py`
pass after changes to `construction_disclosure.optimizer_methodology`.

Session 06 fallback/failure policy: confirm
`test_factory_step_surfaces_optimizer_fallback_quality` in `tests/test_candidate_factory.py`,
`test_optimizer_fallback_quality_degrades_comparison_row` and
`test_failed_factory_step_blocks_comparison_row_even_with_snapshot` in
`tests/test_candidate_comparison.py`, and
`test_selection_warns_when_favored_candidate_has_optimizer_fallback` in
`tests/test_selection_engine.py`.

Session 07 robust scenario solver disclosure: confirm
`test_build_inputs_and_optimize_round_trip` in `tests/test_robust_scenario_optimization.py`,
`test_robust_scenario_factory_step_surfaces_solver_quality` in `tests/test_candidate_factory.py`,
and `test_robust_scenario_optimizer_methodology_disclosure` in
`tests/test_candidate_comparison.py`.

Session 08 estimator date/fingerprint disclosure: confirm
`tests/test_legacy_policy_optimizer_disclosure.py`,
`tests/test_minimum_variance_baseline.py`, `tests/test_maximum_diversification_baseline.py`,
`tests/test_minimum_cvar_baseline.py`, and `tests/test_robust_mean_variance.py` cover
`input_fingerprints`, return-panel start/end/row fields, and estimator `analysis_end` propagation.

Session 09 covariance / Young ETF methodology disclosure: confirm
`tests/test_legacy_policy_optimizer_disclosure.py`, `tests/test_minimum_variance_baseline.py`,
`tests/test_robust_mean_variance.py`, `tests/test_candidate_comparison.py`, and
`tests/test_io_export_ips_summary.py` cover `optimizer_covariance_methodology_v1`,
`optimizer_young_etf_methodology_v1`, comparison-level passthrough, and human TXT summaries.

Session 10 optimization comparison readiness: confirm
`tests/test_optimization_readiness.py` and `test_block5_golden_post_audit_surface` in
`tests/test_optimization_engine_contract.py` cover `optimizer_comparison_readiness_v1`,
`fair_comparison_ready`, and Block 5 comparison disclosure keys.

Blocks 1-5 reliability Session 05 (`RM-1014`) optimizer readiness normalization: confirm
`tests/test_optimization_readiness.py`, `tests/test_candidate_comparison.py`, and
`tests/test_optimization_engine_contract.py` cover degradation of otherwise available
optimizer-backed rows when optimizer methodology is absent, optimizer quality is absent, or solver
quality normalizes to `unknown`.

Session 11 golden contracts and governance bundle closure (2026-05-21): Block 5 governance bundle
**159 passed** (`test_optimization_engine_contract.py` 9 tests included in comparison/factory line);
`verify_docs` OK. Regenerate optimizer golden JSON only after intentional disclosure contract changes.

Session 12 wave closure (2026-05-21): Phase 15 **Done** (`RM-990`-`RM-1002`); baseline snapshot,
ROADMAP, ExecPlan register, `KNOWN_ISSUES` Block 5 gap index, `CHANGELOG`; governance bundle
**159 passed**; `verify_docs` OK.

## Artifact Checks

Generated outputs are evidence, not source, unless the task explicitly targets generated artifacts.

Use [OUTPUTS.md](OUTPUTS.md) to identify which generated folders, artifacts, formats, and source-vs-generated boundaries apply.

Inspect artifacts when their schema, existence, naming, or user-facing content is part of the change:

- `portfolio_weights.yml` and `run_result.json` for optimizer release and weights.
- `stress_report.json` for stress, factor, macro, regime, PCA, and scenario diagnostics.
- `scenario_library.json` and `scenario_library_normalized.json` for scenario-library changes.
- CSV files under `results_csv/` for tabular diagnostics.
- `commentary.txt` and `stress_commentary.txt` for generated narrative output.
- Generated HTML and PDF-style outputs only when report rendering or PDF rebuild behavior changes.

If a CLI smoke run rewrites generated outputs, do not treat those files as source unless the user explicitly asked to update generated artifacts.

## Documentation Checks

Documentation changes require link and stale-reference verification when they rename files, move docs, add source-of-truth maps, or edit commands.

Minimum checks:

```bash
python scripts/verify_docs.py
python -m pytest tests/test_docs_links.py -q
```

- Search for stale names or removed paths with `rg` (for example `rc_asset_cap_pct` in editable UI surfaces after Session 03).
- Confirm changed command examples are real entrypoints or real test commands.

`scripts/verify_docs.py` scans source Markdown under the repo root, `docs/`, and `.cursor/` agents/rules. It checks local file links (repo-root and file-relative), forbidden stale canonical paths, and that `config_ui` does not reintroduce removed editable fields. Planned future spec filenames listed in `src/docs_verify.py` are allowed until those specs are created.

**Archive link hygiene:** `docs/archive/**` is included in the scan. From
`docs/archive/documentation_migration_2026_05_25/`, use `../../../` for repo-root files (for example
`SPEC.md`) and `../../specs/` for canonical specs. Fix broken relative paths only; do not rewrite
historical archive product meaning.
- Keep [docs/DIAGNOSTIC_PRODUCT_CONCEPT.md](docs/DIAGNOSTIC_PRODUCT_CONCEPT.md) non-binding: ideas from that document do not require code tests unless they are promoted into `SPEC.md`, `DATA.md`, `docs/specs/*.md`, or implementation work.

## Source-Of-Truth Links

- Use [RULES.md](RULES.md) for project-wide principles.
- Use [SPEC.md](SPEC.md) for the current implementation contract.
- Use [docs/specs/portfolio_review_workflow_spec.md](docs/specs/portfolio_review_workflow_spec.md) for
  the portfolio-first `analysis_subject` workflow and legacy policy boundary.
- Use [OUTPUTS.md](OUTPUTS.md) for generated output folders, artifacts, formats, report packaging, and generated-vs-source boundaries.
- Use [DATA.md](DATA.md) for data-layer expectations.
- Use [docs/specs/](docs/specs/README.md) for detailed module behavior.
- Use this file for verification strategy and test selection.
- Use [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for active testing gaps, model limitations, technical debt, and known weak spots.
- Use [AGENTS.md](AGENTS.md) only for agent operating rules and the requirement to follow this file.
