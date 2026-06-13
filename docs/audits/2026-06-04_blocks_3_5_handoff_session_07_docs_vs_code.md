# Blocks 3-5 Handoff Audit — Session 07: Docs vs Code Audit

Date: 2026-06-04
Scope: read-only documentation-vs-code audit for the canonical handoff `Stress evidence -> Investment diagnosis -> Testable Launchpad card -> Builder prefill`.
Plan: `docs/exec_plans/2026-06-04_blocks_3_5_integration_readiness_audit_plan.md`.

## Question

Do the current source-of-truth documents contradict implemented behavior around these boundaries...

1. Stress Lab must not issue a rebalance or investment recommendation.
2. Block 4 must produce an investment diagnosis plus `next_diagnostic_step`.
3. Candidate Launchpad cards must be testable cards, not portfolios or recommendations.
4. Builder prefill must not generate candidates, run optimizers, or write weights.
5. Equal Weight and Risk Parity must be reference benchmarks when used by mixed/acceptable outcomes.
6. Decision Verdict must remain the only final product decision layer after comparison evidence exists.

This session does not change source code, tests, schemas, generated portfolio artifacts, candidate artifacts, optimizer outputs, or documentation content outside this audit note and the active ExecPlan status.

## Result

Status: **closed — docs/code consistent, with minor wording caveats**.

`scripts/verify_docs.py` passed. The targeted contradiction audit did not find a blocker. The relevant product docs consistently describe the handoff as diagnostic and non-binding, and the implementation/validators enforce the same boundaries: `is_rebalance_recommendation` is false, Launchpad cards have `generates_portfolio: false`, Builder prefill returns a setup dictionary only, candidate generation is a separate explicit plan/run path, and Decision Verdict remains downstream of comparison evidence.

Minor caveat: documentation still contains some broader demo/runtime references to one-candidate flows such as `run_portfolio_review.py --candidates equal_weight`. Those are not contradictions for this session because they are explicitly framed as opt-in demo or explicit generation paths, not automatic Launchpad/Builder prefill behavior.

## Commands Run

From repository root `D:\Desktop\CURSOR TULA DIAGNOSTICS`.

```powershell
.\.venv\Scripts\python.exe scripts\verify_docs.py
```

Observed result:

```text
docs verification: OK
```

Targeted documentation search:

```powershell
rg -n "rebalance recommendation|is_rebalance_recommendation|not.*recommend|recommendation|Decision Verdict|final decision|next diagnostic step|next_diagnostic_step|Builder prefill|prefill|generat.*candidate|candidate generation|equal....weight|risk....parity|EW|RP|reference benchmark|benchmark" SPEC.md OUTPUTS.md TESTING.md WORKFLOW.md docs\product_flow_operator_guide.md docs\specs\stress_lab_layer_spec.md docs\specs\block_4_diagnosis_v3_spec.md docs\specs\candidate_launchpad_spec.md docs\specs\portfolio_alternatives_builder_spec.md -S
```

Targeted source/test/validator search:

```powershell
rg -n "is_rebalance_recommendation|decision_boundary|next_diagnostic_step|build_builder_prefill|generates_portfolio|launch_status|card_type|equal_weight|risk_parity|reference|subprocess|run_candidate_factory|portfolio_weights" src scripts tests -S
```

## Contradiction-by-document audit table

| Document | Relevant claim checked | Code / validator evidence checked | Result | Notes |
| --- | --- | --- | --- | --- |
| `docs/specs/stress_lab_layer_spec.md` | Stress Lab non-goals include no direct optimizer/mandate release impact and no investment recommendations. | Block 4 consumes Stress/Hedge Gap evidence through diagnosis builders and validators; candidate/optimizer execution is not in Stress Lab handoff. | **Consistent** | No contradiction found for Session 07. The known Session 06 stress commentary wording test failure is a generated text phrase issue, not a docs/code contradiction about recommendations. |
| `docs/specs/block_4_diagnosis_v3_spec.md` | Block 4 converts Blocks 1-3 evidence into one diagnosis and `next_diagnostic_step`; Block 4/Launchpad/Builder prefill must not call this an investment recommendation; Decision Verdict decides action downstream. | `src/block_4/diagnosis_builder.py` emits `next_diagnostic_step` with a decision boundary; `scripts/core_mvp_validation_contract.py` requires `next_diagnostic_step` and a rebalance-blocking decision boundary. | **Consistent** | The spec and code both keep Block 4 diagnosis-first and non-binding. |
| `docs/specs/candidate_launchpad_spec.md` | Launchpad cards expose targeted/reference/monitor/data-quality next steps; they do not create candidates; `is_rebalance_recommendation` is always false; EW/RP are reference benchmarks. | `src/block_4/launchpad_cards.py` sets `is_rebalance_recommendation: False`, `generates_portfolio: False`, and the shared decision boundary; `scripts/core_mvp_validation_contract.py` rejects cards that violate those fields or EW/RP `reference_benchmark` roles. | **Consistent** | No Launchpad documentation was found that frames cards as portfolios or rebalance recommendations. |
| `docs/specs/portfolio_alternatives_builder_spec.md` | Builder prefill is setup only; it does not execute `run_candidate_factory.py`, write weights, or imply rebalance; candidate generation requires separate explicit user action. | `src/portfolio_alternatives_builder.py::build_builder_prefill_from_launchpad_card` returns a dictionary only; `build_portfolio_alternative_plan` only returns a command plan; `run_portfolio_alternative_plan` defaults to `dry_run=True`. Validators require `is_rebalance_recommendation: false` and decision boundary. | **Consistent** | The code imports `subprocess` only for the separate explicit run helper, not for prefill construction. |
| `OUTPUTS.md` | The handoff is `candidate_launchpad.json` card selection -> Builder prefill -> explicit Generate Candidate action; prefill is not a generated portfolio, not a rebalance recommendation, and not a Decision Verdict. | Implementation has no default Builder prefill output file; prefill helper is in-memory/API setup. Candidate artifacts remain in separate explicit factory/compare paths. | **Consistent** | This is aligned with the generated-vs-source boundary and current product-bundle policy. |
| `SPEC.md` | Diagnosis-first product flow: `analysis_subject` is diagnosed before candidates; Launchpad prefill preserves decision boundary; candidate generation is explicit; Decision Verdict remains downstream. | `src/block_4/diagnosis_builder.py`, `src/block_4/launchpad_cards.py`, and `src/portfolio_alternatives_builder.py` implement the same split. | **Consistent** | The spec also preserves technical Selection Engine terminology as backend evidence, which is not a contradiction. |
| `TESTING.md` | Test expectations include `next_diagnostic_step`, EW/RP reference tests for mixed/acceptable outcomes, Launchpad-to-Builder preservation, and no automatic candidate generation. | Session 06 recorded passing Block 4 and Builder/product bundles; validators enforce the same fields. | **Consistent** | The testing document accurately points to the relevant test groups. |
| `docs/product_flow_operator_guide.md` | Operators should not treat Builder prefill as weights; Builder does not recommend a rebalance or generate candidates automatically; explicit commands are needed for one-candidate generation. | `build_builder_prefill_from_launchpad_card` does not execute anything; `build_portfolio_alternative_plan` returns a plan; explicit factory/review commands are documented separately. | **Consistent** | Demo commands are opt-in and therefore not a contradiction. |
| `WORKFLOW.md` | Product demo may explicitly use `run_portfolio_review.py --candidates equal_weight`; routine work should follow workflow and docs/test routing. | `src/portfolio_review_workflow.py` tests and builder plan tests treat `--candidates equal_weight` as explicit one-candidate path. | **Consistent with caveat** | This is adjacent to the handoff but not automatic Builder prefill behavior. It remains useful to keep demo wording visibly “explicit/opt-in”. |

## Code behavior checkpoints

| Checkpoint | Evidence | Session 07 interpretation |
| --- | --- | --- |
| No rebalance recommendation from Stress Lab | Stress Lab spec non-goal; no candidate/optimizer execution found in Stress Lab handoff docs. | Pass. |
| Block 4 diagnosis plus next diagnostic step | `diagnosis_builder.py` creates `next_diagnostic_step`; validator requires it. | Pass. |
| Launchpad testable cards | `launchpad_cards.py` emits diagnosis-linked cards with `card_type`, `launch_status`, `success_criteria`, decision boundary, and no-generation flags. | Pass. |
| Builder prefill not generation | `build_builder_prefill_from_launchpad_card` returns a dict; explicit plan/run helpers are separate; dry-run default protects accidental execution. | Pass. |
| EW/RP as reference benchmarks | Docs say EW/RP reference benchmark tests; validator enforces `method_role: reference_benchmark` for EW/RP reference cards/prefill. | Pass. |
| Decision Verdict as final layer | Docs consistently place Decision Verdict after Current vs Candidate Comparison; code keeps Builder prefill and factory plans separate from verdict. | Pass. |

## Remaining notes / minor gaps

1. No documentation contradiction was found that blocks the canonical handoff audit.
2. The existing Session 06 generated-commentary wording failure remains a test issue, not a Session 07 docs/code contradiction.
3. Documentation has both diagnosis-only handoff language and explicit one-candidate demo language. This is acceptable because the latter is framed as opt-in, but future edits should keep the words “explicit”, “opt-in”, or equivalent near demo candidate-generation commands to avoid user confusion.
4. No docs were edited in this session beyond creating this audit artifact and updating the active ExecPlan.

## Verdict for Session 07

Status: **closed**.

Documentation and implementation are aligned for the canonical chain: Stress evidence remains diagnostic, Block 4 produces a non-binding diagnosis and next step, Launchpad exposes testable non-portfolio cards, Builder prefill is setup only, EW/RP are reference benchmarks when used as references, and Decision Verdict remains the final decision layer after comparison evidence.
