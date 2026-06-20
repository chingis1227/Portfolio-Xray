# Current Website Structure

Status: current source-of-truth description of the implemented Portfolio MRI frontend website in `frontend/`.

This document describes what the current site shows: route order, page blocks, visible copy, CTAs, status states, and how metrics are presented. It is not a backend formula spec and does not override product, data, or output contracts.

## Canonical entry and local shortcut

Canonical new-user path:

```text
/ -> /onboarding/sign-in -> /onboarding/name -> /onboarding/investor-type -> /onboarding/loading -> /portfolio-input
```

Returning-user branch:

```text
eligible returning account -> /workspace -> /portfolio-input or same-run continuation
```

`/workspace` is the signed-in account home for returning users with saved workspace, portfolio, draft, or review history. First-time users without saved workspace data may continue directly from onboarding to Portfolio Input.

Local testing shortcut:

```text
/onboarding/name?dev_bypass=1
```

The shortcut is allowed for local preview while email sign-in is still being stabilized. It is not the documented product path and must not replace sign-in in product docs, demo scripts, or public copy. `/onboarding/goals` is a compatibility-only redirect to `/onboarding/investor-type`; it is not a current onboarding page. `/client-profile` is an advanced/manual Client Fit editor. `/sandbox/components`, developer provenance panels, and legacy/debug helper flows are local review/debug surfaces, not production journey steps.

## Global visual frame

Public routes (`/` and `/onboarding/*`) do not show the platform journey rail, navigation dock, or top journey rail. They use a sparse near-black canvas, white typography, mono uppercase labels, hairline cards, and pill CTAs.

Platform routes show:

- a near-black workspace with restrained radial accent only where helpful, hairline separation, and flat dark evidence surfaces rather than glassy dashboard panels;
- a persistent compact top utility header above platform content, with a larger product/route title and restrained route actions; active portfolio, currency, holdings count, last update, and missing data-window labels are not shown in the header;
- a fixed quiet near-black journey rail on wide screens, positioned beside the content blocks; the current route uses a light active pill while other unlocked or locked steps stay muted;
- account navigation entry for `Workspace` outside the 8-step review rail;
- a bottom compact dark journey dock on narrower screens, with compact `Workspace` and optional account controls;
- gated journey navigation with 8 icon-led steps: Portfolio, Diagnosis, Stress Lab, Client Fit, Hypothesis, Comparison, Verdict, Report;
- no sticky top journey rail on redesigned analytical routes; compact step context appears inside `VerdictHero`;
- verdict-first page hero on redesigned analytical routes;
- platform content constrained to roughly 1180-1240px so analytical screens read as a focused decision room instead of a dashboard wall;
- flat hairline case-file panels, restrained tables, sparse badges, and locked states.

## `/` Landing

Role: public product page that explains Portfolio MRI before the platform opens.

Block order:

1. Header navigation
   - Brand: `Portfolio MRI` / `Investment Decision Room`.
   - Links: `Workflow`, `Evidence`, `System`, `Boundaries`.
   - CTA: `Enter Platform` to `/onboarding/sign-in`.

2. Hero
   - Eyebrow: `Diagnosis-first portfolio intelligence`.
   - H1: `Understand the portfolio before changing it`
   - Body: `Portfolio MRI turns current holdings into stress-tested evidence, then tests one bounded candidate path only after the problem is named.`
   - CTAs: `Enter Platform`, `Read workflow`.
   - Boundary row: `Current portfolio first`, `Stress evidence before candidates`, `One review lineage`.

3. Evidence problem section
   - H2: `Most portfolio tools jump straight to the fix`
   - Explains that Portfolio MRI makes current holdings, stress behavior, and the named problem visible before a candidate path appears.
   - Cards: `Optimize first`, `Stress later`, `Lose lineage`.

4. Workflow section
   - H2: `A strict chain from raw holdings to a grounded verdict`
   - Shows five high-level cards: Input Portfolio, Diagnosis, Stress Lab, Client Fit, Verdict.
   - This is a public explanation, not the full platform sidebar.

5. System map section
   - H2: `A decision room for portfolio evidence`
   - Body explains the same review context moving through current portfolio, stress behavior, Client Fit context, candidate test, comparison, and verdict.
   - Cards: Portfolio Diagnosis, Stress Test Lab, Problem Classification, Candidate Launchpad, Current vs Candidate, Decision Verdict.

6. Boundaries section
   - H2: `Built to preserve diagnostic discipline`
   - Stats/cards: `Current first`, `Evidence first`, `One path`, `Same run`.

7. Final CTA
   - H2: `Open the investment decision room`
   - Copy says the user signs in, answers setup questions, and enters the current portfolio. The first output is diagnosis: exposure, stress behavior, and the problem worth testing.
   - CTA: `Enter Platform`.
   - Legal line: `Portfolio MRI provides non-binding diagnostic decision support. It does not provide investment advice, suitability approval, or trade instructions.`

## `/onboarding/sign-in`

Role: required email-first entry before onboarding.

Main content:

- H1: `Sign in before opening the diagnostic room.`
- Explanation: Portfolio MRI saves the planning profile before the portfolio screen.
- Step strip: `01 Email first`, `02 Verify code`, `03 Then onboarding`.
- Card stage 1:
  - Label: `Step 01 / Email`.
  - H2: `Enter your email`.
  - Input: email address.
  - CTA: `Continue`.
- Card stage 2 after email submission:
  - Label: `Step 02 / Verification`.
  - H2: `Verify your code`.
  - Input: verification code.
  - CTA: `Verify and continue`.
- Local-only fallback:
  - Button: `Continue locally while Supabase is not ready`.
  - This sets the dev bypass and sends the user to `/onboarding/name`.

## `/onboarding/name`

Role: friendly personal setup before portfolio input.

Main content:

- Frame progress: Name / Intake / Setup.
- H1: `What should we call you?`
- Description: name is only used to personalize intake before the portfolio screen opens.
- Input: `Name`.
- CTA: `Continue` to `/onboarding/investor-type`.

## `/onboarding/investor-type`

Role: one-question-at-a-time profile intake that maps to Client Fit context.

Main content:

- H1: `Five questions before we open the portfolio screen.` with the name appended when available.
- Description: answers prepare a starting planning preset before Portfolio Input.
- Progress: `Question X of 5` and percent.
- Questions in order:
  1. `If this portfolio fell 25% in three months...`
  2. `When will this money need to work for withdrawals...`
  3. `What temporary loss limit should trigger concern...`
  4. `What return target would make the risk worthwhile...`
  5. `If the current portfolio is concentrated...`
- Navigation: `Back`, `Next question`, and final `Save intake and open Portfolio Input`.

## `/onboarding/loading`

Role: visible setup transition after intake.

Main content:

- H1: `Setting up your experience`.
- Progress percent animation.
- Setup messages:
  - personalizing diagnostic room with selected profile;
  - saving Client Fit context;
  - preparing portfolio input workspace;
  - keeping diagnostics current-portfolio-first;
  - opening the decision room.
- Redirects to `/workspace` when saved workspace/history exists for a returning signed-in user; otherwise redirects to `/portfolio-input` for a first portfolio input.

## Platform route shell

The shell begins after onboarding. The journey labels and step numbers are:

| Step | Route | Sidebar label | Role |
| --- | --- | --- | --- |
| 01 | `/portfolio-input` | Portfolio | Define the current portfolio. |
| 02 | `/diagnosis` | Diagnosis | Diagnose current portfolio exposures and weaknesses. |
| 03 | `/evidence` | Stress Lab | Show stress behavior and evidence limits. |
| 04 | `/client-fit` | Client Fit | Compare evidence with the provided profile. |
| 05 | `/hypothesis` | Hypothesis | Select and prepare one diagnostic test path. |
| 06 | `/comparison` | Comparison | Compare current vs one generated candidate. |
| 07 | `/verdict` | Verdict | Show non-binding decision-support outcome. |
| 08 | `/report` | Report | Produce a grounded client-ready preview. |

## `/workspace`

Role: signed-in account home and review-history hub. This route restores saved work and lets the user choose what to continue. It is not a calculation stage and must not start diagnosis, refresh market data, generate candidates, compare portfolios, or regenerate verdict/report artifacts on load.

Main blocks:

1. Current workspace card
   - Shows active portfolio name, latest review status, and saved review count.
   - CTAs: `Continue review`, `Start new review`, and `Refresh workspace`.
   - Copy states that opening a saved portfolio starts a new review and completed reviews remain unchanged.

2. Portfolio library
   - Shows active saved portfolios by default.
   - Archived portfolios are hidden unless the user opens the archive view.
   - Loading a saved portfolio prepares a new or existing draft; it does not mutate completed review evidence.

3. Review history
   - Shows past reviews for the signed-in user with portfolio snapshot summary, status, stage chips, and archived state.
   - Past reviews are clearly labeled read-only when full local evidence cannot be restored.

## `/portfolio-input`

Role: Step 01, define the current portfolio case file and run diagnosis.

Diagnostic Case File order:

1. `Portfolio to diagnose` top card: holdings count and total weight for the current allocation.
2. `Input readiness` top card: the readiness blocker or ready state in investor language.
3. `Client Fit context` top card: profile presence as non-binding diagnostic context.
4. Client Fit profile detail and intake adjustment.
5. Holdings and weights input with investor currency.
6. Validation / readiness state and `Run diagnosis` CTA.
7. Saved portfolio, recovery, staged-progress, and technical validation details stay secondary or collapsed.

Top-layer metrics: holdings count, total weight, investor currency, and Client Fit profile presence.

The user should understand: the current portfolio to diagnose has been entered, or the exact missing input is clear. The first viewport must not behave like an optimizer setup screen and must not lead with raw recovery IDs or staged backend progress.

## `/diagnosis`

Role: Step 02, current portfolio diagnosis before candidate tests.

Diagnostic Case File order:

1. `Main diagnosis`: dominant current-portfolio finding.
2. `Why it matters`: investor interpretation of why the issue matters.
3. `Key evidence`: primary issue, main exposure, downside evidence, and evidence quality.
4. Primary diagnostic canvas naming material drivers and the next risk review.
5. Stress Lab CTA as the next safe decision.
6. `Detailed diagnostics` collapsed below the first-read answer.

Top-layer metrics: primary issue, main exposure, concentration, worst observed downside, and evidence quality.

Drill-down contains the grouped MetricMatrix, VaR/ES/skewness/kurtosis/beta/Sharpe/Sortino/Treynor, legacy technical `portfolio_xray.json` detail, evidence-chain notes, provenance, and limitations. The page must not recommend a rebalance from diagnosis alone.

## `/evidence`

Role: Step 03, Stress Test Lab for the current portfolio only.

Diagnostic Case File order:

1. `Stress failure mode`: the main way the current portfolio breaks under stress.
2. `Worst scenario`: scenario name and estimated loss when available.
3. `Loss drivers and protection gap`: drivers, offset behavior, and evidence quality.
4. Stress evidence summary and grouped stress metrics with investor meaning.
5. Scenario contribution and protection canvas.
6. Scenario library, selected scenario detail, factor attribution, evidence trace, and limitations remain secondary technical details.
7. Next decision: continue to Client Fit.

Top-layer metrics: worst scenario, estimated stress loss, loss drivers, hedge/protection gap, and evidence confidence.

The page must not create candidate, verdict, rebalance, or trade-advice language.

## `/client-fit`

Role: Step 04, non-binding profile-fit interpretation after Stress Lab.

Diagnostic Case File order:

1. `Fit interpretation`: one profile-fit conclusion in plain language.
2. `Main mismatch`: the most important portfolio-vs-profile conflict, when present.
3. `Profile context`: source quality and diagnostic-only boundary.
4. Profile metric rows with investor meaning.
5. `How we checked this` collapsed detail for technical evidence and raw profile context.
6. Next decision: continue to Hypothesis.

Top-layer metrics: drawdown tolerance versus portfolio downside, horizon context, meaningful target/volatility mismatch, and profile source quality.

Client Fit remains diagnostic context only. It is not suitability approval, not trade advice, and not proof that no portfolio issue exists.

## `/hypothesis`

Role: Step 05, select one diagnostic hypothesis and prepare/generate one candidate test.

The route remains a merged MVP route, but visible content is split into four sections:

1. `Problem Classification`: named problem, severity/confidence, and evidence behind classification.
2. `Candidate Launchpad`: investment hypothesis, mathematical method, and why the method fits the problem.
3. `Alternatives Builder`: test setup, success criteria, and trade-off to watch.
4. `Candidate Generation Result`: candidate created/failed, method used, and readiness for comparison.

Top-layer metrics: problem severity, problem confidence, selected investment hypothesis, selected mathematical method such as Minimum CVaR, first success criterion, and main trade-off.

Other tests, monitor/data paths, method internals, min/max asset weights, capped/uncapped settings, and developer details remain secondary. Generated candidate weights are not the main Hypothesis answer; they are reviewed on `/comparison`.

## `/comparison`

Role: Step 06, compare the current portfolio with one generated diagnostic test candidate.

Diagnostic Case File order:

1. `What improved`: the strongest improvement signal.
2. `What worsened`: the main cost or trade-off.
3. `Is the trade-off meaningful?`: materiality and evidence confidence.
4. Comparison evidence summary and matrix with investor interpretation.
5. Client Fit impact if meaningful.
6. Allocation tables, warnings, and technical notes stay in secondary detail.
7. Next decision: continue to Verdict.

Top-layer metrics: main improvement, main cost/trade-off, materiality, Client Fit impact when meaningful, and evidence confidence.

The page must show trade-offs without winner, switch, recommendation, or final-verdict framing.

## `/verdict`

Role: Step 07, non-binding decision-support verdict.

Diagnostic Case File order:

1. `Decision stance`: one of `Keep current`, `Review rebalance`, `Test another candidate`, or `Evidence insufficient`.
2. `Reason`: the primary evidence supporting the stance.
3. `What would change the verdict`: the main limitation or monitoring trigger.
4. Selected verdict evidence and rationale.
5. Client Fit as one input, not approval.
6. Detailed rationale, provenance, limitations, and lineage details stay secondary.
7. Next decision: open Report or test another hypothesis.

Top-layer metrics: decision status, confidence, main evidence, main limitation, and next action.

The page avoids recommendation, approval, safety, guarantee, and trade-instruction language.

## `/report`

Role: Step 08, grounded client-ready report preview.

Diagnostic Case File order:

1. `Plain-English explanation`: narrative summary of the active review.
2. `Evidence used`: selected diagnosis, stress, Client Fit, comparison, and verdict evidence.
3. `Limitations`: warnings, unavailable evidence, and next observation point.
4. ClientReadyReportPreview narrative.
5. Evidence used, warnings, unavailable evidence, timestamp, and grounding trace stay secondary.

Top-layer metrics: main diagnosis, stress evidence, comparison result, and verdict stance.

The report does not duplicate every page metric, does not expose raw provenance as the first answer, and does not add unsupported conclusions.

## `/client-profile`

Role: advanced/manual Client Fit editor, not the main onboarding path.

Header:

- Kicker: `Advanced / Client Fit profile editor`.
- H1: `Manual diagnostic context`.
- Boundary: Client Fit is not suitability approval and does not change optimizer behavior.

Main blocks:

- Planning answers.
- Suggested preset/profile summary.
- Editable target rows.
- CTA: `Use suggested profile`.
- CTA: `Save profile and continue to Portfolio Input`.

## `/onboarding/goals`

Role: compatibility-only redirect to the current `/onboarding/investor-type` intake.

Visible structure:

- Safe fallback card explaining that onboarding moved.
- Primary link to continue to `/onboarding/investor-type`.
- No platform rail, goal-screen semantics, portfolio diagnostics, or Client Fit suitability copy.

## Metrics and data presentation rules

- Metric cards show label, value, optional status badge, and short explanation.
- Values are display summaries from compact review state and FastAPI public envelopes, not raw artifact dumps.
- Stress metrics are evidence facts, not candidate instructions.
- Client Fit target rows are diagnostic context, not mandates.
- Comparison metrics must balance improvements and costs.
- Report copy must stay grounded in active review evidence and limitations.

## `/sandbox/components`

Role: local design-system and product-component gallery for iterating on the Portfolio MRI dark decision-room foundation without breaking production routes.

Main content:

- Verdict-style sandbox hero explaining the foundation.
- Primitive controls: primary, secondary, ghost, risk, disabled, long-label, and mobile-width actions; restrained status badges.
- Surface previews for glass, raised, subtle, warning, and risk panels.
- Evidence item, EvidenceStrip, EvidenceSummary, MetricMatrix, and ComparisonMetricMatrix previews.
- Active diagnostic-test context preview for downstream route consistency.
- Empty, loading, error, locked, partial evidence, read-only history, stale lineage, evidence-insufficient, test-candidate unavailable, and failed-generation state previews.
- Collapsed AdvancedDisclosure preview for technical or long-form states.

This route is not part of the user journey, does not alter the 8-step gated rail, and must not call backend review APIs.
