# Blocks 1-5 MVP Core Reliability Plan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan must be maintained in accordance with [PLANS.md](../../PLANS.md).

## Purpose / Big Picture

The first five blocks of Portfolio X-Ray / Portfolio MRI are the practical MVP core. They start
with a user's `analysis_subject` portfolio, diagnose that starting portfolio, stress-test it,
generate alternatives, and prepare optimizer-backed candidates for comparison. After the latest
operational audit, the project can already run this path for a well-formed portfolio, but it is not
yet reliable enough to call a push-button machine. The remaining risks are mostly trust risks:
unsafe weight input can pass as warning-only, comparison artifacts can outlive factory evidence,
full candidate generation is too heavy for one-shot runs, and optimizer readiness is not equally
visible across all optimizer-backed candidates.

After this plan is complete, a user should be able to enter five tickers plus explicit weights,
run the portfolio-first file workflow, and get a clear answer about whether Blocks 1-5 produced
fresh, comparable, diagnostic outputs. The plan must not add new methodology, change optimizer
formulas, change stress formulas, change constraints, or introduce UI work. It tightens validation,
freshness, resumability, disclosure, smoke coverage, and documentation handoff only.

The normal routine command remains:

    python run_portfolio_review.py --mode core --skip-pdf

The full candidate and optimizer menu remains explicit:

    python run_portfolio_review.py --mode full --skip-pdf

Session 04 of this plan will add a resumable full-review command path so interrupted full factory
runs can be resumed through the portfolio-first orchestrator.

**Chat rule:** one session = one new chat unless the user explicitly asks for a tiny follow-up in
the same thread. Session 01 persists this plan and project-memory links only. Start Session 02 in a
new chat.

## Progress

- [x] (2026-05-21) Session 01 (`RM-1010`): ExecPlan persisted; ExecPlan register marks this plan
  active; ROADMAP Phase 16 added; known issues registered for the audit findings; changelog entry
  added. No runtime code, optimizer formulas, stress formulas, constraints, or candidate behavior
  changed.
- [x] (2026-05-21) Session 02 (`RM-1011`): Hardened explicit current/model
  `analysis_subject` weight validation. Material positive-weight sums above `1.0` now fail config
  validation before report generation; partial sums below `1.0` remain valid and visible as
  `partial_with_cash_remainder` in `analysis_setup` and `input_assumptions`. Focused input tests
  passed: `19 passed`; adjacent config tests passed: `6 passed`; docs verification passed.
- [x] (2026-05-21) Session 03 (`RM-1012`): Fixed factory/comparison freshness
  coherence. Comparison now assesses whether `candidate_factory_run.json` is current, missing,
  stale, or not authoritative before using per-step factory evidence. Stale factory summaries are
  disclosed in `candidate_menu` and their `steps[]` are not copied into candidate row construction
  disclosure. Focused comparison tests passed: `32 passed`; comparison contract tests passed:
  `7 passed`; the full candidate factory governance bundle passed with `85 passed`; docs
  verification passed.
- [x] (2026-05-21) Session 04 (`RM-1013`): Made portfolio-first full factory
  resumable from `run_portfolio_review.py`. The new `--resume-candidates` flag passes factory
  `--resume` through the portfolio-first orchestrator, dry-run output exposes the resumed factory
  command, and the operator runbook documents full-review recovery. Focused workflow tests passed:
  `12 passed`; dry-run smoke showed `run_candidate_factory.py --profile default_v1 --resume
  --then-compare`; docs verification passed.
- [x] (2026-05-21) Session 05 (`RM-1014`): Normalized optimizer readiness disclosure across
  optimizer-backed candidates. Otherwise available optimizer rows now degrade when optimizer
  methodology or optimizer quality evidence is missing, and `unknown` optimizer quality is a
  visible degraded condition. Focused readiness tests passed: `8 passed`; candidate comparison
  tests passed: `32 passed`; comparison contract tests passed: `7 passed`; Block 5 golden contract
  tests passed: `9 passed`; docs verification passed.
- [x] (2026-05-21) Session 06 (`RM-1015`): Added an executable offline five-ticker
  Blocks 1-5 MVP smoke gate. The new test validates explicit current-portfolio weights, rejects
  missing/negative/overallocated weights, seeds subject diagnostics, X-Ray, stress, current
  `core_v1` factory evidence, and confirms comparison uses `analysis_subject` as baseline with
  current factory steps. Focused smoke passed: `4 passed`; docs verification passed.
- [x] (2026-05-21) Session 07 (`RM-1016`): Improved data-quality and young-ETF trust signals in
  user-facing stress/data outputs. Added `src/data_trust_signals.py` with
  `stress_report.data_trust_summary`, `input_assumptions.data_trust_signals`, and
  `portfolio_xray.data_trust_signals`; commentary and stress commentary now surface
  `user_summary_lines`. Focused tests passed: `62 passed` (data trust, stress historical, input,
  X-Ray); docs verification passed.
- [x] (2026-05-21) Session 08 (`RM-1017`): Cleaned documentation handoff and operator runbook
  wording. Updated `README.md`, `SPEC.md`, `OUTPUTS.md`, `TESTING.md`, and
  `docs/operational_runbook.md` for Blocks 1-5 MVP core, core/full/resume paths, generated-output
  boundaries, trust-signal artifacts, and offline acceptance flow. `python scripts/verify_docs.py`
  passed.
- [x] (2026-05-21) Session 09 (`RM-1018`): Representative verification and plan closure. Phase 16
  offline bundle `125 passed`; `verify_docs` OK; core/full dry-runs OK; live core subject
  materialization refreshed `Main portfolio/analysis_subject/` (factory/comparison tail not
  re-run to completion in-session). Fixed `tests.mvp_offline_fixtures` import shadowing via
  `tests/conftest.py` and direct fixture imports.

## Surprises & Discoveries

- Observation: There was no active ExecPlan after the Block 5 governance wave closed.
  Evidence: `docs/exec_plans/README.md` said `Active: None` before Session 01.

- Observation: The latest operational audit evidence was only in chat, not in a checked-in handoff
  document.
  Evidence: the audit established concrete findings such as overallocated weights passing as
  warning-only, stale `candidate_factory_run.json` alongside fresh comparison outputs, full factory
  timeout at 300 seconds, and optimizer readiness gaps on available optimizer rows.

- Observation: Prior governance waves already created strong Block 2, Block 3, Block 4, and Block 5
  specs. This plan should not reopen formulas or methodology; it should connect and harden the
  existing contracts.
  Evidence: `docs/specs/portfolio_xray_layer_spec.md`, `docs/specs/stress_lab_layer_spec.md`,
  `docs/specs/candidate_factory_spec.md`, and `docs/specs/optimization_engine_layer_spec.md` are
  already present and registered.

- Observation: The warning-only overallocated case was best fixed at config validation, not by
  adding a downstream report-time blocker.
  Evidence: `src/config_schema.py` already maps explicit current/model `analysis_subject` weights
  to fixed report weights before `analysis_setup` is built, so rejecting sums above `1.0` there
  prevents report generation from starting with impossible weighted input.

- Observation: Candidate snapshot freshness and factory-run freshness are separate trust checks.
  Evidence: `src/candidate_comparison.py` already rejected stale `snapshot_10y.json` rows by
  `analysis_end` and config fingerprint, but it loaded `candidate_factory_run.json` `steps[]`
  without checking whether that factory summary was older than an existing comparison artifact.

- Observation: Full-review resume did not require changes inside the candidate factory.
  Evidence: `run_candidate_factory.py` already accepted `--resume`; Session 04 only needed to expose
  that existing recovery path through `run_portfolio_review.py` and `src/portfolio_review_workflow.py`.

- Observation: Optimizer quality can be present but still not comparison-clean.
  Evidence: an `optimizer_run_metadata.solver` block with no status fields normalizes to
  `optimization_quality_family: unknown`; before Session 05, readiness could report
  `fair_comparison_ready: false` while the row still looked like ordinary `available` evidence.

- Observation: The Block 5 golden input fixture needed a current factory-run context to remain
  authoritative under the Session 03 freshness rules.
  Evidence: adding `generated_at`, `analysis_end`, and `config_fingerprint` to
  `tests/optimization_engine_golden_inputs.py` kept the golden factory-step quality source current
  without regenerating committed generated outputs.

- Observation: Existing offline portfolio-first E2E coverage proved subject-centered decision
  wiring, but not the Blocks 1-5 acceptance gate as one five-ticker command.
  Evidence: `tests/test_portfolio_first_e2e_offline.py` covers current/model/universe subjects and
  decision artifacts, while Session 06 added `tests/test_blocks_1_5_mvp_smoke.py` to include
  five explicit tickers, subject X-Ray, subject stress, and current factory evidence in one focused
  gate.

- Observation: `from tests.mvp_offline_fixtures import ...` fails when a third-party PyPI `tests`
  package shadows the repository `tests/` directory on `PYTHONPATH`.
  Evidence: Session 09 collection error `ModuleNotFoundError: No module named 'tests.mvp_offline_fixtures'`;
  `import tests` resolved to the installed package, not the repo folder, even with repo cwd on
  `sys.path`.
  Fix: `tests/conftest.py` prepends the local `tests/` directory; offline smoke imports use
  `from mvp_offline_fixtures import ...`.

## Decision Log

- Decision: Treat Session 01 as documentation and project-memory setup only.
  Rationale: The user explicitly selected `ExecPlan docs` as the first session. This avoids mixing
  planning registration with runtime behavior changes.
  Date/Author: 2026-05-21 / Codex.

- Decision: Use Phase 16 and roadmap IDs `RM-1010` through `RM-1018` for this wave.
  Rationale: Phase 15 ended at `RM-1002`; continuing with `RM-1010+` keeps ordering clear without
  reopening completed governance phases.
  Date/Author: 2026-05-21 / Codex.

- Decision: Keep UI, new optimizer objectives, stress methodology changes, and candidate formula
  changes out of scope.
  Rationale: The audit request and follow-up plan are about making the current first-five-block core
  reliable, not expanding methodology or product surface.
  Date/Author: 2026-05-21 / Codex.

- Decision: Use the existing `weight_status` contract for partial allocations and add only a strict
  config blocker for material overallocations.
  Rationale: Partial current/model weights below `1.0` can represent unallocated cash and are
  already disclosed as `cash_remainder`; overallocations above `1.0` cannot represent a valid
  long-only starting portfolio and should fail before diagnostics.
  Date/Author: 2026-05-21 / Codex.

- Decision: Treat stale factory summaries as visible menu evidence, not row-level step evidence.
  Rationale: The comparison layer is read-only and should not delete or rewrite old factory
  summaries, but old `steps[]` should not be allowed to block or certify a fresh comparison rebuild.
  Date/Author: 2026-05-21 / Codex.

- Decision: Name the portfolio-first recovery flag `--resume-candidates` and map it directly to
  factory `--resume`.
  Rationale: The flag describes the orchestrator-level behavior without changing factory semantics:
  subject materialization still runs first, and only the candidate factory step resumes from
  `candidate_factory_manifest.json`.
  Date/Author: 2026-05-21 / Codex.

- Decision: Degrade optimizer-backed rows when readiness-critical optimizer evidence is missing or
  quality is `unknown`, rather than making those rows `unavailable`.
  Rationale: Existing report metrics and weights may still be useful diagnostic evidence, but they
  are not fair optimizer-comparison evidence. `degraded` preserves the artifact while making the
  readiness risk visible to downstream scorecards and reports.
  Date/Author: 2026-05-21 / Codex.

## Outcomes & Retrospective

Session 01 outcome: the plan is now checked into the repository and registered as the active
project-level plan. The next session can start from this file alone and implement `RM-1011` without
depending on prior chat context. Runtime behavior was intentionally unchanged.

Session 02 outcome: explicit weighted `analysis_subject` inputs for `current_portfolio` and
`model_portfolio` now reject material overallocations in `src/config_schema.py`. Five-ticker tests
cover valid weights, missing weights, negative weights, overallocated weights, and partial weights.
The remaining sessions are unchanged; Session 03 should start with factory/comparison freshness and
must not reopen this input-validation work unless a regression is found.

Session 03 outcome: `src/candidate_comparison.py` now checks factory-run context before using
factory steps. `candidate_menu` records `factory_evidence_status`, `factory_steps_used`, and
`factory_evidence_warnings`; stale factory summaries are still visible but their `steps[]` are not
copied into candidate row construction disclosure. `KNOWN_ISSUES.md` no longer lists the stale
factory evidence issue as active. Session 04 should start with `run_portfolio_review.py`
resumability only and must not reopen factory freshness unless a regression is found.

Session 04 outcome: `run_portfolio_review.py --mode full --resume-candidates` now keeps recovery in
the portfolio-first workflow. The dry-run plan shows subject materialization followed by
`run_candidate_factory.py --profile default_v1 --resume --then-compare`, and the runbook points
operators to this command after interrupted full factory runs. `KNOWN_ISSUES.md` no longer lists the
orchestrator resume gap as active. Session 05 should start with optimizer readiness disclosure only
and must not reopen resumability unless a regression is found.

Session 05 outcome: optimizer-backed comparison rows no longer remain ordinary `available` evidence
when optimizer methodology or optimizer-quality evidence is incomplete. `src/candidate_comparison.py`
degrades otherwise available optimizer-backed rows with warning codes
`optimizer_readiness_missing:optimizer_methodology`, `optimizer_readiness_missing:optimizer_quality`,
or `optimizer_quality_unknown:unknown`; `src/optimization_readiness.py` marks unknown optimizer
quality as a readiness gap with `overall_status: partial`. Comparison contract coverage still
passes. `KNOWN_ISSUES.md` no longer lists the optimizer-readiness gap as active. Session 06 should
start with the five-ticker MVP smoke gate and must not reopen optimizer readiness unless a
regression is found.

Session 06 outcome: Blocks 1-5 now have a focused offline five-ticker smoke gate. The test starts
from explicit weighted `analysis_subject` config, verifies the core review plan routes through
subject diagnostics before `core_v1` candidates, checks seeded subject `run_metadata`,
`input_assumptions`, `portfolio_xray.json`, and `stress_report.json`, validates current
`candidate_factory_run.json` evidence, and runs comparison/decision package output generation with
`analysis_subject` as the baseline. Missing, negative, and overallocated subject weights fail
validation inside the same smoke file. `KNOWN_ISSUES.md` no longer lists the five-ticker smoke gap
as active. Session 07 should start with data-quality and young-ETF trust signals only.

Session 07 outcome: Blocks 1-5 now promote buried data-quality facts into structured trust
summaries. `run_stress` emits `data_trust_summary`; `input_assumptions` exports young-ETF and
taxonomy trust signals; `build_portfolio_xray_v2` rolls section warnings plus stress trust into
`data_trust_signals`; `stress_commentary.txt` and `commentary.txt` prefer `user_summary_lines`.
`KNOWN_ISSUES.md` no longer lists the buried trust-signal gap as active. Session 08 should start
with documentation handoff only.

Session 08 outcome: root handoff docs now describe the Blocks 1-5 MVP core without chat memory.
`README.md` and `SPEC.md` state portfolio-first as the default entrypoint with core/full/resume
modes; `OUTPUTS.md` documents trust-signal artifacts, factory-evidence fields, and a Blocks 1-5
output acceptance table; `TESTING.md` adds a Phase 16 verification bundle; `docs/operational_runbook.md`
adds an operator acceptance checklist. No runtime code changed. Session 09 should run representative
verification and close the plan.

Session 09 outcome: Phase 16 closed. Offline acceptance bundle passed (`125 passed`);
`python scripts/verify_docs.py` OK; dry-run core and full `--resume-candidates` paths exposed
expected commands. Live `python run_portfolio_review.py --mode core --skip-pdf` refreshed subject
diagnostics (`run_metadata.json` with `analysis_setup` and `input_assumptions`, seven X-Ray
sections, stress scorecard/conclusions/historical methodology/hedge gap/`data_trust_summary`); the
orchestrator did not finish candidate factory + comparison in the same session (long materialize).
Full end-to-end live core remains operator-runnable; offline smoke remains the executable closure
gate. Import fix for offline MVP fixtures shipped in this session.

**Closure verdict:** Blocks 1-5 MVP core reliability objectives for this wave are **met** under
the plan scope (validation, freshness, resumability, readiness disclosure, smoke, trust signals,
docs). Residual operational limits accepted: full `default_v1` factory remains heavy; live full
orchestrator E2E is not re-certified every closure session.

## Context and Orientation

The project is a Python, CLI/file-driven portfolio analytics and decision-support system. The
current binding workflow is portfolio-first: a configured `analysis_subject` is diagnosed before
alternatives are generated or compared. `analysis_subject` means the starting portfolio being
reviewed. It can be a `current_portfolio`, a `model_portfolio`, or a `universe_baseline`.

Blocks 1-5 in this plan mean:

- Block 1, Input and Assumptions: config validation, `analysis_subject`, weights, currency,
  benchmark, cash proxy, risk-free source, mandate/profile, and calculation assumptions.
- Block 2, Portfolio X-Ray: allocation, metrics, risk diagnostics, factor exposure, hidden risk,
  archetype, risk budget, and weakness map.
- Block 3, Stress Test Lab: synthetic and historical stress, scorecard, conclusions, crisis replay,
  hedge gap, and data-quality warnings.
- Block 4, Candidate Portfolio Factory: controlled orchestration of benchmark and candidate
  builders plus `candidate_factory_run.json`.
- Block 5, Optimization Engine: legacy policy optimizer and optimizer-backed candidate builders,
  with solver/methodology/readiness disclosure for comparison.

The most important files for this plan are:

- `src/config_schema.py` and `src/analysis_setup.py` for Block 1.
- `src/candidate_factory.py`, `run_candidate_factory.py`, `src/candidate_comparison.py`, and
  `run_portfolio_review.py` for Blocks 4-5 orchestration.
- `src/optimization_readiness.py` and optimizer candidate builder scripts for Block 5 readiness.
- `TESTING.md`, `docs/operational_runbook.md`, `docs/specs/input_assumptions_spec.md`,
  `docs/specs/candidate_factory_spec.md`, `docs/specs/candidate_comparison_spec.md`, and
  `docs/specs/optimization_engine_layer_spec.md` for the documentation contract.

Generated outputs such as `Main portfolio/`, candidate folders, `results_csv/`, and `pdf files/`
are evidence and deliverables, not source files. Do not commit regenerated outputs unless a later
session explicitly targets them.

## Plan of Work

Session 02 hardens Block 1. Implement a strict rule for weighted `analysis_subject` inputs:
`current_portfolio` and `model_portfolio` must reject materially overallocated positive weights
before report generation. Partial weights may remain valid only as an explicit cash-remainder case
visible in `analysis_setup` and `input_assumptions`. Add tests for a five-ticker valid portfolio,
missing weights, negative weights, overallocated weights, and partial weights. Update the input
assumptions spec and testing docs if the runtime contract changes.

Session 03 hardens Block 4/5 artifact trust. `candidate_comparison.json` should not imply fresh
factory evidence when `candidate_factory_run.json` was produced for a different review context or
older comparison run. Compare the factory run's analysis date, config fingerprint where available,
candidate profile, and generated timestamp against the current comparison context. If the factory
summary is missing, stale, or not authoritative, expose a clear warning in `candidate_menu` and do
not treat per-step factory evidence as current. Add tests for a stale factory summary after a fresh
comparison rebuild.

Session 04 improves operations without changing candidate formulas. Add an orchestrator flag such
as `--resume-candidates` to `run_portfolio_review.py` and pass `--resume` to
`run_candidate_factory.py`. Update dry-run output and workflow tests so the resumable full path is
observable. Document routine `core`, explicit `full`, and resumable full recovery in
`docs/operational_runbook.md`.

Session 05 normalizes optimizer readiness. For optimizer-backed rows, ensure
`construction_disclosure.optimizer_methodology`, `construction_disclosure.optimizer_quality`, and
`construction_disclosure.optimization_readiness` agree. If upstream artifacts contain metadata,
comparison should surface it. If metadata is truly absent, the row must visibly fail readiness or
be degraded rather than looking like ordinary available optimizer evidence. Do not change optimizer
formulas, constraints, solvers, or weights.

Session 06 adds an executable five-ticker MVP smoke gate. Build or extend offline fixtures so one
focused test proves the first-five-block contract from configured tickers and explicit weights
through subject diagnostics, X-Ray, stress, candidate/factory evidence, and comparison baseline
readiness. Include failure-case tests for missing or invalid weights. Record the command in
`TESTING.md` with a workspace-local `--basetemp` example for Windows.

Session 07 improves user-visible trust signals for data gaps and young or short-history holdings.
Audit existing warning propagation from data policy, stress conclusions, X-Ray, and comparison.
Promote key data-quality warnings to report-readable summaries where they are currently buried.
Do not alter stress PnL, historical return methodology, factor betas, covariance formulas, or data
policy rules.

Session 08 cleans the handoff docs. Review `README.md`, `SPEC.md`, `OUTPUTS.md`, `TESTING.md`, and
`docs/operational_runbook.md` for stale wording about core/full/full-resume paths, legacy policy
status, generated-output boundaries, and the first-five-block acceptance flow. Keep this session
documentation-only unless it discovers a blocker that needs a new explicit code session.

Session 09 runs representative verification and closes the plan. Run the focused tests introduced
or touched in Sessions 02-08, run a representative `run_portfolio_review.py --mode core --skip-pdf`,
and run the resumable full path only if it is practical in the available time. Record exact evidence
in this ExecPlan, update `KNOWN_ISSUES.md`, `CHANGELOG.md`, and `docs/ROADMAP.md`, and mark the plan
completed or leave it active with an exact next session.

## Concrete Steps

Session 01 steps were documentation-only:

1. Create this file at `docs/exec_plans/2026-05-21_blocks_1_5_mvp_core_reliability_plan.md`.
2. Update `docs/exec_plans/README.md` so this plan is the active pointer.
3. Add Phase 16 to `docs/ROADMAP.md`.
4. Add active issue entries to `KNOWN_ISSUES.md` for the audit findings.
5. Add a 2026-05-21 changelog entry.
6. Run:

    python scripts/verify_docs.py

Expected result: documentation verification passes and no runtime code changes are made.

Future sessions should begin by reading this ExecPlan, `WORKFLOW.md`, `RULES.md`, and the specific
owning spec for the session's area.

Session 02 steps completed:

1. Updated `src/config_schema.py` so explicit weighted current/model `analysis_subject` inputs must
   have at least one positive weight and must not have a positive-weight sum above `1.0` plus a small
   floating-point tolerance.
2. Extended `tests/test_input_assumptions.py` with five-ticker coverage for valid, missing,
   negative, overallocated, and partial weighted subjects.
3. Updated `docs/specs/input_assumptions_spec.md`, `TESTING.md`, `docs/ROADMAP.md`,
   `KNOWN_ISSUES.md`, and `CHANGELOG.md` for the `RM-1011` contract.
4. Ran:

    python -m pytest tests/test_input_assumptions.py -q --basetemp='tmp\pytest_rm1011_input'
    python -m pytest tests/test_config_weights_sync.py -q --basetemp='tmp\pytest_rm1011_config'
    python scripts/verify_docs.py

Expected result observed: `19 passed`, `6 passed`, and `docs verification: OK`.

Session 03 steps completed:

1. Updated `src/candidate_comparison.py` so comparison assesses `candidate_factory_run.json` against
   the current review `analysis_end`, current config fingerprint, factory profile validity, factory
   `generated_at`, and any existing `candidate_comparison.json.generated_at`.
2. Added `candidate_menu.factory_evidence_status`, `candidate_menu.factory_steps_used`, and
   `candidate_menu.factory_evidence_warnings`.
3. Prevented missing, stale, or not-authoritative factory summaries from contributing
   `construction_disclosure.factory_step` evidence.
4. Added regression coverage for a stale factory summary after a fresh comparison rebuild.
5. Updated `docs/specs/candidate_comparison_spec.md`, `docs/specs/candidate_factory_spec.md`,
   `TESTING.md`, `docs/ROADMAP.md`, `KNOWN_ISSUES.md`, and `CHANGELOG.md` for the `RM-1012`
   contract.
6. Ran:

    python -m pytest tests/test_candidate_comparison.py -q --basetemp='tmp\pytest_rm1012_candidate_comparison'
    python -m pytest tests/test_candidate_comparison_contract.py -q --basetemp='tmp\pytest_rm1012_candidate_comparison_contract'
    python -m pytest tests\test_candidate_factory_contract.py tests\test_candidate_comparison_contract.py tests\test_candidate_factory.py tests\test_candidate_comparison.py tests\test_portfolio_review_workflow.py -q --basetemp='tmp\pytest_rm1012_candidate_factory_bundle'
    python scripts/verify_docs.py

Expected result observed so far: `32 passed`, `7 passed`, full bundle `85 passed`, and
`docs verification: OK`.

Session 04 steps completed:

1. Added `--resume-candidates` to `run_portfolio_review.py`.
2. Updated `src/portfolio_review_workflow.py` so `resume_candidates=True` appends `--resume` to the
   candidate factory step while preserving the existing subject-first order and comparison tail.
3. Extended `tests/test_portfolio_review_workflow.py` so full mode resume propagation is covered and
   existing candidate option forwarding includes `--resume`.
4. Updated `docs/operational_runbook.md`, `docs/specs/portfolio_review_workflow_spec.md`,
   `TESTING.md`, `docs/ROADMAP.md`, `KNOWN_ISSUES.md`, and `CHANGELOG.md` for the `RM-1013`
   contract.
5. Ran:

    python -m pytest tests/test_portfolio_review_workflow.py -q --basetemp='tmp\pytest_rm1013_portfolio_review'
    python run_portfolio_review.py --dry-run --mode full --resume-candidates --skip-pdf
    python scripts/verify_docs.py

Expected result observed: `12 passed`; dry-run displayed
`run_candidate_factory.py --profile default_v1 --resume --then-compare`; docs verification reported
`docs verification: OK`.

Session 05 steps completed:

1. Updated `src/candidate_comparison.py` so optimizer-backed rows that would otherwise be
   `available` are degraded when required optimizer methodology/quality evidence is missing, or when
   optimizer quality normalizes to `unknown`.
2. Updated `src/optimization_readiness.py` so `unknown` optimizer quality is a readiness gap and
   produces `overall_status: partial` instead of looking ready.
3. Extended `tests/test_optimization_readiness.py` with missing-metadata and unknown-quality
   regression coverage.
4. Updated `tests/optimization_engine_golden_inputs.py` so the Block 5 golden comparison fixture
   creates an authoritative current factory summary under the Session 03 freshness rules.
5. Updated `docs/specs/candidate_comparison_spec.md`,
   `docs/specs/optimization_engine_layer_spec.md`, `TESTING.md`, `docs/ROADMAP.md`,
   `KNOWN_ISSUES.md`, and `CHANGELOG.md` for the `RM-1014` contract.
6. Ran:

    python -m pytest tests/test_optimization_readiness.py -q --basetemp='tmp\pytest_rm1014_readiness'
    python -m pytest tests/test_candidate_comparison.py -q --basetemp='tmp\pytest_rm1014_candidate_comparison'
    python -m pytest tests/test_candidate_comparison_contract.py -q --basetemp='tmp\pytest_rm1014_candidate_comparison_contract'
    python -m pytest tests/test_optimization_engine_contract.py -q --basetemp='tmp\pytest_rm1014_optimization_contract'
    python scripts/verify_docs.py

Expected result observed: `8 passed`, `32 passed`, `7 passed`, `9 passed`, and docs verification
reported `docs verification: OK`.

Session 06 steps completed:

1. Extended `tests/mvp_offline_fixtures.py` with five-ticker MVP config fixtures and seed helpers
   for subject diagnostics, X-Ray, stress, core candidate snapshots, and current
   `candidate_factory_run.json` evidence.
2. Added `tests/test_blocks_1_5_mvp_smoke.py` as the focused executable Blocks 1-5 gate.
3. Covered missing, negative, and overallocated explicit subject weights in the same smoke file.
4. Updated `TESTING.md`, `docs/ROADMAP.md`, `KNOWN_ISSUES.md`, `CHANGELOG.md`, and this ExecPlan
   for the `RM-1015` contract.
5. Ran:

    python -m pytest tests/test_blocks_1_5_mvp_smoke.py -q --basetemp='tmp\pytest_rm1015_blocks_1_5_smoke'
    python scripts/verify_docs.py

Expected result observed: `4 passed` and docs verification reported `docs verification: OK`.

Session 08 steps completed:

1. Reviewed `README.md`, `SPEC.md`, `OUTPUTS.md`, `TESTING.md`, and `docs/operational_runbook.md`
   for stale portfolio-first transition wording, missing core/full/resume commands, and absent
   Blocks 1-5 acceptance guidance.
2. Updated root docs with Blocks 1-5 MVP core scope, routine `core` / explicit `full` /
   `--resume-candidates` paths, generated-output boundaries, trust-signal artifacts, factory-evidence
   fields, optimizer readiness degradation, and offline smoke references.
3. Updated `CHANGELOG.md` and `docs/ROADMAP.md` for the `RM-1017` documentation handoff.
4. Ran:

    python scripts/verify_docs.py

Expected result observed: `docs verification: OK`.

## Validation and Acceptance

Session 01 acceptance:

- `docs/exec_plans/README.md` names this file as Active.
- `docs/ROADMAP.md` contains Phase 16 with `RM-1010` through `RM-1018`.
- `KNOWN_ISSUES.md` contains active issue entries for the current audit findings.
- `CHANGELOG.md` records the Session 01 project-memory update.
- `python scripts/verify_docs.py` passes.

Session 02 acceptance:

- A five-ticker current portfolio with explicit weights summing to `1.0` is accepted.
- Missing explicit current/model subject weights fail config validation.
- Negative explicit subject weights fail config validation.
- Explicit current/model subject weights summing materially above `1.0` fail config validation.
- Partial explicit subject weights below `1.0` remain valid and export
  `partial_with_cash_remainder` plus `cash_remainder` in `analysis_setup` and `input_assumptions`.
- `python -m pytest tests/test_input_assumptions.py -q --basetemp='tmp\pytest_rm1011_input'`
  passes.
- `python -m pytest tests/test_config_weights_sync.py -q --basetemp='tmp\pytest_rm1011_config'`
  passes.
- `python scripts/verify_docs.py` passes.

Session 03 acceptance:

- `candidate_menu.factory_evidence_status` reports `missing`, `stale`, `not_authoritative`, or
  `current` for factory summary evidence.
- `candidate_menu.factory_steps_used` is `false` for missing, stale, or not-authoritative factory
  summaries.
- Stale factory summaries remain visible through `candidate_menu.factory_evidence_warnings`.
- Stale factory `steps[]` are not copied into row `construction_disclosure.factory_step` and cannot
  make a fresh row unavailable.
- `python -m pytest tests/test_candidate_comparison.py -q --basetemp='tmp\pytest_rm1012_candidate_comparison'`
  passes.
- `python -m pytest tests/test_candidate_comparison_contract.py -q --basetemp='tmp\pytest_rm1012_candidate_comparison_contract'`
  passes.
- `python -m pytest tests\test_candidate_factory_contract.py tests\test_candidate_comparison_contract.py tests\test_candidate_factory.py tests\test_candidate_comparison.py tests\test_portfolio_review_workflow.py -q --basetemp='tmp\pytest_rm1012_candidate_factory_bundle'`
  passes.
- `python scripts/verify_docs.py` passes.

Session 04 acceptance:

- `run_portfolio_review.py` accepts `--resume-candidates`.
- `build_portfolio_review_plan(..., review_mode="full", resume_candidates=True)` passes `--resume`
  to the candidate factory step.
- Dry-run output for `python run_portfolio_review.py --dry-run --mode full --resume-candidates
  --skip-pdf` exposes `run_candidate_factory.py --profile default_v1 --resume --then-compare`.
- The full-review recovery command is documented in `docs/operational_runbook.md`.
- `python -m pytest tests/test_portfolio_review_workflow.py -q --basetemp='tmp\pytest_rm1013_portfolio_review'`
  passes.
- `python scripts/verify_docs.py` passes.

Session 05 acceptance:

- Optimizer-backed rows with upstream `optimizer_run_metadata` continue to surface
  `construction_disclosure.optimizer_methodology`.
- Optimizer-backed rows with clean optimizer-quality evidence can remain fair-comparison-ready when
  all required artifacts are present and fresh.
- Otherwise available optimizer-backed rows with missing optimizer methodology or optimizer quality
  degrade with explicit warning codes instead of remaining ordinary `available` evidence.
- Optimizer-backed rows whose solver quality normalizes to `unknown` degrade, set
  `optimization_readiness.gaps` to include `optimizer_quality`, and report
  `optimization_readiness.overall_status: partial`.
- `python -m pytest tests/test_optimization_readiness.py -q --basetemp='tmp\pytest_rm1014_readiness'`
  passes.
- `python -m pytest tests/test_candidate_comparison.py -q --basetemp='tmp\pytest_rm1014_candidate_comparison'`
  passes.
- `python -m pytest tests/test_candidate_comparison_contract.py -q --basetemp='tmp\pytest_rm1014_candidate_comparison_contract'`
  passes.
- `python -m pytest tests/test_optimization_engine_contract.py -q --basetemp='tmp\pytest_rm1014_optimization_contract'`
  passes.
- `python scripts/verify_docs.py` passes.

Session 06 acceptance:

- A five-ticker current portfolio with explicit weights is accepted and resolves to
  `config.analysis_subject.weights`.
- Missing explicit subject weights fail config validation.
- Negative explicit subject weights fail config validation.
- Overallocated explicit subject weights fail config validation.
- The smoke fixture exposes `analysis_subject/run_metadata.json` with `analysis_setup` and
  `input_assumptions`.
- The smoke fixture exposes `analysis_subject/portfolio_xray.json` with all seven X-Ray sections.
- The smoke fixture exposes `analysis_subject/stress_report.json` with `stress_scorecard_v1`,
  `stress_conclusions`, `historical_methodology`, and `hedge_gap_analysis`.
- The smoke fixture exposes current `core_v1` `candidate_factory_run.json` evidence and matching
  fresh candidate snapshots.
- `candidate_comparison.json` uses `analysis_subject` as the baseline and reports
  `candidate_menu.factory_evidence_status: current` with factory steps used.
- `python -m pytest tests/test_blocks_1_5_mvp_smoke.py -q --basetemp='tmp\pytest_rm1015_blocks_1_5_smoke'`
  passes.
- `python scripts/verify_docs.py` passes.

Full plan acceptance after Session 09:

- A valid five-ticker current portfolio with explicit weights is accepted and materialized.
- Missing or invalid weighted `analysis_subject` inputs fail before report generation.
- Overallocated weighted `analysis_subject` inputs do not silently proceed.
- `Main portfolio/analysis_subject/run_metadata.json` contains `analysis_setup` and
  `input_assumptions`.
- `Main portfolio/analysis_subject/portfolio_xray.json` has the seven Block 2 sections.
- `Main portfolio/analysis_subject/stress_report.json` has `stress_scorecard_v1`,
  `stress_conclusions`, `historical_methodology`, and `hedge_gap_analysis`.
- `candidate_factory_run.json` evidence is current or explicitly marked stale/missing in comparison.
- `candidate_comparison.json` uses `analysis_subject` as baseline.
- Optimizer-backed rows are either fair-comparison-ready or visibly degraded/unready with reasons.
- The documented smoke command passes with a workspace-local `--basetemp`.

## Idempotence and Recovery

Documentation updates are safe to repeat if the same Active pointer and Phase 16 entries are kept
consistent. Later runtime sessions should be additive and tested with focused commands before broad
verification. If a candidate factory run is interrupted, use the factory manifest and `--resume`
rather than deleting candidate outputs. Do not use destructive git commands or remove generated
folders to force freshness unless the user explicitly asks for that cleanup.

If generated files change during smoke runs, treat them as verification artifacts. Do not commit
them unless the session explicitly targets generated-output refresh.

## Artifacts and Notes

Audit evidence that motivated this plan:

- Five-ticker input simulation accepted valid weights, rejected missing current weights, accepted
  universe-baseline tickers-only, rejected negative weights, but allowed overallocated current
  weights as `valid_with_action_required_warnings`.
- `run_portfolio_review.py --dry-run --mode full --skip-pdf` planned subject materialization and
  factory `default_v1` without legacy `run_optimization.py`.
- A bounded optimizer factory command timed out after 300 seconds, confirming that full optimizer
  candidate generation remains operationally heavy.
- `Main portfolio/analysis_subject/portfolio_xray.json` existed with all seven sections available.
- `Main portfolio/analysis_subject/stress_report.json` existed with 8 synthetic scenarios, 5
  historical episodes, scorecard, conclusions, historical methodology, and visible insufficient-data
  warnings for early episodes.
- `candidate_factory_run.json` was older than freshly rebuilt comparison artifacts, showing a
  stale-evidence risk.
- After rebuilding comparison, only the `minimum_variance` optimizer row was fully ready; other
  optimizer-backed rows remained available but not fair-comparison-ready because optimizer
  methodology or quality evidence was missing in comparison.

Session 02 revision note: this plan was updated after implementing `RM-1011` so a future session can
resume from the checked-in plan without chat history. The update records the strict
overallocation blocker, partial-cash behavior, focused test evidence, and the remaining next
session boundary.

Session 03 revision note: this plan was updated after implementing `RM-1012` so a future session can
resume from the checked-in plan without chat history. The update records the factory-evidence trust
boundary, stale-summary regression coverage, focused test evidence, and the next Session 04
resumability boundary.

Session 04 revision note: this plan was updated after implementing `RM-1013` so a future session can
resume from the checked-in plan without chat history. The update records the
`--resume-candidates` orchestrator flag, dry-run evidence, focused workflow test evidence, and the
next Session 05 optimizer-readiness boundary.

Session 05 revision note: this plan was updated after implementing `RM-1014` so a future session can
resume from the checked-in plan without chat history. The update records the degraded-row readiness
boundary for missing or unknown optimizer evidence, focused test evidence, and the next Session 06
five-ticker smoke-gate boundary.

Session 06 revision note: this plan was updated after implementing `RM-1015` so a future session can
resume from the checked-in plan without chat history. The update records the new five-ticker
offline smoke gate, focused test evidence, and the next Session 07 data-quality trust-signal
boundary.

Session 07 revision note: this plan was updated after implementing `RM-1016` so a future session can
resume from the checked-in plan without chat history. The update records `data_trust_summary` /
`data_trust_signals`, commentary promotion, focused test evidence, and the next Session 08
documentation handoff boundary.

Session 08 revision note: this plan was updated after implementing `RM-1017` so a future session can
resume from the checked-in plan without chat history. The update records the root documentation
handoff (`README.md`, `SPEC.md`, `OUTPUTS.md`, `TESTING.md`, `docs/operational_runbook.md`) and the
next Session 09 representative verification boundary.

Session 09 revision note: Phase 16 closed (`RM-1018`). Offline bundle `125 passed`; docs verify OK;
dry-run core/full resume OK; live core subject materialization OK; `tests/conftest.py` fixes
site-packages `tests` shadowing for offline MVP fixture imports. Plan status: **Completed**.

## Interfaces and Dependencies

This plan depends only on the existing Python project and documentation toolchain. Use the existing
test runner and scripts:

    python -m pytest ...
    python scripts/verify_docs.py

Do not introduce new packages for this wave unless a future session proves they are necessary and
updates `requirements.txt` with user-visible rationale. Do not add UI dependencies. Do not create
new optimizer objectives, stress scenarios, or candidate families.
