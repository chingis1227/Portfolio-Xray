# Repeat Project MVP Readiness Audit

Date: 2026-05-17

Scope: repeat project audit after the completed post-audit stabilization and analytics plan. This
audit checks the current repository against the file-first MVP goal: coherent documentation,
reliable data handling, clean user-facing outputs, correct diagnostics, end-to-end verification, and
a practical user flow from inputs to action artifacts.

Generated outputs were inspected as evidence of current user-facing quality only. They are not
treated as source of truth.

## Executive Conclusion

The project now has the analytical backbone needed for a file-first MVP. Candidate comparison,
robustness, health scoring, selection/no-trade, action planning, monitoring, decision journal,
trade-off/model-risk, assumption sensitivity, Pareto/dominance, regret, current-vs-policy, and
candidate factory artifacts are implemented as V1 file outputs.

The next risk is MVP reliability rather than missing analytics. The project needs a focused
stabilization pass before UI or new major analytics: source-of-truth documents must agree, data
pipeline cache and policy edge cases must be hardened, schema/language drift must be resolved before
regenerated-output QA, and a full offline pipeline smoke test should prove the MVP path without live
data dependencies.

Recommended follow-up plan: `docs/exec_plans/2026-05-17_post_audit_mvp_stabilization_plan.md`.

## Evidence Reviewed

- Source-of-truth documents: `RULES.md`, `WORKFLOW.md`, `SPEC.md`, `DATA.md`, `OUTPUTS.md`,
  `TESTING.md`, `KNOWN_ISSUES.md`, `README.md`, `PRODUCT.md`, `ARCHITECTURE.md`, and
  `docs/ROADMAP.md`.
- Planning and audit registers: `docs/audits/README.md`, `docs/exec_plans/README.md`, and the
  completed 2026-05-17 project-level ExecPlans.
- Product concept: `docs/DIAGNOSTIC_PRODUCT_CONCEPT.md`.
- Core implementation areas: data loader/cache/FX/returns, config risk-free and cash resolution,
  NaN-safe backtest handling, metrics, stress factor diagnostics, candidate comparison, decision
  artifacts, report/PDF generation, and tests.
- Representative generated outputs in portfolio output folders, `pdf_md_sources/`, and `pdf files/`.

## Verification Performed During Audit

- `scripts/verify_docs.py` passed.
- Focused pipeline tests passed after using a workspace-local pytest temp directory:
  - 37 tests for config/input/current-vs-policy/candidate comparison/decision package paths.
  - 64 tests for stress/selection/action/tradeoff/sensitivity/Pareto/regret paths.
- Initial pytest runs without `--basetemp` hit temp cleanup permission errors under the shared cache
  directory; rerunning with workspace-local `--basetemp` isolated that as an environment issue, not
  a business-logic assertion failure.

## Findings

### RMA-001: Source-of-truth status drift remains

Severity: high.

`SPEC.md`, `OUTPUTS.md`, `PRODUCT.md`, and `docs/ROADMAP.md` describe the file-first V1 decision
artifacts as implemented, but `README.md` and parts of `ARCHITECTURE.md` still contain wording that
can read as if several implemented artifacts remain target/TBD. This can mislead new agents into
replanning or rebuilding modules that already exist.

Next action: synchronize top-level current-status wording and search for stale implemented-as-TBD
phrases.

### RMA-002: Generated-output language and encoding quality is still an MVP risk

Severity: high.

Current generated folders can still contain stale Russian text, mojibake, or broken symbols. The
source/generator cleanup from the prior plan reduced the root cause, but representative outputs need
to be regenerated after the remaining schema/language drift is fixed. Generated outputs must not be
hand-edited.

Next action: complete source-level language/schema cleanup first, then regenerate and inspect
representative report, Markdown, HTML, and PDF-facing outputs.

### RMA-003: Monthly cache key does not include asset metadata fingerprint

Severity: high.

The monthly data cache key includes tickers, dates, investor currency, benchmark, cash proxy,
risk-free source, windows, data month, extra tickers, and returns frequency. It does not include the
asset currency metadata from `assets.yml`. If a ticker currency is corrected, stale FX-adjusted
returns can be reused.

Next action: include an asset metadata fingerprint in the monthly cache key and add a regression
test that changes asset currency metadata.

### RMA-004: Risk-free and cash defaults need one explicit policy

Severity: medium-high.

The code supports USD and EUR defaults for cash proxy and risk-free source, while some data/metrics
wording can be read as "any non-USD currency must be explicit." The practical policy should be
documented and tested: USD/EUR defaults are supported; unsupported non-USD currencies require explicit
configuration.

Next action: synchronize `DATA.md`, input assumptions, metrics specs, and config tests with that
policy unless a future decision changes it.

### RMA-005: NaN-safe cash fallback diagnostics underreport fallback months

Severity: high.

The NaN-safe backtest path redistributes missing risk-asset weight to available assets and residual
cash, but the diagnostic counter `n_months_cash_fallback` does not currently reflect fallback months.
This weakens the audit trail in `data_policy.json`.

Next action: fix the counter and add a focused regression test with missing risk weights that must
fall back to cash.

### RMA-006: Time-to-recovery semantics need regression coverage

Severity: medium.

The metric should measure recovery from the peak before the maximum drawdown. The current
implementation needs a focused test for recovered and unrecovered max drawdown paths to confirm or
correct behavior.

Next action: add regression coverage and update the formula or spec if the implementation differs
from the canonical metric definition.

### RMA-007: Stress assessment language/schema naming drift remains

Severity: medium.

Stress multicollinearity diagnostics still use `assessment_ru` naming in some places even though
project artifacts should default to English. Some readers use or expect `assessment_en`. This is a
schema cleanliness issue and can leak confusing fields into generated artifacts.

Next action: make `assessment_en` the primary field and retain `assessment_ru` only as legacy-read
compatibility where needed.

### RMA-008: There is no single offline MVP pipeline smoke test

Severity: medium-high.

The project has many focused tests, but no single synthetic/offline test that proves the practical
MVP flow from input/config through report/comparison to decision-package outputs without live network
data. That makes broad regressions harder to catch.

Next action: add a synthetic end-to-end smoke test and document it in `TESTING.md`.

## Product Concept Alignment

Implemented file-first: input assumptions, diagnostics, stress evaluation, candidate generation,
optimization candidates, backtest reports, macro/regime diagnostics, candidate comparison, health
score, robustness scorecard, selection/no-trade, action plan, monitoring, decision journal,
assumption sensitivity, Pareto/dominance, regret, trade-off, and model-risk artifacts.

Partial or future scope: full product workspace UI, interactive comparison arena, What-If simulator,
crisis replay UI, formal archetype/weakness-map UI, macro dashboard UI, user-maintained journal,
advanced tax/lot/turnover workflows, and polished client portal behavior.

MVP recommendation: stabilize the file-first decision workflow before product UI work. UI/workspace
decisions should remain outside the active stabilization plan.

## Recommended Session Order

1. Audit handoff and active plan.
2. Source-of-truth sync.
3. Risk-free/cash policy sync.
4. Cache and FX metadata correctness.
5. NaN-safe cash fallback diagnostics.
6. Metrics formula hardening.
7. Schema and language drift cleanup.
8. Generated-output QA.
9. Offline end-to-end pipeline test.
10. User-flow orchestration.
11. MVP readiness pass.

## Handoff

Use `docs/exec_plans/2026-05-17_post_audit_mvp_stabilization_plan.md` as the active plan. Keep each
numbered session in a separate chat unless the user explicitly changes that rule.
