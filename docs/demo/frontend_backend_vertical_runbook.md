# Frontend Backend Vertical Demo Runbook

This runbook explains how a human operator can run and demo the completed
frontend-to-backend vertical Portfolio MRI flow from the public landing page through required email sign-in, onboarding,
Portfolio Input, and grounded Report / AI Commentary.

Use this guide for the interactive Next.js demo. Use
`docs/demo/full_demo_mvp_runbook.md` for the older CLI/file-only Blocks 5-9 demo.

## Product boundary

The interactive flow is a diagnosis-first decision-support workflow. The public entry experience
prepares non-binding Client Fit context before the diagnostic platform opens:

```text
Landing
-> required email sign-in
-> Onboarding
-> Loading / setup
Portfolio Input
-> Diagnosis
-> Evidence
-> Hypothesis / Builder prepare and Candidate Generation
-> Current vs Candidate Comparison
-> Decision Verdict
-> Report / AI Commentary grounding
```

The product boundary is strict:

- A candidate is a diagnostic portfolio test, not a recommendation.
- Builder setup is a test configuration, not a generated portfolio.
- Current vs Candidate is trade-off evidence, not an order ticket.
- Decision Verdict is non-binding decision support; no-trade and evidence-insufficient are valid.
- Report / AI Commentary is grounded in run-local JSON artifacts; it is not free-form advice.
- Do not describe Equal Weight, Risk Parity, or any generated candidate as "the best portfolio."

## What the demo proves

The demo proves that a user can open a public landing page, sign in with email, complete friendly
onboarding that saves Client Fit context, enter a portfolio in the frontend, run the real Python
diagnostics bridge, select one Launchpad test path, prepare a matching run-local Builder
setup for that exact card, generate exactly one diagnostic candidate, compare the current
portfolio with that candidate, request a Decision Verdict, and read a client-ready
explanation grounded in the produced backend artifacts.

The demo does not prove that the product is a trading system, a multi-candidate optimizer
arena, a polished PDF product, or a personal recommendation engine.

## Run directory strategy

Every real frontend review creates an isolated run directory:

```text
runs/frontend_review_<UTC timestamp>_<short id>/
```

The frontend stores the compact active review id and stage summaries. The full raw backend JSON is
kept in the run directory, not permanently in browser `localStorage`.

Expected run-local artifacts appear in this order:

| Stage | Run-local file |
| --- | --- |
| Diagnosis / problem materialization | `review_result.json` |
| Selected Builder setup | `builder_setup_result.json` |
| Candidate generation | `candidate_generation_result.json` |
| Current vs Candidate | `current_vs_candidate_result.json` |
| Decision Verdict | `decision_verdict_result.json` |
| Report / AI Commentary | `report_commentary_result.json` |
| Grounded commentary context | `ai_commentary_context.json` |

The same run directory also contains the generated input config and the
`analysis_subject/` evidence tree. Treat `runs/frontend_review_*` as generated output, not source.

## Before running

From the repository root:

```powershell
py -3 --version
python --version
where py
where python
```

If `.venv` already exists, use it:

```powershell
.\.venv\Scripts\python.exe --version
```

If `.venv` does not exist:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Install frontend dependencies from `frontend/` if needed:

```powershell
cd frontend
npm.cmd install
```

## Start the interactive demo

From `frontend/`:

```powershell
npm.cmd run dev
```

Open:

```text
http://localhost:3000
```

`dev` starts both FastAPI and Next.js, sets the frontend proxy to the active FastAPI URL, and
prints the exact local site URL plus log paths. Use it for manual demos instead of starting
`next dev` alone, otherwise the frontend may point at a stale or missing backend. This manual path
preserves the normal live/offline provider diagnosis path; deterministic frozen fixture mode is only
for explicit QA automation. Use `npm.cmd run dev:next` only for static frontend work that
intentionally does not call FastAPI routes.

## Manual click-through guide

Start at `http://localhost:3000`. Confirm the public page shows `Diagnose portfolio risk before you
change it` and does not show the platform sidebar or platform step rail. Click **Enter Platform** and confirm it opens `/onboarding/sign-in`. Enter an email, then enter the email code when the verification step appears. If local email auth is unavailable, use the localhost fallback on the sign-in page or open `http://localhost:3000/onboarding/name?dev_bypass=1` for preview only. After sign-in or local fallback, complete the short onboarding screens and let the setup screen redirect to Portfolio Input.

After onboarding, use a simple portfolio that sums to 100%. A stable smoke portfolio is:

| Holding | Type | Weight |
| --- | --- | ---: |
| VOO | Instrument | 50 |
| BND | Instrument | 35 |
| Cash USD | Cash | 15 |

Then demo the flow:

1. On Portfolio Input, confirm the platform sidebar and top journey rail are now visible, Portfolio is Step 1 of 8, and the
   Client Fit profile is ready from onboarding. Enter investor currency `USD` and the holdings above.
2. Run diagnosis. The frontend calls `POST /api/portfolio/diagnose`.
3. On Diagnosis / Evidence, explain the current portfolio first. Do not discuss candidates yet.
4. On Hypothesis, select one Launchpad test path. The right-hand Builder panel shows
   the selected test setup and says setup has not been prepared yet.
5. Click **Prepare Builder setup**. The frontend calls
   `POST /api/portfolio/builder/prepare` with the active `review_id` and
   `selected_card_id`. This writes `builder_setup_result.json` in the same
   `runs/frontend_review_*` directory and stores only the compact active Builder summary
   in browser state.
6. Confirm the panel now says **Builder setup prepared** and shows the plain-language
   test goal, suggested method, setup status, and whether candidate generation is allowed. If you select a different Launchpad card,
   prepare Builder setup again for that exact card before generating.
7. Click **Generate one diagnostic candidate** only after Builder setup is prepared for the
   selected card. The frontend calls `POST /api/portfolio/candidate/generate`.
8. Move to Comparison and generate Current vs Candidate evidence. The frontend calls
   `POST /api/portfolio/comparison/generate`.
9. Move to Verdict and generate the non-binding Decision Verdict. The frontend calls
   `POST /api/portfolio/verdict/generate`.
10. Move to Report and generate grounded commentary. The frontend calls
    `POST /api/portfolio/report/generate`.

Safe narration:

- "The system diagnosed the current portfolio first."
- "The selected Launchpad card first becomes a Builder setup; only then can the UI generate one diagnostic candidate."
- "This candidate is one diagnostic test selected from the Launchpad."
- "The comparison shows trade-offs, including what improved and what worsened."
- "The verdict can say no-trade or evidence-insufficient; it is not forced to recommend action."
- "The report text is grounded in the run-local JSON artifacts."

## Backend bridge commands for operators

The UI normally runs these steps through API routes. Operators can inspect or replay a stage from
PowerShell when debugging a specific `reviewId`. The frontend API sequence for a live run is
`/diagnose -> /builder/prepare -> /candidate/generate -> /comparison/generate -> /verdict/generate -> /report/generate`.

Diagnosis from a frontend payload:

```powershell
.\.venv\Scripts\python.exe scripts\run_review_from_payload.py --payload path\to\payload.json --mode diagnosis_plus_problem --timeout-seconds 900
```

Stage replay for an existing review:

```powershell
.\.venv\Scripts\python.exe scripts\run_review_from_payload.py --prepare-builder --review-id frontend_review_<id> --selected-card-id <launchpad_card_id>
.\.venv\Scripts\python.exe scripts\run_review_from_payload.py --generate-candidate --review-id frontend_review_<id> --selected-card-id <launchpad_card_id> --factory-execution-mode fast
.\.venv\Scripts\python.exe scripts\run_review_from_payload.py --run-comparison --review-id frontend_review_<id> --selected-card-id <launchpad_card_id>
.\.venv\Scripts\python.exe scripts\run_review_from_payload.py --run-verdict --review-id frontend_review_<id> --selected-card-id <launchpad_card_id>
.\.venv\Scripts\python.exe scripts\run_review_from_payload.py --run-report-context --review-id frontend_review_<id> --selected-card-id <launchpad_card_id>
```

Use only one stage flag per command. All stage commands validate that the selected card,
candidate, comparison, verdict, and report context belong to the same active run lineage.

## Stale artifact risks

Do not use these as proof of the active frontend demo:

- Root `config.yml`; the frontend bridge writes a run-local input config instead.
- Root `portfolio_weights.yml` or root `run_result.json`; those are legacy policy artifacts.
- `Main portfolio/` root comparison/verdict files unless the task explicitly targets legacy or
  CLI output.
- Candidate folders such as `minimum cvar constrained portfolio/`; candidate factory side effects
  can exist from previous QA runs.
- Browser raw `pmri.reviewResult.*` keys from older sessions; current hydration cleans them and
  uses compact `pmri.activeReview.v2` state plus `reviewId`. The active Builder setup summary is
  compact state only and must match the currently selected Launchpad card before candidate
  generation is enabled.
- PDFs under `pdf files/`; the frontend vertical flow is JSON/API-first and does not refresh PDFs.

Trust the active `runs/frontend_review_*` directory and the compact frontend state for the current
demo. If a stage refuses to continue because lineage does not match, treat that as a correct safety
failure rather than bypassing it with older JSON.

## Verification commands

Run these checks before presenting the completed vertical flow:

```powershell
cd frontend
npm.cmd run test:api
npm.cmd run test:smoke
npm.cmd run typecheck
npm.cmd run build
```

Then from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py -q --basetemp='tmp\pytest_frontend_bridge_session15'
```

Passing verification means the frontend compiles/builds and the Python bridge contract tests pass,
including the selected-card Builder prepare lineage guard. `npm.cmd run test:smoke` starts a local
Next dev server on an isolated port and checks that the journey pages render; it does not run the
Python backend stages or replace a live browser click-through, which should be performed separately
when the demo environment is available.

## Browser / Playwright QA hygiene

Use this checklist before trusting a screen observation:

1. Use one active dev server and one known URL/port for the check. If the port is already occupied,
   either stop the old server or start a fresh server on another explicit port and record it.
2. Do not run `next build`, `next dev`, typecheck generation, or other `.next` writers at the same
   time against the same `frontend/.next` directory.
3. Check the dev-server terminal/log before judging the UI. If the server shows missing `.next`
   chunks, React Client Manifest errors, or compile failures, restart/fix the server first.
4. Reset or intentionally recover browser state. Do not trust old `localStorage`, old screenshots,
   or old `runs/frontend_review_*` folders as evidence for the active run.
5. In Playwright, take a fresh snapshot before using element refs and re-snapshot after navigation,
   modal/menu changes, route changes, or any substantial UI update.
6. For a real vertical demo, record the active `reviewId` and verify that
   `builder_setup_result.json`, `candidate_generation_result.json`,
   `current_vs_candidate_result.json`, `decision_verdict_result.json`, and
   `report_commentary_result.json` belong to that same run directory.
7. Report visual QA with URL/port, route, active `reviewId` if relevant, state reset/recovery notes,
   screenshots captured, and any area that was not verified.
