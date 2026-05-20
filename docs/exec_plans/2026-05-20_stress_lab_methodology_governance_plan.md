# Stress Lab Methodology Governance Plan (Block 3 Phase 13)

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan must be maintained in accordance with [PLANS.md](../../PLANS.md).

## Purpose / Big Picture

After the Stress Lab Post-Audit wave (Sessions 00–10) and the 2026-05-20 methodology audit, Block 3
is technically present but not fully **audit-grade** for handoff. This plan closes trust gaps and
extends decision-useful diagnostics without UI, new mandate gates, or silent scenario additions.

After Session 00, a new agent should resume from:

- [Stress Lab Methodology Map](../audits/2026-05-20_stress_lab_methodology_map.md)
- this ExecPlan
- [stress_testing_spec.md](../specs/stress_testing_spec.md)
- [stress_lab_layer_spec.md](../specs/stress_lab_layer_spec.md)

without chat history.

**Non-goals:** UI, optimizer changes, mandate gate changes, silent new scenarios/thresholds.

## Progress

- [x] (2026-05-20) Session 00: Methodology map persisted, this ExecPlan created, audit/plan registers updated, ROADMAP Phase 13 (`RM-951`–`RM-961`), TESTING governance bundle stub.
- [x] (2026-05-20) Session 01 (`RM-952`): Worst historical episode selection integrity (max_dd).
- [x] (2026-05-20) Session 02 (`RM-953`): Historical realized-vs-proxy boundary + disclosure fields.
- [x] (2026-05-20) Session 03 (`RM-954`): Hedge analysis N/A transparency.
- [x] (2026-05-20) Session 04 (`RM-955`): Factor drivers in stress_conclusions.
- [x] (2026-05-20) Session 05 (`RM-956`): Hedge gap v2 by risk type.
- [x] (2026-05-20) Session 06 (`RM-957`): Crisis replay v2 (recovery + asset contrib).
- [x] (2026-05-20) Session 07 (`RM-958`): stress_lab_layer_spec deepening.
- [x] (2026-05-20) Session 08 (`RM-959`): crypto/vol scenarios spec-only package.
- [x] (2026-05-20) Session 09 (`RM-960`): Custom shock optional artifact.
- [x] (2026-05-20) Session 10 (`RM-961` integration): Downstream integration (snapshot, comparison, commentary).
- [x] (2026-05-20) Session 11 (`RM-961` closure): Verification bundle + baseline snapshot update + wave closure.

## Surprises & Discoveries

- Observation: Methodology audit existed only in chat until Session 00; no
  `2026-05-20_stress_lab_methodology_map.md` in repo (unlike Block 2 X-Ray map).
  Evidence: glob search before Session 00.

- Observation: Representative `analysis_subject` run has hedge gap `insufficient_data` because no
  holdings carry hedge `risk_role` labels — easy to misread as "no gap detected."
  Evidence: `stress_report.json` hedge_gap_analysis block during audit.

- Observation: `stress_conclusions.worst_historical_episode` ranks by `pnl_real_episode` while
  historical pass/fail uses episode `max_dd`.
  Evidence: `_build_stress_conclusions` in `src/stress.py`.

## Decision Log

- Decision: One chat = one session; start a new chat after each session unless the user explicitly
  requests a tiny follow-up in the same thread.
  Rationale: Block 3 governance spans spec, code, tests, and docs; separate sessions reduce context loss.
  Date/Author: 2026-05-20 / Agent.

- Decision: Session 00 is documentation and project memory only — no code changes.
  Rationale: Governance wave must record methodology before altering rules.
  Date/Author: 2026-05-20 / Agent.

- Decision: Session 02 default — keep `run_stress` historical path **realized-only**; proxies remain in
  scenario_library_normalized only unless the user explicitly approves primary-proxy in that session.
  Date/Author: 2026-05-20 / Agent.

- Decision: Session 08 default — crypto/vol synthetic scenarios are **spec-only**; no `SCENARIOS`
  code changes unless the user explicitly approves implementation in that chat.
  Date/Author: 2026-05-20 / Agent.

- Decision: `stress_conclusions.worst_historical_episode` selects the episode with **minimum**
  `max_dd` among rows with computed drawdown, not minimum `pnl_real_episode`.
  Rationale: Historical suite pass/fail uses `max_dd >= -max_dd_limit`; conclusions must match.
  Date/Author: 2026-05-20 / Agent (Session 01).

## Outcomes & Retrospective

Session 00 outcome: methodology map persisted in
`docs/audits/2026-05-20_stress_lab_methodology_map.md`; this ExecPlan registered **Active** in
`docs/exec_plans/README.md`; Phase 13 rows `RM-951`–`RM-961` added to `docs/ROADMAP.md`; TESTING.md
governance bundle stub added.

Session 01 outcome: `_select_worst_historical_row` in `src/stress.py` ranks by minimum `max_dd`
(aligned with historical pass/fail); `stress_testing_spec.md` §12.1 updated;
`test_worst_historical_episode_by_max_dd_not_pnl` added. Resume Session 02 (`RM-953`) in a new chat.

Session 02 outcome: `return_method` / `proxy_used` on all `historical_results` rows;
`historical_methodology` report block; enhanced `data_quality_warnings`; DEC-2026-05-20-001;
stress spec §9 boundary + §9.3; tests extended. Resume Session 03 (`RM-954`) in a new chat.

Session 03 outcome: `hedge_gap_analysis` adds `not_applicable` + `status_reason` /
`status_reason_en` + `hedge_label_risk_roles`; no hedge labels no longer reported as
`insufficient_data`; commentary and hedge_gap_analysis_spec updated; G3 closed. Resume Session 04
(`RM-955`) in a new chat.

Session 04 outcome: `stress_conclusions` adds `top_factor_drivers_worst_scenario` and
`helped_factors_worst_scenario` from worst synthetic `pnl_by_factor_pct`; stress spec §12.1;
stress commentary factor driver lines; G4 closed. Resume Session 05 (`RM-956`) in a new chat.

Session 05 outcome: `hedge_gap_analysis` method `stress_scenario_hedge_evidence_v2` with `by_risk_type[]`
per weakness bucket (`HEDGE_GAP_SCENARIO_BY_RISK` aligned with `WEAKNESS_SCENARIO_MAP`); aggregate
v1 fields retained; `any_risk_type_gap_detected`; hedge_gap_analysis_spec v2; contract tests extended;
G5 closed. Resume Session 06 (`RM-957`) in a new chat.

Session 06 outcome: `historical_episode_paths` v2 (`crisis_replay_v2`) adds `time_to_recovery_months`,
`recovered`, `asset_pnl_contrib_episode`, `top_loss_assets_episode`; `run_report.py` exports
`crisis_replay_{episode}_asset_contrib.csv`; crisis_replay_spec v2 + stress spec §9.1; tests extended;
G6 closed. Resume Session 07 (`RM-958`) in a new chat.

Session 07 outcome: handoff-grade [stress_lab_layer_spec.md](../specs/stress_lab_layer_spec.md) —
provenance legend, workflow, JSON contract tables, sub-blocks 3.1–3.6 (incl. 3.1.1/3.1.2), report
surfaces, open gaps, Phase 13 session table; indexed in [SPEC.md](../../SPEC.md) and
[docs/specs/README.md](../specs/README.md); methodology map G7 closed. Resume Session 08 (`RM-959`)
in a new chat.

Session 08 outcome: reviewable
[docs/proposals/2026-05-20_crypto_vol_stress_scenarios_proposal.md](../proposals/2026-05-20_crypto_vol_stress_scenarios_proposal.md)
and [docs/proposals/README.md](../proposals/README.md); **DEC-2026-05-20-002** defers `crypto_shock`
and `volatility_shock` in `run_stress` (no `SCENARIOS` changes); `stress_testing_spec.md` §2.3;
methodology map G8 closed; P4 deferred. Resume Session 09 (`RM-960`) in a new chat.

Session 09 outcome: optional versioned `custom_shock_runs.json` (`custom_shock_runs_v1`) via
`record_custom_shock_run`, `append_custom_shock_run`, `write_custom_shock_runs`, `load_custom_shock_runs`
in `src/stress.py`; not written by `run_stress`; stress spec §12.3 persistence subsection;
OUTPUTS.md; contract tests in `tests/test_stress_simulator_contract.py`; G9/P6 closed. Resume
Session 10 (`RM-961`) in a new chat.

Session 10 outcome: `crisis_replay_summary_from_paths` in `src/stress.py`; `snapshot_10y.stress_suite_results`
mirrors `historical_methodology`, `crisis_replay_summary`, `failed_scenario`, conclusions, hedge gap v2;
`candidate_comparison` `stress` blocks merge snapshot + `stress_report.json`; `stress_commentary.txt`
adds methodology, crisis replay v2, hedge-by-risk-type, and `return_method` on historical rows; G10 closed;
`tests/test_stress_downstream_integration.py`; specs and TESTING bundle updated. Resume Session 11
(`RM-961` closure) in a new chat.

Session 11 outcome: Phase 13 governance wave **closed**. Stress Lab governance pytest bundle **90 passed**
(`--basetemp=tmp/pytest_gov_s11`); `python scripts/verify_docs.py` **OK**. Baseline snapshot checklist
extended (items 14–17) and Session 11 closure documented; Session 00 artifact fingerprints unchanged
(no `Main portfolio/analysis_subject/` on disk — refresh hashes after next
`run_report.py --materialize-analysis-subject`). ExecPlan marked **Completed**; ROADMAP Phase 13 Done;
registers and methodology map updated for handoff without chat history.

## Context and Orientation

Stress Lab in portfolio-first operation is centered on `stress_report.json` under
`Main portfolio/analysis_subject/` after `run_report.py --materialize-analysis-subject`.

Key files:

- `src/stress.py`: scenario execution, historical episodes, scorecard/conclusions, hedge-gap, simulator API.
- `run_report.py`: materialization, crisis replay CSV export, scenario library build.
- `src/portfolio_commentary.py`: stress narrative from structured fields.
- `src/snapshot.py`: `stress_suite_results` mirror.
- `docs/specs/stress_testing_spec.md`: canonical stress methodology.
- `docs/audits/2026-05-20_stress_lab_methodology_map.md`: methodology map (this wave baseline).

Completed prerequisite wave (do not redo):

- [Stress Lab Post-Audit Roadmap](2026-05-20_stress_lab_post_audit_roadmap.md) (Sessions 00–10)

## Plan of Work

Work proceeds one session per chat, in strict order Sessions 00–11.

### Session 00 — Project memory (completed)

Goal: persist audit and active ExecPlan so the next chat can resume from repo files only.

Tasks: methodology map; this ExecPlan; register updates; ROADMAP Phase 13; TESTING stub.

### Session 01 — Worst historical selection (`RM-952`)

Goal: `stress_conclusions.worst_historical_episode` uses worst **max_dd**, consistent with pass/fail.

Tasks: spec §12.1 update; fix `_build_stress_conclusions`; contract test with disagreeing pnl/max_dd.

Files: `src/stress.py`, `docs/specs/stress_testing_spec.md`, `tests/test_stress_scorecard_contract.py`.

Done when: new test passes; representative stress_report shows consistent worst historical.

### Session 02 — Historical methodology boundary (`RM-953`)

Goal: explicit realized-only primary stress vs proxy-in-library; disclosure on historical rows.

Tasks: DECISIONS.md entry; add `return_method` (or equivalent) to historical_results; enhance
data_quality_warnings; spec §9 cross-reference.

Default: no proxy in `run_stress`.

Files: `src/stress.py`, specs, `DECISIONS.md`, `tests/test_stress_historical_fields.py`.

### Session 03 — Hedge N/A transparency (`RM-954`)

Goal: when no hedge labels, user sees explicit N/A reason, not ambiguous insufficient_data.

Tasks: `status_reason` / taxonomy coverage on hedge_gap_analysis; commentary + spec update.

Files: `src/stress.py`, `hedge_gap_analysis_spec.md`, `portfolio_commentary.py`, tests.

### Session 04 — Factor drivers in conclusions (`RM-955`)

Goal: factor-level "why" in `stress_conclusions` without opening scenario_results.

Tasks: `top_factor_drivers_worst_scenario`, `helped_factors_worst_scenario`; spec §12.1; commentary.

Files: `src/stress.py`, `stress_testing_spec.md`, `portfolio_commentary.py`, tests.

### Session 05 — Hedge gap v2 by risk type (`RM-956`)

Goal: hedge effectiveness evaluated against mapped scenarios, not only worst synthetic.

Tasks: spec v2 `by_risk_type[]`; extend `_build_hedge_gap_analysis`; reuse WEAKNESS_SCENARIO_MAP pattern.

Files: `src/stress.py`, `hedge_gap_analysis_spec.md`, tests.

### Session 06 — Crisis replay v2 (`RM-957`)

Goal: recovery timing and static asset contribution summary on episode blocks.

Tasks: crisis_replay_spec v2; implement recovery fields; extend CSV export in run_report.py.

Files: `src/stress.py`, `run_report.py`, `crisis_replay_spec.md`, tests.

### Session 07 — Layer spec deepening (`RM-958`)

Goal: handoff-grade `stress_lab_layer_spec.md` with provenance per sub-block 3.1–3.6.

Tasks: expand layer spec; index in SPEC.md and docs/specs/README.md; doc-only unless drift fix.

### Session 08 — New scenarios spec-only (`RM-959`) — completed 2026-05-20

Goal: reviewable proposal for crypto/vol synthetic scenarios; DECISIONS defer/accept — no code by default.

Delivered: [docs/proposals/2026-05-20_crypto_vol_stress_scenarios_proposal.md](../proposals/2026-05-20_crypto_vol_stress_scenarios_proposal.md);
[DEC-2026-05-20-002](../../DECISIONS.md) (defer both in `run_stress`; X-Ray vol Option B unchanged);
[stress_testing_spec.md](../specs/stress_testing_spec.md) §2.3; G8 closed in methodology map and layer spec.
No `src/stress.py` changes.

### Session 09 — Custom shock artifact (`RM-960`) — completed 2026-05-20

Goal: optional versioned persistence for simulate_custom_shock runs.

Delivered: `CUSTOM_SHOCK_RUNS_VERSION` / `custom_shock_runs.json` helpers in `src/stress.py`;
stress spec §12.3 persistence contract; OUTPUTS.md; methodology map G9 + proposal P6 closed;
`tests/test_stress_simulator_contract.py` persistence tests. `run_stress` unchanged (opt-in only).

### Session 10 — Downstream integration (`RM-961` part 1)

Goal: snapshot, comparison, health/robustness, commentary consume new fields.

Files: `snapshot.py`, `candidate_comparison.py`, `portfolio_commentary.py`, related tests.

### Session 11 — Verification and closure (`RM-961` part 2)

Goal: regression bundle green; baseline snapshot updated; plan Completed.

Commands: see Concrete Steps below.

## Concrete Steps

Session kickoff (Sessions 01+):

    Continue docs/exec_plans/2026-05-20_stress_lab_methodology_governance_plan.md.
    Work on Session NN only.
    Read AGENTS.md, PLANS.md,
    docs/audits/2026-05-20_stress_lab_methodology_map.md,
    docs/specs/stress_testing_spec.md,
    docs/specs/stress_lab_layer_spec.md.
    Run git status --short before edits and do not revert unrelated dirty files.

Stress Lab wave bundle (Sessions 01–10 incremental; full run Session 11):

    python run_report.py --materialize-analysis-subject
    python -m pytest tests/test_stress_scorecard_contract.py tests/test_stress_hedge_gap_contract.py tests/test_stress_scenario_coverage_contract.py tests/test_stress_synthetic_assumptions_contract.py tests/test_stress_simulator_contract.py tests/test_stress_mandate_pass.py tests/test_stress_scenario_analytics.py tests/test_stress_historical_fields.py tests/test_stress_covariance_taxonomy.py tests/test_stress_artifacts_priority.py tests/test_stress_downstream_integration.py tests/test_portfolio_commentary.py tests/test_io_export_ips_summary.py -q
    python scripts/verify_docs.py

## Validation and Acceptance

Session 00 acceptance:

- `docs/audits/2026-05-20_stress_lab_methodology_map.md` exists.
- This ExecPlan registered Active in `docs/exec_plans/README.md`.
- Phase 13 rows in `docs/ROADMAP.md`.
- `python scripts/verify_docs.py` passes.

Wave-level acceptance (Session 11):

- G1–G3 closed; G4–G7 implemented per sessions; G8–G9 spec/deferred or shipped per decision.
- Baseline snapshot checklist updated for new fields.
- ExecPlan marked Completed; ROADMAP Phase 13 Done.

## Idempotence and Recovery

Safe to resume in any future chat. Update `Progress` at end of each session. Do not add scenarios or
change shock vectors without spec decision and DECISIONS.md entry.

## Artifacts and Notes

Primary generated artifacts to track across sessions:

- `Main portfolio/analysis_subject/stress_report.json`
- `Main portfolio/analysis_subject/stress_commentary.txt`
- `Main portfolio/analysis_subject/scenario_library.json`
- `Main portfolio/analysis_subject/results_csv/crisis_replay_*.csv`
- `Main portfolio/analysis_subject/snapshot_10y.json`

Baseline checkpoint: [2026-05-20_stress_lab_baseline_snapshot.md](../audits/2026-05-20_stress_lab_baseline_snapshot.md)

## Interfaces and Dependencies

- Runtime: `src/stress.py`, `run_report.py`, `src/stress_scenario_analytics.py`, `src/portfolio_commentary.py`, `src/snapshot.py`.
- Specs: `stress_testing_spec.md`, `stress_lab_layer_spec.md`, `scenario_library_spec.md`, `hedge_gap_analysis_spec.md`, `crisis_replay_spec.md`.
- Governance: `OUTPUTS.md`, `TESTING.md`, `docs/ROADMAP.md`, `DECISIONS.md`.

Revision note, 2026-05-20: Created Phase 13 Block 3 governance ExecPlan; completed Session 00
(methodology map, registers, ROADMAP Phase 13, TESTING stub).

Revision note, 2026-05-20: Completed Session 01 (`RM-952`) — worst historical by `max_dd`; spec §12.1;
contract test `test_worst_historical_episode_by_max_dd_not_pnl`.

Revision note, 2026-05-20: Completed Session 02 (`RM-953`) — `historical_methodology`, row
`return_method`/`proxy_used`, conclusions warnings; DEC-2026-05-20-001; spec §9.3.

Revision note, 2026-05-20: Completed Session 03 (`RM-954`) — hedge gap `not_applicable`,
`status_reason` taxonomy, commentary N/A line; G3 closed.

Revision note, 2026-05-20: Completed Session 04 (`RM-955`) — `top_factor_drivers_worst_scenario`
and `helped_factors_worst_scenario` on `stress_conclusions`; spec §12.1; commentary factor lines;
G4 closed.

Revision note, 2026-05-20: Completed Session 05 (`RM-956`) — hedge gap v2 `by_risk_type[]`,
`HEDGE_GAP_SCENARIO_BY_RISK`, method `stress_scenario_hedge_evidence_v2`; G5 closed.

Revision note, 2026-05-20: Completed Session 06 (`RM-957`) — crisis replay v2 recovery + asset
contrib on `historical_episode_paths`, asset contrib CSV export; G6 closed.

Revision note, 2026-05-20: Completed Session 07 (`RM-958`) — handoff-grade stress_lab_layer_spec
(3.1–3.6 provenance, JSON index, governance table); SPEC.md + specs README index; G7 closed.

Revision note, 2026-05-20: Completed Session 08 (`RM-959`) — crypto/vol stress scenario proposal;
DEC-2026-05-20-002 defer; stress spec §2.3; G8 closed; no SCENARIOS code changes.

Revision note, 2026-05-20: Completed Session 09 (`RM-960`) — optional `custom_shock_runs.json`
persistence (`custom_shock_runs_v1`); G9 closed; opt-in `record_custom_shock_run` API.

Revision note, 2026-05-20: Completed Session 10 (`RM-961` part 1) — snapshot/comparison/commentary
downstream integration; `crisis_replay_summary`; G10 closed; `test_stress_downstream_integration.py`.

Revision note, 2026-05-20: Completed Session 11 (`RM-961` closure) — governance bundle 90 passed;
verify_docs OK; baseline snapshot Session 11 closure; Phase 13 (`RM-951`–`RM-961`) marked Done; plan
Completed.
