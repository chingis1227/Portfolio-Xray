# Core / Full Artifact and Documentation Confusion Remediation Plan

**Status:** Completed (Sessions 00–06 closed 2026-05-24). Origin audit remediation:
[confusion audit](../audits/2026-05-23_core_full_artifact_documentation_confusion_audit.md) § «Remediation status».

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan must be maintained in accordance with [PLANS.md](../../PLANS.md).

## Purpose / Big Picture

After the [core/full confusion audit](../audits/2026-05-23_core_full_artifact_documentation_confusion_audit.md),
operators and agents still mix portfolio-first subject diagnostics with legacy policy artifacts at
`Main portfolio/` root, treat a **core** factory run as proof of the **full** optimizer menu, and
assume PDF/TXT/CSV exist after the default `site_api` review. The underlying orchestration code is
largely correct; trust breaks down in documentation, runbooks, and stale on-disk evidence.

When this plan is complete, a reader can follow `OUTPUTS.md`, `WORKFLOW.md`, and the operational
runbook without misidentifying which portfolio was diagnosed, which factory profile last ran, or
which files are authoritative JSON versus optional exports. **Scope is documentation and agent rules
only** — no Python changes, no JSON contract changes, and no refresh of generated artifacts unless a
future session explicitly targets them.

**Chat rule:** one session = one new chat. Start the next session in a new thread with the Session
prompt from this plan. Session 00 registers the plan only; content edits begin in Session 01.

## Progress

- [x] (2026-05-23) Session 00 (`RM-1100`): ExecPlan persisted; [exec_plans/README.md](README.md)
  marks this plan **Active**; [audits/README.md](../audits/README.md) registers the confusion audit
  and links this plan; [CHANGELOG.md](../../CHANGELOG.md) entry added. No changes to `OUTPUTS.md`,
  runbook, or other handoff docs in this session.
- [x] (2026-05-24) Session 01 (`RM-1101`): P0 «Read this first» in [OUTPUTS.md](../../OUTPUTS.md) and
  [docs/operational_runbook.md](../operational_runbook.md) §0.1 (subject vs legacy policy root;
  stale exports; factory vs comparison scope). `python scripts/verify_docs.py` OK.
- [x] (2026-05-24) Session 02 (`RM-1102`): Portfolio-first operator checklist in [WORKFLOW.md](../../WORKFLOW.md)
  and runbook §8 cross-links. `python scripts/verify_docs.py` OK.
- [x] (2026-05-24) Session 03 (`RM-1103`): [OUTPUTS.md](../../OUTPUTS.md) command matrix split (core review vs
  standalone `default_v1` factory); verification report §20 snapshot caveat;
  [README.md](../../README.md) PDF one-liner + aligned summary table; [audits/README.md](../audits/README.md)
  Blocks 1–5 row updated. `python scripts/verify_docs.py` OK.
- [x] (2026-05-24) Session 04 (`RM-1104`): [ARCHITECTURE.md](../../ARCHITECTURE.md) candidate flow
  (`analysis_subject` baseline; legacy `policy` row optional); [.cursor/rules/portfolio_run_scope.mdc](../../.cursor/rules/portfolio_run_scope.mdc)
  portfolio-first PDF default vs legacy rebuild scope; [AGENTS.md](../../AGENTS.md) Main Commands
  (`site_api` does not refresh `pdf files/`; `--with-pdf` / `--legacy-full-pdf`). `python scripts/verify_docs.py` OK.
- [x] (2026-05-24) Session 05 (`RM-1105`): [GLOSSARY.md](../../GLOSSARY.md) Blocks 1–5 vs decision package;
  factory/comparison evidence terms; [candidate_comparison_spec.md](../specs/candidate_comparison_spec.md)
  factory vs comparison scope note; [portfolio_review_workflow_spec.md](../specs/portfolio_review_workflow_spec.md)
  cross-links; walkthrough notes in both Blocks 1–5 walkthrough audits; [SPEC.md](../../SPEC.md) pointer.
  `python scripts/verify_docs.py` OK.
- [x] (2026-05-24) Session 06 (`RM-1106`): Closure — remediation status in confusion audit;
  plan **Completed**; [exec_plans/README.md](README.md) pointer cleared; [CHANGELOG.md](../../CHANGELOG.md)
  closure entry. `python scripts/verify_docs.py` OK.

## Surprises & Discoveries

- Observation: The confusion audit found code behavior coherent but disk state misleading (e.g.
  `core_v1` factory with 6 reused steps vs 19 comparison rows including optimizers from prior runs).
  Evidence: [confusion audit](../audits/2026-05-23_core_full_artifact_documentation_confusion_audit.md)
  §4.2; on-disk `Main portfolio/candidate_factory_run.json` and `candidate_comparison.json`.

- Observation: Remediation was explicitly scoped **docs-only** by product decision; product fixes
  (comparison registry filter, manifest on orchestrator, stale export cleanup) remain deferred.
  Evidence: Session 00 planning chat; audit §9 vs § «Out of scope».

## Decision Log

- Decision: Execute remediation as six documentation sessions (01–06) after Session 00 registration,
  without code or generated-artifact changes.
  Rationale: Audit §9 minimal fixes; user confirmed docs-only scope for this plan.
  Date/Author: 2026-05-23 / Session 00.

- Decision: Keep [Blocks 1–5 Verification Report](../audits/2026-05-22_blocks_1_5_verification_report.md)
  as Active input but add disk-caveat in Session 03 rather than re-running full verification in-plan.
  Rationale: Report value is checklist structure; snapshot claims must not be read as current disk
  without checking `factory_profile_id`.
  Date/Author: 2026-05-23 / Session 00.

## Outcomes & Retrospective

**Closure (Session 06, 2026-05-24):** All six documentation sessions delivered without code or
generated-artifact changes. Operators and agents now have a single «Read this first» path
(`OUTPUTS.md`, runbook §0.1), a portfolio-first checklist (`WORKFLOW.md`, runbook §8), a split
command matrix (core `core_v1` review vs standalone/full `default_v1` factory), disk caveats on the
Blocks 1–5 verification report, aligned ARCHITECTURE / agent rules / AGENTS entrypoints for
`site_api` vs PDF, and glossary/spec terms for factory vs comparison scope and Blocks 1–5 vs decision
package.

**What did not change:** on-disk `Main portfolio/` may still mix legacy policy root, subject JSON,
stale TXT/HTML/PNG/PDF, and comparison rows wider than the last `core_v1` factory run — docs now
explain how to read that state; product fixes remain deferred per audit §9 optional hygiene.

**Retrospective:** The audit was correct that orchestration code was largely coherent; trust broke
on documentation and stale evidence. Docs-only remediation was sufficient for the stated goal;
re-verify disk (`factory_profile_id`, `candidate_menu`) before any operational sign-off.

## Context and Orientation

**Source audit:**
[2026-05-23_core_full_artifact_documentation_confusion_audit.md](../audits/2026-05-23_core_full_artifact_documentation_confusion_audit.md)

**Top confusion sources (audit §8):**

1. Two portfolios at `Main portfolio/` — `analysis_subject/` vs root `run_result.json` / policy xray-stress.
2. Comparison wider than last factory run (`_REGISTRY_ROWS` scans disk; docs must explain).
3. `site_api` default vs stale TXT/HTML/PNG/PDF on disk.
4. `candidate_factory_run.json` vs `candidate_comparison.json` different scopes.
5. Blocks 1–5 audit scope vs decision-package JSON from same CLI.

**Routine command (unchanged by this plan):**

    python run_portfolio_review.py --mode core

**Out of scope for this plan:** Python changes in `src/candidate_comparison.py`, `output_policy.py`,
orchestrator manifest wiring, regenerating `Main portfolio/` or `pdf files/`.

## Plan of Work

Session 01 adds a «Read this first» block to `OUTPUTS.md` immediately after Core Rule and a matching
§0.1 in `docs/operational_runbook.md`. Session 02 adds a portfolio-first operator path to
`WORKFLOW.md` and extends runbook §8. Session 03 fixes command matrix ambiguity and verification
report §20 wording. Session 04 updates `ARCHITECTURE.md`, `portfolio_run_scope.mdc`, and `AGENTS.md`.
Session 05 adds glossary terms and short spec cross-links. Session 06 closes the plan and updates the
audit file with remediation status.

## Concrete Steps

Session 00 (complete):

    cd <repository-root>
    python scripts/verify_docs.py

Expected: `docs verification: OK`

Sessions 01–06: each session ends with the same `verify_docs.py` command.

## Validation and Acceptance

Plan-level acceptance when Session 06 completes:

- `OUTPUTS.md` and runbook distinguish subject vs policy root artifacts.
- `WORKFLOW.md` contains a portfolio-first operator checklist.
- Command matrix does not imply `default_v1` for default review.
- Verification report §20 carries snapshot-at-write-time caveat.
- `python scripts/verify_docs.py` passes after every session.
- This ExecPlan is **Completed** and exec_plans README **Active** pointer returns to None with this
  plan listed under Completed.

## Idempotence and Recovery

Documentation edits are idempotent. If a session partially lands, re-run the same session prompt in a
new chat and reconcile `Progress` checkboxes. Do not edit generated portfolio folders as part of this
plan.

## Artifacts and Notes

| Session | Primary deliverables |
| --- | --- |
| 00 | This ExecPlan; register updates; CHANGELOG |
| 01 | OUTPUTS «Read this first»; runbook §0.1 |
| 02 | WORKFLOW operator path; runbook §8 |
| 03 | Command matrix; verification report caveat; audits README; README |
| 04 | ARCHITECTURE; portfolio_run_scope; AGENTS |
| 05 | GLOSSARY; specs; walkthrough; SPEC pointer |
| 06 | Audit remediation status; plan closure |

## Interfaces and Dependencies

No code interfaces. Documentation must remain consistent with:

- [OUTPUTS.md](../../OUTPUTS.md) — output policy and artifact map
- [docs/specs/portfolio_review_workflow_spec.md](../specs/portfolio_review_workflow_spec.md) — portfolio-first order
- [docs/specs/reporting_outputs_spec.md](../specs/reporting_outputs_spec.md) — JSON vs export profiles

---

Revision note, 2026-05-23: Session 00 created plan and project-memory registration; Sessions 01–06
defined per confusion audit §9 (docs-only).
