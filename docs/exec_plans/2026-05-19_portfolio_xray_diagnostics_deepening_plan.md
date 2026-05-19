# Portfolio X-Ray Diagnostics Deepening Plan

This ExecPlan is a living document. Keep `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` updated as work proceeds.

## Purpose / Big Picture

Deepen the Portfolio X-Ray / Diagnostics Layer so the current portfolio is diagnosed reliably before candidate comparison, optimization, or UI work. The target is a trustworthy seven-section diagnostic product for `analysis_subject`:

1. Asset Allocation
2. Portfolio Metrics / Risk Diagnostics
3. Factor Exposure / Factor Sensitivity
4. Hidden Exposure / Hidden Risk Detector
5. Portfolio Archetype Classification
6. Risk Budget View
7. Portfolio Weakness Map

The work stays diagnostic-only. It must not alter optimizer policy, mandate gates, candidate selection, weight release, or formal decision artifacts unless a future accepted spec explicitly changes that boundary.

## Progress

- [x] 2026-05-19 Session 00: Created project-memory scaffold, active ExecPlan, X-Ray diagnostics spec skeleton, roadmap entries, audit registration, and known-issue routing.
- [x] Session 01: P0 Data Cutoff And Analysis-End Integrity.
- [x] Session 02: P0 X-Ray Evidence Completeness.
- [x] Session 03: P0 VaR / ES Methodology Alignment.
- [x] Session 04: Portfolio Metrics Deepening.
- [x] Session 05: Hidden Risk Detector V2.
- [x] Session 06: Weakness Map V2.
- [x] Session 07: Portfolio Archetype Classification V2.
- [x] Session 08: Report / HTML / PDF Productization Of X-Ray.
- [x] Session 09: Operational Portfolio-First Review.

## Surprises & Discoveries

- The X-Ray artifact already has all seven intended sections, but the implementation is closer to a metrics aggregator than a full diagnostic product.
- Latest portfolio-first evidence showed `analysis_end = 2026-04-30`, while at least one generated diagnostic consumer could disclose `data_end = 2026-05-31`.
- Full risk contribution evidence exists in `results_csv/rc_vol_10y.csv`, but X-Ray risk budget reads a top-5 snapshot subset.
- Kalman factor beta evidence exists under `stress_report.factor_betas_kalman.latest`, but X-Ray expects older field names.
- VaR / ES frequency semantics need alignment: the current base output appears monthly while the metrics spec describes daily historical VaR / ES.

- Session 01 (2026-05-19): Added `truncate_to_analysis_end`, report-path panel truncation, SSA/scenario-library cutoff, effective vs raw input exports, and `tests/test_analysis_end_cutoff.py`.
- Session 02 (2026-05-19): Risk Budget View loads full `rc_vol_*` CSV evidence; Kalman betas read `factor_betas_kalman.latest`; focused tests in `tests/test_portfolio_xray.py`.
- Session 03 (2026-05-19): Daily historical VaR/ES via `compute_tail_risk_historical`, `load_daily_asset_returns_shared`, `analytics.tail_risk` block, X-Ray `tail_risk` item; tests in `tests/test_tail_risk.py`.
- Session 04 (2026-05-19): Portfolio skew/kurtosis, downside/upside beta, corr_base, rolling beta/correlation summaries, `metric_quality` metadata; X-Ray risk diagnostics exposure; tests in `tests/test_portfolio_metrics_deepening.py`.
- Session 05 (2026-05-19): Hidden Risk Detector V2 with per-category flagged/below-threshold/unavailable assessments, raw+residual PCA, tail risk, weak hedge, macro factor dependency, section `confidence` and evidence counts; tests in `tests/test_portfolio_xray.py`.
- Session 06 (2026-05-19): Weakness Map V2 with `exposure_present`, `adverse_evidence`, `severity`, `confidence`, `scenario_coverage`, top asset/factor drivers, per-row `missing_inputs`, conditional `crypto_shock`; tests in `tests/test_portfolio_xray.py`.
- Session 07 (2026-05-20): Portfolio Archetype V2 scorecard with per-archetype positive/negative evidence, `archetype_scorecard`, regime `conflicting_signals`, `conflict_summary`, weakness-map tensions; archetype built after weakness map; tests in `tests/test_portfolio_xray.py`.
- Session 08 (2026-05-20): Structured X-Ray HTML (`format_portfolio_xray_html`), readable `report.txt` tables, compact `commentary.txt` via `format_portfolio_xray_commentary`, generated-output QA markers in `src/generated_output_qa.py`; tests in `tests/test_portfolio_xray.py` and `tests/test_generated_output_language.py`.
- Session 09 (2026-05-20): Core/full review modes on `run_portfolio_review.py` (`--mode core|full`, profile `core_v1` vs `default_v1`); `candidate_menu` partial-menu disclosure in comparison and decision package; operational runbook and spec updates; tests in `tests/test_portfolio_review_workflow.py`, `tests/test_candidate_factory.py`, `tests/test_candidate_comparison.py`.

## Decision Log

- Decision: Work must be split into separate sessions/chats after Session 00.
  Rationale: The plan spans data policy, metric methodology, X-Ray schemas, report rendering, and operational workflow. Keeping each major block separate reduces context loss and lets each session verify one risk area.

- Decision: P0 trust fixes precede report polish and UI work.
  Rationale: A better-looking report would create false confidence if date cutoff, risk budget evidence, Kalman evidence, or tail-risk methodology remain wrong.

- Decision: Create a dedicated X-Ray diagnostics spec.
  Rationale: The current X-Ray behavior is spread across `src/portfolio_xray.py`, report code, and older plans. Future sessions need one source-of-truth product/technical contract.

## Outcomes & Retrospective

Plan closed 2026-05-20 after Session 09. Delivered: P0 trust fixes (analysis_end, RC/Kalman, VaR/ES),
deepened metrics and X-Ray sections (hidden risk, weakness map, archetype), report productization,
and operational portfolio-first review (`--mode core|full`, `candidate_menu` disclosure). Remaining
operational gap: factory resumability (`RM-921`). UI (`RM-500+`) can proceed on the stabilized
diagnostic + core-run contract.

## Context and Orientation

Start every session by reading:

- `AGENTS.md`
- `WORKFLOW.md`
- `RULES.md`
- `SPEC.md`
- `OUTPUTS.md`
- `DATA.md` when data behavior is touched
- `TESTING.md`
- [Portfolio X-Ray Layer Audit](../audits/2026-05-19_portfolio_xray_layer_audit.md)
- [Portfolio X-Ray Diagnostics Spec](../specs/portfolio_xray_diagnostics_spec.md)
- this ExecPlan
- the owning specs for the session
- latest generated `Main portfolio/analysis_subject/` artifacts when generated-output evidence matters

Primary code areas:

- `src/portfolio_xray.py`
- `src/snapshot.py`
- `src/portfolio_analytics.py`
- `src/portfolio_commentary.py`
- `src/pdf_reports.py`
- `run_report.py`
- `run_portfolio_review.py`
- `src/stress.py`
- `src/stress_scenario_analytics.py`
- metric modules under `src/`

Generated artifacts are evidence, not source. Do not commit generated outputs unless a session explicitly targets regenerated artifacts.

## Plan of Work

### Session 00: Project Memory And X-Ray Spec Scaffold

Goal: record the audit and plan so the next chat can continue without restating context.

Tasks:

- Create `docs/audits/2026-05-19_portfolio_xray_layer_audit.md`.
- Create this active ExecPlan.
- Create `docs/specs/portfolio_xray_diagnostics_spec.md`.
- Register audit, plan, roadmap, known issues, spec index, outputs ownership, and changelog.

Expected output: active project-level handoff and X-Ray source-of-truth skeleton.

Ready when: `python scripts/verify_docs.py` passes and `docs/exec_plans/README.md` points to this plan as Active.

Start a new session after completion.

### Session 01: P0 Data Cutoff And Analysis-End Integrity

Goal: ensure diagnostics do not use or disclose rows after `analysis_end`.

Tasks:

- Check and fix effective-date filtering for `inputs/monthly_returns.csv`, stress scenario analytics, scenario library, and data exports.
- Ensure diagnostic consumers use rows `<= analysis_end`, even when raw cached panels contain later incomplete periods.
- Add tests proving generated diagnostic consumers do not claim data after `analysis_end`.
- Document the difference between raw cached panels and analysis-effective panels.

Likely files:

- `src/data_loader.py`
- `run_report.py`
- `src/stress_scenario_analytics.py`
- `docs/specs/data_policy_spec.md`
- `docs/specs/metrics_specification.md`
- `DATA.md`

Expected output: `analysis_subject` artifacts do not show diagnostic `data_end` later than `analysis_end`.

Ready when: focused cutoff tests pass and a fresh subject run with `analysis_end = 2026-04-30` has no diagnostic consumer claiming `2026-05-31`.

Start a new session after focused tests and manual artifact review.

### Session 02: P0 X-Ray Evidence Completeness

Goal: remove misleading X-Ray evidence gaps.

Tasks:

- Make Risk Budget View consume full risk contribution evidence, not top-5 snapshot display data.
- Keep `snapshot_10y.json` top-5 behavior only where it is intentionally display-oriented.
- Fix Kalman mapping so X-Ray reads `stress_report.factor_betas_kalman.latest`.
- Add tests for complete RC coverage and Kalman beta population.

Likely files:

- `src/portfolio_xray.py`
- `src/snapshot.py`
- `src/portfolio_commentary.py`
- `tests/test_portfolio_xray.py`
- `OUTPUTS.md`
- `docs/specs/portfolio_xray_diagnostics_spec.md`

Expected output: all positive-weight holdings with RC evidence receive risk contribution in `portfolio_xray.json`; Kalman current beta is populated when available.

Ready when: focused X-Ray tests pass and regenerated subject artifact review confirms complete RC for current holdings.

Start a new session after regenerated artifact review.

### Session 03: P0 VaR / ES Methodology Alignment

Goal: align VaR / ES with the canonical metrics specification or explicitly revise the spec.

Tasks:

- Decide and document whether portfolio diagnostics use daily or monthly historical VaR / ES.
- Recommended default: daily VaR / ES for portfolio diagnostics; monthly version only if explicitly labeled.
- Add daily portfolio return construction aligned with investor currency and cash rules.
- Expose method, frequency, and window in `portfolio_xray.json`.

Likely files:

- `src/portfolio_analytics.py`
- `run_report.py`
- `src/metrics_daily.py`
- `docs/specs/metrics_specification.md`
- `tests/test_returns_frequency.py`
- `tests/test_portfolio_xray.py`

Expected output: generated tail-risk fields and docs agree on method/frequency/window.

Ready when: tests prove daily VaR / ES when daily data is available and report text discloses the tail-risk horizon.

Start a new session after Session 02.

### Session 04: Portfolio Metrics Deepening

Goal: fill core missing risk diagnostics.

Tasks:

- Add portfolio skewness and kurtosis on monthly log returns.
- Add downside beta and upside beta versus base benchmark.
- Add rolling beta / rolling correlation summaries.
- Add metric quality metadata: `n_obs`, frequency, benchmark, risk-free source, and window.

Likely files:

- `src/metrics_portfolio.py`
- `src/metrics_asset.py`
- `src/portfolio_analytics.py`
- `run_report.py`
- snapshot writers
- `docs/specs/portfolio_xray_diagnostics_spec.md`

Expected output: Risk Diagnostics covers core return, drawdown, beta, tail, shape, rolling, and quality metadata.

Ready when: focused metrics tests pass and `snapshot_10y.json` / `portfolio_xray.json` expose the new metrics.

Start a new session after Session 03.

### Session 05: Hidden Risk Detector V2

Goal: make hidden-risk output decision-useful instead of threshold snippets.

Tasks:

- Add explicit flags for tail risk, weak hedge behavior, residual PCA concentration, liquidity risk, and stress contributor concentration.
- Use both raw and residual PCA evidence where available.
- Add "not flagged / below threshold" evidence for critical categories.
- Add section-level confidence and evidence count.

Likely files:

- `src/portfolio_xray.py`
- `src/stress_factors.py` only if PCA summary exposure needs a small extension
- `docs/specs/portfolio_xray_diagnostics_spec.md`
- `tests/test_portfolio_xray.py`

Expected output: Hidden Risk Detector answers hidden equity beta, duration, credit, liquidity, correlation/common factor, weak hedge, tail risk, and macro/factor dependency.

Ready when: tests cover positive flags and below-threshold non-flags.

Start a new session after Session 04.

### Session 06: Weakness Map V2

Goal: turn Weakness Map into a scenario/regime vulnerability map.

Tasks:

- Separate `exposure_present`, `adverse_evidence`, `severity`, and `confidence`.
- Add top asset loss drivers and factor drivers per weakness.
- Add scenario coverage and missing-input warnings.
- Add crypto shock only when relevant assets/taxonomy indicate crypto exposure.

Likely files:

- `src/portfolio_xray.py`
- `src/stress.py`
- `src/stress_scenario_analytics.py`
- `docs/specs/stress_testing_spec.md`
- `docs/specs/portfolio_xray_diagnostics_spec.md`

Expected output: weakness rows explain why a scenario is or is not a weakness, without implying zero risk when severity is low.

Ready when: tests cover high-risk and low-risk scenarios and generated rows include evidence type and top drivers.

Start a new session after Session 05.

### Session 07: Portfolio Archetype Classification V2

Goal: replace simplistic archetype labels with a caveated evidence scorecard.

Tasks:

- Define archetype scorecard in spec before code.
- Each archetype must include positive evidence, negative evidence, confidence, and conflicting signals.
- Explain contradictions, for example inflation-sensitive holdings with high inflation/rates vulnerability.
- Keep archetype diagnostic-only and non-binding.

Likely files:

- `src/portfolio_xray.py`
- `docs/specs/portfolio_xray_diagnostics_spec.md`
- `PRODUCT.md`
- `tests/test_portfolio_xray.py`

Expected output: archetype output is interpretable and caveated.

Ready when: tests cover equity-growth, balanced, duration-heavy, inflation-sensitive, pseudo-diversified, and conflicting-signal cases.

Start a new session after Session 06.

### Session 08: Report / HTML / PDF Productization Of X-Ray

Goal: make X-Ray readable for an investor/advisor instead of exposing a JSON-style dump.

Tasks:

- Replace raw preformatted X-Ray block in HTML with structured sections and tables.
- Improve `report.txt` and `commentary.txt` wording.
- Keep `portfolio_xray.json` as the machine-readable source.
- Add generated-output QA checks for X-Ray wording.

Likely files:

- `src/snapshot.py`
- `src/portfolio_commentary.py`
- `src/pdf_reports.py`
- `src/generated_output_qa.py`
- `DESIGN.md`
- `OUTPUTS.md`

Expected output: report surfaces clearly show allocation, metrics, factor exposure, hidden risks, risk budget, and weakness map.

Ready when: focused commentary/report tests pass and a fresh subject run produces readable `report.html`, `report.txt`, and `commentary.txt`.

Start a new session after Sessions 01-07 are stable.

### Session 09: Operational Portfolio-First Review

Goal: return to deferred operational review work after X-Ray trust fixes.

Tasks:

- Split `run_portfolio_review.py` into core-run and full-run modes.
- Make core-run complete subject diagnostics, lightweight candidates, comparison, and decision package inside normal session limits.
- Keep full-run explicit for expensive optimizer/robust candidates.
- Add partial candidate menu disclosure.

Likely files:

- `run_portfolio_review.py`
- `src/portfolio_review_workflow.py`
- `src/candidate_factory.py`
- `src/candidate_comparison.py`
- `src/decision_package_reporting.py`
- `docs/operational_runbook.md`

Expected output: practical daily workflow exists and UI work no longer depends on one huge full factory run.

Ready when: core path finishes under an agreed time budget and partial menu disclosure is visible in comparison and decision outputs.

Start a new session only after X-Ray diagnostic trust issues are fixed.

## Concrete Steps

For each session:

1. Start a new chat unless the user explicitly asks for a tiny follow-up in the same session.
2. Read the orientation docs and this plan.
3. Inspect current code and generated artifacts before editing.
4. Update the owning spec first when behavior or schema changes.
5. Make the smallest code changes that satisfy the session.
6. Add focused tests.
7. Run focused verification and `python scripts/verify_docs.py` when docs changed.
8. Update this ExecPlan progress, surprises, decision log, and outcomes as needed.
9. Update `KNOWN_ISSUES.md`, `CHANGELOG.md`, and roadmap rows when items are fixed or deferred.

## Validation and Acceptance

Plan-level acceptance:

- Each P0 issue is fixed, tested, documented, and removed or updated in `KNOWN_ISSUES.md`.
- `portfolio_xray.json` remains diagnostic-only and machine-readable.
- User-facing report surfaces explain metrics, frequency, confidence, and limitations.
- A new agent can continue from this ExecPlan without needing chat history.

Session 00 validation:

- `python scripts/verify_docs.py`

Later session validation will include focused pytest suites named in each session plus artifact review of `{output_dir_final}/analysis_subject/`.

## Idempotence and Recovery

- Generated artifacts may be regenerated during verification, but they are not source.
- If a run fails after partially writing generated outputs, rerun the owning command after fixing code; do not infer source behavior from a partially written artifact.
- If a session uncovers a larger methodology conflict, stop and update this ExecPlan and the relevant spec before broad implementation.
- Avoid broad refactors unless the session cannot be completed safely without them.

## Artifacts and Notes

Primary generated artifacts to inspect in later sessions:

- `Main portfolio/analysis_subject/run_metadata.json`
- `Main portfolio/analysis_subject/portfolio_xray.json`
- `Main portfolio/analysis_subject/stress_report.json`
- `Main portfolio/analysis_subject/snapshot_10y.json`
- `Main portfolio/analysis_subject/results_csv/rc_vol_10y.csv`
- `Main portfolio/analysis_subject/results_csv/inputs/monthly_returns.csv`
- stress/scenario analytics CSVs under `Main portfolio/analysis_subject/results_csv/`

Known current evidence from the audit:

- Latest subject run had `analysis_end = 2026-04-30`.
- Some generated inputs or analytics showed later `2026-05-31` rows, which must be treated carefully in Session 01.
- Full RC evidence exists outside the top-5 snapshot.
- Kalman beta evidence exists under `factor_betas_kalman.latest`.

## Interfaces and Dependencies

The X-Ray layer consumes existing diagnostics:

- data policy and return panels from the data loader/report pipeline
- metric formulas from `docs/specs/metrics_specification.md`
- stress/scenario outputs from stress specs and modules
- factor/PCA outputs from factor diagnostics
- portfolio-first `analysis_subject` workflow from `docs/specs/portfolio_review_workflow_spec.md`
- output ownership from `OUTPUTS.md`

It must not:

- change optimizer objective functions
- change candidate selection
- change mandate pass/fail behavior
- release or alter weights
- convert diagnostic labels into formal recommendations
