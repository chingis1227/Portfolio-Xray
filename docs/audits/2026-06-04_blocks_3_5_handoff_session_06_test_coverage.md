# Blocks 3-5 Handoff Audit — Session 06: Test Coverage Audit

Date: 2026-06-04
Scope: read-only audit of test coverage for the canonical handoff `Stress evidence -> Investment diagnosis -> Testable Launchpad card -> Builder prefill`.
Plan: `docs/exec_plans/2026-06-04_blocks_3_5_integration_readiness_audit_plan.md`.

## Question

Do the current pytest bundles cover the handoff chain strongly enough to support the final readiness verdict, and where are the remaining coverage gaps...

This session does not add or edit tests. Missing coverage is recorded for a later post-audit plan.

## Result

Status: **closed — pass with minor gaps**.

The required Session 06 coverage table now exists. The Block 4 and Builder/Bundle/Journey groups pass. The Stress/Hedge Gap group is mostly green but still has one known failing generated-commentary wording assertion: `tests/test_stress_hedge_gap_contract.py::test_stress_commentary_states_hedge_gap_not_applicable`. That failure is a real test failure, but it does not prove a broken JSON handoff from Stress Lab into Block 4 diagnosis.

## Commands Run

From repository root `D:\Desktop\CURSOR TULA DIAGNOSTICS`.

### Block 4 group

The plan's literal command uses a glob:

    .\.venv\Scripts\python.exe -m pytest tests/test_block_4_*.py -q

On Windows PowerShell, this was passed to pytest as a literal path and failed before collecting tests:

    no tests ran in 0.01s
    ERROR: file or directory not found: tests/test_block_4_*.py

I reran the intended group by expanding the file list in PowerShell:

    $files = Get-ChildItem -LiteralPath tests -Filter 'test_block_4_*.py' | ForEach-Object { $_.FullName }
    .\.venv\Scripts\python.exe -m pytest @files -q

Observed result:

    92 passed in 69.69s (0:01:09)

### Builder / product bundle / diagnostic journey group

Command:

    .\.venv\Scripts\python.exe -m pytest tests/test_portfolio_alternatives_builder.py tests/test_candidate_launchpad_builder_handoff.py tests/test_product_bundle_integration.py tests/test_diagnostic_journey_view_model.py -q

Observed result:

    30 passed in 31.79s

### Stress / Hedge Gap group

The plan's literal command uses globs:

    .\.venv\Scripts\python.exe -m pytest tests/test_stress_*.py tests/test_hedge_gap*.py -q

On Windows PowerShell, this was passed to pytest as a literal path and failed before collecting tests:

    no tests ran in 0.01s
    ERROR: file or directory not found: tests/test_stress_*.py

I reran the intended group by expanding the file list in PowerShell:

    $files = @()
    $files += Get-ChildItem -LiteralPath tests -Filter 'test_stress_*.py' | ForEach-Object { $_.FullName }
    $files += Get-ChildItem -LiteralPath tests -Filter 'test_hedge_gap*.py' | ForEach-Object { $_.FullName }
    .\.venv\Scripts\python.exe -m pytest @files -q

Observed result:

    1 failed, 240 passed in 44.64s

Failure:

    tests/test_stress_hedge_gap_contract.py::test_stress_commentary_states_hedge_gap_not_applicable
    AssertionError: assert 'Hedge gap: not applicable' in generated stress commentary text

## Coverage table

| Test group | Actual command / expansion used | Result | What it protects in this audit | Remaining gaps |
| --- | --- | --- | --- | --- |
| Block 4 diagnosis and Launchpad family | Expanded `tests/test_block_4_*.py` with PowerShell, then ran `python -m pytest @files -q`. Files included evidence extraction, diagnosis builder, problem taxonomy, scoring, prioritization, severity/confidence, no-trade gate, action path mapping, Launchpad cards, decision entry contract, v2 contracts, archetype fixtures, and live validation tests. | **Pass: 92 passed** | Protects `Stress/X-Ray evidence -> Problem Classification -> Launchpad outcome` behavior. It covers evidence extraction, taxonomy mapping, confidence/severity, root-cause prioritization, data-quality and mixed-evidence no-trade gates, action-path mapping, Launchpad card generation, and Block 4 contract validation. | Minor: Session 02 already found that severe recession + weak offset coverage is proven by split tests rather than one explicit end-to-end Block 4 fixture; weak hedge gating would benefit from an explicit negative regression test for “no Hedge Gap v1 evidence -> no actionable weak_hedge_behavior”. |
| Builder / product bundle / diagnostic journey | `tests/test_portfolio_alternatives_builder.py tests/test_candidate_launchpad_builder_handoff.py tests/test_product_bundle_integration.py tests/test_diagnostic_journey_view_model.py` | **Pass: 30 passed** | Protects `Launchpad card -> Builder prefill` and the product-bundle/Journey surfaces that expose the chain. It covers context preservation, reference benchmark role, data-quality blocking, no automatic execution through dry-run boundaries, live product-bundle integration, and diagnostic journey view-model visibility. | Minor: the “prefill never executes factory/optimizer/weights” boundary is covered by source separation and dry-run tests, but a future spy/mock test could make this boundary more explicit. |
| Stress / Hedge Gap | Expanded `tests/test_stress_*.py` and `tests/test_hedge_gap*.py` with PowerShell, then ran `python -m pytest @files -q`. | **Mostly pass: 240 passed, 1 failed** | Protects Stress Lab and Hedge Gap input evidence that Block 4 consumes: stress report contracts, scenario analytics, stress scorecards, downstream integration, historical replay fields, simulator/synthetic assumptions contracts, mandate pass, covariance/taxonomy behavior, Hedge Gap v1 contracts, materialization, and candidate-comparison stress/hedge surfaces. | One real failing text-surface test remains: generated commentary no longer includes the exact phrase `Hedge gap: not applicable`. This should be carried forward as a stress commentary wording regression. It is not by itself a broken JSON handoff into Block 4. |

## Coverage findings by handoff boundary

| Handoff boundary | Coverage status | Evidence from Session 06 | Interpretation |
| --- | --- | --- | --- |
| Stress evidence exists in tested artifacts | Covered with one text failure | Stress/Hedge Gap group collected and ran 241 tests: 240 passed, 1 generated-commentary wording failure. | Core Stress/Hedge Gap JSON and materialization contracts are broadly covered; one human-readable text phrase is not currently stable. |
| Stress/X-Ray evidence constrains diagnosis | Covered | Block 4 group passed 92 tests, including evidence extraction, scoring, severity/confidence, prioritization, and no-trade gate files. | The diagnosis layer has broad regression coverage for the signals and safety gates used by the handoff. |
| Diagnosis becomes Launchpad card | Covered | Block 4 group includes Launchpad cards, action-path mapping, no-trade gate, decision-entry contract, and archetype fixtures; all passed. | The mapping from diagnosis outcomes to targeted/reference/monitor/data-quality cards is protected. |
| Launchpad card becomes safe Builder prefill | Covered | Builder/handoff group passed 30 tests, including direct Builder prefill and candidate Launchpad handoff tests. | The prefill boundary is covered and remains non-binding: it does not represent a rebalance recommendation. |
| Product bundle and diagnostic journey expose the chain | Covered | Product bundle integration and diagnostic journey view-model tests are included in the 30 passed group. | The current product surfaces have tests that guard visibility of the handoff, not just internal helpers. |
| No automatic candidate generation / optimizer / weight write before explicit execution | Covered with optional hardening note | Builder tests passed and Session 04 source audit confirmed prefill returns structured data only; run execution is separate and dry-run by default. | No blocker. A future spy/mock regression test would make the non-execution guarantee even more direct. |

## Verdict for Session 06

Status: **closed with minor gaps**.

Session 06 found enough test coverage to proceed to the documentation-vs-code audit and then the final readiness verdict. The test suite coverage is not perfect, but the remaining issues are narrow:

1. A known Stress Lab generated-commentary wording failure remains open: `test_stress_commentary_states_hedge_gap_not_applicable`.
2. Severe recession + weak offset coverage would benefit from one explicit end-to-end Block 4 fixture rather than split proof across Hedge Gap and Block 4 tests.
3. Weak hedge gating would benefit from an explicit negative regression test for absence of Hedge Gap v1 evidence.
4. Builder prefill could be hardened with a spy/mock test proving no factory/optimizer/weight execution during prefill construction.

No source code, tests, schemas, optimizer flows, candidate generation, weights, PDFs, or generated portfolio artifacts were changed during this session. Only this audit note and the active ExecPlan status are intended to change.
