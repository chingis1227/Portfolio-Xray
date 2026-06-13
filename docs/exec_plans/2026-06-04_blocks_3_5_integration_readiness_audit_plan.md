# Blocks 3-5 Product Handoff Integration Readiness Audit Plan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document is maintained according to `PLANS.md` in the repository root. This file is now the
single active ExecPlan for the Blocks 3-5 product handoff audit. It supersedes the earlier broader
one-candidate readiness framing in this same file and absorbs supporting evidence from
`docs/exec_plans/2026-06-04_block_4_portfolio_alternatives_builder_handoff.md` without changing the
main audit question.

## Purpose / Big Picture

The user-visible question for this plan is narrow and product-first: does Stress Lab evidence really
flow into an investment diagnosis, does that diagnosis become a testable Candidate Launchpad card,
does the selected card become safe Builder prefill, and is this chain covered by tests, live
artifacts, and documentation... The target product workflow is:

    Stress evidence -> Investment diagnosis -> Testable Launchpad card -> Builder prefill

This first phase is a read-only audit for source files, documentation, and tests. It may refresh
generated live artifacts when the session explicitly says to do so, but it must not fix source code,
add tests, change schemas, edit product documentation, run optimizer work, generate new candidates,
write weights, or treat a Launchpad/Builder card as a rebalance recommendation. If gaps are found,
the follow-up work gets a separate post-audit ExecPlan.

The audit does not ask whether the full one-candidate Decision Verdict path can run. Earlier work on
that broader question is retained here only as supporting evidence. The controlling question remains:
Legacy note normalized to English-only text.
Legacy note normalized to English-only text.

## Progress

- [x] (2026-06-04) Unified the repository plan around the user's canonical handoff audit question and made this file the single active ExecPlan for that work.
- [x] (2026-06-04) Imported supporting evidence from the earlier broader Blocks 3-5 readiness plan: `docs/audits/2026-06-04_blocks_3_5_integration_readiness_session_01.md` through `session_04.md` prove some cross-block validators and one-candidate/live blocker facts, but they do not by themselves close the canonical handoff sessions below.
- [x] (2026-06-04) Imported supporting evidence from the Block 4 -> Builder handoff plan: `docs/exec_plans/2026-06-04_block_4_portfolio_alternatives_builder_handoff.md` proves Builder prefill implementation, validator strengthening, live diagnosis-only proof, and documentation synchronization for the Launchpad -> Builder boundary.
- [x] (2026-06-04) Session 00 mojibake-marker” Baseline & Source-of-Truth Check. Status: closed in canonical format. Evidence: `docs/audits/2026-06-04_blocks_3_5_handoff_session_00_baseline.md`; source-of-truth documents and real handoff owners were identified without source-code changes, optimizer runs, candidate generation, or weight writes.
- [x] (2026-06-04) Session 00.1 mojibake-marker” Baseline normalization. Status: closed. Evidence: `docs/audits/2026-06-04_blocks_3_5_handoff_session_00_baseline.md`; the current ExecPlan was separated from older one-candidate readiness evidence and the Block 4 -> Builder plan, which remain supporting evidence only.
- [x] (2026-06-04) Session 01 mojibake-marker” Contract Map Audit. Status: closed with minor coverage gaps. Evidence: `docs/audits/2026-06-04_blocks_3_5_handoff_session_01_contract_map.md`; field-level table records Stress/X-Ray -> Block 4 signals, Block 4 -> Launchpad fields, and Launchpad -> Builder prefill fields, including no automatic generation and `is_rebalance_recommendation = false`.
- [x] (2026-06-04) Session 02 mojibake-marker” Block 3 -> Block 4 Behavior Audit. Status: closed with minor coverage gaps and one stress commentary test failure. Evidence: `docs/audits/2026-06-04_blocks_3_5_handoff_session_02_behavior.md`; Block 4 baseline passed (`25 passed`), archetype/no-trade/severity behavior checks passed (`28 passed`), targeted recession Hedge Gap checks passed (`2 passed`), and the stress/hedge-gap bundle showed `240 passed, 1 failed` due to generated commentary wording rather than a proven JSON handoff break.
- [x] Session 03 mojibake-marker” Block 4 -> Launchpad Audit. Status: closed with one minor coverage note. Evidence: `docs/audits/2026-06-04_blocks_3_5_handoff_session_03_launchpad.md`; the requested Launchpad/action/no-trade bundle passed (`20 passed`) and the audit confirms actionable diagnoses map to targeted hypothesis cards, acceptable portfolios map to reference/monitor cards, data-quality cases block candidate methods, and Launchpad wording/flags do not imply a rebalance recommendation.
- [x] Session 04 mojibake-marker” Launchpad -> Builder Prefill Audit. Status: closed in canonical format. Evidence: `docs/audits/2026-06-04_blocks_3_5_handoff_session_04_builder_prefill.md`; the current Session 04 rerun recorded `24 passed` for `tests/test_portfolio_alternatives_builder.py` and `tests/test_candidate_launchpad_builder_handoff.py`, confirms targeted context preservation, EW/RP reference handling, data-quality blocking, and no automatic factory/optimizer/weight execution.
- [x] Session 05 mojibake-marker” Live Portfolio Proof. Status: closed with caveats by supporting evidence. The handoff plan Session 07 recorded `scripts/validate_block_4_live.py --refresh-diagnosis` OK, `scripts/verify_live_core_e2e.py --profile diagnosis_only` OK after diagnosis-only tombstones, and `23 passed` for focused tests. This proves diagnosis-only live handoff; it does not prove fresh one-candidate materialization, which is outside this canonical handoff plan.
- [x] Session 06 mojibake-marker” Test Coverage Audit. Status: closed with minor gaps. Evidence: `docs/audits/2026-06-04_blocks_3_5_handoff_session_06_test_coverage.md`; the required coverage table records `92 passed` for the expanded Block 4 bundle, `30 passed` for Builder/product bundle/diagnostic journey tests, and `240 passed, 1 failed` for the expanded Stress/Hedge Gap bundle, with the remaining failure limited to generated commentary wording.
- [x] Session 07 - Docs vs Code Audit. Status: closed. Evidence: `docs/audits/2026-06-04_blocks_3_5_handoff_session_07_docs_vs_code.md`; `scripts/verify_docs.py` passed (`docs verification: OK`) and the required contradiction-by-document table found docs/code consistency for no Stress Lab recommendation, Block 4 diagnosis plus `next_diagnostic_step`, Launchpad testable non-portfolio cards, Builder prefill as setup only, EW/RP as reference benchmarks, and Decision Verdict as the downstream final decision layer.
- [x] Session 08 - Final Readiness Verdict. Status: closed with strict `NOT_READY` verdict for immediate move-forward. Evidence: `docs/audits/2026-06-04_blocks_3_5_handoff_session_08_final_readiness_verdict.md`; source/docs/tests mostly support the canonical handoff, but fresh diagnosis-only live E2E failed because stale root candidate/compare artifacts remain and the allowed diagnosis-only refresh was blocked by FRED `DTB3` timeout.

## Surprises & Discoveries

- Observation: Two plan names were misleadingly similar.
  Evidence: `docs/exec_plans/2026-06-04_blocks_3_5_integration_readiness_audit_plan.md` previously focused on broader one-candidate readiness through Decision Verdict and FRED blockers, while the user's canonical plan focuses on `Stress evidence -> Investment diagnosis -> Testable Launchpad card -> Builder prefill`.

- Observation: The Launchpad -> Builder part is stronger than the rest of the canonical audit.
  Evidence: `docs/exec_plans/2026-06-04_block_4_portfolio_alternatives_builder_handoff.md` records Builder prefill implementation, tests, validators, docs sync, and live diagnosis-only proof. It includes `19 passed`, `45 passed`, and `23 passed` focused validation transcripts.

- Observation: The older one-candidate readiness work should not be used to close this plan's Session 02 behavior audit.
  Evidence: older Session 01 recorded a broad `51 passed` bundle and a dry-run through Decision Verdict, but it did not record the exact behavior scenarios requested here, such as `weak hedge behavior only when Hedge Gap evidence exists` or `X-Ray risk vs stress contradiction gives mixed evidence, not forced rebalance`.

- Observation: Live one-candidate fresh materialization remains blocked by FRED, but that is not a blocker for the diagnosis-only handoff proof in this plan.
  Evidence: older readiness Sessions 02-04 repeatedly show FRED `DTB3` timeout for `run_portfolio_review.py --candidates equal_weight`; the handoff live proof used `diagnosis_only` and passed after diagnosis-only tombstones.

- Observation: Session 00/00.1 confirmed the current handoff owner split.
  Evidence: `docs/audits/2026-06-04_blocks_3_5_handoff_session_00_baseline.md` maps Stress Lab product evidence to `src/stress_results_block.py`, `src/hedge_gap_analysis_block.py`, and `src/current_portfolio_stress_scorecard_block.py`; Block 4 diagnosis to `src/block_4/*`; Launchpad v3 to `src/block_4/launchpad_cards.py`; and Builder prefill to `src/portfolio_alternatives_builder.py`.

- Observation: Session 01 found the field-level handoff is present, with two non-blocking coverage limits.
  Evidence: `docs/audits/2026-06-04_blocks_3_5_handoff_session_01_contract_map.md` shows Block 4 consumes stress diagnosis, hedge gap, hidden exposure alerts, weakness map risks, portfolio metrics, factor betas, and a top-1 risk-budget signal; broad risk-budget tables and broader factor exposure summaries are not consumed as full tables.

- Observation: Session 02 confirmed behavior, not just field existence, but found one failing stress commentary test.
  Evidence: `docs/audits/2026-06-04_blocks_3_5_handoff_session_02_behavior.md` records `25 passed` for the requested Block 4 baseline, `28 passed` for archetype/no-trade/severity behavior checks, `2 passed` for targeted recession Hedge Gap checks, and `240 passed, 1 failed` for the expanded stress/hedge-gap bundle. The failure is `tests/test_stress_hedge_gap_contract.py::test_stress_commentary_states_hedge_gap_not_applicable`, which expected the generated text phrase `Hedge gap: not applicable`.

- Observation: Severe recession plus weak offset coverage is currently proven through split evidence rather than one end-to-end Block 4 fixture.
  Evidence: Hedge Gap tests prove `recession_severe` can become the weakest protection area, and Block 4 taxonomy/scoring maps stress evidence to `weak_crisis_resilience`; however, Session 02 did not find a single Block 4 fixture whose main Hedge Gap scenario is `recession_severe` and whose final primary diagnosis is asserted.

- Observation: Weak hedge gating is strong but would benefit from an explicit negative regression test.
  Evidence: `src/block_4/problem_scoring.py` requires `offset_coverage_ratio` and/or `protection_status` for `weak_hedge_behavior`, and passing tests prove stress-confirmed weak hedge is demoted behind `weak_crisis_resilience`; Session 02 did not find a named negative test proving no Hedge Gap v1 evidence prevents `weak_hedge_behavior` from becoming actionable.

- Observation: Session 03 confirms the Block 4 -> Launchpad boundary is safe for the canonical handoff.
  Evidence: `docs/audits/2026-06-04_blocks_3_5_handoff_session_03_launchpad.md` records `20 passed` for the Launchpad/action/no-trade bundle and shows targeted, reference, monitor, and data-quality outcomes keep `is_rebalance_recommendation = false`, `generates_portfolio = false`, and a Decision Verdict boundary.

- Observation: Session 04 now has fresh canonical evidence rather than only supporting evidence from the older handoff plan.
  Evidence: `docs/audits/2026-06-04_blocks_3_5_handoff_session_04_builder_prefill.md` records the current baseline bundle as `24 passed`, replacing the older supporting count of `19 passed` for the same Builder prefill boundary.
- Observation: The literal Session 06 glob commands are not portable as written under Windows PowerShell.
  Evidence: `python -m pytest tests/test_block_4_*.py -q` and `python -m pytest tests/test_stress_*.py tests/test_hedge_gap*.py -q` both failed with `file or directory not found` before collection; expanding the file list through `Get-ChildItem` produced the intended runs.

- Observation: Session 06 confirms broad test coverage, with the same Stress Lab commentary wording failure carried forward.
  Evidence: `docs/audits/2026-06-04_blocks_3_5_handoff_session_06_test_coverage.md` records `92 passed` for Block 4, `30 passed` for Builder/product bundle/diagnostic journey, and `240 passed, 1 failed` for Stress/Hedge Gap; the failed test is `tests/test_stress_hedge_gap_contract.py::test_stress_commentary_states_hedge_gap_not_applicable`.



- Observation: Session 07 found docs/code consistency for the canonical handoff, with only a wording caution around explicit demo commands.
  Evidence: `docs/audits/2026-06-04_blocks_3_5_handoff_session_07_docs_vs_code.md` records `scripts/verify_docs.py` as OK and compares `SPEC.md`, `OUTPUTS.md`, `TESTING.md`, `WORKFLOW.md`, `docs/product_flow_operator_guide.md`, and the owning specs against `src/block_4/diagnosis_builder.py`, `src/block_4/launchpad_cards.py`, `src/portfolio_alternatives_builder.py`, and `scripts/core_mvp_validation_contract.py`. The docs and code agree that Stress Lab is diagnostic, Block 4 emits `next_diagnostic_step`, Launchpad cards do not generate portfolios, Builder prefill is setup only, EW/RP are reference benchmarks, and Decision Verdict is downstream.

## Decision Log

- Decision: Treat this file as the single active ExecPlan for the user's canonical Blocks 3-5 handoff audit.
  Rationale: The user explicitly said to work only with the plan whose main question is whether Stress evidence affects diagnosis, diagnosis affects Launchpad, Launchpad affects Builder, and whether that is covered by tests/docs.
  Date/Author: 2026-06-04 / Codex.

- Decision: Keep older broader one-candidate readiness evidence only as supporting context, not as canonical session closure unless it matches the exact session requirements.
  Rationale: The older plan checked one-candidate readiness and FRED blockers; this plan checks product handoff behavior and coverage.
  Date/Author: 2026-06-04 / Codex.

- Decision: Accept Session 04 and Session 05 as closed from the Block 4 -> Builder handoff evidence.
  Rationale: Those sessions match the canonical requirements closely: Builder prefill preserves context, EW/RP are reference benchmarks, data-quality blocks generation, live validation derives Builder prefill, no candidate is generated automatically, and diagnosis-only E2E passes.
  Date/Author: 2026-06-04 / Codex.

- Decision: Do not mark Session 02, Session 06, or Session 08 closed without a canonical audit artifact.
  Rationale: The requested scenario-level behavior audit, coverage table, and final readiness verdict are distinct deliverables and should not be inferred from nearby work.
  Date/Author: 2026-06-04 / Codex.

- Decision: Close Session 00 and Session 00.1 together as a read-only baseline package.
  Rationale: The user requested both baseline source-of-truth review and baseline normalization, and both are satisfied by the same static audit artifact without running product workflows or changing source code.
  Date/Author: 2026-06-04 / Codex.

- Decision: Close Session 01 with minor documented coverage gaps rather than treating partial risk-budget/factor breadth as blockers.
  Rationale: The required table exists and confirms the canonical handoff fields are produced, consumed, and protected by no-rebalance/no-auto-generation boundaries. The gaps are limited to breadth of risk-budget and factor-exposure consumption, not a broken handoff for the requested Stress evidence -> diagnosis -> Launchpad -> Builder chain.
  Date/Author: 2026-06-04 / Codex.

- Decision: Close Session 02 despite the stress commentary failure, while carrying that failure forward as a non-handoff test issue.
  Rationale: The required behavior question is whether Block 3 stress evidence changes or constrains Block 4 diagnosis behavior. The passing Block 4 and archetype/no-trade/severity tests prove activation, prioritization, confidence, and no-trade gating behavior. The one failing stress test is a text-surface wording assertion in generated commentary, not evidence that Block 3 JSON evidence fails to reach or constrain Block 4.
  Date/Author: 2026-06-04 / Codex.

- Decision: Close Session 03 with one minor non-blocking coverage note.
  Rationale: The required Launchpad/action/no-trade tests passed and the audit confirms correct mappings from diagnosis outcomes to targeted hypothesis, reference benchmark, monitor, and data-quality cards, with no rebalance recommendation wording or flags. The only noted gap is a possible future parameterized taxonomy-wide card-type/status regression test.
  Date/Author: 2026-06-04 / Codex.

- Decision: Re-close Session 04 in canonical format with a fresh audit note.
  Rationale: The user explicitly asked to do Session 04 for this active plan. The current rerun passed and directly confirms the Launchpad -> Builder prefill contract rather than relying only on the older Block 4 -> Builder supporting plan.
  Date/Author: 2026-06-04 / Codex.
- Decision: Close Session 06 with minor gaps rather than treating the Stress Lab commentary wording failure as a handoff blocker.
  Rationale: The required Session 06 deliverable is a coverage table across Block 4, Builder/product surfaces, and Stress/Hedge Gap tests. The Block 4 and Builder/product groups passed, and Stress/Hedge Gap has broad passing coverage with one generated-commentary phrase mismatch. That failure is real and remains a follow-up item, but it is not direct evidence that Stress JSON evidence fails to reach Block 4 or Builder prefill.
  Date/Author: 2026-06-04 / Codex.

- Decision: Close Session 07 with no blocking documentation contradictions.
  Rationale: `verify_docs.py` passed, and the contradiction-by-document audit table confirms that the source-of-truth docs match implementation and validators for no pre-verdict rebalance recommendation, required `next_diagnostic_step`, testable Launchpad cards, safe Builder prefill, EW/RP reference benchmark role, and Decision Verdict as the downstream final decision layer. Broader one-candidate demo wording remains acceptable because it is explicitly opt-in.
  Date/Author: 2026-06-04 / Codex.

## Outcomes & Retrospective

The plan is now aligned to the user's intended product handoff audit. The repository already contains strong evidence for Launchpad -> Builder and live diagnosis-only handoff. Session 06 supplies the missing test coverage table, and Session 07 supplies the documentation-vs-code contradiction audit table. Session 08 is now closed. The main remaining work is not the read-only audit; it is a follow-up live-artifact hygiene / FRED-cache remediation before treating the workspace as ready for Candidate Generation.

Session 00 and Session 00.1 are closed in canonical format. Session 01 is now also closed with a canonical field-level contract map. Session 02 is closed with behavior evidence: Block 3 stress evidence does affect and constrain Block 4 activation, prioritization, confidence, and no-trade behavior. Session 03 is closed with Launchpad outcome evidence: Block 4 diagnoses become safe targeted/reference/monitor/data cards without rebalance recommendation flags or wording. Session 04 is closed with fresh Builder prefill evidence: selected Launchpad cards preserve diagnostic setup context, keep EW/RP as reference benchmarks, block data-quality cases, and do not run candidate factory, optimizer, subprocess, or weight-writing paths automatically. Session 07 is closed with docs/code consistency evidence: source-of-truth docs and implementation agree that the handoff remains diagnostic, non-binding, explicitly generated only after user action, and finalized only by Decision Verdict. Session 08 is closed with a strict `NOT_READY` verdict for immediate move-forward: the source handoff is mostly ready with minor gaps, but current diagnosis-only live E2E proof is not clean because stale root candidate/compare artifacts remain and the allowed refresh path is blocked by FRED `DTB3` timeout. The next safe step is a separate follow-up focused on live diagnosis-only artifact hygiene and/or an approved data-cache fallback, not Candidate Generation.

## Context and Orientation

Legacy note normalized to English-only text.

The current product is diagnosis-first and current-portfolio-first. The relevant canonical flow for this plan is:

    Input portfolio
    -> Portfolio X-Ray
    -> Stress Test Lab
    -> Problem Classification
    -> Candidate Launchpad
    -> Portfolio Alternatives Builder

Stress Lab evidence means product stress artifacts on `Main portfolio/analysis_subject/stress_report.json` and the source builders that produce them, including `src/stress_results_block.py`, `src/hedge_gap_analysis_block.py`, and `src/current_portfolio_stress_scorecard_block.py`. Problem Classification means Block 4 diagnosis outputs under `Main portfolio/analysis_subject/`, especially `problem_classification.json`. Candidate Launchpad means `Main portfolio/analysis_subject/candidate_launchpad.json`, currently expected as `candidate_launchpad_v3`. Builder prefill means a safe structured object derived from a Launchpad card by `src/portfolio_alternatives_builder.py`; it pre-populates candidate setup fields but does not run the candidate factory, optimizer, or write weights.

Important source-of-truth documents are `AGENTS.md`, `SPEC.md`, `OUTPUTS.md`, `TESTING.md`, `WORKFLOW.md`, `PLANS.md`, `docs/product_flow_operator_guide.md`, `docs/specs/block_4_diagnosis_v3_spec.md`, `docs/specs/candidate_launchpad_spec.md`, `docs/specs/portfolio_alternatives_builder_spec.md`, and `docs/specs/stress_lab_layer_spec.md`.

Important implementation files include `src/block_4/evidence_extraction.py`, `src/block_4/diagnosis_builder.py`, `src/block_4/problem_prioritization.py`, `src/block_4/problem_scoring.py`, `src/block_4/launchpad_cards.py`, `src/portfolio_alternatives_builder.py`, `scripts/core_mvp_validation_contract.py`, `scripts/validate_block_4_live.py`, and `src/live_core_e2e.py`.

## Plan of Work

Session 00 reads source-of-truth documents and records the owning files/modules for the handoff. It should not edit behavior. It should create or update an audit note only if the user wants checked-in audit artifacts; otherwise, it can report the result in chat and update this ExecPlan progress.

Session 01 builds the field-level contract map requested by the user. It must explicitly cover Block 3 -> Block 4 fields such as stress diagnosis, hedge gap, weakness map, hidden risk alerts, risk budget, portfolio metrics, and factor exposure. It must cover Block 4 -> Launchpad/Builder fields such as primary diagnosis, source diagnosis id, hypothesis, next diagnostic step, launch status, decision boundary, card context preservation, no automatic candidate generation, and `is_rebalance_recommendation = false`.

Session 02 verifies behavior, not just field existence. It runs the stress and Block 4 behavior pytest commands and inspects tests/source to confirm the scenario list: severe recession plus weak offset coverage, rates shock plus duration concentration, weak hedge behavior only with Hedge Gap evidence, missing or partial stress evidence lowering confidence or flagging limitations, and X-Ray-versus-stress contradiction producing mixed evidence rather than forced rebalance.

Session 03 verifies Block 4 -> Launchpad outcomes. It runs the Launchpad/action/no-trade test bundle and confirms mappings from diagnosis outcomes to card types and launch statuses. It must explicitly check that Launchpad wording and flags do not imply a rebalance recommendation.

Session 04 is already supported by evidence, but a future rerun can repeat the Builder prefill test command if the code changes. It verifies that targeted cards preserve goal, method, success criteria, tradeoff, and decision boundary; reference cards keep EW/RP as benchmarks; data-quality cards block candidate generation; and Builder prefill does not execute factory, optimizer, or weight writes.

Session 05 is already supported by evidence, but a future rerun can repeat live diagnosis-only validation if generated artifacts change. It verifies current portfolio artifacts under `Main portfolio/analysis_subject/`, derived Builder prefill, no automatic candidate artifacts, and preserved decision boundary. External API/cache failures must be separated from contract failures.

Session 06 produces the requested coverage table. It runs the baseline pytest bundles and summarizes each group, command, pass/fail, what it protects, and gaps. It must not add missing tests during this audit; missing coverage is recorded for a later post-audit ExecPlan.

Session 07 runs `scripts/verify_docs.py` and compares code behavior against docs. It must look for contradictions around no rebalance recommendation from Stress Lab, Block 4 diagnosis plus next diagnostic step, Launchpad testable cards, Builder prefill not generating candidates, EW/RP as reference benchmarks, and Decision Verdict as the only final decision layer.

Session 08 gives the final readiness verdict: `READY_TO_MOVE_FORWARD`, `READY_WITH_MINOR_GAPS`, or `NOT_READY`. It summarizes live validation, tests passed, docs verified, current portfolio checked, blockers, non-blockers, future improvements, and whether to move to Candidate Generation or fix handoff/docs/tests first.

## Concrete Steps

All commands run from:

    Legacy note normalized to English-only text.

Use the repository virtual environment:

    .\.venv\Scripts\python.exe

If Python appears unavailable on Windows, check in this order before claiming it is missing:

    py -3 --version
    python --version
    where py
    where python

Session 00 commands and inspection targets:

    Get-Content AGENTS.md -Raw
    Get-Content SPEC.md -Raw
    Get-Content OUTPUTS.md -Raw
    Get-Content TESTING.md -Raw
    Get-Content WORKFLOW.md -Raw
    Get-Content PLANS.md -Raw
    Get-Content docs\specs\stress_lab_layer_spec.md -Raw
    Get-Content docs\specs\block_4_diagnosis_v3_spec.md -Raw
    Get-Content docs\specs\candidate_launchpad_spec.md -Raw
    Get-Content docs\specs\portfolio_alternatives_builder_spec.md -Raw

Session 01 inspection should use `rg` and targeted file reads around these modules:

    rg -n "stress_diagnosis|hedge_gap|weakness_map|hidden_risk|risk_budget|factor_exposure|next_diagnostic_step|decision_boundary|is_rebalance_recommendation" src scripts tests docs -S

Session 02 baseline commands:

    .\.venv\Scripts\python.exe -m pytest tests/test_stress_*.py tests/test_hedge_gap*.py -q
    .\.venv\Scripts\python.exe -m pytest tests/test_block_4_evidence_extraction.py tests/test_block_4_diagnosis_builder.py tests/test_block_4_problem_prioritization.py tests/test_block_4_problem_scoring.py -q

Session 03 baseline command:

    .\.venv\Scripts\python.exe -m pytest tests/test_block_4_launchpad_cards.py tests/test_block_4_action_path_mapping.py tests/test_block_4_no_trade_gate.py -q

Session 04 baseline command, already supported by prior evidence:

    .\.venv\Scripts\python.exe -m pytest tests/test_portfolio_alternatives_builder.py tests/test_candidate_launchpad_builder_handoff.py -q

Session 05 baseline commands, already supported by prior evidence:

    .\.venv\Scripts\python.exe scripts\validate_block_4_live.py --refresh-diagnosis
    .\.venv\Scripts\python.exe scripts\verify_live_core_e2e.py --profile diagnosis_only

Optional Session 05 refresh, only if current artifacts are stale and the user accepts generated artifact refresh:

    .\.venv\Scripts\python.exe run_portfolio_review.py --mode core --skip-candidates
    .\.venv\Scripts\python.exe scripts\validate_block_4_live.py --refresh-diagnosis

Session 06 baseline commands:

    .\.venv\Scripts\python.exe -m pytest tests/test_block_4_*.py -q
    .\.venv\Scripts\python.exe -m pytest tests/test_portfolio_alternatives_builder.py tests/test_candidate_launchpad_builder_handoff.py tests/test_product_bundle_integration.py tests/test_diagnostic_journey_view_model.py -q
    .\.venv\Scripts\python.exe -m pytest tests/test_stress_*.py tests/test_hedge_gap*.py -q

Session 07 docs command:

    .\.venv\Scripts\python.exe scripts\verify_docs.py

Minimum pass set for final readiness:

    .\.venv\Scripts\python.exe scripts\validate_block_4_live.py --refresh-diagnosis
    .\.venv\Scripts\python.exe scripts\verify_live_core_e2e.py --profile diagnosis_only
    .\.venv\Scripts\python.exe scripts\verify_docs.py
    .\.venv\Scripts\python.exe -m pytest tests/test_block_4_*.py -q
    .\.venv\Scripts\python.exe -m pytest tests/test_portfolio_alternatives_builder.py tests/test_candidate_launchpad_builder_handoff.py tests/test_product_bundle_integration.py tests/test_diagnostic_journey_view_model.py -q
    .\.venv\Scripts\python.exe -m pytest tests/test_stress_*.py tests/test_hedge_gap*.py -q

## Validation and Acceptance

This audit is accepted only when every canonical session has a recorded result. Session 00 must name the source-of-truth documents and owning modules. Session 01 must include the field-level handoff table and gaps. Session 02 must show whether stress evidence actually changes or constrains Block 4 behavior under the listed scenarios. Session 03 must show that Block 4 outcomes map to safe Launchpad cards and not rebalance recommendations. Session 04 must show Builder prefill preserves context without execution. Session 05 must show the live current portfolio handoff under diagnosis-only mode. Session 06 must show a test coverage table. Session 07 must show docs/code consistency and `verify_docs.py`. Session 08 must give one of the final statuses and a recommendation.

`READY_TO_MOVE_FORWARD` requires all handoffs, tests, live proof, docs, no automatic candidate generation, and no pre-verdict rebalance recommendation to pass. `READY_WITH_MINOR_GAPS` is allowed only when gaps are non-blocking and can be recorded for follow-up. `NOT_READY` is required if the audit finds a broken handoff, misleading rebalance recommendation, missing live proof, or missing critical coverage.

## Idempotence and Recovery

The audit commands are safe to repeat. Pytest and docs verification are read-only. `scripts/validate_block_4_live.py --refresh-diagnosis` may refresh diagnosis artifacts under generated output folders; generated artifacts are not source of truth unless explicitly targeted. `run_portfolio_review.py --mode core --skip-candidates` may refresh live generated artifacts and should be used only when the session explicitly calls for it.

Do not run candidate generation, optimizer, PDF generation, AI commentary generation, or monitoring changes as part of this audit. Do not write `portfolio_weights.yml`. Do not treat root-level legacy artifacts as current product truth when `analysis_subject/` artifacts exist. Do not delete or revert unrelated user changes.

If an external API, cache, or live data source fails, record it separately from product-contract failures. Earlier FRED `DTB3` timeouts are examples of external live data blockers and should not be confused with a Block 3 -> Block 4 handoff failure unless the exact session depends on fresh market data.

## Artifacts and Notes

Supporting evidence already found:

    docs/audits/2026-06-04_blocks_3_5_integration_readiness_session_01.md
        Broad focused contract bundle: 51 passed.
        Dry-run showed Input -> X-Ray -> Stress -> Problem Classification -> Candidate Launchpad -> Current vs Candidate -> Decision Verdict.
        Useful context, but not a substitute for the canonical Session 02 behavior audit.

    docs/audits/2026-06-04_blocks_3_5_integration_readiness_session_02.md
    docs/audits/2026-06-04_blocks_3_5_integration_readiness_session_03.md
    docs/audits/2026-06-04_blocks_3_5_integration_readiness_session_03_1.md
    docs/audits/2026-06-04_blocks_3_5_integration_readiness_session_04.md
        Broader one-candidate/fresh-refresh evidence. These sessions found FRED live timeout and validated existing product_one_candidate bundles.
        Useful context, but outside the main handoff audit except for separating external failures from contract failures.

    docs/exec_plans/2026-06-04_block_4_portfolio_alternatives_builder_handoff.md
        Strong supporting evidence for canonical Session 04 and Session 05.
        Recorded `19 passed` for Builder handoff tests, live Block 4 validation OK, diagnosis-only E2E OK, and `23 passed` focused live proof tests.

Current canonical status summary:

    Session 00: closed by docs/audits/2026-06-04_blocks_3_5_handoff_session_00_baseline.md.
    Session 00.1: closed by docs/audits/2026-06-04_blocks_3_5_handoff_session_00_baseline.md.
    Session 01: closed by docs/audits/2026-06-04_blocks_3_5_handoff_session_01_contract_map.md, with minor coverage gaps for broad risk-budget and factor-exposure breadth.
    Session 02: closed by docs/audits/2026-06-04_blocks_3_5_handoff_session_02_behavior.md, with minor coverage gaps and one non-handoff stress commentary failure.
    Session 03: closed by docs/audits/2026-06-04_blocks_3_5_handoff_session_03_launchpad.md, with one minor coverage note for possible taxonomy-wide card-type/status parameterization.
    Session 04: closed by docs/audits/2026-06-04_blocks_3_5_handoff_session_04_builder_prefill.md; current rerun recorded 24 passed for the Builder prefill baseline bundle.
    Session 05: closed from supporting evidence, with diagnosis-only scope caveat.
    Session 06: closed by docs/audits/2026-06-04_blocks_3_5_handoff_session_06_test_coverage.md, with minor coverage gaps and one stress commentary wording failure.
    Session 07: closed by docs/audits/2026-06-04_blocks_3_5_handoff_session_07_docs_vs_code.md; verify_docs.py passed and the contradiction-by-document audit table found no blocking docs/code contradictions.
    Session 08: closed by docs/audits/2026-06-04_blocks_3_5_handoff_session_08_final_readiness_verdict.md with strict `NOT_READY` verdict for immediate Candidate Generation from the current workspace state; source/docs/tests mostly support the handoff, but live diagnosis-only E2E proof failed due stale root candidate/compare artifacts and FRED `DTB3` timeout during allowed refresh.

## Interfaces and Dependencies

The stable validation and implementation interfaces for this audit are:

    scripts.core_mvp_validation_contract.check_problem_classification_v3
    scripts.core_mvp_validation_contract.check_candidate_launchpad_v3
    scripts.core_mvp_validation_contract.check_builder_prefill_from_launchpad_card, if present in the current code
    scripts.validate_block_4_live.validate_block_4_live
    src.live_core_e2e.validate_live_core_artifacts
    src.portfolio_alternatives_builder.build_builder_prefill_from_launchpad_card

The audit may inspect, but must not change, these source files during the read-only phase:

    src/stress_results_block.py
    src/hedge_gap_analysis_block.py
    src/current_portfolio_stress_scorecard_block.py
    src/block_4/evidence_extraction.py
    src/block_4/diagnosis_builder.py
    src/block_4/problem_prioritization.py
    src/block_4/problem_scoring.py
    src/block_4/launchpad_cards.py
    src/portfolio_alternatives_builder.py
    scripts/core_mvp_validation_contract.py
    scripts/validate_block_4_live.py
    src/live_core_e2e.py

Public APIs and interfaces are not planned to change in this audit phase. If gaps are found, the follow-up ExecPlan may target only contract validators, audit tests, docs alignment, or small field/naming handoff fixes. It may not target optimizer behavior, candidate generation, Decision Verdict logic, PDF output, AI commentary, or monitoring unless the user explicitly starts a separate plan.

Revision note, 2026-06-04: Reframed and unified this plan after the user clarified that the only controlling plan is the product handoff audit: Stress evidence -> diagnosis -> Launchpad card -> Builder prefill. Older one-candidate readiness sessions and the Block 4 -> Builder handoff plan were merged into this file as supporting evidence, not as replacement goals.

Revision note, 2026-06-04: Closed Session 00 and Session 00.1 with the read-only baseline audit note `docs/audits/2026-06-04_blocks_3_5_handoff_session_00_baseline.md`. This records source-of-truth documents, real handoff owners, supporting-evidence boundaries, and the starting field list for Session 01 without changing source code or generated portfolio artifacts.

Revision note, 2026-06-04: Closed Session 01 with the read-only contract map audit note docs/audits/2026-06-04_blocks_3_5_handoff_session_01_contract_map.md. This records the required field-level table and minor non-blocking coverage gaps without changing source code or generated portfolio artifacts.

Revision note, 2026-06-04: Closed Session 02 with the read-only behavior audit note docs/audits/2026-06-04_blocks_3_5_handoff_session_02_behavior.md. This records the requested pytest results, confirms severe recession/rates shock/weak hedge/missing evidence/mixed evidence behavior, and carries forward one generated stress commentary wording failure plus two minor coverage gaps without changing source code or generated portfolio artifacts.

Revision note, 2026-06-04: Closed Session 03 with the read-only Launchpad audit note docs/audits/2026-06-04_blocks_3_5_handoff_session_03_launchpad.md. This records the requested Launchpad/action/no-trade pytest result (`20 passed`), confirms diagnosis-to-card mappings and no-rebalance boundaries, and carries forward one minor optional coverage note without changing source code or generated portfolio artifacts.

Revision note, 2026-06-04: Closed Session 04 in canonical format with the read-only Builder prefill audit note docs/audits/2026-06-04_blocks_3_5_handoff_session_04_builder_prefill.md. This records the requested Builder prefill pytest result (`24 passed`), confirms targeted context preservation, EW/RP reference benchmark handling, data-quality blocking, and no automatic factory/optimizer/weight execution without changing source code or generated portfolio artifacts.

Revision note, 2026-06-04: Closed Session 06 with the read-only test coverage audit note docs/audits/2026-06-04_blocks_3_5_handoff_session_06_test_coverage.md. This records the requested coverage table, the actual Windows PowerShell-expanded pytest commands, `92 passed` for Block 4, `30 passed` for Builder/product bundle/diagnostic journey, and `240 passed, 1 failed` for Stress/Hedge Gap, carrying forward the known generated-commentary wording failure without changing source code, tests, or generated portfolio artifacts.


Revision note, 2026-06-04: Closed Session 07 with the read-only docs-vs-code audit note docs/audits/2026-06-04_blocks_3_5_handoff_session_07_docs_vs_code.md. This records `scripts/verify_docs.py` passing, a contradiction-by-document table across the source-of-truth docs and owning code/validators, and no blocking contradiction around Stress Lab recommendations, Block 4 `next_diagnostic_step`, Launchpad testable cards, Builder prefill non-generation, EW/RP reference benchmark roles, or Decision Verdict boundaries.

Revision note, 2026-06-04: Closed Session 08 with the final readiness verdict audit note docs/audits/2026-06-04_blocks_3_5_handoff_session_08_final_readiness_verdict.md. The strict plan verdict is `NOT_READY` for immediate move-forward into Candidate Generation from the current workspace: Block 4 live validation and docs verification passed, focused tests recorded `92 passed`, `30 passed`, and `240 passed, 1 failed`, but diagnosis-only live E2E failed because stale root candidate/compare artifacts remain and the allowed refresh path was blocked by FRED `DTB3` timeout.
