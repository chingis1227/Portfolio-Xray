# Post-Portfolio-First State Audit

Date: 2026-05-19

Scope: assess the repository **after** the completed portfolio-first transition
([Portfolio-First Transition Plan](../exec_plans/2026-05-18_portfolio_first_transition_plan.md))
and prior MVP stabilization work. This audit does **not** repeat the 2026-05-17 audits; it records
where the system stands **now** given the latest representative run, current artifacts, config, code,
`SPEC.md`, and workflow documentation.

Primary workflow under review:

```text
analysis_subject
-> Portfolio X-Ray
-> stress / factor / macro diagnostics
-> candidate generation
-> candidate comparison
-> robustness / health scoring
-> selection / no-trade decision
-> action plan
-> monitoring / decision journal
-> report / PDF package
```

Generated outputs are evidence only. They do not override canonical specs or code.

## Executive Conclusion

The portfolio-first transition is **implemented in code and contract**: `run_portfolio_review.py`
materializes `analysis_subject` before candidates, does not call `run_optimization.py` by default,
and the V1 decision JSON chain is produced end-to-end when `run_candidate_factory.py --then-compare`
runs successfully.

The latest representative run (`portfolio_review_stdout.log` / `portfolio_review_stderr.log`,
`analysis_end` 2026-05-15) analyzed a **real `current_portfolio`** from `config.analysis_subject.weights`,
not a universe equal-weight placeholder, in `Main portfolio/analysis_subject/`.

The product is **not yet a reliable advisor-facing MVP**. It remains a **strong diagnostic prototype**
with trust gaps: stale candidate snapshots (15/16 `skipped_existing`), contradictory comparison
metadata (summary says `universe_baseline` while the subject row is `current_portfolio`), broken
regime portfolio metrics (`mar_monthly` NameError), a failed decision-package PDF build, and legacy
policy artifacts still visible in comparison and PDF rebuild scope.

**Recommended next work:** stabilization ExecPlan or roadmap tranche focused on P0 items below
(freshness contract, metadata precedence, `mar_monthly`, decision-package PDF). Defer UI until core
pipeline trust is fixed.

**Verdict**

| Question | Answer |
| --- | --- |
| Reliable MVP or prototype? | **Partially working technical prototype** with strong diagnostic core. |
| UI now or stabilize core first? | **Stabilize core first.** |
| Is candidate/optimization layer genuinely useful yet? | **Potentially yes; weak in the latest run** due to stale candidates and mandate block on the baseline. |
| Highest-leverage next step | **P0-2 + P0-4:** consistent baseline metadata + fresh candidate refresh on the same `analysis_end`. |

## Evidence Reviewed

- Config: root `config.yml` (`analysis_subject.type: current_portfolio`, explicit weights).
- Latest run logs: `portfolio_review_stdout.log`, `portfolio_review_stderr.log`.
- Subject diagnostics: `Main portfolio/analysis_subject/` (snapshots, `stress_report.json`,
  `portfolio_xray.json`, commentary, rolling factor betas).
- Decision artifacts: `Main portfolio/candidate_factory_run.json`, `candidate_comparison.json`,
  `selection_decision.json`, `decision_package_summary.json`, `action_plan.json`, monitoring/journal
  paths referenced in factory run summary.
- Legacy/main folder metadata: `Main portfolio/run_metadata.json`, root `Main portfolio/portfolio_xray.json`.
- Source-of-truth: `SPEC.md`, [portfolio_review_workflow_spec.md](../specs/portfolio_review_workflow_spec.md),
  closed [Portfolio-First Transition Plan](../exec_plans/2026-05-18_portfolio_first_transition_plan.md).
- Known issue register: `KNOWN_ISSUES.md` (KI-2026-05-18-001 decision-package PDF).

## Verification Performed During Audit

- Read-only inspection of artifacts and implementation entrypoints (`run_portfolio_review.py`,
  `src/portfolio_review_workflow.py`, `src/candidate_comparison.py`, `src/selection_engine.py`,
  `run_report.py` regime path).
- Focused pytest (audit session): `tests/test_portfolio_review_workflow.py`,
  `tests/test_selection_engine.py` — **18 passed**.
- Full pytest suite not re-run as part of this audit file (last recorded full pass: **486 passed**
  on 2026-05-18 at portfolio-first transition closure).

## Key Questions (Answers)

| # | Question | Answer |
| --- | --- | --- |
| 1 | Real `current_portfolio` or placeholder? | **Real current portfolio** in subject sidecar; placeholder **not** used for diagnostics. |
| 2 | Clean E2E without manual follow-up? | **Partially** — CLI exits 0; decision PDF fails; regime metrics error; most candidates stale-skipped. |
| 3 | Partial factory failures handled? | **Yes** — continues on skip/failure unless `--fail-fast`. |
| 4 | Candidates fresh / stale / failed? | **1 succeeded**, **15 skipped_existing**, **0 failed** (`risk_budget_by_asset_class` only refreshed). |
| 5 | Optimization improving decisions? | **Weak in this run** — ranking exists but mandate blocks favored selection; stale alternatives. |
| 6 | Why no favored candidate? | **`mandate_risk_reduction`** — baseline fails `target_vol` and `max_dd` mandate checks. |
| 7 | Weak outputs when no favored? | **Yes** — trade-off pairs empty, assumption sensitivity `not_evaluated`, favored regret unavailable. |
| 8 | Legacy leaking into portfolio-first? | **Yes** — see findings PPF-002, PPF-005, PPF-006. |
| 9 | Stress / factor / macro reliable? | **Factor/stress strong** on subject; **regime portfolio metrics broken**. |
| 10 | TXT/JSON/HTML/CSV/PDF useful? | **JSON/TXT strong**; **decision PDF missing**; comparison top summary **misleading**. |
| 11 | What could mislead advisors? | Stale candidates treated as current; summary says universe baseline; policy row beside user current. |

## Workflow Block Assessment

### `analysis_subject` / input

| Status | Notes |
| --- | --- |
| Working well | Config `current_portfolio` with explicit weights; materialization to `Main portfolio/analysis_subject/`. |
| Working but weak | Sidecar `resolved_config` still carries compat `analysis_mode: optimize_from_universe`. |
| Legacy / stale | `Main portfolio/run_metadata.json` describes subject as `universe_baseline` / equal-weight. |
| Future | Saved analysis workspaces / UI. |

### Portfolio X-Ray / metrics

| Status | Notes |
| --- | --- |
| Working well | `analysis_subject/portfolio_xray.json` with `user_current_portfolio`; snapshots 3Y/5Y/10Y. |
| Methodological risk | `returns_frequency: daily` in config vs monthly canon in metrics spec. |
| Legacy | Root `Main portfolio/portfolio_xray.json` — policy/universe metadata. |

### Stress / factor / macro

| Status | Notes |
| --- | --- |
| Working well | Subject `stress_report.json`: scenarios, HAC inference, rolling 3Y/5Y/10Y betas; `DIAG_ATTENTION` on recession_severe loss. |
| Broken | `regime_portfolio_metrics_error: name 'mar_monthly' is not defined` (log + stress JSON). |

### Candidate factory

| Status | Notes |
| --- | --- |
| Working well | No legacy policy optimization in default profile; resilient skip/continue. |
| Working but weak | Latest run: 15/16 `skipped_existing` — comparison mostly uses old snapshots. |

### Comparison / scoring / selection

| Status | Notes |
| --- | --- |
| Working well | Baseline row `analysis_subject` with correct metrics; full decision chain generated via `--then-compare`. |
| Broken / misleading | `analysis_setup_summary` at top of `candidate_comparison.json` reads legacy Main `run_metadata` first → false `universe_baseline` label. |
| Working as designed | `mandate_risk_reduction`, `favored_candidate_id: null` when baseline fails vol/DD gates. |

### Action / monitoring / journal / reports

| Status | Notes |
| --- | --- |
| Working well | `action_plan.json` consistent with no-trade under mandate block; journal/history paths written. |
| Working but weak | Monitoring `no_prior_snapshot` yet shows `profile_changes` deltas; prior/current snapshot paths identical with warning. |
| Broken | `Main portfolio_decision_package.pdf` — Pandoc/LaTeX failure (KI-2026-05-18-001). |
| Legacy noise | `rebuild_pdf_reports.py` rebuilds many non-subject variant PDFs each review run. |

## Findings Register

### PPF-001: Regime portfolio metrics fail (`mar_monthly` undefined)

- **Severity:** high
- **Area:** factor_macro / stress
- **Evidence:** `portfolio_review_stderr.log` WARNING; `regime_portfolio_metrics_error` in
  `Main portfolio/analysis_subject/stress_report.json` and other variant stress reports.
- **Risk:** Macro/regime section absent or empty in stress outputs and commentary.
- **Likely fix location:** `run_report.py` (regime path references `mar_monthly` without assignment).
- **Remove when:** Subject stress report includes `regime_portfolio_metrics` without error field.

### PPF-002: Comparison `analysis_setup_summary` contradicts actual subject

- **Severity:** critical (trust)
- **Area:** reports / architecture
- **Evidence:** `candidate_comparison.json` header: `universe_baseline`, `Universe Baseline`,
  `system.equal_weight_universe_baseline`; subject row: `current_portfolio`,
  `config.analysis_subject.weights`. Root cause: `_analysis_setup_summary_from_main` in
  `src/candidate_comparison.py` prefers `Main portfolio/run_metadata.json` before
  `analysis_subject/run_metadata.json`.
- **Risk:** Advisor or UI reads summary and believes the run analyzed equal-weight universe, not
  the client's current allocation.
- **Remove when:** Comparison summary matches subject sidecar and config for `current_portfolio`.

### PPF-003: Decision package PDF build fails

- **Severity:** medium (tracked)
- **Area:** reports
- **Evidence:** `portfolio_review_stderr.log` Pandoc error near `2026-05-15}`; no
  `pdf files/Main portfolio_decision_package.pdf`. See `KNOWN_ISSUES.md` KI-2026-05-18-001.
- **Remove when:** PDF rebuild succeeds without LaTeX errors.

### PPF-004: Candidate freshness not guaranteed on portfolio review

- **Severity:** high
- **Area:** architecture / candidate_factory
- **Evidence:** `candidate_factory_run.json` summary: `succeeded=1`, `skipped_existing=15` on
  2026-05-18 run; default `skip_existing=true` in factory options.
- **Risk:** Selection, robustness, and Pareto compare stale alternatives to a fresh subject.
- **Remove when:** Documented contract plus optional stale warning or `--no-skip-existing` default
  for “full refresh” review runs.

### PPF-005: Legacy policy artifacts visible in portfolio-first path

- **Severity:** medium
- **Area:** architecture
- **Evidence:** `policy` row in `candidate_comparison.json`; `current_vs_policy_status.json`
  (`workflow_profile: policy_only`); decision package summary “Legacy current-vs-policy workflow”;
  health score `display_priority: ["current", "policy"]`.
- **Risk:** Users continue to interpret policy optimizer output as the primary portfolio.
- **Remove when:** Portfolio-first compare and summaries label policy as optional legacy reference only.

### PPF-006: Downstream artifacts weak when `mandate_risk_reduction`

- **Severity:** medium
- **Area:** selection / tradeoff
- **Evidence:** `tradeoff_explanation.json` empty pairs, `baseline_candidate_id: "current"` (not
  `analysis_subject`); `assumption_sensitivity.json` `not_evaluated`; `regret_analysis` favored
  reference `not_available`.
- **Risk:** Decision package feels “empty” even when composite ranking shows stronger candidates.
- **Remove when:** Explicit narrative explains top candidate vs mandate block; trade-off baseline
  aligned to `analysis_subject`.

### PPF-007: Monitoring first-run shows contradictory deltas

- **Severity:** low-medium
- **Area:** monitoring
- **Evidence:** `monitoring_diff.json`: `diff_status: no_prior_snapshot` but non-zero
  `profile_changes`; warning `prior_same_analysis_end_ignored`; prior and current snapshot paths
  both `monitoring/latest/analysis_snapshot.json`.
- **Remove when:** First run shows narrative only or empty deltas without prior history.

## Classification Summary

| Bucket | Items |
| --- | --- |
| **Working well** | Portfolio-first orchestrator; subject materialization; decision JSON chain; mandate gate blocking favored selection; stress/factor depth on subject; factory resilience. |
| **Working but weak** | Stale candidates; downstream when no favored; monitoring first run; PDF volume vs signal. |
| **Broken / unstable** | `mar_monthly` regime path; decision-package PDF; comparison summary metadata. |
| **Methodological risks** | `returns_frequency: daily`; stale cross-candidate comparison; extreme factor betas interpretation. |
| **Legacy / stale** | Main `run_metadata`, root `portfolio_xray`, policy row, current-vs-policy artifact, trade-off `current` baseline, full variant PDF rebuild. |
| **Future / target** | UI; user-maintained journal; optional policy-as-candidate only. |

## Prioritized Fix Plan

### P0 — blockers (trustworthy product run)

| ID | Fix | Why | System area | Files / specs | Verify |
| --- | --- | --- | --- | --- | --- |
| P0-1 | Define/assign `mar_monthly` before regime metrics | Restore macro/regime block | `run_report.py` | stress spec (regime) | No `regime_portfolio_metrics_error` in subject `stress_report.json` |
| P0-2 | Prefer subject sidecar + config for `analysis_setup_summary` | Stop false universe-baseline label | `src/candidate_comparison.py` | portfolio_review_workflow_spec | Comparison header matches `current_portfolio` |
| P0-3 | Harden decision-package Markdown for LaTeX dates | Restore client PDF | `src/decision_package_reporting.py`, `src/pdf_reports.py` | KI-2026-05-18-001 | `Main portfolio_decision_package.pdf` builds |
| P0-4 | Freshness contract for candidates (`skip_existing` / `analysis_end` stamp) | Trustworthy comparison | `src/candidate_factory.py`, workflow spec | candidate_factory_spec | Full refresh documented; stale warning in factory run summary |

### P1 — reliability and decision quality

| ID | Fix | Why | Files / specs | Verify |
| --- | --- | --- | --- | --- |
| P1-1 | Trade-off baseline = `analysis_subject` | Consistency with selection | `src/tradeoff_and_model_risk.py` | `tradeoff_explanation.json` baseline id |
| P1-2 | Health `display_priority` starts with `analysis_subject` | Portfolio-first UX | `src/portfolio_health_score.py` | JSON/TXT priority order |
| P1-3 | Policy row optional or legacy-labeled in portfolio-first compare | Reduce policy-first confusion | `src/candidate_comparison.py` | Comparison docs / flags |
| P1-4 | Monitoring: no fake deltas on first snapshot | Honest “What Changed” | `src/monitoring.py` | `monitoring_diff.json` first run |
| P1-5 | Rejected-candidate copy when `favored=null` | Clear mandate-block wording | `src/selection_engine.py` | `selection_decision.txt` |
| P1-6 | Align `returns_frequency` with metrics spec or warn | Methodology drift | `config.yml`, validation | docs + config example |

### P2 — polish / UX / scale

| ID | Fix | Why |
| --- | --- | --- |
| P2-1 | Portfolio-first PDF subset in rebuild | Less noise per review |
| P2-2 | Decision package summary without legacy policy paragraph | Cleaner advisor read |
| P2-3 | Narrative when `mandate_risk_reduction` but top candidate ranks high | Actionable insight |
| P2-4 | Optional canonical root metadata on subject-only runs | Less Main-folder confusion |

## Suggested Follow-Up

No ExecPlan was created automatically from this audit. Recommended:

1. Add a short stabilization ExecPlan under `docs/exec_plans/` scoped to P0-1–P0-4, or map P0 items
   to `docs/ROADMAP.md` with IDs.
2. Link active known issues (`KI-2026-05-18-001`) to P0-3.
3. After P0 fixes, re-run: `python run_portfolio_review.py --no-skip-existing` (or documented full
   refresh flag) and regenerate decision PDF.

## Related Documents

- [Portfolio-First Transition Plan](../exec_plans/2026-05-18_portfolio_first_transition_plan.md) (completed)
- [Portfolio Review Workflow Specification](../specs/portfolio_review_workflow_spec.md)
- [KNOWN_ISSUES.md](../../KNOWN_ISSUES.md)
- [Audit Register](README.md)
