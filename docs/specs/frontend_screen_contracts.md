# Portfolio MRI Frontend Screen Contracts

Status: **canonical frontend product contract** for Portfolio MRI / Portfolio X-Ray Core MVP screen behavior.

Scope: user-facing screen content, route-to-artifact mapping, required sections, empty states, copy boundaries, and badge/status language.

Non-scope: no backend schema migration, no frontend implementation requirement, no UI refactor, no generated-output refresh.

This document translates the current diagnosis-first Portfolio MRI product truth into frontend screen contracts. It does not rename backend files, JSON schemas, formulas, scenario definitions, or output artifacts. Backend artifact names are listed here for implementers only; they must not appear in normal user-facing UI copy.

## Source-of-truth order

Use this document for frontend screen requirements. When a field-level or formula-level question appears, defer to the owning spec:

- Current product flow and implementation boundary: `SPEC.md`, `OUTPUTS.md`, `RULES.md`.
- Input: `docs/specs/input_assumptions_spec.md`.
- Diagnosis / Portfolio X-Ray: `docs/specs/portfolio_xray_diagnostics_spec.md`, `docs/specs/portfolio_xray_layer_spec.md`.
- Evidence / Stress Test Lab: `docs/specs/stress_lab_layer_spec.md`, `docs/specs/stress_testing_spec.md`, `docs/specs/current_portfolio_stress_scorecard_spec.md`, `docs/specs/hedge_gap_analysis_spec.md`.
- Problem Classification and Launchpad: `docs/specs/block_4_diagnosis_v3_spec.md`, `docs/specs/problem_classification_spec.md`, `docs/specs/candidate_launchpad_spec.md`.
- Builder and Candidate: `docs/specs/portfolio_alternatives_builder_spec.md`, `docs/specs/builder_prefill_spec.md`, `docs/specs/candidate_setup_spec.md`, `docs/specs/candidate_generation_spec.md`.
- Comparison and Verdict: `docs/specs/current_vs_candidate_spec.md`, `docs/specs/decision_verdict_spec.md`.
- Report and grounding: `docs/specs/ai_commentary_grounding_spec.md`.
- Monitoring / What Changed: `docs/specs/light_monitoring_summary_spec.md`, `docs/specs/monitoring_spec.md`.
- Visual style: `docs/design/portfolio_mri_design_system.md`; root `DESIGN.md` is legacy visual reference for new Portfolio MRI UI.

## Canonical journey

```text
Input
-> Diagnosis / Portfolio X-Ray
-> Evidence / Stress Test Lab
-> Problem Classification bridge
-> Hypothesis
-> Candidate / Builder
-> Comparison
-> Verdict
-> Report
-> Monitoring / What Changed
```

Current MVP frontend route reality includes Client Fit onboarding and display screens:

```text
/client-profile -> /portfolio-input -> /diagnosis -> /evidence -> /client-fit -> /hypothesis -> /comparison -> /verdict -> /report
```

There is no separate `/candidate` route in the current MVP frontend. Candidate / Builder is intentionally documented as merged into `/hypothesis` for MVP until a later UI split is approved.

## Global frontend contract rules

1. The UI is diagnosis-first and current-portfolio-first. The current portfolio must be understood before any candidate is presented.
2. A candidate is a diagnostic hypothesis test, not a recommendation and not a trade order.
3. Builder setup is setup-only. It must not be worded as a generated portfolio, comparison, verdict, or action plan.
4. Comparison must show trade-offs: improved, worsened, unchanged, unavailable, and inconclusive areas.
5. Verdict is non-binding decision support. `no-trade`, `keep current`, `test another candidate`, and `evidence insufficient` are valid outcomes.
6. Missing or partial evidence is a valid product state. It must not look like a broken page unless the run itself failed.
7. Raw backend artifact names, raw JSON keys, backend labels, scenario IDs, booleans, and method IDs must not appear in primary user-facing UI copy.
8. Advanced/backend/legacy artifacts may support implementation or drill-down decisions, but must not become Core MVP navigation or screen hero content unless an owning spec promotes them.

## User-facing copy boundary

### Forbidden in primary UI

Do not show these terms, patterns, or raw labels to normal users:

- Artifact/file names: `portfolio_xray.json`, `stress_report.json`, `problem_classification.json`, `candidate_launchpad.json`, `portfolio_alternatives_builder.json`, `candidate_generation.json`, `current_vs_candidate.json`, `decision_verdict.json`, `ai_commentary_context.json`, `what_changed_summary.json`, `candidate_comparison.json`, `selection_decision.json`, `output_manifest.json`, `run_result.json`, `portfolio_weights.yml`, `monitoring_diff.json`.
- Raw JSON/schema terms: `schema_version`, `artifact_status`, `not_authoritative`, `product_run`, `source_artifacts`, `field_path`, `view_mode`, `generation_status`, `validation_status`, `can_generate_candidate`, `is_rebalance_recommendation`, `decision_status`, `verdict_id`, `verdict_reason_id`, `selected_candidate_ids`, `requested_candidate_ids`, `backend_audit`, `loss_gate_mode`, `diagnostic_code`, `fail_reason_code`.
- Raw IDs or scenario IDs: `equity_shock`, `credit_shock`, `rates_shock`, `inflation_stagflation`, `liquidity_shock`, `usd_shock`, `commodity_shock`, `recession_severe`, `dotcom`, `2008`, `2020`, `2022`, `banking_2023`, `weak_crisis_resilience`, `poor_diversification`, `high_concentration`, `mixed_evidence_no_action`, `evidence_insufficient_data_quality`, raw `launchpad_*` IDs, raw candidate IDs when a readable label exists.
- Backend/operator language: `backend`, `valid JSON`, `compact summary`, `Review ID`, `frontend_review_*`, `artifact`, `schema`, `tombstone`, `factory`, `optimizer arena`, `Selection Engine`, `No-Trade artifact`, `Action Engine`, `Decision Journal` as a current MVP product screen.
- Boolean/raw field labels: `true`, `false`, `null`, `n/a`, `Card type`, `Default method`, `Validation status`, `Can generate candidate`, `Generates portfolio`, `Is rebalance recommendation`, `outputs.candidate_launchpad`.
- Advice/execution language: `buy`, `sell`, `execute`, `trade now`, `must rebalance`, `best portfolio`, `guaranteed improvement`, `tax advice`, `client suitability approved`.

### Preferred user-facing translations

| Raw/backend phrase | User-facing phrase |
| --- | --- |
| `portfolio_xray.json` | Portfolio X-Ray evidence |
| `stress_report.json` | stress-test evidence |
| `problem_classification.json` | main portfolio diagnosis |
| `candidate_launchpad.json` | hypothesis cards |
| `portfolio_alternatives_builder.json` | candidate test setup |
| `candidate_generation.json` | generated test candidate |
| `current_vs_candidate.json` | current-vs-candidate comparison |
| `decision_verdict.json` | decision verdict |
| `ai_commentary_context.json` | grounded explanation inputs |
| `what_changed_summary.json` | what changed summary |
| `Card type` | test type |
| `Default method` | starting test method |
| `Validation status` | setup check |
| `Can generate candidate` | ready to test |
| `Is rebalance recommendation: false` | not a rebalance recommendation |
| `Tradeoff to watch` | trade-off to review |
| `outputs.candidate_launchpad` | hypothesis cards for this review |
| `valid JSON` | request format was invalid |
| `Backend failure` | analysis engine error / review could not be completed |

## Global status and badge taxonomy

The UI must map backend statuses into the following user-facing badge families. Do not print raw backend enum values.

### Journey status

| Badge | Meaning | Typical source |
| --- | --- | --- |
| Not started | User has not completed the prerequisite step. | no active review state |
| Ready | The user can run the next step. | valid input, valid setup, comparable candidate |
| Running | A requested analysis step is in progress. | API call in flight |
| Complete | Evidence exists and is usable for this screen. | available artifact/result |
| Blocked | The step cannot proceed because required evidence or setup is not usable. | blocked Builder, failed candidate, data blocker |
| Deferred | Backend evidence may exist, but no MVP UI surface is active. | Monitoring / What Changed |

### Evidence quality

| Badge | Meaning |
| --- | --- |
| Strong evidence | Required evidence is present, current, and internally consistent. |
| Partial evidence | Enough evidence exists to explain the screen, but some sections are missing or limited. |
| Limited evidence | The screen can be shown, but conclusions require caution. |
| Unavailable | Required evidence for this section does not exist. |
| Stale / ignored | Evidence exists but does not belong to the active review or stage. |
| Evidence insufficient | The product cannot support a comparison or verdict from available evidence. |

### Risk / materiality severity

| Badge | Meaning |
| --- | --- |
| High | Material current-portfolio risk or decision issue requiring review. |
| Medium | Meaningful issue; review but do not overstate urgency. |
| Low | Minor or watch-list issue. |
| Monitor | No immediate candidate test is required; continue watching. |
| Data quality blocker | Evidence quality prevents a reliable candidate test or verdict. |

### Candidate and verdict status

| Badge | Meaning |
| --- | --- |
| Setup only | Builder has prepared a test; no candidate is generated yet. |
| Ready to test | The selected setup can generate one candidate attempt. |
| Candidate generated | One diagnostic candidate exists for comparison. |
| Candidate failed | The attempt failed; preserve the reason and do not use stale weights. |
| Candidate infeasible | The requested setup cannot produce a usable candidate. |
| Ready to compare | Candidate evidence is available for current-vs-candidate comparison. |
| Review candidate | Candidate evidence is material enough for decision review. |
| Not material | Evidence does not justify a rebalance review. |
| Keep current / no-trade | Staying with the current portfolio is a valid decision-support outcome. |
| Test another hypothesis | Evidence is inconclusive or the tested candidate is not enough. |
| Evidence insufficient | The system cannot support an action/no-action conclusion. |
| Rebalance review | Evidence supports reviewing a rebalance; still not a trade order. |

## Screen contracts

### 1. Input

| Item | Contract |
| --- | --- |
| Route | `/portfolio-input` (current MVP route; `/input` may be a future alias only after a route decision). |
| Product role | Capture the factual current portfolio to diagnose. This is not an optimizer setup screen. |
| Primary user question | "What portfolio am I asking Portfolio MRI to diagnose?" |
| Backend artifacts used | User input payload; runtime `analysis_setup` / `input_assumptions` projection after diagnosis; frontend API diagnosis result; active run-local review folder. |
| MVP status | **Core MVP**. |
| Next step in journey | Diagnosis / Portfolio X-Ray (`/diagnosis`) after valid input and successful diagnosis run. |

Required sections:

- Portfolio holdings table with instrument, display name when available, and weight.
- Reporting currency.
- Weight total and validation result.
- Clear current-portfolio boundary: diagnose existing allocation as-is.
- Run diagnosis CTA.
- Data and assumptions note: only instruments, allocation, and reporting currency are Core MVP user inputs.
- Recovery/import state only if worded as read-only recovery, not as primary workflow.

Core fields / evidence required:

- At least two positive holdings.
- Weights summing to 100% within accepted UI tolerance.
- Recognized instruments from the local instrument universe or an explicit accepted cash label.
- `investor_currency`.
- Real-cash labels displayed as portfolio cash, not as a cash-proxy ETF.

Optional/detail fields:

- Instrument asset class, region, currency, and risk role if available from taxonomy.
- Advanced settings link, collapsed by default; not required for Core MVP diagnosis.
- Read-only recovered review metadata, translated into user language.

Empty/unavailable state:

- No holdings: "Add at least two holdings to diagnose your current portfolio."
- Invalid weights: explain the exact weight issue in user terms.
- Unknown instrument: ask user to select a supported instrument or cash label.
- Analysis engine error: explain that the review could not be completed and preserve input; do not show raw request/JSON/backend details.

Forbidden user-facing terms:

- `config.yml`, `analysis_subject`, `analysis_mode`, `valid JSON`, `Review ID`, `frontend_review_*`, `cash_proxy_ticker`, `run_result.json`, `portfolio_weights.yml`, raw traceback or backend error labels.

Status/badge taxonomy:

- Input incomplete, Input valid, Ready to diagnose, Diagnosis running, Diagnosis failed, Diagnosis complete.
- Evidence quality is not shown before diagnosis except as input validation.

### 2. Diagnosis / Portfolio X-Ray

| Item | Contract |
| --- | --- |
| Route | `/diagnosis`. |
| Product role | Explain what the current portfolio owns, what drives risk, and what the main current-portfolio problem appears to be before any candidate. |
| Primary user question | "What is actually inside my current portfolio, and what looks risky or weak?" |
| Backend artifacts used | `portfolio_xray.json`; compact `problem_classification.json` bridge; input/assumptions summary; stress evidence only as cross-reference where X-Ray sections already cite it. |
| MVP status | **Core MVP**. |
| Next step in journey | Evidence / Stress Test Lab (`/evidence`) to test the diagnosis under stress. |

Required sections:

- Diagnosis hero: current portfolio, analysis window/currency if available, and one plain-language top finding.
- What you own: asset-level and grouped allocation.
- Risk profile: return/risk/drawdown summary where available.
- Factor exposure: major factor sensitivities and limitations.
- Hidden exposure: duplicate, concentration, or correlation-style risks.
- Risk budget: capital weight versus risk contribution.
- Portfolio weakness map: the main pre-stress weaknesses.
- Problem Classification bridge: a compact "main diagnosis so far" card, placed at the bottom of Diagnosis as the transition into Evidence and Hypothesis.
- Data limitations / evidence quality.

Problem Classification placement:

- Primary placement for MVP: **Diagnosis bridge card**, after X-Ray sections and before navigation to Evidence.
- Evidence screen must reference the same diagnosis as stress confirmation or challenge, but must not own the primary classification.
- Hypothesis screen must consume the selected/primary diagnosis to show testable hypotheses.
- Do not create a separate Problem Classification route for MVP unless a later route spec changes the journey.

Core fields / evidence required:

- Block 2.1 allocation: holdings, top holdings, grouped exposure, concentration flags.
- Block 2.2 metrics: CAGR/return, volatility, drawdown, Sharpe or equivalent available risk metrics, with caveats.
- Block 2.3 factor exposure summary and confidence/coverage.
- Block 2.4 hidden exposure alerts.
- Block 2.5 risk budget contributors.
- Block 2.6 weakness map summary and severity.
- Problem Classification: primary diagnosis, root cause, key evidence, confidence, materiality, actionability, suggested hypothesis, next diagnostic step.

Optional/detail fields:

- Method/window/frequency details in plain language.
- Legacy `sections.*` evidence only when product blocks are absent, labelled as limited compatibility evidence.
- Source/evidence drill-down in non-primary UI; still use product labels, not filenames.

Empty/unavailable state:

- No diagnosis run: prompt user to complete Input first.
- X-Ray partial: show available sections and mark missing sections as limited/unavailable.
- Problem Classification absent: show X-Ray evidence and state that the diagnosis bridge is not available for this run; next step can still be Stress Lab if stress evidence exists.
- Stale root policy artifacts must not be used as current-portfolio diagnosis.

Forbidden user-facing terms:

- `portfolio_xray.json`, `block_2_1_asset_allocation`, `block_2_6_portfolio_weakness_map`, `sections.hidden_risk_detector`, `legacy_summary`, `backend_audit`, `problem_classification.json`, raw diagnosis IDs, `implemented`, `degraded`, `unavailable` as raw backend section statuses unless translated through badge taxonomy.

Status/badge taxonomy:

- Evidence quality: Strong evidence, Partial evidence, Limited evidence, Unavailable.
- Risk/materiality: High, Medium, Low, Monitor, Data quality blocker.
- Diagnosis bridge: Main issue, Secondary issue, Monitor, Data quality blocker.

### 3. Evidence / Stress Test Lab

| Item | Contract |
| --- | --- |
| Route | `/evidence`. |
| Product role | Stress-test the current portfolio and show whether X-Ray weaknesses matter under market shocks. |
| Primary user question | "Where can this portfolio break, under which scenarios, and why?" |
| Backend artifacts used | `stress_report.json`; optional `scenario_library.json` / `scenario_library_normalized.json` as supporting evidence; `portfolio_xray.json` and `problem_classification.json` only for bridge context. |
| MVP status | **Core MVP**. |
| Next step in journey | Hypothesis (`/hypothesis`) after the user understands the stress evidence and main diagnosis. |

Required sections:

- Stress Lab hero: worst meaningful stress result, confidence, and whether stress confirms or challenges the diagnosis.
- Scenario library: readable scenario names grouped into historical and hypothetical scenarios.
- Stress results: current-portfolio loss/drawdown by scenario where available.
- Worst scenario detail: loss, main drivers, and limitations.
- Assets hurt / helped: contributors and offsets.
- Hedge gap: whether protective assets offset losses.
- Stress scorecard summary: phrase as "current-portfolio stress summary," not a generic robustness scorecard.
- X-Ray to Stress bridge: which X-Ray weaknesses were confirmed, not confirmed, or unavailable.
- Data limitations and stress methodology note.

Core fields / evidence required:

- Historical scenario rows or explicit insufficient-overlap state.
- Synthetic scenario rows or explicit unavailable state.
- Worst scenario selector and loss magnitude when available.
- Top negative contributors and any positive offsets.
- Hedge gap / offset coverage summary.
- Stress diagnosis confidence and warning list.
- Link back to primary diagnosis in plain language.

Optional/detail fields:

- Factor stress attribution.
- Scenario methodology and proxy/coverage notes.
- Crisis replay paths only as advanced/deferred detail, not Core MVP hero.
- Scenario library normalized readiness, translated into user terms.

Empty/unavailable state:

- No stress evidence: prompt to run diagnosis/stress; do not show old root policy stress files.
- Partial historical data: state that some past crises cannot be replayed due to insufficient overlap.
- Synthetic unavailable: state which evidence category is missing without printing scenario IDs.
- Stress warnings: show as evidence limitations, not as application failure.

Forbidden user-facing terms:

- `stress_report.json`, `scenario_results`, `historical_results`, `current_portfolio_stress_scorecard_v1`, `stress_scorecard_v1`, `loss_gate_mode`, `DIAG_*`, `fail_reason_code`, scenario IDs such as `recession_severe` or `equity_shock`, `pnl_by_asset`, `beta_rr`, `shock_eq`, raw pass/fail mandate terms on Core MVP paths.

Status/badge taxonomy:

- Stress evidence: Available, Partial, Insufficient overlap, Unavailable.
- Stress severity: High stress risk, Medium stress risk, Low stress risk, Monitor.
- Bridge status: Confirms diagnosis, Partly confirms, Does not confirm, Evidence unavailable.

### 4. Hypothesis

| Item | Contract |
| --- | --- |
| Route | `/hypothesis`. |
| Product role | Convert the diagnosis into one or more testable hypotheses without implying a rebalance recommendation. |
| Primary user question | "What should we test to see whether the portfolio can be improved?" |
| Backend artifacts used | `problem_classification.json`, `candidate_launchpad.json`, `portfolio_alternatives_builder.json` for selected-card setup; `candidate_generation.json` only because Candidate / Builder is merged into this route for MVP. |
| MVP status | **Core MVP**, with Candidate / Builder **merged** into this screen for MVP. |
| Next step in journey | Comparison (`/comparison`) after one selected hypothesis has a generated candidate; otherwise stay on Hypothesis or return to Evidence. |

Required sections:

- Main diagnosis recap: one plain-language problem and why it matters.
- Hypothesis cards: maximum three visible test cards for the current MVP contract.
- Each card must show: hypothesis to test, why this test, success criteria, trade-off to review, when to skip, and decision boundary.
- Not-a-recommendation boundary on every card or card group.
- Selected hypothesis state.
- Builder setup preview for the selected card, because Candidate / Builder is merged here for MVP.
- Data-quality or monitor-only blocked state when candidate generation should not proceed.

Core fields / evidence required:

- Primary diagnosis and next diagnostic step.
- Launchpad card hypothesis, status, suggested method(s), success criteria, trade-off, skip rule, decision boundary.
- Builder setup status, selected method label, constraint preset label, min/max weight if user-adjustable, validation warnings.
- Candidate-generation readiness only as "ready to test," not as automatic generation.

Optional/detail fields:

- Secondary hypotheses.
- Method explanation in plain language.
- Setup assumptions and simple constraints.
- Why reference tests such as equal weight or risk parity are used, if selected.

Empty/unavailable state:

- No diagnosis: prompt user to complete Diagnosis/Evidence first.
- No launchpad cards: explain that no testable hypothesis is available for this review.
- Data-quality blocker: say the portfolio needs better data before a candidate test is reliable.
- Monitor-only diagnosis: show monitoring/reference comparison option if provided; do not force a candidate.
- Builder setup missing: allow prepare/setup action if a card is selected and allowed.

Forbidden user-facing terms:

- `candidate_launchpad.json`, `portfolio_alternatives_builder.json`, `candidate_generation.json`, `card_type`, `launch_status`, `candidate_generation_allowed`, `can_generate_candidate`, `builder_mode`, `validation_status`, `source_diagnosis_id`, `source_card_id`, `is_rebalance_recommendation`, `true`, `false`, raw method IDs when a readable method label exists, `outputs.candidate_launchpad`.

Status/badge taxonomy:

- Hypothesis status: Ready to test, Reference test, Monitor, Data quality blocker, Not available.
- Setup status: Setup only, Ready to test, Blocked, Needs review.
- Recommendation boundary: Not a recommendation, Diagnostic test only.

### 5. Candidate / Builder

| Item | Contract |
| --- | --- |
| Route | **Merged into `/hypothesis` for MVP.** Future split route, if approved: `/candidate`. |
| Product role | Prepare and run exactly one diagnostic candidate attempt from the selected hypothesis. |
| Primary user question | "What candidate test did we generate, and is it ready to compare against the current portfolio?" |
| Backend artifacts used | `portfolio_alternatives_builder.json`, `candidate_generation.json`, candidate weights/evidence from the selected generation attempt when available. |
| MVP status | **Merged with Hypothesis for Core MVP**. Separate screen is **deferred**. |
| Next step in journey | Comparison (`/comparison`) only when one active candidate attempt is generated and comparable. |

Candidate route policy:

- Current MVP has **no separate Candidate screen**. Candidate / Builder content belongs inside `/hypothesis` so the user sees diagnosis, hypothesis, setup, and one generated test in one place.
- The MVP must not add a visible `/candidate` navigation item unless a later UI change intentionally splits this stage.
- If split later, move these sections from `/hypothesis` to `/candidate`:
  - selected hypothesis recap;
  - Builder setup review and editable MVP setup fields;
  - method availability / construction limitations;
  - Generate candidate action;
  - generated candidate identity and weights;
  - candidate failed / infeasible state;
  - compare-readiness state;
  - candidate-is-not-recommendation boundary.
- Keep Hypothesis focused on choosing what to test if `/candidate` is later introduced.

Required sections while merged:

- Selected hypothesis recap.
- Bounded Client Fit overlay that stays separate from the structural diagnosis and setup constraints.
- Candidate setup summary: goal, method label, constraints, success criteria, trade-off, skip rule.
- Generate candidate CTA, visible only when setup is ready.
- Candidate result summary: candidate name, generated/failed/infeasible status, weights when available, and readiness to compare.
- Candidate boundary note: this is one diagnostic test, not a recommendation and not a ranking arena.
- Client Fit pass boundary: a fit result does not hide concentration, stress, drawdown, or other material diagnosis issues.

Core fields / evidence required:

- Builder setup: setup ID internally, selected card linkage internally, user-facing goal/hypothesis/method/constraints.
- Candidate attempt: candidate display name, method label, status, weights if generated, failure/infeasibility reason if not, handoff-to-comparison readiness.
- Freshness/lineage must be enforced by implementation; UI should show stale/ignored only as "not from this active review" if needed.

Optional/detail fields:

- Capped/uncapped explanation.
- Min/max asset weight.
- Constraint preset.
- Warnings about concentration, unavailable method, or construction limits.

Empty/unavailable state:

- No selected hypothesis: ask user to choose a hypothesis first.
- Setup blocked: show reason in plain language and do not show Generate candidate as available.
- Attempt failed/infeasible: explain reason and offer to review setup or test another hypothesis.
- Weights unavailable: show candidate attempt was created but cannot be compared yet.
- Stale candidate evidence: do not render it as current; ask user to regenerate for this review.

Forbidden user-facing terms:

- `CandidateSetup`, `candidate_setup_id`, `builder_prefill_id`, `source_card_id`, `source_builder_setup_id`, `generation_status`, `handoff_to_comparison`, `method_availability`, `factory`, `skipped_existing`, `weights.json`, `candidate_factory_run.json`, raw candidate folder names, optimizer-zoo language.

Status/badge taxonomy:

- Setup only, Ready to test, Candidate generated, Candidate failed, Candidate infeasible, Ready to compare, Stale / ignored.

### 6. Comparison

| Item | Contract |
| --- | --- |
| Route | `/comparison`. |
| Product role | Compare the current portfolio against the selected generated candidate and show trade-offs before a verdict. |
| Primary user question | "Did the tested candidate improve the problem enough, and what did it make worse?" |
| Backend artifacts used | `current_vs_candidate.json`; `candidate_generation.json` for hypothesis/weights context; technical `candidate_comparison.json` only as backend evidence behind the product adapter. |
| MVP status | **Core MVP** for one selected candidate. Full multi-candidate arena is **advanced/deferred**. |
| Next step in journey | Verdict (`/verdict`) after comparison is available or after the system determines evidence is insufficient. |

Required sections:

- Comparison hero: current portfolio vs selected candidate and comparison availability.
- Bounded Client Fit overlay and target-reference context when available.
- Success criteria result: met, not met, not evaluated, or unavailable.
- What improved.
- What worsened.
- What stayed similar / unchanged.
- Risks reduced and risks added.
- Practicality: turnover and estimated cost when available.
- Materiality for decision review.
- Evidence quality and unavailable metrics.
- Boundary note: comparison is evidence for a later verdict, not a recommendation.

Core fields / evidence required:

- Baseline/current label.
- Selected candidate label.
- Comparison status / view mapped to one-candidate user language.
- Dimension-level deltas for return, volatility, drawdown, Sharpe, stress loss, concentration, and factor behavior when available.
- `what_improved`, `what_worsened`, `what_stayed_similar`, `risk_reduced`, `risk_added` or their mapped equivalents.
- Success-criteria evaluation.
- Materiality gate: review candidate, not material, or insufficient evidence.
- Data quality / warnings.

Optional/detail fields:

- Metric table with current value, candidate value, and difference.
- Transaction-cost assumption explanation.
- Drill-down to candidate setup and hypothesis.
- Shortlist mode only if a future spec promotes it; otherwise one-candidate only.

Empty/unavailable state:

- No candidate: return to Hypothesis / Candidate setup.
- Candidate not comparable: show why comparison cannot run.
- Missing metrics: show unavailable per metric; do not invent improvement/worsening.
- Diagnosis-only tombstone / not-current evidence: show "No active candidate comparison for this review."
- Comparison failed: explain retry/review setup path.

Forbidden user-facing terms:

- `current_vs_candidate.json`, `candidate_comparison.json`, `selection_decision.json`, `view_mode`, `diagnosis_only`, `one_candidate`, `shortlist`, `selected_candidate_ids`, `requested_candidate_ids`, `dimensions[]`, `materiality_for_decision_review`, `not_evaluated`, `unavailable_reason`, raw candidate IDs when display labels exist.

Status/badge taxonomy:

- Comparison status: Ready to compare, Comparing, Complete, Evidence insufficient, Not comparable.
- Metric status: Improved, Worsened, Similar, Unavailable, Not evaluated.
- Materiality: Review candidate, Not material, Insufficient evidence.

### 7. Verdict

| Item | Contract |
| --- | --- |
| Route | `/verdict`. |
| Product role | Convert comparison evidence into a non-binding decision-support verdict. |
| Primary user question | "Given the evidence, should I keep the current portfolio, review this rebalance, test another idea, or stop because evidence is insufficient?" |
| Backend artifacts used | `decision_verdict.json`; `current_vs_candidate.json`; `candidate_generation.json` or `selection_decision.json` as backend decision evidence; optional action context only as support. |
| MVP status | **Core MVP**. |
| Next step in journey | Report (`/report`) for grounded explanation and decision record preview. |

Required sections:

- Verdict hero with one of the accepted product outcomes.
- Why this verdict: concise rationale summary.
- Evidence used: improvements, worsening, success criteria, materiality, turnover/cost, data quality.
- No-trade / keep-current explanation when applicable.
- Evidence-insufficient explanation when applicable.
- What would change the verdict.
- Guardrails: decision support only, no trade execution.
- Client Fit context as one verdict input, with explicit copy that a fit result does not clear material diagnosis.
- Next step CTA: generate report, test another hypothesis, return to comparison, or monitor.

Core fields / evidence required:

- Verdict label / outcome family translated into product language.
- Reviewed candidate label.
- Confidence and confidence limitations.
- Evidence summary from comparison.
- Guardrails proving no trade execution and no unsupported recommendation.
- No-trade metadata or evidence-insufficient reason when applicable.

Optional/detail fields:

- Source evidence summary grouped by diagnosis, candidate, comparison, and practicality.
- Action-plan context only if it supports wording; do not turn it into a Core MVP Action Plan screen.
- Legacy policy-mandate verdicts must be filtered or clearly labelled as legacy/policy-path if present.

Empty/unavailable state:

- No comparison: ask user to compare a candidate first.
- Candidate failed/infeasible: verdict may be Evidence insufficient; show why.
- Unknown backend decision status: map to Evidence insufficient, not raw unknown.
- Mismatched/stale verdict evidence: do not render as current; ask user to regenerate verdict.

Forbidden user-facing terms:

- `decision_verdict.json`, `selection_decision.json`, `decision_status`, `selection_decision_status`, `verdict_id`, `verdict_family`, `verdict_reason_id`, `selected_candidate`, `no_material_rebalance`, `data_review_required`, `mandate_risk_reduction`, `action_plan.json`, `execute`, `trade`, `best portfolio`.

Status/badge taxonomy:

- Keep current / no-trade.
- Rebalance review.
- Test another hypothesis.
- Evidence insufficient.
- Risk reduction required (legacy/policy-path only; not normal Core MVP one-candidate language).
- Confidence: High, Medium, Low, Limited by evidence.

### 8. Report

| Item | Contract |
| --- | --- |
| Route | `/report`. |
| Product role | Present a grounded, client-readable explanation of the diagnosis, tested hypothesis, comparison, and verdict. |
| Primary user question | "Can I read a clear explanation of what was found, what was tested, and why the verdict says that?" |
| Backend artifacts used | `ai_commentary_context.json`; `decision_verdict.json`; `current_vs_candidate.json`; diagnosis/stress/hypothesis artifacts through allowed grounding references. |
| MVP status | **Core MVP report preview / grounded explanation**. Polished PDF export and full Decision Journal are **advanced/deferred**. |
| Next step in journey | Monitoring / What Changed when a UI surface exists; otherwise end with review/monitoring note. |

Required sections:

- Executive summary.
- Current portfolio diagnosis.
- Stress evidence summary.
- Hypothesis tested and candidate boundary.
- Current vs candidate trade-offs.
- Decision Verdict explanation.
- Evidence quality and limitations.
- Grounding/source summary in user language.
- Decision-support boundary: not investment advice, not trade execution.
- Monitoring note: whether What Changed is available/deferred.

Core fields / evidence required:

- Deterministic explanation draft or equivalent grounded sentences.
- Evidence references translated into user-readable source categories.
- Warnings and missing evidence.
- Verdict and confidence limitations.
- Candidate not-a-recommendation boundary.

Optional/detail fields:

- Light decision record scaffold.
- Export/copy controls, if implemented later.
- Source references in a collapsed evidence appendix, using product labels rather than filenames.
- Monitoring trigger summary if a What Changed surface is later added.

Empty/unavailable state:

- No verdict: ask user to complete Verdict first.
- Grounding context unavailable: show report cannot be generated yet; do not generate ungrounded prose.
- Partial context: generate only supported sections and mark missing evidence.
- No PDF/export support: say preview only; do not show operator phrases like "No PDF generation".

Forbidden user-facing terms:

- `ai_commentary_context.json`, `grounded_ai_commentary_context`, `client_explanation_draft_v1`, `does_not_call_llm`, `field_path`, `evidence package type(s)`, `No PDF generation`, `Decision Journal` as a completed product, raw source artifact names in primary copy, LLM claims not supported by implementation.

Status/badge taxonomy:

- Report ready, Grounded preview, Partial evidence, Evidence insufficient, Preview only, Export deferred.

### 9. Monitoring / What Changed

| Item | Contract |
| --- | --- |
| Route | **Deferred.** No current MVP frontend route/component is active. Future route may be `/monitoring` or `/what-changed` only after a route decision. |
| Product role | Explain what changed since the prior review and what should be retested or watched. |
| Primary user question | "What changed since the last portfolio review, and do I need to retest anything?" |
| Backend artifacts used | `what_changed_summary.json`; `monitoring_diff.json`; optional `decision_verdict.json`, `problem_classification.json`, `current_vs_candidate.json`. |
| MVP status | **Deferred / Monitoring layer**. Backend artifact may exist; UI surface is intentionally deferred, not missing by accident. |
| Next step in journey | Return to Input/Diagnosis for a new review, or retest the relevant hypothesis when a future Monitoring surface is implemented. |

What Changed status decision:

- `what_changed_summary.json` is implemented as a backend product projection.
- The current frontend journey has no visible What Changed route/component.
- Treat this as **Deferred / Monitoring layer**, not an accidental omission.
- Report may mention monitoring is deferred or show a short grounded monitoring note if already available, but it must not pretend there is a full Monitoring screen.

Required sections when later surfaced:

- What changed headline.
- Current review date and prior review date, if available.
- Changed risk contributor.
- Changed worst stress scenario or stress behavior.
- Changed market context / regime, if available.
- Changed verdict or action status, if available.
- Retest triggers.
- Evidence gaps and warnings.
- Boundary note: monitoring triggers are review prompts, not alerts, trades, or scheduler jobs.

Core fields / evidence required when later surfaced:

- Summary status.
- Headline.
- What changed lines.
- Retest triggers.
- Current/prior analysis dates when available.
- Source presence and warnings translated into user language.

Optional/detail fields:

- Problem IDs and verdict IDs translated into readable problem/verdict labels.
- Compact timeline of previous reviews.
- Link back to the relevant screen: Diagnosis, Evidence, Hypothesis, Comparison, or Verdict.

Empty/unavailable state:

- No prior snapshot: "This is the first review; future runs can show what changed."
- Missing monitoring evidence: "No comparable monitoring snapshot is available yet."
- Optional context missing: show available change lines and mark verdict/comparison context as not available.
- No UI route: Report should say monitoring is deferred, not broken.

Forbidden user-facing terms:

- `what_changed_summary.json`, `monitoring_diff.json`, `monitoring/latest/analysis_snapshot.json`, `summary_status`, `missing_monitoring`, `retest_triggers`, `macro_regime_changed`, `top_risk_contributor_changed`, raw trigger IDs, `scheduler`, `alert`, `notification`, `rebalance_trigger` as trade instruction.

Status/badge taxonomy:

- Deferred, First review, Changed, No material change, Retest suggested, Evidence gap, Monitoring unavailable.

## Advanced and legacy surfaces excluded from Core MVP navigation

Do not add these as Core MVP frontend screens or hero modules unless a later canonical spec promotes them:

- Portfolio Health Score.
- Robustness Scorecard as standalone product score.
- Macro Dashboard / Macro Overlay.
- Full multi-candidate ranking arena.
- Assumption Sensitivity.
- Pareto / Dominance.
- Regret Analysis.
- Model Risk Diagnostics as standalone screen.
- Full Action Plan / Rebalancing Advisor.
- Full Decision Journal.
- Crisis Replay UI.
- What Happens If simulator UI.
- Client-Fit Check.
- Asset X-Ray.
- Max Sharpe, tax-aware optimization, turnover-aware optimizer objective, tactical tilt UI.
- Multi-client workspace.
- Polished PDF report product.

These may remain backend evidence, advanced/research artifacts, generated support, or future backlog.

## Route and MVP status summary

| Screen | Route | MVP status | Notes |
| --- | --- | --- | --- |
| Input | `/portfolio-input` | Core MVP | Current portfolio input only. |
| Diagnosis / Portfolio X-Ray | `/diagnosis` | Core MVP | Includes Problem Classification bridge. |
| Evidence / Stress Test Lab | `/evidence` | Core MVP | Stress Lab; references diagnosis bridge. |
| Hypothesis | `/hypothesis` | Core MVP | Owns Launchpad and merged Builder/Candidate for MVP. |
| Candidate / Builder | merged into `/hypothesis`; future `/candidate` if split | Core MVP content merged; separate route deferred | Move setup/generation/review sections here if split later. |
| Comparison | `/comparison` | Core MVP | One selected candidate; full arena deferred. |
| Verdict | `/verdict` | Core MVP | Non-binding decision support. |
| Report | `/report` | Core MVP preview | Grounded explanation; full PDF/journal deferred. |
| Monitoring / What Changed | no current route; future `/monitoring` or `/what-changed` | Deferred / Monitoring layer | Backend artifact may exist; no UI surface yet. |

## Acceptance checklist for future frontend changes

- [ ] Screen preserves the canonical order and does not skip from diagnosis directly to recommendation.
- [ ] Current portfolio evidence appears before candidate evidence.
- [ ] Problem Classification bridge is visible on Diagnosis and carried into Hypothesis.
- [ ] Candidate / Builder route policy is respected: merged into Hypothesis unless split intentionally.
- [ ] What Changed is either explicitly deferred or surfaced as Monitoring, not silently omitted.
- [ ] No raw artifact names, JSON keys, scenario IDs, backend labels, booleans, or method IDs appear in primary UI.
- [ ] Missing, partial, stale, and evidence-insufficient states are visibly different.
- [ ] No-trade / keep-current and evidence-insufficient are treated as valid outcomes.
- [ ] Comparison shows trade-offs, not only improvements.
- [ ] Verdict and Report say decision support, not trade execution or investment advice.
