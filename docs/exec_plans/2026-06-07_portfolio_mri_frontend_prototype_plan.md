# Portfolio MRI Frontend Prototype Foundation

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows `PLANS.md` in the repository root. It is scoped to a frontend prototype only and does not change the Python analytics engine, backend logic, live API behavior, or generated analytics artifacts.

## Purpose / Big Picture

After this change, a user can open a new `frontend/` app and view a clean Portfolio MRI prototype as an institutional Investment Decision Room. The prototype shows seven screens—Portfolio Input, Diagnosis Summary, Evidence Center, Hypothesis Launchpad, Current vs Candidate Comparison, Decision Verdict, and Client-ready Report—using local static JSON data. It deliberately avoids live Python backend integration and treats imported Stitch files only as visual reference, not as source code to copy.

## Progress

- [x] (2026-06-07 00:00Z) Reviewed repository rules, `DESIGN.md`, canonical `docs/design/portfolio_mri_design_system.md`, imported Stitch design-system markdown, imported tokens JSON, and selected Stitch screenshots as visual reference.
- [x] (2026-06-07 00:00Z) Created a separate `frontend/` Next.js/React/TypeScript/Tailwind prototype folder with no changes to Python analytics files.
- [x] (2026-06-07 00:00Z) Added local demo JSON files for all seven requested screens.
- [x] (2026-06-07 00:00Z) Added reusable layout, UI, portfolio, diagnosis, evidence, hypothesis, comparison, verdict, and report components.
- [x] (2026-06-07 00:00Z) Added seven route screens plus root redirect.
- [x] (2026-06-07 00:00Z) Added frontend README and run commands.

## Surprises & Discoveries

- Observation: The repository already has uncommitted changes in `docs/proposals/portfolio_mri_decision_room_mockup.html` and `docs/proposals/portfolio_mri_decision_room_mvp_ui_spec.md` plus untracked `.codex/` and `imported/` folders.
  Evidence: `git status --short` showed those files before frontend implementation. This plan does not touch them.
- Observation: The local environment did not expose a usable global `npm` command during implementation.
  Evidence: `npm --version` was not recognized. The prototype still includes normal `package.json` scripts for a developer machine with Node/npm installed.

## Decision Log

- Decision: Use a standalone `frontend/` app and local JSON imports instead of adding an API or connecting Python.
  Rationale: The user explicitly requested no Python backend modification, no live backend connection, and no API yet.
  Date/Author: 2026-06-07 / Codex.
- Decision: Rebuild the UI from clean React components rather than converting Stitch HTML.
  Rationale: The Stitch audit said the imported output was plain HTML with Tailwind CDN, inline CSS/JS, duplicated styles, and weak accessibility. Option C requires using Stitch only as visual reference.
  Date/Author: 2026-06-07 / Codex.
- Decision: Use dark institutional tokens, blue action states, sparse gold boundaries, green only for improvement, amber only for caution/evidence insufficiency, and red only for risk/worsening.
  Rationale: This matches `docs/design/portfolio_mri_design_system.md` and the imported Portfolio MRI token reference.
  Date/Author: 2026-06-07 / Codex.

## Outcomes & Retrospective

The completed prototype provides the requested frontend foundation: a clean Next.js App Router structure, reusable components, static JSON data, and seven screens that frame Portfolio MRI as a decision-support room rather than a dashboard, trading app, optimizer cockpit, or backend JSON viewer. The remaining work is to install dependencies on a machine with npm, run the dev server, visually review in a browser, and only later design a backend/API contract after the user confirms the frontend direction.

## Context and Orientation

The repository root is `D:/Рабочий стол/КУРСОР ТУЛА ДИАГНОСТИКА`. The current product truth is diagnosis-first Portfolio MRI / Portfolio X-Ray. The new frontend lives in `frontend/` and is intentionally independent from Python files such as `run_portfolio_review.py`, `run_core_diagnostics.py`, and `src/`. Static demo data lives in `frontend/data/demo/`. Reusable components live in `frontend/components/`. Next.js route screens live in `frontend/app/`.

A candidate is a portfolio hypothesis to test, not a recommendation. A verdict is decision support, not a trading instruction. No-trade and evidence-insufficient outcomes are valid and must be visible in the UI.

## Plan of Work

Create `frontend/package.json`, Next.js configuration, TypeScript configuration, Tailwind configuration, and global styles. Add local JSON files for the seven screens. Add typed data helpers in `frontend/lib/`. Add layout components for the sidebar, top journey progress, and page header. Add requested reusable content components. Add one route per screen. Add `../../frontend/README.md` documenting architecture, data usage, Stitch usage boundary, and run commands.

## Concrete Steps

From the repository root, create files under `frontend/` only plus this plan file under `docs/exec_plans/`. Do not edit Python files. On a developer machine with Node.js and npm installed, run:

    cd frontend
    npm install
    npm run dev

Then open `http://localhost:3000`. The root route redirects to `/portfolio-input`, and sidebar navigation exposes all seven screens.

## Validation and Acceptance

Acceptance is manual and user-visible for this prototype. After running the app, a user should see a premium dark Portfolio MRI interface with sidebar navigation, journey progress, and seven screens. The Portfolio Input screen must show investor currency once at portfolio level, not repeated per row. The table must show Ticker / Instrument and Weight %. The verdict screen must include decision-support wording and say it is not a trading instruction. The comparison and hypothesis screens must state that candidates are hypothesis tests, not recommendations.

The implementation can also be inspected without running the server by confirming that `frontend/data/demo/*.json` files are imported into route pages and components, no `api/` route exists, no Python files changed, and no imported Stitch `index.html` is referenced from frontend source.

## Idempotence and Recovery

The work is additive. If dependency installation fails, delete `frontend/node_modules/` and retry `npm install`. If a later iteration changes the UI direction, keep `frontend/data/demo/` and component names stable where possible so the future API contract can map onto the same screen model. To remove the prototype, delete only `frontend/` and this ExecPlan file; do not delete Python analytics or generated output folders.

## Artifacts and Notes

The visual reference came from the imported Stitch screenshots and design tokens, especially the dark sidebar, top journey, large decision cards, compact evidence panels, and gold decision boundary accents. Raw Stitch HTML, inline CSS, inline JavaScript, and Tailwind CDN code were not integrated.

## Interfaces and Dependencies

The frontend depends on Next.js, React, TypeScript, Tailwind CSS, PostCSS, and Autoprefixer as declared in `frontend/package.json`. It currently has no backend dependency, no API dependency, and no Python dependency. The main interfaces are JSON files imported from `frontend/data/demo/` and typed in `frontend/lib/types.ts`.
