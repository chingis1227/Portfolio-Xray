# Architecture

This document is part of the active project documentation after the documentation migration. It describes target direction and operating context, but it does not override `SPEC.md`, `RULES.md`, `OUTPUTS.md`, `DATA.md`, `TESTING.md`, `docs/specs/*.md`, formulas, stress scenario definitions, optimizer policy, generated-output contracts, or current code behavior. Current implementation claims must be verified against the canonical specs and code.

## 1. Architecture Status

Portfolio MRI currently has a Python, CLI/file-driven, site/API-first backend architecture. The
target product architecture is a diagnosis-first decision-support workflow.

This document uses four labels:

- **Current implementation:** supported by current specs/code and safe to describe as implemented
  only after verification.
- **Target architecture:** desired product architecture that may require future implementation.
- **Advanced / research:** useful capabilities that should not be the core MVP user journey.
- **Legacy / compatibility:** older or compatibility flows that remain operationally useful but are
  not the target product front door.

## 2. Current Runtime Architecture

Current runtime truth must be verified against `SPEC.md`, `OUTPUTS.md`, `DATA.md`, `TESTING.md`,
`docs/specs/*.md`, and code.

High-level current runtime:

```text
config / analysis_subject
-> validation and resolved assumptions
-> data loading, FX, risk-free, benchmark, return panels
-> current portfolio diagnostics / analysis_subject materialization
-> stress, factor, scenario, macro/regime diagnostics where enabled
-> candidate builders / candidate factory
-> candidate diagnostics and comparison
-> generated decision artifacts where implemented
-> JSON/cache default outputs and optional export/report artifacts
```

Current implementation characteristics:

- CLI and file driven.
- JSON/cache are the normal site/API-first contract.
- CSV/TXT/HTML/PNG/PDF/Markdown/CSS outputs are explicit export/report artifacts, not the default
  source of truth.
- `analysis_subject/` should be inspected before interpreting candidate or decision artifacts in
  portfolio-first review runs.
- Legacy policy optimization remains callable as compatibility infrastructure.
- Detailed module contracts live under `docs/specs/*.md`.

Current main entrypoints:

| Entrypoint | Current role | Architecture label |
| --- | --- | --- |
| `run_portfolio_review.py` | Portfolio-first review orchestration. | Current implementation |
| `run_candidate_factory.py` | Candidate factory orchestration and optional comparison. | Current implementation / may become advanced or research UX in target |
| `run_compare_variants.py` | Compare variants and write downstream decision artifacts. | Current implementation |
| `run_report.py` | Report and diagnostics pipeline. | Current implementation |
| `run_optimization.py` | Legacy policy optimization compatibility. | Legacy / compatibility |
| `run_view_after_optimization.py` | Approved post-optimization tilt view. | Legacy / specialized compatibility |

Do not rename, remove, or demote these operational entrypoints without a separate approved
migration plan.

## 3. Target Product Architecture

Target product architecture:

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

This target architecture changes the user-facing product shape, not automatically the existing
backend capabilities. Existing backend modules may be reused, wrapped, reclassified, or preserved as
advanced/legacy infrastructure.

## 4. Target Architecture Layers

### 4.1 Input Portfolio Layer

Target responsibility:

- Accept the current portfolio as the default MVP starting point.
- Keep first-screen input simple: tickers/instruments, current weights, investor currency.
- Resolve system defaults for benchmark, cash proxy, risk-free source, FX logic, market data
  provider, analysis windows, and quality thresholds.

Current implementation mapping:

- Likely maps to current config validation, `analysis_subject`, input assumptions, client profiles,
  and data setup modules.
- Requires code/spec verification before claiming exact current behavior.

Architecture boundary:

- This layer collects and resolves inputs.
- It does not generate candidate weights.
- It does not decide whether to rebalance.

### 4.2 Portfolio X-Ray Layer

Target responsibility:

- Diagnose current portfolio structure and hidden risk.
- Produce allocation, metrics, risk contribution, factor exposure, hidden risk, weakness map, and
  data-trust signals where supported.

Current implementation mapping:

- Maps to existing Portfolio X-Ray / diagnostics specs and generated artifacts where implemented.
- Exact sections, fields, thresholds, and statuses require verification against current specs/code.

Architecture boundary:

- Diagnostic layer only.
- Does not issue final investment verdict.

### 4.3 Stress Test Lab Layer

Target responsibility:

- Evaluate current portfolio behavior under historical and synthetic stress scenarios.
- Identify worst scenarios, loss contributors, helpful offsets, hedge gaps, and stress evidence
  quality.

Current implementation mapping:

- Maps to stress testing, scenario library, hedge gap, crisis replay, and factor diagnostics specs
  where implemented.

Architecture boundary:

- Reports vulnerability and evidence quality.
- Does not fabricate history when data is insufficient.
- Does not generate trades.

### 4.4 Problem Classification Layer

Target responsibility:

- Convert X-Ray and Stress Test Lab outputs into 2-3 user-understandable portfolio problems.
- Examples: high volatility, high drawdown, concentration, weak hedge behavior, poor
  diversification, current portfolio acceptable.

Current implementation mapping:

- Requires code/spec verification. Treat as target module until verified.

Architecture boundary:

- Translates evidence into improvement directions.
- Does not directly construct candidate weights.
- Does not guarantee that a candidate must be generated.

### 4.5 Candidate Launchpad Layer

Target responsibility:

- Show recommended improvement paths and quick benchmark tests.
- Let the user choose what hypothesis to test.

Current implementation mapping:

- Requires code/spec verification. Existing candidate factory may supply methods, but Launchpad is
  target UX/product orchestration unless implemented elsewhere.

Architecture boundary:

- Launchpad cards are not portfolios.
- They open or prefill the Alternatives Builder.

### 4.6 Portfolio Alternatives Builder Layer

Target responsibility:

- Generate one selected candidate from a goal, method, constraints, and parameters.
- Preserve candidate as a hypothesis with evidence and provenance.

Potential backend reuse:

- Equal Weight.
- Equal Weight by Asset Class.
- Risk Parity.
- Hierarchical Risk Parity.
- Minimum Variance.
- Minimum CVaR.
- Maximum Diversification.
- Robust Mean Variance.

Current implementation mapping:

- Existing candidate builders and factory are current capabilities, but on-demand user-triggered
  builder UX requires code/spec verification.

Architecture boundary:

- Builder creates candidate hypotheses.
- It should not be framed as automatically finding the perfect portfolio.
- Batch generation can remain advanced/research or backend automation.

### 4.7 Current vs Candidate Comparison Layer

Target responsibility:

- Compare current portfolio against one selected candidate first.
- If multiple candidates exist, compare only the generated shortlist.

Target evidence:

- Return/risk.
- Volatility.
- Drawdown.
- Stress loss.
- Risk concentration.
- Factor exposure changes.
- Hedge gap changes.
- Turnover and transaction-cost assumptions where available.
- Data/model confidence.

Current implementation mapping:

- Existing candidate comparison specs and artifacts likely provide reusable evidence, but the
  current-vs-selected-candidate product shape requires verification.

Architecture boundary:

- Evidence-first comparison.
- Scores support but do not replace trade-off explanation.

### 4.8 Decision Verdict Layer

Target responsibility:

- Decide whether action is justified under the assumptions and evidence.

Target verdicts:

- Keep current portfolio.
- Rebalance to selected candidate.
- Partial rebalance / minor adjustments.
- Candidate improves risk but cost/turnover is too high.
- Test another candidate.
- No material rebalance recommended.
- Evidence insufficient.

Current implementation mapping:

- Existing Selection Engine / No-Trade specs and generated artifacts may map to this layer.
- Do not rename current schemas or fields without a migration plan.

Architecture boundary:

- Verdict answers "should the user act?"
- It does not always pick a winner.
- It should disclose data/model limits.

### 4.9 AI Commentary Layer

Target responsibility:

- Explain deterministic JSON evidence and verdict in client-friendly language.

Architecture boundary:

- AI does not calculate metrics.
- AI does not set data-quality statuses.
- AI does not create unsupported investment evidence.
- AI should cite or derive from generated evidence.

Current implementation mapping:

- Requires code/spec verification for current availability, inputs, and outputs.

### 4.10 Monitoring / What Changed Layer

Target responsibility:

- Track changes after the verdict.
- Surface risk contributor changes, worst scenario changes, drift, new warnings, retest triggers,
  and assumption changes.

Current implementation mapping:

- Existing monitoring specs/artifacts may map to a light generated implementation.
- Full workspace monitoring remains target/advanced unless current specs say otherwise.

## 5. Current To Target Mapping

| Current / existing area | Target architecture role | Classification |
| --- | --- | --- |
| Config validation, `analysis_subject`, input assumptions | Input Portfolio Layer and system defaults | Preserve / Current |
| Portfolio X-Ray diagnostics | Portfolio X-Ray Layer | Preserve / Current where implemented |
| Stress, factor, scenario diagnostics | Stress Test Lab Layer | Preserve / Current where implemented |
| Candidate factory | Backend candidate capability; target UX should route through Launchpad/Builder | Preserve; Core backend or Advanced UX depending mode |
| Optimization engine / optimizer-backed candidates | Internal construction methods | Preserve / Advanced / Requires Review |
| Candidate comparison | Current-vs-candidate and shortlist comparison evidence | Preserve; target UX adaptation requires review |
| Selection Engine / No-Trade | Decision Verdict backend evidence | Preserve; rename/reframe requires review |
| Action Engine / Rebalancing Advisor | Light action summary or later action layer | Preserve / Advanced / Later |
| Monitoring / Decision Journal | Light monitoring/commentary or full later workflow | Preserve / Advanced depending scope |
| Macro regime diagnostics | Optional overlay, not core MVP dependency | Preserve / Advanced |
| Assumption Sensitivity, Pareto, Regret, Model Risk | Research/advanced evidence | Preserve / Advanced |
| Legacy policy optimizer | Compatibility infrastructure | Preserve / Legacy |
| PDF/report sidecars | Export/presentation | Preserve / Legacy/export, not source of truth |

## 6. Advanced / Later Product Backlog

These capabilities should remain available or documented when supported, but should not be required
for the core MVP user journey unless a canonical spec says otherwise. Do not describe them as
implemented unless verified in `SPEC.md`, `docs/specs/*.md`, or code.

- Macro Risk Dashboard / Macro Overlay.
- Strategy Backtest as a separate block.
- Scenario & Stress Evaluation for Candidates.
- Full multi-candidate ranking / advanced research comparison.
- Out-of-sample / walk-forward analysis.
- Full Crisis Replay UI.
- What Happens If? Simulator.
- Portfolio Health Score / Robustness Scorecard as primary product modules.
- Assumption Sensitivity / Assumption Testing Mode.
- Pareto Frontier / Dominance Check.
- Regret Analysis.
- Model Risk Diagnostics.
- Rebalancing Advisor / Action Plan as full modules.
- Advanced Monitoring / full portfolio health monitoring.
- Macro regime monitoring.
- Advanced breach engine.
- Multi-client monitoring workspace.
- Max Sharpe.
- Custom Constraints.
- Advisor Custom Candidate.
- Tax-aware optimization.
- Turnover-aware optimization objective.
- Tactical Tilt.
- Full custom constraints UI.
- Multi-client workspace / saved workspaces.
- White-label / API integration.
- Full PDF report design.
- Advanced Parameter Builder settings.
- Asset X-Ray / Asset Diagnostics.
- Client-Fit Check / questionnaire.
- Portfolio Archetype Classification is an optional later diagnostic layer that can classify the
  portfolio by behavior, such as Equity Growth Portfolio, Balanced 60/40-like, Credit Carry
  Portfolio, Duration-heavy Defensive, Inflation-sensitive, or Pseudo-diversified Portfolio. It
  should not be part of the core MVP flow until explicitly implemented and approved.

Architecture rule:

Advanced/later does not mean delete. It means keep separate from the core decision path.

## 7. Legacy / Compatibility Architecture

Legacy paths should be preserved unless a future approved plan removes them.

Legacy / compatibility includes:

- `run_optimization.py` policy optimization flow.
- `run_report.py` legacy report behavior where used outside portfolio-first review.
- Full legacy PDF/export suite.
- Existing generated output folders and sidecars.
- Historical policy/current comparison concepts where still supported.

Architecture rule:

Legacy does not mean incorrect. It means not the target product front door.

## 8. Target Data Flow

Target MVP data flow:

```text
Portfolio input
  -> input validation and system defaults
  -> market data / FX / benchmark / risk-free resolution
  -> return panels and quality checks
  -> current portfolio diagnostics
  -> stress and factor diagnostics
  -> problem classification
  -> selected candidate generation
  -> current-vs-candidate comparison
  -> decision verdict
  -> AI commentary grounded in evidence
  -> monitoring snapshot / what changed
```

Source-of-truth rule:

- Code and canonical specs own calculations.
- JSON artifacts own machine-readable run evidence.
- AI and PDF/report outputs explain evidence; they do not replace it.

## 9. Target Module Boundaries

### Calculation Modules

Own:

- returns
- metrics
- risk contribution
- factor exposures
- stress PnL
- candidate weights
- comparison evidence

Must not:

- write unsupported narrative conclusions
- hide degraded data quality
- silently fabricate missing history

### Product Orchestration Modules

Own:

- workflow state
- diagnosis-only state
- candidate launch actions
- candidate shortlist
- current-vs-candidate routing

Requires future implementation verification.

### Decision Modules

Own:

- verdict evidence
- no-trade reasoning
- confidence / evidence quality
- action/no-action classification

Must not:

- ignore model/data limitations
- always force a rebalance

### Commentary / Report Modules

Own:

- human-readable explanation
- advisor/client narrative
- report packaging

Must not:

- become the source of calculations
- contradict JSON/spec evidence

## 10. Requires Code/Spec Verification

Do not claim these as current implementation until verified:

- Problem Classification as a concrete module or artifact.
- Candidate Launchpad state and outputs.
- Portfolio Alternatives Builder as UI/service.
- User-triggered one-candidate generation as the default path.
- Diagnosis-only state as a formal run state.
- Current-vs-selected-candidate as the main implemented comparison mode.
- Decision Verdict replacing or aliasing Selection Engine contracts.
- AI Commentary inputs, grounding, and output contracts.
- Candidate shortlist schema.
- Any new CLI flags, JSON fields, output files, or folder layout.
- Any change to current command behavior.

## 11. Future Implementation Implications

Potential future architecture work, not part of this documentation draft:

- Introduce explicit workflow state: diagnosed/no candidate, one candidate, multiple-candidate
  shortlist.
- Add a Problem Classification service or artifact based on X-Ray and stress evidence.
- Add Candidate Launchpad routing from problems to reasonable paths to test.
- Wrap existing candidate builders in a Portfolio Alternatives Builder interface.
- Add current-vs-selected-candidate presentation layer.
- Map existing Selection Engine outputs to Decision Verdict language without breaking schemas.
- Add AI Commentary grounding rules and evidence references.
- Keep batch candidate factory as advanced/research/backend mode.
- Preserve legacy policy flow and generated outputs during migration.

Each item needs an ExecPlan or focused implementation plan before code changes.

## 12. Migration Strategy For Current `ARCHITECTURE.md`

When replacing the current `ARCHITECTURE.md`, use this order:

1. Preserve current runtime entrypoints and command descriptions.
2. Preserve current source-of-truth links.
3. Move target architecture into a clearly marked target section.
4. Move macro, robust research, full multi-candidate comparison, and advanced decision diagnostics
   into advanced/research unless current specs require core positioning.
5. Keep legacy policy flow as compatibility, not product front door.
6. Mark all unverified target modules as `Requires code/spec verification`.
7. Do not rename public files, generated fields, or CLI flags in architecture docs without an
   approved migration plan.

## 13. Non-Goals

This architecture draft does not:

- Change code.
- Change CLI behavior.
- Change output contracts.
- Change formulas.
- Change optimizer behavior.
- Delete legacy flows.
- Rename generated schemas.
- Claim target UX exists today.
