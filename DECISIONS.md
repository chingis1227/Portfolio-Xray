# DECISIONS.md

This file is the concise living decision log for Portfolio X-Ray & Optimization Terminal / Portfolio MRI.

It records important decisions, why they were made, what alternatives were rejected, and which assumptions existed at the time. It is not a changelog, roadmap, issue tracker, implementation spec, or ExecPlan.

Accepted project-level decisions are listed below. Add entries here only when a real decision is made.

## Purpose

- Preserve the reasoning behind important project choices.
- Prevent the same architectural, product, or methodology questions from being reopened without context.
- Make assumptions visible when a decision is made.
- Keep rationale separate from implementation details and change history.

## What Belongs Here

- Architecture decisions that affect module boundaries, workflows, interfaces, or source-of-truth ownership.
- Product boundary decisions, such as diagnostic-only vs production policy behavior.
- Financial methodology decisions, such as optimizer policy, stress governance, data assumptions, metrics behavior, or model-risk boundaries.
- Testing and quality decisions that affect verification strategy.
- Documentation governance decisions that affect how project knowledge is organized.

## What Does Not Belong Here

- Every code change; use [CHANGELOG.md](CHANGELOG.md) for concise completed-change history.
- Active bugs, weak spots, or technical debt; use [KNOWN_ISSUES.md](KNOWN_ISSUES.md).
- Long formulas or module contracts; use `SPEC.md`, `DATA.md`, and `docs/specs/*.md`.
- Step-by-step implementation plans; use [PLANS.md](PLANS.md) and `docs/exec_plans/`.
- Future product ideas without a decision; use `PRODUCT.md`, `BUSINESS_VISION.md`, or `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`.

## When To Add Or Update

- Add an entry when the project chooses one path among meaningful alternatives.
- Add an entry when a decision affects behavior, source-of-truth structure, methodology, API/UI boundaries, data policy, testing policy, or reporting contracts.
- Update an entry when the decision is superseded, narrowed, expanded, or its assumptions are no longer true.
- Do not rewrite history silently; mark old decisions as `superseded` and link the newer decision.
- If a decision changes current behavior, update the owning spec and add a short entry to [CHANGELOG.md](CHANGELOG.md).
- If a decision exposes an unresolved risk or debt item, add it to [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

## Entry Format

Keep entries short. Use this format:

```markdown
Decision ID: DEC-YYYY-MM-DD-NNN
Title: Short title

- Status: proposed | accepted | superseded
- Date: YYYY-MM-DD
- Decision: What was decided.
- Context: What problem or trade-off triggered the decision.
- Rationale: Why this option was chosen.
- Alternatives considered: What was rejected and why.
- Assumptions: What was believed to be true at the time.
- Consequences: What changes or constraints follow from the decision.
- Related documents: Links to specs, plans, code, tests, or docs.
- Review trigger: When this decision should be revisited.
```

## Decisions

Decision ID: DEC-2026-05-17-002
Title: V1 candidate comparison contract (full registry, current row, Main output)

- Status: accepted
- Date: 2026-05-17
- Decision: The canonical comparison artifact is `candidate_comparison.json` under `output_dir_final` (default `Main portfolio/`). V1 lists the full candidate registry with `unavailable` when artifact folders are missing, and includes a `current` candidate when user-current portfolio artifacts exist (`analyze_current_weights` or `user_current_portfolio` tagging).
- Context: Legacy `portfolio_comparison.json` and `ew_rp_comparison.json` cover partial subsets with inconsistent schemas; audit AUD-010 requires one contract before scores and selection.
- Rationale: A single diagnostic-only table supports current vs policy vs benchmarks without implying a recommendation; Main placement keeps the comparison next to primary run outputs.
- Alternatives considered: Minimal four-candidate launch only; defer `current` to a later session; place the file in a root `comparison/` folder.
- Assumptions: Session 09 implements a read-only builder that does not recompute metrics; legacy comparison files remain until migration.
- Consequences: Robustness Scorecard, Health Score, and Selection Engine must consume `candidate_comparison.json` per [candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md).
- Related documents: [docs/specs/candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md), [OUTPUTS.md](OUTPUTS.md), [docs/ROADMAP.md](docs/ROADMAP.md).
- Review trigger: Revisit when comparison UI, cross-run history, or a dedicated comparison workspace is introduced.

Decision ID: DEC-2026-05-17-003
Title: Robustness Scorecard V1 scoring model

- Status: accepted
- Date: 2026-05-17
- Decision: The Robustness Scorecard uses relative within-run normalization for component sub-scores, product-concept weights under profile `default_weights_reviewable`, primary window 10y, RC-based diversification from a comparison `diversification` block (no vol/beta proxies), and absolute mandate checks only inside `mandate_fit`. Output is diagnostic-only until Selection Engine exists.
- Context: Session 10 specifies the scorecard after canonical `candidate_comparison.json`; the product concept defines six components and example weights.
- Rationale: Relative scoring answers "who is more resilient among these alternatives"; mandate limits stay explicit; RC concentration matches the project's RC_vol diagnostics.
- Alternatives considered: Absolute scoring against fixed thresholds for all components; temporary diversification proxies without RC in comparison.
- Assumptions: Session 11 implements the scorecard module and comparison v1.1 diversification fields together.
- Consequences: See [robustness_scorecard_spec.md](docs/specs/robustness_scorecard_spec.md); `src/robustness.py` remains optimizer weight stability only.
- Related documents: [docs/specs/robustness_scorecard_spec.md](docs/specs/robustness_scorecard_spec.md), [docs/specs/candidate_comparison_spec.md](docs/specs/candidate_comparison_spec.md), [docs/ROADMAP.md](docs/ROADMAP.md).
- Review trigger: Revisit after empirical validation of weights or when Selection Engine consumes score outputs.

Decision ID: DEC-2026-05-17-001
Title: Use docs/ROADMAP.md as the durable development roadmap

- Status: accepted
- Date: 2026-05-17
- Decision: The ordered product-development roadmap lives at `docs/ROADMAP.md`; it is a planning document and does not override canonical specs or current implementation contracts.
- Context: The 2026-05-17 audit found that the project had product concepts, implementation specs, and many analytical modules, but no single execution spine connecting concept layers to ordered development sessions.
- Rationale: `docs/ROADMAP.md` is clearer than `docs/product_backlog.md` for a durable cross-phase plan and matches the audit's first recommended filename.
- Alternatives considered: Use `docs/product_backlog.md`, which is also reasonable but narrower; keep only the ExecPlan, which would make the plan less discoverable from root documentation.
- Assumptions: Future major work continues to use checked-in ExecPlans when changes are large or risky; roadmap items remain non-binding until promoted into owning specs and code.
- Consequences: Future product modules should map to roadmap IDs, source-of-truth specs, artifacts, and verification before implementation. Current behavior remains governed by `SPEC.md` and detailed specs.
- Related documents: [docs/ROADMAP.md](docs/ROADMAP.md), [docs/exec_plans/2026-05-17_project_development_session_plan.md](docs/exec_plans/2026-05-17_project_development_session_plan.md), [docs/audits/2026-05-17_full_project_system_audit.md](docs/audits/2026-05-17_full_project_system_audit.md).
- Review trigger: Revisit if roadmap ownership moves, a separate backlog is introduced, or product planning becomes managed outside the repository.

Decision ID: DEC-2026-05-15-001
Title: Separate current weights from generated policy weights

- Status: accepted
- Date: 2026-05-15
- Decision: The Input and Assumptions Layer supports `analysis_mode=optimize_from_universe` for the default policy workflow and `analysis_mode=analyze_current_weights` for fixed current-portfolio diagnostics using `current_weights`.
- Context: The product concept allows existing-portfolio analysis with current weights, while the current policy rule says final production weights are generated by optimization.
- Rationale: Separating current diagnostic weights from generated policy weights lets users analyze existing portfolios without weakening the rule that policy weights come from the optimizer or approved post-optimization protocols.
- Alternatives considered: Continue using only `weights` for both cases, which keeps ambiguity; allow manual policy weights, which weakens production semantics.
- Assumptions: The first product layer remains CLI/file-driven and report-first; full UI, formal selection, and no-trade logic are still TBD.
- Consequences: `run_optimization.py` rejects `analyze_current_weights`; `run_report.py` can diagnose fixed current weights; artifacts expose an `input_assumptions` summary.
- Related documents: [docs/specs/input_assumptions_spec.md](docs/specs/input_assumptions_spec.md), [docs/exec_plans/2026-05-15_input_assumptions_layer_v1.md](docs/exec_plans/2026-05-15_input_assumptions_layer_v1.md), [docs/specs/portfolio_construction_policy.md](docs/specs/portfolio_construction_policy.md).
- Review trigger: Revisit when the project adds a UI input workflow, formal Selection Engine, or compare-current-to-policy workflow.

Decision ID: DEC-2026-05-15-002
Title: Make analysis_setup the input-layer runtime contract

- Status: accepted
- Date: 2026-05-15
- Decision: `analysis_setup` is the single resolved runtime contract for portfolio input, analysis portfolio, mandate, assumptions, and validation; `input_assumptions` is a report/export projection from it.
- Context: The product needs a clear analysis contract before diagnostics, stress testing, optimization, comparison, recommendation, or reporting, without adding UI or selection-engine scope.
- Rationale: A single resolved contract prevents `input_assumptions`, generated weights, current weights, and future UI inputs from becoming competing sources of truth.
- Alternatives considered: Keep only `input_assumptions` as the runtime summary, which blurs reporting metadata with business logic; immediately change universe-only report behavior, which would exceed the compatibility scope.
- Assumptions: Backward compatibility takes priority; target MVP conflicts are documented before behavior changes.
- Consequences: Run artifacts expose `analysis_setup`; `input_assumptions` is projected from it; Equal Weight Initial Portfolio is labeled as a baseline, not a recommendation.
- Related documents: [docs/specs/input_assumptions_spec.md](docs/specs/input_assumptions_spec.md), [OUTPUTS.md](OUTPUTS.md), [docs/specs/reporting_outputs_spec.md](docs/specs/reporting_outputs_spec.md).
- Review trigger: Revisit when SPEC authorizes taxonomy hard rejection in current repo mode or equal-weight universe-only diagnostics as executable report behavior.
