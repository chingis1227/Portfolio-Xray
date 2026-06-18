# Screen Contracts

Status: canonical screen-level contract for current Portfolio MRI frontend routes, responsibilities, empty states, CTAs, and QA checks.

Scope: current MVP route behavior and product copy boundaries. Non-scope: backend formulas, JSON schemas, stress scenario definitions, generated output refresh, PDF generation, and detailed visual tokens.

Use with:

- `docs/contracts/PRODUCT_FLOW_CONTRACT.md` for product order;
- `docs/specs/frontend_screen_contracts.md` for route-specific screen requirements;
- `docs/design/current_website_structure.md` for current visible blocks and headings;
- `docs/contracts/DESIGN_SYSTEM_CONTRACT.md` for visual rules;
- `docs/contracts/PRESENTATION_LANGUAGE_RULES.md` for wording.

## Current route reality

Canonical visible user path:

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

Local development shortcut:

```text
/onboarding/name?dev_bypass=1
```

`/client-profile` exists as an advanced/manual Client Fit profile editor. It is not the first step of the normal web journey.

There is no current `/candidate`, `/monitoring`, `/what-changed`, optimizer-arena, action-plan, decision-journal, macro-dashboard, or PDF-product route. `/hypothesis` owns Problem Classification handoff, Candidate Launchpad, Builder setup, and the explicit candidate-generation attempt for the MVP. Generated candidate weights are reviewed on `/comparison`, not inside the Hypothesis action console.

## Global screen rules

1. Current portfolio evidence appears before candidate evidence.
2. A candidate is a diagnostic hypothesis test, not a recommendation or trade order.
3. Builder setup is setup-only until the user explicitly generates one candidate attempt.
4. Comparison is trade-off evidence, not a verdict.
5. Verdict is non-binding decision support.
6. Report preview is grounded explanation, not an invented AI recommendation.
7. Client Fit is diagnostic context, not suitability approval or optimizer mandate.
8. Missing, partial, stale, blocked, locked, and evidence-insufficient states are valid and visible.
9. Raw artifact filenames, JSON keys, booleans, backend IDs, run folder paths, and operator terms are not primary UI copy.
10. Evidence-provenance traces from `site_explanation_bundle.json` are hidden by default. Public explanation cards show product-language evidence labels; raw schema names, artifact filenames, and field paths may appear only in an explicit developer/debug provenance panel.
11. Staged diagnosis internals such as `Data check`, `pending`, `waiting`, provider freshness, backend stage IDs, and per-stage status rows are operational state, not normal product UI. Running diagnosis screens may show a simple product-facing preparation message and safe user-facing errors.

## Diagnostic Case File hierarchy

Platform analytical screens use a shared first-read hierarchy:

```text
Main finding
-> Why it matters
-> Key evidence
-> Metrics with investor meaning
-> Collapsed technical drill-down
-> Next safe decision
```

Primary cards must not lead with generic operational labels such as `Evidence available`,
`Evidence unavailable`, `Current portfolio only`, `Diagnostic only`, `No rebalancing`,
`Comparison pending`, `Unavailable`, or `Evidence required`. Those states remain valid, but they
belong in compact status rows, secondary notes, collapsed limitations, or specific explanations of
which conclusion is blocked and what the user can do next.

Promoted metrics must answer at least one investor question: what is the problem, why does it
matter, or what would change the next decision. Full metric matrices remain available below the
first-read answer.

## Route contracts

| Route | Product role | Must show | Primary CTA / next step | Must not show |
| --- | --- | --- | --- | --- |
| `/` | Public landing and product explanation. | Header/nav, hero, problem, workflow, architecture, precision, final CTA. | `Enter Platform` -> `/onboarding/sign-in`. | Platform sidebar, top journey rail, optimizer cockpit language. |
| `/onboarding/sign-in` | Required email-first entry. | Email step, verification step, local fallback on localhost. | Continue to onboarding for new users; route completed signed-in users with saved workspace/history to `/workspace`; route completed users without saved workspace data to Portfolio Input. | Treat local fallback as canonical product path; do not run diagnosis or refresh market data during login. |
| `/onboarding/name` | Friendly personal setup. | Name input and Continue CTA. | `/onboarding/investor-type`. | Portfolio diagnostics or suitability language. |
| `/onboarding/investor-type` | Five-question Client Fit intake. | One question at a time, progress, Back/Next/final save; questions cover stress-loss reaction, withdrawal horizon, temporary-loss limit, return target, and concentration response. | `/onboarding/loading`. | Investment advice or optimizer mandates. |
| `/onboarding/loading` | Setup transition. | Setup progress and Client Fit context save messaging. | Auto-redirect to `/workspace` when saved workspace/history exists for a returning user; otherwise `/portfolio-input`. | Platform sidebar. |
| `/workspace` | Signed-in account home and review-history hub. | Current review, active portfolio, saved review count, portfolio library, past reviews, archive states, and clear no-auto-recalculation copy. | Continue latest review, start new review, open past review, or use a saved portfolio for a new review. | Act as a calculation step, auto-run diagnosis on login, imply a historical verdict applies to edited input, expose raw artifact paths, or replace the 8-step review rail. |
| `/portfolio-input` | Step 01: define current portfolio. | Client Fit summary, empty-by-default holdings/weights input, validation, recovery, and clear draft/new-review semantics when loaded from workspace. | Run diagnosis -> `/diagnosis`. | Prefilled demo allocation, optimizer targets, tax settings, suitability approval, technical staged-progress table, silent overwrite of completed review evidence. |
| `/diagnosis` | Step 02: current portfolio diagnosis. | Compact utility header, controlled diagnosis hero, four-item Evidence Summary, primary two-column diagnostic canvas, Stress Lab CTA, collapsed advanced diagnostics with grouped Metric Matrix, locked state, or simple product-facing running state. | Continue to Stress Lab or return to Portfolio Input. | Rebalance recommendation from diagnosis alone, standalone explanation wall, repeated generic evidence badges, equal-weight card grid as the primary read, Metric Matrix before the diagnosis is understood, Macro Dashboard/PCA diagnostics, technical staged-progress table. |
| `/evidence` | Step 03: Stress Test Lab. | Verdict-first current-portfolio stress answer, Evidence Summary, grouped stress Metric Matrix, scenario contribution/protection canvas, secondary technical drill-downs, or locked/limited state. | Continue to Client Fit. | Candidate/comparison/verdict language or rebalance implication. |
| `/client-fit` | Step 04: profile-fit interpretation. | Verdict-first fit interpretation, explicit diagnostic-only boundary, Evidence Summary of mismatch dimensions, profile-check Metric Matrix, collapsed evidence details, or locked/missing-profile state. | Continue to Hypothesis. | Suitability approval, hiding diagnostic issues, raw evidence walls, repeated outside/aligned badges, or technical provenance in the primary UI. |
| `/hypothesis` | Step 05: one diagnostic test path. | Verdict-first proposed diagnostic test, why-selected evidence, success criteria before controls, primary diagnosis recap, secondary builder/action console, Client Fit context, alternatives, and evidence details. | Generate one test candidate and hand off to Comparison. | Candidate weights/results as the main content, candidate as recommendation, auto-generated action without an explicit click, Client Fit suitability approval, Metric Matrix as the primary pattern, or technical evidence competing with the primary CTA. |
| `/comparison` | Step 06: current vs one candidate. | Verdict-first comparison outcome, Evidence Summary, current/candidate/change/interpretation Metric Matrix grouped by risk improvement, trade-offs, fit impact, and evidence quality, plus secondary allocations/warnings. | Continue to Verdict. | Winner framing, final verdict, trade instruction, switch/recommendation language. |
| `/verdict` | Step 07: decision support. | Verdict-first cautious interpretation, selected evidence summary, narrative rationale, major trade-offs, limitations, Client Fit as one input, and next safe step. | Report or test another. | `recommended`, `approved`, `safe`, `must rebalance`, `trade now`, `best portfolio`, suitability approval. |
| `/report` | Step 08: grounded report preview. | Verdict-first narrative report frame, selected evidence summary, grounded executive preview, secondary evidence used/unavailable/warnings, and boundary. | Create preview when evidence is ready. | Unsupported conclusions, raw artifact viewer, or duplicating every page metric. |
| `/client-profile` | Advanced/manual Client Fit editor. | Manual planning inputs, suggested preset, target rows. | Save profile and continue to Portfolio Input. | Treat as canonical Step 01. |

## QA checklist

- [ ] Landing and onboarding do not show platform shell.
- [ ] Platform routes show the 8-step journey rail.
- [ ] Page-header step labels match the rail.
- [ ] Locked states show the current route step and the missing prerequisite.
- [ ] `/workspace` restores saved work without running diagnosis or market refresh automatically.
- [ ] Past reviews are clearly read-only unless full local evidence can be restored.
- [ ] Editing a completed review portfolio creates a new draft and does not mutate the old completed review.
- [ ] `/client-profile` stays advanced/manual.
- [ ] `/hypothesis` remains the merged Launchpad/Builder/Candidate screen unless a route split is intentionally approved.
- [ ] `/hypothesis` exposes one primary test and keeps Client Fit, alternatives, and technical evidence secondary.
- [ ] Monitoring / What Changed remains deferred unless a route decision promotes it.
- [ ] Same-review, same-selected-card, same-candidate, and same-stage-order lineage is preserved before unlocking downstream screens.
- [ ] Documentation impact was checked against `docs/contracts/DOC_SYNC_CONTRACT.md`.

## Screen hierarchy contracts

Every product screen must guide the user from problem to evidence to decision/action. The fields below are design-facing contracts; they do not change backend schemas or calculations.

### Portfolio Input

- Primary user question: What current portfolio is being diagnosed?
- Primary answer: the user has supplied a valid current allocation, investor currency, and diagnostic context.
- First-read top cards: `Portfolio to diagnose`, `Input readiness`, and `Client Fit context`.
- Top evidence items: holdings count, weight total, instrument/cash validation, Client Fit context presence.
- Primary CTA: Run diagnosis.
- Secondary CTA: adjust intake or recover an active review.
- Hidden/collapsed: technical validation detail and recovery mechanisms unless needed.
- States: empty holdings, invalid weight total, loading diagnosis, backend error, recovered review.
- Never first viewport: optimizer targets, candidate weights, tax-aware controls, suitability approval, or demo allocation as canonical input.

### Diagnosis

- Primary user question: What is wrong or material in the current portfolio before any candidate is tested?
- Primary answer: a dominant current-portfolio diagnosis with one supporting interpretation.
- First-read top cards: `Main diagnosis`, `Why it matters`, and `Key evidence`.
- Top evidence items: primary issue, main exposure, worst observed downside, evidence quality.
- Primary CTA: Review Stress Lab evidence.
- Secondary CTA: export report or test one candidate hypothesis when journey state allows.
- Hidden/collapsed: MetricMatrix, professional metrics, full X-Ray, technical evidence, provenance, and limitations.
- States: locked before Portfolio Input, running diagnosis, failed/retry, partial evidence, complete diagnosis.
- Never first viewport: VaR/ES/skewness/kurtosis/Treynor/beta wall, correlation matrix, raw JSON, repeated evidence badges, optimizer recommendation.

### Stress Lab

- Primary user question: Which stress behavior should be reviewed next for the current portfolio?
- Primary answer: the worst material stress behavior and its current-portfolio-only boundary.
- First-read top cards: `Stress failure mode`, `Worst scenario`, and `Loss drivers and protection gap`.
- Top evidence items: worst scenario, estimated loss, drivers/protection behavior, evidence quality.
- Primary CTA: Continue to Client Fit.
- Secondary CTA: return to Diagnosis.
- Hidden/collapsed: scenario library drill-down, factor attribution detail, data limitations, technical replay notes.
- States: locked before Diagnosis, limited stress evidence, unavailable stress model, ready stress result.
- Never first viewport: candidate comparison, rebalance language, trade instructions, or optimizer cockpit controls.

### Client Fit

- Primary user question: Does the current portfolio conflict with the provided diagnostic profile context?
- Primary answer: a non-binding fit interpretation that cannot clear material portfolio issues.
- First-read top cards: `Fit interpretation`, `Main mismatch`, and `Profile context`.
- Top evidence items: main mismatch, drawdown tolerance, horizon/target context, evidence quality.
- Primary CTA: Continue to Hypothesis.
- Secondary CTA: adjust profile/intake.
- Hidden/collapsed: raw profile rows, provenance, detailed target matrix.
- States: missing profile compatibility state, locked before Stress Lab, partial fit evidence, ready fit check.
- Never first viewport: suitability approval, trade advice, proof that no action is needed, or optimizer mandate.

### Hypothesis

- Primary user question: Which one diagnostic candidate test should be prepared?
- Primary answer: one proposed test path with success criteria and trade-off boundaries.
- First-read sections: `Problem Classification`, `Candidate Launchpad`, `Alternatives Builder`, and `Candidate Generation Result`.
- Candidate Launchpad must show both the investment hypothesis and the mathematical method before generation controls.
- Top evidence items: selected problem, why this test, first success criterion, main trade-off.
- Primary CTA: Generate one test candidate.
- Secondary CTA: review alternatives or return to Client Fit.
- Hidden/collapsed: alternative tests, technical builder details, raw factory IDs.
- States: locked before Client Fit, ready-to-generate, generation running, failed candidate attempt, candidate ready.
- Never first viewport: final candidate weights as the answer, recommendation language, automatic action without click.

### Comparison

- Primary user question: What changes between the current portfolio and the generated diagnostic candidate?
- Primary answer: trade-off evidence, not a winner or final verdict.
- First-read top cards: `What improved`, `What worsened`, and `Is the trade-off meaningful?`.
- Top evidence items: material improvement, material cost, Client Fit impact, comparison evidence quality.
- Primary CTA: Continue to Verdict.
- Secondary CTA: return to Hypothesis or retry generation when safe.
- Hidden/collapsed: allocation tables, warnings, technical comparison notes.
- States: locked before candidate, candidate-not-comparable, comparison unavailable, ready comparison.
- Never first viewport: `best portfolio`, `switch`, `recommended`, trade order, final verdict.

### Verdict

- Primary user question: What non-binding decision-support interpretation follows from the evidence?
- Primary answer: a cautious verdict with evidence, limitations, and what would change it.
- First-read top cards: `Decision stance`, `Reason`, and `What would change the verdict`.
- Allowed decision stances are `Keep current`, `Review rebalance`, `Test another candidate`, and `Evidence insufficient`.
- Top evidence items: main diagnosis, comparison outcome, major trade-off, evidence limitation.
- Primary CTA: Open Report.
- Secondary CTA: test another hypothesis.
- Hidden/collapsed: raw artifact references and detailed provenance.
- States: evidence insufficient, candidate failed, ready verdict, stale/mismatched lineage.
- Never first viewport: suitability approval, guaranteed improvement, `trade now`, `safe`, or mandate language.

### Report

- Primary user question: What client-ready narrative can be grounded in this review?
- Primary answer: an executive preview based on selected evidence from the active review.
- First-read top cards: `Plain-English explanation`, `Evidence used`, and `Limitations`.
- Top evidence items: diagnosis, stress evidence, Client Fit/comparison context, verdict boundary.
- Primary CTA: create/open report preview when evidence is ready.
- Secondary CTA: return to Workspace or Verdict.
- Hidden/collapsed: full evidence used/unavailable/warnings and grounding trace.
- States: locked before verdict, evidence unavailable, ready report preview, partial report context.
- Never first viewport: unsupported AI recommendations, raw artifact viewer, every page metric repeated as a report wall.
