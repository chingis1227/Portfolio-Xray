# Candidate Portfolio Factory Post-Audit Roadmap (Block 4)

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan must be maintained in accordance with [PLANS.md](../../PLANS.md).

## Purpose / Big Picture

Block 4 already builds 16 alternative portfolios and merges them into `candidate_comparison.json`, but operators cannot always trust **why** a step failed, **whether** artifacts match the current config, or **what parameters** defined each hypothesis in the comparison JSON alone.

After Sessions 00–11, the factory layer should be **audit-grade**: explicit failure reasons, config-aware freshness, construction disclosure in comparison, layer spec for handoff, resumable long runs (RM-921 via Session 09), and a regression bundle—without changing the diagnostic-only product boundary.

After Session 00, a new agent should resume from:

- [Candidate Factory Methodology Map](../audits/2026-05-20_candidate_factory_methodology_map.md)
- [Candidate Factory Baseline Snapshot](../audits/2026-05-20_candidate_factory_baseline_snapshot.md)
- this ExecPlan
- [candidate_factory_spec.md](../specs/candidate_factory_spec.md), [candidate_comparison_spec.md](../specs/candidate_comparison_spec.md), [candidate_portfolios_spec.md](../specs/candidate_portfolios_spec.md)

**Non-goals:** UI/workspace, new `candidate_id` rows, new optimizer formulas, mandate/selection logic changes, silent spec changes.

**Chat rule:** one session = one new chat (unless the user explicitly requests a tiny follow-up in the same thread).

## Progress

- [x] (2026-05-20) Session 00 (`RM-970`): ExecPlan persisted; registers and ROADMAP Phase 14; baseline snapshot; TESTING governance bundle stub; `verify_docs` passed.
- [x] (2026-05-20) Session 01 (`RM-971`): Documentation sync.
- [x] (2026-05-20) Session 02 (`RM-972`): Factory builder failure reason propagation (P1 / G1).
- [x] (2026-05-20) Session 03 (`RM-973`): Freshness hardening when review date missing (G3).
- [x] (2026-05-20) Session 04 (`RM-974`): Construction disclosure in comparison (P3 / G6).
- [x] (2026-05-20) Session 05 (`RM-975`): `candidate_factory_layer_spec.md`.
- [x] (2026-05-20) Session 06 (`RM-976`): Config fingerprint freshness (P2 / G2).
- [x] (2026-05-20) Session 07 (`RM-977`): Robust paths disclosure (G8, G10).
- [x] (2026-05-20) Session 08 (`RM-978`): Golden contract tests + TESTING bundle finalize.
- [x] (2026-05-20) Session 09 (`RM-979`): Resumable factory (P4 / RM-921).
- [x] (2026-05-20) Session 10 (`RM-980`): Operational runbook and factory run UX.
- [x] (2026-05-20) Session 11 (`RM-981`): Concept registry decisions and wave closure (P5).

## Surprises & Discoveries

- Observation: No committed `Main portfolio/candidate_factory_run.json` or `candidate_comparison.json` in the workspace at Session 00; baseline snapshot records **contract checklist** and defers SHA256 fingerprints until a representative portfolio-first run.
  Evidence: repository glob search during Session 00.

- Observation: RM-921 (resumable factory) was listed as deferred in ROADMAP until this wave; Session 09 will implement it inside Phase 14 per user decision.
  Evidence: [ROADMAP.md](../ROADMAP.md) prior to Session 00.

## Decision Log

- Decision: Include RM-921 resumable factory as Session 09 in this wave (user choice).
  Rationale: Long `default_v1` runs need resume without redoing succeeded steps.
  Date/Author: 2026-05-20 / Agent.

- Decision: One chat = one session; Session 00 is documentation-only (no production code).
  Rationale: Governance wave must record methodology before altering factory/comparison behavior.
  Date/Author: 2026-05-20 / Agent.

- Decision: No new candidate types or UI in Phase 14.
  Rationale: Methodology map P5 and product concept drift must be spec/DEC only.
  Date/Author: 2026-05-20 / Agent.

- Decision: Map known builder `FAIL_*` statuses to dedicated `builder_*` factory `reason_code` values; unknown `FAIL_*` → `builder_failed`; keep `subprocess_failed` / `missing_snapshot_after_build` when `summary.json` absent or non-FAIL.
  Rationale: P1 / G1 audit trail without changing builder scripts.
  Date/Author: 2026-05-20 / Agent (Session 02).

- Decision: When review `analysis_end` is unknown (`freshness_status: unchecked`), rebuild instead of `skipped_existing`; comparison emits per-row unchecked warning but may still load metrics.
  Rationale: G3 — no silent reuse without certified review date.
  Date/Author: 2026-05-20 / Agent (Session 03).

- Decision: `construction_disclosure` copies existing JSON only (`baseline_metadata` full passthrough; `partial` when only `summary.json` or factory step); no recomputation in comparison builder.
  Rationale: P3 / G6 fair-hypothesis visibility without changing diagnostic boundary.
  Date/Author: 2026-05-20 / Agent (Session 04).

- Decision: Config fingerprint hashes investor currency, sorted tickers, `risk_budgeting`, and min/max single-security bounds only; missing snapshot fingerprint with matching `analysis_end` is `stale_config` (rebuild), not `fresh`.
  Rationale: P2 / G2 — same month-end after config change must not reuse candidate folders silently.
  Date/Author: 2026-05-20 / Agent (Session 06).

- Decision: Robust disclosure is passthrough/metadata only (`robust_paths_disclosure` / `construction_disclosure.robust_paths`); factory does not run λ calibration; `robust_scenario` prerequisites stay on Main `output_dir_final`.
  Rationale: G8/G10 audit trail without changing diagnostic boundary or builder scripts.
  Date/Author: 2026-05-20 / Agent (Session 07).

- Decision: Golden contract tests use structural fingerprints plus committed JSON fixtures; `candidate_factory_golden_inputs.py` normalizes timestamps/paths and uses a snapshot-writing test runner (no network).
  Rationale: RM-978 regression bundle without live Main portfolio artifacts in-repo.
  Date/Author: 2026-05-20 / Agent (Session 08).

- Decision: Resume manifest `run_checksum` binds profile id, ordered candidate ids, `analysis_end`, and `config_fingerprint`; only `succeeded` and fresh `skipped_existing` are skipped on `--resume`; manifest written after each step.
  Rationale: P4 / RM-921 — interrupted `default_v1` runs must not redo succeeded builders; checksum mismatch runs full menu with warning.
  Date/Author: 2026-05-20 / Agent (Session 09).

- Decision: Operator recovery lives in `docs/operational_runbook.md` §8; factory `next_recommended_command` and `.txt` summarize failed `reason_code` values and suggest `--resume` when `summary.failed > 0`.
  Rationale: RM-980 — audit-grade operator UX without changing diagnostic boundary.
  Date/Author: 2026-05-20 / Agent (Session 10).

- Decision: Concept-only product names (Max Sharpe, tactical tilt menu, custom constraints, etc.) stay **out of** `_REGISTRY_ROWS` until a future spec+DEC; statuses documented in `candidate_portfolios_spec.md` appendix and **DEC-2026-05-20-003**.
  Rationale: P5 / G9 — prevent concept drift from being read as missing implementations.
  Date/Author: 2026-05-20 / Agent (Session 11).

## Outcomes & Retrospective

Session 00 outcome: methodology map already in repo; this ExecPlan registered **Active**; Phase 14 (`RM-970`–`RM-981`) added to ROADMAP; baseline snapshot created with contract checklist; TESTING.md stub added.

Session 01 outcome: `CHANGELOG`, `KNOWN_ISSUES` (G1–G10 index + KI-2026-05-20-001–008), `SPEC.md`, and `OUTPUTS.md` synced to methodology map and Phase 14 RM rows; `RM-971` Done in ROADMAP.

Session 02 outcome: `src/candidate_factory.py` maps builder `summary.json` `FAIL_*` to `builder_*` factory `reason_code` values; optional `builder_status` / `builder_reason` on failed steps; spec + tests updated; G1 / `KI-2026-05-20-001` closed; `RM-972` Done.

Session 03 outcome: unchecked freshness no longer emits `skipped_existing`; factory rebuilds with `unchecked_candidate_snapshot_rebuild_attempted` warning; comparison warns `candidate_freshness_unchecked_no_review_analysis_end:{candidate_id}` when review date unknown; G3 / `KI-2026-05-20-003` closed; `RM-973` Done.

Session 04 outcome: `construction_disclosure` on every comparison row (passthrough from `baseline_weights_metadata.json`, `summary.json`, Main/sidecar excerpts, factory step); spec v1.3 + tests; G6 / `KI-2026-05-20-004` closed; `RM-974` Done.

Session 05 outcome: [candidate_factory_layer_spec.md](../specs/candidate_factory_layer_spec.md) promoted from scaffold to active Block 4.1–4.9 handoff (workflow, contracts, sub-block map, gaps G7 closed); SPEC/OUTPUTS/README/KNOWN_ISSUES/ROADMAP synced; `RM-975` Done.

Session 06 outcome: `compute_candidate_config_fingerprint` in `src/snapshot.py`; stamped on window snapshots in `run_portfolio_report_for_weights`; factory `stale_config` rebuild + `stale_config_fingerprint_after_build`; comparison `stale_config_fingerprint` gate; specs/tests/docs synced; G2 / `KI-2026-05-20-002` closed; `RM-976` Done.

Session 07 outcome: `src/candidate_robust_disclosure.py`; factory `robust_paths_disclosure` on robust MV and `robust_scenario` steps; comparison `construction_disclosure.robust_paths`; operational runbook robust suite section; specs updated; G8/G10 and `KI-2026-05-20-005`/`006` closed; `RM-977` Done.

Session 08 outcome: golden fixtures `tests/fixtures/candidate_factory_run_golden_v1.json` and `candidate_comparison_golden_v1.json`; `tests/candidate_factory_golden_inputs.py`; `tests/test_candidate_factory_contract.py` and `tests/test_candidate_comparison_contract.py`; TESTING.md Phase 14 bundle finalized (71 passed); `RM-978` Done.

Session 09 outcome: `candidate_factory_manifest.json` (`candidate_factory_manifest_v1`); `run_candidate_factory.py --resume`; incremental manifest per step; factory run documents `manifest` block and `resumed_from_manifest` summary; specs/runbook/OUTPUTS synced; G5 closed; RM-921 resumable scope and `RM-979` Done.

Session 10 outcome: [operational_runbook.md](../operational_runbook.md) §8 (exit codes, reason-code table, scenario playbooks); `compute_next_recommended_command` and richer `candidate_factory_run.txt` (failed `reason_code` lines, CLI exit hint); specs/layer spec synced; G4 operator playbook closed; `RM-980` Done.

Session 11 outcome: **DEC-2026-05-20-003** and [candidate_portfolios_spec.md](../specs/candidate_portfolios_spec.md) § Concept candidates not in registry; G9 / `KI-2026-05-20-007` closed; baseline snapshot Phase 14 closure section; governance bundle + `verify_docs` passed; Phase 14 (`RM-970`–`RM-981`) **Done**; ExecPlan **Completed**.

## Context and Orientation

Candidate Portfolio Factory orchestration lives in `src/candidate_factory.py` and `run_candidate_factory.py`. Comparison aggregation is read-only in `src/candidate_comparison.py`. Weight construction is centralized in `src/portfolio_variants.py` via per-family `run_*.py` scripts.

Portfolio-first entry: `run_portfolio_review.py` → materialize `analysis_subject` → factory (`core_v1` or `default_v1`) → optional `--then-compare` → decision package artifacts.

Prerequisite waves (do not redo): RM-902 freshness, RM-920 core/full modes, RM-922 partial menu, factory CLI (Session 11 post-audit).

## Plan of Work

Work proceeds one session per chat, in strict order Sessions 00–11. See session sections in the methodology map audit and the Phase 14 table in [ROADMAP.md](../ROADMAP.md).

### Session 00 — Project memory (completed)

Goal: any agent can resume Block 4 from repo files only.

Tasks: ExecPlan; registers; ROADMAP Phase 14; baseline snapshot; TESTING stub; `verify_docs`.

### Session 01 — Documentation sync (`RM-971`) (completed)

Goal: CHANGELOG, KNOWN_ISSUES, SPEC/OUTPUTS links reflect audit gaps G1–G10 mapped to RM rows.

Tasks (done): gap index table; eight `KNOWN_ISSUES` entries; SPEC/OUTPUTS methodology and layer-spec links; `RM-971` Done; `python scripts/verify_docs.py`.

### Session 02 — Builder failure reasons (`RM-972`, G1)

Goal: `candidate_factory_run.json` maps builder `summary.json` FAIL_* to explicit `reason_code` values.

### Session 03 — Freshness unchecked (`RM-973`, G3)

Goal: no silent `skipped_existing` when review `analysis_end` is unknown.

### Session 04 — Construction disclosure (`RM-974`, G6)

Goal: `construction_disclosure` on comparison rows from existing metadata files.

### Session 05 — Layer spec (`RM-975`)

Goal: `docs/specs/candidate_factory_layer_spec.md` (Block 4.1–4.9 handoff).

### Session 06 — Config fingerprint (`RM-976`, G2)

Goal: freshness beyond `analysis_end` only.

### Session 07 — Robust disclosure (`RM-977`, G8, G10)

Goal: λ source and Main-folder robust_scenario prerequisites documented in runbook/spec.

### Session 08 — Golden tests (`RM-978`)

Goal: fixtures + finalized governance pytest bundle in TESTING.md.

### Session 09 — Resumable factory (`RM-979`, RM-921)

Goal: `--resume` + manifest; mark RM-921 Done.

### Session 10 — Runbook (`RM-980`)

Goal: operator playbook for factory exit codes and reason codes.

### Session 11 — Wave closure (`RM-981`, P5)

Goal: DEC for concept-only candidates; baseline refresh; Phase 14 closed.

## Concrete Steps (Session 00)

```bash
python scripts/verify_docs.py
python -m pytest tests/test_candidate_factory.py tests/test_candidate_comparison.py tests/test_portfolio_review_workflow.py -q
```

## Concrete Steps (Session 01)

```bash
python scripts/verify_docs.py
```

Optional (capture baseline fingerprints when network/data available):

```bash
python run_portfolio_review.py --mode core
# Then update docs/audits/2026-05-20_candidate_factory_baseline_snapshot.md fingerprints section.
```

## Verification checklist (wave closure)

```bash
python -m pytest tests/test_candidate_factory.py tests/test_candidate_comparison.py tests/test_portfolio_review_workflow.py -q
python -m pytest tests/test_equal_weight_baselines.py tests/test_risk_parity_baseline.py tests/test_risk_budgeting.py -q
python scripts/verify_docs.py
# After Session 08, add contract/golden modules per TESTING.md Candidate Factory Governance Wave Bundle.
```

Revision note, 2026-05-20: Completed Session 11 (`RM-981`) — DEC-2026-05-20-003 concept registry appendix;
governance bundle 77 passed + family spot-check 19 passed; `verify_docs` OK; baseline snapshot Phase 14
closure; ROADMAP Phase 14 Done; plan **Completed**.
