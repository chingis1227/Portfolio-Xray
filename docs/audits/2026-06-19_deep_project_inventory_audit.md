# Deep Project Inventory and Consistency Audit

Date: 2026-06-19

Status: Current audit snapshot.

Scope: repository inventory, documentation/source-of-truth consistency, frontend/backend static
health, generated-output hygiene, verification gates, and obvious correctness or governance risks.
No runtime, frontend, backend, generated-output, formula, data, or UI behavior was intentionally
changed by this audit.

This audit is evidence and planning input. It does not override `SPEC.md`, `RULES.md`,
`WORKFLOW.md`, `OUTPUTS.md`, `TESTING.md`, `DATA.md`, contract documents, detailed specs, or
current code behavior.

## Executive Verdict

The project is not fundamentally broken: the main frontend production build, frontend typecheck,
frontend API tests, frontend smoke/copy checks, documentation verifier, Python compile check, and
focused backend/API regression bundle passed during this audit.

The main problem is not a single fatal product bug. The main problem is accumulated governance and
maintenance debt: generated artifacts are mixed into tracked source, the official FastAPI/frontend
copy-governance check currently fails, the lint command is not CI-safe, the full pytest suite is
not a practical green gate, and source-of-truth route/copy terminology has small but real drift.

Recommended cleanup order:

1. Fix failing governance gates that future work is supposed to rely on.
2. Reconcile test-suite status so the team knows which failures are accepted and which are new.
3. Separate tracked source from generated portfolio artifacts and local run debris.
4. Clean source mojibake and English-only violations.
5. Normalize route documentation and legacy compatibility routes.
6. Refactor only after the above evidence gates are stable.

## Verification Evidence

Commands run from the repository root unless noted:

| Check | Result |
| --- | --- |
| `git status --short --branch` | Clean `main...origin/main` before audit edits. |
| `.\.venv\Scripts\python.exe -m compileall -q src scripts run_portfolio_review.py run_core_diagnostics.py run_report.py run_optimization.py run_mvp_workflow.py` | Passed. |
| `.\.venv\Scripts\python.exe scripts\verify_docs.py` | Passed: `docs verification: OK`. |
| `cd frontend; npm.cmd run typecheck` | Passed. |
| `cd frontend; npm.cmd run test:api` | Passed: 91 tests. |
| `cd frontend; npm.cmd run test:smoke` | Passed: 1 test. |
| `cd frontend; npm.cmd run test:copy` | Passed: 3 tests. |
| `cd frontend; npm.cmd run build` | Passed. Next.js built 20 static pages and dynamic API routes. |
| `.\.venv\Scripts\python.exe -m pytest --collect-only -q` | Passed collection: 2007 tests collected in 38.09s. |
| `.\.venv\Scripts\python.exe -m pytest tests\test_fastapi_app.py tests\test_frontend_review_bridge.py tests\test_architecture_consistency.py -q` | Passed: 116 tests. |
| `.\.venv\Scripts\python.exe run_portfolio_review.py --dry-run` | Passed and printed the diagnosis-only plan. |

Checks that did not pass or did not complete:

| Check | Result |
| --- | --- |
| `.\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py` | Failed on unqualified advice-like phrases in frontend source. Details below. |
| `cd frontend; npm.cmd run lint` | Not CI-safe: `next lint` opened an interactive ESLint setup prompt. |
| `.\.venv\Scripts\python.exe -m pytest -q` | Timed out after about 304 seconds; no full-suite result was recorded. |
| `.\.venv\Scripts\python.exe -m pytest -q --maxfail=1` | Timed out after about 184 seconds before producing a first failure. |

Live market-data E2E, browser visual QA, and generated-output refreshes were not run. This audit did
not change UI behavior, and repository rules say generated outputs must not be refreshed unless the
active task explicitly targets them.

## Repository Inventory Snapshot

Tracked files by top-level area, based on `git ls-files`:

| Area | Tracked files |
| --- | ---: |
| `docs/` | 377 |
| `tests/` | 271 |
| `src/` | 170 |
| `frontend/` | 152 |
| `scripts/` | 50 |
| `.cursor/` | 32 |
| `legacy/` | 29 |
| portfolio variant output folders | hundreds of generated-like artifacts |

Runtime and app shape:

- Python backend/API: `src/api/app.py`, `src/api/reviews.py`, `run_portfolio_review.py`,
  `run_report.py`, and supporting modules under `src/`.
- Frontend: Next.js app router under `frontend/app/`.
- Frontend routes discovered from source:
  `/`, `/onboarding/sign-in`, `/onboarding/name`, `/onboarding/investor-type`,
  `/onboarding/loading`, `/onboarding/goals`, `/workspace`, `/portfolio-input`, `/diagnosis`,
  `/evidence`, `/client-fit`, `/client-profile`, `/hypothesis`, `/comparison`, `/verdict`,
  `/report`, `/sandbox/components`, plus API routes under `/api/portfolio/*` and `/auth/callback`.
- Current product route chain in the compact top-level product docs excludes `/workspace` and
  `/onboarding/goals`, while contract/frontend docs discuss `/workspace` as the signed-in account
  home. This is a documentation-shape mismatch, not a build failure.

Large modules and maintenance hotspots:

| File | Approximate lines | Risk |
| --- | ---: | --- |
| `frontend/data/instrumentUniverse.ts` | 33886 | Generated/static data is embedded as a very large source file. |
| `src/stress_factors.py` | 5923 | High-change-risk monolith. |
| `src/portfolio_xray.py` | 4092 | High-change-risk monolith. |
| `src/portfolio_variants.py` | 3758 | High-change-risk monolith. |
| `src/api/reviews.py` | 3405 | API orchestration is large and hard to audit locally. |
| `frontend/lib/reviewState.tsx` | 3518 | Frontend state lifecycle is large and central. |
| `frontend/lib/supabase/persistence.tsx` | 1500 | Persistence layer is large and central. |
| `frontend/components/portfolio/PortfolioInputTable.tsx` | 1475 | Main input UI is large and likely expensive to change safely. |
| `frontend/lib/server/fastapiBridge.ts` | 1276 | Backend bridge is large and security/lineage-sensitive. |

## Priority Findings

### P0 / Release-Blocking Governance

#### P0-1: FastAPI/frontend contract governance check fails on current source

Evidence:

- Command: `.\.venv\Scripts\python.exe scripts\verify_fastapi_contract_governance.py`
- Result: failed.
- Reported files included:
  - `frontend/components/evidence/stressStoryModel.ts`
  - `frontend/components/ui/MetricMatrix.tsx`
  - `frontend/lib/diagnosisDisplayModel.ts`
  - `frontend/lib/server/fastapiBridge.ts`
  - `frontend/lib/siteExplanationPresenter.ts`

The script flags advice-like phrases such as `best portfolio`, `must rebalance`, `trade now`,
`suitability approved`, and `winner`.

Important nuance: several flagged strings are inside sanitizer or blacklist patterns, not direct
primary UI copy. That means there are two possible root causes:

1. the source should avoid embedding forbidden public phrases literally even inside sanitizers; or
2. the governance scanner needs an explicit allowlist for sanitizer/negative-test contexts.

Risk:

- The repository has a canonical command for guarding public copy and FastAPI screen mapping, but it
  is red on the current tree.
- Future agents can either ignore the command or waste time re-discovering the same failure.
- Public advice-boundary enforcement becomes less trustworthy.

Recommended fix:

1. Decide whether sanitizer regexes may contain raw forbidden phrases.
2. If not, encode the blacklist without literal public phrases or use tokenized phrase assembly.
3. If yes, update `scripts/verify_fastapi_contract_governance.py` with a narrow allowlist for
   sanitizer declarations and negative-test fixtures only.
4. Add or update a focused test so `verify_fastapi_contract_governance.py` passes cleanly.
5. Record the result in `KNOWN_ISSUES.md` if not fixed immediately.

### P1 / High-Impact Engineering and QA Debt

#### P1-1: `npm run lint` is not non-interactive

Evidence:

- Command: `cd frontend; npm.cmd run lint`
- Result: `next lint` opened an interactive ESLint configuration prompt.

Risk:

- This cannot be used in CI, scripts, or unattended agent verification.
- The package exposes a lint script that looks official but is not a reliable gate.

Recommended fix:

- Either configure ESLint explicitly or remove/replace the lint script with a non-interactive
  command.
- Update `frontend/README.md` and `TESTING.md` if the intended frontend lint gate changes.

#### P1-2: Full pytest status is stale and not quickly reproducible

Evidence:

- `TESTING.md` and `KNOWN_ISSUES.md` say the latest recorded full-suite audit on 2026-06-14 was
  `34 failed, 1887 passed, 3 skipped`.
- This audit collected 2007 tests, which is a different total from the recorded baseline.
- A full run timed out after about 304 seconds.
- A `--maxfail=1` probe timed out after about 184 seconds before producing a first failure.

Risk:

- The project cannot honestly claim full-suite green.
- The known-failure baseline may be stale because the collected test count changed.
- Agents may rely only on focused tests and miss cross-layer regressions.

Recommended fix:

1. Run the exhaustive QA runner or full pytest in a dedicated long-running session.
2. Refresh `KNOWN_ISSUES.md` with the current exact failure count and grouping.
3. Split slow or network-sensitive tests from default local pytest if they block fast feedback.
4. Keep focused checks as normal gates until the full baseline is reconciled.

#### P1-3: Tracked generated-like portfolio artifacts contradict generated-output policy

Evidence:

- `AGENTS.md`, `WORKFLOW.md`, `DOC_SYNC_CONTRACT.md`, and `OUTPUTS.md` say generated outputs are not
  source unless explicitly targeted.
- `git ls-files` shows tracked portfolio variant output folders such as:
  - `hierarchical risk parity portfolio/`
  - `minimum cvar constrained portfolio/`
  - `minimum cvar uncapped portfolio/`
  - `maximum diversification unconstrained portfolio/`
  - `risk budget by asset portfolio/`
  - `risk budget by asset-class portfolio/`
  - `robust mean variance constrained portfolio/`
  - `robust mean variance uncapped portfolio/`
  - `analysis_mv_lambda_sensitivity/`
  - `analysis_robust_mv_lambda_calibration/`
- These folders include generated JSON, TXT, HTML, PNG, and stress report artifacts.
- Sample tracked generated-like payload size for 10 folders is about 281 files / 38.13 MB.
- The largest tracked files are generated stress reports around 1.9-2.4 MB each.

Risk:

- Source and generated evidence are mixed.
- Agents may mistake stale generated artifacts for current product truth.
- Repository diffs and searches are noisier than necessary.
- `.gitignore` does not fully prevent all currently tracked generated-like variants, and ignored
  rules do not remove files already tracked.

Recommended fix:

1. Inventory tracked generated-like folders and classify each as `fixture`, `golden`, `legacy
   evidence`, or `remove from tracking`.
2. Move true fixtures under explicit `tests/fixtures/` or `docs/audits/` evidence folders with
   small curated payloads.
3. Remove stale generated output folders from tracking only after confirming no tests depend on
   them by path.
4. Expand `.gitignore` for remaining generated portfolio variant naming patterns.
5. Update `OUTPUTS.md` or `TESTING.md` if any generated folder is intentionally retained as a
   fixture.

#### P1-4: Source mojibake exists in active frontend display normalization code

Evidence:

- `frontend/lib/displayLabels.ts` contains mojibake-looking dash text in regexes that normalize
  diagnostic section/block labels.
- Repository search found mojibake in active source, not only historical docs.

Risk:

- Regexes may fail to match normal dash/en dash text.
- The project has an English-only/no-mojibake rule, and this violates it in executable frontend
  source.

Recommended fix:

- Replace mojibake dash fragments with explicit ASCII hyphen and Unicode en dash/em dash support,
  or normalize dashes before applying replacements.
- Add a small unit test for `normalizeDisplayLabel` covering `Diagnostic sections 2-2.6`,
  `Diagnostic sections 2-2`, and equivalent en dash forms.

### P2 / Product, Documentation, and Maintainability Drift

#### P2-1: Route inventory and canonical route-chain docs are slightly out of sync

Evidence:

- Source includes `/workspace` and `/onboarding/goals`.
- Product/contracts explain `/workspace` as signed-in account home, but compact route chains in
  top-level docs still show a linear journey without `/workspace`.
- `/onboarding/goals` exists only as a compatibility redirect to `/onboarding/investor-type`; it is
  not listed in the canonical route chain.

Risk:

- QA operators and future agents can test the wrong route order.
- Compatibility routes can look like product routes if not labeled.

Recommended fix:

- Update compact route-chain wording to distinguish:
  - canonical new-user path;
  - returning-user `/workspace` branch;
  - compatibility-only `/onboarding/goals` redirect;
  - advanced/manual `/client-profile`.
- Keep `SCREEN_CONTRACTS.md`, `PRODUCT_FLOW_CONTRACT.md`, `PRODUCT.md`, `AGENTS.md`, and
  `frontend/README.md` aligned.

#### P2-2: Checked-in ExecPlans contain non-English text or local absolute paths with non-English characters

Evidence:

- Search for Cyrillic characters found checked-in ExecPlans containing local absolute paths and a
  Russian completion phrase.
- The active repository rule says in-project artifacts must be English-only and must not introduce
  Russian, mixed-language prose, non-English file names, or mojibake.

Risk:

- The rule is not consistently enforced.
- Local absolute paths make plans less portable.

Recommended fix:

- Replace local absolute paths in checked-in plans with repository-relative paths or a placeholder
  such as `<repo-root>`.
- Translate or remove non-English prose in active/historical plan files when those files are next
  touched.
- Add a lightweight English-only scan to docs QA if this rule is meant to be enforced continuously.

#### P2-3: Brand and terminology drift remains in top-level docs

Evidence:

- Several current top-level files still describe the project as `Portfolio MRI / Optimization
  Terminal` or `Portfolio X-Ray & Optimization Terminal / Portfolio MRI`.
- Current product truth is Portfolio MRI, diagnosis-first, current-portfolio-first.

Risk:

- New contributors may treat old optimizer-first framing as equal current identity.
- This is less severe because many hits are explicitly historical or compatibility language.

Recommended fix:

- Keep legacy names only where explicitly historical.
- Update live top-level governance docs to lead with Portfolio MRI and mention old names only as
  legacy aliases if needed.

#### P2-4: Very large source modules raise change-risk

Evidence:

- Several backend files exceed 2000-5000 lines.
- Several frontend state/UI files exceed 1000 lines.

Risk:

- Small changes require broad context.
- Reviews are harder and hidden coupling is more likely.
- Refactors are risky until tests/governance gates are stable.

Recommended fix:

- Do not start broad refactors before P0/P1 gates are green.
- When a large module is touched, extract only the directly owned helper or adapter with focused
  tests.
- Prioritize `src/api/reviews.py`, `frontend/lib/reviewState.tsx`, and
  `frontend/lib/server/fastapiBridge.ts` only after route/state contracts are stable.

### P3 / Cleanup and Operational Hygiene

#### P3-1: Local working tree is polluted with ignored logs, PID files, and build-info files

Evidence:

- Recursive scan found hundreds of local `.log` files and dozens of `.pid` files outside `.git`,
  `.venv`, and `node_modules`.
- These are ignored and not tracked, but they make local inspection noisy.

Risk:

- Operators can accidentally inspect stale logs or stale PID files.
- Local QA can be confused by old server evidence.

Recommended fix:

- Add a safe cleanup script for ignored local server logs and PID files.
- Keep the script conservative and avoid deleting generated evidence folders unless explicitly
  requested.

#### P3-2: CLI dry-run language still uses mixed old/current terminology

Evidence:

- `run_portfolio_review.py --dry-run` prints `Input -> X-Ray -> Stress -> Client Fit -> ...` while
  product-facing docs now emphasize `Portfolio Diagnosis`.
- The same dry-run prints the full product flow but only executes `Stages: input -> diagnosis` for
  the default diagnosis-only path.

Risk:

- Not a runtime failure, but it can confuse operators about what actually runs by default.

Recommended fix:

- Adjust CLI dry-run copy to distinguish `product flow` from `planned execution stages`.
- Consider replacing user-facing `X-Ray` labels with `Portfolio Diagnosis` unless the label is
  intentionally internal.

## Things That Look Healthy

- Root git state was clean before audit edits.
- No tracked `.env` files or credential files were found.
- Secret-like search found documented environment variable names and test dummy values, not obvious
  checked-in production secrets.
- Frontend build, typecheck, API route tests, smoke route test, and copy/IA tests passed.
- Focused backend/API tests passed.
- Documentation link verification passed.
- Python source/scripts compiled successfully.
- `run_portfolio_review.py --dry-run` successfully described the default diagnosis-only plan.

## Recommended Remediation Plan

### Phase 1: Make gates trustworthy

1. Fix or narrowly allowlist the failing FastAPI contract governance scan.
2. Replace interactive `npm run lint` with a non-interactive lint gate or remove it from expected
   checks.
3. Refresh full pytest status in a dedicated QA run and update `KNOWN_ISSUES.md`.

Acceptance:

- `scripts\verify_fastapi_contract_governance.py` passes.
- `npm.cmd run lint` either passes non-interactively or the documented frontend gate no longer
  points to it.
- `KNOWN_ISSUES.md` has a current full-suite baseline or clearly says the baseline could not be
  refreshed.

### Phase 2: Separate source from generated artifacts

1. Classify tracked portfolio output folders.
2. Keep only intentional fixtures.
3. Move fixture artifacts to explicit fixture/evidence locations.
4. Remove or stop tracking stale generated output folders after dependency checks.
5. Expand generated-output ignore patterns.

Acceptance:

- `git ls-files` no longer shows ordinary generated portfolio output folders as source.
- Tests that need fixtures use explicit fixture paths.
- `OUTPUTS.md` and `TESTING.md` describe any retained generated evidence.

### Phase 3: Clean language and route drift

1. Fix `frontend/lib/displayLabels.ts` mojibake regexes and add coverage.
2. Normalize route docs for `/workspace`, `/onboarding/goals`, and `/client-profile`.
3. Remove or translate non-English prose and local absolute paths from checked-in docs when touched.
4. Normalize live top-level branding away from old `Optimization Terminal` wording unless explicitly
   historical.

Acceptance:

- No mojibake remains in active frontend source.
- Route chain docs match actual route inventory and explain compatibility routes.
- English-only scan has no active-source violations outside intentionally historical examples.

### Phase 4: Targeted refactoring only after gates are stable

1. Extract adapters/helpers from large modules only when there is an active feature or bug fix.
2. Avoid broad rewrites of `src/stress_factors.py`, `src/portfolio_xray.py`,
   `src/api/reviews.py`, `frontend/lib/reviewState.tsx`, or `frontend/lib/server/fastapiBridge.ts`
   without an ExecPlan.
3. Add focused regression tests before moving logic.

Acceptance:

- No large refactor proceeds without a checked-in ExecPlan and focused tests.
- Each extraction reduces module size or coupling without changing product behavior.

## Unverified Areas

- No live networked market-data run was performed.
- No Browser/Playwright visual QA was performed because this audit did not change UI source.
- No generated output refresh was performed.
- Full pytest did not complete during this audit window.
- Security review was limited to repository secret-surface checks and auth/config source inspection
  by search; no penetration test or dependency vulnerability scan was performed.

## Bottom Line

The project has a solid current product direction and many useful focused tests. The biggest risk is
that the repository still carries too much historical/output weight while some of the very gates
meant to prevent drift are currently red or non-interactive. Clean the gates first, then clean
tracked generated artifacts, then normalize docs/routes/language, and only then attempt deeper
module refactors.
