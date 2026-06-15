# Product Flow Contract

Status: **canonical cross-cutting product-flow contract** for Portfolio MRI Core MVP screens, adapters, generated-output interpretation, and documentation alignment.

Scope: product step order, user question per step, allowed behavior, forbidden behavior, artifact ownership, next-step logic, and product boundaries. This document does not define formulas, stress scenarios, optimizer methods, JSON schemas, visual design, or test implementation details. When a field-level, formula-level, or schema-level question appears, defer to the owning spec listed below.

This contract exists to prevent product-code-design drift. A future change that presents a different Core MVP flow must update this file and the owning source-of-truth documents in the same change.

## Source-of-truth order

Use this document for the cross-step product flow. Use the following documents for lower-level authority:

- `RULES.md` for project-wide principles and source-of-truth routing.
- `SPEC.md` for the current implementation contract and canonical spec index.
- `OUTPUTS.md` for generated output folders, artifact names, generated-vs-source boundaries, and output-producing workflows.
- `PRODUCT.md` for product direction, Core MVP vs advanced/later boundaries, and user goals.
- `docs/product_flow_operator_guide.md` for operator read order, demo commands, product-bundle paths, and anti-patterns.
- `docs/runtime_entrypoints.md` for active vs legacy runtime entrypoints.
- `docs/contracts/STAGED_REVIEW_STATE_CONTRACT.md` for the staged web execution contract,
  `review_state_v1`, canonical stage names, status semantics, and compact Supabase boundary.
- `docs/specs/portfolio_review_workflow_spec.md` for `analysis_subject`, diagnosis-before-candidates order, and legacy policy boundary.
- `docs/specs/input_assumptions_spec.md` for Core MVP input assumptions.
- `docs/specs/portfolio_xray_diagnostics_spec.md` and `docs/specs/portfolio_xray_layer_spec.md` for Portfolio Diagnosis.
- `docs/specs/stress_lab_layer_spec.md`, `docs/specs/stress_testing_spec.md`, `docs/specs/hedge_gap_analysis_spec.md`, and `docs/specs/current_portfolio_stress_scorecard_spec.md` for Stress Test Lab.
- `docs/specs/client_fit_check_spec.md` and `docs/specs/client_fit_questionnaire_spec.md` for Client Fit V1.
- `docs/specs/block_4_diagnosis_v3_spec.md`, `docs/specs/problem_classification_spec.md`, and `docs/specs/candidate_launchpad_spec.md` for Problem Classification and Candidate Launchpad.
- `docs/specs/portfolio_alternatives_builder_spec.md`, `docs/specs/builder_prefill_spec.md`, `docs/specs/candidate_setup_spec.md`, and `docs/specs/candidate_generation_spec.md` for Builder and Candidate Generation.
- `docs/specs/current_vs_candidate_spec.md` for Current vs Candidate Comparison.
- `docs/specs/decision_verdict_spec.md` for Decision Verdict.
- `docs/specs/ai_commentary_grounding_spec.md` for AI Commentary grounding.
- `docs/specs/light_monitoring_summary_spec.md` and `docs/specs/monitoring_spec.md` for Monitoring / What Changed.
- `docs/contracts/DOC_SYNC_CONTRACT.md` for documentation impact routing and final-response doc-sync reporting.

## Core product promise

Portfolio MRI is diagnosis-first, current-portfolio-first decision support. The user starts by submitting the current portfolio, not by choosing an optimizer. The product explains what the user owns, where risk lives, how the current portfolio behaves under stress, which problem is worth testing, what one selected candidate hypothesis changes, and whether action, no-action, another test, or evidence-insufficient is justified.

The Core MVP must not be presented as a black-box allocator, optimizer arena, trading system, mandate/suitability approval engine, or polished report factory. Existing code or generated artifacts that support those areas may remain available as advanced, backend, legacy, generated support, or backlog capability, but their existence does not promote them into the Core MVP flow.

## Canonical Core MVP flow

The canonical current product flow is:

```text
Input Portfolio
-> Portfolio Diagnosis
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

Current MVP frontend route reality may merge or defer some backend product steps. As of this contract, the visible frontend path is:

```text
/
-> /onboarding/sign-in
-> /onboarding/name
-> /onboarding/investor-type
-> /onboarding/loading
-> /workspace (returning signed-in account home)
-> /portfolio-input
-> /diagnosis
-> /evidence
-> /client-fit
-> /hypothesis
-> /comparison
-> /verdict
-> /report
```

The public landing opens the required email sign-in step. Local development may use `/onboarding/name?dev_bypass=1` as a preview shortcut while sign-in is being stabilized; that shortcut is not the product path. New users complete onboarding, which captures the planning profile and writes bounded Client Fit context before Portfolio Input. Returning signed-in users with a completed Portfolio MRI onboarding profile may skip the repeated name/questionnaire screens and open `/workspace` when saved workspace, portfolio, draft, or review history exists. `/workspace` is the account home: it restores saved work, shows the latest active review and compact history, and does not run calculations on login. Users without saved workspace data may continue to Portfolio Input with saved Client Fit context restored. `/client-profile` remains an advanced/manual Client Fit editor, not the primary journey start.

`/client-fit` displays the bounded fit interpretation after Stress Lab and before Hypothesis. `/hypothesis` may contain Problem Classification handoff, Candidate Launchpad, Builder setup, and the explicit candidate-generation attempt for the current MVP. There is no separate current Monitoring route; Monitoring / What Changed is a light product artifact and may be surfaced later or in report/summary context. Route merges do not change the product step order or boundaries.

Client Fit V1 status: active web onboarding and display route, plus backend compatibility for missing profiles. Backend/CLI runs may write `analysis_subject/client_fit_check.json` after Stress Lab and before Problem Classification, including `not_provided` when no profile exists. The normal frontend journey requires Client Fit context from onboarding before diagnosis and shows `/client-fit` before Hypothesis. Block 4, Launchpad, Builder, Current vs Candidate, Verdict, and Report may use bounded Client Fit context as display or hypothesis-test evidence only.

## Staged web execution

The web execution model is migrating toward staged, not synchronous, behavior. The intended
user-visible path is:

```text
User clicks Run diagnosis
-> backend creates review_id immediately
-> frontend shows progress
-> backend runs canonical stages
-> frontend receives compact stage state
-> frontend unlocks partial results when the owning stage is ready
```

The stage-state contract is `review_state_v1` in
`docs/contracts/STAGED_REVIEW_STATE_CONTRACT.md`. Its canonical stages are `input`, `data_load`,
`xray`, `stress`, `client_fit`, `problem_classification`, `launchpad_builder`, `candidate`,
`comparison`, `verdict`, and `report`. The backend start/status and diagnosis-stage runner
foundation is implemented through `POST /api/v1/reviews/staged` and
`GET /api/v1/reviews/{review_id}/status`; frontend staged polling and route unlocking remain later
migration work. The existing synchronous FastAPI and
CLI/file-driven compatibility paths remain valid current behavior until the frontend is explicitly
migrated.

Supabase remains compact-only in this target model. It may store account workspace state, saved portfolio inputs, immutable portfolio-version snapshots, review status, current stage, stage statuses, compact summaries, timestamps, archive markers, and saved portfolio links. It must not store raw generated artifacts, raw diagnosis or stress JSON, price history, PDFs, full run folders, or local artifact paths.

Completed reviews are immutable user-history snapshots. Editing a portfolio after a completed review creates a new draft/review snapshot tied to a new portfolio version; it must not mutate the old completed review or make old downstream verdict/report evidence look current. Login and workspace hydration restore compact state only and must not automatically rerun diagnosis, refresh market data, generate candidates, compare portfolios, or regenerate verdict/report artifacts. Recalculation is always an explicit user action.

The target first-run/demo path must support deterministic Demo / QA mode. Demo / QA mode uses frozen
fixture evidence and fixed data-freshness disclosure so the first product experience does not depend
on live market-data provider behavior. Live mode remains available with visible provider status and
freshness disclosure.

## Global product boundaries

The following rules apply to every screen, adapter, report surface, and operator interpretation:

1. Diagnosis happens before action. Portfolio Diagnosis and Stress evidence must exist before candidate testing is presented as current product flow.
2. The current portfolio, represented by `analysis_subject`, is the baseline for interpretation and comparison.
3. Problem Classification translates existing evidence into problems and test paths. It does not calculate new metrics, build candidates, or decide action.
4. Client Fit compares current-portfolio evidence against the provided profile as a non-binding overlay. It must remain separate from diagnostic quality, must not approve suitability, and must not become an optimizer mandate.
5. Candidate Launchpad cards are hypotheses, not portfolios. They contain no weights and do not execute builders.
6. Builder setup is setup only. It validates a selected hypothesis and may prepare a candidate handoff, but it does not create weights, comparison output, or a verdict.
7. Candidate Generation is an explicit user-triggered diagnostic attempt. A generated candidate is not a recommendation, not a trade order, and not automatically better than the current portfolio.
8. Current vs Candidate Comparison is evidence-first and trade-off-first. It must show what improved, worsened, stayed similar, could not be evaluated, and how current/candidate values compare with Client Fit targets when available.
9. Decision Verdict is non-binding decision support. `keep current`, `no material rebalance`, `rebalance review`, `test another candidate`, `candidate failed/infeasible`, and `evidence insufficient` are valid outcomes.
10. A rebalance verdict means evidence is material enough for rebalance review. It does not mean execute a trade.
11. AI Commentary is grounded explanation. It may explain deterministic evidence and gaps, but it must not invent calculations, statuses, scenarios, metrics, recommendations, or verdict evidence.
12. Monitoring / What Changed is non-executing. It compares run evidence over time and may suggest retest triggers, but it does not write weights, trade, or override the verdict.
13. Missing, partial, stale, or insufficient evidence is a valid product state. It must not be hidden or replaced with fabricated values.

## Step contract

| Step | Product role | Primary user question | Primary artifacts / evidence | Allowed behavior | Forbidden behavior | Next-step logic |
| --- | --- | --- | --- | --- | --- | --- |
| 1. Input Portfolio | Capture the factual current portfolio to diagnose. | What portfolio am I asking Portfolio MRI to diagnose... | User input; resolved `analysis_setup`; `analysis_subject/run_metadata.json` after diagnosis. | Ask for instruments, current weights, and investor currency; disclose system defaults and assumptions. | Do not require optimizer targets, client suitability, mandate caps, tax settings, or advanced constraints for Blocks 1-3. Do not treat generated policy weights as manual input. | Valid input can run diagnosis and proceed to Diagnosis. Invalid input stays on input with clear user-facing validation. |
| 2. Portfolio Diagnosis | Explain what the current portfolio owns and where risk lives. | What do I actually own, and what looks risky or weak... | `analysis_subject/portfolio_xray.json`; Portfolio Diagnosis product blocks and trusted legacy sections where required by the owning spec. | Show allocation, risk/return behavior, factor exposure, hidden exposure, concentration, weakness map, and data-trust signals. | Do not recommend a rebalance by itself. Do not create Portfolio Health Score as the main product answer. Do not parse root policy artifacts as subject truth. | If diagnosis evidence exists, proceed to Stress Test Lab. If partial, show limitations and proceed only with disclosed evidence quality. |
| 3. Stress Test Lab | Test how the current portfolio behaves in adverse markets. | Where can this portfolio break, and what evidence supports that view... | `analysis_subject/stress_report.json`; `stress_results_v1`; `hedge_gap_analysis_v1`; `current_portfolio_stress_scorecard_v1`; scenario library evidence. | Show synthetic and supported historical stress facts, worst scenarios, loss contributors, helped/hurt assets, hedge gaps, and data quality. | Do not fabricate historical evidence. Do not show Core MVP mandate pass/fail, `DIAG_*`, `pass`, or `loss_ok` semantics from legacy mandate mode. Do not add or rename scenarios without owning spec and decision record. | If stress evidence exists or is explicitly limited, proceed to Problem Classification. If unavailable, classify the evidence gap as a blocker or limitation. |
| 3.5 Client Fit Check | Compare current-portfolio evidence with the provided return, volatility, drawdown, and horizon profile. | Does this risk fit the provided profile... | `analysis_subject/client_fit_check.json` when available; profile source quality; target/limit rows. | Show fit/watch/breach/conflict/not-provided/evidence-insufficient context as non-binding interpretation. Preserve the separation between Client Fit status and diagnostic quality. | Do not call it suitability approval, hide material portfolio issues after a fit result, create buy/sell/rebalance instructions, or convert target return/vol/drawdown/horizon into optimizer mandates. | Proceed to Problem Classification with Client Fit as bounded context. If no profile exists, backend/CLI remains compatible and no Client Fit conclusion may be claimed. |
| 4. Problem Classification | Turn Portfolio Diagnosis and Stress evidence into a small set of understandable problems. | What is the main problem in the current portfolio... | `analysis_subject/problem_classification.json`; Block 4 v3 diagnosis evidence. | Summarize top problems, supporting evidence, and reasonable paths to test; allow current portfolio acceptable / monitor outcome. | Do not build candidates, choose an optimizer, issue a verdict, or state that a rebalance is required. | If there are testable paths, proceed to Candidate Launchpad. If only monitor/data-quality paths exist, route to monitor/report language or explain why candidate generation is blocked. |
| 5. Candidate Launchpad | Offer diagnosis-linked hypotheses to test. | Which improvement hypothesis should I test next... | `analysis_subject/candidate_launchpad.json`; launchpad cards linked to Problem Classification. | Show cards with goal, evidence, trade-off to watch, suggested method, and decision boundary. | Do not show cards as portfolios, weights, recommendations, or executed factory runs. Do not expose the full optimizer zoo as the Core MVP default. | Selecting a card opens Builder setup. Monitor-only or data-quality cards must not auto-generate candidates. |
| 6. Portfolio Alternatives Builder | Validate the selected hypothesis as a candidate test setup. | What exactly will be tested if I generate a candidate... | `analysis_subject/portfolio_alternatives_builder.json`; Builder prefill; CandidateSetup handoff when valid. | Show goal, method, simple constraints, success criteria, trade-off, skip rule, setup validation, and Client Fit target criteria when available. | Do not create weights, compare portfolios, write a verdict, expose advanced settings such as tax-aware optimization, turnover-aware objective, robust lambda, custom risk budgets, leverage, shorting, or full constraints UI in Core MVP, or silently convert Client Fit targets into optimizer mandates. | If setup is valid and generation is allowed, show explicit Generate Candidate action. If blocked, explain the blocker and keep comparison/verdict unavailable. |
| 7. Candidate Generation | Create one explicit diagnostic candidate attempt from the validated setup. | Was one usable test candidate created, or why did the attempt fail... | Root-level `candidate_generation.json` for the active vertical loop; optional candidate weights and freshness metadata. | Record generation status, method availability, candidate identity, weights when produced, warnings, and source links. | Do not auto-generate after Launchpad. Do not compare or decide. Do not treat stale, tombstoned, inactive, failed, or infeasible candidate artifacts as current evidence. | A live usable candidate can proceed to Current vs Candidate Comparison. Failed/infeasible/missing candidate routes to safe blocked state and then verdict/report as evidence insufficient when applicable. |
| 8. Current vs Candidate Comparison | Compare the diagnosed current portfolio with the selected candidate. | What improves, what worsens, and is the trade-off material enough to review... | `current_vs_candidate.json`; scoped `candidate_comparison.json`; optional `candidate_generation.json` and `client_fit_check.json` context. | Show deltas, improved/worsened/similar/unavailable areas, risk reduced/added, turnover/cost practicality, success criteria, Client Fit target comparisons when available, and materiality for decision review. | Do not build candidates, optimize weights, issue Decision Verdict, crown a winner, infer suitability, or fill missing metrics with fake `n/a` conclusions. Do not trust stale downstream verdict artifacts. | If comparison is live and materiality is evaluable, proceed to Decision Verdict. If comparison is unavailable/degraded, route to evidence-insufficient or test-another outcome. |
| 9. Decision Verdict | Translate comparison evidence into non-binding action/no-action decision support. | Is action justified now, or should I keep current, test another hypothesis, or stop due to insufficient evidence... | `decision_verdict.json`; `current_vs_candidate.json`; `candidate_generation.json` or `selection_decision.json`; optional `action_plan.json` context. | Present keep-current/no-trade, no material rebalance, rebalance review, test another, candidate failed/infeasible, risk-reduction-required where legacy semantics apply, or evidence-insufficient outcomes with confidence limitations. | Do not say "best portfolio", "must rebalance", "trade now", or imply suitability/tax approval. Do not hide trade-offs from comparison. Do not rename Selection Engine schemas or formulas. | Proceed to AI Commentary/report explanation. If verdict is absent because comparison is not ready, report evidence insufficiency rather than inventing a decision. |
| 10. AI Commentary / grounding | Provide grounded explanation inputs and safe narrative preview. | How should I explain the diagnosis, test, trade-offs, and verdict without inventing anything... | `ai_commentary_context.json`; allowed deterministic source artifacts named by the grounding spec. | Explain only grounded facts, warnings, evidence gaps, no-trade rationale, and monitoring context. | Do not call an LLM in the current grounding artifact, calculate new metrics, create unsupported recommendations, or give trade/tax advice. Do not treat `commentary.txt` / `stress_commentary.txt` legacy exports as Core MVP AI Commentary. | If grounding exists, use it in report/explanation. If source artifacts are missing, disclose gaps. |
| 11. Monitoring / What Changed | Summarize what changed since the prior review when monitoring evidence exists. | What changed, and should I retest or review anything... | `what_changed_summary.json`; `monitoring_diff.json`; monitoring snapshots; optional verdict/problem/comparison context. | Show changed risk contributor, stress behavior, market context, decision/action status, warnings, and retest triggers. | Do not create scheduler behavior, multi-client workspace semantics, broker alerts, new formulas, or automatic trades. Do not make advanced monitoring the Core MVP endpoint. | If present, show as light follow-up or report context. If absent, state that there is no prior snapshot or monitoring evidence rather than treating the run as failed. |

## Runtime and artifact boundaries

The default diagnosis-first path is `python run_portfolio_review.py`. It materializes `analysis_subject/` and remains diagnosis-only unless candidate execution is explicitly requested. The canonical one-candidate product demo is `python scripts/run_blocks_5_to_9_vertical_flow.py --method equal_weight`, replacing `equal_weight` with a supported method when needed. The compatibility path `python run_portfolio_review.py --candidates <id>` is allowed when the backend factory id is already known, but it is not the canonical visible Builder-to-Block-7 demo proof.

`python run_core_diagnostics.py` owns Blocks 1-3 only. It must not be interpreted as candidate, comparison, verdict, AI Commentary, or monitoring evidence.

`run_optimization.py`, `run_report.py`, `run_mvp_workflow.py`, full candidate factory batches, PDF rebuilds, optimizer zoo scripts, and advanced/research profiles are support infrastructure unless a task explicitly targets them. They must not be used to describe the Core MVP journey as optimizer-first.

For portfolio-first interpretation, open `{output_dir_final}/analysis_subject/` before root comparison or policy files. Root `run_result.json`, `portfolio_weights.yml`, root `portfolio_xray.json`, and root `stress_report.json` may belong to legacy policy paths and must not override the diagnosed subject.

The product-bundle chain is a set of separate files, not one merged `product_bundle.json`. Diagnosis artifacts prefer `analysis_subject/`; post-candidate artifacts such as `candidate_generation.json`, `current_vs_candidate.json`, `decision_verdict.json`, `ai_commentary_context.json`, and `what_changed_summary.json` are resolved by the product-bundle path helpers and manifest.

## Current MVP vs advanced / legacy / backlog

These capabilities must not be presented as the current Core MVP product flow merely because code, specs, or generated artifacts exist:

- Portfolio Health Score as the main product answer.
- Robustness Scorecard as the main product answer.
- Macro Dashboard / Macro Overlay.
- Full multi-candidate ranking / optimizer arena.
- Assumption Sensitivity, Pareto / Dominance, Regret Analysis, and Model Risk Diagnostics as primary screens.
- Full Action Plan / Rebalancing Advisor.
- Full Decision Journal.
- Advanced monitoring, full portfolio-health monitoring, macro-regime monitoring, and multi-client monitoring workspace.
- Crisis Replay UI and What Happens If simulator UI.
- Client Fit suitability approval, tax-aware optimization, turnover-aware optimizer objective, tactical tilt, Max Sharpe, full custom constraints UI, and Asset Diagnostics.
- Polished PDF report product as the default output path.

When these appear in code or generated outputs, classify them as `Advanced`, `Backend evidence`, `Technical artifact`, `Legacy`, `Generated support artifact`, or `Future/backlog` unless an owning spec and implementation explicitly promote them.

## Presentation and language guardrails

Primary user-facing surfaces should explain goals, evidence, trade-offs, confidence, and limitations. They should not expose raw backend filenames, JSON keys, booleans, schema names, internal status ids, stale artifact warnings, or operator terms as primary copy. Artifact names in this file are for implementers and documentation, not normal screen labels.

Use plain decision-support language:

- "candidate test" or "test candidate", not "recommended portfolio";
- "rebalance review", not "trade now";
- "keep current / no material rebalance", not "failure";
- "evidence insufficient", not "broken" when the run is valid but evidence is limited;
- "grounded explanation inputs", not "AI decided".

## Documentation impact rule

Any meaningful change to product order, step boundaries, runtime interpretation, artifact meaning, route mapping, candidate/verdict language, advanced-vs-Core status, or generated-output policy must update this contract and the owning docs in the same session. If implementation changes do not require this contract to change, the final response for that implementation session must say why.

## Validation for this contract

This contract is documentation-only. The minimum check after editing it is:

```text
git diff --check
```

When a later session applies this contract to code, use the checks in `TESTING.md`, `docs/runtime_entrypoints.md`, and the relevant screen or artifact contract. Frontend visual QA must follow `AGENTS.md` and `docs/demo/frontend_backend_vertical_runbook.md`.
