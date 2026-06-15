# Accelerate cold Run Diagnostics with parallel data loading

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows `PLANS.md` from the repository root. It is self-contained so a future
agent can resume from this file without prior chat context.

## Purpose / Big Picture

A user who clicks Run Diagnostics should not wait minutes because the first backend run is loading
external market and macro data one item at a time. The previous performance work made warm runs fast
by caching repeated data, but the first cold run can still be slow when Yahoo, FRED, factor proxies,
and macro indicators need to be fetched. This plan keeps every formula, stress scenario, diagnostic,
and output contract intact, and only changes the orchestration of independent I/O-bound data loads so
multiple external requests can run at the same time within safe worker limits.

The visible outcome is that the existing staged Run Diagnostics flow still shows progress and recovers
same-run artifacts, while a cold run against the same standard payload completes materially faster or
reports a clear external-provider blocker. A warm run must remain at or below the existing 30-second
target.

## Progress

- [x] (2026-06-15 15:05Z) Session 1 created this checked-in ExecPlan as a documentation-only step.
- [x] (2026-06-15 16:20Z) Session 2 added `src/parallel_data_loading.py`, a bounded standard-library helper with `PMRI_DISABLE_PARALLEL_DATA_LOAD=1` rollback and per-area worker caps.
- [x] (2026-06-15 16:25Z) Session 2 parallelized yfinance ticker downloads in `src/data_yf.py` while preserving ticker insertion order and currency metadata.
- [x] (2026-06-15 16:32Z) Session 2 parallelized independent weekly, monthly, and daily factor proxy loaders in `src/stress_factors.py` while preserving registry order and hard failure propagation.
- [x] (2026-06-15 16:38Z) Session 2 parallelized independent macro indicator resolution in `src/stress_factors_macro.py`; each indicator still calls `resolve_indicator()` normally, so source fallback order inside one indicator is unchanged.
- [x] (2026-06-15 16:55Z) Session 2 added focused regression tests for deterministic order, rollback mode, overlap, and error semantics in `tests/test_parallel_data_loading.py`, and stabilized factor cache tests by clearing process-local caches before each factor builder test.
- [x] (2026-06-15 17:05Z) Session 2 updated `DATA.md`, `TESTING.md`, `CHANGELOG.md`, and this ExecPlan for the new data-loading behavior.
- [x] (2026-06-15 17:15Z) Session 2 ran focused Python tests; frontend safety checks were not required because no frontend code changed.
- [ ] Session 2 run performance smoke comparisons when a staged `runs/.../payload.json` is available locally or supplied by the operator.

## Surprises & Discoveries

- Observation: Initial code inspection found that yfinance ticker downloads are sequential.
  Evidence: `src/data_yf.py` `download_all()` loops over tickers and calls `fetch_daily()` one at a time.
- Observation: Factor matrix construction is sequential for weekly, monthly, and daily factor loaders.
  Evidence: `src/stress_factors.py` `_build_factor_frame()` and `_build_factor_frame_daily()` loop over factor definitions.
- Observation: Macro source fallback order is intentionally sequential inside one indicator.
  Evidence: `src/data_macro_sources.py` `resolve_indicator()` tries each source in `source_chain` until one succeeds.
- Observation: The factor builder regression file depended on process-local caches being empty between tests.
  Evidence: `tests/test_factor_matrix_builders.py` failed as a full file until the test fixture cleared `sf.clear_factor_matrix_memory_cache()` and `data_fred.clear_fred_series_memory_cache()` before each test.
- Observation: No staged performance payload is present in this working tree.
  Evidence: `rg --files runs | rg "payload\.json$"` returned no matches, so live cold/warm timing comparison could not be run in this session.

## Decision Log

- Decision: Use a Balanced default profile with modest worker counts: yfinance 4, factor 4, macro 3.
  Rationale: Yahoo and FRED can rate-limit or time out under aggressive concurrency; the goal is faster cold runs without making provider failures more common.
  Date/Author: 2026-06-15 / Codex
- Decision: Provide a global rollback switch named `PMRI_DISABLE_PARALLEL_DATA_LOAD=1` plus per-area worker environment variables.
  Rationale: Operators need a simple way to return to sequential behavior if an external provider reacts poorly to parallel requests.
  Date/Author: 2026-06-15 / Codex
- Decision: Do not parallelize fallback attempts inside a single macro indicator.
  Rationale: The source chain is a precedence rule, not a set of equivalent requests; changing it could alter provenance and diagnostics.
  Date/Author: 2026-06-15 / Codex

## Outcomes & Retrospective

Session 1 is complete: the plan is checked in and no runtime code was intentionally changed by that session.

Session 2 implemented bounded parallel data loading for independent yfinance, factor, and macro data
requests. Focused Python regression tests pass and the rollback switch is covered by unit tests.
Measured cold/warm staged performance is still pending because no `runs/.../payload.json` exists in
this working tree.

## Context and Orientation

The staged web diagnosis path starts in the frontend and creates a backend `review_id`; the backend then runs Python diagnostics in the background. The latency addressed by this plan is inside the Python data pipeline, not the frontend. A cold run means the backend process does not already have the needed price, FRED, factor, and macro data in memory. A warm run means those data loads can reuse memory or disk cache from earlier work.

The relevant data-loading files are:

- `src/data_yf.py`, where `fetch_daily()` downloads one Yahoo/yfinance ticker and `download_all()` currently downloads a list one ticker at a time.
- `src/stress_factors.py`, where `_build_factor_frame()` and `_build_factor_frame_daily()` build weekly, monthly, and daily factor matrices by calling independent loaders for each factor.
- `src/data_macro_sources.py`, where `resolve_indicator()` preserves source precedence for one macro indicator.
- `src/stress_factors_macro.py`, where macro indicator specs are assembled and fetched for macro regime diagnostics.

A bounded parallel loader means a small `ThreadPoolExecutor` wrapper that runs independent network-bound tasks with a maximum worker count, preserves deterministic output order, and returns captured exceptions to the caller so existing error handling can decide whether an item becomes missing or a hard failure.

## Plan of Work

First, add an internal helper module for parallel data loading. The helper must read integer worker limits from environment variables, cap them to a safe range, honor `PMRI_DISABLE_PARALLEL_DATA_LOAD=1`, preserve input order, and capture exceptions per task. The helper should be dependency-light and use only Python standard-library concurrency.

Second, update `src/data_yf.py`. Keep `fetch_daily()` as the one-ticker implementation and keep its cache behavior. Change `download_all()` so it uses the helper to run one `fetch_daily()` task per ticker with `PMRI_YF_MAX_WORKERS`, defaulting to 4. If parallel loading is disabled or the effective worker count is 1, it should run exactly like the old loop. Returned dictionaries should still use the original ticker keys and attach the same currency metadata.

Third, update `src/stress_factors.py`. Keep every factor loader and all factor formulas unchanged. Replace only the orchestration loops in `_build_factor_frame()` and `_build_factor_frame_daily()` with bounded parallel execution across independent factors. The result processing must remain in `FACTOR_DEFINITIONS` order so column order, diagnostics, and missing-factor behavior remain stable. `FactorDataUnavailableError` must still propagate for hard failures where the current implementation propagates it.

Fourth, update macro loading cautiously. Do not alter `src/data_macro_sources.py` fallback-chain semantics. Instead, add parallel execution at the level that iterates over multiple macro indicators in `src/stress_factors_macro.py`, preserving output order and metadata. Each indicator should still call `resolve_indicator()` normally, so FRED-to-Yahoo-to-CSV precedence remains unchanged.

Fifth, update tests. Add focused tests that prove yfinance and factor loaders overlap when workers are greater than one, prove rollback mode is sequential, prove ordering is deterministic, and prove item-level errors are handled the same way as before. Reuse monkeypatch-based fake loaders rather than live network calls.

Finally, update documentation and performance evidence. `DATA.md` should mention bounded process-local parallel data loading and rollback environment variables. `TESTING.md` should include the sequential-vs-parallel performance smoke comparison. `CHANGELOG.md` should record the completed behavior change. This ExecPlan must be updated as each milestone completes.

## Concrete Steps

From the repository root in PowerShell, first verify Python is available through the existing virtual environment:

    .\.venv\Scripts\python.exe --version

Session 1 writes only this file and validates formatting:

    git diff --check

Session 2 implementation should proceed in small patches. After adding the helper and tests for it, run the new focused tests. After changing yfinance, run the data provider and runtime cache tests. After changing factor and macro loaders, run the factor and macro suites.

The expected focused verification commands are:

    .\.venv\Scripts\python.exe -m pytest tests\test_parallel_data_loading.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_runtime_memory_caches.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_factor_matrix_builders.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_macro_source_resolver.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_analysis_subject_materialization.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_blocks_1_5_mvp_smoke.py -q

The expected frontend safety checks are:

    cd frontend
    npm.cmd run typecheck
    npm.cmd run test:api
    npm.cmd run test:smoke
    cd ..

The expected performance comparison uses the standard staged payload if present:

    .\.venv\Scripts\python.exe scripts\diagnosis_performance_smoke.py --payload runs\frontend_review_20260615T122821Z_q53Uoxnn4lFKi6J8TfYH2Q\payload.json --warm-threshold-seconds 30 --timeout-seconds 420
    $env:PMRI_DISABLE_PARALLEL_DATA_LOAD = "1"
    .\.venv\Scripts\python.exe scripts\diagnosis_performance_smoke.py --payload runs\frontend_review_20260615T122821Z_q53Uoxnn4lFKi6J8TfYH2Q\payload.json --warm-threshold-seconds 30 --timeout-seconds 420
    Remove-Item Env:\PMRI_DISABLE_PARALLEL_DATA_LOAD

If the payload is absent, the implementer should use the nearest existing staged payload with `payload.json` and record the path in this plan.

## Validation and Acceptance

The behavior is accepted when existing diagnostics still materialize the same required artifacts and the focused tests pass. No formula, stress scenario, diagnostic output, public API response, or frontend route should be intentionally removed or renamed.

Performance acceptance is: warm staged diagnosis remains at or below 30 seconds on the standard payload, and cold staged diagnosis is materially faster than the current baseline of roughly 118 to 150 seconds. The target improvement for this iteration is at least 25 percent on the same machine and payload, unless the script reports a specific external-provider or cache blocker.

The implementation must be observable through terminal output. A successful performance transcript should include `status=passed`, a warm runtime below `warm_threshold_seconds=30.000`, and recorded cold/warm seconds for both parallel-enabled and rollback sequential modes.

## Idempotence and Recovery

All changes are additive and safe to run repeatedly. If `PMRI_DISABLE_PARALLEL_DATA_LOAD=1` is set, yfinance, factor, and macro loading must use sequential behavior. If a per-area worker environment variable is missing, invalid, zero, or negative, the code must fall back to the safe default. If a provider returns empty data or raises an item-level error, existing missing-data diagnostics should still describe the missing item rather than hiding the problem.

Generated run folders and caches created during performance checks are evidence only and must not be committed. If parallel loading causes provider instability, set `PMRI_DISABLE_PARALLEL_DATA_LOAD=1` and rerun the focused tests to isolate whether the issue is concurrency-related.

## Artifacts and Notes

Session 1 validation should show `git diff --check` with no whitespace errors. Session 2 should append concise test and performance transcripts here, including the parallel-enabled timing and the sequential rollback timing.

Session 2 focused test transcript:

    .\.venv\Scripts\python.exe -m pytest tests/test_parallel_data_loading.py tests/test_runtime_memory_caches.py tests/test_factor_matrix_builders.py tests/test_macro_source_resolver.py -q
    34 passed in 5.66s

Session 2 adjacent backend and frontend safety transcripts:

    .\.venv\Scripts\python.exe -m pytest tests/test_macro_indicators.py tests/test_analysis_subject_materialization.py tests/test_blocks_1_5_mvp_smoke.py -q
    25 passed in 14.51s

    cd frontend
    npm.cmd run typecheck
    npm.cmd run test:api
    npm.cmd run test:smoke
    # typecheck passed; test:api passed 24 tests; test:smoke passed 1 test.

Session 2 performance transcript:

    rg --files runs | rg "payload\.json$"
    <no matches>

No parallel-enabled or sequential rollback cold/warm seconds were recorded because the working tree
does not contain a staged diagnosis payload. The next operator should rerun the performance commands
above after creating or restoring a `runs/.../payload.json` file.

Expected successful performance transcript shape:

    cold_seconds=...
    warm_seconds=...
    warm_threshold_seconds=30.000
    status=passed

Expected rollback comparison note shape:

    parallel_enabled_cold_seconds=...
    sequential_rollback_cold_seconds=...
    cold_improvement_pct=...

## Interfaces and Dependencies

Use only Python standard-library concurrency: `concurrent.futures.ThreadPoolExecutor` and `as_completed` or equivalent. Do not add new third-party dependencies.

At the end of Session 2, there should be an internal helper with stable functions equivalent to:

    parallel_data_load_disabled() -> bool
    resolve_data_load_workers(env_name: str, default: int, item_count: int) -> int
    bounded_parallel_map(items, worker_fn, *, env_name: str, default_workers: int) -> list[result]

The exact module path is an implementation detail, but it should live under `src/` and be reused by yfinance, factor, and macro loading rather than duplicating thread-pool boilerplate.

New environment variables must be optional:

- `PMRI_DISABLE_PARALLEL_DATA_LOAD=1` disables all new parallel data loading.
- `PMRI_YF_MAX_WORKERS` controls yfinance ticker concurrency, default 4.
- `PMRI_FACTOR_MAX_WORKERS` controls factor-loader concurrency, default 4.
- `PMRI_MACRO_MAX_WORKERS` controls macro-indicator concurrency, default 3.

## Revision Notes

- 2026-06-15 / Codex: Created the initial two-session plan as a checked-in ExecPlan. Session 1 is intentionally documentation-only; Session 2 implements the runtime behavior.
- 2026-06-15 / Codex: Implemented Session 2 bounded parallel data loading and focused tests. Performance timing remains pending until a staged payload is available.
