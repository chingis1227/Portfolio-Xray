# Full Project Architecture Alignment Audit

Date: 2026-05-25  
Scope: full-project architecture / documentation / code / generated-contract alignment for Portfolio MRI.  
Mode: audit only. No code, existing documentation, generated output, staging, commits, deletes, or schema renames were performed.  
Basis: current working tree as inspected on 2026-05-25, including tracked changes and untracked files visible to git. Because the working tree is heavily dirty, this audit treats the checked-out filesystem as the observable project state and explicitly marks dirty-tree risk where relevant.

## 1. Executive Summary

Blunt verdict: the project is **conceptually much more aligned than before**, but it is **not cleanly aligned as a project system** yet.

The new diagnosis-first product architecture is now strongly represented in the active product/architecture documents and in new additive code modules. The safest parts are the guardrails: current portfolio first, candidate portfolios as hypotheses, no-trade as valid, AI as explanation/grounding only, and legacy optimizer flows preserved as compatibility rather than deleted.

The biggest contradictions are:

1. **Dirty-tree authority problem.** Many of the files that make the new architecture real are still modified or untracked. This includes `SPEC.md`, `OUTPUTS.md`, `docs/specs/*.md`, `CODE_MIGRATION_PLAN.md`, `docs/exec_plans/2026-05-25_code_migration_to_diagnosis_first_portfolio_mri.md`, and new source modules such as `src/problem_classification.py`, `src/candidate_launchpad.py`, `src/current_vs_candidate.py`, `src/decision_verdict.py`, `src/ai_commentary_context.py`, and `src/light_monitoring_summary.py`. Until this is reviewed and committed in a clean sequence, the repository has no stable baseline for further development.
2. **Docs disagree about implementation status.** Some high-level docs still say Problem Classification, Candidate Launchpad, Alternatives Builder, Decision Verdict, and AI Commentary are Target/TBD or require verification, while the current working tree contains modules/specs and `SPEC.md` status-matrix rows claiming several are implemented additive artifacts.
3. **Command matrix drift.** `README.md` and `OUTPUTS.md` still say default `run_portfolio_review.py --mode core` maps to `core_v1`; code and `docs/specs/portfolio_review_workflow_spec.md` map core mode to `core_fast`. This is a concrete code/doc contradiction.
4. **Old decision pipeline still dominates runtime output.** `write_candidate_comparison_outputs()` still writes candidate comparison, Robustness Scorecard, Portfolio Health Score, Selection Engine, tradeoff/model-risk, assumption sensitivity, Pareto, regret, action, monitoring, decision journal, decision package, and then the new product-facing adapters. This is technically valid, but product-facing architecture can still be overwhelmed by old scoring/selection artifacts.
5. **Generated outputs are stale relative to the new contracts.** Current known generated folders do not yet contain `problem_classification.json`, `candidate_launchpad.json`, `current_vs_candidate.json`, `decision_verdict.json`, `ai_commentary_context.json`, or `what_changed_summary.json`, even though current code/docs say these are written by report/compare flows. Existing `Main portfolio/analysis_subject/output_manifest.json` is from before those new artifacts.

What is safe:

- The active product philosophy in `BUSINESS_VISION.md`, `PRODUCT.md`, `ARCHITECTURE.md`, `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`, and `AGENTS.md` is mostly aligned with diagnosis-first decision support.
- Current target modules are additive and explicitly guarded: they do not change formulas, optimizers, stress scenarios, Selection Engine schemas, monitoring schemas, or execution instructions.
- Legacy optimizer and batch factory capabilities are mostly documented as preserve/legacy/backend/advanced rather than deleted.
- AI is not currently used as a calculation or decision source. The new `ai_commentary_context.json` layer is grounding-only.

What is risky:

- Future work may accidentally build on uncommitted/untracked migration files as if they are stable.
- Product-facing docs can still be read as target-only while specs/code claim implemented artifacts, creating confusion for implementation sessions.
- The default standalone `run_candidate_factory.py` still defaults to `default_v1`, an advanced/research full batch. This is acceptable for backend tooling but dangerous if treated as product front door.
- Health/Robustness/Selection artifacts are still generated in the main comparison chain and may be mistaken for the main product answer.
- Archive and old audit material contains optimizer-first and macro/scorecard language; registers warn about this, but stale links still block docs verification per the migration plan notes.

Must fix before more development:

1. Resolve and commit or explicitly shelve the diagnosis-first migration working-tree set. Do not continue on top of the current dirty state without a strict allowlist.
2. Align command matrices with actual code: `core_fast` vs `core_v1`.
3. Reconcile implementation-status wording across `README.md`, `PRODUCT.md`, `ARCHITECTURE.md`, `SPEC.md`, `OUTPUTS.md`, and detailed specs.
4. Decide whether new product-facing artifacts should be generated in the same compare pipeline by default or exposed as a separate product bundle on top of the technical decision package.
5. Refresh generated outputs only in a separate approved generated-artifact session, not inside this audit.

## 2. New Architecture Baseline

The intended active architecture is:

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

Product philosophy baseline:

- The system is **diagnosis-first**, not optimizer-first.
- The current portfolio is the subject of analysis before candidate generation or interpretation.
- Candidate portfolios are **investment hypotheses**, not automatic recommendations.
- No-trade / keep-current is a valid verdict.
- Optimization, candidate builders, robust portfolios, Health Score, Robustness Scorecard, Pareto, regret, and assumption sensitivity are supporting evidence or advanced/research infrastructure unless promoted by explicit specs.
- Decision Verdict is product-facing language over deterministic evidence. It must not silently rename `selection_decision.json` or Selection Engine fields.
- AI Commentary is explanation over deterministic JSON evidence. It must not calculate metrics, select portfolios, create source-of-truth statuses, or issue trade instructions.
- Advanced/Later features remain preserved where implemented, but must not leak into Core MVP UX by wording accident.

## 3. Canonical Source-of-Truth Map

| Ownership area | Current source(s) | Audit result |
| --- | --- | --- |
| Product vision | `BUSINESS_VISION.md`, `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md` | Mostly clear. Strong diagnosis-first philosophy. Some sections still say target modules require verification even though current working tree has implementations. |
| Product UX / target flow | `PRODUCT.md`, `DESIGN.md`, `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md` | Mostly clear as target. `PRODUCT.md` is intentionally cautious but now partly stale against implemented additive artifacts. |
| Architecture | `ARCHITECTURE.md` | Mostly aligned as current/target/advanced/legacy map. Still says several target layers require code/spec verification, which is now partly stale in the current working tree. |
| Current implementation contract | `SPEC.md` | Mixed. Status matrix reflects new implementations; earlier sections still describe them as Target/TBD. This is a high-severity source-of-truth contradiction. |
| Detailed technical specs | `docs/specs/*.md` | Generally strong. New specs exist for diagnosis-first adapters. Some older specs intentionally preserve Selection/scorecard language. `candidate_factory_spec.md` has internal wording tension around `default_v1`. |
| Outputs | `OUTPUTS.md`, `docs/specs/reporting_outputs_spec.md`, output manifests | `OUTPUTS.md` lists new artifacts, but current generated outputs/manifests do not show them yet. Command matrix still says `core_v1`, conflicting with code/spec `core_fast`. |
| Workflow/process | `RULES.md`, `WORKFLOW.md`, `TESTING.md`, `PLANS.md`, `AGENTS.md`, `docs/operational_runbook.md` | Mostly aligned. Some top-line old name `Portfolio X-Ray & Optimization Terminal / Portfolio MRI` remains in process docs. |
| Historical/archive references | `docs/archive/*`, old `docs/audits/*.md`, old `docs/exec_plans/*.md`, `CHANGELOG.md`, `DECISIONS.md` | Registers now correctly warn that old language is historical. Archive should not be rewritten except broken-link maintenance if verification requires it. |
| Dirty-tree context | `DIRTY_TREE_CLASSIFICATION.md`, `git status --short` | Clear warning exists, but the tree remains heavily dirty. This is the biggest process risk. |

Source-of-truth ownership is **partly clear but currently confused by timing**: product docs define target direction; specs/code in the dirty working tree claim implementation; generated outputs lag behind; command matrices disagree on default profile.

## 4. Documentation Audit

Classification legend: Aligned, Partially aligned, Misaligned, Historical/Archive only, Requires human review.

| File / group | Classification | What it currently says | Match to new architecture | Old/legacy language found | Risk | Recommended action |
| --- | --- | --- | --- | --- | --- | --- |
| `README.md` | Partially aligned | Leads with Portfolio MRI / Portfolio X-Ray, diagnosis support, JSON default, portfolio-first workflow. | Philosophy aligned. Runtime profile docs stale: says core uses `core_v1`; code uses `core_fast`. Says target modules are TBD though working tree has additive modules. | Candidate Factory and Optimization Engine still listed in “Blocks 1-5 MVP core”; full decision artifacts listed prominently. | High | Patch command matrices to `core_fast`; update target/implemented wording after migration is accepted. |
| `BUSINESS_VISION.md` | Aligned | Defines diagnosis-first chain exactly matching new baseline; candidate as hypothesis; guided not prescriptive; AI as explanation. | Strong match. Correctly demotes Health/Robustness as primary modules. | Uses “no-trade recommendation” in advisor pain/value language; acceptable but could prefer verdict. | Low | Optional wording polish from recommendation to verdict where product-facing. |
| `PRODUCT.md` | Partially aligned | Strong target MVP flow and product language. Marks Problem Classification, Candidate Launchpad, Alternatives Builder, Decision Verdict, AI Commentary as target/requires verification. | Product philosophy aligned, implementation status stale relative to current working tree. | “Recommended action” appears in Decision Verdict output; no automatic recommendation framing. | Medium | Update implementation relationship section after migration baseline is accepted; keep UI/workspace as Target/TBD. |
| `ARCHITECTURE.md` | Partially aligned | Clear current vs target vs advanced vs legacy model; maps Selection Engine to Decision Verdict backend evidence. | Conceptually aligned. “Requires code/spec verification” list is now partly stale. | Legacy optimizer and batch factory preserved. | Medium | Update verification status for implemented additive artifacts; keep UI and schema replacement TBD. |
| `SPEC.md` | Partially aligned / internally inconsistent | Top says target product areas remain TBD; status matrix says the new layers are implemented. | Good implementation mapping but contradictory internal status. | Title line still says `Portfolio X-Ray & Optimization Terminal / Portfolio MRI`; Selection/No-Trade Recommendation remains technical contract. | High | Reconcile top implementation scope with status matrix. Keep Selection Engine terms but map to Decision Verdict. |
| `RULES.md`, `WORKFLOW.md`, `DATA.md`, `GLOSSARY.md`, `KNOWN_ISSUES.md`, `TESTING.md` | Partially aligned | Enforce process, generated-output boundary, testing and source-of-truth rules. | Mostly aligned. | Several top lines still use Optimization Terminal; testing focuses old comparison/selection bundle. | Low/Medium | Naming cleanup; add explicit new-artifact test bundle in `TESTING.md` if migration accepted. |
| `OUTPUTS.md` | Partially aligned | Strong output policy; lists new artifacts and product boundary. | Output contracts mostly aligned. Current generated outputs are stale; command matrix says `core_v1` not `core_fast`. | Full candidate factory commands prominent; scorecards listed with artifacts. | High | Fix core profile matrix; classify advanced artifacts visibly; refresh outputs separately if approved. |
| `AGENTS.md` | Aligned | Describes Portfolio MRI / X-Ray as diagnosis-first and not black-box optimizer. | Strong match. | Mentions Health/Robustness as generated/backend evidence, not core UI. | Low | No change required. |
| `CHANGELOG.md`, `DECISIONS.md` | Historical/current log | Logs many old features and decisions. | Acceptable history, not current product direction. | Health/Robustness/Selection prominence, winner phrases, recommendation terms. | Low | Do not rewrite history. Add new dated entries only when future changes are actually made. |
| `CODE_MIGRATION_PLAN.md` | Partially aligned / requires review | Untracked plan for additive diagnosis-first migration. Early sections say target modules missing; later sessions say implemented. | Good migration intent; stale early inventory remains inside same plan. | Selection/Health/Robustness preserved as backend. | Medium | Add a top “current status after Session 12” note if retained. |
| `DOCUMENTATION_MIGRATION_PLAN.md`, `DOCUMENTATION_ALIGNMENT_AUDIT.md`, `DOCUMENTATION_ALIGNMENT_PATCH_PLAN.md` | Historical/plan | Define/record migration intent and red flags. | Useful but partly superseded. | Search-command examples and old terms. | Low | Preserve; use only after re-verification. |
| `DIRTY_TREE_CLASSIFICATION.md` | Requires human review | Classifies dirty working tree and says do not stage yet. | Highly relevant to process safety. | None problematic. | High | Use before staging/committing anything. |
| `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md` | Aligned | Clear product blueprint with exact new chain; classifies old 24-block concept. | Strong match. | Says target direction unless verified; now partly stale. | Medium | Update guardrail/status notes after migration baseline accepted. |
| `docs/specs/README.md` | Aligned | Says specs own current contracts; product language does not rename schemas. Lists new diagnosis-first specs. | Strong match. | Selection/No-Trade remains technical. | Low | No major change. |
| New diagnosis-first specs | Aligned / requires commit review | Own `workflow_state`, `problem_classification`, `candidate_launchpad`, `portfolio_alternatives_builder`, `current_vs_candidate`, `decision_verdict`, `ai_commentary_grounding`, `light_monitoring_summary`. | Strongly aligned; additive and guarded. | `recommended_action` in Verdict spec is wording-sensitive. | Medium | Review and commit as coherent migration set. |
| `docs/specs/candidate_factory_spec.md` | Partially aligned | Adds boundary that batch factory is backend/advanced/research, but also says `default_v1` is “Standard product comparison arena”. | Boundary aligned; internal wording conflict remains. | `next_recommended_command` technical field; `default_v1` product-arena wording. | High | Replace old product-arena wording; do not rename JSON fields. |
| `docs/specs/candidate_comparison_spec.md` | Partially aligned | Canonical comparison evidence; not recommendation; downstream scorecards and Selection consume it. | Technically aligned. Product risk because full comparison still dominates technical flow. | `recommendation_status` field; Health/Robustness prerequisite language. | Medium | Keep technical contract; bridge product surfaces to `current_vs_candidate.json`. |
| `docs/specs/selection_engine_spec.md` | Partially aligned | Owns Selection Engine and No-Trade technical contract; product docs may call layer Decision Verdict. | Correct if kept technical. | “No-Trade Recommendation”, “composite winner”. | Medium | Keep schema/terms; add product-facing wording guard where needed. |
| Health/Robustness/advanced specs | Mostly aligned with caveat | Most now say diagnostic/non-binding or advanced/supporting. | Good boundary, but runtime writes these by default. | Score/ranking/winner/best metric terms. | Medium | Keep specs; ensure UI/output docs classify as supporting evidence. |
| Stress/X-Ray/data specs | Mostly aligned | Diagnostic evidence contracts. | Core X-Ray and Stress aligned; macro/factor/PCA are advanced overlays. | Macro dashboard/regime concepts in older docs. | Medium | Keep macro/deep diagnostics advanced unless promoted. |
| Optimizer/candidate specs | Partially aligned | Preserve optimizer/candidate capabilities. | Valid as backend/legacy/advanced, not product front door. | Optimizer, target weights, tactical tilt. | Medium | Add “hypothesis builder support / not default UX” notes where missing. |
| `docs/exec_plans/README.md` and `docs/audits/README.md` | Aligned | Warn old plans/audits are historical snapshots. | Good archive policy. | Mojibake in symbols in exec-plan register. | Low | Optional encoding cleanup later. |
| `docs/exec_plans/*.md`, `docs/audits/*.md`, `docs/archive/*` | Historical/Archive only | Many old plans/audits/legacy copies. | Not current direction. | Optimizer-first, Selection, scorecard, Macro, winner language. | Low | Preserve; do not rewrite unless maintaining links. |
| `docs/ROADMAP.md` | Partially aligned / historical-current mix | Durable roadmap still opens with Optimization Terminal and old scoring/selection phases. | Useful history, but can confuse. | Optimization Terminal, Selection/Health/Robustness phases, winner wording. | Medium | Add top note that current direction is diagnosis-first and old phases are history. |
| `docs/operational_runbook.md`, `docs/optimization_run_checks.md` | Partially aligned / legacy-specialized | Portfolio-first guidance plus legacy optimizer playbooks. | Mostly aligned if legacy sections stay separate. | Legacy policy output and candidate factory playbooks prominent. | Low/Medium | Update profile names; keep optimizer checks legacy. |

## 5. Deep Red-Flag Search

Search scope included Markdown and Python source, excluding obvious generated/cache/output folders where possible. Counts are approximate because many historical files and search-command examples intentionally contain the terms.

| Phrase / pattern | Approx count | Example paths and snippets | Classification | Action |
| --- | ---: | --- | --- | --- |
| `Optimization Terminal` | 20 | `WORKFLOW.md:3`, `RULES.md:3`, `OUTPUTS.md:3`, `SPEC.md:3`, `DATA.md:3`, `GLOSSARY.md:3`, `KNOWN_ISSUES.md:3`, `docs/ROADMAP.md:3`. | Needs wording fix in active root docs where it weakens identity; acceptable in archive. | Medium cleanup. |
| `best portfolio` | 13 | `PRODUCT.md:380` says Decision Verdict is not simply “pick the best portfolio”; `BUSINESS_VISION.md:156` says candidate is not the best portfolio. | Mostly acceptable forbidden/non-goal context. | No urgent fix. |
| `recommended portfolio` | 5 | Scorecard specs forbid the phrase; archive contains old usage. | Acceptable forbidden/historical context. | No action except archive policy. |
| `automatic recommendation` | 11 | `PRODUCT.md:42` says candidate is not an automatic recommendation. | Acceptable negative context. | No action. |
| `optimizer-first` | 17 | Migration docs flag it; `src/analysis_setup.py:513` and `input_assumptions_spec.md:133` document compatibility optimizer-first mode. | Mostly acceptable compatibility/negative context. | Ensure default flow avoids it. |
| `batch candidate generation` | 6 | Migration docs say move away from automatic batch as core UX; `PRODUCT.md:526` preserves full batch as infrastructure/research. | Mostly acceptable. | Fix candidate factory wording. |
| `Selection Engine` | 161 | Technical specs/code use it; Decision Verdict maps it. | Acceptable technical context, product exposure risk. | Keep technical term; product surfaces should say Verdict. |
| `Portfolio Health Score` | 83 | Specs define diagnostic/backend; README lists among V1 artifacts. | Acceptable technical context; leakage risk. | Label as supporting evidence. |
| `Robustness Scorecard` | 107 | Same as Health Score. | Acceptable technical context; leakage risk. | Label as supporting evidence. |
| `Macro Dashboard` | 17 | Product concept says do not make mandatory; archive positions it as overlay. | Mostly acceptable negative/historical context. | Do not promote to Core MVP. |
| `AI decides` / `AI calculates` | 0 exact matches | Related docs say AI explains, code calculates. | Aligned. | No action. |
| `winner` | 59 | `ARCHITECTURE.md:261` says it does not always pick a winner; `selection_engine_spec.md` and `regret_analysis_spec.md` use technical winner fields. | Technical context mostly acceptable, product-facing risk. | Avoid in product copy. |
| `black-box optimizer` | 14 | Used as negative/non-goal in active product docs. | Acceptable. | No action. |
| `recommended_action` / recommendation wording | Many | `decision_verdict.py` and spec use `recommended_action`; product docs use “no material rebalance recommended.” | Mixed. | Do not rename now; consider future wording migration only with schema plan. |

Serious contradictions from red-flag search:

- `candidate_factory_spec.md` simultaneously says batch factory is backend/advanced/research and labels `default_v1` as “Standard product comparison arena.”
- Active root docs still use “Optimization Terminal” in top identity lines.
- Code comments/docs contain mojibake in a few places (`—`, `→`), which is readability risk but not an architecture contradiction.

## 6. Code Architecture Audit

| Target layer | Existing modules/files | Current implementation status | Missing / partial pieces | Old modules still drive flow | Classification | Recommended next action |
| --- | --- | --- | --- | --- | --- | --- |
| Input Portfolio | `config.yml`, `src/analysis_setup.py`, `src/config_schema.py`, `run_report.py --materialize-analysis-subject`, `src/workflow_state.py` | Implemented as CLI/config/file-first. `analysis_subject` is materialized first in `run_portfolio_review.py`. Workflow-state helper exists. | No interactive input UX. Dirty config changes require review. | Legacy `run_optimization.py` still writes policy weights for compatibility. | Core backend + legacy compatibility. | Stabilize docs and dirty tree; keep input contracts precise. |
| Portfolio X-Ray | `src/portfolio_xray.py`, `run_report.py`, `docs/specs/portfolio_xray_*` | Implemented diagnostic artifact. Explicitly says it does not optimize, score, select, or recommend. | Product UI sections not implemented. | Root legacy `portfolio_xray.json` may coexist with `analysis_subject/portfolio_xray.json`. | Core backend. | Ensure users inspect `analysis_subject/` first; preserve no-score/no-recommendation language. |
| Stress Test Lab | `src/stress.py`, `src/stress_*`, `run_report.py`, stress specs | Implemented rich stress/factor/regime/PCA diagnostics. | Full “lab” UI and user custom scenario UX are not core. | Macro/regime/factor diagnostics can dominate artifacts. | Core backend for stress; advanced overlays. | Keep macro/PCA/deep factor as advanced unless promoted. |
| Problem Classification | `src/problem_classification.py`, `docs/specs/problem_classification_spec.md`, wired in `run_report.py` after X-Ray summary | Implemented in current working tree as additive `problem_classification.json`; diagnostic-only; no new formulas or decisions. | Current generated outputs inspected do not yet contain the artifact. Product docs still partly say target/TBD. | Uses X-Ray/stress evidence only. | Core product adapter, pending baseline acceptance. | Commit/review migration; update product docs; refresh outputs separately if approved. |
| Candidate Launchpad | `src/candidate_launchpad.py`, `docs/specs/candidate_launchpad_spec.md`, wired in `run_report.py` after Problem Classification | Implemented as `candidate_launchpad.json`; cards contain goals/suggested methods, no weights, no builder execution. | No UI. Current generated outputs absent. | Candidate factory still builds actual candidates. | Core product adapter, pending baseline acceptance. | Keep cards non-portfolio; update product docs after commit. |
| Portfolio Alternatives Builder | `src/portfolio_alternatives_builder.py`, spec | Implemented as wrapper/build-plan generator mapping selected method to `run_candidate_factory.py --candidates <id> ... --then-compare`; delegates to existing builders. | No UI/service endpoint. Does not write an output artifact by itself. | Candidate factory and per-candidate builders still execute actual builds. | Core-adjacent backend wrapper; UI Target/TBD. | Decide product API/CLI surface later; do not replace factory internals. |
| Current vs Candidate Comparison | `src/current_vs_candidate.py`, `docs/specs/current_vs_candidate_spec.md`, wired after Selection in `write_candidate_comparison_outputs()` | Implemented additive `current_vs_candidate.json` adapter over canonical comparison and optional selection. | Current generated outputs absent. It still depends on broader `candidate_comparison.json`. | `src/candidate_comparison.py` remains canonical and multi-candidate. | Core product adapter over technical comparison. | Consider explicit selected-candidate wiring from Alternatives Builder path; keep canonical comparison unchanged. |
| Decision Verdict | `src/decision_verdict.py`, spec, wired after `action_plan.json` | Implemented additive `decision_verdict.json` mapping Selection statuses to product verdicts. No schema rename. | Product copy/report integration may be incomplete. Uses `recommended_action` field. | `src/selection_engine.py` remains technical decision engine. | Core product adapter over Selection. | Keep mapping; do not rename `selection_decision.json`; review wording. |
| AI Commentary | `src/ai_commentary_context.py`, `docs/specs/ai_commentary_grounding_spec.md`, deterministic `src/portfolio_commentary.py` | Implemented grounding context only; no LLM call and no generated AI prose. Safe and aligned. | Actual AI Commentary output is Target/TBD. Need prompt/provider/output contract if later implemented. | Deterministic commentary/reporting remains. | Grounding core; generated AI commentary Target/TBD. | Do not add LLM generation until evidence refs, prompts, tests, and guardrails are approved. |
| Monitoring / What Changed | `src/monitoring.py`, `src/light_monitoring_summary.py`, `src/decision_journal.py`, specs | Full monitoring diff/journal already implemented; light product summary added as `what_changed_summary.json` projection. | Current generated outputs absent for summary; full monitoring may be advanced beyond light MVP. | `monitoring_diff.json`, journal history, action engine remain downstream technical artifacts. | Core light summary + advanced monitoring backend. | Keep summary separate; do not change monitoring history schema. |

Code-level architecture status: the migration is additive and mostly correctly layered, but runtime still flows through the old technical comparison/score/selection package before product adapters are emitted.

## 7. Runtime Flow Audit

### `run_portfolio_review.py`

Actual flow in current code:

```text
load config
resolve review mode/profile
build PortfolioReviewPlan
1. run_report.py --materialize-analysis-subject --output-profile <profile> --review-mode <mode>
2. run_candidate_factory.py --profile/--candidates ... --execution-mode standard --output-profile <profile> [--then-compare]
3. optionally run_compare_variants.py if candidates skipped or compare not delegated
4. optionally rebuild PDFs
```

Matches target:

- Diagnoses `analysis_subject` before candidates.
- Does not call `run_optimization.py` in default path.
- Supports diagnosis-only via `--skip-candidates` plan state.
- Supports explicit one-candidate path via `--candidates`.

Diverges / risk:

- Default core uses a multi-candidate batch (`core_fast`), not a single user-triggered Launchpad/Builder path.
- Comparison/decision package is still technical and broad.
- README/OUTPUTS say core profile is `core_v1`, but code maps to `core_fast`.

### `run_candidate_factory.py`

Actual flow:

- Standalone factory default profile is `default_v1`.
- Orchestrates existing candidate builders; may run compare via `--then-compare`.
- Current code adds static product-boundary helpers classifying factory as backend/advanced/research.

Matches target:

- Preserves candidate builders as infrastructure.
- Does not claim Launchpad cards are portfolios.

Diverges / risk:

- Standalone default `default_v1` is full advanced/research batch. If user treats this as product front door, old batch-candidate UX dominates.
- Spec has contradictory “standard product comparison arena” wording for `default_v1`.

### `run_compare_variants.py`

Actual flow:

- Calls `write_candidate_comparison_outputs()`.
- Writes canonical comparison plus robustness, health, selection, monitoring, journal, decision package, and new product adapters.

Matches target:

- Provides deterministic evidence for Current vs Candidate and Decision Verdict.

Diverges / risk:

- Old technical outputs are not merely optional; they are still generated in the same core compare writer.
- Product-facing artifacts are appended after old score/selection chain rather than driving product flow.

### `run_report.py`

Actual flow:

- Produces report diagnostics, snapshots, stress report, X-Ray, output manifest.
- Current working tree wires `problem_classification.json` and `candidate_launchpad.json` after X-Ray summary.
- Materializes `analysis_subject` sidecar.

Matches target:

- Strong Input -> X-Ray -> Stress -> Problem Classification -> Launchpad backend sequence.

Diverges / risk:

- Current generated `analysis_subject` folder lacks the new artifacts because outputs are stale.
- Report pipeline still contains broad advanced diagnostics (macro/regime/PCA/factors) by default in JSON evidence.

### `run_optimization.py`

Actual flow: legacy policy optimization and weight release checks; can produce policy weights and optional report. This matches the target only as **legacy compatibility**. If used as front door, it is old optimizer-first behavior.

### `run_view_after_optimization.py`

Actual flow: specialized post-optimization tilt view. Classification: legacy/specialized compatibility, not Core MVP diagnosis-first flow.

## 8. Outputs / JSON Contract Audit

| Output / contract | Current classification | Observed/generated status | Alignment notes |
| --- | --- | --- | --- |
| `problem_classification.json` | Core product adapter / diagnostic artifact | Code/docs say written by `run_report.py`; current known outputs did not contain it. | Aligned in design; stale output risk. |
| `candidate_launchpad.json` | Core product adapter / hypothesis cards | Code/docs say written by `run_report.py`; current known outputs did not contain it. | Aligned; cards not portfolios. |
| Portfolio Alternatives Builder outputs | No persistent JSON contract in V1; build-plan object | Implemented as Python plan, not output file. | Acceptable if documented. Product UI/service missing. |
| `current_vs_candidate.json` | Core product adapter over canonical comparison | Code/docs say written by compare; current known outputs did not contain it. | Aligned; depends on technical comparison. |
| `decision_verdict.json` | Core product adapter over Selection | Code/docs say written by compare; current known outputs did not contain it. | Aligned; field wording `recommended_action` sensitive. |
| `selection_decision.json` | Technical contract / backend decision evidence | Present in `Main portfolio/`. | Valid technical artifact, not product-facing final word unless mapped to Verdict. |
| `candidate_comparison.json` | Technical contract / backend evidence / advanced when multi-candidate | Present and large. | Still central runtime contract; product should use adapter for MVP surface. |
| `portfolio_health_score.json` | Technical diagnostic/backend artifact; advanced/supporting evidence | Present in `Main portfolio/`. | Must not be main product output. Runtime writes it by default. |
| `robustness_scorecard.json` | Technical diagnostic/backend artifact; advanced/supporting evidence | Present in `Main portfolio/`. | Same leakage risk as Health Score. |
| `action_plan.json` | Non-executing technical action summary | Present. | Can support verdict/report, but not trade execution. |
| `monitoring_diff.json` | Technical monitoring diff | Present. | Valid backend. Light summary should be product-facing. |
| `what_changed_summary.json` | Core light product summary | Code/docs say written; current known outputs absent. | Aligned design; stale output risk. |
| `decision_journal.json` | Generated decision record / advanced-supporting artifact | Present. | Useful record, not user-maintained workflow source. |
| `ai_commentary_context.json` | Deterministic AI grounding context | Code/docs say written; current known outputs absent. | Aligned and safe. No AI prose yet. |
| `output_manifest.json` | Technical output index | Present only under `Main portfolio/analysis_subject` in inspected generated output; contents did not list new Problem/Launchpad artifacts. | Stale relative to current code. Refresh only in generated-output task. |
| Root `portfolio_xray.json`, `stress_report.json`, `run_metadata.json` | Legacy/root policy/report artifacts unless under `analysis_subject/` | Present. | Must not substitute for `analysis_subject/` after portfolio-first review. |
| PDF/TXT/HTML/PNG/Markdown sidecars | Generated export artifacts | Many dirty generated files exist. | Not source-of-truth; should not be committed unless task targets outputs. |

Output conflict highlight: `OUTPUTS.md` says new product artifacts are part of output contracts, but current generated folders do not show them. This is probably because generated outputs were not refreshed after the new untracked/modified code, but it still matters operationally.

## 9. Specs vs Code vs Product Contradictions

| Product doc claim | Spec claim | Code behavior | Contradiction... | Severity | Recommended fix |
| --- | --- | --- | --- | --- | --- |
| Target modules are target/TBD or require verification (`PRODUCT.md`, `ARCHITECTURE.md`, `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`). | `SPEC.md` status matrix and new specs claim Problem Classification, Launchpad, Current-vs-Candidate, Verdict, AI grounding, Light Monitoring are implemented. | Current working tree contains modules and wiring. | Yes: status timing mismatch. | High | Update product/architecture implementation relationship after migration files are accepted. |
| Routine core review uses `core_v1`. | `portfolio_review_workflow_spec.md` says core uses `core_fast`. | `REVIEW_MODE_PROFILES['core'] = core_fast`. | Yes. | High | Patch `README.md` and `OUTPUTS.md` command matrices. |
| Candidate Factory is not default product UX. | `candidate_factory_spec.md` boundary says backend/advanced/research, but registry row says `default_v1` is “Standard product comparison arena.” | Standalone CLI default remains `default_v1`; review full uses it only with `--mode full`. | Yes, wording and default-risk. | High | Change wording; keep CLI default only if clearly backend. |
| Decision Verdict is product-facing answer. | `selection_engine_spec.md` owns Selection technical contract; `decision_verdict_spec.md` maps statuses. | Compare writer writes Selection first, then Verdict. | No if mapped; risk if UI reads Selection directly. | Medium | Product surfaces should read `decision_verdict.json`; technical tools may read Selection. |
| Current vs Candidate is primary product comparison. | `candidate_comparison_spec.md` remains canonical full technical comparison; `current_vs_candidate_spec.md` is adapter. | Compare writer builds full comparison then adapter. | Partial. | Medium | Keep adapter as product contract; do not expose full candidate ranking as default UX. |
| Candidate Launchpad leads to Alternatives Builder. | Specs state cards do not build portfolios; Builder returns one-candidate factory plan. | Code matches. | No. | Low | Add UI/API later. |
| AI Commentary exists in target architecture. | AI grounding spec says only context, no LLM prose. | Code writes context only. | Partial: product layer not fully implemented. | Medium | Do not claim generated AI Commentary exists; call it grounding context. |
| Light Monitoring / What Changed is product layer. | Monitoring spec remains full backend; light summary spec maps it. | Code writes summary after monitoring diff. | No in design; outputs stale. | Medium | Refresh outputs later; product reads summary. |
| Health/Robustness/Model Risk/Assumption Sensitivity are advanced/supporting. | Specs mostly say diagnostic/non-binding. | Compare writer still always generates them. | Partial leakage. | High | Make UI/output docs classify them as technical evidence; consider product bundle filtering. |

## 10. Advanced / Later Leakage Check

| Feature | Current leakage status | Evidence | Action |
| --- | --- | --- | --- |
| Macro Overlay / Macro Dashboard | Mostly contained as advanced/negative. | Product docs demote; archive has old dashboard language. | Keep advanced. Do not make mandatory MVP. |
| Strategy Backtest | Advanced/later. | Product docs demote; code has backtesting metrics as backend diagnostics. | Keep backend metrics, not product block. |
| Full candidate stress evaluation | Leaks through comparison/factory artifacts. | Candidate comparison scans full candidate artifacts when present. | Product UI should use shortlist/current-vs-candidate. |
| Multi-candidate ranking | Technical core still does this. | `candidate_comparison.json`, Health/Robustness/Selection. | Treat as advanced/research evidence except explicit full mode. |
| Portfolio Health Score | High leakage risk. | Generated by compare; listed in README. | Label supporting/backend everywhere. |
| Robustness Scorecard | High leakage risk. | Generated by compare; listed in README. | Same. |
| Assumption Sensitivity | Medium/high leakage. | Generated in compare chain. | Advanced/supporting evidence. |
| Pareto / Regret / Model Risk | Medium/high leakage. | Specs and compare writer include them. | Advanced/supporting evidence. |
| Asset X-Ray | Not validated in depth. | Taxonomy/asset diagnostics exist. | Requires human/product review before Core MVP. |
| Client-Fit Check | Legacy/technical mandate/client profile artifacts exist. | Mentioned in comparison/report contexts. | Keep as technical suitability/mandate evidence, not advice. |
| Portfolio Archetype Classification | Product concept demotes as advanced/later. | X-Ray weaknesses/archetype-like diagnostics exist. | Do not relabel as Problem Classification. |
| Advanced optimizer cockpit | Preserved optimizer scripts and robust suites. | Many optimizer scripts/specs. | Keep advanced/research. |
| Tax-aware / turnover-aware / tactical tilt | Mostly later/specialized. | `run_view_after_optimization.py`, transaction-cost estimate in action engine. | Do not promote to Core MVP without spec. |

Conclusion: advanced leakage is not mainly from product docs; it is from the fact that the current compare writer emits the full old decision-evidence package by default. This is acceptable technically but risky for product framing.

## 11. Historical / Archive Policy Check

Archive and historical policy is mostly correct:

- `docs/audits/README.md` warns older audits may use optimizer-first, recommendation, Macro Dashboard, Selection Engine, Health Score, or Robustness Scorecard wording and should be preserved as snapshot-at-time evidence.
- `docs/exec_plans/README.md` similarly warns historical plans are not current product direction.
- `AGENTS.md` and root docs state archived migration records do not override `SPEC.md`, detailed specs, and code.

Risks:

- `docs/ROADMAP.md` is not purely archive; it is a durable roadmap and still opens with Optimization Terminal language and a large history of scoring/selection phases. It should get a top-level alignment note.
- The untracked migration ExecPlan is not currently registered as active in `docs/exec_plans/README.md` (active pointer says none). If the plan is current, this is confusing.
- Migration ExecPlan notes say docs verification is blocked by stale archive links. Archive content should not be rewritten for product content, but link maintenance may be needed to restore verification.

Recommendation: preserve archive content; do not rewrite old audits/plans. Add current-direction notes to registers/roadmap only in a separate documentation cleanup session.

## 12. Dirty Working Tree Context

`git status --short` before creating this audit showed a very large dirty tree.

| Category | Examples | Impact on audit |
| --- | --- | --- |
| Migration-related docs/specs | `SPEC.md`, `OUTPUTS.md`, `docs/specs/README.md`, `docs/specs/candidate_factory_spec.md`, new specs, code migration plan, migration ExecPlan | High. These are central to alignment but not yet cleanly committed. |
| Migration-related source | `src/problem_classification.py`, `src/candidate_launchpad.py`, `src/portfolio_alternatives_builder.py`, `src/current_vs_candidate.py`, `src/decision_verdict.py`, `src/ai_commentary_context.py`, `src/light_monitoring_summary.py`, modified `src/action_engine.py`, `src/selection_engine.py` | High. They make the new architecture real but are dirty/untracked. |
| Migration-related tests | `tests/test_problem_classification.py`, `tests/test_candidate_launchpad.py`, `tests/test_current_vs_candidate.py`, etc. | Medium/high. Good evidence exists, but still dirty/untracked. |
| Generated outputs | Candidate portfolio folders, `pdf files/`, `pdf_md_sources/`, `__pycache__`, logs | Medium. They make status noisy and should not be staged with code/docs. |
| Config/env | `config.yml`, `config.yml.example`, `requirements.txt` | High. Needs human review; may be unrelated. |
| Unrelated data-provider work | `run_ibkr_market_data.py`, `src/data_ibkr.py`, `src/data_provider.py`, data-provider tests, cache/data loader changes | High. Appears separate from Portfolio MRI architecture migration. |
| Unknown | Some modified source/generated artifacts not deeply classified in this audit | Medium. Do not stage blindly. |

Dirty tree makes the audit harder because “current codebase” includes untracked/modified architecture migration work while generated outputs reflect an older run. This is the main blocker before further development.

## 13. Findings Ranked by Severity

### Critical: must fix before further development

1. **Dirty-tree baseline is unsafe.** The architecture migration spans many modified/untracked docs, specs, source, tests, logs, generated outputs, and unrelated config/provider files. Further work risks mixing concerns.
2. **Implementation-status contradiction.** Active product/architecture docs still mark target modules as TBD/requires verification, while current specs/code claim they are implemented additive artifacts.
3. **Generated outputs are stale relative to new output contracts.** Current known outputs do not contain new product-facing JSON artifacts, and existing `output_manifest.json` does not list them.

### High: fix before next major code work

1. **Default core profile documentation is wrong.** Docs say `core_v1`; code/spec use `core_fast`.
2. **Candidate factory boundary has internal conflict.** `default_v1` is both advanced/research full batch and “standard product comparison arena” in spec wording.
3. **Old score/selection chain still dominates compare runtime.** Product adapters are appended after Health/Robustness/Selection/advanced evidence.
4. **Standalone factory defaults to full `default_v1`.** Valid backend default, but dangerous if treated as product entrypoint.
5. **AI Commentary is only grounding context.** Do not claim actual AI commentary generation exists.
6. **Roadmap/register status mismatch.** New migration plan appears untracked while active pointer says none.
7. **Archive links reportedly block docs verification.** Needs maintenance without rewriting history.
8. **Config/requirements/provider changes are mixed into the same dirty tree.** Must be reviewed separately.

### Medium: fix soon

1. Root process docs still use `Optimization Terminal` identity.
2. Product docs use `recommendation` wording in a few places where `verdict` or `next step` would be safer.
3. `Decision Verdict` uses `recommended_action` field; do not rename now, but consider future product wording migration.
4. `docs/ROADMAP.md` can be mistaken as current direction despite historical content.
5. Advanced artifacts need a product-bundle/filtering story.
6. New product artifacts need a clear verification/test bundle in `TESTING.md`.
7. Some files show mojibake characters in comments/docs, reducing clarity.

### Low: wording cleanup

1. Historical changelog/exec-plan/audit old terms are acceptable if not used as current direction.
2. `black-box optimizer`, `best portfolio`, and `automatic recommendation` mostly appear as negative/non-goal language.
3. Macro Dashboard mostly appears as advanced/later or archive context.

### Acceptable / no action

1. Selection Engine remains a technical contract until a schema migration is approved.
2. Health/Robustness specs can remain as implemented diagnostic/backend contracts.
3. Legacy optimizer entrypoints should be preserved as compatibility infrastructure.
4. Generated outputs should not be deleted or edited during architecture audit.

## 14. Recommended Improvement Roadmap

### Session A — Dirty Tree Baseline Split

- Objective: separate migration code/docs/tests from generated outputs, config/env changes, and unrelated data-provider work.
- Likely files: use `DIRTY_TREE_CLASSIFICATION.md`, git status, all untracked migration files.
- Risk: High.
- Verification command: `git status --short`, `git diff --name-only`, no tests required until scope isolated.
- Expected output: reviewed allowlist for migration commit(s); generated/unrelated files left unstaged.

### Session B — Source-of-Truth Status Reconciliation

- Objective: reconcile `README.md`, `PRODUCT.md`, `ARCHITECTURE.md`, `SPEC.md`, `OUTPUTS.md`, `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md` around implemented-vs-target status.
- Likely files: those six docs plus `docs/specs/README.md` if needed.
- Risk: Medium/high.
- Verification command: `python scripts/verify_docs.py` if archive-link blocker is handled; otherwise targeted `rg` stale-wording checks.
- Expected output: no contradiction between “target/TBD” and implemented additive artifacts.

### Session C — Command Matrix / Core Profile Fix

- Objective: align all command matrices with code: `--mode core -> core_fast`, `core_v1` as sequential regression/legacy core profile.
- Likely files: `README.md`, `OUTPUTS.md`, `docs/operational_runbook.md`, `docs/specs/candidate_factory_spec.md`, maybe `TESTING.md`.
- Risk: Medium.
- Verification command: `python run_portfolio_review.py --dry-run` and `rg -n "core_v1|core_fast|--mode core" README.md OUTPUTS.md docs`.
- Expected output: no active docs claim default core uses `core_v1` unless explicitly saying sequential regression.

### Session D — Candidate Factory Boundary Cleanup

- Objective: eliminate wording that implies full batch generation is Core MVP/product default.
- Likely files: `docs/specs/candidate_factory_spec.md`, `README.md`, `PRODUCT.md`, `ARCHITECTURE.md`, `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`.
- Risk: Medium.
- Verification command: `rg -n -i "standard product comparison arena|default_v1|batch candidate generation|full batch" docs README.md PRODUCT.md ARCHITECTURE.md`.
- Expected output: `default_v1` consistently described as advanced/research full menu; product path uses Launchpad/Builder/current-vs-candidate.

### Session E — Product-Facing Output Bundle Policy

- Objective: decide whether product-facing outputs should be a filtered bundle (`problem_classification`, `candidate_launchpad`, `current_vs_candidate`, `decision_verdict`, `ai_commentary_context`, `what_changed_summary`) separate from technical decision package.
- Likely files: `OUTPUTS.md`, `docs/specs/reporting_outputs_spec.md`, new/updated product output spec if needed.
- Risk: High if schemas change; medium if only docs.
- Verification command: focused tests for `write_candidate_comparison_outputs()` and output manifest expectations.
- Expected output: clear “Core MVP product output” vs “technical/advanced generated evidence” boundary.

### Session F — Generated Output Refresh (only if approved)

- Objective: regenerate outputs to include new product-facing artifacts and updated manifests.
- Likely files: generated folders only (`Main portfolio/analysis_subject`, `Main portfolio`, maybe candidate folders).
- Risk: High due noisy generated diffs.
- Verification command: `python run_portfolio_review.py --mode core --skip-pdf` or narrower offline fixture smoke if available; then inspect output files.
- Expected output: new JSON artifacts present; output manifests list them; generated diffs intentionally scoped.

### Session G — AI Commentary Product Contract

- Objective: decide if/when to generate actual AI commentary prose. Keep deterministic grounding first.
- Likely files: `docs/specs/ai_commentary_grounding_spec.md`, possible new `ai_commentary_spec.md`, tests, maybe prompt templates.
- Risk: High.
- Verification command: grounding tests plus strict no-calculation/no-unsupported-claim tests.
- Expected output: either “grounding only” remains final for now, or an approved AI commentary generation contract exists.

### Session H — Archive Link / Verification Hygiene

- Objective: fix docs verification blockers from archive links without rewriting historical content.
- Likely files: archive link paths or `scripts/verify_docs.py` archive policy, depending desired behavior.
- Risk: Medium.
- Verification command: `python scripts/verify_docs.py`.
- Expected output: documentation verification can run cleanly while archive content remains historical.

## 15. Final Verdict

Is the project now conceptually aligned... **Mostly yes.** The active product philosophy is diagnosis-first and decision-support oriented. The old black-box optimizer identity is no longer the main product narrative in the most important product docs.

Is the implementation aligned... **Partially.** The current working tree contains good additive modules for the new architecture, but runtime still goes through the old batch/comparison/score/Selection package. The new modules are adapters/projections over that technical chain, not yet a full product UX flow. Also, the migration implementation is dirty/untracked and generated outputs are stale.

Is documentation aligned... **Partially.** Product docs are aligned philosophically, but implementation-status and command-profile contradictions remain. Specs are mostly strong, but a few technical docs still have wording that can reintroduce old framing.

Next highest-leverage improvement: **cleanly resolve the dirty-tree migration baseline and then patch the source-of-truth contradictions (`core_fast` vs `core_v1`, implemented vs Target/TBD status, and factory full-batch product boundary).**

What should not be touched yet:

- Do not rename `selection_decision.json`, Selection Engine fields, or existing generated schemas.
- Do not rewrite archived historical docs for product language.
- Do not delete generated outputs in an audit/doc alignment task.
- Do not promote AI Commentary from grounding context to generated AI prose without a separate spec and tests.
- Do not demote or remove optimizer/candidate/scorecard capabilities just because they are not Core MVP UX.
