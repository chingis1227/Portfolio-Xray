# Candidate Factory Runtime Refactor

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows [PLANS.md](../../PLANS.md) in the repository root.

**Status:** Completed (Sessions 0–9 closed 2026-05-22).

**Constraint (non-negotiable):** orchestration and runtime only. Do not change financial formulas,
optimizer mathematics, stress scenario definitions, metric estimators, or candidate weight semantics.
Generated artifacts are evidence, not source of truth.

---

## Purpose / Big Picture

A timing audit showed that **optimizer cores are sub-second** while a full `default_v1` factory run
(16 candidates) takes **~57 minutes** because each `run_*.py` builder invokes the full
`run_portfolio_report_for_weights` pipeline and often **`try_rebuild_pdfs_after_variant`** (~167s
report probe, ~181s PDF per candidate).

After this refactor, an operator (or web backend) can run
`python run_candidate_factory.py --profile default_v1` in **standard** mode and get comparison-ready
results in minutes: weights plus lightweight snapshots, **one** comparison pass, **no** per-candidate
Pandoc. Full HTML, PNG, commentary, and PDF remain available only when explicitly requested.
Standalone `run_equal_weight.py` and sibling scripts keep today's default full behavior.

Proof: `candidate_factory_run.json` lists `builder_core_seconds`, `report_seconds`, and `pdf_seconds`
per step; default factory runs do not call Pandoc per candidate; `candidate_comparison.json` metrics
match the full-report path for the same weights (regression tests in Session 9).

---

## Progress

- [x] (2026-05-22) Timing audit analyzed; bottleneck confirmed as reporting/PDF, not optimizers.
- [x] (2026-05-22) ExecPlan drafted and reviewed in planning chat.
- [x] (2026-05-22) **Session 0:** Checked in this ExecPlan; set Active in [docs/exec_plans/README.md](README.md).
- [x] (2026-05-22) **Session 1:** PDF guard in factory + timing fields in `candidate_factory_run.json`.
- [x] (2026-05-22) **Session 2:** `build_candidate_weights` API + factory weights-only Phase 1.
- [x] (2026-05-22) **Session 3:** `report_profile` = `lightweight_comparison` in `run_portfolio_report_for_weights`.
- [x] (2026-05-22) **Session 4:** `CandidateRunContext` shared data/factor cache.
- [x] (2026-05-22) **Session 5:** Per-candidate `candidate_manifest.json` + partial failure statuses.
- [x] (2026-05-22) **Session 6:** Wire `standard` mode through `run_portfolio_review.py` + factory phases.
- [x] (2026-05-22) **Session 7:** Fix `run_compare_ew_rp.py` `historical` float PDF bug + test.
- [x] (2026-05-22) **Session 8:** `--full-candidate-reports` / selected export + doc closure.
- [x] (2026-05-22) **Session 9:** Full verification + timing baseline audit + retrospective.

---

## Surprises & Discoveries

- Observation: Optimizer time is negligible versus one full report call.
  Evidence: Timing audit — `equal_weight` optimizer core ~0.01s vs ~227.9s total step;
  `run_portfolio_report_for_weights` probe ~166.9s; successful Pandoc rebuild ~181.2s.

- Observation: Live `standard` smoke (Session 9) confirms PDF=0 and ~104s/report per candidate;
  `prepare_candidate_run_context` initially omitted `cli_lambda=None` and blocked live standard runs.
  Evidence: [2026-05-22_candidate_factory_timing_baseline.md](../audits/2026-05-22_candidate_factory_timing_baseline.md);
  fix in `src/candidate_run_context.py`; pytest bundle **102 passed**.

---

## Decision Log

- Decision: Default factory PDF mode will be `none`; standalone `run_*.py` unchanged unless the
  factory sets an environment variable.
  Rationale: Removes ~181s×N without touching formulas; lowest-risk first step (Session 1).
  Date/Author: 2026-05-22 / planning agent.

- Decision: `lightweight_comparison` must still emit real `snapshot_10y.json` and `stress_report.json`
  via the same report builders, not a parallel metric schema.
  Rationale: `src/candidate_comparison.py` contract; avoids semantic drift.
  Date/Author: 2026-05-22 / planning agent.

- Decision: Prefer extending [candidate_factory_spec.md](../specs/candidate_factory_spec.md) over a
  new `candidate_factory_runtime_spec.md` unless duplication becomes painful.
  Rationale: Single orchestration spec already exists (Session 0).
  Date/Author: 2026-05-22 / Session 0.

- Decision: In `standard` mode, stop subprocessing 16 full `run_*.py` scripts once Sessions 2–3 land.
  Rationale: Eliminates duplicate `load_monthly_data_shared` and process overhead.
  Date/Author: 2026-05-22 / planning agent.

---

## Outcomes & Retrospective

Session 0 delivered documentation only. Session 1 shipped `--pdf-mode` (default `none`),
`PORTFOLIO_SKIP_VARIANT_PDF` gating in all factory-backed `run_*.py` scripts, `builder_runtime_timing.json`
support (instrumented on `run_equal_weight.py`; other builders emit timing when extended), and
`timing_summary` on `candidate_factory_run.json`. Verified with `tests/test_candidate_factory.py`
(new PDF/timing tests). Full 16-candidate live timing baseline deferred to Session 9.

Session 2 shipped `src/candidate_weights.py`, factory `--execution-mode fast|standard` (Phase 1
weights in-process; default `legacy_full` unchanged), `candidate_weights_build.json` freshness for
skip-existing, and pilot parity tests (`equal_weight`, `risk_parity`, `minimum_variance`).

Session 3 shipped `src/report_profile.py`, `report_profile` on
`run_portfolio_report_for_weights`, factory Phase 2 for `--execution-mode standard`
(`_execute_lightweight_report`), skip-existing on fresh `snapshot_10y.json`, and pytest parity
(`tests/test_report_profile.py`, factory standard-mode test). Verified:
`python -m pytest tests/test_report_profile.py tests/test_candidate_factory.py -q` (40 passed).

Session 4 shipped `src/candidate_run_context.py` (`CandidateRunContext`,
`FactoryFactorStressInputs`, `prepare_candidate_run_context`), factory threads `run_context` into
Phase 1 weights and Phase 2 lightweight report, `run_portfolio_report_for_weights(..., run_context=...)`
reuses monthly data and factor/scenario cache, invariant vs candidate-dependent table in
`candidate_factory_spec.md`, and tests in `tests/test_candidate_run_context.py`.

Session 5 shipped `src/candidate_manifest.py` (`candidate_manifest_v1` per `{artifact_root}/`,
`comparison_readiness`, optional `partial_failure`), factory `run_status` on
`candidate_factory_run.json`, `_persist_manifest_step` writes manifests after each step,
`fail_fast_aborted` disclosure, spec/OUTPUTS updates, golden fixture regen, and
`tests/test_candidate_manifest.py` (48 factory-related tests passed).

Session 6 shipped `resolve_factory_execution_mode` / `REVIEW_DEFAULT_FACTORY_EXECUTION_MODE`
(`standard`) in `src/portfolio_review_workflow.py`; `run_portfolio_review.py --execution-mode`
override; factory argv always includes `--execution-mode` from review; specs/runbook/CHANGELOG
updated; `tests/test_portfolio_review_workflow.py` extended (dry-run argv checks).

Session 7 shipped `_read_var_es_metrics_csv` in `run_compare_ew_rp.py` so `var_es_10y.csv` metadata
(`method` = `historical`, `frequency`, etc.) is not coerced to float during EW/RP compare or PDF
rebuild; `tests/test_compare_ew_rp.py` locks the contract.

Session 8 shipped Phase 3 full report export: `--full-candidate-reports`,
`--selected-candidates-for-full-report`, `_execute_full_report` / `_run_full_candidate_reports_phase`,
`final_only` PDF rebuild step, KNOWN_ISSUES G4 guidance, README/PRODUCT/ARCHITECTURE/runbook/spec
updates; `tests/test_candidate_factory.py` (+4 tests, 40 passed).

Session 9 closed verification and timing baseline: pytest bundle **102 passed** (factory,
comparison, report_profile, run_context, manifest, compare_ew_rp, review workflow); live smoke
`core_benchmarks` × 2 candidates in `standard` + `pdf_mode none` (~209s report total, 0 PDF);
audit [2026-05-22_candidate_factory_timing_baseline.md](../audits/2026-05-22_candidate_factory_timing_baseline.md);
bugfix `cli_lambda=None` in `prepare_candidate_run_context`; plan marked **Completed** in register.

**Retrospective:** Primary win is removing per-candidate Pandoc and subprocess overhead while keeping
compare-ready `snapshot_10y.json` / `stress_report.json` via `lightweight_comparison`. Residual cost
is stress/report CPU (~100s/candidate on warm cache). Full 16-candidate live re-benchmark optional;
extrapolation ~28 min vs ~57 min legacy. G4 stays accepted with operator mitigations.

---

## Context and Orientation

**Candidate Portfolio Factory** orchestrates existing per-candidate `run_*.py` scripts via
`src/candidate_factory.py` and `run_candidate_factory.py`. Each script typically:

1. Loads monthly data (`load_monthly_data_shared`).
2. Builds weights (`src/portfolio_variants`).
3. Runs `run_portfolio_report_for_weights` (metrics, stress, snapshots, CSV, commentary).
4. Calls `try_rebuild_pdfs_after_variant` (EW/RP compare + variant PDF suite).

**Comparison** (`src/candidate_comparison.py`, `run_compare_variants.py`) is read-only aggregation.
It requires `{artifact_root}/snapshot_10y.json` for a non-degraded row (summary-only fallback is
degraded). Stress fields come from snapshot `stress_suite_results` and/or `stress_report.json`.

**Portfolio-first review** (`src/portfolio_review_workflow.py`) already supports `--skip-pdf` for
the final rebuild step; factory subprocesses do not inherit that today.

**Known issue to close:** [KNOWN_ISSUES.md](../../KNOWN_ISSUES.md) — full `default_v1` factory refresh
is operationally heavy (G4 / P17-G11).

Key paths (repository root):

| Path | Role |
| --- | --- |
| `src/candidate_factory.py` | Factory orchestration, profiles, subprocess chain |
| `run_candidate_factory.py` | CLI |
| `run_equal_weight.py` (and 15 siblings) | Per-family builder + full report + PDF |
| `run_report.py` | `run_portfolio_report_for_weights` |
| `src/candidate_comparison.py` | Comparison contract |
| `run_portfolio_review.py` | Review wrapper |

Owning specs: [candidate_factory_spec.md](../specs/candidate_factory_spec.md),
[candidate_comparison_spec.md](../specs/candidate_comparison_spec.md),
[candidate_factory_layer_spec.md](../specs/candidate_factory_layer_spec.md).

---

## Target execution model

```text
prepare_context()
  -> build_all_candidate_weights(context)
  -> write candidate weights + per-candidate manifests
  -> generate_lightweight_candidate_artifacts(context, candidates)   # standard mode
  -> run_comparison_once()
  -> optionally generate_full_reports(selected candidates)
  -> optionally rebuild_pdf_once()
```

**Execution modes (product-facing):**

| Mode | Weights | Report profile | Per-candidate PDF | Compare | Typical use |
| --- | --- | --- | --- | --- | --- |
| `fast` | yes | `none` | no | optional | API / first response |
| `standard` (new factory default) | yes | `lightweight_comparison` | no | yes | Default factory + review full menu |
| `full` | yes | `full` | no | yes | Deep-dive all candidates |
| `legacy_full` | existing `run_*.py` subprocess | full | per_candidate (today) | yes | Debug / parity |

---

## Roadmap phases

| Phase | Outcome | Sessions |
| --- | --- | --- |
| A — Observability + PDF guard | Timing buckets; no Pandoc in factory loop | 1 |
| B — Phased factory API | Weights without full report | 2, 6 |
| C — Lightweight report | Compare-ready without HTML/PNG/PDF | 3, 6 |
| D — Shared context | One data load per factory run | 4 |
| E — Manifest + partial failure | Per-candidate readiness JSON | 5 |
| F — PDF reliability | `historical` categorical parse fix | 7 |
| G — Verification + docs | Tests, timing audit, closure | 8, 9 |

---

## Documentation readiness

**Read first in any session:** [PLANS.md](../../PLANS.md), [AGENTS.md](../../AGENTS.md),
[WORKFLOW.md](../../WORKFLOW.md), [TESTING.md](../../TESTING.md), factory/comparison specs,
[docs/audits/2026-05-20_candidate_factory_methodology_map.md](../audits/2026-05-20_candidate_factory_methodology_map.md),
[OUTPUTS.md](../../OUTPUTS.md), [KNOWN_ISSUES.md](../../KNOWN_ISSUES.md).

**Update during implementation:**

| Gap | Action | Session |
| --- | --- | --- |
| Phased factory contract | § Runtime modes in `candidate_factory_spec.md` | 1+ |
| Layer spec workflow diagram | `candidate_factory_layer_spec.md` | 3–4 |
| `report_profile` artifact set | `reporting_outputs_spec.md` or run_report note | 3 |
| Per-candidate `candidate_manifest.json` | `OUTPUTS.md` | 5 |
| ARCHITECTURE phased factory | `ARCHITECTURE.md` | 4, 8 |
| README CLI flags | `README.md` | 1, 8 |
| PRODUCT modes | `PRODUCT.md` | 8 |
| Post-refactor timing baseline | `docs/audits/2026-05-22_candidate_factory_timing_baseline.md` | 9 |
| PDF `historical` bug | `KNOWN_ISSUES.md` until fixed | 7 |

---

## Work sessions (one chat each)

Start a **new chat** at each boundary. Carry this file path and the prior session `Progress` /
`Decision Log` updates.

### Session 0 — ExecPlan bootstrap (complete)

**Goal:** Checked-in ExecPlan + register pointer; no runtime behavior change.

**Done when:** Plan file exists under `docs/exec_plans/` and register marks Active.

---

### Session 1 — Timing schema + disable per-candidate PDF in factory

**Goal:** Immediate runtime win without splitting weights/report yet.

**Tasks:**

1. Add `--pdf-mode {none,final_only,per_candidate}` to `run_candidate_factory.py`; default `none`.
2. Factory subprocess: set env (e.g. `PORTFOLIO_SKIP_VARIANT_PDF=1`) when PDF mode is not
   `per_candidate`.
3. Gate `try_rebuild_pdfs_after_variant` in each `run_*.py` (and robust report script) on env;
   standalone runs unchanged when env unset.
4. Extend `candidate_factory_run_v1` step fields: `builder_core_seconds`, `report_seconds`,
   `pdf_seconds`, `total_seconds`; run-level `timing_summary` in JSON and `.txt`.
5. Tests in `tests/test_candidate_factory.py`; update `candidate_factory_spec.md` and `CHANGELOG.md`.

**Files:** `src/candidate_factory.py`, `run_candidate_factory.py`, `run_*.py`, tests, spec.

**Done when:** pytest factory tests pass; 2–3 candidate `--force` run shows no per-candidate Pandoc.

**Prompt for next chat:**

    Implement Session 1 of docs/exec_plans/2026-05-22_candidate_factory_runtime_refactor_plan.md only:
    - default factory pdf_mode=none via env/CLI
    - extend candidate_factory_run.json timing fields
    - tests + candidate_factory_spec + CHANGELOG
    Do not start weights-only or report_profile yet.

---

### Session 2 — Weights-only API + factory Phase 1

**Goal:** All 16 candidate weights in seconds; factory does not require full `run_*.py` for weights.

**Tasks:** `build_candidate_weights` / `write_candidate_weights`; pilot then roll all families;
factory Phase 1 in fast/standard; keep `legacy_full` subprocess path.

**Done when:** Weights-only &lt;2 min offline; weights JSON match pre-refactor for 3 pilot IDs.

---

### Session 3 — `report_profile` + lightweight comparison path

**Goal:** Comparison-ready artifacts without HTML/PNG/full commentary.

**Tasks:** `report_profile` on `run_portfolio_report_for_weights`; factory Phase 2; comparison rows
`available` not `degraded`.

**Done when:** `snapshot_10y` metrics match full profile for 2–3 candidates (pytest).

---

### Session 4 — Shared `CandidateRunContext`

**Goal:** Single `load_monthly_data_shared` + reused factor/scenario inputs per factory run.

**Tasks:** `src/candidate_run_context.py`; thread into builders and report; invariant vs
candidate-dependent table in spec.

---

### Session 5 — Per-candidate `candidate_manifest.json` + partial failure

**Goal:** Machine-readable readiness; one failure does not kill the run unless `--fail-fast`.

---

### Session 6 — Review workflow + standard mode wiring

**Goal:** `run_portfolio_review.py --mode full` uses phased factory by default.

---

### Session 7 — PDF `historical` float bug (parallel track)

**Goal:** `run_compare_ew_rp.py` does not raise `ValueError` on categorical `historical` during PDF rebuild.

---

### Session 8 — Full report export for selected candidates + docs

**Goal:** `--full-candidate-reports`, `--selected-candidates-for-full-report`, close KNOWN_ISSUES G4 guidance.

---

### Session 9 — Verification + timing audit + retrospective

**Goal:** Prove refactor; write `docs/audits/2026-05-22_candidate_factory_timing_baseline.md`; mark plan Completed in register.

**Smoke commands:**

    python -m pytest tests/test_candidate_factory.py tests/test_candidate_comparison.py -q
    python run_candidate_factory.py --profile default_v1 --then-compare
    python run_candidate_factory.py --profile core_benchmarks --candidates equal_weight,risk_parity

---

## Plan of Work

Session 0 added only this plan and register pointer. Sessions 1–9 follow the session blocks above in
order; Session 7 may run in parallel after Session 1. Do not change formulas or optimizer outputs in
any session.

---

## Concrete Steps

**Session 0 (completed):**

    # From repository root — verify plan file exists
    dir docs\exec_plans\2026-05-22_candidate_factory_runtime_refactor_plan.md
    # Read register Active pointer
    type docs\exec_plans\README.md

**Session 1 (next):** implement per Session 1 block; run factory tests before any full 16-candidate live run.

---

## Validation and Acceptance

**Session 0:** `docs/exec_plans/2026-05-22_candidate_factory_runtime_refactor_plan.md` exists;
`docs/exec_plans/README.md` Current Pointer names this plan as **Active**; no Python behavior change.

**End state (Session 9):** `default_v1` standard mode materially faster than ~57 minutes; weights-only
under one minute; comparison JSON metric-consistent with full path; KNOWN_ISSUES G4 updated or closed.

---

## Idempotence and Recovery

Re-running Session 0 doc steps is safe. Factory `--resume` and manifest behavior from the prior
post-audit plan remain valid during this refactor until explicitly superseded in spec (Session 5+).

If a session fails mid-way, update `Progress` with completed vs remaining, commit doc/code for the
finished slice, and resume in a new chat from the next session number.

---

## Related audits and plans

- Prior factory governance: [2026-05-20_candidate_factory_post_audit_roadmap.md](2026-05-20_candidate_factory_post_audit_roadmap.md) (Completed).
- Methodology map: [docs/audits/2026-05-20_candidate_factory_methodology_map.md](../audits/2026-05-20_candidate_factory_methodology_map.md).
- Timing baseline (to create): `docs/audits/2026-05-22_candidate_factory_timing_baseline.md` (Session 9).
