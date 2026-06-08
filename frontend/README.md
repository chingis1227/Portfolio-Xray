# Portfolio MRI Frontend Prototype

Clean Next.js/React prototype for Portfolio MRI as an institutional Investment Decision Room.

## Scope boundaries

- No Python analytics engine changes.
- No backend logic changes.
- Live API routes are available for diagnosis, Builder setup prepare, candidate generation,
  comparison, verdict, grounded report commentary, and read-only review recovery:
  - `POST /api/portfolio/diagnose`
  - `GET|POST /api/portfolio/review/recover`
  - `POST /api/portfolio/builder/prepare`
  - `POST /api/portfolio/candidate/generate`
  - `POST /api/portfolio/comparison/generate`
  - `POST /api/portfolio/verdict/generate`
  - `POST /api/portfolio/report/generate`
- The flow is one selected hypothesis at a time; it is not a multi-candidate optimizer arena.
- A candidate is a diagnostic test, not a recommendation. Decision Verdict is non-binding
  decision support, and no-trade / evidence-insufficient are valid outcomes.
- Raw Stitch HTML/CSS/JS is not integrated.
- Imported Stitch screenshots and design tokens are used only as visual reference.

## Architecture

- `app/` contains seven route screens plus root redirect.
- `app/api/portfolio/*` routes write/consume run-local frontend review artifacts through
  `scripts/run_review_from_payload.py`; they do not modify root `config.yml`. The Builder prepare
  route calls the bridge `--prepare-builder` action before candidate generation.
- `components/layout/` contains the application shell, sidebar, top journey progress, and page header.
- `components/ui/` contains reusable card, metric, badge, and hero primitives.
- `components/portfolio/`, `diagnosis/`, `evidence/`, `hypothesis/`, `comparison/`, `verdict/`, and `report/` contain product-stage components.
- `data/demo/` contains local static JSON used by pages during prototype phase.
- `lib/` contains shared journey metadata and TypeScript types.
- `styles/` contains global Tailwind and Portfolio MRI CSS variables.

## Portfolio Input validation

- Investor currency is required.
- Every visible portfolio row must use a selected instrument from the local instrument list and a weight greater than 0.
- At least 2 valid rows are required before diagnosis.
- Portfolio weights must add up to 100%, with a 0.01 tolerance for rounding.
- Weights are never auto-normalized or silently corrected; the diagnosis CTA remains disabled until blocking validation passes.
- The API route repeats lightweight validation before running `scripts/run_review_from_payload.py`.


## Review state and storage

- The real flow is Portfolio Input -> Diagnosis -> Evidence -> Hypothesis / Builder prepare ->
  Candidate Generation -> Current vs Candidate -> Decision Verdict -> Report / AI Commentary.
- The UI stores compact state in `pmri.activeReview.v2`: `reviewId`, portfolio input, diagnosis/evidence/launchpad/builder summaries, selected card/candidate, and stage summaries. Candidate generation is enabled only when the active Builder setup matches the currently selected Launchpad card and says generation is allowed.
- The complete `review_result.json` is not persisted in browser storage. During the current tab session it may remain in memory for immediate rendering; after hydration the UI relies on compact summaries and `reviewId`.
- Portfolio Input includes a read-only recovery control for `frontend_review_*` IDs. It calls
  `/api/portfolio/review/recover`, reads only run-local diagnosis/launchpad/builder artifacts, and
  restores candidate/comparison/verdict/report readiness as false so stale downstream artifacts are
  not silently trusted as active state.
- Legacy raw keys matching `pmri.reviewResult.*` are removed on hydration/write. Future raw access should go through backend artifacts addressed by `reviewId`, not permanent localStorage copies.
- Real backend failures are persisted as `runStatus: "failed"` with a visible error state; static demo data remains clearly separate from `runMode: "real_run"`.

## Run directory strategy

- Every real frontend diagnosis creates `runs/frontend_review_<timestamp>_<id>/`.
- Later stages must use the same `reviewId`; lineage guards reject mismatched Builder, candidate,
  comparison, verdict, or report artifacts. Selecting another Launchpad card clears downstream
  candidate/comparison/verdict/report readiness until Builder setup is prepared for that card.
- Trust the active `runs/frontend_review_*` folder for a live demo. Do not use root
  `run_result.json`, root `portfolio_weights.yml`, `Main portfolio/` root verdict/comparison files,
  candidate portfolio folders, or PDFs as proof of the active frontend review.
- `runs/` is generated output. Do not edit it as source.

## Run locally

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

Optional checks:

```bash
npm run test:api
npm run test:smoke
npm run typecheck
npm run build
```


## Vertical demo runbook

Use [../docs/demo/frontend_backend_vertical_runbook.md](../docs/demo/frontend_backend_vertical_runbook.md) for the human operator path. It covers:

- commands for Python bridge tests and frontend typecheck/build;
- how to start the Next.js frontend;
- the manual Input -> Diagnosis -> Evidence -> Hypothesis -> Builder prepare -> Candidate -> Comparison -> Verdict -> Report click path;
- run directory strategy under `runs/frontend_review_*`;
- stale artifact risks and recovery;
- product language boundaries: candidate is a diagnostic test, Builder setup is not a rebalance instruction, and Verdict/Report are decision-support only.

Quick verification from a fresh terminal:

```powershell
cd frontend
npm.cmd run test:api
npm.cmd run test:smoke
npm.cmd run typecheck
npm.cmd run build
cd ..
.\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py -q --basetemp='tmp\pytest_frontend_bridge_session15'
```
