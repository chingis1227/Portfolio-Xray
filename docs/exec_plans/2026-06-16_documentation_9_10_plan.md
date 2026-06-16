# Documentation 9/10 Maintenance Plan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows `PLANS.md` from the repository root. It is documentation-only: it must not change
runtime code, formulas, schemas, API behavior, frontend routes, backend behavior, or generated
outputs.

## Purpose / Big Picture

Portfolio MRI already has strong source-of-truth discipline, but the top-level documentation has
become expensive to maintain because several documents repeat the same product story, command
taxonomy, and current-versus-legacy warnings. After this plan, a new reader should understand the
product from `README.md` in a few minutes, then know which single owning document to open for each
deeper topic. The observable result is a smaller product-facing README, clearer ownership rules in
workflow/governance docs, shorter product direction, and explicit historical-document boundaries.

## Progress

- [x] (2026-06-16) Read `PLANS.md`, `WORKFLOW.md`, `docs/contracts/DOC_SYNC_CONTRACT.md`, and the
  current top-level documentation shape.
- [x] (2026-06-16) Replace the oversized `README.md` with a concise product-facing entry point.
- [x] (2026-06-16) Create and register this ExecPlan as the active documentation plan.
- [x] (2026-06-16) Clarify the owning-doc-first rule in workflow and documentation synchronization
  guidance.
- [x] (2026-06-16) Shorten and align the most duplicated top-level documentation without changing product or
  implementation behavior.
- [x] (2026-06-16) Add or strengthen historical-document entry-point warnings.
- [x] (2026-06-16) Run documentation checks and record final evidence.

## Surprises & Discoveries

- Observation: Before this plan, `README.md` had become a mini-spec rather than a short product
  entry point.
  Evidence: `git diff --stat` after the README rewrite showed 458 deleted lines and 62 inserted
  lines in `README.md`.
- Observation: The repository already had strong historical warnings in `docs/audits/README.md` and
  `docs/exec_plans/README.md`; the main gap is making the current active pointer and archive entry
  clearer.
  Evidence: `rg -n "Historical|historical" docs/exec_plans/README.md docs/audits/README.md` found
  existing historical status language.
- Observation: `PRODUCT.md` was the best candidate for medium-depth shortening because no active
  Markdown links targeted its old section anchors.
  Evidence: `rg -n "PRODUCT\\.md#|SPEC\\.md#|OUTPUTS\\.md#|TESTING\\.md#" -g '*.md'` found only
  `OUTPUTS.md` anchors, not `PRODUCT.md` anchors.
- Observation: The first Cyrillic scan found the scan pattern itself inside this plan.
  Evidence: the scan matched the ExecPlan line that contained a literal Cyrillic character class.
  The command was replaced with an ASCII-only Python Unicode-range scan.

## Decision Log

- Decision: Use a medium-depth documentation cleanup instead of a full rewrite of every Markdown
  file.
  Rationale: The user wants a 9/10 documentation system that remains useful and maintainable, not a
  large documentation project that creates dead weight. The repository has hundreds of Markdown
  files, so a focused top-level cleanup gives the best risk/reward.
  Date/Author: 2026-06-16 / Codex.
- Decision: Keep `README.md` short and product-facing.
  Rationale: README is the first document a non-specialist or new contributor reads. It should
  explain what the product does and route to owning docs, not duplicate formulas, schemas, long
  command matrices, or implementation details.
  Date/Author: 2026-06-16 / Codex.
- Decision: Do not change runtime code, commands, APIs, schemas, or generated artifacts in this
  plan.
  Rationale: The requested improvement is documentation governance and readability. Any runtime
  change would increase risk and require unrelated verification.
  Date/Author: 2026-06-16 / Codex.
- Decision: Rewrite `PRODUCT.md` into a compact product-owner document instead of trying to trim it
  paragraph by paragraph.
  Rationale: Its role is product direction, not implementation detail. A concise replacement reduces
  duplicate README/SPEC/contract language while preserving the current Core MVP boundaries and links
  to owning technical documents.
  Date/Author: 2026-06-16 / Codex.

## Outcomes & Retrospective

Completed for the requested medium-depth cleanup. The README and PRODUCT documents now serve
distinct roles: README is a short product entry point, and PRODUCT owns product direction and
boundaries. Workflow and doc-sync guidance now state the owning-doc-first rule explicitly. The
ExecPlan register points to this plan as active, archive documentation now has a clear traceability
warning, and the key top-level technical docs were aligned without changing runtime behavior.

Verification evidence:

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    docs verification: OK

    git diff --check
    no whitespace errors; Git printed line-ending normalization warnings only

    ASCII-only Cyrillic scan over changed docs
    Cyrillic scan: OK

## Context and Orientation

This repository is Portfolio MRI, a diagnosis-first investment decision-support product. The product
starts from the user's current portfolio, diagnoses the portfolio, tests stress behavior, uses
Client Fit as non-binding context, optionally tests one candidate hypothesis, and produces a
non-binding Decision Verdict. The repository also contains older optimizer-first, report-heavy, and
scorecard-heavy infrastructure. Those older capabilities may remain useful as support, advanced, or
legacy code, but they must not be presented as the current Core MVP product flow unless current
specs and code explicitly promote them.

The important documentation roles are:

- `README.md` is the short product-facing entry point.
- `PRODUCT.md` owns product direction, user goals, Core MVP boundaries, advanced/legacy boundaries,
  and product non-goals.
- `SPEC.md` owns the current implementation contract and points to detailed specs.
- `OUTPUTS.md` owns generated-output folders, artifacts, output profiles, and generated-vs-source
  policy.
- `TESTING.md` owns verification strategy and check selection.
- `WORKFLOW.md` owns the working process for future agents.
- `docs/contracts/DOC_SYNC_CONTRACT.md` owns documentation update routing.
- `docs/exec_plans/README.md`, `docs/audits/README.md`, and `docs/archive/README.md` are entry
  points for historical project memory.

An "owning doc" is the single document that is responsible for the current truth of a topic. Other
documents may link to it or summarize it, but they should not copy long details from it. "Generated
outputs" are files created by running the product, such as output folders, PDFs, reports, caches,
and run-local artifacts. They are evidence from a run, not source-of-truth documentation.

## Plan of Work

First, register this plan in `docs/exec_plans/README.md` as the active documentation plan while
preserving the previous `Exhaustive QA System` pointer as paused release-readiness context. Second,
clarify the owning-doc-first rule in `WORKFLOW.md` and
`docs/contracts/DOC_SYNC_CONTRACT.md`: update the narrowest owning document first, and update
README only when product understanding, common commands, setup, or top-level orientation changes.
Third, keep `README.md` compact and shorten or align top-level docs where they duplicate README or
contract language. Fourth, add an archive entry point if needed and strengthen historical warnings
without rewriting historical files. Finally, run documentation checks and record the evidence in
this plan.

## Concrete Steps

Work from the repository root. In this desktop session, use the current working directory rather
than copying any machine-specific absolute path into repository documentation.

Edit only Markdown source files. Do not run code generators, portfolio review commands, frontend
builds, backend tests, or generated-output refreshes for this plan.

After edits, run:

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    git diff --check
    .\.venv\Scripts\python.exe -c "from pathlib import Path; files=['README.md','PRODUCT.md','SPEC.md','OUTPUTS.md','TESTING.md','WORKFLOW.md','docs/contracts/DOC_SYNC_CONTRACT.md','docs/exec_plans/2026-06-16_documentation_9_10_plan.md']; bad=[(f,i,l) for f in files for i,l in enumerate(Path(f).read_text(encoding='utf-8').splitlines(),1) if any(0x0400 <= ord(ch) <= 0x04FF for ch in l)]; print(bad); raise SystemExit(1 if bad else 0)"
    git status --short

The Cyrillic scan may print the working directory only if a command error occurs; the expected
result for repository files is no matches.

## Validation and Acceptance

Acceptance is documentation-only. A reader should be able to open `README.md`, understand what
Portfolio MRI does, what it does not promise, and where to go next. A contributor should be able to
open `WORKFLOW.md` or `docs/contracts/DOC_SYNC_CONTRACT.md` and know that they should update the
owning doc first, not every broad document. Historical docs must be clearly labeled as traceability
only and must not override current specs.

Required validation:

- `scripts/verify_docs.py` reports `docs verification: OK`.
- `git diff --check` reports no whitespace errors.
- The Cyrillic scan reports no matches in the changed repository docs.
- `git status --short` shows only intentional documentation changes.

Runtime pytest, frontend build, browser QA, backend API tests, and portfolio review commands are not
required because this plan does not change executable behavior.

## Idempotence and Recovery

The changes are safe to repeat because they are Markdown edits only. If a documentation edit is too
aggressive, restore the previous section from `git diff` and replace it with a shorter routing note
instead of trying to preserve every duplicated detail. If link verification fails, fix the broken
link or restore the original heading/link target. Do not edit generated folders to make docs checks
pass.

## Artifacts and Notes

Important evidence to record at closure:

    docs verification: OK
    git diff --check: no output
    Cyrillic scan: no matches in changed docs
    git status --short: intentional Markdown changes only

## Interfaces and Dependencies

There are no runtime interfaces or dependencies. The only interface changed by this plan is the
documentation navigation contract: future contributors should use `README.md` for orientation and
the owning source-of-truth documents for details. No Python modules, TypeScript types, FastAPI
endpoints, CLI flags, JSON artifacts, or generated files are introduced or changed.
