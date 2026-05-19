# Post-Portfolio-First Stabilization Plan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows [PLANS.md](../../PLANS.md). It is the active project-level plan after the
2026-05-19 post-portfolio-first audit.

## Purpose / Big Picture

The portfolio-first transition is implemented, but the latest representative run still has trust
gaps that make advisor-facing interpretation risky. After this plan is complete,
`python run_portfolio_review.py` should produce a review whose subject metadata is correct, whose
candidate comparison is fresh enough to trust, whose selection/no-trade outcome is explainable, and
whose report package can be used as a client/advisor artifact. UI and broader product surfaces stay
deferred until the existing file-first pipeline is stable.

## Progress

- [x] (2026-05-19) Created the active stabilization ExecPlan and mapped the user-approved session order.
- [x] (2026-05-19) Session 01: Metadata Trust Fix.
- [x] (2026-05-19) Session 02: Candidate Freshness Contract.
- [x] (2026-05-19) Session 03: Quick Methodology Check.
- [x] (2026-05-19) Session 03A: Return Frequency Methodology Alignment.
- [x] (2026-05-19) Session 04: Selection And Mandate Reliability.
- [x] (2026-05-19) Session 05: Legacy Policy Boundary Cleanup.
- [x] (2026-05-19) Session 06: Regime Metrics Fix.
- [x] (2026-05-19) Session 07: Methodology Consistency Follow-Up.
- [x] (2026-05-19) Session 08: Monitoring First-Run Honesty.
- [x] (2026-05-19) Session 09: Decision PDF Repair.
- [x] (2026-05-19) Session 10: Report Scope And Noise Reduction.
- [x] (2026-05-19) Session 11: Fresh Representative Run And Closure.

## Surprises & Discoveries

- Observation: The working tree contains many modified generated outputs and source/document files
  from prior work.
  Evidence: `git status --short` shows modified root docs, generated portfolio folders, PDF outputs,
  Python modules, tests, and untracked portfolio-first artifacts.

- Observation: There is no active project-level ExecPlan before this session.
  Evidence: `docs/exec_plans/README.md` stated `Active: none`.

- Observation: Candidate factory skip-existing was based only on file presence.
  Evidence: `src/candidate_factory.py` skipped when `{artifact_root}/snapshot_10y.json` existed,
  without checking the snapshot `analysis_end` against the review date.

- Observation: Candidate comparison could aggregate a stale candidate snapshot when its
  `analysis_end` differed from the portfolio-first subject date.
  Evidence: focused regression coverage now marks such a row `unavailable` with
  `stale_snapshot_analysis_end`.

- Observation: `returns_frequency: daily` is not limited to daily/regime diagnostics; it changes
  the main investor return panel and portfolio metrics path.
  Evidence: `src/data_loader.py` builds `monthly_prices`, `monthly_returns`, `rf_monthly`,
  benchmark returns, and cash returns at `returns_frequency`; `run_report.py` passes
  `periods_per_year` from that frequency into `asset_metrics_one_window` and
  `portfolio_metrics_one_window`, uses the same panel for RC_vol and correlation, and writes
  frequency disclosure saying "Portfolio metrics and covariance use returns_frequency=...".

- Observation: `returns_frequency: daily` also affects legacy optimizer inputs rather than only
  report diagnostics.
  Evidence: `run_optimization.py` loads returns through `load_monthly_data_shared(...,
  returns_frequency=cfg.returns_frequency)`, derives `periods_per_year`, and passes both
  `periods_per_year` and `returns_frequency` into `run_max_return_optimization`; `src/optimization.py`
  maps the calendar window to frequency-specific bars and annualizes soft target volatility and
  return penalties with that period count.

- Observation: Session 04 began from a partially updated selection/reporting surface, but
  `tradeoff_explanation` still hard-coded `current` as the primary baseline.
  Evidence: before this session, `src/selection_engine.py` and
  `src/decision_package_reporting.py` already contained `analysis_subject` baseline handling, while
  `src/tradeoff_and_model_risk.py` still built the primary pair from `by_id["current"]` with
  `pair_id: current_to_favored`.

- Observation: A normal focused pytest run failed because pytest tried to remove a locked temp
  directory outside the workspace cache, not because of assertion failures.
  Evidence: `python` was not on PATH; `.venv\Scripts\python.exe -m pytest ...` without `--basetemp`
  raised `PermissionError: [WinError 5]` for
  `C:\Users\ShumeikoYe\.cache\codex-pytest-temp`, while the same focused tests passed with
  `--basetemp='tmp\pytest_session04_selection_mandate'`.

- Observation: The legacy policy visibility problem was not only wording; it also affected scoring
  surfaces.
  Evidence: before Session 05, `src/portfolio_health_score.py` used static
  `display_priority = ["current", "policy"]`, and `src/current_vs_policy.py` always classified
  portfolio-first comparison outputs into current-vs-policy profiles instead of marking the status
  as compatibility-only.

- Observation: The regime metrics failure was caused by the caller, not the regime metrics module.
  Evidence: `src/regime_portfolio_metrics.py` already accepted `mar_daily=None` and delegated the
  default to `sortino_daily(..., mar_daily=None)`, while `run_report.py` attempted to build
  `mar_daily_ser` from undefined `mar_monthly`.

- Observation: Decision-package PDF failure was a Pandoc section-title line break, not unescaped
  body percentages.
  Evidence: LaTeX error `l.186 2026-05-15}` came from `\section{Decision Package Summary --- analysis end`
  split across lines; body `%` values were already emitted as `\%`. YAML front matter removed the
  broken H1.

- Observation: A full `default_v1` candidate factory rebuild exceeds practical agent-session runtime
  on this machine; comparison refresh after a fresh subject run is sufficient to validate freshness
  gating when stale rows are marked `unavailable`.
  Evidence: Session 11 subject materialization completed; `run_compare_variants.py` at `2026-05-19`
  aligned `candidate_comparison.json` to `analysis_end: 2026-04-30` with six `available` and thirteen
  `unavailable` candidates (stale optimizers at `2026-05-15`); factory subprocess attempts timed out
  at 10–30 minutes without finishing the profile.

## Decision Log

- Decision: The stabilization sequence prioritizes subject metadata and candidate freshness before
  regime metrics and PDF repair.
  Rationale: Incorrect subject identity and stale candidates can invalidate comparison and selection;
  PDF and macro/regime issues matter, but they do not define the main comparison truth.
  Date/Author: 2026-05-19 / Codex, from user-approved roadmap revision.

- Decision: UI and product-layer work remain deferred until this plan closes.
  Rationale: A UI would amplify current trust gaps instead of solving them.
  Date/Author: 2026-05-19 / Codex, from user-approved roadmap revision.

- Decision: Each major roadmap item should be handled in a separate chat/session.
  Rationale: The project already has a large context surface; isolated sessions reduce accidental
  drift and make verification easier.
  Date/Author: 2026-05-19 / Codex, from repository agent rules and user instruction.

- Decision: Freshness is enforced both before reuse in Candidate Factory and during read-only
  Candidate Comparison.
  Rationale: Rebuilding stale artifacts solves the normal portfolio-first path, while comparison
  gating prevents manual or failed factory runs from silently feeding stale candidate evidence into
  Selection and downstream decision artifacts.
  Date/Author: 2026-05-19 / Codex, Session 02 RM-902.

- Decision: RM-903 promotes a methodology alignment fix before Session 04 instead of continuing
  directly to selection reliability.
  Rationale: The quick check found that non-monthly `returns_frequency` changes main metrics,
  covariance, RC_vol, correlation, backtest, and optimizer inputs governed by the monthly metrics
  standard. Selection/mandate explanations would be built on inconsistent methodology if Session
  04 proceeded first.
  Date/Author: 2026-05-19 / Codex, Session 03 RM-903.

- Decision: Session 04 was implemented as explicitly requested even though Session 03A remains open.
  Rationale: The user asked to continue the active plan with Session 04 and implement only that
  stage. The methodology alignment work remains deferred and was not changed in this session.
  Date/Author: 2026-05-19 / Codex, Session 04.

- Decision: Trade-off explanations now use the same preferred baseline as Selection:
  `selection_decision.baseline_candidate_id`, then `candidate_comparison.comparison_baseline_candidate_id`,
  then legacy `current`.
  Rationale: Portfolio-first decision artifacts must explain trade-offs versus the diagnosed
  starting portfolio (`analysis_subject`), not silently revert to legacy current-vs-policy framing.
  Date/Author: 2026-05-19 / Codex, Session 04.

- Decision: Decision-package summaries explicitly explain null favored candidates when
  `mandate_risk_reduction` blocks selection.
  Rationale: Advisor-facing output should not show only `Favored profile: —`; it must state that
  mandate risk-reduction gates blocked allocation selection and surface plain-English mandate notes.
  Date/Author: 2026-05-19 / Codex, Session 04.

- Decision: In portfolio-first runs with an available `analysis_subject`, root `policy` artifacts are
  gated as legacy compatibility evidence rather than ranked candidate evidence.
  Rationale: Keeping the row preserves legacy schema and consumers, while making it unavailable with
  an explicit reason prevents Health Score, Selection, and summaries from treating generated policy
  output as the default portfolio-first alternative.
  Date/Author: 2026-05-19 / Codex, Session 05.

- Decision: Regime-level daily Sortino uses `mar_daily=None` when no custom MAR is configured, which
  makes the metric use aligned daily risk-free as the default MAR; configured annual MAR is converted
  directly to a daily per-period value for this diagnostic block.
  Rationale: This matches the stress-testing spec and avoids depending on a monthly scalar in the
  daily regime path.
  Date/Author: 2026-05-19 / Codex, Session 06.

- Decision: Main portfolio metrics, covariance, RC_vol, correlation, optimizer inputs, mandate
  checks, and backtest always use monthly returns; config `returns_frequency` weekly/daily is
  disclosure-only via `configured_returns_frequency` and `frequency_disclosure`.
  Rationale: Session 03 found non-monthly config changed the main metrics path and contradicted the
  monthly metrics standard; portfolio-first selection must not run on mixed cadences.
  Date/Author: 2026-05-19 / Codex, Session 07 RM-907.

- Decision: When `monitoring_diff_v1` has `diff_status: no_prior_snapshot`, omit profile/decision
  deltas and do not report a prior `analysis_end` or prior snapshot path.
  Rationale: First-run and same-`analysis_end` re-runs were computing profile diffs against the
  on-disk prior file while labeling the result as having no prior, which misled advisors.
  Date/Author: 2026-05-19 / Codex, Session 08 RM-908.

- Decision: Decision-package PDF Markdown uses YAML front matter via
  `build_decision_package_pdf_md` instead of a long `#` H1 that embeds `analysis_end`.
  Rationale: Pandoc split the H1 across lines in LaTeX (`\section{... analysis end` / `2026-05-15}`),
  producing `Extra }, or forgotten \endgroup` and failing XeLaTeX; other reports already use YAML
  titles.
  Date/Author: 2026-05-19 / Codex, Session 09 RM-909.

- Decision: `run_portfolio_review.py` calls `rebuild_pdf_reports.py --portfolio-first` by default;
  `--legacy-full-pdf` opts into the full legacy variant suite.
  Rationale: Portfolio-first review should refresh advisor-facing subject and decision-package PDFs
  without rewriting EW/RP, policy Main, and optimizer baseline PDFs on every run.
  Date/Author: 2026-05-19 / Codex, Session 10 RM-910.

- Decision: Session 11 closure accepts a subject refresh plus comparison/PDF refresh when a full
  `default_v1` factory rebuild cannot complete within the session window; stale optimizer snapshots
  must remain explicitly `unavailable` in comparison, not silently scored.
  Rationale: Representative verification proved freshness gating and portfolio-first artifacts; a
  multi-hour factory rebuild is operational follow-up, not a blocker for plan closure.
  Date/Author: 2026-05-19 / Codex, Session 11 RM-911.

## Outcomes & Retrospective

Session 01 completed RM-901 by making candidate comparison prefer
`{output_dir_final}/analysis_subject/run_metadata.json` for top-level
`analysis_setup_summary`, with root metadata retained as fallback. Focused regression coverage now
proves a `current_portfolio` subject sidecar beats a stale root `universe_baseline` metadata file.

Session 02 completed RM-902 by adding a candidate freshness contract. Candidate Factory now resolves
the review `analysis_end` from `analysis_subject` first, skips an existing candidate snapshot only
when `snapshot_10y.json.analysis_end` matches that date, attempts rebuilds for stale snapshots, and
fails explicitly with `stale_snapshot_after_build` when a builder leaves stale evidence behind.
Candidate Comparison now resolves the comparison date from `analysis_subject` first and marks
mismatched candidate snapshots `unavailable` with `stale_snapshot_analysis_end`, blocking silent
downstream use of stale candidate metrics.

Session 03 completed RM-903 as a scoped methodology check. The finding is that
`returns_frequency: daily` affects the main portfolio metrics and optimizer path, not only
regime/daily diagnostics. The monthly metrics standard still defines the canonical portfolio
analytics base as monthly simple/log returns, monthly risk-free alignment, monthly covariance,
monthly RC_vol, and monthly drawdown/TTR periods. Because this is a methodology conflict, the next
work item before Session 04 is Session 03A: align runtime/config behavior and docs so
portfolio-first selection is not built on mixed daily-vs-monthly main metrics.

Session 04 completed the selection and mandate reliability slice requested in this chat without
touching Session 03A methodology behavior. Selection outputs now expose plain-English
`risk_reduction_notes` for mandate-blocked decisions. Trade-off explanations use the portfolio-first
baseline (`analysis_subject`) when Selection or Candidate Comparison identifies it, emit
`baseline_to_favored` as the primary pair, and retain legacy current-based secondary pairs when
available. Decision-package summaries now explain why no favored profile is shown when mandate
risk-reduction gates block selection, and map the internal `mandate_risk_reduction` warning to
client-safe English.

Session 05 completed RM-905 by tightening the legacy policy boundary without deleting compatibility
artifacts. Candidate Comparison now gates `policy` as unavailable with
`legacy_policy_not_default_portfolio_first_candidate` when an `analysis_subject` sidecar is present.
`current_vs_policy_status.json` uses `workflow_profile: portfolio_first_review` in that context,
Decision Package summaries hide the legacy current-vs-policy block for portfolio-first runs, and
Portfolio Health Score priority starts with `analysis_subject` instead of `current` / `policy`.
The active known issue for legacy policy visibility was removed after focused regression coverage and
documentation verification passed.

Session 06 completed RM-906 by removing the undefined `mar_monthly` dependency from
`run_report.py`'s regime metrics path. Regime portfolio metrics now pass `None` for MAR when
`min_acceptable_return` is absent so `sortino_daily` uses aligned daily risk-free, and they pass a
daily per-period MAR only when the annual config override exists. Focused regression coverage now
checks both default daily risk-free Sortino behavior and annual-MAR-to-daily conversion.

Session 03A and Session 07 completed RM-907 by aligning runtime, config examples, and specs with the
monthly metrics standard. `resolve_returns_frequencies` now forces the main investor return panel,
optimizer inputs, covariance, RC_vol, correlation, mandate checks, and backtest to monthly regardless
of config `returns_frequency`; non-monthly values are disclosure-only via
`configured_returns_frequency` and `frequency_disclosure`. `config.yml` was reset to `monthly`;
focused tests cover resolution, disclosure, and input-assumption export.

Session 08 completed RM-908 (monitoring first-run honesty). `build_monitoring_diff` now treats
`no_prior_snapshot` as narrative-only: empty `profile_changes`, null `prior_analysis_end` and
`input_artifacts.prior_snapshot`, and neutral decision/action change flags when there is no prior
or when the prior shares the same `analysis_end`. Focused tests cover first run, same-end re-run,
and unchanged real diffs when `analysis_end` advances.

Session 09 completed RM-909 (decision package PDF repair). `build_decision_package_pdf_md` in
`pdf_reports.py` emits YAML front matter with a single-line title and date subtitle, client-sanitizes
the summary body, and strips the redundant TXT banner. `build_decision_package_report_md` delegates to
this builder. `Main portfolio_decision_package.pdf` rebuilds successfully with Pandoc/XeLaTeX; focused
tests cover Markdown structure and optional PDF smoke when pandoc is available.

Session 10 completed RM-910 (report scope and noise reduction). `rebuild_portfolio_first_pdfs` and
`rebuild_pdf_reports.py --portfolio-first` rebuild only the decision package and `analysis_subject/`
sidecar PDFs. `run_portfolio_review.py` uses this narrow scope by default; `--legacy-full-pdf` restores
the full legacy variant suite. Focused tests cover workflow argv forwarding and rebuild scope.

Session 11 completed RM-911 (fresh representative run and plan closure). A fresh
`run_report.py --materialize-analysis-subject` run produced `analysis_end: 2026-04-30` subject
artifacts with `regime_portfolio_metrics` and no `regime_portfolio_metrics_error`. Comparison and the
decision package were refreshed via `run_compare_variants.py` and `rebuild_pdf_reports.py
--portfolio-first`; `candidate_comparison.json` reports `analysis_subject_type: current_portfolio`,
`comparison_baseline_candidate_id: analysis_subject`, and marks stale optimizer/policy rows
`unavailable` with explicit reasons. `Main portfolio_decision_package.pdf` and subject PDFs rebuilt
successfully. Verification: `python scripts/verify_docs.py` OK; full pytest `504 passed` with
`--basetemp=tmp/pytest_session11`. Phase 9 stabilization plan is closed; rebuild remaining stale
optimizer candidates with `run_candidate_factory.py --no-skip-existing` when a full refresh is needed.

## Context and Orientation

The main workflow is portfolio-first. The starting portfolio is called `analysis_subject` and is
materialized under `{output_dir_final}/analysis_subject/` before candidate generation. The normal
entrypoint is `run_portfolio_review.py`. The legacy policy optimizer remains callable through older
commands, but it is not the default product starting point.

The 2026-05-19 audit found that the transition exists in code and contract, but the latest run still
has trust gaps:

- `candidate_comparison.json.analysis_setup_summary` can prefer root `Main portfolio/run_metadata.json`
  and falsely describe the run as `universe_baseline` even when the subject row is a real
  `current_portfolio`.
- Candidate factory defaults can skip existing snapshots without checking whether their
  `analysis_end` matches the fresh subject run.
- `returns_frequency: daily` needs an early check to determine whether it affects main portfolio
  metrics or only daily/regime diagnostics.
- Selection and downstream artifacts are weak when `favored_candidate_id` is null because the
  baseline fails mandate risk-reduction gates.
- Legacy policy artifacts still appear in portfolio-first outputs and need clearer optional/legacy
  labeling.
- Regime portfolio metrics fail with `mar_monthly` undefined.
- First-run monitoring can show contradictory deltas despite `no_prior_snapshot`.
- The decision package PDF can fail Pandoc/LaTeX rendering.
- Portfolio-first review currently rebuilds too many legacy PDFs.

## Plan of Work

Session 01 fixes metadata precedence in candidate comparison. The implementation should prefer
`analysis_subject/run_metadata.json` and only use root metadata as a fallback. Regression coverage
must prove that `analysis_setup_summary.analysis_subject_type` is `current_portfolio` when subject
sidecar metadata says so, even if root metadata still says `universe_baseline`.

Session 02 defines and implements candidate freshness. Existing snapshots may be reused only when
their `snapshot_10y.json.analysis_end` matches the review `analysis_end`; stale snapshots must be
rebuilt or marked with an explicit stale warning/status so comparison and selection cannot silently
use them as current evidence.

Session 03 performs the quick methodology check. Inspect the `returns_frequency` config path and
write the result into this plan. This check is now complete: daily frequency changes main portfolio
metrics and legacy optimizer inputs governed by the monthly metrics spec, not only regime/daily
diagnostics.

Session 03A aligns return-frequency methodology before Session 04. The fix must decide and
document the product contract for non-monthly return panels. The conservative expected direction is
to keep main portfolio metrics, covariance, RC_vol, correlation, mandate checks, and optimizer
inputs on the canonical monthly panel unless a future spec explicitly promotes daily/weekly main
metrics; daily/weekly data can remain available for operational diagnostics and explicitly
frequency-disclosed blocks such as VaR/ES or regime analytics. The implementation must update
runtime behavior, config examples, and source-of-truth docs together.

Session 04 improves no-favored and mandate-block outputs after metadata and freshness are trustworthy.
The baseline for trade-off explanations must be `analysis_subject`, and the decision package must
explain why no candidate is favored when mandate gates block selection.

Session 05 cleans the legacy policy boundary. Policy artifacts may remain for compatibility, but
portfolio-first outputs must not present them as the main workflow or starting portfolio.

Session 06 fixes the regime metrics `mar_monthly` failure using canonical MAR behavior. If
`min_acceptable_return` is absent, regime Sortino should use aligned daily risk-free behavior rather
than an undefined monthly scalar.

Session 07 applies any methodology follow-up from Session 03 and ensures docs, config examples, and
runtime behavior agree.

Session 08 fixes first-run monitoring honesty so `no_prior_snapshot` does not include fake deltas or
confusing identical prior/current paths.

Session 09 repairs decision-package PDF generation. This is important for advisor/client output but
comes after core analytical trust.

Session 10 reduces portfolio-first report noise by making legacy full-variant PDF rebuild explicit
rather than default.

Session 11 runs a fresh representative review, verifies outputs and tests, updates project memory,
and closes or defers any remaining issues.

## Concrete Steps

Use a new chat for each session after Session 00. At the beginning of every session:

1. Read `AGENTS.md`, `WORKFLOW.md`, this ExecPlan, and the owning spec for the session.
2. Run `git status --short` and identify unrelated dirty/generated files.
3. Keep changes scoped to the session.
4. Update this ExecPlan `Progress`, `Surprises & Discoveries`, `Decision Log`, and
   `Outcomes & Retrospective` as needed.
5. Run the narrowest reliable tests first, then broaden when the session changes shared behavior.
6. Update source-of-truth docs before finishing.

The starting verification command for documentation-only changes is:

    python scripts/verify_docs.py

Focused code sessions should also run the relevant test files named in the roadmap row.

## Validation and Acceptance

The whole plan is accepted only after a fresh `run_portfolio_review.py` run shows:

- `candidate_comparison.json.analysis_setup_summary` correctly identifies the configured
  `analysis_subject`;
- candidate factory output clearly reports fresh, reused, stale, failed, and skipped candidates;
- selection/no-trade explains mandate blocks without relying on stale comparison evidence;
- methodology docs and runtime behavior do not contradict the metrics standard;
- subject `stress_report.json` includes `regime_portfolio_metrics` without a
  `regime_portfolio_metrics_error`;
- first-run monitoring does not show fake deltas;
- `Main portfolio_decision_package.pdf` builds successfully;
- `python scripts/verify_docs.py` and the relevant focused/broad pytest commands pass.

## Idempotence and Recovery

Generated outputs are evidence only and must not be treated as source unless a session explicitly
targets generated artifacts. Because the current working tree is dirty, every session must review
diffs before editing and avoid reverting unrelated files. If a session fails midway, leave this plan
updated with the exact completed and remaining steps so the next chat can resume safely.

## Artifacts and Notes

Primary audit input:

    docs/audits/2026-05-19_post_portfolio_first_state_audit.md

Primary source-of-truth specs by session:

    docs/specs/candidate_comparison_spec.md
    docs/specs/candidate_factory_spec.md
    docs/specs/selection_engine_spec.md
    docs/specs/tradeoff_and_model_risk_spec.md
    docs/specs/stress_testing_spec.md
    docs/specs/monitoring_spec.md
    docs/specs/decision_package_reporting_spec.md
    docs/specs/metrics_specification.md

## Interfaces and Dependencies

No new public product API is introduced by Session 00. Later sessions may alter existing generated
artifact fields or warnings, but must document those changes in the owning specs and keep backward
compatibility where existing V1 artifacts are consumed by downstream modules.

Revision note, 2026-05-19 / Session 03 RM-903: recorded the quick methodology check result and
inserted Session 03A before Session 04 because `returns_frequency: daily` currently affects main
portfolio metrics and optimizer inputs governed by the monthly metrics standard.

Revision note, 2026-05-19 / Session 04: completed the user-requested selection and mandate
reliability slice only. Session 03A remains open; this revision aligns Selection, Trade-off, and
Decision Package outputs around the portfolio-first baseline and mandate-block explanations.

Revision note, 2026-05-19 / Session 05: completed legacy policy boundary cleanup. Portfolio-first
outputs now keep legacy policy/current-vs-policy artifacts as compatibility metadata only, while the
main comparison, Health Score priority, and summary story center `analysis_subject`.

Revision note, 2026-05-19 / Session 06: completed the regime metrics MAR fix. The daily regime
metrics path now relies on aligned daily risk-free by default and only uses a configured MAR after
annual-to-daily conversion.

Revision note, 2026-05-19 / Session 07 (RM-907): completed methodology consistency follow-up and
Session 03A alignment. Main portfolio metrics and optimizer paths always use monthly returns; config
`returns_frequency` weekly/daily is disclosure-only. Updated metrics, input-assumptions, and stress
specs, config examples, and focused tests.

Revision note, 2026-05-19 / Session 08 (RM-908): completed monitoring first-run honesty.
`no_prior_snapshot` diffs omit profile/decision deltas, null prior metadata, and narrative-only
summaries; same-`analysis_end` re-runs keep warning `prior_same_analysis_end_ignored`.

Revision note, 2026-05-19 / Session 09 (RM-909): completed decision package PDF repair. PDF Markdown
uses YAML front matter instead of a long H1 with embedded analysis-end dates; `KI-2026-05-18-001`
removed after verification.

Revision note, 2026-05-19 / Session 10 (RM-910): portfolio-first review defaults to narrow PDF rebuild
(`--portfolio-first`); full legacy variant PDFs require `--legacy-full-pdf`.

Revision note, 2026-05-19 / Session 11 (RM-911): closed Phase 9 stabilization. Representative
verification used fresh subject materialization, comparison/PDF refresh, `504` pytest passes, and docs
verify. Remaining stale optimizer candidates are operational rebuild follow-up, not open plan items.
