# DOCUMENTATION_MIGRATION_PLAN.md

This document is a migration plan only. It does not rewrite existing project documentation, change
source-of-truth ownership, change formulas, change code behavior, or change generated artifacts.

The goal is to map the current Markdown documentation to the updated Portfolio MRI product direction
from the provided DOCX concept drafts while preserving the current implementation contracts.

## 1. Executive Summary

- Portfolio MRI should be framed as a portfolio diagnostic and investment decision-support system,
  not as a black-box optimizer or a machine that always produces "best weights."
- The target product story moves from optimizer-first to diagnosis-first: current portfolio input,
  X-Ray, stress behavior, problem classification, candidate hypothesis, comparison, verdict, and
  monitoring.
- Candidate portfolios should be described as investment hypotheses generated from diagnosed
  problems, not as automatic recommendations or guaranteed improvements.
- The target MVP comparison mode should be current portfolio vs selected candidate; full
  multi-candidate research comparison remains useful but should be positioned as advanced or
  research-mode unless code/specs say otherwise.
- No-trade should be a first-class investment verdict, not a failure to recommend.
- AI commentary should be positioned as an explanation layer over deterministic calculations,
  rule-based statuses, and generated JSON evidence; it must not be described as the source of
  metrics, stress results, data-quality statuses, or investment truth.
- Existing implementation capabilities must not be deleted or demoted only because they are absent
  from the new DOCX files. Mark them as `Preserve`, `Advanced`, `Legacy`, or `Requires Review`.
- The documentation migration must keep a strict separation between current implementation,
  target architecture, advanced/later features, deprecated framing, and claims requiring code/spec
  verification.
- The safest rewrite path is to create `NEW_*` documents first, compare them with the existing
  source-of-truth files, and replace current files only after human review.

## 2. New Product Direction

### Source Inputs Used

This plan uses only these explicitly provided DOCX concept drafts:

- `D:\Рабочий стол\ДИАГНОСТИКА\ДИАГНОСТИКА 2\ВОПРОСЫ ПРОЕКТА.docx`
- `D:\Рабочий стол\ДИАГНОСТИКА\ДИАГНОСТИКА 2\ДИАГНОСТИКА 2.docx`
- `D:\Рабочий стол\ДИАГНОСТИКА\ДИАГНОСТИКА 2\ЦА ЦЕННОСТЬ ЦЕЛЬ ФИЛОСОФИЯ ПОДХОД ДИАГНОСТИКА 2 — копия.docx`

The DOCX files are product concept drafts and implementation notes. They do not override `SPEC.md`,
`RULES.md`, `OUTPUTS.md`, `DATA.md`, `TESTING.md`, detailed specs, formulas, stress scenario
definitions, optimizer policy, current code behavior, or generated-output contracts.

### Target Audience

- **Primary ICP:** independent investment advisors / financial advisors working with client
  portfolios around `$250k-$5m`, needing fast, professional, client-ready portfolio risk reviews
  before client meetings.
- **Secondary ICP:** sophisticated self-directed investors with meaningful portfolios, roughly
  `$100k-$1m+`, who already use broker analytics, Portfolio Visualizer, Excel, Koyfin, Python, or
  similar tools and want deeper institutional-style diagnostics.
- **Preserve / Requires Review:** family offices, wealth managers, and broader HNWI users remain
  valid in older docs. They should not be deleted automatically; review whether they are primary,
  secondary, or later commercial segments.

### Value Proposition

Portfolio MRI helps the user answer:

> What is really inside this portfolio, where is the true risk, where can it break, what alternative
> is reasonable to test, what trade-off would I accept, and should I rebalance or do nothing?

The product value is not "perfect weights." It is disciplined, transparent, defensible
decision-support.

### Core Client Pains

- The user sees tickers and weights but does not understand the real economic exposure.
- The portfolio may look diversified while risk is concentrated in equity beta, duration, credit,
  currency, liquidity, weak hedge behavior, or correlated assets.
- Analytics may exist, but the user still does not know what to do: keep, rebalance, test another
  hypothesis, or wait because evidence is insufficient.

### Product Philosophy

- Diagnosis before action.
- Current portfolio first.
- Hidden risk, factor exposure, risk contribution, stress behavior, and hedge gaps matter more than
  optimizer labels.
- Candidate portfolios are investment hypotheses.
- Guided, not prescriptive: the system supports a decision process but does not replace advisor or
  investor responsibility.
- No-trade is a valid verdict.
- AI explains calculations; it does not invent calculations.
- Decision-ready output matters more than exposing every metric directly in the main user view.

### Target MVP Workflow

```text
Input portfolio
-> Portfolio X-Ray
-> Stress Test Lab
-> Problem Classification
-> Candidate Launchpad
-> Portfolio Alternatives Builder
-> Current vs Candidate Comparison
-> Decision Verdict
-> AI Commentary
-> Monitoring / What Changed
```

### What The Product Is

- A portfolio diagnostics and decision-support workflow.
- A structured way to move from evidence to verdict.
- A tool for client-ready portfolio risk review and advisor/investor explanation.
- A system that can preserve deterministic calculations, JSON evidence, quality statuses, and
  current CLI/reporting capabilities while evolving the product UX.

### What The Product Is Not

- Not a black-box optimizer.
- Not a promise of the single best portfolio.
- Not an AI system that computes or decides without deterministic evidence.
- Not a UI that must expose every advanced research metric in the core MVP.
- Not a reason to delete working advanced, legacy, or backend capabilities just because they are not
  the main user-facing MVP narrative.

## 3. Document-by-Document Migration Matrix

Legend:

- **Fully rewrite:** replace most narrative in a future reviewed rewrite.
- **Partially rewrite:** preserve current contracts, update framing and separation.
- **Lightly update:** small wording/routing updates only.
- **Preserve:** keep mostly as-is.
- **Archive / Legacy:** retain for compatibility/history; do not delete without approval.

| Document | Current role | Migration action | Keep | Remove / reframe | Move to Advanced / Later / Legacy | Add from DOCX | Claims requiring code/spec verification | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `README.md` | Public project overview, commands, current scope, documentation map. | Partially rewrite after product and spec alignment. | Current commands, install/test instructions, JSON/site API default, generated-output warnings, current vs target/TBD separation. | Reframe optimizer-heavy title/positioning if approved; avoid implying automatic candidate generation is the target UX. | Legacy policy commands remain `Legacy`; full candidate menu remains `Advanced` or `Research` if not core UX. | Diagnosis-first positioning, current-vs-candidate MVP, no-trade verdict, AI commentary as explanation. | Any claim that on-demand candidate UX exists; any claim about UI/workspaces; any claim that Decision Verdict replaces current selection artifacts. | High |
| `BUSINESS_VISION.md` | Business narrative, audience, value proposition, use cases. | Fully rewrite first as `NEW_BUSINESS_VISION.md`. | Decision-support goal, clarity under uncertainty, advisors/HNWI/self-directed value, no-trade concept if already present. | Reframe "optimization terminal" and "best allocation" language. | Family office/wealth manager can be secondary/later unless approved as primary. | Primary ICP advisors, secondary ICP self-directed investors, top 3 pains, "not black-box optimizer." | Revenue model, exact ICP portfolio-size ranges, commercial claims. | Medium |
| `PRODUCT.md` | Product flow, UX behavior, feature inventory, non-goals. | Fully/partially rewrite as `NEW_PRODUCT.md` before replacing. | Diagnostic-first principle, assumptions visibility, no-trade support, report/export concepts. | Reframe 12+ blocks into a clearer MVP journey; do not make all advanced blocks core. | Macro Dashboard, full strategy backtest, multi-candidate research, assumption sensitivity, Pareto, regret, advanced optimizer cockpit as `Advanced / Later`. | Problem Classification, Candidate Launchpad, Alternatives Builder, current-vs-candidate comparison, Decision Verdict, AI Commentary. | Whether diagnosis-only state, user-triggered candidate generation, shortlist arena, or builder parameters exist in current code. | High |
| `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md` | Living non-binding product blueprint. | Do not edit first; create `NEW_DIAGNOSTIC_PRODUCT_CONCEPT.md` in a later session. | Non-binding status, product direction role, concept vocabulary, current/target warning. | Reframe old 24-block list so core MVP is not overloaded. | Keep rich modules as `Advanced / Later`, not deleted. | New target workflow, on-demand candidate philosophy, no-trade, AI as explanation layer. | Any current implementation statements copied from DOCX walkthroughs. | Medium |
| `ARCHITECTURE.md` | Current architecture map, entrypoints, module layers, target boundaries. | Partially rewrite after product docs. | Current CLI/file-driven architecture, site/API JSON default, `analysis_subject` flow, legacy compatibility boundaries, module dependencies. | Reframe target chain to match new MVP; avoid saying target UI exists. | Legacy policy flow remains `Legacy`; full optimizer/research suite can be `Advanced`. | Problem Classification, Candidate Launchpad, Alternatives Builder as target modules. | Whether these target modules exist as implemented services or only concepts. | High |
| `SPEC.md` | Compact technical source-of-truth and implementation contract. | Light/partial update only after architecture/product review. | Current implementation scope, detailed spec index, binding behavior rules, generated artifact contracts, current CLI behavior. | Do not convert vision into binding spec until implemented and verified. | Keep legacy policy compatibility, robust optimizers, decision artifacts according to current specs. | Add target/non-binding notes only if clearly marked as future direction. | All target workflow steps not already implemented; on-demand candidate flow; Decision Verdict naming. | High |
| `OUTPUTS.md` | Generated-output and artifact policy. | Light/partial update after spec alignment. | Generated vs source distinction, JSON-first/site API default, command matrix, `analysis_subject/` operator warning. | Reframe PDFs as exports, not algorithm source; avoid deleting legacy output info. | Full legacy PDF suite and presentation outputs remain explicit export/legacy. | Future current-vs-candidate output orientation; AI commentary as presentation/explanation layer. | Any new output file names, schemas, or folder contracts. | High |
| `WORKFLOW.md` | Practical development workflow and docs sync rules. | Light update. | Source-of-truth check, planning discipline, verification, docs sync, final response expectations. | Do not replace workflow with product vision. | Add documentation migration workflow as future guidance if needed. | Guardrail: product concept drafts do not override current specs. | Any new required migration process. | Medium |
| `DECISIONS.md` | Accepted decision log. | Preserve now; update only when decisions are approved. | Existing accepted/superseded decision structure. | Do not backfill product wishes as accepted decisions. | Later add decisions for positioning, candidate UX, Decision Verdict naming after approval. | Potential decisions: diagnosis-first, no-trade first-class, AI explanation boundary. | Whether these are already accepted decisions or only proposed. | Medium |
| `AGENTS.md` | Agent operating rules, commands, source-of-truth routing. | Light update last. | Russian chat rule, source-of-truth routing, generated-output policy, commands, no destructive edits, ExecPlan rules. | Do not overload with product narrative. | Legacy commands remain as compatibility instructions. | Add migration-specific routing only if recurring. | Whether command matrix changes after docs migration. | High |
| `DATA.md` | Data-layer map, sources, inputs, quality rules. | Preserve / light update. | Data quality warnings, source families, FX/risk-free/benchmark rules, no fabricated returns. | Do not let product copy weaken data-quality caveats. | Advanced data providers and assumptions remain `Requires Review` or `Advanced`. | Reinforce that AI does not create data or statuses. | IBKR/yfinance/fallback details, factor availability, current provider defaults. | Medium |
| `TESTING.md` | Verification framework and test matrix. | Preserve / light update. | "Verify the changed risk", offline smoke, CLI smoke, artifact checks, docs checks. | Do not remove checks because target UX is simpler. | Full workflow tests remain as current verification if code supports them. | Add future docs migration sanity checks if useful. | Any new tests for on-demand candidate flow or verdict UX. | Medium |
| `RULES.md` | High-level rule map and source-of-truth hierarchy. | Preserve / light update. | Rule discipline, source-of-truth map, diagnostics non-binding boundary, generated-output rule. | Do not replace with product philosophy. | Add target concept routing only after docs are created. | Explicitly mark DOCX/NEW_* product drafts as non-binding until promoted. | Whether new docs become source-of-truth. | High |
| `DESIGN.md` | Visual design guidance. | Preserve / Requires Review. | Existing UI/design tokens and visual guidance. | Do not force core MVP product rewrite into visual spec prematurely. | Advanced UI/report design remains later unless approved. | Later: client-ready report and core-vs-advanced view hierarchy. | Whether UI implementation exists or uses this design. | Low |
| `GLOSSARY.md` | Shared terminology. | Light/partial update after product docs. | Current terms and links to canonical specs. | Avoid renaming terms without compatibility aliases. | Old names can become aliases: Selection Engine -> Decision Verdict language if approved. | Terms: Problem Classification, Candidate Launchpad, Portfolio Alternatives Builder, Decision Verdict, AI Commentary. | Whether terms are current implementation or target vocabulary. | Medium |
| `KNOWN_ISSUES.md` | Active issues and technical debt. | Preserve / update only with concrete issues. | Current known issues, model limitations, testing gaps. | Do not use as product wishlist. | Add migration risks only if they become active debt. | Potential issue: docs may overstate target vs current. | Any claim that issue exists in code. | Low |
| `CHANGELOG.md` | Concise completed-change history. | Preserve; update only after actual doc changes. | Existing history format. | Do not log future planned rewrites as completed. | N/A | Later add entry for migration plan and rewrites if performed. | Whether change has actually happened. | Low |
| `docs/ROADMAP.md` | Durable roadmap/backlog and historical phase map. | Preserve / partial update after plan approval. | Historical phase status, active/closed plans, audit mapping. | Do not erase past phases because product framing changed. | Reclassify future work into MVP/Advanced/Legacy only after review. | Add documentation migration sequence if accepted as roadmap work. | Whether on-demand candidate migration is planned, active, or completed. | Medium |
| `docs/operational_runbook.md` | Operator runbook for current CLI workflows. | Preserve / light update after command changes only. | Current command behavior, `analysis_subject/` warning, stale export warning, core/full profile details. | Do not rewrite as target UX. | Legacy flow stays as compatibility. | Add target warnings only if operators need them. | Any command semantics from DOCX walkthroughs. | High |
| `docs/optimization_run_checks.md` | Legacy/full optimization troubleshooting. | Preserve as legacy implementation support. | Failure points, network notes, parameter conflicts, pre-run checks. | Do not remove because optimizer is no longer product front door. | Mark as `Legacy / Advanced operational support` if needed. | Clarify optimizer is internal/legacy support, not product identity. | Whether run_optimization behavior remains unchanged. | Medium |
| `docs/specs/*.md` | Detailed implementation/spec contracts. | Grouped: preserve; update only owning specs when behavior changes. | All current formulas, schemas, statuses, constraints, output contracts, module ownership. | Do not rewrite specs from concept drafts alone. | Advanced specs can remain advanced but should not be deleted. Legacy specs remain compatibility docs. | Only add new target concepts after code/spec approval. | Any target feature not implemented. | High |
| `docs/exec_plans/*.md` | Historical and active implementation plans. | Preserve as project memory. | Progress, decisions, surprises, outcomes, session history. | Do not rewrite history. | Completed/historical plans remain historical. | Future migration plan can be registered if project process requires it. | Active-plan pointer if changed. | Medium |
| `docs/audits/*.md` | Audit evidence and audit-to-plan links. | Preserve as evidence. | Audit findings, methodology maps, timing audits, closure reports. | Do not reinterpret audits as product promises. | Historical audits remain historical. | Future documentation audit can be added later. | Any audit conclusions being current after later changes. | Medium |
| `pdf_md_sources/*.md` | Generated Markdown sidecars for PDF/report outputs. | Do not migrate as source docs. | Preserve as generated evidence unless task targets outputs. | Do not treat as source-of-truth. | Generated / export-only. | None. | Whether generated files are fresh. | Low |

## 4. Current vs Target Separation

### Current Implementation

Current implementation should be described only where supported by current source-of-truth docs and
code. From the existing Markdown inventory, current implementation includes a report-first,
CLI/file-driven and site/API-first JSON workflow with:

- `run_portfolio_review.py` as the portfolio-first review entrypoint.
- `analysis_subject` materialization and diagnostics before candidate interpretation.
- Portfolio X-Ray, stress/factor/macro/scenario diagnostics, candidate generation, comparison, and
  V1 decision artifacts as generated files where implemented.
- JSON/cache default output behavior, with CSV/TXT/HTML/PNG/PDF/Markdown presentation artifacts as
  explicit exports.
- Legacy policy optimization compatibility through `run_optimization.py` and `run_report.py`.
- Detailed spec ownership under `docs/specs/*.md`.

Any more specific implementation claim must be checked against the owning spec and code before being
stated as current.

### Target Architecture

The target architecture from the DOCX concept drafts is:

```text
Input portfolio
-> Portfolio X-Ray
-> Stress Test Lab
-> Problem Classification
-> Candidate Launchpad
-> Portfolio Alternatives Builder
-> Current vs Candidate Comparison
-> Decision Verdict
-> AI Commentary
-> Monitoring / What Changed
```

This is product direction unless and until promoted to canonical specs and implemented.

### Deprecated Or Demoted Concepts

These should not be presented as the core product story:

- Optimizer-first positioning.
- "Best portfolio" or always-pick-a-winner framing.
- Full automatic generation of many candidates as the default user experience.
- Macro Risk Dashboard as a core MVP dependency.
- Score-first user experience where Health Score or Robustness Score is the main answer.
- AI as a calculation or decision source.

Demotion does not mean deletion. Existing working capabilities should be preserved unless a future
approved plan removes them.

### Advanced / Later Features

These may remain valuable but should not be forced into the core MVP narrative:

- Full multi-candidate research arena.
- Full strategy backtest as a separate product block.
- Full candidate stress evaluation and advanced research comparison.
- Macro overlay / macro regime dashboard as a user-facing core block.
- Assumption sensitivity, Pareto/dominance, regret analysis, model risk diagnostics.
- Advanced optimizer cockpit, custom constraints, tax-aware optimization, turnover-aware objective,
  tactical tilt, advisor custom candidate.
- Full PDF report design, white-label workspace, API integrations, saved multi-client workspaces.
- Advanced asset-level diagnostics and client-fit questionnaire unless separately specified.

### Requires Code/Spec Verification

Do not state these as implemented without checking code and specs:

- User-triggered candidate generation as the current default UX.
- Diagnosis-only state in the current product contract.
- Problem Classification as an implemented module.
- Candidate Launchpad and Portfolio Alternatives Builder as implemented UI/service layers.
- Current-vs-candidate as the only or main implemented comparison mode.
- Decision Verdict replacing Selection Engine in generated contracts.
- AI Commentary implementation details.
- Any new JSON schema, CLI flag, folder structure, report section, or status name.

## 5. Concepts To Preserve

Do not delete these during migration:

- Source-of-truth hierarchy: `RULES.md`, `SPEC.md`, `OUTPUTS.md`, `DATA.md`, `TESTING.md`,
  `docs/specs/*.md`.
- Verification loop: narrow checks first, broaden based on risk, report unverified areas.
- Generated vs source distinction.
- JSON contracts and `output_manifest.json` orientation.
- `analysis_subject/` operator rule before interpreting candidate or decision artifacts.
- Current CLI commands and compatibility commands.
- Legacy policy flow as compatibility infrastructure.
- Data quality warnings, insufficient-data handling, data trust signals, and no-fabricated-history
  rules.
- Optimizer readiness and quality disclosure.
- Current candidate factory profiles and full/core menu distinctions where implemented.
- Detailed specs for metrics, stress, factor, macro, robust optimization, selection, action,
  monitoring, and journal artifacts.
- AGENTS operating rules, including communication style, editing discipline, generated-output
  policy, and no destructive changes.
- Audit and ExecPlan history as traceability, not product clutter.

## 6. Concepts To Remove, Demote, Or Reframe

- **Optimizer-first framing** -> reframe as diagnostics and decision support; optimizers are internal
  candidate construction methods.
- **Automatic full candidate batch as core UX** -> reframe as current implementation capability or
  advanced/research mode; target MVP is user-triggered candidate hypotheses.
- **Selection Engine always chooses the best portfolio** -> reframe as Decision Verdict that may
  choose keep, rebalance, test another candidate, no-trade, or evidence insufficient.
- **Macro Risk Dashboard as core MVP** -> demote to optional/advanced diagnostic overlay unless a
  canonical spec says otherwise.
- **Portfolio Health Score or Robustness Score as main output** -> reframe as supporting evidence;
  final product answer is a verdict with rationale.
- **Advanced optimizer cockpit UX** -> move to advanced/later.
- **Too many metrics in the main view** -> separate core decision view from advanced/drill-down
  evidence and appendix.
- **AI as decision-maker** -> reframe as explanation and report-writing layer over deterministic
  JSON evidence.
- **PDF as algorithm source** -> reframe as export/presentation; JSON/spec/code remain truth.

## 7. Recommended Rewrite Order

Recommended order:

1. `BUSINESS_VISION.md`
2. `PRODUCT.md`
3. `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`
4. `ARCHITECTURE.md`
5. `SPEC.md`
6. `README.md`
7. `OUTPUTS.md`
8. `WORKFLOW.md`
9. `DECISIONS.md`
10. `AGENTS.md`

Why this is safest:

- Start with business and product documents because they can absorb the new positioning without
  immediately changing current technical contracts.
- Update diagnostic concept next because it is already explicitly non-binding and can hold target
  architecture safely.
- Update architecture only after the product language is stable, so current/target/legacy boundaries
  are clear.
- Update `SPEC.md` only after target concepts are separated from implemented behavior; `SPEC.md` is
  a current implementation contract and must not become a product wish list.
- Update `README.md` after the key documents agree, because it is a public entrypoint and should not
  overstate target behavior.
- Update `OUTPUTS.md`, `WORKFLOW.md`, `DECISIONS.md`, and `AGENTS.md` last because these documents
  govern operator safety, process, decisions, and agent behavior.

## 8. Safe Replacement Strategy

Preferred strategy:

1. Create `NEW_*` versions first:
   - `NEW_BUSINESS_VISION.md`
   - `NEW_PRODUCT.md`
   - `NEW_DIAGNOSTIC_PRODUCT_CONCEPT.md`
   - optionally `NEW_ARCHITECTURE.md` if the architecture rewrite is large
2. Compare each `NEW_*` file with its existing counterpart.
3. Check every current-implementation claim against `SPEC.md`, `OUTPUTS.md`, `DATA.md`,
   `TESTING.md`, `docs/specs/*.md`, and code where needed.
4. Replace current files only after human approval.
5. Archive old versions as `LEGACY_*` only if explicitly approved.
6. Do not archive or rewrite generated files unless the task explicitly targets generated outputs.
7. Keep aliases and compatibility notes for old terms where renaming would confuse operators or
   break existing docs.

Do not update current source-of-truth files directly as the first step, except for small corrections
that are explicitly reviewed and requested.

## 9. Code Migration Implications

Do not write or modify code as part of this documentation migration plan. Likely future code
migration areas implied by the new product direction:

- Move from automatic batch candidate generation as the core UX to user-triggered candidate
  generation, while preserving batch/full research mode where useful.
- Make a diagnosis-only state explicit: portfolio diagnosed, no candidate generated yet, suggested
  paths available.
- Add or formalize Problem Classification between X-Ray/stress and candidate generation.
- Add or formalize Candidate Launchpad and Portfolio Alternatives Builder concepts.
- Make current-vs-candidate comparison the primary MVP comparison path.
- Make no-trade verdict a first-class generated outcome.
- Separate core-view metrics from advanced/drill-down metrics.
- Preserve legacy outputs and existing JSON contracts where needed for compatibility.
- Keep advanced optimizers and research diagnostics available as advanced/internal capabilities.
- Maintain deterministic code as the source of metrics, statuses, stress results, candidate
  freshness, and data-quality labels.
- Use AI only for explanation, narrative, and client-friendly commentary unless a future canonical
  spec explicitly expands its role.

Each item requires an ExecPlan or specific implementation plan before code changes.

## 10. Risks And Guardrails

| Risk | Guardrail |
| --- | --- |
| Claiming target behavior as current implementation. | Mark target behavior as `Target` or `Requires code/spec verification` until verified against specs and code. |
| Deleting important implementation capability because it is absent from DOCX. | Classify missing capabilities as `Preserve`, `Advanced`, `Legacy`, or `Requires Review`; do not delete by default. |
| Breaking source-of-truth hierarchy. | Keep `SPEC.md`, `RULES.md`, `OUTPUTS.md`, `DATA.md`, `TESTING.md`, and `docs/specs/*.md` authoritative for current behavior. |
| Mixing product vision into technical SPEC. | Use product docs for target direction; promote into specs only after approval and implementation plan. |
| Confusing deprecated with advanced/later. | Deprecated means harmful framing; advanced/later means useful capability outside core MVP. |
| Replacing Selection Engine terminology without preserving contracts. | Add aliases and migration notes; do not rename generated fields or schemas without a breaking-change plan. |
| Over-simplifying docs and losing operator warnings. | Preserve current CLI commands, output warnings, stale export warnings, and `analysis_subject/` interpretation rules. |
| Turning AI into an investment decision-maker in docs. | State that AI commentary explains deterministic outputs and must not invent metrics, statuses, or verdict evidence. |
| Making PDF/report output sound like the algorithm. | Keep JSON/spec/code as source-of-truth; PDFs and Markdown report sources are export/presentation artifacts. |
| Introducing new product modules without implementation evidence. | Mark Problem Classification, Launchpad, Alternatives Builder, and Decision Verdict as target unless verified. |

## 11. Session-by-Session Migration Roadmap

### Session 1 — Approve Migration Plan

- Review this `DOCUMENTATION_MIGRATION_PLAN.md`.
- Confirm target document list, rewrite order, and current-vs-target guardrails.
- Decide whether to register this migration as an ExecPlan under `docs/exec_plans/`.
- No existing docs should be rewritten in this session.

### Session 2 — Draft `NEW_BUSINESS_VISION.md`

- Create a new business vision draft without replacing `BUSINESS_VISION.md`.
- Center the primary ICP on independent advisors / financial advisors.
- Keep secondary ICP as sophisticated self-directed investors.
- Preserve broader segments as secondary/later where useful.
- Emphasize pains, value proposition, no-trade, decision-support, and not-black-box-optimizer
  positioning.

### Session 3 — Draft `NEW_PRODUCT.md`

- Create a new product draft without replacing `PRODUCT.md`.
- Define the target MVP journey:
  `Input -> X-Ray -> Stress -> Problem Classification -> Candidate Launchpad -> Builder -> Current vs Candidate -> Verdict -> AI Commentary -> Monitoring`.
- Separate core MVP, advanced/research, legacy, and requires-verification features.
- Avoid claiming user-triggered candidate generation exists until verified.

### Session 4 — Create `NEW_DIAGNOSTIC_PRODUCT_CONCEPT.md`

- Create `NEW_DIAGNOSTIC_PRODUCT_CONCEPT.md`.
- Do not edit the current `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md` in this session.
- Use it as a clean target concept document with clear non-binding status.
- Keep advanced/later modules in a separate section instead of deleting them.

### Session 5 — Draft Target Architecture Separation

- Create a target architecture draft or reviewed patch plan for `ARCHITECTURE.md`.
- Separate current runtime, target product modules, advanced/research modules, and legacy
  compatibility.
- Identify which target modules require code/spec verification.

### Session 6 — Reconcile `SPEC.md` Current vs Target Claims

- Review `SPEC.md` against the new product drafts.
- Keep `SPEC.md` focused on implemented behavior and canonical spec index.
- Add only carefully worded target notes if needed.
- Do not promote target behavior into binding contract without implementation proof.

### Session 7 — Update README / OUTPUTS / WORKFLOW Docs

- Update `README.md` only after product/spec boundaries are clear.
- Update `OUTPUTS.md` only for artifact policy wording, not new schemas unless implemented.
- Update `WORKFLOW.md` to reinforce product concept vs source-of-truth routing if needed.

### Session 8 — Update DECISIONS / AGENTS / GLOSSARY As Needed

- Add `DECISIONS.md` entries only for approved decisions, not draft concepts.
- Update `GLOSSARY.md` with new terms and aliases if approved.
- Update `AGENTS.md` only if agent routing or operating instructions change.

### Session 9 — Link Check And Stale Reference Audit

- Check Markdown links and stale references.
- Verify old terms are either preserved as aliases or intentionally reframed.
- Confirm generated outputs are not treated as source docs.
- Confirm current implementation claims are backed by specs/code or marked `Requires code/spec
  verification`.

## Verification Checklist For This Plan File

- This file is documentation-only.
- No code tests are required for creating this plan.
- The only intended new file is `DOCUMENTATION_MIGRATION_PLAN.md`.
- Check `git diff` / `git status` and confirm this task did not modify existing project files.
- Confirm `pdf_md_sources/*.md` is treated as generated output, not source documentation.
