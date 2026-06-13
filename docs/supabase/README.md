# Supabase Free optional persistence

Portfolio MRI can optionally use Supabase Free as a compact app-data layer for signed-in browser users. It is disabled unless `NEXT_PUBLIC_PMRI_SUPABASE_ENABLED=true` and both public Supabase values are present in the frontend environment.

Supabase stores only lightweight records: profile metadata, saved portfolio inputs, saved holdings, compact review rows, compact per-stage summaries, and compact verdict summaries. The application measures every `review_stage_summaries.summary` payload before writing; payloads above the 55 KB soft limit are skipped, a warning is shown, and local browser state remains active.

Supabase is not an analytics engine and not a generated-artifact store. Do not upload `runs/`, `Main portfolio/`, `cache/`, `pdf files/`, generated candidate folders, full `portfolio_xray.json`, full `stress_report.json`, price history, parquet, CSV exports, PDFs, or raw backend artifact bundles. Those remain local/generated evidence governed by `OUTPUTS.md`.

Client Fit persistence is compact display-state only. The frontend may save/recover Client Fit
status label/tone, profile label, source-quality label, compact target rows, decision boundary, and
next-test text inside `reviews.compact_summary` and `review_stage_summaries.summary`. It must not
store raw `client_fit_check.json`, generated artifact paths, schema versions, source-artifact maps,
field paths, raw X-Ray/Stress evidence, or raw Client Fit artifact JSON in Supabase.

Setup starts with `docs/supabase/supabase_free_schema.sql` in the Supabase SQL Editor. The frontend uses public browser-safe Supabase clients plus Row Level Security; it must not use service-role keys, secret keys, database passwords, Supabase Storage, Realtime, Edge Functions, or privileged frontend credentials for this optional persistence layer.
