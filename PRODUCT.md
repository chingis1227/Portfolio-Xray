# Product

## Status

This document describes Portfolio X-Ray / Portfolio MRI from the user experience perspective: user flow, primary screens, key features, and expected user outputs.

It is a product UX document. It does not replace [SPEC.md](SPEC.md), metric formulas, stress scenario definitions, investment policy logic, configuration schemas, or current implementation behavior.

Product priority: report-first before full UI, unless a future product decision changes this to TBD.

Related documents:

- [RULES.md](RULES.md) for high-level principles and source-of-truth ownership.
- [WORKFLOW.md](WORKFLOW.md) for how product changes move from task to implementation, verification, docs sync, and commit.
- [OUTPUTS.md](OUTPUTS.md) for generated reports, artifacts, folders, and output-format ownership.
- [GLOSSARY.md](GLOSSARY.md) for shared product and technical terminology.
- [Business Vision](BUSINESS_VISION.md) for the business goal, audience, value proposition, and monetization direction.
- [Diagnostic Product Concept](docs/DIAGNOSTIC_PRODUCT_CONCEPT.md) for living target product architecture ideas; non-binding until promoted to specs.
- [README.md](README.md) for current project overview and commands.
- [SPEC.md](SPEC.md) for canonical technical source-of-truth links.
- [Portfolio Review Workflow](docs/specs/portfolio_review_workflow_spec.md) for the
  `analysis_subject`-first product workflow.

## Product Summary

Portfolio MRI helps a user move from a portfolio input to a decision-ready investment view.

Primary user flow:

```text
Create analysis
-> Define analysis_subject and assumptions
-> Review Portfolio X-Ray
-> Run Stress Test Lab
-> Generate candidate portfolios
-> Compare candidates
-> Review recommendation or no-trade conclusion
-> Export report
-> Monitor changes over time
```

The product should feel like a structured portfolio review workflow, not a collection of disconnected metrics.

## UX Principles

- Diagnostic first: show what the current portfolio really is before recommending changes.
- Explain trade-offs: every recommendation should state what improves, what worsens, and what it costs.
- Keep assumptions visible: users should know which data window, benchmark, currency, constraints, and methods are being used.
- Compare alternatives fairly: candidates should be evaluated under the same metric, backtest, and stress framework.
- Support no-trade outcomes: the product should be able to conclude that changing the portfolio is not worth it.
- Separate product concept from implementation: target UX does not override current code or specs.

## Primary User Roles

### Investor

Goal:

Understand real portfolio risk and decide whether to improve the allocation.

Expected output:

A clear diagnosis, stress view, candidate comparison, and recommendation or no-trade conclusion.

### Advisor

Goal:

Prepare a professional portfolio review before a client meeting.

Expected output:

A client-ready report with portfolio diagnosis, key risks, stress behavior, candidate comparison, and action rationale.

### Wealth Manager / Family Office User

Goal:

Run consistent diagnostics across multiple portfolios.

Expected output:

Repeatable portfolio reviews, comparable outputs, and governance-friendly decision records.

## Core User Flow

### 1. Create Analysis

User goal:

Start a new portfolio review.

Inputs:

- Analysis name.
- Portfolio owner or client name, if applicable.
- Analysis date.
- Analysis type: current portfolio review, candidate construction, comparison, or monitoring review.

Outputs:

- A new analysis workspace.
- Initial status: incomplete inputs.

Current implementation:

- The current project is primarily CLI and file-driven through `config.yml` and generated artifacts.
- The portfolio-first workflow contract starts from `analysis_subject`; runtime migration is active.
- `run_optimization.py` and `run_report.py` remain existing compatibility entrypoints during the transition.

Target status:

- Product UI / workspace is TBD.

### 2. Portfolio Input

User goal:

Define what is being analyzed.

Inputs:

- Tickers or instruments.
- Current weights, if analyzing an existing portfolio.
- Analysis subject type: `current_portfolio`, `model_portfolio`, or `universe_baseline`.
- Investor currency.
- Benchmark.
- Risk profile.
- Investment horizon.
- Optional asset metadata.

Key UX requirements:

- Clearly show whether the user is analyzing an existing weighted portfolio or building from a universe.
- Validate tickers and missing metadata.
- Surface unknown assets, missing prices, short history, and taxonomy gaps.
- Keep current weights separate from optimized target weights.
- Treat `analysis_subject` as the portfolio diagnosed first before candidates.

Outputs:

- Validated portfolio universe.
- Current portfolio weights when supplied.
- Warnings for missing data or taxonomy gaps.

Current implementation:

- `config.yml` defines the active universe and settings.
- `analysis_mode` separates build-from-universe runs from existing-portfolio diagnostics.
- `current_weights` can be used for existing-portfolio diagnostics in `analysis_mode=analyze_current_weights`.
- The accepted portfolio-first contract defines `analysis_subject`; explicit runtime resolver work is
  planned in the active transition.
- ETF and stock taxonomy are annotation and validation layers.
- Final production weights are generated by optimization, not manually entered as final policy weights.

### 3. Mandate & Assumptions

User goal:

Define the rules and assumptions for the analysis.

Inputs:

- Risk profile.
- Target volatility.
- Maximum drawdown.
- Target or minimum return.
- Liquidity floor.
- Cash policy.
- Weight limits.
- Return frequency.
- Data windows.
- Benchmark.
- Risk-free source.
- Missing data policy.

Key UX requirements:

- Make constraints and assumptions visible before results are shown.
- Distinguish hard gates, soft objectives, and diagnostic-only metrics.
- Warn when a setting affects interpretation, such as non-monthly return frequency with weekly factor diagnostics.

Outputs:

- Analysis assumptions summary.
- Mandate summary.
- Feasibility warnings.

Current implementation:

- Current assumptions are controlled by `config.yml`, `config/client_profiles.yml`, and canonical specs.
- `analysis_setup` is the resolved input-layer runtime contract; the structured `input_assumptions` artifact is its reporting view for active input mode, resolved market assumptions, mandate inputs, calculation settings, and current V1 gaps.

### 4. Portfolio X-Ray

User goal:

Understand what the current portfolio really contains and how it behaves.

Primary screen sections:

- Allocation breakdown.
- Portfolio metrics.
- Risk contribution.
- Factor exposure.
- Hidden exposure warnings.
- Weakness map.
- Portfolio archetype.

Key outputs:

- Asset allocation view.
- Asset class, region, currency, sector, or risk bucket breakdown where available.
- Return, volatility, Sharpe, Sortino, drawdown, beta, and other implemented metrics.
- Top risk contributors.
- Hidden risk narrative.
- Plain-language portfolio diagnosis.

User questions answered:

- What do I actually own?
- Where is my risk concentrated?
- Which assets contribute more risk than their weight suggests?
- Does the portfolio behave like its labels imply?

Current implementation:

- Portfolio metrics, risk contribution, factor diagnostics, commentary, and snapshots exist in the reporting pipeline.

Target additions:

- Portfolio Archetype Classification is implemented in `portfolio_xray.json` (V2 evidence scorecard with conflicts); structured report/HTML surfaces ship via Session 08 formatters in `src/portfolio_xray.py`.
- Formal Weakness Map UI is TBD.

### 5. Stress Test Lab

User goal:

Understand how the portfolio behaves in bad market environments.

Primary screen sections:

- Scenario Library.
- Current Portfolio Stress Scorecard.
- Historical crisis replay.
- Synthetic scenario results.
- Loss contribution.
- Hedge gap analysis.
- What Happens If? simulator.

Key outputs:

- Worst stress scenario.
- Portfolio loss by scenario.
- Top asset loss contributors.
- Top factor contributors.
- Assets that helped.
- Mandate pass / fail where applicable.
- Hedge gap summary.

User questions answered:

- Where does this portfolio break?
- Which assets pull it down in crisis?
- Which assets actually hedge?
- Is the main weakness equity, rates, inflation, credit, liquidity, USD, commodity, or another risk?

Current implementation:

- Stress reports, scenario libraries, stress commentary, factor diagnostics, and stress scenario analytics exist.

Target additions:

- Interactive What Happens If? simulator is TBD.
- Full visual crisis replay is TBD.

### 6. Candidate Portfolio Factory

User goal:

Generate alternative portfolios for comparison.

Candidate types:

- Analysis Subject.
- Current Portfolio.
- Model Portfolio.
- Universe Baseline.
- Legacy policy optimized portfolio only when explicitly enabled by a future canonical spec.
- Equal Weight.
- Equal Weight by Asset Class.
- Risk Parity.
- Risk Budgeting.
- HRP.
- Minimum Variance.
- Maximum Diversification.
- Minimum CVaR.
- Robust Mean-Variance.
- Scenario-Based Robust Optimization.
- Custom constraints.
- Tactical tilt where enabled.

Key UX requirements:

- Explain each candidate as a construction hypothesis.
- Show whether the candidate is policy, benchmark, diagnostic, or custom.
- Avoid implying that every candidate is a production recommendation.

Outputs:

- Candidate list.
- Candidate weights.
- Construction method.
- Candidate metadata.
- Feasibility or mandate notes.

Current implementation:

- Multiple candidate builders exist as `run_*.py` scripts, and `run_candidate_factory.py` orchestrates configured builder sets before optional comparison.
- In the portfolio-first contract, candidates are generated after `analysis_subject` diagnostics; the old policy optimizer is not a default candidate.

Target additions:

- Unified candidate selection UI and workspace UX are TBD.

### 7. Strategy Backtest

User goal:

Compare how the current portfolio and candidates behaved historically.

Primary screen sections:

- Growth of capital.
- Rolling return and risk.
- Drawdown history.
- Calendar return table.
- Recovery and underwater periods.
- Benchmark comparison.

Key outputs:

- CAGR.
- Volatility.
- Sharpe.
- Sortino.
- Max drawdown.
- Time to recovery.
- Worst month / year where implemented.
- Rolling metrics where implemented.

User questions answered:

- Did the candidate improve historical behavior?
- Did lower risk come with lower return?
- Did the strategy only look good in one period?

Current implementation:

- Backtest and reporting outputs exist in the current pipeline.

Target additions:

- Full user-facing backtest screen is TBD.
- Walk-forward / out-of-sample UX is TBD.

### 8. Macro Risk Dashboard

User goal:

Understand the macro context and where the portfolio is vulnerable by regime.

Primary screen sections:

- Current macro regime.
- Growth score.
- Inflation score.
- Regime confidence.
- Portfolio fit by regime.
- Best and worst regimes.
- Watchpoints.

Key outputs:

- Current regime label.
- Confidence / coverage warnings.
- Regime-specific performance and risk where implemented.
- Macro risk narrative.

User questions answered:

- What macro environment are we in?
- Which regimes are dangerous for this portfolio?
- Is the current portfolio exposed to the wrong risks for the current environment?

Current implementation:

- Macro regime diagnostics, regime factor analytics, and regime portfolio metrics exist as diagnostic outputs.
- Macro Dashboard is positioned as a diagnostic overlay after portfolio and candidate stress evaluation; it contextualizes regime vulnerability without directly controlling optimizer weights.

Target additions:

- Productized macro dashboard UI is TBD.

### 9. Candidate Comparison Arena

User goal:

Compare two to five portfolios side by side and understand the trade-offs.

Primary screen sections:

- Candidate selector.
- Summary comparison table.
- Risk/return chart.
- Drawdown comparison.
- Stress comparison.
- Risk contribution comparison.
- Turnover and action comparison.
- Verdict panel.

Minimum comparison dimensions:

- Return.
- Volatility.
- Sharpe.
- Max drawdown.
- CVaR or tail loss where implemented.
- Worst stress.
- Top asset risk contributor.
- Top factor risk contributor.
- Turnover.
- Mandate fit.

Key outputs:

- Clear winner by dimension.
- Areas where each candidate is stronger.
- Areas where each candidate is weaker.
- Dominated candidates where applicable.
- Trade-off explanation.

User questions answered:

- Which portfolio is better, and in what sense?
- What do I give up if I choose the more robust portfolio?
- Which candidates should be rejected?

Current implementation:

- Canonical file-first comparison exists through `run_compare_variants.py` and `src/candidate_comparison.py`. It emits `candidate_comparison.json` / `.txt` and downstream V1 artifacts when inputs are available, including robustness, health, selection, trade-off/model-risk, assumption sensitivity, Pareto / dominance, regret, action, current-vs-policy status, monitoring, journal, and decision-package summary outputs.

Target additions:

- Full Portfolio Comparison Arena UI is TBD.
- Unified product UX around the file-first factory, current-vs-policy, Pareto, regret, and trade-off artifacts remains future product work.

### 10. Recommendation & Action

User goal:

Receive a decision-ready conclusion.

Possible outcomes:

- Rebalance recommended.
- No material rebalance recommended.
- More data or assumption review required.
- Mandate breach requires risk reduction.
- Candidate comparison is inconclusive.

Primary screen sections:

- Recommended portfolio or no-trade conclusion.
- Rationale.
- Trade-off explanation.
- Target weights.
- Buy / sell / hold.
- Delta vs current.
- Turnover.
- Expected risk improvement.
- Model risk warnings.

Key outputs:

- Recommendation summary.
- Action list.
- No-trade explanation where applicable.
- Risk improvement per turnover where available.
- Decision rationale.

User questions answered:

- What should I do?
- Why is this recommendation reasonable?
- What is the cost of changing?
- Is doing nothing better?

Current implementation:

- V1 Selection/No-Trade, trade-off/model-risk, and Action artifacts are implemented. `src/selection_engine.py` emits `selection_decision.json` / `.txt`; [tradeoff_and_model_risk.py](src/tradeoff_and_model_risk.py) emits `tradeoff_explanation.json` / `.txt` and `model_risk_diagnostics.json` / `.txt`; `src/action_engine.py` emits `action_plan.json` / `.txt`; mechanical rebalance helpers remain available through `src/rebalance.py`.

Target additions:

- Risk improvement per 1% turnover is TBD.

### 11. Report Export

User goal:

Produce a professional artifact for review, client communication, or decision records.

Outputs:

- Portfolio summary.
- Portfolio X-Ray.
- Stress scorecard.
- Candidate comparison.
- Recommendation or no-trade conclusion.
- Assumptions.
- Model risk warnings.
- Appendix with technical metrics where needed.

Formats:

- HTML.
- TXT / Markdown-style commentary.
- CSV/JSON diagnostics.
- PDF-style reports where configured.

Current implementation:

- The reporting pipeline exports CSV, JSON, HTML, TXT, and PDF-style artifacts. After comparison, the file-first decision package summary is implemented as `decision_package_summary.json` / `.txt`, with PDF-facing output where configured.

Target additions:

- More deliberately designed client-facing report packages and interactive report UX are TBD.

### 12. Monitoring / What Changed

User goal:

Track how portfolio risk changes over time.

Primary screen sections:

- Change since last analysis.
- New risk warnings.
- Changed worst scenario.
- Changed top risk contributor.
- Changed macro regime.
- Mandate status change.
- Rebalance trigger.

Key outputs:

- What changed.
- Why it changed.
- Whether action is needed.

Current implementation:

- V1 monitoring snapshots and `monitoring_diff.json` after `run_compare_variants.py` (see [monitoring spec](docs/specs/monitoring_spec.md)). Full product UI for monitoring remains TBD.

### 13. Decision Journal

User goal:

Record why a decision was made.

Stored fields:

- Analysis date.
- Selected portfolio.
- Rejected alternatives.
- Assumptions.
- Expected improvement.
- Accepted risks.
- Macro context.
- Rationale.
- Follow-up review date.

Key output:

- Decision record.

Current implementation:

- V1 implemented in [decision journal spec](docs/specs/decision_journal_spec.md) and [src/decision_journal.py](src/decision_journal.py) (generated-only, non-executing `decision_journal.json`).

## Feature Inventory

| Feature | Product Status | Implementation Status |
| --- | --- | --- |
| Portfolio input | Core | File/config-driven today |
| Mandate and assumptions | Core | Implemented through config/specs |
| Portfolio X-Ray | Core | Partially implemented through reports |
| Stress Test Lab | Core | Reports/diagnostics available; UI remains future scope |
| Candidate Portfolio Factory | Core | Implemented through scripts and `run_candidate_factory.py`, unified UX TBD |
| Strategy Backtest | Core | Implemented in reporting pipeline, UX TBD |
| Macro Risk Dashboard | Important | Diagnostics available; product UI remains future scope |
| Candidate Comparison Arena | Core target | File-first comparison and downstream decision artifacts available; full UI remains future scope |
| Portfolio Health Score | Implemented (diagnostic) | [portfolio_health_score_spec.md](docs/specs/portfolio_health_score_spec.md), [src/portfolio_health_score.py](src/portfolio_health_score.py) |
| Robustness Scorecard | Implemented (diagnostic) | Spec: [robustness_scorecard_spec.md](docs/specs/robustness_scorecard_spec.md); code: `src/robustness_scorecard.py` |
| Selection Engine | Implemented | [selection_engine_spec.md](docs/specs/selection_engine_spec.md), [src/selection_engine.py](src/selection_engine.py) |
| Assumption Sensitivity | Implemented (V1) | [assumption_sensitivity_spec.md](docs/specs/assumption_sensitivity_spec.md); `src/assumption_sensitivity.py` after trade-off in compare pipeline |
| Pareto / Dominance Check | Implemented (V1) | [src/pareto_dominance.py](src/pareto_dominance.py); [pareto_dominance_spec.md](docs/specs/pareto_dominance_spec.md) |
| Regret Analysis | Implemented (V1) | [regret_analysis_spec.md](docs/specs/regret_analysis_spec.md); `src/regret_analysis.py` |
| Trade-off Explanation | Implemented | `tradeoff_explanation_v1` via [tradeoff_and_model_risk.py](src/tradeoff_and_model_risk.py) |
| Action Engine | Implemented (V1) | `action_plan.json` via [src/action_engine.py](src/action_engine.py); mechanical trades via [src/rebalance.py](src/rebalance.py) |
| Rebalancing Advisor | Implemented (V1) | `action_plan.txt` companion summary |
| No-Trade Recommendation | Implemented (V1) | Same module as Selection Engine; `no_material_rebalance` outcome |
| AI Portfolio Commentary | Core | Implemented in report/commentary form |
| Monitoring / What Changed | Implemented (V1) | [monitoring_spec.md](docs/specs/monitoring_spec.md), [src/monitoring.py](src/monitoring.py) |
| Decision Journal | Implemented (V1) | `decision_journal.json` via [decision_journal.py](src/decision_journal.py); user-maintained journal workflow remains TBD |

## User Outputs

At the end of a complete analysis, the user should receive:

- A validated portfolio and assumptions summary.
- A Portfolio X-Ray diagnosis.
- A stress test scorecard.
- A candidate portfolio menu.
- A backtest and stress comparison of candidates.
- A recommendation, no-trade conclusion, or inconclusive status.
- A trade-off explanation.
- Actionable rebalance details where applicable.
- A professional report.
- A generated decision record from the V1 Decision Journal.

## Empty / Error States

The product should handle:

- Missing or invalid tickers.
- Missing price history.
- Short-history assets.
- Missing current weights.
- Invalid weight totals.
- Unsupported currency or missing FX data.
- Missing benchmark.
- Infeasible mandate constraints.
- Failed optimization.
- Failed mandate release.
- Insufficient stress or factor data.

Expected behavior:

- Explain the blocker in plain language.
- Identify what the user can fix.
- Preserve partial diagnostics when safe.
- Avoid presenting invalid recommendations.

## Product Non-Goals

- Do not present optimizer output as guaranteed best portfolio.
- Do not present generated policy optimization before the user's `analysis_subject` has been
  diagnosed in the portfolio-first workflow.
- Do not hide model risk or assumption sensitivity.
- Do not make stress diagnostics binding unless a canonical spec says so.
- Do not treat target UX lists as automatic implementation changes.
- Do not replace formulas, policy logic, or scenario definitions from canonical specs.

## Open Product Questions

- What is the first real UI surface: dashboard, static report, local app, or web app?
- Should the initial product be investor-first, advisor-first, or report-first?
- What minimum comparison set is required for launch?
- How should monitoring frequency work?
- What fields and review workflow are required for a user-maintained Decision Journal beyond generated V1 records?

## Source Of Truth Relationship

Product UX should be driven by this document, [Business Vision](BUSINESS_VISION.md), and [Diagnostic Product Concept](docs/DIAGNOSTIC_PRODUCT_CONCEPT.md).

Current behavior remains governed by:

- [RULES.md](RULES.md)
- [WORKFLOW.md](WORKFLOW.md)
- [README.md](README.md)
- [SPEC.md](SPEC.md)
- [Portfolio Review Workflow](docs/specs/portfolio_review_workflow_spec.md)
- [OUTPUTS.md](OUTPUTS.md)
- [DATA.md](DATA.md)
- [Portfolio Construction Policy](docs/specs/portfolio_construction_policy.md)
- [Metrics Specification](docs/specs/metrics_specification.md)
- [Stress Testing Spec](docs/specs/stress_testing_spec.md)
- [Data Policy](docs/specs/data_policy_spec.md)
- [PLANS.md](PLANS.md)
- [AGENTS.md](AGENTS.md)
