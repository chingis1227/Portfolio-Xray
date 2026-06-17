# Portfolio MRI Redesign PRD

## Objective

Redesign the Portfolio MRI web experience to feel more premium, calm, structured, and trustworthy for investors and advisors without deeply changing the current product logic.

The redesign must preserve the diagnosis-first, current-portfolio-first journey. The product should continue to help users understand what is wrong with the current portfolio, why it matters, what evidence supports the conclusion, and what should be tested next.

The target design direction is:

**Bloomberg meets private bank** — dark, strict, analytical, premium, calm, and free of bright SaaS-style gradients.

## Design Principles

### 1. One primary answer per page

Each key page must start with one clear page-level verdict. The user should immediately understand the main conclusion before reading evidence or technical detail.

Examples:

- Stress Lab: `Material stress vulnerability detected`
- Client Fit: `Portfolio is outside stated risk profile`
- Hypothesis: `Improve crisis resilience`
- Comparison: `Candidate improves stress resilience, with trade-offs`
- Verdict: `Proceed to review, not a recommendation`

The verdict is the page's main headline. Traditional section titles such as `Stress Test Lab` or `Hypothesis Builder` should move into smaller contextual labels.

### 2. Reduce panel overload

The current interface uses too many similar dark panels, cards, badges, and nested blocks. The redesign must reduce the number of visible containers and make page hierarchy easier to scan.

The UI should avoid presenting every metric as an individual card. Cards should be reserved for genuinely important summary elements, not used as the default layout for all data.

### 3. Replace card grids with structured metric matrices where needed

Pages with many metrics should use a `Metric Matrix` pattern instead of a grid of small cards.

The Metric Matrix should organize metrics by group, show values and statuses in a consistent format, and provide short explanations without requiring the user to open many separate panels.

### 4. Progressive disclosure without hiding everything

The redesign should not solve complexity by placing all details behind collapsed sections. Users should see:

1. the main verdict;
2. the main evidence;
3. the most important metric matrix or comparison structure;
4. optional technical details only after the main story is clear.

Important evidence should remain visible. Deep technical evidence can be secondary.

### 5. Calm premium visual system

The UI should feel like a high-trust financial decision room, not a technical lab dashboard. Use dark surfaces, restrained contrast, fewer borders, more consistent spacing, and a limited color system.

## Color System

The redesign must use four documented semantic colors.

### 1. Soft White / Ivory

Purpose:

- primary text;
- main headlines;
- key numeric values;
- neutral premium clarity.

Usage:

- use for the main reading layer;
- avoid pure harsh white where possible;
- maintain strong readability on dark backgrounds.

### 2. Steel Blue

Purpose:

- active navigation state;
- selected state;
- analytical focus;
- links and interactive emphasis.

Usage:

- use for current step indication;
- use for selected tabs or selected options;
- use sparingly to guide attention.

### 3. Muted Copper Red

Purpose:

- material risk;
- outside profile state;
- negative portfolio signal;
- warning that requires attention.

Usage:

- use only when the portfolio or evidence indicates an actual risk issue;
- avoid repeating the same red status badge many times on the same screen;
- one page-level risk state should be enough unless row-level status is necessary.

### 4. Muted Amber Gold

Purpose:

- uncertainty;
- limited evidence;
- caveat;
- assumption warning;
- incomplete data or confidence limitation.

Usage:

- use for confidence and evidence-quality caveats;
- do not use amber for material risk when copper red is the correct semantic color.

### Excluded system color

Green must not be used as a system-level status color in this redesign. Positive or ready states should use neutral styling, soft borders, or subtle text rather than a separate green success language.

## Feature: Verdict Hero

Each major screen must start with a `Verdict Hero`.

Product purpose:

The Verdict Hero gives the user the main answer first. It replaces large generic page titles as the primary headline.

Requirements:

- Show the page-level verdict as the largest text on the screen.
- Show one concise explanation sentence below the verdict.
- Show 2-3 critical supporting facts only when useful.
- Keep the screen context as a small label, such as `Step 3 of 8 · Stress Lab`.
- Avoid large decorative gradients.
- Avoid competing badges inside the hero unless the badge is essential.

Example structure:

```text
Step 3 of 8 · Stress Lab

Material stress vulnerability detected
Worst case: Severe recession · Estimated loss: -22.9%
Current portfolio only. No rebalance verdict is created here.
```

## Feature: Simplified Top Step Context

The current long horizontal top stepper must be removed or heavily simplified.

Product purpose:

The top of the page should not duplicate the sidebar or compete with the main verdict. It should only provide lightweight journey context.

Requirements:

- Replace the full horizontal journey navigation with a compact context label.
- Use the format: `Step X of 8 · Page Name`.
- Do not show every journey step across the top.
- Do not duplicate active-step indication from the sidebar.

## Feature: Quieter Desktop Sidebar

The desktop sidebar remains always visible, but it must become visually quieter.

Product purpose:

The sidebar provides stable journey navigation without adding visual noise.

Requirements:

- Keep the product name and short subtitle.
- Keep the journey step list.
- Keep completed, current, and unavailable states.
- Reduce heavy borders, bright outlines, dots, and repeated micro-elements.
- Use Steel Blue only for the active/current step.
- Make step numbers quieter than step names.
- Keep the sidebar readable but secondary to page content.
- Do not implement collapsed/presentation mode in this redesign phase.

Example sidebar content:

```text
Portfolio MRI
Decision Room

01 Portfolio
02 Diagnosis
03 Stress Lab
04 Client Fit
05 Hypothesis
06 Comparison
07 Verdict
08 Report
```

## Feature: Metric Matrix

The Metric Matrix is the primary pattern for pages with many metrics.

Product purpose:

The Metric Matrix lets users see many metrics without experiencing a wall of cards or needing to open many hidden panels.

Requirements:

- Use the Metric Matrix only where there are many metrics.
- Organize metrics into clear groups.
- Each row should include:
  - metric name;
  - portfolio value;
  - reference value or threshold where relevant;
  - status;
  - short explanation.
- Use compact rows and consistent alignment.
- Avoid turning every metric into a separate card.
- Keep row-level status visually restrained.
- Do not repeat the same status badge excessively.
- Allow secondary technical details below the matrix when needed.

Example:

```text
Risk pressure
Stress loss        -22.9%    Material issue    Worst visible stress result
Drawdown           -18.8%    Issue             Deep historical decline
Volatility          8.3%     Outside profile   Above stated comfort range

Portfolio structure
Concentration       —        Watch             Top holdings drive stress loss
Diversification     —        Neutral           Not the primary issue

Evidence quality
Scenario coverage   8/9      Limited           Historical replay incomplete
Confidence          High     Reliable enough   Signal is stable
```

## Feature: Page-Level Information Architecture

Analytical pages should follow a consistent reading order.

Product purpose:

Users should understand the answer first, then the evidence, then the details.

Required structure:

1. **Verdict Hero**  
   The primary answer and one-line interpretation.

2. **Evidence Summary**  
   A compact visible summary of the 3-4 most important facts.

3. **Metric Matrix or Main Analytical Canvas**  
   Structured detail for pages with many metrics.

4. **Optional Technical Detail**  
   Drill-downs, raw evidence, scenario tables, or technical explanations.

This structure should reduce page clutter while keeping important information accessible without excessive clicking.

## Feature: Evidence Summary

Each analytical page should include a compact evidence summary immediately after the Verdict Hero.

Product purpose:

The Evidence Summary explains why the system reached the verdict before the user reaches detailed data.

Requirements:

- Show 3-4 evidence items maximum.
- Use one shared visual container or a quiet strip, not many competing cards.
- Use concise labels and values.
- Include only evidence that directly supports the page-level verdict.
- Avoid repeating status language already shown in the hero.

Example:

```text
Primary issue       Weak crisis resilience
Main drivers        AAXJ, EWJ, SPY
Severity            Material
Evidence quality    Limited
```

## Feature: Diagnosis Page Redesign

The Diagnosis page should use the new page architecture and Metric Matrix.

Product purpose:

The user should quickly understand the dominant portfolio issue and the evidence supporting that diagnosis.

Requirements:

- Start with a Verdict Hero describing the dominant diagnosis.
- Show the primary issue, severity, main drivers, and evidence quality in the Evidence Summary.
- Replace large grids of diagnostic cards with a Metric Matrix.
- Group diagnosis metrics into clear categories such as:
  - risk pressure;
  - portfolio structure;
  - evidence quality;
  - secondary observations.
- Keep technical diagnostic evidence below the main matrix.

## Feature: Stress Lab Page Redesign

The Stress Lab page should use the new page architecture and Metric Matrix.

Product purpose:

The user should understand how the current portfolio behaves under stress, what the worst scenario is, and which assets drive the loss.

Requirements:

- Start with a Verdict Hero such as `Material stress vulnerability detected`.
- Keep the message clear that Stress Lab is current-portfolio-only and does not create a rebalance verdict.
- Show the worst scenario, estimated loss, main loss drivers, offset behavior, and evidence quality in the Evidence Summary.
- Use Metric Matrix for stress metrics and scenario evidence.
- Use a single analytical canvas for scenario contribution and asset impact instead of many small panels.
- Avoid repeating risk badges such as `Material vulnerability` across many elements.

## Feature: Client Fit Page Redesign

The Client Fit page should use the new page architecture and Metric Matrix.

Product purpose:

The user should understand whether the current portfolio aligns with the stated risk profile while preserving the non-binding diagnostic boundary.

Requirements:

- Start with a Verdict Hero such as `Portfolio is outside stated risk profile`.
- Clearly state that Client Fit is diagnostic context only and not suitability approval, trade advice, or a replacement for portfolio diagnosis.
- Show the main mismatch dimensions in the Evidence Summary.
- Use Metric Matrix for profile checks such as volatility, drawdown, stress loss, and other relevant dimensions.
- Avoid repeating `Outside` on every card. Use the page verdict once, then row-level status only where necessary.

## Feature: Comparison Page Redesign

The Comparison page should use a current-vs-candidate matrix where many metrics are compared.

Product purpose:

The user should understand what improved, what worsened, and what trade-offs the candidate introduces.

Requirements:

- Start with a Verdict Hero summarizing the comparison outcome.
- Use a comparison-focused Metric Matrix with columns for current portfolio, candidate portfolio, change, and interpretation.
- Group comparison rows by:
  - risk improvement;
  - trade-offs;
  - fit impact;
  - evidence quality.
- Highlight only material differences.
- Avoid turning each comparison metric into a standalone card.

## Feature: Hypothesis Page Redesign

The Hypothesis page should not use Metric Matrix as its main pattern.

Product purpose:

The page should help the user understand the selected diagnostic test and prepare a candidate test without feeling like an optimization dashboard.

Requirements:

- Start with a Verdict Hero focused on the proposed test, such as `Improve crisis resilience`.
- Show why this test was selected.
- Show success criteria clearly.
- Keep builder controls visually secondary and calm.
- Avoid excessive panels around controls.
- Preserve the boundary that this is a test candidate, not a rebalance recommendation.

## Feature: Verdict Page Redesign

The Verdict page should focus on decision summary, not metric density.

Product purpose:

The user should understand the final decision interpretation and the evidence behind it without reading a dense dashboard.

Requirements:

- Start with a clear decision-level Verdict Hero.
- Present the decision, rationale, major trade-offs, and boundaries.
- Use narrative summary and selected evidence rather than a full Metric Matrix.
- Preserve non-binding diagnostic language.

## Feature: Report Page Redesign

The Report page should read like an executive summary.

Product purpose:

The user should be able to review and share the main diagnostic story without navigating a complex analytical interface.

Requirements:

- Use a narrative report structure.
- Include the main diagnosis, stress evidence, client-fit context, comparison outcome, and final verdict.
- Use selected evidence only.
- Do not present every metric from every screen.
- Avoid dashboard-like clutter.

## Feature: Badge and Status Rationalization

Badges must become less frequent and more meaningful.

Product purpose:

The user should not see repeated labels like `Outside`, `Limited evidence`, or `Material vulnerability` in many places at once.

Requirements:

- Use page-level status in the Verdict Hero.
- Use row-level status only when it clarifies a specific metric.
- Avoid duplicating the same status across hero, cards, table rows, and side panels.
- Use badges sparingly.
- Keep badge colors bound to the four-color semantic system.
- Prefer text hierarchy and placement over many colored pills.

## Feature: Surface and Container System

The visual surface system must be simplified.

Product purpose:

The interface should feel calmer, more premium, and easier to scan.

Requirements:

- Reduce the number of nested cards.
- Use fewer borders.
- Use softer contrast between background and panels.
- Avoid bright or inconsistent gradients.
- Make primary content areas larger and less fragmented.
- Use whitespace and spacing to define hierarchy instead of many boxes.
- Keep technical detail visually secondary.

## Feature: Typography and Readability

The redesign must improve readability and reduce small-text overload.

Product purpose:

The site should feel trustworthy and executive-grade, not dense and difficult to read.

Requirements:

- Increase size and weight of page verdict headlines.
- Reduce the amount of very small text.
- Use concise explanations.
- Create clear hierarchy between headline, explanation, evidence labels, metric values, and technical notes.
- Ensure important values are readable without zooming.

## Feature: Product Boundary Language

The redesign must preserve Portfolio MRI's diagnostic and non-binding boundaries.

Product purpose:

The interface must remain clear that the system supports investment decision-making but does not provide trade instructions or suitability approval.

Requirements:

- Keep Client Fit described as diagnostic context only.
- Keep Stress Lab described as current-portfolio-only.
- Keep Hypothesis and Candidate flows described as tests, not recommendations.
- Keep Verdict language non-binding unless current product contracts explicitly change.
- Do not promote optimizer-first language.

## Initial Scope

This PRD covers visual and information architecture redesign only.

In scope:

- color system;
- page hierarchy;
- Verdict Hero;
- simplified top context;
- quieter sidebar;
- Metric Matrix;
- evidence summaries;
- reduced badges;
- reduced panel overload;
- page-level redesign requirements for Diagnosis, Stress Lab, Client Fit, Comparison, Hypothesis, Verdict, and Report.

Out of scope:

- changing backend formulas;
- changing portfolio diagnosis logic;
- changing candidate generation algorithms;
- adding full optimizer-first workflows;
- adding collapsed sidebar mode;
- adding new product modules;
- redesigning generated PDF output unless explicitly requested later.

## Acceptance Criteria

The redesign is successful when:

- every major page has one obvious primary verdict;
- the top stepper no longer duplicates the full journey;
- the sidebar remains visible but visually quieter;
- high-metric pages use Metric Matrix instead of card overload;
- repeated badges are reduced;
- the visual system uses the four documented colors consistently;
- green is not used as a system status color;
- the product feels calmer, more premium, and more trustworthy;
- diagnostic and non-binding product boundaries remain intact.
