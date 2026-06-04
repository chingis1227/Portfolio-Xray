# Block 4 to Portfolio Alternatives Builder Handoff

> Supersession note, 2026-06-04: This focused handoff plan is retained as supporting evidence for the single active ExecPlan `docs/exec_plans/2026-06-04_blocks_3_5_integration_readiness_audit_plan.md`. Do not treat this file as a separate active plan unless the user explicitly reopens it. Its completed Sessions 04-07 are imported into the canonical Blocks 3-5 product handoff audit as evidence for Launchpad -> Builder prefill and live diagnosis-only proof.

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained according to `PLANS.md` in the repository root. It is self-contained: a future agent should be able to continue from this file without relying on chat history.

## Purpose / Big Picture

Portfolio MRI currently has a diagnosis-first product flow. Block 4 identifies what is wrong or uncertain in the current portfolio and Candidate Launchpad turns that diagnosis into cards describing hypotheses or reference comparisons. The next product step is Portfolio Alternatives Builder: it should consume a Launchpad v3 card and pre-fill candidate setup fields, while still making clear that no candidate is generated until the user explicitly asks and that no rebalance recommendation is being made.

After this work, a user or UI can select a Launchpad card and obtain a structured Builder prefill that preserves the diagnosis, hypothesis, success criteria, tradeoff, and decision boundary. Actionable diagnoses create targeted test setups, mixed or acceptable evidence creates Equal Weight / Risk Parity reference benchmark setups, and data-quality blockers prevent candidate generation.

## Progress

- [x] (2026-06-04) Session 01 audit completed without code changes. Current Builder reads only `suggested_methods`, `goal`, and `card_id` from Launchpad cards. Focused tests passed: `16 passed` for `tests/test_block_4_launchpad_cards.py` and `tests/test_portfolio_alternatives_builder.py`.
- [x] (2026-06-04) ExecPlan saved in the repository as `docs/exec_plans/2026-06-04_block_4_portfolio_alternatives_builder_handoff.md`.
- [x] (2026-06-04) Session 02 defined the Builder prefill contract in `docs/specs/portfolio_alternatives_builder_spec.md` and added the Launchpad-to-Builder handoff boundary in `docs/specs/candidate_launchpad_spec.md`. No conversion code was implemented.
- [x] (2026-06-04) Session 03 implemented Launchpad card to Builder prefill conversion in `src/portfolio_alternatives_builder.py`. Focused validation passed: `19 passed` for `tests/test_portfolio_alternatives_builder.py` and `tests/test_block_4_launchpad_cards.py`.
- [x] (2026-06-04) Session 04 added archetype handoff tests in `tests/test_candidate_launchpad_builder_handoff.py`. Focused validation passed: `19 passed` for `tests/test_portfolio_alternatives_builder.py` and `tests/test_candidate_launchpad_builder_handoff.py`.
- [x] (2026-06-04) Session 05 strengthened Launchpad and Builder prefill contract validation. Focused validation passed: live Block 4 validation OK; `45 passed` for `tests/test_product_bundle_integration.py`, `tests/test_product_bundle_paths.py`, `tests/test_diagnostic_journey_view_model.py`, and `tests/test_portfolio_alternatives_builder.py`; additional Block 4 contract validation passed with `19 passed`.
- [x] (2026-06-04) Session 06 synchronized canonical documentation for the Block 4 -> Launchpad -> Builder -> explicit Candidate Generation -> Comparison -> Decision Verdict boundary.
- [x] (2026-06-04) Session 07 proved the flow on the current live portfolio. Live Block 4 validation passed, live core E2E diagnosis-only validation passed after applying existing diagnosis-only product-bundle hygiene tombstones, and focused tests passed with `23 passed`.

## Surprises & Discoveries

- Observation: The current product-facing v3 Launchpad artifact is under `Main portfolio/analysis_subject/candidate_launchpad.json`, while `Main portfolio/candidate_launchpad.json` and some older fixture outputs still contain `candidate_launchpad_v1`.
  Evidence: Session 01 inspection found `schema_version: candidate_launchpad_v3` only under the `analysis_subject` path for the current portfolio-first output, while root-level and some fixture outputs reported `candidate_launchpad_v1`.

- Observation: the candidate_builder module was listed as a possible file to inspect in the original plan, but it does not exist in the current repository.
  Evidence: Session 01 file existence check reported `MISSING candidate_builder module`.

- Observation: Existing Launchpad v3 cards already contain most of the information needed for Builder prefill, but the Builder does not yet preserve it.
  Evidence: `src/block_4/launchpad_cards.py` writes `source_diagnosis_id`, `hypothesis_to_test`, `card_type`, `launch_status`, `success_criteria`, `tradeoff_to_watch`, `when_to_skip`, `decision_boundary`, and `is_rebalance_recommendation`; `src/portfolio_alternatives_builder.py` currently extracts only method id, goal, and source card id.

- Observation: Current Launchpad targeted method rows use `method_role: targeted_hypothesis`, while the planned Builder prefill contract uses `method_role: targeted_candidate_method` for the selected method role.
  Evidence: Session 02 inspection of `src/block_4/launchpad_cards.py` found `_suggested_method_row()` emits `targeted_hypothesis` except for reference benchmark rows. The Builder spec now documents that the future conversion should normalize Launchpad targeted rows to `targeted_candidate_method` in the Builder prefill object.

- Observation: The Session 03 conversion can be implemented as a pure dictionary transformer without touching candidate factory execution or the legacy `PortfolioAlternativeRequest` path.
  Evidence: `build_builder_prefill_from_launchpad_card()` now returns a stable prefill dictionary, while the existing `request_from_launchpad_card`, `build_portfolio_alternative_plan`, and `run_portfolio_alternative_plan` tests still pass unchanged.

- Observation: Session 05 live validation can derive Builder prefill from the primary `analysis_subject/candidate_launchpad.json` card without materializing a new artifact.
  Evidence: `scripts/validate_block_4_live.py --refresh-diagnosis` now reports `builder_mode`, `builder_source_card_id`, and `builder_candidate_generation_allowed` from the derived prefill, and the run completed with `Block 4 v3 live validation: OK`.

- Observation: Session 07 live proof needed diagnosis-only root tombstones before `scripts/verify_live_core_e2e.py --profile diagnosis_only` would pass.
  Evidence: The first E2E attempt failed with missing or non-tombstone `candidate_comparison.json`, `current_vs_candidate.json`, and `decision_verdict.json`; applying `src.product_bundle_hygiene.apply_diagnosis_only_product_bundle_hygiene()` wrote `no_candidate_v1` tombstones, and the same E2E command then completed with `live core E2E validation: OK`.

## Decision Log

- Decision: Store this plan as a checked-in ExecPlan under `docs/exec_plans/` rather than only in chat.
  Rationale: The work spans multiple sessions, code, validators, tests, and documentation; repository rules say complex work should use a living ExecPlan.
  Date/Author: 2026-06-04 / Codex.

- Decision: Treat `Main portfolio/analysis_subject/candidate_launchpad.json` as the current product artifact when validating the portfolio-first path.
  Rationale: The root-level `Main portfolio/candidate_launchpad.json` can be legacy v1 and should not override the current product flow.
  Date/Author: 2026-06-04 / Codex.

- Decision: Portfolio Alternatives Builder remains a prefill and delegation layer, not a recommender or optimizer menu.
  Rationale: The product boundary says Block 4 states what to test, Launchpad exposes test cards, Builder prepares candidate parameters, Candidate Generation happens only after explicit user action, and Decision Verdict is the only layer that decides whether real action is justified.
  Date/Author: 2026-06-04 / Codex.

- Decision: Session 02 documents the prefill contract without adding a test-only placeholder implementation.
  Rationale: The session scope is contract definition. Adding the conversion function before Session 03 would blur the plan boundary, and existing Builder tests are sufficient to verify that current behavior stayed unchanged.
  Date/Author: 2026-06-04 / Codex.

- Decision: Implement Session 03 as a plain `dict[str, Any]` helper rather than introducing a new dataclass.
  Rationale: The Session 02 contract explicitly calls for a stable JSON-like prefill object that UI code and validators can inspect directly.
  Date/Author: 2026-06-04 / Codex.

## Outcomes & Retrospective

Session 01 established the current state safely. No implementation behavior was changed. The key gap is clear: Launchpad v3 has the handoff information, but Builder currently discards most of it. Future sessions should implement the handoff additively, preserve the existing manual/custom Builder path, and keep candidate generation explicit.

Session 02 defined the Builder prefill contract in documentation only. The owning Builder spec now lists stable prefill keys, builder modes, method-role semantics, blocked/monitor behavior, and the rule that `candidate_generation_allowed` never means automatic generation. The Candidate Launchpad spec now states that Launchpad cards are Builder prefill sources, not candidate-generation artifacts.

Session 03 added `build_builder_prefill_from_launchpad_card()` as a pure Launchpad v3 card transformer. Targeted and reference cards now open `guided_from_diagnosis` prefill, targeted Launchpad method role `targeted_hypothesis` is normalized to Builder role `targeted_candidate_method`, reference benchmark role is preserved, and monitor/data-quality cards with no methods return non-generating prefill. Candidate factory execution remains explicit and downstream.

Session 04 added focused archetype handoff tests without changing production code. The new tests cover weak crisis resilience, poor diversification, high concentration constraints, mixed-evidence EW/RP reference comparison, acceptable-portfolio monitoring, data-quality blocking, and the manual custom Builder request path.

Session 05 added product-contract checks for the Launchpad-to-Builder handoff. The core validation contract now rejects Launchpad data-quality cards that expose candidate methods, EW/RP comparisons, defaults, or candidate-generation flags; keeps EW/RP reference benchmark role checks; and introduces a Builder prefill validator that requires stable handoff fields, success criteria for guided setups, preserved decision boundaries, `is_rebalance_recommendation: false`, and blocked data-quality candidate generation. The live Block 4 validator now derives and validates Builder prefill from the selected Launchpad card without generating a candidate.

Session 06 synchronized canonical documentation only. The top-level implementation/output/testing/decision/changelog docs and the owning Block 4, Launchpad, Builder, and operator-guide specs now state that Block 4 identifies the diagnosis and next diagnostic step, Launchpad exposes testable cards, Builder consumes selected cards as prefill, Builder does not recommend a rebalance, candidate generation requires explicit user action, and Decision Verdict is the only layer that decides whether action is justified.

Session 07 proved the handoff on the current live portfolio. The refreshed live diagnosis produced primary problem `mixed_evidence_no_action`, top-level next diagnostic step `reference_comparison`, and primary Launchpad card `launchpad_01_compare_against_simple_benchmark` with `card_type: reference_benchmark_test` and `launch_status: reference_test`. The derived Builder prefill used `builder_mode: guided_from_diagnosis`, `suggested_method: equal_weight`, `alternative_methods: ["risk_parity"]`, `method_role: reference_benchmark`, `candidate_generation_allowed: true` only for explicit user action, and `is_rebalance_recommendation: false`. No `candidate_factory_run.json` was created automatically, and root compare/verdict artifacts carried `no_candidate_v1` tombstones for diagnosis-only mode.

## Context and Orientation

The repository root is `D:\Рабочий стол\КУРСОР ТУЛА ДИАГНОСТИКА`. The project is a Python portfolio diagnostics and investment decision-support system. The current canonical product direction is diagnosis-first and current-portfolio-first, not optimizer-first.

The relevant product flow is:

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

Important terms:

Candidate Launchpad is the Block 4 product artifact that exposes cards describing what to test next. A card is not a portfolio and must not contain weights.

Portfolio Alternatives Builder is the layer that turns a selected Launchpad card into candidate setup parameters. In the current code it is implemented in `src/portfolio_alternatives_builder.py` as a wrapper that can return a one-candidate factory plan but does not execute it by default.

Builder prefill means a structured object that a UI or caller can use to open Builder in guided mode with fields already populated from the selected diagnosis card.

Reference benchmark means Equal Weight or Risk Parity used only as a diagnostic comparison point. It is not a recommendation to rebalance into Equal Weight or Risk Parity.

Decision boundary means the text and flags that prevent users from interpreting a diagnostic card or Builder setup as a real trade recommendation. Decision Verdict remains the downstream layer that can say whether action is justified.

Key files:

- `src/block_4/launchpad_cards.py` builds `candidate_launchpad_v3` cards.
- `src/block_4/diagnosis_builder.py` orchestrates Block 4 diagnosis outputs and writes `problem_classification.json` plus `candidate_launchpad.json`.
- `src/portfolio_alternatives_builder.py` owns the Builder wrapper and should receive the new prefill conversion function.
- `src/candidate_factory.py` and `run_candidate_factory.py` generate candidates only when explicitly called.
- `scripts/core_mvp_validation_contract.py` owns product-contract validators.
- `scripts/validate_block_4_live.py` validates live Block 4 artifacts.
- `docs/specs/block_4_diagnosis_v3_spec.md`, `docs/specs/candidate_launchpad_spec.md`, and `docs/specs/portfolio_alternatives_builder_spec.md` own the canonical documentation for this handoff.

The focused existing tests are:

- `tests/test_block_4_launchpad_cards.py`
- `tests/test_portfolio_alternatives_builder.py`
- `tests/test_product_bundle_integration.py`
- `tests/test_product_bundle_paths.py`
- `tests/test_diagnostic_journey_view_model.py`

## Plan of Work

Session 01 is complete. It audited the current state and confirmed that no code behavior had been changed. The current Builder can convert a Launchpad card into `PortfolioAlternativeRequest`, but it only extracts the selected candidate method id, `goal`, and `source_card_id`. It rejects monitor-only or data-quality cards by raising `PortfolioAlternativesBuilderError("launchpad_card_has_no_suggested_methods")`. That fallback prevents accidental candidate generation, but it does not yet produce a user-friendly blocked prefill object.

Session 02 should define the Builder prefill contract. Update `docs/specs/portfolio_alternatives_builder_spec.md` and, if needed, `docs/specs/candidate_launchpad_spec.md` to describe the following minimum fields: `builder_mode`, `source`, `source_diagnosis_id`, `source_card_id`, `goal`, `hypothesis_to_test`, `next_diagnostic_step`, `suggested_method`, `alternative_methods`, `constraint_preset`, `max_asset_weight`, `min_asset_weight`, `volatility_target`, `success_criteria`, `tradeoff_to_watch`, `when_to_skip`, `card_type`, `launch_status`, `method_role`, `is_rebalance_recommendation`, `decision_boundary`, and `candidate_generation_allowed`. In this session, add only minimal tests if they document the contract; do not implement the full conversion yet.

Session 03 should implement the conversion function in `src/portfolio_alternatives_builder.py`. Use a stable name such as `build_builder_prefill_from_launchpad_card(card: Mapping[str, Any], *, next_diagnostic_step: Mapping[str, Any] | None = None)`. The function should return a plain `dict[str, Any]` unless the repository style strongly prefers a dataclass after inspection. For targeted cards, return `builder_mode: guided_from_diagnosis`, preserve the card fields, set `candidate_generation_allowed: true`, set `suggested_method` from `default_method` if present or the first method, and set `alternative_methods` to the other candidate method ids. For reference cards, preserve EW/RP as reference benchmarks and keep `is_rebalance_recommendation: false`. For data-quality or monitor-only cards with no suggested methods, return a blocked or monitor prefill with `candidate_generation_allowed: false`; do not call or prepare candidate factory execution. Preserve `request_from_launchpad_card`, `build_portfolio_alternative_plan`, and manual `PortfolioAlternativeRequest` behavior.

Session 04 should add archetype tests in `tests/test_candidate_launchpad_builder_handoff.py`. Tests must prove that `weak_crisis_resilience` opens a targeted crisis-resilience setup, `poor_diversification` opens a diversification setup using Risk Parity or Equal Weight by Asset Class, `high_concentration` exposes max asset weight or concentration constraints, `mixed_evidence_no_action` opens an EW/RP reference comparison, `current_portfolio_acceptable` does not force a candidate and keeps monitoring visible, `evidence_insufficient_data_quality` blocks candidate generation, and manual custom Builder requests still work without a Launchpad card.

Session 05 should update validators. In `scripts/core_mvp_validation_contract.py`, strengthen or add checks so missing Builder handoff fields are contract violations. The validator should catch targeted cards without success criteria, reference cards whose EW/RP methods are not `method_role: reference_benchmark`, data-quality cards that allow candidate generation or provide unreliable EW/RP comparisons, and Builder prefill objects that lose the decision boundary if such objects are materialized or validated. Update `scripts/validate_block_4_live.py` if it needs to inspect derived Builder prefill from the selected card.

Session 06 should synchronize documentation. Update only the docs needed to keep the product truth current: `docs/specs/block_4_diagnosis_v3_spec.md`, `docs/specs/candidate_launchpad_spec.md`, `docs/specs/portfolio_alternatives_builder_spec.md`, `SPEC.md`, `OUTPUTS.md`, `TESTING.md`, `DECISIONS.md`, `CHANGELOG.md`, and `docs/product_flow_operator_guide.md`. The documentation must state that Block 4 identifies the diagnosis and next diagnostic step, Candidate Launchpad exposes testable cards, Builder consumes Launchpad cards and pre-fills candidate setup, Builder does not recommend rebalance, Candidate Generation happens only after explicit user action, and Decision Verdict is the only layer that decides whether action is justified.

Session 07 should run a live proof on the current portfolio. Refresh current diagnosis, inspect `problem_classification.json`, `candidate_launchpad.json`, and the derived Builder prefill. Confirm that the primary diagnosis has a next diagnostic step, Launchpad has a valid card, Builder can prefill from the selected card, no candidate is generated automatically, and the decision boundary is preserved. The optional `run_portfolio_review.py --candidates equal_weight` path may be used only if safe and should not block this handoff work if unrelated market-data issues occur.

## Concrete Steps

All commands should be run from the repository root:

    D:\Рабочий стол\КУРСОР ТУЛА ДИАГНОСТИКА

Use the repository virtual environment when available:

    .\.venv\Scripts\python.exe

If Python appears unavailable, follow the Windows Python discovery rule and check:

    py -3 --version
    python --version
    where py
    where python

Session 01 commands already run:

    .\.venv\Scripts\python.exe -m pytest tests/test_block_4_launchpad_cards.py tests/test_portfolio_alternatives_builder.py -q

Expected completed Session 01 output:

    ................                                                         [100%]
    16 passed

Session 02 validation command:

    .\.venv\Scripts\python.exe -m pytest tests/test_portfolio_alternatives_builder.py -q

Session 03 validation command:

    .\.venv\Scripts\python.exe -m pytest tests/test_portfolio_alternatives_builder.py tests/test_block_4_launchpad_cards.py -q

Session 04 validation command:

    .\.venv\Scripts\python.exe -m pytest tests/test_portfolio_alternatives_builder.py tests/test_candidate_launchpad_builder_handoff.py -q

Session 05 validation commands:

    .\.venv\Scripts\python.exe scripts\validate_block_4_live.py --refresh-diagnosis
    .\.venv\Scripts\python.exe -m pytest tests/test_product_bundle_integration.py tests/test_product_bundle_paths.py tests/test_diagnostic_journey_view_model.py tests/test_portfolio_alternatives_builder.py -q

Session 06 validation commands:

    .\.venv\Scripts\python.exe scripts\verify_docs.py
    .\.venv\Scripts\python.exe -m pytest tests/test_portfolio_alternatives_builder.py tests/test_block_4_launchpad_cards.py -q

Session 07 validation commands:

    .\.venv\Scripts\python.exe scripts\validate_block_4_live.py --refresh-diagnosis
    .\.venv\Scripts\python.exe scripts\verify_live_core_e2e.py --profile diagnosis_only
    .\.venv\Scripts\python.exe -m pytest tests/test_portfolio_alternatives_builder.py tests/test_product_bundle_integration.py tests/test_diagnostic_journey_view_model.py -q

Optional Session 07 command, only if safe:

    .\.venv\Scripts\python.exe run_portfolio_review.py --candidates equal_weight

Session 07 actual validation transcript:

    .\.venv\Scripts\python.exe scripts\validate_block_4_live.py --refresh-diagnosis
    ...
    primary_problem_id=mixed_evidence_no_action
    no_trade_outcome=do_not_act_yet
    n_cards=2
    launchpad_outcome=do_not_act_yet
    primary_card_id=launchpad_01_compare_against_simple_benchmark
    builder_mode=guided_from_diagnosis
    builder_source_card_id=launchpad_01_compare_against_simple_benchmark
    builder_candidate_generation_allowed=True
    product_contract_ok=True
    handoff_ok=True
    Block 4 v3 live validation: OK

    .\.venv\Scripts\python.exe scripts\verify_live_core_e2e.py --profile diagnosis_only
    ...
    ok=True
    profile=diagnosis_only
    block_4_primary_problem_id: mixed_evidence_no_action
    block_4_primary_card_id: launchpad_01_compare_against_simple_benchmark
    workflow_state: diagnosis_only
    live core E2E validation: OK

    .\.venv\Scripts\python.exe -m pytest tests/test_portfolio_alternatives_builder.py tests/test_product_bundle_integration.py tests/test_diagnostic_journey_view_model.py -q
    .......................                                                  [100%]
    23 passed in 21.68s

The optional `run_portfolio_review.py --candidates equal_weight` command was not run in Session 07. Reason: the required handoff proof already passed, and running an explicit candidate path would intentionally change the diagnosis-only artifact profile and mix the proof that no candidate is generated automatically.

## Validation and Acceptance

The full work is accepted when every valid Launchpad v3 card can be transformed into Builder prefill. Actionable diagnoses must create targeted Builder setup. Mixed or acceptable diagnoses must create Equal Weight and Risk Parity reference comparison setup. Data-quality blockers must prevent candidate generation. Builder must preserve source diagnosis, hypothesis, success criteria, tradeoff, decision boundary, and `is_rebalance_recommendation: false`. Candidate generation must happen only after explicit user action. Manual custom Builder path must continue to work. Validators must catch missing handoff fields. Documentation must explain the boundary from Block 4 to Launchpad to Builder to Candidate Generation to Comparison to Verdict.

For targeted crisis-resilience cards, acceptance means the prefill contains `builder_mode: guided_from_diagnosis`, a crisis-resilience goal or canonical equivalent, `suggested_method` such as `minimum_cvar_constrained` or `robust_mv_constrained`, success criteria that mention stress loss or offset coverage, and `is_rebalance_recommendation: false`.

For reference benchmark cards, acceptance means the prefill contains Equal Weight and Risk Parity as reference methods, `card_type: reference_benchmark_test`, `launch_status: reference_test`, `candidate_generation_allowed: true` only for explicit user action, and no wording that implies rebalance to a benchmark.

For data-quality cards, acceptance means the prefill contains `candidate_generation_allowed: false`, a blocked or resolve-data builder mode, no unreliable EW/RP candidate setup, and a next step equivalent to resolving data quality and rerunning diagnostics.

## Idempotence and Recovery

The implementation should be additive. Re-running tests is safe. The Builder prefill function should not write files, execute subprocesses, or trigger candidate generation. If a later session introduces a failing test, first inspect whether the failure is from the handoff changes or from unrelated generated outputs, stale cache, or market data. Generated directories such as `cache/`, `output/`, `results_csv/`, `Main portfolio/`, `portfolio_weights.yml`, `__pycache__/`, `.pytest_cache/`, generated PDFs, and generated markdown report sources are not source of truth unless a task explicitly targets them.

Do not revert unrelated dirty working-tree changes. Before any edit session, run `git status --short` and preserve existing user changes. Use `apply_patch` for manual edits when possible. Do not use destructive git commands unless explicitly requested.

## Artifacts and Notes

Session 01 audit evidence:

    PWD: D:\Рабочий стол\КУРСОР ТУЛА ДИАГНОСТИКА
    EXISTS src/block_4/launchpad_cards.py
    EXISTS src/block_4/diagnosis_builder.py
    EXISTS src/portfolio_alternatives_builder.py
    MISSING candidate_builder module
    EXISTS src/candidate_factory.py
    EXISTS scripts/core_mvp_validation_contract.py
    EXISTS scripts/validate_block_4_live.py
    EXISTS tests/test_block_4_launchpad_cards.py
    EXISTS tests/test_portfolio_alternatives_builder.py

Observed current Builder behavior from Session 01:

    targeted_full_v3 -> PortfolioAlternativeRequest(candidate_method_id='minimum_cvar_constrained', goal='Improve crisis resilience', source_card_id='launchpad_01_improve_crisis_resilience', ...)
    reference_v3 -> PortfolioAlternativeRequest(candidate_method_id='equal_weight', goal='Compare against simple benchmark', source_card_id='launchpad_01_compare_against_simple_benchmark', ...)
    monitor_only -> PortfolioAlternativesBuilderError launchpad_card_has_no_suggested_methods

Focused tests from Session 01:

    ................                                                         [100%]
    16 passed in 1.98s

## Interfaces and Dependencies

The main new interface should live in `src/portfolio_alternatives_builder.py`.

Recommended function signature:

    def build_builder_prefill_from_launchpad_card(
        card: Mapping[str, Any],
        *,
        next_diagnostic_step: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        ...

The returned dictionary should use stable keys so UI and validators can depend on them:

    builder_mode
    source
    source_diagnosis_id
    source_card_id
    goal
    hypothesis_to_test
    next_diagnostic_step
    suggested_method
    alternative_methods
    suggested_methods
    constraint_preset
    max_asset_weight
    min_asset_weight
    volatility_target
    success_criteria
    tradeoff_to_watch
    when_to_skip
    card_type
    launch_status
    method_role
    is_rebalance_recommendation
    decision_boundary
    candidate_generation_allowed

Allowed `builder_mode` values for this plan are:

    guided_from_diagnosis
    blocked_data_quality
    monitor_only
    custom_builder_entry

Allowed method role values for this plan are:

    targeted_candidate_method
    reference_benchmark
    custom_user_selected

The existing `PortfolioAlternativeRequest`, `request_from_launchpad_card`, `build_portfolio_alternative_plan`, and `run_portfolio_alternative_plan` interfaces must remain compatible with current tests. `build_builder_prefill_from_launchpad_card` must not call `build_portfolio_alternative_plan` automatically. Candidate factory execution remains explicit and downstream.

## Revision Notes

2026-06-04: Created this ExecPlan from the user-approved multi-session plan and added Session 01 audit evidence. Reason: the plan previously existed only in chat and needed to be saved in the repository as a living checked-in plan.

2026-06-04: Marked Session 02 complete after documenting the Builder prefill contract and Launchpad handoff boundary. Reason: future implementation sessions need a stable, self-contained contract before code and validator work.

2026-06-04: Marked Session 03 complete after implementing the pure Builder prefill conversion helper and focused tests. Reason: Launchpad v3 cards can now be transformed into Builder setup objects without generating candidates automatically.

2026-06-04: Marked Session 05 complete after strengthening JSON/product-bundle validators for Launchpad-to-Builder handoff. Reason: validators now catch missing or unsafe Builder handoff fields and live validation proves the primary card can derive a contract-valid Builder prefill.

2026-06-04: Marked Session 06 complete after synchronizing canonical documentation for the Launchpad-to-Builder handoff boundary. Reason: the code and validators from Sessions 03-05 needed top-level product truth, output, testing, decision, changelog, and operator-guide documentation alignment before live proof in Session 07.

2026-06-04: Marked Session 07 complete after running the current live portfolio proof. Reason: live validation now demonstrates Block 4 diagnosis, Launchpad card selection, derived Builder prefill, preserved decision boundary, diagnosis-only tombstones, and no automatic candidate generation.
