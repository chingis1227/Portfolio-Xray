---
description:
alwaysApply: true
---

# AGENTS.md

This file is the compact operating guide for agents working in this repository. Detailed behavior lives in the linked source-of-truth documents; do not duplicate long specs here.

Update this file only when agent operating rules, source-of-truth routing, generated-output policy, Browser/Playwright hygiene, or editing guidance changes.

## Current Product Truth

Portfolio MRI is a diagnosis-first, current-portfolio-first investment decision-support system. It is not optimizer-first.

Canonical current product flow:

```text
Input Portfolio
-> Portfolio Diagnosis
-> Stress Test Lab
-> Client Fit Check
-> Problem Classification
-> Candidate Launchpad
-> Portfolio Alternatives Builder
-> Candidate Generation
-> Current vs Candidate Comparison
-> Decision Verdict
-> AI Commentary / grounding
-> Monitoring / What Changed
```

Current frontend route reality:

```text
/
-> /onboarding/sign-in
-> /onboarding/name
-> /onboarding/investor-type
-> /onboarding/loading
-> /portfolio-input
-> /diagnosis
-> /evidence
-> /client-fit
-> /hypothesis
-> /comparison
-> /verdict
-> /report
```

Returning signed-in users with completed onboarding and saved workspace, portfolio, draft, or
review history may branch from sign-in/loading to `/workspace` before continuing or starting a new
review at `/portfolio-input`. `/workspace` is an account home and history hub, not a product
calculation stage.

`/onboarding/goals` is a compatibility-only redirect to `/onboarding/investor-type`; do not promote
it into current route maps. `/onboarding/name?dev_bypass=1` is a local preview shortcut, not the
canonical product path.

`/client-profile` is an advanced/manual Client Fit editor, not the normal onboarding entry step.
`/sandbox/components` and developer/debug provenance surfaces are local review/debug surfaces, not
canonical product journey routes.

The implementation remains partly CLI/file-driven and still contains older optimizer/report/scorecard-heavy infrastructure. Treat that older infrastructure as support code unless a task explicitly targets it.

## Client Fit V1 Boundary

Client Fit V1 is current, active, and non-binding diagnostic context.

It is part of the current web journey through onboarding plus `/client-fit` after Stress Lab and before Hypothesis. Backend/CLI compatibility remains: missing Client Fit context writes a `not_provided` compatibility state instead of failing the run. The backend may write `analysis_subject/client_fit_check.json` and downstream screens may use bounded Client Fit context.

Client Fit must not be described as suitability approval, trade advice, an optimizer mandate, proof that no action is needed, or a reason to hide material portfolio issues.

## Main Commands

Install dependencies:

```bash
pip install -r requirements.txt
```

Run tests:

```bash
python -m pytest
```

Run core diagnostics (Blocks 1-3 only):

```bash
python run_core_diagnostics.py [--no-cache] [--dry-run]
```

Run the default portfolio-first diagnosis review:

```bash
python run_portfolio_review.py [--dry-run] [--skip-candidates] [--with-pdf] [--legacy-full-pdf]
```

Default `run_portfolio_review.py` is diagnosis-only and uses the `site_api` output profile unless an explicit export/PDF option is selected.

Run the canonical one-candidate vertical demo:

```bash
python scripts/run_blocks_5_to_9_vertical_flow.py --method equal_weight
```

Run the explicit backend factory-id compatibility path:

```bash
python run_portfolio_review.py --candidates equal_weight
```

Use this only when the backend factory id is already known; it is not the canonical visible Builder-to-Block-7 proof.

Run advanced/research candidate batches:

```bash
python run_portfolio_review.py --with-candidates
python run_portfolio_review.py --mode full
```

Run legacy policy compatibility flows only when explicitly needed:

```bash
python run_optimization.py
python run_report.py
python run_mvp_workflow.py [--workflow policy-only|policy-current|full-decision|diagnosis-only]
```

Candidate and robust portfolio commands are indexed in `docs/specs/candidate_portfolios_spec.md`, `docs/specs/candidate_factory_spec.md`, `docs/specs/robust_mv_spec.md`, and `docs/specs/robust_scenario_optimization_spec.md`.

## Production Stack Snapshot

- Public domain: `portfolio-mri.com`.
- DNS, domain, and frontend hosting: Cloudflare / Workers & Pages project `portfolio-xray` (legacy
  infrastructure project id; public product name remains Portfolio MRI).
- Python API backend: Render web service `portfolio-mri-backend`, public health URL `https://portfolio-mri-backend.onrender.com/api/v1/health`.
- Database/persistence: Supabase stores compact review records and stage summaries only; generated artifacts remain backend/run-local.
- Frontend-to-backend bridge: Cloudflare Pages calls Render through `PMRI_FASTAPI_BASE_URL=https://portfolio-mri-backend.onrender.com`.
- Shared internal API auth: set the same `PMRI_FASTAPI_INTERNAL_SECRET` in Cloudflare Pages and Render.
- Website link: https://portfolio-mri.com/
- Render runtime defaults: start FastAPI with `uvicorn src.api.app:app --host 0.0.0.0 --port $PORT`; set `PMRI_STAGED_REVIEW_RUNTIME=direct`.
- Render memory guardrail: keep `PMRI_STAGED_REVIEW_MAX_WORKERS=1` unless the instance has been load-tested with staged diagnosis plus candidate generation.
- Market data dependencies: Yahoo/yfinance for prices and FRED `DTB3` for USD risk-free data; production Render should set `FRED_API_KEY` to reduce FRED timeout failures.
- After changing Cloudflare env vars, redeploy Cloudflare Pages. After changing Render env vars or backend code, redeploy the Render service.

## Source of Truth Routing

Before changing behavior, follow `WORKFLOW.md` and start from `RULES.md`.

Use this current source-of-truth hierarchy:

1. Agent operating rules: `AGENTS.md`.
2. Task workflow and documentation sync: `WORKFLOW.md`, `docs/contracts/DOC_SYNC_CONTRACT.md`.
3. Current implementation contract: `SPEC.md`.
4. Product flow and boundaries: `docs/contracts/PRODUCT_FLOW_CONTRACT.md`, `PRODUCT.md`.
5. Screen flow and route responsibilities: `docs/contracts/SCREEN_CONTRACTS.md`, `docs/specs/frontend_screen_contracts.md`, `frontend/README.md`.
6. Staged web review state, progress semantics, and compact persistence boundary:
   `docs/contracts/STAGED_REVIEW_STATE_CONTRACT.md`.
7. Artifact-to-screen routing and same-run lineage: `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md`.
8. Runtime entrypoints: `docs/runtime_entrypoints.md`, `docs/specs/portfolio_review_workflow_spec.md`, `OUTPUTS.md`.
9. Data rules: `DATA.md` and owning `docs/specs/*.md` files.
10. Testing and QA: `TESTING.md`, `docs/contracts/QA_CONTRACT.md`, `KNOWN_ISSUES.md`.
11. Design: `DESIGN.md`, `docs/design/current_website_structure.md`, `docs/design/portfolio_mri_design_system.md`.
12. Information architecture and UI copy discipline:
   `docs/contracts/INFORMATION_ARCHITECTURE_COPY_CONTRACT.md`.
13. Decisions and history: `DECISIONS.md`, `CHANGELOG.md`, `docs/audits/README.md`, `docs/exec_plans/README.md`.
14. ExecPlan rules for large/risky work: `PLANS.md`.

Product concept documents, historical audits, completed ExecPlans, and archived legacy docs are traceability only. They do not override current specs, contracts, code, frontend routes, formulas, output contracts, or runtime behavior.

## Do Not Treat As Current Core MVP

Do not describe these as the current Core MVP product flow unless a current spec explicitly promotes them:

- Portfolio Health Score as the main product answer.
- Robustness Scorecard as the main product answer.
- Macro Dashboard / Macro Overlay.
- Full multi-candidate ranking / optimizer arena.
- Assumption Sensitivity, Pareto / Dominance, Regret Analysis, and Model Risk Diagnostics as primary screens.
- Full Action Plan / Rebalancing Advisor.
- Full Decision Journal.
- Advanced monitoring UI or multi-client monitoring workspace.
- Crisis Replay UI and What Happens If simulator UI.
- Client Fit suitability approval.
- Asset Diagnostics, Max Sharpe, tax-aware optimization, turnover-aware optimizer objective, tactical tilt, full custom constraints UI, or multi-client workspace.
- Polished PDF report product as the default output path.

If these capabilities exist in code or generated outputs, classify them as `Advanced`, `Backend evidence`, `Technical artifact`, `Legacy`, `Generated support artifact`, or `Future/backlog`; do not promote them into current product truth merely because files exist.

## Core Agent Rules

- In chat with the user, communicate in Russian by default and as with a non-professional developer: explain ongoing work simply, point out misunderstandings or risky assumptions respectfully, and ask necessary project questions in plain language.
- Repository language policy is strict: all in-project artifacts must be created, edited, named, and documented in English regardless of the language used in chat, voice dictation, source prompts, or user phrasing.
- Do not introduce Russian, mixed-language prose, non-English file names, or mojibake into repository files. If legacy Russian text or broken encoding is found while touching a file, normalize it to clear English or remove/replace it when exact translation is not required for current behavior.
- Keep changes scoped to the requested behavior and owning files.
- Prefer existing helpers and repo patterns over new parallel implementations.
- Treat diagnostics as non-binding unless a canonical spec says otherwise.
- Treat diagnosis-first, current-portfolio-first, and decision-support boundaries as authoring constraints, not repeated primary UI disclaimers. Follow `docs/contracts/INFORMATION_ARCHITECTURE_COPY_CONTRACT.md` for visible copy.
- Do not manually require final weights in `config.yml`; optimization writes `portfolio_weights.yml` and `run_result.json`.
- ETF and stock taxonomy are annotation-only in V1 unless a canonical spec changes that boundary.
- Preserve full precision during calculations; round only at final export/report stage when governed by metric specs.
- Do not invent formulas, estimators, scenarios, constraints, statuses, or data rules when a canonical spec exists.
- Do not demote or delete implementation capabilities only because older concept docs omitted them; classify them as `Preserve`, `Advanced`, `Legacy`, or `Requires Review` unless a canonical spec or explicit task says otherwise.

## Documentation and Verification

Documentation sync is required for meaningful code, behavior, workflow, output, interface, QA, or source-of-truth changes. Use `WORKFLOW.md` and `docs/contracts/DOC_SYNC_CONTRACT.md` to decide which documents to update. Use `TESTING.md` and `docs/contracts/QA_CONTRACT.md` to decide which checks to run.

After meaningful changes:

- update owning docs when behavior, logic, formulas, configs, workflows, outputs, interfaces, or shared helpers change;
- verify no stale references remain after renames, removals, or moved documents;
- run the narrowest reliable verification first and broaden when risk warrants it;
- report any unverified area with the reason and blocker.

A task is done only when the requested change is implemented, relevant docs are updated or explicitly waived, verification is run or explicitly waived, unrelated files are not changed, and unverified areas are reported.

## Browser / Playwright QA

For frontend visual QA or browser click-throughs, avoid stale dev servers, stale browser state, and stale Playwright element references.

- Every frontend UI change must be visually checked with Playwright or an equivalent browser-based QA flow, even for small copy, spacing, styling, visibility, responsive, or component changes. If browser visual QA cannot be completed, explicitly report that it was not completed and why.
- Start from a clean, active local target: use a fresh localhost port when possible, confirm the exact URL, and do not assume an already-open tab or old server is the current build.
- Check dev-server terminal/logs before judging the screen. If Next reports missing `.next` chunks, React Client Manifest errors, or a failed compile, fix/restart the server before making product/UI conclusions from the browser.
- Do not run `next build`, `next dev`, typecheck generation, or other `.next` writers concurrently against the same `frontend/.next` directory during visual QA.
- Treat browser `localStorage`, old `runs/frontend_review_*` folders, screenshots, and generated artifacts as stale unless explicitly created or recovered for the active run being tested.
- In Playwright, take a fresh snapshot before using element refs and re-snapshot after navigation, modal/menu changes, route changes, or major UI updates.
- For Portfolio MRI vertical demos, follow `docs/demo/frontend_backend_vertical_runbook.md` and verify the active `reviewId`, selected Launchpad card, Builder setup, candidate, comparison, verdict, and report all belong to the same run-local artifact chain.
- When reporting visual QA, include URL/port, route, active `reviewId` if relevant, sample mode status, browser state reset/recovery, screenshots captured, and any unverified area.

## ExecPlans

For new complex tasks, large changes, or refactors, follow `PLANS.md` before implementation.

- Read `PLANS.md` fully before authoring or changing an ExecPlan.
- Create or update checked-in ExecPlans under `docs/exec_plans/`.
- Keep ExecPlans as living documents: update `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` as work proceeds.
- Small, localized fixes do not need a separate ExecPlan unless the user asks for one.

## Generated Outputs

Do not treat generated artifacts as source unless the task explicitly targets them.

Common generated paths include:

- `cache/`
- `output/`
- `results_csv/`
- `Main portfolio/`
- portfolio variant output folders
- `runs/frontend_review_*`
- `portfolio_weights.yml`
- `__pycache__/`
- `.pytest_cache/`
- `pdf files/`
- `pdf_md_sources/`
- generated CSV/TXT/HTML/PNG/PDF/Markdown/CSS sidecars

## Specialized agents (routing)

| Task | Agent |
| --- | --- |
| New ticker / ETF or stock universe / stress block EQ-CA onboarding | `.cursor/agents/asset-taxonomy-stress-classification-agent.md` |

## Editing Guidance

- Use `rg` or `rg --files` for searches when available.
- Use `apply_patch` for manual file edits.
- Do not revert user changes or unrelated dirty working-tree changes.
- Do not use destructive git commands unless explicitly requested.
- Prefer non-interactive git commands.
- Keep final responses concise and include changed files, verification performed, and any unverified area.
