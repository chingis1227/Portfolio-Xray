# Post-Session Deep System Audit

Date: 2026-05-17

Scope: full repository audit after Sessions 01-20 in
`docs/exec_plans/2026-05-17_project_development_session_plan.md`, including the Phase 6
Post-closure checks requested after the first audit and session plan.

This audit compares the current project against:

- `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`
- `docs/audits/2026-05-17_full_project_system_audit.md`
- the completed session plan and roadmap
- current code and generated artifact wiring
- current source-of-truth docs and module specs

Generated outputs were inspected only as evidence that the current pipeline emits the expected files.
They are not treated as source of truth.

## Executive Conclusion

Sessions 01-20 materially changed the project. The missing decision-support pipeline identified in the
first audit is no longer just a concept: the repository now has canonical candidate comparison,
robustness scoring, health scoring, selection/no-trade logic, an action plan, monitoring snapshots,
and a generated decision journal. These are implemented as file-first V1 artifacts and are wired from
`src/candidate_comparison.py`.

The next risk is not lack of core decision artifacts. The next risk is drift around them:

- top-level docs still describe several implemented modules as target/TBD;
- several detailed specs still use "future" wording for modules that now exist;
- report/PDF/user-facing surfaces do not yet consistently consume the new decision artifacts;
- source and generated text still need an English-only/text-quality pass because mojibake/broken
  symbols remain;
- roadmap and decision-log metadata have integrity issues;
- product-concept layers such as assumption sensitivity, Pareto/dominance, regret, and a real UI remain
  incomplete.

Recommended next stage: stabilize and integrate the new decision layer before adding major new
analytics. The highest-value next work is docs/status sync, reporting integration, mojibake cleanup,
current-vs-policy workflow hardening, and then the next analytical layers: assumption sensitivity,
Pareto/dominance, and regret.

## Method

Reviewed representative root docs, detailed specs, runner scripts, core modules, tests, and current
generated outputs. Main evidence points:

- Root docs: `README.md`, `AGENTS.md`, `SPEC.md`, `PRODUCT.md`, `ARCHITECTURE.md`, `OUTPUTS.md`,
  `TESTING.md`, `KNOWN_ISSUES.md`, `DECISIONS.md`, `CHANGELOG.md`.
- Planning docs: `docs/ROADMAP.md`,
  `docs/exec_plans/2026-05-17_project_development_session_plan.md`.
- Concept: `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`.
- Core post-session modules: `src/candidate_comparison.py`, `src/robustness_scorecard.py`,
  `src/portfolio_health_score.py`, `src/selection_engine.py`, `src/action_engine.py`,
  `src/monitoring.py`, `src/decision_journal.py`.
- Optimizer paths: `run_optimization.py`, `src/optimization.py`,
  `run_robust_mean_variance_constrained.py`, `src/robust_mv.py`,
  `run_robust_scenario_optimization.py`, `src/robust_scenario_optimization.py`.
- Specs: candidate comparison, robustness scorecard, health score, selection engine, action engine,
  monitoring, decision journal, robust MV, robust scenario optimization, reporting outputs, and
  portfolio construction policy specs.
- Generated evidence in `Main portfolio/`: comparison, robustness, health, selection, action,
  monitoring, and journal JSON/TXT files.

## Post-closure Checklist

| Item | Status | Audit result |
| --- | --- | --- |
| Post-closure 1: new full audit vs concept | Complete | This file is the new audit. Next-stage priorities are recorded below and linked from the roadmap. |
| Post-closure 2: identify weak or incomplete blocks | Complete as triage | Weak blocks are listed in Findings and translated into roadmap items. Implementation should happen in separate scoped sessions. |
| Post-closure 3: mojibake/broken-symbol/language sweep | Complete as triage | Remaining source/generator mojibake was found and registered as a known issue. Literal Cyrillic was not found in the non-generated source scan used for this audit, but a dedicated English-only acceptance pass is still needed. |
| Post-closure 4: Main vs robust optimizer review | Complete as audit decision | Current boundary is internally coherent: Main is the production policy optimizer; robust paths are candidate/benchmark builders unless a future spec changes that. Both still make sense to keep with explicit roles. |

## Current Implementation Map Vs Product Concept

| # | Product concept layer | Current status | Notes / remaining gap |
| --- | --- | --- | --- |
| 1 | Input & Assumptions Layer | Implemented V1 | `analysis_setup` and `input_assumptions` exist; config UI semantics improved. Full guided product input UX remains not done. |
| 2 | Portfolio X-Ray | Implemented | X-Ray diagnostics and report wiring exist. Some generated text still has encoding problems. |
| 3 | Stress Test Lab | Implemented | Historical/synthetic stress logic exists with canonical stress covariance docs. UI/lab experience remains not done. |
| 4 | Candidate Portfolio Factory | Partially implemented | Many candidate builders exist and comparison registry lists 18 candidates. A single orchestrated factory/workspace is still missing. |
| 5 | Optimization Engine | Implemented, split by role | Main optimizer is policy production; robust optimizers are candidate/benchmark paths. Boundary is coherent but should stay explicit. |
| 6 | Strategy Backtest | Implemented | Backtest/report artifacts exist. No major post-session gap found in this audit. |
| 7 | Scenario/Stress Evaluation | Implemented | Stress outputs feed comparison/robustness where available. |
| 8 | Macro Dashboard | Partially implemented | Macro/factor analytics exist; productized dashboard surface remains incomplete. |
| 9 | Candidate Comparison | Implemented V1 | `candidate_comparison.json` and `.txt` are emitted under Main output. Some candidates can be unavailable when source folders are absent. |
| 10 | Portfolio Comparison Arena | Partially implemented | File artifacts exist; interactive arena/workspace does not. Current-vs-policy comparison depends on materializing a current row. |
| 11 | Portfolio Health Score | Implemented V1 | `portfolio_health_score.json` and `.txt` exist. Report/UI integration is still limited. |
| 12 | Robustness Scorecard | Implemented V1 | `robustness_scorecard.json` and `.txt` exist. |
| 13 | Selection Engine | Implemented V1 | `selection_decision.json` and `.txt` exist. V1 defaults to policy when mandate-clean; this should be explained clearly in report/UI. |
| 14 | Assumption Sensitivity | Not implemented | No accepted spec or module found. This is a good next analytical layer after stabilization. |
| 15 | Pareto/Dominance | Not implemented | Deferred from Selection V1. Needs a spec before implementation. |
| 16 | Regret Analysis | Not implemented | Deferred from Selection V1. Needs a spec before implementation. |
| 17 | Trade-off Explanation | Partial | Selection/action/journal include rationale, but there is no dedicated candidate-level trade-off artifact or polished report section. |
| 18 | Model Risk Diagnostics | Partial | Warnings and diagnostics exist across modules, but no unified model-risk artifact/layer exists. |
| 19 | Action Engine | Implemented V1 | `action_plan.json` and `.txt` exist; non-executing plan with simple bps costs. |
| 20 | Rebalancing Advisor | Implemented V1 | Action plan plus existing rebalance helper cover the V1 boundary. Advanced tax/lot/turnover optimization not done. |
| 21 | No-Trade Recommendation | Implemented V1 | Selection engine has No-Trade materiality logic when current and favored target are both available. Current-row availability is still a workflow risk. |
| 22 | AI Commentary | Implemented, needs cleanup | Report commentary exists, but source/generated text still has mojibake in places. |
| 23 | Monitoring / What Changed | Implemented V1 | `monitoring_diff.json`, snapshots, latest/history folders exist. No full monitoring UI/frequency process yet. |
| 24 | Decision Journal | Implemented V1 | Generated-only `decision_journal.json`, TXT, latest/history exist. User-maintained journal workflow remains future scope. |

## Main Vs Robust Optimization Review

The current split is intentional and internally consistent.

| Path | Role today | Inputs / objective | Constraints / gates | Output role |
| --- | --- | --- | --- | --- |
| `run_optimization.py` + `src/optimization.py` | Production policy optimizer | Max expected return objective with optional soft volatility/return penalties; covariance from current policy setup, including sample or dual covariance paths. | Long-only bounds, policy constraints, ProLiquidity policy, historical MaxDD release gate, writes generated policy weights only if release permits. | Authoritative `portfolio_weights.yml` / policy candidate and report source. |
| `run_robust_mean_variance_constrained.py` + `src/robust_mv.py` | Robust candidate / benchmark | Robust MV objective using stabilized estimates and lambda calibration/CLI settings. | Constrained variant has bounds and young ETF caps, but does not apply the full Main production release boundary. | Candidate folder/report for comparison. |
| `run_robust_scenario_optimization.py` + `src/robust_scenario_optimization.py` | Scenario-robust candidate / benchmark | Scenario objective modes from normalized stress/scenario inputs. | Candidate-specific bounds and warm starts; does not overwrite production policy weights or run Main release gates. | Candidate folder/report for comparison. |

Decision implication: keep robust MV and robust scenario paths as comparison candidates for now. Do not silently replace Main optimizer behavior. If robust optimization should become production policy or part of policy selection, create a new spec/decision first.

Retention conclusion:

- Keep Main optimization. It matches the current project logic because the project still needs one
  production policy generator that writes `portfolio_weights.yml`, applies release gates, and anchors
  the Main report.
- Keep robust MV and robust scenario optimization. They match the product concept as alternative
  candidate construction methods and robustness benchmarks, not as hidden replacements for Main.
- Do not merge the roles silently. The next improvement is orchestration and labeling: robust paths
  should be clearly surfaced as candidate factory inputs, and Main should remain the authoritative
  policy path until an accepted spec changes that.

## Project Language Review

Project language contract: chat with the user may be Russian, but project source docs, code comments,
CLI/report text, generated report copy, specs, product copy, and output artifacts should be English
unless a future localization feature explicitly says otherwise.

Audit result:

- A literal Cyrillic scan of non-generated source areas, excluding common generated/cache folders, did
  not find Russian-language source text in this audit pass.
- That does not close the language issue. Several source files contain mojibake that appears to be
  broken Russian or broken Unicode. Those strings can still leak into CLI output, generated Markdown,
  HTML, TXT, and PDF artifacts.
- Generated outputs should not be hand-edited. They should become English by fixing source strings and
  generators, then regenerating outputs.

Recommended acceptance criteria for a future language cleanup session:

1. Source scan for literal Cyrillic returns no matches outside explicitly allowed agent/chat
   instructions or localization fixtures.
2. Source scan for common mojibake markers (`вЂ`, `Р`, `О`, broken arrows/checkmarks) is reviewed and
   fixed or explicitly accepted.
3. Representative generated report, TXT, HTML, and PDF-facing text are regenerated and visually/readably
   checked for English output.
4. If Russian localization is ever desired, it should be introduced as an explicit locale feature, not
   mixed into default project artifacts.

## Findings

### PSA-001 - Core session pipeline is implemented, not just planned

Severity: high positive finding.

Evidence: `src/candidate_comparison.py` now wires canonical comparison, robustness scorecard, health
score, selection decision, action plan, monitoring, and decision journal outputs. Current generated
Main artifacts include `candidate_comparison.json`, `robustness_scorecard.json`,
`portfolio_health_score.json`, `selection_decision.json`, `action_plan.json`,
`monitoring_diff.json`, and `decision_journal.json`.

Impact: future work should assume the V1 decision pipeline exists. The first audit's "missing
recommendation layer" finding is largely closed at artifact/code level.

Next action: update stale root docs and reporting specs so contributors stop treating these modules as
future-only.

### PSA-002 - Top-level docs still describe implemented modules as target/TBD

Severity: high.

Evidence:

- `README.md` still lists "Formal Selection Engine and Portfolio Health Score", "Monitoring / What
  Changed workflow", and "Decision Journal" under target/TBD areas.
- `AGENTS.md` still says full UI, Selection Engine implementation, Monitoring, and Decision Journal
  remain target/TBD.
- `SPEC.md` has a current status matrix showing implemented V1 modules, but earlier text still lists
  "full Monitoring" and "Decision Journal" as target/TBD.
- `ARCHITECTURE.md` still describes Health Score, Selection Engine, No-Trade, Monitoring, and Decision
  Journal as target modules and omits several new owning files from the comparison/action layer.
- `PRODUCT.md` feature inventory is closer, but some open questions and target-addition wording are
  stale after Sessions 14-20.

Impact: a future agent or developer can make the wrong implementation plan, recreate existing modules,
or skip the new artifacts because they appear unofficial.

Next action: run a focused documentation sync session covering `README.md`, `AGENTS.md`, `SPEC.md`,
`ARCHITECTURE.md`, and `PRODUCT.md`.

### PSA-003 - Detailed specs lag the post-session artifact surface

Severity: high.

Evidence:

- `docs/specs/reporting_outputs_spec.md` still focuses on candidate comparison and does not cover the
  full decision package: robustness, health, selection, action, monitoring, and journal report
  surfaces.
- `docs/specs/candidate_comparison_spec.md` still has stale ownership wording that treats future
  health/selection specs as TBD.
- `docs/specs/selection_engine_spec.md` still has "future" wording around action/monitoring in places
  even though those V1 modules now exist.

Impact: the generated files exist, but the report/export contract does not fully tell future agents
where these outputs should be surfaced or how they should be summarized.

Next action: update reporting and decision artifact specs before expanding report/PDF/UI integration.

### PSA-004 - Decision log has a duplicate decision ID

Severity: medium.

Evidence: `DECISIONS.md` uses `DEC-2026-05-17-003` for both the Robustness Scorecard V1 decision and
the Selection Engine V1 decision.

Impact: future references to `DEC-2026-05-17-003` are ambiguous. This is not a runtime bug, but it
weakens the project memory layer.

Next action: fix or supersede the duplicate ID in a dedicated doc sync pass, and update any references.

Resolution note, 2026-05-17: fixed by RM-611 / post-audit Session 03. Robustness Scorecard V1 keeps
`DEC-2026-05-17-003`; Selection Engine V1 now uses `DEC-2026-05-17-006`.

### PSA-005 - Source and generator mojibake remains outside the first cleanup scope

Severity: high for user-facing quality, medium for runtime correctness.

Evidence:

- `run_optimization.py` contains broken Russian/Unicode text in CLI/log strings.
- Robust optimization runners and modules contain broken symbols in comments, help text, and labels.
- `src/pdf_reports.py` contains extensive broken source strings and also has a mojibake repair helper,
  indicating generator-level text quality risk.
- `docs/specs/portfolio_construction_policy.md`, `docs/specs/candidate_comparison_spec.md`,
  `docs/specs/selection_engine_spec.md`, `docs/specs/action_engine_spec.md`, and `DESIGN.md` still
  contain broken symbols.
- Generated reports under output folders show broken text. Those should be fixed at source, not by
  editing generated outputs.
- A non-generated source scan for literal Cyrillic did not find current Russian text, so the immediate
  language problem is mostly broken encoding and default-output quality rather than intentional
  Russian-language source copy.

Impact: reports, PDFs, CLI messages, and docs can look corrupted to the user even when analytics are
correct. It also weakens the project-level rule that default artifacts should be English.

Next action: run a dedicated mojibake/source-text hygiene session focused on source docs and generator
strings, enforce English output as the default language, then regenerate outputs.

### PSA-006 - Reporting/PDF surfaces do not yet fully present the new decision package

Severity: high for product readiness.

Evidence: the new JSON/TXT artifacts are emitted, but the main report/PDF spec does not fully define a
decision package section for comparison, health, robustness, selection, action, monitoring, and journal.
`run_compare_variants.py` also only mentions comparison, robustness, and health in its CLI output even
though downstream decision files are emitted.

Impact: the system has machine-readable decision artifacts, but the user-facing report experience can
still feel like an analytical report rather than a decision-support product.

Next action: specify and implement a compact "decision package" report/PDF section after source docs are
synced.

### PSA-007 - No-Trade depends on current-row availability

Severity: medium.

Evidence: Selection V1 can compare `current` to a favored target, but the canonical comparison row for
`current` is available only when a user-current portfolio is materialized/tagged. In the inspected Main
comparison, `current` was unavailable, while `policy` was selected.

Impact: No-Trade is implemented but not always useful in the default policy-only workflow. Product
concept expects "should I change?" behavior, which needs current and target to be available together.

Next action: define the expected current-vs-policy workflow: either a two-run materialization process,
a combined runner, or a UI/report workflow that requires current weights before No-Trade is presented as
actionable.

### PSA-008 - Candidate availability is still file-orchestration dependent

Severity: medium.

Evidence: `candidate_comparison.json` includes a full registry with unavailable candidates when
variant output folders are missing. This is correct for V1, but it means the comparison quality depends
on which candidate scripts were run before comparison.

Impact: the product concept's Candidate Portfolio Factory implies a controlled set of alternatives.
The current implementation is closer to "compare whatever artifacts are available".

Next action: add a candidate factory/orchestration decision before presenting the comparison arena as a
complete product workflow.

### PSA-009 - Product open questions need pruning after V1 modules

Severity: medium.

Evidence: `PRODUCT.md` still contains open questions about Health Score components, no-trade rules,
monitoring frequency, and Decision Journal fields. Some of these are answered by accepted V1 specs;
others are now V2/UI/process questions.

Impact: contributors may think accepted V1 behavior is still undecided.

Next action: update product questions to separate "answered in V1" from "still open for UI/V2".

### PSA-010 - ExecPlan and roadmap contain stale handoff language

Severity: medium.

Evidence:

- The ExecPlan `Concrete Steps` section still says the next immediate action is Session 08, even though
  Sessions 01-20 are complete.
- The ExecPlan and roadmap still call several generated artifact names "proposals" even though the
  owning specs and implementations now exist.
- `docs/ROADMAP.md` audit mapping still says AUD-010 and AUD-011 are deferred, although their main
  roadmap items are now done.

Impact: fresh-session handoff can restart old work or misclassify implemented artifacts as proposals.

Next action: update planning docs to mark post-session state and next-stage backlog clearly.

### PSA-011 - Full UI/workspace remains not done

Severity: medium, expected gap.

Evidence: Sessions 21-22 remain planned/deferred. Existing utilities (`config_ui/`,
`results_dashboard/`) are partial surfaces, not the full product workspace described in the concept.

Impact: this is still a report-first and CLI/file-driven system. It is much closer to decision support
than before, but not yet a polished product experience.

Next action: after stabilization, run Session 21 as a product decision: static report package, local
dashboard, or web app. Do not build UI before deciding the first narrow surface.

### PSA-012 - Assumption sensitivity, Pareto/dominance, and regret are the largest missing analytic layers

Severity: medium.

Evidence: product concept sections 14-16 exist, and Selection V1 explicitly defers these layers.

Impact: Selection V1 can choose and explain under current inputs, but does not yet answer how stable
the choice is across assumptions, whether a candidate is dominated, or what the opportunity cost/regret
would be under alternative scenarios.

Next action: prioritize these after docs/reporting/text cleanup. Recommended order: assumption
sensitivity, Pareto/dominance, then regret.

### PSA-013 - Main and robust optimization both fit the project, but only with explicit roles

Severity: medium.

Evidence: Main optimization has production-policy behavior: it writes policy weights, applies policy
constraints and release gates, and feeds the Main report. Robust MV and robust scenario optimization
produce alternative candidates/benchmarks for comparison and robustness evaluation.

Impact: keeping both is useful and consistent with the product concept. The risk is user confusion if
robust optimization is presented as a competing production optimizer without the Main-vs-candidate
boundary.

Next action: keep both families in the project, but document and surface them as distinct roles:
Main = production policy path; robust MV/scenario = candidate factory and robustness benchmark inputs.
If a future product decision wants robust optimization to become policy, require a new accepted spec,
release-gate design, and tests.

## Next-Stage Recommendation

### Stage A - Stabilize the source of truth

1. Sync top-level docs with Sessions 01-20.
2. Fix decision log duplicate ID.
3. Update reporting outputs spec and stale detailed specs.
4. Update planning docs so "next work" no longer points to completed sessions.

### Stage B - Fix user-facing text and report integration

1. Run source mojibake cleanup for docs, CLI strings, report/PDF generators, and robust optimizer
   scripts, with English as the default project/output language.
2. Regenerate representative outputs after fixing source text.
3. Add a compact decision package section to report/PDF/user-facing summaries.

### Stage C - Harden decision workflow

1. Define a reliable current-vs-policy workflow so No-Trade is useful by default when current weights
   are provided.
2. Decide whether candidate generation should be orchestrated as a factory before comparison.
3. Keep robust optimizers as comparison candidates unless a future policy spec changes that boundary.

### Stage D - Add the next concept analytics

1. Assumption Sensitivity.
2. Pareto/Dominance.
3. Regret Analysis.
4. Unified Model Risk Diagnostics, if the above surfaces need a shared warning layer.

### Stage E - Product UI decision

Run Session 21 only after the above source/reporting state is stable enough to display. The first UI
surface should consume existing artifacts, not duplicate portfolio formulas in frontend code.

## Verification Notes

This audit did not change runtime behavior. It is a documentation and planning audit.

Recommended verification after this audit package:

- Run `python scripts/verify_docs.py`.
- No full `pytest` run is required for the audit itself unless follow-up sessions change code behavior.
