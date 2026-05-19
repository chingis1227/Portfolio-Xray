# Portfolio-First Transition Plan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.
This document follows `PLANS.md` at the repository root.

## Purpose / Big Picture

The project must stop treating generated policy optimization as the first thing a user sees. The
intended product workflow is diagnostic-first: a user supplies or selects an `analysis_subject`, the
system diagnoses that portfolio first, and only then builds alternatives for comparison. After this
plan is complete, the main file-first workflow will answer the user's practical question: "Should I
keep, improve, rebalance, or rethink the portfolio I started with?"

The old policy optimizer is preserved because it contains useful investment-policy infrastructure.
It is not deleted, but it is removed from the default portfolio-first path and treated as legacy,
archived, or experimental infrastructure until a future canonical spec explicitly reactivates it as
an optional candidate generator.

## Progress

- [x] (2026-05-18) Session 01 started from the user's approved portfolio-first transition plan and
  read `RULES.md`, `WORKFLOW.md`, `PLANS.md`, the roadmap, known issues, changelog, and ExecPlan
  register.
- [x] (2026-05-18) Session 01 created this active ExecPlan and recorded the central architecture
  conflict: old mental model `policy first`; new mental model `analysis_subject first`.
- [x] (2026-05-18) Session 01 updated project memory so the next session can start from this file:
  ExecPlan register, roadmap, known issues, decisions, and changelog.
- [x] (2026-05-18) Session 01 verification passed: `.\.venv\Scripts\python.exe scripts\verify_docs.py`
  returned `docs verification: OK`.
- [x] (2026-05-18) Session 02 created
  [portfolio_review_workflow_spec.md](../specs/portfolio_review_workflow_spec.md), made
  `analysis_subject` the binding portfolio-first baseline, and updated top-level source-of-truth
  links in `RULES.md`, `SPEC.md`, `README.md`, `ARCHITECTURE.md`, `PRODUCT.md`, `OUTPUTS.md`,
  `GLOSSARY.md`, `TESTING.md`, the spec index, roadmap, known issues, decisions, changelog, and
  ExecPlan register.
- [x] (2026-05-18) Session 03 added explicit `analysis_subject` config/schema support, resolver
  output in `analysis_setup.analysis_subject`, projection in `input_assumptions`, config example
  docs, and focused tests for `current_portfolio`, `model_portfolio`, `universe_baseline`, invalid
  subject weights, and stale generated-weight merge prevention.
- [x] (2026-05-18) Session 03 verification passed: focused input/config tests returned `19 passed`
  and `.\.venv\Scripts\python.exe scripts\verify_docs.py` returned `docs verification: OK`.
- [x] (2026-05-18) Session 04 added `run_report.py --materialize-analysis-subject`, resolving
  current/model/universe-baseline subject weights into `{output_dir_final}/analysis_subject/` and
  marking the sidecar `analysis_portfolio` as the subject role instead of a fixed-report portfolio.
- [x] (2026-05-18) Session 05 added `run_portfolio_review.py` and
  `src/portfolio_review_workflow.py`, proving by dry-run tests that the default plan materializes
  `analysis_subject` before candidate generation and does not call `run_optimization.py`.
- [x] (2026-05-18) Session 05 documentation verification passed:
  `.\.venv\Scripts\python.exe scripts\verify_docs.py` returned `docs verification: OK`.
- [x] (2026-05-18) Session 06 centered candidate comparison and downstream decision artifacts on
  `analysis_subject`: comparison adds the subject row, Selection/No-Trade prefer it as baseline,
  Action deltas use it, and Monitoring / Decision Journal identify it before legacy `current`.
- [x] (2026-05-18) Session 07 isolated old policy language: `AGENTS.md`, `README.md`,
  `docs/operational_runbook.md`, candidate/input/reporting specs, `TESTING.md`, and CLI help now
  route the normal path through `run_portfolio_review.py` and label `run_optimization.py` /
  `run_mvp_workflow.py` as legacy compatibility.
- [x] (2026-05-18) Session 08 updated decision-package report language, config examples, and
  generated-output QA so summaries name `analysis_subject` as the starting portfolio and scored rows
  as candidate alternatives.
- [x] (2026-05-18) Session 09 added offline end-to-end coverage for `current_portfolio`,
  `model_portfolio`, and `universe_baseline`, verified the subject-first workflow and decision
  package chain, removed the active known issue, marked RM-808 done, and closed this transition.
- [x] (2026-05-18) Session 09 verification passed: focused portfolio-first E2E, adjacent
  materialization/orchestrator tests, decision-chain tests, docs verification, and full pytest
  (`486 passed`) using a cache basetemp outside the OneDrive workspace.

## Surprises & Discoveries

- Observation: The divergence is contractual, not isolated to one function.
  Evidence: `SPEC.md`, `ARCHITECTURE.md`, `README.md`, and `docs/operational_runbook.md` currently
  orient the main file-first path around `run_optimization.py` and generated policy weights, while
  `PRODUCT.md` says the product should be diagnostic-first and `docs/specs/input_assumptions_spec.md`
  already describes target semantics for user-current and universe-only starts.

- Observation: The existing docs already contain the seed of the new model but not a binding
  implementation contract.
  Evidence: `docs/specs/input_assumptions_spec.md` mentions target MVP semantics where tickers
  without weights become an equal-weight initial baseline, but it also says current repo compatibility
  remains optimizer-first until `SPEC.md` and code are updated.

- Observation: Existing generated and cache files were dirty before Session 01.
  Evidence: `git status --short` showed modified `src/__pycache__/*.pyc` files and untracked
  generated portfolio folders. Session 01 did not touch those paths.

- Observation: Session 02 needed to distinguish a binding workflow contract from implemented runtime
  behavior to avoid overclaiming.
  Evidence: `README.md`, `SPEC.md`, `ARCHITECTURE.md`, and `OUTPUTS.md` still described runnable
  compatibility commands centered on `run_optimization.py`; the new spec marks those commands as
  legacy/compatibility while later sessions implement the portfolio-first resolver and orchestrator.

- Observation: The existing `analysis_setup` contract already had an `analysis_portfolio` block, but
  that block also carries legacy "what this report run actually calculated" semantics.
  Evidence: `run_report.py` passes actual report weights into `build_analysis_setup`, and
  `run_optimization.py` passes generated policy weights. Session 03 therefore added a separate
  `analysis_subject` object instead of renaming or overloading `analysis_portfolio`.

- Observation: Generated `portfolio_weights.yml` could be merged by `load_validated_config` before
  a resolver had a chance to choose the portfolio-first subject.
  Evidence: `load_validated_config` loaded `{output_dir_final}/portfolio_weights.yml` whenever no
  fixed user weights were detected. Session 03 treats an explicit `analysis_subject` as user fixed
  intent so stale generated weights are not merged over it.

- Observation: The existing report pipeline was already folder-parameterized enough to materialize a
  subject without duplicating report logic.
  Evidence: `run_portfolio_report_for_weights` accepts explicit weights plus output directories, so
  Session 04 added a subject resolver wrapper and sidecar CLI instead of creating a second report
  implementation.

- Observation: The existing MVP workflow wrapper was policy-oriented enough that reusing it directly
  would keep the old mental model visible.
  Evidence: `src/mvp_workflow.py` includes policy-only and policy-current modes and normally plans
  `run_optimization.py`; Session 05 therefore added a separate `src/portfolio_review_workflow.py`
  wrapper for the `analysis_subject`-first path.

- Observation: Candidate factory profiles already exclude the legacy policy row.
  Evidence: `src/candidate_factory.py` defines `POLICY_EXCLUDED_IDS = {"policy", "current"}` and
  default profiles are script-backed candidate ids, so the Session 05 orchestrator can call
  `run_candidate_factory.py --then-compare` without adding `run_optimization.py`.

- Observation: The stale policy-first risk was strongest in operator guidance, not in the new
  orchestrator.
  Evidence: Before Session 07, `AGENTS.md` still listed `python run_optimization.py` then
  `python run_report.py` as the main flow, `docs/operational_runbook.md` taught first and recurring
  runs through `run_optimization.py`, and `run_mvp_workflow.py --help` described the policy path
  without calling it legacy.

- Observation: The report-facing decision package still carried the old comparison story after the
  subject-centered JSON artifacts existed.
  Evidence: Before Session 08, `src/decision_package_reporting.py` rendered comparison highlights by
  iterating `policy` and `current`, used "Top candidates by health rank", and wrote "Versus current"
  in the Selection summary. Session 08 changed the summary to prefer the `analysis_subject` baseline
  and added generated-output QA markers for "Starting portfolio" and "Candidate alternatives".

- Observation: Full pytest needs a non-OneDrive basetemp on this Windows desktop when prior temp
  folders are locked.
  Evidence: Session 09 full pytest with `tmp\pytest_portfolio_first_session_09_full` hit
  `PermissionError` during pytest temp cleanup; rerunning with
  `C:\Users\ShumeikoYe\.cache\codex-pytest-temp-portfolio-first-session09-full2` passed all tests.

## Decision Log

- Decision: The new central object is named `analysis_subject`.
  Rationale: The user explicitly chose this name to mean the portfolio diagnosed first. Using one
  stable term prevents future agents from drifting back to `policy` as the implied starting object.
  Date/Author: 2026-05-18 / User and Codex.

- Decision: The default workflow must not present any optimization result before
  `analysis_subject` diagnostics exist.
  Rationale: The product is a portfolio review and decision-support system. A user must first see
  what the starting portfolio is and how it behaves before alternatives are generated or scored.
  Date/Author: 2026-05-18 / User and Codex.

- Decision: The old policy engine is preserved but removed from the default portfolio-first path.
  Rationale: The code may be useful later, but the old policy-first contract caused the architecture
  drift this plan is correcting. Reintroducing it as a default or optional candidate requires a future
  canonical spec.
  Date/Author: 2026-05-18 / User and Codex.

- Decision: Work remains file-first; UI is not part of this transition.
  Rationale: The immediate defect is the source-of-truth workflow order, not the presence or absence
  of a graphical interface.
  Date/Author: 2026-05-18 / User and Codex.

- Decision: Session 02 docs must label existing policy-first commands as compatibility behavior, not
  as the new default workflow.
  Rationale: The code still exposes `run_optimization.py`, but the source-of-truth correction must
  stop teaching generated policy optimization as the user's starting portfolio. Explicit
  compatibility wording keeps the docs truthful until Sessions 03-09 implement the new runtime path.
  Date/Author: 2026-05-18 / Codex.

- Decision: Keep `analysis_subject` separate from the legacy `analysis_portfolio` block.
  Rationale: During the transition, old entrypoints may still calculate a generated policy or fixed
  report portfolio, while the portfolio-first contract needs a stable subject baseline that is not
  inferred from generated policy weights. Keeping both fields avoids a silent behavior change and
  gives Session 04 a clear subject to materialize.
  Date/Author: 2026-05-18 / Codex.

- Decision: Explicit `analysis_subject` config maps to runtime report weights for Session 03.
  Rationale: Current/model subjects need their own user weights, and universe-baseline subjects need
  system-created equal weights. Mapping those into `PortfolioConfig.weights` with distinct
  `weights_source` values lets existing report code diagnose explicit subjects without treating them
  as optimizer outputs.
  Date/Author: 2026-05-18 / Codex.

- Decision: Portfolio-first report summaries must use "Starting portfolio" for `analysis_subject`
  and "Candidate alternatives" for scored non-baseline rows.
  Rationale: The generated JSON contract already identifies `analysis_subject` as the comparison
  baseline, but report/PDF-facing English needs the same story so users do not read policy/current
  compatibility rows as the main workflow.
  Date/Author: 2026-05-18 / Codex.

## Outcomes & Retrospective

Session 01 outcome: project memory now has an active portfolio-first transition handoff. The plan
records the architecture conflict, the approved new mental model, the product invariant that
diagnostics must precede optimization results, and the rule that `run_optimization.py` is preserved
but removed from the default path. `DEC-2026-05-18-001` records the project-level decision. No
runtime behavior changed in this session.

Session 02 outcome: the portfolio-first contract now has an owning spec:
`docs/specs/portfolio_review_workflow_spec.md`. Top-level source-of-truth maps point to it, and the
docs distinguish the binding `analysis_subject` workflow from legacy policy-first compatibility
commands. No runtime behavior changed in this session; Session 03 remains the first input/resolver
implementation step.

Session 03 outcome: runtime input resolution now has an explicit `analysis_subject` contract.
`PortfolioConfig` accepts the subject object, `build_analysis_setup` exports
`analysis_setup.analysis_subject`, `input_assumptions` projects a reporting summary, and explicit
subjects prevent stale generated `portfolio_weights.yml` from replacing the subject. This session
does not yet create `{output_dir_final}/analysis_subject/`; Session 04 owns subject diagnostics
materialization.

Session 04 outcome: the report pipeline can now materialize `analysis_subject` diagnostics before
candidates with `run_report.py --materialize-analysis-subject`. The sidecar writes to
`{output_dir_final}/analysis_subject/`, uses resolved subject weights for `current_portfolio`,
`model_portfolio`, and `universe_baseline`, and records the analyzed portfolio role as the subject
role in `analysis_setup.analysis_portfolio`. Session 05 owns the orchestrator that will call this
before candidate generation.

Session 05 outcome: the file-first portfolio review path now has a dedicated entrypoint:
`run_portfolio_review.py`. It plans `run_report.py --materialize-analysis-subject` first, then the
non-policy candidate factory with optional comparison, then PDF-style report rebuild unless skipped.
Focused tests prove the default plan order and that `run_optimization.py` is not present in the
default command list. Session 06 follows this by updating comparison and decision artifacts to treat
`analysis_subject` as the baseline.

Session 06 outcome: comparison and decision artifacts now have a subject-centered baseline.
`candidate_comparison.json` includes `analysis_subject` from `{output_dir_final}/analysis_subject/`
when materialized. `selection_decision.json` exposes `baseline_candidate_id` and disables the legacy
policy default when that baseline exists. `action_plan.json` writes baseline fields and calculates
deltas from the subject; monitoring snapshots prefer `analysis_subject` as the primary profile; and
`decision_journal.json` records the diagnosed subject and expected improvement versus that baseline.
Legacy `current` fallback remains for current-vs-policy compatibility.

Session 07 outcome: user-facing docs and help text no longer teach generated policy optimization as
the default starting command. `AGENTS.md`, `README.md`, and the operational runbook now point first to
`run_portfolio_review.py`; `run_optimization.py` and `run_mvp_workflow.py` are labeled legacy
compatibility in docs and argparse help; candidate/input/reporting specs describe policy outputs as
legacy or compatibility surfaces. The old policy engine remains callable and tested infrastructure.

Session 08 outcome: report-facing decision-package summaries now tell the portfolio-first story.
`decision_package_summary.txt` starts comparison highlights from the selected or comparison-declared
baseline, preferring `analysis_subject`, labels it as the starting portfolio, and labels scored
non-baseline rows as candidate alternatives. `config.yml.example` includes portfolio-first current
and model subject examples, generated-output QA has story marker checks, and reporting specs/project
memory point Session 09 to offline end-to-end coverage and transition closure.

Session 09 outcome: the portfolio-first transition is closed. `tests/test_portfolio_first_e2e_offline.py`
now runs the synthetic offline path for current, model, and universe-baseline subjects: it verifies
the `run_portfolio_review.py` plan materializes `analysis_subject` before candidates and excludes
`run_optimization.py`, then writes comparison, scorecard, Selection, Action, Monitoring, Journal, and
decision-package artifacts from synthetic subject/candidate snapshots without network access. Project
memory marks RM-808 done, removes the active policy-first known issue, and changes this plan to
completed.

## Context and Orientation

The current repository is a Python portfolio decision-support system. It loads configuration from
`config.yml`, runs reports with `run_report.py`, compares candidate portfolios with
`run_compare_variants.py`, and has a completed file-first MVP decision artifact chain. The old main
path was built around `run_optimization.py`, which creates generated policy weights in
`portfolio_weights.yml` and then runs reports from those weights.

In this plan, `analysis_subject` means the portfolio that is analyzed first. It has three approved
types:

- `current_portfolio`: the user provides real current tickers and weights.
- `model_portfolio`: the user provides a desired or model portfolio with tickers and weights.
- `universe_baseline`: the user provides only tickers; the system builds an equal-weight initial
  baseline for diagnostic purposes.

The new workflow is:

    analysis_subject
    -> diagnostics / Portfolio X-Ray
    -> stress / macro / risk analysis
    -> generate allowed candidates
    -> compare analysis_subject vs candidates
    -> decide: keep / rebalance / review / no-trade
    -> decision package / report

The old mental model was:

    policy optimization
    -> generated policy portfolio
    -> report diagnostics
    -> compare with other optimized portfolios

That old mental model is no longer the main product contract.

## Plan of Work

Session 02 creates the planned `portfolio_review_workflow_spec` file under `docs/specs/` and updates
top-level source of truth documents so portfolio-first is a binding workflow contract. It must define
`analysis_subject`, the three subject types, the diagnostics-before-candidates rule, and the legacy
status of the old policy engine.

Session 03 updates config and analysis setup semantics. It adds the canonical `analysis_subject`
config object, maps existing compatibility fields into it, and updates tests so the runtime always
knows which portfolio is analyzed first.

Session 04 updates report materialization. It creates a dedicated materialization path such as
`{output_dir_final}/analysis_subject/`, builds diagnostics for current, model, and universe-baseline
subjects, and preserves old current sidecar behavior only as a compatibility alias.

Session 05 adds the new file-first orchestrator, expected to be `run_portfolio_review.py`. The default
order resolves `analysis_subject`, materializes and diagnoses it, generates allowed non-policy
candidates, runs candidate diagnostics where applicable, compares against the subject, and emits
decision/report artifacts. The default path must not call `run_optimization.py`.

Session 06 updates comparison and decision logic. Candidate comparison must be centered on
`analysis_subject` versus candidates. Selection, no-trade, action, and status artifacts must answer
whether to keep, improve, rebalance, or rethink the starting portfolio. The old
`current_vs_policy_status.json` remains compatibility-only.

Session 07 isolates legacy policy language. User-facing docs and help text must no longer teach
`run_optimization.py` as the default starting command. The code and tests remain, but portfolio-first
acceptance must not depend on policy-first behavior.

Session 08 updates report language, examples, config examples, and generated-output QA. The generated
story must say that `analysis_subject` is the first analyzed portfolio and candidates are
alternatives.

Session 09 added offline end-to-end tests for `current_portfolio`, `model_portfolio`, and
`universe_baseline`, ran focused and adjacent verification, and closed this ExecPlan with the new
contract working.

## Concrete Steps

Use a new chat for each numbered session unless the user explicitly changes the session boundary
rule. At the start of every session, read this file, run `git status --short`, and inspect only the
files owned by that session before editing.

Session 02 should run from the repository root:

    .\.venv\Scripts\python.exe scripts\verify_docs.py

Session 03 and later code sessions should run focused tests first. Use workspace-local pytest temp
directories when possible, for example:

    .\.venv\Scripts\python.exe -m pytest tests\test_input_assumptions.py -q --basetemp='tmp\pytest_portfolio_first_session_03'

Session 05 should include a dry-run or plan-building test proving the new orchestrator order and
proving that the default path does not call `run_optimization.py`.

Session 05 verification:

    .\.venv\Scripts\python.exe -m pytest tests\test_portfolio_review_workflow.py -q --basetemp='tmp\pytest_portfolio_first_session_05_workflow'
    4 passed

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    .\.venv\Scripts\python.exe -m pytest tests\test_docs_links.py -q --basetemp='tmp\pytest_portfolio_first_session_07_docs_links'
    6 passed

Session 07 verification:

    .\.venv\Scripts\python.exe -m py_compile run_optimization.py run_mvp_workflow.py run_report.py
    passed

    .\.venv\Scripts\python.exe run_optimization.py --help
    output labels the command "Legacy policy optimization compatibility flow" and points to
    run_portfolio_review.py for the portfolio-first workflow.

    .\.venv\Scripts\python.exe run_mvp_workflow.py --help
    output labels the command "legacy file-first MVP policy workflow" and points to
    run_portfolio_review.py for portfolio-first review.

    .\.venv\Scripts\python.exe run_report.py --help
    output includes --materialize-analysis-subject.

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    rg "Run the main production flow|Main policy workflow|Full decision-support run \(recommended\)|default policy|This is the default policy workflow|main policy portfolio|normal production weights|CLI/file-driven portfolio optimization|normal first step" AGENTS.md README.md SPEC.md ARCHITECTURE.md OUTPUTS.md TESTING.md docs run_optimization.py run_mvp_workflow.py run_report.py
    Remaining hits were contextual in the historical audit and this ExecPlan; no user-facing command
    doc in the active top-level maps teaches policy optimization as the default first step.

Session 08 verification:

    .\.venv\Scripts\python.exe -m pytest tests\test_decision_package_reporting.py tests\test_generated_output_language.py -q --basetemp='tmp\pytest_portfolio_first_session_08_summary'
    8 passed

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

Session 09 ran the new offline end-to-end tests and broadened verification according to
`TESTING.md`.

## Validation and Acceptance

The full plan is accepted because a user can run the new file-first portfolio review command and
observe that the first diagnostic artifacts describe `analysis_subject`, not a generated policy
portfolio. Candidate comparison and decision artifacts must compare that subject against allowed
candidates. The old policy engine must remain callable as legacy infrastructure but must not appear
as the default starting portfolio or default candidate.

For Session 01 specifically, acceptance is:

- this ExecPlan exists and is registered as active;
- `docs/ROADMAP.md` contains a portfolio-first transition phase;
- `KNOWN_ISSUES.md` tracks the unresolved policy-first architecture conflict;
- `DECISIONS.md` records the portfolio-first workflow and legacy policy engine boundary;
- `CHANGELOG.md` records the new active transition plan;
- documentation verification passes.

For Session 02 specifically, acceptance is:

- [portfolio_review_workflow_spec.md](../specs/portfolio_review_workflow_spec.md) exists and defines
  `analysis_subject`, `current_portfolio`, `model_portfolio`, `universe_baseline`,
  diagnostics-before-candidates ordering, and the old policy engine boundary;
- top-level source-of-truth maps link to the new spec;
- roadmap and project memory mark Session 02 complete and Session 03 next;
- documentation verification passes.

## Idempotence and Recovery

The plan is additive at first. If a later session is interrupted, do not restart from scratch. Read
the Progress section, inspect the session-owned files, and continue from the first unchecked item.
Do not delete the old policy engine. Do not treat generated outputs, caches, or dirty unrelated files
as source changes unless a session explicitly targets them.

## Artifacts and Notes

Session 01 verification:

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

Session 02 verification:

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

Session 03 focused verification:

    .\.venv\Scripts\python.exe -m pytest tests\test_input_assumptions.py tests\test_config_weights_sync.py -q --basetemp='tmp\pytest_portfolio_first_session_03'
    19 passed

Session 03 documentation verification:

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

Session 05 focused verification:

    .\.venv\Scripts\python.exe -m pytest tests\test_portfolio_review_workflow.py -q --basetemp='tmp\pytest_portfolio_first_session_05_workflow'
    4 passed

Session 05 documentation verification:

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

Session 09 focused verification:

    .\.venv\Scripts\python.exe -m pytest tests\test_portfolio_first_e2e_offline.py -q --basetemp='tmp\pytest_portfolio_first_session_09_e2e'
    3 passed

Session 09 adjacent verification:

    .\.venv\Scripts\python.exe -m pytest tests\test_portfolio_first_e2e_offline.py tests\test_portfolio_review_workflow.py tests\test_analysis_subject_materialization.py -q --basetemp='tmp\pytest_portfolio_first_session_09_adjacent'
    11 passed

Session 09 decision-chain verification:

    .\.venv\Scripts\python.exe -m pytest tests\test_candidate_comparison.py tests\test_selection_engine.py tests\test_action_engine.py tests\test_monitoring.py tests\test_decision_journal.py tests\test_decision_package_reporting.py tests\test_generated_output_language.py tests\test_mvp_pipeline_offline.py -q --basetemp='tmp\pytest_portfolio_first_session_09_decision_chain'
    59 passed

Session 09 full verification:

    .\.venv\Scripts\python.exe -m pytest -q --basetemp='C:\Users\ShumeikoYe\.cache\codex-pytest-temp-portfolio-first-session09-full2'
    486 passed

Session 09 documentation verification:

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

Session 02 stale wording search:

    rg "Run the main production flow|Main policy workflow|policy-first|normal first step|default policy"

Remaining hits were contextual transition/legacy wording in this ExecPlan, the roadmap, `SPEC.md`,
`README.md`, `ARCHITECTURE.md`, and `portfolio_review_workflow_spec.md`; no hit teaches
`run_optimization.py` as the normal portfolio-first first step in the edited top-level maps.

## Interfaces and Dependencies

The new stable user-facing concept is `analysis_subject`. Later sessions must expose it through
configuration, `analysis_setup`, report metadata, comparison artifacts, and generated decision
outputs. The old `analysis_mode`, `current_weights`, `weights`, and `portfolio_weights.yml` fields
are compatibility inputs or outputs until the owning specs say otherwise.

Revision note, 2026-05-18: Initial active plan created from the user's approved portfolio-first
transition plan. This revision records the source-of-truth correction and the Session 01 project
memory updates.

Revision note, 2026-05-18 Session 02: Added the canonical portfolio review workflow spec and updated
source-of-truth routing so later sessions implement `analysis_subject` first rather than policy first.

Revision note, 2026-05-18 Session 03: Added the runtime `analysis_subject` input contract and
resolver handoff. The plan now records why `analysis_subject` remains separate from legacy
`analysis_portfolio` during the transition and points Session 04 to subject diagnostics
materialization.

Revision note, 2026-05-18 Session 04: Added canonical `analysis_subject` report sidecar
materialization and focused tests. The next session is the portfolio-first orchestrator.

Revision note, 2026-05-18 Session 05: Added the portfolio-first orchestrator and focused dry-run
tests. The next session is subject-centered comparison and decision artifacts.

Revision note, 2026-05-18 Session 06: Added the subject-centered comparison and decision baseline
across comparison, Selection/No-Trade, Action, Monitoring, and Decision Journal. The next session is
legacy policy language isolation in docs and help text.

Revision note, 2026-05-18 Session 07: Isolated legacy policy language in user-facing docs and CLI
help. The next session is generated report language, examples, and output QA for the
`analysis_subject`-first story.

Revision note, 2026-05-18 Session 08: Updated decision-package report wording, generated-output QA,
and config examples so generated summaries present `analysis_subject` as the starting portfolio and
candidates as alternatives. The next session is offline end-to-end coverage and transition closure.

Revision note, 2026-05-18 Session 09: Added offline portfolio-first end-to-end coverage across all
three subject types and closed the transition. The plan is now completed; no portfolio-first session
remains active.
