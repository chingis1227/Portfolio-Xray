# Supabase Free Optional Persistence and Auth Plan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows `PLANS.md` from the repository root. It is self-contained for implementing Supabase Free as an optional app-data layer for Portfolio MRI without changing portfolio analytics.

## Purpose / Big Picture

After this change, a signed-in Portfolio MRI user can save portfolios, recover compact review history, and persist diagnosis-to-verdict summaries across browser sessions through Supabase Free. If Supabase is not configured, the application continues to work exactly like the current local demo using browser `localStorage`. Supabase is not an analytics engine and not a generated-artifact store; it stores only lightweight app records such as users, portfolios, holdings, compact review summaries, compact stage summaries, and verdict summaries.

The user-visible proof is simple: with no Supabase environment variables the frontend still runs and the current review journey works locally; with Supabase public environment variables and Email OTP Auth configured, a user can sign in, save a portfolio, run diagnosis, persist compact stage summaries, refresh the browser, and recover saved review state from Supabase.

## Progress

- [x] (2026-06-11) Session 0 created this ExecPlan and recorded the architecture decision that Supabase Free is an optional compact app-data layer.
- [x] (2026-06-12) Session 1 added the optional Supabase environment gate, public-only `.env.example`, guarded browser-client helper, and sidebar local demo status UI.
- [x] (2026-06-12) Session 2 added the Supabase SQL Editor schema script with tables, foreign keys, cascade behavior, indexes, update triggers, profile bootstrap trigger, and Row Level Security policies.
- [x] (2026-06-12) Session 3 added guarded browser/server Supabase clients, an Email OTP sign-in panel, direct OTP verification, a magic-link callback route, and auth documentation using only public Supabase environment variables.
- [x] (2026-06-12) Session 4 added optional cloud portfolio persistence with save/list/load/delete UI and non-blocking warnings.
- [x] (2026-06-12) Session 5 added automatic compact diagnosis review persistence into `reviews` plus `review_stage_summaries.stage = diagnosis`.
- [x] (2026-06-12) Session 6 persisted compact builder, candidate, comparison, verdict, and report stage summaries with a 55 KB application soft limit.
- [x] (2026-06-12) Session 7 added a Saved cloud reviews sidebar panel and compact cloud recovery while keeping existing run-local recovery.
- [x] (2026-06-12) Session 8 ran frontend typecheck and updated docs that describe Supabase storage boundaries.

## Surprises & Discoveries

- Observation: The current frontend already stores only compact active review state in `localStorage` and intentionally avoids persisting raw review JSON in browser storage.
  Evidence: `frontend/lib/reviewState.tsx` writes `reviewResult: undefined` into the stored active review and uses `buildCompactReviewSummary` for UI-ready state.
- Observation: The current Next.js routes proxy to the FastAPI backend and FastAPI writes full evidence artifacts locally.
  Evidence: routes under `frontend/app/api/portfolio/*/route.ts` call helpers in `frontend/lib/server/fastapiBridge.ts`, while `src/api/app.py` exposes `/api/v1/reviews` and downstream review endpoints.
- Observation: Session 1 frontend typecheck passes with Supabase disabled by default.
  Evidence: `cd frontend; npm.cmd run typecheck` completed successfully on 2026-06-12 after PowerShell blocked `npm.ps1`.
- Observation: Session 2 is documentation/schema-only and does not touch frontend runtime code, portfolio analytics, generated artifacts, or the local demo path.
  Evidence: the only new implementation artifact for Session 2 is `docs/supabase/supabase_free_schema.sql`, plus this ExecPlan status update.
- Observation: Session 3 frontend typecheck passes after adding Supabase Auth UI and the callback route.
  Evidence: `cd frontend; npm.cmd run typecheck` completed successfully on 2026-06-12.
- Observation: Session 3 keeps disabled mode login-free because the auth provider returns `status: "disabled"` and the sidebar auth panel renders `null` unless the public Supabase gate is enabled.
  Evidence: `frontend/lib/supabase/auth.tsx` initializes disabled mode from `getSupabaseRuntimeStatus()`, and `frontend/components/layout/AuthPanel.tsx` returns `null` when `enabled` is false.
- Observation: Session 4/5 frontend typecheck passes after adding the Supabase persistence provider, cloud portfolio UI, and automatic diagnosis-summary upsert logic.
  Evidence: `cd frontend; npm.cmd run typecheck` completed successfully on 2026-06-12.
- Observation: Session 5 diagnosis persistence is implemented as a post-success optional side effect from `ReviewStateProvider`, so local diagnosis completion and route navigation do not depend on Supabase availability.
  Evidence: `frontend/lib/reviewState.tsx` updates local review state first, then calls `persistDiagnosisSummaryForReview()` only when Supabase is enabled and the user is signed in.
- Observation: Session 6/7 frontend typecheck passes after adding late-stage compact persistence, the 55 KB stage-summary guard, saved review listing, report-state capture, and cloud recovery.
  Evidence: `cd frontend; npm.cmd run typecheck` completed successfully on 2026-06-12.
- Observation: Cloud recovery deliberately hydrates compact UI state only and does not attempt to reconstruct raw generated evidence artifacts.
  Evidence: `frontend/lib/reviewState.tsx` builds recovered state from `SavedReviewRecord.stages` and sets `reviewResult: undefined`, while `frontend/lib/supabase/persistence.tsx` fetches rows from `reviews` and `review_stage_summaries` only.

## Decision Log

- Decision: Supabase must be fully optional and disabled unless `NEXT_PUBLIC_PMRI_SUPABASE_ENABLED=true` and both public Supabase keys are present.
  Rationale: The current local demo must remain reliable and development must not require a cloud account.
  Date/Author: 2026-06-11 / Codex.
- Decision: The frontend must not use service-role keys, secret keys, private database passwords, Edge Functions, Realtime, or Supabase Storage in the first implementation.
  Rationale: The Free-plan MVP needs the smallest safe surface and must rely on browser/server clients plus Row Level Security, not privileged frontend credentials.
  Date/Author: 2026-06-11 / Codex.
- Decision: Supabase stores compact summaries only and must never upload full generated artifacts, PDFs, price history, cache, parquet, `runs/`, `Main portfolio/`, or generated candidate folders.
  Rationale: Supabase Free storage is limited and Portfolio MRI already treats generated artifacts as local evidence, not source data.
  Date/Author: 2026-06-11 / Codex.
- Decision: `review_stage_summaries.summary` has a 55 KB soft limit; oversized summaries are skipped with a user-facing warning and the localStorage flow remains active.
  Rationale: This prevents accidental Free-plan overload while preserving user workflow continuity.
  Date/Author: 2026-06-11 / Codex.
- Decision: The Session 2 SQL schema records `summary_size_bytes` for stage summaries but does not enforce the 55 KB limit as a database `check` constraint.
  Rationale: The plan defines 55 KB as a soft application guard for Session 6; a hard database constraint would turn an oversized optional cloud write into an avoidable database error instead of a controlled skip-and-warn path.
  Date/Author: 2026-06-12 / Codex.
- Decision: Session 3 uses a guarded server Supabase client only for `/auth/callback`, and uses the browser client for Email OTP send, OTP verification, session observation, and sign-out.
  Rationale: This supports both magic-link and direct-code Email OTP sign-in while keeping the frontend limited to public Supabase URL and publishable key. No service-role key or privileged server credential is introduced.
  Date/Author: 2026-06-12 / Codex.
- Decision: Session 4 portfolio save/load/delete uses the browser Supabase client directly from the signed-in frontend session, and replaces child holdings by deleting and reinserting `portfolio_holdings` rows after the parent portfolio upsert.
  Rationale: This keeps the first persistence version simple, RLS-compatible, and aligned with the plan requirement that saving a portfolio replaces its holdings snapshot rather than diffing rows.
  Date/Author: 2026-06-12 / Codex.
- Decision: Session 5 writes a compact review-level summary to `reviews.compact_summary` and a separate compact diagnosis stage payload to `review_stage_summaries.summary`, but does not upload raw `reviewResult`, generated output files, or full artifact JSON.
  Rationale: The plan explicitly limits Supabase to lightweight app-data persistence and forbids generated-artifact storage.
  Date/Author: 2026-06-12 / Codex.
- Decision: Session 6 applies the 55 KB soft limit in the shared stage-summary upsert helper and skips oversized optional cloud writes instead of blocking local state updates.
  Rationale: A soft application guard protects Supabase Free limits while preserving the local-first review journey.
  Date/Author: 2026-06-12 / Codex.
- Decision: Session 7 recovers saved cloud reviews into compact `ReviewStateProvider` state and keeps raw `reviewResult` unavailable after cloud recovery.
  Rationale: Supabase is app-data persistence only; full generated artifacts remain local and run-scoped, with the existing review-id recovery path as the advanced fallback.
  Date/Author: 2026-06-12 / Codex.

## Outcomes & Retrospective

Session 0 established the implementation boundary and records the decision before code-level Supabase work proceeds. No portfolio formulas, FastAPI analytics, generated artifact schemas, or product decision logic are changed by Session 0.

Session 1 added only the optional frontend feature gate and visible disabled-mode status. The default app remains a local demo using compact browser state, and the Supabase browser client helper returns `null` unless `NEXT_PUBLIC_PMRI_SUPABASE_ENABLED=true` and both public Supabase values are present.

Session 2 added `docs/supabase/supabase_free_schema.sql` for manual use in the Supabase SQL Editor. The schema creates the six planned app-data tables, keeps child cleanup explicit through `on delete cascade` on portfolio holdings, review stage summaries, and verdicts, enforces `unique(user_id, review_id)` on reviews, and enables owner-only Row Level Security policies for every app table. No frontend secrets, service-role keys, analytics code, or generated-output storage paths were added.

Session 3 added optional Supabase Auth without changing portfolio analytics or local review storage. `frontend/lib/supabase/auth.tsx` tracks the browser auth session, sends Email OTP links, verifies OTP codes, and signs out. `frontend/lib/supabase/server.ts` creates a per-request server client from the same public values for `frontend/app/auth/callback/route.ts`, which exchanges magic-link codes and redirects back to Portfolio Input. `frontend/components/layout/AuthPanel.tsx` renders only when Supabase is enabled, so disabled/default mode remains login-free and localStorage-based. `frontend/README.md` now documents the local callback URL and reiterates that Session 3 adds auth only, not saved portfolios or review history.

Session 4 added `frontend/lib/supabase/persistence.tsx` plus a cloud-portfolio panel on `frontend/components/portfolio/PortfolioInputTable.tsx`. Signed-in users can now save the current portfolio input, list saved portfolios, load a saved portfolio back into the input screen, and delete a saved portfolio. Holdings are stored in Supabase as lightweight rows under `portfolio_holdings`; cloud failures surface as non-blocking notices in the sidebar and do not block the normal local diagnosis journey.

Session 5 added automatic optional diagnosis persistence after successful local diagnosis. `frontend/lib/reviewState.tsx` now preserves the active cloud-portfolio link when appropriate and, for signed-in users, upserts one compact row into `reviews` keyed by `(user_id, review_id)` plus one compact `diagnosis` row into `review_stage_summaries`. The saved payloads carry portfolio metadata, compact diagnosis/evidence/launchpad summaries, and artifact keys only; they do not upload raw generated artifacts, PDFs, `runs/`, or full backend JSON outputs.

Session 6 added compact late-stage persistence for Builder setup, Candidate Generation, Current-vs-Candidate Comparison, Decision Verdict, and Report preview. `frontend/lib/supabase/persistence.tsx` now uses a shared stage-summary upsert helper that measures serialized JSON and skips any `review_stage_summaries.summary` payload above the 55 KB soft limit with a warning path instead of breaking local state. `frontend/lib/reviewState.tsx` triggers these writes as optional side effects after local state changes, and verdict persistence also maintains the compact `verdicts` row.

Session 7 added cloud review history and recovery. `frontend/components/layout/SavedReviewsPanel.tsx` lists recent saved reviews for signed-in users, shows which compact stages exist, and can hydrate the active browser state from Supabase `reviews` plus `review_stage_summaries` rows. This recovery intentionally restores compact screen-ready state only; raw generated artifacts remain local and the existing Portfolio Input run-local review-id recovery stays available for artifact-backed fallback.

Session 8 updated `frontend/README.md` and added `docs/supabase/README.md` to document the storage boundary, public-key-only Supabase setup, the 55 KB soft limit, cloud recovery scope, and the explicit ban on uploading generated artifacts. Frontend typecheck passed after the implementation. Manual Supabase Email OTP, two-user RLS, and live cloud CRUD checks were not run in this local session because no Supabase project credentials were configured in the environment.

## Context and Orientation

Portfolio MRI currently uses a Next.js frontend in `frontend/` and a Python FastAPI backend in `src/api/`. The frontend review journey stores active browser state through `frontend/lib/reviewState.tsx`. It intentionally keeps compact summaries in `localStorage` rather than storing the raw generated evidence bundle. Next.js route handlers in `frontend/app/api/portfolio/` call the local FastAPI service through `frontend/lib/server/fastapiBridge.ts`. The FastAPI app in `src/api/app.py` orchestrates diagnosis, builder, candidate, comparison, verdict, and report stages and reads or writes generated artifacts under local runtime folders such as `runs/` and `Main portfolio/`.

In this plan, “compact summary” means a small UI-ready JSON object with fields already needed to render saved history: portfolio metadata, holdings, review id, stage status, diagnosis headline, launchpad summary, candidate id, comparison status, verdict, confidence, limitations, and safe artifact references. It does not mean full `reviewResult`, full `outputs`, full `portfolio_xray.json`, full `stress_report.json`, CSV exports, PDFs, parquet files, cache files, or generated folders.

## Plan of Work

Session 1 adds a Supabase environment gate in the frontend. The gate returns enabled only when `NEXT_PUBLIC_PMRI_SUPABASE_ENABLED` is exactly `true` and both `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` are non-empty. The UI must show a local demo status when disabled and must not instantiate a Supabase client without valid public configuration.

Session 2 creates a SQL script for the Supabase SQL Editor. The script defines `profiles`, `portfolios`, `portfolio_holdings`, `reviews`, `review_stage_summaries`, and `verdicts`. It enables Row Level Security on every app table. It adds `on delete cascade` for child rows where deletion should cascade: `portfolio_holdings`, `review_stage_summaries`, and `verdicts`. It also adds `unique(user_id, review_id)` on `reviews` to prevent duplicate review rows.

Session 3 adds Next.js Supabase clients and Email OTP Auth. The clients use only public Supabase URL and publishable key. There must be no service role key in frontend code, examples, or runtime configuration. Signed-out enabled mode should show an email login form. Disabled mode should not require login and should keep the local journey usable.

Session 4 adds optional portfolio persistence. A signed-in user can save, list, load, and delete portfolios. Saving a portfolio writes portfolio metadata and replaces its child holdings. Failed cloud writes must show a non-blocking warning and must not interrupt local diagnosis flow.

Session 5 persists compact diagnosis summaries after `/api/portfolio/diagnose` succeeds. The implementation upserts into `reviews` using `(user_id, review_id)` and writes a compact `diagnosis` stage summary. It must not upload full result outputs or generated files.

Session 6 persists later compact stage summaries for `builder`, `candidate`, `comparison`, `verdict`, and `report`. Before writing any `review_stage_summaries.summary`, the implementation serializes the summary and measures byte size. If the payload exceeds 55 KB, it skips the Supabase write, shows a warning, and leaves the current local state intact.

Session 7 adds a saved reviews panel and cloud recovery. Signed-in users can list recent saved reviews and hydrate the current `ReviewStateProvider` from compact Supabase state. Existing run-local recovery by review id remains available as an advanced fallback.

Session 8 validates behavior, updates documentation, and records outcomes. Documentation must explicitly state that Supabase is app-data persistence only and generated outputs remain local/generated evidence.

## Concrete Steps

From the repository root `D:\Рабочий стол\КУРСОР ТУЛА ДИАГНОСТИКА`, implement sessions in order. Do not skip the Session 1 disabled-mode test before enabling cloud behavior.

For Session 1, add frontend helpers under `frontend/lib/supabase/` and a `frontend/.env.example` containing only public keys and the optional flag. Run:

    cd frontend
    npm run typecheck

For Session 2, add a SQL file under a docs or scripts path such as `docs/supabase/supabase_free_schema.sql`. The SQL file must be idempotent enough to re-run during setup when possible. It must not require a service role in the frontend.

For Session 3, add `frontend/lib/supabase/auth.tsx`, `frontend/lib/supabase/server.ts`, `frontend/components/layout/AuthPanel.tsx`, and `frontend/app/auth/callback/route.ts`. Wrap the app in `SupabaseAuthProvider` from `frontend/app/layout.tsx`, render `AuthPanel` under the persistence status in `frontend/components/layout/Sidebar.tsx`, and update `frontend/components/layout/PersistenceStatus.tsx` so enabled mode points users to Email OTP sign-in. Run:

    cd frontend
    npm.cmd run typecheck

For Sessions 3 through 7, use existing frontend state functions in `frontend/lib/reviewState.tsx` as the source for compact UI summaries. Add Supabase persistence as optional side effects after successful local state updates, not as a replacement for local state.

## Validation and Acceptance

The baseline acceptance for every session is that the app starts and works without Supabase environment variables. Disabled mode must not throw import-time or runtime errors. The current local journey remains usable through `localStorage`.

Run this command after frontend code changes:

    cd frontend
    npm run typecheck

When Supabase is enabled, manually verify Email OTP login, portfolio save/load/delete, diagnosis persistence, stage persistence, saved review listing, and cloud recovery. Also verify that user A cannot read or write user B's rows by using Supabase Auth sessions for two different users and confirming RLS denies cross-user access.

Verify the 55 KB guard by attempting to write a deliberately oversized stage summary. Expected behavior: the Supabase write is skipped, a warning is shown, and the current local review state remains usable.

Verify that no implementation path uploads these local/generated locations or artifacts to Supabase: `runs/`, `Main portfolio/`, `cache/`, `pdf files/`, generated candidate folders, full `portfolio_xray.json`, full `stress_report.json`, price history, parquet, CSV exports, or PDFs.

## Idempotence and Recovery

All Supabase integration is additive. If environment variables are absent or invalid, the feature gate disables Supabase and the app behaves as before. If a cloud write fails, the user action still succeeds locally and the user sees a non-blocking warning.

The SQL setup should be safe to inspect and apply manually in the Supabase SQL Editor. Because Row Level Security is mandatory, do not temporarily disable RLS for convenience. If a policy blocks a legitimate operation, fix the policy instead of adding privileged frontend credentials.

## Artifacts and Notes

Session 0 created this plan and the decision log entry. Future sessions should update `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` with concrete test results and any deviations.

The compact-persistence boundary is part of the feature. A successful implementation that writes large generated evidence into Supabase is not acceptable even if the UI appears to work.

## Interfaces and Dependencies

Frontend environment variables are:

    NEXT_PUBLIC_PMRI_SUPABASE_ENABLED
    NEXT_PUBLIC_SUPABASE_URL
    NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY

The implementation may depend on `@supabase/supabase-js` and `@supabase/ssr`. It must not depend on a frontend service-role key, Supabase secret key, private database password, Supabase Storage, Edge Functions, or Realtime for this first version.

The app database interface consists of these Supabase tables: `profiles`, `portfolios`, `portfolio_holdings`, `reviews`, `review_stage_summaries`, and `verdicts`. All tables must have Row Level Security enabled. The `reviews` table must enforce `unique(user_id, review_id)`. Child rows in `portfolio_holdings`, `review_stage_summaries`, and `verdicts` must be deleted automatically when their parent row is deleted.

Revision note 2026-06-11: Initial Session 0 plan created from the user-approved Supabase Free optional persistence plan, with explicit safeguards against frontend secrets, mandatory RLS, duplicate review rows, heavy artifact uploads, and oversized stage summaries.
Revision note 2026-06-12: Session 1 marked complete after adding the frontend environment gate, default local demo status UI, and typecheck evidence.
Revision note 2026-06-12: Session 2 marked complete after adding the Supabase SQL schema script and documenting the soft-limit database decision for `review_stage_summaries.summary_size_bytes`.
Revision note 2026-06-12: Session 3 marked complete after adding optional Email OTP Auth UI, guarded browser/server Supabase clients, the `/auth/callback` route, README auth setup notes, and frontend typecheck evidence.
Revision note 2026-06-12: Session 4 marked complete after adding the Supabase persistence provider plus signed-in save/list/load/delete support for compact portfolio inputs and holdings.
Revision note 2026-06-12: Session 5 marked complete after adding automatic compact diagnosis persistence into `reviews` and `review_stage_summaries` with local-first non-blocking behavior.



Revision note 2026-06-12: Session 6 marked complete after adding optional compact late-stage persistence for builder, candidate, comparison, verdict, and report summaries with a 55 KB soft limit before Supabase writes.
Revision note 2026-06-12: Session 7 marked complete after adding the Saved cloud reviews sidebar panel and compact Supabase review recovery while preserving run-local review-id recovery as the artifact fallback.
Revision note 2026-06-12: Session 8 marked complete after frontend typecheck and documentation updates for Supabase storage boundaries, generated-artifact exclusions, and validation gaps.
