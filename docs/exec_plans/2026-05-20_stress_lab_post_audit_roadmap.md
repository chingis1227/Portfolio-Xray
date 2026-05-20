# Stress Lab Post-Audit Roadmap

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan must be maintained in accordance with `PLANS.md`.

## Purpose / Big Picture

This plan turns the current stress-testing layer into a stable, decision-useful portfolio-first
diagnostic contract for `analysis_subject`. After this wave, the stress layer should be trusted
for downstream decision artifacts because it will have explicit quality signals, standardized
conclusion blocks, stronger scenario/replay coverage, and cleaner reporting boundaries.

## Progress

- [x] (2026-05-20 07:30Z) Session 00 baseline snapshot captured in `docs/audits/2026-05-20_stress_lab_baseline_snapshot.md`.
- [x] (2026-05-20 07:49Z) Session 00 baseline re-verified: baseline artifacts exist, hash fingerprints match snapshot values, and baseline checklist blocks are present.
- [x] (2026-05-20 08:02Z) Session 01 completed: representative run produced `regime_portfolio_metrics` with no `regime_portfolio_metrics_error`; `historical_results` keeps explicit `coverage_ratio` and `data_quality` fields for all episodes; stress commentary preserves non-binding wording against mandate gates.
- [x] (2026-05-20) Session 02: `stress_scorecard_v1` and `stress_conclusions` contract hardening.
- [x] (2026-05-20) Session 03: historical quality and replay path v1.
- [x] (2026-05-20) Session 04: `hedge_gap_analysis` contract.
- [x] (2026-05-20) Session 05: scenario coverage expansion.
- [x] (2026-05-20) Session 06: synthetic engine hardening.
- [x] (2026-05-20) Session 07: portfolio-first stress integration hardening.
- [x] (2026-05-20) Session 08: reporting and commentary decision usefulness.
- [x] (2026-05-20) Session 09: simulator API foundation (no UI).
- [x] (2026-05-20) Session 10: final verification and documentation pack.

## Surprises & Discoveries

- Observation: A dedicated baseline snapshot for this wave already exists and includes a fixed
  artifact fingerprint checklist.
  Evidence: `docs/audits/2026-05-20_stress_lab_baseline_snapshot.md`.

- Observation: Some Session 01 goals are likely partially addressed by prior fixes and may need
  confirmation rather than full reimplementation.
  Evidence: prior roadmap rows such as `RM-906` and stress-layer fields already present in
  `src/stress.py`.

- Observation: `snapshot_10y.json` stress mirror uses compact keys (`overall`, `scenarios`) rather
  than full `stress_report.json` names (`status`, `scenario_results`).
  Evidence: `Main portfolio/analysis_subject/snapshot_10y.json` key inspection during Session 00
  re-verification.

- Observation: Session 01 checklist command listed a removed monolithic stress test module; the
  current repository uses
  `tests/test_stress_historical_fields.py`, `tests/test_stress_mandate_pass.py`,
  `tests/test_stress_scenario_analytics.py`, `tests/test_stress_covariance_taxonomy.py`, and
  (from Session 02) `tests/test_stress_scorecard_contract.py`.
  Evidence: test discovery in `tests/` during Session 01 execution.

## Decision Log

- Decision: Keep this roadmap as a project-local ExecPlan under `docs/exec_plans/` and treat it
  as the source for future session handoffs.
  Rationale: The original plan lived in Cursor Plans storage and was not visible in repository
  history for future chats.
  Date/Author: 2026-05-20 / Codex.

- Decision: Keep this plan in English even if chats with the user remain in Russian.
  Rationale: Project-facing documentation follows the English-only documentation policy.
  Date/Author: 2026-05-20 / Codex.

- Decision: For Session 01 verification, substitute the removed monolithic stress test module with the
  available stress-focused test bundle while preserving intended stress-layer coverage.
  Rationale: Keep execution aligned with actual repository test inventory and still validate stress
  contract behavior.
  Date/Author: 2026-05-20 / Codex.

## Outcomes & Retrospective

Initial setup outcome: the Stress Lab roadmap is now represented as a repository ExecPlan that can
be resumed by any future chat from project files only.

Session 00 re-verification outcome: baseline artifacts and fingerprints remain stable, so Session 01
can start without re-baselining. Noted caveat: snapshot stress mirror is semantically aligned but
uses compact field names.

Session 01 outcome: representative `run_report.py --materialize-analysis-subject` output contains
`regime_portfolio_metrics` and no `regime_portfolio_metrics_error`; historical episode rows in
`stress_report.json` carry explicit `n_obs`, `n_expected_obs`, `coverage_ratio`, and `data_quality`.
Stress commentary keeps explicit non-binding boundary wording ("diagnostics inform interpretation but
do not release/block weights"). Stress tests and docs verification passed on the adapted stress suite.

Session 02 outcome: `stress_scorecard_v1` and `stress_conclusions` hardened in `src/stress.py` with
`overall_confidence`, per-row `loss_severity` / `beta_confidence`, and unified builders;
`portfolio_commentary.py` prefers scorecard rows for synthetic summaries; spec §12.1 documents the
contract; `tests/test_stress_scorecard_contract.py` added.

Session 03 outcome: `historical_episode_paths` replay contract verified end-to-end — path max drawdown
matches aggregate `historical_results[*].max_dd`, row count equals `n_obs`, insufficient episodes
retain quality metadata without path blocks; CSV export contract covered in
`tests/test_stress_historical_fields.py`; baseline snapshot checklist item 11 added.

Session 04 outcome: `_build_hedge_gap_analysis` in `src/stress.py` aligns gap detection with spec
(portfolio loss required; hedge non-positive contribution); evidence fields
(`worst_scenario_portfolio_pnl_pct`, `n_hedge_assets_considered`, `gap_detected`);
`insufficient_data` when no hedge labels; `tests/test_stress_hedge_gap_contract.py`; stress commentary
lists weak hedges when `gap_detected`; specs and baseline known-gap updated.

Session 05 outcome: dedicated taxonomy calibration for `usd_shock` and `commodity_shock` in
`src/stress_covariance_taxonomy.py`; `WEAKNESS_SCENARIO_MAP` extended in `src/portfolio_xray.py`;
spec §10.1 lists all eight synthetic scenarios; `tests/test_stress_scenario_coverage_contract.py`
asserts canonical synthetic/historical ids (including `banking_2023`) in `stress_report`,
`stress_scorecard_v1`, and `scenario_library`; baseline known-gap closed.

Session 06 outcome: synthetic scenario rows now expose explicit fallback/proxy assumptions via
`synthetic_assumptions` (`version`, beta coverage/confidence, fallback usage, proxy method/targets)
in `src/stress.py`; `scenario_library` and `scenario_library_normalized` preserve this block for
downstream consumers; `snapshot_10y.stress_suite_results.scenarios[*]` mirrors it; spec §4 updated;
contract tests added in `tests/test_stress_synthetic_assumptions_contract.py`.

Session 07 outcome: downstream consumers now prioritize `analysis_subject` stress artifacts in
portfolio-first baseline contexts via shared resolver helpers in `src/stress_artifacts.py`;
`src/robustness_scorecard.py`, `src/portfolio_health_score.py`,
`src/tradeoff_and_model_risk.py`, and `src/regret_analysis.py` consume this resolver so baseline
stress reads no longer depend on implicit root-folder fallback; contract coverage added in
`tests/test_stress_artifacts_priority.py`; stress bundle and docs verification passed.

Session 08 outcome: reporting and commentary now surface the core stress decision context in plain
English. `write_stress_commentary` states worst synthetic/historical outcomes, main loss drivers,
hedge-gap interpretation, and confidence directly from `stress_conclusions` / `hedge_gap_analysis`.
`generate_ips_summary` mirrors the same context from `stress_diagnostic_report` when available.
Coverage added in `tests/test_portfolio_commentary.py` and
`tests/test_io_export_ips_summary.py`.

Session 09 outcome: What Happens If simulator API (no UI) in `src/stress.py` —
`simulate_custom_shock`, `shock_vector_from_scenario`, `_normalize_shock_vector`, versioned contract
`custom_shock_simulator_v1`. Custom shocks reproduce built-in `scenario_results` PnL fields for all
static scenarios and calibrated `recession_severe`. Spec §12.3 and layer spec §3.3 updated;
`tests/test_stress_simulator_contract.py` added.

Session 10 outcome: wave-level regression bundle (70 tests) and `python scripts/verify_docs.py`
passed; `TESTING.md` documents the Stress Lab bundle and refresh commands; baseline snapshot updated
with Session 10 closure; stale `test_write_portfolio_commentary_creates_file` assertions aligned with
current X-Ray commentary headings; exec-plan register marks this roadmap **Completed** (Sessions
00-10).

## Context and Orientation

Stress Lab in this repository is the stress diagnostics layer centered on `stress_report.json` in
the output folder for each run. In portfolio-first operation, the primary source is
`Main portfolio/analysis_subject/` after `run_report.py --materialize-analysis-subject`.

Key files and their roles:

- `src/stress.py`: scenario execution, historical episodes, scorecard/conclusions, hedge-gap fields.
- `run_report.py`: main materialization and export path for stress artifacts.
- `src/portfolio_commentary.py`: stress narrative generation and boundary wording.
- `src/stress_scenario_analytics.py`: stress analytics consistency and derived diagnostics.
- `src/snapshot.py`: downstream snapshot consumption of stress outputs.
- `docs/specs/stress_testing_spec.md`: canonical stress methodology and output contract.
- `docs/specs/stress_lab_layer_spec.md`: layer-level map for Stress Lab sub-blocks (3.1 to 3.6).
- `OUTPUTS.md`: generated artifact inventory and output locations.

## Plan of Work

Work must proceed one session per chat, in strict order:

Session 00 (completed) established baseline artifacts and hash fingerprints for regression checks.
Session 01 closes P0 trust risks: regime-block runtime reliability, explicit historical data quality
signals, and clear non-binding wording of stress diagnostics versus mandate gates. Session 02
hardens scorecard and conclusions into one machine-readable contract that downstream consumers can
read without parsing commentary.

Sessions 03 to 06 deepen methodology: historical path replay artifacts, explicit hedge-gap
diagnostics, expanded historical/synthetic scenario coverage, and synthetic fallback transparency.
Sessions 07 and 08 harden portfolio-first integration and client-facing interpretation. Session 09
adds a no-UI simulator primitive for custom shock vectors. Session 10 closes the wave with broad
verification and full documentation synchronization.

## Concrete Steps

For each session, use this kickoff:

    Continue `docs/exec_plans/2026-05-20_stress_lab_post_audit_roadmap.md`.
    Work on Session NN only.
    Read `AGENTS.md`, `WORKFLOW.md`, `RULES.md`, `PLANS.md`,
    `docs/specs/stress_testing_spec.md`, `docs/specs/stress_lab_layer_spec.md`,
    and `docs/audits/2026-05-20_stress_lab_baseline_snapshot.md`.
    Run `git status --short` before edits and do not revert unrelated dirty files.

Baseline and smoke commands for this wave:

    python run_report.py --materialize-analysis-subject
    python run_stress_variant.py --variant main
    python -m pytest tests/test_stress_scorecard_contract.py tests/test_stress_hedge_gap_contract.py tests/test_stress_scenario_coverage_contract.py tests/test_stress_synthetic_assumptions_contract.py tests/test_stress_simulator_contract.py tests/test_stress_mandate_pass.py tests/test_stress_scenario_analytics.py tests/test_stress_historical_fields.py tests/test_stress_covariance_taxonomy.py -q
    python scripts/verify_docs.py

Baseline hash comparison command:

    python -c "from pathlib import Path; import hashlib; base=Path('Main portfolio/analysis_subject'); files=['stress_report.json','stress_commentary.txt','results_csv/stress_scenario_analytics_summary.csv','scenario_library.json','scenario_library_normalized.json','snapshot_10y.json']; print('\n'.join(f'{f}|{hashlib.sha256((base/f).read_bytes()).hexdigest()}' for f in files if (base/f).exists()))"

## Validation and Acceptance

Session-level acceptance:

- Session 01: representative run has no `regime_portfolio_metrics_error`; incomplete historical
  episodes are explicitly marked by coverage/data-quality metadata.
- Session 02: one stable block exposes scenario severity, pass/fail, top contributors, and
  confidence/quality signals.
- Session 03: replay path artifacts write reliably and path max drawdown matches aggregate episode
  result.
- Session 04: hedge gaps are machine-readable with explicit status and evidence fields.
- Session 05: new scenarios appear in both stress report and scenario library artifacts with
  versioned metadata.
- Session 06: synthetic rows expose fallback/proxy assumptions directly in artifact fields.
- Session 07: downstream consumers consistently prioritize `analysis_subject` stress artifacts.
- Session 08: stress commentary and report language answer worst case, drivers, hedge gaps, and
  confidence in plain English.
- Session 09: custom shock simulation reproduces equivalent built-in scenario behavior for matching
  inputs.
- Session 10: wave-level regression checks pass and docs/spec indexes no longer contradict runtime.

## Idempotence and Recovery

This plan is safe to resume in any future chat. Always update `Progress` and the living sections at
the end of each session. If a session fails mid-way, keep completed substeps checked and convert the
remaining part into explicit pending entries. Do not edit generated output folders manually as source
unless a session explicitly targets generated artifacts.

## Artifacts and Notes

Baseline checkpoint artifact for this wave:

- `docs/audits/2026-05-20_stress_lab_baseline_snapshot.md`

Expected primary generated artifacts to track across sessions:

- `Main portfolio/analysis_subject/stress_report.json`
- `Main portfolio/analysis_subject/stress_commentary.txt`
- `Main portfolio/analysis_subject/results_csv/stress_scenario_analytics_summary.csv`
- `Main portfolio/analysis_subject/scenario_library.json`
- `Main portfolio/analysis_subject/scenario_library_normalized.json`
- `Main portfolio/analysis_subject/snapshot_10y.json`

## Interfaces and Dependencies

Use the existing stress stack and contracts as the only implementation surface:

- Runtime modules: `src/stress.py`, `run_report.py`, `src/stress_scenario_analytics.py`,
  `src/portfolio_commentary.py`, `src/snapshot.py`, `src/portfolio_xray.py`.
- Canonical specs: `docs/specs/stress_testing_spec.md`,
  `docs/specs/scenario_library_spec.md`,
  `docs/specs/portfolio_review_workflow_spec.md`,
  `docs/specs/reporting_outputs_spec.md`,
  `docs/specs/portfolio_xray_diagnostics_spec.md`.
- Governance docs: `WORKFLOW.md`, `TESTING.md`, `OUTPUTS.md`.

No new UI surface is in scope for this wave. Stress diagnostics remain non-binding unless canonical
specs explicitly change decision boundaries.

Revision note, 2026-05-20: Created this project-local Stress Lab roadmap ExecPlan by migrating the
existing Cursor Plan into repository documentation and translating it to English for durable handoff.

Revision note, 2026-05-20: Re-verified Session 00 baseline in-place (artifact existence, hashes, and
checklist presence) and documented the snapshot compact-key caveat for future sessions.

Revision note, 2026-05-20: Executed Session 01 acceptance checks and marked Session 01 complete with
evidence for regime-metrics reliability, historical coverage/data-quality signaling, and non-binding
stress wording.

Revision note, 2026-05-20: Session 03 completed — crisis replay path contract hardened with
acceptance tests (`max_dd` consistency, row count, CSV mirror); baseline snapshot known gap closed.

Revision note, 2026-05-20: Session 05 completed — dedicated taxonomy for `usd_shock` /
`commodity_shock`, scenario coverage contract tests, X-Ray weakness map, spec §10.1 update; baseline
known gap closed.

Revision note, 2026-05-20: Session 06 completed — synthetic fallback/proxy assumptions are explicit
in `scenario_results`, propagated to scenario-library and snapshot artifacts, and covered by a
dedicated contract test module.

Revision note, 2026-05-20: Session 07 completed — portfolio-first downstream consumers now resolve
baseline stress inputs with `analysis_subject` priority via `src/stress_artifacts.py`; coverage in
`tests/test_stress_artifacts_priority.py`; stress bundle and docs verification passed.

Revision note, 2026-05-20: Session 08 completed — stress commentary and IPS summary language now
explicitly answer worst case, loss drivers, hedge-gap status, and confidence in plain English from
structured stress fields, with focused test coverage.

Revision note, 2026-05-20: Session 09 completed — simulator API (`simulate_custom_shock`,
`shock_vector_from_scenario`) with built-in PnL equivalence tests; spec §12.3 and baseline known-gap
updated.

Revision note, 2026-05-20: Session 10 completed — Stress Lab wave closed (Sessions 00-10); regression
bundle and docs sync verified; plan status **Completed**.
