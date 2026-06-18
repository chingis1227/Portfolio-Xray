# UX/UI Product Audit Sprint

Status: Active input
Date: 2026-06-18
Scope: Documentation and static frontend source audit only. No frontend code, backend code, generated output, styling, or runtime behavior was changed.

## 1. Purpose

This audit translates a professional design-thinking and component-driven product workflow into a
Portfolio MRI-specific UX/UI improvement roadmap.

The audit uses these external process references as methodology inputs only:

- Nielsen Norman Group, Design Thinking 101:
  `understand -> explore -> materialize`, with empathize, define, ideate, prototype, test, and implement.
- Nielsen Norman Group, 10 Usability Heuristics:
  broad interaction principles such as system-status visibility, match with the real world, consistency,
  error prevention, recognition rather than recall, and aesthetic/minimalist design.
- Atlassian Design Foundations:
  design foundations, tokens, accessibility, content, spacing, grid, color, typography, motion,
  iconography, components, and patterns.
- Storybook documentation:
  component-driven UI development in isolation, with stories capturing variations and edge cases.

This audit does not override `RULES.md`, `SPEC.md`, `PRODUCT.md`, `DESIGN.md`, screen contracts,
data rules, formulas, backend schemas, or output contracts.

## 2. Method

Reviewed sources:

- Current operating rules: `RULES.md`, `WORKFLOW.md`, `AGENTS.md`.
- Product/design contracts: `PRODUCT.md`, `DESIGN.md`,
  `docs/contracts/PRODUCT_FLOW_CONTRACT.md`,
  `docs/contracts/SCREEN_CONTRACTS.md`,
  `docs/contracts/DESIGN_SYSTEM_CONTRACT.md`,
  `docs/design/current_website_structure.md`,
  `docs/design/portfolio_mri_design_system.md`.
- Frontend structure:
  - `frontend/app/**/page.tsx`
  - `frontend/components/layout/`
  - `frontend/components/ui/`
  - `frontend/components/landing/`
  - `frontend/components/onboarding/`
  - `frontend/components/portfolio/`
  - `frontend/components/diagnosis/`
  - `frontend/components/evidence/`
  - `frontend/components/client-fit/`
  - `frontend/components/hypothesis/`
  - `frontend/components/comparison/`
  - `frontend/components/verdict/`
  - `frontend/components/report/`
  - `frontend/lib/journey.ts`
  - `frontend/package.json`

Not performed:

- No browser visual QA.
- No Playwright click-through.
- No real user testing.
- No Storybook install or stories.
- No component refactor.
- No CSS/token changes.
- No production route changes.

## 3. Executive Verdict

Portfolio MRI already has a stronger product/design foundation than a typical early UI:

- the product truth is clear: diagnosis-first, current-portfolio-first, decision-support only;
- the route chain is documented and mostly implemented around the current journey;
- a dark institutional visual thesis exists and is governed by active contracts;
- shared primitives already exist in `frontend/components/ui/`;
- `/sandbox/components` exists as a lightweight component gallery;
- `/diagnosis` already follows the intended first-read pattern better than the rest of the app.

However, the frontend is not yet operating like a top-tier component-driven product organization.
The main gaps are process and system maturity, not just visual polish:

1. There is no dedicated UX discovery brief tying users, pains, mental models, and decision jobs to each route.
2. Information architecture is documented, but the route implementations vary in how consistently they apply it.
3. Diagnosis has a benchmark composition model; several downstream screens still carry heavier page-local logic and local state components.
4. Component foundations exist, but some repeated states and patterns are still duplicated inside screens.
5. The current sandbox is useful but not yet equivalent to Storybook-style isolated state coverage.
6. The project has visual-design rules, but not yet a complete design QA matrix across desktop, mobile, long text, loading, partial evidence, error, locked, and read-only history states.
7. The UX has not yet been validated with real users or even scripted task-based usability sessions.

Recommended next move: do not start with a full visual redesign. Start with a controlled
foundation-first redesign program:

```text
UX brief
-> journey and screen-job map
-> route IA wireframes
-> component/state inventory
-> sandbox or Storybook state coverage
-> benchmark route hardening
-> route-by-route refactor
-> visual QA and usability checks
```

The best benchmark route is `/diagnosis`, because it is the product's core promise and already has
the cleanest separation between first-read diagnosis, evidence, diagnostic canvas, and advanced
technical detail.

## 4. Current Product Truth for UX Work

The current product must be treated as:

```text
Portfolio MRI = Investment Decision Room
```

It is not:

- a trading terminal;
- an optimizer cockpit;
- a portfolio recommendation engine;
- a suitability approval tool;
- a colorful metric dashboard;
- a PDF-first reporting product.

Current canonical product journey:

```text
Landing
-> Required email sign-in
-> Onboarding
-> Portfolio Input
-> Portfolio Diagnosis
-> Stress Test Lab
-> Client Fit
-> Hypothesis
-> Current vs Candidate Comparison
-> Decision Verdict
-> Report Preview
```

Core UX promise:

> Help a user understand the current portfolio first, see evidence and stress behavior, test one
> bounded diagnostic candidate when appropriate, and receive non-binding decision-support language
> with limitations visible.

Every design decision should be judged against that promise.

## 5. User and Job-to-Be-Done Framing

### 5.1 Primary user assumption

The implemented product appears to serve an investor, advisor, analyst, or financially literate
portfolio owner who has current holdings and wants a defensible risk/decision review before
considering changes.

This assumption is not yet formalized as a dedicated UX research artifact.

### 5.2 Core user jobs

| Job | User question | Product response |
| --- | --- | --- |
| Understand what the system is | "Is this an optimizer, report, or diagnostic room?" | Landing explains diagnosis-first decision support. |
| Enter current portfolio | "What holdings and weights are needed?" | Portfolio Input validates tickers, weights, currency, and blocking errors. |
| Understand current risk | "What is wrong or notable in my current portfolio?" | Diagnosis should lead with a clear diagnosis, not raw metrics. |
| Trust evidence | "Why should I believe this?" | Evidence / Stress Lab shows stress and support facts. |
| Add personal context | "Does this evidence fit my stated profile?" | Client Fit adds non-binding context. |
| Decide what to test | "What alternative hypothesis is worth checking?" | Hypothesis / Builder selects one diagnostic candidate test. |
| Compare trade-offs | "What changes if I test this candidate?" | Comparison shows current vs candidate evidence. |
| Interpret outcome | "What does the evidence support?" | Verdict gives decision-support only, not trade advice. |
| Save/explain | "How can I explain this later?" | Report preview summarizes grounded evidence and limitations. |

### 5.3 Missing discovery artifact

There is no obvious dedicated artifact that answers, in one place:

- who the primary and secondary users are;
- what user language should replace internal portfolio-engine terms;
- what confidence, fear, or confusion each stage must resolve;
- which tasks a first-time user should complete without help;
- where the product intentionally blocks, slows, or warns the user;
- which misconceptions must be prevented, especially optimizer-first and advice-like interpretations.

Recommendation: create a UX brief before broad UI redesign.

## 6. Journey Audit

### 6.1 Current route inventory

Current app route pages include:

```text
/
/onboarding/sign-in
/onboarding/name
/onboarding/investor-type
/onboarding/loading
/workspace
/portfolio-input
/diagnosis
/evidence
/client-fit
/hypothesis
/comparison
/verdict
/report
/client-profile
/sandbox/components
```

Additional route present in code:

```text
/onboarding/goals
```

Active documentation does not include `/onboarding/goals` in the canonical current route chain.
It appears to be a leftover or non-current route from an earlier onboarding design. This is not a
runtime finding; it is a static source/documentation alignment observation.

### 6.2 Route jobs

| Route | Current job | UX audit verdict |
| --- | --- | --- |
| `/` | Explain the product and send user to sign-in. | Strong current framing. Needs future real-user validation for whether "diagnosis before rebalance" is understood. |
| `/onboarding/sign-in` | Required email-first entry. | Product discipline is clear. Need to ensure local fallback never reads as normal public path. |
| `/onboarding/name` | Friendly identity setup. | Simple and focused. |
| `/onboarding/investor-type` | Five-question intake for Client Fit context. | Strong fit with Client Fit V1. Needs copy validation to ensure users do not treat this as suitability approval. |
| `/onboarding/loading` | Prepare context and route to workspace/input. | Good transition pattern if progress language stays simple. |
| `/workspace` | Account home/history hub, not calculation stage. | Correct product boundary. Needs careful empty-state design for first-time users. |
| `/portfolio-input` | Collect holdings, weights, and currency. | Critical conversion point. Needs dedicated usability testing around validation and ticker selection. |
| `/diagnosis` | Explain current portfolio diagnosis. | Best benchmark route. Already uses a stronger first-read structure. |
| `/evidence` | Stress Test Lab and evidence review. | Good placement after Diagnosis. Should avoid looking like a separate advanced analytics product. |
| `/client-fit` | Non-binding profile fit check. | Correct stage. Copy must keep "context, not approval" visible. |
| `/hypothesis` | Select one diagnostic hypothesis and prepare/generate candidate. | High complexity route. Needs wireframe and state simplification before visual polish. |
| `/comparison` | Compare current and generated candidate. | Correct route job. Needs strong empty/blocked states and clear lineage messaging. |
| `/verdict` | Generate evidence-grounded decision-support verdict. | Correct boundary. Must continue to avoid advice-like or trade-execution copy. |
| `/report` | Create grounded report preview. | Correct as preview, not default polished PDF product. |
| `/client-profile` | Advanced/manual Client Fit editor. | Correctly outside normal onboarding path. |
| `/sandbox/components` | Local component gallery. | Useful foundation. Needs broader state coverage or Storybook adoption. |

### 6.3 Journey findings

#### J1 - The journey is conceptually strong

The current sequence solves the most important product problem: it prevents the user from jumping
directly from input to optimizer output.

Impact: positive.

Recommendation: preserve this route order unless a current product contract changes.

#### J2 - `/diagnosis` is the best product benchmark route

The diagnosis route already composes through `DiagnosisSummaryPanel`, with product-facing pieces
such as `DiagnosisHero`, `EvidenceStrip`, `DiagnosticCanvas`, and `AdvancedDiagnostics`.

Impact: positive; this route should become the standard for the rest of the platform.

Recommendation: use `/diagnosis` as the first benchmark for future screen templates and component
contracts.

#### J3 - Downstream routes carry more page-local complexity

`/hypothesis`, `/comparison`, `/verdict`, and `/report` contain more local helper functions,
screen-local empty states, and route-specific orchestration. Some complexity is unavoidable because
these screens coordinate lineage and backend stage actions, but the UX surface could be simplified
through more shared product-state components and screen view models.

Impact: medium-to-high maintainability and consistency risk.

Recommendation: extract repeated state and route-hero patterns only after wireframes define the
desired screen hierarchy.

#### J4 - A non-current onboarding route may need classification

`frontend/app/onboarding/goals/page.tsx` exists, while active current docs route through
`/onboarding/investor-type` and `/onboarding/loading`. No active current-doc reference was found
that promotes `/onboarding/goals` into the canonical route chain.

Impact: low-to-medium documentation/code hygiene risk.

Recommendation: classify it later as active, legacy, hidden, or removable. Do not remove it as part
of this audit.

## 7. Information Architecture Audit

### 7.1 Desired IA pattern

For Portfolio MRI, the strongest IA pattern is:

```text
1. Product-facing verdict or diagnosis
2. Evidence summary
3. Main decision canvas
4. User action / next safe step
5. Secondary context
6. Advanced technical detail
7. Raw/provenance detail only when needed
```

This aligns with the current design-system contract:

- diagnosis must show hero, evidence strip, and primary diagnostic canvas before advanced metrics;
- `VerdictHero` should lead redesigned analytical routes;
- technical evidence should not dominate first-read surfaces.

### 7.2 Current IA strengths

- The docs strongly separate public landing, onboarding, and platform routes.
- The left journey rail establishes the product sequence.
- Platform headers are intended to be compact utility bars, not noisy dashboards.
- Diagnosis has a first-read hierarchy.
- Candidate/verdict/report wording boundaries are documented.
- Generated artifacts are not treated as frontend source.

### 7.3 Current IA gaps

| Gap | Evidence | Risk | Recommendation |
| --- | --- | --- | --- |
| No consolidated screen-job matrix in implementation planning form | Route responsibilities exist across design docs, but not as a working UX audit matrix. | Future redesign may optimize isolated pages instead of the journey. | Create a screen-job matrix before route refactors. |
| Hypothesis route has high conceptual density | It includes diagnosis, selected card, Builder controls, Client Fit context, alternatives, generation, lineage checks, and technical details. | User may not know what decision is being made. | Wireframe this route before any visual polish. |
| Comparison, Verdict, Report depend on many blocked/partial states | These states are product-valid but can feel broken if not clearly presented. | Users may interpret evidence-insufficient as product failure. | Create shared blocked/partial/evidence-insufficient state patterns. |
| Technical detail still has gravity | Many metrics and evidence details are available. | The UI may drift toward dashboard wall / analytics terminal. | Keep technical detail collapsed or secondary unless it directly supports the primary decision. |

## 8. Wireframe Recommendations

No wireframes were created in this audit. The recommended wireframe sequence is:

1. `/diagnosis` benchmark wireframe.
2. `/hypothesis` workstation wireframe.
3. `/comparison` trade-off evidence wireframe.
4. `/verdict` decision-support wireframe.
5. `/portfolio-input` validation and recovery wireframe.
6. Mobile variants for the above.

Each wireframe should answer:

- What does the user need to understand in the first 5 seconds?
- What is the one primary action?
- What evidence must be visible before the action?
- What can be collapsed?
- What state is shown when the review is locked, loading, failed, partial, stale, or read-only?
- Which words prevent advice-like interpretation?

## 9. Design System Audit

### 9.1 Current foundations

The design system has an explicit thesis:

```text
premium dark institutional investment decision room
```

Current foundations include:

- color token guidance in `DESIGN.md` and `docs/contracts/DESIGN_SYSTEM_CONTRACT.md`;
- dark graphite surfaces and restrained blue action accents;
- semantic use of amber, muted red, ivory/neutral, and blue;
- typography scale classes;
- motion rules that prefer calm explanatory transitions;
- strict separation between landing/onboarding and platform shell.

### 9.2 Token and foundation verdict

The token strategy is adequate for the current product stage. The bigger need is not a new palette;
it is stronger enforcement of design-system usage across page implementations.

Recommendation: avoid broad color/style redesign until components and states are standardized.

### 9.3 Component inventory

Current shared primitives in `frontend/components/ui/` include:

- `AdvancedDisclosure`
- `Button`
- `DecisionHeroCard`
- `EvidenceItem`
- `EvidenceSummary`
- `MetricCard`
- `MetricMatrix`
- `ScoreIndicator`
- `SectionHeader`
- `States`
- `StatusBadge`
- `Surface`
- `VerdictHero`
- shared motion helpers

Product component areas include:

- `landing`
- `onboarding`
- `portfolio`
- `diagnosis`
- `evidence`
- `client-fit`
- `hypothesis`
- `comparison`
- `verdict`
- `report`
- `workspace`
- `layout`

### 9.4 Component-system findings

#### C1 - Shared primitives exist and should be preserved

`Button`, `Surface`, `StatusBadge`, `EvidenceSummary`, `MetricMatrix`, `States`, and `VerdictHero`
are strong primitives for the current visual language.

Recommendation: future redesign should compose these before creating new route-local UI.

#### C2 - Repeated state patterns are not fully centralized

There is a shared `frontend/components/ui/States.tsx`, but several routes define local `EmptyState`
or locked/missing state shells. Some local states may be justified by route-specific copy, but the
visual and interaction pattern should be centralized.

Risk: inconsistent empty/error/locked/partial states across screens.

Recommendation: create a richer product-state component family:

```text
LockedState
PartialEvidenceState
ReadOnlyHistoryState
StaleLineageState
EvidenceInsufficientState
CandidateUnavailableState
GenerationFailedState
```

#### C3 - `VerdictHero` is doing valuable cross-screen work

Several analytical routes use `VerdictHero`. This is good because it creates a consistent first-read
pattern.

Risk: if too much route-specific data is packed into the hero facts, it can become a generic header
rather than a decision explanation.

Recommendation: document when to use facts, boundary notes, and actions inside `VerdictHero`.

#### C4 - The sandbox is useful but underpowered

`/sandbox/components` previews shared primitives and some diagnosis components. This is valuable and
should remain. However, it does not yet provide Storybook-level isolated coverage of all meaningful
component states.

Recommendation: either:

1. expand `/sandbox/components` into a structured state gallery first; or
2. install Storybook and create stories for primitives and key product components.

The low-risk path is to expand the sandbox first, then decide whether Storybook is worth the
additional dependency and maintenance cost.

## 10. Storybook / Isolated UI Workflow Assessment

`frontend/package.json` does not currently include Storybook scripts or dependencies.

Current status:

| Capability | Current state | Gap |
| --- | --- | --- |
| Component primitives | Present in `frontend/components/ui/`. | Need more state coverage. |
| Component gallery | Present at `/sandbox/components`. | Needs route-state matrix and more edge cases. |
| Stories | Not present. | No standardized isolated component variation files. |
| Visual regression | Not observed in package scripts. | Future need after component coverage matures. |
| A11y component checks | Not observed as isolated workflow. | Future need. |

Recommended isolated-state coverage:

```text
Button: primary, secondary, ghost, danger, disabled, long label, mobile width
StatusBadge: slate, blue, amber, red, neutral, long label
Surface: default, glass, raised, subtle, risk, warning
EvidenceSummary: 0, 1, 4, long text, amber/red/blue tones
MetricMatrix: normal, material rows, unavailable rows, mobile layout
VerdictHero: no facts, 3 facts, long interpretation, boundary note, actions
States: loading, empty, locked, error, partial, stale lineage, evidence insufficient
DiagnosisHero: normal, weak evidence, no candidate path
Hypothesis action console: blocked, ready, generating, failed, generated
Comparison: candidate missing, comparison running, metrics unavailable, valid comparison
Verdict: evidence insufficient, ready to generate, generated, failed candidate
Report: blocked, generating, preview created, warnings
```

## 11. Usability Heuristic Review

### H1 - Visibility of system status

Strengths:

- Staged diagnosis progress exists.
- Loading, error, locked, and evidence-limited states are represented.
- Journey flags gate downstream steps.

Risks:

- Too much backend/stage complexity can leak into user understanding if copy is not carefully managed.
- Evidence-insufficient states can be mistaken for failure.
- Stale lineage and read-only history are complex concepts for non-technical users.

Recommendations:

- Use product-facing state labels, not backend process labels.
- Create a standard state pattern for "not broken, just not enough evidence."
- Keep operator terms out of primary UI copy.

### H2 - Match between system and real world

Strengths:

- Product docs already require product-facing language and non-binding boundaries.
- Landing copy explains "diagnose before rebalance."

Risks:

- Terms such as lineage, candidate, Builder, evidence quality, and diagnostic hypothesis may still need plain-language validation.
- Financial users may interpret "candidate" as a recommendation unless repeatedly framed as a test.

Recommendations:

- Run a terminology pass with non-professional users.
- Prefer "test one alternative" or "diagnostic test" near candidate actions.
- Keep "not trade advice" boundaries close to generation, comparison, verdict, and report actions.

### H3 - User control and freedom

Strengths:

- Users can return to Portfolio Input and revisit earlier steps.
- Changing hypothesis or builder settings clears downstream readiness.

Risks:

- The consequence of changing a card/setup may not be obvious.
- Recovery by review ID is advanced and may confuse non-technical users.

Recommendations:

- Make reset consequences visible before destructive state changes.
- Separate normal user recovery from advanced/local recovery.

### H4 - Consistency and standards

Strengths:

- Shared journey rail and platform shell exist.
- Shared UI primitives exist.
- Design contracts are explicit.

Risks:

- Local state components and route-specific shells may drift.
- Some pages may evolve differently because they own complex backend orchestration.

Recommendations:

- Centralize recurring product states.
- Add sandbox/Storybook coverage before refactoring production routes.

### H5 - Error prevention

Strengths:

- Portfolio Input has validation requirements in docs.
- Candidate generation is blocked when prerequisites are missing.
- Same-run lineage checks protect downstream actions.

Risks:

- High-complexity forms such as Builder settings require especially clear infeasibility messaging.
- Users may not understand why a downstream step is locked.

Recommendations:

- Use inline prevention copy before errors happen.
- Show locked-state prerequisites in user language.

### H6 - Recognition rather than recall

Strengths:

- Journey rail keeps the route sequence visible.
- Evidence summaries repeat key facts.

Risks:

- Users may need to remember what was selected in Hypothesis when they reach Comparison/Verdict.
- Client Fit context may be forgotten downstream.

Recommendations:

- Carry a compact "active test context" strip from Hypothesis through Report.
- Show selected card, candidate id/name, and one-sentence purpose in Comparison, Verdict, and Report.

### H7 - Aesthetic and minimalist design

Strengths:

- The design contract explicitly avoids dashboard walls and terminal-like density.
- Diagnosis separates first-read evidence from advanced details.

Risks:

- Financial products naturally accumulate metrics, warnings, and caveats.
- Downstream screens can become dense because they need to explain lineage, evidence, and action state.

Recommendations:

- Keep the first viewport focused on meaning and next action.
- Collapse advanced technical content by default unless required for trust.

## 12. Route-by-Route UX Backlog

| Route | Priority | Recommended next action |
| --- | --- | --- |
| `/diagnosis` | P0 | Treat as benchmark route. Create wireframe and component-state checklist, then align implementation only if gaps remain. |
| `/hypothesis` | P0 | Create workstation IA wireframe before visual changes. Simplify the decision being made: choose one test, configure bounds, generate candidate. |
| `/comparison` | P1 | Standardize candidate/current context, unavailable metrics, stale comparison, and evidence-quality states. |
| `/verdict` | P1 | Standardize evidence-insufficient vs generated verdict presentation and keep decision-support boundary explicit. |
| `/portfolio-input` | P1 | Run task-based usability review for ticker selection, weight entry, sum-to-100 validation, and recovery. |
| `/report` | P1 | Clarify preview-only status and evidence-grounding trace without making the report feel like a final polished product. |
| `/client-fit` | P1 | Validate that users understand it as non-binding context, not approval. |
| `/evidence` | P2 | Ensure Stress Lab reads as evidence for diagnosis, not a separate advanced analytics destination. |
| `/workspace` | P2 | Improve first-time and returning-user empty states after route/state audit. |
| `/landing` | P2 | Validate public messaging with first-time users. |
| `/sandbox/components` | P0 | Expand into state gallery or replace with Storybook workflow. |

## 13. Recommended Redesign / Refactor Sequence

### Phase 0 - No-code UX foundation

Deliverables:

- UX brief.
- Screen-job matrix.
- Journey decision map.
- Route IA wireframes.
- Component/state inventory.

### Phase 1 - Component state system

Deliverables:

- Expanded `/sandbox/components` or Storybook setup.
- Shared product-state components.
- Component state matrix.
- No production route redesign yet.

### Phase 2 - Benchmark route

Recommended route: `/diagnosis`.

Deliverables:

- Confirm first-read hierarchy.
- Confirm evidence strip behavior.
- Confirm advanced detail collapse.
- Confirm mobile layout.
- Run browser visual QA.

### Phase 3 - High-complexity route hardening

Recommended route: `/hypothesis`.

Deliverables:

- Workstation wireframe.
- Simplified action console.
- Clear selected-test context.
- Builder state and infeasibility messaging.
- Candidate generation states.

### Phase 4 - Downstream consistency

Routes:

- `/comparison`
- `/verdict`
- `/report`

Deliverables:

- Shared active-test context.
- Shared stale/partial/evidence-insufficient states.
- Standard boundary notes.
- Consistent CTA hierarchy.

### Phase 5 - End-to-end UX QA

Deliverables:

- Fresh localhost visual QA.
- Mobile screenshots.
- One happy path.
- One locked/blocked path.
- One evidence-insufficient path.
- One stale-lineage or read-only-history path.
- Findings logged before implementation closure.

## 14. Suggested Future Artifacts

Recommended new documents or sections:

1. `docs/design/ux_product_brief.md`
   - Users, jobs, pains, decision moments, terminology, success criteria.

2. `docs/design/screen_job_matrix.md`
   - One job per route, primary user question, primary CTA, allowed secondary actions,
     locked/error states.

3. `docs/design/component_state_matrix.md`
   - Component state coverage and required sandbox/Storybook examples.

4. Future ExecPlan under `docs/exec_plans/`
   - Required before broad route refactor or Storybook adoption.

## 15. Acceptance Criteria for a Top-Tier Workflow

Portfolio MRI can be considered operating with a professional UX/UI workflow when:

- every route has one documented screen job;
- every key route has a wireframe before visual implementation;
- shared UI primitives cover normal, loading, empty, locked, partial, error, and long-text states;
- candidate, verdict, Client Fit, and report copy consistently avoids advice-like wording;
- component variants are reviewable in `/sandbox/components` or Storybook without running the full app flow;
- visual QA is performed on fresh localhost builds for every UI change;
- route-level decisions are tested against NN/g heuristics;
- at least a small task-based usability test is performed before major visual redesign;
- docs are updated with implementation changes, not after the fact.

## 16. Immediate Next-Step Recommendation

Start with a no-code design foundation task:

```text
Create UX brief + screen-job matrix + component-state matrix.
```

Then implement a controlled component-state foundation:

```text
Expand /sandbox/components or adopt Storybook.
```

Only after that should production routes be redesigned.

## 17. Open Questions

1. Who is the primary launch user: self-directed investor, advisor, analyst, or internal demo user?
2. Should "Candidate" remain the visible user-facing word, or should the UI prefer "Diagnostic test"?
3. Should `/sandbox/components` remain the official isolated UI workflow, or should Storybook be adopted?
4. Is `/onboarding/goals` intentionally retained as a hidden/legacy route?
5. Which route should define the first production benchmark after `/diagnosis`: `/hypothesis` or `/portfolio-input`?

## 18. Verification

Performed:

- Static inspection of current frontend route files.
- Static inspection of shared UI primitives.
- Static inspection of current design and product contracts.
- Static inspection of `frontend/package.json` for Storybook presence.

Not performed:

- Browser QA.
- Playwright QA.
- User testing.
- Runtime journey execution.
- Accessibility tooling.
- Visual regression testing.

This is acceptable for the requested no-code audit, but not sufficient for accepting future UI
implementation changes.
