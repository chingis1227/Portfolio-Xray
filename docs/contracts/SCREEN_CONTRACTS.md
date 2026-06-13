# Screen Contracts

Status: **canonical screen-level contract** for Portfolio MRI / Portfolio X-Ray Core MVP frontend routes, screen responsibilities, product copy boundaries, empty states, CTAs, and QA checks.

Scope: current MVP screen roles, user questions, artifact use, adapter ownership, must-show and must-not-show sections, primary CTAs, next-step rules, forbidden UI language, current mismatches, empty states, and screen-specific QA checks.

Non-scope: backend formulas, JSON schemas, stress scenario definitions, route implementation, component refactors, generated-output refreshes, PDF generation, and visual design tokens. When a field-level, formula-level, schema-level, or design-system question appears, defer to the owning source of truth listed below.

This contract exists to prevent product-code-design drift. A future screen, adapter, copy, route, or QA change that alters Core MVP screen behavior must update this contract and the owning documents in the same change.

## Source-of-truth order

Use this document for screen-level product responsibilities. Use these documents for lower-level authority:

- `RULES.md` and `WORKFLOW.md` for project-wide rules, documentation sync, and verification discipline.
- `SPEC.md` for the current implementation contract and canonical spec index.
- `OUTPUTS.md` for generated output folders, artifact names, output profiles, and generated-vs-source boundaries.
- `docs/contracts/PRODUCT_FLOW_CONTRACT.md` for canonical product step order and global product boundaries.
- `docs/contracts/ARTIFACT_TO_SCREEN_MAP.md` for artifact producer, location, consumer screen, adapter, lineage, and stale-data policy.
- `docs/contracts/FASTAPI_SCREEN_MAPPING.json` for the machine-readable FastAPI operation,
  response-field, and screen-route governance map.
- `docs/product_flow_operator_guide.md` and `docs/runtime_entrypoints.md` for runtime interpretation and demo-vs-core command boundaries.
- `docs/specs/input_assumptions_spec.md` for portfolio input assumptions.
- `docs/specs/portfolio_xray_diagnostics_spec.md` and `docs/specs/portfolio_xray_layer_spec.md` for Portfolio X-Ray evidence.
- `docs/specs/stress_lab_layer_spec.md`, `docs/specs/stress_testing_spec.md`, `docs/specs/current_portfolio_stress_scorecard_spec.md`, and `docs/specs/hedge_gap_analysis_spec.md` for Stress Test Lab evidence.
- `docs/specs/client_fit_check_spec.md` and `docs/specs/client_fit_questionnaire_spec.md` for Client Fit V1 evidence and questionnaire boundaries.
- `docs/specs/block_4_diagnosis_v3_spec.md`, `docs/specs/problem_classification_spec.md`, and `docs/specs/candidate_launchpad_spec.md` for Problem Classification and Candidate Launchpad.
- `docs/specs/portfolio_alternatives_builder_spec.md`, `docs/specs/builder_prefill_spec.md`, `docs/specs/candidate_setup_spec.md`, and `docs/specs/candidate_generation_spec.md` for Builder setup and Candidate Generation.
- `docs/specs/current_vs_candidate_spec.md` for Current vs Candidate Comparison.
- `docs/specs/decision_verdict_spec.md` for Decision Verdict.
- `docs/specs/ai_commentary_grounding_spec.md` for Report / AI Commentary grounding.
- `docs/specs/light_monitoring_summary_spec.md` and `docs/specs/monitoring_spec.md` for Monitoring / What Changed.
- `docs/design/portfolio_mri_design_system.md` and future `docs/contracts/DESIGN_SYSTEM_CONTRACT.md` for visual hierarchy and status styling.
- `docs/contracts/DOC_SYNC_CONTRACT.md` for documentation impact routing and final-response doc-sync reporting.

## Current MVP route reality

The visible current MVP frontend route chain is:

```text
/client-profile
-> /portfolio-input
-> /diagnosis
-> /evidence
-> /client-fit
-> /hypothesis
-> /comparison
-> /verdict
-> /report
```

There is no current `/candidate`, `/monitoring`, `/what-changed`, optimizer-arena, action-plan, decision-journal, macro-dashboard, or PDF-product route. `/hypothesis` intentionally owns Problem Classification handoff, Candidate Launchpad, Builder setup, and the explicit candidate-generation attempt for the MVP. Monitoring / What Changed is a deferred UI layer.

Client Fit V1 now has active frontend onboarding and display routes. `/client-profile` captures a
mandatory web planning profile before diagnosis; `/client-fit` displays bounded Client Fit evidence
after Stress Test Lab and before Hypothesis. Backend/CLI compatibility remains intact when Client
Fit is missing: those paths may produce a `not_provided` Client Fit state, but the normal web
journey disables diagnosis until the profile exists.

Previous route chain before Session 15 was:

```text
/portfolio-input
-> /diagnosis
-> /evidence
-> /hypothesis
-> /comparison
-> /verdict
-> /report
```

## Global screen rules

1. The UI is diagnosis-first and current-portfolio-first. Current portfolio evidence must appear before candidate evidence.
2. A candidate is a diagnostic hypothesis test, not a recommendation, not a best portfolio, and not a trade order.
3. Builder setup is setup-only until the user explicitly generates one candidate attempt.
4. Comparison is trade-off evidence, not a verdict.
5. Verdict is non-binding decision support. Keep-current, no material rebalance, test-another, candidate failed/infeasible, and evidence-insufficient states are valid outcomes.
6. Report / AI Commentary uses grounded evidence only. It must not invent conclusions, imply an LLM decided, or treat missing evidence as if it exists.
7. Monitoring / What Changed can be mentioned as deferred or light report context, but it must not become a scheduler, alerting, or trading system.
8. Missing, partial, stale, blocked, and evidence-insufficient states must be visible and distinct.
9. Client Fit status, Diagnostic Quality status, and Decision Action are separate concepts. A Client Fit pass must not hide material diagnostic issues, and a Client Fit breach must not become trade advice.
10. Raw artifact filenames, JSON keys, schema names, booleans, backend IDs, run folder paths, and operator terms are implementer vocabulary, not primary UI copy.
11. Screen components consume display models (`reviewSummary`, stage summaries, and FastAPI public-envelope display models). Raw generated artifacts may be parsed only inside adapters, compatibility proxies, tests, or explicit operator/debug views.
12. Advanced, backend, generated support, and legacy capabilities must not be promoted into Core MVP navigation unless `PRODUCT_FLOW_CONTRACT.md`, `ARTIFACT_TO_SCREEN_MAP.md`, this contract, and owning specs are updated together.

## Shared forbidden primary UI language

Do not show these in normal screen hero copy, CTAs, primary cards, or empty states:

- Raw artifact names: `portfolio_xray.json`, `stress_report.json`, `client_fit_check.json`, `problem_classification.json`, `candidate_launchpad.json`, `portfolio_alternatives_builder.json`, `candidate_generation.json`, `current_vs_candidate.json`, `decision_verdict.json`, `ai_commentary_context.json`, `what_changed_summary.json`, `candidate_comparison.json`, `selection_decision.json`, `output_manifest.json`, `run_result.json`, `portfolio_weights.yml`, `monitoring_diff.json`.
- Raw JSON/schema terms: `schema_version`, `artifact_status`, `source_artifacts`, `field_path`, `view_mode`, `generation_status`, `validation_status`, `can_generate_candidate`, `decision_status`, `verdict_id`, `verdict_reason_id`, `selected_candidate_ids`, `requested_candidate_ids`, `backend_audit`, `loss_gate_mode`, `diagnostic_code`, `fail_reason_code`.
- Backend/operator terms: `backend`, `artifact`, `valid JSON`, `Review ID`, `frontend_review_*`, `analysis_subject`, `tombstone`, `factory`, `skipped_existing`, `optimizer arena`, `Selection Engine`, `Action Engine`, `Decision Journal` as a completed Core MVP screen.
- Raw booleans or placeholders: `true`, `false`, `null`, raw `n/a`, `outputs.*`, raw method IDs, raw candidate folder names, raw scenario IDs, and raw diagnosis IDs when a readable label exists.
- Advice/execution language: `buy`, `sell`, `execute`, `trade now`, `must rebalance`, `best portfolio`, `guaranteed improvement`, `tax advice`, `client suitability approved`.

Technical appendices, logs, or developer diagnostics may use artifact names only when clearly outside primary user-facing copy and only when the task explicitly targets operator diagnostics.

## Shared status taxonomy

Screens must translate backend statuses into user-facing status families.

| Family | Approved labels | Meaning |
| --- | --- | --- |
| Journey | Not started; Ready; Running; Complete; Blocked; Deferred | Whether the user can proceed to this step. |
| Evidence quality | Strong evidence; Partial evidence; Limited evidence; Unavailable; Stale / ignored; Evidence insufficient | Whether the screen has enough current evidence. |
| Risk / materiality | High; Medium; Low; Monitor; Data quality blocker | Severity of a diagnosis or decision issue. |
| Candidate | Setup only; Ready to test; Candidate generated; Candidate failed; Candidate infeasible; Ready to compare | State of the selected hypothesis and candidate attempt. |
| Comparison | Ready to compare; Comparing; Complete; Not comparable; Improved; Worsened; Similar; Unavailable; Not evaluated | State of current-vs-candidate evidence. |
| Client Fit | Within stated limits; Watch; Breach; Objective conflict; Not provided; Evidence insufficient | Non-binding personal-fit interpretation from provided profile evidence. |
| Verdict | Keep current / no-trade; No material rebalance; Rebalance review; Test another hypothesis; Candidate failed / infeasible; Evidence insufficient | Non-binding decision-support outcome. |
| Report | Grounded preview; Partial evidence; Evidence insufficient; Preview only; Export deferred | State of the report/explanation surface. |
| Monitoring | Deferred; First review; Changed; No material change; Retest suggested; Evidence gap; Monitoring unavailable | State of What Changed when surfaced later. |

## Screen-level contracts

### 1. Client Profile

| Item | Contract |
| --- | --- |
| Route | `/client-profile`. |
| Product role | Capture who the portfolio is for before diagnosis: stated objective, horizon, suggested preset, editable target return, volatility comfort range, maximum temporary loss, and source-quality disclosure. |
| Primary user question | "Who is this portfolio for..." |
| Artifacts / evidence | User-entered Client Fit V1 profile request object; no portfolio diagnostics yet. |
| Primary adapter / owner | `frontend/app/client-profile/page.tsx`; `frontend/lib/reviewState.tsx`; `frontend/lib/server/fastapiBridge.ts` for forwarding the bounded request object. |
| Must show | Mandatory questionnaire inputs; suggested preset; editable target rows; profile confidence/source quality; clear planning-profile disclaimer. |
| Must not show | Portfolio diagnostics, candidate evidence, suitability approval, optimizer mandates, tax settings, or generated artifact details. |
| Primary CTA | Save profile and continue to Portfolio Input. |
| Next step | `/portfolio-input` after a valid profile exists. |
| Empty / blocked state | Invalid ranges stay on the page with a plain validation message. |
| Forbidden terms | `client_fit_check.json`, raw source-artifact fields, optimizer constraints, suitability approval, trade/execution language. |
| Current mismatch to control | The profile can be mistaken for an investment mandate. Copy must state it is diagnostic context only. |
| QA checks | Verify `/portfolio-input` is locked until Client Profile is complete; changing the profile clears stale diagnosis/candidate/comparison/verdict/report state; no portfolio diagnosis appears on this page. |

### 2. Portfolio Input

| Item | Contract |
| --- | --- |
| Route | `/portfolio-input`. |
| Product role | Capture the factual current portfolio to diagnose. This is not an optimizer setup, policy mandate, or constraints screen. |
| Primary user question | "What portfolio am I asking Portfolio MRI to diagnose..." |
| Artifacts / evidence | User input payload plus bounded Client Fit profile request; resolved `analysis_setup` / `input_assumptions` after diagnosis; run-local frontend review result. |
| Primary adapter / owner | `frontend/components/portfolio/PortfolioInputTable.tsx`; `frontend/app/api/portfolio/diagnose/route.ts`; `frontend/lib/reviewState.tsx` for active review state. |
| Must show | Compact Client Fit profile chip with edit link; holdings table; instrument label; weight; reporting currency; weight-total validation; clear current-portfolio boundary; Run diagnosis CTA; plain-language assumptions note. |
| Must not show | Optimizer targets, full constraint panels, tax settings, suitability approval, raw config fields, raw request JSON, root legacy policy weights as manual input, or generated policy weights as user input. |
| Primary CTA | Run diagnosis. |
| Next step | `/diagnosis` after valid input and completed diagnosis run. Stay on input when validation or diagnosis fails. |
| Empty / blocked state | Ask for Client Profile first; ask for at least two positive holdings; explain invalid weights; explain unsupported instruments; preserve user input after analysis failure without raw backend details. |
| Forbidden terms | `config.yml`, `analysis_subject`, `analysis_mode`, `valid JSON`, `Review ID`, `frontend_review_*`, `cash_proxy_ticker`, `run_result.json`, `portfolio_weights.yml`, raw traceback labels. |
| Current mismatch to control | Recovery metadata and run-local IDs can leak operator language; input can drift toward optimizer setup if advanced fields become primary. |
| QA checks | Verify `/client-profile` is first in `frontend/lib/journey.ts`; invalid weights or missing Client Fit profile do not proceed; successful run clears stale candidate/comparison/verdict/report state; no raw review folder or JSON vocabulary appears in primary copy. |

### 3. Portfolio X-Ray / Diagnosis

| Item | Contract |
| --- | --- |
| Route | `/diagnosis`. |
| Product role | Explain what the current portfolio owns, what drives risk, and what looks weak before candidate testing. Includes the Problem Classification bridge as a transition, not a separate route. |
| Primary user question | "What is actually inside my current portfolio, and what looks risky or weak..." |
| Artifacts / evidence | `analysis_subject/portfolio_xray.json`; compact `analysis_subject/problem_classification.json`; input/assumptions summary; stress evidence only as a cited cross-reference when already available. |
| Primary adapter / owner | `frontend/lib/reviewState.tsx`; Diagnosis page/components; `frontend/lib/displayLabels.ts` for label cleanup. |
| Must show | Diagnosis hero; current portfolio identity; reporting currency/window when available; allocation; concentration; risk/return/drawdown summary; factor exposure; hidden exposure; risk budget; weakness map; Problem Classification bridge; data limitations. |
| Must not show | Candidate cards as if they are recommendations; Portfolio Health Score as the main answer; root legacy X-Ray as subject truth; raw block IDs as labels; any rebalance verdict. |
| Primary CTA | Continue to Stress Test Lab. |
| Next step | `/evidence` when X-Ray evidence exists or partial evidence is clearly disclosed. |
| Empty / blocked state | If no diagnosis run exists, return to Input. If X-Ray is partial, show available sections and mark missing sections as limited/unavailable. If Problem Classification is absent, show X-Ray evidence and say the diagnosis bridge is unavailable for this run. |
| Forbidden terms | `portfolio_xray.json`, `problem_classification.json`, `block_2_1_asset_allocation`, `block_2_6_portfolio_weakness_map`, `sections.hidden_risk_detector`, `legacy_summary`, `backend_audit`, raw diagnosis IDs, raw backend section statuses. |
| Current mismatch to control | Problem Classification has no dedicated route and can be underplayed; adapter fallback can mix product blocks and legacy sections; route must not become an action/rebalance screen. |
| QA checks | Confirm `/diagnosis` uses active review state, not root policy artifacts; Problem Classification appears as a bridge; screen contains no candidate generation CTA; forbidden block/artifact terms are absent from primary UI. |

### 4. Stress Test Lab

| Item | Contract |
| --- | --- |
| Route | `/evidence`. Product label is Stress Test Lab. |
| Product role | Stress-test the current portfolio and show whether X-Ray weaknesses matter under market shocks. |
| Primary user question | "Where can this portfolio break, under which scenarios, and why..." |
| Artifacts / evidence | `analysis_subject/stress_report.json`; scenario library sidecars where available; `portfolio_xray.json` and `problem_classification.json` only for bridge context. |
| Primary adapter / owner | `frontend/components/evidence/stressLabModel.ts`; Stress Lab components; `frontend/lib/displayLabels.ts`; `frontend/lib/reviewState.tsx` summary fields. |
| Must show | Stress hero; worst meaningful scenario; evidence quality; historical and synthetic scenario availability; loss/drawdown by scenario; helped/hurt contributors; hedge gap; stress scorecard summary in current-portfolio terms; X-Ray-to-Stress bridge; data limitations. |
| Must not show | Generic backend evidence dashboard; mandate pass/fail semantics; `DIAG_*`; raw scenario IDs; root legacy stress files; candidate comparison or verdict content. |
| Primary CTA | Continue to Client Fit. |
| Next step | `/client-fit` after stress evidence is reviewed. If stress evidence is unavailable, classify the gap as a limitation/blocker and do not invent stress conclusions. |
| Empty / blocked state | No stress evidence returns to Input/Diagnosis; partial historical data says some past crises cannot be replayed; unavailable synthetic rows are labelled as evidence gaps, not app failure. |
| Forbidden terms | `stress_report.json`, `scenario_results`, `historical_results`, `current_portfolio_stress_scorecard_v1`, `stress_scorecard_v1`, `loss_gate_mode`, `DIAG_*`, `fail_reason_code`, `pnl_by_asset`, `beta_rr`, raw scenario IDs such as `recession_severe` or `equity_shock`. |
| Current mismatch to control | Route name is `/evidence` while product screen is Stress Test Lab; raw stress IDs or mandate statuses can leak if adapter normalization regresses. |
| QA checks | Verify `/evidence` labels the page as Stress Test Lab; scenario names are readable; historical/synthetic unavailable states are distinct; next CTA leads to Client Fit; no candidate/verdict CTA appears before Hypothesis; forbidden scenario/backend terms are absent from primary UI. |

### 5. Client Fit

| Item | Contract |
| --- | --- |
| Route | `/client-fit`. |
| Product role | Compare objective portfolio evidence against the provided profile after Stress Test Lab and before Hypothesis. |
| Primary user question | "Does this risk fit the provided profile..." |
| Artifacts / evidence | Bounded FastAPI/adapter `client_fit` display summary derived from `analysis_subject/client_fit_check.json`; no raw artifact copy in primary UI. |
| Primary adapter / owner | `frontend/app/client-fit/page.tsx`; `frontend/lib/reviewState.tsx`; FastAPI public `ClientFitDisplaySummary`. |
| Must show | Four visible sections: `Your stated profile`, `Portfolio vs your limits`, `What this means`, and `Next best test`; status label/tone; target rows; source-quality disclosure; decision boundary. |
| Must not show | Raw `client_fit_check.json`, raw context/schema/source-artifact fields, suitability approval, optimizer mandate, trade instruction, or verdict. |
| Primary CTA | Continue to Hypothesis when a provided Client Fit summary exists. |
| Next step | `/hypothesis`; missing profile routes back to `/client-profile`; insufficient evidence stays clearly labelled. |
| Empty / blocked state | Missing Client Fit profile or missing diagnosis evidence shows a locked state and explains that backend/CLI compatibility can still produce missing-profile output. |
| Forbidden terms | `client_fit_check.json`, `client_fit_context`, `schema_version`, `source_artifacts`, `field_path`, `suitable`, `approved`, `buy`, `sell`, `must rebalance`, `best portfolio`. |
| Current mismatch to control | Client Fit can be over-read as suitability approval or as the final decision. The screen must keep Client Fit Status separate from Diagnostic Quality and Decision Action. |
| QA checks | Verify all four required sections render; target rows use only green/amber/red status tones; missing profile blocks Hypothesis; no forbidden advice/suitability language appears. |

### 6. Hypothesis Builder

| Item | Contract |
| --- | --- |
| Route | `/hypothesis`. |
| Product role | Convert diagnosis and stress evidence into one selected test path, prepare the Builder setup, and optionally generate one diagnostic candidate attempt. |
| Primary user question | "What should we test to see whether the portfolio can be improved, and what exactly will be tested..." |
| Artifacts / evidence | `analysis_subject/problem_classification.json`; `analysis_subject/candidate_launchpad.json`; `analysis_subject/portfolio_alternatives_builder.json`; same-run `candidate_generation.json` only after explicit user action. |
| Primary adapter / owner | `frontend/app/hypothesis/page.tsx`; `frontend/components/hypothesis/HypothesisCard.tsx`; `frontend/lib/reviewState.tsx`; `frontend/lib/displayLabels.ts`; Builder prepare and candidate generate API routes. |
| Must show | Primary diagnosis recap; bounded Client Fit overlay as context separate from diagnosis; hypothesis cards; evidence behind each test path; suggested method in plain language; success criteria; Client Fit target criteria when available; trade-off to watch; skip rule; selected test setup; setup validation; candidate-is-not-recommendation boundary; Generate candidate CTA only when ready; generated/failed/infeasible candidate state after explicit action. |
| Must not show | Full optimizer zoo; disabled backend method catalog; candidate as recommended portfolio; weights before generation; comparison/verdict results; Client Fit targets as optimizer mandates; advanced settings such as tax-aware optimization, turnover-aware objective, robust lambda, leverage, shorting, or full custom constraints UI. |
| Primary CTA | Select test path; Prepare setup; Generate test candidate when setup is ready. |
| Next step | `/comparison` only when one active candidate attempt is generated and compare-ready. Monitor-only/data-quality paths should route to report/monitor language or explain why candidate generation is blocked. |
| Empty / blocked state | No diagnosis asks user to complete Diagnosis/Evidence; missing Client Fit asks user to open Client Fit; no launchpad cards says no testable hypothesis is available; data-quality blocker says better data is needed; monitor-only diagnosis does not force a candidate; blocked setup explains the blocker. |
| Forbidden terms | `candidate_launchpad.json`, `portfolio_alternatives_builder.json`, `candidate_generation.json`, `card_type`, `launch_status`, `candidate_generation_allowed`, `can_generate_candidate`, `builder_mode`, `validation_status`, `source_diagnosis_id`, `source_card_id`, `source_builder_setup_id`, `is_rebalance_recommendation`, `true`, `false`, raw method IDs, `outputs.candidate_launchpad`, `factory`, `skipped_existing`, `weights.json`, raw candidate folder names. |
| Current mismatch to control | Launchpad, Builder, and Candidate Generation are merged into one route; raw setup fields can make the screen feel like an internal config panel or optimizer cockpit. |
| QA checks | Verify selecting a different hypothesis clears downstream candidate/comparison/verdict/report readiness; Generate candidate is hidden or disabled when setup is blocked; generated candidate copy says diagnostic test only; Client Fit pass does not hide structural issue copy; comparison remains locked until same-run candidate is available; forbidden setup/backend/advice terms are absent from primary UI. |

### 7. Current vs Candidate Comparison

| Item | Contract |
| --- | --- |
| Route | `/comparison`. |
| Product role | Compare the diagnosed current portfolio against the selected generated candidate and explain trade-offs before a verdict. |
| Primary user question | "Did the tested candidate improve the problem enough, and what did it make worse..." |
| Artifacts / evidence | Same-run `current_vs_candidate.json`; same-run `candidate_generation.json`; product-scoped `candidate_comparison.json` only behind adapters where needed. |
| Primary adapter / owner | `frontend/app/comparison/page.tsx`; `frontend/components/comparison/CandidateComparisonPanel.tsx`; `frontend/components/comparison/TradeoffSummary.tsx`; `frontend/lib/reviewState.tsx`; comparison API route. |
| Must show | Current portfolio label; selected candidate label; comparison availability; bounded Client Fit overlay and Current vs Candidate vs Client Target rows when Client Fit evidence exists; success-criteria result; what improved; what worsened; what stayed similar; risks reduced/added; turnover/cost practicality when available; materiality for decision review; unavailable metrics; candidate-not-recommendation boundary. |
| Must not show | Candidate generation controls; final verdict; "winner" language; suitability approval; multi-candidate arena; batch rankings; fake `n/a` conclusions; stale comparison from another candidate; Selection Engine statuses. |
| Primary CTA | Run diagnostic comparison when ready; Continue to Verdict when comparison is current and either has usable trade-off metrics or can safely produce an evidence-insufficient verdict. |
| Next step | `/verdict` when same-run comparison is complete or when the system can safely produce an evidence-insufficient / candidate-failed verdict. |
| Empty / blocked state | No candidate returns to Hypothesis; candidate not comparable explains why; diagnosis-only tombstones say no active candidate comparison for this review; missing metrics are shown per metric, not as fabricated conclusions; failed comparison offers retry or setup review. |
| Forbidden terms | `current_vs_candidate.json`, `candidate_comparison.json`, `selection_decision.json`, `view_mode`, `diagnosis_only`, `one_candidate`, `shortlist`, `selected_candidate_ids`, `requested_candidate_ids`, `dimensions[]`, `materiality_for_decision_review`, `not_evaluated`, `unavailable_reason`, raw candidate IDs when labels exist. |
| Current mismatch to control | Summary-only mapping can hide unavailable criteria; stale or mismatched comparison artifacts can unlock downstream screens if lineage checks regress. |
| QA checks | Verify comparison requires same selected card and candidate as active generation; no verdict or report readiness is set by stale comparison; unavailable metrics render as unavailable/not evaluated; Client Fit target evidence remains context rather than a verdict; "Continue to verdict" only appears after valid current comparison; forbidden comparison/backend/advice terms are absent from primary UI. |

### 8. Decision Verdict

| Item | Contract |
| --- | --- |
| Route | `/verdict`. |
| Product role | Translate comparison evidence into non-binding decision support. |
| Primary user question | "Given the evidence, should I keep the current portfolio, review this rebalance, test another idea, or stop because evidence is insufficient..." |
| Artifacts / evidence | Same-run `decision_verdict.json`; same-run `current_vs_candidate.json`; same-run `candidate_generation.json`; `selection_decision.json` only as translated backend evidence if needed. |
| Primary adapter / owner | `frontend/app/verdict/page.tsx`; `frontend/components/verdict/VerdictPanel.tsx`; `frontend/lib/reviewState.tsx`; verdict API route. |
| Must show | Verdict hero with accepted outcome; concise rationale; bounded Client Fit overlay as one input to the verdict; evidence used; improvements and worsening; materiality and success criteria; confidence and limitations; no-trade explanation where applicable; evidence-insufficient explanation where applicable; what would change the verdict; decision-support guardrail; next CTA. |
| Must not show | Trading instruction; best-portfolio ranking; suitability approval; tax advice; raw verdict IDs; full Action Plan; hidden comparison trade-offs; stale/mismatched verdicts. |
| Primary CTA | Generate report; or Test another hypothesis / Return to comparison when evidence is insufficient or mixed. |
| Next step | `/report` for grounded explanation when verdict is current, or back to `/hypothesis` / `/comparison` when the safe outcome is test-another or evidence-insufficient. |
| Empty / blocked state | No comparison asks user to compare first; failed/infeasible candidate can produce evidence-insufficient language; unknown backend status maps to Evidence insufficient; stale verdict asks user to regenerate for the active review. |
| Forbidden terms | `decision_verdict.json`, `selection_decision.json`, `decision_status`, `selection_decision_status`, `verdict_id`, `verdict_family`, `verdict_reason_id`, `selected_candidate`, `no_material_rebalance`, `data_review_required`, `mandate_risk_reduction`, `action_plan.json`, `execute`, `trade`, `best portfolio`. |
| Current mismatch to control | Backend decision IDs can leak through formatting; no-trade/evidence-insufficient must be treated as professional outcomes rather than failures; Client Fit pass can be over-read as enough to clear objective diagnosis. |
| QA checks | Verify verdict lineage matches same candidate/comparison; no raw decision IDs appear; no-trade and evidence-insufficient render as valid states; Client Fit pass plus a material diagnosis issue still shows monitor/review/test framing, not automatic no-action; action wording says decision support only; report CTA is not shown for stale/missing verdict evidence. |

### 9. Report / AI Commentary Grounding

| Item | Contract |
| --- | --- |
| Route | `/report`. |
| Product role | Present a grounded, client-readable explanation of the diagnosis, tested hypothesis, comparison, and verdict. |
| Primary user question | "Can I read a clear explanation of what was found, what was tested, and why the verdict says that..." |
| Artifacts / evidence | `ai_commentary_context.json`; same-run `decision_verdict.json`; same-run `current_vs_candidate.json`; diagnosis, stress, hypothesis, and candidate artifacts through allowed grounding references; optional `what_changed_summary.json` as a short deferred-monitoring note. |
| Primary adapter / owner | `frontend/app/report/page.tsx`; report components; report API route; future report adapter. |
| Must show | Executive summary; current portfolio diagnosis; stress evidence; hypothesis tested; candidate boundary; current-vs-candidate trade-offs; verdict explanation; evidence quality and limitations; grounding/source summary in user language; decision-support boundary; monitoring/deferred note. |
| Must not show | Ungrounded prose; "AI decided"; raw grounding package names; PDF/export absence as primary product result; completed Decision Journal; source artifact filenames in primary copy; invented missing conclusions. |
| Primary CTA | Generate grounded report preview; copy/export only if implemented and explicitly labelled as preview/export. |
| Next step | End with review/monitor note. Future Monitoring route may follow only after route contract approval. |
| Empty / blocked state | No verdict asks user to complete Verdict; unavailable grounding says report cannot be generated yet; partial context generates only supported sections; no PDF support says preview/export deferred in plain language, not operator copy. |
| Forbidden terms | `ai_commentary_context.json`, `grounded_ai_commentary_context`, `client_explanation_draft_v1`, `does_not_call_llm`, `field_path`, `evidence package type(s)`, `No PDF generation`, `Decision Journal` as completed product, raw source artifact names, unsupported LLM claims. |
| Current mismatch to control | Report context can expose prototype/operator phrases; report results may be transient in frontend state; monitoring artifact is optional and deferred. |
| QA checks | Verify report is generated only from current verdict context; unsupported sections are omitted or marked partial; no raw source package names appear in primary copy; no PDF/export wording implies a broken product; forbidden grounding terms are absent. |

### 8. Deferred Monitoring / What Changed

| Item | Contract |
| --- | --- |
| Route | **Deferred.** No current MVP route/component is active. Future route may be `/monitoring` or `/what-changed` only after a route decision. |
| Product role | Explain what changed since the prior review and what should be retested or watched. |
| Primary user question | "What changed since the last portfolio review, and do I need to retest anything..." |
| Artifacts / evidence | `what_changed_summary.json`; `monitoring_diff.json`; optional verdict/problem/comparison context. |
| Primary adapter / owner | No active screen adapter. Future Monitoring adapter must be added before user-facing route promotion. Report may show a short grounded note if evidence exists. |
| Must show when later surfaced | What changed headline; current/prior review dates if available; changed risk contributor; changed stress behavior; changed market context if available; changed verdict/action status if available; retest triggers; warnings; boundary note that monitoring prompts review, not trades. |
| Must not show | Scheduler, broker alerts, automatic rebalance triggers, multi-client workspace semantics, full monitoring dashboard, or trade instructions. |
| Primary CTA | Retest relevant hypothesis / Start a new review, only after a Monitoring route is approved. |
| Next step | Return to Input/Diagnosis or retest a hypothesis. Until then, Report may end with a monitoring note. |
| Empty / blocked state | First review says future runs can show what changed; no monitoring evidence says no comparable snapshot exists; no route says Monitoring is deferred, not broken. |
| Forbidden terms | `what_changed_summary.json`, `monitoring_diff.json`, `monitoring/latest/analysis_snapshot.json`, `summary_status`, `missing_monitoring`, `retest_triggers`, `macro_regime_changed`, `top_risk_contributor_changed`, raw trigger IDs, `scheduler`, `alert`, `notification`, `rebalance_trigger` as trade instruction. |
| Current mismatch to control | Backend artifacts exist, but no current UI route exists. Absence must be treated as intentional deferred UI scope, not as a frontend bug. |
| QA checks | Verify no Monitoring navigation appears in current MVP; Report mentions Monitoring only as short grounded/deferred context; no scheduler/alert/trade semantics appear; future route promotion updates product-flow, artifact-map, screen, design, QA, and docs-sync contracts together. |

## Route and screen summary

| Screen | Route | MVP status | Primary artifacts | Primary CTA |
| --- | --- | --- | --- | --- |
| Client Profile | `/client-profile` | Core MVP Client Fit onboarding | Bounded Client Fit request profile | Save profile and continue |
| Portfolio Input | `/portfolio-input` | Core MVP | User input; Client Fit profile; diagnosis result; `analysis_setup` projection | Run diagnosis |
| Portfolio X-Ray / Diagnosis | `/diagnosis` | Core MVP | `portfolio_xray.json`; `problem_classification.json` bridge | Continue to Stress Test Lab |
| Stress Test Lab | `/evidence` | Core MVP | `stress_report.json` | Continue to Client Fit |
| Client Fit | `/client-fit` | Core MVP Client Fit screen | bounded `client_fit` display summary | Continue to Hypothesis |
| Hypothesis Builder | `/hypothesis` | Core MVP merged stage | `problem_classification.json`; `candidate_launchpad.json`; `portfolio_alternatives_builder.json`; same-run `candidate_generation.json` | Select / prepare / generate test candidate |
| Current vs Candidate Comparison | `/comparison` | Core MVP | same-run `current_vs_candidate.json`; same-run `candidate_generation.json` | Run comparison / Continue to verdict |
| Decision Verdict | `/verdict` | Core MVP | same-run `decision_verdict.json`; same-run `current_vs_candidate.json` | Generate report / test another |
| Report / AI Commentary Grounding | `/report` | Core MVP preview | `ai_commentary_context.json`; verdict/comparison/diagnosis grounding | Generate grounded report preview |
| Monitoring / What Changed | no current route | Deferred UI layer | `what_changed_summary.json`; `monitoring_diff.json` | Future retest/new review CTA only after route approval |

## Acceptance checklist for future screen changes

- [ ] The route list still matches the approved MVP chain or this contract and `PRODUCT_FLOW_CONTRACT.md` were updated for an intentional route change.
- [ ] The screen product role and primary user question are preserved.
- [ ] Current portfolio evidence appears before candidate evidence.
- [ ] Problem Classification remains a bridge into Hypothesis unless a later route decision changes it.
- [ ] `/hypothesis` remains the merged Launchpad / Builder / Candidate Generation stage unless a future `/candidate` route is explicitly approved.
- [ ] Comparison shows improvements, worsening, similar results, unavailable results, practicality, and materiality before Verdict.
- [ ] Verdict keeps no-trade and evidence-insufficient as valid outcomes.
- [ ] Report uses grounded evidence and does not imply unsupported AI generation.
- [ ] Monitoring / What Changed remains deferred unless a route decision promotes it.
- [ ] Missing, partial, blocked, stale, and evidence-insufficient states are visually and textually distinct.
- [ ] No raw artifact names, JSON keys, schema names, booleans, backend IDs, raw scenario IDs, or operator path strings appear in primary UI.
- [ ] Same-review, same-selected-card, same-candidate, and same-stage-order lineage is preserved before unlocking downstream screens.
- [ ] Public FastAPI response fields used by the screen are present in
  `docs/contracts/FASTAPI_SCREEN_MAPPING.json` and generated frontend API types are current.
- [ ] Screen code consumes display-ready models instead of parsing raw `reviewResult.outputs.*` or stage artifact internals directly.
- [ ] Documentation impact was checked against the dynamic doc-sync matrix in the active ExecPlan and `docs/contracts/DOC_SYNC_CONTRACT.md`.

## Validation for this contract

This session is documentation-only. Minimum checks after editing this contract:

```text
git diff --check
```

Required evidence check for this session:

```text
Get-ChildItem frontend/app -Directory
```

The route list must include `client-profile`, `portfolio-input`, `diagnosis`, `evidence`,
`client-fit`, `hypothesis`, `comparison`, `verdict`, and `report`, and must not include a current
`candidate`, `monitoring`, or `what-changed` route unless a later route decision updates this
contract.

Recommended checks when applying this contract to implementation:

```text
rg -n "portfolio_xray\\.json|stress_report\\.json|problem_classification\\.json|candidate_launchpad\\.json|portfolio_alternatives_builder\\.json|candidate_generation\\.json|current_vs_candidate\\.json|decision_verdict\\.json|ai_commentary_context\\.json|what_changed_summary\\.json|Review ID|frontend_review_|valid JSON|backend|artifact|true|false|n/a|best portfolio|must rebalance|trade now" frontend/app frontend/components frontend/lib
```

Frontend implementation sessions must also run the checks required by `TESTING.md`, `../../frontend/README.md`, `AGENTS.md`, and the relevant future `QA_CONTRACT.md`.
