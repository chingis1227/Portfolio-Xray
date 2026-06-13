# Project Development Session Plan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.
Maintenance follows [PLANS.md](../../PLANS.md) at the repository root.

## Purpose / Big Picture

This plan turns the current audit, product concept, documentation set, and implemented codebase
into a practical development sequence. After following it, the project should move from a strong
report-first analytical system toward a decision-support product in a controlled order: first clean
stale source-of-truth issues, then standardize candidate comparison, then add scoring, then add
selection, no-trade, action, monitoring, and journal workflows.

After Sessions 01–20 are done, **Phase 6 (Post-plan closure)** records four mandatory follow-ups:
re-audit vs concept and choose the next stage; improve weak blocks in separate scoped sessions; fix
remaining mojibake/broken symbols; review Main vs robust optimizer inputs against the concept (decide
change vs document-as-is). Phase 6 starts only when the user explicitly requests it.

The plan is intentionally split into separate future sessions. A "session" means a fresh Codex chat
or work thread with a narrow goal, its own context refresh, its own verification, and a concise final
report. Use a new session for every session item below so the chat context does not become overloaded
or mix decisions from unrelated areas.

## Progress

- [x] (2026-05-17) Read `WORKFLOW.md`, `RULES.md`, and `PLANS.md` to confirm planning and source-of-truth rules.
- [x] (2026-05-17) Reviewed `docs/audits/2026-05-17_full_project_system_audit.md`, `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`, `SPEC.md`, `PRODUCT.md`, `ARCHITECTURE.md`, `OUTPUTS.md`, `TESTING.md`, `KNOWN_ISSUES.md`, `DECISIONS.md`, and the candidate/reporting specs.
- [x] (2026-05-17) Classified the immediate audit fixes and the larger product-development path.
- [x] (2026-05-17) Assessed whether the current documentation is enough to restart work in fresh sessions.
- [x] (2026-05-17) Created this sessionized ExecPlan as the handoff document for future development sessions.
- [x] (2026-05-17) Recorded the operating agreement that Codex should guide the user through the plan, preserve session state in this ExecPlan, and resume from the last recorded point when a new chat starts.
- [x] (2026-05-17) Session 01 completed: created `docs/ROADMAP.md`, registered unresolved audit issues in `KNOWN_ISSUES.md`, fixed the stale `DECISIONS.md` intro, recorded the roadmap decision, linked the roadmap from `README.md`, updated `CHANGELOG.md`, and ran documentation verification searches.
- [x] (2026-05-17) Session 02 completed: rewrote the stale stress covariance section so
  `taxonomy_blend_v1` is the current default, documented `uniform_legacy` as legacy-only, removed the
  resolved known issue, marked roadmap `RM-001` done, ran the focused stress covariance taxonomy test
  (`13 passed`), and confirmed legacy scalar references are only in legacy context.
- [x] (2026-05-17) Session 03 completed: removed the editable `rc_asset_cap_pct` field from
  `config_ui/templates/config_form.html`, added focused config UI regression tests, removed the
  resolved known issue, marked roadmap `RM-002` done, updated `CHANGELOG.md`, and verified no editable
  ignored RC cap UI remains.
- [x] (2026-05-17) Session 04 completed: added explicit `analysis_mode` controls to
  `config_ui`, added `current_weights` entry for `analyze_current_weights`, stopped loading
  generated `portfolio_weights.yml` into editable fields, showed generated policy weights as
  read-only output, removed the resolved known issue, marked roadmap `RM-003` done, updated
  `CHANGELOG.md`, and ran focused config/input tests (`16 passed`).
- [x] (2026-05-17) Session 05 completed: corrected `src/rebalance.py` docstrings so `threshold_pct`
  gates on max absolute per-ticker drift only (not turnover), added `tests/test_rebalance_threshold.py`,
  removed the resolved known issue, marked roadmap `RM-005` done, updated `CHANGELOG.md`, and ran
  focused tests (`2 passed`).
- [x] (2026-05-17) Session 06 completed: rewrote `docs/specs/production_workflow.md` in clean English,
  normalized mojibake in `stress_testing_spec.md`, `metrics_specification.md`, and
  `view_after_optimization_spec.md`, removed the resolved known issue, marked roadmap `RM-006` done,
  updated `CHANGELOG.md`, and confirmed targeted mojibake scans pass on `docs/specs/*.md`.
- [x] (2026-05-17) Session 07 completed: added `src/docs_verify.py`, `scripts/verify_docs.py`, and
  `tests/test_docs_links.py` for source Markdown link checks, forbidden stale canonical paths, and
  removed config UI field guards; fixed a stale exec-plan link in `stress_testing_spec.md`; updated
  `TESTING.md`, removed the resolved known issue, marked roadmap `RM-007` done, updated `CHANGELOG.md`,
  and ran `python scripts/verify_docs.py` plus `tests/test_docs_links.py` (`6 passed`).
- [x] (2026-05-17) Session 08 completed: created `docs/specs/candidate_comparison_spec.md` with
  `candidate_comparison_v1`, full candidate registry (`unavailable` when artifacts missing),
  mandatory `current` row when user-current report is materialized, canonical path under
  `output_dir_final`, legacy artifact notes, and cross-links in `OUTPUTS.md`, `SPEC.md`,
  `docs/specs/README.md`, reporting/candidate specs; marked roadmap `RM-100` done; ran docs verify.
- [x] (2026-05-17) Session 09 completed: implemented `src/candidate_comparison.py` and wired
  `run_compare_variants.py` to emit `candidate_comparison.json` (full registry, diagnostic-only),
  optional `candidate_comparison.txt`, and legacy `portfolio_comparison.*` for compatibility.
  Added `tests/test_candidate_comparison.py`.
- [x] (2026-05-17) Session 10 completed: created `docs/specs/robustness_scorecard_spec.md` with
  `robustness_scorecard_v1`, six reviewable-weight components, relative within-run normalization,
  mandate absolute checks in `mandate_fit`, RC diversification via comparison v1.1 prerequisite,
  10y primary window and stress scenario ids per stress spec, JSON/TXT contracts, ranking and
  explanation templates; extended `candidate_comparison_spec.md` with `diversification` block;
  updated `OUTPUTS.md`, `SPEC.md`, `docs/specs/README.md`, `docs/ROADMAP.md` (RM-200 done);
  ran `python scripts/verify_docs.py`.
- [x] (2026-05-17) Session 11 completed: implemented `src/robustness_scorecard.py` (`robustness_scorecard_v1` JSON/TXT),
  comparison `diversification` block from `snapshot_10y` RC_asset, wired export via `write_candidate_comparison_outputs` /
  `run_compare_variants.py`, added `tests/test_robustness_scorecard.py`, updated `SPEC.md`, `OUTPUTS.md`, `CHANGELOG.md`,
  `docs/ROADMAP.md` (RM-201 done); pytest on scorecard and comparison tests passed.
- [x] (2026-05-17) Session 12 completed: created `docs/specs/portfolio_health_score_spec.md` with
  `portfolio_health_score_v1`, ten reviewable-weight components (including optional `resilience_reference`
  from robustness scorecard), within-run + absolute normalization, comparison `weight_concentration`
  prerequisite, cross-links in `OUTPUTS.md`, `SPEC.md`, `docs/specs/README.md`, `candidate_comparison_spec.md`,
  `robustness_scorecard_spec.md`, `PRODUCT.md`; marked roadmap `RM-210` done; ran `python scripts/verify_docs.py`.
- [x] (2026-05-17) Session 13 completed: implemented `src/portfolio_health_score.py` (`portfolio_health_score_v1` JSON/TXT),
  comparison `weight_concentration` from `snapshot_10y.final_weights_total`, wired export via `write_candidate_comparison_outputs` /
  `run_compare_variants.py`, added `tests/test_portfolio_health_score.py`, updated `SPEC.md`, `OUTPUTS.md`, `CHANGELOG.md`,
  `docs/ROADMAP.md` (RM-211 done); pytest on health, scorecard, and comparison tests passed.
- [x] (2026-05-17) Session 14 completed: created `docs/specs/selection_engine_spec.md` with `selection_decision_v1`, five decision outcomes, composite selection (health + robustness + mandate), No-Trade materiality thresholds, neutral decision-support boundaries; updated `SPEC.md`, `OUTPUTS.md`, `docs/specs/README.md`, score/comparison cross-links, `PRODUCT.md`, `DECISIONS.md` (DEC-2026-05-17-006), `CHANGELOG.md`, `docs/ROADMAP.md` (RM-300 done); ran `python scripts/verify_docs.py`.
- [x] (2026-05-17) Session 15 completed: implemented `src/selection_engine.py` (`selection_decision_v1` JSON/TXT),
  composite selection from health and robustness scores, No-Trade materiality vs current, five decision outcomes;
  wired export via `write_candidate_comparison_outputs` / `run_compare_variants.py`, added `tests/test_selection_engine.py`,
  updated `SPEC.md`, `OUTPUTS.md`, `CHANGELOG.md`, `docs/ROADMAP.md` (RM-301 done), `src/input_assumptions.py`;
  pytest on selection, health, scorecard, and comparison tests passed.
- [x] (2026-05-17) Session 16 completed: created `docs/specs/action_engine_spec.md` (`action_plan_v1`, 10 bps on turnover half-sum),
  implemented `src/action_engine.py` and `tests/test_action_engine.py`, always emit `action_plan.json` / `.txt` after selection
  (empty `trades` with reason on No-Trade and other non-trade outcomes), wired via `write_candidate_comparison_outputs`;
  updated `SPEC.md`, `OUTPUTS.md`, `CHANGELOG.md`, `docs/ROADMAP.md` (RM-310 done); pytest on action, selection, and comparison tests passed.
- [x] (2026-05-17) Session 17 completed: created `docs/specs/monitoring_spec.md` (`analysis_snapshot_v1`, `monitoring_diff_v1`),
  storage under `{output_dir_final}/monitoring/` (latest + history), current/policy profiles, What Changed fields and diff statuses;
  updated `OUTPUTS.md`, `SPEC.md`, `docs/specs/README.md`, `PRODUCT.md`, `docs/ROADMAP.md` (RM-400 done).
- [x] (2026-05-17) Session 18 completed: implemented `src/monitoring.py` and `tests/test_monitoring.py`, wired export via
  `write_candidate_comparison_outputs`; emits `monitoring_diff.json` / `.txt` and snapshot files; `docs/ROADMAP.md` (RM-401 done);
  pytest on monitoring tests passed.
- [x] (2026-05-17) Session 19 completed: created `docs/specs/decision_journal_spec.md` (`decision_journal_v1`, generated-only, `journal/latest/` + `history/`, pipeline after monitoring), updated `OUTPUTS.md`, `SPEC.md`, `PRODUCT.md`, `docs/specs/README.md`, `docs/ROADMAP.md` (RM-410 done), `CHANGELOG.md`; ran `python scripts/verify_docs.py`.
- [x] (2026-05-17) Session 20 completed: implemented `src/decision_journal.py` and `tests/test_decision_journal.py`, wired export via `write_candidate_comparison_outputs` after monitoring (`decision_journal.json` / `.txt`, `journal/latest/` and `history/`); updated `SPEC.md`, `docs/ROADMAP.md` (RM-411 done), `CHANGELOG.md`; pytest on journal and related tests passed.
- [x] (2026-05-17) Phase 6 post-closure triage completed as a new deep audit:
  `docs/audits/2026-05-17_post_session_deep_system_audit.md`; updated `docs/ROADMAP.md`,
  `DECISIONS.md`, `KNOWN_ISSUES.md`, and `CHANGELOG.md` with next-stage priorities and tracked
  follow-up issues. Implementation follow-ups remain separate scoped sessions.
- [ ] Session 21: Deferred/later - decide the first real product UI surface only after core analytics,
  comparison, scoring, selection, monitoring, and journal artifacts are stable.
- [ ] Session 22: Deferred/later - implement the first UI slice only after Session 21 is explicitly
  reactivated.

**Post-plan closure (mandatory after Sessions 01–20 are complete; start only when the user reactivates
Phase 6 or explicitly asks to run post-closure work — not automatically after Session 20):**

- [x] Post-closure 1: New full project audit; compare implemented system vs
  `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md` and `docs/audits/2026-05-17_*`; decide the next development
  stage and record it in `docs/ROADMAP.md` / `DECISIONS.md`.
- [x] Post-closure 2: Identify weak or incomplete product blocks; prioritize and improve them in
  separate scoped sessions (one block or workstream per session; do not mix unrelated block fixes).
- [x] Post-closure 3: Mojibake and broken-symbol sweep beyond Session 06 (source docs, specs,
  generated commentary, PDF-facing Markdown, config examples, and other user-visible text); fix or
  track in `KNOWN_ISSUES.md`.
- [x] Post-closure 4: Review what currently feeds **Main** optimization (`run_optimization.py` /
  `docs/specs/portfolio_construction_policy.md`) vs **robust** paths (`run_robust_mean_variance_constrained.py`,
  `run_robust_scenario_optimization.py`, related specs); compare inputs, objectives, and constraints
  to the product concept; decide per path whether to change, document-as-is, or defer — record in
  `DECISIONS.md` without silent behavior changes.

## Surprises & Discoveries

- Observation: The repository already has a strong analytical and reporting base, including
  optimization, reports, Input and Assumptions V1, Portfolio X-Ray, stress, factor, macro, scenario,
  candidate, robust, and partial UI utilities.
  Evidence: `SPEC.md`, `ARCHITECTURE.md`, `OUTPUTS.md`, and the 2026-05-17 audit all show these
  areas as implemented or largely implemented.

- Observation: The main missing layer is not another analytics module. The missing layer is an
  ordered execution spine from product concept to canonical artifacts, scores, selection, action,
  monitoring, and decision records.
  Evidence: `docs/audits/2026-05-17_full_project_system_audit.md` identifies `AUD-001` and recommends
  a roadmap before new major analytics.

- Observation: Current documentation is mostly sufficient for fresh sessions about current behavior,
  but not yet sufficient for future product modules that lack owning specs.
  Evidence: `SPEC.md` marks Selection Engine, Portfolio Health Score, Monitoring, and Decision Journal
  as target/TBD; no canonical specs currently define their formulas, thresholds, artifacts, or tests.

- Observation: Before Session 01, `KNOWN_ISSUES.md` was not accurate as a risk register because it said no active
  issues are recorded while the audit lists unresolved issues.
  Evidence: The pre-Session 01 `KNOWN_ISSUES.md` active section and audit items `AUD-002` through `AUD-012`.

- Observation: The working tree was already dirty before this plan was created.
  Evidence: `git status --short` showed many modified and untracked files, including prior docs, source,
  tests, generated outputs, and audit files. Future sessions must avoid reverting unrelated changes.

- Observation: Session 01 resolved the missing roadmap and empty issue-register gaps without changing
  runtime behavior.
  Evidence: `docs/ROADMAP.md` now maps all `AUD-001` through `AUD-012` findings; `KNOWN_ISSUES.md`
  initially tracked unresolved audit issues that were not fixed in Session 01. Session 02 later removed
  the resolved stress covariance issue.

- Observation: Session 02 confirmed the runtime and tests already matched the intended current default.
  Evidence: `src/stress.py` defaults `run_stress` to `stress_cov_method = "taxonomy_blend_v1"` and calls
  `_stress_covariance` only when `stress_cov_method == "uniform_legacy"`; the focused test
  `tests/test_stress_covariance_taxonomy.py -q` passed with 13 tests.

- Observation: Session 03 confirmed the stale RC cap problem was UI-only.
  Evidence: `config_ui/templates/config_form.html` rendered `name="rc_asset_cap_pct"`, while
  `config_ui/app.py` did not parse or write that field and the feasibility/policy specs already state
  that RC_vol is diagnostic-only.

- Observation: Session 04 confirmed the generated-weight ambiguity was isolated to `config_ui`.
  Evidence: `src/config.py` still intentionally loads generated `portfolio_weights.yml` from
  `output_dir_final` for report compatibility, while `config_ui/app.py` no longer merges generated
  weights into editable form values and focused config/input tests passed.

- Observation: Session 05 confirmed the rebalance threshold mismatch was documentation-only.
  Evidence: `compute_trades` already gated on `max_abs_delta_pct`; only `rebalance_needed` and module
  docstrings overstated turnover. `tests/test_rebalance_threshold.py` shows high half-sum turnover
  with sub-threshold max per-ticker drift does not trigger rebalance.

## Decision Log

- Decision: Split future work into separate sessions by product or technical boundary.
  Rationale: The user explicitly wants separate sessions so context stays small. The project also has
  enough independent workstreams that each should be verified and documented on its own.
  Date/Author: 2026-05-17 / Codex

- Decision: Prioritize source-of-truth cleanup before implementing scores or recommendations.
  Rationale: The audit found stale docs and UI surfaces that can mislead future implementation. Scoring
  and selection must not build on ambiguous contracts.
  Date/Author: 2026-05-17 / Codex

- Decision: Standardize candidate comparison before Robustness Scorecard, Health Score, Selection
  Engine, or No-Trade Recommendation.
  Rationale: Scores and recommendations need stable, comparable candidate inputs. Ad hoc comparison
  artifacts are not a safe base for decision logic.
  Date/Author: 2026-05-17 / Codex

- Decision: Treat `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md` as product direction only.
  Rationale: The concept document itself, `RULES.md`, and `SPEC.md` all say product concepts do not
  override current formulas, scenarios, optimizer policy, data rules, output contracts, or code behavior.
  Date/Author: 2026-05-17 / Codex

- Decision: Each future session must begin by reading a common context bundle plus session-specific
  docs.
  Rationale: Fresh sessions need enough context to work safely without relying on chat memory.
  Date/Author: 2026-05-17 / Codex

- Decision: Codex should actively guide the user through the session plan rather than requiring the
  user to paste kickoff text manually.
  Rationale: The user wants to be able to ask "what are we working on now" or "continue the plan" in a
  new chat. Therefore the durable state must live in this ExecPlan: current session, partial progress,
  completed work, remaining work, blockers, and the recommended next action.
  Date/Author: 2026-05-17 / User and Codex

- Decision: Use `docs/ROADMAP.md` as the durable roadmap filename for Session 01.
  Rationale: The session prompt allowed either `docs/ROADMAP.md` or `docs/product_backlog.md` and said
  to default to `docs/ROADMAP.md` if the user did not choose. The user asked to continue the plan
  without choosing a filename.
  Date/Author: 2026-05-17 / Codex

- Decision: Treat Session 02 as a documentation/source-of-truth cleanup, not a runtime behavior change.
  Rationale: Code and tests already use `taxonomy_blend_v1` as the normal path and retain
  `uniform_legacy` only as an explicit compatibility mode, so the safe fix was to align the stale spec
  wording to existing behavior.
  Date/Author: 2026-05-17 / Codex

- Decision: Remove the stale config UI `rc_asset_cap_pct` field entirely instead of keeping it as
  read-only diagnostic context.
  Rationale: Current policy makes RC_vol diagnostic-only and `config_ui/app.py` does not parse or write
  `rc_asset_cap_pct`; a read-only remnant would add clutter without clarifying an active setting. The
  Session 03 default also says to remove the field if the user does not choose.
  Date/Author: 2026-05-17 / Codex

- Decision: Defer product UI and design work until later.
  Rationale: The user wants the current plan execution to focus on source-of-truth cleanup, canonical
  artifacts, comparison, scoring, selection, action, monitoring, and journal work. Sessions 21 and 22
  remain documented as future work, but they should not be treated as near-term implementation scope or
  started automatically after Session 20 unless the user explicitly reactivates UI/design work.
  Date/Author: 2026-05-17 / User and Codex

- Decision: After Sessions 01–20 are complete, run **Phase 6 (Post-plan closure)** as four separate
  follow-ups: (1) new audit vs product concept and next-stage decision, (2) block-by-block improvement
  backlog executed in scoped sessions, (3) extended mojibake/symbol integrity fixes, (4) Main vs robust
  optimizer input/objective review vs concept with explicit change/no-change decisions. Phase 6 does not
  start automatically when Session 20 ends; the user must explicitly request post-closure work or a
  numbered Post-closure item. Sessions 21–22 remain optional and independent of Phase 6.
  Rationale: The user asked to record mandatory follow-up work after the session plan is implemented,
  without folding it into the current session sequence or implying automatic execution.
  Date/Author: 2026-05-17 / User and Codex

- Decision: V1 candidate comparison uses the full candidate registry, includes `current` when
  user-current artifacts exist, and writes `candidate_comparison.json` under `output_dir_final` (Main).
  Rationale: User confirmed full list with `unavailable` rows, include current vs policy/benchmarks,
  and Main folder placement for a single decision-support table next to existing Main outputs.
  Date/Author: 2026-05-17 / User and Codex

- Decision: Keep Session 04 config UI input modes on one screen with a clear `analysis_mode`
  selector rather than creating a separate current-portfolio diagnostics panel.
  Rationale: The user explicitly chose one screen with a clear mode switch. This keeps the utility UI
  small while still separating optimize-from-universe ticker input from analyze-current-weights
  current-weight input.
  Date/Author: 2026-05-17 / User and Codex

## Outcomes & Retrospective

Initial outcome: this ExecPlan creates a concrete sessionized development plan. It does not change
runtime behavior, formulas, output contracts, UI behavior, or generated artifacts. Its next practical
use is to start Session 01 in a fresh chat and promote the audit backlog into a durable roadmap and
known-issues register.

Session 01 outcome: the durable roadmap and issue register now exist. `docs/ROADMAP.md` is the
ordered backlog, `KNOWN_ISSUES.md` records unresolved audit-derived risks, `DECISIONS.md` records the
roadmap ownership decision, and `README.md` links the new roadmap. The next practical step is Session
02: fix the stale stress covariance documentation.

Session 02 outcome: the stress covariance source-of-truth no longer presents legacy uniform covariance
as current behavior. `docs/specs/stress_testing_spec.md` now states that synthetic RC_vol uses
`taxonomy_blend_v1` by default and documents `uniform_legacy` as opt-in legacy behavior only. The
resolved stress covariance known issue was removed, `docs/ROADMAP.md` marks `RM-001` done, and the next
practical step is Session 03: remove or correct the stale RC cap surface in `config_ui`.

Session 03 outcome: the config UI no longer presents `rc_asset_cap_pct` as an editable optimization
constraint. `config_ui/templates/config_form.html` removed the old field, focused regression tests
cover both the rendered form and posted ignored field behavior, the resolved known issue was removed,
`docs/ROADMAP.md` marks `RM-002` done, and the next practical step is Session 04: fix `config_ui`
analysis-mode and generated-weight semantics.

Session 04 outcome: the config UI now exposes a single-screen `analysis_mode` selector. In
`optimize_from_universe`, ticker rows define the investable universe and generated policy weights remain
read-only output from `portfolio_weights.yml`; in `analyze_current_weights`, the UI writes
`current_weights` for fixed current-portfolio diagnostics and disables optimization actions. The
resolved known issue was removed, `docs/ROADMAP.md` marks `RM-003` done, focused config/input tests
passed, and the next practical step is Session 06: clean source-document mojibake in a focused
documentation hygiene pass.

Session 05 outcome: `src/rebalance.py` docstrings now state that `threshold_pct` gates on maximum
absolute per-ticker weight deviation only; portfolio turnover is not evaluated. Explicit turnover
threshold logic remains deferred to Action/No-Trade sessions. Focused tests in
`tests/test_rebalance_threshold.py` lock the semantics (`2 passed`). The resolved known issue was
removed, `docs/ROADMAP.md` marks `RM-005` done, and the next practical step was Session 06.

Session 06 outcome: source specs targeted by audit `AUD-009` are readable UTF-8 English again.
`docs/specs/production_workflow.md` was fully rewritten (the prior file was double-encoded Russian).
`stress_testing_spec.md`, `metrics_specification.md`, and `view_after_optimization_spec.md` had
mojibake punctuation and math tokens replaced with ASCII equivalents (`->`, `>=`, `Sigma`,
`sigma_sq`, `rho`, and similar). The resolved known issue was removed, `docs/ROADMAP.md` marks
`RM-006` done, and the next practical step is Session 07: lightweight documentation verification.

Session 07 outcome: documentation verification is now repeatable. `scripts/verify_docs.py` and
`tests/test_docs_links.py` check local Markdown links in source docs (with repo-root resolution for
`docs/`, `src/`, `tests/`, and similar prefixes), forbidden stale canonical paths, and that
`config_ui` does not reintroduce editable `rc_asset_cap_pct`. Planned future spec filenames remain
allowlisted until Sessions 08+ create them. The resolved known issue was removed, `docs/ROADMAP.md`
marks `RM-007` done, and the next practical step is Session 08: specify the canonical candidate
comparison artifact.

Session 08 outcome: `docs/specs/candidate_comparison_spec.md` defines the canonical
`candidate_comparison.json` contract under `output_dir_final`. V1 includes the full candidate registry
(policy, current, EW, RP, robust scenario, robust MV, min variance, max diversification, min CVaR,
and extended baselines) with explicit `unavailable` status when folders are missing; `current` is a
first-class row when `analyze_current_weights` or `user_current_portfolio` artifacts exist. Legacy
`portfolio_comparison.json` / `ew_rp_comparison.json` remain documented as compatibility outputs.
`docs/ROADMAP.md` marks `RM-101` done. Next step: Session 10 — specify the Robustness Scorecard.

Session 10 outcome: `docs/specs/robustness_scorecard_spec.md` defines diagnostic-only
`robustness_scorecard.json` (0–100 total, six components, relative within-run normalization,
mandate absolute checks in `mandate_fit`, RC via planned comparison `diversification` block).
`docs/ROADMAP.md` marks `RM-200` done. Session 11 implemented scorecard + comparison v1.1
diversification fields (`RM-201` done). Next step: Session 12 — specify Portfolio Health Score.

Session 12 outcome: `docs/specs/portfolio_health_score_spec.md` defines diagnostic-only
`portfolio_health_score.json` (0–100 total, ten components, holistic quality vs robustness resilience,
optional ingest of robustness total in `resilience_reference`). `docs/ROADMAP.md` marks `RM-210` done.
Next step: Session 13 — implement Portfolio Health Score and comparison `weight_concentration` block.

Session 13 outcome: `src/portfolio_health_score.py` emits `portfolio_health_score.json` / `.txt` under
`output_dir_final`; `candidate_comparison` includes `weight_concentration` from `final_weights_total`.
`docs/ROADMAP.md` marks `RM-211` done. Next step: Session 14 — specify Selection Engine and No-Trade.

Session 15 outcome: `src/selection_engine.py` emits `selection_decision.json` / `.txt` under
`output_dir_final` after comparison and score artifacts; `docs/ROADMAP.md` marks `RM-301` done.
Next step: Session 16 — extend Action Engine and Rebalancing Advisor.

Session 16 outcome: `docs/specs/action_engine_spec.md` and `src/action_engine.py` emit
`action_plan.json` / `.txt` after every selection write (10 bps on turnover, empty trades with
reason on No-Trade). `docs/ROADMAP.md` marks `RM-310` done. Next step: Session 17 — monitoring spec.

Session 17–18 outcome: `docs/specs/monitoring_spec.md` and `src/monitoring.py` emit
`monitoring/latest/analysis_snapshot.json`, history archives, and `monitoring_diff.json` / `.txt`
after the decision pipeline. `docs/ROADMAP.md` marks `RM-400` and `RM-401` done. Next step: Session 19 — Decision Journal spec.

Session 19 outcome: `docs/specs/decision_journal_spec.md` defines `decision_journal_v1` (generated-only,
non-executing, latest + history under `journal/`, projects selection/action/monitoring/comparison).
`docs/ROADMAP.md` marks `RM-410` done. Next step: Session 20 — implement `src/decision_journal.py` and wire after monitoring.

Session 20 outcome: `src/decision_journal.py` emits `decision_journal_v1` JSON/TXT and journal latest/history copies after monitoring; `docs/ROADMAP.md` marks `RM-411` done. Sessions 01–20 of the core plan are complete. Next optional work: Session 21 (UI decision) or Phase 6 post-closure when the user explicitly requests it.

The current documentation set is enough to restart most implementation sessions if the session reads
the correct files. Core decision-pipeline artifacts through Decision Journal are implemented.

## Context and Orientation

The repository is a Python portfolio decision-support and reporting system. The current product is
report-first and CLI/file-driven. The main flow is:

    python run_optimization.py
    python run_report.py

`run_optimization.py` creates optimized weights and release metadata. `run_report.py` creates metrics,
stress diagnostics, factor and macro diagnostics, Portfolio X-Ray, commentary, JSON, CSV, HTML, TXT,
and PDF-style artifacts. Candidate scripts such as `run_equal_weight.py`, `run_risk_parity.py`,
`run_minimum_variance.py`, `run_minimum_cvar_constrained.py`, `run_robust_mean_variance_constrained.py`,
and `run_robust_scenario_optimization.py` build fixed comparison portfolios.

The current implementation contract starts at `SPEC.md`. Detailed behavior lives under
`docs/specs/`. Product direction lives in `PRODUCT.md`, `BUSINESS_VISION.md`, and
`docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`, but those documents are not binding implementation specs. The
2026-05-17 audit is the main evidence document for this plan:

- `docs/audits/2026-05-17_full_project_system_audit.md`
- `docs/audits/2026-05-17_diagnostic_product_concept_alignment_audit.md`

The audit conclusion is that the analytical base is substantial, while the formal product decision
layer is not done. Missing or partial areas include a unified candidate comparison arena, Robustness
Scorecard, Portfolio Health Score, Selection Engine, No-Trade Recommendation, Action Engine,
Monitoring / What Changed, and Decision Journal.

Important boundaries:

- Final policy weights are optimizer outputs, not normal manual user inputs.
- Manual post-optimization tilt is allowed only through View After Optimization.
- Diagnostics do not become binding optimizer policy unless a canonical spec says so.
- Portfolio X-Ray and commentary are diagnostic-only today and must not imply selection or trade advice.
- Generated outputs are evidence, not source, unless a task explicitly targets generated artifacts.
- ETF and stock taxonomy are annotation-only in V1 unless a future canonical spec changes that boundary.

## Documentation Sufficiency For Future Sessions

The current documentation is enough for a new session to understand the current system if it reads the
right files. The required common context bundle is:

- `AGENTS.md`
- `WORKFLOW.md`
- `RULES.md`
- `SPEC.md`
- `TESTING.md`
- `OUTPUTS.md`
- `docs/audits/2026-05-17_full_project_system_audit.md`
- this ExecPlan

For product-direction sessions, also read:

- `PRODUCT.md`
- `BUSINESS_VISION.md`
- `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`
- `ARCHITECTURE.md`

For implementation sessions, also read the owning detailed spec under `docs/specs/` and the owning
code or tests listed in the session.

After Session 01, the documentation is still not sufficient in one major way:

1. Future product modules lack owning specs. Sessions 08, 10, 12, 14, 17, and 19 should create them
   before implementation sessions write code.

## Session Operating Rules

Start a new session for each numbered session below. Do not combine sessions unless the user explicitly
asks to do so. Each session should:

1. Read the common context bundle.
2. Read the session-specific docs and code.
3. Ask only the listed clarifying questions if the answer changes behavior.
4. Make the scoped change.
5. Sync docs according to `WORKFLOW.md`.
6. Verify according to `TESTING.md`.
7. Update this ExecPlan progress if the session changes the plan.
8. Report changed files, verification, and unverified areas.

Codex is responsible for guiding the user through the plan. The user does not need to paste the long
kickoff text manually. If the user starts a fresh chat and says "continue the project development plan",
"continue the plan", "what are we working on now", or similar, Codex should open this ExecPlan, inspect
`Progress`, and continue the first incomplete or explicitly partial session. If a session was only
partly completed, continue that same session before starting the next one.

At the beginning of any chat that continues this plan, Codex must first give the user a short plain
summary before making edits. The summary should say: the current session number and title, why this
session is next, what concrete work is included, what is not included, and what will count as done.
Keep this startup summary brief enough that a non-professional developer can quickly understand the
scope before work begins.

Before implementation-heavy or methodology-heavy sessions, Codex must also make the plan understandable
to the user rather than treating the ExecPlan as an autopilot script. Briefly explain what will be built
or specified, which audit item or product-concept layer motivates it, which source documents control it,
what assumptions are already fixed, and which decisions still need the user's input. The user may discuss,
challenge, add requirements, or change priorities during a session. Codex should incorporate those
decisions into the session work and record durable decisions or plan changes in this ExecPlan and, when
appropriate, `DECISIONS.md` or the owning spec.

At the beginning or continuation of every session, after the short summary and before making edits,
Codex must ask the user 1-3 concise, highly relevant questions about the session scope, input
assumptions, preferred approach, or trade-offs. These questions are mandatory even when the plan already
contains a default path, because they give the user a clear control point before implementation. The
questions should be specific to the current session, not generic process questions. The user may answer
the questions, and Codex must use those answers as context for the session. If the proposed defaults are
acceptable, the user may simply answer "continue the plan", "continue", or "continue"; after that,
Codex should proceed using the documented defaults and record any relevant assumption in this ExecPlan
or the owning spec when appropriate.

At the end of every work session, Codex must update this ExecPlan with one of these states:

- completed: the session scope is done, docs are synced, and verification is reported;
- partial: some work is done, but specific remaining steps or checks are still required;
- blocked: the session cannot proceed without a user decision, missing dependency, or unresolved
  contradiction.

When a session is partial or blocked, Codex must write a plain next-step note in this ExecPlan, for
example: "Next session should continue Session 03 from template verification; remaining: update docs
and run stale-reference search." The final chat response must repeat that same handoff in short form
so the user knows whether to continue the same session or open a new one.

When a session is completed, Codex should tell the user that the session is complete, identify the next
session, and recommend starting a new chat if the current chat context is becoming large. This
historical ExecPlan is now complete; for current post-audit work, the user may simply write:
"Continue the post-audit stabilization plan." Codex should then read the active post-audit ExecPlan and
resume from its recorded state.

Generic kickoff text for any future session:

    We are continuing `docs/exec_plans/2026-05-17_project_development_session_plan.md`.
    Read `AGENTS.md`, `WORKFLOW.md`, `RULES.md`, `SPEC.md`, `TESTING.md`, `OUTPUTS.md`,
    `docs/audits/2026-05-17_full_project_system_audit.md`, and that ExecPlan first.
    Then work only on Session <NUMBER>: <TITLE>. Keep changes scoped, do not touch generated outputs
    unless required, update docs/tests as needed, and report verification.

## Plan of Work

### Phase 0: Stabilize current source of truth

This phase prevents future sessions from building on misleading docs or UI behavior. It should be
completed before new scoring, selection, no-trade, monitoring, or journal work.

#### Session 01: Create roadmap and register audit issues

Purpose: create the missing execution spine and make active audit issues visible.

Session-specific docs to read:

- `KNOWN_ISSUES.md`
- `DECISIONS.md`
- `CHANGELOG.md`
- `README.md`
- `PRODUCT.md`
- `ARCHITECTURE.md`
- `docs/audits/2026-05-17_full_project_system_audit.md`
- `docs/audits/2026-05-17_diagnostic_product_concept_alignment_audit.md`

Expected work:

- Create `docs/ROADMAP.md` unless the user chooses `docs/product_backlog.md`.
- Include phases, item IDs, status, prerequisites, owning docs, artifacts, verification, and session
  boundaries.
- Add concise `KNOWN_ISSUES.md` entries for unresolved audit items that are not fixed in the same
  session.
- Fix the stale `DECISIONS.md` intro that says no project-level decisions exist.
- Add one short `CHANGELOG.md` entry for roadmap/issue-register documentation if project convention
  warrants it.

Clarifying question before work:

- Ask: "Should the durable roadmap file be `docs/ROADMAP.md` or `docs/product_backlog.md`..."
- If the user does not answer, use `docs/ROADMAP.md`, because the audit named it first and it is
  clearer for future sessions.

Kickoff text:

    We are continuing `docs/exec_plans/2026-05-17_project_development_session_plan.md`.
    Work on Session 01 only: create the durable roadmap/backlog and register unresolved audit issues.
    Read the common context bundle plus `KNOWN_ISSUES.md`, `DECISIONS.md`, `CHANGELOG.md`,
    `README.md`, `PRODUCT.md`, `ARCHITECTURE.md`, and both 2026-05-17 audit files. Ask me whether
    to name the roadmap `docs/ROADMAP.md` or `docs/product_backlog.md`; if I do not choose, use
    `docs/ROADMAP.md`.

Validation:

- Search for all `AUD-` IDs and confirm each is either fixed, represented in `KNOWN_ISSUES.md`, or
  intentionally deferred in the roadmap.
- Search for obsolete empty-log placeholder text in `DECISIONS.md`.
- Documentation-only change: no pytest required unless command examples or behavior claims change.

#### Session 02: Fix stale stress covariance documentation

Purpose: remove a high-risk contradiction in the stress testing source of truth.

Session-specific docs and code to read:

- `docs/specs/stress_testing_spec.md`
- `src/stress.py`
- `src/stress_covariance_taxonomy.py`
- `tests/test_stress_covariance_taxonomy.py`
- `docs/exec_plans/2026-05-08_stress_scenario_analytics_v1.md` if needed for context

Expected work:

- Rewrite the stale section "Stress covariance (for RC in stress)" so `taxonomy_blend_v1` is the
  current default.
- Move the old `_stress_covariance` behavior under a clearly labeled `uniform_legacy` subsection.
- Keep scenario rows for equity, credit, liquidity, recession severe, rates shock, and
  inflation/stagflation consistent.
- Do not change code unless the spec review uncovers an actual implementation mismatch.

Clarifying question before work:

- Usually none. If code and tests contradict the audit, ask whether to align docs to code or treat it
  as a behavior bug.

Kickoff text:

    Work on Session 02 only: fix the stale stress covariance documentation. Read the common context
    bundle plus `docs/specs/stress_testing_spec.md`, `src/stress.py`, `src/stress_covariance_taxonomy.py`,
    and `tests/test_stress_covariance_taxonomy.py`. Align the spec around `taxonomy_blend_v1` as the
    current default and clearly mark `uniform_legacy` as legacy behavior.

Validation:

- Search `docs/specs/stress_testing_spec.md` for legacy `vol_mult` and `_stress_covariance` references
  and confirm they are not presented as current default behavior.
- Documentation-only change: no pytest required unless code examples or behavior claims change.

#### Session 03: Remove or correct stale RC cap UI

Purpose: prevent the config UI from implying that a removed risk-contribution cap is active.

Session-specific docs and code to read:

- `config_ui/templates/config_form.html`
- `config_ui/app.py`
- `docs/specs/feasibility_constraints_spec.md`
- `docs/exec_plans/2026-04-28_rc_diagnostic_only.md`
- `docs/specs/portfolio_construction_policy.md`
- `DESIGN.md`

Expected work:

- Remove the editable `rc_asset_cap_pct` UI field, or replace it with non-editable diagnostic wording.
- Do not reintroduce RC caps without a new decision and spec.
- Update user-facing docs only if the UI surface description changes.

Clarifying question before work:

- Ask: "Should the old RC cap field be removed entirely, or kept as read-only diagnostic context..."
- If the user does not answer, remove it entirely. Silent ignored inputs are worse than a missing field.

Kickoff text:

    Work on Session 03 only: remove or correct the stale RC cap in `config_ui`. Read the common context
    bundle plus `config_ui/templates/config_form.html`, `config_ui/app.py`,
    `docs/specs/feasibility_constraints_spec.md`, `docs/exec_plans/2026-04-28_rc_diagnostic_only.md`,
    `docs/specs/portfolio_construction_policy.md`, and `DESIGN.md`. Ask whether to remove the field
    or make it read-only; default to removing it if I do not choose.

Validation:

- Search for `rc_asset_cap_pct` and confirm no editable UI path remains unless deliberately read-only.
- Run focused config UI validation if tests exist; otherwise inspect the rendered template path manually.
- No portfolio math tests required unless config schema or optimizer behavior changes.

#### Session 04: Fix config UI analysis-mode and generated-weight semantics

Purpose: make the UI respect the distinction between current user weights and generated optimizer
weights.

Session-specific docs and code to read:

- `config_ui/app.py`
- `config_ui/templates/config_form.html`
- `config_ui/static/design.css`
- `docs/specs/input_assumptions_spec.md`
- `config.yml.example`
- `src/config.py`
- `src/config_schema.py`
- `tests/test_input_assumptions.py`
- `tests/test_config_weights_sync.py`
- `DECISIONS.md` decisions `DEC-2026-05-15-001` and `DEC-2026-05-15-002`

Expected work:

- Add explicit `analysis_mode` UI controls.
- Add `current_weights` entry/editing path for `analysis_mode=analyze_current_weights`.
- Stop loading generated `portfolio_weights.yml` into editable `weights` by default.
- Show generated `portfolio_weights.yml` as read-only generated output if useful.
- Preserve the rule that optimizer output is not normal manual source config.

Clarifying question before work:

- Ask: "Should the config UI support both optimize-from-universe and analyze-current-weights in the
  same screen, or should current-weight diagnostics be a separate mode panel..."
- If the user does not answer, implement a clear mode control on the same screen.

Kickoff text:

    Work on Session 04 only: fix `config_ui` analysis-mode and generated-weight semantics. Read the
    common context bundle plus `config_ui/app.py`, `config_ui/templates/config_form.html`,
    `config_ui/static/design.css`, `docs/specs/input_assumptions_spec.md`, `config.yml.example`,
    `src/config.py`, `src/config_schema.py`, `tests/test_input_assumptions.py`,
    `tests/test_config_weights_sync.py`, and `DECISIONS.md`. Keep generated `portfolio_weights.yml`
    read-only and separate from user-entered `current_weights`.

Validation:

- Run focused tests around config/input assumptions, at minimum `tests/test_input_assumptions.py` and
  `tests/test_config_weights_sync.py`.
- Manually inspect the UI template behavior or run the local config UI if needed.
- Search for `portfolio_weights.yml` loading into editable `weights` and confirm it is gone.

#### Session 05: Fix rebalance threshold semantics

Purpose: prevent the future no-trade layer from inheriting inaccurate threshold wording or behavior.

Session-specific docs and code to read:

- `src/rebalance.py`
- `run_rebalance.py`
- any existing rebalance tests
- `PRODUCT.md` sections for Rebalancing Advisor and No-Trade Recommendation
- `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md` sections 19, 20, and 21

Expected work:

- Option A: update `src/rebalance.py` docstrings to state that `threshold_pct` means max absolute
  per-ticker drift only.
- Option B: implement explicit turnover threshold behavior with tests and docs.

Clarifying question before work:

- Ask: "Should this session only correct the docstring, or should it add real turnover-threshold logic..."
- If the user does not answer, do the smaller safe fix: correct the docstring and leave product
  turnover logic for Action/No-Trade sessions.

Kickoff text:

    Work on Session 05 only: fix rebalance threshold semantics. Read the common context bundle plus
    `src/rebalance.py`, `run_rebalance.py`, existing rebalance tests if any, `PRODUCT.md`, and
    `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md` sections for Action Engine, Rebalancing Advisor, and No-Trade
    Recommendation. Ask whether to correct wording only or implement turnover threshold logic; default
    to wording only if I do not choose.

Validation:

- If docstring-only: search for "turnover above threshold" and confirm the overstatement is removed.
- If behavior changes: add focused tests and run them, then update docs and CLI help if needed.

#### Session 06: Clean source-document mojibake

Purpose: restore readability of source documentation that contains encoding artifacts.

Session-specific docs to read:

- `docs/specs/production_workflow.md`
- `docs/specs/stress_testing_spec.md`
- `docs/specs/metrics_specification.md`
- `docs/specs/factor_diagnostics_spec.md`
- Any files found by a targeted mojibake search

Expected work:

- Legacy note normalized to English-only text.
- Fix source documentation only. Do not edit generated report outputs in this session.
- Preserve technical meaning; where exact intended symbol is uncertain, prefer plain ASCII terms such
  as `Sigma_base` instead of guessing a mathematical glyph.

Clarifying question before work:

- Ask only if a corrupted phrase cannot be reconstructed from context.

Kickoff text:

    Work on Session 06 only: clean mojibake in source documentation, not generated outputs. Read the
    common context bundle plus `docs/specs/production_workflow.md`, `docs/specs/stress_testing_spec.md`,
    `docs/specs/metrics_specification.md`, and `docs/specs/factor_diagnostics_spec.md`. Search for
    mojibake patterns and fix only source docs where meaning is clear.

Validation:

- Run targeted `rg` searches for known mojibake patterns.
- Documentation-only change: no pytest required.

#### Session 07: Add lightweight docs verification

Purpose: reduce stale links and stale field references after documentation changes.

Session-specific docs to read:

- `TESTING.md`
- `WORKFLOW.md`
- `README.md`
- `docs/specs/README.md`
- Existing scripts under `scripts/`

Expected work:

- Add or document a lightweight Markdown link and stale-reference verification method.
- Include checks for removed fields such as `rc_asset_cap_pct` after Session 03.
- Prefer a small script or documented command that works on this repo without changing runtime behavior.
- Update `TESTING.md` if a repeatable command is added.

Clarifying question before work:

- Ask whether the user wants a checked-in script or only a documented manual command.
- If no answer, add a checked-in script only if it is simple and dependency-light; otherwise document a
  manual command in `TESTING.md`.

Kickoff text:

    Work on Session 07 only: add lightweight documentation verification for Markdown links and stale
    references. Read the common context bundle plus `TESTING.md`, `WORKFLOW.md`, `README.md`,
    `docs/specs/README.md`, and existing scripts. Ask whether I should add a checked-in script or only
    document a manual check.

Validation:

- Run the new or documented docs verification command.
- Confirm it can find stale references without scanning generated output folders as source.

### Phase 1: Standardize candidate comparison

This phase creates the foundation for any score, recommendation, or no-trade conclusion.

#### Session 08: Specify canonical candidate comparison artifact

Purpose: define the stable artifact that all scoring and selection work will consume.

Session-specific docs and code to read:

- `docs/specs/candidate_portfolios_spec.md`
- `docs/specs/reporting_outputs_spec.md`
- `OUTPUTS.md`
- `run_compare_variants.py`
- `run_compare_ew_rp.py`
- `src/portfolio_variants.py`
- `docs/specs/robust_mv_spec.md`
- `docs/specs/robust_scenario_optimization_spec.md`
- `PRODUCT.md` Candidate Comparison Arena section
- `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md` sections 9 and 10

Expected work:

- Create a canonical spec, likely `docs/specs/candidate_comparison_spec.md`.
- Define `candidate_comparison.json` with version, candidate metadata, construction method, role,
  weights source, constraints, metrics block, stress block, drawdown block, factor/regime block,
  warnings, missing-data behavior, and diagnostic-only boundaries.
- Update `docs/specs/README.md`, `SPEC.md`, `OUTPUTS.md`, and `PRODUCT.md` only if appropriate and
  safe with current worktree state.

Clarifying question before work:

- Ask: "Which candidate set must be first-class in V1: policy, current, equal weight, risk parity,
  robust scenario, robust MV, min variance, max diversification, and min CVaR; or a smaller launch set..."
- If the user does not answer, specify the broader set but allow candidates to be `unavailable` when
  artifacts are missing.

Kickoff text:

    Work on Session 08 only: specify the canonical candidate comparison artifact. Read the common
    context bundle plus candidate/reporting/robust specs, `run_compare_variants.py`,
    `run_compare_ew_rp.py`, `src/portfolio_variants.py`, `PRODUCT.md`, and concept sections 9 and 10.
    Ask which candidate set is first-class in V1; default to a broad set with explicit unavailable
    statuses.

Validation:

- Documentation-only unless executable examples change.
- Search for `candidate_comparison` and confirm no conflicting contract exists.

#### Session 09: Implement canonical candidate comparison output

Purpose: produce `candidate_comparison.json` from existing candidate and report artifacts.

Session-specific docs and code to read:

- The spec created in Session 08
- `run_compare_variants.py`
- `run_compare_ew_rp.py`
- `src/portfolio_variants.py`
- `src/io_export.py`
- `src/snapshot.py`
- Relevant tests for candidate builders and reporting

Expected work:

- Implement a shared comparison builder instead of duplicating schema logic in CLI scripts.
- Preserve old comparison outputs if needed for compatibility, but make `candidate_comparison.json`
  the canonical artifact.
- Add focused tests for schema, missing candidates, degraded diagnostics, and stable candidate roles.
- Update output docs and changelog.

Clarifying question before work:

- Ask only if the Session 08 spec leaves artifact location or compatibility behavior unresolved.

Kickoff text:

    Work on Session 09 only: implement `candidate_comparison.json` according to the Session 08 spec.
    Read the common context bundle plus the candidate comparison spec, `run_compare_variants.py`,
    `run_compare_ew_rp.py`, candidate/reporting code, and relevant tests. Keep old outputs compatible
    unless the spec says otherwise.

Validation:

- Run focused candidate comparison tests added in the session.
- Run affected candidate comparison CLI smoke command.
- Inspect generated `candidate_comparison.json` if generated artifacts are intentionally targeted.

### Phase 2: Add transparent scoring

Scores must be transparent. They should explain their inputs, weights, missing-data handling, and why
a portfolio scored well or poorly.

#### Session 10: Specify Robustness Scorecard

Purpose: formalize resilience scoring before any code uses it.

Session-specific docs to read:

- Candidate comparison spec from Session 08
- `docs/specs/stress_testing_spec.md`
- `docs/specs/metrics_specification.md`
- `docs/specs/factor_diagnostics_spec.md`
- `docs/specs/macro_regime_spec.md`
- `PRODUCT.md`
- `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md` section 12

Expected work:

- Create a Robustness Scorecard spec.
- Define inputs, component scores, normalization, missing-data statuses, thresholds, output artifact,
  diagnostic-only wording, and tests.
- Do not implement code until the spec is accepted or clearly complete.

Clarifying question before work:

- Ask whether the user wants initial conceptual weights from the product concept or a stricter TBD
  draft with no numeric score until validated.
- If no answer, draft the spec with transparent proposed defaults but mark them reviewable.

Kickoff text:

    Work on Session 10 only: specify the Robustness Scorecard. Read the common context bundle plus the
    candidate comparison spec, stress, metrics, factor, and macro specs, `PRODUCT.md`, and concept
    section 12. Ask whether to use conceptual default weights or keep weights TBD; default to proposed
    reviewable defaults.

Validation:

- Documentation-only unless examples are executable.
- Search to confirm no recommendation or selection behavior is accidentally introduced.

#### Session 11: Implement Robustness Scorecard

Purpose: produce transparent robustness outputs after the spec and comparison artifact exist.

Session-specific docs and code to read:

- Robustness Scorecard spec from Session 10
- Candidate comparison spec from Session 08
- Implementation from Session 09
- Relevant metrics, stress, factor, and report modules
- Relevant tests

Expected work:

- Implement score calculation from the canonical candidate comparison artifact.
- Emit score components and explanations, not only a single number.
- Handle missing data explicitly.
- Add tests and docs.

Clarifying question before work:

- Ask only if Session 10 left component weights or artifact location unresolved.

Kickoff text:

    Work on Session 11 only: implement Robustness Scorecard according to the accepted spec. Read the
    common context bundle plus the Robustness Scorecard spec, candidate comparison spec, implementation
    from Session 09, relevant analytics modules, and tests. Emit component explanations and explicit
    missing-data statuses.

Validation:

- Run new robustness scorecard tests.
- Run candidate comparison tests.
- Run report or comparison CLI smoke if the score is exported.

#### Session 12: Specify Portfolio Health Score

Purpose: define an investor-facing overall quality score without making it a black box.

Session-specific docs to read:

- Robustness Scorecard spec and implementation docs
- Candidate comparison spec
- `docs/specs/metrics_specification.md`
- `docs/specs/stress_testing_spec.md`
- `docs/specs/reporting_outputs_spec.md`
- `PRODUCT.md`
- `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md` section 11

Expected work:

- Create a Portfolio Health Score spec.
- Define how it differs from Robustness Scorecard.
- Define components such as diversification, concentration, drawdown resilience, stress behavior,
  factor balance, liquidity, mandate fit, and model-risk caveats.
- Keep it explanatory and non-binding until Selection Engine exists.

Clarifying question before work:

- Ask: "Should Health Score apply first to current/policy only, or to every candidate..."
- If no answer, specify it for every candidate but allow report surfaces to show current/policy first.

Kickoff text:

    Work on Session 12 only: specify Portfolio Health Score. Read the common context bundle plus the
    Robustness Scorecard spec, candidate comparison spec, metrics/stress/reporting specs, `PRODUCT.md`,
    and concept section 11. Ask whether the score applies to current/policy only or every candidate;
    default to every candidate with current/policy shown first.

Validation:

- Documentation-only unless examples are executable.
- Search for wording that implies a recommendation before Selection Engine exists.

#### Session 13: Implement Portfolio Health Score

Purpose: emit Health Score outputs after comparison and robustness inputs are stable.

Session-specific docs and code to read:

- Health Score spec from Session 12
- Robustness Scorecard implementation
- Candidate comparison implementation
- Reporting outputs spec
- Relevant tests

Expected work:

- Implement Health Score components and explanations.
- Add generated artifact and report surface only as specified.
- Add tests for scoring, missing data, and non-recommendation wording.

Clarifying question before work:

- Ask only if Session 12 left artifact location or display surface unresolved.

Kickoff text:

    Work on Session 13 only: implement Portfolio Health Score according to the accepted spec. Read the
    common context bundle plus the Health Score spec, Robustness Scorecard implementation, candidate
    comparison implementation, reporting outputs spec, and tests. Keep output explanatory and
    non-binding.

Validation:

- Run new Health Score tests.
- Run adjacent robustness and candidate comparison tests.
- Run report/comparison CLI smoke if outputs are generated.

### Phase 3: Add selection, no-trade, and action

This phase is where the product may start saying which candidate is favored, but only after comparison
and scores are stable.

#### Session 14: Specify Selection Engine and No-Trade Recommendation

Purpose: define decision rules before adding recommendation language.

Session-specific docs to read:

- Candidate comparison spec
- Robustness Scorecard spec
- Health Score spec
- `docs/specs/portfolio_construction_policy.md`
- `docs/specs/production_workflow.md`
- `PRODUCT.md`
- `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md` sections 13 and 21

Expected work:

- Create a Selection Engine and No-Trade spec.
- Define allowed outcomes: selected candidate, no material rebalance, inconclusive, data review
  required, mandate breach requires risk reduction.
- Define how scores, mandate gates, turnover, model-risk warnings, and missing data affect decisions.
- Define recommendation wording boundaries.

Clarifying question before work:

- Ask what tone is allowed for decisions: neutral decision-support wording or direct action wording.
- If no answer, use neutral decision-support wording and avoid direct financial-advice phrasing.

Kickoff text:

    Work on Session 14 only: specify Selection Engine and No-Trade Recommendation. Read the common
    context bundle plus candidate comparison, Robustness Scorecard, Health Score, portfolio policy,
    production workflow, `PRODUCT.md`, and concept sections 13 and 21. Ask what decision tone is
    allowed; default to neutral decision-support wording.

Validation:

- Documentation-only unless examples are executable.
- Search to confirm Portfolio X-Ray and diagnostic commentary remain non-binding.

#### Session 15: Implement Selection Engine and No-Trade Recommendation

Purpose: create the first formal decision artifact after comparison and scores exist.

Session-specific docs and code to read:

- Selection/No-Trade spec from Session 14
- Candidate comparison implementation
- Robustness and Health Score implementations
- Rebalance utilities
- Report/commentary modules
- Relevant tests

Expected work:

- Implement a decision artifact with selected candidate or no-trade/inconclusive status.
- Include rationale, rejected candidates, trade-offs, warnings, and missing-data notes.
- Keep diagnostic artifacts separate from decision artifacts.
- Add tests for each allowed decision outcome.

Clarifying question before work:

- Ask only if Session 14 left a decision threshold unresolved.

Kickoff text:

    Work on Session 15 only: implement Selection Engine and No-Trade Recommendation according to the
    accepted spec. Read the common context bundle plus the Selection/No-Trade spec, candidate
    comparison, score implementations, rebalance utilities, report/commentary modules, and tests.
    Keep diagnostic artifacts separate from formal decision artifacts.

Validation:

- Run new selection/no-trade tests.
- Run score and comparison tests.
- Run report or comparison CLI smoke if decision artifacts are exported.

#### Session 16: Extend Action Engine and Rebalancing Advisor

Purpose: turn a selected candidate into practical deltas without overtrading.

Session-specific docs and code to read:

- Selection/No-Trade spec and implementation
- `src/rebalance.py`
- `run_rebalance.py`
- View After Optimization spec
- `PRODUCT.md` Action/Rebalancing sections
- `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md` sections 19 and 20

Expected work:

- Define or implement target-vs-current deltas, buy/sell/hold, turnover, optional cost assumptions,
  and risk improvement per turnover.
- Keep transaction costs simple or explicitly TBD unless separately specified.
- Add tests and docs.

Clarifying question before work:

- Ask whether transaction costs should be simple basis-point assumptions, per-asset config, or left
  as TBD.
- If no answer, leave transaction costs as explicit TBD and implement only fields supported by current
  data.

Kickoff text:

    Work on Session 16 only: extend Action Engine and Rebalancing Advisor around selected candidates.
    Read the common context bundle plus Selection/No-Trade docs and implementation, `src/rebalance.py`,
    `run_rebalance.py`, View After Optimization spec, `PRODUCT.md`, and concept sections 19 and 20.
    Ask how to model transaction costs; default to leaving costs as explicit TBD.

Validation:

- Run rebalance/action tests.
- Run selection tests if action consumes decision artifacts.
- Run CLI smoke if `run_rebalance.py` behavior changes.

### Phase 4: Add monitoring and decision records

This phase turns one-time analysis into a repeatable process.

#### Session 17: Specify monitoring snapshots and What Changed artifacts

Purpose: define persistent analysis snapshots before implementing monitoring diffs.

Session-specific docs to read:

- `OUTPUTS.md`
- `docs/specs/reporting_outputs_spec.md`
- `PRODUCT.md` Monitoring section
- `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md` section 23
- Selection/No-Trade and Action specs if they exist

Expected work:

- Create a monitoring snapshot spec.
- Define what gets persisted from each analysis and how snapshots are compared.
- Define "What Changed" artifact fields, missing prior snapshot behavior, and data-quality warnings.

Clarifying question before work:

- Ask where persistent snapshots should live: generated output folder, dedicated `analyses/`, or another
  path.
- If no answer, specify a generated output location first and defer durable workspace storage.

Kickoff text:

    Work on Session 17 only: specify monitoring snapshots and What Changed artifacts. Read the common
    context bundle plus `OUTPUTS.md`, reporting outputs spec, `PRODUCT.md`, concept section 23, and
    any existing Selection/Action specs. Ask where persistent snapshots should live; default to a
    generated output location and defer durable workspace storage.

Validation:

- Documentation-only unless examples are executable.
- Check output docs for generated-vs-source clarity.

#### Session 18: Implement monitoring diff outputs

Purpose: emit what changed since the prior analysis.

Session-specific docs and code to read:

- Monitoring spec from Session 17
- Report output modules
- Snapshot/reporting code
- Tests around reporting outputs

Expected work:

- Implement comparison against a prior snapshot when available.
- Emit changed risk score, top risk contributor, worst scenario, macro regime, mandate status, and
  warnings where data exists.
- Add tests for no prior snapshot, normal diff, and degraded/missing fields.

Clarifying question before work:

- Ask only if snapshot location or retention rules are unresolved.

Kickoff text:

    Work on Session 18 only: implement monitoring diff outputs according to the accepted monitoring
    spec. Read the common context bundle plus the monitoring spec, report output modules,
    snapshot/reporting code, and tests. Handle missing prior snapshots explicitly.

Validation:

- Run new monitoring tests.
- Run report tests and CLI smoke if report outputs change.

#### Session 19: Specify Decision Journal schema and lifecycle

Purpose: define how decisions are recorded before writing journal artifacts.

Session-specific docs to read:

- Selection/No-Trade spec
- Action/Rebalance spec if it exists
- Monitoring spec if it exists
- `PRODUCT.md` Decision Journal section
- `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md` section 24
- `OUTPUTS.md`

Expected work:

- Create a Decision Journal spec.
- Define fields: analysis date, selected portfolio, rejected alternatives, assumptions, expected
  improvement, accepted risks, macro context, rationale, no-trade status, follow-up date, and links to
  artifacts.
- Define append/update behavior and generated-vs-source boundary.

Clarifying question before work:

- Ask whether the journal is a generated artifact only or a user-maintained source record.
- If no answer, make V1 generated-only to avoid silently editing user records.

Kickoff text:

    Work on Session 19 only: specify the Decision Journal schema and lifecycle. Read the common context
    bundle plus Selection/No-Trade docs, Action/Rebalance docs if they exist, Monitoring docs if they
    exist, `PRODUCT.md`, concept section 24, and `OUTPUTS.md`. Ask whether the journal is generated-only
    or user-maintained; default to generated-only V1.

Validation:

- Documentation-only unless examples are executable.
- Confirm output docs distinguish generated journal artifacts from source docs.

#### Session 20: Implement Decision Journal output

Purpose: emit a decision record from the decision/action pipeline.

Session-specific docs and code to read:

- Decision Journal spec from Session 19
- Selection/No-Trade implementation
- Action/Rebalance implementation
- Monitoring implementation if relevant
- Report/commentary modules
- Relevant tests

Expected work:

- Implement generated decision journal output.
- Include links or references to candidate comparison, score, decision, action, and monitoring artifacts
  where available.
- Add tests for selected candidate, no-trade, inconclusive, and missing-data decisions.

Clarifying question before work:

- Ask only if Session 19 leaves append/update behavior unresolved.

Kickoff text:

    Work on Session 20 only: implement Decision Journal output according to the accepted spec. Read the
    common context bundle plus the Decision Journal spec, Selection/No-Trade implementation,
    Action/Rebalance implementation, Monitoring implementation if relevant, report/commentary modules,
    and tests. Keep V1 generated-only unless the spec says otherwise.

Validation:

- Run journal tests.
- Run selection/action tests.
- Run report CLI smoke if journal output is part of report generation.

### Phase 5: Deferred Product UI / Design Work

UI and design work is intentionally deferred. Do not start Session 21 or Session 22 automatically after
Session 20. Return to this phase only when the user explicitly asks to reactivate UI/design work after
the analytical contracts and decision artifacts are stable.

#### Session 21: Decide the first real product UI surface

Purpose: choose whether the first product surface is static report package, local dashboard, or web app.

Session-specific docs and code to read:

- `DESIGN.md`
- `PRODUCT.md`
- `ARCHITECTURE.md`
- `config_ui/`
- `results_dashboard/`
- Candidate comparison, score, selection, action, monitoring, and journal specs that exist by then

Expected work:

- Record a decision in `DECISIONS.md`.
- Update `PRODUCT.md` and `ARCHITECTURE.md` if the product direction changes.
- Do not implement a broad UI in this session unless the user explicitly asks.

Clarifying question before work:

- Ask the user to choose the first product surface: report package, local dashboard, or web app.
- If no answer, recommend local read-only dashboard after stable artifacts, because it can consume
  generated JSON without changing the analytical engine.

Kickoff text:

    Work on Session 21 only: decide the first real product UI surface. Read the common context bundle
    plus `DESIGN.md`, `PRODUCT.md`, `ARCHITECTURE.md`, `config_ui/`, `results_dashboard/`, and all
    stable product artifact specs created so far. Ask me to choose report package, local dashboard, or
    web app; default recommendation is a local read-only dashboard after stable artifacts.

Validation:

- Documentation-only unless code is explicitly requested.
- Confirm decision log and product docs do not contradict current CLI/report-first status.

#### Session 22: Implement the first UI slice

Purpose: display stable artifacts without inventing new product logic in the UI.

Session-specific docs and code to read:

- Decision from Session 21
- `DESIGN.md`
- `results_dashboard/` or chosen UI code
- Stable artifact specs
- Relevant tests or manual UI checks

Expected work:

- Implement the first narrow UI slice around existing stable artifacts.
- Do not compute formulas directly in the UI when shared modules or generated JSON already own them.
- Use the design rules in `DESIGN.md`.

Clarifying question before work:

- Ask for the minimum first screen if Session 21 did not define it.

Kickoff text:

    Work on Session 22 only: implement the first UI slice chosen in Session 21. Read the common context
    bundle plus `DESIGN.md`, the chosen UI code, and all stable artifact specs that the UI will display.
    Do not invent formulas in the UI; consume existing artifacts or shared helpers.

Validation:

- Run UI tests if present.
- Start the local UI server if applicable.
- Inspect the UI in a browser and verify no overlapping text or incoherent layout.
- Run Playwright/browser checks for significant frontend changes when available.

### Phase 6: Post-plan closure (after Sessions 01–20)

**Prerequisite:** Sessions 01–20 are marked complete in `Progress` (or the user explicitly waives
remaining session items and authorizes Phase 6 anyway). Sessions 21–22 are optional and do not block
Phase 6.

**Trigger:** Phase 6 does **not** start automatically after Session 20. The user must say something
like "start post-closure", "run Post-closure 1", or "continue post-plan work". Each post-closure item
should use a **fresh chat** when practical, same as numbered sessions.

Purpose: close the session plan with evidence-based next steps — not more feature work by default.

#### Post-closure 1: New audit and next-stage decision

Purpose: re-audit the repository after the session plan implementation; compare reality to product
concept; decide what the **next** development stage is.

Session-specific docs to read:

- `docs/audits/2026-05-17_full_project_system_audit.md`
- `docs/audits/2026-05-17_diagnostic_product_concept_alignment_audit.md`
- `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`
- `PRODUCT.md`, `SPEC.md`, `ARCHITECTURE.md`, `docs/ROADMAP.md`
- This ExecPlan `Progress` and artifacts created in Sessions 08–20

Expected work:

- Produce a **new** dated audit under `docs/audits/` (do not overwrite the 2026-05-17 audits).
- Compare implemented vs concept: what is done, partial, missing, or misaligned.
- Update `docs/ROADMAP.md` with the next stage and priorities.
- Record the next-stage decision in `DECISIONS.md`.

Validation:

- New audit file exists and references concrete evidence (specs, modules, outputs).
- Roadmap and decision log updated; no silent claim that concept items are "shipped" when they are TBD.

#### Post-closure 2: Block improvement backlog (scoped sessions)

Purpose: after the audit, identify **which blocks** (comparison, scores, selection, stress, data,
reporting, config UI, etc.) need improvement; fix or specify them **one block per session**, not in
one mega-change.

Expected work:

- From Post-closure 1, extract a prioritized block list with owner specs and verification.
- For each block: either a small ExecPlan addendum, a `KNOWN_ISSUES.md` entry, or a new roadmap item.
- Implement or specify improvements in **separate** future sessions; update this ExecPlan when a
  block is done.

Validation:

- Each block session has scoped files, tests, and doc sync per `WORKFLOW.md`.
- No mixing unrelated block fixes in one session unless the user explicitly asks.

#### Post-closure 3: Mojibake and broken symbols (extended sweep)

Purpose: Session 06 fixed a **focused** set of source specs; after full plan implementation, sweep
remaining broken encoding and symbols wherever they affect readability or client-facing output.

Scope (search and fix or track):

- Remaining `docs/specs/`, `docs/`, `PRODUCT.md`, and other source Markdown not covered in Session 06.
- Generated but durable text: `commentary.txt`, `stress_commentary.txt`, comparison notes, PDF Markdown
  sources under `pdf_md_sources/` (fix generators if the root cause is code, not hand-edit artifacts).
- Config examples and UI-visible strings.
- Do **not** treat one-off generated run folders as source unless fixing a reproducible generator bug.

Expected work:

- Targeted `rg` for mojibake patterns; document findings.
- Fix at source (templates, report builders, specs); run `python scripts/verify_docs.py` where applicable.
- Unresolved items → `KNOWN_ISSUES.md`.

Validation:

- Repeat targeted scans on touched paths; report any remaining issues explicitly.

#### Post-closure 4: Main optimizer vs robust optimization — inputs vs concept

Purpose: document what **currently** enters Main policy optimization vs robust MV / robust scenario
optimization; decide whether each path should change to match the product concept or stay as-is with
explicit rationale.

Session-specific docs and code to read:

- `docs/specs/portfolio_construction_policy.md`
- `docs/specs/robust_mv_spec.md`
- `docs/specs/robust_scenario_optimization_spec.md`
- `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md` (portfolio construction and candidate roles)
- `run_optimization.py`, `src/optimizer*.py` (or owning optimizer modules)
- `run_robust_mean_variance_constrained.py`, `run_robust_scenario_optimization.py`
- `config.yml` / `config.yml.example` and `portfolio_weights.yml` boundaries

Expected work:

- Table or structured note: inputs, objective, constraints, outputs, and **role in product** (policy
  vs diagnostic candidate) for Main vs each robust path.
- Gap analysis vs concept: what is intentional diagnostic-only vs what would be a product misalignment.
- **Decision only in this closure item** unless the user explicitly authorizes code changes in a
  follow-up session: `change`, `document as-is`, or `defer` per path; record in `DECISIONS.md`.
- No silent optimizer behavior changes during the review-only pass.

Clarifying question before work:

- Ask whether robust paths are strictly **candidates for comparison** or should converge toward policy
  construction rules; if no answer, default to comparison candidates unless the audit shows a hard
  misalignment.

Validation:

- Written comparison artifact (audit subsection or `DECISIONS.md` + short note in roadmap).
- No code changes unless user explicitly requests a follow-up implementation session.

Generic kickoff for Post-closure work:

    We are continuing `docs/exec_plans/2026-05-17_project_development_session_plan.md`.
    Work on Post-closure <N> only. Sessions 01–20 must be complete unless I explicitly waive.
    Read the common context bundle, this ExecPlan Phase 6 section, and the Post-closure doc list.

## Concrete Steps

Sessions 01-20 and the Phase 6 post-closure audit triage are complete. This ExecPlan is historical.
The active handoff now lives in
`docs/exec_plans/2026-05-17_post_audit_stabilization_and_analytics_plan.md`; after post-audit
Sessions 01-03, the next default action is Session 04 / RM-612 unless the user explicitly chooses a
different session or Session 21 UI work. The user can start it by saying:

    Continue the post-audit stabilization plan.

Codex should then read the active post-audit ExecPlan and `docs/ROADMAP.md`, identify the first
incomplete or explicitly requested roadmap item, and guide the work without requiring the user to paste
the full kickoff text.

If a precise kickoff prompt is useful, use this:

    We are continuing `docs/exec_plans/2026-05-17_project_development_session_plan.md`.
    Work on the first incomplete post-audit stabilization item from `docs/ROADMAP.md`. Read `AGENTS.md`,
    `WORKFLOW.md`, `RULES.md`, `SPEC.md`, `TESTING.md`, `OUTPUTS.md`,
    `docs/audits/2026-05-17_post_session_deep_system_audit.md`, this ExecPlan, and the owning specs
    for that roadmap item.

Continue the new roadmap sequence one scoped workstream at a time. If a workstream discovers a material
contradiction, update this ExecPlan before continuing to the next session.

Sessions 21-22 (UI) remain independent and optional. Do not start them unless the user explicitly asks
for UI direction or implementation.

## Validation and Acceptance

For this plan itself, acceptance is documentation-level:

- The plan exists under `docs/exec_plans/`.
- The plan explains the current state, what is missing, what to fix first, and why.
- The plan lists future sessions with session-specific docs, questions, expected work, kickoff text,
  and validation.
- The plan states whether the existing documentation is enough for future context transfer and names
  the missing docs/specs that must be created.

For future sessions, acceptance is session-specific. A session is not complete until the changed files
are documented, the narrowest reliable verification has run, and any unverified area is reported.

## Idempotence and Recovery

This plan is safe to re-read and reuse. Future sessions should be safe if they keep changes scoped and
do not edit generated outputs unless explicitly required. If a future session is interrupted, resume by
reading this file, checking `Progress`, running `git status --short`, and inspecting only the files
owned by that session.

Do not revert unrelated dirty files. The current repository may already contain user or prior-agent
changes. Work with those changes if they affect the session; otherwise ignore them.

If two sessions appear to touch the same file, complete the earlier source-of-truth cleanup first, then
re-read the file before starting the later session.

## Artifacts and Notes

Audit items mapped to sessions:

- `AUD-001` maps to Session 01.
- `AUD-002` maps to Session 02.
- `AUD-003` maps to Session 03.
- `AUD-004` maps to Session 04.
- `AUD-005` maps to Session 01 and later docs cleanup if needed.
- `AUD-006` maps to Session 05.
- `AUD-007` maps to Session 01.
- `AUD-008` maps to Session 01.
- `AUD-009` maps to Session 06.
- `AUD-010` maps to Sessions 08 and 09.
- `AUD-011` maps to Sessions 10 through 15 because recommendation boundaries must stay explicit.
- `AUD-012` maps to Session 07.

Suggested immediate priority order:

1. Session 08
2. Session 09
3. Sessions 10 onward

Revision note, 2026-05-17: Session 03 was completed and the plan now points to Session 04 as the next
work item. This keeps the handoff state accurate for a fresh chat that resumes the project plan.

Revision note, 2026-05-17: Session 04 was completed and the plan now points to Session 05 as the next
work item. This keeps the handoff state accurate for a fresh chat that resumes the project plan.

Revision note, 2026-05-17: Session 05 was completed and the plan now points to Session 06 as the next
work item. This keeps the handoff state accurate for a fresh chat that resumes the project plan.

Revision note, 2026-05-17: Session 06 was completed and the plan now points to Session 07 as the next
work item. This keeps the handoff state accurate for a fresh chat that resumes the project plan.

Revision note, 2026-05-17: Session 07 was completed and the plan now points to Session 08 as the next
work item. This keeps the handoff state accurate for a fresh chat that resumes the project plan.

Revision note, 2026-05-17: Session 09 was completed (`src/candidate_comparison.py`, tests, wired
`run_compare_variants.py`). Next work item: Session 10 (Robustness Scorecard spec).

Revision note, 2026-05-17: Session 10 completed (`docs/specs/robustness_scorecard_spec.md`).
Next work item: Session 11 (implement scorecard and comparison diversification block).

Revision note, 2026-05-17: Session 11 completed (`src/robustness_scorecard.py`, comparison
`diversification`, tests). Next work item: Session 12 (Portfolio Health Score spec).

Revision note, 2026-05-17: Session 12 completed (`docs/specs/portfolio_health_score_spec.md`).
Next work item: Session 13 (implement health score + comparison `weight_concentration`).

Revision note, 2026-05-17: Session 13 completed (`src/portfolio_health_score.py`, comparison
`weight_concentration`, tests). Next work item: Session 14 (Selection Engine and No-Trade spec).

Revision note, 2026-05-17: Session 14 completed (`docs/specs/selection_engine_spec.md`,
`selection_decision_v1`). Next work item: Session 15 (implement Selection Engine and No-Trade).

Revision note, 2026-05-17: Session 08 was completed and the plan now points to Session 09 as the next
work item (implement `candidate_comparison.json` builder).

Revision note, 2026-05-17: Added **Phase 6 (Post-plan closure)** with four mandatory follow-ups after
Sessions 01–20: new audit vs concept and next stage; block-by-block improvements in scoped sessions;
extended mojibake/symbol sweep; Main vs robust optimizer input review with explicit change/no-change
decisions. Phase 6 requires an explicit user trigger and does not run automatically after Session 20.

Revision note, 2026-05-17: Phase 6 was completed as audit/triage in
`docs/audits/2026-05-17_post_session_deep_system_audit.md`. The next work should follow the
post-audit stabilization backlog in `docs/ROADMAP.md`.

## Interfaces and Dependencies

Future implementation sessions should prefer these stable module boundaries:

- Candidate comparison should be a shared builder module consumed by `run_compare_variants.py` and
  related CLI scripts, not a schema duplicated inside each entry point.
- Robustness Scorecard and Portfolio Health Score should consume canonical comparison artifacts or
  shared analytics outputs, not recompute metrics with parallel formulas.
- Selection Engine should consume candidate comparison and score artifacts, not diagnostic-only X-Ray
  text.
- Action/Rebalance should consume selected target weights plus current weights and should keep View
  After Optimization boundaries intact.
- Monitoring should compare generated analysis snapshots and expose explicit missing-prior-snapshot
  behavior.
- Decision Journal V1 should be generated-only unless a future spec deliberately defines a
  user-maintained source record.

Accepted V1 decision-pipeline spec files:

- `docs/specs/candidate_comparison_spec.md`
- `docs/specs/robustness_scorecard_spec.md`
- `docs/specs/portfolio_health_score_spec.md`
- `docs/specs/selection_engine_spec.md`
- `docs/specs/action_engine_spec.md`
- `docs/specs/monitoring_spec.md`
- `docs/specs/decision_journal_spec.md`

Accepted V1 generated decision artifacts:

- `candidate_comparison.json`
- `robustness_scorecard.json`
- `portfolio_health_score.json`
- `selection_decision.json`
- `action_plan.json`
- `monitoring_diff.json`
- `decision_journal.json`

These names are no longer proposals. They have owning specs and V1 implementations after Sessions
08-20. Future sessions may revise them only through the owning specs and tests.
