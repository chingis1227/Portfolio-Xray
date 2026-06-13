# Product-Code-Docs-Design Alignment Audit

Date: 2026-06-10  
Scope: audit-only review of Portfolio MRI / Portfolio X-Ray product truth, backend output contracts, frontend screens, design system, and user-facing copy.  
Constraint: no code, backend, UI, refactor, merge, push, or generated-output change.

## Executive verdict

Portfolio MRI is directionally aligned around a diagnosis-first, current-portfolio-first decision-support SaaS, but the alignment is not yet contract-tight enough for more UI/product expansion.

The strongest source-of-truth chain is:

1. `SPEC.md`
2. `OUTPUTS.md`
3. `docs/product_flow_operator_guide.md`
4. `docs/runtime_artifact_contract.md`
5. `docs/specs/*.md`
6. `docs/design/portfolio_mri_design_system.md`
7. `../../frontend/README.md`

The frontend prototype implements the broad journey, but it still mixes product language with implementation artifacts, hand-written adapter logic, raw backend field labels, and incomplete screen contracts. The biggest immediate risk is adding more UI features before locking the data-to-screen and copy contracts.

Screen contract follow-up: [canonical frontend screen contracts](../specs/frontend_screen_contracts.md).

## Product truth audit

### Canonical docs found

| Area | Canonical / strongest source | Notes |
| --- | --- | --- |
| Current product truth | `SPEC.md`, `PRODUCT.md`, `AGENTS.md` | All define “Diagnosis 2” / diagnosis-first product truth and warn against optimizer-first framing. |
| Runtime/operator flow | `docs/product_flow_operator_guide.md`, `docs/runtime_artifact_contract.md`, `OUTPUTS.md` | Best current map for artifact read order and diagnosis-only vs one-candidate modes. |
| Output boundaries | `OUTPUTS.md` | Strongly states generated outputs are evidence/deliverables, not source. |
| X-Ray | `docs/specs/portfolio_xray_diagnostics_spec.md`, `docs/specs/portfolio_xray_layer_spec.md` | Blocks 2.1-2.6 are Core MVP; 2.7 archetype is advanced/legacy. |
| Stress Lab | `docs/specs/stress_lab_layer_spec.md`, `docs/specs/stress_testing_spec.md`, `docs/specs/current_portfolio_stress_scorecard_spec.md`, `docs/specs/hedge_gap_analysis_spec.md` | Clear split: scenario library, stress results, hedge gap, current-portfolio stress scorecard. |
| Problem / Launchpad | `docs/specs/problem_classification_spec.md`, `docs/specs/block_4_diagnosis_v3_spec.md`, `docs/specs/candidate_launchpad_spec.md` | Strong diagnosis-to-hypothesis boundary. |
| Builder / Candidate | `docs/specs/portfolio_alternatives_builder_spec.md`, `docs/specs/candidate_generation_spec.md` | Builder is setup only; candidate generation is explicit. |
| Comparison / Verdict | `docs/specs/current_vs_candidate_spec.md`, `docs/specs/decision_verdict_spec.md` | No-trade and evidence-insufficient are valid. |
| AI Commentary | `docs/specs/ai_commentary_grounding_spec.md` | Grounding only; no LLM in current implementation. |
| Monitoring / What Changed | `docs/specs/light_monitoring_summary_spec.md`, `docs/specs/monitoring_spec.md` | Additive projection over monitoring evidence. |
| Design | `docs/design/portfolio_mri_design_system.md` | Canonical design direction; root `DESIGN.md` is legacy reference for new Portfolio MRI UI. |
| Frontend prototype | `../../frontend/README.md` | Good local architecture and state strategy description. |

### Product principles consistency

| Principle | Docs alignment | Code/frontend alignment | Audit finding |
| --- | --- | --- | --- |
| Diagnosis-first | Strong | Mostly strong | Frontend starts at input, then diagnosis/evidence. Good. |
| Decision-support, not advice | Strong | Mostly strong | Verdict/report copy repeats decision-support boundary. |
| Current portfolio first | Strong | Strong | Input, Diagnosis, Stress copy emphasize current portfolio. |
| Candidate as hypothesis | Strong | Medium/strong | Hypothesis page says this, but raw Builder fields and method IDs make it feel technical. |
| No-trade valid | Strong | Medium | Comparison/Verdict mention no-trade. Earlier screens do not make it a first-class possible outcome. |
| Evidence insufficient valid | Strong | Medium | Specs are clear. UI has unavailable/limited states, but not a unified “evidence insufficient” pattern across screens. |
| AI commentary explanatory | Strong | Medium | Report page uses AI Commentary context correctly, but phrases like “Opening report” and “Grounded commentary” could better explain no LLM / deterministic grounding. |

## Biggest mismatches

1. **Frontend flow has no dedicated Candidate screen.** Canonical/design flow includes `Hypothesis -> Candidate -> Comparison`; frontend routes go `/hypothesis -> /comparison`. Candidate generation is embedded in Hypothesis/Builder.
2. **Backend mapping exists, but no single frontend screen contract.** `frontend/lib/reviewState.tsx` and `frontend/components/evidence/stressLabModel.ts` manually adapt artifacts. This creates scattered UI truth.
3. **Raw backend terms leak on Hypothesis and error paths.** Examples: `Card type`, `Default method`, `Validation status`, `Can generate candidate`, `true/false`, `outputs.candidate_launchpad`, `review_id`, `valid JSON`.
4. **Design docs and CSS are close but not identical.** Canonical design says dark navy/slate tokens and restrained shadows; CSS uses near-black tokens, shadow-heavy cards, animated effects, and `gold` as a near-slate tone.
5. **What Changed is implemented in backend docs but absent from the visible frontend journey.** `what_changed_summary.json` has no route/component mapping in the current seven-route UI.

## Backend output to frontend mapping

| Backend artifact | Canonical role | Current frontend route/component | Current use | Gap |
| --- | --- | --- | --- | --- |
| `portfolio_xray.json` | Portfolio X-Ray / Diagnosis Blocks 2.1-2.6 | `/diagnosis`; `DiagnosisSummaryPanel`, `PortfolioXRayBlocks`; compacted in `frontend/lib/reviewState.tsx` | Strongly used for composition, metrics, factors, hidden risks, risk budget, weakness map | No explicit artifact/source drill-down; Problem Classification not the diagnosis hero source. |
| `stress_report.json` | Stress Test Lab / Evidence Blocks 3.1-3.4 | `/evidence`; `StressTestLab` and stress panels; mapped in `stressLabModel.ts` | Strongly used for scenarios, worst loss, helped/hurt assets, factor attribution, hedge gap, limitations | Route is “Evidence” but journey label is “Stress”; Problem Classification evidence is not shown here. |
| `problem_classification.json` | Converts X-Ray/stress into primary diagnosis and next step | Indirectly compacted in `reviewState.tsx`; visible mostly as availability / primary problem summaries | Partial | No dedicated Problem Classification section/card; source evidence and `next_diagnostic_step` are not first-class. |
| `candidate_launchpad.json` | Hypothesis cards | `/hypothesis`; `HypothesisCard`, inline card mapping | Used for real Launchpad cards | Raw Launchpad field labels leak; no clean card-level contract for product copy. |
| `portfolio_alternatives_builder.json` | Builder setup only | `/hypothesis`; `BuilderSetupPanel`, `HypothesisBuilderPanel` | Used after prepare action | Builder setup is mixed into Hypothesis; raw setup fields are visible; no dedicated Candidate/Builder screen. |
| `candidate_generation.json` | One candidate attempt after explicit user action | `/hypothesis`; `recordCandidateGeneration`, inline generated candidate panel | Used to show candidate status and weights | Candidate has no own route; generation status/weights are shown before a dedicated candidate review step. |
| `current_vs_candidate.json` | Current vs selected candidate | `/comparison`; `CandidateComparisonPanel`, `TradeoffSummary` | Used after comparison API call | Mapping is summary-only; artifact source and unavailable criteria are not clearly drill-downable. |
| `decision_verdict.json` | Decision-support verdict | `/verdict`; `VerdictPanel` | Used after verdict API call | Good boundary copy; could expose no-trade/evidence-insufficient as explicit state taxonomy. |
| `ai_commentary_context.json` | Grounding only for future AI commentary/report draft | `/report`; `reportFromResult`, `ClientReadyReportPreview` | Used transiently after report generation | Not persisted in frontend state; source references/warnings are summarized but not inspectable. |
| `what_changed_summary.json` | Monitoring / What Changed | No visible route/component found | Not mapped | Missing product surface; Report only has monitoring text from AI context, not What Changed projection. |

## Frontend screen-by-screen audit

### 1. Input

| Item | Finding |
| --- | --- |
| Route | `/portfolio-input` |
| Main components | `PortfolioInputTable`, `PageHeader` |
| Backend source | User input -> `POST /api/portfolio/diagnose` -> run-local `review_result.json`; later `portfolio_xray.json`, `stress_report.json`, `problem_classification.json`, `candidate_launchpad.json` |
| Current sections | current allocation only, investor currency, holdings/weights, validation summary, run diagnosis CTA, advanced recovery |
| Missing sections | input assumptions disclosure is only implied; no clear “data availability before run”; no model/current portfolio selector, though docs say distinction should be clear if applicable |
| Duplicated logic | Frontend repeats weight validation and instrument validation while API route also validates |
| Backend terms in UI | `Review ID`, `frontend_review_...`, “compact summary”, possible raw error messages |
| Product fit | Strong diagnosis-first start. Recovery is useful but technical for a premium client-ready UI. |

### 2. Diagnosis

| Item | Finding |
| --- | --- |
| Route | `/diagnosis` |
| Main components | `DiagnosisSummaryPanel`, `PortfolioXRayBlocks` |
| Backend source | `portfolio_xray.json`; partly `problem_classification.json` via compact review summary |
| Current sections | hero, summary, composition, risk profile, factors, hidden risks, risk budget, weakness map, data limitations |
| Missing sections | explicit Problem Classification card; evidence-source drill-down; clean “what user owns / what drives risk / where concentrated” synthesis in one stable executive contract |
| Duplicated logic | Label normalization and percent formatting are repeated across display helpers and component-local helpers |
| Backend terms in UI | Mostly cleaned, but section names such as “Risk Profile”, “Risk Budget”, “Weakness Map” still need canonical capitalization rules |
| Product fit | Good X-Ray screen. It answers most diagnosis questions, but it is still X-Ray-first rather than Problem-Classification-first. |

### 3. Evidence / Stress Test Lab

| Item | Finding |
| --- | --- |
| Route | `/evidence` |
| Main components | `StressTestLab`, `StressScorecardPanel`, `ScenarioLibraryPanel`, `SelectedScenarioDetailPanel`, `LossContributionPanel`, `HelpedHurtPanel`, `FactorStressAttributionPanel`, `HedgeGapAnalysisPanel`, `XRayStressConfirmationPanel`, `DataLimitationsPanel` |
| Backend source | `stress_report.json`, with some X-Ray bridge context |
| Current sections | stress scorecard, scenario library, selected scenario detail, loss contribution, helped/hurt assets, factor attribution, hedge gap, X-Ray bridge, data limitations |
| Missing sections | explicit Problem Classification link; unified Evidence Center that combines X-Ray + Stress + Classification; source artifact references as drill-down |
| Duplicated logic | Scenario ID display mapping appears in both `stressLabModel.ts` and `displayLabels.ts` / `reviewState.tsx` |
| Backend terms in UI | Internal terms are mostly mapped, but “Scorecard” may promote advanced/backend language unless scoped as current-portfolio stress summary |
| Product fit | Strongest screen for Stress Lab requirements. Needs naming cleanup: route is Evidence, journey short label is Stress, design says Evidence. |

### 4. Hypothesis

| Item | Finding |
| --- | --- |
| Route | `/hypothesis` |
| Main components | `HypothesisCard`, inline `BuilderSetupPanel`, `HypothesisBuilderPanel` in sample mode |
| Backend source | `candidate_launchpad.json`, `portfolio_alternatives_builder.json`, `candidate_generation.json` |
| Current sections | launchpad cards, Builder setup preview, prepare test setup, test hypothesis, generated candidate panel |
| Missing sections | clean separation between Hypothesis, Builder setup, and Candidate result; selected card rationale in client-ready copy; data-quality blocked state pattern |
| Duplicated logic | Launchpad card mapping lives inline in route; method label mapping is local |
| Backend terms in UI | `Card type`, `Default method`, `Validation status`, `Can generate candidate`, `Generates portfolio`, `Is rebalance recommendation`, `true/false`, raw method ids when unknown, `outputs.candidate_launchpad` in missing state |
| Product fit | Correct boundary intent, but this is the noisiest screen and highest copy risk. |

### 5. Candidate / Builder

| Item | Finding |
| --- | --- |
| Route | No dedicated route found |
| Main components | Embedded inside `/hypothesis` |
| Backend source | `portfolio_alternatives_builder.json`, `candidate_generation.json` |
| Current sections | setup preview, generate candidate, generated weights |
| Missing sections | standalone Candidate review; candidate hypothesis summary; method availability; construction limitations; candidate-is-not-recommendation boundary; compare-readiness state |
| Duplicated logic | Candidate readiness flags are stored in review state and also derived in page logic |
| Backend terms in UI | `candidateId`, generation status, raw weight display without candidate explanation |
| Product fit | Biggest flow mismatch. Candidate exists as a backend stage but not as a screen. |

### 6. Comparison

| Item | Finding |
| --- | --- |
| Route | `/comparison` |
| Main components | `TradeoffSummary`, `CandidateComparisonPanel` |
| Backend source | `current_vs_candidate.json` via `/api/portfolio/comparison/generate` |
| Current sections | ready-to-compare state, generate comparison, what changed/cost/unclear, detailed comparison table |
| Missing sections | explicit “unchanged / inconclusive areas” from artifact; success criteria evaluation; materiality status; source artifact drill-down |
| Duplicated logic | Comparison summary is built in `reviewState.tsx` instead of a shared screen contract |
| Backend terms in UI | `view_mode` is hidden, but possible fallback method/candidate IDs can leak |
| Product fit | Good trade-off framing; needs stricter mapping for success criteria and unavailable metrics. |

### 7. Verdict

| Item | Finding |
| --- | --- |
| Route | `/verdict` |
| Main components | `VerdictPanel` |
| Backend source | `decision_verdict.json` via `/api/portfolio/verdict/generate` |
| Current sections | generate verdict, verdict hero, key evidence, monitoring trigger, action framing, evidence quality, what would change it |
| Missing sections | explicit verdict taxonomy display: keep current/no-trade/test another/evidence insufficient/rebalance-review; guardrail checklist |
| Duplicated logic | Verdict result is summarized into frontend state; source details are not inspectable |
| Backend terms in UI | `Decision status: ${verdict.decisionStatus.replaceAll("_", " ")}` may expose backend status vocabulary |
| Product fit | Good decision-support boundary. Needs stronger no-trade/evidence-insufficient visual treatment. |

### 8. Report

| Item | Finding |
| --- | --- |
| Route | `/report` |
| Main components | `ClientReadyReportPreview` |
| Backend source | `ai_commentary_context.json` via `/api/portfolio/report/generate`; not `what_changed_summary.json` |
| Current sections | generate report summary, executive summary, supporting sections, monitoring, decision boundary, limitations |
| Missing sections | source references; evidence quality summary; what changed since prior review; copy/edit/export behavior is target-only |
| Duplicated logic | `reportFromResult()` maps context to report locally in the page |
| Backend terms in UI | “AI Commentary context”, “No PDF generation”, “evidence package type(s)” |
| Product fit | Good report preview skeleton, but current copy is still operator/prototype-like rather than client-ready. |

## Diagnosis audit

Diagnosis must answer:

| Required question | Current status | Evidence / screen | Gap |
| --- | --- | --- | --- |
| What the user owns | Mostly covered | Input table; Diagnosis composition; X-Ray allocation blocks | Needs more visible “current holdings / economic exposure” summary in Diagnosis. |
| What drives risk | Covered | Risk budget, top contributors, risk profile | Good, but needs a single “top risk driver” executive line tied to Problem Classification. |
| Where capital/risk is concentrated | Covered | Capital concentration, risk contribution | Good. |
| Factor exposures | Covered | Factor exposure panel | Good, subject to data availability. |
| Hidden risks | Covered | Hidden risk alerts | Good, but “detector” style language should stay hidden/normalized. |
| Risk budget | Covered | Risk budget panel | Good. |
| Weakness map | Covered | Weakness map grid | Good, but should clearly say pre-stress hypothesis, not confirmed failure. |

Diagnosis gaps:

- Problem Classification is not visible enough as the bridge from diagnosis to action.
- Data trust/evidence quality is present but not unified across all diagnosis cards.
- Diagnosis and Evidence both invite “Test a candidate hypothesis”; guardrails are good, but users may still skip the problem-classification reasoning.
- Current screen answers many questions through multiple panels; it needs a stable executive summary contract before more sections are added.

## Evidence / Stress Test Lab audit

Evidence must answer:

| Required question | Current status | Evidence / screen | Gap |
| --- | --- | --- | --- |
| Worst scenario | Covered | Stress scorecard / selected scenario | Good. |
| Portfolio loss | Covered | Stress scorecard / selected scenario detail | Good. |
| Scenarios tested | Covered | Scenario Library | Good. |
| Assets hurt/helped | Covered | Helped/Hurt panel, Loss Contribution | Good. |
| Offset coverage | Covered | Hedge Gap panel, selected scenario detail | Good. |
| Factor stress drivers | Covered | Factor Stress Attribution | Good. |
| Hedge gap | Covered | Hedge Gap Analysis | Good. |
| X-Ray confirmation | Covered | X-Ray bridge | Good. |
| Data limitations | Covered | Data Limitations panel | Good. |

Stress Lab gaps:

- Evidence screen is actually Stress Lab only; it does not yet combine X-Ray + Stress + Problem Classification into a full Evidence Center.
- “Scorecard” wording risks pulling advanced/backend concepts into product copy unless it is consistently named “Current-portfolio stress summary.”
- Source paths and artifact references are not visible in drill-down, despite design system allowing source artifact references.
- `what_changed_summary.json` is not represented after stress/verdict/report.

## Design system audit

### What is aligned

- Overall UI direction is premium dark institutional.
- Cards, badges, sticky navigation, restrained semantic colors, and boundary notes broadly match the design system.
- Frontend CSS uses CSS variables and avoids a generic dashboard look.
- Copy often says candidate is not recommendation and verdict is not a trade order.

### Gaps

| Design area | Finding | Risk |
| --- | --- | --- |
| Color tokens | `docs/design/portfolio_mri_design_system.md` specifies navy/slate tokens; `frontend/styles/globals.css` uses near-black/gray tokens and softer semantic colors | Design drift becomes hard to govern. |
| Shadows | Canonical design says prefer thin borders/subtle surface shifts; CSS uses `shadow-decision` and heavy card shadows | Premium style can become glossy/visual-heavy. |
| Badges | `StatusBadge` supports tones, but no typed status taxonomy for risk severity/evidence quality/unavailable/no-trade | Inconsistent labels as screens grow. |
| Evidence quality | Helpers exist, but not centralized as a formal UI status contract | “Limited”, “Unavailable”, “Evidence insufficient” may diverge. |
| Unavailable states | Present per screen, but no single component/voice | Missing evidence may look like a page failure instead of a valid product state. |
| Typography | Mostly aligned; no explicit enforcement for capitalization and sentence case | Backend labels can leak with underscores / title case. |
| Motion | CSS has hover lifts and animated borders; reduced-motion handling exists in one nav path only | Motion can exceed “calm institutional” if expanded. |
| Forbidden terms | Design forbids advice-like terms; frontend has only partial normalization | Copy regressions likely without lint/checklist. |

## Copy audit: raw/backend terms

### Terms searched

`backend`, `JSON`, `portfolio_xray`, `stress_report`, `recession_severe`, `equity_shock`, `pnl_by_asset`, `Signal visible`, `Watch`, `Info`, `technical detail`, `detector checks`, `equity_weight`, `risk_on_weight`.

### Findings

| Term | Frontend status | User-facing risk |
| --- | --- | --- |
| `backend` | Mostly README/tests/API internals; API scrubbed error phrase can appear in details | Low/medium. Avoid exposing “Backend failure…” to users. |
| `JSON` | Mostly internals/tests/API; invalid request error says “valid JSON” | Medium on error surfaces. |
| `portfolio_xray` | Internals and tests; normalized by display labels | Low if normalization always applies. |
| `stress_report` | Internals; normalized by display labels | Low. |
| `recession_severe` | Internal mapping in stress model/review state | Low; mapped to “Severe recession.” |
| `equity_shock` | Internal mapping | Low; mapped to “Equity sell-off.” |
| `pnl_by_asset` | Internal stress model only | Low. |
| `Signal visible` | Not found as exact text | Low. |
| `Watch` | `tradeoff_to_watch` appears; UI label “Tradeoff to watch” | Medium; acceptable concept, but should be “Trade-off to review.” |
| `Info` | CSS `pmri-info-hint`, type names, instrument names | Low. |
| `technical detail` | Normalized in display labels | Low. |
| `detector checks` | Normalized in display labels | Low. |
| `equity_weight` | Normalized in display labels | Low. |
| `risk_on_weight` | Normalized in display labels | Low. |

### Other user-facing backend terms found

- `/hypothesis`: `Card type`, `Default method`, `Validation status`, `Can generate candidate`, `Generates portfolio`, `Is rebalance recommendation`, `true`, `false`, `n/a`.
- `/hypothesis` missing state: `outputs.candidate_launchpad`.
- `/report`: `AI Commentary context`, `evidence package type(s)`, `No PDF generation`.
- `/portfolio-input`: `Review ID`, `frontend_review_...`, `compact summary`.
- `/verdict`: backend `decisionStatus` is displayed after replacing underscores.
- API errors: “Request body must be valid JSON”, “Backend failure details were captured safely.”

Recommended copy replacements:

| Current | Preferred |
| --- | --- |
| `Card type` | Test type |
| `Default method` | Starting test method |
| `Validation status` | Setup check |
| `Can generate candidate` | Ready to test |
| `Is rebalance recommendation: false` | Not a rebalance recommendation |
| `Generates portfolio: false` | Setup only |
| `Tradeoff to watch` | Trade-off to review |
| `outputs.candidate_launchpad` | hypothesis cards for this review |
| `AI Commentary context` | grounded explanation inputs |
| `No PDF generation` | preview only |
| `valid JSON` | request format was invalid |
| `Backend failure` | analysis engine error / review could not be completed |

## Scaling risk

The next MVP expansion may create chaos without these contracts:

1. **Screen contracts.** Each screen needs an owned data contract: required artifacts, sections, empty states, copy rules, and source fields.
2. **Central artifact-to-UI adapter.** Current mapping is distributed across `reviewState.tsx`, route files, and component-local helpers.
3. **Copy normalization/lint.** Display label normalization helps, but raw labels can still be introduced in pages.
4. **Design token enforcement.** Canonical design tokens and CSS tokens should be reconciled before adding more visual surfaces.
5. **State lineage contract.** Frontend state stores compact summaries and some transient results. More stages will need stricter artifact lineage and stale-state handling.
6. **Unavailable/evidence-insufficient pattern.** Missing data must be a valid product state, not a failure-looking UI.
7. **One-candidate vs batch/research boundary.** More candidate UI could accidentally expose the optimizer arena unless method/menu rules are centralized.
8. **Monitoring route.** `what_changed_summary.json` needs a product home before “Monitoring / What Changed” expands.

## Pareto roadmap

### P0 — block before more UI/product changes

1. Define a screen contract table for all routes: artifacts, fields, copy, empty states, and forbidden raw terms.
2. Add a dedicated Candidate/Builder screen or explicitly rename Hypothesis as “Hypothesis + Candidate test” in docs and journey until split.
3. Remove raw backend labels from Hypothesis/Builder UI.
4. Create a central UI status taxonomy for evidence quality, risk severity, unavailable, no-trade, and evidence-insufficient.
5. Map `what_changed_summary.json` to a visible Report/Monitoring section or mark it explicitly “not yet surfaced.”

### P1 — high leverage hardening

1. Move artifact adapter logic out of route files into one product UI adapter layer.
2. Add copy lint/search for forbidden/raw terms in user-facing frontend files.
3. Reconcile `docs/design/portfolio_mri_design_system.md` tokens with `frontend/styles/globals.css`.
4. Add source/evidence drill-down pattern for Diagnosis, Evidence, Comparison, Verdict, and Report.
5. Make Problem Classification a visible bridge section on Diagnosis or Evidence.

### P2 — product polish

1. Add explicit no-trade / evidence-insufficient visual states earlier in the journey.
2. Add client-ready language layer for Report that hides operator terms.
3. Standardize capitalization: sentence case for UI labels; no underscores; no boolean literals.
4. Add reduced-motion coverage for all animated panels.
5. Add a compact “What changed since last review” card once monitoring evidence exists.

### P3 — later / advanced

1. Advanced candidate registry/drill-down.
2. Full Decision Journal product.
3. PDF export workflow.
4. Multi-client workspace.
5. Advanced settings, optimizer zoo, tax-aware, what-if, asset diagnostics.

## Recommended implementation order

1. **Freeze screen contracts** in docs before changing UI.
2. **Clean Hypothesis/Builder copy** because it has the highest raw-backend leakage.
3. **Decide Candidate route strategy**: add `/candidate` or formally keep it inside `/hypothesis` for MVP.
4. **Centralize adapter/mapping logic** for artifact-to-screen data.
5. **Add Problem Classification bridge** to Diagnosis/Evidence.
6. **Add What Changed surface** or mark it deferred in frontend docs.
7. **Reconcile design tokens and statuses**.
8. **Add copy/design QA checks**.

## QA checklist for future UI/product changes

- [ ] Does the screen preserve diagnosis-first ordering...
- [ ] Is the current portfolio diagnosed before any candidate is shown...
- [ ] Is every candidate labeled as a hypothesis test...
- [ ] Is no-trade visible as a valid outcome...
- [ ] Is evidence-insufficient visible as a valid outcome...
- [ ] Are AI/explanation claims grounded in deterministic source artifacts...
- [ ] Does the screen avoid raw artifact names except in explicit technical drill-down...
- [ ] Does the screen avoid `backend`, `JSON`, snake_case fields, booleans, and method IDs in primary UI...
- [ ] Does every unavailable state explain whether data is missing, stale, partial, or not yet generated...
- [ ] Does every comparison show trade-offs, not just improvements...
- [ ] Does Verdict say decision-support, not trading instruction...
- [ ] Does Report keep evidence quality and boundary notes visible...
- [ ] Do routes match the canonical journey or clearly document any intentional merge...
- [ ] Are design tokens, badge tones, and severity labels from one shared taxonomy...
- [ ] Are source artifacts referenced in drill-down, not in primary copy...
- [ ] Are legacy/advanced artifacts kept out of Core MVP navigation...

## Final audit conclusion

The product/docs/backend foundation is strong enough to support a premium diagnosis-first SaaS, but the frontend is still a prototype with scattered contracts. Before further UI/product changes, lock the route-by-route data and copy contracts, split or formalize the Candidate stage, clean raw backend labels, and reconcile design/status tokens.
