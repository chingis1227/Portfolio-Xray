# Block 6 Portfolio Alternatives Builder

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained according to `PLANS.md` in the repository root. It is self-contained: a future agent should be able to implement Block 6 from this file without relying on chat history.

## Purpose / Big Picture

Portfolio MRI is a diagnosis-first, current-portfolio-first system. Blocks 1 through 5 diagnose the current portfolio and produce Candidate Launchpad cards that describe what to test next. Block 6 must turn one selected Launchpad card into an editable, validated Builder setup. It must not create a candidate portfolio.

After this work, a user or UI can select a Launchpad card, see a pre-filled Portfolio Alternatives Builder form, edit simple setup fields, validate the setup, and hand a clean `CandidateSetup` object to Block 7. Block 6 prepares validated candidate setup; actual candidate generation belongs to Block 7 after an explicit Generate candidate action.

The observable outcome is a new product-bundle artifact named `portfolio_alternatives_builder.json`. For a valid targeted or reference card it reports `status: ok`, `can_generate_candidate: true`, and contains separate `builder_prefill` and `candidate_setup` objects. For a data-quality card it may be written, but it must report `status: blocked`, `can_generate_candidate: false`, `reason: data_quality_blocker`, and must not expose a ready CandidateSetup.

## Progress

- [x] (2026-06-05) Session 00 baseline audit completed. Current code and docs were inspected with targeted `rg` searches for Builder, Launchpad, candidate generation, comparison/verdict, and `is_rebalance_recommendation`. No source behavior was changed in Session 00.
- [x] (2026-06-05) Session 00 ExecPlan file created at `docs/exec_plans/block_6_builder_exec_plan.md`.
- [x] (2026-06-05) Session 01 BuilderPrefill contract implemented. `src/portfolio_alternatives_builder.py` now exposes strict required/prohibited BuilderPrefill contract constants and validation, and `build_builder_prefill_from_launchpad_card()` emits the Session 01 fields without candidate output fields. Product-contract validation and focused tests were updated.
- [x] (2026-06-05) Session 02 Launchpad card to BuilderPrefill mapper implemented. `src/portfolio_alternatives_builder.py` now exposes `launchpad_card_to_builder_prefill()` as the public mapper, keeps `build_builder_prefill_from_launchpad_card()` as a backward-compatible wrapper, and focused Session 02 tests cover targeted, reference-benchmark, and data-quality handoff behavior.
- [x] (2026-06-05) Session 03 Strategy Selector implemented. `src/portfolio_alternatives_builder.py` now exposes `select_builder_strategy()` and the Launchpad-to-prefill mapper includes strategy state while still avoiding candidate generation.
- [x] (2026-06-05) Session 04 Parameter Builder Simple Mode implemented. `src/portfolio_alternatives_builder.py` now exposes `build_simple_builder_parameters()` with the requested editable fields, basic preset allowlist, user overrides, method-change preservation, and advanced-setting rejection without candidate outputs.
- [x] (2026-06-05) Session 05 Builder validation layer implemented. `src/portfolio_alternatives_builder.py` now exposes `validate_builder_setup()` with explicit validation statuses and focused tests for valid, blocked data-quality, missing goal/method, unsupported method, invalid constraints, feasibility risk, reference boundary, and targeted-context preservation.
- [x] (2026-06-05) Session 06 CandidateSetup output contract implemented. `src/portfolio_alternatives_builder.py` now exposes `builder_prefill_to_candidate_setup()` and strict CandidateSetup contract validation without candidate ids, weights, metrics, stress results, comparison, or verdict fields.
- [x] (2026-06-05) Session 07 runtime wiring implemented. Block 4 diagnosis writing now also materializes `portfolio_alternatives_builder.json` beside `candidate_launchpad.json`; product-bundle discovery exposes `portfolio_alternatives_builder_json`, and core Blocks 1-3 hygiene prunes stale Builder output.
- [x] (2026-06-05) Session 08 documentation sync completed. Product, architecture, output, workflow, runtime-entrypoint, detailed specs, changelog, decisions, and Block 6 contract docs now state that Block 6 is setup/validation and Block 7 owns candidate generation.
- [x] (2026-06-05) Session 09 live validation completed. Focused tests, product-bundle adjacency tests, docs verification, synthetic live Builder cases, dry-run smoke, and actual `run_portfolio_review.py` smoke all passed; the smoke wrote `portfolio_alternatives_builder.json` for a reference benchmark setup without running candidate factory.
- [x] (2026-06-05) Session 10 final readiness gate completed with verdict `NOT_READY` for immediate Block 7 handoff from this workspace state. Block 6 focused tests, adjacent product-bundle tests, documentation verification, dry-run smoke, and Builder artifact inspection passed; fresh live `run_portfolio_review.py` did not complete within the allowed runtime window and was stopped, so the plan cannot honestly claim `BLOCK_6_READY` / `READY_FOR_BLOCK_7_CANDIDATE_GENERATION`.

## Surprises & Discoveries

- Observation: The repository already contains a partial Builder prefill helper.
  Evidence: `src/portfolio_alternatives_builder.py` defines `build_builder_prefill_from_launchpad_card()`, which returns a dictionary with Launchpad-derived fields and does not execute subprocesses.

- Observation: The current Builder also contains an explicit one-candidate delegation path that is too close to Block 7 for the new Block 6 boundary.
  Evidence: `src/portfolio_alternatives_builder.py` defines `PortfolioAlternativeRequest`, `build_portfolio_alternative_plan()`, and `run_portfolio_alternative_plan()`. The plan delegates to `run_candidate_factory.py --candidates <candidate_id> --then-compare`; `run_portfolio_alternative_plan()` defaults to `dry_run=True`.

- Observation: There is no separate `CandidateSetup` contract yet.
  Evidence: targeted file inspection found `docs/specs/portfolio_alternatives_builder_spec.md` and existing Builder prefill tests, but no `docs/specs/builder_prefill_spec.md`, no `docs/specs/candidate_setup_spec.md`, and no dedicated source-level CandidateSetup object.

- Observation: There is no product-bundle artifact named `portfolio_alternatives_builder.json` yet.
  Evidence: `src/product_bundle_paths.py` product-bundle keys currently include `problem_classification_json`, `candidate_launchpad_json`, `current_vs_candidate_json`, `decision_verdict_json`, `ai_commentary_context_json`, and `what_changed_summary_json`, but not `portfolio_alternatives_builder_json`.

- Observation: Launchpad v3 already carries most source fields needed by BuilderPrefill.
  Evidence: `src/block_4/launchpad_cards.py` writes `source_diagnosis_id`, `hypothesis_to_test`, `card_type`, `launch_status`, `success_criteria`, `tradeoff_to_watch`, `when_to_skip`, `decision_boundary`, and `is_rebalance_recommendation: False`.

- Observation: Existing validators already enforce part of the no-recommendation boundary.
  Evidence: `scripts/core_mvp_validation_contract.py` rejects Launchpad cards or Builder prefill objects that lose the decision boundary, set `is_rebalance_recommendation` to anything other than `false`, or let data-quality prefill allow candidate generation.

- Observation: The default portfolio review runtime already avoids automatic candidate generation.
  Evidence: `run_portfolio_review.py::resolve_candidate_execution_flags()` runs candidates only when explicit candidate flags, full/research flags, profile overrides, or factory control flags are present. Plain `run_portfolio_review.py` is diagnosis-only.

- Observation: Existing explicit candidate paths must be preserved but labelled carefully.
  Evidence: `run_portfolio_review.py --candidates equal_weight` and `src/portfolio_review_workflow.py` still call `run_candidate_factory.py` when candidates are explicitly requested. This is legacy/explicit candidate generation, not Block 6 setup.

- Observation: Session 01 can tighten BuilderPrefill without changing runtime candidate-generation behavior.
  Evidence: The focused handoff suite passed after adding `builder_prefill_id`, `source_problem_id`, `rebalancing_frequency`, `transaction_cost_bps`, `created_from`, `status`, and `warnings`, and after adding a guard that rejects `candidate_id`, `weights`, `candidate_status`, and `comparison_status`.

- Observation: The current repository documentation validator is `scripts/verify_docs.py`, not the older validate-docs script name.
  Evidence: Session 01 ran `.\.venv\Scripts\python.exe scripts\verify_docs.py`; the docs verifier needed the Block 6 future-session paths added to `src/docs_verify.py`'s allowed-missing list because the ExecPlan intentionally names future files.

- Observation: Session 02 could make the requested mapper name public without changing existing callers.
  Evidence: `launchpad_card_to_builder_prefill()` now owns the Launchpad-to-prefill transformation and `build_builder_prefill_from_launchpad_card()` delegates to it, so existing tests and imports remain compatible.

- Observation: Session 03 could add guided method selection without touching optimizer or candidate factory behavior.
  Evidence: `select_builder_strategy()` returns method setup state only, does not call `build_portfolio_alternative_plan()`, and the focused Block 6/Builder handoff suite passed with no generated output refresh.

- Observation: Session 04 could keep Simple Mode as a visible setup object instead of translating presets into hidden optimizer formulas.
  Evidence: `build_simple_builder_parameters()` returns only `goal`, `method`, `constraint_preset`, `max_asset_weight`, `min_asset_weight`, `volatility_target`, `rebalancing_frequency`, and `transaction_cost_bps` as editable fields, and rejects advanced override fields such as tax-aware optimization.

- Observation: Session 05 validation can block obviously bad setup without knowing or running the optimizer.
  Evidence: `validate_builder_setup()` checks allowlisted method ids, missing goal/method, simple constraint sanity, optional `asset_count` feasibility risk, reference boundary preservation, and targeted hypothesis/success/tradeoff preservation while leaving CandidateSetup and candidate generation for later sessions.

- Observation: PowerShell did not expand the pytest glob `tests\test_block_6_*.py` when passed directly to pytest in this environment.
  Evidence: The direct command returned `ERROR: file or directory not found: tests\test_block_6_*.py`; using `Get-ChildItem -Filter 'test_block_6_*.py'` to pass concrete file paths ran the intended suite.

- Observation: CandidateSetup could be built from existing Simple Mode setup plus validation without introducing a candidate-generation plan.
  Evidence: `builder_prefill_to_candidate_setup()` calls `build_simple_builder_parameters()` and `validate_builder_setup()`, returns a setup only when validation is `valid`, and focused tests confirm prohibited fields such as `candidate_id` and `weights` are absent.

- Observation: The safest runtime hook is the Block 4 diagnosis writer because it is the single place that writes `candidate_launchpad.json` for direct Block 4 use and portfolio-first materialization.
  Evidence: `write_block_4_diagnosis_outputs()` now calls `write_portfolio_alternatives_builder_outputs()` immediately after writing Launchpad; `tests/test_product_bundle_paths.py` fixtures that seed Block 4 now discover `portfolio_alternatives_builder_json`.

- Observation: Session 08 documentation sync required changing the output boundary from a six-file-only bundle to a six-file decision bundle plus the Block 6 setup artifact.
  Evidence: `OUTPUTS.md`, `docs/specs/README.md`, `SPEC.md`, `PRODUCT.md`, `ARCHITECTURE.md`, and `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md` now name `portfolio_alternatives_builder.json` as setup-only and route candidate generation to Block 7.

- Observation: The live default portfolio review can update diagnosis-only tombstones for comparison/verdict files while still not generating candidates.
  Evidence: Actual `run_portfolio_review.py` completed with `Runtime mode: product_diagnosis_only`, `candidate_factory_run.json` was missing, and `current_vs_candidate.json` / `decision_verdict.json` contained `diagnostic_only: true`, `tombstone: no_candidate_v1`, and `artifact_status: not_authoritative`.

- Observation: The live current/demo portfolio primary Launchpad card was a mixed-evidence reference benchmark setup.
  Evidence: `Main portfolio/analysis_subject/portfolio_alternatives_builder.json` had `schema_version: portfolio_alternatives_builder_v1`, `status: ok`, `validation_status: valid`, `builder_prefill.method_role: reference_benchmark`, `candidate_setup` present, `is_rebalance_recommendation: false`, and no prohibited `candidate_id` field.

- Observation: Session 10 source/docs/contracts remained green, but the fresh live CLI completion gate did not pass in this workspace.
  Evidence: Block 6 focused/adjacent pytest returned `63 passed`, product-bundle path tests returned `22 passed`, product-bundle hygiene plus Block 4 diagnosis tests returned `12 passed`, and `scripts/verify_docs.py` returned `docs verification: OK`. `run_portfolio_review.py --dry-run` reported `Runtime mode: product_diagnosis_only` and `Candidates: disabled by default`. A fresh `run_portfolio_review.py` run exceeded 304 seconds, was still running after an additional 180 seconds, and was stopped to avoid leaving background processes. The existing `Main portfolio/analysis_subject/portfolio_alternatives_builder.json` inspection still passed the Block 6 boundary checks: schema `portfolio_alternatives_builder_v1`, `status: ok`, `can_generate_candidate: true`, `candidate_setup` present, `method_role: reference_benchmark`, `is_rebalance_recommendation: false`, no `candidate_id`, and no `candidate_factory_run.json`.

## Decision Log

- Decision: Block 6 will introduce a separate `CandidateSetup` contract rather than reusing `PortfolioAlternativeBuildPlan`.
  Rationale: `PortfolioAlternativeBuildPlan` contains `candidate_id` and a factory command. The requested Block 6 boundary says CandidateSetup is a validated setup handoff to Block 7, not a candidate and not a factory execution plan.
  Date/Author: 2026-06-05 / Codex.

- Decision: `BuilderPrefill` and `CandidateSetup` must be separate in both documentation and implementation.
  Rationale: `BuilderPrefill` means “what came from Launchpad card.” `CandidateSetup` means “what the user confirmed or edited in Builder and what can be passed to Block 7.” Mixing them would make it unclear whether the user accepted the setup.
  Date/Author: 2026-06-05 / Codex.

- Decision: Data-quality Launchpad cards may write `portfolio_alternatives_builder.json`, but only as a blocked artifact.
  Rationale: The file can be useful for UI/API state, but it must not look successful and must not expose a ready setup for candidate generation.
  Date/Author: 2026-06-05 / Codex.

- Decision: Equal Weight and Risk Parity reference tests remain `reference_benchmark`, never rebalance recommendations.
  Rationale: Mixed evidence and acceptable-current-portfolio states may need transparent references, but those references are diagnostic comparisons only.
  Date/Author: 2026-06-05 / Codex.

- Decision: Keep `build_builder_prefill_from_launchpad_card()` as a compatibility wrapper around the new `launchpad_card_to_builder_prefill()` mapper.
  Rationale: Session 02 requires the stable public mapper name, while existing code, tests, validators, and docs already use the older helper name. A wrapper avoids churn and preserves the no-candidate-generation boundary.
  Date/Author: 2026-06-05 / Codex.

- Decision: The Strategy Selector will choose guided defaults from goal ids before falling back to a Launchpad card's raw first/default method when that guided method is available in the card.
  Rationale: Session 03 requires the Builder to map goals to guided methods instead of exposing a raw optimizer menu. Preferring the guided method when present lets `Improve diversification` open on `risk_parity` while preserving Launchpad's allowed method rows and avoiding unsupported methods.
  Date/Author: 2026-06-05 / Codex.

- Decision: Simple Mode presets are labels and visible constraint fields, not hidden optimizer recipes.
  Rationale: Session 04 requires presets but also says not to add advanced settings or change optimizer behavior. Keeping presets as setup labels avoids inventing formulas and preserves the Block 6 boundary.
  Date/Author: 2026-06-05 / Codex.

- Decision: Validation returns one blocking status instead of trying to repair setup.
  Rationale: Session 05 asks Block 6 to block bad setup before Block 7. A single `validation_status` with explicit errors is easier for UI/API callers to route and avoids silently changing user input.
  Date/Author: 2026-06-05 / Codex.

- Decision: CandidateSetup is emitted only for `valid` Builder validation; blocked or invalid Builder states keep `candidate_setup: null` in the Builder document.
  Rationale: Session 06 defines CandidateSetup as what Block 7 can consume. Exposing a setup for data-quality, missing-method, invalid-method, or infeasible states would blur the Block 6/Block 7 boundary.
  Date/Author: 2026-06-05 / Codex.

- Decision: Runtime wiring lives in `write_block_4_diagnosis_outputs()` rather than only in `run_report.py`.
  Rationale: The plan says Builder output is written after `candidate_launchpad.json`; placing the hook beside the Launchpad writer covers direct Block 4 calls, tests, scripts, and portfolio-first materialization without starting candidate generation.
  Date/Author: 2026-06-05 / Codex.

- Decision: Treat `portfolio_alternatives_builder.json` as a product-bundle setup artifact, but keep `current_vs_candidate.json` / `decision_verdict.json` as post-candidate or diagnosis-only tombstone artifacts depending on workflow state.
  Rationale: Block 6 now has a durable UI/API handoff file, but comparison and verdict still require either an explicit generated candidate or a non-authoritative diagnosis-only tombstone. This keeps Session 09 live smoke consistent with the Block 6/Block 7 boundary.
  Date/Author: 2026-06-05 / Codex.

- Decision: Close Session 10 with final verdict `NOT_READY` rather than `BLOCK_6_READY`.
  Rationale: The plan explicitly permits `BLOCK_6_READY` and `READY_FOR_BLOCK_7_CANDIDATE_GENERATION` only if all contracts, tests, docs, and live proof pass. The code/docs/contract evidence passed, but the fresh live `run_portfolio_review.py` completion proof timed out in this workspace. A partial artifact inspection is useful evidence but is not the same as a completed live smoke.
  Date/Author: 2026-06-05 / Codex.

## Outcomes & Retrospective

Session 00 established the current baseline without implementation changes. Session 01 defined and implemented the strict Launchpad-derived BuilderPrefill contract. Session 02 added the public Launchpad-card-to-BuilderPrefill mapper while preserving the previous helper as a wrapper. Session 03 added the guided Strategy Selector and wired its state into prefill without creating candidates. Session 04 added the Simple Mode parameter builder with only the requested editable fields and advanced-setting rejection. Session 05 added the validation layer with explicit statuses that block data-quality cards, unsupported methods, missing setup, invalid constraints, obvious feasibility risks, reference-boundary violations, and targeted-context loss before Block 7. Session 06 added the CandidateSetup contract as a validated setup handoff only. Session 07 added runtime writing for `portfolio_alternatives_builder.json` after Launchpad and product-bundle discovery for `portfolio_alternatives_builder_json`, without invoking candidate generation. Session 08 synchronized the product, architecture, output, workflow, runtime-entrypoint, changelog, decision, and detailed spec documentation, including dedicated `builder_prefill_spec.md` and `candidate_setup_spec.md`. Session 09 proved targeted, reference-benchmark, and data-quality Builder states and ran a current/demo portfolio smoke. Session 10 closed the readiness gate with a strict `NOT_READY` verdict for immediate Block 7 handoff from this workspace state: Block 6 contracts, tests, docs, dry-run, and artifact boundary checks passed, but the fresh live CLI completion proof timed out.

## Context and Orientation

The repository root is `D:\Desktop\CURSOR TULA DIAGNOSTICS`. The current canonical product flow is:

    Input portfolio
    -> Portfolio X-Ray
    -> Stress Test Lab
    -> Problem Classification
    -> Candidate Launchpad
    -> Portfolio Alternatives Builder
    -> Candidate Generation
    -> Current vs Candidate Comparison
    -> Decision Verdict
    -> AI Commentary / grounding
    -> Monitoring / What Changed

Block 5 is Candidate Launchpad. It produces `candidate_launchpad.json`, normally under `{output_dir_final}/analysis_subject/` for portfolio-first runs. A Launchpad card is not a portfolio and must not contain weights.

Block 6 is Portfolio Alternatives Builder. It reads one selected Launchpad card or a manual/custom entry and produces editable setup state. It must not run optimizers, must not call candidate factory, must not create weights, and must not write comparison or verdict artifacts.

Block 7 is Candidate Generation. It is the first layer that may turn a validated setup into a real candidate portfolio after an explicit Generate candidate action.

`BuilderPrefill` means the fields copied from a Launchpad card before the user edits anything. `CandidateSetup` means the Builder fields after the user has confirmed or edited them and after validation has passed. Neither object is a candidate.

Key current files:

- `src/portfolio_alternatives_builder.py`: current Builder wrapper, existing prefill helper, legacy one-candidate factory plan helper.
- `src/block_4/launchpad_cards.py`: builds Launchpad v3 cards.
- `src/block_4/diagnosis_builder.py`: writes `problem_classification.json` and `candidate_launchpad.json`.
- `run_portfolio_review.py`: portfolio-first CLI and candidate-generation flag handling.
- `src/portfolio_review_workflow.py`: ordered subprocess plan for diagnosis, candidate factory, comparison, and PDF steps.
- `src/product_bundle_paths.py`: manifest/product-bundle path discovery.
- `scripts/core_mvp_validation_contract.py`: product-contract validators for Launchpad, Builder prefill, Current vs Candidate, and Decision Verdict.
- `docs/specs/portfolio_alternatives_builder_spec.md`: current Builder spec.
- `docs/specs/candidate_launchpad_spec.md`: Launchpad artifact spec.

## Current State

The current implementation has a partial Builder prefill layer. `build_builder_prefill_from_launchpad_card(card, next_diagnostic_step=None)` returns a plain dictionary. It copies many Launchpad fields and sets `is_rebalance_recommendation: False`. It uses `builder_mode` values such as `guided_from_diagnosis`, `blocked_data_quality`, and `monitor_only`.

The current implementation also has a separate `build_portfolio_alternative_plan()` path that maps method ids to candidate ids and returns a command for `run_candidate_factory.py`. This is not suitable as the canonical Block 6 output because it includes candidate-generation plumbing and a `candidate_id`.

The default `run_portfolio_review.py` path is already diagnosis-only. Candidate factory and comparison are explicit. This helps Block 6 because runtime wiring can add Builder state after Launchpad without changing default candidate generation behavior.

## Existing Files

Existing source and test files relevant to Block 6:

- `src/portfolio_alternatives_builder.py`
- `src/block_4/launchpad_cards.py`
- `src/block_4/diagnosis_builder.py`
- `run_portfolio_review.py`
- `src/portfolio_review_workflow.py`
- `scripts/core_mvp_validation_contract.py`
- `scripts/validate_block_4_live.py`
- `tests/test_portfolio_alternatives_builder.py`
- `tests/test_candidate_launchpad_builder_handoff.py`
- `tests/test_block_6_builder_prefill_contract.py`
- `tests/test_block_6_launchpad_to_builder_prefill.py`
- `tests/test_block_6_strategy_selector.py`
- `tests/test_block_4_launchpad_cards.py`
- `tests/test_portfolio_review_workflow.py`
- `tests/test_product_bundle_hygiene.py`

Existing documentation relevant to Block 6:

- `docs/specs/portfolio_alternatives_builder_spec.md`
- `docs/specs/candidate_launchpad_spec.md`
- `docs/product_flow_operator_guide.md`
- `docs/runtime_entrypoints.md`
- `OUTPUTS.md`
- `SPEC.md`
- `WORKFLOW.md`
- `DECISIONS.md`
- `CHANGELOG.md`

Files that are missing and should be added in later sessions:

- `docs/specs/builder_prefill_spec.md`
- `docs/specs/candidate_setup_spec.md`
- `tests/test_block_6_parameter_builder_simple_mode.py`
- `tests/test_block_6_builder_validation.py`
- `tests/test_block_6_candidate_setup_contract.py`
- `tests/test_block_6_product_runtime_wiring.py`

## Existing JSON Outputs

Current portfolio-first diagnosis artifacts:

- `{output_dir_final}/analysis_subject/problem_classification.json`
- `{output_dir_final}/analysis_subject/candidate_launchpad.json`
- `{output_dir_final}/analysis_subject/portfolio_xray.json`
- `{output_dir_final}/analysis_subject/stress_report.json`
- `{output_dir_final}/analysis_subject/output_manifest.json`

Current post-candidate/post-comparison artifacts:

- `{output_dir_final}/candidate_factory_run.json`
- `{output_dir_final}/candidate_comparison.json`
- `{output_dir_final}/current_vs_candidate.json`
- `{output_dir_final}/decision_verdict.json`
- `{output_dir_final}/ai_commentary_context.json`
- `{output_dir_final}/what_changed_summary.json`

Missing Block 6 artifact:

- `{output_dir_final}/analysis_subject/portfolio_alternatives_builder.json` should be introduced as the product-facing Builder state artifact. It should be discoverable in manifests as `portfolio_alternatives_builder_json`.

## Known Gaps

There is no dedicated `BuilderPrefill` type with the exact requested fields and prohibited-field checks.

There is now a dedicated CandidateSetup dictionary contract exposed by `builder_prefill_to_candidate_setup()`. Existing `PortfolioAlternativeBuildPlan` remains a separate legacy/explicit factory delegation helper and is not the canonical Block 6 output because it contains a `candidate_id` and factory command.

The Strategy Selector now maps goal to suggested method while preserving `original_suggested_method`, `selected_method`, and `method_changed_by_user`. Later sessions still need to consume this state in the Simple Mode parameter builder, validation layer, and CandidateSetup contract.

The Simple Mode parameter builder now exposes only `goal`, `method`, `constraint_preset`, `max_asset_weight`, `min_asset_weight`, `volatility_target`, `rebalancing_frequency`, and `transaction_cost_bps`, and blocks advanced settings.

The validation layer now returns the requested statuses: `valid`, `blocked_by_data_quality`, `invalid_method`, `missing_goal`, `missing_method`, `invalid_constraints`, `infeasible_constraints_risk`, and `reference_benchmark_boundary_violation`.

`portfolio_alternatives_builder.json` is now written after Launchpad by `write_block_4_diagnosis_outputs()`, and `write_portfolio_alternatives_builder_outputs()` can also be called directly.

Documentation currently describes Builder prefill and one-candidate delegation, but must be tightened to say that Block 6 prepares setup only and Block 7 owns actual candidate generation after explicit Generate candidate action.

## Do Not Touch

Do not change optimizer formulas, candidate factory formulas, stress calculations, metric formulas, or existing candidate portfolio construction behavior.

Do not remove or break legacy explicit candidate paths such as `run_portfolio_review.py --candidates equal_weight`, `run_candidate_factory.py`, or the current `PortfolioAlternativeBuildPlan` helper. Later sessions may relabel them as explicit/legacy candidate-generation paths, but they must keep working.

Do not treat generated outputs as source. Do not refresh or commit routine generated portfolio artifacts unless the active session explicitly targets generated output refresh.

Do not create candidate weights, comparison artifacts, or Decision Verdict from Block 6.

Do not let data-quality cards become Equal Weight or Risk Parity benchmark tests.

Do not treat Equal Weight or Risk Parity reference benchmarks as rebalance recommendations.

## Plan of Work

Session 01 defines the strict BuilderPrefill contract. Implement or document a separate object for Launchpad-derived prefill only. The minimum fields are `builder_prefill_id`, `source_card_id`, `source_diagnosis_id`, `source_problem_id`, `card_type`, `launch_status`, `method_role`, `hypothesis_to_test`, `next_diagnostic_step`, `goal`, `suggested_method`, `alternative_methods`, `constraint_preset`, `max_asset_weight`, `min_asset_weight`, `volatility_target`, `rebalancing_frequency`, `transaction_cost_bps`, `success_criteria`, `tradeoff_to_watch`, `when_to_skip`, `decision_boundary`, `is_rebalance_recommendation`, `created_from`, `status`, and `warnings`. It must never contain `candidate_id`, `weights`, `candidate_status`, or `comparison_status`.

Session 02 implements `launchpad_card_to_builder_prefill(card)`. It must preserve source diagnosis, card id, hypothesis, goal, method fields, success criteria, tradeoff, skip rule, decision boundary, card type, launch status, method role, and `is_rebalance_recommendation: false`. It must not create candidates, call optimizers, write weights, write current-vs-candidate, or write Decision Verdict.

Session 03 implements Strategy Selector. It maps goals to suggested methods in a guided way instead of showing a raw optimizer menu. Examples: `improve_crisis_resilience` maps to `minimum_cvar_constrained`; `improve_diversification` maps to `risk_parity`; `reduce_concentration` maps to `equal_weight` with max-weight constraints; `reduce_volatility` maps to `minimum_variance`; `compare_simple_benchmark` maps to `equal_weight` or `risk_parity`. If the user changes method, the setup must preserve `original_suggested_method`, `selected_method`, and `method_changed_by_user: true`.

Session 04 implements Parameter Builder Simple Mode. It must provide editable fields for `goal`, `method`, `constraint_preset`, `max_asset_weight`, `min_asset_weight`, `volatility_target`, `rebalancing_frequency`, and `transaction_cost_bps`. Presets are `conservative`, `balanced`, `aggressive`, `custom`, and `basic_reference`. Do not add advanced settings such as tax-aware optimization, turnover-aware objective, asset-class bounds, custom risk budgets, Robust MV lambda, advanced CVaR settings, covariance selector, expected-return model selector, leverage, or shorting.

Session 05 implements validation. It must produce explicit statuses and block bad setup before Block 7. Data-quality cards produce `blocked_by_data_quality` and `can_generate_candidate: false`. Unsupported methods fail. Constraint sanity checks must reject max weight below min weight, negative min weight, non-positive max weight, and obvious feasibility failures. Reference benchmark setups must preserve `method_role: reference_benchmark`, `is_rebalance_recommendation: false`, and a decision boundary. Targeted setups must preserve `hypothesis_to_test`, `success_criteria`, and `tradeoff_to_watch`.

Session 06 implements CandidateSetup. CandidateSetup is what the user confirmed or edited and what Block 7 can consume. It should contain `candidate_setup_id`, `builder_prefill_id`, `source_card_id`, `source_diagnosis_id`, `goal`, `selected_method`, `original_suggested_method`, `method_changed_by_user`, `parameters`, `constraints`, `success_criteria`, `tradeoff_to_watch`, `when_to_skip`, `decision_boundary`, `is_rebalance_recommendation`, `can_generate_candidate`, `validation_status`, `validation_warnings`, and `created_at`. It must not contain `candidate_id`, `weights`, `portfolio_metrics`, `stress_results`, `comparison`, or `verdict`.

Session 07 wires runtime. After `candidate_launchpad.json` is written, the product workflow should write `portfolio_alternatives_builder.json` when a primary Launchpad card exists. Valid targeted/reference cards get a ready setup. Data-quality cards get a blocked file with `status: blocked`, `can_generate_candidate: false`, and `reason: data_quality_blocker`. Plain `run_portfolio_review.py` must still not run Block 7 automatically.

Session 08 synchronizes docs. Update `PRODUCT.md`, `ARCHITECTURE.md`, `SPEC.md`, `OUTPUTS.md`, `WORKFLOW.md`, `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`, `docs/specs/builder_prefill_spec.md`, `docs/specs/candidate_setup_spec.md`, `docs/runtime_entrypoints.md`, `CHANGELOG.md`, and `DECISIONS.md` as needed. The docs must state that Block 6 is Builder setup and Block 7 is Candidate Generation.

Session 09 runs live validation. Prove mixed-evidence reference setup, targeted weak-crisis-resilience setup, and data-quality blocker setup. Run focused tests and a representative `run_portfolio_review.py` smoke. Confirm Builder preserves success criteria and decision boundary, blocks bad data, and does not create candidates.

Session 10 closes readiness. The final verdict is `BLOCK_6_READY` and `READY_FOR_BLOCK_7_CANDIDATE_GENERATION` only if all contracts, tests, docs, and live proof pass. Otherwise mark `NOT_READY` and list blockers.

## Concrete Steps

From repository root `D:\Desktop\CURSOR TULA DIAGNOSTICS`, Session 00 used these audit commands:

    rg -n "builder|Builder|portfolio_alternatives_builder|builder_prefill|Generate candidate" src tests docs *.py *.md
    rg -n "candidate_launchpad|Candidate Launchpad|Launchpad" src tests docs *.py *.md
    rg -n "candidate_generation|optimization config|candidate config|current_vs_candidate|Decision Verdict|decision_verdict" src tests docs *.py *.md
    rg -n "is_rebalance_recommendation" src tests docs *.py *.md

The next implementation agent should start Session 01 by reading:

    Get-Content -Raw PLANS.md
    Get-Content -Raw WORKFLOW.md
    Get-Content -Raw RULES.md
    Get-Content -Raw docs/specs/portfolio_alternatives_builder_spec.md
    Get-Content -Raw docs/specs/candidate_launchpad_spec.md
    Get-Content -Raw src/portfolio_alternatives_builder.py
    Get-Content -Raw scripts/core_mvp_validation_contract.py

Then implement each session with focused tests before broad tests.

## Validation and Acceptance

Session 00 acceptance is complete when this ExecPlan exists and the baseline makes clear where Block 5 ends, where Block 6 should start, and where Block 7 should start.

Block 5 ends at `candidate_launchpad.json`: it is a set of diagnostic cards and never a portfolio.

Block 6 starts when one Launchpad card is selected and converted into `BuilderPrefill`, then user-confirmed/edited into validated `CandidateSetup`.

Block 7 starts only after explicit Generate candidate action consumes a valid `CandidateSetup`.

Full Block 6 acceptance requires:

- `BuilderPrefill` and `CandidateSetup` are separate contracts.
- `portfolio_alternatives_builder.json` exists for valid Builder setup.
- A data-quality card produces blocked Builder output, not successful output.
- Builder preserves success criteria and decision boundary.
- Builder validates method, constraints, and generation boundary.
- Reference benchmarks are not recommendations.
- No candidate is generated automatically.
- No comparison or verdict is written by Block 6.
- Docs state that Block 6 is Builder setup and Block 7 is Candidate Generation.

Focused test commands for later sessions:

    $block6 = Get-ChildItem -Path .\tests -Filter 'test_block_6_*.py' | ForEach-Object { $_.FullName }; .\.venv\Scripts\python.exe -m pytest $block6
    .\.venv\Scripts\python.exe -m pytest tests\test_portfolio_alternatives_builder.py tests\test_candidate_launchpad_builder_handoff.py
    .\.venv\Scripts\python.exe run_portfolio_review.py
    .\.venv\Scripts\python.exe scripts\verify_docs.py

Session 01 confirmed `scripts/verify_docs.py` is the current docs-check command. If a later session changes the docs validator, record the substitution in `Surprises & Discoveries`.

Session 01 validation completed from the repository root:

    .\.venv\Scripts\python.exe -m pytest tests\test_block_6_builder_prefill_contract.py tests\test_portfolio_alternatives_builder.py tests\test_candidate_launchpad_builder_handoff.py -q

Expected/observed result:

    27 passed

Session 02 validation completed from the repository root:

    .\.venv\Scripts\python.exe -m pytest tests\test_block_6_launchpad_to_builder_prefill.py tests\test_block_6_builder_prefill_contract.py tests\test_portfolio_alternatives_builder.py tests\test_candidate_launchpad_builder_handoff.py -q
    .\.venv\Scripts\python.exe scripts\verify_docs.py

Expected/observed result:

    30 passed
    docs verification: OK

Session 03 validation completed from the repository root:

    .\.venv\Scripts\python.exe -m pytest tests\test_block_6_strategy_selector.py tests\test_block_6_launchpad_to_builder_prefill.py tests\test_block_6_builder_prefill_contract.py tests\test_portfolio_alternatives_builder.py tests\test_candidate_launchpad_builder_handoff.py -q

Expected/observed result:

    43 passed

Session 04-05 focused validation completed from the repository root:

    .\.venv\Scripts\python.exe -m pytest tests\test_block_6_parameter_builder_simple_mode.py tests\test_block_6_builder_validation.py -q

Expected/observed result:

    14 passed

Session 04-05 adjacent Block 6/Builder validation completed from the repository root:

    $block6 = Get-ChildItem -Path .\tests -Filter 'test_block_6_*.py' | ForEach-Object { $_.FullName }; .\.venv\Scripts\python.exe -m pytest $block6 .\tests\test_portfolio_alternatives_builder.py .\tests\test_candidate_launchpad_builder_handoff.py -q

Expected/observed result:

    57 passed

Session 06-07 focused validation completed from the repository root:

    .\.venv\Scripts\python.exe -m pytest tests\test_block_6_candidate_setup_contract.py tests\test_block_6_product_runtime_wiring.py -q

Expected/observed result:

    6 passed

Session 06-07 adjacent Block 6/Builder validation completed from the repository root:

    $block6 = Get-ChildItem -Path .\tests -Filter 'test_block_6_*.py' | ForEach-Object { $_.FullName }; .\.venv\Scripts\python.exe -m pytest $block6 .\tests\test_portfolio_alternatives_builder.py .\tests\test_candidate_launchpad_builder_handoff.py -q

Expected/observed result:

    63 passed

Session 07 product-bundle and Block 4 adjacency validation completed from the repository root:

    .\.venv\Scripts\python.exe -m pytest tests\test_product_bundle_paths.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_product_bundle_hygiene.py tests\test_block_4_diagnosis_builder.py -q
    .\.venv\Scripts\python.exe scripts\verify_docs.py

Expected/observed result:

    22 passed
    12 passed
    docs verification: OK

Session 08-09 documentation and live validation completed from the repository root:

    $block6 = Get-ChildItem -Path .\tests -Filter 'test_block_6_*.py' | ForEach-Object { $_.FullName }; .\.venv\Scripts\python.exe -m pytest $block6 .\tests\test_portfolio_alternatives_builder.py .\tests\test_candidate_launchpad_builder_handoff.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_product_bundle_paths.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_product_bundle_hygiene.py tests\test_block_4_diagnosis_builder.py -q
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    .\.venv\Scripts\python.exe run_portfolio_review.py --dry-run
    .\.venv\Scripts\python.exe run_portfolio_review.py

Expected/observed result:

    63 passed
    22 passed
    12 passed
    docs verification: OK
    dry-run: Runtime mode product_diagnosis_only; Candidates disabled by default
    actual smoke: completed; wrote Main portfolio/analysis_subject/portfolio_alternatives_builder.json with schema portfolio_alternatives_builder_v1, status ok, validation valid, reference_benchmark method role, can_generate_candidate true, is_rebalance_recommendation false; no candidate_factory_run.json was created

Session 09 synthetic live Builder proof completed from the repository root with an inline Python check of three Launchpad cards:

    targeted_weak_crisis_resilience: status ready_for_user_confirmation, validation valid, can_generate true, candidate_setup present, selected_method minimum_cvar_constrained, decision boundary preserved
    mixed_evidence_reference: status ready_for_user_confirmation, validation valid, can_generate true, candidate_setup present, method_role reference_benchmark, selected_method equal_weight, decision boundary preserved
    data_quality_blocker: status blocked, validation blocked_by_data_quality, can_generate false, candidate_setup absent, decision boundary preserved

Session 10 final readiness gate completed from the repository root:

    $block6 = Get-ChildItem -Path .\tests -Filter 'test_block_6_*.py' | ForEach-Object { $_.FullName }; .\.venv\Scripts\python.exe -m pytest $block6 .\tests\test_portfolio_alternatives_builder.py .\tests\test_candidate_launchpad_builder_handoff.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_product_bundle_paths.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_product_bundle_hygiene.py tests\test_block_4_diagnosis_builder.py -q
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    .\.venv\Scripts\python.exe run_portfolio_review.py --dry-run
    .\.venv\Scripts\python.exe run_portfolio_review.py

Observed result:

    63 passed
    22 passed
    12 passed
    docs verification: OK
    dry-run: Runtime mode product_diagnosis_only; Candidates disabled by default
    actual smoke: timed out after 304 seconds and was still running after an additional 180 seconds; stopped by operator
    artifact inspection after timeout: portfolio_alternatives_builder_v1, status ok, can_generate_candidate true, candidate_setup present, method_role reference_benchmark, is_rebalance_recommendation false, no candidate_id, no candidate_factory_run.json

Final Session 10 verdict:

    NOT_READY

The blocker is not a failed Block 6 contract. The blocker is missing fresh completed live CLI proof in this workspace. Until a completed `run_portfolio_review.py` smoke or an accepted equivalent live/offline gate passes, do not mark this plan `BLOCK_6_READY` or `READY_FOR_BLOCK_7_CANDIDATE_GENERATION`.

## Idempotence and Recovery

All implementation should be additive and safe to rerun. Writing `portfolio_alternatives_builder.json` should overwrite only that file for the current run and should not delete candidate, comparison, or verdict artifacts except through existing product-bundle hygiene functions that already own diagnosis-only cleanup.

If a later session breaks legacy explicit candidate generation, revert the wiring change for that path and preserve `run_portfolio_review.py --candidates <id>` behavior before continuing.

If a docs validation command is missing, do not invent a new docs validator in the same session. Use the existing validator discovered in the repo and record the finding.

## Artifacts and Notes

Session 00 file existence audit found these key files present:

    src/portfolio_alternatives_builder.py
    src/block_4/launchpad_cards.py
    src/block_4/diagnosis_builder.py
    run_portfolio_review.py
    src/portfolio_review_workflow.py
    scripts/core_mvp_validation_contract.py
    docs/specs/portfolio_alternatives_builder_spec.md
    docs/specs/candidate_launchpad_spec.md
    docs/specs/current_vs_candidate_spec.md

Session 00 git status before writing this plan showed only an unrelated untracked `.codex/` directory. Do not stage or modify that directory.

## Interfaces and Dependencies

Use Python standard library dataclasses or typed dictionaries in `src/portfolio_alternatives_builder.py` unless repo style during Session 01 shows a stronger local pattern. Keep JSON output as plain dictionaries.

Required public functions by the end of Block 6:

    launchpad_card_to_builder_prefill(card: Mapping[str, Any], *, next_diagnostic_step: Mapping[str, Any] | None = None) -> dict[str, Any]
    select_builder_strategy(goal: str | None, *, card_type: str | None = None, method_role: str | None = None, selected_method: str | None = None) -> dict[str, Any]
    build_simple_builder_parameters(prefill: Mapping[str, Any], *, overrides: Mapping[str, Any] | None = None) -> dict[str, Any]
    validate_builder_setup(setup: Mapping[str, Any]) -> dict[str, Any]
    builder_prefill_to_candidate_setup(prefill: Mapping[str, Any], *, edits: Mapping[str, Any] | None = None) -> dict[str, Any] | None
    build_portfolio_alternatives_builder_document(builder_prefill: Mapping[str, Any], candidate_setup: Mapping[str, Any] | None, validation: Mapping[str, Any]) -> dict[str, Any]
    write_portfolio_alternatives_builder_outputs(output_dir: str | Path, *, candidate_launchpad: Mapping[str, Any] | None, problem_classification: Mapping[str, Any] | None = None) -> dict[str, Path]

The exact names may be adjusted only if a later session records the reason in `Decision Log` and updates tests/docs consistently.

Revision note, 2026-06-05: Created during Session 00 at the user's request. This revision records the baseline audit and defines the remaining implementation sessions without changing source behavior.

Revision note, 2026-06-05: Session 01 implemented the strict BuilderPrefill contract only. It did not add CandidateSetup, runtime writing, candidate generation, comparison, or verdict behavior.

Revision note, 2026-06-05: Session 02 implemented only the public Launchpad-card-to-BuilderPrefill mapper. It added focused mapper tests and minimal documentation sync, but did not add Strategy Selector, Simple Mode parameters, validation statuses, CandidateSetup, runtime writing, candidate generation, comparison, or verdict behavior.

Revision note, 2026-06-05: Session 03 implemented only the Strategy Selector. It added `select_builder_strategy()`, strategy state on Builder prefill, focused strategy tests, and minimal documentation sync, but did not add Simple Mode parameter builder, validation statuses, CandidateSetup, runtime writing, candidate generation, comparison, or verdict behavior.

Revision note, 2026-06-05: Sessions 04-05 implemented only the Simple Mode parameter builder and Builder validation layer. They added `build_simple_builder_parameters()`, `validate_builder_setup()`, focused tests, and spec/changelog sync, but did not add CandidateSetup, runtime writing, candidate generation, comparison, or verdict behavior.

Revision note, 2026-06-05: Sessions 06-07 implemented CandidateSetup and runtime Builder artifact wiring only. They added `builder_prefill_to_candidate_setup()`, `build_portfolio_alternatives_builder_document()`, `write_portfolio_alternatives_builder_outputs()`, the `portfolio_alternatives_builder_json` manifest key, focused tests, and runtime wiring after Launchpad. They did not implement Session 08 documentation sync, Session 09 live validation, Block 7 candidate generation, comparison, or verdict behavior.

Revision note, 2026-06-05: Sessions 08-09 implemented documentation sync and live validation only. They added `docs/specs/builder_prefill_spec.md` and `docs/specs/candidate_setup_spec.md`, synchronized product/architecture/output/workflow/runtime/changelog/decision docs around the Block 6 setup and Block 7 generation boundary, and recorded focused/live validation evidence. They did not implement Session 10 final readiness, Block 7 candidate generation, comparison logic, or verdict behavior.

Revision note, 2026-06-05: Session 10 closed the final readiness gate only. It did not add features, did not implement Block 7 candidate generation, and did not change comparison or verdict logic. Focused tests, adjacent product-bundle tests, docs verification, dry-run, and artifact boundary inspection passed, but fresh live `run_portfolio_review.py` did not complete within the available runtime window. The final readiness verdict is `NOT_READY` pending a completed live smoke or accepted equivalent proof.
