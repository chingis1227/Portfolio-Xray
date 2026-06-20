# Portfolio MRI Stabilization and Review Case Engine

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows `PLANS.md` from the repository root. A new contributor must be able to
resume work from this file alone, while still checking the current source-of-truth documents
before changing code, contracts, routes, generated-output policy, or QA gates.

## Purpose / Big Picture

Portfolio MRI already has a strong diagnosis-first product direction, but the 2026-06-19
inventory audit shows that the repository is not yet stable enough for broad architecture
work. The immediate user-facing risk is that release and agent workflows can rely on red or
ambiguous gates: FastAPI/frontend copy governance is failing, frontend lint is interactive,
the full pytest baseline is stale, generated portfolio outputs are tracked as source, and
route and language documentation has drifted.

After this plan is implemented, the project should have trustworthy daily and release QA
gates, generated artifacts separated from source, clean current documentation, and a staged
path toward a durable Review Case Engine. A Review Case Engine means that the system treats
one portfolio review as a durable case with a stable id, owner, stages, evidence, artifact
manifest, selected candidate, comparison, verdict, and report context instead of forcing the
frontend and API to infer current truth from scattered run-local files.

## Progress

- [x] (2026-06-19) Session 00 created this active stabilization ExecPlan, registered it in
  `docs/exec_plans/README.md`, linked the 2026-06-19 inventory audit to this plan, and passed
  the required docs, diff, and status validation.
- [x] (2026-06-19) Session 01 fixed the FastAPI/frontend governance gate by teaching the
  advice-language scanner to ignore JavaScript/TypeScript sanitizer regex literals while still
  scanning quoted public copy, replacing the visible comparison matrix `winner` wording, and
  validating the focused backend, frontend copy, typecheck, and browser QA gates.
- [x] (2026-06-19) Session 02 made frontend lint non-interactive by adding an explicit
  Next.js ESLint configuration and dev dependencies, then validated lint, typecheck, build, and
  frontend API route tests.
- [x] (2026-06-19) Session 03 refreshed the full pytest baseline, fixed three small regressions found by the first run, and recorded the green full-suite truth in QA docs.
- [x] (2026-06-19) Session 04 narrowed the exhaustive QA runner build-exit instability: standalone and post-run builds pass, but the long local static gate still records the build step as a known P1 failure after full pytest.
- [x] (2026-06-19) Session 05 inventoried the tracked generated-like portfolio
  artifact folders without deleting or untracking files, classified each target, and recorded the
  dependency evidence that Session 06 must respect.
- [x] (2026-06-19) Session 06 removed ordinary generated outputs from git tracking after dependency checks.
- [x] (2026-06-19) Session 07 fixed active-source mojibake in frontend display-label
  normalization and added dash-variant coverage for diagnostic section and block labels.
- [x] (2026-06-19) Session 08 normalized route documentation across compact product docs,
  contracts, frontend docs, design structure, and the vertical runbook.
- [x] (2026-06-19) Session 09 audited active and touched docs/plans for non-English text,
  mojibake markers, and machine-local absolute path traces; no active cleanup edits were needed
  beyond recording the result.
- [x] (2026-06-19) Session 10 cleaned current brand and terminology drift in active docs so
  current reference files lead with Portfolio MRI and old product names remain only as explicit
  legacy or compatibility aliases.
- [x] (2026-06-19) Session 11 established the trusted daily QA gate by adding the
  FastAPI/frontend governance command to `qa_fast` and validating the expanded gate.
- [x] (2026-06-19) Session 12 reran the local static release-readiness gate, recorded a current
  acceptance audit, and kept the remaining frontend production build runner failure visible as a
  P1 release-readiness blocker.
- [x] (2026-06-19) Session 13 introduced the first Review Case domain model in
  `src/review_case/`, wired initial staged `review_state_v1` creation through it, added focused
  domain tests, and synced architecture/staged-state docs without changing public routes or
  generated artifact schemas.
- [x] (2026-06-19) Session 14 added a run-local Review Case repository abstraction for
  `review_state.json`, covered typed load/save behavior with focused tests, and minimally wired new
  staged-review creation through the repository while preserving public `review_state_v1` behavior.
- [x] (2026-06-19) Session 15 added a narrow Review Case stage state machine for staged-review
  stage/status transitions, minimally wired the existing FastAPI stage-status helper through it, and
  preserved public routes, API envelopes, generated artifacts, and raw-state sanitization behavior.
- [x] (2026-06-19) Session 16 added a narrow Review Case artifact manifest abstraction for the
  existing staged `artifacts` map, minimally wired staged artifact-map refresh through it, and
  preserved the public `review_state_v1` artifacts map plus stage `artifact_refs` shape.
- [x] (2026-06-19) Session 17 added a narrow internal Review Case Evidence Graph abstraction for
  relating canonical stages, artifact manifest entries, and source evidence refs without changing
  public FastAPI routes, API envelopes, CLI commands, generated artifact schemas, or raw-state
  public sanitization compatibility.
- [x] (2026-06-19) Session 18 added a narrow internal Review Case screen read-model abstraction for
  projecting typed stage progress, artifact availability, and evidence links without changing
  public FastAPI routes, API envelopes, CLI commands, generated artifact schemas, or raw-state
  public sanitization compatibility.
- [x] (2026-06-19) Session 19 added a narrow frontend Review Case client-state helper for
  projecting staged progress into screen-ready stage progress, safe artifact availability, progress
  counts, and diagnosis-chain readiness without changing public FastAPI routes, API envelopes, CLI
  commands, generated artifact schemas, diagnosis-first behavior, or raw-state public sanitization
  compatibility.
- [x] (2026-06-20) Session 20 added a narrow FastAPI staged-review state helper in
  `src/api/staged_review_state.py` for `review_state.json` IO, owner checks, safe public status
  projection, missing-state envelopes, and legacy raw-ref sanitization while preserving public
  FastAPI routes, API envelopes, CLI commands, generated artifact schemas, diagnosis-first behavior,
  and raw-state public sanitization compatibility.
- [x] (2026-06-20) Session 21 added a narrow internal Review Case MarketDataSnapshot metadata
  seam in `src/review_case/market_data_snapshot.py` for summarizing existing run
  metadata/provider/data-policy evidence into a stable internal basis key without changing public
  FastAPI routes, API envelopes, CLI commands, generated artifact schemas, diagnosis-first
  behavior, calculation formulas, data providers, or raw-state public sanitization compatibility.
- [x] (2026-06-20) Session 22 added an inactive-by-default Review Case execution queue seam in
  `src/review_case/execution_queue.py`, wired FastAPI staged review start through it with the same
  in-process daemon-thread default, and added an opt-in RQ/Redis enqueue prototype with local
  fallback semantics without changing public FastAPI routes, API envelopes, CLI commands, generated
  artifact schemas, diagnosis-first behavior, calculation formulas, data providers, or raw-state
  public sanitization compatibility.
- [x] (2026-06-20) Session 23 hardened the inactive-by-default Review Case execution queue seam with
  validated internal queue configuration, bounded operational metadata/logging, safe queue-name and
  Redis URL handling, and focused RQ/Redis enqueue success and failure tests without changing public
  FastAPI routes, API envelopes, CLI commands, generated artifact schemas, diagnosis-first behavior,
  calculation formulas, data providers, or raw-state public sanitization compatibility.
- [x] (2026-06-20) Session 24 added an inactive-by-default Review Case artifact storage seam with
  run-local filesystem storage as the only active backend, safe future S3/R2 object-key validation,
  remote-backend configuration fallback metadata, minimal staged artifact-map wiring, focused tests,
  and docs sync without migrating generated artifacts or changing public contracts.
- [x] (2026-06-20) Session 25 added a behavior-preserving read-model migration step: FastAPI state
  helpers can project sanitized staged status into the internal Review Case screen read model, and
  frontend active-review compact progress now delegates staged status and stage-readiness projection
  to the Review Case client read-model helper without changing public contracts.
- [x] (2026-06-20) Session 26 added a behavior-preserving Review Case staged-status projection
  bundle: FastAPI state helpers now build the existing public staged status envelope and the
  internal screen read model as one paired projection, and the FastAPI status wrapper returns only
  the public envelope from that projection without changing public contracts.
- [x] (2026-06-20) Session 27 added a behavior-preserving Review Case stage-readiness helper:
  downstream candidate/comparison/verdict/report gates now read the existing raw staged state
  through `src/review_case/stage_readiness.py`, while FastAPI still returns the same
  `stage_not_ready` envelopes and public staged schemas.
- [x] (2026-06-20) Session 28 added a behavior-preserving Review Case downstream-lineage helper:
  candidate/comparison/verdict lineage validation now reads existing generated artifact dictionaries
  through `src/review_case/downstream_lineage.py`, while FastAPI wrappers still raise the same
  bridge errors that map to existing public safe-error envelopes and messages.
- [x] (2026-06-20) Session 29 added a behavior-preserving Review Case downstream evidence-chain
  context helper: comparison/verdict/report display context now reads existing generated artifact
  dictionaries through `src/review_case/downstream_context.py`, while FastAPI still returns the same
  public response envelopes and fields.
- [x] (2026-06-20) Session 30 completed the Review Case Engine architecture migration
  closeout by adding a focused package seam export test for the internal Review Case helpers,
  updating this living plan, and preserving public FastAPI routes, API envelopes, CLI commands,
  generated artifact schemas, diagnosis-first behavior, calculation formulas, data providers, and
  raw-state public sanitization compatibility.
- [x] (2026-06-20) Release-blocker follow-up fixed the P1 exhaustive-runner frontend
  production build blocker without creating a Session 31. The exhaustive QA runner now runs the
  frontend production build in an isolated `.next-qa-build` directory through a fresh child process,
  the local static gate completed `ready`, and the active known issue was removed.

## Surprises & Discoveries

- Observation: Session 00 starts from a worktree that already contains the user-created
  2026-06-19 audit file and audit-register edit.
  Evidence: `git status --short --branch` showed `M docs/audits/README.md` and
  `?? docs/audits/2026-06-19_deep_project_inventory_audit.md` before this plan was created.
- Observation: Session 01's initial FastAPI/frontend governance failure mixed real public copy
  drift with sanitizer false positives.
  Evidence: `scripts/verify_fastapi_contract_governance.py` flagged sanitizer regex patterns in
  `frontend/components/evidence/stressStoryModel.ts`, `frontend/lib/diagnosisDisplayModel.ts`,
  `frontend/lib/server/fastapiBridge.ts`, and `frontend/lib/siteExplanationPresenter.ts`, plus
  visible `winner` wording in `frontend/components/ui/MetricMatrix.tsx`.
- Observation: Headless Playwright visual QA scripts stored outside `frontend/` do not resolve
  the local `playwright` package by bare module name.
  Evidence: the first temporary visual QA script failed with `Cannot find module 'playwright'`;
  rerunning it with the package loaded from `frontend/node_modules` passed.
- Observation: Session 02's starting `npm.cmd run lint` did not fail cleanly; it opened the
  interactive Next.js ESLint setup prompt because the frontend had no checked-in ESLint
  configuration or ESLint dependencies.
  Evidence: the command printed `How would you like to configure ESLint?` with Strict/Base/Cancel
  choices.
- Observation: After explicit ESLint setup, lint and build pass but surface pre-existing warnings
  rather than errors.
  Evidence: `npm.cmd run lint` and `npm.cmd run build` both exited 0 while reporting
  `react-hooks/exhaustive-deps` and one `jsx-a11y/role-has-required-aria-props` warning in existing
  frontend files.
- Observation: Production dependency audit is not clean and cannot be fixed safely inside this
  lint session.
  Evidence: `npm.cmd audit --omit=dev` reported Next.js/PostCSS advisories and proposed
  `next@16.2.9` via `npm audit fix --force`, which is a breaking major upgrade. This is recorded
  in `KNOWN_ISSUES.md` as `KI-2026-06-19-001`.

- Observation: Session 03 collection succeeded and the first full pytest run exposed only three
  focused failures instead of the older 34-failure baseline.
  Evidence: `pytest --collect-only -q` collected 2007 tests in 10.46 seconds. The first
  `pytest -q` run failed after 12:24 with two site-explanation recommendation guardrail failures
  and one universe-ingestion warrant-cleaning failure.
- Observation: The site-explanation candidate recommendation guardrail regex and the universe
  ingestion warrant/unit name regexes contained malformed non-capturing-group fragments.
  Evidence: `_RECOMMENDATION_PATTERN` did not match `recommended`, so candidate copy was not
  rejected; `_WARRANT_NAME` did not match `Example Warrant`, so the fixture ticker `WARR` stayed
  in the cleaned universe. Focused tests passed after replacing those regexes with explicit
  `(?:...)`, `warrants?`, and `units?` forms.
- Observation: Session 04 reproduced the exhaustive runner build instability, but only inside the
  long QA gate after full pytest.
  Evidence: `output/qa_runs/20260619T123459Z/qa-summary.md` reports
  `passed_with_known_failures`, release readiness `not_ready`, and one P1 blocker:
  `Frontend production build` failed with exit `-1`. The per-step log
  `output/qa_runs/20260619T123459Z/logs/frontend-production-build.log` shows both attempts
  reaching `Collecting page data ...` and then exiting `-1` before static-page generation.
- Observation: The failure is not a general Next.js production-build failure and was not reproduced
  by a simple output-capture wrapper after the exhaustive run.
  Evidence: the prescribed standalone `cd frontend; npm.cmd run build` passed before the runner in
  about 45 seconds. After the runner, a direct build passed in about 34.7 seconds, and a PowerShell
  command using the same `2>&1 | ForEach-Object` capture pattern passed in about 35.2 seconds.
- Observation: Session 05 found that most tracked generated-like target folders are ordinary
  generated portfolio outputs, but `analysis_robust_mv_lambda_calibration/` is mixed because the
  runtime can read its default calibration file.
  Evidence: `rg -n "analysis_robust_mv_lambda_calibration" tests src scripts docs README.md
  OUTPUTS.md TESTING.md SPEC.md -S` found `src/robust_mv_lambda_resolve.py` defaulting to that
  directory and `src/candidate_robust_disclosure.py` documenting
  `analysis_robust_mv_lambda_calibration/selected_lambda.txt`, while tests use temporary
  calibration directories instead of requiring the tracked payload.
- Observation: Session 06 confirmed that untracking generated folders did not delete local
  calibration evidence.
  Evidence: after `git rm --cached`, `git ls-files` returned no tracked files for the target
  folders, while `analysis_robust_mv_lambda_calibration/selected_lambda.txt` still existed on
  disk and the folders were ignored by `.gitignore`.
- Observation: Session 07's targeted mojibake scan found one active-source issue and one
  historical-plan evidence line.
  Evidence: the targeted mojibake-marker search initially found `frontend/lib/displayLabels.ts`
  diagnostic section and block range regexes plus an old
  `docs/exec_plans/2026-06-18_ux_ui_product_audit_implementation_plan.md` cleanup-evidence line.
  After the fix, the same search found only the historical-plan evidence line.
- Observation: Session 08 route inspection found only one actual local sandbox page and no separate
  frontend `/debug` page.
  Evidence: the route-directory scan over `frontend/app` found `/sandbox/components`,
  `/onboarding/goals`, `/workspace`, `/client-profile`, and the Core MVP journey routes; debug
  behavior remains limited to developer provenance panels, compatibility helpers, API auth bypass,
  and operator tooling rather than a public route.
- Observation: Session 09 did not find active or touched Markdown files requiring content cleanup.
  Evidence: targeted scans over changed Markdown plus `AGENTS.md`, `RULES.md`, `WORKFLOW.md`,
  `PLANS.md`, `CHANGELOG.md`, and the active 2026-06-19 ExecPlan returned no Cyrillic, no
  mojibake-marker, and no machine-local absolute path hits after excluding normal web URLs.
- Observation: Session 10's live-brand drift was concentrated in active-document opening
  descriptions, diagnosis drill-down wording, and one legacy infrastructure project id.
  Evidence: targeted stale-brand searches over active docs found `Optimization Terminal` in top
  descriptions for `RULES.md`, `DATA.md`, `DECISIONS.md`, `WORKFLOW.md`, `TESTING.md`, and
  `GLOSSARY.md`; `Portfolio X-Ray & Optimization Terminal / Portfolio MRI` in `KNOWN_ISSUES.md`;
  `full X-Ray detail` style wording in design/screen docs; and Cloudflare project id
  `portfolio-xray` in `AGENTS.md`.
- Observation: Session 12 confirmed that the local static exhaustive gate is still not release-ready
  even after the Session 01-11 stabilization cleanup.
  Evidence: `output/qa_runs/20260619T152701Z/qa-summary.md` reports
  `passed_with_known_failures`, release readiness `not_ready`, full pytest
  `2004 passed, 3 skipped`, and one P1 blocker: `Frontend production build` failed both attempts
  with exit `-1` after `Collecting page data ...`.
- Observation: The Session 12 follow-up standalone frontend build probe did not produce a clean pass.
  Evidence: running `npm.cmd run build` from `frontend/` after the exhaustive gate timed out in the
  local tool wrapper and left exact Next.js build worker processes, which were stopped by process id.
  Treat this as inconclusive evidence requiring a clean standalone build rerun, not as proof that the
  build passes outside the runner.
- Observation: Session 13 found that initial staged review state was still assembled as a raw dict
  in `src/api/reviews.py`.
  Evidence: `_initial_staged_state` built the canonical stage map directly before Session 13 wired
  the same public `review_state_v1` shape through `src/review_case/ReviewCase`.
- Observation: Session 14 found that some staged API tests intentionally persist unsafe raw artifact
  refs to prove public status-response sanitization.
  Evidence: `tests/test_staged_review_api.py::test_get_staged_review_status_returns_safe_public_state`
  writes Windows absolute refs and expects the response mapper to replace them with `logical://...`.
  Therefore Session 14 kept raw compatibility reads and updates in `src/api/reviews.py` instead of
  forcing all existing state access through strict `ReviewCase` validation.
- Observation: Session 15 found that row-level stage transitions were still concentrated in the
  FastAPI `_set_stage_status` helper rather than the Review Case package.
  Evidence: `_set_stage_status` directly stamped `started_at`, `completed_at`, `status`,
  `artifact_refs`, and `current_stage`. Session 15 moved those rules into
  `src/review_case/stage_machine.py` while keeping the FastAPI artifact-ref sanitizer injected for
  raw compatibility.
- Observation: Session 16 found that safe artifact-ref validation already existed inside the
  Review Case domain, but the top-level staged `artifacts` map still had no named internal
  manifest abstraction.
  Evidence: `src/review_case/domain.py` validated artifact refs inline, while
  `src/api/reviews.py` refreshed `state["artifacts"]` with a raw dict comprehension over
  `STAGED_ARTIFACT_REFS`.
- Observation: Session 17 did not need FastAPI wiring to prove the Evidence Graph boundary.
  Evidence: `tests/test_review_case_evidence_graph.py` builds graph nodes and links from a
  `ReviewCase`, artifact manifest entries, and source refs, while staged API compatibility remains
  covered by the broader Review Case test run.
- Observation: Session 18 could project screen-ready stage progress and evidence without touching
  FastAPI status responses.
  Evidence: `tests/test_review_case_screen_read_model.py` builds a `ReviewCase` plus optional
  `ReviewCaseEvidenceGraph` and asserts the internal read model exposes progress counts, artifact
  availability, and evidence links while staged API compatibility remains covered separately.
- Observation: Session 19 could add a browser/client read-model projection without changing the
  staged status API or route screens.
  Evidence: `frontend/lib/review/reviewCaseClientState.ts` consumes the existing staged start/status
  shapes and compact stored progress, while `frontend/lib/reviewState.tsx` only delegates the
  diagnosis-chain readiness helper and keeps existing active-review storage keys and public route
  behavior unchanged. Focused frontend API/helper tests passed with 94 tests.
- Observation: Session 20 found that FastAPI state IO, owner checks, status projection, and
  missing-state envelope construction were still embedded in the large route adapter.
  Evidence: `src/api/reviews.py` owned `_write_staged_state`, `_read_staged_state`,
  `_read_authorized_staged_state`, `_public_staged_status_from_state`, and
  `_staged_status_not_found`; Session 20 moved those behaviors behind `src/api/staged_review_state.py`
  while retaining thin compatibility wrappers where existing tests and monkeypatches expect them.
- Observation: Session 21 found that Review Case evidence and screen read-model tests already used
  a generic `market_data_snapshot` evidence source, but there was no typed metadata object for the
  market-data basis behind that source.
  Evidence: `tests/test_review_case_evidence_graph.py` and
  `tests/test_review_case_screen_read_model.py` used `logical://market-data/yahoo` as an ad hoc
  source ref; Session 21 added `ReviewCaseMarketDataSnapshot` to build stable internal metadata from
  existing `run_metadata.json`, provider status, and `data_policy.json` evidence.
- Observation: Session 22 found that the staged FastAPI route already had a bounded in-process
  daemon-thread admission queue around `_run_staged_review_background`, so the safest RQ/Redis
  prototype was an internal adapter seam rather than a route rewrite.
  Evidence: `src/api/reviews.py` already used `_try_reserve_staged_worker_slot`,
  `_mark_staged_worker_started`, and `_release_staged_worker_slot`; Session 22 preserved that path
  as the default `in_process` backend and added RQ only behind `PMRI_REVIEW_CASE_QUEUE_BACKEND=rq`.
- Observation: Session 23 found that the initial RQ/Redis prototype returned raw exception text as
  the internal enqueue failure reason.
  Evidence: before Session 23, `RqRedisReviewCaseExecutionQueue.enqueue` built
  `reason=f"{type(exc).__name__}: {exc}"`; the hardened version now returns the bounded
  `rq_enqueue_failed` reason plus an internal `error_type` metadata field so backend logs remain
  inspectable without copying Redis URLs or credentials.
- Observation: Session 24 found that the existing top-level staged `artifacts` map already had a
  safe run-local manifest seam, so the storage adapter could stay very narrow.
  Evidence: `_refresh_staged_artifact_map` already built `ReviewCaseArtifactManifest` from
  `STAGED_ARTIFACT_REFS` and run-local existence checks. Session 24 replaced that construction with
  `run_local_review_case_artifact_storage().manifest_from_existing_refs(...)`, preserving the same
  public `dict[str, str]` shape.
- Observation: Session 25 found that the safe API migration point is the already-sanitized staged
  status response, not raw `review_state.json`.
  Evidence: `tests/test_fastapi_staged_review_state.py` now projects a raw state containing Windows
  absolute artifact refs through `public_staged_status_from_state(...)` and then into
  `ReviewCaseScreenReadModel`; the serialized read model contains only `logical://...` or run-local
  refs.
- Observation: Session 26 found that the next smallest safe migration step was not a new public
  field, but a paired internal projection object.
  Evidence: `ReviewCaseStatusProjection` in `src/api/staged_review_state.py` contains the existing
  `StagedReviewStatusResponse` plus the internal `ReviewCaseScreenReadModel`, and
  `src/api/reviews.py` still returns only `.public_status`.
- Observation: Session 27 found that downstream stage-readiness checks were still embedded in
  `src/api/reviews.py` as raw helper logic even after stage transitions had moved to the Review Case
  stage machine.
  Evidence: before Session 27, `_is_stage_completed` and `_assert_downstream_stage_ready` directly
  inspected `state["stages"]` and raised `ReviewAccessError`; after Session 27, they delegate to
  `src/review_case/stage_readiness.py` and preserve the same FastAPI error code and messages.
- Observation: Session 28 found that downstream artifact lineage was still mixed into the FastAPI
  adapter after readiness gates had moved into Review Case helpers.
  Evidence: `_candidate_lineage`, `_active_comparison_lineage`,
  `_active_verdict_lineage`, and `_comparison_has_displayable_evidence` in `src/api/reviews.py`
  still parsed generated artifact dictionaries directly. Session 28 moved those rules into
  `src/review_case/downstream_lineage.py` while preserving thin FastAPI wrappers and existing
  bridge-error messages.
- Observation: Session 29 found that downstream response display context was the next smallest
  remaining generated-dictionary parsing seam after lineage validation.
  Evidence: `_candidate_evidence_chain_context` in `src/api/reviews.py` still merged
  candidate/comparison/verdict/report context fields and fallback source-artifact lists directly.
  Session 29 moved that bounded projection into `src/review_case/downstream_context.py` while keeping
  the FastAPI wrapper responsible for returning the existing `DownstreamEvidenceChainContext`
  Pydantic model.
- Observation: Session 30 found no need for another runtime extraction after the Session 29
  downstream context helper.
  Evidence: the final closeout added `tests/test_review_case_architecture_seams.py`, which imports
  `src.review_case` and locks the expected internal seam export surface without touching FastAPI
  routes, response envelopes, CLI commands, generated artifacts, formulas, data providers, or
  frontend contracts.
- Observation: The P1 frontend production build blocker was caused by QA-runner process and build
  directory isolation, not by a deterministic Next.js application build failure.
  Evidence: direct and clean standalone builds passed, while the old exhaustive runner could fail
  after full pytest with exit `-1` or a stale `.next` `PageNotFoundError` when local Next.js dev
  servers were active. The fixed runner builds in `.next-qa-build` with `PMRI_NEXT_DIST_DIR` and
  `Start-Process`, and `output/qa_runs/20260620T093133Z/qa-summary.md` records `Frontend production
  build` as passed on the first attempt.

## Decision Log

- Decision: Use a stabilize-first migration order.
  Rationale: The project should not begin broad runtime, queue, storage, or frontend-state
  refactors while governance, lint, full-suite baseline, and generated-output hygiene are
  still unresolved.
  Date/Author: 2026-06-19 / Codex.
- Decision: Make this plan the active project-level plan and keep the Exhaustive QA System as
  paused release-readiness context.
  Rationale: The 2026-06-19 audit supersedes the prior documentation-only active plan as the
  current work driver, but the QA system remains important evidence and tooling for later
  sessions.
  Date/Author: 2026-06-19 / Codex.
- Decision: Choose RQ plus Redis as the first future queue prototype, with Celery or Temporal
  deferred until there is evidence that the simpler option is insufficient.
  Rationale: RQ is easier to introduce into the current Python/FastAPI stack and supports the
  first goal: moving heavy review execution out of the web request path behind an opt-in
  feature flag.
  Date/Author: 2026-06-19 / Codex.
- Decision: Use local filesystem-compatible storage first for artifact manifests, with an
  S3-compatible Cloudflare R2 adapter as the later production target.
  Rationale: This preserves local development and test behavior while creating a path away
  from raw generated files as the production source of UI truth.
  Date/Author: 2026-06-19 / Codex.
- Decision: Strip JavaScript/TypeScript regex literals before advice-language scanning instead
  of weakening the forbidden advice-like phrase list.
  Rationale: sanitizer and blacklist regexes must be allowed to contain phrases such as `best
  portfolio`, `must rebalance`, and `trade now`, but normal quoted public copy with those phrases
  must still fail the governance gate.
  Date/Author: 2026-06-19 / Codex.
- Decision: Keep lint as a configured frontend gate instead of removing it from official QA
  guidance.
  Rationale: Adding `frontend/.eslintrc.json` plus the Next.js ESLint dependencies is a small,
  localized change that makes `npm.cmd run lint` deterministic and preserves lint as a useful
  frontend implementation check. Removing lint from the official gate would have reduced coverage
  while leaving the interactive prompt unresolved.
  Date/Author: 2026-06-19 / Codex.

- Decision: Fix the three small full-suite regressions discovered during Session 03 instead of
  merely recording a failing baseline.
  Rationale: The failures were localized regex defects covered by existing tests, and fixing them
  made the full-suite baseline green without broad behavior changes.
  Date/Author: 2026-06-19 / Codex.
- Decision: Keep `KI-2026-06-14-001` open after Session 04 and treat the exhaustive local static
  gate as not release-ready while the frontend build step fails inside that runner.
  Rationale: The standalone and post-run build checks pass, but the actual release-candidate gate
  still records a known P1 build failure after full pytest. No deterministic runner code fix was
  proven in Session 04, so documenting the narrowed boundary is safer than marking the issue fixed.
  Date/Author: 2026-06-19 / Codex.
- Decision: Treat Session 05 as inventory-only and defer all untracking, moves, `.gitignore`
  changes, and fixture extraction to Session 06.
  Rationale: The portfolio output folders have hardcoded artifact-root names in runtime registries
  and specs, and `analysis_robust_mv_lambda_calibration/selected_lambda.txt` is a default runtime
  input. Removing tracked files safely requires a separate change that preserves those names as
  generated output paths while relocating or regenerating any needed fixture/input evidence.
  Date/Author: 2026-06-19 / Codex.
- Decision: Treat `analysis_robust_mv_lambda_calibration/` as generated local calibration output,
  not a checked-in source fixture.
  Rationale: Robust MV builders already support missing calibration by reporting no resolved lambda,
  and focused tests use temporary calibration directories. Keeping `selected_lambda.txt` as a
  tracked root artifact would preserve a hidden generated-state dependency. Operators must run
  `python run_robust_mv_lambda_calibration.py` or pass `--robust-mv-lambda` when Robust MV builders
  need a lambda in a fresh checkout.
  Date/Author: 2026-06-19 / Codex.
- Decision: Represent en dash and em dash label normalization with Unicode escape sequences in
  source and tests instead of literal non-ASCII dash characters.
  Rationale: The bug was caused by a corrupted dash range in a regular expression. Unicode escapes
  make the accepted dash forms explicit while keeping the repository text robust against encoding
  drift.
  Date/Author: 2026-06-19 / Codex.
- Decision: Document route reality by route purpose instead of treating every implemented route
  folder as part of the canonical user journey.
  Rationale: The current product path is the new-user route chain through Portfolio Input and the
  eight-step review rail. `/workspace` is a returning-user account branch, `/onboarding/goals` is
  compatibility-only, `/client-profile` is advanced/manual editing, and `/sandbox/components` plus
  developer/debug helpers are operator surfaces. Mixing those into one linear path was the route
  documentation drift Session 08 was created to fix.
  Date/Author: 2026-06-19 / Codex.
- Decision: Keep Session 09 scoped to active and touched documentation rather than rewriting
  historical audits or older plans wholesale.
  Rationale: The session goal is to remove active English-only/local-path violations without
  disturbing historical evidence. Targeted scans found no active/touched cleanup targets, so broad
  historical rewrites would add risk without improving the current source-of-truth set.
  Date/Author: 2026-06-19 / Codex.
- Decision: Keep `portfolio_xray.json`, `portfolio-xray`, and historical X-Ray decision/issue labels
  as compatibility or technical identifiers, but stop presenting old names as current product names
  in live reference introductions and UI hierarchy guidance.
  Rationale: Renaming runtime artifacts, infrastructure project ids, or historical audit labels would
  be a behavior and operations migration outside Session 10. The safe cleanup is to make active docs
  lead with Portfolio MRI and explicitly label old names where they still matter.
  Date/Author: 2026-06-19 / Codex.
- Decision: Promote `scripts/verify_fastapi_contract_governance.py` into `scripts/qa_fast.ps1`.
  Rationale: Session 01 made the FastAPI/frontend governance command green, and Session 11's goal is
  one trusted daily gate. Keeping the governance guard inside `qa_fast` prevents source, OpenAPI,
  screen-map, and public-copy drift from passing routine local QA while still avoiding full pytest,
  live E2E, frontend build, and browser checks.
  Date/Author: 2026-06-19 / Codex.
- Decision: Close Session 12 as an evidence-capture session while keeping release readiness blocked.
  Rationale: The requested Session 12 work was to rerun gates and record evidence, not to fix the
  known exhaustive-runner build instability. The gate produced honest current evidence and all other
  local static checks passed, but release readiness remains `not_ready` until the P1 build blocker is
  fixed and browser/staging gates are run when needed.
  Date/Author: 2026-06-19 / Codex.
- Decision: Continue Sessions 13-30 as separate local background sessions when cloud targets are not
  available.
  Rationale: The user explicitly replaced the previous cloud-only handoff constraint with a local
  execution instruction. The current local working tree contains many pre-existing uncommitted
  changes from Sessions 01-12, so each architecture session still needs an explicit handoff and must
  preserve unrelated dirty state.
  Date/Author: 2026-06-19 / Codex.
- Decision: Make Session 13 additive by introducing a Review Case domain seam before moving storage,
  stage transitions, or API modules.
  Rationale: The safest first architecture migration step is to centralize canonical stage order and
  safe run-local artifact reference validation while preserving `review_state_v1`, existing FastAPI
  envelopes, CLI commands, generated artifacts, and diagnosis-first behavior. Repository,
  state-machine, storage, and frontend migrations remain later sessions.
  Date/Author: 2026-06-19 / Codex.
- Decision: Keep the Session 14 repository strict for `ReviewCase` load/save but wire it into
  `src/api/reviews.py` only for initial staged-state creation.
  Rationale: A strict repository proves the new architecture seam can load and save safe
  `ReviewCase` objects around `review_state.json`, while existing raw-dict staged state paths still
  preserve compatibility behavior, including public sanitization of older or unsafe raw artifact
  refs. Broader read/update migration belongs to the later state-machine and API decomposition
  sessions.
  Date/Author: 2026-06-19 / Codex.
- Decision: Implement the Session 15 state machine as a narrow row-level transition helper instead
  of forcing every staged raw-dict read/update through full `ReviewCase` validation.
  Rationale: The new `ReviewCaseStageMachine` centralizes canonical stage/status validation and
  timestamp behavior, but accepts an injected artifact-ref sanitizer and leaves unrelated raw state
  untouched. This preserves existing public sanitization tests for older or unsafe artifact refs
  while moving transition rules out of the FastAPI module.
  Date/Author: 2026-06-19 / Codex.
- Decision: Keep the Session 16 artifact manifest strict for new Review Case architecture seams,
  but wire it into `src/api/reviews.py` only where the API builds the artifact map from known
  safe constants and run-local existence checks.
  Rationale: The manifest centralizes safe artifact keys and run-local refs without forcing old
  raw staged states through strict validation. Public status responses still use the existing
  sanitizer for legacy or unsafe artifact refs, so compatibility tests continue to prove safe
  public output.
  Date/Author: 2026-06-19 / Codex.
- Decision: Keep the Session 17 Evidence Graph internal and unwired to public FastAPI responses.
  Rationale: The session goal is to create an additive architecture seam that can relate stages,
  artifacts, and source evidence for later read-model work. Wiring it into status responses now
  would risk changing public envelopes or forcing old raw staged-state compatibility paths through
  stricter validation before the later migration sessions.
  Date/Author: 2026-06-19 / Codex.
- Decision: Keep the Session 18 screen read model internal and unwired to public FastAPI responses.
  Rationale: The new `ReviewCaseScreenReadModel` proves that future API/frontend migration can
  project stage progress, artifact availability, and evidence links from strict Review Case seams.
  Wiring it into the current status endpoint during this session would risk changing public
  envelopes or bypassing the existing raw-state sanitizer that protects older unsafe refs.
  Date/Author: 2026-06-19 / Codex.
- Decision: Keep the Session 19 frontend decomposition as a pure client helper plus a minimal
  readiness delegation, not a route-screen refactor.
  Rationale: The session goal is to give later screens a clearer browser/client seam for staged
  progress and read-model-like data. Wiring new UI fields or changing Next.js compatibility
  envelopes now would create migration risk and could bypass existing public sanitization tests.
  Date/Author: 2026-06-19 / Codex.
- Decision: Keep the Session 20 FastAPI decomposition as a state-helper extraction, not a route,
  worker, or generated-artifact refactor.
  Rationale: The public staged routes and raw-state compatibility tests are stable, while future
  Review Case work needs clearer internal seams. Moving `review_state.json` IO, owner checks, safe
  public status projection, and missing-state envelopes into `src/api/staged_review_state.py` reduces
  `src/api/reviews.py` responsibility without changing route envelopes or execution semantics.
  Date/Author: 2026-06-20 / Codex.
- Decision: Keep the Session 22 RQ/Redis prototype inactive by default and fallback-capable.
  Rationale: RQ and Redis are useful for later productionization, but making them mandatory would
  break default local operation and exceed the session scope. The prototype therefore imports RQ and
  Redis only when `PMRI_REVIEW_CASE_QUEUE_BACKEND` requests them, and it falls back to the existing
  in-process daemon-thread path if opt-in configuration or dependencies are unavailable.
  Date/Author: 2026-06-20 / Codex.
- Decision: Keep Session 23 queue productionization hardening internal-only.
  Rationale: Queue configuration validation and enqueue metadata are operational concerns for a
  later worker deployment. Exposing them through public staged start/status envelopes would create a
  contract migration outside Session 23 and could leak infrastructure details. The hardened seam
  therefore validates unsupported backend names, unsafe queue names, and unsupported Redis URL
  schemes internally, logs only bounded metadata, and preserves the existing public API behavior.
  Date/Author: 2026-06-20 / Codex.
- Decision: Keep Session 24 artifact storage run-local-only, even when future remote backend names
  are configured.
  Rationale: The session goal is groundwork, not an artifact migration. Treating S3/R2 settings as
  inactive intent with bounded metadata avoids cloud credential requirements, uploads, generated
  artifact schema changes, and public API contract changes while still establishing safe object-key
  and configuration validation for later work.
  Date/Author: 2026-06-20 / Codex.
- Decision: Migrate read-model usage through sanitized adapter outputs instead of exposing new read
  model fields in public FastAPI responses.
  Rationale: Session 25 needs to advance the API/frontend migration without changing route
  contracts. The backend helper therefore proves compatibility by building `ReviewCaseScreenReadModel`
  from the existing public-safe status response, and the frontend reuses the existing client
  read-model helper for compact progress and readiness while preserving the stored active-review
  shape.
  Date/Author: 2026-06-20 / Codex.
- Decision: Keep the Session 26 status projection bundle internal and return only the existing
  public staged status envelope from FastAPI routes.
  Rationale: Pairing the public status response and internal screen read model reduces duplicate
  projection work for later API migration, but exposing the read model now would change the public
  status contract. The safe architecture step is to prove both derive from the same sanitized data
  while preserving route envelopes.
  Date/Author: 2026-06-20 / Codex.
- Decision: Move downstream stage-readiness rules into a Review Case helper but keep FastAPI as the
  public error-envelope owner.
  Rationale: Session 27 should reduce `src/api/reviews.py` responsibility without changing public
  routes or response shapes. The new helper therefore reports internal `stage_not_ready` issues, and
  the existing FastAPI wrapper converts them to the same `ReviewAccessError` status code, code, and
  messages that public clients already receive.
  Date/Author: 2026-06-20 / Codex.
- Decision: Move downstream artifact-lineage validation into a Review Case helper but keep FastAPI
  bridge exception classes and public safe-error mapping unchanged.
  Rationale: Session 28 should continue reducing `src/api/reviews.py` responsibility after the
  stage-readiness extraction. Candidate, comparison, and verdict lineage rules can be validated from
  existing generated dictionaries inside `src/review_case/downstream_lineage.py`, while the FastAPI
  wrappers still translate internal lineage errors into `CandidateBridgeError`,
  `ComparisonBridgeError`, or `VerdictBridgeError` with the same messages used by current public
  envelopes.
  Date/Author: 2026-06-20 / Codex.
- Decision: Move downstream evidence-chain context projection into a Review Case helper but keep
  FastAPI Pydantic response models as the public envelope owner.
  Rationale: Session 29 should continue reducing `src/api/reviews.py` responsibility without
  changing comparison, verdict, or report response shapes. The new helper returns an internal
  dataclass that serializes to the same public field names, and the FastAPI wrapper still constructs
  the existing `DownstreamEvidenceChainContext` model before returning responses.
  Date/Author: 2026-06-20 / Codex.
- Decision: Close the Sessions 13-30 Review Case migration with an internal seam-surface test
  instead of starting another extraction.
  Rationale: After Session 29, the remaining safe closeout need is confidence that the extracted
  Review Case seams stay discoverable from the package boundary. A focused export test documents
  the migration surface without changing runtime routes, response envelopes, generated artifacts,
  formulas, data providers, or frontend contracts.
  Date/Author: 2026-06-20 / Codex.
- Decision: Fix the P1 exhaustive-runner frontend build blocker as a release-blocker follow-up,
  not as a new Review Case migration session.
  Rationale: Session 30 completed the architecture migration. The remaining blocker was a QA runner
  isolation problem: local dev servers can write the default `.next` directory while the exhaustive
  production build runs. Using an isolated `.next-qa-build` dist directory and a fresh child process
  fixes the release gate without changing frontend routes, UI behavior, FastAPI contracts, generated
  artifact schemas, formulas, or data providers.
  Date/Author: 2026-06-20 / Codex.

## Outcomes & Retrospective

Session 00 outcome: this plan is now the active stabilization handoff. No runtime code,
frontend code, backend code, formulas, API schemas, generated artifacts, or portfolio
calculations were changed in Session 00.

Validation evidence:

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    git diff --check
    no whitespace errors; Git printed line-ending normalization warnings only

    git status --short
     M docs/audits/README.md
     M docs/exec_plans/README.md
    ?? docs/audits/2026-06-19_deep_project_inventory_audit.md
    ?? docs/exec_plans/2026-06-19_project_stabilization_and_review_case_engine_plan.md

Session 01 outcome: the FastAPI/frontend governance gate now passes. The scanner still rejects
real public advice-like copy, as covered by the focused pytest case, but no longer fails on
frontend sanitizer regex literals. The comparison metric matrix no longer tells users to avoid
reading metrics as a portfolio `winner`; it now uses neutral ranking/instruction language.

Validation evidence:

    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    FastAPI contract governance OK.

    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_contract_governance.py -q
    4 passed

    cd frontend
    npm.cmd run test:copy
    tests 3; pass 3; fail 0

    cd frontend
    npm.cmd run typecheck
    tsc --noEmit completed successfully

    Browser QA
    Fresh local Next.js target: http://127.0.0.1:3219/comparison
    Browser state: fresh Playwright context, localStorage and sessionStorage cleared before
    seeding a Session 01 comparison fixture.
    Result: the replacement sentence `Read them as investor trade-offs, not as a ranking or
    instruction.` was visible, the old `not as a portfolio winner` matrix sentence was absent,
    and a screenshot was captured in the temporary directory. The local server was stopped after
    the check.

Session 02 outcome: frontend lint no longer opens the interactive Next.js setup prompt.
The frontend now has an explicit `frontend/.eslintrc.json` extending `next/core-web-vitals`, and
`frontend/package.json` / `frontend/package-lock.json` include the required ESLint dev
dependencies. QA documentation now treats `npm.cmd run lint` as a configured non-interactive
frontend gate, while `qa_fast` still intentionally skips lint until Session 11 revisits the daily
gate.

Validation evidence:

    cd frontend
    npm.cmd run lint
    next lint completed with exit code 0; existing warnings only

    cd frontend
    npm.cmd run typecheck
    tsc --noEmit completed successfully

    cd frontend
    npm.cmd run build
    next build completed successfully; existing lint warnings only

    cd frontend
    npm.cmd run test:api
    tests 91; pass 91; fail 0

    cd frontend
    npm.cmd run test:smoke
    tests 1; pass 1; fail 0

Additional evidence and residual risk:

    cd frontend
    npm.cmd audit --omit=dev
    failed with 2 production dependency audit findings and proposed a breaking Next.js 16 upgrade

The audit finding is out of scope for Session 02 and is recorded as `KI-2026-06-19-001`.

Session 03 outcome: the repository full pytest baseline is green again. The first full run found
three localized regressions: two site-explanation recommendation guardrail failures and one
universe-ingestion warrant-cleaning failure. Session 03 fixed the malformed regexes in
`src/site_explanation_bundle.py` and `src/universe_ingestion.py`, then compacted the stale
full-suite known-issue baseline in `KNOWN_ISSUES.md`, `TESTING.md`, and `docs/contracts/QA_CONTRACT.md`.

Validation evidence:

    .\.venv\Scripts\python.exe -m pytest --collect-only -q
    2007 tests collected in 10.46s

    .\.venv\Scripts\python.exe -m pytest tests\test_site_explanation_candidate_comparison_verdict.py::test_site_explanation_populates_candidate_hierarchy_without_recommendation_language tests\test_site_explanation_guardrails.py::test_site_explanation_candidate_copy_cannot_be_recommendation tests\test_universe_ingestion.py::test_cleaning_removes_test_and_warrants -q
    3 passed in 0.34s

    .\.venv\Scripts\python.exe -m pytest -q
    2004 passed, 3 skipped in 590.85s (0:09:50)

Session 04 outcome: the exhaustive QA runner instability was narrowed but not repaired. The
frontend production build is green when run standalone, but the release-candidate local static
gate still records `Frontend production build` as a known P1 failure after full pytest. The issue
therefore remains open in `KNOWN_ISSUES.md` as `KI-2026-06-14-001`, and
`.\scripts\qa_exhaustive.cmd -LocalOnly -SkipLive` is not release-ready until this step passes
inside the runner.

Validation evidence:

    cd frontend
    npm.cmd run build
    next build completed successfully in about 45 seconds; existing lint warnings only

    .\scripts\qa_exhaustive.cmd -LocalOnly -SkipLive
    exit code 0 from the wrapper after about 785.9 seconds
    qa summary status: passed_with_known_failures
    release readiness: not_ready
    full backend pytest inside the runner: 2004 passed, 3 skipped in 573.92s
    frontend production build: failed, known_failure, exit -1 after two attempts
    evidence: output/qa_runs/20260619T123459Z/qa-summary.md
    evidence: output/qa_runs/20260619T123459Z/logs/frontend-production-build.log

    cd frontend
    npm.cmd run build
    DIRECT_BUILD_EXIT=0 ELAPSED_SECONDS=34.7

    cd frontend
    npm.cmd run build through the same PowerShell output-capture pattern used by Invoke-QaCommand
    CAPTURE_BUILD_EXIT=0 ELAPSED_SECONDS=35.2

Session 05 outcome: the tracked generated-like portfolio artifact folders were inventoried and no
files were deleted, moved, or untracked. The search scope was `tests src scripts docs README.md
OUTPUTS.md TESTING.md SPEC.md`, matching the Session 05 instruction.

Classification evidence:

| Target folder | Tracked files | Approx. bytes | Classification | Dependency finding |
| --- | ---: | ---: | --- | --- |
| `hierarchical risk parity portfolio/` | 30 | 3,651,577 | Removable generated output | Runtime/specs name it as an artifact root; tests and golden fixtures assert the path string, but no test requires the tracked payload files. |
| `minimum cvar constrained portfolio/` | 30 | 3,671,495 | Removable generated output | Runtime/specs name it as an artifact root; tests create temporary folders by this name and do not require the tracked payload. |
| `minimum cvar uncapped portfolio/` | 30 | 3,601,052 | Removable generated output | Runtime/specs name it as an artifact root; golden fixtures assert the path string, but no direct dependency on tracked payload files was found. |
| `maximum diversification unconstrained portfolio/` | 30 | 3,637,774 | Removable generated output | Runtime/specs name it as an artifact root; golden fixtures assert the path string, but no direct dependency on tracked payload files was found. |
| `risk budget by asset portfolio/` | 30 | 3,647,852 | Removable generated output | Runtime/specs name it as an artifact root; tests create temporary folders by this name and do not require the tracked payload. |
| `risk budget by asset-class portfolio/` | 30 | 3,650,817 | Removable generated output | Runtime/specs name it as an artifact root; golden fixtures assert the path string, but no direct dependency on tracked payload files was found. |
| `robust mean variance constrained portfolio/` | 30 | 3,663,518 | Removable generated output | Runtime/specs name it as an artifact root; tests create temporary folders by this name and do not require the tracked payload. |
| `robust mean variance uncapped portfolio/` | 30 | 3,604,457 | Removable generated output | Runtime/specs name it as an artifact root; golden fixtures assert the path string, but no direct dependency on tracked payload files was found. |
| `analysis_mv_lambda_sensitivity/` | 13 | 7,290,666 | Legacy generated artifact | Only the 2026-06-19 inventory audit referenced the folder in the searched scope; no code or test dependency was found. |
| `analysis_robust_mv_lambda_calibration/` | 28 | 3,571,929 | Legacy generated artifact with a runtime input dependency | Code and docs reference `analysis_robust_mv_lambda_calibration/selected_lambda.txt` as the default Robust MV calibration input. Session 06 must preserve, relocate, or regenerate that input before untracking the folder wholesale. |
 
Validation evidence:

    git status --short
    showed the pre-existing uncommitted Session 00-04 changes plus this active ExecPlan change;
    no generated artifact files were changed by Session 05

    git ls-files
    confirmed the 10 tracked generated-like target folders above

    rg -n "<folder-name>" tests src scripts docs README.md OUTPUTS.md TESTING.md SPEC.md -S
    was run for each target folder above; findings are summarized in the table

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    git diff --check
    no whitespace errors; Git printed line-ending normalization warnings only

Session 06 outcome: ordinary generated portfolio output folders and legacy Robust MV
calibration/sensitivity output folders are no longer tracked as source. Local files were not
deleted; the repository now ignores these generated folders, and `OUTPUTS.md` plus
`docs/specs/robust_mv_spec.md` clarify that Robust MV calibration artifacts are generated local
outputs rather than fixtures. No runtime artifact-root strings were changed.

Untracked-from-source targets:

- `hierarchical risk parity portfolio/`
- `minimum cvar constrained portfolio/`
- `minimum cvar uncapped portfolio/`
- `maximum diversification unconstrained portfolio/`
- `risk budget by asset portfolio/`
- `risk budget by asset-class portfolio/`
- `robust mean variance constrained portfolio/`
- `robust mean variance uncapped portfolio/`
- `analysis_mv_lambda_sensitivity/`
- `analysis_robust_mv_lambda_calibration/`

Validation evidence:

    git ls-files -- <target folders>
    returned no tracked files for the ten Session 06 target folders

    Test-Path analysis_robust_mv_lambda_calibration\selected_lambda.txt
    True; local generated calibration file remained on disk after untracking

    .\.venv\Scripts\python.exe -m pytest tests\test_robust_mv_calibration.py tests\test_candidate_factory.py::test_robust_mv_lambda_disclosure_missing_calibration tests\test_candidate_factory.py::test_robust_mv_lambda_disclosure_from_calibration_file tests\test_candidate_comparison.py::test_robust_mv_construction_disclosure_lambda_without_factory_run -q
    18 passed in 4.21s

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    .\scripts\qa_fast.cmd
    Fast QA gate passed: docs verification OK, staged route guard passed, backend fast offline pytest
    81 passed, frontend typecheck passed, frontend API route tests 91 passed

    git diff --check
    no whitespace errors; Git printed line-ending normalization warnings only

Session 07 outcome: active frontend display-label source no longer contains the corrupted dash
range in diagnostic section and block label normalization. `frontend/lib/displayLabels.ts` now
accepts ASCII hyphen, en dash, and em dash forms through explicit Unicode escapes, and
`frontend/tests/api-route-tests.cjs` covers those forms for both `diagnostic section(s)` and
`block(s)` labels. The only remaining mojibake-marker search hit is an older historical ExecPlan
line that documents pre-existing cleanup evidence and was intentionally left for Session 09 or a
future historical-doc cleanup.

Validation evidence:

    cd frontend
    node --test tests/api-route-tests.cjs --test-name-pattern "display labels normalize diagnostic section"
    tests 92; pass 92; fail 0

    cd frontend
    npm.cmd run typecheck
    tsc --noEmit completed successfully

    cd frontend
    npm.cmd run test:copy
    tests 3; pass 3; fail 0

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    targeted mojibake-marker search over active source and docs
    remaining hit: historical cleanup-evidence line in
    docs/exec_plans/2026-06-18_ux_ui_product_audit_implementation_plan.md

Session 08 outcome: route documentation now distinguishes the canonical new-user path, the
returning-user `/workspace` account branch, the compatibility-only `/onboarding/goals` redirect,
advanced/manual `/client-profile`, and sandbox/debug routes. The synced docs are `AGENTS.md`,
`PRODUCT.md`, `docs/contracts/PRODUCT_FLOW_CONTRACT.md`,
`docs/contracts/SCREEN_CONTRACTS.md`, `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md`,
`docs/specs/frontend_screen_contracts.md`, `docs/design/current_website_structure.md`,
`frontend/README.md`, and `docs/demo/frontend_backend_vertical_runbook.md`. `CHANGELOG.md` records
the completed docs normalization.

Validation evidence:

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    targeted stale route searches over active route docs
    no matches for stale route-chain headings, old linear Workspace path wording, old Goals
    onboarding-step wording, or the old Goals render-success wording

    targeted route classification search over active route docs
    confirmed `/workspace`, `/onboarding/goals`, `/client-profile`, `/sandbox/components`,
    `dev_bypass`, developer provenance, and `/auth/callback` are classified as account branch,
    compatibility, advanced/manual, sandbox/debug, local preview, developer-only, or technical
    callback routes as appropriate

    git diff --check
    no whitespace errors; Git printed line-ending normalization warnings only

Session 09 outcome: active and touched Markdown documentation was audited for English-only,
mojibake, and machine-local absolute path hygiene. The scan covered changed Markdown files plus
`AGENTS.md`, `RULES.md`, `WORKFLOW.md`, `PLANS.md`, `CHANGELOG.md`, and this active ExecPlan. No
Cyrillic text, mojibake markers, or local absolute path traces were found in that scoped set after
excluding normal web URLs, so no historical audits or older plans were rewritten. `CHANGELOG.md`
records the completed documentation hygiene audit.

Validation evidence:

    targeted Cyrillic scan over active/touched Markdown
    no matches

    targeted mojibake-marker scan over active/touched Markdown
    no matches

    targeted machine-local absolute path scan over active/touched Markdown, excluding web URLs
    no matches

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    git diff --check
    no whitespace errors; Git printed line-ending normalization warnings only

Session 10 outcome: live brand and terminology drift was cleaned in active docs without changing
runtime behavior, routes, artifact names, or generated-output tracking. Root reference docs now
lead with Portfolio MRI and label `Optimization Terminal` as an old compatibility name. The
known-issues register leads with Portfolio MRI and labels `Portfolio X-Ray` and `Optimization
Terminal` as compatibility names. Design and screen hierarchy docs now refer to legacy technical
`portfolio_xray.json` detail instead of presenting X-Ray as current product UI terminology. The
Cloudflare `portfolio-xray` project id remains documented as a legacy infrastructure id.

Validation evidence:

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    targeted stale-brand search over active docs
    no matches for stale live-brand patterns that present old product names as current names or
    use X-Ray as current first-read UI terminology

    broader legacy-name search over active docs
    remaining hits are classified as explicit compatibility aliases, the legacy infrastructure
    id `portfolio-xray`, stable technical artifact identifiers such as `portfolio_xray.json`, or
    historical decision/known-issue labels

    git diff --check
    no whitespace errors; Git printed line-ending normalization warnings only

Session 11 outcome: the trusted fast daily QA gate now includes the FastAPI/frontend contract
governance command. `scripts/qa_fast.ps1` runs docs verification, staged Run Diagnosis route
compatibility, FastAPI/frontend governance, focused backend offline pytest, frontend typecheck,
and frontend API route tests. `TESTING.md` and `docs/contracts/QA_CONTRACT.md` now describe that
expanded canonical daily coverage.

Validation evidence:

    .\scripts\qa_fast.cmd
    Fast QA gate passed.

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    git diff --check
    no whitespace errors; Git printed line-ending normalization warnings only

Session 12 outcome: the stabilization phase has a current local static release-readiness audit, but
the product is not release-ready. `.\scripts\qa_exhaustive.cmd -LocalOnly -SkipLive` completed with
status `passed_with_known_failures` and release readiness `not_ready`. The gate passed environment
readiness, local FastAPI staged OpenAPI, fast daily QA, contract QA, FastAPI governance, focused
FastAPI public contract pytest, full backend pytest, frontend typecheck, frontend API route tests,
frontend smoke tests, docs verification, docs link pytest, Supabase compact Client Fit pytest, and
Supabase compact/privacy frontend API rows. Full pytest passed with `2004 passed, 3 skipped` in
666.78 seconds. The only blocker was the known P1 `Frontend production build` runner failure:
both build attempts exited `-1` after `Collecting page data ...`. Browser vertical QA was skipped
because `-SkipLive` was supplied.

Validation evidence:

    .\scripts\qa_exhaustive.cmd -LocalOnly -SkipLive
    output/qa_runs/20260619T152701Z/qa-summary.md
    status: passed_with_known_failures
    release readiness: not_ready
    P0/P1/P2 blockers: 0/1/0

    output/qa_runs/20260619T152701Z/qa-release-readiness.md
    QA-FRONTEND-PRODUCTION-BUILD
    Severity: P1
    Classification: known_failure

    cd frontend
    npm.cmd run build
    inconclusive: timed out in the local tool wrapper and left Next.js build worker processes

Session 13 outcome: the first Review Case domain boundary now exists in `src/review_case/`.
`src/api/reviews.py` still writes the public `review_state_v1` schema, but initial staged state is
created through `ReviewCase.initial(...)` so canonical stage order and safe artifact-reference rules
are no longer only raw API-module dict logic. `tests/test_review_case_domain.py` covers initial
state shape, round-tripping the existing staged-state fields, and rejection of unsafe artifact refs.
`ARCHITECTURE.md`, `docs/contracts/STAGED_REVIEW_STATE_CONTRACT.md`, and `CHANGELOG.md` were synced.

Validation evidence:

    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_domain.py tests\test_staged_review_api.py -q
    14 passed

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    git diff --check
    no whitespace errors; Git printed line-ending normalization warnings only

Session 14 outcome: `src/review_case/repository.py` now provides a run-local repository seam around
`review_state.json`. It can save a `ReviewCase` atomically as the existing `review_state_v1` JSON,
load it back into the domain model, return `None` for missing optional state, and reject invalid JSON
or wrong schema versions. `src/api/reviews.py` now saves newly created staged reviews through this
repository, then continues to use the existing raw-dict read/update paths for compatibility.
`tests/test_review_case_repository.py` covers the repository behavior, and `ARCHITECTURE.md`,
`docs/contracts/STAGED_REVIEW_STATE_CONTRACT.md`, and `CHANGELOG.md` were synced.

Validation evidence:

    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_repository.py -q
    4 passed

    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_staged_review_api.py -q
    18 passed

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    git diff --check
    no whitespace errors; Git printed line-ending normalization warnings only

Session 15 outcome: `src/review_case/stage_machine.py` now provides the narrow state-machine seam
for row-level staged-review transitions. It validates canonical stage names and stage statuses,
preserves existing `started_at`, stamps terminal statuses with `completed_at`, sanitizes artifact
refs through an injected adapter, and updates `current_stage` without parsing or rejecting the whole
raw staged-state dictionary. `src/api/reviews.py` now delegates `_set_stage_status` to this seam,
preserving public FastAPI routes, response envelopes, CLI behavior, generated artifact schemas, and
the existing raw-state public sanitization compatibility tests. `ARCHITECTURE.md`,
`docs/contracts/STAGED_REVIEW_STATE_CONTRACT.md`, and `CHANGELOG.md` were synced.

Validation evidence:

    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_stage_machine.py -q
    5 passed

    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_staged_review_api.py -q
    23 passed

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    git diff --check
    no whitespace errors; Git printed line-ending normalization warnings only

Session 16 outcome: `src/review_case/artifact_manifest.py` now provides the narrow manifest seam
for Review Case artifact keys and refs. It validates stable artifact keys, accepts safe run-local or
`logical://` refs, builds a manifest from existing run-local refs, and serializes back to the same
public `review_state_v1` `artifacts` map. `ReviewCase` now reuses this manifest validation, and
`src/api/reviews.py` uses it only when refreshing the staged artifact map from known constants and
existing files. Stage-level `artifact_refs`, public routes, API envelopes, CLI commands, generated
artifact schemas, diagnosis-first behavior, and old raw-state public sanitization compatibility were
preserved. `ARCHITECTURE.md`, `docs/contracts/STAGED_REVIEW_STATE_CONTRACT.md`, and `CHANGELOG.md`
were synced.

Validation evidence:

    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py -q
    19 passed

    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_staged_review_api.py -q
    36 passed

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    git diff --check
    no whitespace errors; Git printed line-ending normalization warnings only

Session 17 outcome: `src/review_case/evidence_graph.py` now provides the narrow internal Evidence
Graph seam for Review Case architecture work. It creates stable stage, artifact, and source nodes;
validates safe run-local or `logical://` refs; and validates links such as stage-to-artifact,
stage-to-source, and artifact-to-source without adding fields to `review_state_v1` or changing
FastAPI routes, response envelopes, CLI commands, generated artifact schemas, diagnosis-first
behavior, or old raw-state public sanitization compatibility. `ARCHITECTURE.md`,
`docs/contracts/STAGED_REVIEW_STATE_CONTRACT.md`, and `CHANGELOG.md` were synced.

Validation evidence:

    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_evidence_graph.py -q
    8 passed

    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_evidence_graph.py tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_staged_review_api.py -q
    44 passed

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    git diff --check
    no whitespace errors; Git printed line-ending normalization warnings only

Session 18 outcome: `src/review_case/screen_read_model.py` now provides the narrow internal screen
read-model seam for Review Case architecture work. It projects a typed `ReviewCase` and optional
`ReviewCaseEvidenceGraph` into stage progress, artifact availability, and evidence links for future
API/frontend migration. It remains unwired to FastAPI, so public routes, response envelopes, CLI
commands, generated artifact schemas, diagnosis-first behavior, and old raw-state public
sanitization compatibility are unchanged. `ARCHITECTURE.md`,
`docs/contracts/STAGED_REVIEW_STATE_CONTRACT.md`, and `CHANGELOG.md` were synced.

Validation evidence:

    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_screen_read_model.py -q
    3 passed

    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_screen_read_model.py tests\test_review_case_evidence_graph.py tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_staged_review_api.py -q
    47 passed

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    git diff --check
    no whitespace errors; Git printed line-ending normalization warnings only

Session 19 outcome: `frontend/lib/review/reviewCaseClientState.ts` now provides the narrow frontend
client-state seam for Review Case migration work. It consumes the existing staged start/status
shapes and compact stored progress, then projects `review_case_client_state_v1` with ordered stage
progress, progress counts, safe artifact availability, and diagnosis-chain readiness.
`frontend/lib/reviewState.tsx` keeps the old active-review storage and public state shape, but
delegates `diagnosisStageChainReady` to the new helper. No public FastAPI routes, API envelopes,
CLI commands, generated artifact schemas, diagnosis-first behavior, or raw-state public
sanitization compatibility changed. `ARCHITECTURE.md`,
`docs/contracts/STAGED_REVIEW_STATE_CONTRACT.md`, `frontend/README.md`, and `CHANGELOG.md` were
synced.

Validation evidence:

    cd frontend
    node --test tests/api-route-tests.cjs --test-name-pattern "review case client state|active review state exposes"
    94 passed

    cd frontend
    npm.cmd run test:api
    94 passed

    cd frontend
    npm.cmd run typecheck
    tsc --noEmit completed successfully

    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_screen_read_model.py tests\test_review_case_evidence_graph.py tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_staged_review_api.py -q
    47 passed

    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    FastAPI contract governance OK.

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    git diff --check
    no whitespace errors; Git printed line-ending normalization warnings only

Session 20 outcome: `src/api/staged_review_state.py` now provides the narrow FastAPI-adjacent
state seam for Review Case migration work. It centralizes run-local `review_state.json` reads and
writes, schema checks, owner authorization, public staged status projection, missing-state envelopes,
and legacy raw artifact-ref sanitization. `src/api/reviews.py` still owns FastAPI routes, staged
execution, downstream actions, and thin compatibility wrappers used by existing tests, so public
routes, API envelopes, CLI commands, generated artifact schemas, diagnosis-first behavior, and
raw-state public sanitization compatibility remain unchanged. `ARCHITECTURE.md`,
`docs/contracts/STAGED_REVIEW_STATE_CONTRACT.md`, and `CHANGELOG.md` were synced.

Validation evidence:

    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_staged_review_state.py tests\test_staged_review_api.py -q
    12 passed

    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_staged_review_state.py tests\test_review_case_screen_read_model.py tests\test_review_case_evidence_graph.py tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_staged_review_api.py -q
    51 passed

    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    FastAPI contract governance OK.

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    git diff --check
    no whitespace errors; Git printed line-ending normalization warnings only

Session 21 outcome: `src/review_case/market_data_snapshot.py` now provides a narrow internal
MarketDataSnapshot metadata seam for Review Case migration work. It summarizes existing
`run_metadata.json`, staged provider status, and `data_policy.json` evidence into
`review_case_market_data_snapshot_v1`, including a stable metadata `basis_key` and logical evidence
source ref. This is not a raw price-panel fingerprint and does not fetch providers, alter formulas,
change public FastAPI routes or envelopes, add fields to `review_state_v1`, change CLI commands, or
change generated artifact schemas. `ARCHITECTURE.md`,
`docs/contracts/STAGED_REVIEW_STATE_CONTRACT.md`, `CHANGELOG.md`, and this ExecPlan were synced.

Validation evidence:

    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_market_data_snapshot.py -q
    3 passed

    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_market_data_snapshot.py tests\test_review_case_screen_read_model.py tests\test_review_case_evidence_graph.py tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_fastapi_staged_review_state.py tests\test_staged_review_api.py -q
    54 passed

    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    FastAPI contract governance OK.

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    git diff --check
    no whitespace errors; Git printed line-ending normalization warnings only

Session 22 outcome: `src/review_case/execution_queue.py` now provides the narrow internal Review
Case execution queue seam for staged diagnosis work. The default backend remains the same
in-process daemon-thread behavior that `src/api/reviews.py` already used. Operators can explicitly
prototype RQ plus Redis with `PMRI_REVIEW_CASE_QUEUE_BACKEND=rq` and
`PMRI_REVIEW_CASE_REDIS_URL` or `REDIS_URL`; RQ and Redis are optional imports, and missing
configuration or dependencies fall back to the in-process path. Public FastAPI routes, API
envelopes, CLI commands, generated artifact schemas, diagnosis-first behavior, calculation
formulas, data providers, and raw-state public sanitization compatibility remain unchanged.
`ARCHITECTURE.md`, `docs/contracts/STAGED_REVIEW_STATE_CONTRACT.md`, `CHANGELOG.md`, and this
ExecPlan were synced.

Validation evidence:

    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_execution_queue.py -q
    5 passed

    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_execution_queue.py tests\test_review_case_market_data_snapshot.py tests\test_review_case_screen_read_model.py tests\test_review_case_evidence_graph.py tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_fastapi_staged_review_state.py tests\test_staged_review_api.py -q
    59 passed

    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py::test_staged_review_queue_limit_returns_429 tests\test_fastapi_app.py::test_staged_worker_reservation_allows_bounded_waiting_queue -q
    2 passed

    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    FastAPI contract governance OK.

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    git diff --check
    no whitespace errors; Git printed line-ending normalization warnings only

Session 23 outcome: the inactive-by-default Review Case execution queue seam is now safer to
inspect and configure for a later real RQ worker deployment. `src/review_case/execution_queue.py`
validates queue backend names, queue names, Redis URL presence, and Redis URL schemes into safe
internal defaults or warnings. RQ enqueue failures now return bounded reason codes and error-type
metadata instead of raw exception text, and successful RQ enqueues include bounded internal metadata
such as queue name and TTL settings. `src/api/reviews.py` logs those internal metadata objects only
for RQ success or fallback events. Public FastAPI routes, API envelopes, CLI commands, generated
artifact schemas, diagnosis-first behavior, calculation formulas, data providers, and raw-state
public sanitization compatibility remain unchanged. `ARCHITECTURE.md`,
`docs/contracts/STAGED_REVIEW_STATE_CONTRACT.md`, `CHANGELOG.md`, and this ExecPlan were synced.

Validation evidence:

    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_execution_queue.py -q
    11 passed

    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_execution_queue.py tests\test_review_case_market_data_snapshot.py tests\test_review_case_screen_read_model.py tests\test_review_case_evidence_graph.py tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_fastapi_staged_review_state.py tests\test_staged_review_api.py -q
    65 passed

    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py::test_staged_review_queue_limit_returns_429 tests\test_fastapi_app.py::test_staged_worker_reservation_allows_bounded_waiting_queue -q
    2 passed

    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    FastAPI contract governance OK.

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    git diff --check
    no whitespace errors; Git printed line-ending normalization warnings only

Session 24 outcome: `src/review_case/artifact_storage.py` now provides the inactive-by-default
artifact storage seam for Review Case architecture work. The only active adapter is
`RunLocalReviewCaseArtifactStorage`, which builds manifests from existing run-local files and returns
the same public staged `artifacts` map shape. Future S3-compatible or Cloudflare R2 settings are
recognized only as inactive intent and fall back to run-local behavior with safe internal metadata.
The module validates future object-key prefixes, review ids, and artifact refs without uploading,
copying, renaming, or migrating generated artifacts. `src/api/reviews.py` uses the run-local storage
adapter only where it already refreshed the top-level staged artifact map. Public FastAPI routes, API
envelopes, CLI commands, generated artifact schemas, diagnosis-first behavior, calculation formulas,
data providers, and raw-state public sanitization compatibility remain unchanged. `ARCHITECTURE.md`,
`docs/contracts/STAGED_REVIEW_STATE_CONTRACT.md`, `CHANGELOG.md`, and this ExecPlan were synced.

Validation evidence:

    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_artifact_storage.py -q
    11 passed

    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_artifact_storage.py tests\test_review_case_execution_queue.py tests\test_review_case_market_data_snapshot.py tests\test_review_case_screen_read_model.py tests\test_review_case_evidence_graph.py tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_fastapi_staged_review_state.py tests\test_staged_review_api.py -q
    76 passed

    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    FastAPI contract governance OK.

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    git diff --check
    no whitespace errors; Git printed line-ending normalization warnings only

Session 25 outcome: the Review Case read-model migration advanced without changing public contracts.
`src/api/staged_review_state.py` can now project the existing public-safe staged status response into
`ReviewCaseScreenReadModel`, proving that legacy raw refs are sanitized before strict read-model
projection. `frontend/lib/reviewState.tsx` now compacts staged status and checks stage readiness
through `frontend/lib/review/reviewCaseClientState.ts` instead of duplicating readiness and artifact
safety rules. Public FastAPI routes, API envelopes, CLI commands, generated artifact schemas,
diagnosis-first behavior, calculation formulas, data providers, and raw-state public sanitization
compatibility remain unchanged. `ARCHITECTURE.md`,
`docs/contracts/STAGED_REVIEW_STATE_CONTRACT.md`, `CHANGELOG.md`, and this ExecPlan were synced.

Validation evidence:

    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_staged_review_state.py -q
    6 passed

    cd frontend
    node --test tests/api-route-tests.cjs --test-name-pattern "active review state compacts staged status|review case client state helper projects staged status"
    95 passed

    cd frontend
    npm.cmd run typecheck
    tsc --noEmit completed successfully

    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_staged_review_state.py tests\test_review_case_screen_read_model.py tests\test_review_case_artifact_storage.py tests\test_review_case_execution_queue.py tests\test_review_case_market_data_snapshot.py tests\test_review_case_evidence_graph.py tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_staged_review_api.py -q
    78 passed

    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    FastAPI contract governance OK.

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    git diff --check
    no whitespace errors; Git printed line-ending normalization warnings only

Session 26 outcome: the Review Case status projection seam advanced without changing public
contracts. `src/api/staged_review_state.py` now exposes `ReviewCaseStatusProjection`, which pairs
the existing sanitized `StagedReviewStatusResponse` with the internal
`ReviewCaseScreenReadModel`. `src/api/reviews.py` uses that paired projection internally but still
returns only the existing public staged status response. Public FastAPI routes, API envelopes, CLI
commands, generated artifact schemas, diagnosis-first behavior, calculation formulas, data
providers, and raw-state public sanitization compatibility remain unchanged. `ARCHITECTURE.md`,
`docs/contracts/STAGED_REVIEW_STATE_CONTRACT.md`, `CHANGELOG.md`, and this ExecPlan were synced.

Validation evidence:

    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_staged_review_state.py -q
    8 passed

    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_staged_review_state.py tests\test_review_case_screen_read_model.py tests\test_review_case_artifact_storage.py tests\test_review_case_execution_queue.py tests\test_review_case_market_data_snapshot.py tests\test_review_case_evidence_graph.py tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_staged_review_api.py -q
    80 passed

    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    FastAPI contract governance OK.

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    git diff --check
    no whitespace errors; Git printed line-ending normalization warnings only

Session 27 outcome: the Review Case downstream stage-readiness seam advanced without changing public
contracts. `src/review_case/stage_readiness.py` now owns the internal readiness checks for explicit
candidate/comparison/verdict/report gates against the existing raw staged-state dictionary.
`src/api/reviews.py` keeps thin compatibility wrappers, so public FastAPI routes still return the
same `stage_not_ready` safe-error envelopes and messages. Public FastAPI routes, API envelopes, CLI
commands, generated artifact schemas, diagnosis-first behavior, calculation formulas, data
providers, and raw-state public sanitization compatibility remain unchanged. `ARCHITECTURE.md`,
`docs/contracts/STAGED_REVIEW_STATE_CONTRACT.md`, `CHANGELOG.md`, and this ExecPlan were synced.

Validation evidence:

    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_stage_readiness.py tests\test_fastapi_app.py::test_generate_candidate_requires_completed_launchpad_builder_stage tests\test_fastapi_app.py::test_downstream_stage_rejects_before_previous_stage_is_complete -q
    7 passed

    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_stage_readiness.py tests\test_fastapi_staged_review_state.py tests\test_review_case_screen_read_model.py tests\test_review_case_artifact_storage.py tests\test_review_case_execution_queue.py tests\test_review_case_market_data_snapshot.py tests\test_review_case_evidence_graph.py tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_staged_review_api.py tests\test_fastapi_app.py::test_generate_candidate_requires_completed_launchpad_builder_stage tests\test_fastapi_app.py::test_downstream_stage_rejects_before_previous_stage_is_complete -q
    87 passed

    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    FastAPI contract governance OK.

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    git diff --check
    no whitespace errors; Git printed line-ending normalization warnings only

Session 28 outcome: the Review Case downstream artifact-lineage seam advanced without changing
public contracts. `src/review_case/downstream_lineage.py` now owns internal validation for active
candidate, current-vs-candidate comparison, and Decision Verdict consistency over the existing
generated artifact dictionaries. `src/api/reviews.py` keeps thin wrappers that read the same
run-local JSON files and re-raise existing FastAPI bridge errors, so public routes, API envelopes,
CLI commands, generated artifact schemas, diagnosis-first behavior, calculation formulas, data
providers, and raw-state public sanitization compatibility remain unchanged. `ARCHITECTURE.md`,
`docs/contracts/STAGED_REVIEW_STATE_CONTRACT.md`, `CHANGELOG.md`, and this ExecPlan were synced.

Validation evidence:

    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_downstream_lineage.py -q
    8 passed

    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_downstream_lineage.py tests\test_review_case_stage_readiness.py tests\test_fastapi_staged_review_state.py tests\test_review_case_screen_read_model.py tests\test_review_case_artifact_storage.py tests\test_review_case_execution_queue.py tests\test_review_case_market_data_snapshot.py tests\test_review_case_evidence_graph.py tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_staged_review_api.py tests\test_fastapi_app.py::test_run_comparison_runs_adapter_and_returns_public_envelope tests\test_fastapi_app.py::test_run_comparison_blocks_when_no_displayable_evidence tests\test_fastapi_app.py::test_run_comparison_requires_selected_candidate_display_row tests\test_fastapi_app.py::test_generate_verdict_runs_adapter_and_returns_public_envelope tests\test_fastapi_app.py::test_generate_verdict_rejects_partial_comparison_artifact tests\test_fastapi_app.py::test_generate_verdict_rejects_stale_comparison_candidate_row tests\test_fastapi_app.py::test_generate_report_runs_adapter_and_returns_grounded_preview tests\test_fastapi_app.py::test_generate_report_rejects_stale_comparison_before_writer_runs tests\test_fastapi_app.py::test_generate_report_rejects_missing_displayable_comparison_evidence -q
    102 passed

    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    FastAPI contract governance OK.

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    git diff --check
    no whitespace errors; Git printed line-ending normalization warnings only

Session 29 outcome: the Review Case downstream evidence-chain context seam advanced without
changing public contracts. `src/review_case/downstream_context.py` now owns the bounded projection
that links comparison, verdict, and report responses back to selected diagnosis evidence using the
existing generated artifact dictionaries. `src/api/reviews.py` keeps a thin wrapper that converts the
internal dataclass into the existing public `DownstreamEvidenceChainContext` Pydantic model, so public
FastAPI routes, API envelopes, CLI commands, generated artifact schemas, diagnosis-first behavior,
calculation formulas, data providers, and raw-state public sanitization compatibility remain
unchanged. `ARCHITECTURE.md`, `docs/contracts/STAGED_REVIEW_STATE_CONTRACT.md`, `CHANGELOG.md`, and
this ExecPlan were synced.

Validation evidence:

    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_downstream_context.py -q
    4 passed

    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_downstream_context.py tests\test_review_case_downstream_lineage.py tests\test_review_case_stage_readiness.py tests\test_fastapi_staged_review_state.py tests\test_review_case_screen_read_model.py tests\test_review_case_artifact_storage.py tests\test_review_case_execution_queue.py tests\test_review_case_market_data_snapshot.py tests\test_review_case_evidence_graph.py tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_staged_review_api.py tests\test_fastapi_app.py::test_run_comparison_runs_adapter_and_returns_public_envelope tests\test_fastapi_app.py::test_generate_verdict_runs_adapter_and_returns_public_envelope tests\test_fastapi_app.py::test_generate_report_runs_adapter_and_returns_grounded_preview -q
    100 passed

    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    FastAPI contract governance OK.

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    git diff --check
    no whitespace errors; Git printed line-ending normalization warnings only

Session 30 outcome: the Sessions 13-30 Review Case architecture migration closeout is complete.
`tests/test_review_case_architecture_seams.py` documents the extracted internal seam surface by
asserting that the package boundary exports the domain, repository, stage-machine, artifact
manifest, Evidence Graph, screen read-model, MarketDataSnapshot, execution queue, artifact storage,
stage readiness, downstream lineage, and downstream evidence-chain context helpers created across
the migration sessions. This is a test-only closeout step; public FastAPI routes, API envelopes, CLI
commands, generated artifact schemas, diagnosis-first behavior, calculation formulas, data
providers, frontend contracts, and raw-state public sanitization compatibility remain unchanged.
`CHANGELOG.md` and this ExecPlan were synced.

Validation evidence:

    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_architecture_seams.py -q
    1 passed

    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_architecture_seams.py tests\test_review_case_downstream_context.py tests\test_review_case_downstream_lineage.py tests\test_review_case_stage_readiness.py tests\test_fastapi_staged_review_state.py tests\test_review_case_screen_read_model.py tests\test_review_case_artifact_storage.py tests\test_review_case_execution_queue.py tests\test_review_case_market_data_snapshot.py tests\test_review_case_evidence_graph.py tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_staged_review_api.py tests\test_fastapi_app.py::test_run_comparison_runs_adapter_and_returns_public_envelope tests\test_fastapi_app.py::test_generate_verdict_runs_adapter_and_returns_public_envelope tests\test_fastapi_app.py::test_generate_report_runs_adapter_and_returns_grounded_preview -q
    101 passed

    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    FastAPI contract governance OK.

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    git diff --check
    no whitespace errors; Git printed line-ending normalization warnings only

Release-blocker follow-up outcome: the known P1 frontend production build runner blocker is fixed.
`scripts/qa_exhaustive.ps1` now runs the frontend production build through `Start-Process` with
redirected logs and sets `PMRI_NEXT_DIST_DIR=.next-qa-build` only for that step. `frontend/next.config.mjs`
uses that environment variable as an opt-in build directory, `frontend/tsconfig.json` includes the
QA build types directory so Next.js does not mutate the config during QA, and `.gitignore` excludes
`.next-qa-build/` as generated output. The fix avoids sharing `.next` with active local dev servers
and removes the old known-failure classification from the build step. `KNOWN_ISSUES.md`,
`TESTING.md`, `docs/contracts/QA_CONTRACT.md`, `CHANGELOG.md`, and this ExecPlan were synced. This
is not Session 31 and does not change product routes, UI behavior, FastAPI contracts, CLI commands,
generated artifact schemas, formulas, or data providers.

Validation evidence:

    clean standalone build with PMRI_NEXT_DIST_DIR=.next-qa-build
    npm.cmd run build passed

    .\scripts\qa_exhaustive.cmd -LocalOnly -SkipLive
    output/qa_runs/20260620T093133Z/qa-summary.md
    status: passed
    release readiness: ready
    P0/P1/P2 blockers: 0/0/0
    full backend pytest: 2094 passed, 3 skipped in 830.96 seconds
    Frontend production build: passed on first attempt in 73.9 seconds

## Context and Orientation

Portfolio MRI is a diagnosis-first, current-portfolio-first investment decision-support
system. The current product flow starts from the user's current portfolio, diagnoses the
portfolio, tests stress behavior, uses Client Fit as bounded non-binding context, tests one
candidate hypothesis when appropriate, compares current versus candidate evidence, and then
produces a non-binding Decision Verdict and grounded report context.

The origin audit for this plan is
`docs/audits/2026-06-19_deep_project_inventory_audit.md`. It found the following high-impact
issues: the FastAPI/frontend governance command is red; `npm run lint` is interactive; the
full pytest baseline is stale; generated-like portfolio output folders are tracked as
source; active frontend source contains mojibake; route documentation has drift; checked-in
plans contain some non-English or machine-local path traces; current docs still contain some
legacy product naming; and ignored local log and PID files make operator inspection noisy.

The current release QA tooling is described in
`docs/exec_plans/2026-06-14_exhaustive_qa_system_plan.md`, `TESTING.md`, and
`docs/contracts/QA_CONTRACT.md`. The active product and documentation rules are governed by
`AGENTS.md`, `RULES.md`, `WORKFLOW.md`, `SPEC.md`, `OUTPUTS.md`, `TESTING.md`, and the
contracts under `docs/contracts/`.

Generated outputs are run evidence, not source, unless a task explicitly targets them.
Examples include `output/`, `runs/`, `cache/`, `Main portfolio/`, portfolio variant folders,
PDF folders, generated CSV/TXT/HTML/PNG/PDF sidecars, and `portfolio_weights.yml`.

## Plan of Work

Sessions 01-12 are stabilization sessions. They must be completed before architecture
migration unless a remaining issue is explicitly accepted in `KNOWN_ISSUES.md`, this plan,
and the final response of the session that accepts it.

Session 01 fixes the P0 FastAPI/frontend governance gate. Run
`.\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py`, repair the
current advice-like phrase failures, and keep the scanner strong enough to catch real public
copy violations. The known starting point is that several matches are sanitizer or blacklist
patterns, while one visible UI phrase says users should not read metrics as a portfolio
winner.

Session 02 makes frontend lint non-interactive or removes it from official QA gates. The
preferred implementation is an explicit ESLint configuration compatible with the current
Next.js 14 project. If that is too invasive, the accepted fallback is to document that
typecheck, build, API tests, smoke tests, and copy tests are the official frontend gates, and
that `lint` is not a CI gate until configured.

Session 03 refreshes full pytest truth. Run collection and a full suite in a dedicated long
window. If the suite times out, capture elapsed time and last visible evidence, then update
`KNOWN_ISSUES.md` with an honest current baseline. Do not claim full-suite green unless the
suite actually completes green.

Session 04 repairs or narrows `KI-2026-06-14-001`, where the exhaustive QA runner can record
frontend build exit `-1` after full pytest even though the standalone build passes. Reproduce
with `.\scripts\qa_exhaustive.cmd -LocalOnly -SkipLive`, isolate command ordering and process
capture, and keep `.next` writers sequential on Windows.

Session 05 inventories tracked generated-like portfolio artifacts before deletion. Classify
each target folder as a source fixture, audit evidence, legacy generated artifact, or
removable generated output. Search code, tests, and docs for direct dependencies before any
removal.

Session 06 removes ordinary generated outputs from git tracking only after Session 05 proves
dependency safety. Use `git rm --cached` rather than deleting local files unless the user
explicitly approves deletion. Move any true fixtures under explicit fixture paths and expand
`.gitignore` so future generated variants are not added accidentally.

Session 07 fixes active-source mojibake, especially in `frontend/lib/displayLabels.ts`, and
adds focused coverage for diagnostic section and block label normalization across ASCII
hyphen, en dash, and em dash forms.

Session 08 normalizes route documentation. The docs must distinguish the canonical new-user
path, returning-user `/workspace` branch, compatibility-only `/onboarding/goals` redirect,
advanced/manual `/client-profile`, and sandbox/debug routes.

Session 09 cleans non-English and local absolute path traces from active or touched docs and
plans. Do not rewrite old historical audits wholesale unless they are active source material
for this plan.

Session 10 cleans live brand and terminology drift so current docs lead with Portfolio MRI
and keep old names only as explicit historical or compatibility aliases.

Session 11 establishes one trusted daily QA gate. `qa_fast` should pass or document exact
known exceptions, and it should include the governance command after Session 01 is fixed.

Session 12 reruns release-readiness gates after the P0/P1 cleanup, records the generated QA
evidence, updates `KNOWN_ISSUES.md`, and writes a short acceptance audit under `docs/audits/`.

Sessions 13-30 are architecture migration sessions. They introduce the Review Case domain
model, a repository abstraction, a stage state machine, artifact manifest, Evidence Graph,
screen read models, frontend state decomposition, FastAPI reviews module decomposition,
MarketDataSnapshot metadata, an opt-in RQ plus Redis queue prototype, queue productionization,
R2-compatible artifact storage, frontend migration to read models, Core/Advanced/Legacy code
separation, observability, staging readiness, and final closeout. These sessions must not
start until Sessions 01-12 are complete or explicitly accepted as residual risk.

## Concrete Steps

All commands are run from the repository root unless a step says otherwise. Use Windows
PowerShell by default. Prefer `.\.venv\Scripts\python.exe` for Python commands when the
virtual environment exists.

Session 00 commands:

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check
    git status --short

Session 01 commands:

    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_contract_governance.py -q
    cd frontend
    npm.cmd run test:copy
    npm.cmd run typecheck

Session 02 commands:

    cd frontend
    npm.cmd run lint
    npm.cmd run typecheck
    npm.cmd run build
    npm.cmd run test:api

Session 03 commands:

    .\.venv\Scripts\python.exe -m pytest --collect-only -q
    .\.venv\Scripts\python.exe -m pytest -q

If the full suite times out, record the timeout and update `KNOWN_ISSUES.md`; do not hide the
failed attempt.

Session 04 commands:

    cd frontend
    npm.cmd run build
    cd ..
    .\scripts\qa_exhaustive.cmd -LocalOnly -SkipLive

Session 05 commands:

    git ls-files
    rg -n "<folder-name>" tests src scripts docs README.md OUTPUTS.md TESTING.md SPEC.md -S
    .\.venv\Scripts\python.exe scripts\verify_docs.py

Replace `<folder-name>` with each generated-like folder being classified.

Session 05 executed those commands for these target folders:

    hierarchical risk parity portfolio
    minimum cvar constrained portfolio
    minimum cvar uncapped portfolio
    maximum diversification unconstrained portfolio
    risk budget by asset portfolio
    risk budget by asset-class portfolio
    robust mean variance constrained portfolio
    robust mean variance uncapped portfolio
    analysis_mv_lambda_sensitivity
    analysis_robust_mv_lambda_calibration

Session 06 commands:

    git ls-files
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    .\scripts\qa_fast.cmd

Session 07 commands:

    targeted mojibake-marker search over active source and docs
    cd frontend
    node --test tests/api-route-tests.cjs --test-name-pattern "display labels normalize diagnostic section"
    npm.cmd run typecheck
    npm.cmd run test:copy
    cd ..
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Session 08 commands:

    route-directory scan over frontend/app
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    targeted stale route searches over active route docs
    targeted route classification search over active route docs
    git diff --check

Session 09 commands:

    git status --short
    targeted Cyrillic scan over active/touched Markdown
    targeted mojibake-marker scan over active/touched Markdown
    targeted machine-local absolute path scan over active/touched Markdown, excluding web URLs
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Session 10 commands:

    git status --short
    targeted stale-brand and terminology searches over active docs
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    targeted stale-brand and terminology searches over active docs
    git diff --check

Session 11 commands:

    git status --short
    .\scripts\qa_fast.cmd
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Session 12 commands:

    git status --short
    .\scripts\qa_exhaustive.cmd -LocalOnly -SkipLive
    cd frontend
    npm.cmd run build
    cd ..
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check
    git status --short

The standalone frontend build probe in Session 12 was inconclusive because it timed out in the local
tool wrapper and left Next.js build worker processes. Future verification must rerun a clean
standalone build in a fresh shell before deciding whether `KI-2026-06-14-001` is still runner-only.

Session 13 commands:

    git status --short
    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_domain.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_domain.py tests\test_staged_review_api.py -q
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Session 14 commands:

    git status --short
    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_repository.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_staged_review_api.py -q
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Session 15 commands:

    git status --short
    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_stage_machine.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_staged_review_api.py -q
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Session 16 commands:

    git status --short
    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_staged_review_api.py -q
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Session 17 commands:

    git status --short
    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_evidence_graph.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_evidence_graph.py tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_staged_review_api.py -q
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Session 18 commands:

    git status --short
    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_screen_read_model.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_screen_read_model.py tests\test_review_case_evidence_graph.py tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_staged_review_api.py -q
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Session 19 commands:

    git status --short
    cd frontend
    node --test tests/api-route-tests.cjs --test-name-pattern "review case client state|active review state exposes"
    npm.cmd run test:api
    npm.cmd run typecheck
    cd ..
    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_screen_read_model.py tests\test_review_case_evidence_graph.py tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_staged_review_api.py -q
    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Session 20 commands:

    git status --short
    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_staged_review_state.py tests\test_staged_review_api.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_staged_review_state.py tests\test_review_case_screen_read_model.py tests\test_review_case_evidence_graph.py tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_staged_review_api.py -q
    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Session 21 commands:

    git status --short
    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_market_data_snapshot.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_market_data_snapshot.py tests\test_review_case_screen_read_model.py tests\test_review_case_evidence_graph.py tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_fastapi_staged_review_state.py tests\test_staged_review_api.py -q
    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Session 22 commands:

    git status --short
    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_execution_queue.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_execution_queue.py tests\test_review_case_market_data_snapshot.py tests\test_review_case_screen_read_model.py tests\test_review_case_evidence_graph.py tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_fastapi_staged_review_state.py tests\test_staged_review_api.py -q
    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Session 23 commands:

    git status --short
    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_execution_queue.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_execution_queue.py tests\test_review_case_market_data_snapshot.py tests\test_review_case_screen_read_model.py tests\test_review_case_evidence_graph.py tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_fastapi_staged_review_state.py tests\test_staged_review_api.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py::test_staged_review_queue_limit_returns_429 tests\test_fastapi_app.py::test_staged_worker_reservation_allows_bounded_waiting_queue -q
    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Session 24 commands:

    git status --short
    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_artifact_storage.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_artifact_storage.py tests\test_review_case_execution_queue.py tests\test_review_case_market_data_snapshot.py tests\test_review_case_screen_read_model.py tests\test_review_case_evidence_graph.py tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_fastapi_staged_review_state.py tests\test_staged_review_api.py -q
    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Session 25 commands:

    git status --short
    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_staged_review_state.py -q
    cd frontend
    node --test tests/api-route-tests.cjs --test-name-pattern "active review state compacts staged status|review case client state helper projects staged status"
    npm.cmd run typecheck
    cd ..
    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_staged_review_state.py tests\test_review_case_screen_read_model.py tests\test_review_case_artifact_storage.py tests\test_review_case_execution_queue.py tests\test_review_case_market_data_snapshot.py tests\test_review_case_evidence_graph.py tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_staged_review_api.py -q
    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Session 26 commands:

    git status --short
    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_staged_review_state.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_staged_review_state.py tests\test_review_case_screen_read_model.py tests\test_review_case_artifact_storage.py tests\test_review_case_execution_queue.py tests\test_review_case_market_data_snapshot.py tests\test_review_case_evidence_graph.py tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_staged_review_api.py -q
    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Session 27 commands:

    git status --short
    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_stage_readiness.py tests\test_fastapi_app.py::test_generate_candidate_requires_completed_launchpad_builder_stage tests\test_fastapi_app.py::test_downstream_stage_rejects_before_previous_stage_is_complete -q
    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_stage_readiness.py tests\test_fastapi_staged_review_state.py tests\test_review_case_screen_read_model.py tests\test_review_case_artifact_storage.py tests\test_review_case_execution_queue.py tests\test_review_case_market_data_snapshot.py tests\test_review_case_evidence_graph.py tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_staged_review_api.py tests\test_fastapi_app.py::test_generate_candidate_requires_completed_launchpad_builder_stage tests\test_fastapi_app.py::test_downstream_stage_rejects_before_previous_stage_is_complete -q
    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Session 28 commands:

    git status --short
    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_downstream_lineage.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_downstream_lineage.py tests\test_review_case_stage_readiness.py tests\test_fastapi_staged_review_state.py tests\test_review_case_screen_read_model.py tests\test_review_case_artifact_storage.py tests\test_review_case_execution_queue.py tests\test_review_case_market_data_snapshot.py tests\test_review_case_evidence_graph.py tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_staged_review_api.py tests\test_fastapi_app.py::test_run_comparison_runs_adapter_and_returns_public_envelope tests\test_fastapi_app.py::test_run_comparison_blocks_when_no_displayable_evidence tests\test_fastapi_app.py::test_run_comparison_requires_selected_candidate_display_row tests\test_fastapi_app.py::test_generate_verdict_runs_adapter_and_returns_public_envelope tests\test_fastapi_app.py::test_generate_verdict_rejects_partial_comparison_artifact tests\test_fastapi_app.py::test_generate_verdict_rejects_stale_comparison_candidate_row tests\test_fastapi_app.py::test_generate_report_runs_adapter_and_returns_grounded_preview tests\test_fastapi_app.py::test_generate_report_rejects_stale_comparison_before_writer_runs tests\test_fastapi_app.py::test_generate_report_rejects_missing_displayable_comparison_evidence -q
    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Session 29 commands:

    git status --short
    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_downstream_context.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_downstream_context.py tests\test_review_case_downstream_lineage.py tests\test_review_case_stage_readiness.py tests\test_fastapi_staged_review_state.py tests\test_review_case_screen_read_model.py tests\test_review_case_artifact_storage.py tests\test_review_case_execution_queue.py tests\test_review_case_market_data_snapshot.py tests\test_review_case_evidence_graph.py tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_staged_review_api.py tests\test_fastapi_app.py::test_run_comparison_runs_adapter_and_returns_public_envelope tests\test_fastapi_app.py::test_generate_verdict_runs_adapter_and_returns_public_envelope tests\test_fastapi_app.py::test_generate_report_runs_adapter_and_returns_grounded_preview -q
    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Session 30 commands:

    git status --short
    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_architecture_seams.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_review_case_architecture_seams.py tests\test_review_case_downstream_context.py tests\test_review_case_downstream_lineage.py tests\test_review_case_stage_readiness.py tests\test_fastapi_staged_review_state.py tests\test_review_case_screen_read_model.py tests\test_review_case_artifact_storage.py tests\test_review_case_execution_queue.py tests\test_review_case_market_data_snapshot.py tests\test_review_case_evidence_graph.py tests\test_review_case_artifact_manifest.py tests\test_review_case_domain.py tests\test_review_case_repository.py tests\test_review_case_stage_machine.py tests\test_staged_review_api.py tests\test_fastapi_app.py::test_run_comparison_runs_adapter_and_returns_public_envelope tests\test_fastapi_app.py::test_generate_verdict_runs_adapter_and_returns_public_envelope tests\test_fastapi_app.py::test_generate_report_runs_adapter_and_returns_grounded_preview -q
    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Release-blocker follow-up commands:

    git status --short
    clean standalone build with PMRI_NEXT_DIST_DIR=.next-qa-build
    .\scripts\qa_exhaustive.cmd -LocalOnly -SkipLive
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check

Session 13 and later local handoff command pattern:

    Use the Codex thread tool to create a separate local background thread or local worktree thread
    for the next session when only local project targets are available. The handoff prompt must
    include this plan path, the Session 12 audit path, the dirty-tree warning, and the instruction to
    implement only that one session before creating the following local background session.

Architecture sessions must add their own focused tests before implementation and must update
this section as they proceed.

## Validation and Acceptance

Session 00 is accepted when this plan exists, the ExecPlan register points to it as the active
plan, the 2026-06-19 audit register row links to it as follow-up, docs verification passes,
`git diff --check` has no whitespace errors, and `git status --short` shows only intentional
changes plus any pre-existing user audit changes.

Session 01 is accepted when the FastAPI/frontend governance command passes and the scanner
still catches real public advice-boundary violations.

Session 02 is accepted when `npm.cmd run lint` no longer opens an interactive setup prompt, or
the official docs clearly remove lint from CI/agent gates and explain the replacement frontend
checks.

Session 03 is accepted when `KNOWN_ISSUES.md` and `TESTING.md` reflect current full-pytest
truth. Passing full pytest is ideal, but an honest current failure or timeout baseline is
acceptable only if grouped and documented.

Session 04 is accepted when the exhaustive QA runner no longer reports a false frontend build
exit `-1`, or the issue is narrowed with exact retry guidance and current evidence. Session 12
confirmed that this narrowed P1 blocker still exists and must remain visible before release.

Session 05 is accepted when every tracked generated-like target folder has a classification
and no deletion has happened without dependency proof.

Session 06 is accepted when ordinary generated portfolio output folders are no longer tracked
as source, retained fixtures live in explicit fixture or evidence paths, and focused tests
still pass.

Sessions 07-12 are accepted when their scoped issue is fixed, owning docs are synced or
explicitly waived, and the validation commands in this plan pass or have documented blockers.
Session 12 is accepted as a release-readiness evidence capture, not as release-ready status, because
the documented P1 frontend production build blocker remains open.

Architecture sessions are accepted only when they preserve current public routes, API
envelopes, CLI commands, generated artifact schemas, and diagnosis-first product behavior
unless a separate contract migration explicitly changes them.

Session 13 is accepted when the Review Case domain model is additive, initial staged-state creation
still serializes as `review_state_v1`, unsafe absolute or parent-directory artifact refs are rejected
by the new domain seam, focused Review Case and staged API tests pass, docs verification passes, and
`git diff --check` reports no whitespace errors.

Session 14 is accepted when a run-local repository can save and load `ReviewCase` objects through the
existing `review_state.json` file, invalid or wrong-schema state is rejected by focused tests, new
staged-review creation uses the repository without changing public FastAPI envelopes or
`review_state_v1`, staged API compatibility tests pass, docs verification passes, and
`git diff --check` reports no whitespace errors.

Session 15 is accepted when a Review Case stage state-machine abstraction owns canonical
stage/status transition rules, focused tests cover timestamp and artifact-ref behavior, the existing
FastAPI staged helper uses that abstraction without changing public envelopes or `review_state_v1`,
staged API compatibility tests pass, docs verification passes, and `git diff --check` reports no
whitespace errors.

Session 16 is accepted when a Review Case artifact-manifest abstraction owns safe top-level
artifact key/ref handling for new architecture work, focused tests cover public map shape and unsafe
key/ref rejection, any FastAPI wiring is minimal and behavior-preserving, staged API compatibility
tests pass, docs verification passes, and `git diff --check` reports no whitespace errors.

Session 17 is accepted when a Review Case Evidence Graph abstraction can relate canonical stages,
artifact manifest entries, and source evidence refs for new architecture work, focused tests cover
graph serialization plus unsafe or undeclared refs, public FastAPI routes and envelopes remain
unchanged, staged API compatibility tests pass, docs verification passes, and `git diff --check`
reports no whitespace errors.

Session 18 is accepted when a Review Case screen read-model abstraction can project typed stage
progress, artifact availability, and evidence links for future screen/API migration, focused tests
cover read-model serialization and graph/case artifact mismatch rejection, public FastAPI routes and
envelopes remain unchanged, staged API compatibility tests pass, docs verification passes, and
`git diff --check` reports no whitespace errors.

Session 19 is accepted when a frontend Review Case client-state helper can project existing staged
start/status and compact stored progress into screen-ready stage progress, safe artifact
availability, progress counts, and diagnosis-chain readiness, focused frontend tests cover the
helper and readiness delegation, public FastAPI routes and envelopes remain unchanged, staged API
compatibility tests pass, docs verification passes, and `git diff --check` reports no whitespace
errors.

Session 20 is accepted when a narrow FastAPI staged-review state helper owns behavior-preserving
`review_state.json` IO, owner checks, safe public status projection, missing-state envelopes, and
legacy raw artifact-ref sanitization; `src/api/reviews.py` uses that helper without changing public
FastAPI routes, API envelopes, CLI commands, generated artifact schemas, diagnosis-first behavior,
or raw-state public sanitization compatibility; focused helper/staged API tests pass; FastAPI
contract governance and docs verification pass; and `git diff --check` reports no whitespace errors.

Session 21 is accepted when a narrow internal Review Case MarketDataSnapshot metadata seam can
project existing run metadata, provider status, and data-policy evidence into a stable internal
metadata shape and logical evidence-source ref; focused tests cover demo/live metadata projection,
stable basis-key behavior, and unsafe source-ref rejection; public FastAPI routes, API envelopes,
CLI commands, generated artifact schemas, diagnosis-first behavior, data providers, formulas, and
raw-state public sanitization compatibility remain unchanged; adjacent Review Case/staged API tests
pass; FastAPI contract governance and docs verification pass; and `git diff --check` reports no
whitespace errors.

Session 22 is accepted when a narrow Review Case execution queue adapter preserves the existing
in-process staged-review background-worker behavior by default, can enqueue the existing staged
runner through an opt-in RQ/Redis prototype when explicitly configured, falls back to the in-process
path when optional RQ/Redis configuration or dependencies are unavailable, and does not change public
FastAPI routes, API envelopes, CLI commands, generated artifact schemas, diagnosis-first behavior,
calculation formulas, data providers, or raw-state public sanitization compatibility. Focused queue
tests and adjacent Review Case/staged API tests must pass, FastAPI contract governance and docs
verification must pass, and `git diff --check` must report no whitespace errors.

Session 23 is accepted when the inactive-by-default Review Case execution queue seam has validated
internal configuration for backend names, queue names, Redis URL presence, and Redis URL schemes;
RQ enqueue success and failure paths expose only bounded internal metadata/logging; missing or
failing RQ/Redis still falls back to the existing in-process path; and public FastAPI routes, API
envelopes, CLI commands, generated artifact schemas, diagnosis-first behavior, calculation formulas,
data providers, and raw-state public sanitization compatibility remain unchanged. Focused queue
hardening tests and adjacent Review Case/staged API tests must pass, FastAPI contract governance and
docs verification must pass, and `git diff --check` must report no whitespace errors.

Session 24 is accepted when an inactive-by-default Review Case artifact storage seam preserves
run-local filesystem artifacts as the only active source of truth, validates safe future object keys
and remote-storage configuration metadata, falls back to local behavior when S3/R2-like backend names
are requested, and does not upload artifacts, require cloud credentials, change public FastAPI
routes, API envelopes, CLI commands, generated artifact schemas, diagnosis-first behavior,
calculation formulas, data providers, or raw-state public sanitization compatibility. Focused
artifact-storage tests and adjacent Review Case/staged API tests must pass, FastAPI contract
governance and docs verification must pass, and `git diff --check` must report no whitespace errors.

Session 25 is accepted when the narrow read-model migration step proves that sanitized staged status
can project into the internal Review Case screen read model, active frontend staged progress uses the
Review Case client read-model helper for compact progress and readiness, and public FastAPI routes,
API envelopes, CLI commands, generated artifact schemas, diagnosis-first behavior, calculation
formulas, data providers, and raw-state public sanitization compatibility remain unchanged. Focused
read-model/API/frontend tests and adjacent Review Case/staged API tests must pass, FastAPI contract
governance and docs verification must pass, and `git diff --check` must report no whitespace errors.

Session 26 is accepted when a narrow internal Review Case status projection bundle pairs the
existing sanitized public staged status response with the internal screen read model, the FastAPI
status wrapper uses that projection while still returning only the public status envelope, and public
FastAPI routes, API envelopes, CLI commands, generated artifact schemas, diagnosis-first behavior,
calculation formulas, data providers, and raw-state public sanitization compatibility remain
unchanged. Focused status-projection tests and adjacent Review Case/staged API tests must pass,
FastAPI contract governance and docs verification must pass, and `git diff --check` must report no
whitespace errors.

Session 27 is accepted when a narrow internal Review Case stage-readiness helper owns downstream
candidate/comparison/verdict/report readiness checks over the existing raw staged-state dictionary,
the FastAPI wrappers still return the same public `stage_not_ready` envelopes and messages, and
public FastAPI routes, API envelopes, CLI commands, generated artifact schemas, diagnosis-first
behavior, calculation formulas, data providers, and raw-state public sanitization compatibility
remain unchanged. Focused readiness tests and adjacent Review Case/staged API/FastAPI gate tests
must pass, FastAPI contract governance and docs verification must pass, and `git diff --check` must
report no whitespace errors.

Session 28 is accepted when a narrow internal Review Case downstream-lineage helper owns candidate,
comparison, verdict, and displayable-comparison consistency checks over existing generated artifact
dictionaries; the FastAPI wrappers still raise the same bridge errors that map to existing public
safe-error envelopes and messages; and public FastAPI routes, API envelopes, CLI commands, generated
artifact schemas, diagnosis-first behavior, calculation formulas, data providers, and raw-state
public sanitization compatibility remain unchanged. Focused lineage tests and adjacent Review
Case/staged API/FastAPI downstream compatibility tests must pass, FastAPI contract governance and
docs verification must pass, and `git diff --check` must report no whitespace errors.

Session 29 is accepted when a narrow internal Review Case downstream evidence-chain context helper
owns the bounded comparison/verdict/report display context projection over existing generated
artifact dictionaries; the FastAPI wrapper still returns the same public
`DownstreamEvidenceChainContext` fields inside existing response envelopes; and public FastAPI
routes, API envelopes, CLI commands, generated artifact schemas, diagnosis-first behavior,
calculation formulas, data providers, and raw-state public sanitization compatibility remain
unchanged. Focused context tests and adjacent Review Case/staged API/FastAPI downstream
compatibility tests must pass, FastAPI contract governance and docs verification must pass, and
`git diff --check` must report no whitespace errors.

Session 30 is accepted when the extracted Review Case seam surface is documented by a focused
package export test, public FastAPI routes, API envelopes, CLI commands, generated artifact schemas,
diagnosis-first behavior, calculation formulas, data providers, frontend contracts, and raw-state
public sanitization compatibility remain unchanged, adjacent Review Case/FastAPI compatibility tests
pass, FastAPI contract governance and docs verification pass, and `git diff --check` reports no
whitespace errors.

The release-blocker follow-up is accepted when `scripts/qa_exhaustive.ps1` no longer classifies the
frontend production build as a known P1 failure, the build runs in an isolated QA dist directory that
cannot conflict with the default `.next` dev-server directory, `KNOWN_ISSUES.md` no longer lists
`KI-2026-06-14-001` as active, `TESTING.md` and `docs/contracts/QA_CONTRACT.md` point to current
green evidence, and `.\scripts\qa_exhaustive.cmd -LocalOnly -SkipLive` records `Frontend production
build` as passed on the first attempt with zero P0/P1/P2 blockers. Browser vertical and staging
readiness remain separate release gates when needed.

## Idempotence and Recovery

Each session must start with `git status --short`. Do not revert user changes or unrelated
dirty files. Do not run destructive git commands. Do not commit, push, create branches, or
open pull requests unless the user explicitly requests it.

If a validation command fails, record the failure in this plan and in `KNOWN_ISSUES.md` when
the issue is not fixed immediately. If a session discovers that the planned approach is too
risky, stop, update the `Decision Log`, and write the next safe action instead of continuing
with a broad refactor.

Generated-output folders are evidence. Do not delete or refresh them unless the active
session explicitly targets generated-output hygiene or generated-output refresh.

## Artifacts and Notes

Origin audit:

    docs/audits/2026-06-19_deep_project_inventory_audit.md

Pre-Session 00 worktree evidence:

    ## main...origin/main
     M docs/audits/README.md
    ?? docs/audits/2026-06-19_deep_project_inventory_audit.md

The new active plan file is:

    docs/exec_plans/2026-06-19_project_stabilization_and_review_case_engine_plan.md

## Interfaces and Dependencies

Stable public interfaces that this plan must preserve unless a later contract migration
explicitly changes them:

- FastAPI staged review start: `POST /api/v1/reviews/staged`.
- FastAPI staged status: `GET /api/v1/reviews/{review_id}/status`.
- Next.js portfolio compatibility routes under `/api/portfolio/*`.
- Browser active-review storage keys documented in `frontend/lib/reviewState.tsx` and
  `frontend/README.md`.
- Core MVP CLI entrypoints: `run_core_diagnostics.py`, `run_portfolio_review.py`, and
  `scripts/run_blocks_5_to_9_vertical_flow.py`.
- Generated artifact names and schemas governed by `OUTPUTS.md` and detailed specs.

Future optional dependencies:

- RQ plus Redis for the first opt-in queue prototype.
- Cloudflare R2 or another S3-compatible backend for the later artifact-storage adapter.

Do not add those dependencies until their specific architecture sessions begin.

## Immediate Next Action

Sessions 13-30 Review Case architecture migration is complete, and the known P1 frontend
production build runner blocker from the Session 12 release-readiness audit is fixed. The local
static release gate `.\scripts\qa_exhaustive.cmd -LocalOnly -SkipLive` now records `ready` with
zero P0/P1/P2 blockers. The plan can be closed as architecture-complete plus local-static-ready
after final diff review. Browser vertical QA and staging release readiness are separate gates and
should be run only when claiming browser or staging release readiness. Do not start a Session 31 from
this plan unless a new user-approved plan or release-blocker scope is created.

## Revision Notes

- 2026-06-19 / Codex: Initial active plan created from the 2026-06-19 inventory audit and the
  user-approved stabilization and Review Case Engine session roadmap.
- 2026-06-19 / Codex: Session 01 completed the FastAPI/frontend governance fix, recorded
  validation evidence, and advanced the immediate next action to Session 02.
- 2026-06-19 / Codex: Session 02 completed the non-interactive frontend lint setup, recorded
  validation evidence and the dependency-audit residual, and advanced the immediate next action to
  Session 03.
- 2026-06-19 / Codex: Session 03 refreshed full pytest truth, fixed the small regex regressions
  found during the first run, recorded the green 2004-passed baseline, and advanced the immediate
  next action to Session 04.
- 2026-06-19 / Codex: Session 04 narrowed the exhaustive QA runner build-exit instability,
  recorded current local static gate evidence, kept `KI-2026-06-14-001` open, and advanced the
  immediate next action to Session 05.
- 2026-06-19 / Codex: Session 05 inventoried tracked generated-like portfolio artifacts without
  deletion, classified target folders, recorded the Robust MV calibration dependency, and advanced
  the immediate next action to Session 06.
- 2026-06-19 / Codex: Session 06 removed generated portfolio and Robust MV
  calibration/sensitivity folders from source tracking, expanded `.gitignore`, documented the
  generated calibration boundary, validated focused Robust MV tests plus `qa_fast`, and advanced the
  immediate next action to Session 07.
- 2026-06-19 / Codex: Session 07 fixed active-source display-label mojibake, added diagnostic
  section and block dash-variant coverage, recorded focused frontend and docs validation, and left
  Session 08 as the next not-started action.
- 2026-06-19 / Codex: Session 08 normalized route documentation, recorded docs and stale-route
  verification, and left Session 09 as the next not-started action.
- 2026-06-19 / Codex: Session 09 audited active/touched docs and plans for English-only,
  mojibake, and machine-local path hygiene, recorded clean targeted-scan evidence, and left Session
  10 as the next not-started action.
- 2026-06-19 / Codex: Session 10 cleaned live brand and terminology drift in active docs, recorded
  docs and targeted stale-brand verification, and left Session 11 as the next not-started action.
- 2026-06-19 / Codex: Session 11 promoted FastAPI/frontend governance into `qa_fast`, validated the
  expanded daily gate, synced QA docs, and left Session 12 as the next not-started action.
- 2026-06-19 / Codex: Session 12 reran local static release-readiness QA, recorded the current
  `passed_with_known_failures` evidence, kept the frontend production build runner failure open as a
  P1 blocker, added a release-readiness acceptance audit, and changed the next-action handoff to
  cloud/background Sessions 13-30 when such a project target is available.
- 2026-06-19 / Codex: The user explicitly authorized local execution for Sessions 13-30, replacing
  the previous cloud-only handoff blocker with separate local background/worktree session handoffs.
- 2026-06-19 / Codex: Session 13 introduced the first Review Case domain boundary, wired initial
  staged-state creation through it, recorded focused validation evidence, and advanced the immediate
  next action to local Session 14.
- 2026-06-19 / Codex: Session 14 added the run-local Review Case repository abstraction, wired new
  staged-review creation through it without changing public contracts, recorded focused validation
  evidence, and advanced the immediate next action to local Session 15.
- 2026-06-19 / Codex: Session 15 added the Review Case stage state-machine abstraction, wired the
  existing FastAPI stage-status helper through it without changing public contracts, recorded
  focused validation evidence, and advanced the immediate next action to local Session 16.
- 2026-06-19 / Codex: Session 16 added the Review Case artifact manifest abstraction, wired staged
  artifact-map refresh through it without changing public contracts, recorded focused validation
  evidence, and advanced the immediate next action to local Session 17.
- 2026-06-19 / Codex: Session 17 added the internal Review Case Evidence Graph abstraction without
  changing public contracts, recorded focused validation evidence, and advanced the immediate next
  action to local Session 18.
- 2026-06-19 / Codex: Session 18 added the internal Review Case screen read-model abstraction
  without changing public contracts, recorded focused validation evidence, and advanced the
  immediate next action to local Session 19.
- 2026-06-19 / Codex: Session 19 added the frontend Review Case client-state helper
  without changing public contracts, recorded focused frontend/backend/docs validation evidence,
  and advanced the immediate next action to local Session 20.
- 2026-06-20 / Codex: Session 20 added the FastAPI staged-review state helper without changing
  public contracts, recorded focused helper/staged API and docs validation evidence, and advanced
  the immediate next action to local Session 21.

- 2026-06-20 / Codex: Session 21 added the internal MarketDataSnapshot metadata seam without
  changing public contracts, recorded focused Review Case metadata validation evidence, and advanced
  the immediate next action to local Session 22.
- 2026-06-20 / Codex: Session 22 added the inactive-by-default Review Case execution queue seam with
  an opt-in RQ/Redis prototype and in-process fallback, recorded focused queue validation evidence,
  and advanced the immediate next action to local Session 23.
- 2026-06-20 / Codex: Session 23 hardened the inactive-by-default Review Case execution queue seam
  with validated internal configuration, bounded operational metadata/logging, and focused RQ/Redis
  success/failure coverage, then advanced the immediate next action to local Session 24.
- 2026-06-20 / Codex: Session 24 added the inactive-by-default Review Case artifact storage seam
  with run-local-only active behavior, safe future S3/R2 object-key and configuration validation,
  local fallback semantics, focused Review Case/staged API validation, and advanced the immediate
  next action to local Session 25.
- 2026-06-20 / Codex: Session 25 added the behavior-preserving read-model migration step for
  sanitized FastAPI status projection and frontend compact-progress delegation, recorded focused
  API/frontend/read-model validation, and advanced the immediate next action to local Session 26.
- 2026-06-20 / Codex: Session 26 added the internal Review Case status projection bundle for pairing
  the existing sanitized public staged status response with the internal screen read model, recorded
  focused status-projection validation, and advanced the immediate next action to local Session 27.
- 2026-06-20 / Codex: Session 27 added the internal Review Case stage-readiness helper for
  downstream candidate/comparison/verdict/report gates, recorded focused readiness and adjacent
  FastAPI validation, and advanced the immediate next action to local Session 28.
- 2026-06-20 / Codex: Session 28 added the internal Review Case downstream-lineage helper for
  candidate/comparison/verdict artifact consistency, recorded focused lineage validation, and
  advanced the immediate next action to local Session 29.
- 2026-06-20 / Codex: Session 29 added the internal Review Case downstream evidence-chain context
  helper for comparison/verdict/report display context, recorded focused context validation, and
  advanced the immediate next action to local Session 30.
- 2026-06-20 / Codex: Session 30 completed the Review Case architecture migration closeout with a
  focused package seam export test, recorded final validation expectations, and changed the
  immediate next action to plan closure/release only after explicitly remaining blockers are handled
  or accepted.
- 2026-06-20 / Codex: Release-blocker follow-up fixed the P1 exhaustive-runner frontend
  production build blocker by isolating the QA build directory and child process, removed the active
  known issue, recorded the green local static exhaustive gate, and left browser/staging release
  readiness as separate optional release gates.
