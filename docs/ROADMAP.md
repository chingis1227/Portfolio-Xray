# Project Roadmap

This file is the durable roadmap and backlog for Portfolio X-Ray & Optimization Terminal /
Portfolio MRI. It turns the product concept, audit findings, and current implementation state into
an ordered development sequence.

This is a planning document. It does not override [SPEC.md](../SPEC.md), [RULES.md](../RULES.md),
[OUTPUTS.md](../OUTPUTS.md), [TESTING.md](../TESTING.md), or the detailed specs under
[docs/specs/](specs/README.md). Product ideas become binding only after the relevant source-of-truth
spec and implementation are updated.

## Current Development Rule

Do not add new major analytics until the current source-of-truth cleanup and the canonical candidate
comparison contract are done. The current project already has a strong report-first analytical base;
the next quality step is a controlled decision pipeline:

```text
concept -> source-of-truth spec -> canonical artifact -> tests -> report/UI surface -> decision record
```

## Status Values

Use these statuses for roadmap items:

| Status | Meaning |
| --- | --- |
| Done | Implemented or documented, with the relevant verification recorded. |
| In progress | Work has started and must be resumed before starting dependent items. |
| Planned | Accepted as future work, but not started in source. |
| Blocked | Cannot proceed until a user decision, dependency, or contradiction is resolved. |
| Deferred | Intentionally postponed; not part of the near-term sequence. |
| TBD | Needs a spec or decision before implementation can be planned. |

## Phase 0: Stabilize Current Source Of Truth

Goal: make the current repository harder to misunderstand before adding scores,
recommendations, monitoring, or a full product UI.

Exit condition: a new developer can read root docs, specs, and utility UI descriptions without
confusing current behavior with future product goals.

| ID | Status | Session | Work item | Prerequisites | Owning docs/code | Artifact or output | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RM-000 | Done | Session 01 | Create this durable roadmap and register unresolved audit issues. | 2026-05-17 audit completed. | [Session plan](exec_plans/2026-05-17_project_development_session_plan.md), [full audit](audits/2026-05-17_full_project_system_audit.md), [known issues](../KNOWN_ISSUES.md), [decisions](../DECISIONS.md) | `docs/ROADMAP.md`, updated issue and decision registers | Search all `AUD-` IDs and confirm each is fixed, registered, or deferred here. |
| RM-001 | Done | Session 02 | Fix stale stress covariance documentation so `taxonomy_blend_v1` is clearly current default and `uniform_legacy` is legacy. | RM-000. | [stress testing spec](specs/stress_testing_spec.md), [stress.py](../src/stress.py), [stress covariance taxonomy](../src/stress_covariance_taxonomy.py) | Updated stress spec; no runtime code change required | `tests/test_stress_covariance_taxonomy.py -q` passed; stale-reference search confirms legacy scalars are only in legacy context. |
| RM-002 | Done | Session 03 | Remove or correct the stale `rc_asset_cap_pct` config UI surface. | RM-000. | [config form](../config_ui/templates/config_form.html), [config UI app](../config_ui/app.py), [feasibility constraints spec](specs/feasibility_constraints_spec.md), [portfolio construction policy](specs/portfolio_construction_policy.md) | Removed editable config UI field and added focused regression coverage. | Search `rc_asset_cap_pct`; focused config UI tests passed. |
| RM-003 | Done | Session 04 | Fix config UI `analysis_mode`, `current_weights`, and generated-weight semantics. | RM-002 recommended first. | [config UI app](../config_ui/app.py), [config form](../config_ui/templates/config_form.html), [input assumptions spec](specs/input_assumptions_spec.md), [config schema](../src/config_schema.py) | Config UI distinguishes current weights from generated policy weights and shows generated policy weights as read-only output. | `tests/test_config_ui_input_modes.py`, `tests/test_config_ui_rc_cap_removed.py`, `tests/test_input_assumptions.py`, and `tests/test_config_weights_sync.py` passed. |
| RM-004 | Planned | Session 01 or later docs cleanup | Clarify that partial utility UIs exist for config editing and read-only result viewing, while full product workspace remains TBD. | RM-000. | [README](../README.md), [SPEC](../SPEC.md), [PRODUCT](../PRODUCT.md), [ARCHITECTURE](../ARCHITECTURE.md), [DESIGN](../DESIGN.md) | Consistent top-level wording | Stale-reference search for UI status wording. |
| RM-005 | Done | Session 05 | Fix rebalance threshold semantics or implement explicit turnover logic. | RM-000. | [rebalance.py](../src/rebalance.py), [run_rebalance.py](../run_rebalance.py), [test_rebalance_threshold.py](../tests/test_rebalance_threshold.py) | Docstrings state max per-ticker drift gate only; turnover threshold deferred to Action/No-Trade sessions | `tests/test_rebalance_threshold.py -q` passed (2 tests); stale-reference search for turnover-threshold overstatement in `src/rebalance.py`. |
| RM-006 | Done | Session 06 | Clean source-document mojibake in a focused documentation hygiene pass. | RM-000. | Source docs/specs, especially [production workflow spec](specs/production_workflow.md) | Rewrote `production_workflow.md` in English; normalized encoding artifacts in stress, metrics, and view-after-optimization specs | Targeted mojibake codepoint scan on `docs/specs/*.md` passed. |
| RM-007 | Done | Session 07 | Add lightweight Markdown link and stale-reference verification. | RM-000. | [TESTING](../TESTING.md), [verify_docs.py](../scripts/verify_docs.py), [docs_verify.py](../src/docs_verify.py), [test_docs_links.py](../tests/test_docs_links.py) | `scripts/verify_docs.py` plus pytest coverage for source Markdown links, forbidden stale paths, and removed config UI fields | `python scripts/verify_docs.py` and `python -m pytest tests/test_docs_links.py -q` passed. |

## Phase 1: Standardize Candidate Comparison

Goal: create the canonical comparison artifact that later scores, selection, action, monitoring, and
UI can consume without special-case interpretation.

Exit condition: every supported candidate can be represented in one comparison table with clear
metadata, metrics, diagnostics, warnings, and construction method.

| ID | Status | Session | Work item | Prerequisites | Owning docs/code | Artifact or output | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RM-100 | Done | Session 08 | Specify the canonical candidate comparison artifact. | Phase 0 complete. | [candidate_comparison_spec.md](specs/candidate_comparison_spec.md), [candidate portfolios spec](specs/candidate_portfolios_spec.md), [reporting outputs spec](specs/reporting_outputs_spec.md), [OUTPUTS](../OUTPUTS.md) | Accepted spec for `candidate_comparison.json` (full registry, `current` row, Main output path) | `rg candidate_comparison` shows single contract; docs verify passes. |
| RM-101 | Done | Session 09 | Implement canonical candidate comparison output. | RM-100. | [candidate_comparison.py](../src/candidate_comparison.py), `run_compare_variants.py`, [candidate_comparison_spec.md](specs/candidate_comparison_spec.md) | `candidate_comparison.json` (+ optional `.txt`, legacy `portfolio_comparison.*`) under `output_dir_final` | `tests/test_candidate_comparison.py -q`; `python run_compare_variants.py` smoke when Main artifacts exist. |

## Phase 2: Build Scoring Carefully

Goal: add transparent scores only after candidate comparison inputs are stable.

Exit condition: scores are explainable, testable, and non-binding until the Selection Engine exists.

| ID | Status | Session | Work item | Prerequisites | Owning docs/code | Artifact or output | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RM-200 | Done | Session 10 | Specify the Robustness Scorecard. | RM-100. | [robustness_scorecard_spec.md](specs/robustness_scorecard_spec.md), [candidate_comparison_spec.md](specs/candidate_comparison_spec.md), [stress testing spec](specs/stress_testing_spec.md) | Accepted spec: relative within-run scoring, RC via comparison v1.1, 10y primary | `python scripts/verify_docs.py`; no recommendation wording in spec |
| RM-201 | Done | Session 11 | Implement the Robustness Scorecard. | RM-200 and RM-101. | [robustness_scorecard.py](../src/robustness_scorecard.py), [candidate_comparison.py](../src/candidate_comparison.py), [run_compare_variants.py](../run_compare_variants.py) | `robustness_scorecard.json` / `.txt` under `output_dir_final` | `tests/test_robustness_scorecard.py`, `tests/test_candidate_comparison.py` |
| RM-210 | Planned | Session 12 | Specify the Portfolio Health Score. | RM-200 recommended; RM-100 required. | Proposed `docs/specs/portfolio_health_score_spec.md`, metrics/stress/reporting specs, [PRODUCT](../PRODUCT.md) | Accepted Health Score spec | Documentation checks; confirm score remains explanatory and non-binding. |
| RM-211 | Planned | Session 13 | Implement the Portfolio Health Score. | RM-210 and RM-101. | Health score module, comparison outputs, report/export modules | Generated `portfolio_health_score.json` or spec-approved equivalent | New health score tests plus adjacent score/comparison tests. |

## Phase 3: Add Selection, No-Trade, And Action

Goal: create the first formal decision artifact only after comparison and scores exist.

Exit condition: the system can produce a selected candidate, no-trade conclusion, inconclusive status,
or data-review status with rationale and warnings, without mixing diagnostics and decisions.

| ID | Status | Session | Work item | Prerequisites | Owning docs/code | Artifact or output | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RM-300 | Planned | Session 14 | Specify Selection Engine and No-Trade Recommendation boundaries. | RM-201 and RM-211. | Proposed `docs/specs/selection_engine_spec.md`, comparison and score specs, [production workflow spec](specs/production_workflow.md) | Accepted selection/no-trade spec | Documentation checks; confirm diagnostic artifacts stay non-binding. |
| RM-301 | Planned | Session 15 | Implement Selection Engine and No-Trade Recommendation. | RM-300. | Selection module, score outputs, comparison outputs, report/commentary modules | Generated `selection_decision.json` or spec-approved equivalent | Tests for each allowed decision outcome plus report/comparison smoke if exported. |
| RM-310 | Planned | Session 16 | Extend Action Engine and Rebalancing Advisor around selected candidates. | RM-301. | [rebalance.py](../src/rebalance.py), [run_rebalance.py](../run_rebalance.py), View After Optimization spec, selection outputs | Generated `action_plan.json` or spec-approved equivalent | Rebalance/action tests plus selection tests when action consumes decisions. |

## Phase 4: Add Monitoring And Decision Records

Goal: turn one-time analysis into a repeatable process that can explain what changed and what was
decided.

Exit condition: the system can compare an analysis with a prior snapshot and emit a generated decision
record.

| ID | Status | Session | Work item | Prerequisites | Owning docs/code | Artifact or output | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RM-400 | Planned | Session 17 | Specify monitoring snapshots and What Changed artifacts. | RM-301 recommended. | Proposed `docs/specs/monitoring_spec.md`, [OUTPUTS](../OUTPUTS.md), [reporting outputs spec](specs/reporting_outputs_spec.md), [PRODUCT](../PRODUCT.md) | Accepted monitoring spec | Documentation checks; generated-vs-source boundary confirmed. |
| RM-401 | Planned | Session 18 | Implement monitoring diff outputs. | RM-400. | Snapshot/reporting modules, report output modules | Generated `monitoring_diff.json` or spec-approved equivalent | Tests for no prior snapshot, normal diff, and degraded fields; report smoke if outputs change. |
| RM-410 | Planned | Session 19 | Specify Decision Journal schema and lifecycle. | RM-300 required; RM-310 and RM-400 preferred. | Proposed `docs/specs/decision_journal_spec.md`, [OUTPUTS](../OUTPUTS.md), selection/action/monitoring specs | Accepted journal spec | Documentation checks; generated-only V1 boundary confirmed unless explicitly changed. |
| RM-411 | Planned | Session 20 | Implement generated Decision Journal output. | RM-410. | Journal module, selection/action/report modules | Generated `decision_journal.json` or spec-approved equivalent | Journal tests for selected, no-trade, inconclusive, and missing-data decisions. |

## Phase 5: Product UI Only After Stable Contracts

Goal: display stable artifacts without moving formulas or product decisions into the UI layer.

Exit condition: the first UI slice consumes existing stable artifacts and does not invent its own
portfolio logic.

| ID | Status | Session | Work item | Prerequisites | Owning docs/code | Artifact or output | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RM-500 | Planned | Session 21 | Decide the first real product UI surface: static report package, local dashboard, or web app. | Phases 1-4 enough for the chosen surface. | [DESIGN](../DESIGN.md), [PRODUCT](../PRODUCT.md), [ARCHITECTURE](../ARCHITECTURE.md), `config_ui/`, `results_dashboard/` | Decision record and updated product docs if direction changes | Documentation checks; no code unless explicitly requested. |
| RM-501 | Planned | Session 22 | Implement the first narrow UI slice. | RM-500 and stable artifact contracts. | Chosen UI code, stable artifact specs, [DESIGN](../DESIGN.md) | First UI surface around existing artifacts | UI tests if present; local browser inspection for significant frontend changes. |

## Audit Mapping

| Audit ID | Roadmap handling |
| --- | --- |
| AUD-001 | Fixed by RM-000 and this roadmap. |
| AUD-002 | Fixed by RM-001 in Session 02; resolved issue removed from [KNOWN_ISSUES](../KNOWN_ISSUES.md). |
| AUD-003 | Fixed by RM-002 in Session 03; resolved issue removed from [KNOWN_ISSUES](../KNOWN_ISSUES.md). |
| AUD-004 | Fixed by RM-003 in Session 04; resolved issue removed from [KNOWN_ISSUES](../KNOWN_ISSUES.md). |
| AUD-005 | Registered in [KNOWN_ISSUES](../KNOWN_ISSUES.md); planned as RM-004. |
| AUD-006 | Resolved in Session 05 via RM-005 (docstrings + focused tests). |
| AUD-007 | Fixed by updating [DECISIONS](../DECISIONS.md). |
| AUD-008 | Fixed by registering unresolved issues in [KNOWN_ISSUES](../KNOWN_ISSUES.md). |
| AUD-009 | Fixed by RM-006 in Session 06; resolved issue removed from [KNOWN_ISSUES](../KNOWN_ISSUES.md). |
| AUD-010 | Deferred to RM-100 and RM-101. |
| AUD-011 | Deferred to RM-200 through RM-301; current X-Ray/commentary remain diagnostic-only. |
| AUD-012 | Resolved via RM-007 (Session 07): `scripts/verify_docs.py` and `tests/test_docs_links.py`. |

## Session Boundary Rule

Use [the session plan](exec_plans/2026-05-17_project_development_session_plan.md) to continue work.
Complete the first incomplete or partial session before starting later items. Update that ExecPlan
after each session with one of three states: completed, partial, or blocked.

## Proposed Future Artifacts

These names are proposals until accepted by owning specs:

- `candidate_comparison.json`
- `robustness_scorecard.json`
- `portfolio_health_score.json`
- `selection_decision.json`
- `action_plan.json`
- `monitoring_diff.json`
- `decision_journal.json`
