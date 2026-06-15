# Account Workspace, Portfolio Versions, and Review History

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows `PLANS.md` from the repository root. It is self-contained so a future
contributor can restart the work from this file and the current working tree without relying on
prior chat context.

## Purpose / Big Picture

Portfolio MRI must behave like a real signed-in decision-support workspace, not a one-time browser
form. After this change, a returning user who signs in can see saved work, the latest active review,
saved portfolio inputs, and prior compact review history without repeating onboarding or triggering
new calculations. A completed review is an immutable snapshot of the portfolio that was analyzed at
that time. If the user edits the portfolio or tests another portfolio, the system creates a new
draft/review snapshot and keeps the old completed review in history.

The observable outcome is: sign in, complete onboarding once, enter a portfolio and run diagnosis,
sign out, sign in again, and land in `/workspace`. The workspace shows the latest review and saved
portfolio context without recalculating. Editing the portfolio starts a new draft and leaves the old
review available in history.

## Progress

- [x] (2026-06-15) Session 01 created this ExecPlan and updated product, screen, staged-state,
  frontend, design, Supabase, decision, and changelog documentation with the account workspace
  direction. Validation passed with `git diff --check`, `scripts/verify_docs.py`, and targeted stale
  returning-user wording search.
- [x] (2026-06-15) Session 02 added additive Supabase schema support for portfolio versions,
  workspace state, compact Client Fit profile fields, archive fields, and review-to-version links.
  Validation passed with SQL text sanity checks, `git diff --check`, and `scripts/verify_docs.py`.
- [x] (2026-06-15) Session 03 extended frontend Supabase persistence and active review state to hydrate the
  cloud workspace, create immutable portfolio versions, create draft reviews on input changes, and
  distinguish read-only compact history from live recoverable review state. Validation passed with
  `npm.cmd run typecheck` and `npm.cmd run test:api`.
- [x] (2026-06-15) Session 04 added `/workspace`, workspace navigation, portfolio library, review
  history, archive controls, and returning-user account-home routing. Validation passed with
  `npm.cmd run typecheck`, `npm.cmd run test:api`, and `npm.cmd run test:smoke`.
- [x] (2026-06-15) Session 05 hardened stale-result and lineage behavior: compact cloud history
  opens read-only unless recoverable live lineage fields are present, portfolio edits still clear
  downstream state, Hypothesis/Comparison/Verdict/Report actions require live same-run lineage, and
  historical screens are labeled as read-only compact history. Validation passed with
  `npm.cmd run typecheck`, `npm.cmd run test:api`, and `npm.cmd run test:smoke`.
- [x] (2026-06-15) Session 06 verified backend/API owner and recovery boundaries. Next.js API
  route tests confirm signed internal FastAPI headers, FastAPI tests now cover different-owner and
  ownerless rejection for downstream mutation routes, and no additive API fields were required
  because Session 05 already keeps compact history read-only unless explicit recoverable action
  metadata exists. Validation passed with targeted FastAPI tests, FastAPI contract governance, and
  `npm.cmd run test:api`.
- [x] (2026-06-15) Session 07 ran final static, contract, frontend, backend, docs, and browser
  vertical QA. The first vertical QA attempts exposed two local QA harness gaps: the helper did not
  force local dev-bypass auth/internal signing when Supabase env was present, and Demo / QA
  candidate generation still fell through to the live factory with `frozen_fixture` provider
  metadata. Session 07 fixed both local QA paths, then passed `npm.cmd run qa:vertical --
  --scenario-limit 1` with same-run lineage through Report and stale-card HTTP 409 proof.

## Surprises & Discoveries

- Observation: The project already has most compact persistence primitives: Supabase `profiles`,
  `portfolios`, `portfolio_holdings`, `reviews`, `review_stage_summaries`, `verdicts`, compact cloud
  sanitization, localStorage `pmri.activeReview.v2`, and `review_state_v1`.
  Evidence: `docs/supabase/supabase_free_schema.sql`, `frontend/lib/supabase/persistence.tsx`, and
  `frontend/lib/reviewState.tsx`.
- Observation: The Portfolio Input cloud portfolio UI exists but is hidden behind a dead
  `{false ? ... : null}` branch.
  Evidence: `frontend/components/portfolio/PortfolioInputTable.tsx`.
- Observation: Editing portfolio input already clears active downstream readiness in local review
  state. That behavior is the correct seed for the new immutable-review model, but it needs durable
  portfolio versions and a workspace/history UX.
  Evidence: `savePortfolioInput()` in `frontend/lib/reviewState.tsx` clears `reviewId`,
  `reviewSummary`, candidate, comparison, verdict, and report state.

- Observation: Session 03 could preserve the existing local review-state clearing behavior while
  adding cloud portfolio versions by keeping the cloud portfolio link, clearing the old
  `portfolioVersionId`, and letting a signed-in draft effect create or reuse a compact immutable
  `portfolio_versions` row.
  Evidence: `savePortfolioInput()` and the `lastEnsuredDraftVersionKeyRef` effect in
  `frontend/lib/reviewState.tsx`.

- Observation: Session 04 could reuse the Session 03 persistence context for the workspace instead
  of adding a separate data loader. The only additional persistence action needed was an archive
  helper for saved review rows.
  Evidence: `frontend/app/workspace/page.tsx` consumes `useSupabasePersistence()` and
  `frontend/lib/supabase/persistence.tsx` now exposes `archiveReview()`.

- Observation: Session 05 found that compact cloud review rows could carry
  `compact_summary.lineageAvailable=true` even though the frontend had no run-local recovery proof
  after a fresh sign-in. Treating such rows as live could let old candidate/comparison/verdict
  summaries unlock downstream actions.
  Evidence: `frontend/lib/supabase/persistence.tsx` now derives `lineageAvailable` only from future
  recoverable action metadata, while historical compact rows hydrate with read-only labels and locked
  actions.

- Observation: The report page kept a local `report` preview state independent of the current
  action locks, so a compact or stale `reportResult` could still render after `canGenerateReport`
  was false.
  Evidence: `frontend/app/report/page.tsx` now displays a stored report only when it matches the
  active candidate and either live lineage exists or the review is explicitly read-only history.

- Observation: The live base Supabase schema did not yet include the workspace fields described by
  Session 01 docs, so Session 02 needed both a one-shot migration for existing projects and a base
  schema sync for new projects.
  Evidence: `docs/supabase/2026-06-15_account_workspace_schema.sql` and
  `docs/supabase/supabase_free_schema.sql`.

- Observation: Adding `reviews.portfolio_version_id` requires refreshing the existing review write
  RLS policies, not only adding table-level policies for `portfolio_versions`.
  Evidence: Session 02 drops and recreates `pmri_reviews_insert_own` and `pmri_reviews_update_own`
  so review rows can only link to portfolio versions owned by the authenticated user.

- Observation: Session 06 found that the FastAPI ownership implementation already stores
  `owner_id` in run-local `review_state_v1`, reads review state through
  `_read_authorized_staged_state()`, and routes Next.js calls through signed internal headers rather
  than browser-supplied identity.
  Evidence: `src/api/app.py` passes `auth.user_id` into staged, recovery, builder, candidate,
  comparison, verdict, and report handlers; `frontend/tests/api-route-tests.cjs` asserts the signed
  `X-PMRI-*` headers; new tests in `tests/test_fastapi_app.py` verify different-owner and
  ownerless downstream mutations return HTTP 403 before mutation.

- Observation: Session 07 found that the documented local vertical QA command can run under a
  developer shell where Supabase browser auth is enabled. Without an explicit local process override,
  the script received HTTP 401 before diagnosis because no browser user was signed in.
  Evidence: `npm.cmd run qa:vertical -- --scenario-limit 1` first failed at diagnosis start; the QA
  helper now starts Next.js with `PMRI_PORTFOLIO_API_AUTH_MODE=dev_bypass` and a deterministic
  `PMRI_PORTFOLIO_API_DEV_USER_ID` unless the caller explicitly provides another auth mode.

- Observation: Session 07 found that Demo / QA candidate generation still tried the live candidate
  factory after the staged diagnosis fixture path wrote `market_data_provider: frozen_fixture`.
  Evidence: vertical QA failed while waiting for the candidate stage with
  `market_data_provider must be one of ['ibkr', 'ibkr_yfinance_fallback', 'yfinance'], got
  'frozen_fixture'`; `src/api/reviews.py` now writes deterministic Demo / QA
  `candidate_generation.json` and `candidate_factory_run.json` instead of calling the live factory
  for Demo / QA staged reviews.

## Decision Log

- Decision: `/workspace` is the returning-user account home.
  Rationale: Returning users need a stable place to understand latest review, active portfolio,
  draft state, and history before entering the 8-step review rail. Sending them straight to
  `/portfolio-input` hides history and makes the product feel like a single form.
  Date/Author: 2026-06-15 / Codex.

- Decision: Completed reviews are immutable snapshots.
  Rationale: A diagnosis, comparison, verdict, or report belongs to the exact portfolio and stage
  lineage that created it. Mutating a completed review after portfolio edits risks showing an old
  verdict for a new portfolio.
  Date/Author: 2026-06-15 / Codex.

- Decision: Portfolio edits after a completed review create a new draft tied to a new portfolio
  version.
  Rationale: The user can safely test another portfolio or update holdings without losing prior
  history. This also prevents automatic recalculation on login.
  Date/Author: 2026-06-15 / Codex.

- Decision: Archive is the normal UI removal action; hard delete is deferred.
  Rationale: Archive protects user trust and auditability while still letting the user hide old
  portfolios and reviews. Permanent deletion can be designed later as a separate privacy/admin
  feature.
  Date/Author: 2026-06-15 / Codex.

- Decision: Supabase remains compact app-data storage only.
  Rationale: Generated artifacts, raw diagnostic JSON, price history, PDFs, and run folders are
  sensitive and too large for the intended Supabase Free app-data layer.
  Date/Author: 2026-06-15 / Codex.

- Decision: Review write RLS must validate `portfolio_version_id` ownership and portfolio consistency.
  Rationale: A review row is only trustworthy if both its editable portfolio pointer and immutable
  portfolio-version pointer belong to the signed-in user. Refreshing the existing insert/update
  policies keeps the schema additive while closing cross-user linkage risk.
  Date/Author: 2026-06-15 / Codex.

- Decision: `/workspace` opens compact history into the existing review-state hydrator and routes to
  the most advanced available product screen, while draft reviews return to Portfolio Input.
  Rationale: This keeps Session 04 additive and avoids inventing a second read-only review viewer.
  Later stale-lineage hardening can tighten which downstream actions are recoverable.
  Date/Author: 2026-06-15 / Codex.

- Decision: Compact Supabase review history is read-only by default until explicit recoverable
  action metadata exists.
  Rationale: A compact row proves that a prior summary exists, but it does not prove the browser can
  safely recover the same run-local artifacts needed to generate candidates, comparisons, verdicts,
  or reports. Locking actions by default prevents stale verdicts from appearing current after
  portfolio edits or account rehydration.
  Date/Author: 2026-06-15 / Codex.

- Decision: Same-run lineage checks live in `frontend/lib/reviewState.tsx` and are repeated at the
  action screens.
  Rationale: State normalization prevents stale readiness flags from surviving storage hydration,
  while screen-level checks keep buttons and status labels honest even when a compact summary is
  displayed read-only.
  Date/Author: 2026-06-15 / Codex.

- Decision: Session 06 does not add new FastAPI response fields for workspace lineage display.
  Rationale: The UI already gets `readOnlyHistory` and `lineageAvailable` from compact Supabase
  metadata, and Session 05 deliberately treats compact history as read-only unless future
  `recoverable_actions` metadata is present. Adding duplicate FastAPI fields now would expand the
  public contract without a current UI consumer.
  Date/Author: 2026-06-15 / Codex.

- Decision: Local browser vertical QA should use explicit local dev-bypass auth and an ephemeral
  internal signing secret when the caller has not provided auth env vars.
  Rationale: The QA helper starts isolated local Next.js and FastAPI processes to verify route-chain
  behavior. It should not depend on a real Supabase browser session or production secrets, and
  production remains protected because `dev_bypass` is rejected in production runtime.
  Date/Author: 2026-06-15 / Codex.

- Decision: Demo / QA staged reviews must keep candidate, comparison, verdict, and report evidence
  on the deterministic fixture path.
  Rationale: The fixture diagnosis path intentionally uses provider source `frozen_fixture`; sending
  later stages through the live factory mixes modes and blocks local QA before it can verify same-run
  lineage and stale-card rejection.
  Date/Author: 2026-06-15 / Codex.

## Outcomes & Retrospective

Session 01 established the source-of-truth direction and implementation plan. Documentation
validation passed. Session 02 added the additive Supabase workspace schema as both an existing-project
migration and a synced base schema for new projects. Session 03 added frontend compact workspace
hydration, portfolio-version creation, review-to-version persistence, archive-first portfolio
hiding, and read-only compact history flags. Session 04 surfaced the signed-in account home at
`/workspace`, added portfolio library and compact review history controls, linked the sidebar to
Workspace outside the 8-step journey, and routed completed returning users to Workspace when saved
cloud work exists. Session 05 closed the main stale-lineage UI risk by making compact cloud history
read-only unless recoverable lineage is explicitly available, adding same-run lineage checks to
active review state, and locking downstream action buttons on historical summaries. Session 06
verified the backend owner boundary and recovery/mutation gate with targeted FastAPI and frontend
API-route tests; no public API field expansion was needed. Session 07 closed the local verification
pass: frontend typecheck, frontend API routes, frontend smoke, targeted FastAPI ownership tests,
FastAPI contract governance, docs verification, diff whitespace checks, and one-scenario browser
vertical QA all passed. The successful vertical QA used
`output/playwright/vertical-qa-2026-06-15T19-32-21-214Z`, active review
`frontend_review_20260615T193233Z_26Y7mUhNUiC_KwuYHlFJ9A`, selected card
`launchpad_demo_reduce_concentration`, candidate `equal_weight`, comparison
`current_vs_candidate:equal_weight`, verdict `evidence_insufficient`, and stale-card HTTP 409 proof.
Full sign-out/sign-in behavior against a real Supabase project remains an external manual acceptance
item because this local QA session used the documented dev-bypass browser harness, not a real
Supabase account.

## Context and Orientation

The current frontend is a Next.js app in `frontend/`. Public and onboarding routes live under
`frontend/app/`, product screens live at routes such as `frontend/app/portfolio-input/page.tsx` and
`frontend/app/diagnosis/page.tsx`, and shared active review state lives in
`frontend/lib/reviewState.tsx`.

The optional Supabase browser persistence layer lives in `frontend/lib/supabase/`. It uses browser
safe clients only. The schema is documented in `docs/supabase/supabase_free_schema.sql` and
`docs/supabase/README.md`. Supabase is an app-data layer, not a generated-artifact store.

A review means a calculation run for a specific portfolio snapshot at a specific time. A portfolio
means the user-entered holdings and weights. A portfolio version means an immutable copy of a
portfolio input at the moment it is used for a draft or completed review. A stage summary means a
small display-ready row for a product stage such as Diagnosis, Stress Lab, Candidate, Comparison,
Verdict, or Report. A run-local artifact means generated files under `runs/frontend_review_*` and
related output folders; these must not be uploaded to Supabase.

The current normal route chain is:

    / -> /onboarding/sign-in -> /onboarding/name -> /onboarding/investor-type
    -> /onboarding/loading -> /portfolio-input -> /diagnosis -> /evidence
    -> /client-fit -> /hypothesis -> /comparison -> /verdict -> /report

This plan adds `/workspace` as the signed-in account home for returning users. `/workspace` does not
replace the 8-step review route chain; it coordinates saved workspace state and lets the user choose
which review or draft to continue.

## Plan of Work

Session 02 adds schema support. Create an additive migration under `docs/supabase/` that adds
profile Client Fit fields, `portfolio_versions`, `workspace_state`, archive columns, and
`reviews.portfolio_version_id`. Keep the existing `portfolio_snapshot` compatibility field. Add RLS
policies so users only see and update their own rows. Do not introduce service-role keys or raw
artifact storage.

Session 03 extends `frontend/lib/supabase/persistence.tsx` and `frontend/lib/reviewState.tsx`. Add
types for `WorkspaceStateRecord`, portfolio versions, archived portfolios, archived reviews,
read-only compact history, and lineage availability. On signed-in hydration, fetch workspace state
from Supabase and prefer it over localStorage when available. Keep localStorage as a fallback for
local and unsynced drafts. When a meaningful portfolio input change happens after a completed
review, create a new draft tied to a new portfolio version and clear downstream readiness.

Session 04 adds `frontend/app/workspace/page.tsx` and supporting components. The workspace shows a
current workspace card, portfolio library, and review history. It includes explicit copy that login
restores work but never recalculates automatically, and that changing a portfolio starts a new draft.
Update sign-in routing so completed users go to `/workspace` when cloud workspace or saved reviews
exist, otherwise to `/portfolio-input`. Add a Workspace link to the platform sidebar outside the
8-step review journey.

Session 05 hardens stale-result behavior. Historical compact summaries are read-only unless live
run-local lineage can be recovered for the signed-in owner. Downstream actions remain locked unless
the active review has same-run lineage for selected card, candidate, comparison, verdict, and report.
Use UI labels such as `Current`, `Draft changed`, `Historical`, `Read-only compact history`, and
`Needs new diagnosis`; do not add `outdated` as a canonical staged status.

Session 06 reviews backend/API ownership. Confirm Next.js API routes pass signed user context and
FastAPI rejects different-owner or ownerless mutations. Add only additive fields such as
`lineage_available`, `read_only_history`, `recoverable_actions`, or `portfolio_version_id` if the UI
needs them.

Session 07 runs full verification and closes the plan. Update this file's progress, discoveries,
decision log, and retrospective with actual results.

## Concrete Steps

Use PowerShell from the repository root:

    cd "D:\Рабочий стол\КУРСОР ТУЛА ДИАГНОСТИКА"

For Session 01 documentation validation:

    git diff --check
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    rg -n "returning signed-in users|completed users|automatic recalculation|workspace hydration" docs frontend README.md

For Session 02 schema validation:

    git diff --check
    .\.venv\Scripts\python.exe scripts\verify_docs.py

For later frontend sessions:

    cd frontend
    npm.cmd run typecheck
    npm.cmd run test:api
    npm.cmd run test:smoke

For backend ownership sessions:

    .\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py tests\test_staged_review_api.py -q
    .\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py

For final browser QA:

    cd frontend
    npm.cmd run qa:vertical -- --scenario-limit 1

## Validation and Acceptance

The feature is accepted only when these behaviors are observable:

1. A new user signs in, completes onboarding, enters a portfolio, runs diagnosis, and sees the review
   saved in workspace history.
2. The same user signs out and signs in again, lands on `/workspace`, and does not repeat onboarding
   or trigger automatic recalculation.
3. The workspace shows the latest active review, active portfolio, stage status, and review history.
4. Editing a portfolio after a completed review creates a new draft and locks downstream stages until
   the user explicitly runs diagnosis again.
5. The old completed review remains visible in history with its original portfolio snapshot.
6. Starting a test portfolio creates a separate draft under the same user.
7. Archive hides portfolios or reviews from the default lists without physical deletion.
8. Compact Supabase rows contain no local artifact paths, raw generated JSON, run folders, price
   history, PDFs, CSVs, or generated candidate folders.
9. Another user cannot recover or mutate the first user's protected review.

## Idempotence and Recovery

Schema changes must be additive and safe to run once in Supabase SQL Editor. Migration files should
use `if not exists`, `add column if not exists`, and idempotent policy/trigger creation patterns.
Frontend writes should be upserts keyed by the authenticated user and stable row identifiers.

If cloud persistence fails, local active review state must remain usable and the UI should show a
bounded warning. If backend run-local recovery is unavailable for a compact history record, the
workspace should open a read-only compact summary instead of pretending full artifacts are available.

Do not run destructive git commands. Do not delete generated run folders as part of this plan.

## Artifacts and Notes

The current docs and code already establish these relevant boundaries:

    Supabase compact-only boundary:
    - profiles, portfolios, holdings, compact review rows, compact stage summaries, verdict summaries
    - no raw generated artifacts or run folders

    Staged route authority:
    - POST /api/v1/reviews/staged
    - GET /api/v1/reviews/{review_id}/status
    - review_state_v1 with owner_id

    Frontend compact state:
    - pmri.activeReview.v2 in browser localStorage
    - reviewId, portfolio input, compact diagnosis/stage summaries, selected lineage IDs

## Interfaces and Dependencies

Supabase tables after the schema session must support:

    profiles.client_fit_profile jsonb
    profiles.onboarding_completed_at timestamptz
    profiles.client_fit_updated_at timestamptz

    portfolio_versions.id uuid
    portfolio_versions.portfolio_id uuid
    portfolio_versions.user_id uuid
    portfolio_versions.version_number integer
    portfolio_versions.base_currency text
    portfolio_versions.holdings_snapshot jsonb
    portfolio_versions.input_fingerprint text
    portfolio_versions.source_kind text
    portfolio_versions.source_review_id text

    workspace_state.user_id uuid
    workspace_state.active_portfolio_id uuid
    workspace_state.active_portfolio_version_id uuid
    workspace_state.active_review_row_id uuid
    workspace_state.last_opened_review_row_id uuid

    portfolios.archived_at timestamptz
    reviews.archived_at timestamptz
    reviews.portfolio_version_id uuid

Frontend state after the implementation sessions must expose:

    SavedPortfolioRecord.archivedAt
    SavedPortfolioRecord.latestVersionId
    SavedPortfolioRecord.versionNumber
    SavedReviewRecord.portfolioVersionId
    SavedReviewRecord.archivedAt
    SavedReviewRecord.readOnlyHistory
    SavedReviewRecord.lineageAvailable
    WorkspaceStateRecord

No new runtime dependency is required for Session 01. Later frontend implementation should continue
using Next.js, React, Tailwind, the existing Portfolio MRI dark design system, and existing Supabase
browser clients.

Revision note, 2026-06-15 / Codex: Session 03 implemented the frontend persistence/state portion of
this plan. The plan now records the completed workspace hydration, portfolio-version, draft lineage,
archive, read-only compact history, and validation results so Session 04 can start from a current
living document.

Revision note, 2026-06-15 / Codex: Session 04 implemented the `/workspace` account-home UI, sidebar
navigation, portfolio library actions, compact review history actions, review archiving, and
returning-user sign-in routing. The plan now records the validation commands and remaining lineage
hardening risk for Session 05.

Revision note, 2026-06-15 / Codex: Session 05 implemented stale-result hardening for compact cloud
history and downstream lineage locks. Compact history now hydrates as read-only unless future
recoverable action metadata proves live lineage, and Hypothesis, Comparison, Verdict, and Report
actions require live same-run lineage before creating or unlocking downstream evidence.

Revision note, 2026-06-15 / Codex: Session 06 verified the backend/API ownership boundary without
expanding the public API contract. FastAPI now has regression coverage proving different-owner and
ownerless staged reviews cannot be mutated through builder, candidate, comparison, verdict, or
report endpoints; frontend API-route tests continue to prove signed internal auth headers are sent
to FastAPI.

Revision note, 2026-06-15 / Codex: Session 07 completed the local final QA pass and fixed the
browser QA harness so local vertical QA uses dev-bypass auth/internal signing and deterministic
Demo / QA candidate fixtures. Final checks passed, including one-scenario vertical QA through
Report with stale-card HTTP 409 evidence. Real Supabase sign-out/sign-in remains external manual
acceptance coverage.
