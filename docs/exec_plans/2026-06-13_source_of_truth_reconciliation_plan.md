# Source-of-Truth Reconciliation Plan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows `PLANS.md` from the repository root. It is self-contained for the current source-of-truth reconciliation work.

## Purpose / Big Picture

Portfolio MRI / Portfolio X-Ray has working backend, frontend, and documentation contracts, but the highest-visibility root documents no longer described the same current product. After this plan, a new agent starting from `AGENTS.md`, `README.md`, `SPEC.md`, and the contract docs receives one consistent picture: the product is diagnosis-first, current-portfolio-first, Client Fit is active and non-binding, routine review is diagnosis-only, the vertical demo uses the Blocks 5-9 vertical script, and old optimizer/report artifacts remain support infrastructure rather than the primary product story.

The work was split into three sessions. Session 1 reset root source-of-truth documents and removed obsolete root historical files. Sessions 2 and 3 aligned detailed contracts, runtime labels, tests, manifest/product-bundle discovery, and final verification.

## Progress

- [x] (2026-06-13) Session 0 audit created: `docs/audits/2026-06-13_current_state_source_of_truth_alignment_audit.md`.
- [x] (2026-06-13) Plan created and registered as the active source-of-truth reconciliation plan.
- [x] (2026-06-13) Session 1 scoped to root truth reset, `AGENTS.md`, active root docs, removed root historical files, and reference cleanup.
- [x] (2026-06-13) Session 1 verification completed with `scripts/verify_docs.py`, `run_portfolio_review.py --dry-run`, stale product-brand scan, and removed-file reference scan.
- [x] (2026-06-13) Session 2 contract/runtime/test alignment completed: runtime banners now include Client Fit, Builder setup, and the explicit factory-id compatibility warning; contracts/runbooks/specs now route to the vertical demo for canonical one-candidate proof.
- [x] (2026-06-13) Session 3 product-bundle/manifest/final acceptance completed: `product_discovery` includes Client Fit and Candidate Generation, diagnosis-only hygiene removes stale downstream files, docs/registers/changelog/decisions were synchronized, and final focused/backend/frontend checks passed.

## Surprises & Discoveries

- Observation: The old root historical files were tracked source files and therefore needed explicit deletion rather than being treated as generated output.
  Evidence: `git ls-files` listed the obsolete root planning and dirty-tree files before Session 1.
- Observation: The current frontend route and contract docs already treat Client Fit as active, while several root files still treated it as future or advanced.
  Evidence: the Session 0 audit and current contract docs identify `/client-fit` as a current journey route and `/client-profile` as advanced/manual.
- Observation: Session 1 dry-run confirmed diagnosis-only default behavior, but the human-readable banner still used older flow wording.
  Evidence: `run_portfolio_review.py --dry-run` returned `Runtime mode: product_diagnosis_only`; runtime label cleanup was completed in Session 2.
- Observation: Analysis-subject `site_api` manifests explicitly stripped Launchpad and Builder paths even though they are now screen-critical diagnosis artifacts.
  Evidence: `run_report.py` blocked `candidate_launchpad_json` and `portfolio_alternatives_builder_json`; Session 3 changed the blocklist to suppress post-candidate root artifacts instead.
- Observation: The product-bundle implementation still had older six-file assumptions while current product flow requires Client Fit and Candidate Generation discovery.
  Evidence: `src/product_bundle_paths.py` docstring and tests omitted `client_fit_check_json` and `candidate_generation_json` from the required bundle chain.
- Observation: Diagnosis-only hygiene removed stale compare/verdict tombstones but did not remove stale root `candidate_generation.json`, root AI context, or site explanation files.
  Evidence: `src/product_bundle_hygiene.py` lacked those filenames before Session 3; focused hygiene tests now cover removal.
- Observation: The latest recorded full-suite status was newer and worse than the stale six-failure note in `TESTING.md` / `KNOWN_ISSUES.md`.
  Evidence: `docs/audits/2026-06-12_full_pytest_failure_audit_after_client_fit.md` records `13 failed, 1898 passed, 3 skipped`.

## Decision Log

- Decision: Remove the old root migration, dirty-tree, and documentation-alignment files instead of archiving them under a new path.
  Rationale: The user explicitly requested full deletion, and their root placement made them look like current instructions.
  Date/Author: 2026-06-13 / Codex.
- Decision: Remove the `Diagnosis 2` product-truth brand from active source-of-truth docs and describe the product directly.
  Rationale: The user explicitly requested that active docs not frame the current product as being tied to that label.
  Date/Author: 2026-06-13 / Codex.
- Decision: Do not clean generated PDFs, report sidecars, or tracked generated artifacts in this plan.
  Rationale: The user selected generated cleanup as a follow-up so source-of-truth reconciliation stays focused.
  Date/Author: 2026-06-13 / Codex.
- Decision: Treat `output_manifest.json -> product_discovery` as a discovery index, not as a trust bypass.
  Rationale: UI/API consumers need one screen-critical artifact index, but stale root files and compatibility paths still require same-run and same-candidate lineage checks.
  Date/Author: 2026-06-13 / Codex. Recorded as `DEC-2026-06-13-002`.
- Decision: Require `candidate_generation.json` for `product_bundle_complete` in the canonical product bundle, while allowing the backend factory-id compatibility path to remain partial if it bypasses visible Block 6/7 proof.
  Rationale: The current user journey includes explicit Candidate Generation; the compatibility path remains useful but is not the canonical vertical demo.
  Date/Author: 2026-06-13 / Codex.
- Decision: Diagnosis-only hygiene should remove stale downstream root files that are not valid diagnosis evidence.
  Rationale: A default diagnosis review must not make prior candidate generation, AI context, or site-copy files look current.
  Date/Author: 2026-06-13 / Codex.

## Outcomes & Retrospective

The plan is complete as of 2026-06-13.

Session 1 reset root docs and `AGENTS.md`, deleted obsolete root historical files, neutralized references to those deleted files, and passed documentation/dry-run verification.

Session 2 aligned runtime labels and detailed runtime documentation. The default dry-run banner now says `Input -> X-Ray -> Stress -> Client Fit -> Problem Classification -> Candidate Launchpad -> Portfolio Alternatives Builder -> diagnosis grounding`. The `--candidates <id>` banner now labels the path as explicit factory-id compatibility and says Builder/Candidate Generation proof is bypassed.

Session 3 aligned product-bundle discovery and final acceptance. Manifest discovery now includes `client_fit_check_json`, `candidate_generation_json`, phase `candidate_generated`, and a stricter `complete` rule. Analysis-subject manifests expose current diagnosis/Builder artifacts but suppress post-candidate root artifacts. Diagnosis-only hygiene removes stale candidate generation and grounding/site-copy root files. Current docs, runbooks, test policy, issue status, decisions, changelog, and registers now reflect the current product boundary.

Full repository pytest was not rerun in this session because the current recorded full-suite audit from 2026-06-12 already documents known broad failures (`13 failed, 1898 passed, 3 skipped`) unrelated to this focused reconciliation. Focused backend/runtime/product-bundle tests and frontend typecheck/API/smoke/build checks passed.

## Context and Orientation

`AGENTS.md` is the repository entry instruction for coding agents. It should be compact and route agents to current source-of-truth files rather than trying to duplicate every spec. `SPEC.md` is the implementation entry point. `OUTPUTS.md` owns generated-output interpretation. `WORKFLOW.md` owns the working process. `docs/contracts/PRODUCT_FLOW_CONTRACT.md`, `docs/contracts/SCREEN_CONTRACTS.md`, and `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md` own current cross-cutting product and screen boundaries.

The current product is a diagnosis-first, current-portfolio-first investment decision-support system. The normal frontend route chain is landing, sign-in, onboarding, portfolio input, diagnosis, evidence, Client Fit, Hypothesis, Comparison, Verdict, and Report. Client Fit V1 is active, non-binding context; it is not suitability approval, trade advice, or an optimizer mandate.

Default `run_portfolio_review.py` is diagnosis-only. The canonical one-candidate vertical demo is `python scripts/run_blocks_5_to_9_vertical_flow.py --method equal_weight`. The compatibility path `python run_portfolio_review.py --candidates equal_weight` remains available when the backend factory id is already known, but it is not the canonical visible Builder-to-Block-7 proof.

## Plan of Work

Session 1 updated the root source-of-truth layer. It rewrote `AGENTS.md` as a compact agent guide, updated active root docs to use direct product wording, removed stale Client Fit and runtime language, deleted obsolete root historical files, and repaired links or references to those deleted files.

Session 2 aligned detailed contracts, runbooks, runtime labels, and regression tests without changing portfolio math.

Session 3 aligned product-bundle and manifest discovery so screen-critical artifacts are exposed consistently, then ran final backend and frontend acceptance checks.

## Concrete Steps

Run from the repository root in PowerShell. Use `.\.venv\Scripts\python.exe` when Python is needed.

Session 1 commands completed:

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    .\.venv\Scripts\python.exe run_portfolio_review.py --dry-run

Session 2-3 focused backend/runtime checks completed:

    .\.venv\Scripts\python.exe -m pytest tests\test_product_bundle_paths.py tests\test_product_bundle_integration.py tests\test_runtime_entrypoint_labels.py tests\test_product_bundle_hygiene.py tests\test_block_6_product_runtime_wiring.py tests\test_block_4_diagnosis_builder.py::test_write_block_4_diagnosis_outputs_writes_both_files tests\test_runtime_mode_regression_boundaries.py::test_product_one_candidate_compare_contract_excludes_advanced_package tests\test_runtime_mode_regression_boundaries.py::test_product_bundle_schema_versions_in_product_mode tests\test_input_layer_mvp_regression.py::test_mvp_product_bundle_one_candidate_compare_regression tests\test_one_candidate_demo_validation.py::test_session07_product_scoping_with_stale_risk_parity_folder tests\test_candidate_factory.py::test_write_outputs_preserves_product_manifest_after_then_compare -q

Result: `41 passed in 16.60s`.

Session 2-3 CLI/docs/frontend checks completed:

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    .\.venv\Scripts\python.exe run_portfolio_review.py --dry-run
    .\.venv\Scripts\python.exe run_portfolio_review.py --candidates equal_weight --dry-run
    .\.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --help
    npm.cmd run typecheck
    npm.cmd run test:api
    npm.cmd run test:smoke
    npm.cmd run build
    git diff --check

Results: docs verification OK; dry-run labels matched the current diagnosis and compatibility boundaries; vertical demo help rendered successfully; frontend typecheck/API/smoke/build passed; `git diff --check` passed with line-ending warnings only.

## Validation and Acceptance

The plan is accepted because:

- the requested Sessions 2 and 3 implementation is complete;
- runtime labels and dry-run output now distinguish default diagnosis, canonical vertical demo, and explicit factory-id compatibility;
- manifest/product-bundle discovery includes Client Fit and Candidate Generation and remains a discovery index rather than a trust bypass;
- diagnosis-only hygiene removes stale downstream root artifacts;
- owning docs and registers are synchronized;
- focused backend/runtime tests passed;
- frontend typecheck/API/smoke/build checks passed;
- documentation verification passed;
- no generated output refresh was intentionally staged;
- full pytest status is reported from the current 2026-06-12 audit rather than claimed green.

## Idempotence and Recovery

The documentation edits are idempotent. If a check fails, rerun the matching search, repair only the failing references, and rerun the same check. The deleted root files can be recovered from git history if needed, but the intended state is that they remain deleted and no active docs link to them.

The code changes are additive around discovery, labels, and hygiene. If a downstream consumer needs the older bundle semantics, first decide whether that consumer is a historical/technical path or a current product path; do not silently remove Client Fit or Candidate Generation from current product discovery.

## Artifacts and Notes

Origin audit: `docs/audits/2026-06-13_current_state_source_of_truth_alignment_audit.md`.

Session 3 decision: `DEC-2026-06-13-002`.

Expected Session 1 deleted files are the old root code-migration, dirty-tree, documentation-alignment, and documentation-migration records. They are intentionally not moved to another folder.

No generated portfolio/report output refresh was performed. Frontend build wrote ignored `.next/` output only.

## Interfaces and Dependencies

No public API schema, formula, optimizer, or frontend route was changed by this plan. Runtime console labels, manifest discovery, and stale-artifact hygiene changed to match the current product boundary. Frontend verification was run because source-of-truth docs mention the current route chain, but no frontend source files were edited.

Revision note (2026-06-13): Sessions 2 and 3 were implemented and the plan was finalized because the user explicitly requested completion of this ExecPlan.
