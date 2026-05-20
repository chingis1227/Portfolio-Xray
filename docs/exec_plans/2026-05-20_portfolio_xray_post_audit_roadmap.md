# Portfolio X-Ray Post-Audit Roadmap (Block 2 Governance)

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan must be maintained in accordance with `PLANS.md`.

## Purpose / Big Picture

After the Portfolio X-Ray Diagnostics Deepening wave (`RM-930`–`RM-939`, Sessions 00–09) and the
2026-05-20 methodology audit, Block 2 is technically present but not fully **audit-grade**. This
plan makes Portfolio X-Ray **transparent, defensible, and handoff-safe** before new heuristics or UI.

After this wave, a new agent should be able to resume from:

- [Portfolio X-Ray Methodology Map](../audits/2026-05-20_portfolio_xray_methodology_map.md)
- this ExecPlan
- [portfolio_xray_diagnostics_spec.md](../specs/portfolio_xray_diagnostics_spec.md)

without chat history.

**Non-goals:** new optimizer logic, mandate gates, candidate selection, binding recommendations, or
silent changes to `XRAY_THRESHOLDS` without spec ownership.

## Progress

- [x] (2026-05-20) Session 00: Methodology map audit, this ExecPlan, audit/plan registers, ROADMAP Phase 12 rows.
- [x] (2026-05-20) Session 01: Documentation sync (`KNOWN_ISSUES`, `RM-932`, `CHANGELOG`, `TESTING` bundle stub).
- [x] (2026-05-20) Session 02 (`RM-942`): Canonical threshold registry.
- [x] (2026-05-20) Session 03 (`RM-943`): Section provenance metadata.
- [x] (2026-05-20) Session 04 (`RM-944`): Factor regression inference panel.
- [x] (2026-05-20) Session 05 (`RM-945`): Multi-window metrics + TTR.
- [x] (2026-05-20) Session 06 (`RM-946`): `portfolio_xray_layer_spec.md`.
- [x] (2026-05-20) Session 07 (`RM-947`): Allocation concentration diagnostics.
- [x] (2026-05-20) Session 08 (`RM-948`): `volatility_spike` methodology decision.
- [x] (2026-05-20) Session 09 (`RM-949`): Golden contract tests + QA bundle.
- [x] (2026-05-20) Session 10: Baseline snapshot and wave closure.

## Surprises & Discoveries

- Observation: Deepening Session 02 already fixed RC CSV and Kalman mapping in code and tests, but
  `KNOWN_ISSUES.md` and `docs/ROADMAP.md` still listed `RM-932` as open/planned until Session 01.
  Evidence: `tests/test_portfolio_xray.py` (`test_resolve_rc_asset_prefers_full_csv_over_snapshot_top5`,
  `test_portfolio_xray_v2_kalman_reads_factor_betas_kalman_latest`).

- Observation: Resolved KNOWN_ISSUES entries `KI-2026-05-19-007` and `KI-2026-05-19-008` remained in
  the active list with stale next-action text after the fix shipped.
  Evidence: Session 01 register sync removed them; fixes recorded in CHANGELOG 2026-05-19.

- Observation: Unlike Block 3 (Stress Lab), Block 2 had no `portfolio_xray_layer_spec.md` until
  Session 06 (`RM-946`).
  Evidence: `docs/specs/stress_lab_layer_spec.md` existed earlier; X-Ray layer spec added 2026-05-20.

- Observation: Three threshold keys (`top3_rc_high`, `factor_residual_moderate`, `factor_residual_high`)
  are exported in `portfolio_xray.json.thresholds` but not referenced in V2 rule comparisons; kept
  for backward compatibility and documented as reserved in spec §8.
  Evidence: `rg` on `src/portfolio_xray.py`; `tests/test_portfolio_xray_threshold_registry.py`.

## Decision Log

- Decision: One chat = one session; start a new chat after each session unless the user explicitly
  requests a tiny follow-up in the same thread.
  Rationale: Block 2 governance spans spec, code, tests, and docs; separate sessions reduce context loss.
  Date/Author: 2026-05-20 / Agent.

- Decision: Session 00 is documentation and project memory only — no code or threshold changes.
  Rationale: Governance wave must record methodology before altering rules.
  Date/Author: 2026-05-20 / Agent.

- Decision: Default assumptions for later sessions unless the user overrides:
  threshold registry documents current values only (Session 02); HHI on capital weights only (Session 07);
  `volatility_spike` factor-only rule Option B (Session 08).
  Date/Author: 2026-05-20 / Agent.

## Outcomes & Retrospective

Session 00 outcome: methodology map persisted in
`docs/audits/2026-05-20_portfolio_xray_methodology_map.md`; this ExecPlan registered as **Active**;
Phase 12 (`RM-940`–`RM-949`) added to `docs/ROADMAP.md`. Session 01 can start with doc/register sync.

Session 01 outcome: `RM-932` and `RM-941` marked Done; stale `KI-2026-05-19-007` / `KI-2026-05-19-008`
removed from active KNOWN_ISSUES; CHANGELOG and TESTING.md Portfolio X-Ray bundle stub updated;
methodology map G9 closed. Session 02 can start with threshold registry (`RM-942`).

Session 02 outcome: `RM-942` Done — spec §8 documents all 34 `XRAY_THRESHOLDS` keys (current values
only, no numeric changes); `tests/test_portfolio_xray_threshold_registry.py` locks runtime to
canonical dict; methodology map G1/N1 closed; TESTING bundle includes threshold module. Session 03
can start with section provenance (`RM-943`).

Session 03 outcome: `RM-943` Done — sections `risk_diagnostics`, `factor_exposure`,
`risk_budget_view`, and `weakness_map` expose `method`, `frequency`, `window`, `n_obs`, and
`benchmark` per common section contract; `load_rc_vol_map_from_csv` returns the RC filename actually
loaded; HTML/text meta phrase includes benchmark; methodology map G2/N2 closed; spec §2.2–2.7 updated.
Session 04 can start with factor inference panel (`RM-944`).

Session 04 outcome: `RM-944` Done — `factor_exposure` includes read-only
`factor_regression_inference` items from `stress_report.factor_regression_5y/10y` (HAC t/p/CI,
multicollinearity, serial/heteroskedasticity summaries); text/HTML tables when betas present;
methodology map G3/N3 closed; spec §2.3 updated; tests
`test_portfolio_xray_factor_regression_inference_panel`. Session 05 can start with multi-window
metrics + TTR (`RM-945`).

Session 05 outcome: `RM-945` Done — `risk_diagnostics` exposes `ttr_months`/`recovered`/`treynor` on
primary `portfolio_metrics` and a read-only `multi_window_metrics` panel when snapshot horizons
provide metrics; `load_portfolio_windows_from_dir` wired through `snapshot.py` and
`portfolio_commentary.py`; methodology map G4/G5/N4 closed; spec §2.2 updated; tests
`test_portfolio_xray_multi_window_metrics_panel`, `test_portfolio_xray_ttr_in_primary_risk_metrics`,
`test_load_portfolio_windows_from_dir`. Session 06 can start with layer spec (`RM-946`).

Session 06 outcome: `RM-946` Done — `docs/specs/portfolio_xray_layer_spec.md` maps Block 2.1–2.7 to
`XRAY_SECTION_KEYS`, `build_portfolio_xray_v2`, upstream inputs, tests, and Phase 12 follow-ups;
indexed in `SPEC.md`, `docs/specs/README.md`, and diagnostics spec header; methodology map G11
closed. Session 07 can start with allocation concentration (`RM-947`).

Session 07 outcome: `RM-947` Done — `asset_allocation` exposes `weight_concentration` item (top-1/top-3
sums, HHI on positive capital weights, `basis=capital_weights`, no look-through); legacy summary
mirrors fields; text/HTML tables prefer concentration KPI block; methodology map G6/N6 closed; spec
§2.1 updated; test `test_portfolio_xray_weight_concentration_in_asset_allocation`. Session 08 can
start with `volatility_spike` methodology (`RM-948`).

Session 08 outcome: `RM-948` Done — **Option B (factor-only)** for `volatility_spike`: spec §2.7
documents `beta_vix` + historical `es_95` channels and deferred Option A; runtime adds
`WEAKNESS_FACTOR_ONLY_RISKS`, `scenario_coverage.evidence_mode` / `scenario_mapping`, and
`WEAKNESS_FACTOR_SHORTS["volatility_spike"]=("vix",)`; methodology map G8/N7 closed; test
`test_volatility_spike_weakness_factor_only_methodology`. Session 09 can start with golden contract
tests (`RM-949`).

Session 09 outcome: `RM-949` Done — committed golden fixture
`tests/fixtures/portfolio_xray_golden_v2.json`, builder inputs in
`tests/portfolio_xray_golden_inputs.py`, and schema drift tests in
`tests/test_portfolio_xray_contract.py` (top-level/section contract, post-audit surface fingerprint,
live-vs-golden equality); [TESTING.md](../../TESTING.md) wave bundle updated. Session 10 can start
with baseline snapshot audit (`RM-950`).

Session 10 outcome: `RM-950` Done — baseline snapshot audit
`docs/audits/2026-05-20_portfolio_xray_baseline_snapshot.md` (artifact checklist, golden contract
reference, compare template); governance pytest bundle **40 passed** and `verify_docs` OK; Phase 12
closed in ROADMAP; exec-plan register marks this roadmap **Completed** (Sessions 00–10).

## Context and Orientation

Portfolio X-Ray in portfolio-first operation is centered on `portfolio_xray.json` under
`{output_dir_final}/analysis_subject/` after `run_report.py --materialize-analysis-subject`.

Key files:

- `src/portfolio_xray.py`: seven-section builder, thresholds, formatters.
- `src/snapshot.py`: writes `portfolio_xray.json` and embeds X-Ray in reports.
- `docs/specs/portfolio_xray_diagnostics_spec.md`: section contracts (skeleton, deepening in progress).
- `docs/audits/2026-05-20_portfolio_xray_methodology_map.md`: methodology map (this wave baseline).

Completed prerequisite waves (do not redo):

- [Portfolio X-Ray Diagnostics Deepening Plan](2026-05-19_portfolio_xray_diagnostics_deepening_plan.md)
- [Stress Lab Post-Audit Roadmap](2026-05-20_stress_lab_post_audit_roadmap.md)

## Plan of Work

Work proceeds one session per chat, in strict order Sessions 00–10.

### Session 00 — Project memory (completed)

Goal: persist audit and active ExecPlan so the next chat can resume from repo files only.

Tasks: methodology map audit; this ExecPlan; register updates; ROADMAP Phase 12.

### Session 01 — Documentation sync (`RM-940`, `RM-941`)

Goal: registers reflect runtime after deepening wave.

Tasks: close stale KNOWN_ISSUES (RC, Kalman); mark `RM-932` Done; CHANGELOG; TESTING X-Ray bundle stub.

### Session 02 — Threshold registry (`RM-942`)

Goal: spec-owned `XRAY_THRESHOLDS`; validation tests; no silent threshold drift.

### Session 03 — Section provenance (`RM-943`)

Goal: frequency/window/n_obs/benchmark on sections 2.2, 2.3, 2.6, 2.7.

### Session 04 — Factor inference panel (`RM-944`)

Goal: surface `factor_regression_5y/10y` inference read-only in X-Ray.

### Session 05 — Multi-window + TTR (`RM-945`)

Goal: 3Y/5Y/10Y metrics panel; expose TTR in risk diagnostics.

### Session 06 — Layer spec (`RM-946`)

Goal: create `portfolio_xray_layer_spec.md` under docs/specs (mirror Stress Lab layer spec pattern).

### Session 07 — Concentration (`RM-947`)

Goal: HHI, top-N sums in asset allocation (spec decision first).

### Session 08 — Vol spike (`RM-948`)

Goal: spec decision Option A (new scenario) vs Option B (factor-only); implement chosen path.

### Session 09 — Contract tests (`RM-949`)

Goal: fixture JSON + schema tests; document pytest bundle in TESTING.md.

### Session 10 — Baseline and closure

Goal: baseline snapshot audit doc; close ExecPlan; Phase 12 Done in ROADMAP.

## Concrete Steps

For each session, use this kickoff:

    Continue docs/exec_plans/2026-05-20_portfolio_xray_post_audit_roadmap.md.
    Work on Session NN only.
    Read AGENTS.md, WORKFLOW.md, PLANS.md,
    docs/specs/portfolio_xray_diagnostics_spec.md,
    docs/audits/2026-05-20_portfolio_xray_methodology_map.md,
    and docs/audits/2026-05-19_portfolio_xray_layer_audit.md.
    Run git status --short before edits and do not revert unrelated dirty files.

Verification commands (Session 09+):

    python scripts/verify_docs.py
    python -m pytest tests/test_portfolio_xray.py tests/test_portfolio_xray_threshold_registry.py tests/test_portfolio_xray_contract.py -q
    python tests/portfolio_xray_golden_inputs.py

## Validation and Acceptance

Wave-level acceptance:

- Thresholds documented in spec and validated by tests (Session 02).
- Sections disclose provenance metadata where applicable (Session 03).
- Factor inference visible when stress_report provides it (Session 04).
- Multi-window metrics and TTR exposed when snapshots exist (Session 05).
- Layer spec navigates 2.1–2.7 without chat history (Session 06).
- Contract tests prevent schema drift (Session 09).
- Baseline snapshot documents artifact checklist (Session 10).

Session 00 acceptance:

- `docs/audits/2026-05-20_portfolio_xray_methodology_map.md` exists.
- This ExecPlan registered Active in `docs/exec_plans/README.md`.
- Phase 12 rows in `docs/ROADMAP.md`.
- `python scripts/verify_docs.py` passes.

## Idempotence and Recovery

Safe to resume in any future chat. Update `Progress` at end of each session. Do not change
`XRAY_THRESHOLDS` values in Session 02 without explicit spec decision — document first.

## Artifacts and Notes

Primary generated artifacts to track from Session 10:

- `Main portfolio/analysis_subject/portfolio_xray.json`
- `Main portfolio/analysis_subject/snapshot_{3y,5y,10y}.json`
- `Main portfolio/analysis_subject/stress_report.json`
- `Main portfolio/analysis_subject/results_csv/rc_vol_10y.csv`

Baseline checkpoint (Session 10): portfolio X-Ray baseline snapshot audit document under docs/audits/.

## Interfaces and Dependencies

- Runtime: `src/portfolio_xray.py`, `src/snapshot.py`, `run_report.py`.
- Specs: `portfolio_xray_diagnostics_spec.md`, `metrics_specification.md`, `stress_testing_spec.md`,
  `factor_diagnostics_spec.md`.
- Governance: `OUTPUTS.md`, `TESTING.md`, `KNOWN_ISSUES.md`, `docs/ROADMAP.md`.

Revision note, 2026-05-20: Created post-audit Block 2 governance ExecPlan and completed Session 00
(methodology map, registers, ROADMAP Phase 12).

Revision note, 2026-05-20: Completed Session 01 documentation sync (`RM-941`): registers aligned with
deepening-wave runtime; TESTING.md X-Ray bundle stub added for Sessions 02–08.

Revision note, 2026-05-20: Completed Session 02 threshold registry (`RM-942`): spec §8, drift tests,
ROADMAP/CHANGELOG/methodology map updates; runtime values unchanged.

Revision note, 2026-05-20: Completed Session 03 section provenance (`RM-943`): `_section` provenance
fields; builders for 2.2/2.3/2.6/2.7; RC CSV source filename fix; `test_portfolio_xray_section_provenance_metadata`.

Revision note, 2026-05-20: Completed Session 04 factor inference panel (`RM-944`):
`factor_regression_inference` items in `factor_exposure`; HAC-first read-only pass-through from
stress_report; `test_portfolio_xray_factor_regression_inference_panel`.

Revision note, 2026-05-20: Completed Session 05 multi-window metrics + TTR (`RM-945`):
`multi_window_metrics` panel and TTR on primary metrics; `load_portfolio_windows_from_dir`;
snapshot/commentary wiring; multi-window and TTR X-Ray tests.

Revision note, 2026-05-20: Completed Session 06 layer spec (`RM-946`): added
`portfolio_xray_layer_spec.md`; register and methodology map updates; no runtime threshold or code
changes.

Revision note, 2026-05-20: Completed Session 07 allocation concentration (`RM-947`):
`weight_concentration` item in `asset_allocation`; `_weight_concentration_item` aligned with
candidate comparison; `test_portfolio_xray_weight_concentration_in_asset_allocation`.

Revision note, 2026-05-20: Completed Session 08 volatility_spike methodology (`RM-948`): Option B
factor-only contract in spec and `portfolio_xray.py`; `test_volatility_spike_weakness_factor_only_methodology`.

Revision note, 2026-05-20: Completed Session 09 golden contract tests (`RM-949`):
`tests/fixtures/portfolio_xray_golden_v2.json`, `tests/test_portfolio_xray_contract.py`,
`tests/portfolio_xray_golden_inputs.py`; TESTING.md wave bundle updated.

Revision note, 2026-05-20: Completed Session 10 baseline and wave closure (`RM-950`):
`docs/audits/2026-05-20_portfolio_xray_baseline_snapshot.md`; Phase 12 Done; plan Completed.
