# QA Contract

Status: **canonical QA and verification contract** for Portfolio MRI / Portfolio X-Ray Core MVP product, frontend, backend, visual, language, documentation, and git gates.

Scope: required checks for future docs, frontend, backend, design, language, artifact, and product-flow sessions. This contract defines what to run, in what order, what evidence to report, and which checks may be waived only with an explicit reason. It does not change runtime behavior, backend formulas, frontend implementation, generated artifacts, tests, package scripts, or documentation sync policy by itself.

This contract exists to prevent product-code-design drift. A future change that alters required checks, package scripts, visual QA hygiene, forbidden-term scans, or documentation verification must update this file and the owning source-of-truth documents in the same change.

## Source-of-truth order

Use this document for cross-cutting QA selection and final reporting. Use these adjacent sources for details:

- `TESTING.md` for repository-wide verification strategy, backend pytest selection, docs verification, CLI smoke policy, and known full-suite caveats.
- `frontend/package.json` for the actual frontend script names.
- `../../frontend/README.md` for frontend architecture, local run commands, run-local review state, and vertical-flow checks.
- `AGENTS.md` for Browser / Playwright QA hygiene, generated-output boundaries, and final response expectations.
- `docs/demo/frontend_backend_vertical_runbook.md` for manual vertical demo, active `reviewId`, stale-artifact risks, and browser QA reporting.
- `docs/contracts/PRODUCT_FLOW_CONTRACT.md` for product-step order and product boundaries.
- `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md` for artifact routing, same-run lineage, stale-data rules, and generated-output trust boundaries.
- `docs/contracts/SCREEN_CONTRACTS.md` for screen-level QA checks and route responsibilities.
- `docs/contracts/PRESENTATION_LANGUAGE_RULES.md` for forbidden terms, approved replacements, and scan commands.
- `docs/contracts/DESIGN_SYSTEM_CONTRACT.md` for visual QA rules, badge semantics, CTA states, and forbidden visual directions.
- `docs/contracts/DOC_SYNC_CONTRACT.md` for documentation-impact checks.

## QA principle

Verify the changed risk, not just the changed file. Start with the narrowest reliable check, then broaden when the change touches shared helpers, route state, artifact lineage, backend contracts, generated outputs, or user-visible product flow.

A session is not complete until it reports:

1. changed files;
2. checks run and results;
3. checks not run and why;
4. unverified areas or blockers;
5. whether a commit was made. No commit should be made unless the user explicitly requests it.

## Fast local QA shortcuts

Use these repository-root PowerShell shortcuts when the goal is fast, repeatable local QA without the heavy full-suite/runtime checks:

| Gate | Command | Purpose |
| --- | --- | --- |
| Fast daily QA | `.\scripts\qa_fast.ps1` (`.\scripts\qa_fast.cmd` if PowerShell policy blocks scripts) | Canonical quick gate: docs verification, core offline workflow smoke, product-bundle adapter checks, frontend typecheck, and frontend API route tests. It intentionally skips full pytest, live E2E, frontend build, frontend smoke, and browser visual QA. |
| Contract QA | `.\scripts\qa_contracts.ps1` (`.\scripts\qa_contracts.cmd` if PowerShell policy blocks scripts) | Candidate factory/comparison contract and golden-fixture gate. It intentionally skips networked/live checks, full pytest, and the still-open KI-2026-05-26-001 drift test. |

Full `python -m pytest` remains a manual/nightly or risk-based check. Live core/full E2E remains operator proof for demos, releases, or explicit requests, not the default daily gate.

## Standard frontend checks

The actual scripts in `frontend/package.json` are:

| Script | Actual Windows command from `frontend/` | Purpose |
| --- | --- | --- |
| `typecheck` | `npm.cmd run typecheck` | TypeScript compile contract: `tsc --noEmit`. |
| `build` | `npm.cmd run build` | Next.js production build contract: `next build`. |
| `test:api` | `npm.cmd run test:api` | Node API-route tests: `node --test tests/api-route-tests.cjs`. |
| `test:smoke` | `npm.cmd run test:smoke` | Frontend smoke tests: `node --test tests/frontend-smoke-tests.cjs`. |
| `qa:vertical` | `npm.cmd run qa:vertical` | Live FastAPI + Next.js + Playwright vertical QA helper. It starts fresh local FastAPI/Next servers on free ports, clears browser storage, runs multiple portfolio scenarios through the frontend compatibility API routes, probes stale selected-card rejection, captures screenshots or DOM fallbacks, and writes `output/playwright/**/qa-report.json`. |
| `dev` | `npm.cmd run dev` | Manual/browser QA local server: `next dev`. |
| `start` | `npm.cmd run start` | Serve a built app: `next start`. |
| `lint` | `npm.cmd run lint` | Optional lint script currently declared as `next lint`; run when lint or style rules are touched, or when requested. |

For future frontend implementation sessions, run the standard checks sequentially from `frontend/` unless a narrower or broader set is justified:

    npm.cmd run typecheck
    npm.cmd run build
    npm.cmd run test:api
    npm.cmd run test:smoke

Do not run these concurrently on Windows when they may write or read `frontend/.next` at the same time. See the Windows `.next` race warning below.

## Windows `.next` race warning

On Windows, do **not** run `next build`, `next dev`, typecheck generation, smoke tests, or any other `.next` writer concurrently against the same `frontend/.next` directory.

Required behavior:

1. Use one active local frontend target for visual QA.
2. Do not run `npm.cmd run build` while `npm.cmd run dev` or a smoke test is writing/serving the same `.next` tree.
3. If Next reports missing `.next` chunks, React Client Manifest errors, or compile failures, fix or restart the server before drawing product/UI conclusions.
4. If a stale dev server may be open, use a fresh localhost port and record it in the QA report.
5. Do not treat old browser state, old screenshots, or old `runs/frontend_review_*` folders as evidence for the active run.

## Backend targeted pytest policy

Backend verification follows `TESTING.md`: run the narrowest reliable pytest first, then broaden by risk.

Minimum policy:

1. For docs-only changes, no backend pytest is required unless the docs changed executable commands, schemas, or behavior claims.
2. For one backend module or behavior, run the focused test file first, for example `python -m pytest tests/test_name.py -q`.
3. For shared helpers, artifact adapters, or product-bundle paths, add adjacent focused suites from `TESTING.md`.
4. For portfolio math, optimizer behavior, data alignment, config schema, stress logic, report contracts, or generated-output contracts, consider full `python -m pytest` only after focused tests or when risk warrants it.
5. For CLI or generated-output behavior, add the affected CLI smoke command and artifact inspection only when the session explicitly targets executable behavior or generated artifacts.
6. Do not refresh generated outputs by default. Generated folders such as `cache/`, `output/`, `results_csv/`, `Main portfolio/`, `runs/`, portfolio variant folders, PDFs, and generated Markdown/report sources are evidence, not source, unless the task explicitly targets them.

Examples from `TESTING.md` for product-bundle work:

    python -m pytest tests/test_problem_classification.py tests/test_candidate_launchpad.py tests/test_portfolio_alternatives_builder.py tests/test_current_vs_candidate.py tests/test_decision_verdict.py tests/test_ai_commentary_context.py tests/test_light_monitoring_summary.py -q

For frontend bridge lineage changes, `../../frontend/README.md` and the vertical runbook currently reference:

    .\.venv\Scripts\python.exe -m pytest tests\test_frontend_review_bridge.py -q --basetemp='tmp\pytest_frontend_bridge_session15'

Use the current project Python policy from AGENTS: prefer `.\.venv\Scripts\python.exe` if `.venv` exists; otherwise use `py -3` to create it when Python is needed.

## Visual QA requirements

Visual QA is required when a frontend route, screen component, layout, design token, status badge, CTA, user-facing state, or product copy changes.

Before trusting a browser observation:

1. Start from a clean, active local target. Use a fresh localhost port when possible.
2. Record the exact URL and port.
3. Record the route tested, for example `/hypothesis?sample=1`.
4. Record active `reviewId` when the run is a real vertical flow.
5. Record whether sample mode, demo data, or a real run was used.
6. Reset browser state or intentionally recover it; do not silently trust old `localStorage`.
7. Check the dev-server terminal/log before judging the screen.
8. In Playwright, take a fresh snapshot before using element refs and re-snapshot after navigation, modal/menu changes, route changes, or major UI updates.
9. For vertical Portfolio MRI demos, verify the selected Launchpad card, Builder setup, candidate, comparison, verdict, and report all belong to the same run-local artifact chain.
10. Capture screenshots when visual layout, state colors, or screen hierarchy are part of acceptance.
11. Report every unverified route or state with the reason.

Visual QA reports must include:

- URL and port;
- route;
- active `reviewId` if relevant;
- sample mode / demo data / real run status;
- browser state reset or recovery notes;
- screenshots captured, if any;
- dev-server health or relevant log status;
- unverified areas.

## Live vertical Browser/Playwright QA helper

Use this helper for explicit live FastAPI/frontend acceptance, not as a default fast gate:

```powershell
cd frontend
npm.cmd run qa:vertical -- --scenario-limit 3
```

The helper is intentionally defensive:

1. starts FastAPI and Next.js on fresh available `127.0.0.1` ports;
2. passes `PMRI_FASTAPI_BASE_URL` to Next.js so route handlers use the active FastAPI process;
3. uses a fresh Playwright browser context and clears `localStorage` / `sessionStorage` before each scenario;
4. checks server readiness and scans Next logs for compile, `.next`, module, and React Client Manifest failures before trusting product observations;
5. captures screenshots when possible and writes HTML/text DOM fallbacks when Playwright screenshot capture fails;
6. verifies diagnosis, Builder, Candidate, Comparison, Verdict, and Report lineage through the frontend API routes;
7. rejects a stale selected-card probe with HTTP 409 before marking the run passed.

If the helper fails because the live market-data provider cannot return prices, report it as a live-data blocker with the QA report path; do not describe it as a frontend, browser-state, stale-artifact, or product-copy failure unless the report/log evidence shows that.

## Forbidden-term scan policy

Run forbidden-term scans whenever UI copy, report copy, display labels, frontend adapters, screen components, or product language changes. These scans are evidence-gathering checks: inspect matches manually and distinguish primary user-facing copy from developer-only code, API validation, tests, docs, and contract evidence.

From the repository root, use the scan commands maintained in `docs/contracts/PRESENTATION_LANGUAGE_RULES.md`.

Primary UI forbidden-term scan:

    rg -n "backend|artifact|JSON|valid JSON|source problem|selected hypothesis|setup preview|run-local|candidate generation readiness|not available yet|disabled|true|false|n/a|outputs\\.|stale downstream|baseline_or_candidate|no comparison or verdict was generated|factory|candidate_generation|implementation order|source artifact|Backend does not expose|No PDF generation|AI Commentary context|best portfolio|must rebalance|trade now|execute|buy|sell" frontend/app frontend/components

Adapter leakage scan:

    rg -n "portfolio_xray\\.json|stress_report\\.json|problem_classification\\.json|candidate_launchpad\\.json|portfolio_alternatives_builder\\.json|candidate_generation\\.json|current_vs_candidate\\.json|decision_verdict\\.json|ai_commentary_context\\.json|what_changed_summary\\.json|selection_decision\\.json|output_manifest\\.json|run_result\\.json|portfolio_weights\\.yml|Review ID|frontend_review_|analysis_subject|valid JSON|tombstone|skipped_existing|optimizer arena|Selection Engine|Action Engine" frontend/app frontend/components frontend/lib

Advice/execution scan:

    rg -n "recommended portfolio|best portfolio|winner|must rebalance|trade now|execute trade|buy|sell|guaranteed improvement|tax advice|client suitability approved|implementation order" frontend/app frontend/components frontend/lib

State placeholder scan:

    rg -n "\\bn/a\\b|\\bnull\\b|\\bundefined\\b|\\btrue\\b|\\bfalse\\b|disabled|not available yet" frontend/app frontend/components

Contract evidence scan:

    rg -n "Presentation Language Rules|candidate is not|verdict is not|grounded explanation|backend/artifact/JSON|displayLabels|forbidden" docs/contracts

Expected result for implementation sessions: no forbidden primary UI leakage. Matches in `frontend/lib/displayLabels.ts` may be valid replacement rules; matches in API routes may be valid technical validation; matches in docs/contracts are allowed as evidence.

## Git gates

Every meaningful session must run from the repository root:

    git diff --check
    git status --short

Rules:

1. `git diff --check` must pass before reporting completion.
2. `git status --short` must be reported so pre-existing dirty files and new changes are visible.
3. Do not use broad `git add .`, checkout, reset, or cleanup commands in this repository unless the user explicitly requests them.
4. Do not commit, push, merge, or change branches unless the user explicitly requests it.
5. If committing is approved later, stage only intended files and run `git diff --cached --check` before commit.

Note: this working tree may contain pre-existing dirty files from earlier sessions. Treat them as user/worktree state and do not revert or stage them unless explicitly scoped.

## Docs-only vs implementation verification matrix

| Session type | Minimum checks | Usually not required | Required final-response note |
| --- | --- | --- | --- |
| Docs-only contract or plan update | Verify referenced commands/paths are real when changed; targeted `rg` if stale terms or command names changed; `git diff --check`; `git status --short`. | Frontend build, frontend smoke, backend pytest, visual QA, generated-output refresh. | State that no runtime/frontend/backend code changed and why runtime tests were not run. |
| Docs-only command or QA documentation change | Confirm commands against `frontend/package.json`, `TESTING.md`, runbooks, or entrypoint files; `git diff --check`; `git status --short`. | Full test suite unless executable behavior claims changed. | State which sources were checked for command accuracy. |
| Frontend route/screen implementation | `npm.cmd run typecheck`; `npm.cmd run build`; `npm.cmd run test:api`; `npm.cmd run test:smoke`; visual QA for changed route; relevant forbidden-term scans; git gates. | Backend full pytest unless API contracts or Python bridge behavior changed. | Include route, URL/port, sample/real mode, screenshots, and unverified states. |
| Frontend API route / Python bridge / run-local lineage | Standard frontend checks; focused bridge/backend pytest; visual or smoke check if route behavior is user-visible; git gates. | Full pytest unless shared backend contracts changed. | Include active `reviewId` or explain why visual lineage was not exercised. |
| Backend artifact/schema/product-bundle implementation | Focused pytest from `TESTING.md`; adjacent product-bundle tests when shared; CLI smoke/artifact inspection when generated outputs are intentionally affected; docs sync; git gates. | Frontend build unless frontend consumption or route behavior changed. | State generated outputs changed or not changed. |
| Product flow, screen contract, artifact routing, language, or design implementation | Combine frontend checks, relevant backend focused tests if data contracts changed, visual QA, forbidden-term scans, docs sync, git gates. | None by default; broaden by risk. | State which contracts were checked and updated or why no contract change was needed. |
| Generated-output refresh | Approved CLI command; artifact inspection; generated-output language scan when reports/PDF/text changed; git gates. | Source code changes unless explicitly scoped. | List generated paths refreshed and confirm they were intentionally targeted. |
| Full journey QA | Standard frontend checks; vertical visual QA from Input through Report; run-local `reviewId` chain verification; forbidden-term scans; git gates; targeted backend bridge test when relevant. | Full backend pytest unless product logic changed. | Include URL/port, route coverage, active `reviewId`, sample/real status, screenshots, and gaps. |

## Mapping from change type to required checks

| Change type | Required checks |
| --- | --- |
| Product flow / product boundary | Review `PRODUCT_FLOW_CONTRACT.md`; update owning docs if needed; targeted stale-language `rg`; `git diff --check`; `git status --short`. Add frontend/backend tests only if implementation changes. |
| Artifact producer, location, lifecycle, or stale-data rule | Review `ARTIFACT_TO_SCREEN_MAP.md`; focused backend tests for affected artifact; frontend checks if UI consumption changes; same-run lineage QA when frontend state changes; git gates. |
| Screen route, CTA, unlock state, or empty/blocked state | Standard frontend checks; visual QA for changed route; forbidden-term scans; review `SCREEN_CONTRACTS.md`; git gates. |
| UI copy, display labels, report wording, or forbidden terms | Forbidden-term scans; standard frontend checks if code changed; visual QA if primary copy changed; review `PRESENTATION_LANGUAGE_RULES.md`; git gates. |
| Design tokens, color semantics, badges, cards, CTA styling, or layout | Standard frontend checks; visual QA with screenshots; review `DESIGN_SYSTEM_CONTRACT.md`; forbidden visual direction checklist; git gates. |
| API route, frontend bridge, or active `reviewId` lineage | Standard frontend checks; `tests\test_frontend_review_bridge.py` or narrower relevant pytest; visual/smoke route check; git gates. |
| FastAPI public contract, generated API types, or FastAPI-to-screen mapping | `.\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py`; `.\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py tests\test_fastapi_contract_governance.py -q`; `cd frontend && npm.cmd run typecheck`; git gates. |
| Backend formulas, stress logic, optimizer behavior, data alignment, or metric contracts | Focused pytest first; adjacent or full pytest by risk; CLI smoke/artifact inspection if outputs changed; docs sync; git gates. |
| Runtime commands or documented CLI examples | Verify command exists; targeted docs `rg`; focused CLI/workflow tests if behavior claim changed; `git diff --check`; `git status --short`. |
| Documentation-only source-of-truth update | Verify links/commands touched; optional `python scripts/verify_docs.py` or `python -m pytest tests/test_docs_links.py -q` when links or source maps changed; git gates. |
| Test or QA workflow change | Verify commands against package/test files; update `TESTING.md` and this contract if permanent; git gates. |

## Final response reporting requirements

Final responses must be concise and evidence-based. Include:

- changed files;
- what changed in plain language;
- checks run and whether they passed or failed;
- checks not run and why;
- unverified areas, blockers, or assumptions;
- whether frontend/backend/runtime/generated outputs were changed;
- whether a commit was made. If no commit was requested, say no commit was made.

For visual QA work, additionally include URL/port, route, active `reviewId` if relevant, sample/real mode, browser state reset/recovery, screenshots captured, and unverified areas.

For docs-only sessions, explicitly say that runtime tests were not run because no runtime code changed, unless executable examples or commands required test execution.

## Acceptance checklist for future sessions

- [ ] The session selected checks based on the changed risk.
- [ ] Frontend commands match `frontend/package.json` if frontend checks are listed.
- [ ] Backend pytest selection follows `TESTING.md` and starts narrow.
- [ ] Visual QA follows AGENTS and the vertical runbook when UI changed.
- [ ] Forbidden-term scans were run or explicitly waived with a reason when language/copy changed.
- [ ] `git diff --check` passed.
- [ ] `git status --short` was reviewed and reported.
- [ ] Documentation impact was checked against the active ExecPlan and `docs/contracts/DOC_SYNC_CONTRACT.md`.
- [ ] Generated outputs were not treated as source unless explicitly targeted.
- [ ] No commit, push, branch switch, or generated-output refresh happened without user approval.

## Validation for this contract

Session 6 is documentation-only. Minimum checks after editing this file:

    git diff --check
    git status --short

Required evidence checks for Session 6:

    (Get-Content frontend\package.json -Raw | ConvertFrom-Json).scripts | Format-List | Out-String
    rg -n "frontend|typecheck|test:api|test:smoke|git diff --check|docs-only|Documentation-only|visual|Playwright|\.next|forbidden" TESTING.md docs\demo\frontend_backend_vertical_runbook.md AGENTS.md docs\exec_plans\2026-06-10_product_code_design_synchronization_plan.md

This session does not require running frontend builds, frontend tests, backend pytest, or visual QA because it creates a docs-only QA contract and does not change implementation code.


## Session 09 display-adapter QA

Confirm Core MVP screens consume display models instead of raw artifacts; use targeted `rg` checks for direct `reviewResult.outputs.*` use in screen files plus `npm.cmd run test:api` and `npm.cmd run typecheck`.
