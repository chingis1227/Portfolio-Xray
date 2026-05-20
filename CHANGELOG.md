# CHANGELOG.md

This file is the concise living history of meaningful project changes.

It records what was added, changed, removed, fixed, or deprecated at a project level. It is not a full git log, not a roadmap, and not a replacement for specs, tests, or ExecPlans.

## How To Use

- Add entries only for meaningful project changes: behavior, formulas, data flow, configs, commands, outputs, docs structure, source-of-truth rules, or user-facing workflows.
- Keep each bullet short: one change, one sentence, no implementation essay.
- Do not log every typo, formatting edit, generated-output refresh, or internal refactor with no project-facing effect.
- Link the owning document or module when it helps.
- When an item from [KNOWN_ISSUES.md](KNOWN_ISSUES.md) is fixed, remove it from active issues and add one short `Fixed` entry here if the fix is meaningful.
- For large changes, use this file as the summary and keep detailed rationale in an ExecPlan under `docs/exec_plans/`.

## Entry Format

Use date-based sections unless formal releases are introduced later.

```markdown
Date: YYYY-MM-DD

Category: Added

- Short change summary.

Category: Changed

- Short change summary.

Category: Fixed

- Short change summary.

Category: Removed

- Short change summary.
```

Omit empty categories.

## 2026-05-20

### Added

- Block 4 governance Session 11 (`RM-981`): **DEC-2026-05-20-003** concept registry boundary;
  [candidate_portfolios_spec.md](docs/specs/candidate_portfolios_spec.md) § Concept candidates not in registry;
  Phase 14 wave closure (baseline snapshot, methodology map verdict, registers); G9 / `KI-2026-05-20-007` closed.

- Block 4 governance Session 10 (`RM-980`): [operational_runbook.md](docs/operational_runbook.md) §8
  (factory exit codes, reason-code table, scenario playbooks); contextual `next_recommended_command` and
  richer `candidate_factory_run.txt` in [candidate_factory.py](src/candidate_factory.py); G4 operator
  playbook documented.

- Block 4 governance Session 09 (`RM-979`): resumable candidate factory — `candidate_factory_manifest.json`,
  `--resume` on `run_candidate_factory.py`, incremental manifest persistence per step, `resumed_from_manifest`
  summary field; closes RM-921 resumable scope and G5; [candidate_factory_spec.md](docs/specs/candidate_factory_spec.md).

- Block 4 governance Session 00 (`RM-970`): [Candidate Factory Methodology Map](docs/audits/2026-05-20_candidate_factory_methodology_map.md),
  [Candidate Factory Baseline Snapshot](docs/audits/2026-05-20_candidate_factory_baseline_snapshot.md), active
  [Candidate Portfolio Factory Post-Audit Roadmap](docs/exec_plans/2026-05-20_candidate_factory_post_audit_roadmap.md),
  ROADMAP Phase 14 (`RM-970`–`RM-981`), TESTING.md governance bundle stub.

- Block 4 governance Session 01 (`RM-971`): documentation sync — G1–G10 gap index and eight active
  `KNOWN_ISSUES` entries mapped to Phase 14 `RM-972`–`RM-981`; [SPEC.md](SPEC.md) and [OUTPUTS.md](OUTPUTS.md)
  link methodology map, layer spec scaffold, and governance ExecPlan; `KI-2026-05-19-005` cross-ref G4/G5.

- Block 4 governance Session 08 (`RM-978`): golden contract tests —
  `tests/fixtures/candidate_factory_run_golden_v1.json`,
  `tests/fixtures/candidate_comparison_golden_v1.json`,
  `tests/candidate_factory_golden_inputs.py`,
  `tests/test_candidate_factory_contract.py`,
  `tests/test_candidate_comparison_contract.py`; Phase 14 governance bundle finalized in [TESTING.md](TESTING.md).

- Block 4 governance Session 07 (`RM-977`): robust paths disclosure — `src/candidate_robust_disclosure.py`,
  factory `robust_paths_disclosure` on robust suite steps, comparison `construction_disclosure.robust_paths`,
  operational runbook robust prerequisites; G8 / G10 and `KI-2026-05-20-005` / `006` closed.

- Block 4 governance Session 06 (`RM-976`): config fingerprint freshness — `candidate_config_fingerprint`
  on window snapshots, factory `config_fingerprint` / `stale_config` gating, comparison
  `stale_config_fingerprint` unavailable reason; G2 / `KI-2026-05-20-002` closed.

- Block 4 governance Session 05 (`RM-975`): [candidate_factory_layer_spec.md](docs/specs/candidate_factory_layer_spec.md)
  active handoff for Block 4.1–4.9 (workflow, artifacts, sub-block map, Phase 14 gap table); G7 closed.

- Block 4 governance Session 04 (`RM-974`): `construction_disclosure` on every
  `candidate_comparison.json` row — passthrough from `baseline_weights_metadata.json`, builder
  `summary.json`, policy/subject excerpts, and optional factory step; [candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md) v1.3.

- Block 3 governance Session 11 (`RM-961` closure): Phase 13 wave closed — governance pytest bundle
  **90 passed**, `verify_docs` OK; baseline snapshot Session 11 section and G1–G10 table;
  [Stress Lab Methodology Governance Plan](docs/exec_plans/2026-05-20_stress_lab_methodology_governance_plan.md)
  marked Completed; ROADMAP Phase 13 Done.

- Block 3 governance Session 10 (`RM-961` part 1): downstream integration — `crisis_replay_summary`
  on `snapshot_10y.stress_suite_results` and `candidate_comparison` `stress` blocks;
  `historical_methodology` mirror; commentary lines for methodology, crisis replay v2, hedge
  `by_risk_type`, and per-episode `return_method`; `tests/test_stress_downstream_integration.py`;
  G10 closed.

- Block 3 governance Session 09 (`RM-960`): optional `custom_shock_runs.json` audit trail
  (`custom_shock_runs_v1`) via `record_custom_shock_run` in [src/stress.py](src/stress.py); opt-in
  only (not written by `run_stress`); [stress_testing_spec.md](docs/specs/stress_testing_spec.md) §12.3;
  [OUTPUTS.md](OUTPUTS.md); G9 closed.

- Block 3 governance Session 08 (`RM-959`): crypto/vol synthetic stress **proposal** and
  [docs/proposals/README.md](docs/proposals/README.md); [DEC-2026-05-20-002](DECISIONS.md) defers
  `crypto_shock` / `volatility_shock` in `run_stress` (no `SCENARIOS` changes);
  [stress_testing_spec.md](docs/specs/stress_testing_spec.md) §2.3; methodology map G8 closed.

- Block 3 governance Session 07 (`RM-958`): handoff-grade
  [stress_lab_layer_spec.md](docs/specs/stress_lab_layer_spec.md) — provenance per sub-block 3.1–3.6,
  JSON contract index, Phase 13 session table; indexed in [SPEC.md](SPEC.md) and
  [docs/specs/README.md](docs/specs/README.md); methodology map G7 closed.

- Block 3 governance Session 06 (`RM-957`): crisis replay v2 — `time_to_recovery_months`,
  `recovered`, `asset_pnl_contrib_episode`, `top_loss_assets_episode` on `historical_episode_paths`;
  `crisis_replay_{episode}_asset_contrib.csv` export; [crisis_replay_spec.md](docs/specs/crisis_replay_spec.md);
  G6 closed.

- Block 3 governance Session 05 (`RM-956`): hedge gap v2 — `by_risk_type[]` per weakness bucket
  via `HEDGE_GAP_SCENARIO_BY_RISK` (aligned with X-Ray `WEAKNESS_SCENARIO_MAP`); method
  `stress_scenario_hedge_evidence_v2`; [hedge_gap_analysis_spec.md](docs/specs/hedge_gap_analysis_spec.md);
  extended `tests/test_stress_hedge_gap_contract.py`; G5 closed.

- Block 3 governance Session 04 (`RM-955`): factor drivers in `stress_conclusions` —
  `top_factor_drivers_worst_scenario` and `helped_factors_worst_scenario` from worst synthetic
  `pnl_by_factor_pct`; [stress_testing_spec.md](docs/specs/stress_testing_spec.md) §12.1;
  stress commentary factor driver lines; G4 closed.

- Block 3 governance Session 03 (`RM-954`): hedge gap N/A transparency —
  `not_applicable` + `status_reason` / `status_reason_en` on `hedge_gap_analysis` when no hedge
  `risk_role` labels; [hedge_gap_analysis_spec.md](docs/specs/hedge_gap_analysis_spec.md) taxonomy;
  stress commentary plain-English N/A line; G3 closed.

- Block 3 governance Session 02 (`RM-953`): primary historical stress disclosure —
  `historical_methodology` on `stress_report.json`, `return_method` / `proxy_used` on
  `historical_results`, enhanced `stress_conclusions.data_quality_warnings`; DEC-2026-05-20-001;
  [stress_testing_spec.md](docs/specs/stress_testing_spec.md) §9.3.

- Block 2 post-audit Session 10 (`RM-950`): [Portfolio X-Ray Baseline Snapshot](docs/audits/2026-05-20_portfolio_xray_baseline_snapshot.md)
  — artifact checklist, golden contract reference, compare template; Phase 12 (`RM-940`–`RM-950`) closed;
  post-audit ExecPlan marked Completed.

- Block 2 post-audit Session 09 (`RM-949`): golden `portfolio_xray.json` contract tests —
  `tests/fixtures/portfolio_xray_golden_v2.json`, `tests/test_portfolio_xray_contract.py`,
  `tests/portfolio_xray_golden_inputs.py`; Portfolio X-Ray wave bundle in [TESTING.md](TESTING.md).

- Block 2 post-audit Session 08 (`RM-948`): `volatility_spike` weakness row documented and implemented
  as **factor-only (Option B)** — `beta_vix` + historical `es_95`; `scenario_coverage.evidence_mode`
  and `WEAKNESS_FACTOR_ONLY_RISKS`; test `test_volatility_spike_weakness_factor_only_methodology`.

- Block 2 post-audit Session 07 (`RM-947`): Portfolio X-Ray `weight_concentration` item in
  `asset_allocation` (top-1/top-3 capital weight sums, HHI on positive weights, no look-through);
  legacy summary mirrors fields; test `test_portfolio_xray_weight_concentration_in_asset_allocation`.

- Block 2 post-audit Session 06 (`RM-946`): [portfolio_xray_layer_spec.md](docs/specs/portfolio_xray_layer_spec.md)
  — Block 2.1–2.7 layer map (code, upstream inputs, tests, Phase 12 follow-ups); indexed in
  [SPEC.md](SPEC.md) and [docs/specs/README.md](docs/specs/README.md).

- Block 2 post-audit Session 05 (`RM-945`): Portfolio X-Ray `multi_window_metrics` panel (3Y/5Y/10Y
  from snapshot metrics) and `ttr_months`/`recovered` on primary `portfolio_metrics`; loader
  `load_portfolio_windows_from_dir`; tests `test_portfolio_xray_multi_window_metrics_panel`,
  `test_portfolio_xray_ttr_in_primary_risk_metrics`, `test_load_portfolio_windows_from_dir`.

- Block 2 post-audit Session 04 (`RM-944`): Portfolio X-Ray `factor_regression_inference` items in
  `factor_exposure` (read-only HAC inference, multicollinearity, and residual diagnostics from
  `stress_report.factor_regression_5y/10y`); tests
  `test_portfolio_xray_factor_regression_inference_panel`.

- Block 2 post-audit Session 03 (`RM-943`): section-level provenance on Portfolio X-Ray sections
  `risk_diagnostics`, `factor_exposure`, `risk_budget_view`, and `weakness_map` (`method`,
  `frequency`, `window`, `n_obs`, `benchmark`); RC CSV loader returns the file actually used;
  test `test_portfolio_xray_section_provenance_metadata`.

- Block 2 post-audit Session 02 (`RM-942`): canonical `XRAY_THRESHOLDS` registry in
  [portfolio_xray_diagnostics_spec.md](docs/specs/portfolio_xray_diagnostics_spec.md) §8 and drift
  tests in [tests/test_portfolio_xray_threshold_registry.py](tests/test_portfolio_xray_threshold_registry.py).

- Block 2 post-audit governance Session 00: [Portfolio X-Ray Methodology Map](docs/audits/2026-05-20_portfolio_xray_methodology_map.md),
  active ExecPlan [2026-05-20_portfolio_xray_post_audit_roadmap.md](docs/exec_plans/2026-05-20_portfolio_xray_post_audit_roadmap.md),
  and ROADMAP Phase 12 (`RM-940`–`RM-950`) for audit-grade X-Ray transparency.

- Stress Lab Sessions 01-10 (post-audit wave): hardened `stress_scorecard_v1` / `stress_conclusions`,
  `historical_episode_paths` crisis replay CSVs, `hedge_gap_analysis`, expanded synthetic scenario
  coverage (`usd_shock`, `commodity_shock`, `banking_2023`), `synthetic_assumptions` transparency,
  portfolio-first stress resolution via `src/stress_artifacts.py`, plain-English stress narrative in
  commentary/IPS, and custom-shock simulator API (`simulate_custom_shock`); contract tests and specs
  (`stress_lab_layer_spec`, `hedge_gap_analysis_spec`, `crisis_replay_spec`); Session 10 closed the
  wave with documented regression bundle in [TESTING.md](TESTING.md).

- X-Ray Session 09 / RM-939: portfolio-first **core** vs **full** review modes on
  `run_portfolio_review.py` (`--mode core|full`, factory profiles `core_v1` / `default_v1`);
  `candidate_menu` partial-menu disclosure in `candidate_comparison.json` and decision-package
  summary; operational runbook and spec updates.

- X-Ray Session 08 / RM-938: structured X-Ray report surfaces (`format_portfolio_xray_html`,
  `format_portfolio_xray_text`, `format_portfolio_xray_commentary`) and generated-output QA scans
  for X-Ray wording in `report.txt`, `report.html`, and `commentary.txt`.

- X-Ray Session 07 / RM-937: Portfolio Archetype V2 scorecard with per-archetype
  `positive_evidence` / `negative_evidence`, `archetype_scorecard`, regime
  `conflicting_signals`, and `conflict_summary` (built after weakness map).

### Changed

- Block 4 governance Session 04 (`RM-974`): comparison rows include `construction_disclosure`
  (passthrough `baseline_weights_metadata.json`, builder `summary.json`, policy/subject excerpts,
  optional factory step); closes G6 / `KI-2026-05-20-004`; [candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md) v1.3.

- Block 4 governance Session 03 (`RM-973`): unchecked freshness rebuilds instead of `skipped_existing`;
  comparison warns `candidate_freshness_unchecked_no_review_analysis_end:{candidate_id}` when review
  `analysis_end` unknown; closes G3 / `KI-2026-05-20-003`; factory + comparison specs updated.

- Block 4 governance Session 02 (`RM-972`): factory propagates builder `summary.json` `FAIL_*` into
  `candidate_factory_run.json` `reason_code` (`builder_fail_config`, `builder_infeasible_universe`, …)
  with optional `builder_status` / `builder_reason`; closes G1 / `KI-2026-05-20-001`;
  [candidate_factory_spec.md](docs/specs/candidate_factory_spec.md) reason-code table updated.

- Block 2 post-audit governance Session 01 / `RM-941`: documentation registers aligned with the
  deepening wave — `RM-932` marked Done in ROADMAP Phase 11; resolved RC/Kalman known issues removed
  from active KNOWN_ISSUES; Portfolio X-Ray regression bundle stub added to [TESTING.md](TESTING.md)
  (golden contract tests shipped in post-audit Session 09 / `RM-949`).

- Default `run_portfolio_review.py` factory scope is `core_v1` via `--mode core` (was implicit
  full `default_v1`). Use `--mode full` for the complete optimizer menu.

### Fixed

- Stress Lab Session 10: aligned stale `test_write_portfolio_commentary_creates_file` assertions with
  current `format_portfolio_xray_commentary` headings (`Portfolio X-Ray (diagnostic-only)`).

- X-Ray Session 07 / RM-937: archetype labels no longer hide inflation/rates regime
  tensions (`KI-2026-05-19-010`).

- Mitigated `KI-2026-05-19-005`: core/full review modes and `candidate_menu` disclosure (Session 09).

## 2026-05-19

### Added

- X-Ray Session 06 / RM-936: Weakness Map V2 separates `exposure_present`,
  `adverse_evidence`, `severity`, and `confidence`; adds `scenario_coverage`,
  `top_asset_loss_drivers`, `top_factor_drivers`, per-row `missing_inputs`, and
  conditional `crypto_shock` when crypto taxonomy/weights are present.

- X-Ray Session 05 / RM-935: Hidden Risk Detector V2 emits per-category
  `flagged` / `below_threshold` / `unavailable` assessments (equity beta, duration, credit, liquidity,
  raw/residual PCA, weak hedge, tail risk, stress RC, macro factor dependency, Top1 RC) plus section
  `confidence`, `evidence_count`, and flag counts in `portfolio_xray.json`.

- X-Ray Session 04 / RM-934: portfolio window metrics now include skewness/kurtosis (monthly log
  returns), downside/upside beta, `corr_base`, rolling beta/correlation summaries, and `metric_quality`
  metadata; exposed in snapshots, CSV exports, and X-Ray risk diagnostics.

### Fixed

- X-Ray Session 03 / RM-933: portfolio VaR/ES computed on daily historical returns with
  `analytics.tail_risk` disclosure (method, frequency, window, n_obs); X-Ray and report surfaces
  updated (`KI-2026-05-19-009`).
- X-Ray Session 02 / RM-932: Risk Budget View loads full `rc_vol_*` CSV evidence; factor exposure
  reads Kalman betas from `stress_report.factor_betas_kalman.latest` (`KI-2026-05-19-007`,
  `KI-2026-05-19-008`).
- X-Ray Session 01 / RM-931: report path truncates return panels to `analysis_end`; stress scenario
  analytics and scenario library honor cutoff; `inputs/monthly_returns.csv` is analysis-effective with
  optional `monthly_returns_raw.csv` and `inputs_manifest.json` (`KI-2026-05-19-006`).

### Changed

- Documented deferred operational follow-up after Phase 9: heavy full candidate refresh vs practical
  one-shot runs (`RM-920`–`RM-922`, `KI-2026-05-19-005`; ROADMAP Phase 10, ExecPlan post-closure,
  runbook and factory/review specs).

- Closed RM-911 / Phase 9 post-portfolio-first stabilization: representative review verified subject
  metadata, freshness gating, selection/decision package, regime metrics, monitoring, and PDF outputs;
  removed active issues `KI-2026-05-19-002` and `KI-2026-05-19-004`.

- RM-910: `run_portfolio_review.py` now rebuilds portfolio-first PDFs only by default
  (`rebuild_pdf_reports.py --portfolio-first`: decision package + `analysis_subject` sidecar);
  use `--legacy-full-pdf` for the full EW/RP/policy/baseline variant suite.

### Fixed

- Fixed RM-909: Decision package PDF now uses YAML front matter (`build_decision_package_pdf_md`)
  instead of a long H1 with embedded `analysis_end`, restoring `Main portfolio_decision_package.pdf`
  Pandoc/XeLaTeX builds; closed `KI-2026-05-18-001`.
- Fixed RM-908: `monitoring_diff_v1` with `no_prior_snapshot` no longer emits profile/decision
  deltas or prior snapshot paths; same-`analysis_end` re-runs stay narrative-only with warning
  `prior_same_analysis_end_ignored`.
- Fixed RM-906: Regime portfolio metrics no longer reference undefined `mar_monthly`; daily regime
  Sortino uses aligned daily risk-free by default or a daily-converted configured MAR.
- Fixed RM-905: Portfolio-first comparison now gates root `policy` artifacts as legacy optional
  references, Health Score prioritizes `analysis_subject`, and decision summaries hide the
  current-vs-policy compatibility block for portfolio-first runs.
- Fixed RM-902: Candidate Factory now reuses existing candidate snapshots only when
  `snapshot_10y.json.analysis_end` matches the review date, and Candidate Comparison marks stale
  candidate snapshots unavailable.
- Fixed RM-901: `candidate_comparison.json.analysis_setup_summary` now prefers `analysis_subject/run_metadata.json` over stale root metadata, with regression coverage for `current_portfolio` subjects.

### Added

- Added the [Portfolio X-Ray Layer Audit](docs/audits/2026-05-19_portfolio_xray_layer_audit.md),
  active [Portfolio X-Ray Diagnostics Deepening Plan](docs/exec_plans/2026-05-19_portfolio_xray_diagnostics_deepening_plan.md),
  and dedicated [Portfolio X-Ray diagnostics spec](docs/specs/portfolio_xray_diagnostics_spec.md)
  for Sessions 00-09 (`RM-930`-`RM-939`).
- Added active [Post-Portfolio-First Stabilization Plan](docs/exec_plans/2026-05-19_post_portfolio_first_stabilization_plan.md)
  and roadmap Phase 9 (`RM-900`-`RM-911`) to stabilize subject metadata, candidate freshness,
  decision reliability, methodology consistency, monitoring, and report/PDF output before UI work.
- [Post-Portfolio-First State Audit](docs/audits/2026-05-19_post_portfolio_first_state_audit.md):
  documents system state after transition closure, latest `run_portfolio_review.py` evidence, P0–P2
  stabilization backlog, and register entry in [docs/audits/README.md](docs/audits/README.md).

## 2026-05-18

### Added

- Closed the portfolio-first transition with offline E2E coverage for `current_portfolio`,
  `model_portfolio`, and `universe_baseline` subjects through comparison, decision artifacts, and
  decision-package reporting (Portfolio-first Session 09).
- Updated decision-package report language and generated-output QA for the portfolio-first story:
  summaries now name `analysis_subject` as the starting portfolio and scored rows as candidate
  alternatives, with config examples for current/model subjects (Portfolio-first Session 08).
- Isolated legacy policy workflow language: `run_portfolio_review.py` is now the documented normal
  first command, while `run_optimization.py` and `run_mvp_workflow.py` help/docs are labeled legacy
  compatibility (Portfolio-first Session 07).
- Added subject-centered comparison and decision baselines: `candidate_comparison.json` now includes `analysis_subject`, and Selection/No-Trade, Action, Monitoring, and Decision Journal prefer that baseline before legacy `current` (Portfolio-first Session 06).
- Added portfolio-first orchestration ([run_portfolio_review.py](run_portfolio_review.py), [src/portfolio_review_workflow.py](src/portfolio_review_workflow.py), [tests/test_portfolio_review_workflow.py](tests/test_portfolio_review_workflow.py)) to materialize `analysis_subject` before non-policy candidates and comparison without calling `run_optimization.py` by default (Portfolio-first Session 05).
- Added `run_report.py --materialize-analysis-subject` to write portfolio-first subject diagnostics under `{output_dir_final}/analysis_subject/` before candidate generation (Portfolio-first Session 04).
- Added explicit `analysis_subject` config/schema support and resolver export through `analysis_setup` and `input_assumptions` (Portfolio-first Session 03).
- Added canonical [portfolio review workflow spec](docs/specs/portfolio_review_workflow_spec.md) for the `analysis_subject`-first contract and linked it from top-level source-of-truth docs (Portfolio-first Session 02).
- Added active [Portfolio-First Transition Plan](docs/exec_plans/2026-05-18_portfolio_first_transition_plan.md) and roadmap Phase 8 (`RM-800`-`RM-808`) to move the main workflow from policy-first to `analysis_subject`-first while preserving the old policy engine as legacy infrastructure.

- Closed [post-audit MVP stabilization plan](docs/exec_plans/2026-05-17_post_audit_mvp_stabilization_plan.md) Session 11: Phase 7 (`RM-700`–`RM-710`) complete; broad verification (`462` pytest passes, docs verify, generated-output QA scan).
- Added file-first MVP workflow orchestration ([run_mvp_workflow.py](run_mvp_workflow.py), [src/mvp_workflow.py](src/mvp_workflow.py), [tests/test_mvp_workflow.py](tests/test_mvp_workflow.py)): thin wrapper for `input -> diagnosis -> comparison -> action`; documented in [docs/operational_runbook.md](docs/operational_runbook.md) (MVP stabilization Session 10).
- Added offline MVP pipeline smoke test ([tests/test_mvp_pipeline_offline.py](tests/test_mvp_pipeline_offline.py), [tests/mvp_offline_fixtures.py](tests/mvp_offline_fixtures.py)): synthetic snapshots, network guards, and decision-package JSON chain verification; documented in [TESTING.md](TESTING.md) (MVP stabilization Session 09).

### Changed

- Updated [README](README.md) and [ARCHITECTURE](ARCHITECTURE.md) to document supported partial utility UIs (`config_ui/`, `results_dashboard/`) vs full product workspace TBD.

### Fixed

- Removed active issue `KI-2026-05-18-002` after the default workflow was moved to
  `analysis_subject`-first and covered by offline end-to-end tests.
- Removed active issue `KI-2026-05-17-004` after partial utility UI status was synced in top-level docs (MVP stabilization Session 11).
- Removed active issue `KI-2026-05-17-020` after the offline MVP smoke test landed.

## 2026-05-17

### Added

- Added [repeat project MVP readiness audit](docs/audits/2026-05-17_repeat_project_mvp_readiness_audit.md) and active [post-audit MVP stabilization plan](docs/exec_plans/2026-05-17_post_audit_mvp_stabilization_plan.md), with roadmap/register/known-issue handoff for Sessions 01-11.
- Implemented [src/regret_analysis.py](src/regret_analysis.py): `regret_analysis_v1` JSON/TXT, stress-scenario regret vs best available, reference profiles favored/current/benchmark, Tier B CAGR slice, wired after Pareto in `write_candidate_comparison_outputs`, decision-package Regret section; [tests/test_regret_analysis.py](tests/test_regret_analysis.py) (post-audit Session 19).
- Added [regret analysis spec](docs/specs/regret_analysis_spec.md): `regret_analysis_v1` contract, stress-scenario regret vs best available, reference profiles favored/current/benchmark, pipeline placement after Pareto (post-audit Session 18); decision `DEC-2026-05-17-011`.
- Implemented [src/pareto_dominance.py](src/pareto_dominance.py): `pareto_dominance_v1` JSON/TXT, strict Pareto dominance on comparison metrics, wired after assumption sensitivity in `write_candidate_comparison_outputs`, decision-package section; optional `es_95` in comparison metrics; [tests/test_pareto_dominance.py](tests/test_pareto_dominance.py) (post-audit Session 17).
- Added [pareto dominance spec](docs/specs/pareto_dominance_spec.md): `pareto_dominance_v1` contract, strict Pareto objectives, pairwise dominance rules, pipeline placement after assumption sensitivity (post-audit Session 16); decision `DEC-2026-05-17-010`.
- Implemented [src/assumption_sensitivity.py](src/assumption_sensitivity.py): `assumption_sensitivity_v1` JSON/TXT, Tier A/B variant grid, wired after trade-off in `write_candidate_comparison_outputs`, decision-package summary section; [tests/test_assumption_sensitivity.py](tests/test_assumption_sensitivity.py) (post-audit Session 15).
- Added [assumption sensitivity spec](docs/specs/assumption_sensitivity_spec.md): `assumption_sensitivity_v1` contract, Tier A selection-weight variants, Tier B evidence ranks, stability bands, pipeline placement after trade-off (post-audit Session 14); decision `DEC-2026-05-17-009`.
- Implemented [src/tradeoff_and_model_risk.py](src/tradeoff_and_model_risk.py): `tradeoff_explanation_v1` and `model_risk_diagnostics_v1` after selection in `write_candidate_comparison_outputs`; decision package and journal integration; [tests/test_tradeoff_and_model_risk.py](tests/test_tradeoff_and_model_risk.py) (post-audit Session 13).
- Added [trade-off and model risk spec](docs/specs/tradeoff_and_model_risk_spec.md): `tradeoff_explanation_v1` and `model_risk_diagnostics_v1` contracts, warning catalog, pipeline placement after selection (post-audit Session 12); decision `DEC-2026-05-17-008`.
- Implemented candidate factory (post-audit Session 11): [run_candidate_factory.py](run_candidate_factory.py), [src/candidate_factory.py](src/candidate_factory.py), profiles and skip-existing orchestration, `candidate_factory_run.json` / `.txt`, optional `--then-compare`; [tests/test_candidate_factory.py](tests/test_candidate_factory.py).
- Added [candidate factory spec](docs/specs/candidate_factory_spec.md): V1 orchestration profiles, registry-to-script table, `candidate_factory_run_v1` contract, and planned `run_candidate_factory.py` CLI (post-audit Session 10; implementation Session 11); decision `DEC-2026-05-17-007`.
- Implemented current-vs-policy workflow (post-audit Session 09): `run_report.py --materialize-current`, sidecar resolution in [src/candidate_comparison.py](src/candidate_comparison.py), [src/current_vs_policy.py](src/current_vs_policy.py) status artifacts, reporting/selection/action gating; [tests/test_current_vs_policy_workflow.py](tests/test_current_vs_policy_workflow.py).
- Added [current vs policy workflow spec](docs/specs/current_vs_policy_workflow_spec.md): V1 combined workflow (policy on Main + `current_portfolio/` sidecar), No-Trade actionability matrix, skip reason codes, and `current_vs_policy_status_v1` contract (post-audit Session 08).
- Added [audit register](docs/audits/README.md) and [ExecPlan register](docs/exec_plans/README.md) to keep audit history, plan history, and the active plan pointer in concise documentation indexes.
- Added [post-audit stabilization and analytics ExecPlan](docs/exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md) to guide separate future sessions for docs sync, report integration, workflow hardening, candidate factory, and new analytics.
- Added the post-session deep system audit after Sessions 01-20, covering concept alignment, docs/code drift, Post-closure triage, and Main-vs-robust optimizer boundaries.
- Implemented [src/decision_journal.py](src/decision_journal.py): generated-only `decision_journal_v1` JSON/TXT projecting selection, action, monitoring, and comparison; `journal/latest/` and `journal/history/` copies; wired after monitoring in `write_candidate_comparison_outputs`; [tests/test_decision_journal.py](tests/test_decision_journal.py).
- Added [decision journal spec](docs/specs/decision_journal_spec.md) (`decision_journal_v1`): generated-only decision record, journal latest/history layout, pipeline placement after monitoring.
- Implemented [src/monitoring.py](src/monitoring.py): `analysis_snapshot_v1` under `monitoring/latest/` and `history/`, `monitoring_diff_v1` JSON/TXT vs prior snapshot; wired in `write_candidate_comparison_outputs`; [tests/test_monitoring.py](tests/test_monitoring.py).
- Added [monitoring spec](docs/specs/monitoring_spec.md) (`analysis_snapshot_v1`, `monitoring_diff_v1`): What Changed contract, profile projection for current/policy, pipeline placement.
- Implemented [src/action_engine.py](src/action_engine.py): non-executing `action_plan.json` / `.txt` from selection and comparison (weight deltas, trades when `selected_candidate`, 10 bps transaction-cost estimate on turnover half-sum, always written after selection); wired in `write_candidate_comparison_outputs`; [tests/test_action_engine.py](tests/test_action_engine.py).
- Added [action engine spec](docs/specs/action_engine_spec.md) (`action_plan_v1`): Rebalancing Advisor contract, action statuses, transaction-cost model, pipeline placement.
- Implemented [src/selection_engine.py](src/selection_engine.py): formal non-executing `selection_decision.json` / `.txt` from comparison and score artifacts (policy default, composite fallback, No-Trade materiality, five decision statuses); wired in `write_candidate_comparison_outputs`; [tests/test_selection_engine.py](tests/test_selection_engine.py).
- Added [selection engine spec](docs/specs/selection_engine_spec.md) (`selection_decision_v1`): formal decision outcomes, composite selection from health and robustness scores, No-Trade materiality thresholds, neutral decision-support wording.
- Implemented [src/portfolio_health_score.py](src/portfolio_health_score.py): diagnostic `portfolio_health_score.json` / `.txt` from `candidate_comparison.json` (ten components, optional robustness `resilience_reference`); comparison `weight_concentration` from `snapshot_10y.final_weights_total`; [tests/test_portfolio_health_score.py](tests/test_portfolio_health_score.py).
- Added [portfolio health score spec](docs/specs/portfolio_health_score_spec.md) (`portfolio_health_score_v1`): ten weighted components, within-run ranks plus absolute mandate/liquidity checks, optional `resilience_reference` from robustness scorecard, comparison `weight_concentration` prerequisite for Session 13.
- Implemented [src/robustness_scorecard.py](src/robustness_scorecard.py): diagnostic `robustness_scorecard.json` / `.txt` from `candidate_comparison.json` (six components, within-run ranks, mandate cap, stress_report fallback).
- Extended [src/candidate_comparison.py](src/candidate_comparison.py) with per-candidate `diversification` (RC from `snapshot_10y.json`) and automatic scorecard export; [tests/test_robustness_scorecard.py](tests/test_robustness_scorecard.py).
- Added [robustness scorecard spec](docs/specs/robustness_scorecard_spec.md) (`robustness_scorecard_v1`): six weighted components, relative within-run scoring, mandate absolute checks, RC via comparison `diversification` block.
- Added [src/candidate_comparison.py](src/candidate_comparison.py) read-only builder for canonical `candidate_comparison.json` (18-candidate registry, policy/current gating, legacy subset export) and [tests/test_candidate_comparison.py](tests/test_candidate_comparison.py).
- Added [candidate comparison spec](docs/specs/candidate_comparison_spec.md) defining canonical `candidate_comparison.json` under `output_dir_final` (full candidate registry, `current` row, diagnostic-only boundary).
- Added [docs/ROADMAP.md](docs/ROADMAP.md) as the durable phased development roadmap and audit-to-session backlog.
- Added active audit-derived issues to [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for unresolved source-of-truth, config UI, rebalance, encoding, and docs-verification gaps.
- Added [scripts/verify_docs.py](scripts/verify_docs.py), [src/docs_verify.py](src/docs_verify.py), and [tests/test_docs_links.py](tests/test_docs_links.py) for repeatable Markdown link and stale-reference checks.
- Added [decision package reporting spec](docs/specs/decision_package_reporting_spec.md) and [src/decision_package_reporting.py](src/decision_package_reporting.py): compact `decision_package_summary` TXT/JSON, `report.txt` append, comparison CLI paths, optional decision-package PDF; [tests/test_decision_package_reporting.py](tests/test_decision_package_reporting.py).

### Changed

- Completed MVP stabilization Session 08 (`RM-707`): regenerated representative Main/EW/RP outputs, added generated-output QA scan/test, English EW/RP comparison labels, and FRED CSV fallback when `pandas_datareader` is unavailable.
- Completed MVP stabilization Session 06 (`RM-705`): time-to-recovery now follows the max-drawdown peak/trough path, counts monthly/trading observations by index position, and treats no-drawdown windows as recovered with `ttr = 0`.
- Completed MVP stabilization Session 07 (`RM-706`): factor multicollinearity diagnostics now emit `assessment_en`; stress commentary prefers `assessment_en` and legacy-reads `assessment_ru` from older reports only.
- Completed MVP stabilization Session 05 (`RM-704`): NaN-safe data policy docs now define when `n_months_cash_fallback` is counted after risk-weight redistribution.
- Completed MVP stabilization Session 04 (`RM-703`): monthly return-panel cache keys now include resolved asset-currency metadata so FX-adjusted cached panels invalidate after `assets.yml` currency changes.
- Completed MVP stabilization Session 03 (`RM-702`): synced risk-free and cash policy docs/tests so USD/EUR defaults are explicit and unsupported non-USD currencies require configured cash and risk-free sources.
- Completed MVP stabilization Session 02 (`RM-701`): synced `README.md`, `ARCHITECTURE.md`, and `PRODUCT.md` so implemented file-first factory, current-vs-policy, trade-off/model-risk, assumption sensitivity, Pareto, regret, and decision-package outputs are not described as target/TBD work.
- Closed post-audit stabilization plan (Session 20, `RM-623`): marked [post-audit ExecPlan](docs/exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md) completed, updated [docs/ROADMAP.md](docs/ROADMAP.md) and [exec plan register](docs/exec_plans/README.md), synced [PRODUCT.md](PRODUCT.md) comparison targets with implemented factory/current-vs-policy/Pareto/regret file-first artifacts.
- Cross-linked current-vs-policy workflow spec from candidate comparison, input assumptions, selection, action, reporting outputs, OUTPUTS, and spec index (post-audit Session 08).
- Cleaned source/generator text defaults across optimization/report/PDF/config/docs paths so project artifacts use English and common mojibake markers are removed from source.
- Synced detailed decision-package specs so reporting, comparison, selection, action, monitoring, and journal contracts describe the implemented V1 artifact chain instead of stale future/TBD neighbors.
- Synced top-level docs after the post-session audit: `README.md`, `AGENTS.md`, `SPEC.md`, `PRODUCT.md`, and `ARCHITECTURE.md` now treat the V1 decision pipeline as implemented file-first artifacts while keeping full UI/workspace and advanced analytics as future work.
- Updated [docs/ROADMAP.md](docs/ROADMAP.md), [DECISIONS.md](DECISIONS.md), and [KNOWN_ISSUES.md](KNOWN_ISSUES.md) with post-session next-stage priorities and unresolved stabilization issues.
- Extended [src/candidate_comparison.py](src/candidate_comparison.py) and [run_compare_variants.py](run_compare_variants.py) to export robustness scorecard and portfolio health score after each comparison run.
- Refactored [run_compare_variants.py](run_compare_variants.py) to call the shared candidate comparison builder (canonical JSON + legacy `portfolio_comparison.*`).
- Updated [DECISIONS.md](DECISIONS.md) to remove the stale empty-log wording and record the roadmap ownership decision.

### Fixed

- Closed `KI-2026-05-17-019` by emitting `assessment_en` from factor multicollinearity diagnostics and keeping `assessment_ru` as legacy-read compatibility in stress commentary only.
- Closed `KI-2026-05-17-007` after representative output regeneration and automated QA scan passed; opened `KI-2026-05-18-001` for the residual decision-package PDF Pandoc failure.
- Closed `KI-2026-05-17-018` by adding focused recovered/unrecovered/no-drawdown TTR regressions and correcting monthly/daily recovery semantics.
- Closed `KI-2026-05-17-017` by counting actual NaN-safe cash fallback months and adding focused regressions for missing-risk residual cash usage.
- Closed `KI-2026-05-17-016` by adding an asset-currency metadata fingerprint to monthly cache keys and focused regression coverage for currency-metadata invalidation.
- Closed `KI-2026-05-17-015` by aligning risk-free/cash policy wording with config resolver behavior and adding focused regressions for EUR defaults and unsupported-currency explicit configuration.
- Closed `KI-2026-05-17-014` by removing top-level implemented-as-TBD wording for the file-first V1 decision artifact chain.
- Closed `KI-2026-05-17-006` by assigning Selection Engine V1 the unique decision ID `DEC-2026-05-17-006` and updating the session handoff references.
- Closed `KI-2026-05-17-005` by removing stale top-level wording that described implemented Health Score, Selection/No-Trade, Monitoring, and Decision Journal artifacts as target/TBD.
- Project-wide documentation hygiene: fixed punctuation/math mojibake in `.cursor/` agents and rules, `docs/`, and engineering Python (`run_report.py`, `src/snapshot.py`, `results_dashboard/app.py`, `src/pdf_reports.py`, `src/config.py`); restored cp1251-mojibake logger text in `run_report.py`.
- Cleaned source-document mojibake in [production_workflow.md](docs/specs/production_workflow.md), [stress_testing_spec.md](docs/specs/stress_testing_spec.md), [metrics_specification.md](docs/specs/metrics_specification.md), and [view_after_optimization_spec.md](docs/specs/view_after_optimization_spec.md).
- Clarified [rebalance.py](src/rebalance.py) threshold docstrings: `threshold_pct` gates on max absolute per-ticker weight drift only; added focused regression tests.
- Rewrote the [stress testing spec](docs/specs/stress_testing_spec.md) stress covariance section so `taxonomy_blend_v1` is the current default and `uniform_legacy` is clearly legacy-only.
- Removed the stale editable `rc_asset_cap_pct` field from the config UI and added focused regression coverage.
- Updated the config UI to separate `analysis_mode`, user-entered `current_weights`, and read-only generated `portfolio_weights.yml` output.

## 2026-05-15

### Added

- Added Portfolio X-Ray v2 with generated `portfolio_xray.json`, common section schema, rule-based hidden-risk flags, archetype caveats, weakness map, and diagnostic-only report wiring.
- Added `analysis_setup_v1` as the resolved Input and Assumptions runtime contract and exported it in run artifacts alongside projected `input_assumptions`.
- Added Portfolio X-Ray summary helpers for report/commentary surfaces, including setup, allocation, risk-contribution, and explanatory diagnostic verdict sections.
- Added Input and Assumptions Layer V1 with `analysis_mode`, `current_weights`, an `input_assumptions` artifact summary, and the canonical [input assumptions spec](docs/specs/input_assumptions_spec.md).
- Added [GLOSSARY.md](GLOSSARY.md) as a living glossary for shared project terminology.
- Added [OUTPUTS.md](OUTPUTS.md) as the root map for generated outputs, report artifacts, output folders, formats, and generated-vs-source boundaries.
- Added [WORKFLOW.md](WORKFLOW.md) as the explicit task workflow from request to implementation, verification, docs sync, project memory, and commit.
- Added [DECISIONS.md](DECISIONS.md) as the concise living decision log for key project decisions and rationale.
- Added [CHANGELOG.md](CHANGELOG.md) as the concise living history for meaningful project changes.
- Added [KNOWN_ISSUES.md](KNOWN_ISSUES.md) as the living register for active issues, model limitations, testing gaps, and technical debt.

### Changed

- Populated [GLOSSARY.md](GLOSSARY.md) with the initial 80 shared project terms.
- Linked decision-log, changelog, and known-issues governance from the top-level documentation maps.
- Simplified top-level documentation routing and clarified source-of-truth links across root docs.

## 2026-05-14

### Added

- Added [DATA.md](DATA.md) as the living data-layer map.
- Added [TESTING.md](TESTING.md) as the project verification framework.

### Changed

- Reorganized project documentation around compact top-level maps and detailed specs under [docs/specs/](docs/specs/README.md).
- Clarified that [docs/DIAGNOSTIC_PRODUCT_CONCEPT.md](docs/DIAGNOSTIC_PRODUCT_CONCEPT.md) is a living product blueprint, not a binding implementation spec.
