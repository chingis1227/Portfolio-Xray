# Supabase Free optional persistence

Portfolio MRI can optionally use Supabase Free as a compact app-data layer for signed-in browser users. It is disabled unless `NEXT_PUBLIC_PMRI_SUPABASE_ENABLED=true` and both public Supabase values are present in the frontend environment.

Supabase stores only lightweight records: profile metadata, compact Client Fit profile fields, saved portfolio inputs, saved holdings, immutable portfolio-version snapshots, workspace pointers, compact review rows, compact per-stage summaries, archive markers, and compact verdict summaries. The application measures every `review_stage_summaries.summary` payload before writing; payloads above the 55 KB soft limit are skipped, a warning is shown, and local browser state remains active.

Supabase is not an analytics engine and not a generated-artifact store. Do not upload `runs/`, `Main portfolio/`, `cache/`, `pdf files/`, generated candidate folders, full `portfolio_xray.json`, full `stress_report.json`, price history, parquet, CSV exports, PDFs, or raw backend artifact bundles. Those remain local/generated evidence governed by `OUTPUTS.md`.

The staged-review migration keeps the same compact-only boundary. Supabase stores staged progress
as compact rows only: `review_id`, overall review status, current stage, stage statuses, provider
freshness disclosure, safe errors, timestamps, compact verdict/report summaries, and saved
portfolio links. The frontend sanitizes cloud review payloads before writing so local paths,
artifact references, raw generated JSON filenames, raw `review_state.json`, raw artifact path maps,
price history, and full run folders are not persisted. The canonical staged contract is
`docs/contracts/STAGED_REVIEW_STATE_CONTRACT.md`.

Client Fit persistence is compact display-state only. The frontend may save/recover Client Fit
status label/tone, profile label, source-quality label, compact target rows, decision boundary, and
next-test text inside `reviews.compact_summary` and `review_stage_summaries.summary`. It must not
store raw `client_fit_check.json`, generated artifact paths, schema versions, source-artifact maps,
field paths, raw Diagnosis/Stress evidence, or raw Client Fit artifact JSON in Supabase.

Setup starts with `docs/supabase/supabase_free_schema.sql` in the Supabase SQL Editor. New
projects get the account workspace schema from that base file. Existing Supabase projects that
already ran an older schema should run `docs/supabase/2026-06-15_account_workspace_schema.sql` once
in the SQL Editor to add compact Client Fit profile fields, immutable portfolio versions, workspace
state pointers, archive markers, and review-to-version links. If an existing Supabase database
rejects staged rows with `review_stage_summaries_stage_check` for `input`, `data_load`, `xray`,
`stress`, `client_fit`, `problem_classification`, or `launchpad_builder`, run
`docs/supabase/2026-06-15_review_stage_summaries_stage_constraint_patch.sql` once in the SQL Editor
to align the live check constraint with `review_state_v1`.

The frontend uses public browser-safe Supabase clients plus Row Level Security; it must not use service-role keys, secret keys, database passwords, Supabase Storage, Realtime, Edge Functions, or privileged frontend credentials for this optional persistence layer.

## Account workspace model

The production account workspace model is compact and versioned:

```text
User -> Profile / Client Fit -> Portfolio -> Portfolio Version -> Review -> Stage Summaries
```

A portfolio is editable user input. A portfolio version is an immutable compact snapshot of holdings and currency used by a draft or completed review. A review is a calculation record tied to that snapshot. Completed reviews are immutable history; editing a portfolio creates a new draft/review snapshot instead of mutating the old result. `/workspace` may show active portfolios, archived portfolios, latest review state, and compact review history. Login and workspace hydration restore compact state only and must not run diagnosis or refresh market data automatically.

Archive is the normal UI removal behavior for portfolios and reviews. Hard delete is deferred to a separate privacy/admin design and is not the default workspace action.

## Auth email setup

The Portfolio MRI sign-in screen is code-first: the user enters an email, receives a one-time code,
types that code into `/onboarding/sign-in`, and only then continues into onboarding. The frontend
calls `signInWithOtp()` and verifies the typed code with `verifyOtp(..., type: "email")`.

Supabase controls the actual email body and sender identity from the project dashboard. If the
project is left on the default template, users may receive a "Supabase Auth" magic-link email even
though the Portfolio MRI UI is waiting for a code. For the production code-only UX, configure the
Supabase project outside this repo:

1. Open Supabase Dashboard -> Authentication -> Emails / Templates.
2. Update the Email OTP / Magic Link template to show `{{ .Token }}` as the primary sign-in code.
   Use `docs/supabase/auth_email_otp_template.html` as the minimal Portfolio MRI template.
3. Remove or de-emphasize `{{ .ConfirmationURL }}` if the desired public UX is code-only.
4. Open Authentication -> SMTP / Email provider settings and set a verified Portfolio MRI sender,
   for example `Portfolio MRI <no-reply@portfolio-mri.com>`.

These sender/template settings are not changed by a Next.js redeploy. They take effect from the
Supabase project configuration.
