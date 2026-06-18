# Current Website Structure

Status: current source-of-truth description of the implemented Portfolio MRI frontend website in `frontend/`.

This document describes what the current site shows: route order, page blocks, visible copy, CTAs, status states, and how metrics are presented. It is not a backend formula spec and does not override product, data, or output contracts.

## Canonical entry and local shortcut

Canonical product entry:

```text
/ -> /onboarding/sign-in -> /onboarding/name -> /onboarding/investor-type -> /onboarding/loading -> /workspace -> /portfolio-input
```

`/workspace` is the signed-in account home for returning users with saved workspace, portfolio, draft, or review history. First-time users without saved workspace data may continue directly from onboarding to Portfolio Input.

Local testing shortcut:

```text
/onboarding/name?dev_bypass=1
```

The shortcut is allowed for local preview while email sign-in is still being stabilized. It is not the documented product path and must not replace sign-in in product docs, demo scripts, or public copy.

## Global visual frame

Public routes (`/` and `/onboarding/*`) do not show the platform journey rail, navigation dock, or top journey rail. They use a dark graphite background, radial atmospheric gradients, moving-grid accents, rounded cards, and blue CTAs.

Platform routes show:

- a persistent top utility header above platform content, with product/route title, active portfolio name, investor currency, holdings count, review status, a single screen-level evidence-quality indicator when available, data window when provided, last update, and a primary route CTA area;
- a fixed vertical graphite journey rail on wide screens, positioned beside the content blocks;
- account navigation entry for `Workspace` outside the 8-step review rail;
- a bottom glass journey dock on narrower screens, with compact `Workspace` and optional account controls;
- gated journey navigation with 8 icon-led steps: Portfolio, Diagnosis, Stress Lab, Client Fit, Hypothesis, Comparison, Verdict, Report;
- no sticky top journey rail on redesigned analytical routes; compact step context appears inside `VerdictHero`;
- verdict-first page hero on redesigned analytical routes;
- platform content constrained to roughly 1180-1240px so analytical screens read as a focused decision room instead of a dashboard wall;
- content cards, tables, badges, and locked states.

## `/` Landing

Role: public product page that explains Portfolio MRI before the platform opens.

Block order:

1. Header navigation
   - Brand: `Portfolio MRI` / `Investment Decision Room`.
   - Links: `Problem`, `How it works`, `Architecture`, `Precision`.
   - CTA: `Enter Platform` to `/onboarding/sign-in`.

2. Hero
   - Eyebrow: `PORTFOLIO MRI`.
   - Label: `PORTFOLIO DIAGNOSTICS & INVESTMENT DECISION-SUPPORT SYSTEM`.
   - H1: `Diagnose portfolio risk before you rebalance.`
   - Body: `Portfolio MRI turns current holdings into stress-tested decision evidence before any alternative is considered.`
   - CTAs: `Enter Platform`, `See how it works ?`.
   - Trust chips: `Current portfolio first`, `Stress-tested evidence`, `Candidate tests, not orders`.

3. Problem section
   - H2: `TOO MANY TICKERS. TOO LITTLE DIAGNOSIS.`
   - Explains that a list of ETFs, funds, stocks, and cash is not a diagnosis.
   - Bullets: no allocation logic, no hidden concentration view, no stress evidence before changing, no framework to defend a decision.

4. Workflow section
   - H2: `FROM RAW HOLDINGS TO A DEFENSIBLE DECISION PATH.`
   - Shows five high-level cards: Input, Diagnosis, Stress Lab, Client Fit, Verdict.
   - This is a public explanation, not the full platform sidebar.

5. Architecture section
   - H2: `DIAGNOSIS ARCHITECTURE, NOT AN OPTIMIZER COCKPIT.`
   - Cards: Portfolio Diagnosis, Stress Test Lab, Problem Classification, Candidate Launchpad, Current vs Candidate, Grounded Report.

6. Precision section
   - H2: `BUILT FOR PRECISION.`
   - Stats/cards: `Current first`, `1 path`, `Run-local`, `Non-binding`.

7. Final CTA
   - H2: `OPEN THE DECISION ROOM.`
   - Copy says the user signs in, answers setup questions, then enters tickers and weights.
   - CTA: `Enter Platform`.

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

Role: Step 01, define the current portfolio and run diagnosis.

Header:

- Kicker: `Step 01 / Portfolio to diagnose`.
- H1: `Define the current portfolio`.
- Description: enter the portfolio as it stands today before any alternative is tested.

Main blocks:

1. Client Fit profile card
   - Shows profile label such as `Balanced`.
   - Shows target return, volatility, temporary loss, horizon.
   - CTA: `Adjust intake`; saving manual target rows reclassifies the displayed profile label from the edited return, volatility, drawdown, and horizon.

2. Current allocation only explanation
   - Explains that the diagnosis checks the current allocation before alternatives.

3. Investor currency
   - Select values: USD or EUR.

4. Holdings and weights table
   - Ticker / cash, instrument, weight, actions.
   - CTAs: `Add holding`, `Add cash position`, `Remove row`.
   - First-time entry starts with empty input fields, not a prefilled demo allocation.
   - Empty guidance tells the user to add at least two current positions and treats cash as a position.
   - Empty ticker fields use a neutral light shimmering border; red appears only after invalid user input.
   - Cash is treated as a portfolio position.

5. Validation / readiness state
   - Shows whether instruments, weights, currency, and Client Fit profile are ready.
   - CTA: `Run diagnosis` when valid.

6. Recovery panel
   - H2: `Reload an existing review by ID`.
   - CTA: `Recover active review`.

## `/diagnosis`

Role: Step 02, current portfolio diagnosis before candidate tests.

Primary hero:

- Shared `VerdictHero` with compact context `Step 02 of 8 - Portfolio Diagnosis`.
- Headline: dominant current-portfolio diagnosis from the active review.
- Interpretation: one concise sentence explaining why the diagnosis matters.
- Supporting facts: review scope, evidence quality, and next safe step.
- Boundary note: diagnostic current-portfolio review, not a rebalance recommendation.

Locked state:

- H2: `Complete Portfolio Input first to unlock Diagnosis.`
- Copy asks the user to enter the current portfolio and run diagnosis.
- CTA: `Go to Portfolio Input`.

Ready state:

- Shows the persistent `PlatformTopHeader`, then the shared `VerdictHero`, an `EvidenceSummary` with primary issue, materiality, supporting evidence, and next safe step.
- Shows one primary diagnostic canvas combining concentration, dominant exposure, and main weakness before any metric matrix.
- Replaces the previous first-read card grid with a compact grouped `MetricMatrix`: risk pressure, portfolio structure, and secondary observations.
- Does not show the standalone `Diagnosis explanation` wall in the normal ready state. Evidence-chain and technical text are integrated into collapsed advanced diagnostics when available.
- Professional metrics such as VaR, ES, skewness, kurtosis, beta, Sharpe, Sortino, and Treynor remain secondary behind `Advanced diagnostics and technical evidence`.
- Metrics are shown through matrix rows, not as raw backend JSON or repeated unavailable/evidence badges.

## `/evidence`

Role: Step 03, Stress Test Lab for current portfolio only.

Primary structure:

- Shared `VerdictHero` with compact context `Step 3 of 8 - Stress Lab`.
- Headline is the current-portfolio stress answer, such as material stress vulnerability or limited stress evidence.
- Interpretation states the worst visible stress behavior and the current-portfolio-only boundary.
- `EvidenceSummary` shows worst scenario, estimated loss, loss drivers/protection behavior, and evidence quality when available.
- A grouped `MetricMatrix` shows stress vulnerability and scenario evidence rows.
- A single analytical canvas keeps scenario contribution and hedge protection together.
- Scenario library, selected scenario detail, factor attribution, evidence trace, and limitations remain secondary technical details.

Locked or compact-history states explain the missing stress model and route the user back to Portfolio Input.

The page must not create candidate, verdict, rebalance, or trade-advice language.


## `/client-fit`

Role: Step 04, non-binding profile-fit check after Stress Lab.

Primary structure:

- Shared `VerdictHero` with compact context `Step 4 of 8 - Client Fit`.
- Hero states the main alignment or mismatch with the provided profile.
- Boundary note states that Client Fit is diagnostic context only, not suitability approval, not trade advice, and not a replacement for diagnosis.
- `EvidenceSummary` shows the main mismatch dimensions.
- `MetricMatrix` shows portfolio value, profile target/reference, restrained row status, and explanation for each target row.
- Missing profile and evidence-required states remain visible and non-failing.
- Technical evidence details remain collapsed below the main fit read.

The page reduces repeated `Outside`/aligned badges and keeps Client Fit from clearing material diagnosis issues.


## `/hypothesis`

Role: Step 05, select one diagnostic hypothesis and prepare/generate one candidate test.

Primary structure:

- Shared `VerdictHero` with compact context `Step 5 of 8 - Hypothesis`.
- Hero names the proposed diagnostic test and states that the candidate is a test, not a rebalance recommendation.
- `EvidenceSummary` shows why this test was selected, first success criterion, trade-off to watch, and candidate boundary.
- The primary diagnosis recap and proposed test panel appear before the builder controls.
- The builder action console is visually secondary and prepares one candidate attempt only.
- Client Fit context, alternative tests, and evidence/technical details are secondary panels.
- The page intentionally does not use `MetricMatrix` as the primary pattern.

Generated candidate weights are not the main Hypothesis content; they are reviewed on `/comparison`.


## `/comparison`

Role: Step 06, compare current portfolio with one generated diagnostic candidate.

Primary structure:

- Shared `VerdictHero` with compact context `Step 6 of 8 - Comparison`.
- Hero states whether comparison evidence is available and repeats that this is diagnostic comparison only.
- `EvidenceSummary` promotes only selected material comparison facts when comparison evidence is available.
- Empty, unavailable, ready-to-run, retry, read-only history, and candidate-not-comparable states remain visible.
- Ready state uses comparison `MetricMatrix` groups: risk improvement, trade-offs, fit impact, and evidence quality.
- Allocation lists, warnings, and technical comparison notes are secondary details.

The page must show trade-offs without winner, switch, recommendation, or final-verdict framing.


## `/verdict`

Role: Step 07, non-binding decision-support verdict.

Primary structure:

- Shared `VerdictHero` with compact context `Step 7 of 8 - Verdict`.
- Hero presents the cautious decision interpretation and a visible boundary: diagnostic interpretation only, not trade advice or suitability approval.
- `EvidenceSummary` shows selected verdict evidence, rationale, major trade-off or limitation, and boundary.
- Ready state uses narrative cards for decision interpretation, rationale, evidence quality, and what would change the verdict.
- Client Fit is shown as one input to the verdict, not as an approval.
- Evidence-insufficient and candidate-failed states remain valid outcomes with recovery paths.

The page avoids recommendation, approval, safety, and trade-instruction language.


## `/report`

Role: Step 08, grounded client-ready report preview.

Primary structure:

- Shared `VerdictHero` with compact context `Step 8 of 8 - Report`.
- Hero frames the page as a narrative report preview grounded in active evidence.
- `EvidenceSummary` includes selected evidence only: main diagnosis, stress evidence, Client Fit/comparison context when returned, and final verdict.
- Report grounding trace is secondary detail.
- Ready state shows `ClientReadyReportPreview` as a narrative executive summary with supporting sections, next observation, and boundary.
- Evidence used, warnings, unavailable evidence, and timestamp are secondary support, not a dashboard wall.

The report does not duplicate every metric from every page and does not add unsupported conclusions.


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

## Metrics and data presentation rules

- Metric cards show label, value, optional status badge, and short explanation.
- Values are display summaries from compact review state and FastAPI public envelopes, not raw artifact dumps.
- Stress metrics are evidence facts, not candidate instructions.
- Client Fit target rows are diagnostic context, not mandates.
- Comparison metrics must balance improvements and costs.
- Report copy must stay grounded in active review evidence and limitations.
