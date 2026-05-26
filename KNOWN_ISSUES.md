# KNOWN_ISSUES.md

This file is the living register of known active issues, bugs, weak spots, model limitations, testing gaps, and technical debt for Portfolio X-Ray & Optimization Terminal / Portfolio MRI.

It is not a roadmap, product concept, or technical specification. It does not override `SPEC.md`, `DATA.md`, `TESTING.md`, `RULES.md`, or `docs/specs/*.md`.

## Purpose

- Keep known risks visible until they are fixed or intentionally accepted.
- Prevent agents and developers from rediscovering the same problem repeatedly.
- Separate active issues from future product ideas and target/TBD modules.
- Make model limitations and quality gaps explicit before they affect decisions.

## What Belongs Here

- Confirmed bugs or likely behavioral defects.
- Model risks and assumption limitations.
- Data quality risks and fragile fallback behavior.
- Testing gaps and missing regression coverage.
- Documentation debt that can mislead implementation or users.
- Technical debt that increases maintenance or correctness risk.

## What Does Not Belong Here

- Long formulas or implementation details; put those in the owning spec.
- Pure roadmap ideas; keep those in `PRODUCT.md`, `BUSINESS_VISION.md`, or an ExecPlan when work starts.
- Generated-output diffs unless the generated artifact itself is the problem.
- Resolved issues that no longer affect the current project state.

## Lifecycle

1. Add an issue when a real risk, bug, limitation, or quality gap is discovered and not fixed immediately.
2. Keep active issues short, specific, and linked to the affected source of truth.
3. When an issue is fixed, verified, and documented, remove it from the active list.
4. If the fix needs audit history, record it in the relevant commit, PR, [CHANGELOG.md](CHANGELOG.md), or ExecPlan instead of keeping stale active issues here.
5. If an issue is intentionally accepted, mark it as `accepted` and explain the boundary and mitigation.

## Entry Format

Use this format for new entries:

```markdown
Issue ID: KI-YYYY-MM-DD-NNN
Title: Short title

- Status: open | planned | in_progress | blocked | accepted
- Severity: low | medium | high | critical
- Area: data | metrics | optimizer | stress | factor_macro | reports | config | docs | testing | architecture
- Risk: What can go wrong if this stays unresolved.
- Evidence: Where the issue is observed or why it is believed to exist.
- Current mitigation: What reduces the risk today, if anything.
- Next action: The smallest practical next step.
- Source links: Relevant docs, specs, code, tests, or outputs.
- Remove when: Concrete condition for deleting this active issue.
```

## Active Issues

### Full pytest suite contract drift index (2026-05-26)

Recorded after `python -m pytest` on the Block 2.4 closure path: **1037 passed**, **6 failed**, **2 skipped**
(live E2E markers). Failures are **pre-existing contract drift / tech debt**, not regressions from
`src/block_2_4_hidden_exposure.py`. Do not treat a green Block 2.4 focused run as proof of full-suite green
until these rows are closed or explicitly re-accepted.

| ID | Failing test | Drift summary | Owning area |
| --- | --- | --- | --- |
| KI-2026-05-26-001 | `tests/test_candidate_comparison.py::test_current_unavailable_in_optimize_mode` | `current` row `status` is `degraded`; test expects `unavailable` + `missing_current_report` | candidate comparison |
| KI-2026-05-26-002 | `tests/test_candidate_factory_contract.py::test_live_factory_build_matches_golden_document` | `factory_contract_fingerprint` `options_keys` mismatch (live vs golden fixture) | candidate factory |
| KI-2026-05-26-003 | `tests/test_current_vs_policy_workflow.py::test_combined_context_both_available` | `current.artifact_root` does not end with `current_portfolio`; combined-context path contract drift | current vs policy |
| KI-2026-05-26-004 | `tests/test_current_vs_policy_workflow.py::test_current_weights_without_sidecar` | Same as KI-001: `degraded` vs `unavailable` when sidecar missing | current vs policy |
| KI-2026-05-26-005 | `tests/test_factor_covariance.py::test_factor_covariance_empty_factor_frame_returns_explicit_skip_reason` | Empty factor frame returns `status: available`; test expects `unavailable` | factor / macro |
| KI-2026-05-26-006 | `tests/test_mvp_workflow.py::test_policy_current_adds_materialize_when_weights_set` | MVP plan argv lacks `--materialize-current` for policy+current workflow | MVP workflow |

Issue entries: KI-2026-05-26-001 through KI-2026-05-26-006 (below).

---

### Blocks 1-5 MVP core reliability gap index (Phase 16)

Wave **closed** 2026-05-21 (Session 09 / `RM-1018`). See
[Blocks 1-5 MVP Core Reliability Plan](docs/exec_plans/2026-05-21_blocks_1_5_mvp_core_reliability_plan.md)
for closure evidence. Audit gaps B15-G1 through B15-G6 from the opening audit are closed in
Sessions 02-07; representative verification and offline acceptance bundle closed in Session 09.

**Accepted residual (not Phase 16 blockers):** full `default_v1` factory remains operationally heavy
(use `--resume-candidates` after interruption); live full orchestrator E2E is operator-run, not
required every closure session.

---
### Phase 17 post-deep-audit gap index (closed)

Wave **closed** 2026-05-22 (Session 10 / `RM-1029`). Source:
[Blocks 1–5 Deep Audit Snapshot](docs/audits/2026-05-21_blocks_1_5_deep_audit_snapshot.md).
Plan: [Post-Deep-Audit Foundation Plan](docs/exec_plans/2026-05-21_post_deep_audit_foundation_plan.md).

| Gap | Summary | Roadmap | Target session |
| --- | --- | --- | --- |
| P17-G1 | ~~Selection/health rank `degraded` rows~~ | RM-1022 | **closed** Session 03 (favoring requires `available`; optimizers require `fair_comparison_ready`) |
| P17-G2 | ~~Core vs full menu misinterpretation~~ | RM-1022, RM-1028 | **closed** Session 03 + 09 (selection warnings + decision package review-scope banner) |
| P17-G3 | ~~Most optimizer rows not fair-comparison-ready on disk~~ | RM-1023 | **closed** Session 04 (offline full-menu gate; rebuild per runbook §8.6) |
| P17-G4 | ~~No live core E2E in automated closure~~ | RM-1021 | **closed** Session 02 (operator/`--live-core` gate; offline smoke remains default CI) |
| P17-G5 | ~~Invalid ticker not blocked at Block 1~~ | RM-1024 | **closed** Session 05 (explicit `analysis_subject` hard-rejects unknown tickers in `validate_config`) |
| P17-G6 | ~~False stale factory vs comparison timing~~ | RM-1025 | **closed** Session 06 (`factory_then_compare` context + write-before-compare ordering) |
| P17-G7 | ~~`analysis_mode` vs subject type confusion~~ | RM-1026 | **closed** Session 07 (`review_bundle_context` + `input_assumptions` trust lines) |
| P17-G8 | ~~No single review bundle fingerprint~~ | RM-1026 | **closed** Session 07 (`review_bundle_fingerprint` in comparison) |
| P17-G9 | ~~Blocks 6–7 lack guarded handoff spec~~ | RM-1027 | **closed** Session 08 (`downstream_decision_readiness_spec.md`, `src/downstream_decision_readiness.py`, health/robustness stress guards) |
| P17-G10 | ~~Decision package vs partial/degraded~~ | RM-1028 | **closed** Session 09 (`package_truthfulness`, review-scope banner, action context warning) |
| P17-G11 | Full factory heavy | — | accepted (runbook) |
| P17-G12 | X-Ray G7 deferred displays | — | Phase 12 accepted |
| P17-G13 | X-Ray optional in comparison readiness | KI-2026-05-21-001 | accepted |
| P17-G14 | `robust_scenario` Main stress dependency | RM-977 docs | accepted |

Remediation sessions 02–10 closed P17-G1–G10; G11–G14 remain **accepted** per ExecPlan closure.
Live full + resume E2E is documented (`scripts/verify_live_full_e2e.py`); operator-run, not default CI.

---
### Block 5 governance gap index (Phase 15)

Audit gaps **G1–G10** are defined in
[Optimization Engine Methodology Map](docs/audits/2026-05-20_optimization_engine_methodology_map.md) §4.
Phase 15 sessions **RM-991**–**RM-1002** close them per
[Optimization Engine Post-Audit Roadmap](docs/exec_plans/2026-05-20_optimization_engine_post_audit_roadmap.md).
Wave closed Session 12 (`RM-1002`), 2026-05-21.

| Gap | Summary | Roadmap | Session |
| --- | --- | --- | --- |
| G1 | ~~No single Block 5 optimization-engine spec~~ | RM-991 | 01 — **closed** |
| G2 | ~~Legacy policy disclosure weaker than candidate metadata~~ | RM-993 | 03 — **closed** |
| G3 | ~~Comparison does not surface optimizer methodology~~ | RM-995 | 05 — **closed** |
| G4 | ~~Fallback/approximate paths look like clean success~~ | RM-996 | 06 — **closed** |
| G5 | ~~Freshness lacks config/universe/estimator fingerprint~~ | RM-998 | 08 — **closed** |
| G6 | ~~Robust scenario lacks formal solver status~~ | RM-997 | 07 — **closed** |
| G7 | ~~Young ETF / covariance methodology not in summaries~~ | RM-999 | 09 — **closed** |
| G8 | ~~Target-only objectives (Max Sharpe, drawdown, macro, tax)~~ | RM-992 | 02 — **closed** (`DEC-2026-05-21-001`) |
| G9 | Stress `FAIL_*` labels vs mandate/release semantics | — | **accepted** (Stress Lab / policy specs; not Block 5 optimizer scope) |
| G10 | ~~X-Ray not a formal comparison-readiness gate~~ | RM-1000 | 10 — **closed** for required optimizer checks; optional `portfolio_xray` only (`KI-2026-05-21-001`) |
| — | ~~No Block 5 golden disclosure fixtures~~ | RM-1001 | 11 — **closed** |

---

### Block 4 governance gap index (Phase 14)

Audit gaps **G1–G10** are defined in
[Candidate Factory Methodology Map](docs/audits/2026-05-20_candidate_factory_methodology_map.md) §4.
Phase 14 sessions **RM-972**–**RM-981** close them per
[Candidate Portfolio Factory Post-Audit Roadmap](docs/exec_plans/2026-05-20_candidate_factory_post_audit_roadmap.md).
Registered in Session 01 (`RM-971`).

| Gap | Summary | Roadmap | Session |
| --- | --- | --- | --- |
| G1 | ~~Builder `FAIL_*` collapses to generic factory reason~~ | RM-972 | 02 — **closed** |
| G2 | ~~Freshness is `analysis_end` only; no config fingerprint~~ | RM-976 Done | — |
| G3 | ~~`freshness_status: unchecked` can skip without review date~~ | RM-973 | 03 — **closed** |
| G4 | Full `default_v1` run is operationally heavy | RM-920 (mitigated); `execution-mode standard` + optional Phase 3 full reports (`RM-1022` Session 8); `--resume` (`RM-979`); runbook §8 | 08 |
| G5 | ~~No resumable factory checkpoint~~ | RM-979 Done (closes RM-921 resumable scope) | — |
| G6 | ~~No `construction_disclosure` on comparison rows~~ | RM-974 Done | — |
| G7 | Per-candidate `portfolio_xray.json` not in comparison contract | — | No Phase 14 code session |
| G8 | ~~Robust MV λ calibration path outside factory menu~~ | RM-977 Done | — |
| G9 | ~~Product concept lists candidates not in registry~~ | RM-981 Done | — |
| G10 | ~~`robust_scenario` uses Main stress/scenario artifacts~~ | RM-977 Done | — |
| — | No golden `candidate_comparison` fixture bundle | RM-978 | 08 |

---

Issue ID: KI-2026-05-20-001
Title: Factory run JSON does not propagate builder FAIL_* reasons (G1)

- Status: **resolved** (2026-05-20, Session 02 / `RM-972`)
- Severity: medium (was)
- Area: architecture
- Resolution: `src/candidate_factory.py` reads `{artifact_root}/summary.json` after failed builds and maps `FAIL_*` to `builder_*` factory `reason_code` values; optional `builder_status` / `builder_reason` on steps; tests in `tests/test_candidate_factory.py`.
- Source links: [methodology map §4 G1](docs/audits/2026-05-20_candidate_factory_methodology_map.md), [candidate factory spec](docs/specs/candidate_factory_spec.md).

Issue ID: KI-2026-05-20-002
Title: Candidate freshness ignores config/universe fingerprint (G2)

- Status: **resolved** (2026-05-20, Session 06 / `RM-976`)
- Severity: medium (was)
- Area: architecture
- Resolution: `compute_candidate_config_fingerprint` in `src/snapshot.py`; stamped on window snapshots in `run_portfolio_report_for_weights`; factory reuse gated on `stale_config` + comparison `stale_config_fingerprint` unavailable reason; tests in `tests/test_candidate_factory.py` and `tests/test_candidate_comparison.py`.
- Source links: [methodology map G2](docs/audits/2026-05-20_candidate_factory_methodology_map.md), [candidate_factory_spec.md](docs/specs/candidate_factory_spec.md), [candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md).

Issue ID: KI-2026-05-20-003
Title: Factory may skip existing snapshots when review analysis_end is unknown (G3)

- Status: **resolved** (2026-05-20, Session 03 / `RM-973`)
- Severity: medium (was)
- Area: architecture
- Resolution: `src/candidate_factory.py` rebuilds on `freshness_status: unchecked` instead of `skipped_existing`; comparison rows warn with `candidate_freshness_unchecked_no_review_analysis_end:{candidate_id}` when review date is unknown; tests in `tests/test_candidate_factory.py` and `tests/test_candidate_comparison.py`.
- Source links: [methodology map G3](docs/audits/2026-05-20_candidate_factory_methodology_map.md), [candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md).

Issue ID: KI-2026-05-20-004
Title: Comparison rows lack construction_disclosure passthrough (G6)

- Status: **resolved** (2026-05-20, Session 04 / `RM-974`)
- Severity: low (was)
- Area: reports
- Resolution: `src/candidate_comparison.py` emits `construction_disclosure` on every registry row (`baseline_metadata` passthrough, `builder_summary`, Main/sidecar excerpts, optional `factory_step`); spec v1.3 in [candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md); tests in `tests/test_candidate_comparison.py`.
- Source links: [methodology map G6](docs/audits/2026-05-20_candidate_factory_methodology_map.md), [candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md).

Issue ID: KI-2026-05-20-005
Title: Robust MV lambda source not disclosed in factory orchestration (G8)

- Status: **resolved** (2026-05-20, Session 07 / `RM-977`)
- Severity: low (was)
- Area: docs
- Resolution: `src/candidate_robust_disclosure.py`; factory `robust_paths_disclosure` on robust MV steps; comparison `construction_disclosure.robust_paths`; [operational_runbook.md](docs/operational_runbook.md) robust suite section; specs updated.
- Source links: [robust_mv_spec.md](docs/specs/robust_mv_spec.md), [methodology map G8](docs/audits/2026-05-20_candidate_factory_methodology_map.md).

Issue ID: KI-2026-05-20-006
Title: robust_scenario factory depends on Main stress artifacts (G10)

- Status: **resolved** (2026-05-20, Session 07 / `RM-977`)
- Severity: low (was)
- Area: architecture
- Resolution: Main prerequisite disclosure on factory/comparison rows; explicit `skipped_dependency` messages; runbook and [robust_scenario_optimization_spec.md](docs/specs/robust_scenario_optimization_spec.md) shared-calibration boundary documented.
- Source links: [methodology map G10](docs/audits/2026-05-20_candidate_factory_methodology_map.md), [candidate_factory_layer_spec.md](docs/specs/candidate_factory_layer_spec.md).

Issue ID: KI-2026-05-20-007
Title: Product concept candidate families not in registry (G9)

- Status: **resolved** (2026-05-20, Session 11 / `RM-981`)
- Severity: low (was)
- Area: docs
- Resolution: **DEC-2026-05-20-003** and [candidate_portfolios_spec.md](docs/specs/candidate_portfolios_spec.md) § Concept candidates not in registry — explicit **declined** / **deferred** / **covered_by_existing** per concept id; registry remains implementation truth.
- Source links: [methodology map G9](docs/audits/2026-05-20_candidate_factory_methodology_map.md), [DIAGNOSTIC_PRODUCT_CONCEPT.md](docs/DIAGNOSTIC_PRODUCT_CONCEPT.md) §4–5.

Issue ID: KI-2026-05-20-008
Title: portfolio_xray.json not part of candidate comparison readiness (G7)

- Status: accepted
- Severity: low
- Area: architecture
- Risk: Comparison arena cannot rank X-Ray archetype or weakness signals across candidates without opening each folder.
- Evidence: Methodology map G7; comparison contract uses snapshots and stress blocks only.
- Current mitigation: Open `{artifact_root}/portfolio_xray.json` per candidate when X-Ray comparison is needed.
- Next action: None in Phase 14; revisit only if product spec requires X-Ray in comparison JSON.
- Source links: [methodology map G7](docs/audits/2026-05-20_candidate_factory_methodology_map.md), [portfolio_xray_diagnostics_spec.md](docs/specs/portfolio_xray_diagnostics_spec.md).
- Remove when: A canonical spec requires X-Ray fields on comparison rows and implementation ships.

Issue ID: KI-2026-05-19-010
Title: X-Ray archetype and weakness explanations can create false confidence

- Status: resolved
- Severity: medium
- Area: reports
- Risk: Simple labels or low-severity rows can be read as definitive conclusions instead of partial diagnostics with incomplete evidence and conflicting signals.
- Evidence: Portfolio X-Ray audit found archetype output capable of labeling a portfolio as inflation-sensitive without explaining simultaneous inflation/rates vulnerability.
- Resolution (2026-05-20, Session 07 / RM-937): Archetype V2 emits `positive_evidence`, `negative_evidence`, `archetype_scorecard`, `conflicting_signals`, and `conflict_summary`, including weakness-map regime tensions when inflation-sensitive holdings coexist with inflation/rates vulnerability.
- Source links: [Portfolio X-Ray audit](docs/audits/2026-05-19_portfolio_xray_layer_audit.md), [X-Ray diagnostics spec](docs/specs/portfolio_xray_diagnostics_spec.md), [portfolio_xray.py](src/portfolio_xray.py), [tests/test_portfolio_xray.py](tests/test_portfolio_xray.py).

Issue ID: KI-2026-05-19-005
Title: Full candidate factory refresh is operationally heavy for one-shot review runs

- Status: mitigated
- Severity: medium
- Area: architecture
- Risk: Full `--mode full` rebuild can still exceed session limits when many optimizer snapshots are stale; decision outputs must not be read as covering the full product menu when `candidate_menu.is_partial_menu` is true.
- Resolution (2026-05-20, Session 09 / RM-939): Default `run_portfolio_review.py` uses `--mode core` and factory profile `core_v1`; `--mode full` runs `default_v1` explicitly. Comparison and decision-package outputs include `candidate_menu` partial-menu disclosure and refresh commands.
- Remaining gap (G4): full `default_v1` menu is still operationally heavy when every candidate
  needs Phase 3 full reports and PDFs, or when candidate weight builders themselves are slow.
  Mitigated for portfolio-first review via `--execution-mode standard` (compare-ready lightweight
  snapshots), opt-in `--parallel-lightweight-reports` for eligible Phase 2 reports,
  `--selected-candidates-for-full-report` for deep-dive HTML/PDF on a subset, `--resume` after
  interrupt (`RM-979`), and `--pdf-mode final_only` with Phase 3 instead of per-candidate Pandoc.
- Source links: [run_portfolio_review.py](run_portfolio_review.py), [portfolio_review_workflow.py](src/portfolio_review_workflow.py), [candidate_factory.py](src/candidate_factory.py), [candidate_comparison.py](src/candidate_comparison.py), [operational_runbook.md](docs/operational_runbook.md), [methodology map G4](docs/audits/2026-05-20_candidate_factory_methodology_map.md).
- Remove when: Full-run reliably completes within agreed operator time budget without manual staging, including the Phase 3/full-report cases that remain outside lightweight-report parallelism.

Issue ID: KI-2026-05-26-001
Title: Current row in optimize mode reported as degraded instead of unavailable

- Status: open
- Severity: medium
- Area: testing
- Risk: Comparison and downstream selection treat a non-materialized current portfolio as partially usable (`degraded`) when product contract expects hard `unavailable` with `missing_current_report`.
- Evidence: `python -m pytest tests/test_candidate_comparison.py::test_current_unavailable_in_optimize_mode` fails (2026-05-26 full suite); actual `cur["status"] == "degraded"`.
- Current mitigation: Focused suites that do not assert strict unavailable semantics still pass; operators must not infer current is compare-ready from `degraded` alone.
- Next action: Align `src/candidate_comparison.py` current-row status with spec/tests, or update spec + tests if `degraded` is the new canonical signal (document `unavailable_reason`).
- Source links: [tests/test_candidate_comparison.py](tests/test_candidate_comparison.py), [candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md), [DECISIONS.md](DECISIONS.md) (portfolio-first subject).
- Remove when: `test_current_unavailable_in_optimize_mode` passes and comparison spec matches behavior.

Issue ID: KI-2026-05-26-002
Title: Candidate factory live build golden fingerprint drift (options_keys)

- Status: open
- Severity: low
- Area: testing
- Risk: Factory contract regressions can slip through if golden `options_keys` are stale; CI/full suite noise hides real breaks.
- Evidence: `python -m pytest tests/test_candidate_factory_contract.py::test_live_factory_build_matches_golden_document` fails (2026-05-26 full suite); `options_keys` differ between live `normalize_factory_run(build_golden_factory_run())` and golden fixture (e.g. `lightweight_report_workers` vs `pdf_mode`).
- Current mitigation: Run `tests/test_candidate_factory.py` and factory-focused contract tests; regenerate golden via `tests/candidate_factory_golden_inputs.py` when options surface is intentionally changed.
- Next action: Regenerate golden fixture and/or narrow fingerprint to stable contract fields; document new factory CLI options in spec.
- Source links: [tests/test_candidate_factory_contract.py](tests/test_candidate_factory_contract.py), [docs/exec_plans/2026-05-25_code_migration_to_diagnosis_first_portfolio_mri.md](docs/exec_plans/2026-05-25_code_migration_to_diagnosis_first_portfolio_mri.md) (Session 12 noted same drift).
- Remove when: `test_live_factory_build_matches_golden_document` passes after intentional golden refresh.

Issue ID: KI-2026-05-26-003
Title: Combined current vs policy artifact_root path convention drift

- Status: open
- Severity: medium
- Area: architecture
- Risk: `build_current_vs_policy_status` and no-trade workflow may assume `current_portfolio` sidecar paths that comparison no longer emits, breaking combined-context completeness checks.
- Evidence: `tests/test_current_vs_policy_workflow.py::test_combined_context_both_available` fails; `cur["artifact_root"].endswith("current_portfolio")` is False (2026-05-26 full suite).
- Current mitigation: Portfolio-first review paths that materialize subject explicitly may still work on disk; do not rely on comparison `artifact_root` suffix alone without verification.
- Next action: Reconcile `candidate_comparison` current `artifact_root` with `CURRENT_SIDECAR_SUBDIR` / materialization helpers and `analysis_setup_summary.current_materialization_root`.
- Source links: [tests/test_current_vs_policy_workflow.py](tests/test_current_vs_policy_workflow.py), [src/candidate_comparison.py](src/candidate_comparison.py), [portfolio_review_workflow.py](src/portfolio_review_workflow.py).
- Remove when: `test_combined_context_both_available` passes and path contract is documented in spec.

Issue ID: KI-2026-05-26-004
Title: Current without sidecar should be unavailable, not degraded

- Status: open
- Severity: medium
- Area: testing
- Risk: No-trade and current-vs-policy status may mark workflows actionable when current evidence was never materialized to a sidecar report tree.
- Evidence: `tests/test_current_vs_policy_workflow.py::test_current_weights_without_sidecar` fails (2026-05-26 full suite); `cur["status"] == "degraded"` vs expected `unavailable` / `missing_current_report`.
- Current mitigation: Same as KI-2026-05-26-001; treat missing sidecar as operator action required before trusting current row.
- Next action: Fix with KI-2026-05-26-001/003 in one comparison + materialization alignment pass; verify `build_current_vs_policy_status` `skip_reason == current_not_materialized`.
- Source links: [tests/test_current_vs_policy_workflow.py](tests/test_current_vs_policy_workflow.py), KI-2026-05-26-001, KI-2026-05-26-003.
- Remove when: `test_current_weights_without_sidecar` passes.

Issue ID: KI-2026-05-26-005
Title: Factor covariance empty factor frame should return unavailable

- Status: open
- Severity: medium
- Area: factor_macro
- Risk: Downstream commentary and diagnostics may show factor-covariance analytics as available when no factors loaded, masking data-quality failure.
- Evidence: `tests/test_factor_covariance.py::test_factor_covariance_empty_factor_frame_returns_explicit_skip_reason` fails (2026-05-26 full suite); `out["status"] == "available"`.
- Current mitigation: Inspect `factor_load_diagnostics` and missing-factor lists in reports when factors are sparse.
- Next action: Align `factor_covariance_analytics` empty-input branch in `src/stress_factors.py` (or owning module) with spec/tests for explicit `unavailable` + skip reason.
- Source links: [tests/test_factor_covariance.py](tests/test_factor_covariance.py), [docs/exec_plans/2026-04-29_factor_covariance_forecast_quality.md](docs/exec_plans/2026-04-29_factor_covariance_forecast_quality.md).
- Remove when: Empty-frame test passes and export/commentary reflects skip reason.

Issue ID: KI-2026-05-26-006
Title: MVP workflow policy+current plan missing materialize-current step

- Status: open
- Severity: medium
- Area: architecture
- Risk: `run_mvp_workflow.py` policy+current profile may skip automatic current materialization when `current_weights` are set, leaving comparison/workflow tests and operators without the expected CLI hook.
- Evidence: `tests/test_mvp_workflow.py::test_policy_current_adds_materialize_when_weights_set` fails (2026-05-26 full suite); joined plan argv lacks `--materialize-current`.
- Current mitigation: Run materialization explicitly via portfolio-review or materialize script before compare when using MVP workflow.
- Next action: Add `--materialize-current` to `build_mvp_workflow_plan` for `WORKFLOW_POLICY_CURRENT` when weights present, or update test/spec if materialization moved to another entrypoint.
- Source links: [tests/test_mvp_workflow.py](tests/test_mvp_workflow.py), [run_mvp_workflow.py](run_mvp_workflow.py), [src/mvp_workflow.py](src/mvp_workflow.py) if present.
- Remove when: `test_policy_current_adds_materialize_when_weights_set` passes.

Issue ID: KI-2026-05-21-001
Title: portfolio_xray.json optional in optimization comparison readiness (G10)

- Status: accepted
- Severity: low
- Area: architecture
- Risk: Fair-comparison readiness can pass without per-candidate X-Ray archetype/weakness signals in `candidate_comparison.json`.
- Evidence: Methodology map G10; `optimizer_comparison_readiness_v1` treats `portfolio_xray` as optional; required checks are weights, snapshot, stress, disclosure, methodology, quality, freshness.
- Current mitigation: Open `{artifact_root}/portfolio_xray.json` per candidate when X-Ray comparison is needed; readiness block documents missing optional X-Ray.
- Next action: None in Phase 15; revisit only if product spec requires X-Ray on comparison rows.
- Source links: [methodology map G10](docs/audits/2026-05-20_optimization_engine_methodology_map.md), [optimization_engine_layer_spec.md](docs/specs/optimization_engine_layer_spec.md), [optimization_readiness.py](src/optimization_readiness.py).
- Remove when: A canonical spec requires X-Ray fields on optimizer comparison rows and implementation ships.

## Update Rules

- Update this file when a known issue is discovered, fixed, accepted, or no longer relevant.
- If a code change fixes an active issue, remove the issue only after verification passes and related docs are synced.
- If a fixed issue is meaningful at project level, add one short `Fixed` entry to [CHANGELOG.md](CHANGELOG.md).
- If a code change introduces a known limitation that is not fixed in the same change, add it here before considering the task done.
- If the issue affects data behavior, also check [DATA.md](DATA.md).
- If the issue affects verification strategy, also check [TESTING.md](TESTING.md).
- If the issue affects implementation behavior, also check [SPEC.md](SPEC.md) and the owning file under [docs/specs/](docs/specs/README.md).
- If the issue requires multi-step implementation, create or update an ExecPlan under `docs/exec_plans/`.
