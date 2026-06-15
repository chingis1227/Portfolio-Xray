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

Public routes (`/` and `/onboarding/*`) do not show the platform sidebar or top journey rail. They use a dark graphite background, radial atmospheric gradients, moving-grid accents, rounded cards, and blue CTAs.

Platform routes show:

- left sidebar brand block: `Portfolio MRI` / `Investment Decision Room`;
- account navigation entry for `Workspace` outside the 8-step review rail;
- gated journey rail with 8 steps: Portfolio, Diagnosis, Stress Lab, Client Fit, Hypothesis, Comparison, Verdict, Report;
- sticky top progress rail with the current route step;
- large page header card;
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

Role: signed-in account home and compact review-history hub. This route restores saved work and lets the user choose what to continue. It is not a calculation stage and must not start diagnosis, refresh market data, generate candidates, compare portfolios, or regenerate verdict/report artifacts on load.

Main blocks:

1. Current workspace card
   - Shows active portfolio name, latest review status, latest `reviewId`, and stage readiness.
   - CTAs: `Continue review`, `Edit as new draft`, and `Start new review`.
   - Copy states that logging in restores saved work and does not recalculate automatically.

2. Portfolio library
   - Shows active saved portfolios by default.
   - Archived portfolios are hidden unless the user opens the archive view.
   - Loading a saved portfolio prepares a new or existing draft; it does not mutate completed review evidence.

3. Review history
   - Shows compact reviews for the signed-in user with portfolio snapshot summary, status, stage chips, and archived state.
   - `Open compact summary` is read-only when live run-local lineage is unavailable.
   - `Recover live review` is available only when same-owner backend lineage can be verified.

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

Header:

- Kicker: `Step 02 / Portfolio Diagnosis`.
- H1: `Current Portfolio Diagnosis`.
- Description: `Current-portfolio review before any candidate test.`

Locked state:

- H2: `Complete Portfolio Input first to unlock Diagnosis.`
- Copy asks the user to enter the current portfolio and run diagnosis.
- CTA: `Go to Portfolio Input`.

Ready state:

- Shows diagnosis summary panels, Portfolio Diagnosis blocks, evidence chain context, and site explanation when available.
- Metrics are shown through decision cards and metric cards, not as raw backend JSON.

## `/evidence`

Role: Step 03, Stress Test Lab for current portfolio only.

Header:

- Kicker: `Step 03 / Stress Test Lab`.
- H1: `Stress Test Lab`.
- Boundary: no candidate or rebalance verdict is created here.

Locked state:

- Status: `Stress review locked`.
- H2: `Complete Portfolio Input first to unlock Stress Test Lab.`
- CTA: `Go to Portfolio Input`.

Ready state:

- Shows scenario library, selected scenario detail, helped/hurt assets, loss contribution, hedge gap, scorecard, factor stress attribution, and data limitations.
- Metrics are scenario/evidence facts tied to current portfolio stress behavior.

## `/client-fit`

Role: Step 04, non-binding profile-fit check after Stress Lab.

Header:

- Kicker: `Step 04 / Client Fit`.
- H1: `Does this risk fit the provided profile?`
- Boundary: Client Fit status is not diagnostic quality and is not a decision action.

Locked state:

- Status: `Client Fit locked` / `Evidence required`.
- H2: `Run profile-first diagnosis before Client Fit.`
- CTAs: `Open Client Profile`, `Portfolio Input`.

Ready state:

- Shows status, profile confidence/source quality, target rows, portfolio values, target/limit values, and explanations.
- CTA: `Continue to Hypothesis`.

## `/hypothesis`

Role: Step 05, select one diagnostic hypothesis and prepare/generate one candidate test.

Header:

- Kicker: `Step 05 / Hypothesis`.
- Candidates are test portfolios for comparison, not recommendations.

Locked state:

- H1: `Hypothesis is locked`.
- Copy asks the user to complete Portfolio Input first.
- CTA: `Go to Portfolio Input`.

Ready state:

- Shows current diagnosis, recommended test, launchpad cards, selected test setup, candidate generation state, and continue-to-comparison action when valid.
- Candidate language must remain test/hypothesis language.

## `/comparison`

Role: Step 06, compare current portfolio with one generated diagnostic candidate.

Header:

- Kicker: `Step 06 / Comparison`.
- H1: `Current vs Candidate Comparison`.
- Boundary: comparison does not create a final decision or rebalance instruction.

Blocked state:

- Status: `Comparison required`.
- H2: `Generate a test candidate first`.
- CTA: `Return to Hypothesis Builder`.

Ready state:

- Shows current vs candidate values, improved/worsened/similar/unavailable evidence, trade-off summary, Client Fit context when available, and materiality cues.

## `/verdict`

Role: Step 07, non-binding decision-support verdict.

Header:

- Kicker: `Step 07 / Verdict`.
- H1: `Decision verdict`.
- Boundary: no-trade and evidence-insufficient are valid outcomes.

Blocked state:

- Status: `Verdict required`.
- H2: `Verdict unavailable`.
- CTA: `Return to Hypothesis Builder`.

Ready state:

- Shows verdict outcome, rationale, confidence/limitations, comparison links, and next safe step.
- Must not say trade now, must rebalance, best portfolio, or suitability approved.

## `/report`

Role: Step 08, grounded client-ready report preview.

Header:

- Kicker: `Step 08 / Report`.
- H1: `Client-ready report preview`.
- Description: concise narrative grounded in active review evidence.

Blocked states:

- Start with portfolio review first.
- Generate/select candidate first.
- Complete active comparison first.
- Complete active verdict first.

Ready state:

- CTA: `Create preview`.
- Shows grounded diagnosis/test/comparison/verdict narrative, evidence used, unavailable evidence, warnings/limitations, timestamp, and next observation point.

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
