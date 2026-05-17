# Post-Audit Stabilization And Analytics Plan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.
Maintenance follows `PLANS.md` at the repository root.

This plan starts after the post-session audit in `docs/audits/2026-05-17_post_session_deep_system_audit.md`.
It intentionally splits the remaining work into separate future sessions so a new Codex chat can load
only the relevant context, complete one narrow workstream, verify it, and update this file before the
next session starts.

## Purpose / Big Picture

The project already has a file-first V1 decision pipeline: candidate comparison, robustness scoring,
health scoring, selection, action planning, monitoring, and generated decision journal outputs. The
next user-visible improvement is to make the project coherent and reliable around that pipeline: docs
should describe what exists, reports should expose the decision package, default text should be clean
English, current-vs-policy workflows should be reliable, candidates should be orchestrated instead of
compared only when folders happen to exist, and the next analytical layers should be added in a
controlled order.

When this plan is complete, a user should be able to run the project and see a coherent decision-support
package: source docs agree with code, stale known issues are closed, user-facing text is readable
English, current portfolios can be compared against policy targets, candidate generation is organized,
trade-offs and model risks are explicit, and new sensitivity, Pareto/dominance, and regret artifacts are
available without silently changing the policy optimizer.

## Progress

- [x] (2026-05-17) Created this post-audit stabilization ExecPlan after reading `PLANS.md`,
  `docs/audits/2026-05-17_post_session_deep_system_audit.md`, `docs/ROADMAP.md`, and the prior
  session plan.
- [x] (2026-05-17) Linked this ExecPlan from `docs/ROADMAP.md` and recorded the planning change in
  `CHANGELOG.md`.
- [x] (2026-05-17) Session 02 completed: synchronized `README.md`, `AGENTS.md`, `SPEC.md`,
  `PRODUCT.md`, and `ARCHITECTURE.md` so implemented file-first V1 decision artifacts are no longer
  described as target/TBD; updated `docs/ROADMAP.md`, `KNOWN_ISSUES.md`, and `CHANGELOG.md`.
- [x] (2026-05-17) Session 03 completed: assigned Selection Engine V1 the unique
  `DEC-2026-05-17-006` decision ID, updated the historical session-plan reference, closed
  `KI-2026-05-17-006`, and marked RM-611 done.
- [x] (2026-05-17) Session 04 completed: synchronized detailed decision-package specs for the
  implemented artifact chain from comparison through robustness, health, selection, action,
  monitoring, and journal outputs; RM-612 is now in progress because compact report/PDF surfacing
  remains for Sessions 06-07.
- [x] (2026-05-17) Session 05 completed: cleaned source/generator English defaults and mojibake in
  optimization/report/PDF/config/docs paths, removed the obsolete one-off translation helper, updated
  `KI-2026-05-17-007` to track only generated-output refresh/QA, and moved RM-613 to in progress.
- [x] (2026-05-17) Session 06 completed: created `docs/specs/decision_package_reporting_spec.md`,
  updated `reporting_outputs_spec.md`, `OUTPUTS.md`, and `docs/specs/README.md`.
- [x] (2026-05-17) Session 07 completed: implemented `src/decision_package_reporting.py`,
  wired `write_decision_package_reporting_outputs` after the decision journal in
  `write_candidate_comparison_outputs`, extended `run_compare_variants.py` CLI messaging,
  added decision-package PDF rebuild in `pdf_reports.py`, and added
  `tests/test_decision_package_reporting.py`.
- [ ] Session 08: Current-vs-policy workflow spec.
- [ ] Session 09: Current-vs-policy workflow implementation.
- [ ] Session 10: Candidate factory spec.
- [ ] Session 11: Candidate factory implementation.
- [ ] Session 12: Trade-off and model-risk spec.
- [ ] Session 13: Trade-off and model-risk implementation.
- [ ] Session 14: Assumption Sensitivity spec.
- [ ] Session 15: Assumption Sensitivity implementation.
- [ ] Session 16: Pareto/Dominance spec.
- [ ] Session 17: Pareto/Dominance implementation.
- [ ] Session 18: Regret Analysis spec.
- [ ] Session 19: Regret Analysis implementation.
- [ ] Session 20: Final integration and closure.

## Surprises & Discoveries

- Observation: The old development plan remains useful as a pattern, but it should no longer be the
  handoff spine for post-audit work.
  Evidence: `docs/exec_plans/2026-05-17_project_development_session_plan.md` completed Sessions 01-20
  and Phase 6 audit triage; the new open work starts at roadmap item RM-610.

- Observation: The current repository already contains planned roadmap rows for most post-audit
  stabilization work.
  Evidence: `docs/ROADMAP.md` lists RM-610 through RM-622, covering docs sync, planning integrity,
  reporting integration, text hygiene, current-vs-policy workflow, candidate workflow, and future
  analytics.

- Observation: There are existing tests for the current decision pipeline, so later sessions should
  extend those tests rather than creating parallel fixtures from scratch.
  Evidence: current focused tests include candidate comparison, robustness scorecard, portfolio health
  score, selection engine, action engine, monitoring, and decision journal tests.

- Observation: The only non-audit reference that needed retargeting from `DEC-2026-05-17-003` to the
  Selection Engine decision was the historical Session 14 progress note.
  Evidence: targeted search found the duplicate IDs in `DECISIONS.md`, the active known issue, the
  post-audit handoff text, and one selection-specific reference in
  `docs/exec_plans/2026-05-17_project_development_session_plan.md`.

- Observation: Session 04 did not require code changes because the implemented pipeline already writes
  the V1 decision-package artifacts from `write_candidate_comparison_outputs`.
  Evidence: targeted source search found comparison, robustness, health, selection, action, monitoring,
  and journal writes in `src/candidate_comparison.py`; the specs mainly needed stale future/TBD wording
  and ownership links updated.

- Observation: Session 05 found that some PDF generator functions already returned English output but
  still contained unreachable old Russian/mojibake branches after `return` statements.
  Evidence: `src/pdf_reports.py` had old unreachable blocks in `build_ew_rp_markdown`,
  `build_commentary_report_md`, `build_weights_report_md`, and `build_ips_summary_md`; these were
  removed so source scans no longer flag stale user-facing text there.

- Observation: Source/generator text can be fixed without hand-editing generated reports, but existing
  generated folders may still show older text until a report/PDF regeneration pass is run.
  Evidence: Session 05 targeted source scans passed after code and docs cleanup; `KI-2026-05-17-007`
  remains open for generated-output refresh and visual/readability QA.

## Decision Log

- Decision: This plan excludes full product UI/workspace work.
  Rationale: The user explicitly asked to remove product UI/workspace from the current scope. The
  current priority is stabilization, report integration, workflow hardening, and selected analytics.
  Date/Author: 2026-05-17 / Codex.

- Decision: Keep Main optimization and robust optimization as separate roles throughout this plan.
  Rationale: Main optimization is the production policy path that writes policy weights and applies
  release gates. Robust MV and robust scenario optimization are candidate/benchmark paths. Changing
  that boundary would require a separate accepted spec and decision.
  Date/Author: 2026-05-17 / Codex.

- Decision: Default project artifacts remain English-only unless a future localization feature is
  explicitly specified.
  Rationale: Chat with the user can be Russian, but source docs, code comments, CLI text, report copy,
  and generated artifacts should be stable English project artifacts.
  Date/Author: 2026-05-17 / Codex.

- Decision: New analytics must not automatically override Selection Engine output in V1.
  Rationale: Assumption Sensitivity, Pareto/Dominance, and Regret Analysis should first be diagnostic
  evidence. Selection behavior changes require their own accepted spec update.
  Date/Author: 2026-05-17 / Codex.

- Decision: Use `DEC-2026-05-17-006` for the Selection Engine V1 contract and keep
  `DEC-2026-05-17-003` for the Robustness Scorecard V1 contract.
  Rationale: `DEC-2026-05-17-003` was already referenced by the robustness-scorecard decision, while
  `DEC-2026-05-17-006` is the next unused same-day project decision ID.
  Date/Author: 2026-05-17 / Codex.

## Outcomes & Retrospective

Session 01 outcome: this ExecPlan now exists and is linked from the roadmap. No runtime behavior was
changed.

Session 02 outcome: top-level docs now distinguish implemented file-first V1 artifacts from still-future
UI/workspace, report-package, current-vs-policy, candidate-factory, and advanced analytics work. Runtime
behavior was not changed. This handed off to Session 03, which is now complete.

Session 03 outcome: decision IDs are unique again. Robustness Scorecard V1 keeps
`DEC-2026-05-17-003`; Selection Engine V1 now uses `DEC-2026-05-17-006`; RM-611 is done; the duplicate
ID known issue is closed. Runtime behavior was not changed. This handed off to Session 04, which is now
complete.

Session 04 outcome: detailed specs now acknowledge the implemented file-first V1 decision package.
`reporting_outputs_spec.md` names the generated artifact chain, `candidate_comparison_spec.md` records
the downstream wiring boundary, and selection/action/monitoring/journal specs no longer describe
implemented neighbors as future-only. Runtime behavior was not changed. The next session should start
with Session 05 unless the user explicitly chooses another session.

Session 05 outcome: source and generator text defaults are cleaned to English in the main optimization
CLI, report messages, cache/data-loader logs, config UI error text, client profile notes, PDF report
builder, stress-factor assessment text, and two operational docs. The old one-off translation helper was
removed because it only preserved obsolete Russian source strings. Targeted source scans for literal
Cyrillic and common mojibake markers now pass. Existing generated outputs were not hand-edited; their
refresh and visual/readability QA remains tracked under `KI-2026-05-17-007` and should be handled with
a representative regeneration pass when data allows. The next session should start with Session 08
unless the user explicitly chooses another session.

Session 06–07 outcome: `decision_package_summary.txt` / `.json` project the full V1 artifact chain;
`report.txt` receives an appended decision-package section when present; PDF rebuild can emit
`Main portfolio_decision_package.pdf` when the summary exists. `RM-612` is done; `KI-2026-05-17-008`
is resolved for the compact summary surface (regenerated-folder QA may remain under `KI-2026-05-17-007`).

Future sessions must update this section when each milestone completes, noting what changed, what was
verified, and what remains.

## Context and Orientation

The repository is a Python portfolio decision-support and reporting system. The main user workflow is
still command/file driven:

- `run_optimization.py` creates the production policy portfolio and writes generated policy weights.
- `run_report.py` builds diagnostics and reports for a configured portfolio.
- `run_compare_variants.py` reads existing candidate output folders and writes the canonical comparison
  and downstream decision artifacts.

Important terms in this plan:

- "Main optimization" means the production policy path controlled by `run_optimization.py` and the
  portfolio construction policy spec. It is the path allowed to write authoritative policy weights.
- "Robust optimization" means robust mean-variance and robust scenario scripts that build alternative
  candidate portfolios for comparison. They are not policy replacements in this plan.
- "Decision package" means the user-facing set of generated artifacts around comparison, robustness,
  health, selection, action, monitoring, and decision journal outputs.
- "Current-vs-policy" means a workflow where a user-supplied current portfolio and the generated policy
  target are both available in one comparison context so No-Trade and action planning can be meaningful.
- "Generated outputs" are files under output folders such as Main portfolio, candidate folders, PDF
  output folders, caches, and report artifacts. Do not manually edit those as source.

The post-session audit found that the V1 decision pipeline is implemented, but several risks remain.
Session 02 synced the top-level current-status docs, and Session 03 fixed the duplicate decision ID.
Remaining risks are that user-facing text has mojibake/broken symbols, reports do not yet fully surface
the decision package, current-vs-policy workflows need hardening, candidate generation is not yet
orchestrated, and sensitivity/Pareto/regret analytics are missing.

## Documentation Sufficiency

Each future session can start from these documents without relying on prior chat memory:

- `AGENTS.md`
- `WORKFLOW.md`
- `RULES.md`
- `PLANS.md`
- this ExecPlan
- `docs/audits/2026-05-17_post_session_deep_system_audit.md`
- `docs/ROADMAP.md`
- owning specs for the session

If a session adds a new analytical or reporting block, create or update the owning spec first and
implement it in the later implementation session. The exception is a small docs-only cleanup where the
owning spec already exists and only stale wording is being corrected.

Before beginning any future session, run `git status --short`, read this `Progress` section, and
continue the first incomplete session unless the user explicitly requests a later session.

## Plan of Work

The work must proceed one session at a time. Do not implement multiple sessions in one chat unless the
user explicitly overrides this session boundary. Each session must update this ExecPlan before finishing,
marking progress, discoveries, decisions, and outcomes.

Session 02 synchronizes top-level documentation. Edit `README.md`, `AGENTS.md`, `SPEC.md`,
`PRODUCT.md`, and `ARCHITECTURE.md` so they no longer describe implemented V1 modules as target/TBD.
Keep the full product UI/workspace as future scope, but distinguish it from implemented file-first V1
artifacts.

Session 03 fixes decision-log and planning integrity. Resolve the duplicate `DEC-2026-05-17-003` in
`DECISIONS.md`, update references, update roadmap and this ExecPlan if needed, and close or revise the
known issue that tracks the duplicate decision ID.

Session 04 synchronizes detailed specs with the implemented decision pipeline. Update the reporting
outputs spec, candidate comparison spec, selection engine spec, action engine spec, monitoring spec, and
decision journal spec where they still imply future-only behavior or omit the implemented artifact chain.

Session 05 cleans language and text quality. Fix source and generator text so project artifacts default
to English and mojibake/broken symbols are removed from source docs, runner messages, report generators,
and robust optimizer scripts. Do not manually edit generated output files as source.

Session 06 specifies the reporting decision package. Define how reports and PDF-facing Markdown should
summarize comparison, robustness, health, selection, action, monitoring, and journal artifacts using
existing JSON outputs and without inventing new formulas.

Session 07 implements the reporting decision package. Add the report/PDF-facing summary and update
`run_compare_variants.py` so CLI output names all emitted downstream artifacts. Run focused report and
comparison verification.

Session 08 specifies the current-vs-policy workflow. Define the expected CLI/file workflow for making
both a current portfolio and policy target available in one comparison context. State exactly when
No-Trade is actionable and when it must be skipped with a clear reason.

Session 09 implements the current-vs-policy workflow. Add or harden the runner behavior and decision
messages so current-row availability is reliable and missing-current cases are explicit.

Session 10 specifies the candidate factory. Define a default orchestration layer that can run the
existing candidate scripts, record skipped/failed/unavailable candidates, and keep Main optimization as
the production policy path.

Session 11 implements the candidate factory. Build a CLI orchestrator around existing scripts without
copying their formulas. It should produce a factory run summary and refresh the canonical comparison.

Session 12 specifies a trade-off and model-risk layer. Define an artifact that explains what improves,
what worsens, what model/data warnings matter, and why the selected candidate is not simply "top score
wins".

Session 13 implements the trade-off and model-risk layer. Wire it into the decision package and decision
journal where appropriate, with focused tests.

Session 14 specifies Assumption Sensitivity. Define an artifact that evaluates whether the favored
candidate remains stable under deterministic assumption perturbations. This is diagnostic in V1.

Session 15 implements Assumption Sensitivity and wires it into the comparison pipeline with focused
tests.

Session 16 specifies Pareto/Dominance. Treat the user's "product domain analysis" request as
Pareto/Dominance unless the user later defines a different concept. Define an artifact that marks
dominated and non-dominated available candidates.

Session 17 implements Pareto/Dominance. It must not automatically change selection output unless the
spec is explicitly updated to do so.

Session 18 specifies Regret Analysis. Define an artifact that estimates scenario/regime opportunity
loss versus the best available candidate in the same run.

Session 19 implements Regret Analysis and optional report-package surfacing with focused tests.

Session 20 closes the plan. Close resolved known issues, update roadmap, changelog, decisions, and this
ExecPlan, then run the broad verification set recorded below.

## Concrete Steps

The generic kickoff for every future session is:

    Continue `docs/exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md`.
    Work on Session NN only: <session title>.
    Read `AGENTS.md`, `WORKFLOW.md`, `RULES.md`, `PLANS.md`,
    `docs/audits/2026-05-17_post_session_deep_system_audit.md`,
    `docs/ROADMAP.md`, this ExecPlan, and the owning specs for this session.
    Before editing, run `git status --short` and do not revert unrelated dirty files.

Recommended kickoff prompts:

Session 02:

    Continue `docs/exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md`.
    Work on Session 02 only: top-level documentation sync. Fix stale current-status wording in
    README.md, AGENTS.md, SPEC.md, PRODUCT.md, and ARCHITECTURE.md so implemented V1 decision modules
    are no longer described as target/TBD.

Session 03:

    Continue `docs/exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md`.
    Work on Session 03 only: decision log and planning integrity. Fix the duplicate decision ID,
    update references, and close or revise the known issue that tracks it.

Session 04:

    Continue `docs/exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md`.
    Work on Session 04 only: detailed specs sync for the implemented V1 decision pipeline.

Session 05:

    Continue `docs/exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md`.
    Work on Session 05 only: English and mojibake cleanup. Fix source/generator text, not generated
    outputs as source.

Session 06:

    Continue `docs/exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md`.
    Work on Session 06 only: specify the reporting decision package for report and PDF-facing surfaces.

Session 07:

    Continue `docs/exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md`.
    Work on Session 07 only: implement the reporting/PDF decision package and update comparison CLI
    output messaging.

Session 08:

    Continue `docs/exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md`.
    Work on Session 08 only: specify the current-vs-policy workflow and No-Trade actionability rules.

Session 09:

    Continue `docs/exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md`.
    Work on Session 09 only: implement the current-vs-policy workflow.

Session 10:

    Continue `docs/exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md`.
    Work on Session 10 only: specify the candidate factory/orchestration layer.

Session 11:

    Continue `docs/exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md`.
    Work on Session 11 only: implement the candidate factory/orchestrator around existing scripts.

Session 12:

    Continue `docs/exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md`.
    Work on Session 12 only: specify the trade-off and model-risk diagnostic layer.

Session 13:

    Continue `docs/exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md`.
    Work on Session 13 only: implement the trade-off and model-risk diagnostic layer.

Session 14:

    Continue `docs/exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md`.
    Work on Session 14 only: specify Assumption Sensitivity.

Session 15:

    Continue `docs/exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md`.
    Work on Session 15 only: implement Assumption Sensitivity.

Session 16:

    Continue `docs/exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md`.
    Work on Session 16 only: specify Pareto/Dominance.

Session 17:

    Continue `docs/exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md`.
    Work on Session 17 only: implement Pareto/Dominance.

Session 18:

    Continue `docs/exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md`.
    Work on Session 18 only: specify Regret Analysis.

Session 19:

    Continue `docs/exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md`.
    Work on Session 19 only: implement Regret Analysis.

Session 20:

    Continue `docs/exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md`.
    Work on Session 20 only: final integration and closure for the post-audit plan.

## Validation and Acceptance

Every session must finish with verification appropriate to its scope.

Docs-only sessions must run:

    python scripts/verify_docs.py

If `python` is not available in the local shell, use the project runtime Python available in the Codex
desktop environment or the active virtual environment.

Docs sync sessions must also run targeted stale-reference searches with `rg`, such as searches for
implemented modules still being described as "TBD", "future", or "target-only" in source-of-truth docs.

Implementation sessions must run focused tests for the changed modules and the existing decision
pipeline tests that can be affected. For example, selection/action workflow changes should run
selection, action, and candidate comparison tests. New analytics must add focused tests for their new
artifact and at least one integration test proving the artifact is emitted by the pipeline.

The final closure session must run documentation verification, all new focused tests, relevant existing
pipeline tests, and one smoke comparison/report command if runtime dependencies and data availability
allow it. If a smoke command cannot run because data/network/cache requirements are unavailable, record
the blocker in `Outcomes & Retrospective`.

Acceptance for the whole plan:

- Root docs and detailed specs no longer contradict the implemented V1 decision pipeline.
- Duplicate decision IDs are fixed or superseded with unambiguous references.
- User-facing source/generator text is English and no obvious mojibake remains in source.
- Reports include a compact decision package drawn from existing artifacts.
- No-Trade behavior is actionable only when current and target weights are both available.
- Candidate generation can be orchestrated and summarized before comparison.
- Trade-off/model-risk, Assumption Sensitivity, Pareto/Dominance, and Regret Analysis artifacts exist
  with focused tests.
- Main optimization remains the production policy path; robust optimization remains candidate/benchmark
  unless a later accepted decision changes that.

## Idempotence and Recovery

This plan is safe to resume from any future chat. Always read `Progress`, run `git status --short`, and
continue the first incomplete session unless the user explicitly chooses another one. Do not revert
unrelated dirty files. Generated outputs may change during smoke runs, but they should not be treated as
source unless the session explicitly targets generated artifacts.

If a future session fails mid-way, leave `Progress` with a partial entry that states what is done, what
remains, and which command failed. If an implementation creates a new artifact and tests fail, keep the
spec and test evidence in the plan so the next session can resume from the failure rather than restarting.

If a behavior decision conflicts with this plan, record the new decision in `DECISIONS.md`, update this
ExecPlan's `Decision Log`, and update the owning spec before code changes.

## Artifacts and Notes

Current completed baseline before this plan:

- `candidate_comparison.json`
- `robustness_scorecard.json`
- `portfolio_health_score.json`
- `selection_decision.json`
- `action_plan.json`
- `monitoring_diff.json`
- `decision_journal.json`

Known active issue IDs relevant to this plan:

- `KI-2026-05-17-004`: partial utility UI status is under-described.
- `KI-2026-05-17-007`: regenerated representative outputs still need language/readability QA.
- `KI-2026-05-17-008`: report surfaces still lag new decision artifacts.

The current audit finding IDs for this plan are PSA-001 through PSA-013 in
`docs/audits/2026-05-17_post_session_deep_system_audit.md`.

## Interfaces and Dependencies

Use existing Python modules and project helpers. Do not introduce new external dependencies for these
sessions unless the relevant spec session records why the existing stack is insufficient.

New artifacts should follow the existing pattern:

- JSON artifact with `schema_version`, run metadata where useful, candidate identifiers, warnings, and
  machine-readable fields.
- TXT artifact with a concise human-readable summary.
- Pipeline wiring from the existing comparison/decision package path unless the owning spec explicitly
  chooses a different placement.
- Focused tests under `tests/`.
- Output contracts documented in `OUTPUTS.md` and the owning spec.

For future analytics, use these artifact names unless a spec session records a better name:

- `tradeoff_explanation.json` and `model_risk_diagnostics.json` may be separate artifacts or one combined
  artifact if the spec proves that is clearer.
- `assumption_sensitivity.json` and `assumption_sensitivity.txt`.
- `pareto_dominance.json` and `pareto_dominance.txt`.
- `regret_analysis.json` and `regret_analysis.txt`.

Default integration point is the existing comparison pipeline centered on `src/candidate_comparison.py`,
because that module already emits the V1 decision package. If a later session chooses a different
integration point, it must explain why and add regression tests proving the existing artifacts still
emit correctly.

Revision note, 2026-05-17: Initial plan created from the user's requested session order and the
post-session audit. It creates the handoff spine for Sessions 02-20 and does not change runtime behavior.

Revision note, 2026-05-17: Session 02 completed the top-level documentation sync and closed
`KI-2026-05-17-005`. At that point, the remaining handoff started at Session 03.

Revision note, 2026-05-17: Session 03 completed the decision-log integrity cleanup, closed
`KI-2026-05-17-006`, and moved the remaining handoff to Session 04.

Revision note, 2026-05-17: Session 04 completed the detailed specs sync for the implemented V1
decision-package chain. It moved the remaining handoff to Session 05 and left report/PDF decision
package surfacing open for Sessions 06-07.

Revision note, 2026-05-17: Session 05 completed source/generator English and mojibake cleanup, left
generated-output refresh/QA tracked in `KI-2026-05-17-007`, and moved the remaining handoff to Session
06.
