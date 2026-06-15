# Portfolio MRI Frontend

Next.js/React Core MVP surface for Portfolio MRI as an institutional Investment Decision Room.
The current implemented journey is still a local/frontend vertical flow, not a polished hosted
product or trading system.

## Scope boundaries

- No Python analytics engine changes.
- No Python analytics or backend calculation changes live in this frontend package.
- Live API routes are available for diagnosis, Builder setup prepare, candidate generation,
  comparison, verdict, grounded report commentary, and read-only review recovery. The normal
  frontend path keeps the existing Next.js route URLs for compatibility, but those handlers proxy
  to the local FastAPI backend instead of launching Python scripts directly:
  - `POST /api/portfolio/diagnose` -> `POST /api/v1/reviews/staged`, returning a `review_id`
    immediately instead of waiting for the full diagnosis run. Portfolio Input navigates to
    `/diagnosis` after the staged start response; the Diagnosis route owns progress polling and
    same-run recovery.
  - `GET /api/portfolio/review/status?reviewId=...` -> `GET /api/v1/reviews/{review_id}/status`
    for staged progress polling.
  - `GET|POST /api/portfolio/review/recover` -> `GET /api/v1/reviews/{review_id}`
  - `POST /api/portfolio/builder/prepare` -> `POST /api/v1/reviews/{review_id}/builder`
  - `POST /api/portfolio/candidate/generate` -> `POST /api/v1/reviews/{review_id}/candidate`
  - `POST /api/portfolio/comparison/generate` -> `POST /api/v1/reviews/{review_id}/comparison`
  - `POST /api/portfolio/verdict/generate` -> `POST /api/v1/reviews/{review_id}/verdict`
  - `POST /api/portfolio/report/generate` -> `POST /api/v1/reviews/{review_id}/report`
- The flow is one selected test path at a time; it is not a multi-candidate optimizer arena.
- A candidate is a diagnostic test, not a recommendation. Decision Verdict is non-binding
  decision support, and no-trade / evidence-insufficient are valid outcomes.
- Old imported design artifacts are not integrated and are not current design authority.
- Current design and route structure are documented in `../DESIGN.md` and `../docs/design/current_website_structure.md`.

## Architecture

- `app/` contains the public landing page, the required email sign-in step, the short onboarding flow, the platform route screens,
  and API route compatibility handlers. The root route now renders the public landing page instead
  of redirecting directly into an internal product step.
- `app/api/portfolio/*` routes are compatibility proxies over the local FastAPI v1 API. They keep
  the current screen-facing response shape while FastAPI runs the Python review stages and enforces
  typed request/response contracts. The proxy layer is deployment-safe for Edge-style route
  handlers: it passes explicit same-run lineage ids from frontend state to FastAPI and builds
  screen-compatible responses from FastAPI public envelopes instead of reading `runs/...` files
  from the Next.js runtime. Screens consume display models from `reviewState` and FastAPI public
  envelopes rather than raw artifact internals. The proxy no longer spawns
  `scripts/run_review_from_payload.py`.
- `components/layout/` contains the application shell, sidebar, top journey progress, and page header.
- `components/ui/` contains reusable card, metric, badge, and hero primitives.
- `components/portfolio/`, `diagnosis/`, `evidence/`, `hypothesis/`, `comparison/`, `verdict/`, and `report/` contain product-stage components.
- `data/demo/` contains local static JSON used by sample/demo page states.
- `data/instrumentUniverse.ts` is generated from the canonical `../config/etf_universe.yml`
  and `../config/stock_universe.yml` taxonomies. Regenerate it from the repo root with
  `.\.venv\Scripts\python.exe scripts\generate_frontend_instrument_universe.py` after
  taxonomy changes.
- `lib/` contains shared journey metadata and TypeScript types.
- `lib/generated/api-types.ts` is generated from the local FastAPI OpenAPI contract. It is a
  contract safety net for the staged migration. As of Session 07, FastAPI can create and recover
  diagnosis reviews and can run Builder setup, Candidate Generation, Current-vs-Candidate
  Comparison, Decision Verdict, and grounded Report context through
  `POST /api/v1/reviews`, `GET /api/v1/reviews/{review_id}`,
  `POST /api/v1/reviews/{review_id}/builder`, `POST /api/v1/reviews/{review_id}/candidate`,
  `POST /api/v1/reviews/{review_id}/comparison`,
  `POST /api/v1/reviews/{review_id}/verdict`, and
  `POST /api/v1/reviews/{review_id}/report`. The existing Next.js `/api/portfolio/*` URLs now
  proxy to those FastAPI endpoints for the normal frontend path. Diagnosis interpretation
  Session 08 adds generated types for the expanded `DiagnosisSummary` interpretation-chain display
  fields (`diagnosis_evidence_items`, `root_cause_narrative`, `metric_to_diagnosis_trace`,
  `rejected_alternatives`, `professional_rationale_refs`, and `recommendation_boundary`).
  Session 10 updates the frontend adapters so diagnosis, candidate, comparison, verdict, and report
  summaries prefer these FastAPI public display fields, including downstream
  `evidence_chain_context`, and downstream compatibility routes no longer require local filesystem
  artifact reads in the Next.js runtime.
  Staged pipeline Session 5 migrates the normal diagnosis route to
  `POST /api/v1/reviews/staged` plus status polling through
  `GET /api/v1/reviews/{review_id}/status`. After the diagnosis-stage chain is ready, the frontend
  uses the existing review recovery path to build compact screen summaries from same-run artifacts.
- `../docs/contracts/FASTAPI_SCREEN_MAPPING.json` is the governance map between FastAPI operations,
  generated response `data` fields, and approved Core MVP screen routes. Backend schema changes must
  regenerate `lib/generated/api-types.ts` and update this mapping before fields are surfaced in UI.
- `styles/` contains global Tailwind and Portfolio MRI CSS variables.

## Portfolio Input validation

- The normal web journey starts with the public landing page and requires email sign-in. New users
  then run a short one-question-at-a-time onboarding flow. Returning signed-in users with a completed
  Portfolio MRI onboarding profile are routed to `/workspace` when saved workspace, portfolio, draft,
  or review history exists. `/workspace` restores saved work and compact review history without
  running diagnosis. Completed users without saved workspace data may continue to Portfolio Input,
  and the saved non-binding Client Fit profile is restored before Run diagnosis is allowed.
- The five-question intake maps risk behavior into a Client Fit preset using stress-loss reaction,
  withdrawal horizon, temporary-loss limit, return target, and concentration response.
- The Portfolio Input `Adjust intake` control edits the saved Client Fit target rows in a modal. It
  does not send the user back through the five-question onboarding flow, and saving manual values
  reclassifies the displayed preset from the edited target rows.
- Investor currency is required and currently limited in the UI to USD or EUR.
- New Portfolio Input sessions start with empty holding fields rather than the old static demo allocation.
- Legacy unsubmitted demo draft portfolios in browser storage are cleared on hydration so the old
  SPY/QQQ/BND/GLD/Cash allocation does not reappear as a default input.
- Every visible portfolio row must use a selected instrument from the local instrument list and a weight greater than 0.
- At least 2 valid rows are required before diagnosis.
- Portfolio weights must add up to 100%, with a 0.01 tolerance for rounding.
- Weights are never auto-normalized or silently corrected; the diagnosis CTA remains disabled until blocking validation passes.
- The Next.js compatibility route repeats lightweight validation before calling FastAPI.
- After changing FastAPI route contracts or generated API types, restart both the FastAPI backend
  and the Next.js frontend. A stale backend that does not expose
  `POST /api/v1/reviews/staged` is reported as a frontend/backend version mismatch, not as a
  generic Python diagnosis failure.
- The backend bridge retries the same diagnosis command once when the first attempt returns a
  transient empty market-data panel on a cold cache. The retry does not change formulas or accept
  partial results.


## Review state and storage

- The real user-facing flow is Landing -> required email sign-in -> Onboarding -> Workspace for returning users -> Portfolio Input ->
  Diagnosis -> Stress Test Lab -> Client Fit
  -> Hypothesis / Builder prepare and Candidate Generation -> Current vs Candidate -> Decision Verdict -> Report / grounded
  explanation preview. `/workspace` is an account home and history hub, not a calculation stage. If comparison evidence is current but metrics are unavailable, the UI may still
  continue to Verdict so the system can show an evidence-insufficient decision-support outcome
  instead of silently blocking the journey.
- The UI stores compact display state in `pmri.activeReview.v2`: the Client Fit profile, `reviewId`, portfolio input, diagnosis/stress/Client Fit evidence, launchpad/builder summaries, selected card/candidate, and stage summaries. Core screens consume these display models, not raw backend artifact trees. Candidate generation is enabled only when the active Builder setup matches the currently selected Launchpad card and says generation is allowed.
- The staged migration adds compact `review_state_v1` progress fields to the active review state:
  overall run status, current stage, per-stage statuses, provider status, mode (`demo_qa` or `live`),
  and safe stage errors. Portfolio Input saves `reviewId` immediately and moves the user to
  `/diagnosis` without waiting for the full backend calculation. The Diagnosis route polls staged
  status but keeps per-stage status rows and provider freshness as internal operational state; the
  normal UI shows only a simple product-facing running message and safe errors. It hydrates screen
  summaries through run-local recovery after the
  Diagnosis, Stress, Client Fit, Problem Classification, and Launchpad/Builder evidence chain is
  available. The canonical contract is `../docs/contracts/STAGED_REVIEW_STATE_CONTRACT.md`.
- When Supabase is enabled and the user is signed in, the active review may also keep a compact
  link to the selected cloud portfolio so diagnosis-history rows can point back to the saved
  portfolio input without uploading generated evidence.
- The complete `review_result.json` is not persisted in browser storage. During the current tab session compatibility routes may include bounded FastAPI-derived compatibility fields for older screen adapters, but screen rendering relies on compact display summaries, FastAPI public envelopes, explicit lineage ids, and `reviewId`; Next.js route handlers must not read run-local JSON files as part of the normal deployed path.
- Portfolio Input includes a read-only recovery control for `frontend_review_*` IDs. It calls
  `/api/portfolio/review/recover`, reads bounded run-local diagnosis/evidence/launchpad/builder
  artifact payloads from the FastAPI recovery envelope, and
  restores candidate/comparison/verdict/report readiness as false so stale downstream artifacts are
  not silently trusted as active state.
- Legacy raw keys matching `pmri.reviewResult.*` are removed on hydration/write. Future raw access should go through backend artifacts addressed by `reviewId`, not permanent localStorage copies.
- Real backend failures are persisted as `runStatus: "failed"` with a visible error state; static demo data remains clearly separate from `runMode: "real_run"`.

## Run directory strategy

- Every real frontend diagnosis creates `runs/frontend_review_<timestamp>_<id>/`.
- Backend staged diagnosis writes `runs/frontend_review_<timestamp>_<id>/review_state.json` as the
  active progress source for the future polling path. It records stage state only; it does not
  replace the canonical calculation artifacts and must not be uploaded to Supabase as a raw artifact.
- Later stages must use the same `reviewId`; lineage guards reject mismatched Builder, candidate,
  comparison, verdict, or report artifacts. Selecting another Launchpad card clears downstream
  candidate/comparison/verdict/report readiness until Builder setup is prepared for that card.
- Trust the active `runs/frontend_review_*` folder for a live demo. Do not use root
  `run_result.json`, root `portfolio_weights.yml`, `Main portfolio/` root verdict/comparison files,
  candidate portfolio folders, or PDFs as proof of the active frontend review.
- `runs/` is generated output. Do not edit it as source.

## Run locally

Supabase persistence is optional, but the canonical public product path still starts with email sign-in. With local or incomplete Supabase setup, the sign-in page exposes a localhost-only fallback button so the site can be tested without a working email code. The active compact review is stored in browser `localStorage`.
To enable Supabase-backed auth for later cloud persistence sessions, set only public browser-safe
values:

```powershell
NEXT_PUBLIC_PMRI_SUPABASE_ENABLED=true
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=your-public-publishable-key
```

If the flag is not exactly `true`, or either public value is blank, the Supabase gate remains
disabled and no Supabase browser client is created.

Canonical public entry requires an email OTP before onboarding when Supabase is available. The
platform sidebar shows the signed-in email and a `Sign out` control on authenticated workspace
screens. Configure Supabase Auth Email OTP in the Supabase dashboard and allow the local callback URL
for legacy magic-link compatibility:

```text
http://localhost:3000/auth/callback
```

The callback exchanges a legacy public magic-link auth code for a browser session and returns to the
sign-in gate, which then routes completed users to `/workspace` when saved workspace/history exists
or to Portfolio Input when no saved workspace exists yet. New users continue to onboarding. The
primary UI asks for the email OTP code. No service-role key, secret key, database password, Supabase
Storage, Realtime channel, or Edge Function is used by the frontend.

For production email branding and code-only UX, update Supabase project settings outside this repo:

- Authentication -> Emails / Templates: make the relevant Email OTP/Magic Link template show
  `{{ .Token }}` as the primary login code and remove or de-emphasize `{{ .ConfirmationURL }}`.
  A minimal Portfolio MRI code template is checked in at
  `docs/supabase/auth_email_otp_template.html`.
- Authentication -> SMTP or Email provider settings: set sender name/from name to `Portfolio MRI`
  and use a verified product/domain sender address, for example `Portfolio MRI <no-reply@portfolio-mri.com>`.
- Redeploy the frontend after changing Cloudflare environment variables, but note that Supabase
  sender/template changes take effect from the Supabase project configuration, not from Next.js code.

Current Supabase-backed behavior is now the foundation for the dedicated `/workspace` account area:

- signed-in users can save, list, load, update, and delete compact portfolio inputs through the
  existing persistence layer when that UI is intentionally exposed;
- staged diagnosis progress automatically attempts compact cloud upserts into `reviews` and compact
  canonical stage rows such as `input`, `xray`, `stress`, `client_fit`,
  `problem_classification`, and `launchpad_builder` in `review_stage_summaries`; successful local
  diagnosis still writes a compact `diagnosis` summary row when screen summaries are available;
- later successful local stages can save compact `builder`, `candidate`, `comparison`, `verdict`,
  and `report` rows in `review_stage_summaries`; before each stage write the app measures the
  serialized JSON payload and skips the cloud write with a warning when it exceeds the 55 KB soft
  limit;
- signed-in users use `/workspace` to list recent compact reviews, open read-only compact history, and recover the current browser state from Supabase summaries when live same-owner lineage is available; run-local recovery by `reviewId` on Portfolio Input remains the advanced fallback for local generated artifacts;
- login and workspace hydration never run diagnosis, refresh market data, generate candidates, compare portfolios, or regenerate verdict/report artifacts automatically;
- completed reviews are immutable compact history tied to the portfolio snapshot/version used at run time; editing a portfolio starts a new draft and keeps old completed reviews visible in history;
- cloud failures stay non-blocking: the local browser journey and local diagnosis/stage completion
  still succeed;
- Supabase remains an app-data layer only. The frontend does **not** upload `runs/`,
  `Main portfolio/`, `cache/`, PDFs, generated candidate folders, full `portfolio_xray.json`,
  full `stress_report.json`, price history, parquet, CSV exports, or raw generated artifact bundles.
  Cloud payloads are sanitized before write to strip local paths, artifact references, raw generated
  JSON filenames, and artifact path maps.

```powershell
cd frontend
npm install
npm.cmd run dev
```

`dev` starts both FastAPI and Next.js, sets the Next.js proxy to the active FastAPI URL, waits
for both servers to respond, and prints the local site link plus log file paths. This is the
preferred manual localhost launcher because it prevents stale or mismatched FastAPI ports from
surfacing as frontend `Method Not Allowed` errors while preserving the normal live/offline provider
diagnosis path. Use `npm.cmd run dev:next` only for static frontend work that intentionally does not
call FastAPI routes.
If Next.js reports missing `.next` chunks, React Client Manifest errors, or failed compilation,
restart the dev server before making visual QA conclusions.

Live vertical QA helper:

```powershell
cd frontend
npm.cmd run qa:vertical -- --scenario-limit 3
```

This starts fresh FastAPI and Next.js servers on free localhost ports, opens a clean Playwright
browser context, clears browser storage before each scenario, runs diagnosis through report via the
frontend compatibility API routes, probes stale selected-card rejection, and writes screenshots or
DOM fallbacks plus `qa-report.json` under `../output/playwright/`. Demo QA mode uses fixed fixture
diagnosis text across scenarios, so the helper treats identical diagnosis summaries as a warning
when the route chain and stale-card 409 proof pass. If live market data is
unavailable, treat the failure as a data-provider blocker and inspect the report/logs before making
frontend or product conclusions.

Open `http://localhost:3000` to start at the landing page. Click `Enter Platform`, sign in with email when auth is available, complete the short onboarding, and the app will open the signed-in workspace when saved workspace/history exists or Portfolio Input when no saved workspace exists yet. For local preview while email sign-in is unavailable, open `http://localhost:3000/onboarding/name?dev_bypass=1`; this is a development shortcut, not the canonical product path.
Override the FastAPI URL for the Next.js proxy with `PMRI_FASTAPI_BASE_URL` only when intentionally
using a separately managed backend. `FASTAPI_BASE_URL` is also accepted as a compatibility alias for
manual local launches.

Optional checks:

```bash
npm run test:api
npm run test:smoke
npm run typecheck
npm run build
```

Regenerate FastAPI contract types from the repository root after intentional FastAPI schema changes:

```powershell
.\.venv\Scripts\python.exe scripts\generate_fastapi_api_types.py
.\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py
```

`verify_fastapi_contract_governance.py` also checks that public diagnosis/comparison/verdict/report
claim fields keep source/provenance companions and that governed frontend/API copy does not introduce
unqualified advice-like language.


## Vertical demo runbook

Use [../docs/demo/frontend_backend_vertical_runbook.md](../docs/demo/frontend_backend_vertical_runbook.md) for the human operator path. It covers:

- commands for Python bridge tests and frontend typecheck/build;
- how to start the Next.js frontend;
- the public Landing -> required email sign-in -> Onboarding entry path before Portfolio Input, plus the local-only `dev_bypass` preview path;
- the manual Portfolio Input -> Diagnosis -> Stress Test Lab -> Hypothesis / Builder prepare and Candidate Generation -> Comparison -> Verdict -> Report click path;
- run directory strategy under `runs/frontend_review_*`;
- stale artifact risks and recovery;
- product language boundaries: candidate is a diagnostic test, Builder setup is not a rebalance instruction, and Verdict/Report are decision-support only.

Quick verification from a fresh terminal:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py -q
cd frontend
npm.cmd run test:api
npm.cmd run test:smoke
npm.cmd run typecheck
npm.cmd run build
```

`tests/test_frontend_review_bridge.py` remains available for the legacy/debug script helper, but it
is no longer the normal frontend route-path gate.
