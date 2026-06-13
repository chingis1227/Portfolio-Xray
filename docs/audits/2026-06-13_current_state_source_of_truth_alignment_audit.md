# Current State Source-of-Truth Alignment Audit

Date: 2026-06-13
Status: Audit only; no remediation performed in this pass
Repository scope: Portfolio MRI / Portfolio X-Ray
Primary risk: active root documentation and some operational docs no longer describe the implemented product accurately enough for agents to rely on them safely.

## 1. Audit objective

The goal of this audit is to compare the current project state across code, frontend routes, design docs, root Markdown files, detailed specs, runtime entrypoints, generated-output policy, and historical planning files.

The requested outcome for this pass is an audit file only. This file intentionally does not patch product behavior, documentation, tests, generated outputs, routes, or runtime code.

## 2. Executive verdict

The project has a newer and more coherent current product implementation than several high-visibility root documents describe. The most reliable current truth is now spread across the newer contract/design/frontend docs and the implemented FastAPI/Next.js flow, while several root documents still preserve older pre-Client-Fit or optimizer-era descriptions.

The highest-risk mismatch is that agents reading only root files can conclude that Client Fit is future/backlog/advanced, that the official product demo is `run_portfolio_review.py --candidates equal_weight`, or that routine `run_portfolio_review.py` still runs a multi-candidate `core_fast` package. Those claims are not aligned with the current implementation and newer contracts.

Current implementation truth observed in this audit:

```text
Public landing
-> required email sign-in
-> lightweight onboarding
-> portfolio input
-> portfolio X-Ray / diagnosis
-> evidence / Stress Lab
-> Client Fit
-> Hypothesis route containing Problem Classification, Launchpad, Builder setup, and candidate generation status
-> Current vs Candidate Comparison
-> Decision Verdict
-> Report Preview
```

Current backend/runtime truth observed in this audit:

- FastAPI review creation runs a diagnosis-first review through `scripts/run_review_from_payload.py` and `run_portfolio_review.py --skip-candidates --output-profile site_api`.
- Default `run_portfolio_review.py` is diagnosis-only.
- Explicit candidate execution is opt-in.
- The current one-candidate vertical demo is documented most consistently as `python scripts/run_blocks_5_to_9_vertical_flow.py --method equal_weight`.
- `run_portfolio_review.py --candidates equal_weight` still exists as a compatibility path, but should not be the primary current demo path unless the project intentionally reverses that decision.

## 3. Work performed

This audit inspected repository files and ran non-destructive checks only.

Commands and checks used:

- `git status --short`
- Root Markdown inventory
- Recursive docs inventory
- Frontend route inventory under `frontend/app`
- API route inspection under `src/api/`
- Runtime entrypoint inspection for `run_portfolio_review.py`, `run_core_diagnostics.py`, `scripts/run_review_from_payload.py`, and `scripts/run_blocks_5_to_9_vertical_flow.py`
- Documentation searches for Client Fit, canonical flow, core_fast, product bundle, generated outputs, and demo commands
- `.venv\Scripts\python.exe run_portfolio_review.py --dry-run`
- `.venv\Scripts\python.exe run_portfolio_review.py --candidates equal_weight --dry-run`
- `.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --help`
- `.venv\Scripts\python.exe scripts\verify_docs.py`
- Inspection of the latest available frontend review run artifacts as evidence, without treating generated output as source

Checks not run in this audit:

- Full pytest suite
- Frontend typecheck
- Frontend smoke tests
- Browser or Playwright visual QA
- Live FastAPI/Next.js click-through
- Non-dry-run regeneration of outputs

## 4. Current reliable source-of-truth map

This is the practical source-of-truth hierarchy that appears closest to the current implementation.

| Area | Most reliable current source | Notes |
| --- | --- | --- |
| Cross-product flow | `docs/contracts/PRODUCT_FLOW_CONTRACT.md` | Best current cross-step contract. It includes Client Fit and Candidate Generation. |
| Screen flow | `docs/contracts/SCREEN_CONTRACTS.md`, `docs/specs/frontend_screen_contracts.md` | Matches implemented route chain and keeps `/client-profile` advanced/manual. |
| Frontend implementation | `frontend/app/**`, `frontend/README.md` | Matches required sign-in/onboarding and Client Fit before Hypothesis. |
| Design system | `docs/design/current_website_structure.md`, `docs/design/portfolio_mri_design_system.md`, `DESIGN.md` | The design docs are newer and generally aligned with current frontend structure. |
| Runtime commands | `docs/runtime_entrypoints.md`, `docs/specs/portfolio_review_workflow_spec.md`, `OUTPUTS.md` | Mostly aligned with current default diagnosis-only behavior and vertical demo script. |
| API bridge | `src/api/app.py`, `src/api/reviews.py`, `scripts/run_review_from_payload.py` | FastAPI creates run-local diagnosis artifacts and proxies explicit downstream steps. |
| Detailed formulas and implementation contract | `SPEC.md`, detailed files under `docs/specs/` | Strong authority, but several local status/path statements need patching. |
| Generated-output boundaries | `OUTPUTS.md`, `.gitignore` | Mostly clear, but old tracked generated artifacts still exist. |
| Historical plans and audits | `docs/audits/`, `docs/exec_plans/`, root migration files | Useful as history only unless explicitly marked active. Several register/status files need cleanup. |

## 5. Current implementation snapshot

### 5.1 Frontend routes

Observed route structure under `frontend/app`:

```text
/
/onboarding/sign-in
/onboarding/name
/onboarding/investor-type
/onboarding/loading
/portfolio-input
/diagnosis
/evidence
/client-fit
/hypothesis
/comparison
/verdict
/report
/client-profile
```

Interpretation:

- `/client-fit` is part of the current main journey after Stress Lab/evidence and before Hypothesis.
- `/client-profile` exists, but current screen contracts and frontend docs classify it as an advanced/manual editor, not the primary onboarding step.
- There is no separate current route for `/candidate`, `/monitoring`, `/what-changed`, optimizer arena, action plan, decision journal, macro dashboard, or PDF-product route.

### 5.2 FastAPI bridge

Observed API bridge behavior:

- `POST /api/v1/reviews` creates or reuses a review.
- The review bridge calls `scripts/run_review_from_payload.py`.
- The payload runner maps web reviews into `run_portfolio_review.py --skip-candidates --output-profile site_api` for the diagnosis-first path.
- Downstream endpoints generate Builder, Candidate, Comparison, Verdict, and Report artifacts explicitly.

### 5.3 CLI/runtime behavior

Dry-run evidence:

- `run_portfolio_review.py --dry-run` reports diagnosis-only execution and candidate execution disabled.
- `run_portfolio_review.py --candidates equal_weight --dry-run` reports explicit one-candidate compatibility execution and warns that the canonical Blocks 5-9 demo uses `scripts/run_blocks_5_to_9_vertical_flow.py --method <id>`.
- `scripts/run_blocks_5_to_9_vertical_flow.py --help` confirms the current vertical flow script and default method.

### 5.4 Artifact chain evidence

A recent run-local frontend review folder contained these relevant files:

```text
analysis_subject/client_fit_check.json
analysis_subject/problem_classification.json
analysis_subject/candidate_launchpad.json
analysis_subject/portfolio_alternatives_builder.json
candidate_comparison.json
current_vs_candidate.json
decision_verdict.json
```

The diagnosis-only root candidate/comparison/verdict files were safe tombstones rather than authoritative candidate evidence. This is useful compatibility behavior, but the manifest and product-bundle docs do not yet describe that state consistently.

## 6. Major findings

### F01 - Root product flow is inconsistent across the highest-visibility files

Severity: Critical

Files affected:

- `AGENTS.md`
- `README.md`
- `PRODUCT.md`
- `ARCHITECTURE.md`
- `BUSINESS_VISION.md`
- `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`
- `SPEC.md`

Evidence:

- Some root flows omit Client Fit entirely.
- Some root files still classify Client Fit Check as advanced, later, or future-only.
- `AGENTS.md` includes Client Fit but omits Candidate Generation in its canonical flow.
- `SPEC.md` has the strongest current flow, but still has local stale wording around `/client-profile` as a primary frontend step.

Risk:

Agents can start from different root files and build different products. The most damaging path is treating Client Fit as backlog even though current frontend and API flows already depend on it.

Recommended remediation:

Patch all root current-product summaries in one coordinated documentation pass. Use `docs/contracts/PRODUCT_FLOW_CONTRACT.md` as the cross-product flow source, then mirror a compact version into `AGENTS.md`, `README.md`, `PRODUCT.md`, `ARCHITECTURE.md`, and `BUSINESS_VISION.md`.

### F02 - Client Fit status is split between current implementation and stale specs

Severity: Critical

Files affected:

- `README.md`
- `PRODUCT.md`
- `ARCHITECTURE.md`
- `BUSINESS_VISION.md`
- `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`
- `docs/specs/client_fit_check_spec.md`
- `SPEC.md`
- `docs/runtime_artifact_contract.md`

Evidence:

- Current frontend route chain includes `/client-fit`.
- Current contracts describe Client Fit as active and after Stress Lab.
- Root files and the Client Fit spec still contain wording that says Client Fit is future, advanced, or not yet wired.
- `SPEC.md` and `docs/runtime_artifact_contract.md` contain stale path wording that places `/client-profile` before Portfolio Input as if it were the primary journey.

Risk:

Future work may bypass or duplicate Client Fit, place it in the wrong route, or make it binding suitability logic instead of non-binding diagnostic context.

Recommended remediation:

Replace future-only Client Fit language with the current V1 status: non-binding profile-fit context, required frontend onboarding, `/client-fit` after Stress Lab before Hypothesis, `/client-profile` advanced/manual editor, backend compatibility state `not_provided` for missing context.

### F03 - Official demo path is inconsistent

Severity: High

Files affected:

- `AGENTS.md`
- `WORKFLOW.md`
- `docs/operational_runbook.md`
- `docs/runtime_entrypoints.md`
- `docs/product_flow_operator_guide.md`
- `OUTPUTS.md`

Evidence:

- Newer runtime docs identify `scripts/run_blocks_5_to_9_vertical_flow.py --method equal_weight` as the official one-candidate vertical demo.
- `run_portfolio_review.py --candidates equal_weight --dry-run` explicitly warns that this is a compatibility path and points to the vertical script.
- `AGENTS.md` and parts of `docs/operational_runbook.md` still present `run_portfolio_review.py --candidates equal_weight` as the preferred or official demo path.

Risk:

Agents may run the compatibility path and then make screen/artifact conclusions that do not reflect the current frontend vertical flow.

Recommended remediation:

Declare one official demo path. Based on current contracts and code warnings, it should be:

```bash
python scripts/run_blocks_5_to_9_vertical_flow.py --method equal_weight
```

Then describe `run_portfolio_review.py --candidates equal_weight` as a compatibility path only.

### F04 - Default `run_portfolio_review.py` behavior is documented inconsistently

Severity: High

Files affected:

- `WORKFLOW.md`
- `docs/specs/portfolio_review_workflow_spec.md`
- `docs/operational_runbook.md`
- Historical ExecPlans under `docs/exec_plans/`

Evidence:

- Actual dry-run behavior: default `run_portfolio_review.py` is diagnosis-only.
- Some docs still say or imply routine core/default review runs a six-candidate `core_fast` package.
- Newer files say `--with-candidates` triggers the advanced/research batch path.

Risk:

Agents can waste time regenerating candidates unintentionally, misread missing candidate artifacts as failures, or update the wrong documentation after a diagnosis-only run.

Recommended remediation:

Normalize terminology:

- `run_portfolio_review.py`: default diagnosis-only.
- `run_portfolio_review.py --with-candidates`: advanced/research `core_fast` batch.
- `run_portfolio_review.py --mode full`: broader legacy/full candidate profile where applicable.
- `scripts/run_blocks_5_to_9_vertical_flow.py --method <id>`: current one-candidate vertical demo.

### F05 - Runtime console labels lag behind the current product flow

Severity: Medium

Files affected:

- `src/runtime_entrypoint_labels.py`

Evidence:

- `run_portfolio_review.py --dry-run` prints a flow banner that omits Client Fit and Builder and includes `AI Commentary / Monitoring` in a diagnosis-only context.
- `run_portfolio_review.py --candidates equal_weight --dry-run` prints a flow banner that omits Client Fit, Builder, and Candidate Generation.

Risk:

Even when docs are fixed, dry-run banners can reintroduce stale mental models.

Recommended remediation:

Update only labels/help text, not calculations. The labels should match the current contract and clearly distinguish diagnosis-only, compatibility one-candidate, and vertical demo flows.

### F06 - Product bundle definitions disagree on the number and identity of artifacts

Severity: High

Files affected:

- `src/product_bundle_paths.py`
- `OUTPUTS.md`
- `docs/specs/README.md`
- `docs/product_flow_operator_guide.md`
- `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md`
- `docs/runtime_artifact_contract.md`

Evidence:

- Some docs describe a six-file bundle.
- Other docs describe Client Fit, Builder, Candidate Generation, Comparison, Verdict, AI Commentary, and Monitoring as product stages.
- `src/product_bundle_paths.py` has an old six-file docstring while constants include a different set of bundle paths.
- Current route/screen contracts treat Client Fit as an active screen and artifact.

Risk:

Agents can inspect the wrong artifact set before making decisions about comparison or verdict validity.

Recommended remediation:

Make an explicit artifact taxonomy:

1. Required diagnosis artifacts.
2. Required Client Fit context artifact.
3. Launchpad/Builder artifacts.
4. Candidate generation artifacts.
5. Comparison/Verdict artifacts.
6. AI grounding/report artifacts.
7. Monitoring or What Changed artifacts, if present and authoritative.
8. Safe tombstones for disabled candidate paths.

Then update code docstrings, output docs, and operator read order accordingly.

### F07 - Output manifest does not list all current run-local artifacts consistently

Severity: Medium

Files affected:

- `analysis_subject/output_manifest.json` generation logic
- `OUTPUTS.md`
- `docs/runtime_artifact_contract.md`
- `docs/product_flow_operator_guide.md`

Evidence:

A recent frontend review run had `client_fit_check.json`, `candidate_launchpad.json`, and `portfolio_alternatives_builder.json` present in `analysis_subject/`, but the manifest's generated-path listing did not clearly expose all of those current screen-critical artifacts.

Risk:

Agents following the manifest can miss real current artifacts, while agents listing folders can over-trust stale or generated files.

Recommended remediation:

Decide whether the manifest is the authoritative complete artifact index. If yes, add current screen-critical artifacts. If no, document the manifest as a partial diagnostic manifest and provide a separate product-flow artifact map.

### F08 - Test-status documentation conflicts

Severity: High

Files affected:

- `CHANGELOG.md`
- `KNOWN_ISSUES.md`
- `TESTING.md`
- `docs/audits/2026-06-12_full_pytest_failure_audit_after_client_fit.md`
- `docs/audits/2026-06-12_client_fit_v1_final_acceptance_audit.md`

Evidence:

- `CHANGELOG.md` contains a claim that a full backend suite passed with `1911 passed, 3 skipped`.
- Nearby newer audit evidence records a full pytest attempt with `13 failed`.
- `KNOWN_ISSUES.md` and `TESTING.md` still reference an older 2026-05-26 failure state with 6 failures.

Risk:

Agents may claim the full suite is green, skip known failure review, or chase obsolete failures.

Recommended remediation:

Choose a current testing status policy:

- `CHANGELOG.md` should remain history, but add a later correction entry if needed.
- `KNOWN_ISSUES.md` should carry the current active failure matrix.
- `TESTING.md` should link to the current failure audit and explain expected full-suite state.
- New test results should record exact command, date, environment, and failure count.

### F09 - Root historical planning files still look active

Severity: High

Files affected:

- `removed root code-migration record`
- `removed root dirty-tree classification record`
- `removed root dirty-tree cleanup record`
- `removed root documentation-alignment audit`
- `removed root documentation-alignment patch plan`
- `removed root documentation-migration plan`
- `removed root documentation-migration session audit`

Evidence:

- `removed root code-migration record` still says several now-implemented product blocks have no verified owning module or artifact.
- Dirty-tree files describe an old dirty workspace state while the current audit started from a clean tracked tree.
- Documentation migration files are history but remain in the root alongside active source-of-truth files.

Risk:

Agents can read root historical files as current instructions and revert the product mentally to an older architecture.

Recommended remediation:

Do not delete history. Move historical files to archive/register locations or add unmistakable superseded headers at the top. Root should contain only active operating/source-of-truth files and small pointers to history.

### F10 - Audit and ExecPlan registers are incomplete or stale

Severity: Medium

Files affected:

- `docs/audits/README.md`
- `docs/exec_plans/README.md`
- Several files under `docs/audits/`
- Several files under `docs/exec_plans/`

Evidence:

- Several newer audit files are not listed in `docs/audits/README.md`.
- At least one audit file lacks the date-prefix convention used elsewhere.
- ExecPlan register entries still mark old frontend/FastAPI plans as active even though later docs and implementation show more progress.

Risk:

Agents can choose a stale active plan and ignore newer completed work.

Recommended remediation:

Update the audit register and ExecPlan register after the source-of-truth cleanup. Classify each plan as active, completed, superseded, or historical.

### F11 - Generated and legacy tracked artifacts can still pollute reasoning

Severity: Medium

Files affected:

- `pdf files/`
- `pdf_md_sources/`
- tracked `__pycache__` files under `src/`
- generated run/output folders
- `.gitignore`
- `OUTPUTS.md`

Evidence:

- Generated PDFs and Markdown sidecars are tracked even though routine current reviews do not refresh `pdf files/` by default.
- Tracked `.pyc` files remain in the repository.
- Generated folders such as `runs/`, `output/`, `Main portfolio/`, and candidate output folders exist and must not be treated as source.

Risk:

Agents may infer product capabilities from stale generated files or noisy tracked artifacts instead of source and contracts.

Recommended remediation:

Perform a separate generated-artifact cleanup plan. Do not combine it with source-of-truth text edits unless explicitly scoped.

### F12 - Design and frontend docs are more current than several root docs

Severity: Medium

Files affected:

- `DESIGN.md`
- `docs/design/current_website_structure.md`
- `docs/design/portfolio_mri_design_system.md`
- `frontend/README.md`
- `README.md`
- `ARCHITECTURE.md`
- `PRODUCT.md`
- `BUSINESS_VISION.md`

Evidence:

- Design and frontend docs describe the current landing, sign-in, onboarding, Client Fit, Hypothesis, Comparison, Verdict, and Report structure.
- Root product/business/architecture summaries still preserve an older flow that omits Client Fit or treats it as future.

Risk:

Frontend agents may follow newer design docs while backend/product agents follow stale root docs, creating cross-layer drift.

Recommended remediation:

Make `DESIGN.md` a root pointer to current design docs and ensure product root files reference the same screen contract.

## 7. Files that should be updated in a remediation pass

### Must update first

These files directly shape agent behavior and should be patched together:

- `AGENTS.md`
- `README.md`
- `PRODUCT.md`
- `ARCHITECTURE.md`
- `BUSINESS_VISION.md`
- `SPEC.md`
- `WORKFLOW.md`
- `OUTPUTS.md`
- `TESTING.md`
- `KNOWN_ISSUES.md`
- `docs/runtime_entrypoints.md`
- `docs/product_flow_operator_guide.md`
- `docs/operational_runbook.md`

### Must update for Client Fit status

- `docs/specs/client_fit_check_spec.md`
- `docs/runtime_artifact_contract.md`
- `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md`, if artifact naming or route handoff is changed
- `docs/contracts/PRODUCT_FLOW_CONTRACT.md`, only if the project chooses a different final canonical flow
- `docs/contracts/SCREEN_CONTRACTS.md`, only if the route chain changes

### Should update for artifact and manifest clarity

- `src/product_bundle_paths.py`
- `src/runtime_entrypoint_labels.py`
- Output manifest generation logic
- `docs/specs/README.md`
- `docs/contracts/FASTAPI_SCREEN_MAPPING.json`, if API/screen ownership changes

### Should archive or mark superseded

- `removed root code-migration record`
- `removed root dirty-tree classification record`
- `removed root dirty-tree cleanup record`
- `removed root documentation-alignment audit`
- `removed root documentation-alignment patch plan`
- `removed root documentation-migration plan`
- `removed root documentation-migration session audit`
- Older ExecPlans that still describe pre-current behavior as active

### Should register or reclassify

- `docs/audits/README.md`
- `docs/exec_plans/README.md`

This audit file itself is intentionally not registered in this pass because the user requested an audit file only and no broader repository edits.

## 8. Do not fix by doing these anti-patterns

- Do not update only `AGENTS.md` and leave root docs stale.
- Do not delete historical files without preserving traceability.
- Do not treat generated output as source truth.
- Do not remove implemented capabilities just because old concept docs omitted them.
- Do not make Client Fit a binding suitability approval unless a future spec explicitly changes that boundary.
- Do not make `run_portfolio_review.py` default generate candidates again unless the runtime contract is intentionally changed.
- Do not use stale PDFs, old run folders, or old dirty-tree reports as evidence of current product behavior without checking source and current contracts.

## 9. Recommended remediation sequence

### Phase 0 - Freeze the current product truth

Goal: define one compact canonical flow before editing many files.

Recommended current flow:

```text
Input Portfolio
-> Portfolio X-Ray
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

Frontend route realization:

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

Important nuance:

- Candidate Generation is a product step, but the current frontend may present it inside `/hypothesis` rather than as a separate route.
- Monitoring / What Changed may be artifact-level or future UI depending on current implementation; do not imply a full visible route unless implemented.

### Phase 1 - Patch root source-of-truth files

Patch the root docs in one coordinated branch:

1. `AGENTS.md`
2. `README.md`
3. `PRODUCT.md`
4. `ARCHITECTURE.md`
5. `BUSINESS_VISION.md`
6. `SPEC.md`
7. `WORKFLOW.md`
8. `OUTPUTS.md`
9. `TESTING.md`
10. `KNOWN_ISSUES.md`

Expected result:

- No root file classifies Client Fit V1 as future-only.
- No root file describes routine `run_portfolio_review.py` as candidate-generating by default.
- Official demo path is consistent.
- Advanced/legacy/backlog lists no longer include current Core MVP screens.

### Phase 2 - Patch detailed specs and operational docs

Patch:

- `docs/specs/client_fit_check_spec.md`
- `docs/specs/portfolio_review_workflow_spec.md`
- `docs/specs/frontend_screen_contracts.md`, only if route terms need clarification
- `docs/runtime_entrypoints.md`
- `docs/runtime_artifact_contract.md`
- `docs/product_flow_operator_guide.md`
- `docs/operational_runbook.md`
- `docs/specs/README.md`

Expected result:

- Client Fit V1 status is consistent.
- `/client-profile` is consistently advanced/manual.
- Vertical demo, compatibility demo, diagnosis-only, and candidate batch paths are distinct.
- Artifact read order includes Client Fit and Builder where relevant.

### Phase 3 - Update code-facing labels and docstrings

Patch only non-business-logic text unless a manifest decision requires code changes:

- `src/runtime_entrypoint_labels.py`
- `src/product_bundle_paths.py`
- Output manifest generation, if the project decides the manifest must list all screen-critical artifacts

Expected result:

- Dry-run banners no longer teach stale flows.
- Product bundle constants and docstrings use the same artifact terminology as docs.

### Phase 4 - Reclassify historical root files

Choose one strategy:

1. Move old root migration/dirty/alignment files into `docs/archive/` with current pointers.
2. Keep files in place but add a top warning that they are historical/superseded.
3. Convert useful parts into registered audits or ExecPlans and remove root ambiguity.

Expected result:

- A new agent can read root files and know which files are active source-of-truth and which are history.

### Phase 5 - Register and verify

Patch:

- `docs/audits/README.md`
- `docs/exec_plans/README.md`

Then run, at minimum:

```bash
python scripts/verify_docs.py
python run_portfolio_review.py --dry-run
python run_portfolio_review.py --candidates equal_weight --dry-run
python scripts/run_blocks_5_to_9_vertical_flow.py --help
```

If code labels or manifest generation changes, add narrow pytest for the touched modules. If frontend docs or route behavior changes, run frontend typecheck/smoke and a browser walkthrough using a fresh localhost target.

## 10. Open decisions before remediation

1. Is Client Fit part of the product bundle, or a required context artifact outside the product bundle?
2. Should `candidate_generation.json` be listed as a canonical product artifact when the current candidate generation step is route-owned by `/hypothesis`?
3. Should the official one-candidate demo be only `scripts/run_blocks_5_to_9_vertical_flow.py --method equal_weight`, with `run_portfolio_review.py --candidates equal_weight` compatibility-only?
4. Should diagnosis-only tombstone files at the run root be part of the output contract, or only compatibility cleanup artifacts?
5. Should old generated PDFs and tracked `.pyc` files be removed from tracking in a separate cleanup PR?
6. Should `CHANGELOG.md` receive corrective entries for later test status, or should it remain purely historical with current status moved to `KNOWN_ISSUES.md` and test audits?

## 11. Verification result for this audit file

Verification performed during this audit:

- Documentation verification script completed successfully: `docs verification: OK`.
- Runtime dry-run confirmed diagnosis-only default review behavior.
- Runtime dry-run confirmed explicit one-candidate compatibility path and its warning to use the vertical script for the canonical Blocks 5-9 demo.
- Vertical flow script help was available and confirmed the expected CLI surface.
- Initial tracked working tree was clean before this audit file was created.

Verification not performed:

- No full pytest run.
- No frontend typecheck.
- No frontend smoke test.
- No Playwright/browser QA.
- No non-dry-run output regeneration.

## 12. Bottom line

The project does not need a random documentation rewrite. It needs a controlled source-of-truth reconciliation.

The safest next action is to make `docs/contracts/PRODUCT_FLOW_CONTRACT.md` the explicit cross-product flow source, patch the root docs to match it, fix Client Fit status everywhere, separate diagnosis-only from candidate demo/runtime paths, and then update the artifact/manifest language so the frontend, backend, CLI, and generated-output docs all describe the same product.
