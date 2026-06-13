# Canonical Product Truth Reset Audit

> **Status note (2026-05-27):** Historical snapshot. Findings that said default
> `run_portfolio_review.py` runs a batch candidate factory were valid at audit time but are now stale
> for current runtime. Current default behavior is diagnosis-only unless candidates are explicitly
> requested. See `docs/specs/portfolio_review_workflow_spec.md` and
> `docs/exec_plans/final_architecture_consistency_audit_plan.md` for the updated architecture baseline.

Date: 2026-05-26  
Repository: Portfolio MRI / Portfolio X-Ray  
Branch observed: `change-the-project`  
Audit mode: evidence-only; no code or existing documentation was modified.

## 1. Executive Summary

The project is **partially aligned** with the canonical current product, “Diagnosis 2”, but it is **not yet cleanly reset** around that product truth.

The desired canonical product is:

```text
Input portfolio
-> Portfolio X-Ray
-> Stress Test Lab
-> Problem Classification
-> Candidate Launchpad
-> Portfolio Alternatives Builder
-> Current vs Candidate Comparison
-> Decision Verdict
-> AI Commentary / grounding
-> Monitoring / What Changed
```

The repository still carries a large amount of older optimizer/report/scorecard-heavy architecture in active docs and default runtime wiring. Some of that old capability is useful and implemented, but it is still too visible as “current implementation” and too tightly wired into comparison output generation.

### Where the old project still leaks

1. **`AGENTS.md` still opens the project summary with V1 decision artifacts**: candidate comparison, robustness scorecard, Portfolio Health Score, Selection/No-Trade, Action Plan, Monitoring, and Decision Journal. It says these are not necessarily Core MVP UI, but their prominence causes the next agent to understand the project through the old scorecard/report bundle first.
2. **`SPEC.md` current-implementation matrix lists Health Score, Robustness Scorecard, Selection Engine, Action Engine, Monitoring, and Decision Journal as implemented runtime capabilities** without making the canonical product hierarchy dominant enough.
3. **`src/candidate_comparison.py::write_candidate_comparison_outputs()` always writes the old downstream package** after comparison: robustness scorecard, portfolio health score, selection, tradeoff/model risk, assumption sensitivity, Pareto, regret, current-vs-policy, action plan, monitoring, and decision journal. This is the largest runtime contradiction.
4. **Default portfolio review still runs a batch candidate factory**. `run_portfolio_review.py` defaults to `--mode core`, which maps to `core_fast`; `core_fast` uses six candidates, not one selected hypothesis. This is better than the full 16-candidate old menu, but it is still batch-first rather than selected-candidate-first.
5. **`candidate_comparison.json` still treats `default_v1` as `PRODUCT_MENU_PROFILE_ID`** in `src/candidate_comparison.py`. That embeds the old full-menu comparison concept as “product menu”, even though the canonical product should be current-vs-selected-candidate.

### Biggest source of confusion

The biggest source of confusion is the word **“implemented”** being used without product classification.

Many features from “Diagnosis 2 Later” are implemented as backend/generated artifacts, but the canonical product meaning is: they are **not current Core MVP product flow**. The repo often says they are implemented, then later says they are advanced or not UI. That is accurate at the engineering level but confusing at the product-truth level.

### What must be fixed first

First fix should be a **documentation truth reset for agent entrypoints and product-defining docs**:

1. `AGENTS.md`
2. `README.md`
3. `SPEC.md`
4. `OUTPUTS.md`
5. `PRODUCT.md`
6. `ARCHITECTURE.md`
7. `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`

The first message any future agent sees must say: current product = “Diagnosis 2”; Health Score / Robustness / Action / Journal / macro / full candidate arena are advanced/backend/backlog unless explicitly promoted.

Second fix should be a **runtime cleanup plan**: make default review produce the six-file product bundle as the main path and hide/filter advanced downstream artifacts from current product flow.

## 2. Canonical Product Definition

### Current canonical product: “Diagnosis 2”

“Diagnosis 2” is the current product truth. It is diagnosis-first, current-portfolio-first, decision-support oriented, and not optimizer-first.

Canonical current flow:

```text
Input portfolio
-> Portfolio X-Ray
-> Stress Test Lab
-> Problem Classification
-> Candidate Launchpad
-> Portfolio Alternatives Builder
-> Current vs Candidate Comparison
-> Decision Verdict
-> AI Commentary / grounding
-> Monitoring / What Changed
```

The core user question is:

> What is really inside the current portfolio, where is risk concentrated, what problem exists, what candidate hypothesis is worth testing, and is any action justified...

### “Diagnosis 2 Later”

“Diagnosis 2 Later” is not the current Core MVP. It is backlog / advanced / later.

Features in that document must not be presented as current Core MVP even if code exists. If code exists, classify it as one of:

- legacy;
- advanced;
- backend evidence;
- technical artifact;
- future/backlog;
- generated support artifact.

### Product classification terms

| Term | Meaning for this project |
|---|---|
| Current Core MVP | The “Diagnosis 2” path and its product-facing bundle. Should be what agents and users understand as the project. |
| Advanced/backend evidence | Useful generated evidence or diagnostics that may support product outputs but must not lead the product story. |
| Legacy | Older optimizer/report/policy behavior preserved for compatibility or research, not the current product. |
| Future backlog | Desired later features from “Diagnosis 2 Later”. |
| Generated artifact | Output produced by runtime. It is not source-of-truth documentation and may be stale unless regenerated. |

## 3. Documentation Truth Audit

| File path | Presents “Diagnosis 2” as current... | Old/advanced leakage as current/core... | Risk | Recommended action |
|---|---:|---:|---|---|
| `AGENTS.md` | Partially | Yes, high prominence of V1 score/action/journal bundle | Critical | Rewrite project summary around canonical “Diagnosis 2”; move Health/Robustness/Action/Journal to advanced/backend/support note. |
| `README.md` | Partially | Yes, “Implemented today” lists V1 decision artifacts before product distinction | High | Reorder around canonical flow and six-file product bundle; demote scorecards/action/journal to advanced/generated evidence. |
| `SPEC.md` | Partially | Yes, current implementation matrix gives old artifacts equal weight | High | Add canonical product truth section first; classify implemented capabilities by product role, not just existence. |
| `OUTPUTS.md` | Mostly | Some | Medium | It already classifies bundles well; strengthen “Core product surfaces must ignore advanced artifacts by default.” |
| `PRODUCT.md` | Mostly | Some | Medium | Keep “Later” features clearly future/advanced; remove any “primary module” wording for scorecards/action/journal. |
| `ARCHITECTURE.md` | Mostly | Some | Medium | Make canonical flow the top architecture; put old pipeline under compatibility/backend. |
| `BUSINESS_VISION.md` | Mostly | Some | Medium | Ensure no old product modules are described as current product modules. |
| `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md` | Mostly | Some contradictory remnants | Medium | Treat as canonical concept only if it matches “Diagnosis 2”; move later list to backlog section. |
| `RULES.md` | Not deeply contradicted in search | Low | Low | Add brief routing rule: product truth = “Diagnosis 2”. |
| `WORKFLOW.md` | Partially | Possible because workflow still discusses old generated artifacts | Medium | Make workflow distinguish product changes vs advanced/generated support changes. |
| `GLOSSARY.md` | Partially | Yes, V1 generated decision-support bundle definition can anchor agents in old frame | Medium | Reclassify generated decision-support bundle as advanced/backend support, not core product. |
| `DATA.md` | Not primary source of leakage | Low | Low | No first-pass change unless data assumptions mention macro/client-fit as core. |
| `TESTING.md` | Partially | It tests old downstream package as part of comparison path | Medium | Split tests into Core Product Bundle vs Advanced Downstream Package. |
| `KNOWN_ISSUES.md` | Historical issue tracking | Low | Low | Add issue for canonical truth reset and runtime product filtering. |
| `docs/specs/*.md` | Mixed | Yes, many specs are valid but advanced; some specs still appear first-class | High | Add product-classification headers to specs: core/current, advanced/backend, legacy, future. |
| `docs/audits/*.md` | Historical mixed | Yes if read as current | Low/Medium | Keep as historical; active registers should point to this reset audit. |
| `docs/exec_plans/*.md` | Historical mixed | Yes if read as current | Low/Medium | Keep as historical; new remediation ExecPlan should supersede product-truth decisions. |
| `docs/ROADMAP.md` | Partially | Done items for old artifacts can imply product endorsement | Medium | Add column/category: Core MVP vs Advanced/backend vs Legacy/backlog. |
| `docs/archive/*` | Legacy reference | Acceptable | Low | Keep archive as legacy only; never use archived docs as current truth. |

### Exact old-current leakage examples

#### `AGENTS.md`

Evidence: `AGENTS.md` says the current implementation includes V1 decision artifacts: candidate comparison, robustness scorecard, Portfolio Health Score, Selection/No-Trade decision, Action Plan, Monitoring / What Changed, and generated Decision Journal.

Assessment: technically true, but dangerous as first-contact agent instruction. It makes the old generated decision package feel like the project identity.

Recommended action: rewrite to:

- canonical current project = “Diagnosis 2”;
- current product flow = Input -> X-Ray -> Stress -> Problem -> Launchpad -> Builder -> Current vs Candidate -> Verdict -> AI grounding -> What Changed;
- old V1 artifacts exist only as advanced/backend/generated support unless explicitly requested.

#### `README.md`

Evidence: `README.md` lists canonical candidate comparison and V1 decision artifacts under “Implemented today”, then separately lists diagnosis-first artifacts.

Assessment: good distinction exists, but ordering and wording still let old artifacts dominate.

Recommended action: make the product bundle the top “Implemented today” section; move the V1 decision package to “Advanced/backend generated support already present”.

#### `SPEC.md`

Evidence: `SPEC.md` lists robustness scorecard, Portfolio Health Score, Selection/No-Trade, trade-off/model-risk, Assumption Sensitivity, Action Plan, Monitoring, Decision Journal as current implementation artifacts and marks many of them implemented.

Assessment: engineering status is documented, but product status is not forceful enough. It should not tell the next agent “this is the project” before saying “these are advanced/backend/support”.

Recommended action: split status table into:

1. Current Core Product Flow;
2. Core support / technical contracts;
3. Advanced/backend generated evidence;
4. Legacy compatibility;
5. Future backlog.

#### `OUTPUTS.md`

Evidence: `OUTPUTS.md` correctly defines:

- Core MVP product bundle: `problem_classification.json`, `candidate_launchpad.json`, `current_vs_candidate.json`, `decision_verdict.json`, `ai_commentary_context.json`, `what_changed_summary.json`;
- Advanced / research evidence: `portfolio_health_score.json`, `robustness_scorecard.json`, `assumption_sensitivity.json`, `pareto_dominance.json`, `regret_analysis.json`, `tradeoff_explanation.json`, `model_risk_diagnostics.json`;
- Action / monitoring / journal evidence: `action_plan.json`, `monitoring_diff.json`, `decision_journal.json`, `decision_package_summary.json`.

Assessment: `OUTPUTS.md` is the closest to correct product truth. It should become the model for other docs.

Recommended action: strengthen by saying these advanced outputs may be generated in default code today but must not be product-facing unless advanced mode is requested.

## 4. Code Behavior Audit

### `run_portfolio_review.py`

What it does:

- default mode is core;
- if no explicit `--candidates`, mode core maps to factory profile `core_fast`;
- help text says full mode uses entire `default_v1` menu including optimizers and robust suite;
- supports `--candidates ID,ID,...` for explicit candidate selection;
- supports `--skip-candidates`.

Alignment:

- Partially aligned: it materializes `analysis_subject` first and avoids legacy policy optimization by default.
- Old behavior: default still runs a batch candidate factory (`core_fast`, six candidates) rather than a diagnostic-only state followed by user-selected hypothesis / one candidate.

Recommended fix:

- Make default current product runtime either diagnosis-only or one selected candidate when explicitly requested.
- Keep `core_fast` as backend/advanced batch mode, not default product UX.

### `src/portfolio_review_workflow.py`

What it does:

- orders existing entrypoints so `analysis_subject` is diagnosed before candidates;
- if candidates are not skipped, invokes `run_candidate_factory.py` with either explicit candidates or profile;
- if comparison not skipped, appends `--then-compare`.

Alignment:

- Strongly aligned on current-portfolio-first ordering.
- Partially old on candidate orchestration: profile-based batch generation is still default when no explicit candidate is selected.

Recommended fix:

- Add a product-mode plan that stops after `analysis_subject`, problem classification, launchpad, and builder plan unless one selected candidate is requested.
- If `--candidates equal_weight` is supplied, ensure downstream comparison is scoped to that candidate plus current baseline.

### `run_candidate_factory.py` and `src/candidate_factory.py`

What it does:

- standalone default profile is `default_v1`;
- `default_v1` includes core benchmarks, risk budgets, classic optimizers, and robust suite;
- `core_fast` / `core_v1` include six benchmark/risk-budget candidates;
- profile classifications already label `default_v1` as `advanced_research_full_batch` and `core_fast` as `backend_routine_core_batch`.

Alignment:

- Acceptable as backend/advanced/research infrastructure.
- Not aligned if treated as product front door.

Recommended fix:

- Keep factory code, but rename product-boundary language away from “product menu”.
- Do not make `default_v1` or `core_fast` the default product UX.

### `run_compare_variants.py` and `src/candidate_comparison.py`

What it does:

- builds `candidate_comparison.json`;
- then unconditionally writes a large downstream artifact package:
  - `robustness_scorecard.json`;
  - `portfolio_health_score.json`;
  - `selection_decision.json`;
  - `current_vs_candidate.json`;
  - `tradeoff_explanation.json`;
  - `model_risk_diagnostics.json`;
  - `assumption_sensitivity.json`;
  - `pareto_dominance.json`;
  - `regret_analysis.json`;
  - `current_vs_policy_status.json`;
  - `action_plan.json`;
  - `decision_verdict.json`;
  - `ai_commentary_context.json`;
  - `monitoring_diff.json`;
  - `what_changed_summary.json`;
  - `decision_journal.json`;
  - decision package report / manifest.

Evidence: `src/candidate_comparison.py` writes this chain in `write_candidate_comparison_outputs()`.

Alignment:

- The six current product outputs are present.
- Serious contradiction: old/advanced outputs are generated as part of the same default compare path and precede some product-facing outputs in code order.
- Product output depends on old technical outputs: `decision_verdict.json` maps over `selection_decision.json` and action context; `current_vs_candidate.json` reads comparison and optional selection.

Recommended fix:

- Split compare writer into:
  1. core product writer;
  2. advanced downstream package writer;
  3. legacy compatibility writer.
- Product default should write only the current product bundle and necessary hidden technical inputs, or at minimum mark advanced outputs as non-product and hide them from product manifest/surface.

### `src/candidate_comparison.py` product menu logic

What it does:

- `PRODUCT_MENU_PROFILE_ID = "default_v1"`;
- `candidate_menu.product_menu_size` is based on default full menu;
- reduced menus are marked partial vs product default.

Alignment:

- Old behavior. It treats full-menu comparison as the product menu.
- This contradicts canonical “Diagnosis 2”, where the product should be current-vs-selected-candidate or a small user-created shortlist, not a hidden full candidate arena.

Recommended fix:

- Rename full menu to `advanced_research_menu_profile_id`.
- Product menu should be explicit selected candidate(s), not `default_v1`.

### New product adapter modules

Files:

- `src/problem_classification.py`
- `src/candidate_launchpad.py`
- `src/portfolio_alternatives_builder.py`
- `src/current_vs_candidate.py`
- `src/decision_verdict.py`
- `src/ai_commentary_context.py`
- `src/light_monitoring_summary.py`

What they do:

- implement the new diagnosis-first adapter/product bundle layer.

Alignment:

- These are the strongest code alignment with “Diagnosis 2”.
- Caveat: several depend on old comparison/selection/action/monitoring artifacts, so they are not yet an independent product pipeline.

Recommended fix:

- Promote these modules as the only current product-facing output layer.
- Ensure they can run in a selected-candidate-only flow.

### `src/selection_engine.py`

What it does:

- writes `selection_decision.json`, formal technical selection/no-trade artifact.

Alignment:

- Useful technical evidence.
- Not product-facing final answer; should be hidden behind `decision_verdict.json`.

### `src/action_engine.py`

What it does:

- writes `action_plan.json`, including deltas/trades/turnover/cost context.

Alignment:

- Useful backend/generated support.
- Full Action Plan / Rebalancing Advisor is listed in “Later”; it should not be current core product.

### `src/monitoring.py` and `src/light_monitoring_summary.py`

What they do:

- `monitoring.py` writes technical `monitoring_diff.json` and history;
- `light_monitoring_summary.py` writes product-facing `what_changed_summary.json`.

Alignment:

- `what_changed_summary.json` aligns with “Diagnosis 2”.
- Advanced monitoring/history is “Later” unless hidden/support.

### `src/decision_journal.py`

What it does:

- writes generated V1 decision journal.

Alignment:

- Full Decision Journal is “Later”; current core only needs light journal/grounding inside commentary if any.

### `src/portfolio_xray.py` and `src/stress.py`

What they do:

- implement Portfolio X-Ray, hidden risk, weakness map, archetype, risk budget, stress diagnostics, stress lab primitives, and some What Happens If API foundation.

Alignment:

- X-Ray and Stress are core.
- Portfolio Archetype is already implemented despite “Later” mentioning it. It is acceptable as diagnostic evidence inside X-Ray if not marketed as a separate later product module.
- What Happens If UI remains backlog; programmatic primitive can remain backend.

### `run_optimization.py`

What it does:

- legacy policy optimization.

Alignment:

- Legacy compatibility only.
- Must not be presented as current product path.

## 5. Output Contract Truth Audit

| Output | Correct classification | Current positioning risk | Notes / fix |
|---|---|---|---|
| `problem_classification.json` | Current Core Product Output | Low | Core diagnosis-to-problem bridge. |
| `candidate_launchpad.json` | Current Core Product Output | Low | Core hypothesis-card layer; not a candidate output. |
| `current_vs_candidate.json` | Current Core Product Output | Medium | Core only if scoped to selected candidate/shortlist; not full arena. |
| `decision_verdict.json` | Current Core Product Output | Medium | Product verdict; should hide Selection Engine terminology. |
| `ai_commentary_context.json` | Current Core Product Output / grounding only | Low | No LLM; should not be described as final AI prose. |
| `what_changed_summary.json` | Current Core Product Output | Low | Light monitoring summary; use instead of technical monitoring diff. |
| `candidate_comparison.json` | Advanced / Backend Evidence / technical contract | Medium | Useful input, but not current product answer. |
| `selection_decision.json` | Technical artifact / backend evidence | High | Must be hidden behind Decision Verdict. |
| `portfolio_health_score.json` | Advanced / Backend Evidence | High | From “Later”; do not present as core. |
| `robustness_scorecard.json` | Advanced / Backend Evidence | High | From “Later”; do not present as core. |
| `assumption_sensitivity.json` | Advanced / Backend Evidence | High | From “Later”; current code writes it after compare. |
| `pareto_dominance.json` | Advanced / Backend Evidence | High | Full comparison/research; not core. |
| `regret_analysis.json` | Advanced / Backend Evidence | High | Full comparison/research; not core. |
| `model_risk_diagnostics.json` | Advanced / Backend Evidence | Medium | Can support verdict, not product front. |
| `tradeoff_explanation.json` | Advanced/backend support or product support | Medium | Trade-off belongs in Current vs Candidate, but standalone artifact should be support unless product spec promotes it. |
| `action_plan.json` | Generated support artifact / advanced action evidence | High | Full Action Plan/Rebalancing Advisor is “Later”. |
| `monitoring_diff.json` | Technical artifact / advanced monitoring | Medium | Product should use `what_changed_summary.json`. |
| `decision_journal.json` | Generated support artifact / future full journal | High | Full journal is “Later”; keep as generated support. |
| `decision_package_summary.json/txt` | Generated report/support artifact | Medium | Not current product source of truth. |
| `portfolio_comparison.json/txt` | Legacy compatibility | Medium | Old policy/equal/risk/robust comparison; hide from current product. |
| CSV/TXT/HTML/PNG/PDF sidecars | Generated export artifacts | Medium | Not source-of-truth; optional export only. |

## 6. “Later” Leakage Audit

| Feature from “Later” | Where it appears now | Acceptable as backend evidence... | Needs doc demotion... | Runtime hide/filter... |
|---|---|---:|---:|---:|
| Portfolio Health Score | `SPEC.md`, `README.md`, `OUTPUTS.md`, `src/portfolio_health_score.py`, compare writer | Yes | Yes | Yes |
| Robustness Scorecard | `SPEC.md`, `README.md`, `OUTPUTS.md`, `src/robustness_scorecard.py`, compare writer | Yes | Yes | Yes |
| Macro Dashboard / Macro Overlay | Concept docs, macro/regime diagnostics in code/docs | Partial | Yes | Yes, dashboard not core |
| Full multi-candidate ranking / arena | Candidate factory/comparison docs and default batch profiles | Yes for research | Yes | Yes |
| Assumption Sensitivity | `src/assumption_sensitivity.py`, compare writer, roadmap/specs | Yes | Yes | Yes |
| Pareto / Dominance | `src/pareto_dominance.py`, compare writer | Yes | Yes | Yes |
| Regret Analysis | `src/regret_analysis.py`, compare writer | Yes | Yes | Yes |
| Model Risk Diagnostics | `src/tradeoff_and_model_risk.py`, compare writer | Yes | Yes | Possibly |
| Full Action Plan / Rebalancing Advisor | `src/action_engine.py`, compare writer, roadmap/specs | Yes | Yes | Yes |
| Full Decision Journal | `src/decision_journal.py`, compare writer | Yes | Yes | Yes |
| Advanced monitoring | `src/monitoring.py`, monitoring history/diff | Yes | Yes | Yes |
| Crisis Replay UI | specs/concept docs | No UI; specs only | Yes | N/A |
| What Happens If simulator | `src/stress.py` primitive/tests/spec; no UI | Backend primitive yes | Yes | Hide UI/product |
| Client-Fit Check | old mandate/client-fit mentions | Technical only | Yes | Yes |
| Asset X-Ray | concept/audit mentions; not validated as core | Maybe | Yes | Yes |
| Max Sharpe | docs explicitly target-only/deferred | No current runtime | Already mostly demoted | N/A |
| Tax-aware optimization | docs target-only/deferred | No current runtime | Already mostly demoted | N/A |
| Turnover-aware optimizer objective | docs target-only/deferred; turnover warnings/action exist | Partial support only | Yes | Yes |
| Tactical tilt | `run_view_after_optimization.py`, spec | Legacy/special protocol | Yes | Yes |
| Full custom constraints UI | concept docs | No | Yes | N/A |
| Multi-client workspace | target docs | No | Yes | N/A |
| Polished PDF report product | export/report docs | Export only | Yes | Yes |

## 7. New Project Runtime Gap

### Desired runtime

```text
current portfolio
-> X-Ray
-> Stress
-> Problem Classification
-> Launchpad
-> Builder
-> one selected candidate
-> Current vs Candidate
-> Decision Verdict
-> AI grounding/commentary
-> What Changed
```

### Actual runtime today

Based on code inspection:

1. `run_portfolio_review.py` builds a portfolio-first plan.
2. `run_report.py` materializes `analysis_subject` and writes diagnostics/product diagnosis artifacts.
3. Unless `--skip-candidates` is used, portfolio review invokes `run_candidate_factory.py`.
4. If no explicit `--candidates` is supplied, default review mode `core` maps to `core_fast`.
5. `core_fast` runs the same six candidate ids as `core_v1` and enables parallel lightweight reports by default.
6. Factory usually invokes comparison with `--then-compare`.
7. Comparison scans/generated candidate evidence and writes `candidate_comparison.json`.
8. The comparison writer then writes advanced/old downstream artifacts: robustness, health score, selection, sensitivity, Pareto, regret, action, monitoring, journal, etc.
9. Product-facing outputs (`current_vs_candidate.json`, `decision_verdict.json`, `ai_commentary_context.json`, `what_changed_summary.json`) are written as adapters on top of the technical/advanced pipeline.

### Gap table

| Desired stage | Actual status | Mark |
|---|---|---|
| Current portfolio first | `analysis_subject` is materialized first | Aligned |
| X-Ray | Implemented | Aligned |
| Stress | Implemented | Aligned |
| Problem Classification | Implemented | Aligned |
| Candidate Launchpad | Implemented as JSON | Aligned/partial UX |
| Builder | Backend wrapper only | Partially aligned |
| One selected candidate | Possible via `--candidates`, not default | Serious contradiction |
| Current vs Candidate | Implemented, but built from broader comparison | Partially aligned |
| Decision Verdict | Implemented mapping over Selection/Action | Partially aligned |
| AI Commentary | Grounding only, no LLM | Aligned if called grounding; not final commentary |
| What Changed | Light summary implemented | Aligned |
| No old scorecard/action/journal dominance | Old package is still generated by default compare | Serious contradiction |

## 8. Critical Contradictions

### Critical

1. **Agent entrypoint contradiction**: `AGENTS.md` still frames the current implementation around V1 decision artifacts including scorecards, health score, action plan, monitoring, and decision journal. This can mislead every future agent response.
2. **Runtime default contradiction**: default portfolio review still runs a batch candidate factory (`core_fast`, six candidates) when canonical product should diagnose first and test one selected hypothesis unless the user chooses a shortlist/research mode.
3. **Compare writer contradiction**: `write_candidate_comparison_outputs()` unconditionally generates advanced/old downstream artifacts as part of the main compare path.
4. **Product menu contradiction**: `candidate_comparison.py` treats `default_v1` full menu as `PRODUCT_MENU_PROFILE_ID`, contradicting “current-vs-selected-candidate” product truth.

### High

1. **`SPEC.md` implementation table contradiction**: implemented advanced modules are listed alongside core product modules without product-priority separation.
2. **`README.md` ordering contradiction**: old V1 artifacts appear before/alongside diagnosis-first product bundle in “Implemented today”.
3. **Output contradiction**: `OUTPUTS.md` classifies correctly, but runtime still writes advanced outputs in the same default path.
4. **Terminology contradiction**: Selection Engine remains the technical contract, but product truth says Decision Verdict is user-facing. This is acceptable only if consistently hidden/mapped.
5. **Testing contradiction**: tests validate old downstream package as part of comparison; product tests must assert product-bundle dominance.

### Medium

1. **Macro/regime diagnostics exist while Macro Dashboard is backlog**. Needs clearer distinction.
2. **Portfolio Archetype exists despite being listed as later in “Later”**. Acceptable if described as X-Ray diagnostic evidence, not separate product module.
3. **Action Plan exists but full Rebalancing Advisor is backlog**. Needs product filtering.
4. **Decision Journal exists but full journal/workflow is backlog**. Needs product filtering.
5. **PDF/export docs remain prominent in some places**. Should be export-only.

### Low

1. Historical audits and ExecPlans contain old product language. Acceptable if clearly historical.
2. Archived docs contain old architecture. Acceptable if never treated as current truth.

## 9. Remediation Roadmap

### Session 01 — Documentation Truth Reset

Objective: make “Diagnosis 2” the unmistakable current product across top-level docs.

Files likely affected:

- `AGENTS.md`
- `README.md`
- `SPEC.md`
- `PRODUCT.md`
- `ARCHITECTURE.md`
- `BUSINESS_VISION.md`
- `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`
- `GLOSSARY.md`

What to change:

- Put canonical current flow at the top.
- Define “Diagnosis 2 Later” as backlog/advanced/later.
- Move Health Score, Robustness, Action, Journal, macro dashboard, full candidate arena, etc. out of current product wording.
- Preserve implemented capability notes but classify them as advanced/backend/generated support.

What not to touch:

- Do not delete specs or code.
- Do not rename output schemas yet.

Verification:

```bash
python scripts/verify_docs.py
python -m pytest tests/test_docs_links.py -q
rg -n "Portfolio Health Score|Robustness Scorecard|Action Plan|Decision Journal|Macro Dashboard|default_v1|PRODUCT_MENU_PROFILE_ID" AGENTS.md README.md SPEC.md PRODUCT.md ARCHITECTURE.md docs/DIAGNOSTIC_PRODUCT_CONCEPT.md
```

Expected output:

- All top-level docs say canonical product = “Diagnosis 2”.
- Old modules appear only with advanced/backend/backlog qualifiers.

### Session 02 — Output Classification Cleanup

Objective: make output policy and manifests reflect product-vs-advanced truth.

Files likely affected:

- `OUTPUTS.md`
- `src/product_bundle_paths.py`
- manifest-related code if applicable
- specs for affected output contracts

What to change:

- Product surfaces should list only six current product outputs by default.
- Advanced outputs can remain generated but categorized as non-product.
- Add explicit “do not present as Core MVP” notes to advanced output specs.

What not to touch:

- Do not remove generated files yet.

Verification:

```bash
python -m pytest tests/test_product_bundle_paths.py tests/test_product_bundle_integration.py -q
```

Expected output:

- Product bundle paths resolve the six current outputs first.
- Advanced artifacts are categorized but not product-facing.

### Session 03 — Default Runtime Cleanup

Objective: stop default current-product review from behaving like batch candidate research.

Files likely affected:

- `run_portfolio_review.py`
- `src/portfolio_review_workflow.py`
- `src/candidate_factory.py`
- workflow specs and operator guide

What to change:

- Decide product default:
  - diagnosis-only by default; or
  - explicit one-candidate demo when `--candidates ID` is supplied.
- Move `core_fast` to backend/advanced batch option.
- Keep `--mode full` and standalone factory as advanced/research.

What not to touch:

- Do not remove candidate builders.
- Do not remove factory profiles.

Verification:

```bash
python run_portfolio_review.py --dry-run
python run_portfolio_review.py --dry-run --candidates equal_weight
python -m pytest tests/test_portfolio_review_workflow.py -q
```

Expected output:

- Default dry run does not imply six-candidate product flow.
- Explicit candidate dry run shows one selected candidate path.

### Session 04 — Selected-Candidate-Only Compare Fix

Objective: make product comparison use current vs selected candidate, not all old candidate folders.

Files likely affected:

- `src/candidate_comparison.py`
- `src/current_vs_candidate.py`
- `src/selection_engine.py`
- `src/portfolio_review_workflow.py`
- tests around comparison/current-vs-candidate

What to change:

- Ensure explicit `--candidates equal_weight` limits product comparison to `analysis_subject` + selected candidate.
- Do not let stale candidate folders silently dominate product verdict.
- Keep full folder scan only in advanced/research compare mode.

What not to touch:

- Do not break advanced full comparison.

Verification:

```bash
python run_portfolio_review.py --dry-run --candidates equal_weight
python -m pytest tests/test_current_vs_candidate.py tests/test_candidate_comparison.py tests/test_portfolio_review_workflow.py -q
```

Expected output:

- Product current-vs-candidate is selected-candidate scoped.
- Full comparison still works when explicitly requested as advanced.

### Session 05 — Demote Health/Robustness/Scorecards Runtime Surface

Objective: keep advanced artifacts in code but prevent them from driving current product flow.

Files likely affected:

- `src/candidate_comparison.py`
- `src/portfolio_health_score.py`
- `src/robustness_scorecard.py`
- `src/selection_engine.py`
- `src/decision_verdict.py`
- `OUTPUTS.md`
- related specs/tests

What to change:

- Add mode/output policy gating: core product vs advanced package.
- In core product mode, either do not write advanced scorecards or write them under advanced category only.
- `decision_verdict.json` should remain product-facing; if it needs technical selection evidence, keep that hidden.

What not to touch:

- Do not delete scoring modules.

Verification:

```bash
python -m pytest tests/test_decision_verdict.py tests/test_portfolio_health_score.py tests/test_robustness_scorecard.py tests/test_selection_engine.py -q
```

Expected output:

- Advanced tests still pass.
- Product mode no longer presents scorecards as main answer.

### Session 06 — Operator Guide Update

Objective: make operator commands match canonical product truth.

Files likely affected:

- `docs/product_flow_operator_guide.md`
- `README.md`
- `WORKFLOW.md`
- `TESTING.md`

What to change:

- Show canonical command order.
- Explain diagnosis-only, one-candidate, shortlist, and advanced/research modes.
- Mark `run_candidate_factory.py --profile default_v1` as advanced/research only.

What not to touch:

- Do not remove legacy command docs; demote them.

Verification:

```bash
python scripts/verify_docs.py
python -m pytest tests/test_docs_links.py -q
```

Expected output:

- Operators cannot accidentally treat old full candidate arena as current product.

### Session 07 — Final Validation Run

Objective: prove the project now behaves and documents itself as “Diagnosis 2”.

Verification:

```bash
python run_portfolio_review.py --dry-run
python run_portfolio_review.py --dry-run --candidates equal_weight
python -m pytest tests/test_problem_classification.py tests/test_candidate_launchpad.py tests/test_portfolio_alternatives_builder.py tests/test_current_vs_candidate.py tests/test_decision_verdict.py tests/test_ai_commentary_context.py tests/test_light_monitoring_summary.py tests/test_product_bundle_integration.py -q
python scripts/verify_docs.py
```

Expected output:

- Dry-run default matches canonical product path.
- One selected candidate path is explicit and scoped.
- Product bundle tests pass.
- Advanced outputs remain available only as advanced/backend evidence.

## 10. Final Verdict

### What is the project today...

Today the project is a **hybrid**:

```text
old optimizer/report/scorecard-heavy backend
+
new diagnosis-first “Diagnosis 2” product adapter layer
+
partially corrected documentation
+
default runtime that still generates too much old/advanced evidence
```

It is not a clean “Diagnosis 2” project yet.

### What should the project become after remediation...

It should become:

```text
Diagnosis 2 as the canonical current product
with old optimizer/report/scorecard capabilities preserved as advanced/backend/legacy support
```

The current product should be understood as:

```text
Input portfolio -> X-Ray -> Stress -> Problems -> Launchpad -> Builder -> one selected candidate -> Current vs Candidate -> Decision Verdict -> AI grounding -> What Changed
```

### One highest-leverage fix

The highest-leverage fix is:

> Rewrite `AGENTS.md`, `README.md`, `SPEC.md`, and `OUTPUTS.md` so the six-file product bundle and “Diagnosis 2” flow are the first and dominant truth, while Health/Robustness/Action/Journal/Macro/full candidate arena are explicitly advanced/backend/backlog.

This prevents future agents from inheriting the old project identity.

### What should be hidden from current product flow...

Hide or demote by default:

- Portfolio Health Score;
- Robustness Scorecard;
- Assumption Sensitivity;
- Pareto / Dominance;
- Regret Analysis;
- Model Risk Diagnostics as standalone product module;
- Selection Engine terminology;
- full Action Plan / Rebalancing Advisor;
- technical Monitoring Diff;
- full Decision Journal;
- decision package summary;
- full multi-candidate arena;
- macro dashboard;
- legacy PDF/report suite;
- legacy policy optimization.

### What can remain in code but only as advanced/backend evidence...

These can remain:

- `candidate_comparison.json` and candidate factory;
- `selection_decision.json`;
- `portfolio_health_score.json`;
- `robustness_scorecard.json`;
- `assumption_sensitivity.json`;
- `pareto_dominance.json`;
- `regret_analysis.json`;
- `tradeoff_explanation.json`;
- `model_risk_diagnostics.json`;
- `action_plan.json`;
- `monitoring_diff.json`;
- `decision_journal.json`;
- `decision_package_summary.*`;
- macro/regime diagnostics;
- robust optimizers and scenario research;
- tactical tilt protocol;
- PDF/export tools.

But they must not define the current product unless a future accepted spec explicitly promotes them.

## Finding Counts

| Severity | Count |
|---|---:|
| Critical | 4 |
| High | 5 |
| Medium | 5 |
| Low | 2 |

## Appendix A — Evidence Commands Used

Representative local searches and inspections used for this audit:

```powershell
Select-String -Path README.md,OUTPUTS.md,AGENTS.md,SPEC.md -Pattern 'robustness scorecard|Portfolio Health Score|Action Plan|Decision Journal|Selection/No-Trade|advanced|backend|current generated|generated V1 decision artifacts' -CaseSensitive:$false
Select-String -Path run_portfolio_review.py,run_candidate_factory.py,run_compare_variants.py,run_report.py,src/candidate_comparison.py -Pattern 'core_fast|default_v1|core_v1|write_candidate_comparison_outputs|write_robustness|write_portfolio_health|write_selection|write_action|write_monitoring|write_decision_journal|current_vs_candidate|decision_verdict|ai_commentary|what_changed|candidate_profile|--candidates|skip-candidates|parallel' -CaseSensitive:$false
rg -n "What Happens If|Crisis Replay|Asset X-Ray|Asset Diagnostics|Client-Fit|Portfolio Archetype|Macro Overlay|Regime Dashboard|walk-forward|out-of-sample" README.md SPEC.md docs src tests -S
```

No code was executed to regenerate project artifacts. This is a source/doc/runtime inspection audit only.
