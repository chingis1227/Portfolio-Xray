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
| G4 | Full `default_v1` run is operationally heavy | RM-920 (mitigated); `--resume` (`RM-979`); operator playbooks (`RM-980`, runbook §8) | — |
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
- Remaining gap (G4): full `default_v1` menu is still sequential and heavy; use `core` default or `run_candidate_factory.py --resume` after interrupt (`RM-979`). Optional parallelism still open.
- Source links: [run_portfolio_review.py](run_portfolio_review.py), [portfolio_review_workflow.py](src/portfolio_review_workflow.py), [candidate_factory.py](src/candidate_factory.py), [candidate_comparison.py](src/candidate_comparison.py), [operational_runbook.md](docs/operational_runbook.md), [methodology map G4](docs/audits/2026-05-20_candidate_factory_methodology_map.md).
- Remove when: Full-run reliably completes within agreed operator time budget without manual staging, or parallelism ships with isolation guarantees.

## Update Rules

- Update this file when a known issue is discovered, fixed, accepted, or no longer relevant.
- If a code change fixes an active issue, remove the issue only after verification passes and related docs are synced.
- If a fixed issue is meaningful at project level, add one short `Fixed` entry to [CHANGELOG.md](CHANGELOG.md).
- If a code change introduces a known limitation that is not fixed in the same change, add it here before considering the task done.
- If the issue affects data behavior, also check [DATA.md](DATA.md).
- If the issue affects verification strategy, also check [TESTING.md](TESTING.md).
- If the issue affects implementation behavior, also check [SPEC.md](SPEC.md) and the owning file under [docs/specs/](docs/specs/README.md).
- If the issue requires multi-step implementation, create or update an ExecPlan under `docs/exec_plans/`.
