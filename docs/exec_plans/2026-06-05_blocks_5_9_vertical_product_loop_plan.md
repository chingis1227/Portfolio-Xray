# Blocks 5-9 Vertical Product Loop

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This file follows `PLANS.md` from the repository root. It is deliberately self-contained so a future Codex chat can resume from this file without relying on earlier conversation memory.

## Purpose / Big Picture

The user-facing Portfolio MRI product should not feel like an optimizer cockpit. It should feel like a guided decision-support workflow: the user uploads or reviews the current portfolio, sees the main diagnosed problem, tests one reasonable hypothesis, compares the trade-off, and receives a decision verdict. The formula that governs this plan is `Diagnosis -> Hypothesis -> Candidate -> Comparison -> Verdict`.

After this plan is complete, a real demo should be able to produce this chain from the current portfolio: `problem_classification.json`, `candidate_launchpad.json`, `portfolio_alternatives_builder.json`, `candidate_generation.json`, `current_vs_candidate.json`, `decision_verdict.json`, and `ai_commentary_context.json`. The demo must use one selected candidate by default, not a candidate zoo, not a full research optimizer menu, and not a hidden recommendation engine.

The next implementation chat must begin with Session 00 only. If Session 00 succeeds, the implementer must stop, not start Session 01 in the same chat, and report: `Session 00 Р·Р°РІРµСЂС€РµРЅР° СѓСЃРїРµС€РЅРѕ` plus readiness status or blockers.

## Progress

- [x] 2026-06-05: Session 00 started. The ExecPlan file was created under `docs/exec_plans/` from the user-approved plan.
- [x] 2026-06-05: Session 00 updated `docs/exec_plans/README.md` so this plan is the active pointer.
- [x] 2026-06-05: Session 00 inspected dirty tree and recorded that many Block 6-related files were already modified or untracked before this plan file was added.
- [x] 2026-06-05: Session 00 ran the Block 6 focused pytest gate with explicit PowerShell file expansion. Result: 63 passed in 1.61 seconds.
- [x] 2026-06-05: Session 00 ran documentation verification. First run failed because this new ExecPlan used code-formatted references to future files; after rewording those future paths as planned targets, `scripts/verify_docs.py` passed.
- [x] 2026-06-05: Session 00 ran `run_portfolio_review.py --dry-run`. Result: exit 0; runtime mode `product_diagnosis_only`, workflow state `diagnosis_only`, candidates disabled by default.
- [x] 2026-06-05: Session 00 readiness decision: the Session 00 gate is passed and the next chat may start Session 01. This is not `READY_FOR_PRODUCT_DEMO`; it only means Block 6 setup/handoff is ready enough for the next planned method-scope session under the accepted dry-run gate.
- [x] 2026-06-05: Session 01 normalized guided Block 6 methods to the MVP allowlist: Equal Weight, Risk Parity, Hierarchical Risk Parity, Minimum Variance, Minimum CVaR, and Maximum Diversification.
- [x] 2026-06-05: Session 01 added capped/uncapped mode mapping, Session 01 constraint presets, and the required uncapped concentration warning while keeping Block 6 setup-only.
- [x] 2026-06-05: Session 01 hid advanced/legacy optimizer families from guided Builder validation while preserving them as backend/legacy classifications.

- [x] 2026-06-05: Session 02 added `src/candidate_generation.py` with the `candidate_generation_v1` one-attempt contract, writer, Builder-document extractor, method availability mapping, and non-recommendation guardrails.
- [x] 2026-06-05: Session 02 extended `CandidateSetup` to preserve `source_launchpad_card_type` and `hypothesis_to_test` so Block 7 can carry the Launchpad rationale without inventing it.
- [x] 2026-06-05: Session 02 added focused tests for Builder setup preservation, guided method/mode mapping, uncapped warning propagation, and the candidate-not-recommendation boundary.
- [x] 2026-06-05: Session 03 added `scripts/generate_candidate_from_builder_setup.py` with default input `Main portfolio/analysis_subject/portfolio_alternatives_builder.json` and default output `Main portfolio/candidate_generation.json`.
- [x] 2026-06-05: Session 03 wired the runtime script to delegate exactly one backend candidate through `run_candidate_factory.py --execution-mode fast` without `--then-compare`.
- [x] 2026-06-05: Session 03 added failed/infeasible factory-result mapping so failed attempts keep source setup/reason evidence, ignore stale weights, keep `is_rebalance_recommendation: false`, and set `handoff_to_comparison.can_compare = false`.
- [x] 2026-06-05: Session 03 added `tests/test_candidate_generation_failed_infeasible.py` and ran the focused Block 7 bundle with PowerShell-expanded file paths. Result: 18 passed in 0.64 seconds.
- [x] 2026-06-05: Session 03 ran `scripts/verify_docs.py` and Python compilation for `scripts/generate_candidate_from_builder_setup.py` plus `src/candidate_generation.py`. Result: both passed.

- [x] 2026-06-05: Session 04 added a Block 8-only helper, `write_block8_current_vs_candidate_only_outputs()`, which scopes `candidate_comparison.json` to one selected candidate and writes `current_vs_candidate.json` without writing Block 9+ artifacts.
- [x] 2026-06-05: Session 04 added `run_compare_variants.py --block8-only --candidate ID` as the CLI mode for the same boundary while preserving the existing all-in-one comparison package for old callers.
- [x] 2026-06-05: Session 04 added `tests/test_block8_current_vs_candidate_boundary.py` proving stale `decision_verdict.json` is not refreshed or treated as current, and Action Plan / Decision Journal / AI Commentary context are not written by the Block 8-only path.
- [x] 2026-06-05: Session 04 also tightened `current_vs_candidate.json` selection semantics: requested ids are preserved in `requested_candidate_ids`, while `selected_candidate_ids` includes only live comparison rows so unavailable requested candidates are not treated as current comparison evidence.
- [x] 2026-06-05: Session 04 ran `tests/test_block8_current_vs_candidate_boundary.py tests/test_current_vs_candidate.py`. Result: 6 passed in 2.11 seconds.
- [x] 2026-06-05: Session 04 ran Python compilation for `src/candidate_comparison.py`, `src/current_vs_candidate.py`, and `run_compare_variants.py`, plus `scripts/verify_docs.py`. Result: both passed.
- [ ] 2026-06-05: Session 04 adjacent `tests/test_candidate_comparison.py tests/test_candidate_comparison_contract.py` was not clean: 45 passed and 1 failed (`test_current_unavailable_in_optimize_mode`, expected `current` unavailable but got `degraded`). This failure is in pre-existing `build_candidate_comparison()` current-row behavior, not in the new Block 8-only helper, and remains unresolved in this session.
- [x] 2026-06-05: Session 05 expanded `src/current_vs_candidate.py` so each live comparison row now carries trade-off summaries, unavailable metric flags, risk reduced/added groupings, practicality/turnover/cost fields, success-criteria evaluation, and materiality for decision review.
- [x] 2026-06-05: Session 05 wired the Block 8-only helper to pass the in-memory `candidate_generation.json` document into the Current-vs-Candidate adapter, so selected-candidate success criteria, weights, and transaction-cost assumptions can be used without reading downstream verdict artifacts.
- [x] 2026-06-05: Session 05 added focused tests for the expanded Block 8 contract, success criteria, and practicality/trade-off handling.
- [x] 2026-06-05: Session 05 updated `docs/specs/current_vs_candidate_spec.md` to document the expanded content contract and no-fake-metrics behavior.
- [x] 2026-06-05: Session 05 ran focused verification: `tests/test_current_vs_candidate.py tests/test_current_vs_candidate_comparison_contract.py tests/test_current_vs_candidate_success_criteria.py tests/test_current_vs_candidate_tradeoffs.py tests/test_block8_current_vs_candidate_boundary.py` passed with 12 tests; `tests/test_block_5_decision_compare_contract.py tests/test_decision_verdict.py` passed with 10 tests; Python compilation and `scripts/verify_docs.py` passed.
- [x] 2026-06-05: Session 06 added `build_decision_verdict_from_block7_8()` so Block 9 can consume `candidate_generation.json` and `current_vs_candidate.json` directly without advanced Selection Engine ranking.
- [x] 2026-06-05: Session 06 covered failed/infeasible candidates, insufficient data quality, insufficient optimizer/method quality, no material rebalance, keep-current/no-trade, material rebalance review, test-another-candidate, and risk-improved-but-turnover-too-high outcomes.
- [x] 2026-06-05: Session 06 added the planned focused test files for the direct Block 9 contract and ran the first focused verdict bundle before docs sync: 15 passed.
- [x] 2026-06-05: Session 06 synced `docs/specs/decision_verdict_spec.md`, `docs/specs/README.md`, `SPEC.md`, `DECISIONS.md`, and `CHANGELOG.md` for the direct Block 7/8 verdict builder.
- [x] 2026-06-05: Session 06 final focused verification passed: `tests/test_block_5_decision_compare_contract.py tests/test_decision_verdict.py tests/test_decision_verdict_contract.py tests/test_decision_verdict_no_trade.py tests/test_decision_verdict_rebalance_when_material.py tests/test_decision_verdict_evidence_insufficient.py tests/test_decision_verdict_failed_candidate.py` produced 21 passed in 15.78 seconds; `py_compile src/decision_verdict.py` passed; `scripts/verify_docs.py` passed.
- [x] 2026-06-05: Session 07 added `candidate_generation.json` to the AI Commentary grounding allowlist and `source_artifacts` map.
- [x] 2026-06-05: Session 07 expanded `src/ai_commentary_context.py` references for Block 7 hypothesis/candidate evidence, Block 8 improvements/deteriorations/turnover/cost/success criteria, and Block 9 verdict/no-trade rationale.
- [x] 2026-06-05: Session 07 allowed post-compare AI grounding for the direct vertical path when `candidate_generation.json`, `current_vs_candidate.json`, and `decision_verdict.json` are present without requiring `selection_decision.json`.
- [x] 2026-06-05: Session 07 updated `tests/test_ai_commentary_context.py` for the direct Block 7/8/9 grounding path and ran the focused AI grounding test file. Result: 13 passed in 5.98 seconds.
- [x] 2026-06-05: Session 07 synced `docs/specs/ai_commentary_grounding_spec.md`, `OUTPUTS.md`, `SPEC.md`, `DECISIONS.md`, `CHANGELOG.md`, and this ExecPlan.
- [x] 2026-06-05: Session 07 final verification passed: `py_compile src/ai_commentary_context.py src/candidate_comparison.py`, `tests/test_ai_commentary_context.py tests/test_current_vs_candidate.py tests/test_decision_verdict.py` (23 passed in 7.24 seconds), and `scripts/verify_docs.py`.
- [x] 2026-06-05: Session 08 added `scripts/run_blocks_5_to_9_vertical_flow.py` as the one-command Blocks 5-9 vertical demo.
- [x] 2026-06-05: Session 08 wired the script to run diagnosis-only review, rebuild one selected Builder setup, generate one candidate attempt, run Block 8-only scoped comparison, write direct Block 9 verdict, and write AI Commentary grounding.
- [x] 2026-06-05: Session 08 default card selection now prefers reference or mixed-evidence Launchpad cards and tests Equal Weight first, while still allowing explicit card/method/preset overrides.
- [x] 2026-06-05: Session 08 added runtime hygiene that clears stale root vertical-loop artifacts, including stale `candidate_factory_run.json`, before the one-candidate generation step.
- [x] 2026-06-05: Session 08 added focused tests for one-command orchestration, reference-card preference, targeted fallback, and data-quality blocker behavior.
- [x] 2026-06-05: Session 08 verification passed: Python compilation for the new script and adjacent Block 7/8/9/AI modules; focused and adjacent pytest bundle produced 29 passed in 6.52 seconds; `scripts/verify_docs.py` passed; `scripts/run_blocks_5_to_9_vertical_flow.py --help` printed the expected CLI options.
- [x] 2026-06-05: Session 09 synchronized product wording across `README.md`, `docs/runtime_entrypoints.md`, `docs/product_flow_operator_guide.md`, `PRODUCT.md`, `ARCHITECTURE.md`, `OUTPUTS.md`, `docs/specs/README.md`, `DECISIONS.md`, `CHANGELOG.md`, and `docs/exec_plans/README.md`.
- [x] 2026-06-05: Session 09 documented the required boundaries: Builder setup is not a candidate, Candidate Generation is not a recommendation, reference tests are diagnostic comparisons, Decision Verdict evaluates action/no-action, and no-trade/evidence-insufficient are valid outcomes.
- [x] 2026-06-05: Session 10 ran the focused live-acceptance pytest bundles for Block 7 Candidate Generation, Block 8 Current-vs-Candidate, Block 9 Decision Verdict, and the vertical-flow/reference demo tests. Result: 18 + 6 + 11 + 2 tests passed.
- [x] 2026-06-05: Session 10 ran `scripts/verify_docs.py`. Result: passed.
- [x] 2026-06-05: Session 10 ran the real one-command vertical demo, `scripts/run_blocks_5_to_9_vertical_flow.py --method equal_weight`. Result: completed successfully after allowing a longer runtime budget for the diagnosis-only stage.
- [x] 2026-06-05: Session 10 verified that the live run produced all required closure artifacts: `problem_classification.json`, `candidate_launchpad.json`, `portfolio_alternatives_builder.json`, `candidate_generation.json`, `current_vs_candidate.json`, `decision_verdict.json`, and `ai_commentary_context.json`.
- [x] 2026-06-05: Session 10 closed the whole Blocks 5-9 vertical product loop plan as `READY_FOR_PRODUCT_DEMO`.

## Surprises & Discoveries


- Observation: The existing Block 6 `CandidateSetup` did not carry `hypothesis_to_test` or Launchpad card type even though Session 02 requires Block 7 to preserve those fields in the candidate object.
  Evidence: Session 02 added `source_launchpad_card_type` and `hypothesis_to_test` to `CANDIDATE_SETUP_REQUIRED_FIELDS` and `_candidate_setup_from_validated_setup()` before building `candidate_generation.json`.

- Observation: The existing candidate factory can leave or reuse `weights.json` under candidate artifact folders, so Block 7 runtime must trust the current factory step status before reading weights.
  Evidence: Session 03 tests create a stale `weights.json` next to a failed factory step; `candidate_generation.json` remains `failed`, keeps `weights: null`, and blocks comparison.


- Observation: Before Session 00, the working tree already contained many modified and untracked Block 6-related files, including `src/portfolio_alternatives_builder.py`, `src/block_4/diagnosis_builder.py`, Block 6 tests, and `docs/exec_plans/block_6_builder_exec_plan.md`.
  Evidence: initial `git status --short` in Session 00 showed those files before this ExecPlan file was created. Future sessions must not treat those files as changes made by this plan unless they intentionally edit them later.

- Observation: The literal command `.\.venv\Scripts\python.exe -m pytest tests\test_block_6_*.py ...` does not expand the wildcard when passed through PowerShell to pytest in this workspace.
  Evidence: pytest returned `ERROR: file or directory not found: tests\test_block_6_*.py` and `no tests ran`. The equivalent PowerShell-expanded command using `Get-ChildItem -Filter 'test_block_6_*.py'` passed with 63 tests.

- Observation: The same wildcard behavior applies to `tests\test_candidate_generation_*.py`.
  Evidence: Session 03's literal wildcard pytest command returned `ERROR: file or directory not found`; the PowerShell-expanded command using `Get-ChildItem -Filter 'test_candidate_generation_*.py'` passed with 18 tests.

- Observation: The adjacent candidate-comparison suite currently has a failing current-row expectation unrelated to the Session 04 helper.
  Evidence: Session 04 ran `.\.venv\Scripts\python.exe -m pytest tests\test_candidate_comparison.py tests\test_candidate_comparison_contract.py -q`; result was 45 passed and 1 failed in `test_current_unavailable_in_optimize_mode`, where `build_candidate_comparison()` emitted `current.status == degraded` instead of the expected `unavailable`.

- Observation: `candidate_comparison.json` rows do not always carry baseline and candidate weights, and many comparison rows do not carry concentration or factor evidence.
  Evidence: Session 05 keeps `turnover_required.status = unavailable` when baseline or candidate weights are missing and marks missing concentration/factor dimensions with `status: unavailable` instead of inventing values.

- Observation: Success criteria are plain-language card text, not a formal rules engine.
  Evidence: Session 05 maps only simple criteria to existing metrics such as stress loss, drawdown, volatility, return, Sharpe, concentration, risk contribution, and beta; unmapped criteria are `not_evaluated`, and mapped-but-missing criteria are `unavailable`.

- Observation: The existing Decision Verdict validator still expects Selection Engine-compatible `selection_decision_status` values.
  Evidence: Session 06 direct Block 7/8 verdict builder maps vertical-loop outcomes back to `selected_candidate`, `no_material_rebalance`, `inconclusive`, or `data_review_required` while adding `verdict_reason_id` and `evidence_summary` for product-specific reasons.

- Observation: AI Commentary grounding was still oriented around the legacy comparison flow, where Selection evidence is expected.
  Evidence: Before Session 07, `src/ai_commentary_context.py` allowed `selection_decision.json` but not `candidate_generation.json`, and the post-compare phase required Selection evidence even though Session 06 made `selection_decision.json` optional for the direct Block 7/8 verdict path.

- Observation: A stale `candidate_factory_run.json` can describe a previous candidate menu even after a fresh diagnosis-only review.
  Evidence: Session 08 deletes root vertical-loop artifacts, including `candidate_factory_run.json`, before generating the selected candidate so the one-command demo cannot accidentally treat an old factory menu as current product evidence.

- Observation: Some operator-facing docs still named `run_portfolio_review.py --candidates equal_weight` as the recommended product demo even after the Session 08 vertical-flow script existed.
  Evidence: Session 09 changed README/runtime/operator docs so `scripts/run_blocks_5_to_9_vertical_flow.py --method equal_weight` is the canonical Blocks 5-9 demo, while `run_portfolio_review.py --candidates <id>` is described as a factory-id compatibility path.

- Observation: The live acceptance command can exceed a short five-minute tool timeout even when it is not broken.
  Evidence: Session 10's first `scripts/run_blocks_5_to_9_vertical_flow.py --method equal_weight` attempt timed out at roughly 304 seconds while the diagnosis-only review was still running. Running the diagnosis-only command directly showed it completed successfully in about 547 seconds with FRED/factor timeout warnings and cached data fallbacks. Re-running the vertical flow with a longer runtime budget completed successfully in about 651 seconds.

- Observation: A diagnosis-only timeout attempt can leave non-authoritative no-candidate root tombstones before the real vertical run completes.
  Evidence: After the first timed-out Session 10 attempt, root `current_vs_candidate.json` and `decision_verdict.json` were diagnosis-only tombstones with `artifact_status: not_authoritative`, and `candidate_generation.json` was missing. The plan was not marked accepted until the later successful run produced the real Block 7/8/9/AI artifacts.

- Observation: Markdown code formatting around planned future Python files causes `scripts/verify_docs.py` to treat them as broken local links before those sessions create the files.
  Evidence: the first docs verification failed on planned future paths such as the candidate generation module and future tests. Rewording those future paths without markdown-code local-reference syntax made docs verification pass without changing verifier logic.

- Observation: Existing Block 6 tests used backend engine ids such as `minimum_cvar_constrained` and advanced methods such as Robust MV as guided Builder options.
  Evidence: Session 01 updated the tests and product validator allowlist to use the product-facing `minimum_cvar` id and hide Robust MV / Robust Scenario from the guided path.

## Decision Log


- Decision: Session 02 implements the Block 7 contract and JSON writer, but does not wire a runtime optimizer/factory script yet.
  Rationale: The accepted plan assigns default input/output script behavior and failed/infeasible runtime handling to Session 03. Session 02 should establish the schema, one-attempt boundary, method mapping, and recommendation guardrails first.
  Date/Author: 2026-06-05 / Codex.

- Decision: Session 03 uses factory `--execution-mode fast` and does not pass `--then-compare`.
  Rationale: Block 7 should generate or record one candidate attempt only. Fast mode produces candidate weights through existing plumbing while keeping comparison and verdict work for later Blocks 8 and 9.
  Date/Author: 2026-06-05 / Codex.

- Decision: Session 04 implements Block 8 as a separate helper and CLI mode instead of adding flags to the existing all-in-one writer.
  Rationale: Existing callers depend on `write_candidate_comparison_outputs()` producing the legacy/backend decision package. A separate Block 8-only boundary avoids silently changing old behavior while giving the vertical product loop a no-verdict compare path.
  Date/Author: 2026-06-05 / Codex.

- Decision: Session 05 keeps materiality-for-decision-review inside `current_vs_candidate.json` as a review gate, not as a recommendation.
  Rationale: Block 8 should answer whether the evidence is worth decision review, while Block 9 remains responsible for action/no-action/evidence-insufficient verdicts.
  Date/Author: 2026-06-05 / Codex.

- Decision: Session 05 uses explicit unavailable statuses for missing turnover, concentration, factor, and success-criteria evidence.
  Rationale: The product contract says not to fake success or invent values. Unavailable evidence is safer and more useful for Block 9 than silent assumptions.
  Date/Author: 2026-06-05 / Codex.

- Decision: Session 06 keeps the existing `decision_verdict_v1` status vocabulary but adds direct Block 7/8 evidence fields.
  Rationale: Existing validators, AI grounding, monitoring, and product-bundle checks already understand the current verdict ids and Selection-compatible statuses. Adding `verdict_reason_id`, `reviewed_candidate_id`, and `evidence_summary` gives the vertical product loop Block 9 semantics without forcing a schema rename or breaking older Selection Engine callers.
  Date/Author: 2026-06-05 / Codex.

- Decision: Session 06 treats high turnover as a no-trade reason even when risk metrics improve.
  Rationale: The current product is decision support, not automatic rebalancing. A risk improvement that requires high turnover or high estimated cost should be visible as a trade-off and can legitimately produce "keep current portfolio" instead of a rebalance verdict.
  Date/Author: 2026-06-05 / Codex.

- Decision: Session 07 treats `candidate_generation.json` as a first-class AI Commentary grounding source for the direct vertical loop.
  Rationale: The tested hypothesis, generated candidate method, setup source, success criteria, and comparison handoff live in Block 7, not in the Selection Engine artifact. The AI grounding layer must cite that evidence directly while remaining deterministic and non-recommendational.
  Date/Author: 2026-06-05 / Codex.

- Decision: Session 08 implements the product demo as a dedicated one-command wrapper instead of reusing the backend batch review flags.
  Rationale: `run_portfolio_review.py --with-candidates` and `--mode full` are backend/research batch paths. The product demo needs the narrower `Diagnosis -> Hypothesis -> Candidate -> Comparison -> Verdict` loop with one selected Launchpad card, one candidate attempt, scoped Block 8 evidence, and direct Block 9 verdict.
  Date/Author: 2026-06-05 / Codex.

- Decision: Failed and infeasible factory steps take precedence over any existing candidate `weights.json`.
  Rationale: This avoids silent fallback to stale generated artifacts and preserves the product boundary that a failed/infeasible candidate is not comparable and not a rebalance recommendation.
  Date/Author: 2026-06-05 / Codex.


- Decision: This plan starts with a narrow Session 00 gate and stops after that session.
  Rationale: The user explicitly requested that the implementer begin with Session 00, then stop and report when it completes. The previous Block 6 ExecPlan also recorded that final live proof was not completed, so beginning Block 7 immediately would risk building on an unverified handoff.
  Date/Author: 2026-06-05 / Codex.

- Decision: The product path remains one selected hypothesis by default.
  Rationale: The product principle is diagnosis-first decision support. Multi-candidate ranking, optimizer menus, robust research suites, and scorecard-first framing are advanced or legacy support, not the current vertical MVP.
  Date/Author: 2026-06-05 / Codex.

- Decision: Block 6 MVP method scope is limited to Equal Weight, Risk Parity, Hierarchical Risk Parity, Minimum Variance, Minimum CVaR, and Maximum Diversification, with capped and uncapped modes.
  Rationale: These methods cover the three MVP scenarios: simple reference test, diversification/concentration test, and crisis/tail-risk test. Advanced/legacy optimizers should remain hidden from the guided product path until the one-candidate flow is stable.
  Date/Author: 2026-06-05 / Codex.

- Decision: Use `minimum_cvar` as the guided product method id, then map it to `minimum_cvar_constrained` or `minimum_cvar_uncapped` only at backend delegation time.
  Rationale: The guided Builder should expose a product concept, not backend engine suffixes. Mode owns the capped/uncapped distinction.
  Date/Author: 2026-06-05 / Codex.

- Decision: Session 10 accepts `evidence_insufficient` as a successful live demo verdict when all required artifacts are produced.
  Rationale: The product contract explicitly allows evidence-insufficient outcomes. The closure gate is the end-to-end artifact chain and honest Decision Verdict, not a forced rebalance recommendation.
  Date/Author: 2026-06-05 / Codex.

## Outcomes & Retrospective

Session 00 is closed successfully. The ExecPlan file and plan register were updated. The focused Block 6 test gate passed after expanding the wildcard in PowerShell. Documentation verification passed after rewording future file paths so they are not treated as missing links. `run_portfolio_review.py --dry-run` passed and confirmed the default workflow remains diagnosis-only with candidates disabled. The next chat should start Session 01 and must not assume product-demo readiness.

Session 00 status: `BLOCK_6_READY_FOR_NEXT_SESSION`.

Session 01 is closed successfully. Guided Block 6 no longer exposes the raw optimizer menu: the product method set is Equal Weight, Risk Parity, Hierarchical Risk Parity, Minimum Variance, Minimum CVaR, and Maximum Diversification. Capped/uncapped mode handling and conservative/balanced/aggressive/basic-reference/custom/uncapped presets are implemented. Uncapped setup keeps `max_asset_weight: null`, `min_asset_weight: 0.0`, `capped: false`, and the required concentration warning. Block 6 still writes setup only: no weights, no candidate generation, no comparison, and no verdict.

Session 01 status: `BLOCK_6_MVP_METHODS_READY_FOR_NEXT_SESSION`.

Session 02 is closed successfully at the contract layer. `candidate_generation_v1` now creates exactly one candidate attempt from a validated `CandidateSetup`, maps guided method/mode to one backend candidate variant, preserves diagnosis/card/setup context, copies weights when supplied, carries failed/infeasible reason fields, and keeps `is_rebalance_recommendation: false`. The writer materializes `candidate_generation.json` under the requested output directory. Runtime script wiring and real factory failure/infeasible handling were deferred to Session 03 and are now complete.

Session 02 status: `BLOCK_7_CONTRACT_READY_FOR_NEXT_SESSION`.

Session 03 is closed successfully at the runtime boundary. `scripts/generate_candidate_from_builder_setup.py` reads the default Builder artifact, delegates one backend candidate through the existing factory in weights-only fast mode, writes the default `candidate_generation.json`, and does not write comparison or verdict artifacts. Failed and infeasible factory evidence is preserved in the Block 7 artifact, stale weights are ignored for failed/infeasible current steps, `is_rebalance_recommendation` remains false, and `handoff_to_comparison.can_compare` is false unless weights are available from a successful/reused current factory step.

Session 03 status: `BLOCK_7_RUNTIME_READY_FOR_NEXT_SESSION`.

Session 04 is closed at the Block 8 boundary. The new Block 8-only helper and CLI mode scope `candidate_comparison.json` to one selected candidate and write `current_vs_candidate.json` without writing or refreshing `decision_verdict.json`, `action_plan.json`, `decision_journal.json`, or `ai_commentary_context.json`. The focused boundary test passed and verifies that an existing stale verdict remains ignored rather than current. Documentation verification and Python compilation passed. One adjacent candidate-comparison suite still has an unrelated current-row expectation failure and was recorded above.

Session 04 status: `BLOCK_8_BOUNDARY_READY_WITH_ADJACENT_TEST_NOTE`.

Session 05 is closed successfully for Block 8 content. `current_vs_candidate.json` now gives a product-readable trade-off comparison for the selected candidate: what improved, what worsened, what stayed similar, what risk was reduced or added, practicality/turnover/cost evidence, success-criteria evaluation, unavailable metric disclosure, and whether the evidence is material enough for decision review. This remains diagnostic only and does not create a verdict or recommendation. Focused current-vs-candidate tests, Block 8 boundary tests, Block 5 compare/verdict contract tests, Python compilation, and docs verification passed.

Session 05 status: `BLOCK_8_CONTENT_READY_FOR_NEXT_SESSION`.

Session 06 is closed successfully for Block 9 contract implementation. `decision_verdict.json` can now be built directly from Block 7 `candidate_generation.json` and Block 8 `current_vs_candidate.json` evidence without using advanced Selection Engine ranking. The direct builder supports evidence-insufficient outcomes for missing, failed, infeasible, degraded, or non-comparable candidates; no-trade / keep-current outcomes for non-material or failed-hypothesis candidates; a material rebalance-review verdict for one selected candidate; a test-another-candidate outcome for inconclusive evidence; and a risk-improved-but-turnover-too-high no-trade outcome. The existing Selection Engine mapping remains compatible for old callers. Focused verdict verification passed with 21 tests; Python compilation and documentation verification also passed.

Session 06 status: `BLOCK_9_VERDICT_CONTRACT_READY_FOR_NEXT_SESSION`.

Session 07 is closed successfully for AI Commentary grounding. `ai_commentary_context.json` can now cite `candidate_generation.json` as an allowed source, carry direct Block 7/8/9 evidence without requiring Selection Engine artifacts, and expose grounding topics for diagnosis, hypothesis tested, candidate generated, improvements, deteriorations, turnover/cost, success-criteria result, Decision Verdict, no-trade rationale, and monitoring trigger. This remains deterministic grounding only: no LLM call, no new metrics, no verdict creation, and no trade instructions. Focused and adjacent adapter tests passed with 23 tests; Python compilation and docs verification passed.

Session 07 status: `AI_COMMENTARY_GROUNDING_READY_FOR_NEXT_SESSION`.

Session 08 is closed successfully for the one-command vertical demo contract. `scripts/run_blocks_5_to_9_vertical_flow.py` now runs diagnosis-only review, selects one Launchpad card, rebuilds one Builder setup, generates one Block 7 candidate attempt, runs Block 8-only scoped current-vs-candidate comparison, writes the direct Block 9 verdict, and writes deterministic AI Commentary grounding. The default demo prefers reference or mixed-evidence cards and tests Equal Weight first. The script clears stale root vertical-loop artifacts before generation so an old candidate zoo or stale verdict is not treated as current evidence. Focused Session 08 tests passed.

Session 08 status: `ONE_COMMAND_VERTICAL_DEMO_READY_FOR_DOC_SYNC_SESSION`.

Session 09 is closed successfully for documentation sync and product wording. The docs now consistently route the canonical Blocks 5-9 demo through `scripts/run_blocks_5_to_9_vertical_flow.py --method equal_weight`, document the full product-bundle chain including `portfolio_alternatives_builder.json` and `candidate_generation.json`, and preserve the safety boundaries that Builder setup is not a candidate, generated candidates are not recommendations, reference tests are diagnostic comparisons, Decision Verdict owns action/no-action, and no-trade/evidence-insufficient are valid verdicts. This session did not run live acceptance; Session 10 still owns the real vertical demo proof.

Session 09 status: `DOC_SYNC_READY_FOR_LIVE_ACCEPTANCE_SESSION`.

Session 10 is closed successfully for live acceptance and plan closure. Focused pytest bundles passed for Candidate Generation, Current-vs-Candidate, Decision Verdict, and the vertical-flow/reference demo tests. Documentation verification passed. The real vertical product demo completed with `scripts/run_blocks_5_to_9_vertical_flow.py --method equal_weight`, selected `launchpad_01_compare_against_simple_benchmark`, generated the `equal_weight` candidate attempt, wrote one scoped Block 8 comparison, wrote a direct Block 9 verdict, and wrote deterministic AI Commentary grounding. The live run produced all required artifacts: `Main portfolio/analysis_subject/problem_classification.json`, `Main portfolio/analysis_subject/candidate_launchpad.json`, `Main portfolio/analysis_subject/portfolio_alternatives_builder.json`, `Main portfolio/candidate_generation.json`, `Main portfolio/current_vs_candidate.json`, `Main portfolio/decision_verdict.json`, and `Main portfolio/ai_commentary_context.json`. The verdict was `evidence_insufficient`, which is an accepted honest outcome under the plan and product contract.

Session 10 status: `BLOCK_6_READY BLOCK_7_READY BLOCK_8_READY BLOCK_9_READY READY_FOR_PRODUCT_DEMO`.

## Context and Orientation

Portfolio MRI / Portfolio X-Ray is a Python CLI/file-driven portfolio diagnostics system moving toward the product truth called `Р”РРђР“РќРћРЎРўРРљРђ 2`. Current product direction is diagnosis-first, current-portfolio-first, and decision-support-first. It must not become optimizer-first, scorecard-first, or a black-box portfolio recommender.

The current canonical blocks for this plan are:

- Blocks 1-3: Portfolio Evidence Engine.
- Block 4: Diagnosis Engine.
- Block 5: Hypothesis Launchpad.
- Block 6: Hypothesis Builder / Builder Setup.
- Block 7: Candidate Generator.
- Block 8: Trade-off Comparison.
- Block 9: Decision Verdict.
- Block 10: AI Commentary / Monitoring later.

The repository already contains Block 4 / 5 / 6 code and contracts:

- `src/block_4/diagnosis_builder.py` writes Problem Classification, Candidate Launchpad, and currently wires Block 6 Builder setup.
- `src/portfolio_alternatives_builder.py` owns Block 6 `BuilderPrefill`, simple setup, validation, and `CandidateSetup`.
- `docs/specs/portfolio_alternatives_builder_spec.md`, `docs/specs/builder_prefill_spec.md`, and `docs/specs/candidate_setup_spec.md` own Block 6 documentation.
- At this plan's start, `docs/exec_plans/block_6_builder_exec_plan.md` was the Block 6 handoff plan and reported that final live smoke proof had timed out, so Session 00 checked Block 6 readiness before downstream work.

The repository also contains older backend comparison and verdict support:

- `src/candidate_factory.py` orchestrates legacy/back-end candidate generation and can run explicit candidate ids.
- `src/candidate_comparison.py` builds `candidate_comparison.json` and currently can also write downstream support artifacts.
- `src/current_vs_candidate.py` writes the current product-facing comparison adapter, but it is still thin compared with the requested Block 8 trade-off comparison.
- `src/decision_verdict.py` maps existing Selection Engine outputs into product-facing verdict language; this plan turns Block 9 into a direct verdict over the new Block 7/8 artifacts.
- `src/ai_commentary_context.py` writes deterministic grounding for future AI commentary. It does not call an LLM.

Generated outputs are not source. Routine generated folders such as `Main portfolio/`, `output/`, `cache/`, candidate portfolio folders, and PDF/report outputs must not be committed unless a task explicitly targets generated artifacts.

## Plan of Work

This section describes all sessions. Each session is intended to run in a separate Codex chat. Session 00 must run first and must stop after it completes.

### Session 00 - Save ExecPlan and close Block 6 gate

Start here and only here. Create this file at `docs/exec_plans/2026-06-05_blocks_5_9_vertical_product_loop_plan.md`, update `docs/exec_plans/README.md` so this file is the active plan, inspect the dirty tree, and run the Block 6 readiness gate. Do not implement Block 7 in this session.

Run from the repository root:

    .\.venv\Scripts\python.exe -m pytest tests\test_block_6_*.py tests\test_portfolio_alternatives_builder.py tests\test_candidate_launchpad_builder_handoff.py -q
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    .\.venv\Scripts\python.exe run_portfolio_review.py --dry-run

If these pass, record `BLOCK_6_READY_FOR_NEXT_SESSION` in the outcomes for Session 00 and stop. If they fail, record the failure and stop with a blocker. Do not proceed to Session 01 in the same chat.

### Session 01 - Block 6 MVP methods, modes, and presets

Normalize the guided Block 6 product path. The Block 6 guided method allowlist must match the MVP scope: Equal Weight, Risk Parity, Hierarchical Risk Parity, Minimum Variance, Minimum CVaR, and Maximum Diversification. The two supported modes are `capped` and `uncapped`. The only user-adjustable optimization fields in the MVP are `min_asset_weight` and `max_asset_weight`.

The constraint presets are:

- Conservative: `min_asset_weight = 0%`, `max_asset_weight = 15%`, capped.
- Balanced: `min_asset_weight = 0%`, `max_asset_weight = 20%`, capped.
- Aggressive: `min_asset_weight = 0%`, `max_asset_weight = 30%`, capped.
- Basic reference: for Equal Weight / Risk Parity diagnostic reference tests only.
- Custom: only `min_asset_weight` and `max_asset_weight`.
- Uncapped: `min_asset_weight = 0%`, `max_asset_weight = null`, `capped = false`.

Minimum Variance, Minimum CVaR, and Maximum Diversification must map to constrained/current capped engines in capped mode and uncapped engines in uncapped mode. Uncapped mode must always carry this warning:

    Uncapped mode may create concentrated portfolios. Use only for diagnostic comparison, not as an automatic rebalance recommendation.

Hide Equal Weight by Asset Class, Risk Budget by Asset, Risk Budget by Asset Class, Minimum Variance Advanced Controls, Robust Mean-Variance, Scenario-Based Robust Optimization, and Legacy Policy Optimizer from the guided product path. They may remain available in code as `advanced_hidden`, `legacy_supported`, or equivalent non-guided classifications.

Acceptance for Session 01: Block 6 method allowlist matches MVP scope, advanced/legacy optimizers remain hidden from the guided product path, uncapped mode always carries the concentration warning, and Block 6 remains setup-only with no weights, no candidate generation, no comparison, and no verdict.

### Session 02 - Block 7 Candidate Generator contract

Add the planned module named src/candidate_generation.py. Block 7 reads a validated `CandidateSetup`, verifies `can_generate_candidate == true`, creates exactly one candidate attempt, and writes `{output_dir_final}/candidate_generation.json`.

The new artifact schema is `candidate_generation_v1`. It must contain top-level `candidate`, `generation_status`, `source_builder_setup`, `method_availability`, `warnings`, and `handoff_to_comparison`.

The candidate object must preserve: `candidate_id`, `candidate_name`, `source_card_id`, `source_diagnosis_id`, `source_launchpad_card_type`, `source_builder_setup_id` or `candidate_setup_id`, `goal`, `hypothesis_to_test`, `method`, `method_variant`, `capped`, `uncapped`, `min_asset_weight`, `max_asset_weight`, `constraint_preset`, `parameters`, `constraints`, `weights`, `status`, failure or infeasibility reason, `success_criteria`, `tradeoff_to_watch`, `decision_boundary`, `is_rebalance_recommendation = false`, and `generation_source = block_6_builder_setup`.

Tests to add or update in future sessions:

- planned test file tests/test_candidate_generation_from_builder_setup.py
- planned test file tests/test_candidate_generation_method_mapping.py
- planned test file tests/test_candidate_generation_no_recommendation_boundary.py

### Session 03 - Block 7 runtime and failure/infeasible handling

Session 03 added scripts/generate_candidate_from_builder_setup.py. Its default input is `Main portfolio/analysis_subject/portfolio_alternatives_builder.json`, and its default output is `Main portfolio/candidate_generation.json`.

If the existing factory or optimizer plumbing fails or proves infeasible, Block 7 must save the attempt as `failed` or `infeasible`, preserve source diagnosis/method/parameters/failure reason, avoid silent fallback, and set `handoff_to_comparison.can_compare = false`.

Tests added or updated in Session 03:

- tests/test_candidate_generation_failed_infeasible.py
- a stale-artifact regression proving failed/infeasible candidate attempts do not become rebalance recommendations.

### Session 04 - Block 8 boundary: comparison without verdict

Add a product vertical helper or mode that builds/scopes `candidate_comparison.json` to the selected candidate and writes only Block 8 `current_vs_candidate.json`. This mode must not write `decision_verdict.json`, Action Plan, Decision Journal, or post-verdict AI context.

Keep the existing legacy/back-end all-in-one comparison package compatible for old callers. The new path is for the vertical product loop.

Acceptance for Session 04: a test proves that after the Block 8-only helper runs, no new verdict is written and no stale verdict is treated as current.

### Session 05 - Block 8 Trade-off Comparison content

Session 05 expanded `src/current_vs_candidate.py` so `current_vs_candidate.json` answers what improved, what worsened, what stayed similar, what risk was reduced, what risk was added, turnover required, transaction-cost assumption, success-criteria result, and whether improvement is material enough for decision review.

Compare available evidence across risk/return, stress, concentration, factor behavior, and practicality. If a metric is unavailable, mark the criterion or metric unavailable. Do not fake success and do not invent a value.

Tests added or covered in Session 05:

- tests/test_current_vs_candidate_comparison_contract.py
- tests/test_current_vs_candidate_success_criteria.py
- tests/test_current_vs_candidate_tradeoffs.py
- tests/test_block8_current_vs_candidate_boundary.py covers stale downstream artifact behavior for the Block 8-only path.

### Session 06 - Block 9 Decision Verdict

Session 06 expanded `src/decision_verdict.py` with a builder that consumes Block 7 and Block 8 evidence directly. It covers failed or infeasible candidates, insufficient data quality, insufficient optimizer/method quality, no material rebalance, keep current portfolio, rebalance to selected candidate, test another candidate, and risk improved but turnover too high.

No-trade is a valid outcome. Evidence insufficient is a valid outcome. The verdict must not say `best portfolio` and must not hide trade-offs.

Tests added in Session 06:

- tests/test_decision_verdict_contract.py
- tests/test_decision_verdict_no_trade.py
- tests/test_decision_verdict_rebalance_when_material.py
- tests/test_decision_verdict_evidence_insufficient.py
- tests/test_decision_verdict_failed_candidate.py

### Session 07 - AI Commentary grounding update

Update `src/ai_commentary_context.py` so `candidate_generation.json` is an allowed source artifact. Add grounding topics for diagnosis, hypothesis tested, candidate generated, improvements, deteriorations, turnover/cost, success criteria result, decision verdict, no-trade rationale, and monitoring trigger.

This remains deterministic grounding only. It must not call an LLM, calculate new metrics, invent data, create a verdict, or provide trade execution instructions.

Run or update:

- `tests/test_ai_commentary_context.py`

### Session 08 - One-command vertical demo and hygiene

Add the planned script named scripts/run_blocks_5_to_9_vertical_flow.py. It should run diagnosis-only review, read the primary Builder setup, optionally override method or preset, generate one candidate, compare current versus that candidate, build the verdict, and write AI context.

The default demo should prefer a reference or mixed-evidence card when available and generate Equal Weight first. Runtime hygiene must ensure the default run does not create a candidate zoo, diagnosis-only does not leave authoritative stale downstream artifacts, and one-candidate mode scopes to one selected candidate.

Tests to add or update in future sessions:

- planned test file tests/test_blocks_5_to_9_vertical_flow.py
- planned test file tests/test_reference_benchmark_vertical_flow.py
- planned test file tests/test_targeted_hypothesis_vertical_flow.py
- planned test file tests/test_data_quality_blocks_generation.py

### Session 09 - Documentation sync and product wording

Update the owning specs and docs, including `docs/specs/`, `docs/runtime_entrypoints.md`, product workflow docs, `OUTPUTS.md` or any explicit output-contract doc, `DECISIONS.md`, `CHANGELOG.md`, `README.md`, and `docs/exec_plans/README.md`.

Docs must state: Builder setup is not a candidate, Candidate is not a recommendation, reference tests are diagnostic comparisons rather than rebalance recommendations, Decision Verdict is where action/no-action is evaluated, and no-trade/evidence-insufficient are valid outcomes.

### Session 10 - Live acceptance and closure

Run from the repository root:

    .\.venv\Scripts\python.exe -m pytest tests\test_candidate_generation_*.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_current_vs_candidate_*.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_decision_verdict_*.py -q
    .\.venv\Scripts\python.exe -m pytest tests\test_blocks_5_to_9_vertical_flow.py tests\test_reference_benchmark_vertical_flow.py -q
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    .\.venv\Scripts\python.exe scripts\run_blocks_5_to_9_vertical_flow.py --method equal_weight

Only mark `READY_FOR_PRODUCT_DEMO` if a real run produces `problem_classification.json`, `candidate_launchpad.json`, `portfolio_alternatives_builder.json`, `candidate_generation.json`, `current_vs_candidate.json`, `decision_verdict.json`, and `ai_commentary_context.json`.

The final status line may be recorded only when true:

    BLOCK_6_READY BLOCK_7_READY BLOCK_8_READY BLOCK_9_READY READY_FOR_PRODUCT_DEMO

## Concrete Steps

For Session 00, edit only this file and `docs/exec_plans/README.md` unless a verification command reveals an unavoidable blocker that must be recorded. Do not touch Block 7+ code in Session 00.

Session 00 exact command sequence:

    git status --short
    .\.venv\Scripts\python.exe -m pytest tests\test_block_6_*.py tests\test_portfolio_alternatives_builder.py tests\test_candidate_launchpad_builder_handoff.py -q
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    .\.venv\Scripts\python.exe run_portfolio_review.py --dry-run
    git status --short

If `.venv` is unexpectedly missing, follow the repository's Windows Python rule and create it with `py -3 -m venv .venv`, then install dependencies if required. In this workspace `.venv` is expected to exist.

## Validation and Acceptance

Session 00 acceptance is intentionally narrow:

1. This ExecPlan exists at `docs/exec_plans/2026-06-05_blocks_5_9_vertical_product_loop_plan.md`.
2. `docs/exec_plans/README.md` points to this plan as the active plan.
3. The dirty tree is recorded in this plan or final Session 00 report.
4. The focused Block 6 test gate has a recorded pass/fail result.
5. `scripts/verify_docs.py` has a recorded pass/fail result.
6. `run_portfolio_review.py --dry-run` has a recorded pass/fail result.
7. The implementer stops after Session 00 and does not implement Session 01.

The whole plan is accepted only after Session 10, when the real one-candidate vertical demo produces all required artifacts and the final status is genuinely true.

## Idempotence and Recovery

The plan is additive. Re-running Session 00 should not overwrite code or generated outputs. If the ExecPlan file already exists, update its living sections rather than creating a duplicate. If `docs/exec_plans/README.md` already points to this plan, leave the pointer stable and only update explanatory text if needed.

If any Session 00 command fails, record the failure in `Progress`, `Surprises & Discoveries`, and `Outcomes & Retrospective`, then stop. Future sessions should resolve that blocker before beginning Session 01.

## Notes at Revision Bottom

2026-06-05: Initial checked-in plan created from the user-approved session breakdown. It intentionally starts with Session 00 and includes the rule that the implementer must stop after Session 00 succeeds or fails.

2026-06-05: Session 03 updated the plan after adding the Block 7 runtime script, failed/infeasible handling, stale-weight regression coverage, and focused verification evidence.

2026-06-05: Session 05 updated the plan after expanding Block 8 Current-vs-Candidate content, adding focused trade-off/success-criteria tests, syncing the owning spec, and recording verification evidence.

2026-06-05: Session 06 updated the plan after adding the direct Block 7/8 to Block 9 Decision Verdict builder, focused verdict outcome tests, owning spec sync, and verification evidence.

2026-06-05: Session 07 updated the plan after expanding AI Commentary grounding to include Block 7 candidate-generation evidence and direct vertical-loop topics, syncing docs, and recording focused test evidence.

2026-06-05: Session 08 updated the plan after adding the one-command Blocks 5-9 vertical flow script, reference/mixed-evidence Equal Weight default selection, stale vertical artifact hygiene, focused tests, and minimal owning-doc sync.

2026-06-05: Session 09 updated the plan after synchronizing product wording and docs around the Builder setup / Candidate Generation / Comparison / Verdict boundary, adding the Session 09 decision/changelog/register entries, and leaving live demo acceptance for Session 10.

2026-06-05: Session 10 closed the plan after focused acceptance tests, docs verification, and a real one-command vertical demo produced the required Blocks 5-9 + AI grounding artifact chain. Final status: `BLOCK_6_READY BLOCK_7_READY BLOCK_8_READY BLOCK_9_READY READY_FOR_PRODUCT_DEMO`.
