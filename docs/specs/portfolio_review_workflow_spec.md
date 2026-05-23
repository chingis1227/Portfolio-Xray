# Portfolio Review Workflow Specification

This document owns the portfolio-first review workflow for Portfolio X-Ray / Portfolio MRI.
It defines the binding product workflow that starts from `analysis_subject`, diagnoses that
portfolio first, and only then builds and compares alternatives.

Implementation status: this is the canonical workflow contract for the portfolio-first transition.
Session 04 added subject diagnostics materialization through
`run_report.py --materialize-analysis-subject`; Session 05 added `run_portfolio_review.py` as the
portfolio-first orchestrator; Sessions 06-09 added subject-centered comparison/decision artifacts,
report wording, and offline end-to-end coverage.
Legacy policy-first entrypoints remain callable for compatibility, but they are not the default
portfolio-first product contract.

## Scope

This spec owns:

- the `analysis_subject` concept and supported subject types;
- the required order of the portfolio review workflow;
- the rule that diagnostics for `analysis_subject` must exist before candidate generation or
  decision artifacts are interpreted;
- the legacy boundary for the old policy optimizer in the portfolio-first path;
- handoff expectations for input resolution, materialization, comparison, decision artifacts,
  reporting language, and tests.

This spec does not own:

- metric formulas, return alignment, covariance, beta, drawdown, or rounding rules;
- stress scenario definitions, factor diagnostics, or macro regime formulas;
- candidate construction formulas;
- optimizer release status formulas or mandate gates;
- report rendering details outside workflow ordering and wording boundaries.

Those remain governed by their dedicated specs in this directory.

## Product Question

The portfolio-first workflow answers:

```text
Given the portfolio I started with, should I keep it, improve it, rebalance it, or rethink it?
```

The system must not answer that question by showing a generated policy optimization result first.
It must first show what the starting portfolio is, how it behaves, where its risks are, and how it
performs under the same metric, stress, factor, and reporting framework later used for alternatives.

## Core Concept: `analysis_subject`

`analysis_subject` is the portfolio diagnosed first in a review run.

It is the baseline for interpretation, comparison, Selection, No-Trade, Action Plan, Monitoring, and
Decision Journal outputs in the portfolio-first workflow. It is not automatically a generated policy
portfolio, and it is not inferred from the existence of `portfolio_weights.yml`.

Supported `analysis_subject.type` values:

| Type | Meaning | Required portfolio input | Weight source |
| --- | --- | --- | --- |
| `current_portfolio` | The user's real current allocation. | Tickers plus user weights. | User-supplied current weights. |
| `model_portfolio` | A user-specified target, model, or proposed allocation to diagnose before alternatives. | Tickers plus user weights. | User-supplied model weights. |
| `universe_baseline` | A ticker universe without user weights; the system builds an initial equal-weight diagnostic baseline. | Tickers only. | System-created equal weights for diagnostics. |

`universe_baseline` is a baseline, not a recommendation. Report, comparison, and decision text must
not describe it as a selected target unless a later formal decision artifact explicitly selects it
under a documented selection rule.

## Required Workflow Order

The portfolio-first order is:

```text
analysis_subject
-> validation and resolved assumptions
-> diagnostics / Portfolio X-Ray
-> stress / factor / macro / scenario diagnostics
-> allowed candidate generation
-> candidate diagnostics
-> comparison: analysis_subject versus candidates
-> decision: keep / rebalance / review / no-trade / data review
-> action plan, monitoring, journal, and report package
```

The current file-first orchestration entrypoint is:

```bash
python run_portfolio_review.py
```

It materializes `analysis_subject` diagnostics before invoking the non-policy candidate factory and
comparison path. Its default plan must not include `run_optimization.py`.

The invariant is simple: candidate generation, candidate comparison, and decision artifacts must not
be presented as the main review outcome until `analysis_subject` diagnostics are available or the run
has failed with a clear diagnostic blocker.

## Input Resolution Contract

Runtime input resolution is owned by [input_assumptions_spec.md](input_assumptions_spec.md). Session
03 adds the explicit `analysis_subject` config object and resolver. This workflow requires that the
resolved runtime setup expose:

- `analysis_subject.type`;
- a stable subject id, defaulting to `analysis_subject`;
- display name suitable for reports;
- ticker list;
- resolved weights, or an explicit blocker if weights cannot be resolved;
- `weight_source`;
- investor currency, benchmark, cash proxy, risk-free source, windows, and return frequency through
  the existing resolved assumptions contract;
- validation result with blocking errors, warnings, and compatibility notes.

Compatibility mapping during the transition:

| Existing input | Portfolio-first interpretation |
| --- | --- |
| `analysis_mode: analyze_current_weights` with `current_weights` | `analysis_subject.type = current_portfolio` |
| `analysis_mode: optimize_from_universe` with tickers and no subject object | Temporary legacy policy mode until Session 03 adds explicit resolution; target mapping is `universe_baseline` |
| legacy `weights` used for fixed report compatibility | Fixed-weight compatibility input, not automatically a policy target |
| generated `portfolio_weights.yml` | Legacy policy output, not default `analysis_subject` |

When explicit `analysis_subject` config exists, it takes priority over compatibility inference unless
the config is invalid.

## Diagnostics Contract

The report pipeline can materialize diagnostics for `analysis_subject` before candidates:

```bash
python run_report.py --materialize-analysis-subject
```

The canonical location is:

```text
{output_dir_final}/analysis_subject/
```

The materialized subject diagnostics must expose the same minimum evidence used for candidate review:

- `run_metadata.json` or equivalent metadata with `analysis_setup.analysis_subject`;
- primary-window snapshot metrics and weights;
- stress diagnostics where data permits;
- `portfolio_xray.json` or the equivalent X-Ray summary for the subject;
- clear warnings when any diagnostic degrades.

Session 04 implements this sidecar by running the existing report pipeline with resolved subject
weights and `analysis_setup.analysis_portfolio` mirrored to `analysis_subject`.

## Candidate Generation Boundary

Candidates are alternatives to compare against `analysis_subject`. They are not the starting
portfolio.

Allowed default candidate families in the portfolio-first path are benchmark, robust, and other
explicit comparison builders governed by [candidate_portfolios_spec.md](candidate_portfolios_spec.md)
and [candidate_factory_spec.md](candidate_factory_spec.md). Candidate generation must run only after
the subject diagnostics step succeeds or explicitly degrades in a reportable way.

The old policy optimizer is excluded from the default portfolio-first candidate set. A future
canonical spec may reintroduce it as an optional candidate generator, but until then it must not be
called by the default portfolio-first orchestrator and must not appear as a default recommended
candidate.

## Comparison And Decision Boundary

Portfolio-first comparison uses `analysis_subject` as the baseline row.

Required downstream behavior:

- candidate comparison must compare subject evidence against alternative candidate evidence;
- Selection and No-Trade must answer whether to keep the subject or move to an alternative;
- Action Plan must express deltas from subject weights to the favored target when a move is selected;
- Monitoring and Decision Journal must identify the diagnosed subject and the chosen outcome;
- decision package/report wording must not frame generated policy optimization as the user's starting
  portfolio.

The existing `current_vs_policy_status.json` workflow remains compatibility-only for the legacy
policy-vs-current path. It must not be treated as the portfolio-first status contract after the new
subject-centered comparison/status artifact is implemented.

## Legacy Policy Engine Boundary

`run_optimization.py` and the main policy construction modules remain in the repository. They may
continue to support historical tests, compatibility workflows, and future experimentation.

In the portfolio-first workflow:

- policy optimization is not the first visible result;
- `portfolio_weights.yml` is not default user input;
- generated policy weights are not the default `analysis_subject`;
- the default portfolio-first orchestrator must not call `run_optimization.py`;
- when `analysis_subject` diagnostics are available, root `policy` artifacts are legacy optional
  references only and must not be ranked or selected as default portfolio-first candidate evidence;
- `current_vs_policy_status.json` may still be written for compatibility, but portfolio-first runs
  must mark it as `workflow_profile: portfolio_first_review` and not surface it as the main workflow;
- user-facing docs and help text must describe policy optimization as legacy, compatibility, or
  explicitly optional infrastructure until a later accepted spec changes that status.

Deleting the policy engine is not part of this transition.

## Report Package And PDF Scope

After comparison and decision artifacts are written, the default portfolio-first orchestrator
rebuilds a **narrow** PDF subset only:

- `{output_dir_final}/decision_package_summary.txt` → `Main portfolio_decision_package.pdf`
- `{output_dir_final}/analysis_subject/` commentary, stress commentary, and weights (when present)
  → `analysis_subject_*` PDFs under `pdf files/`

It calls `rebuild_pdf_reports.py --portfolio-first` and does **not** refresh legacy Equal-Weight,
Risk-Parity, policy Main, or optimizer baseline variant PDFs on every review run.

Use `run_portfolio_review.py --legacy-full-pdf` (or bare `rebuild_pdf_reports.py`) when the full
legacy PDF suite must be regenerated from on-disk variant folders.

## Output And Artifact Direction

Later implementation sessions must align generated outputs with these roles:

| Role | Planned artifact direction |
| --- | --- |
| `analysis_subject` diagnostics | `{output_dir_final}/analysis_subject/` subject snapshots, metadata, X-Ray, and diagnostics |
| Candidate diagnostics | Existing candidate output folders, built only after subject diagnostics |
| Subject-centered comparison | `candidate_comparison.json` or successor fields identifying the subject baseline |
| Formal decision | `selection_decision.json` centered on subject versus candidates |
| Action | `action_plan.json` deltas from subject to favored target |
| Monitoring / journal | generated records that name the subject and outcome |

Output file names remain owned by [OUTPUTS.md](../../OUTPUTS.md) and specific output specs. This
workflow spec owns the role and order, not every file schema.

## Non-Goals

- Building a full UI or saved workspace system.
- Removing `run_optimization.py`.
- Changing portfolio metric formulas.
- Changing stress pass/fail or mandate release logic.
- Treating taxonomy validation as portfolio selection.
- Making any diagnostic score binding without an owning selection or policy spec.
- Automatically importing brokerage holdings.

## Implementation Sessions

The active transition plan stages this spec into runtime behavior:

- Session 03: add the `analysis_subject` input contract and resolver.
- Session 04: materialize diagnostics for `analysis_subject`.
- Session 05: add the portfolio-first orchestrator and keep `run_optimization.py` out of the default
  path.
- Session 06: center comparison, Selection, No-Trade, Action, Monitoring, and Journal on the subject.
- Session 07: isolate legacy policy language in docs and help text.
- Session 08: update generated report language and examples.
- Session 09: add offline end-to-end coverage and close the transition. Done.

## Tests And Verification

Each implementation session must add focused tests around its owned behavior. The completed
portfolio-first transition includes `tests/test_portfolio_first_e2e_offline.py`, which proves:

- `current_portfolio` resolves and is diagnosed before candidates;
- `model_portfolio` resolves and is diagnosed before candidates;
- `universe_baseline` resolves equal-weight diagnostic weights and is not described as a
  recommendation;
- the portfolio-first orchestrator does not call `run_optimization.py` by default;
- comparison and decision artifacts use `analysis_subject` as the baseline;
- legacy current-vs-policy artifacts remain compatibility-only.

Documentation-only changes to this spec require:

```text
python scripts/verify_docs.py
```

and a stale wording search for policy-first defaults when source-of-truth maps or user-facing command
sections are edited.

## Operational Model (Session 09 — RM-939)

The portfolio-first **workflow order** is implemented. The default CLI uses **core-run** scope.

### Command matrix (portfolio-first)

| Use case | Command |
| --- | --- |
| Default site/API review | `python run_portfolio_review.py` |
| Core menu (six candidates) | `python run_portfolio_review.py --mode core` |
| Full menu (16 candidates) | `python run_portfolio_review.py --mode full` |
| Resume interrupted full factory | `python run_portfolio_review.py --mode full --resume-candidates` |
| Subject only (skip factory) | `python run_portfolio_review.py --skip-candidates` |
| Explicit PDF (narrow subset) | `python run_portfolio_review.py --with-pdf` |
| Full legacy PDF suite | `python run_portfolio_review.py --legacy-full-pdf` |
| Export profile override | `python run_portfolio_review.py --output-profile full_report` |

Writes `output_manifest.json` under `output_dir_final`. Output policy: `src/output_policy.py`;
artifact map: [OUTPUTS.md](../../OUTPUTS.md).

| Topic | Behavior |
| --- | --- |
| End-to-end command | `run_portfolio_review.py` chains subject → factory → compare in `site_api` JSON/cache mode |
| **Core-run** (default) | `--mode core` → factory profile `core_v1`; factory `--execution-mode standard` (phased weights + lightweight_comparison); no PDF by default |
| **Full-run** | `--mode full` → factory profile `default_v1`; factory `--execution-mode standard` by default |
| **Full-run (legacy builders)** | `--mode full --execution-mode legacy_full` → subprocess `run_*.py` per candidate (parity/debug) |
| **Full-run recovery** | `--mode full --resume-candidates` passes factory `--resume` through the portfolio-first orchestrator |
| **Portfolio-first PDF export** | `--with-pdf` explicitly enables the narrow portfolio-first PDF rebuild after export-capable artifacts are written |
| Stale snapshots | Comparison marks non-matching `analysis_end` as `unavailable` |
| Partial menu | `candidate_comparison.json` includes `candidate_menu`; decision-package summary repeats scope and refresh commands |
| Long factory | Full rebuild can still take hours; use `--mode full --no-skip-existing` intentionally |

Factory resume is available from both `run_candidate_factory.py --resume` and
`run_portfolio_review.py --mode full --resume-candidates`. Advanced factory-only runs can opt into
parallel Phase 2 lightweight reports with `run_candidate_factory.py --execution-mode standard
--parallel-lightweight-reports`; portfolio-first review keeps the documented core/full mode
contract and does not enable that flag by default. Parallel candidate builders remain deferred.
See
[operational_runbook.md](../operational_runbook.md) and [candidate_factory_spec.md](candidate_factory_spec.md).

## Detailed Ownership

| Area | Source |
| --- | --- |
| Portfolio-first workflow order and `analysis_subject` role | This spec |
| Input resolution and assumptions | [input_assumptions_spec.md](input_assumptions_spec.md) |
| Output folders and generated-vs-source boundaries | [../../OUTPUTS.md](../../OUTPUTS.md) |
| Report artifact schema and rendering | [reporting_outputs_spec.md](reporting_outputs_spec.md) |
| Candidate builders and factory orchestration | [candidate_portfolios_spec.md](candidate_portfolios_spec.md), [candidate_factory_spec.md](candidate_factory_spec.md) |
| Candidate comparison | [candidate_comparison_spec.md](candidate_comparison_spec.md) |
| Selection and No-Trade | [selection_engine_spec.md](selection_engine_spec.md) |
| Action Plan | [action_engine_spec.md](action_engine_spec.md) |
| Monitoring and Decision Journal | [monitoring_spec.md](monitoring_spec.md), [decision_journal_spec.md](decision_journal_spec.md) |
| Legacy policy optimizer | [portfolio_construction_policy.md](portfolio_construction_policy.md), [production_workflow.md](production_workflow.md) |
| Active transition plan | [../exec_plans/2026-05-18_portfolio_first_transition_plan.md](../exec_plans/2026-05-18_portfolio_first_transition_plan.md) |
