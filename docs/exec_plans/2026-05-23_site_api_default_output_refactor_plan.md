# Site/API Default Output Refactor Plan

**Status:** Completed (Sessions 0–7 closed 2026-05-23). Closure:
[Session 07 closure report](../audits/2026-05-23_site_api_default_output_session07_closure_report.md).

This ExecPlan is a living implementation plan. Generated artifacts are evidence, not source of
truth. The refactor changes output routing and execution defaults only; it does not change formulas,
optimizers, stress methodology, candidate weights, comparison ranking, or selection logic.

## Purpose

Make the default project workflow lean for future website/API usage:

```text
config / analysis_subject
-> validation and assumptions
-> data loading / cache
-> diagnostics
-> candidate generation when requested
-> lightweight comparison
-> decision/action JSON contracts
-> machine-readable output_manifest.json
```

Default runs must not generate PDF, HTML, TXT, PNG, CSV, Markdown PDF sidecars, or CSS/visual
presentation assets.

## Scope

- Introduce a central output policy with `site_api`, `core_json`, `lightweight_comparison`,
  `full_report`, and `legacy_export` profiles.
- Switch normal defaults to `site_api` JSON/cache-first behavior.
- Keep CSV/report/export code in place, but make it explicit export/report behavior.
- Preserve required JSON contracts for subject diagnostics, candidate factory, comparison,
  robustness, health, selection, action, monitoring, journal, and decision package summary.
- Add `output_manifest.json` as the UI/API artifact index.
- Update documentation and tests to prove disabled artifact classes are absent by count.

## Non-goals

- No deletion of legacy/report/export source code.
- No cleanup or deletion of historical generated files already on disk.
- No changes to investment formulas, optimizer behavior, stress scenarios, candidate weights,
  comparison ranking, selection rules, or precision policy.
- No product/UI rewrite.

## Current Behavior

- `run_report.py` defaults to the full report profile and writes CSV/TXT/HTML/commentary outputs.
- `run_portfolio_review.py` defaults to portfolio-first flow but schedules a PDF rebuild unless
  skipped.
- `run_candidate_factory.py` has optimized standard mode available, but the CLI default was still
  legacy-full.
- `run_optimization.py` implicitly runs `run_report.py` and attempts PDF rebuilds.
- `write_candidate_comparison_outputs()` writes TXT and legacy subset comparison outputs by default.

## Target Behavior

- `run_report.py` default: `site_api`, JSON contracts + cache only.
- `run_portfolio_review.py` default: `site_api`, no PDF rebuild.
- `run_candidate_factory.py` CLI default: `standard` execution with `site_api` output policy.
- `run_optimization.py` default: optimize/write policy JSON/YAML outputs only; no report/PDF unless
  `--with-report` is explicitly provided.
- Legacy/export outputs remain available through `full_report`, `legacy_export`, and explicit PDF
  commands/flags.

## Artifact Policy

| Artifact type | Default site/API mode | Explicit export/report mode |
| --- | --- | --- |
| JSON contracts | Required | Required |
| Parquet/cache | Allowed where needed | Allowed |
| Minimal YAML/config outputs | Allowed if architecturally required | Allowed |
| CSV | Disabled | Allowed for audit, Excel review, debugging, legacy reports |
| TXT | Disabled | Allowed |
| HTML | Disabled | Allowed |
| PNG | Disabled | Allowed |
| PDF | Disabled | Allowed |
| Markdown PDF sidecars | Disabled | Allowed |
| CSS / visual assets | Disabled | Allowed |

CSV exporters must remain source-supported but export-only.

## Session Breakdown

- **Session 0:** Discovery, code/output map, create this ExecPlan.
- **Session 1:** Add central output policy and output manifest helper.
- **Session 2:** Apply policy to report, candidate factory, portfolio review, optimization, and
  comparison defaults.
- **Session 3:** Preserve JSON contracts and replace any downstream CSV/TXT/HTML dependency with JSON
  inputs.
- **Session 4:** Documentation sync and command matrix.
- **Session 5:** Focused tests and default artifact absence count.
- **Session 6:** Runtime benchmark with artifact counts by type.
- **Session 7:** Closure report.

## Risks

- Hidden CSV dependency in commentary, Portfolio X-Ray, robust scenario, or downstream comparison.
- Legacy operators expecting `run_optimization.py` to build reports implicitly.
- Existing tests that encoded report-first defaults.
- Stale generated files in the working tree making manual artifact inspection confusing.

## Rollback Strategy

- Revert source changes to `src/output_policy.py`, entrypoint wiring, and guarded writer calls.
- Legacy/export source code is not deleted, so restoring report-first defaults is a small routing
  change.
- Do not touch or delete generated historical artifacts during rollback.

## Verification Plan

- Focused tests:
  - output policy / report profile tests;
  - candidate factory tests;
  - portfolio review workflow tests;
  - candidate comparison and downstream decision readiness tests;
  - reporting output tests affected by policy.
- CLI smoke:
  - default site/API workflow;
  - candidate factory site/API mode;
  - portfolio review site/API mode;
  - explicit `full_report`/`legacy_export` mode;
  - explicit PDF export mode.
- Artifact count:
  - clean temporary default run must produce zero `.pdf`, `.html`, `.txt`, `.png`, `.csv`,
    Markdown PDF sidecars, and CSS/visual presentation assets.

## Timing Benchmark Plan

Measure wall-clock time, per-stage timing when available, artifact counts by type, required JSON
presence, missing/failed outputs, and remaining bottlenecks. Compare with known baselines:

- legacy `default_v1`: ~57-61 minutes;
- optimized parallel path: ~10-11 minutes;
- sequential after Shared Evidence: ~15 minutes.

## Documentation Sync Plan

Update `README.md`, `ARCHITECTURE.md`, `OUTPUTS.md`, `PRODUCT.md`,
`docs/specs/reporting_outputs_spec.md`, `docs/specs/portfolio_review_workflow_spec.md`, and
`docs/specs/candidate_factory_spec.md` with:

- JSON as default machine-readable contract;
- cache as internal;
- CSV/TXT/HTML/PNG/PDF/Markdown/CSS disabled by default;
- CSV retained as export-only;
- command matrix for site/API, factory, review, legacy report, PDF export, and benchmark runs.

## Acceptance Criteria

1. Default workflow no longer generates presentation/export artifacts.
2. Required JSON contracts still generate successfully.
3. Cache continues to work.
4. Candidate generation and comparison still work.
5. No formulas, optimizer outputs, stress logic, or weights change.
6. Legacy/export mode remains explicitly callable.
7. Documentation clearly explains output policy and commands.
8. Focused tests pass.
9. Timing benchmark includes artifact counts.
10. Final closure report documents remaining risks and next optimization step.

## Progress

- 2026-05-23: Session restarted after prior read-only environment blocked writes. Discovery re-run
  against docs and entrypoints. Implementation began with central output policy and default routing.
- 2026-05-23: **Session 3 done.** Rolling beta CSV/HTML/PNG exports gated on `output_policy`;
  `RC_asset_all` added to window snapshots; `load_rc_vol_map_from_snapshot` + JSON-first RC resolution
  for X-Ray and commentary; candidate factory Phase 2/3 pass `output_profile` into reports.
  Tests: `test_resolve_rc_asset_prefers_snapshot_json_before_csv`,
  `test_site_api_with_full_report_profile_writes_no_presentation_artifacts`.
- 2026-05-23: **Session 4 done.** Documentation sync: `README.md`, `ARCHITECTURE.md`, `OUTPUTS.md`,
  `PRODUCT.md`, `reporting_outputs_spec.md`, `portfolio_review_workflow_spec.md`,
  `candidate_factory_spec.md` — site/API default, `output_manifest.json`, export-only CSV/PDF,
  expanded command matrix, corrected PDF-by-default wording.
- 2026-05-23: **Session 5 done.** Focused tests: `tests/test_output_policy.py` (policy aliases,
  manifest, MVP comparison artifact counts, full_report TXT path, optimization CLI defaults);
  `test_mvp_pipeline_offline` and `test_portfolio_first_e2e_offline` aligned to JSON-only site_api
  (no `decision_package_summary.txt`). Verification:
  `python -m pytest tests/test_output_policy.py tests/test_report_profile.py
  tests/test_portfolio_review_workflow.py tests/test_mvp_pipeline_offline.py
  tests/test_portfolio_first_e2e_offline.py -q`.
- 2026-05-23: **Session 6 done.** Runtime benchmark: `scripts/site_api_session06_benchmark_smoke.py`
  (isolated `tmp/site_api_session06/benchmark/`, `core_benchmarks` × 2, `site_api` + `then_compare`);
  wall **171.6 s**, `report_seconds` **155.0** (−25.7% vs 2026-05-22 baseline 208.7 s); presentation
  artifact counts **0** across project root and candidates; decision-package JSON **14/14** present;
  pytest bundle **38 passed**. Audit:
  [Session 06 timing audit](../audits/2026-05-23_site_api_default_output_session06_timing_audit.md).
- 2026-05-23: **Session 7 done (plan closed).** Closure report, register updates, acceptance sign-off.
  Re-verification: pytest bundle **38 passed** (`tmp/pytest_site_api_session7`). Audit:
  [Session 07 closure report](../audits/2026-05-23_site_api_default_output_session07_closure_report.md).

## Surprises & Discoveries

- Rolling beta CSV/HTML/PNG were still emitted until Session 3 gated them on `output_policy`; tests
  now assert zero presentation files for `site_api` even when `report_profile=full`.
- RC_vol for Portfolio X-Ray and commentary had a hidden CSV fallback; Session 3 added
  `RC_asset_all` in snapshots and JSON-first `load_rc_vol_map_from_snapshot`.
- Default `run_optimization.py` previously implied full report + PDF; operators must now pass
  `--with-report` explicitly — documented as a behavioral change, not a bug.
- Session 6 wall-clock improvement (−27%) is largely warm cache + prior shared-evidence work;
  artifact-policy proof is independent of that timing delta.

## Decision Log

- Decision: Centralize profiles in `src/output_policy.py` with `site_api` as `DEFAULT_OUTPUT_PROFILE`.
  Rationale: Single gate for CSV/TXT/HTML/PNG/PDF/Markdown/CSS across report, factory, review, and comparison.
  Date/Author: 2026-05-23 / implementation sessions 1–2.

- Decision: Keep all legacy export code; gate writes with `output_policy` rather than delete modules.
  Rationale: Rollback and explicit `full_report` / `legacy_export` operator paths.
  Date/Author: 2026-05-23 / ExecPlan non-goals.

- Decision: `run_optimization.py` skips `run_report.py` and PDF rebuild unless `--with-report`.
  Rationale: Site/API default is optimize + JSON/YAML only; reports are explicit export behavior.
  Date/Author: 2026-05-23 / session 2.

- Decision: Emit `output_manifest.json` as the UI/API artifact index on gated runs.
  Rationale: Machine-readable index of enabled/disabled artifact classes per run.
  Date/Author: 2026-05-23 / session 1.

## Outcomes & Retrospective

Sessions 0–7 delivered JSON/cache-first defaults for website/API integration without changing
investment semantics. Entrypoints (`run_report.py`, `run_portfolio_review.py`,
`run_candidate_factory.py`, `run_optimization.py`, comparison writers) default to `site_api`;
presentation artifacts require explicit profiles or PDF/export commands.

Verification: focused pytest **38 passed**; Session 6 isolated smoke proved presentation artifact
counts **0** and decision-package JSON **14/14** with `comparison_succeeded` true.

**Product outcome:** Operators and future UI/API consumers get lean machine-readable runs by default;
audit and client PDF paths remain one flag away.

**Remaining work (outside this ExecPlan):** Report CPU optimization (shared evidence extensions,
optional parallel lightweight reports), CI artifact-count gate, and operator communication for
`--with-report` on legacy optimize flows.

**Closure evidence:** [Session 07 closure report](../audits/2026-05-23_site_api_default_output_session07_closure_report.md).

