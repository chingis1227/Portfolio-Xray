# Refactor Documentation Structure

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows `PLANS.md` in the repository root. It is self-contained so a future contributor can continue the documentation refactor without relying on prior conversation.

## Purpose / Big Picture

The project documentation has grown in the wrong places. `AGENTS.md` should tell agents how to work in this repository, and `SPEC.md` should be the compact implementation contract and index. Both files currently contain long module-specific details that belong in focused specs. After this change, a reader should be able to open `AGENTS.md` for operating rules, `SPEC.md` for the current implementation contract, and `docs/specs/` for detailed domain rules.

This is a documentation-only refactor. It must not change Python code, formulas, scenarios, optimizer behavior, generated outputs, or tests.

## Progress

- [x] (2026-05-14 00:00 Europe/Budapest) Read `PLANS.md` and inspected current documentation structure.
- [x] (2026-05-14 00:00 Europe/Budapest) Confirmed existing detailed specs were split across root, `docs/`, and a nested legacy docs folder.
- [x] (2026-05-14 00:00 Europe/Budapest) Created the `docs/specs/` structure by moving existing equivalent spec files rather than duplicating canonical details.
- [x] (2026-05-14 00:00 Europe/Budapest) Created focused specs for detailed content that previously lived mainly in `AGENTS.md` and `SPEC.md`.
- [x] (2026-05-14 00:00 Europe/Budapest) Rewrote `AGENTS.md` as a compact agent operating guide.
- [x] (2026-05-14 00:00 Europe/Budapest) Rewrote `SPEC.md` as a compact technical entry point and implementation contract.
- [x] (2026-05-14 00:00 Europe/Budapest) Updated links in `README.md`, `ARCHITECTURE.md`, `RULES.md`, and affected docs.
- [x] (2026-05-14 00:00 Europe/Budapest) Validated Markdown links; checker reported `Markdown link check passed: 0 missing relative targets`.

## Surprises & Discoveries

- Observation: The working tree was already dirty before this refactor, including prior documentation changes, deleted `PROJECT_RULES.md`, deleted `00_ВАЖНОЕ`, generated PDFs, `config.yml`, and `__pycache__` files.
  Evidence: `git status --short` listed those files before this plan was created.
- Observation: Equivalent detailed specs already exist but not under a single folder: `docs/specs/metrics_specification.md`, `docs/specs/portfolio_construction_policy.md`, `docs/specs/data_policy_spec.md`, `docs/specs/stress_testing_spec.md`, `docs/specs/feasibility_constraints_spec.md`, `docs/specs/view_after_optimization_spec.md`, `docs/specs/etf_universe_spec.md`, and `docs/specs/stock_universe_spec.md`.
  Evidence: `rg --files docs` and root Markdown listing showed those paths.
- Observation: Plain `python` was not available in PATH for validation.
  Evidence: The first Markdown link-check attempt failed with `python : Имя "python" не распознано`; the bundled runtime at `C:\Users\ShumeikoYe\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe` succeeded.

## Decision Log

- Decision: Move existing canonical detailed specs into `docs/specs/` instead of creating duplicate spec files with the same content.
  Rationale: The user asked for a linked `docs/specs/` structure and also said to update existing equivalent files rather than create duplicates. Moving preserves information while giving the repo one clear detailed-spec home.
  Date/Author: 2026-05-14 / Codex.
- Decision: Keep `AGENTS.md` and `SPEC.md` as compact source-of-truth indexes and contracts rather than preserving module inventories in those files.
  Rationale: The requested outcome is smaller top-level docs with module-specific details moved to focused specs.
  Date/Author: 2026-05-14 / Codex.

## Outcomes & Retrospective

This section will be updated after the refactor and link validation are complete.

The documentation refactor is complete. `AGENTS.md` and `SPEC.md` are compact top-level documents. Detailed behavior now lives under `docs/specs/`, including moved canonical specs and newly added focused specs for factor diagnostics, macro regimes, scenario library, candidate portfolios, robust MV, robust scenario optimization, reporting outputs, and taxonomy. Markdown link validation passed with zero missing relative targets. No executable code was edited as part of this refactor.

## Context and Orientation

The project is a Python portfolio analytics and reporting system. Important top-level documents are `README.md`, `RULES.md`, `AGENTS.md`, `SPEC.md`, `ARCHITECTURE.md`, `PRODUCT.md`, and `BUSINESS_VISION.md`.

Before this refactor, detailed behavior is documented in several places: metric formulas in `docs/specs/metrics_specification.md`, stress behavior in `docs/specs/stress_testing_spec.md`, portfolio policy in `docs/specs/portfolio_construction_policy.md`, data handling in `docs/specs/data_policy_spec.md`, feasibility rules in `docs/specs/feasibility_constraints_spec.md`, and taxonomy specs in `docs/specs/etf_universe_spec.md` and `docs/specs/stock_universe_spec.md`. `AGENTS.md` and `SPEC.md` also contain long summaries of module-specific behavior. The goal is to move those details into `docs/specs/` and keep the top-level documents concise.

## Plan of Work

First, create `docs/specs/` and move existing equivalent detailed specs into that folder. Update internal links as needed so moved specs continue to point to each other and to root documents.

Second, add focused docs under `docs/specs/` for detailed areas that are currently summarized at length in `AGENTS.md` and `SPEC.md`: macro regime diagnostics, factor diagnostics, scenario library, candidate portfolios, robust mean-variance, robust scenario optimization, reporting outputs, and taxonomy. These docs should preserve current behavior and link to deeper canonical specs where a deeper spec already exists.

Third, rewrite `AGENTS.md` to contain only agent operating rules: project summary, main commands, source-of-truth order, core rules, verification loop, documentation sync, generated-output policy, and ExecPlan rule. Add explicit update rules for when to update `AGENTS.md`, `SPEC.md`, and `docs/specs/*.md`.

Fourth, rewrite `SPEC.md` to remain the technical entry point: current implementation scope, workflows, inputs, outputs, binding behavior rules, edge cases, product status matrix, and an index of detailed specs. Add the same update-boundary rule.

Fifth, update `README.md`, `ARCHITECTURE.md`, `RULES.md`, and affected docs to point to the new `docs/specs/` paths. Run a Markdown link check that scans `.md` files for relative Markdown links and verifies the target files exist.

## Concrete Steps

Run all commands from the repository root:

    C:\Users\ShumeikoYe\OneDrive\Рабочий стол\КУРСОР ТУЛА ДИАГНОСТИКА

Move existing specs into `docs/specs/`, add focused specs with `apply_patch`, rewrite top-level docs with `apply_patch`, then validate links.

## Validation and Acceptance

Acceptance is documentation-level:

- `AGENTS.md` is compact and contains agent operating rules only.
- `SPEC.md` is compact and contains the implementation contract and detailed-spec index only.
- Detailed module rules are available under `docs/specs/`.
- Repository Markdown links resolve.
- No executable code changes are made as part of this refactor.

The link check command should report zero missing Markdown targets.

## Idempotence and Recovery

The file moves are safe to repeat only after checking current paths. If a move has already happened, update links to the new path rather than moving again. If link validation fails, fix the broken links and rerun the checker. Do not revert unrelated dirty working-tree changes.

## Artifacts and Notes

This section will record the final link-check result and notable changed files after implementation.

Final validation transcript:

    Markdown link check passed: 0 missing relative targets

Notable documentation moves:

    legacy metrics spec -> docs/specs/metrics_specification.md
    legacy portfolio policy spec -> docs/specs/portfolio_construction_policy.md
    legacy data policy spec -> docs/specs/data_policy_spec.md
    legacy stress testing spec -> docs/specs/stress_testing_spec.md
    legacy feasibility constraints spec -> docs/specs/feasibility_constraints_spec.md
    legacy view-after-optimization spec -> docs/specs/view_after_optimization_spec.md
    legacy production workflow spec -> docs/specs/production_workflow.md
    legacy ETF universe spec -> docs/specs/etf_universe_spec.md
    legacy stock universe spec -> docs/specs/stock_universe_spec.md

Revision note: Updated after implementation to reflect completed moves, compact top-level docs, link validation, and the final outcome.

## Interfaces and Dependencies

No Python API, CLI interface, formulas, configs, or runtime behavior should change. The only dependency for validation is a local Markdown link checker script run from the shell.
