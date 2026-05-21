# Optimization Engine Post-Audit Roadmap (Block 5)

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan must be maintained in accordance with [PLANS.md](../../PLANS.md).

## Purpose / Big Picture

Block 5 is the Optimization Engine layer: the part of the project that builds or evaluates
optimized portfolio weights. After the methodology audit, the main problem is not a lack of
optimizers. The project already has a legacy policy optimizer, candidate optimizer families,
Robust Mean-Variance, and scenario-aware robust optimization. The problem is that optimizer roles,
inputs, objectives, constraints, fallback behavior, reproducibility metadata, and comparison
readiness are spread across code, specs, and generated artifacts.

After this roadmap is complete, a user or future agent should be able to answer: how was an
optimized portfolio built, what assumptions drove it, which constraints bound it, what could fail,
how solver or fallback quality is disclosed, and whether the optimized candidate can be fairly
compared. This wave must not add new optimizers, change objective formulas, change constraints, or
change mandate gates silently.

The primary audit baseline is [Optimization Engine Methodology Map](../audits/2026-05-20_optimization_engine_methodology_map.md).
The initial baseline snapshot is [Optimization Engine Baseline Snapshot](../audits/2026-05-20_optimization_engine_baseline_snapshot.md).

**Chat rule:** one session = one new chat unless the user explicitly requests a tiny follow-up in
the same thread. Session 00 persists project memory only. Start Session 01 in a new chat.

## Progress

- [x] (2026-05-21) Session 00 (`RM-990`): ExecPlan persisted; registers and ROADMAP Phase 15 updated; baseline snapshot stub created; TESTING governance bundle stub added; `verify_docs` target recorded.
- [x] (2026-05-21) Session 01 (`RM-991`): Created canonical `optimization_engine_layer_spec.md` for current Block 5 roles, matrices, boundaries, and target-only objective status. No optimizer behavior, formulas, constraints, runtime fields, or generated outputs changed.
- [x] (2026-05-21) Session 02 (`RM-992`): Added `DEC-2026-05-21-001` and the Optimization Engine spec appendix for target-only objective boundaries. No optimizer behavior, formulas, constraints, runtime fields, or generated outputs changed.
- [x] (2026-05-21) Session 03 (`RM-993`): Added legacy policy optimizer disclosure in `run_result.json.optimizer_run_metadata`. No optimizer formulas, constraints, mandate gates, fallback semantics, or generated weights changed.
- [x] (2026-05-21) Session 04 (`RM-994`): Added candidate optimizer reproducibility envelope in optimizer candidate `baseline_weights_metadata.json.optimizer_run_metadata`. No optimizer formulas, constraints, fallback behavior, mandate gates, comparison semantics, or generated weights changed.
- [x] (2026-05-21) Session 05 (`RM-995`): Added comparison-level optimizer disclosure in
  `candidate_comparison.json` row `construction_disclosure.optimizer_methodology`. No optimizer
  formulas, constraints, fallback behavior, mandate gates, row status semantics, generated weights,
  or generated artifacts changed.
- [x] (2026-05-21) Session 06 (`RM-996`): Formalized fallback and failure policy across
  optimizer metadata, factory step evidence, comparison readiness, and Selection warnings. No
  optimizer formulas, constraints, fallback behavior, mandate gates, generated weights, or
  generated artifacts changed.
- [x] (2026-05-21) Session 07 (`RM-997`): Added robust scenario solver status contract.
- [x] (2026-05-21) Session 08 (`RM-998`): Made `analysis_end` and input fingerprints explicit in
  legacy and candidate optimizer estimator metadata.
- [x] (2026-05-21) Session 09 (`RM-999`): Surfaced covariance and young ETF methodology in
  machine-readable metadata and human-readable summaries. No covariance formulas, constraints,
  fallback behavior, mandate gates, comparison ranking, or generated weights changed.
- [x] (2026-05-21) Session 10 (`RM-1000`): Formalize optimization readiness for candidate comparison.
- [x] (2026-05-21) Session 11 (`RM-1001`): Add golden contracts and Block 5 governance bundle.
- [x] (2026-05-21) Session 12 (`RM-1002`): Wave closure and documentation sync.

## Surprises & Discoveries

- Observation: Before Session 00, there was no single Block 5 owning spec or active plan. The
  methodology map already existed and was registered as an active audit input, but its follow-up plan
  was still `TBD`.
  Evidence: `docs/audits/README.md` row for `2026-05-20_optimization_engine_methodology_map.md`.

- Observation: `docs/specs/README.md`, `SPEC.md`, and `OUTPUTS.md` already index policy,
  candidate, robust MV, robust scenario, and production workflow specs, but not a unified
  Optimization Engine layer spec.
  Evidence: spec index entries for `portfolio_construction_policy.md`,
  `candidate_portfolios_spec.md`, `robust_mv_spec.md`, and
  `robust_scenario_optimization_spec.md`.

- Observation: Session 01 can define canonical Block 5 governance without changing code because the
  audit map already captured the current optimizer role split and the existing detailed specs own
  formulas and candidate contracts.
  Evidence: `docs/specs/optimization_engine_layer_spec.md` references the audit map and routes
  formulas/status semantics back to the existing owning specs.

- Observation: Session 02 needs a broader Optimization Engine decision than the earlier candidate
  registry decision.
  Evidence: `DEC-2026-05-20-003` governs concept-only comparison registry rows, while
  `DEC-2026-05-21-001` now governs policy objectives, candidate objectives, robust modes,
  hard constraints, gates, and output contracts.

- Observation: The legacy policy path already had the raw facts needed for disclosure at the point
  where `run_result.json` is assembled.
  Evidence: `run_optimization.py` has `analysis_end_str`, primary/secondary windows,
  `cols_primary`, dual-covariance diagnostics, bounds config, cash policy, optimizer status, and
  mandate gate state before writing `run_result.json`.

- Observation: Candidate optimizer metadata exports already centralized the strongest per-family
  construction facts, so Session 04 could add a normalized nested envelope without changing builder
  signatures or wrapper output file names.
  Evidence: `src/portfolio_variants.py` metadata export helpers for Minimum Variance, Maximum
  Diversification, Minimum CVaR, and Robust Mean-Variance are the source used by candidate
  `baseline_weights_metadata.json` files and by comparison passthrough.

- Observation: Session 05 could keep comparison disclosure read-only because the comparison builder
  already loads both `baseline_weights_metadata.json` and factory step freshness excerpts in one
  place.
  Evidence: `src/candidate_comparison.py::construction_disclosure_from_folder` now projects
  `optimizer_methodology` from existing `optimizer_run_metadata` blocks and factory freshness fields
  without calling optimizer code or candidate scripts.

- Observation: Factory `status: succeeded` is only orchestration evidence, not clean optimizer
  evidence.
  Evidence: `src/candidate_factory.py` can mark a step `succeeded` when `snapshot_10y.json` exists
  after script execution; Session 06 now separately copies `optimization_quality_status` from
  `baseline_weights_metadata.json.optimizer_run_metadata` or `summary.json`.

- Observation: Robust scenario optimization wrote solver information in the Main robust summary,
  while factory/comparison read candidate-folder artifacts.
  Evidence: `run_robust_scenario_optimization.py` writes `robust_optimization_v1_summary.json`
  under `output_dir_final`, and `run_robust_scenario_portfolio_report.py` materializes
  `robust scenario portfolio/baseline_weights_metadata.json`.

- Observation: The shared candidate covariance helper did not pass the wrapper `analysis_end` into
  young-ETF dual covariance estimation.
  Evidence: `src/portfolio_variants.py::_mv_covariance_for_eligible` called
  `build_dual_covariance_and_mu(...)` without `analysis_end`; Session 08 now passes
  `pd.Timestamp(analysis_end)` explicitly.

- Observation: Candidate comparison already had the right read-only passthrough point for human
  methodology notes.
  Evidence: `src/candidate_comparison.py::write_candidate_comparison_txt` renders from
  `construction_disclosure.optimizer_methodology`, so Session 09 could summarize covariance and
  Young ETF methodology without loading optimizer code or recomputing weights.

- Observation: Session 10 could formalize fair-comparison readiness without changing row-status
  rules because Sessions 06-09 already defined artifact gates, optimizer quality degradation, and
  methodology passthrough.
  Evidence: `src/optimization_readiness.py::build_optimization_readiness` mirrors final row status
  and copies checklist results into `construction_disclosure.optimization_readiness` after
  `_apply_factory_and_optimizer_quality_policy`.

- Observation: Session 11 can add Block 5 golden contracts without rerunning legacy policy or
  candidate optimizers because Sessions 03-10 already centralized disclosure builders and comparison
  passthrough.
  Evidence: `tests/optimization_engine_golden_inputs.py` builds legacy metadata via
  `run_optimization._build_legacy_policy_optimizer_run_metadata`, candidate metadata via
  `portfolio_variants._candidate_optimizer_run_metadata`, and comparison Block 5 slices via
  `build_candidate_comparison` on a deterministic temp project.

## Decision Log

- Decision: Session 00 is documentation and project-memory only.
  Rationale: The audit explicitly requires methodology governance before changing any optimizer,
  objective, estimator, constraint, fallback, or output contract.
  Date/Author: 2026-05-21 / Agent.

- Decision: Phase 15 uses roadmap IDs `RM-990` through `RM-1002`.
  Rationale: Phase 14 ended at `RM-981`; leaving a small numeric gap avoids confusing the completed
  Candidate Factory wave with the new Optimization Engine wave.
  Date/Author: 2026-05-21 / Agent.

- Decision: Do not link `optimization_engine_layer_spec.md` as an existing source of truth until
  Session 01 creates it.
  Rationale: Session 00 should not imply a spec exists before it is authored and accepted.
  Date/Author: 2026-05-21 / Agent.

- Decision: Session 01 defines `optimization_engine_layer_spec.md` as the canonical Block 5 layer
  spec, but keeps target-only objective names such as Max Sharpe, drawdown-controlled,
  macro-resilient, and tax/turnover-aware optimization marked not implemented.
  Rationale: The goal is to prevent product-concept language from being mistaken for shipped
  optimizer behavior before later sessions make explicit decisions.
  Date/Author: 2026-05-21 / Agent.

- Decision: Session 01 does not add `optimizer_run_metadata` or any other planned public contract
  field to runtime outputs.
  Rationale: Later sessions own output contract implementation. Session 01 is the source-of-truth
  specification layer only.
  Date/Author: 2026-05-21 / Agent.

- Decision: Session 02 records Max Sharpe, drawdown-controlled, macro-resilient,
  stress-test-optimized, tax-aware, and turnover-aware optimizer objectives as target-only until a
  future accepted spec, implementation, tests, and documentation update promotes them.
  Rationale: These names appear in product-direction material, but current runtime behavior is
  limited to the shipped legacy policy, candidate, robust MV, and robust scenario paths.
  Date/Author: 2026-05-21 / Agent.

- Decision: Session 03 uses `run_result.json.optimizer_run_metadata` for legacy policy disclosure
  and derives solver/fallback quality from the existing optimizer status string.
  Rationale: This makes the policy output auditable without changing the optimizer return signature,
  release statuses, objective, constraints, ProLiquidity overlay, or mandate gate semantics.
  Date/Author: 2026-05-21 / Agent.

- Decision: Session 04 nests candidate disclosure under
  `baseline_weights_metadata.json.optimizer_run_metadata` instead of adding a new candidate artifact.
  Rationale: Existing candidate wrappers already write `baseline_weights_metadata.json`, and
  `candidate_comparison.json` already passes that file through as construction disclosure. A nested
  envelope preserves top-level compatibility while making optimizer methodology machine-readable.
  Date/Author: 2026-05-21 / Agent.

- Decision: Session 05 exposes a compact
  `construction_disclosure.optimizer_methodology` block instead of duplicating full upstream
  metadata as a new top-level candidate row field.
  Rationale: `construction_disclosure` already owns comparison-level construction passthrough, and a
  compact projection makes method, objective, constraints, solver/fallback quality, candidate-only
  status, and freshness visible without changing comparison scoring or ranking semantics.
  Date/Author: 2026-05-21 / Agent.

- Decision: Session 06 treats fallback/approximate optimizer quality as degraded comparison
  evidence and failed factory/optimizer quality as unavailable comparison evidence.
  Rationale: A fallback or approximate optimizer output can still be useful for review, but it must
  not look like a clean solve in factory, comparison, or Selection artifacts.
  Date/Author: 2026-05-21 / Agent.

- Decision: Session 07 copies robust scenario solver disclosure into the materialized candidate
  `baseline_weights_metadata.json.optimizer_run_metadata` instead of teaching factory/comparison to
  read Main robust summary files directly.
  Rationale: Candidate comparison already owns construction disclosure from candidate artifacts;
  keeping robust scenario metadata beside its fixed candidate weights preserves the existing
  read-only comparison boundary.
  Date/Author: 2026-05-21 / Agent.

- Decision: Session 08 adds `input_fingerprints` inside existing optimizer metadata envelopes
  rather than adding new generated artifacts or comparison gates.
  Rationale: The goal is reproducibility and stale-input auditability without changing formulas,
  weights, fallback behavior, mandate gates, or comparison semantics.
  Date/Author: 2026-05-21 / Agent.

- Decision: Session 09 nests covariance methodology under the existing `covariance` metadata block
  and exposes Young ETF methodology as a sibling `young_etf_methodology` block.
  Rationale: Covariance method facts belong with covariance disclosure, while Young ETF policy can
  affect covariance and/or caps depending on optimizer family. A sibling block avoids implying that
  every Young ETF cap is itself a covariance estimator.
  Date/Author: 2026-05-21 / Agent.

- Decision: Session 10 adds `construction_disclosure.optimization_readiness` with an explicit
  `fair_comparison_ready` gate instead of changing comparison ranking or selection math.
  Rationale: Optimizer-backed rows need a machine-readable checklist for weights, snapshot, stress,
  disclosure, freshness, and clean optimizer quality before they are treated as fairly comparable;
  row `status` rules from Sessions 04-06 remain authoritative.
  Date/Author: 2026-05-21 / Agent.

- Decision: Session 11 uses three committed golden JSON fixtures plus structural fingerprints
  instead of expanding the Phase 14 candidate comparison golden for Block 5-only fields.
  Rationale: Block 5 disclosure is versioned separately (`optimizer_run_metadata` schemas and
  comparison Block 5 slice); a focused fixture keeps Phase 14 comparison goldens stable while still
  catching disclosure drift.
  Date/Author: 2026-05-21 / Agent.

- Decision: Session 12 leaves methodology-map G9 (stress `FAIL_*` vs release semantics) **accepted**
  outside Block 5 optimizer scope; G10 X-Ray in comparison remains optional via `KI-2026-05-21-001`.
  Rationale: Phase 15 exit condition is optimizer-layer governance and disclosure, not Stress Lab
  pass/fail wording or mandatory X-Ray on comparison rows.
  Date/Author: 2026-05-21 / Agent.

## Outcomes & Retrospective

Session 00 outcome: this ExecPlan is the active Block 5 handoff; `docs/ROADMAP.md`,
`docs/exec_plans/README.md`, `docs/audits/README.md`, `SPEC.md`, `docs/specs/README.md`, and
`TESTING.md` point to the audit and plan; baseline snapshot stub exists. No runtime code,
optimizer formulas, generated weights, or optimizer outputs were changed.

Session 01 outcome: `docs/specs/optimization_engine_layer_spec.md` now exists as the canonical
Block 5 source of truth. It describes Blocks 5.1 through 5.11, optimizer path roles, objective,
estimator, constraint, status, output, and comparison-readiness matrices, and the hard-constraint
versus diagnostic-only boundary. `SPEC.md`, `OUTPUTS.md`, and `docs/specs/README.md` index the new
spec. No optimizer code, formulas, constraints, gates, runtime output fields, or generated artifacts
were changed.

Session 02 outcome: `DECISIONS.md` now contains `DEC-2026-05-21-001`, and
`docs/specs/optimization_engine_layer_spec.md` has a target-only objective appendix. Max Sharpe,
drawdown-controlled, macro-resilient, stress-test-optimized, tax-aware, and turnover-aware objective
names are explicitly non-runtime concepts until a later spec and implementation promote them. No
optimizer code, formulas, constraints, gates, runtime output fields, or generated artifacts were
changed.

Session 03 outcome: legacy policy `run_result.json` now includes
`optimizer_run_metadata` (`legacy_policy_optimizer_run_metadata_v1`) describing objective mode,
expected-return and covariance sources, windows, `analysis_end`, eligible universe, resolved
bounds/caps, cash policy, solver/fallback quality, and mandate release status. The metadata is
explanatory only; optimizer formulas, constraints, fallback behavior, mandate release semantics, and
generated weights were not changed.

Session 04 outcome: Minimum Variance, Maximum Diversification, Minimum CVaR, and Robust
Mean-Variance metadata exports now include `optimizer_run_metadata`
(`candidate_optimizer_run_metadata_v1`) inside `baseline_weights_metadata.json`. The envelope
records candidate-only role, method id, objective, monthly input window, expected-return usage,
covariance method, eligible universe, active constraints/resolved bounds, relevant parameters,
solver/fallback quality, and output summary fields. Existing top-level metadata fields remain for
compatibility; optimizer formulas, constraints, fallback behavior, mandate gates, comparison
semantics, generated weights, and generated artifacts were not changed.

Session 05 outcome: `candidate_comparison.json` rows now include
`construction_disclosure.optimizer_methodology` when source artifacts expose normalized optimizer
metadata. Optimizer candidates copy from
`baseline_weights_metadata.json.optimizer_run_metadata`; legacy policy copies from
`run_result.json.optimizer_run_metadata`. The block surfaces source schema, role, candidate-only
status, method id, objective, input window, expected-return and covariance disclosure, constraints,
solver/fallback quality, and factory freshness fields when present. Comparison remains read-only and
diagnostic-only; optimizer formulas, constraints, fallback behavior, mandate gates, row status
semantics, generated weights, and generated artifacts were not changed.

Session 06 outcome: `src/optimization_status.py` defines normalized quality statuses; legacy policy
metadata now uses `clean_solve` / `approximate_fallback`; candidate factory steps surface optimizer
quality evidence when artifacts expose it; candidate comparison adds
`construction_disclosure.optimizer_quality`, degrades fallback/approximate optimizer rows, and marks
failed current factory/optimizer quality unavailable; Selection warns when a fallback/approximate
optimizer target is favored. Optimizer formulas, constraints, fallback branches, mandate gates,
generated weights, and generated artifacts were not changed.

Session 07 outcome: robust scenario SLSQP solves now export a normalized `solver` block and compact
top-level quality fields in `robust_optimization_v1_summary.json`. When
`run_robust_scenario_portfolio_report.py` materializes `robust scenario portfolio/`, it copies that
solver disclosure into `baseline_weights_metadata.json.optimizer_run_metadata`
(`robust_scenario_optimizer_run_metadata_v1`), allowing candidate factory and comparison to surface
robust scenario solver quality through existing `optimization_quality` mechanisms. Optimizer
formulas, constraints, fallback branches, mandate gates, and generated weights were not changed.

Session 08 outcome: `run_result.json.optimizer_run_metadata` and optimizer candidate
`baseline_weights_metadata.json.optimizer_run_metadata` now disclose estimator return-panel
start/end/rows and `input_fingerprints` (`returns_panel_fingerprint`, `config_fingerprint`,
`universe_fingerprint`). Expected-return and covariance metadata also carry the estimator
`analysis_end` and return-panel fingerprint. Candidate young-ETF dual covariance now receives the
wrapper `analysis_end` explicitly. Optimizer formulas, constraints, fallback branches, mandate
gates, comparison semantics, generated weights, and generated artifacts were not changed.

Session 09 outcome: legacy policy and candidate optimizer metadata now include
`covariance.methodology` (`optimizer_covariance_methodology_v1`), `covariance.methodology_summary`,
and `young_etf_methodology` (`optimizer_young_etf_methodology_v1`). Candidate comparison copies the
Young ETF block into `construction_disclosure.optimizer_methodology`; `candidate_comparison.txt`
and legacy `ips_summary.txt` include compact methodology notes when metadata exists. No covariance
formulas, Young ETF bucket/cap rules, fallback behavior, optimizer constraints, mandate gates,
comparison ranking, generated weights, or generated artifacts were changed.

Session 10 outcome: optimizer-backed comparison rows now include
`construction_disclosure.optimization_readiness` (`optimizer_comparison_readiness_v1`) with required
checks for weights, `snapshot_10y`, stress summary, construction disclosure, optimizer methodology,
optimizer quality, and freshness, plus optional `portfolio_xray`. The block exposes
`fair_comparison_ready` for clean, fully disclosed `available` optimizer rows and marks gaps for
partial, stale, approximate, or failed cases. `candidate_comparison.txt` adds a compact readiness
section. Optimizer formulas, constraints, fallback branches, mandate gates, comparison ranking,
generated weights, and generated artifacts were not changed.

Session 11 outcome: committed golden fixtures for legacy policy metadata, candidate optimizer
metadata, and comparison Block 5 disclosure; `tests/optimization_engine_golden_inputs.py` and
`tests/test_optimization_engine_contract.py`; `TESTING.md` Block 5 bundle finalized with golden
regenerate commands. Governance bundle **159 passed**; `verify_docs` OK. No optimizer formulas,
constraints, fallback branches, mandate gates, comparison ranking, generated weights, or generated
artifacts were changed. Resume Session 12 (`RM-1002`) for wave closure.

Session 12 outcome (`RM-1002`): Phase 15 **Done** — `CHANGELOG.md`, `KNOWN_ISSUES.md` Block 5 gap index,
`docs/ROADMAP.md`, baseline snapshot closure section, ExecPlan register (plan **Completed**, no active
project-level plan), audits register (Block 5 audits **Historical**), `TESTING.md` wave-closed note.
Governance bundle **159 passed**; `verify_docs` OK. No optimizer code, formulas, constraints, mandate
gates, comparison ranking, generated weights, or generated artifacts were changed.

**Wave complete:** Block 5 Optimization Engine governance Sessions 00–12 closed 2026-05-21.

## Context and Orientation

The current product is a CLI and file-driven portfolio decision-support system. The portfolio-first
workflow starts from an `analysis_subject`, diagnoses it, builds candidate alternatives, compares
them, and emits decision artifacts. The legacy policy optimizer remains callable through
`run_optimization.py`, but it is not the default portfolio-first starting point.

The Optimization Engine layer spans several code paths:

- `run_optimization.py` and `src/optimization.py` implement the legacy policy optimizer and release
  checks.
- `src/portfolio_variants.py` implements candidate optimizer families such as Minimum Variance,
  Maximum Diversification, Minimum CVaR, and related benchmark constructions.
- `src/robust_mv.py` and `src/robust_mv_calibration.py` implement Robust Mean-Variance and lambda
  calibration.
- `src/robust_scenario_optimization.py` and robust scenario scripts build a scenario-aware robust
  candidate from Main portfolio stress/scenario artifacts.
- `src/candidate_factory.py` and `src/candidate_comparison.py` orchestrate and compare generated
  candidate artifacts, but they should not define optimizer formulas.

Terms used in this plan:

- **Legacy policy optimizer** means the compatibility path that can write `portfolio_weights.yml`
  and `run_result.json` after release checks.
- **Candidate optimizer** means a builder that creates fixed candidate weights for comparison. It
  does not replace the portfolio-first subject or production release policy.
- **Diagnostic-only** means output that informs analysis but does not bind weights, mandate status,
  or selection unless a canonical spec says so.
- **Reproducibility envelope** means a machine-readable block that records enough method, input,
  parameter, and solver information to explain or reproduce how weights were built.

## Plan of Work

Work proceeds in strict session order. Each major session should be a separate chat and should update
this ExecPlan as a living document.

Session 01 creates the missing canonical Optimization Engine layer spec. It must describe roles,
objectives, estimators, constraints, failure statuses, outputs, and comparison readiness for Block
5.1 through Block 5.11. This is documentation and governance first; it must not change code.

Session 02 records target-only optimizer concepts in `DECISIONS.md` and the spec appendix so names
such as Max Sharpe, drawdown-controlled, macro-resilient, and tax/turnover-aware objectives cannot
be mistaken for implemented optimizers.

Session 03 adds disclosure to the legacy policy optimizer output. The key behavior is that
`run_result.json` should explain the objective mode, return/covariance sources, window,
`analysis_end`, eligible universe, bounds/caps, cash policy, and solver/fallback status without
changing the existing objective or mandate release semantics.

Session 04 adds a normalized `optimizer_run_metadata` block for candidate optimizer outputs while
preserving existing metadata fields for compatibility.

Session 05 propagates optimizer methodology into `candidate_comparison.json` so comparison rows show
method, objective, constraints, solver/fallback quality, candidate-only status, and freshness.

Session 06 formalizes fallback and failure statuses across optimizer builders, factory, comparison,
and selection boundaries. No fallback should look like an ordinary successful optimization.

Session 07 adds normalized robust scenario solver status fields and propagates them to factory and
comparison disclosure.

Session 08 makes `analysis_end` and input fingerprints explicit in optimization estimator paths.
This prevents stale or incomplete-period data from being silently reused.

Session 09 surfaces covariance and young ETF methodology in machine-readable metadata and
human-readable summaries. It must not change covariance formulas.

Session 10 formalizes optimization readiness for candidate comparison, including required weights,
snapshot, stress, X-Ray, construction disclosure, freshness, and failure/approximation status.

Session 11 adds Block 5 golden/contract coverage and finalizes the governance verification bundle.

Session 12 closes the wave by syncing `CHANGELOG.md`, `KNOWN_ISSUES.md`, `docs/ROADMAP.md`, this
ExecPlan, and the baseline snapshot.

## Concrete Steps

For Session 00, from repository root:

    python scripts/verify_docs.py

If plain `python` is not available in the Codex desktop shell, use the bundled Python path reported
by the workspace dependencies tool, for example:

    C:\Users\ShumeikoYe\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe scripts\verify_docs.py

For Sessions 01 and 02, run:

    python scripts/verify_docs.py

For code/output contract sessions, run the focused Block 5 bundle after the targeted tests for the
changed behavior:

    python -m pytest tests/test_legacy_policy_optimizer_disclosure.py tests/test_optimization_fallback.py tests/test_config_weights_sync.py tests/test_young_etfs_dual_cov.py -q
    python -m pytest tests/test_minimum_variance_baseline.py tests/test_maximum_diversification_baseline.py tests/test_minimum_cvar_baseline.py -q
    python -m pytest tests/test_robust_mean_variance.py tests/test_robust_mv_calibration.py tests/test_robust_scenario_optimization.py -q
    python -m pytest tests/test_optimization_readiness.py tests/test_optimization_engine_contract.py tests/test_candidate_factory.py tests/test_candidate_comparison.py tests/test_candidate_factory_contract.py tests/test_candidate_comparison_contract.py -q
    python scripts/verify_docs.py

Regenerate Block 5 golden fixtures after intentional disclosure contract changes:

    python tests/optimization_engine_golden_inputs.py
    python -m pytest tests/test_optimization_engine_contract.py -q

Run `python run_optimization.py` only when legacy policy outputs change. Run affected candidate or
robust scripts only when their wrapper/output contract changes. Do not refresh generated artifacts
for commit unless the session explicitly targets generated outputs.

## Validation and Acceptance

Session 00 is accepted when:

- this ExecPlan exists under `docs/exec_plans/`;
- `docs/exec_plans/README.md` marks it as the active plan;
- `docs/ROADMAP.md` contains Phase 15 and Session 00 is `Done`;
- `SPEC.md` and `docs/specs/README.md` link the Block 5 methodology map;
- `docs/audits/2026-05-20_optimization_engine_baseline_snapshot.md` exists;
- `TESTING.md` contains the Block 5 governance bundle stub;
- `python scripts/verify_docs.py` passes;
- no optimizer code, formulas, constraints, gates, or generated outputs are changed.

The whole wave is accepted when every optimizer path has spec-owned disclosure, fallback and solver
quality are not hidden, reproducibility metadata is present for policy and candidate optimizers, and
candidate comparison clearly distinguishes constrained, uncapped, approximate, failed, stale, and
candidate-only optimized portfolios.

## Idempotence and Recovery

Documentation edits in Session 00 are safe to repeat if links remain unique and the ExecPlan
register has only one active project-level plan. If verification fails because a linked file is
missing, either create the referenced file in the same session if it is part of Session 00, or remove
the link until the owning session creates it. Do not fix verification by creating behavior specs or
code changes that belong to later sessions.

If a code session changes generated artifacts accidentally, treat them as generated evidence, not
source. Revert only the accidental generated-output changes you made, and never revert unrelated user
changes or pre-existing dirty files.

## Artifacts and Notes

Session 00 creates these source documentation artifacts:

- `docs/exec_plans/2026-05-20_optimization_engine_post_audit_roadmap.md`
- `docs/audits/2026-05-20_optimization_engine_baseline_snapshot.md`

Session 01 creates this source documentation artifact:

- `docs/specs/optimization_engine_layer_spec.md`

Session 00 updates these source documentation indexes:

- `docs/exec_plans/README.md`
- `docs/audits/README.md`
- `docs/ROADMAP.md`
- `SPEC.md`
- `docs/specs/README.md`
- `TESTING.md`

The methodology map remains the audit baseline:

- `docs/audits/2026-05-20_optimization_engine_methodology_map.md`

## Interfaces and Dependencies

Session 00 adds no runtime interface. Later sessions should use stable field names unless the
Session 01 spec chooses different names:

- `optimizer_run_metadata`
- `construction_disclosure.optimizer_methodology`
- `solver_success`
- `solver_status`
- `fallback_used`
- `fallback_reason`
- `optimization_quality_status`
- `analysis_end`
- `window_months`
- `eligible_universe`
- `returns_panel_fingerprint`
- `config_fingerprint`
- `universe_fingerprint`
- `optimizer_covariance_methodology_v1`
- `optimizer_young_etf_methodology_v1`
- `young_etf_methodology`

These are planned public contract names, not implemented fields until the relevant later session
updates specs, code, and tests.

Revision note, 2026-05-21: Session 00 persisted the active Block 5 roadmap and project-memory
links. No optimizer behavior was changed.

Revision note, 2026-05-21: Session 01 added the canonical Optimization Engine layer spec and
documentation indexes. No optimizer behavior, runtime outputs, generated artifacts, formulas,
constraints, objectives, gates, or status semantics were changed.

Revision note, 2026-05-21: Session 02 added the global target-only optimizer objective decision and
Optimization Engine spec appendix. No optimizer behavior, runtime outputs, generated artifacts,
formulas, constraints, objectives, gates, or status semantics were changed.

Revision note, 2026-05-21: Session 03 added legacy policy `optimizer_run_metadata` disclosure to
`run_result.json` and updated the owning docs/tests. No optimizer formulas, constraints, fallback
behavior, mandate gates, or generated weights were changed.

Revision note, 2026-05-21: Session 04 added candidate optimizer `optimizer_run_metadata`
disclosure to optimizer candidate `baseline_weights_metadata.json` exports and updated owning
docs/tests. No optimizer formulas, constraints, fallback behavior, mandate gates, comparison
semantics, generated weights, or generated artifacts were changed.

Revision note, 2026-05-21: Session 05 added comparison-level optimizer methodology passthrough in
`candidate_comparison.json` rows and updated owning docs/tests. No optimizer formulas, constraints,
fallback behavior, mandate gates, row status semantics, generated weights, or generated artifacts
were changed.

Revision note, 2026-05-21: Session 06 formalized fallback/failure quality propagation through
factory, comparison, and Selection boundaries and updated owning docs/tests. No optimizer formulas,
constraints, fallback behavior, mandate gates, generated weights, or generated artifacts were
changed.

Revision note, 2026-05-21: Session 07 added robust scenario solver status disclosure to robust
scenario summary and materialized candidate metadata, then updated factory/comparison specs and
tests. No optimizer formulas, constraints, fallback behavior, mandate gates, or generated weights
were changed.

Revision note, 2026-05-21: Session 08 added estimator input fingerprints and explicit
`analysis_end` disclosure to legacy/candidate optimizer metadata and fixed candidate young-ETF dual
covariance calls to use the wrapper `analysis_end`. No optimizer formulas, constraints, fallback
behavior, mandate gates, comparison semantics, generated weights, or generated artifacts were
changed.

Revision note, 2026-05-21: Session 09 added covariance and Young ETF methodology disclosure to
legacy/candidate optimizer metadata and compact TXT summaries. No optimizer formulas, constraints,
fallback behavior, mandate gates, comparison semantics, generated weights, or generated artifacts
were changed.

Revision note, 2026-05-21: Session 10 added optimization comparison readiness disclosure to
`candidate_comparison.json` and `candidate_comparison.txt`. No optimizer formulas, constraints,
fallback behavior, mandate gates, comparison ranking, generated weights, or generated artifacts
were changed.

Revision note, 2026-05-21: Session 11 (`RM-1001`) added Block 5 golden contract fixtures and tests;
finalized `TESTING.md` governance bundle (159 passed). No optimizer behavior changed. Resume Session
12 for wave closure.

Revision note, 2026-05-21: Session 12 (`RM-1002`) closed Phase 15 — documentation sync, gap index,
registers, baseline snapshot closure; governance bundle **159 passed**; `verify_docs` OK. Block 5
wave complete; no optimizer behavior changed.
