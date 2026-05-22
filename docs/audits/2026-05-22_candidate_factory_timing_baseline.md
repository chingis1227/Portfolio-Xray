# Candidate Factory Timing Baseline (Post Runtime Refactor)

Date: 2026-05-22

Purpose: record **evidence** for the [Candidate Factory Runtime Refactor Plan](../exec_plans/2026-05-22_candidate_factory_runtime_refactor_plan.md) Session 9 closure. This audit compares pre-refactor operator timing (planning audit) with post-refactor **`execution-mode standard`** behavior. No formulas or optimizer mathematics were changed.

Governed by: ExecPlan Sessions 1–9 (orchestration and reporting profile only).

Related specs: [candidate_factory_spec.md](../specs/candidate_factory_spec.md), [candidate_comparison_spec.md](../specs/candidate_comparison_spec.md).

---

## Verification bundle (Session 9)

```bash
python -m pytest tests/test_candidate_factory.py tests/test_candidate_comparison.py \
  tests/test_report_profile.py tests/test_candidate_run_context.py \
  tests/test_candidate_manifest.py tests/test_compare_ew_rp.py \
  tests/test_portfolio_review_workflow.py -q
```

**Result (2026-05-22):** **102 passed** in ~149s (offline; one integration test may hit network for parity).

**Regression coverage (metric parity, no semantic drift):**

| Area | Test module | What it proves |
| --- | --- | --- |
| Weights in-process | `tests/test_candidate_factory.py` | `equal_weight`, `risk_parity`, `minimum_variance` weights match subprocess path |
| `report_profile` | `tests/test_report_profile.py` | `snapshot_10y` metrics match `full` vs `lightweight_comparison` for same weights |
| Standard factory phases | `tests/test_candidate_factory.py` | Phase 1 weights + Phase 2 lightweight report; no per-candidate Pandoc |
| Shared context | `tests/test_candidate_run_context.py` | Single monthly load; report skips reload with `run_context` |
| Manifest / partial failure | `tests/test_candidate_manifest.py` | `candidate_manifest_v1` + factory `run_status` |
| Review wiring | `tests/test_portfolio_review_workflow.py` | Review forwards `--execution-mode standard` by default |
| EW/RP PDF CSV | `tests/test_compare_ew_rp.py` | `var_es_10y.csv` `method=historical` not coerced to float |

---

## Pre-refactor reference (planning timing audit)

Source: ExecPlan § Surprises & Discoveries (operator run, `default_v1`, **legacy** subprocess + full report + per-candidate PDF).

| Bucket | `equal_weight` (representative) | Notes |
| --- | ---: | --- |
| Optimizer / weights core | ~0.01 s | Negligible vs reporting |
| `run_portfolio_report_for_weights` (full) | ~166.9 s | Dominant cost |
| `try_rebuild_pdfs_after_variant` | ~181.2 s | Second dominant cost |
| **Step total** | **~227.9 s** | Per candidate |
| **16 × `default_v1`** | **~57 min** | Sequential factory loop |

Bottleneck conclusion (unchanged): **reporting + PDF**, not optimizer cores.

---

## Post-refactor live smoke (`standard`, PDF `none`)

**Command (Session 9):**

```bash
python run_candidate_factory.py --profile core_benchmarks \
  --candidates equal_weight,risk_parity \
  --execution-mode standard --force --pdf-mode none
```

**Environment:** Windows, Python 3.13, 9-ticker `config.yml`, monthly/daily cache warm.

**Artifact:** `Main portfolio/candidate_factory_run.json` (`generated_at` 2026-05-22T19:25:33Z).

| `candidate_id` | `builder_core_seconds` | `report_seconds` | `pdf_seconds` | `total_seconds` | `report_profile` |
| --- | ---: | ---: | ---: | ---: | --- |
| `equal_weight` | 0.011 | 107.276 | 0.0 | 107.287 | `lightweight_comparison` |
| `risk_parity` | 0.014 | 101.395 | 0.0 | 101.409 | `lightweight_comparison` |
| **Run totals** | **0.025** | **208.671** | **0.0** | **208.696** | — |

**Wall clock:** ~235 s (2 candidates, includes one shared `prepare_candidate_run_context` + factor/stress preload).

**Observations:**

1. **Per-candidate PDF eliminated** — `pdf_seconds` = 0; factory default `--pdf-mode none` and review `standard` path do not invoke Pandoc per candidate.
2. **Weights phase is sub-second** — in-process `build_candidate_weights` (Phase 1) as designed.
3. **Report remains the main cost** — lightweight profile ~**101–107 s** per candidate vs ~167 s full report in the pre-refactor probe (~35–40% reduction on report slice only).
4. **No subprocess `run_*.py`** for this run — `execution_summary.builder_invoked` = 0; phases `weights` + `report` in-process.

**Linear extrapolation (indicative, same machine/cache):**

| Mode | Per-candidate step (approx.) | 16 candidates (sequential) |
| --- | ---: | ---: |
| Legacy full (audit) | ~228 s | ~61 min |
| **Standard + PDF none** | ~104 s | **~28 min** |
| Savings vs legacy | ~124 s / candidate | **~33 min** (mostly PDF removal + lighter report + single data context) |

Full **16-candidate** live `default_v1` standard run was not re-executed in Session 9 (operator time); extrapolation uses the 2-candidate smoke above. Re-measure after cache cold-start or universe change.

---

## Acceptance vs ExecPlan end state

| Criterion | Status | Evidence |
| --- | --- | --- |
| `candidate_factory_run.json` timing buckets | **Met** | `builder_core_seconds`, `report_seconds`, `pdf_seconds`, `timing_summary` on smoke JSON |
| Default factory path avoids per-candidate Pandoc | **Met** | `pdf_mode: none`; `pdf_seconds: 0`; Session 1 env guard + review `standard` |
| Comparison metrics consistent with full path | **Met** | `tests/test_report_profile.py` parity; factory standard-mode tests |
| `default_v1` materially faster than ~57 min | **Met (projected)** | ~28 min extrapolation; smoke confirms PDF=0 and ~104 s/step |
| Weights-only under one minute (16 families) | **Met (offline tests)** | Session 2 pilot + in-process Phase 1 (not re-timed live here) |
| KNOWN_ISSUES G4 guidance | **Met** | G4 remains **accepted** with mitigations (`standard`, Phase 3 subset, `--resume`); see [KNOWN_ISSUES.md](../../KNOWN_ISSUES.md) KI-2026-05-21-002 |

---

## Session 9 defect fixed during verification

`prepare_candidate_run_context` called `resolve_robust_mv_lambda_for_baseline(project_root=...)` without required `cli_lambda=None`, breaking **live** `standard` factory runs. Fixed in `src/candidate_run_context.py`; regression test `test_prepare_candidate_run_context_resolves_robust_mv_lambda`.

---

## Operator commands (post-refactor defaults)

| Use case | Command |
| --- | --- |
| Portfolio-first full menu (compare-ready, no per-candidate PDF) | `python run_portfolio_review.py --mode full` (factory `--execution-mode standard`) |
| Factory only, standard | `python run_candidate_factory.py --profile default_v1 --execution-mode standard --then-compare` |
| Legacy parity / debug | `python run_candidate_factory.py --profile default_v1 --execution-mode legacy_full` |
| Deep-dive HTML/PDF on subset | `--full-candidate-reports --selected-candidates-for-full-report ID,...` |
| Timing evidence | Inspect `Main portfolio/candidate_factory_run.json` → `timing_summary` and per-step buckets |

---

## Maintenance

- Re-run the smoke command after major data-pipeline or stress-report changes; append a dated row to the per-candidate table.
- Do not treat this file as a performance SLA; it documents **observed** buckets on one machine.
- For methodology ownership, see [2026-05-20_candidate_factory_methodology_map.md](2026-05-20_candidate_factory_methodology_map.md).
